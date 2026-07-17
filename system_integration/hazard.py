"""d4PDF stage-frequency and event characteristics at a study node (RQ4).

ADR-0038 decision 3. Each band-workbook member column is one
annual-maximum flood event of one simulated ensemble-year (HPB: 3,000
years, HFB/+4K: 5,400 years — ADR-0019). The hazard at a node is therefore
the empirical annual-maximum peak-stage distribution, obtained through the
verbatim M3 chain (band-workbook resolution, ADR-0019 §7 discharge proxy,
the node's own Eq. 4.19 rating). No parametric flood-frequency model is
fitted: the thesis scope stays inside the simulated d4PDF envelope.

Event characteristics for the RQ4 attribution (peak, above-datum exposure,
rise time, plateau, peak count) are computed per member with the existing
M3 ``flood_timescales`` plus the above-toe exposure measures here.

The workbook streaming read is the expensive step (~minutes per node);
:func:`load_node_hazard` therefore supports caching the per-event table to
a processed CSV whose provenance records the workbook and rating file.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from bep_reliability_engine.hydrographs import (
    flood_timescales,
    load_hydrograph_ensemble,
    load_rating_coefficients,
    rating_curve_path,
    resolve_band_workbook,
)

__all__ = ["EventSummary", "NodeHazard", "load_node_hazard", "load_reach_hazard"]


@dataclass(frozen=True)
class EventSummary:
    """Scalar characteristics of one annual-maximum ensemble event.

    Attributes
    ----------
    event_id : str
        The verbatim d4PDF member header (``HPB_mXXX_YYYY`` / HFB form).
    peak_stage_m_msl : float
        Peak stage at the node [m MSL] via the node's own rating.
    hours_above_datum : float
        Time the stage spends above the reference datum (the section toe
        when supplied) [h]; 0 when the event never reaches it.
    t_rise_h, plateau_h : float
        M3 ``flood_timescales`` rising-limb and plateau measures [h].
    n_peaks_above_datum : int
        Count of separate above-datum excursions (compound-event marker).
    """

    event_id: str
    peak_stage_m_msl: float
    hours_above_datum: float
    t_rise_h: float
    plateau_h: float
    n_peaks_above_datum: int


@dataclass(frozen=True)
class NodeHazard:
    """The empirical annual-maximum stage-frequency at one node/scenario.

    Attributes
    ----------
    river : str
        ``'Tokachi'`` or ``'Satsunai'``.
    kp : float
        Node KP [km].
    scenario : str
        ``'historical'`` (HPB) or ``'+4K'`` (HFB).
    n_years : int
        Ensemble-years represented (one event per year).
    events : tuple of EventSummary
        Per-event characteristics, workbook column order.
    datum_m_msl : float or None
        The above-datum reference used for exposure measures (section toe),
        or None when not supplied.
    provenance : dict
        Workbook and rating-file names.
    """

    river: str
    kp: float
    scenario: str
    n_years: int
    events: tuple[EventSummary, ...]
    datum_m_msl: float | None
    provenance: dict[str, str]

    def peak_stages(self) -> NDArray[np.float64]:
        """All annual-maximum peak stages [m MSL], workbook order."""
        return np.asarray([e.peak_stage_m_msl for e in self.events], dtype=np.float64)

    def annual_exceedance(
        self, stage_m: NDArray[np.float64] | float
    ) -> NDArray[np.float64]:
        """Empirical P(annual max stage > h) per queried level."""
        stage = np.atleast_1d(np.asarray(stage_m, dtype=np.float64))
        peaks = self.peak_stages()
        return np.asarray([(peaks > level).mean() for level in stage], dtype=np.float64)

    def return_period_stages(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Weibull plotting positions: (return period [years], stage [m MSL]).

        Sorted descending in stage; T_i = (n + 1) / i for the i-th largest.
        """
        peaks = np.sort(self.peak_stages())[::-1]
        ranks = np.arange(1, peaks.size + 1, dtype=np.float64)
        return (self.n_years + 1.0) / ranks, peaks


def _datum_matches(cached: float | None, requested: float | None) -> bool:
    """True when the cache was built with the requested exposure datum."""
    if cached is None or requested is None:
        return cached is None and requested is None
    return abs(cached - requested) <= 1e-9


def _above_datum_measures(
    h: NDArray[np.float64], dt_hours: float, datum_m: float | None
) -> tuple[float, int]:
    """(hours above datum, count of separate above-datum excursions)."""
    if datum_m is None:
        return float("nan"), 0
    above = h > datum_m
    hours = float(above.sum() * dt_hours)
    # Rising edges of the boolean series = separate excursions.
    excursions = int(np.sum(np.diff(above.astype(np.int8)) == 1))
    if above.size and above[0]:
        excursions += 1
    return hours, excursions


