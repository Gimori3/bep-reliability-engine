"""ADR-0045 Sellmeijer model factor m_p: sampler, M8 threading, run wiring.

Locks the three ADR-0045 guarantees:

1. **Baseline bit-identity when off.** A config without the
   ``sellmeijer_model_factor`` block (and one carrying it ``enabled=False``)
   produces bit-identical failure matrices, and the None case is dropped from
   ``to_metadata()`` so pre-ADR-0045 config hashes are preserved (the Phase 2
   replay hash gate).
2. **Single-source propagation.** When enabled, one per-realization m_p draw
   scales the critical head in BOTH its uses — the static comparator H_c and
   the transient H_eq anchor H_c_transient — and nothing else (l_c, lambda_in,
   r_e untouched). Never one branch alone.
3. **Frozen sampling contract.** m_p is a standalone 1-D LHS draw under its
   own SeedSequence salt (the ``sample_seepage_length`` pattern): enabling it
   does not shift the theta matrix or the L draw, and the draw is regenerable
   through the public ``model_factor_samples_for_config`` seam.
"""

from __future__ import annotations

import numpy as np
import pytest

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import (
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.run import (
    model_factor_samples_for_config,
    run_fragility_analysis,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_model_factor, sample_theta

from .phase2_helpers import generate_stub_phase1, stressing_record, stub_config

# Small prior-style theta matrix in the canonical column order (spec §2);
# values from the M8 test suite (positive H_c everywhere).
THETA = np.array(
    [
        [1.0e-4, 2.0e-4, 3.0, 3.0, 1.0e-6, 16.0, 0.014],
        [2.0e-4, 2.5e-4, 4.0, 2.0, 2.0e-6, 14.0, 0.020],
        [5.0e-5, 1.8e-4, 2.5, 4.0, 5.0e-7, 18.0, 0.010],
        [3.0e-4, 3.0e-4, 5.0, 1.5, 3.0e-6, 12.0, 0.030],
    ]
)

GEOMETRY = {
    "L": 30.0,
    "z_toe": 2.0,
    "foreshore_width": 0.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}


def _two_peak_record(peak_m: float = 9.0, dt_s: float = 3600.0) -> HydrographRecord:
    """A compound two-peak record high enough to open the gate on every row."""
    h = np.concatenate(
        [
            np.full(6, 2.0),
            np.linspace(2.0, 0.6 * peak_m, 8),
            np.linspace(0.6 * peak_m, 2.5, 6),
            np.linspace(2.5, peak_m, 8),
            np.full(6, peak_m),
            np.linspace(peak_m, 2.0, 8),
        ]
    )
    t = np.arange(h.size, dtype=np.float64) * dt_s
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(peak_m),
        duration_hours=float((h.size - 1) * dt_s / 3600.0),
        scenario="historical",
        event_id="mp_test_event",
        native_dt=float(dt_s),
        provenance={},
    )


# ---------------------------------------------------------------------------
# Sampler
# ---------------------------------------------------------------------------


def test_sample_model_factor_moments_and_determinism() -> None:
    draws = sample_model_factor(1.0, 0.12, seed=123, n_samples=20_000)
    assert draws.shape == (20_000,)
    assert np.all(draws > 0.0)
    assert draws.mean() == pytest.approx(1.0, rel=0.01)
    assert draws.std() / draws.mean() == pytest.approx(0.12, rel=0.05)
    again = sample_model_factor(1.0, 0.12, seed=123, n_samples=20_000)
    np.testing.assert_array_equal(draws, again)
    other = sample_model_factor(1.0, 0.12, seed=124, n_samples=20_000)
    assert not np.array_equal(draws, other)


def test_sample_model_factor_validation() -> None:
    with pytest.raises(ValueError, match="mean"):
        sample_model_factor(0.0, 0.12, seed=1, n_samples=10)
    with pytest.raises(ValueError, match="cov"):
        sample_model_factor(1.0, 0.0, seed=1, n_samples=10)
    with pytest.raises(ValueError, match="n_samples"):
        sample_model_factor(1.0, 0.12, seed=1, n_samples=0)


# ---------------------------------------------------------------------------
# Config: hash preservation (load-bearing for the Phase 2 replay) + validation
# ---------------------------------------------------------------------------


def test_config_hash_preserved_when_block_absent() -> None:
    baseline = stub_config()
    assert baseline.sellmeijer_model_factor is None
    snapshot = baseline.to_metadata()
    assert "sellmeijer_model_factor" not in snapshot
    # Round-trip: a pre-ADR-0045 snapshot (no key) reconstructs to None and
    # hashes identically — the Phase 2 hash gate keeps passing.
    rebuilt = Config.model_validate(snapshot)
    assert rebuilt.sellmeijer_model_factor is None
    assert rebuilt.config_hash() == baseline.config_hash()


def test_config_block_roundtrips_and_changes_hash() -> None:
    baseline = stub_config()
    with_block = stub_config(
        sellmeijer_model_factor={"enabled": True, "mean": 1.0, "cov": 0.12}
    )
    snapshot = with_block.to_metadata()
    assert snapshot["sellmeijer_model_factor"] == {
        "enabled": True,
        "mean": 1.0,
        "cov": 0.12,
    }
    assert with_block.config_hash() != baseline.config_hash()
    rebuilt = Config.model_validate(snapshot)
    assert rebuilt.config_hash() == with_block.config_hash()


def test_config_block_validation() -> None:
    with pytest.raises(Exception, match="cov"):
        stub_config(sellmeijer_model_factor={"enabled": True, "cov": 0.0})
    with pytest.raises(Exception, match="mean"):
        stub_config(sellmeijer_model_factor={"enabled": True, "mean": 0.0})


# ---------------------------------------------------------------------------
# M8: single-source propagation and scalar/batch equivalence
# ---------------------------------------------------------------------------


def test_model_factor_scales_both_hc_uses_and_nothing_else() -> None:
    record = _two_peak_record()
    factors = np.array([0.8, 1.0, 1.1, 1.3])
    base = evaluate_batch_diagnostics(THETA, record, GEOMETRY)
    scaled = evaluate_batch_diagnostics(
        THETA, record, GEOMETRY, model_factor_samples=factors
    )
    # Both H_c uses carry the same per-row factor (ADR-0045: one belief per
    # realization), bit-exactly.
    np.testing.assert_array_equal(scaled.H_c, base.H_c * factors)
    np.testing.assert_array_equal(scaled.H_c_transient, base.H_c_transient * factors)
    # Everything geometric/hydraulic is untouched.
    np.testing.assert_array_equal(scaled.l_c, base.l_c)
    np.testing.assert_array_equal(scaled.lambda_in, base.lambda_in)
    np.testing.assert_array_equal(scaled.r_e, base.r_e)
    # The factored static margin is exactly the factored-H_c margin.
    load = float(record.peak) - GEOMETRY["z_toe"]
    np.testing.assert_array_equal(
        scaled.failure_static, (base.H_c * factors - load) <= 0.0
    )


def test_model_factor_scales_transient_hc_under_asymmetric_alpha() -> None:
    """The ADR-0017 transient-only H_c is scaled by the same m_p draw."""
    record = _two_peak_record()
    factors = np.array([0.7, 1.2, 0.9, 1.05])
    base = evaluate_batch_diagnostics(
        THETA, record, GEOMETRY, alpha_exponent_transient=-0.5
    )
    scaled = evaluate_batch_diagnostics(
        THETA,
        record,
        GEOMETRY,
        alpha_exponent_transient=-0.5,
        model_factor_samples=factors,
    )
    np.testing.assert_array_equal(scaled.H_c, base.H_c * factors)
    np.testing.assert_array_equal(scaled.H_c_transient, base.H_c_transient * factors)


def test_batch_matches_scalar_with_model_factor() -> None:
    record = _two_peak_record()
    factors = np.array([0.85, 1.0, 1.15, 1.25])
    batch = evaluate_batch_diagnostics(
        THETA, record, GEOMETRY, model_factor_samples=factors
    )
    for j in range(THETA.shape[0]):
        scalar = evaluate_realization(
            THETA[j], record, GEOMETRY, model_factor_mp=float(factors[j])
        )
        assert scalar.H_c == batch.H_c[j]
        assert scalar.H_c_transient == batch.H_c_transient[j]
        assert scalar.Z_static == batch.Z_static[j]
        assert scalar.Z_transient == batch.Z_transient[j]
        assert scalar.l_e_final == batch.l_e_final[j]
        assert scalar.failure_static == batch.failure_static[j]
        assert scalar.failure_trans == batch.failure_trans[j]


def test_model_factor_none_is_bit_identical() -> None:
    record = _two_peak_record()
    base = evaluate_batch_diagnostics(THETA, record, GEOMETRY)
    explicit_none = evaluate_batch_diagnostics(
        THETA, record, GEOMETRY, model_factor_samples=None
    )
    for field in ("Z_static", "Z_transient", "H_c", "H_c_transient", "l_e_final"):
        np.testing.assert_array_equal(
            getattr(base, field), getattr(explicit_none, field)
        )


def test_model_factor_shape_mismatch_raises() -> None:
    record = _two_peak_record()
    with pytest.raises(ValueError, match="model_factor_samples"):
        evaluate_batch_diagnostics(
            THETA, record, GEOMETRY, model_factor_samples=np.ones(3)
        )


# ---------------------------------------------------------------------------
# Orchestrator wiring: baseline bit-identity, metadata stamp, regeneration
# ---------------------------------------------------------------------------


def test_run_baseline_bit_identity_and_metadata_stamp(tmp_path) -> None:
    baseline_cfg = stub_config()
    disabled_cfg = stub_config(
        sellmeijer_model_factor={"enabled": False, "mean": 1.0, "cov": 0.12}
    )
    enabled_cfg = stub_config(
        sellmeijer_model_factor={"enabled": True, "mean": 1.0, "cov": 0.12}
    )

    baseline = run_fragility_analysis(
        baseline_cfg, n_jobs=1, progress=False, output_path=tmp_path / "base.h5"
    )
    disabled = run_fragility_analysis(
        disabled_cfg, n_jobs=1, progress=False, output_path=tmp_path / "off.h5"
    )
    enabled = run_fragility_analysis(
        enabled_cfg, n_jobs=1, progress=False, output_path=tmp_path / "on.h5"
    )

    # (1) enabled=False is bit-identical to no-block baseline.
    np.testing.assert_array_equal(
        baseline.failure_matrix_stat, disabled.failure_matrix_stat
    )
    np.testing.assert_array_equal(
        baseline.failure_matrix_tran, disabled.failure_matrix_tran
    )
    np.testing.assert_array_equal(baseline.P_f_static_raw, disabled.P_f_static_raw)
    np.testing.assert_array_equal(baseline.P_f_trans_raw, disabled.P_f_trans_raw)

    # (2) The metadata stamp: absent without the block, truthful with it.
    assert "sellmeijer_model_factor" not in baseline.metadata
    assert disabled.metadata["sellmeijer_model_factor"] == {
        "stochastic": False,
        "mean": 1.0,
        "cov": 0.12,
    }
    assert enabled.metadata["sellmeijer_model_factor"]["stochastic"] is True

    # (3) The enabled run genuinely differs (the factor is live).
    assert not np.array_equal(baseline.failure_matrix_stat, enabled.failure_matrix_stat)

    # (4) Enabling m_p does NOT shift the theta draw or the L draw (the
    # frozen sampling contract): both regenerate identically for all three.
    np.testing.assert_array_equal(baseline.theta_matrix, enabled.theta_matrix)
    np.testing.assert_array_equal(
        seepage_length_samples_for_config(baseline_cfg),
        seepage_length_samples_for_config(enabled_cfg),
    )

    # (5) The public regeneration seam: None for baseline/disabled, the
    # exact (N,) draw for enabled.
    assert model_factor_samples_for_config(baseline_cfg) is None
    assert model_factor_samples_for_config(disabled_cfg) is None
    factors = model_factor_samples_for_config(enabled_cfg)
    assert factors is not None and factors.shape == (enabled_cfg.mc.n_samples,)

    # (6) End-to-end regeneration check: the enabled run's static failure
    # column at the top level reproduces from the regenerated draws through
    # the plain M6 static comparison (failure iff m_p*H_c <= peak - z_toe).
    from bep_reliability_engine.sellmeijer import compute_critical_head_vectorized

    theta = sample_theta(
        enabled_cfg.priors.to_marginal_specs(),
        seed=enabled_cfg.mc.seed,
        rho_log_kaq_d70=enabled_cfg.correlation.rho_log_kaq_d70,
        d70_interpretation=enabled_cfg.priors.d70_interpretation,
        n_samples=enabled_cfg.mc.n_samples,
        coupling=enabled_cfg.correlation.coupling,
        bounds=enabled_cfg.priors.bounds,
    ).theta_matrix
    lengths = seepage_length_samples_for_config(enabled_cfg)
    h_c = compute_critical_head_vectorized(theta, {"L": lengths}).H_c
    top_level = float(enabled_cfg.mc.conditioning_grid[-1])
    expected = (factors * h_c) <= (top_level - enabled_cfg.geometry.z_toe)
    np.testing.assert_array_equal(enabled.failure_matrix_stat[:, -1], expected)


# ---------------------------------------------------------------------------
# Phase 2 replay: the m_p draw regenerates and threads through the replay
# ---------------------------------------------------------------------------


def test_phase2_replay_threads_regenerated_model_factor(tmp_path) -> None:
    from bayesian_reliability_updating.replay import load_phase1_run, replay_event

    mp_block = {"enabled": True, "mean": 1.0, "cov": 0.12}
    path = generate_stub_phase1(
        tmp_path,
        cross_section_id="mp_replay_xs",
        sellmeijer_model_factor=mp_block,
    )
    run = load_phase1_run(path)

    # The draw regenerates through the public seam, row-paired with theta.
    expected = model_factor_samples_for_config(run.config)
    assert run.model_factor_samples is not None
    np.testing.assert_array_equal(run.model_factor_samples, expected)

    # The replay applies it: H_c diagnostics equal the factored no-mp values.
    record = stressing_record(9.0)
    replay = replay_event(run, record)
    assert replay.settings["model_factor_stochastic"] is True
    bare = evaluate_batch_diagnostics(
        run.theta,
        replay.record,
        run.geometry,
        seepage_length_samples=run.seepage_length_samples,
        alpha_exponent=run.config.alpha_exponent,
        theta_repose_rad=run.config.theta_repose_rad,
        relative_density=run.config.relative_density_insitu,
    )
    np.testing.assert_array_equal(
        replay.diagnostics.H_c, bare.H_c * run.model_factor_samples
    )
    np.testing.assert_array_equal(
        replay.diagnostics.H_c_transient,
        bare.H_c_transient * run.model_factor_samples,
    )


def test_phase2_replay_baseline_has_no_model_factor(tmp_path) -> None:
    from bayesian_reliability_updating.replay import load_phase1_run, replay_event

    path = generate_stub_phase1(tmp_path, cross_section_id="mp_baseline_xs")
    run = load_phase1_run(path)
    assert run.model_factor_samples is None
    replay = replay_event(run, stressing_record(9.0))
    assert replay.settings["model_factor_stochastic"] is False
