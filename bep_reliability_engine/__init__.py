"""bep_reliability_engine: Phase 1 time-dependent BEP reliability engine.

Top-level entry points for the thin notebook drivers (spec §9): construct a
:class:`Config`, run :func:`run_fragility_analysis`, and persist/inspect the
returned :class:`FragilityResult`.
"""

from bep_reliability_engine.config import Config
from bep_reliability_engine.fragility import FragilityResult
from bep_reliability_engine.run import run_fragility_analysis

__all__ = ["Config", "FragilityResult", "run_fragility_analysis"]
