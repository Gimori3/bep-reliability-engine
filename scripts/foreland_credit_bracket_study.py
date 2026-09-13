"""ADR-0052 companion: the declined foreland seepage-length credit, measured.

The engine splits the gross head into three resistances in series -- the
foreland entry length ``lambda_out_eff``, the under-levee path ``L`` and the
hinterland exit length ``lambda_in`` -- and uses that split for the response
factor ``r_e = lambda_in / (lambda_out_eff + L + lambda_in)``, the USACE
EM 1110-2-1913 Appendix B Case 7a landside head factor. Since ADR-0028 that
split reaches the uplift and heave gate and **nothing else**: both piping heads
are gross, and both limit states take Sellmeijer's critical head at the
under-levee ``L`` alone.

So the entry resistance is carried in the gate and declined in the rule. That
is a legitimate, conservative reading -- gross head over the under-levee length
is Sellmeijer's own calibration geometry -- and TR Zandmeevoerende Wellen (1999)
section 4.4.2 states the alternative explicitly and permissively: a foreland
displaces the theoretical entry point riverward by
``L'_v = lambda * tanh(L_v / lambda)`` -- the same tanh section 4.4.1 gives
``lambda_out_eff`` -- and that increase in seepage length "mag in rekening
worden gebracht" in Sellmeijer's rule, as in Bligh's and Lane's. *May* be, not
must be. Declining a permissive credit is a recognised conservative
simplification, so this driver does **not** change the production baseline. It
measures what declining it is worth.

What it does, per section:

1. **Baseline gate.** Re-runs the section's committed YAML with
   ``foreland_seepage_credit=None`` set *explicitly* and asserts the two failure
   matrices are bit-identical to the persisted production sweep. One run
   discharges two obligations: the knob is inert when off, and the baseline has
   not drifted.
2. **Two arms.** The same config at a half credit (phi = 0.5) and the full
   TR Zmw 1999 section 4.4.2 credit (phi = 1.0). Same seed, same theta, same L
   draw, same grid, same hydrographs, so the arms are coupled to the baseline by
   common random numbers row for row -- which is what makes step 5 exact.
3. **Per-level conditional probabilities** on BOTH branches, baseline vs arms.
4. **Design-level failing-realization counts** on both branches under both arms.
5. **The cancellation test**, the ADR-0047 section 4.5 paired-bootstrap
   ratio-of-ratios statistic, imported rather than re-implemented::

       rho = (P_static / P_transient)_arm  /  (P_static / P_transient)_baseline

   null pinned at rho = 1.0, 2000 replicates over the 16 joint pattern counts,
   a level counted ``resolved`` only when the 95 per cent interval excludes 1.
6. **Stage displacement** of the transient transition, and -- because under the
   credited arm the transition leaves the reachable grid at every section -- of
   the ADR-0040 closed-form sustained-peak upper bound
   ``gate AND H_erosion > H_c,trans``, on a fine scan grid.

The channel reading, made BEFORE the numbers (the epistemic-bracket-synthesis
rule), and the prediction that follows from it, are frozen in
``docs/decisions/adr0052-foreland-credit-prereg.md``; its SHA-256 is written
into the evidence record so the prediction cannot be edited after the fact.

Unlike ADR-0049 and ADR-0050, this knob is **not** single-branch. It reaches
``H_c``, and ``H_c`` is single-source, so BOTH columns move. This driver
therefore *counts* the static cells that moved rather than asserting none did.

Usage (from the repo root, venv active)::

    python scripts/foreland_credit_bracket_study.py                  # matrix
    python scripts/foreland_credit_bracket_study.py --reading bulk
    python scripts/foreland_credit_bracket_study.py --sections KP62.0
    python scripts/foreland_credit_bracket_study.py --skip-run       # re-analyse
    python scripts/foreland_credit_bracket_study.py --n 2000 --allow-unverified

``--n`` pilots at a reduced sample size; it can never be bit-identical, so it
requires ``--allow-unverified`` and refuses to write the evidence record.
"""

from __future__ import annotations

