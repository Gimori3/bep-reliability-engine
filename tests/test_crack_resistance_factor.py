"""ADR-0051: the opt-in crack-resistance override and the equal head convention.

Fast, stub-based (the synthetic record path; no d4PDF data needed). The knob is a
keyword-only, default-``None`` override of the Pol SIE 2024 Eq. (6) coefficient in
the transient erosion driver, on the additive pattern ADR-0041/0045/0049/0050
established. What is pinned here:

* **bit-identity when off** at every layer -- the M7 kernel, both progression
  backends, the scalar and batch M8 paths, and a full ``run_fragility_analysis``
  sweep;
* the **head equality** the whole experiment rests on: at factor ``0.0`` the
  transient erosion driver is the static comparator's own gross head
  ``h - z_toe``, exactly, not merely closely;
* the **channel claim**: the coefficient reaches the erosion driver alone, so the
  static failure column, the uplift/heave latches, ``H_c``, ``H_eq``, ``l_c`` and
  ``r_e`` are all invariant under it;
* the **nesting expectation** (campaign plan section 4, expectation 2): the
  gross-head transient failure set nests inside the static one;
* the **closed-form sustained-peak identity** (expectation 4): under an
  indefinitely held head the gross-head transient limit is exactly
  ``C0 and gate``, where the production limit is ``gate and (crack-reduced head >
  H_c)``;
* the **hash-preservation** mechanism the Phase 2 replay gate depends on: the
  field is dropped from ``to_metadata()`` when None, so pre-ADR-0051 config
  hashes do not move.
"""

from __future__ import annotations

