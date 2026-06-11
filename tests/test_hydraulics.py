"""Tests for M4 hydraulic translation (``bep_reliability_engine.hydraulics``).

Executable contract for the approved M4 interface (ADR-0004 through
ADR-0007), written before the implementation: every test is expected to fail
with ``NotImplementedError`` until ``hydraulics.py`` is filled in.

Parameter values are physically representative of the Tokachi A_c / A_g
stratigraphy: k_aq of order 1e-3 m/s (Form 5 A_g range 1e-3 to 3e-3 m/s),
k_bl of order 1e-6 m/s (Form 5 A_c range 1e-6 to 3e-6 m/s), and the actual
cross-section foreshore widths 44 / 200 / 325 / 600 m. Foreshore blanket
properties use the hinterland A_c values as proxy (ADR-0005).
"""

import warnings

import numpy as np
import pytest

from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    LaggedHead,
    aquifer_response_time,
    leakage_length_in,
    leakage_length_out,
    leakage_ratio_diagnostic,
    make_head_model,
    response_factor,
    translate_instantaneous,
)

# Tokachi-representative base case, engineered to round numbers:
# lambda_in = sqrt(1e-3 * 20 * 2 / 1e-6) = 200 m exactly.
K_AQ_MPS = 1.0e-3  # A_g aquifer conductivity (Form 5 range 1e-3 - 3e-3 m/s)
K_BL_MPS = 1.0e-6  # A_c blanket conductivity (Form 5 range 1e-6 - 3e-6 m/s)
D_AQ_M = 20.0
D_BL_M = 2.0
SEEPAGE_LENGTH_M = 50.0
Z_TOE_M = 0.0
LAMBDA_IN_M = 200.0  # hand value for the base case above

# Hinterland A_c values as the foreshore-blanket proxy (ADR-0005).
D_FORE_M = D_BL_M
K_FORE_MPS = K_BL_MPS

# Actual foreshore widths across the reach; 44 m is KP62.0-like (narrowest),
# 600 m is KP60.0-like (widest).
FORESHORE_WIDTHS_M = (44.0, 200.0, 325.0, 600.0)

DT_S = 600.0

# Spec §2 theta column order; M4 consumes k_aq, D_aq, D_bl, k_bl.
PARAM_NAMES = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_s_sub", "C_e"]


def _flashy_hydrograph(
    dt_s: float = DT_S,
    duration_s: float = 24.0 * 3600.0,
    h_base_m: float = 0.5,
    h_peak_m: float = 6.0,
    t_peak_s: float = 12.0 * 3600.0,
    sigma_s: float = 1.5 * 3600.0,
) -> np.ndarray:
    """Synthetic single-peak Gaussian hydrograph with a flashy rising limb."""
    t_s = np.arange(0.0, duration_s + dt_s, dt_s)
    return h_base_m + (h_peak_m - h_base_m) * np.exp(
        -(((t_s - t_peak_s) / sigma_s) ** 2)
    )


def _march(model, h_series_m, dt_s, r_e, z_toe_m) -> np.ndarray:
    """Drive a head model through a hydrograph.

    Row 0 is the equilibrium initial condition (ADR-0004); rows 1..T-1 are
    the ``step()`` returns. Output shape is (T,) for scalar r_e and (T, N)
    for vector r_e.
    """
    model.reset(float(h_series_m[0]))
    rows = [np.asarray(translate_instantaneous(h_series_m[0], r_e, z_toe_m))]
    for h_t in h_series_m[1:]:
        rows.append(np.asarray(model.step(float(h_t), dt_s)))
    return np.stack(rows)


def _base_response_factor(foreshore_width_m: float) -> float:
    """r_e for the round-number base case at a given foreshore width."""
    lam_in = leakage_length_in(K_AQ_MPS, D_AQ_M, D_BL_M, K_BL_MPS)
    lam_out_eff = leakage_length_out(
        K_AQ_MPS, D_AQ_M, D_FORE_M, K_FORE_MPS, foreshore_width_m
    )
    return float(response_factor(lam_in, lam_out_eff, SEEPAGE_LENGTH_M))


