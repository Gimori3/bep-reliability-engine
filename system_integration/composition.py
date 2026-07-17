"""Series-system composition of per-mechanism conditional fragilities.

ADR-0038 decision 6; thesis "Multi-Mechanism Integration" section. Under
conditional independence given the water level h (after Pol RESS 2023):

    P_sys(h) = 1 - prod_i (1 - P_i(h)),   i in {overflow, fluvial_scour, bep}

Missing mechanisms compose over the available subset and are stamped absent
(``mechanisms`` lists what was present) — absence is visible, never a silent
zero. The known non-conservative exclusion of dynamic mechanism coupling is
a documented thesis limitation, not re-decided here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

__all__ = ["MechanismCurve", "SystemFragility", "compose", "max_within_section"]


@dataclass(frozen=True)
class MechanismCurve:
    """One mechanism's conditional P_f evaluated on the composition grid.

    Attributes
    ----------
    mechanism : str
        Mechanism label (``'bep'``, ``'overflow'``, ``'fluvial_scour'``).
    p_f : numpy.ndarray
        Conditional failure probabilities on the shared stage grid, [0, 1].
    source : str
        Provenance stamp (e.g. ``'phase2_posterior'``, ``'uemura_csv'``,
        ``'synthetic_stub'``) carried into the composed result.
    """

    mechanism: str
    p_f: NDArray[np.float64]
    source: str


@dataclass(frozen=True)
class SystemFragility:
    """The composed segment fragility and its per-mechanism decomposition.

    Attributes
    ----------
    stage_m_msl : numpy.ndarray
        The shared stage grid [m MSL].
    p_sys : numpy.ndarray
        Series-system conditional failure probability per stage.
    mechanisms : tuple of str
        Mechanism labels actually composed (absence is visible).
    per_mechanism : dict of str to numpy.ndarray
        Each mechanism's own conditional P_f on the grid.
    sources : dict of str to str
        Provenance stamp per mechanism.
    """

    stage_m_msl: NDArray[np.float64]
    p_sys: NDArray[np.float64]
    mechanisms: tuple[str, ...]
    per_mechanism: dict[str, NDArray[np.float64]]
    sources: dict[str, str]

    def dominance_share(self, mechanism: str) -> NDArray[np.float64]:
        """Mechanism i's share of the union failure probability per stage.

        Defined as ``P_i(h) / sum_j P_j(h)`` (the thesis's relative-dominance
        comparison of the mechanisms against the system curve); stages where
        every mechanism is 0 return 0 for all shares.
        """
        total = np.zeros_like(self.p_sys)
        for p in self.per_mechanism.values():
            total = total + p
        share = np.zeros_like(self.p_sys)
        np.divide(self.per_mechanism[mechanism], total, out=share, where=total > 0.0)
        return share


def compose(
    stage_m_msl: NDArray[np.float64],
    curves: list[MechanismCurve],
) -> SystemFragility:
    """Compose mechanism curves into the series-system segment fragility.

    Parameters
    ----------
    stage_m_msl : numpy.ndarray
        The shared stage grid [m MSL] every curve was evaluated on.
    curves : list of MechanismCurve
        At least one mechanism; each ``p_f`` must match the grid length and
        lie in [0, 1].

    Returns
    -------
    SystemFragility
        ``p_sys = 1 - prod(1 - p_i)`` with the decomposition retained.

    Raises
    ------
    ValueError
        On an empty mechanism list, duplicate mechanism labels, length
        mismatches, or probabilities outside [0, 1].
    """
    if not curves:
        raise ValueError("compose() needs at least one mechanism curve.")
    labels = [c.mechanism for c in curves]
    if len(set(labels)) != len(labels):
        raise ValueError(f"duplicate mechanism labels: {labels!r}.")
    stage = np.asarray(stage_m_msl, dtype=np.float64)

    survival = np.ones_like(stage)
    per_mechanism: dict[str, NDArray[np.float64]] = {}
    sources: dict[str, str] = {}
    for curve in curves:
        p = np.asarray(curve.p_f, dtype=np.float64)
        if p.shape != stage.shape:
            raise ValueError(
                f"{curve.mechanism}: p_f shape {p.shape} != grid {stage.shape}."
            )
        if np.any((p < 0.0) | (p > 1.0)):
            raise ValueError(f"{curve.mechanism}: p_f outside [0, 1].")
        survival = survival * (1.0 - p)
        per_mechanism[curve.mechanism] = p
        sources[curve.mechanism] = curve.source

    return SystemFragility(
        stage_m_msl=stage,
        p_sys=1.0 - survival,
        mechanisms=tuple(labels),
        per_mechanism=per_mechanism,
        sources=sources,
    )


def max_within_section(
    members: list[tuple[float, SystemFragility]],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Uemura's within-section rule: P_section(h) = max over member segments.

    Full dependence within a consequence section (Uemura et al. 2024
    Eq. 14; ADR-0043 decision 3): at every stage the section fails iff its
    weakest member fails, so the section conditional fragility is the
    pointwise maximum of the member system curves on their union grid
    (members interpolated linearly, clamped at their grid ends).

    Parameters
    ----------
    members : list of (kp, SystemFragility)
        The section's member segments and their composed curves.

    Returns
    -------
    tuple of (numpy.ndarray, numpy.ndarray, numpy.ndarray)
        ``(stage grid, section p_sys, argmax member kp per stage)`` — the
        third array names the governing segment at each stage.

    Raises
    ------
    ValueError
        On an empty member list.
    """
    if not members:
        raise ValueError("max_within_section() needs at least one member.")
    grid = np.unique(np.concatenate([frag.stage_m_msl for _, frag in members]))
    stack = np.vstack(
        [np.interp(grid, frag.stage_m_msl, frag.p_sys) for _, frag in members]
    )
    idx = np.argmax(stack, axis=0)
    kps = np.asarray([kp for kp, _ in members], dtype=np.float64)
    return grid, stack[idx, np.arange(grid.size)], kps[idx]
