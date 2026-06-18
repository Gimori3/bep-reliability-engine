"""M9 ``fragility_assembler``: lognormal fragility fitting and the Phase 2 handoff.

Single responsibility (spec §1, M9): take the raw ``(N, N_h)`` static and
transient failure-indicator matrices, fit a lognormal fragility curve to *each*
empirical point set separately, attach bootstrap confidence bands, and package
everything Phase 2 needs into one :class:`FragilityResult` — including the
retained ``theta_matrix`` and *both* failure matrices, which are the
non-negotiable Phase 2 / survival-discrimination payload (spec §2, §8). This
module also owns persistence: HDF5 (h5py) for the large arrays plus a JSON
sidecar for the metadata block (spec §8 "Persistence format").

Lognormal fragility model (spec §2)
-----------------------------------
A fragility curve gives the conditional failure probability as a function of the
conditioning head ``h``::

    P_f(h) = Phi((ln h - mu) / sigma)

with ``mu`` and ``sigma`` the location and scale of the lognormal "capacity"
(the mean and standard deviation of ``ln`` capacity). This is the
:class:`LognormFragility` curve. The fit consumes the *empirical point set*
``(conditioning_grid, P_f_raw)`` — the Monte Carlo point estimates — rather than
per-realization capacities, because a lognormal fragility is a straight line in
probit space::

    Phi^-1(P_f) = (1/sigma) * ln h - mu/sigma

so an ordinary least-squares line through ``(ln h_i, Phi^-1(P_f_i))`` recovers
``sigma = 1/slope`` and ``mu = -intercept/slope`` exactly when the points lie on
a true curve (:func:`fit_lognormal_fragility`). Degenerate points where
``P_f`` is exactly 0 or 1 (probit ``= -+inf``) are masked before the fit.

Separate static and transient fits (spec §2, §4)
------------------------------------------------
The two limit states are fit independently: ``P_f_static_raw`` and
``P_f_trans_raw`` are the per-column failure fractions of the two matrices, and
each gets its own :class:`LognormFragility`. They are never collapsed into one
shared fit — the static-versus-transient bias *is* the Phase 1 deliverable.

Bootstrap confidence bands (spec §11)
-------------------------------------
Bands come from resampling the realizations (the rows shared by both limit
states, ADR-0002): for each of ``n_bootstrap`` replicates a single row index set
is drawn with replacement and applied to *both* matrices, the per-column failure
fractions are recomputed and refit, and the fitted curve is evaluated on the
grid. The ``confidence`` percentile interval of those refit curves, taken per
conditioning level, is the ``(lo, hi)`` band. The RNG is seeded solely from
``seed`` (independent of ``confidence``), so two runs at the same ``seed`` and
``n_bootstrap`` share identical resamples and differ only in the percentile cut
— a wider ``confidence`` is then a strictly wider band.

Persistence (spec §2, §8)
-------------------------
:meth:`FragilityResult.save` writes one HDF5 file (the arrays: ``theta_matrix``,
``conditioning_grid``, the raw point estimates, both bool failure matrices, the
bootstrap bands, with the fitted ``(mu, sigma)`` as root attributes and
``param_names`` as a string dataset) and one JSON sidecar next to it (the
``metadata`` block). :meth:`FragilityResult.load` reconstructs the result from
the pair. Avoiding pickle (version brittleness) and CSV (lossy floats) is
deliberate (spec §8). One HDF5 file per cross-section per scenario.

References
----------
Spec §1 (M9 responsibility), §2 (the FragilityResult contract and field set),
§8 (Phase 2 handoff, the survival-discrimination decomposition, the recommended
HDF5 schema and JSON sidecar), §10 (``scipy.stats`` lognormal fitting), §11
(bootstrap confidence bands). ADR-0001 (``c_e_stochastic`` metadata flag),
ADR-0002 (shared realizations across both limit states).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

__all__ = [
    "LognormFragility",
    "FragilityResult",
    "fit_lognormal_fragility",
    "assemble_fragility",
]


@dataclass(frozen=True)
class LognormFragility:
    """A fitted lognormal fragility curve ``P_f(h) = Phi((ln h - mu)/sigma)``.

    The two-parameter handoff curve of spec §2 (``P_f_static_fit`` /
    ``P_f_trans_fit``). ``mu`` and ``sigma`` are the location and scale of the
    lognormal capacity (mean and standard deviation of ``ln`` capacity), so the
    median capacity is ``exp(mu)`` and ``P_f(exp(mu)) = 0.5``.

    Attributes
    ----------
    mu : float
        Location parameter (mean of ``ln`` capacity) [ln-m].
    sigma : float
        Scale parameter (std of ``ln`` capacity) [-]; ``> 0``.
    """

    mu: float
    sigma: float

    def probability_of_failure(
        self, conditioning_level: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """Evaluate the fragility curve at one or more conditioning heads.

        Parameters
        ----------
        conditioning_level : float or numpy.ndarray
            Conditioning head(s) h [m above datum], strictly positive.

        Returns
        -------
        float or numpy.ndarray
            ``Phi((ln h - mu)/sigma)``: a Python float for scalar input, an
            array of the same shape for array input.
        """
        head = np.asarray(conditioning_level, dtype=np.float64)
        probability = norm.cdf((np.log(head) - self.mu) / self.sigma)
        return float(probability) if probability.ndim == 0 else probability


def fit_lognormal_fragility(
    conditioning_grid: NDArray[np.float64], p_f: NDArray[np.float64]
) -> LognormFragility:
    """Fit a lognormal fragility curve to an empirical ``(h, P_f)`` point set.

    Fits ``P_f(h) = Phi((ln h - mu)/sigma)`` by ordinary least squares in probit
    space: a lognormal fragility is the straight line
    ``Phi^-1(P_f) = (1/sigma) ln h - mu/sigma``, so a degree-1 fit of
    ``Phi^-1(P_f)`` against ``ln h`` gives ``sigma = 1/slope`` and
    ``mu = -intercept/slope``. Points with ``P_f`` exactly 0 or 1 (probit
    ``-+inf``) carry no finite information and are dropped before the fit.

    Parameters
    ----------
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads h [m above datum], strictly positive.
    p_f : numpy.ndarray, shape (N_h,)
        Empirical failure probabilities at each conditioning level, in
        ``[0, 1]`` (the Monte Carlo point estimates).

    Returns
    -------
    LognormFragility
        The fitted curve.

    Raises
    ------
    ValueError
        If fewer than two interior (``0 < P_f < 1``) points remain, or the
        fitted slope is non-positive (not a monotone-increasing fragility).
    """
    grid = np.asarray(conditioning_grid, dtype=np.float64)
    probabilities = np.asarray(p_f, dtype=np.float64)

    interior = (probabilities > 0.0) & (probabilities < 1.0)
    if int(np.count_nonzero(interior)) < 2:
        raise ValueError(
            "fit_lognormal_fragility needs at least two interior (0 < P_f < 1) "
            f"points; got {int(np.count_nonzero(interior))}."
        )

    ln_head = np.log(grid[interior])
    probit = norm.ppf(probabilities[interior])
    slope, intercept = np.polyfit(ln_head, probit, 1)
    if not slope > 0.0:
        raise ValueError(
            f"fitted probit slope {slope!r} is non-positive; the point set is "
            "not a monotone-increasing fragility."
        )

    sigma = 1.0 / slope
    mu = -intercept / slope
    return LognormFragility(mu=float(mu), sigma=float(sigma))


def _bootstrap_bands(
    failure_matrix_stat: NDArray[np.bool_],
    failure_matrix_tran: NDArray[np.bool_],
    conditioning_grid: NDArray[np.float64],
    n_bootstrap: int,
    confidence: float,
    seed: int,
) -> dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Bootstrap ``(lo, hi)`` bands on the fitted curves (spec §11).

    Each replicate draws one row index set with replacement and applies it to
    both matrices (realizations are shared across the two limit states,
    ADR-0002), refits each curve, and evaluates it on the grid. The band is the
    per-level ``confidence`` percentile interval of those refit curves. The RNG
    depends only on ``seed`` (not ``confidence``), so the resamples are shared
    across confidence levels.
    """
    n_realizations = failure_matrix_stat.shape[0]
    n_levels = conditioning_grid.shape[0]
    rng = np.random.default_rng(seed)

    boot_static = np.empty((n_bootstrap, n_levels), dtype=np.float64)
    boot_trans = np.empty((n_bootstrap, n_levels), dtype=np.float64)
    for b in range(n_bootstrap):
        rows = rng.integers(0, n_realizations, size=n_realizations)
        p_f_static = failure_matrix_stat[rows].mean(axis=0)
        p_f_trans = failure_matrix_tran[rows].mean(axis=0)
        boot_static[b] = fit_lognormal_fragility(
            conditioning_grid, p_f_static
        ).probability_of_failure(conditioning_grid)
        boot_trans[b] = fit_lognormal_fragility(
            conditioning_grid, p_f_trans
        ).probability_of_failure(conditioning_grid)

    lower_pct = 100.0 * (1.0 - confidence) / 2.0
    upper_pct = 100.0 * (1.0 + confidence) / 2.0
    return {
        "static": (
            np.percentile(boot_static, lower_pct, axis=0),
            np.percentile(boot_static, upper_pct, axis=0),
        ),
        "transient": (
            np.percentile(boot_trans, lower_pct, axis=0),
            np.percentile(boot_trans, upper_pct, axis=0),
        ),
    }


