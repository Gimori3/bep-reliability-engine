"""Tests for M8 limit-state evaluator (``bep_reliability_engine.evaluator``).

Executable contract for the M8 interface, written in the same pre-implementation
pattern as M5/M7: every behavioural test below is the contract the
implementation must satisfy, and the interface guard at the bottom passes
independently of the kernels.

What these tests lock (the M8 invariants, spec §2-§4, §8):

1. **Shared-sample contract (ADR-0002).** The same theta row and the same
   computed r_e feed both branches, checked on a deterministic single-Euler-step
   case whose Z_static and Z_transient are reconstructed from the consumed
   kernels (M6 H_c, M4 r_e, M7 progression_rate).
2. **Head-convention separation (spec §3, §4; ADR-0007).** On a matched peak the
   static branch uses the gross head ``r_e*(h_peak - z_toe)`` while the transient
   drives progression with ``H_erosion = Delta_h_blanket - 0.3*D_bl``; the two
   driving heads differ by exactly ``0.3*D_bl``, and l_e is shown to follow the
   reduced head, not the gross one.
3. **Failure signs.** Both ``failure_static`` and ``failure_trans`` are returned
   and equal ``Z <= 0`` (the boundary Z = 0 counts as failure).
4. **Single-source H_c (spec §1, §4).** The static branch reuses the same H_c
   that anchors the transient H_eq — verified with l_ini > 0 so H_c enters the
   rate through H_eq(l_ini); no recomputation, no drift.
5. **Diagnostics (spec §2).** H_c, l_c, lambda_in, r_e, t_uh, the latched
   uplift/heave flags, and l_e_final are all returned and correct.
6. **store_trajectory flag (spec §2, §12 failure mode 6).** Controls whether the
   full l(t) is retained or None.

Numbers are reconstructed from the consumed kernels (never re-derived by hand
inside the test) so the M8 wiring — not the physics, which M4/M6/M7 already
test — is what is under test. The deterministic fixture is tuned so r_e = 0.5
and lambda_in = 30 m exactly (foreshore_width = 0 removes lambda_out), which
makes the shared-r_e arithmetic auditable.
"""

import inspect
from dataclasses import fields, is_dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from bep_reliability_engine import evaluator
from bep_reliability_engine.evaluator import EvaluationResult, evaluate_realization
from bep_reliability_engine.hydraulics import (
    leakage_length_in,
    leakage_length_out,
    response_factor,
)
from bep_reliability_engine.progression import (
    CRACK_RESISTANCE_FACTOR,
    equilibrium_head,
    progression_rate,
)
from bep_reliability_engine.sellmeijer import compute_critical_head

# Canonical theta column order (spec §2, M2 contract).
PARAM_NAMES = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_s_sub", "C_e"]
I_K_AQ, I_D70, I_D_AQ, I_D_BL, I_K_BL, I_GAMMA, I_C_E = range(7)

# Deterministic fixture. lambda_in = sqrt(k_aq*D_aq*D_bl/k_bl)
#   = sqrt(1e-4 * 3 * 3 / 1e-6) = sqrt(900) = 30 m; with L = 30 m and
# foreshore_width = 0 (=> lambda_out_eff = 0) the response factor is
#   r_e = lambda_in / (0 + L + lambda_in) = 30 / 60 = 0.5 exactly.
THETA = np.array([1.0e-4, 2.0e-4, 3.0, 3.0, 1.0e-6, 16.0, 0.014])
GEOMETRY = {
    "L": 30.0,
    "z_toe": 2.0,
    "foreshore_width": 0.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}
DT_S = 600.0

EXPECTED_R_E = 0.5
EXPECTED_LAMBDA_IN = 30.0


