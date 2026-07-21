"""Tests for the ADR-0042 Uemura surface-model reproductions.

The load-bearing tests are the literal-transcription equivalences: the
vectorized module implementations are compared against direct scalar
transcriptions of Uemura's own reference code (the WP2 notebook
``count_failures`` loop for overflow; ``ErosionModel_231019.py`` for scour)
on random inputs — bit-level agreement of the failure decisions.
"""

from __future__ import annotations

import numpy as np
import pytest

from system_integration.uemura_models import (
    GRAVITY_MPS2,
    OVERFLOW_DAMAGE_THRESHOLD,
    OVERFLOW_FRICTION_F,
    PSF_TO_PA,
    SCOUR_BED_ROUGHNESS_KB_M,
    SCOUR_K_CONVERSION_SCRIPT,
    SCOUR_K_CONVERSION_USACE,
    SCOUR_MANNING_N,
    SCOUR_MIN_DEPTH_M,
    OverflowDraws,
    ScourDraws,
    SegmentSurfaceInputs,
    draw_overflow,
    draw_scour,
    load_segment_inputs,
    overflow_failure_fraction,
    scour_failure_fraction,
)

SEGMENT_INPUTS_CSV = "data/processed/uemura_segments/segment_inputs.csv"


def _example_inputs(**overrides) -> SegmentSurfaceInputs:
    base = dict(
        river="Tokachi",
        bank="right",
        kp=58.8,
        crest_design_m_msl=41.0,
        crest_err_mu_m=0.8,
        crest_err_sigma_m=0.05,
        ground_m_msl=38.0,
        floodplain_m_msl=36.5,
        crest_width_m=8.0,
        slope_h_per_v=3.0,
        water_surface_gradient_inv=617.0,
        wl_err_mu_m=0.6,
        wl_err_sigma_m=0.38,
    )
    base.update(overrides)
    return SegmentSurfaceInputs(**base)


# ---------------------------------------------------------------------------
# Reference transcriptions (scalar, verbatim algorithm structure)
# ---------------------------------------------------------------------------


def _overflow_reference(stage, dt_s, inputs, draws):
    """Scalar transcription of the WP2 notebook ``count_failures`` loop."""
    failures = 0
    n = draws.wl_err_m.size
    for i in range(n):
        wl_t = stage + draws.wl_err_m[i]
        depth = np.maximum(wl_t - draws.crest_m_msl[i], 0.0)
        qov = (GRAVITY_MPS2 * depth) ** 0.5 * depth
        v_toe = (
            8.0
            * GRAVITY_MPS2
            * qov
            * np.sin(np.arctan(1.0 / inputs.slope_h_per_v))
            / OVERFLOW_FRICTION_F
        ) ** (1.0 / 3.0)
        damage = np.sum(np.maximum(0.0, v_toe**3 - draws.u_c_mps[i] ** 3)) * dt_s
        if damage > OVERFLOW_DAMAGE_THRESHOLD:
            failures += 1
    return failures / n


def _scour_reference(stage, dt_s, inputs, draws):
    """Scalar transcription of ``ErosionModel_231019.py`` (his -999 mask)."""
    z_crest = inputs.crest_design_m_msl
    z_fp = inputs.floodplain_m_msl
    slope = inputs.slope_h_per_v
    s_ws = 1.0 / inputs.water_surface_gradient_inv

    depth = stage - z_fp
    depth[depth < 0.0] = 0.0
    depth[depth > z_crest - z_fp] = z_crest - z_fp
    velocity = (1.0 / SCOUR_MANNING_N) * depth ** (2.0 / 3.0) * s_ws**0.5
    with np.errstate(divide="ignore"):
        fc = 2.0 * (2.5 * np.log(30.0 * depth / SCOUR_BED_ROUGHNESS_KB_M)) ** (-2.0)
    fc = np.where(depth > 0.0, fc, 0.0)
    tau = 0.5 * 1000.0 * fc * velocity**2

    width = inputs.crest_width_m + (z_crest - stage) * slope
    width[stage > z_crest] = inputs.crest_width_m

    failures = 0
    n = draws.k_si_per_hr_pa.size
    for i in range(n):
        diff = tau - draws.tau_c_pa[i]
        # His mask1 + the ADR-0042 decision-10 depth floor.
        diff = np.where(stage - z_fp < SCOUR_MIN_DEPTH_M, 0.0, diff)
        diff = np.where(diff < 0.0, 0.0, diff)
        er = draws.k_si_per_hr_pa[i] * diff * (dt_s / 3600.0)
        crm = np.cumsum(er)
        crm = np.where(stage - inputs.ground_m_msl < 0.0, -999.0, crm)
        if np.max(crm - width) > 0.0:
            failures += 1
    return failures / n


