"""Observed-event ingestion: gauge extracts to per-section loading records.

The reusable loader behind the Phase 2 survival constraint (ADR-0035). It
turns the committed processed extracts of an observed flood event (hourly
gauge stage plus the post-flood trace survey, see
``data/processed/2016_event/README.md``) into the per-cross-section
:class:`~bep_reliability_engine.hydrographs.HydrographRecord` that the M8
replay consumes. The 2016 consecutive-typhoon event is built in
(:func:`default_2016_source`); a further event (for example the September
2011 flood) drops in by pointing a new :class:`ObservedEventSource` at its
own processed extracts, with zero code changes here.

Construction method (ADR-0035)
------------------------------
Stage translation from the reference gauge to a study section reuses the
Phase 1 M3 machinery verbatim, so datum handling and unit conversion happen
in exactly one place:

1. The observed stage series at the reference gauge (Obihiro, Tokachi
   KP 56.6 for 2016, hourly, m MSL) is inverted through the gauge's own
   Eq. 4.19 rating, ``Q_eq(t) = a_g * (h_obs(t) + b_g)^2``, giving the
   rating-equivalent discharge. This is exact: pushing ``Q_eq`` back
   through the gauge rating reproduces the observed series bit for bit.
2. ``Q_eq(t)`` is fed to :func:`bep_reliability_engine.hydrographs.\
build_hydrograph_record` with the study section's OWN local rating
   coefficients, exactly the ADR-0019 band philosophy (one discharge per
   reach, intensely local rating).
3. Because the 2017 rating and the observed 2016 stage-discharge pairs
   disagree at the gauge by up to ~1 m at the peak (channel change and
   loop-rating effects), the translated series is anchored to the
   field-surveyed flood-trace elevation at the section's own KP: the raw
   translated series is normalized in stage domain
   (:func:`~bep_reliability_engine.hydrographs.normalize_stage_shape`) and
   rescaled so its peak equals the surveyed trace verbatim while the trough
   floor stays pinned at the translated base-flow stage, the same G1 rule
   the Phase 1 conditioning sweep uses. The unanchored pure rating
   translation remains available (``anchor='rating'``) as a sensitivity.

The anchoring uses the local *observed* maximum water level at the levee
line; the event's temporal structure (all four typhoon peaks, the troughs,
the timing) comes verbatim from the gauge record and is never smoothed,
clipped or truncated. The full August observation window is used; the
loader quantifies that the truncated September recession is hydraulically
inert for BEP (:func:`window_closure_diagnostic`).

All stages are m MSL end to end (the datum evidence is recorded in the
processed-data README); the datum guard
:func:`~bep_reliability_engine.hydrographs.validate_datum_consistency` is
applied by the replay before any evaluation.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from bep_reliability_engine.hydrographs import (
    HydrographRecord,
    build_hydrograph_record,
    load_rating_coefficients,
    normalize_stage_shape,
    rating_curve_path,
)

__all__ = [
    "FloodTrace",
    "ObservedEventSource",
    "StageSeries",
    "default_2016_source",
    "inverse_rating_discharge",
    "observed_event_record",
    "read_flood_traces",
    "read_stage_series",
    "window_closure_diagnostic",
]

# Anchor modes for the per-section peak (ADR-0035): the surveyed trace on the
# study levee's bank (right bank for the Tokachi study sections, whose OYO
# drawings carry the R prefix), the opposite bank, or the unanchored rating
# translation (sensitivity only).
_ANCHOR_MODES: tuple[str, ...] = ("trace_right", "trace_left", "rating")

# Seconds per hour at the single ingest unit boundary (matches M3).
_SECONDS_PER_HOUR = 3600.0


@dataclass(frozen=True)
class ObservedEventSource:
    """One observed survival event's data sources and gauge assignment.

    Attributes
    ----------
    event_id : str
        Event identifier stamped into records and provenance, for example
        ``'typhoon_201608'``.
    river : str
        Study river the sections belong to (``'Tokachi'`` or ``'Satsunai'``);
        selects the rating CSV.
    gauge_station : str
        ASCII station column name of the reference gauge in the processed
        stage CSV (for example ``'obihiro'``).
    gauge_kp : float
        The reference gauge's KP on ``river``; selects the gauge's own rating
        for the inverse step.
    stage_csv : pathlib.Path
        Processed hourly stage CSV (wide, one column per station, m MSL).
    trace_csv : pathlib.Path or None
        Processed flood-trace CSV (per-KP surveyed peak elevations, m MSL),
        or None when no trace survey exists for the event (then only
        ``anchor='rating'`` is available).
    description : str
        Free-text provenance note.
    """

    event_id: str
    river: str
    gauge_station: str
    gauge_kp: float
    stage_csv: Path
    trace_csv: Path | None
    description: str = ""


@dataclass(frozen=True)
class StageSeries:
    """One gauge's uniformly sampled observed stage series.

    Attributes
    ----------
    time_hours : numpy.ndarray, shape (T,)
        Hours since the first sample (0, 1, 2, ...), native hourly cadence.
    stage_m_msl : numpy.ndarray, shape (T,)
        Observed stage [m MSL].
    t0_iso : str
        ISO timestamp (JST) of the first sample, provenance only.
    station : str
        ASCII station name the series was read from.
    """

    time_hours: NDArray[np.float64]
    stage_m_msl: NDArray[np.float64]
    t0_iso: str
    station: str


@dataclass(frozen=True)
class FloodTrace:
    """Surveyed peak water levels at one KP (post-flood trace survey).

    Attributes are m MSL; a bank without a usable trace carries NaN.
    """

    kp: float
    design_hwl_m: float
    trace_left_m: float
    trace_right_m: float


def default_2016_source(
    processed_dir: str | Path = "data/processed/2016_event",
) -> ObservedEventSource:
    """The built-in August 2016 consecutive-typhoon event (ADR-0035).

    Reference gauge: Obihiro (帯広), Tokachi KP 56.6, the ADR-0019 section 4
    validation-anchor station, 0.8 to 5.4 km downstream of the four study
    sections with no major tributary in between (the Satsunai and Otofuke
    confluences bracket the reach outside it, matching the d4PDF band
    KP 056.20 to 061.80 that Phase 1 itself uses for these sections).

    Parameters
    ----------
    processed_dir : str or pathlib.Path
        Directory of the committed processed extracts.

    Returns
    -------
    ObservedEventSource
        The 2016 event source for the Tokachi study sections.
    """
    processed = Path(processed_dir)
    return ObservedEventSource(
        event_id="typhoon_201608",
        river="Tokachi",
        gauge_station="obihiro",
        gauge_kp=56.6,
        stage_csv=processed / "stage_hourly_Tokachi_201608.csv",
        trace_csv=processed / "flood_trace_2016.csv",
        description=(
            "August 2016 consecutive typhoons (7, 11, 9, 10), Tokachi river; "
            "hourly observed stage at Obihiro; September 2016 trace survey."
        ),
    )


def read_stage_series(csv_path: str | Path, station: str) -> StageSeries:
    """Read one station's hourly stage series from a processed stage CSV.

    Parameters
    ----------
    csv_path : str or pathlib.Path
        A ``stage_hourly_{river}_{month}.csv`` extract (UTF-8, wide format,
        first column ``datetime_jst``).
    station : str
        ASCII station column name.

    Returns
    -------
    StageSeries
        The uniformly sampled series (m MSL, hourly).

    Raises
    ------
    ValueError
        If the station column is missing, any of its cells is empty or
        non-numeric (the survival replay needs a gap-free loading signal;
        gaps must be resolved at extraction, not silently interpolated
        here), or the time axis is not the uniform hourly cadence.
    """
    csv_path = Path(csv_path)
    with open(csv_path, encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    header, data = rows[0], rows[1:]
    if station not in header:
        raise ValueError(
            f"station {station!r} not in {csv_path.name} (columns: {header[1:]})"
        )
    column = header.index(station)

    stamps: list[str] = []
    values: list[float] = []
    for row in data:
        cell = row[column]
        if cell == "":
            raise ValueError(
                f"missing stage for station {station!r} at {row[0]} in "
                f"{csv_path.name}; the replay needs a gap-free series."
            )
        stamps.append(row[0])
        values.append(float(cell))

    stage = np.asarray(values, dtype=np.float64)
    t0 = np.datetime64(stamps[0])
    offsets = (np.array([np.datetime64(s) for s in stamps]) - t0) / np.timedelta64(
        1, "h"
    )
    time_hours = np.asarray(offsets, dtype=np.float64)
    diffs = np.diff(time_hours)
    if time_hours.size < 2 or not np.all(diffs == 1.0):
        raise ValueError(
            f"stage series for {station!r} in {csv_path.name} is not the "
            "uniform hourly cadence."
        )
    return StageSeries(
        time_hours=time_hours, stage_m_msl=stage, t0_iso=stamps[0], station=station
    )


def read_flood_traces(csv_path: str | Path, river: str) -> dict[float, FloodTrace]:
    """Read one river's flood-trace survey into a KP-keyed mapping.

    Parameters
    ----------
    csv_path : str or pathlib.Path
        A ``flood_trace_*.csv`` extract.
    river : str
        River name to select rows for.

    Returns
    -------
    dict of float to FloodTrace
        Per-KP surveyed peak elevations (m MSL); banks without a usable
        trace carry NaN.
    """
    csv_path = Path(csv_path)
    with open(csv_path, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        traces: dict[float, FloodTrace] = {}
        for row in reader:
            if row["river"] != river:
                continue
            kp = float(row["kp"])
            traces[kp] = FloodTrace(
                kp=kp,
                design_hwl_m=float(row["design_hwl_m_msl"] or "nan"),
                trace_left_m=float(row["trace_left_m_msl"] or "nan"),
                trace_right_m=float(row["trace_right_m_msl"] or "nan"),
            )
    if not traces:
        raise ValueError(f"no trace rows for river {river!r} in {csv_path.name}")
    return traces


# Largest tolerable low-flow excursion below the flood-rating datum before
# the series is treated as being on the wrong vertical datum outright. The
# 2016 Obihiro record dips at most 0.82 m below the 2017 rating datum during
# the pre-typhoon low-flow weeks (the flood rating from non-uniform flow
# computation has no validity at low flow); a wrong-datum series (for
# example a gauge-local zero instead of MSL) would sit tens of metres off.
_MAX_SUBDATUM_EXCURSION_M: float = 2.0


def inverse_rating_discharge(
    stage_m_msl: NDArray[np.float64], a_kp: float, b_kp: float
) -> NDArray[np.float64]:
    """Invert the Eq. 4.19 rating: stage back to rating-equivalent discharge.

    ``Q_eq = a_kp * (h + b_kp)**2``, the exact inverse of
    :func:`~bep_reliability_engine.hydrographs.apply_rating_curve`
    (``h = sqrt(Q/a) - b``), so translating ``Q_eq`` back through the same
    coefficients reproduces the observed stage bit for bit wherever the
    stage sits at or above the rating datum ``-b_kp``.

    Low-flow handling: readings BELOW the rating datum are floored to zero
    discharge. The Eq. 4.19 coefficients come from non-uniform flow
    computation of flood profiles (ADR-0019) and have no validity at low
    flow; the 2016 Obihiro record sits up to 0.82 m below the datum during
    the pre-typhoon weeks. Floored samples translate to the target
    section's own rating datum, which lies several metres below every
    study section's landside toe, so they are hydraulically inert for BEP.
    An excursion beyond :data:`_MAX_SUBDATUM_EXCURSION_M` still raises: a
    series on the wrong vertical datum must fail loudly, not be flattened.

    Parameters
    ----------
    stage_m_msl : numpy.ndarray
        Observed stage [m MSL].
    a_kp, b_kp : float
        The gauge's own rating coefficients.

    Returns
    -------
    numpy.ndarray
        Rating-equivalent discharge [m^3/s]; zero where the stage sits
        below the rating datum.

    Raises
    ------
    ValueError
        If ``a_kp`` is not positive, or any stage sits more than
        :data:`_MAX_SUBDATUM_EXCURSION_M` below the rating datum.
    """
    if not a_kp > 0.0:
        raise ValueError(f"a_kp must be positive (got {a_kp!r}).")
    head = np.asarray(stage_m_msl, dtype=np.float64) + b_kp
    worst = float(head.min())
    if worst < -_MAX_SUBDATUM_EXCURSION_M:
        raise ValueError(
            f"observed stage sits {-worst:.2f} m below the rating datum "
            f"(-b_kp = {-b_kp:.2f} m MSL), beyond the "
            f"{_MAX_SUBDATUM_EXCURSION_M} m low-flow tolerance: datum "
            "mismatch between the gauge series and the rating coefficients."
        )
    return a_kp * np.maximum(head, 0.0) ** 2


def observed_event_record(
    source: ObservedEventSource,
    *,
    section_kp: float,
    data_root: str | Path = "data/raw",
    anchor: str = "trace_right",
) -> HydrographRecord:
    """Build one study section's observed-event loading record (ADR-0035).

    The full construction of the module docstring: observed gauge stage,
    inverse rating at the gauge, forward rating at the section's own KP
    through the verbatim M3 path, then the per-section trace anchoring.

    Parameters
    ----------
    source : ObservedEventSource
        The event's data sources and gauge assignment.
    section_kp : float
        The study section's KP (must exist in the river's rating CSV and,
        for trace anchoring, in the trace survey).
    data_root : str or pathlib.Path
        Root of the raw data drop holding ``rating_curves/`` (ADR-0020
        layout).
    anchor : {'trace_right', 'trace_left', 'rating'}
        Peak anchoring mode: the surveyed trace on the right bank (default;
        the study levees' bank), the left bank, or no anchoring (pure
        rating translation, sensitivity only).

    Returns
    -------
    HydrographRecord
        The section's loading record: hourly native cadence, m MSL stages,
        ``peak`` equal to the anchor level verbatim (trace modes) or the
        translated maximum (rating mode), and full construction provenance.

    Raises
    ------
    ValueError
        On a missing rating KP, a missing or NaN trace at the section KP in
        a trace mode, an unknown anchor mode, or any upstream reader error.
    """
    if anchor not in _ANCHOR_MODES:
        raise ValueError(f"anchor {anchor!r} must be one of {_ANCHOR_MODES}.")

    series = read_stage_series(source.stage_csv, source.gauge_station)
    rating_csv = rating_curve_path(data_root, source.river)
    coefficients = load_rating_coefficients(rating_csv)
    try:
        a_gauge, b_gauge = coefficients[source.gauge_kp]
    except KeyError:
        raise ValueError(
            f"no rating coefficients at the gauge KP {source.gauge_kp} in "
            f"{rating_csv.name}."
        ) from None
    try:
        a_section, b_section = coefficients[section_kp]
    except KeyError:
        raise ValueError(
            f"no rating coefficients at section KP {section_kp} in "
            f"{rating_csv.name}."
        ) from None

    q_eq = inverse_rating_discharge(series.stage_m_msl, a_gauge, b_gauge)

    provenance = {
        "construction": "observed_stage_inverse_rating",
        "event_source": source.event_id,
        "gauge_station": series.station,
        "gauge_kp": source.gauge_kp,
        "gauge_rating_a": a_gauge,
        "gauge_rating_b": b_gauge,
        "section_kp": section_kp,
        "section_rating_a": a_section,
        "section_rating_b": b_section,
        "rating_csv": rating_csv.name,
        "stage_csv": Path(source.stage_csv).name,
        "window_start_jst": series.t0_iso,
        "window_hours": float(series.time_hours[-1] - series.time_hours[0]),
        "gauge_peak_stage_m_msl": float(series.stage_m_msl.max()),
        "anchor": anchor,
    }

    record = build_hydrograph_record(
        series.time_hours,
        q_eq,
        a_kp=a_section,
        b_kp=b_section,
        scenario="historical",
        event_id=f"{source.event_id}_kp{section_kp:g}",
        provenance=provenance,
    )
    if anchor == "rating":
        return record

    if source.trace_csv is None:
        raise ValueError(
            f"event {source.event_id!r} has no trace survey; only "
            "anchor='rating' is available."
        )
    traces = read_flood_traces(source.trace_csv, source.river)
    try:
        trace = traces[round(float(section_kp), 1)]
    except KeyError:
        raise ValueError(
            f"no flood trace at KP {section_kp} for the {source.river}."
        ) from None
    level = trace.trace_right_m if anchor == "trace_right" else trace.trace_left_m
    if not np.isfinite(level):
        raise ValueError(
            f"flood trace at KP {section_kp} has no usable {anchor} value; "
            "use the other bank or anchor='rating'."
        )

    # G1-style amplitude anchoring (ADR-0035): trough floor pinned at the
    # translated base-flow stage, peak set to the surveyed trace verbatim.
    shape, h_base_m, h_peak_raw = normalize_stage_shape(record.h)
    anchored_h = h_base_m + (level - h_base_m) * shape
    return HydrographRecord(
        t=record.t,
        h=anchored_h,
        peak=float(level),
        duration_hours=record.duration_hours,
        scenario=record.scenario,
        event_id=record.event_id,
        native_dt=record.native_dt,
        provenance={
            **record.provenance,
            "trace_csv": Path(source.trace_csv).name,
            "trace_anchor_m_msl": float(level),
            "translated_peak_m_msl": float(h_peak_raw),
            "translated_base_m_msl": float(h_base_m),
            "anchor_minus_translated_m": float(level - h_peak_raw),
        },
    )


def window_closure_diagnostic(
    record: HydrographRecord, z_toe_m: float
) -> dict[str, float | bool]:
    """Quantify whether the observation window contains the erosive loading.

    The 2016 stage observations end early in the final recession (the
    September stage sheet of the source workbook is corrupted, see the
    processed-data README). Truncation is harmless for BEP if and only if
    the stage at the window end is already below the landside toe: below
    ``z_toe`` the erosion head is negative and the progression rate is
    identically zero (Pol SIE 2024 Eq. 6 under ADR-0027), so the lost
    recession can drive no further pipe growth.

    Parameters
    ----------
    record : HydrographRecord
        The section's observed-event record.
    z_toe_m : float
        The section's landside-toe elevation [m MSL] (ADR-0021).

    Returns
    -------
    dict
        ``closed`` (bool): end stage below the toe; ``end_stage_m_msl``,
        ``end_margin_below_toe_m`` (positive = below toe),
        ``hours_after_last_exceedance`` (hours between the last sample at
        or above the toe and the window end; 0 means the window ends
        loaded), ``peak_m_msl``.
    """
    h = np.asarray(record.h, dtype=np.float64)
    end_stage = float(h[-1])
    above = np.nonzero(h >= z_toe_m)[0]
    if above.size:
        dt_hours = record.native_dt / _SECONDS_PER_HOUR
        hours_after = float((h.size - 1 - above[-1]) * dt_hours)
    else:
        hours_after = float(record.duration_hours)
    return {
        "closed": bool(end_stage < z_toe_m),
        "end_stage_m_msl": end_stage,
        "end_margin_below_toe_m": float(z_toe_m - end_stage),
        "hours_after_last_exceedance": hours_after,
        "peak_m_msl": float(record.peak),
    }
