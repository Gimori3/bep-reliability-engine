"""ADR-0049: the opt-in critical-pipe-length bracket on Pol SIE 2024 Eq. (13).

Fast, stub-based (the synthetic record path; no d4PDF data needed). The knob is
a keyword-only, default-``None`` multiplicative override on ``l_c`` in the same
additive pattern ADR-0041 established for the equilibrium end factor and
ADR-0045 for the model factor ``m_p``. What is pinned here:

* **bit-identity when off** at every layer -- M6 kernel, both M6 entry points,
  the scalar and batch M8 paths, and a full ``run_fragility_analysis`` sweep;
* the **hash-preservation** mechanism the Phase 2 replay gate depends on: the
  field is dropped from ``to_metadata()`` when None, so pre-ADR-0049 config
  hashes do not move;
* the structural claim the bracket study rests on: ``l_c`` reaches nothing but
  the M7 equilibrium curve, so the **static branch is exactly invariant** under
  any factor while the transient branch is not;
* the knob works on **both** progression backends (unlike the ADR-0041 end
  factor, whose constant is baked into the JIT kernel): here ``l_c`` is scaled
  upstream and the kernel receives it as an input array.
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
from bep_reliability_engine.gap_decomposition import sustained_peak_record
from bep_reliability_engine.run import (
    conditioning_hydrographs_for_config,
    run_fragility_analysis,
)
from bep_reliability_engine.sampling import sample_theta
from bep_reliability_engine.sellmeijer import (
    compute_critical_head,
    compute_critical_head_vectorized,
    compute_critical_pipe_length,
)

_SEED = 20260626
_N = 400
_GRID = (6.0, 8.0, 10.0, 12.0, 14.0)
_DT_S = 900.0

#: A factor far enough from 1 to move the transient branch on the stub grid.
_FACTOR = 1.5

#: The two study arms (see ``scripts/critical_length_bracket_study.py``): the
#: DgFlow 3D hole-exit critical length relative to Eq. (13) at the in-domain
#: S2-2 geometry, and its reciprocal.
_ARM_UPPER = 1.5557536024418221
_ARM_LOWER = 0.6427753073690184


def _make_config(
    *, n_samples: int = _N, conditioning_grid=_GRID, **overrides
) -> Config:
    """Small, fast stub Config (mirrors tests/test_gap_decomposition.py)."""
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
# M6: the kernel and both entry points
# ---------------------------------------------------------------------------


def test_critical_pipe_length_default_and_none_are_bit_identical() -> None:
    """The published Eq. (13) value survives the added keyword untouched."""
    d_aq = np.array([1.0, 3.0, 7.5, 20.0])
    base = compute_critical_pipe_length(d_aq, 30.0)
    assert np.array_equal(
        base, compute_critical_pipe_length(d_aq, 30.0, critical_length_factor=None)
    )
    assert np.array_equal(
        base, compute_critical_pipe_length(d_aq, 30.0, critical_length_factor=1.0)
    )


def test_critical_pipe_length_scales_exactly() -> None:
    """The override is a pure multiplier on Eq. (13), not a reparameterisation."""
    d_aq = np.array([1.0, 3.0, 7.5, 20.0])
    base = compute_critical_pipe_length(d_aq, 30.0)
    for factor in (0.5, _ARM_LOWER, _ARM_UPPER, 2.0):
        np.testing.assert_allclose(
            compute_critical_pipe_length(d_aq, 30.0, critical_length_factor=factor),
            base * factor,
            rtol=0.0,
            atol=0.0,
        )


@pytest.mark.parametrize("bad", [0.0, -1.0, -0.25])
def test_critical_pipe_length_refuses_non_positive_factor(bad: float) -> None:
    """l_c <= 0 has no rising H_eq branch; the kernel refuses before dividing."""
    with pytest.raises(ValueError, match="strictly positive"):
        compute_critical_pipe_length(3.0, 30.0, critical_length_factor=bad)


def test_both_m6_entry_points_forward_the_factor_and_leave_H_c_alone() -> None:
    """H_c has no l_c dependence; the two entry points must not drift apart."""
    theta = _theta_for(_make_config(n_samples=32))
    geometry = {"L": 30.0}
    base_v = compute_critical_head_vectorized(theta, geometry)
    scaled_v = compute_critical_head_vectorized(
        theta, geometry, critical_length_factor=_FACTOR
    )
    assert np.array_equal(base_v.H_c, scaled_v.H_c)
    np.testing.assert_allclose(scaled_v.l_c, base_v.l_c * _FACTOR, rtol=0.0, atol=0.0)

    base_s = compute_critical_head(theta[0], geometry)
    scaled_s = compute_critical_head(theta[0], geometry, critical_length_factor=_FACTOR)
    assert scaled_s.H_c == base_s.H_c
    assert scaled_s.l_c == pytest.approx(base_s.l_c * _FACTOR, rel=0.0, abs=1e-15)
    # the scalar and vectorized paths agree under the override too
    assert scaled_s.l_c == pytest.approx(float(scaled_v.l_c[0]), rel=0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# M8: bit-identity off, and the transient-only channel claim
# ---------------------------------------------------------------------------


def test_batch_default_none_is_bit_identical() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base = evaluate_batch(theta, record, geometry)
    for factor in (None, 1.0):
        again = evaluate_batch(theta, record, geometry, critical_length_factor=factor)
        assert np.array_equal(base[0], again[0])
        assert np.array_equal(base[1], again[1])


def test_scalar_default_none_is_bit_identical() -> None:
    config = _make_config(n_samples=16)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    for row in theta[:8]:
        base = evaluate_realization(row, record, geometry)
        again = evaluate_realization(row, record, geometry, critical_length_factor=None)
        assert base.Z_static == again.Z_static
        assert base.Z_transient == again.Z_transient
        assert base.l_c == again.l_c


def test_static_branch_is_exactly_invariant_and_transient_is_not() -> None:
    """The channel claim the bracket study rests on, read from the code.

    ``l_c`` enters the M7 equilibrium curve and nothing else: it does not
    reach H_c, r_e, the uplift/heave gate or the static comparator. So the
    static failure column must be **bit-identical** under any factor, while
    the transient column must actually move -- otherwise the study would be
    measuring a knob that does nothing.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base_static, base_trans = evaluate_batch(theta, record, geometry)
    moved = False
    for factor in (_ARM_LOWER, _ARM_UPPER):
        static, trans = evaluate_batch(
            theta, record, geometry, critical_length_factor=factor
        )
        assert np.array_equal(base_static, static)
        moved = moved or not np.array_equal(base_trans, trans)
    assert moved, "the bracket must move the transient branch on the stub grid"


