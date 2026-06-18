"""Throwaway diagnostic: compound-event memory model on a synthetic hydrograph.

Read-only. Runs the M7 scalar timestepper on the synthetic two-peak hydrograph
from the test suite (``_two_peak_event``), extended to a single trace that shows
BOTH gated behaviours the tests check separately:

    peak 1 (3.0 m) -> trough (1.0 m) -> REAL peak 2 (3.0 m) -> trough (1.0 m)
    -> DEAD peak 3 (1.5 m, below the heave threshold)

so growth initiates on peak 1, plateaus through the trough, RESUMES on the real
second peak (uplift latched + heave reactivates), and does NOT resume on the
dead peak (1.5 m < the 2.04 m heave threshold) even though uplift is latched and
l > 0. Parameters are identical to ``test_two_peak_*`` (D_bl = 2.0, gamma'_bl =
10.0, dt = 600 s, etc.).

Four stacked panels on a shared time axis: river stage h(t); pipe length l(t);
the I_er indicator; and both driving heads -- the un-reduced Delta_h_blanket and
the crack-reduced H_erosion = Delta_h_blanket - 0.3*D_bl -- on one panel so the
constant 0.3*D_bl offset is visible. The integrator returns only l(t) and scalar
diagnostics, so the heads and I_er are RECONSTRUCTED read-only from the same M5
kernels (z_uplift, z_heave, erosion_indicator); no module code is changed.

Run: ``python scripts/plot_compound_demo.py``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bep_reliability_engine.constants import GAMMA_W
from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.initiation import erosion_indicator, z_heave, z_uplift
from bep_reliability_engine.progression import (
    CRACK_RESISTANCE_FACTOR,
    integrate_progression,
)

plt.switch_backend("Agg")  # headless: save only, never show

# --- configuration (identical to test_two_peak_* + the shared theta) --------
D_BL_M = 2.0  # blanket thickness -> heave threshold gamma'_bl*D_bl/gamma_w
GAMMA_BL_SUB = 10.0
STEPS = 30  # steps per segment
DT_S = 600.0
C_E = 0.014
K_MPS = 1.0e-4
H_C_M = 5.0
L_C_M = 10.0
L_M = 50.0
THRESHOLD_M = GAMMA_BL_SUB * D_BL_M / GAMMA_W  # 2.039 m (ADR-0008 collapse)

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "results" / "diagnostics"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Single trace: peak1 | trough | REAL peak2 | trough | DEAD peak3 (1.5 m).
    h_river = np.concatenate(
        [
            np.full(STEPS, 3.0),  # peak 1: initiates growth
            np.full(STEPS, 1.0),  # trough: I_er off, plateau
            np.full(STEPS, 3.0),  # real peak 2: heave reactivates, resumes
            np.full(STEPS, 1.0),  # trough: plateau
            np.full(STEPS, 1.5),  # dead peak 3: 1.5 < 2.04 threshold, no resume
        ]
    )
    n = h_river.size
    result = integrate_progression(
        h_river,
        DT_S,
        InstantaneousHead(1.0, 0.0),  # r_e = 1, z_toe = 0
        0.0,
        c_e=C_E,
        k_aq_mps=K_MPS,
        d_bl_m=D_BL_M,
        gamma_bl_sub_knpm3=GAMMA_BL_SUB,
        h_c_m=H_C_M,
        l_c_m=L_C_M,
        seepage_length_m=L_M,
        store_trajectory=True,
    )
    traj = result.l_trajectory_m

    # --- reconstruct the per-step heads and I_er (read-only, M5 kernels) ----
    # r_e = 1 and z_toe = 0, so Delta_h_blanket(t) = h(t).
    delta_h = h_river
    h_erosion = delta_h - CRACK_RESISTANCE_FACTOR * D_BL_M
    uplift_now = z_uplift(delta_h, GAMMA_BL_SUB, D_BL_M) < 0.0
    heave_now = z_heave(delta_h, GAMMA_BL_SUB, D_BL_M) < 0.0
    uplift_ever = np.logical_or.accumulate(uplift_now)
    # l going INTO step k (the value the integrator's I_er sees): l_ini for k=0,
    # else the trajectory after step k-1.
    l_before = np.concatenate([[0.0], traj[:-1]])
    i_er = erosion_indicator(uplift_ever, l_before > 0.0, heave_now)

    # --- time axes (hours); steps are piecewise-constant over [t_k, t_k+dt] --
    t_h = np.arange(n) * DT_S / 3600.0
    t_l = np.arange(n + 1) * DT_S / 3600.0  # l includes l_ini at t = 0
    l_plot = np.concatenate([[0.0], traj])
    seg_h = STEPS * DT_S / 3600.0  # segment width in hours (= 5 h)

    # --- plot --------------------------------------------------------------
    fig, axes = plt.subplots(4, 1, figsize=(11.0, 9.5), sharex=True)
    ax_h, ax_l, ax_ier, ax_head = axes

    # shade the three peaks across all panels: green = clears threshold, red =
    # dead peak (below threshold).
    for ax in axes:
        ax.axvspan(0.0, seg_h, color="tab:green", alpha=0.07)
        ax.axvspan(2 * seg_h, 3 * seg_h, color="tab:green", alpha=0.07)
        ax.axvspan(4 * seg_h, 5 * seg_h, color="tab:red", alpha=0.07)

    # panel 1: river stage
    ax_h.step(t_h, h_river, where="post", color="tab:blue", lw=2)
    ax_h.axhline(THRESHOLD_M, ls="--", color="black", lw=1)
    ax_h.text(
        0.2,
        THRESHOLD_M + 0.1,
        f"heave/uplift threshold gamma'_bl*D_bl/gamma_w = {THRESHOLD_M:.2f} m",
        fontsize=8,
    )
    ax_h.set_ylabel("river stage h [m]")
    ax_h.set_title(
        "Compound-event memory model on the synthetic two-peak hydrograph "
        "(+ a dead third peak)\n[parameters from test_two_peak_*]"
    )
    ax_h.annotate("peak 1", (0.5 * seg_h, 3.0), ha="center", va="bottom", fontsize=8)
    ax_h.annotate(
        "REAL peak 2\n(resumes)",
        (2.5 * seg_h, 3.0),
        ha="center",
        va="bottom",
        fontsize=8,
    )
    ax_h.annotate(
        "DEAD peak 3\n(1.5 < threshold)",
        (4.5 * seg_h, 1.5),
        ha="center",
        va="bottom",
        fontsize=8,
        color="darkred",
    )
    ax_h.set_ylim(0.0, 3.7)

    # panel 2: pipe length
    ax_l.plot(t_l, l_plot, color="tab:blue", lw=2)
    ax_l.set_ylabel("pipe length l [m]")
    ax_l.annotate(
        "grows", (0.5 * seg_h, 0.6), ha="center", fontsize=8, color="darkgreen"
    )
    ax_l.annotate(
        "flat (trough)", (1.5 * seg_h, l_plot[STEPS] + 0.05), ha="center", fontsize=8
    )
    ax_l.annotate(
        "resumes",
        (2.5 * seg_h, l_plot[2 * STEPS] + 0.4),
        ha="center",
        fontsize=8,
        color="darkgreen",
    )
    ax_l.annotate(
        "flat: dead peak, NO resumption\n(uplift latched & l>0, but heave off)",
        (4.5 * seg_h, l_plot[-1] + 0.05),
        ha="center",
        va="bottom",
        fontsize=8,
        color="darkred",
    )
    ax_l.set_ylim(0.0, float(l_plot.max()) * 1.35)

    # panel 3: I_er indicator
    ax_ier.step(t_h, i_er.astype(int), where="post", color="tab:purple", lw=2)
    ax_ier.set_ylabel("I_er")
    ax_ier.set_yticks([0, 1])
    ax_ier.set_yticklabels(["False", "True"])
    ax_ier.set_ylim(-0.2, 1.2)

    # panel 4: the two driving heads, with the constant 0.3*D_bl offset
    ax_head.step(
        t_h,
        delta_h,
        where="post",
        color="tab:blue",
        lw=2,
        label="Delta_h_blanket (un-reduced; -> uplift/heave gate)",
    )
    ax_head.step(
        t_h,
        h_erosion,
        where="post",
        color="tab:orange",
        lw=2,
        label="H_erosion = Delta_h_blanket - 0.3*D_bl (-> rate)",
    )
    # mark the constant offset during peak 1
    x_off = 0.5 * seg_h
    ax_head.annotate(
        "",
        xy=(x_off, 3.0),
        xytext=(x_off, 3.0 - CRACK_RESISTANCE_FACTOR * D_BL_M),
        arrowprops={"arrowstyle": "<->", "color": "black"},
    )
    ax_head.text(
        x_off + 0.3,
        3.0 - CRACK_RESISTANCE_FACTOR * D_BL_M / 2.0,
        f"0.3*D_bl = {CRACK_RESISTANCE_FACTOR * D_BL_M:.1f} m",
        fontsize=8,
        va="center",
    )
    ax_head.set_ylabel("head [m]")
    ax_head.set_xlabel("time [h]")
    ax_head.legend(loc="upper right", fontsize=8)
    ax_head.set_ylim(0.0, 3.7)

    fig.tight_layout()
    out = OUT_DIR / "compound_demo.png"
    fig.savefig(out, dpi=130)

    # --- console summary (sanity, mirrors the test assertions) -------------
    grew_peak2 = bool(traj[2 * STEPS] - traj[2 * STEPS - 1] > 0)  # within real p2
    grew_deadpeak = bool(traj[-1] - traj[4 * STEPS - 1] > 0)
    print(
        f"compound demo: l_final={float(result.l_final_m):.3f} m, "
        f"t_uh={float(result.t_uh_s):.0f} s, resumes_on_real_peak2={grew_peak2}, "
        f"grows_on_dead_peak={grew_deadpeak}"
    )
    print(f"saved {out}")


if __name__ == "__main__":
    main()
