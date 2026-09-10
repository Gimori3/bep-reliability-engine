"""Presentation figures for Phase 1 fragility results (thin driver, no physics).

Reads persisted :class:`~bep_reliability_engine.fragility.FragilityResult`
files (HDF5 + JSON sidecar, spec §8) from ``results/`` and renders three
figures to ``results/figures/`` and the tracked ``docs/figures/``:

1. ``fragility_per_section.png`` — static vs transient per cross-section
   (raw MC points with 95% Clopper-Pearson CIs + the fitted lognormal
   deliverable, ADR-0024), conditioning water level [m MSL] vs P(failure|h),
   with the landside toe, the 2019 design HWL, and — at KP 62.0 — the
   hypothetical fit-stabilizer grid extension marked.
2. ``fragility_comparison.png`` — all sections overlaid per branch on the
   common load-excess axis h - z_toe (the fit datum, ADR-0024).
3. ``fragility_tail_log.png`` — the same per-section data on a log
   probability axis (tail behaviour and per-level static/transient ratios).

Usage (repo root, venv active)::

    python scripts/plot_fragility_curves.py

The KP 63.4 exclusion is recorded in the thesis captions: the section is
unconfined with no A_c blanket (k_bl undefined in the geotech table), so the
confined-blanket BEP model does not apply (generate_configs.py, provenance
3.1/3.5) — a data/mechanism gap, not an oversight.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bep_reliability_engine.fragility import FragilityResult, LognormFragility

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as fs  # noqa: E402

RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
#: Tracked publication copy. ``results/`` is gitignored, so a figure that
#: lives only there is not a deliverable; both copies are written in one
#: call so no manual copy step can let them diverge.
PUB_FIGURES_DIR = REPO_ROOT / "docs" / "figures"


def save_both(fig, name: str) -> None:
    """Write the study-local copy and the tracked publication copy."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PUB_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / name, dpi=200, bbox_inches="tight")
    fig.savefig(PUB_FIGURES_DIR / name, dpi=200, bbox_inches="tight")


SECTIONS = ["57.4", "58.8", "60.0", "62.0"]

#: Authored width of every figure in this driver, and the ``width=`` fraction
#: of ``\textwidth`` it is placed at, so the house type scale can be derived.
FIGURE_WIDTH_IN = 12.6
SCALE = fs.scale_for(FIGURE_WIDTH_IN, 1.0)

#: Top of the physically attainable stage range, per section (ADR-0024). The
#: shaded grid extension starts here. Read from the recorded value rather than
#: from ``HWL + 4.0``: the two differ by 0.11 m at KP 62.0, which put a tenth of
#: a metre of attainable stage inside the hypothetical band and disagreed with
#: the caption's own figure of 50.5 m.
ATTAINABLE_MAX_M = {"57.4": 43.25, "58.8": 42.75, "60.0": 44.25, "62.0": 50.5}

# Reference palette (validated project set; light mode).
BLUE = "#2a78d6"  # slot 1 - static branch / section 1
AQUA = "#1baf7a"  # slot 2 - section 2
YELLOW = "#eda100"  # slot 3 - section 3
GREEN = "#008300"  # slot 4 - section 4
RED = "#e34948"  # slot 6 - transient branch
SECTION_COLORS = {"57.4": BLUE, "58.8": AQUA, "60.0": YELLOW, "62.0": GREEN}

INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

KP634_NOTE = (
    "KP 63.4 excluded by design: unconfined section, no A$_c$ blanket "
    "(k$_\\mathrm{bl}$ not determined there), so the confined-blanket BEP model "
    "(uplift/heave gate) does not apply."
)


def style() -> None:
    """The house rcParams at this driver's printed-type scale."""
    fs.style(SCALE)


def load_all() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for kp in SECTIONS:
        path = RESULTS_DIR / f"tokachi_kp{kp}_historical_matrix.h5"
        result = FragilityResult.load(path)
        sidecar = json.loads(path.with_suffix(".json").read_text())
        geometry = sidecar["config"]["geometry"]
        out[kp] = {
            "result": result,
            "sidecar": sidecar,
            "z_toe": float(geometry["z_toe"]),
            "hwl": float(geometry["HWL"]),
            "remediation": sidecar["remediation_state"],
            "event": sidecar["hydrograph"]["shape_event_id"],
        }
    return out


def fit_curve(
    fit: LognormFragility | None, grid: np.ndarray
) -> tuple[np.ndarray, np.ndarray] | None:
    if fit is None:
        return None
    h = np.linspace(grid.min(), grid.max(), 400)
    return h, np.asarray(fit.probability_of_failure(h))


