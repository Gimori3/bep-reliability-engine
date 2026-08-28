"""Initiation fragility alongside the two piping branches (thin driver).

Renders ``initiation_fragility.png``: per cross-section, the conditional
probability that the uplift-plus-heave gate opens, drawn against the static
and transient piping branches on the same realization set and the same
conditioning grid.

The initiation probability is not a separate simulation. Under the Terzaghi
collapse (ADR-0008) the gate is open at the peak of a conditioning event
exactly where

    r_e * (h - z_toe)  >  (gamma'_bl / gamma_w) * D_bl

so it is a closed-form function of three retained theta columns and the
per-realization response factor r_e, evaluated on the persisted Phase 1
matrices. ``r_e`` is stage-independent, so the response factors recorded by
the Phase 2 replay pair row for row with the Phase 1 sample and are reused
here rather than recomputed. The identity is checked against the replay's own
stored initiation flags at the observed 2016 peak before anything is drawn,
and the driver refuses if a single row disagrees.

Inputs (persisted production artifacts, no re-run):

* ``results/tokachi_kp<kp>_historical_<reading>.h5`` (theta matrix, both
  failure matrices, conditioning grid) and its JSON sidecar (toe elevation,
  design high water level);
* ``results/phase2/tokachi_kp<kp>_historical_<reading>_posterior.h5``
  (``r_e`` and the stored initiation flags for the verification gate).

Usage (repo root, venv active)::

    python scripts/plot_initiation_fragility.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as figstyle  # noqa: E402

from bep_reliability_engine.constants import GAMMA_W  # noqa: E402

RESULTS_DIR = REPO_ROOT / "results"
PHASE2_DIR = RESULTS_DIR / "phase2"
FIGURES_DIR = RESULTS_DIR / "figures"

SECTIONS = ("57.4", "58.8", "60.0", "62.0")

#: Highest stage the loading can physically reach at each section. Every panel
#: is clipped here, so no part of this figure can be read as a hypothetical
#: above-crest level (ADR-0024).
ATTAINABLE_MAX_M = {"57.4": 43.25, "58.8": 42.75, "60.0": 44.25, "62.0": 50.5}

#: The gate keeps its own hue, distinct from the two limit-state colours that
#: are fixed for the whole thesis. Validated all-pairs against the static and
#: transient slots on the light surface.
INITIATION = figstyle.VIOLET


def load_section(kp: str, reading: str) -> dict:
    """Assemble one section's curves from the persisted artifacts."""
    with h5py.File(RESULTS_DIR / f"tokachi_kp{kp}_historical_{reading}.h5", "r") as f:
        names = [n.decode() if isinstance(n, bytes) else n for n in f["param_names"][:]]
        theta = f["theta_matrix"][:]
        grid = f["conditioning_grid"][:]
        p_static = f["failure_matrix_static"][:].mean(axis=0)
        p_trans = f["failure_matrix_trans"][:].mean(axis=0)

    meta = json.loads(
        (RESULTS_DIR / f"tokachi_kp{kp}_historical_{reading}.json").read_text()
    )
    geometry = meta["config"]["geometry"]

    posterior = PHASE2_DIR / f"tokachi_kp{kp}_historical_{reading}_posterior.h5"
    with h5py.File(posterior, "r") as f:
        event = next(iter(f["events"]))
        r_e = f[f"events/{event}/r_e"][:]
        stored_initiation = f[f"events/{event}/initiation"][:]
    peak_2016 = json.loads(posterior.with_suffix(".json").read_text())["phase2"][
        "event_chain"
    ][0]["record"]["peak_m_msl"]

    z_toe = float(geometry["z_toe"])
    threshold = (theta[:, names.index("gamma_bl_sub")] / GAMMA_W) * theta[
        :, names.index("D_bl")
    ]

    # Verification gate: the closed form must reproduce the replay's own flags
    # at the observed peak, row for row, before any curve is drawn.
    recomputed = r_e * (peak_2016 - z_toe) > threshold
    disagreeing = int(np.count_nonzero(recomputed != stored_initiation))
    if disagreeing:
        raise SystemExit(
            f"KP {kp} ({reading}): the closed-form gate disagrees with the "
            f"replay on {disagreeing} of {recomputed.size} realizations; the "
            "figure would not describe the production engine."
        )

    p_initiation = (r_e[:, None] * (grid[None, :] - z_toe) > threshold[:, None]).mean(
        axis=0
    )

    return {
        "kp": kp,
        "grid": grid,
        "p_initiation": p_initiation,
        "p_static": p_static,
        "p_trans": p_trans,
        "z_toe": z_toe,
        "hwl": float(geometry["HWL"]),
        "peak_2016": float(peak_2016),
    }


