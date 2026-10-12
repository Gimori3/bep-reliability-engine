"""Gate for the time-effect-in-proportion study (Pol round 2, A24 with A10).

The driver reads only committed evidence JSON, so every check here runs on a
fresh clone: the collation reproduces the tracked study JSON, every row's
baseline is the adopted annual value, the criterion row equals the
time-dependence study's annual comparison, and the pre-registered verdicts are
the ones the thesis quotes.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "time_effect_in_proportion.py"
EVIDENCE = REPO / "docs" / "decisions" / "time-effect-in-proportion-study.json"


def _module():
    spec = importlib.util.spec_from_file_location("time_effect_in_proportion", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["time_effect_in_proportion"] = mod
    spec.loader.exec_module(mod)
    return mod


TEP = _module()


@pytest.fixture(scope="module")
def record() -> dict:
    return TEP._round(TEP.build())


def test_collation_reproduces_the_tracked_evidence(record: dict) -> None:
    tracked = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert tracked == json.loads(json.dumps(record))


def test_criterion_row_is_the_time_dependence_studys_annual_ratio(
    record: dict,
) -> None:
    tdf = json.loads(
        (REPO / "docs" / "decisions" / "time-dependence-factor-study.json").read_text(
            encoding="utf-8"
        )
    )
    paired = tdf["annual"]["matrix"]["paired_comparisons"]["I-prior / T-prior"]
    for c in TEP.CLIMATES:
        for s in TEP.SECTIONS:
            assert math.isclose(
                record["factors"]["criterion_steady_state"][c][s],
                paired[f"{s} {c} system"]["point"],
                rel_tol=1e-5,
            )


def test_historical_time_effect_is_the_thesis_range(record: dict) -> None:
    te = record["factors"]["criterion_steady_state"]["historical"]
    assert round(min(te.values()), 1) == 1.8
    assert round(max(te.values()), 1) == 3.3


def test_conductivity_spans_are_the_thesis_values(record: dict) -> None:
    span = record["conductivity_span"]["historical"]
    assert span["KP 57.4"] is None and span["KP 60.0"] is None
    assert round(span["KP 58.8"]) == 165
    assert round(span["KP 62.0"]) == 66


def test_drain_rows_exist_only_at_the_drained_sections(record: dict) -> None:
    for key in ("drain_berm_inert", "drain_berm_relief80"):
        for c in TEP.CLIMATES:
            row = record["factors"][key][c]
            assert row["KP 57.4"] is None and row["KP 62.0"] is None
            assert row["KP 58.8"] is not None and row["KP 60.0"] is not None


def test_every_preregistered_prediction_held(record: dict) -> None:
    assert [p for p, v in record["verdicts"].items() if not v["holds"]] == []
    assert sorted(record["verdicts"]) == ["P1", "P2", "P3", "P4", "P5", "P6"]


def test_figure_is_declared_in_figure_drivers() -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import production_campaign

    owners = [
        d
        for d in production_campaign.FIGURE_DRIVERS
        if TEP.FIGURE_NAME in d.get("produces", [])
    ]
    assert len(owners) == 1
