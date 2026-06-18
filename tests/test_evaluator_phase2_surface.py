"""Phase 2 import-surface stability test for M8 (spec §8).

This is an **interface-stability** test, not a physics test. It pins the
contract Phase 2 depends on (spec §8, §9 point 1): ``evaluate_realization`` is
importable as a clean top-level symbol with no notebook or orchestrator
context, is callable per prior theta row against the 2016 hydrograph, and
returns per-row results exposing *both* ``Z_static`` and ``Z_transient`` (and
the matching failure flags) so the static and transient rejection sets — and
hence the survival-discrimination decomposition — can be formed.

Phase 2's Accept-Reject filtering, verbatim from spec §8 (the spec writes the
package as ``bep_phase1``; the importable package is ``bep_reliability_engine``)::

    from bep_reliability_engine.evaluator import evaluate_realization
    results_2016 = [
        evaluate_realization(theta_matrix[j], h_2016, geometry, l_ini=0.0)
        for j in range(N)
    ]
    surviving_mask_trans  = np.array([r.Z_transient > 0 for r in results_2016])
    surviving_mask_static = np.array([r.Z_static    > 0 for r in results_2016])
    theta_posterior = theta_matrix[surviving_mask_trans]

No physical outcome is asserted: the matrix and the synthetic 2016 stand-in are
arbitrary, and the assertions hold regardless of which rows happen to fail.
What is locked is that the *surface* supports the Phase 2 procedure — types,
per-row cardinality, the equivalence of the Z-based and flag-based rejection
sets, and importability in a bare interpreter.
"""

import subprocess
import sys
import textwrap
from types import SimpleNamespace

import numpy as np

# The exact clean top-level import Phase 2 performs: the evaluator symbol comes
# straight from its module, with no package-level orchestration pulled in.
from bep_reliability_engine.evaluator import EvaluationResult, evaluate_realization

# Small prior-style theta matrix in the canonical column order
# ['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e'] (spec §2).
# Plausible SI values spanning weak-to-strong configurations; chosen only so
# every row yields a positive H_c, not to force any particular failure pattern.
THETA_MATRIX = np.array(
    [
        [1.0e-4, 2.0e-4, 3.0, 3.0, 1.0e-6, 16.0, 0.014],
        [2.0e-4, 2.5e-4, 4.0, 2.0, 2.0e-6, 14.0, 0.020],
        [5.0e-5, 1.8e-4, 2.5, 4.0, 5.0e-7, 18.0, 0.010],
        [3.0e-4, 3.0e-4, 5.0, 1.5, 3.0e-6, 12.0, 0.030],
        [8.0e-5, 2.2e-4, 3.5, 3.5, 1.0e-6, 17.0, 0.012],
        [1.5e-4, 2.0e-4, 3.0, 2.5, 1.5e-6, 15.0, 0.018],
    ]
)

GEOMETRY = {
    "L": 30.0,
    "z_toe": 2.0,
    "foreshore_width": 0.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}


def _synthetic_2016_hydrograph(dt_s: float = 600.0) -> SimpleNamespace:
    """A synthetic, multi-peak stand-in for the 2016 typhoon hydrograph.

    Compound (two-peak) shape only to mirror the real event's character; the
    physics is irrelevant to this interface test. Carries the canonical
    HydrographRecord fields (ADR-0010): ``h`` (SI stage series), ``peak``
    (max instantaneous stage), ``native_dt`` (authoritative timestep), plus
    the descriptive fields M8 ignores.
    """
    h = np.concatenate(
        [
            np.full(20, 2.0),
            np.linspace(2.0, 13.0, 10),
            np.full(10, 13.0),
            np.linspace(13.0, 3.0, 10),
            np.full(15, 3.0),
            np.linspace(3.0, 15.0, 10),
            np.full(10, 15.0),
            np.linspace(15.0, 2.0, 15),
        ]
    )
    return SimpleNamespace(
        t=np.arange(h.size, dtype=np.float64) * dt_s,
        h=h,
        peak=float(h.max()),
        duration_hours=float(h.size * dt_s / 3600.0),
        scenario="historical",
        event_id="typhoon-2016-synthetic",
        native_dt=dt_s,
    )


def test_evaluate_realization_is_clean_toplevel_symbol() -> None:
    """The Phase 2 entry point is importable as a stable top-level symbol.

    Confirms the symbol resolves to the evaluator module (not re-exported from
    an orchestrator) and is plainly callable — the §9 requirement that M8 be
    importable without notebook context.
    """
    assert callable(evaluate_realization)
    assert evaluate_realization.__module__ == "bep_reliability_engine.evaluator"


