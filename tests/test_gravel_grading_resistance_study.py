"""Pin the gravel and grading resistance study (Pol comments 4 and 5).

Checked without rerunning a sweep:

* the bedding-angle route multiplies the Sellmeijer resistance factor, hence
  the single-source H_c, by exactly the ladder value, and the Dutch gravel
  factor of 1.8 is on the ladder;
* the committed record's own gates held: H_c scaled row for row, no row fails
  an arm without failing the baseline, the 2016 initiation indicator is
  unchanged by any multiplier, and the baseline annual rows reproduced the
  production table;
* the measured directions the thesis states: the index difference between the
  criteria falls at every shared count-qualified stage, the 2016 update and the
  piping share fall with the multiplier, and the quoted values hold.

Driver ``scripts/gravel_grading_resistance_study.py``; evidence
``docs/decisions/gravel-grading-resistance-study.{md,json}``. Every path read
here is tracked, so nothing skips (conventions section 9.4).
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
RECORD = REPO / "docs" / "decisions" / "gravel-grading-resistance-study.json"


def _driver():
    sys.path.insert(0, str(REPO / "scripts"))
    path = REPO / "scripts" / "gravel_grading_resistance_study.py"
    spec = importlib.util.spec_from_file_location("gravel_grading_study", path)
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


def test_record_stays_under_the_large_file_hook() -> None:
    assert RECORD.stat().st_size < 500_000


def test_dutch_gravel_factor_is_on_the_ladder(driver) -> None:
    assert driver.DUTCH_GRAVEL in driver.LADDER
    assert list(driver.LADDER) == sorted(driver.LADDER)


@pytest.mark.parametrize("c", [1.25, 1.5, 1.8, 2.2, 2.7])
def test_bedding_angle_route_is_an_exact_multiplier(driver, c) -> None:
    theta = math.radians(driver.theta_for(c))
    base = sellmeijer._factor_Fr()
    assert sellmeijer._factor_Fr(theta_repose_rad=theta) / base == pytest.approx(
        c, rel=1e-13
    )


def test_event_gates_held(record) -> None:
    for key, gate in record["gates"]["event"].items():
        assert gate["H_c_ratio_max_rel_dev"] < 1e-12, key
        nest = gate["nesting_violations"]
        assert nest["transient"] == 0 and nest["same_head"] == 0, key
        assert nest["gross_static"] == 0, key


def test_initiation_in_2016_does_not_read_the_critical_head(record) -> None:
    for sec in record["sections"].values():
        for arm, a in sec["arms"].items():
            if arm == "x1.00":
                continue
            assert a["evidence_2016"]["initiation_identical_to_baseline"]


def test_annual_gate_reproduced_the_production_table(record) -> None:
    gates = record["gates"]["annual"]
    assert gates["gate_iii"]["passed"] and gates["gate_iii"]["rows_compared"] > 0
    assert gates["hazard_cache_unchanged"]


def test_index_difference_falls_with_a_shared_resistance(record) -> None:
    for arm, summary in record["event_summary"]["by_arm"].items():
        assert summary["shared_qualified_levels"] > 0, arm
        assert summary["dbeta_fell_at_every_shared_level"], arm


def test_2016_rejection_never_rises_with_the_multiplier(record) -> None:
    for sec in record["sections"].values():
        rej = [a["evidence_2016"]["rejected_transient"] for a in sec["arms"].values()]
        assert all(b <= a + 1e-12 for a, b in zip(rej, rej[1:]))


def test_dutch_factor_values_quoted_in_the_thesis(record) -> None:
    """Chapter 5, 7, 8 and Appendix C.3 print these; a regression makes them false."""
    dg = record["event_summary"]["design_grid"]["KP 58.8"]["x1.80"]
    assert dg["k_transient"] == 464
    assert round(dg["P_transient"], 4) == 0.0046
    assert round(dg["P_same_head"], 4) == 0.0097
    assert round(dg["dbeta"], 2) == 0.26
    assert [round(x, 2) for x in dg["dbeta_ci95"]] == [0.24, 0.29]
    arm = record["event_summary"]["by_arm"]["x1.80"]
    assert [round(x, 2) for x in arm["delta_dbeta_range"]] == [-0.82, -0.39]
    assert [round(x, 2) for x in arm["F_td_factor_range"]] == [0.73, 1.53]
    ev = record["sections"]["KP 58.8"]["arms"]["x1.80"]["evidence_2016"]
    assert round(100 * ev["rejected_transient"], 3) == 0.037
    assert round(ev["LR_transient_over_same_head"], 3) == 1.002


def test_piping_keeps_the_lead_in_six_cells_at_the_dutch_factor(record) -> None:
    cells = record["annual"]["cells"]
    leads = {
        key: cells[f"x1.80 T-post {key}"]["leading"]
        for key in (
            f"{s} KP {kp}"
            for s in ("historical", "+4K")
            for kp in ("57.4", "58.8", "60.0", "62.0")
        )
    }
    assert sum(v == "piping" for v in leads.values()) == 6
    assert leads["historical KP 62.0"] == leads["+4K KP 62.0"] == "overflow"
    be = record["annual"]["break_even_posterior"]
    assert be["historical KP 62.0"]["first_change_at"] == 1.5
    assert be["historical KP 58.8"]["first_change_at"] == 2.2


def test_resistance_never_changes_the_2016_initiation(record) -> None:
    """The gate reads blanket pressure, not H_c: the 2016 initiation share is fixed."""
    for sec in record["sections"].values():
        shares = {a["evidence_2016"]["initiated_2016"] for a in sec["arms"].values()}
        assert len(shares) == 1