def draw_branch(ax, grid, raw, ci, fit, color, marker, label) -> None:
    lo, hi = ci
    curve = fit_curve(fit, grid)
    if curve is not None:
        ax.plot(*curve, color=color, lw=2.0, label=label, zorder=3)
    ax.errorbar(
        grid,
        raw,
        yerr=[raw - lo, hi - raw],
        fmt=marker,
        color=color,
        markersize=4.0,
        markeredgecolor=SURFACE,
        markeredgewidth=0.5,
        elinewidth=1.0,
        capsize=1.8,
        capthick=1.0,
        linestyle="none",
        zorder=4,
    )


def annotate_levels(
    ax,
    z_toe: float,
    hwl: float,
    y_text: float = 0.55,
    *,
    hwl_y_axes: float | None = None,
) -> None:
    ax.axvline(z_toe, color=MUTED, lw=1.1, ls=(0, (4, 2, 1, 2)), zorder=2)
    ax.axvline(hwl, color=INK_2, lw=1.1, ls=(0, (5, 3)), zorder=2)
    ax.annotate(
        "toe",
        xy=(z_toe, y_text),
        xytext=(3, 0),
        textcoords="offset points",
        color=MUTED,
        fontsize=fs.pt("annotation", SCALE),
        rotation=90,
        va="center",
    )
    ax.annotate(
        "HWL",
        xy=(hwl, y_text if hwl_y_axes is None else hwl_y_axes),
        xycoords="data" if hwl_y_axes is None else ("data", "axes fraction"),
        xytext=(3, 0),
        textcoords="offset points",
        color=INK_2,
        fontsize=fs.pt("annotation", SCALE),
        rotation=90,
        va="center" if hwl_y_axes is None else "top",
    )


