"""Bimodal foundation, operative d70 and the distribution chosen for it.

Green Light item 4 study driver. Study note of record:
``docs/decisions/bimodal-foundation-d70-study.md`` (Part 1 pre-registered and
committed before this driver computed anything). Evidence:
``docs/decisions/bimodal-foundation-d70-study.json``.

What it does, in order:

1. Loads the OYO (1999) per-layer gradations transcribed from report Tables
   4-3-1 (embankment fill) and 4-3-2 (foundation),
   ``data/processed/oyo_1999_gradations_by_layer.csv``, and checks each row
   for internal consistency (monotone percentiles, Uc = d60/d10, the 2 mm
   point against the bracketing percentiles).
2. Reconstructs each specimen's cumulative grading from its tabulated points
   and derives matrix gradations under the pre-registered definitions:
   M2 (finer than 2 mm, primary), S2 (sand 0.075 to 2 mm), M4.75 (finer than
   4.75 mm). Reports matrix d70, d60, d10 and Cu per specimen, and the
   section medians over the aquifer (Ag) specimens.
3. Recomputes the ADR-0012 dependence diagnostic with the KP 58.8
   laboratory conductivities attached to the specimens sheet 4 attaches them
   to, and records that all six pairs are embankment fill.
4. With ``--consequence``: runs in-memory (``persist=False``) variants of the
   four historical matrix sweeps with the d70 prior mean replaced, on the
   production seed (common random numbers), and reports P_s, P_t, B and
   delta-beta at each section's design-level anchor. Production configs and
   ``results/`` are never written.

Physics is never reimplemented here: the consequence arm goes through
``run_fragility_analysis``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = REPO_ROOT / "data" / "processed" / "oyo_1999_gradations_by_layer.csv"
RECORD_JSON = REPO_ROOT / "docs" / "decisions" / "bimodal-foundation-d70-study.json"

SECTIONS = ("57.4", "58.8", "60.0", "62.0")

#: Production matrix d70 means (mm), from ``tokachi_bep_inputs.csv``.
ADOPTED_MATRIX_D70_MM = {"57.4": 0.70, "58.8": 0.53, "60.0": 0.26, "62.0": 0.70}
#: Production bulk co-primary d70 (mm), ``generate_configs.BULK_D70_MM``.
ADOPTED_BULK_D70_MM = {"57.4": 5.5, "58.8": 13.0, "60.0": 1.3, "62.0": 13.5}
#: The specimen each adopted matrix mean was extrapolated from (OYO test no.).
ADOPTED_MATRIX_SOURCE = {"57.4": "57.4", "58.8": "58.8", "60.0": "60.0"}
#: Pre-registered agreement band: one sigma_ln of the adopted prior (CoV 0.30).
SIGMA_LN_D70 = math.sqrt(math.log(1.0 + 0.30**2))
AGREEMENT_FACTOR = math.exp(SIGMA_LN_D70)

#: Design-level anchors (m T.P.) of the RQ1 record, nearest production grid
#: level used at N = 1e5 (KP 62.0's 46.39 m is not a grid level).
DESIGN_ANCHOR_M = {"57.4": 39.21, "58.8": 41.00, "60.0": 42.75, "62.0": 46.39}

CONFIGS = {
    kp: REPO_ROOT / "configs" / f"kp{kp.replace('.', '_')}_historical_matrix.yaml"
    for kp in SECTIONS
}


# --------------------------------------------------------------------------
# 1. Data
# --------------------------------------------------------------------------


def _num(value: str) -> float | None:
    value = value.strip()
    return float(value) if value else None


def load_specimens(path: Path = DATA_CSV) -> list[dict[str, Any]]:
    """Read the transcription; numeric fields become floats or None."""
    numeric = {
        "kp",
        "depth_top_m",
        "depth_bot_m",
        "rho_s_gcm3",
        "wn_pct",
        "gravel_pct",
        "sand_pct",
        "silt_pct",
        "clay_pct",
        "dmax_mm",
        "d60_mm",
        "d50_mm",
        "d30_mm",
        "d20_mm",
        "d10_mm",
        "uc",
        "ucc",
        "k_est_cms",
        "k_lab_cms",
    }
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, Any] = {}
            for key, value in raw.items():
                row[key] = _num(value) if key in numeric else value
            row["kp"] = f"{row['kp']:.1f}"
            rows.append(row)
    return rows


def consistency_flags(row: dict[str, Any]) -> list[str]:
    """Internal-consistency checks on one transcribed row."""
    flags = []
    total = sum(
        row[k] or 0.0 for k in ("gravel_pct", "sand_pct", "silt_pct", "clay_pct")
    )
    if abs(total - 100.0) > 0.25:
        flags.append(f"fractions sum to {total:.1f}")
    ds = [(p, row[f"d{p}_mm"]) for p in (10, 20, 30, 50, 60)]
    ds = [(p, d) for p, d in ds if d is not None]
    for (p1, d1), (p2, d2) in zip(ds, ds[1:], strict=False):
        if d2 < d1:
            flags.append(f"d{p2} {d2} below d{p1} {d1}")
    if row["d60_mm"] and row["d10_mm"] and row["uc"]:
        uc = row["d60_mm"] / row["d10_mm"]
        if abs(uc / row["uc"] - 1.0) > 0.05:
            flags.append(f"Uc printed {row['uc']} vs d60/d10 {uc:.1f}")
    p2 = 100.0 - row["gravel_pct"]
    for p, d in ds:
        if (d < 2.0 and p > p2 + 0.5) or (d > 2.0 and p < p2 - 0.5):
            flags.append(f"d{p} = {d} mm inconsistent with {p2:.1f} % passing 2 mm")
    return flags


# --------------------------------------------------------------------------
# 2. Grading reconstruction and matrix gradations
# --------------------------------------------------------------------------


def grading_points(row: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Cumulative (size mm, percent passing) points, monotone, sorted by size."""
    fines = (row["silt_pct"] or 0.0) + (row["clay_pct"] or 0.0)
    candidates = [
        (0.005, row["clay_pct"]),
        (0.075, fines),
        (row["d10_mm"], 10.0),
        (row["d20_mm"], 20.0),
        (row["d30_mm"], 30.0),
        (row["d50_mm"], 50.0),
        (row["d60_mm"], 60.0),
        (2.0, 100.0 - row["gravel_pct"]),
        (row["dmax_mm"], 100.0),
    ]
    pts = sorted(
        (d, p) for d, p in candidates if d is not None and p is not None and d > 0
    )
    kept: list[tuple[float, float]] = []
    dropped = []
    for d, p in pts:
        if kept and (p < kept[-1][1] - 1e-9 or d <= kept[-1][0]):
            # Keep the tabulated fraction points over a conflicting percentile.
            dropped.append(f"({d:g} mm, {p:g} %)")
            continue
        kept.append((d, p))
    sizes = np.array([d for d, _ in kept])
    passing = np.array([p for _, p in kept])
    return sizes, passing, dropped


