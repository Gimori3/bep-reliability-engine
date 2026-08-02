"""Throwaway diagnostic: S2-2 (L = 3 m DgFlow) shape-gate visual confirmation.

Read-only. Runs the M7 scalar timestepper on the S2-2 in-domain configuration
(note docs/decisions/m7-pol-ode-reference-values.md §5D; ADR-0009) and overlays
the simulated l(t) on the digitized DgFlow trajectory. Saves a two-panel figure
to results/diagnostics/ (gitignored).

This is the visual companion to ``test_s2_2_in_domain_shape_and_rate``. The shape
gate operates on the NORMALIZED curve (right panel) -- that is where "our
progressive-phase curvature tracks DgFlow" is legible. The left panel shows the
absolute l(t), where the ~1.95x progressive-phase over-prediction (the Eq. (11)
H_eq conservatism, ADR-0009) makes M7 breach ~2x sooner than DgFlow; that is
documented expected behaviour, not a defect.

Run: ``python scripts/plot_s2_2.py``
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.progression import integrate_progression

plt.switch_backend("Agg")  # headless: save only, never show

# --- S2-2 configuration (note §5D) ------------------------------------------
L_M = 3.0  # seepage length
H_C_M = 0.143  # critical head (Fig. 10 caption)
H_M = 0.157  # constant imposed head (~10% overload)
C_E = 0.08  # DgFlow / regression value
L_C_M = 1.36  # DgFlow critical length (Fig. 5.9); anchors H_eq peak
K_MPS = 2.158e-4  # S2-2 sand k
DT_S = 10.0
DGFLOW_RATE_MPS = 7.08e-5  # Table A.5 published average dl/dt over [L/2, L]

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "data" / "digitized"
OUT_DIR = REPO / "results" / "diagnostics"


def _normalized_growth_curve(
    t: np.ndarray, l_series: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize (t, l) to [0, 1] x [0, 1] over the growth span (note §5D)."""
    growth = np.flatnonzero(np.diff(l_series) > 0.0)
    t0, t1 = t[growth[0]], t[growth[-1] + 1]
    span = (t >= t0) & (t <= t1)
    t_n = (t[span] - t0) / (t1 - t0)
    l_n = (l_series[span] - l_series[span][0]) / (
        l_series[span][-1] - l_series[span][0]
    )
    return t_n, l_n


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- run the scalar timestepper at constant head -----------------------
    # t_max long enough to cover DgFlow's later breach (~9 h) on one axis.
    t = np.arange(0.0, 35000.0, DT_S)
    result = integrate_progression(
        np.full(t.size, H_M),
        DT_S,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=C_E,
        k_aq_mps=K_MPS,
        d_bl_m=0.0,
        gamma_bl_sub_knpm3=10.0,
        h_c_m=H_C_M,
        l_c_m=L_C_M,
        seepage_length_m=L_M,
        store_trajectory=True,
    )
    sim = result.l_trajectory_m

    # --- digitized DgFlow trajectory (running-max cleaned, note §5C) --------
    dg = np.loadtxt(DATA_DIR / "L3m_S2-2_pipelength_l-t.csv", delimiter=",", skiprows=1)
    t_dg, l_dg = dg[:, 0], np.maximum.accumulate(dg[:, 1])

    # --- metrics, computed live (should match note §5D) --------------------
    sn_t, sn_l = _normalized_growth_curve(t, sim)
    dn_t, dn_l = _normalized_growth_curve(t_dg, l_dg)
    grid = np.linspace(0.0, 1.0, 200)
    sim_n = np.interp(grid, sn_t, sn_l)
    dg_n = np.interp(grid, dn_t, dn_l)
    shape_rms = float(np.sqrt(np.mean((sim_n - dg_n) ** 2)))
    shape_max = float(np.max(np.abs(sim_n - dg_n)))
    t_half = t[int(np.argmax(sim >= L_M / 2.0))]
    t_breach = t[int(np.argmax(sim >= L_M * 0.999))]
    rate = (L_M - L_M / 2.0) / (t_breach - t_half)

    # --- plot --------------------------------------------------------------
    fig, (ax_abs, ax_shape) = plt.subplots(1, 2, figsize=(13.0, 5.2))

    # left: absolute l(t)
    ax_abs.plot(
        t / 3600.0, sim, "-", color="tab:blue", lw=2, label="M7 sim (Eq.5+Eq.11)"
    )
    ax_abs.plot(
        t_dg / 3600.0,
        l_dg,
        "o",
        color="black",
        ms=3,
        label="DgFlow digitized (CG24 Fig.10)",
    )
    ax_abs.axhline(L_C_M, ls="--", color="tab:green", lw=1)
    ax_abs.text(8.5, L_C_M + 0.04, f"l_c = {L_C_M} m", color="tab:green", fontsize=8)
    ax_abs.axhline(L_M, ls="--", color="tab:red", lw=1)
    ax_abs.text(8.5, L_M - 0.13, f"L = {L_M} m (breach)", color="tab:red", fontsize=8)
    ax_abs.set_xlabel("time [h]")
    ax_abs.set_ylabel("pipe length l [m]")
    ax_abs.set_title(
        "Absolute l(t): M7 breaches ~2x sooner\n(Eq.11 H_eq conservatism, ADR-0009)"
    )
    ax_abs.legend(loc="center right", fontsize=8)
    ax_abs.annotate(
        f"integrated [L/2,L] rate = {rate:.3e} m/s\n"
        f"= {rate / DGFLOW_RATE_MPS:.2f}x DgFlow {DGFLOW_RATE_MPS:.2e} (ADR-0009)",
        xy=(0.03, 0.97),
        xycoords="axes fraction",
        va="top",
        fontsize=8,
        bbox={"boxstyle": "round", "fc": "lightyellow", "ec": "grey"},
    )

    # right: normalized shape (the gated quantity)
    ax_shape.plot(grid, sim_n, "-", color="tab:blue", lw=2, label="M7 sim (normalized)")
    ax_shape.plot(grid, dg_n, "--", color="black", lw=1.5, label="DgFlow (normalized)")
    ax_shape.plot([0, 1], [0, 1], ":", color="grey", lw=1, label="constant-rate ref")
    ax_shape.set_xlabel("normalized time  (t - t0) / (t1 - t0)")
    ax_shape.set_ylabel("normalized length")
    ax_shape.set_title(
        "Normalized SHAPE -- the gated quantity\n"
        "(progressive-phase curvature tracks DgFlow)"
    )
    ax_shape.legend(loc="lower right", fontsize=8)
    verdict = "PASS" if shape_max <= 0.10 else "FAIL"
    ax_shape.annotate(
        f"shape RMS = {shape_rms:.3f}\n"
        f"max dev = {shape_max:.3f}  (gate <= 0.10)  {verdict}",
        xy=(0.03, 0.97),
        xycoords="axes fraction",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round", "fc": "honeydew", "ec": "green"},
    )

    fig.suptitle(
        "S2-2 (L=3m DgFlow) in-domain shape gate  [test_s2_2_in_domain_shape_and_rate]",
        fontsize=11,
    )
    fig.tight_layout()
    out = OUT_DIR / "s2_2_shape.png"
    fig.savefig(out, dpi=130)
    print(
        f"S2-2: shape RMS={shape_rms:.4f} max={shape_max:.4f}  "
        f"rate={rate:.4e} ({rate / DGFLOW_RATE_MPS:.2f}x DgFlow)"
    )
    print(f"saved {out}")


if __name__ == "__main__":
    main()