def test_phase2_per_row_replay_exposes_both_failure_flags() -> None:
    """Per-row replay against h_2016 yields both Z values and both flags.

    Mirrors the spec §8 list comprehension exactly, then checks the surface
    each result must expose: ``Z_static``/``Z_transient`` as finite floats and
    ``failure_static``/``failure_trans`` as bools, one result per theta row.
    """
    h_2016 = _synthetic_2016_hydrograph()
    n = THETA_MATRIX.shape[0]

    results_2016 = [
        evaluate_realization(THETA_MATRIX[j], h_2016, GEOMETRY, l_ini=0.0)
        for j in range(n)
    ]

    assert len(results_2016) == n
    for r in results_2016:
        assert isinstance(r, EvaluationResult)
        # Both limit-state margins are exposed as finite Python floats.
        assert isinstance(r.Z_static, float) and np.isfinite(r.Z_static)
        assert isinstance(r.Z_transient, float) and np.isfinite(r.Z_transient)
        # Both failure flags are exposed as Python bools.
        assert isinstance(r.failure_static, bool)
        assert isinstance(r.failure_trans, bool)


def test_phase2_static_and_transient_rejection_sets_are_formable() -> None:
    """Both rejection sets and the survival-discrimination decomposition form.

    Builds the Z-based survival masks of spec §8, the posterior theta slice,
    and the marginal transient rejection (transient beyond static). Asserts the
    surface supports them as well-typed boolean arrays — not any particular
    rejection counts (this is interface, not physics).
    """
    h_2016 = _synthetic_2016_hydrograph()
    n = THETA_MATRIX.shape[0]

    results_2016 = [
        evaluate_realization(THETA_MATRIX[j], h_2016, GEOMETRY, l_ini=0.0)
        for j in range(n)
    ]

    surviving_mask_trans = np.array([r.Z_transient > 0 for r in results_2016])
    surviving_mask_static = np.array([r.Z_static > 0 for r in results_2016])

    for mask in (surviving_mask_trans, surviving_mask_static):
        assert mask.shape == (n,)
        assert mask.dtype == np.bool_

    # The posterior sample is the transient-surviving slice of the prior matrix.
    theta_posterior = THETA_MATRIX[surviving_mask_trans]
    assert theta_posterior.shape == (int(surviving_mask_trans.sum()), 7)

    # Survival-discrimination decomposition (spec §8): both rejection fractions
    # side by side, and the marginal transient rejection beyond the static set.
    rejected_static = ~surviving_mask_static
    rejected_trans = ~surviving_mask_trans
    marginal_transient = rejected_trans & ~rejected_static

    assert 0.0 <= rejected_static.mean() <= 1.0
    assert 0.0 <= rejected_trans.mean() <= 1.0
    assert marginal_transient.shape == (n,)
    assert marginal_transient.dtype == np.bool_


def test_z_based_and_flag_based_rejection_sets_agree() -> None:
    """The two ways Phase 2 may form a rejection set are equivalent.

    Phase 2 may reject on ``Z_transient <= 0`` or read ``failure_trans``
    directly; both must yield the identical partition (failure is Z <= 0, the
    boundary included). Locking this keeps either Phase 2 idiom valid.
    """
    h_2016 = _synthetic_2016_hydrograph()
    n = THETA_MATRIX.shape[0]

    results_2016 = [
        evaluate_realization(THETA_MATRIX[j], h_2016, GEOMETRY, l_ini=0.0)
        for j in range(n)
    ]

    rejected_trans_by_z = np.array([r.Z_transient <= 0 for r in results_2016])
    rejected_trans_by_flag = np.array([r.failure_trans for r in results_2016])
    rejected_static_by_z = np.array([r.Z_static <= 0 for r in results_2016])
    rejected_static_by_flag = np.array([r.failure_static for r in results_2016])

    assert np.array_equal(rejected_trans_by_z, rejected_trans_by_flag)
    assert np.array_equal(rejected_static_by_z, rejected_static_by_flag)


def test_import_surface_is_self_contained_in_a_bare_interpreter() -> None:
    """A fresh interpreter can import and call M8 with no project context.

    The strongest form of the §9 "importable without notebook context"
    requirement: a subprocess that imports only ``evaluate_realization`` (plus
    numpy) and runs one call. If the evaluator module ever grew a heavy or
    notebook-bound import, this would fail in isolation even while the in-process
    tests pass.
    """
    script = textwrap.dedent(
        """
        import numpy as np
        from types import SimpleNamespace
        from bep_reliability_engine.evaluator import evaluate_realization

        theta = np.array([1.0e-4, 2.0e-4, 3.0, 3.0, 1.0e-6, 16.0, 0.014])
        geometry = {
            "L": 30.0, "z_toe": 2.0, "foreshore_width": 0.0,
            "D_fore": 3.0, "k_fore": 1.0e-6,
        }
        h = np.array([2.0, 14.0, 2.0])
        h_2016 = SimpleNamespace(
            t=np.arange(3) * 600.0, h=h, peak=14.0, duration_hours=0.5,
            scenario="historical", event_id="2016", native_dt=600.0,
        )
        r = evaluate_realization(theta, h_2016, geometry, l_ini=0.0)
        assert isinstance(r.Z_static, float)
        assert isinstance(r.Z_transient, float)
        assert isinstance(r.failure_static, bool)
        assert isinstance(r.failure_trans, bool)
        print("PHASE2_IMPORT_OK")
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "PHASE2_IMPORT_OK" in proc.stdout
