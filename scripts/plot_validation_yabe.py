"""Figures for the Yabe validation note.

Reads ``results/validation_yabe/validation_results.json`` and writes two
PNGs to ``docs/figures/``:

1. ``validation_yabe_timeline.png`` — forced-clock time-to-breach and
   time-to-l_c distributions at R7.3k (primary anchor A2) across the
   committee's As-permeability case ladder, vs the observed 6.33 h
   initiation-to-breach interval.
2. ``validation_yabe_discrimination.png`` — per-site transient breach
   probability and static exceedance probability vs observed outcomes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "validation_yabe" / "validation_results.json"
FIG_DIR = REPO / "docs" / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"
AQUA = "#1baf7a"
YELLOW = "#eda100"

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

K_LABEL = {
    3.4e-4: "central k (case 2/4)\n3.4e-4 m/s",
    1.0e-3: "intermediate\n1.0e-3 m/s",
    3.1e-3: "coarse trench-As (case 3/5)\n3.1e-3 m/s",
}
K_COLOR = {3.4e-4: BLUE, 1.0e-3: AQUA, 3.1e-3: YELLOW}


def fig_timeline(results: dict) -> None:
    rows = [r for r in results["timeline_test"] if r["anchor"].startswith("A2")]
    obs = rows[0]["observed_interval_h"]

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(7.4, 4.4),
        dpi=160,
        sharex=True,
        gridspec_kw={"hspace": 0.45},
    )
    # The reported probability is that the endpoint is ever reached over the
    # whole simulated window, which is not the probability of reaching it
    # inside the observed interval; the label names the endpoint so the two
    # cannot be read for each other.
    panels = [
        ("full", "time to l ≥ L (modeled breach)", "P(l ≥ L)"),
        ("lc", "time to l ≥ l_c (point of no return)", "P(l ≥ l_c)"),
    ]
    ks = [3.4e-4, 1.0e-3, 3.1e-3]
    for ax, (lab, title, reach_label) in zip(axes, panels):
        ax.axvline(obs, color=INK, lw=1.4, ls=(0, (6, 3)))
        for i, k in enumerate(ks):
            r = next(x for x in rows if abs(x["k_aq_mean"] - k) < 1e-9)
            q = r.get(f"t_{lab}_q05_25_50_75_95_h")
            p = r.get(f"p_reached_{lab}", 0.0)
            y = len(ks) - 1 - i
            c = K_COLOR[k]
            if q:
                q05, q25, q50, q75, q95 = q
                ax.plot([q05, q95], [y, y], color=c, lw=2.0, solid_capstyle="round")
                ax.plot([q25, q75], [y, y], color=c, lw=5.5, solid_capstyle="round")
                ax.plot(q50, y, "o", ms=8, mfc=SURFACE, mec=c, mew=2.0)
            ax.text(
                13.55,
                y,
                f"{reach_label} = {p:.2f}",
                color=INK2,
                fontsize=8,
                va="center",
            )
        ax.set_yticks(range(len(ks)))
        ax.set_yticklabels([K_LABEL[k] for k in reversed(ks)], fontsize=8, color=INK2)
        ax.set_ylim(-0.6, len(ks) - 0.4)
        ax.set_xlim(0, 16.5)
        ax.grid(axis="y", visible=False)
        ax.set_title(title, fontsize=9, color=INK2, loc="left")
    axes[0].annotate(
        "observed: initiation (07:00)\n→ breach (13:20) = 6.3 h",
        xy=(obs, 2.55),
        xytext=(7.6, 2.35),
        color=INK,
        fontsize=8,
        arrowprops={"arrowstyle": "-", "color": BASELINE, "lw": 0.8},
    )
    axes[1].set_xlabel(
        "hours after forced initiation at anchor A2 "
        "(whisker 5 to 95, bar 25 to 75 per cent, median dot)"
    )
    fig.suptitle(
        "Yabe R7.3k forced-clock timeline test: Pol progression vs the "
        "observed breach interval",
        fontsize=9.5,
        color=INK,
        x=0.02,
        ha="left",
    )
    out = FIG_DIR / "validation_yabe_timeline.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_discrimination(results: dict) -> None:
    rows = results["discrimination"]
    order = ["R7.3k", "R11.86k", "L16.10k"]
    outcome = {
        "R7.3k": "BREACHED 13:20",
        "R11.86k": "boils + toe settlement",
        "L16.10k": "boils only",
    }
    floor = 5e-6  # plotting floor for P = 0 (0 failures / 100k)

    fig, ax = plt.subplots(figsize=(7.4, 2.9), dpi=160)
    for i, s in enumerate(order):
        r = next(x for x in rows if x["site"] == s)
        y = len(order) - 1 - i
        pt = max(r["p_breach_transient"], floor)
        ps = max(r["p_static_exceeded"], floor)
        ax.plot(pt, y + 0.12, "o", ms=9, mfc=BLUE, mec=SURFACE, mew=1.5, clip_on=False)
        ax.plot(
            ps, y - 0.12, "s", ms=8, mfc=YELLOW, mec=SURFACE, mew=1.5, clip_on=False
        )
        t_lab = (
            "0 / 100k"
            if r["p_breach_transient"] == 0
            else f"{r['p_breach_transient']:.2g}"
        )
        ax.text(pt * 1.6, y + 0.12, t_lab, color=INK2, fontsize=8, va="center")
        ax.text(
            ps * 1.6,
            y - 0.12,
            f"{r['p_static_exceeded']:.2g}",
            color=INK2,
            fontsize=8,
            va="center",
        )
        ax.text(1.6e-6, y + 0.30, outcome[s], color=MUTED, fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(1.5e-6, 3)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(list(reversed(order)), fontsize=9, color=INK2)
    ax.set_ylim(-0.6, len(order) - 0.2)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("probability under the site prior (N = 10⁵ LHS)")
    ax.plot([], [], "o", ms=8, mfc=BLUE, mec=SURFACE, label="P(transient breach)")
    ax.plot([], [], "s", ms=7, mfc=YELLOW, mec=SURFACE, label="P(static H_c exceeded)")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.02), frameon=False, fontsize=8)
    ax.set_title(
        "Yabe 2012 three-site discrimination: transient race condition vs "
        "static comparator",
        fontsize=9.5,
        color=INK,
        loc="left",
        pad=10,
    )
    out = FIG_DIR / "validation_yabe_discrimination.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    results = json.loads(RESULTS.read_text())
    fig_timeline(results)
    fig_discrimination(results)


if __name__ == "__main__":
    main()
