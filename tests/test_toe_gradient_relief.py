"""ADR-0050: the opt-in landside-toe gradient relief and the drained bracket.

Fast, stub-based (the synthetic record path; no d4PDF data needed). The knob is
a keyword-only, default-``None`` relief on the exit gradient, in the same
additive pattern ADR-0041 established for the equilibrium end factor, ADR-0045
for the model factor ``m_p`` and ADR-0049 for the critical pipe length. What is
pinned here:

* **bit-identity when off** at every layer -- both M8 entry points, the scalar
  path and a full ``run_fragility_analysis`` sweep -- for ``None`` and for the
  explicit no-op ``1.0``;
* the **hash-preservation** mechanism the Phase 2 replay gate depends on: the
  field is dropped from ``to_metadata()`` when None, so pre-ADR-0050 config
  hashes do not move;
* the structural claim the whole bracket rests on: since ADR-0028 ``r_e``
  reaches the uplift/heave gate and nothing else, so the **static branch is
  exactly invariant** under any relief factor while the transient branch is
  not. This is the study's falsifier, checked here on a stub and enforced again
  by the driver on the production sections;
* that the relief scales the exit gradient by **exactly** the factor, which is
  what makes the number a statement about the quantity PWRI 2014 Table 7.1.1
  names rather than about an arbitrary knob;
* **one-sidedness and monotonicity**: less relief never raises the transient
  probability, and factors outside ``(0, 1]`` are refused rather than silently
  extrapolated into an aggravation the guidance does not license.
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
from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    LaggedHead,
    translate_instantaneous,
)
from bep_reliability_engine.initiation import z_heave
from bep_reliability_engine.run import (
    conditioning_hydrographs_for_config,
    run_fragility_analysis,
)
from bep_reliability_engine.sampling import sample_theta

_SEED = 20260626
_N = 400
_GRID = (6.0, 8.0, 10.0, 12.0, 14.0)
_DT_S = 900.0

#: A relief strong enough to move the transient branch on the stub grid.
_FACTOR = 0.5

#: The ladder the drained-configuration bracket sweeps
#: (``scripts/drained_configuration_bracket.py``).
_LADDER = (0.8, 0.6, 0.4, 0.2)


def _make_config(
    *, n_samples: int = _N, conditioning_grid=_GRID, **overrides
) -> Config:
    """Small, fast stub Config (mirrors tests/test_critical_length_factor.py)."""
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
# The physical identity: the relief scales the exit gradient, exactly
# ---------------------------------------------------------------------------


def test_the_relief_scales_the_exit_gradient_by_exactly_the_factor() -> None:
    """The claim that makes this a statement about the guidance's quantity.

    PWRI 2014 Table 7.1.1 names "the hydraulic gradient at the landside toe"
    as what a drain acts upon. In this engine that quantity is
    ``i_exit = Delta_h_blanket / D_bl`` inside ``z_heave``. Scaling ``r_e``
    scales it by the same factor at every stage, which is what licenses
    reading the factor as a gradient relief rather than as an abstract knob.

    Exact in exact arithmetic; checked to a relative 1e-12 because the head
    model forms the overpressure by adding and subtracting the datum
    ``z_toe``, which costs a few ulps whether or not a relief is applied.
    """
    r_e = np.array([0.20, 0.436, 0.75])
    z_toe, d_bl, gamma = 38.5, 0.85, 6.9
    for stage in (39.0, 41.03, 45.0):
        base = translate_instantaneous(stage, r_e, z_toe) - z_toe
        for factor in _LADDER:
            relieved = translate_instantaneous(stage, r_e * factor, z_toe) - z_toe
            np.testing.assert_allclose(relieved, base * factor, rtol=1e-12, atol=0.0)
            # and therefore the gradient margin moves as the gradient does
            i_base = base / d_bl
            i_relieved = relieved / d_bl
            np.testing.assert_allclose(
                gamma / 9.81 - i_relieved,
                z_heave(relieved, gamma, d_bl),
                rtol=1e-12,
                atol=0.0,
            )
            np.testing.assert_allclose(
                i_relieved, i_base * factor, rtol=1e-12, atol=0.0
            )


def test_the_relief_is_exact_under_the_lagged_head_model_too() -> None:
    """The lag state is linear in the equilibrium target, so it scales as well.

    The lag form is off in production (ADR-0032), but the knob must not be
    silently wrong there: a future run with the lag active would otherwise get
    a relief that is exact at equilibrium and wrong in between.
    """
    r_e = np.array([0.30, 0.55])
    z_toe, tau = 38.5, 3600.0
    stages = [39.0, 40.5, 42.0, 41.0, 39.5]
    for factor in _LADDER:
        base_model = LaggedHead(r_e, z_toe, tau)
        arm_model = LaggedHead(r_e * factor, z_toe, tau)
        base_model.reset(stages[0])
        arm_model.reset(stages[0])
        for stage in stages:
            base = base_model.step(stage, 900.0) - z_toe
            arm = arm_model.step(stage, 900.0) - z_toe
            np.testing.assert_allclose(arm, base * factor, rtol=1e-11, atol=0.0)


def test_the_instantaneous_head_model_carries_the_scaled_factor() -> None:
    """A guard that the seam is the head model and not something downstream."""
    r_e = np.array([0.25, 0.60])
    z_toe = 38.5
    plain = InstantaneousHead(r_e * 0.4, z_toe).step(42.0, 0.0)
    expected = translate_instantaneous(42.0, r_e * 0.4, z_toe)
    np.testing.assert_allclose(plain, expected, rtol=0.0, atol=0.0)


# ---------------------------------------------------------------------------
# M8: bit-identity off, and the gate-only channel claim
# ---------------------------------------------------------------------------


def test_batch_default_none_and_unity_are_bit_identical() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base = evaluate_batch(theta, record, geometry)
    for factor in (None, 1.0):
        again = evaluate_batch(
            theta, record, geometry, toe_gradient_relief_factor=factor
        )
        assert np.array_equal(base[0], again[0])
        assert np.array_equal(base[1], again[1])


def test_scalar_default_none_and_unity_are_bit_identical() -> None:
    config = _make_config(n_samples=16)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    for row in theta[:8]:
        base = evaluate_realization(row, record, geometry)
        for factor in (None, 1.0):
            again = evaluate_realization(
                row, record, geometry, toe_gradient_relief_factor=factor
            )
            assert base.Z_static == again.Z_static
            assert base.Z_transient == again.Z_transient
            assert base.r_e == again.r_e


def test_static_branch_is_exactly_invariant_and_transient_is_not() -> None:
    """The falsifier of the whole bracket, read from the code.

    Since ADR-0028 the r_e-attenuated blanket overpressure reaches the
    uplift/heave gate and nothing else: both piping heads are r_e-independent
    and the static comparator is entirely r_e-independent. So the static
    failure column must be **bit-identical** under any relief, while the
    transient column must actually move -- otherwise the bracket would be
    measuring a knob that does nothing.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base_static, base_trans = evaluate_batch(theta, record, geometry)
    moved = False
    for factor in _LADDER:
        static, trans = evaluate_batch(
            theta, record, geometry, toe_gradient_relief_factor=factor
        )
        assert np.array_equal(base_static, static), factor
        moved = moved or not np.array_equal(base_trans, trans)
    assert moved, "the relief must move the transient branch on the stub grid"


