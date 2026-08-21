"""ADR-0049 companion: the critical-pipe-length bracket, and whether it cancels.

The static-transient gap decomposition (ADR-0040) isolated the H_eq-conservatism
component by relaxing the *end* anchor of Pol SIE 2024 Eq. (11) through the
ADR-0041 opt-in override. The **other** anchor of that same equilibrium curve --
the critical pipe length l_c of Eq. (13), which fixes where H_eq attains its
maximum H_c and therefore where a pipe stops stalling and starts running away --
had no override and no measurement. This driver closes that.

What it does, per matrix section:

1. **Baseline gate.** Re-runs the section's committed YAML with
   ``critical_length_factor=None`` set *explicitly* and asserts the two failure
   matrices are bit-identical to the persisted production sweep. That single run
   discharges two obligations at once: the knob is inert when off, and the
   baseline this study compares against has not drifted.
2. **Two arms.** Re-runs the same config at ``l_c x LOWER`` and ``l_c x UPPER``.
   Same seed, same theta, same L draw, same grid, same hydrographs: the arms are
   coupled to the baseline by common random numbers row for row, which is what
   makes the paired bootstrap of step 4 exact.
3. **Per-level effect** on the transient conditional failure probability, and on
   the static one (which must not move at all -- see below).
4. **The cancellation test**, with the ADR-0047 section 4.5 paired-bootstrap
   ratio-of-ratios statistic, imported rather than re-implemented::

       rho = (P_static / P_transient)_arm  /  (P_static / P_transient)_baseline

   null pinned at rho = 1.0 exactly, 2000 replicates over the 16 joint pattern
   counts, a level counted ``resolved`` only when the 95 per cent interval
   excludes unity.

The channel reading, made BEFORE the numbers (the epistemic-bracket-synthesis
rule: predict cancellation only where every channel is shared):

    | channel                          | where            | branches        |
    |----------------------------------|------------------|-----------------|
    | the (l_c, H_c) breakpoint of the | progression.py   | transient only  |
    | piecewise-linear H_eq(l)         | equilibrium_head |                 |

That is the whole list. l_c does not enter H_c (Eq. (12) has no l_c), does not
enter r_e or the leakage lengths, and is not read by the static comparator. The
knob therefore has **zero common-mode channels**. It is not the first such
input in the register: the blanket unit weight already touches the transient
branch alone. It is the larger of the two in the comparison, and the one that
is not inert at the governing section. Prediction: the bracket cannot cancel in
the static-to-transient ratio; and because the static branch is not merely
*nearly* invariant but *exactly* so, the displacement of the ratio must equal
the reciprocal of the displacement of the transient probability, level by
level, to machine precision.
Step 4 measures that instead of asserting it, and the driver refuses to report
if the static branch moves anywhere.

The bracket range, from the repository's own reference material
(``docs/decisions/m7-pol-ode-reference-values.md`` section 2), NOT invented here:

* Eq. (13) states its own basis as agreement with **2D** numerical piping
  simulations (Pol SIE 2024 section 2.3).
* The one **3D** hole-exit critical length published alongside it, for the
  in-domain S2-2 case (L = 3 m, D = L/3), is l = 1.36 m (Pol 2022 thesis,
  Fig. 5.9 caption), against Eq. (13)'s 0.874 m at that geometry: a factor
  1.556.
* No evidence places the truth *below* Eq. (13), so the lower arm is the
  reciprocal of the measured upper deviation, 0.643. The bracket is therefore
  one measured arm and one mirrored counterfactual, and the note says so.
* Corroborating but deliberately NOT used to widen the range: the B25-245
  small-scale box measured l_c = 0.197 m against Eq. (13)'s 0.0905 m, a factor
  2.18 -- also above. That case is out of the fitted domain and is a qualitative
  gate only (ADR-0009 / m7 note section 5D), so it is reported as a direction
  check, not as a bracket edge.

Usage (from the repo root, venv active)::

    python scripts/critical_length_bracket_study.py                 # all four
    python scripts/critical_length_bracket_study.py --sections KP62.0
    python scripts/critical_length_bracket_study.py --skip-run      # re-analyse
    python scripts/critical_length_bracket_study.py --n 2000 --allow-unverified

``--n`` pilots at a reduced sample size; it can never be bit-identical, so it
requires ``--allow-unverified`` and refuses to write the evidence record.
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
from numpy.typing import NDArray

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402
from bep_reliability_engine.sellmeijer import (  # noqa: E402
    compute_critical_pipe_length,
)


def _load_adr0047_module():
    """Import the ADR-0047 study module for its ratio-of-ratios kernel.

    The paired-bootstrap statistic is **reused, never re-implemented**: a second
    copy could drift from the one that produced the ADR-0047 and
    epistemic-bracket-synthesis numbers this study sits beside. Same
    ``importlib`` route those two already use.
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

