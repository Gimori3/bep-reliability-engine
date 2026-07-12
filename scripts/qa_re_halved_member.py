"""KP58.8 r_e-halved QA sensitivity member (registered 2026-07-11; ADR-0032 scope).

Realizes the QA member registered in the ``run_sweep.py`` header and
``docs/validation/shikaga-case.md`` sec. 3 item 4: one harness-level rerun of
the KP58.8 matrix production member with the M4 response factor halved
(r_e -> r_e / 2), converting the Japanese case-validation shoulder bound
(M4 over-translation 1.15-2.7x at FEM-calibrated sites) into a measured
delta-P_f per conditioning level.

Design (per the registration text; r_e is derived per realization, never a
config field, so this is a harness-level run in the style of
``scripts/validate_*.py``, NOT a generated sweep member):

* The persisted KP58.8 matrix run is loaded through the Phase 2 loader
  (``load_phase1_run``: config hash-checked, theta regenerated bit-for-bit,
  stochastic L regenerated through the public run.py seam), so the QA member
  filters exactly the production population against exactly the production
  conditioning records (``run.conditioning_hydrographs_for_config``).
* The M8 preamble is mirrored here through the public M4/M6 kernels
  (``compute_critical_head_vectorized``, ``leakage_length_in/out``,
  ``response_factor``) and the M7 timestepper is driven through
  ``InstantaneousHead(scale * r_e, z_toe)`` + ``integrate_progression``.
* DRIFT GUARD: the scale = 1.0 branch must reproduce the persisted
  ``failure_matrix_trans`` column bit-for-bit at every level (and the static
  branch is r_e-independent, so it is not recomputed at all). A mismatch
  aborts the run - the mirror is then stale against M8 and the QA numbers
  would be meaningless.
* Since ADR-0027/0028 r_e drives ONLY the uplift/heave gate, so the halved
  member measures gate sensitivity: fewer/later I_er latches, hence a pure
  one-sided reduction of P_f,trans (rows that never latch never erode).

Expected direction (registration text): standard r_e is the conservative
side; the halved member bounds how much of the shoulder is
M4-translation-sensitive.

Usage (repo root, venv active; needs results/tokachi_kp58.8_historical_matrix.h5)::

    python scripts/qa_re_halved_member.py

Output: ``results/qa_re_halved_kp58_8.json`` (per-level P_f baseline vs
halved with Clopper-Pearson 95% CIs) and a console table.
"""

from __future__ import annotations

import datetime as _dt
import json
import time
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from bayesian_reliability_updating.replay import Phase1Run, load_phase1_run
from bep_reliability_engine.fragility import binomial_ci
from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    leakage_length_in,
    leakage_length_out,
    response_factor,
)
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.progression import integrate_progression
from bep_reliability_engine.run import conditioning_hydrographs_for_config
from bep_reliability_engine.sellmeijer import compute_critical_head_vectorized

REPO = Path(__file__).resolve().parents[1]
SOURCE_H5 = REPO / "results" / "tokachi_kp58.8_historical_matrix.h5"
OUT_JSON = REPO / "results" / "qa_re_halved_kp58_8.json"

R_E_SCALE_QA = 0.5  # the registered sensitivity: r_e -> r_e / 2


def transient_failures_for_scale(
    run: Phase1Run,
    record: HydrographRecord,
    r_e_scale: float,
) -> NDArray[np.bool_]:
    """One conditioning level's transient failure column at ``r_e_scale``.

    Mirrors the transient branch of ``evaluate_batch_diagnostics`` exactly
    (same kernels, same argument threading, numpy backend) with the single
    intervention ``r_e -> r_e_scale * r_e`` applied between the M4 preamble
    and the M7 head model. ``r_e_scale = 1.0`` must therefore be bit-identical
    to the production sweep column - the caller asserts that.
    """
    config = run.config
    theta = run.theta
    geometry = run.geometry
    z_toe_m = float(geometry["z_toe"])

    if run.seepage_length_samples is None:
        seepage_length: float | NDArray[np.float64] = float(geometry["L"])
        geometry_for_hc = geometry
    else:
        seepage_length = run.seepage_length_samples
        geometry_for_hc = {**geometry, "L": seepage_length}

    sellmeijer = compute_critical_head_vectorized(
        theta,
        geometry_for_hc,
        alpha_exponent=config.alpha_exponent,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
    )
    h_c = np.asarray(sellmeijer.H_c, dtype=np.float64)
    l_c = np.asarray(sellmeijer.l_c, dtype=np.float64)

    lambda_in = leakage_length_in(theta[:, 0], theta[:, 2], theta[:, 3], theta[:, 4])
    lambda_out_eff = leakage_length_out(
        theta[:, 0],
        theta[:, 2],
        geometry["D_fore"],
        geometry["k_fore"],
        geometry["foreshore_width"],
    )
    if config.foreland_treatment == "open_entry":
        lambda_out_eff = np.zeros_like(lambda_out_eff)
    r_e = r_e_scale * response_factor(lambda_in, lambda_out_eff, seepage_length)

    head_model = InstantaneousHead(r_e, z_toe_m)
    progression = integrate_progression(
        np.asarray(record.h, dtype=np.float64),
        float(record.native_dt),
        head_model,
        z_toe_m,
        c_e=theta[:, 6],
        k_aq_mps=theta[:, 0],
        d_bl_m=theta[:, 3],
        gamma_bl_sub_knpm3=theta[:, 5],
        h_c_m=h_c,
        l_c_m=l_c,
        seepage_length_m=seepage_length,
        l_ini_m=0.0,
        store_trajectory=False,
    )
    z_transient = seepage_length - np.asarray(progression.l_final_m, dtype=np.float64)
    return np.asarray(z_transient <= 0.0, dtype=bool)