def _theta_matrix(n: int, seed: int) -> np.ndarray:
    """Synthetic (N, 7) prior draws in spec §2 column order (seeded RNG)."""
    rng = np.random.default_rng(seed)
    return np.column_stack(
        [
            rng.lognormal(np.log(2.0e-3), 0.4, n),  # k_aq [m/s], A_g
            rng.lognormal(np.log(2.0e-4), 0.1, n),  # d_70 [m] (unused in M4)
            rng.lognormal(np.log(20.0), 0.2, n),  # D_aq [m]
            rng.lognormal(np.log(3.0), 0.2, n),  # D_bl [m]
            rng.lognormal(np.log(2.0e-6), 0.4, n),  # k_bl [m/s], A_c
            rng.normal(10.0, 0.5, n),  # gamma_s_sub [kN/m3] (unused)
            rng.lognormal(np.log(0.014), 0.5, n),  # C_e [-] (unused in M4)
        ]
    )


# ---------------------------------------------------------------------------
# (1) Mazure analytical check (spec §11, physics validation test 3)
# ---------------------------------------------------------------------------


def test_mazure_no_foreshore_hand_values_machine_precision() -> None:
    """No-foreshore geometry with hand-computed round numbers.

    lambda_in = sqrt(1e-3 * 20 * 2 / 1e-6) = 200 m
    r_e       = 200 / (0 + 50 + 200)       = 0.8
    """
    lam_in = leakage_length_in(K_AQ_MPS, D_AQ_M, D_BL_M, K_BL_MPS)
    assert float(lam_in) == pytest.approx(LAMBDA_IN_M, rel=1e-12)

    lam_out_eff = leakage_length_out(K_AQ_MPS, D_AQ_M, D_FORE_M, K_FORE_MPS, 0.0)
    assert float(lam_out_eff) == 0.0

    r_e = response_factor(lam_in, lam_out_eff, SEEPAGE_LENGTH_M)
    assert float(r_e) == pytest.approx(0.8, rel=1e-12)


def test_translate_instantaneous_hand_value() -> None:
    """h_aq = 1.5 + 0.8 * (4.0 - 1.5) = 3.5 m (Pol SIE 2024 Eq. 10), by hand."""
    h_aq = translate_instantaneous(4.0, 0.8, 1.5)
    assert float(h_aq) == pytest.approx(3.5, rel=1e-12)


# ---------------------------------------------------------------------------
# (2) Three foreshore regimes: narrow (KP62.0-like), moderate, wide
#     (KP60.0-like), using the actual reach widths 44 / 200 / 325 / 600 m
# ---------------------------------------------------------------------------


def test_foreshore_three_regimes() -> None:
    lam_semi = float(leakage_length_out(K_AQ_MPS, D_AQ_M, D_FORE_M, K_FORE_MPS, np.inf))
    # Identical formula and proxy properties: semi-infinite lambda_out equals
    # the base-case lambda_in.
    assert lam_semi == pytest.approx(LAMBDA_IN_M, rel=1e-12)

    lam_eff = {
        b_f: float(leakage_length_out(K_AQ_MPS, D_AQ_M, D_FORE_M, K_FORE_MPS, b_f))
        for b_f in FORESHORE_WIDTHS_M
    }
    widths = (0.0, *FORESHORE_WIDTHS_M, np.inf)
    r_e = {b_f: _base_response_factor(b_f) for b_f in widths}

    # Narrow regime (KP62.0-like, 44 m): lambda_out_eff ~ B_f, i.e. the
    # "lambda_out ~ 0" treatment emerges from the tanh limit rather than
    # being asserted (TR ZMW 1999: L'_v ~ L_v for narrow foreshores).
    assert lam_eff[44.0] < 44.0
    assert lam_eff[44.0] == pytest.approx(44.0, rel=0.02)

    # Wide regime (KP60.0-like, 600 m): within 0.5% of the semi-infinite
    # limit (TR ZMW 1999: L'_v ~ lambda_1 for wide foreshores).
    assert lam_eff[600.0] == pytest.approx(lam_semi, rel=0.005)
    assert r_e[600.0] == pytest.approx(r_e[np.inf], rel=0.005)

    # r_e is strictly monotonically suppressed as the foreshore widens.
    r_values = [r_e[b_f] for b_f in widths]
    assert all(a > b for a, b in zip(r_values, r_values[1:]))

    # The widest foreshore suppresses r_e well below the no-foreshore value.
    assert r_e[600.0] < 0.6 * r_e[0.0]


# ---------------------------------------------------------------------------
# (3) Limit behavior of r_e
# ---------------------------------------------------------------------------


