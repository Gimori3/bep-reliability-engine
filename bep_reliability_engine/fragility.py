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
conditioning head ``h``, parameterized in the load excess above a datum::

    P_f(h) = Phi((ln(h - datum_m) - mu) / sigma)

with ``mu`` and ``sigma`` the location and scale of the lognormal "capacity"
excess (the mean and standard deviation of ``ln(capacity - datum_m)``). This is
the :class:`LognormFragility` curve. The orchestrator passes ``datum_m =
z_toe`` (the exit-point elevation), which makes the fitted parameters
datum-invariant and physically anchored — the load variable is the stage
excess the driving head ``r_e * (h - z_toe)`` is linear in — instead of the
vertical-reference-dependent ``ln(absolute MSL stage)``; ``datum_m = 0``
reproduces the original spec §2 ``ln h`` form. The fit consumes the *empirical
point set* ``(conditioning_grid, P_f_raw)`` — the Monte Carlo point estimates —
rather than per-realization capacities, because a lognormal fragility is a
straight line in probit space::

    Phi^-1(P_f) = (1/sigma) * ln(h - datum_m) - mu/sigma

so a least-squares line through ``(ln(h_i - datum), Phi^-1(P_f_i))`` recovers
``sigma = 1/slope`` and ``mu = -intercept/slope`` exactly when the points lie on
a true curve (:func:`fit_lognormal_fragility`). The line is fitted with
inverse-variance probit weights (delta method: ``Var(Phi^-1(p_hat)) ~=
p(1-p)/(N phi(z)^2)``), so noisy deep-tail levels — a P_f carried by one or two
failing realizations — no longer weigh as much as well-resolved mid-curve
levels. Degenerate points where ``P_f`` is exactly 0 or 1 (probit ``= -+inf``)
are masked before the fit.

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

Degenerate replicates (tail-dominated grids) are skipped, never fatal: a
resample whose point set cannot be refit (fewer than two interior levels, or a
non-increasing probit slope) contributes NaN to that curve only, the band is
the ``nanpercentile`` over the surviving replicates, a ``UserWarning`` reports
the skipped fraction, and the per-curve skip counts are recorded in
``metadata['bootstrap_degenerate_replicates']``. This is the fix for the
observed post-sweep crash on a deep-tail production grid (2026-07-03).

Length-effect upscaling (thesis §"Length Effect Upscaling")
-----------------------------------------------------------
:func:`upscale_length_effect` provides the weakest-link transform
``P_f,BEP = 1 - (1 - P_f,cs)^(L_seg/lambda_ac)`` from a per-cross-section curve
to the 200 m segment level. It is a documented post-processing step, **not wired
into the default pipeline**: the autocorrelation length ``lambda_ac`` is still
undetermined, so the function takes ``n_eff`` explicitly and ``run.py`` never
calls it. Apply it to the fitted prior/posterior curve once ``lambda_ac`` is fixed.

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
import logging
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

logger = logging.getLogger(__name__)

__all__ = [
    "PF_COV_TARGET",
    "LognormFragility",
    "FragilityResult",
    "binomial_ci",
    "fit_lognormal_fragility",
    "assemble_fragility",
    "mc_cov_of_pf",
    "save_raw_failure_payload",
    "upscale_length_effect",
]

# Spec §11 convergence target: CoV of the Monte Carlo P_f estimator across the
# relevant failure range (Schweckendiek 2014 practice). Recorded next to the
# computed per-level CoVs in metadata['mc_convergence'] so every run carries
# its own §11 sufficiency verdict instead of assuming it.
PF_COV_TARGET: float = 0.05


def mc_cov_of_pf(p_f: NDArray[np.float64], n_realizations: int) -> list[float | None]:
    """Coefficient of variation of the Monte Carlo P_f estimator, per level.

    For the binomial point estimate ``p_hat = k / N`` the estimator CoV is::

        CoV(p_hat) = sqrt((1 - p) / (N * p))

    evaluated here at the observed ``p_hat`` per conditioning level (spec §11).
    Levels with ``p`` exactly 0 or 1 carry no interior information (the CoV is
    undefined at 0 and vacuous at 1) and map to ``None`` — deliberately not
    NaN, so the list stays JSON-round-trip-exact in the metadata sidecar.

    Parameters
    ----------
    p_f : numpy.ndarray, shape (N_h,)
        Empirical failure probabilities (the Monte Carlo point estimates).
    n_realizations : int
        Number of realizations N behind each estimate.

    Returns
    -------
    list of (float or None)
        Estimator CoV per level; ``None`` where ``p_f`` is 0 or 1.
    """
    covs: list[float | None] = []
    for p in np.asarray(p_f, dtype=np.float64):
        if 0.0 < p < 1.0:
            covs.append(float(np.sqrt((1.0 - p) / (n_realizations * p))))
        else:
            covs.append(None)
    return covs