def main() -> None:
    t0 = time.perf_counter()
    run = load_phase1_run(SOURCE_H5)
    if run.config.alpha_exponent_transient is not None:
        raise SystemExit(
            "QA member assumes the single-source H_c baseline "
            "(alpha_exponent_transient unset); the mirror does not thread "
            "the ADR-0017 decomposition."
        )
    if run.config.timestepper.progression_backend != "numpy":
        raise SystemExit(
            "QA member mirrors the numpy reference backend; the source run "
            f"used {run.config.timestepper.progression_backend!r}."
        )
    records = conditioning_hydrographs_for_config(run.config)
    grid = [float(rec.peak) for rec in records]
    n = run.n_samples

    per_level: list[dict[str, float]] = []
    print(
        f"KP58.8 r_e-halved QA member: N={n}, {len(records)} levels "
        f"(baseline drift guard + halved member per level)"
    )
    header = (
        f"{'level_m_msl':>11s} {'P_f_base':>10s} {'P_f_halved':>10s} "
        f"{'delta_P_f':>10s} {'ratio':>7s}"
    )
    print(header)
    for j, record in enumerate(records):
        baseline = transient_failures_for_scale(run, record, 1.0)
        persisted = np.asarray(run.result.failure_matrix_tran[:, j], dtype=bool)
        if not np.array_equal(baseline, persisted):
            raise SystemExit(
                f"DRIFT GUARD FAILED at level {grid[j]} m: the scale=1.0 "
                "mirror does not reproduce the persisted production column; "
                "the harness is stale against M8. Aborting."
            )
        halved = transient_failures_for_scale(run, record, R_E_SCALE_QA)
        extra = halved & ~baseline
        if np.any(extra):
            raise SystemExit(
                f"Level {grid[j]} m: halving r_e produced {int(extra.sum())} "
                "NEW transient failures - physically impossible (r_e drives "
                "only the gate); the harness is broken. Aborting."
            )
        p_base = float(baseline.mean())
        p_half = float(halved.mean())
        lo_b, hi_b = binomial_ci(np.asarray([p_base]), n, 0.95)
        lo_h, hi_h = binomial_ci(np.asarray([p_half]), n, 0.95)
        ratio = p_half / p_base if p_base > 0.0 else float("nan")
        per_level.append(
            {
                "level_m_msl": grid[j],
                "p_f_trans_baseline": p_base,
                "p_f_trans_baseline_ci95": [float(lo_b[0]), float(hi_b[0])],
                "p_f_trans_re_halved": p_half,
                "p_f_trans_re_halved_ci95": [float(lo_h[0]), float(hi_h[0])],
                "delta_p_f": p_half - p_base,
                "ratio_halved_over_baseline": ratio,
                "n_failures_baseline": int(baseline.sum()),
                "n_failures_re_halved": int(halved.sum()),
            }
        )
        print(
            f"{grid[j]:11.2f} {p_base:10.5f} {p_half:10.5f} "
            f"{p_half - p_base:+10.5f} {ratio:7.3f}"
        )

    payload = {
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "purpose": (
            "Registered KP58.8 r_e-halved QA sensitivity member (ADR-0032 "
            "scope amendment; shikaga-case.md sec. 3 item 4; run_sweep.py "
            "header). Measures the M4-translation sensitivity of the "
            "transient fragility through the uplift/heave gate (the only "
            "r_e consumer since ADR-0027/0028)."
        ),
        "source_h5": SOURCE_H5.name,
        "source_h5_sha256": run.h5_sha256,
        "config_hash": run.config.config_hash(),
        "theta_verified": run.theta_verified,
        "n_realizations": n,
        "r_e_scale": R_E_SCALE_QA,
        "baseline_drift_guard": "bit-identical at every level",
        "static_branch": "r_e-independent (ADR-0028); unchanged by construction",
        "per_level": per_level,
        "runtime_seconds": time.perf_counter() - t0,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT_JSON.relative_to(REPO)} in {payload['runtime_seconds']:.1f} s")


if __name__ == "__main__":
    main()
