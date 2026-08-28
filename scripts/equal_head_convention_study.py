"""ADR-0051 companion: the equal-head-convention comparison (gross vs gross).

Pre-registration and decision: ``docs/decisions/0051-crack-resistance-factor-\
equal-head-convention.md``.
Result of record: ``docs/decisions/equal-head-convention-study.md``.
Evidence: ``docs/decisions/adr0051-equal-head-convention.json``.

Since ADR-0027/0028 the two piping heads are both measured on the raw outer
level against the same landside-toe datum, and neither carries ``r_e``. What is
left between them is one term: the Pol SIE 2024 Eq. (6) crack-resistance loss
``0.3*D_bl``, which the transient erosion driver carries and the static
Sellmeijer comparator does not. Sellmeijer (2011) contains no such term; it is a
Dutch assessment-rule convention Pol adopted by citation. This driver removes it
from the transient side (``crack_resistance_factor = 0.0``, ADR-0051), so both
limit states run on one head convention, and measures what is left.

What it does, per matrix section:

1. **Gate.** Re-runs the section's committed YAML with
   ``crack_resistance_factor=None`` set *explicitly* and asserts both failure
   matrices are bit-identical to the persisted production sweep. One run
   discharges two obligations: the knob is inert when off, and the baseline this
   study compares against has not drifted.
2. **The equal-convention arm.** Re-runs the same config at factor 0. Same seed,
   same theta, same L draw, same grid, same hydrographs: the arm is coupled to
   the baseline by common random numbers row for row, which is what makes the
   paired bootstrap exact.
3. **Consistency gates**, all three reported rather than assumed:
   (i) the static failure matrix is bit-identical to production -- the knob is
   transient-erosion-only by construction, and the driver refuses to report if a
   single static cell moves;
   (ii) the gross-head transient failure set nests inside the static set at
   every level, up to forward-Euler barrier-jump rows (ADR-0030), which are
   counted; and the production transient set nests inside the gross-head one,
   since removing a head loss can only help a pipe;
   (iii) the sustained-peak limit of the gross-head transient equals
   ``C0 and gate`` in closed form (ADR-0040 Decision 2 with the crack term
   removed), checked against a 64-day hold at the design and top anchors.
4. **Per-level table** of ``B_eq = P_static / P_trans,gross`` with its paired
   interval, and of ``dbeta_eq = beta_trans,gross - beta_static`` with a paired
   bootstrap interval; the per-branch beta intervals are the monotone image of
   the exact Clopper-Pearson interval on the raw count (campaign plan D1).

The statistics kernel is **imported, never re-implemented**: the paired
bootstrap and the ``bias_ratio`` estimator with its pre-registered R1/R2
criteria come from ``scripts/hwl_bias_resolution.py`` (ADR-0040), the same
route ``epistemic_bracket_synthesis`` and ``critical_length_bracket_study``
already use for their kernels.

Usage (repo root, venv active)::

    python scripts/equal_head_convention_study.py n1e5
    python scripts/equal_head_convention_study.py n1e5 --sections KP62.0
    python scripts/equal_head_convention_study.py n1e6
    python scripts/equal_head_convention_study.py report

``n1e6`` evaluates only the two branches (not the ten-comparator ladder) at the
design anchors and their neighbours, on the *same* seed recipe as the persisted
N = 1e6 ladder, and gates on reproducing its static and transient counts
exactly.
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
from joblib import Parallel, delayed
from numpy.typing import NDArray
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.evaluator import (  # noqa: E402
    evaluate_batch,
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.fragility import (  # noqa: E402
    FragilityResult,
    save_raw_failure_payload,
)
from bep_reliability_engine.gap_decomposition import (  # noqa: E402
    sustained_peak_record,
)
from bep_reliability_engine.run import (  # noqa: E402
    conditioning_hydrographs_for_config,
    model_factor_samples_for_config,
    run_fragility_analysis,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_theta  # noqa: E402


def _load_module(name: str):
    """Import a sibling driver for its kernels (the house ``importlib`` route)."""
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_HWL = _load_module("hwl_bias_resolution")
_CLB = _load_module("critical_length_bracket_study")

bias_ratio = _HWL.bias_ratio
paired_column_means_bootstrap = _HWL.paired_column_means_bootstrap
cp_interval = _HWL.cp_interval
ratio_payload = _HWL.ratio_payload
stable_seed = _HWL._stable_seed
anchor_indices = _CLB.anchor_indices

#: The equal-head-convention arm: Eq. (6)'s coefficient set to zero, so the
#: erosion driver is the static comparator's own gross head h(t) - z_toe.
GROSS_HEAD_FACTOR = 0.0

#: Bootstrap settings, inherited from the ADR-0040 kernel this study reuses.
BOOTSTRAP_REPLICATES = 10_000

#: A level's ratio/dbeta interval is reported only above this failure count in
#: both branches (the ADR-0047 convention, deliberately low).
MIN_ROWS_FOR_INTERVAL = 10

#: Sustained-peak hold used for gate (iii). ADR-0040 recorded the analytic
#: limit as ODE-exact at 64 days; the same horizon is used here.
SUSTAINED_HOLD_DAYS = 64.0

SECTIONS: dict[str, dict[str, str]] = {
    "KP57.4": {
        "config": "configs/kp57_4_historical_matrix.yaml",
        "production": "results/tokachi_kp57.4_historical_matrix.h5",
        "stem": "tokachi_kp57.4_historical_matrix",
        "ladder_key": "kp57_4",
    },
    "KP58.8": {
        "config": "configs/kp58_8_historical_matrix.yaml",
        "production": "results/tokachi_kp58.8_historical_matrix.h5",
        "stem": "tokachi_kp58.8_historical_matrix",
        "ladder_key": None,
    },
    "KP60.0": {
        "config": "configs/kp60_0_historical_matrix.yaml",
        "production": "results/tokachi_kp60.0_historical_matrix.h5",
        "stem": "tokachi_kp60.0_historical_matrix",
        "ladder_key": None,
    },
    "KP62.0": {
        "config": "configs/kp62_0_historical_matrix.yaml",
        "production": "results/tokachi_kp62.0_historical_matrix.h5",
        "stem": "tokachi_kp62.0_historical_matrix",
        "ladder_key": "kp62_0",
    },
}

#: N = 1e6 scope: the design anchor (A1), the nearest grid level (A2) and the
#: neighbouring levels the persisted 1e6 campaign already carries, so the new
#: gross-head transient pairs against existing static counts row for row.
BIG_N = 1_000_000
BIG_LEVELS: dict[str, tuple[float, ...]] = {
    "KP62.0": (46.39, 46.50, 47.00, 48.00, 50.50),
    "KP57.4": (39.21, 39.25, 39.50, 40.00, 43.25),
}
#: The gate values, read from the persisted ladder before this study existed.
BIG_STATIC_GATE: dict[tuple[str, float], int] = {
    ("KP62.0", 46.39): 1696,
    ("KP57.4", 39.21): 1132,
}

OUT_DIR = REPO_ROOT / "results" / "equal_head_convention"
JSON_OUT = REPO_ROOT / "docs" / "decisions" / "adr0051-equal-head-convention.json"


# --------------------------------------------------------------------------- #
# beta re-expression (campaign plan D1)                                        #
# --------------------------------------------------------------------------- #
def beta_of(p: float) -> float:
    """beta = -Phi^-1(p). Infinite at p = 0 (no failures) and at p = 1."""
    if not np.isfinite(p):
        return float("nan")
    if p <= 0.0:
        return float("inf")
    if p >= 1.0:
        return float("-inf")
    return float(-norm.ppf(p))


def beta_block(k: int, n: int) -> dict[str, Any]:
    """beta with the monotone image of the exact Clopper-Pearson interval.

    beta is strictly decreasing in p, so mapping the CP interval endpoints and
    swapping them is exact: no new statistical machinery, and the interval is
    the same one the raw-tail fragility presentation already uses (ADR-0024).
    A zero-failure level gives a one-sided lower bound on beta, reported as
    ``inf`` with a finite ``ci_lo``.
    """
    p = k / n
    lo, hi = cp_interval(k, n)
    return {
        "k": int(k),
        "n": int(n),
        "p": float(p),
        "p_cp": [float(lo), float(hi)],
        "beta": beta_of(p),
        "beta_ci": [beta_of(hi), beta_of(lo)],
        "one_sided": bool(k == 0),
    }


def delta_beta_block(
    static_col: NDArray[np.bool_],
    trans_col: NDArray[np.bool_],
    *,
    seed: int,
    n_replicates: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    """dbeta = beta_transient - beta_static with a paired bootstrap interval.

    One row resample per replicate feeds both columns, which is the whole point:
    the two branches are evaluated on the same realizations under the ADR-0002
    shared-sample contract, and the transient set nests inside the static one,
    so the interval reflects the discordant rows rather than two independent
    binomials. Kernel imported from ``scripts/hwl_bias_resolution.py``.
    """
    k_s = int(np.count_nonzero(static_col))
    k_t = int(np.count_nonzero(trans_col))
    n = int(static_col.size)
    point = beta_of(k_t / n) - beta_of(k_s / n)
    entry: dict[str, Any] = {
        "delta_beta": point,
        "delta_beta_ci": None,
        "reportable": bool(
            min(k_s, k_t) >= MIN_ROWS_FOR_INTERVAL and n - max(k_s, k_t) > 0
        ),
    }
    if not entry["reportable"]:
        return entry
    means = paired_column_means_bootstrap(
        [np.asarray(static_col, dtype=bool), np.asarray(trans_col, dtype=bool)],
        n_replicates=n_replicates,
        seed=seed,
    )
    reps = np.array(
        [beta_of(float(t)) - beta_of(float(s)) for s, t in means], dtype=np.float64
    )
    finite = reps[np.isfinite(reps)]
    if finite.size == 0:
        return entry
    lo, hi = np.percentile(finite, [2.5, 97.5])
    entry["delta_beta_ci"] = [float(lo), float(hi)]
    entry["bootstrap_finite_fraction"] = float(finite.size / reps.size)
    return entry


# --------------------------------------------------------------------------- #
# Shared helpers                                                               #
# --------------------------------------------------------------------------- #
def _load_persisted(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        return {
            "grid": np.asarray(handle["conditioning_grid"], dtype=float),
            "failure_matrix_static": np.asarray(
                handle["failure_matrix_static"], dtype=bool
            ),
            "failure_matrix_trans": np.asarray(
                handle["failure_matrix_trans"], dtype=bool
            ),
        }


def _assert_bit_identical(label: str, fresh, persisted: dict) -> None:
    """Gate on the WHOLE failure matrices, not the column means."""
    for name, matrix in (
        ("static", fresh.failure_matrix_stat),
        ("trans", fresh.failure_matrix_tran),
    ):
        if not np.array_equal(
            np.asarray(matrix, dtype=bool), persisted[f"failure_matrix_{name}"]
        ):
            raise AssertionError(
                f"{label}: fresh {name} failure matrix differs from the persisted "
                "production sweep. Either crack_resistance_factor=None is not "
                "bit-identical, or the baseline has drifted. Refusing to report "
                "a sensitivity either way."
            )


def _compact(obj: Any, sig: int = 6) -> Any:
    """Round every float in a nested payload to ``sig`` significant digits."""
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return str(obj)
        return float(f"%.{sig}g" % obj)
    if isinstance(obj, dict):
        return {key: _compact(value, sig) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_compact(value, sig) for value in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return _compact(float(obj), sig)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _theta_for(config: Config) -> NDArray[np.float64]:
    """The config's own M2 draw, by exactly the recipe run.py uses."""
    return sample_theta(
        config.effective_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    ).theta_matrix


