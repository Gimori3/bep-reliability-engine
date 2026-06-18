"""Throwaway diagnostic: B25-245 qualitative-gate visual confirmation.

Read-only. Runs the M7 scalar timestepper on the B25-245 configuration
(note docs/decisions/m7-pol-ode-reference-values.md §4) and overlays the
simulated l(t) on the digitized measured curve. Saves to results/diagnostics/
(gitignored).

B25-245 (L = 0.352 m) is OUT OF DOMAIN for the Eq. (5) regression (fitted
0.9-90 m), so its progressive-phase magnitude is deliberately NOT gated. The
plot is built so the passing behaviour is legible and does not read as a
failure: it shades the regressive-phase tracking window (+/-0.18*L) and draws
the no-overshoot bound (meas + 0.15*L) that the qualitative gate actually
checks, and annotates that the magnitude under-prediction (~0.36x measured,
non-breaching) is expected out-of-domain behaviour, not a defect (note §4,
ADR-0009).

Run: ``python scripts/plot_b25_245.py``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.progression import integrate_progression

plt.switch_backend("Agg")  # headless: save only, never show

# --- B25-245 configuration (note §4) ----------------------------------------
L_M = 0.352  # seepage length
H_C_M = 0.054  # corrected critical head H_c,corr
L_C_M = 0.197  # measured critical pipe length (anchors H_eq peak)
C_E = 0.010  # calibrated C_e (Fig. caption 0.014 is an FPH copy-paste)
K_MPS = 3.1e-4
DT_S = 5.0
MEASURED_VCAVG_MPS = 6.14e-5  # Table 3.2 post-critical average rate
OVERSHOOT_MAX_FRAC = 0.15  # gate: no overshoot beyond this * L
REGRESSIVE_ENVELOPE_FRAC = 0.18  # gate: regressive tracking within this * L

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "data" / "digitized"
OUT_DIR = REPO / "results" / "diagnostics"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- cleaned, time-varying head BC (note §5C) --------------------------
    raw = np.loadtxt(DATA_DIR / "B25-245_head-BC_Hcorr.csv", delimiter=",", skiprows=1)
    t_raw, h_raw = raw[:, 0], raw[:, 1]
    keep = ~((t_raw > 1000.0) & (h_raw < 0.03))  # drop curve-crossing artifact
    t = np.arange(0.0, t_raw[-1] + DT_S, DT_S)
    h_grid = np.interp(t, t_raw[keep], h_raw[keep])

    result = integrate_progression(
        h_grid,
        DT_S,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=C_E,
        k_aq_mps=K_MPS,
        d_bl_m=0.0,
        gamma_bl_sub_knpm3=9.7,
        h_c_m=H_C_M,
        l_c_m=L_C_M,
        seepage_length_m=L_M,
        store_trajectory=True,
    )
    sim = result.l_trajectory_m

    # --- digitized measured pipe length ------------------------------------
    exp = np.loadtxt(
        DATA_DIR / "B25-245_pipelength_l-exp.csv", delimiter=",", skiprows=1
    )
    t_exp, l_exp = exp[:, 0], exp[:, 1]

    # --- gate quantities, computed live ------------------------------------
    t_c = t[int(np.argmax(sim >= L_C_M))]  # sim crosses l_c -> progressive
    sim_at_exp = np.interp(t_exp, t, sim)
    overshoot = sim_at_exp - l_exp
    max_overshoot_frac = float(overshoot.max() / L_M)
    regressive = t_exp <= t_c
    reg_dev_frac = float(np.max(np.abs(overshoot[regressive])) / L_M)
    # post-critical end-to-end rate and its ratio to the measured v_c,avg
    growth = np.flatnonzero(np.diff(sim) > 0.0)
    last = int(growth[-1]) + 1
    post_rate = (float(sim[last]) - L_C_M) / (t[last] - t_c)
    rate_ratio = post_rate / MEASURED_VCAVG_MPS
    l_final = float(sim[-1])

    meas_on_grid = np.interp(t, t_exp, l_exp)  # for the bands

    # --- plot --------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11.0, 6.2))
    tk = t / 1000.0  # kiloseconds
    tk_c = t_c / 1000.0

    # phase backdrops
    ax.axvspan(0.0, tk_c, color="tab:green", alpha=0.06)
    ax.axvspan(tk_c, tk[-1], color="grey", alpha=0.06)
    ax.text(
        tk_c / 2.0,
        0.345,
        "regressive\n(shape gated)",
        ha="center",
        va="top",
        fontsize=8,
        color="darkgreen",
    )
    ax.text(
        (tk_c + tk[-1]) / 2.0,
        0.345,
        "progressive\n(magnitude NOT gated -- out of domain)",
        ha="center",
        va="top",
        fontsize=8,
        color="dimgrey",
    )

    # gated regressive tracking window (+/- 0.18 L around measured)
    reg = tk <= tk_c
    ax.fill_between(
        tk[reg],
        meas_on_grid[reg] - REGRESSIVE_ENVELOPE_FRAC * L_M,
        meas_on_grid[reg] + REGRESSIVE_ENVELOPE_FRAC * L_M,
        color="tab:green",
        alpha=0.18,
        label=f"regressive tracking window (+/-{REGRESSIVE_ENVELOPE_FRAC}*L, GATED)",
    )
    # gated no-overshoot bound (measured + 0.15 L)
    ax.plot(
        tk,
        meas_on_grid + OVERSHOOT_MAX_FRAC * L_M,
        ":",
        color="tab:orange",
        lw=1.5,
        label=f"no-overshoot bound (meas + {OVERSHOOT_MAX_FRAC}*L, GATED)",
    )

    # the curves
    ax.plot(tk, sim, "-", color="tab:blue", lw=2, label="M7 sim (Eq.5+Eq.11)")
    ax.plot(t_exp / 1000.0, l_exp, "o", color="black", ms=4, label="measured l_exp")

    # l_c and L markers
    ax.axhline(L_C_M, ls="--", color="tab:green", lw=1)
    ax.text(
        0.1, L_C_M + 0.004, f"l_c = {L_C_M} m (measured)", color="tab:green", fontsize=8
    )
    ax.axhline(L_M, ls="--", color="tab:red", lw=1)
    ax.text(0.1, L_M - 0.012, f"L = {L_M} m (breach)", color="tab:red", fontsize=8)
    ax.axvline(tk_c, color="black", lw=0.8, alpha=0.4)

    ax.set_xlabel("time [10^3 s]")
    ax.set_ylabel("pipe length l [m]")
    ax.set_ylim(0.0, 0.37)
    ax.set_title(
        "B25-245 qualitative gate  [test_b25_245_qualitative_shape_and_behavior]"
    )
    ax.legend(loc="center right", fontsize=8)

    ax.annotate(
        "Out-of-domain (L = 0.352 m < 0.9-90 m fitted).\n"
        f"Magnitude under-predicts: post-critical {rate_ratio:.2f}x measured;\n"
        f"non-breaching, stalls at {l_final:.2f} m.  EXPECTED, not a defect\n"
        "(note §4, ADR-0009). What IS gated (and passing): entry to\n"
        f"progressive phase, monotone + staircase, regressive tracking\n"
        f"{reg_dev_frac:.2f}*L <= {REGRESSIVE_ENVELOPE_FRAC}*L, no overshoot "
        f"{max_overshoot_frac:.2f}*L <= {OVERSHOOT_MAX_FRAC}*L,\n"
        "breach-threshold C_e bracket, C_e-rate monotonicity.",
        xy=(0.015, 0.015),
        xycoords="axes fraction",
        va="bottom",
        ha="left",
        fontsize=8,
        bbox={"boxstyle": "round", "fc": "lightyellow", "ec": "grey"},
    )

    fig.tight_layout()
    out = OUT_DIR / "b25_245_qualitative.png"
    fig.savefig(out, dpi=130)
    print(
        f"B25-245: post-critical {rate_ratio:.2f}x measured, l_final={l_final:.3f} m, "
        f"reg_dev={reg_dev_frac:.2f}*L, max_overshoot={max_overshoot_frac:.2f}*L"
    )
    print(f"saved {out}")


if __name__ == "__main__":
    main()
