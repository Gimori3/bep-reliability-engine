"""Accept-Reject survival filtering and the survival-discrimination decomposition.

The Phase 2 core (spec section 8; thesis methodology, Accept-Reject
Filtering section; Schweckendiek 2014 Eq. 4.10/4.12, direct reliability
updating with inequality information). Survival of the observed event is
the evidence ``epsilon = {Z_transient(h_obs(t), theta) > 0}``; the
posterior parameter distribution is the prior restricted to the survival
region, realized on the Monte Carlo sample as the accepted subset of joint
7-tuples. Rejection is row-wise on the full joint vector including C_e
(mission invariant 2): no per-parameter rejection exists, so the posterior
retains every correlation the constraint induces (Schweckendiek 2014
section 4.2.2 cautions that updating changes the dependence structure; the
retained joint sample carries it exactly).

Two acceptance criteria exist (ADR-0036):

* ``'no_breach'`` (baseline, thesis): accept row j iff
  ``Z_transient(h_obs, theta_j) > 0`` with ``l_ini = 0`` and ``r_l = 0``.
  The boundary ``Z = 0`` counts as failure (ADR-0008), so survival is the
  strict complement.
* ``'no_breach_no_initiation'`` (stricter optional variant, config-gated,
  OFF by default): additionally reject rows whose uplift-plus-heave
  initiation gate latched under the observed loading, reflecting the
  committee-documented absence of sand boils at the study reaches. The
  modeling caveats (the gate models blanket uplift/heave initiation, not
  boil visibility; survey completeness) are documented in ADR-0036 and the
  Phase 2 report; the baseline remains no-breach.

The survival-discrimination decomposition (spec section 8) cross-tabulates
the transient rejection with the static rejection under the same replay:
rows rejected by the static criterion would have failed at peak head
regardless of time, so only the additional transient rejection (survives
static, fails transient) is evidence about the time-dependent progression
mechanism. The two failure sets are not strictly nested (different driving
heads, ADR-0027/0028), so the full two-by-two table is reported.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from bayesian_reliability_updating.replay import EventReplay

logger = logging.getLogger(__name__)

__all__ = [
    "ACCEPTANCE_CRITERIA",
    "SurvivalFilterResult",
    "apply_survival_filter",
    "decompose",
]

ACCEPTANCE_CRITERIA: tuple[str, ...] = ("no_breach", "no_breach_no_initiation")

# Posterior sample-size floors (ADR-0036). The spec section 11 Monte Carlo
# CoV target (< 5 percent at per-level P_f >= 5e-3) needs on the order of
# 8e4 effective rows, and the architecture anticipates ~20 percent rejection
# at N = 1e5, leaving ~8e4: a posterior that keeps less than
# _WARN_FRACTION of the prior loses that headroom and the posterior tail
# quality degrades below the Phase 1 standard, so it is warned about.
# The collapse floor is scale-aware: at production N = 1e5 both terms give
# 1000 rows (below which a single-row flip moves a posterior P_f point by
# > 1e-3, statistically meaningless); at self-test N a few hundred, the
# 1 percent term governs so only a near-total collapse triggers the
# error-level log. The run still completes either way, because a drained
# segment with near-zero rejection is CORRECT behavior and the mirror case
# (extreme rejection) must stay inspectable.
_WARN_FRACTION: float = 0.5
_ERROR_COUNT: int = 1000
_ERROR_FRACTION: float = 0.01


def _collapse_floor(n_prior: int) -> float:
    """The scale-aware posterior-collapse floor (see the constants note)."""
    return max(1.0, min(float(_ERROR_COUNT), _ERROR_FRACTION * n_prior))


@dataclass(frozen=True)
class SurvivalFilterResult:
    """One event's Accept-Reject outcome over the N prior rows.

    All masks index the original prior rows (row j pairs with theta row j).

    Attributes
    ----------
    event_id : str
        The replayed event.
    criterion : str
        The acceptance criterion applied (one of
        :data:`ACCEPTANCE_CRITERIA`).
    accept : numpy.ndarray, shape (N,), bool
        The operative acceptance mask under ``criterion``.
    accept_trans : numpy.ndarray, shape (N,), bool
        Strict transient survival ``Z_transient > 0`` (the baseline mask;
        equals ``accept`` for the ``'no_breach'`` criterion).
    accept_static : numpy.ndarray, shape (N,), bool
        Strict static survival ``Z_static > 0`` under the same replay
        (mission invariant 4; retained for the decomposition).
    initiation_occurred : numpy.ndarray, shape (N,), bool
        The uplift-plus-heave latch under the observed loading (M5).
    n_prior, n_accepted : int
        Row counts.
    rejection_fraction : float
        ``1 - n_accepted / n_prior`` under the operative criterion.
    decomposition : dict
        The survival-discrimination two-by-two (see :func:`decompose`).
    warnings : list of str
        Posterior sample-size diagnostics that fired (also logged).
    """

    event_id: str
    criterion: str
    accept: NDArray[np.bool_]
    accept_trans: NDArray[np.bool_]
    accept_static: NDArray[np.bool_]
    initiation_occurred: NDArray[np.bool_]
    n_prior: int
    n_accepted: int
    rejection_fraction: float
    decomposition: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def decompose(
    accept_static: NDArray[np.bool_], accept_trans: NDArray[np.bool_]
) -> dict[str, Any]:
    """The survival-discrimination two-by-two over the prior rows (spec 8).

    Parameters
    ----------
    accept_static, accept_trans : numpy.ndarray, bool
        Strict survival masks under the two limit states, same replay.

    Returns
    -------
    dict
        Counts and fractions of the four cells plus the headline rejection
        fractions. ``f_marginal_transient`` (survives static, fails
        transient) is the marginal informativeness of the survival for the
        time-dependent mechanism; ``f_static_only_reject`` (fails static,
        survives transient) is its non-nested complement and is reported,
        not assumed zero.
    """
    accept_static = np.asarray(accept_static, dtype=bool)
    accept_trans = np.asarray(accept_trans, dtype=bool)
    n = accept_static.size

    both_survive = accept_static & accept_trans
    transient_only_reject = accept_static & ~accept_trans
    static_only_reject = ~accept_static & accept_trans
    both_reject = ~accept_static & ~accept_trans

    def _cell(mask: NDArray[np.bool_]) -> dict[str, float | int]:
        count = int(mask.sum())
        return {"count": count, "fraction": count / n if n else float("nan")}

    return {
        "n_prior": int(n),
        "f_static_reject": float((~accept_static).mean()) if n else float("nan"),
        "f_trans_reject": float((~accept_trans).mean()) if n else float("nan"),
        "f_marginal_transient": (
            float(transient_only_reject.mean()) if n else float("nan")
        ),
        "cells": {
            "both_survive": _cell(both_survive),
            "transient_only_reject": _cell(transient_only_reject),
            "static_only_reject": _cell(static_only_reject),
            "both_reject": _cell(both_reject),
        },
    }


def apply_survival_filter(
    replay: EventReplay,
    *,
    criterion: str = "no_breach",
) -> SurvivalFilterResult:
    """Classify every prior row as accepted or rejected under one event.

    Parameters
    ----------
    replay : EventReplay
        The M8 replay of the event over all prior rows.
    criterion : {'no_breach', 'no_breach_no_initiation'}
        The acceptance criterion (see the module docstring). The baseline
        is ``'no_breach'``.

    Returns
    -------
    SurvivalFilterResult
        Masks, counts, the decomposition and any sample-size warnings.

    Raises
    ------
    ValueError
        On an unknown criterion.
    """
    if criterion not in ACCEPTANCE_CRITERIA:
        raise ValueError(
            f"criterion {criterion!r} must be one of {ACCEPTANCE_CRITERIA}."
        )
    diagnostics = replay.diagnostics

    # Survival is the STRICT complement of failure: failure is Z <= 0
    # (ADR-0008), so the retained flags encode the acceptance rule exactly.
    accept_trans = ~np.asarray(diagnostics.failure_trans, dtype=bool)
    accept_static = ~np.asarray(diagnostics.failure_static, dtype=bool)
    initiation = np.asarray(diagnostics.uplift_occurred, dtype=bool) & np.asarray(
        diagnostics.heave_occurred, dtype=bool
    )

    if criterion == "no_breach":
        accept = accept_trans
    else:
        accept = accept_trans & ~initiation

    n_prior = int(accept.size)
    n_accepted = int(accept.sum())
    rejection_fraction = 1.0 - (n_accepted / n_prior) if n_prior else float("nan")

    warnings: list[str] = []
    if n_accepted < _collapse_floor(n_prior):
        message = (
            f"posterior sample collapsed to {n_accepted} of {n_prior} rows "
            f"under {criterion!r} for event {replay.record.event_id!r}: "
            "posterior fragility tails are statistically meaningless at this "
            "size; treat downstream results as qualitative only."
        )
        warnings.append(message)
        logger.error("%s", message)
    elif n_accepted < _WARN_FRACTION * n_prior:
        message = (
            f"posterior keeps {n_accepted} of {n_prior} rows "
            f"({100.0 * n_accepted / n_prior:.1f} percent) under "
            f"{criterion!r} for event {replay.record.event_id!r}: below the "
            f"{_WARN_FRACTION:.0%} headroom floor, the posterior tail "
            "resolution degrades below the Phase 1 spec section 11 standard."
        )
        warnings.append(message)
        logger.warning("%s", message)

    return SurvivalFilterResult(
        event_id=replay.record.event_id,
        criterion=criterion,
        accept=accept,
        accept_trans=accept_trans,
        accept_static=accept_static,
        initiation_occurred=initiation,
        n_prior=n_prior,
        n_accepted=n_accepted,
        rejection_fraction=float(rejection_fraction),
        decomposition=decompose(accept_static, accept_trans),
        warnings=warnings,
    )