def binomial_ci(
    p_f: NDArray[np.float64],
    n_realizations: int,
    confidence: float = 0.95,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Clopper-Pearson exact binomial CIs on the raw point estimates (ADR-0024).

    For the failure count ``k = round(p * N)`` at each conditioning level
    (exact, since the point estimates are means of a boolean matrix)::

        lower = 0                                   if k == 0
              = Beta.ppf(alpha/2,     k,     N-k+1) otherwise
        upper = 1                                   if k == N
              = Beta.ppf(1 - alpha/2, k + 1, N-k)   otherwise

    with ``alpha = 1 - confidence``. Exact (conservative) coverage — the
    standard choice for rare-event counts, where the deep-tail levels are
    carried by a handful of failing realizations. Computed always, for both
    branches, at every section: at tail-only branches (ADR-0024) the raw
    points with these CIs ARE the fragility deliverable, and at bracketed
    branches they complement the bootstrap bands (which quantify the fitted
    curve, not the points).

    Parameters
    ----------
    p_f : numpy.ndarray, shape (N_h,)
        Empirical failure probabilities (per-column means of the boolean
        failure matrix).
    n_realizations : int
        Number of realizations N behind each estimate.
    confidence : float, optional
        Two-sided confidence level, in ``(0, 1)``. Default 0.95.

    Returns
    -------
    tuple of (numpy.ndarray, numpy.ndarray)
        ``(lower, upper)`` bounds, each shape ``(N_h,)``, satisfying
        ``lower <= p_f <= upper`` elementwise.
    """
    from scipy.stats import beta

    p = np.asarray(p_f, dtype=np.float64)
    n = int(n_realizations)
    k = np.rint(p * n).astype(np.int64)
    alpha = 1.0 - float(confidence)

    lower = np.zeros_like(p)
    upper = np.ones_like(p)
    at_floor = k == 0
    at_ceiling = k == n
    if np.any(~at_floor):
        kk = k[~at_floor]
        lower[~at_floor] = beta.ppf(alpha / 2.0, kk, n - kk + 1)
    if np.any(~at_ceiling):
        kk = k[~at_ceiling]
        upper[~at_ceiling] = beta.ppf(1.0 - alpha / 2.0, kk + 1, n - kk)
    return lower, upper


@dataclass(frozen=True)
class LognormFragility:
    """A fitted lognormal fragility curve in the load excess ``h - datum_m``.

    ``P_f(h) = Phi((ln(h - datum_m) - mu)/sigma)`` for ``h > datum_m`` and
    exactly 0 at or below the datum. The two-parameter handoff curve of spec §2
    (``P_f_static_fit`` / ``P_f_trans_fit``). ``mu`` and ``sigma`` are the
    location and scale of the lognormal capacity *excess* (mean and standard
    deviation of ``ln(capacity - datum_m)``), so the median capacity is
    ``datum_m + exp(mu)`` and ``P_f(datum_m + exp(mu)) = 0.5``.

    Anchoring the curve at the exit-point elevation ``z_toe`` makes the fitted
    parameters datum-invariant and physically meaningful (the load variable is
    the stage excess above the seepage exit, the quantity the driving head
    ``r_e * (h - z_toe)`` is linear in); ``datum_m = 0`` reproduces the
    original spec §2 ``ln(h)`` parametrization for backward compatibility.

    Attributes
    ----------
    mu : float
        Location parameter (mean of ``ln`` capacity excess) [ln-m].
    sigma : float
        Scale parameter (std of ``ln`` capacity excess) [-]; ``> 0``.
    datum_m : float
        Load datum [m above the vertical reference]; the curve lives in
        ``h - datum_m``. Default ``0.0`` (the original absolute-stage form).
    """

    mu: float
    sigma: float
    datum_m: float = 0.0

    def probability_of_failure(
        self, conditioning_level: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """Evaluate the fragility curve at one or more conditioning heads.

        Parameters
        ----------
        conditioning_level : float or numpy.ndarray
            Conditioning head(s) h [m above the vertical reference]. Levels at
            or below ``datum_m`` return exactly 0 (no load excess above the
            exit elevation).

        Returns
        -------
        float or numpy.ndarray
            ``Phi((ln(h - datum_m) - mu)/sigma)`` where ``h > datum_m``, else
            0.0: a Python float for scalar input, an array of the same shape
            for array input.
        """
        head = np.asarray(conditioning_level, dtype=np.float64)
        excess = head - self.datum_m
        positive = excess > 0.0
        # Guard the log argument so sub-datum levels never produce NaN; the
        # placeholder 1.0 is discarded by the final where().
        safe_excess = np.where(positive, excess, 1.0)
        probability = np.where(
            positive,
            norm.cdf((np.log(safe_excess) - self.mu) / self.sigma),
            0.0,
        )
        return float(probability) if probability.ndim == 0 else probability


def fit_lognormal_fragility(
    conditioning_grid: NDArray[np.float64],
    p_f: NDArray[np.float64],
    datum_m: float = 0.0,
) -> LognormFragility:
    """Fit a lognormal fragility curve to an empirical ``(h, P_f)`` point set.

    Fits ``P_f(h) = Phi((ln(h - datum_m) - mu)/sigma)`` by weighted least
    squares in probit space: a lognormal fragility is the straight line
    ``Phi^-1(P_f) = (1/sigma) ln(h - datum) - mu/sigma``, so a degree-1 fit of
    ``Phi^-1(P_f)`` against ``ln(h - datum)`` gives ``sigma = 1/slope`` and
    ``mu = -intercept/slope``. Points with ``P_f`` exactly 0 or 1 (probit
    ``-+inf``), and any point at or below the datum, carry no finite
    information and are dropped before the fit.

    **Deep-tail weighting.** The probit-transformed Monte Carlo estimates are
    strongly heteroscedastic: by the delta method
    ``Var(Phi^-1(p_hat)) ~= p (1 - p) / (N * phi(z)^2)`` with ``z =
    Phi^-1(p)``, so a P_f ~ 1e-4 level (one or two failing realizations)
    carries orders of magnitude more probit noise than a mid-curve level. The
    fit therefore uses inverse-standard-deviation weights ``w = phi(z) /
    sqrt(p (1 - p))`` (the common factor ``sqrt(N)`` cancels), which is
    standard probit-regression GLS weighting. Points lying exactly on a true
    lognormal curve are still recovered exactly, weights or not.

    Parameters
    ----------
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads h [m above the vertical reference].
    p_f : numpy.ndarray, shape (N_h,)
        Empirical failure probabilities at each conditioning level, in
        ``[0, 1]`` (the Monte Carlo point estimates).
    datum_m : float, optional
        Load datum [m]; the fit variable is the excess ``h - datum_m``.
        Default ``0.0`` (the original absolute-stage ``ln h`` form). The
        orchestrator passes the exit-point elevation ``z_toe`` so the fitted
        parameters are datum-invariant and physically anchored.

    Returns
    -------
    LognormFragility
        The fitted curve, carrying ``datum_m``.

    Raises
    ------
    ValueError
        If fewer than two interior (``0 < P_f < 1``, ``h > datum_m``) points
        remain, or the fitted slope is non-positive (not a monotone-increasing
        fragility).
    """
    grid = np.asarray(conditioning_grid, dtype=np.float64)
    probabilities = np.asarray(p_f, dtype=np.float64)

    excess = grid - datum_m
    interior = (probabilities > 0.0) & (probabilities < 1.0) & (excess > 0.0)
    if int(np.count_nonzero(interior)) < 2:
        raise ValueError(
            "fit_lognormal_fragility needs at least two interior (0 < P_f < 1, "
            f"h > datum) points; got {int(np.count_nonzero(interior))}."
        )

    ln_excess = np.log(excess[interior])
    p_interior = probabilities[interior]
    probit = norm.ppf(p_interior)
    # Inverse-std weights from the delta method (see docstring); numpy.polyfit
    # applies w to the unsquared residuals, i.e. minimizes sum (w * r)^2.
    weights = norm.pdf(probit) / np.sqrt(p_interior * (1.0 - p_interior))
    slope, intercept = np.polyfit(ln_excess, probit, 1, w=weights)
    if not slope > 0.0:
        raise ValueError(
            f"fitted probit slope {slope!r} is non-positive; the point set is "
            "not a monotone-increasing fragility."
        )

    sigma = 1.0 / slope
    mu = -intercept / slope
    return LognormFragility(mu=float(mu), sigma=float(sigma), datum_m=float(datum_m))


def upscale_length_effect(
    p_f_cross_section: float | NDArray[np.float64],
    n_eff: float,
) -> float | NDArray[np.float64]:
    """Weakest-link upscaling of a per-cross-section P_f to the segment level.

    Implements the thesis "Length Effect Upscaling" relation::

        P_f,BEP(h) = 1 - (1 - P_f,cs(h)) ** n_eff,    n_eff = L_seg / lambda_ac

    Piping is a weakest-link mechanism, so a finite 200 m segment containing
    ``n_eff`` effectively independent cross-sections fails if *any* of them does;
    a single representative cross-section therefore under-states the segment
    failure probability (Kanning 2012; Hoffmans 2014). The exact expression is
    retained (not the ``n_eff * P_f`` linearization) so the high-loading tail is
    not under-estimated.

    .. important::
       **Not yet wired into the default Phase 1 pipeline.** The autocorrelation
       length ``lambda_ac`` of the governing parameters (D_bl, k_aquifer) — and
       hence ``n_eff`` — is still undetermined (it must be estimated from the OYO
       longitudinal profile / literature; thesis §"The Length Effect and Spatial
       Autocorrelation"). This function therefore takes ``n_eff`` as an explicit
       argument with **no default**: the caller supplies it once ``lambda_ac`` is
       fixed, and applies the transform to the fitted prior/posterior fragility
       curve as a post-processing step. ``run.py`` does not call it.

    Parameters
    ----------
    p_f_cross_section : float or numpy.ndarray
        Per-cross-section conditional failure probability P_f,cs(h), in
        ``[0, 1]`` (a scalar, or the curve sampled on a head grid).
    n_eff : float
        Effective number of independent cross-sections in the segment,
        ``L_seg / lambda_ac``; ``>= 1`` for a segment longer than one
        autocorrelation length (``n_eff = 1`` returns the input unchanged).

    Returns
    -------
    float or numpy.ndarray
        The segment-level conditional failure probability P_f,BEP(h), the
        quantity passed into the Phase 3 series-system integration. Same shape
        as ``p_f_cross_section``.

    Raises
    ------
    ValueError
        If ``n_eff < 1`` or any ``p_f_cross_section`` is outside ``[0, 1]``.
    """
    if not n_eff >= 1.0:
        raise ValueError(f"n_eff must be >= 1 (L_seg / lambda_ac), got {n_eff!r}.")
    p_cs = np.asarray(p_f_cross_section, dtype=np.float64)
    if np.any((p_cs < 0.0) | (p_cs > 1.0)):
        raise ValueError("p_f_cross_section must lie in [0, 1].")
    p_seg = 1.0 - np.power(1.0 - p_cs, n_eff)
    return float(p_seg) if p_seg.ndim == 0 else p_seg


def _bootstrap_bands(
    failure_matrix_stat: NDArray[np.bool_],
    failure_matrix_tran: NDArray[np.bool_],
    conditioning_grid: NDArray[np.float64],
    n_bootstrap: int,
    confidence: float,
    seed: int,
    datum_m: float = 0.0,
) -> tuple[
    dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]],
    dict[str, int],
]:
    """Bootstrap ``(lo, hi)`` bands on the fitted curves (spec §11).

    Each replicate draws one row index set with replacement and applies it to
    both matrices (realizations are shared across the two limit states,
    ADR-0002), refits each curve, and evaluates it on the grid. The band is the
    per-level ``confidence`` percentile interval of those refit curves. The RNG
    depends only on ``seed`` (not ``confidence``), so the resamples are shared
    across confidence levels.

    Degenerate replicates — resamples whose point set has fewer than two
    interior levels or a non-increasing probit slope, which occurs on
    tail-dominated grids where an interior level is carried by a handful of
    rows — are **skipped, never fatal**: the replicate's row is left NaN for
    that curve only (the shared row draw still feeds the other curve), the
    band is taken over the surviving replicates via ``nanpercentile``, and a
    :class:`UserWarning` reports the skipped fraction. If *every* replicate
    degenerates for a curve, its band is all-NaN. The per-curve skip counts
    are returned so :func:`assemble_fragility` can record them in metadata.

    Returns
    -------
    tuple of (dict, dict)
        ``(bands, degenerate)``: the ``{'static'|'transient': (lo, hi)}`` band
        dict and the per-curve degenerate-replicate counts.
    """
    n_realizations = failure_matrix_stat.shape[0]
    n_levels = conditioning_grid.shape[0]
    rng = np.random.default_rng(seed)

    boot = {
        "static": np.full((n_bootstrap, n_levels), np.nan),
        "transient": np.full((n_bootstrap, n_levels), np.nan),
    }
    matrices = {"static": failure_matrix_stat, "transient": failure_matrix_tran}
    degenerate = {"static": 0, "transient": 0}
    for b in range(n_bootstrap):
        rows = rng.integers(0, n_realizations, size=n_realizations)
        for key, matrix in matrices.items():
            p_f = matrix[rows].mean(axis=0)
            try:
                fit = fit_lognormal_fragility(conditioning_grid, p_f, datum_m)
            except ValueError:
                degenerate[key] += 1
                continue
            boot[key][b] = fit.probability_of_failure(conditioning_grid)

    lower_pct = 100.0 * (1.0 - confidence) / 2.0
    upper_pct = 100.0 * (1.0 + confidence) / 2.0
    bands: dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]] = {}
    for key in ("static", "transient"):
        n_skipped = degenerate[key]
        if n_skipped:
            warnings.warn(
                f"{n_skipped} of {n_bootstrap} bootstrap replicates were "
                f"degenerate for the {key} fragility curve (fewer than two "
                "interior points or non-increasing probit slope) and were "
                "skipped; the band uses the remaining "
                f"{n_bootstrap - n_skipped} replicates. A large skipped "
                "fraction indicates a tail-dominated conditioning grid "
                "(spec §11).",
                UserWarning,
                stacklevel=3,
            )
        if n_skipped == n_bootstrap:
            bands[key] = (
                np.full(n_levels, np.nan),
                np.full(n_levels, np.nan),
            )
            continue
        bands[key] = (
            np.nanpercentile(boot[key], lower_pct, axis=0),
            np.nanpercentile(boot[key], upper_pct, axis=0),
        )
    return bands, degenerate


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
    datum_m: float = 0.0,
) -> FragilityResult:
    """Assemble the Phase 2 :class:`FragilityResult` from the raw matrices (M9).

    Computes the per-column failure fractions as the static and transient
    empirical point estimates, fits a separate :class:`LognormFragility` to each
    (spec §2), attaches bootstrap confidence bands (spec §11) and the always-on
    Clopper-Pearson binomial CIs on the raw points (ADR-0024), and retains the
    ``theta_matrix`` and *both* failure matrices for the Phase 2 / survival-
    discrimination handoff (spec §8).

    **Never aborts after a completed sweep (ADR-0024).** A branch whose point
    set cannot be fit (fewer than two interior points, or a non-increasing
    probit slope) yields ``P_f_*_fit = None`` instead of raising. Each branch's
    deliverable form is decided by the data-driven bracketing criterion
    ``max(P_f_raw) >= 0.5`` and recorded under
    ``metadata['fragility_deliverable']``: a bracketed branch with a fit
    delivers the fitted lognormal; an unbracketed branch delivers the raw tail
    points with their binomial CIs (per the accepted ADR-0024 reframing, the
    intended primary presentation where the transition is unreachable — the
    static-transient bias is then reported as per-level probability ratios),
    with any existing fit stored but labelled ``extrapolative_only``.

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
    datum_m : float, optional
        Load datum [m] for the fits (see :func:`fit_lognormal_fragility`):
        the curves are lognormal in the excess ``h - datum_m``. Default
        ``0.0`` (the original absolute-stage form); the orchestrator passes
        the exit-point elevation ``z_toe``. Recorded, with the weighting
        scheme, under ``metadata['fragility_fit']``.

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

    # Optional fits (ADR-0024): a degenerate point set — fewer than two
    # interior levels, or a non-increasing probit slope, both raised by the
    # fitter — yields None instead of aborting a completed sweep. The raw
    # matrices and the binomial CIs below carry the branch either way.
    def _fit_or_none(
        p_raw: NDArray[np.float64], branch: str
    ) -> LognormFragility | None:
        try:
            return fit_lognormal_fragility(grid, p_raw, datum_m)
        except ValueError as error:
            logger.warning(
                "No lognormal fit for the %s branch (%s); the branch is "
                "carried by its raw points and binomial CIs (ADR-0024).",
                branch,
                error,
            )
            return None

    p_f_static_fit = _fit_or_none(p_f_static_raw, "static")
    p_f_trans_fit = _fit_or_none(p_f_trans_raw, "transient")

    bands, degenerate = _bootstrap_bands(
        fm_stat, fm_tran, grid, n_bootstrap, confidence, seed, datum_m
    )

    # Always-on exact binomial CIs on the raw points (ADR-0024), both branches.
    n_realizations = int(fm_stat.shape[0])
    ci_confidence = 0.95
    cis = {
        "static": binomial_ci(p_f_static_raw, n_realizations, ci_confidence),
        "transient": binomial_ci(p_f_trans_raw, n_realizations, ci_confidence),
    }

    # Annotate a shallow copy of the metadata (never mutate the caller's dict)
    # with the degenerate-replicate counts, so a tail-dominated grid is visible
    # in the persisted provenance and not only in a transient warning.
    metadata = dict(metadata)
    metadata["bootstrap_degenerate_replicates"] = {
        "static": int(degenerate["static"]),
        "transient": int(degenerate["transient"]),
        "n_bootstrap": int(n_bootstrap),
    }

    # Spec §11 convergence monitoring: compute (not assume) the CoV of the
    # Monte Carlo P_f estimator per level and per branch, with the worst
    # interior CoV and the target verdict recorded for the run's provenance.
    cov_static = mc_cov_of_pf(p_f_static_raw, n_realizations)
    cov_trans = mc_cov_of_pf(p_f_trans_raw, n_realizations)

    def _worst_and_verdict(
        covs: list[float | None],
    ) -> tuple[float | None, bool | None]:
        interior = [c for c in covs if c is not None]
        if not interior:
            return None, None
        worst = max(interior)
        return worst, bool(worst <= PF_COV_TARGET)

    # Fit provenance: which load variable and weighting produced (mu, sigma),
    # so the parameters are interpretable without reading the code version.
    metadata["fragility_fit"] = {
        "load_variable": "conditioning_level_minus_datum",
        "datum_m": float(datum_m),
        "weighting": "inverse_variance_probit",
    }

    max_cov_static, meets_static = _worst_and_verdict(cov_static)
    max_cov_trans, meets_trans = _worst_and_verdict(cov_trans)
    metadata["mc_convergence"] = {
        "n_realizations": n_realizations,
        "cov_target": float(PF_COV_TARGET),
        "cov_pf_static": cov_static,
        "cov_pf_trans": cov_trans,
        "max_cov_static": max_cov_static,
        "max_cov_trans": max_cov_trans,
        "meets_cov_target_static": meets_static,
        "meets_cov_target_trans": meets_trans,
    }

    # ADR-0024 deliverable flag: the data-driven bracketing criterion decides,
    # per branch, whether the fitted lognormal is the deliverable or the raw
    # tail points with their binomial CIs are (the intended primary
    # presentation where the transition is unreachable — reported against the
    # other branch as per-level probability ratios, not a fallback). A fit
    # that exists on an unbracketed branch is stored but labelled
    # extrapolative: it describes the fit, not the site, beyond the data.
    def _deliverable(
        p_raw: NDArray[np.float64], fit: LognormFragility | None
    ) -> dict[str, Any]:
        bracketed = bool(np.max(p_raw) >= 0.5)
        if bracketed and fit is not None:
            form, fit_role = "fitted_lognormal", "deliverable"
        elif fit is not None:
            form, fit_role = "raw_tail_binomial", "extrapolative_only"
        else:
            form, fit_role = "raw_tail_binomial", "unavailable"
        return {
            "form": form,
            "transition_bracketed": bracketed,
            "max_p_f_raw": float(np.max(p_raw)),
            "fit_available": fit is not None,
            "fit_role": fit_role,
        }

    metadata["fragility_deliverable"] = {
        "static": _deliverable(p_f_static_raw, p_f_static_fit),
        "transient": _deliverable(p_f_trans_raw, p_f_trans_fit),
        "ci_method": "clopper_pearson",
        "ci_level": float(ci_confidence),
    }

    return FragilityResult(
        conditioning_grid=grid,
        P_f_static_raw=p_f_static_raw,
        P_f_trans_raw=p_f_trans_raw,
        P_f_static_fit=p_f_static_fit,
        P_f_trans_fit=p_f_trans_fit,
        bootstrap_bands=bands,
        binomial_ci=cis,
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
    P_f_static_fit, P_f_trans_fit : LognormFragility or None
        The separately fitted lognormal fragility curves, or ``None`` where
        the branch's point set could not be fit (ADR-0024: fewer than two
        interior levels or a non-increasing probit slope — the branch is
        then carried by its raw points and binomial CIs, and a completed
        sweep never aborts). ``metadata['fragility_deliverable']`` records,
        per branch, whether an existing fit is the deliverable or is stored
        as extrapolative only.
    bootstrap_bands : dict of str to (numpy.ndarray, numpy.ndarray)
        ``{'static': (lo, hi), 'transient': (lo, hi)}``, each band shape
        ``(N_h,)`` (spec §11). Uncertainty of the *fitted curve*.
    binomial_ci : dict of str to (numpy.ndarray, numpy.ndarray)
        ``{'static': (lo, hi), 'transient': (lo, hi)}``, each shape
        ``(N_h,)``: always-on Clopper-Pearson exact CIs on the *raw points*
        (ADR-0024; additive field per the ADR-0017 contract-extension
        precedent). At unbracketed (tail-only) branches these, with the raw
        points, ARE the fragility deliverable.
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
    P_f_static_fit: LognormFragility | None
    P_f_trans_fit: LognormFragility | None
    bootstrap_bands: dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]
    binomial_ci: dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]
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

            # ADR-0024: always-on Clopper-Pearson CIs on the raw points.
            cis = handle.create_group("binomial_ci")
            ci_static_lo, ci_static_hi = self.binomial_ci["static"]
            ci_trans_lo, ci_trans_hi = self.binomial_ci["transient"]
            cis.create_dataset("static_lo", data=np.asarray(ci_static_lo))
            cis.create_dataset("static_hi", data=np.asarray(ci_static_hi))
            cis.create_dataset("trans_lo", data=np.asarray(ci_trans_lo))
            cis.create_dataset("trans_hi", data=np.asarray(ci_trans_hi))

            # Optional fits (ADR-0024): a missing fit is encoded as NaN attrs
            # (HDF5 attrs cannot hold None) and decoded back to None on load.
            def _fit_attrs(prefix: str, fit: LognormFragility | None) -> None:
                handle.attrs[f"{prefix}_mu"] = float(fit.mu) if fit else np.nan
                handle.attrs[f"{prefix}_sigma"] = float(fit.sigma) if fit else np.nan
                handle.attrs[f"{prefix}_datum_m"] = (
                    float(fit.datum_m) if fit else np.nan
                )

            _fit_attrs("fit_static", self.P_f_static_fit)
            _fit_attrs("fit_trans", self.P_f_trans_fit)

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

            # ADR-0024 CIs. Files written before the field existed carry no
            # group; the CI is a deterministic function of the retained
            # matrices, so legacy files load with identically recomputed
            # values rather than a missing field.
            if "binomial_ci" in handle:
                ci_group = handle["binomial_ci"]
                cis = {
                    "static": (
                        ci_group["static_lo"][:],
                        ci_group["static_hi"][:],
                    ),
                    "transient": (
                        ci_group["trans_lo"][:],
                        ci_group["trans_hi"][:],
                    ),
                }
            else:
                n_realizations = int(failure_matrix_stat.shape[0])
                cis = {
                    "static": binomial_ci(p_f_static_raw, n_realizations),
                    "transient": binomial_ci(p_f_trans_raw, n_realizations),
                }

            # Files written before the datum-anchored fit carry no datum
            # attrs; they load with the backward-compatible 0.0 (the original
            # absolute-stage ln(h) parametrization). NaN mu/sigma encode the
            # ADR-0024 None fit.
            def _fit_or_none_from_attrs(prefix: str) -> LognormFragility | None:
                mu = float(handle.attrs[f"{prefix}_mu"])
                sigma = float(handle.attrs[f"{prefix}_sigma"])
                if np.isnan(mu) or np.isnan(sigma):
                    return None
                return LognormFragility(
                    mu=mu,
                    sigma=sigma,
                    datum_m=float(handle.attrs.get(f"{prefix}_datum_m", 0.0)),
                )

            p_f_static_fit = _fit_or_none_from_attrs("fit_static")
            p_f_trans_fit = _fit_or_none_from_attrs("fit_trans")

        with open(cls._sidecar_path(path), encoding="utf-8") as handle:
            metadata = json.load(handle)

        return cls(
            conditioning_grid=conditioning_grid,
            P_f_static_raw=p_f_static_raw,
            P_f_trans_raw=p_f_trans_raw,
            P_f_static_fit=p_f_static_fit,
            P_f_trans_fit=p_f_trans_fit,
            bootstrap_bands=bootstrap_bands,
            binomial_ci=cis,
            theta_matrix=theta_matrix,
            param_names=param_names,
            failure_matrix_stat=failure_matrix_stat,
            failure_matrix_tran=failure_matrix_tran,
            metadata=metadata,
        )


