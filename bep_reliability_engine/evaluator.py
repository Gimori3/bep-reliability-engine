"""M8 ``limit_state_evaluator``: the shared-sample static/transient evaluator.

Single responsibility (spec §1, M8): orchestrate *both* limit states for one
realization behind one function, :func:`evaluate_realization`, enforcing the
shared-sample contract (spec Property 2, ADR-0002) — the same theta row and
the same computed r_e feed the static Sellmeijer comparison and the transient
Pol progression ODE. Independent static/transient execution tracks are banned
(spec §4): there is exactly one call site for H_c, l_c, lambda_in and r_e per
realization, and the static branch reuses the same H_c that anchors the
transient equilibrium curve H_eq.

This module is the stable public API that Phase 2 imports directly (spec §8):
``from bep_reliability_engine.evaluator import evaluate_realization``. Treat
the :func:`evaluate_realization` signature and the :class:`EvaluationResult`
field set as a frozen contract — Phase 2 Accept-Reject filtering re-runs this
exact function on the surviving theta rows against h_2016 and reads both
``Z_static`` and ``Z_transient`` for the survival-discrimination decomposition
(spec §8). M8 must stay importable without notebook context.

Shared preamble, then branch (spec §3, §4)
------------------------------------------
Per realization, O(1) preamble computed once::

    H_c, l_c            = M6 compute_critical_head(theta_row, geometry)
    lambda_in           = M4 leakage_length_in(k_aq, D_aq, D_bl, k_bl)
    lambda_out_eff      = M4 leakage_length_out(k_aq, D_aq, D_fore, k_fore, B_f)
    r_e                 = M4 response_factor(lambda_in, lambda_out_eff, L)

Static branch (scalar, O(1); spec §3 steps 4-6)::

    H_load_peak = r_e * (h_peak - z_toe)        # gross head; NO 0.3*D_bl term
    Z_static    = H_c - H_load_peak
    failure_static = (Z_static <= 0)

Transient branch (O(T); spec §3 steps 7-10) delegates the timestep loop to M7
``integrate_progression`` with an M4 head model built from the *same* r_e::

    head_model  = InstantaneousHead(r_e, z_toe)         # Phase 1 default
    result_m7   = integrate_progression(h_river, dt_s, head_model, z_toe, ...,
                                        H_c, l_c, L, l_ini, store_trajectory)
    Z_transient = L - result_m7.l_final_m
    failure_trans = (Z_transient <= 0)

The two branches use intentionally different driving heads (spec §3, §4,
ADR-0007, ADR-0008): the static comparator takes the gross translated peak
``r_e * (h_peak - z_toe)``, while inside M7 the rate is driven by
``H_erosion = Delta_h_blanket - 0.3*D_bl`` and the uplift/heave gate by the
un-reduced ``Delta_h_blanket``. The 0.3*D_bl head-convention offset between the
static and transient branches is deliberate and is one of the components of
the static-transient gap (spec §12, failure mode 4); it is not silently
absorbed.

Failure sign convention: failure is ``Z <= 0`` for both limit states (the
boundary Z = 0 counts as failure), consistent with M5's resistance-minus-load
convention (ADR-0008).

Trajectory storage is off by default (spec §2, §12 failure mode 6: ~800 MB per
cross-section at N = 1e5); ``store_trajectory=True`` retains the full l(t) for
the 2016 calibration run and visualization subsets.

Spec ambiguities flagged at the M8 boundary
-------------------------------------------
These are points where the spec does not fully pin the M8/M3 contract; the
choices made here are provisional and are called out for the user to confirm
when M3 (``hydrographs.py``) is implemented:

1. **HydrographRecord is undefined (M3 not implemented).** Spec §2 types the
   ``hydrograph`` argument as ``HydrographRecord``; that class does not exist
   yet. The annotation here is a forward reference and the function consumes
   only three documented fields by duck typing: ``.h`` (river-stage series),
   ``.peak`` (static comparator level) and ``.native_dt`` (timestep). The
   test suite uses a structural stand-in with those fields.
2. **Integration timestep source.** The spec does not state whether dt_s is
   ``hydrograph.native_dt`` or the spacing of ``hydrograph.t``. This boundary
   uses ``native_dt`` (the M3-recorded native resolution, spec §1, §11) and
   assumes ``h`` is uniformly sampled at that spacing.
3. **Static comparator level.** The static branch uses ``hydrograph.peak``
   (spec §1: "a representative scalar h_peak per event"), not a recomputed
   ``max(h)``; ``peak`` is treated as authoritative.
4. **geometry keys.** Spec §2 names the contents (L, z_toe, foreshore_width,
   D_fore, k_fore) but not the exact dict keys; the keys ``'L'``, ``'z_toe'``,
   ``'foreshore_width'``, ``'D_fore'`` and ``'k_fore'`` are assumed.
5. **Aquifer-lag wiring.** Spec §3 step 8a allows M8 to activate the M4 lag
   form, but the §2/§8 signature carries no lag flag, tau_aq or S_s. Phase 1
   defaults to :class:`~bep_reliability_engine.hydraulics.InstantaneousHead`;
   threading the lag flag (and per-realization tau_aq) through ``geometry`` or
   a config object is a documented extension, not yet in this signature.
6. **3D scale-exponent hook.** The alpha = -1/2 sensitivity hook of spec §12
   (failure mode 4) is not part of the stable §8 signature; M8 uses the M6
   default (2D, alpha = -1/3) and the hook is deferred.
7. **Units at the boundary.** Heads are assumed SI (m above one datum) and dt
   in seconds, i.e. M3 has already done all unit conversion (spec §1, M3;
   docs/conventions.md). Spec §2's "seconds or hours, units in metadata"
   note is taken to be resolved to SI by M3.

References
----------
Spec §1 (M8), §2 (the M8 input/output contract), §3 (the per-realization
execution sequence, steps 1-10), §4 (shared preamble then branch), §8 (Phase 2
handoff and the survival-discrimination decomposition). ADR-0001 (C_e a
random variable; static branch has no C_e exposure), ADR-0002 (shared-sample
contract), ADR-0007 (head datum), ADR-0008 (gate collapse and the
resistance-minus-load sign convention). Consumes M4 ``hydraulics``, M6
``sellmeijer``, M7 ``progression`` (which in turn consumes M5 ``initiation``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    leakage_length_in,
    leakage_length_out,
    response_factor,
)
from bep_reliability_engine.progression import integrate_progression
from bep_reliability_engine.sellmeijer import compute_critical_head

if TYPE_CHECKING:  # pragma: no cover
    # M3 is not implemented yet; HydrographRecord is a forward reference only
    # (spec ambiguity 1 in the module docstring). evaluate_realization consumes
    # the record structurally via .h, .peak and .native_dt.
    from numpy import float64

    from bep_reliability_engine.hydrographs import HydrographRecord

__all__ = [
    "EvaluationResult",
    "evaluate_realization",
]


@dataclass(frozen=True)
class EvaluationResult:
    """Both limit states and the diagnostics for one realization (spec §2).

    The frozen, non-negotiable Phase 2 handoff payload of a single M8 call
    (spec §2, §8). Field order follows the spec §2 output listing. All
    per-realization scalars are Python floats/bools; ``l_trajectory`` is the
    only array field and is ``None`` unless ``store_trajectory=True``.

    Attributes
    ----------
    Z_static : float
        Static limit-state margin ``H_c - r_e*(h_peak - z_toe)`` [m]
        (spec §3 step 5). Failure when ``Z_static <= 0``.
    Z_transient : float
        Transient limit-state margin ``L - l_e_final`` [m] (spec §3 step 9).
        Failure when ``Z_transient <= 0`` (l reached the seepage length L).
    l_e_final : float
        Final pipe length after the full hydrograph [m]; ``<= L`` always
        (M7 clips at L, breach absorbing). Equals ``l_ini`` when C_e -> 0 or
        the gate never opens.
    l_trajectory : numpy.ndarray of float, shape (T,), or None
        Full l(t) trajectory [m] when ``store_trajectory=True``, else None
        (spec §2, §12 failure mode 6). ``l_trajectory[-1] == l_e_final``.
    H_c : float
        Critical head [m] from M6 (Sellmeijer 2011 eq. (12)). The single
        source: this same value anchors the transient H_eq curve — no
        recomputation, no drift (spec §1, §4).
    l_c : float
        Critical pipe length [m] from M6 (Pol SIE 2024 eq. (13)); the
        (l_c, H_c) breakpoint of the transient H_eq curve.
    lambda_in : float
        Hinterland Mazure leakage length [m] from M4.
    r_e : float
        Response factor [-] from M4, in (0, 1). The *same* r_e drives both
        branches (shared-sample contract, ADR-0002); stochastic per
        realization (spec Property 3).
    t_uh : float
        Time [s] of first uplift+heave co-occurrence (M7 diagnostic), or NaN
        if it never occurs within the event.
    failure_static : bool
        ``Z_static <= 0`` (spec §3 step 6).
    failure_trans : bool
        ``Z_transient <= 0`` (spec §3 step 10).
    uplift_occurred : bool
        Per-event uplift latch at termination (Z_uplift < 0 at any step, M5).
    heave_occurred : bool
        Heave activated (Z_heave < 0) at any step (M5). Under the ADR-0008
        collapse this latches at the same step as ``uplift_occurred``.
    """

    Z_static: float
    Z_transient: float
    l_e_final: float
    l_trajectory: npt.NDArray[float64] | None
    H_c: float
    l_c: float
    lambda_in: float
    r_e: float
    t_uh: float
    failure_static: bool
    failure_trans: bool
    uplift_occurred: bool
    heave_occurred: bool


def evaluate_realization(
    theta_row: npt.NDArray[float64],
    hydrograph: HydrographRecord,
    geometry: dict,
    l_ini: float = 0.0,
    store_trajectory: bool = False,
) -> EvaluationResult:
    """Evaluate both limit states for one realization (M8, spec §2-§4).

    **This is the stable public API imported by Phase 2** (spec §8):
    ``from bep_reliability_engine.evaluator import evaluate_realization``.
    Phase 2 Accept-Reject filtering calls it once per prior theta row against
    the 2016 hydrograph and reads both ``Z_static`` and ``Z_transient`` for the
    survival-discrimination decomposition. The signature and the
    :class:`EvaluationResult` field set are therefore a frozen contract; the
    import surface is pinned by ``tests/test_evaluator_phase2_surface.py``
    (ADR-0011).

    Computes the shared preamble (H_c, l_c, lambda_in, r_e) exactly once,
    then evaluates the static Sellmeijer comparison and the transient Pol
    progression ODE against the *same* theta row and the *same* r_e
    (shared-sample contract, ADR-0002). The static branch reuses the same H_c
    that anchors the transient H_eq curve. Returns both Z values and the
    diagnostics Phase 2 needs (spec §8).

    Parameters
    ----------
    theta_row : numpy.ndarray, shape (7,)
        One realization's parameter vector in the canonical column order
        ``['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_s_sub', 'C_e']``
        (spec §2, M2 contract), in strict SI / kN-m^3 units. Consumed by all
        of M4, M6 and M7; ``C_e`` enters only the transient branch (the static
        branch has no C_e exposure by design, ADR-0001).
    hydrograph : HydrographRecord
        One event's loading record (M3). Consumed fields (duck-typed; M3 is
        not implemented yet, see module docstring ambiguity 1): ``h`` — the
        river-stage series [m above datum], shape (T,); ``peak`` — the scalar
        static comparator level h_peak [m above datum] (spec §1); and
        ``native_dt`` — the integration timestep dt_s [s], at which ``h`` is
        assumed uniformly sampled (ambiguities 2-3).
    geometry : dict
        Cross-section geometry (spec §2), read-only. Required keys:
        ``'L'`` (seepage length [m]), ``'z_toe'`` (polder surface elevation
        at the landside exit point [m above datum]; = h_e in Pol SIE 2024
        Eqs. (6) and (8), ADR-0007), ``'foreshore_width'`` (B_f [m]),
        ``'D_fore'`` and ``'k_fore'`` (deterministic foreshore blanket
        thickness [m] and vertical conductivity [m/s], ADR-0005). Key names
        are provisional (module docstring ambiguity 4).
    l_ini : float, optional
        Initial pipe length [m], default 0. Non-zero values bypass the M5
        uplift gate via the ``l_current > 0`` clause (an existing pipe means
        the blanket is already breached, spec §5) — the hook for event
        sequences and sensitivity studies. Phase 1 prior fragility uses 0.
    store_trajectory : bool, optional
        Retain the full l(t) trajectory in the result; default False to save
        memory (spec §2, §12 failure mode 6). Enable for the 2016 calibration
        run and visualization subsets.

    Returns
    -------
    EvaluationResult
        The pair ``(Z_static, Z_transient)`` plus the auxiliary diagnostics
        (H_c, l_c, lambda_in, r_e, t_uh, the latched uplift/heave flags,
        l_e_final, the two failure flags, and the optional trajectory). See
        :class:`EvaluationResult`.

    Notes
    -----
    Mathematical assumptions inherited from the consumed modules: 2D
    plane-strain Sellmeijer critical head (M6); exact quasi-static Mazure
    response factor under the semi-infinite-blanket schematization, computed
    per realization because r_e is stochastic (M4, spec Property 3); forward
    Euler with the M5 erosion-indicator gate and the monotone (positive-part)
    pipe-length update (M7). The static comparator uses the gross peak head
    ``r_e*(h_peak - z_toe)`` with no crack-resistance reduction; the transient
    rate uses ``H_erosion = Delta_h_blanket - 0.3*D_bl`` and the uplift/heave
    gate uses the un-reduced ``Delta_h_blanket`` — the 0.3*D_bl head-convention
    difference between the branches is deliberate (spec §3, §4, §12 failure
    mode 4; ADR-0007). Failure is ``Z <= 0`` for both limit states.

    The erosion coefficient ``C_e`` enters only the transient branch: it
    appears solely in the M7 progression rate, so ``Z_static`` is independent
    of ``C_e`` entirely (ADR-0001). This is intended — Phase 2 tightens C_e
    through the transient branch alone, which is exactly the laminar-flow
    conservatism the calibration targets (spec §4).

    Phase 1 builds the M4 head model as the instantaneous (quasi-static)
    form; the linear-reservoir lag hook is not threaded through this signature
    yet (module docstring ambiguity 5). The 3D scale-exponent hook (alpha =
    -1/2, spec §12) is likewise deferred (ambiguity 6).
    """
    seepage_length_m = float(geometry["L"])
    z_toe_m = float(geometry["z_toe"])

    # theta columns (canonical order; access by index per the M2 contract).
    k_aq_mps = float(theta_row[0])
    d_aq_m = float(theta_row[2])
    d_bl_m = float(theta_row[3])
    k_bl_mps = float(theta_row[4])
    gamma_s_sub_knpm3 = float(theta_row[5])
    c_e = float(theta_row[6])

    # --- Shared preamble (spec §3 steps 1-3; §4): computed exactly once and
    # consumed by both branches. H_c is the single source: the same value
    # feeds the static comparison and anchors the transient H_eq curve below
    # (spec §1, §4 -- no recomputation, no drift).
    sellmeijer = compute_critical_head(theta_row, geometry)
    h_c_m = float(sellmeijer.H_c)
    l_c_m = float(sellmeijer.l_c)

    lambda_in_m = float(leakage_length_in(k_aq_mps, d_aq_m, d_bl_m, k_bl_mps))
    lambda_out_eff_m = float(
        leakage_length_out(
            k_aq_mps,
            d_aq_m,
            geometry["D_fore"],
            geometry["k_fore"],
            geometry["foreshore_width"],
        )
    )
    # r_e is stochastic (four sampled variables) and lives in the per-realization
    # path -- never precomputed once (spec Property 3). The same r_e feeds both
    # branches (shared-sample contract, ADR-0002).
    r_e = float(response_factor(lambda_in_m, lambda_out_eff_m, seepage_length_m))

    # --- Static branch (spec §3 steps 4-6): scalar gross-head comparison. The
    # static comparator takes the gross translated peak head -- the un-reduced
    # Delta_h_blanket at h_peak, with NO 0.3*D_bl crack reduction (spec §3
    # step 4; §4). delta_h_blanket_peak is kept as its own named variable to
    # mirror the head separation M7 keeps internally per timestep.
    h_peak_m = float(hydrograph.peak)
    delta_h_blanket_peak_m = r_e * (h_peak_m - z_toe_m)
    z_static = h_c_m - delta_h_blanket_peak_m
    failure_static = bool(z_static <= 0.0)

    # --- Transient branch (spec §3 steps 7-10): delegate the irreducibly serial
    # timestep loop to the M7 timestepper, built on the SAME r_e via the M4 head
    # model. Inside integrate_progression the per-timestep un-reduced
    # Delta_h_blanket(t) drives the M5 uplift/heave gate while the reduced
    # H_erosion(t) = Delta_h_blanket(t) - 0.3*D_bl drives the rate -- the two
    # heads kept separate exactly as the M7 tests verify. Phase 1 uses the
    # instantaneous (quasi-static) M4 form (module docstring ambiguity 5).
    h_river_m = np.asarray(hydrograph.h, dtype=np.float64)
    dt_s = float(hydrograph.native_dt)
    head_model = InstantaneousHead(r_e, z_toe_m)
    progression = integrate_progression(
        h_river_m,
        dt_s,
        head_model,
        z_toe_m,
        c_e=c_e,
        k_aq_mps=k_aq_mps,
        d_bl_m=d_bl_m,
        gamma_s_sub_knpm3=gamma_s_sub_knpm3,
        h_c_m=h_c_m,
        l_c_m=l_c_m,
        seepage_length_m=seepage_length_m,
        l_ini_m=l_ini,
        store_trajectory=store_trajectory,
    )
    l_e_final = float(progression.l_final_m)
    z_transient = seepage_length_m - l_e_final
    failure_trans = bool(z_transient <= 0.0)

    return EvaluationResult(
        Z_static=z_static,
        Z_transient=z_transient,
        l_e_final=l_e_final,
        l_trajectory=progression.l_trajectory_m,
        H_c=h_c_m,
        l_c=l_c_m,
        lambda_in=lambda_in_m,
        r_e=r_e,
        t_uh=float(progression.t_uh_s),
        failure_static=failure_static,
        failure_trans=failure_trans,
        uplift_occurred=bool(progression.uplift_occurred),
        heave_occurred=bool(progression.heave_occurred),
    )
