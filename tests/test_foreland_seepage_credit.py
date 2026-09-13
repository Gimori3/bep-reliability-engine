"""ADR-0052: the opt-in foreland seepage-length credit (TR Zmw 1999 §4.4.2).

Fast, stub-based (the synthetic record path; no d4PDF data needed). The knob is
a keyword-only, default-``None`` fraction in ``[0, 1]`` of each realization's
own ``lambda_out_eff``, added to the seepage length the **Sellmeijer rule** is
evaluated at, in the same additive pattern ADR-0041/0045/0049/0050/0051
established. What is pinned here:

* **bit-identity when off** at every layer -- M6 kernel, both M6 entry points,
  the scalar and batch M8 paths, and a full ``run_fragility_analysis`` sweep;
* the **hash-preservation** mechanism the Phase 2 replay gate depends on: the
  field is dropped from ``to_metadata()`` when None, so pre-ADR-0052 config
  hashes do not move;
* the **channel claim the bracket study rests on**, which is the opposite of
  ADR-0049's and ADR-0050's: the credit reaches ``H_c``, and ``H_c`` is
  single-source, so **both** branches move and neither is invariant. What stays
  on the physical under-levee ``L`` is pinned instead -- ``l_c``, the traverse
  length and the ``Z_transient = L - l_e`` criterion, the ``L`` in the Eq. (5)
  rate denominator, and the ``L`` in ``r_e``;
* the credit is **per realization**, never precomputed once: ``lambda_out_eff``
  is stochastic in ``k_aq`` and ``D_aq``;
* it composes correctly with the ADR-0025 ``foreland_open`` sensitivity (no
  foreland blanket, no displaced entry point, so no credit);
* it works on **both** progression backends.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import (
    evaluate_batch,
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.hydraulics import leakage_length_out
from bep_reliability_engine.run import (
    conditioning_hydrographs_for_config,
    run_fragility_analysis,
)
from bep_reliability_engine.sampling import sample_theta
from bep_reliability_engine.sellmeijer import (
    compute_critical_head,
    compute_critical_head_vectorized,
    resolve_effective_seepage_length,
)

_SEED = 20260626
_N = 400
_GRID = (6.0, 8.0, 10.0, 12.0, 14.0)
_DT_S = 900.0

#: Full credit: the whole TR Zmw 1999 §4.4.2 entry-point displacement.
_FULL = 1.0
#: Half credit, to pin that the fraction is honoured linearly.
_HALF = 0.5


def _make_config(
    *, n_samples: int = _N, conditioning_grid=_GRID, **overrides
) -> Config:
    """Small, fast stub Config (mirrors tests/test_critical_length_factor.py).

    ``foreshore_width`` is finite and non-zero here, unlike the ADR-0049 stub:
    a zero-width foreshore gives ``lambda_out_eff = 0`` and would make the
    credit identically zero, which is exactly the degenerate case this module
    must *not* be testing by accident.
    """
    data = {
        "cross_section_id": "test_xs",
        "segment_id": "TEST.000",
        "scenario": "historical",
        "remediation_state": "none",
        "geometry": {
            "L": 30.0,
            "z_toe": 2.0,
            "foreshore_width": 120.0,
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


def _lambda_out_eff_for(config: Config, theta: np.ndarray) -> np.ndarray:
    geom = config.geometry.as_evaluator_dict()
    return np.asarray(
        leakage_length_out(
            theta[:, 0],
            theta[:, 2],
            geom["D_fore"],
            geom["k_fore"],
            geom["foreshore_width"],
        ),
        dtype=np.float64,
    )


# ---------------------------------------------------------------------------
# M6: the resolver and both entry points
# ---------------------------------------------------------------------------


def test_resolver_returns_the_length_itself_when_the_credit_is_none() -> None:
    """``None`` must return the caller's own object, not a rebuilt float."""
    length = 33.0
    assert resolve_effective_seepage_length(length, None) is length
    vector = np.array([31.0, 33.0, 35.0])
    assert resolve_effective_seepage_length(vector, None) is vector


