"""Event-based / annualized failure probability per segment (RQ4 metrics).

ADR-0038 decision 3, composition rule: the conditional fragility is
evaluated at each ensemble event's peak stage, and the annual failure
probability is the ensemble mean over the simulated years,

    P_f,annual = (1 / n_years) * sum_year P_sys(peak_stage_year),

per scenario, with the per-mechanism annual contributions reported the same
way (each mechanism's own conditional curve under the same peak-stage
distribution — the thesis's mechanism-dominance comparison at the
annualized level). Climate change enters ONLY through the peak-stage
distribution and the event-characteristic stratification (ADR-0023).

Stratified variants for the RQ4 attribution group the events by a boolean
predicate over :class:`~system_integration.hazard.EventSummary` (duration
classes, compound-event flags) and report the conditional mean within each
stratum, so peak-matched comparisons are one predicate away.

Hazard-coverage diagnostics (HKV-audit item 2, 2026-07-18)
----------------------------------------------------------
The curve interpolators clamp at the grid ends, so ensemble peaks outside a
mechanism's stage grid are silently evaluated at the end values. Mirroring
the four truncation guards of the HKV Fragility Curve Creator
(``class_probpiping.py`` lines 446-468), :func:`annualize` now records, per
mechanism and for the composed system curve, the fraction of ensemble peaks
above/below the grid together with the clamp end-values, and **warns** when

* peaks land above a grid whose top P_f is below
  :data:`P_TOP_SATURATION_THRESHOLD` — the clamp is then a genuine **lower
  bound** on the annual probability (the documented KP62.0 BEP situation),
  not saturation; or
* peaks land below a grid whose bottom P_f is above
  :data:`P_BOTTOM_NEGLIGIBLE_THRESHOLD` — the curve has not decayed to ~0 at
  its lowest level, so the below-grid mass is unresolved.

Diagnostics only: the annualized numbers themselves are untouched.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import interp1d

from system_integration.composition import SystemFragility
from system_integration.hazard import EventSummary, NodeHazard

logger = logging.getLogger(__name__)

__all__ = [
    "AnnualizedResult",
    "P_BOTTOM_NEGLIGIBLE_THRESHOLD",
    "P_TOP_SATURATION_THRESHOLD",
    "annualize",
    "stratified_annual_p_f",
]

# Coverage-guard thresholds, after HKV's warnings: a curve whose top sits
# below 0.99 has not saturated (an above-grid clamp is then a lower bound);
# a curve whose bottom sits above 0.01 has not decayed (a below-grid clamp
# leaves the low-stage mass unresolved).
P_TOP_SATURATION_THRESHOLD: float = 0.99
P_BOTTOM_NEGLIGIBLE_THRESHOLD: float = 0.01


@dataclass(frozen=True)
class AnnualizedResult:
    """Annualized failure probabilities for one segment and scenario.

    Attributes
    ----------
    scenario : str
        ``'historical'`` or ``'+4K'``.
    n_years : int
        Ensemble-years behind the mean.
    p_f_annual_system : float
        Annual series-system failure probability.
    p_f_annual_per_mechanism : dict of str to float
        Each mechanism's own annual failure probability under the same
        peak-stage distribution (dominance numerators).
    mechanisms : tuple of str
        What was composed (absence visible).
    sources : dict of str to str
        Provenance stamp per mechanism (stub results can never pass as
        Uemura's).
    coverage : dict of str to dict
        Per-curve hazard-coverage diagnostics (HKV-audit item 2): one entry
        per mechanism plus ``'__system__'``, each carrying
        ``grid_bottom_m_msl`` / ``grid_top_m_msl``, the clamp end-values
        ``p_bottom`` / ``p_top``, the ensemble fractions
        ``frac_peaks_below_grid`` / ``frac_peaks_above_grid``, and the two
        boolean flags ``lower_bound_clamp`` (peaks above a non-saturated
        grid top — the annualized number is a lower bound) and
        ``below_grid_unresolved`` (peaks below a non-decayed grid bottom).
        Purely diagnostic; empty only on legacy constructions.
    """

    scenario: str
    n_years: int
    p_f_annual_system: float
    p_f_annual_per_mechanism: dict[str, float]
    mechanisms: tuple[str, ...]
    sources: dict[str, str]
    coverage: dict[str, dict[str, float | bool]] = field(default_factory=dict)

    def dominance_share(self, mechanism: str) -> float:
        """Mechanism share of the summed annual contributions."""
        total = sum(self.p_f_annual_per_mechanism.values())
        if total <= 0.0:
            return 0.0
        return self.p_f_annual_per_mechanism[mechanism] / total


def _curve_interpolators(
    fragility: SystemFragility,
) -> dict[str, Callable[[np.ndarray], np.ndarray]]:
    """Linear interpolators over the composition grid, clamped at the ends."""
    interpolators: dict[str, Callable[[np.ndarray], np.ndarray]] = {}
    for name, p in {"__system__": fragility.p_sys, **fragility.per_mechanism}.items():
        interpolators[name] = interp1d(
            fragility.stage_m_msl,
            p,
            kind="linear",
            bounds_error=False,
            fill_value=(float(p[0]), float(p[-1])),
        )
    return interpolators


def _coverage_diagnostics(
    fragility: SystemFragility, hazard: NodeHazard
) -> dict[str, dict[str, float | bool]]:
    """Per-curve hazard-coverage record + clamp warnings (HKV-audit item 2).

    Mirrors HKV's four truncation guards for the ensemble-mean formulation:
    every peak is a real event, so the two failure modes are peaks landing
    *outside* the curve grid where the interpolator clamps. Emits one
    ``logger.warning`` per tripped curve; returns the full record either way.
    """
    peaks = hazard.peak_stages()
    grid = np.asarray(fragility.stage_m_msl, dtype=np.float64)
    coverage: dict[str, dict[str, float | bool]] = {}
    curves = {"__system__": fragility.p_sys, **fragility.per_mechanism}
    for name, p in curves.items():
        p_bottom = float(p[0])
        p_top = float(p[-1])
        frac_above = float(np.mean(peaks > grid[-1]))
        frac_below = float(np.mean(peaks < grid[0]))
        lower_bound_clamp = frac_above > 0.0 and p_top < P_TOP_SATURATION_THRESHOLD
        below_grid_unresolved = (
            frac_below > 0.0 and p_bottom > P_BOTTOM_NEGLIGIBLE_THRESHOLD
        )
        coverage[name] = {
            "grid_bottom_m_msl": float(grid[0]),
            "grid_top_m_msl": float(grid[-1]),
            "p_bottom": p_bottom,
            "p_top": p_top,
            "frac_peaks_below_grid": frac_below,
            "frac_peaks_above_grid": frac_above,
            "lower_bound_clamp": bool(lower_bound_clamp),
            "below_grid_unresolved": bool(below_grid_unresolved),
        }
        label = "system curve" if name == "__system__" else f"mechanism '{name}'"
        where = f"{hazard.river} KP{hazard.kp:g} {hazard.scenario}"
        if lower_bound_clamp:
            logger.warning(
                "Hazard-coverage: %s at %s — %.1f%% of ensemble peaks exceed "
                "the curve grid top (%.2f m MSL) where P_f is only %.3g "
                "(< %.2f): the annualized probability is a LOWER BOUND "
                "(clamped above the grid).",
                label,
                where,
                100.0 * frac_above,
                float(grid[-1]),
                p_top,
                P_TOP_SATURATION_THRESHOLD,
            )
        if below_grid_unresolved:
            logger.warning(
                "Hazard-coverage: %s at %s — %.1f%% of ensemble peaks fall "
                "below the curve grid bottom (%.2f m MSL) where P_f is still "
                "%.3g (> %.2g): the curve has not decayed at its lowest "
                "level, so the below-grid contribution is unresolved.",
                label,
                where,
                100.0 * frac_below,
                float(grid[0]),
                p_bottom,
                P_BOTTOM_NEGLIGIBLE_THRESHOLD,
            )
    return coverage


def annualize(fragility: SystemFragility, hazard: NodeHazard) -> AnnualizedResult:
    """Annual failure probability from the composed curve and node hazard.

    Parameters
    ----------
    fragility : SystemFragility
        The composed segment fragility on its stage grid.
    hazard : NodeHazard
        The node's ensemble hazard (one event per simulated year).

    Returns
    -------
    AnnualizedResult
        System and per-mechanism annual probabilities for the hazard's
        scenario, with the per-curve hazard-coverage diagnostics attached
        (and clamp warnings emitted; numbers unchanged — HKV-audit item 2).
    """
    peaks = hazard.peak_stages()
    interpolators = _curve_interpolators(fragility)
    per_mechanism = {
        name: float(np.mean(interpolators[name](peaks)))
        for name in fragility.mechanisms
    }
    return AnnualizedResult(
        scenario=hazard.scenario,
        n_years=hazard.n_years,
        p_f_annual_system=float(np.mean(interpolators["__system__"](peaks))),
        p_f_annual_per_mechanism=per_mechanism,
        mechanisms=fragility.mechanisms,
        sources=dict(fragility.sources),
        coverage=_coverage_diagnostics(fragility, hazard),
    )


def stratified_annual_p_f(
    fragility: SystemFragility,
    hazard: NodeHazard,
    predicate: Callable[[EventSummary], bool],
) -> tuple[float, float, int, int]:
    """Conditional annual P_f inside/outside an event stratum (RQ4).

    Parameters
    ----------
    fragility : SystemFragility
        The composed segment fragility.
    hazard : NodeHazard
        The node's ensemble hazard.
    predicate : callable
        Boolean stratifier over :class:`EventSummary` (e.g. long-duration
        events: ``lambda e: e.hours_above_datum > 24``).

    Returns
    -------
    tuple of (float, float, int, int)
        ``(p_f_inside, p_f_outside, n_inside, n_outside)`` — conditional
        system P_f means within each stratum and the stratum sizes. Empty
        strata return ``nan`` for their mean.
    """
    interpolator = _curve_interpolators(fragility)["__system__"]
    inside = np.asarray([predicate(e) for e in hazard.events], dtype=bool)
    peaks = hazard.peak_stages()
    p_events = np.asarray(interpolator(peaks), dtype=np.float64)
    p_in = float(np.mean(p_events[inside])) if np.any(inside) else float("nan")
    p_out = float(np.mean(p_events[~inside])) if np.any(~inside) else float("nan")
    return p_in, p_out, int(inside.sum()), int((~inside).sum())
