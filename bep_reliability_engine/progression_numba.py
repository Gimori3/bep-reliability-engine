"""Opt-in Numba backend for the M7 timestepper (ADR-0029).

A JIT-compiled, realization-parallel twin of
:func:`~bep_reliability_engine.progression.integrate_progression` for the
vectorized production sweep. The numpy path advances all N realizations one
timestep at a time (~20 full passes over N-length arrays per step, memory-
bandwidth bound); this kernel swaps the loop nest — realizations outer
(``numba.prange``), time inner — so each realization's entire trajectory stays
in registers, and evaluates the fractional power only where the I_er gate is
open with positive overload. Same forward Euler, same operation order per
element, same two-heads discipline (spec §3 steps a-j; ADR-0027/0008).

Equivalence contract (ADR-0029)
-------------------------------
The per-element arithmetic chain is written to match the numpy path operation
for operation, so add/sub/mul/div/min/max and every comparison round
identically (IEEE-exact). The single non-reproducible operation is the
fractional power ``x**0.81``: numpy dispatches to its own pow loop while LLVM
lowers ``**`` to the platform ``pow``, and the two may differ in the last ulp.
The backend is therefore **opt-in** (``config.timestepper.progression_backend
= 'numba'``; default ``'numpy'`` is untouched) and its guarantee is numerical
equivalence to better than 1e-10 on every float output plus exact equality of
every boolean/latch output — proven by ``tests/test_progression_numba.py`` —
NOT bit-identity. A run's backend is recorded in the persisted config
snapshot, so no numba result can masquerade as a numpy one.

Scope restrictions (both enforced, not silently ignored)
--------------------------------------------------------
* **Instantaneous head model only.** The M4 translation is inlined as
  ``h_aq = z_toe + r_e*(h - z_toe)`` (Pol SIE 2024 Eq. (10)). The lagged
  form is not implemented here; M8 refuses the numba backend when the lag
  is active rather than dropping the lag (ADR-0029).
* **No trajectory storage.** The production sweep never stores trajectories
  (spec §12 fm6); diagnostic/trajectory runs use the numpy path.

The integration math is deliberately duplicated from ``progression.py`` (the
kernels cannot be called from nopython code); the numpy path remains the
single *authoritative* implementation, and the cross-backend equivalence test
is the drift guard that keeps this copy honest.

Units: strict SI, as everywhere in M7 (docs/conventions.md).

References
----------
Spec §6 (vectorization; the Numba note), §10 (numba "held in reserve. Only if
profiling demands it" — the ADR-0029 profile demanded it), §12 Tradeoff 1.
ADR-0029 (backend decision, equivalence caveats). Pol SIE 2024 Eqs. (5)-(11).
"""

from __future__ import annotations

import numpy as np
from numba import njit, prange
from numpy.typing import ArrayLike, NDArray

from bep_reliability_engine.constants import GAMMA_W
from bep_reliability_engine.progression import (
    EQUILIBRIUM_END_FACTOR,
    POL_RATE_COEFFICIENT,
    POL_RATE_EXPONENT,
    ProgressionResult,
    resolve_crack_resistance_factor,
)

__all__ = ["integrate_progression_numba"]


