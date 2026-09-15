"""Validated instantaneous records and left-endpoint interval loads (ADR-0053)."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def validate_interval_loads(h: ArrayLike, dt_s: float) -> NDArray[np.float64]:
    """Validate finite, one-dimensional left-endpoint loads and positive dt."""
    values = np.asarray(h, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("hydrograph requires a finite stage series (1-D array)")
    if not np.isfinite(dt_s) or dt_s <= 0:
        raise ValueError("hydrograph native_dt must be finite and positive")
    return values


def validate_record(record: object) -> NDArray[np.float64]:
    """Validate a duck-typed instantaneous record without redefining its peak.

    A single sample denotes a zero-span record. When supplied, time must
    agree with the authoritative uniform native_dt; absolute origins are valid.
    """
    h = validate_interval_loads(record.h, float(record.native_dt))
    if not h.size:
        raise ValueError("hydrograph needs at least one instantaneous sample")
    if not np.isfinite(record.peak):
        raise ValueError("hydrograph peak must be finite")
    if hasattr(record, "t"):
        t = np.asarray(record.t, dtype=np.float64)
        if t.shape != h.shape or not np.all(np.isfinite(t)):
            raise ValueError("hydrograph times must be finite and match stages")
        if not np.allclose(np.diff(t), record.native_dt, rtol=1e-6, atol=0):
            raise ValueError("hydrograph times must increase uniformly at native_dt")
    return h
