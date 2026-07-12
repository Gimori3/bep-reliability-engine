"""BEP fragility provider: Phase 2 posteriors (default) or Phase 1 priors.

ADR-0038 decision 4. One :class:`FragilityCurve` type wraps either source
and evaluates P_f(h) at arbitrary stage under the ADR-0024 deliverable
semantics:

* where the branch's fit is the deliverable form (transition bracketed),
  the fitted lognormal is evaluated;
* otherwise the raw points are interpolated **linearly in probit space**
  between grid neighbours (monotone and tail-respecting), never
  extrapolated above the highest grid level — evaluation there returns the
  last raw value and sets the ``clamped_above_grid`` flag (KP62.0's
  transient branch lives in this regime by design);
* stages at or below the leading zero-failure grid levels evaluate to
  exactly 0; the nonzero Clopper-Pearson upper bounds stay available on the
  curve for uncertainty presentation.

The ADR-0037 length effect is applied by the caller (composition layer) via
the public transform — this module returns cross-section curves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from bep_reliability_engine.fragility import FragilityResult, LognormFragility

__all__ = ["FragilityCurve", "load_bep_curve"]

_PROBIT_EPS = 1e-12  # probit clip keeps 0/1 grid points finite
# ADR-0024 data-driven bracketing criterion: a fit is the deliverable form
# only where the raw curve reaches the transition.
_TRANSITION_BRACKET_MIN_P = 0.5


@dataclass(frozen=True)
class FragilityCurve:
    """One branch's conditional fragility with ADR-0024 evaluation semantics.

    Attributes
    ----------
    grid_m_msl : numpy.ndarray
        Conditioning grid [m MSL], strictly increasing.
    p_raw : numpy.ndarray
        Per-level raw failure fractions.
    ci_lower, ci_upper : numpy.ndarray
        Clopper-Pearson 95% bounds per level (always on, ADR-0024).
    fit : LognormFragility or None
        The fitted lognormal, if any.
    fit_is_deliverable : bool
        True when ADR-0024 classifies the fit as the deliverable form
        (transition bracketed); False means raw-tail presentation.
    branch : str
        ``'transient'`` or ``'static'``.
    source : str
        Provenance stamp: ``'phase2_posterior'`` or ``'phase1_prior'``.
    source_path : str
        The artifact the curve came from.
    """

    grid_m_msl: NDArray[np.float64]
    p_raw: NDArray[np.float64]
    ci_lower: NDArray[np.float64]
    ci_upper: NDArray[np.float64]
    fit: LognormFragility | None
    fit_is_deliverable: bool
    branch: str
    source: str
    source_path: str
    datum_m: float | None = None

    def evaluate(
        self, stage_m: NDArray[np.float64] | float
    ) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
        """Evaluate P_f at ``stage_m`` under the ADR-0024 policy.

        Parameters
        ----------
        stage_m : numpy.ndarray or float
            Stage(s) [m MSL].

        Returns
        -------
        tuple of (numpy.ndarray, numpy.ndarray)
            ``(p_f, clamped_above_grid)``: the probabilities, and a per-value
            flag marking stages above the highest grid level where the
            raw-tail branch holds its last value instead of extrapolating
            (all-False on the fitted branch, which extrapolates by design).
        """
        stage = np.atleast_1d(np.asarray(stage_m, dtype=np.float64))

        if self.fit is not None and self.fit_is_deliverable:
            p_f = np.asarray(self.fit.probability_of_failure(stage), dtype=np.float64)
            return p_f, np.zeros(stage.shape, dtype=bool)

        # Raw-tail branch (ADR-0024): probit-space linear interpolation,
        # clamped at both grid ends — never extrapolated above the grid.
        clamped = stage > self.grid_m_msl[-1] + 1e-12
        probit = norm.ppf(np.clip(self.p_raw, _PROBIT_EPS, 1.0 - _PROBIT_EPS))
        p_f = np.asarray(
            norm.cdf(np.interp(stage, self.grid_m_msl, probit)), dtype=np.float64
        )
        # Leading zero-failure levels are exact zeros, not probit artifacts:
        # at or below the last leading-zero level nothing ever failed at
        # equal-or-higher loading, so report 0 (CI upper bounds carry the
        # uncertainty statement).
        n_leading_zero = (
            int(np.argmax(self.p_raw > 0.0))
            if np.any(self.p_raw > 0.0)
            else int(self.p_raw.size)
        )
        if n_leading_zero > 0:
            p_f[stage <= self.grid_m_msl[n_leading_zero - 1] + 1e-12] = 0.0
        return p_f, clamped


def _deliverable_fit(fit: LognormFragility | None, p_raw: NDArray[np.float64]) -> bool:
    """ADR-0024 bracketing criterion, computed from the data (not trusted)."""
    return fit is not None and float(np.max(p_raw)) >= _TRANSITION_BRACKET_MIN_P


def load_bep_curve(
    path: str | Path,
    *,
    branch: str = "transient",
) -> FragilityCurve:
    """Load one BEP fragility curve from a persisted artifact.

    Parameters
    ----------
    path : str or pathlib.Path
        A Phase 2 ``*_posterior.h5`` (the ADR-0038 default BEP input) or a
        Phase 1 FragilityResult HDF5 (the prior option).
    branch : {'transient', 'static'}
        Which limit state's curve to expose. The thesis composes the
        transient branch; the static one exists for the bias comparison.

    Returns
    -------
    FragilityCurve
        With provenance stamped (``phase2_posterior`` / ``phase1_prior``)
        and the ADR-0024 deliverable classification recomputed from the
        curve's own data (max raw P_f >= 0.5 and a fit exists).

    Raises
    ------
    ValueError
        On an unknown branch.
    """
    if branch not in ("transient", "static"):
        raise ValueError(f"unknown branch {branch!r}; expected transient|static.")
    path = Path(path)

    if path.name.endswith("_posterior.h5"):
        # Imported lazily: Phase 3 needs Phase 2 only when posterior curves
        # are actually consumed.
        from bayesian_reliability_updating.posterior import PosteriorResult

        posterior = PosteriorResult.load(path)
        frag = posterior.fragility
        if branch == "transient":
            p_raw = frag.P_f_trans_post_raw
            fit = frag.P_f_trans_post_fit
        else:
            p_raw = frag.P_f_static_post_raw
            fit = frag.P_f_static_post_fit
        lower, upper = frag.binomial_ci[branch]
        datum = (
            posterior.metadata.get("phase2", {})
            .get("posterior_fragility", {})
            .get("datum_m")
        )
        return FragilityCurve(
            grid_m_msl=np.asarray(frag.conditioning_grid, dtype=np.float64),
            p_raw=np.asarray(p_raw, dtype=np.float64),
            ci_lower=np.asarray(lower, dtype=np.float64),
            ci_upper=np.asarray(upper, dtype=np.float64),
            fit=fit,
            fit_is_deliverable=_deliverable_fit(fit, np.asarray(p_raw)),
            branch=branch,
            source="phase2_posterior",
            source_path=str(path),
            datum_m=None if datum is None else float(datum),
        )

    result = FragilityResult.load(path)
    if branch == "transient":
        p_raw = result.P_f_trans_raw
        fit = result.P_f_trans_fit
    else:
        p_raw = result.P_f_static_raw
        fit = result.P_f_static_fit
    lower, upper = result.binomial_ci[branch]
    datum = result.metadata.get("fragility_fit", {}).get("datum_m")
    return FragilityCurve(
        grid_m_msl=np.asarray(result.conditioning_grid, dtype=np.float64),
        p_raw=np.asarray(p_raw, dtype=np.float64),
        ci_lower=np.asarray(lower, dtype=np.float64),
        ci_upper=np.asarray(upper, dtype=np.float64),
        fit=fit,
        fit_is_deliverable=_deliverable_fit(fit, np.asarray(p_raw)),
        branch=branch,
        source="phase1_prior",
        source_path=str(path),
        datum_m=None if datum is None else float(datum),
    )
