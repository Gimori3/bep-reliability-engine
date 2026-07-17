"""Tests for Stage 6.6: the ADR-0041 end-factor hook and the ADR-0040 ladder.

Fast, stub-based (the synthetic two-peak record path; no d4PDF data needed):
the ladder is exercised end to end on a small Config mirroring the
``test_run.py`` stub, and the physics invariants of ADR-0040 (structural
nestings, telescoping ladders, the analytic sustained-peak limit, the
bit-identity of C0/C4b with the M8 production flags) are pinned directly.
"""

from __future__ import annotations

import numpy as np
import pytest

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import (
    evaluate_batch,
    evaluate_batch_diagnostics,
)
from bep_reliability_engine.gap_decomposition import (
    COMPARATOR_ORDER,
    ENGINE_LADDER_STEPS,
    PHYSICS_LADDER_STEPS,
    GapDecompositionResult,
    bootstrap_comparator_means,
    component_table,
    delta_ci,
    prepare_config,
    run_comparator_ladder,
    static_pair_shapley,
    sustained_duration_ladder,
    sustained_peak_record,
)
from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.progression import (
    EQUILIBRIUM_END_FACTOR,
    equilibrium_head,
    integrate_progression,
)
from bep_reliability_engine.run import conditioning_hydrographs_for_config
from bep_reliability_engine.sampling import sample_theta

_SEED = 20260626
_N = 400
_GRID = (6.0, 8.0, 10.0, 12.0, 14.0)
_DT_S = 900.0


def _make_config(
    *, n_samples: int = _N, conditioning_grid=_GRID, **overrides
) -> Config:
    """Small, fast stub Config (mirrors tests/test_run.py; stub hydrograph path)."""
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
            "target_dt_seconds": _DT_S,
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
        "seepage_length_cov": 0.2,
    }
    data.update(overrides)
    return Config(**data)


def _theta_for(config: Config) -> np.ndarray:
    return sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    ).theta_matrix


# ---------------------------------------------------------------------------
# ADR-0041: the equilibrium_end_factor override
# ---------------------------------------------------------------------------


def test_equilibrium_head_end_factor_default_bit_identical() -> None:
    """None and an explicit 0.9 reproduce the published curve bit for bit."""
    lengths = np.linspace(0.0, 30.0, 121)
    base = equilibrium_head(lengths, 2.5, 6.0, 30.0)
    assert np.array_equal(
        base, equilibrium_head(lengths, 2.5, 6.0, 30.0, equilibrium_end_factor=None)
    )
    assert np.array_equal(
        base,
        equilibrium_head(
            lengths, 2.5, 6.0, 30.0, equilibrium_end_factor=EQUILIBRIUM_END_FACTOR
        ),
    )


def test_equilibrium_head_end_factor_one_flattens_descending_branch() -> None:
    """End factor 1.0 pins H_eq = H_c beyond l_c and leaves the rising branch."""
    h_c, l_c, length = 2.5, 6.0, 30.0
    lengths = np.linspace(0.0, length, 121)
    flat = equilibrium_head(lengths, h_c, l_c, length, equilibrium_end_factor=1.0)
    rising = lengths < l_c
    assert np.array_equal(
        flat[rising], equilibrium_head(lengths, h_c, l_c, length)[rising]
    )
    np.testing.assert_allclose(flat[~rising], h_c, rtol=0.0, atol=1e-12)


def test_integrate_progression_end_factor_default_bit_identical() -> None:
    """The timestepper with None / explicit 0.9 equals the unoverridden run."""
    rng = np.random.default_rng(7)
    h = (
        2.0
        + 3.0 * np.abs(np.sin(np.linspace(0.0, 3.0, 200)))
        + rng.normal(0, 0.05, 200)
    )
    kwargs = dict(
        c_e=0.05,
        k_aq_mps=3e-4,
        d_bl_m=0.5,
        gamma_bl_sub_knpm3=6.9,
        h_c_m=1.2,
        l_c_m=6.0,
        seepage_length_m=30.0,
    )
    base = integrate_progression(h, 600.0, InstantaneousHead(0.8, 2.0), 2.0, **kwargs)
    for factor in (None, EQUILIBRIUM_END_FACTOR):
        again = integrate_progression(
            h,
            600.0,
            InstantaneousHead(0.8, 2.0),
            2.0,
            equilibrium_end_factor=factor,
            **kwargs,
        )
        assert np.array_equal(base.l_final_m, again.l_final_m)