def _make_hydrograph(
    h: list[float] | np.ndarray,
    dt_s: float = DT_S,
    peak: float | None = None,
) -> SimpleNamespace:
    """Structural stand-in for the not-yet-implemented M3 HydrographRecord.

    M3 (``hydrographs.py``) is unimplemented, so ``HydrographRecord`` does not
    exist yet; M8 consumes a record by duck typing (module docstring ambiguity
    1). This builds the three fields evaluate_realization reads — ``h`` (river
    stage), ``native_dt`` (timestep), ``peak`` (static comparator) — plus the
    rest of the spec §2 record for completeness. ``peak`` defaults to max(h).
    """
    h_arr = np.asarray(h, dtype=np.float64)
    t = np.arange(h_arr.size, dtype=np.float64) * dt_s
    return SimpleNamespace(
        t=t,
        h=h_arr,
        peak=float(np.max(h_arr)) if peak is None else float(peak),
        duration_hours=float(h_arr.size * dt_s / 3600.0),
        scenario="historical",
        event_id="test-event",
        native_dt=float(dt_s),
    )


def _reference_preamble(
    theta: np.ndarray, geometry: dict
) -> tuple[float, float, float, float]:
    """Recompute the shared preamble (H_c, l_c, lambda_in, r_e) from the kernels.

    The same M6/M4 calls M8 must make, used as the reference M8 is checked
    against (shared-sample contract).
    """
    sellmeijer = compute_critical_head(theta, geometry)
    lambda_in = float(
        leakage_length_in(theta[I_K_AQ], theta[I_D_AQ], theta[I_D_BL], theta[I_K_BL])
    )
    lambda_out_eff = float(
        leakage_length_out(
            theta[I_K_AQ],
            theta[I_D_AQ],
            geometry["D_fore"],
            geometry["k_fore"],
            geometry["foreshore_width"],
        )
    )
    r_e = float(response_factor(lambda_in, lambda_out_eff, geometry["L"]))
    return float(sellmeijer.H_c), float(sellmeijer.l_c), lambda_in, r_e


# ---------------------------------------------------------------------------
# (1) Shared-sample contract: deterministic single-Euler-step reconstruction
# ---------------------------------------------------------------------------


def test_shared_sample_deterministic_single_step() -> None:
    """Same theta and same r_e feed both branches (ADR-0002).

    One timestep at a constant over-critical stage, started from l = 0 (so
    H_eq(0) = 0): the transient is exactly one forward-Euler step
    ``l_e = dt * progression_rate(H_erosion, 0, C_e, k_aq, L)`` and the static
    margin is ``H_c - r_e*(h_peak - z_toe)``. Both reconstructions use the same
    r_e = 0.5 and the same M6 H_c, so the case fails if M8 draws r_e or H_c
    independently for the two branches.
    """
    H_c, l_c, lambda_in, r_e = _reference_preamble(THETA, GEOMETRY)
    assert r_e == pytest.approx(EXPECTED_R_E, rel=1e-12)
    assert lambda_in == pytest.approx(EXPECTED_LAMBDA_IN, rel=1e-12)

    h_peak = 14.0
    result = evaluate_realization(
        THETA, _make_hydrograph([h_peak], peak=h_peak), GEOMETRY
    )

    L = GEOMETRY["L"]
    z_toe = GEOMETRY["z_toe"]
    d_bl = THETA[I_D_BL]
    k_aq = THETA[I_K_AQ]
    c_e = THETA[I_C_E]

    # Preamble reused exactly (no drift): the reported diagnostics equal the
    # standalone M6/M4 references.
    assert result.r_e == pytest.approx(r_e, rel=1e-12)
    assert result.H_c == pytest.approx(H_c, rel=1e-12)
    assert result.l_c == pytest.approx(l_c, rel=1e-12)
    assert result.lambda_in == pytest.approx(lambda_in, rel=1e-12)

    # Static branch: gross translated peak head, no crack reduction.
    delta_h_blanket_peak = r_e * (h_peak - z_toe)  # = 6.0 m
    assert result.Z_static == pytest.approx(H_c - delta_h_blanket_peak, rel=1e-12)

    # Transient branch: exactly one Euler step with the crack-reduced head.
    h_erosion = delta_h_blanket_peak - CRACK_RESISTANCE_FACTOR * d_bl  # = 5.1 m
    rate = float(progression_rate(h_erosion, 0.0, c_e, k_aq, L))
    l_e_expected = DT_S * rate
    assert l_e_expected > 0.0
    assert result.l_e_final == pytest.approx(l_e_expected, rel=1e-12)
    assert result.Z_transient == pytest.approx(L - l_e_expected, rel=1e-12)

    # Failure signs and the latched diagnostics.
    assert result.failure_static is True
    assert result.failure_trans is False
    assert result.uplift_occurred is True
    assert result.heave_occurred is True
    assert result.t_uh == 0.0


