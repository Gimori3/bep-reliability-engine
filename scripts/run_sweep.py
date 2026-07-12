"""Thin driver for Phase 1 fragility sweeps: one run per config file.

Loops :func:`bep_reliability_engine.run.run_fragility_analysis` over the given
config YAMLs (no physics here, spec §9) and persists each FragilityResult to
``results/`` under an interpretation-qualified name — the generated matrix and
bulk configs share ``cross_section_id`` (their difference is
``priors.d70_interpretation``), so the run.py default stem would collide across
the co-primary d_70 runs.

Usage (from the repo root, venv active)::

    python scripts/run_sweep.py configs/kp*_historical_matrix.yaml
    python scripts/run_sweep.py --n-jobs 4 --overwrite configs/kp58_8_*.yaml

Output: ``results/<cross_section_id>_<scenario>_<d70_interpretation>.h5`` plus
the JSON metadata sidecar (spec §8). Existing results are refused unless
``--overwrite`` is passed (the run.py guard).

QA MEMBER (registered 2026-07-11; EXECUTED 2026-07-13)
------------------------------------------------------
The KP58.8 r_e-halved sensitivity member (r_e -> r_e/2; ADR-0032 scope
amendment; ``docs/validation/shikaga-case.md`` sec. 3) is realized as the
harness-level run ``scripts/qa_re_halved_member.py`` (r_e is derived per
realization, never a config field). Measured on the production
``tokachi_kp58.8_historical_matrix`` member (N = 1e5, baseline drift guard
bit-identical at all 29 levels): the effect is shoulder-concentrated exactly
as predicted — max |delta P_f| = 0.181 at 41.25 m MSL, deep-shoulder
suppression down to ratios 0.002-0.09 (40.0-40.5 m), converging to parity
(>= 0.99) above 43.5 m; halving r_e produced zero new failures, confirming
standard r_e as the conservative side. Full per-level table:
``results/qa_re_halved_kp58_8.json``. Re-run the harness after any re-sweep
that changes the KP58.8 matrix member.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from bep_reliability_engine import Config, run_fragility_analysis

REPO_ROOT = Path(__file__).resolve().parents[1]


def output_path_for(config: Config) -> Path:
    """Interpretation-qualified result path (matrix/bulk configs never collide)."""
    scenario_tag = config.scenario.replace("+", "plus")
    stem = (
        f"{config.cross_section_id}_{scenario_tag}_"
        f"{config.priors.d70_interpretation}"
    )
    return REPO_ROOT / config.output.results_dir / f"{stem}.h5"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("configs", nargs="+", type=Path, help="config YAML paths")
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="joblib workers over conditioning levels (results identical for any "
        "value; default 1)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing result files instead of refusing",
    )
    args = parser.parse_args()

    for config_path in args.configs:
        config = Config.from_yaml(config_path)
        out = output_path_for(config)
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{config_path.name}] -> {out.relative_to(REPO_ROOT)}", flush=True)
        t0 = time.perf_counter()
        result = run_fragility_analysis(
            config,
            n_jobs=args.n_jobs,
            output_path=out,
            overwrite=args.overwrite,
        )
        elapsed = time.perf_counter() - t0
        deliverable = result.metadata.get("fragility_deliverable", {})
        for branch in ("static", "transient"):
            flags = deliverable.get(branch, {})
            print(
                f"  {branch:9s} form={flags.get('form', '?'):18s} "
                f"max_p_f_raw={flags.get('max_p_f_raw', float('nan')):.4f} "
                f"fit_role={flags.get('fit_role', '?')}",
                flush=True,
            )
        print(f"  done in {elapsed:.1f} s", flush=True)


if __name__ == "__main__":
    main()
