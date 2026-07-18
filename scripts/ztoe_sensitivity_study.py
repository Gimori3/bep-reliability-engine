"""ADR-0046 companion: surveyed exit-datum (z_toe +/- 0.3 m) sensitivity.

The ADR-0021 landside-toe elevations carry a surveyed uncertainty of about
+/-0.3 m. This driver treats that as a systematic per-section epistemic
scenario (never a stochastic sampler column) and quantifies it end to end
for the informative sections:

1. **Phase 1 curve shift** — for each persisted baseline sweep, re-run the
   full sweep with ``geometry.z_toe`` shifted by +/-0.3 m (config otherwise
   identical, reconstructed from the baseline's own hash-checked metadata
   snapshot; theta/L/hydrographs unchanged). Also measures how well the
   shifted curve equals the baseline curve translated horizontally by the
   same 0.3 m (the first-order reading).
2. **Phase 2 posterior movement, fully consistent datum** — run the 2016
   survival update on each shifted Phase 1 companion (the shifted config
   carries the datum end to end: prior matrices, h_2016 window closure and
   the replay all at z_toe +/- 0.3).
3. **Phase 2 evidence-channel isolation** — run the update on the BASELINE
   Phase 1 file with the ADR-0046 ``z_toe_delta_m`` replay-only scenario
   knob, isolating how much of the movement comes through the evidence
   replay datum alone (prior matrices stay baseline).

Baseline sweeps and the baseline posterior are NEVER regenerated: baselines
are read from ``results/`` and ``results/phase2/``; companion outputs land
under ``results/sensitivity/adr0046_ztoe/`` and the comparison table in
``docs/decisions/adr0046-ztoe-companion.json``.

Usage (repo root, venv active)::

    python scripts/ztoe_sensitivity_study.py            # both sections
    python scripts/ztoe_sensitivity_study.py --delta 0.3 --n-jobs 4 \
        results/tokachi_kp58.8_historical_matrix.h5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bayesian_reliability_updating.pipeline import (  # noqa: E402
    Phase2Settings,
    run_survival_update,
)
from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402

DEFAULT_BASELINES = [
    "results/tokachi_kp58.8_historical_matrix.h5",
    "results/tokachi_kp60.0_historical_matrix.h5",
]
OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0046_ztoe"
JSON_OUT = REPO_ROOT / "docs" / "decisions" / "adr0046-ztoe-companion.json"


def _delta_tag(delta: float) -> str:
    sign = "plus" if delta > 0 else "minus"
    return f"ztoe_{sign}{abs(delta):.2f}m"


def _posterior_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    """Comparable numbers from a Phase 2 metadata dict (file or in-memory)."""
    posterior = metadata["phase2"]["posterior"]
    decomposition = metadata["phase2"]["event_chain"][-1]["decomposition"]
    marginals = metadata["analysis"]["marginals"]

    def _mean_shift(name: str) -> dict[str, float]:
        prior = marginals[name]["prior"]["mean"]
        post = marginals[name]["posterior"]["mean"]
        return {
            "prior_mean": float(prior),
            "posterior_mean": float(post),
            "shift_percent": 100.0 * (post / prior - 1.0),
        }

    return {
        "rejection_fraction_trans": float(posterior["rejection_fraction"]),
        "f_static_reject": float(decomposition["f_static_reject"]),
        "f_marginal_transient": float(decomposition["f_marginal_transient"]),
        "C_e": _mean_shift("C_e"),
        "k_aq": _mean_shift("k_aq"),
    }


def _horizontal_shift_check(
    grid: np.ndarray, p_base: np.ndarray, p_shift: np.ndarray, delta: float
) -> float:
    """Max |P_f,shifted(h) - P_f,base(h - delta)| on the overlapping grid.

    The first-order reading of the datum scenario is a horizontal curve
    translation by delta; the residual measures how far the full re-run
    deviates from it (the hydrograph shape is anchored at the base-flow
    stage, not at the toe, so the transient branch need not translate
    exactly).
    """
    translated = np.interp(grid, grid + delta, p_base, left=np.nan, right=np.nan)
    valid = np.isfinite(translated)
    if not valid.any():
        return float("nan")
    return float(np.nanmax(np.abs(p_shift[valid] - translated[valid])))


def run_section(
    baseline_path: Path, *, delta: float, n_jobs: int, n_bootstrap: int
) -> dict[str, Any]:
    baseline = FragilityResult.load(baseline_path)
    config = Config.model_validate(baseline.metadata["config"])
    recorded = baseline.metadata.get("config_hash")
    if recorded is not None and config.config_hash() != recorded:
        raise ValueError(
            f"{baseline_path.name}: reconstructed config hash mismatch; "
            "refusing to compare against drifted assumptions."
        )

    grid = np.asarray(baseline.conditioning_grid, dtype=float)
    entry: dict[str, Any] = {
        "baseline_file": baseline_path.name,
        "cross_section_id": config.cross_section_id,
        "d70_interpretation": config.priors.d70_interpretation,
        "z_toe_baseline_m_msl": float(config.geometry.z_toe),
        "delta_m": delta,
        "grid_m_msl": grid.tolist(),
        "phase1": {},
        "phase2_end_to_end": {},
        "phase2_replay_only": {},
    }

    # Baseline Phase 2 numbers for reference (read-only, never regenerated).
    baseline_posterior = (
        REPO_ROOT / "results" / "phase2" / f"{baseline_path.stem}_posterior.json"
    )
    if baseline_posterior.exists():
        with open(baseline_posterior, encoding="utf-8") as handle:
            entry["phase2_baseline"] = _posterior_summary(json.load(handle))

    for signed in (-delta, +delta):
        tag = _delta_tag(signed)
        shifted_geom = config.geometry.model_copy(
            update={"z_toe": float(config.geometry.z_toe) + signed}
        )
        variant = config.model_copy(update={"geometry": shifted_geom})
        out_path = OUT_DIR / f"{baseline_path.stem}_{tag}.h5"

        print(f"[{baseline_path.stem}] Phase 1 sweep at z_toe {signed:+.2f} m ...")
        companion = run_fragility_analysis(
            variant,
            n_jobs=n_jobs,
            progress=True,
            output_path=out_path,
            overwrite=True,
        )
        p_stat = np.asarray(companion.P_f_static_raw, float)
        p_tran = np.asarray(companion.P_f_trans_raw, float)
        entry["phase1"][tag] = {
            "companion_file": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "p_f_static": p_stat.tolist(),
            "p_f_trans": p_tran.tolist(),
            "max_dev_from_horizontal_shift_static": _horizontal_shift_check(
                grid, np.asarray(baseline.P_f_static_raw, float), p_stat, signed
            ),
            "max_dev_from_horizontal_shift_trans": _horizontal_shift_check(
                grid, np.asarray(baseline.P_f_trans_raw, float), p_tran, signed
            ),
        }

        # Phase 2 on the shifted companion: datum consistent end to end.
        print(f"[{baseline_path.stem}] Phase 2 update on the {tag} companion ...")
        settings = Phase2Settings(
            output_dir=str(OUT_DIR / "phase2"),
            verify_by_reevaluation=False,
            trace_breach_times=False,
            figures=False,
            n_bootstrap=n_bootstrap,
            overwrite=True,
        )
        result = run_survival_update(out_path, settings=settings)
        entry["phase2_end_to_end"][tag] = _posterior_summary(result.metadata)

        # Phase 2 replay-only scenario on the BASELINE file (evidence channel).
        print(f"[{baseline_path.stem}] Phase 2 replay-only scenario {tag} ...")
        replay_settings = Phase2Settings(
            output_dir=str(OUT_DIR / "phase2"),
            verify_by_reevaluation=False,
            trace_breach_times=False,
            figures=False,
            n_bootstrap=n_bootstrap,
            overwrite=True,
            z_toe_delta_m=signed,
        )
        replay_result = run_survival_update(
            baseline_path, settings=replay_settings, persist=False
        )
        entry["phase2_replay_only"][tag] = _posterior_summary(replay_result.metadata)

    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("baselines", nargs="*", default=DEFAULT_BASELINES)
    parser.add_argument(
        "--delta",
        type=float,
        default=0.3,
        help="Datum offset magnitude [m]; both signs run (default 0.3, "
        "the ADR-0021 survey band).",
    )
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--n-bootstrap", type=int, default=200)
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sections = []
    for raw in args.baselines:
        path = (REPO_ROOT / raw) if not Path(raw).is_absolute() else Path(raw)
        sections.append(
            run_section(
                path,
                delta=args.delta,
                n_jobs=args.n_jobs,
                n_bootstrap=args.n_bootstrap,
            )
        )

    payload = {
        "adr": "0046",
        "description": (
            "Epistemic exit-datum sensitivity (ADR-0021 surveyed z_toe "
            "+/-0.3 m): Phase 1 curve shift, Phase 2 posterior movement "
            "with the datum consistent end to end, and the replay-only "
            "evidence-channel isolation. Baselines untouched."
        ),
        "sections": sections,
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {JSON_OUT.relative_to(REPO_ROOT)}")

    for section in sections:
        print(
            f"\n=== {section['cross_section_id']} "
            f"(toe {section['z_toe_baseline_m_msl']:.2f} m MSL) ==="
        )
        base = section.get("phase2_baseline")
        if base:
            print(
                f"  baseline        : trans rejection "
                f"{100 * base['rejection_fraction_trans']:6.2f}%  "
                f"C_e {base['C_e']['shift_percent']:+.1f}%  "
                f"k_aq {base['k_aq']['shift_percent']:+.1f}%"
            )
        for tag in sorted(section["phase2_end_to_end"]):
            e2e = section["phase2_end_to_end"][tag]
            rep = section["phase2_replay_only"][tag]
            r_e2e = 100 * e2e["rejection_fraction_trans"]
            r_rep = 100 * rep["rejection_fraction_trans"]
            print(
                f"  {tag:18s}: trans rejection {r_e2e:6.2f}% "
                f"(replay-only {r_rep:6.2f}%)  "
                f"C_e {e2e['C_e']['shift_percent']:+.1f}%  "
                f"k_aq {e2e['k_aq']['shift_percent']:+.1f}%"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
