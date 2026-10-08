"""Gate for the loading-context study (Pol round 2, A25, A29, A32).

Pins the pure helpers of ``scripts/loading_context_study.py``, the committed
Futochanae extract and the tracked evidence JSON. The one check that re-reads
the gitignored Phase 3 hazard files skips on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "loading_context_study.py"
EVIDENCE = REPO / "docs" / "decisions" / "loading-context-study.json"
TOKORO = REPO / "data" / "processed" / "2016_event" / "stage_hourly_Tokoro_201608.csv"


def _module():
    spec = importlib.util.spec_from_file_location("loading_context_study", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["loading_context_study"] = mod
    spec.loader.exec_module(mod)
    return mod


LCS = _module()


def test_stage_shape_is_independent_of_the_rating_coefficients() -> None:
    q = np.array([80.0, 300.0, 2500.0, 7000.0, 1200.0, 3000.0, 400.0, 90.0])
    shape = LCS.stage_shape(q)
    for a, b in ((0.8, 1.2), (12.0, -32.49), (3.3, 0.0)):
        h = np.sqrt(q / a) - b
        assert np.allclose(shape, (h - h.min()) / (h.max() - h.min()))


def test_shape_statistics_counts_two_significant_peaks() -> None:
    t = np.arange(192.0)
    s = np.exp(-(((t - 40) / 8) ** 2)) + 0.7 * np.exp(-(((t - 90) / 8) ** 2))
    s = (s - s.min()) / (s.max() - s.min())
    stats = LCS.shape_statistics(s)
    assert stats["n_peaks"] == 2
    assert stats["peak_hour_index"] == 40
    assert stats["t50_h"] == np.count_nonzero(s >= 0.5)


def test_shape_statistics_ignores_a_shallow_shoulder() -> None:
    t = np.arange(120.0)
    s = np.exp(-(((t - 40) / 10) ** 2)) + 0.25 * np.exp(-(((t - 75) / 6) ** 2))
    s = (s - s.min()) / (s.max() - s.min())
    assert LCS.shape_statistics(s)["n_peaks"] == 1


def test_excursions_are_runs_strictly_above_the_level() -> None:
    v = np.array([0, 2, 3, 1, 1, 4, 4, 4, 0, 5])
    assert LCS.excursions_above(v, 1.0) == [2, 3, 1]
    assert LCS.excursions_above(v, 9.0) == []


def test_committed_tokoro_record_matches_the_committee() -> None:
    times, h = LCS.read_stage_csv(TOKORO, "futochanae")
    assert len(times) == 744 and np.all(np.isfinite(h))
    k = int(np.argmax(h))
    assert times[k].strftime("%Y-%m-%dT%H:%M") == "2016-08-21T01:00"
    assert h[k] == pytest.approx(14.24)
    # Committee (2017): above 12.38 m for 32 h 40 min, waveform peak 14.22 m.
    runs = LCS.excursions_above(h, LCS.FUTOCHANAE_DESIGN_M)
    assert runs == [6, 33]
    assert abs(h[k] - 14.22) <= 0.05


def test_adjusted_ratio_is_one_for_identical_populations() -> None:
    rng = np.random.default_rng(1)
    n = 3000
    peak = 38.5 + rng.gamma(2.0, 0.6, n)
    hours = np.where(peak > 38.5, 10 * (peak - 38.5) + rng.normal(0, 2, n), 0)
    multi = (rng.random(n) < 0.05).astype(float) * 2
    pop = {
        "peak_stage_m_msl": peak,
        "hours_above_datum": np.clip(hours, 0, None),
        "n_peaks_above_datum": multi,
    }
    edges = np.arange(38.5, 46.51, 0.25)
    for metric in ("multi", "hours"):
        r = LCS.adjusted_ratio(pop, pop, edges, metric)
        assert r["ratio"] == pytest.approx(1.0)


def test_blocks_stratify_warming_members_by_sst_pattern() -> None:
    ids = np.array(
        ["HPB_m001_1951", "HPB_m001_1952", "HPB_m002_1951"]
        + ["HFB_CC_m101_2051", "HFB_CC_m101_2052", "HFB_MR_m115_2051"]
    )
    hist = LCS._blocks(ids[:3])
    warm = LCS._blocks(ids[3:])
    assert set(hist) == {"historical"}
    assert sorted(hist["historical"]) == ["HPB_m001", "HPB_m002"]
    assert set(warm) == {"CC", "MR"}
    assert list(warm["CC"]["HFB_CC_m101"]) == [0, 1]


def test_evidence_records_the_reproduction_gate_and_the_verdicts() -> None:
    rec = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert rec["pre_registration_commit"] == "20e2330"
    pred = rec["predictions"]
    assert pred["P2"]["held"] is True  # ADR-0023 reproduced exactly
    assert pred["P1"]["held"] is True
    assert pred["P3"]["held"] is False and pred["P3"]["august_peaks"] == 3
    assert pred["P4"]["held"] is False  # fails at KP 62.0 only
    failed = [
        k for k, v in pred["P4"]["detail"].items() if v["given_loaded_ratio"] >= 1.5
    ]
    assert failed == ["KP 62.0"]
    assert pred["P5"]["held"] is True and pred["P6"]["held"] is True
    ens = rec["ensemble"]
    assert ens["historical"]["peak_hour_max"] <= 96
    assert ens["+4K"]["peak_hour_max"] <= 96
    rivers = rec["three_rivers_2016"]
    assert rivers["Tokoro, Futochanae"]["peak_above_design_m"] == pytest.approx(1.86)
    assert rivers["Satsunai, KP 15.0"]["record_complete"] is False
    assert rivers["Satsunai, KP 15.0"]["peak_above_design_m"] == pytest.approx(0.16)
    toka = [rivers[f"Tokachi, KP {kp}"]["peak_above_design_m"] for kp in LCS.KPS]
    assert toka == pytest.approx([0.448, -0.28, -0.454, -0.661], abs=1e-3)
    same = rec["post_hoc"]["same_height_kp58_8"]
    assert same["record_2016_hours"] == 21 and same["record_2016_percentile"] == 0
    hours = rec["post_hoc"]["amplitude_adjusted_hours_above_toe"]
    assert all(0.9 <= v["ratio"] <= 1.05 for v in hours.values())


def test_hazard_statistics_reproduce_from_the_hazard_files() -> None:
    path = REPO / "results" / "system_integration" / "hazard_tokachi_kp58.8_plus4K.csv"
    if not path.is_file():
        pytest.skip("untracked results/system_integration hazard files absent")
    rec = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    hz = LCS._hazard(58.8, "+4K")
    loaded = hz["hours_above_datum"] > 0
    multi = hz["n_peaks_above_datum"] >= 2
    row = rec["hazard"]["KP 58.8"]["+4K"]
    assert 100 * loaded.mean() == pytest.approx(row["loaded_pct"], rel=1e-5)
    assert 100 * multi[loaded].mean() == pytest.approx(
        row["multi_given_loaded_pct"], rel=1e-5
    )
