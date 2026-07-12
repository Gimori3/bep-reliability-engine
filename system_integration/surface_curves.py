"""The Uemura surface-fragility seam: arrival contract, validation, stub.

ADR-0038 decision 5. The overflow and fluvial-scour conditional fragility
curves of Uemura (2025) are pre-calculated external inputs that are **not**
yet on disk in machine-readable form (class D). This module defines the
exact interface they must arrive in, validates arrivals loudly, and provides
a schema-exact synthetic stub so every downstream consumer is tested today.

Arrival format (long-form CSV, UTF-8, header row; one row per
(segment, mechanism, scenario, stage) sample):

======================  =====================================================
column                  contract
======================  =====================================================
``river``               ``Tokachi`` or ``Satsunai``
``bank``                ``right`` or ``left``
``kp``                  float, a 0.2 km registry node
``mechanism``           ``overflow`` or ``fluvial_scour``
``scenario``            ``historical`` or ``+4K`` (``plus4K`` accepted alias)
``stage_m_msl``         float, T.P. metres — the M3/ADR-0021 m MSL datum
``p_f``                 conditional failure probability in [0, 1]
======================  =====================================================

Within each (river, bank, kp, mechanism, scenario) group the stages must be
strictly increasing, ``p_f`` non-decreasing, and at least two samples must
exist. Any datum conversion (crest-relative, local datum) happens before the
CSV, by the data owner — the loader refuses to guess (ADR-0038).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "MECHANISMS",
    "SCENARIOS",
    "SurfaceCurve",
    "SurfaceCurveSet",
    "load_surface_curves",
    "synthetic_stub",
]

MECHANISMS: tuple[str, ...] = ("overflow", "fluvial_scour")
SCENARIOS: tuple[str, ...] = ("historical", "+4K")
_SCENARIO_ALIASES: dict[str, str] = {"plus4K": "+4K"}
_KNOWN_RIVER_BANKS: tuple[tuple[str, str], ...] = (
    ("Tokachi", "right"),
    ("Satsunai", "left"),
)

_SOURCE_STUB = "synthetic_stub"
_SOURCE_CSV = "uemura_csv"


@dataclass(frozen=True)
class SurfaceCurve:
    """One mechanism's conditional fragility at one segment and scenario.

    Attributes
    ----------
    river, bank : str
        Segment location.
    kp : float
        Segment node KP [km].
    mechanism : str
        ``'overflow'`` or ``'fluvial_scour'``.
    scenario : str
        ``'historical'`` or ``'+4K'``.
    stage_m_msl : numpy.ndarray
        Strictly increasing stage grid [m MSL].
    p_f : numpy.ndarray
        Conditional failure probabilities, non-decreasing, in [0, 1].
    """

    river: str
    bank: str
    kp: float
    mechanism: str
    scenario: str
    stage_m_msl: NDArray[np.float64]
    p_f: NDArray[np.float64]

    def evaluate(self, stage_m: NDArray[np.float64]) -> NDArray[np.float64]:
        """Interpolate P_f at ``stage_m`` (linear; clamped at the grid ends).

        Clamping matches the curves' semantics: below the lowest sampled
        stage the mechanism is not loaded (first value, typically 0); above
        the highest it holds its last sampled value — surface curves
        saturate near 1 at overtopping stages by construction.
        """
        stage = np.asarray(stage_m, dtype=np.float64)
        return np.interp(stage, self.stage_m_msl, self.p_f)


@dataclass(frozen=True)
class SurfaceCurveSet:
    """All loaded surface curves plus their provenance.

    Attributes
    ----------
    curves : tuple of SurfaceCurve
        Every (segment, mechanism, scenario) curve.
    source : str
        ``'uemura_csv'`` or ``'synthetic_stub'`` — stamped through to every
        composed result so stub numbers can never masquerade as Uemura's.
    """

    curves: tuple[SurfaceCurve, ...]
    source: str

    def lookup(
        self, *, river: str, kp: float, mechanism: str, scenario: str
    ) -> SurfaceCurve | None:
        """Return the matching curve, or None when the set has no coverage."""
        for curve in self.curves:
            if (
                curve.river == river
                and abs(curve.kp - kp) <= 1e-6
                and curve.mechanism == mechanism
                and curve.scenario == scenario
            ):
                return curve
        return None


def load_surface_curves(path: str | Path) -> SurfaceCurveSet:
    """Load and validate an Uemura surface-curve CSV (the arrival contract).

    Parameters
    ----------
    path : str or pathlib.Path
        Long-form CSV in the module-docstring format.

    Returns
    -------
    SurfaceCurveSet
        Validated curves, ``source='uemura_csv'``.

    Raises
    ------
    ValueError
        On missing columns, unknown categorical values, off-grid stages,
        probabilities outside [0, 1], non-increasing stage grids,
        decreasing ``p_f`` within a group, or groups with fewer than two
        samples — each with the offending group named.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "river",
        "bank",
        "kp",
        "mechanism",
        "scenario",
        "stage_m_msl",
        "p_f",
    }
    if not rows or not required <= set(rows[0].keys()):
        raise ValueError(
            f"{path.name}: expected columns {sorted(required)} "
            f"(got {sorted(rows[0].keys()) if rows else 'no rows'})."
        )

    groups: dict[tuple[str, str, float, str, str], list[tuple[float, float]]] = {}
    for i, row in enumerate(rows, start=2):  # header is line 1
        river, bank = row["river"], row["bank"]
        if (river, bank) not in _KNOWN_RIVER_BANKS:
            raise ValueError(
                f"{path.name} line {i}: unknown river/bank "
                f"{(river, bank)!r}; expected {_KNOWN_RIVER_BANKS!r}."
            )
        mechanism = row["mechanism"]
        if mechanism not in MECHANISMS:
            raise ValueError(
                f"{path.name} line {i}: unknown mechanism {mechanism!r}; "
                f"expected {MECHANISMS!r}."
            )
        scenario = _SCENARIO_ALIASES.get(row["scenario"], row["scenario"])
        if scenario not in SCENARIOS:
            raise ValueError(
                f"{path.name} line {i}: unknown scenario {row['scenario']!r}; "
                f"expected {SCENARIOS!r} (alias 'plus4K' accepted)."
            )
        kp = float(row["kp"])
        stage = float(row["stage_m_msl"])
        p_f = float(row["p_f"])
        if not 0.0 <= p_f <= 1.0:
            raise ValueError(
                f"{path.name} line {i}: p_f {p_f!r} outside [0, 1] for "
                f"{river} KP {kp:g} {mechanism}/{scenario}."
            )
        groups.setdefault((river, bank, kp, mechanism, scenario), []).append(
            (stage, p_f)
        )

    curves: list[SurfaceCurve] = []
    for (river, bank, kp, mechanism, scenario), samples in sorted(groups.items()):
        if len(samples) < 2:
            raise ValueError(
                f"{path.name}: group {river} KP {kp:g} {mechanism}/{scenario} "
                f"has {len(samples)} sample(s); at least two stages required."
            )
        stages = np.asarray([s for s, _ in samples], dtype=np.float64)
        p_fs = np.asarray([p for _, p in samples], dtype=np.float64)
        if not np.all(np.diff(stages) > 0.0):
            raise ValueError(
                f"{path.name}: stages not strictly increasing in group "
                f"{river} KP {kp:g} {mechanism}/{scenario} — rows must be "
                "sorted by stage within each group."
            )
        if np.any(np.diff(p_fs) < 0.0):
            raise ValueError(
                f"{path.name}: p_f decreases with stage in group {river} "
                f"KP {kp:g} {mechanism}/{scenario} — a conditional fragility "
                "curve must be non-decreasing."
            )
        curves.append(
            SurfaceCurve(
                river=river,
                bank=bank,
                kp=kp,
                mechanism=mechanism,
                scenario=scenario,
                stage_m_msl=stages,
                p_f=p_fs,
            )
        )
    return SurfaceCurveSet(curves=tuple(curves), source=_SOURCE_CSV)