# ---------------------------------------------------------------------------
# (2) Head-convention separation: static gross head vs transient H_erosion
# ---------------------------------------------------------------------------


def test_head_convention_separation_by_crack_term() -> None:
    """Static and transient driving heads differ by exactly 0.3*D_bl (spec §4).

    The static comparator uses the gross head ``r_e*(h_peak - z_toe)``; the
    transient rate uses ``H_erosion = Delta_h_blanket - 0.3*D_bl``. The case
    pins both: (a) the static head carries no crack reduction, (b) the two
    heads differ by exactly 0.3*D_bl, and (c) l_e follows the REDUCED head, not
    the gross head — the decisive guard against the head-mixing error of
    spec §5 (un-reduced head leaking into the rate).
    """
    H_c, _l_c, _lambda_in, r_e = _reference_preamble(THETA, GEOMETRY)
    h_peak = 14.0
    result = evaluate_realization(
        THETA, _make_hydrograph([h_peak], peak=h_peak), GEOMETRY
    )

    L = GEOMETRY["L"]
    z_toe = GEOMETRY["z_toe"]
    d_bl = THETA[I_D_BL]
    k_aq = THETA[I_K_AQ]
    c_e = THETA[I_C_E]

    # Recover the static driving head from the reported margin; it must be the
    # gross translated peak with NO crack reduction.
    static_head = result.H_c - result.Z_static
    assert static_head == pytest.approx(r_e * (h_peak - z_toe), rel=1e-12)

    # The transient driving head is the crack-reduced head, exactly 0.3*D_bl
    # below the static head.
    transient_head = static_head - CRACK_RESISTANCE_FACTOR * d_bl
    assert static_head - transient_head == pytest.approx(
        CRACK_RESISTANCE_FACTOR * d_bl, rel=1e-12
    )

    # l_e is driven by the REDUCED head (single Euler step from l = 0).
    l_e_reduced = DT_S * float(progression_rate(transient_head, 0.0, c_e, k_aq, L))
    assert result.l_e_final == pytest.approx(l_e_reduced, rel=1e-12)

    # ... and NOT by the un-reduced gross head: had M8 fed the gross head into
    # the rate, l_e would be measurably larger.
    l_e_gross = DT_S * float(progression_rate(static_head, 0.0, c_e, k_aq, L))
    assert l_e_gross > l_e_reduced
    assert abs(result.l_e_final - l_e_gross) > 1e-9
    assert H_c == pytest.approx(result.H_c, rel=1e-12)  # same single-source H_c


# ---------------------------------------------------------------------------
# (3) Single-source H_c anchors both branches (l_ini > 0 so H_c enters H_eq)
# ---------------------------------------------------------------------------


