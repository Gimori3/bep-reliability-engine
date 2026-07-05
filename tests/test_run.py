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

import json
import warnings

import h5py
import numpy as np
import pytest

from bep_reliability_engine import FragilityResult, run_fragility_analysis
from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import evaluate_realization
from bep_reliability_engine.run import (
    _L_INI_M,
    _SOURCE_SYNTHETIC,
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
    assert result.metadata["hydrograph_source"] == _SOURCE_SYNTHETIC


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
    assert loaded.metadata["hydrograph_source"] == _SOURCE_SYNTHETIC
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
# (4a) ADR-0006 (amended 2026-07-05) leakage-geometry record. The former
#      L/lambda_in "validity" alarm was a category error — L is the exact
#      linear USACE-L2 term and carries no smallness condition — so the
#      monitor is repurposed: descriptive geometry of the r_e denominator,
#      recorded per run, gating nothing and warning about nothing.
# ---------------------------------------------------------------------------


def _independent_leakage_arrays(config):
    """Recompute lambda_in / lambda_out_eff from the config-determined draw."""
    from bep_reliability_engine.hydraulics import (
        leakage_length_in,
        leakage_length_out,
    )

    sample = sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    )
    lambda_in = leakage_length_in(
        sample.column("k_aq"),
        sample.column("D_aq"),
        sample.column("D_bl"),
        sample.column("k_bl"),
    )
    lambda_out_eff = leakage_length_out(
        sample.column("k_aq"),
        sample.column("D_aq"),
        config.geometry.D_fore,
        config.geometry.k_fore,
        config.geometry.foreshore_width,
    )
    return lambda_in, lambda_out_eff


def test_leakage_geometry_recorded_without_warning() -> None:
    """The repurposed monitor records geometry and no longer false-alarms.

    The toy prior has median lambda_in ~ 30 m against L = 30 m — exactly the
    configuration the retired L/lambda_in alarm misread as '100% invalid'.
    Under the amended ADR-0006 the run must complete with NO Mazure warning
    (the ratio form is exact in L), and ``metadata['leakage_geometry']`` must
    carry the descriptive record: median leakage lengths, the foreland tanh
    credit, the r_e denominator shares, the descriptive L/lambda_in, and the
    hinterland semi-infinite assumption with its 3*lambda_in threshold — all
    matching an independent recomputation from the same config-determined
    sample.
    """
    config = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)

    block = result.metadata["leakage_geometry"]
    lambda_in, lambda_out_eff = _independent_leakage_arrays(config)
    length = config.geometry.L
    denominator = lambda_out_eff + length + lambda_in

    assert block["median_lambda_in_m"] == pytest.approx(float(np.median(lambda_in)))
    assert block["median_lambda_out_eff_m"] == pytest.approx(
        float(np.median(lambda_out_eff))
    )
    # Toy geometry has B_f = 0: no foreland credit, zero foreland share.
    assert block["foreshore_width_m"] == pytest.approx(0.0)
    assert block["median_foreland_tanh_credit"] == pytest.approx(0.0)
    assert block["denominator_share_foreland_median"] == pytest.approx(0.0)
    assert block["denominator_share_base_L_median"] == pytest.approx(
        float(np.median(length / denominator))
    )
    assert block["denominator_share_hinterland_median"] == pytest.approx(
        float(np.median(lambda_in / denominator))
    )
    # Descriptive only — present, ~1.0 for this prior, and gating nothing.
    assert block["median_L_over_lambda_in"] == pytest.approx(
        float(np.median(length / lambda_in))
    )
    assert block["median_L_over_lambda_in"] > 0.9
    # The hinterland semi-infinite assumption is surfaced with its threshold,
    # auto-generating the numbers the L3 site resolution needs.
    assert block["hinterland_assumption"] == "semi_infinite"
    assert block["hinterland_semi_infinite_threshold_m"] == pytest.approx(
        3.0 * float(np.median(lambda_in))
    )

    # ADR-0012 (accepted 2026-07-03): runs carry the empirical-rho status.
    assert (
        result.metadata["correlation_rho_k_d70_status"]
        == "empirical_two_population_adr_0012"
    )