def test_resolver_adds_the_credit_exactly() -> None:
    assert resolve_effective_seepage_length(33.0, 7.5) == pytest.approx(40.5, abs=0.0)
    got = resolve_effective_seepage_length(np.array([30.0, 40.0]), np.array([5.0, 2.5]))
    assert np.array_equal(got, np.array([35.0, 42.5]))


def test_resolver_accepts_a_zero_credit_as_a_no_op_in_value() -> None:
    assert resolve_effective_seepage_length(33.0, 0.0) == 33.0


@pytest.mark.parametrize("bad", [-1.0, -1e-12, np.nan, np.inf])
def test_resolver_refuses_a_negative_or_non_finite_credit(bad: float) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        resolve_effective_seepage_length(33.0, bad)


def test_both_m6_entry_points_credit_H_c_and_leave_l_c_alone() -> None:
    """H_c is evaluated at L + credit; l_c keeps the physical L."""
    config = _make_config()
    theta = _theta_for(config)
    geom = {"L": 30.0}
    credit = 12.0

    base_s = compute_critical_head(theta[0], geom)
    arm_s = compute_critical_head(theta[0], geom, seepage_length_credit_m=credit)
    direct = compute_critical_head(theta[0], {"L": 30.0 + credit})
    assert arm_s.H_c == direct.H_c  # H_c at L_eff, exactly
    assert arm_s.l_c == base_s.l_c  # l_c on the physical L, exactly
    assert arm_s.H_c > base_s.H_c

    base_v = compute_critical_head_vectorized(theta, geom)
    arm_v = compute_critical_head_vectorized(
        theta, geom, seepage_length_credit_m=credit
    )
    assert np.array_equal(
        arm_v.H_c, compute_critical_head_vectorized(theta, {"L": 42.0}).H_c
    )
    assert np.array_equal(arm_v.l_c, base_v.l_c)
    # And the two entry points agree row for row under the credit.
    assert arm_v.H_c[0] == arm_s.H_c


def test_m6_default_and_none_are_bit_identical() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geom = {"L": 30.0}
    assert np.array_equal(
        compute_critical_head_vectorized(theta, geom).H_c,
        compute_critical_head_vectorized(theta, geom, seepage_length_credit_m=None).H_c,
    )
    assert (
        compute_critical_head(theta[0], geom).H_c
        == compute_critical_head(theta[0], geom, seepage_length_credit_m=None).H_c
    )


# ---------------------------------------------------------------------------
# M8: bit-identity when off, and the channel claim when on
# ---------------------------------------------------------------------------


def _stub_records(config: Config):
    return conditioning_hydrographs_for_config(config)


def test_batch_default_none_is_bit_identical() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    base = evaluate_batch(theta, rec, geom)
    again = evaluate_batch(theta, rec, geom, foreland_seepage_credit=None)
    assert np.array_equal(base[0], again[0])
    assert np.array_equal(base[1], again[1])


def test_scalar_default_none_is_bit_identical() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    for j in (0, 7, 91):
        base = evaluate_realization(theta[j], rec, geom)
        again = evaluate_realization(theta[j], rec, geom, foreland_seepage_credit=None)
        assert base.Z_static == again.Z_static
        assert base.Z_transient == again.Z_transient
        assert base.H_c == again.H_c
        assert base.l_c == again.l_c
        assert base.r_e == again.r_e


def test_a_zero_fraction_is_bit_identical_to_declining_the_credit() -> None:
    """phi = 0 credits nothing, so it must reproduce the baseline exactly."""
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    base = evaluate_batch_diagnostics(theta, rec, geom)
    zero = evaluate_batch_diagnostics(theta, rec, geom, foreland_seepage_credit=0.0)
    assert np.array_equal(base.H_c, zero.H_c)
    assert np.array_equal(base.failure_static, zero.failure_static)
    assert np.array_equal(base.failure_trans, zero.failure_trans)


