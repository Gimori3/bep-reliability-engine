"""Green Light item 1: the coefficient of uniformity, piping resistance and suffusion.

Driver for `docs/decisions/uniformity-coefficient-study.md` (Part 1 pre-registered
and committed before any arm ran). Three parts, all read-only on production:

1. **Internal stability** of the 28 aquifer (Ag) gradations. The whole-specimen
   curve is reconstructed exactly as item 4 reconstructs it (the routine is
   imported, not copied), and the Kenney-Lau shape index (H/F)min is evaluated
   over F <= 20 % (widely graded; F <= 30 % reported as a sensitivity). Because
   log-linear interpolation fills any gap in a gap-graded curve, it biases H
   upward, so a rigorous upper bound on (H/F)min over EVERY monotone curve
   through the tabulated points is computed as well, and a specimen is called
   unstable robustly only where that bound is below 1.

2. **The C_u arms through Phase 1.** C_u enters only the Sellmeijer resistance
   factor, as ``(C_u / 1.81)^0.13``, so an arm is an exact multiplier ``c`` on the
   single-source H_c. It is applied in memory through the bedding angle
   (``theta' = atan(c tan 37 deg)``), which enters F_r and nothing else, with the
   production seed and N; each baseline must be bit-identical to the persisted
   sweep. Measured: monotonicity, the static stretch, curve shifts, the design
   level, and the displacement of B and delta-beta at quotable levels with the
   metric study's own paired bootstrap.

3. **The arms through Phase 3** on the prior side, via the conductivity study's
   composition path, which must first reproduce ``rq4_annual.csv`` exactly for the
   baseline (its gate 1) and then again from the in-memory baseline curves (so
   the in-memory route is proved identical to the persisted one).

Usage (repo root)::

    python scripts/uniformity_coefficient_study.py --n-jobs 8
    python scripts/uniformity_coefficient_study.py --stability-only
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

RECORD_JSON = REPO_ROOT / "docs" / "decisions" / "uniformity-coefficient-study.json"
ITEM4_JSON = REPO_ROOT / "docs" / "decisions" / "bimodal-foundation-d70-study.json"
RESULTS = REPO_ROOT / "results"

SECTIONS = ("57.4", "58.8", "60.0", "62.0")
CONFIGS = {
    kp: REPO_ROOT / "configs" / f"kp{kp.replace('.', '_')}_historical_matrix.yaml"
    for kp in SECTIONS
}
#: Design-level anchors of the RQ1 comparison (the grid level nearest is read).
DESIGN_ANCHOR_M = {"57.4": 39.21, "58.8": 41.00, "60.0": 42.75, "62.0": 46.39}

C_U_MEAN = 1.81
C_U_EXPONENT = 0.13
C_U_TESTED_MAX = 2.6
THETA_REPOSE_DEG = 37.0

#: Kenney-Lau evaluation ranges (Ronnqvist and Viklander 2014): F up to 20 %
#: for a widely graded material, 30 % for a uniformly graded one.
KL_F_MAX = {"widely_graded": 20.0, "uniformly_graded": 30.0}
#: Ronnqvist (2017) zones for silt-sand-gravel soils.
KL_ZONES = (
    (0.45, "suffusive"),
    (0.68, "potentially unstable"),
    (1.0, "potential stability"),
)
#: Finer-fraction thresholds: ~35 % (Ronnqvist 2017, after Wan 2006) and ~25 %
#: (Okamura et al. 2025, after Skempton and Brogan 1994).
FINER_FRACTION_THRESHOLDS = (25.0, 35.0)
STATIC_QUANTILES = (0.05, 0.1, 0.25, 0.5)


def _load_module(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ITEM4 = _load_module("bimodal_foundation_d70_study")


def factor_for_cu(cu: float) -> float:
    """The Sellmeijer multiplier on H_c for a uniformity coefficient."""
    return (cu / C_U_MEAN) ** C_U_EXPONENT


def theta_for_factor(c: float) -> float:
    """Bedding angle [deg] whose tan scales F_r, hence H_c, by exactly ``c``."""
    return math.degrees(math.atan(c * math.tan(math.radians(THETA_REPOSE_DEG))))


# --------------------------------------------------------------------------- #
# 1. Internal stability                                                          #
# --------------------------------------------------------------------------- #
def _envelopes(sizes: np.ndarray, passing: np.ndarray):
    """Tightest bounds on F(x) for any monotone curve through the points."""

    def upper(x: float) -> float:
        idx = np.searchsorted(sizes, x, side="left")
        return float(passing[idx]) if idx < sizes.size else 100.0

    def lower(x: float) -> float:
        idx = np.searchsorted(sizes, x, side="right") - 1
        return float(passing[idx]) if idx >= 0 else 0.0

    return upper, lower


def kenney_lau(
    row: dict[str, Any], f_max: float, d_min: float | None = None
) -> dict[str, Any] | None:
    """(H/F)min on the reconstructed curve, and its upper bound over all curves.

    H(D) = F(4D) - F(D), evaluated for D up to the size at which F = ``f_max``
    (a tabulated percentile, so the range is exact for every consistent curve).
    ``d_min`` restricts the window from below (the post-hoc sand window,
    D >= 0.075 mm); ``None`` is returned when the window is empty.
    """
    sizes, passing, dropped = _ITEM4.grading_points(row)
    d_top = _ITEM4.size_at(sizes, passing, f_max)
    positive = sizes[passing > 0.0]
    d_bottom = float(positive[0]) if positive.size else float(sizes[0])
    if d_min is not None:
        d_bottom = max(d_bottom, d_min)
        if d_top <= d_bottom:
            return None
    grid = np.exp(np.linspace(math.log(d_bottom), math.log(d_top), 400))
    log_sizes = np.log(sizes)

    def f(x):
        return np.interp(np.log(x), log_sizes, passing, left=0.0, right=100.0)

    fd = f(grid)
    h = f(4.0 * grid) - fd
    ok = fd > 0.0
    ratio = np.where(ok, h / np.where(ok, fd, 1.0), np.inf)
    i_min = int(np.argmin(ratio))

    upper, lower = _envelopes(sizes, passing)
    bound = np.array(
        [(upper(4.0 * d) / lower(d) - 1.0) if lower(d) > 0.0 else np.inf for d in grid]
    )
    return {
        "f_max_pct": f_max,
        "hf_min_interpolated": float(ratio[i_min]),
        "d_at_min_mm": float(grid[i_min]),
        "f_at_min_pct": float(fd[i_min]),
        "hf_min_upper_bound": float(np.min(bound)),
        "dropped_points": dropped,
    }


def _zone(hf: float) -> str:
    for limit, name in KL_ZONES:
        if hf < limit:
            return name
    return "stable"


def internal_stability() -> dict[str, Any]:
    rows = [r for r in _ITEM4.load_specimens() if r["layer"] == "Ag"]
    rows = [r for r in rows if r["kp"] in SECTIONS]
    specimens = []
    for row in rows:
        p2 = 100.0 - row["gravel_pct"]
        kl = {name: kenney_lau(row, f) for name, f in KL_F_MAX.items()}
        # Post hoc (not pre-registered): the window above the fines, where the
        # sand matrix and the gravel framework meet.
        kl["sand_window"] = kenney_lau(row, KL_F_MAX["widely_graded"], d_min=0.075)
        wg = kl["widely_graded"]
        specimens.append(
            {
                "kp": row["kp"],
                "borehole": row["borehole"],
                "test_no": row["test_no"],
                "depth_m": [row["depth_top_m"], row["depth_bot_m"]],
                "gravel_pct": row["gravel_pct"],
                "sand_pct": row["sand_pct"],
                "fines_pct": (row["silt_pct"] or 0.0) + (row["clay_pct"] or 0.0),
                "passing_2mm_pct": p2,
                "uc_printed": row["uc"],
                "ucc_printed": row["ucc"],
                "gravel_supported": p2 < 50.0,
                "kenney_lau": kl,
                "zone_interpolated": _zone(wg["hf_min_interpolated"]),
                "unstable_interpolated": wg["hf_min_interpolated"] < 1.0,
                "unstable_robust": wg["hf_min_upper_bound"] < 1.0,
            }
        )
    gravels = [s for s in specimens if s["gravel_supported"]]
    sands = [s for s in specimens if not s["gravel_supported"]]

    def count(items, key):
        return sum(1 for s in items if s[key])

    ucc = [s["ucc_printed"] for s in specimens if s["ucc_printed"] is not None]
    summary = {
        "n_specimens": len(specimens),
        "n_gravel_supported": len(gravels),
        "n_sand_rich": len(sands),
        "gravels_unstable_interpolated": count(gravels, "unstable_interpolated"),
        "gravels_unstable_robust": count(gravels, "unstable_robust"),
        "sand_rich_unstable_interpolated": count(sands, "unstable_interpolated"),
        "gravel_zones_interpolated": {
            z: sum(1 for s in gravels if s["zone_interpolated"] == z)
            for z in (
                "suffusive",
                "potentially unstable",
                "potential stability",
                "stable",
            )
        },
        "gravel_hf_min_interpolated_range": [
            min(
                s["kenney_lau"]["widely_graded"]["hf_min_interpolated"] for s in gravels
            ),
            max(
                s["kenney_lau"]["widely_graded"]["hf_min_interpolated"] for s in gravels
            ),
        ],
        "gravel_hf_min_interpolated_median": float(
            np.median(
                [
                    s["kenney_lau"]["widely_graded"]["hf_min_interpolated"]
                    for s in gravels
                ]
            )
        ),
        "gravel_d_at_min_mm_range": [
            min(s["kenney_lau"]["widely_graded"]["d_at_min_mm"] for s in gravels),
            max(s["kenney_lau"]["widely_graded"]["d_at_min_mm"] for s in gravels),
        ],
        "sand_window_post_hoc": {
            "n_with_window": sum(
                1 for s in specimens if s["kenney_lau"]["sand_window"]
            ),
            "gravels_unstable_interpolated": sum(
                1
                for s in gravels
                if s["kenney_lau"]["sand_window"]
                and s["kenney_lau"]["sand_window"]["hf_min_interpolated"] < 1.0
            ),
            "gravels_unstable_robust": sum(
                1
                for s in gravels
                if s["kenney_lau"]["sand_window"]
                and s["kenney_lau"]["sand_window"]["hf_min_upper_bound"] < 1.0
            ),
            "sand_rich_unstable_interpolated": sum(
                1
                for s in sands
                if s["kenney_lau"]["sand_window"]
                and s["kenney_lau"]["sand_window"]["hf_min_interpolated"] < 1.0
            ),
            "gravel_zones_interpolated": {
                z: sum(
                    1
                    for s in gravels
                    if s["kenney_lau"]["sand_window"]
                    and _zone(s["kenney_lau"]["sand_window"]["hf_min_interpolated"])
                    == z
                )
                for z in (
                    "suffusive",
                    "potentially unstable",
                    "potential stability",
                    "stable",
                )
            },
        },
        "gravels_unstable_interpolated_f30": sum(
            1
            for s in gravels
            if s["kenney_lau"]["uniformly_graded"]["hf_min_interpolated"] < 1.0
        ),
        "finer_fraction_below": {
            f"{t:g}": sum(1 for s in gravels if s["passing_2mm_pct"] < t)
            for t in FINER_FRACTION_THRESHOLDS
        },
        "gravel_passing_2mm_range": [
            min(s["passing_2mm_pct"] for s in gravels),
            max(s["passing_2mm_pct"] for s in gravels),
        ],
        "ucc_printed_range": [min(ucc), max(ucc)],
        "ucc_between_1_and_3": sum(1 for u in ucc if 1.0 <= u <= 3.0),
        "n_ucc": len(ucc),
    }
    return {
        "method": (
            "Whole-specimen curve through (0.005 mm, clay), (0.075 mm, fines), d10, "
            "d20, d30, d50, d60, (2 mm, 100 - gravel), (dmax, 100), log-linear "
            "(item 4's reconstruction). H(D) = F(4D) - F(D); (H/F)min over D with "
            "F(D) <= 20 % (widely graded; all 28 have Uc > 3) and <= 30 %. The "
            "upper bound uses, at each D, the largest F(4D) and smallest F(D) any "
            "monotone curve through the tabulated points allows."
        ),
        "summary": summary,
        "specimens": specimens,
    }


# --------------------------------------------------------------------------- #
# 2. The arms through Phase 1                                                    #
# --------------------------------------------------------------------------- #
def arm_factors() -> dict[str, dict[str, dict[str, float]]]:
    by_section = json.loads(ITEM4_JSON.read_text(encoding="utf-8"))["gradations"][
        "by_section"
    ]
    arms: dict[str, dict[str, dict[str, float]]] = {"cap": {}, "sand": {}, "matrix": {}}
    for kp in SECTIONS:
        cus = {
            "cap": C_U_TESTED_MAX,
            "sand": by_section[kp]["S2_cu"]["median_mm"],
            "matrix": by_section[kp]["M2_cu"]["median_mm"],
        }
        for arm, cu in cus.items():
            c = factor_for_cu(cu)
            arms[arm][kp] = {
                "c_u": cu,
                "factor": c,
                "theta_repose_deg": theta_for_factor(c),
            }
    return arms


def _run(kp: str, theta_deg: float | None, n_jobs: int):
    import yaml

    from bep_reliability_engine.config import Config
    from bep_reliability_engine.run import run_fragility_analysis

    data = yaml.safe_load(CONFIGS[kp].read_text(encoding="utf-8"))
    if theta_deg is not None:
        data["theta_repose_deg"] = float(theta_deg)
    return run_fragility_analysis(
        Config.model_validate(data), n_jobs=n_jobs, progress=False, persist=False
    )


def _assert_bit_identical(result, kp: str) -> None:
    import h5py

    path = RESULTS / f"tokachi_kp{kp}_historical_matrix.h5"
    with h5py.File(path, "r") as handle:
        same = np.array_equal(
            result.P_f_static_raw, handle["P_f_static_raw"][()]
        ) and np.array_equal(result.P_f_trans_raw, handle["P_f_trans_raw"][()])
    if not same:
        raise AssertionError(f"KP {kp}: in-memory baseline differs from {path.name}")


def _stage_at(grid: np.ndarray, p: np.ndarray, q: float) -> float | None:
    """Stage at which a (monotone, raw) curve first reaches q, log-free interp."""
    p = np.maximum.accumulate(np.asarray(p, dtype=float))
    if p[-1] < q or p[0] >= q:
        return None
    i = int(np.argmax(p >= q))
    p0, p1 = p[i - 1], p[i]
    return float(grid[i - 1] + (q - p0) / (p1 - p0) * (grid[i] - grid[i - 1]))


def _beta(p: float) -> float | None:
    from scipy.stats import norm

    return float(-norm.ppf(p)) if 0.0 < p < 1.0 else None


def _anchor(result, kp: str) -> dict[str, Any]:
    grid = np.asarray(result.conditioning_grid, dtype=float)
    i = int(np.argmin(np.abs(grid - DESIGN_ANCHOR_M[kp])))
    fs = np.asarray(result.failure_matrix_stat[:, i], dtype=bool)
    ft = np.asarray(result.failure_matrix_tran[:, i], dtype=bool)
    n = fs.size
    ps, pt = fs.sum() / n, ft.sum() / n
    bs, bt = _beta(ps), _beta(pt)
    return {
        "stage_m": float(grid[i]),
        "static_failures": int(fs.sum()),
        "transient_failures": int(ft.sum()),
        "P_s": float(ps),
        "P_t": float(pt),
        "B": float(ps / pt) if pt > 0 else None,
        "delta_beta": (bt - bs) if (bs is not None and bt is not None) else None,
    }


def phase1(n_jobs: int, n_boot: int) -> tuple[dict[str, Any], dict[str, Any]]:
    metric = _load_module("metric_decomposition_study")
    attainable = metric._RQ1.attainable_maxima()
    arms = arm_factors()
    out: dict[str, Any] = {"arms": arms, "sections": {}}
    results: dict[str, Any] = {}
    import h5py

    for kp in SECTIONS:
        t0 = time.time()
        base = _run(kp, None, n_jobs)
        _assert_bit_identical(base, kp)
        results[(kp, "baseline")] = base
        grid = np.asarray(base.conditioning_grid, dtype=float)
        with h5py.File(RESULTS / f"tokachi_kp{kp}_historical_bulk.h5", "r") as h:
            bulk_ps = h["P_f_static_raw"][()]
            bulk_pt = h["P_f_trans_raw"][()]
            bulk_grid = h["conditioning_grid"][()]
        import yaml

        z_toe = float(
            yaml.safe_load(CONFIGS[kp].read_text(encoding="utf-8"))["geometry"]["z_toe"]
        )
        rec: dict[str, Any] = {
            "z_toe_m": z_toe,
            "attainable_max_m": attainable[kp],
            "baseline": {
                "anchor": _anchor(base, kp),
                "P_s": [float(x) for x in base.P_f_static_raw],
                "P_t": [float(x) for x in base.P_f_trans_raw],
            },
            "grid_m": [float(x) for x in grid],
            "bulk_lever": {},
            "arms": {},
        }
        for q in STATIC_QUANTILES:
            m = _stage_at(grid, base.P_f_static_raw, q)
            b = _stage_at(bulk_grid, bulk_ps, q)
            rec["bulk_lever"][f"static_q{q:g}"] = (
                (b - z_toe) / (m - z_toe) if (m is not None and b is not None) else None
            )
            mt = _stage_at(grid, base.P_f_trans_raw, q)
            bt = _stage_at(bulk_grid, bulk_pt, q)
            rec["bulk_lever"][f"transient_shift_q{q:g}_m"] = (
                (bt - mt) if (mt is not None and bt is not None) else None
            )
        for arm, spec in arms.items():
            res = _run(kp, spec[kp]["theta_repose_deg"], n_jobs)
            results[(kp, arm)] = res
            bs, bt_ = base.failure_matrix_stat, base.failure_matrix_tran
            as_, at_ = res.failure_matrix_stat, res.failure_matrix_tran
            mono = {
                "static_rows_failing_arm_not_baseline": int((as_ & ~bs).sum()),
                "transient_rows_failing_arm_not_baseline": int((at_ & ~bt_).sum()),
                "nesting_violations_arm": int((at_ & ~as_).sum()),
            }
            stretch, shifts = {}, {}
            for q in STATIC_QUANTILES:
                m = _stage_at(grid, base.P_f_static_raw, q)
                a = _stage_at(grid, res.P_f_static_raw, q)
                stretch[f"q{q:g}"] = (
                    (a - z_toe) / (m - z_toe)
                    if (m is not None and a is not None)
                    else None
                )
                for branch, pb, pa in (
                    ("static", base.P_f_static_raw, res.P_f_static_raw),
                    ("transient", base.P_f_trans_raw, res.P_f_trans_raw),
                ):
                    x0, x1 = _stage_at(grid, pb, q), _stage_at(grid, pa, q)
                    shifts[f"{branch}_q{q:g}_m"] = (
                        (x1 - x0) if (x0 is not None and x1 is not None) else None
                    )
            levels = []
            for i, level in enumerate(grid):
                counts = metric._pattern_counts(
                    bs[:, i], bt_[:, i], as_[:, i], at_[:, i]
                )
                entry = metric._displacement_ci(
                    counts,
                    n_boot=n_boot,
                    seed=metric._RQ1._stable_seed(f"uniformity-{arm}-{kp}-{level:.2f}"),
                )
                entry["level_m_msl"] = float(level)
                entry["quotable"] = bool(
                    level <= attainable[kp] + 1e-9
                    and entry["min_cell_failures"] >= metric.R1_MIN_ROWS
                    and np.isfinite(entry["rho"])
                    and np.isfinite(entry["delta_delta_beta"])
                )
                levels.append(entry)
            quot = [lv for lv in levels if lv["quotable"]]
            rec["arms"][arm] = {
                **spec[kp],
                "monotonicity": mono,
                "static_stretch": stretch,
                "curve_shifts": shifts,
                "anchor": _anchor(res, kp),
                "P_s": [float(x) for x in res.P_f_static_raw],
                "P_t": [float(x) for x in res.P_f_trans_raw],
                "n_quotable": len(quot),
                "quotable_rho_range": (
                    [min(lv["rho"] for lv in quot), max(lv["rho"] for lv in quot)]
                    if quot
                    else None
                ),
                "quotable_ddb_range": (
                    [
                        min(lv["delta_delta_beta"] for lv in quot),
                        max(lv["delta_delta_beta"] for lv in quot),
                    ]
                    if quot
                    else None
                ),
                "quotable_rho_resolved": sum(1 for lv in quot if lv["rho_resolved"]),
                "quotable_ddb_resolved": sum(
                    1 for lv in quot if lv["delta_delta_beta_resolved"]
                ),
                "quotable_disagree_rho_only": sum(
                    1
                    for lv in quot
                    if lv["rho_resolved"] and not lv["delta_delta_beta_resolved"]
                ),
                "quotable_disagree_ddb_only": sum(
                    1
                    for lv in quot
                    if lv["delta_delta_beta_resolved"] and not lv["rho_resolved"]
                ),
                "levels": levels,
            }
        rec["elapsed_s"] = round(time.time() - t0, 1)
        out["sections"][kp] = rec
        print(f"KP {kp} phase 1 done in {rec['elapsed_s']} s", flush=True)
    return out, results


# --------------------------------------------------------------------------- #
# 3. The arms through Phase 3 (prior side)                                       #
# --------------------------------------------------------------------------- #
def _curve_from_result(result, source_path: str):
    """The in-memory twin of ``system_integration.bep_input.load_bep_curve``."""
    from system_integration.bep_input import FragilityCurve, _deliverable_fit

    lower, upper = result.binomial_ci["transient"]
    p_raw = np.asarray(result.P_f_trans_raw, dtype=np.float64)
    fit = result.P_f_trans_fit
    datum = result.metadata.get("fragility_fit", {}).get("datum_m")
    return FragilityCurve(
        grid_m_msl=np.asarray(result.conditioning_grid, dtype=np.float64),
        p_raw=p_raw,
        ci_lower=np.asarray(lower, dtype=np.float64),
        ci_upper=np.asarray(upper, dtype=np.float64),
        fit=fit,
        fit_is_deliverable=_deliverable_fit(fit, p_raw),
        branch="transient",
        source="phase1_prior",
        source_path=source_path,
        datum_m=None if datum is None else float(datum),
    )


def _leading(row: dict[str, Any]) -> str:
    vals = {
        m: float(row[f"p_annual_{m}"])
        for m in ("bep", "overflow", "fluvial_scour")
        if row[f"p_annual_{m}"] != ""
    }
    if not vals or sum(vals.values()) <= 0.0:
        return "not defined"
    return max(vals, key=lambda m: vals[m])


def phase3(results: dict[str, Any]) -> dict[str, Any]:
    import csv

    cond = _load_module("conductivity_annualisation_study")
    campaign = cond._load_campaign_module()
    context = cond.build_context(campaign, "matrix", "prior")
    base_rows, _, _ = cond.annualise_variant(
        campaign, context, context["baseline_curves"], "matrix", "prior"
    )
    gate_persisted = cond.gate_one(base_rows, "matrix", "prior")

    kp_float = {kp: float(kp) for kp in SECTIONS}
    mem_curves = {
        kp_float[kp]: _curve_from_result(
            results[(kp, "baseline")],
            str(context["baseline_curves"][kp_float[kp]].source_path),
        )
        for kp in SECTIONS
    }
    mem_rows, _, _ = cond.annualise_variant(
        campaign, context, mem_curves, "matrix", "prior"
    )
    gate_in_memory = cond.gate_one(mem_rows, "matrix", "prior")

    with open(cond.PRODUCTION_TABLE, encoding="utf-8", newline="") as handle:
        bulk = {
            (float(r["kp"]), r["scenario"]): r
            for r in csv.DictReader(handle)
            if r["river"] == "Tokachi"
            and r["d70"] == "bulk"
            and r["bep_source"] == "prior"
            and r["lambda_ac_m"] == str(cond.LAMBDA_AC_M)
            and r["surface_variant"] == cond.SURFACE_VARIANT
        }

    arm_rows = {}
    for arm in ("cap", "sand", "matrix"):
        curves = {
            kp_float[kp]: _curve_from_result(results[(kp, arm)], f"in-memory:{arm}")
            for kp in SECTIONS
        }
        rows, _, _ = cond.annualise_variant(
            campaign, context, curves, "matrix", "prior"
        )
        arm_rows[arm] = rows

    # Segments without a BEP source must be untouched by every arm.
    untouched = all(
        arm_rows[arm][key] == row
        for arm in arm_rows
        for key, row in base_rows.items()
        if round(key[1], 1) not in kp_float.values() or key[0] != "Tokachi"
    )

    cells = []
    for kp in SECTIONS:
        for scenario in campaign.SCENARIOS:
            key = ("Tokachi", kp_float[kp], scenario)
            b = base_rows[key]
            cell = {
                "section": f"KP {kp}",
                "scenario": scenario,
                "baseline": {
                    "p_system": float(b["p_annual_system"]),
                    "p_bep": float(b["p_annual_bep"]),
                    "p_overflow": float(b["p_annual_overflow"]),
                    "share_bep": float(b["share_bep"]),
                    "leading": _leading(b),
                },
                "bulk_reading": {
                    "p_bep": float(bulk[(kp_float[kp], scenario)]["p_annual_bep"]),
                    "leading": _leading(bulk[(kp_float[kp], scenario)]),
                },
                "arms": {},
            }
            for arm, rows in arm_rows.items():
                r = rows[key]
                p_bep = float(r["p_annual_bep"])
                cell["arms"][arm] = {
                    "p_system": float(r["p_annual_system"]),
                    "p_bep": p_bep,
                    "share_bep": float(r["share_bep"]),
                    "leading": _leading(r),
                    "reverses": _leading(r) != cell["baseline"]["leading"],
                    "bep_reduction_factor": (
                        cell["baseline"]["p_bep"] / p_bep if p_bep > 0 else None
                    ),
                    "bep_clamped_above_grid": bool(r["bep_clamped_above_grid"]),
                }
            cells.append(cell)
    return {
        "side": "prior",
        "lambda_ac_m": cond.LAMBDA_AC_M,
        "surface_variant": cond.SURFACE_VARIANT,
        "gate_persisted_baseline": gate_persisted,
        "gate_in_memory_baseline": gate_in_memory,
        "non_bep_segments_untouched": untouched,
        "cells": cells,
        "reversals": {
            arm: [
                f"{c['section']} {c['scenario']}"
                for c in cells
                if c["arms"][arm]["reverses"]
            ]
            for arm in arm_rows
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--stability-only", action="store_true")
    parser.add_argument("--out", type=Path, default=RECORD_JSON)
    args = parser.parse_args(argv)

    record: dict[str, Any] = {
        "study": "uniformity-coefficient-study (Green Light item 1)",
        "note": "docs/decisions/uniformity-coefficient-study.md",
        "internal_stability": internal_stability(),
    }
    if not args.stability_only:
        p1, results = phase1(args.n_jobs, args.n_boot)
        record["phase1"] = p1
        record["phase3"] = phase3(results)
    args.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
