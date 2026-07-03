"""Tests for M9 fragility assembler (``bep_reliability_engine.fragility``).

Executable contract for the M9 interface, written in the same pre-implementation
pattern as M2/M5/M7/M8: ``fragility.py`` is not implemented yet, so these tests
fail at import until it exists. Every assertion below is the contract the
implementation must satisfy. They lock the three deliverables the spec assigns
to M9 (spec §1, §2, §8, §11):

1. **Lognormal fragility fitting (parameter recovery).** A lognormal fragility
   curve ``P_f(h) = Phi((ln h - mu)/sigma)`` is fit to an *empirical point set*
   ``(conditioning_grid, P_f_raw)``; given points that lie exactly on a known
   curve the fit recovers ``(mu, sigma)``, and the full assembler recovers the
   static and transient parameters from stratified failure matrices.
2. **Bootstrap confidence bands.** Resampling the realizations yields a
   ``(lo, hi)`` band per curve that brackets the central fitted curve at every
   conditioning level and is a proper ``[0, 1]`` interval.
3. **HDF5 + JSON-sidecar round trip.** ``save``/``load`` preserve *both* failure
   matrices bit-for-bit and *every* metadata field, plus the retained
   ``theta_matrix``, grids, raw point estimates, fitted curves and bands.

Two points where the spec leaves the contract open and these tests pin a choice
(flagged for review):

* **Fit target.** The spec §2 says "fits lognormal fragility curves ... to the
  empirical point sets" and §10 names ``scipy.stats`` lognormal fitting. These
  tests fit to the ``(h_i, P_f_i)`` points (probit/least-squares on the curve),
  not to per-realization capacities via ``lognorm.fit``. The exact-recovery test
  feeds analytic ``P_f`` points (no failure matrix), which locks the fitter to
  consume ``(grid, P_f)`` pairs.
* **Band keys.** ``FragilityResult.bootstrap_bands`` is keyed ``'static'`` and
  ``'transient'`` (spec §2 types it only as ``dict[curve -> (lo, hi)]``).

Field names and order of :class:`FragilityResult` follow the spec §2 listing
exactly (including ``failure_matrix_stat`` / ``failure_matrix_tran`` and the full
``metadata`` block). The data used here is synthetic and analytic so the
*assembler wiring* — not the upstream physics, which M4/M6/M7/M8 already test —
is what is under test.
"""

import json
from dataclasses import fields, is_dataclass

import h5py
import numpy as np
import pytest
from scipy.stats import norm

from bep_reliability_engine.fragility import (
    FragilityResult,
    LognormFragility,
    assemble_fragility,
    fit_lognormal_fragility,
    upscale_length_effect,
)

# Canonical theta column order (spec §2, M2 contract). M9 only retains the
# matrix and its names; the column contents are immaterial to the fragility math.
PARAM_NAMES = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]

# FragilityResult field listing, in the exact spec §2 order (the "defines the
# dataclass exactly per the spec" requirement).
EXPECTED_FRAGILITY_FIELDS = (
    "conditioning_grid",
    "P_f_static_raw",
    "P_f_trans_raw",
    "P_f_static_fit",
    "P_f_trans_fit",
    "bootstrap_bands",
    "theta_matrix",
    "param_names",
    "failure_matrix_stat",
    "failure_matrix_tran",
    "metadata",
)


