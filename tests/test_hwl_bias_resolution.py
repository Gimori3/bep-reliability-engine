"""Tests for the design-HWL bias resolution machinery.

Pins (a) the pre-registered criteria constants, so a later edit to them trips a
test rather than silently rewriting the pre-registration; (b) the two exact
routes of the paired ratio bootstrap against each other; (c) the "HWL is read
from the config, never from prose" rule; and (d) the additive
``run_comparator_ladder(theta_override=...)`` seam's default bit-identity.

Companion note: ``docs/decisions/adr0040-hwl-bias-resolution.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import hwl_bias_resolution as H  # noqa: E402

from bep_reliability_engine.gap_decomposition import (  # noqa: E402
    COMPARATOR_ORDER,
    run_comparator_ladder,
)
from tests.test_gap_decomposition import _make_config, _theta_for  # noqa: E402

# ---------------------------------------------------------------------------
# The pre-registration is a contract: its constants are pinned here.
# ---------------------------------------------------------------------------


def test_preregistered_criteria_constants_are_pinned() -> None:
    """Part 1 of the companion note fixes these before any number was seen.

    If a future change wants different thresholds it must say so in a dated
    amendment, not by editing the driver and leaving the note behind.
    """
    assert H.R1_MIN_ROWS == 30
    assert H.R2_MAX_WIDTH == 2.0
    assert H.V3_TOLERANCE == 1.5
    assert H.V3_MIN_ROWS == 100
    assert H.V4_MIN_NEFF == 200.0
    assert H.V4_COV_FACTOR == 0.5
    assert H.F3_EPISTEMIC_FACTOR == 10.0
    assert H.SMOKE_MP_TOLERANCE == 1.5


def test_resolution_requires_both_criteria_never_either() -> None:
    """R1 AND R2, as pre-registered; a narrow interval on 4 rows must fail."""
    narrow_but_tiny = H.RatioEstimate(
        level_m=46.39,
        p_static=1e-3,
        p_transient=4e-5,
        ratio=25.0,
        ci_lo=20.0,
        ci_hi=30.0,
        width_factor=1.5,
        k_static=100,
        k_transient=4,
        n_eff_transient=float("nan"),
        n_samples=100_000,
        weighted=False,
    )
    assert not narrow_but_tiny.resolved
    assert narrow_but_tiny.criterion_flags == {
        "R1_rows": False,
        "R2_width": True,
        "resolved": False,
    }

    many_rows_wide = H.RatioEstimate(
        level_m=46.39,
        p_static=1e-3,
        p_transient=4e-4,
        ratio=2.5,
        ci_lo=1.0,
        ci_hi=9.0,
        width_factor=9.0,
        k_static=100,
        k_transient=40,
        n_eff_transient=float("nan"),
        n_samples=100_000,
        weighted=False,
    )
    assert not many_rows_wide.resolved
    assert many_rows_wide.criterion_flags["R1_rows"]
    assert not many_rows_wide.criterion_flags["R2_width"]

    passes = H.RatioEstimate(
        level_m=47.0,
        p_static=5.2e-2,
        p_transient=5.0e-3,
        ratio=10.5,
        ci_lo=9.6,
        ci_hi=11.5,
        width_factor=1.2,
        k_static=5220,
        k_transient=499,
        n_eff_transient=float("nan"),
        n_samples=100_000,
        weighted=False,
    )
    assert passes.resolved


# ---------------------------------------------------------------------------
# The paired ratio bootstrap: two exact routes, pinned against each other.
# ---------------------------------------------------------------------------


def _synthetic_pair(n: int = 20_000, seed: int = 7) -> tuple:
    """Nested flags: transient subset of static, as the physics guarantees."""
    rng = np.random.default_rng(seed)
    static = rng.random(n) < 0.05
    transient = static & (rng.random(n) < 0.12)
    return static, transient


def test_multinomial_and_index_resample_routes_agree_in_distribution() -> None:
    """The unweighted fast route is exactly the index resample, in law.

    Resampling N rows with replacement makes the four joint-pattern counts
    Multinomial(N, p_hat), so the O(B) multinomial draw is not an approximation
    of the O(B*N) index resample; it is the same distribution. The two use
    different RNG streams, so they are compared on their percentiles.
    """
    static, transient = _synthetic_pair()
    fast = H.paired_ratio_bootstrap(static, transient, n_replicates=4000, seed=1)
    slow = H.paired_ratio_bootstrap(
        static,
        transient,
        weights=np.ones(static.size),
        n_replicates=4000,
        seed=2,
        chunk=500,
    )
    for q in (2.5, 25.0, 50.0, 75.0, 97.5):
        a, b = np.percentile(fast, q), np.percentile(slow, q)
        assert a == pytest.approx(b, rel=0.03), f"percentile {q}: {a} vs {b}"


def test_weighted_active_row_route_matches_an_explicit_index_resample() -> None:
    """The active-row reduction is exact, not an approximation.

    A row whose every column is False contributes exactly zero to every weighted
    mean, so lumping all such rows into one multinomial category leaves the draw
    an exact Multinomial(N, uniform) over the N rows, just marginalised. Checked
    against a literal O(B*N) index resample carrying the same weights.
    """
    rng = np.random.default_rng(21)
    n = 8_000
    static = rng.random(n) < 0.04
    transient = static & (rng.random(n) < 0.25)
    weights = np.exp(rng.normal(0.0, 0.8, size=n))

    fast = H.paired_column_means_bootstrap(
        [static, transient], weights=weights, n_replicates=3000, seed=31
    )
    # Literal reference: resample row indices, gather, average.
    ref_rng = np.random.default_rng(32)
    packed = np.stack(
        [np.where(static, weights, 0.0), np.where(transient, weights, 0.0)], axis=1
    )
    ref = np.empty((3000, 2))
    for b in range(3000):
        ref[b] = packed[ref_rng.integers(0, n, size=n)].mean(axis=0)

    for col in (0, 1):
        for q in (2.5, 50.0, 97.5):
            a = np.percentile(fast[:, col], q)
            b_ = np.percentile(ref[:, col], q)
            assert a == pytest.approx(b_, rel=0.05), f"col {col} q{q}: {a} vs {b_}"


def test_unit_weights_reproduce_the_unweighted_point_estimate_exactly() -> None:
    static, transient = _synthetic_pair()
    plain = H.bias_ratio(46.5, static, transient, n_replicates=200)
    unit = H.bias_ratio(
        46.5, static, transient, weights=np.ones(static.size), n_replicates=200
    )
    assert unit.p_static == plain.p_static
    assert unit.p_transient == plain.p_transient
    assert unit.ratio == plain.ratio
    assert unit.k_transient == plain.k_transient
    # ... and the Kish n_eff of unit weights is exactly the failure count.
    assert unit.n_eff_transient == pytest.approx(float(plain.k_transient))


def test_paired_interval_is_tighter_than_independent_binomials() -> None:
    """The pairing is the point: independent binomials overstate the width."""
    static, transient = _synthetic_pair()
    paired = H.bias_ratio(46.5, static, transient, n_replicates=4000)
    rng = np.random.default_rng(11)
    n = static.size
    p_s = rng.binomial(n, static.mean(), size=4000) / n
    p_t = rng.binomial(n, transient.mean(), size=4000) / n
    lo, hi = np.percentile(
        np.where(p_t > 0, p_s / np.where(p_t > 0, p_t, 1), np.inf), [2.5, 97.5]
    )
    assert paired.ci_hi / paired.ci_lo < hi / lo


def test_zero_transient_mass_yields_infinite_ratio_not_a_crash() -> None:
    static = np.zeros(1000, dtype=bool)
    static[:20] = True
    transient = np.zeros(1000, dtype=bool)
    est = H.bias_ratio(39.21, static, transient, n_replicates=200)
    assert est.k_transient == 0
    assert np.isinf(est.ratio)
    assert not est.resolved


def test_unweighted_four_column_route_reproduces_the_adr0047_kernel() -> None:
    """The K=4 unweighted route IS the ADR-0047 section 4.5 16-cell bootstrap.

    That kernel is the accepted statistic behind the published L non-cancellation
    numbers, so the generalisation used here (which additionally supports the
    weighted case the pre-registration requires) must reproduce it. Compared on
    percentiles, since the two use different RNG streams.
    """
    adr0047 = H._load_adr0047_module()
    rng = np.random.default_rng(3)
    n = 30_000
    base_s = rng.random(n) < 0.08
    base_t = base_s & (rng.random(n) < 0.20)
    arm_s = base_s | (rng.random(n) < 0.01)
    arm_t = arm_s & (rng.random(n) < 0.35)

    mine = H.ratio_of_ratios(base_s, base_t, arm_s, arm_t, n_replicates=4000, seed=5)
    theirs = adr0047.ratio_of_ratios_ci(
        adr0047._pattern_counts(base_s, base_t, arm_s, arm_t), n_boot=4000, seed=5
    )
    assert mine["rho"] == pytest.approx(theirs["rho"], rel=1e-12)
    assert mine["rho_lo"] == pytest.approx(theirs["rho_lo"], rel=0.05)
    assert mine["rho_hi"] == pytest.approx(theirs["rho_hi"], rel=0.05)
    assert mine["resolved"] == theirs["resolved"]


def test_ratio_of_ratios_null_is_pinned_at_one_for_an_identical_arm() -> None:
    """An arm identical to the baseline must give rho = 1 and resolve nothing."""
    rng = np.random.default_rng(4)
    n = 5_000
    s = rng.random(n) < 0.10
    t = s & (rng.random(n) < 0.3)
    out = H.ratio_of_ratios(s, t, s, t, n_replicates=2000, seed=9)
    assert out["rho"] == pytest.approx(1.0)
    assert not out["resolved"]
    assert out["departure_factor"] == pytest.approx(1.0)


def test_weighted_route_is_used_and_differs_from_the_pattern_count_route() -> None:
    """Under weights the pattern counts stop being sufficient statistics.

    Two rows sharing a joint pattern contribute differently once they carry
    different weights, so the cheap multinomial route would be *wrong* here.
    This pins that the weighted path is genuinely a different computation, which
    is the reason the pre-registration replaces the ADR-0047 bootstrap under IS.
    """
    rng = np.random.default_rng(6)
    n = 4_000
    s = rng.random(n) < 0.2
    t = s & (rng.random(n) < 0.3)
    skewed = np.exp(rng.normal(0.0, 1.2, size=n))  # heavy weight dispersion
    plain = H.bias_ratio(46.5, s, t, n_replicates=2000)
    weighted = H.bias_ratio(46.5, s, t, weights=skewed, n_replicates=2000)
    assert weighted.weighted and not plain.weighted
    assert weighted.n_eff_transient < float(t.sum())  # degeneracy is visible
    assert weighted.ratio != pytest.approx(plain.ratio, rel=1e-6)


def test_intervals_overlap_semantics() -> None:
    assert H.intervals_overlap((1.0, 2.0), (1.5, 3.0))
    assert H.intervals_overlap((1.0, 2.0), (2.0, 3.0))
    assert not H.intervals_overlap((1.0, 2.0), (2.5, 3.0))
    # An unbounded interval cannot be shown to disagree.
    assert H.intervals_overlap((1.0, float("inf")), (1e9, 2e9))


# ---------------------------------------------------------------------------
# "Read every HWL from configs/*.yaml, never from a prose document."
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["kp62_0", "kp57_4"])
def test_hwl_anchors_come_from_the_config_and_match_the_preregistration(key) -> None:
    config, a1, a2 = H.load_section(key)
    assert a1 == float(config.geometry.HWL)
    assert a1 == H.SECTIONS[key]["hwl_expected"]
    assert a2 == H.SECTIONS[key]["a2_expected"]
    grid = np.asarray(config.mc.conditioning_grid, dtype=float)
    # A2 really is the nearest grid level, and A1 really is not on the grid.
    assert a2 in set(grid.tolist())
    assert a1 not in set(grid.tolist())


def test_the_two_kp62_anchors_are_distinct_levels() -> None:
    """The conflation this exercise exists to end: 46.39 is not 46.50."""
    _, a1, a2 = H.load_section("kp62_0")
    assert a1 != a2
    assert abs(a2 - a1) == pytest.approx(0.11, abs=1e-9)


# ---------------------------------------------------------------------------
# The additive theta_override seam (ADR-0029 tilted population -> ADR-0040 ladder).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def small_config():
    return _make_config(n_samples=120, conditioning_grid=(8.0, 12.0))


def test_theta_override_none_is_the_production_path(small_config) -> None:
    """Default None must be bit-identical to the pre-seam behaviour."""
    base = run_comparator_ladder(small_config, n_jobs=1)
    same = run_comparator_ladder(small_config, n_jobs=1, theta_override=None)
    np.testing.assert_array_equal(base.theta_matrix, same.theta_matrix)
    for name in COMPARATOR_ORDER:
        np.testing.assert_array_equal(base.comparators[name], same.comparators[name])
    assert "theta_override" not in base.metadata


def test_theta_override_with_the_configs_own_theta_changes_nothing(
    small_config,
) -> None:
    """The seam routes an external population through identical machinery."""
    base = run_comparator_ladder(small_config, n_jobs=1)
    echoed = run_comparator_ladder(
        small_config, n_jobs=1, theta_override=_theta_for(small_config)
    )
    for name in COMPARATOR_ORDER:
        np.testing.assert_array_equal(base.comparators[name], echoed.comparators[name])


def test_theta_override_is_stamped_so_it_cannot_masquerade_as_a_baseline(
    small_config,
) -> None:
    result = run_comparator_ladder(
        small_config, n_jobs=1, theta_override=_theta_for(small_config)
    )
    assert result.metadata["theta_override"] is True
    assert "reweighted" in result.metadata["theta_override_note"]


# ---------------------------------------------------------------------------
# Stage D arm construction: the negative control must come first.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["kp62_0", "kp57_4"])
def test_mp_is_the_first_epistemic_arm(key) -> None:
    """The pre-registration runs m_p first, as a smoke test.

    ADR-0045 section 2 applies m_p to the single-source H_c in *both* of its
    uses, so it is pure common-mode by construction and must return rho ~ 1. If
    the machinery disagrees, the machinery is wrong and no other arm is
    trustworthy -- which only helps if it is evaluated before them.
    """
    config, _, _ = H.load_section(key)
    arms = H.epistemic_arms(config, key)
    assert arms[0][0] == "m_p"
    assert arms[0][1] == "m_p"


@pytest.mark.parametrize("key", ["kp62_0", "kp57_4"])
def test_epistemic_arms_cover_every_required_bracket(key) -> None:
    """Every knob Stage D names is present; none is left off by omission."""
    config, _, _ = H.load_section(key)
    arms = H.epistemic_arms(config, key)
    labels = [a[0] for a in arms]
    brackets = {a[1] for a in arms}
    for required in (
        "m_p",
        "k_aq_field_toe",
        "k_aq_field_geomean",
        "k_aq_regional_upper",
        "gamma_bl_sub_lower",
        "z_toe_plus0.30m",
        "z_toe_minus0.30m",
    ):
        assert required in labels, required
    assert "L_measurement" in brackets, "the ADR-0047 L arm is missing"
    assert any(lbl.startswith("L_") for lbl in labels)


@pytest.mark.parametrize("key", ["kp62_0", "kp57_4"])
def test_epistemic_arms_never_mutate_the_baseline_config(key) -> None:
    """Arms are in-memory copies; every knob stays OFF in production."""
    config, _, _ = H.load_section(key)
    before = config.config_hash()
    arms = H.epistemic_arms(config, key)
    assert config.config_hash() == before
    assert config.sellmeijer_model_factor is None
    assert config.prior_mean_scenario is None
    # ... and each arm really did move exactly one thing away from the baseline.
    for label, _, arm in arms:
        assert arm.config_hash() != before, label


def test_stable_seed_is_reproducible_across_processes() -> None:
    """`hash()` on a str is salted per interpreter; the arm seeds must not be."""
    assert H._stable_seed("m_p") == H._stable_seed("m_p")
    assert H._stable_seed("m_p") != H._stable_seed("k_aq_field_toe")
    # Pinned literals: a change here would silently move every reported interval.
    assert H._stable_seed("m_p") == 1382592966
    assert H._stable_seed("k_aq_field_toe") == 1293704257


def test_theta_override_shape_is_validated(small_config) -> None:
    with pytest.raises(ValueError, match="theta_override shape"):
        run_comparator_ladder(
            small_config, n_jobs=1, theta_override=np.zeros((7, 7), dtype=float)
        )