def test_single_H_c_anchors_static_and_transient() -> None:
    """The static H_c equals the H_c anchoring the transient H_eq (spec §1, §4).

    With l_ini on the rising segment (l_ini = l_c/2) the equilibrium head is
    H_eq = 0.5*H_c, so H_c enters the transient rate through the overload
    ``H_erosion - H_eq``. Reconstructing l_e with the REPORTED H_c/l_c and the
    static margin with the same reported H_c means a divergent internal H_c for
    the two uses would break at least one assertion.
    """
    H_c, l_c, _lambda_in, r_e = _reference_preamble(THETA, GEOMETRY)
    h_peak = 14.0
    l_ini = l_c / 2.0
    result = evaluate_realization(
        THETA, _make_hydrograph([h_peak], peak=h_peak), GEOMETRY, l_ini=l_ini
    )

    L = GEOMETRY["L"]
    z_toe = GEOMETRY["z_toe"]
    d_bl = THETA[I_D_BL]
    k_aq = THETA[I_K_AQ]
    c_e = THETA[I_C_E]

    assert result.H_c == pytest.approx(H_c, rel=1e-12)
    assert result.l_c == pytest.approx(l_c, rel=1e-12)

    # Static branch consumes the reported H_c.
    delta_h_blanket_peak = r_e * (h_peak - z_toe)
    assert result.Z_static == pytest.approx(
        result.H_c - delta_h_blanket_peak, rel=1e-12
    )

    # Transient H_eq anchored on the SAME H_c/l_c (rising-segment midpoint).
    h_eq = float(equilibrium_head(l_ini, result.H_c, result.l_c, L))
    assert h_eq == pytest.approx(0.5 * result.H_c, rel=1e-12)

    h_erosion = delta_h_blanket_peak - CRACK_RESISTANCE_FACTOR * d_bl
    assert h_erosion > h_eq  # growth must actually occur for the test to bite
    rate = float(progression_rate(h_erosion, h_eq, c_e, k_aq, L))
    l_e_expected = l_ini + DT_S * rate
    assert result.l_e_final == pytest.approx(l_e_expected, rel=1e-12)
    assert result.Z_transient == pytest.approx(L - l_e_expected, rel=1e-12)


# ---------------------------------------------------------------------------
# (4) Failure signs: Z <= 0, both branches; safe and breach extremes
# ---------------------------------------------------------------------------


def test_subcritical_peak_no_failure_no_growth() -> None:
    """A sub-threshold peak: both branches safe, no growth, flags off, t_uh NaN.

    delta_h_blanket = r_e*(4 - 2) = 1.0 m is below the uplift/heave threshold
    gamma'_s*D_bl/gamma_w = 16*3/9.81 = 4.89 m, so the gate never opens: l stays
    at l_ini = 0, Z_transient = L, and uplift/heave never latch.
    """
    H_c, _l_c, _lambda_in, r_e = _reference_preamble(THETA, GEOMETRY)
    h_peak = 4.0
    result = evaluate_realization(
        THETA, _make_hydrograph([h_peak] * 5, peak=h_peak), GEOMETRY
    )

    L = GEOMETRY["L"]
    z_toe = GEOMETRY["z_toe"]

    assert result.Z_static == pytest.approx(H_c - r_e * (h_peak - z_toe), rel=1e-12)
    assert result.failure_static is False
    assert result.l_e_final == 0.0
    assert result.Z_transient == pytest.approx(L, rel=1e-12)
    assert result.failure_trans is False
    assert result.uplift_occurred is False
    assert result.heave_occurred is False
    assert np.isnan(result.t_uh)

    # The failure flags are exactly the Z <= 0 indicators.
    assert result.failure_static == (result.Z_static <= 0.0)
    assert result.failure_trans == (result.Z_transient <= 0.0)