def _analytic_pf(conditioning_grid: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Lognormal fragility curve ``Phi((ln h - mu)/sigma)`` on the grid.

    Parameters
    ----------
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads h [m above datum], strictly positive.
    mu, sigma : float
        Location and scale of the lognormal fragility (mean and std of
        ``ln(capacity)``); ``sigma > 0``.

    Returns
    -------
    numpy.ndarray, shape (N_h,)
        Exact failure probabilities at each conditioning level.
    """
    grid = np.asarray(conditioning_grid, dtype=np.float64)
    return norm.cdf((np.log(grid) - mu) / sigma)


def _lognormal_failure_matrix(
    mu: float, sigma: float, conditioning_grid: np.ndarray, n: int
) -> np.ndarray:
    """Monotone ``(N, N_h)`` bool failure matrix matching a lognormal fragility.

    Realization ``i`` is assigned the deterministic stratified-midpoint
    lognormal "capacity" ``c_i = exp(mu + sigma * Phi^-1((i + 0.5)/N))`` and
    fails at level ``h`` iff ``c_i <= h``. The capacities are the exact midpoint
    quantiles of ``Lognormal(mu, sigma)``, so (a) the per-column failure fraction
    reproduces ``Phi((ln h - mu)/sigma)`` to ``O(1/N)`` and (b) the columns are
    monotone non-decreasing in ``h`` (physical: a higher stage fails at least as
    many realizations). This recovers ``(mu, sigma)`` without locking the fit
    method: it is consistent with both a probit fit to the column fractions and
    a per-realization capacity fit.

    Parameters
    ----------
    mu, sigma : float
        Lognormal fragility parameters (``sigma > 0``).
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning heads h [m above datum], strictly positive.
    n : int
        Number of realizations N.

    Returns
    -------
    numpy.ndarray, shape (N, N_h), dtype bool
        ``True`` where realization ``i`` has failed at level ``h_j``.
    """
    quantile_points = (np.arange(n, dtype=np.float64) + 0.5) / n
    capacities = np.exp(mu + sigma * norm.ppf(quantile_points))  # (N,)
    grid = np.asarray(conditioning_grid, dtype=np.float64)
    return capacities[:, None] <= grid[None, :]


def _metadata() -> dict:
    """A representative §8 metadata block, JSON-clean and pure-Python.

    Mixes the field types the §8 attrs list specifies — strings, floats, ints, a
    bool, ``None`` (inactive ``tau_aq``), name->value dicts and a nested config
    snapshot — so the round-trip test exercises type fidelity, not just values.
    """
    return {
        "config_hash": "a1b2c3d4e5f6",
        "code_version": "0.0.2",
        "runtime_seconds": 1234.5,
        "c_e_stochastic": True,
        "d70_interpretation": "matrix",
        "remediation_state": "none",
        "lhs_seed": 20240617,
        "cross_section_id": "tokachi_kp58",
        "segment_id": "KP58.200",
        "scenario": "historical",
        "hydrograph_source": "d4PDF",
        "aquifer_lag_active": False,
        "tau_aq": None,
        "correlation_rho_k_d70": -0.42,
        "prior_means": {
            "k_aq": 1.0e-4,
            "d_70": 2.0e-4,
            "D_aq": 3.0,
            "D_bl": 3.0,
            "k_bl": 1.0e-6,
            "gamma_bl_sub": 16.0,
            "C_e": 0.014,
        },
        "prior_covs": {
            "k_aq": 0.50,
            "d_70": 0.10,
            "D_aq": 0.20,
            "D_bl": 0.20,
            "k_bl": 0.50,
            "gamma_bl_sub": 0.05,
            "C_e": 0.50,
        },
        "config": {
            "geometry": {"L": 30.0, "z_toe": 2.0},
            "mc": {"n_samples": 256, "seed": 7},
        },
    }


# ---------------------------------------------------------------------------
# (1) Lognormal fragility fitting: parameter recovery
# ---------------------------------------------------------------------------


def test_lognormal_fit_recovers_parameters() -> None:
    """The fit recovers ``(mu, sigma)`` of the curve it is fed (spec §2, M9).

    Two legs. First, the fitter is handed an *exact* analytic point set
    ``P_f_i = Phi((ln h_i - mu)/sigma)`` (no Monte Carlo noise): a lognormal
    fragility maps to a straight line in ``(ln h, Phi^-1(P_f))`` space, so the fit
    must recover ``(mu, sigma)`` to near machine precision and the fitted curve
    must reproduce the inputs and the defining median property
    ``P_f(exp(mu)) = 0.5``. Second, the *full assembler* recovers distinct static
    and transient parameters from stratified failure matrices, proving the
    ``failure_matrix -> P_f_raw -> fit`` path is wired for both branches.
    """
    grid = np.linspace(3.0, 12.0, 19)
    mu_true, sigma_true = float(np.log(6.0)), 0.35

    p_f = _analytic_pf(grid, mu_true, sigma_true)
    assert np.all((p_f > 1e-3) & (p_f < 1 - 1e-3))  # interior: no 0/1 masking

    fit = fit_lognormal_fragility(grid, p_f)
    assert isinstance(fit, LognormFragility)
    assert fit.mu == pytest.approx(mu_true, abs=1e-4)
    assert fit.sigma == pytest.approx(sigma_true, abs=1e-4)

    # The fitted curve reproduces the empirical points and the median property.
    assert fit.probability_of_failure(float(np.exp(mu_true))) == pytest.approx(
        0.5, abs=1e-6
    )
    np.testing.assert_allclose(fit.probability_of_failure(grid), p_f, atol=1e-3)

    # Full assembler: distinct static/transient curves recovered from stratified
    # (near-exact) failure matrices. Transient fails earlier and wider than
    # static, so the two fits must come out genuinely different.
    mu_s, sigma_s = float(np.log(8.0)), 0.30
    mu_t, sigma_t = float(np.log(5.0)), 0.45
    n = 20_000
    fm_stat = _lognormal_failure_matrix(mu_s, sigma_s, grid, n)
    fm_tran = _lognormal_failure_matrix(mu_t, sigma_t, grid, n)
    theta = np.zeros((n, len(PARAM_NAMES)))

    result = assemble_fragility(
        theta,
        list(PARAM_NAMES),
        grid,
        fm_stat,
        fm_tran,
        _metadata(),
        n_bootstrap=25,
        seed=1,
    )

    # Raw point estimates are the per-column failure fractions of the matrices,
    # matching the analytic curve they were built from.
    np.testing.assert_allclose(
        result.P_f_static_raw, _analytic_pf(grid, mu_s, sigma_s), atol=0.01
    )
    np.testing.assert_allclose(
        result.P_f_trans_raw, _analytic_pf(grid, mu_t, sigma_t), atol=0.01
    )

    assert isinstance(result.P_f_static_fit, LognormFragility)
    assert isinstance(result.P_f_trans_fit, LognormFragility)
    assert result.P_f_static_fit.mu == pytest.approx(mu_s, abs=0.02)
    assert result.P_f_static_fit.sigma == pytest.approx(sigma_s, abs=0.02)
    assert result.P_f_trans_fit.mu == pytest.approx(mu_t, abs=0.02)
    assert result.P_f_trans_fit.sigma == pytest.approx(sigma_t, abs=0.02)

    # Static and transient are fit SEPARATELY (spec §2): each branch's own point
    # set yields its own lognormal. Having recovered two different ground-truth
    # pairs, the two fitted curves must come out genuinely distinct -- a single
    # shared fit applied to both branches would fail here.
    assert result.P_f_static_fit.mu != result.P_f_trans_fit.mu
    assert result.P_f_static_fit.sigma != result.P_f_trans_fit.sigma


# ---------------------------------------------------------------------------
# (2) Bootstrap confidence bands: nesting and well-formedness
# ---------------------------------------------------------------------------


def test_bootstrap_bands_nest_central_curve() -> None:
    """Bootstrap ``(lo, hi)`` bands bracket the central fitted curve (spec §11).

    Resampling the realizations and refitting yields a per-level band whose
    central fitted curve sits at roughly the bootstrap median, so the band must
    bracket it at every conditioning level. The grid is chosen so both curves'
    ``P_f`` stay comfortably interior (~0.07 to ~0.94), keeping the percentile
    band away from the degenerate 0/1 boundaries. The band is also checked to be
    a proper, ordered ``[0, 1]`` interval and non-degenerate (positive width).

    Finally, a 95% band is compared against a 50% band built from the *same*
    resampling (same ``seed`` and ``n_bootstrap``): the only difference is the
    percentile cut, so the 95% band must be at least as wide everywhere and
    strictly wider somewhere -- basic evidence the resampling spread is real and
    that ``confidence`` actually controls the band.
    """
    grid = np.linspace(4.5, 10.0, 12)
    mu_s, sigma_s = float(np.log(7.0)), 0.30
    mu_t, sigma_t = float(np.log(5.0)), 0.45
    n = 5_000
    fm_stat = _lognormal_failure_matrix(mu_s, sigma_s, grid, n)
    fm_tran = _lognormal_failure_matrix(mu_t, sigma_t, grid, n)
    theta = np.zeros((n, len(PARAM_NAMES)))

    common = dict(n_bootstrap=400, seed=7)
    result = assemble_fragility(
        theta,
        list(PARAM_NAMES),
        grid,
        fm_stat,
        fm_tran,
        _metadata(),
        confidence=0.95,
        **common,
    )
    # Same resamples (same seed/n_bootstrap), a narrower confidence level.
    result_50 = assemble_fragility(
        theta,
        list(PARAM_NAMES),
        grid,
        fm_stat,
        fm_tran,
        _metadata(),
        confidence=0.50,
        **common,
    )

    assert set(result.bootstrap_bands) == {"static", "transient"}

    branches = [
        ("static", result.P_f_static_fit),
        ("transient", result.P_f_trans_fit),
    ]
    for key, fit in branches:
        lo, hi = (np.asarray(band) for band in result.bootstrap_bands[key])

        assert lo.shape == grid.shape
        assert hi.shape == grid.shape

        # Proper, ordered probability band.
        assert np.all(lo <= hi)
        assert np.all((lo >= 0.0) & (hi <= 1.0))
        assert np.any(hi - lo > 1e-6), "band collapsed to zero width"

        # Nesting: the central fitted curve lies inside the band everywhere.
        central = fit.probability_of_failure(grid)
        assert np.all(lo <= central + 1e-12)
        assert np.all(central <= hi + 1e-12)

        # The 95% band is wider than the 50% band built from the same resamples.
        lo50, hi50 = (np.asarray(band) for band in result_50.bootstrap_bands[key])
        width_95 = hi - lo
        width_50 = hi50 - lo50
        assert np.all(width_95 >= width_50 - 1e-12)
        assert np.any(width_95 > width_50 + 1e-9)


def test_bootstrap_survives_degenerate_replicates() -> None:
    """Degenerate bootstrap replicates are skipped, never fatal (fix 2).

    A tail-dominated branch (here: a transient curve held up by two interior
    levels with 1 and 2 failing rows out of 60) produces resamples whose point
    set collapses to fewer than two interior points or a non-increasing probit
    slope. Previously any such replicate raised out of ``_bootstrap_bands``
    *after* the sweep, destroying the run (observed end-to-end on the KP 62.0
    production config at reduced N, 2026-07-03 health assessment). Now the
    replicate is skipped: the run completes, a ``UserWarning`` reports the
    skipped fraction, the bands come from the surviving replicates only, and
    the skip counts are recorded in the result metadata.
    """
    grid = np.array([4.0, 6.0, 8.0, 10.0])
    n = 60
    # Healthy static branch: comfortably interior at every level.
    fm_stat = _lognormal_failure_matrix(float(np.log(7.0)), 0.30, grid, n)
    # Tail-dominated transient branch: p = [0, 0, 1/60, 2/60]. Any resample
    # that omits row 0 (probability ~(59/60)^60 ~ 0.37 per replicate) leaves a
    # single interior point -> a degenerate refit.
    fm_tran = np.zeros((n, grid.size), dtype=bool)
    fm_tran[0, 2] = True
    fm_tran[0, 3] = True
    fm_tran[1, 3] = True
    theta = np.zeros((n, len(PARAM_NAMES)))

    with pytest.warns(UserWarning, match="degenerate"):
        result = assemble_fragility(
            theta,
            list(PARAM_NAMES),
            grid,
            fm_stat,
            fm_tran,
            _metadata(),
            n_bootstrap=200,
            seed=3,
        )

    # Skip counts are recorded per curve; only the transient branch degenerates.
    info = result.metadata["bootstrap_degenerate_replicates"]
    assert info["n_bootstrap"] == 200
    assert info["static"] == 0
    assert 0 < info["transient"] < 200

    # The healthy branch's band is untouched: finite, ordered, in [0, 1].
    lo_s, hi_s = (np.asarray(b) for b in result.bootstrap_bands["static"])
    assert np.all(np.isfinite(lo_s)) and np.all(np.isfinite(hi_s))
    assert np.all(lo_s <= hi_s)

    # The degenerate branch still yields a band from the surviving replicates.
    lo_t, hi_t = (np.asarray(b) for b in result.bootstrap_bands["transient"])
    assert np.all(np.isfinite(lo_t)) and np.all(np.isfinite(hi_t))
    assert np.all(lo_t <= hi_t)
    assert np.all((lo_t >= 0.0) & (hi_t <= 1.0))


def test_bootstrap_all_degenerate_yields_nan_band_not_crash() -> None:
    """If every replicate degenerates the band is NaN and the run still completes.

    Extreme tail case, pinned at the ``_bootstrap_bands`` level: the transient
    branch has a *single* interior level (one failing row at the top level
    only), so every resample yields at most one interior point and every one of
    the ``n_bootstrap`` refits is degenerate. (The corresponding main fit would
    refuse this point set too, which is why this is tested on the band helper
    directly rather than through ``assemble_fragility``.) The contract: an
    all-NaN band plus a warning — never an exception after the sweep. The
    healthy static branch sharing the same resamples must keep its full band.
    """
    from bep_reliability_engine.fragility import _bootstrap_bands

    grid = np.array([4.0, 6.0, 8.0, 10.0])
    n = 40
    fm_stat = _lognormal_failure_matrix(float(np.log(7.0)), 0.30, grid, n)
    fm_single = np.zeros((n, grid.size), dtype=bool)
    fm_single[0, 3] = True  # one interior level at most, in every resample

    with pytest.warns(UserWarning, match="degenerate"):
        bands, degenerate = _bootstrap_bands(
            fm_stat, fm_single, grid, n_bootstrap=50, confidence=0.95, seed=5
        )

    assert degenerate["static"] == 0
    assert degenerate["transient"] == 50
    lo_t, hi_t = (np.asarray(b) for b in bands["transient"])
    assert np.all(np.isnan(lo_t)) and np.all(np.isnan(hi_t))
    lo_s, hi_s = (np.asarray(b) for b in bands["static"])
    assert np.all(np.isfinite(lo_s)) and np.all(np.isfinite(hi_s))


# ---------------------------------------------------------------------------
# (1b) Datum-anchored fit and deep-tail weighting (health-assessment fix 5)
# ---------------------------------------------------------------------------


def test_fit_with_datum_recovers_parameters_and_is_zero_below_datum() -> None:
    """The fit is anchored to the load excess (h - datum), not absolute stage.

    Fitting in ln(absolute MSL stage) makes (mu, sigma) depend on the vertical
    datum — physically meaningless parameters. With ``datum_m`` the curve is
    lognormal in the excess ``h - datum``: exact analytic points generated in
    excess space must be recovered exactly, the median-capacity property holds
    at ``datum + exp(mu)``, and the curve is identically zero at and below the
    datum (no load above the exit elevation means no failure probability).
    """
    datum = 38.3  # a real toe elevation (ADR-0021, KP 57.4)
    grid = datum + np.linspace(0.5, 6.0, 15)
    mu_true, sigma_true = float(np.log(2.5)), 0.40
    p_f = norm.cdf((np.log(grid - datum) - mu_true) / sigma_true)

    fit = fit_lognormal_fragility(grid, p_f, datum_m=datum)
    assert fit.datum_m == datum
    assert fit.mu == pytest.approx(mu_true, abs=1e-6)
    assert fit.sigma == pytest.approx(sigma_true, abs=1e-6)

    # Median property in excess space; the fitted curve reproduces the inputs.
    assert fit.probability_of_failure(datum + float(np.exp(mu_true))) == pytest.approx(
        0.5, abs=1e-9
    )
    np.testing.assert_allclose(fit.probability_of_failure(grid), p_f, atol=1e-9)

    # Identically zero at and below the datum, scalar and array alike.
    assert fit.probability_of_failure(datum) == 0.0
    assert fit.probability_of_failure(datum - 5.0) == 0.0
    mixed = np.array([datum - 1.0, datum, datum + 1.0])
    out = fit.probability_of_failure(mixed)
    assert out[0] == 0.0 and out[1] == 0.0 and out[2] > 0.0

    # datum_m = 0 (the default) reproduces the original ln(h) parametrization.
    legacy = fit_lognormal_fragility(grid - datum, p_f)
    assert legacy.datum_m == 0.0
    assert legacy.mu == pytest.approx(mu_true, abs=1e-6)
    assert legacy.sigma == pytest.approx(sigma_true, abs=1e-6)


def test_deep_tail_weighting_downweights_noisy_tail_points() -> None:
    """Inverse-variance probit weights damp the deep-tail estimator noise.

    An equal-weight probit OLS gives a P_f ~ 1e-4 point (one or two failing
    realizations) the same say as a well-resolved mid-curve point, although its
    probit-space noise is orders of magnitude larger. With the delta-method
    weights ``w = phi(z) / sqrt(p (1 - p))`` a corrupted deepest-tail point
    (a factor-5 fluctuation, i.e. a 1-vs-5-failure difference) must move the
    fitted parameters strictly less than the equal-weight fit computed here as
    the reference (the pre-fix behavior).
    """
    grid = np.linspace(4.0, 12.0, 9)
    mu_true, sigma_true = float(np.log(9.0)), 0.25
    p_exact = norm.cdf((np.log(grid) - mu_true) / sigma_true)
    p_noisy = p_exact.copy()
    p_noisy[0] *= 5.0  # deepest tail point: ~6e-4 -> ~3e-3

    fit_weighted = fit_lognormal_fragility(grid, p_noisy)

    # Equal-weight reference: the plain probit OLS the fitter used previously.
    probit = norm.ppf(p_noisy)
    slope, intercept = np.polyfit(np.log(grid), probit, 1)
    mu_ols, sigma_ols = -intercept / slope, 1.0 / slope

    assert abs(fit_weighted.mu - mu_true) < abs(mu_ols - mu_true)
    assert abs(fit_weighted.sigma - sigma_true) < abs(sigma_ols - sigma_true)


def test_save_load_round_trips_datum_and_legacy_files_default_to_zero(
    tmp_path,
) -> None:
    """``datum_m`` persists through save/load; legacy files load as datum 0.

    The fitted curves' datum is part of their meaning (P_f is evaluated in
    excess space), so it must survive the HDF5 round trip. Files written
    before the datum existed carry no datum attrs and must load with the
    backward-compatible ``datum_m = 0.0`` (the original ln(h) form).
    """
    datum = 2.0
    grid = np.linspace(4.5, 10.0, 9)
    n = 256
    fm_stat = _lognormal_failure_matrix(float(np.log(7.0)), 0.30, grid, n)
    fm_tran = _lognormal_failure_matrix(float(np.log(5.0)), 0.45, grid, n)
    theta = np.zeros((n, len(PARAM_NAMES)))

    result = assemble_fragility(
        theta,
        list(PARAM_NAMES),
        grid,
        fm_stat,
        fm_tran,
        _metadata(),
        n_bootstrap=25,
        seed=4,
        datum_m=datum,
    )
    assert result.P_f_static_fit.datum_m == datum
    assert result.P_f_trans_fit.datum_m == datum
    # The fit provenance is recorded alongside the curves.
    assert result.metadata["fragility_fit"]["datum_m"] == pytest.approx(datum)

    path = tmp_path / "datum.h5"
    result.save(path)
    loaded = FragilityResult.load(path)
    assert loaded.P_f_static_fit == result.P_f_static_fit
    assert loaded.P_f_trans_fit == result.P_f_trans_fit

    # Legacy file: strip the datum attrs and reload -> datum defaults to 0.0.
    with h5py.File(path, "a") as handle:
        del handle.attrs["fit_static_datum_m"]
        del handle.attrs["fit_trans_datum_m"]
    legacy = FragilityResult.load(path)
    assert legacy.P_f_static_fit.datum_m == 0.0
    assert legacy.P_f_trans_fit.datum_m == 0.0


# ---------------------------------------------------------------------------
# (2b) Spec §11 Monte Carlo convergence monitoring (health-assessment fix 3)
# ---------------------------------------------------------------------------


def test_mc_convergence_cov_recorded_in_metadata(tmp_path) -> None:
    """The §11 CoV of the P_f estimator is computed and persisted, not assumed.

    Spec §11 targets CoV(P_f-hat) < 5% across the relevant failure range and
    says the sufficiency "is verified directly for each cross-section once the
    engine runs" — so the assembler must compute the binomial-estimator CoV
    ``sqrt((1 - p) / (N * p))`` per conditioning level and record it in the
    result metadata: ``None`` outside the interior (p = 0 or 1), the worst
    interior CoV per branch, and whether the branch meets the target. The block
    must survive the HDF5 + JSON round trip (None/float mixing is the classic
    failure).
    """
    from bep_reliability_engine.fragility import PF_COV_TARGET, mc_cov_of_pf

    grid = np.array([4.0, 6.0, 8.0, 10.0])
    n = 400

    def matrix(fractions: list[float]) -> np.ndarray:
        out = np.zeros((n, len(fractions)), dtype=bool)
        for j, fraction in enumerate(fractions):
            out[: int(round(fraction * n)), j] = True
        return out

    fm_stat = matrix([0.0, 0.25, 0.50, 0.80])
    fm_tran = matrix([0.0, 0.05, 0.20, 0.50])
    theta = np.zeros((n, len(PARAM_NAMES)))

    result = assemble_fragility(
        theta,
        list(PARAM_NAMES),
        grid,
        fm_stat,
        fm_tran,
        _metadata(),
        n_bootstrap=50,
        seed=2,
    )

    convergence = result.metadata["mc_convergence"]
    assert convergence["n_realizations"] == n
    assert convergence["cov_target"] == pytest.approx(PF_COV_TARGET)

    def expected_cov(p: float) -> float:
        return float(np.sqrt((1.0 - p) / (n * p)))

    cov_static = convergence["cov_pf_static"]
    assert cov_static[0] is None  # p = 0: estimator CoV undefined
    assert cov_static[1] == pytest.approx(expected_cov(0.25))
    assert cov_static[2] == pytest.approx(expected_cov(0.50))
    assert cov_static[3] == pytest.approx(expected_cov(0.80))

    cov_trans = convergence["cov_pf_trans"]
    assert cov_trans[0] is None
    assert cov_trans[1] == pytest.approx(expected_cov(0.05))

    # Worst interior CoV and the target verdict, per branch. At N = 400 the
    # static worst is ~0.087 (p = 0.25) and the transient worst ~0.218
    # (p = 0.05): both above the 5% target, so both verdicts are False.
    assert convergence["max_cov_static"] == pytest.approx(expected_cov(0.25))
    assert convergence["max_cov_trans"] == pytest.approx(expected_cov(0.05))
    assert convergence["meets_cov_target_static"] is False
    assert convergence["meets_cov_target_trans"] is False

    # The standalone helper agrees and handles the boundary levels with None.
    assert mc_cov_of_pf(np.array([0.0, 0.25, 1.0]), n) == [
        None,
        pytest.approx(expected_cov(0.25)),
        None,
    ]

    # The block survives persistence (None/float lists through the JSON sidecar).
    path = tmp_path / "cov.h5"
    result.save(path)
    loaded = FragilityResult.load(path)
    assert loaded.metadata["mc_convergence"] == result.metadata["mc_convergence"]


# ---------------------------------------------------------------------------
# (3) HDF5 + JSON-sidecar round trip
# ---------------------------------------------------------------------------


def test_save_load_round_trip(tmp_path) -> None:
    """``save``/``load`` preserve both failure matrices and every metadata field.

    The Phase 2 handoff is non-negotiable (spec §2, §8): the round trip must
    return ``failure_matrix_stat`` and ``failure_matrix_tran`` bit-for-bit (and
    as bool), every metadata field exactly and with its Python type, and the
    retained ``theta_matrix``, ``conditioning_grid``, raw point estimates,
    ``param_names``, fitted curves and bootstrap bands. The metadata must land in
    a JSON sidecar (spec §8: "JSON sidecar for metadata"), checked by reading the
    sidecar back independently.
    """
    grid = np.linspace(4.5, 10.0, 9)
    mu_s, sigma_s = float(np.log(7.0)), 0.30
    mu_t, sigma_t = float(np.log(5.0)), 0.45
    n = 256
    fm_stat = _lognormal_failure_matrix(mu_s, sigma_s, grid, n)
    fm_tran = _lognormal_failure_matrix(mu_t, sigma_t, grid, n)
    theta = np.random.default_rng(0).random((n, len(PARAM_NAMES)))
    metadata = _metadata()

    result = assemble_fragility(
        theta,
        list(PARAM_NAMES),
        grid,
        fm_stat,
        fm_tran,
        metadata,
        n_bootstrap=50,
        seed=3,
    )

    # The dataclass is defined exactly per the spec §2 listing.
    assert is_dataclass(FragilityResult)
    assert tuple(f.name for f in fields(FragilityResult)) == EXPECTED_FRAGILITY_FIELDS

    path = tmp_path / "tokachi_kp58_historical.h5"
    result.save(path)
    assert path.exists()

    # Metadata is written to a JSON sidecar (not buried in HDF5 attrs alone).
    sidecars = list(tmp_path.glob("*.json"))
    assert sidecars, "expected a JSON metadata sidecar next to the HDF5 file"
    with open(sidecars[0], encoding="utf-8") as handle:
        sidecar = json.load(handle)
    assert sidecar["cross_section_id"] == "tokachi_kp58"

    loaded = FragilityResult.load(path)

    # Both failure matrices survive bit-for-bit and stay bool (the §2/§8
    # non-negotiable Phase 2 payload).
    assert loaded.failure_matrix_stat.dtype == np.bool_
    assert loaded.failure_matrix_tran.dtype == np.bool_
    np.testing.assert_array_equal(
        loaded.failure_matrix_stat, result.failure_matrix_stat
    )
    np.testing.assert_array_equal(
        loaded.failure_matrix_tran, result.failure_matrix_tran
    )

    # The other retained arrays survive exactly.
    np.testing.assert_array_equal(loaded.theta_matrix, result.theta_matrix)
    np.testing.assert_array_equal(loaded.conditioning_grid, result.conditioning_grid)
    np.testing.assert_array_equal(loaded.P_f_static_raw, result.P_f_static_raw)
    np.testing.assert_array_equal(loaded.P_f_trans_raw, result.P_f_trans_raw)
    assert loaded.param_names == result.param_names

    # Every metadata field survives, by value and by Python type. A bool that
    # comes back as int (or numpy bool) and a missing ``None`` are the classic
    # HDF5/JSON round-trip failures, so they are checked explicitly.
    assert loaded.metadata == result.metadata
    for field_name, value in result.metadata.items():
        assert field_name in loaded.metadata
        assert loaded.metadata[field_name] == value
        assert type(loaded.metadata[field_name]) is type(value)

    # The fields Phase 2 and the survival-discrimination decomposition stratify
    # on (spec §8) are asserted by name: a silent drop here would break the
    # decomposition, not merely lose a provenance label, so they are pinned
    # individually rather than left to the generic loop above.
    assert loaded.metadata["d70_interpretation"] == "matrix"
    assert loaded.metadata["remediation_state"] == "none"
    assert loaded.metadata["correlation_rho_k_d70"] == pytest.approx(-0.42)
    assert loaded.metadata["segment_id"] == "KP58.200"
    assert loaded.metadata["scenario"] == "historical"
    assert loaded.metadata["aquifer_lag_active"] is False
    assert loaded.metadata["tau_aq"] is None

    # Fitted curves and bootstrap bands survive too.
    assert loaded.P_f_static_fit.mu == pytest.approx(result.P_f_static_fit.mu)
    assert loaded.P_f_static_fit.sigma == pytest.approx(result.P_f_static_fit.sigma)
    assert loaded.P_f_trans_fit.mu == pytest.approx(result.P_f_trans_fit.mu)
    assert loaded.P_f_trans_fit.sigma == pytest.approx(result.P_f_trans_fit.sigma)
    assert set(loaded.bootstrap_bands) == set(result.bootstrap_bands)
    for key in result.bootstrap_bands:
        lo0, hi0 = result.bootstrap_bands[key]
        lo1, hi1 = loaded.bootstrap_bands[key]
        np.testing.assert_array_equal(np.asarray(lo1), np.asarray(lo0))
        np.testing.assert_array_equal(np.asarray(hi1), np.asarray(hi0))


# ---------------------------------------------------------------------------
# (4) Length-effect upscaling: weakest-link transform (review item #9)
# ---------------------------------------------------------------------------


def test_upscale_length_effect_weakest_link() -> None:
    """``P_f,seg = 1 - (1 - P_f,cs)^n_eff`` upscales a per-cross-section curve.

    Pins the thesis "Length Effect Upscaling" transform: it raises the segment
    failure probability above the per-cross-section one (weakest link), returns
    the input unchanged at ``n_eff = 1``, matches the ``n_eff * P_f``
    linearization in the small-``P_f`` limit, stays a proper ``[0, 1]``
    probability, and broadcasts over a fitted fragility curve sampled on a grid.
    """
    grid = np.linspace(4.0, 10.0, 13)
    p_cs = _analytic_pf(grid, float(np.log(7.0)), 0.35)
    n_eff = 4.0

    p_seg = upscale_length_effect(p_cs, n_eff)
    assert p_seg.shape == p_cs.shape
    # Weakest link: the segment is at least as likely to fail as one section,
    # strictly more wherever 0 < P_f < 1.
    assert np.all(p_seg >= p_cs - 1e-15)
    interior = (p_cs > 1e-6) & (p_cs < 1 - 1e-6)
    assert np.all(p_seg[interior] > p_cs[interior])
    assert np.all((p_seg >= 0.0) & (p_seg <= 1.0))
    np.testing.assert_array_equal(p_seg, 1.0 - (1.0 - p_cs) ** n_eff)

    # n_eff = 1 is the identity (segment == one cross-section).
    np.testing.assert_allclose(upscale_length_effect(p_cs, 1.0), p_cs, atol=0.0)

    # Small-P_f limit reduces to the linear approximation n_eff * P_f.
    small = 1.0e-4
    assert upscale_length_effect(small, n_eff) == pytest.approx(n_eff * small, rel=1e-3)

    # Scalar input returns a float.
    assert isinstance(upscale_length_effect(0.1, 3.0), float)


def test_upscale_length_effect_validates_inputs() -> None:
    """Guards: ``n_eff >= 1`` and ``P_f in [0, 1]`` (review item #9)."""
    with pytest.raises(ValueError, match="n_eff"):
        upscale_length_effect(0.1, 0.5)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        upscale_length_effect(1.5, 2.0)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        upscale_length_effect(-0.1, 2.0)
