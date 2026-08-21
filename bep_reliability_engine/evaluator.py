"""M8 ``limit_state_evaluator``: the shared-sample static/transient evaluator.

Single responsibility (spec §1, M8): orchestrate *both* limit states for one
realization behind one function, :func:`evaluate_realization`, enforcing the
shared-sample contract (spec Property 2, ADR-0002) — the same theta row feeds
the static Sellmeijer comparison and the transient Pol progression ODE, so the
static-vs-transient gap is a same-sample comparison, not sampling noise.
Independent static/transient execution tracks are banned (spec §4): there is
exactly one call site for l_c, lambda_in and r_e per realization, and by default
a single H_c feeds both the static comparison and the transient equilibrium
curve H_eq. Note (ADR-0028): r_e now drives ONLY the transient uplift/heave gate
— the static branch uses the raw Sellmeijer head and is r_e-independent — so the
ADR-0002 "same r_e feeds both" clause is moot for the static branch; the
shared-sample intent (same θ_j, one call) is preserved. The single H_c is
relaxed in exactly one controlled way — the optional ``alpha_exponent_transient``
recomputes a separate transient H_c at the 3D scale exponent for the
dimensional-bias decomposition (ADR-0017); the shared θ_j is never relaxed.

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

    H_load_peak = h_peak - z_toe        # RAW gross head; NO r_e, NO 0.3*D_bl
    Z_static    = H_c - H_load_peak
    failure_static = (Z_static <= 0)

Transient branch (O(T); spec §3 steps 7-10) delegates the timestep loop to M7
``integrate_progression`` with an M4 head model built from the *same* r_e::

    head_model  = InstantaneousHead(r_e, z_toe)         # Phase 1 default
    result_m7   = integrate_progression(h_river, dt_s, head_model, z_toe, ...,
                                        H_c, l_c, L, l_ini, store_trajectory)
    Z_transient = L - result_m7.l_final_m
    failure_trans = (Z_transient <= 0)

Each model is used exactly as its author intended (ADR-0027, ADR-0028, ADR-0008):
the static Sellmeijer comparator takes the RAW gross head across the structure
``h_peak - z_toe`` (Sellmeijer 2011's "critical hydraulic head across structure";
no r_e, no crack term), and inside M7 the rate is driven by the RAW crack-reduced
head ``H_erosion = (h - z_toe) - 0.3*D_bl`` (Pol SIE 2024 Eq. (6): after heave
ruptures the blanket the exit is unfiltered) while the uplift/heave gate uses the
r_e-attenuated ``Delta_h_blanket`` (Eq. (10)). r_e therefore drives ONLY the
uplift/heave initiation and does NOT enter either piping head; the static branch
is entirely r_e-independent. The two piping heads differ by exactly the 0.3*D_bl
crack loss (transient only) -- the clean head-convention component of the
static-transient gap (spec §12, failure mode 4), r_e having dropped out of both.

Failure sign convention: failure is ``Z <= 0`` for both limit states (the
boundary Z = 0 counts as failure), consistent with M5's resistance-minus-load
convention (ADR-0008).

Trajectory storage is off by default (spec §2, §12 failure mode 6: ~800 MB per
cross-section at N = 1e5); ``store_trajectory=True`` retains the full l(t) for
the 2016 calibration run and visualization subsets.

Spec ambiguities flagged at the M8 boundary
-------------------------------------------
These are points where the spec did not fully pin the M8/M3 contract. The
choices below were pinned by ADR-0010 and are now confirmed against the built
M3 (``hydrographs.py``, ADR-0019/0020); the numbering is kept for
cross-reference stability:

1. **HydrographRecord is consumed structurally (resolved; M3 built).** Spec §2
   types the ``hydrograph`` argument as ``HydrographRecord``; the concrete
   class now lives in M3 (``hydrographs.HydrographRecord``, ADR-0019/0020).
   The function still consumes only three documented fields by duck typing
   per ADR-0010 — ``.h`` (river-stage series), ``.peak`` (static comparator
   level) and ``.native_dt`` (timestep) — so structural stand-ins (used by
   parts of the test suite and permitted to Phase 2 for the 2016 record)
   remain valid alongside the real M3 type.
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
4b. **Landside-toe gradient relief (ADR-0050).** The optional
   ``toe_gradient_relief_factor`` scales the response factor handed to the M4
   head model, and therefore scales ``Delta_h_blanket`` and the exit gradient
   ``i_exit`` by the same factor at every timestep. It is the engine handle for
   the one quantity Japanese guidance names for a landside toe drain (PWRI 2014
   Table 7.1.1, "reduce the hydraulic gradient at the landside toe"), and by
   ADR-0028 it reaches that gate and nothing else. Default None; the reported
   ``r_e`` stays the unrelieved physical response factor.
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
    # Typing-only import: M8 consumes the record structurally via .h, .peak
    # and .native_dt (ADR-0010), so the concrete M3 HydrographRecord is not a
    # runtime dependency and duck-typed stand-ins remain valid.
    from numpy import float64

    from bep_reliability_engine.hydrographs import HydrographRecord

__all__ = [
    "BatchDiagnostics",
    "EvaluationResult",
    "evaluate_realization",
    "evaluate_batch",
    "evaluate_batch_diagnostics",
]


def _gate_response_factor(r_e, toe_gradient_relief_factor: float | None):
    """Scale the response factor the uplift/heave gate sees (ADR-0050).

    The landside-toe exit gradient is ``i_exit = Delta_h_blanket / D_bl`` with
    ``Delta_h_blanket = r_e * (h - z_toe)``, so multiplying ``r_e`` by a relief
    factor multiplies ``i_exit`` by exactly the same factor at every timestep.
    Since ADR-0028 ``r_e`` reaches the uplift/heave gate and nothing else --
    both piping heads are r_e-independent and the static comparator is entirely
    r_e-independent -- this is a perturbation of the one quantity Japanese
    guidance names for a landside toe drain (PWRI 2014 Table 7.1.1) and of
    nothing else.

    Returns the input unchanged for ``None`` and for ``1.0`` (both are the
    undrained baseline), so the axis is bit-identical when off.

    Parameters
    ----------
    r_e : float or numpy.ndarray
        The physical M4 response factor. Never mutated: the value reported in
        ``EvaluationResult.r_e`` / ``BatchDiagnostics.r_e`` stays the
        blanket-aquifer property, and the drain credit is recorded separately
        in run metadata.
    toe_gradient_relief_factor : float or None
        Fraction of the undrained landside-toe exit gradient that survives the
        drain, in ``(0, 1]``. None is the undrained baseline.

    Raises
    ------
    ValueError
        If the factor is outside ``(0, 1]``. The mapping is one-sided: the
        guidance states the countermeasure *reduces* the gradient, so a value
        above 1 would be an aggravation it does not license, and a value of 0
        would assert a perfect drain rather than bracket one.
    """
    if toe_gradient_relief_factor is None:
        return r_e
    factor = float(toe_gradient_relief_factor)
    if not 0.0 < factor <= 1.0:
        raise ValueError(
            "toe_gradient_relief_factor must lie in (0, 1]; got "
            f"{toe_gradient_relief_factor!r}."
        )
    if factor == 1.0:
        return r_e
    return r_e * factor


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
        Static limit-state margin ``H_c - (h_peak - z_toe)`` [m] on the RAW
        gross head across the structure (Sellmeijer 2011; no r_e, ADR-0028)
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
        Response factor [-] from M4, in (0, 1). Drives the transient
        uplift/heave gate only (Eq. (10)); the static branch and both piping
        heads are r_e-independent (ADR-0027/ADR-0028). Stochastic per
        realization (spec Property 3); retained as a diagnostic.
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


@dataclass(frozen=True)
class BatchDiagnostics:
    """Per-realization M8 batch outputs with the diagnostics retained (ADR-0034).

    The array twin of :class:`EvaluationResult` for one
    :func:`evaluate_batch_diagnostics` call: every field is the ``(N,)``
    vector of the corresponding scalar-path quantity, computed by the *same*
    kernels in the same order, so ``BatchDiagnostics`` row j equals the
    :func:`evaluate_realization` result for theta row j bit for bit (numpy
    backend; pinned by ``tests/test_evaluator.py``). Built for the Phase 2
    survival replay, which needs the continuous margins and the
    initiation/progression diagnostics for *all* rows, not only the two
    failure flags the production sweep keeps (spec §12 fm6).

    Attributes
    ----------
    Z_static : numpy.ndarray, shape (N,)
        Static margin ``H_c - (h_peak - z_toe)`` [m] (raw gross head,
        ADR-0028). Failure where ``<= 0``.
    Z_transient : numpy.ndarray, shape (N,)
        Transient margin ``L - l_e_final`` [m] (per-realization L when L is
        stochastic). Failure where ``<= 0``.
    l_e_final : numpy.ndarray, shape (N,)
        Final pipe length after the full hydrograph [m] (clipped at L).
    H_c : numpy.ndarray, shape (N,)
        Static critical head [m] (M6, at the static scale exponent).
    H_c_transient : numpy.ndarray, shape (N,)
        Transient H_eq anchor head [m]; equals ``H_c`` unless the ADR-0017
        transient-only scale exponent is active.
    l_c : numpy.ndarray, shape (N,)
        Critical pipe length [m] (scale-exponent independent).
    lambda_in : numpy.ndarray, shape (N,)
        Hinterland Mazure leakage length [m] (M4).
    r_e : numpy.ndarray, shape (N,)
        Response factor [-] in (0, 1); drives only the uplift/heave gate
        (ADR-0027/ADR-0028).
    t_uh : numpy.ndarray, shape (N,)
        Time [s] of first uplift+heave co-occurrence, NaN where never.
    failure_static, failure_trans : numpy.ndarray, shape (N,), bool
        The ``Z <= 0`` flags; identical to the :func:`evaluate_batch` return.
    uplift_occurred, heave_occurred : numpy.ndarray, shape (N,), bool
        Per-event M5 latches at termination.
    """

    Z_static: npt.NDArray[float64]
    Z_transient: npt.NDArray[float64]
    l_e_final: npt.NDArray[float64]
    H_c: npt.NDArray[float64]
    H_c_transient: npt.NDArray[float64]
    l_c: npt.NDArray[float64]
    lambda_in: npt.NDArray[float64]
    r_e: npt.NDArray[float64]
    t_uh: npt.NDArray[float64]
    failure_static: npt.NDArray[np.bool_]
    failure_trans: npt.NDArray[np.bool_]
    uplift_occurred: npt.NDArray[np.bool_]
    heave_occurred: npt.NDArray[np.bool_]


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
    foreland_open: bool = False,
    model_factor_mp: float | None = None,
    critical_length_factor: float | None = None,
    toe_gradient_relief_factor: float | None = None,
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
    progression ODE against the *same* theta row (shared-sample contract,
    ADR-0002). r_e feeds only the transient uplift/heave gate; the static
    branch is r_e-independent (raw Sellmeijer head, ADR-0028). The static
    branch reuses the same H_c that anchors the transient H_eq curve. Returns
    both Z values and the diagnostics Phase 2 needs (spec §8).

    Parameters
    ----------
    theta_row : numpy.ndarray, shape (7,)
        One realization's parameter vector in the canonical column order
        ``['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']``
        (spec §2, M2 contract), in strict SI / kN-m^3 units. Consumed by all
        of M4, M6 and M7; ``C_e`` enters only the transient branch (the static
        branch has no C_e exposure by design, ADR-0001).
    hydrograph : HydrographRecord
        One event's loading record (M3 ``hydrographs.HydrographRecord``, or
        any structural stand-in — consumption is duck-typed per ADR-0010, see
        module docstring point 1): ``h`` — the river-stage series [m above
        datum], shape (T,); ``peak`` — the scalar static comparator level
        h_peak [m above datum] (spec §1); and ``native_dt`` — the integration
        timestep dt_s [s], at which ``h`` is assumed uniformly sampled
        (ambiguities 2-3).
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
    foreland_open : bool, optional
        Keyword-only ADR-0025 sensitivity hook, default False (the adopted
        blanketed baseline — unchanged behaviour). True substitutes the USACE
        Case 7a x1 = 0 bound: the effective foreland entry length is zeroed,
        so r_e = lambda_in / (L + lambda_in) (Pol thesis Eq. 7.13's own
        no-riverside-blanket form). The measured ``geometry`` is never
        mutated. On-demand only (the KP 62.0 foreland-confinement
        sensitivity); production configs stay blanketed.
    model_factor_mp : float, optional
        Keyword-only ADR-0045 Sellmeijer model factor m_p for this
        realization. ``None`` (default) applies no factor — bit-identical to
        pre-ADR-0045 behaviour. When set, the **single-source** critical head
        is multiplied by m_p in both places it appears — the static
        comparator H_c and the transient H_eq anchor H_c_transient — so one
        physical draw of Sellmeijer model-form error moves the critical head
        consistently everywhere within the realization (the reported ``H_c``
        and ``H_c_transient`` diagnostics carry the factored values actually
        used). l_c is geometric (Pol Eq. (13)) and is not scaled. Companion
        sensitivity runs only; the caller draws m_p per realization via
        ``sampling.sample_model_factor``.
    critical_length_factor : float, optional
        Keyword-only multiplicative override on the M6 critical pipe length
        l_c (Pol SIE 2024 Eq. (13); ADR-0049). ``None`` (default) keeps the
        published formula and is **bit-identical** to prior behaviour. When
        set, l_c is scaled at source, so the reported ``l_c`` diagnostic and
        the value the M7 equilibrium curve is built on can never disagree.
        The knob is **transient-only by construction**: l_c enters nothing
        but H_eq(l), and the static comparator does not read it, so the
        static branch is exactly invariant under it. Works on both
        progression backends (the scaling happens upstream of the M7
        kernel, which receives l_c as an input array).
    toe_gradient_relief_factor : float, optional
        Keyword-only relief on the landside-toe exit gradient (ADR-0050), in
        ``(0, 1]``: the fraction of the undrained gradient that survives a
        landside toe drain. ``None`` (default) and ``1.0`` are the undrained
        baseline and **bit-identical** to prior behaviour. Applied by scaling
        the response factor handed to the M4 head model, so
        ``Delta_h_blanket`` and ``i_exit = Delta_h_blanket / D_bl`` scale by
        exactly this factor at every timestep. Since ADR-0028 r_e reaches the
        uplift/heave gate and nothing else, the knob is **gate-only by
        construction**: the static branch is exactly invariant under it, and
        neither piping head moves. The reported ``r_e`` diagnostic stays the
        *physical* response factor, unrelieved; the credit belongs to a
        structure, not to the blanket-aquifer system. Works on both
        progression backends. Companion sensitivity runs only.

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
    pipe-length update (M7). The static Sellmeijer comparator uses the RAW gross
    head across the structure ``h_peak - z_toe`` (Sellmeijer 2011; no r_e, no
    crack term; ADR-0028); the transient rate uses the RAW crack-reduced head
    ``H_erosion = (h - z_toe) - 0.3*D_bl`` (Pol SIE 2024 Eq. (6), no r_e --
    ADR-0027); the uplift/heave gate uses the r_e-attenuated ``Delta_h_blanket``
    (Eq. (10)). r_e drives only initiation, not either piping head, so the two
    piping heads differ by exactly 0.3*D_bl -- the clean head-convention gap
    component (spec §3, §4, §12 failure mode 4). Failure is ``Z <= 0`` for both.

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
    sellmeijer = compute_critical_head(
        theta_row,
        geometry,
        **sell_kwargs,
        critical_length_factor=critical_length_factor,
    )
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

    # ADR-0045: one per-realization Sellmeijer model factor scales the
    # single-source critical head in BOTH its uses (static comparator and
    # transient H_eq anchor) — never one branch alone. l_c stays geometric.
    if model_factor_mp is not None:
        h_c_m = h_c_m * float(model_factor_mp)
        h_c_transient_m = h_c_transient_m * float(model_factor_mp)

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
    if foreland_open:
        # ADR-0025 open-entry sensitivity: the USACE Case 7a x1 = 0 bound
        # (river head applied directly at the riverside toe). The measured
        # geometry['foreshore_width'] is never mutated — only the entry
        # length used by this evaluation is zeroed.
        lambda_out_eff_m = 0.0
    # r_e is stochastic (four sampled variables) and lives in the per-realization
    # path -- never precomputed once (spec Property 3). It drives ONLY the
    # transient uplift/heave gate (ADR-0027/ADR-0028); the static branch is
    # r_e-independent. The shared sample (theta row j) still feeds both branches.
    r_e = float(response_factor(lambda_in_m, lambda_out_eff_m, seepage_length_m))

    # --- Static branch (spec §3 steps 4-6): scalar gross-head comparison. The
    # static Sellmeijer comparator takes the RAW gross head across the structure
    # (Sellmeijer 2011's "critical hydraulic head across structure"; no r_e, no
    # 0.3*D_bl crack term; ADR-0028). r_e drives only the uplift/heave
    # initiation (Eq. 10), which Sellmeijer's static model does not include, so
    # the static branch is r_e-independent.
    h_peak_m = float(hydrograph.peak)
    static_head_m = h_peak_m - z_toe_m
    z_static = h_c_m - static_head_m
    failure_static = bool(z_static <= 0.0)

    # --- Transient branch (spec §3 steps 7-10): delegate the irreducibly serial
    # timestep loop to the M7 timestepper, built on the SAME r_e via the M4 head
    # model. Inside integrate_progression the un-reduced, r_e-attenuated
    # Delta_h_blanket(t) drives the M5 uplift/heave gate while the RAW-outer-level
    # H_erosion(t) = (h(t) - z_toe) - 0.3*D_bl drives the rate (ADR-0027) -- the
    # two heads kept separate exactly as the M7 tests verify. Phase 1 uses the
    # instantaneous (quasi-static) M4 form (module docstring ambiguity 5).
    h_river_m = np.asarray(hydrograph.h, dtype=np.float64)
    dt_s = float(hydrograph.native_dt)
    head_model = InstantaneousHead(
        _gate_response_factor(r_e, toe_gradient_relief_factor), z_toe_m
    )
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
    foreland_open: bool = False,
    progression_backend: str = "numpy",
    equilibrium_end_factor: float | None = None,
    model_factor_samples: npt.NDArray[float64] | None = None,
    critical_length_factor: float | None = None,
    toe_gradient_relief_factor: float | None = None,
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
    ``tests/test_run.py::test_orchestration_matches_reference_loop``. (The
    bit-identity statement holds for the default ``progression_backend=
    'numpy'``; the opt-in ``'numba'`` backend is equivalent to < 1e-10, not
    bit-identical — ADR-0029.) Only the
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
    foreland_open : bool, optional
        ADR-0025 open-entry sensitivity (default False = blanketed baseline,
        unchanged behaviour): zeroes the effective foreland entry length for
        every realization. Same semantics as :func:`evaluate_realization`.
    progression_backend : {'numpy', 'numba'}, optional
        M7 timestepper backend (ADR-0029). ``'numpy'`` (default) is the
        reference path, bit-identical to looping
        :func:`evaluate_realization`. ``'numba'`` dispatches the transient
        branch to the JIT-parallel kernel
        (:func:`~bep_reliability_engine.progression_numba.\
integrate_progression_numba`) — numerically equivalent to < 1e-10 but NOT
        bit-identical (the platform ``pow`` may differ in the last ulp), so
        it is opt-in via ``config.timestepper.progression_backend`` and the
        choice is recorded in run metadata. Requires the optional ``numba``
        dependency (``pip install -e .[accel]``). The static branch is
        backend-independent (no timestepper).
    equilibrium_end_factor : float, optional
        Keyword-only H_eq(L)/H_c end-anchor override forwarded to M7 for the
        spec §12 fm4 H_eq-conservatism isolation (ADR-0041). ``None``
        (default) keeps the published 0.9 anchor, bit-identical to prior
        behavior. Refused on the numba backend (the JIT kernel hard-codes
        the constant). Analysis-only; the static branch is unaffected.
    model_factor_samples : numpy.ndarray, shape (N,), optional
        Keyword-only per-realization Sellmeijer model factor m_p (ADR-0045),
        drawn via :func:`~bep_reliability_engine.sampling.sample_model_factor`
        and pairing with theta row j row-for-row. ``None`` (default) applies
        no factor — bit-identical to pre-ADR-0045 behaviour. When provided,
        the single-source H_c is multiplied by m_p,j in both its uses (static
        comparator and transient H_eq anchor) before the branches evaluate;
        the reported diagnostics carry the factored values. Works on both
        backends (the factor is applied upstream of the M7 kernel).
    critical_length_factor : float, optional
        Keyword-only multiplicative override on the M6 critical pipe length
        l_c (Pol SIE 2024 Eq. (13); ADR-0049). ``None`` (default) keeps the
        published formula and is **bit-identical** to prior behaviour. When
        set, l_c is scaled at source, so the reported ``l_c`` diagnostic and
        the value the M7 equilibrium curve is built on can never disagree.
        The knob is **transient-only by construction**: l_c enters nothing
        but H_eq(l), and the static comparator does not read it, so the
        static branch is exactly invariant under it. Works on both
        progression backends (the scaling happens upstream of the M7
        kernel, which receives l_c as an input array).
    toe_gradient_relief_factor : float, optional
        Keyword-only relief on the landside-toe exit gradient (ADR-0050), in
        ``(0, 1]``: the fraction of the undrained gradient that survives a
        landside toe drain. ``None`` (default) and ``1.0`` are the undrained
        baseline and **bit-identical** to prior behaviour. Applied by scaling
        the response factor handed to the M4 head model, so
        ``Delta_h_blanket`` and ``i_exit = Delta_h_blanket / D_bl`` scale by
        exactly this factor at every timestep. Since ADR-0028 r_e reaches the
        uplift/heave gate and nothing else, the knob is **gate-only by
        construction**: the static branch is exactly invariant under it, and
        neither piping head moves. The reported ``r_e`` diagnostic stays the
        *physical* response factor, unrelieved; the credit belongs to a
        structure, not to the blanket-aquifer system. Works on both
        progression backends. Companion sensitivity runs only.

    Returns
    -------
    failure_static, failure_trans : numpy.ndarray, shape (N,), dtype bool
        Per-realization static and transient failure indicators (``Z <= 0``).

    Raises
    ------
    ValueError
        If ``progression_backend`` is not ``'numpy'`` or ``'numba'``.
    RuntimeError
        If ``progression_backend='numba'`` and numba is not installed.
    """
    diagnostics = evaluate_batch_diagnostics(
        theta_matrix,
        hydrograph,
        geometry,
        l_ini=l_ini,
        seepage_length_samples=seepage_length_samples,
        alpha_exponent=alpha_exponent,
        alpha_exponent_transient=alpha_exponent_transient,
        theta_repose_rad=theta_repose_rad,
        relative_density=relative_density,
        gamma_p_sub_kn_m3=gamma_p_sub_kn_m3,
        foreland_open=foreland_open,
        progression_backend=progression_backend,
        equilibrium_end_factor=equilibrium_end_factor,
        model_factor_samples=model_factor_samples,
        critical_length_factor=critical_length_factor,
        toe_gradient_relief_factor=toe_gradient_relief_factor,
    )
    return diagnostics.failure_static, diagnostics.failure_trans