def _eval_settings(config: Config, crack: float | None) -> dict[str, Any]:
    """The run-constant M8 keywords, threaded exactly as ``run.py`` threads them."""
    return dict(
        l_ini=0.0,
        seepage_length_samples=seepage_length_samples_for_config(config),
        alpha_exponent=config.alpha_exponent,
        alpha_exponent_transient=config.alpha_exponent_transient,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        foreland_open=config.foreland_treatment == "open_entry",
        progression_backend="numpy",
        model_factor_samples=model_factor_samples_for_config(config),
        critical_length_factor=config.critical_length_factor,
        toe_gradient_relief_factor=config.toe_gradient_relief_factor,
        crack_resistance_factor=crack,
    )


def _eval_level(index, record, theta, geometry, settings):
    return index, evaluate_batch(theta, record, geometry, **settings)


# --------------------------------------------------------------------------- #
# Per-level table                                                              #
# --------------------------------------------------------------------------- #
def level_table(
    grid: NDArray[np.float64],
    static: NDArray[np.bool_],
    trans_production: NDArray[np.bool_],
    trans_gross: NDArray[np.bool_],
    *,
    label: str,
) -> list[dict[str, Any]]:
    """One row per conditioning level: counts, B, beta, dbeta, nesting."""
    n = static.shape[0]
    rows: list[dict[str, Any]] = []
    for index in range(grid.size):
        s = static[:, index]
        tp = trans_production[:, index]
        tg = trans_gross[:, index]
        seed = stable_seed(f"{label}|{grid[index]:.4f}")
        entry: dict[str, Any] = {
            "stage_m_msl": float(grid[index]),
            "n_samples": int(n),
            "k_static": int(s.sum()),
            "k_trans_production": int(tp.sum()),
            "k_trans_gross": int(tg.sum()),
            # (ii) nesting diagnostics, counted rather than assumed.
            "gross_not_static_rows": int(np.count_nonzero(tg & ~s)),
            "production_not_static_rows": int(np.count_nonzero(tp & ~s)),
            "production_not_gross_rows": int(np.count_nonzero(tp & ~tg)),
            "beta_static": beta_block(int(s.sum()), n),
            "beta_trans_production": beta_block(int(tp.sum()), n),
            "beta_trans_gross": beta_block(int(tg.sum()), n),
        }
        for name, column in (("production", tp), ("eq", tg)):
            est = bias_ratio(
                float(grid[index]),
                s,
                column,
                n_replicates=BOOTSTRAP_REPLICATES,
                seed=seed,
            )
            entry[f"B_{name}"] = ratio_payload(est)
            entry[f"delta_beta_{name}"] = delta_beta_block(s, column, seed=seed)
        rows.append(entry)
    return rows


