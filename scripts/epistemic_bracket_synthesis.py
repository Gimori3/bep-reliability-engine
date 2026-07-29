"""Cross-bracket epistemic synthesis: how big is each knob, and does it cancel?

Three companion studies now cover all four matrix cross-sections -- ADR-0045
(Sellmeijer model factor ``m_p``), ADR-0046 (surveyed exit datum ``z_toe``
+/- 0.3 m) and ADR-0048 (``k_aq`` / ``gamma_bl_sub`` prior-mean scenarios) --
and two further *epistemic* brackets live outside them: the ADR-0047
seepage-length measurement (adopted at KP 62.0, carried unadopted at the other
three) and the CoV(L) band of the seepage-length-L study. Against those sit the
two *statistical* uncertainties the reports already quote: the spec section 11
Monte Carlo CoV of the P_f estimator and the ADR-0024 Clopper-Pearson band.

Until now each lived in its own record with its own anchor levels, so "which
knob dominates" could not be read off anywhere. This driver puts all seven on
one footing and answers the one question the thesis actually leans on:

1. **Ranking table** -- the transient and static P_f multiplier each knob
   produces at four anchor levels (lowest reachable / shoulder / design HWL /
   grid top), per section, plus one comparable ``span`` factor per bracket.
2. **Cancellation test** -- ADR-0048's carried property (c): that a bracket
   which dominates the *absolute* probabilities largely cancels in the
   static-vs-transient *ratio*, which is what licenses the thesis's
   comparative claims. ADR-0047 section 4.5 showed the L bracket does **not**
   cancel, so cancellation is a property to be measured per knob, never
   assumed. Retested here per level with that same method: a paired bootstrap
   over the 16 joint pattern counts, 2000 replicates, null pinned at
   ``rho = 1.0`` exactly, ``resolved`` only when the interval excludes it.

Nothing here changes a production default. Every arm is a persisted, default-OFF
companion sweep (or an in-memory ``geometry.L`` override); the CSV and
``configs/`` are read-only; and each section's baseline is re-run fresh and
asserted **bit-identical to its persisted production sweep on the whole failure
matrices** before any number at that section is reported.

Usage (repo root, venv active)::

    python scripts/epistemic_bracket_synthesis.py            # all four sections
    python scripts/epistemic_bracket_synthesis.py --sections KP62.0
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import yaml
from numpy.typing import NDArray

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402


def _load_adr0047_module():
    """Import the ADR-0047 study module for its ratio-of-ratios kernel.

    The paired-bootstrap statistic is **reused, never re-implemented**: a second
    copy could drift from the one that produced the ADR-0047 numbers this note
    compares against. Same ``importlib`` route ``tests/test_dem_cross_section.py``
    already uses to reach that module.
    """
    path = REPO_ROOT / "scripts" / "dem_cross_section_study.py"
    spec = importlib.util.spec_from_file_location("dem_cross_section_study", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ADR0047 = _load_adr0047_module()
pattern_counts = _ADR0047._pattern_counts
ratio_of_ratios_ci = _ADR0047.ratio_of_ratios_ci
fragility_arms_from_measurements = _ADR0047.fragility_arms_from_measurements

#: Production matrix sections, in chainage order.
SECTIONS: dict[str, dict[str, str]] = {
    "KP57.4": {
        "config": "configs/kp57_4_historical_matrix.yaml",
        "production": "results/tokachi_kp57.4_historical_matrix.h5",
        "stem": "tokachi_kp57.4_historical_matrix",
    },
    "KP58.8": {
        "config": "configs/kp58_8_historical_matrix.yaml",
        "production": "results/tokachi_kp58.8_historical_matrix.h5",
        "stem": "tokachi_kp58.8_historical_matrix",
    },
    "KP60.0": {
        "config": "configs/kp60_0_historical_matrix.yaml",
        "production": "results/tokachi_kp60.0_historical_matrix.h5",
        "stem": "tokachi_kp60.0_historical_matrix",
    },
    "KP62.0": {
        "config": "configs/kp62_0_historical_matrix.yaml",
        "production": "results/tokachi_kp62.0_historical_matrix.h5",
        "stem": "tokachi_kp62.0_historical_matrix",
    },
}

#: Persisted companion arms: (arm label, bracket, results subdir, filename suffix).
#: Every one of these is a full production-N sweep already on disk, so the ratio
#: test over them costs nothing but the baseline gate.
PERSISTED_ARMS: list[tuple[str, str, str, str]] = [
    ("m_p", "m_p", "adr0045_mp", "_mp.h5"),
    ("z_toe_plus0.30m", "z_toe", "adr0046_ztoe", "_ztoe_plus0.30m.h5"),
    ("z_toe_minus0.30m", "z_toe", "adr0046_ztoe", "_ztoe_minus0.30m.h5"),
    ("k_aq_field_toe", "k_aq_prior_mean", "adr0048_prior_means", "_k_aq_field_toe.h5"),
    (
        "k_aq_field_geomean",
        "k_aq_prior_mean",
        "adr0048_prior_means",
        "_k_aq_field_geomean.h5",
    ),
    (
        "k_aq_regional_upper",
        "k_aq_prior_mean",
        "adr0048_prior_means",
        "_k_aq_regional_upper.h5",
    ),
    (
        "gamma_bl_sub_lower",
        "gamma_bl_sub_prior_mean",
        "adr0048_prior_means",
        "_gamma_bl_sub_lower.h5",
    ),
]

#: Ordering of the brackets in the ranking table, epistemic first.
BRACKET_ORDER = [
    "k_aq_prior_mean",
    "L_measurement",
    "cov_L",
    "m_p",
    "z_toe",
    "gamma_bl_sub_prior_mean",
    "mc_cov",
    "clopper_pearson",
]

ADR0047_EVIDENCE = REPO_ROOT / "docs" / "decisions" / "adr0047-dem-seepage-length.json"
COV_L_EVIDENCE = (
    REPO_ROOT
    / "results"
    / "sensitivity"
    / "seepage_length"
    / "marginal_sensitivity.json"
)
JSON_OUT = REPO_ROOT / "docs" / "decisions" / "epistemic-bracket-synthesis.json"

#: Normal quantile for the nominal 95% Monte Carlo band around P_f_hat.
Z95 = 1.959963984540054
#: Bootstrap replicates / confidence for the ratio-of-ratios, pinned to ADR-0047.
RATIO_BOOTSTRAP_N = _ADR0047.RATIO_BOOTSTRAP_N
RATIO_CONFIDENCE = _ADR0047.RATIO_CONFIDENCE
RATIO_MIN_FAILURES = _ADR0047.RATIO_MIN_FAILURES


# --------------------------------------------------------------------------- #
# Loading                                                                      #
# --------------------------------------------------------------------------- #
def load_sweep(path: Path) -> dict[str, Any]:
    """Read the arrays and diagnostics one sweep contributes, read-only."""
    with h5py.File(path, "r") as handle:
        payload = {
            "grid": np.asarray(handle["conditioning_grid"], dtype=float),
            "P_f_static_raw": np.asarray(handle["P_f_static_raw"], dtype=float),
            "P_f_trans_raw": np.asarray(handle["P_f_trans_raw"], dtype=float),
            "failure_matrix_static": np.asarray(handle["failure_matrix_static"]),
            "failure_matrix_trans": np.asarray(handle["failure_matrix_trans"]),
        }
        if "binomial_ci" in handle:
            payload["binomial_ci"] = {
                key: np.asarray(handle[f"binomial_ci/{key}"], dtype=float)
                for key in ("static_lo", "static_hi", "trans_lo", "trans_hi")
            }
    sidecar = path.with_suffix(".json")
    payload["metadata"] = (
        json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
    )
    return payload


def run_arm(config: Config, n_jobs: int) -> Any:
    """Run one in-memory sweep; nothing is written to ``results/``."""
    return run_fragility_analysis(config, n_jobs=n_jobs, progress=False, persist=False)


def gate_baseline(fresh: Any, persisted: dict[str, Any], label: str) -> None:
    """Refuse to report anything at a section whose baseline has drifted.

    Gates on the **whole failure matrices**, not the column means: a drift that
    happened to preserve P_f would still fail here.
    """
    for name, matrix in (
        ("static", fresh.failure_matrix_stat),
        ("trans", fresh.failure_matrix_tran),
    ):
        if not np.array_equal(matrix, persisted[f"failure_matrix_{name}"]):
            raise AssertionError(
                f"{label}: fresh {name} failure matrix differs from the persisted "
                "production sweep. Refusing to report a sensitivity against a "
                "drifted baseline."
            )


# --------------------------------------------------------------------------- #
# Anchors                                                                      #
# --------------------------------------------------------------------------- #
#: Transient P_f the "rising limb" anchor targets -- the low-probability shoulder
#: ADR-0045 quotes its m_p factors at (its text names P_f ~ 2e-3 explicitly).
RISING_LIMB_P_F = 2.0e-3
#: Transient P_f the "transition midpoint" anchor targets -- the level ADR-0048
#: quotes its k_aq factors at (verified: its KP58.8 field-toe "shoulder" ratio
#: x0.088 sits at 41.50 m MSL, where baseline P_f_trans = 0.4915).
TRANSITION_P_F = 0.5


def anchor_indices(
    grid: NDArray[np.float64], p_trans: NDArray[np.float64], hwl: float
) -> dict[str, int]:
    """The five conditioning levels the ranking table is quoted at.

    **The word "shoulder" is deliberately not used here.** ADR-0045 and ADR-0048
    both quote factors "at the shoulder" and mean *different stages*: ADR-0045's
    is the low-probability rising limb (its text says P_f ~ 2e-3), ADR-0048's is
    the transition midpoint (P_f ~ 0.5). Quoting the two side by side under one
    word would silently compare different levels, so this table names both and
    keeps them separate:

    ``lowest_reachable``
        Lowest level with any transient failure at all; below it every ratio is
        0/0 and says nothing.
    ``rising_limb``
        Nearest transient P_f = 2e-3 -- ADR-0045's "shoulder".
    ``transition_midpoint``
        Nearest transient P_f = 0.5 -- ADR-0048's "shoulder".
    ``design_hwl``
        Nearest the section's design high water, the stage the thesis defends
        its claims at.
    ``grid_top``
        Last level, where P_f saturates and every ratio is driven toward 1.
    """
    reachable = np.flatnonzero(p_trans > 0.0)
    return {
        "lowest_reachable": int(reachable[0]) if reachable.size else 0,
        "rising_limb": int(np.argmin(np.abs(p_trans - RISING_LIMB_P_F))),
        "transition_midpoint": int(np.argmin(np.abs(p_trans - TRANSITION_P_F))),
        "design_hwl": int(np.argmin(np.abs(grid - hwl))),
        "grid_top": int(grid.size - 1),
    }


def _ratio(numer: float, denom: float) -> float | None:
    return None if denom == 0.0 else float(numer / denom)


def _compact(obj: Any, sig: int = 6) -> Any:
    """Round every float in a nested payload to ``sig`` significant digits.

    Full float repr costs about 17 characters per number and buys nothing here:
    these are Monte Carlo estimates on 1e5 samples and bootstrap quantiles on
    2000 replicates, so six significant digits is already far beyond what the
    numbers mean. Keeps the evidence file inside the repo's 500 KB large-file
    hook without dropping any per-level content.
    """
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return obj
        return float(f"%.{sig}g" % obj)
    if isinstance(obj, dict):
        return {key: _compact(value, sig) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_compact(value, sig) for value in obj]
    return obj


def _span(values: list[float]) -> float | None:
    """Multiplicative width of a set of variants; None if the low end is zero."""
    lo, hi = min(values), max(values)
    return None if lo <= 0.0 else float(hi / lo)


# --------------------------------------------------------------------------- #
# Per-arm comparison + the ADR-0047 section 4.5 cancellation test              #
# --------------------------------------------------------------------------- #
def compare_arm(
    baseline: dict[str, Any],
    arm_static: NDArray[np.bool_],
    arm_trans: NDArray[np.bool_],
    arm_p_static: NDArray[np.float64],
    arm_p_trans: NDArray[np.float64],
    anchors: dict[str, int],
) -> dict[str, Any]:
    """Per-level P_f ratios plus the paired-bootstrap ratio-of-ratios.

    The two arms share the config seed, and an ADR-0048 scenario moves only a
    prior *mean* while leaving family, CoV, name and ordering untouched, so row
    j is the same LHS stratum in both arms. The comparison is therefore paired by
    common random numbers, which is exactly what makes the 16-cell joint
    contingency the sufficient statistic for the bootstrap.
    """
    base_static = baseline["P_f_static_raw"]
    base_trans = baseline["P_f_trans_raw"]
    grid = baseline["grid"]

    levels: list[dict[str, Any]] = []
    for index in range(grid.size):
        cells = (
            int(baseline["failure_matrix_static"][:, index].sum()),
            int(baseline["failure_matrix_trans"][:, index].sum()),
            int(arm_static[:, index].sum()),
            int(arm_trans[:, index].sum()),
        )
        # Per-level entries carry only what is NOT recomputable: the arm's own
        # P_f, the cell count and the bootstrap result. The stage and both
        # ratios follow from the section-level ``grid_m_msl`` and
        # ``P_f_*_baseline_curve``, which are stored once, so duplicating them
        # into every arm's every level would only cost the evidence file its
        # place under the repo's 500 KB large-file hook. The anchors below keep
        # the ratios explicitly, because that is where they are read.
        entry: dict[str, Any] = {
            "P_f_trans_arm": float(arm_p_trans[index]),
            "P_f_static_arm": float(arm_p_static[index]),
            "min_cell_failures": int(min(cells)),
        }
        if min(cells) >= RATIO_MIN_FAILURES:
            counts = pattern_counts(
                baseline["failure_matrix_static"][:, index],
                baseline["failure_matrix_trans"][:, index],
                arm_static[:, index],
                arm_trans[:, index],
            )
            entry.update(ratio_of_ratios_ci(counts, seed=index))
        levels.append(entry)

    evaluated = [lv for lv in levels if "rho" in lv]
    resolved = [lv for lv in evaluated if lv["resolved"]]
    departures = [abs(np.log(lv["rho"])) for lv in resolved if lv["rho"] > 0]
    return {
        "at_anchors": {
            name: {
                "stage_m_msl": float(grid[index]),
                "ratio_trans": _ratio(arm_p_trans[index], base_trans[index]),
                "ratio_static": _ratio(arm_p_static[index], base_static[index]),
                "P_f_trans_arm": levels[index]["P_f_trans_arm"],
                "P_f_static_arm": levels[index]["P_f_static_arm"],
                "rho": levels[index].get("rho"),
                "rho_lo": levels[index].get("rho_lo"),
                "rho_hi": levels[index].get("rho_hi"),
                "rho_resolved": levels[index].get("resolved"),
            }
            for name, index in anchors.items()
        },
        "n_levels_ratio_evaluated": len(evaluated),
        "n_levels_ratio_resolved": len(resolved),
        "max_resolved_departure_factor": float(
            np.exp(max(departures)) if departures else 1.0
        ),
        "rho_min": float(min((lv["rho"] for lv in evaluated), default=float("nan"))),
        "rho_max": float(max((lv["rho"] for lv in evaluated), default=float("nan"))),
        "levels": levels,
    }


def _arm_shift_size(arm: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    """How big was the input move, and how much ratio movement did it buy?

    **Needed to avoid a confound.** An ADR-0048 scenario is specified as an
    absolute *target* mean, so each section is shifted by a different factor
    (``k_aq`` 3.0e-3 / 2.0e-3 / 1.0e-3 all move to the same 5.15e-4). Raw
    departure factors therefore cannot be compared across sections: a section
    with a bigger input shift will show a bigger ratio movement for that reason
    alone. ``rho_decades_per_input_decade`` normalises the departure by the size
    of the input move, which is the comparable quantity.
    """
    factors = (
        (arm.get("metadata", {}).get("config") or {}).get("prior_mean_scenario") or {}
    ).get("factors") or {}
    if not factors:
        return {}
    parameter, factor = next(iter(factors.items()))
    departure = entry.get("max_resolved_departure_factor")
    input_decades = abs(np.log10(factor)) if factor > 0 else float("nan")
    normalised = (
        float(np.log10(departure) / input_decades)
        if departure and departure > 0 and input_decades > 0
        else None
    )
    return {
        "scenario_parameter": parameter,
        "scenario_factor": float(factor),
        "input_decades_moved": float(input_decades),
        "rho_decades_per_input_decade": normalised,
    }


# --------------------------------------------------------------------------- #
# The L bracket: in-memory geometry.L arms                                     #
# --------------------------------------------------------------------------- #
def seepage_length_arms(label: str, current_L: float) -> list[tuple[str, float]]:
    """The ADR-0047 L arms for one section, against its *current* config L.

    Reuses the accepted arm-selection rule, but feeds it the config's live
    ``geometry.L`` rather than the ``csv_L_m`` recorded in the evidence file --
    which at KP 62.0 still names the withdrawn 47 m, so the unpatched record
    would ask for a no-op 40 m arm alongside the withdrawn one.
    """
    if not ADR0047_EVIDENCE.exists():
        return []
    payload = json.loads(ADR0047_EVIDENCE.read_text(encoding="utf-8"))
    for record in payload.get("measurements", []):
        if record["section"] == label:
            patched = dict(record, csv_L_m=current_L)
            return fragility_arms_from_measurements([patched])[label]
    return []


# --------------------------------------------------------------------------- #
# The CoV(L) bracket: curves only, from the seepage-length-L study             #
# --------------------------------------------------------------------------- #
def cov_L_bracket(
    label: str, grid: NDArray[np.float64], anchors: dict[str, int]
) -> dict[str, Any] | None:
    """CoV(L) 0.10 vs 0.40 against the production CoV, from the L study record.

    Curves only (that study ran N = 30000 and kept no failure matrices), so this
    bracket contributes to the ranking table but cannot be put through the
    cancellation test.
    """
    if not COV_L_EVIDENCE.exists():
        return None
    payload = json.loads(COV_L_EVIDENCE.read_text(encoding="utf-8"))
    section = payload["sections"].get(label)
    if section is None:
        return None
    study_grid = np.asarray(section["grid_m_msl"], dtype=float)
    if study_grid.shape != grid.shape or not np.allclose(study_grid, grid):
        return {"available": False, "reason": "study grid differs from production grid"}

    production_cov = "cov0.15" if label == "KP60.0" else "cov0.20"
    curves = section["curves"]
    base = np.asarray(curves[production_cov]["transient"], dtype=float)
    base_static = np.asarray(curves[production_cov]["static"], dtype=float)
    arms = {}
    for key in ("cov0.10", "cov0.40", "det"):
        if key not in curves:
            continue
        trans = np.asarray(curves[key]["transient"], dtype=float)
        static = np.asarray(curves[key]["static"], dtype=float)
        arms[key] = {
            name: {
                "stage_m_msl": float(grid[index]),
                "ratio_trans": _ratio(trans[index], base[index]),
                "ratio_static": _ratio(static[index], base_static[index]),
            }
            for name, index in anchors.items()
        }
    return {
        "available": True,
        "n_samples": int(payload["n_samples"]),
        "production_cov": production_cov,
        "note": (
            "Curves from the seepage-length-L study at N=30000, not the "
            "production N=1e5; no failure matrices, so no cancellation test."
        ),
        "arms": arms,
        "span_trans": {
            name: _span(
                [
                    float(np.asarray(curves[key]["transient"], float)[index])
                    for key in ("cov0.10", "cov0.40")
                    if key in curves
                ]
                + [float(base[index])]
            )
            for name, index in anchors.items()
        },
    }


# --------------------------------------------------------------------------- #
# Statistical rows                                                             #
# --------------------------------------------------------------------------- #
def statistical_rows(
    baseline: dict[str, Any], anchors: dict[str, int]
) -> dict[str, Any]:
    """The spec section 11 MC CoV band and the ADR-0024 Clopper-Pearson band.

    Both are expressed as a multiplicative ``span`` so they sit on the same axis
    as the epistemic brackets. The MC band is the nominal normal one,
    ``P_f_hat * (1 +/- 1.96 CoV)``; where that lower end is non-positive (deep
    tail, few failures) the span is reported as ``None`` and the
    Clopper-Pearson interval is the honest statement, exactly as ADR-0024 says.
    """
    mc = baseline["metadata"].get("mc_convergence", {})
    cov_trans = np.asarray(mc.get("cov_pf_trans", []), dtype=float)
    cov_static = np.asarray(mc.get("cov_pf_static", []), dtype=float)
    ci = baseline.get("binomial_ci")

    out: dict[str, Any] = {"mc_cov": {}, "clopper_pearson": {}}
    for name, index in anchors.items():
        point = float(baseline["P_f_trans_raw"][index])
        if cov_trans.size > index:
            cov = float(cov_trans[index])
            lo, hi = point * (1.0 - Z95 * cov), point * (1.0 + Z95 * cov)
            out["mc_cov"][name] = {
                "stage_m_msl": float(baseline["grid"][index]),
                "cov_trans": cov,
                "cov_static": (
                    float(cov_static[index]) if cov_static.size > index else None
                ),
                "P_f_trans": point,
                "band_lo": lo,
                "band_hi": hi,
                "span_trans": _span([lo, hi]) if lo > 0.0 else None,
            }
        if ci is not None:
            lo, hi = float(ci["trans_lo"][index]), float(ci["trans_hi"][index])
            out["clopper_pearson"][name] = {
                "stage_m_msl": float(baseline["grid"][index]),
                "P_f_trans": point,
                "ci_lo": lo,
                "ci_hi": hi,
                "span_trans": _span([lo, hi]) if lo > 0.0 else None,
            }
    return out


# --------------------------------------------------------------------------- #
# Per-section driver                                                           #
# --------------------------------------------------------------------------- #
def study_section(label: str, n_jobs: int, *, verbose: bool = True) -> dict[str, Any]:
    """Every bracket at one section, gated on a bit-identical baseline."""
    spec = SECTIONS[label]
    config_path = REPO_ROOT / spec["config"]
    production_path = REPO_ROOT / spec["production"]
    config = Config.from_yaml(config_path)
    baseline = load_sweep(production_path)

    started = time.time()
    if verbose:
        print(f"[{label}] baseline gate (fresh sweep vs persisted) ...", flush=True)
    fresh = run_arm(config, n_jobs)
    gate_baseline(fresh, baseline, label)

    grid = baseline["grid"]
    hwl = float(config.geometry.HWL)
    anchors = anchor_indices(grid, baseline["P_f_trans_raw"], hwl)

    record: dict[str, Any] = {
        "section": label,
        "config": spec["config"],
        "production_sweep": spec["production"],
        "config_hash": baseline["metadata"].get("config_hash"),
        "config_hash_matches_yaml": config.config_hash()
        == baseline["metadata"].get("config_hash"),
        "baseline_failure_matrices_bit_identical_to_production": True,
        "n_samples": int(fresh.theta_matrix.shape[0]),
        "L_m": float(config.geometry.L),
        "seepage_length_cov": config.seepage_length_cov,
        "z_toe_m_msl": float(config.geometry.z_toe),
        "hwl_m_msl": hwl,
        "anchors": {
            name: {
                "index": index,
                "stage_m_msl": float(grid[index]),
                "P_f_trans_baseline": float(baseline["P_f_trans_raw"][index]),
                "P_f_static_baseline": float(baseline["P_f_static_raw"][index]),
                # Carried explicitly: an anchor with zero baseline transient
                # failures makes every multiplier there undefined, and that is a
                # finding about the section, not a gap in the table.
                "n_failures_trans_baseline": int(
                    baseline["failure_matrix_trans"][:, index].sum()
                ),
                "n_failures_static_baseline": int(
                    baseline["failure_matrix_static"][:, index].sum()
                ),
            }
            for name, index in anchors.items()
        },
        "bootstrap": {"n": RATIO_BOOTSTRAP_N, "confidence": RATIO_CONFIDENCE},
        # Recorded once here, not per arm per level (see ``compare_arm``).
        "grid_m_msl": grid.tolist(),
        "P_f_trans_baseline_curve": baseline["P_f_trans_raw"].tolist(),
        "P_f_static_baseline_curve": baseline["P_f_static_raw"].tolist(),
        "arms": {},
    }

    # --- persisted companion arms (free: matrices already on disk) ----------
    for arm_label, bracket, subdir, suffix in PERSISTED_ARMS:
        path = (
            REPO_ROOT / "results" / "sensitivity" / subdir / f"{spec['stem']}{suffix}"
        )
        if not path.exists():
            record["arms"][arm_label] = {
                "bracket": bracket,
                "available": False,
                "reason": f"companion sweep absent: {path.name}",
            }
            continue
        arm = load_sweep(path)
        if arm["grid"].shape != grid.shape or not np.allclose(arm["grid"], grid):
            record["arms"][arm_label] = {
                "bracket": bracket,
                "available": False,
                "reason": "companion grid differs from the production grid",
            }
            continue
        entry = compare_arm(
            baseline,
            arm["failure_matrix_static"],
            arm["failure_matrix_trans"],
            arm["P_f_static_raw"],
            arm["P_f_trans_raw"],
            anchors,
        )
        entry.update(
            {
                "bracket": bracket,
                "available": True,
                "source": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            }
        )
        entry.update(_arm_shift_size(arm, entry))
        record["arms"][arm_label] = entry
        if verbose:
            _report(label, arm_label, entry)

    # --- the L bracket: in-memory geometry.L overrides ----------------------
    for arm_label, length in seepage_length_arms(label, float(config.geometry.L)):
        if verbose:
            print(f"[{label}] L arm {arm_label} = {length:g} m ...", flush=True)
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        data["geometry"]["L"] = float(length)
        arm = run_arm(Config.model_validate(data), n_jobs)
        entry = compare_arm(
            baseline,
            arm.failure_matrix_stat,
            arm.failure_matrix_tran,
            arm.P_f_static_raw,
            arm.P_f_trans_raw,
            anchors,
        )
        entry.update(
            {
                "bracket": "L_measurement",
                "available": True,
                "source": "in-memory geometry.L override (configs/ read-only)",
                "L_m": float(length),
                "delta_L_m": float(length) - float(config.geometry.L),
            }
        )
        record["arms"][f"L_{arm_label}"] = entry
        if verbose:
            _report(label, f"L_{arm_label}", entry)

    record["cov_L"] = cov_L_bracket(label, grid, anchors)
    record["statistical"] = statistical_rows(baseline, anchors)
    record["brackets"] = summarise_brackets(record, anchors)
    record["elapsed_s"] = round(time.time() - started, 1)
    return record


def _report(section: str, arm: str, entry: dict[str, Any]) -> None:
    hwl = entry["at_anchors"]["design_hwl"]
    ratio = hwl["ratio_trans"]
    rho = hwl["rho"]
    print(
        f"    {section} {arm:24s} HWL x{'-' if ratio is None else f'{ratio:.3g}'}"
        f"  rho {'-' if rho is None else f'{rho:.3f}'}"
        f" ({'resolved' if hwl.get('rho_resolved') else 'unresolved'});"
        f" {entry['n_levels_ratio_resolved']}/{entry['n_levels_ratio_evaluated']}"
        f" levels resolved",
        flush=True,
    )


def summarise_brackets(
    record: dict[str, Any], anchors: dict[str, int]
) -> dict[str, Any]:
    """Collapse the arms into one comparable ``span`` per bracket per anchor.

    ``span`` is the multiplicative width the knob spans at that level -- the
    largest transient P_f any of its arms produces divided by the smallest,
    baseline included. One number, same units for an epistemic bracket and for
    a statistical band, which is what makes the ranking readable.
    """
    out: dict[str, Any] = {}
    by_bracket: dict[str, list[str]] = {}
    for arm_label, entry in record["arms"].items():
        if entry.get("available"):
            by_bracket.setdefault(entry["bracket"], []).append(arm_label)

    for bracket, arm_labels in by_bracket.items():
        spans = {}
        for name in anchors:
            base = record["anchors"][name]["P_f_trans_baseline"]
            values = [base] + [
                record["arms"][a]["at_anchors"][name]["P_f_trans_arm"]
                for a in arm_labels
            ]
            spans[name] = {
                "span_trans": _span(values),
                "ratio_min": _ratio(min(values), base),
                "ratio_max": _ratio(max(values), base),
                "P_f_trans_baseline": base,
            }
        cancels = [
            record["arms"][a]["n_levels_ratio_resolved"]
            / max(record["arms"][a]["n_levels_ratio_evaluated"], 1)
            for a in arm_labels
        ]
        out[bracket] = {
            "arms": sorted(arm_labels),
            "span": spans,
            "fraction_of_levels_where_ratio_moved": (
                float(max(cancels)) if cancels else None
            ),
        }

    if record.get("cov_L") and record["cov_L"].get("available"):
        out["cov_L"] = {
            "arms": sorted(record["cov_L"]["arms"]),
            "span": {
                name: {"span_trans": value}
                for name, value in record["cov_L"]["span_trans"].items()
            },
            "fraction_of_levels_where_ratio_moved": None,
            "note": record["cov_L"]["note"],
        }
    for key in ("mc_cov", "clopper_pearson"):
        block = record["statistical"].get(key, {})
        if block:
            out[key] = {
                "arms": [key],
                "span": {
                    name: {"span_trans": value.get("span_trans")}
                    for name, value in block.items()
                },
                "fraction_of_levels_where_ratio_moved": None,
            }
    return out


# --------------------------------------------------------------------------- #
# Printing                                                                     #
# --------------------------------------------------------------------------- #
def print_table(records: list[dict[str, Any]]) -> None:
    anchors = (
        "lowest_reachable",
        "rising_limb",
        "transition_midpoint",
        "design_hwl",
        "grid_top",
    )
    for record in records:
        print(f"\n=== {record['section']} (transient P_f span factor) ===")
        header = f"  {'bracket':26s}" + "".join(f"{a:>18s}" for a in anchors)
        print(header)
        print("  " + "-" * (len(header) - 2))
        for bracket in BRACKET_ORDER:
            block = record["brackets"].get(bracket)
            if block is None:
                continue
            cells = []
            for name in anchors:
                span = block["span"].get(name, {}).get("span_trans")
                cells.append("        unbounded" if span is None else f"{span:18.3g}")
            print(f"  {bracket:26s}" + "".join(cells))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sections", nargs="+", default=list(SECTIONS), choices=SECTIONS
    )
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--out", type=Path, default=JSON_OUT)
    args = parser.parse_args(argv)

    records = [study_section(label, args.n_jobs) for label in args.sections]
    payload = {
        "study": "Cross-bracket epistemic synthesis (ADR-0045/0046/0047/0048)",
        "generated_by": "scripts/epistemic_bracket_synthesis.py",
        "note": (
            "Ranking of every quantified epistemic bracket against the two "
            "statistical uncertainties, on one set of anchor levels, plus the "
            "ADR-0047 section 4.5 paired-bootstrap ratio-of-ratios cancellation "
            "test per arm. No production default is touched; every section's "
            "baseline is asserted bit-identical to its persisted production "
            "sweep on the whole failure matrices before any number is reported."
        ),
        "bootstrap": {"n": RATIO_BOOTSTRAP_N, "confidence": RATIO_CONFIDENCE},
        "sections": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8"
    )
    print_table(records)
    print(f"\nwrote {args.out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
