"""What the survival constraint does and does not establish (2026-09-16).

Two statements about the Phase 2 update had no gate anywhere in the suite,
and both had reached documents of record in a false form:

1. that survival filtering cannot condition the independently drawn seepage
   length, and that a Sobol total-effect share therefore bounds what any
   future survival could achieve;
2. that the transient and static failure sets are "not strictly nested", so
   an empty ``transient_only_reject`` cell is an empirical finding about the
   observed event.

Both are statements ABOUT computed quantities rather than computed
quantities themselves, which is why every numerical gate in the suite was
blind to them (the same blind spot ``tests/test_physical_model_qualifications``
closes for the physical-model statements). These tests assert the true
forms, so each one fails if the false form becomes true again.

The nesting checks drive the real M8 kernels; the conditioning checks are
pure analysis on hand-built masks whose likelihood is known by construction.
"""

from __future__ import annotations

import numpy as np
import pytest

from bayesian_reliability_updating.analysis import seepage_length_update
from bayesian_reliability_updating.filtering import decompose
from bep_reliability_engine.evaluator import evaluate_batch_diagnostics
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.progression import CRACK_RESISTANCE_FACTOR

PARAM_NAMES = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]
I_D_BL = PARAM_NAMES.index("D_bl")

GEOMETRY = {
    "L": 30.0,
    "z_toe": 2.0,
    "foreshore_width": 0.0,
    "D_fore": 3.0,
    "k_fore": 1.0e-6,
}
DT_S = 225.0


def _record(h: np.ndarray, dt_s: float = DT_S) -> HydrographRecord:
    t = np.arange(h.size, dtype=np.float64) * dt_s
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(h.max()),
        duration_hours=float((h.size - 1) * dt_s / 3600.0),
        native_dt=dt_s,
        event_id="nesting_fixture",
        scenario="historical",
    )


def _spread_theta(n: int, seed: int = 20260916) -> np.ndarray:
    """A theta sample wide enough to straddle both failure boundaries."""
    rng = np.random.default_rng(seed)
    theta = np.empty((n, 7), dtype=np.float64)
    theta[:, 0] = np.exp(rng.normal(np.log(3.0e-4), 0.8, n))  # k_aq
    theta[:, 1] = np.exp(rng.normal(np.log(2.2e-4), 0.3, n))  # d_70
    theta[:, 2] = np.exp(rng.normal(np.log(3.0), 0.2, n))  # D_aq
    theta[:, 3] = np.exp(rng.normal(np.log(2.0), 0.3, n))  # D_bl
    theta[:, 4] = np.exp(rng.normal(np.log(1.0e-6), 0.5, n))  # k_bl
    theta[:, 5] = np.exp(rng.normal(np.log(6.9), 0.056, n))  # gamma_bl_sub
    theta[:, 6] = np.exp(rng.normal(np.log(0.30), 0.8, n))  # C_e
    return theta


def _sustained(peak: float, hours: float = 40.0) -> np.ndarray:
    """A long plateau at ``peak``, ramped from the toe at both ends."""
    n_hold = int(hours * 3600.0 / DT_S)
    ramp = np.linspace(GEOMETRY["z_toe"], peak, 40)
    return np.concatenate([ramp, np.full(n_hold, peak), ramp[::-1]])


# --------------------------------------------------------------------- #
# 1. Nesting is a theorem of the head convention, not a measurement.
# --------------------------------------------------------------------- #


@pytest.mark.parametrize("peak", [5.0, 6.0, 7.0, 9.0])
def test_transient_failure_implies_static_failure_with_crack_margin(
    peak: float,
) -> None:
    """F_transient is contained in F_static, with margin 0.3 * D_bl.

    Derivation: passing l_c needs H_erosion > H_eq(l_c) = H_c, and
    max_t H_erosion = (h_peak - z_toe) - 0.3 * D_bl. So transient failure
    forces Z_static < -0.3 * D_bl, strictly. This is the property ADR-0030
    used as its timestep diagnostic; nothing asserted it.
    """
    theta = _spread_theta(400)
    record = _record(_sustained(peak))
    diagnostics = evaluate_batch_diagnostics(theta, record, GEOMETRY)

    failed_trans = np.asarray(diagnostics.failure_trans, dtype=bool)
    failed_static = np.asarray(diagnostics.failure_static, dtype=bool)

    # the set relation itself
    assert not np.any(failed_trans & ~failed_static), (
        "a row failed transient while surviving static: the nesting "
        "implication of the production head convention is broken."
    )
    # and the quantitative margin the derivation predicts
    if failed_trans.any():
        margin = (
            diagnostics.Z_static[failed_trans]
            + CRACK_RESISTANCE_FACTOR * theta[failed_trans, I_D_BL]
        )
        assert np.all(margin < 0.0), (
            "a transient failure did not clear the static threshold by a "
            f"whole crack decrement (worst margin {margin.max():+.6f} m)."
        )


def test_nesting_is_informative_only_where_both_branches_are_exercised() -> None:
    """The fixture must actually produce failures, or the test is vacuous."""
    theta = _spread_theta(400)
    record = _record(_sustained(6.0))
    diagnostics = evaluate_batch_diagnostics(theta, record, GEOMETRY)
    n_trans = int(np.asarray(diagnostics.failure_trans, dtype=bool).sum())
    n_static = int(np.asarray(diagnostics.failure_static, dtype=bool).sum())
    assert 0 < n_trans < 400
    assert n_trans < n_static < 400


