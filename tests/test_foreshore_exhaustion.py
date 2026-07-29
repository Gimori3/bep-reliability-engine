"""Tests for the R10 Tier 1 foreshore-exhaustion screening indicator.

Pure-logic coverage runs everywhere: the indicator arithmetic, the
mobilisation-threshold handling, the boundary cases (B_f = 0 as at KP 63.4,
zero-duration forcing, a flood that never engages the bed), and the
critical-rate inversion. The registry-joined loader tests skip on fresh
clones, mirroring the Phase 3 pattern.

One guard here is structural rather than numerical: the screening module
must stay unwired from :mod:`system_integration.composition`. Tier 1 adds no
mechanism to the Phase 3 series system, so every persisted Phase 3 number
stays bit-identical; a future import would silently break that promise.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from system_integration.foreshore_exhaustion import (
    RETREAT_RATE_BRACKET_M_PER_H,
    ForeshoreState,
    critical_retreat_rate_m_per_h,
    foreshore_coverage,
    foreshore_exhaustion,
    load_measured_foreshore_states,
    mobilising_duration_hours,
)
from system_integration.segments import Segment, SegmentRegistry, build_registry

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO / "data" / "raw"

requires_rating_csvs = pytest.mark.skipif(
    not (DATA_ROOT / "rating_curves" / "HQrelation_TokachiRiv_2017.csv").exists(),
    reason="rating-curve CSVs absent (untracked data drop)",
)


# ============================================================================
# Mobilising duration
# ============================================================================
def test_mobilising_duration_counts_samples_strictly_above() -> None:
    """Strictly above, sample-counted on the record's own grid."""
    stage = np.array([10.0, 11.0, 12.0, 11.0, 10.0])
    # Threshold at 11.0: only the 12.0 sample counts (strict inequality),
    # matching hazard._above_datum_measures.
    assert mobilising_duration_hours(stage, 3600.0, 11.0) == pytest.approx(1.0)
    assert mobilising_duration_hours(stage, 3600.0, 10.5) == pytest.approx(3.0)
    assert mobilising_duration_hours(stage, 1800.0, 10.5) == pytest.approx(1.5)


def test_mobilising_duration_is_zero_when_the_bed_is_never_engaged() -> None:
    stage = np.array([10.0, 11.0, 12.0])
    assert mobilising_duration_hours(stage, 3600.0, 12.0) == 0.0
    assert mobilising_duration_hours(stage, 3600.0, 99.0) == 0.0


def test_mobilising_duration_rejects_bad_arguments() -> None:
    stage = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="dt_seconds must be positive"):
        mobilising_duration_hours(stage, 0.0, 1.5)
    with pytest.raises(ValueError, match="threshold_m_msl must be finite"):
        mobilising_duration_hours(stage, 3600.0, float("nan"))
    with pytest.raises(ValueError, match="non-finite samples"):
        mobilising_duration_hours(np.array([1.0, np.nan]), 3600.0, 1.5)
    with pytest.raises(ValueError, match="one-dimensional"):
        mobilising_duration_hours(np.zeros((2, 3)), 3600.0, 1.5)


# ============================================================================
# Indicator arithmetic
# ============================================================================
def test_exposure_ratio_and_time_to_exhaustion_arithmetic() -> None:
    """B_f = 100 m, 2 m/h, 10 mobilising hours -> 20 m eroded, ratio 0.2."""
    stage = np.full(10, 5.0)
    result = foreshore_exhaustion(
        stage,
        3600.0,
        foreshore_width_m=100.0,
        mobilisation_stage_m_msl=4.0,
        retreat_rate_m_per_h=2.0,
    )
    assert result.mobilising_hours == pytest.approx(10.0)
    assert result.record_hours == pytest.approx(10.0)
    assert result.cumulative_retreat_m == pytest.approx(20.0)
    assert result.time_to_exhaustion_h == pytest.approx(50.0)
    assert result.exposure_ratio == pytest.approx(0.2)
    assert result.exhausted is False
    assert result.peak_stage_m_msl == pytest.approx(5.0)
    assert result.peak_excess_depth_m == pytest.approx(1.0)
    assert result.mean_excess_depth_m == pytest.approx(1.0)


def test_exposure_ratio_is_the_ratio_of_the_two_durations() -> None:
    """exposure_ratio == mobilising_hours / time_to_exhaustion, exactly."""
    rng = np.random.default_rng(0)
    stage = 40.0 + rng.random(500) * 3.0
    for rate in RETREAT_RATE_BRACKET_M_PER_H.values():
        result = foreshore_exhaustion(
            stage,
            900.0,
            foreshore_width_m=250.0,
            mobilisation_stage_m_msl=41.5,
            retreat_rate_m_per_h=rate,
        )
        assert result.exposure_ratio == pytest.approx(
            result.mobilising_hours / result.time_to_exhaustion_h
        )


