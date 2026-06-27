"""Tests for the top-level orchestrator (``bep_reliability_engine.run``).

Two integration deliverables, plus focused guards on the seams:

1. **Orchestration / aggregation wiring.** A full
   :func:`run_fragility_analysis` is reconstructed from its parts — theta sampled
   independently from the same config, and a reference scalar loop over
   :func:`evaluate_realization` against the *same* stub hydrographs — and the two
   ``(N, N_h)`` failure matrices, the retained ``theta_matrix`` and the raw point
   estimates are required to match bit-for-bit. This locks where theta is sampled
   (once, from config), that the stub ``peak`` is the conditioning level, and that
   per-realization flags land at ``[j, i]``.
2. **Serial == parallel equivalence.** The same run at ``n_jobs=1`` and
   ``n_jobs=2`` must produce bit-identical results — failure matrices,
   ``theta_matrix``, raw and fitted curves, and bootstrap bands — the executable
   form of the reproducibility-by-construction argument (no in-loop RNG,
   index-addressed assembly, bootstrap seeded from config in the main process).

The remaining tests pin the persistence contract (HDF5 + JSON sidecar round trip
via M9), the refuse-to-overwrite guard (and its ``overwrite=True`` escape), the
derived output-path naming, and the loud ``hydrograph_source`` stub marker.

The config is synthetic and tuned (``C_e`` mean lifted, a coarse stub ``dt``) so
both branches sit comfortably interior on the grid and the run is fast; the
*orchestration wiring* — not the upstream physics, which M2/M4/M6/M7/M8/M9 already
test — is what is under test here.
"""

from __future__ import annotations

import numpy as np
import pytest

from bep_reliability_engine import FragilityResult, run_fragility_analysis
from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import evaluate_realization
from bep_reliability_engine.run import (
    _HYDROGRAPH_SOURCE,
    _L_INI_M,
    _hydrograph_for_level,
    _resolve_output_path,
)
from bep_reliability_engine.sampling import sample_theta

# Grid and parameters tuned (see the module docstring) so both branches are
# comfortably interior: static ~0.20->0.96, transient ~0.02->0.72 across [9, 18].
_GRID = [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]
_N_SAMPLES = 300
_SEED = 12345
_STUB_DT_S = 7200.0  # coarse dt (also exercises the target_dt_seconds threading)

# Toy config for the two integration tests below (N=1000, N_h=5). The 5-level grid
# keeps both branches interior with the two-peak stub: static ~0.34->0.95,
# transient ~0.07->0.74.
_TOY_N = 1000
_TOY_GRID = [10.0, 12.0, 14.0, 16.0, 18.0]


