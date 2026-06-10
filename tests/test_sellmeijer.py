"""Tests for M6 ``sellmeijer``: critical head H_c and critical pipe length l_c.

Expected values trace to:

- Sellmeijer et al. (2011), EJECE 15(8): adapted piping rule (formula [6]),
  experimental mean values (Table 2), regression scatter (~13%, sections 6
  and 8) and the IJkdijk large-scale validation (section 7, Figs. 5-7).
- Pol et al. (2024), Structure and Infrastructure Engineering: Eq. (12)
  (restated Sellmeijer rule) and Eq. (13) (l_c formula).
- The user-provided IJkdijk / Pol scale-analysis reference sheet for the
  tabulated parameter sets: the 2011 EJECE paper reports the IJkdijk
  parameters only in prose and figures (its Table 2 is parameter limits,
  not test data). Values marked FLAG below should be confirmed against the
  paper copies.
"""

import numpy as np
import pytest

from bep_reliability_engine.sellmeijer import (
    _factor_Fg,
    _factor_Fr,
    _factor_Fs,
    compute_critical_head,
    compute_critical_head_vectorized,
    compute_critical_pipe_length,
)

# Canonical theta-vector column order (spec section 2, M2 contract).
PARAM_NAMES = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_s_sub", "C_e"]

# Submerged particle unit weight of the IJkdijk sand [kN/m^3]:
# rho_s = 2.50 Mg/m^3, rho_w = 1.00 Mg/m^3 (user-provided IJkdijk reference
# sheet, section 4): (2500 - 1000) * 9.81 / 1000 = 14.715.
GAMMA_SUB_IJKDIJK_KN_M3 = 14.715

# Submerged particle unit weight of Pol's base-case sand S2-2 [kN/m^3]:
# rho_s = 2650 kg/m^3 (reference sheet, section 5):
# (2650 - 1000) * 9.81 / 1000 = 16.1865.
GAMMA_SUB_POL_BASE_KN_M3 = 16.1865


def _theta_row(k_aq, d_70, D_aq, gamma_s_sub, D_bl=4.0, k_bl=1.0e-7, C_e=0.014):
    """Assemble one theta row in the canonical column order.

    D_bl, k_bl and C_e do not enter H_c (the static branch has no C_e
    exposure by design, ADR-0001); plausible filler values are used.
    """
    return np.array([k_aq, d_70, D_aq, D_bl, k_bl, gamma_s_sub, C_e])


def _random_theta_matrix(rng, n):
    """Uniform draws within physically defensible bounds (see
    test_hc_positive_for_large_sample for the bound rationale)."""
    return np.column_stack(
        [
            rng.uniform(1.0e-5, 1.0e-3, n),  # k_aq [m/s]
            rng.uniform(150e-6, 430e-6, n),  # d_70 [m], Table 2 range
            rng.uniform(2.0, 40.0, n),  # D_aq [m]
            rng.uniform(0.5, 10.0, n),  # D_bl [m] (unused by H_c)
            rng.uniform(1.0e-9, 1.0e-6, n),  # k_bl [m/s] (unused by H_c)
            rng.uniform(13.0, 18.0, n),  # gamma_s_sub [kN/m^3]
            rng.uniform(0.005, 0.05, n),  # C_e [-] (unused by H_c)
        ]
    )


def test_factor_fr_known_values():
    # Sellmeijer (2011) formula [6] resistance factor, hand computation
    # with the regression ratio terms (D_r/D_r,m), (C_u/C_u,m), (KAS/KAS_m)
    # all equal to 1 at the Table 2 experimental means:
    #   F_r = eta * (gamma'_p / gamma_w) * tan(theta)
    #       = 0.25 * (14.715 / 9.81) * tan(37 deg)
    #       = 0.25 * 1.500 * 0.753554 = 0.282583
    assert _factor_Fr(GAMMA_SUB_IJKDIJK_KN_M3) == pytest.approx(0.28258, rel=1e-3)

    # Relative-density regression exponent (Sellmeijer 2011, Table 1,
    # beta_RD = 0.35): F_r(D_r=1.0) / F_r(D_r=0.725) = (1.0/0.725)^0.35.
    ratio = _factor_Fr(GAMMA_SUB_IJKDIJK_KN_M3, relative_density=1.0) / _factor_Fr(
        GAMMA_SUB_IJKDIJK_KN_M3
    )
    assert ratio == pytest.approx((1.0 / 0.725) ** 0.35, rel=1e-9)


