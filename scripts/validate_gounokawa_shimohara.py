"""Case-study validation: Gounokawa River right-bank levee, Shimohara district.

Validates the Phase 1 engine against the repeated sand-boiling case of
Okamura, Mori, Ishihara, Maeda et al. (2025), Soils and Foundations 65,
101656 (2018 / 2020 / 2021 flooding events; no breach). This is a standalone
validation harness: it never touches ``configs/`` or the config generator,
and it drives the frozen public engine APIs only (M2 ``sample_theta``, M4
kernels, M6 vectorized Sellmeijer, M7 ``integrate_progression``, M8
``evaluate_realization``/``evaluate_batch``).

Design (approved 2026-07-11, conversation record):

* 2018 virgin-state event is the core quantitative test; 2020/2021 are
  qualitative (post-2018 sheet pile + established ejecta pathways are not
  representable).
* Primary observable: the head difference across the levee at incipient sand
  ejection, eyewitness-bracketed to 05:30-05:54 JST on 2018-07-07 (paper
  section 3.4). Survival (no breach) is a consistency check only (one
  Bernoulli draw). The trench null (no BEP pipes at the sand-layer surface,
  paper section 4.3) is compared against the predicted equilibrium pipe
  length.
* z_toe = 12.9 m T.P. (hinterland ground at Location A) is the PRIMARY
  datum; the ponded-paddy datum (~13.3 m) is a bounding sensitivity, and the
  pond's stabilizing effects are part of the conservatism budget, not a
  confound to remove.
* L = 150 m (hydraulic entry at the riverbed-gravel contact, inferred from
  the paper's Fig. 9 dH/L axis and Fig. 3 cross-section) is the baseline;
  L = 75 m (embankment base width, Fig. 3b) is the sensitivity. The Waseda
  DEM (34 x 41 m patch at Location A) cannot pin L.
* Three single-aquifer schematizations of the sand-over-gravel foundation
  are the central axis (first-class finding, not a robustness check):
  ``framework_gravel`` (gravel k, sand d70 - the ADR-0012 two-population
  analog), ``single_soil_sand`` (sand k and d70, sand layer only), and
  ``composite`` (transmissivity-weighted k over the full thickness).

Input provenance
----------------
Hydrographs: Waseda companion dataset (doi:10.20556/0002006234), Fig. 5
water-level workbook - hourly Tanijugo stages for all three events. Time
alignment t0 = first sample at 05:00 JST on day one of each event window,
verified against the paper's anchors (2018 peak 19.567 m T.P. at 07-07
06:00; hinterland-level crossing 20-21h on 07-06; 8 h above T.P. 19). Site
stage = Tanijugo + 0.40 m (paper section 2.2 flood-mark offset).

Soil/geometry values marked READ-OFF below are digitized from paper figures
(Figs. 2d, 3, 17) and are NOT in the companion dataset; they carry the
read-off uncertainty flagged in the validation note.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

import numpy as np
import openpyxl

from bep_reliability_engine.constants import GAMMA_W
from bep_reliability_engine.evaluator import evaluate_batch, evaluate_realization
from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    aquifer_response_diagnostic,
    leakage_length_in,
    response_factor,
)
from bep_reliability_engine.hydrographs import (
    HydrographRecord,
    flood_timescales,
    resample_record,
)
from bep_reliability_engine.progression import integrate_progression
from bep_reliability_engine.sampling import MarginalSpec, sample_theta
from bep_reliability_engine.sellmeijer import (
    compute_critical_head_vectorized,
    compute_critical_pipe_length,
)

REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "data" / "digitized" / "Gounokawa_River_Levee_Okamura"
OUT_DIR = REPO / "results" / "validation_gounokawa"

# --------------------------------------------------------------------------
# Case constants (provenance per line; READ-OFF = digitized from a figure)
# --------------------------------------------------------------------------
SITE_STAGE_OFFSET_M = 0.40  # paper section 2.2: flood marks 0.4 m above Tanijugo
Z_TOE_PRIMARY_M = 12.9  # hinterland ground, Location A (dataset Fig11 min 12.87)
Z_TOE_POND_M = 13.3  # 2018 paddy pond level implied by the paper's dH band
L_BASELINE_M = 150.0  # READ-OFF: Fig. 9 dH/L axis + Fig. 3 riverbed contact
L_SENSITIVITY_M = 75.0  # Fig. 3b embankment base width
D_BL_M = 3.1  # trench: erodible sand surface at G.L. -3.1 m (Loc. A)
K_BL_MPS = 3.0e-6  # READ-OFF: Fig. 2d silty sand / sandy silt band centre
GAMMA_BL_SUB = 7.5  # ASSUMED: silty sand, gamma_sat ~ 17.3 kN/m3
D70_SAND_M = 3.5e-4  # READ-OFF: Fig. 17 sand-layer curve (0.1-1.0 mm band)
K_SAND_MPS = 5.0e-4  # READ-OFF: Fig. 2d sand band centre
K_GRAVEL_MPS = 3.0e-2  # READ-OFF: Fig. 2d gravel band centre (1e-2..1e-1)
D_SAND_M = 2.0  # paper section 2.1: sand layer 1-3 m
D_GRAVEL_M = 8.0  # ASSUMED: gravel from ~T.P. 7 to below boring depth
C_E_MEAN, C_E_COV = 0.055, 0.043 / 0.055  # ADR-0026 field prior (unchanged)

# Thesis prior-table CoVs (stated assumption: the paper reports no scatter)
COV = {
    "k_aq": 0.50,
    "d_70": 0.30,
    "D_aq": 0.10,
    "D_bl": 0.167,
    "k_bl": 0.50,
    "gamma_bl_sub": 0.056,
}

N_SAMPLES = 100_000
SEED = 20260711
TARGET_DT_S = 225.0  # ADR-0030 integration-timestep policy

# Single-aquifer schematizations of the sand-over-gravel foundation, plus a
# harness-level hybrid added after the first results round: the three
# single-k poles proved decisive (gravel-k falsified in both directions,
# sand-k consistent but with an r_e that contradicts the paper's gravel-fed
# pressure mechanism), so the hybrid separates the roles: the gravel drives
# the M4 pressure translation (r_e), the sand layer drives M6 resistance and
# the M7 erosion law. The engine's theta has a single k_aq, so the hybrid is
# built from the public kernels (head model is an explicit M7 input); it is
# NOT an engine mode and evaluate_batch cannot reproduce it.
_T_COMPOSITE = K_SAND_MPS * D_SAND_M + K_GRAVEL_MPS * D_GRAVEL_M
D_PRESSURE_M = D_SAND_M + D_GRAVEL_M  # transmissive thickness for hybrid M4
SCHEMATIZATIONS = {
    "framework_gravel": {  # gravel k everywhere (ADR-0012 framework analog)
        "k_aq": K_GRAVEL_MPS,
        "d_70": D70_SAND_M,
        "D_aq": D_SAND_M + D_GRAVEL_M,
    },
    "single_soil_sand": {  # erodible sand layer treated as the whole aquifer
        "k_aq": K_SAND_MPS,
        "d_70": D70_SAND_M,
        "D_aq": D_SAND_M,
    },
    "composite": {  # transmissivity-weighted k over full thickness
        "k_aq": _T_COMPOSITE / (D_SAND_M + D_GRAVEL_M),
        "d_70": D70_SAND_M,
        "D_aq": D_SAND_M + D_GRAVEL_M,
    },
}
HYBRID = "hybrid_gravel_pressure"  # M4 from gravel, M6/M7 from sand

# Observed quantities (paper section 3.4, Fig. 9; dataset-verified stages)
OBSERVED = {
    "onset_window_jst": "2018-07-07 05:30-05:54",
    "onset_site_stage_band_m": (19.5, 19.9),  # Tanijugo 19.1/19.5 + 0.4
    "onset_dh_ground_band_m": (6.6, 7.0),  # stage - 12.9 (primary datum)
    "onset_dh_paper_band_m": (6.2, 6.6),  # paper's pond-datum dH
    "onset_dh_2020_m": 5.8,  # Fig. 9 upper estimate
    "onset_dh_2021_m": 5.0,  # Fig. 9 upper estimate
    "peak_site_stage_2018_m": 19.567 + SITE_STAGE_OFFSET_M,
    "breach": False,
    "trench_pipes_found": False,
    # Fig. 4 dataset: largest pre-2018 annual stage (1999, Tanijugo 16.73 m)
    # produced no reported ejecta ("the 2018 event was the first"), so the
    # virgin-state onset dH over ground exceeds this bound.
    "pre2018_max_site_stage_m": 16.73 + SITE_STAGE_OFFSET_M,
    "pre2018_no_ejecta_dh_bound_m": 16.73 + SITE_STAGE_OFFSET_M - Z_TOE_PRIMARY_M,
}

EVENT_T0 = {  # first water-level sample (JST); alignment verified vs paper
    2018: _dt.datetime(2018, 7, 2, 5, 0),
    2020: _dt.datetime(2020, 7, 10, 5, 0),
    2021: _dt.datetime(2021, 8, 9, 5, 0),
}
EVENT_COL = {2018: 1, 2020: 3, 2021: 5}


def load_event(year: int) -> HydrographRecord:
    """Build the site-stage HydrographRecord for one event from the dataset."""
    wb = openpyxl.load_workbook(
        DATASET / "Fig5_Hydorographs and hourly precipitation du_OKAMURA Mitsu.xlsx",
        read_only=True,
        data_only=True,
    )
    ws = wb["Water level"]
    col = EVENT_COL[year]
    h = np.array(
        [
            r[col]
            for r in ws.iter_rows(min_row=3, max_col=6, values_only=True)
            if r[col] is not None
        ],
        dtype=np.float64,
    )
    wb.close()
    h_site = h + SITE_STAGE_OFFSET_M
    t = np.arange(h_site.size, dtype=np.float64) * 3600.0
    record = HydrographRecord(
        t=t,
        h=h_site,
        peak=float(h_site.max()),
        duration_hours=float(h_site.size),
        scenario="historical",
        event_id=f"gounokawa_shimohara_{year}",
        native_dt=3600.0,
        provenance={
            "source": "Waseda dataset doi:10.20556/0002006234, Fig5 workbook",
            "station": "Tanijugo (14.8k)",
            "site_stage_offset_m": SITE_STAGE_OFFSET_M,
            "t0_jst": EVENT_T0[year].isoformat(),
        },
    )
    return resample_record(record, TARGET_DT_S)


def geometry_dict(L: float, z_toe: float) -> dict:
    """Engine geometry contract. Foreshore keys are inert under open entry."""
    return {
        "L": L,
        "z_toe": z_toe,
        "foreshore_width": 0.0,
        "D_fore": D_BL_M,
        "k_fore": K_BL_MPS,
    }


def theta_mean_row(schem: dict) -> np.ndarray:
    """Mean theta row in PARAM_NAMES order."""
    return np.array(
        [
            schem["k_aq"],
            schem["d_70"],
            schem["D_aq"],
            D_BL_M,
            K_BL_MPS,
            GAMMA_BL_SUB,
            C_E_MEAN,
        ]
    )


def marginals(schem: dict) -> list[MarginalSpec]:
    means = {
        "k_aq": schem["k_aq"],
        "d_70": schem["d_70"],
        "D_aq": schem["D_aq"],
        "D_bl": D_BL_M,
        "k_bl": K_BL_MPS,
        "gamma_bl_sub": GAMMA_BL_SUB,
    }
    specs = [
        MarginalSpec(name=n, family="lognormal", mean=m, cov=COV[n])
        for n, m in means.items()
    ]
    specs.append(
        MarginalSpec(name="C_e", family="lognormal", mean=C_E_MEAN, cov=C_E_COV)
    )
    return specs


def onset_stage_analytic(
    r_e: np.ndarray, gamma_bl: np.ndarray, d_bl: np.ndarray, z_toe: float
) -> np.ndarray:
    """Stage at which the uplift/heave gate opens (ADR-0008 collapse).

    Gate opens when Delta_h_blanket = r_e * (h - z_toe) exceeds
    gamma'_bl * D_bl / gamma_w; uplift and heave flip together.
    """
    return z_toe + (gamma_bl * d_bl) / (GAMMA_W * r_e)


def _hybrid_scalar(rec: HydrographRecord, L: float, z_toe: float) -> dict:
    """Mean-value hybrid run: M4 from gravel means, M6/M7 from sand means."""
    sand = SCHEMATIZATIONS["single_soil_sand"]
    theta = theta_mean_row(sand)
    geom = geometry_dict(L, z_toe)
    lam_in = float(leakage_length_in(K_GRAVEL_MPS, D_PRESSURE_M, D_BL_M, K_BL_MPS))
    r_e = float(response_factor(lam_in, 0.0, L))
    sell = compute_critical_head_vectorized(theta[None, :], geom)
    h_c = float(np.asarray(sell.H_c)[0])
    l_c = float(np.asarray(compute_critical_pipe_length(sand["D_aq"], L)))
    prog = integrate_progression(
        np.asarray(rec.h),
        float(rec.native_dt),
        InstantaneousHead(np.array([r_e]), z_toe),
        z_toe,
        c_e=np.array([C_E_MEAN]),
        k_aq_mps=np.array([sand["k_aq"]]),
        d_bl_m=np.array([D_BL_M]),
        gamma_bl_sub_knpm3=np.array([GAMMA_BL_SUB]),
        h_c_m=np.array([h_c]),
        l_c_m=np.array([l_c]),
        seepage_length_m=L,
    )
    l_e = float(np.asarray(prog.l_final_m)[0])
    t_uh = float(np.asarray(prog.t_uh_s)[0])
    return {
        "r_e": r_e,
        "lambda_in_m": lam_in,
        "H_c_m": h_c,
        "l_c_m": l_c,
        "t_uh_h": t_uh / 3600.0 if np.isfinite(t_uh) else None,
        "l_e_final_m": l_e,
        "Z_static_m": h_c - (float(rec.peak) - z_toe),
        "Z_transient_m": L - l_e,
        "failure_static": bool(h_c <= float(rec.peak) - z_toe),
        "failure_trans": bool(l_e >= L),
        "initiated": bool(np.asarray(prog.heave_occurred)[0]),
    }


def tier1(records: dict) -> list[dict]:
    """Mean-theta deterministic runs across the full sensitivity grid."""
    rows = []
    for name in [*SCHEMATIZATIONS, HYBRID]:
        for L in (L_BASELINE_M, L_SENSITIVITY_M):
            for z_toe in (Z_TOE_PRIMARY_M, Z_TOE_POND_M):
                for year, rec in records.items():
                    if name == HYBRID:
                        row = _hybrid_scalar(rec, L, z_toe)
                        onset = onset_stage_analytic(
                            row["r_e"], GAMMA_BL_SUB, D_BL_M, z_toe
                        )
                    else:
                        theta = theta_mean_row(SCHEMATIZATIONS[name])
                        res = evaluate_realization(
                            theta,
                            rec,
                            geometry_dict(L, z_toe),
                            store_trajectory=True,
                            foreland_open=True,
                        )
                        onset = onset_stage_analytic(
                            res.r_e, GAMMA_BL_SUB, D_BL_M, z_toe
                        )
                        # engine-consistency guard: analytic onset stage must
                        # bracket the engine's own first uplift+heave time
                        h = np.asarray(rec.h)
                        if np.isfinite(res.t_uh):
                            k = int(round(res.t_uh / rec.native_dt))
                            assert (
                                h[k] > onset - 1e-9
                            ), "analytic onset disagrees with engine t_uh"
                        row = {
                            "r_e": res.r_e,
                            "lambda_in_m": res.lambda_in,
                            "H_c_m": res.H_c,
                            "l_c_m": res.l_c,
                            "t_uh_h": (
                                res.t_uh / 3600.0 if np.isfinite(res.t_uh) else None
                            ),
                            "l_e_final_m": res.l_e_final,
                            "Z_static_m": res.Z_static,
                            "Z_transient_m": res.Z_transient,
                            "failure_static": res.failure_static,
                            "failure_trans": res.failure_trans,
                            "initiated": bool(res.heave_occurred),
                        }
                    rows.append(
                        {
                            "schematization": name,
                            "L_m": L,
                            "z_toe_m": z_toe,
                            "event": year,
                            "onset_stage_m": float(onset),
                            "onset_dh_m": float(onset - z_toe),
                            **row,
                        }
                    )
    return rows


def tier2(record_2018: HydrographRecord) -> list[dict]:
    """Probabilistic runs: 2018 event, primary datum, both L, four schems."""
    out = []
    peak = float(record_2018.peak)
    for name in [*SCHEMATIZATIONS, HYBRID]:
        schem = SCHEMATIZATIONS["single_soil_sand" if name == HYBRID else name]
        sample = sample_theta(
            marginals(schem),
            seed=SEED,
            rho_log_kaq_d70=0.0,
            d70_interpretation="matrix",
            n_samples=N_SAMPLES,
            coupling="two_population",
            bounds={"d_70": (5.0e-5, 1.0e-3)},
        )
        tm = sample.theta_matrix
        k_aq = sample.column("k_aq")
        d_aq = sample.column("D_aq")
        d_bl = sample.column("D_bl")
        k_bl = sample.column("k_bl")
        gamma_bl = sample.column("gamma_bl_sub")
        c_e = sample.column("C_e")
        if name == HYBRID:
            # M4 pressure path via the gravel: independent lognormal gravel-k
            # draw (moment-matched), transmissive thickness scaled from the
            # sampled sand D_aq to preserve its stratified variability.
            rng = np.random.default_rng(SEED + 7)
            cov_k = COV["k_aq"]
            sig = np.sqrt(np.log1p(cov_k**2))
            mu = np.log(K_GRAVEL_MPS) - 0.5 * sig**2
            k_press = rng.lognormal(mu, sig, N_SAMPLES)
            d_press = d_aq * (D_PRESSURE_M / D_SAND_M)
            lam_in = leakage_length_in(k_press, d_press, d_bl, k_bl)
        else:
            lam_in = leakage_length_in(k_aq, d_aq, d_bl, k_bl)

        for L in (L_BASELINE_M, L_SENSITIVITY_M):
            geom = geometry_dict(L, Z_TOE_PRIMARY_M)
            r_e = response_factor(lam_in, 0.0, L)  # open entry: lambda_out=0
            onset_stage = onset_stage_analytic(r_e, gamma_bl, d_bl, Z_TOE_PRIMARY_M)
            onset_dh = onset_stage - Z_TOE_PRIMARY_M

            sell = compute_critical_head_vectorized(tm, geom)
            h_c = np.asarray(sell.H_c, dtype=np.float64)
            l_c = np.asarray(compute_critical_pipe_length(d_aq, L), dtype=np.float64)

            head_model = InstantaneousHead(r_e, Z_TOE_PRIMARY_M)
            prog = integrate_progression(
                np.asarray(record_2018.h),
                float(record_2018.native_dt),
                head_model,
                Z_TOE_PRIMARY_M,
                c_e=c_e,
                k_aq_mps=k_aq,
                d_bl_m=d_bl,
                gamma_bl_sub_knpm3=gamma_bl,
                h_c_m=h_c,
                l_c_m=l_c,
                seepage_length_m=L,
            )
            l_e = np.asarray(prog.l_final_m)
            initiated = np.asarray(prog.heave_occurred, dtype=bool)
            fail_trans = l_e >= L
            fail_static = h_c <= (peak - Z_TOE_PRIMARY_M)

            # engine-fidelity cross-check on a subsample: the production M8
            # batch path must reproduce the flags derived above (skipped for
            # the hybrid, which is a harness construct M8 cannot represent)
            if name != HYBRID:
                sub = slice(0, 2000)
                fs_ref, ft_ref = evaluate_batch(
                    tm[sub], record_2018, geom, foreland_open=True
                )
                assert np.array_equal(fs_ref, fail_static[sub]), "static flag drift"
                assert np.array_equal(ft_ref, fail_trans[sub]), "transient flag drift"

            def q(x, p):
                return [float(np.percentile(x, pi)) for pi in p]

            lo_obs, hi_obs = OBSERVED["onset_site_stage_band_m"]
            dh_bound = OBSERVED["pre2018_no_ejecta_dh_bound_m"]
            out.append(
                {
                    "schematization": name,
                    "L_m": L,
                    "z_toe_m": Z_TOE_PRIMARY_M,
                    "n": N_SAMPLES,
                    "r_e_q05_50_95": q(r_e, (5, 50, 95)),
                    "lambda_in_q50": float(np.median(lam_in)),
                    "H_c_q05_50_95_m": q(h_c, (5, 50, 95)),
                    "l_c_q50_m": float(np.median(l_c)),
                    "onset_stage_q05_25_50_75_95_m": q(
                        onset_stage, (5, 25, 50, 75, 95)
                    ),
                    "onset_dh_q05_50_95_m": q(onset_dh, (5, 50, 95)),
                    "p_onset_below_obs_band": float((onset_stage < lo_obs).mean()),
                    "p_onset_within_obs_band": float(
                        ((onset_stage >= lo_obs) & (onset_stage <= hi_obs)).mean()
                    ),
                    "p_onset_respects_pre2018_bound": float(
                        (onset_dh > dh_bound).mean()
                    ),
                    "median_bias_factor_dh": float(
                        np.mean(OBSERVED["onset_dh_ground_band_m"])
                        / np.median(onset_dh)
                    ),
                    "p_initiated_2018": float(initiated.mean()),
                    "p_breach_2018": float(fail_trans.mean()),
                    "p_static_exceeded_2018": float(fail_static.mean()),
                    "l_e_q50_90_99_m": q(l_e, (50, 90, 99)),
                    "p_pipe_gt_1m": float((l_e > 1.0).mean()),
                }
            )
            print(f"  tier2 done: {name} L={L}")
    return out


def aquifer_diagnostics(record_2018: HydrographRecord) -> list[dict]:
    ts = flood_timescales(np.asarray(record_2018.h), float(record_2018.native_dt))
    rows = []
    for name, schem in SCHEMATIZATIONS.items():
        d = aquifer_response_diagnostic(
            segment_id=f"gounokawa_shimohara_{name}",
            d_aq_mean_m=schem["D_aq"],
            d_bl_mean_m=D_BL_M,
            k_bl_mean_mps=K_BL_MPS,
            d_aq_cov=COV["D_aq"],
            d_bl_cov=COV["D_bl"],
            k_bl_cov=COV["k_bl"],
            t_rise_s=ts.get("rise_10_90_s"),
            t_plateau_s=ts.get("plateau_s"),
            native_dt_s=float(record_2018.native_dt),
        )
        rows.append(
            {
                "schematization": name,
                **{
                    k: d[k]
                    for k in d
                    if isinstance(d[k], (int, float, str, bool, type(None)))
                },
            }
        )
    return rows


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = {y: load_event(y) for y in (2018, 2020, 2021)}
    for y, r in records.items():
        print(
            f"event {y}: {r.h.size} steps @ {r.native_dt}s, "
            f"peak site stage {r.peak:.3f} m T.P."
        )

    print("\n--- aquifer-response diagnostic (2018 record) ---")
    diag = aquifer_diagnostics(records[2018])
    for d in diag:
        print(" ", {k: d[k] for k in list(d)[:8]})

    print("\n--- Tier 1: mean-theta deterministic grid ---")
    t1 = tier1(records)

    print("\n--- Tier 2: probabilistic (2018, z_toe=12.9) ---")
    t2 = tier2(records[2018])

    payload = {
        "case": "Gounokawa Shimohara (Okamura et al. 2025, S&F 65:101656)",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "observed": {k: v for k, v in OBSERVED.items()},
        "constants": {
            "site_stage_offset_m": SITE_STAGE_OFFSET_M,
            "z_toe_primary_m": Z_TOE_PRIMARY_M,
            "z_toe_pond_m": Z_TOE_POND_M,
            "L_baseline_m": L_BASELINE_M,
            "L_sensitivity_m": L_SENSITIVITY_M,
            "D_bl_m": D_BL_M,
            "k_bl_mps": K_BL_MPS,
            "gamma_bl_sub_knpm3": GAMMA_BL_SUB,
            "schematizations": SCHEMATIZATIONS,
            "cov": COV,
            "c_e": [C_E_MEAN, C_E_COV],
            "n_samples": N_SAMPLES,
            "seed": SEED,
            "target_dt_s": TARGET_DT_S,
        },
        "aquifer_diagnostic": diag,
        "tier1": t1,
        "tier2": t2,
    }
    out = OUT_DIR / "validation_results.json"
    out.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
