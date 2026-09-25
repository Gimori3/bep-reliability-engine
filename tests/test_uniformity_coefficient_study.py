"""Pin the uniformity-coefficient study (Green Light item 1).

Three things are checked, none of which reruns a sweep:

* the bedding-angle route is an EXACT multiplier on the Sellmeijer resistance
  factor, equal to substituting the uniformity coefficient itself, so the arms
  measured the uniformity term and nothing else;
* the internal-stability block of the committed record is reproduced from the
  tracked gradation transcription, and the robust bound never lies below the
  reconstructed value (it is an upper bound over every consistent curve);
* the committed record's own gates held and the measured direction is pinned:
  the uniformity term raises B and lowers delta-beta, so it cancels in neither
  metric. The thesis states that direction; a regression would make it false.

Driver ``scripts/uniformity_coefficient_study.py``; evidence
``docs/decisions/uniformity-coefficient-study.{md,json}``. Every path here is
tracked, so nothing skips (conventions section 9.4).
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

from bep_reliability_engine import sellmeijer

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "docs" / "decisions" / "uniformity-coefficient-study.json"


def _driver():
    sys.path.insert(0, str(REPO / "scripts"))
    path = REPO / "scripts" / "uniformity_coefficient_study.py"
    spec = importlib.util.spec_from_file_location("uniformity_coefficient_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def driver():
    return _driver()


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.mark.parametrize("cu", [1.3, 2.6, 4.47, 5.44, 42.06, 65.7])
def test_bedding_angle_route_equals_the_uniformity_term(driver, cu):
    theta = math.radians(driver.theta_for_factor(driver.factor_for_cu(cu)))
    via_theta = sellmeijer._factor_Fr(theta_repose_rad=theta)
    via_cu = sellmeijer._factor_Fr(uniformity_cu=cu)
    assert via_theta == pytest.approx(via_cu, rel=1e-14)


def test_tested_maximum_moves_critical_head_by_under_five_per_cent(driver):
    assert driver.factor_for_cu(2.6) == pytest.approx(1.0482, abs=1e-4)
    assert driver.factor_for_cu(1.3) == pytest.approx(0.9579, abs=1e-4)


def test_internal_stability_reproduces_the_record(driver, record):
    fresh = json.loads(json.dumps(driver.internal_stability()))
    assert fresh == record["internal_stability"]


def test_robust_bound_is_never_below_the_reconstruction(record):
    for spec in record["internal_stability"]["specimens"]:
        for window in spec["kenney_lau"].values():
            if window is None:
                continue
            assert window["hf_min_upper_bound"] >= window["hf_min_interpolated"] - 1e-9


def test_stability_counts(record):
    s = record["internal_stability"]["summary"]
    assert (s["n_gravel_supported"], s["n_sand_rich"]) == (24, 4)
    assert s["gravels_unstable_interpolated"] == 24
    assert s["gravels_unstable_robust"] == 9
    assert s["sand_window_post_hoc"]["gravels_unstable_interpolated"] == 21
    assert s["sand_window_post_hoc"]["gravels_unstable_robust"] == 8
    assert s["sand_window_post_hoc"]["sand_rich_unstable_interpolated"] == 0
    assert s["finer_fraction_below"] == {"25": 5, "35": 18}


def test_gates_held(record):
    p3 = record["phase3"]
    assert p3["gate_persisted_baseline"]["passed"]
    assert p3["gate_in_memory_baseline"]["passed"]
    assert p3["non_bep_segments_untouched"]
    for rec in record["phase1"]["sections"].values():
        for arm in rec["arms"].values():
            assert all(v == 0 for v in arm["monotonicity"].values())


def test_uniformity_term_cancels_in_neither_metric(record):
    """B rises and delta-beta falls at every resolved quotable level."""
    for rec in record["phase1"]["sections"].values():
        for arm in rec["arms"].values():
            for level in arm["levels"]:
                if not level["quotable"]:
                    continue
                if level["delta_delta_beta_resolved"]:
                    assert level["delta_delta_beta"] < 0.0
                if level["rho_resolved"]:
                    assert level["rho"] > 1.0


def test_only_the_whole_grading_arm_reverses_an_ordering(record):
    assert record["phase3"]["reversals"] == {
        "cap": [],
        "sand": [],
        "matrix": ["KP 62.0 historical"],
    }
