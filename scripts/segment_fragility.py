"""ADR-0037 segment-level fragility tables from persisted results (post hoc).

Applies the weakest-link transform ``P_seg = 1 - (1 - P_cs)^n_eff`` (public
:func:`bep_reliability_engine.fragility.upscale_length_effect`) to persisted
cross-section curves at the ADR-0037 primary value (lambda_ac = 250 m,
n_eff = 1) and the conservative sensitivity bracket (100 m -> n_eff = 2,
40 m -> n_eff = 5), for both the Phase 1 prior results and, when present,
the Phase 2 posterior results. Pure post-processing: no persisted file is
modified; output is one JSON summary.

Under the primary value the transform is the identity (n_eff = 1) — that is
the ADR-0037 finding, not a bug: the OYO section spacing and the
blanket-anchored literature both put the 200 m segment inside one
correlation length.

Usage (repo root, venv active)::

    python scripts/segment_fragility.py

Output: ``results/segment_fragility_adr0037.json``.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

import numpy as np

from bayesian_reliability_updating.posterior import PosteriorResult
from bep_reliability_engine.fragility import FragilityResult, upscale_length_effect

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
OUT_JSON = RESULTS / "segment_fragility_adr0037.json"

# ADR-0037: primary + conservative sensitivity bracket.
LAMBDA_AC_CASES_M = (250.0, 100.0, 40.0)
SEGMENT_LENGTH_M = 200.0


def n_eff_for(lambda_ac_m: float) -> float:
    """ADR-0037 n_eff with the clamp at 1 from below."""
    return max(1.0, SEGMENT_LENGTH_M / lambda_ac_m)


def upscaled_block(
    grid: np.ndarray, curves: dict[str, np.ndarray]
) -> dict[str, object]:
    """Segment curves for every lambda_ac case, JSON-native."""
    block: dict[str, object] = {
        "conditioning_grid_m_msl": np.asarray(grid, dtype=float).tolist()
    }
    for lambda_ac_m in LAMBDA_AC_CASES_M:
        n_eff = n_eff_for(lambda_ac_m)
        case: dict[str, object] = {"n_eff": n_eff}
        for name, curve in curves.items():
            case[name] = np.asarray(
                upscale_length_effect(np.asarray(curve, dtype=float), n_eff),
                dtype=float,
            ).tolist()
        block[f"lambda_ac_{lambda_ac_m:g}m"] = case
    return block


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    entries: dict[str, object] = {}

    for path in sorted(RESULTS.glob("tokachi_*_historical_*.h5")):
        if path.name.endswith(".raw.h5"):
            continue
        result = FragilityResult.load(path)
        entries[path.name] = upscaled_block(
            result.conditioning_grid,
            {
                "p_f_static_raw": result.P_f_static_raw,
                "p_f_trans_raw": result.P_f_trans_raw,
            },
        )

    phase2_dir = RESULTS / "phase2"
    if phase2_dir.exists():
        for path in sorted(phase2_dir.glob("*_posterior.h5")):
            posterior = PosteriorResult.load(path)
            entries[f"phase2/{path.name}"] = upscaled_block(
                posterior.fragility.conditioning_grid,
                {
                    "p_f_static_post_raw": posterior.fragility.P_f_static_post_raw,
                    "p_f_trans_post_raw": posterior.fragility.P_f_trans_post_raw,
                },
            )

    payload = {
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "adr": "ADR-0037",
        "segment_length_m": SEGMENT_LENGTH_M,
        "lambda_ac_cases_m": list(LAMBDA_AC_CASES_M),
        "note": (
            "Weakest-link segment upscaling of persisted cross-section raw "
            "curves; primary lambda_ac = 250 m gives n_eff = 1 (identity) — "
            "the ADR-0037 finding. Bracket cases are conservative "
            "sensitivities, never the deliverable."
        ),
        "results": entries,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT_JSON.relative_to(REPO)} ({len(entries)} result files)")

    # Compact console table: worst-case amplification at the governing
    # sections' shoulder (the max raw transient P_f below 0.5).
    print(
        f"\n{'file':52s} {'branch':9s} {'P_cs(shoulder)':>14s} "
        f"{'seg@100m':>10s} {'seg@40m':>10s}"
    )
    for name, block in entries.items():
        for branch in ("p_f_trans_raw", "p_f_trans_post_raw"):
            base = block.get("lambda_ac_250m", {}).get(branch)  # type: ignore[union-attr]
            if base is None:
                continue
            arr = np.asarray(base, dtype=float)
            shoulder = arr[(arr > 0.0) & (arr < 0.5)]
            if shoulder.size == 0:
                continue
            p = float(shoulder.max())
            row100 = 1.0 - (1.0 - p) ** 2.0
            row40 = 1.0 - (1.0 - p) ** 5.0
            print(f"{name:52s} {branch[4:9]:9s} {p:14.5f} {row100:10.5f} {row40:10.5f}")


if __name__ == "__main__":
    main()