def load_node_hazard(
    data_root: str | Path,
    *,
    river: str,
    kp: float,
    scenario: str,
    datum_m_msl: float | None = None,
    cache_csv: str | Path | None = None,
) -> NodeHazard:
    """Load (or reload from cache) the node's ensemble hazard table.

    Parameters
    ----------
    data_root : str or pathlib.Path
        Raw data root (band workbooks under ``hydrographs/``, rating files
        under ``rating_curves/`` — the M3 conventions).
    river : str
        ``'Tokachi'`` or ``'Satsunai'``.
    kp : float
        The study node's KP (rating at this KP; discharge band per the
        ADR-0019 §7 proxy where applicable).
    scenario : str
        ``'historical'`` (HPB workbook) or ``'+4K'`` (HFB workbook).
    datum_m_msl : float, optional
        Above-datum reference for the exposure measures (the section toe).
    cache_csv : str or pathlib.Path, optional
        Per-event table cache. When the file exists it is read instead of
        streaming the workbook; when absent it is written after the read.

    Returns
    -------
    NodeHazard
        The per-event table plus the empirical exceedance accessors.
    """
    if cache_csv is not None and Path(cache_csv).exists():
        cached = _read_cache(Path(cache_csv), river=river, kp=kp, scenario=scenario)
        if _datum_matches(cached.datum_m_msl, datum_m_msl):
            return cached
        # Stale cache parameters (different datum): recompute and rewrite.
        # A wrong node raises inside _read_cache; a wrong datum is a
        # legitimate re-parameterization, not a data error.

    workbook = resolve_band_workbook(data_root, river=river, kp=kp, scenario=scenario)
    coefficients = load_rating_coefficients(rating_curve_path(data_root, river))
    records = load_hydrograph_ensemble(
        workbook, kp=kp, rating_coefficients=coefficients
    )

    events: list[EventSummary] = []
    for event_id, record in records.items():
        h = np.asarray(record.h, dtype=np.float64)
        dt_hours = float(record.native_dt) / 3600.0
        timescales = flood_timescales(h, float(record.native_dt))
        hours_above, n_excursions = _above_datum_measures(h, dt_hours, datum_m_msl)
        events.append(
            EventSummary(
                event_id=event_id,
                peak_stage_m_msl=float(record.peak),
                hours_above_datum=hours_above,
                t_rise_h=float(timescales["rising_limb_s"]) / 3600.0,
                plateau_h=float(timescales["plateau_s"]) / 3600.0,
                n_peaks_above_datum=n_excursions,
            )
        )

    hazard = NodeHazard(
        river=river,
        kp=float(kp),
        scenario=scenario,
        n_years=len(events),
        events=tuple(events),
        datum_m_msl=datum_m_msl,
        provenance={
            "band_workbook": workbook.name,
            "rating_csv": rating_curve_path(data_root, river).name,
        },
    )
    if cache_csv is not None:
        _write_cache(Path(cache_csv), hazard)
    return hazard


def _events_from_records(
    records, datum_m_msl: float | None
) -> tuple[EventSummary, ...]:
    """Per-event characteristic table from M3 records (shared summarizer)."""
    events: list[EventSummary] = []
    for event_id, record in records.items():
        h = np.asarray(record.h, dtype=np.float64)
        dt_hours = float(record.native_dt) / 3600.0
        timescales = flood_timescales(h, float(record.native_dt))
        hours_above, n_excursions = _above_datum_measures(h, dt_hours, datum_m_msl)
        events.append(
            EventSummary(
                event_id=event_id,
                peak_stage_m_msl=float(record.peak),
                hours_above_datum=hours_above,
                t_rise_h=float(timescales["rising_limb_s"]) / 3600.0,
                plateau_h=float(timescales["plateau_s"]) / 3600.0,
                n_peaks_above_datum=n_excursions,
            )
        )
    return tuple(events)