def test_factor_fs_known_values():
    # Sellmeijer (2011) formula [6] scale factor for the IJkdijk test 1
    # inputs (L = 15 m, d_70 = 180 um, k_aq = 8.0e-5 m/s; section 7 and
    # reference sheet section 4). Hand computation:
    #   kappa = k * nu / g = 8.0e-5 * 1.3e-6 / 9.81 = 1.06014e-11 m^2
    #   (kappa * L)^(1/3) = (1.59021e-10)^(1/3) = 5.4177e-4 m
    #   d_70 / (kappa*L)^(1/3) = 1.8e-4 / 5.4177e-4 = 0.33224
    #   (d_70,m / d_70)^0.6 = (208/180)^0.6 = 1.09062
    #   F_s = 0.33224 * 1.09062 = 0.36235
    assert _factor_Fs(180e-6, 8.0e-5, 15.0) == pytest.approx(0.36235, rel=1e-3)


def test_factor_fg_known_values():
    # Sellmeijer (2011) formula [6] geometrical shape factor,
    # F_g = 0.91 * (D/L)^(0.28 / ((D/L)^2.8 - 1) + 0.04), hand-computed.

    # IJkdijk geometry, D/L = 3/15 = 0.20:
    # exponent = 0.28/(0.2^2.8 - 1) + 0.04 = -0.243117
    # F_g = 0.91 * 0.2^(-0.243117) = 1.34578
    assert _factor_Fg(3.0, 15.0) == pytest.approx(1.3458, rel=1e-3)

    # Small D_aq/L (thin aquifer at field scale), D/L = 2.5/50 = 0.05:
    # exponent = 0.28/(0.05^2.8 - 1) + 0.04 = -0.240064
    # F_g = 0.91 * 0.05^(-0.240064) = 1.86790
    assert _factor_Fg(2.5, 50.0) == pytest.approx(1.8679, rel=1e-3)

    # Larger D_aq/L = 25/50 = 0.5:
    # exponent = 0.28/(0.5^2.8 - 1) + 0.04 = -0.286945
    # F_g = 0.91 * 0.5^(-0.286945) = 1.11025
    assert _factor_Fg(25.0, 50.0) == pytest.approx(1.1103, rel=1e-3)


def test_hc_ijkdijk_case_1():
    # IJkdijk test 1 (IJkfs01): fine sand d_70 = 180 um, L = 15 m,
    # D = 3.00 m, k_aq = 8.0e-5 m/s; observed critical head H_c = 2.30 m.
    # Source: Sellmeijer (2011) section 7 / Fig. 5 (5% silt head
    # correction); tabulated values from the user-provided reference
    # sheet, section 4. FLAG: confirm H_c = 2.30 m and k_aq = 8.0e-5 m/s
    # against the paper copy -- the EJECE PDF tabulates neither.
    # Tolerance 15%: the paper reports ~13% scatter (13.2% regression
    # noise, section 6; 13.4% model drift, section 6) and states the fine
    # sand predictions "agree quite well" (section 8). Formula [6]
    # evaluates to 2.07 m for these inputs (-10% vs observed).
    theta = _theta_row(8.0e-5, 180e-6, 3.00, GAMMA_SUB_IJKDIJK_KN_M3)
    h_c = compute_critical_head(theta, {"L": 15.0})
    assert h_c == pytest.approx(2.30, rel=0.15)


def test_hc_ijkdijk_case_2():
    # IJkdijk test 2 (IJkfs02): coarse sand d_70 = 260 um, L = 15 m,
    # D = 2.85 m, k_aq = 1.4e-4 m/s; observed critical head H_c = 1.75 m.
    # Source: Sellmeijer (2011) section 7 / Fig. 6 (10% silt head
    # correction); tabulated values from the user-provided reference
    # sheet, section 4. FLAG: confirm H_c = 1.75 m and k_aq = 1.4e-4 m/s
    # against the paper copy.
    # Tolerance 25%: the paper itself reports that the formula [6]
    # prediction for this coarse-sand test "deviates from the experiment
    # by 25%" (sections 8 and 9). Formula [6] evaluates to 2.01 m for
    # these inputs (+15% vs observed).
    theta = _theta_row(1.4e-4, 260e-6, 2.85, GAMMA_SUB_IJKDIJK_KN_M3)
    h_c = compute_critical_head(theta, {"L": 15.0})
    assert h_c == pytest.approx(1.75, rel=0.25)


def test_hc_ijkdijk_case_3():
    # IJkdijk test 3 (IJkfs03): fine sand d_70 = 180 um, L = 15 m,
    # D = 3.00 m, k_aq = 8.0e-5 m/s (same sand and geometry as test 1,
    # silt sedimentation removed, 0% correction); observed critical head
    # H_c = 2.10 m. Source: Sellmeijer (2011) section 7 / Fig. 7;
    # tabulated values from the user-provided reference sheet, section 4.
    # FLAG: confirm H_c = 2.10 m against the paper copy.
    # Tolerance 15% as in case 1; formula [6] evaluates to 2.07 m for
    # these inputs (-1.6% vs observed).
    theta = _theta_row(8.0e-5, 180e-6, 3.00, GAMMA_SUB_IJKDIJK_KN_M3)
    h_c = compute_critical_head(theta, {"L": 15.0})
    assert h_c == pytest.approx(2.10, rel=0.15)


