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
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import _figstyle as fs  # noqa: E402

P3 = REPO / "results/system_integration/phase3"
FIGS = REPO / "docs/figures"
#: Committed 95 % hazard-sampling intervals for the RQ4 headline figure.
INTERVALS = REPO / "docs/decisions/annualisation-hazard-sampling-uncertainty.json"

# The mechanism palette is the shared one, beside the section and climate
# palettes, so the three hues cannot drift apart between figures.
MECH_COLORS = fs.MECHANISM_COLORS
MECH_LABELS = fs.MECHANISM_LABELS
MECH_LINESTYLES = fs.MECHANISM_LINESTYLES

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

#: The two climate scenarios, from the house palette. Until 2026-09-09 these
#: were the static/transient blue and red, which a reader of Chapter 6 has
#: learned as the two limit states.
SCEN_COLORS = fs.CLIMATE_COLORS
#: How each scenario is written in rendered text: the thesis sets the warming
#: case ``$+4$\,K``, and "+4K" without its space had spread across six figures.
SCEN_LABELS = fs.CLIMATE_LABELS

#: Authored width and placement fraction per figure, for the printed type
#: scale (``docs/conventions.md`` section 9.3.2).
WIDTH_IN = {
    "dominance": 12.5,
    "sections": 11.5,
    "climate": 12.5,
    "rq4": 12.4,
    "attribution": 12.0,
    "event": 6.8,
}
PLACEMENT = {
    "dominance": 1.0,
    "sections": 1.0,
    "climate": 1.0,
    "rq4": 1.0,
    "attribution": 1.0,
    "event": 0.80,
}