def test_response_factor_limit_kbl_to_zero() -> None:
    """r_e -> 1 as the hinterland blanket seals (k_bl -> 0).

    lambda_in grows without bound while lambda_out_eff stays capped by the
    finite foreshore width, so the ratio is dominated by lambda_in.
    """
    k_bl_seq = np.array([1.0e-6, 1.0e-8, 1.0e-10, 1.0e-12])
    lam_in = leakage_length_in(K_AQ_MPS, D_AQ_M, D_BL_M, k_bl_seq)
    lam_out_eff = leakage_length_out(K_AQ_MPS, D_AQ_M, D_FORE_M, K_FORE_MPS, 44.0)
    r_e = np.asarray(response_factor(lam_in, lam_out_eff, SEEPAGE_LENGTH_M))

    assert np.all(np.diff(r_e) > 0.0)
    assert np.all(r_e < 1.0)
    assert r_e[-1] > 0.999


def test_response_factor_open_interval_for_realistic_draws() -> None:
    """r_e lies strictly in (0, 1) across a realistic seeded prior sweep."""
    rng = np.random.default_rng(20260611)
    n = 1000
    k_aq_mps = rng.lognormal(np.log(2.0e-3), 0.4, n)  # around Form 5 A_g
    d_aq_m = rng.lognormal(np.log(20.0), 0.2, n)
    d_bl_m = rng.lognormal(np.log(3.0), 0.2, n)
    k_bl_mps = rng.lognormal(np.log(2.0e-6), 0.4, n)  # around Form 5 A_c

    lam_in = leakage_length_in(k_aq_mps, d_aq_m, d_bl_m, k_bl_mps)
    lam_out_eff = leakage_length_out(k_aq_mps, d_aq_m, D_FORE_M, K_FORE_MPS, 325.0)
    r_e = np.asarray(response_factor(lam_in, lam_out_eff, SEEPAGE_LENGTH_M))

    assert r_e.shape == (n,)
    assert np.all(np.isfinite(r_e))
    assert np.all(r_e > 0.0)
    assert np.all(r_e < 1.0)


# ---------------------------------------------------------------------------
# (4) Lag collapse: tau_aq -> 0 reproduces the instantaneous translation
# ---------------------------------------------------------------------------


def test_lag_collapse_to_instantaneous() -> None:
    """ADR-0004: as tau_aq -> 0 the lag reproduces the instantaneous form.

    With the exact exponential update the collapse is exact (the update
    factor saturates at 1); under the rejected explicit-Euler form this
    limit would diverge instead of converging.
    """
    h_m = _flashy_hydrograph()
    r_e = 0.8
    model = make_head_model(r_e, Z_TOE_M, lag_active=True, tau_aq_s=1.0e-9)
    h_lag = _march(model, h_m, DT_S, r_e, Z_TOE_M)
    h_inst = np.asarray(translate_instantaneous(h_m, r_e, Z_TOE_M))
    np.testing.assert_allclose(h_lag, h_inst, rtol=1e-12, atol=1e-12)


# ---------------------------------------------------------------------------
# (5) Lag smoothing on a synthetic flashy hydrograph
# ---------------------------------------------------------------------------


def test_lag_smoothing_peak_lower_and_later() -> None:
    """Finite tau_aq attenuates and delays the aquifer peak."""
    h_m = _flashy_hydrograph()
    r_e = 0.8
    tau_aq_s = 4.0 * 3600.0  # slow aquifer vs the ~1.5 h flashy peak
    lagged = LaggedHead(r_e, Z_TOE_M, tau_aq_s)
    h_lag = _march(lagged, h_m, DT_S, r_e, Z_TOE_M)
    h_inst = np.asarray(translate_instantaneous(h_m, r_e, Z_TOE_M))

    base_m = h_inst[0]
    assert h_lag.max() < h_inst.max()
    # Strong attenuation expected for tau_aq >> peak duration; the 0.9
    # factor is a generous margin around the ~0.6 analytic estimate.
    assert h_lag.max() - base_m < 0.9 * (h_inst.max() - base_m)
    assert int(np.argmax(h_lag)) > int(np.argmax(h_inst))


def test_lag_constant_hydrograph_exact_equality() -> None:
    """ADR-0004 equilibrium-initialization guard, exact at every timestep.

    With h(t) = h0 and equilibrium initialization the lagged head equals
    the instantaneous head identically (the update increment is exactly
    zero), so the assertion is exact equality, not a tolerance.
    """
    h_m = np.full(48, 3.0)
    r_e = 0.8
    lagged = LaggedHead(r_e, Z_TOE_M, 2.0 * DT_S)
    h_lag = _march(lagged, h_m, DT_S, r_e, Z_TOE_M)
    h_inst = np.asarray(translate_instantaneous(h_m, r_e, Z_TOE_M))
    np.testing.assert_array_equal(h_lag, h_inst)


