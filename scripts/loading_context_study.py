"""Loading-context study: the 2016 floods on three rivers and the d4PDF hydrographs.

Pol feedback round 2, annotations A25, A29 and A32
(``docs/decisions/loading-context-study.md``; pre-registration ``20e2330``).
Descriptive only: no sweep, replay, posterior, prior or Phase 3 table is
touched, and nothing here enters a fragility.

Parts
-----
``stats``
    Reads the d4PDF band workbook feeding the four Tokachi study sections
    (3,000 historical and 5,400 +4 K annual-maximum discharge series), the
    Phase 3 hazard files of those sections and the observed August 2016 gauge
    records, and evaluates the pre-registered predictions P1 to P6. Writes the
    evidence JSON beside the study note and a figure cache under the gitignored
    ``results/loading_context/``.
``figures``
    Renders ``loading_2016_three_rivers.png`` (A25) and
    ``loading_d4pdf_hydrographs.png`` (A29) into ``docs/figures/`` with a
    study-local mirror.

Definitions follow ADR-0023 exactly (normalized stage shape at KP 57.4, peaks
by ``scipy.signal.find_peaks(height=0.3, prominence=0.2)``, durations at or
above a shape fraction). The normalized stage shape of a member is the same at
every node of one band, because ``h = sqrt(Q/a) - b`` makes
``(h - h_min) / (h_max - h_min)`` independent of ``a`` and ``b``.

Usage::

    python scripts/loading_context_study.py stats
    python scripts/loading_context_study.py figures
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from numpy.typing import NDArray
from scipy.signal import find_peaks

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

DATA_RAW = REPO / "data" / "raw"
EVENT_DIR = REPO / "data" / "processed" / "2016_event"
HAZARD_DIR = REPO / "results" / "system_integration"
OUT_DIR = REPO / "results" / "loading_context"
CACHE = OUT_DIR / "shapes.npz"
EVIDENCE = REPO / "docs" / "decisions" / "loading-context-study.json"

KPS: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0)
SHAPE_KP = 57.4  # ADR-0023's node
DURATION_KP = 58.8  # panel (b) and P6
BAND = "Tokachi Riv. KP056.20-KP061.80"
CANONICAL = "HPB_m064_1987"
ALTERNATE = "HPB_m067_1978"
SHAPE_FRACTIONS: tuple[float, ...] = (0.25, 0.5, 0.6, 0.75, 0.9)
PEAK_HEIGHT = 0.3
PEAK_PROMINENCE = 0.2
WINDOW_H = 192
#: ADR-0023 table, the reproduction gate of P2.
ADR0023 = {
    "historical": {"t50": 40.0, "t90": 10.0, "compound_pct": 9.6},
    "+4K": {"t50": 35.0, "t90": 8.0, "compound_pct": 10.1},
}
#: Rating-anchored 2016 peaks (initiation-evidence-2016-study.md section 8).
RATING_2016 = {57.4: 39.02, 58.8: 40.78, 60.0: 41.65, 62.0: 46.64}
#: Thesis Table 7.5 rows checked by P4 (percent of years, hist -> +4 K).
TABLE_7_5 = {
    57.4: {"toe": (4.3, 14.1), "multi": (0.17, 0.54)},
    58.8: {"toe": (24.7, 40.8), "multi": (1.17, 2.43)},
    60.0: {"toe": (20.5, 36.6), "multi": (0.90, 1.87)},
    62.0: {"toe": (10.4, 24.3), "multi": (0.33, 1.33)},
}
#: Gauges outside the study sections: (river, column, KP, design level source).
SATSUNAI_GAUGES = (("satsunai", 4.0), ("nantaibashi", 15.0))
#: Futochanae (Tokoro, KP 18.9) design high water level, committee report
#: (Tokoro River Levee Investigation Committee 2017, pp. 5-15 and 5-20, as read
#: in why-no-piping-2016-study.md section 2).
FUTOCHANAE_DESIGN_M = 12.38
FUTOCHANAE_KP = 18.9
SCENARIOS = {"historical": "HPB", "+4K": "HFB"}


# --------------------------------------------------------------------------- #
# Pure helpers (unit-tested)                                                   #
# --------------------------------------------------------------------------- #
def stage_shape(discharge: NDArray[np.float64]) -> NDArray[np.float64]:
    """Normalized stage shape of a discharge series under any band rating."""
    root = np.sqrt(np.asarray(discharge, dtype=np.float64))
    lo, hi = float(root.min()), float(root.max())
    if not hi > lo:
        raise ValueError("constant discharge series has no shape")
    return (root - lo) / (hi - lo)


def shape_statistics(shape: NDArray[np.float64]) -> dict[str, float]:
    """ADR-0023 statistics of one normalized shape (hourly samples)."""
    s = np.asarray(shape, dtype=np.float64)
    peaks, _ = find_peaks(s, height=PEAK_HEIGHT, prominence=PEAK_PROMINENCE)
    # find_peaks cannot report a maximum on the first or last sample; a member
    # whose global maximum sits on an edge still has that one peak.
    n_peaks = int(peaks.size)
    k_max = int(np.argmax(s))
    if k_max in (0, s.size - 1):
        n_peaks += 1
    return {
        "t50_h": float(np.count_nonzero(s >= 0.5)),
        "t90_h": float(np.count_nonzero(s >= 0.9)),
        "n_peaks": float(n_peaks),
        "peak_hour_index": float(k_max),
    }


def excursions_above(values: NDArray[np.float64], level: float) -> list[int]:
    """Lengths of the runs of consecutive samples strictly above ``level``."""
    above = np.asarray(values, dtype=np.float64) > level
    runs: list[int] = []
    count = 0
    for flag in above:
        if flag:
            count += 1
        elif count:
            runs.append(count)
            count = 0
    if count:
        runs.append(count)
    return runs


def read_stage_csv(path: Path, column: str) -> tuple[list[dt.datetime], NDArray]:
    """Read one station column of a ``stage_hourly_*`` extract (NaN for blanks)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    idx = header.index(column)
    times: list[dt.datetime] = []
    vals: list[float] = []
    for line in lines[1:]:
        parts = line.split(",")
        times.append(dt.datetime.strptime(parts[0], "%Y-%m-%dT%H:%M"))
        raw = parts[idx].strip() if idx < len(parts) else ""
        vals.append(float(raw) if raw else np.nan)
    return times, np.asarray(vals, dtype=np.float64)


