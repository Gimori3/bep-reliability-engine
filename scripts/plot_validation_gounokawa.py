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
    "hybrid_gravel_pressure": "hybrid (gravel M4 / sand M6-M7)",
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

    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=160)
    ax.plot(times, h, color="#2a78d6", lw=2.0, solid_capstyle="round")

    # observed onset: stage band + eyewitness time window
    ax.axhspan(obs_lo, obs_hi, color="#0b0b0b", alpha=0.10, lw=0)
    ax.text(
        times[10],
        obs_hi + 0.25,
        "observed onset stage 19.5-19.9",
        color=INK2,
        fontsize=8,
    )
    w0 = dt.datetime(2018, 7, 7, 5, 30)
    w1 = dt.datetime(2018, 7, 7, 5, 54)
    ax.axvspan(w0, w1, color="#0b0b0b", alpha=0.18, lw=0)
    ax.annotate(
        "eyewitness window\n05:30-05:54",
        xy=(w1, 13.6),
        xytext=(dt.datetime(2018, 7, 7, 14), 13.4),
        color=INK2,
        fontsize=8,
        arrowprops={"arrowstyle": "-", "color": BASELINE, "lw": 0.8},
    )

    # predicted onset band (hybrid schematization, L = 150 m)
    ax.axhspan(q05, q95, color="#008300", alpha=0.12, lw=0)
    ax.axhline(q50, color="#008300", lw=1.6, ls=(0, (6, 3)))
    ax.text(
        times[10],
        q50 + 0.22,
        f"predicted onset (hybrid): median {q50:.1f}, 5-95% " f"{q05:.1f}-{q95:.1f}",
        color="#006300",
        fontsize=8,
    )

    # 1999 no-ejecta bound and ground level
    ax.axhline(pre2018, color=MUTED, lw=1.0, ls=(0, (2, 3)))
    ax.text(
        times[10],
        pre2018 + 0.2,
        "largest pre-2018 stage (1999) - no ejecta ever observed",
        color=MUTED,
        fontsize=8,
    )
    ax.axhline(z_toe, color=BASELINE, lw=1.0)
    ax.text(times[10], z_toe + 0.2, "hinterland ground 12.9", color=MUTED, fontsize=8)

    ax.set_ylabel("site stage [m T.P.]")
    ax.set_title(
        "Gounokawa Shimohara, July 2018: site stage vs observed and "
        "predicted sand-boil onset",
        fontsize=9.5,
        color=INK,
        loc="left",
        pad=10,
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_ylim(4, 22.5)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    out = FIG_DIR / "validation_gounokawa_hydrograph_2018.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_onset_intervals(results: dict) -> None:
    obs_g = results["observed"]["onset_dh_ground_band_m"]
    obs_p = results["observed"]["onset_dh_paper_band_m"]
    bound = results["observed"]["pre2018_no_ejecta_dh_bound_m"]
    order = list(SLOT)

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(7.4, 4.2),
        dpi=160,
        sharex=True,
        gridspec_kw={"hspace": 0.35},
    )
    for ax, L in zip(axes, (150.0, 75.0)):
        rows = {r["schematization"]: r for r in results["tier2"] if r["L_m"] == L}
        ax.axvspan(*obs_g, color="#0b0b0b", alpha=0.13, lw=0)
        ax.axvspan(*obs_p, color="#0b0b0b", alpha=0.06, lw=0)
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
        ax.set_yticklabels(
            [LABEL[n] for n in reversed(order)], fontsize=8.5, color=INK2
        )
        ax.set_ylim(-0.6, len(order) - 0.4)
        ax.grid(axis="y", visible=False)
        ax.set_title(f"L = {L:.0f} m", fontsize=9, color=INK2, loc="left")

    axes[0].annotate(
        "observed 2018 onset\n(6.6-7.0 over ground;\n6.2-6.6 paper datum)",
        xy=(obs_g[0], 3.4),
        xytext=(8.6, 2.6),
        color=INK2,
        fontsize=8,
        arrowprops={"arrowstyle": "-", "color": BASELINE, "lw": 0.8},
    )
    axes[1].text(0.5, -0.5, "1999 no-ejecta bound (4.2 m)", color=MUTED, fontsize=8)
    axes[1].set_xlabel(
        "predicted onset head over hinterland ground, dH [m]  "
        "(5-95% whisker, 25-75% bar, median dot)"
    )
    axes[1].set_xlim(0, 24)
    fig.suptitle(
        "Predicted sand-boil onset head by aquifer schematization vs "
        "observation (2018 virgin state)",
        fontsize=9.5,
        color=INK,
        x=0.02,
        ha="left",
    )
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