# ---------------------------------------------------------------------------
# Equivalence with the reference transcriptions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_overflow_matches_reference_loop(seed):
    rng = np.random.default_rng(seed)
    inputs = _example_inputs()
    # A stage series straddling the crest so all regimes are exercised.
    t = np.arange(0.0, 48.0)
    stage = 39.0 + 3.5 * np.exp(-0.5 * ((t - 20.0) / 6.0) ** 2)
    draws = draw_overflow(rng, inputs, n_mc=400)
    fast = overflow_failure_fraction(stage, 3600.0, inputs, draws)
    slow = _overflow_reference(stage, 3600.0, inputs, draws)
    assert fast == slow


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_scour_matches_reference_loop(seed):
    rng = np.random.default_rng(seed)
    inputs = _example_inputs()
    t = np.arange(0.0, 96.0)
    stage = 36.0 + 5.5 * np.exp(-0.5 * ((t - 40.0) / 12.0) ** 2)
    draws = draw_scour(rng, n_mc=400)
    fast = scour_failure_fraction(stage, 3600.0, inputs, draws)
    slow = _scour_reference(stage.copy(), 3600.0, inputs, draws)
    assert fast == slow


# ---------------------------------------------------------------------------
# Hand-computed / structural cases
# ---------------------------------------------------------------------------


def test_overflow_zero_below_crest():
    """No crest exceedance in any draw => exactly zero failures."""
    inputs = _example_inputs()
    draws = OverflowDraws(
        wl_err_m=np.zeros(50),
        crest_m_msl=np.full(50, 41.8),
        u_c_mps=np.full(50, 1.8),
    )
    stage = np.full(100, 40.0)
    assert overflow_failure_fraction(stage, 3600.0, inputs, draws) == 0.0


def test_overflow_single_step_hand_value():
    """One time step, deterministic draws: damage crosses the threshold
    exactly where the hand-computed velocity implies."""
    inputs = _example_inputs(slope_h_per_v=3.0)
    depth = 0.8
    crest = 41.8
    draws = OverflowDraws(
        wl_err_m=np.zeros(1), crest_m_msl=np.array([crest]), u_c_mps=np.array([1.8])
    )
    q = np.sqrt(GRAVITY_MPS2 * depth) * depth
    v = (
        8.0 * GRAVITY_MPS2 * q * np.sin(np.arctan(1.0 / 3.0)) / OVERFLOW_FRICTION_F
    ) ** (1.0 / 3.0)
    work_one_hour = (v**3 - 1.8**3) * 3600.0
    n_steps_to_fail = int(np.ceil(OVERFLOW_DAMAGE_THRESHOLD / work_one_hour))
    stage_fail = np.full(n_steps_to_fail + 1, crest + depth)
    stage_hold = np.full(n_steps_to_fail - 1, crest + depth)
    assert overflow_failure_fraction(stage_fail, 3600.0, inputs, draws) == 1.0
    assert overflow_failure_fraction(stage_hold, 3600.0, inputs, draws) == 0.0


def test_scour_never_declared_below_ground():
    """Erosion may accumulate, but a breach is only declared while the
    stage loads the landside ground (his -999 mask)."""
    inputs = _example_inputs(ground_m_msl=44.0)  # ground above any stage here
    draws = ScourDraws(
        k_si_per_hr_pa=np.full(20, 10.0),  # absurdly erosive
        tau_c_pa=np.full(20, 0.1),
    )
    stage = np.full(500, 40.0)  # far above floodplain, below ground
    assert scour_failure_fraction(stage, 3600.0, inputs, draws) == 0.0


def test_scour_zero_below_floodplain():
    inputs = _example_inputs()
    draws = draw_scour(np.random.default_rng(0), 100)
    stage = np.full(200, inputs.floodplain_m_msl - 0.5)
    assert scour_failure_fraction(stage, 3600.0, inputs, draws) == 0.0


