"""Measure the four physical-model qualifications of the 2026-09-16 pass.

Companion driver for ``docs/decisions/physical-model-qualifications-study.md``.
Changes no default, touches no persisted production artifact, and imports the
engine's own kernels rather than re-deriving any relation.

Four parts, selected with ``--part`` (default ``all``):

``gradients``
    Whether the 1998 exit gradients discriminate between the under-levee and
    the foreshore-spanning seepage-length conventions. The adopted
    leakage-length translation gives a local vertical exit gradient
    ``i_v = r_e * (H - z_toe) / D_bl`` and a horizontal gradient at the toe
    ``i_h = r_e * (H - z_toe) / lambda_in``. Both are evaluated at each
    section's prior means and at its 1998 design level, once with ``L`` the
    surveyed under-levee path and once with ``L + B_f``, and compared with the
    values OYO's own finite-element model reported.

``scaling``
    The exponent of the seepage length in the Sellmeijer critical head. M6 is
    called directly, so the measured exponent is the engine's, not an algebraic
    restatement of it.

``contrast``
    How much of KP 62.0's static-branch displacement the seepage path accounts
    for, measured on the persisted production theta matrices with each
    section's own sampled ``L`` and with that ``L`` rescaled to KP 62.0's
    nominal 40 m.

``scour``
    Whether the fluvial-scour law engages at all under the ADR-0042
    dimensionally-corrected erodibility conversion, separating activation
    (does bed shear exceed the sampled threshold?), accumulation (how much
    depth accrues?) and the breach criterion (does that depth consume the
    levee width?). Reproduces the committed surface-curve generation exactly:
    same segment inputs, canonical event, level ladder, seeds and MC count.
    This part reads the raw d4PDF band workbooks and takes a few minutes.

Usage::

    python scripts/physical_model_qualifications.py \
        --out docs/decisions/physical-model-qualifications-study.json

Provenance of the externally tabulated inputs used by ``gradients``: the 1998
deterministic safety evaluation of OYO (1999), Forms 6 and 7, as transcribed in
``docs/tokachi_bep_inputs_provenance.md`` section 3.10. They are inputs to the
comparison, never outputs of it.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine import hydraulics, sellmeijer  # noqa: E402
from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.run import seepage_length_samples_for_config  # noqa: E402
from bep_reliability_engine.sampling import PARAM_NAMES  # noqa: E402

CONFIG_STEMS: dict[str, str] = {
    "57.4": "kp57_4_historical_matrix",
    "58.8": "kp58_8_historical_matrix",
    "60.0": "kp60_0_historical_matrix",
    "62.0": "kp62_0_historical_matrix",
}
RESULT_STEMS: dict[str, str] = {
    "57.4": "tokachi_kp57.4_historical_matrix",
    "58.8": "tokachi_kp58.8_historical_matrix",
    "60.0": "tokachi_kp60.0_historical_matrix",
    "62.0": "tokachi_kp62.0_historical_matrix",
}

# OYO (1999) Form 6/7, the 1998 deterministic safety evaluation. Inputs to the
# comparison; see the module docstring for their provenance.
OYO_1998_EXIT_GRADIENT_V: dict[str, float] = {
    "57.4": 0.040,
    "58.8": 1.300,
    "60.0": 0.500,
    "62.0": 0.970,
}
OYO_1998_EXIT_GRADIENT_H: dict[str, float | None] = {
    "57.4": 0.050,
    "58.8": 0.620,
    "60.0": 0.400,
    "62.0": None,
}
OYO_1998_DESIGN_LEVEL_M: dict[str, float] = {
    "57.4": 39.51,
    "58.8": 41.33,
    "60.0": 43.06,
    "62.0": 46.68,
}

# --- scour part: the committed surface-curve generation settings ----------
CANONICAL_EVENT = "HPB_m064_1987"
N_MC = 10_000
LEVEL_STEP_M = 0.2
LEVEL_MARGIN_ABOVE_CREST_M = 3.0
SEED_ROOT = 20260717
MECH_INDEX_SCOUR_USACE = 3
MECH_INDEX_SCOUR_SCRIPT = 1


def _prior_means(config: Config) -> dict[str, float]:
    """The seven prior means as a name-keyed dict."""
    priors = config.priors
    return {name: getattr(priors, name).mean for name in PARAM_NAMES}


def _theta_row(config: Config) -> np.ndarray:
    means = _prior_means(config)
    return np.array([means[name] for name in PARAM_NAMES], dtype=float)


def part_gradients() -> list[dict]:
    """Do the 1998 exit gradients select a seepage-length convention?"""
    rows: list[dict] = []
    for kp, stem in CONFIG_STEMS.items():
        config = Config.from_yaml(REPO / "configs" / f"{stem}.yaml")
        geom = config.geometry
        means = _prior_means(config)
        lam_in = float(
            hydraulics.leakage_length_in(
                means["k_aq"], means["D_aq"], means["D_bl"], means["k_bl"]
            )
        )
        lam_out_eff = float(
            hydraulics.leakage_length_out(
                means["k_aq"],
                means["D_aq"],
                geom.D_fore,
                geom.k_fore,
                geom.foreshore_width,
            )
        )
        r_e_under = float(hydraulics.response_factor(lam_in, lam_out_eff, geom.L))
        r_e_span = float(
            hydraulics.response_factor(
                lam_in, lam_out_eff, geom.L + geom.foreshore_width
            )
        )
        head = OYO_1998_DESIGN_LEVEL_M[kp] - geom.z_toe
        d_bl = means["D_bl"]
        i_v_under = r_e_under * head / d_bl
        i_v_span = r_e_span * head / d_bl
        i_h_under = r_e_under * head / lam_in
        reported_v = OYO_1998_EXIT_GRADIENT_V[kp]
        rows.append(
            {
                "kp": kp,
                "L_m": geom.L,
                "foreshore_width_m": geom.foreshore_width,
                "z_toe_m": geom.z_toe,
                "design_level_1998_m": OYO_1998_DESIGN_LEVEL_M[kp],
                "head_1998_m": head,
                "D_bl_m": d_bl,
                "lambda_in_m": lam_in,
                "lambda_out_eff_m": lam_out_eff,
                "r_e_under_levee": r_e_under,
                "r_e_foreshore_spanning": r_e_span,
                "i_v_model_under_levee": i_v_under,
                "i_v_model_foreshore_spanning": i_v_span,
                "i_v_reported_1998": reported_v,
                "ratio_under_levee_to_reported": i_v_under / reported_v,
                "ratio_spanning_to_reported": i_v_span / reported_v,
                "i_h_model_under_levee": i_h_under,
                "i_h_reported_1998": OYO_1998_EXIT_GRADIENT_H[kp],
                "mean_horizontal_gradient_over_L_plus_Bf": head
                / (geom.L + geom.foreshore_width),
            }
        )
    return rows


def part_scaling() -> list[dict]:
    """The exponent of L in the Sellmeijer critical head, measured through M6."""
    rows: list[dict] = []
    for kp, stem in CONFIG_STEMS.items():
        config = Config.from_yaml(REPO / "configs" / f"{stem}.yaml")
        theta = _theta_row(config)
        length = config.geometry.L
        kwargs = {
            "alpha_exponent": config.alpha_exponent,
            "theta_repose_rad": config.theta_repose_rad,
            "relative_density": config.relative_density_insitu,
        }

        def h_c(value: float) -> float:
            return float(
                sellmeijer.compute_critical_head(theta, {"L": value}, **kwargs).H_c
            )

        lo, hi = h_c(length * 0.99), h_c(length * 1.01)
        local = math.log(hi / lo) / math.log(1.01 / 0.99)
        means = _prior_means(config)
        lam_out_eff = float(
            hydraulics.leakage_length_out(
                means["k_aq"],
                means["D_aq"],
                config.geometry.D_fore,
                config.geometry.k_fore,
                config.geometry.foreshore_width,
            )
        )
        credited = length + lam_out_eff
        base, up = h_c(length), h_c(credited)
        rows.append(
            {
                "kp": kp,
                "L_m": length,
                "D_aq_over_L": means["D_aq"] / length,
                "H_c_m": base,
                "critical_gradient_H_c_over_L": base / length,
                "local_exponent_dlnHc_dlnL": local,
                "credited_L_m": credited,
                "H_c_at_credited_L_m": up,
                "kappa_H_c_ratio": up / base,
                "secant_exponent_over_credited_range": math.log(up / base)
                / math.log(credited / length),
                "critical_gradient_at_credited_L": up / credited,
            }
        )
    return rows


def part_contrast() -> dict:
    """How much of KP 62.0's static displacement is the seepage path?"""
    import h5py

    per_section: list[dict] = []
    for kp, stem in CONFIG_STEMS.items():
        config = Config.from_yaml(REPO / "configs" / f"{stem}.yaml")
        lengths = seepage_length_samples_for_config(config)
        path = REPO / "results" / f"{RESULT_STEMS[kp]}.h5"
        with h5py.File(path, "r") as handle:
            theta = handle["theta_matrix"][:]
        kwargs = {
            "alpha_exponent": config.alpha_exponent,
            "theta_repose_rad": config.theta_repose_rad,
            "relative_density": config.relative_density_insitu,
        }
        own = sellmeijer.compute_critical_head_vectorized(
            theta, {"L": lengths}, **kwargs
        ).H_c
        rescaled = lengths * (40.0 / config.geometry.L)
        equalised = sellmeijer.compute_critical_head_vectorized(
            theta, {"L": rescaled}, **kwargs
        ).H_c
        per_section.append(
            {
                "kp": kp,
                "nominal_L_m": config.geometry.L,
                "median_sampled_L_m": float(np.median(lengths)),
                "median_H_c_m": float(np.median(own)),
                "median_H_c_at_L_40m": float(np.median(equalised)),
                "length_factor": float(np.median(equalised) / np.median(own)),
                "d_70_m": float(config.priors.d_70.mean),
                "k_aq_mps": float(config.priors.k_aq.mean),
            }
        )
    anchor = next(r for r in per_section if r["kp"] == "62.0")
    others = [r for r in per_section if r["kp"] != "62.0"]
    return {
        "per_section": per_section,
        "elevation_over_others": sorted(
            anchor["median_H_c_m"] / r["median_H_c_m"] for r in others
        ),
        "residual_after_equalising_L": sorted(
            anchor["median_H_c_m"] / r["median_H_c_at_L_40m"] for r in others
        ),
        "length_share_of_log_elevation": sorted(
            math.log(r["length_factor"])
            / math.log(anchor["median_H_c_m"] / r["median_H_c_m"])
            for r in others
        ),
    }