def binned_medians(
    x: NDArray, y: NDArray, edges: NDArray, min_count: int
) -> dict[str, list[float]]:
    """Median and quartiles of ``y`` in bins of ``x``; bins under the count omitted."""
    out: dict[str, list[float]] = {"lo": [], "hi": [], "n": [], "q25": [], "med": []}
    out["q75"] = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        sel = (x >= lo) & (x < hi)
        n = int(sel.sum())
        if n < min_count:
            continue
        q25, med, q75 = np.percentile(y[sel], [25, 50, 75])
        for key, val in zip(
            ("lo", "hi", "n", "q25", "med", "q75"),
            (lo, hi, n, q25, med, q75),
            strict=True,
        ):
            out[key].append(float(val))
    return out


# --------------------------------------------------------------------------- #
# Inputs                                                                       #
# --------------------------------------------------------------------------- #
def _section_geometry(kp: float) -> dict[str, float]:
    tag = f"{kp:.1f}".replace(".", "_")
    cfg = yaml.safe_load(
        (REPO / "configs" / f"kp{tag}_historical_matrix.yaml").read_text("utf-8")
    )
    geo = cfg["geometry"]
    return {"z_toe_m": float(geo["z_toe"]), "design_m": float(geo["HWL"])}


def _hazard(kp: float, scenario: str) -> dict[str, NDArray]:
    tag = "historical" if scenario == "historical" else "plus4K"
    path = HAZARD_DIR / f"hazard_tokachi_kp{kp:.1f}_{tag}.csv"
    lines = [ln for ln in path.read_text("utf-8").splitlines() if ln[:1] != '"']
    header = lines[0].split(",")
    cols: dict[str, list] = {h: [] for h in header}
    for line in lines[1:]:
        for h, v in zip(header, line.split(","), strict=True):
            cols[h].append(v)
    out: dict[str, NDArray] = {"event_id": np.asarray(cols["event_id"])}
    for h in header[1:]:
        out[h] = np.asarray(cols[h], dtype=np.float64)
    return out


def _band_members(scenario: str) -> dict[str, NDArray[np.float64]]:
    from bep_reliability_engine.hydrographs import read_discharge_ensemble

    exp = SCENARIOS[scenario]
    path = DATA_RAW / "hydrographs" / f"Hydro Data, {exp}, {BAND}.xlsx"
    time_h, members = read_discharge_ensemble(path)
    if time_h.size != WINDOW_H:
        raise SystemExit(f"{path.name}: {time_h.size} hours, not {WINDOW_H}")
    return members


def _tokachi_records() -> dict[float, dict[str, Any]]:
    from bayesian_reliability_updating.events import (
        default_2016_source,
        observed_event_record,
    )

    src = default_2016_source(EVENT_DIR)
    out: dict[float, dict[str, Any]] = {}
    for kp in KPS:
        geo = _section_geometry(kp)
        rec = observed_event_record(src, section_kp=kp, data_root=DATA_RAW)
        rat = observed_event_record(
            src, section_kp=kp, data_root=DATA_RAW, anchor="rating"
        )
        start = dt.datetime.strptime(
            rec.provenance["window_start_jst"][:16], "%Y-%m-%dT%H:%M"
        )
        t = [start + dt.timedelta(seconds=float(s)) for s in np.asarray(rec.t)]
        out[kp] = {
            "t": t,
            "h": np.asarray(rec.h, dtype=np.float64),
            "peak_m": float(rec.peak),
            "rating_peak_m": float(rat.peak),
            **geo,
        }
    return out


