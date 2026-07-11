"""Case-study validation 3 (Case A): Gounokawa Shikaga L28.75k - M4/M5 separation.

Validates the M4 hydraulic-translation kernel against the calibrated 2D
saturated-unsaturated FEM of Sako, Kurata, Mori et al. (2019), JSCE Journal
B1 (Hydraulic Engineering) 75(1), 279-290 (open access, J-STAGE; local copy
`docs/references/sako_2019_gounokawa_75_279.pdf`): the Gounokawa left-bank
Shikaga district, 28.75k, July 2018 flood - sand boils in the hinterland
paddies and at the landside toe (replacement gravel ejected with Ums sand),
berm cracks; **no breach**.

PRE-REGISTERED PURPOSE (2026-07-11 user steer)
----------------------------------------------
This case is the instrument that separates "M4 over-translates" from "M5
under-resists" in the Gounokawa/Yabe conservatism budget, and the input to a
production-exposure judgment for the Tokachi sweep:

* **M4 factor**: engine peak toe overpressure r_e*(peak - z_exit) vs the FEM
  triplet's Delta_h = i_v * D_Ums at the same observed load (i_v = 0.91,
  G/W = 0.99 at the hinterland surface; the shown FEM case applies no
  interior-water forcing, so the exit datum is the dry ground).
* **M5 check with FEM-true heads**: at the moment boils were observed the
  FEM says i_v = 0.91 vs the Terzaghi weight-only critical gradient
  gamma'/gamma_w = (18.4-9.81)/9.81 = 0.876 - a bias ratio of ~0.96. If the
  gate is unbiased when the heads are right, the onset conservatism measured
  at Gounokawa/Yabe re-attributes to M4 (plus site 3D/pond effects).
  Corollary: the Ums lab cohesion (c = 40.8 kPa, Fig. 14b) demonstrably did
  NOT act (boils occurred at G/W ~ 1), consistent with the trench's
  sand-vein/pocket fabric providing cohesionless preferential paths.
* **Cross-case M4 pattern**: Shikaga + the three Yabe FEM comparisons,
  characterized against candidate discriminators (elastic Pi, transmissivity,
  entry/initial-saturation state).
* **Tokachi production exposure**: the same indicators computed for the four
  production configs, an onset-stage shift bound under r_e -> r_e/2, and the
  explicit judgment the user asked for.

VERDICT-CRITICAL choices (flagged): (i) D_Ums = 3.0 m at the FEM evaluation
point (Fig. 10 elevation axis: ~24.3 -> ~21.3) - the FEM Delta_h benchmark is
0.91 * D, linear in this read-off; (ii) exit datum z = 24.5 m (dry hinterland
ground; the shown FEM case has no interior-water forcing; pond 25.0 m
sensitivity); (iii) peak stage 31.23 m T.P. - figure-confirmed (Fig. 11
inset: trace DHWL 31.23, HWL 31.64); (iv) aquifer variant (Us-g only vs
Us-g+Usg composite) - both reported, composite is the baseline because the
paper names BOTH layers as the pressure path (sec. 3(1)).

Inputs (Fig. 14b table unless noted): Ums gamma_t 18.4, k 1.26e-6 m/s,
c 40.8 kPa (inoperative, see above); Us-g k 8.59e-5, D ~6.0 m (READ-OFF);
Usg k 3.1e-4, D ~4.5 m (READ-OFF); d70(Ums/boils) 3.5e-4 m (Fig. 12,
READ-OFF); L = 40 m base width (READ-OFF, 30-50); open entry (riverside
slope is sheeted, entry through the bed into Us-g/Usg). Loading: local
two-peak shape per the paper's own forcing convention (Kawamoto shape
shifted to the trace peak), APPROX control points below; peak exact.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import numpy as np
import yaml

from bep_reliability_engine.constants import GAMMA_W
from bep_reliability_engine.evaluator import evaluate_batch
from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    leakage_length_in,
    leakage_length_out,
    response_factor,
)
from bep_reliability_engine.hydrographs import HydrographRecord, resample_record
from bep_reliability_engine.progression import integrate_progression
from bep_reliability_engine.sampling import MarginalSpec, sample_theta
from bep_reliability_engine.sellmeijer import (
    compute_critical_head_vectorized,
    compute_critical_pipe_length,
)

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "results" / "validation_shikaga"

SEED = 20260713
N_CHAIN = 30_000
TARGET_DT_S = 225.0
COV = {
    "k_aq": 0.50,
    "d_70": 0.30,
    "D_aq": 0.10,
    "D_bl": 0.167,
    "k_bl": 0.50,
    "gamma_bl_sub": 0.056,
}
C_E_MEAN, C_E_COV = 0.055, 0.043 / 0.055

# --- Shikaga 28.75k case constants ---------------------------------------
PEAK_STAGE_M = 31.23  # trace level, Fig. 11 inset (figure-confirmed)
HWL_M = 31.64  # Fig. 11 inset
Z_EXIT_PRIMARY = 24.5  # dry hinterland ground (FEM case shown: no pond)
Z_EXIT_POND = 25.0  # max interior pond (paper sec. 2(2)b)
D_UMS_M = 3.0  # READ-OFF Fig. 10 (~24.3 -> ~21.3)
K_UMS_MPS = 1.26e-6  # Fig. 14b (1.26e-4 cm/s)
GAMMA_T_UMS = 18.4  # Fig. 14b
GAMMA_SUB_UMS = GAMMA_T_UMS - GAMMA_W
D70_M = 3.5e-4  # READ-OFF Fig. 12 (boil-matching Ums family)
L_BASE_M = 40.0  # READ-OFF (30-50 sensitivity)
FEM_IV = 0.91  # Fig. 15(c)/(d), hinterland, observed load
FEM_GW = 0.99
FEM_DH_M = FEM_IV * D_UMS_M  # 2.73 m above the exit datum
TERZAGHI_IC = GAMMA_SUB_UMS / GAMMA_W  # 0.876

AQUIFER_VARIANTS = {
    "us_g_only": {"k_aq": 8.59e-5, "D_aq": 6.0},
    "composite_usg": {  # transmissivity-weighted Us-g (6.0 m) + Usg (4.5 m)
        "k_aq": (8.59e-5 * 6.0 + 3.1e-4 * 4.5) / 10.5,
        "D_aq": 10.5,
    },
}

# Local stage record (m T.P.), APPROX two-peak shape per the paper's forcing
# convention (Kawamoto shape shifted so the peak equals the 31.23 trace);
# hours from 2018-07-05 12:00 JST.
H_CONTROL = [
    (0, 26.0),
    (6, 26.2),
    (12, 27.0),
    (15, 28.5),
    (18, 29.5),
    (21, 29.2),
    (27, 28.4),
    (30, 28.3),
    (33, 28.8),
    (36, 29.8),
    (39, 31.23),
    (42, 31.1),
    (45, 30.9),
    (48, 30.3),
    (54, 29.0),
    (60, 28.0),
    (72, 26.8),
    (84, 26.2),
]

# Cross-case M4 pattern: engine/FEM peak toe-overpressure ratios established
# in the Yabe validation (docs/validation/yabe-case.md sec. 3).
YABE_M4_ROWS = [
    {
        "site": "Yabe R7.3k (thin dead-ended As, floodplain-mediated entry)",
        "factor": 3.65 / 1.85,
        "datum_confidence": "anchored",
    },
    {
        "site": "Yabe R11.86k (thick transmissive Dg, channel-connected)",
        "factor": 2.72 / 2.4,
        "datum_confidence": "anchored",
    },
    {
        "site": "Yabe L16.10k (Dg under fan levee)",
        "factor": 6.94 / 2.6,
        "datum_confidence": "z_toe read-off uncertain",
    },
]

TOKACHI_T_RISE_S = 64_800.0  # ADR-0032: canonical-event 10-90% rise ~18 h
S_EFF_RANGE = (1.0e-2, 1.0e-1)  # effective storativity implied by FEM damping

PARAM_ORDER = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]


def build_record() -> HydrographRecord:
    pts = np.array(H_CONTROL, dtype=np.float64)
    t_h = np.arange(0.0, pts[-1, 0] + 1e-9, 1.0)
    h = np.interp(t_h, pts[:, 0], pts[:, 1])
    rec = HydrographRecord(
        t=t_h * 3600.0,
        h=h,
        peak=float(h.max()),
        duration_hours=float(t_h[-1]),
        scenario="historical",
        event_id="gounokawa_shikaga_2018",
        native_dt=3600.0,
        provenance={
            "source": "Sako et al. 2019 forcing convention "
            "(Kawamoto shape -> trace peak 31.23)",
            "t0_jst": "2018-07-05T12:00",
        },
    )
    return resample_record(rec, TARGET_DT_S)


def m4_factor_grid() -> list[dict]:
    """Engine peak toe overpressure vs the FEM benchmark, mean values."""
    rows = []
    for vname, v in AQUIFER_VARIANTS.items():
        lam_in = float(leakage_length_in(v["k_aq"], v["D_aq"], D_UMS_M, K_UMS_MPS))
        for L in (30.0, 40.0, 50.0):
            for z_exit in (Z_EXIT_PRIMARY, Z_EXIT_POND):
                r_e = float(response_factor(lam_in, 0.0, L))
                dh_engine = r_e * (PEAK_STAGE_M - z_exit)
                rows.append(
                    {
                        "aquifer_variant": vname,
                        "L_m": L,
                        "z_exit_m": z_exit,
                        "lambda_in_m": lam_in,
                        "r_e": r_e,
                        "dh_engine_peak_m": dh_engine,
                        "dh_fem_m": FEM_DH_M,
                        "m4_factor": dh_engine / FEM_DH_M,
                    }
                )
    return rows


def full_chain(rec: HydrographRecord) -> list[dict]:
    """Survival/initiation consistency check (secondary to the M4 goal)."""
    out = []
    for vname, v in AQUIFER_VARIANTS.items():
        means = {
            "k_aq": v["k_aq"],
            "d_70": D70_M,
            "D_aq": v["D_aq"],
            "D_bl": D_UMS_M,
            "k_bl": K_UMS_MPS,
            "gamma_bl_sub": GAMMA_SUB_UMS,
        }
        specs = [
            MarginalSpec(name=n, family="lognormal", mean=means[n], cov=COV[n])
            for n in PARAM_ORDER[:-1]
        ]
        specs.append(
            MarginalSpec(name="C_e", family="lognormal", mean=C_E_MEAN, cov=C_E_COV)
        )
        sample = sample_theta(
            specs,
            seed=SEED,
            rho_log_kaq_d70=0.0,
            d70_interpretation="matrix",
            n_samples=N_CHAIN,
            coupling="two_population",
            bounds={"d_70": (5.0e-5, 1.5e-3)},
        )
        tm = sample.theta_matrix
        geom = {
            "L": L_BASE_M,
            "z_toe": Z_EXIT_PRIMARY,
            "foreshore_width": 0.0,
            "D_fore": D_UMS_M,
            "k_fore": K_UMS_MPS,
        }
        k_aq = sample.column("k_aq")
        d_aq = sample.column("D_aq")
        d_bl = sample.column("D_bl")
        k_bl = sample.column("k_bl")
        gamma_bl = sample.column("gamma_bl_sub")
        c_e = sample.column("C_e")
        lam = leakage_length_in(k_aq, d_aq, d_bl, k_bl)
        r_e = response_factor(lam, 0.0, L_BASE_M)
        h_c = np.asarray(compute_critical_head_vectorized(tm, geom).H_c)
        l_c = np.asarray(compute_critical_pipe_length(d_aq, L_BASE_M))
        prog = integrate_progression(
            np.asarray(rec.h),
            float(rec.native_dt),
            InstantaneousHead(r_e, Z_EXIT_PRIMARY),
            Z_EXIT_PRIMARY,
            c_e=c_e,
            k_aq_mps=k_aq,
            d_bl_m=d_bl,
            gamma_bl_sub_knpm3=gamma_bl,
            h_c_m=h_c,
            l_c_m=l_c,
            seepage_length_m=L_BASE_M,
        )
        l_e = np.asarray(prog.l_final_m)
        fail_trans = l_e >= L_BASE_M
        fail_static = h_c <= (float(rec.peak) - Z_EXIT_PRIMARY)
        sub = slice(0, 2000)
        fs_ref, ft_ref = evaluate_batch(tm[sub], rec, geom, foreland_open=True)
        assert np.array_equal(fs_ref, fail_static[sub])
        assert np.array_equal(ft_ref, fail_trans[sub])

        def q(x, p):
            return [float(np.percentile(x, pi)) for pi in p]

        out.append(
            {
                "aquifer_variant": vname,
                "p_initiated": float(np.asarray(prog.heave_occurred).mean()),
                "p_breach_transient": float(fail_trans.mean()),
                "p_static_exceeded": float(fail_static.mean()),
                "H_c_q05_50_95_m": q(h_c, (5, 50, 95)),
                "l_e_q50_90_99_m": q(l_e, (50, 90, 99)),
            }
        )
    return out


def tokachi_exposure() -> list[dict]:
    """Production-exposure indicators for the four Tokachi matrix configs."""
    rows = []
    for cfg_path in sorted((REPO / "configs").glob("kp*matrix.yaml")):
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        g = cfg["geometry"]
        pri = cfg["priors"]
        k_aq = float(pri["k_aq"]["mean"])
        d_aq = float(pri["D_aq"]["mean"])
        d_bl = float(pri["D_bl"]["mean"])
        k_bl = float(pri["k_bl"]["mean"])
        gam = float(pri["gamma_bl_sub"]["mean"])
        L = float(g["L"])
        lam_in = float(leakage_length_in(k_aq, d_aq, d_bl, k_bl))
        lam_out = float(
            leakage_length_out(
                k_aq, d_aq, g["D_fore"], g["k_fore"], g["foreshore_width"]
            )
        )
        r_e = float(response_factor(lam_in, lam_out, L))
        transmissivity = k_aq * d_aq
        tau_elastic = 1.0e-4 * d_aq * d_bl / k_bl  # ADR-0032 form, S_s=1e-4
        tau_eff = [s * lam_in**2 / transmissivity for s in S_EFF_RANGE]
        resistance_m = gam * d_bl / GAMMA_W
        onset_dh = resistance_m / r_e
        onset_dh_half_re = resistance_m / (0.5 * r_e)
        rows.append(
            {
                "config": cfg_path.stem,
                "lambda_in_m": lam_in,
                "lambda_out_eff_m": lam_out,
                "r_e": r_e,
                "transmissivity_m2ps": transmissivity,
                "pi_elastic": tau_elastic / TOKACHI_T_RISE_S,
                "pi_eff_range": [t / TOKACHI_T_RISE_S for t in tau_eff],
                "onset_dh_m": onset_dh,
                "onset_dh_if_re_halved_m": onset_dh_half_re,
                "hwl_minus_toe_m": float(g["HWL"]) - float(g["z_toe"]),
            }
        )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rec = build_record()
    print(f"record: peak {rec.peak:.2f} m T.P., {rec.h.size} steps")

    print("\n--- M4 factor grid (engine vs FEM Delta_h at observed load) ---")
    m4 = m4_factor_grid()
    for r in m4:
        if r["L_m"] == L_BASE_M and r["z_exit_m"] == Z_EXIT_PRIMARY:
            print(
                f"  {r['aquifer_variant']:14s} lambda={r['lambda_in_m']:5.1f} "
                f"r_e={r['r_e']:.3f} dh={r['dh_engine_peak_m']:.2f} "
                f"vs FEM {FEM_DH_M:.2f} -> factor {r['m4_factor']:.2f}"
            )

    print("\n--- M5 check with FEM-true heads ---")
    m5 = {
        "fem_iv_at_observed_boiling": FEM_IV,
        "terzaghi_critical_iv": TERZAGHI_IC,
        "m5_bias_ratio_fem_over_critical": FEM_IV / TERZAGHI_IC,
        "fem_gw_at_observed_boiling": FEM_GW,
        "ums_lab_cohesion_kpa": 40.8,
        "cohesion_operative": False,
        "note": "boils at G/W~1.0 despite c=40.8 kPa lab value: weight-only "
        "Terzaghi with FEM heads is ~unbiased (0.96-1.04 given "
        "gamma_t read-off); the lab cohesion did not act through "
        "the sand-vein/pocket fabric (Fig. 16 trench sketch).",
    }
    print(
        f"  FEM iv {FEM_IV} vs Terzaghi {TERZAGHI_IC:.3f} -> "
        f"ratio {FEM_IV / TERZAGHI_IC:.3f}"
    )

    print("\n--- full chain (survival consistency) ---")
    chain = full_chain(rec)
    for r in chain:
        print(
            f"  {r['aquifer_variant']:14s} P_init={r['p_initiated']:.3f} "
            f"P_breach={r['p_breach_transient']:.4f} "
            f"P_static={r['p_static_exceeded']:.4f}"
        )

    print("\n--- Tokachi production exposure ---")
    tok = tokachi_exposure()
    for r in tok:
        print(
            f"  {r['config']:28s} r_e={r['r_e']:.3f} "
            f"Pi_el={r['pi_elastic']:.4f} "
            f"Pi_eff={r['pi_eff_range'][0]:.2f}-{r['pi_eff_range'][1]:.2f} "
            f"onset dH {r['onset_dh_m']:.2f} -> "
            f"{r['onset_dh_if_re_halved_m']:.2f} m if r_e/2 "
            f"(HWL head {r['hwl_minus_toe_m']:.2f})"
        )

    payload = {
        "case": "Gounokawa Shikaga L28.75k (Sako et al. 2019 JSCE B1 75(1))",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "constants": {
            "peak_stage_m": PEAK_STAGE_M,
            "hwl_m": HWL_M,
            "z_exit_primary_m": Z_EXIT_PRIMARY,
            "z_exit_pond_m": Z_EXIT_POND,
            "D_ums_m": D_UMS_M,
            "k_ums_mps": K_UMS_MPS,
            "gamma_t_ums": GAMMA_T_UMS,
            "d70_m": D70_M,
            "L_base_m": L_BASE_M,
            "fem_iv": FEM_IV,
            "fem_gw": FEM_GW,
            "aquifer_variants": AQUIFER_VARIANTS,
            "n_chain": N_CHAIN,
            "seed": SEED,
        },
        "m4_factor_grid": m4,
        "m5_check": m5,
        "full_chain": chain,
        "cross_case_m4": YABE_M4_ROWS
        + [
            {
                "site": "Shikaga L28.75k (this case)",
                "factor": next(
                    r["m4_factor"]
                    for r in m4
                    if r["aquifer_variant"] == "composite_usg"
                    and r["L_m"] == L_BASE_M
                    and r["z_exit_m"] == Z_EXIT_PRIMARY
                ),
                "datum_confidence": "anchored (trace + elevation axis)",
            },
        ],
        "tokachi_exposure": tok,
    }
    out = OUT_DIR / "validation_results.json"
    out.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