def _scale(key: str) -> float:
    """This figure's authored points per printed point, and set the rcParams."""
    value = fs.scale_for(WIDTH_IN[key], PLACEMENT[key])
    fs.style(value)
    return value


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
    scale = _scale("dominance")
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(WIDTH_IN["dominance"], 7.6),
        sharey=True,
        gridspec_kw={"hspace": 0.42, "wspace": 0.08},
    )
    for i, river in enumerate(("Tokachi", "Satsunai")):
        for j, scenario in enumerate(("historical", "+4K")):
            ax = axes[i, j]
            sub = base[(base.river == river) & (base.scenario == scenario)]
            sub = sub.sort_values("kp")
            # The system curve goes down first, as a wide pale halo. Drawn on
            # top as a heavy dark stroke it hid the overflow branch it
            # coincides with almost everywhere, which is the branch that
            # governs 110 of the 114 segments.
            sysv = np.maximum(sub.p_annual_system.to_numpy(float), FLOOR)
            ax.plot(
                sub.kp,
                sysv,
                "-",
                color=INK,
                lw=5.0,
                alpha=0.16,
                solid_capstyle="round",
                zorder=1,
                label="System",
            )
            for mech in ("overflow", "fluvial_scour", "bep"):
                col = f"p_annual_{mech}"
                vals = pd.to_numeric(sub[col], errors="coerce")
                mask = vals.notna()
                if not mask.any():
                    continue
                shown = np.maximum(vals[mask].to_numpy(float), FLOOR)
                # BEP exists only at the four isolated OYO nodes — markers
                # only, never a connecting line implying reach continuity.
                fmt = "o" if mech == "bep" else "."
                ax.plot(
                    sub.kp[mask],
                    shown,
                    fmt,
                    color=MECH_COLORS[mech],
                    # The dash pattern is the second channel: overflow and
                    # scour are all but identical in luminance.
                    ls=MECH_LINESTYLES[mech],
                    lw=1.4,
                    ms=7 if mech == "bep" else 5,
                    mfc="none" if mech == "bep" else None,
                    zorder=3,
                    label=MECH_LABELS[mech],
                )
            ax.set_yscale("log")
            ax.set_ylim(FLOOR, 1.0)
            fs.panel_title(ax, f"{river}, {SCEN_LABELS[scenario]}", scale=scale)
            ax.set_xlabel("KP [km]")
            if j == 0:
                ax.set_ylabel("Annual failure probability [1/yr]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    wanted = ("Overflow", "Fluvial scour", MECH_LABELS["bep"], "System")
    order = [labels.index(v) for v in wanted]
    fs.legend_below(
        fig, [handles[i] for i in order], [labels[i] for i in order], scale=scale
    )
    fs.title(
        fig,
        "Annual failure probability of each mechanism along the two reaches",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=1)
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
    scale = _scale("sections")
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH_IN["sections"], 7.8), sharey=True)
    for ax, key, kp in zip(axes.ravel(), keys, kps):
        entry = curves[key]
        stage = np.asarray(entry["stage_m_msl"])
        for mech in entry["mechanisms"]:
            ax.plot(
                stage,
                entry["per_mechanism"][mech],
                color=MECH_COLORS[mech],
                # The dash pattern is the second channel; see _figstyle.
                ls="-" if mech == "bep" else MECH_LINESTYLES[mech],
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
            # Horizontal and centred in the band. At the band's left edge the
            # overflow curve is still rising at two sections and used to run
            # straight through the label; at the centre every curve has
            # saturated. The plate is insurance, not the fix.
            ax.text(
                0.5 * (h_max + stage[-1]),
                0.5,
                "beyond max\nattainable stage\n(+4 K ensemble)",
                fontsize=fs.pt("small", scale),
                color=MUTED,
                ha="center",
                va="center",
                linespacing=1.35,
                zorder=6,
                bbox={
                    "facecolor": SURFACE,
                    "edgecolor": "none",
                    "alpha": 0.85,
                    "pad": 2.0,
                },
            )
        fs.panel_title(ax, f"Tokachi KP {kp:.1f}", scale=scale)
        ax.set_xlabel("Water level h [m T.P.]")
        ax.set_ylabel("P(failure | h)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fs.legend_below(fig, handles, labels, scale=scale)
    fs.title(
        fig,
        "Composed three-mechanism fragility at the four cross-sections",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=1)
    fig.savefig(
        FIGS / "phase3_system_fragility_bep_sections.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)


def fig_climate_shift(df: pd.DataFrame) -> None:
    base = _primary(df)
    scale = _scale("climate")
    # ``sharey="row"`` on 2026-09-09: the two reaches were drawn side by side
    # on different vertical scales, which invites a comparison of heights that
    # do not correspond. The reach comparison is the figure's whole purpose.
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(WIDTH_IN["climate"], 7.2),
        sharex="col",
        sharey="row",
        gridspec_kw={"height_ratios": [2.2, 1.0], "hspace": 0.12, "wspace": 0.08},
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
            color=SCEN_COLORS["historical"],
            lw=1.5,
            ms=5,
            label="historical (HPB, 3000 yr)",
        )
        ax.plot(
            futu.kp,
            np.maximum(futu.p_annual_system.to_numpy(float), FLOOR),
            ".-",
            color=SCEN_COLORS["+4K"],
            lw=1.5,
            ms=5,
            label="+4 K (HFB, 5400 yr)",
        )
        # ADR-0037 lambda bracket at the BEP sections (posterior, matrix).
        brack = df[
            (df.river == river)
            & (df.d70 == "matrix")
            & (df.bep_source == "posterior")
            & (df.surface_variant == "primary")
            & (df.lambda_ac_m == 40.0)
        ]
        for scen in ("historical", "+4K"):
            color = SCEN_COLORS[scen]
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
                        f"{LAMBDA_AC_SYMBOL} = 40 m bracket, " f"{SCEN_LABELS[scen]}"
                    ),
                )
        ax.set_yscale("log")
        # Headroom above the data, then pin the legend into it. The house
        # style draws legends unframed, so a marker left under the legend
        # strikes through its text: the 40 m bracket triangle at KP 57.4 sat
        # on the last letter of its own legend entry.
        ax.set_ylim(top=ax.get_ylim()[1] * 12.0)
        fs.panel_title(ax, river, scale=scale)
        ax.set_ylabel("Annual system $P_f$ [1/yr]" if j == 0 else "")
        if j == 0:
            key_handles, key_labels = ax.get_legend_handles_labels()

        merged = hist.merge(futu, on="kp", suffixes=("_h", "_f"))
        ratio = np.where(
            merged.p_annual_system_h > 0,
            merged.p_annual_system_f / np.maximum(merged.p_annual_system_h, 1e-300),
            np.nan,
        )
        axr.plot(merged.kp, ratio, ".-", color=INK_2, lw=1.3, ms=4)
        axr.set_yscale("log")
        axr.set_ylabel("+4 K / historical" if j == 0 else "")
        axr.set_xlabel("KP [km]")
    fs.legend_below(fig, key_handles, key_labels, scale=scale, ncol=2)
    fs.title(
        fig,
        "Climate shift of the annual system failure probability, " "all 114 segments",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=2)
    fig.savefig(FIGS / "phase3_climate_shift.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_rq4_four_sections(df: pd.DataFrame) -> None:
    """RQ4 headline: the four characterised sections, historical vs +4K.

    Author decision 5 of the 2026-07-29 campaign scopes RQ3/RQ4 to the four
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

    scale = _scale("rq4")
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(WIDTH_IN["rq4"], 5.4),
        gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.28},
    )

    # --- panel 1: the two annual probabilities, and the BEP share of each ------
    ax = axes[0]
    x = np.arange(len(sections), dtype=float)
    width = 0.34
    headroom = 0.0
    for offset, scenario in ((-width / 2, "historical"), (+width / 2, "+4K")):
        color = SCEN_COLORS[scenario]
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
            label=f"{SCEN_LABELS[scenario]}: system (all mechanisms)",
        )
        ax.bar(
            x + offset,
            np.maximum(bep_part, FLOOR),
            width=width * 0.9,
            color=color,
            lw=0,
            label=f"{SCEN_LABELS[scenario]}: BEP contribution",
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
                fontsize=fs.pt("small", scale),
                color=INK_2,
            )
        headroom = max(headroom, float(band[1].max()))
    ax.set_yscale("log")
    ax.set_xticks(x, labels)
    ax.set_ylabel("annual system $P_f$ [1/yr]")
    fs.panel_title(ax, "Annual system failure probability", scale=scale)
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
    key_handles, key_labels = ax.get_legend_handles_labels()
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
    ax2.set_ylabel("+4 K / historical annual system $P_f$")
    ax2.set_ylim(0, float(ratio_band[1].max()) * 1.18)
    fs.panel_title(ax2, "Climate ratio per section", scale=scale)
    ax2.grid(axis="x", visible=False)
    fs.legend_below(fig, key_handles, key_labels, scale=scale, ncol=3)
    fs.title(
        fig,
        "Annual system failure probability and the climate ratio, "
        "four cross-sections",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=2)
    fig.savefig(FIGS / "phase3_rq4_four_sections.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_attribution(attr: dict) -> None:
    sections = list(attr.keys())
    scale = _scale("attribution")
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN["attribution"], 4.8), sharey=True)
    width = 0.38
    tallest = 0.0
    for ax, scen in zip(axes, ("historical", "+4K")):
        tint = SCEN_COLORS[scen]
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
        fs.panel_title(ax, SCEN_LABELS[scen], scale=scale)
        tallest = max(tallest, max(long_v), max(short_v), max(comp_v))

    axes[0].set_ylim(top=tallest * 2.6)
    axes[0].set_ylabel("Conditional annual $P_f$")
    handles, labels = axes[0].get_legend_handles_labels()
    fs.legend_below(fig, handles, labels, scale=scale)
    fs.title(
        fig,
        "Duration and compound stratification of the annual probability",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=1)
    fig.savefig(FIGS / "phase3_rq4_attribution.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_event_validation(df: pd.DataFrame, val: dict) -> None:
    base = _primary(df)
    scale = _scale("event")
    fig, ax = plt.subplots(figsize=(WIDTH_IN["event"], 6.2))
    # Shape carries the mechanism as a family and the scenario as the member
    # within it, so the mechanism survives greyscale: overflow is round then
    # square, fluvial scour triangular then diamond. Fill still carries
    # whether ten or more events engaged the mechanism.
    markers = {
        "overflow": {"historical": "o", "+4K": "s"},
        "fluvial_scour": {"historical": "^", "+4K": "D"},
    }
    floor_count = 0
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
                if max(event_v, FLOOR) <= FLOOR and max(curve_v, FLOOR) <= FLOOR:
                    floor_count += 1
                # Fewer than ten engaged events is the small-count regime the
                # caption names; an open marker says which comparisons it is
                # rather than leaving the reader to take the caption on trust.
                engaged = int(
                    node[scen].get(
                        "n_overflow_active" if mech == "overflow" else "n_scour_active",
                        0,
                    )
                )
                ax.plot(
                    max(event_v, FLOOR),
                    max(curve_v, FLOOR),
                    markers[mech][scen],
                    color=MECH_COLORS[mech],
                    mfc=MECH_COLORS[mech] if engaged >= 10 else SURFACE,
                    ms=7,
                    mec=MECH_COLORS[mech] if engaged < 10 else SURFACE,
                    mew=1.1 if engaged < 10 else 0.8,
                    zorder=3,
                )
    # The floor row sat exactly on the axis corner, so both of its markers were
    # cut in half by the spines and eighteen scour comparisons rendered as a
    # quarter of one square. The limits now carry a decade of padding below the
    # floor, and the stack says how many results it holds.
    lims = (FLOOR / 4.0, 1.0)
    ax.plot(lims, lims, "-", color=BASELINE, lw=1.0, zorder=0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lims)
    ax.set_ylim(*lims)
    ax.set_xlabel("Event-based annual $P_f$ (full d4PDF ensembles)")
    ax.set_ylabel("Curve-based annual $P_f$ (canonical conditioning)")
    if floor_count:
        ax.annotate(
            f"{floor_count} comparisons\nat the display floor",
            xy=(FLOOR, FLOOR),
            xytext=(14, 10),
            textcoords="offset points",
            fontsize=fs.pt("small", scale),
            color=MUTED,
            ha="left",
            va="bottom",
        )
    # The four combinations are named directly rather than split into two
    # separate keys, so nothing has to be inferred by crossing them.
    handles = [
        plt.Line2D(
            [],
            [],
            marker=markers[m][sc],
            ls="none",
            color=MECH_COLORS[m],
            label=f"{MECH_LABELS[m]}, {SCEN_LABELS[sc]}",
        )
        for m in ("overflow", "fluvial_scour")
        for sc in ("historical", "+4K")
    ] + [
        plt.Line2D(
            [],
            [],
            marker="o",
            ls="none",
            mfc=SURFACE,
            mec=INK_2,
            color=INK_2,
            label="open mark: fewer than ten engaged events",
        )
    ]
    fs.legend_below(fig, handles, [h.get_label() for h in handles], scale=scale, ncol=3)
    fs.title(
        fig,
        "Curve-based against event-based annual probability",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=2)
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
