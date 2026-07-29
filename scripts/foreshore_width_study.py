"""Foreshore-width (B_f) provenance check and measured fragility sensitivity.

Companion driver for ADR-0025 (see `docs/decisions/adr0025-foreshore-width-and-
sensitivity.md`). Two questions, one script:

1. **Does B_f matter?** For each confined production section, re-run the matrix
   sweep at the adopted CSV foreshore width and at the ADR-0025 bounding
   ``open_entry`` end (B_f = 0, x1 = 0), plus two extra arms at KP 62.0 that
   demonstrate the tanh saturation. Report max |dP_f| per branch.
2. **Is the baseline still the persisted production physics?** Each section's
   baseline arm is asserted bit-identical against its persisted production
   sweep in ``results/`` before any comparison is reported, so a drifted engine
   cannot quietly produce a reassuring sensitivity number.

The static branch is expected to be *exactly* invariant to B_f: since ADR-0028
r_e drives only the uplift/heave gate and both piping heads are raw, so the
static comparator has no foreland dependence at all. The run asserts this
rather than merely reporting it.

Nothing here is a sweep member and nothing is persisted into ``results/``:
this is an on-demand companion, run with ``persist=False``. The measured
``geometry.foreshore_width`` in the CSV and configs is never modified.

Usage
-----
    python scripts/foreshore_width_study.py
    python scripts/foreshore_width_study.py --sections KP62.0 --out other.json

Runtime is roughly 3 to 4 minutes per arm at the production N = 1e5 (ten arms
by default), dominated by the M7 timestepper.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import yaml

from bep_reliability_engine.config import Config
from bep_reliability_engine.run import run_fragility_analysis

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "docs" / "decisions" / "adr0025-foreshore-sensitivity.json"

#: Per-section: config, persisted production sweep, and the extra B_f arms to
#: run beyond {CSV baseline, 0.0}. The CSV baseline is read from the config, so
#: this table cannot drift from the CSV independently.
SECTIONS: dict[str, dict[str, Any]] = {
    "KP57.4": {
        "config": "configs/kp57_4_historical_matrix.yaml",
        "production": "results/tokachi_kp57.4_historical_matrix.h5",
        "extra_arms": (),
    },
    "KP58.8": {
        "config": "configs/kp58_8_historical_matrix.yaml",
        "production": "results/tokachi_kp58.8_historical_matrix.h5",
        "extra_arms": (),
    },
    "KP60.0": {
        "config": "configs/kp60_0_historical_matrix.yaml",
        "production": "results/tokachi_kp60.0_historical_matrix.h5",
        "extra_arms": (),
    },
    "KP62.0": {
        "config": "configs/kp62_0_historical_matrix.yaml",
        "production": "results/tokachi_kp62.0_historical_matrix.h5",
        # 100 m and 300 m demonstrate that the tanh has saturated: every value
        # above ~2.5 * lambda_out is numerically the same answer.
        "extra_arms": (100.0, 300.0),
    },
}


def _run_arm(config_path: Path, foreshore_width_m: float, n_jobs: int):
    """Run one sweep with ``geometry.foreshore_width`` overridden.

    The YAML is loaded, the single field replaced, and the result re-validated
    through :class:`Config`; the on-disk config is never written to.
    """
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["geometry"]["foreshore_width"] = float(foreshore_width_m)
    config = Config.model_validate(data)
    return run_fragility_analysis(config, n_jobs=n_jobs, progress=False, persist=False)


def _assert_baseline_bit_identical(result, production_path: Path, label: str) -> None:
    """Refuse to report a sensitivity if the baseline arm has drifted."""
    with h5py.File(production_path, "r") as handle:
        prod_static = np.asarray(handle["P_f_static_raw"])
        prod_trans = np.asarray(handle["P_f_trans_raw"])
    d_static = float(np.max(np.abs(result.P_f_static_raw - prod_static)))
    d_trans = float(np.max(np.abs(result.P_f_trans_raw - prod_trans)))
    if d_static != 0.0 or d_trans != 0.0:
        raise AssertionError(
            f"{label}: baseline arm is not bit-identical to the persisted "
            f"production sweep {production_path.name} "
            f"(max |d| static {d_static:.3e}, transient {d_trans:.3e}). "
            "Refusing to report a sensitivity against a drifted baseline."
        )


def study_section(label: str, spec: dict[str, Any], n_jobs: int) -> dict[str, Any]:
    config_path = REPO_ROOT / spec["config"]
    production_path = REPO_ROOT / spec["production"]
    baseline_b_f = float(Config.from_yaml(config_path).geometry.foreshore_width)

    started = time.time()
    baseline = _run_arm(config_path, baseline_b_f, n_jobs)
    _assert_baseline_bit_identical(baseline, production_path, label)

    grid = np.asarray(baseline.conditioning_grid, dtype=float)
    leakage = baseline.metadata["leakage_geometry"]
    record: dict[str, Any] = {
        "section": label,
        "config": spec["config"],
        "production_sweep": spec["production"],
        "baseline_foreshore_width_m": baseline_b_f,
        "baseline_bit_identical_to_production": True,
        "n_samples": int(baseline.theta_matrix.shape[0]),
        "median_lambda_in_m": float(leakage["median_lambda_in_m"]),
        "median_lambda_out_eff_m": float(leakage["median_lambda_out_eff_m"]),
        "median_foreland_tanh_credit": float(leakage["median_foreland_tanh_credit"]),
        "arms": {},
    }

    for b_f in (0.0, *spec["extra_arms"]):
        arm = _run_arm(config_path, b_f, n_jobs)
        d_trans = np.abs(arm.P_f_trans_raw - baseline.P_f_trans_raw)
        d_static = np.abs(arm.P_f_static_raw - baseline.P_f_static_raw)
        # ADR-0028: the static branch is r_e-independent by construction.
        if float(d_static.max()) != 0.0:
            raise AssertionError(
                f"{label}: static P_f moved with B_f (max |d| "
                f"{float(d_static.max()):.3e}). Since ADR-0028 the static "
                "comparator has no foreland dependence; this is a regression."
            )
        worst = int(d_trans.argmax())
        record["arms"][f"B_f={b_f:g}m"] = {
            "foreshore_width_m": b_f,
            "median_lambda_out_eff_m": float(
                arm.metadata["leakage_geometry"]["median_lambda_out_eff_m"]
            ),
            "median_foreland_tanh_credit": float(
                arm.metadata["leakage_geometry"]["median_foreland_tanh_credit"]
            ),
            "max_abs_delta_P_f_trans": float(d_trans.max()),
            "max_abs_delta_P_f_trans_at_stage_m_msl": float(grid[worst]),
            "P_f_trans_baseline_at_that_stage": float(baseline.P_f_trans_raw[worst]),
            "P_f_trans_arm_at_that_stage": float(arm.P_f_trans_raw[worst]),
            "max_abs_delta_P_f_static": float(d_static.max()),
        }

    record["elapsed_s"] = round(time.time() - started, 1)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sections",
        nargs="+",
        default=list(SECTIONS),
        choices=list(SECTIONS),
        help="Sections to study (default: all four confined production sections).",
    )
    parser.add_argument(
        "--n-jobs", type=int, default=4, help="joblib workers per sweep."
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Evidence JSON output path."
    )
    args = parser.parse_args()

    records = []
    for label in args.sections:
        print(f"[{label}] running ...", flush=True)
        record = study_section(label, SECTIONS[label], args.n_jobs)
        records.append(record)
        for arm_name, arm in record["arms"].items():
            print(
                f"  {arm_name:<12} max |dP_f_trans| = "
                f"{arm['max_abs_delta_P_f_trans']:.5f} at "
                f"{arm['max_abs_delta_P_f_trans_at_stage_m_msl']:.2f} m MSL; "
                f"static {arm['max_abs_delta_P_f_static']:.5f}",
                flush=True,
            )

    payload = {
        "study": "ADR-0025 foreshore-width (B_f) fragility sensitivity",
        "generated_by": "scripts/foreshore_width_study.py",
        "d70_interpretation": "matrix",
        "note": (
            "B_f enters only hydraulics.leakage_length_out -> r_e, and since "
            "ADR-0028 r_e drives only the uplift/heave gate. B_f = 0 is the "
            "ADR-0025 open_entry bound (x1 = 0). Every baseline arm is asserted "
            "bit-identical to its persisted production sweep before comparison."
        ),
        "sections": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