# --------------------------------------------------------------------------- #
# The bracket                                                                  #
# --------------------------------------------------------------------------- #
#: The in-domain S2-2 DgFlow case the anchor is read from (Pol 2022 thesis,
#: Fig. 5.9 caption; m7-pol-ode-reference-values.md section 2).
S2_2_SEEPAGE_LENGTH_M = 3.0
S2_2_AQUIFER_DEPTH_M = S2_2_SEEPAGE_LENGTH_M / 3.0
S2_2_DGFLOW_CRITICAL_LENGTH_M = 1.36

#: Upper arm: the DgFlow 3D hole-exit critical length divided by what Eq. (13)
#: gives at the same geometry. Derived here rather than pasted, so the
#: provenance of the number is the two published values above.
_EQ13_S2_2 = float(
    compute_critical_pipe_length(S2_2_AQUIFER_DEPTH_M, S2_2_SEEPAGE_LENGTH_M)
)
CRITICAL_LENGTH_FACTOR_UPPER = S2_2_DGFLOW_CRITICAL_LENGTH_M / _EQ13_S2_2
#: Lower arm: the mirrored counterfactual. No published case places the true
#: critical length below Eq. (13); this arm exists so the bracket is two-sided.
CRITICAL_LENGTH_FACTOR_LOWER = 1.0 / CRITICAL_LENGTH_FACTOR_UPPER

#: Direction check only (out of the fitted domain; qualitative gate).
B25_245_SEEPAGE_LENGTH_M = 0.352
B25_245_AQUIFER_DEPTH_M = 0.1
B25_245_MEASURED_CRITICAL_LENGTH_M = 0.197
_EQ13_B25_245 = float(
    compute_critical_pipe_length(B25_245_AQUIFER_DEPTH_M, B25_245_SEEPAGE_LENGTH_M)
)

ARMS: list[tuple[str, float]] = [
    ("l_c_lower", CRITICAL_LENGTH_FACTOR_LOWER),
    ("l_c_upper", CRITICAL_LENGTH_FACTOR_UPPER),
]

#: Production matrix sections, in chainage order (the set the epistemic
#: brackets and the thesis's conditional claims are quoted at).
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

OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0049_critical_length"
JSON_OUT = REPO_ROOT / "docs" / "decisions" / "adr0049-critical-length-companion.json"

