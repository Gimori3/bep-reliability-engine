"""Tests for the GSA machinery (``bep_reliability_engine.sensitivity``).

ADR-0033 §5: the estimator stack must be validated against analytical
benchmarks with known Sobol' indices **before** it is trusted on the engine.
Four benchmarks, each targeting a distinct feature the engine analysis leans
on:

1. **Ishigami function** (Primer §4.6 / Ch. 5 Ex. 2; A = 7, B = 0.1) —
   interactions and a pure-interaction factor (S_3 = 0, ST_3 > 0).
2. **Sobol' g-function at k = 8** (Primer Ch. 5 Ex. 3 coefficient set) —
   the engine's dimensionality with a strong importance contrast.
3. **Linear-Gaussian threshold indicator** — a binary QoI (the engine's Y1/Y2
   failure indicators) with quadrature ground truth.
4. **Correlated lognormal pair through the production copula** — the
   ADR-0033 §2 Rosenblatt/generator route with closed-form full/independent
   indices, validating the Nataf companion machinery on the exact M2
   construction.

Plus structural tests: design layout, determinism, the M2 bit-identity pin
of the generator -> physical map, estimator invariants (additive model,
degenerate output), and bootstrap/replicate aggregation sanity.

All tolerances are set for the fixed seeds below (deterministic tests) with
a comfortable margin over the observed estimator error.
"""

import numpy as np
import pytest
from scipy.stats import norm
from scipy.stats.qmc import LatinHypercube

