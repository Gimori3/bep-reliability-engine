"""Pins the first-breach shares of the alternative readings (ADR-0058).

Reads only the committed evidence record ``first-breach-alternatives-study.json``
and the adopted table it must agree with; no gitignored result is touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "docs" / "decisions" / "first-breach-alternatives-study.json"
ADOPTED = REPO / "docs" / "decisions" / "drained-section-conditioning-adopted.json"
CELLS = [
    f"{sc} KP {kp}"
    for sc in ("historical", "+4K")
    for kp in ("57.4", "58.8", "60.0", "62.0")
]


@pytest.fixture(scope="module")
def ev() -> dict:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_every_gate_passed(ev: dict) -> None:
    gates = ev["gates"]
    assert gates["adopted_retrace_reproduces_committed_time_order"] is True
    assert gates["adopted_table_reproduced"] is True
    assert gates["hazard_cache_unchanged"] is True
    assert all(g["committed_system_reproduced"] for g in gates["arms"].values())


def test_the_adopted_cells_equal_the_adopted_table(ev: dict) -> None:
    table = json.loads(ADOPTED.read_text(encoding="utf-8"))["table"]
    for cell in CELLS:
        mine = ev["cells"][f"adopted {cell}"]
        assert mine["first_breach_share_bep"] == pytest.approx(
            table[cell]["first_breach_share_bep"], rel=1e-5
        )
        assert mine["p_system"] == pytest.approx(table[cell]["p_system"], rel=1e-5)


def test_no_alternative_changes_its_leader_between_the_two_shares(ev: dict) -> None:
    """The ADR-0058 finding: the measure moves values, not orderings."""
    for arm, rec in ev["orderings"].items():
        for cell, v in rec.items():
            assert v["first_breach"] == v["summed"], (arm, cell)


def test_the_thesis_counts_hold_on_the_first_breach_share(ev: dict) -> None:
    o = ev["orderings"]
    bulk_overflow = [c for c in CELLS if o["bulk"][c]["first_breach"] == "overflow"]
    # 5 before ADR-0059 (2026-10-17): KP 57.4 +4K is now piping-led (0.54).
    assert len(bulk_overflow) == 4
    half = [c for c in CELLS if o["credit_half"][c]["first_breach"] == "piping"]
    assert half == []
    gravel = [c for c in CELLS if o["gravel_x1.80"][c]["first_breach"] == "piping"]
    assert len(gravel) == 6
    field = [c for c in CELLS if o["k_aq_field_geomean"][c]["first_breach"] == "piping"]
    assert field == []


def test_the_kp62_warming_cell(ev: dict) -> None:
    c = ev["cells"]
    assert round(c["adopted +4K KP 62.0"]["first_breach_share_bep"], 2) == 0.39
    assert (
        round(c["k_aq_regional_upper +4K KP 62.0"]["first_breach_share_bep"], 2) == 0.99
    )
    assert round(c["steady_state +4K KP 62.0"]["first_breach_share_bep"], 2) == 0.90
    assert round(c["lambda_ac_100 +4K KP 62.0"]["first_breach_share_bep"], 2) == 0.56
    assert round(c["lambda_ac_40 +4K KP 62.0"]["first_breach_share_bep"], 2) == 0.78
    assert (
        round(c["seepage_tail_0.85 +4K KP 62.0"]["first_breach_share_bep"], 2) == 0.24
    )


def test_the_resistance_ladder_break_even(ev: dict) -> None:
    be = ev["resistance_ladder_break_even"]
    three = [
        be[f"{sc} KP {kp}"]["first_overflow_lead_at"]
        for sc in ("historical", "+4K")
        for kp in ("57.4", "58.8", "60.0")
    ]
    assert min(x for x in three if x) == 2.2
    assert max(x for x in three if x) == 2.7
