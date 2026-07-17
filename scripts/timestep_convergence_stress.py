"""Worst-case forward-Euler timestep stress test (spec section 11; ADR-0039).

Single-realization Delta-t-halving ladder at the point where the explicit
Euler scheme is genuinely weakest, per the spec section 11 protocol that
ADR-0030's population-level P_f ladders did not execute in its literal form:

* **Loading**: the flashiest rising limb in the real d4PDF ensemble at the
  section, selected by the largest one-native-step normalized stage rise --
  exactly the head jump one native forward-Euler step integrates across --
  with the 10%-90% rise time as tiebreak context. A real member, never a
  synthetic shape; the G1 conditioning-level scaling then loads it exactly
  as the production sweep would (``conditioning_record_for_level``).
* **Parameter vector**: the spec section 11 / section 13 worst case drawn
  from the high-progression-rate tail -- p99 ``k_aq``, p99 ``C_e``, p01
  ``D_bl``, medians elsewhere -- moment-matched lognormal quantiles of the
  section's own generated priors (identical arithmetic to the M2 sampler),
  bounds-clipped where the config clips (spec section 12 failure mode 2).
* **Ladder**: Delta-t = native/2^k, evaluated through the frozen M8 scalar
  API (``evaluate_realization``) on records refined by the ADR-0013/0030
  ``resample_record`` hook, so every rung is the production code path.
  The loading signal never changes; only the Euler grid is refined.

Convergence criterion (spec section 11): terminal eroded length l_e at
Delta-t vs Delta-t/2 within 1% relative. Near the breach barrier l_e is a
stall-vs-breach bifurcation, so branch flips are reported separately along
with the breach-threshold stage h*(Delta-t) on a 0.05 m refined grid --
"converged" demands the 1% criterion off the bifurcation AND a stationary
threshold.

Everything physics goes through the public M3/M8 modules; this script owns
no kernels. Deterministic: no RNG anywhere (quantiles, not draws).

Usage (repo root, venv active; needs the gitignored d4PDF drop under
``data/raw/hydrographs/``)::

    python scripts/timestep_convergence_stress.py
    python scripts/timestep_convergence_stress.py --skip-confirm  # KP58.8 only

Outputs: ``docs/decisions/adr0039-timestep-stress.json`` (evidence tables),
``docs/figures/adr0039-timestep-stress.png`` (four-panel figure), console
summary.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import EvaluationResult, evaluate_realization
from bep_reliability_engine.hydrographs import (
    CanonicalShape,
    HydrographRecord,
    conditioning_record_for_level,
    flood_timescales,
    load_hydrograph_ensemble,
    load_rating_coefficients,
    normalize_stage_shape,
    rating_curve_path,
    resample_record,
    resolve_band_workbook,
    validate_datum_consistency,
)
from bep_reliability_engine.progression import CRACK_RESISTANCE_FACTOR
from bep_reliability_engine.sampling import PARAM_NAMES

# The Delta-t-halving ladder [s]: native 3600 s down to native/128 = 28.125 s
# on the production conditioning grid, with one extra rung native/256 =
# 14.0625 s on the refined grid to certify the reference itself (successive
# change at the two finest rungs must be far under the criterion). All rungs
# are exact integer subdivisions of the native grid (ADR-0030), and the two
# finest sit at/below Pol's own small-scale 10 s -- 100 s integration range.
NATIVE_DT_S: float = 3600.0
DT_LADDER_S: list[float] = [NATIVE_DT_S / 2**k for k in range(8)]
DT_REFERENCE_S: float = NATIVE_DT_S / 2**8

# Spec section 11 acceptance: successive-halving terminal-l_e change < 1%.
REL_CRITERION: float = 0.01

# Worst-case tail quantiles (spec section 11 / section 13 "Convergence-test
# worst-case theta": high k_aq, high C_e, low D_bl; medians elsewhere).
Q_HIGH: float = 0.99
Q_LOW: float = 0.01

# Refined threshold grid: step and half-window around the coarse-pass
# breach-threshold band. 0.05 m resolves the h* shift far below the
# production grid's 0.25 m spacing.
REFINE_STEP_M: float = 0.05
REFINE_PAD_M: float = 0.30

# l_e floor [m] under which a level counts as "no erosion" for the relative
# criterion (0 vs 0 is converged; the criterion is meaningless on nothing).
L_E_FLOOR_M: float = 0.01

DEFAULT_CONFIG = "configs/kp58_8_historical_matrix.yaml"
DEFAULT_CONFIRM_CONFIG = "configs/kp57_4_historical_matrix.yaml"
DEFAULT_JSON = "docs/decisions/adr0039-timestep-stress.json"
DEFAULT_FIGURE = "docs/figures/adr0039-timestep-stress.png"


def lognormal_quantile(mean: float, cov: float, q: float) -> float:
    """Quantile of a lognormal given physical mean and COV (M2 arithmetic).

    Moment-matching identical to the M2 sampler (``sampling.MarginalSpec``
    notes): ``sigma_ln**2 = ln(1 + cov**2)``, ``mu_ln = ln(mean) -
    sigma_ln**2 / 2``, then ``exp(mu_ln + sigma_ln * Phi^-1(q))``.

    Parameters
    ----------
    mean : float
        Physical mean (> 0).
    cov : float
        Coefficient of variation (fraction).
    q : float
        Quantile level in (0, 1); 0.5 returns the median ``exp(mu_ln)``.

    Returns
    -------
    float
        The physical-space quantile.
    """
    sigma_ln_sq = math.log(1.0 + cov * cov)
    mu_ln = math.log(mean) - sigma_ln_sq / 2.0
    return math.exp(mu_ln + math.sqrt(sigma_ln_sq) * float(norm.ppf(q)))


def worst_case_theta(config: Config) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Build the spec section 11 worst-case theta row from the config priors.

    p99 ``k_aq`` and ``C_e`` (rate drivers), p01 ``D_bl`` (smallest crack
    term and gate resistance), medians for the remaining four parameters,
    all from the section's own generated prior table, clipped to the config
    bounds exactly as the M2 sampler clips (spec section 12 failure mode 2).

    Parameters
    ----------
    config : Config
        The section's validated run configuration.

    Returns
    -------
    tuple of (numpy.ndarray, dict)
        The (7,) theta row in canonical ``PARAM_NAMES`` order, and a record
        of the quantile levels and resulting physical values per parameter.
    """
    quantile_by_name = {name: 0.5 for name in PARAM_NAMES}
    quantile_by_name["k_aq"] = Q_HIGH
    quantile_by_name["C_e"] = Q_HIGH
    quantile_by_name["D_bl"] = Q_LOW

    bounds = config.priors.bounds or {}
    theta = np.empty(len(PARAM_NAMES), dtype=np.float64)
    record: dict[str, Any] = {}
    for i, name in enumerate(PARAM_NAMES):
        spec = getattr(config.priors, name)
        if spec.family != "lognormal":
            raise ValueError(
                f"worst-case quantiles are implemented for lognormal "
                f"marginals only; prior {name!r} is {spec.family!r}."
            )
        value = lognormal_quantile(spec.mean, spec.cov, quantile_by_name[name])
        if name in bounds:
            low, high = bounds[name]
            value = min(max(value, low), high)
        theta[i] = value
        record[name] = {
            "quantile": quantile_by_name[name],
            "value": value,
            "prior_mean": spec.mean,
            "prior_cov": spec.cov,
        }
    return theta, record