def test_lag_stability_tau_below_timestep() -> None:
    """ADR-0004 stability: tau_aq = 0.1 * dt stays bounded and tracks.

    Explicit Euler diverges for dt > 2 * tau_aq; the exponential update
    must remain within the instantaneous hull and track it closely.
    """
    h_m = _flashy_hydrograph()
    r_e = 0.8
    lagged = LaggedHead(r_e, Z_TOE_M, 0.1 * DT_S)
    h_lag = _march(lagged, h_m, DT_S, r_e, Z_TOE_M)
    h_inst = np.asarray(translate_instantaneous(h_m, r_e, Z_TOE_M))

    assert np.all(np.isfinite(h_lag))
    tiny = 1e-9
    assert np.all(h_lag <= h_inst.max() + tiny)
    assert np.all(h_lag >= h_inst.min() - tiny)
    assert np.max(np.abs(h_lag - h_inst)) < 1e-3


# ---------------------------------------------------------------------------
# (6) Scalar / vectorized equivalence
# ---------------------------------------------------------------------------


def test_vectorized_kernels_match_scalar_rowwise() -> None:
    """The (N, 7) matrix path agrees with row-by-row scalar calls."""
    n = 64
    theta = _theta_matrix(n, seed=42)
    i_k_aq = PARAM_NAMES.index("k_aq")
    i_d_aq = PARAM_NAMES.index("D_aq")
    i_d_bl = PARAM_NAMES.index("D_bl")
    i_k_bl = PARAM_NAMES.index("k_bl")
    s_s_per_m = 5.0e-5
    b_f_m = 325.0

    lam_in_vec = np.asarray(
        leakage_length_in(
            theta[:, i_k_aq], theta[:, i_d_aq], theta[:, i_d_bl], theta[:, i_k_bl]
        )
    )
    lam_out_vec = np.asarray(
        leakage_length_out(
            theta[:, i_k_aq], theta[:, i_d_aq], D_FORE_M, K_FORE_MPS, b_f_m
        )
    )
    r_e_vec = np.asarray(response_factor(lam_in_vec, lam_out_vec, SEEPAGE_LENGTH_M))
    tau_vec = np.asarray(
        aquifer_response_time(
            theta[:, i_d_aq], theta[:, i_d_bl], theta[:, i_k_bl], s_s_per_m
        )
    )
    h_aq_vec = np.asarray(translate_instantaneous(4.2, r_e_vec, Z_TOE_M))

    assert lam_in_vec.shape == (n,)
    for j in range(n):
        row = theta[j]
        lam_in_j = leakage_length_in(
            float(row[i_k_aq]),
            float(row[i_d_aq]),
            float(row[i_d_bl]),
            float(row[i_k_bl]),
        )
        lam_out_j = leakage_length_out(
            float(row[i_k_aq]), float(row[i_d_aq]), D_FORE_M, K_FORE_MPS, b_f_m
        )
        r_e_j = response_factor(lam_in_j, lam_out_j, SEEPAGE_LENGTH_M)
        tau_j = aquifer_response_time(
            float(row[i_d_aq]), float(row[i_d_bl]), float(row[i_k_bl]), s_s_per_m
        )
        h_aq_j = translate_instantaneous(4.2, r_e_j, Z_TOE_M)

        np.testing.assert_allclose(float(lam_in_j), lam_in_vec[j], rtol=1e-14)
        np.testing.assert_allclose(float(lam_out_j), lam_out_vec[j], rtol=1e-14)
        np.testing.assert_allclose(float(r_e_j), r_e_vec[j], rtol=1e-14)
        np.testing.assert_allclose(float(tau_j), tau_vec[j], rtol=1e-14)
        np.testing.assert_allclose(float(h_aq_j), h_aq_vec[j], rtol=1e-14)