def test_end_factor_one_never_increases_failures() -> None:
    """A higher equilibrium barrier cannot add transient failures (stub run)."""
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base_static, base_trans = evaluate_batch(theta, record, geometry)
    _, flat_trans = evaluate_batch(theta, record, geometry, equilibrium_end_factor=1.0)
    assert not np.any(flat_trans & ~base_trans)
    # and the static branch is untouched by construction
    flat_static, _ = evaluate_batch(theta, record, geometry, equilibrium_end_factor=1.0)
    assert np.array_equal(base_static, flat_static)


def test_end_factor_refused_on_numba_backend() -> None:
    """ADR-0041: the override is numpy-only; numba raises before any work."""
    config = _make_config(n_samples=8)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[0]
    with pytest.raises(ValueError, match="numpy-backend only"):
        evaluate_batch_diagnostics(
            theta,
            record,
            geometry,
            progression_backend="numba",
            equilibrium_end_factor=1.0,
        )


# ---------------------------------------------------------------------------
# ADR-0040: sustained record, ladder invariants, statistics, persistence
# ---------------------------------------------------------------------------


def test_sustained_peak_record_shape_and_peak() -> None:
    record = sustained_peak_record(12.5, dt_s=225.0, n_steps=6)
    assert record.peak == 12.5
    assert record.native_dt == 225.0
    assert np.array_equal(record.h, np.full(6, 12.5))
    assert record.provenance["source"] == "stage6_6_sustained_peak"
    with pytest.raises(ValueError):
        sustained_peak_record(12.5, dt_s=225.0, n_steps=1)


def test_prepare_config_grid_union_and_n_override() -> None:
    config = _make_config()
    modified = prepare_config(config, n_samples=99, extra_levels=(7.3, 8.0))
    assert modified.mc.n_samples == 99
    assert modified.mc.conditioning_grid == (6.0, 7.3, 8.0, 10.0, 12.0, 14.0)
    # base config untouched
    assert config.mc.n_samples == _N
    assert config.mc.conditioning_grid == _GRID


@pytest.fixture(scope="module")
def ladder_result() -> GapDecompositionResult:
    """One shared stub ladder run for the invariant and statistics tests."""
    return run_comparator_ladder(_make_config(), n_jobs=1)


def test_ladder_c0_c4b_match_production_batch(ladder_result) -> None:
    """C0/C4b are bit-identical to the M8 production flags per level."""
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    seepage = None
    from bep_reliability_engine.run import seepage_length_samples_for_config

    seepage = seepage_length_samples_for_config(config)
    for i, record in enumerate(conditioning_hydrographs_for_config(config)):
        col_static, col_trans = evaluate_batch(
            theta,
            record,
            geometry,
            seepage_length_samples=seepage,
            alpha_exponent=config.alpha_exponent,
            theta_repose_rad=config.theta_repose_rad,
            relative_density=config.relative_density_insitu,
        )
        assert np.array_equal(ladder_result.comparators["C0"][:, i], col_static)
        assert np.array_equal(ladder_result.comparators["C4b"][:, i], col_trans)


def test_ladder_structural_nestings(ladder_result) -> None:
    """The algebraically exact nestings of ADR-0040 hold at every level."""
    c = ladder_result.comparators
    assert not np.any(c["C1"] & ~c["C0"])  # crack load < raw load
    assert not np.any(c["C2"] & ~c["C0b"])
    assert not np.any(c["C1"] & ~c["C2"])  # H_c(-1/2) < H_c(-1/3) at field scale
    assert not np.any(c["C0"] & ~c["C0b"])
    assert not np.any(c["C3a"] & ~c["C2"])  # gate AND strict > inside >=
    assert not np.any(c["C3b"] & ~c["C1"])


def test_ladder_telescoping_and_component_table(ladder_result) -> None:
    """Ladder steps telescope exactly; the table flags unresolved steps."""
    p_f = ladder_result.p_f()
    for steps, endpoint in (
        (PHYSICS_LADDER_STEPS, "C4a"),
        (ENGINE_LADDER_STEPS, "C4b"),
    ):
        total = p_f["C0"] - p_f[endpoint]
        summed = np.zeros_like(total)
        for _, minuend, subtrahend in steps:
            summed = summed + (p_f[minuend] - p_f[subtrahend])
        np.testing.assert_allclose(summed, total, rtol=0.0, atol=1e-15)

    boot = bootstrap_comparator_means(ladder_result, n_replicates=50, seed=1)
    table = component_table(ladder_result, boot)
    assert set(table["ladders"]) == {"physics", "engine"}
    engine = table["ladders"]["engine"]
    assert set(engine["steps"]) == {
        "head_convention",
        "initiation_gate",
        "temporal_net",
    }
    # every reported delta must reproduce the raw difference
    for name, minuend, subtrahend in ENGINE_LADDER_STEPS:
        np.testing.assert_allclose(
            np.asarray(engine["steps"][name]["delta"]),
            p_f[minuend] - p_f[subtrahend],
            atol=1e-15,
        )


