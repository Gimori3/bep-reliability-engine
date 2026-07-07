"""Bit-identity drift guard for the ADR-0029 fast-path M7 timestepper.

``integrate_progression`` was restructured for speed (hoisted time-invariant
factors, gate-masked fractional power, whole-step skip below z_toe under the
instantaneous head model). The public kernels (``z_uplift``, ``z_heave``,
``equilibrium_head``, ``progression_rate``, ``erosion_indicator``) remain the
documented single sources of the physics; this module pins that the
restructured loop is **bit-identical** — ``numpy.array_equal``, no tolerance —
to the straightforward reference loop over those kernels (the pre-ADR-0029
implementation, reproduced verbatim below).

If a kernel's arithmetic ever changes without the inlined fast path following
(or vice versa), these tests fail exactly, not within a tolerance.

Regimes covered: vectorized batch and 0-d scalar inputs; a compound two-peak
hydrograph whose trough dips below z_toe (exercises the whole-step skip); a
hydrograph entirely below z_toe (every step after the first skipped); the
D_bl = 0 laboratory configuration (guarded exit-gradient division); non-zero
l_ini (uplift-gate bypass); per-realization stochastic L; trajectory storage;
and the lagged head model (skip must be disabled — state advances every step).
"""

from __future__ import annotations

import numpy as np
import pytest

from bep_reliability_engine.hydraulics import InstantaneousHead, LaggedHead
from bep_reliability_engine.initiation import erosion_indicator, z_heave, z_uplift
from bep_reliability_engine.progression import (
    ProgressionResult,
    equilibrium_head,
    integrate_progression,
    progression_rate,
)

Z_TOE_M = 2.0


def _reference_integrate(
    h_river_m,
    dt_s,
    head_model,
    z_toe_m,
    c_e,
    k_aq_mps,
    d_bl_m,
    gamma_bl_sub_knpm3,
    h_c_m,
    l_c_m,
    seepage_length_m,
    *,
    l_ini_m=0.0,
    store_trajectory=False,
) -> ProgressionResult:
    """The pre-ADR-0029 loop, verbatim, over the public kernels.

    Every step calls ``z_uplift``, ``z_heave``, ``erosion_indicator``,
    ``equilibrium_head`` and ``progression_rate`` exactly as the original
    implementation did — no hoisting, no masking, no skipping. This is the
    reference the fast path must reproduce bit for bit.
    """
    h_river = np.asarray(h_river_m, dtype=np.float64)
    n_steps = h_river.shape[0]

    c_e_arr = np.asarray(c_e, dtype=np.float64)
    k_aq = np.asarray(k_aq_mps, dtype=np.float64)
    d_bl = np.asarray(d_bl_m, dtype=np.float64)
    gamma_bl_sub = np.asarray(gamma_bl_sub_knpm3, dtype=np.float64)
    h_c = np.asarray(h_c_m, dtype=np.float64)
    l_c = np.asarray(l_c_m, dtype=np.float64)

    head_model.reset(float(h_river[0]))

    l_current = np.asarray(l_ini_m, dtype=np.float64)
    uplift_ever = np.asarray(False)
    heave_ever = np.asarray(False)
    t_uh = np.asarray(np.nan)

    trajectory = [] if store_trajectory else None

    for k in range(n_steps):
        h_aq = head_model.step(float(h_river[k]), dt_s)
        delta_h_blanket = h_aq - z_toe_m
        h_erosion = (float(h_river[k]) - z_toe_m) - 0.3 * d_bl

        uplift_now = z_uplift(delta_h_blanket, gamma_bl_sub, d_bl) < 0.0
        uplift_ever = uplift_ever | uplift_now

        with np.errstate(divide="ignore", invalid="ignore"):
            heave_now = z_heave(delta_h_blanket, gamma_bl_sub, d_bl) < 0.0

        co_occurrence = uplift_now & heave_now
        first_co = co_occurrence & np.isnan(t_uh)
        t_uh = np.where(first_co, k * dt_s, t_uh)
        heave_ever = heave_ever | heave_now

        i_er = erosion_indicator(uplift_ever, l_current > 0.0, heave_now)

        h_eq = equilibrium_head(l_current, h_c, l_c, seepage_length_m)
        rate = progression_rate(h_erosion, h_eq, c_e_arr, k_aq, seepage_length_m)
        dl = np.where(i_er, rate, 0.0) * dt_s

        l_current = np.minimum(l_current + dl, seepage_length_m)

        if trajectory is not None:
            trajectory.append(np.array(l_current))

    realization_shape = l_current.shape
    l_trajectory = np.stack(trajectory) if trajectory is not None else None
    return ProgressionResult(
        l_final_m=l_current,
        l_trajectory_m=l_trajectory,
        uplift_occurred=np.broadcast_to(uplift_ever, realization_shape).copy(),
        heave_occurred=np.broadcast_to(heave_ever, realization_shape).copy(),
        t_uh_s=np.broadcast_to(t_uh, realization_shape).copy(),
    )


