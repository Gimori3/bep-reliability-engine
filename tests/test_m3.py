"""Interface-contract tests for M3 ``hydrograph_loader`` (``hydrographs.py``).

These tests are written **ahead of the real d4PDF data files** and ahead of the
module itself (``bep_reliability_engine/hydrographs.py`` is still empty). They
therefore test the *interface contract* of spec §2 — the ``HydrographRecord``
schema and the discharge-to-stage conversion + record-construction logic — not
any specific on-disk file format. They are expected to fail at *collection* until
M3 is implemented against the interface assumed here; that is the interface-first
pattern (cf. the M2 ``sampling.py`` build-out).

Assumed M3 public interface (what these tests pin)
--------------------------------------------------
``HydrographRecord``
    Frozen record with the spec §2 fields:
    ``t`` (s), ``h`` (m above datum), ``peak`` (m), ``duration_hours`` (h),
    ``scenario`` (str), ``event_id`` (str), ``native_dt`` (s). This is the same
    schema the ``run.py`` M3 stub already duck-types (``.h``/``.peak``/
    ``.native_dt`` are the three fields M8 reads).

``apply_rating_curve(discharge_m3s, a_h, b_h) -> ndarray``
    Pure, elementwise H-Q rating-curve conversion Q(t) -> h(t). **This is the one
    function to change if the rating-curve form is revised** (see the provisional
    caveat below).

``build_hydrograph_record(time_hours, discharge_m3s, *, a_h, b_h, scenario,
    event_id) -> HydrographRecord``
    The record-construction seam and **the unit boundary**. It receives time in
    the source's *native unit (hours)* and discharge in m^3/s, and it:
    (1) converts the time axis to SI seconds (``t = time_hours * 3600``);
    (2) applies the rating curve to produce h(t);
    (3) derives ``native_dt`` [s] from the *converted* spacing and
    ``duration_hours`` from the elapsed span; and
    (4) validates that the time axis is strictly increasing and uniformly spaced.
    Keeping the hours->seconds conversion *inside this pure function* (rather than
    in the file reader) is deliberate: it is the M3 analogue of the M4
    m/s-vs-m/day conductivity trap, so it must be covered by a test that runs
    without a file (see :func:`test_time_array_is_converted_to_seconds`).

File I/O is a **separate seam, deliberately not exercised here.** The data
provider gives hourly discharge series Q(t) for a historical and a +4K ensemble;
the real loader is expected to be a thin composition ``load_hydrograph(path, ...)
= build_hydrograph_record(*_read_discharge_series(path), ...)`` where
``_read_discharge_series`` is the fill-in-later I/O boundary that returns the raw
columns **in their native source units** (time in hours, Q in m^3/s) and does no
unit conversion of its own. By testing only ``apply_rating_curve`` and
``build_hydrograph_record`` against an in-memory synthetic hydrograph, the
conversion and record-construction logic is locked now, independently of the file
format that lands later.

Units (SI at this boundary; spec §1 "all unit conversion at this boundary")
---------------------------------------------------------------------------
Source discharge is at **1-hour** native resolution, time expressed in hours. M3
converts to strict SI at ingest, so the record's ``t`` and ``native_dt`` are in
**seconds** (hourly source => ``native_dt == 3600.0``) and ``duration_hours`` is
the elapsed span in hours. ``native_dt`` is **derived from the actual time-array
spacing**, not assumed — a non-hourly spacing must come back as the correct
number of seconds (see :func:`test_native_dt_is_derived_from_actual_spacing`).
This matches the ``run.py`` stub and the M7 timestepper, which consume
``native_dt`` in seconds.

.. warning::
   **PROVISIONAL RATING-CURVE FORM — confirm with Uemura-san.**
   The H-Q rating curve is assumed here to be the two-coefficient power law

       h(Q) = a_h * Q ** b_h

   This form is *not yet confirmed*; it is a placeholder pending the Chapter 3
   coefficients and functional form from Uemura-san. The golden value in
   :func:`test_rating_curve_power_law_hand_value` is hand-computed from this form
   alone. If the confirmed form differs (linear ``a_h + b_h*Q``, semi-log
   ``a_h + b_h*ln Q``, an added datum offset, or different units of Q), update
   :func:`apply_rating_curve` and the golden values in this file together.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from bep_reliability_engine.hydrographs import (
    HydrographRecord,
    apply_rating_curve,
    build_hydrograph_record,
)

# --- Test fixtures / provisional rating-curve coefficients -------------------
# Simple, round coefficients chosen so every expected stage is exact (no float
# fuzz): with b_h = 0.5 a perfect square Q maps to an integer stage.
_A_H = 2.0
_B_H = 0.5
_SECONDS_PER_HOUR = 3600.0


def _synthetic_hourly_discharge() -> tuple[np.ndarray, np.ndarray]:
    """Return an in-memory synthetic (time_hours, discharge_m3s) hydrograph.

    A single-peaked hourly discharge series in **native source units**: 25 samples
    at 1-hour spacing (24-hour span), rising to a clear interior maximum of
    400 m^3/s so the peak stage and duration are unambiguous and hand-checkable.
    All perfect squares so the power-law (b_h = 0.5) stages are exact.

    Returns
    -------
    time_hours : numpy.ndarray, shape (25,)
        Time axis in **hours** (native source unit), ``np.arange(25)``.
    discharge_m3s : numpy.ndarray, shape (25,)
        Discharge Q(t) [m^3/s] with a single interior peak of 400.
    """
    time_hours = np.arange(25, dtype=np.float64)
    # Symmetric triangular-ish rise/fall in perfect squares, peak 400 at the apex.
    ramp = np.array(
        [1.0, 4.0, 9.0, 16.0, 25.0, 36.0, 49.0, 64.0, 81.0, 100.0, 225.0, 324.0],
        dtype=np.float64,
    )
    discharge = np.concatenate([ramp, [400.0], ramp[::-1]])
    assert discharge.shape == time_hours.shape
    return time_hours, discharge


# --- HydrographRecord field contract -----------------------------------------
def test_hydrograph_record_field_contract() -> None:
    """The record exposes exactly the spec §2 fields with the right types.

    Locks the schema M8/run.py duck-type against: ``t``/``h`` equal-length float
    arrays, scalar ``peak``/``duration_hours``/``native_dt``, and string
    ``scenario``/``event_id``.
    """
    time_hours, discharge = _synthetic_hourly_discharge()
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="synthetic_0001",
    )

    assert isinstance(record, HydrographRecord)
    expected_fields = {
        "t",
        "h",
        "peak",
        "duration_hours",
        "scenario",
        "event_id",
        "native_dt",
    }
    assert {f.name for f in dataclasses.fields(record)} == expected_fields

    # Array fields: equal-length 1-D float arrays.
    assert isinstance(record.t, np.ndarray)
    assert isinstance(record.h, np.ndarray)
    assert record.t.shape == record.h.shape == discharge.shape
    assert np.issubdtype(record.t.dtype, np.floating)
    assert np.issubdtype(record.h.dtype, np.floating)

    # Scalar metadata fields (np.float64 is a subclass of float).
    assert isinstance(record.peak, float)
    assert isinstance(record.duration_hours, float)
    assert isinstance(record.native_dt, float)

    # Tag fields.
    assert isinstance(record.scenario, str)
    assert isinstance(record.event_id, str)
    assert record.event_id == "synthetic_0001"


# --- Q -> h rating-curve conversion (PROVISIONAL power law) -------------------
@pytest.mark.parametrize(
    ("a_h", "b_h", "discharge", "expected_stage"),
    [
        # The documented golden value: 2.0 * 100^0.5 = 2.0 * 10 = 20.0.
        (2.0, 0.5, 100.0, 20.0),
        (1.0, 1.0, 42.0, 42.0),  # b_h = 1, a_h = 1 -> stage == discharge
        (3.0, 2.0, 4.0, 48.0),  # 3.0 * 4^2 = 48.0
        (0.5, 0.5, 144.0, 6.0),  # 0.5 * 12 = 6.0
    ],
)
def test_rating_curve_power_law_hand_value(
    a_h: float, b_h: float, discharge: float, expected_stage: float
) -> None:
    """``apply_rating_curve`` reproduces hand-computed h = a_h * Q**b_h.

    This is the M3 formula guard: a wrong functional form produces plausible,
    visually-passable output, so the assertion is against a number computable with
    a calculator, not merely that the call returns.

    PROVISIONAL: power-law form pending Uemura-san (see module docstring). If the
    confirmed form differs, these golden values must be recomputed alongside
    :func:`apply_rating_curve`.
    """
    result = apply_rating_curve(discharge, a_h, b_h)
    assert float(result) == pytest.approx(expected_stage)


def test_rating_curve_is_elementwise_on_arrays() -> None:
    """The conversion broadcasts elementwise over a discharge array."""
    discharge = np.array([1.0, 4.0, 9.0, 16.0])
    # 2.0 * sqrt(Q) -> [2, 4, 6, 8]
    expected = np.array([2.0, 4.0, 6.0, 8.0])
    result = apply_rating_curve(discharge, _A_H, _B_H)
    np.testing.assert_allclose(result, expected)


def test_record_h_equals_rating_curve_of_discharge() -> None:
    """The record's h(t) is exactly the rating curve applied to Q(t).

    Ties record construction to the single conversion function, so a future
    rating-curve change propagates through the record with no separate code path.
    """
    time_hours, discharge = _synthetic_hourly_discharge()
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="synthetic_0001",
    )
    np.testing.assert_allclose(record.h, apply_rating_curve(discharge, _A_H, _B_H))


# --- Units at the boundary: hours -> seconds ---------------------------------
def test_time_array_is_converted_to_seconds() -> None:
    """The record's time axis is SI seconds, converted from the source's hours.

    The M3 unit-boundary guard (analogue of the M4 m/s-vs-m/day trap): feed a time
    axis in hours and require the record to carry ``t`` in seconds. If the
    hours->seconds conversion is dropped, ``record.t`` would still read as hours
    and this assertion catches the slip.
    """
    time_hours = np.array([0.0, 1.0, 2.0, 3.0])
    discharge = np.array([1.0, 4.0, 9.0, 16.0])
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="units_check",
    )
    np.testing.assert_allclose(record.t, time_hours * _SECONDS_PER_HOUR)
    # Sanity: the last sample is 3 h == 10800 s, not left as 3.
    assert record.t[-1] == pytest.approx(10800.0)


# --- native_dt is derived from the time array, not hardcoded -----------------
def test_native_dt_reflects_hourly_source_resolution() -> None:
    """An hourly source yields native_dt == 3600 s."""
    time_hours, discharge = _synthetic_hourly_discharge()
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="synthetic_0001",
    )
    assert record.native_dt == pytest.approx(_SECONDS_PER_HOUR)


@pytest.mark.parametrize(
    ("spacing_hours", "expected_native_dt_s"),
    [
        (1.0, 3600.0),  # hourly (the expected d4PDF resolution)
        (0.5, 1800.0),  # 30-min: must NOT come back as 3600
        (2.0, 7200.0),  # 2-hourly: must NOT come back as 3600
    ],
)
def test_native_dt_is_derived_from_actual_spacing(
    spacing_hours: float, expected_native_dt_s: float
) -> None:
    """``native_dt`` is computed from the real spacing, not assumed to be 3600 s.

    Feeding a non-hourly spacing is what distinguishes a derived ``native_dt``
    from an implementation that hardcodes 3600 s: the 0.5 h and 2.0 h cases fail
    against any hardcoded-hourly assumption.
    """
    time_hours = np.arange(6, dtype=np.float64) * spacing_hours
    discharge = np.linspace(10.0, 60.0, time_hours.size)
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="spacing_check",
    )
    assert record.native_dt == pytest.approx(expected_native_dt_s)


def test_non_uniform_time_spacing_is_rejected() -> None:
    """A non-uniformly spaced time axis is rejected (native_dt ill-defined).

    ``native_dt`` is a single scalar resolution, so the loader must refuse a time
    axis whose spacing is not constant rather than silently pick one gap.
    """
    time_hours = np.array([0.0, 1.0, 2.0, 3.5])  # last gap is 1.5 h
    discharge = np.array([10.0, 20.0, 30.0, 40.0])
    with pytest.raises(ValueError):
        build_hydrograph_record(
            time_hours,
            discharge,
            a_h=_A_H,
            b_h=_B_H,
            scenario="historical",
            event_id="bad_spacing",
        )


# --- monotonic time ----------------------------------------------------------
@pytest.mark.parametrize(
    "time_hours",
    [
        np.array([0.0, 1.0, 1.0, 2.0]),  # repeated (non-strict)
        np.array([0.0, 1.0, 0.5, 2.0]),  # decreasing step
    ],
)
def test_time_axis_must_be_strictly_increasing(time_hours: np.ndarray) -> None:
    """A non-strictly-increasing time axis is rejected."""
    discharge = np.array([10.0, 20.0, 30.0, 40.0])
    with pytest.raises(ValueError):
        build_hydrograph_record(
            time_hours,
            discharge,
            a_h=_A_H,
            b_h=_B_H,
            scenario="historical",
            event_id="non_monotonic",
        )


# --- peak and duration -------------------------------------------------------
def test_peak_is_max_stage() -> None:
    """``peak`` is the maximum stage, i.e. the rating curve at the peak discharge.

    Under a monotonically increasing rating curve (b_h > 0) the peak stage occurs
    at the peak discharge; here Q_max = 400 => peak = 2.0 * sqrt(400) = 40.0.
    """
    time_hours, discharge = _synthetic_hourly_discharge()
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="synthetic_0001",
    )
    assert record.peak == pytest.approx(40.0)
    assert record.peak == pytest.approx(float(record.h.max()))


def test_duration_hours_is_elapsed_span() -> None:
    """``duration_hours`` is the elapsed span in hours.

    25 hourly samples span 24 hours.
    """
    time_hours, discharge = _synthetic_hourly_discharge()
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario="historical",
        event_id="synthetic_0001",
    )
    assert record.duration_hours == pytest.approx(24.0)


# --- scenario tag ------------------------------------------------------------
@pytest.mark.parametrize("scenario", ["historical", "+4K"])
def test_scenario_tag_is_carried_through(scenario: str) -> None:
    """The scenario tag ('historical' or '+4K') round-trips onto the record.

    The scenario field flows through to ``FragilityResult`` metadata and the
    climate comparison depends on it, so both tags are exercised.
    """
    time_hours, discharge = _synthetic_hourly_discharge()
    record = build_hydrograph_record(
        time_hours,
        discharge,
        a_h=_A_H,
        b_h=_B_H,
        scenario=scenario,
        event_id="synthetic_0001",
    )
    assert record.scenario == scenario