def test_marginal_transient_cell_is_empty_by_construction_not_by_event() -> None:
    """The empty cell follows from the criteria, so it survives the event."""
    theta = _spread_theta(300)
    for peak in (5.0, 6.0, 7.0):
        diagnostics = evaluate_batch_diagnostics(
            theta, _record(_sustained(peak)), GEOMETRY
        )
        table = decompose(
            ~np.asarray(diagnostics.failure_static, dtype=bool),
            ~np.asarray(diagnostics.failure_trans, dtype=bool),
        )
        assert table["cells"]["transient_only_reject"]["count"] == 0


def test_decoupled_transient_exponent_can_break_nesting() -> None:
    """The cell is retained because a knob can genuinely break inclusion.

    With a transient-only scale exponent the two branches no longer share
    one critical head, so the implication has no reason to hold and the
    two-by-two table must keep reporting the cell.
    """
    theta = _spread_theta(400)
    record = _record(_sustained(9.0))
    decoupled = evaluate_batch_diagnostics(
        theta, record, GEOMETRY, alpha_exponent_transient=-0.5
    )
    baseline = evaluate_batch_diagnostics(theta, record, GEOMETRY)
    # the knob must actually move the transient branch, or this proves nothing
    assert not np.array_equal(decoupled.failure_trans, baseline.failure_trans)
    assert np.any(np.asarray(decoupled.H_c_transient) != np.asarray(decoupled.H_c))


# --------------------------------------------------------------------- #
# 2. Prior independence does not survive conditioning.
# --------------------------------------------------------------------- #


def _lognormal_L(n: int, mean: float = 35.0, cov: float = 0.20) -> np.ndarray:
    sigma = np.sqrt(np.log(1.0 + cov**2))
    mu = np.log(mean) - 0.5 * sigma**2
    return np.exp(np.random.default_rng(4242).normal(mu, sigma, n))


def test_L_independent_acceptance_leaves_the_marginal_alone() -> None:
    """The control: a mask that ignores L must not move L."""
    L = _lognormal_L(20000)
    rng = np.random.default_rng(7)
    accept = rng.random(L.size) > 0.2  # independent of L by construction
    out = seepage_length_update(L, accept)
    assert out["relative_mean_shift"] == pytest.approx(0.0, abs=5e-3)
    assert out["acceptance_spread"] < 0.05
    assert out["variance_ratio"] == pytest.approx(1.0, abs=0.05)


def test_L_dependent_acceptance_conditions_the_marginal() -> None:
    """The case that matters: survival depending on L conditions L.

    Independence in the prior is not preserved by conditioning, because
    pi(L|S) = pi(L) P(S|L) / P(S). Rejecting short paths must raise the
    retained mean and narrow the retained spread.
    """
    L = _lognormal_L(20000)
    accept = L > np.quantile(L, 0.10)  # survival favours the longer paths
    out = seepage_length_update(L, accept)
    assert out["relative_mean_shift"] > 0.02
    assert out["variance_ratio"] < 0.95
    assert out["acceptance_spread"] > 0.5
    assert out["ks_statistic"] > 0.05


def test_acceptance_profile_detects_conditioning_a_flat_mean_would_hide() -> None:
    """A symmetric rejection moves no mean and still conditions L.

    This is why the profile, not the mean shift, is the object of record:
    rejecting both tails leaves the mean where it was while removing a
    fifth of the variance.
    """
    L = _lognormal_L(20000)
    lo, hi = np.quantile(L, [0.10, 0.90])
    accept = (L > lo) & (L < hi)
    out = seepage_length_update(L, accept)
    assert abs(out["relative_mean_shift"]) < 0.05
    assert out["variance_ratio"] < 0.6
    assert out["acceptance_spread"] > 0.5


def test_induced_dependence_is_reported_against_theta() -> None:
    """Row-wise rejection couples L to theta even from an independent prior."""
    n = 20000
    L = _lognormal_L(n)
    rng = np.random.default_rng(11)
    theta = np.exp(rng.normal(0.0, 1.0, (n, 7)))
    # survive unless BOTH the path is short and the conductivity is high:
    # the joint corner, which is what a real survival constraint removes.
    short_path = L < np.quantile(L, 0.35)
    fast_soil = theta[:, 0] > np.quantile(theta[:, 0], 0.65)
    accept = ~(short_path & fast_soil)
    out = seepage_length_update(L, accept, theta=theta, param_names=PARAM_NAMES)
    induced = out["induced_dependence"]
    assert abs(induced["k_aq"]["spearman_prior"]) < 0.05
    assert induced["k_aq"]["spearman_posterior"] > 0.05
    assert out["max_induced_shift_parameter"] == "k_aq"


def test_seepage_length_update_rejects_mismatched_inputs() -> None:
    L = _lognormal_L(100)
    with pytest.raises(ValueError, match="pair row for row"):
        seepage_length_update(L, np.ones(99, dtype=bool))
    with pytest.raises(ValueError, match="given together"):
        seepage_length_update(L, np.ones(100, dtype=bool), theta=np.zeros((100, 7)))
