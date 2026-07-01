"""M3 ``hydrograph_loader``: discharge ensemble I/O and stage translation.

Single responsibility (spec §1, M3): ingest the d4PDF discharge ensemble, apply
the per-KP H-Q rating curve to turn discharge Q(t) into river stage h(t), and
expose each event as a clean :class:`HydrographRecord` (spec §2) carrying the time
axis, stage series, peak, duration, scenario tag and native resolution. This
module also **isolates all unit handling at the ingest boundary** (spec §1,
docs/conventions.md): everything downstream of :func:`build_hydrograph_record`
works in strict SI base units.

What is built here, and what is not
-----------------------------------
Everything that does **not** depend on the (still unknown) on-disk file format is
implemented and exercised by ``tests/test_m3.py``:

* :func:`apply_rating_curve` — the pure Q -> h conversion.
* :func:`build_hydrograph_record` — the pure record-construction seam **and the
  unit boundary**: it takes time in the source's native unit (hours) and Q in
  m^3/s, converts the time axis to SI seconds, applies the rating curve, derives
  ``native_dt`` from the actual (converted) spacing, and validates the axis.
* :class:`HydrographRecord` — the spec §2 output contract (the same schema the
  ``run.py`` M3 stub currently duck-types).

The **file reader** :func:`_read_discharge_series` is a deliberately marked stub:
its body cannot be written until the real d4PDF file layout is known, and the
format must not be guessed. Its docstring specifies exactly what it must return so
the one-line composition :func:`load_hydrograph` works unchanged once it is
filled. Keeping the reader as a dumb parser (raw columns, native units, *no* unit
conversion) is what lets the conversion and record logic be tested now, without a
file on disk.

Units at the boundary (spec §1; the M4 m/s-vs-m/day lesson)
-----------------------------------------------------------
The source is at 1-hour resolution with time in hours and discharge in m^3/s.
:func:`build_hydrograph_record` converts time to **seconds** (``t = time_hours *
3600``) so ``native_dt`` and ``t`` are SI, matching the M7 timestepper and the
``run.py`` stub; ``duration_hours`` is the elapsed span in hours. ``native_dt`` is
**derived** from the real spacing, never assumed to be 3600 s — a non-hourly
source comes back as the correct number of seconds. Placing this conversion
inside the pure function (not the file reader) is the M3 analogue of the M4
conductivity unit trap: a dropped hours->seconds step is caught by a test that
runs without any file.

.. warning::
   **PROVISIONAL RATING-CURVE FORM — confirm with Uemura-san.**
   :func:`apply_rating_curve` assumes the two-coefficient power law

       h(Q) = a_h * Q ** b_h

   This functional form is **not yet confirmed**; it is a placeholder pending the
   Chapter 3 coefficients and functional form from Uemura-san. It is the single
   point to change if the confirmed form differs (linear ``a_h + b_h*Q``, semi-log
   ``a_h + b_h*ln Q``, an added datum offset, or different units of Q); the golden
   values in ``tests/test_m3.py`` must be recomputed alongside any such change.

References
----------
Spec §1 (M3 responsibility, unit isolation), §2 (``HydrographRecord`` contract),
§11 (native resolution / rising-limb resolution check). docs/conventions.md
(strict SI base units; unit conversions only at the M1/M3 boundary).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = [
    "HydrographRecord",
    "apply_rating_curve",
    "build_hydrograph_record",
    "load_hydrograph",
]

# Exact SI conversion for the ingest boundary; the source expresses time in hours.
_SECONDS_PER_HOUR: float = 3600.0

# Relative tolerance for the uniform-spacing check. The source is nominally at a
# fixed native resolution, so the spacing must be constant to within float noise;
# a genuinely irregular axis (native_dt ill-defined) is rejected.
_SPACING_RTOL: float = 1e-6


@dataclass(frozen=True)
class HydrographRecord:
    """One loaded event: stage series plus metadata (the spec §2 M3 output).

    Emitted by :func:`build_hydrograph_record` (and, once the format is known, by
    :func:`load_hydrograph`). The field names mirror the schema the ``run.py`` M3
    stub duck-types; M8 reads only ``h``, ``peak`` and ``native_dt``, while the
    remaining fields carry provenance and the static-comparison scalar.

    Attributes
    ----------
    t : numpy.ndarray, shape (T,)
        Time axis in **seconds** (SI), strictly increasing and uniformly spaced.
    h : numpy.ndarray, shape (T,)
        River stage h(t) [m above datum], the rating curve applied to Q(t).
    peak : float
        Peak stage max(h) [m above datum]; the scalar the static branch compares
        against (spec §3 step 4).
    duration_hours : float
        Elapsed event span in hours (``(t[-1] - t[0]) / 3600``).
    scenario : str
        Climate scenario tag, ``'historical'`` or ``'+4K'``; flows through to the
        ``FragilityResult`` metadata and the climate comparison.
    event_id : str
        Event identifier (ensemble member / event key).
    native_dt : float
        Native temporal resolution [s], derived from the time-array spacing; the
        default integration timestep and the spec §11 rising-limb-resolution check.
    """

    t: NDArray[np.float64]
    h: NDArray[np.float64]
    peak: float
    duration_hours: float
    scenario: str
    event_id: str
    native_dt: float


def apply_rating_curve(
    discharge_m3s: ArrayLike, a_h: float, b_h: float
) -> NDArray[np.float64]:
    """Convert discharge Q(t) to river stage h(t) via the H-Q rating curve.

    PROVISIONAL power-law form (pending Uemura-san; see the module warning)::

        h(Q) = a_h * Q ** b_h

    Pure and elementwise, so it maps a scalar Q to a scalar stage and a discharge
    array to a stage array of the same shape. This is the single conversion point:
    :func:`build_hydrograph_record` calls it, so revising the rating-curve form
    here propagates through the record with no separate code path.

    Parameters
    ----------
    discharge_m3s : array_like
        Discharge Q [m^3/s]; scalar or array. Assumed non-negative (a fractional
        ``b_h`` on a negative Q is not physical and yields NaN).
    a_h, b_h : float
        The per-KP rating-curve coefficients (multiplier and exponent).

    Returns
    -------
    numpy.ndarray
        River stage h [m above datum], same shape as ``discharge_m3s``.
    """
    discharge = np.asarray(discharge_m3s, dtype=np.float64)
    return a_h * np.power(discharge, b_h)


def build_hydrograph_record(
    time_hours: ArrayLike,
    discharge_m3s: ArrayLike,
    *,
    a_h: float,
    b_h: float,
    scenario: str,
    event_id: str,
) -> HydrographRecord:
    """Build a :class:`HydrographRecord` from a native-unit discharge series.

    The pure record-construction seam **and the unit boundary** (spec §1). Given
    time in the source's native unit (hours) and discharge in m^3/s, it:

    1. validates that the time axis is strictly increasing and uniformly spaced;
    2. converts the time axis to SI seconds (``t = time_hours * 3600``);
    3. derives ``native_dt`` [s] from the converted spacing (never assumed 3600 s);
    4. applies :func:`apply_rating_curve` to produce h(t); and
    5. records the peak stage and the elapsed duration in hours.

    Deliberately independent of any file: it takes in-memory arrays, so the
    conversion and construction logic is testable before the file format is known
    (``tests/test_m3.py``). The file reader (:func:`_read_discharge_series`) feeds
    it raw native-unit columns and does no conversion of its own.

    Parameters
    ----------
    time_hours : array_like, shape (T,)
        Time axis in **hours** (native source unit), strictly increasing and
        uniformly spaced; ``T >= 2`` so the spacing is defined.
    discharge_m3s : array_like, shape (T,)
        Discharge Q(t) [m^3/s], same length as ``time_hours``.
    a_h, b_h : float
        Per-KP rating-curve coefficients passed to :func:`apply_rating_curve`.
    scenario : str
        Climate scenario tag (``'historical'`` or ``'+4K'``); carried through.
    event_id : str
        Event identifier; carried through.

    Returns
    -------
    HydrographRecord
        The event with ``t``/``native_dt`` in seconds and ``h`` from the rating
        curve.

    Raises
    ------
    ValueError
        If the time and discharge lengths differ, if fewer than two samples are
        given, or if the time axis is not strictly increasing or not uniformly
        spaced (``native_dt`` would be ill-defined).
    """
    time_hours_arr = np.asarray(time_hours, dtype=np.float64)
    discharge = np.asarray(discharge_m3s, dtype=np.float64)

    if time_hours_arr.ndim != 1 or discharge.ndim != 1:
        raise ValueError("time_hours and discharge_m3s must be 1-D arrays.")
    if time_hours_arr.shape != discharge.shape:
        raise ValueError(
            "time_hours and discharge_m3s must have the same length "
            f"(got {time_hours_arr.shape} and {discharge.shape})."
        )
    if time_hours_arr.size < 2:
        raise ValueError(
            "need at least two samples to derive native_dt "
            f"(got {time_hours_arr.size})."
        )

    diffs_hours = np.diff(time_hours_arr)
    if np.any(diffs_hours <= 0.0):
        raise ValueError("time axis must be strictly increasing.")
    dt_hours = float(diffs_hours[0])
    if not np.allclose(diffs_hours, dt_hours, rtol=_SPACING_RTOL, atol=0.0):
        raise ValueError(
            "time axis must be uniformly spaced (native_dt is a single scalar "
            "resolution); got non-constant spacing."
        )

    # Unit boundary: hours -> SI seconds. native_dt is derived from the converted
    # spacing, so a non-hourly source yields the correct number of seconds.
    t_seconds = time_hours_arr * _SECONDS_PER_HOUR
    native_dt = dt_hours * _SECONDS_PER_HOUR

    h = apply_rating_curve(discharge, a_h, b_h)
    duration_hours = float(time_hours_arr[-1] - time_hours_arr[0])

    return HydrographRecord(
        t=t_seconds,
        h=h,
        peak=float(h.max()),
        duration_hours=duration_hours,
        scenario=scenario,
        event_id=event_id,
        native_dt=float(native_dt),
    )


# ============================================================================
# FILE-READING SEAM — STUB. Do not guess the d4PDF format; fill this in once the
# real layout is known. Everything above is format-independent and tested.
# ============================================================================
def _read_discharge_series(
    path: str | Path,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Read one d4PDF discharge event from disk (STUB — format unknown).

    .. note:: TODO(M3 file format) — not yet implemented; the on-disk d4PDF layout
       is not yet known and must **not** be guessed.

    Source context (from Uemura-san's email; confirm exact layout on arrival)
    ------------------------------------------------------------------------
    * The data are **discharge time series Q(t)**, not stage — the H-Q conversion
      to river stage happens here in M3 via :func:`apply_rating_curve`.
    * Native temporal resolution is **1 hour**.
    * Two separate ensembles are delivered — the **historical** ensemble and the
      **+4K** (warmed-climate) ensemble; the ``scenario`` tag distinguishes them.
    * The rating-curve coefficients ``a_h``/``b_h`` are **per-KP** (one pair per
      cross-section), so they are supplied by the caller/config to
      :func:`load_hydrograph`, not read here.
    * The files live in the **shared Dropbox** (project data folder); ``path``
      points into that synced location once it is populated.

    Contract this stub must satisfy once filled, so :func:`load_hydrograph` works
    unchanged:

    * Parse one event's discharge time series from ``path`` and return the raw
      columns ``(time_hours, discharge_m3s)`` as ``float64`` arrays of equal
      length, **in the source's native units** — time in hours, discharge in
      m^3/s.
    * Do **no** unit conversion, rating-curve application, or metadata derivation:
      those belong to :func:`build_hydrograph_record`, which is the single unit
      boundary. This function stays a dumb parser.
    * The source is at 1-hour native resolution; the returned time axis should be
      strictly increasing and uniformly spaced (``build_hydrograph_record``
      re-validates this and derives ``native_dt`` from it).
    * Handle both the historical and +4K ensembles (the scenario tag and event_id
      are supplied by the caller / config, not inferred here unless the format
      encodes them).

    Parameters
    ----------
    path : str or pathlib.Path
        Location of the discharge series for one event.

    Returns
    -------
    tuple of (numpy.ndarray, numpy.ndarray)
        ``(time_hours, discharge_m3s)`` in native units.

    Raises
    ------
    NotImplementedError
        Always, until the real d4PDF file format is known and implemented.
    """
    raise NotImplementedError(
        "M3 file reader is not implemented: the d4PDF discharge file format is "
        "not yet known. Once it is, return (time_hours, discharge_m3s) in native "
        "units per this function's docstring; the conversion and record logic in "
        "build_hydrograph_record is already implemented and tested."
    )


def load_hydrograph(
    path: str | Path,
    *,
    a_h: float,
    b_h: float,
    scenario: str,
    event_id: str,
) -> HydrographRecord:
    """Load one event from disk as a :class:`HydrographRecord` (thin composition).

    The intended one-line seam composition (spec §2): read the raw native-unit
    discharge columns, then hand them to the pure :func:`build_hydrograph_record`
    (the unit boundary + rating-curve application). It is blocked only on
    :func:`_read_discharge_series`, the format stub; the construction half is
    already implemented and tested.

    Parameters
    ----------
    path : str or pathlib.Path
        Location of the discharge series for one event.
    a_h, b_h : float
        Per-KP rating-curve coefficients.
    scenario : str
        Climate scenario tag (``'historical'`` or ``'+4K'``).
    event_id : str
        Event identifier.

    Returns
    -------
    HydrographRecord
        The loaded, stage-translated event.

    Raises
    ------
    NotImplementedError
        Until :func:`_read_discharge_series` is implemented for the real format.
    """
    time_hours, discharge_m3s = _read_discharge_series(path)
    return build_hydrograph_record(
        time_hours,
        discharge_m3s,
        a_h=a_h,
        b_h=b_h,
        scenario=scenario,
        event_id=event_id,
    )
