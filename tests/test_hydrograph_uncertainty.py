"""Discriminating checks for the Green Light 5 companion estimators."""

import importlib.util
from pathlib import Path

import numpy as np


def _driver():
    path = Path(__file__).parents[1] / "scripts/hydrograph_uncertainty_study.py"
    spec = importlib.util.spec_from_file_location("g5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sst_patterns_keep_equal_weight_despite_unequal_event_counts():
    driver = _driver()
    members = {}
    for sst, n in (("CC", 60), ("GF", 120)):
        for i in range(n):
            members[f"HFB_{sst}_m{i//60+1:03d}_{1951+i%60}"] = np.array([0, i + 1, 0])
    groups = driver.stratified_selection(members)
    for sst in ("CC", "GF"):
        assert np.isclose(
            sum(g["weight"] for g in groups if g["stratum"].startswith(sst)), 0.5
        )
    assert all(len(set(g["events"])) == len(g["events"]) for g in groups)


def test_union_is_taken_before_averaging_over_events():
    # Mechanisms fail in different events. Composing annual marginals would
    # wrongly return 0.75 instead of the event-wise union's exact 1.
    got = _driver().summary(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
    assert got["system"] == 1
    assert got["share"] == 0.5


def test_stratum_weights_are_population_weights_not_sample_counts():
    got = _driver().weighted_summary(
        [{"weight": 0.9}, {"weight": 0.1}],
        [np.array([[0.0, 0.0, 0.0]]), np.array([[1.0, 0.0, 0.0]] * 4)],
    )
    assert got["system"] == 0.1


def test_peak_shift_is_not_a_uniform_stage_shift():
    from bep_reliability_engine.hydrographs import (
        CanonicalShape,
        HydrographRecord,
        conditioning_record_for_level,
    )

    shape = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
    record = HydrographRecord(
        t=np.arange(5.0) * 3600,
        h=10 + 2 * shape,
        peak=12,
        duration_hours=4,
        scenario="historical",
        event_id="test",
        native_dt=3600,
    )
    canonical = CanonicalShape(record, shape, 10.0)
    shifted = conditioning_record_for_level(canonical, 12.3, scenario="historical")
    np.testing.assert_allclose(shifted.h - record.h, 0.3 * shape)
    assert shifted.h[0] == record.h[0]
    assert not np.allclose(shifted.h, record.h + 0.3)