def sustained_peak_check(
    config: Config,
    theta: NDArray[np.float64],
    levels: list[float],
    *,
    n_jobs: int,
) -> list[dict[str, Any]]:
    """Gate (iii): the closed-form sustained-peak limit of the gross-head arm.

    ADR-0040 Decision 2 gives the sustained-peak indicator as
    ``gate and (H_erosion > H_c,trans)``. With the crack term removed
    ``H_erosion`` is the static comparator's own gross head, so the limit is
    exactly ``C0 and gate``. A finite hold approaches that from below (marginal
    rows need the longest to traverse), so a residual disagreement must be
    one-sided: analytic True where the finite hold has not yet breached.
    """
    geometry = config.geometry.as_evaluator_dict()
    dt_s = float(
        config.timestepper.target_dt_seconds
        if config.timestepper.target_dt_seconds is not None
        else 3600.0
    )
    n_steps = int(SUSTAINED_HOLD_DAYS * 86400.0 / dt_s)
    settings = _eval_settings(config, GROSS_HEAD_FACTOR)

    def _one(level: float) -> dict[str, Any]:
        record = sustained_peak_record(
            level, dt_s=dt_s, n_steps=n_steps, scenario=config.scenario
        )
        diagnostics = evaluate_batch_diagnostics(theta, record, geometry, **settings)
        gate = np.asarray(diagnostics.heave_occurred, dtype=bool)
        static = np.asarray(diagnostics.failure_static, dtype=bool)
        observed = np.asarray(diagnostics.failure_trans, dtype=bool)
        analytic = static & gate
        return {
            "stage_m_msl": float(level),
            "hold_days": SUSTAINED_HOLD_DAYS,
            "n_steps": n_steps,
            "k_analytic_c0_and_gate": int(analytic.sum()),
            "k_observed_finite_hold": int(observed.sum()),
            "analytic_not_observed": int(np.count_nonzero(analytic & ~observed)),
            "observed_not_analytic": int(np.count_nonzero(observed & ~analytic)),
            "identical": bool(np.array_equal(analytic, observed)),
        }

    return list(Parallel(n_jobs=n_jobs)(delayed(_one)(lv) for lv in levels))