def test_flag_trips_exactly_at_unity() -> None:
    """The screening flag is >= 1, boundary included."""
    stage = np.full(10, 5.0)  # 10 mobilising hours
    kwargs = {"mobilisation_stage_m_msl": 4.0, "retreat_rate_m_per_h": 1.0}
    just_under = foreshore_exhaustion(
        stage, 3600.0, foreshore_width_m=10.000001, **kwargs
    )
    exactly = foreshore_exhaustion(stage, 3600.0, foreshore_width_m=10.0, **kwargs)
    assert just_under.exhausted is False
    assert exactly.exposure_ratio == pytest.approx(1.0)
    assert exactly.exhausted is True


def test_raising_the_threshold_cannot_increase_exposure() -> None:
    """Monotone in the mobilisation threshold — the bracket must behave."""
    rng = np.random.default_rng(7)
    stage = 40.0 + np.cumsum(rng.normal(size=400)) * 0.05
    previous = math.inf
    for threshold in (39.0, 40.0, 41.0, 42.0):
        result = foreshore_exhaustion(
            stage,
            3600.0,
            foreshore_width_m=120.0,
            mobilisation_stage_m_msl=threshold,
            retreat_rate_m_per_h=1.0,
        )
        assert result.exposure_ratio <= previous + 1e-12
        previous = result.exposure_ratio


def test_mean_excess_depth_never_exceeds_the_peak() -> None:
    """The constant-rate treatment is the bounding one; this is the factor."""
    stage = np.array([40.0, 41.0, 42.0, 43.0, 41.5, 40.0])
    result = foreshore_exhaustion(
        stage,
        3600.0,
        foreshore_width_m=50.0,
        mobilisation_stage_m_msl=40.5,
        retreat_rate_m_per_h=1.0,
    )
    assert 0.0 < result.mean_excess_depth_m <= result.peak_excess_depth_m


# ============================================================================
# Boundary cases
# ============================================================================
def test_zero_foreshore_width_is_already_exhausted() -> None:
    """The KP 63.4 'river-tight' case: no bed left to consume.

    The geotech CSV records ``foreshore_width_m = 0`` at KP 63.4. That
    section sits outside the production population and outside the Phase 3
    study reach, but the indicator must not divide by zero or quietly
    report a benign number for it.
    """
    stage = np.full(5, 3.0)
    result = foreshore_exhaustion(
        stage,
        3600.0,
        foreshore_width_m=0.0,
        mobilisation_stage_m_msl=2.0,
        retreat_rate_m_per_h=0.1,
    )
    assert result.time_to_exhaustion_h == 0.0
    assert math.isinf(result.exposure_ratio)
    assert result.exhausted is True
    # ... and it stays exhausted even when the flood never engages the bed:
    # there is no bed, whatever the forcing does.
    quiet = foreshore_exhaustion(
        stage,
        3600.0,
        foreshore_width_m=0.0,
        mobilisation_stage_m_msl=99.0,
        retreat_rate_m_per_h=0.1,
    )
    assert quiet.mobilising_hours == 0.0
    assert math.isinf(quiet.exposure_ratio)
    assert quiet.exhausted is True


def test_zero_duration_forcing() -> None:
    """An empty record erodes nothing and trips nothing."""
    result = foreshore_exhaustion(
        np.array([], dtype=float),
        3600.0,
        foreshore_width_m=44.0,
        mobilisation_stage_m_msl=43.82,
        retreat_rate_m_per_h=10.0,
    )
    assert result.mobilising_hours == 0.0
    assert result.record_hours == 0.0
    assert result.cumulative_retreat_m == 0.0
    assert result.exposure_ratio == 0.0
    assert result.exhausted is False
    assert result.mean_excess_depth_m == 0.0
    assert math.isnan(result.peak_stage_m_msl)


def test_forcing_entirely_below_the_threshold() -> None:
    stage = np.linspace(40.0, 43.0, 200)
    result = foreshore_exhaustion(
        stage,
        3600.0,
        foreshore_width_m=44.0,
        mobilisation_stage_m_msl=50.0,
        retreat_rate_m_per_h=10.0,
    )
    assert result.mobilising_hours == 0.0
    assert result.exposure_ratio == 0.0
    assert result.exhausted is False
    assert result.peak_excess_depth_m == 0.0
    assert result.mean_excess_depth_m == 0.0


def test_indicator_rejects_bad_arguments() -> None:
    stage = np.full(3, 5.0)
    common = {"mobilisation_stage_m_msl": 4.0}
    with pytest.raises(ValueError, match="retreat_rate_m_per_h must be strictly"):
        foreshore_exhaustion(
            stage, 3600.0, foreshore_width_m=10.0, retreat_rate_m_per_h=0.0, **common
        )
    with pytest.raises(ValueError, match="foreshore_width_m must be finite"):
        foreshore_exhaustion(
            stage, 3600.0, foreshore_width_m=-1.0, retreat_rate_m_per_h=1.0, **common
        )
    with pytest.raises(ValueError, match="dt_seconds must be positive"):
        foreshore_exhaustion(
            stage, -1.0, foreshore_width_m=10.0, retreat_rate_m_per_h=1.0, **common
        )