def _make_config(
    *, n_samples: int = _N_SAMPLES, conditioning_grid=_GRID, **overrides
) -> Config:
    """Build a small, fast, fittable test :class:`Config` (overridable fields)."""
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
        "correlation": {"rho_log_kaq_d70": 0.6, "coupling": "correlated"},
        "mc": {
            "n_samples": n_samples,
            "seed": _SEED,
            "conditioning_grid": [float(x) for x in conditioning_grid],
            "sampling_scheme": "latin_hypercube",
        },
        "timestepper": {
            "integration_scheme": "forward_euler",
            "target_dt_seconds": _STUB_DT_S,
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


def _reference_failure_matrices(
    config: Config, theta_matrix: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Independent scalar reference: the matrices the orchestrator must reproduce.

    Rebuilds, per conditioning level, the hydrograph via the *same*
    :func:`_hydrograph_for_level` seam the orchestrator uses (``peak`` == the
    level), then loops :func:`evaluate_realization` over the rows of the given
    ``theta_matrix``, writing each realization's failure flags at ``[j, i]``.
    """
    geometry = config.geometry.as_evaluator_dict()
    grid = np.asarray(config.mc.conditioning_grid, dtype=np.float64)
    n_samples = theta_matrix.shape[0]
    n_levels = grid.size

    ref_stat = np.empty((n_samples, n_levels), dtype=bool)
    ref_tran = np.empty((n_samples, n_levels), dtype=bool)
    for i, level in enumerate(grid):
        hydrograph = _hydrograph_for_level(float(level), config)
        for j in range(n_samples):
            result = evaluate_realization(
                theta_matrix[j],
                hydrograph,
                geometry,
                l_ini=_L_INI_M,
                store_trajectory=False,
            )
            ref_stat[j, i] = result.failure_static
            ref_tran[j, i] = result.failure_trans
    return ref_stat, ref_tran


# ---------------------------------------------------------------------------
# (1) Orchestration / aggregation wiring
# ---------------------------------------------------------------------------


def test_orchestration_matches_reference_loop() -> None:
    """run.py reproduces an independent sample-once + scalar-loop reference.

    Locks the four wiring contracts of the orchestrator at once: theta is sampled
    once from the config (``result.theta_matrix`` equals an independent
    :func:`sample_theta` with the same arguments); each level's stub carries
    ``peak == h_i``; per-realization flags are aggregated at ``[j, i]`` (both
    ``(N, N_h)`` matrices match bit-for-bit); and the raw point estimates are the
    per-column means of those matrices. Also checks the loud stub marker and the
    exact-monotonicity both branches must have in the conditioning level.
    """
    config = _make_config()

    # Independent theta from the same config inputs (deterministic seed): this is
    # bit-identical to what the orchestrator samples, so it doubles as the
    # reference theta for the scalar loop and as the equality target.
    theta = sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    ).theta_matrix

    ref_stat, ref_tran = _reference_failure_matrices(config, theta)

    result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)

    # Theta sampled once, from config.
    np.testing.assert_array_equal(result.theta_matrix, theta)
    assert result.theta_matrix.shape == (_N_SAMPLES, 7)

    # Aggregation: both failure matrices match the reference bit-for-bit.
    assert result.failure_matrix_stat.shape == (_N_SAMPLES, len(_GRID))
    assert result.failure_matrix_tran.shape == (_N_SAMPLES, len(_GRID))
    np.testing.assert_array_equal(result.failure_matrix_stat, ref_stat)
    np.testing.assert_array_equal(result.failure_matrix_tran, ref_tran)

    # Raw point estimates are the per-column failure fractions of the matrices.
    np.testing.assert_array_equal(result.P_f_static_raw, ref_stat.mean(axis=0))
    np.testing.assert_array_equal(result.P_f_trans_raw, ref_tran.mean(axis=0))

    # Per-realization failure is monotone in the level (a failed realization
    # stays failed as h rises), so each column fraction is exactly non-decreasing.
    assert np.all(np.diff(result.P_f_static_raw) >= 0.0)
    assert np.all(np.diff(result.P_f_trans_raw) >= 0.0)

    # Loud provenance: the run is a synthetic stub, marked as such.
    assert result.metadata["hydrograph_source"] == _HYDROGRAPH_SOURCE


# ---------------------------------------------------------------------------
# (2) Serial == parallel equivalence (reproducibility by construction)
# ---------------------------------------------------------------------------


def test_serial_parallel_equivalence() -> None:
    """``n_jobs=1`` and ``n_jobs=2`` give bit-identical results.

    The executable reproducibility-by-construction claim: all RNG is front-loaded
    into the single prior draw, the per-(level, realization) evaluation is pure
    and deterministic, the stub is deterministic, aggregation is index-addressed,
    and the bootstrap is seeded from the config in the main process — so worker
    count cannot change anything, from the raw matrices to the bootstrap bands.
    """
    config = _make_config()

    serial = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)
    parallel = run_fragility_analysis(config, n_jobs=2, progress=False, persist=False)

    # Retained raw data.
    np.testing.assert_array_equal(serial.theta_matrix, parallel.theta_matrix)
    np.testing.assert_array_equal(
        serial.failure_matrix_stat, parallel.failure_matrix_stat
    )
    np.testing.assert_array_equal(
        serial.failure_matrix_tran, parallel.failure_matrix_tran
    )

    # Raw point estimates.
    np.testing.assert_array_equal(serial.P_f_static_raw, parallel.P_f_static_raw)
    np.testing.assert_array_equal(serial.P_f_trans_raw, parallel.P_f_trans_raw)

    # Fitted curves.
    assert serial.P_f_static_fit.mu == parallel.P_f_static_fit.mu
    assert serial.P_f_static_fit.sigma == parallel.P_f_static_fit.sigma
    assert serial.P_f_trans_fit.mu == parallel.P_f_trans_fit.mu
    assert serial.P_f_trans_fit.sigma == parallel.P_f_trans_fit.sigma

    # Bootstrap bands (seeded from config, run in the main process): identical.
    for key in ("static", "transient"):
        lo_s, hi_s = serial.bootstrap_bands[key]
        lo_p, hi_p = parallel.bootstrap_bands[key]
        np.testing.assert_array_equal(np.asarray(lo_s), np.asarray(lo_p))
        np.testing.assert_array_equal(np.asarray(hi_s), np.asarray(hi_p))


# ---------------------------------------------------------------------------
# (3) Persistence: HDF5 + JSON sidecar round trip
# ---------------------------------------------------------------------------


def test_persistence_round_trip(tmp_path) -> None:
    """``persist=True`` writes the HDF5 + JSON pair that M9 reloads exactly."""
    config = _make_config()
    out = tmp_path / "test_xs_historical.h5"

    result = run_fragility_analysis(
        config, n_jobs=1, progress=False, output_path=out, persist=True
    )

    assert out.exists()
    assert out.with_suffix(".json").exists()

    loaded = FragilityResult.load(out)
    np.testing.assert_array_equal(
        loaded.failure_matrix_stat, result.failure_matrix_stat
    )
    np.testing.assert_array_equal(
        loaded.failure_matrix_tran, result.failure_matrix_tran
    )
    np.testing.assert_array_equal(loaded.theta_matrix, result.theta_matrix)
    assert loaded.metadata["hydrograph_source"] == _HYDROGRAPH_SOURCE
    # The deferred bootstrap settings are recorded in metadata (decision log).
    assert loaded.metadata["bootstrap"]["seed"] == config.mc.seed
    # The full metadata round-trips bit-for-bit (the M9 contract applied to a real
    # run.py result): _build_metadata canonicalizes to JSON-native types, so the
    # sampling-block ``bounds`` (built as tuples) survive as the lists JSON yields
    # on reload, rather than breaking this equality.
    assert loaded.metadata == result.metadata


def test_persist_false_writes_nothing(tmp_path) -> None:
    """``persist=False`` returns the result without touching the filesystem."""
    config = _make_config(output={"results_dir": str(tmp_path)})
    result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)
    assert isinstance(result, FragilityResult)
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# (4) Output path: derivation and the refuse-to-overwrite guard
# ---------------------------------------------------------------------------


def test_default_output_path_is_derived_from_config(tmp_path) -> None:
    """With no explicit path, the run writes to results_dir/{id}_{scenario}.h5."""
    config = _make_config(output={"results_dir": str(tmp_path)})
    run_fragility_analysis(config, n_jobs=1, progress=False, persist=True)
    assert (tmp_path / "test_xs_historical.h5").exists()


def test_resolve_output_path_sanitizes_plus4k_scenario() -> None:
    """The derived stem maps the '+4K' scenario to a filesystem-safe 'plus4K'."""
    config = _make_config(scenario="+4K", output={"results_dir": "out"})
    path = _resolve_output_path(config, None)
    assert path.name == "test_xs_plus4K.h5"


def test_refuses_to_overwrite_existing_result(tmp_path) -> None:
    """An existing result (or its sidecar) is never silently overwritten.

    The guard fires *before* the sweep (fail fast); ``overwrite=True`` is the
    explicit escape and replaces the file.
    """
    config = _make_config()
    out = tmp_path / "run.h5"

    run_fragility_analysis(config, n_jobs=1, progress=False, output_path=out)
    assert out.exists()

    # Refuse on the existing HDF5 file.
    with pytest.raises(FileExistsError):
        run_fragility_analysis(config, n_jobs=1, progress=False, output_path=out)

    # The guard also covers a stray sidecar with the HDF5 already removed.
    out.unlink()
    assert out.with_suffix(".json").exists()
    with pytest.raises(FileExistsError):
        run_fragility_analysis(config, n_jobs=1, progress=False, output_path=out)

    # overwrite=True is the explicit escape hatch and succeeds.
    result = run_fragility_analysis(
        config, n_jobs=1, progress=False, output_path=out, overwrite=True
    )
    assert isinstance(result, FragilityResult)
    assert out.exists()


# ---------------------------------------------------------------------------
# (5) Toy end-to-end integration: N=1000, N_h=5, the two-peak stub
# ---------------------------------------------------------------------------


def test_toy_run_produces_well_formed_fragility_result() -> None:
    """A toy run (N=1000, N_h=5, two-peak stub) completes and yields a usable result.

    Asserts the run completes without error and returns a :class:`FragilityResult`
    whose two failure matrices are correctly shaped ``(1000, 5)`` bool and
    genuinely populated (a mix of pass and fail, not all-False / all-True), and
    whose two fitted lognormal fragility curves are strictly monotone increasing
    in the conditioning head.
    """
    config = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)

    result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)

    assert isinstance(result, FragilityResult)

    # Both failure matrices: correctly shaped, bool, and genuinely populated
    # (some realizations fail and some survive at the engine — not degenerate).
    for failure_matrix in (result.failure_matrix_stat, result.failure_matrix_tran):
        assert failure_matrix.shape == (_TOY_N, len(_TOY_GRID))
        assert failure_matrix.dtype == np.bool_
        assert failure_matrix.any()
        assert not failure_matrix.all()

    # The retained prior matrix matches the run dimensions.
    assert result.theta_matrix.shape == (_TOY_N, 7)

    # The fitted fragility curves are strictly increasing in head (a lognormal
    # fragility with sigma > 0 is monotone by construction; check it explicitly
    # on the grid for both branches).
    heads = np.asarray(_TOY_GRID, dtype=np.float64)
    for fit in (result.P_f_static_fit, result.P_f_trans_fit):
        assert fit.sigma > 0.0
        curve = fit.probability_of_failure(heads)
        assert np.all(np.diff(curve) > 0.0)


def test_serial_parallel_failure_matrices_bit_identical() -> None:
    """Serial and parallel runs give bit-for-bit identical failure matrices.

    The focused reproducibility check on the toy config: running the same analysis
    at ``n_jobs=1`` and ``n_jobs=2`` must yield element-for-element identical
    static and transient failure matrices, regardless of worker count — all RNG is
    in the single prior draw, the per-(level, realization) evaluation and the
    two-peak stub are deterministic, and aggregation is index-addressed.
    """
    config = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)

    serial = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)
    parallel = run_fragility_analysis(config, n_jobs=2, progress=False, persist=False)

    np.testing.assert_array_equal(
        serial.failure_matrix_stat, parallel.failure_matrix_stat
    )
    np.testing.assert_array_equal(
        serial.failure_matrix_tran, parallel.failure_matrix_tran
    )