def test_diagnostics_report_the_l_c_actually_used() -> None:
    """A scaled run must not report the unscaled l_c (silent-drift guard)."""
    config = _make_config(n_samples=64)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base = evaluate_batch_diagnostics(theta, record, geometry)
    scaled = evaluate_batch_diagnostics(
        theta, record, geometry, critical_length_factor=_FACTOR
    )
    np.testing.assert_allclose(scaled.l_c, base.l_c * _FACTOR, rtol=0.0, atol=0.0)
    assert np.array_equal(base.H_c, scaled.H_c)
    assert np.array_equal(base.r_e, scaled.r_e)


def test_the_two_arms_do_not_collapse_onto_each_other() -> None:
    """Sanity on direction: the arms bracket the baseline, not repeat it."""
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    _, lo = evaluate_batch(theta, record, geometry, critical_length_factor=_ARM_LOWER)
    _, hi = evaluate_batch(theta, record, geometry, critical_length_factor=_ARM_UPPER)
    assert not np.array_equal(lo, hi)


def test_sustained_peak_indicator_is_l_c_invariant_where_the_hold_converges() -> None:
    """Under an indefinitely held head the bracket does nothing at all.

    The ADR-0040 closed form for the sustained-peak limit is ``gate and
    H_erosion > H_c,trans``, and ``l_c`` appears nowhere in it. The reason is
    geometric: ``H_eq`` is linear through (0, 0), (l_c, H_c) and (L, 0.9 H_c),
    so its maximum is ``H_c`` at ``l_c`` whatever ``l_c`` is. A head above that
    maximum runs away from any starting length; a head below it stalls at
    ``l_eq = l_c * H_erosion / H_c``, which moves with ``l_c`` but never
    breaches.

    The whole effect of the critical pipe length is therefore on the *time* the
    traverse takes, not on whether the traverse is possible, which is what puts
    it inside the temporal step of the comparator ladder exactly as the
    equilibrium end anchor sits there. Checked here on a mid-curve level whose
    finite hold has converged, across factors spanning a factor of sixteen.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    peak = float(conditioning_hydrographs_for_config(config)[1].peak)
    held = sustained_peak_record(peak, dt_s=_DT_S, n_steps=1200)
    base_static, base_trans = evaluate_batch(theta, held, geometry)
    # A non-degenerate split, so the identity below is a real comparison and
    # not two all-True columns.
    assert 0.05 < base_trans.mean() < 0.95
    for factor in (0.25, _ARM_LOWER, _ARM_UPPER, 4.0):
        static, trans = evaluate_batch(
            theta, held, geometry, critical_length_factor=factor
        )
        assert np.array_equal(base_static, static)
        assert np.array_equal(base_trans, trans), (
            f"the sustained-peak indicator moved under l_c x {factor}; the "
            "closed-form limit is l_c-independent"
        )


def test_sustained_peak_invariance_holds_deep_in_the_tail_too() -> None:
    """The same invariance where the finite hold has *not* converged.

    Deep in the tail the marginal realizations are the ones whose erosion head
    sits closest to the barrier, so they take longest to traverse and a hold a
    test can afford has not converged there. The indicator is nevertheless
    unmoved across the study bracket, which says the residual non-convergence
    is not what the bracket acts on: the measured effect under real hydrographs
    comes from the *shape* of the finite loading window, not from a level the
    hold has failed to resolve.

    Stated as a bracket property, not a universal one. The invariance is
    checked over the two arms the study actually uses; the companion note
    records what a factor-four shortening does, which is outside this range and
    outside the range any published case supports.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    peak = float(conditioning_hydrographs_for_config(config)[0].peak)
    held = sustained_peak_record(peak, dt_s=_DT_S, n_steps=1200)
    base_static, base_trans = evaluate_batch(theta, held, geometry)
    assert base_trans.any(), "the deep-tail level must load something"
    for factor in (_ARM_LOWER, _ARM_UPPER):
        static, trans = evaluate_batch(
            theta, held, geometry, critical_length_factor=factor
        )
        assert np.array_equal(base_static, static)
        assert np.array_equal(base_trans, trans)