def save_raw_failure_payload(
    path: str | Path,
    *,
    theta_matrix: NDArray[np.float64],
    param_names: list[str],
    conditioning_grid: NDArray[np.float64],
    failure_matrix_stat: NDArray[np.bool_],
    failure_matrix_tran: NDArray[np.bool_],
    metadata: dict[str, Any],
) -> None:
    """Persist the raw sweep payload (no fits) as a crash-recovery file.

    The sweep is the expensive part of a fragility run; the M9 fitting and
    bootstrap that follow can fail on a tail-dominated grid (degenerate probit
    point sets). The orchestrator therefore writes this payload *before* any
    fitting, so an assembly failure can never destroy a completed sweep: the
    raw arrays — everything Phase 2 filtering actually needs (spec §8) — stay
    recoverable on disk. On a successful run the orchestrator removes the
    recovery pair after the full :class:`FragilityResult` is saved.

    Dataset names follow the spec §8 HDF5 schema, identical to
    :meth:`FragilityResult.save` (``failure_matrix_static`` /
    ``failure_matrix_trans``), so recovery tooling reads one layout. The
    metadata block goes to a JSON sidecar at ``path`` with a ``.json`` suffix,
    exactly as for the full result.

    Parameters
    ----------
    path : str or pathlib.Path
        Destination HDF5 path; by convention the orchestrator uses the final
        result path with a ``.raw.h5`` suffix so a leftover recovery file is
        self-identifying.
    theta_matrix : numpy.ndarray, shape (N, 7)
        The prior sample matrix (spec §2, §8).
    param_names : list of str
        Canonical column names of ``theta_matrix``.
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads.
    failure_matrix_stat, failure_matrix_tran : numpy.ndarray, shape (N, N_h)
        Boolean static / transient failure indicators from the sweep.
    metadata : dict
        The provenance block (JSON-serializable), written to the sidecar.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    string_dtype = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.create_dataset(
            "theta_matrix", data=np.asarray(theta_matrix, dtype=np.float64)
        )
        handle.create_dataset(
            "conditioning_grid",
            data=np.asarray(conditioning_grid, dtype=np.float64),
        )
        handle.create_dataset(
            "failure_matrix_static",
            data=np.asarray(failure_matrix_stat, dtype=bool),
        )
        handle.create_dataset(
            "failure_matrix_trans",
            data=np.asarray(failure_matrix_tran, dtype=bool),
        )
        handle.create_dataset(
            "param_names",
            data=np.array(list(param_names), dtype=object),
            dtype=string_dtype,
        )

    sidecar = path.with_suffix(".json")
    with open(sidecar, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=False)