def test_leakage_geometry_pairs_stochastic_L_rowwise() -> None:
    """With stochastic L the record pairs L_j with theta_j row-for-row."""
    from bep_reliability_engine.run import _sample_seepage_length_or_none

    config = _make_config(
        n_samples=_TOY_N, conditioning_grid=_TOY_GRID, seepage_length_cov=0.2
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)

    lambda_in, lambda_out_eff = _independent_leakage_arrays(config)
    seepage = _sample_seepage_length_or_none(config)
    assert seepage is not None
    denominator = lambda_out_eff + seepage + lambda_in

    block = result.metadata["leakage_geometry"]
    assert block["median_L_over_lambda_in"] == pytest.approx(
        float(np.median(seepage / lambda_in))
    )
    assert block["denominator_share_base_L_median"] == pytest.approx(
        float(np.median(seepage / denominator))
    )


# ---------------------------------------------------------------------------
# (4a-ii) ADR-0025: foreland_treatment threading (blanketed baseline; the
#         open-entry end is a one-flag, on-demand sensitivity)
# ---------------------------------------------------------------------------


def test_foreland_treatment_threaded_and_recorded() -> None:
    """``config.foreland_treatment`` reaches M8 and is recorded in metadata.

    A wide-foreshore toy geometry gives the blanketed baseline a saturated
    tanh entry length; the ``open_entry`` sensitivity removes it (USACE
    x1 = 0), so every realization sees a strictly higher driving head at
    every level: the open run's failure sets must be supersets of the
    baseline's (strictly larger somewhere), both treatments must be stamped
    into metadata, and the leakage-geometry record must cohere with the
    physics actually run (zero foreland entry length under open_entry).
    """
    geometry = {
        "L": 30.0,
        "z_toe": 2.0,
        "foreshore_width": 200.0,
        "D_fore": 3.0,
        "k_fore": 1.0e-6,
        "HWL": 16.0,
    }
    grid = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0]
    base_cfg = _make_config(n_samples=400, conditioning_grid=grid, geometry=geometry)
    open_cfg = _make_config(
        n_samples=400,
        conditioning_grid=grid,
        geometry=geometry,
        foreland_treatment="open_entry",
    )

    base = run_fragility_analysis(base_cfg, n_jobs=1, progress=False, persist=False)
    opened = run_fragility_analysis(open_cfg, n_jobs=1, progress=False, persist=False)

    assert base.metadata["foreland_treatment"] == "blanketed_tanh"
    assert opened.metadata["foreland_treatment"] == "open_entry"

    # Monotonicity: a strictly higher r_e per realization can only add
    # failures, never remove them — on both branches.
    assert np.all(opened.failure_matrix_stat >= base.failure_matrix_stat)
    assert opened.failure_matrix_stat.sum() > base.failure_matrix_stat.sum()
    assert np.all(opened.failure_matrix_tran >= base.failure_matrix_tran)

    # The leakage-geometry record reflects the physics actually run.
    assert base.metadata["leakage_geometry"]["median_lambda_out_eff_m"] > 0.0
    assert opened.metadata["leakage_geometry"]["median_lambda_out_eff_m"] == 0.0
    assert opened.metadata["leakage_geometry"]["median_foreland_tanh_credit"] == 0.0


# ---------------------------------------------------------------------------
# (4b) Raw-payload crash recovery: a fit failure never destroys a completed
#      sweep (health-assessment fix 1, 2026-07-03)
# ---------------------------------------------------------------------------