def test_factor_accepted_on_both_backends() -> None:
    """Unlike ADR-0041's end factor, this knob is not numba-refused.

    The scaling happens in M6, upstream of the timestepper, and the JIT kernel
    receives ``l_c`` as an input array -- so both backends see the same
    equilibrium curve.
    """
    pytest.importorskip("numba")
    config = _make_config(n_samples=64)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    ref = evaluate_batch_diagnostics(
        theta, record, geometry, critical_length_factor=_FACTOR
    )
    jit = evaluate_batch_diagnostics(
        theta,
        record,
        geometry,
        critical_length_factor=_FACTOR,
        progression_backend="numba",
    )
    np.testing.assert_allclose(jit.l_e_final, ref.l_e_final, rtol=1e-10, atol=1e-10)


# ---------------------------------------------------------------------------
# M1: the hash-preservation mechanism the Phase 2 replay gate depends on
# ---------------------------------------------------------------------------


def test_field_defaults_to_none_and_is_dropped_from_metadata() -> None:
    config = _make_config()
    assert config.critical_length_factor is None
    assert "critical_length_factor" not in config.to_metadata()


def test_hash_is_preserved_against_a_pre_adr0049_snapshot() -> None:
    """A snapshot written before the field existed must rehash identically."""
    config = _make_config()
    snapshot = config.to_metadata()
    assert Config.model_validate(snapshot).config_hash() == config.config_hash()


def test_setting_the_factor_records_it_and_moves_the_hash() -> None:
    base = _make_config()
    variant = base.model_copy(update={"critical_length_factor": _FACTOR})
    assert variant.to_metadata()["critical_length_factor"] == _FACTOR
    assert variant.config_hash() != base.config_hash()


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_config_refuses_a_non_positive_factor(bad: float) -> None:
    with pytest.raises(ValueError):
        _make_config(critical_length_factor=bad)