def sustained_dt_ladder(
    label: str, spec: dict[str, str], level_m: float, *, divisors=(1, 2, 4, 8)
) -> dict[str, Any]:
    """Diagnose a sustained-peak mismatch as a forward-Euler barrier jump.

    A row that breaches under a finite hold while the closed form says it must
    stall is the ADR-0030 signature: one Euler step clears the ``H_eq`` maximum
    at ``l_c`` that a continuous trajectory could never reach. The
    discriminating experiment is the ADR-0039 timestep ladder on that row
    alone -- a genuine failure survives refinement, an integration artifact
    does not. Run on the offending rows only, so it is cheap.
    """
    config = Config.from_yaml(REPO_ROOT / spec["config"]).model_copy(
        update={"crack_resistance_factor": GROSS_HEAD_FACTOR}
    )
    theta = _theta_for(config)
    lengths = seepage_length_samples_for_config(config)
    geometry = config.geometry.as_evaluator_dict()
    dt_s = float(config.timestepper.target_dt_seconds)
    n_steps = int(SUSTAINED_HOLD_DAYS * 86400.0 / dt_s)
    settings = _eval_settings(config, GROSS_HEAD_FACTOR)

    record = sustained_peak_record(
        level_m, dt_s=dt_s, n_steps=n_steps, scenario=config.scenario
    )
    diagnostics = evaluate_batch_diagnostics(theta, record, geometry, **settings)
    analytic = np.asarray(diagnostics.failure_static, dtype=bool) & np.asarray(
        diagnostics.heave_occurred, dtype=bool
    )
    observed = np.asarray(diagnostics.failure_trans, dtype=bool)
    offenders = np.flatnonzero(observed & ~analytic)

    rows: list[dict[str, Any]] = []
    raw_head = float(level_m) - float(geometry["z_toe"])
    for j in offenders:
        row_geometry = dict(geometry)
        if lengths is not None:
            row_geometry["L"] = float(lengths[j])
        ladder = []
        for divisor in divisors:
            fine = sustained_peak_record(
                level_m,
                dt_s=dt_s / divisor,
                n_steps=n_steps * divisor,
                scenario=config.scenario,
            )
            result = evaluate_realization(
                theta[j],
                fine,
                row_geometry,
                alpha_exponent=config.alpha_exponent,
                theta_repose_rad=config.theta_repose_rad,
                relative_density=config.relative_density_insitu,
                crack_resistance_factor=GROSS_HEAD_FACTOR,
            )
            ladder.append(
                {
                    "dt_s": dt_s / divisor,
                    "l_e_m": float(result.l_e_final),
                    "breach": bool(result.failure_trans),
                }
            )
        rows.append(
            {
                "row_index": int(j),
                "seepage_length_m": float(row_geometry["L"]),
                "H_c_m": float(diagnostics.H_c[j]),
                "l_c_m": float(diagnostics.l_c[j]),
                "raw_head_m": raw_head,
                "raw_head_minus_H_c_m": raw_head - float(diagnostics.H_c[j]),
                "C_e": float(theta[j, 6]),
                "k_aq_mps": float(theta[j, 0]),
                "D_bl_m": float(theta[j, 3]),
                "dt_ladder": ladder,
                "resolves_on_refinement": bool(
                    ladder[0]["breach"] and not any(e["breach"] for e in ladder[1:])
                ),
            }
        )
    return {
        "section": label,
        "stage_m_msl": float(level_m),
        "n_samples": int(config.mc.n_samples),
        "offending_rows": rows,
        "verdict": (
            "forward-Euler barrier jump (ADR-0030), removed by refinement"
            if rows and all(r["resolves_on_refinement"] for r in rows)
            else ("no offending row found" if not rows else "SURVIVES REFINEMENT")
        ),
    }