def _random_theta(n: int, seed: int) -> dict[str, np.ndarray]:
    """Lognormal-flavored per-realization inputs spanning weak to strong."""
    rng = np.random.default_rng(seed)
    return {
        "c_e": np.exp(rng.normal(np.log(0.05), 0.7, n)),
        "k_aq": np.exp(rng.normal(np.log(2.0e-3), 0.5, n)),
        "d_bl": np.exp(rng.normal(np.log(0.9), 0.17, n)),
        "gamma_bl_sub": np.exp(rng.normal(np.log(6.9), 0.056, n)),
        "h_c": np.exp(rng.normal(np.log(2.5), 0.4, n)),
        "l_c": np.exp(rng.normal(np.log(3.0), 0.2, n)),
        "r_e": 1.0 / (1.0 + np.exp(-rng.normal(0.3, 0.8, n))),
    }


def _two_peak_hydrograph(
    peak_m: float, trough_m: float, base_m: float, n_steps: int = 96
) -> np.ndarray:
    """Compound two-peak stage series: base -> peak -> trough -> peak -> base.

    The trough (and the base) sit below z_toe when ``trough_m < Z_TOE_M``,
    exercising the whole-step skip through the inter-peak staircase segment.
    """
    n4 = n_steps // 4
    up1 = np.linspace(base_m, 0.7 * peak_m, n4)
    down1 = np.linspace(0.7 * peak_m, trough_m, n4)
    up2 = np.linspace(trough_m, peak_m, n4)
    down2 = np.linspace(peak_m, base_m, n_steps - 3 * n4)
    return np.concatenate([up1, down1, up2, down2])


def _assert_bit_identical(fast: ProgressionResult, ref: ProgressionResult) -> None:
    """Exact (bitwise) equality of every ProgressionResult field."""
    assert np.array_equal(fast.l_final_m, ref.l_final_m)
    assert fast.l_final_m.shape == ref.l_final_m.shape
    assert np.array_equal(fast.uplift_occurred, ref.uplift_occurred)
    assert np.array_equal(fast.heave_occurred, ref.heave_occurred)
    assert np.array_equal(fast.t_uh_s, ref.t_uh_s, equal_nan=True)
    if ref.l_trajectory_m is None:
        assert fast.l_trajectory_m is None
    else:
        assert fast.l_trajectory_m is not None
        assert np.array_equal(fast.l_trajectory_m, ref.l_trajectory_m)


def _run_both(h_river, theta, seepage_length, *, l_ini=0.0, store_trajectory=False):
    """Run fast path and reference on identical inputs and models."""
    dt_s = 3600.0
    fast = integrate_progression(
        h_river,
        dt_s,
        InstantaneousHead(theta["r_e"], Z_TOE_M),
        Z_TOE_M,
        c_e=theta["c_e"],
        k_aq_mps=theta["k_aq"],
        d_bl_m=theta["d_bl"],
        gamma_bl_sub_knpm3=theta["gamma_bl_sub"],
        h_c_m=theta["h_c"],
        l_c_m=theta["l_c"],
        seepage_length_m=seepage_length,
        l_ini_m=l_ini,
        store_trajectory=store_trajectory,
    )
    ref = _reference_integrate(
        h_river,
        dt_s,
        InstantaneousHead(theta["r_e"], Z_TOE_M),
        Z_TOE_M,
        c_e=theta["c_e"],
        k_aq_mps=theta["k_aq"],
        d_bl_m=theta["d_bl"],
        gamma_bl_sub_knpm3=theta["gamma_bl_sub"],
        h_c_m=theta["h_c"],
        l_c_m=theta["l_c"],
        seepage_length_m=seepage_length,
        l_ini_m=l_ini,
        store_trajectory=store_trajectory,
    )
    return fast, ref


def test_batch_with_sub_toe_trough_is_bit_identical() -> None:
    """Vectorized batch over a compound event whose trough skips steps."""
    theta = _random_theta(300, seed=42)
    h = _two_peak_hydrograph(peak_m=9.0, trough_m=0.5, base_m=0.2)
    assert np.any(h <= Z_TOE_M)  # the skip path is actually exercised
    fast, ref = _run_both(h, theta, 30.0)
    _assert_bit_identical(fast, ref)
    # The transition region is populated: some but not all realizations fail.
    assert 0 < np.count_nonzero(fast.l_final_m >= 30.0) < 300