def scan_ensemble_flashiness(
    config: Config,
) -> tuple[dict[str, HydrographRecord], list[dict[str, Any]]]:
    """Rank every d4PDF member at the section by rising-limb flashiness.

    The primary metric is ``max_step_rise``: the largest one-native-step
    increment of the *normalized* stage shape -- after the G1 scaling to a
    conditioning level h_i the corresponding absolute head jump is
    ``(h_i - h_base) * max_step_rise``, which is precisely what a single
    native forward-Euler step integrates across. ``rise_10_90_s`` from
    ``flood_timescales`` is carried as the field-facing flashiness measure.

    Parameters
    ----------
    config : Config
        The section's configuration (supplies data root, river, KP and the
        scenario -> experiment mapping).

    Returns
    -------
    tuple of (dict, list of dict)
        The full member-record dict from ``load_hydrograph_ensemble``, and
        the per-member metric rows sorted flashiest-first.
    """
    source = config.hydrograph_source
    if source is None:
        raise ValueError("config has no hydrograph_source block (ADR-0020).")
    rating_csv = rating_curve_path(source.data_root, source.river)
    coefficients = load_rating_coefficients(rating_csv)
    workbook = resolve_band_workbook(
        source.data_root, river=source.river, kp=source.kp, scenario=config.scenario
    )
    records = load_hydrograph_ensemble(
        workbook, kp=source.kp, rating_coefficients=coefficients
    )

    rows: list[dict[str, Any]] = []
    for event_id, record in records.items():
        shape, _, _ = normalize_stage_shape(record.h)
        timescales = flood_timescales(record.h, record.native_dt)
        rows.append(
            {
                "event_id": event_id,
                "max_step_rise": float(np.max(np.diff(shape))),
                "rise_10_90_s": timescales["rise_10_90_s"],
                "rising_limb_s": timescales["rising_limb_s"],
                "plateau_s": timescales["plateau_s"],
                "peak_m_msl": timescales["peak_m"],
                "amplitude_m": timescales["amplitude_m"],
            }
        )
    rows.sort(key=lambda r: -r["max_step_rise"])
    return records, rows


