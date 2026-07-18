"""ADR-0045 companion: quantify the Sellmeijer model factor m_p against baseline.

For each persisted production sweep given (default: the two informative
matrix sections KP58.8 and KP60.0), this driver

1. reconstructs the run's exact Config from its own metadata snapshot
   (hash-checked), so the comparison is against the frozen baseline under
   identical assumptions;
2. re-runs the full sweep with the ADR-0045 ``sellmeijer_model_factor``
   block enabled (m_p ~ Lognormal(mean 1.0, CoV 0.12), Pol SIE 2024
   Table 2) — theta, L, hydrographs and grid all identical, only m_p added;
3. writes the companion FragilityResult under
   ``results/sensitivity/adr0045_mp/`` (never touching the baseline files)
   and the per-level comparison table to
   ``docs/decisions/adr0045-mp-companion.json``.

The baseline is NEVER regenerated: it is loaded read-only from ``results/``.

Usage (from the repo root, venv active)::

    python scripts/mp_model_factor_companion.py                # both sections
    python scripts/mp_model_factor_companion.py --n-jobs 4 \
        results/tokachi_kp58.8_historical_matrix.h5            # one section
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import (  # noqa: E402
    Config,
    SellmeijerModelFactorSettings,
)
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402

DEFAULT_BASELINES = [
    "results/tokachi_kp58.8_historical_matrix.h5",
    "results/tokachi_kp60.0_historical_matrix.h5",
]
OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0045_mp"
JSON_OUT = REPO_ROOT / "docs" / "decisions" / "adr0045-mp-companion.json"


def _ratio(numer: np.ndarray, denom: np.ndarray) -> list[float | None]:
    """Elementwise numer/denom with None where the baseline is exactly 0."""
    out: list[float | None] = []
    for a, b in zip(numer, denom):
        out.append(None if b == 0.0 else float(a / b))
    return out


def run_companion(
    baseline_path: Path, *, mean: float, cov: float, n_jobs: int, overwrite: bool
) -> dict:
    baseline = FragilityResult.load(baseline_path)
    config = Config.model_validate(baseline.metadata["config"])
    recorded = baseline.metadata.get("config_hash")
    if recorded is not None and config.config_hash() != recorded:
        raise ValueError(
            f"{baseline_path.name}: reconstructed config hash does not match "
            "the recorded config_hash; refusing to compare against drifted "
            "assumptions."
        )
    if config.sellmeijer_model_factor is not None:
        raise ValueError(
            f"{baseline_path.name}: baseline already carries a "
            "sellmeijer_model_factor block; this driver expects the m_p-off "
            "production baseline."
        )

    variant = config.model_copy(
        update={
            "sellmeijer_model_factor": SellmeijerModelFactorSettings(
                enabled=True, mean=mean, cov=cov
            )
        }
    )
    out_path = OUT_DIR / f"{baseline_path.stem}_mp.h5"
    print(f"[{baseline_path.stem}] sweeping with m_p ~ Ln({mean}, CoV {cov}) ...")
    companion = run_fragility_analysis(
        variant,
        n_jobs=n_jobs,
        progress=True,
        output_path=out_path,
        overwrite=overwrite,
    )

    grid = np.asarray(baseline.conditioning_grid, dtype=float)
    if not np.array_equal(grid, np.asarray(companion.conditioning_grid, dtype=float)):
        raise RuntimeError("companion grid differs from baseline grid")

    entry = {
        "baseline_file": baseline_path.name,
        "companion_file": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "cross_section_id": config.cross_section_id,
        "d70_interpretation": config.priors.d70_interpretation,
        "mp_mean": mean,
        "mp_cov": cov,
        "n_samples": int(config.mc.n_samples),
        "z_toe_m_msl": float(config.geometry.z_toe),
        "grid_m_msl": grid.tolist(),
        "p_f_static_baseline": np.asarray(baseline.P_f_static_raw, float).tolist(),
        "p_f_static_mp": np.asarray(companion.P_f_static_raw, float).tolist(),
        "p_f_trans_baseline": np.asarray(baseline.P_f_trans_raw, float).tolist(),
        "p_f_trans_mp": np.asarray(companion.P_f_trans_raw, float).tolist(),
        "ratio_static": _ratio(
            np.asarray(companion.P_f_static_raw, float),
            np.asarray(baseline.P_f_static_raw, float),
        ),
        "ratio_trans": _ratio(
            np.asarray(companion.P_f_trans_raw, float),
            np.asarray(baseline.P_f_trans_raw, float),
        ),
    }

    print(
        f"  {'stage':>7s} {'Pf_stat base':>12s} {'Pf_stat mp':>12s} {'ratio':>7s}"
        f" {'Pf_tran base':>12s} {'Pf_tran mp':>12s} {'ratio':>7s}"
    )
    for i, level in enumerate(grid):
        rs = entry["ratio_static"][i]
        rt = entry["ratio_trans"][i]
        print(
            f"  {level:7.2f} {entry['p_f_static_baseline'][i]:12.3e} "
            f"{entry['p_f_static_mp'][i]:12.3e} "
            f"{'-' if rs is None else format(rs, '7.3f')} "
            f"{entry['p_f_trans_baseline'][i]:12.3e} "
            f"{entry['p_f_trans_mp'][i]:12.3e} "
            f"{'-' if rt is None else format(rt, '7.3f')}"
        )
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "baselines",
        nargs="*",
        default=DEFAULT_BASELINES,
        help="Persisted baseline HDF5 files (default: the two informative "
        "matrix sections).",
    )
    parser.add_argument("--mp-mean", type=float, default=1.0)
    parser.add_argument("--mp-cov", type=float, default=0.12)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--overwrite", action="store_true", default=True)
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for raw in args.baselines:
        path = (REPO_ROOT / raw) if not Path(raw).is_absolute() else Path(raw)
        entries.append(
            run_companion(
                path,
                mean=args.mp_mean,
                cov=args.mp_cov,
                n_jobs=args.n_jobs,
                overwrite=args.overwrite,
            )
        )

    payload = {
        "adr": "0045",
        "description": (
            "Companion sensitivity: Sellmeijer model factor m_p on the "
            "single-source H_c (both branches), vs the frozen m_p-off "
            "production baseline. Baseline files untouched."
        ),
        "sections": entries,
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {JSON_OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