def synthetic_stub(
    *,
    river: str = "Tokachi",
    bank: str = "right",
    kps: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0),
    stage_range_m: tuple[float, float] = (36.0, 46.0),
    n_stages: int = 21,
) -> SurfaceCurveSet:
    """Schema-exact fake surface curves for tests and plumbing runs.

    Smooth logistic-shaped overflow/scour curves per KP and scenario, with
    the +4K curve shifted 0.5 m lower (higher P_f at a given stage) so
    scenario plumbing is distinguishable in tests. Deterministic — no RNG.

    Returns
    -------
    SurfaceCurveSet
        ``source='synthetic_stub'``; the CLI refuses these without
        ``--allow-stub`` (ADR-0038 decision 5).
    """
    lo, hi = stage_range_m
    stages = np.linspace(lo, hi, n_stages)
    curves: list[SurfaceCurve] = []
    for kp in kps:
        for mechanism, midpoint_offset in (("overflow", 0.75), ("fluvial_scour", 0.55)):
            for scenario, shift in (("historical", 0.0), ("+4K", -0.5)):
                midpoint = lo + midpoint_offset * (hi - lo) + shift
                p_f = 1.0 / (1.0 + np.exp(-(stages - midpoint) / 0.6))
                p_f[0] = 0.0  # not loaded below the sampled range
                curves.append(
                    SurfaceCurve(
                        river=river,
                        bank=bank,
                        kp=float(kp),
                        mechanism=mechanism,
                        scenario=scenario,
                        stage_m_msl=stages.copy(),
                        p_f=np.maximum.accumulate(p_f),  # monotone non-decreasing
                    )
                )
    return SurfaceCurveSet(curves=tuple(curves), source=_SOURCE_STUB)
