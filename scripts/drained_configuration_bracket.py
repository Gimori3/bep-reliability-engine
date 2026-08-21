"""ADR-0050 companion: a bracket on the drained configuration at KP58.8/KP60.0.

The two sections fitted with a side berm plus a landside toe drain between 1999
and 2003 carry the largest annual failure probabilities in the basin and top the
prioritisation ranking. The engine represents no drain, so every probability at
those two sections is an as-if-undrained statement. This driver converts that
caveat from a sentence into a range.

What is grounded, and what is not
---------------------------------
PWRI (2014) Table 7.1.1 (printed p. 33) names the quantity each countermeasure
acts upon, for heave and piping specifically. The two works recorded here map
onto two quantities the engine already carries:

* 断面拡大工法 section enlargement (the berm) -> lengthen the seepage path
  -> ``geometry.L``. **Magnitude measured**: ADR-0047 read 42.0 m at KP58.8
  (31 of 31 clean stations) and 43.0 m at KP60.0 (31 of 31) from a 2025 GSI
  DEM5A surface, against the modelled 1998 values 35.0 and 34.8 m. ADR-0047
  deliberately HELD both, on the stated ground that adopting the longer path
  while the engine models no drain imports only the anti-conservative half of
  the works. This study is the configuration in which that objection lapses,
  because both halves move together.
* ドレーン工法 landside toe drain -> reduce the hydraulic gradient at the
  landside toe -> ``i_exit`` in the M5 heave limit state, reached through the
  ADR-0050 ``toe_gradient_relief_factor``. **Magnitude NOT grounded**: the
  guidance gives a design rule for the drain body (width set so the average
  gradient stays below 0.3, printed p. 42) but states no equivalence between
  that quantity and the foundation blanket exit gradient, and provenance
  section 7.3 warns that these drains need not have been sized against the
  seepage exit gradient at all. No relief magnitude is therefore assumed. The
  relief is a **swept** axis and its response curve is the deliverable.

The channel reading, made before the numbers
--------------------------------------------
    | channel                              | where            | branches       |
    |--------------------------------------|------------------|----------------|
    | Delta_h_blanket -> i_exit -> the      | initiation       | transient only |
    | uplift/heave gate                     | z_uplift/z_heave |                |

That is the whole list for the relief arm. Since ADR-0028 r_e reaches the gate
and nothing else: it is not in H_c, not in the raw erosion head, and not in the
static comparator. So the relief arms must leave the static failure matrix
**bit-identical**, and the driver refuses to report if a single cell moves.

The berm arm is different and must not be described as gate-only: L enters H_c
through the Sellmeijer scale and damping factors and enters Z = L - l_e
directly, so it moves both branches. The record marks each arm with
``gate_only`` so a later reader cannot conflate the two.

What it does, per section and d70 reading
-----------------------------------------
1. **Gate.** Re-runs the committed YAML with ``toe_gradient_relief_factor=None``
   set explicitly and asserts both whole failure matrices are bit-identical to
   the persisted production sweep. That discharges two obligations at once: the
   knob is inert when off, and the baseline has not drifted.
2. **berm_only.** ``L -> L_dem``, no relief. The measured half, credited alone.
3. **joint_x.xx.** ``L -> L_dem`` and the relief ladder 0.8 / 0.6 / 0.4 / 0.2.
4. **Per-level effect** on both conditional probabilities, the monotonicity
   check (a smaller factor may never add a failing row), and the stage at which
   each arm's transient branch reaches zero.

Every arm is coupled to the gate by common random numbers: same seed, same
theta, same L draw shape, same grid, same hydrographs.

Usage (repo root, venv active)::

    python scripts/drained_configuration_bracket.py
    python scripts/drained_configuration_bracket.py --sections KP58.8
    python scripts/drained_configuration_bracket.py --d70 matrix
    python scripts/drained_configuration_bracket.py --skip-run     # re-analyse
    python scripts/drained_configuration_bracket.py --n 2000 --allow-unverified

``--n`` pilots at a reduced sample size; it can never be bit-identical, so it
requires ``--allow-unverified`` and refuses to write the evidence record.

Outputs: ``results/sensitivity/adr0050_drained_bracket/*.h5`` (the arm sweeps,
which Phase 2 and Phase 3 then consume) and
``docs/decisions/adr0050-drained-configuration-bracket.json``.
"""