def test_transient_breach_sets_failure_and_zero_margin() -> None:
    """A breaching transient: l_e clipped at L, Z_transient = 0, failure True.

    High C_e under a sustained over-critical stage drives the pipe to L; M7
    clips at L (breach absorbing), so Z_transient = L - L = 0 and the boundary
    Z = 0 must count as failure (Z <= 0).
    """
    theta = THETA.copy()
    theta[I_C_E] = 0.2  # high erosion coefficient: breach within the record
    result = evaluate_realization(
        theta, _make_hydrograph([30.0] * 60, peak=30.0), GEOMETRY
    )

    L = GEOMETRY["L"]
    assert result.l_e_final == pytest.approx(L, rel=1e-12)
    assert result.Z_transient == pytest.approx(0.0, abs=1e-9)
    assert result.Z_transient <= 0.0
    assert result.failure_trans is True
    assert result.failure_trans == (result.Z_transient <= 0.0)
    assert result.failure_static == (result.Z_static <= 0.0)


# ---------------------------------------------------------------------------
# (5) store_trajectory flag controls retention (spec §2, §12 failure mode 6)
# ---------------------------------------------------------------------------


def test_store_trajectory_flag_controls_retention() -> None:
    """l_trajectory is None when off, a (T,) monotone array when on.

    The terminal value of the stored trajectory equals l_e_final, and the
    final value is identical whether or not the trajectory is stored.
    """
    hydrograph = _make_hydrograph([14.0] * 20, peak=14.0)

    off = evaluate_realization(THETA, hydrograph, GEOMETRY, store_trajectory=False)
    assert off.l_trajectory is None

    on = evaluate_realization(THETA, hydrograph, GEOMETRY, store_trajectory=True)
    trajectory = on.l_trajectory
    assert trajectory is not None
    assert trajectory.shape == (20,)
    assert np.all(np.diff(trajectory) >= 0.0)  # monotone non-decreasing
    assert float(trajectory[-1]) == pytest.approx(on.l_e_final, rel=1e-12)

    # Storage must not change the computed result.
    assert on.l_e_final == pytest.approx(off.l_e_final, rel=1e-12)
    assert on.Z_transient == pytest.approx(off.Z_transient, rel=1e-12)


# ---------------------------------------------------------------------------
# (6) Interface guard (independent of the kernels; pins the Phase 2 contract)
# ---------------------------------------------------------------------------


def test_public_interface() -> None:
    """The module exposes the frozen Phase 2 contract: EvaluationResult + M8.

    Field order follows the spec §2 output listing; the call signature is the
    stable API Phase 2 imports (spec §8). Field names, the parameter tuple, and
    the defaults (l_ini = 0.0, store_trajectory = False) are pinned here.
    """
    assert set(evaluator.__all__) == {"EvaluationResult", "evaluate_realization"}

    assert is_dataclass(EvaluationResult)
    assert tuple(f.name for f in fields(EvaluationResult)) == (
        "Z_static",
        "Z_transient",
        "l_e_final",
        "l_trajectory",
        "H_c",
        "l_c",
        "lambda_in",
        "r_e",
        "t_uh",
        "failure_static",
        "failure_trans",
        "uplift_occurred",
        "heave_occurred",
    )

    signature = inspect.signature(evaluate_realization)
    assert tuple(signature.parameters) == (
        "theta_row",
        "hydrograph",
        "geometry",
        "l_ini",
        "store_trajectory",
    )
    assert signature.parameters["l_ini"].default == 0.0
    assert signature.parameters["store_trajectory"].default is False


# ---------------------------------------------------------------------------
# (7) Cross-row shared-sample properties on distinct live inputs
# ---------------------------------------------------------------------------

# Three distinct theta rows (canonical column order). d_70 in the Sellmeijer
# validity range [150e-6, 430e-6] m and all rows yield a positive H_c. Distinct
# k_aq/D_aq/D_bl/k_bl give distinct lambda_in -> distinct r_e per row; distinct
# D_bl gives distinct 0.3*D_bl head offsets.
THETA_ROWS = [
    np.array([1.0e-4, 2.0e-4, 3.0, 3.0, 1.0e-6, 16.0, 0.014]),
    np.array([2.0e-4, 2.5e-4, 4.0, 2.0, 2.0e-6, 14.0, 0.020]),
    np.array([5.0e-5, 1.8e-4, 2.5, 4.0, 5.0e-7, 18.0, 0.010]),
]

