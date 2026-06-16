"""Tests for M2 prior sampling (``bep_reliability_engine.sampling``).

Executable contract for the approved M2 interface, written before the sampler
is implemented (the M4 precedent). Two tiers:

* **Container tests** exercise the inert data holders (:class:`MarginalSpec`,
  :class:`ThetaSample`) and pass now.
* **Sampler-contract tests** call :func:`sample_theta` and are expected to fail
  with ``NotImplementedError`` until ``sampling.py`` is filled in. They pin the
  five behaviours the user required — correlation recovery, marginal recovery,
  LHS stratification (accounting for the correlation perturbation),
  reproducibility under a fixed seed, and the two-population fallback path.

Marginal values are physically representative of the Tokachi A_c / A_g
stratigraphy (matching ``tests/test_hydraulics.py``): k_aq ~ 2e-3 m/s (A_g),
k_bl ~ 2e-6 m/s (A_c), d_70 ~ 2e-4 m, gamma_s_sub ~ 10 kN/m^3, C_e ~ 0.014.
The COVs are fixed by spec §7; the means are site-stand-ins. The expected
lognormal/normal moment-matching is recomputed here independently of the
module, so these are genuine checks rather than a mirror of the implementation.
"""

import numpy as np
import pytest
from scipy.stats import norm

from bep_reliability_engine.sampling import (
    PARAM_NAMES,
    MarginalSpec,
    ThetaSample,
    sample_theta,
)

# Spec §7 marginal table: (family, mean [physical units], COV). COVs are the
# spec values; means are Tokachi-representative stand-ins for the site values.
MARGINAL_TABLE: dict[str, tuple[str, float, float]] = {
    "k_aq": ("lognormal", 2.0e-3, 0.50),
    "d_70": ("lognormal", 2.0e-4, 0.10),
    "D_aq": ("lognormal", 20.0, 0.20),
    "D_bl": ("lognormal", 3.0, 0.20),
    "k_bl": ("lognormal", 2.0e-6, 0.50),
    "gamma_s_sub": ("normal", 10.0, 0.05),
    "C_e": ("lognormal", 0.014, 0.50),
}


def _marginals(order: list[str] | None = None) -> list[MarginalSpec]:
    """Build the seven §7 marginals (canonical order unless ``order`` given)."""
    names = order if order is not None else PARAM_NAMES
    return [
        MarginalSpec(name, MARGINAL_TABLE[name][0], *MARGINAL_TABLE[name][1:])
        for name in names
    ]


def _lognormal_params(mean: float, cov: float) -> tuple[float, float]:
    """Moment-match a lognormal to (mean, COV): returns (mu_ln, sigma_ln)."""
    sigma_ln = np.sqrt(np.log(1.0 + cov**2))
    mu_ln = np.log(mean) - 0.5 * sigma_ln**2
    return mu_ln, sigma_ln


def _uniform_percentiles(column: np.ndarray, name: str) -> np.ndarray:
    """Map a physical-unit column back to its marginal CDF value (in [0, 1]).

    For a monotone marginal transform of a stratified LHS uniform this round
    trips to the original uniform, so it is the natural coordinate for the
    stratification check.
    """
    family, mean, cov = MARGINAL_TABLE[name]
    if family == "lognormal":
        mu_ln, sigma_ln = _lognormal_params(mean, cov)
        z = (np.log(column) - mu_ln) / sigma_ln
    else:
        z = (column - mean) / (mean * cov)
    return norm.cdf(z)


def _is_perfectly_stratified(u: np.ndarray, n: int) -> bool:
    """True iff each of the n equal strata of [0, 1) holds exactly one point."""
    bins = np.clip(np.floor(u * n).astype(int), 0, n - 1)
    return np.array_equal(np.sort(bins), np.arange(n))


def _is_approximately_uniform(u: np.ndarray, n_bins: int = 20) -> bool:
    """True if a coarse histogram of u is within 50% of the flat expectation."""
    counts, _ = np.histogram(u, bins=n_bins, range=(0.0, 1.0))
    expected = u.size / n_bins
    return bool(np.all(np.abs(counts - expected) <= 0.5 * expected))


def _occupied_strata(u: np.ndarray, n: int) -> int:
    """How many of the n equal strata of [0, 1) contain at least one point.

    Equals n for a perfectly stratified column and drops below n once
    correlation perturbs the column (some strata empty, others doubled); a
    coverage measure that does not require perfection.
    """
    bins = np.clip(np.floor(u * n).astype(int), 0, n - 1)
    return int(np.unique(bins).size)


# ===========================================================================
# Container tests (pass now; independent of the sampler implementation)
# ===========================================================================


def test_param_names_is_the_canonical_order() -> None:
    """M2 owns the one authoritative column order consumed by M4/M6/M8."""
    assert PARAM_NAMES == [
        "k_aq",
        "d_70",
        "D_aq",
        "D_bl",
        "k_bl",
        "gamma_s_sub",
        "C_e",
    ]


