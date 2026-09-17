"""Does the ADR-0024 interval cover under the production LHS design? (F5)

Every raw fragility point is delivered with a two-sided 95 per cent
Clopper-Pearson interval. Its endpoints are exact functions of the count, but
the ``>= 1 - alpha`` coverage guarantee behind the word "exact" is derived from
``K ~ Binomial(n, p)``, and the production sample is a randomized Latin
hypercube whose **rows are dependent**. Two things are already known and
neither settles it:

* the estimator is **exactly unbiased** under LHS, because with scipy's
  scrambled design each row's coordinate is ``(perm_i(j) - 1 + U_ij)/n`` with
  ``perm`` uniform and independent of ``U``, so every row is marginally the
  target distribution;
* ADR-0031 measured the estimator's **dispersion** over 50 replicate designs.

Coverage is a different functional of the same law, so it is measured here,
under a decision rule fixed before the first replicate was drawn
(``.codex/remediation/2026-09-14/S05-preedit-verdicts.md``, reproduced in
``docs/decisions/binomial-interval-coverage-study.md``).

Design
------
Two arms at the same conditioning levels, both reusing
:func:`bep_reliability_engine.convergence.run_replicates`:

* **production** -- ``sample_theta_tilted(shift_z=None, stratified=True)``,
  which is bit-identical to M2 ``sample_theta``, plus the production 1-D LHS
  seepage length. Replicates differ only in seed.
* **iid control** -- the same pipeline with ``stratified=False`` and an iid
  seepage length drawn from the identical moment-matched lognormal. Its rows
  are independent, so its count IS binomial and its measured coverage
  validates the apparatus. If the control fails, the study is void.

Sections KP 58.8 and KP 60.0 (matrix), the two ADR-0031 chose because their
fragility transitions are bracketed, at that study's own four conditioning
levels spanning bulk to deep tail. Both branches. The reference probability is
the **leave-one-out** mean of the other replicates in the same arm, so no
replicate is tested against a target that contains it.

The numba progression backend is used for speed, as ADR-0031 did. A
pre-registered gate re-evaluates one replicate on the numpy production backend
and requires the failure **indicators** to agree exactly.

Run from the repository root (venv active)::

    python scripts/interval_coverage_study.py                       # KP 58.8
    python scripts/interval_coverage_study.py --config kp60_0_historical_matrix.yaml \
        --levels 42.75,42.00,41.50,41.25
    python scripts/interval_coverage_study.py --replicates 20       # quick check

Outputs::

    results/convergence/<slug>_interval_coverage.json      working record
    docs/decisions/binomial-interval-coverage-<slug>.json  tracked record
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.convergence import (  # noqa: E402
    ReplicateSample,
    binomial_cov,
    coverage_lower_limit,
    interval_coverage,
    run_replicates,
)
from bep_reliability_engine.evaluator import evaluate_batch  # noqa: E402
from bep_reliability_engine.run import (  # noqa: E402
    _hydrograph_for_level,
    _load_canonical_or_none,
)
from bep_reliability_engine.sampling import sample_seepage_length  # noqa: E402
from bep_reliability_engine.tail_sampling import sample_theta_tilted  # noqa: E402

DEFAULT_CONFIG_NAME = "kp58_8_historical_matrix.yaml"
#: The ADR-0031 conditioning levels, reused so the coverage record sits on the
#: same bulk -> deep-tail ladder the dispersion record was measured on.
DEFAULT_LEVELS = [41.00, 40.25, 40.00, 39.75]
DEFAULT_REPLICATES = 800
N_SAMPLES = 100_000
BACKEND = "numba"
CONFIDENCE = 0.95

#: Pre-registered decision rule. A cell passes when the one-sided 95 per cent
#: lower confidence limit on its measured coverage is at or above this value.
#: Fixed before any replicate was drawn; it is the resolution R buys, not a
#: threshold chosen to admit a result.
COVERAGE_LOWER_LIMIT_FLOOR = 0.90

# Seed-stream tags, distinct from the ADR-0031 study's so the two records never
# share a draw. The seepage-length stream is keyed on (arm, level, replicate).
_TAG_PROD = 0x0C05
_TAG_IID = 0x0C1D
_TAG_LENGTH = 0x0C5E


def _slug(config_path: Path) -> str:
    return config_path.stem.replace("_historical", "")


def _output_paths(config_path: Path) -> dict[str, Path]:
    slug = _slug(config_path)
    return {
        "json": REPO_ROOT
        / "results"
        / "convergence"
        / f"{slug}_interval_coverage.json",
        "tracked_json": REPO_ROOT
        / "docs"
        / "decisions"
        / f"binomial-interval-coverage-{slug}.json",
    }


def _make_evaluate(record, geometry, cfg, backend: str = BACKEND):
    """One M8 ``evaluate_batch`` at a fixed conditioning level."""

    def evaluate(theta_sample, seepage):
        return evaluate_batch(
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
            progression_backend=backend,
        )

    return evaluate


def _iid_seepage_length(mean_m: float, cov: float, *, seed: int, n_samples: int):
    """Independent seepage-length draws, moment-matched exactly as M2's.

    ``sample_seepage_length`` is a 1-D Latin hypercube, so the production arm's
    L column is stratified too. The control arm has to replace it with an
    independent draw, or its rows are not independent either and it stops being
    a binomial reference. The moment matching is copied verbatim from
    :func:`bep_reliability_engine.sampling.sample_seepage_length`, so the two
    arms differ in the design and in nothing else.
    """
    sigma_ln = float(np.sqrt(np.log(1.0 + cov**2)))
    mu_ln = float(np.log(mean_m) - 0.5 * sigma_ln**2)
    z = np.random.default_rng(seed).standard_normal(n_samples)
    return np.exp(mu_ln + sigma_ln * z)


def _make_draw_length(cfg, base_seed: int, level_index: int, *, stratified: bool):
    """Per-replicate seepage-length draw for one arm."""
    arm_tag = _TAG_PROD if stratified else _TAG_IID

    def draw_length(replicate_index: int, n_samples: int):
        if cfg.seepage_length_cov is None:
            return None
        seed = int(
            np.random.SeedSequence(
                [base_seed, _TAG_LENGTH, arm_tag, level_index, replicate_index]
            ).generate_state(1)[0]
        )
        if stratified:
            return sample_seepage_length(
                cfg.geometry.L, cfg.seepage_length_cov, seed=seed, n_samples=n_samples
            )
        return _iid_seepage_length(
            cfg.geometry.L, cfg.seepage_length_cov, seed=seed, n_samples=n_samples
        )

    return draw_length


def _leave_one_out(values: np.ndarray) -> np.ndarray:
    """Mean of every element except the one at each position."""
    v = np.asarray(values, dtype=np.float64)
    total = v.sum()
    return (total - v) / (v.size - 1)


def _branch_block(sample: ReplicateSample, branch: str) -> dict:
    """Coverage, dispersion and verdict for one (arm, level, branch) cell."""
    counts = (
        sample.n_failures_static if branch == "static" else sample.n_failures_trans
    ).astype(np.int64)
    fractions = sample.p_f_static if branch == "static" else sample.p_f_trans
    n = int(sample.n_samples)
    p_ref = _leave_one_out(fractions)

    cov_stats = interval_coverage(counts, n, p_ref, confidence=CONFIDENCE)
    lower_limit = coverage_lower_limit(
        cov_stats["n_covered"], cov_stats["n_replicates"], confidence=CONFIDENCE
    )
    mean_p = float(np.mean(fractions))
    var_counts = float(np.var(counts.astype(np.float64), ddof=1))
    var_binomial = n * mean_p * (1.0 - mean_p)
    return {
        "mean_p_f": mean_p,
        "mean_count": float(np.mean(counts)),
        "zero_failure_fraction": float(np.mean(counts == 0)),
        "empirical_cov": sample.cov(branch),
        "binomial_cov": binomial_cov(mean_p, n),
        "var_counts": var_counts,
        "var_binomial": var_binomial,
        "var_ratio": (var_counts / var_binomial) if var_binomial > 0 else float("nan"),
        "coverage": cov_stats["coverage"],
        "n_covered": cov_stats["n_covered"],
        "n_replicates": cov_stats["n_replicates"],
        "miss_low": cov_stats["miss_low"],
        "miss_high": cov_stats["miss_high"],
        "mean_interval_width": cov_stats["mean_width"],
        "coverage_lower_limit_95": lower_limit,
        "passes_rule": bool(lower_limit >= COVERAGE_LOWER_LIMIT_FLOOR),
        "counts": [int(c) for c in counts],
    }


def _paired_bootstrap_block(sample: ReplicateSample, n_bootstrap: int = 1000) -> dict:
    """Coverage of the paired row bootstrap on ``dbeta``, over the same replicates.

    The row bootstrap resamples rows with replacement, which treats them as
    independent. Under a randomized Latin hypercube they are not, so the same
    question the Clopper-Pearson interval raises is raised here, for the
    interval the headline ``dbeta`` is actually quoted with.

    It costs no extra physics. The transient failure set is contained in the
    static one on every row the engine reaches (a theorem, and measured at zero
    violations in 24 million row evaluations), so a replicate's joint pattern
    counts are fixed by its two marginal counts: ``k_t`` rows fail both,
    ``k_s - k_t`` fail only the static branch, ``n - k_s`` fail neither and the
    transient-only cell is empty. The multinomial resample of those three
    patterns is distributionally identical to resampling ``n`` row indices,
    which is exactly ``rq1_beta_analysis.paired_bootstrap_means``.
    """
    k_static = sample.n_failures_static.astype(np.int64)
    k_trans = sample.n_failures_trans.astype(np.int64)
    n = int(sample.n_samples)
    nesting_violations = int(np.count_nonzero(k_trans > k_static))

    p_s_ref = _leave_one_out(k_static / n)
    p_t_ref = _leave_one_out(k_trans / n)
    with np.errstate(divide="ignore"):
        dbeta_ref = -norm.ppf(p_t_ref) + norm.ppf(p_s_ref)

    rng = np.random.default_rng(20260917)
    covered = np.zeros(k_static.size, dtype=bool)
    reportable = np.zeros(k_static.size, dtype=bool)
    widths = np.full(k_static.size, np.nan)
    for r in range(k_static.size):
        ks, kt = int(k_static[r]), int(k_trans[r])
        if kt < 1 or ks <= kt:
            continue  # no finite interval: the R1 floor exists for this reason
        pvals = [(n - ks) / n, (ks - kt) / n, kt / n]
        draws = rng.multinomial(n, pvals, size=n_bootstrap)
        ks_star = (draws[:, 1] + draws[:, 2]) / n
        kt_star = draws[:, 2] / n
        finite = (kt_star > 0) & (ks_star < 1.0)
        if finite.sum() < 0.5 * n_bootstrap:
            continue
        with np.errstate(divide="ignore"):
            d_star = -norm.ppf(kt_star[finite]) + norm.ppf(ks_star[finite])
        lo, hi = np.percentile(d_star, [2.5, 97.5])
        reportable[r] = True
        widths[r] = hi - lo
        covered[r] = bool(lo <= dbeta_ref[r] <= hi)

    n_reportable = int(reportable.sum())
    n_covered = int(covered[reportable].sum())
    lower_limit = (
        coverage_lower_limit(n_covered, n_reportable, confidence=CONFIDENCE)
        if n_reportable > 0
        else float("nan")
    )
    return {
        "n_bootstrap": int(n_bootstrap),
        "n_reportable": n_reportable,
        "n_covered": n_covered,
        "coverage": (n_covered / n_reportable) if n_reportable else float("nan"),
        "coverage_lower_limit_95": lower_limit,
        "passes_rule": bool(
            n_reportable > 0 and lower_limit >= COVERAGE_LOWER_LIMIT_FLOOR
        ),
        "mean_interval_width": float(np.nanmean(widths)) if n_reportable else None,
        "mean_delta_beta": (
            float(np.mean(dbeta_ref[reportable])) if n_reportable else None
        ),
        "nesting_violations": nesting_violations,
    }


def _backend_gate(cfg, canonical, geometry, marginals, sampler_kwargs, level) -> dict:
    """One replicate on both backends: the failure indicators must agree."""
    record = _hydrograph_for_level(float(level), cfg, canonical)
    theta = sample_theta_tilted(
        marginals,
        seed=7,
        shift_z=None,
        n_samples=N_SAMPLES,
        stratified=True,
        **sampler_kwargs,
    ).theta
    seepage = (
        None
        if cfg.seepage_length_cov is None
        else sample_seepage_length(
            cfg.geometry.L, cfg.seepage_length_cov, seed=7, n_samples=N_SAMPLES
        )
    )
    numba_static, numba_trans = _make_evaluate(record, geometry, cfg, "numba")(
        theta, seepage
    )
    numpy_static, numpy_trans = _make_evaluate(record, geometry, cfg, "numpy")(
        theta, seepage
    )
    return {
        "level_m": float(level),
        "n_samples": N_SAMPLES,
        "static_identical": bool(np.array_equal(numba_static, numpy_static)),
        "transient_identical": bool(np.array_equal(numba_trans, numpy_trans)),
        "static_disagreements": int(np.count_nonzero(numba_static != numpy_static)),
        "transient_disagreements": int(np.count_nonzero(numba_trans != numpy_trans)),
    }


def run_study(config_path: Path, levels, n_replicates: int) -> dict:
    """Execute both arms at every level and return the JSON-ready payload."""
    cfg = Config.from_yaml(config_path)
    base_seed = int(cfg.mc.seed)
    canonical = _load_canonical_or_none(cfg)
    geometry = cfg.geometry.as_evaluator_dict()
    marginals = cfg.priors.to_marginal_specs()
    sampler_kwargs = dict(
        rho_log_kaq_d70=cfg.correlation.rho_log_kaq_d70,
        d70_interpretation=cfg.priors.d70_interpretation,
        coupling=cfg.correlation.coupling,
        bounds=cfg.priors.bounds,
    )

    gate = _backend_gate(cfg, canonical, geometry, marginals, sampler_kwargs, levels[0])
    print(
        f"backend gate: static identical={gate['static_identical']} "
        f"transient identical={gate['transient_identical']}",
        flush=True,
    )

    t_start = time.perf_counter()
    level_records = []
    for level_index, level in enumerate(levels):
        record = _hydrograph_for_level(float(level), cfg, canonical)
        evaluate = _make_evaluate(record, geometry, cfg)
        arms = {}
        for arm, stratified, tag in (
            ("production_lhs", True, _TAG_PROD),
            ("iid_control", False, _TAG_IID),
        ):
            sample = run_replicates(
                marginals=marginals,
                sampler_kwargs=sampler_kwargs,
                evaluate=evaluate,
                draw_length=_make_draw_length(
                    cfg, base_seed, level_index, stratified=stratified
                ),
                n_samples=N_SAMPLES,
                n_replicates=n_replicates,
                seed_root=base_seed,
                stratified=stratified,
                scheme_tag=tag,
                level_tag=level_index,
            )
            arms[arm] = {
                branch: _branch_block(sample, branch)
                for branch in ("static", "transient")
            }
            arms[arm]["paired_bootstrap_delta_beta"] = _paired_bootstrap_block(sample)
            print(
                f"h={level:6.2f} {arm:14s} "
                f"static cov={arms[arm]['static']['coverage']:.4f} "
                f"trans cov={arms[arm]['transient']['coverage']:.4f} "
                f"(P_f_tr={arms[arm]['transient']['mean_p_f']:.3e})",
                flush=True,
            )
        # A free unbiasedness check: both arms estimate the same integral.
        agreement = {}
        for branch in ("static", "transient"):
            p_lhs = arms["production_lhs"][branch]["mean_p_f"]
            p_iid = arms["iid_control"][branch]["mean_p_f"]
            se = float(
                np.sqrt(
                    max(p_iid * (1.0 - p_iid), 0.0) / (N_SAMPLES * n_replicates) * 2.0
                )
            )
            agreement[branch] = {
                "p_lhs": p_lhs,
                "p_iid": p_iid,
                "difference": p_lhs - p_iid,
                "pooled_standard_error": se,
                "z": (p_lhs - p_iid) / se if se > 0 else float("nan"),
            }
        level_records.append(
            {"level_m": float(level), "arms": arms, "arm_mean_agreement": agreement}
        )

    runtime = time.perf_counter() - t_start

    # The primary, pre-registered verdict is on the Clopper-Pearson cells. The
    # paired-bootstrap block is a secondary measurement added after the rule was
    # fixed, so it is reported under its own flag and does not move that verdict.
    def _cells(arm: str, key: str | None = None):
        keys = ("static", "transient") if key is None else (key,)
        return [lv["arms"][arm][k] for lv in level_records for k in keys]

    control_ok = all(c["passes_rule"] for c in _cells("iid_control"))
    lhs_ok = all(c["passes_rule"] for c in _cells("production_lhs"))
    boot_key = "paired_bootstrap_delta_beta"
    boot_cells = {
        arm: [c for c in _cells(arm, boot_key) if c["n_reportable"] > 0]
        for arm in ("production_lhs", "iid_control")
    }
    boot_ok = {
        arm: (all(c["passes_rule"] for c in cells) if cells else None)
        for arm, cells in boot_cells.items()
    }
    return {
        "study": "Clopper-Pearson interval coverage under the production LHS design",
        "audit_item": "F5",
        "question": (
            "Does the two-sided 95 per cent Clopper-Pearson interval attain its "
            "nominal coverage when the sample is the production randomized-LHS "
            "design at N = 1e5, whose rows are dependent?"
        ),
        "decision_rule": {
            "registered": (
                "before the first replicate was drawn (S05 pre-edit verdicts)"
            ),
            "apparatus_gate": (
                "the iid control's one-sided 95 per cent lower confidence limit on "
                f"coverage is at least {COVERAGE_LOWER_LIMIT_FLOOR} at every cell, "
                "or the study is void"
            ),
            "verdict": (
                "coverage is not contradicted at a cell when the same lower limit "
                f"is at least {COVERAGE_LOWER_LIMIT_FLOOR}"
            ),
            "coverage_lower_limit_floor": COVERAGE_LOWER_LIMIT_FLOOR,
        },
        "config": config_path.name,
        "config_hash": cfg.config_hash(),
        "cross_section_id": cfg.cross_section_id,
        "d70_interpretation": cfg.priors.d70_interpretation,
        "hydrograph_source": "d4pdf_scaled_canonical",
        "progression_backend": BACKEND,
        "backend_gate": gate,
        "base_seed": base_seed,
        "n_samples": N_SAMPLES,
        "n_replicates": int(n_replicates),
        "confidence": CONFIDENCE,
        "levels": level_records,
        "apparatus_sound": bool(control_ok),
        "lhs_coverage_not_contradicted": bool(lhs_ok),
        "paired_bootstrap_secondary": {
            "note": (
                "secondary measurement, added after the decision rule was fixed; "
                "the same rule is applied to it but the primary verdict above is "
                "on the Clopper-Pearson cells only"
            ),
            "iid_control_not_contradicted": boot_ok["iid_control"],
            "lhs_not_contradicted": boot_ok["production_lhs"],
            "evaluable_cells": {arm: len(cells) for arm, cells in boot_cells.items()},
        },
        "runtime_seconds": runtime,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    parser.add_argument("--levels", default=None)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = parser.parse_args()

    config_path = REPO_ROOT / "configs" / args.config
    if args.levels:
        levels = [float(x) for x in args.levels.split(",")]
    elif config_path.name == DEFAULT_CONFIG_NAME:
        levels = DEFAULT_LEVELS
    else:
        parser.error("--levels is required for a config other than the default")

    payload = run_study(config_path, levels, args.replicates)
    paths = _output_paths(config_path)
    for key in ("json", "tracked_json"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
        paths[key].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"\napparatus sound: {payload['apparatus_sound']}   "
        f"LHS coverage not contradicted: {payload['lhs_coverage_not_contradicted']}   "
        f"({payload['runtime_seconds']:.0f} s)"
    )
    print(f"wrote {paths['json']}\nwrote {paths['tracked_json']}")


if __name__ == "__main__":
    main()