# ============================================================================
# Critical retreat rate (the inverse reading)
# ============================================================================
def test_critical_rate_inverts_the_indicator_exactly() -> None:
    """Screening at v* must land exactly on the flag boundary."""
    rng = np.random.default_rng(11)
    stage = 45.0 + rng.random(300) * 2.0
    width, threshold = 44.0, 46.0
    hours = mobilising_duration_hours(stage, 900.0, threshold)
    v_star = critical_retreat_rate_m_per_h(width, hours)
    result = foreshore_exhaustion(
        stage,
        900.0,
        foreshore_width_m=width,
        mobilisation_stage_m_msl=threshold,
        retreat_rate_m_per_h=v_star,
    )
    assert result.exposure_ratio == pytest.approx(1.0)
    assert result.exhausted is True


def test_critical_rate_edge_cases() -> None:
    assert math.isinf(critical_retreat_rate_m_per_h(600.0, 0.0))
    assert critical_retreat_rate_m_per_h(0.0, 25.0) == 0.0
    assert critical_retreat_rate_m_per_h(0.0, 0.0) == 0.0
    with pytest.raises(ValueError, match="foreshore_width_m must be finite"):
        critical_retreat_rate_m_per_h(-1.0, 10.0)
    with pytest.raises(ValueError, match="mobilising_hours must be finite"):
        critical_retreat_rate_m_per_h(100.0, -1.0)


def test_retreat_rate_bracket_spans_two_orders_of_magnitude() -> None:
    """A single rate would be false precision; the bracket must be wide."""
    rates = RETREAT_RATE_BRACKET_M_PER_H
    assert max(rates.values()) / min(rates.values()) >= 100.0
    # The one documented datum is carried unconverted and labelled as such.
    assert rates["narrative_2011"] == pytest.approx(5.0)


# ============================================================================
# Registry join and coverage
# ============================================================================
def test_coverage_reports_the_gap_rather_than_hiding_it() -> None:
    registry = SegmentRegistry(
        segments=tuple(
            Segment(river="Tokachi", bank="right", kp=kp)
            for kp in (57.4, 57.6, 57.8, 58.0)
        )
    )
    states = (
        ForeshoreState(
            river="Tokachi",
            bank="right",
            kp=57.4,
            foreshore_width_m=200.0,
            mobilisation_stage_m_msl=36.41,
            width_source="test",
            stage_source="test",
        ),
    )
    coverage = foreshore_coverage(registry, states)
    assert coverage["n_segments"] == 4
    assert coverage["n_screened"] == 1
    assert coverage["n_without_measured_width"] == 3
    assert coverage["screened_fraction"] == pytest.approx(0.25)
    assert coverage["nodes"] == ["Tokachi KP 57.4"]


def test_loader_refuses_a_width_without_a_mobilisation_stage(tmp_path) -> None:
    """An inconsistent input pair is an error, not a silent drop."""
    widths = tmp_path / "widths.csv"
    widths.write_text(
        "kp,river,bank,foreshore_width_m\n57.4,Tokachi,right,200\n", encoding="utf-8"
    )
    stages = tmp_path / "stages.csv"
    stages.write_text(
        "river,bank,kp,floodplain_m_msl\nTokachi,right,58.8,37.53\n", encoding="utf-8"
    )
    registry = SegmentRegistry(
        segments=(Segment(river="Tokachi", bank="right", kp=57.4),)
    )
    with pytest.raises(ValueError, match="no floodplain elevation"):
        load_measured_foreshore_states(
            registry, foreshore_csv=widths, segment_inputs_csv=stages
        )


@requires_rating_csvs
def test_measured_states_match_the_adr0025_verified_widths() -> None:
    """The four confined OYO sections, verbatim 200 / 325 / 600 / 44 m."""
    registry = build_registry(DATA_ROOT)
    states = load_measured_foreshore_states(registry)
    assert {round(s.kp, 3) for s in states} == {57.4, 58.8, 60.0, 62.0}
    widths = {round(s.kp, 3): s.foreshore_width_m for s in states}
    assert widths == {57.4: 200.0, 58.8: 325.0, 60.0: 600.0, 62.0: 44.0}
    coverage = foreshore_coverage(registry, states)
    assert coverage["n_segments"] == 114
    assert coverage["n_screened"] == 4
    assert coverage["n_without_measured_width"] == 110
    # Every screenable node must carry a threshold below its design HWL,
    # or the bed could never be engaged at all.
    assert all(s.mobilisation_stage_m_msl > 0.0 for s in states)


# ============================================================================
# Phase 3 isolation (structural)
# ============================================================================
def test_screening_module_is_not_wired_into_the_phase_3_composition() -> None:
    """Tier 1 adds no mechanism: composition must not know this module.

    ``docs/scoping_bank_retreat_mechanism.md`` Tier 2 — a stage-conditioned
    retreat fragility joining the series system — is declined and would
    need its own ADR. Until then the Phase 3 headline numbers must stay
    bit-identical, which requires the composition path never to import
    this screening code.
    """
    from system_integration import composition

    source = Path(composition.__file__).read_text(encoding="utf-8")
    assert "foreshore_exhaustion" not in source
    assert not hasattr(composition, "foreshore_exhaustion")
    assert "foreshore_exhaustion" not in composition.__all__
