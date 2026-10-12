"""Gate for the time-dependence factor study (ADR-0055).

The pure helpers are tested on constructed inputs, so they run anywhere. The
record checks read only the tracked evidence JSON, so they run on a fresh
clone: they pin the gates the driver enforced when it ran, the containment the
comparison rests on, and the numbers the thesis quotes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import time_dependence_factor_study as study  # noqa: E402

RECORD = REPO_ROOT / "docs/decisions/time-dependence-factor-study.json"


@pytest.fixture(scope="module")
def record() -> dict:
    assert RECORD.is_file(), "tracked evidence record missing"
    return json.loads(RECORD.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def test_paired_pair_point_values_match_their_definitions() -> None:
    rng = np.random.default_rng(1)
    a = rng.random(20000) < 0.3
    b = a & (rng.random(20000) < 0.4)  # nested, as the transient set is
    out = study.paired_pair(a, b, seed=3)
    pa, pb = a.mean(), b.mean()
    assert out["ratio"] == pytest.approx(pa / pb)
    assert out["dbeta"] == pytest.approx(norm.isf(pb) - norm.isf(pa))
    lo, hi = out["ratio_ci95"]
    assert lo < out["ratio"] < hi
    lo, hi = out["dbeta_ci95"]
    assert lo < out["dbeta"] < hi
    assert out["b_not_a"] == 0


def test_paired_pair_reports_no_ratio_without_failures() -> None:
    a = np.zeros(100, dtype=bool)
    a[:5] = True
    out = study.paired_pair(a, np.zeros(100, dtype=bool), seed=0)
    assert out["ratio"] is None and out["dbeta"] is None
    assert "ratio_ci95" not in out


def test_held_peak_traverse_matches_the_progression_kernel() -> None:
    """The quadrature agrees with the engine's own forward-Euler integration."""
    from bep_reliability_engine.hydraulics import InstantaneousHead
    from bep_reliability_engine.progression import integrate_progression

    h_c, l_c, length, c_e, k = 1.0, 2.5, 10.0, 0.05, 1e-3
    head = 1.2  # held erosion head above H_c
    t_quad = study.held_peak_traverse_s(
        np.array([head]),
        np.array([h_c]),
        np.array([l_c]),
        np.array([length]),
        np.array([c_e]),
        np.array([k]),
    )[0]
    dt = 5.0
    n = int(2.0 * t_quad / dt)
    # D_bl = 0 is the no-blanket configuration: no crack term, gate always open.
    result = integrate_progression(
        np.full(n, head),
        dt,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e,
        k,
        0.0,
        9.0,
        h_c,
        l_c,
        length,
        store_trajectory=True,
    )
    trajectory = np.asarray(result.l_trajectory_m).ravel()
    t_euler = (int(np.argmax(trajectory >= length - 1e-9))) * dt
    assert t_euler == pytest.approx(t_quad, rel=0.02)


def test_held_peak_traverse_is_infinite_below_the_critical_head() -> None:
    t = study.held_peak_traverse_s(
        np.array([0.9]),
        np.array([1.0]),
        np.array([2.5]),
        np.array([10.0]),
        np.array([0.05]),
        np.array([1e-3]),
    )
    assert np.isinf(t[0])


def test_pol_trapezoid_follows_the_published_base_duration() -> None:
    h = study.pol_trapezoid(4.0, 48.0, 3600.0)
    assert h.size == int(240 + 3 * 48) + 1  # D0 = 240 + 3 Dp hours, hourly
    assert h.max() == pytest.approx(4.0)
    assert (h == 4.0).sum() == 49  # the plateau of Dp hours, both ends included
    assert h[0] == 0.0 and h[-1] == pytest.approx(0.0)


def test_same_head_survival_needs_both_the_gate_and_the_head() -> None:
    arrays = {
        "Z_static": np.array([-0.5, -0.5, -0.1, 0.2]),
        "d_bl": np.array([0.5, 0.5, 0.5, 0.5]),
        "initiation": np.array([True, False, True, True]),
    }
    # crack term 0.15: -0.5 + 0.15 < 0 fails if the gate opened; -0.1 + 0.15 > 0
    # survives; a positive gross margin always survives.
    assert study._same_head_survival(arrays).tolist() == [False, True, True, True]


# --------------------------------------------------------------------------- #
# The record                                                                    #
# --------------------------------------------------------------------------- #
def test_record_stays_under_the_large_file_hook() -> None:
    assert RECORD.stat().st_size < 500_000


def test_gross_head_departures_reproduce_the_published_synthesis(record) -> None:
    rows = record["brackets"]["gross_reproduction_gate"]
    assert len(rows) == 32  # 8 published arms x 4 sections, z_toe arms included
    for row in rows:
        assert row["reproduced"] == pytest.approx(row["published"], rel=1e-4)
        assert row["reproduced_n_levels"] == row["published_n_levels"]


def test_annual_gates_passed(record) -> None:
    gates = record["annual"]["gates"]
    assert gates["gate_1"]["passed"] and gates["gate_1"]["rows_compared"] == 912
    assert gates["hazard_cache_unchanged"]