def test_both_branches_move_and_neither_is_invariant() -> None:
    """The channel claim: H_c is single-source, so the static branch moves too.

    This is the structural opposite of ADR-0049 and ADR-0050, where the static
    column is exactly invariant. The bracket study rests on it, so it is pinned.
    """
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    records = _stub_records(config)

    static_moved = transient_moved = 0
    for rec in records:
        base = evaluate_batch_diagnostics(theta, rec, geom)
        arm = evaluate_batch_diagnostics(
            theta, rec, geom, foreland_seepage_credit=_FULL
        )
        # Every realization gains head, at every level: the margin always moves,
        # even where the flag it decides is saturated at 0 or 1.
        assert np.all(arm.H_c > base.H_c)
        assert np.all(arm.Z_static > base.Z_static)
        # Direction: a raised critical head can only remove failures, never add.
        assert np.all(arm.failure_static <= base.failure_static)
        assert np.all(arm.failure_trans <= base.failure_trans)
        static_moved += int((base.failure_static != arm.failure_static).sum())
        transient_moved += int((base.failure_trans != arm.failure_trans).sum())

    # And on the unsaturated levels the flags themselves move, on BOTH branches.
    assert static_moved > 0
    assert transient_moved > 0


def test_what_stays_on_the_physical_under_levee_length() -> None:
    """l_c, r_e and the Z_transient datum are untouched by the credit."""
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    base = evaluate_batch_diagnostics(theta, rec, geom)
    arm = evaluate_batch_diagnostics(theta, rec, geom, foreland_seepage_credit=_FULL)

    assert np.array_equal(base.l_c, arm.l_c)
    assert np.array_equal(base.r_e, arm.r_e)
    assert np.array_equal(base.lambda_in, arm.lambda_in)
    # Z_transient = L - l_e is measured against the physical L: a realization
    # that never erodes keeps exactly the baseline margin L - l_ini.
    stalled = np.flatnonzero(arm.l_e_final == 0.0)
    assert stalled.size > 0
    assert np.allclose(arm.Z_transient[stalled], float(geom["L"]), atol=0.0)


def test_the_credit_is_per_realization_not_a_single_number() -> None:
    """lambda_out_eff is stochastic, so the credited H_c ratio must scatter."""
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    base = evaluate_batch_diagnostics(theta, rec, geom)
    arm = evaluate_batch_diagnostics(theta, rec, geom, foreland_seepage_credit=_FULL)

    ratio = arm.H_c / base.H_c
    assert ratio.std() > 1e-6, "a precomputed scalar credit would give zero spread"

    # And it is exactly phi * lambda_out_eff, realization by realization.
    lam_out = _lambda_out_eff_for(config, theta)
    expected = compute_critical_head_vectorized(
        theta, {**geom, "L": float(geom["L"]) + lam_out}
    ).H_c
    assert np.array_equal(arm.H_c, expected)


def test_the_fraction_is_honoured_linearly_in_length() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    lam_out = _lambda_out_eff_for(config, theta)
    half = evaluate_batch_diagnostics(theta, rec, geom, foreland_seepage_credit=_HALF)
    expected = compute_critical_head_vectorized(
        theta, {**geom, "L": float(geom["L"]) + _HALF * lam_out}
    ).H_c
    assert np.array_equal(half.H_c, expected)


def test_open_entry_leaves_no_foreland_to_credit() -> None:
    """ADR-0025 zeroes lambda_out_eff, so the credit is identically zero."""
    config = _make_config()
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    opened = evaluate_batch_diagnostics(theta, rec, geom, foreland_open=True)
    credited = evaluate_batch_diagnostics(
        theta, rec, geom, foreland_open=True, foreland_seepage_credit=_FULL
    )
    assert np.array_equal(opened.H_c, credited.H_c)
    assert np.array_equal(opened.failure_static, credited.failure_static)
    assert np.array_equal(opened.failure_trans, credited.failure_trans)


def test_scalar_and_batch_agree_row_for_row_under_the_credit() -> None:
    config = _make_config(n_samples=40)
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    batch = evaluate_batch_diagnostics(theta, rec, geom, foreland_seepage_credit=_FULL)
    for j in range(theta.shape[0]):
        row = evaluate_realization(theta[j], rec, geom, foreland_seepage_credit=_FULL)
        assert row.H_c == batch.H_c[j]
        assert row.l_c == batch.l_c[j]
        assert row.Z_static == batch.Z_static[j]
        assert row.Z_transient == batch.Z_transient[j]


