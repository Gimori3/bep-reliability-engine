"""Figures for the seepage-length L study (companion to ADR-0033/0037).

Reads the JSON records written by ``scripts/seepage_length_study.py`` and draws
three figures into ``docs/figures/``:

* ``seepage_length_marginal.png``  — transient P_f(stage) under the CoV(L) ladder,
  one panel per section, with the deterministic-L and one-sided-upward references.
* ``seepage_length_marginal_ratio.png`` — shoulder vs design-level P_f ratio to the
  production CoV 0.20, versus CoV, all four sections (where the CoV bites).
* ``seepage_length_system_and_ceiling.png`` — the length-effect-at-system bound
  (reach union vs lambda_ac) and the Phase 2 L-borne ceiling (prior vs posterior
  L marginal and theta shifts).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
REC = REPO / "results" / "sensitivity" / "seepage_length"
FIG = REPO / "docs" / "figures"

# Colour-blind-safe ladder (Wong-style), deterministic to CoV 0.40.
COV_KEYS = ["det", "cov0.10", "cov0.15", "cov0.20", "cov0.30", "cov0.40"]
COV_LABEL = {
    "det": "deterministic",
    "cov0.10": "CoV 0.10",
    "cov0.15": "CoV 0.15 (KP60.0 prod.)",
    "cov0.20": "CoV 0.20 (production)",
    "cov0.30": "CoV 0.30",
    "cov0.40": "CoV 0.40",
}
COV_COLOR = {
    "det": "#999999",
    "cov0.10": "#56B4E9",
    "cov0.15": "#009E73",
    "cov0.20": "#000000",
    "cov0.30": "#E69F00",
    "cov0.40": "#D55E00",
}
COV_VAL = {
    "cov0.10": 0.10,
    "cov0.15": 0.15,
    "cov0.20": 0.20,
    "cov0.30": 0.30,
    "cov0.40": 0.40,
}


def fig_marginal() -> None:
    d = json.loads((REC / "marginal_sensitivity.json").read_text())
    secs = d["sections"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.2), sharex=False)
    for ax, (label, s) in zip(axes.ravel(), secs.items()):
        grid = np.array(s["grid_m_msl"])
        cur = s["curves"]
        for key in COV_KEYS:
            tr = np.array(cur[key]["transient"])
            ax.plot(
                grid,
                tr,
                color=COV_COLOR[key],
                lw=2.2 if key == "cov0.20" else 1.5,
                ls="--" if key == "det" else "-",
                label=COV_LABEL[key],
            )
        # one-sided-upward reference (mean +15%), thin dotted
        up = np.array(cur["lognormal_meanplus15pct"]["transient"])
        ax.plot(
            grid, up, color="#CC79A7", lw=1.4, ls=":", label="mean +15% (one-sided)"
        )
        ax.set_title(f"{label}  (L = {s['L_mean_m']:g} m)", fontsize=11)
        ax.set_ylabel("transient $P_f$")
        ax.set_xlabel("river stage [m MSL]")
        ax.set_ylim(-0.02, 1.02)
        ax.grid(alpha=0.25)
        # zoom the shoulder where the CoV bites: mark the 0.05-0.4 band
        base = np.array(cur["cov0.20"]["transient"])
        sh = grid[int(np.argmin(np.abs(base - 0.05)))]
        ax.axvline(sh, color="#888888", lw=0.8, alpha=0.6)
    axes.ravel()[0].legend(fontsize=7.5, loc="upper left", framealpha=0.9)
    fig.suptitle(
        "Transient fragility under the seepage-length CoV(L) ladder\n"
        "(shoulder is the CoV-sensitive regime; grey line marks $P_f\\approx0.05$)",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = FIG / "seepage_length_marginal.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


def fig_marginal_ratio() -> None:
    d = json.loads((REC / "marginal_sensitivity.json").read_text())
    secs = d["sections"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    covs = [0.10, 0.15, 0.20, 0.30, 0.40]
    markers = {"KP57.4": "o", "KP58.8": "s", "KP60.0": "^", "KP62.0": "D"}
    for label, s in secs.items():
        cur = s["curves"]
        base = np.array(cur["cov0.20"]["transient"])
        ish = int(np.argmin(np.abs(base - 0.05)))
        idz = int(np.argmin(np.abs(base - 0.30)))
        for ax, i, ttl in (
            (axes[0], ish, "shoulder ($P_f\\approx0.05$)"),
            (axes[1], idz, "design ($P_f\\approx0.30$)"),
        ):
            ratios = [
                np.array(cur[f"cov{c:.2f}"]["transient"])[i] / base[i] for c in covs
            ]
            ax.plot(covs, ratios, marker=markers[label], label=label, lw=1.6)
            ax.set_title(f"transient $P_f$ ratio at the {ttl}")
    for ax in axes:
        ax.axhline(1.0, color="#000000", lw=0.8, alpha=0.4)
        ax.axvline(0.20, color="#000000", lw=0.8, ls=":", alpha=0.5)
        ax.set_xlabel("CoV(L)")
        ax.set_ylabel("$P_f(\\mathrm{CoV})\\,/\\,P_f(0.20)$")
        ax.grid(alpha=0.25)
    axes[0].legend(fontsize=9)
    fig.suptitle(
        "Sensitivity of transient $P_f$ to CoV(L): steep at the shoulder, "
        "flat at design level",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = FIG / "seepage_length_marginal_ratio.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


def fig_system_and_ceiling() -> None:
    sysd = json.loads((REC / "system_correlation.json").read_text())
    ceil = json.loads((REC / "phase2_ceiling.json").read_text())
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))

    # Panel A: independence over-count ratio vs lambda_ac.
    ax = axes[0]
    lam = np.linspace(20, 400, 200)
    ratio = lam / sysd["segment_spacing_m"]
    ax.plot(lam, ratio, color="#0072B2", lw=2)
    ax.axhline(1.0, color="#000000", lw=0.8, alpha=0.5)
    for name, lval in (("40 m", 40), ("100 m", 100), ("250 m", 250)):
        ax.plot([lval], [lval / 200.0], "o", color="#D55E00")
        ax.annotate(
            name,
            (lval, lval / 200.0),
            textcoords="offset points",
            xytext=(4, 6),
            fontsize=8,
        )
    ax.fill_between(lam, 0, 1, color="#D55E00", alpha=0.07)
    ax.fill_between(lam, 1, ratio.max(), color="#009E73", alpha=0.07)
    ax.set_xlabel("$\\lambda_{ac}$ [m]")
    ax.set_ylabel("independence over-count = $\\lambda_{ac}/200$")
    ax.set_title("Reach-scale length effect\n(>1 conservative, <1 under-counts)")
    ax.grid(alpha=0.25)

    # Panel B: production 4-node reach union — independent vs comonotone.
    ax = axes[1]
    b = sysd["reach_union_bounds_from_rq4"]
    keys = [k for k in ("historical/posterior", "+4K/posterior") if k in b]
    x = np.arange(len(keys))
    ind = [b[k]["reach_union_independent"] for k in keys]
    com = [b[k]["reach_union_comonotone"] for k in keys]
    ax.bar(x - 0.18, ind, 0.36, label="independent (production)", color="#009E73")
    ax.bar(x + 0.18, com, 0.36, label="comonotone (full corr.)", color="#0072B2")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([k.split("/")[0] for k in keys])
    ax.set_ylabel("annual BEP reach union")
    ax.set_title(
        "Production 4-section BEP reach union\n"
        "(1.2-2.0 km apart: bounds within ~1.4-1.7x)"
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, axis="y")

    # Panel C: Phase 2 ceiling — prior vs posterior L marginal & theta shifts.
    ax = axes[2]
    labels = list(ceil["sections"].keys())
    params = ["L", "k_aq", "C_e", "D_bl", "d_70"]
    width = 0.8 / len(labels)
    for j, lab in enumerate(labels):
        s = ceil["sections"][lab]
        shifts = [s["L_mean_change_pct"]] + [
            s["theta_marginal_shift"][p]["mean_change_pct"] for p in params[1:]
        ]
        ax.bar(np.arange(len(params)) + j * width, shifts, width, label=lab)
    ax.axhline(0, color="#000000", lw=0.8)
    ax.set_xticks(np.arange(len(params)) + width * (len(labels) - 1) / 2)
    ax.set_xticklabels(params)
    ax.set_ylabel("posterior mean shift [%]")
    ax.set_title(
        "Phase 2: 2016 survival barely moves L\n"
        "(filters $\\theta$, not the geometric L)"
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, axis="y")

    fig.suptitle(
        "Seepage length L at the system level (left, centre) and the "
        "Phase 2 ceiling (right)",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = FIG / "seepage_length_system_and_ceiling.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("wrote", out)


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of redrawing the figures.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    FIG.mkdir(parents=True, exist_ok=True)
    fig_marginal()
    fig_marginal_ratio()
    fig_system_and_ceiling()


if __name__ == "__main__":
    main()