#: Transient P_f the "rising limb" anchor targets (ADR-0045's shoulder).
RISING_LIMB_P_F = 2.0e-3
#: Transient P_f the "transition midpoint" anchor targets (ADR-0048's shoulder).
TRANSITION_P_F = 0.5
#: Minimum failure count in every one of the four cells before a level's ratio
#: is reported at all (the ADR-0047 convention, deliberately low).
RATIO_MIN_FAILURES = 10


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _load_persisted(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        return {
            "grid": np.asarray(handle["conditioning_grid"], dtype=float),
            "P_f_static_raw": np.asarray(handle["P_f_static_raw"], dtype=float),
            "P_f_trans_raw": np.asarray(handle["P_f_trans_raw"], dtype=float),
            "failure_matrix_static": np.asarray(handle["failure_matrix_static"]),
            "failure_matrix_trans": np.asarray(handle["failure_matrix_trans"]),
        }


def _assert_bit_identical(label: str, fresh: FragilityResult, persisted: dict) -> None:
    """Gate on the WHOLE failure matrices, not the column means.

    A drift that happened to preserve P_f would still fail here.
    """
    for name, matrix in (
        ("static", fresh.failure_matrix_stat),
        ("trans", fresh.failure_matrix_tran),
    ):
        if not np.array_equal(matrix, persisted[f"failure_matrix_{name}"]):
            raise AssertionError(
                f"{label}: fresh {name} failure matrix differs from the persisted "
                "production sweep. Either critical_length_factor=None is not "
                "bit-identical, or the baseline has drifted. Refusing to report "
                "a sensitivity either way."
            )


def anchor_indices(
    grid: NDArray[np.float64], p_trans: NDArray[np.float64], hwl: float
) -> dict[str, int]:
    """The five conditioning levels the tables are quoted at.

    Identical definitions to ``scripts/epistemic_bracket_synthesis.py``, so this
    bracket can be read straight into that ranking table. The word "shoulder" is
    deliberately avoided: ADR-0045 and ADR-0048 both use it and mean different
    stages, which is why ``rising_limb`` and ``transition_midpoint`` are named
    separately here.
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

    These are Monte Carlo estimates on 1e5 samples and bootstrap quantiles on
    2000 replicates; six significant digits is already far beyond what they
    mean, and it keeps the evidence file inside the repo's 500 KB hook.
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
    """Multiplicative width of a set of arms; None when the low end is zero."""
    lo, hi = min(values), max(values)
    return None if lo <= 0.0 else float(hi / lo)


# --------------------------------------------------------------------------- #
# Per-arm comparison and the cancellation test                                 #
# --------------------------------------------------------------------------- #
def compare_arm(
    baseline: dict[str, Any],
    arm: FragilityResult,
    *,
    seed: int,
) -> dict[str, Any]:
    """Per-level effect of one arm, plus the ratio-of-ratios interval."""
    base_static = baseline["failure_matrix_static"].astype(bool)
    base_trans = baseline["failure_matrix_trans"].astype(bool)
    arm_static = np.asarray(arm.failure_matrix_stat, dtype=bool)
    arm_trans = np.asarray(arm.failure_matrix_tran, dtype=bool)

    p_static = np.asarray(arm.P_f_static_raw, dtype=float)
    p_trans = np.asarray(arm.P_f_trans_raw, dtype=float)
    b_static = baseline["P_f_static_raw"]
    b_trans = baseline["P_f_trans_raw"]

    # The structural claim, enforced rather than assumed: l_c reaches only the
    # M7 equilibrium curve, so the static column must not move ANYWHERE.
    if not np.array_equal(base_static, arm_static):
        moved = int(np.count_nonzero(base_static != arm_static))
        raise AssertionError(
            f"the static failure matrix moved in {moved} cells under an l_c "
            "arm. l_c must not reach the static comparator; a non-zero count "
            "means a channel exists that this study's reasoning does not know "
            "about. Refusing to report."
        )

    levels = []
    for index in range(p_trans.size):
        counts = pattern_counts(
            base_static[:, index],
            base_trans[:, index],
            arm_static[:, index],
            arm_trans[:, index],
        )
        cell_min = min(
            int(base_static[:, index].sum()),
            int(base_trans[:, index].sum()),
            int(arm_static[:, index].sum()),
            int(arm_trans[:, index].sum()),
        )
        # ADR-0030 discreteness diagnostic. A row that fails transiently but
        # not statically is impossible in continuous time under the shared
        # sample: the transient branch needs the same critical head the static
        # one compares against, plus time. Any such row is a forward-Euler
        # barrier jump. A SHORTER l_c puts the barrier fewer metres from the
        # start, so one step can clear it more easily; the lower arm is where
        # the artifact would appear first, and it must be checked rather than
        # assumed absent.
        trans_not_static_arm = int(
            np.count_nonzero(arm_trans[:, index] & ~arm_static[:, index])
        )
        trans_not_static_base = int(
            np.count_nonzero(base_trans[:, index] & ~base_static[:, index])
        )
        entry: dict[str, Any] = {
            "stage_m_msl": float(baseline["grid"][index]),
            "trans_not_static_baseline": trans_not_static_base,
            "trans_not_static_arm": trans_not_static_arm,
            "p_f_static_baseline": float(b_static[index]),
            "p_f_static_arm": float(p_static[index]),
            "p_f_trans_baseline": float(b_trans[index]),
            "p_f_trans_arm": float(p_trans[index]),
            "ratio_static": _ratio(float(p_static[index]), float(b_static[index])),
            "ratio_trans": _ratio(float(p_trans[index]), float(b_trans[index])),
            "min_cell_failures": cell_min,
        }
        if cell_min >= RATIO_MIN_FAILURES:
            entry["rho"] = ratio_of_ratios_ci(counts, seed=seed + index)
        else:
            entry["rho"] = None
        levels.append(entry)
    return {"levels": levels}


def run_section(
    label: str,
    spec: dict[str, str],
    *,
    n_jobs: int,
    n_override: int | None,
    skip_run: bool,
    allow_unverified: bool,
) -> dict[str, Any]:
    """Gate the baseline, run both arms, and assemble the section record."""
    started = time.time()
    config = Config.from_yaml(REPO_ROOT / spec["config"])
    if config.critical_length_factor is not None:
        raise ValueError(
            f"{label}: the committed config already carries a "
            "critical_length_factor; this driver expects the production "
            "baseline, where the knob is off."
        )
    if n_override is not None:
        config = config.model_copy(
            update={"mc": config.mc.model_copy(update={"n_samples": n_override})}
        )

    production = _load_persisted(REPO_ROOT / spec["production"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. the gate: knob explicitly off, bit-identical to production -------
    gate_path = OUT_DIR / f"{spec['stem']}_gate.h5"
    if not skip_run:
        print(f"[{label}] gate: baseline with the knob explicitly off ...", flush=True)
        gate = run_fragility_analysis(
            config.model_copy(update={"critical_length_factor": None}),
            n_jobs=n_jobs,
            progress=True,
            output_path=gate_path,
            overwrite=True,
        )
    else:
        gate = FragilityResult.load(gate_path)
    if allow_unverified:
        try:
            _assert_bit_identical(f"{label} gate", gate, production)
            gate_status = "bit_identical"
        except (AssertionError, ValueError) as exc:
            gate_status = f"UNVERIFIED: {exc}"
            print(f"[{label}] {gate_status}", flush=True)
    else:
        _assert_bit_identical(f"{label} gate", gate, production)
        gate_status = "bit_identical"

    # Everything downstream compares against the FRESH gate run rather than the
    # persisted file. In production the gate has just proved the two are
    # bit-identical, so this is the same comparison; under a reduced-N pilot it
    # is the only one that is even shaped correctly.
    baseline = {
        "grid": np.asarray(gate.conditioning_grid, dtype=float),
        "P_f_static_raw": np.asarray(gate.P_f_static_raw, dtype=float),
        "P_f_trans_raw": np.asarray(gate.P_f_trans_raw, dtype=float),
        "failure_matrix_static": np.asarray(gate.failure_matrix_stat),
        "failure_matrix_trans": np.asarray(gate.failure_matrix_tran),
    }

    # --- 2. the two arms ------------------------------------------------------
    arms: dict[str, Any] = {}
    for arm_label, factor in ARMS:
        arm_path = OUT_DIR / f"{spec['stem']}_{arm_label}.h5"
        if not skip_run:
            print(f"[{label}] arm {arm_label}: l_c x {factor:.4f} ...", flush=True)
            arm = run_fragility_analysis(
                config.model_copy(update={"critical_length_factor": factor}),
                n_jobs=n_jobs,
                progress=True,
                output_path=arm_path,
                overwrite=True,
            )
        else:
            arm = FragilityResult.load(arm_path)
        if not np.array_equal(
            np.asarray(arm.conditioning_grid, dtype=float), baseline["grid"]
        ):
            raise RuntimeError(f"{label}/{arm_label}: arm grid differs from baseline")
        arms[arm_label] = {
            "factor": float(factor),
            "file": str(arm_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            **compare_arm(baseline, arm, seed=hash((label, arm_label)) % 100000),
        }

    # --- 3. anchors and spans -------------------------------------------------
    hwl = float(config.geometry.HWL)
    anchors = anchor_indices(baseline["grid"], baseline["P_f_trans_raw"], hwl)
    at_anchors: dict[str, Any] = {}
    for name, index in anchors.items():
        values = [float(baseline["P_f_trans_raw"][index])] + [
            arms[a]["levels"][index]["p_f_trans_arm"] for a, _ in ARMS
        ]
        at_anchors[name] = {
            "stage_m_msl": float(baseline["grid"][index]),
            "p_f_trans_baseline": float(baseline["P_f_trans_raw"][index]),
            "p_f_static_baseline": float(baseline["P_f_static_raw"][index]),
            "span_trans": _span(values),
            "arms": {
                a: {
                    "p_f_trans": arms[a]["levels"][index]["p_f_trans_arm"],
                    "ratio_trans": arms[a]["levels"][index]["ratio_trans"],
                    "rho": arms[a]["levels"][index]["rho"],
                }
                for a, _ in ARMS
            },
        }

    # --- 4. the cancellation verdict -----------------------------------------
    cancellation: dict[str, Any] = {}
    for arm_label, _ in ARMS:
        levels = arms[arm_label]["levels"]
        evaluated = [entry for entry in levels if entry["rho"] is not None]
        resolved = [entry for entry in evaluated if entry["rho"]["resolved"]]
        departures = [
            max(entry["rho"]["rho"], 1.0 / entry["rho"]["rho"])
            for entry in resolved
            if entry["rho"]["rho"] > 0.0
        ]
        # Exact-reciprocal check: with the static branch bit-identical, rho must
        # equal P_trans,baseline / P_trans,arm level by level.
        recip_err = []
        for entry in evaluated:
            if entry["p_f_trans_arm"] > 0.0 and entry["p_f_trans_baseline"] > 0.0:
                expected = entry["p_f_trans_baseline"] / entry["p_f_trans_arm"]
                recip_err.append(abs(entry["rho"]["rho"] / expected - 1.0))
        cancellation[arm_label] = {
            "trans_not_static_rows_baseline": sum(
                entry["trans_not_static_baseline"] for entry in levels
            ),
            "trans_not_static_rows_arm": sum(
                entry["trans_not_static_arm"] for entry in levels
            ),
            "levels_evaluated": len(evaluated),
            "levels_resolved": len(resolved),
            "max_resolved_departure_factor": max(departures) if departures else None,
            "max_reciprocal_identity_error": max(recip_err) if recip_err else None,
        }

    return {
        "section": label,
        "config": spec["config"],
        "production_file": spec["production"],
        "cross_section_id": config.cross_section_id,
        "d70_interpretation": config.priors.d70_interpretation,
        "n_samples": int(config.mc.n_samples),
        "design_hwl_m_msl": hwl,
        "z_toe_m_msl": float(config.geometry.z_toe),
        "seepage_length_m": float(config.geometry.L),
        "gate_status": gate_status,
        "grid_m_msl": baseline["grid"].tolist(),
        "anchor_indices": anchors,
        "at_anchors": at_anchors,
        "arms": arms,
        "cancellation": cancellation,
        "elapsed_s": round(time.time() - started, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sections", nargs="*", default=list(SECTIONS))
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--n", type=int, default=None, help="Pilot sample size.")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args(argv)

    if args.n is not None and not args.allow_unverified:
        parser.error(
            "--n changes the sample size, so the gate can never be "
            "bit-identical; pass --allow-unverified to pilot."
        )

    started = time.time()
    sections = []
    for label in args.sections:
        if label not in SECTIONS:
            parser.error(f"unknown section {label!r}; known: {sorted(SECTIONS)}")
        sections.append(
            run_section(
                label,
                SECTIONS[label],
                n_jobs=args.n_jobs,
                n_override=args.n,
                skip_run=args.skip_run,
                allow_unverified=args.allow_unverified,
            )
        )

    payload = {
        "adr": "0049",
        "description": (
            "Companion sensitivity: the critical pipe length l_c of Pol SIE "
            "2024 Eq. (13), bracketed multiplicatively against the frozen "
            "production baseline. l_c anchors the (l_c, H_c) breakpoint of the "
            "transient equilibrium curve and reaches nothing else, so the "
            "static branch is exactly invariant and the bracket is a pure "
            "transient-only knob. Baseline files untouched."
        ),
        "bracket": {
            "lower_factor": CRITICAL_LENGTH_FACTOR_LOWER,
            "upper_factor": CRITICAL_LENGTH_FACTOR_UPPER,
            "upper_provenance": (
                "DgFlow 3D hole-exit critical length 1.36 m for the in-domain "
                "S2-2 case (L = 3 m, D = L/3), Pol 2022 thesis Fig. 5.9 "
                "caption, divided by Eq. (13) at the same geometry "
                f"({_EQ13_S2_2:.6g} m). "
                "Eq. (13) states its own basis as agreement with 2D simulations "
                "(Pol SIE 2024 section 2.3)."
            ),
            "lower_provenance": (
                "The reciprocal of the upper arm. No published case places the "
                "true critical length below Eq. (13); this arm is a mirrored "
                "counterfactual so the bracket is two-sided, not a measurement."
            ),
            "direction_check_b25_245": {
                "measured_l_c_m": B25_245_MEASURED_CRITICAL_LENGTH_M,
                "eq13_l_c_m": _EQ13_B25_245,
                "factor": B25_245_MEASURED_CRITICAL_LENGTH_M / _EQ13_B25_245,
                "note": (
                    "Out of the fitted domain (small-scale box, qualitative "
                    "gate only). Reported as a direction check -- it also sits "
                    "ABOVE Eq. (13) -- and deliberately not used to widen the "
                    "bracket."
                ),
            },
        },
        "channel_reading": {
            "shared_with_static": [],
            "transient_only": [
                "the (l_c, H_c) breakpoint of the piecewise-linear H_eq(l) in "
                "progression.equilibrium_head / integrate_progression"
            ],
            "prediction": (
                "Zero common-mode channels, so no cancellation. Because the "
                "static branch is EXACTLY invariant, the ratio-of-ratios "
                "displacement must equal the reciprocal of the transient "
                "displacement to machine precision at every level."
            ),
        },
        "ratio_statistic": (
            "ADR-0047 section 4.5 paired bootstrap over the 16 joint pattern "
            "counts, 2000 replicates, null pinned at rho = 1.0, imported from "
            "scripts/dem_cross_section_study.py rather than re-implemented."
        ),
        "sections": sections,
        "total_runtime_s": round(time.time() - started, 1),
    }

    if args.n is not None:
        print("\nPilot run (--n): evidence record NOT written.")
        print(json.dumps(_compact(payload["sections"][0]["cancellation"]), indent=2))
        return 0

    JSON_OUT.write_text(
        json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {JSON_OUT.relative_to(REPO_ROOT)}")
    for section in sections:
        print(f"\n{section['section']}  (gate: {section['gate_status']})")
        for name, entry in section["at_anchors"].items():
            span = entry["span_trans"]
            print(
                f"  {name:<20s} {entry['stage_m_msl']:7.2f} m  "
                f"P_t,base {entry['p_f_trans_baseline']:.3e}  "
                f"span {'unbnd' if span is None else format(span, '.3g')}"
            )
        for arm_label, verdict in section["cancellation"].items():
            dep = verdict["max_resolved_departure_factor"]
            print(
                f"  {arm_label}: resolved {verdict['levels_resolved']}"
                f"/{verdict['levels_evaluated']} levels, max departure "
                f"{'n/d' if dep is None else format(dep, '.3f')}, "
                f"reciprocal-identity error "
                f"{verdict['max_reciprocal_identity_error']}, "
                f"trans-not-static rows "
                f"{verdict['trans_not_static_rows_baseline']} -> "
                f"{verdict['trans_not_static_rows_arm']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