@pytest.mark.parametrize("bad", [-0.1, 1.5])
def test_m8_refuses_a_fraction_outside_the_unit_interval(bad: float) -> None:
    config = _make_config(n_samples=20)
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        evaluate_batch(theta, rec, geom, foreland_seepage_credit=bad)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        evaluate_realization(theta[0], rec, geom, foreland_seepage_credit=bad)


def test_credit_accepted_on_both_backends() -> None:
    """Scaled in M6, upstream of the kernel, so numba is not refused."""
    numba = pytest.importorskip("numba")
    assert numba is not None
    config = _make_config(n_samples=120)
    theta = _theta_for(config)
    geom = config.geometry.as_evaluator_dict()
    rec = _stub_records(config)[-1]
    ref = evaluate_batch_diagnostics(
        theta, rec, geom, foreland_seepage_credit=_FULL, progression_backend="numpy"
    )
    jit = evaluate_batch_diagnostics(
        theta, rec, geom, foreland_seepage_credit=_FULL, progression_backend="numba"
    )
    assert np.array_equal(ref.H_c, jit.H_c)
    assert np.allclose(ref.Z_transient, jit.Z_transient, rtol=0.0, atol=1e-10)


# ---------------------------------------------------------------------------
# M1: the hash-preservation mechanism the Phase 2 replay gate depends on
# ---------------------------------------------------------------------------


def test_field_defaults_to_none_and_is_dropped_from_metadata() -> None:
    config = _make_config()
    assert config.foreland_seepage_credit is None
    assert "foreland_seepage_credit" not in config.to_metadata()


def test_hash_is_preserved_against_a_pre_adr0052_snapshot() -> None:
    """A snapshot written before the field existed must rehash identically."""
    config = _make_config()
    snapshot = config.to_metadata()
    assert Config.model_validate(snapshot).config_hash() == config.config_hash()


def test_setting_the_credit_records_it_and_moves_the_hash() -> None:
    base = _make_config()
    variant = base.model_copy(update={"foreland_seepage_credit": _FULL})
    assert variant.to_metadata()["foreland_seepage_credit"] == _FULL
    assert variant.config_hash() != base.config_hash()


@pytest.mark.parametrize("bad", [-0.1, 1.5])
def test_config_refuses_a_fraction_outside_the_unit_interval(bad: float) -> None:
    with pytest.raises(ValueError):
        _make_config(foreland_seepage_credit=bad)


def test_every_committed_config_hash_survives_the_new_field() -> None:
    """The eight production YAMLs must hash exactly as their sidecars record."""
    root = pathlib.Path(__file__).resolve().parents[1]
    configs = sorted((root / "configs").glob("*.yaml"))
    assert len(configs) == 8
    for path in configs:
        config = Config.from_yaml(path)
        assert config.foreland_seepage_credit is None
        assert "foreland_seepage_credit" not in config.to_metadata()
        # Round-tripping through the snapshot must not move the hash either.
        assert (
            Config.model_validate(config.to_metadata()).config_hash()
            == config.config_hash()
        )


# ---------------------------------------------------------------------------
# M9 / orchestrator: end-to-end threading
# ---------------------------------------------------------------------------


def test_run_threads_the_credit_and_is_bit_identical_when_unset() -> None:
    """A full sweep: unset reproduces the baseline; set moves BOTH columns."""
    base_cfg = _make_config(n_samples=200)
    kwargs = dict(n_jobs=1, progress=False, persist=False)
    base = run_fragility_analysis(base_cfg, **kwargs)
    again = run_fragility_analysis(
        base_cfg.model_copy(update={"foreland_seepage_credit": None}), **kwargs
    )
    assert np.array_equal(base.failure_matrix_stat, again.failure_matrix_stat)
    assert np.array_equal(base.failure_matrix_tran, again.failure_matrix_tran)

    arm = run_fragility_analysis(
        base_cfg.model_copy(update={"foreland_seepage_credit": _FULL}), **kwargs
    )
    assert not np.array_equal(base.failure_matrix_stat, arm.failure_matrix_stat)
    assert not np.array_equal(base.failure_matrix_tran, arm.failure_matrix_tran)
    assert arm.metadata["config"]["foreland_seepage_credit"] == _FULL


