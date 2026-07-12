"""Pin tests for the ADR-0034 Phase 1 surface extensions.

Three additive public entry points exist so the Phase 2 survival replay can
run under assumptions identical to Phase 1 without touching any frozen
contract:

* ``evaluator.evaluate_batch_diagnostics`` — the single batch M8
  implementation (``evaluate_batch`` now delegates to it), returning the
  per-realization margins and M5/M7 diagnostics alongside the two failure
  flags. Pinned here: row-for-row **bit identity** with the scalar
  ``evaluate_realization`` (the same guarantee the production sweep rests
  on), and flag identity with ``evaluate_batch``.
* ``run.seepage_length_samples_for_config`` — regenerates the exact
  stochastic seepage-length draw a run paired with theta rows (the L vector
  is deliberately not persisted; Phase 2 must re-enter through this seam).
* ``run.conditioning_hydrographs_for_config`` — rebuilds the per-level
  loading records of the conditioning sweep (the Phase 2 posterior-fragility
  verification mode re-evaluates accepted rows on these).
"""

from __future__ import annotations

import numpy as np

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import (
    BatchDiagnostics,
    evaluate_batch,
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.run import (
    conditioning_hydrographs_for_config,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_seepage_length, sample_theta

_SEED = 20260712
_N = 60

_GEOMETRY = {
    "L": 30.0,
    "z_toe": 2.0,
    "foreshore_width": 40.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}

_MARGINALS = [
    ("k_aq", 1.0e-4, 0.50),
    ("d_70", 2.0e-4, 0.10),
    ("D_aq", 3.0, 0.20),
    ("D_bl", 3.0, 0.20),
    ("k_bl", 1.0e-6, 0.50),
    ("gamma_bl_sub", 6.9, 0.056),
    ("C_e", 0.20, 0.50),
]


def _theta_matrix() -> np.ndarray:
    from bep_reliability_engine.sampling import MarginalSpec

    specs = [
        MarginalSpec(name=name, family="lognormal", mean=mean, cov=cov)
        for name, mean, cov in _MARGINALS
    ]
    sample = sample_theta(
        specs,
        seed=_SEED,
        rho_log_kaq_d70=0.0,
        d70_interpretation="matrix",
        n_samples=_N,
        coupling="two_population",
    )
    return sample.theta_matrix


def _two_peak_hydrograph() -> HydrographRecord:
    """A compound two-peak event exercising the gate, trough and progression."""
    dt_s = 3600.0
    t = np.arange(48, dtype=np.float64) * dt_s
    first = 2.0 + 4.5 * np.sin(np.linspace(0.0, np.pi, 16)) ** 2
    trough = np.full(8, 2.0)
    second = 2.0 + 7.5 * np.sin(np.linspace(0.0, np.pi, 24)) ** 2
    h = np.concatenate([first, trough, second])
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(h.max()),
        duration_hours=47.0,
        scenario="historical",
        event_id="adr0034_fixture",
        native_dt=dt_s,
    )


def _scalar_reference(
    theta: np.ndarray,
    hydrograph: HydrographRecord,
    seepage_length_samples: np.ndarray | None,
) -> list:
    results = []
    for j in range(theta.shape[0]):
        geometry = dict(_GEOMETRY)
        if seepage_length_samples is not None:
            geometry["L"] = float(seepage_length_samples[j])
        results.append(evaluate_realization(theta[j], hydrograph, geometry, l_ini=0.0))
    return results


def test_flags_identical_between_batch_entry_points() -> None:
    """evaluate_batch and evaluate_batch_diagnostics return the same flags."""
    theta = _theta_matrix()
    hydrograph = _two_peak_hydrograph()
    col_static, col_trans = evaluate_batch(theta, hydrograph, _GEOMETRY)
    diagnostics = evaluate_batch_diagnostics(theta, hydrograph, _GEOMETRY)
    assert isinstance(diagnostics, BatchDiagnostics)
    np.testing.assert_array_equal(col_static, diagnostics.failure_static)
    np.testing.assert_array_equal(col_trans, diagnostics.failure_trans)


def test_diagnostics_rows_bit_identical_to_scalar_evaluator() -> None:
    """Every BatchDiagnostics field equals the scalar M8 result, row for row."""
    theta = _theta_matrix()
    hydrograph = _two_peak_hydrograph()
    diagnostics = evaluate_batch_diagnostics(theta, hydrograph, _GEOMETRY)
    reference = _scalar_reference(theta, hydrograph, None)

    for j, ref in enumerate(reference):
        assert diagnostics.Z_static[j] == ref.Z_static
        assert diagnostics.Z_transient[j] == ref.Z_transient
        assert diagnostics.l_e_final[j] == ref.l_e_final
        assert diagnostics.H_c[j] == ref.H_c
        assert diagnostics.H_c_transient[j] == ref.H_c_transient
        assert diagnostics.l_c[j] == ref.l_c
        assert diagnostics.lambda_in[j] == ref.lambda_in
        assert diagnostics.r_e[j] == ref.r_e
        assert bool(diagnostics.failure_static[j]) == ref.failure_static
        assert bool(diagnostics.failure_trans[j]) == ref.failure_trans
        assert bool(diagnostics.uplift_occurred[j]) == ref.uplift_occurred
        assert bool(diagnostics.heave_occurred[j]) == ref.heave_occurred
        if np.isnan(ref.t_uh):
            assert np.isnan(diagnostics.t_uh[j])
        else:
            assert diagnostics.t_uh[j] == ref.t_uh


def test_diagnostics_with_stochastic_seepage_length() -> None:
    """Per-row L pairs with theta row j exactly as in the scalar evaluator."""
    theta = _theta_matrix()
    hydrograph = _two_peak_hydrograph()
    seepage = sample_seepage_length(30.0, 0.2, seed=_SEED + 1, n_samples=_N)
    diagnostics = evaluate_batch_diagnostics(
        theta, hydrograph, _GEOMETRY, seepage_length_samples=seepage
    )
    reference = _scalar_reference(theta, hydrograph, seepage)
    for j, ref in enumerate(reference):
        assert diagnostics.Z_transient[j] == ref.Z_transient
        assert diagnostics.l_e_final[j] == ref.l_e_final
        assert diagnostics.H_c[j] == ref.H_c
        assert bool(diagnostics.failure_trans[j]) == ref.failure_trans


def _stub_config(**overrides) -> Config:
    data = {
        "cross_section_id": "test_xs",
        "segment_id": "TEST.000",
        "scenario": "historical",
        "remediation_state": "none",
        "geometry": {
            "L": 30.0,
            "z_toe": 2.0,
            "foreshore_width": 0.0,
            "D_fore": 3.0,
            "k_fore": 1.0e-6,
            "HWL": 16.0,
        },
        "priors": {
            "k_aq": {"family": "lognormal", "mean": 1.0e-4, "cov": 0.50},
            "d_70": {"family": "lognormal", "mean": 2.0e-4, "cov": 0.10},
            "D_aq": {"family": "lognormal", "mean": 3.0, "cov": 0.20},
            "D_bl": {"family": "lognormal", "mean": 3.0, "cov": 0.20},
            "k_bl": {"family": "lognormal", "mean": 1.0e-6, "cov": 0.50},
            "gamma_bl_sub": {"family": "lognormal", "mean": 6.9, "cov": 0.056},
            "C_e": {"family": "lognormal", "mean": 0.20, "cov": 0.50},
            "bounds": {"d_70": [50.0e-6, 1.0e-3]},
            "d70_interpretation": "matrix",
        },
        "correlation": {"rho_log_kaq_d70": 0.0, "coupling": "two_population"},
        "mc": {
            "n_samples": 200,
            "seed": _SEED,
            "conditioning_grid": [5.5, 6.5, 7.5],
            "sampling_scheme": "latin_hypercube",
        },
        "timestepper": {
            "integration_scheme": "forward_euler",
            "target_dt_seconds": 1800.0,
            "convergence_test": False,
            "convergence_threshold": 0.01,
            "aquifer_lag_active": False,
            "specific_storage_per_m": None,
        },
        "output": {
            "store_trajectories": False,
            "persistence_format": "hdf5",
            "results_dir": "results",
        },
        "theta_repose_deg": 37.0,
        "relative_density_insitu": 0.725,
        "alpha_exponent": -1.0 / 3.0,
    }
    data.update(overrides)
    return Config.model_validate(data)


def test_seepage_length_regeneration_is_deterministic() -> None:
    """The public seam regenerates one exact, reproducible L vector."""
    config = _stub_config(seepage_length_cov=0.2)
    first = seepage_length_samples_for_config(config)
    second = seepage_length_samples_for_config(config)
    assert first is not None and second is not None
    assert first.shape == (200,)
    np.testing.assert_array_equal(first, second)
    # Lognormal(mean = geometry.L): the sample mean sits near 30 m.
    assert abs(float(first.mean()) - 30.0) < 2.0
    # A different config seed yields a different draw.
    other = seepage_length_samples_for_config(
        _stub_config(
            seepage_length_cov=0.2,
            mc={
                "n_samples": 200,
                "seed": _SEED + 1,
                "conditioning_grid": [5.5, 6.5, 7.5],
                "sampling_scheme": "latin_hypercube",
            },
        )
    )
    assert other is not None
    assert not np.array_equal(first, other)


def test_seepage_length_regeneration_none_when_deterministic() -> None:
    """No CoV configured means L stays deterministic, exactly like the run."""
    assert seepage_length_samples_for_config(_stub_config()) is None


def test_conditioning_hydrographs_match_grid_on_stub_path() -> None:
    """Grid-ordered records with verbatim peaks and the configured dt."""
    config = _stub_config()
    records = conditioning_hydrographs_for_config(config)
    grid = list(config.mc.conditioning_grid)
    assert len(records) == len(grid)
    for record, level in zip(records, grid):
        assert record.peak == float(level)
        assert record.native_dt == 1800.0
