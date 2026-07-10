"""Tests for the M-adjacent convergence-study statistics (``convergence.py``).

These cover the *statistical* primitives and the replicate driver in isolation
(no physics): the analytic binomial reference, the empirical CoV, the
N-sufficiency inverse, reproducibility from the seed root, and — as a genuine
end-to-end check that the injected sampler really stratifies — that LHS beats
crude Monte Carlo on a single-marginal-threshold integrand (the case where
stratification is provably effective). The empirical LHS-vs-crude *tail* verdict
is the study's job (ADR-0031), not asserted here.
"""

from __future__ import annotations

import numpy as np
import pytest

from bep_reliability_engine.convergence import (
    PF_COV_TARGET,
    binomial_cov,
    empirical_cov,
    n_for_cov_target,
    run_replicates,
)
from bep_reliability_engine.sampling import MarginalSpec

# A plausible seven-marginal prior (KP58.8-like), built directly so the tests
# carry no config/data-file dependency.
_MARGINALS = [
    MarginalSpec("k_aq", "lognormal", 2.0e-3, 0.50),
    MarginalSpec("d_70", "lognormal", 5.3e-4, 0.30),
    MarginalSpec("D_aq", "lognormal", 8.0, 0.10),
    MarginalSpec("D_bl", "lognormal", 0.85, 0.167),
    MarginalSpec("k_bl", "lognormal", 1.0e-6, 0.50),
    MarginalSpec("gamma_bl_sub", "lognormal", 6.9, 0.056),
    MarginalSpec("C_e", "lognormal", 0.055, 0.782),
]
_SAMPLER_KWARGS = dict(
    rho_log_kaq_d70=0.0,
    d70_interpretation="matrix",
    coupling="two_population",
    bounds={"d_70": (5.0e-5, 1.0e-3)},
)


def _lognormal_median(spec: MarginalSpec) -> float:
    sigma_ln = np.sqrt(np.log(1.0 + spec.cov**2))
    mu_ln = np.log(spec.mean) - 0.5 * sigma_ln**2
    return float(np.exp(mu_ln))


def _threshold_evaluate(threshold: float):
    """Injected physics stand-in: failure iff C_e exceeds ``threshold``.

    A single-marginal indicator, so LHS (which stratifies the C_e axis) drives
    the estimator variance far below the crude-MC binomial value — the property
    the test asserts. Returns the same indicator for both branches.
    """

    def evaluate(theta_sample, seepage):
        c_e = theta_sample.column("C_e")
        fail = c_e > threshold
        return fail, fail

    return evaluate


def _no_length(_replicate_index: int, _n_samples: int):
    return None


def test_binomial_cov_known_value_and_domain():
    # p = 0.5, N = 100 -> sqrt(0.5 / 50) = 0.1
    assert binomial_cov(0.5, 100) == pytest.approx(0.1)
    # Rarer events have larger CoV at fixed N.
    assert binomial_cov(1e-3, 100_000) > binomial_cov(1e-1, 100_000)
    # Degenerate probabilities are undefined.
    assert np.isnan(binomial_cov(0.0, 100))
    assert np.isnan(binomial_cov(1.0, 100))


def test_n_for_cov_target_inverts_binomial_cov():
    for p in (0.5, 1e-2, 1e-3):
        n = n_for_cov_target(p, PF_COV_TARGET)
        assert binomial_cov(p, n) == pytest.approx(PF_COV_TARGET, rel=1e-9)
    # p = 0.5 at the 5% target needs (1-p)/(p*0.05^2) = 400 samples.
    assert n_for_cov_target(0.5, 0.05) == pytest.approx(400.0)
    # The 1/p blow-up: an order of magnitude rarer needs ~an order more N.
    assert n_for_cov_target(1e-3) > 9 * n_for_cov_target(1e-2)


def test_empirical_cov_basic():
    assert empirical_cov(np.array([0.2, 0.2, 0.2])) == pytest.approx(0.0)
    assert np.isnan(empirical_cov(np.array([0.0, 0.0, 0.0])))
    assert np.isnan(empirical_cov(np.array([0.3])))  # need >= 2 replicates
    p = np.array([0.10, 0.12, 0.08, 0.11, 0.09])
    assert empirical_cov(p) == pytest.approx(p.std(ddof=1) / p.mean())


def test_run_replicates_reproducible_and_shaped():
    kwargs = dict(
        marginals=_MARGINALS,
        sampler_kwargs=_SAMPLER_KWARGS,
        evaluate=_threshold_evaluate(_lognormal_median(_MARGINALS[-1])),
        draw_length=_no_length,
        n_samples=2000,
        n_replicates=8,
        seed_root=12345,
        stratified=True,
        scheme_tag=0,
        level_tag=0,
    )
    a = run_replicates(**kwargs)
    b = run_replicates(**kwargs)
    assert a.p_f_trans.shape == (8,)
    np.testing.assert_array_equal(a.p_f_trans, b.p_f_trans)  # seed-reproducible
    assert a.scheme == "lhs"
    # Thresholding at the marginal median -> P_f ~ 0.5.
    assert a.mean_p_f("transient") == pytest.approx(0.5, abs=0.02)


def test_lhs_beats_crude_on_single_marginal_threshold():
    # For a single-marginal indicator, LHS stratifies the governing axis and its
    # estimator CoV is far below the crude-MC binomial value. This confirms the
    # injected sampler genuinely stratifies through the full M2 pipeline.
    threshold = _lognormal_median(_MARGINALS[-1])  # C_e median -> p ~ 0.5
    common = dict(
        marginals=_MARGINALS,
        sampler_kwargs=_SAMPLER_KWARGS,
        evaluate=_threshold_evaluate(threshold),
        draw_length=_no_length,
        n_samples=1000,
        n_replicates=30,
        seed_root=2024,
        level_tag=1,
    )
    lhs = run_replicates(stratified=True, scheme_tag=0, **common)
    crude = run_replicates(stratified=False, scheme_tag=1, **common)

    cov_lhs = lhs.cov("transient")
    cov_crude = crude.cov("transient")
    # Both unbiased at ~0.5.
    assert lhs.mean_p_f("transient") == pytest.approx(0.5, abs=0.02)
    assert crude.mean_p_f("transient") == pytest.approx(0.5, abs=0.02)
    # Crude tracks the binomial law; LHS is dramatically tighter on this axis.
    assert cov_crude == pytest.approx(binomial_cov(0.5, 1000), rel=0.6)
    assert cov_lhs < 0.25 * cov_crude