from bep_reliability_engine.sampling import (
    PARAM_NAMES,
    MarginalSpec,
    sample_theta,
)
from bep_reliability_engine.sensitivity import (
    GsaInputSpace,
    aggregate_replicates,
    bootstrap_indices,
    generate_design,
    sobol_indices,
    split_outputs,
    stack_evaluation_matrix,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_replicated(model, k, n_base, n_replicates, seed0, names=None):
    """Evaluate ``model(U)`` on R independent scrambled designs; return reps."""
    reps = []
    for r in range(n_replicates):
        u_a, u_b = generate_design(k, n_base, seed=seed0 + r)
        u_all = stack_evaluation_matrix(u_a, u_b)
        y_all = model(u_all)
        y_a, y_b, y_abi = split_outputs(y_all, n_base, k)
        reps.append(sobol_indices(y_a, y_b, y_abi, names=names))
    return reps


def _canonical_marginals():
    """The seven canonical marginals with the production-style parameters."""
    return (
        MarginalSpec("k_aq", "lognormal", 2.0e-3, 0.50),
        MarginalSpec("d_70", "lognormal", 5.3e-4, 0.30),
        MarginalSpec("D_aq", "lognormal", 8.0, 0.10),
        MarginalSpec("D_bl", "lognormal", 0.85, 0.167),
        MarginalSpec("k_bl", "lognormal", 1.0e-6, 0.50),
        MarginalSpec("gamma_bl_sub", "lognormal", 6.9, 0.056),
        MarginalSpec("C_e", "lognormal", 0.055, 0.782),
    )


# ---------------------------------------------------------------------------
# Design structure
# ---------------------------------------------------------------------------


def test_design_shapes_and_radial_structure():
    """A/B are (N, k); A_B^(i) differs from A in exactly column i (from B)."""
    k, n = 5, 64
    u_a, u_b = generate_design(k, n, seed=7)
    assert u_a.shape == (n, k) and u_b.shape == (n, k)
    assert np.all((u_a > 0) & (u_a < 1)) and np.all((u_b > 0) & (u_b < 1))
    assert not np.array_equal(u_a, u_b)

    u_all = stack_evaluation_matrix(u_a, u_b)
    assert u_all.shape == ((k + 2) * n, k)
    assert np.array_equal(u_all[:n], u_a)
    assert np.array_equal(u_all[n : 2 * n], u_b)
    for i in range(k):
        block = u_all[(2 + i) * n : (3 + i) * n]
        assert np.array_equal(block[:, i], u_b[:, i])
        other = [j for j in range(k) if j != i]
        assert np.array_equal(block[:, other], u_a[:, other])


def test_design_determinism_and_power_of_two_guard():
    """Same seed reproduces the design bit-for-bit; non-2^m N is refused."""
    u_a1, u_b1 = generate_design(3, 32, seed=123)
    u_a2, u_b2 = generate_design(3, 32, seed=123)
    assert np.array_equal(u_a1, u_a2) and np.array_equal(u_b1, u_b2)
    u_a3, _ = generate_design(3, 32, seed=124)
    assert not np.array_equal(u_a1, u_a3)
    with pytest.raises(ValueError, match="power of two"):
        generate_design(3, 100, seed=1)


def test_split_outputs_roundtrip():
    """split_outputs inverts the stacking order, including bool casting."""
    k, n = 4, 16
    y_all = np.arange((k + 2) * n)
    y_a, y_b, y_abi = split_outputs(y_all, n, k)
    assert np.array_equal(y_a, np.arange(n, dtype=float))
    assert np.array_equal(y_b, np.arange(n, 2 * n, dtype=float))
    assert y_abi.shape == (k, n)
    assert np.array_equal(y_abi[2], np.arange(4 * n, 5 * n, dtype=float))
    y_bool = split_outputs(np.ones((k + 2) * n, dtype=bool), n, k)[0]
    assert y_bool.dtype == np.float64


# ---------------------------------------------------------------------------
# Benchmark 1: Ishigami (Primer Ch. 5 Ex. 2; A = 7, B = 0.1)
# ---------------------------------------------------------------------------

ISHIGAMI_A, ISHIGAMI_B = 7.0, 0.1


def _ishigami(u):
    x = -np.pi + 2.0 * np.pi * u
    return (
        np.sin(x[:, 0])
        + ISHIGAMI_A * np.sin(x[:, 1]) ** 2
        + ISHIGAMI_B * x[:, 2] ** 4 * np.sin(x[:, 0])
    )


def _ishigami_exact():
    a, b = ISHIGAMI_A, ISHIGAMI_B
    v1 = 0.5 * (1.0 + b * np.pi**4 / 5.0) ** 2
    v2 = a**2 / 8.0
    v13 = b**2 * np.pi**8 * (1.0 / 18.0 - 1.0 / 50.0)
    v = v1 + v2 + v13
    s = np.array([v1 / v, v2 / v, 0.0])
    st = np.array([(v1 + v13) / v, v2 / v, v13 / v])
    return s, st


def test_ishigami_indices_match_analytic():
    """S and ST reproduce the Primer's Ishigami decomposition within 0.01."""
    s_exact, st_exact = _ishigami_exact()
    reps = _run_replicated(_ishigami, k=3, n_base=4096, n_replicates=5, seed0=42)
    agg = aggregate_replicates(reps)
    np.testing.assert_allclose(agg["S_mean"], s_exact, atol=0.01)
    np.testing.assert_allclose(agg["ST_mean"], st_exact, atol=0.01)
    # The pure-interaction factor: S_3 = 0 but ST_3 clearly positive.
    assert agg["ST_mean"][2] > 0.2
    # sum(S) < 1 signals interactions (Primer p. 167).
    assert sum(agg["S_mean"]) < 0.9


# ---------------------------------------------------------------------------
# Benchmark 2: Sobol' g-function at k = 8 (Primer Ch. 5 Ex. 3)
# ---------------------------------------------------------------------------

G_COEFFS = np.array([0.0, 1.0, 4.5, 9.0, 99.0, 99.0, 99.0, 99.0])


def _g_function(u):
    return np.prod((np.abs(4.0 * u - 2.0) + G_COEFFS) / (1.0 + G_COEFFS), axis=1)


def _g_function_exact():
    v_i = 1.0 / (3.0 * (1.0 + G_COEFFS) ** 2)
    v = np.prod(1.0 + v_i) - 1.0
    s = v_i / v
    st = np.array(
        [v_i[i] * np.prod(1.0 + np.delete(v_i, i)) / v for i in range(v_i.size)]
    )
    return s, st


def test_g_function_k8_indices_match_analytic():
    """The k = 8 g-function (engine dimensionality) within 0.015."""
    s_exact, st_exact = _g_function_exact()
    reps = _run_replicated(_g_function, k=8, n_base=4096, n_replicates=5, seed0=101)
    agg = aggregate_replicates(reps)
    np.testing.assert_allclose(agg["S_mean"], s_exact, atol=0.015)
    np.testing.assert_allclose(agg["ST_mean"], st_exact, atol=0.015)
    # Importance ranking preserved: x1 dominant, x5..x8 negligible.
    assert np.argmax(agg["ST_mean"]) == 0
    assert np.all(agg["ST_mean"][4:] < 0.01)


# ---------------------------------------------------------------------------
# Benchmark 3: linear-Gaussian threshold indicator (binary QoI ground truth)
# ---------------------------------------------------------------------------

THRESH_C = np.array([3.0, 2.0, 1.0, 0.5])
THRESH_TAU = 2.5


def _threshold_indicator(u):
    z = norm.ppf(u)
    return (z @ THRESH_C > THRESH_TAU).astype(np.float64)


def _threshold_exact():
    """Quadrature ground truth for Y = 1{sum(c_i Z_i) > tau}.

    E(Y | Z_i = z) = Phi((c_i z - tau)/s_i) with s_i = sqrt(s^2 - c_i^2), so
    V_i = E[Phi(.)^2] - P^2 by Gauss-Hermite. For the total effect,
    V(Y | Z_~i) = p(1-p) with p = Phi((w - tau)/c_i), w ~ N(0, s_i^2), so
    E[V(Y | Z_~i)] is a second 1-D quadrature and ST_i = 1 - E[V]/V ...
    (note ST_i = (V - V[E(Y|Z_~i)])/V = E[V(Y|Z_~i)]/V).
    """
    nodes, weights = np.polynomial.hermite_e.hermegauss(200)
    # hermegauss weights target exp(-z^2/2); dividing by their sum sqrt(2*pi)
    # turns the rule into expectation against the standard normal density.
    w_norm = weights / weights.sum()
    s2 = float(np.sum(THRESH_C**2))
    s = np.sqrt(s2)
    p_fail = float(norm.sf(THRESH_TAU / s))
    var_y = p_fail * (1.0 - p_fail)
    s_first = np.empty(THRESH_C.size)
    s_total = np.empty(THRESH_C.size)
    for i, c in enumerate(THRESH_C):
        s_i = np.sqrt(s2 - c**2)
        cond_mean = norm.cdf((c * nodes - THRESH_TAU) / s_i)
        v_i = float(np.sum(w_norm * cond_mean**2)) - p_fail**2
        s_first[i] = v_i / var_y
        p_cond = norm.cdf((s_i * nodes - THRESH_TAU) / c)
        e_v = float(np.sum(w_norm * p_cond * (1.0 - p_cond)))
        s_total[i] = e_v / var_y
    return s_first, s_total, p_fail


def test_threshold_indicator_indices_match_quadrature():
    """Binary-QoI indices (the engine's Y1/Y2 case) within 0.02."""
    s_exact, st_exact, p_exact = _threshold_exact()
    reps = _run_replicated(
        _threshold_indicator, k=4, n_base=8192, n_replicates=5, seed0=1001
    )
    agg = aggregate_replicates(reps)
    assert agg["mean_y_mean"] == pytest.approx(p_exact, abs=0.01)
    np.testing.assert_allclose(agg["S_mean"], s_exact, atol=0.02)
    np.testing.assert_allclose(agg["ST_mean"], st_exact, atol=0.02)


# ---------------------------------------------------------------------------
# Benchmark 4: correlated pair through the production copula (ADR-0033 §2)
# ---------------------------------------------------------------------------

RHO_TEST = 0.6


def _log_pair_model(space):
    """Y = ln(k_aq) + ln(d_70): linear in the copula Z-space, closed form."""

    def model(u):
        theta, _ = space.map_uniform(u)
        return np.log(theta[:, 0]) + np.log(theta[:, 1])

    return model


def _log_pair_exact(anchor):
    """Closed-form generator indices for Y = ln k_aq + ln d_70 under rho."""
    s1 = np.sqrt(np.log(1.0 + 0.50**2))  # sigma_ln of k_aq
    s2 = np.sqrt(np.log(1.0 + 0.30**2))  # sigma_ln of d_70
    rho = RHO_TEST
    if anchor == "k_aq":
        v_anchor = (s1 + s2 * rho) ** 2
        v_other = s2**2 * (1.0 - rho**2)
    else:
        v_anchor = (s2 + s1 * rho) ** 2
        v_other = s1**2 * (1.0 - rho**2)
    v = v_anchor + v_other
    return v_anchor / v, v_other / v


@pytest.mark.parametrize("anchor", ["k_aq", "d_70"])
def test_correlated_generator_indices_match_closed_form(anchor):
    """Full (anchor) and independent (other) indices match the closed form.

    Validates the Rosenblatt/generator route on the exact M2 copula
    construction: the anchor generator carries the full Kucherenko
    contribution (own effect plus the correlated share), the other pair
    member's generator only its decorrelated part (Mara-Tarantola).
    """
    space = GsaInputSpace(
        marginals=_canonical_marginals(),
        bounds=None,
        coupling="correlated",
        rho_log_kaq_d70=RHO_TEST,
        anchor=anchor,
    )
    s_anchor_exact, s_other_exact = _log_pair_exact(anchor)
    reps = _run_replicated(
        _log_pair_model(space),
        k=space.k,
        n_base=2048,
        n_replicates=5,
        seed0=2024,
        names=space.names,
    )
    agg = aggregate_replicates(reps)
    i_kaq = space.names.index("k_aq")
    i_d70 = space.names.index("d_70")
    i_anchor = i_kaq if anchor == "k_aq" else i_d70
    i_other = i_d70 if anchor == "k_aq" else i_kaq
    assert agg["S_mean"][i_anchor] == pytest.approx(s_anchor_exact, abs=0.015)
    assert agg["S_mean"][i_other] == pytest.approx(s_other_exact, abs=0.015)
    # Additive-in-Z model: ST == S per generator; all other generators ~ 0.
    np.testing.assert_allclose(agg["ST_mean"], agg["S_mean"], atol=0.02)
    others = [j for j in range(space.k) if j not in (i_kaq, i_d70)]
    assert np.all(np.abs(agg["S_mean"][others]) < 0.01)
    # Role labels for the driver's JSON record.
    roles = space.generator_roles
    assert roles[anchor] == "full (incl. correlated share)"
    other_name = "d_70" if anchor == "k_aq" else "k_aq"
    assert roles[other_name] == "independent (decorrelated)"


def test_correlated_space_at_rho_zero_equals_two_population():
    """The Nataf companion collapses to the production map at rho = 0."""
    marginals = _canonical_marginals()
    u = LatinHypercube(d=7, seed=5).random(256)
    space_ind = GsaInputSpace(marginals=marginals)
    space_rho0 = GsaInputSpace(
        marginals=marginals, coupling="correlated", rho_log_kaq_d70=0.0
    )
    theta_ind, _ = space_ind.map_uniform(u)
    theta_rho0, _ = space_rho0.map_uniform(u)
    np.testing.assert_array_equal(theta_ind, theta_rho0)


# ---------------------------------------------------------------------------
# M2 bit-identity pin (ADR-0033 §5)
# ---------------------------------------------------------------------------

BOUNDS = {"d_70": (5.0e-5, 1.0e-3)}


@pytest.mark.parametrize(
    "coupling, rho", [("two_population", 0.0), ("correlated", 0.6)]
)
def test_map_uniform_bit_identical_to_sample_theta(coupling, rho):
    """GsaInputSpace.map_uniform reproduces M2's theta bit-for-bit.

    Reconstructs the same LHS design M2 draws internally (same scipy QMC
    seed), pushes it through the GSA map, and requires bit-identity with
    ``sample_theta`` — the guarantee that the GSA analyzes the production
    prior, not an approximation (ADR-0033 §5). Covers both the production
    two-population mode and the Nataf companion (k_aq anchor, M2's own
    construction).
    """
    seed, n = 314159, 512
    marginals = _canonical_marginals()
    reference = sample_theta(
        marginals,
        seed=seed,
        rho_log_kaq_d70=rho,
        d70_interpretation="matrix",
        n_samples=n,
        coupling=coupling,
        bounds=BOUNDS,
    )
    design = LatinHypercube(d=len(PARAM_NAMES), seed=seed).random(n)
    space = GsaInputSpace(
        marginals=marginals,
        bounds=BOUNDS,
        coupling=coupling,
        rho_log_kaq_d70=rho,
        anchor="k_aq",
    )
    theta, seepage = space.map_uniform(design)
    np.testing.assert_array_equal(theta, reference.theta_matrix)
    assert seepage is None


def test_stochastic_seepage_column():
    """With L stochastic the eighth generator maps to a lognormal L."""
    space = GsaInputSpace(
        marginals=_canonical_marginals(),
        seepage_mean_m=35.0,
        seepage_cov=0.2,
    )
    assert space.k == 8
    assert space.names[-1] == "L"
    u = LatinHypercube(d=8, seed=9).random(4096)
    theta, seepage = space.map_uniform(u)
    assert theta.shape == (4096, 7) and seepage.shape == (4096,)
    assert seepage.mean() == pytest.approx(35.0, rel=0.02)
    assert seepage.std() / seepage.mean() == pytest.approx(0.2, rel=0.05)


# ---------------------------------------------------------------------------
# Estimator invariants, bootstrap, aggregation
# ---------------------------------------------------------------------------


def test_additive_model_invariants():
    """Additive model: ST == S within noise and sum(S) == 1 within noise."""
    weights = np.array([1.0, 2.0, 3.0])

    def model(u):
        return u @ weights

    reps = _run_replicated(model, k=3, n_base=4096, n_replicates=5, seed0=77)
    agg = aggregate_replicates(reps)
    exact = weights**2 / np.sum(weights**2)  # Var(w*U) prop. to w^2/12
    np.testing.assert_allclose(agg["S_mean"], exact, atol=0.01)
    np.testing.assert_allclose(agg["ST_mean"], agg["S_mean"], atol=0.01)
    assert sum(agg["S_mean"]) == pytest.approx(1.0, abs=0.02)


def test_degenerate_output_yields_nan_not_raise():
    """A zero-variance output (dead indicator level) -> NaN indices."""
    n, k = 64, 3
    y = np.zeros((k + 2) * n)
    y_a, y_b, y_abi = split_outputs(y, n, k)
    result = sobol_indices(y_a, y_b, y_abi)
    assert np.all(np.isnan(result.S)) and np.all(np.isnan(result.ST))
    assert result.var_y == 0.0


def test_bootstrap_ci_brackets_analytic_ishigami():
    """Row-bootstrap CIs bracket the analytic Ishigami indices."""
    s_exact, st_exact = _ishigami_exact()
    n_base = 4096
    u_a, u_b = generate_design(3, n_base, seed=55)
    y_all = _ishigami(stack_evaluation_matrix(u_a, u_b))
    y_a, y_b, y_abi = split_outputs(y_all, n_base, 3)
    ci = bootstrap_indices(y_a, y_b, y_abi, n_boot=400, seed=8, confidence=0.95)
    assert np.all(ci["S_lo"] <= s_exact + 0.01)
    assert np.all(ci["S_hi"] >= s_exact - 0.01)
    assert np.all(ci["ST_lo"] <= st_exact + 0.01)
    assert np.all(ci["ST_hi"] >= st_exact - 0.01)
    assert ci["S_boot"].shape == (400, 3)


def test_aggregate_replicates_requires_two_and_reports_se():
    """t-aggregation needs R >= 2; SE shrinks the CI around the mean."""
    reps = _run_replicated(_ishigami, k=3, n_base=1024, n_replicates=4, seed0=3)
    with pytest.raises(ValueError, match="two replicates"):
        aggregate_replicates(reps[:1])
    agg = aggregate_replicates(reps)
    assert agg["n_replicates"] == 4
    assert np.all(agg["S_lo"] <= agg["S_mean"])
    assert np.all(agg["S_hi"] >= agg["S_mean"])
    assert np.all(agg["S_se"] > 0)


def test_interaction_gap_and_sum_s_properties():
    """SobolIndices convenience accessors are consistent with S/ST."""
    reps = _run_replicated(_ishigami, k=3, n_base=1024, n_replicates=2, seed0=11)
    rep = reps[0]
    np.testing.assert_array_equal(rep.interaction_gap, rep.ST - rep.S)
    assert rep.sum_S == pytest.approx(float(np.sum(rep.S)))