def canonical_from_record(record: HydrographRecord) -> CanonicalShape:
    """Wrap a loaded member record as a ``CanonicalShape`` for G1 scaling.

    Identical composition to the tail of ``load_canonical_shape`` (normalize
    in stage domain under the node's own rating), applied to an
    already-loaded ensemble member so the flashiness scan's records are
    reused instead of re-reading the workbook.

    Parameters
    ----------
    record : HydrographRecord
        One member's stage record at the study node.

    Returns
    -------
    CanonicalShape
        The normalized shape with its base-flow floor.
    """
    shape, h_base_m, _ = normalize_stage_shape(record.h)
    return CanonicalShape(source_record=record, shape=shape, h_base_m=h_base_m)


def evaluate_case(
    record: HydrographRecord,
    theta: NDArray[np.float64],
    geometry: dict[str, float],
    config: Config,
    *,
    store_trajectory: bool = False,
) -> EvaluationResult:
    """One frozen-API M8 evaluation with the config's deterministic inputs.

    Mirrors exactly how ``run.run_fragility_analysis`` threads the ADR-0015
    deterministic Sellmeijer inputs and the ADR-0025 foreland treatment into
    ``evaluate_realization``.

    Parameters
    ----------
    record : HydrographRecord
        The loading record (already on the desired integration grid).
    theta : numpy.ndarray, shape (7,)
        The realization's parameter vector (canonical order).
    geometry : dict of str to float
        The flat ADR-0010 geometry dict (possibly with an overridden L).
    config : Config
        Supplies the deterministic evaluator inputs.
    store_trajectory : bool, optional
        Retain l(t) for plotting. Default False.

    Returns
    -------
    EvaluationResult
        The M8 result.
    """
    return evaluate_realization(
        theta,
        record,
        geometry,
        store_trajectory=store_trajectory,
        alpha_exponent=config.alpha_exponent,
        alpha_exponent_transient=config.alpha_exponent_transient,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        foreland_open=config.foreland_treatment == "open_entry",
    )


def run_ladder(
    canonical: CanonicalShape,
    levels: NDArray[np.float64],
    dts: list[float],
    theta: NDArray[np.float64],
    geometry: dict[str, float],
    config: Config,
    label: str,
) -> dict[str, Any]:
    """Integrate the worst case at every (conditioning level, Delta-t) pair.

    Parameters
    ----------
    canonical : CanonicalShape
        The flashiest member's normalized shape.
    levels : numpy.ndarray
        Conditioning levels h_i [m MSL], ascending.
    dts : list of float
        The Delta-t rungs [s] (integer subdivisions of native).
    theta : numpy.ndarray, shape (7,)
        The worst-case parameter vector.
    geometry : dict of str to float
        The ADR-0010 geometry dict for this variant.
    config : Config
        The section configuration.
    label : str
        Progress label.

    Returns
    -------
    dict
        ``levels_m_msl`` plus, per Delta-t key, the terminal ``l_e_m`` list
        and both failure-flag lists.
    """
    out: dict[str, Any] = {
        "levels_m_msl": [float(x) for x in levels],
        "by_dt": {},
    }
    for dt in dts:
        start = time.perf_counter()
        l_e: list[float] = []
        f_trans: list[bool] = []
        f_static: list[bool] = []
        for level in levels:
            record = conditioning_record_for_level(
                canonical, float(level), scenario=config.scenario
            )
            record = resample_record(record, dt)
            result = evaluate_case(record, theta, geometry, config)
            l_e.append(result.l_e_final)
            f_trans.append(result.failure_trans)
            f_static.append(result.failure_static)
        out["by_dt"][f"{dt:g}"] = {
            "l_e_m": l_e,
            "failure_trans": f_trans,
            "failure_static": f_static,
        }
        print(
            f"    [{label}] dt = {dt:8.4f} s : {len(levels)} levels in "
            f"{time.perf_counter() - start:5.1f} s",
            flush=True,
        )
    return out


def breach_threshold_m(
    levels: NDArray[np.float64], failure_trans: list[bool]
) -> float | None:
    """Lowest conditioning level [m MSL] with a transient breach, or None."""
    for level, failed in zip(levels, failure_trans):
        if failed:
            return float(level)
    return None


