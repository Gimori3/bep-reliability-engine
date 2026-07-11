"""Figure for the Shikaga (Case A) validation note.

Reads ``results/validation_shikaga/validation_results.json`` and writes
``docs/figures/validation_shikaga_m4_pattern.png``: the cross-case M4
over-translation pattern (engine instantaneous Mazure vs committee/paper 2D
FEM peak toe overpressure) with the Tokachi production sections' expected
position.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "validation_shikaga" / "validation_results.json"
FIG_DIR = REPO / "docs" / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"

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


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    results = json.loads(RESULTS.read_text())
    m4 = results["m4_factor_grid"]
    shik = sorted(
        r["m4_factor"] for r in m4 if r["L_m"] == 40.0 and r["z_exit_m"] == 24.5
    )

    rows = [
        ("Yabe R11.86k\nthick Dg, channel-connected", (1.13, 1.13), "anchored"),
        ("Shikaga L28.75k\nUs-g(+Usg), sheeted slope", (shik[0], shik[-1]), "anchored"),
        ("Yabe R7.3k\nthin dead-ended As", (1.97, 1.97), "anchored"),
        ("Yabe L16.10k\nDg under fan levee", (2.67, 2.67), "z_toe read-off uncertain"),
    ]

    fig, ax = plt.subplots(figsize=(7.4, 3.0), dpi=160)
    ax.axvline(1.0, color=INK, lw=1.2, ls=(0, (6, 3)))
    ax.axvspan(1.0, 1.15, color="#008300", alpha=0.10, lw=0)
    for i, (label, (lo, hi), conf) in enumerate(rows):
        y = len(rows) - 1 - i
        open_marker = "uncertain" in conf
        if hi > lo:
            ax.plot([lo, hi], [y, y], color=BLUE, lw=5.5, solid_capstyle="round")
            ax.plot((lo + hi) / 2, y, "o", ms=8, mfc=SURFACE, mec=BLUE, mew=2)
            txt = f"{lo:.2f}-{hi:.2f}"
        else:
            ax.plot(
                lo, y, "o", ms=9, mfc=SURFACE if open_marker else BLUE, mec=BLUE, mew=2
            )
            txt = f"{lo:.2f}" + ("  (datum uncertain)" if open_marker else "")
        ax.text(hi + 0.09, y, txt, color=INK2, fontsize=8, va="center")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=8, color=INK2)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(0.8, 3.2)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(
        "M4 factor: engine instantaneous Mazure / 2D-FEM peak toe " "overpressure  [-]"
    )
    ax.annotate(
        "expected Tokachi position\n(saturated, channel-connected,\n"
        "10x the 11.86k transmissivity)",
        xy=(1.08, 3.28),
        xytext=(1.35, 3.05),
        color="#006300",
        fontsize=8,
        arrowprops={"arrowstyle": "-", "color": BASELINE, "lw": 0.8},
    )
    ax.set_title(
        "M4 over-translation vs calibrated FEMs across the Japanese cases",
        fontsize=9.5,
        color=INK,
        loc="left",
        pad=10,
    )
    out = FIG_DIR / "validation_shikaga_m4_pattern.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