# --------------------------------------------------------------------------- #
# Stage: N = 1e5, four sections, full production grid                          #
# --------------------------------------------------------------------------- #
def run_section_n1e5(
    label: str,
    spec: dict[str, str],
    *,
    n_jobs: int,
    skip_run: bool,
    skip_sustained: bool,
) -> dict[str, Any]:
    started = time.time()
    config = Config.from_yaml(REPO_ROOT / spec["config"])
    if config.crack_resistance_factor is not None:
        raise ValueError(
            f"{label}: the committed config already carries a "
            "crack_resistance_factor; this driver expects the production "
            "baseline, where the knob is off."
        )
    production = _load_persisted(REPO_ROOT / spec["production"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gate_path = OUT_DIR / f"{spec['stem']}_gate.h5"
    gross_path = OUT_DIR / f"{spec['stem']}_gross.h5"

    if not skip_run:
        print(f"[{label}] gate: baseline with the knob explicitly off ...", flush=True)
        gate = run_fragility_analysis(
            config.model_copy(update={"crack_resistance_factor": None}),
            n_jobs=n_jobs,
            progress=True,
            output_path=gate_path,
            overwrite=True,
        )
        print(
            f"[{label}] arm: crack_resistance_factor = 0 (gross head) ...", flush=True
        )
        gross = run_fragility_analysis(
            config.model_copy(update={"crack_resistance_factor": GROSS_HEAD_FACTOR}),
            n_jobs=n_jobs,
            progress=True,
            output_path=gross_path,
            overwrite=True,
        )
    else:
        gate = FragilityResult.load(gate_path)
        gross = FragilityResult.load(gross_path)

    # (i) the knob is inert when off, and the baseline has not drifted.
    _assert_bit_identical(f"{label} gate", gate, production)
    # (i) again, and this is the structural claim: with the knob ON the static
    # matrix must STILL be bit-identical to production.
    if not np.array_equal(
        np.asarray(gross.failure_matrix_stat, dtype=bool),
        production["failure_matrix_static"],
    ):
        moved = int(
            np.count_nonzero(
                np.asarray(gross.failure_matrix_stat, dtype=bool)
                != production["failure_matrix_static"]
            )
        )
        raise AssertionError(
            f"{label}: the static failure matrix moved in {moved} cells under "
            "the gross-head arm. The crack coefficient must not reach the "
            "static comparator; a non-zero count means a channel exists that "
            "this study's reasoning does not know about. Refusing to report."
        )

    grid = np.asarray(gate.conditioning_grid, dtype=float)
    if not np.array_equal(np.asarray(gross.conditioning_grid, dtype=float), grid):
        raise RuntimeError(f"{label}: arm grid differs from the gate grid")

    static = production["failure_matrix_static"]
    trans_production = production["failure_matrix_trans"]
    trans_gross = np.asarray(gross.failure_matrix_tran, dtype=bool)
    levels = level_table(
        grid, static, trans_production, trans_gross, label=f"{label}|n1e5"
    )

    hwl = float(config.geometry.HWL)
    p_trans = trans_production.mean(axis=0)
    anchors = anchor_indices(grid, p_trans, hwl)

    sustained: list[dict[str, Any]] = []
    if not skip_sustained:
        want = sorted(
            {float(grid[anchors["design_hwl"]]), float(grid[anchors["grid_top"]])}
        )
        print(f"[{label}] sustained-peak closed form at {want} ...", flush=True)
        sustained = sustained_peak_check(
            config.model_copy(update={"crack_resistance_factor": GROSS_HEAD_FACTOR}),
            _theta_for(config),
            want,
            n_jobs=min(n_jobs if n_jobs > 0 else 2, len(want)),
        )

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
        "gate_status": "bit_identical",
        "static_invariance": "exact",
        "artifacts": {
            "gate": str(gate_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "gross": str(gross_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        },
        "grid_m_msl": grid.tolist(),
        "anchor_indices": anchors,
        "levels": levels,
        "nesting": {
            "gross_not_static_rows_total": sum(
                row["gross_not_static_rows"] for row in levels
            ),
            "production_not_static_rows_total": sum(
                row["production_not_static_rows"] for row in levels
            ),
            "production_not_gross_rows_total": sum(
                row["production_not_gross_rows"] for row in levels
            ),
        },
        "sustained_peak": sustained,
        "elapsed_s": round(time.time() - started, 1),
    }


# --------------------------------------------------------------------------- #
# Stage: N = 1e6 at the design anchors, two sections                           #
# --------------------------------------------------------------------------- #
def run_section_n1e6(
    label: str, spec: dict[str, str], *, n_jobs: int, skip_run: bool
) -> dict[str, Any]:
    started = time.time()
    base = Config.from_yaml(REPO_ROOT / spec["config"])
    levels = tuple(sorted(BIG_LEVELS[label]))
    config = base.model_copy(
        update={
            "mc": base.mc.model_copy(
                update={"n_samples": BIG_N, "conditioning_grid": levels}
            )
        }
    )
    ladder_path = (
        REPO_ROOT
        / "results"
        / "hwl_bias_resolution"
        / f"ladder_{spec['ladder_key']}_n{BIG_N}.h5"
    )
    out_path = OUT_DIR / f"{spec['stem']}_n{BIG_N}.h5"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()

    if not skip_run:
        records = conditioning_hydrographs_for_config(config)
        columns: dict[str, NDArray[np.bool_]] = {}
        for arm, crack in (("gate", None), ("gross", GROSS_HEAD_FACTOR)):
            print(
                f"[{label}] N = {BIG_N:,} arm {arm} over {len(levels)} levels ...",
                flush=True,
            )
            settings = _eval_settings(config, crack)
            out = Parallel(n_jobs=n_jobs)(
                delayed(_eval_level)(i, records[i], theta, geometry, settings)
                for i in range(len(levels))
            )
            static = np.zeros((BIG_N, len(levels)), dtype=bool)
            trans = np.zeros((BIG_N, len(levels)), dtype=bool)
            for index, (col_s, col_t) in out:
                static[:, index] = col_s
                trans[:, index] = col_t
            columns[f"{arm}_static"] = static
            columns[f"{arm}_trans"] = trans
        save_raw_failure_payload(
            out_path,
            theta_matrix=theta,
            param_names=["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"],
            conditioning_grid=np.asarray(levels, dtype=float),
            failure_matrix_stat=columns["gross_static"],
            failure_matrix_tran=columns["gross_trans"],
            metadata={
                "adr": "0051",
                "stage": "equal-head-convention N = 1e6",
                "section": label,
                "crack_resistance_factor": GROSS_HEAD_FACTOR,
                "note": (
                    "failure_matrix_trans is the GROSS-HEAD transient "
                    "(crack_resistance_factor = 0). The static matrix is "
                    "unaffected by the knob and reproduces the persisted "
                    "ADR-0040 ladder C0 exactly."
                ),
                "config": config.to_metadata(),
                "config_hash": config.config_hash(),
                "ladder_reference": str(ladder_path.relative_to(REPO_ROOT)).replace(
                    "\\", "/"
                ),
            },
        )
        np.save(out_path.with_suffix(".production_trans.npy"), columns["gate_trans"])
    else:
        with h5py.File(out_path, "r") as handle:
            columns = {
                "gross_static": np.asarray(handle["failure_matrix_static"], dtype=bool),
                "gross_trans": np.asarray(handle["failure_matrix_trans"], dtype=bool),
            }
        columns["gate_static"] = columns["gross_static"]
        columns["gate_trans"] = np.load(out_path.with_suffix(".production_trans.npy"))

    # (i) at 1e6 too: the knob must not move a single static cell.
    if not np.array_equal(columns["gate_static"], columns["gross_static"]):
        moved = int(np.count_nonzero(columns["gate_static"] != columns["gross_static"]))
        raise AssertionError(
            f"{label}: the N = 1e6 static matrix moved in {moved} cells under "
            "the gross-head arm. Refusing to report."
        )

    # --- the gate: reproduce the persisted 1e6 ladder counts exactly ---------
    gate_rows: list[dict[str, Any]] = []
    with h5py.File(ladder_path, "r") as handle:
        ladder_grid = np.asarray(handle["conditioning_grid"], dtype=float)
        c0 = handle["comparators"]["C0"]
        c1 = handle["comparators"]["C1"]
        c4b = handle["comparators"]["C4b"]
        for index, level in enumerate(levels):
            j = int(np.argmin(np.abs(ladder_grid - level)))
            if abs(float(ladder_grid[j]) - level) > 1e-9:
                raise RuntimeError(f"{label}: level {level} absent from the ladder")
            k_c0 = int(np.asarray(c0[:, j]).sum())
            k_c1 = int(np.asarray(c1[:, j]).sum())
            k_c4b = int(np.asarray(c4b[:, j]).sum())
            k_static = int(columns["gross_static"][:, index].sum())
            k_trans = int(columns["gate_trans"][:, index].sum())
            row = {
                "stage_m_msl": float(level),
                "ladder_C0": k_c0,
                "fresh_static": k_static,
                "static_matches": bool(k_c0 == k_static),
                "ladder_C4b": k_c4b,
                "fresh_production_trans": k_trans,
                "transient_matches": bool(k_c4b == k_trans),
                "ladder_C1_crack_reduced_static": k_c1,
            }
            gate_rows.append(row)
    failures = [
        r for r in gate_rows if not (r["static_matches"] and r["transient_matches"])
    ]
    for (sec, level), expected in BIG_STATIC_GATE.items():
        if sec != label:
            continue
        row = next(r for r in gate_rows if abs(r["stage_m_msl"] - level) < 1e-9)
        if row["fresh_static"] != expected:
            failures.append(
                {
                    "stage_m_msl": level,
                    "pre_registered_static_count": expected,
                    "fresh_static": row["fresh_static"],
                }
            )
    if failures:
        raise AssertionError(
            f"{label}: the N = 1e6 seed-recipe gate failed -- the fresh run does "
            f"not reproduce the persisted ladder counts: {failures}. Refusing to "
            "report a paired comparison against a population it does not share."
        )

    table = level_table(
        np.asarray(levels, dtype=float),
        columns["gross_static"],
        columns["gate_trans"],
        columns["gross_trans"],
        label=f"{label}|n1e6",
    )
    for row, gate_row in zip(table, gate_rows):
        row["k_static_crack_reduced_C1"] = gate_row["ladder_C1_crack_reduced_static"]

    return {
        "section": label,
        "n_samples": BIG_N,
        "levels_m_msl": [float(x) for x in levels],
        "design_hwl_m_msl": float(base.geometry.HWL),
        "seed_recipe_gate": {"status": "reproduced", "detail": gate_rows},
        "artifact": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "ladder_reference": str(ladder_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "levels": table,
        "nesting": {
            "gross_not_static_rows_total": sum(
                row["gross_not_static_rows"] for row in table
            ),
            "production_not_static_rows_total": sum(
                row["production_not_static_rows"] for row in table
            ),
            "production_not_gross_rows_total": sum(
                row["production_not_gross_rows"] for row in table
            ),
        },
        "elapsed_s": round(time.time() - started, 1),
    }


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _stage_path(name: str) -> Path:
    return OUT_DIR / f"stage_{name}.json"


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


def cmd_n1e5(args: argparse.Namespace) -> int:
    started = time.time()
    payload: dict[str, Any] = {"stage": "n1e5", "sections": {}}
    path = _stage_path("n1e5")
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.setdefault("sections", {})
    for label in args.sections:
        record = run_section_n1e5(
            label,
            SECTIONS[label],
            n_jobs=args.n_jobs,
            skip_run=args.skip_run,
            skip_sustained=args.skip_sustained,
        )
        payload["sections"][label] = record
        print(
            f"[{label}] gate {record['gate_status']}, "
            f"nesting violations {record['nesting']['gross_not_static_rows_total']}, "
            f"{record['elapsed_s']} s"
        )
    payload["total_runtime_s"] = round(
        payload.get("total_runtime_s", 0.0) + time.time() - started, 1
    )
    _write(path, payload)
    return 0


def cmd_n1e6(args: argparse.Namespace) -> int:
    started = time.time()
    path = _stage_path("n1e6")
    payload: dict[str, Any] = {"stage": "n1e6", "sections": {}}
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.setdefault("sections", {})
    for label in args.sections:
        if label not in BIG_LEVELS:
            raise SystemExit(f"{label}: no persisted N = 1e6 ladder to pair against")
        record = run_section_n1e6(
            label, SECTIONS[label], n_jobs=args.n_jobs, skip_run=args.skip_run
        )
        payload["sections"][label] = record
        print(f"[{label}] seed-recipe gate reproduced, {record['elapsed_s']} s")
    payload["total_runtime_s"] = round(
        payload.get("total_runtime_s", 0.0) + time.time() - started, 1
    )
    _write(path, payload)
    return 0


def cmd_dtcheck(args: argparse.Namespace) -> int:
    """Run the ADR-0039 timestep ladder on every recorded sustained mismatch."""
    small = json.loads(_stage_path("n1e5").read_text(encoding="utf-8"))
    payload: dict[str, Any] = {"stage": "dtcheck", "checks": []}
    for label, record in small.get("sections", {}).items():
        for entry in record.get("sustained_peak") or []:
            if entry.get("identical"):
                continue
            print(
                f"[{label}] timestep ladder at {entry['stage_m_msl']:.2f} m ...",
                flush=True,
            )
            payload["checks"].append(
                sustained_dt_ladder(label, SECTIONS[label], entry["stage_m_msl"])
            )
    if not payload["checks"]:
        print("no sustained-peak mismatch recorded; nothing to diagnose")
    for check in payload["checks"]:
        print(f"  {check['section']} {check['stage_m_msl']:.2f} m: {check['verdict']}")
    _write(_stage_path("dtcheck"), payload)
    return 0


def _c1_corroboration() -> dict[str, Any]:
    """Reduced-vs-reduced (C1 / C4b) counts from the Stage 6.6 ladders.

    The *other* equal-convention reading: both branches crack-reduced, which is
    what Dutch practice does (Schweckendiek 2014 Eq. (3.14) puts the term on the
    static limit state too). It already exists at KP 57.4 and KP 62.0 and is read
    here rather than re-run. Nothing is available at the drained sections, where
    Stage 6.6 never ran; that is stated, not silently omitted.
    """
    out: dict[str, Any] = {}
    for label, spec in SECTIONS.items():
        if spec["ladder_key"] is None:
            out[label] = {"available": False, "reason": "Stage 6.6 never ran here"}
            continue
        section: dict[str, Any] = {"available": True, "by_n": {}}
        for n in (100_000, BIG_N):
            path = (
                REPO_ROOT
                / "results"
                / "hwl_bias_resolution"
                / f"ladder_{spec['ladder_key']}_n{n}.h5"
            )
            if not path.exists():
                continue
            rows = []
            with h5py.File(path, "r") as handle:
                grid = np.asarray(handle["conditioning_grid"], dtype=float)
                c0 = handle["comparators"]["C0"]
                c1 = handle["comparators"]["C1"]
                c4b = handle["comparators"]["C4b"]
                for index in range(grid.size):
                    k0 = int(np.asarray(c0[:, index]).sum())
                    k1 = int(np.asarray(c1[:, index]).sum())
                    k4 = int(np.asarray(c4b[:, index]).sum())
                    rows.append(
                        {
                            "stage_m_msl": float(grid[index]),
                            "k_C0_gross_static": k0,
                            "k_C1_crack_reduced_static": k1,
                            "k_C4b_production_transient": k4,
                            "B_reduced_vs_reduced": (k1 / k4) if k4 else None,
                            "delta_beta_reduced_vs_reduced": (
                                beta_of(k4 / n) - beta_of(k1 / n)
                            ),
                        }
                    )
            section["by_n"][str(n)] = {
                "artifact": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "levels": rows,
            }
        out[label] = section
    return out


def cmd_report(args: argparse.Namespace) -> int:
    small = json.loads(_stage_path("n1e5").read_text(encoding="utf-8"))
    big = json.loads(_stage_path("n1e6").read_text(encoding="utf-8"))
    payload = {
        "adr": "0051",
        "description": (
            "Equal-head-convention comparison: the Pol SIE 2024 Eq. (6) "
            "crack-resistance coefficient set to zero, so the transient erosion "
            "driver is the static comparator's own gross head h(t) - z_toe. The "
            "coefficient reaches the erosion driver alone, so the static branch "
            "is exactly invariant and the whole displacement sits in the "
            "transient branch. Baseline files untouched."
        ),
        "crack_resistance_factor": GROSS_HEAD_FACTOR,
        "published_value": 0.3,
        "metric_definitions": {
            "B": "P_static / P_transient at one conditioning level",
            "beta": "-Phi^-1(P_f) per branch",
            "delta_beta": "beta_transient - beta_static (paired, shared sample)",
            "beta_interval": (
                "monotone image of the exact Clopper-Pearson interval on the raw "
                "count; no new statistical machinery (campaign plan D1)"
            ),
            "delta_beta_interval": (
                "paired percentile bootstrap over the shared realization set, "
                f"B = {BOOTSTRAP_REPLICATES} replicates, one row resample per "
                "replicate applied to both branches; kernel imported from "
                "scripts/hwl_bias_resolution.py"
            ),
            "B_interval": (
                "the ADR-0040 paired-bootstrap bias_ratio estimator with its "
                "pre-registered R1 (>= 30 transient rows) and R2 (interval width "
                "factor <= 2) criteria, imported unchanged"
            ),
        },
        "scope": (
            "Matrix reading only. Bulk is skipped on the ADR-0040 section 4 "
            "precedent: it is degenerate at the stages where the head convention "
            "matters. Historical scenario only (ADR-0023 shape invariance)."
        ),
        "n1e5": small.get("sections", {}),
        "n1e6": big.get("sections", {}),
        "corroboration_reduced_vs_reduced": _c1_corroboration(),
        "sustained_peak_dt_diagnosis": (
            json.loads(_stage_path("dtcheck").read_text(encoding="utf-8"))
            if _stage_path("dtcheck").exists()
            else None
        ),
    }
    JSON_OUT.write_text(
        json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {JSON_OUT.relative_to(REPO_ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    small = sub.add_parser("n1e5", help="four matrix sections, full production grid")
    small.add_argument("--sections", nargs="*", default=list(SECTIONS))
    small.add_argument("--n-jobs", type=int, default=-1)
    small.add_argument("--skip-run", action="store_true")
    small.add_argument("--skip-sustained", action="store_true")
    small.set_defaults(func=cmd_n1e5)

    large = sub.add_parser("n1e6", help="design anchors at KP 57.4 and KP 62.0")
    large.add_argument("--sections", nargs="*", default=list(BIG_LEVELS))
    large.add_argument("--n-jobs", type=int, default=-1)
    large.add_argument("--skip-run", action="store_true")
    large.set_defaults(func=cmd_n1e6)

    dtcheck = sub.add_parser(
        "dtcheck", help="timestep ladder on any sustained-peak mismatch"
    )
    dtcheck.set_defaults(func=cmd_dtcheck)

    report = sub.add_parser("report", help="assemble the evidence JSON")
    report.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    for label in getattr(args, "sections", []):
        if label not in SECTIONS:
            parser.error(f"unknown section {label!r}; known: {sorted(SECTIONS)}")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
