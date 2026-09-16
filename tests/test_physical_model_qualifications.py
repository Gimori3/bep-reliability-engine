"""Pin the physical relations the 2026-09-16 qualification pass corrected.

These are analytic properties of the implemented kernels, not reruns of the
study. Each one contradicts a statement the thesis carried before that pass, so
a regression here would let the old statement become true again and go
unnoticed. Evidence and the measured numbers live in
``docs/decisions/physical-model-qualifications-study.md`` and its JSON.

Nothing here touches a default, a config or a persisted result.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from bep_reliability_engine import hydraulics, initiation, sellmeijer
from bep_reliability_engine.constants import GAMMA_W

REPO = Path(__file__).resolve().parents[1]

# One representative production realization: KP 60.0's matrix prior means, in
# the canonical theta order ['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl',
# 'gamma_bl_sub', 'C_e'].
THETA_KP60 = np.array([1.0e-3, 2.6e-4, 9.0, 0.85, 1.0e-6, 6.9, 0.055])
L_KP60_M = 34.8


def _h_c(length_m: float, theta: np.ndarray = THETA_KP60) -> float:
    return float(sellmeijer.compute_critical_head(theta, {"L": length_m}).H_c)


class TestCriticalHeadIsSublinearInSeepageLength:
    """H_c grows with L, but the critical gradient H_c/L falls.

    The thesis said "linearly" and "decreasing piping resistance as L
    increases" before 2026-09-16. Both are wrong on the implemented rule:
    F_s carries L^(-1/3) and F_g carries a further positive power, so the
    exponent lands near 0.89 and neither statement survives.
    """

    def test_critical_head_strictly_increases_with_length(self) -> None:
        lengths = [20.0, 34.8, 50.0, 100.0, 200.0, 600.0]
        heads = [_h_c(value) for value in lengths]
        assert all(b > a for a, b in zip(heads, heads[1:]))

    def test_critical_gradient_strictly_decreases_with_length(self) -> None:
        lengths = [20.0, 34.8, 50.0, 100.0, 200.0, 600.0]
        gradients = [_h_c(value) / value for value in lengths]
        assert all(b < a for a, b in zip(gradients, gradients[1:]))

    def test_exponent_is_sublinear_and_near_the_reported_value(self) -> None:
        low, high = _h_c(L_KP60_M * 0.99), _h_c(L_KP60_M * 1.01)
        exponent = math.log(high / low) / math.log(1.01 / 0.99)
        assert 0.80 < exponent < 0.95
        # The value the thesis now prints, to two decimals.
        assert exponent == pytest.approx(0.89, abs=0.01)

    def test_a_doubled_path_does_not_double_the_critical_head(self) -> None:
        assert _h_c(2 * L_KP60_M) < 2 * _h_c(L_KP60_M)


class TestBlanketThicknessEntersTheTwoGateTermsDifferently:
    """The uplift margin is proportional to D_bl; only the gradient is inverse.

    The thesis said both scaled inversely with thickness before 2026-09-16.
    """

    DELTA_H_M = 0.60
    GAMMA_BL_SUB = 6.9

    def test_uplift_margin_is_proportional_to_thickness(self) -> None:
        thin = float(initiation.z_uplift(self.DELTA_H_M, self.GAMMA_BL_SUB, 0.45))
        thick = float(initiation.z_uplift(self.DELTA_H_M, self.GAMMA_BL_SUB, 0.85))
        assert thick > thin
        # Exactly linear: the resistance term is gamma'_bl * D_bl / gamma_w.
        resistance_thin = thin + self.DELTA_H_M
        resistance_thick = thick + self.DELTA_H_M
        assert resistance_thick / resistance_thin == pytest.approx(0.85 / 0.45)

    def test_heave_exit_gradient_is_inversely_proportional_to_thickness(self) -> None:
        thin = self.DELTA_H_M / 0.45
        thick = self.DELTA_H_M / 0.85
        assert thin > thick
        assert thin / thick == pytest.approx(0.85 / 0.45)
        # And the heave margin is the uplift margin divided by the thickness
        # (ADR-0008), which is what makes a single thickness statement wrong.
        for d_bl in (0.45, 0.85):
            z_u = float(initiation.z_uplift(self.DELTA_H_M, self.GAMMA_BL_SUB, d_bl))
            z_h = float(initiation.z_heave(self.DELTA_H_M, self.GAMMA_BL_SUB, d_bl))
            assert z_h == pytest.approx(z_u / d_bl)

    def test_a_thinner_blanket_is_unfavourable_on_both_terms(self) -> None:
        """Opposite scalings, same direction of vulnerability."""
        head_to_open_gate = {
            d_bl: self.GAMMA_BL_SUB * d_bl / GAMMA_W for d_bl in (0.45, 0.85)
        }
        assert head_to_open_gate[0.45] < head_to_open_gate[0.85]


class TestErosionRateUsesAPositivePart:
    """The fractional power is applied to a clipped overload, never a negative.

    The Chapter 2 equation printed no positive part before 2026-09-16, which
    left the rate undefined whenever the gate stood open below the equilibrium
    head.
    """

    def test_rate_is_zero_below_the_equilibrium_head(self) -> None:
        from bep_reliability_engine.progression import progression_rate

        rate = progression_rate(
            h_erosion_m=1.0,
            h_eq_m=2.5,
            c_e=0.055,
            k_aq_mps=1.0e-3,
            seepage_length_m=L_KP60_M,
        )
        assert float(rate) == 0.0

    def test_rate_is_finite_and_positive_above_it(self) -> None:
        from bep_reliability_engine.progression import progression_rate

        rate = float(
            progression_rate(
                h_erosion_m=3.0,
                h_eq_m=2.5,
                c_e=0.055,
                k_aq_mps=1.0e-3,
                seepage_length_m=L_KP60_M,
            )
        )
        assert rate > 0.0 and math.isfinite(rate)

    def test_a_deep_negative_overload_never_produces_nan(self) -> None:
        from bep_reliability_engine.progression import progression_rate

        rates = progression_rate(
            h_erosion_m=np.array([-5.0, 0.0, 2.49, 2.5]),
            h_eq_m=2.5,
            c_e=0.055,
            k_aq_mps=1.0e-3,
            seepage_length_m=L_KP60_M,
        )
        assert np.all(np.isfinite(rates))
        assert np.all(rates == 0.0)


class TestTheCrackDecrementDoesNotOrderTheSections:
    """0.3 * D_bl is largest at the two 0.85 m sections, not at KP 57.4."""

    D_BL_BY_KP = {"57.4": 0.80, "58.8": 0.85, "60.0": 0.85, "62.0": 0.45}
    TRANSIENT_MINUS_STATIC_OFFSET_M = {
        "57.4": 0.74,
        "58.8": 0.88,
        "60.0": 1.20,
        "62.0": 1.49,
    }

    def test_kp57_4_does_not_carry_the_largest_decrement(self) -> None:
        decrements = {kp: 0.3 * d for kp, d in self.D_BL_BY_KP.items()}
        assert decrements["57.4"] == pytest.approx(0.240)
        assert decrements["62.0"] == pytest.approx(0.135)
        assert max(decrements, key=decrements.get) != "57.4"
        assert decrements["58.8"] > decrements["57.4"]
        assert decrements["60.0"] > decrements["57.4"]

    def test_the_smallest_decrement_carries_the_largest_offset(self) -> None:
        decrements = {kp: 0.3 * d for kp, d in self.D_BL_BY_KP.items()}
        smallest = min(decrements, key=decrements.get)
        largest_offset = max(
            self.TRANSIENT_MINUS_STATIC_OFFSET_M,
            key=self.TRANSIENT_MINUS_STATIC_OFFSET_M.get,
        )
        assert smallest == largest_offset == "62.0"


class TestExitGradientsDoNotSelectASeepageLengthConvention:
    """A local exit gradient is not an average along the path.

    Reproduces, at KP 60.0's committed geometry and prior means, the comparison
    that replaced the withdrawn back-calculation cross-check.
    """

    LAMBDA_ARGS = dict(k_aq_mps=1.0e-3, d_aq_m=9.0, d_bl_m=0.85, k_bl_mps=1.0e-6)
    L_M = 34.8
    B_F_M = 600.0
    HEAD_1998_M = 43.06 - 40.0
    REPORTED_I_V = 0.50
    REPORTED_I_H = 0.40

    def _factors(self) -> tuple[float, float, float]:
        lam_in = float(hydraulics.leakage_length_in(**self.LAMBDA_ARGS))
        lam_out = float(
            hydraulics.leakage_length_out(
                k_aq_mps=1.0e-3,
                d_aq_m=9.0,
                d_fore_m=0.85,
                k_fore_mps=1.0e-6,
                foreshore_width_m=self.B_F_M,
            )
        )
        return lam_in, lam_out, self.LAMBDA_ARGS["d_bl_m"]

    def test_neither_convention_reproduces_the_reported_vertical_gradient(self) -> None:
        lam_in, lam_out, d_bl = self._factors()
        under = float(hydraulics.response_factor(lam_in, lam_out, self.L_M))
        spanning = float(
            hydraulics.response_factor(lam_in, lam_out, self.L_M + self.B_F_M)
        )
        i_v_under = under * self.HEAD_1998_M / d_bl
        i_v_spanning = spanning * self.HEAD_1998_M / d_bl
        # The under-levee convention over-predicts by about three,
        # the foreshore-spanning one under-predicts by about 1.3.
        assert i_v_under / self.REPORTED_I_V == pytest.approx(3.00, abs=0.05)
        assert i_v_spanning / self.REPORTED_I_V == pytest.approx(0.78, abs=0.05)
        # The alternative is the closer of the two here, so the comparison
        # cannot be offered as corroboration of the adopted convention.
        assert abs(math.log(i_v_spanning / self.REPORTED_I_V)) < abs(
            math.log(i_v_under / self.REPORTED_I_V)
        )

    def test_the_modelled_horizontal_gradient_is_far_below_the_reported_one(
        self,
    ) -> None:
        lam_in, lam_out, _ = self._factors()
        under = float(hydraulics.response_factor(lam_in, lam_out, self.L_M))
        i_h_model = under * self.HEAD_1998_M / lam_in
        assert i_h_model < self.REPORTED_I_H / 10.0
        # And it is the same order as the "incapable" average gradient the
        # withdrawn argument rejected, which is why that argument proved too
        # much: applied consistently it refutes the adopted convention too.
        average_gradient = self.HEAD_1998_M / (self.L_M + self.B_F_M)
        assert 0.5 < i_h_model / average_gradient < 10.0


class TestScourConversionChangesTheRateNotTheThreshold:
    """The ADR-0042 correction divides the erodibility, not the threshold.

    Chapter 7 explained the exact-zero scour result by a threshold the loading
    never reaches. The threshold is sampled and is untouched by the conversion.
    """

    def test_the_two_conversions_differ_by_the_stress_unit_ratio(self) -> None:
        from system_integration.uemura_models import (
            PSF_TO_PA,
            SCOUR_K_CONVERSION_SCRIPT,
            SCOUR_K_CONVERSION_USACE,
        )

        ratio = SCOUR_K_CONVERSION_SCRIPT / SCOUR_K_CONVERSION_USACE
        assert ratio == pytest.approx(PSF_TO_PA / 0.45359237)
        assert ratio == pytest.approx(105.56, abs=0.01)

    def test_the_critical_shear_draws_are_identical_under_both_conversions(
        self,
    ) -> None:
        from system_integration.uemura_models import (
            SCOUR_K_CONVERSION_SCRIPT,
            SCOUR_K_CONVERSION_USACE,
            draw_scour,
        )

        corrected = draw_scour(
            np.random.default_rng(np.random.SeedSequence(7)),
            2048,
            k_conversion=SCOUR_K_CONVERSION_USACE,
        )
        as_received = draw_scour(
            np.random.default_rng(np.random.SeedSequence(7)),
            2048,
            k_conversion=SCOUR_K_CONVERSION_SCRIPT,
        )
        np.testing.assert_array_equal(corrected.tau_c_pa, as_received.tau_c_pa)
        np.testing.assert_allclose(
            as_received.k_si_per_hr_pa / corrected.k_si_per_hr_pa,
            SCOUR_K_CONVERSION_SCRIPT / SCOUR_K_CONVERSION_USACE,
            rtol=1e-12,
        )

    def test_the_threshold_is_sampled_and_a_large_share_falls_below_50_pa(
        self,
    ) -> None:
        from system_integration.uemura_models import (
            PSF_TO_PA,
            SCOUR_K_CONVERSION_USACE,
            SCOUR_TAU_C_COV,
            SCOUR_TAU_C_MEAN_PSF,
            draw_scour,
        )

        draws = draw_scour(
            np.random.default_rng(np.random.SeedSequence(11)),
            20_000,
            k_conversion=SCOUR_K_CONVERSION_USACE,
        )
        mean_pa = SCOUR_TAU_C_MEAN_PSF * PSF_TO_PA
        assert mean_pa == pytest.approx(50.66, abs=0.05)
        assert SCOUR_TAU_C_COV == pytest.approx(0.560)
        assert float(np.std(draws.tau_c_pa)) > 0.3 * mean_pa
        # "Roughly 51 Pa exceeds the loading throughout" was never a property
        # of the draws: a quarter of them sit below 30 Pa.
        assert float(np.mean(draws.tau_c_pa < 30.0)) > 0.2
