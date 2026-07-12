"""Sequential survival updating: posterior-in, posterior-out event composition.

Additional survival events (the September 2011 flood, further historical
floods) compose as successive constraints on the same prior population
(thesis methodology: the 2011 peak levels are "applied sequentially to the
posterior parameter set derived from the 2016 filtering"). For pure
survival (indicator) evidence the posterior after events A then B is the
prior restricted to the intersection of the survival regions:

    pi_post(theta) proportional to pi_prior(theta) * 1[survive A] * 1[survive B]

so ordering is immaterial and the composition is exact on the Monte Carlo
sample as a logical AND of per-event acceptance masks over the ORIGINAL
prior rows. The implementation therefore evaluates every event over all N
prior rows and composes masks, rather than physically shrinking the sample
between events: masks over original row indices keep the provenance exact,
make the composition test (A then B equals B then A equals A-and-B) an
identity on arrays, and keep every event's decomposition reportable against
the full prior. The physical "posterior-in" reading is recovered exactly:
rows alive after the chain are those accepted by every event.

Physical note (ADR-0036): with ``l_ini = 0`` and recovery ``r_l = 0`` each
event is replayed from a virgin blanket, so events are mutually
independent constraints and no cross-event pipe-length memory exists. A
cross-event memory model (carrying l_e between events years apart) would
contradict the Phase 1 recovery evidence (Pol thesis: inter-flood recovery
on these timescales) and is deliberately out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
from numpy.typing import NDArray

from bayesian_reliability_updating.filtering import (
    SurvivalFilterResult,
    apply_survival_filter,
)
from bayesian_reliability_updating.replay import (
    EventReplay,
    Phase1Run,
    replay_event,
)
from bep_reliability_engine.hydrographs import HydrographRecord

__all__ = [
    "UpdateState",
    "apply_event",
    "initial_state",
]


@dataclass(frozen=True)
class UpdateState:
    """The updating chain's state after zero or more survival events.

    Attributes
    ----------
    run : Phase1Run
        The underlying Phase 1 run (theta, matrices, config, L draw).
    alive : numpy.ndarray, shape (N,), bool
        Rows accepted by every event applied so far (all True initially).
    chain : list
        One entry per applied event:
        ``(event_id, SurvivalFilterResult, EventReplay)``.
    """

    run: Phase1Run
    alive: NDArray[np.bool_]
    chain: list[tuple[str, SurvivalFilterResult, EventReplay]] = field(
        default_factory=list
    )

    @property
    def n_alive(self) -> int:
        """Rows surviving the whole chain."""
        return int(self.alive.sum())

    @property
    def theta_posterior(self) -> NDArray[np.float64]:
        """The posterior sample: prior rows surviving the whole chain."""
        return self.run.theta[self.alive, :]

    def chain_summary(self) -> list[dict[str, Any]]:
        """Per-event provenance for metadata (JSON-safe)."""
        summary = []
        alive_running = np.ones(self.run.n_samples, dtype=bool)
        for event_id, outcome, replay in self.chain:
            alive_running &= outcome.accept
            summary.append(
                {
                    "event_id": event_id,
                    "criterion": outcome.criterion,
                    "n_accepted_event": outcome.n_accepted,
                    "rejection_fraction_event": outcome.rejection_fraction,
                    "n_alive_after": int(alive_running.sum()),
                    "decomposition": outcome.decomposition,
                    "warnings": list(outcome.warnings),
                    "record": {
                        "event_id": replay.record.event_id,
                        "peak_m_msl": float(replay.record.peak),
                        "native_dt_s": float(replay.record.native_dt),
                        "duration_hours": float(replay.record.duration_hours),
                        "provenance": dict(replay.record.provenance),
                    },
                    "settings": dict(replay.settings),
                    "window_closure": dict(replay.window_closure),
                }
            )
        return summary


def initial_state(run: Phase1Run) -> UpdateState:
    """The pre-update state: every prior row alive, empty chain."""
    return UpdateState(run=run, alive=np.ones(run.n_samples, dtype=bool), chain=[])


def apply_event(
    state: UpdateState,
    record: HydrographRecord,
    *,
    criterion: str = "no_breach",
    progression_backend: str | None = None,
) -> tuple[UpdateState, SurvivalFilterResult, EventReplay]:
    """Apply one survival event to the chain (posterior-in, posterior-out).

    Replays the event over ALL original prior rows (see the module
    docstring for why masks compose over original indices) and returns the
    new state with ``alive`` narrowed by the event's acceptance mask.

    Parameters
    ----------
    state : UpdateState
        The current chain state.
    record : HydrographRecord
        The event's loading record at this run's section.
    criterion : str, optional
        Acceptance criterion for this event (default ``'no_breach'``).
    progression_backend : str, optional
        M7 backend override for this replay.

    Returns
    -------
    tuple of (UpdateState, SurvivalFilterResult, EventReplay)
        The narrowed state plus this event's filter outcome and replay.
    """
    replay = replay_event(state.run, record, progression_backend=progression_backend)
    outcome = apply_survival_filter(replay, criterion=criterion)
    new_state = replace(
        state,
        alive=state.alive & outcome.accept,
        chain=[*state.chain, (record.event_id, outcome, replay)],
    )
    return new_state, outcome, replay
