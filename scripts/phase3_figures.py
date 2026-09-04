"""Publication figures for the Phase 3 RQ3+RQ4 campaign (thin driver).

Reads the ``results/system_integration/phase3/`` campaign outputs and the
committed surface curves and renders six figures to ``docs/figures/``:

1. ``phase3_dominance_profile.png`` — longitudinal annualized per-mechanism
   failure probability along both rivers, both scenarios (the RQ3 headline).
2. ``phase3_system_fragility_bep_sections.png`` — the composed conditional
   three-mechanism fragility at the four BEP sections.
3. ``phase3_rq4_four_sections.png`` — **the RQ4 headline**: annual system P_f
   historical vs +4K and the climate ratio at the four geotechnically
   characterised sections (campaign decision 5 scopes RQ3/RQ4 to these).
4. ``phase3_climate_shift.png`` — the same quantity across all 114 segments.
   Captioned **reach context, not the RQ4 answer**: 110 of 114 segments carry
   no BEP source under the production ``exact`` policy and are surface-only
   lower bounds.
5. ``phase3_rq4_attribution.png`` — duration/compound stratified conditional
   P_f at the BEP sections (RQ4 attribution).
6. ``phase3_event_based_validation.png`` — curve-based vs event-based annual
   surface-mechanism probabilities at the 9 section-representative nodes.

Usage: ``python scripts/phase3_figures.py`` (after ``phase3_campaign.py``
and ``validate_event_based_surface.py``).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "results/system_integration/phase3"
FIGS = REPO / "docs/figures"
#: Committed 95 % hazard-sampling intervals for the RQ4 headline figure.
INTERVALS = REPO / "docs/decisions/annualisation-hazard-sampling-uncertainty.json"

# Reference palette (validated project set; light mode), fixed slots.
MECH_COLORS = {
    "bep": "#2a78d6",  # slot 1 blue
    "overflow": "#008300",  # slot 2 green
    "fluvial_scour": "#e87ba4",  # slot 3 magenta
}
MECH_LABELS = {
    "bep": "BEP (posterior transient)",
    "overflow": "Overflow",
    "fluvial_scour": "Fluvial scour",
}

#: Rendered names for the ``rq4_annual.csv`` record vocabulary. ``d70`` and
#: ``lambda_ac_m`` are the annual table's own column names and are never
#: renamed to satisfy the figure rule (conventions section 9.3.1); the
#: substitution happens here, at render time. Chapter 3 names these the
#: grain-size reading and the spatial autocorrelation length, and the RQ4
#: headline figure already rendered them this way, so this is the driver's
#: single source for both.
D70_DISPLAY_NAMES: dict[str, str] = {
    "matrix": "matrix $d_{70}$",
    "bulk": "bulk $d_{70}$",
}
LAMBDA_AC_SYMBOL = r"$\lambda_\mathrm{ac}$"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

FLOOR = 1e-7  # display floor for log axes (zero -> below-floor marker)


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": BASELINE,
            "axes.labelcolor": INK_2,
            "axes.titlecolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "font.size": 10.5,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
        }
    )


def _primary(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        (df.d70 == "matrix")
        & (df.bep_source == "posterior")
        & (df.lambda_ac_m == 250.0)
        & (df.surface_variant == "primary")
    ]


def _hazard_intervals(df: pd.DataFrame) -> dict:
    """The committed 95 % hazard-sampling intervals, checked against this table.

    Written by ``scripts/annualisation_uncertainty_study.py``, which
    block-bootstraps the annualisation over d4PDF ensemble members with the
    fragility curves held fixed. Two properties matter here and both are
    asserted rather than assumed, because the alternative is a figure that
    silently loses its intervals or draws stale ones over fresh bars:

    * the record is a **tracked** artifact, so its absence is a failure, never
      a skip (``docs/conventions.md`` section 9.4);
    * every point estimate it carries must equal the published value, exactly.

    The comparison reads ``rq4_annual.csv`` again through the ``csv`` module
    rather than reusing the DataFrame: ``pandas.read_csv`` does not round-trip
    a float by default, and a staleness gate that fires on the reader's own
    last three digits is worse than no gate at all.
    """
    if not INTERVALS.is_file():
        raise FileNotFoundError(
            f"{INTERVALS.relative_to(REPO).as_posix()} is missing. It is a "
            "tracked artifact and the RQ4 headline figure draws its intervals "
            "from it. Regenerate with "
            "'python scripts/annualisation_uncertainty_study.py'."
        )
    payload = json.loads(INTERVALS.read_text(encoding="utf-8"))
    arm = payload["scope"]["primary_arm"]
    d70, source = arm.split("/")
    with open(P3 / "rq4_annual.csv", encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            label = f"KP {float(record['kp']):.1f}"
            if (
                record["d70"] != d70
                or record["bep_source"] != source
                or record["lambda_ac_m"] != "250.0"
                or record["surface_variant"] != "primary"
                or label not in payload["sections"]
            ):
                continue
            block = payload["sections"][label][arm][record["scenario"]]
            if str(block["p_annual_system"]["point"]) != record["p_annual_system"]:
                raise AssertionError(
                    f"the hazard-sampling record is stale at {label} "
                    f"{record['scenario']}: it carries "
                    f"{block['p_annual_system']['point']!r} where the annual "
                    f"table now has {record['p_annual_system']}. Drawing its "
                    "intervals over these bars would be wrong. Re-run "
                    "'python scripts/annualisation_uncertainty_study.py'."
                )
    return payload


def fig_dominance_profile(df: pd.DataFrame) -> None:
    base = _primary(df)
    fig, axes = plt.subplots(
        2, 2, figsize=(12.5, 7.6), sharey=True, gridspec_kw={"hspace": 0.42}
    )
    for i, river in enumerate(("Tokachi", "Satsunai")):
        for j, scenario in enumerate(("historical", "+4K")):
            ax = axes[i, j]
            sub = base[(base.river == river) & (base.scenario == scenario)]
            sub = sub.sort_values("kp")
            for mech in ("overflow", "fluvial_scour", "bep"):
                col = f"p_annual_{mech}"
                vals = pd.to_numeric(sub[col], errors="coerce")
                mask = vals.notna()
                if not mask.any():
                    continue
                shown = np.maximum(vals[mask].to_numpy(float), FLOOR)
                # BEP exists only at the four isolated OYO nodes — markers
                # only, never a connecting line implying reach continuity.
                fmt = "o" if mech == "bep" else ".-"
                ax.plot(
                    sub.kp[mask],
                    shown,
                    fmt,
                    color=MECH_COLORS[mech],
                    lw=1.4,
                    ms=7 if mech == "bep" else 5,
                    mfc="none" if mech == "bep" else None,
                    label=MECH_LABELS[mech],
                )
            sysv = np.maximum(sub.p_annual_system.to_numpy(float), FLOOR)
            ax.plot(sub.kp, sysv, "-", color=INK, lw=2.0, alpha=0.75, label="System")
            ax.set_yscale("log")
            ax.set_ylim(FLOOR, 1.0)
            ax.set_title(f"{river}, {scenario}")
            ax.set_xlabel("KP [km]")
            if j == 0:
                ax.set_ylabel("Annual failure probability [1/yr]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(
        "Annualized per-mechanism failure probability along the study reaches\n"
        f"(posterior BEP, {D70_DISPLAY_NAMES['matrix']}, "
        f"{LAMBDA_AC_SYMBOL} = 250 m; values at the display "
        f"floor {FLOOR:g} are exact zeros)",
        y=1.10,
        fontsize=11,
        color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGS / "phase3_dominance_profile.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def _max_attainable_stage(river: str, kp: float) -> float:
    """Largest +4K ensemble peak stage at the node (from the hazard cache)."""
    cache = (
        REPO
        / "results/system_integration/hazard_cache"
        / f"hazard_{river.lower()}_kp{kp:.1f}_plus4K.csv"
    )
    peaks = pd.read_csv(cache, skiprows=1)["peak_stage_m_msl"]
    return float(peaks.max())


def fig_bep_sections(curves: dict) -> None:
    keys = [f"Tokachi_KP{s}" for s in ("57.4", "58.8", "60", "62")]
    kps = (57.4, 58.8, 60.0, 62.0)
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.8), sharey=True)
    for ax, key, kp in zip(axes.ravel(), keys, kps):
        entry = curves[key]
        stage = np.asarray(entry["stage_m_msl"])
        for mech in entry["mechanisms"]:
            ax.plot(
                stage,
                entry["per_mechanism"][mech],
                color=MECH_COLORS[mech],
                lw=1.6,
                label=MECH_LABELS[mech],
            )
        ax.plot(stage, entry["p_sys"], color=INK, lw=2.2, alpha=0.8, label="System")
        # Stages beyond the largest +4K ensemble peak are unattainable —
        # KP62.0's grid extension is a fit stabilizer (ADR-0024), never to
        # be read as reachable loading.
        h_max = _max_attainable_stage("Tokachi", kp)
        if stage[-1] > h_max:
            ax.axvspan(h_max, stage[-1], color=GRID, alpha=0.45, zorder=0)
            ax.text(
                h_max + 0.1,
                0.5,
                "beyond max attainable\nstage (+4K ensemble)",
                fontsize=7.5,
                color=MUTED,
                rotation=90,
                va="center",
            )
        ax.set_title(f"Tokachi KP {kp:.1f}")
        ax.set_xlabel("Water level h [m T.P.]")
        ax.set_ylabel("P(failure | h)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(
        "Composed three-mechanism segment fragility at the BEP sections "
        f"(posterior, {D70_DISPLAY_NAMES['matrix']})",
        y=1.07,
        fontsize=11,
        color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(
        FIGS / "phase3_system_fragility_bep_sections.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)


def fig_climate_shift(df: pd.DataFrame) -> None:
    base = _primary(df)
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12.5, 7.2),
        sharex="col",
        gridspec_kw={"height_ratios": [2.2, 1.0], "hspace": 0.12},
    )
    for j, river in enumerate(("Tokachi", "Satsunai")):
        ax, axr = axes[0, j], axes[1, j]
        hist = base[(base.river == river) & (base.scenario == "historical")]
        futu = base[(base.river == river) & (base.scenario == "+4K")]
        hist, futu = hist.sort_values("kp"), futu.sort_values("kp")
        ax.plot(
            hist.kp,
            np.maximum(hist.p_annual_system.to_numpy(float), FLOOR),
            ".-",
            color="#2a78d6",
            lw=1.5,
            ms=5,
            label="historical (HPB, 3000 yr)",
        )
        ax.plot(
            futu.kp,
            np.maximum(futu.p_annual_system.to_numpy(float), FLOOR),
            ".-",
            color="#e34948",
            lw=1.5,
            ms=5,
            label="+4K (HFB, 5400 yr)",
        )
        # ADR-0037 lambda bracket at the BEP sections (posterior, matrix).
        brack = df[
            (df.river == river)
            & (df.d70 == "matrix")
            & (df.bep_source == "posterior")
            & (df.surface_variant == "primary")
            & (df.lambda_ac_m == 40.0)
        ]
        for scen, color in (("historical", "#2a78d6"), ("+4K", "#e34948")):
            b = brack[brack.scenario == scen].sort_values("kp")
            bep_nodes = b[b.mechanisms.str.contains("bep")]
            if len(bep_nodes):
                ax.plot(
                    bep_nodes.kp,
                    np.maximum(bep_nodes.p_annual_system.to_numpy(float), FLOOR),
                    marker="v",
                    ls="none",
                    ms=6,
                    mfc="none",
                    color=color,
                    label=(
                        f"{LAMBDA_AC_SYMBOL} = 40 m bracket"
                        if scen == "historical"
                        else None
                    ),
                )
        ax.set_yscale("log")
        # Headroom above the data, then pin the legend into it. The house
        # style draws legends unframed, so a marker left under the legend
        # strikes through its text: the 40 m bracket triangle at KP 57.4 sat
        # on the last letter of its own legend entry.
        ax.set_ylim(top=ax.get_ylim()[1] * 12.0)
        ax.set_title(river)
        ax.set_ylabel("Annual system $P_f$ [1/yr]" if j == 0 else "")
        ax.legend(fontsize=8.5, loc="upper left")

        merged = hist.merge(futu, on="kp", suffixes=("_h", "_f"))
        ratio = np.where(
            merged.p_annual_system_h > 0,
            merged.p_annual_system_f / np.maximum(merged.p_annual_system_h, 1e-300),
            np.nan,
        )
        axr.plot(merged.kp, ratio, ".-", color=INK_2, lw=1.3, ms=4)
        axr.set_yscale("log")
        axr.set_ylabel("+4K / historical" if j == 0 else "")
        axr.set_xlabel("KP [km]")
    # Caption, not decoration: 110 of the 114 segments carry bep_source None
    # under the production `exact` policy, so this distribution is reach context
    # and its surface-only segments are lower bounds. The quantified answer to
    # RQ4 is the four-section figure (fig_rq4_four_sections), not this one.
    fig.suptitle(
        "REACH CONTEXT (not the RQ4 answer): climate shift of the annualized "
        "system failure probability over all 114 segments\n"
        f"posterior BEP, {D70_DISPLAY_NAMES['matrix']}. 110 of 114 segments "
        "have no geotechnically characterized cross-section of their own and "
        "are surface-only LOWER BOUNDS;\n"
        "the quantified RQ4 answer is the four characterized sections, given "
        "separately.",
        fontsize=9.5,
        color=INK_2,
    )
    fig.savefig(FIGS / "phase3_climate_shift.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_rq4_four_sections(df: pd.DataFrame) -> None:
    """RQ4 headline: the four characterised sections, historical vs +4K.

    Owner decision 5 of the 2026-07-29 campaign scopes RQ3/RQ4 to the four
    geotechnically characterised sections, because the other 110 segments carry
    no BEP source and are surface-only lower bounds. This is therefore the
    figure that answers RQ4; ``phase3_climate_shift.png`` is reach context.

    Both panels carry a 95 % hazard-sampling interval (2026-08-20). It is the
    finite-ensemble spread of the peak-stage distribution with the fragility
    curves held fixed, so it is **not** the total uncertainty, and the figure
    says so in its own footnote rather than leaving the reader to assume
    otherwise: the aquifer-conductivity range is far wider and is a separate
    figure. The climate-ratio interval is formed inside each replicate, so it
    is an interval on the ratio and not a quotient of two marginal intervals.
    """
    intervals = _hazard_intervals(df)
    arm = intervals["scope"]["primary_arm"]
    recorded = intervals["sections"]
    base = _primary(df)
    bep = base[base.p_annual_bep.notna()].copy()
    bep["kp"] = bep.kp.astype(float)
    sections = sorted(bep.kp.unique())
    labels = [f"KP {kp:.1f}" for kp in sections]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12.4, 5.4),
        gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.28},
    )

    # --- panel 1: the two annual probabilities, and the BEP share of each ------
    ax = axes[0]
    x = np.arange(len(sections), dtype=float)
    width = 0.34
    headroom = 0.0
    for offset, scenario, color in (
        (-width / 2, "historical", "#2a78d6"),
        (+width / 2, "+4K", "#e34948"),
    ):
        rows = bep[bep.scenario == scenario].set_index("kp").loc[sections]
        total = rows.p_annual_system.to_numpy(float)
        bep_part = rows.p_annual_bep.to_numpy(float)
        band = np.array(
            [
                [
                    recorded[f"KP {kp:.1f}"][arm][scenario]["p_annual_system"][end]
                    for kp in sections
                ]
                for end in ("ci_low", "ci_high")
            ]
        )
        ax.bar(
            x + offset,
            np.maximum(total, FLOOR),
            width=width * 0.9,
            color=color,
            alpha=0.30,
            lw=0,
            label=f"{scenario}: system (all mechanisms)",
        )
        ax.bar(
            x + offset,
            np.maximum(bep_part, FLOOR),
            width=width * 0.9,
            color=color,
            lw=0,
            label=f"{scenario}: BEP contribution",
        )
        ax.errorbar(
            x + offset,
            total,
            yerr=np.abs(band - total),
            fmt="none",
            ecolor=INK_2,
            elinewidth=1.1,
            capsize=3.5,
            capthick=1.1,
            zorder=5,
        )
        for xi, value, top, share in zip(
            x + offset, total, band[1], rows.share_bep.to_numpy(float)
        ):
            ax.annotate(
                f"{value:.1e}\nBEP {share:.0%}",
                (xi, top),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize=8,
                color=INK_2,
            )
        headroom = max(headroom, float(band[1].max()))
    ax.set_yscale("log")
    ax.set_xticks(x, labels)
    ax.set_ylabel("annual system $P_f$ [1/yr]")
    ax.set_title(
        "RQ4: annual system failure probability at the four characterized "
        f"sections\nposterior BEP, {D70_DISPLAY_NAMES['matrix']}, "
        f"{LAMBDA_AC_SYMBOL} = 250 m, primary surface curves",
        loc="left",
    )
    ax.set_ylim(top=headroom * 12.0)
    ax.plot(
        [],
        [],
        color=INK_2,
        lw=1.1,
        marker="_",
        markersize=7,
        label="95 per cent flood-ensemble sampling interval",
    )
    ax.legend(fontsize=8.5, ncol=2, loc="upper left")
    ax.grid(axis="x", visible=False)

    # --- panel 2: the climate ratio, the number the thesis quotes --------------
    ax2 = axes[1]
    hist = bep[bep.scenario == "historical"].set_index("kp").loc[sections]
    futu = bep[bep.scenario == "+4K"].set_index("kp").loc[sections]
    ratio = futu.p_annual_system.to_numpy(float) / hist.p_annual_system.to_numpy(float)
    ratio_band = np.array(
        [
            [recorded[f"KP {kp:.1f}"][arm]["climate_ratio"][end] for kp in sections]
            for end in ("ci_low", "ci_high")
        ]
    )
    colors = ["#2a78d6", "#1baf7a", "#eda100", "#008300"]
    ax2.bar(x, ratio, width=0.55, color=colors[: len(sections)], lw=0)
    ax2.errorbar(
        x,
        ratio,
        yerr=np.abs(ratio_band - ratio),
        fmt="none",
        ecolor=INK_2,
        elinewidth=1.1,
        capsize=3.5,
        capthick=1.1,
        zorder=5,
    )
    for xi, value, top in zip(x, ratio, ratio_band[1]):
        ax2.annotate(
            rf"$\times${value:.1f}",
            (xi, top),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=10,
            color=INK,
        )
    ax2.axhline(1.0, color=BASELINE, lw=1.2)
    ax2.set_xticks(x, labels)
    ax2.set_ylabel("+4K / historical annual system $P_f$")
    ax2.set_ylim(0, float(ratio_band[1].max()) * 1.18)
    ax2.set_title(
        "Climate ratio per section, with its 95 per cent sampling interval\n"
        "KP 58.8 carries the highest absolute risk and the lowest ratio; the "
        "two outer sections are not distinguishable",
        loc="left",
    )
    ax2.grid(axis="x", visible=False)
    fig.text(
        0.5,
        -0.045,
        "Intervals are flood-ensemble sampling only: the fragility curves are "
        "held fixed, so this is not the total uncertainty. The aquifer "
        "conductivity range is far wider and does not cancel in the ratio.",
        ha="center",
        va="top",
        fontsize=8.5,
        color=INK_2,
    )
    fig.savefig(FIGS / "phase3_rq4_four_sections.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_attribution(attr: dict) -> None:
    sections = list(attr.keys())
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), sharey=True)
    width = 0.38
    for ax, scen, tint in zip(axes, ("historical", "+4K"), ("#2a78d6", "#e34948")):
        x = np.arange(len(sections))
        long_v = [attr[s][scen]["p_f_long_loading"] for s in sections]
        short_v = [attr[s][scen]["p_f_short_loading"] for s in sections]
        comp_v = [attr[s][scen]["p_f_compound"] for s in sections]
        ax.bar(
            x - width / 2,
            np.maximum(long_v, FLOOR),
            width * 0.9,
            color=tint,
            label=r"$>$ 24 h above toe",
        )
        ax.bar(
            x + width / 2,
            np.maximum(short_v, FLOOR),
            width * 0.9,
            color=tint,
            alpha=0.35,
            label=r"$\leq$ 24 h above toe",
        )
        ax.plot(
            x,
            np.maximum(comp_v, FLOOR),
            marker="D",
            ls="none",
            ms=6,
            color=INK,
            label=r"compound years ($\geq$ 2 excursions)",
        )
        ax.set_yscale("log")
        ax.set_xticks(x)
        # The record's node keys carry the chainage without its decimal at two
        # sections; the thesis names every section to one, so the display name
        # is normalised here rather than left to the key.
        ax.set_xticklabels(
            [f"KP {float(s.split('KP')[-1]):.1f}" for s in sections],
        )
        ax.set_title(scen)
        ax.legend(fontsize=8.5)
    axes[0].set_ylabel("Conditional annual system $P_f$ within stratum")
    fig.suptitle(
        "RQ4 attribution: duration- and compound-stratified conditional "
        f"failure probability (BEP sections, posterior, "
        f"{D70_DISPLAY_NAMES['matrix']})",
        fontsize=11,
        color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGS / "phase3_rq4_attribution.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_event_validation(df: pd.DataFrame, val: dict) -> None:
    base = _primary(df)
    fig, ax = plt.subplots(figsize=(6.8, 6.2))
    markers = {"historical": "o", "+4K": "s"}
    for key, node in val["nodes"].items():
        river, kp_s = key.split("_KP")
        kp = float(kp_s)
        for scen in ("historical", "+4K"):
            row = base[
                (base.river == river) & (base.kp == kp) & (base.scenario == scen)
            ]
            if row.empty or scen not in node:
                continue
            for mech, colkey in (
                ("overflow", "p_annual_overflow_event_based"),
                ("fluvial_scour", "p_annual_scour_event_based"),
            ):
                curve_v = float(pd.to_numeric(row[f"p_annual_{mech}"]).iloc[0])
                event_v = float(node[scen][colkey])
                ax.plot(
                    max(event_v, FLOOR),
                    max(curve_v, FLOOR),
                    markers[scen],
                    color=MECH_COLORS[mech],
                    ms=7,
                    mec=SURFACE,
                    mew=0.8,
                )
    lims = (FLOOR, 1.0)
    ax.plot(lims, lims, "-", color=BASELINE, lw=1.0, zorder=0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lims)
    ax.set_ylim(*lims)
    ax.set_xlabel("Event-based annual $P_f$ (full d4PDF ensembles)")
    ax.set_ylabel("Curve-based annual $P_f$ (canonical conditioning)")
    handles = [
        plt.Line2D(
            [], [], marker="o", ls="none", color=MECH_COLORS[m], label=MECH_LABELS[m]
        )
        for m in ("overflow", "fluvial_scour")
    ] + [
        plt.Line2D([], [], marker=mk, ls="none", color=INK_2, label=sc)
        for sc, mk in markers.items()
    ]
    ax.legend(handles=handles, fontsize=8.5)
    ax.set_title(
        "Surface mechanisms: canonical-shape curves vs event-based re-execution\n"
        "(9 section-representative nodes; diagonal = agreement)",
        fontsize=10.5,
    )
    fig.tight_layout()
    fig.savefig(
        FIGS / "phase3_event_based_validation.png", dpi=160, bbox_inches="tight"
    )
    plt.close(fig)


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    style()
    FIGS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(P3 / "rq4_annual.csv")
    curves = json.loads((P3 / "rq3_segment_curves_matrix_posterior.json").read_text())
    attr = json.loads((P3 / "rq4_attribution.json").read_text())

    fig_dominance_profile(df)
    fig_bep_sections(curves)
    fig_rq4_four_sections(df)
    fig_climate_shift(df)
    fig_attribution(attr)
    val_path = P3 / "event_based_validation.json"
    if val_path.exists():
        fig_event_validation(df, json.loads(val_path.read_text()))
    print(f"figures written to {FIGS}")


if __name__ == "__main__":
    main()
