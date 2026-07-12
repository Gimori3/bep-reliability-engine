"""Phase 2 end-to-end self-test on genuine small-N Phase 1 runs.

Generates real Phase 1 FragilityResults (production configs, canonical
d4PDF path, ADR-0030 225 s grid) at reduced N for the two reachable
sections (KP 58.8 and KP 60.0, matrix interpretation), then runs the full
Phase 2 survival update against the observed 2016 event with the
re-evaluation verification enabled, and prints the summary block the
Phase 2 report quotes. Outputs land under ``results/phase2_selftest/``
(gitignored).

Run from the repository root (needs the untracked ``data/raw`` drop)::

    python scripts/run_phase2_selftest.py [--n 4000] [--n-jobs 4]
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from bayesian_reliability_updating.pipeline import (
    Phase2Settings,
    run_survival_update,
)
from bep_reliability_engine.config import Config
from bep_reliability_engine.run import run_fragility_analysis

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO_ROOT / "results" / "phase2_selftest"
CONFIGS = [
    REPO_ROOT / "configs" / "kp58_8_historical_matrix.yaml",
    REPO_ROOT / "configs" / "kp60_0_historical_matrix.yaml",
]


def _small_config(path: Path, n_samples: int) -> Config:
    config = Config.from_yaml(path)
    data = config.model_dump(mode="json")
    data["mc"]["n_samples"] = int(n_samples)
    return Config.model_validate(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=4000, help="Phase 1 sample size.")
    parser.add_argument("--n-jobs", type=int, default=4, help="Phase 1 sweep workers.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    settings = Phase2Settings(
        output_dir=str(OUT_ROOT),
        verify_by_reevaluation=True,
        trace_breach_times=True,
        figures=True,
        overwrite=True,
    )

    summaries = []
    for config_path in CONFIGS:
        config = _small_config(config_path, args.n)
        stem = f"{config.cross_section_id}_{config.priors.d70_interpretation}_N{args.n}"
        phase1_out = OUT_ROOT / f"{stem}.h5"

        start = time.perf_counter()
        if not phase1_out.exists():
            print(f"\n=== Phase 1 small-N sweep: {stem} ===")
            run_fragility_analysis(
                config,
                n_jobs=args.n_jobs,
                progress=True,
                output_path=phase1_out,
                overwrite=True,
            )
        phase1_seconds = time.perf_counter() - start

        print(f"\n=== Phase 2 survival update: {stem} ===")
        start = time.perf_counter()
        result = run_survival_update(phase1_out, settings=settings)
        phase2_seconds = time.perf_counter() - start

        meta = result.metadata
        event = meta["phase2"]["event_chain"][0]
        headline = meta["analysis"]["c_e_headline"]
        summaries.append(
            {
                "stem": stem,
                "segment": meta["phase1"]["segment_id"],
                "n_prior": meta["phase2"]["posterior"]["n_prior"],
                "n_accepted": meta["phase2"]["posterior"]["n_accepted"],
                "rejection_fraction": meta["phase2"]["posterior"]["rejection_fraction"],
                "decomposition": event["decomposition"],
                "verified": meta["phase2"]["verification"]["verified"],
                "record_peak_m_msl": event["record"]["peak_m_msl"],
                "window_closed": event["window_closure"]["closed"],
                "c_e_prior_mean": headline["prior_mean"],
                "c_e_posterior_mean": headline["posterior_mean"],
                "phase1_seconds": round(phase1_seconds, 1),
                "phase2_seconds": round(phase2_seconds, 1),
            }
        )

    print("\n" + "=" * 72)
    print("PHASE 2 SELF-TEST SUMMARY")
    print("=" * 72)
    print(json.dumps(summaries, indent=2))
    (OUT_ROOT / "selftest_summary.json").write_text(
        json.dumps(summaries, indent=2), encoding="utf-8"
    )
    print(f"\nSummary written to {OUT_ROOT / 'selftest_summary.json'}")


if __name__ == "__main__":
    main()