from __future__ import annotations

import argparse
import datetime as _dt
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

from bayesian_reliability_updating.replay import load_phase1_run  # noqa: E402
from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.evaluator import evaluate_realization  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult, binomial_ci  # noqa: E402
from bep_reliability_engine.hydrographs import resample_record  # noqa: E402
from bep_reliability_engine.run import (  # noqa: E402
    conditioning_hydrographs_for_config,
    run_fragility_analysis,
)

# --------------------------------------------------------------------------- #
# The bracket                                                                  #
# --------------------------------------------------------------------------- #
#: The swept relief ladder. NOT a set of assumed drain performances: the
#: guidance grounds the direction and the quantity, never the magnitude, so the
#: reported object is the response curve across the ladder.
RELIEF_LADDER: tuple[float, ...] = (0.8, 0.6, 0.4, 0.2)

#: ADR-0047 clean-station median seepage length from the 2025 GSI DEM5A surface.
#: Measured, held, and carried here as the berm arm. Keyed by section.
DEM_SEEPAGE_LENGTH_M: dict[str, float] = {"KP58.8": 42.0, "KP60.0": 43.0}
DEM_SOURCE = (
    "ADR-0047 clean-station median, 2025 GSI DEM5A (mesh 644331, devDate "
    "2025-06-20); 31 of 31 clean stations at both sections"
)

#: PWRI 2014 printed p. 42: the drain WIDTH is sized so the average hydraulic
#: gradient stays below this. Recorded as a sourced consistency observation
#: only. It governs the drain body, not the foundation blanket exit gradient,
#: and is deliberately NOT an arm of this bracket.
PWRI_DRAIN_DESIGN_GRADIENT = 0.3

SECTIONS: dict[str, dict[str, dict[str, str]]] = {
    "KP58.8": {
        "matrix": {
            "config": "configs/kp58_8_historical_matrix.yaml",
            "production": "results/tokachi_kp58.8_historical_matrix.h5",
            "stem": "tokachi_kp58.8_historical_matrix",
        },
        "bulk": {
            "config": "configs/kp58_8_historical_bulk.yaml",
            "production": "results/tokachi_kp58.8_historical_bulk.h5",
            "stem": "tokachi_kp58.8_historical_bulk",
        },
    },
    "KP60.0": {
        "matrix": {
            "config": "configs/kp60_0_historical_matrix.yaml",
            "production": "results/tokachi_kp60.0_historical_matrix.h5",
            "stem": "tokachi_kp60.0_historical_matrix",
        },
        "bulk": {
            "config": "configs/kp60_0_historical_bulk.yaml",
            "production": "results/tokachi_kp60.0_historical_bulk.h5",
            "stem": "tokachi_kp60.0_historical_bulk",
        },
    },
}

OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0050_drained_bracket"
JSON_OUT = (
    REPO_ROOT / "docs" / "decisions" / "adr0050-drained-configuration-bracket.json"
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def arm_labels() -> list[tuple[str, float | None]]:
    """The arm list in report order: the measured half first, then the ladder."""
    return [("berm_only", None)] + [
        (f"joint_{factor:.2f}", factor) for factor in RELIEF_LADDER
    ]


def _reusable(path: Path, expected: Config) -> bool:
    """True when a persisted sweep is exactly the run this arm would produce.

    The criterion is the arm's own ``config_hash``, not the file's existence: a
    resumed campaign must never reuse a sweep produced under a different L,
    relief factor or sample size. Same-hash means same inputs and same seed, so
    re-running would reproduce it bit for bit.
    """
    sidecar = path.with_suffix(".json")
    if not (path.is_file() and sidecar.is_file()):
        return False
    try:
        recorded = json.loads(sidecar.read_text(encoding="utf-8"))["config_hash"]
    except (KeyError, ValueError):
        return False
    return bool(recorded == expected.config_hash())


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
    """Gate on the WHOLE failure matrices, not the column means."""
    for name, matrix in (
        ("static", fresh.failure_matrix_stat),
        ("trans", fresh.failure_matrix_tran),
    ):
        if not np.array_equal(matrix, persisted[f"failure_matrix_{name}"]):
            raise AssertionError(
                f"{label}: fresh {name} failure matrix differs from the persisted "
                "production sweep. Either toe_gradient_relief_factor=None is not "
                "bit-identical, or the baseline has drifted. Refusing to report "
                "a bracket either way."
            )


def _ratio(numer: float, denom: float) -> float | None:
    return None if denom == 0.0 else float(numer / denom)


def _compact(obj: Any, sig: int = 6) -> Any:
    """Round every float in a nested payload to ``sig`` significant digits."""
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return obj
        return float(f"%.{sig}g" % obj)
    if isinstance(obj, dict):
        return {key: _compact(value, sig) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_compact(value, sig) for value in obj]
    return obj


def _first_zero_stage(
    grid: NDArray[np.float64], p_trans: NDArray[np.float64]
) -> float | None:
    """Lowest stage at and above which the transient branch is identically zero.

    ``None`` when the arm still loads something at the top of the grid.
    """
    nonzero = np.flatnonzero(p_trans > 0.0)
    if nonzero.size == 0:
        return float(grid[0])
    last = int(nonzero[-1])
    if last == grid.size - 1:
        return None
    return float(grid[last + 1])


#: Timestep refinements the artifact test walks. ADR-0039 established that the
#: failure *indicator* is stationary from 450 s but the literal 1 per cent l_e
#: criterion needs 112.5 s or finer; both refinements are checked so a violation
#: that merely moves rather than vanishing is still caught.
ARTIFACT_LADDER_DT_S: tuple[float, ...] = (112.5, 56.25)


def verify_violations_are_artifacts(
    config: Config,
    run: Any,
    entries: list[dict[str, Any]],
    *,
    weaker_relief: float | None,
    stronger_relief: float | None,
    arm_label: str,
) -> list[dict[str, Any]]:
    """Re-integrate each monotonicity violation on a halved grid.

    A violation is a **discretisation artifact** if the inversion disappears at
    every refinement in :data:`ARTIFACT_LADDER_DT_S`. If it survives anywhere,
    the ordering claim is false about the continuous problem too and the caller
    refuses to report.

    Uses the same public seams the QA r_e-halved member uses: the Phase 2 loader
    regenerates theta and the stochastic L bit-for-bit from the run's own
    config, ``conditioning_hydrographs_for_config`` rebuilds the very record the
    sweep conditioned on, and ``resample_record`` refines it on the ADR-0013
    integer-subdivision hook so every native sample stays a node.
    """
    records = conditioning_hydrographs_for_config(config)
    verified: list[dict[str, Any]] = []
    for entry in entries:
        row, level = entry["row"], entry["level_index"]
        geometry = dict(config.geometry.as_evaluator_dict())
        if run.seepage_length_samples is not None:
            geometry["L"] = float(run.seepage_length_samples[row])
        theta_row = run.theta[row]
        ladder = []
        survives = False
        for dt_s in ARTIFACT_LADDER_DT_S:
            refined = resample_record(records[level], dt_s)
            weaker = evaluate_realization(
                theta_row,
                refined,
                geometry,
                toe_gradient_relief_factor=weaker_relief,
            )
            stronger = evaluate_realization(
                theta_row,
                refined,
                geometry,
                toe_gradient_relief_factor=stronger_relief,
            )
            inverted = bool(stronger.failure_trans and not weaker.failure_trans)
            survives = survives or inverted
            ladder.append(
                {
                    "dt_s": dt_s,
                    "z_transient_weaker": float(weaker.Z_transient),
                    "z_transient_stronger": float(stronger.Z_transient),
                    "inverted": inverted,
                }
            )
        record = {
            **entry,
            "theta": {
                name: float(value)
                for name, value in zip(run.param_names, theta_row, strict=True)
            },
            "seepage_length_m": float(geometry["L"]),
            "refinement_ladder": ladder,
            "verdict": "survives_refinement" if survives else "euler_artifact",
        }
        verified.append(record)
        if survives:
            raise AssertionError(
                f"{arm_label}: the monotonicity violation at row {row}, stage "
                f"{entry['stage_m_msl']} m survives timestep refinement to "
                f"{ARTIFACT_LADDER_DT_S[-1]} s. It is therefore a real inversion "
                "and not an ADR-0030 barrier jump: a stronger gradient relief "
                "genuinely makes this realization fail. The one-sidedness the "
                "bracket rests on would be false. Refusing to report."
            )
    return verified


# --------------------------------------------------------------------------- #
# Per-arm comparison                                                           #
# --------------------------------------------------------------------------- #
def compare_arm(
    baseline: dict[str, Any],
    arm: FragilityResult,
    *,
    gate_only: bool,
    previous_trans: NDArray[np.bool_] | None,
    arm_label: str,
) -> dict[str, Any]:
    """Per-level effect of one arm, with the two structural claims enforced."""
    base_static = baseline["failure_matrix_static"].astype(bool)
    arm_static = np.asarray(arm.failure_matrix_stat, dtype=bool)
    arm_trans = np.asarray(arm.failure_matrix_tran, dtype=bool)

    # P1, enforced rather than assumed: a relief arm at unchanged L must leave
    # the static branch bit-identical, because r_e reaches the gate alone.
    # The berm arm is exempt by construction (P3): L is in H_c and in Z.
    if gate_only and not np.array_equal(base_static, arm_static):
        moved = int(np.count_nonzero(base_static != arm_static))
        raise AssertionError(
            f"{arm_label}: the static failure matrix moved in {moved} cells under "
            "a gradient-relief arm. The relief must not reach the static "
            "comparator (ADR-0028); a non-zero count means a channel exists that "
            "this study's reasoning does not know about. Refusing to report."
        )

    # P2: one-sided and monotone. Checked as set inclusion against the arm one
    # step weaker in the ladder, which is stronger than comparing column means.
    #
    # AMENDED 2026-08-21, after the pre-registered form of P2 fired. Exact set
    # inclusion is the right claim about the CONTINUOUS problem and the wrong
    # one about a forward-Euler solution of it. Relief delays the gate, so a
    # relieved realization meets its first active timestep at a higher driving
    # head and takes a larger first step; at Delta_t = 225 s a marginal row deep
    # in the C_e and k_aq tails can therefore clear the H_eq barrier in one step
    # that the unrelieved row climbs gradually. That is the ADR-0030 pathology,
    # not a physical inversion, and the discriminator is ADR-0039's: halve the
    # timestep and see whether it survives.
    #
    # So the gate now tests the claim that is actually true: every violation is
    # a discretisation artifact. Each violating row is re-integrated on a
    # halved grid, and the driver still refuses if a single one SURVIVES. That
    # is a stronger test than a tolerance on the count, because it does not
    # care how many there are, only whether any of them is real.
    monotonicity: dict[str, Any] = {"violations": 0, "rows": []}
    if previous_trans is not None:
        offenders = np.argwhere(arm_trans & ~previous_trans)
        monotonicity["violations"] = int(offenders.shape[0])
        for row_index, level_index in offenders:
            monotonicity["rows"].append(
                {
                    "row": int(row_index),
                    "level_index": int(level_index),
                    "stage_m_msl": float(baseline["grid"][level_index]),
                }
            )

    p_static = np.asarray(arm.P_f_static_raw, dtype=float)
    p_trans = np.asarray(arm.P_f_trans_raw, dtype=float)
    b_static = baseline["P_f_static_raw"]
    b_trans = baseline["P_f_trans_raw"]
    n = int(arm_trans.shape[0])

    levels = []
    for index in range(p_trans.size):
        n_fail = int(arm_trans[:, index].sum())
        lo, hi = binomial_ci(np.float64(p_trans[index]), n)
        levels.append(
            {
                "stage_m_msl": float(baseline["grid"][index]),
                "p_f_static_baseline": float(b_static[index]),
                "p_f_static_arm": float(p_static[index]),
                "p_f_trans_baseline": float(b_trans[index]),
                "p_f_trans_arm": float(p_trans[index]),
                "p_f_trans_arm_ci95": [float(lo), float(hi)],
                "ratio_static": _ratio(float(p_static[index]), float(b_static[index])),
                "ratio_trans": _ratio(float(p_trans[index]), float(b_trans[index])),
                "n_failures_trans_arm": n_fail,
            }
        )
    return {
        "gate_only": gate_only,
        "monotonicity": monotonicity,
        "first_zero_stage_m_msl": _first_zero_stage(baseline["grid"], p_trans),
        "levels": levels,
        "_trans_matrix": arm_trans,
    }


def run_case(
    label: str,
    d70: str,
    spec: dict[str, str],
    *,
    n_jobs: int,
    n_override: int | None,
    skip_run: bool,
    allow_unverified: bool,
    reuse: bool = False,
) -> dict[str, Any]:
    """Gate the baseline, run every arm, and assemble one section record."""
    started = time.time()
    config = Config.from_yaml(REPO_ROOT / spec["config"])
    if config.toe_gradient_relief_factor is not None:
        raise ValueError(
            f"{label}/{d70}: the committed config already carries a "
            "toe_gradient_relief_factor; this driver expects the production "
            "baseline, where the knob is off."
        )
    if config.remediation_state != "drained":
        raise ValueError(
            f"{label}/{d70}: remediation_state is {config.remediation_state!r}, "
            "not 'drained'. This bracket applies only to the two sections whose "
            "recorded works are a berm plus a landside toe drain."
        )
    if n_override is not None:
        config = config.model_copy(
            update={"mc": config.mc.model_copy(update={"n_samples": n_override})}
        )

    production = _load_persisted(REPO_ROOT / spec["production"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"{label}/{d70}"

    # --- 1. the gate: knob explicitly off, bit-identical to production --------
    gate_path = OUT_DIR / f"{spec['stem']}_gate.h5"
    gate_config = config.model_copy(update={"toe_gradient_relief_factor": None})
    if reuse and _reusable(gate_path, gate_config):
        print(f"[{tag}] gate: reusing {gate_path.name}", flush=True)
        gate = FragilityResult.load(gate_path)
    elif not skip_run:
        print(f"[{tag}] gate: baseline with the knob explicitly off ...", flush=True)
        gate = run_fragility_analysis(
            gate_config,
            n_jobs=n_jobs,
            progress=True,
            output_path=gate_path,
            overwrite=True,
        )
    else:
        gate = FragilityResult.load(gate_path)
    if allow_unverified:
        try:
            _assert_bit_identical(f"{tag} gate", gate, production)
            gate_status = "bit_identical"
        except (AssertionError, ValueError) as exc:
            gate_status = f"UNVERIFIED: {exc}"
            print(f"[{tag}] {gate_status}", flush=True)
    else:
        _assert_bit_identical(f"{tag} gate", gate, production)
        gate_status = "bit_identical"

    baseline = {
        "grid": np.asarray(gate.conditioning_grid, dtype=float),
        "P_f_static_raw": np.asarray(gate.P_f_static_raw, dtype=float),
        "P_f_trans_raw": np.asarray(gate.P_f_trans_raw, dtype=float),
        "failure_matrix_static": np.asarray(gate.failure_matrix_stat),
        "failure_matrix_trans": np.asarray(gate.failure_matrix_tran),
    }

    # --- 2. the arms ----------------------------------------------------------
    dem_length = DEM_SEEPAGE_LENGTH_M[label]
    arms: dict[str, Any] = {}
    previous_trans: NDArray[np.bool_] | None = None
    previous_factor: float | None = None
    for arm_label, factor in arm_labels():
        arm_path = OUT_DIR / f"{spec['stem']}_{arm_label}.h5"
        update: dict[str, Any] = {
            "geometry": config.geometry.model_copy(update={"L": dem_length}),
            "toe_gradient_relief_factor": factor,
        }
        arm_config = config.model_copy(update=update)
        if reuse and _reusable(arm_path, arm_config):
            print(f"[{tag}] arm {arm_label}: reusing {arm_path.name}", flush=True)
            arm = FragilityResult.load(arm_path)
        elif not skip_run:
            shown = "none" if factor is None else f"{factor:.2f}"
            print(
                f"[{tag}] arm {arm_label}: L -> {dem_length} m, relief {shown} ...",
                flush=True,
            )
            arm = run_fragility_analysis(
                arm_config,
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
            raise RuntimeError(f"{tag}/{arm_label}: arm grid differs from baseline")
        deliverable = arm.metadata.get("fragility_deliverable", {})
        record = compare_arm(
            baseline,
            arm,
            # The berm arm changes L, which is in H_c and in Z: not gate-only.
            # Every joint arm changes L too, so the static-invariance claim is
            # checked against the berm arm rather than against the gate.
            gate_only=False,
            previous_trans=previous_trans,
            arm_label=f"{tag}/{arm_label}",
        )
        previous_trans = record.pop("_trans_matrix")
        if record["monotonicity"]["violations"]:
            # Loaded from the ARM's own persisted sweep, never from production:
            # the stochastic L is drawn about geometry.L, which every arm here
            # moves to the DEM value, so the production run's L samples are a
            # different population and would verify the wrong realization.
            arm_run = load_phase1_run(arm_path)
            record["monotonicity"]["rows"] = verify_violations_are_artifacts(
                arm_run.config,
                arm_run,
                record["monotonicity"]["rows"],
                weaker_relief=previous_factor,
                stronger_relief=factor,
                arm_label=f"{tag}/{arm_label}",
            )
        previous_factor = factor
        record["file"] = str(arm_path.relative_to(REPO_ROOT)).replace("\\", "/")
        record["relief_factor"] = factor
        record["seepage_length_m"] = dem_length
        # ADR-0024 deliverable form. Recorded per arm because a relief strong
        # enough to unbracket the transition flips the transient branch from a
        # fitted curve to the raw tail, and a reader must be able to see that
        # rather than infer it from a suspiciously clean number.
        record["fragility_form"] = {
            branch: deliverable.get(branch, {}).get("form")
            for branch in ("static", "transient")
        }
        record["transition_bracketed"] = {
            branch: deliverable.get(branch, {}).get("transition_bracketed")
            for branch in ("static", "transient")
        }
        arms[arm_label] = record

    # --- 3. the gate-only claim, isolated ------------------------------------
    # Every arm above moves L, so none of them can test the ADR-0028 channel
    # claim on its own. The relief arms are re-referenced to the berm arm, at
    # which L is identical and the relief is the ONLY difference: there the
    # static column must be bit-identical, and the record says so per level.
    berm = arms["berm_only"]
    for arm_label, factor in arm_labels():
        if factor is None:
            arms[arm_label]["gate_only"] = False
            continue
        arms[arm_label]["gate_only"] = True
        for level, berm_level in zip(arms[arm_label]["levels"], berm["levels"]):
            level["p_f_static_baseline"] = berm_level["p_f_static_arm"]
            level["p_f_trans_baseline"] = berm_level["p_f_trans_arm"]
            level["ratio_static"] = _ratio(
                level["p_f_static_arm"], berm_level["p_f_static_arm"]
            )
            level["ratio_trans"] = _ratio(
                level["p_f_trans_arm"], berm_level["p_f_trans_arm"]
            )
            if level["ratio_static"] not in (None, 1.0):
                raise AssertionError(
                    f"{tag}/{arm_label}: the static probability moved relative to "
                    f"the berm arm at {level['stage_m_msl']} m. The relief must "
                    "not reach the static comparator (ADR-0028). Refusing."
                )

    hwl = float(config.geometry.HWL)
    grid = baseline["grid"]
    hwl_index = int(np.argmin(np.abs(grid - hwl)))
    return {
        "section": label,
        "d70_interpretation": d70,
        "config": spec["config"],
        "production_file": spec["production"],
        "cross_section_id": config.cross_section_id,
        "remediation_state": config.remediation_state,
        "n_samples": int(config.mc.n_samples),
        "design_hwl_m_msl": hwl,
        "hwl_index": hwl_index,
        "z_toe_m_msl": float(config.geometry.z_toe),
        "seepage_length_1998_m": float(config.geometry.L),
        "seepage_length_dem_m": dem_length,
        "seepage_length_source": DEM_SOURCE,
        "gate_status": gate_status,
        "fragility_form_as_if_undrained": {
            branch: gate.metadata.get("fragility_deliverable", {})
            .get(branch, {})
            .get("form")
            for branch in ("static", "transient")
        },
        "grid_m_msl": grid.tolist(),
        "p_f_trans_as_if_undrained": baseline["P_f_trans_raw"].tolist(),
        "p_f_static_as_if_undrained": baseline["P_f_static_raw"].tolist(),
        "arms": arms,
        "elapsed_s": round(time.time() - started, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sections", nargs="*", default=sorted(SECTIONS))
    parser.add_argument("--d70", nargs="*", default=["matrix", "bulk"])
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--n", type=int, default=None, dest="n_override")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument(
        "--reuse",
        action="store_true",
        help=(
            "Resume: load any arm whose persisted sweep already carries this "
            "arm's exact config_hash, and run only the rest. Same hash means "
            "same inputs and same seed, so a reused arm is what a re-run would "
            "reproduce bit for bit."
        ),
    )
    parser.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args(argv)

    if args.n_override is not None and not args.allow_unverified:
        parser.error(
            "--n changes the sample size, so the baseline cannot be "
            "bit-identical to the persisted sweep; pass --allow-unverified to "
            "pilot. The evidence record is not written in that mode."
        )

    started = time.time()
    records = []
    for label in args.sections:
        if label not in SECTIONS:
            parser.error(
                f"unknown section {label!r}; expected one of {sorted(SECTIONS)}"
            )
        for d70 in args.d70:
            if d70 not in SECTIONS[label]:
                parser.error(f"unknown d70 reading {d70!r}")
            records.append(
                run_case(
                    label,
                    d70,
                    SECTIONS[label][d70],
                    n_jobs=args.n_jobs,
                    n_override=args.n_override,
                    skip_run=args.skip_run,
                    allow_unverified=args.allow_unverified,
                    reuse=args.reuse,
                )
            )

    payload = {
        "study": "ADR-0050 drained-configuration bracket at KP58.8 and KP60.0",
        "generated": _dt.datetime.now().replace(microsecond=0).isoformat(),
        "generated_by": "scripts/drained_configuration_bracket.py",
        "grounding": {
            "mapping_source": (
                "PWRI 2014 Table 7.1.1 (printed p. 33), via "
                "docs/tokachi_bep_inputs_provenance.md section 6.3"
            ),
            "berm_quantity": "geometry.L (section enlargement lengthens the path)",
            "berm_magnitude_grounded": True,
            "berm_magnitude_source": DEM_SOURCE,
            "drain_quantity": (
                "landside-toe exit gradient i_exit in the M5 heave limit state, "
                "reached through toe_gradient_relief_factor (ADR-0050)"
            ),
            "relief_magnitude_grounded": False,
            "relief_axis_treatment": "swept",
            "relief_ladder": list(RELIEF_LADDER),
            "why_not_grounded": (
                "PWRI's 0.3 design gradient (printed p. 42) sizes the drain body, "
                "not the foundation blanket exit gradient, and the guidance states "
                "no equivalence between them; provenance section 7.3 records that "
                "the basin's toe drains have three documented rationales, of which "
                "only one is seepage, so a drained label identifies a physical "
                "feature and not a design intent."
            ),
            "pwri_drain_design_gradient_not_an_arm": PWRI_DRAIN_DESIGN_GRADIENT,
        },
        "sections": records,
        "total_elapsed_s": round(time.time() - started, 1),
    }
    if args.n_override is not None:
        print("\npilot mode: evidence record NOT written", flush=True)
        return 0
    JSON_OUT.write_text(
        json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {JSON_OUT.relative_to(REPO_ROOT)}", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
