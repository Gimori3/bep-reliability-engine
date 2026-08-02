"""Case-study validation 2: Yabe River, July 2012 - breach (R7.3k) vs survivals.

Validates the engine against the Yabe River Levee Investigation Committee
report (houkokusyo_compressed.pdf, H25/2013): the canonical Japanese
piping-attributed levee breach (right bank 7.3k, 2012-07-14 13:15-13:30 JST;
overtopping/erosion/body-seepage excluded by CCTV + witnesses) plus two
initiated-but-survived sites under the same flood (R11.860k: boils + toe
settlement; L16.100k: boils, no levee deformation). This is the first
progression-to-breach test of M7 / C_e / the transient race condition.

PRE-REGISTERED DESIGN (2026-07-11, user steer applied)
------------------------------------------------------
Two isolated tests:

T1 - timeline test (7.3k only, M7/C_e isolation): the progression clock is
FORCED on at a committee-documented initiation anchor rather than the
engine's own M5 gate (the Gounokawa case showed that gate fires ~2.3x early;
letting it decide would contaminate the first real C_e test). Anchors, all
2012-07-14 JST, hours from record start 7/11 12:00:

  A1 62.00 (02:00)  committee case-4 model (trench-confirmed Fg-As
                    connection): G/W < 1 onset
  A2 67.00 (07:00)  PRIMARY: committee case-2 baseline G/W < 1 onset,
                    independently corroborated by four hinterland wells
                    surging from ~07:00 (resident interview, sec. 4.2.3)
  A3 72.33 (12:20)  committee summary: pressure "sufficient to uplift the
                    clay and form a water path" ~1 h before breach
  A4 73.08 (13:05)  observed surface boil (firefighters, 13:00-13:10)

Observed breach: 73.33 h (13:20; CCTV brackets 13:15-13:30). Endpoints
reported per anchor: t(l >= l_c) (point of no return), t(l >= L/2) (cavity
under the crest - the field's structural-collapse proxy), t(l >= L) (engine
breach). The field mechanism was cavity growth by fines washout (<= 0.1 mm
mobile at the committee's computed velocities) -> settlement -> washout, not
a discrete pipe daylighting the river; l >= L is therefore an analog, and
l >= L/2 is pre-registered as the closer structural proxy.

T2 - breach-vs-survival discrimination (all three sites, full chain,
engine's own M5 gate): does the transient race condition breach 7.3k while
sparing R11.860k and L16.100k under the same flood? All three initiated in
the field (boils everywhere; committee FEM G/W minima 0.47-0.62 / 0.86-0.88
/ 0.65-0.76), so common-mode early M5 firing is acceptable here. The
committee's own explanation of the outcome difference is a progression-rate
argument (p4-106: the survival sites' Dg has larger grains and greater
thickness than 7.3k's As, so void progression under the levee was slower) -
precisely the mechanism the transient engine embodies and the static
comparator lacks.

VERDICT-CRITICAL choices (flagged): (i) As d70 = 0.35 mm (toe-boring family
of Fig. 4.2.50-3; the trench family is gravel-mixed coarse sand - within-
layer matrix/framework split, handled by pairing committee framework k with
matrix d70 per the ADR-0012 logic, d70 sensitivity 0.2-0.7 mm); (ii) z_toe
anchored to the committee models' initial-head/cover-weight arithmetic;
(iii) the digitized hydrographs (control points below; text anchors: 7.3k
above HWL 7.225 from ~08:00 for ~6 h, peak = trace 8.36 at ~12:00, below HWL
~14:00). Survival-site Dg d70 ~ 5 mm sits far OUTSIDE the Sellmeijer
calibration domain: their huge H_c values are extrapolations, but the
discrimination direction (coarse -> high resistance -> stall) is the
committee's own mechanism and is robust to the exact value.

Input provenance: all values from the committee report (text pages cited in
the validation note); hydrographs digitized from Figs. 2.2.5/4.2.12/4.2.42
(7.3k), 4.3.19 (11.8k), 4.4.17 (16.0k) top panels. k values are the
committee's seepage-analysis case values (Table 4.2.3 etc.), not read off
plots. CoVs from the thesis prior table (stated assumption); C_e keeps the
ADR-0026 field prior.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

import numpy as np

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
from bep_reliability_engine.progression import (
    equilibrium_head,
    integrate_progression,
    progression_rate,
)
from bep_reliability_engine.sampling import MarginalSpec, sample_theta
from bep_reliability_engine.sellmeijer import (
    compute_critical_head_vectorized,
    compute_critical_pipe_length,
)

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "results" / "validation_yabe"

TARGET_DT_S = 225.0  # ADR-0030
SEED = 20260712
N_DISCRIMINATION = 100_000
N_TIMELINE = 30_000
COV = {
    "k_aq": 0.50,
    "d_70": 0.30,
    "D_aq": 0.10,
    "D_bl": 0.167,
    "k_bl": 0.50,
    "gamma_bl_sub": 0.056,
}
C_E_MEAN, C_E_COV = 0.055, 0.043 / 0.055

T0 = _dt.datetime(2012, 7, 11, 12, 0)  # record start (committee FEM convention)
BREACH_T_H = 73.33  # 2012-07-14 13:20 JST
ANCHORS_H = {
    "A1_case4_GW_lt1_0200": 62.0,
    "A2_case2_GW_lt1_wells_0700": 67.0,  # PRIMARY
    "A3_committee_waterpath_1220": 72.33,
    "A4_surface_boil_1305": 73.08,
}

# Hydrograph control points (hours from T0, stage m T.P.) - DIGITIZED
H_CONTROL = {
    "R7.3k": [
        (0, 1.8),
        (6, 2.0),
        (13, 2.5),
        (15, 2.5),
        (18, 2.2),
        (24, 1.5),
        (30, 1.2),
        (36, 1.0),
        (42, 1.0),
        (44, 1.2),
        (46, 2.5),
        (48, 3.9),
        (50, 3.9),
        (52, 3.3),
        (54, 2.8),
        (56, 2.7),
        (58, 3.0),
        (60, 3.3),
        (62, 3.8),
        (64, 4.6),
        (66, 5.8),
        (68, 7.0),
        (69, 7.6),
        (70, 8.0),
        (71, 8.25),
        (72, 8.36),
        (73, 8.3),
        (74, 7.8),
        (75, 7.2),
        (76, 6.6),
        (78, 5.6),
        (80, 4.9),
        (84, 3.9),
        (90, 3.2),
        (96, 2.6),
        (108, 1.9),
        (120, 1.5),
    ],
    "R11.86k": [
        (0, 4.7),
        (13, 5.5),
        (15, 5.4),
        (24, 4.6),
        (36, 4.1),
        (42, 4.0),
        (46, 5.5),
        (48, 6.9),
        (50, 7.0),
        (52, 6.2),
        (56, 5.8),
        (60, 6.2),
        (64, 7.5),
        (68, 9.6),
        (69, 10.5),
        (70, 11.05),
        (71, 11.4),
        (72, 11.57),
        (73, 11.35),
        (74, 10.95),
        (75, 10.3),
        (76, 9.6),
        (78, 8.4),
        (80, 7.6),
        (84, 6.4),
        (90, 5.4),
        (96, 4.9),
        (108, 4.2),
        (120, 3.8),
    ],
    "L16.10k": [
        (0, 9.6),
        (13, 11.8),
        (15, 11.7),
        (24, 10.8),
        (36, 10.3),
        (42, 10.2),
        (46, 11.6),
        (48, 12.6),
        (49, 12.7),
        (52, 11.9),
        (56, 11.5),
        (60, 11.8),
        (64, 12.8),
        (68, 14.6),
        (70, 16.0),
        (71, 16.5),
        (72, 16.65),
        (73, 16.55),
        (74, 16.2),
        (76, 14.2),
        (78, 13.3),
        (80, 12.8),
        (84, 12.1),
        (90, 11.5),
        (96, 11.0),
        (108, 10.7),
        (120, 10.5),
    ],
}

# Site parameters. Sources: Table 4.2.3 (k), report text (thicknesses),
# committee-model initial-head/cover-weight arithmetic (z_toe, D_bl, gamma).
SITES = {
    "R7.3k": {
        "outcome": "breach 13:15-13:30",
        "k_aq": 3.4e-4,  # As, committee case 2/4 central (3.4e-2 cm/s)
        "d_70": 3.5e-4,  # As toe-boring family, Fig. 4.2.50-3 (READ-OFF)
        "D_aq": 1.5,  # As 1-1.5 m borings / 1.8-1.9 m excavation
        "D_bl": 1.05,  # Fc cover at toe (G ~ 18 kPa anchor)
        "k_bl": 1.0e-7,  # Fc ~ Bc class 1e-5 cm/s (ASSUMED)
        "gamma_bl_sub": 7.3,
        "z_toe": 3.2,  # committee-model initial head / canal level
        "L": 30.0,  # base width, A-line section (READ-OFF; 20-40)
        "d70_bounds": (5.0e-5, 1.5e-3),
        "fem_dh_toe_peak": 2.9 - 1.05,  # case 2: p-head minus cover
        "committee_gw_min": 0.62,
    },
    "R11.86k": {
        "outcome": "boils + toe settlement, no breach",
        "k_aq": 1.3e-4,  # Dg field-test avg 1.3e-2 cm/s (range 3.6e-3-2.2e-2)
        "d_70": 5.0e-3,  # Dg curves Fig. 4.3.24-3 (READ-OFF; 2-20 mm)
        "D_aq": 10.0,  # Dg ~10 m
        "D_bl": 2.4,  # As+b2 cover at toe (G ~ 40.6 kPa anchor)
        "k_bl": 1.0e-7,  # As cover avg 1.0e-5 cm/s (p4-86)
        "gamma_bl_sub": 7.1,
        "z_toe": 8.3,
        "L": 35.0,
        "d70_bounds": (5.0e-4, 5.0e-2),
        "fem_dh_toe_peak": 4.8 - 2.4,
        "committee_gw_min": 0.86,
    },
    "L16.10k": {
        "outcome": "boils, no levee deformation, no breach",
        "k_aq": 4.0e-4,  # Dg (max 9.4e-2 cm/s; avg ASSUMED ~4e-2 cm/s)
        "d_70": 5.0e-3,  # Dg curves Fig. 4.4.22-3 (READ-OFF)
        "D_aq": 5.0,  # Dg ~5 m
        "D_bl": 1.6,  # As+b2 cover at toe (G ~ 27-29 kPa anchor)
        "k_bl": 2.0e-7,  # As cover (max 5.7e-5 cm/s; avg ASSUMED)
        "gamma_bl_sub": 7.2,
        "z_toe": 7.5,
        "L": 40.0,
        "d70_bounds": (5.0e-4, 5.0e-2),
        "fem_dh_toe_peak": 4.1 - 1.5,
        "committee_gw_min": 0.65,
    },
}

PARAM_ORDER = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]


def build_record(site: str) -> HydrographRecord:
    pts = np.array(H_CONTROL[site], dtype=np.float64)
    t_h = np.arange(0.0, 120.0 + 1e-9, 1.0)
    h = np.interp(t_h, pts[:, 0], pts[:, 1])
    rec = HydrographRecord(
        t=t_h * 3600.0,
        h=h,
        peak=float(h.max()),
        duration_hours=120.0,
        scenario="historical",
        event_id=f"yabe_2012_{site}",
        native_dt=3600.0,
        provenance={
            "source": "Yabe committee report, digitized control points",
            "t0_jst": T0.isoformat(),
            "n_control_points": int(pts.shape[0]),
        },
    )
    return resample_record(rec, TARGET_DT_S)


def geometry_dict(site: dict) -> dict:
    return {
        "L": site["L"],
        "z_toe": site["z_toe"],
        "foreshore_width": 0.0,
        "D_fore": site["D_bl"],
        "k_fore": site["k_bl"],
    }


def marginals(site: dict) -> list[MarginalSpec]:
    specs = [
        MarginalSpec(name=n, family="lognormal", mean=site[n], cov=COV[n])
        for n in PARAM_ORDER[:-1]
    ]
    specs.append(
        MarginalSpec(name="C_e", family="lognormal", mean=C_E_MEAN, cov=C_E_COV)
    )
    return specs


def sample_site(site: dict, n: int):
    return sample_theta(
        marginals(site),
        seed=SEED,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        n_samples=n,
        coupling="two_population",
        bounds={"d_70": site["d70_bounds"]},
    )


def forced_progression(
    h: np.ndarray,
    dt_s: float,
    i_start: int,
    site: dict,
    c_e: np.ndarray,
    k_aq: np.ndarray,
    d_bl: np.ndarray,
    h_c: np.ndarray,
    l_c: np.ndarray,
) -> dict:
    """M7 rate law with the I_er gate FORCED open from step ``i_start``.

    Uses only the public M7 kernels (progression_rate, equilibrium_head);
    the positive-part operator in progression_rate keeps dl/dt = 0 whenever
    H_erosion <= H_eq, so forcing the gate never manufactures overload.
    Returns end-of-step crossing times [s from record start] for l >= l_c,
    l >= L/2 and l >= L.
    """
    length = site["L"]
    z_toe = site["z_toe"]
    n = c_e.size
    length_arr = np.full(n, length)
    l_cur = np.zeros(n)
    t_lc = np.full(n, np.nan)
    t_half = np.full(n, np.nan)
    t_full = np.full(n, np.nan)
    for k in range(i_start, h.size):
        h_ero = (h[k] - z_toe) - 0.3 * d_bl
        h_eq = equilibrium_head(l_cur, h_c, l_c, length_arr)
        rate = progression_rate(h_ero, h_eq, c_e, k_aq, length_arr)
        l_cur = np.minimum(l_cur + rate * dt_s, length)
        t_now = (k + 1) * dt_s
        for arr, thr in ((t_lc, l_c), (t_half, 0.5 * length), (t_full, length - 1e-9)):
            newly = np.isnan(arr) & (l_cur >= thr)
            arr[newly] = t_now
    return {"t_lc_s": t_lc, "t_half_s": t_half, "t_full_s": t_full, "l_final": l_cur}


def timeline_test(
    rec: HydrographRecord,
    k_aq_mean: float | None = None,
    dt_guard: bool = True,
) -> list[dict]:
    """T1: forced-clock progression at R7.3k, one row per anchor.

    ``k_aq_mean`` overrides the As permeability mean: the committee's own
    case ladder spans 3.4e-4 (case 2/4 central, D20-based) to 3.1e-3 m/s
    (case 3/5, the coarse trench-As actually connected to the Fg at the
    breach front) - the pre-registered verdict hinge (i).
    """
    site = dict(SITES["R7.3k"])
    if k_aq_mean is not None:
        site["k_aq"] = k_aq_mean
    sample = sample_site(site, N_TIMELINE)
    tm = sample.theta_matrix
    geom = geometry_dict(site)
    sell = compute_critical_head_vectorized(tm, geom)
    h_c = np.asarray(sell.H_c, dtype=np.float64)
    l_c = np.asarray(
        compute_critical_pipe_length(sample.column("D_aq"), site["L"]),
        dtype=np.float64,
    )
    h = np.asarray(rec.h)
    dt_s = float(rec.native_dt)

    if dt_guard:
        # dt-halving guard on the forced loop (mean-theta, primary anchor)
        theta_mean = np.array([site[n] for n in PARAM_ORDER[:-1]] + [C_E_MEAN])
        sell_m = compute_critical_head_vectorized(theta_mean[None, :], geom)
        hc_m = np.asarray(sell_m.H_c)
        lc_m = np.asarray(compute_critical_pipe_length(site["D_aq"], site["L"]))[None]
        rec_half = resample_record(build_record("R7.3k"), TARGET_DT_S / 2)
        i0 = int(round(67.0 * 3600 / dt_s))
        i0h = int(round(67.0 * 3600 / float(rec_half.native_dt)))
        a = forced_progression(
            h,
            dt_s,
            i0,
            site,
            np.array([C_E_MEAN]),
            np.array([site["k_aq"]]),
            np.array([site["D_bl"]]),
            hc_m,
            lc_m,
        )
        b = forced_progression(
            np.asarray(rec_half.h),
            float(rec_half.native_dt),
            i0h,
            site,
            np.array([C_E_MEAN]),
            np.array([site["k_aq"]]),
            np.array([site["D_bl"]]),
            hc_m,
            lc_m,
        )
        la, lb = float(a["l_final"][0]), float(b["l_final"][0])
        rel = abs(la - lb) / max(la, 1e-12)
        assert rel < 0.01 or (
            la >= site["L"] and lb >= site["L"]
        ), f"forced-loop dt convergence failed: {la} vs {lb}"

    rows = []
    obs_interval_h = None
    for name, a_h in ANCHORS_H.items():
        i_start = int(round(a_h * 3600.0 / dt_s))
        res = forced_progression(
            h,
            dt_s,
            i_start,
            site,
            sample.column("C_e"),
            sample.column("k_aq"),
            sample.column("D_bl"),
            h_c,
            l_c,
        )
        obs_interval_h = BREACH_T_H - a_h
        out = {
            "anchor": name,
            "anchor_h": a_h,
            "k_aq_mean": site["k_aq"],
            "observed_interval_h": obs_interval_h,
        }
        for key, label in (
            ("t_lc_s", "lc"),
            ("t_half_s", "half"),
            ("t_full_s", "full"),
        ):
            t_rel_h = (res[key] - a_h * 3600.0) / 3600.0
            reached = np.isfinite(t_rel_h)
            out[f"p_reached_{label}"] = float(reached.mean())
            if reached.any():
                q = np.nanpercentile(t_rel_h, (5, 25, 50, 75, 95))
                out[f"t_{label}_q05_25_50_75_95_h"] = [float(x) for x in q]
                out[f"p_{label}_before_observed_breach"] = float(
                    np.nansum(t_rel_h <= obs_interval_h) / t_rel_h.size
                )
        rows.append(out)
    return rows


def discrimination_test(records: dict) -> list[dict]:
    """T2: full-chain (engine M5 gate) breach-vs-survival across sites."""
    out = []
    for name, site in SITES.items():
        rec = records[name]
        sample = sample_site(site, N_DISCRIMINATION)
        tm = sample.theta_matrix
        geom = geometry_dict(site)
        k_aq = sample.column("k_aq")
        d_aq = sample.column("D_aq")
        d_bl = sample.column("D_bl")
        k_bl = sample.column("k_bl")
        gamma_bl = sample.column("gamma_bl_sub")
        c_e = sample.column("C_e")
        lam_in = leakage_length_in(k_aq, d_aq, d_bl, k_bl)
        r_e = response_factor(lam_in, 0.0, site["L"])  # open entry
        sell = compute_critical_head_vectorized(tm, geom)
        h_c = np.asarray(sell.H_c, dtype=np.float64)
        l_c = np.asarray(
            compute_critical_pipe_length(d_aq, site["L"]), dtype=np.float64
        )
        prog = integrate_progression(
            np.asarray(rec.h),
            float(rec.native_dt),
            InstantaneousHead(r_e, site["z_toe"]),
            site["z_toe"],
            c_e=c_e,
            k_aq_mps=k_aq,
            d_bl_m=d_bl,
            gamma_bl_sub_knpm3=gamma_bl,
            h_c_m=h_c,
            l_c_m=l_c,
            seepage_length_m=site["L"],
        )
        l_e = np.asarray(prog.l_final_m)
        initiated = np.asarray(prog.heave_occurred, dtype=bool)
        fail_trans = l_e >= site["L"]
        peak_head = float(rec.peak) - site["z_toe"]
        fail_static = h_c <= peak_head

        sub = slice(0, 2000)
        fs_ref, ft_ref = evaluate_batch(tm[sub], rec, geom, foreland_open=True)
        assert np.array_equal(fs_ref, fail_static[sub]), "static flag drift"
        assert np.array_equal(ft_ref, fail_trans[sub]), "transient flag drift"

        def q(x, p):
            return [float(np.percentile(x, pi)) for pi in p]

        # engine peak toe overpressure vs committee FEM
        dh_peak = np.median(r_e) * peak_head
        out.append(
            {
                "site": name,
                "outcome_observed": site["outcome"],
                "n": N_DISCRIMINATION,
                "peak_gross_head_m": peak_head,
                "r_e_q05_50_95": q(r_e, (5, 50, 95)),
                "engine_dh_toe_peak_median_m": float(dh_peak),
                "fem_dh_toe_peak_m": site["fem_dh_toe_peak"],
                "committee_gw_min": site["committee_gw_min"],
                "H_c_q05_50_95_m": q(h_c, (5, 50, 95)),
                "l_c_q50_m": float(np.median(l_c)),
                "p_initiated": float(initiated.mean()),
                "p_breach_transient": float(fail_trans.mean()),
                "p_static_exceeded": float(fail_static.mean()),
                "l_e_q50_90_99_m": q(l_e, (50, 90, 99)),
                "p_pipe_gt_1m": float((l_e > 1.0).mean()),
            }
        )
        print(f"  discrimination done: {name}")
    return out


def tier1_sensitivity(rec: HydrographRecord) -> list[dict]:
    """Mean-theta verdict scan over the 7.3k read-off hinges (k, d70, L)."""
    site = dict(SITES["R7.3k"])
    rows = []
    for k_aq in (2.0e-5, 3.4e-4, 3.1e-3):
        for d70 in (2.0e-4, 3.5e-4, 7.0e-4):
            for L in (20.0, 30.0, 40.0):
                s = dict(site, k_aq=k_aq, d_70=d70, L=L)
                theta = np.array([s[n] for n in PARAM_ORDER[:-1]] + [C_E_MEAN])
                res = evaluate_realization(
                    theta, rec, geometry_dict(s), foreland_open=True
                )
                rows.append(
                    {
                        "k_aq": k_aq,
                        "d_70": d70,
                        "L": L,
                        "H_c_m": res.H_c,
                        "l_c_m": res.l_c,
                        "r_e": res.r_e,
                        "l_e_final_m": res.l_e_final,
                        "t_uh_h": (
                            res.t_uh / 3600.0 if np.isfinite(res.t_uh) else None
                        ),
                        "failure_trans": res.failure_trans,
                        "failure_static": res.failure_static,
                    }
                )
    return rows


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = {s: build_record(s) for s in SITES}
    for s, r in records.items():
        print(f"{s}: peak {r.peak:.2f} m T.P., {r.h.size} steps @ {r.native_dt}s")

    diag = []
    for s, site in SITES.items():
        ts = flood_timescales(np.asarray(records[s].h), float(records[s].native_dt))
        d = aquifer_response_diagnostic(
            segment_id=f"yabe_{s}",
            d_aq_mean_m=site["D_aq"],
            d_bl_mean_m=site["D_bl"],
            k_bl_mean_mps=site["k_bl"],
            d_aq_cov=COV["D_aq"],
            d_bl_cov=COV["D_bl"],
            k_bl_cov=COV["k_bl"],
            t_rise_s=ts.get("rise_10_90_s"),
            t_plateau_s=ts.get("plateau_s"),
            native_dt_s=float(records[s].native_dt),
        )
        diag.append(
            {
                "site": s,
                **{
                    k: d[k]
                    for k in d
                    if isinstance(d[k], (int, float, str, bool, type(None)))
                },
            }
        )
        print(
            f"  aquifer diag {s}: pi_central={d.get('pi_central'):.4f} "
            f"verdict={d.get('verdict')}"
        )

    print("\n--- Tier 1: 7.3k mean-theta verdict scan ---")
    t1 = tier1_sensitivity(records["R7.3k"])

    print("\n--- T1: forced-clock timeline test (7.3k) ---")
    # k-variant ladder = the committee's own case ladder (Table 4.2.3):
    # central 3.4e-4 (case 2/4), intermediate 1e-3, coarse trench-As 3.1e-3
    # (case 3/5) - the pre-registered verdict hinge (i).
    timeline = []
    for i, k_mean in enumerate((None, 1.0e-3, 3.1e-3)):
        timeline.extend(
            timeline_test(records["R7.3k"], k_aq_mean=k_mean, dt_guard=(i == 0))
        )

    print("\n--- T2: discrimination across the three sites ---")
    disc = discrimination_test(records)

    payload = {
        "case": "Yabe River 2012 (committee report H25/2013): R7.3k breach "
        "vs R11.860k / L16.100k survivals",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "breach_time_h": BREACH_T_H,
        "anchors_h": ANCHORS_H,
        "sites": SITES,
        "cov": COV,
        "c_e": [C_E_MEAN, C_E_COV],
        "n_timeline": N_TIMELINE,
        "n_discrimination": N_DISCRIMINATION,
        "seed": SEED,
        "aquifer_diagnostic": diag,
        "tier1_sensitivity_7_3k": t1,
        "timeline_test": timeline,
        "discrimination": disc,
    }
    out = OUT_DIR / "validation_results.json"
    out.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
