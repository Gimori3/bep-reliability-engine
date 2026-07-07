"""Equivalence tests for the opt-in Numba M7 backend (ADR-0029).

The numba kernel (``progression_numba.integrate_progression_numba``) is the
JIT-parallel twin of the numpy timestepper. Its contract is **numerical
equivalence, not bit-identity**: every float output within 1e-10 of the numpy
path, every boolean latch and every t_uh exactly equal (the gate logic is
power-free, so latch timing cannot drift). These tests prove that contract
across the same regimes the fast-path drift guard covers, plus the M8
dispatch (``evaluate_batch(progression_backend='numba')``) and the config
gate (numba + aquifer lag refused).

Skipped in environments without the optional numba dependency
(``pip install -e .[accel]``).
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("numba")

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.evaluator import evaluate_batch  # noqa: E402
from bep_reliability_engine.hydraulics import InstantaneousHead  # noqa: E402
from bep_reliability_engine.progression import integrate_progression  # noqa: E402
from bep_reliability_engine.progression_numba import (  # noqa: E402
    integrate_progression_numba,
)

Z_TOE_M = 2.0
DT_S = 3600.0

# ADR-0029 equivalence bound on float outputs (l_final in meters).
ATOL = 1.0e-10


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
    """Compound two-peak stage series exercising trough + skip behavior."""
    n4 = n_steps // 4
    return np.concatenate(
        [
            np.linspace(base_m, 0.7 * peak_m, n4),
            np.linspace(0.7 * peak_m, trough_m, n4),
            np.linspace(trough_m, peak_m, n4),
            np.linspace(peak_m, base_m, n_steps - 3 * n4),
        ]
    )


def _run_both(h_river, theta, seepage_length, *, l_ini=0.0):
    """Run the numpy reference and the numba kernel on identical inputs."""
    common = dict(
        c_e=theta["c_e"],
        k_aq_mps=theta["k_aq"],
        d_bl_m=theta["d_bl"],
        gamma_bl_sub_knpm3=theta["gamma_bl_sub"],
        h_c_m=theta["h_c"],
        l_c_m=theta["l_c"],
        seepage_length_m=seepage_length,
        l_ini_m=l_ini,
    )
    ref = integrate_progression(
        h_river, DT_S, InstantaneousHead(theta["r_e"], Z_TOE_M), Z_TOE_M, **common
    )
    jit = integrate_progression_numba(h_river, DT_S, theta["r_e"], Z_TOE_M, **common)
    return jit, ref


def _assert_equivalent(jit, ref) -> None:
    """The ADR-0029 equivalence contract: <= 1e-10 floats, exact booleans."""
    assert jit.l_final_m.shape == ref.l_final_m.shape
    np.testing.assert_allclose(jit.l_final_m, ref.l_final_m, rtol=0.0, atol=ATOL)
    assert np.array_equal(jit.uplift_occurred, ref.uplift_occurred)
    assert np.array_equal(jit.heave_occurred, ref.heave_occurred)
    # t_uh is gate-driven (power-free), so it must match exactly, NaNs aligned.
    assert np.array_equal(jit.t_uh_s, ref.t_uh_s, equal_nan=True)
    assert jit.l_trajectory_m is None


def test_batch_transition_regime_is_equivalent() -> None:
    """N=300 across the transition: some fail, some do not; <= 1e-10 agreement."""
    theta = _random_theta(300, seed=42)
    h = _two_peak_hydrograph(peak_m=9.0, trough_m=0.5, base_m=0.2)
    jit, ref = _run_both(h, theta, 30.0)
    _assert_equivalent(jit, ref)
    assert 0 < np.count_nonzero(ref.l_final_m >= 30.0) < 300


@pytest.mark.parametrize("peak", [4.0, 9.0, 14.0])
def test_gate_regimes_across_peaks_are_equivalent(peak: float) -> None:
    """Gate closed / transitional / saturated (breach-clip absorbing)."""
    theta = _random_theta(150, seed=int(peak * 10))
    h = _two_peak_hydrograph(peak_m=peak, trough_m=0.5, base_m=0.5)
    jit, ref = _run_both(h, theta, 30.0)
    _assert_equivalent(jit, ref)


def test_no_blanket_lab_configuration_is_equivalent() -> None:
    """D_bl = 0: the guarded division must resolve identically (inf/nan gate)."""
    theta = _random_theta(60, seed=19)
    theta["d_bl"] = np.zeros(60)
    h = _two_peak_hydrograph(peak_m=6.0, trough_m=1.5, base_m=1.5)
    jit, ref = _run_both(h, theta, 30.0)
    _assert_equivalent(jit, ref)


def test_nonzero_l_ini_and_stochastic_length_are_equivalent() -> None:
    """l_ini gate bypass plus per-realization L, together."""
    rng = np.random.default_rng(5)
    theta = _random_theta(120, seed=29)
    seepage = np.exp(rng.normal(np.log(30.0), 0.2, 120))
    h = _two_peak_hydrograph(peak_m=9.0, trough_m=0.5, base_m=0.5)
    jit, ref = _run_both(h, theta, seepage, l_ini=1.5)
    _assert_equivalent(jit, ref)


def test_scalar_inputs_produce_scalar_shape() -> None:
    """0-d inputs yield the 0-d realization shape, matching the numpy path."""
    theta = {k: float(v[0]) for k, v in _random_theta(1, seed=11).items()}
    h = _two_peak_hydrograph(peak_m=9.5, trough_m=1.0, base_m=0.5)
    jit, ref = _run_both(h, theta, 30.0)
    assert jit.l_final_m.shape == ref.l_final_m.shape == ()
    _assert_equivalent(jit, ref)


def test_all_sub_toe_event_is_equivalent() -> None:
    """Every step below z_toe: nothing happens on either backend."""
    theta = _random_theta(40, seed=3)
    h = np.full(24, Z_TOE_M - 1.0)
    jit, ref = _run_both(h, theta, 30.0)
    _assert_equivalent(jit, ref)
    assert np.all(jit.l_final_m == 0.0)


def test_kernel_validates_garbage_inputs() -> None:
    """Non-finite inputs, negative C_e and l_ini > L are refused loudly."""
    theta = _random_theta(10, seed=1)
    h = _two_peak_hydrograph(peak_m=9.0, trough_m=0.5, base_m=0.5)

    with pytest.raises(ValueError, match="finite stage"):
        bad_h = h.copy()
        bad_h[3] = np.nan
        _run_both(bad_h, theta, 30.0)

    with pytest.raises(ValueError, match="C_e"):
        bad = {**theta, "c_e": theta["c_e"] * -1.0}
        integrate_progression_numba(
            h,
            DT_S,
            bad["r_e"],
            Z_TOE_M,
            c_e=bad["c_e"],
            k_aq_mps=bad["k_aq"],
            d_bl_m=bad["d_bl"],
            gamma_bl_sub_knpm3=bad["gamma_bl_sub"],
            h_c_m=bad["h_c"],
            l_c_m=bad["l_c"],
            seepage_length_m=30.0,
        )

    with pytest.raises(ValueError, match="l_ini"):
        integrate_progression_numba(
            h,
            DT_S,
            theta["r_e"],
            Z_TOE_M,
            c_e=theta["c_e"],
            k_aq_mps=theta["k_aq"],
            d_bl_m=theta["d_bl"],
            gamma_bl_sub_knpm3=theta["gamma_bl_sub"],
            h_c_m=theta["h_c"],
            l_c_m=theta["l_c"],
            seepage_length_m=30.0,
            l_ini_m=31.0,
        )


# ---------------------------------------------------------------------------
# M8 dispatch and config gate
# ---------------------------------------------------------------------------

_GEOMETRY = {
    "L": 30.0,
    "z_toe": Z_TOE_M,
    "foreshore_width": 0.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}


class _Record:
    """Minimal duck-typed HydrographRecord stand-in (ADR-0010)."""

    def __init__(self, h: np.ndarray, dt_s: float) -> None:
        self.h = h
        self.peak = float(h.max())
        self.native_dt = dt_s


def _theta_matrix(n: int, seed: int) -> np.ndarray:
    """(N, 7) matrix in canonical column order, spanning the transition."""
    rng = np.random.default_rng(seed)
    return np.column_stack(
        [
            np.exp(rng.normal(np.log(1.0e-4), 0.5, n)),  # k_aq
            np.exp(rng.normal(np.log(2.0e-4), 0.3, n)),  # d_70
            np.exp(rng.normal(np.log(3.0), 0.1, n)),  # D_aq
            np.exp(rng.normal(np.log(3.0), 0.17, n)),  # D_bl
            np.exp(rng.normal(np.log(1.0e-6), 0.5, n)),  # k_bl
            np.exp(rng.normal(np.log(6.9), 0.056, n)),  # gamma_bl_sub
            np.exp(rng.normal(np.log(0.2), 0.7, n)),  # C_e (lifted, fast tests)
        ]
    )


def test_evaluate_batch_numba_matches_numpy_backend() -> None:
    """The M8 dispatch: identical failure columns from both backends.

    The failure indicators are threshold crossings of quantities that agree
    to <= 1e-10; at test scale no realization sits within 1e-10 of the
    boundary, so the boolean columns must match exactly. The static branch
    has no timestepper and must be backend-invariant by construction.
    """
    theta = _theta_matrix(400, seed=99)
    h = _two_peak_hydrograph(peak_m=13.0, trough_m=2.5, base_m=2.5)
    record = _Record(h, DT_S)

    fs_np, ft_np = evaluate_batch(theta, record, _GEOMETRY)
    fs_nb, ft_nb = evaluate_batch(theta, record, _GEOMETRY, progression_backend="numba")

    assert np.array_equal(fs_np, fs_nb)
    assert np.array_equal(ft_np, ft_nb)
    assert 0 < ft_np.sum() < 400  # the transition is actually populated


def test_evaluate_batch_rejects_unknown_backend() -> None:
    theta = _theta_matrix(4, seed=1)
    record = _Record(_two_peak_hydrograph(9.0, 0.5, 0.5), DT_S)
    with pytest.raises(ValueError, match="progression_backend"):
        evaluate_batch(theta, record, _GEOMETRY, progression_backend="jax")


def test_config_accepts_numba_backend_and_gates_the_lag() -> None:
    """Config field: default numpy; numba accepted; numba + lag refused."""
    base = {
        "integration_scheme": "forward_euler",
        "target_dt_seconds": None,
        "convergence_test": False,
        "convergence_threshold": 0.01,
        "aquifer_lag_active": False,
        "specific_storage_per_m": None,
    }
    from bep_reliability_engine.config import TimestepperSettings

    assert TimestepperSettings.model_validate(base).progression_backend == "numpy"
    assert (
        TimestepperSettings.model_validate(
            {**base, "progression_backend": "numba"}
        ).progression_backend
        == "numba"
    )
    with pytest.raises(ValueError):
        TimestepperSettings.model_validate({**base, "progression_backend": "jax"})
    with pytest.raises(ValueError, match="instantaneous"):
        TimestepperSettings.model_validate(
            {
                **base,
                "progression_backend": "numba",
                "aquifer_lag_active": True,
                "specific_storage_per_m": 1.0e-5,
            }
        )
    # Config-level import sanity: the field threads to the full Config too.
    assert "progression_backend" in TimestepperSettings.model_fields
    assert Config.model_fields["timestepper"].annotation is TimestepperSettings
