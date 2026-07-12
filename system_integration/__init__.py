"""Phase 3 system integration: multi-mechanism composition + d4PDF hazard.

The RQ3/RQ4 composition layer (ADR-0038): series-system integration of the
BEP fragility (Phase 2 posteriors by default) with Uemura's pre-calculated
overflow/fluvial-scour curves at the 200 m segment level, driven by the
d4PDF historical (HPB) versus +4K (HFB) stage-frequency at each section.
Physics-free by construction — everything hydraulic comes through the M3
public interfaces, everything probabilistic through persisted Phase 1/2
artifacts and the public ADR-0037 transform.

One command::

    python -m system_integration --help
"""

from system_integration.bep_input import FragilityCurve, load_bep_curve
from system_integration.composition import MechanismCurve, SystemFragility, compose
from system_integration.hazard import NodeHazard, load_node_hazard
from system_integration.segments import Segment, SegmentRegistry, build_registry
from system_integration.surface_curves import (
    SurfaceCurveSet,
    load_surface_curves,
    synthetic_stub,
)

__all__ = [
    "FragilityCurve",
    "MechanismCurve",
    "NodeHazard",
    "Segment",
    "SegmentRegistry",
    "SurfaceCurveSet",
    "SystemFragility",
    "build_registry",
    "compose",
    "load_bep_curve",
    "load_node_hazard",
    "load_surface_curves",
    "synthetic_stub",
]