def test_containment_holds_on_every_matrix_sweep(record) -> None:
    """No transient failure outside the same-head set at N = 1e5 (the four
    matrix strata); the KP 57.4 N = 1e6 barrier jumps are the documented
    forward-Euler class, at most 0.14 % of transient failures at a level."""
    for kp in ("KP 58.8", "KP 60.0", "KP 62.0"):
        for lv in record["event"]["n1e5"][f"{kp} matrix"]["levels"]:
            assert lv["flips_C4b_not_C3b"] == 0
    for lv in record["event"]["n1e6"]["KP 57.4"]["levels"]:
        if lv["k_C4b"]:
            assert lv["flips_C4b_not_C3b"] <= 0.0015 * lv["k_C4b"]
    for entry in record["evidence"]["per_stratum"].values():
        assert entry["same_head_survivors_failing_transient"] == 0


def test_design_anchors_quoted_in_the_thesis(record) -> None:
    a = record["design_anchors"]
    kp62 = a["KP 62.0 design"]
    assert (kp62["k_same_head"], kp62["k_transient"]) == (350, 51)
    assert kp62["time_factor"]["ratio"] == pytest.approx(6.86, abs=0.01)
    assert kp62["time_factor"]["dbeta"] == pytest.approx(0.50, abs=0.005)
    assert (
        kp62["time_factor"]["ratio_quotable"] and kp62["time_factor"]["dbeta_quotable"]
    )
    assert a["KP 58.8 design grid"]["time_factor"]["dbeta"] == pytest.approx(
        0.72, abs=0.005
    )
    assert a["KP 60.0 design"]["time_factor"]["dbeta"] == pytest.approx(0.81, abs=0.005)
    resolved = a["KP 57.4 resolved"]
    assert resolved["time_factor"]["dbeta"] == pytest.approx(0.34, abs=0.005)
    design = a["KP 57.4 design"]
    assert (design["k_same_head"], design["k_transient"]) == (4, 2)
    assert design["bounds_union"]["dbeta_upper"] == pytest.approx(0.77, abs=0.005)


def test_survival_ratio_quoted_in_the_thesis(record) -> None:
    kp58 = record["evidence"]["per_stratum"]["KP 58.8 matrix"]
    assert kp58["LR_transient_over_same_head"] == pytest.approx(1.34, abs=0.005)
    assert kp58["LR_transient_over_gross_static"] == pytest.approx(1.76, abs=0.005)
    joint = record["evidence"]["joint"]
    assert joint["comonotone"] == pytest.approx(1.34, abs=0.005)
    assert joint["frechet_lower"] == pytest.approx(1.45, abs=0.005)


def test_appendix_brackets_quoted_in_the_thesis(record) -> None:
    """Thesis Appendix C.3 values on one head and gate (Tables C.5 and C.6)."""
    d = record["derived"]
    gain = d["pairing_variance_gain"]
    assert gain["n_levels"] == 53
    assert (round(gain["min"], 2), round(gain["max"], 2)) == (1.14, 2.48)
    mp = [
        round(d["single_branch_ratios"][f"{kp} m_p"]["same_head_ratio_max"], 2)
        for kp in ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")
    ]
    assert mp == [2.19, 2.24, 2.42, 2.22]
    matrix = d["uniformity"]["cu_matrix"]
    assert round(matrix["dbeta_displacement_min"], 2) == -0.63
    assert (
        round(matrix["time_factor_ratio_min"], 2),
        round(matrix["time_factor_ratio_max"], 2),
    ) == (0.79, 1.44)
    # Relief reaches both criteria through the shared gate, so the
    # as-if-undrained index difference sits at the top of the drained ladder.
    ladder = d["drained_ladder"]["KP 58.8 41.00 m"]
    assert round(ladder["as if undrained"]["dbeta"], 2) == 0.72
    assert round(ladder["berm, 60 % relief"]["dbeta"], 2) == 0.55
    assert ladder["berm, 80 % relief"]["k_transient"] == 0
    kp62 = d["kp62_arms_46.75m"]
    assert (kp62["adopted"]["k_same_head"], kp62["adopted"]["k_transient"]) == (
        629,
        101,
    )
    assert kp62["gamma_bl_sub_lower"] == kp62["adopted"]
    half = next(lv for lv in record["halved_r_e"]["levels"] if lv["stage_m"] == 41.0)
    assert round(half["gate_half"], 3) == 0.368
    assert round(half["P_same_head_half"], 3) == 0.203
    assert all(
        lv["new_same_head_failures"] == 0 for lv in record["halved_r_e"]["levels"]
    )


def test_pol_case_reproduction_is_recorded(record) -> None:
    first = record["polriver"]["first_year_no_flood_fighting"]
    case = first["Gumbel(3, 0.25), Pol case 3d"]
    published = first["pol_published_case_3d_2025"]
    assert published == {"P_td": 1.1e-3, "P_stat": 7.3e-3, "F_td": 6.5}
    assert 4.0 < case["F_td"] < 6.5