def successive_metrics(
    levels: NDArray[np.float64],
    ladder: dict[str, Any],
    dts: list[float],
    seepage_length_m: float,
) -> dict[str, Any]:
    """Successive-halving convergence metrics over the level grid.

    For each adjacent rung pair (coarse Delta-t, fine Delta-t/2): the max
    relative terminal-l_e change over levels that neither branch-flip
    (stall vs breach differs -- the bifurcation neighborhood, reported
    separately) nor sit under the no-erosion floor at both rungs; the max
    absolute change on non-flip levels; the branch-flip count; and the
    breach-threshold shift.

    Parameters
    ----------
    levels : numpy.ndarray
        The grid the ladder ran on, ascending.
    ladder : dict
        Output of :func:`run_ladder`.
    dts : list of float
        The rung values, coarse to fine.
    seepage_length_m : float
        L for the breach classification (l_e >= L within float noise).

    Returns
    -------
    dict
        Per-pair metrics keyed ``"<coarse>-><fine>"``, plus the per-rung
        breach thresholds and trans-not-static level lists.
    """
    eps_breach = 1e-9 * max(1.0, seepage_length_m)
    pairs: dict[str, Any] = {}
    thresholds: dict[str, float | None] = {}
    trans_not_static: dict[str, list[float]] = {}

    for dt in dts:
        row = ladder["by_dt"][f"{dt:g}"]
        thresholds[f"{dt:g}"] = breach_threshold_m(levels, row["failure_trans"])
        trans_not_static[f"{dt:g}"] = [
            float(level)
            for level, ft, fs in zip(
                levels, row["failure_trans"], row["failure_static"]
            )
            if ft and not fs
        ]

    for dt_coarse, dt_fine in zip(dts[:-1], dts[1:]):
        a = np.asarray(ladder["by_dt"][f"{dt_coarse:g}"]["l_e_m"])
        b = np.asarray(ladder["by_dt"][f"{dt_fine:g}"]["l_e_m"])
        breach_a = a >= seepage_length_m - eps_breach
        breach_b = b >= seepage_length_m - eps_breach
        flips = breach_a != breach_b
        active = ~flips & ((a > L_E_FLOOR_M) | (b > L_E_FLOOR_M))
        if np.any(active):
            rel = np.abs(a[active] - b[active]) / np.maximum(b[active], L_E_FLOOR_M)
            max_rel = float(np.max(rel))
            argmax_level = float(levels[active][int(np.argmax(rel))])
        else:
            max_rel = 0.0
            argmax_level = None
        t_a = thresholds[f"{dt_coarse:g}"]
        t_b = thresholds[f"{dt_fine:g}"]
        shift = None if (t_a is None or t_b is None) else abs(t_a - t_b)
        pairs[f"{dt_coarse:g}->{dt_fine:g}"] = {
            "max_rel_l_e": max_rel,
            "max_rel_at_level_m_msl": argmax_level,
            "max_abs_l_e_m": (
                float(np.max(np.abs(a[~flips] - b[~flips]))) if np.any(~flips) else 0.0
            ),
            "n_branch_flips": int(np.count_nonzero(flips)),
            "flip_levels_m_msl": [float(x) for x in levels[flips]],
            "threshold_shift_m": shift,
            "passes_1pct": bool(max_rel <= REL_CRITERION and not np.any(flips)),
        }

    return {
        "pairs": pairs,
        "breach_threshold_m_msl": thresholds,
        "trans_not_static_levels": trans_not_static,
    }


def first_converged_dt(metrics: dict[str, Any], dts: list[float]) -> float | None:
    """Coarsest Delta-t whose halving check (and every finer one) passes."""
    verdicts = [
        metrics["pairs"][f"{c:g}->{f:g}"]["passes_1pct"]
        for c, f in zip(dts[:-1], dts[1:])
    ]
    for i in range(len(verdicts)):
        if all(verdicts[i:]):
            return dts[i]
    return None