import argparse
import hashlib
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
from bep_reliability_engine.evaluator import (  # noqa: E402
    evaluate_batch_diagnostics,
)
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402
from bep_reliability_engine.gap_decomposition import (  # noqa: E402
    sustained_peak_record,
)
from bep_reliability_engine.hydraulics import (  # noqa: E402
    leakage_length_in,
    leakage_length_out,
    response_factor,
)
from bep_reliability_engine.progression import (  # noqa: E402
    resolve_crack_resistance_factor,
)
from bep_reliability_engine.run import (  # noqa: E402
    run_fragility_analysis,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_theta  # noqa: E402
from bep_reliability_engine.sellmeijer import compute_critical_head  # noqa: E402


def _load_adr0047_module():
    """Import the ADR-0047 study module for its ratio-of-ratios kernel.

    The paired-bootstrap statistic is **reused, never re-implemented**: a second
    copy could drift from the one that produced the ADR-0047, ADR-0049 and
    epistemic-bracket-synthesis numbers this study sits beside.
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
#: The two credited arms. phi is the fraction of each realization's own
#: lambda_out_eff added to the seepage length the Sellmeijer rule is evaluated
#: at. 1.0 is exactly the TR Zmw 1999 section 4.4.2 displacement L'_v; 0.5 is a
#: partial credit, included so the response is shown to be graded rather than
#: read off one endpoint.
ARMS: list[tuple[str, float]] = [
    ("credit_half", 0.5),
    ("credit_full", 1.0),
]

SECTIONS: dict[str, dict[str, str]] = {
    "KP57.4": {"slug": "kp57_4", "stem": "tokachi_kp57.4"},
    "KP58.8": {"slug": "kp58_8", "stem": "tokachi_kp58.8"},
    "KP60.0": {"slug": "kp60_0", "stem": "tokachi_kp60.0"},
    "KP62.0": {"slug": "kp62_0", "stem": "tokachi_kp62.0"},
}

OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0052_foreland_credit"
PREREG = REPO_ROOT / "docs" / "decisions" / "adr0052-foreland-credit-prereg.md"

#: Transient P_f the "rising limb" anchor targets (ADR-0045's shoulder).
RISING_LIMB_P_F = 2.0e-3
#: Transient P_f the "transition midpoint" anchor targets (ADR-0048's shoulder).
TRANSITION_P_F = 0.5
#: Minimum failure count in every one of the four cells before a level's ratio
#: is reported at all (the ADR-0047 convention, deliberately low).
RATIO_MIN_FAILURES = 10

#: Exceedance probabilities the stage displacement is quoted at.
DISPLACEMENT_ANCHORS = (1.0e-3, 1.0e-2, 1.0e-1, 0.5)
#: Scan step of the sustained-peak fine grid [m]. The production conditioning
#: grids step 0.25 m, so this resolves a displacement an order finer.
SCAN_STEP_M = 0.05
#: How far above the section's design HWL the scan reaches. The credited arm
#: pushes the bound well above the crest, which is hypothetical loading -- it is
#: reported as a displacement of an indicator, never as an attainable stage.
SCAN_ABOVE_HWL_M = 14.0


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _config_path(slug: str, reading: str) -> Path:
    return REPO_ROOT / "configs" / f"{slug}_historical_{reading}.yaml"


def _production_path(stem: str, reading: str) -> Path:
    return REPO_ROOT / "results" / f"{stem}_historical_{reading}.h5"


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
                "production sweep. Either foreland_seepage_credit=None is not "
                "bit-identical, or the baseline has drifted. Refusing to report "
                "a sensitivity either way."
            )


def anchor_indices(
    grid: NDArray[np.float64], p_trans: NDArray[np.float64], hwl: float
) -> dict[str, int]:
    """The five conditioning levels the tables are quoted at (ADR-0049 §3)."""
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


def _crossing_stage(
    grid: NDArray[np.float64], probs: NDArray[np.float64], target: float
) -> float | None:
    """Stage at which a monotone-rising probability curve reaches ``target``.

    Linear interpolation between the bracketing scan points. ``None`` when the
    curve never reaches the target inside the scanned range -- which is itself a
    result, and is reported as such rather than extrapolated.
    """
    above = np.flatnonzero(probs >= target)
    if above.size == 0:
        return None
    first = int(above[0])
    if first == 0:
        return float(grid[0])
    x0, x1 = float(grid[first - 1]), float(grid[first])
    y0, y1 = float(probs[first - 1]), float(probs[first])
    if y1 == y0:
        return x1
    return float(x0 + (target - y0) * (x1 - x0) / (y1 - y0))


# --------------------------------------------------------------------------- #
# The prior-mean series split (the Part 1 reproduction, carried in the record)  #
# --------------------------------------------------------------------------- #
def prior_mean_baseline(config: Config) -> dict[str, float]:
    """The three-resistance split and the credited H_c ratio at the priors.

    Deterministic, computed from the committed config's own prior means through
    the engine's own kernels -- this is the table the ADR quotes, and it is
    recomputed here rather than pasted so it cannot drift from the code.
    """
    means = {
        name: float(config.priors.__getattribute__(name).mean)
        for name in ("k_aq", "d_70", "D_aq", "D_bl", "k_bl")
    }
    geom = config.geometry
    lam_in = float(
        leakage_length_in(means["k_aq"], means["D_aq"], means["D_bl"], means["k_bl"])
    )
    lam_out = float(
        leakage_length_out(
            means["k_aq"],
            means["D_aq"],
            geom.D_fore,
            geom.k_fore,
            geom.foreshore_width,
        )
    )
    length = float(geom.L)
    r_e = float(response_factor(lam_in, lam_out, length))
    theta = np.array(
        [
            means["k_aq"],
            means["d_70"],
            means["D_aq"],
            means["D_bl"],
            means["k_bl"],
            float(config.priors.gamma_bl_sub.mean),
            float(config.priors.C_e.mean),
        ]
    )
    kwargs = dict(
        alpha_exponent=config.alpha_exponent,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
    )
    h_c = float(compute_critical_head(theta, {"L": length}, **kwargs).H_c)
    h_c_credited = float(
        compute_critical_head(theta, {"L": length + lam_out}, **kwargs).H_c
    )
    return {
        "lambda_in_m": lam_in,
        "lambda_out_eff_m": lam_out,
        "seepage_length_m": length,
        "series_total_m": lam_out + length + lam_in,
        "entry_share_of_series": lam_out / (lam_out + length + lam_in),
        "r_e": r_e,
        "H_c_at_L_m": h_c,
        "H_c_at_L_eff_m": h_c_credited,
        "H_c_ratio": h_c_credited / h_c,
    }


# --------------------------------------------------------------------------- #
# Stage displacement of the ADR-0040 sustained-peak upper bound                 #
# --------------------------------------------------------------------------- #
def sustained_peak_scan(
    config: Config, stages: NDArray[np.float64], *, credit: float | None
) -> NDArray[np.float64]:
    """Exceedance probability of the ADR-0040 closed-form bound, per stage.

    ``gate AND H_erosion > H_c,trans`` on a held peak: the exact analytic limit
    of the transient branch under indefinitely sustained loading, so it upper
    bounds the finite-duration transient failure probability at every stage.
    Used for the stage displacement because under the credited arm the *actual*
    transition leaves the reachable grid at every section, and an indicator that
    is defined everywhere is the only one that can be displaced measurably.

    Evaluated through ``evaluate_batch_diagnostics`` on a short sustained
    record, so the gate latch, ``H_c`` and the crack term all come from the
    engine's own shared preamble rather than from a second implementation.
    """
    theta = _theta_for(config)
    seepage = _seepage_for(config)
    geometry = config.geometry.as_evaluator_dict()
    z_toe_m = float(geometry["z_toe"])
    d_bl_m = np.asarray(theta[:, 3], dtype=np.float64)
    crack = resolve_crack_resistance_factor(config.crack_resistance_factor)
    dt_s = float(config.timestepper.target_dt_seconds)

    probs = np.empty(stages.size, dtype=np.float64)
    for index, level in enumerate(stages):
        record = sustained_peak_record(
            float(level), dt_s=dt_s, scenario=config.scenario
        )
        diag = evaluate_batch_diagnostics(
            theta,
            record,
            geometry,
            seepage_length_samples=seepage,
            alpha_exponent=config.alpha_exponent,
            theta_repose_rad=config.theta_repose_rad,
            relative_density=config.relative_density_insitu,
            foreland_open=config.foreland_treatment == "open_entry",
            foreland_seepage_credit=credit,
        )
        gate_open = np.asarray(diag.heave_occurred, dtype=bool)
        h_erosion = (float(level) - z_toe_m) - crack * d_bl_m
        probs[index] = float(
            np.count_nonzero(gate_open & (h_erosion > diag.H_c_transient))
        ) / float(theta.shape[0])
    return probs


def _theta_for(config: Config) -> NDArray[np.float64]:
    """The run's own theta draw, argument for argument as ``run.py`` makes it.

    ``effective_marginal_specs()`` (not ``priors.to_marginal_specs()``) so an
    ADR-0048 prior-mean scenario would be honoured from the one shared
    definition; with no scenario set, which is production, the two agree.
    """
    return sample_theta(
        config.effective_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    ).theta_matrix


def _seepage_for(config: Config) -> NDArray[np.float64] | None:
    """The run's own stochastic L draw, through the public re-entry point.

    ``run.seepage_length_samples_for_config`` derives the seed from
    ``config.mc.seed`` through a ``SeedSequence`` salt, and its docstring
    requires consumers to call it rather than re-derive the recipe. Re-deriving
    it here would put the sustained-peak scan on a different L population from
    the sweeps it is compared against.
    """
    return seepage_length_samples_for_config(config)


def stage_displacement(config: Config, *, hwl: float, skip: bool) -> dict[str, Any]:
    """Displacement of the sustained-peak bound, baseline vs each arm."""
    if skip:
        return {"skipped": True}
    low = float(config.mc.conditioning_grid[0])
    stages = np.arange(low, hwl + SCAN_ABOVE_HWL_M + SCAN_STEP_M, SCAN_STEP_M)
    curves = {"baseline": sustained_peak_scan(config, stages, credit=None)}
    for label, phi in ARMS:
        curves[label] = sustained_peak_scan(config, stages, credit=phi)

    out: dict[str, Any] = {
        "indicator": (
            "ADR-0040 closed-form sustained-peak upper bound: gate AND "
            "H_erosion > H_c,trans on a held peak"
        ),
        "scan_step_m": SCAN_STEP_M,
        "scan_range_m_msl": [float(stages[0]), float(stages[-1])],
        "anchors": {},
    }
    for target in DISPLACEMENT_ANCHORS:
        base_stage = _crossing_stage(stages, curves["baseline"], target)
        entry: dict[str, Any] = {"baseline_stage_m_msl": base_stage, "arms": {}}
        for label, _ in ARMS:
            arm_stage = _crossing_stage(stages, curves[label], target)
            entry["arms"][label] = {
                "stage_m_msl": arm_stage,
                "displacement_m": (
                    None
                    if (arm_stage is None or base_stage is None)
                    else float(arm_stage - base_stage)
                ),
            }
        out["anchors"][f"p_{target:g}"] = entry
    return out


# --------------------------------------------------------------------------- #
# Per-arm comparison and the cancellation test                                 #
# --------------------------------------------------------------------------- #
def compare_arm(
    baseline: dict[str, Any], arm: FragilityResult, *, seed: int
) -> dict[str, Any]:
    """Per-level effect of one arm on BOTH branches, plus the rho interval."""
    base_static = baseline["failure_matrix_static"].astype(bool)
    base_trans = baseline["failure_matrix_trans"].astype(bool)
    arm_static = np.asarray(arm.failure_matrix_stat, dtype=bool)
    arm_trans = np.asarray(arm.failure_matrix_tran, dtype=bool)

    p_static = np.asarray(arm.P_f_static_raw, dtype=float)
    p_trans = np.asarray(arm.P_f_trans_raw, dtype=float)
    b_static = baseline["P_f_static_raw"]
    b_trans = baseline["P_f_trans_raw"]

    # The channel claim, checked rather than assumed. Unlike ADR-0049/0050 the
    # static column is EXPECTED to move; what must hold is the direction, since
    # a raised critical head can only remove failures, never create them.
    for name, base_col, arm_col in (
        ("static", base_static, arm_static),
        ("transient", base_trans, arm_trans),
    ):
        created = int(np.count_nonzero(arm_col & ~base_col))
        if created:
            raise AssertionError(
                f"the credited arm CREATED {created} {name} failures. A longer "
                "seepage length raises H_c for every realization, so it can only "
                "remove failures. A non-zero count means a channel exists that "
                "this study's reasoning does not know about. Refusing to report."
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
        entry: dict[str, Any] = {
            "stage_m_msl": float(baseline["grid"][index]),
            "n_fail_static_baseline": int(base_static[:, index].sum()),
            "n_fail_static_arm": int(arm_static[:, index].sum()),
            "n_fail_trans_baseline": int(base_trans[:, index].sum()),
            "n_fail_trans_arm": int(arm_trans[:, index].sum()),
            "static_cells_moved": int(
                np.count_nonzero(base_static[:, index] != arm_static[:, index])
            ),
            "trans_not_static_baseline": int(
                np.count_nonzero(base_trans[:, index] & ~base_static[:, index])
            ),
            "trans_not_static_arm": int(
                np.count_nonzero(arm_trans[:, index] & ~arm_static[:, index])
            ),
            "p_f_static_baseline": float(b_static[index]),
            "p_f_static_arm": float(p_static[index]),
            "p_f_trans_baseline": float(b_trans[index]),
            "p_f_trans_arm": float(p_trans[index]),
            "ratio_static": _ratio(float(p_static[index]), float(b_static[index])),
            "ratio_trans": _ratio(float(p_trans[index]), float(b_trans[index])),
            "min_cell_failures": cell_min,
        }
        entry["rho"] = (
            ratio_of_ratios_ci(counts, seed=seed + index)
            if cell_min >= RATIO_MIN_FAILURES
            else None
        )
        levels.append(entry)
    return {"levels": levels}


def run_section(
    label: str,
    spec: dict[str, str],
    *,
    reading: str,
    n_jobs: int,
    n_override: int | None,
    skip_run: bool,
    allow_unverified: bool,
    skip_displacement: bool,
) -> dict[str, Any]:
    """Gate the baseline, run both arms, and assemble the section record."""
    started = time.time()
    config_path = _config_path(spec["slug"], reading)
    config = Config.from_yaml(config_path)
    if config.foreland_seepage_credit is not None:
        raise ValueError(
            f"{label}: the committed config already carries a "
            "foreland_seepage_credit; this driver expects the production "
            "baseline, where the knob is off."
        )
    if n_override is not None:
        config = config.model_copy(
            update={"mc": config.mc.model_copy(update={"n_samples": n_override})}
        )

    stem = f"{spec['stem']}_historical_{reading}"
    production = _load_persisted(_production_path(spec["stem"], reading))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. the gate: knob explicitly off, bit-identical to production -------
    gate_path = OUT_DIR / f"{stem}_gate.h5"
    if not skip_run:
        print(
            f"[{label}] gate: baseline with the credit explicitly off ...", flush=True
        )
        gate = run_fragility_analysis(
            config.model_copy(update={"foreland_seepage_credit": None}),
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

    baseline = {
        "grid": np.asarray(gate.conditioning_grid, dtype=float),
        "P_f_static_raw": np.asarray(gate.P_f_static_raw, dtype=float),
        "P_f_trans_raw": np.asarray(gate.P_f_trans_raw, dtype=float),
        "failure_matrix_static": np.asarray(gate.failure_matrix_stat),
        "failure_matrix_trans": np.asarray(gate.failure_matrix_tran),
    }

    # --- 2. the two arms ------------------------------------------------------
    arms: dict[str, Any] = {}
    for arm_label, phi in ARMS:
        arm_path = OUT_DIR / f"{stem}_{arm_label}.h5"
        if not skip_run:
            print(f"[{label}] arm {arm_label}: phi = {phi:.2f} ...", flush=True)
            arm = run_fragility_analysis(
                config.model_copy(update={"foreland_seepage_credit": phi}),
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
            "phi": float(phi),
            "file": str(arm_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            **compare_arm(baseline, arm, seed=abs(hash((label, arm_label))) % 100000),
        }

    # --- 3. anchors -----------------------------------------------------------
    hwl = float(config.geometry.HWL)
    anchors = anchor_indices(baseline["grid"], baseline["P_f_trans_raw"], hwl)
    at_anchors: dict[str, Any] = {}
    for name, index in anchors.items():
        at_anchors[name] = {
            "stage_m_msl": float(baseline["grid"][index]),
            "p_f_static_baseline": float(baseline["P_f_static_raw"][index]),
            "p_f_trans_baseline": float(baseline["P_f_trans_raw"][index]),
            "arms": {
                a: {
                    key: arms[a]["levels"][index][key]
                    for key in (
                        "n_fail_static_arm",
                        "n_fail_trans_arm",
                        "p_f_static_arm",
                        "p_f_trans_arm",
                        "ratio_static",
                        "ratio_trans",
                        "rho",
                    )
                }
                for a, _ in ARMS
            },
        }

    # --- 4. the design-level statement, stated as counts ---------------------
    design_index = anchors["design_hwl"]
    design = {
        "stage_m_msl": float(baseline["grid"][design_index]),
        "n_samples": int(config.mc.n_samples),
        "baseline": {
            "n_fail_static": int(
                baseline["failure_matrix_static"][:, design_index].sum()
            ),
            "n_fail_trans": int(
                baseline["failure_matrix_trans"][:, design_index].sum()
            ),
        },
        "arms": {
            a: {
                "n_fail_static": arms[a]["levels"][design_index]["n_fail_static_arm"],
                "n_fail_trans": arms[a]["levels"][design_index]["n_fail_trans_arm"],
            }
            for a, _ in ARMS
        },
    }

    # --- 5. the cancellation verdict -----------------------------------------
    cancellation: dict[str, Any] = {}
    for arm_label, _ in ARMS:
        levels = arms[arm_label]["levels"]
        evaluated = [entry for entry in levels if entry["rho"] is not None]
        resolved = [entry for entry in evaluated if entry["rho"]["resolved"]]
        rhos = [entry["rho"]["rho"] for entry in resolved]
        above = [value for value in rhos if value > 1.0]
        cancellation[arm_label] = {
            "levels_evaluated": len(evaluated),
            "levels_resolved": len(resolved),
            "resolved_rho_min": min(rhos) if rhos else None,
            "resolved_rho_max": max(rhos) if rhos else None,
            "resolved_levels_with_rho_above_one": len(above),
            "static_cells_moved_total": sum(
                entry["static_cells_moved"] for entry in levels
            ),
            "trans_not_static_rows_baseline": sum(
                entry["trans_not_static_baseline"] for entry in levels
            ),
            "trans_not_static_rows_arm": sum(
                entry["trans_not_static_arm"] for entry in levels
            ),
        }

    # --- 6. stage displacement of the sustained-peak bound --------------------
    displacement = stage_displacement(config, hwl=hwl, skip=skip_displacement)

    return {
        "section": label,
        "reading": reading,
        "config": str(config_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "production_file": str(
            _production_path(spec["stem"], reading).relative_to(REPO_ROOT)
        ).replace("\\", "/"),
        "cross_section_id": config.cross_section_id,
        "d70_interpretation": config.priors.d70_interpretation,
        "n_samples": int(config.mc.n_samples),
        "design_hwl_m_msl": hwl,
        "attainable_note": (
            "Stages above the section's attainable maximum are hypothetical "
            "(ADR-0024); a displacement of an indicator is reported, never an "
            "attainable stage."
        ),
        "z_toe_m_msl": float(config.geometry.z_toe),
        "gate_status": gate_status,
        "prior_mean_baseline": prior_mean_baseline(config),
        "grid_m_msl": baseline["grid"].tolist(),
        "anchor_indices": anchors,
        "at_anchors": at_anchors,
        "design_level": design,
        "arms": arms,
        "cancellation": cancellation,
        "stage_displacement": displacement,
        "elapsed_s": round(time.time() - started, 1),
    }


def preregistration_digest() -> str:
    """Digest of the frozen prediction, so it cannot be edited after the fact.

    The text is decoded and re-encoded rather than hashed as raw bytes: this
    repository is checked out with line-ending translation, so a byte digest
    would depend on the checkout rather than on the content (the lesson
    ``scripts/canonical_shape_sensitivity_study.py`` already records).
    """
    return hashlib.sha256(
        PREREG.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()


def prediction_outcomes(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Score the frozen predictions against what was measured.

    Derived from the section records, never hand-written, so the outcome cannot
    drift from the numbers beside it. See
    ``docs/decisions/adr0052-foreland-credit-prereg.md`` for the statements.
    """
    static_moved = {
        s["section"]: max(
            c["static_cells_moved_total"] for c in s["cancellation"].values()
        )
        for s in sections
    }
    resolved = above = evaluated = 0
    max_rho: dict[str, float] = {}
    for s in sections:
        best = 0.0
        for c in s["cancellation"].values():
            evaluated += c["levels_evaluated"]
            resolved += c["levels_resolved"]
            above += c["resolved_levels_with_rho_above_one"]
            if c["resolved_rho_max"] is not None:
                best = max(best, float(c["resolved_rho_max"]))
        max_rho[s["section"]] = best
    design_all_zero = all(
        arm["n_fail_static"] == 0 and arm["n_fail_trans"] == 0
        for s in sections
        for name, arm in s["design_level"]["arms"].items()
        if name == "credit_full"
    )
    kappa_order = [
        s["section"]
        for s in sorted(
            sections,
            key=lambda x: x["prior_mean_baseline"]["H_c_ratio"],
            reverse=True,
        )
    ]
    rho_order = sorted(max_rho, key=lambda k: max_rho[k], reverse=True)
    return {
        "P1": {
            "statement": "neither branch is invariant; the static matrix moves",
            "held": all(v > 0 for v in static_moved.values()),
            "static_cells_moved_max_per_section": static_moved,
        },
        "P2": {
            # Held only if EVERY level with enough failures to evaluate came
            # back with an interval excluding unity: one evaluated-but-
            # unresolved level would be a level where cancellation could not
            # be ruled out, and the prediction would be weakened there.
            "statement": "the bracket does not cancel; rho != 1 where resolved",
            "held": resolved > 0 and resolved == evaluated,
            "levels_evaluated": evaluated,
            "levels_resolved": resolved,
        },
        "P3": {
            "statement": "rho > 1: the credit widens the static-to-transient bias",
            "held": resolved > 0 and above == resolved,
            "levels_resolved": resolved,
            "levels_with_rho_above_one": above,
        },
        "P4": {
            "statement": "the per-section displacement orders by kappa",
            "held": kappa_order == rho_order,
            "kappa_order": kappa_order,
            "max_rho_order": rho_order,
            "max_rho": max_rho,
        },
        "P5": {
            "statement": (
                "rho unresolvable at most levels; the design level a pair of "
                "zero counts under the full credit"
            ),
            "held": design_all_zero,
            "design_level_all_zero_under_full_credit": design_all_zero,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sections", nargs="*", default=list(SECTIONS))
    parser.add_argument("--reading", choices=("matrix", "bulk"), default="matrix")
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--n", type=int, default=None, help="Pilot sample size.")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--allow-unverified", action="store_true")
    parser.add_argument("--skip-displacement", action="store_true")
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
                reading=args.reading,
                n_jobs=args.n_jobs,
                n_override=args.n,
                skip_run=args.skip_run,
                allow_unverified=args.allow_unverified,
                skip_displacement=args.skip_displacement,
            )
        )

    payload = {
        "adr": "0052",
        "reading": args.reading,
        "description": (
            "Companion sensitivity: the foreland seepage-length credit of "
            "TR Zandmeevoerende Wellen (1999) section 4.4.2, which the "
            "production baseline declines. When credited, the Sellmeijer "
            "critical head is evaluated at L_eff = L + phi * lambda_out_eff "
            "while the traverse length, the Z_transient = L - l_e criterion, "
            "the Eq. (5) rate denominator and r_e all keep the physical "
            "under-levee L. H_c is single-source, so BOTH branches move. "
            "Production baseline unchanged; baseline files untouched."
        ),
        "bracket": {
            "arms": {name: phi for name, phi in ARMS},
            "provenance": (
                "TR Zandmeevoerende Wellen (1999) section 4.4.2: a foreland "
                "displaces the theoretical entry point riverward by "
                "L'_v = lambda * tanh(L_v / lambda), the same tanh section "
                "4.4.1 gives lambda_out_eff, and that increase in seepage "
                "length 'mag in rekening worden gebracht' in Sellmeijer's rule "
                "as in Bligh's and Lane's. The permission is optional, so "
                "declining it is a recognised conservative simplification and "
                "stays the production baseline. phi = 1.0 is exactly that "
                "displacement; phi = 0.5 is a partial credit included so the "
                "response is shown to be graded."
            ),
        },
        "channel_reading": {
            "shared_with_static": [
                "the Sellmeijer critical head H_c, which is single-source and "
                "feeds both the static comparator and the transient H_eq anchor"
            ],
            "transient_only": [],
            "not_reached": [
                "the critical pipe length l_c of Eq. (13)",
                "the traverse length and the Z_transient = L - l_e criterion",
                "the L in the Eq. (5) rate denominator",
                "the L in r_e and the leakage lengths themselves",
                "the erosion head H_erosion and the uplift/heave gate",
            ],
        },
        "ratio_statistic": (
            "ADR-0047 section 4.5 paired bootstrap over the 16 joint pattern "
            "counts, 2000 replicates, null pinned at rho = 1.0, imported from "
            "scripts/dem_cross_section_study.py rather than re-implemented."
        ),
        "baseline_bit_identity": {
            s["section"]: {
                "status": s["gate_status"],
                "static_matches": s["gate_status"] == "bit_identical",
                "transient_matches": s["gate_status"] == "bit_identical",
            }
            for s in sections
        },
        "static_branch_moved": {
            s["section"]: max(
                c["static_cells_moved_total"] for c in s["cancellation"].values()
            )
            for s in sections
        },
        "prediction_outcomes": prediction_outcomes(sections),
        "prior_mean_baseline": {
            s["section"]: s["prior_mean_baseline"] for s in sections
        },
        "sections": sections,
        "total_runtime_s": round(time.time() - started, 1),
    }
    if PREREG.is_file():
        payload["preregistration"] = {
            "file": str(PREREG.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": preregistration_digest(),
        }

    suffix = "" if args.reading == "matrix" else f"-{args.reading}"
    json_out = (
        REPO_ROOT
        / "docs"
        / "decisions"
        / f"adr0052-foreland-credit-companion{suffix}.json"
    )
    if args.n is not None:
        print("\nPilot run (--n): evidence record NOT written.")
        print(json.dumps(_compact(payload["sections"][0]["cancellation"]), indent=2))
        return 0

    json_out.write_text(
        json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {json_out.relative_to(REPO_ROOT)}")
    for section in sections:
        design = section["design_level"]
        print(
            f"  {section['section']}: gate {section['gate_status']}; "
            f"design {design['stage_m_msl']:.2f} m "
            f"baseline {design['baseline']['n_fail_static']}/"
            f"{design['baseline']['n_fail_trans']} -> full credit "
            f"{design['arms']['credit_full']['n_fail_static']}/"
            f"{design['arms']['credit_full']['n_fail_trans']} "
            f"(static/transient of {design['n_samples']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