def test_fit_failure_preserves_raw_payload(tmp_path, monkeypatch) -> None:
    """An M9 assembly failure after the sweep leaves the raw payload on disk.

    The sweep is the expensive part; fitting is cheap and can fail on a
    tail-dominated grid (degenerate probit point sets). The orchestrator must
    therefore persist the raw failure matrices *before* any fitting, so the
    completed sweep survives: the ``.raw.h5`` recovery file (plus its JSON
    sidecar) must exist and carry the exact matrices an unbroken run produces,
    while the final result file is never written.
    """
    config = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)
    out = tmp_path / "res.h5"

    # Reference matrices from an unbroken run of the same config (same seed
    # => bit-identical sweep).
    reference = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)

    def _boom(*args, **kwargs):
        raise ValueError("synthetic fit failure")

    monkeypatch.setattr("bep_reliability_engine.run.assemble_fragility", _boom)
    with pytest.raises(ValueError, match="synthetic fit failure"):
        run_fragility_analysis(config, n_jobs=1, progress=False, output_path=out)

    raw = tmp_path / "res.raw.h5"
    sidecar = tmp_path / "res.raw.json"
    assert raw.exists(), "raw recovery payload missing after fit failure"
    assert sidecar.exists(), "raw recovery JSON sidecar missing after fit failure"
    assert not out.exists()
    assert not out.with_suffix(".json").exists()

    with h5py.File(raw, "r") as handle:
        np.testing.assert_array_equal(
            handle["failure_matrix_static"][:].astype(bool),
            reference.failure_matrix_stat,
        )
        np.testing.assert_array_equal(
            handle["failure_matrix_trans"][:].astype(bool),
            reference.failure_matrix_tran,
        )
        np.testing.assert_array_equal(handle["theta_matrix"][:], reference.theta_matrix)
        np.testing.assert_array_equal(
            handle["conditioning_grid"][:],
            np.asarray(config.mc.conditioning_grid, dtype=np.float64),
        )
        names = [str(name) for name in handle["param_names"].asstr()[:]]
        assert names == reference.param_names

    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    assert metadata["config_hash"] == config.config_hash()


def test_raw_payload_removed_after_successful_persist(tmp_path) -> None:
    """On success the recovery payload is superseded by the final result.

    The ``.raw.h5`` file exists only to survive a fitting crash; once the full
    ``FragilityResult`` (fits, bands, raw arrays) is written, the recovery pair
    is removed so the results directory holds exactly one artifact per run.
    """
    config = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)
    out = tmp_path / "res.h5"

    run_fragility_analysis(config, n_jobs=1, progress=False, output_path=out)

    assert out.exists()
    assert out.with_suffix(".json").exists()
    assert not (tmp_path / "res.raw.h5").exists()
    assert not (tmp_path / "res.raw.json").exists()


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


# ---------------------------------------------------------------------------
# (6) Stochastic seepage length L wiring (review item #3)
# ---------------------------------------------------------------------------


def test_stochastic_seepage_length_run_wiring() -> None:
    """``seepage_length_cov`` makes run.py draw a per-realization L (review #3).

    Locks the orchestrator wiring of the stochastic seepage length: with the CoV
    set the run records it in metadata, stays reproducible across worker counts
    (the L draw is front-loaded like theta), and produces failure matrices that
    differ from the deterministic-L run (so L genuinely moved). With the CoV
    unset, metadata reports deterministic L.
    """
    base = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)
    stoch = _make_config(
        n_samples=_TOY_N, conditioning_grid=_TOY_GRID, seepage_length_cov=0.20
    )

    det_result = run_fragility_analysis(base, n_jobs=1, progress=False, persist=False)
    serial = run_fragility_analysis(stoch, n_jobs=1, progress=False, persist=False)
    parallel = run_fragility_analysis(stoch, n_jobs=2, progress=False, persist=False)

    # Metadata records the stochastic-L decision both ways.
    assert det_result.metadata["seepage_length"]["stochastic"] is False
    assert serial.metadata["seepage_length"]["stochastic"] is True
    assert serial.metadata["seepage_length"]["cov"] == pytest.approx(0.20)
    assert serial.metadata["seepage_length"]["mean_m"] == pytest.approx(
        stoch.geometry.L
    )

    # Reproducible across worker counts (L draw front-loaded in the main process).
    np.testing.assert_array_equal(
        serial.failure_matrix_tran, parallel.failure_matrix_tran
    )
    np.testing.assert_array_equal(
        serial.failure_matrix_stat, parallel.failure_matrix_stat
    )

    # Stochastic L genuinely changes the outcome vs deterministic geometry.L.
    assert not np.array_equal(
        serial.failure_matrix_tran, det_result.failure_matrix_tran
    )