def test_marginalspec_rejects_unknown_name() -> None:
    with pytest.raises(ValueError):
        MarginalSpec("not_a_param", "lognormal", 1.0, 0.5)


def test_marginalspec_rejects_bad_family() -> None:
    with pytest.raises(ValueError):
        MarginalSpec("k_aq", "weibull", 1.0e-3, 0.5)


def test_marginalspec_rejects_negative_cov() -> None:
    with pytest.raises(ValueError):
        MarginalSpec("D_aq", "lognormal", 20.0, -0.1)


def test_marginalspec_rejects_nonpositive_lognormal_mean() -> None:
    with pytest.raises(ValueError):
        MarginalSpec("k_aq", "lognormal", 0.0, 0.5)


def test_normal_marginal_allows_any_mean_sign() -> None:
    """Only lognormals require a positive mean; normals do not."""
    spec = MarginalSpec("gamma_s_sub", "normal", 10.0, 0.05)
    assert spec.family == "normal"


def test_theta_sample_named_access() -> None:
    """ThetaSample exposes both the ndarray view and named-column access."""
    matrix = np.arange(15.0).reshape(5, 3)
    names = ["k_aq", "d_70", "D_aq"]
    sample = ThetaSample(theta_matrix=matrix, param_names=names)

    assert sample.n_samples == 5
    np.testing.assert_array_equal(sample.column("d_70"), matrix[:, 1])
    assert set(sample.as_named_dict()) == set(names)
    np.testing.assert_array_equal(sample.as_named_dict()["D_aq"], matrix[:, 2])


def test_theta_sample_default_param_names_are_canonical() -> None:
    sample = ThetaSample(theta_matrix=np.zeros((2, 7)))
    assert sample.param_names == PARAM_NAMES
    # A copy, not the shared module list (mutating must not corrupt PARAM_NAMES).
    assert sample.param_names is not PARAM_NAMES


def test_theta_sample_unknown_column_raises_keyerror() -> None:
    sample = ThetaSample(theta_matrix=np.zeros((2, 7)))
    with pytest.raises(KeyError):
        sample.column("permeability")


# ===========================================================================
# Sampler-contract tests (fail with NotImplementedError until implemented)
# ===========================================================================


def test_shape_dtype_and_param_names() -> None:
    """theta_matrix is (N, 7) float64 in canonical order; names are a copy."""
    n = 256
    sample = sample_theta(
        _marginals(),
        seed=20260616,
        rho_log_kaq_d70=0.6,
        d70_interpretation="matrix",
        n_samples=n,
    )
    assert sample.theta_matrix.shape == (n, 7)
    assert sample.theta_matrix.dtype == np.float64
    assert sample.param_names == PARAM_NAMES
    assert sample.n_samples == n


def test_marginals_supplied_out_of_order_are_canonicalized() -> None:
    """Specs may arrive in any order; columns come back canonical."""
    shuffled = list(reversed(PARAM_NAMES))
    sample = sample_theta(
        _marginals(order=shuffled),
        seed=7,
        rho_log_kaq_d70=0.6,
        d70_interpretation="matrix",
        n_samples=256,
    )
    assert sample.param_names == PARAM_NAMES
    # k_aq (a lognormal with COV 0.50) must land in column 0, not column 6.
    assert sample.column("k_aq").mean() == pytest.approx(2.0e-3, rel=0.1)


@pytest.mark.parametrize("rho", [-0.5, 0.0, 0.6])
def test_correlation_recovery_in_log_space(rho: float) -> None:
    """Empirical log-space corr(k_aq, d_70) recovers the specified target.

    The target is stated in log space, so for the lognormal-lognormal pair it
    is the Gaussian-copula correlation directly and must be reproduced by the
    correlation of the column logarithms within LHS sampling tolerance.
    """
    n = 20_000
    sample = sample_theta(
        _marginals(),
        seed=11,
        rho_log_kaq_d70=rho,
        d70_interpretation="matrix",
        n_samples=n,
    )
    log_k = np.log(sample.column("k_aq"))
    log_d = np.log(sample.column("d_70"))
    empirical = float(np.corrcoef(log_k, log_d)[0, 1])
    assert empirical == pytest.approx(rho, abs=0.02)


def test_marginal_recovery_all_seven_parameters() -> None:
    """Empirical mean and COV recover the spec for every marginal."""
    n = 20_000
    sample = sample_theta(
        _marginals(),
        seed=2024,
        rho_log_kaq_d70=0.6,
        d70_interpretation="matrix",
        n_samples=n,
    )
    for name, (_family, mean, cov) in MARGINAL_TABLE.items():
        col = sample.column(name)
        emp_mean = float(col.mean())
        emp_cov = float(col.std(ddof=1) / col.mean())
        assert emp_mean == pytest.approx(mean, rel=0.03), name
        assert emp_cov == pytest.approx(cov, rel=0.10), name