def assemble_fragility(
    theta_matrix: NDArray[np.float64],
    param_names: list[str],
    conditioning_grid: NDArray[np.float64],
    failure_matrix_stat: NDArray[np.bool_],
    failure_matrix_tran: NDArray[np.bool_],
    metadata: dict[str, Any],
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> FragilityResult:
    """Assemble the Phase 2 :class:`FragilityResult` from the raw matrices (M9).

    Computes the per-column failure fractions as the static and transient
    empirical point estimates, fits a separate :class:`LognormFragility` to each
    (spec §2), attaches bootstrap confidence bands (spec §11), and retains the
    ``theta_matrix`` and *both* failure matrices for the Phase 2 / survival-
    discrimination handoff (spec §8).

    Parameters
    ----------
    theta_matrix : numpy.ndarray, shape (N, 7)
        The prior sample matrix, retained verbatim for Phase 2 Accept-Reject
        filtering (spec §2, §8). Its contents do not enter the fragility math.
    param_names : list of str
        Canonical column names of ``theta_matrix`` (the M2 contract).
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads ``{h_1, ..., h_Nh}`` [m above datum], strictly
        positive.
    failure_matrix_stat, failure_matrix_tran : numpy.ndarray, shape (N, N_h)
        Boolean static / transient failure indicators (``True`` = failed).
    metadata : dict
        The provenance / config-snapshot block (spec §8); stored verbatim and
        written to the JSON sidecar on :meth:`FragilityResult.save`.
    n_bootstrap : int, optional
        Number of bootstrap replicates for the confidence bands. Default 1000.
    confidence : float, optional
        Confidence level of the bootstrap bands, in ``(0, 1)``. Default 0.95.
    seed : int, optional
        RNG seed for the bootstrap resampling; fully determines the bands.
        Default 0.

    Returns
    -------
    FragilityResult
        The Phase 2 handoff artifact (spec §2).
    """
    grid = np.asarray(conditioning_grid, dtype=np.float64)
    fm_stat = np.asarray(failure_matrix_stat, dtype=bool)
    fm_tran = np.asarray(failure_matrix_tran, dtype=bool)

    p_f_static_raw = fm_stat.mean(axis=0)
    p_f_trans_raw = fm_tran.mean(axis=0)

    p_f_static_fit = fit_lognormal_fragility(grid, p_f_static_raw)
    p_f_trans_fit = fit_lognormal_fragility(grid, p_f_trans_raw)

    bands = _bootstrap_bands(fm_stat, fm_tran, grid, n_bootstrap, confidence, seed)

    return FragilityResult(
        conditioning_grid=grid,
        P_f_static_raw=p_f_static_raw,
        P_f_trans_raw=p_f_trans_raw,
        P_f_static_fit=p_f_static_fit,
        P_f_trans_fit=p_f_trans_fit,
        bootstrap_bands=bands,
        theta_matrix=np.asarray(theta_matrix, dtype=np.float64),
        param_names=list(param_names),
        failure_matrix_stat=fm_stat,
        failure_matrix_tran=fm_tran,
        metadata=metadata,
    )


@dataclass(frozen=True)
class FragilityResult:
    """The Phase 2 handoff artifact: fitted curves plus the retained raw data.

    The non-negotiable Phase 2 payload (spec §2, §8). Field order follows the
    spec §2 listing. ``theta_matrix`` and ``failure_matrix_tran`` let Phase 2
    re-run M8 Accept-Reject filtering on the prior; ``failure_matrix_stat``
    enables the survival-discrimination decomposition (spec §8). Persisted via
    :meth:`save` / :meth:`load` (HDF5 + JSON sidecar).

    Attributes
    ----------
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads [m above datum].
    P_f_static_raw, P_f_trans_raw : numpy.ndarray, shape (N_h,)
        Monte Carlo point estimates (per-column failure fractions).
    P_f_static_fit, P_f_trans_fit : LognormFragility
        The separately fitted lognormal fragility curves.
    bootstrap_bands : dict of str to (numpy.ndarray, numpy.ndarray)
        ``{'static': (lo, hi), 'transient': (lo, hi)}``, each band shape
        ``(N_h,)`` (spec §11).
    theta_matrix : numpy.ndarray, shape (N, 7)
        The prior sample matrix, retained for Phase 2 (spec §2, §8).
    param_names : list of str
        Column names of ``theta_matrix``.
    failure_matrix_stat, failure_matrix_tran : numpy.ndarray, shape (N, N_h)
        Boolean static / transient failure matrices, retained (spec §2, §8).
    metadata : dict
        Provenance / config-snapshot block; persisted to the JSON sidecar.
    """

    conditioning_grid: NDArray[np.float64]
    P_f_static_raw: NDArray[np.float64]
    P_f_trans_raw: NDArray[np.float64]
    P_f_static_fit: LognormFragility
    P_f_trans_fit: LognormFragility
    bootstrap_bands: dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]
    theta_matrix: NDArray[np.float64]
    param_names: list[str]
    failure_matrix_stat: NDArray[np.bool_]
    failure_matrix_tran: NDArray[np.bool_]
    metadata: dict[str, Any]

    @staticmethod
    def _sidecar_path(path: Path) -> Path:
        """Return the JSON metadata sidecar path next to the HDF5 file."""
        return path.with_suffix(".json")

    def save(self, path: str | Path) -> None:
        """Persist to an HDF5 file plus a JSON metadata sidecar (spec §2, §8).

        The large arrays (``theta_matrix``, ``conditioning_grid``, the raw point
        estimates, both bool failure matrices and the bootstrap bands) go to the
        HDF5 file at ``path``, with the fitted ``(mu, sigma)`` as root attributes
        and ``param_names`` as a string dataset. The ``metadata`` block is
        written to a JSON sidecar at ``path`` with a ``.json`` suffix.

        On-disk dataset names follow the spec §8 HDF5 schema exactly —
        ``/failure_matrix_static`` and ``/failure_matrix_trans`` — which differ
        from the spec §2 :class:`FragilityResult` field names
        (``failure_matrix_stat`` / ``failure_matrix_tran``); the spec is itself
        inconsistent between §2 and §8, so :meth:`save` / :meth:`load` map between
        the two namings rather than picking one. The ``metadata`` block lives in
        the JSON sidecar (spec §2/§8 "Persistence format"), not in the HDF5 attrs
        the §8 schema *lists*, because those attrs cannot hold ``None`` (e.g.
        ``tau_aq``) or nested dicts (``prior_means``, the config snapshot); the
        HDF5 root attrs instead carry the fitted ``(mu, sigma)``.

        Parameters
        ----------
        path : str or pathlib.Path
            Destination HDF5 path (e.g. ``results/xs_historical.h5``). The
            sidecar is the same path with a ``.json`` suffix.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        string_dtype = h5py.string_dtype(encoding="utf-8")
        with h5py.File(path, "w") as handle:
            handle.create_dataset("theta_matrix", data=self.theta_matrix)
            handle.create_dataset("conditioning_grid", data=self.conditioning_grid)
            handle.create_dataset("P_f_static_raw", data=self.P_f_static_raw)
            handle.create_dataset("P_f_trans_raw", data=self.P_f_trans_raw)
            # Spec §8 dataset names (static/trans), not the §2 field names.
            handle.create_dataset(
                "failure_matrix_static",
                data=np.asarray(self.failure_matrix_stat, dtype=bool),
            )
            handle.create_dataset(
                "failure_matrix_trans",
                data=np.asarray(self.failure_matrix_tran, dtype=bool),
            )
            handle.create_dataset(
                "param_names",
                data=np.array(self.param_names, dtype=object),
                dtype=string_dtype,
            )

            bands = handle.create_group("bootstrap_bands")
            static_lo, static_hi = self.bootstrap_bands["static"]
            trans_lo, trans_hi = self.bootstrap_bands["transient"]
            bands.create_dataset("static_lo", data=np.asarray(static_lo))
            bands.create_dataset("static_hi", data=np.asarray(static_hi))
            bands.create_dataset("trans_lo", data=np.asarray(trans_lo))
            bands.create_dataset("trans_hi", data=np.asarray(trans_hi))

            handle.attrs["fit_static_mu"] = float(self.P_f_static_fit.mu)
            handle.attrs["fit_static_sigma"] = float(self.P_f_static_fit.sigma)
            handle.attrs["fit_trans_mu"] = float(self.P_f_trans_fit.mu)
            handle.attrs["fit_trans_sigma"] = float(self.P_f_trans_fit.sigma)

        sidecar = self._sidecar_path(path)
        with open(sidecar, "w", encoding="utf-8") as handle:
            json.dump(self.metadata, handle, indent=2, sort_keys=False)

    @classmethod
    def load(cls, path: str | Path) -> FragilityResult:
        """Reconstruct a :class:`FragilityResult` from the HDF5 + JSON pair.

        Inverse of :meth:`save`: reads the arrays and fitted parameters from the
        HDF5 file at ``path`` and the metadata from the JSON sidecar. Both
        failure matrices come back as ``bool`` and every metadata field
        round-trips with its JSON-native Python type (spec §2, §8).

        Parameters
        ----------
        path : str or pathlib.Path
            The HDF5 path written by :meth:`save`.

        Returns
        -------
        FragilityResult
            The reconstructed handoff artifact.
        """
        path = Path(path)
        with h5py.File(path, "r") as handle:
            theta_matrix = handle["theta_matrix"][:]
            conditioning_grid = handle["conditioning_grid"][:]
            p_f_static_raw = handle["P_f_static_raw"][:]
            p_f_trans_raw = handle["P_f_trans_raw"][:]
            # Spec §8 dataset names (static/trans) -> §2 field names (stat/tran).
            failure_matrix_stat = handle["failure_matrix_static"][:].astype(bool)
            failure_matrix_tran = handle["failure_matrix_trans"][:].astype(bool)
            param_names = [str(name) for name in handle["param_names"].asstr()[:]]

            bands_group = handle["bootstrap_bands"]
            bootstrap_bands = {
                "static": (
                    bands_group["static_lo"][:],
                    bands_group["static_hi"][:],
                ),
                "transient": (
                    bands_group["trans_lo"][:],
                    bands_group["trans_hi"][:],
                ),
            }

            p_f_static_fit = LognormFragility(
                mu=float(handle.attrs["fit_static_mu"]),
                sigma=float(handle.attrs["fit_static_sigma"]),
            )
            p_f_trans_fit = LognormFragility(
                mu=float(handle.attrs["fit_trans_mu"]),
                sigma=float(handle.attrs["fit_trans_sigma"]),
            )

        with open(cls._sidecar_path(path), encoding="utf-8") as handle:
            metadata = json.load(handle)

        return cls(
            conditioning_grid=conditioning_grid,
            P_f_static_raw=p_f_static_raw,
            P_f_trans_raw=p_f_trans_raw,
            P_f_static_fit=p_f_static_fit,
            P_f_trans_fit=p_f_trans_fit,
            bootstrap_bands=bootstrap_bands,
            theta_matrix=theta_matrix,
            param_names=param_names,
            failure_matrix_stat=failure_matrix_stat,
            failure_matrix_tran=failure_matrix_tran,
            metadata=metadata,
        )
