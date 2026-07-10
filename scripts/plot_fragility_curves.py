"""Presentation figures for Phase 1 fragility results (thin driver, no physics).

Reads persisted :class:`~bep_reliability_engine.fragility.FragilityResult`
files (HDF5 + JSON sidecar, spec §8) from ``results/`` and renders three
figures to ``results/figures/``:

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

The KP 63.4 exclusion note is stamped on the figures: the section is
unconfined with no A_c blanket (k_bl undefined in the geotech table), so the
confined-blanket BEP model does not apply (generate_configs.py, provenance
3.1/3.5) — a data/mechanism gap, not an oversight.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bep_reliability_engine.fragility import FragilityResult, LognormFragility

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

SECTIONS = ["57.4", "58.8", "60.0", "62.0"]

# Reference palette (dataviz guide, validated set; light mode).
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
    "(k$_{bl}$ undefined in the geotech table) — the confined-blanket BEP "
    "model (uplift/heave gate) does not apply."
)


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


def annotate_levels(ax, z_toe: float, hwl: float, y_text: float = 0.55) -> None:
    ax.axvline(z_toe, color=MUTED, lw=1.1, ls=(0, (4, 2, 1, 2)), zorder=2)
    ax.axvline(hwl, color=INK_2, lw=1.1, ls=(0, (5, 3)), zorder=2)
    ax.annotate(
        "toe",
        xy=(z_toe, y_text),
        xytext=(3, 0),
        textcoords="offset points",
        color=MUTED,
        fontsize=8.5,
        rotation=90,
        va="center",
    )
    ax.annotate(
        "HWL",
        xy=(hwl, y_text),
        xytext=(3, 0),
        textcoords="offset points",
        color=INK_2,
        fontsize=8.5,
        rotation=90,
        va="center",
    )


def run_stamp(data: dict[str, dict]) -> str:
    side = data["57.4"]["sidecar"]
    dt_s = (
        side["config"]["timestepper"]["target_dt_seconds"]
        or side["hydrograph"]["native_dt_s"]
    )
    return (
        f"First end-to-end run — historical scenario, matrix d$_{{70}}$, "
        f"N = 10$^5$ LHS (seed {side['lhs_seed']}), canonical d4PDF shape "
        f"{data['57.4']['event']}, Δt = {dt_s:g} s (ADR-0030), "
        f"raw-head conventions (ADR-0027/0028), C$_e$ prior ADR-0026."
    )


def footnote(fig, data: dict[str, dict], extra: str) -> None:
    """Three short stamped lines; wrapped manually so nothing clips."""
    fig.text(
        0.01,
        0.005,
        run_stamp(data) + "\n" + KP634_NOTE + "\n" + extra,
        fontsize=8,
        color=MUTED,
        va="bottom",
    )


def figure_per_section(data: dict[str, dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.2), sharey=True)
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
            attainable_top = d["hwl"] + 4.0
            ax.axvspan(attainable_top, grid.max(), color=GRID, alpha=0.55, zorder=1)
            ax.annotate(
                "fit-stabilizer levels\n(above max attainable stage)",
                xy=(0.985, 0.42),
                xycoords="axes fraction",
                ha="right",
                color=INK_2,
                fontsize=8.5,
            )
        ax.set_title(f"KP {kp}  ·  {d['remediation']}", loc="left")
        ax.set_ylim(-0.03, 1.03)
        ax.set_xlabel("conditioning water level h  [m MSL]")
    for ax in axes[:, 0]:
        ax.set_ylabel("P(failure | h)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.99, 1.0),
        ncols=2,
        fontsize=10,
    )
    fig.suptitle(
        "Backward erosion piping fragility — Tokachi right bank "
        "(static vs transient limit state)",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )
    footnote(
        fig,
        data,
        "Points: raw MC estimates with 95% Clopper–Pearson CIs; "
        "lines: fitted lognormal deliverables (ADR-0024).",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 0.95))
    fig.savefig(FIGURES_DIR / "fragility_per_section.png", dpi=200)
    plt.close(fig)


def figure_comparison(data: dict[str, dict]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.6), sharey=True)
    titles = {
        "static": "Static limit state — Sellmeijer 2011 (raw gross head)",
        "transient": "Transient limit state — Pol 2024 ODE (raw erosion head)",
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
            # Direct label only the well-separated KP 62.0 curve; the three
            # clustered sections are identified by the figure legend (their
            # labels would collide inline).
            if kp == "62.0" and curve is not None:
                idx = int(np.searchsorted(curve[1], 0.70))
                idx = min(idx, curve[0].size - 1)
                ax.annotate(
                    f"KP {kp}",
                    xy=(curve[0][idx] - d["z_toe"], 0.70),
                    xytext=(8, -2),
                    textcoords="offset points",
                    color=color,
                    fontsize=9.5,
                    fontweight="bold",
                )
        ax.set_title(titles[branch], loc="left")
        ax.set_xlabel("water level above landside toe  h − z$_{toe}$  [m]")
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
    fig.legend(
        handles=handles,
        loc="upper right",
        bbox_to_anchor=(0.99, 1.0),
        ncols=4,
        fontsize=10,
    )
    fig.suptitle(
        "Cross-section comparison — load excess above the landside toe",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )
    footnote(
        fig,
        data,
        "KP 62.0 points beyond h − z$_{toe}$ ≈ 5.5 m come from the "
        "hypothetical fit-stabilizer grid extension (unattainable stages).",
    )
    fig.tight_layout(rect=(0, 0.075, 1, 0.94))
    fig.savefig(FIGURES_DIR / "fragility_comparison.png", dpi=200)
    plt.close(fig)


def figure_tail_log(data: dict[str, dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.2), sharey=True)
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
        annotate_levels(ax, d["z_toe"], d["hwl"], y_text=0.02)
        ax.set_yscale("log")
        ax.set_ylim(floor / 2, 1.5)
        ax.set_title(f"KP {kp}  ·  {d['remediation']}", loc="left")
        ax.set_xlabel("conditioning water level h  [m MSL]")
    for ax in axes[:, 0]:
        ax.set_ylabel("P(failure | h)   [log]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.99, 1.0),
        ncols=2,
        fontsize=10,
    )
    fig.suptitle(
        "Tail view — raw MC points, 95% binomial CIs (log scale)",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )
    footnote(
        fig,
        data,
        f"Raw-point floor at 1/N = {floor:.0e}; fitted-curve tails below the "
        "lowest plotted point are extrapolation beyond the MC evidence.",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 0.95))
    fig.savefig(FIGURES_DIR / "fragility_tail_log.png", dpi=200)
    plt.close(fig)


def main() -> None:
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
        print(f"wrote {FIGURES_DIR / name}")


if __name__ == "__main__":
    main()