@njit(parallel=True, cache=True, error_model="numpy", nogil=True)
def _integrate_kernel(  # pragma: no cover - exercised via the wrapper
    h_river: NDArray[np.float64],
    dt_s: float,
    r_e: NDArray[np.float64],
    z_toe_m: float,
    c_e: NDArray[np.float64],
    k_aq: NDArray[np.float64],
    d_bl: NDArray[np.float64],
    gamma_bl_sub: NDArray[np.float64],
    h_c: NDArray[np.float64],
    l_c: NDArray[np.float64],
    length: NDArray[np.float64],
    l_ini: NDArray[np.float64],
    crack_factor: float,
) -> tuple[
    NDArray[np.float64], NDArray[np.bool_], NDArray[np.bool_], NDArray[np.float64]
]:
    """Realization-parallel forward-Euler kernel (spec §3 steps a-j).

    All inputs are pre-broadcast, C-contiguous ``(N,)`` float64 arrays except
    the ``(T,)`` stage series and the scalars; the wrapper owns validation.
    ``error_model='numpy'`` gives IEEE inf/nan division semantics, so the
    D_bl = 0 laboratory exit gradient resolves exactly as the numpy path's
    errstate-guarded ``z_heave`` does.
    """
    n_realizations = c_e.shape[0]
    n_steps = h_river.shape[0]

    l_final = np.empty(n_realizations, dtype=np.float64)
    uplift_out = np.zeros(n_realizations, dtype=np.bool_)
    heave_out = np.zeros(n_realizations, dtype=np.bool_)
    t_uh_out = np.full(n_realizations, np.nan, dtype=np.float64)

    for j in prange(n_realizations):
        r_e_j = r_e[j]
        c_e_j = c_e[j]
        k_aq_j = k_aq[j]
        d_bl_j = d_bl[j]
        h_c_j = h_c[j]
        l_c_j = l_c[j]
        length_j = length[j]

        # Time-invariant factors, the same expressions the numpy path hoists.
        crack_term = crack_factor * d_bl_j
        uplift_resistance = (gamma_bl_sub[j] * d_bl_j) / GAMMA_W
        heave_resistance = gamma_bl_sub[j] / GAMMA_W
        rate_coefficient = POL_RATE_COEFFICIENT * c_e_j
        falling_slope = (EQUILIBRIUM_END_FACTOR - 1.0) * h_c_j / (length_j - l_c_j)

        l_current = l_ini[j]
        uplift_ever = False
        heave_ever = False
        t_uh = np.nan

        for k in range(n_steps):
            h_t = h_river[k]

            # Whole-step skip below z_toe: same proof as the numpy fast path
            # (delta_h <= 0 so neither gate can fire and dl = 0). Valid at
            # k = 0 too — the kernel has no array-shape seeding to preserve.
            if h_t <= z_toe_m:
                continue

            # (a, b) instantaneous M4 translation, then the un-reduced
            # blanket overpressure driving uplift and heave.
            h_aq = z_toe_m + r_e_j * (h_t - z_toe_m)
            delta_h_blanket = h_aq - z_toe_m

            # (c) erosion driver on the RAW outer level (ADR-0027).
            h_erosion = (h_t - z_toe_m) - crack_term

            # (d, e) uplift limit state and per-event latch (M5 z_uplift).
            uplift_now = (uplift_resistance - delta_h_blanket) < 0.0
            uplift_ever = uplift_ever or uplift_now

            # (f, g, h) heave, checked instantaneously (M5 z_heave). At
            # D_bl = 0 the division yields inf/nan and the comparison
            # resolves to the intended gate, exactly like the numpy path.
            heave_now = (heave_resistance - delta_h_blanket / d_bl_j) < 0.0

            # t_uh diagnostic: first uplift+heave co-occurrence.
            if uplift_now and heave_now and np.isnan(t_uh):
                t_uh = k * dt_s
            heave_ever = heave_ever or heave_now

            # (i) erosion-indicator gate (M5 erosion_indicator).
            i_er = (uplift_ever or (l_current > 0.0)) and heave_now
            if not i_er:
                # dl = 0; min(l, L) leaves l unchanged (l <= L invariant).
                continue

            # (j) equilibrium head (Pol Eq. (11), per-realization anchors).
            l_clamped = min(max(l_current, 0.0), length_j)
            if l_clamped < l_c_j:
                h_eq = h_c_j * (l_clamped / l_c_j)
            else:
                h_eq = h_c_j + falling_slope * (l_clamped - l_c_j)

            # (j) progression rate (Pol Eq. (5)); the fractional power runs
            # only for positive overload — it is exactly zero otherwise.
            overload = h_erosion - h_eq
            if overload > 0.0:
                velocity_group = k_aq_j * overload / length_j
                rate = rate_coefficient * velocity_group**POL_RATE_EXPONENT
                # Forward Euler with the absorbing breach clip at L.
                l_current = min(l_current + rate * dt_s, length_j)

        l_final[j] = l_current
        uplift_out[j] = uplift_ever
        heave_out[j] = heave_ever
        t_uh_out[j] = t_uh

    return l_final, uplift_out, heave_out, t_uh_out


