"""Phase 2: Bayesian reliability updating of the BEP fragility by survival.

Monte Carlo Accept-Reject filtering of the Phase 1 prior realization set
against observed survival events (Schweckendiek 2014, direct reliability
updating with inequality information; thesis methodology chapter, Phase 2
sections). The physics is never reimplemented here: every limit-state
evaluation goes through the Phase 1 M8 evaluator
(``bep_reliability_engine.evaluator``), replayed under assumptions identical
to the Phase 1 run that produced the prior.

Module map (one responsibility each):

* :mod:`~bayesian_reliability_updating.events`: observed-event ingestion,
  the reusable loader that turns processed gauge and flood-trace extracts
  into per-section ``HydrographRecord`` loading records (2016 built in;
  2011 drops in with a new ``ObservedEventSource``).
* :mod:`~bayesian_reliability_updating.replay`: loads a Phase 1
  ``FragilityResult``, reconstructs the run's exact evaluation settings
  (config, geometry, regenerated stochastic seepage lengths) and replays
  M8 over every prior row against an observed event.
* :mod:`~bayesian_reliability_updating.filtering`: the Accept-Reject
  criterion, the survival-discrimination decomposition and the posterior
  sample-size diagnostics.
* :mod:`~bayesian_reliability_updating.fragility_update`: posterior
  fragility curves from the retained Phase 1 failure matrices (masked-matrix
  default path) with bootstrap bands and binomial CIs, plus the optional
  re-evaluation verification mode.
* :mod:`~bayesian_reliability_updating.sequential`: posterior-in,
  posterior-out composition of multiple survival events.
* :mod:`~bayesian_reliability_updating.posterior`: the ``PosteriorResult``
  artifact and its HDF5 + JSON persistence.
* :mod:`~bayesian_reliability_updating.analysis` /
  :mod:`~bayesian_reliability_updating.plots`: prior-versus-posterior
  marginals (C_e called out), decomposition tables and figures.
* :mod:`~bayesian_reliability_updating.pipeline` /
  :mod:`~bayesian_reliability_updating.cli`: the one-command entry point
  (``python -m bayesian_reliability_updating``).
"""

from __future__ import annotations

__version__ = "0.1.0"

from bayesian_reliability_updating.events import (  # noqa: F401
    ObservedEventSource,
    default_2016_source,
    observed_event_record,
)
from bayesian_reliability_updating.filtering import (  # noqa: F401
    SurvivalFilterResult,
    apply_survival_filter,
)
from bayesian_reliability_updating.posterior import PosteriorResult  # noqa: F401
from bayesian_reliability_updating.replay import (  # noqa: F401
    EventReplay,
    Phase1Run,
    load_phase1_run,
    replay_event,
)
from bayesian_reliability_updating.sequential import (  # noqa: F401
    UpdateState,
    apply_event,
    initial_state,
)