# ---------------------------------------------------------------------------
# M9 / orchestrator: end-to-end threading
# ---------------------------------------------------------------------------


def test_run_threads_the_factor_and_is_bit_identical_when_unset() -> None:
    """A full sweep: unset reproduces the baseline; set moves transient only."""
    base_cfg = _make_config(n_samples=200)
    kwargs = dict(n_jobs=1, progress=False, persist=False)
    base = run_fragility_analysis(base_cfg, **kwargs)
    again = run_fragility_analysis(
        base_cfg.model_copy(update={"critical_length_factor": None}), **kwargs
    )
    assert np.array_equal(base.failure_matrix_stat, again.failure_matrix_stat)
    assert np.array_equal(base.failure_matrix_tran, again.failure_matrix_tran)

    arm = run_fragility_analysis(
        base_cfg.model_copy(update={"critical_length_factor": _FACTOR}), **kwargs
    )
    assert np.array_equal(base.failure_matrix_stat, arm.failure_matrix_stat)
    assert not np.array_equal(base.failure_matrix_tran, arm.failure_matrix_tran)
    assert arm.metadata["config"]["critical_length_factor"] == _FACTOR


# ---------------------------------------------------------------------------
# The committed ADR-0049 evidence record
# ---------------------------------------------------------------------------

_EVIDENCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "decisions"
    / "adr0049-critical-length-companion.json"
)
_NOTE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "decisions"
    / "adr0049-critical-length-bracket.md"
)


def _evidence() -> dict:
    assert _EVIDENCE.is_file(), (
        f"tracked evidence record missing: {_EVIDENCE.name}. It moved, was "
        "renamed or was deleted; it is not optional."
    )
    return json.loads(_EVIDENCE.read_text(encoding="utf-8"))


def test_the_committed_record_passed_its_bit_identity_gate_at_all_four() -> None:
    """No arm number is quotable against a baseline that did not reproduce."""
    sections = _evidence()["sections"]
    assert len(sections) == 4
    for section in sections:
        assert section["gate_status"] == "bit_identical", section["section"]


def test_the_recorded_bracket_still_traces_to_its_two_published_values() -> None:
    """The range is derived, not pasted, and must stay derived."""
    bracket = _evidence()["bracket"]
    expected_upper = 1.36 / float(compute_critical_pipe_length(1.0, 3.0))
    assert bracket["upper_factor"] == pytest.approx(expected_upper, rel=1e-5)
    assert bracket["lower_factor"] == pytest.approx(1.0 / expected_upper, rel=1e-5)
    # The out-of-domain corroboration is a direction check only, and it also
    # sits above the formula; if it ever came out below, the note's claim that
    # both empirical anchors are on the upper side would be wrong.
    assert bracket["direction_check_b25_245"]["factor"] > 1.0


def test_the_record_shows_the_static_branch_never_moved() -> None:
    """The channel claim the whole study rests on, as measured rather than said.

    The driver refuses to write a record at all if a single static cell moves,
    so a record that exists is already the assertion; this pins the visible
    consequence, that every recorded static ratio is exactly 1.
    """
    for section in _evidence()["sections"]:
        for arm in section["arms"].values():
            for level in arm["levels"]:
                ratio = level["ratio_static"]
                assert ratio is None or ratio == 1.0, (
                    section["section"],
                    level["stage_m_msl"],
                )


def test_the_record_confirms_the_exact_reciprocal_identity() -> None:
    """With the static branch invariant, rho is the reciprocal transient move."""
    for section in _evidence()["sections"]:
        for arm, verdict in section["cancellation"].items():
            error = verdict["max_reciprocal_identity_error"]
            assert error is not None and error < 1e-12, (section["section"], arm)


def test_the_record_shows_no_euler_barrier_jump_rows_in_either_arm() -> None:
    """A shorter l_c puts the barrier fewer metres away (ADR-0030 hazard)."""
    for section in _evidence()["sections"]:
        for arm, verdict in section["cancellation"].items():
            assert verdict["trans_not_static_rows_baseline"] == 0
            assert verdict["trans_not_static_rows_arm"] == 0, (
                section["section"],
                arm,
            )


def test_the_companion_note_is_committed() -> None:
    assert _NOTE.is_file(), f"tracked companion note missing: {_NOTE.name}"