def test_vectorized_lag_trajectory_matches_scalar_rowwise() -> None:
    """A vector LaggedHead trajectory equals per-row scalar trajectories."""
    n = 64
    theta = _theta_matrix(n, seed=42)
    i_k_aq = PARAM_NAMES.index("k_aq")
    i_d_aq = PARAM_NAMES.index("D_aq")
    i_d_bl = PARAM_NAMES.index("D_bl")
    i_k_bl = PARAM_NAMES.index("k_bl")
    s_s_per_m = 5.0e-5

    lam_in = leakage_length_in(
        theta[:, i_k_aq], theta[:, i_d_aq], theta[:, i_d_bl], theta[:, i_k_bl]
    )
    lam_out = leakage_length_out(
        theta[:, i_k_aq], theta[:, i_d_aq], D_FORE_M, K_FORE_MPS, 325.0
    )
    r_e_vec = np.asarray(response_factor(lam_in, lam_out, SEEPAGE_LENGTH_M))
    tau_vec = np.asarray(
        aquifer_response_time(
            theta[:, i_d_aq], theta[:, i_d_bl], theta[:, i_k_bl], s_s_per_m
        )
    )

    h_m = _flashy_hydrograph()[:8]  # a short series suffices here
    vec_model = LaggedHead(r_e_vec, Z_TOE_M, tau_vec)
    h_vec = _march(vec_model, h_m, DT_S, r_e_vec, Z_TOE_M)  # (T, N)
    assert h_vec.shape == (len(h_m), n)

    for j in (0, 17, 63):
        scalar_model = LaggedHead(float(r_e_vec[j]), Z_TOE_M, float(tau_vec[j]))
        h_j = _march(scalar_model, h_m, DT_S, float(r_e_vec[j]), Z_TOE_M)
        np.testing.assert_allclose(h_j, h_vec[:, j], rtol=1e-14, atol=0.0)


# ---------------------------------------------------------------------------
# (7) L / lambda_in validity diagnostic (ADR-0006)
# ---------------------------------------------------------------------------


def test_validity_diagnostic_flags_and_warns() -> None:
    """Flags rows with L / lambda_in above threshold; warns on the fraction."""
    lam_in_m = np.array([400.0, 200.0, 60.0, 25.0])
    # L / lambda_in = [0.125, 0.25, 0.833, 2.0] against threshold 0.5;
    # flagged fraction 0.5 exceeds warn_fraction 0.25.
    with pytest.warns(UserWarning):
        mask = leakage_ratio_diagnostic(
            SEEPAGE_LENGTH_M, lam_in_m, ratio_threshold=0.5, warn_fraction=0.25
        )
    np.testing.assert_array_equal(mask, [False, False, True, True])


def test_validity_diagnostic_silent_when_valid() -> None:
    """No flags and no warning when L << lambda_in for all realizations."""
    lam_in_m = np.array([400.0, 500.0, 1000.0])  # ratios 0.125, 0.10, 0.05
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mask = leakage_ratio_diagnostic(
            SEEPAGE_LENGTH_M, lam_in_m, ratio_threshold=0.5, warn_fraction=0.01
        )
    assert not np.asarray(mask).any()


# ---------------------------------------------------------------------------
# Interface contract: factory dispatch and form interchangeability
# ---------------------------------------------------------------------------


def test_factory_dispatch_matches_direct_classes() -> None:
    """make_head_model output is behaviorally identical to the classes."""
    h_m = _flashy_hydrograph()[:12]
    r_e = 0.7

    inst_factory = make_head_model(r_e, Z_TOE_M, lag_active=False)
    inst_direct = InstantaneousHead(r_e, Z_TOE_M)
    np.testing.assert_array_equal(
        _march(inst_factory, h_m, DT_S, r_e, Z_TOE_M),
        _march(inst_direct, h_m, DT_S, r_e, Z_TOE_M),
    )

    tau_aq_s = 3600.0
    lag_factory = make_head_model(r_e, Z_TOE_M, lag_active=True, tau_aq_s=tau_aq_s)
    lag_direct = LaggedHead(r_e, Z_TOE_M, tau_aq_s)
    np.testing.assert_array_equal(
        _march(lag_factory, h_m, DT_S, r_e, Z_TOE_M),
        _march(lag_direct, h_m, DT_S, r_e, Z_TOE_M),
    )


def test_factory_requires_tau_when_lag_active() -> None:
    with pytest.raises(ValueError):
        make_head_model(0.7, Z_TOE_M, lag_active=True, tau_aq_s=None)


def test_instantaneous_step_ignores_dt() -> None:
    """The instantaneous form is timestep-independent by construction."""
    model = InstantaneousHead(0.8, Z_TOE_M)
    model.reset(0.5)
    head_small_dt = np.asarray(model.step(4.0, 1.0))
    model.reset(0.5)
    head_large_dt = np.asarray(model.step(4.0, 1.0e6))
    np.testing.assert_array_equal(head_small_dt, head_large_dt)
