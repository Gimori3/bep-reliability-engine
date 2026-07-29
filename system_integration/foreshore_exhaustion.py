"""Foreshore-exhaustion screening indicator (review item R10, Tier 1).

**This module is a screening indicator and nothing else.** It is deliberately
not imported by :mod:`system_integration.composition`, contributes no
mechanism to the Phase 3 series system, and leaves every persisted Phase 3
number bit-identical — the same standing as
:func:`system_integration.segments.load_kasumi_tei`. Tier 2 of
``docs/scoping_bank_retreat_mechanism.md`` (a stage-conditioned
``P_f,retreat(h)`` that *would* join the composition) is explicitly declined
and would need its own ADR.

Why it exists
-------------
Phase 3 composes BEP, overflow and fluvial scour per segment, and under the
ADR-0042 decision 9 dimensionally-corrected conversion the scour branch is
exactly zero at all 114 segments in both climate scenarios. Yet the
documented failure record for this system is dominated by channel migration
consuming the high-water bed in front of the levee (2011-09 Otofuke KP 18.2;
2016-08 Otofuke KP 21.2 and Satsunai KP 40.5). Uemura's P2 cannot represent
that chain: its shear comes from a uniform-flow Manning velocity keyed on
*floodplain inundation depth*, and its input record carries no thalweg
position, no bend curvature and no foreshore width, so it has no state in
which a receding flood is more dangerous than a peak one.

The state variable the represented mechanism set lacks is the **remaining
high-water-bed width**, and the failure condition is its exhaustion. This
module supplies the deterministic screening form of that condition:

.. code-block:: text

    time_to_exhaustion  =  B_f / v_lat
    cumulative_retreat  =  v_lat * (time the flood mobilises the bed)
    exposure_ratio      =  cumulative_retreat / B_f

``exposure_ratio >= 1`` means the event is, on this bounding treatment,
capable of consuming the high-water bed and reaching the embankment.

What it is not
--------------
It is order-of-magnitude screening. It is **not** a probability and **not** a
failure rate. It carries no planform, no bend mechanics, no sediment supply,
and no representation of *why* a thalweg approaches one bank rather than
another. It answers "is there enough high-water bed to survive this flood at
this assumed retreat rate", never "will this levee fail".

The retreat rate is the weak link and is treated as such: no rate is
calibrated here. :data:`RETREAT_RATE_BRACKET_M_PER_H` spans two orders of
magnitude and every result must be reported across it. The one documented
datum for this basin — ~5 m of levee **length** lost per hour at Otofuke
KP 18.2 in September 2011 — is a *longitudinal* rate from a prose account in
a flood-control history, not a calibrated lateral retreat rate; it enters the
bracket as the labelled ``narrative_2011`` member on the stated assumption
that it is used unconverted as a lateral proxy, and nowhere else.

State variables and their sources
---------------------------------
``foreshore_width_m`` (B_f) is the OYO 様式-3 高水敷幅 (high-water-bed width)
of ``data/processed/tokachi_bep_inputs.csv``, source-verified 4/4 verbatim
and retained over the MLIT 2008 profile by the ADR-0025 companion
(``docs/decisions/adr0025-foreshore-width-and-sensitivity.md``). It is
measured at the four confined OYO cross-sections only; the remaining
segments carry no measured width and are reported as an explicit coverage
gap rather than interpolated.

``mobilisation_stage_m_msl`` (z_mob) is the high-water-bed surface elevation
— the stage at which the flood stops being confined to the low-water channel
and engages the terrace. It is taken from ``floodplain_m_msl`` of
``data/processed/uemura_segments/segment_inputs.csv`` (Uemura's df_river
``FloodplaneHeight``, T.P. m MSL, the same datum as every other stage in the
three packages), which exists at all 114 segments. The threshold is a
*choice*, not a measurement: a lower threshold (bank-toe attack while the
flood is still in-channel) lengthens the mobilising window, so the driver
brackets it as well.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

from system_integration.segments import SegmentRegistry

__all__ = [
    "OYO_FORESHORE_CSV",
    "RETREAT_RATE_BRACKET_M_PER_H",
    "SEGMENT_INPUTS_CSV",
    "ExhaustionResult",
    "ForeshoreState",
    "critical_retreat_rate_m_per_h",
    "foreshore_coverage",
    "foreshore_exhaustion",
    "load_measured_foreshore_states",
    "mobilising_duration_hours",
]

#: The geotechnical source of truth carrying the OYO 高水敷幅 column.
OYO_FORESHORE_CSV = Path("data/processed/tokachi_bep_inputs.csv")

#: Per-segment Uemura inputs carrying the high-water-bed surface elevation.
SEGMENT_INPUTS_CSV = Path("data/processed/uemura_segments/segment_inputs.csv")

#: Lateral retreat-rate bracket [m/h]. Spans two orders of magnitude on
#: purpose: there is no calibrated rate for this mechanism on this river.
#: ``narrative_2011`` is the 2011 Otofuke KP 18.2 figure of ~5 m of levee
#: *length* per hour, carried across to a lateral rate WITHOUT conversion —
#: a stated assumption, not a derivation, and one observation from a prose
#: account rather than a measurement campaign.
RETREAT_RATE_BRACKET_M_PER_H: dict[str, float] = {
    "low": 0.1,
    "central": 1.0,
    "narrative_2011": 5.0,
    "high": 10.0,
}

_KP_TOL = 1e-6


@dataclass(frozen=True)
class ForeshoreState:
    """One segment's screening state: measured bed width and its threshold.

    Attributes
    ----------
    river : str
        ``'Tokachi'`` or ``'Satsunai'``.
    bank : str
        ``'right'`` or ``'left'``.
    kp : float
        Segment node KP [km].
    foreshore_width_m : float
        B_f, the measured 高水敷幅 [m]. Zero means *no high-water bed*, i.e.
        the low-water channel already reaches the levee line.
    mobilisation_stage_m_msl : float
        z_mob, the high-water-bed surface elevation [m MSL]; the flood
        mobilises the bed while the stage stands strictly above it.
    width_source : str
        Provenance stamp for ``foreshore_width_m``.
    stage_source : str
        Provenance stamp for ``mobilisation_stage_m_msl``.
    """

    river: str
    bank: str
    kp: float
    foreshore_width_m: float
    mobilisation_stage_m_msl: float
    width_source: str
    stage_source: str


@dataclass(frozen=True)
class ExhaustionResult:
    """The screening indicator for one (segment, forcing, retreat rate).

    Attributes
    ----------
    mobilising_hours : float
        Time the stage stands strictly above ``z_mob`` [h].
    record_hours : float
        Total length of the forcing record [h] — the bounding duration a
        threshold of minus infinity would give.
    retreat_rate_m_per_h : float
        The assumed lateral retreat rate while mobilising [m/h].
    cumulative_retreat_m : float
        ``retreat_rate_m_per_h * mobilising_hours`` [m].
    time_to_exhaustion_h : float
        ``foreshore_width_m / retreat_rate_m_per_h`` [h]: mobilising hours
        the segment can absorb before the bed is gone. ``0.0`` when there
        is no bed to begin with.
    exposure_ratio : float
        ``cumulative_retreat_m / foreshore_width_m``; ``inf`` when
        ``foreshore_width_m == 0``. The screening flag is ``>= 1``.
    exhausted : bool
        ``exposure_ratio >= 1``.
    peak_stage_m_msl : float
        Peak of the forcing record [m MSL].
    peak_excess_depth_m : float
        ``max(peak - z_mob, 0)`` [m] — how deeply the bed is engaged at the
        peak. Diagnostic only: the indicator itself is depth-independent.
    mean_excess_depth_m : float
        Mean of ``stage - z_mob`` over the mobilising samples [m]; ``0.0``
        when the bed is never mobilised. Diagnostic only. Its ratio to
        ``peak_excess_depth_m`` is the factor by which any monotone
        depth-dependent rate law, calibrated to the same peak rate, would
        *reduce* ``exposure_ratio`` — which is why the constant-rate
        treatment used here is the bounding one.
    """

    mobilising_hours: float
    record_hours: float
    retreat_rate_m_per_h: float
    cumulative_retreat_m: float
    time_to_exhaustion_h: float
    exposure_ratio: float
    exhausted: bool
    peak_stage_m_msl: float
    peak_excess_depth_m: float
    mean_excess_depth_m: float


def _as_stage_array(stage_m_msl: ArrayLike) -> NDArray[np.float64]:
    """Validate and return the forcing stage series as a 1-D float array."""
    stage = np.atleast_1d(np.asarray(stage_m_msl, dtype=np.float64))
    if stage.ndim != 1:
        raise ValueError(
            f"stage_m_msl must be one-dimensional, got shape {stage.shape}."
        )
    if stage.size and not np.all(np.isfinite(stage)):
        raise ValueError("stage_m_msl contains non-finite samples.")
    return stage


def mobilising_duration_hours(
    stage_m_msl: ArrayLike, dt_seconds: float, threshold_m_msl: float
) -> float:
    """Time the stage stands strictly above a threshold elevation [h].

    Sample counting on the record's own uniform grid, matching
    :func:`system_integration.hazard._above_datum_measures` (``h > datum``,
    strictly above) so the two exposure measures cannot drift apart.

    Parameters
    ----------
    stage_m_msl : array_like, shape (T,)
        Stage series [m MSL], uniformly sampled at ``dt_seconds``.
    dt_seconds : float
        Sampling interval [s]; must be positive.
    threshold_m_msl : float
        The mobilisation threshold elevation [m MSL].

    Returns
    -------
    float
        Mobilising duration [h]; ``0.0`` for an empty record or a threshold
        the record never exceeds.

    Raises
    ------
    ValueError
        If ``dt_seconds`` is not positive, ``threshold_m_msl`` is not
        finite, or the stage series is not finite/1-D.
    """
    if not dt_seconds > 0.0:
        raise ValueError(f"dt_seconds must be positive, got {dt_seconds!r}.")
    if not math.isfinite(threshold_m_msl):
        raise ValueError(f"threshold_m_msl must be finite, got {threshold_m_msl!r}.")
    stage = _as_stage_array(stage_m_msl)
    return float((stage > threshold_m_msl).sum() * dt_seconds / 3600.0)


def foreshore_exhaustion(
    stage_m_msl: ArrayLike,
    dt_seconds: float,
    *,
    foreshore_width_m: float,
    mobilisation_stage_m_msl: float,
    retreat_rate_m_per_h: float,
) -> ExhaustionResult:
    """Screen one forcing record against one segment's high-water bed.

    The retreat rate is held constant while the bed is mobilised. That is
    the bounding treatment: any monotone depth-dependent law calibrated to
    the same peak rate erodes less over the same event (see
    ``ExhaustionResult.mean_excess_depth_m``).

    Parameters
    ----------
    stage_m_msl : array_like, shape (T,)
        Forcing stage series [m MSL], uniformly sampled at ``dt_seconds``.
        Injected, never constructed here — this module contains no physics
        and no hydrology.
    dt_seconds : float
        Sampling interval [s].
    foreshore_width_m : float
        B_f [m]; must be finite and non-negative. ``0.0`` is the
        already-exhausted state: the result is ``exposure_ratio = inf``,
        ``time_to_exhaustion_h = 0.0``, ``exhausted = True``, whatever the
        forcing does, because there is no bed left to consume.
    mobilisation_stage_m_msl : float
        z_mob [m MSL], the high-water-bed surface.
    retreat_rate_m_per_h : float
        Lateral retreat rate while mobilising [m/h]; must be strictly
        positive. Take it from :data:`RETREAT_RATE_BRACKET_M_PER_H` and
        report across the whole bracket — a single value is false
        precision.

    Returns
    -------
    ExhaustionResult

    Raises
    ------
    ValueError
        On a non-positive ``dt_seconds`` or ``retreat_rate_m_per_h``, a
        negative or non-finite ``foreshore_width_m``, a non-finite
        threshold, or a non-finite/non-1-D stage series.
    """
    if not retreat_rate_m_per_h > 0.0:
        raise ValueError(
            "retreat_rate_m_per_h must be strictly positive, got "
            f"{retreat_rate_m_per_h!r}."
        )
    if not math.isfinite(foreshore_width_m) or foreshore_width_m < 0.0:
        raise ValueError(
            "foreshore_width_m must be finite and non-negative, got "
            f"{foreshore_width_m!r}."
        )
    hours = mobilising_duration_hours(stage_m_msl, dt_seconds, mobilisation_stage_m_msl)
    stage = _as_stage_array(stage_m_msl)
    record_hours = float(stage.size * dt_seconds / 3600.0)
    peak = float(stage.max()) if stage.size else float("nan")
    excess = stage - mobilisation_stage_m_msl
    mobilising = excess > 0.0
    retreat = retreat_rate_m_per_h * hours

    if foreshore_width_m == 0.0:
        time_to_exhaustion = 0.0
        ratio = float("inf")
    else:
        time_to_exhaustion = foreshore_width_m / retreat_rate_m_per_h
        ratio = retreat / foreshore_width_m

    return ExhaustionResult(
        mobilising_hours=hours,
        record_hours=record_hours,
        retreat_rate_m_per_h=float(retreat_rate_m_per_h),
        cumulative_retreat_m=retreat,
        time_to_exhaustion_h=time_to_exhaustion,
        exposure_ratio=ratio,
        exhausted=bool(ratio >= 1.0),
        peak_stage_m_msl=peak,
        peak_excess_depth_m=(
            float(max(peak - mobilisation_stage_m_msl, 0.0)) if stage.size else 0.0
        ),
        mean_excess_depth_m=(
            float(excess[mobilising].mean()) if mobilising.any() else 0.0
        ),
    )


def critical_retreat_rate_m_per_h(
    foreshore_width_m: float, mobilising_hours: float
) -> float:
    """The retreat rate at which this event exactly exhausts the bed [m/h].

    The inverse reading of :func:`foreshore_exhaustion`: rather than asking
    "is this segment exposed at an assumed rate", it asks "what rate would
    it take". Reporting this alongside
    :data:`RETREAT_RATE_BRACKET_M_PER_H` is the honest presentation — it
    puts the whole bracket question on one axis instead of hiding the
    assumption inside a binary flag.

    Parameters
    ----------
    foreshore_width_m : float
        B_f [m]; finite and non-negative.
    mobilising_hours : float
        Time the event mobilises the bed [h]; finite and non-negative.

    Returns
    -------
    float
        ``foreshore_width_m / mobilising_hours``. ``inf`` when the event
        never mobilises the bed (no rate suffices); ``0.0`` when there is
        no bed to consume (any positive rate suffices).

    Raises
    ------
    ValueError
        On negative or non-finite arguments.
    """
    if not math.isfinite(foreshore_width_m) or foreshore_width_m < 0.0:
        raise ValueError(
            "foreshore_width_m must be finite and non-negative, got "
            f"{foreshore_width_m!r}."
        )
    if not math.isfinite(mobilising_hours) or mobilising_hours < 0.0:
        raise ValueError(
            "mobilising_hours must be finite and non-negative, got "
            f"{mobilising_hours!r}."
        )
    if foreshore_width_m == 0.0:
        return 0.0
    if mobilising_hours == 0.0:
        return float("inf")
    return foreshore_width_m / mobilising_hours


def _read_measured_widths(csv_path: str | Path) -> dict[tuple[str, float], float]:
    """(river, kp) -> measured 高水敷幅 [m] from the geotech CSV."""
    widths: dict[tuple[str, float], float] = {}
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            widths[(row["river"], float(row["kp"]))] = float(row["foreshore_width_m"])
    if not widths:
        raise ValueError(f"{Path(csv_path).name}: no rows.")
    return widths


def _read_mobilisation_stages(csv_path: str | Path) -> dict[tuple[str, float], float]:
    """(river, kp) -> high-water-bed surface elevation [m MSL]."""
    stages: dict[tuple[str, float], float] = {}
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            stages[(row["river"], float(row["kp"]))] = float(row["floodplain_m_msl"])
    if not stages:
        raise ValueError(f"{Path(csv_path).name}: no rows.")
    return stages


def load_measured_foreshore_states(
    registry: SegmentRegistry,
    *,
    foreshore_csv: str | Path = OYO_FORESHORE_CSV,
    segment_inputs_csv: str | Path = SEGMENT_INPUTS_CSV,
) -> tuple[ForeshoreState, ...]:
    """Registry segments that carry BOTH a measured B_f and a threshold.

    A segment is screenable only where the high-water-bed width was actually
    surveyed. That is the four confined OYO cross-sections; every other
    segment is left out rather than given an interpolated width it does not
    have. Use :func:`foreshore_coverage` to report the gap.

    Parameters
    ----------
    registry : SegmentRegistry
        Typically :func:`system_integration.segments.build_registry`.
    foreshore_csv : str or pathlib.Path
        Geotechnical CSV carrying ``kp``, ``river`` and
        ``foreshore_width_m`` (the OYO 高水敷幅).
    segment_inputs_csv : str or pathlib.Path
        Per-segment inputs carrying ``river``, ``kp`` and
        ``floodplain_m_msl``.

    Returns
    -------
    tuple of ForeshoreState
        Ordered by (river, kp).

    Raises
    ------
    ValueError
        If either CSV is empty, or a segment has a measured width but no
        mobilisation stage (an inconsistent input pair, not a data gap).
    """
    widths = _read_measured_widths(foreshore_csv)
    stages = _read_mobilisation_stages(segment_inputs_csv)
    width_source = f"{Path(foreshore_csv).name}:foreshore_width_m (OYO 高水敷幅)"
    stage_source = f"{Path(segment_inputs_csv).name}:floodplain_m_msl"

    states: list[ForeshoreState] = []
    for segment in registry.segments:
        match = [
            width
            for (river, kp), width in widths.items()
            if river == segment.river and abs(kp - segment.kp) <= _KP_TOL
        ]
        if not match:
            continue
        stage_match = [
            stage
            for (river, kp), stage in stages.items()
            if river == segment.river and abs(kp - segment.kp) <= _KP_TOL
        ]
        if not stage_match:
            raise ValueError(
                f"{segment.river} KP {segment.kp:g} has a measured foreshore "
                f"width but no floodplain elevation in "
                f"{Path(segment_inputs_csv).name}."
            )
        states.append(
            ForeshoreState(
                river=segment.river,
                bank=segment.bank,
                kp=segment.kp,
                foreshore_width_m=float(match[0]),
                mobilisation_stage_m_msl=float(stage_match[0]),
                width_source=width_source,
                stage_source=stage_source,
            )
        )
    return tuple(states)


def foreshore_coverage(
    registry: SegmentRegistry, states: tuple[ForeshoreState, ...]
) -> dict[str, object]:
    """The honest coverage statement for a screening run.

    Parameters
    ----------
    registry : SegmentRegistry
        The full study-reach segment set.
    states : tuple of ForeshoreState
        The screenable subset, from :func:`load_measured_foreshore_states`.

    Returns
    -------
    dict
        ``n_segments``, ``n_screened``, ``n_without_measured_width``,
        ``screened_fraction`` and the screened ``nodes`` as
        ``'<river> KP <kp>'`` labels.
    """
    n_segments = len(registry.segments)
    return {
        "n_segments": n_segments,
        "n_screened": len(states),
        "n_without_measured_width": n_segments - len(states),
        "screened_fraction": (len(states) / n_segments) if n_segments else 0.0,
        "nodes": [f"{s.river} KP {s.kp:g}" for s in states],
    }
