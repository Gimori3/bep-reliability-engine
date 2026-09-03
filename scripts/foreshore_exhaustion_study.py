"""R10 Tier 1: foreshore-exhaustion screening across the study sections.

Companion driver for the review item R10 scoping note
(``docs/scoping_bank_retreat_mechanism.md`` Tier 1) and the companion note
``docs/decisions/r10-foreshore-exhaustion-screening.md``. It answers one
question per segment and forcing case:

    how long does this flood take to erode away the high-water bed in front
    of the levee, and how does that compare with how long the flood lasts?

Method
------
The indicator itself is :mod:`system_integration.foreshore_exhaustion` —
pure arithmetic, no physics, forcing injected. This driver supplies the
forcing from records that already exist and are already verified, and never
invents a hydrograph:

* ``event_2016`` — the observed August 2016 consecutive-typhoon record at
  each section, via the Phase 2 loader
  :func:`bayesian_reliability_updating.events.observed_event_record`
  (ADR-0035: Obihiro stage, inverse gauge rating, section rating through
  verbatim M3, peak anchored to the surveyed right-bank flood trace).
* ``conditioning_grid`` — the Phase 1 conditioning records via
  :func:`bep_reliability_engine.run.conditioning_hydrographs_for_config`
  (ADR-0020 canonical d4PDF shape scaled per level, ADR-0030 225 s grid).
  The design-class reading is the level nearest the section's design HWL.
* ``d4pdf_ensemble`` (optional, ``--no-ensemble`` to skip) — the mobilising
  duration of every annual-maximum ensemble event at the section, historical
  (HPB, 3,000 y) against +4K (HFB, 5,400 y). Under ADR-0023 the event
  *shape* is climate-invariant, so this is the only place a climate signal
  can appear for this indicator: in how often a long mobilising window
  occurs, never in the indicator's stage dependence.

Three deliberate brackets, because none of the three is measured:

1. **Retreat rate** — :data:`~system_integration.foreshore_exhaustion.\
RETREAT_RATE_BRACKET_M_PER_H`, 0.1 to 10 m/h, two orders of magnitude. The
   headline number reported per case is instead the *critical* rate
   ``v* = B_f / mobilising_hours``, which puts the assumption on one axis.
2. **Mobilisation threshold** — the high-water-bed surface plus/minus 1.0 m.
   The band is not invented: at KP 62.0 the OYO 1998 様式-5 高水敷高 reads
   45.00 m T.P. against 43.82 m in Uemura's MLIT-derived df_river, a 1.18 m
   cross-source spread on the same terrace.
3. **Forcing** — an observed event of record against the design-class
   conditioning ladder.

Limits, stated up front
-----------------------
This is order-of-magnitude screening. It is not a probability and not a
failure rate. It has no planform, no bend mechanics, no sediment supply and
no representation of why a thalweg approaches one bank rather than another,
and the only documented retreat datum for this basin (2011 Otofuke, ~5 m of
levee *length* per hour) is one narrative observation and is *longitudinal*,
carried into the bracket unconverted and labelled as such.

Scope
-----
Nothing here is persisted into ``results/`` as a deliverable, no production
default is touched, no ``Config`` field is added, and no mechanism joins the
Phase 3 composition (Tier 2, declined). The evidence JSON lands in
``docs/decisions/``; the optional ensemble arm caches its per-event tables
under a study-local directory, never the production Phase 3 hazard cache.

Usage
-----
    python scripts/foreshore_exhaustion_study.py
    python scripts/foreshore_exhaustion_study.py --sections KP62.0 --no-ensemble

Runtime is seconds without the ensemble arm; the first ensemble run streams
the d4PDF band workbooks once per scenario (minutes), then caches.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from bayesian_reliability_updating.events import (
    default_2016_source,
    observed_event_record,
)
from bep_reliability_engine.config import Config
from bep_reliability_engine.run import conditioning_hydrographs_for_config
from system_integration.foreshore_exhaustion import (
    RETREAT_RATE_BRACKET_M_PER_H,
    ForeshoreState,
    critical_retreat_rate_m_per_h,
    foreshore_coverage,
    foreshore_exhaustion,
    load_measured_foreshore_states,
    mobilising_duration_hours,
)
from system_integration.segments import build_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = (
    REPO_ROOT / "docs" / "decisions" / "r10-foreshore-exhaustion-screening.json"
)
DEFAULT_FIGURE = REPO_ROOT / "docs" / "figures" / "r10_foreshore_exhaustion.png"
DEFAULT_HAZARD_CACHE = (
    REPO_ROOT / "results" / "sensitivity" / "foreshore_exhaustion" / "hazard_cache"
)

#: Section label -> Phase 1 config. Only the four confined OYO sections have
#: a measured 高水敷幅; the label set is derived from that, not chosen here.
SECTION_CONFIGS: dict[str, str] = {
    "KP57.4": "configs/kp57_4_historical_matrix.yaml",
    "KP58.8": "configs/kp58_8_historical_matrix.yaml",
    "KP60.0": "configs/kp60_0_historical_matrix.yaml",
    "KP62.0": "configs/kp62_0_historical_matrix.yaml",
}

#: ADR-0025-verified OYO 様式-3 高水敷幅 values [m]. Asserted, not read as
#: advisory: a study that silently ran on an edited geotech CSV would also
#: silently invalidate every persisted sweep through ``config_hash()``.
VERIFIED_FORESHORE_WIDTHS_M: dict[float, float] = {
    57.4: 200.0,
    58.8: 325.0,
    60.0: 600.0,
    62.0: 44.0,
}

#: Mobilisation-threshold band [m] about the high-water-bed surface; the
#: magnitude is the measured KP 62.0 OYO-vs-MLIT cross-source spread.
THRESHOLD_OFFSETS_M: tuple[float, ...] = (-1.0, 0.0, +1.0)

#: The KP 62.0 (44 m) versus KP 60.0 (600 m) separation the indicator must
#: reproduce to be worth anything; the measured value is reported, this is
#: only the floor below which something is wrong.
MIN_KP62_KP60_SEPARATION = 5.0


def _threshold_label(offset_m: float) -> str:
    if offset_m == 0.0:
        return "z_mob"
    return f"z_mob{offset_m:+.1f}m"


def _screen(
    stage: np.ndarray,
    dt_seconds: float,
    state: ForeshoreState,
    threshold_m: float,
) -> dict[str, Any]:
    """One (record, threshold) screened across the whole rate bracket."""
    hours = mobilising_duration_hours(stage, dt_seconds, threshold_m)
    per_rate: dict[str, Any] = {}
    for name, rate in RETREAT_RATE_BRACKET_M_PER_H.items():
        result = foreshore_exhaustion(
            stage,
            dt_seconds,
            foreshore_width_m=state.foreshore_width_m,
            mobilisation_stage_m_msl=threshold_m,
            retreat_rate_m_per_h=rate,
        )
        per_rate[name] = {
            "retreat_rate_m_per_h": result.retreat_rate_m_per_h,
            "cumulative_retreat_m": result.cumulative_retreat_m,
            "time_to_exhaustion_h": result.time_to_exhaustion_h,
            "exposure_ratio": result.exposure_ratio,
            "exhausted": result.exhausted,
        }
    probe = foreshore_exhaustion(
        stage,
        dt_seconds,
        foreshore_width_m=state.foreshore_width_m,
        mobilisation_stage_m_msl=threshold_m,
        retreat_rate_m_per_h=RETREAT_RATE_BRACKET_M_PER_H["central"],
    )
    return {
        "threshold_m_msl": float(threshold_m),
        "mobilising_hours": hours,
        "record_hours": probe.record_hours,
        "peak_stage_m_msl": probe.peak_stage_m_msl,
        "peak_excess_depth_m": probe.peak_excess_depth_m,
        "mean_excess_depth_m": probe.mean_excess_depth_m,
        "critical_retreat_rate_m_per_h": critical_retreat_rate_m_per_h(
            state.foreshore_width_m, hours
        ),
        "rates": per_rate,
    }


def _ensemble_arm(
    states: tuple[ForeshoreState, ...],
    *,
    data_root: Path,
    cache_dir: Path,
) -> dict[str, Any]:
    """Mobilising-duration distribution per scenario over the d4PDF ensemble.

    Reported as duration statistics and as the *count* of simulated
    annual-maximum events whose mobilising window exceeds the exhaustion
    time — an ensemble frequency of a screening flag, deliberately NOT an
    annual failure probability.
    """
    from system_integration.hazard import load_reach_hazard

    nodes = [
        (s.river, s.kp, s.mobilisation_stage_m_msl) for s in states
    ]  # per-node datum = the high-water-bed surface
    out: dict[str, Any] = {}
    for scenario in ("historical", "+4K"):
        cache_dir.mkdir(parents=True, exist_ok=True)
        hazards = load_reach_hazard(
            data_root, nodes=nodes, scenario=scenario, cache_dir=cache_dir
        )
        per_node: dict[str, Any] = {}
        for state in states:
            hazard = hazards[(state.river, round(state.kp, 3))]
            hours = np.asarray(
                [e.hours_above_datum for e in hazard.events], dtype=np.float64
            )
            entry: dict[str, Any] = {
                "n_years": hazard.n_years,
                "band_workbook": hazard.provenance["band_workbook"],
                "mobilising_hours_median": float(np.median(hours)),
                "mobilising_hours_p90": float(np.percentile(hours, 90.0)),
                "mobilising_hours_p99": float(np.percentile(hours, 99.0)),
                "mobilising_hours_max": float(hours.max()),
                "share_years_bed_mobilised": float((hours > 0.0).mean()),
                "flag_counts": {},
            }
            for name, rate in RETREAT_RATE_BRACKET_M_PER_H.items():
                exhaustion_h = state.foreshore_width_m / rate
                n_flag = int((hours * rate >= state.foreshore_width_m).sum())
                entry["flag_counts"][name] = {
                    "retreat_rate_m_per_h": rate,
                    "time_to_exhaustion_h": exhaustion_h,
                    "n_events_flagged": n_flag,
                    "share_events_flagged": n_flag / hazard.n_years,
                }
            per_node[f"KP{state.kp:.1f}"] = entry
        out[scenario] = per_node
    return out


def study_section(
    label: str,
    state: ForeshoreState,
    config: Config,
    *,
    event_source,
) -> dict[str, Any]:
    """Screen one section against both forcing families."""
    started = time.time()

    record = observed_event_record(event_source, section_kp=state.kp)
    event_stage = np.asarray(record.h, dtype=np.float64)
    event = {
        _threshold_label(offset): _screen(
            event_stage,
            float(record.native_dt),
            state,
            state.mobilisation_stage_m_msl + offset,
        )
        for offset in THRESHOLD_OFFSETS_M
    }

    grid = np.asarray(config.mc.conditioning_grid, dtype=float)
    records = conditioning_hydrographs_for_config(config)
    levels = []
    for level_m, level_record in zip(grid, records, strict=True):
        stage = np.asarray(level_record.h, dtype=np.float64)
        dt_seconds = float(level_record.native_dt)
        hours = mobilising_duration_hours(
            stage, dt_seconds, state.mobilisation_stage_m_msl
        )
        levels.append(
            {
                "stage_m_msl": float(level_m),
                "mobilising_hours": hours,
                "critical_retreat_rate_m_per_h": critical_retreat_rate_m_per_h(
                    state.foreshore_width_m, hours
                ),
                "exposure_ratio": {
                    name: (
                        (rate * hours / state.foreshore_width_m)
                        if state.foreshore_width_m > 0.0
                        else float("inf")
                    )
                    for name, rate in RETREAT_RATE_BRACKET_M_PER_H.items()
                },
            }
        )

    hwl_index = int(np.abs(grid - config.geometry.HWL).argmin())
    hwl_record = records[hwl_index]
    hwl_stage = np.asarray(hwl_record.h, dtype=np.float64)
    design = {
        _threshold_label(offset): _screen(
            hwl_stage,
            float(hwl_record.native_dt),
            state,
            state.mobilisation_stage_m_msl + offset,
        )
        for offset in THRESHOLD_OFFSETS_M
    }

    top_record = records[-1]
    grid_top = _screen(
        np.asarray(top_record.h, dtype=np.float64),
        float(top_record.native_dt),
        state,
        state.mobilisation_stage_m_msl,
    )

    return {
        "section": label,
        "river": state.river,
        "bank": state.bank,
        "kp": state.kp,
        "foreshore_width_m": state.foreshore_width_m,
        "foreshore_width_source": state.width_source,
        "mobilisation_stage_m_msl": state.mobilisation_stage_m_msl,
        "mobilisation_stage_source": state.stage_source,
        "z_toe_m_msl": float(config.geometry.z_toe),
        "design_hwl_m_msl": float(config.geometry.HWL),
        "event_2016": {"event_id": record.event_id, "thresholds": event},
        "design_hwl": {
            "conditioning_level_m_msl": float(grid[hwl_index]),
            "thresholds": design,
        },
        "grid_top": {
            "conditioning_level_m_msl": float(grid[-1]),
            "z_mob": grid_top,
        },
        "conditioning_grid": {
            "threshold_m_msl": state.mobilisation_stage_m_msl,
            "levels": levels,
        },
        "elapsed_s": round(time.time() - started, 2),
    }


def _assert_inputs_undrifted(states: tuple[ForeshoreState, ...]) -> None:
    """Refuse to report a screening run against edited geotech inputs."""
    for state in states:
        expected = VERIFIED_FORESHORE_WIDTHS_M.get(round(state.kp, 3))
        if expected is None:
            continue
        if float(state.foreshore_width_m) != expected:
            raise AssertionError(
                f"KP {state.kp:g}: foreshore_width_m is "
                f"{state.foreshore_width_m:g} m, not the ADR-0025-verified "
                f"{expected:g} m. The geotech CSV has been edited; that "
                "invalidates every persisted Phase 1 sweep through "
                "config_hash(). Refusing to report a screening result."
            )


def _separation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """The KP 62.0 / KP 60.0 sanity anchor, measured on both forcings."""
    by_kp = {round(r["kp"], 3): r for r in records}
    out: dict[str, Any] = {}
    for case in ("event_2016", "design_hwl"):
        if 62.0 not in by_kp or 60.0 not in by_kp:
            continue
        ratios = {}
        for kp in (62.0, 60.0):
            block = by_kp[kp][case]["thresholds"]["z_mob"]
            ratios[kp] = block["rates"]["central"]["exposure_ratio"]
        separation = ratios[62.0] / ratios[60.0] if ratios[60.0] > 0 else float("inf")
        out[case] = {
            "exposure_ratio_kp62_0": ratios[62.0],
            "exposure_ratio_kp60_0": ratios[60.0],
            "separation": separation,
            "foreshore_width_ratio": 600.0 / 44.0,
        }
        if separation < MIN_KP62_KP60_SEPARATION:
            raise AssertionError(
                f"{case}: KP 62.0 (44 m of bed) and KP 60.0 (600 m) separate "
                f"by only {separation:.2f}x, below the {MIN_KP62_KP60_SEPARATION}x "
                "floor. A 13.6x width contrast must show through; investigate "
                "the thresholds or the forcing before reporting."
            )
    return out


#: Plain-English rendering of the forcing-case and retreat-rate keys, for
#: figure text only. The keys are the evidence record's own field names (and,
#: for the rates, the shipped bracket's) and must not change; a main-body
#: thesis figure may not print them.
CASE_DISPLAY_NAMES = {"event_2016": "2016 event", "design_hwl": "design HWL"}
RATE_DISPLAY_NAMES = {"narrative_2011": "2011 account"}


def _make_figure(records: list[dict[str, Any]], out_path: Path) -> None:
    """Exposure ratio versus bed width, and the critical-rate ladder."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.5, 4.6))

    widths = np.asarray([r["foreshore_width_m"] for r in records], dtype=float)
    order = np.argsort(widths)
    colors = plt.get_cmap("viridis")(
        np.linspace(0.08, 0.86, len(RETREAT_RATE_BRACKET_M_PER_H))
    )
    for (name, rate), color in zip(RETREAT_RATE_BRACKET_M_PER_H.items(), colors):
        for case, marker, style in (
            ("event_2016", "o", "-"),
            ("design_hwl", "s", "--"),
        ):
            ratios = np.asarray(
                [
                    r[case]["thresholds"]["z_mob"]["rates"][name]["exposure_ratio"]
                    for r in records
                ],
                dtype=float,
            )
            ax_a.plot(
                widths[order],
                ratios[order],
                style,
                marker=marker,
                color=color,
                markersize=5,
                linewidth=1.2,
                label=(
                    f"{RATE_DISPLAY_NAMES.get(name, name)} ({rate:g} m/h), "
                    f"{CASE_DISPLAY_NAMES[case]}"
                ),
            )
    ax_a.axhline(1.0, color="crimson", linewidth=1.4)
    ax_a.text(
        0.98,
        1.0,
        " bed exhausted",
        color="crimson",
        va="bottom",
        ha="right",
        fontsize=8,
        transform=ax_a.get_yaxis_transform(),
    )
    for record in records:
        ratio = record["event_2016"]["thresholds"]["z_mob"]["rates"]["central"][
            "exposure_ratio"
        ]
        ax_a.annotate(
            record["section"],
            (record["foreshore_width_m"], ratio),
            textcoords="offset points",
            xytext=(4, 5),
            fontsize=8,
        )
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    # The bracket carried the Japanese term for the quantity; the thesis
    # romanises nothing it can translate, and "high-water-bed width" already
    # is that translation, so the bracket names the source instead.
    ax_a.set_xlabel("measured high-water-bed width $B_f$ [m] (OYO survey)")
    ax_a.set_ylabel(r"exposure ratio  $v_\mathrm{lat}\,T_\mathrm{mob} / B_f$  [-]")
    ax_a.set_title("(a) Exposure ratio across the retreat-rate bracket")
    ax_a.grid(alpha=0.3, which="both")
    ax_a.legend(fontsize=6.2, ncol=2, loc="lower left")

    for record in records:
        levels = record["conditioning_grid"]["levels"]
        stages = np.asarray([lv["stage_m_msl"] for lv in levels], dtype=float)
        crit = np.asarray(
            [lv["critical_retreat_rate_m_per_h"] for lv in levels], dtype=float
        )
        finite = np.isfinite(crit)
        (line,) = ax_b.plot(
            stages[finite] - record["design_hwl_m_msl"],
            crit[finite],
            "-",
            linewidth=1.5,
            label=f"{record['section']}  ($B_f$ = {record['foreshore_width_m']:g} m)",
        )
        event_crit = record["event_2016"]["thresholds"]["z_mob"][
            "critical_retreat_rate_m_per_h"
        ]
        event_peak = record["event_2016"]["thresholds"]["z_mob"]["peak_stage_m_msl"]
        ax_b.plot(
            event_peak - record["design_hwl_m_msl"],
            event_crit,
            marker="*",
            markersize=11,
            linestyle="none",
            color=line.get_color(),
        )
    lo = min(RETREAT_RATE_BRACKET_M_PER_H.values())
    hi = max(RETREAT_RATE_BRACKET_M_PER_H.values())
    ax_b.axhspan(lo, hi, color="0.82", alpha=0.55, zorder=0)
    ax_b.text(
        0.02,
        (lo * hi) ** 0.5,
        "assumed retreat-rate bracket",
        fontsize=8,
        color="0.25",
        va="center",
        transform=ax_b.get_yaxis_transform(),
    )
    ax_b.axvline(0.0, color="0.35", linewidth=1.0, linestyle=":")
    ax_b.set_yscale("log")
    ax_b.set_xlabel("conditioning stage relative to the design HWL [m]")
    ax_b.set_ylabel(r"critical retreat rate  $v^{*} = B_f / T_\mathrm{mob}$  [m/h]")
    ax_b.set_title("(b) Rate needed to exhaust the bed ($\\star$ = 2016 event)")
    ax_b.grid(alpha=0.3, which="both")
    ax_b.legend(fontsize=7.5, loc="upper right")

    fig.suptitle(
        "Foreshore-exhaustion screening indicator: order-of-magnitude only, "
        "not a probability",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sections",
        nargs="+",
        default=list(SECTION_CONFIGS),
        choices=list(SECTION_CONFIGS),
        help="Sections to screen (default: all four with a measured B_f).",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=REPO_ROOT / "data" / "raw",
        help="Raw data root (M3 conventions).",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Evidence JSON output path."
    )
    parser.add_argument(
        "--figure", type=Path, default=DEFAULT_FIGURE, help="Figure output path."
    )
    parser.add_argument(
        "--hazard-cache",
        type=Path,
        default=DEFAULT_HAZARD_CACHE,
        help=(
            "Study-local d4PDF per-event cache directory. Never point this at "
            "the production Phase 3 hazard cache: the exposure datum differs."
        ),
    )
    parser.add_argument(
        "--no-ensemble",
        action="store_true",
        help="Skip the d4PDF ensemble climate arm (the slow step).",
    )
    parser.add_argument("--no-figure", action="store_true", help="Skip the figure.")
    args = parser.parse_args()

    registry = build_registry(args.data_root)
    states = load_measured_foreshore_states(registry)
    _assert_inputs_undrifted(states)
    coverage = foreshore_coverage(registry, states)
    print(
        f"coverage: {coverage['n_screened']}/{coverage['n_segments']} segments "
        f"carry a measured high-water-bed width "
        f"({coverage['n_without_measured_width']} do not)",
        flush=True,
    )

    by_kp = {round(s.kp, 3): s for s in states}
    selected_kps = [
        round(float(label.removeprefix("KP")), 3) for label in args.sections
    ]
    event_source = default_2016_source()
    records: list[dict[str, Any]] = []
    for label, kp in zip(args.sections, selected_kps, strict=True):
        state = by_kp.get(kp)
        if state is None:
            raise SystemExit(
                f"{label}: no measured foreshore width in the registry-joined "
                "inputs; the screenable set is "
                f"{[f'KP{s.kp:.1f}' for s in states]}."
            )
        print(f"[{label}] screening ...", flush=True)
        config = Config.from_yaml(REPO_ROOT / SECTION_CONFIGS[label])
        record = study_section(label, state, config, event_source=event_source)
        records.append(record)
        for case in ("event_2016", "design_hwl"):
            block = record[case]["thresholds"]["z_mob"]
            print(
                f"  {case:<12} T_mob = {block['mobilising_hours']:6.1f} h, "
                f"B_f = {state.foreshore_width_m:5.0f} m, "
                f"v* = {block['critical_retreat_rate_m_per_h']:7.2f} m/h, "
                f"ratio(central 1 m/h) = "
                f"{block['rates']['central']['exposure_ratio']:.3f}",
                flush=True,
            )

    separation = _separation(records)
    for case, block in separation.items():
        print(
            f"KP62.0 / KP60.0 separation ({case}): {block['separation']:.1f}x "
            f"against a {block['foreshore_width_ratio']:.1f}x width contrast",
            flush=True,
        )

    ensemble: dict[str, Any] | None = None
    if not args.no_ensemble:
        print("d4PDF ensemble arm (streams the band workbooks once) ...", flush=True)
        screened = tuple(s for s in states if round(s.kp, 3) in set(selected_kps))
        ensemble = _ensemble_arm(
            screened, data_root=args.data_root, cache_dir=args.hazard_cache
        )
        for scenario, per_node in ensemble.items():
            for node, entry in per_node.items():
                print(
                    f"  {scenario:<10} {node:<8} "
                    f"median {entry['mobilising_hours_median']:5.1f} h, "
                    f"p99 {entry['mobilising_hours_p99']:6.1f} h, "
                    f"max {entry['mobilising_hours_max']:6.1f} h",
                    flush=True,
                )

    payload = {
        "study": "R10 Tier 1 foreshore-exhaustion screening indicator",
        "generated_by": "scripts/foreshore_exhaustion_study.py",
        "scoping_note": "docs/scoping_bank_retreat_mechanism.md",
        "companion_note": "docs/decisions/r10-foreshore-exhaustion-screening.md",
        "tier": 1,
        "not_a_probability": (
            "exposure_ratio is a deterministic screening flag on an assumed "
            "retreat rate, not a failure probability and not a rate. No "
            "mechanism was added to the Phase 3 composition (Tier 2 declined)."
        ),
        "retreat_rate_bracket_m_per_h": RETREAT_RATE_BRACKET_M_PER_H,
        "retreat_rate_provenance": (
            "No calibrated lateral retreat rate exists for this mechanism on "
            "this river. The single documented datum is the September 2011 "
            "Otofuke KP 18.2 account of ~5 m of levee LENGTH lost per hour "
            "with no revetment present — a longitudinal rate from a prose "
            "narrative in a flood-control history, entered as the labelled "
            "'narrative_2011' bracket member unconverted. The bracket spans "
            "two orders of magnitude precisely because the rate is unknown."
        ),
        "threshold_offsets_m": list(THRESHOLD_OFFSETS_M),
        "threshold_provenance": (
            "Primary threshold = the high-water-bed surface "
            "(floodplain_m_msl, Uemura df_river FloodplaneHeight, T.P. m MSL). "
            "The +/-1.0 m band is the measured KP 62.0 cross-source spread "
            "between the OYO 1998 kousuishiki-daka 45.00 m and the 43.82 m in "
            "the MLIT-derived table."
        ),
        "coverage": coverage,
        "sanity_anchor": separation,
        "sections": records,
        "d4pdf_ensemble": ensemble,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out}")

    if not args.no_figure:
        _make_figure(records, args.figure)
        print(f"wrote {args.figure}")


if __name__ == "__main__":
    main()
