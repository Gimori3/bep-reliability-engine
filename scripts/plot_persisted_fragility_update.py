"""Redraw prior and posterior fragility from persisted results without replay.

Run from the repository root::

    python scripts/plot_persisted_fragility_update.py
    python scripts/plot_persisted_fragility_update.py --sections kp58_8

Only figures are written. The toe and survived peak are read from the parent
and posterior sidecars, respectively; no hydraulic datum is retyped here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bayesian_reliability_updating import plots  # noqa: E402
from bayesian_reliability_updating.posterior import PosteriorResult  # noqa: E402

SECTIONS = {"kp58_8": "58.8", "kp60_0": "60.0"}


def redraw(section: str) -> Path:
    """Render one of the promoted baseline strata from its saved posterior."""
    kp = SECTIONS[section]
    stem = f"tokachi_kp{kp}_historical_matrix"
    path = REPO / "results/phase2" / f"{stem}_posterior.h5"
    posterior = PosteriorResult.load(path)
    side = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    parent = Path(side["phase1"]["path"].replace("\\", "/"))
    if not parent.is_absolute():
        parent = REPO / parent
    parent_side = json.loads(parent.with_suffix(".json").read_text(encoding="utf-8"))
    toe = float(parent_side["config"]["geometry"]["z_toe"])
    peak = float(side["phase2"]["event_chain"][-1]["record"]["peak_m_msl"])
    return plots.plot_fragility_update(
        posterior.fragility.conditioning_grid,
        posterior.P_f_trans_prior_raw,
        posterior.P_f_static_prior_raw,
        posterior.fragility,
        REPO / "results/phase2/figures" / f"{stem}_fragility_update.png",
        z_toe_m=toe,
        event_peak_m=peak,
        title=f"Prior and posterior fragility at KP {kp}",
        publication_path=REPO
        / "docs/figures"
        / f"phase2_fragility_update_{section}_matrix.png",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sections", nargs="+", choices=SECTIONS, default=list(SECTIONS)
    )
    args = parser.parse_args()
    for section in args.sections:
        print(f"wrote {redraw(section)}")


if __name__ == "__main__":
    main()
