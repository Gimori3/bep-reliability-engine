"""The spec §12 fm5 tail-variance study: LHS vs crude MC vs tilted IS.

Empirically verifies (or refutes) the LHS tail-variance claim of spec §12
failure mode 5 on the real production physics: the deep transient failure
tail is governed by the multiplicative C_e x k_aq interaction (fm7), LHS
stratifies marginals only, so the assumed LHS CoV advantage over crude Monte
Carlo must be *measured* on the failure tail at the reduced operating N —
and the ADR-0029 tilted importance sampler is measured alongside as the
targeted alternative for the lowest conditioning levels.

Protocol (all reproducible from the config seed):

1. KP58.8 historical/matrix config, canonical d4PDF shape, N_study = 1e4
   (the fm5 "reduced N" at which sensitivity and cross-section sweeps run).
2. A cross-entropy pilot at a bulk level seeds the Z-space shift; the shift
   is then re-tuned level by level (staged CE) as the study descends into
   the tail.
3. Study levels are chosen from the production conditioning grid to hit
   transient P_f ~ {bulk, 1e-2, 1e-3, 1e-4} (probed with the tilted
   estimator, which is precise where raw MC is blind).
4. Per level, R replicates of three estimators at identical N (the same
   independently drawn stochastic L per replicate index, so the schemes
   differ only in the theta design):
   * LHS      — M2-style stratified draw, raw failure fraction;
   * crude MC — iid draw (the spec §13 debug fallback), raw fraction;
   * IS       — LHS-stratified tilted draw, weighted estimate.
5. Reported per (level, scheme): replicate-mean P_f, empirical replicate
   CoV (the ground-truth precision), the mean analytic within-run CoV, the
   fraction of replicates with zero observed failures, and the IS Kish
   effective failure count.

The transient branch is evaluated with the ADR-0029 numba backend (cross-
backend failure indicators are identical at production scale; the numpy
default remains the reference engine). Results go to
``docs/decisions/adr0029-tail-cov-study.json`` and a figure in
``docs/figures/``; the companion note
``docs/decisions/adr0029-tail-variance-study.md`` interprets them.

Run from the repository root::

    python scripts/tail_variance_study.py [--n 10000] [--replicates 40]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.evaluator import evaluate_batch  # noqa: E402
from bep_reliability_engine.run import (  # noqa: E402
    _hydrograph_for_level,
    _load_canonical_or_none,
)
from bep_reliability_engine.sampling import sample_seepage_length  # noqa: E402
from bep_reliability_engine.tail_sampling import (  # noqa: E402
    cross_entropy_shift,
    importance_estimate,
    sample_theta_tilted,
)

CONFIG_PATH = REPO_ROOT / "configs" / "kp58_8_historical_matrix.yaml"
OUTPUT_JSON = REPO_ROOT / "docs" / "decisions" / "adr0029-tail-cov-study.json"
OUTPUT_FIGURE = REPO_ROOT / "docs" / "figures" / "adr0029-tail-cov.png"

# Target raw transient failure probabilities for the study levels: one bulk
# anchor plus three tail decades.
P_TARGETS = [0.3, 1.0e-2, 1.0e-3, 1.0e-4]

# Seed-derivation tags (SeedSequence entropy words) so every draw is distinct
# and reproducible from the config seed alone.
_TAG_THETA = 0x7E7A
_TAG_LENGTH = 0x5EE9
_TAG_PILOT = 0xCE01


def _study_seed(base: int, *words: int) -> int:
    return int(np.random.SeedSequence([base, *words]).generate_state(1)[0])


def _evaluate(theta_sample, seepage, record, geometry, cfg) -> np.ndarray:
    """Transient failure indicators for one draw at one level (M8 batch)."""
    _, failure_trans = evaluate_batch(
        theta_sample.theta_matrix,
        record,
        geometry,
        l_ini=0.0,
        seepage_length_samples=seepage,
        alpha_exponent=cfg.alpha_exponent,
        alpha_exponent_transient=cfg.alpha_exponent_transient,
        theta_repose_rad=cfg.theta_repose_rad,
        relative_density=cfg.relative_density_insitu,
        foreland_open=cfg.foreland_treatment == "open_entry",
        progression_backend="numba",
    )
    return failure_trans


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=10_000, help="operating N")
    parser.add_argument("--replicates", type=int, default=40)
    args = parser.parse_args()
    n_study, n_replicates = args.n, args.replicates

    cfg = Config.from_yaml(CONFIG_PATH)
    base_seed = int(cfg.mc.seed)
    canonical = _load_canonical_or_none(cfg)
    geometry = cfg.geometry.as_evaluator_dict()
    grid = np.asarray(cfg.mc.conditioning_grid, dtype=np.float64)

    marginals = cfg.priors.to_marginal_specs()
    sampler_kwargs = dict(
        rho_log_kaq_d70=cfg.correlation.rho_log_kaq_d70,
        d70_interpretation=cfg.priors.d70_interpretation,
        coupling=cfg.correlation.coupling,
        bounds=cfg.priors.bounds,
    )

    def draw_length(seed_words: tuple[int, ...]) -> np.ndarray | None:
        if cfg.seepage_length_cov is None:
            return None
        return sample_seepage_length(
            cfg.geometry.L,
            cfg.seepage_length_cov,
            seed=_study_seed(base_seed, _TAG_LENGTH, *seed_words),
            n_samples=n_study,
        )

    t_start = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. Cross-entropy pilot at a bulk level (plenty of failures), then a
    #    tilted probe of the production grid to place the study levels.
    # ------------------------------------------------------------------
    pilot_level = float(grid[len(grid) // 2])
    pilot = sample_theta_tilted(
        marginals,
        seed=_study_seed(base_seed, _TAG_PILOT, 0),
        n_samples=n_study,
        shift_z=None,
        **sampler_kwargs,
    )
    pilot_length = draw_length((0xB, 0))
    record = _hydrograph_for_level(pilot_level, cfg, canonical)
    pilot_fail = _evaluate(pilot.theta, pilot_length, record, geometry, cfg)
    shift = cross_entropy_shift(pilot, pilot_fail)
    print(
        f"CE pilot at h = {pilot_level} m: P_f ~ {pilot_fail.mean():.3f}, "
        f"shift = {{k_aq: {shift['k_aq']:.2f}, C_e: {shift['C_e']:.2f}}}"
    )

    # The probe uses a deliberately strong shift (deep-tail reach matters
    # more than bulk n_eff here — the weights keep every estimate unbiased)
    # and refines OFF-GRID levels where the production grid's 0.25 m spacing
    # jumps over a whole target decade. Study levels need not be sweep
    # members: _hydrograph_for_level is a pure function of any stage.
    probe_shift = {k: max(2.0, v) for k, v in shift.items()}
    probe = sample_theta_tilted(
        marginals,
        seed=_study_seed(base_seed, _TAG_PILOT, 1),
        n_samples=n_study,
        shift_z=probe_shift,
        **sampler_kwargs,
    )
    probe_length = draw_length((0xB, 1))

    def probe_level(level: float) -> float:
        record = _hydrograph_for_level(float(level), cfg, canonical)
        fail = _evaluate(probe.theta, probe_length, record, geometry, cfg)
        return importance_estimate(fail, probe.log_weights).p_f

    probe_p: dict[float, float] = {float(lvl): probe_level(float(lvl)) for lvl in grid}

    def nearest(target: float, taken: list[float]) -> tuple[float, float]:
        candidates = {
            lvl: p for lvl, p in probe_p.items() if p > 0.0 and lvl not in taken
        }
        level = min(
            candidates, key=lambda lvl: abs(np.log(candidates[lvl]) - np.log(target))
        )
        return level, candidates[level]

    study_levels: list[float] = []
    for target in P_TARGETS:
        level, p = nearest(target, study_levels)
        # Off-grid refinement: bisect toward the target decade when the grid
        # overshoots it by more than a factor 3 (up to 4 bisections).
        for _ in range(4):
            if abs(np.log(p) - np.log(target)) <= np.log(3.0):
                break
            below = [lvl for lvl in probe_p if lvl < level]
            above = [lvl for lvl in probe_p if lvl > level]
            neighbor = max(below) if p > target else min(above)
            midpoint = round(0.5 * (level + neighbor), 3)
            if midpoint in probe_p:
                break
            probe_p[midpoint] = probe_level(midpoint)
            level, p = nearest(target, study_levels)
        study_levels.append(level)

    # Shallow -> deep: the staged CE re-tune below descends into the tail.
    study_levels.sort(key=lambda lvl: -probe_p[lvl])
    print(
        "probe P_f_trans:", {f"{k:g}": f"{v:.2e}" for k, v in sorted(probe_p.items())}
    )
    print(f"study levels: {study_levels} (targets {P_TARGETS})\n")

    # ------------------------------------------------------------------
    # 2. Replicated estimators per level (staged CE re-tune per level).
    # ------------------------------------------------------------------
    results: list[dict] = []
    for level_index, level in enumerate(study_levels):
        record = _hydrograph_for_level(float(level), cfg, canonical)

        # Stage the CE shift into this level's own failure region.
        tune = sample_theta_tilted(
            marginals,
            seed=_study_seed(base_seed, _TAG_PILOT, 2, level_index),
            n_samples=n_study,
            shift_z=shift,
            **sampler_kwargs,
        )
        tune_length = draw_length((0xC, level_index))
        tune_fail = _evaluate(tune.theta, tune_length, record, geometry, cfg)
        if tune_fail.any():
            shift = cross_entropy_shift(tune, tune_fail)

        rows = {"lhs": [], "mc": [], "is": []}
        analytic_cov = {"lhs": [], "mc": [], "is": []}
        n_eff_is: list[float] = []
        for r in range(n_replicates):
            seepage = draw_length((level_index, r))
            common = dict(n_samples=n_study, **sampler_kwargs)

            lhs = sample_theta_tilted(
                marginals,
                seed=_study_seed(base_seed, _TAG_THETA, level_index, r, 0),
                shift_z=None,
                stratified=True,
                **common,
            )
            est = importance_estimate(
                _evaluate(lhs.theta, seepage, record, geometry, cfg),
                lhs.log_weights,
            )
            rows["lhs"].append(est.p_f)
            analytic_cov["lhs"].append(est.cov)

            mc = sample_theta_tilted(
                marginals,
                seed=_study_seed(base_seed, _TAG_THETA, level_index, r, 1),
                shift_z=None,
                stratified=False,
                **common,
            )
            est = importance_estimate(
                _evaluate(mc.theta, seepage, record, geometry, cfg),
                mc.log_weights,
            )
            rows["mc"].append(est.p_f)
            analytic_cov["mc"].append(est.cov)

            tilted = sample_theta_tilted(
                marginals,
                seed=_study_seed(base_seed, _TAG_THETA, level_index, r, 2),
                shift_z=shift,
                stratified=True,
                **common,
            )
            est = importance_estimate(
                _evaluate(tilted.theta, seepage, record, geometry, cfg),
                tilted.log_weights,
            )
            rows["is"].append(est.p_f)
            analytic_cov["is"].append(est.cov)
            n_eff_is.append(est.n_effective)

        level_result = {
            "level_m": float(level),
            "shift_z": {k: float(v) for k, v in shift.items()},
            "schemes": {},
        }
        for scheme in ("lhs", "mc", "is"):
            p = np.asarray(rows[scheme], dtype=np.float64)
            mean_p = float(p.mean())
            emp_cov = float(p.std(ddof=1) / mean_p) if mean_p > 0.0 else float("nan")
            finite_cov = [c for c in analytic_cov[scheme] if np.isfinite(c)]
            level_result["schemes"][scheme] = {
                "mean_p_f": mean_p,
                "empirical_cov": emp_cov,
                "mean_analytic_cov": (
                    float(np.mean(finite_cov)) if finite_cov else float("nan")
                ),
                "zero_failure_fraction": float(np.mean(p == 0.0)),
            }
        level_result["schemes"]["is"]["mean_n_effective"] = float(np.nanmean(n_eff_is))
        lhs_cov = level_result["schemes"]["lhs"]["empirical_cov"]
        mc_cov = level_result["schemes"]["mc"]["empirical_cov"]
        is_cov = level_result["schemes"]["is"]["empirical_cov"]
        level_result["cov_ratio_mc_over_lhs"] = (
            float(mc_cov / lhs_cov) if np.isfinite(mc_cov * lhs_cov) else float("nan")
        )
        level_result["cov_ratio_mc_over_is"] = (
            float(mc_cov / is_cov) if np.isfinite(mc_cov * is_cov) else float("nan")
        )
        results.append(level_result)

        print(
            f"h = {level:6.2f} m | "
            f"P_f: LHS {level_result['schemes']['lhs']['mean_p_f']:.2e} / "
            f"MC {level_result['schemes']['mc']['mean_p_f']:.2e} / "
            f"IS {level_result['schemes']['is']['mean_p_f']:.2e} | "
            f"emp. CoV: LHS {lhs_cov:.3f} / MC {mc_cov:.3f} / IS {is_cov:.3f} | "
            f"MC/LHS {level_result['cov_ratio_mc_over_lhs']:.2f} "
            f"MC/IS {level_result['cov_ratio_mc_over_is']:.2f}"
        )

    runtime = time.perf_counter() - t_start

    payload = {
        "study": "spec §12 fm5 tail-variance verification (ADR-0029)",
        "config": str(CONFIG_PATH.name),
        "config_hash": cfg.config_hash(),
        "hydrograph_source": "d4pdf_scaled_canonical",
        "progression_backend": "numba",
        "n_study": n_study,
        "n_replicates": n_replicates,
        "base_seed": base_seed,
        "pilot_level_m": pilot_level,
        "probe_p_f_trans": {f"{k:g}": v for k, v in probe_p.items()},
        "runtime_seconds": runtime,
        "levels": results,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {OUTPUT_JSON} ({runtime:.0f} s)")

    _plot(results, n_study, n_replicates)


def _plot(results: list[dict], n_study: int, n_replicates: int) -> None:
    """Empirical replicate CoV per scheme against the tail depth."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    p_axis = [r["schemes"]["lhs"]["mean_p_f"] for r in results]
    styles = {
        "lhs": ("o-", "tab:blue", "LHS (production sampler)"),
        "mc": ("s--", "tab:gray", "crude Monte Carlo"),
        "is": ("^-", "tab:red", "tilted importance sampling"),
    }
    for scheme, (fmt, color, label) in styles.items():
        cov = [r["schemes"][scheme]["empirical_cov"] for r in results]
        ax.loglog(p_axis, cov, fmt, color=color, label=label)
    ax.invert_xaxis()
    ax.set_xlabel(r"transient failure probability $P_f$ (deeper tail $\rightarrow$)")
    ax.set_ylabel(r"empirical replicate CoV of $\hat{P}_f$")
    ax.set_title(
        f"Tail-variance study: KP 58.8, N = {n_study:,}, "
        f"R = {n_replicates} replicates"
    )
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    OUTPUT_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIGURE, dpi=160)
    print(f"wrote {OUTPUT_FIGURE}")


if __name__ == "__main__":
    main()
