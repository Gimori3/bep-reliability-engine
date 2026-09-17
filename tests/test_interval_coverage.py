"""Gates on the binomial endpoints, their confidence levels, and coverage.

These pin the corrections of `docs/decisions/binomial-interval-coverage-study.md`
and the `l_c` admissibility amendment in
`docs/decisions/adr0049-critical-length-bracket.md` section 8 (audit items F5,
U01 and U02). Everything here is analytic, synthetic or read from a committed
JSON: no sweep is run and no physics beyond a single cheap marginal threshold,
so the suite stays fast.

The five things that must not come back:

1. the upper endpoint of a two-sided 95 per cent interval described as a
   one-sided 95 per cent bound;
2. a lower limit on a failure probability read as a lower bound on its
   reliability index;
3. the paired bound at KP 57.4 described without its union-bound construction;
4. a rank for KP 57.4's design level against KP 60.0, which the bound does not
   support in either direction;
5. a departure factor quoted from a level whose contingency cells fall below
   the pre-registered thirty-realization floor.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import beta as Beta
from scipy.stats import norm

from bep_reliability_engine.convergence import (
    coverage_lower_limit,
    interval_coverage,
    run_replicates,
)
from bep_reliability_engine.fragility import binomial_ci
from bep_reliability_engine.sampling import MarginalSpec

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rq1():
    return _load("rq1_beta_analysis")


# --------------------------------------------------------------------------- #
# 1. The endpoints, and which confidence level each one carries                #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("n", [100_000, 1_000_000])
def test_zero_count_endpoint_is_the_one_sided_97_5_bound(n):
    """P(K = 0 | p) = (1-p)^n, so the one-sided (1-a) limit is 1 - a**(1/n).

    The two-sided 95 per cent Clopper-Pearson upper endpoint at k = 0 equals
    the ONE-SIDED 97.5 per cent limit, not the one-sided 95 per cent one. The
    two differ by about 23 per cent, which is the size of the mislabel this
    pins.
    """
    _, upper = binomial_ci(np.array([0.0]), n, confidence=0.95)
    one_sided_95 = 1.0 - 0.05 ** (1.0 / n)
    one_sided_975 = 1.0 - 0.025 ** (1.0 / n)
    assert upper[0] == pytest.approx(one_sided_975, rel=1e-12)
    assert upper[0] != pytest.approx(one_sided_95, rel=1e-3)
    assert upper[0] / one_sided_95 == pytest.approx(1.2314, rel=1e-3)


def test_published_zero_count_numbers_at_1e5():
    """The two figures the thesis and the audit both quote."""
    n = 100_000
    assert 1.0 - 0.05 ** (1.0 / n) == pytest.approx(2.9957e-5, rel=1e-4)
    _, upper = binomial_ci(np.array([0.0]), n, confidence=0.95)
    assert upper[0] == pytest.approx(3.6888e-5, rel=1e-4)


def test_binomial_ci_endpoints_match_the_beta_quantiles():
    """The helper is the textbook construction, k = 0 and k = n included."""
    n = 1000
    for k in (0, 1, 7, 500, 999, 1000):
        lower, upper = binomial_ci(np.array([k / n]), n, confidence=0.95)
        expected_lo = 0.0 if k == 0 else Beta.ppf(0.025, k, n - k + 1)
        expected_hi = 1.0 if k == n else Beta.ppf(0.975, k + 1, n - k)
        assert lower[0] == pytest.approx(expected_lo, rel=1e-12, abs=1e-15)
        assert upper[0] == pytest.approx(expected_hi, rel=1e-12, abs=1e-15)
        assert lower[0] <= k / n <= upper[0]


# --------------------------------------------------------------------------- #
# 2. Direction: beta is decreasing in p, so the endpoints swap                 #
# --------------------------------------------------------------------------- #
def test_probability_limits_map_to_opposite_index_bounds(rq1):
    """A LOWER limit on p gives an UPPER bound on beta, and vice versa."""
    n, k = 1_000_000, 1132
    p_lo, p_hi = rq1._cp(k, n)
    assert p_lo < k / n < p_hi
    assert rq1.beta_from_p(p_lo) > rq1.beta_from_p(k / n) > rq1.beta_from_p(p_hi)
    block = rq1.beta_interval(k, n)
    # beta_ci is the monotone image with endpoints swapped.
    assert block["beta_ci"][0] == pytest.approx(rq1.beta_from_p(p_hi))
    assert block["beta_ci"][1] == pytest.approx(rq1.beta_from_p(p_lo))


def test_paired_bound_uses_the_two_97_5_endpoints(rq1):
    """The lower bound on dbeta pairs beta(p_t upper) with beta(p_s lower).

    Each endpoint is a 97.5 per cent one-sided limit, so the union bound makes
    the pair a 95 per cent statement. Reproduced here from the definition, not
    read from the helper.
    """
    n, k_static, k_trans = 1_000_000, 1132, 2
    _, p_t_hi = rq1._cp(k_trans, n)
    p_s_lo, _ = rq1._cp(k_static, n)
    expected = rq1.beta_from_p(p_t_hi) - rq1.beta_from_p(p_s_lo)
    assert rq1.delta_beta_cp_bound(k_static, k_trans, n) == pytest.approx(expected)
    assert expected == pytest.approx(1.2660, abs=5e-4)  # the published 1.27
    assert p_s_lo / p_t_hi == pytest.approx(147.694, rel=1e-4)  # the published 148


def test_kp57_4_design_level_does_not_rank_against_kp60_0(rq1):
    """The bound orders KP 57.4 above the drained pair and nowhere else.

    Bounding dbeta from ABOVE with the same construction gives 2.00, and
    KP 60.0's resolved 1.8657 lies inside [1.27, 2.00]. So "KP 57.4 falls from
    first to second" is not supported, in either direction.
    """
    n, k_static, k_trans = 1_000_000, 1132, 2
    p_s_lo, p_s_hi = rq1._cp(k_static, n)
    p_t_lo, p_t_hi = rq1._cp(k_trans, n)
    lower = rq1.beta_from_p(p_t_hi) - rq1.beta_from_p(p_s_lo)
    upper = rq1.beta_from_p(p_t_lo) - rq1.beta_from_p(p_s_hi)
    kp60_0, kp58_8, kp62_0 = 1.8656906737797416, 1.2239236569829481, 0.9043666261686552
    assert lower == pytest.approx(1.2660, abs=5e-4)
    assert upper == pytest.approx(1.9967, abs=5e-4)
    assert lower > kp58_8 > kp62_0  # ordered against the drained pair and KP 62.0
    assert lower < kp60_0 < upper  # NOT ordered against KP 60.0
    # KP 62.0's 0.90 is the smallest of the four, which the bound does settle.
    assert kp62_0 < min(kp58_8, kp60_0, lower)


# --------------------------------------------------------------------------- #
# 3. Coverage: the reduction, and an iid sanity check                          #
# --------------------------------------------------------------------------- #
def test_coverage_lower_limit_known_values():
    # All R replicates covered: Beta.ppf(0.05, R, 1) = 0.05**(1/R).
    assert coverage_lower_limit(200, 200) == pytest.approx(0.05 ** (1 / 200))
    assert coverage_lower_limit(0, 200) == 0.0
    # Monotone in the covered count, and below the point estimate.
    limits = [coverage_lower_limit(k, 400) for k in (340, 370, 390, 400)]
    assert limits == sorted(limits)
    assert coverage_lower_limit(380, 400) < 380 / 400
    with pytest.raises(ValueError):
        coverage_lower_limit(5, 4)


def test_interval_coverage_counts_both_sides():
    counts = np.array([0, 5, 50, 500], dtype=np.int64)
    n = 1000
    # Reference far below every interval except the k = 0 one.
    out = interval_coverage(counts, n, 1e-6)
    assert out["n_replicates"] == 4
    assert out["miss_low"] == pytest.approx(0.75)  # intervals entirely above
    assert out["miss_high"] == pytest.approx(0.0)
    assert out["coverage"] == pytest.approx(0.25)
    # Reference above every interval.
    out = interval_coverage(counts, n, 0.99)
    assert out["miss_high"] == pytest.approx(1.0)
    assert out["coverage"] == pytest.approx(0.0)
    # Its own point estimate is always inside its own interval.
    out = interval_coverage(np.array([50]), n, 0.05)
    assert out["coverage"] == pytest.approx(1.0)


def test_clopper_pearson_covers_at_least_nominally_under_iid():
    """The apparatus control, in miniature: iid counts ARE binomial.

    Drawing the counts directly from the binomial law is the exact analogue of
    the study's crude-MC arm, and its coverage must reach the nominal level
    (Clopper-Pearson is conservative under iid). Fixed seed, so this is a gate
    and not a coin toss.
    """
    rng = np.random.default_rng(20260917)
    n, p, replicates = 2000, 0.01, 4000
    counts = rng.binomial(n, p, size=replicates).astype(np.int64)
    out = interval_coverage(counts, n, p)
    assert out["coverage"] >= 0.95
    assert coverage_lower_limit(out["n_covered"], out["n_replicates"]) >= 0.95


def test_lhs_coverage_is_conservative_on_a_stratified_integrand():
    """A fast, physics-free analogue of the study's finding.

    On a single-marginal threshold LHS stratifies the governing axis, so the
    count is far less dispersed than binomial and an interval built at binomial
    width over-covers. This is the mechanism; the production question (whether
    it still holds for an interaction-driven deep tail on the real limit state)
    is the study's, not this test's.
    """
    marginals = [
        MarginalSpec("k_aq", "lognormal", 2.0e-3, 0.50),
        MarginalSpec("d_70", "lognormal", 5.3e-4, 0.30),
        MarginalSpec("D_aq", "lognormal", 8.0, 0.10),
        MarginalSpec("D_bl", "lognormal", 0.85, 0.167),
        MarginalSpec("k_bl", "lognormal", 1.0e-6, 0.50),
        MarginalSpec("gamma_bl_sub", "lognormal", 6.9, 0.056),
        MarginalSpec("C_e", "lognormal", 0.055, 0.782),
    ]
    sampler_kwargs = dict(
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        coupling="two_population",
        bounds={"d_70": (5.0e-5, 1.0e-3)},
    )
    sigma_ln = np.sqrt(np.log(1.0 + 0.782**2))
    mu_ln = np.log(0.055) - 0.5 * sigma_ln**2
    threshold = float(np.exp(mu_ln + sigma_ln * norm.ppf(0.9)))  # p = 0.10

    def evaluate(theta_sample, _seepage):
        fail = theta_sample.column("C_e") > threshold
        return fail, fail

    common = dict(
        marginals=marginals,
        sampler_kwargs=sampler_kwargs,
        evaluate=evaluate,
        draw_length=lambda _r, _n: None,
        n_samples=2000,
        n_replicates=120,
        seed_root=20260917,
        level_tag=3,
    )
    lhs = run_replicates(stratified=True, scheme_tag=0, **common)
    crude = run_replicates(stratified=False, scheme_tag=1, **common)

    lhs_cov = interval_coverage(
        lhs.n_failures_trans, 2000, float(np.mean(lhs.p_f_trans))
    )
    crude_cov = interval_coverage(
        crude.n_failures_trans, 2000, float(np.mean(crude.p_f_trans))
    )
    assert lhs_cov["coverage"] == pytest.approx(1.0)
    assert lhs_cov["coverage"] >= crude_cov["coverage"]
    # and the mechanism behind it: the stratified count is less dispersed.
    assert np.var(lhs.n_failures_trans) < np.var(crude.n_failures_trans)


# --------------------------------------------------------------------------- #
# 4. The critical-length admissibility window                                  #
# --------------------------------------------------------------------------- #
def _lc_companion() -> dict:
    path = REPO_ROOT / "docs" / "decisions" / "adr0049-critical-length-companion.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_critical_length_window_under_the_thirty_row_floor():
    """The published 1.11 to 1.38 is the R1-qualified window; 1.67 is not.

    Pins ADR-0049 note section 8: the unfiltered maximum rests on 15 failing
    realizations in its smallest contingency cell, and the maximum over levels
    where every cell clears 30 is 1.3846.
    """
    payload = _lc_companion()
    rows = []
    for section in payload["sections"]:
        for arm, block in section["arms"].items():
            for level in block["levels"]:
                rho = level.get("rho")
                if not rho or rho.get("rho") is None or not rho["resolved"]:
                    continue
                departure = max(rho["rho"], 1.0 / rho["rho"])
                rows.append((departure, int(level["min_cell_failures"]), arm))

    assert len(rows) == 176
    qualified = [r for r in rows if r[1] >= 30]
    assert len(qualified) == 175  # exactly one level falls below the floor

    unfiltered_max = max(r[0] for r in rows)
    qualified_max = max(r[0] for r in qualified)
    assert unfiltered_max == pytest.approx(1.6667, abs=5e-4)
    assert qualified_max == pytest.approx(1.3846, abs=5e-4)

    # The excluded level is the unfiltered maximum, and its count is 15.
    excluded = [r for r in rows if r[1] < 30]
    assert excluded[0][0] == pytest.approx(unfiltered_max)
    assert excluded[0][1] == 15

    # The shorter-arm window is untouched by the floor.
    lower_arm = [r[0] for r in qualified if r[2] == "l_c_lower"]
    assert max(lower_arm) == pytest.approx(1.2264, abs=5e-4)


def test_critical_length_transient_span_window():
    """The quoted transient span 1.00 to 1.70 is the R1-qualified maximum.

    The unfiltered 2.083 sits at KP 62.0's design level, whose smallest cell
    holds 12 failing realizations.
    """
    payload = _lc_companion()
    spans = []
    for section in payload["sections"]:
        by_stage = {
            lv["stage_m_msl"]: lv for lv in section["arms"]["l_c_upper"]["levels"]
        }
        by_stage_lo = {
            lv["stage_m_msl"]: lv for lv in section["arms"]["l_c_lower"]["levels"]
        }
        for anchor in section["at_anchors"].values():
            span = anchor["span_trans"]
            stage = anchor["stage_m_msl"]
            if span is None or stage not in by_stage:
                continue
            cells = min(
                int(by_stage[stage]["min_cell_failures"]),
                int(by_stage_lo[stage]["min_cell_failures"]),
            )
            spans.append((float(span), cells))

    assert max(s for s, _ in spans) == pytest.approx(2.0833, abs=5e-4)
    qualified = [s for s, c in spans if c >= 30]
    assert max(qualified) == pytest.approx(1.6981, abs=5e-4)
    assert min(qualified) == pytest.approx(1.0014, abs=5e-3)


# --------------------------------------------------------------------------- #
# 5. The measured coverage record                                             #
# --------------------------------------------------------------------------- #
def _coverage_records() -> list[dict]:
    paths = [
        REPO_ROOT / "docs" / "decisions" / f"binomial-interval-coverage-{slug}.json"
        for slug in ("kp58_8_matrix", "kp60_0_matrix")
    ]
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def test_measured_coverage_record_still_says_what_the_thesis_quotes():
    """Pins the study's headline numbers and both pre-registered verdicts.

    The thesis quotes 94.1 to 99.9 per cent under the production design and
    93.8 to 96.6 under the iid control, so a regenerated record that moved
    either range must fail here rather than leave the text behind.
    """
    lhs_cov, iid_cov, lhs_lim, iid_lim = [], [], [], []
    for d in _coverage_records():
        assert d["n_replicates"] == 800 and d["n_samples"] == 100_000
        assert d["confidence"] == 0.95
        assert d["decision_rule"]["coverage_lower_limit_floor"] == 0.90
        gate = d["backend_gate"]
        assert gate["static_identical"] and gate["transient_identical"]
        assert d["apparatus_sound"] is True
        assert d["lhs_coverage_not_contradicted"] is True
        for lv in d["levels"]:
            for branch in ("static", "transient"):
                lhs = lv["arms"]["production_lhs"][branch]
                iid = lv["arms"]["iid_control"][branch]
                lhs_cov.append(lhs["coverage"])
                iid_cov.append(iid["coverage"])
                lhs_lim.append(lhs["coverage_lower_limit_95"])
                iid_lim.append(iid["coverage_lower_limit_95"])

    assert len(lhs_cov) == 16  # 2 sections x 4 levels x 2 branches
    assert min(lhs_cov) == pytest.approx(0.9413, abs=5e-4)
    assert max(lhs_cov) == pytest.approx(0.9988, abs=5e-4)
    assert min(iid_cov) == pytest.approx(0.9375, abs=5e-4)
    assert max(iid_cov) == pytest.approx(0.9663, abs=5e-4)
    # Every cell clears the pre-registered floor, in both arms.
    assert min(lhs_lim) >= 0.90 and min(iid_lim) >= 0.90
    assert min(lhs_lim) == pytest.approx(0.9257, abs=5e-4)


def test_stratification_does_not_reduce_coverage_below_the_iid_arm():
    """15 of 16 matched cells cover at least as often; the exception is explained.

    The one shortfall is KP 58.8's deepest transient level on a mean of 31
    failing realizations, and its own exact interval contains 0.95, so it is
    not a measured deficit.
    """
    at_least = 0
    exception = None
    for d in _coverage_records():
        for lv in d["levels"]:
            for branch in ("static", "transient"):
                lhs = lv["arms"]["production_lhs"][branch]
                iid = lv["arms"]["iid_control"][branch]
                if lhs["coverage"] >= iid["coverage"]:
                    at_least += 1
                else:
                    exception = (lv["level_m"], branch, lhs, iid)
    assert at_least == 15
    assert exception is not None
    level, branch, lhs, _iid = exception
    assert branch == "transient" and level == pytest.approx(39.75)
    assert lhs["mean_count"] == pytest.approx(31.0, abs=1.0)
    lo = Beta.ppf(0.025, lhs["n_covered"], lhs["n_replicates"] - lhs["n_covered"] + 1)
    hi = Beta.ppf(0.975, lhs["n_covered"] + 1, lhs["n_replicates"] - lhs["n_covered"])
    assert lo <= 0.95 <= hi


def test_variance_ratio_decays_from_stratified_to_parity():
    """The mechanism behind the conservatism, and its limit.

    In the bulk the stratified count carries a third to two fifths of the
    binomial variance; by the deepest level it is back at 1. The iid arm stays
    near 1 throughout, which is the second apparatus check.
    """
    for d in _coverage_records():
        bulk = d["levels"][0]["arms"]["production_lhs"]["transient"]["var_ratio"]
        deep = d["levels"][-1]["arms"]["production_lhs"]["transient"]["var_ratio"]
        assert bulk < 0.45
        assert 0.95 < deep < 1.10
        iid_ratios = [
            lv["arms"]["iid_control"][b]["var_ratio"]
            for lv in d["levels"]
            for b in ("static", "transient")
        ]
        assert 0.85 < min(iid_ratios) and max(iid_ratios) < 1.20


def test_paired_bootstrap_shortfall_belongs_to_the_percentile_interval():
    """The iid arm under-covers slightly at every level, so LHS is not the cause.

    The percentile bootstrap is an approximate interval for a proportion, and
    the independent-sampling arm shows that directly: 0.928 to 0.958 across all
    eight levels, pooling to 0.943 over 6399 replicates against a nominal 0.95,
    with no trend in the failure count. The stratified arm runs 0.925 to 0.979
    and pools to 0.954, conservative in the bulk and converging onto the iid
    values with depth, which is the same decay the Clopper-Pearson cells show.
    No cell falls below the pre-registered floor, and the nesting implication
    held in every replicate.
    """
    lhs_cov, iid_cov, lhs_lim, iid_lim = [], [], [], []
    for d in _coverage_records():
        for lv in d["levels"]:
            for arm, cov, lim in (
                ("production_lhs", lhs_cov, lhs_lim),
                ("iid_control", iid_cov, iid_lim),
            ):
                block = lv["arms"][arm]["paired_bootstrap_delta_beta"]
                assert block["nesting_violations"] == 0
                assert block["n_reportable"] >= 799
                cov.append(block["coverage"])
                lim.append(block["coverage_lower_limit_95"])

    assert len(iid_cov) == 8
    assert min(iid_cov) == pytest.approx(0.9275, abs=5e-4)
    assert max(iid_cov) == pytest.approx(0.9575, abs=5e-4)
    assert sum(c < 0.95 for c in iid_cov) == 5  # the interval is approximate
    assert min(lhs_cov) == pytest.approx(0.9250, abs=5e-4)
    assert max(lhs_cov) == pytest.approx(0.9788, abs=5e-4)
    assert min(lhs_lim) >= 0.90 and min(iid_lim) >= 0.90

    # Pooled over every replicate: the iid arm sits below nominal, the
    # stratified one at it.
    pooled = {}
    for arm in ("production_lhs", "iid_control"):
        covered = reportable = 0
        for d in _coverage_records():
            for lv in d["levels"]:
                block = lv["arms"][arm]["paired_bootstrap_delta_beta"]
                covered += block["n_covered"]
                reportable += block["n_reportable"]
        pooled[arm] = covered / reportable
    assert pooled["iid_control"] == pytest.approx(0.9430, abs=5e-4)
    assert pooled["production_lhs"] == pytest.approx(0.9544, abs=5e-4)

    # The stratified arm is conservative where the Clopper-Pearson cells are.
    for d in _coverage_records():
        bulk = d["levels"][0]["arms"]
        assert (
            bulk["production_lhs"]["paired_bootstrap_delta_beta"]["coverage"]
            > bulk["iid_control"]["paired_bootstrap_delta_beta"]["coverage"]
        )