# Peak high enough that the uplift/heave gate opens on every row (the highest
# threshold is row C: gamma'_s*D_bl/gamma_w = 18*4/9.81 = 7.34 m; r_e*(20-2)
# clears it on all three rows), so the transient grows and the crack offset can
# be checked through l_e on each row.
CROSS_ROW_PEAK = 20.0


@pytest.mark.parametrize("theta", THETA_ROWS, ids=["rowA", "rowB", "rowC"])
def test_per_row_single_re_single_Hc_and_crack_offset(theta: np.ndarray) -> None:
    """Within one row: one r_e and one H_c feed both branches, offset 0.3*D_bl.

    Locks, on live distinct inputs (not the constructed r_e = 0.5 fixture):
    the reported r_e/H_c equal the standalone M4/M6 references; the static
    branch consumes that same r_e and that same H_c (gross head); and the
    transient drives the rate with exactly ``static_head - 0.3*D_bl`` -- proven
    by reconstructing l_e from the reduced head and showing it differs from the
    gross-head result. A single Euler step from l = 0 (H_eq(0) = 0).
    """
    H_c, l_c, lambda_in, r_e = _reference_preamble(theta, GEOMETRY)
    result = evaluate_realization(
        theta, _make_hydrograph([CROSS_ROW_PEAK], peak=CROSS_ROW_PEAK), GEOMETRY
    )

    L = GEOMETRY["L"]
    z_toe = GEOMETRY["z_toe"]
    d_bl = theta[I_D_BL]
    k_aq = theta[I_K_AQ]
    c_e = theta[I_C_E]

    # One preamble, reused: reported diagnostics equal the standalone references.
    assert result.r_e == pytest.approx(r_e, rel=1e-12)
    assert result.H_c == pytest.approx(H_c, rel=1e-12)
    assert result.l_c == pytest.approx(l_c, rel=1e-12)
    assert result.lambda_in == pytest.approx(lambda_in, rel=1e-12)

    # Static branch uses the SAME r_e and the SAME H_c, gross head (no crack term).
    static_head = result.H_c - result.Z_static
    assert static_head == pytest.approx(
        result.r_e * (CROSS_ROW_PEAK - z_toe), rel=1e-12
    )

    # Transient drives the rate with static_head - 0.3*D_bl exactly: l_e matches
    # the reduced-head reconstruction and is measurably below the gross-head one.
    transient_head = static_head - CRACK_RESISTANCE_FACTOR * d_bl
    l_e_reduced = DT_S * float(progression_rate(transient_head, 0.0, c_e, k_aq, L))
    l_e_gross = DT_S * float(progression_rate(static_head, 0.0, c_e, k_aq, L))
    assert l_e_reduced > 0.0  # gate open and growing on this row
    assert result.l_e_final == pytest.approx(l_e_reduced, rel=1e-12)
    assert abs(result.l_e_final - l_e_gross) > 1e-9


def test_re_and_Hc_vary_across_distinct_theta_rows() -> None:
    """r_e and H_c are computed per row from theta, not shared constants.

    If r_e (or H_c) were identical across these distinct rows, it would signal a
    value computed from something other than the per-row theta -- a shared-sample
    violation. Companion to the per-row test: that one shows reuse *within* a
    row, this one shows variation *across* rows.
    """
    results = [
        evaluate_realization(
            theta, _make_hydrograph([CROSS_ROW_PEAK], peak=CROSS_ROW_PEAK), GEOMETRY
        )
        for theta in THETA_ROWS
    ]
    r_es = [r.r_e for r in results]
    h_cs = [r.H_c for r in results]

    assert len({round(x, 12) for x in r_es}) == len(r_es), "r_e not distinct per row"
    assert len({round(x, 12) for x in h_cs}) == len(h_cs), "H_c not distinct per row"
