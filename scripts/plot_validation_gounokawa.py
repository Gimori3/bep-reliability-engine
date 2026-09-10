"""Figures for the Gounokawa Shimohara validation note.

Reads ``results/validation_gounokawa/validation_results.json`` (produced by
``scripts/validate_gounokawa_shimohara.py``) plus the Waseda Fig. 5 workbook,
and writes two PNGs to ``docs/figures/``:

1. ``validation_gounokawa_hydrograph_2018.png`` — the 2018 site-stage record
   with the observed onset window/stage band, the hybrid-schematization
   predicted onset band, and the 1999 no-ejecta bound.
2. ``validation_gounokawa_onset_intervals.png`` — predicted onset-head
   (dH over hinterland ground) intervals per schematization vs the observed
   bands, for L = 150 m and L = 75 m.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import _figstyle as fs
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from validate_gounokawa_shimohara import EVENT_T0, load_event  # noqa: E402

RESULTS = REPO / "results" / "validation_gounokawa" / "validation_results.json"
FIG_DIR = REPO / "docs" / "figures"

# Reference palette (project set, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SLOT = {  # fixed categorical order; color follows the entity
    "framework_gravel": "#2a78d6",
    "single_soil_sand": "#1baf7a",
    "composite": "#eda100",
    "hybrid_gravel_pressure": "#008300",
}
LABEL = {
    "framework_gravel": "framework gravel",
    "single_soil_sand": "single-soil sand",
    "composite": "composite",
    "hybrid_gravel_pressure": "hybrid: gravel hydraulics,\nsand resistance and erosion",
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 9,
        "text.color": INK,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK2,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def fig_hydrograph(results: dict) -> None:
    rec = load_event(2018)
    t0 = EVENT_T0[2018]
    times = [t0 + dt.timedelta(seconds=float(s)) for s in np.asarray(rec.t)]
    h = np.asarray(rec.h)

    hyb = next(
        r
        for r in results["tier2"]
        if r["schematization"] == "hybrid_gravel_pressure" and r["L_m"] == 150.0
    )
    q05, _, q50, _, q95 = hyb["onset_stage_q05_25_50_75_95_m"]
    obs_lo, obs_hi = results["observed"]["onset_site_stage_band_m"]
    pre2018 = results["observed"]["pre2018_max_site_stage_m"]
    z_toe = 12.9

    scale = fs.scale_for(9.8, 1.0)
    fs.style(scale)
    fig, ax = plt.subplots(figsize=(9.8, 5.8), dpi=160)
    ax.plot(times, h, color=fs.BLUE, lw=2.0, solid_capstyle="round", label="site stage")

    # observed onset: stage band + eyewitness time window
    ax.axhspan(
        obs_lo, obs_hi, color=INK, alpha=0.10, lw=0, label="observed onset stage"
    )
    w0 = dt.datetime(2018, 7, 7, 5, 30)
    w1 = dt.datetime(2018, 7, 7, 5, 54)
    ax.axvspan(w0, w1, color=INK, alpha=0.18, lw=0, label="eyewitness time window")

    # predicted onset band (hybrid schematization, L = 150 m)
    ax.axhspan(
        q05,
        q95,
        color=fs.GREEN,
        alpha=0.12,
        lw=0,
        label="predicted 5th to 95th percentile",
    )
    ax.axhline(
        q50, color=fs.GREEN, lw=1.6, ls=(0, (6, 3)), label="predicted median (hybrid)"
    )

    # 1999 no-ejecta bound and ground level
    ax.axhline(
        pre2018, color=MUTED, lw=1.0, ls=(0, (2, 3)), label="1999 no-ejecta maximum"
    )
    ax.axhline(z_toe, color=BASELINE, lw=1.0, label="hinterland ground")

    ax.set_ylabel("site stage [m T.P.]")
    fs.title(fig, "Stage and sand-boil onset at Gounokawa Shimohara", scale=scale)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_ylim(4, 22.5)
    ax.grid(axis="x", visible=False)
    handles, labels = ax.get_legend_handles_labels()
    fs.legend_below(fig, handles, labels, scale=scale, ncol=3)
    fs.layout(fig, scale=scale, legend_rows=3)
    out = FIG_DIR / "validation_gounokawa_hydrograph_2018.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_onset_intervals(results: dict) -> None:
    obs_g = results["observed"]["onset_dh_ground_band_m"]
    obs_p = results["observed"]["onset_dh_paper_band_m"]
    bound = results["observed"]["pre2018_no_ejecta_dh_bound_m"]
    order = list(SLOT)
    scale = fs.scale_for(10.2, 1.0)
    fs.style(scale)

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(10.2, 7.0),
        dpi=160,
        sharex=True,
    )
    for ax, L in zip(axes, (150.0, 75.0)):
        rows = {r["schematization"]: r for r in results["tier2"] if r["L_m"] == L}
        ax.axvspan(*obs_g, color=INK, alpha=0.13, lw=0, label="observed: ground datum")
        ax.axvspan(*obs_p, color=INK, alpha=0.06, lw=0, label="observed: paper datum")
        ax.axvline(bound, color=MUTED, lw=1.0, ls=(0, (2, 3)))
        for i, name in enumerate(order):
            r = rows[name]
            y = len(order) - 1 - i
            c = SLOT[name]
            q05, q25, q50, q75, q95 = [
                v - 12.9 + 0.0 for v in r["onset_stage_q05_25_50_75_95_m"]
            ]
            ax.plot([q05, q95], [y, y], color=c, lw=2.0, solid_capstyle="round")
            ax.plot([q25, q75], [y, y], color=c, lw=5.5, solid_capstyle="round")
            ax.plot(q50, y, "o", ms=8, mfc=SURFACE, mec=c, mew=2.0)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([LABEL[n] for n in reversed(order)], color=INK2)
        ax.set_ylim(-1.0, len(order) - 0.4)
        ax.grid(axis="y", visible=False)
        fs.panel_title(ax, f"$L = {L:.0f}$ m", scale=scale)

    axes[1].annotate(
        "1999 no-ejecta bound (4.2 m)",
        xy=(bound, 0),
        xycoords=axes[1].get_xaxis_transform(),
        xytext=(9.0, -0.52),
        textcoords="data",
        va="center",
        arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 1.0},
        color=MUTED,
        fontsize=fs.pt("annotation", scale),
        zorder=6,
    )
    # One line ran off the canvas and lost its closing bracket.
    axes[1].set_xlabel(r"predicted onset head over hinterland ground, $\Delta h$ [m]")
    axes[1].set_xlim(0, 24)
    handles, labels = axes[0].get_legend_handles_labels()
    handles += [
        plt.Line2D([], [], color=INK2, lw=2),
        plt.Line2D([], [], color=INK2, lw=5.5),
        plt.Line2D([], [], color=INK2, marker="o", mfc=SURFACE, ls="none"),
    ]
    labels += ["5th to 95th percentile", "25th to 75th percentile", "median"]
    fs.legend_below(fig, handles, labels, scale=scale, ncol=3)
    fs.title(fig, "Predicted sand-boil onset by aquifer schematization", scale=scale)
    fs.layout(fig, scale=scale, legend_rows=2)
    out = FIG_DIR / "validation_gounokawa_onset_intervals.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    results = json.loads(RESULTS.read_text())
    fig_hydrograph(results)
    fig_onset_intervals(results)


if __name__ == "__main__":
    main()
