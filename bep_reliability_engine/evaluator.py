"""M8 ``limit_state_evaluator``: the shared-sample static/transient evaluator.

Single responsibility (spec §1, M8): orchestrate *both* limit states for one
realization behind one function, :func:`evaluate_realization`, enforcing the
shared-sample contract (spec Property 2, ADR-0002) — the same theta row and
the same computed r_e feed the static Sellmeijer comparison and the transient
Pol progression ODE. Independent static/transient execution tracks are banned
(spec §4): there is exactly one call site for l_c, lambda_in and r_e per
realization, and by default a single H_c feeds both the static comparison and
the transient equilibrium curve H_eq. The single H_c is relaxed in exactly one
controlled way — the optional ``alpha_exponent_transient`` recomputes a separate
transient H_c at the 3D scale exponent for the dimensional-bias decomposition
(ADR-0017); the shared θ_j and r_e (ADR-0002) are never relaxed.

Two entry points, one physics
-----------------------------
* :func:`evaluate_realization` — the **scalar** per-row API Phase 2 imports
  directly (spec §8): ``from bep_reliability_engine.evaluator import
  evaluate_realization``. Treat its signature and the :class:`EvaluationResult`
  field set as a frozen contract — Phase 2 Accept-Reject filtering re-runs this
  exact function on the surviving theta rows against h_2016 and reads both
  ``Z_static`` and ``Z_transient`` for the survival-discrimination decomposition
  (spec §8). It must stay importable without notebook context.
* :func:`evaluate_batch` — the **vectorized** production path the fragility
  sweep (``run.py``) calls once per conditioning level, evaluating all N
  realizations through the already-vectorized M4/M6/M7 kernels in one pass
  instead of a Python loop. It is bit-identical to looping
  :func:`evaluate_realization` over the rows and returns just the two boolean
  failure columns the sweep needs.

Both honor the deterministic run-owned Sellmeijer inputs (``alpha_exponent``,
``theta_repose_rad``, ``relative_density``, ``gamma_p_sub_kn_m3``; ADR-0015) as
keyword overrides forwarded to M6, and both accept a per-realization stochastic
seepage length L (``geometry['L']`` scalar by default; ``evaluate_batch`` takes
the vector via ``seepage_length_samples``, Phase 2 sets ``geometry['L']`` per
call). Independent static/transient execution tracks remain banned (spec §4).

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
6. **Deterministic Sellmeijer inputs wired, incl. the asymmetric-alpha
   decomposition (review item #6; ADR-0017).** Both entry points accept
   ``alpha_exponent`` (static/baseline), ``theta_repose_rad``,
   ``relative_density`` and ``gamma_p_sub_kn_m3`` as keyword overrides forwarded
   to M6, defaulting to None -> the M6 baseline (2D, alpha = -1/3); ``run.py``
   passes the config values, so an override is honored rather than silently
   ignored. ``alpha_exponent`` alone is a *symmetric* knob (it sets the single
   shared H_c, shifting both branches together). The transient-only override
   ``alpha_exponent_transient`` (ADR-0017) additionally recomputes the transient
   H_c at a different exponent while the static comparator keeps
   ``alpha_exponent``, delivering the spec §12 fm4 dimensional-bias decomposition
   (alpha = -1/2 on the transient branch only). It defaults to None, which
   preserves the single-source contract (transient H_c == static H_c,
   bit-identical to before).
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
from bep_reliability_engine.sellmeijer import (
    compute_critical_head,
    compute_critical_head_vectorized,
)

if TYPE_CHECKING:  # pragma: no cover
    # M3 is not implemented yet; HydrographRecord is a forward reference only
    # (spec ambiguity 1 in the module docstring). evaluate_realization consumes
    # the record structurally via .h, .peak and .native_dt.
    from numpy import float64

    from bep_reliability_engine.hydrographs import HydrographRecord

__all__ = [
    "EvaluationResult",
    "evaluate_realization",
    "evaluate_batch",
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
        Critical head [m] from M6 (Sellmeijer 2011 eq. (12)) for the **static**
        comparator, at the static scale exponent ``alpha_exponent``. By default
        this same value also anchors the transient H_eq curve (single-source
        contract, spec §1/§4); it diverges from ``H_c_transient`` only under the
        asymmetric dimensional-bias decomposition (ADR-0017).
    H_c_transient : float
        Critical head [m] anchoring the **transient** H_eq curve, at the
        transient scale exponent. Equals ``H_c`` by default (single source
        preserved, no drift); it is lower than ``H_c`` only when the 3D exponent
        ``alpha_exponent_transient = -1/2`` is applied to the transient branch
        alone for the spec §12 fm4 dimensional-bias decomposition (ADR-0017).
    l_c : float
        Critical pipe length [m] from M6 (Pol SIE 2024 eq. (13)); the
        (l_c, H_c_transient) breakpoint of the transient H_eq curve. Scale-
        exponent-independent, so it is shared by both branches.
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
    H_c_transient: float
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
    *,
    alpha_exponent: float | None = None,
    alpha_exponent_transient: float | None = None,
    theta_repose_rad: float | None = None,
    relative_density: float | None = None,
    gamma_p_sub_kn_m3: float | None = None,
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
        ``['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']``
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
    alpha_exponent, theta_repose_rad, relative_density, gamma_p_sub_kn_m3 : \
float, optional
        Deterministic run-owned Sellmeijer F_r/F_s inputs (ADR-0015), threaded
        to M6 ``compute_critical_head``. Keyword-only; each defaults to ``None``,
        which falls back to the pinned M6 constant, so an un-overridden call is
        bit-identical to the previous behaviour. ``run.py`` passes the config
        values. ``alpha_exponent`` is the **static / baseline** scale exponent
        (it sets the static H_c and, unless overridden below, the transient one
        too).
    alpha_exponent_transient : float, optional
        Keyword-only **transient-only** scale-exponent override for the spec §12
        fm4 dimensional-bias decomposition (ADR-0017). ``None`` (default) keeps
        the single-source contract — the transient H_eq anchor is the *same* H_c
        as the static comparator (bit-identical to the previous behaviour). When
        set (e.g. ``-1/2``) the transient H_c is recomputed at this exponent
        while the static comparator retains ``alpha_exponent``, so the 2D-vs-3D
        dimensional bias is isolated from the temporal bias rather than shifting
        both branches together.

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
    gamma_bl_sub_knpm3 = float(theta_row[5])
    c_e = float(theta_row[6])

    # --- Shared preamble (spec §3 steps 1-3; §4): computed exactly once and
    # consumed by both branches. H_c is the single source: the same value
    # feeds the static comparison and anchors the transient H_eq curve below
    # (spec §1, §4 -- no recomputation, no drift). The deterministic Sellmeijer
    # inputs are forwarded only when overridden (None -> M6 default), so an
    # un-threaded call is unchanged (ADR-0015 threading; review item #6).
    sell_kwargs: dict[str, float] = {}
    if alpha_exponent is not None:
        sell_kwargs["alpha_exponent"] = alpha_exponent
    if theta_repose_rad is not None:
        sell_kwargs["theta_repose_rad"] = theta_repose_rad
    if relative_density is not None:
        sell_kwargs["relative_density"] = relative_density
    if gamma_p_sub_kn_m3 is not None:
        sell_kwargs["gamma_p_sub_kn_m3"] = gamma_p_sub_kn_m3
    sellmeijer = compute_critical_head(theta_row, geometry, **sell_kwargs)
    h_c_m = float(sellmeijer.H_c)  # static (canonical) H_c
    l_c_m = float(sellmeijer.l_c)  # scale-exponent independent; shared

    # Transient H_c: by default identical to the static H_c (single-source
    # contract, spec §1/§4 -- no recomputation, no drift). Only when an
    # asymmetric transient scale exponent is requested (ADR-0017) is the
    # transient branch's H_c recomputed at alpha_exponent_transient, isolating
    # the 2D-vs-3D dimensional bias for the spec §12 fm4 decomposition.
    if alpha_exponent_transient is None:
        h_c_transient_m = h_c_m
    else:
        h_c_transient_m = float(
            compute_critical_head(
                theta_row,
                geometry,
                **{**sell_kwargs, "alpha_exponent": alpha_exponent_transient},
            ).H_c
        )

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
        gamma_bl_sub_knpm3=gamma_bl_sub_knpm3,
        h_c_m=h_c_transient_m,  # transient H_c anchors H_eq (= h_c_m by default)
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
        H_c_transient=h_c_transient_m,
        l_c=l_c_m,
        lambda_in=lambda_in_m,
        r_e=r_e,
        t_uh=float(progression.t_uh_s),
        failure_static=failure_static,
        failure_trans=failure_trans,
        uplift_occurred=bool(progression.uplift_occurred),
        heave_occurred=bool(progression.heave_occurred),
    )


def evaluate_batch(
    theta_matrix: npt.NDArray[float64],
    hydrograph: HydrographRecord,
    geometry: dict,
    *,
    l_ini: float = 0.0,
    seepage_length_samples: npt.NDArray[float64] | None = None,
    alpha_exponent: float | None = None,
    alpha_exponent_transient: float | None = None,
    theta_repose_rad: float | None = None,
    relative_density: float | None = None,
    gamma_p_sub_kn_m3: float | None = None,
) -> tuple[npt.NDArray[np.bool_], npt.NDArray[np.bool_]]:
    """Evaluate both limit states for all N realizations at one level (M8 batch).

    The **vectorized production path** the fragility sweep calls once per
    conditioning level (spec §6 across-realization vectorization). It is the
    batch twin of :func:`evaluate_realization`: same shared preamble, same two
    branches, same head conventions and the same ``Z <= 0`` failure rule, but
    every per-realization quantity is an ``(N,)`` array advanced through the
    already-vectorized M4/M6/M7 kernels in one pass instead of a Python loop.

    Reusing the identical kernels (``compute_critical_head_vectorized``, the M4
    leakage functions, ``InstantaneousHead`` and ``integrate_progression`` with
    array inputs) makes this **bit-identical** to looping
    :func:`evaluate_realization` over the rows — locked by
    ``tests/test_evaluator.py`` and, end to end, by
    ``tests/test_run.py::test_orchestration_matches_reference_loop``. Only the
    two boolean failure columns are returned (the bulk sweep keeps neither
    diagnostics nor trajectories, spec §12 fm6); Phase 2's per-row replay and
    survival-discrimination decomposition continue to use the scalar
    :func:`evaluate_realization`, whose diagnostics it needs.

    Parameters
    ----------
    theta_matrix : numpy.ndarray, shape (N, 7)
        The shared prior population in canonical column order (spec §2), SI /
        kN-m^3 units. Read-only.
    hydrograph : HydrographRecord
        This level's loading record (``peak`` is the static comparator level);
        the same record drives all N realizations.
    geometry : dict
        Cross-section geometry (the M8 flat dict). ``geometry['L']`` is the mean
        seepage length, used directly when ``seepage_length_samples`` is None.
    l_ini : float, optional
        Initial pipe length [m]; 0 for Phase 1 prior fragility.
    seepage_length_samples : numpy.ndarray, shape (N,), optional
        Per-realization stochastic seepage length L [m] from
        :func:`~bep_reliability_engine.sampling.sample_seepage_length`, drawn
        independently of theta. When None (default) L is the deterministic
        scalar ``geometry['L']`` for every realization. When provided, L_j pairs
        with theta_j row-for-row and enters H_c, l_c, r_e, H_eq and
        Z_transient = L_j - l_e_j.
    alpha_exponent, theta_repose_rad, relative_density, gamma_p_sub_kn_m3 : \