def load_reach_hazard(
    data_root: str | Path,
    *,
    nodes: list[tuple[str, float, float | None]],
    scenario: str,
    cache_dir: str | Path | None = None,
) -> dict[tuple[str, float], NodeHazard]:
    """Hazard for many nodes, streaming each band workbook exactly once.

    The single-node :func:`load_node_hazard` re-reads its workbook per call
    (minutes each); a full-reach campaign over ~114 nodes would re-stream
    the same three workbooks dozens of times. This loader groups the nodes
    by resolved workbook, reads each workbook once, and emits one
    :class:`NodeHazard` per node — identical to what ``load_node_hazard``
    would have produced (same M3 chain, same cache format).

    Parameters
    ----------
    data_root : str or pathlib.Path
        Raw data root (M3 conventions).
    nodes : list of (river, kp, datum_m_msl)
        Study nodes with their per-node exposure datum (or None).
    scenario : str
        ``'historical'`` or ``'+4K'``.
    cache_dir : str or pathlib.Path, optional
        Directory of per-node cache CSVs (``load_node_hazard`` format).
        Cached nodes are served from disk; only workbooks needed by
        uncached nodes are streamed.

    Returns
    -------
    dict of (river, kp) -> NodeHazard
    """
    from bep_reliability_engine.hydrographs import (
        build_hydrograph_record,
        parse_member_header,
        read_discharge_ensemble,
        resolve_discharge_source_kp,
    )

    out: dict[tuple[str, float], NodeHazard] = {}
    pending: dict[Path, list[tuple[str, float, float | None]]] = {}
    scenario_token = scenario.replace("+", "plus")

    def _cache_path(river: str, kp: float) -> Path | None:
        if cache_dir is None:
            return None
        return Path(cache_dir) / (
            f"hazard_{river.lower()}_kp{kp:.1f}_{scenario_token}.csv"
        )

    for river, kp, datum in nodes:
        cache = _cache_path(river, kp)
        if cache is not None and cache.exists():
            cached = _read_cache(cache, river=river, kp=kp, scenario=scenario)
            if _datum_matches(cached.datum_m_msl, datum):
                out[(river, round(kp, 3))] = cached
                continue
        workbook = resolve_band_workbook(
            data_root, river=river, kp=kp, scenario=scenario
        )
        pending.setdefault(workbook, []).append((river, kp, datum))

    for workbook, node_list in pending.items():
        time_hours, members = read_discharge_ensemble(workbook)  # ONE read
        member_info = {h: parse_member_header(h) for h in members}
        rating_cache: dict[str, dict[float, tuple[float, float]]] = {}
        for river, kp, datum in node_list:
            if river not in rating_cache:
                rating_cache[river] = load_rating_coefficients(
                    rating_curve_path(data_root, river)
                )
            a_kp, b_kp = rating_cache[river][kp]
            _, proxied = resolve_discharge_source_kp(kp)
            records = {}
            for header, discharge in members.items():
                provenance = {**member_info[header], "kp": kp}
                if proxied is not None:
                    provenance["discharge_proxied_from"] = proxied
                records[header] = build_hydrograph_record(
                    time_hours,
                    discharge,
                    a_kp=a_kp,
                    b_kp=b_kp,
                    scenario=str(member_info[header]["scenario"]),
                    event_id=header,
                    provenance=provenance,
                )
            events = _events_from_records(records, datum)
            hazard = NodeHazard(
                river=river,
                kp=float(kp),
                scenario=scenario,
                n_years=len(events),
                events=events,
                datum_m_msl=datum,
                provenance={
                    "band_workbook": workbook.name,
                    "rating_csv": rating_curve_path(data_root, river).name,
                },
            )
            cache = _cache_path(river, kp)
            if cache is not None:
                _write_cache(cache, hazard)
            out[(river, round(kp, 3))] = hazard
    return out


_CACHE_FIELDS = (
    "event_id",
    "peak_stage_m_msl",
    "hours_above_datum",
    "t_rise_h",
    "plateau_h",
    "n_peaks_above_datum",
)


def _write_cache(path: Path, hazard: NodeHazard) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                f"# river={hazard.river} kp={hazard.kp:g} "
                f"scenario={hazard.scenario} datum={hazard.datum_m_msl!r} "
                f"workbook={hazard.provenance['band_workbook']} "
                f"rating={hazard.provenance['rating_csv']}"
            ]
        )
        writer.writerow(_CACHE_FIELDS)
        for event in hazard.events:
            writer.writerow([getattr(event, field) for field in _CACHE_FIELDS])


def _read_cache(path: Path, *, river: str, kp: float, scenario: str) -> NodeHazard:
    with open(path, encoding="utf-8") as handle:
        header = handle.readline().strip().lstrip("# ")
        tokens = dict(token.split("=", 1) for token in header.split() if "=" in token)
        if (
            tokens.get("river") != river
            or abs(float(tokens.get("kp", "nan")) - kp) > 1e-6
            or tokens.get("scenario") != scenario
        ):
            raise ValueError(
                f"{path.name}: cache header {header!r} does not match the "
                f"requested node ({river} KP {kp:g} {scenario}); refusing "
                "to serve another node's hazard."
            )
        datum_token = tokens.get("datum", "None")
        datum = None if datum_token == "None" else float(datum_token)
        rows = list(csv.DictReader(handle))
    events = tuple(
        EventSummary(
            event_id=row["event_id"],
            peak_stage_m_msl=float(row["peak_stage_m_msl"]),
            hours_above_datum=float(row["hours_above_datum"]),
            t_rise_h=float(row["t_rise_h"]),
            plateau_h=float(row["plateau_h"]),
            n_peaks_above_datum=int(row["n_peaks_above_datum"]),
        )
        for row in rows
    )
    return NodeHazard(
        river=river,
        kp=float(kp),
        scenario=scenario,
        n_years=len(events),
        events=events,
        datum_m_msl=datum,
        provenance={
            "band_workbook": tokens.get("workbook", "cache"),
            "rating_csv": tokens.get("rating", "cache"),
        },
    )