# ---------------------------------------------------------------------------
# (7) Asymmetric-alpha dimensional-bias decomposition wiring (ADR-0017)
# ---------------------------------------------------------------------------


def test_dimensional_decomposition_run_wiring() -> None:
    """``alpha_exponent_transient`` runs the decomposition through run.py (ADR-0017).

    Locks the run-level wiring: with the transient-only override set, run.py
    records it in metadata, leaves the STATIC failure matrix bit-identical to the
    baseline (the static comparator keeps -1/3 — the decomposition does not shift
    it), and shifts the TRANSIENT matrix toward more failures (the lower 3D
    transient H_c lowers H_eq and speeds progression).
    """
    base = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)
    decomp = _make_config(
        n_samples=_TOY_N,
        conditioning_grid=_TOY_GRID,
        alpha_exponent_transient=-1.0 / 2.0,
    )

    base_res = run_fragility_analysis(base, n_jobs=1, progress=False, persist=False)
    decomp_res = run_fragility_analysis(decomp, n_jobs=1, progress=False, persist=False)

    # Metadata records the decomposition state both ways.
    assert base_res.metadata["alpha_exponent_transient"] is None
    assert base_res.metadata["dimensional_decomposition_active"] is False
    assert decomp_res.metadata["alpha_exponent_transient"] == pytest.approx(-0.5)
    assert decomp_res.metadata["dimensional_decomposition_active"] is True

    # The static branch is untouched (the whole point of the asymmetric form).
    np.testing.assert_array_equal(
        decomp_res.failure_matrix_stat, base_res.failure_matrix_stat
    )
    # The transient branch shifts toward more failures (lower 3D transient H_c).
    assert not np.array_equal(
        decomp_res.failure_matrix_tran, base_res.failure_matrix_tran
    )
    assert decomp_res.failure_matrix_tran.sum() > base_res.failure_matrix_tran.sum()


# ---------------------------------------------------------------------------
# (8) Real-hydrograph path: canonical d4PDF shape (G1), determinism (G4),
#     provenance metadata (G5), and the fail-fast MSL datum guard (G2)
# ---------------------------------------------------------------------------
# Hermetic: a fake ADR-0020 data drop (rating CSV + band workbook) is written
# to tmp_path, so the real path runs end-to-end without the untracked d4PDF
# files. Rating a=1, b=-30 => h = sqrt(Q) + 30 (exact stages); base flow Q=4
# => h_base = 32.0 m "MSL". Values tuned so both branches are interior on the
# grid (static ~0.02->1.0, transient ~0->0.98 across [33.5, 40.0]).

_REAL_GRID = [33.5, 34.5, 35.5, 36.5, 37.5, 38.5, 40.0]
_REAL_H_BASE = 32.0
_REAL_Z_TOE = 33.0

# Compound (two-peak) discharge for the production event; single-peak for the
# recorded alternate. 48 hourly samples each.
_Q_COMPOUND = np.concatenate(
    [
        np.full(4, 4.0),
        np.linspace(4.0, 49.0, 6),
        np.full(4, 49.0),
        np.linspace(49.0, 9.0, 4),
        np.full(4, 9.0),
        np.linspace(9.0, 100.0, 6),
        np.full(8, 100.0),
        np.linspace(100.0, 4.0, 8),
        np.full(4, 4.0),
    ]
)
_Q_SINGLE = np.concatenate(
    [
        np.full(10, 4.0),
        np.linspace(4.0, 100.0, 10),
        np.full(8, 100.0),
        np.linspace(100.0, 4.0, 12),
        np.full(8, 4.0),
    ]
)


@pytest.fixture()
def real_data_root(tmp_path):
    """Write the fake ADR-0020 drop and return its root."""
    from openpyxl import Workbook

    rating_dir = tmp_path / "rating_curves"
    rating_dir.mkdir()
    header = "River,KP,HQ_ａ,HQ_ｂ"  # full-width a/b (ADR-0019 S5)
    (rating_dir / "HQrelation_TokachiRiv_2017.csv").write_bytes(
        (header + "\r\nTokachi,57.4,1.0,-30.0\r\n").encode("shift_jis")
    )

    hydro_dir = tmp_path / "hydrographs"
    hydro_dir.mkdir()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "QT"
    sheet.append(["Time", "HPB_m064_1987", "HPB_m067_1978"])
    for hour in range(_Q_COMPOUND.size):
        sheet.append([hour + 1, float(_Q_COMPOUND[hour]), float(_Q_SINGLE[hour])])
    workbook.save(hydro_dir / "Hydro Data, HPB, Tokachi Riv. KP056.20-KP061.80.xlsx")
    return tmp_path