def study_section(
    config_path: Path, quick: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the full stress study for one section config.

    Parameters
    ----------
    config_path : pathlib.Path
        A generated section YAML.
    quick : bool, optional
        Smoke mode: every 4th production level, rungs {native, /4, /16},
        no refined pass. Plumbing check only -- never evidence.

    Returns
    -------
    tuple of (dict, dict)
        The section's full evidence block (JSON-ready), and the loaded
        working objects (config, canonical shape, theta, geometry, the
        production canonical member's shape) for the trajectory/figure pass.
    """
    config = Config.from_yaml(config_path)
    geometry = config.geometry.as_evaluator_dict()
    print(f"\n=== {config.cross_section_id} ({config_path}) ===", flush=True)

    print("  scanning d4PDF ensemble for the flashiest rising limb...", flush=True)
    records, flash_rows = scan_ensemble_flashiness(config)
    chosen = flash_rows[0]
    chosen_record = records[chosen["event_id"]]
    validate_datum_consistency(chosen_record, config.geometry.z_toe)
    canonical = canonical_from_record(chosen_record)
    production_event = config.hydrograph_source.canonical_event_ids[0]
    canonical_row = next(
        (r for r in flash_rows if r["event_id"] == production_event), None
    )
    canonical_rank = (
        flash_rows.index(canonical_row) + 1 if canonical_row is not None else None
    )
    print(
        f"  flashiest: {chosen['event_id']} "
        f"(max one-step rise {chosen['max_step_rise']:.3f} of amplitude/h, "
        f"10-90% rise {chosen['rise_10_90_s'] / 3600.0:.0f} h); "
        f"production shape {production_event} ranks #{canonical_rank}",
        flush=True,
    )

    theta, theta_record = worst_case_theta(config)

    levels = np.asarray([float(x) for x in config.mc.conditioning_grid])
    dts = list(DT_LADDER_S)
    if quick:
        levels = levels[::4]
        dts = [DT_LADDER_S[0], DT_LADDER_S[2], DT_LADDER_S[4]]

    # Diagnostics at the top production level (theta-only quantities are
    # level-independent; one evaluation exposes H_c, l_c, r_e, lambda_in).
    diag_record = resample_record(
        conditioning_record_for_level(
            canonical, float(levels[-1]), scenario=config.scenario
        ),
        dts[-1],
    )
    diag = evaluate_case(diag_record, theta, geometry, config)
    d_bl_m = float(theta[PARAM_NAMES.index("D_bl")])
    barrier_stage = config.geometry.z_toe + diag.H_c + CRACK_RESISTANCE_FACTOR * d_bl_m
    diagnostics = {
        "H_c_m": diag.H_c,
        "l_c_m": diag.l_c,
        "lambda_in_m": diag.lambda_in,
        "r_e": diag.r_e,
        "static_failure_stage_m_msl": config.geometry.z_toe + diag.H_c,
        "continuum_breach_barrier_stage_m_msl": barrier_stage,
    }
    print(
        f"  worst-case theta: H_c = {diag.H_c:.3f} m, l_c = {diag.l_c:.2f} m, "
        f"r_e = {diag.r_e:.3f}; continuum breach barrier at "
        f"h = {barrier_stage:.2f} m MSL",
        flush=True,
    )

    print("  ladder over the production conditioning grid:", flush=True)
    production = run_ladder(canonical, levels, dts, theta, geometry, config, "grid")
    production_metrics = successive_metrics(levels, production, dts, geometry["L"])

    refined = None
    refined_metrics = None
    refined_levels: NDArray[np.float64] | None = None
    if not quick:
        found = [
            t
            for t in production_metrics["breach_threshold_m_msl"].values()
            if t is not None
        ]
        if found:
            lo = max(float(levels[0]), min(found) - REFINE_PAD_M)
            hi = min(float(levels[-1]), max(found) + REFINE_PAD_M)
            refined_levels = np.round(
                np.arange(lo, hi + REFINE_STEP_M / 2, REFINE_STEP_M), 6
            )
            refined_dts = dts + [DT_REFERENCE_S]
            print(
                f"  refined threshold grid {lo:.2f}-{hi:.2f} m MSL "
                f"({refined_levels.size} levels, extra rung "
                f"{DT_REFERENCE_S:g} s):",
                flush=True,
            )
            refined = run_ladder(
                canonical,
                refined_levels,
                refined_dts,
                theta,
                geometry,
                config,
                "refined",
            )
            refined_metrics = successive_metrics(
                refined_levels, refined, refined_dts, geometry["L"]
            )
        else:
            print(
                "  no transient breach anywhere on the production grid; "
                "refined pass skipped.",
                flush=True,
            )

    # Low-L stress variant (L is stochastic in production, sampled
    # independently of theta): p01 of Lognormal(mean = geometry L,
    # cov = seepage_length_cov). Smaller L raises the rate AND shortens the
    # breach target -- the harshest plausible geometry for overshoot.
    variant = None
    if not quick and config.seepage_length_cov:
        l_q01 = lognormal_quantile(geometry["L"], config.seepage_length_cov, Q_LOW)
        geometry_q01 = {**geometry, "L": l_q01}
        print(
            f"  low-L stress variant: L = {l_q01:.2f} m "
            f"(p01 of Lognormal(mean {geometry['L']:g}, "
            f"cov {config.seepage_length_cov:g})), production grid:",
            flush=True,
        )
        variant_ladder = run_ladder(
            canonical,
            levels,
            dts + [DT_REFERENCE_S],
            theta,
            geometry_q01,
            config,
            "low-L",
        )
        variant = {
            "L_m": l_q01,
            "ladder": variant_ladder,
            "metrics": successive_metrics(
                levels, variant_ladder, dts + [DT_REFERENCE_S], l_q01
            ),
        }

    production_shape, _, _ = normalize_stage_shape(records[production_event].h)
    block = {
        "config": str(config_path).replace("\\", "/"),
        "cross_section_id": config.cross_section_id,
        "event_selection": {
            "metric": "max one-native-step rise of the normalized stage shape",
            "chosen": chosen,
            "production_shape_reference": canonical_row,
            "production_shape_rank": canonical_rank,
            "n_members_scanned": len(flash_rows),
            "top10": flash_rows[:10],
        },
        "worst_case_theta": theta_record,
        "diagnostics": diagnostics,
        "production_grid": {"ladder": production, "metrics": production_metrics},
        "refined_grid": (
            None if refined is None else {"ladder": refined, "metrics": refined_metrics}
        ),
        "low_L_variant": variant,
    }
    extras = {
        "config": config,
        "canonical": canonical,
        "theta": theta,
        "geometry": geometry,
        "production_shape": production_shape,
        "production_event_id": production_event,
    }
    return block, extras


def _dt_color(dt: float) -> str:
    """Sequential blue ramp position for a ladder rung (dark = finer)."""
    ramp = [
        "#86b6ef",
        "#6da7ec",
        "#5598e7",
        "#3987e5",
        "#2a78d6",
        "#256abf",
        "#1c5cab",
        "#184f95",
        "#104281",
        "#0d366b",
    ]
    k = int(round(math.log2(NATIVE_DT_S / dt)))
    return ramp[min(k, len(ramp) - 1)]


def _dt_label(dt: float) -> str:
    """Human label for a rung."""
    return f"{dt:g} s"


def make_figure(
    payload: dict[str, Any],
    trajectories: dict[str, Any],
    figure_path: Path,
) -> None:
    """Render the four-panel evidence figure.

    (a) chosen flashiest shape vs the production canonical shape;
    (b) l(t) at the showcase level for a subset of rungs;
    (c) terminal l_e vs conditioning level per rung (refined grid);
    (d) successive-halving max relative terminal-l_e change vs Delta-t.

    Parameters
    ----------
    payload : dict
        The full evidence payload (all sections).
    trajectories : dict
        Showcase trajectories per section from :func:`collect_trajectories`.
    figure_path : pathlib.Path
        Output PNG path.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink = "#0b0b0b"
    ink2 = "#52514e"
    muted = "#898781"
    grid = "#e1e0d9"
    baseline = "#c3c2b7"
    surface = "#fcfcfb"
    section_colors = ["#2a78d6", "#1baf7a"]

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 9,
            "text.color": ink,
            "axes.edgecolor": baseline,
            "axes.labelcolor": ink2,
            "axes.titlecolor": ink,
            "xtick.color": muted,
            "ytick.color": muted,
            "axes.grid": True,
            "grid.color": grid,
            "grid.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": surface,
            "axes.facecolor": surface,
        }
    )

    sections = payload["sections"]
    primary_id = payload["primary_section"]
    primary = sections[primary_id]

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.6))
    ax_a, ax_b, ax_c, ax_d = axes.flat

    # (a) shapes ------------------------------------------------------------
    traj = trajectories[primary_id]
    t_h = np.asarray(traj["shape_t_s"]) / 3600.0
    ax_a.plot(
        t_h,
        traj["chosen_shape"],
        color="#2a78d6",
        lw=1.6,
        label=f"flashiest: {primary['event_selection']['chosen']['event_id']}",
    )
    ax_a.plot(
        t_h,
        traj["production_shape"],
        color=muted,
        lw=1.2,
        ls="--",
        label=f"production shape: {traj['production_event_id']}",
    )
    ax_a.set_xlabel("time [h]")
    ax_a.set_ylabel("normalized stage shape [-]")
    ax_a.set_title("(a) Selected flashiest d4PDF member", loc="left", fontsize=10)
    ax_a.legend(frameon=False, fontsize=8, loc="upper left")

    # (b) trajectories -------------------------------------------------------
    for dt_key, tr in traj["by_dt"].items():
        dt = float(dt_key)
        t_hours = np.asarray(tr["t_s"]) / 3600.0
        ax_b.plot(
            t_hours,
            tr["l_m"],
            color=_dt_color(dt),
            lw=1.4,
            label=f"Δt = {_dt_label(dt)}",
        )
    ax_b.axhline(traj["l_c_m"], color=muted, lw=0.9, ls=":", zorder=1)
    ax_b.text(
        0.99,
        traj["l_c_m"],
        " l_c",
        color=muted,
        fontsize=8,
        va="bottom",
        ha="right",
        transform=ax_b.get_yaxis_transform(),
    )
    ax_b.axhline(traj["L_m"], color=muted, lw=0.9, ls="--", zorder=1)
    ax_b.text(
        0.99,
        traj["L_m"],
        " L (breach)",
        color=muted,
        fontsize=8,
        va="bottom",
        ha="right",
        transform=ax_b.get_yaxis_transform(),
    )
    ax_b.set_xlabel("time [h]")
    ax_b.set_ylabel("pipe length l(t) [m]")
    ax_b.set_title(
        f"(b) Worst-case trajectories at h = {traj['showcase_level_m_msl']:g} m MSL"
        f" ({primary_id})",
        loc="left",
        fontsize=10,
    )
    ax_b.legend(frameon=False, fontsize=8, loc="upper left")

    # (c) terminal l_e vs level ----------------------------------------------
    grid_block = primary["refined_grid"] or primary["production_grid"]
    levels_c = np.asarray(grid_block["ladder"]["levels_m_msl"])
    show_dts = [
        dt
        for dt in [3600.0, 1800.0, 900.0, 225.0, 28.125]
        if f"{dt:g}" in grid_block["ladder"]["by_dt"]
    ]
    for dt in show_dts:
        ax_c.plot(
            levels_c,
            grid_block["ladder"]["by_dt"][f"{dt:g}"]["l_e_m"],
            color=_dt_color(dt),
            lw=1.4,
            marker="o",
            ms=2.5,
            label=f"Δt = {_dt_label(dt)}",
        )
    ax_c.set_xlabel("conditioning stage h [m MSL]")
    ax_c.set_ylabel("terminal eroded length l_e [m]")
    ax_c.set_title(
        f"(c) Terminal l_e vs stage, worst-case θ ({primary_id})",
        loc="left",
        fontsize=10,
    )
    ax_c.legend(frameon=False, fontsize=8, loc="upper left")

    # (d) convergence --------------------------------------------------------
    for color, (section_id, block) in zip(section_colors, sections.items()):
        grid_block = block["refined_grid"] or block["production_grid"]
        pairs = grid_block["metrics"]["pairs"]
        xs, ys, flips = [], [], []
        for key, row in pairs.items():
            dt_coarse = float(key.split("->")[0])
            xs.append(dt_coarse)
            ys.append(max(row["max_rel_l_e"], 1e-8))
            flips.append(row["n_branch_flips"] > 0)
        order = np.argsort(xs)
        xs_arr = np.asarray(xs)[order]
        ys_arr = np.asarray(ys)[order]
        flips_arr = np.asarray(flips)[order]
        ax_d.plot(xs_arr, ys_arr, color=color, lw=1.4, label=section_id, zorder=3)
        ax_d.scatter(
            xs_arr[~flips_arr],
            ys_arr[~flips_arr],
            s=24,
            color=color,
            zorder=4,
        )
        if np.any(flips_arr):
            ax_d.scatter(
                xs_arr[flips_arr],
                ys_arr[flips_arr],
                s=30,
                facecolors=surface,
                edgecolors=color,
                linewidths=1.4,
                zorder=4,
            )
    ax_d.axhline(REL_CRITERION, color=muted, lw=0.9, ls="--")
    ax_d.text(
        0.02,
        REL_CRITERION,
        " 1% criterion",
        color=muted,
        fontsize=8,
        va="bottom",
        transform=ax_d.get_yaxis_transform(),
    )
    ax_d.set_xscale("log", base=2)
    ax_d.set_yscale("log")
    tick_dts = [3600.0, 1800.0, 900.0, 450.0, 225.0, 112.5, 56.25, 28.125]
    ax_d.set_xticks(tick_dts)
    ax_d.set_xticklabels(
        ["3600", "1800", "900", "450", "225", "112.5", "56.25", "28.125"],
        fontsize=8,
    )
    ax_d.minorticks_off()
    ax_d.set_xlabel("Δt [s] (error of Δt vs Δt/2, plotted at Δt)")
    ax_d.set_ylabel("max relative change in terminal l_e [-]")
    ax_d.set_title(
        "(d) Successive-halving convergence (open markers: branch flips)",
        loc="left",
        fontsize=10,
    )
    ax_d.legend(frameon=False, fontsize=8, loc="upper right")
    ax_d.invert_xaxis()

    fig.suptitle(
        "Worst-case forward-Euler timestep stress test (spec §11; ADR-0039):\n"
        "p99 k_aq × p99 C_e × p01 D_bl on the flashiest d4PDF rising limb",
        fontsize=11,
        x=0.02,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=220)
    plt.close(fig)
    print(f"figure written: {figure_path}", flush=True)