@pytest.mark.parametrize("mechanism", ["overflow", "scour"])
def test_monotone_in_peak_under_common_draws(mechanism):
    """ADR-0042 decision 5: fixed draws => P_f non-decreasing in the level."""
    rng = np.random.default_rng(7)
    inputs = _example_inputs()
    shape = np.sin(np.linspace(0.0, np.pi, 96)) ** 2  # 0..1..0
    h_base = 36.0
    levels = np.linspace(37.0, 45.0, 25)
    if mechanism == "overflow":
        draws = draw_overflow(rng, inputs, 300)
        fn = overflow_failure_fraction
    else:
        draws = draw_scour(rng, 300)
        fn = scour_failure_fraction
    p = [fn(h_base + (lv - h_base) * shape, 3600.0, inputs, draws) for lv in levels]
    assert np.all(np.diff(p) >= 0.0)


def test_scour_depth_floor_kills_log_law_singularity():
    """ADR-0042 decision 10: the f_c log-law diverges at depth k_b/30
    (~1.6 mm); a series parked in that sliver must contribute nothing."""
    inputs = _example_inputs(ground_m_msl=36.0)  # ground below the series
    draws = ScourDraws(
        k_si_per_hr_pa=np.full(10, 0.014),  # ~mean script-converted k
        tau_c_pa=np.full(10, 50.0),
    )
    singular_depth = SCOUR_BED_ROUGHNESS_KB_M / 30.0  # f_c -> infinity here
    assert singular_depth < SCOUR_MIN_DEPTH_M
    stage = np.full(500, inputs.floodplain_m_msl + singular_depth * 1.0000001)
    assert scour_failure_fraction(stage, 3600.0, inputs, draws) == 0.0
    # Just above the floor the model is live again (finite tau, no failure
    # here because tau(0.06 m) ~ 1 Pa << tau_c, but the mask is open).
    stage_live = np.full(500, inputs.floodplain_m_msl + SCOUR_MIN_DEPTH_M + 0.01)
    assert scour_failure_fraction(stage_live, 3600.0, inputs, draws) == 0.0


def test_scour_draws_positive_and_seeded():
    a = draw_scour(np.random.default_rng(42), 2000)
    b = draw_scour(np.random.default_rng(42), 2000)
    assert np.array_equal(a.k_si_per_hr_pa, b.k_si_per_hr_pa)
    assert np.array_equal(a.tau_c_pa, b.tau_c_pa)
    assert np.all(a.k_si_per_hr_pa > 0.0)
    assert np.all(a.tau_c_pa > 0.0)


def test_k_conversion_constants():
    """ADR-0042 decision 9: the script factor is ~105.6x the USACE factor."""
    ratio = SCOUR_K_CONVERSION_SCRIPT / SCOUR_K_CONVERSION_USACE
    assert ratio == pytest.approx(PSF_TO_PA / 0.45359237, rel=1e-12)
    assert ratio == pytest.approx(105.56, abs=0.05)


def test_load_segment_inputs_committed_csv():
    inputs = load_segment_inputs(SEGMENT_INPUTS_CSV)
    assert len(inputs) == 114
    kp588 = inputs[("Tokachi", 58.8)]
    assert kp588.bank == "right"
    assert kp588.crest_width_m == 8.0
    assert kp588.slope_h_per_v == 3.0
    sat = inputs[("Satsunai", 3.2)]
    assert sat.bank == "left"
    # ADR-0042 decision 6: Satsunai carries the adopted Obihiro pair.
    assert sat.wl_err_mu_m == 0.6
    assert sat.wl_err_sigma_m == 0.38


def test_primary_surface_curves_use_corrected_scour_conversion():
    """Drift guard for the ADR-0042 decision-9 amendment (2026-07-21): the
    committed *primary* surface curves carry the dimensionally-correct USACE
    scour conversion, under which fluvial scour is zero at every node; the
    as-received script conversion lives only in the labeled ``scour_script_k``
    companion. Regenerating with the script factor as primary regresses this."""
    from system_integration.surface_curves import load_surface_curves

    root = "data/processed/uemura_surface_curves"
    primary = load_surface_curves(f"{root}/uemura_surface_curves_historical.csv")
    scour = [c for c in primary.curves if c.mechanism == "fluvial_scour"]
    assert scour, "primary set must carry a fluvial_scour mechanism"
    assert all(
        np.all(c.p_f == 0.0) for c in scour
    ), "primary fluvial scour must be zero under the corrected USACE conversion"
    companion = load_surface_curves(f"{root}/uemura_surface_curves_scour_script_k.csv")
    csc = [c for c in companion.curves if c.mechanism == "fluvial_scour"]
    assert any(
        np.any(c.p_f > 0.0) for c in csc
    ), "the as-received script companion must carry nonzero scour"
