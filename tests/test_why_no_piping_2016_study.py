"""Pin the why-no-piping-in-2016 study (Pol comment 8).

Checked without rerunning anything:

* the committed record's own gates held: the closed-form 2016 gate and the
  blanket identity reproduced every stored initiation flag, an M8 replay of
  2016 reproduced the persisted breach and initiation flags at all four
  sections, and the design-grid transient and same-head columns were
  reproduced before any arm was evaluated;
* the arithmetic from the OYO (1999) forms: the 2016 heads against OYO's 1998
  levels and OYO's toe gradients scaled to them, recomputed here from the
  constants of the driver;
* the structure the thesis relies on: every four-way outcome sums to one, no
  breach lies outside same-head failure, a diagnostic that only divides the
  toe pressure never opens more exits than the adopted gate, and the
  pre-registered verdicts are the ones the study note reports.

Driver ``scripts/why_no_piping_2016_study.py``; evidence
``docs/decisions/why-no-piping-2016-study.{md,json}``. Every path read here is
tracked, so nothing skips (conventions section 9.4).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "docs" / "decisions" / "why-no-piping-2016-study.json"
KPS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def driver():
    path = REPO / "scripts" / "why_no_piping_2016_study.py"
    spec = importlib.util.spec_from_file_location("why_no_piping_2016_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_record_stays_small(record) -> None:
    assert RECORD.stat().st_size < 200_000


def test_gates_held(record) -> None:
    for key, gate in record["gate"].items():
        assert gate["closed_form_initiation_mismatches"] == 0, key
        assert gate["blanket_identity_mismatches"] == 0, key
        if key.startswith("undrained"):
            assert gate["replay_breach_mismatches"] == 0, key
            assert gate["replay_initiation_mismatches"] == 0, key
    assert set(record["gate"]) == {
        *(f"undrained {kp}" for kp in KPS),
        "berm KP 58.8",
        "berm KP 60.0",
    }


def test_oyo_arithmetic(record, driver) -> None:
    src = record["sources"]
    for kp in (57.4, 58.8, 60.0, 62.0):
        e = src[f"KP {kp}"]
        ratio = (driver.PEAK_2016[kp] - driver.Z_TOE[kp]) / (
            driver.OYO_LEVEL[kp] - driver.Z_TOE[kp]
        )
        assert e["head_ratio_2016_to_oyo"] == pytest.approx(ratio, rel=1e-5)
        iv = driver.OYO_GRADIENT[kp][0] * ratio
        assert e["oyo_iv_scaled_2016"] == pytest.approx(iv, rel=1e-5)
        hours = driver.hours_above(driver.OYO_WAVEFORM[kp], driver.Z_TOE[kp])
        assert e["oyo_waveform_hours_above_toe"] == pytest.approx(hours, rel=1e-4)
    # The quoted reading: scaled to the 2016 heads, only KP 58.8 exceeds
    # OYO's 0.5 criterion or the cover's heave gradient.
    over = [k for k in KPS if src[k]["oyo_iv_2016_exceeds_criterion"]]
    heave = [k for k in KPS if src[k]["oyo_iv_2016_exceeds_heave"]]
    assert over == ["KP 58.8"] and heave == ["KP 58.8"]
    # 2016 was lower and shorter above the toe than OYO's design flood at the
    # three sections OYO flagged.
    hours_2016 = {"KP 58.8": 21.0, "KP 60.0": 28.0, "KP 62.0": 6.0}
    for k, h in hours_2016.items():
        assert src[k]["peak_minus_oyo_m"] < 0.0
        assert src[k]["oyo_waveform_hours_above_toe"] > h


def _check_outcome(o: dict) -> None:
    parts = [o["no_exit"], o["exit_stalls_below_H_c"], o["same_head_static_failure"]]
    assert sum(parts) == pytest.approx(1.0, abs=1e-5)
    if o["breach"] is not None:
        assert o["breach"] <= o["same_head_static_failure"] + 1e-9
        assert o["held_only_by_duration"] + o["breach"] == pytest.approx(
            o["same_head_static_failure"], abs=1e-5
        )


def test_outcomes_are_consistent(record) -> None:
    for key, arms in record["exits"].items():
        adopted = arms["adopted"]
        for name, o in arms.items():
            if not isinstance(o, dict):
                continue
            _check_outcome(o)
            # Every arm only lowers the toe pressure or raises the weight, so
            # none opens more exits than the adopted gate.
            assert o["exit"] <= adopted["exit"] + 1e-9, (key, name)
    for key, o in record["replay_oyo_matched"].items():
        _check_outcome(o)
        closed = record["exits"][f"undrained {key}"]["OYO-matched toe pressure"]
        assert o["exit"] == closed["exit"], key


def test_design_grid_consequence(record) -> None:
    des = record["design_grid_oyo_matched"]
    for key, d in des.items():
        assert d["P_trans_oyo"] <= d["P_static_oyo"] + 1e-12, key
        assert d["P_trans_oyo"] <= d["P_trans_adopted"] + 1e-12, key
    assert des["KP 60.0"]["k_trans_oyo"] == 81
    assert des["KP 58.8"]["k_trans_adopted"] == 19736


def test_verdicts(record) -> None:
    v = record["verdicts"]
    held = {k: v[k]["held"] for k in v}
    assert held == {
        "P1": True,
        "P2": True,
        "P3": True,
        "P4": False,
        "P5": True,
        "P6": True,
    }