def collect_trajectories(
    section_block: dict[str, Any],
    config: Config,
    canonical: CanonicalShape,
    production_shape: NDArray[np.float64],
    production_event_id: str,
    theta: NDArray[np.float64],
    geometry: dict[str, float],
) -> dict[str, Any]:
    """Re-run the showcase level with stored trajectories for panel (b).

    The showcase level is the lowest level where the native rung breaches
    but the finest rung does not (the maximal-artifact level); if none, the
    finest rung's own breach threshold; if that is also absent, the top
    production level.

    Parameters
    ----------
    section_block : dict
        The section's evidence block from :func:`study_section`.
    config, canonical, theta, geometry
        As in :func:`study_section`.
    production_shape : numpy.ndarray
        The production canonical member's normalized shape (for panel a).
    production_event_id : str
        Its event id.

    Returns
    -------
    dict
        Shapes and per-rung trajectories at the showcase level.
    """
    grid_block = section_block["refined_grid"] or section_block["production_grid"]
    ladder = grid_block["ladder"]
    levels = np.asarray(ladder["levels_m_msl"])
    dt_keys = list(ladder["by_dt"])
    native = np.asarray(ladder["by_dt"][dt_keys[0]]["failure_trans"])
    finest = np.asarray(ladder["by_dt"][dt_keys[-1]]["failure_trans"])
    artifact = native & ~finest
    if np.any(artifact):
        showcase = float(levels[np.argmax(artifact)])
    elif np.any(finest):
        showcase = float(levels[np.argmax(finest)])
    else:
        showcase = float(levels[-1])

    show_dts = [
        dt for dt in [3600.0, 1800.0, 900.0, 225.0, 28.125] if f"{dt:g}" in dt_keys
    ]
    by_dt: dict[str, Any] = {}
    l_c_m = None
    for dt in show_dts:
        record = resample_record(
            conditioning_record_for_level(
                canonical, showcase, scenario=config.scenario
            ),
            dt,
        )
        result = evaluate_case(record, theta, geometry, config, store_trajectory=True)
        l_c_m = result.l_c
        by_dt[f"{dt:g}"] = {
            "t_s": [float(x) for x in record.t],
            "l_m": [float(x) for x in np.asarray(result.l_trajectory).ravel()],
        }
    return {
        "showcase_level_m_msl": showcase,
        "L_m": geometry["L"],
        "l_c_m": l_c_m,
        "by_dt": by_dt,
        "shape_t_s": [float(x) for x in canonical.source_record.t],
        "chosen_shape": [float(x) for x in canonical.shape],
        "production_shape": [float(x) for x in production_shape],
        "production_event_id": production_event_id,
    }


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--confirm-config", default=DEFAULT_CONFIRM_CONFIG)
    parser.add_argument("--skip-confirm", action="store_true")
    parser.add_argument("--output-json", default=DEFAULT_JSON)
    parser.add_argument("--figure", default=DEFAULT_FIGURE)
    parser.add_argument("--quick", action="store_true", help="plumbing smoke only")
    args = parser.parse_args()

    start = time.perf_counter()
    payload: dict[str, Any] = {
        "adr": "0039",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "criterion": {
            "quantity": "terminal eroded length l_e per conditioning level",
            "rule": "successive Delta-t halving relative change <= 1%, zero "
            "stall-vs-breach branch flips, stationary breach threshold",
            "rel_threshold": REL_CRITERION,
            "worst_case_quantiles": {"k_aq": Q_HIGH, "C_e": Q_HIGH, "D_bl": Q_LOW},
        },
        "dt_ladder_s": DT_LADDER_S + [DT_REFERENCE_S],
        "sections": {},
    }

    config_paths = [Path(args.config)]
    if not args.skip_confirm and args.confirm_config:
        config_paths.append(Path(args.confirm_config))

    trajectories: dict[str, Any] = {}
    for path in config_paths:
        block, extras = study_section(path, quick=args.quick)
        payload["sections"][block["cross_section_id"]] = block
        trajectories[block["cross_section_id"]] = collect_trajectories(
            block,
            extras["config"],
            extras["canonical"],
            extras["production_shape"],
            extras["production_event_id"],
            extras["theta"],
            extras["geometry"],
        )

    payload["primary_section"] = next(iter(payload["sections"]))

    # Verdict block: per section, the coarsest converged rung.
    verdicts: dict[str, Any] = {}
    for section_id, block in payload["sections"].items():
        grid_block = block["refined_grid"] or block["production_grid"]
        dts_used = [float(k) for k in grid_block["ladder"]["by_dt"]]
        verdicts[section_id] = {
            "native_converged": grid_block["metrics"]["pairs"][
                f"{dts_used[0]:g}->{dts_used[1]:g}"
            ]["passes_1pct"],
            "first_converged_dt_s": first_converged_dt(grid_block["metrics"], dts_used),
        }
    payload["verdicts"] = verdicts

    json_path = Path(args.output_json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nevidence written: {json_path}", flush=True)

    if not args.quick:
        make_figure(payload, trajectories, Path(args.figure))

    print("\n=== VERDICTS ===", flush=True)
    for section_id, verdict in verdicts.items():
        print(
            f"  {section_id}: native 3600 s converged = "
            f"{verdict['native_converged']}; first converged rung = "
            f"{verdict['first_converged_dt_s']} s",
            flush=True,
        )
    print(f"total {time.perf_counter() - start:.0f} s", flush=True)


if __name__ == "__main__":
    main()