def test_trajectory_storage_is_bit_identical_through_skipped_steps() -> None:
    """Full l(t) staircase equality, including entries for skipped steps."""
    theta = _random_theta(50, seed=7)
    h = _two_peak_hydrograph(peak_m=8.0, trough_m=0.0, base_m=0.0)
    fast, ref = _run_both(h, theta, 30.0, store_trajectory=True)
    _assert_bit_identical(fast, ref)
    assert fast.l_trajectory_m.shape == (h.size, 50)


def test_all_sub_toe_event_is_bit_identical_and_shape_conforming() -> None:
    """An event entirely below z_toe: every step after the first skips.

    The running state never leaves its seed values, so this pins that the
    skip path still conforms the diagnostics to the broadcast realization
    shape (step 0 always executes) and returns all-zeros / all-False / NaN.
    """
    theta = _random_theta(40, seed=3)
    h = np.full(24, Z_TOE_M - 1.0)
    fast, ref = _run_both(h, theta, 30.0)
    _assert_bit_identical(fast, ref)
    assert fast.l_final_m.shape == (40,)
    assert np.all(fast.l_final_m == 0.0)
    assert not np.any(fast.uplift_occurred)
    assert np.all(np.isnan(fast.t_uh_s))


def test_scalar_inputs_are_bit_identical() -> None:
    """0-d scalar realization (the evaluate_realization path)."""
    theta = {k: float(v[0]) for k, v in _random_theta(1, seed=11).items()}
    h = _two_peak_hydrograph(peak_m=9.5, trough_m=1.0, base_m=0.5)
    fast, ref = _run_both(h, theta, 30.0)
    _assert_bit_identical(fast, ref)
    assert fast.l_final_m.shape == ()


def test_no_blanket_lab_configuration_is_bit_identical() -> None:
    """D_bl = 0 (B25-245 box): guarded exit-gradient division, zero crack term."""
    theta = _random_theta(60, seed=19)
    theta["d_bl"] = np.zeros(60)
    h = _two_peak_hydrograph(peak_m=6.0, trough_m=1.5, base_m=1.5)
    fast, ref = _run_both(h, theta, 30.0)
    _assert_bit_identical(fast, ref)


def test_nonzero_l_ini_gate_bypass_is_bit_identical() -> None:
    """l_ini > 0 bypasses the uplift gate (spec §5); values must not drift."""
    theta = _random_theta(80, seed=23)
    h = _two_peak_hydrograph(peak_m=7.0, trough_m=0.5, base_m=0.5)
    fast, ref = _run_both(h, theta, 30.0, l_ini=1.5)
    _assert_bit_identical(fast, ref)


def test_stochastic_seepage_length_vector_is_bit_identical() -> None:
    """Per-realization L (the stochastic-L production path)."""
    rng = np.random.default_rng(5)
    theta = _random_theta(120, seed=29)
    seepage = np.exp(rng.normal(np.log(30.0), 0.2, 120))
    h = _two_peak_hydrograph(peak_m=9.0, trough_m=0.5, base_m=0.5)
    fast, ref = _run_both(h, theta, seepage)
    _assert_bit_identical(fast, ref)


def test_lagged_head_model_never_skips_and_is_bit_identical() -> None:
    """LaggedHead carries state: the skip must be disabled, values identical.

    The hydrograph dips below z_toe mid-event; a skipped step would freeze
    the lag state and corrupt every subsequent head. Equality against the
    (never-skipping) reference proves the skip is correctly gated on the
    instantaneous model only.
    """
    theta = _random_theta(60, seed=31)
    tau_aq = np.full(60, 7200.0)
    h = _two_peak_hydrograph(peak_m=9.0, trough_m=0.5, base_m=0.5)
    assert np.any(h <= Z_TOE_M)
    dt_s = 3600.0
    kwargs = dict(
        c_e=theta["c_e"],
        k_aq_mps=theta["k_aq"],
        d_bl_m=theta["d_bl"],
        gamma_bl_sub_knpm3=theta["gamma_bl_sub"],
        h_c_m=theta["h_c"],
        l_c_m=theta["l_c"],
        seepage_length_m=30.0,
    )
    fast = integrate_progression(
        h, dt_s, LaggedHead(theta["r_e"], Z_TOE_M, tau_aq), Z_TOE_M, **kwargs
    )
    ref = _reference_integrate(
        h, dt_s, LaggedHead(theta["r_e"], Z_TOE_M, tau_aq), Z_TOE_M, **kwargs
    )
    _assert_bit_identical(fast, ref)


@pytest.mark.parametrize("peak", [4.0, 9.0, 14.0])
def test_gate_regimes_across_peaks_are_bit_identical(peak: float) -> None:
    """Sweep peak levels so the gate is closed / transitional / saturated."""
    theta = _random_theta(150, seed=int(peak * 10))
    h = _two_peak_hydrograph(peak_m=peak, trough_m=0.5, base_m=0.5)
    fast, ref = _run_both(h, theta, 30.0)
    _assert_bit_identical(fast, ref)
