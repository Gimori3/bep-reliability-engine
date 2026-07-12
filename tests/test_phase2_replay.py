"""Replay, sequential composition and posterior-fragility tests (stub path).

Driven by a genuine small-N Phase 1 run on the synthetic-stub hydrograph
path (no external data), generated once per session through the real
``run_fragility_analysis`` and reloaded through the real persistence layer,
so the entire Phase 2 chain is exercised against the true interface. The
stochastic seepage length is ON, so the L-regeneration seam is load-bearing
in every test here.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from bayesian_reliability_updating.analysis import c_e_headline, column
from bayesian_reliability_updating.filtering import apply_survival_filter
from bayesian_reliability_updating.fragility_update import (
    posterior_fragility_from_matrices,
    verify_posterior_fragility_by_reevaluation,
)
from bayesian_reliability_updating.replay import (
    breach_times_for_rows,
    load_phase1_run,
    replay_event,
)
from bayesian_reliability_updating.sequential import apply_event, initial_state
from tests.phase2_helpers import (
    STUB_N,
    Z_TOE,
    flat_record,
    generate_stub_phase1,
    stressing_record,
)


@pytest.fixture(scope="module")
def phase1_path(tmp_path_factory: pytest.TempPathFactory):
    return generate_stub_phase1(tmp_path_factory.mktemp("phase1_stub"))


@pytest.fixture(scope="module")
def run(phase1_path):
    return load_phase1_run(phase1_path)


# ---------------------------------------------------------------------------
# Loading and provenance integrity
# ---------------------------------------------------------------------------


def test_load_reconstructs_and_verifies_the_run(run) -> None:
    assert run.n_samples == STUB_N
    assert run.theta_verified is True
    assert run.seepage_length_samples is not None
    assert run.seepage_length_samples.shape == (STUB_N,)
    assert set(run.geometry) >= {"L", "z_toe", "foreshore_width", "D_fore", "k_fore"}
    assert len(run.h5_sha256) == 64 and len(run.sidecar_sha256) == 64


def test_load_refuses_a_drifted_config_snapshot(phase1_path, tmp_path) -> None:
    """A tampered config snapshot must fail the hash check loudly."""
    import shutil

    h5_copy = tmp_path / phase1_path.name
    shutil.copy(phase1_path, h5_copy)
    sidecar = phase1_path.with_suffix(".json")
    tampered = json.loads(sidecar.read_text(encoding="utf-8"))
    tampered["config"]["geometry"]["L"] = 31.0  # not what the run used
    h5_copy.with_suffix(".json").write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="config hash"):
        load_phase1_run(h5_copy)


# ---------------------------------------------------------------------------
# Replay behavior
# ---------------------------------------------------------------------------


def test_negligible_event_accepts_every_row(run) -> None:
    """A flat record at the toe drives nothing: rejection fraction zero."""
    record = flat_record(Z_TOE, event_id="negligible")
    replay = replay_event(run, record)
    outcome = apply_survival_filter(replay)
    assert outcome.n_accepted == run.n_samples
    assert outcome.rejection_fraction == 0.0
    assert outcome.decomposition["f_trans_reject"] == 0.0


def test_replay_refines_onto_the_run_integration_grid(run) -> None:
    """ADR-0036: the record is resampled to the config target_dt_seconds."""
    record = flat_record(Z_TOE + 1.0, dt_s=4.0 * 7200.0, event_id="coarse")
    replay = replay_event(run, record)
    assert replay.record.native_dt == run.config.timestepper.target_dt_seconds
    assert replay.settings["replay_dt_seconds"] == pytest.approx(7200.0)
    assert replay.settings["record_native_dt_seconds"] == pytest.approx(28800.0)


def test_stressing_event_rejects_the_fast_corner(run) -> None:
    """Rejection concentrates in high C_e times k_aq; C_e posterior drops.

    The laminar-conservatism signature (spec section 4, section 12 failure
    mode 7) needs a TIME-LIMITED event: a short high pulse breaches only
    the rows whose progression rate (C_e times k_aq) is fast enough to
    cross within the pulse, so the accepted set must show (a) a rejection
    fraction strictly inside (0, 1), (b) near-total rejection of the top
    C_e times k_aq decile, and (c) a posterior C_e mean shifted below the
    prior mean. (A long plateau shows a much weaker C_e signature: with
    unlimited time the rejection is barrier-driven, not rate-driven, which
    is itself part of the survival-discrimination story.)
    """
    record = stressing_record(9.0, hours=16, event_id="stress9")
    replay = replay_event(run, record)
    outcome = apply_survival_filter(replay)
    assert 0 < outcome.n_accepted < run.n_samples

    headline = c_e_headline(run.theta, run.param_names, outcome.accept)
    assert headline["rejection_fraction_top_decile_ce_kaq"] > 0.9
    assert headline["rejection_concentration_ratio"] > 1.3
    assert headline["posterior_mean"] < 0.95 * headline["prior_mean"]

    # And the joint driver check directly: the rejected rows' median
    # C_e * k_aq product sits above the accepted rows' median.
    c_e = column(run.theta, run.param_names, "C_e")
    k_aq = column(run.theta, run.param_names, "k_aq")
    driver = c_e * k_aq
    assert np.median(driver[~outcome.accept]) > np.median(driver[outcome.accept])


def test_breach_times_finite_for_rejected_rows_only(run) -> None:
    record = stressing_record(9.0, hours=120, event_id="stress9b")
    replay = replay_event(run, record)
    outcome = apply_survival_filter(replay)
    rejected = np.nonzero(~outcome.accept_trans)[0]
    accepted = np.nonzero(outcome.accept_trans)[0][:5]
    assert rejected.size > 0

    t_breach = breach_times_for_rows(run, replay, rejected)
    assert np.all(np.isfinite(t_breach))
    assert np.all(t_breach >= replay.record.t[0])
    assert np.all(t_breach <= replay.record.t[-1])

    t_none = breach_times_for_rows(run, replay, accepted)
    assert np.all(np.isnan(t_none))


# ---------------------------------------------------------------------------
# Sequential composition
# ---------------------------------------------------------------------------


def test_sequential_composition_equals_joint_filtering(run) -> None:
    """Filter by A then B == filter by B then A == elementwise AND."""
    event_a = stressing_record(8.5, hours=96, event_id="event_a")
    event_b = stressing_record(9.0, hours=48, event_id="event_b")

    state_ab = initial_state(run)
    state_ab, outcome_a, _ = apply_event(state_ab, event_a)
    state_ab, outcome_b, _ = apply_event(state_ab, event_b)

    state_ba = initial_state(run)
    state_ba, outcome_b2, _ = apply_event(state_ba, event_b)
    state_ba, outcome_a2, _ = apply_event(state_ba, event_a)

    joint = outcome_a.accept & outcome_b.accept
    np.testing.assert_array_equal(state_ab.alive, joint)
    np.testing.assert_array_equal(state_ba.alive, joint)
    # Per-event masks are order-independent (pure functions of the event).
    np.testing.assert_array_equal(outcome_a.accept, outcome_a2.accept)
    np.testing.assert_array_equal(outcome_b.accept, outcome_b2.accept)
    # The chain summary records the narrowing.
    summary = state_ab.chain_summary()
    assert summary[-1]["n_alive_after"] == int(joint.sum())


# ---------------------------------------------------------------------------
# Posterior fragility: masked-matrix default and re-evaluation verification
# ---------------------------------------------------------------------------


def test_masked_matrix_posterior_matches_manual_fractions(run) -> None:
    rng = np.random.default_rng(3)
    accept = rng.random(run.n_samples) < 0.7
    posterior = posterior_fragility_from_matrices(run, accept, n_bootstrap=50)
    manual_trans = run.result.failure_matrix_tran[accept, :].mean(axis=0)
    manual_stat = run.result.failure_matrix_stat[accept, :].mean(axis=0)
    np.testing.assert_array_equal(posterior.P_f_trans_post_raw, manual_trans)
    np.testing.assert_array_equal(posterior.P_f_static_post_raw, manual_stat)
    assert posterior.n_accepted == int(accept.sum())
    n_h = run.result.conditioning_grid.size
    for lo, hi in posterior.binomial_ci.values():
        assert lo.shape == (n_h,) and hi.shape == (n_h,)
        assert np.all(lo <= hi)
    for lo, hi in posterior.bootstrap_bands.values():
        assert np.all(lo <= hi)


def test_all_accept_posterior_equals_the_prior_curves(run) -> None:
    accept = np.ones(run.n_samples, dtype=bool)
    posterior = posterior_fragility_from_matrices(run, accept, n_bootstrap=20)
    np.testing.assert_array_equal(
        posterior.P_f_trans_post_raw, run.result.P_f_trans_raw
    )
    np.testing.assert_array_equal(
        posterior.P_f_static_post_raw, run.result.P_f_static_raw
    )


def test_zero_accept_raises(run) -> None:
    with pytest.raises(ValueError, match="no accepted rows"):
        posterior_fragility_from_matrices(
            run, np.zeros(run.n_samples, dtype=bool), n_bootstrap=10
        )


def test_reevaluation_verification_agrees_exactly(run) -> None:
    """Mission invariant 7: masked-matrix and re-evaluation paths agree
    exactly (zero flag mismatches, zero curve deviation)."""
    rng = np.random.default_rng(5)
    accept = rng.random(run.n_samples) < 0.5
    posterior = posterior_fragility_from_matrices(run, accept, n_bootstrap=20)
    report = verify_posterior_fragility_by_reevaluation(run, accept, posterior)
    assert report["verified"] is True
    assert report["flag_mismatch_static"] == 0
    assert report["flag_mismatch_trans"] == 0
    assert report["max_abs_dev_trans"] == 0.0
    assert report["max_abs_dev_static"] == 0.0
