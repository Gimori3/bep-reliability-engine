"""Analytic time-contract and invalid-observation regressions (ADR-0053)."""

from types import SimpleNamespace

import numpy as np
import pytest

from bep_reliability_engine.evaluator import (
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.gsa_qoi import evaluate_qoi_batch
from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.hydrographs import HydrographRecord, resample_record
from bep_reliability_engine.progression import integrate_progression

THETA = np.array([1e-4, 2e-4, 3.0, 1.0, 1e-6, 6.9, 0.055])
GEOMETRY = dict(L=30.0, z_toe=0.0, foreshore_width=0.0, D_fore=1.0, k_fore=1e-6)


def record(h, dt=10.0):
    """Instantaneous samples with a deliberately nonzero absolute origin."""
    return SimpleNamespace(
        h=np.asarray(h), t=123.0 + np.arange(len(h)) * dt, peak=max(h), native_dt=dt
    )


def test_constant_rate_interval_kernel_and_state_times():
    """A flat postcritical H_eq gives l(T)=l0+v*T, independently of Euler."""
    rate = 89 * 0.055 * (1e-4 * (4.0 - 0.3 - 1.0) / 30.0) ** 0.81
    out = integrate_progression(
        [4.0, 4.0],
        10.0,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=0.055,
        k_aq_mps=1e-4,
        d_bl_m=1.0,
        gamma_bl_sub_knpm3=6.9,
        h_c_m=1.0,
        l_c_m=1.0,
        seepage_length_m=30.0,
        l_ini_m=2.0,
        equilibrium_end_factor=1.0,
        store_trajectory=True,
    )
    np.testing.assert_allclose(
        out.l_trajectory_m, 2.0 + rate * np.array([10.0, 20.0]), rtol=1e-14
    )


@pytest.mark.parametrize("backend", ["numpy", "numba"])
@pytest.mark.parametrize(
    "stages", [[4.0, 4.0], [0.0, 4.0], [4.0, 0.0], [0.0, 4.0, 0.0]]
)
def test_record_has_exactly_n_minus_one_updates(backend, stages):
    """Active last samples have no duration; inactive endpoints remain inert."""
    if backend == "numba":
        pytest.importorskip("numba")
    rec = record(stages)
    scalar = evaluate_realization(THETA, rec, GEOMETRY, store_trajectory=True)
    batch = evaluate_batch_diagnostics(
        THETA[None, :], rec, GEOMETRY, progression_backend=backend
    )
    rate = (
        89 * THETA[6] * (THETA[0] * max(0.0, stages[0] - 0.3) / GEOMETRY["L"]) ** 0.81
    )
    # These cases have at most one active left endpoint, starting from l=0.
    expected = (
        rate * 10.0
        if stages[0] > 0
        else (
            89 * THETA[6] * (THETA[0] * 3.7 / 30.0) ** 0.81 * 10.0
            if len(stages) == 3
            else 0.0
        )
    )
    assert scalar.l_e_final == pytest.approx(expected, rel=1e-13)
    assert batch.l_e_final[0] == pytest.approx(expected, rel=1e-13)
    qoi = evaluate_qoi_batch(THETA[None, :], rec, GEOMETRY, progression_backend=backend)
    assert qoi.l_e_final_m[0] == pytest.approx(expected, rel=1e-13)
    assert scalar.l_trajectory[0] == 0.0
    assert len(scalar.l_trajectory) == len(stages)
    assert scalar.l_trajectory[-1] == scalar.l_e_final


def test_zero_span_and_threshold_crossing():
    """A point load cannot advance; a completing step is stored at its end."""
    one = evaluate_realization(
        THETA, record([100.0]), GEOMETRY, l_ini=29.99, store_trajectory=True
    )
    assert one.l_e_final == 29.99
    out = evaluate_realization(
        THETA,
        record([100.0, 100.0], dt=1000.0),
        GEOMETRY,
        l_ini=29.99,
        store_trajectory=True,
    )
    np.testing.assert_array_equal(out.l_trajectory, [29.99, 30.0])


@pytest.mark.parametrize("field", ["h", "t", "peak", "native_dt"])
@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_rejected_at_construction_and_duck_boundaries(field, bad):
    """Invalid observations must never be interpreted as physical survival."""
    rec = record([4.0, 4.0])
    value = getattr(rec, field)
    if isinstance(value, np.ndarray):
        value = value.copy()
        value[-1] = bad
    else:
        value = bad
    setattr(rec, field, value)
    with pytest.raises(ValueError, match="finite"):
        HydrographRecord(
            **vars(rec), duration_hours=10.0 / 3600, scenario="test", event_id="test"
        )
    with pytest.raises(ValueError, match="finite"):
        evaluate_realization(THETA, rec, GEOMETRY)
    for backend in ["numpy", "numba"]:
        with pytest.raises(ValueError, match="finite"):
            evaluate_qoi_batch(
                THETA[None, :], rec, GEOMETRY, progression_backend=backend
            )
        with pytest.raises(ValueError, match="finite"):
            evaluate_batch_diagnostics(
                THETA[None, :], rec, GEOMETRY, progression_backend=backend
            )


def test_refinement_preserves_span_and_initial_state():
    """Refinement adds nodes, not exposure beyond the final observation."""
    rec = HydrographRecord(
        **vars(record([4.0, 4.0])),
        duration_hours=10.0 / 3600,
        scenario="test",
        event_id="test",
    )
    fine = resample_record(rec, 5.0)
    np.testing.assert_array_equal(fine.t, [123.0, 128.0, 133.0])
    assert fine.duration_hours == rec.duration_hours


def test_final_observation_records_initiation_without_progression():
    """A newly active final node records onset but has no following interval."""
    out = evaluate_realization(THETA, record([0.0, 4.0]), GEOMETRY)
    assert out.l_e_final == 0.0
    assert out.uplift_occurred and out.heave_occurred
    assert out.t_uh == 10.0


def test_breach_extraction_uses_end_state_and_elapsed_origin():
    """Real scalar progression crosses on the first interval, at elapsed dt."""
    from bayesian_reliability_updating.replay import breach_times_for_rows

    config = SimpleNamespace(
        alpha_exponent=None,
        alpha_exponent_transient=None,
        theta_repose_rad=None,
        relative_density_insitu=None,
        foreland_treatment="blanketed_tanh",
        critical_length_factor=None,
        toe_gradient_relief_factor=None,
        crack_resistance_factor=None,
        foreland_seepage_credit=None,
    )
    theta = THETA.copy()
    theta[6] = 100.0
    run = SimpleNamespace(
        config=config,
        geometry=GEOMETRY,
        theta=theta[None, :],
        seepage_length_samples=None,
        model_factor_samples=None,
    )
    times = breach_times_for_rows(
        run, SimpleNamespace(record=record([100.0, 100.0])), np.array([0])
    )
    assert times[0] == 10.0


@pytest.mark.parametrize("times", [[123.0, 123.0], [123.0, 132.0], [123.0]])
def test_inconsistent_duck_time_axis_rejected(times):
    rec = record([4.0, 4.0])
    rec.t = np.asarray(times)
    with pytest.raises(ValueError, match="times"):
        evaluate_realization(THETA, rec, GEOMETRY)
    with pytest.raises(ValueError, match="times"):
        evaluate_batch_diagnostics(THETA[None, :], rec, GEOMETRY)


def test_mutated_lag_config_rejected_before_orchestration():
    from bep_reliability_engine.run import run_fragility_analysis

    config = SimpleNamespace(timestepper=SimpleNamespace(aquifer_lag_active=True))
    with pytest.raises(ValueError, match="unsupported"):
        run_fragility_analysis(config)


def test_clock_migration_dataset_hashes_use_string_values(tmp_path):
    import h5py

    from scripts.migrate_breach_clock import dataset_hashes

    path = tmp_path / "posterior.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("names", data=["k_aq", "C_e"], dtype=h5py.string_dtype())
        handle.create_dataset("accept", data=[True, False])
    first = dataset_hashes(path)
    assert first == dataset_hashes(path)
    with h5py.File(path, "r+") as handle:
        handle["accept"][0] = False
    changed = dataset_hashes(path)
    assert first["names"] == changed["names"]
    assert first["accept"] != changed["accept"]


def test_clock_migration_refuses_a_new_contract_run_before_mutation(tmp_path):
    import json

    from scripts.migrate_breach_clock import migrate

    path = tmp_path / "posterior.json"
    payload = {
        "phase2": {
            "l_ini_m": 0,
            "recovery_r_l": 0,
            "event_chain": [
                {"settings": {"time_contract": "instantaneous_samples_left_euler_v1"}}
            ],
        }
    }
    path.write_text(json.dumps(payload))
    before = path.read_bytes()
    with pytest.raises(AssertionError, match="already uses corrected clock"):
        migrate(path, tmp_path / "archive")
    assert path.read_bytes() == before
    assert not (tmp_path / "archive").exists()
