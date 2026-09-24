"""Pins for the drained-sections scope study (2026-09-24).

The committed record ``docs/decisions/drained-sections-scope-study.json`` is
checked against the tracked evidence it was assembled from, never against
itself: the ADR-0050 Phase 1 and Phase 3 records and the hazard-sampling
record. Those are asserted, never skipped (``docs/conventions.md`` section 9.4).
The one part that reads untracked Phase 2 sidecars is re-derived only when they
are present.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import drained_sections_scope_study as study  # noqa: E402

RECORD = REPO / "docs/decisions/drained-sections-scope-study.json"
PHASE1 = REPO / "docs/decisions/adr0050-drained-configuration-bracket.json"
HAZARD = REPO / "docs/decisions/annualisation-hazard-sampling-uncertainty.json"
RESULTS = REPO / "results"


def _load(path: Path) -> dict:
    assert path.exists(), f"tracked file missing: {path.relative_to(REPO)}"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def record() -> dict:
    return _load(RECORD)


def test_annual_part_is_the_tracked_phase3_record(record: dict) -> None:
    assert record["annual"] == json.loads(json.dumps(study.annual_part()))


def test_design_level_probabilities_match_the_phase1_bracket(record: dict) -> None:
    phase1 = _load(PHASE1)
    names = {"KP 58.8": "KP58.8", "KP 60.0": "KP60.0"}
    for section, block in record["design"].items():
        entry = next(
            s
            for s in phase1["sections"]
            if s["section"] == names[section] and s["d70_interpretation"] == "matrix"
        )
        stage = block["grid_stage_m"]
        for arm, row in block["arms"].items():
            if arm == "gate":
                level = next(
                    lv
                    for lv in entry["arms"]["berm_only"]["levels"]
                    if abs(lv["stage_m_msl"] - stage) < 1e-9
                )
                assert row["p_static"] == pytest.approx(level["p_f_static_baseline"])
                assert row["p_transient"] == pytest.approx(level["p_f_trans_baseline"])
                continue
            level = next(
                lv
                for lv in entry["arms"][arm]["levels"]
                if abs(lv["stage_m_msl"] - stage) < 1e-9
            )
            assert row["p_static"] == pytest.approx(level["p_f_static_arm"])
            assert row["p_transient"] == pytest.approx(level["p_f_trans_arm"])


def test_delta_beta_is_the_index_difference_of_the_recorded_probabilities(
    record: dict,
) -> None:
    for block in record["design"].values():
        gate = block["arms"]["gate"]["delta_beta"]
        for arm, row in block["arms"].items():
            if row["transient_failures"] == 0:
                assert row["delta_beta"] is None
                continue
            expected = -norm.ppf(row["p_transient"]) + norm.ppf(row["p_static"])
            assert row["delta_beta"] == pytest.approx(expected, abs=1e-12)
            lo, hi = row["delta_beta_ci95"]
            assert lo <= row["delta_beta"] <= hi
            if arm != "gate":
                assert row["delta_beta_shift_from_as_if_undrained"] == pytest.approx(
                    row["delta_beta"] - gate, abs=1e-12
                )


def test_the_berm_moves_the_index_little_and_the_ratio_a_lot(record: dict) -> None:
    """The finding the thesis quotes: shift below 0.1 index, B up 1.6 to 2.3 times."""
    for block in record["design"].values():
        gate, berm = block["arms"]["gate"], block["arms"]["berm_only"]
        assert abs(berm["delta_beta_shift_from_as_if_undrained"]) < 0.1
        assert 1.6 < berm["ratio_B"] / gate["ratio_B"] < 2.3
        lo, hi = berm["shift_ci95"]
        assert hi < 0.0


def test_as_if_undrained_intervals_reproduce_the_published_record(record: dict) -> None:
    hazard = _load(HAZARD)
    ranking = record["ranking_intervals"]
    for scenario in ("historical", "+4K"):
        for section, value in ranking[scenario]["as_if_undrained"]["values"].items():
            published = hazard["sections"][section]["matrix/posterior"][scenario][
                "p_annual_system"
            ]
            for key in ("point", "ci_low", "ci_high"):
                assert value[key] == pytest.approx(published[key], rel=1e-9)
    for section, ratio in ranking["climate_ratio"]["as_if_undrained"].items():
        published = hazard["sections"][section]["matrix/posterior"]["climate_ratio"]
        assert ratio["point"] == pytest.approx(published["point"], rel=1e-9)
        assert ratio["ci95"][0] == pytest.approx(published["ci_low"], rel=1e-9)
        assert ratio["ci95"][1] == pytest.approx(published["ci_high"], rel=1e-9)


def test_the_berm_reading_ranking_statement_is_the_resolved_one(record: dict) -> None:
    """KP 60.0 falls below KP 62.0 in every resample; last only under warming."""
    ranking = record["ranking_intervals"]
    hist = ranking["historical"]["berm_only"]
    warm = ranking["+4K"]["berm_only"]
    assert hist["rank_frequency"]["KP 58.8"]["1"] == 1.0
    assert warm["rank_frequency"]["KP 58.8"]["1"] == 1.0
    assert hist["pairwise"]["KP 60.0 / KP 62.0"]["fraction_a_above_b"] == 0.0
    assert warm["rank_frequency"]["KP 60.0"]["4"] == 1.0
    assert 0.5 < hist["rank_frequency"]["KP 60.0"]["4"] < 0.95
    assert hist["pairwise"]["KP 57.4 / KP 60.0"]["ci95"][0] < 1.0


def test_survival_part_reproduces_from_the_sidecars(record: dict) -> None:
    if not (RESULTS / "phase2").is_dir():
        pytest.skip("untracked results/ absent (fresh clone)")
    assert record["survival"] == json.loads(json.dumps(study.survival_part(RESULTS)))


def test_survival_rejections_are_the_corrected_gauge_values(record: dict) -> None:
    rows = record["survival"]
    assert math.isclose(
        rows["KP 58.8"]["as_if_undrained"]["rejection_fraction"], 0.05512
    )
    assert math.isclose(
        rows["KP 60.0"]["as_if_undrained"]["rejection_fraction"], 0.03244
    )
    assert math.isclose(rows["KP 58.8"]["berm_only"]["rejection_fraction"], 0.01497)
    assert math.isclose(rows["KP 60.0"]["berm_only"]["rejection_fraction"], 0.00531)