# --------------------------------------------------------------------------- #
# Part: stats                                                                  #
# --------------------------------------------------------------------------- #
def _ensemble_part() -> tuple[dict[str, Any], dict[str, NDArray]]:
    stats: dict[str, Any] = {}
    cache: dict[str, NDArray] = {}
    for scenario in SCENARIOS:
        members = _band_members(scenario)
        ids = np.asarray(sorted(members))
        rows = [shape_statistics(stage_shape(members[i])) for i in ids]
        t50 = np.asarray([r["t50_h"] for r in rows])
        t90 = np.asarray([r["t90_h"] for r in rows])
        npk = np.asarray([r["n_peaks"] for r in rows])
        kpk = np.asarray([r["peak_hour_index"] for r in rows])
        # Peak-aligned shapes for the figure: hours -48 .. +120 about the peak.
        rel = np.arange(-48, 121)
        aligned = np.full((ids.size, rel.size), np.nan)
        for j, i in enumerate(ids):
            s = stage_shape(members[i])
            k = int(np.argmax(s))
            idx = rel + k
            ok = (idx >= 0) & (idx < s.size)
            aligned[j, ok] = s[idx[ok]]
        cache[f"{scenario}_ids"] = ids
        cache[f"{scenario}_aligned"] = aligned
        cache[f"{scenario}_npeaks"] = npk
        cache["rel_hours"] = rel
        for special in (CANONICAL, ALTERNATE):
            if special in members:
                s = stage_shape(members[special])
                cache[f"shape_{special}"] = s
        if scenario == "historical":
            # Where the canonical and alternate members sit among all members
            # in hours at or above each fraction of the rise.
            durations = {
                f: np.asarray(
                    [np.count_nonzero(stage_shape(members[i]) >= f) for i in ids]
                )
                for f in SHAPE_FRACTIONS
            }
            ranks: dict[str, Any] = {}
            for special in (CANONICAL, ALTERNATE):
                s = stage_shape(members[special])
                ranks[special] = {
                    f"{f:.2f}": {
                        "hours": int(np.count_nonzero(s >= f)),
                        "median_hours": float(np.median(durations[f])),
                        "share_strictly_shorter": float(
                            np.mean(durations[f] < np.count_nonzero(s >= f))
                        ),
                        "share_strictly_longer": float(
                            np.mean(durations[f] > np.count_nonzero(s >= f))
                        ),
                    }
                    for f in SHAPE_FRACTIONS
                }
            stats["member_rank_by_fraction_of_rise"] = ranks
        stats[scenario] = {
            "members": int(ids.size),
            "t50_median_h": float(np.median(t50)),
            "t50_iqr_h": [float(np.percentile(t50, 25)), float(np.percentile(t50, 75))],
            "t90_median_h": float(np.median(t90)),
            "compound_pct": float(100.0 * np.mean(npk >= 2)),
            "three_or_more_peaks_pct": float(100.0 * np.mean(npk >= 3)),
            "peak_hour_median": float(np.median(kpk) + 1),
            "peak_hour_p90": float(np.percentile(kpk, 90) + 1),
            "peak_hour_max": float(kpk.max() + 1),
            "peak_within_96h_pct": float(100.0 * np.mean(kpk < 96)),
            "hours_before_peak_min": float(kpk.min()),
            "hours_before_peak_median": float(np.median(kpk)),
            "hours_before_peak_max": float(kpk.max()),
        }
    return stats, cache


def _obihiro_2016() -> dict[str, Any]:
    times, h = read_stage_csv(EVENT_DIR / "stage_hourly_Tokachi_201608.csv", "obihiro")
    ok = np.isfinite(h)
    s = (h - np.nanmin(h)) / (np.nanmax(h) - np.nanmin(h))
    s_ok = np.where(ok, s, 0.0)
    peaks, props = find_peaks(s_ok, height=PEAK_HEIGHT, prominence=PEAK_PROMINENCE)
    k_max = int(np.nanargmax(h))
    # Every 192-h window containing the maximum and starting >= 24 h before it.
    counts = []
    for start in range(max(0, k_max - WINDOW_H + 1), k_max - 23):
        w = h[start : start + WINDOW_H]
        if w.size < WINDOW_H or not np.all(np.isfinite(w)):
            continue
        counts.append(shape_statistics((w - w.min()) / (w.max() - w.min()))["n_peaks"])
    named = []
    for p in peaks:
        named.append(
            {
                "time_jst": times[int(p)].strftime("%Y-%m-%dT%H:%M"),
                "stage_m": float(h[int(p)]),
                "shape": float(s[int(p)]),
            }
        )
    return {
        "base_m": float(np.nanmin(h)),
        "peak_m": float(np.nanmax(h)),
        "peak_time_jst": times[k_max].strftime("%Y-%m-%dT%H:%M"),
        "significant_peaks_august": named,
        "window_peak_counts": sorted({int(c) for c in counts}),
        "window_count": len(counts),
        "hours_from_second_last_to_last_peak": (
            float(peaks[-1] - peaks[-2]) if peaks.size >= 2 else None
        ),
    }


