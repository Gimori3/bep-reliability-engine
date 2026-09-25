"""Gate for the Green Light item 2 study (criterion consequence and 2016 evidence).

Reads only the tracked evidence record, so it runs on a fresh clone. What it
pins: the two theorems the study relies on (static dominates transient before
any update; a survival can only favour the transient criterion), the arithmetic
that turns the published rejections into likelihood ratios, the gates the driver
enforced when it ran, and the handful of numbers the thesis quotes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import criterion_consequence_study as study  # noqa: E402

RECORD = REPO_ROOT / "docs/decisions/criterion-consequence-and-2016-evidence-study.json"
KPS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")
SCENARIOS = ("historical", "+4K")


@pytest.fixture(scope="module")
def record() -> dict:
    assert RECORD.is_file(), "tracked evidence record missing"
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_crack_reduced_rule_is_the_static_margin_plus_the_decrement() -> None:
    names = ["k_aq", "D_bl"]
    arrays = {
        "theta": np.array([[1e-3, 0.8], [1e-3, 0.8], [1e-3, 0.5]]),
        "param_names": names,
        # margins: fails gross by less than the decrement, fails by more, exact
        "Z_static": np.array([-0.2, -0.3, -0.15]),
    }
    accept = study._crack_reduced_accept(arrays)
    # 0.3 * 0.8 = 0.24: -0.2 + 0.24 > 0 survives; -0.3 + 0.24 < 0 fails;
    # 0.3 * 0.5 = 0.15: -0.15 + 0.15 = 0 is failure (ADR-0008 boundary).
    assert accept.tolist() == [True, False, False]


def test_every_run_gate_passed(record: dict) -> None:
    gates = record["annual"]["gates"]
    assert gates["gate_1"]["passed"] and gates["gate_1"]["rows_compared"] == 912
    assert gates["gate_2"]["passed"] and gates["hazard_cache_unchanged"]


def test_no_static_survivor_fails_transiently(record: dict) -> None:
    """The nesting theorem, on every stratum and on the measured berm."""
    for entry in record["evidence"]["per_stratum"].values():
        assert entry["nesting"]["static_survivors_failing_transient"] == 0
        assert entry["nesting"]["crack_reduced_survivors_failing_transient"] == 0
    for entry in record["evidence"]["berm"].values():
        assert entry["static_survivors_failing_transient"] == 0


def test_a_survival_can_only_favour_the_transient_criterion(record: dict) -> None:
    for entry in record["evidence"]["per_stratum"].values():
        assert entry["LR_transient_over_static"]["point"] >= 1.0
    for section in record["hypothetical"].values():
        for level in section["levels"]:
            if level["LR_one_survival"] is not None:
                assert level["LR_one_survival"] >= 1.0 - 1e-12
            breach = level["LR_one_breach_transient_over_static"]
            if breach is not None:
                assert breach <= 1.0 + 1e-12


def test_likelihood_ratio_is_the_published_rejections(record: dict) -> None:
    kp588 = record["evidence"]["per_stratum"]["KP 58.8 matrix"]
    rej = kp588["rejection_fraction"]
    # The published re-based production rejections (docs/phase2_report.md).
    assert rej["transient"] == pytest.approx(0.03813, abs=1e-12)
    assert rej["static_gross"] == pytest.approx(0.45217, abs=1e-12)
    assert kp588["LR_transient_over_static"]["point"] == pytest.approx(
        (1 - 0.03813) / (1 - 0.45217)
    )
    assert round(kp588["LR_transient_over_static"]["point"], 2) == 1.76
    kp600 = record["evidence"]["per_stratum"]["KP 60.0 matrix"]
    assert round(kp600["LR_transient_over_static"]["point"], 2) == 1.14


def test_joint_bounds_are_ordered_by_dependence(record: dict) -> None:
    joint = record["evidence"]["joint"]["transient over static_gross"]
    como = joint["comonotone (maximal positive dependence)"]["LR"]
    ind = joint["independent"]["LR"]
    lower = joint["Frechet lower (maximal negative dependence)"]["LR"]
    assert como <= ind <= lower
    assert lower < 2.5  # pre-registered E2


def test_disagreement_about_2016_is_duration_not_initiation(record: dict) -> None:
    for kp in ("KP 58.8", "KP 60.0"):
        nest = record["evidence"]["per_stratum"][f"{kp} matrix"]["nesting"]
        assert nest["disagreeing_rows_gate_opened"] / nest["disagreeing_rows"] > 0.99


def test_static_dominates_transient_before_any_update(record: dict) -> None:
    """Pre-registered A1: pointwise curve dominance survives the annualisation."""
    branches = record["annual"]["matrix"]["branches"]
    for scenario in SCENARIOS:
        for kp in KPS:
            s = branches["S-prior"][scenario][kp]
            t = branches["T-prior"][scenario][kp]
            assert s["p_annual_system"] >= t["p_annual_system"]
            assert s["share_bep"] >= t["share_bep"]


def test_transient_posterior_is_the_published_deliverable(record: dict) -> None:
    """The production numbers Chapter 7 prints (Table 7.2)."""
    t = record["annual"]["matrix"]["branches"]["T-post"]
    printed = {
        ("KP 57.4", "historical"): 4.98e-4,
        ("KP 58.8", "historical"): 6.18e-3,
        ("KP 60.0", "historical"): 3.15e-4,
        ("KP 62.0", "historical"): 9.17e-4,
        ("KP 58.8", "+4K"): 3.57e-2,
        ("KP 62.0", "+4K"): 1.23e-2,
    }
    for (kp, scenario), value in printed.items():
        assert t[scenario][kp]["p_annual_system"] == pytest.approx(value, rel=5e-3)


def test_the_figure_is_declared() -> None:
    import production_campaign as pc

    entries = [
        d
        for d in pc.FIGURE_DRIVERS
        if "criterion_survival_evidence.png" in d["produces"]
    ]
    assert len(entries) == 1
    assert "scripts/criterion_consequence_study.py" in entries[0]["command"]
    assert (REPO_ROOT / "docs/figures/criterion_survival_evidence.png").is_file()