def test_hc_pol_base_case():
    # Pol et al. scale-analysis base case (sand S2-2): L = 30 m,
    # D_aq = 10 m (= L/3), k_aq = 1.62e-4 m/s (from intrinsic permeability
    # K = 2.2e-11 m^2 with mu = 1.33e-3 Pa.s, rho_w = 1000 kg/m^3),
    # d_70 = 0.200 mm, gamma'_p = 16.19 kN/m^3 (rho_s = 2650 kg/m^3).
    # The Sellmeijer (2011) reference for this case is H_c/L <~ 0.10,
    # i.e. H_c ~ 2.7-3.0 m. Source: user-provided reference sheet,
    # section 5 (cf. pol_compgeo_2024). FLAG: range value, not an exact
    # paper number -- confirm against the paper copy.
    # Direct evaluation of formula [6] with these inputs and the module's
    # nu = 1.3e-6 m^2/s gives H_c = 2.66 m (the sheet's K = 2.2e-11 m^2
    # implies nu = 1.33e-6, a 0.8% difference in F_s), so the assertion
    # brackets [2.4, 3.0] together with the paper's gradient bound.
    theta = _theta_row(1.62e-4, 200e-6, 10.0, GAMMA_SUB_POL_BASE_KN_M3)
    h_c = compute_critical_head(theta, {"L": 30.0})
    assert 2.4 <= h_c <= 3.0
    assert h_c / 30.0 <= 0.10


def test_lc_formula():
    # Pol et al. (2024, SIE) Eq. (13): l_c = 0.5 * L * tanh(2 * D_aq / L).
    # Hand computation for D_aq = 10 m, L = 50 m:
    #   l_c = 0.5 * 50 * tanh(20/50) = 25 * tanh(0.4)
    #       = 25 * 0.3799490 = 9.498724 m
    assert compute_critical_pipe_length(10.0, 50.0) == pytest.approx(9.49872, rel=1e-4)


def test_alpha_exponent_hook():
    # Spec section 12, failure mode 4: substituting the 3D hole-type-exit
    # scale exponent alpha = -1/2 for the 2D Sellmeijer value alpha = -1/3
    # must strictly lower H_c at field seepage lengths (van Beek 2015
    # scale-effect divergence; Pol's 3D simulations report H_c = 0.470 m
    # for a hole-type exit vs ~2.7-3.0 m for the 2D Sellmeijer reference,
    # user-provided reference sheet section 5).
    # Representative field-scale set: L = 50 m, D_aq = 10 m, Pol base-case
    # sand (k_aq = 1.62e-4 m/s, d_70 = 0.200 mm, gamma'_p = 16.19 kN/m^3).
    theta = _theta_row(1.62e-4, 200e-6, 10.0, GAMMA_SUB_POL_BASE_KN_M3)
    geometry = {"L": 50.0}
    h_c_2d = compute_critical_head(theta, geometry, alpha_exponent=-1.0 / 3.0)
    h_c_3d = compute_critical_head(theta, geometry, alpha_exponent=-1.0 / 2.0)
    assert h_c_3d < h_c_2d


def test_hc_positive_for_large_sample():
    # Spec section 12, failure mode 2: H_c must remain positive and finite
    # over physically defensible parameter bounds. Bounds: d_70 within the
    # Sellmeijer (2011) Table 2 validity range [150 um, 430 um]; k_aq in
    # [1e-5, 1e-3] m/s (silty sand to coarse sand/gravel); D_aq in
    # [2, 40] m; gamma'_p in [13, 18] kN/m^3 (quartz-density sands).
    rng = np.random.default_rng(20260610)
    n = 1000
    theta_matrix = _random_theta_matrix(rng, n)
    h_c = compute_critical_head_vectorized(theta_matrix, {"L": 50.0})
    assert h_c.shape == (n,)
    assert np.all(np.isfinite(h_c))
    assert np.all(h_c > 0.0)


def test_vectorized_matches_scalar():
    # Spec section 6 (shared preamble): the vectorized production path
    # must reproduce the scalar evaluator row by row to machine precision.
    rng = np.random.default_rng(42)
    n = 50
    theta_matrix = _random_theta_matrix(rng, n)
    geometry = {"L": 30.0}
    h_c_vec = compute_critical_head_vectorized(theta_matrix, geometry)
    h_c_scalar = np.array(
        [compute_critical_head(theta_matrix[j], geometry) for j in range(n)]
    )
    np.testing.assert_allclose(h_c_vec, h_c_scalar, rtol=1e-12, atol=0.0)