def integrate_progression_numba(
    h_river_m: ArrayLike,
    dt_s: float,
    r_e: ArrayLike,
    z_toe_m: float,
    c_e: ArrayLike,
    k_aq_mps: ArrayLike,
    d_bl_m: ArrayLike,
    gamma_bl_sub_knpm3: ArrayLike,
    h_c_m: ArrayLike,
    l_c_m: ArrayLike,
    seepage_length_m: ArrayLike,
    *,
    l_ini_m: ArrayLike = 0.0,
    crack_resistance_factor: float | None = None,
) -> ProgressionResult:
    """Numba-parallel forward-Euler timestepper (opt-in M7 backend, ADR-0029).

    Drop-in batch twin of
    :func:`~bep_reliability_engine.progression.integrate_progression` for the
    instantaneous head model: instead of a ``head_model`` it takes the
    response factor ``r_e`` directly and inlines the M4 translation
    ``h_aq = z_toe + r_e * (h - z_toe)`` (Pol SIE 2024 Eq. (10)). Same
    forward Euler (spec §10 — never solve_ivp), same I_er gating, same
    monotone positive-part pipe-length update, same absorbing breach clip.

    Parameters
    ----------
    h_river_m : array_like of float, shape (T,)
        River stage series [m above datum], uniformly sampled at ``dt_s``.
        Must be finite throughout (validated; the numpy path is the one that
        propagates NaN for diagnostic purposes).
    dt_s : float
        Timestep [s].
    r_e : array_like of float
        Response factor [-] per realization, from M4 ``response_factor``.
    z_toe_m : float
        Polder surface elevation at the landside exit point [m above datum].
    c_e, k_aq_mps, d_bl_m, gamma_bl_sub_knpm3 : array_like of float
        Theta columns, exactly as for ``integrate_progression``.
    h_c_m, l_c_m : array_like of float
        M6 critical head and critical pipe length per realization.
    seepage_length_m : array_like of float
        Seepage length L [m]; scalar or per-realization ``(N,)``.
    l_ini_m : array_like of float, optional
        Initial pipe length [m], default 0. Must satisfy ``l_ini <= L``
        (validated — the numpy path's per-step monotonicity assert catches
        this; the kernel guarantees monotonicity structurally instead).
    crack_resistance_factor : float, optional
        Keyword-only ADR-0051 override of the Pol SIE 2024 Eq. (6) crack
        coefficient, resolved through the shared
        :func:`~bep_reliability_engine.progression.resolve_crack_resistance_factor`
        so both backends read one definition. ``None`` (default) is the
        published 0.3; ``0.0`` gives the gross erosion head. Unlike the
        ADR-0041 end factor, this knob **is** supported here: the coefficient
        is a kernel argument rather than a baked-in constant.

    Returns
    -------
    ProgressionResult
        Identical field set to the numpy path, all per-realization fields
        shape ``(N,)``; ``l_trajectory_m`` is always None (trajectory storage
        is a numpy-path-only feature; spec §12 fm6).

    Raises
    ------
    ValueError
        If any input is non-finite, if ``l_ini > L`` anywhere, if C_e is
        negative anywhere (the kernel relies on ``dl >= 0`` being structural;
        the numpy path enforces the same invariant with its per-step assert),
        or if ``crack_resistance_factor`` is negative (ADR-0051).

    Notes
    -----
    Numerical equivalence to the numpy path is better than 1e-10 on
    ``l_final_m`` and ``t_uh_s`` and exact on the boolean latches — but NOT
    bit-identical, because the platform ``pow`` may differ from numpy's in
    the last ulp (module docstring; ADR-0029). First call per process pays
    one JIT compilation (cached on disk thereafter via ``cache=True``).
    """
    crack_factor = resolve_crack_resistance_factor(crack_resistance_factor)
    h_river = np.ascontiguousarray(np.asarray(h_river_m, dtype=np.float64))
    if not np.all(np.isfinite(h_river)):
        raise ValueError(
            "integrate_progression_numba requires a finite stage series; "
            "use the numpy backend to diagnose non-finite hydrographs."
        )

    # Broadcast every per-realization input to one common (N,) shape. Scalars
    # are valid inputs (N = 1); the result shape then matches the broadcast
    # realization shape exactly as the numpy path produces it.
    broadcast = np.broadcast(
        np.asarray(r_e, dtype=np.float64),
        np.asarray(c_e, dtype=np.float64),
        np.asarray(k_aq_mps, dtype=np.float64),
        np.asarray(d_bl_m, dtype=np.float64),
        np.asarray(gamma_bl_sub_knpm3, dtype=np.float64),
        np.asarray(h_c_m, dtype=np.float64),
        np.asarray(l_c_m, dtype=np.float64),
        np.asarray(seepage_length_m, dtype=np.float64),
        np.asarray(l_ini_m, dtype=np.float64),
    )
    realization_shape = broadcast.shape

    def _as_column(value: ArrayLike) -> NDArray[np.float64]:
        arr = np.asarray(value, dtype=np.float64)
        return np.ascontiguousarray(np.broadcast_to(arr, realization_shape).reshape(-1))

    r_e_v = _as_column(r_e)
    c_e_v = _as_column(c_e)
    k_aq_v = _as_column(k_aq_mps)
    d_bl_v = _as_column(d_bl_m)
    gamma_v = _as_column(gamma_bl_sub_knpm3)
    h_c_v = _as_column(h_c_m)
    l_c_v = _as_column(l_c_m)
    length_v = _as_column(seepage_length_m)
    l_ini_v = _as_column(l_ini_m)

    for name, column in (
        ("r_e", r_e_v),
        ("c_e", c_e_v),
        ("k_aq_mps", k_aq_v),
        ("d_bl_m", d_bl_v),
        ("gamma_bl_sub_knpm3", gamma_v),
        ("h_c_m", h_c_v),
        ("l_c_m", l_c_v),
        ("seepage_length_m", length_v),
        ("l_ini_m", l_ini_v),
    ):
        if not np.all(np.isfinite(column)):
            raise ValueError(f"integrate_progression_numba: {name} is non-finite.")
    if np.any(c_e_v < 0.0):
        raise ValueError("integrate_progression_numba: C_e must be >= 0.")
    if np.any(l_ini_v > length_v):
        raise ValueError("integrate_progression_numba: l_ini exceeds L.")

    l_final, uplift_ever, heave_ever, t_uh = _integrate_kernel(
        h_river,
        float(dt_s),
        r_e_v,
        float(z_toe_m),
        c_e_v,
        k_aq_v,
        d_bl_v,
        gamma_v,
        h_c_v,
        l_c_v,
        length_v,
        l_ini_v,
        crack_factor,
    )

    return ProgressionResult(
        l_final_m=l_final.reshape(realization_shape),
        l_trajectory_m=None,
        uplift_occurred=uplift_ever.reshape(realization_shape),
        heave_occurred=heave_ever.reshape(realization_shape),
        t_uh_s=t_uh.reshape(realization_shape),
    )