def test_lhs_stratification_with_correlation_perturbation() -> None:
    """Independent axes keep perfect LHS; the correlated pair keeps good
    coverage (not demanded perfect), with the anchor cleaner than the
    conditioned variable.

    Imposing the k_aq-d_70 correlation necessarily perturbs the marginal
    stratification of the pair, so the pair is checked for *good coverage*
    rather than for being untouched. The five variables the correlation does
    not touch keep pristine one-per-stratum LHS. The approved k_aq-anchor
    construction puts the perturbation on d_70, so k_aq occupies strictly more
    fine strata than d_70 — the asymmetry of approved decision #1 — but neither
    member of the pair is required to be perfectly stratified.
    """
    n = 2_000
    sample = sample_theta(
        _marginals(),
        seed=99,
        rho_log_kaq_d70=0.6,
        d70_interpretation="matrix",
        n_samples=n,
    )
    # Variables untouched by the correlation keep pristine one-per-stratum LHS.
    for name in ["D_aq", "D_bl", "k_bl", "gamma_s_sub", "C_e"]:
        u = _uniform_percentiles(sample.column(name), name)
        assert _is_perfectly_stratified(u, n), name

    # The correlated pair: coverage still good, not demanded perfect (check #4).
    u_kaq = _uniform_percentiles(sample.column("k_aq"), "k_aq")
    u_d70 = _uniform_percentiles(sample.column("d_70"), "d_70")
    assert _is_approximately_uniform(u_kaq)
    assert _is_approximately_uniform(u_d70)

    # Approved asymmetry: the anchor covers more strata than the conditioned
    # variable, verified by occupancy rather than a hard perfect-stratification
    # assertion on either pair member.
    assert _occupied_strata(u_kaq, n) > _occupied_strata(u_d70, n)


def test_reproducibility_under_fixed_seed() -> None:
    """Same seed -> bit-identical matrix; different seed -> different matrix."""
    kwargs = dict(
        rho_log_kaq_d70=0.6,
        d70_interpretation="matrix",
        n_samples=512,
    )
    a = sample_theta(_marginals(), seed=12345, **kwargs)
    b = sample_theta(_marginals(), seed=12345, **kwargs)
    c = sample_theta(_marginals(), seed=54321, **kwargs)

    np.testing.assert_array_equal(a.theta_matrix, b.theta_matrix)
    assert not np.array_equal(a.theta_matrix, c.theta_matrix)


def test_two_population_fallback_decouples_kaq_and_d70() -> None:
    """The two-population mode samples k_aq and d_70 independently.

    The decoupled fallback (spec §7, §13): even with a non-zero
    ``rho_log_kaq_d70`` supplied, no correlation is imposed, so the empirical
    log-space correlation is ~0 and *both* k_aq and d_70 regain perfect LHS
    stratification. The grain-size interpretation is recorded in metadata.
    """
    n = 20_000
    sample = sample_theta(
        _marginals(),
        seed=303,
        rho_log_kaq_d70=0.6,  # supplied but must NOT be imposed
        d70_interpretation="bulk",
        n_samples=n,
        coupling="two_population",
    )
    log_k = np.log(sample.column("k_aq"))
    log_d = np.log(sample.column("d_70"))
    assert float(np.corrcoef(log_k, log_d)[0, 1]) == pytest.approx(0.0, abs=0.02)

    # d_70 is no longer perturbed: both correlated-pair columns are stratified.
    for name in ("k_aq", "d_70"):
        u = _uniform_percentiles(sample.column(name), name)
        assert _is_perfectly_stratified(u, n)

    assert sample.metadata["coupling"] == "two_population"
    assert sample.metadata["rho_imposed"] is False
    assert sample.metadata["d70_interpretation"] == "bulk"


def test_metadata_records_provenance_in_correlated_mode() -> None:
    """Metadata carries the §8 provenance fields for the HDF5 attrs."""
    sample = sample_theta(
        _marginals(),
        seed=41,
        rho_log_kaq_d70=0.55,
        d70_interpretation="matrix",
        n_samples=256,
    )
    md = sample.metadata
    assert md["sampling_scheme"] == "latin_hypercube"
    assert md["coupling"] == "correlated"
    assert md["correlation_space"] == "log"
    assert md["rho_log_kaq_d70"] == pytest.approx(0.55)
    assert md["rho_imposed"] is True
    assert md["d70_interpretation"] == "matrix"
    assert md["seed"] == 41
    assert md["c_e_stochastic"] is True
    assert md["prior_covs"]["k_aq"] == pytest.approx(0.50)
    assert md["prior_families"]["gamma_s_sub"] == "normal"


def test_bounds_clip_pathological_tails() -> None:
    """Optional per-parameter bounds clamp the physical samples (spec §12 fm2)."""
    lo, hi = 50e-6, 1e-3
    sample = sample_theta(
        _marginals(),
        seed=88,
        rho_log_kaq_d70=0.6,
        d70_interpretation="matrix",
        n_samples=5_000,
        bounds={"d_70": (lo, hi)},
    )
    d70 = sample.column("d_70")
    assert d70.min() >= lo
    assert d70.max() <= hi