def draw(sections: list[dict], reading: str) -> plt.Figure:
    """Render the two-by-two small-multiple panel."""
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 5.2), sharey=True)

    for ax, data in zip(axes.ravel(), sections):
        kp = data["kp"]
        top = ATTAINABLE_MAX_M[kp]
        keep = data["grid"] <= top + 1e-9
        stage = data["grid"][keep]

        ax.axvline(data["hwl"], color=figstyle.MUTED, lw=1.0, ls=(0, (4, 2)))
        ax.axvline(data["peak_2016"], color=figstyle.INK_2, lw=1.0, ls=(0, (1, 1.6)))
        ax.plot(
            stage,
            data["p_initiation"][keep],
            color=INITIATION,
            lw=2.0,
            label="uplift and heave",
        )
        ax.plot(
            stage,
            data["p_static"][keep],
            color=figstyle.STATIC,
            lw=2.0,
            label="static piping",
        )
        ax.plot(
            stage,
            data["p_trans"][keep],
            color=figstyle.TRANSIENT,
            lw=2.0,
            label="transient piping",
        )

        ax.set_title(f"KP {kp}", loc="left", fontsize=11)
        ax.set_xlim(max(data["z_toe"], stage[0]), top)
        ax.set_ylim(-0.03, 1.03)

    for ax in axes[1]:
        ax.set_xlabel("conditioning water level h  [m MSL]")
    for ax in axes[:, 0]:
        ax.set_ylabel("conditional probability")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    handles += [
        plt.Line2D([], [], color=figstyle.MUTED, lw=1.0, ls=(0, (4, 2))),
        plt.Line2D([], [], color=figstyle.INK_2, lw=1.0, ls=(0, (1, 1.6))),
    ]
    labels += ["design level", "2016 peak"]
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=5,
        bbox_to_anchor=(0.5, -0.035),
        columnspacing=1.6,
        handlelength=1.9,
    )
    fig.suptitle(
        "The three sub-mechanism probabilities on one realization set",
        fontsize=12,
        fontweight="bold",
        color=figstyle.INK,
        x=0.012,
        y=0.995,
        ha="left",
    )
    fig.text(
        0.012,
        -0.055,
        f"Historical scenario, {reading} d$_{{70}}$ reading, N = 10$^5$; "
        "every panel stops at the highest attainable stage.",
        fontsize=8,
        color=figstyle.MUTED,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    return fig


def main() -> None:
    """Render the figure for the production grain-size reading."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reading", default="matrix", choices=["matrix", "bulk"])
    args = parser.parse_args()

    figstyle.style()
    sections = [load_section(kp, args.reading) for kp in SECTIONS]
    figure = draw(sections, args.reading)
    out = figstyle.save(figure, "initiation_fragility.png", mirror=FIGURES_DIR)

    for data in sections:
        top = ATTAINABLE_MAX_M[data["kp"]]
        keep = data["grid"] <= top + 1e-9
        saturated = data["grid"][keep][data["p_initiation"][keep] >= 0.999]
        first = float(saturated[0]) if saturated.size else float("nan")
        print(
            f"KP {data['kp']}: gate reaches 0.999 at {first:.2f} m MSL, "
            f"{data['hwl'] - first:+.2f} m relative to the design level"
        )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