float, optional
        Deterministic run-owned Sellmeijer F_r/F_s inputs (ADR-0015), forwarded
        to M6 only when not None (else the pinned M6 constant). Same semantics
        as :func:`evaluate_realization`.
    alpha_exponent_transient : float, optional
        Transient-only scale-exponent override (ADR-0017). ``None`` (default)
        keeps the single-source H_c (the transient anchor equals the static
        H_c, bit-identical to before); when set, the transient H_c is recomputed
        at this exponent for the spec §12 fm4 dimensional-bias decomposition,
        while the static comparator retains ``alpha_exponent``.

    Returns
    -------
    failure_static, failure_trans : numpy.ndarray, shape (N,), dtype bool
        Per-realization static and transient failure indicators (``Z <= 0``).
    """
    theta = np.asarray(theta_matrix, dtype=np.float64)

    # theta columns by canonical position (spec §2). C_e (col 6) enters only the
    # transient branch (ADR-0001); d_70 (col 1) enters H_c via M6.
    k_aq_mps = theta[:, 0]
    d_aq_m = theta[:, 2]
    d_bl_m = theta[:, 3]
    k_bl_mps = theta[:, 4]
    gamma_bl_sub_knpm3 = theta[:, 5]
    c_e = theta[:, 6]

    z_toe_m = float(geometry["z_toe"])

    # Seepage length: deterministic scalar geometry['L'], or a per-realization
    # (N,) vector (stochastic L, sampled independently of theta, review item #3).
    if seepage_length_samples is None:
        seepage_length: float | npt.NDArray[float64] = float(geometry["L"])
        geometry_for_hc = geometry
    else:
        seepage_length = np.asarray(seepage_length_samples, dtype=np.float64)
        # M6 reads L from geometry['L']; override it with the vector so H_c and
        # l_c become per-realization in L (every M6 term broadcasts).
        geometry_for_hc = {**geometry, "L": seepage_length}

    # --- Shared preamble (vectorized), forwarding Sellmeijer overrides only when
    # set (None -> M6 default), exactly as the scalar path does.
    sell_kwargs: dict[str, float] = {}
    if alpha_exponent is not None:
        sell_kwargs["alpha_exponent"] = alpha_exponent
    if theta_repose_rad is not None:
        sell_kwargs["theta_repose_rad"] = theta_repose_rad
    if relative_density is not None:
        sell_kwargs["relative_density"] = relative_density
    if gamma_p_sub_kn_m3 is not None:
        sell_kwargs["gamma_p_sub_kn_m3"] = gamma_p_sub_kn_m3
    sellmeijer = compute_critical_head_vectorized(theta, geometry_for_hc, **sell_kwargs)
    h_c = np.asarray(sellmeijer.H_c, dtype=np.float64)  # static H_c
    l_c = np.asarray(sellmeijer.l_c, dtype=np.float64)  # scale-independent; shared

    # Transient H_c equals the static H_c by default (single source, spec §1/§4);
    # recomputed at the transient exponent only for the ADR-0017 decomposition.
    if alpha_exponent_transient is None:
        h_c_transient = h_c
    else:
        h_c_transient = np.asarray(
            compute_critical_head_vectorized(
                theta,
                geometry_for_hc,
                **{**sell_kwargs, "alpha_exponent": alpha_exponent_transient},
            ).H_c,
            dtype=np.float64,
        )

    lambda_in = leakage_length_in(k_aq_mps, d_aq_m, d_bl_m, k_bl_mps)
    lambda_out_eff = leakage_length_out(
        k_aq_mps,
        d_aq_m,
        geometry["D_fore"],
        geometry["k_fore"],
        geometry["foreshore_width"],
    )
    # r_e is stochastic (four sampled variables, plus L when L is sampled) and
    # feeds both branches (shared-sample contract, ADR-0002).
    r_e = response_factor(lambda_in, lambda_out_eff, seepage_length)

    # --- Static branch: gross translated peak head, no 0.3*D_bl reduction.
    h_peak_m = float(hydrograph.peak)
    delta_h_blanket_peak = r_e * (h_peak_m - z_toe_m)
    failure_static = (h_c - delta_h_blanket_peak) <= 0.0

    # --- Transient branch: the same r_e drives the M7 timestepper, vectorized
    # across realizations within each (serial) timestep (spec §6).
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
        gamma_bl_sub_knpm3=gamma_bl_sub_knpm3,
        h_c_m=h_c_transient,  # transient H_c anchors H_eq (= h_c by default)
        l_c_m=l_c,
        seepage_length_m=seepage_length,
        l_ini_m=l_ini,
        store_trajectory=False,
    )
    l_e_final = np.asarray(progression.l_final_m, dtype=np.float64)
    failure_trans = (seepage_length - l_e_final) <= 0.0

    return (
        np.asarray(failure_static, dtype=bool),
        np.asarray(failure_trans, dtype=bool),
    )