import numpy as np
import pytest

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import (
    evaluate_batch,
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.gap_decomposition import sustained_peak_record
from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.progression import (
    CRACK_RESISTANCE_FACTOR,
    integrate_progression,
    progression_rate,
    resolve_crack_resistance_factor,
)
from bep_reliability_engine.run import (
    conditioning_hydrographs_for_config,
    run_fragility_analysis,
)
from bep_reliability_engine.sampling import sample_theta

_SEED = 20260626
_N = 400
_GRID = (6.0, 8.0, 10.0, 12.0, 14.0)
_DT_S = 900.0

#: The equal-head-convention arm: the contested term removed entirely.
_GROSS = 0.0


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
# M7: the resolver and the kernel
# ---------------------------------------------------------------------------


def test_resolver_returns_the_published_constant_for_none() -> None:
    """The None path is the module constant itself, not a copy of its value."""
    assert resolve_crack_resistance_factor(None) == CRACK_RESISTANCE_FACTOR
    assert resolve_crack_resistance_factor(0.3) == 0.3
    assert resolve_crack_resistance_factor(_GROSS) == 0.0


@pytest.mark.parametrize("bad", [-1e-12, -0.3, -1.0])
def test_resolver_refuses_a_negative_factor(bad: float) -> None:
    """A negative coefficient would add head above the gross outer level."""
    with pytest.raises(ValueError, match="non-negative"):
        resolve_crack_resistance_factor(bad)


def _integrate(**kwargs):
    h = np.linspace(2.0, 11.0, 80)
    return integrate_progression(
        h,
        _DT_S,
        InstantaneousHead(0.5, 2.0),
        2.0,
        c_e=0.05,
        k_aq_mps=1.0e-4,
        d_bl_m=3.0,
        gamma_bl_sub_knpm3=6.9,
        h_c_m=4.0,
        l_c_m=5.0,
        seepage_length_m=30.0,
        **kwargs,
    )


def test_kernel_default_none_and_explicit_0_3_are_bit_identical() -> None:
    base = _integrate()
    for factor in (None, CRACK_RESISTANCE_FACTOR):
        again = _integrate(crack_resistance_factor=factor)
        assert float(again.l_final_m) == float(base.l_final_m)
        assert bool(again.uplift_occurred) == bool(base.uplift_occurred)
        assert bool(again.heave_occurred) == bool(base.heave_occurred)


def test_kernel_refuses_a_negative_factor() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        _integrate(crack_resistance_factor=-0.1)


def test_gross_head_erodes_strictly_faster_and_leaves_the_gate_alone() -> None:
    """The knob moves the rate and only the rate.

    A removed head loss can only raise the erosion driver, so the pipe can only
    get longer; the uplift/heave latches read ``Delta_h_blanket``, which never
    carried the crack term (ADR-0027/0028), so they must not move at all.
    """
    base = _integrate()
    gross = _integrate(crack_resistance_factor=_GROSS)
    assert float(gross.l_final_m) > float(base.l_final_m)
    assert bool(gross.uplift_occurred) == bool(base.uplift_occurred)
    assert bool(gross.heave_occurred) == bool(base.heave_occurred)
    assert np.array_equal(
        np.asarray(gross.t_uh_s), np.asarray(base.t_uh_s), equal_nan=True
    )


# ---------------------------------------------------------------------------
# M8: bit-identity off, and the head-equality claim the experiment rests on
# ---------------------------------------------------------------------------


def _single_step_record(peak: float):
    """A one-sample record: l_e is then exactly one forward-Euler step."""

    class _Rec:
        h = np.array([peak], dtype=np.float64)
        native_dt = _DT_S

    rec = _Rec()
    rec.peak = float(peak)
    return rec


def test_factor_zero_drives_the_rate_with_the_static_comparator_head() -> None:
    """The equal-head-convention identity, read off one Euler step.

    ``tests/test_evaluator.py::test_head_convention_both_raw_differ_by_crack_term``
    pins that the production transient head sits exactly ``0.3*D_bl`` below the
    static comparator head. This is that test's mirror: at factor 0 the two heads
    coincide, so ``l_e`` is exactly the step the *static* head produces.
    """
    theta = np.array([1.0e-4, 2.0e-4, 3.0, 3.0, 1.0e-6, 16.0, 0.014])
    geometry = {
        "L": 30.0,
        "z_toe": 2.0,
        "foreshore_width": 0.0,
        "D_fore": 3.0,
        "k_fore": 1.0e-6,
    }
    peak = 14.0
    record = _single_step_record(peak)

    gross = evaluate_realization(
        theta, record, geometry, crack_resistance_factor=_GROSS
    )
    static_head = gross.H_c - gross.Z_static
    assert static_head == pytest.approx(peak - geometry["z_toe"], rel=1e-12)

    expected = _DT_S * float(
        progression_rate(static_head, 0.0, theta[6], theta[0], geometry["L"])
    )
    assert gross.l_e_final == pytest.approx(expected, rel=1e-12)

    # ... and the production run is exactly 0.3*D_bl of head below it.
    base = evaluate_realization(theta, record, geometry)
    reduced = static_head - CRACK_RESISTANCE_FACTOR * theta[3]
    assert base.l_e_final == pytest.approx(
        _DT_S * float(progression_rate(reduced, 0.0, theta[6], theta[0], 30.0)),
        rel=1e-12,
    )
    assert gross.l_e_final > base.l_e_final
    # Every shared-preamble diagnostic is untouched by the knob.
    assert gross.H_c == base.H_c
    assert gross.H_c_transient == base.H_c_transient
    assert gross.l_c == base.l_c
    assert gross.r_e == base.r_e
    assert gross.Z_static == base.Z_static


def test_scalar_default_none_is_bit_identical() -> None:
    config = _make_config(n_samples=16)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    for row in theta[:8]:
        base = evaluate_realization(row, record, geometry)
        for factor in (None, CRACK_RESISTANCE_FACTOR):
            again = evaluate_realization(
                row, record, geometry, crack_resistance_factor=factor
            )
            assert base.Z_static == again.Z_static
            assert base.Z_transient == again.Z_transient
            assert base.l_e_final == again.l_e_final


def test_batch_default_none_is_bit_identical() -> None:
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base = evaluate_batch(theta, record, geometry)
    for factor in (None, CRACK_RESISTANCE_FACTOR):
        again = evaluate_batch(theta, record, geometry, crack_resistance_factor=factor)
        assert np.array_equal(base[0], again[0])
        assert np.array_equal(base[1], again[1])


def test_static_branch_is_exactly_invariant_and_transient_is_not() -> None:
    """The channel claim, read from the code rather than asserted in prose."""
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    base = evaluate_batch_diagnostics(theta, record, geometry)
    gross = evaluate_batch_diagnostics(
        theta, record, geometry, crack_resistance_factor=_GROSS
    )
    assert np.array_equal(base.failure_static, gross.failure_static)
    assert np.array_equal(base.Z_static, gross.Z_static)
    assert np.array_equal(base.H_c, gross.H_c)
    assert np.array_equal(base.H_c_transient, gross.H_c_transient)
    assert np.array_equal(base.l_c, gross.l_c)
    assert np.array_equal(base.r_e, gross.r_e)
    assert np.array_equal(base.uplift_occurred, gross.uplift_occurred)
    assert np.array_equal(base.heave_occurred, gross.heave_occurred)
    assert not np.array_equal(base.failure_trans, gross.failure_trans)


def test_gross_head_transient_nests_inside_the_production_transient() -> None:
    """Removing a head loss can only help the pipe: the sets are ordered."""
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    for record in conditioning_hydrographs_for_config(config):
        _, base = evaluate_batch(theta, record, geometry)
        _, gross = evaluate_batch(
            theta, record, geometry, crack_resistance_factor=_GROSS
        )
        assert not np.any(base & ~gross), "a production failure stopped failing"


def test_gross_head_transient_nests_inside_the_static_set() -> None:
    """Campaign plan section 4, expectation 2, on the stub grid.

    In continuous time a gross-head transient failure needs the same head the
    static comparator needs, and time as well, so the transient set nests inside
    the static one. Any exception is a forward-Euler barrier jump (ADR-0030); at
    the stub timestep there should be none, and the production study counts them
    rather than assuming them away.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    flips = 0
    for record in conditioning_hydrographs_for_config(config):
        static, gross = evaluate_batch(
            theta, record, geometry, crack_resistance_factor=_GROSS
        )
        flips += int(np.count_nonzero(gross & ~static))
    assert flips == 0


def test_sustained_peak_limit_of_the_gross_head_transient_is_c0_and_gate() -> None:
    """Campaign plan section 4, expectation 4, in closed form.

    ADR-0040's sustained-peak limit is ``gate and (H_erosion > H_c,trans)``. With
    the crack term removed ``H_erosion`` is the static comparator's own gross
    head, so the limit collapses to ``C0 and gate`` -- the static failure column
    intersected with the heave gate. Checked on a hold long enough for the level
    to have converged.
    """
    config = _make_config()
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    peak = float(conditioning_hydrographs_for_config(config)[1].peak)
    held = sustained_peak_record(peak, dt_s=_DT_S, n_steps=4000)
    diagnostics = evaluate_batch_diagnostics(
        theta, held, geometry, crack_resistance_factor=_GROSS
    )
    gate_open = np.asarray(diagnostics.heave_occurred, dtype=bool)
    static = np.asarray(diagnostics.failure_static, dtype=bool)
    # The strict inequality of the closed form vs the engine's Z <= 0 differ only
    # on a measure-zero boundary set, which a continuous prior never lands on.
    expected = static & gate_open
    assert 0.02 < expected.mean() < 0.98, "the check must be a real comparison"
    assert np.array_equal(np.asarray(diagnostics.failure_trans), expected)


def test_factor_accepted_on_both_backends() -> None:
    """Unlike ADR-0041's end factor, this knob is not numba-refused."""
    pytest.importorskip("numba")
    config = _make_config(n_samples=64)
    theta = _theta_for(config)
    geometry = config.geometry.as_evaluator_dict()
    record = conditioning_hydrographs_for_config(config)[-1]
    ref = evaluate_batch_diagnostics(
        theta, record, geometry, crack_resistance_factor=_GROSS
    )
    jit = evaluate_batch_diagnostics(
        theta,
        record,
        geometry,
        crack_resistance_factor=_GROSS,
        progression_backend="numba",
    )
    np.testing.assert_allclose(jit.l_e_final, ref.l_e_final, rtol=1e-10, atol=1e-10)
    # And the numba baseline is unmoved when the knob is off.
    off = evaluate_batch_diagnostics(
        theta,
        record,
        geometry,
        crack_resistance_factor=None,
        progression_backend="numba",
    )
    plain = evaluate_batch_diagnostics(
        theta, record, geometry, progression_backend="numba"
    )
    assert np.array_equal(off.l_e_final, plain.l_e_final)


# ---------------------------------------------------------------------------
# M1: the hash-preservation mechanism the Phase 2 replay gate depends on
# ---------------------------------------------------------------------------


def test_field_defaults_to_none_and_is_dropped_from_metadata() -> None:
    config = _make_config()
    assert config.crack_resistance_factor is None
    assert "crack_resistance_factor" not in config.to_metadata()


def test_hash_is_preserved_against_a_pre_adr0051_snapshot() -> None:
    """A snapshot written before the field existed must rehash identically."""
    config = _make_config()
    snapshot = config.to_metadata()
    assert Config.model_validate(snapshot).config_hash() == config.config_hash()


def test_setting_the_factor_records_it_and_moves_the_hash() -> None:
    base = _make_config()
    variant = base.model_copy(update={"crack_resistance_factor": _GROSS})
    assert variant.to_metadata()["crack_resistance_factor"] == _GROSS
    assert variant.config_hash() != base.config_hash()


@pytest.mark.parametrize("bad", [-1e-6, -0.3])
def test_config_refuses_a_negative_factor(bad: float) -> None:
    with pytest.raises(ValueError):
        _make_config(crack_resistance_factor=bad)


def test_config_accepts_zero_which_is_the_whole_experiment() -> None:
    assert _make_config(crack_resistance_factor=0.0).crack_resistance_factor == 0.0


# ---------------------------------------------------------------------------
# M9 / orchestrator: end-to-end threading
# ---------------------------------------------------------------------------


def test_run_threads_the_factor_and_is_bit_identical_when_unset() -> None:
    """A full sweep: unset reproduces the baseline; set moves transient only."""
    base_cfg = _make_config(n_samples=200)
    kwargs = dict(n_jobs=1, progress=False, persist=False)
    base = run_fragility_analysis(base_cfg, **kwargs)
    again = run_fragility_analysis(
        base_cfg.model_copy(update={"crack_resistance_factor": None}), **kwargs
    )
    assert np.array_equal(base.failure_matrix_stat, again.failure_matrix_stat)
    assert np.array_equal(base.failure_matrix_tran, again.failure_matrix_tran)

    arm = run_fragility_analysis(
        base_cfg.model_copy(update={"crack_resistance_factor": _GROSS}), **kwargs
    )
    assert np.array_equal(base.failure_matrix_stat, arm.failure_matrix_stat)
    assert not np.array_equal(base.failure_matrix_tran, arm.failure_matrix_tran)
    assert arm.metadata["config"]["crack_resistance_factor"] == _GROSS
    # Nesting again, this time through the orchestrator's own matrices.
    assert not np.any(base.failure_matrix_tran & ~arm.failure_matrix_tran)
    assert not np.any(arm.failure_matrix_tran & ~arm.failure_matrix_stat)