def figure_per_section(data: dict[str, dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(FIGURE_WIDTH_IN, 8.2), sharey=True)
    for ax, kp in zip(axes.ravel(), SECTIONS):
        d = data[kp]
        r = d["result"]
        grid = r.conditioning_grid
        draw_branch(
            ax,
            grid,
            r.P_f_static_raw,
            r.binomial_ci["static"],
            r.P_f_static_fit,
            BLUE,
            "o",
            "Static (Sellmeijer 2011)",
        )
        draw_branch(
            ax,
            grid,
            r.P_f_trans_raw,
            r.binomial_ci["transient"],
            r.P_f_trans_fit,
            RED,
            "D",
            "Transient (Pol 2024 ODE)",
        )
        annotate_levels(ax, d["z_toe"], d["hwl"])
        if kp == "62.0":
            attainable_top = ATTAINABLE_MAX_M[kp]
            ax.axvspan(attainable_top, grid.max(), color=GRID, alpha=0.55, zorder=1)
            # Centred on the band it names, so the note reads as the band's
            # label rather than as an annotation of the curve beside it.
            ax.annotate(
                "fit-stabilizer levels\n(above max attainable stage)",
                xy=(0.5 * (attainable_top + grid.max()), 0.42),
                xycoords=("data", "axes fraction"),
                ha="center",
                va="center",
                color=INK_2,
                fontsize=fs.pt("annotation", SCALE),
            )
        fs.panel_title(ax, f"KP {kp}  ·  {d['remediation']}", scale=SCALE)
        ax.set_ylim(-0.03, 1.03)
        ax.set_xlabel("conditioning water level h  [m T.P.]")
    for ax in axes[:, 0]:
        ax.set_ylabel("P(failure | h)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fs.legend_below(fig, handles, labels, scale=SCALE)
    fs.title(
        fig,
        "Prior fragility at the four cross-sections",
        scale=SCALE,
    )
    fs.layout(fig, scale=SCALE, legend_rows=1)
    save_both(fig, "fragility_per_section.png")
    plt.close(fig)


def figure_comparison(data: dict[str, dict]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH_IN, 5.6), sharey=True)
    titles = {
        "static": "Static limit state, raw gross head",
        "transient": "Transient limit state, raw erosion head",
    }
    for ax, branch in zip(axes, ("static", "transient")):
        for kp in SECTIONS:
            d = data[kp]
            r = d["result"]
            grid = r.conditioning_grid - d["z_toe"]
            raw = r.P_f_static_raw if branch == "static" else r.P_f_trans_raw
            fit = r.P_f_static_fit if branch == "static" else r.P_f_trans_fit
            color = SECTION_COLORS[kp]
            curve = fit_curve(fit, r.conditioning_grid)
            if curve is not None:
                ax.plot(curve[0] - d["z_toe"], curve[1], color=color, lw=2.0)
            ax.plot(
                grid,
                raw,
                "o",
                color=color,
                markersize=3.2,
                markeredgecolor=SURFACE,
                markeredgewidth=0.4,
                alpha=0.85,
                linestyle="none",
            )
        fs.panel_title(ax, titles[branch], scale=SCALE)
        ax.set_xlabel("water level above landside toe  h − z$_\\mathrm{toe}$  [m]")
        ax.set_xlim(0.0, 8.0)
        ax.set_ylim(-0.03, 1.03)
    axes[0].set_ylabel("P(failure | h)")
    handles = [
        plt.Line2D(
            [],
            [],
            color=SECTION_COLORS[kp],
            lw=2.0,
            marker="o",
            markersize=4,
            markeredgecolor=SURFACE,
            label=f"KP {kp}",
        )
        for kp in SECTIONS
    ]
    fs.legend_below(fig, handles, [h.get_label() for h in handles], scale=SCALE)
    fs.title(
        fig,
        "The four cross-sections on a common load-excess axis",
        scale=SCALE,
    )
    fs.layout(fig, scale=SCALE, legend_rows=1)
    save_both(fig, "fragility_comparison.png")
    plt.close(fig)


def figure_tail_log(data: dict[str, dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(FIGURE_WIDTH_IN, 7.28), sharey=True)
    floor = 1.0 / 100000  # N = 1e5: one failure in the sample
    for ax, kp in zip(axes.ravel(), SECTIONS):
        d = data[kp]
        r = d["result"]
        grid = r.conditioning_grid
        for raw, ci, fit, color, marker, label in (
            (
                r.P_f_static_raw,
                r.binomial_ci["static"],
                r.P_f_static_fit,
                BLUE,
                "o",
                "Static (Sellmeijer 2011)",
            ),
            (
                r.P_f_trans_raw,
                r.binomial_ci["transient"],
                r.P_f_trans_fit,
                RED,
                "D",
                "Transient (Pol 2024 ODE)",
            ),
        ):
            curve = fit_curve(fit, grid)
            if curve is not None:
                ax.plot(*curve, color=color, lw=1.8, label=label, zorder=3)
            lo, hi = ci
            shown = raw > 0
            ax.errorbar(
                grid[shown],
                raw[shown],
                yerr=[(raw - np.maximum(lo, floor / 10))[shown], (hi - raw)[shown]],
                fmt=marker,
                color=color,
                markersize=3.8,
                markeredgecolor=SURFACE,
                markeredgewidth=0.5,
                elinewidth=0.9,
                capsize=1.6,
                linestyle="none",
                zorder=4,
            )
        annotate_levels(
            ax,
            d["z_toe"],
            d["hwl"],
            y_text=0.02,
            hwl_y_axes=0.985 if kp in ("57.4", "62.0") else None,
        )
        if kp == "62.0":
            # The same grid extension the per-section view shades. It is a fit
            # stabilizer, never attainable loading, and the two views of one
            # section must not disagree about which stages are reachable.
            attainable_top = ATTAINABLE_MAX_M[kp]
            ax.axvspan(attainable_top, grid.max(), color=GRID, alpha=0.55, zorder=1)
            # Centred on the band it names, so the caption sits wholly inside
            # the shading rather than straddling its left edge.
            ax.annotate(
                "fit-stabilizer levels\n(above max\nattainable stage)",
                xy=(0.5 * (attainable_top + grid.max()), 0.06),
                xycoords=("data", "axes fraction"),
                ha="center",
                color=INK_2,
                fontsize=fs.pt("annotation", SCALE),
            )
        ax.set_yscale("log")
        ax.set_ylim(floor / 2, 1.5)
        fs.panel_title(ax, f"KP {kp}  ·  {d['remediation']}", scale=SCALE)
        ax.set_xlabel("conditioning water level h  [m T.P.]")
    for ax in axes[:, 0]:
        ax.set_ylabel("P(failure | h)   [log]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fs.legend_below(fig, handles, labels, scale=SCALE)
    fs.title(
        fig,
        "The fragility tails on a logarithmic axis",
        scale=SCALE,
    )
    fs.layout(fig, scale=SCALE, legend_rows=1)
    save_both(fig, "fragility_tail_log.png")
    plt.close(fig)


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data = load_all()
    figure_per_section(data)
    figure_comparison(data)
    figure_tail_log(data)
    for name in (
        "fragility_per_section.png",
        "fragility_comparison.png",
        "fragility_tail_log.png",
    ):
        print(f"wrote {FIGURES_DIR / name} (+ docs/figures/{name})")


if __name__ == "__main__":
    main()