def evaluate_batch_diagnostics(
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
    foreland_open: bool = False,
    progression_backend: str = "numpy",
    equilibrium_end_factor: float | None = None,
    model_factor_samples: npt.NDArray[float64] | None = None,
    critical_length_factor: float | None = None,
    toe_gradient_relief_factor: float | None = None,
) -> BatchDiagnostics:
    """Evaluate all N realizations at one level, retaining diagnostics (ADR-0034).

    The single batch implementation of M8: :func:`evaluate_batch` delegates
    here and returns only the two failure columns (its frozen contract), so
    there is exactly one batch code path and the two entry points can never
    drift apart. Same parameters and semantics as :func:`evaluate_batch`;
    see its docstring for the full contract. The only difference is the
    return type: the continuous margins and the M5/M7 diagnostics behind the
    flags are retained per realization.

    Added (additively, ADR-0034) for the Phase 2 survival replay against the
    observed 2016 hydrograph: the Accept-Reject filter needs the failure
    flags for all N rows at production speed, and the analysis needs the
    margins, terminal pipe lengths and initiation latches row by row. The
    production Phase 1 sweep continues to call :func:`evaluate_batch`.

    Returns
    -------
    BatchDiagnostics
        Per-realization margins, diagnostics and both failure flags; row j
        is bit-identical to ``evaluate_realization(theta_matrix[j], ...)``
        on the numpy backend (< 1e-10 on the opt-in numba backend,
        ADR-0029).

    Raises
    ------
    ValueError
        If ``progression_backend`` is not ``'numpy'`` or ``'numba'``.
    RuntimeError
        If ``progression_backend='numba'`` and numba is not installed.
    """
    if progression_backend not in ("numpy", "numba"):
        raise ValueError(
            f"progression_backend {progression_backend!r} must be 'numpy' or "
            "'numba' (ADR-0029)."
        )
    if equilibrium_end_factor is not None and progression_backend == "numba":
        raise ValueError(
            "equilibrium_end_factor override is numpy-backend only (ADR-0041): "
            "the numba kernel hard-codes the published 0.9 anchor."
        )
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
    sellmeijer = compute_critical_head_vectorized(
        theta,
        geometry_for_hc,
        **sell_kwargs,
        critical_length_factor=critical_length_factor,
    )
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

    # ADR-0045: one per-realization Sellmeijer model factor m_p,j scales the
    # single-source critical head in BOTH its uses (static comparator and
    # transient H_eq anchor) — never one branch alone. Applied upstream of the
    # branches (and of the M7 kernel, so both backends see it identically);
    # l_c stays geometric and unscaled.
    if model_factor_samples is not None:
        model_factor = np.asarray(model_factor_samples, dtype=np.float64)
        if model_factor.shape != (theta.shape[0],):
            raise ValueError(
                f"model_factor_samples has shape {model_factor.shape} for "
                f"{theta.shape[0]} theta rows; the ADR-0045 m_p draw must "
                "pair with theta row-for-row."
            )
        h_c = h_c * model_factor
        h_c_transient = h_c_transient * model_factor

    lambda_in = leakage_length_in(k_aq_mps, d_aq_m, d_bl_m, k_bl_mps)
    lambda_out_eff = leakage_length_out(
        k_aq_mps,
        d_aq_m,
        geometry["D_fore"],
        geometry["k_fore"],
        geometry["foreshore_width"],
    )
    if foreland_open:
        # ADR-0025 open-entry sensitivity: x1 = 0 for every realization,
        # identical to the scalar path; the measured geometry is untouched.
        lambda_out_eff = np.zeros_like(lambda_out_eff)
    # r_e is stochastic (four sampled variables, plus L when L is sampled) and
    # drives ONLY the transient uplift/heave gate (ADR-0027/ADR-0028); the
    # static branch is r_e-independent. The shared theta feeds both branches.
    r_e = response_factor(lambda_in, lambda_out_eff, seepage_length)

    # --- Static branch: RAW gross head across the structure (Sellmeijer 2011,
    # no r_e, no 0.3*D_bl; ADR-0028). r_e-independent.
    h_peak_m = float(hydrograph.peak)
    static_head = h_peak_m - z_toe_m
    z_static = h_c - static_head
    failure_static = z_static <= 0.0

    # --- Transient branch: the same r_e drives the M7 timestepper, vectorized
    # across realizations within each (serial) timestep (spec §6).
    h_river_m = np.asarray(hydrograph.h, dtype=np.float64)
    dt_s = float(hydrograph.native_dt)
    if progression_backend == "numba":
        # ADR-0029 opt-in JIT backend: same physics, realization-parallel,
        # instantaneous head model inlined (< 1e-10 equivalence, not
        # bit-identity — see the parameter docs). Imported lazily so the
        # numba dependency stays optional.
        try:
            from bep_reliability_engine.progression_numba import (
                integrate_progression_numba,
            )
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError(
                "progression_backend='numba' requires the optional numba "
                "dependency; install it with `pip install -e .[accel]` or "
                "use the default 'numpy' backend."
            ) from exc
        progression = integrate_progression_numba(
            h_river_m,
            dt_s,
            _gate_response_factor(r_e, toe_gradient_relief_factor),
            z_toe_m,
            c_e=c_e,
            k_aq_mps=k_aq_mps,
            d_bl_m=d_bl_m,
            gamma_bl_sub_knpm3=gamma_bl_sub_knpm3,
            h_c_m=h_c_transient,
            l_c_m=l_c,
            seepage_length_m=seepage_length,
            l_ini_m=l_ini,
        )
    else:
        head_model = InstantaneousHead(
            _gate_response_factor(r_e, toe_gradient_relief_factor), z_toe_m
        )
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
            equilibrium_end_factor=equilibrium_end_factor,
        )
    l_e_final = np.asarray(progression.l_final_m, dtype=np.float64)
    z_transient = seepage_length - l_e_final
    failure_trans = z_transient <= 0.0

    return BatchDiagnostics(
        Z_static=np.asarray(z_static, dtype=np.float64),
        Z_transient=np.asarray(z_transient, dtype=np.float64),
        l_e_final=l_e_final,
        H_c=h_c,
        H_c_transient=h_c_transient,
        l_c=l_c,
        lambda_in=np.asarray(lambda_in, dtype=np.float64),
        r_e=np.asarray(r_e, dtype=np.float64),
        t_uh=np.asarray(progression.t_uh_s, dtype=np.float64),
        failure_static=np.asarray(failure_static, dtype=bool),
        failure_trans=np.asarray(failure_trans, dtype=bool),
        uplift_occurred=np.asarray(progression.uplift_occurred, dtype=bool),
        heave_occurred=np.asarray(progression.heave_occurred, dtype=bool),
    )
