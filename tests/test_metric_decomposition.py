"""Gates on the two RQ1 metrics and on the comparator ladder's order.

These pin the corrections of `docs/decisions/metric-and-decomposition-study.md`
(audit items F3, M01, M02, M03). They are analytic or run on tiny synthetic
arrays: nothing here reads a sweep, so the suite stays fast and the statements
are proved rather than reproduced from a stored number.

The four things that must not come back:

1. a map from ``B`` alone to ``dbeta``;
2. R2's ratio-space width verdict carried to ``dbeta``;
3. the claim that the ladder's *components* are order-independent;
4. the claim that a shared sample removes the sampling noise of the comparison.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

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


@pytest.fixture(scope="module")
def study():
    return _load("metric_decomposition_study")


def _beta(p: float) -> float:
    return float(-norm.ppf(p))


def _dbeta(p_s: float, p_t: float) -> float:
    return _beta(p_t) - _beta(p_s)


# --------------------------------------------------------------------------- #
# 1. B does not determine dbeta                                               #
# --------------------------------------------------------------------------- #
def test_equal_ratio_gives_unequal_delta_beta():
    """Two stages with identical B whose index gaps differ by a factor of 2.

    The counterexample the correction rests on. If this ever fails, the metric
    identity has been redefined and every statement in the study note must be
    re-derived.
    """
    ratio = 1696.0 / 63.0
    shallow = _dbeta(ratio * 1e-2, 1e-2)
    deep = _dbeta(ratio * 1e-6, 1e-6)
    assert shallow / deep > 2.0
    # and the ratio really is identical
    assert (ratio * 1e-2) / 1e-2 == pytest.approx((ratio * 1e-6) / 1e-6)


def test_delta_beta_increases_with_B_only_when_a_probability_is_fixed():
    """The restriction that does hold, against its analytic derivative."""
    p_t = 6.3e-5
    previous = -np.inf
    for ratio in (2.0, 5.0, 10.0, 26.9, 50.0, 100.0):
        value = _dbeta(ratio * p_t, p_t)
        assert value > previous
        previous = value
        slope = p_t / norm.pdf(norm.ppf(ratio * p_t))
        step = 1e-7
        numeric = (
            _dbeta((ratio + step) * p_t, p_t) - _dbeta((ratio - step) * p_t, p_t)
        ) / (2 * step)
        assert slope > 0.0
        assert numeric == pytest.approx(slope, rel=1e-4)

    p_s = 1.696e-3
    previous = -np.inf
    for ratio in (2.0, 5.0, 10.0, 26.9, 50.0, 100.0):
        value = _dbeta(p_s, p_s / ratio)
        assert value > previous
        previous = value


def test_the_two_notions_of_common_mode_are_distinct():
    """Multiplicative in probability is not additive in index, and vice versa."""
    p_s, p_t = 1.696e-3, 6.3e-5
    base_b, base_d = p_s / p_t, _dbeta(p_s, p_t)

    # Common multiplicative factor: B exactly invariant, dbeta moves.
    for factor in (0.1, 10.0):
        moved_b = (factor * p_s) / (factor * p_t)
        moved_d = _dbeta(factor * p_s, factor * p_t)
        assert moved_b == pytest.approx(base_b, rel=1e-12)
        assert abs(moved_d - base_d) > 0.05

    # Common additive index shift: dbeta exactly invariant, B moves.
    for shift in (-0.5, 0.5):
        q_s = float(norm.cdf(-(_beta(p_s) + shift)))
        q_t = float(norm.cdf(-(_beta(p_t) + shift)))
        assert _dbeta(q_s, q_t) == pytest.approx(base_d, abs=1e-9)
        assert abs((q_s / q_t) / base_b - 1.0) > 0.30


# --------------------------------------------------------------------------- #
# 2. the gates, and what each one governs                                     #
# --------------------------------------------------------------------------- #
def test_R2_width_verdict_does_not_determine_the_delta_beta_width():
    """One B-interval of factor exactly 2 maps to very different index widths."""
    widths = []
    for p_t in (1e-6, 1e-4, 1e-2):
        lo = _dbeta(5.0 * p_t, p_t)
        hi = _dbeta(10.0 * p_t, p_t)
        assert 10.0 / 5.0 <= 2.0  # passes R2 in every case
        widths.append(hi - lo)
    assert max(widths) / min(widths) > 2.0


def test_index_space_criterion_is_declared_and_separate(rq1):
    """R2 stays on B; the index criterion is its own constant, not an image."""
    assert rq1.R2_MAX_WIDTH == 2.0
    assert rq1.R2_BETA_MAX_WIDTH == 0.30
    assert rq1.R1_MIN_ROWS == 30


def test_level_row_reports_an_index_space_verdict_from_its_own_interval(rq1):
    """The flag must be computed from dbeta's interval, not from B's width."""
    rng = np.random.default_rng(20260916)
    n = 20_000
    static = rng.random(n) < 0.02
    trans = static & (rng.random(n) < 0.20)
    row = rq1.level_row(
        static, trans, level_m=40.0, label="unit-test", n_replicates=200
    )
    assert row["delta_beta_ci_source"] == "paired_bootstrap"
    lo, hi = row["delta_beta_ci"]
    assert row["delta_beta_ci_width"] == pytest.approx(hi - lo)
    assert row["R2_beta_width"] is (row["delta_beta_ci_width"] <= 0.30)
    assert row["resolved_index_space"] is (row["R1_rows"] and row["R2_beta_width"])


def test_index_verdict_can_differ_from_the_ratio_verdict(rq1):
    """A level the ratio calls resolved while the index has no interval at all.

    Reproduces, in miniature, the only disagreement the production record shows:
    the static branch fails in every realization, so beta_static is -inf, no
    dbeta interval exists, and a criterion defined on B nevertheless passes.
    """
    n = 5_000
    static = np.ones(n, dtype=bool)
    rng = np.random.default_rng(7)
    trans = rng.random(n) < 0.90
    row = rq1.level_row(
        static, trans, level_m=56.5, label="unit-test-degenerate", n_replicates=200
    )
    assert row["R1_rows"] is True
    assert row["resolved_index_space"] is False
    assert row["delta_beta_ci"] is None


# --------------------------------------------------------------------------- #
# 3. the ladder telescopes, its components do not commute                     #
# --------------------------------------------------------------------------- #
def test_two_ladder_orders_share_a_total_and_split_it_differently():
    """Both paths through the lattice reach one total by different components.

    Counts are the persisted KP 57.4 39.50 m ones, used here as fixed integers
    so the algebra is gated without touching a sweep.
    """
    n = 1_000_000
    c0, c1, gross, c4b = 22249, 2388, 3861, 521
    b0, b1, bg, b4 = (_beta(k / n) for k in (c0, c1, gross, c4b))

    total = b4 - b0
    order_a = (b1 - b0) + (b4 - b1)
    order_b = (bg - b0) + (b4 - bg)
    assert order_a == pytest.approx(total, abs=1e-12)
    assert order_b == pytest.approx(total, abs=1e-12)

    head_a, head_b = b1 - b0, b4 - bg
    assert head_a / total == pytest.approx(0.640, abs=0.002)
    assert head_b / total == pytest.approx(0.484, abs=0.002)
    # The components genuinely do not commute at this anchor.
    assert head_a - head_b == pytest.approx(0.198, abs=0.002)
    # The two-toggle Shapley value is the average of the two orders.
    assert 0.5 * (head_a + head_b) == pytest.approx(0.714, abs=0.002)


def test_ladder_step_definitions_are_unchanged(study):
    """The published order and its comparators must stay as ADR-0040 set them."""
    rq1 = _load("rq1_beta_analysis")
    assert rq1.BETA_LADDER_STEPS == (
        ("head_convention", "C0", "C1"),
        ("initiation_gate", "C1", "C3b"),
        ("temporal", "C3b", "C4b"),
    )
    assert rq1.LADDER_COMPARATORS == ("C0", "C1", "C3b", "C4b")
    assert set(study.LADDER_SECTIONS) == {"kp62_0", "kp57_4"}


# --------------------------------------------------------------------------- #
# 4. a shared sample reduces noise and does not remove it                     #
# --------------------------------------------------------------------------- #
def test_pairing_reduces_the_variance_without_removing_it(study):
    """Exact delta-method variances at the published KP 62.0 design anchor."""
    result = study._analytic_variance_reduction(1696 / 1e6, 63 / 1e6, 1_000_000)
    assert result["available"] is True
    assert result["delta_beta_variance_reduction"] > 1.0
    assert result["log_B_variance_reduction"] > 1.0
    # The whole point: the paired error is not zero.
    assert result["paired_variance_is_positive"] is True
    assert result["delta_beta_se_paired"] > 0.02
    assert result["delta_beta_se_paired"] < result["delta_beta_se_independent"]


def test_pairing_never_increases_the_variance_under_nesting(study):
    """The cross term is negative for every admissible nested pair."""
    for p_s in (1e-4, 1e-3, 1e-2, 1e-1, 0.5):
        for factor in (2.0, 10.0, 100.0):
            p_t = p_s / factor
            result = study._analytic_variance_reduction(p_s, p_t, 1_000_000)
            assert result["delta_beta_variance_reduction"] >= 1.0
            assert result["log_B_variance_reduction"] >= 1.0


# --------------------------------------------------------------------------- #
# 5. cancellation is a per-metric verdict                                     #
# --------------------------------------------------------------------------- #
def test_transient_only_input_gives_agreeing_verdicts(study):
    """Static exactly invariant: both statistics move with one transient count.

    So their resolved/unresolved verdicts must agree, which is why the
    critical-length arms never disagree in the production measurement.
    """
    rng = np.random.default_rng(11)
    n = 200_000
    base_static = rng.random(n) < 0.05
    base_trans = base_static & (rng.random(n) < 0.20)
    # The arm moves only the transient column; the static column is reused.
    arm_trans = base_trans & (rng.random(n) < 0.70)
    counts = study._pattern_counts(base_static, base_trans, base_static, arm_trans)
    entry = study._displacement_ci(counts, n_boot=400, seed=3)
    assert entry["p_static_arm"] == pytest.approx(entry["p_static_baseline"], abs=0.0)
    assert entry["rho_resolved"] == entry["delta_delta_beta_resolved"]
    assert entry["rho_resolved"] is True


def test_common_mode_input_can_cancel_in_one_metric_only(study):
    """A move that leaves B near 1 while the index gap moves resolvably."""
    rng = np.random.default_rng(29)
    n = 400_000
    base_static = rng.random(n) < 0.20
    base_trans = base_static & (rng.random(n) < 0.05)
    # Both branches expand by roughly the same factor: near-cancellation in B.
    extra = rng.random(n) < 0.10
    arm_static = base_static | extra
    arm_trans = base_trans | (extra & (rng.random(n) < 0.05))
    counts = study._pattern_counts(base_static, base_trans, arm_static, arm_trans)
    entry = study._displacement_ci(counts, n_boot=800, seed=5)
    assert 0.80 < entry["rho"] < 1.25
    assert entry["delta_delta_beta_resolved"] is True
    assert abs(entry["delta_delta_beta"]) > 0.02
