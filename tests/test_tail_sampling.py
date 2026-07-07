"""Tests for the tilted (importance) prior sampler (ADR-0029, spec §12 fm5).

What is pinned:

1. **Zero-shift degeneracy** — stratified, unshifted, two-population draws
   reproduce M2 ``sample_theta`` bit for bit with all-zero log weights, so
   the tilted sampler genuinely is a substitutable superset of the M2
   surface, not a fork.
2. **Exactness of the weights** — on an analytically tractable tail event in
   the (ln k_aq, ln C_e) plane (their sum is Gaussian under the prior), the
   IS estimate agrees with the closed-form probability within a few standard
   errors, for LHS and crude proposals, with and without the copula and the
   fm2 bounds clip in the pipeline.
3. **Marginal geometry of the tilt** — a Z-shift of nu on a lognormal
   marginal preserves sigma_ln and moves the log-mean by nu * sigma_ln.
4. **Estimator arithmetic** — hand-checkable cases of
   ``importance_estimate`` (unit weights = raw MC fraction; zero failures).
5. **Cross-entropy update** — recovers the analytic CE optimum (the mean of
   the failure-region Z) on the tractable event, and refuses a pilot with
   no failures.
6. **Variance reduction where it matters** — for a deep tail event
   (P ~ 1e-4), replicate CoV of the CE-tilted estimator is well below crude
   MC at the same N. (The LHS-vs-crude tail comparison on the *physics* is
   the ADR-0029 study, not a unit test.)
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from bep_reliability_engine.sampling import MarginalSpec, sample_theta
from bep_reliability_engine.tail_sampling import (
    TailEstimate,
    cross_entropy_shift,
    importance_estimate,
    sample_theta_tilted,
)

# The KP58.8 production marginals (configs/kp58_8_historical_matrix.yaml).
MARGINALS = [
    MarginalSpec(name="k_aq", family="lognormal", mean=2.0e-3, cov=0.50),
    MarginalSpec(name="d_70", family="lognormal", mean=5.3e-4, cov=0.30),
    MarginalSpec(name="D_aq", family="lognormal", mean=8.0, cov=0.10),
    MarginalSpec(name="D_bl", family="lognormal", mean=0.85, cov=0.167),
    MarginalSpec(name="k_bl", family="lognormal", mean=1.0e-6, cov=0.50),
    MarginalSpec(name="gamma_bl_sub", family="lognormal", mean=6.9, cov=0.056),
    MarginalSpec(name="C_e", family="lognormal", mean=0.055, cov=0.782),
]
SPEC = {m.name: m for m in MARGINALS}


def _sigma_mu_ln(spec: MarginalSpec) -> tuple[float, float]:
    """Moment-matched lognormal parameters, recomputed independently."""
    sigma_ln = np.sqrt(np.log(1.0 + spec.cov**2))
    mu_ln = np.log(spec.mean) - 0.5 * sigma_ln**2
    return sigma_ln, mu_ln


def _analytic_tail(theta: np.ndarray, threshold_quantile: float) -> tuple:
    """A tractable stand-in tail event: ln k_aq + ln C_e > c.

    Under the (two-population) prior the sum is Normal with known mean and
    variance, so the exact event probability is available in closed form —
    the ground truth the weighted estimators must recover. Monotone in both
    k_aq and C_e, mirroring the fm7 interaction structure.
    """
    s_k, m_k = _sigma_mu_ln(SPEC["k_aq"])
    s_c, m_c = _sigma_mu_ln(SPEC["C_e"])
    mean = m_k + m_c
    std = float(np.hypot(s_k, s_c))
    c = mean + norm.ppf(threshold_quantile) * std
    indicator = (np.log(theta[:, 0]) + np.log(theta[:, 6])) > c
    p_exact = float(1.0 - threshold_quantile)
    return indicator, p_exact


def test_zero_shift_stratified_reproduces_m2_bit_for_bit() -> None:
    """The substitutability contract: unshifted tilt == sample_theta."""
    kwargs = dict(
        seed=20260707,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        n_samples=2_000,
        coupling="two_population",
        bounds={"d_70": (50.0e-6, 1.0e-3)},
    )
    reference = sample_theta(MARGINALS, **kwargs)
    tilted = sample_theta_tilted(MARGINALS, shift_z=None, **kwargs)

    assert np.array_equal(tilted.theta.theta_matrix, reference.theta_matrix)
    assert tilted.theta.param_names == reference.param_names
    assert np.all(tilted.log_weights == 0.0)
    assert np.all(tilted.weights == 1.0)
    assert tilted.shift_z == {}
    assert tilted.theta.metadata["importance_sampling"] is False


def test_tilted_lognormal_marginal_shifts_log_mean_by_nu_sigma() -> None:
    """Z-shift nu => lognormal proposal with log-mean mu_ln + nu*sigma_ln."""
    nu = 1.25
    tilted = sample_theta_tilted(
        MARGINALS,
        seed=7,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        shift_z={"C_e": nu},
        n_samples=50_000,
        coupling="two_population",
    )
    sigma_ln, mu_ln = _sigma_mu_ln(SPEC["C_e"])
    log_ce = np.log(tilted.theta.column("C_e"))
    assert log_ce.mean() == pytest.approx(mu_ln + nu * sigma_ln, abs=0.02)
    assert log_ce.std(ddof=1) == pytest.approx(sigma_ln, rel=0.02)
    # Untilted columns are untouched by the tilt.
    log_kaq = np.log(tilted.theta.column("k_aq"))
    s_k, m_k = _sigma_mu_ln(SPEC["k_aq"])
    assert log_kaq.mean() == pytest.approx(m_k, abs=0.02)


def test_weights_have_unit_mean_under_the_proposal() -> None:
    """E_q[w] = 1 exactly in expectation (the density-ratio sanity check)."""
    tilted = sample_theta_tilted(
        MARGINALS,
        seed=11,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        shift_z={"k_aq": 1.0, "C_e": 1.0},
        n_samples=100_000,
        coupling="two_population",
    )
    assert tilted.weights.mean() == pytest.approx(1.0, abs=0.02)


@pytest.mark.parametrize("stratified", [True, False])
@pytest.mark.parametrize("coupling", ["two_population", "correlated"])
def test_is_estimate_recovers_analytic_tail_probability(
    stratified: bool, coupling: str
) -> None:
    """Weighted estimate == closed-form tail probability, all pipeline modes.

    P ~ 4.7e-4 at N = 20k: unreachable for the unweighted estimator at this
    N without luck (~9 expected hits), routine for the tilted one. The
    bounds clip is active (on d_70) to pin that clipping does not bias the
    weights (the tilt lives upstream in Z-space). The correlated mode uses
    a nonzero rho so the copula genuinely mixes.
    """
    indicator_quantile = 1.0 - 4.7e-4
    tilted = sample_theta_tilted(
        MARGINALS,
        seed=13,
        rho_log_kaq_d70=0.6 if coupling == "correlated" else 0.0,
        d70_interpretation="matrix",
        shift_z={"k_aq": 2.0, "C_e": 2.0},
        n_samples=20_000,
        coupling=coupling,
        bounds={"d_70": (50.0e-6, 1.0e-3)},
        stratified=stratified,
    )
    indicator, p_exact = _analytic_tail(tilted.theta.theta_matrix, indicator_quantile)
    estimate = importance_estimate(indicator, tilted.log_weights)

    assert estimate.n_failures > 500  # the tilt actually reaches the tail
    assert estimate.p_f == pytest.approx(p_exact, abs=4.0 * estimate.standard_error)
    assert estimate.cov < 0.15  # far tighter than crude MC's ~0.33 at this N
    assert estimate.n_effective > 100.0


def test_importance_estimate_arithmetic() -> None:
    """Unit weights reduce to the raw fraction; zero failures give NaN CoV."""
    fail = np.array([True, False, True, False])
    est = importance_estimate(fail, np.zeros(4))
    assert isinstance(est, TailEstimate)
    assert est.p_f == 0.5
    assert est.n_failures == 2
    assert est.n_effective == pytest.approx(2.0)
    assert est.n_samples == 4

    none = importance_estimate(np.zeros(4, dtype=bool), np.zeros(4))
    assert none.p_f == 0.0
    assert np.isnan(none.cov)
    assert np.isnan(none.n_effective)

    with pytest.raises(ValueError, match="shape"):
        importance_estimate(fail, np.zeros(3))


def test_cross_entropy_update_recovers_failure_region_mean() -> None:
    """On the tractable event, CE returns the failure-region Z mean.

    The event is symmetric in (z_kaq, z_Ce) up to the sigma_ln ratio, and
    the analytic CE optimum for a deep half-space event sits well above 0;
    the untilted pilot's update must match a direct computation exactly and
    both coordinates must be positive (pointing INTO the joint tail).
    """
    pilot = sample_theta_tilted(
        MARGINALS,
        seed=17,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        shift_z=None,
        n_samples=50_000,
        coupling="two_population",
    )
    indicator, _ = _analytic_tail(pilot.theta.theta_matrix, 0.99)
    shifts = cross_entropy_shift(pilot, indicator)

    assert set(shifts) == {"k_aq", "C_e"}
    expected_kaq = pilot.z_by_param["k_aq"][indicator].mean()
    expected_ce = pilot.z_by_param["C_e"][indicator].mean()
    assert shifts["k_aq"] == pytest.approx(expected_kaq)
    assert shifts["C_e"] == pytest.approx(expected_ce)
    assert shifts["k_aq"] > 0.5 and shifts["C_e"] > 0.5

    with pytest.raises(ValueError, match="no failures"):
        cross_entropy_shift(pilot, np.zeros(50_000, dtype=bool))


def test_tilted_estimator_beats_crude_mc_on_the_deep_tail() -> None:
    """Replicate CoV: CE-tilted IS << crude MC at the same N (P ~ 1e-3).

    20 replicate seeds each at N = 4000, exact P = 1e-3 (expected crude
    hits: 4). This is the module-level variance-reduction guarantee; the
    physics-level fm5 study lives in scripts/tail_variance_study.py.
    """
    p_target = 1.0e-3
    n = 4_000
    estimates_is, estimates_mc = [], []
    for seed in range(20):
        tilted = sample_theta_tilted(
            MARGINALS,
            seed=1000 + seed,
            rho_log_kaq_d70=0.0,
            d70_interpretation="matrix",
            shift_z={"k_aq": 1.8, "C_e": 1.8},
            n_samples=n,
            coupling="two_population",
        )
        indicator, p_exact = _analytic_tail(tilted.theta.theta_matrix, 1.0 - p_target)
        estimates_is.append(importance_estimate(indicator, tilted.log_weights).p_f)

        crude = sample_theta_tilted(
            MARGINALS,
            seed=1000 + seed,
            rho_log_kaq_d70=0.0,
            d70_interpretation="matrix",
            shift_z=None,
            n_samples=n,
            coupling="two_population",
            stratified=False,
        )
        indicator_mc, _ = _analytic_tail(crude.theta.theta_matrix, 1.0 - p_target)
        estimates_mc.append(importance_estimate(indicator_mc, crude.log_weights).p_f)

    is_arr = np.asarray(estimates_is)
    mc_arr = np.asarray(estimates_mc)
    cov_is = is_arr.std(ddof=1) / is_arr.mean()
    cov_mc = mc_arr.std(ddof=1) / mc_arr.mean()

    assert is_arr.mean() == pytest.approx(p_exact, rel=0.15)
    # Crude MC at N=4000, P=1e-3 has analytic CoV ~ 0.5; the tilt must cut
    # the replicate CoV by at least 3x (typically ~10x).
    assert cov_is < cov_mc / 3.0


def test_shift_validation() -> None:
    """Unknown or non-finite shifts are refused loudly."""
    kwargs = dict(
        seed=1,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        n_samples=10,
        coupling="two_population",
    )
    with pytest.raises(ValueError, match="shift_z keys"):
        sample_theta_tilted(MARGINALS, shift_z={"C_E": 1.0}, **kwargs)
    with pytest.raises(ValueError, match="finite"):
        sample_theta_tilted(MARGINALS, shift_z={"C_e": np.inf}, **kwargs)