def _hazard_part(npk_by_id: dict[str, dict[str, float]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for kp in KPS:
        geo = _section_geometry(kp)
        row: dict[str, Any] = {}
        for scenario in SCENARIOS:
            hz = _hazard(kp, scenario)
            loaded = hz["hours_above_datum"] > 0
            multi = hz["n_peaks_above_datum"] >= 2
            big = hz["peak_stage_m_msl"] >= RATING_2016[kp]
            sig = np.asarray([npk_by_id[scenario][e] for e in hz["event_id"]])
            row[scenario] = {
                "years": int(loaded.size),
                "loaded_pct": float(100 * loaded.mean()),
                "multi_excursion_pct": float(100 * multi.mean()),
                "multi_given_loaded_pct": float(100 * multi[loaded].mean()),
                "years_at_least_2016": int(big.sum()),
                "multi_excursion_given_2016_pct": (
                    float(100 * multi[big].mean()) if big.any() else None
                ),
                "compound_given_2016_pct": (
                    float(100 * (sig[big] >= 2).mean()) if big.any() else None
                ),
                "compound_all_pct": float(100 * (sig >= 2).mean()),
                "median_hours_above_toe_given_2016": (
                    float(np.median(hz["hours_above_datum"][big]))
                    if big.any()
                    else None
                ),
            }
        h, w = row["historical"], row["+4K"]
        row["multi_unconditional_ratio"] = w["multi_excursion_pct"] / max(
            h["multi_excursion_pct"], 1e-12
        )
        row["multi_given_loaded_ratio"] = w["multi_given_loaded_pct"] / max(
            h["multi_given_loaded_pct"], 1e-12
        )
        row["z_toe_m"] = geo["z_toe_m"]
        row["design_m"] = geo["design_m"]
        out[f"KP {kp:.1f}"] = row
    return out


def _fixed_peak_duration() -> dict[str, Any]:
    geo = _section_geometry(DURATION_KP)
    edges = np.arange(geo["z_toe_m"], geo["z_toe_m"] + 6.01, 0.25)
    res: dict[str, Any] = {"edges_m": [float(e) for e in edges]}
    for scenario in SCENARIOS:
        hz = _hazard(DURATION_KP, scenario)
        sel = hz["hours_above_datum"] > 0
        res[scenario] = binned_medians(
            hz["peak_stage_m_msl"][sel], hz["hours_above_datum"][sel], edges, 1
        )
    h, w = res["historical"], res["+4K"]
    common = []
    for i, lo in enumerate(h["lo"]):
        if lo in w["lo"]:
            j = w["lo"].index(lo)
            if h["n"][i] >= 30 and w["n"][j] >= 30:
                common.append(
                    {
                        "lo_m": lo,
                        "n_hist": h["n"][i],
                        "n_warm": w["n"][j],
                        "median_hist_h": h["med"][i],
                        "median_warm_h": w["med"][j],
                        "ratio": w["med"][j] / h["med"][i],
                    }
                )
    res["bins_with_30_each"] = common
    return res


N_BOOT = 2000


def adjusted_ratio(
    hist: dict[str, NDArray], warm: dict[str, NDArray], edges: NDArray, metric: str
) -> dict[str, Any]:
    """Warming total of a per-year metric over its total at historical bin means.

    ``metric`` is ``'multi'`` (two or more separate excursions above the toe)
    or ``'hours'`` (hours above the toe, loaded years only). A ratio near one
    means the warming change in the metric follows from the peak-stage
    distribution; bins holding fewer than 20 historical years are left out.
    """

    def value(h: dict[str, NDArray]) -> NDArray:
        if metric == "multi":
            return (h["n_peaks_above_datum"] >= 2).astype(np.float64)
        return h["hours_above_datum"]

    def mask(h: dict[str, NDArray]) -> NDArray:
        if metric == "multi":
            return np.ones(h["peak_stage_m_msl"].size, dtype=bool)
        return h["hours_above_datum"] > 0

    vh, vw = value(hist), value(warm)
    mh, mw = mask(hist), mask(warm)
    expected = observed = 0.0
    kept = dropped = 0
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        sh = mh & (hist["peak_stage_m_msl"] >= lo) & (hist["peak_stage_m_msl"] < hi)
        sw = mw & (warm["peak_stage_m_msl"] >= lo) & (warm["peak_stage_m_msl"] < hi)
        if not sw.any():
            continue
        if sh.sum() < 20:
            dropped += int(sw.sum())
            continue
        expected += float(vh[sh].mean()) * int(sw.sum())
        observed += float(vw[sw].sum())
        kept += int(sw.sum())
    return {
        "warming_years_compared": kept,
        "warming_years_left_out": dropped,
        "observed": observed,
        "expected_at_historical_means": expected,
        "ratio": observed / expected if expected else None,
    }


def _blocks(event_ids: NDArray) -> dict[str, dict[str, NDArray]]:
    """Row indices per ensemble member, grouped by stratum (SST pattern or one)."""
    strata: dict[str, dict[str, list[int]]] = {}
    for i, eid in enumerate(event_ids):
        member = eid.rsplit("_", 1)[0]
        parts = member.split("_")
        stratum = parts[1] if parts[0] == "HFB" else "historical"
        strata.setdefault(stratum, {}).setdefault(member, []).append(i)
    return {
        s: {m: np.asarray(ix) for m, ix in members.items()}
        for s, members in strata.items()
    }


def _resample(blocks: dict[str, dict[str, NDArray]], rng) -> NDArray:
    picks = []
    for members in blocks.values():
        names = sorted(members)
        for j in rng.integers(0, len(names), len(names)):
            picks.append(members[names[j]])
    return np.concatenate(picks)


def _take(h: dict[str, NDArray], idx: NDArray) -> dict[str, NDArray]:
    return {k: v[idx] for k, v in h.items()}


def _post_hoc(toka: dict[float, dict[str, Any]]) -> dict[str, Any]:
    """Checks added after Part 2 was first computed (labelled as such).

    (1) P4 conditions on reaching the toe, not on the peak. The amplitude-
    adjusted ratio gives each warming year the historical multi-excursion rate
    of its own 0.25 m peak bin; observed over expected near one means repeated
    excursions follow from the peaks. Warming years in bins with fewer than 20
    historical years are left out and counted. (2) Where the 2016 record and
    the canonical flood sit among historical floods of the same height at
    KP 58.8 (peaks within 0.25 m of 2016's).
    """
    out: dict[str, Any] = {
        "method": (
            "observed warming total over the total expected if every warming "
            "year had the historical mean of its own 0.25 m peak-stage bin; bins "
            "with fewer than 20 historical years left out; 95 % intervals from "
            f"{N_BOOT} member-block resamples (historical members; warming "
            "members within each of the six SST patterns)"
        ),
        "amplitude_adjusted_multi_excursion": {},
        "amplitude_adjusted_hours_above_toe": {},
    }
    rng = np.random.default_rng(20261008)
    for kp in KPS:
        geo = _section_geometry(kp)
        hh, hw = _hazard(kp, "historical"), _hazard(kp, "+4K")
        edges = np.arange(geo["z_toe_m"], geo["z_toe_m"] + 8.01, 0.25)
        for key, metric in (
            ("amplitude_adjusted_multi_excursion", "multi"),
            ("amplitude_adjusted_hours_above_toe", "hours"),
        ):
            point = adjusted_ratio(hh, hw, edges, metric)
            boots = []
            hb, wb = _blocks(hh["event_id"]), _blocks(hw["event_id"])
            for _ in range(N_BOOT):
                ih = _resample(hb, rng)
                iw = _resample(wb, rng)
                r = adjusted_ratio(_take(hh, ih), _take(hw, iw), edges, metric)
                if r["ratio"] is not None:
                    boots.append(r["ratio"])
            point["ci95"] = [float(q) for q in np.percentile(boots, [2.5, 97.5])]
            out[key][f"KP {kp:.1f}"] = point
    geo = _section_geometry(DURATION_KP)
    hz = _hazard(DURATION_KP, "historical")
    obs = toka[DURATION_KP]
    peak = obs["peak_m"]
    sel = np.abs(hz["peak_stage_m_msl"] - peak) <= 0.25
    hrs = hz["hours_above_datum"][sel]
    rec_hours = float(sum(excursions_above(obs["h"], geo["z_toe_m"])))
    from bep_reliability_engine.hydrographs import (
        conditioning_record_for_level,
        load_canonical_shape,
    )

    canon = load_canonical_shape(
        DATA_RAW, river="Tokachi", kp=DURATION_KP, event_id=CANONICAL
    )
    rc = conditioning_record_for_level(canon, peak, scenario="historical")
    canon_hours = float((np.asarray(rc.h) > geo["z_toe_m"]).sum())
    out["same_height_kp58_8"] = {
        "peak_m": peak,
        "historical_years": int(sel.sum()),
        "quartiles_h": [float(q) for q in np.percentile(hrs, [25, 50, 75])],
        "record_2016_hours": rec_hours,
        "record_2016_percentile": float(100.0 * np.mean(hrs < rec_hours)),
        "canonical_hours": canon_hours,
        "canonical_percentile": float(100.0 * np.mean(hrs < canon_hours)),
        "max_h": float(hrs.max()),
    }
    # (3) The canonical flood's time above the toe against simulated floods of
    # the same height, at every section, at the design level and at stages
    # 0.5 m apart from 1 m above the toe (historical years within +-0.25 m;
    # levels with fewer than 20 such years are skipped).
    canon_rank: dict[str, Any] = {}
    for kp in KPS:
        geo_k = _section_geometry(kp)
        hz_k = _hazard(kp, "historical")
        shape_k = load_canonical_shape(
            DATA_RAW, river="Tokachi", kp=kp, event_id=CANONICAL
        )
        levels = sorted(
            {round(geo_k["design_m"], 2)}
            | {
                round(float(x), 2)
                for x in np.arange(geo_k["z_toe_m"] + 1.0, geo_k["z_toe_m"] + 4.01, 0.5)
            }
        )
        rows = []
        for lv in levels:
            near = np.abs(hz_k["peak_stage_m_msl"] - lv) <= 0.25
            if near.sum() < 20:
                continue
            rc_k = conditioning_record_for_level(shape_k, lv, scenario="historical")
            ch = float((np.asarray(rc_k.h) > geo_k["z_toe_m"]).sum())
            h_near = hz_k["hours_above_datum"][near]
            rows.append(
                {
                    "stage_m": lv,
                    "years": int(near.sum()),
                    "median_h": float(np.median(h_near)),
                    "canonical_h": ch,
                    "share_shorter_than_canonical": float(np.mean(h_near < ch)),
                }
            )
        canon_rank[f"KP {kp:.1f}"] = rows
    out["canonical_time_above_toe_rank"] = canon_rank
    return out


def _three_rivers(toka: dict[float, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    t_tok, h_tok = read_stage_csv(
        EVENT_DIR / "stage_hourly_Tokoro_201608.csv", "futochanae"
    )
    runs = excursions_above(h_tok, FUTOCHANAE_DESIGN_M)
    out["Tokoro, Futochanae"] = {
        "kp": FUTOCHANAE_KP,
        "design_m": FUTOCHANAE_DESIGN_M,
        "peak_m": float(np.nanmax(h_tok)),
        "peak_time_jst": t_tok[int(np.nanargmax(h_tok))].strftime("%Y-%m-%dT%H:%M"),
        "peak_above_design_m": float(np.nanmax(h_tok) - FUTOCHANAE_DESIGN_M),
        "hours_above_design_runs": runs,
    }
    trace = {}
    for line in (
        (EVENT_DIR / "flood_trace_2016.csv").read_text("utf-8").splitlines()[1:]
    ):
        p = line.split(",")
        if p[0] == "Satsunai" and p[2]:
            trace[round(float(p[1]), 1)] = (
                float(p[2]),
                float(p[3]) if p[3] else None,
                float(p[5]) if p[5] else None,
            )
    for col, kp in SATSUNAI_GAUGES:
        t_s, h_s = read_stage_csv(EVENT_DIR / "stage_hourly_Satsunai_201608.csv", col)
        design, tl, tr = trace[kp]
        good = np.isfinite(h_s)
        last = int(np.where(good)[0][-1])
        out[f"Satsunai, KP {kp:.1f}"] = {
            "kp": kp,
            "design_m": design,
            "peak_m": float(np.nanmax(h_s)),
            "peak_time_jst": t_s[int(np.nanargmax(h_s))].strftime("%Y-%m-%dT%H:%M"),
            "peak_above_design_m": float(np.nanmax(h_s) - design),
            "hours_above_design_runs": excursions_above(h_s[good], design),
            "last_reading_jst": t_s[last].strftime("%Y-%m-%dT%H:%M"),
            "record_complete": bool(good.all()),
            "trace_left_m": tl,
            "trace_right_m": tr,
        }
    for kp, r in toka.items():
        out[f"Tokachi, KP {kp:.1f}"] = {
            "kp": kp,
            "design_m": r["design_m"],
            "z_toe_m": r["z_toe_m"],
            "peak_m": r["peak_m"],
            "rating_peak_m": r["rating_peak_m"],
            "peak_above_design_m": r["peak_m"] - r["design_m"],
            "hours_above_design_runs": excursions_above(r["h"], r["design_m"]),
            "hours_above_toe_runs": excursions_above(r["h"], r["z_toe_m"]),
        }
    return out


def stats_part() -> dict[str, Any]:
    ens, cache = _ensemble_part()
    npk_by_id = {
        sc: dict(zip(cache[f"{sc}_ids"], cache[f"{sc}_npeaks"], strict=True))
        for sc in SCENARIOS
    }
    toka = _tokachi_records()
    record: dict[str, Any] = {
        "study": "loading-context-study",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "pre_registration_commit": "20e2330",
        "ensemble_shape_kp": SHAPE_KP,
        "ensemble": ens,
        "obihiro_2016": _obihiro_2016(),
        "hazard": _hazard_part(npk_by_id),
        "fixed_peak_duration_kp58_8": _fixed_peak_duration(),
        "three_rivers_2016": _three_rivers(toka),
        "post_hoc": _post_hoc(toka),
    }
    record["predictions"] = _verdicts(record)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **cache)
    EVIDENCE.write_text(json.dumps(_round(record), indent=1) + "\n", encoding="utf-8")
    return record


def _verdicts(r: dict[str, Any]) -> dict[str, Any]:
    ens, hz = r["ensemble"], r["hazard"]
    v: dict[str, Any] = {}
    p1 = [ens[s]["peak_within_96h_pct"] for s in SCENARIOS]
    v["P1"] = {"held": all(x >= 90.0 for x in p1), "peak_within_96h_pct": p1}
    p2 = {
        s: {
            "t50": ens[s]["t50_median_h"] == ADR0023[s]["t50"],
            "t90": ens[s]["t90_median_h"] == ADR0023[s]["t90"],
            "compound": round(ens[s]["compound_pct"], 1) == ADR0023[s]["compound_pct"],
        }
        for s in SCENARIOS
    }
    v["P2"] = {"held": all(all(x.values()) for x in p2.values()), "detail": p2}
    ob = r["obihiro_2016"]
    v["P3"] = {
        "held": len(ob["significant_peaks_august"]) == 2
        and ob["window_peak_counts"] == [1],
        "august_peaks": len(ob["significant_peaks_august"]),
        "window_counts": ob["window_peak_counts"],
    }
    p4 = {}
    for key, row in hz.items():
        p4[key] = {
            "given_loaded_ratio": row["multi_given_loaded_ratio"],
            "unconditional_ratio": row["multi_unconditional_ratio"],
        }
    v["P4"] = {
        "held": all(x["given_loaded_ratio"] < 1.5 for x in p4.values()),
        "detail": p4,
    }
    p5 = {}
    held5 = True
    for key, row in hz.items():
        for s in SCENARIOS:
            c = row[s]
            if c["years_at_least_2016"] == 0:
                continue
            ok = (
                c["multi_excursion_given_2016_pct"] < 25.0
                and abs(c["compound_given_2016_pct"] - c["compound_all_pct"]) <= 10.0
            )
            held5 &= ok
            p5[f"{key} {s}"] = ok
    v["P5"] = {"held": held5, "detail": p5}
    bins = r["fixed_peak_duration_kp58_8"]["bins_with_30_each"]
    within = all(abs(b["ratio"] - 1.0) <= 0.20 for b in bins)
    longer = sum(b["ratio"] > 1.0 for b in bins)
    v["P6"] = {
        "held": within and longer <= len(bins) / 2,
        "bins": len(bins),
        "warming_longer_bins": longer,
        "ratios": [b["ratio"] for b in bins],
    }
    return v


def _round(obj: Any, sig: int = 6) -> Any:
    if isinstance(obj, float):
        return float(f"{obj:.{sig}g}") if np.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _round(v, sig) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, sig) for v in obj]
    if isinstance(obj, np.generic):
        return _round(obj.item(), sig)
    return obj


# --------------------------------------------------------------------------- #
# Part: figures                                                                #
# --------------------------------------------------------------------------- #
FIG_RIVERS = "loading_2016_three_rivers.png"
FIG_D4PDF = "loading_d4pdf_hydrographs.png"


def _days(times: list[dt.datetime]) -> NDArray[np.float64]:
    """August day numbers, continuing past 31 into September (1 Sep = 32)."""
    origin = dt.datetime(2016, 8, 1)
    return np.asarray([1.0 + (t - origin).total_seconds() / 86400.0 for t in times])


def _fig_rivers(record: dict[str, Any], fs) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    rivers = record["three_rivers_2016"]
    width = fs.TEXTWIDTH_IN
    height = width * 0.46
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(1, 3, figsize=(width, height), sharey=True, sharex=True)
    design_style = dict(color=fs.INK_2, lw=1.1 * scale, ls=(0, (5, 2)), zorder=3)
    xlim = (15.0, 32.0)
    ylim = (-3.2, 2.3)

    # (a) Tokoro
    ax = axes[0]
    t, h = read_stage_csv(EVENT_DIR / "stage_hourly_Tokoro_201608.csv", "futochanae")
    d = _days(t)
    rel = h - FUTOCHANAE_DESIGN_M
    ax.plot(d, rel, color=fs.INK, lw=1.5 * scale, zorder=5)
    ax.fill_between(d, 0, rel, where=rel > 0, color=fs.INK, alpha=0.18, lw=0)
    fs.panel_title(ax, "Tokoro, Futochanae gauge", scale=scale, letter="a")

    # (b) Satsunai
    ax = axes[1]
    sat_colors = {"satsunai": fs.VIOLET, "nantaibashi": fs.MAGENTA}
    for col, kp in SATSUNAI_GAUGES:
        t, h = read_stage_csv(EVENT_DIR / "stage_hourly_Satsunai_201608.csv", col)
        info = rivers[f"Satsunai, KP {kp:.1f}"]
        d = _days(t)
        rel = h - info["design_m"]
        ax.plot(d, rel, color=sat_colors[col], lw=1.5 * scale, zorder=5)
        ax.fill_between(
            d,
            0,
            rel,
            where=np.nan_to_num(rel, nan=-9) > 0,
            color=sat_colors[col],
            alpha=0.25,
            lw=0,
        )
        if not info["record_complete"]:
            k = int(np.where(np.isfinite(h))[0][-1])
            ax.plot(
                d[k], rel[k], marker="^", ms=6 * scale, color=sat_colors[col], zorder=6
            )
    fs.panel_title(ax, "Satsunai, two gauges", scale=scale, letter="b")

    # (c) Tokachi sections
    ax = axes[2]
    toka = _tokachi_records()
    for kp in KPS:
        r = toka[kp]
        d = _days(r["t"])
        color = fs.SECTION_COLORS[f"KP{kp:.1f}"]
        ax.plot(d, r["h"] - r["design_m"], color=color, lw=1.4 * scale, zorder=5)
        ax.axhline(
            r["z_toe_m"] - r["design_m"],
            color=color,
            lw=1.0 * scale,
            ls=(0, (1.2, 1.6)),
            zorder=2,
        )
    fs.panel_title(ax, "Tokachi, four study sections", scale=scale, letter="c")

    for ax in axes:
        ax.axhline(0.0, **design_style)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_xticks([16, 20, 24, 28, 32])
        ax.set_xticklabels(["16 Aug", "20 Aug", "24 Aug", "28 Aug", "1 Sep"])
    axes[0].set_ylabel("stage relative to design level [m]")
    handles = [
        Line2D([], [], **{k: v for k, v in design_style.items() if k != "zorder"}),
        Line2D([], [], color=fs.INK, lw=1.5 * scale),
        Line2D([], [], color=fs.VIOLET, lw=1.5 * scale),
        Line2D([], [], color=fs.MAGENTA, lw=1.5 * scale, marker="^", ms=6 * scale),
    ]
    labels = [
        "design level",
        "Tokoro, KP 18.9",
        "Satsunai, KP 4.0",
        "Satsunai, KP 15.0 (gauge lost)",
    ]
    for kp in KPS:
        handles.append(
            Line2D([], [], color=fs.SECTION_COLORS[f"KP{kp:.1f}"], lw=1.4 * scale)
        )
        labels.append(f"Tokachi, KP {kp:.1f}")
    handles.append(Line2D([], [], color=fs.MUTED, lw=1.0 * scale, ls=(0, (1.2, 1.6))))
    labels.append("Tokachi landside toe")
    fs.title(
        fig, "The August 2016 floods against each river's design level", scale=scale
    )
    fs.legend_below(fig, handles, labels, scale=scale, ncol=5)
    fs.layout(fig, scale=scale, legend_rows=2)
    return fs.save(fig, FIG_RIVERS, mirror=OUT_DIR / "figures")


def _fig_d4pdf(record: dict[str, Any], fs) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    from bep_reliability_engine.hydrographs import (
        conditioning_record_for_level,
        load_canonical_shape,
    )

    cache = np.load(CACHE)
    rel = cache["rel_hours"]
    width = fs.TEXTWIDTH_IN
    height = width * 0.46
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(width, height))
    clim = fs.CLIMATE_COLORS
    for scenario, key in (("historical", "historical"), ("+4K", "+4K")):
        a = cache[f"{scenario}_aligned"]
        cover = np.mean(np.isfinite(a), axis=0)
        keep = cover >= 0.9
        q10, q50, q90 = np.nanpercentile(a[:, keep], [10, 50, 90], axis=0)
        ax.fill_between(rel[keep], q10, q90, color=clim[key], alpha=0.16, lw=0)
        ax.plot(rel[keep], q50, color=clim[key], lw=1.6 * scale, zorder=4)
    special_style = {
        CANONICAL: dict(color=fs.INK, lw=1.3 * scale, ls=(0, (4, 1.6))),
        ALTERNATE: dict(color=fs.MUTED, lw=1.3 * scale, ls=(0, (1.2, 1.4))),
    }
    for eid, sty in special_style.items():
        s = cache[f"shape_{eid}"]
        k = int(np.argmax(s))
        ax.plot(np.arange(s.size) - k, s, zorder=5, **sty)
    ax.set_xlim(-48, 120)
    ax.set_xticks([-48, -24, 0, 24, 48, 72, 96, 120])
    ax.set_ylim(0, 1.03)
    ax.set_xlabel("hours from the peak")
    ax.set_ylabel("stage, fraction of the flood's rise")
    fs.panel_title(ax, "Shape of the annual flood", scale=scale, letter="a")

    # (b) hours above the toe against peak stage at KP 58.8
    fp = record["fixed_peak_duration_kp58_8"]
    geo = _section_geometry(DURATION_KP)
    for scenario, key in (("historical", "historical"), ("+4K", "+4K")):
        b = fp[scenario]
        ok = np.asarray(b["n"]) >= 30
        mid = (np.asarray(b["lo"]) + np.asarray(b["hi"])) / 2
        bx.fill_between(
            mid[ok],
            np.asarray(b["q25"])[ok],
            np.asarray(b["q75"])[ok],
            color=clim[key],
            alpha=0.16,
            lw=0,
        )
        bx.plot(
            mid[ok],
            np.asarray(b["med"])[ok],
            color=clim[key],
            lw=1.6 * scale,
            marker="o",
            ms=3.2 * scale,
            zorder=4,
        )
    canon = load_canonical_shape(
        DATA_RAW, river="Tokachi", kp=DURATION_KP, event_id=CANONICAL
    )
    levels = np.arange(geo["z_toe_m"] + 0.25, geo["z_toe_m"] + 5.01, 0.05)
    hrs = []
    for lv in levels:
        rc = conditioning_record_for_level(canon, float(lv), scenario="historical")
        hrs.append(float((np.asarray(rc.h) > geo["z_toe_m"]).sum()))
    bx.plot(levels, hrs, zorder=5, **special_style[CANONICAL])
    obs = record["three_rivers_2016"]["Tokachi, KP 58.8"]
    bx.plot(
        obs["peak_m"],
        sum(obs["hours_above_toe_runs"]),
        marker="D",
        ms=5.5 * scale,
        color=fs.SECTION_COLORS["KP58.8"],
        zorder=6,
        ls="none",
    )
    bx.axvline(
        geo["design_m"], color=fs.INK_2, lw=1.1 * scale, ls=(0, (5, 2)), zorder=2
    )
    bx.set_xlim(geo["z_toe_m"], geo["z_toe_m"] + 5.0)
    bx.set_ylim(0, None)
    bx.set_xlabel("annual peak stage at KP 58.8 [m T.P.]")
    bx.set_ylabel("hours above the landside toe")
    fs.panel_title(ax=bx, text="Time above the toe, KP 58.8", scale=scale, letter="b")

    handles = [
        Line2D([], [], color=clim["historical"], lw=1.6 * scale),
        Line2D([], [], color=clim["+4K"], lw=1.6 * scale),
        Patch(facecolor=fs.MUTED, alpha=0.3, lw=0),
        Line2D([], [], **special_style[CANONICAL]),
        Line2D([], [], **special_style[ALTERNATE]),
        Line2D([], [], color=fs.INK_2, lw=1.1 * scale, ls=(0, (5, 2))),
        Line2D(
            [],
            [],
            marker="D",
            ms=5.5 * scale,
            ls="none",
            color=fs.SECTION_COLORS["KP58.8"],
        ),
    ]
    labels = [
        "historical, median",
        "+4 K, median",
        "spread (a: 10 to 90 %, b: 25 to 75 %)",
        "canonical flood",
        "shorter alternative",
        "design level",
        "2016 record",
    ]
    fs.title(fig, "Annual-maximum floods in the two climates", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale, ncol=4)
    fs.layout(fig, scale=scale, legend_rows=2)
    return fs.save(fig, FIG_D4PDF, mirror=OUT_DIR / "figures")


def figures_part() -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as fs

    record = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    paths = [_fig_rivers(record, fs), _fig_d4pdf(record, fs)]
    return [str(p.relative_to(REPO)).replace("\\", "/") for p in paths]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("part", choices=("stats", "figures"))
    args = parser.parse_args(argv)
    if args.part == "stats":
        rec = stats_part()
        print(json.dumps(_round(rec["predictions"]), indent=1))
    else:
        print(figures_part())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