def _make_real_config(data_root, **overrides) -> Config:
    """A config on the real path: MSL-ish geometry/grid + hydrograph_source."""
    geometry = overrides.pop(
        "geometry",
        {
            "L": 10.0,
            "z_toe": _REAL_Z_TOE,
            "foreshore_width": 0.0,
            "D_fore": 3.0,
            "k_fore": 1.0e-6,
            "HWL": 36.0,
        },
    )
    return _make_config(
        conditioning_grid=_REAL_GRID,
        geometry=geometry,
        # Native hourly resolution drives the timestep (ADR-0013/0019 S6).
        timestepper={
            "integration_scheme": "forward_euler",
            "target_dt_seconds": None,
            "convergence_test": False,
            "convergence_threshold": 0.01,
            "aquifer_lag_active": False,
            "specific_storage_per_m": None,
        },
        hydrograph_source={
            "data_root": str(data_root),
            "river": "Tokachi",
            "kp": 57.4,
            "canonical_event_ids": ["HPB_m064_1987", "HPB_m067_1978"],
        },
        **overrides,
    )


def test_real_path_matches_reference_scalar_loop(real_data_root) -> None:
    """The canonical-shape sweep reproduces an independent scalar reference.

    The real-path twin of ``test_orchestration_matches_reference_loop``:
    the reference rebuilds each level's record through the same
    ``load_canonical_shape`` + ``conditioning_record_for_level`` seam and
    loops the scalar ``evaluate_realization`` — locking the shared-sample
    contract, ``peak == h_i`` verbatim, the h_base trough floor, and the
    index-addressed aggregation, end to end on the real path.
    """
    from bep_reliability_engine.hydrographs import (
        conditioning_record_for_level,
        load_canonical_shape,
    )

    config = _make_real_config(real_data_root)
    canonical = load_canonical_shape(
        real_data_root, river="Tokachi", kp=57.4, event_id="HPB_m064_1987"
    )
    assert canonical.h_base_m == pytest.approx(_REAL_H_BASE)

    theta = sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    ).theta_matrix

    geometry = config.geometry.as_evaluator_dict()
    grid = np.asarray(config.mc.conditioning_grid)
    ref_stat = np.empty((theta.shape[0], grid.size), dtype=bool)
    ref_tran = np.empty((theta.shape[0], grid.size), dtype=bool)
    for i, level in enumerate(grid):
        record = conditioning_record_for_level(
            canonical, float(level), scenario=config.scenario
        )
        assert record.peak == float(level)  # verbatim conditioning anchor
        assert float(record.h.min()) >= _REAL_H_BASE  # trough floor pinned
        for j in range(theta.shape[0]):
            r = evaluate_realization(
                theta[j], record, geometry, l_ini=_L_INI_M, store_trajectory=False
            )
            ref_stat[j, i] = r.failure_static
            ref_tran[j, i] = r.failure_trans

    result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)
    np.testing.assert_array_equal(result.failure_matrix_stat, ref_stat)
    np.testing.assert_array_equal(result.failure_matrix_tran, ref_tran)
    # Non-degenerate: both branches genuinely transition across the grid.
    assert 0.0 < result.failure_matrix_stat.mean() < 1.0
    assert 0.0 < result.failure_matrix_tran.mean() < 1.0


