"""Q1 of the hazard-sampling study on the adopted conditioning.

``scripts/annualisation_uncertainty_study.py`` answers its pre-registered Q1 (are
the four per-section climate ratios resolvably different from one another?) on
its primary arm, the matrix posterior at all four sections. Since ADR-0056 the
adopted conditioning keeps the prior at the drained sections, KP 58.8 and
KP 60.0, so the thesis's statement of which pairs separate rests on a different
mix. This driver repeats Q1 on that mix: matrix posterior at KP 57.4 and 62.0,
matrix prior at KP 58.8 and 60.0.

It reuses the study's own functions, seed, replicate count and member-block draw
stratified within the SST patterns. One block draw per scenario serves both arms
and all nodes, so every pairwise difference is paired exactly as in the study.
Nothing persisted is changed; the record is written to ``--out``.

Usage:
    python scripts/climate_ratio_pairs_adopted.py
        [--out docs/decisions/climate-ratio-pairs-adopted.json]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
STUDY = REPO / "scripts" / "annualisation_uncertainty_study.py"
DEFAULT_OUT = REPO / "docs" / "decisions" / "climate-ratio-pairs-adopted.json"
REPLICATES = 10_000
ADOPTED = {
    57.4: ("matrix", "posterior"),
    58.8: ("matrix", "prior"),
    60.0: ("matrix", "prior"),
    62.0: ("matrix", "posterior"),
}


def _load_study():
    spec = importlib.util.spec_from_file_location("aus", STUDY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    aus = _load_study()
    campaign = aus._load_campaign_module()
    context = aus.build_context(campaign)
    event_ids = {
        scenario: [
            event.event_id
            for event in context["hazards"][scenario][("Tokachi", 58.8)].events
        ]
        for scenario in campaign.SCENARIOS
    }

    per_event = {}
    for d70, source in sorted(set(ADOPTED.values())):
        rows, values = aus.annualise_arm(campaign, context, d70, source)
        per_event[aus._arm_key(d70, source)] = (rows, values)

    rng = np.random.default_rng(aus.SEED)
    draws = {}
    for scenario in campaign.SCENARIOS:
        labels = aus.block_labels(event_ids[scenario], "member")
        index, n_blocks, _ = aus.block_index(labels)
        multiplicities = aus.draw_multiplicities_stratified(
            aus.stratum_columns(event_ids[scenario]), n_blocks, REPLICATES, rng
        )
        draws[scenario] = (index, n_blocks, multiplicities)

    samples, points = {}, {}
    for kp, (d70, source) in ADOPTED.items():
        rows, values = per_event[aus._arm_key(d70, source)]
        system = {}
        for scenario in campaign.SCENARIOS:
            index, n_blocks, multiplicities = draws[scenario]
            system[scenario] = aus.node_replicates(
                values[("Tokachi", kp, scenario)],
                index,
                n_blocks,
                multiplicities,
                len(event_ids[scenario]),
            )["__system__"]
        label = aus._label(kp)
        samples[label] = aus.ratio_series(system["historical"], system["+4K"])
        historical = rows[("Tokachi", kp, "historical")]["p_annual_system"]
        warming = rows[("Tokachi", kp, "+4K")]["p_annual_system"]
        points[label] = warming / historical

    record = {
        "study": "climate-ratio-pairs-adopted",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generated_by": "scripts/climate_ratio_pairs_adopted.py",
        "parent": "docs/decisions/annualisation-hazard-sampling-uncertainty.md, Q1",
        "conditioning": {aus._label(kp): "/".join(arm) for kp, arm in ADOPTED.items()},
        "seed": int(aus.SEED),
        "replicates": REPLICATES,
        "scope": (
            "hazard-sampling uncertainty only: the finite-ensemble spread of the "
            "d4PDF peak-stage distribution with the fragility curves held fixed"
        ),
        "climate_ratio_points": points,
        "q1": aus.answer_q1(samples, points),
    }
    args.out.write_text(json.dumps(record, indent=1, default=float) + "\n")
    print(record["q1"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