def test_the_relief_is_one_sided_and_monotone() -> None:
    """Prediction P2: less relief never raises the transient probability.

    The gate is a necessary condition for erosion and a row that never latches
    never erodes, so the effect can only be one-sided. Checked as set
    inclusion, which is stronger than a comparison of the column means: every
    row that fails under a smaller factor must also fail under a larger one.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    previous = evaluate_batch(theta, record, geometry)[1]
    for factor in _LADDER:
        trans = evaluate_batch(
            theta, record, geometry, toe_gradient_relief_factor=factor
        )[1]
        assert not np.any(trans & ~previous), (
            f"relief {factor} made a realization fail that did not fail at the "
            "weaker relief above it; the gate effect must be one-sided"
        )
        previous = trans


def test_diagnostics_report_the_unrelieved_physical_response_factor() -> None:
    """r_e is a blanket-aquifer property; the drain credit is not part of it.

    Conflating them would make a scenario run's leakage diagnostics unreadable
    and would silently redefine a field Phase 2 reads.
    """
    config = _make_config(n_samples=64)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base = evaluate_batch_diagnostics(theta, record, geometry)
    relieved = evaluate_batch_diagnostics(
        theta, record, geometry, toe_gradient_relief_factor=_FACTOR
    )
    assert np.array_equal(base.r_e, relieved.r_e)
    assert np.array_equal(base.H_c, relieved.H_c)
    assert np.array_equal(base.l_c, relieved.l_c)
    assert np.array_equal(base.lambda_in, relieved.lambda_in)
    # ... and the transient margin did move, so the invariance above is not
    # the trivial consequence of a no-op.
    assert not np.array_equal(base.Z_transient, relieved.Z_transient)


@pytest.mark.parametrize("bad", [0.0, -0.5, 1.0001, 2.0])
def test_m8_refuses_a_factor_outside_the_licensed_interval(bad: float) -> None:
    """One-sided by construction; 0 would assert a perfect drain, not bracket."""
    config = _make_config(n_samples=16)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    with pytest.raises(ValueError, match=r"\(0, 1\]"):
        evaluate_batch(theta, record, geometry, toe_gradient_relief_factor=bad)
    with pytest.raises(ValueError, match=r"\(0, 1\]"):
        evaluate_realization(theta[0], record, geometry, toe_gradient_relief_factor=bad)


def test_factor_accepted_on_both_backends() -> None:
    """The scaling happens upstream of the timestepper, so the JIT sees it too."""
    pytest.importorskip("numba")
    config = _make_config(n_samples=64)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    ref = evaluate_batch_diagnostics(
        theta, record, geometry, toe_gradient_relief_factor=_FACTOR
    )
    jit = evaluate_batch_diagnostics(
        theta,
        record,
        geometry,
        toe_gradient_relief_factor=_FACTOR,
        progression_backend="numba",
    )
    np.testing.assert_allclose(jit.l_e_final, ref.l_e_final, rtol=1e-10, atol=1e-10)


# ---------------------------------------------------------------------------
# M1: the hash-preservation mechanism the Phase 2 replay gate depends on
# ---------------------------------------------------------------------------


def test_field_defaults_to_none_and_is_dropped_from_metadata() -> None:
    config = _make_config()
    assert config.toe_gradient_relief_factor is None
    assert "toe_gradient_relief_factor" not in config.to_metadata()


def test_hash_is_preserved_against_a_pre_adr0050_snapshot() -> None:
    """A snapshot written before the field existed must rehash identically."""
    config = _make_config()
    snapshot = config.to_metadata()
    assert Config.model_validate(snapshot).config_hash() == config.config_hash()


def test_setting_the_factor_records_it_and_moves_the_hash() -> None:
    base = _make_config()
    variant = base.model_copy(update={"toe_gradient_relief_factor": _FACTOR})
    assert variant.to_metadata()["toe_gradient_relief_factor"] == _FACTOR
    assert variant.config_hash() != base.config_hash()


@pytest.mark.parametrize("bad", [0.0, -1.0, 1.5])
def test_config_refuses_a_factor_outside_the_licensed_interval(bad: float) -> None:
    with pytest.raises(ValueError):
        _make_config(toe_gradient_relief_factor=bad)


def test_every_committed_production_config_leaves_the_knob_off() -> None:
    """Production never carries it; this is what keeps the eight hashes fixed."""
    configs = sorted(
        (pathlib.Path(__file__).resolve().parents[1] / "configs").glob("*.yaml")
    )
    assert configs, "tracked configs/ is empty"
    for path in configs:
        config = Config.from_yaml(path)
        assert config.toe_gradient_relief_factor is None, path.name
        assert "toe_gradient_relief_factor" not in config.to_metadata(), path.name


# ---------------------------------------------------------------------------
# M9 / orchestrator: end-to-end threading
# ---------------------------------------------------------------------------


def test_run_threads_the_factor_and_is_bit_identical_when_unset() -> None:
    """A full sweep: unset reproduces the baseline; set moves transient only."""
    base_cfg = _make_config(n_samples=200)
    kwargs = dict(n_jobs=1, progress=False, persist=False)
    base = run_fragility_analysis(base_cfg, **kwargs)
    for factor in (None, 1.0):
        again = run_fragility_analysis(
            base_cfg.model_copy(update={"toe_gradient_relief_factor": factor}),
            **kwargs,
        )
        assert np.array_equal(base.failure_matrix_stat, again.failure_matrix_stat)
        assert np.array_equal(base.failure_matrix_tran, again.failure_matrix_tran)

    arm = run_fragility_analysis(
        base_cfg.model_copy(update={"toe_gradient_relief_factor": _FACTOR}), **kwargs
    )
    assert np.array_equal(base.failure_matrix_stat, arm.failure_matrix_stat)
    assert not np.array_equal(base.failure_matrix_tran, arm.failure_matrix_tran)
    assert arm.metadata["config"]["toe_gradient_relief_factor"] == _FACTOR


# ---------------------------------------------------------------------------
# The committed ADR-0050 evidence record
# ---------------------------------------------------------------------------

_EVIDENCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "decisions"
    / "adr0050-drained-configuration-bracket.json"
)


def _evidence() -> dict:
    assert _EVIDENCE.is_file(), (
        f"tracked evidence record missing: {_EVIDENCE.name}. It moved, was "
        "renamed or was deleted; it is not optional."
    )
    return json.loads(_EVIDENCE.read_text(encoding="utf-8"))


def test_the_committed_record_passed_its_bit_identity_gate_everywhere() -> None:
    """No arm number is quotable against a baseline that did not reproduce."""
    sections = _evidence()["sections"]
    assert sections, "the record carries no section"
    for section in sections:
        assert section["gate_status"] == "bit_identical", section["section"]


def test_the_record_shows_the_static_branch_never_moved_under_relief() -> None:
    """Prediction P1, as measured rather than said.

    The driver refuses to write a record at all if a single static cell moves
    under a relief arm, so a record that exists is already the assertion; this
    pins the visible consequence. The berm arm is deliberately exempt: L enters
    H_c and Z = L - l_e, so it moves both branches (prediction P3), and a test
    that demanded static invariance there would be asserting something false.
    """
    for section in _evidence()["sections"]:
        for name, arm in section["arms"].items():
            if not arm["gate_only"]:
                continue
            for level in arm["levels"]:
                ratio = level["ratio_static"]
                assert ratio is None or ratio == 1.0, (
                    f"{section['section']} {name}: static ratio {ratio} at "
                    f"{level['stage_m_msl']} m"
                )


def test_the_recorded_berm_lengths_trace_to_the_adr0047_measurement() -> None:
    """The one arm with a magnitude must keep the provenance of that magnitude."""
    expected = {"KP58.8": 42.0, "KP60.0": 43.0}
    seen = {}
    for section in _evidence()["sections"]:
        seen[section["section"]] = section["seepage_length_dem_m"]
        assert section["seepage_length_source"].startswith("ADR-0047")
    assert seen == expected


def test_the_record_states_that_no_relief_magnitude_was_assumed() -> None:
    """The hard constraint of this study, pinned so it cannot quietly lapse."""
    grounding = _evidence()["grounding"]
    assert grounding["relief_magnitude_grounded"] is False
    assert grounding["relief_axis_treatment"] == "swept"
    assert "pwri_2014" in grounding["mapping_source"].lower().replace(" ", "_")
    # PWRI's 0.3 drain design gradient is recorded as a sourced observation and
    # must never become an arm: it governs the drain body, not the foundation
    # blanket exit gradient, and the guidance states no equivalence.
    assert grounding["pwri_drain_design_gradient_not_an_arm"] == 0.3
    assert 0.3 not in set(grounding["relief_ladder"])


def test_every_recorded_monotonicity_violation_is_an_euler_artifact() -> None:
    """The amended P2: violations are allowed, surviving ones are not.

    Relief delays the gate, so a relieved realization meets its first active
    timestep at a higher head and takes a larger step; at 225 s a marginal row
    deep in the C_e and k_aq tails can clear the H_eq barrier in one step
    (ADR-0030). The driver re-integrates every violation on a halved grid and
    refuses if one survives, so a record that exists already carries the
    assertion. This pins the visible consequence, and pins that the refinement
    ladder was actually walked rather than the field being defaulted.
    """
    for section in _evidence()["sections"]:
        for name, arm in section["arms"].items():
            monotonicity = arm["monotonicity"]
            assert monotonicity["violations"] == len(monotonicity["rows"])
            for row in monotonicity["rows"]:
                assert row["verdict"] == "euler_artifact", (
                    f"{section['section']} {section['d70_interpretation']} "
                    f"{name}: row {row['row']} at {row['stage_m_msl']} m is not "
                    "a discretisation artifact"
                )
                assert row["refinement_ladder"], "no refinement ladder recorded"
                assert not any(step["inverted"] for step in row["refinement_ladder"])