def part_scour() -> dict:
    """Activation, accumulation and criterion for the corrected scour law."""
    from bep_reliability_engine.hydrographs import (
        build_hydrograph_record,
        load_rating_coefficients,
        normalize_stage_shape,
        rating_curve_path,
        read_discharge_ensemble,
        resolve_band_workbook,
    )
    from system_integration.uemura_models import (
        PSF_TO_PA,
        SCOUR_BED_ROUGHNESS_KB_M,
        SCOUR_K_CONVERSION_SCRIPT,
        SCOUR_K_CONVERSION_USACE,
        SCOUR_MANNING_N,
        SCOUR_MIN_DEPTH_M,
        SCOUR_TAU_C_COV,
        SCOUR_TAU_C_MEAN_PSF,
        draw_scour,
        load_segment_inputs,
    )

    data_root = REPO / "data" / "raw"
    segment_inputs = REPO / "data/processed/uemura_segments/segment_inputs.csv"
    inputs = load_segment_inputs(segment_inputs)

    def shear(stage: np.ndarray, seg) -> np.ndarray:
        depth = np.clip(
            stage - seg.floodplain_m_msl,
            0.0,
            seg.crest_design_m_msl - seg.floodplain_m_msl,
        )
        velocity = (
            (1.0 / SCOUR_MANNING_N)
            * depth ** (2.0 / 3.0)
            * seg.water_surface_slope**0.5
        )
        with np.errstate(divide="ignore"):
            log_term = np.log(30.0 * depth / SCOUR_BED_ROUGHNESS_KB_M)
        f_c = np.where(depth > 0.0, 2.0 * (2.5 * log_term) ** (-2.0), 0.0)
        tau = 0.5 * 1000.0 * f_c * velocity**2
        return np.where(stage < seg.floodplain_m_msl + SCOUR_MIN_DEPTH_M, 0.0, tau)

    bands: dict[Path, tuple] = {}
    rows: list[dict] = []
    for node_index, ((river, kp), seg) in enumerate(sorted(inputs.items())):
        workbook = resolve_band_workbook(
            data_root, river=river, kp=kp, scenario="historical"
        )
        if workbook not in bands:
            time_hours, members = read_discharge_ensemble(workbook)
            bands[workbook] = (time_hours, members[CANONICAL_EVENT])
        time_hours, discharge = bands[workbook]
        a_kp, b_kp = load_rating_coefficients(rating_curve_path(data_root, river))[kp]
        record = build_hydrograph_record(
            time_hours,
            discharge,
            a_kp=a_kp,
            b_kp=b_kp,
            scenario="historical",
            event_id=CANONICAL_EVENT,
            provenance={"kp": kp},
        )
        shape, h_base, _ = normalize_stage_shape(record.h)
        dt_s = float(record.native_dt)
        crest_mean = seg.crest_design_m_msl + seg.crest_err_mu_m
        lo = np.floor(max(seg.floodplain_m_msl, h_base) / LEVEL_STEP_M) * LEVEL_STEP_M
        levels = np.round(
            np.arange(
                lo,
                crest_mean + LEVEL_MARGIN_ABOVE_CREST_M + LEVEL_STEP_M / 2.0,
                LEVEL_STEP_M,
            ),
            6,
        )
        usace = draw_scour(
            np.random.default_rng(
                np.random.SeedSequence((SEED_ROOT, node_index, MECH_INDEX_SCOUR_USACE))
            ),
            N_MC,
            k_conversion=SCOUR_K_CONVERSION_USACE,
        )
        script = draw_scour(
            np.random.default_rng(
                np.random.SeedSequence((SEED_ROOT, node_index, MECH_INDEX_SCOUR_SCRIPT))
            ),
            N_MC,
            k_conversion=SCOUR_K_CONVERSION_SCRIPT,
        )

        tau_peak = 0.0
        best = (-1.0, None, -1.0, -1.0)  # max depth, level, mean depth, script depth
        best_at_crest = -1.0
        for level in levels:
            stage = (
                h_base + (level - h_base) * shape
                if level > h_base
                else np.full_like(shape, level)
            )
            tau = shear(stage, seg)
            tau_peak = max(tau_peak, float(np.max(tau)))
            loaded = stage > seg.ground_m_msl
            excess = np.maximum(0.0, tau[:, None] - usace.tau_c_pa[None, :])
            excess[~loaded, :] = 0.0
            depth = usace.k_si_per_hr_pa * np.sum(excess, axis=0) * dt_s / 3600.0
            excess_s = np.maximum(0.0, tau[:, None] - script.tau_c_pa[None, :])
            excess_s[~loaded, :] = 0.0
            depth_s = script.k_si_per_hr_pa * np.sum(excess_s, axis=0) * dt_s / 3600.0
            if float(np.max(depth)) > best[0]:
                best = (
                    float(np.max(depth)),
                    float(level),
                    float(np.mean(depth)),
                    float(np.max(depth_s)),
                )
            if level <= crest_mean:
                best_at_crest = max(best_at_crest, float(np.max(depth)))
        width_at_crest = seg.crest_width_m
        width_at_floodplain = (
            seg.crest_width_m
            + (seg.crest_design_m_msl - seg.floodplain_m_msl) * seg.slope_h_per_v
        )
        rows.append(
            {
                "river": river,
                "kp": kp,
                "tau_peak_pa": tau_peak,
                "fraction_draws_activated": float(np.mean(usace.tau_c_pa < tau_peak)),
                "max_depth_corrected_m": best[0],
                "max_depth_corrected_at_or_below_crest_m": best_at_crest,
                "mean_depth_corrected_m": best[2],
                "max_depth_as_received_m": best[3],
                "worst_level_m_msl": best[1],
                "crest_width_m": width_at_crest,
                "width_at_floodplain_m": width_at_floodplain,
            }
        )
        print(
            f"  {river} KP{kp:6.2f} tau_peak={tau_peak:7.2f} Pa "
            f"act={rows[-1]['fraction_draws_activated']:.4f} "
            f"depth={best[0]:.3f} m",
            flush=True,
        )

    activated = [r["fraction_draws_activated"] for r in rows]
    depths = [r["max_depth_corrected_m"] for r in rows]
    return {
        "n_segments": len(rows),
        "tau_c_mean_pa": SCOUR_TAU_C_MEAN_PSF * PSF_TO_PA,
        "tau_c_cov": SCOUR_TAU_C_COV,
        "tau_c_is_sampled": True,
        "k_conversion_corrected": SCOUR_K_CONVERSION_USACE,
        "k_conversion_as_received": SCOUR_K_CONVERSION_SCRIPT,
        "k_conversion_ratio": SCOUR_K_CONVERSION_SCRIPT / SCOUR_K_CONVERSION_USACE,
        "tau_peak_range_pa": [
            min(r["tau_peak_pa"] for r in rows),
            max(r["tau_peak_pa"] for r in rows),
        ],
        "tau_peak_median_pa": float(np.median([r["tau_peak_pa"] for r in rows])),
        "segments_with_activation": sum(1 for a in activated if a > 0.0),
        "activated_fraction_range": [min(activated), max(activated)],
        "activated_fraction_median": float(np.median(activated)),
        "max_depth_corrected_range_m": [min(depths), max(depths)],
        "max_depth_corrected_median_m": float(np.median(depths)),
        "mean_depth_corrected_range_m": [
            min(r["mean_depth_corrected_m"] for r in rows),
            max(r["mean_depth_corrected_m"] for r in rows),
        ],
        "max_depth_as_received_m": max(r["max_depth_as_received_m"] for r in rows),
        "width_range_m": [
            min(r["crest_width_m"] for r in rows),
            max(r["width_at_floodplain_m"] for r in rows),
        ],
        "largest_depth_to_width_ratio": max(
            r["max_depth_corrected_m"] / r["crest_width_m"] for r in rows
        ),
        "segments": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--part",
        default="all",
        choices=("all", "gradients", "scaling", "contrast", "scour"),
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    payload: dict = {"driver": "scripts/physical_model_qualifications.py"}
    if args.part in ("all", "gradients"):
        print("gradients ...", flush=True)
        payload["gradients"] = part_gradients()
    if args.part in ("all", "scaling"):
        print("scaling ...", flush=True)
        payload["scaling"] = part_scaling()
    if args.part in ("all", "contrast"):
        print("contrast ...", flush=True)
        payload["contrast"] = part_contrast()
    if args.part in ("all", "scour"):
        print("scour ...", flush=True)
        payload["scour"] = part_scour()

    text = json.dumps(payload, indent=1, sort_keys=False)
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