def test_real_path_njobs_invariance(real_data_root) -> None:
    """Parallel == serial on the real path (gap G4 determinism test).

    The canonical shape is loaded once in the main process and the per-level
    scaling is pure, so ``n_jobs`` must not change a single bit: failure
    matrices, raw and fitted curves, and bootstrap bands all match.
    """
    config = _make_real_config(real_data_root)
    serial = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)
    parallel = run_fragility_analysis(config, n_jobs=2, progress=False, persist=False)

    np.testing.assert_array_equal(
        serial.failure_matrix_stat, parallel.failure_matrix_stat
    )
    np.testing.assert_array_equal(
        serial.failure_matrix_tran, parallel.failure_matrix_tran
    )
    np.testing.assert_array_equal(serial.theta_matrix, parallel.theta_matrix)
    np.testing.assert_array_equal(serial.P_f_static_raw, parallel.P_f_static_raw)
    np.testing.assert_array_equal(serial.P_f_trans_raw, parallel.P_f_trans_raw)
    assert serial.P_f_static_fit == parallel.P_f_static_fit
    assert serial.P_f_trans_fit == parallel.P_f_trans_fit
    for curve in serial.bootstrap_bands:
        np.testing.assert_array_equal(
            serial.bootstrap_bands[curve][0], parallel.bootstrap_bands[curve][0]
        )
        np.testing.assert_array_equal(
            serial.bootstrap_bands[curve][1], parallel.bootstrap_bands[curve][1]
        )


def test_real_path_metadata_provenance(real_data_root) -> None:
    """Real-path metadata carries the loud marker + full shape provenance (G5).

    ``hydrograph_source`` flips to ``'d4pdf_scaled_canonical'`` and the
    ``hydrograph`` block records the shape event, the ordered canonical list,
    h_base, and the ADR-0019 member provenance — while ``scenario`` stays the
    RUN identity (the config's), with the shape source's own tags inside the
    provenance block.
    """
    config = _make_real_config(real_data_root)
    result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)

    assert result.metadata["hydrograph_source"] == "d4pdf_scaled_canonical"
    assert result.metadata["scenario"] == "historical"  # run identity

    block = result.metadata["hydrograph"]
    assert block["shape_event_id"] == "HPB_m064_1987"
    assert block["canonical_event_ids"] == ["HPB_m064_1987", "HPB_m067_1978"]
    assert block["h_base_m_msl"] == pytest.approx(_REAL_H_BASE)
    assert block["source_peak_stage_m_msl"] == pytest.approx(40.0)
    assert block["native_dt_s"] == 3600.0
    prov = block["provenance"]
    assert prov["experiment"] == "HPB"
    assert prov["member_id"] == "m064"
    assert prov["year"] == 1987
    assert prov["kp"] == pytest.approx(57.4)
    assert prov["rating_csv"] == "HQrelation_TokachiRiv_2017.csv"
    assert prov["band_workbook"].endswith(".xlsx")
    assert "discharge_proxied_from" not in prov  # KP 57.4 has own coverage

    # The stub marker and the real marker are mutually exclusive.
    assert result.metadata["hydrograph_source"] != _SOURCE_SYNTHETIC


def test_real_path_datum_guard_fails_fast(real_data_root) -> None:
    """A provisional z_toe = 0.0 on the real path raises BEFORE the sweep (G2).

    The run-level wiring of ``validate_datum_consistency``: MSL stages against
    the retired placeholder must refuse loudly at load time, not produce ~35 m
    heads for hours.
    """
    config = _make_real_config(
        real_data_root,
        geometry={
            "L": 10.0,
            "z_toe": 0.0,  # the retired provisional placeholder
            "foreshore_width": 0.0,
            "D_fore": 3.0,
            "k_fore": 1.0e-6,
            "HWL": 36.0,
        },
    )
    with pytest.raises(ValueError, match="z_toe"):
        run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)


def test_stub_path_still_available_without_source_block() -> None:
    """A config without hydrograph_source keeps the marked stub path (ADR-0020).

    The block is optional; its absence selects the synthetic stub and the
    metadata stays loudly marked, with no hydrograph provenance block.
    """
    config = _make_config(n_samples=_TOY_N, conditioning_grid=_TOY_GRID)
    assert config.hydrograph_source is None
    result = run_fragility_analysis(config, n_jobs=1, progress=False, persist=False)
    assert result.metadata["hydrograph_source"] == _SOURCE_SYNTHETIC
    assert result.metadata["hydrograph"] is None