# ---------------------------------------------------------------------------
# The committed ADR-0052 evidence record
# ---------------------------------------------------------------------------

_EVIDENCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "decisions"
    / "adr0052-foreland-credit-companion.json"
)
_NOTE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "decisions"
    / "adr0052-foreland-seepage-credit-bracket.md"
)
_PREREG = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "decisions"
    / "adr0052-foreland-credit-prereg.md"
)


def _evidence() -> dict:
    assert _EVIDENCE.is_file(), (
        f"tracked evidence record missing: {_EVIDENCE.name}. It moved, was "
        "renamed or was deleted; it is not optional."
    )
    return json.loads(_EVIDENCE.read_text(encoding="utf-8"))


def test_the_committed_record_passed_its_bit_identity_gate_at_all_four() -> None:
    record = _evidence()
    gates = record["baseline_bit_identity"]
    assert len(gates) == 4
    for section, verdict in gates.items():
        assert verdict["static_matches"] is True, section
        assert verdict["transient_matches"] is True, section


def test_the_record_pins_the_preregistration_it_was_measured_against() -> None:
    """The prediction must be the one that was frozen before the arms ran."""
    import hashlib

    record = _evidence()
    assert _PREREG.is_file()
    # Decoded and re-encoded, never raw bytes: this repository is checked out
    # with line-ending translation, so a byte digest would pin the checkout
    # rather than the content.
    digest = hashlib.sha256(
        _PREREG.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    assert record["preregistration"]["sha256"] == digest


def test_the_record_shows_both_branches_moved() -> None:
    """P1: unlike ADR-0049/0050, the static column is NOT invariant."""
    record = _evidence()
    assert record["prediction_outcomes"]["P1"]["held"] is True
    moved = record["static_branch_moved"]
    assert len(moved) == 4
    for section, cells in moved.items():
        assert cells > 0, f"{section}: the static column did not move"


def test_the_record_scores_every_frozen_prediction() -> None:
    """All five predictions are scored, and the failure is recorded as one.

    P4 FAILED and the record must keep saying so: a pre-registration whose
    losing prediction quietly turns green is worth nothing.
    """
    outcomes = _evidence()["prediction_outcomes"]
    assert sorted(outcomes) == ["P1", "P2", "P3", "P4", "P5"]
    for key in ("P1", "P2", "P3", "P5"):
        assert outcomes[key]["held"] is True, key
    assert outcomes["P4"]["held"] is False
    assert outcomes["P4"]["kappa_order"] != outcomes["P4"]["max_rho_order"]


def test_the_record_shows_the_bias_widened_at_every_resolved_level() -> None:
    """P3: rho > 1 everywhere it resolves, which is the directional call."""
    p3 = _evidence()["prediction_outcomes"]["P3"]
    assert p3["levels_resolved"] > 0
    assert p3["levels_with_rho_above_one"] == p3["levels_resolved"]


def test_the_recorded_lambda_split_traces_to_the_part_1_gate() -> None:
    """The series split that motivates the ADR, reproduced in this session."""
    record = _evidence()
    # Section keys are the record's own, without the space (``KP57.4``).
    expected_r_e = {
        "KP57.4": 0.4381,
        "KP58.8": 0.4362,
        "KP60.0": 0.4170,
        "KP62.0": 0.3514,
    }
    for section, want in expected_r_e.items():
        got = record["prior_mean_baseline"][section]["r_e"]
        assert abs(got - want) < 5e-5, section


def test_the_companion_note_is_committed() -> None:
    assert _NOTE.is_file(), f"companion measurement note missing: {_NOTE.name}"