def test_paired_delta_ci_tighter_than_unpaired(ladder_result) -> None:
    """Pairing exploits shared samples: the C0-C1 delta CI must be narrower
    than the width implied by treating the two comparators independently."""
    boot = bootstrap_comparator_means(ladder_result, n_replicates=200, seed=2)
    lo, hi = delta_ci(boot, "C0", "C1")
    paired_width = hi - lo
    i0, i1 = boot.index("C0"), boot.index("C1")
    var_c0 = boot.means[:, i0, :].var(axis=0)
    var_c1 = boot.means[:, i1, :].var(axis=0)
    unpaired_width = 2.0 * 1.96 * np.sqrt(var_c0 + var_c1)
    active = ladder_result.p_f()["C0"] > 0.05
    assert np.all(paired_width[active] <= unpaired_width[active] + 1e-12)


def test_static_pair_shapley_orders_sum_to_lattice_gap(ladder_result) -> None:
    """Both orderings and the Shapley pair each sum to P(C0) - P(C2)."""
    p_f = ladder_result.p_f()
    boot = bootstrap_comparator_means(ladder_result, n_replicates=50, seed=3)
    shapley = static_pair_shapley(ladder_result, boot)
    lattice_gap = p_f["C0"] - p_f["C2"]
    for a, b in (
        ("head_first_head", "head_first_dimensional"),
        ("alpha_first_head", "alpha_first_dimensional"),
        ("shapley_head", "shapley_dimensional"),
    ):
        np.testing.assert_allclose(
            np.asarray(shapley[a]["delta"]) + np.asarray(shapley[b]["delta"]),
            lattice_gap,
            atol=1e-15,
        )


def test_analytic_sustained_limit_matches_long_ode() -> None:
    """The finite-hold ODE indicator converges to the analytic limit.

    On the stub section at a bracketing level, a long hold must agree with
    the analytic sustained-peak limit except for near-critical rows, and the
    disagreement must shrink monotonically with the hold duration.
    """
    config = _make_config(n_samples=300)
    ladder = sustained_duration_ladder(
        config,
        levels_m=(12.0,),
        durations_hours=(6.0, 48.0, 384.0),
        n_jobs=1,
    )
    rows = ladder["rows"]
    missing = [row["analytic_not_ode"] for row in rows]
    assert missing[0] >= missing[-1]
    assert missing[-1] <= max(1, int(0.01 * 300))
    # the ODE may never exceed the analytic limit except by Euler jumps
    assert all(row["ode_not_analytic"] <= 1 for row in rows)


def test_result_persistence_roundtrip(tmp_path, ladder_result) -> None:
    """HDF5 + JSON sidecar round-trip preserves every array and the metadata."""
    path = tmp_path / "stage6_6_test.h5"
    ladder_result.save(path)
    loaded = GapDecompositionResult.load(path)
    assert set(loaded.comparators) == set(COMPARATOR_ORDER)
    for name in COMPARATOR_ORDER:
        np.testing.assert_array_equal(
            loaded.comparators[name], ladder_result.comparators[name]
        )
    np.testing.assert_array_equal(loaded.theta_matrix, ladder_result.theta_matrix)
    np.testing.assert_array_equal(
        loaded.conditioning_grid, ladder_result.conditioning_grid
    )
    np.testing.assert_array_equal(
        loaded.seepage_length_samples, ladder_result.seepage_length_samples
    )
    for name, counts in ladder_result.flip_counts.items():
        np.testing.assert_array_equal(loaded.flip_counts[name], counts)
    assert loaded.metadata["config_hash"] == ladder_result.metadata["config_hash"]
    assert loaded.param_names == ladder_result.param_names


def test_dimensional_direction_via_alpha_transient(ladder_result) -> None:
    """C4a (3D exponent) can only add transient failures relative to C4b
    in the continuum; count violations like the Euler-flip diagnostics."""
    c = ladder_result.comparators
    # H_c(-1/2) <= H_c(-1/3) at field scale -> lower barrier -> more failures.
    added = np.sum(c["C4a"] & ~c["C4b"])
    removed = np.sum(c["C4b"] & ~c["C4a"])
    assert removed == 0
    assert added >= 0
