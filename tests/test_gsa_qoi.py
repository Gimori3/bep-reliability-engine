"""Drift guard for the GSA QoI adapter (``bep_reliability_engine.gsa_qoi``).

ADR-0033 §5: ``evaluate_qoi_batch`` mirrors M8's ``evaluate_batch`` kernel for
kernel, adding only the continuous outputs the GSA QoIs need. These tests pin
that mirror:

1. **Bit-identity of the failure flags** against ``evaluate_batch`` on the
   numpy backend, across the option surface (stochastic L, the ADR-0017
   transient-alpha decomposition, the ADR-0025 open-entry sensitivity).
2. **Internal consistency** of the continuous outputs with the flags
   (``failure_static == (z_static <= 0)``, ``failure_trans == (l_fraction >=
   1)``, ``0 <= l_e <= L``).
3. **Scalar cross-check**: a handful of rows against the frozen Phase 2 API
   ``evaluate_realization`` (H_c, Z_static, l_e_final).

The fixture style follows ``tests/test_evaluator.py`` (a concrete M3
``HydrographRecord`` built directly, the flat M8 geometry dict).
"""

import numpy as np
import pytest

from bep_reliability_engine.evaluator import evaluate_batch, evaluate_realization
from bep_reliability_engine.gsa_qoi import QoiBatch, evaluate_qoi_batch
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.sampling import MarginalSpec, sample_theta

GEOMETRY = {
    "L": 30.0,
    "z_toe": 2.0,
    "foreshore_width": 50.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}
DT_S = 600.0
N_ROWS = 300


def _two_peak_hydrograph(peak_m: float) -> HydrographRecord:
    """A compound two-peak record exercising the memory model (spec §5)."""
    n = 72
    t = np.arange(n, dtype=np.float64) * DT_S
    half = n // 2
    hump1 = 0.5 * (1.0 - np.cos(np.linspace(0.0, 2.0 * np.pi, half)))
    hump2 = 0.5 * (1.0 - np.cos(np.linspace(0.0, 2.0 * np.pi, n - half)))
    shape = np.concatenate([0.6 * hump1, hump2])
    shape /= shape.max()
    z_toe = GEOMETRY["z_toe"]
    h = z_toe + (peak_m - z_toe) * shape
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(peak_m),
        duration_hours=float(n * DT_S / 3600.0),
        scenario="historical",
        event_id="gsa-qoi-test",
        native_dt=DT_S,
    )


def _theta_population() -> np.ndarray:
    """A production-style (N, 7) prior population (tuned to mixed outcomes)."""
    marginals = (
        MarginalSpec("k_aq", "lognormal", 2.0e-3, 0.50),
        MarginalSpec("d_70", "lognormal", 5.3e-4, 0.30),
        MarginalSpec("D_aq", "lognormal", 8.0, 0.10),
        MarginalSpec("D_bl", "lognormal", 0.85, 0.167),
        MarginalSpec("k_bl", "lognormal", 1.0e-6, 0.50),
        MarginalSpec("gamma_bl_sub", "lognormal", 6.9, 0.056),
        MarginalSpec("C_e", "lognormal", 0.055, 0.782),
    )
    return sample_theta(
        marginals,
        seed=2026,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        n_samples=N_ROWS,
        coupling="two_population",
        bounds={"d_70": (5.0e-5, 1.0e-3)},
    ).theta_matrix


# Peak tuned so BOTH branches produce mixed outcomes over the population
# (static 270/300, transient 12/300 at 4.5 m): production sections operate at
# gross heads of a few m (H_c/L ~ 0.1), not at tens of m.
THETA = _theta_population()
HYDROGRAPH = _two_peak_hydrograph(peak_m=4.5)


def _seepage_samples() -> np.ndarray:
    rng = np.random.default_rng(7)
    return np.exp(rng.normal(np.log(GEOMETRY["L"]), 0.2, N_ROWS))


CASES = {
    "baseline": {},
    "stochastic_L": {"seepage_length_samples": _seepage_samples()},
    "transient_alpha": {"alpha_exponent_transient": -0.5},
    "open_entry": {"foreland_open": True},
    "l_ini": {"l_ini": 2.0},
}


@pytest.mark.parametrize("case", CASES.keys())
def test_flags_bit_identical_to_evaluate_batch(case):
    """The adapter's failure flags equal M8's exactly (numpy backend)."""
    kwargs = CASES[case]
    qoi = evaluate_qoi_batch(THETA, HYDROGRAPH, GEOMETRY, **kwargs)
    ref_static, ref_trans = evaluate_batch(THETA, HYDROGRAPH, GEOMETRY, **kwargs)
    np.testing.assert_array_equal(qoi.failure_static, ref_static)
    np.testing.assert_array_equal(qoi.failure_trans, ref_trans)


def test_outcome_mix_is_nontrivial():
    """The fixture produces mixed outcomes, so bit-identity is a real test."""
    qoi = evaluate_qoi_batch(THETA, HYDROGRAPH, GEOMETRY)
    for flags in (qoi.failure_static, qoi.failure_trans):
        assert 0 < int(flags.sum()) < N_ROWS


def test_continuous_outputs_consistent_with_flags():
    """Margins, fractions, and flags agree by definition (ADR-0033 §1)."""
    seepage = _seepage_samples()
    qoi = evaluate_qoi_batch(
        THETA, HYDROGRAPH, GEOMETRY, seepage_length_samples=seepage
    )
    assert isinstance(qoi, QoiBatch)
    np.testing.assert_array_equal(qoi.failure_static, qoi.z_static_m <= 0.0)
    # Breach rows have l_e clipped to exactly L, so l_fraction == 1.0 there.
    np.testing.assert_array_equal(qoi.failure_trans, qoi.l_fraction >= 1.0)
    assert np.all(qoi.l_e_final_m >= 0.0)
    assert np.all(qoi.l_e_final_m <= seepage + 1e-12)
    assert np.all((qoi.l_fraction >= 0.0) & (qoi.l_fraction <= 1.0))
    # Y4 is H_c minus the level constant.
    np.testing.assert_allclose(
        qoi.z_static_m,
        qoi.h_c_m - (HYDROGRAPH.peak - GEOMETRY["z_toe"]),
        rtol=0.0,
        atol=0.0,
    )


def test_scalar_cross_check_against_frozen_api():
    """A few rows against ``evaluate_realization`` (the Phase 2 contract)."""
    qoi = evaluate_qoi_batch(THETA, HYDROGRAPH, GEOMETRY)
    for j in (0, 57, 123, N_ROWS - 1):
        ref = evaluate_realization(THETA[j], HYDROGRAPH, GEOMETRY)
        assert qoi.z_static_m[j] == ref.Z_static
        assert qoi.l_e_final_m[j] == ref.l_e_final
        assert qoi.h_c_m[j] == ref.H_c
        assert bool(qoi.failure_trans[j]) == ref.failure_trans


def test_unknown_backend_refused():
    """The ADR-0029 backend guard is mirrored."""
    with pytest.raises(ValueError, match="progression_backend"):
        evaluate_qoi_batch(THETA, HYDROGRAPH, GEOMETRY, progression_backend="jax")