def size_at(sizes: np.ndarray, passing: np.ndarray, target: float) -> float:
    """Size at a percent passing, linear in percent against log size."""
    if target <= passing[0]:
        return float(sizes[0])
    if target >= passing[-1]:
        return float(sizes[-1])
    idx = int(np.searchsorted(passing, target, side="left"))
    p0, p1 = passing[idx - 1], passing[idx]
    d0, d1 = sizes[idx - 1], sizes[idx]
    if p1 == p0:
        return float(d1)
    frac = (target - p0) / (p1 - p0)
    return float(math.exp(math.log(d0) + frac * (math.log(d1) - math.log(d0))))


def passing_at(sizes: np.ndarray, passing: np.ndarray, size: float) -> float:
    """Percent passing at a size, linear in percent against log size."""
    return float(np.interp(math.log(size), np.log(sizes), passing))


def matrix_gradation(row: dict[str, Any]) -> dict[str, Any]:
    """Matrix d70/d60/d10/Cu under the three pre-registered definitions."""
    sizes, passing, dropped = grading_points(row)
    fines = (row["silt_pct"] or 0.0) + (row["clay_pct"] or 0.0)
    out: dict[str, Any] = {"dropped_points": dropped}

    def summarise(lower_pct: float, upper_pct: float) -> dict[str, float | None]:
        span = upper_pct - lower_pct
        if span <= 1.0:
            return {"d70_mm": None, "d60_mm": None, "d10_mm": None, "cu": None}
        d = {
            q: size_at(sizes, passing, lower_pct + q / 100.0 * span)
            for q in (10, 60, 70)
        }
        return {
            "d70_mm": d[70],
            "d60_mm": d[60],
            "d10_mm": d[10],
            "cu": d[60] / d[10],
            "share_of_specimen_pct": span,
        }

    p2 = 100.0 - row["gravel_pct"]
    p475 = passing_at(sizes, passing, 4.75)
    out["passing_2mm_pct"] = p2
    out["passing_4p75mm_pct"] = p475
    out["M2"] = summarise(0.0, p2)
    out["S2"] = summarise(fines, p2)
    out["M4.75"] = summarise(0.0, p475)
    out["whole"] = summarise(0.0, 100.0)
    return out


