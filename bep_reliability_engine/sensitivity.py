"""Variance-based global sensitivity analysis: designs, estimators, input maps.

Stage 6.5 (ADR-0033): the Sobol'-index machinery for the Phase 1 GSA,
grounded in Saltelli, Tarantola et al., *Global Sensitivity Analysis: The
Primer* (Wiley 2008) — first-order indices ``S_i = V[E(Y|X_i)]/V(Y)`` (the
Factor Prioritization setting, Primer §1.2.9/§4.3) and total-effect indices
``ST_i = E[V(Y|X_~i)]/V(Y)`` (the Factor Fixing setting, §1.2.13/§4.5), with
``ST_i - S_i`` as the interaction diagnostic.

This module follows the ``convergence.py`` pattern: **statistics only, physics
injected**. It knows nothing about limit states; the engine enters exclusively
through an output vector ``y`` the caller computes (see ``gsa_qoi`` for the M8
adapter and ``scripts/gsa_study.py`` for the driver).

Design and estimators (ADR-0033 §3)
-----------------------------------
The sample design is the Saltelli (2002) two-matrix scheme of Primer §4.6 in
its radial Saltelli et al. (2010) form: base matrices ``A`` and ``B`` (each
``(N, k)``) plus the ``k`` spliced matrices ``A_B^(i)`` (``A`` with column
``i`` replaced from ``B``), total cost ``N*(k+2)`` model runs for the full
``{S_i, ST_i}`` set. The matrices are drawn from an **Owen-scrambled Sobol'
sequence** in ``2k`` dimensions split ``A|B`` — the Primer §4.6 explicitly
recommends quasi-random sequences here, and scrambling makes independent
replicates an unbiased randomized-QMC error estimate (Owen 1997).

Estimators (Saltelli et al. 2010 best practice, superseding the Primer's
Eqs. (4.21)/(4.23) — the deliberate extension recorded in ADR-0033)::

    S_i  = mean( y_B * (y_ABi - y_A) ) / V         (Saltelli et al. 2010)
    ST_i = mean( (y_A - y_ABi)**2 ) / (2 * V)      (Jansen 1999)

with the mean and variance ``V`` of Y estimated from the pooled
``(y_A, y_B)`` sample (Primer p. 166 accuracy note). Both work unchanged for
binary outputs (failure indicators), where ``V = P_f * (1 - P_f)``.

Uncertainty (ADR-0033 §4): the primary statement is the replicate spread over
independent scramblings (:func:`aggregate_replicates`, Student-t CI); the
Primer's row-bootstrap (p. 166, after Archer et al.) is retained as the
cross-check (:func:`bootstrap_indices`). Small negative estimates for
noninfluential factors are expected (Primer p. 170) and must be judged
against their CI, not clipped.

Input space (ADR-0033 §2)
-------------------------
:class:`GsaInputSpace` maps the unit-hypercube design columns (the
*generators*) to physical engine inputs — the seven canonical theta marginals
(bit-identical arithmetic to M2 ``sampling.sample_theta``: the same
moment-matched lognormal map and the same bounds clip) plus the optional
independent seepage length L as the eighth column. Under the production
two-population coupling (ADR-0012) all generators map one-to-one onto
independent physical inputs and generator-space indices *are* physical-input
indices. Under the Nataf ``correlated`` companion the map applies the M2
Gaussian-copula construction, so the analysis lives in the space of the
independent copula generators (the Rosenblatt transform): the anchored
variable's index is its **full** (Kucherenko) contribution including the
correlated share, and the other pair member's index is its **independent**
(Mara-Tarantola decorrelated) contribution. Running both ``anchor``
orderings yields the complementary full/independent pairs.

References
----------
Saltelli et al. (2008) *The Primer* §1.2, §1.3, §4.3-4.6, §4.9; Saltelli
(2002) CPC 145; Saltelli et al. (2010) CPC 181; Jansen (1999) CPC 117;
Mara & Tarantola (2012) RESS 107; Kucherenko et al. (2012) CPC 183; Owen
(1997) SINUM 34. ADR-0033; spec §7 (input space), §12 fm7 (the C_e x k_aq
interaction this analysis quantifies).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm
from scipy.stats.qmc import Sobol

from bep_reliability_engine.sampling import PARAM_NAMES, MarginalSpec

logger = logging.getLogger(__name__)

__all__ = [
    "SobolIndices",
    "GsaInputSpace",
    "generate_design",
    "stack_evaluation_matrix",
    "split_outputs",
    "sobol_indices",
    "bootstrap_indices",
    "aggregate_replicates",
]

# Guard for the inverse-normal map: Owen-scrambled Sobol' points are strictly
# inside (0, 1) with probability 1 at 64-bit granularity, but the map must
# never emit +-inf. The floor is one 64-bit quantum; the ceiling is the
# largest float64 strictly below 1.
_U_FLOOR = float(2.0**-64)
_U_CEIL = float(np.nextafter(1.0, 0.0))

CorrelatedAnchor = Literal["k_aq", "d_70"]


# ============================================================================
# Design generation (Primer §4.6; Saltelli et al. 2010 radial form)
# ============================================================================
def generate_design(
    k: int,
    n_base: int,
    *,
    seed: int,
    scramble: bool = True,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Draw the base matrices ``A`` and ``B`` on the unit hypercube.

    One Sobol' sequence in ``2k`` dimensions supplies both matrices (the
    Primer §4.6 construction: "a (N, 2k) matrix ... two matrices of data (A
    and B), each containing half of the sample"), so ``A`` and ``B`` are
    mutually independent by the sequence's dimension-wise balance.

    Parameters
    ----------
    k : int
        Number of input factors (columns per matrix).
    n_base : int
        Base sample size N (rows per matrix). Must be a power of two so the
        Sobol' sequence retains its balance properties (scipy emits a
        ``UserWarning`` otherwise); enforced here.
    seed : int
        Seed for the Owen scrambling. The same seed reproduces the design
        bit-for-bit (docs/conventions.md: deterministic RNG seeds everywhere).
    scramble : bool, optional
        Owen-scramble the sequence (default True). Scrambling is what makes
        independent replicates an unbiased error estimate (ADR-0033 §4);
        ``False`` exists for didactic comparisons only.

    Returns
    -------
    u_a, u_b : numpy.ndarray, shape (n_base, k)
        The two base matrices, entries in the open unit interval.

    Raises
    ------
    ValueError
        If ``n_base`` is not a positive power of two or ``k < 1``.
    """
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}.")
    if n_base < 1 or (n_base & (n_base - 1)) != 0:
        raise ValueError(
            f"n_base must be a positive power of two for Sobol' balance, "
            f"got {n_base}."
        )
    engine = Sobol(d=2 * k, scramble=scramble, seed=seed)
    u = engine.random(n_base)
    if not scramble:
        # The unscrambled sequence starts at the all-zeros point, which the
        # inverse-normal map cannot accept; shift into the cell interiors.
        u = np.clip(u + 0.5 / n_base, _U_FLOOR, _U_CEIL)
    return u[:, :k].copy(), u[:, k:].copy()