def median(values: list[float]) -> float:
    return float(np.median(np.asarray(values, dtype=float)))


def geo_stats(values: list[float]) -> dict[str, float]:
    arr = np.log(np.asarray(values, dtype=float))
    sd = float(arr.std(ddof=1)) if arr.size > 1 else float("nan")
    return {
        "n": int(arr.size),
        "median_mm": float(np.exp(np.median(arr))),
        "geo_mean_mm": float(np.exp(arr.mean())),
        "min_mm": float(np.exp(arr.min())),
        "max_mm": float(np.exp(arr.max())),
        "sigma_ln": sd,
        "equivalent_cov": (
            float(math.sqrt(math.exp(sd**2) - 1.0)) if arr.size > 1 else None
        ),
        "arithmetic_mean_mm": float(np.mean(np.exp(arr))),
    }


def uppermost_ag(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The shallowest Ag specimen of each boring (the pipe-horizon subset)."""
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row["layer"] != "Ag":
            continue
        key = (row["kp"], row["borehole"])
        if key not in best or row["depth_top_m"] < best[key]["depth_top_m"]:
            best[key] = row
    return list(best.values())


def gradation_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    specimens = []
    for row in rows:
        mg = matrix_gradation(row)
        specimens.append(
            {
                "kp": row["kp"],
                "borehole": row["borehole"],
                "test_no": row["test_no"],
                "thesis_label": row["thesis_label"] or None,
                "depth_m": [row["depth_top_m"], row["depth_bot_m"]],
                "layer": row["layer"],
                "unit": row["unit"],
                "gravel_pct": row["gravel_pct"],
                "fines_pct": (row["silt_pct"] or 0.0) + (row["clay_pct"] or 0.0),
                "whole_d60_mm": row["d60_mm"],
                "whole_d10_mm": row["d10_mm"],
                "whole_uc_printed": row["uc"],
                "consistency_flags": consistency_flags(row),
                **mg,
            }
        )

    by_section: dict[str, Any] = {}
    top = {(r["kp"], r["test_no"]) for r in uppermost_ag(rows)}
    for kp in SECTIONS:
        ag = [s for s in specimens if s["kp"] == kp and s["layer"] == "Ag"]
        section: dict[str, Any] = {"n_ag": len(ag)}
        for definition in ("M2", "S2", "M4.75"):
            vals = [s[definition]["d70_mm"] for s in ag if s[definition]["d70_mm"]]
            section[definition] = geo_stats(vals)
            tops = [
                s[definition]["d70_mm"]
                for s in ag
                if (s["kp"], s["test_no"]) in top and s[definition]["d70_mm"]
            ]
            section[f"{definition}_uppermost_per_boring_mm"] = sorted(tops)
        section["M2_cu"] = geo_stats([s["M2"]["cu"] for s in ag])
        section["S2_cu"] = geo_stats([s["S2"]["cu"] for s in ag])
        section["whole_uc"] = geo_stats([s["whole_uc_printed"] for s in ag])
        section["whole_d60"] = geo_stats([s["whole_d60_mm"] for s in ag])
        adopted = ADOPTED_MATRIX_D70_MM[kp]
        derived = section["M2"]["median_mm"]
        ratio = adopted / derived
        if ratio > AGREEMENT_FACTOR:
            verdict = "adopted coarser than the aquifer matrix (non-conservative)"
        elif ratio < 1.0 / AGREEMENT_FACTOR:
            verdict = "adopted finer than the aquifer matrix (conservative)"
        else:
            verdict = "reproduced within one sigma_ln"
        section["adopted_matrix_d70_mm"] = adopted
        section["adopted_over_M2_median"] = ratio
        section["verdict_M2"] = verdict
        section["adopted_over_S2_median"] = adopted / section["S2"]["median_mm"]
        section["adopted_bulk_d70_mm"] = ADOPTED_BULK_D70_MM[kp]
        by_section[kp] = section

    ag_all = [s for s in specimens if s["layer"] == "Ag"]
    pooled = {
        d: geo_stats([s[d]["d70_mm"] for s in ag_all]) for d in ("M2", "S2", "M4.75")
    }
    ns_all = [s for s in specimens if s["layer"] == "Ns"]
    pooled_ns = geo_stats([s["M2"]["d70_mm"] for s in ns_all])
    fill_sources = {
        kp: next(s for s in specimens if s["kp"] == kp and s["test_no"] == test)
        for kp, test in ADOPTED_MATRIX_SOURCE.items()
    }
    return {
        "specimens": specimens,
        "by_section": by_section,
        "pooled_ag": pooled,
        "pooled_ns_M2": pooled_ns,
        "adopted_matrix_sources": {
            kp: {
                "test_no": s["test_no"],
                "thesis_label": s["thesis_label"],
                "layer": s["layer"],
                "unit": s["unit"],
                "whole_d60_mm": s["whole_d60_mm"],
                "whole_d70_mm": s["whole"]["d70_mm"],
                "fines_pct": s["fines_pct"],
                "gravel_pct": s["gravel_pct"],
            }
            for kp, s in fill_sources.items()
        },
    }


# --------------------------------------------------------------------------
# 3. ADR-0012 diagnostic with the sheet-4 pairing
# --------------------------------------------------------------------------


def _pearson(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    r = float(np.corrcoef(x, y)[0, 1])
    n = x.size
    slope = float(np.polyfit(x, y, 1)[0])
    t = r * math.sqrt((n - 2) / max(1e-300, 1.0 - r * r))
    from scipy.stats import t as student

    p = float(2.0 * student.sf(abs(t), n - 2))
    return {"r": r, "r2": r * r, "p": p, "slope": slope, "n": int(n)}


def dependence_diagnostic(rows: list[dict[str, Any]]) -> dict[str, Any]:
    in_scope = [r for r in rows if r["k_lab_cms"] is not None and r["kp"] in SECTIONS]
    k = np.log(np.array([r["k_lab_cms"] / 100.0 for r in in_scope]))
    d60 = np.log(np.array([r["d60_mm"] for r in in_scope]))
    d10 = np.log(np.array([r["d10_mm"] for r in in_scope]))
    pairs = [
        {
            "kp": r["kp"],
            "test_no": r["test_no"],
            "thesis_label": r["thesis_label"],
            "layer": r["layer"],
            "unit": r["unit"],
            "d60_mm": r["d60_mm"],
            "d10_mm": r["d10_mm"],
            "k_lab_mps": r["k_lab_cms"] / 100.0,
        }
        for r in in_scope
    ]
    # The ADR-0012 companion table as published (KP 58.8 shifted one specimen).
    published = [
        (1.47, 0.0057, 2.69e-5),
        (7.10, 0.0152, 9.16e-6),
        (11.10, 0.192, 2.84e-5),
        (0.228, 0.0053, 5.59e-4),
        (13.20, 0.530, 1.83e-4),
        (3.46, 0.016, 1.08e-5),
    ]
    pk = np.log(np.array([p[2] for p in published]))
    pd60 = np.log(np.array([p[0] for p in published]))
    pd10 = np.log(np.array([p[1] for p in published]))
    return {
        "pairs_sheet4": pairs,
        "all_pairs_are_fill": all(p["unit"] == "fill" for p in pairs),
        "sheet4_pairing": {
            "ln_k_vs_ln_d60": _pearson(d60, k),
            "ln_k_vs_ln_d10": _pearson(d10, k),
        },
        "published_pairing": {
            "ln_k_vs_ln_d60": _pearson(pd60, pk),
            "ln_k_vs_ln_d10": _pearson(pd10, pk),
        },
        "rule": "Hazen-consistent slope (within 2x of +2) and r2 >= 0.5 selects Nataf; "
        "r2 < 0.3 selects the two-soil model",
    }


# --------------------------------------------------------------------------
# 4. Consequence: in-memory variants of the historical matrix sweeps
# --------------------------------------------------------------------------


def _beta(p: float) -> float:
    return (
        float(-norm.ppf(p))
        if 0.0 < p < 1.0
        else float("inf") if p == 0.0 else float("-inf")
    )


def _run(kp: str, d70_mean_m: float | None, n_jobs: int):
    import yaml

    from bep_reliability_engine.config import Config
    from bep_reliability_engine.run import run_fragility_analysis

    data = yaml.safe_load(CONFIGS[kp].read_text(encoding="utf-8"))
    if d70_mean_m is not None:
        data["priors"]["d_70"]["mean"] = float(d70_mean_m)
    config = Config.model_validate(data)
    return run_fragility_analysis(config, n_jobs=n_jobs, progress=False, persist=False)


def _at_anchor(result, kp: str) -> dict[str, Any]:
    grid = np.asarray(result.conditioning_grid, dtype=float)
    i = int(np.argmin(np.abs(grid - DESIGN_ANCHOR_M[kp])))
    fs = np.asarray(result.failure_matrix_stat[:, i], dtype=bool)
    ft = np.asarray(result.failure_matrix_tran[:, i], dtype=bool)
    n = fs.size
    ps, pt = fs.sum() / n, ft.sum() / n
    return {
        "stage_m": float(grid[i]),
        "n": int(n),
        "static_failures": int(fs.sum()),
        "transient_failures": int(ft.sum()),
        "P_s": float(ps),
        "P_t": float(pt),
        "B": float(ps / pt) if pt > 0 else None,
        "delta_beta": _beta(pt) - _beta(ps) if 0 < pt and 0 < ps < 1 else None,
    }


def _assert_baseline_bit_identical(result, kp: str, results_dir: Path) -> bool:
    """Refuse to report a variant against a baseline that has drifted."""
    import h5py

    path = results_dir / f"tokachi_kp{kp}_historical_matrix.h5"
    if not path.exists():
        return False
    with h5py.File(path, "r") as handle:
        prod_static = np.asarray(handle["P_f_static_raw"])
        prod_trans = np.asarray(handle["P_f_trans_raw"])
    if not (
        np.array_equal(result.P_f_static_raw, prod_static)
        and np.array_equal(result.P_f_trans_raw, prod_trans)
    ):
        raise AssertionError(
            f"KP {kp}: baseline arm is not bit-identical to {path.name}"
        )
    return True


def consequence(
    arms: dict[str, dict[str, float]], n_jobs: int, results_dir: Path
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for kp in SECTIONS:
        t0 = time.time()
        base = _run(kp, None, n_jobs)
        rec: dict[str, Any] = {
            "config": str(CONFIGS[kp].relative_to(REPO_ROOT)).replace("\\", "/"),
            "baseline_bit_identical_to_production": _assert_baseline_bit_identical(
                base, kp, results_dir
            ),
            "baseline": _at_anchor(base, kp),
            "baseline_curve": {
                "stage_m": [float(x) for x in base.conditioning_grid],
                "P_s": [float(x) for x in base.P_f_static_raw],
                "P_t": [float(x) for x in base.P_f_trans_raw],
            },
            "arms": {},
        }
        for name, means in arms.items():
            if kp not in means:
                continue
            res = _run(kp, means[kp] * 1e-3, n_jobs)
            rec["arms"][name] = {
                "d70_mean_mm": means[kp],
                "anchor": _at_anchor(res, kp),
                "curve": {
                    "P_s": [float(x) for x in res.P_f_static_raw],
                    "P_t": [float(x) for x in res.P_f_trans_raw],
                },
            }
        rec["elapsed_s"] = round(time.time() - t0, 1)
        out[kp] = rec
        print(f"KP {kp} done in {rec['elapsed_s']} s", flush=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consequence", action="store_true")
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=REPO_ROOT / "results",
        help="where the persisted production sweeps live (read-only)",
    )
    args = parser.parse_args()

    rows = load_specimens()
    record: dict[str, Any] = {
        "study": "docs/decisions/bimodal-foundation-d70-study.md",
        "data": str(DATA_CSV.relative_to(REPO_ROOT)).replace("\\", "/"),
        "source": "OYO (1999) report Tables 4-3-1 (fill) and 4-3-2 (foundation), "
        "report pp. 52 to 53; sheet 4 per section; soil logs Figure 4-3-1",
        "agreement_factor": AGREEMENT_FACTOR,
        "gradations": gradation_analysis(rows),
        "dependence_diagnostic": dependence_diagnostic(rows),
    }
    if args.consequence:
        g = record["gradations"]["by_section"]
        arms = {
            "aquifer_M2_median": {
                kp: round(g[kp]["M2"]["median_mm"], 3) for kp in SECTIONS
            },
        }
        record["consequence"] = consequence(arms, args.n_jobs, args.results_dir)
    elif RECORD_JSON.exists():
        previous = json.loads(RECORD_JSON.read_text(encoding="utf-8"))
        if "consequence" in previous:
            record["consequence"] = previous["consequence"]
    RECORD_JSON.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {RECORD_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