def stack_evaluation_matrix(
    u_a: NDArray[np.float64], u_b: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Stack ``[A; B; A_B^(1); ...; A_B^(k)]`` into one evaluation matrix.

    ``A_B^(i)`` is ``A`` with column ``i`` replaced from ``B`` (the radial
    Saltelli et al. 2010 form of the Primer's ``C_i``). Stacking lets the
    caller run the model **once** on ``(k+2)*N`` rows — the engine's batch
    evaluator amortizes its per-call overhead over the whole design.

    Parameters
    ----------
    u_a, u_b : numpy.ndarray, shape (N, k)
        The base matrices from :func:`generate_design`.

    Returns
    -------
    numpy.ndarray, shape ((k+2)*N, k)
        Row blocks: ``[0:N] = A``, ``[N:2N] = B``, ``[(2+i)N:(3+i)N] =
        A_B^(i)`` for ``i = 0..k-1``.
    """
    if u_a.shape != u_b.shape or u_a.ndim != 2:
        raise ValueError(
            f"u_a and u_b must share the same (N, k) shape, got "
            f"{u_a.shape} and {u_b.shape}."
        )
    n_base, k = u_a.shape
    blocks = [u_a, u_b]
    for i in range(k):
        ab_i = u_a.copy()
        ab_i[:, i] = u_b[:, i]
        blocks.append(ab_i)
    return np.vstack(blocks)


def split_outputs(
    y_all: NDArray[np.float64], n_base: int, k: int
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Split the stacked model output back into ``(y_A, y_B, y_ABi)``.

    Parameters
    ----------
    y_all : numpy.ndarray, shape ((k+2)*n_base,)
        Model output for the rows of :func:`stack_evaluation_matrix`, in
        order. Booleans are accepted and cast to float64 (indicator QoIs).
    n_base, k : int
        The design dimensions.

    Returns
    -------
    y_a, y_b : numpy.ndarray, shape (n_base,)
    y_abi : numpy.ndarray, shape (k, n_base)
        ``y_abi[i]`` is the output on ``A_B^(i)``.
    """
    y = np.asarray(y_all, dtype=np.float64).ravel()
    expected = (k + 2) * n_base
    if y.size != expected:
        raise ValueError(
            f"y_all has {y.size} entries; expected (k+2)*n_base = {expected}."
        )
    y_a = y[:n_base]
    y_b = y[n_base : 2 * n_base]
    y_abi = y[2 * n_base :].reshape(k, n_base)
    return y_a, y_b, y_abi


# ============================================================================
# Estimators (Saltelli et al. 2010; Jansen 1999)
# ============================================================================
@dataclass(frozen=True)
class SobolIndices:
    """First-order and total-effect indices for one QoI from one replicate.

    Attributes
    ----------
    names : list of str
        Input (generator) names, index-aligned with :attr:`S` and :attr:`ST`.
    S : numpy.ndarray, shape (k,)
        First-order indices (Saltelli et al. 2010 estimator). May go mildly
        negative for noninfluential factors (Primer p. 170); judge against
        the CI, do not clip.
    ST : numpy.ndarray, shape (k,)
        Total-effect indices (Jansen 1999 estimator; numerator non-negative
        by construction).
    mean_y : float
        Pooled (y_A, y_B) output mean. For an indicator QoI this is the
        failure probability at the analyzed level.
    var_y : float
        Pooled output variance (the normalizer V). For an indicator QoI this
        is ``P_f * (1 - P_f)``.
    n_base : int
        Base sample size N of the replicate.
    """

    names: list[str]
    S: NDArray[np.float64]
    ST: NDArray[np.float64]
    mean_y: float
    var_y: float
    n_base: int

    @property
    def interaction_gap(self) -> NDArray[np.float64]:
        """``ST - S`` per input: the interaction involvement (Primer p. 166)."""
        return self.ST - self.S

    @property
    def sum_S(self) -> float:
        """``sum(S_i)``; 1 for additive models, < 1 with interactions."""
        return float(np.sum(self.S))


def sobol_indices(
    y_a: NDArray[np.float64],
    y_b: NDArray[np.float64],
    y_abi: NDArray[np.float64],
    *,
    names: Sequence[str] | None = None,
) -> SobolIndices:
    """Estimate ``{S_i, ST_i}`` from one evaluated design (ADR-0033 §3).

    Mathematical assumptions: the rows of A and B are (quasi-)random draws
    from the **joint input distribution with independent columns** — under
    dependence use the generator-space route of :class:`GsaInputSpace`, never
    this estimator on correlated physical samples (Primer §4.4 footnote: the
    ANOVA decomposition requires orthogonal inputs). Y must be square
    integrable; binary indicators qualify.

    Parameters
    ----------
    y_a, y_b : numpy.ndarray, shape (N,)
        Output on the base matrices.
    y_abi : numpy.ndarray, shape (k, N)
        Output on the spliced matrices, ``y_abi[i] = f(A_B^(i))``.
    names : sequence of str, optional
        Input names; defaults to ``x1..xk``.

    Returns
    -------
    SobolIndices
        Indices with the pooled mean/variance. If the pooled variance is
        zero (degenerate output, e.g. an all-survive indicator level) the
        indices are NaN and a warning is logged — never an exception, so a
        sweep over levels cannot be killed by one dead level.
    """
    y_a = np.asarray(y_a, dtype=np.float64)
    y_b = np.asarray(y_b, dtype=np.float64)
    y_abi = np.asarray(y_abi, dtype=np.float64)
    k, n_base = y_abi.shape
    if y_a.shape != (n_base,) or y_b.shape != (n_base,):
        raise ValueError(
            f"Shape mismatch: y_a {y_a.shape}, y_b {y_b.shape}, "
            f"y_abi {y_abi.shape}."
        )
    resolved_names = (
        list(names) if names is not None else [f"x{i + 1}" for i in range(k)]
    )
    if len(resolved_names) != k:
        raise ValueError(f"{len(resolved_names)} names supplied for k = {k} inputs.")

    pooled = np.concatenate([y_a, y_b])
    mean_y = float(pooled.mean())
    var_y = float(pooled.var())
    if var_y <= 0.0:
        logger.warning(
            "Degenerate output (pooled variance %.3e); indices set to NaN.",
            var_y,
        )
        nan = np.full(k, np.nan)
        return SobolIndices(
            names=resolved_names,
            S=nan,
            ST=nan.copy(),
            mean_y=mean_y,
            var_y=var_y,
            n_base=n_base,
        )

    s_first = np.empty(k, dtype=np.float64)
    s_total = np.empty(k, dtype=np.float64)
    for i in range(k):
        delta = y_abi[i] - y_a
        s_first[i] = float(np.mean(y_b * delta)) / var_y
        s_total[i] = 0.5 * float(np.mean(delta**2)) / var_y
    return SobolIndices(
        names=resolved_names,
        S=s_first,
        ST=s_total,
        mean_y=mean_y,
        var_y=var_y,
        n_base=n_base,
    )


def bootstrap_indices(
    y_a: NDArray[np.float64],
    y_b: NDArray[np.float64],
    y_abi: NDArray[np.float64],
    *,
    n_boot: int,
    seed: int,
    confidence: float = 0.95,
) -> dict[str, NDArray[np.float64]]:
    """Row-bootstrap percentile CIs for one replicate's indices.

    The Primer's error-estimation recommendation (p. 166, after Archer et
    al. 1997): resample the N **design rows jointly** — each bootstrap draw
    picks row indices ``j`` and carries ``(y_A(j), y_B(j), y_AB1(j), ...,
    y_ABk(j))`` together, preserving the pairing the estimators rely on.
    Note the caveat recorded in ADR-0033 §4: row bootstrap on a QMC design
    ignores the sequence's balance, so these CIs are the *cross-check*; the
    primary uncertainty statement is the spread over independent scramblings
    (:func:`aggregate_replicates`).

    Parameters
    ----------
    y_a, y_b : numpy.ndarray, shape (N,)
    y_abi : numpy.ndarray, shape (k, N)
        As in :func:`sobol_indices`.
    n_boot : int
        Number of bootstrap resamples (B).
    seed : int
        RNG seed (deterministic CIs).
    confidence : float, optional
        Two-sided confidence level (default 0.95).

    Returns
    -------
    dict
        ``{'S_lo', 'S_hi', 'ST_lo', 'ST_hi'}`` each shape ``(k,)``, plus
        ``'S_boot'``/``'ST_boot'`` the full ``(n_boot, k)`` bootstrap draws
        (the driver pools these across replicates for the CI of the
        replicate-mean index).
    """
    y_a = np.asarray(y_a, dtype=np.float64)
    y_b = np.asarray(y_b, dtype=np.float64)
    y_abi = np.asarray(y_abi, dtype=np.float64)
    k, n_base = y_abi.shape
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_base, size=(n_boot, n_base))

    ya = y_a[idx]  # (n_boot, N)
    yb = y_b[idx]
    pooled_mean = 0.5 * (ya.mean(axis=1) + yb.mean(axis=1))
    pooled_sq = 0.5 * ((ya**2).mean(axis=1) + (yb**2).mean(axis=1))
    var = pooled_sq - pooled_mean**2  # (n_boot,)
    var = np.where(var > 0.0, var, np.nan)

    s_boot = np.empty((n_boot, k), dtype=np.float64)
    st_boot = np.empty((n_boot, k), dtype=np.float64)
    for i in range(k):
        delta = y_abi[i][idx] - ya  # (n_boot, N)
        s_boot[:, i] = (yb * delta).mean(axis=1) / var
        st_boot[:, i] = 0.5 * (delta**2).mean(axis=1) / var

    alpha = 100.0 * (1.0 - confidence) / 2.0
    return {
        "S_lo": np.nanpercentile(s_boot, alpha, axis=0),
        "S_hi": np.nanpercentile(s_boot, 100.0 - alpha, axis=0),
        "ST_lo": np.nanpercentile(st_boot, alpha, axis=0),
        "ST_hi": np.nanpercentile(st_boot, 100.0 - alpha, axis=0),
        "S_boot": s_boot,
        "ST_boot": st_boot,
    }


def aggregate_replicates(
    replicates: Sequence[SobolIndices],
    *,
    confidence: float = 0.95,
) -> dict[str, NDArray[np.float64] | float | list[str] | int]:
    """Mean, SE, and Student-t CI across independent scrambling replicates.

    The primary uncertainty statement (ADR-0033 §4): each replicate is an
    independent randomized-QMC estimate, so the replicate mean is unbiased
    and the t-interval over R replicates is an honest CI for every index.

    Parameters
    ----------
    replicates : sequence of SobolIndices
        R >= 2 replicates for the same QoI and input space (same names).
    confidence : float, optional
        Two-sided confidence level (default 0.95).

    Returns
    -------
    dict
        ``names``; ``S_mean``, ``S_se``, ``S_lo``, ``S_hi`` (each ``(k,)``);
        the same four for ``ST``; ``mean_y_mean`` and ``var_y_mean`` (floats);
        ``n_replicates``.
    """
    if len(replicates) < 2:
        raise ValueError("Need at least two replicates for a t-interval.")
    names = replicates[0].names
    for rep in replicates[1:]:
        if rep.names != names:
            raise ValueError("Replicates disagree on input names.")
    from scipy.stats import t as student_t

    r = len(replicates)
    s_stack = np.vstack([rep.S for rep in replicates])  # (R, k)
    st_stack = np.vstack([rep.ST for rep in replicates])
    t_crit = float(student_t.ppf(0.5 + confidence / 2.0, df=r - 1))

    def _summary(stack: NDArray[np.float64]) -> tuple[NDArray, NDArray]:
        mean = stack.mean(axis=0)
        se = stack.std(axis=0, ddof=1) / np.sqrt(r)
        return mean, se

    s_mean, s_se = _summary(s_stack)
    st_mean, st_se = _summary(st_stack)
    return {
        "names": list(names),
        "n_replicates": r,
        "S_mean": s_mean,
        "S_se": s_se,
        "S_lo": s_mean - t_crit * s_se,
        "S_hi": s_mean + t_crit * s_se,
        "ST_mean": st_mean,
        "ST_se": st_se,
        "ST_lo": st_mean - t_crit * st_se,
        "ST_hi": st_mean + t_crit * st_se,
        "mean_y_mean": float(np.mean([rep.mean_y for rep in replicates])),
        "var_y_mean": float(np.mean([rep.var_y for rep in replicates])),
    }


# ============================================================================
# Generator -> physical input map (bit-identical arithmetic to M2)
# ============================================================================
@dataclass(frozen=True)
class GsaInputSpace:
    """The GSA input space: unit-hypercube generators -> physical inputs.

    Wraps the seven canonical theta marginals plus (optionally) the
    independent stochastic seepage length L as the eighth generator column,
    reproducing M2's arithmetic **exactly** (same moment-matched lognormal
    map, same bounds clip; pinned bit-identical by
    ``tests/test_sensitivity.py``), so the GSA analyzes the production prior
    and not an approximation of it.

    Under ``coupling='two_population'`` (the ADR-0012 production mode) every
    generator maps one-to-one onto an independent physical input. Under
    ``coupling='correlated'`` (the ADR-0033 §2 Nataf companion) the
    generators are the independent standard normals of the Rosenblatt
    transform: the ``anchor`` variable keeps its own generator (its index is
    then the **full** Kucherenko contribution, correlation share included)
    while the other member of the (k_aq, d_70) pair receives
    ``z = rho*z_anchor + sqrt(1-rho^2)*eta`` (its generator ``eta`` carries
    the **independent**, Mara-Tarantola decorrelated contribution).

    Attributes
    ----------
    marginals : tuple of MarginalSpec
        Exactly the seven canonical marginals (any order; resolved by name).
    bounds : mapping or None
        The M2 physical clip (spec §12 fm2), e.g. ``{'d_70': (5e-5, 1e-3)}``.
    seepage_mean_m, seepage_cov : float or None
        Lognormal L spec (``geometry.L``, ``config.seepage_length_cov``).
        Both None -> deterministic L, seven generators only.
    coupling : {'two_population', 'correlated'}
        ADR-0012 production mode vs the Nataf companion.
    rho_log_kaq_d70 : float
        Log-space copula correlation (used only under ``'correlated'``).
    anchor : {'k_aq', 'd_70'}
        Rosenblatt ordering for the correlated pair (ignored under
        ``'two_population'``).
    """

    marginals: tuple[MarginalSpec, ...]
    bounds: Mapping[str, tuple[float, float]] | None = None
    seepage_mean_m: float | None = None
    seepage_cov: float | None = None
    coupling: str = "two_population"
    rho_log_kaq_d70: float = 0.0
    anchor: CorrelatedAnchor = "k_aq"
    _spec_by_name: dict[str, MarginalSpec] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        spec_by_name = {spec.name: spec for spec in self.marginals}
        missing = [n for n in PARAM_NAMES if n not in spec_by_name]
        if missing or len(self.marginals) != len(PARAM_NAMES):
            raise ValueError(
                f"Exactly the seven canonical marginals {PARAM_NAMES} are "
                f"required; missing {missing}."
            )
        if (self.seepage_mean_m is None) != (self.seepage_cov is None):
            raise ValueError(
                "seepage_mean_m and seepage_cov must be supplied together "
                "(both None for deterministic L)."
            )
        if self.coupling not in ("two_population", "correlated"):
            raise ValueError(f"Unknown coupling {self.coupling!r}.")
        if self.coupling == "correlated":
            if not -1.0 < self.rho_log_kaq_d70 < 1.0:
                raise ValueError(
                    f"rho_log_kaq_d70 {self.rho_log_kaq_d70!r} must lie in " "(-1, 1)."
                )
            if self.anchor not in ("k_aq", "d_70"):
                raise ValueError(f"anchor {self.anchor!r} must be 'k_aq' or 'd_70'.")
        object.__setattr__(self, "_spec_by_name", spec_by_name)

    @property
    def stochastic_seepage(self) -> bool:
        """Whether L is a generator column (True in every production config)."""
        return self.seepage_mean_m is not None

    @property
    def names(self) -> list[str]:
        """Generator names, index-aligned with the design columns.

        The theta columns keep the canonical PARAM_NAMES; the L column is
        ``'L'``. Under ``'correlated'`` the non-anchor pair member's
        generator is its *independent* component — the driver records the
        role labels alongside (see :attr:`generator_roles`).
        """
        base = list(PARAM_NAMES)
        if self.stochastic_seepage:
            base.append("L")
        return base

    @property
    def generator_roles(self) -> dict[str, str]:
        """Interpretation label per generator (ADR-0033 §2).

        ``'marginal'`` everywhere under two-population; under the Nataf
        companion the anchor is ``'full (incl. correlated share)'`` and the
        other pair member ``'independent (decorrelated)'``.
        """
        roles = {name: "marginal" for name in self.names}
        if self.coupling == "correlated":
            other = "d_70" if self.anchor == "k_aq" else "k_aq"
            roles[self.anchor] = "full (incl. correlated share)"
            roles[other] = "independent (decorrelated)"
        return roles

    @property
    def k(self) -> int:
        """Number of generator columns (7, or 8 with stochastic L)."""
        return len(PARAM_NAMES) + (1 if self.stochastic_seepage else 0)

    def map_uniform(
        self, u: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64] | None]:
        """Map unit-hypercube generators to (theta_matrix, seepage_lengths).

        Reproduces M2's arithmetic exactly: ``z = norm.ppf(u)``, the copula
        mix (correlated mode only), the moment-matched marginal map
        (``sigma_ln**2 = ln(1+cov**2)``, ``mu_ln = ln(mean) - sigma_ln**2/2``)
        and the bounds clip. Given the same underlying design this is
        bit-identical to ``sampling.sample_theta`` (pinned by test).

        Parameters
        ----------
        u : numpy.ndarray, shape (n, k)
            Generator matrix (rows of A/B/A_B^(i) blocks); entries in (0, 1).

        Returns
        -------
        theta_matrix : numpy.ndarray, shape (n, 7)
            Physical theta rows in canonical column order.
        seepage_lengths : numpy.ndarray of shape (n,), or None
            Physical L per row, or None when L is deterministic.
        """
        u = np.asarray(u, dtype=np.float64)
        if u.ndim != 2 or u.shape[1] != self.k:
            raise ValueError(f"u must have shape (n, {self.k}), got {u.shape}.")
        z = norm.ppf(np.clip(u, _U_FLOOR, _U_CEIL))

        if self.coupling == "correlated":
            i_kaq = PARAM_NAMES.index("k_aq")
            i_d70 = PARAM_NAMES.index("d_70")
            rho = float(self.rho_log_kaq_d70)
            mix = np.sqrt(1.0 - rho**2)
            if self.anchor == "k_aq":
                z[:, i_d70] = rho * z[:, i_kaq] + mix * z[:, i_d70]
            else:
                z[:, i_kaq] = rho * z[:, i_d70] + mix * z[:, i_kaq]

        n = u.shape[0]
        theta = np.empty((n, len(PARAM_NAMES)), dtype=np.float64)
        for j, name in enumerate(PARAM_NAMES):
            spec = self._spec_by_name[name]
            if spec.family == "lognormal":
                sigma_ln = np.sqrt(np.log(1.0 + spec.cov**2))
                mu_ln = np.log(spec.mean) - 0.5 * sigma_ln**2
                theta[:, j] = np.exp(mu_ln + sigma_ln * z[:, j])
            else:  # normal: sigma = mean * COV (M2 arithmetic)
                theta[:, j] = spec.mean + spec.mean * spec.cov * z[:, j]

        if self.bounds:
            for name, (low, high) in self.bounds.items():
                j = PARAM_NAMES.index(name)
                theta[:, j] = np.clip(theta[:, j], low, high)

        seepage: NDArray[np.float64] | None = None
        if self.stochastic_seepage:
            sigma_ln = np.sqrt(np.log(1.0 + float(self.seepage_cov) ** 2))
            mu_ln = np.log(float(self.seepage_mean_m)) - 0.5 * sigma_ln**2
            seepage = np.exp(mu_ln + sigma_ln * z[:, len(PARAM_NAMES)])
        return theta, seepage
