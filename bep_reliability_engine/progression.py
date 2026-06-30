"""M7 ``pol_ode_progression``: forward-Euler integration of the Pol pipe ODE.

Single responsibility (spec §1, M7): given one realization's (or N stacked
realizations') sampled parameters, the M4 aquifer-head model, and the H_c and
l_c from M6, integrate the Pol progression rate

    dl/dt = 89 * C_e * (k_aq * max(0, H_erosion - H_eq(l)) / L)**0.81

(Pol SIE 2024 Eq. (5) = CG24 Eq. (15) = thesis Eqs. (5.18)/(6.5); regression
on DgFlow hole-exit simulations, R^2 = 0.94) forward in time with explicit
Euler, gated by the M5 erosion indicator I_er. ``scipy.integrate.solve_ivp``
is banned for this loop: adaptive integrators fight the I_er discontinuities
(spec §10), and forward Euler is what Pol uses.

The two heads (spec §3 steps a-j; ADR-0007, ADR-0008)
-----------------------------------------------------
The timestepper computes both driving heads at every step and never mixes
them (spec §5 lists mixing as a known error):

* ``Delta_h_blanket(t) = h_aq(t) - z_toe`` -- the un-reduced, r_e-translated
  blanket overpressure (phi_it - h_e of Pol SIE 2024 Eqs. (8)-(10)). Feeds
  the M5 uplift and heave kernels only.
* ``H_erosion(t) = Delta_h_blanket(t) - 0.3 * D_bl`` -- the crack-resistance-
  reduced erosion driver of Pol SIE 2024 Eq. (6) (ADR-0007: r_e-translated,
  deliberate deviation from the paper's untranslated outer level; the two
  coincide for the r_e = 1 calibration configurations). Feeds the rate
  kernel only, never the uplift/heave gate.

Datum: all heads pivot on z_toe, the polder surface elevation at the
landside exit point, identical to Pol's h_e (ADR-0007; physics note
``docs/decisions/m7-pol-ode-reference-values.md`` §3).

State ownership (spec §5; initiation.py module docstring)
----------------------------------------------------------
All running state lives here, advanced serially in time and vectorized
across realizations (spec Property 4, §6):

* ``l_current`` -- monotonically non-decreasing pipe length: the positive-
  part operator ``max(0, H_erosion - H_eq)`` plus the I_er gate guarantee
  dl/dt >= 0; there is no negative-progression term and no reset between
  peaks. Staircase-shaped trajectories through inter-peak troughs are
  correct -- do not "fix" them. l is clipped at L: breach is absorbing.
* ``uplift_ever`` -- the per-event uplift latch (single-boolean
  implementation of Pol's running minimum min_{0..t} Z_u < 0). Latched from
  the M5 ``z_uplift`` sign each step; never carries across events.
* t_uh bookkeeping -- first co-occurrence of Z_uplift < 0 and Z_heave < 0
  (diagnostic only; NOT Pol's three-way sand-boil proxy, which adds an
  H > H_eq clause -- see the physics note §3). The flood-fighting clause of
  Pol's I_er is deliberately omitted (spec M5, ADR-0008 context).

Recovery r_l = 0 in Phase 1: the inter-event hook
(``l_ini_next = (1 - r_l) * l_e_prev``) lives outside this module, between
M8 event evaluations (spec §5).

Laboratory configuration (D_bl = 0)
-----------------------------------
``d_bl_m = 0`` represents the no-blanket box experiments (B25-245 replay):
the crack term vanishes (H_erosion = Delta_h_blanket) and the gate
degenerates -- uplift and heave thresholds are zero, so I_er is active for
any positive overpressure and inactive otherwise. The implementation must
evaluate this limit without NaN propagation or floating-point warnings
(guard the heave exit gradient Delta_h / D_bl at D_bl = 0: heave is active
for Delta_h > 0 and inactive for Delta_h <= 0).

Units and validity
------------------
Strict SI base units (m, s, m/s); unit conversion happens only in M1/M3,
never here. The rate formula is dimensional: the coefficient 89 carries
implicit units (m/s)^0.19, so inputs MUST be SI (physics note §1). Fitted
validity domain: hole-type exits, homogeneous aquifers with D/L = 1/3,
0.2 <= d_50 <= 0.4 mm, 2 <= C_u <= 3, overloading H/H_c <= 1.4, scales
L = 0.9-90 m; regression-vs-simulation scatter up to a factor ~3.

References
----------
Pol, Kanning, Jonkman & Kok (2024), Structure and Infrastructure
Engineering, Eqs. (5), (6), (11). Pol, Noordam & Kanning (2024), Computers
and Geotechnics 167, Eq. (15). Pol (2022), doctoral thesis, Eqs. (5.18),
(6.5), (6.10). Spec §3 (steps 8a-j), §5, §6, §11. ADR-0002 (shared sample),
ADR-0007 (head datum), ADR-0008 (gate collapse).
``docs/decisions/m7-pol-ode-reference-values.md`` (equation provenance and
test targets).
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from bep_reliability_engine.hydraulics import AquiferHeadModel
from bep_reliability_engine.initiation import erosion_indicator, z_heave, z_uplift

__all__ = [
    "CRACK_RESISTANCE_FACTOR",
    "EQUILIBRIUM_END_FACTOR",
    "POL_RATE_COEFFICIENT",
    "POL_RATE_EXPONENT",
    "ProgressionResult",
    "equilibrium_head",
    "integrate_progression",
    "progression_rate",
]

# Regression coefficients of the Pol progression rate (SIE 2024 Eq. (5);
# CG24 Eq. (15); thesis Eqs. (5.18)/(6.5)). The coefficient is dimensional:
# it carries implicit units (m/s)^(1 - POL_RATE_EXPONENT).
POL_RATE_COEFFICIENT: float = 89.0
POL_RATE_EXPONENT: float = 0.81

# Crack-resistance head loss over the blanket, H = dh_blanket - 0.3 * D_bl
# (Pol SIE 2024 Eq. (6); TAW 1999; Schweckendiek et al. 2014). M7-only:
# initiation.py is signature-guarded against ever seeing this term.
CRACK_RESISTANCE_FACTOR: float = 0.3

# End anchor of the equilibrium curve, H_eq(L) = 0.9 * H_c (Pol SIE 2024
# Eq. (11); conservative fit to the DgFlow hole-exit equilibrium curves).
EQUILIBRIUM_END_FACTOR: float = 0.9


class ProgressionResult(NamedTuple):
    """Outputs of one :func:`integrate_progression` event integration.

    Per-realization fields have the broadcast realization shape ``R`` of the
    parameter inputs (``R = ()``, i.e. scalars wrapped in 0-d arrays, when
    every per-realization input is scalar). M8 consumes these directly for
    the EvaluationResult contract (spec §2).
    """

    l_final_m: NDArray[np.float64]
    """Pipe length after the last timestep [m], shape ``R``; <= L always."""

    l_trajectory_m: NDArray[np.float64] | None
    """Full trajectory [m], shape ``(T,) + R``; ``l_trajectory_m[k]`` is the
    pipe length after processing sample k. None unless
    ``store_trajectory=True`` (default off: ~800 MB per cross-section at
    N = 1e5, spec §12 failure mode 6)."""

    uplift_occurred: NDArray[np.bool_]
    """Per-event uplift latch at termination (Z_uplift < 0 at any step;
    [SIE24] Eq. (8), M5), shape ``R``."""

    heave_occurred: NDArray[np.bool_]
    """True where Z_heave < 0 ([SIE24] Eq. (9), M5) occurred at any step, shape
    ``R``. Under the ADR-0008 collapse this latches at the same step as
    uplift_occurred."""

    t_uh_s: NDArray[np.float64]
    """Time of first uplift+heave co-occurrence [s], shape ``R``; sample k
    maps to t = k * dt_s (first sample at t = 0). NaN where never. This is the
    repo diagnostic, NOT [SIE24] Eq. (7)'s three-way sand-boil proxy, which
    adds an H > H_eq clause (module docstring)."""


def equilibrium_head(
    pipe_length_m: ArrayLike,
    h_c_m: ArrayLike,
    l_c_m: ArrayLike,
    seepage_length_m: ArrayLike,
) -> NDArray[np.float64]:
    """Piecewise-linear equilibrium head H_eq(l) of Pol SIE 2024 Eq. (11).

    Linear interpolation through the three anchors::

        H_eq(0)   = 0
        H_eq(l_c) = H_c
        H_eq(L)   = EQUILIBRIUM_END_FACTOR * H_c   (= 0.9 * H_c)

    Parameters
    ----------
    pipe_length_m : array_like of float
        Pipe length l [m] at which to evaluate the curve. Values are
        clamped to [0, L] before interpolation (l >= L returns 0.9 * H_c:
        breach is absorbing).
    h_c_m : array_like of float
        Critical head H_c [m] from M6 ``compute_critical_head`` (Sellmeijer
        2011; never recomputed here -- single-source contract, spec §1).
        Per-realization.
    l_c_m : array_like of float
        Critical pipe length l_c [m] from M6
        ``compute_critical_pipe_length`` (SIE 2024 Eq. (13)), or a measured
        value for experiment replays. Per-realization; must satisfy
        0 < l_c < L.
    seepage_length_m : array_like of float
        Seepage length L [m]. Geometry input.

    Returns
    -------
    numpy.ndarray of float
        H_eq [m], broadcast over the inputs. A head *difference* on the
        same datum as H_erosion: in excess of the polder surface at the
        exit point, z_toe = h_e (physics note §3).

    Notes
    -----
    Mathematical assumptions: 3D hole-type-exit equilibrium behavior --
    H_eq rises to the maximum H_c at l_c and "decreases only slightly"
    beyond it (CG24 §4.2); the two straight segments and the 0.9 * H_c end
    anchor are Pol's conservative fit to the DgFlow equilibrium curves
    (SIE 2024 §2.3). Plane-type (initiation-dominated) exits are *not*
    represented. Breakpoints (l_c, H_c) differ per realization, so the
    implementation must use ``numpy.where`` over the two segments rather
    than ``scipy.interpolate`` (spec §6, "where broadcasting breaks down").
    """
    pipe_length = np.asarray(pipe_length_m, dtype=np.float64)
    h_c = np.asarray(h_c_m, dtype=np.float64)
    l_c = np.asarray(l_c_m, dtype=np.float64)
    length = np.asarray(seepage_length_m, dtype=np.float64)

    # Clamp to [0, L]: l >= L is absorbing (returns the 0.9*H_c end anchor);
    # l < 0 cannot occur physically but is clamped for safety.
    l_clamped = np.clip(pipe_length, 0.0, length)

    # Two straight segments: 0 -> H_c over [0, l_c], then H_c -> 0.9*H_c over
    # [l_c, L]. np.where (not scipy.interpolate) so per-realization breakpoints
    # broadcast (spec §6).
    rising = h_c * (l_clamped / l_c)
    falling_slope = (EQUILIBRIUM_END_FACTOR - 1.0) * h_c / (length - l_c)
    falling = h_c + falling_slope * (l_clamped - l_c)
    return np.where(l_clamped < l_c, rising, falling)


def progression_rate(
    h_erosion_m: ArrayLike,
    h_eq_m: ArrayLike,
    c_e: ArrayLike,
    k_aq_mps: ArrayLike,
    seepage_length_m: ArrayLike,
) -> NDArray[np.float64]:
    """Instantaneous Pol progression rate dl/dt [m/s], positive part only.

    Implements Pol SIE 2024 Eq. (5) = CG24 Eq. (15) with the erosion
    threshold as a positive-part operator::

        dl/dt = 89 * C_e * (k_aq * max(0, H_erosion - H_eq) / L)**0.81

    The I_er gate is *not* applied here; the timestepper zeroes the rate
    where I_er is False (spec §3 step 8j).

    Parameters
    ----------
    h_erosion_m : array_like of float
        Crack-resistance-reduced erosion-driving head [m]:
        H_erosion = Delta_h_blanket - 0.3 * D_bl (SIE 2024 Eq. (6),
        ADR-0007). Never the un-reduced blanket overpressure, which belongs
        to the uplift/heave gate (spec §5).
    h_eq_m : array_like of float
        Equilibrium head H_eq(l) [m] from :func:`equilibrium_head`, on the
        same datum as ``h_erosion_m``.
    c_e : array_like of float
        Erosion coefficient C_e [-]. Sampled (theta, ADR-0001); rate is
        exactly linear in C_e. Calibrated experiment values: 0.007-0.030
        small-scale, 0.014 FPH (physics note §4).
    k_aq_mps : array_like of float
        Aquifer hydraulic conductivity [m/s]. Sampled (theta); the same
        draw feeds M4 and M6 per the shared-sample contract (ADR-0002).
    seepage_length_m : array_like of float
        Seepage length L [m]. Geometry input.

    Returns
    -------
    numpy.ndarray of float
        dl/dt [m/s] >= 0, broadcast over the inputs. Exactly 0 where
        H_erosion <= H_eq (grains in the pipe are in equilibrium below the
        threshold, SIE 2024 §2.1).

    Notes
    -----
    Dimensional regression formula, SI-only: the coefficient 89 carries
    implicit units (m/s)^0.19, so k in m/s and heads/lengths in m are
    mandatory and no unit conversion may occur inside this kernel (physics
    note §1; docs/conventions.md). Fitted on DgFlow hole-exit simulations
    (S22/S42 sands, L = 3 and 30 m, 31 simulations / 3100 points, 80/20
    split, R^2 = 0.94) with individual-case scatter up to a factor ~3 --
    reference tests assert order-of-magnitude bands, never tight agreement
    with single DgFlow values (physics note §1, §5).
    """
    h_erosion = np.asarray(h_erosion_m, dtype=np.float64)
    h_eq = np.asarray(h_eq_m, dtype=np.float64)
    c_e_arr = np.asarray(c_e, dtype=np.float64)
    k_aq = np.asarray(k_aq_mps, dtype=np.float64)
    length = np.asarray(seepage_length_m, dtype=np.float64)

    # Positive-part operator: erosion only above the equilibrium threshold
    # (SIE 2024 §2.1). Clamping the base to >= 0 also keeps the fractional
    # power real -- a negative base under **0.81 would be NaN.
    overload = np.maximum(0.0, h_erosion - h_eq)
    velocity_group = k_aq * overload / length
    return POL_RATE_COEFFICIENT * c_e_arr * velocity_group**POL_RATE_EXPONENT


def integrate_progression(
    h_river_m: ArrayLike,
    dt_s: float,
    head_model: AquiferHeadModel,
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
    store_trajectory: bool = False,
) -> ProgressionResult:
    """Forward-Euler timestepper for the pipe length over one event.

    Owns all running state (pipe length, uplift latch, t_uh bookkeeping)
    and computes both driving heads at every step, per spec §3 steps 8a-j::

        reset head_model with h_river_m[0]
        for k in 0 .. T-1:                       # serial in t (Property 4)
            h_aq        = head_model.step(h_river_m[k], dt_s)     # (a)
            dh_blanket  = h_aq - z_toe_m                          # (b)
            H_erosion   = dh_blanket - 0.3 * d_bl_m               # (c)
            Z_u         = z_uplift(dh_blanket, gamma, d_bl)       # (d) M5
            uplift_ever |= (Z_u < 0)                              # (e)
            Z_h         = z_heave(dh_blanket, gamma, d_bl)        # (f, g) M5
            heave_now   = (Z_h < 0)                               # (h)
            I_er        = erosion_indicator(uplift_ever,          # (i) M5
                                            l_current > 0, heave_now)
            H_eq        = equilibrium_head(l_current, H_c, l_c, L)
            rate        = progression_rate(H_erosion, H_eq, ...)  # (j)
            l_current   = min(L, l_current + dt_s * rate * I_er)

    Pol equation map for the loop: (c) H_erosion is [SIE24] Eq. (6); (d) Z_u is
    Eq. (8) and (f,g) Z_h is Eq. (9), both M5 in the resistance-minus-load
    reading (ADR-0008); (i) I_er is Eq. (7) (flood-fighting clause omitted,
    Terzaghi collapse, ADR-0008); H_eq is Eq. (11); (j) the rate is Eq. (5) =
    [CG24] Eq. (15) = [T22] Eqs. (5.18)/(6.5).

    All per-realization inputs broadcast to a common realization shape R;
    the loop is vectorized across R within each timestep (spec §6) and is
    irreducibly serial along t.

    Parameters
    ----------
    h_river_m : array_like of float, shape (T,)
        River stage series [m above datum], one continuous record spanning
        the entire (possibly multi-peak) compound event at uniform spacing
        ``dt_s``. Sample k is at time t = k * dt_s.
    dt_s : float
        Timestep [s]. Native d4PDF resolution by default, validated by the
        spec §11 dt/2 convergence test on a flashy rising limb with the
        high-k_aq / high-C_e / low-D_bl worst case.
    head_model : AquiferHeadModel
        M4 head model (``InstantaneousHead`` or gated ``LaggedHead``),
        constructed by M8 from this realization's r_e (and tau_aq when the
        lag is active) and the *same* ``z_toe_m`` passed below. Consumed
        identically in both forms (ADR-0004); it is reset here at event
        start, because aquifer-head state never carries across events
        (spec §5).
    z_toe_m : float
        Polder surface elevation at the landside exit point [m above
        datum]; equals h_e in Pol SIE 2024 Eqs. (6) and (8) (ADR-0007).
        Must equal the z_toe the head model was built with.
    c_e : array_like of float
        Erosion coefficient C_e [-], theta column. Transient-branch-only
        parameter (ADR-0001).
    k_aq_mps : array_like of float
        Aquifer hydraulic conductivity [m/s], theta column.
    d_bl_m : array_like of float
        Blanket thickness D_bl [m], theta column. Enters the crack term
        (0.3 * D_bl, rate path) AND the M5 gate kernels (un-reduced path).
        ``0.0`` selects the no-blanket laboratory configuration (module
        docstring): zero crack term, gate open for any positive
        overpressure, no NaN or warnings.
    gamma_bl_sub_knpm3 : array_like of float
        Submerged blanket unit weight gamma'_bl [kN/m3], theta column.
        Gate kernels only; inert when ``d_bl_m = 0``.
    h_c_m : array_like of float
        Critical head H_c [m] from M6 (single source, spec §1).
    l_c_m : array_like of float
        Critical pipe length l_c [m] from M6, or measured (replays).
    seepage_length_m : array_like of float
        Seepage length L [m]. Z_transient = L - l_e in M8; breach when l
        reaches L. A scalar for deterministic L, or an ``(N,)`` array when L is
        a per-realization stochastic draw (sampled independently of theta): the
        breach clip ``min(l, L)`` and every L-dependent term then broadcast
        per realization.
    l_ini_m : array_like of float, optional
        Initial pipe length [m], default 0. Non-zero values bypass the
        uplift gate via the ``l_current > 0`` clause (an existing pipe
        means the blanket is already breached, spec §5) -- the hook for
        event sequences and sensitivity studies.
    store_trajectory : bool, optional
        Store the full l(t); default False to save memory (spec §12
        failure mode 6). Enable for the 2016 calibration run,
        visualization subsets, and reference tests.

    Returns
    -------
    ProgressionResult
        Final pipe length, optional trajectory, the latched uplift/heave
        diagnostics, and t_uh (all per realization; see the class
        docstring).

    Notes
    -----
    Mathematical assumptions: explicit (forward) Euler exactly as in Pol's
    implementation -- no adaptive integration (spec §10); instantaneous or
    exponentially lagged hydraulic translation per the injected M4 model;
    uplift latch per event only; recovery r_l = 0 within Phase 1 (the
    cross-event hook lives in M8, spec §5). Monotonicity is structural:
    dl/dt >= 0 always, so l never decreases; troughs yield exactly flat
    staircase segments (I_er False or overload 0). l is clipped at L and
    breach is absorbing. Invariants asserted by the spec §11 validation
    suite: l non-decreasing at every step, l_e <= L at termination, I_er
    never True -> False except via heave inactivation.
    """
    h_river = np.asarray(h_river_m, dtype=np.float64)
    n_steps = h_river.shape[0]

    # Per-realization theta inputs (scalars or (N,) arrays; numpy broadcasts
    # across realizations within each timestep -- the time axis stays serial).
    c_e_arr = np.asarray(c_e, dtype=np.float64)
    k_aq = np.asarray(k_aq_mps, dtype=np.float64)
    d_bl = np.asarray(d_bl_m, dtype=np.float64)
    gamma_bl_sub = np.asarray(gamma_bl_sub_knpm3, dtype=np.float64)
    h_c = np.asarray(h_c_m, dtype=np.float64)
    l_c = np.asarray(l_c_m, dtype=np.float64)

    # Aquifer-head state is reinitialized per event in equilibrium with the
    # initial river stage (it never carries across events; spec §5).
    head_model.reset(float(h_river[0]))

    # Running state owned by the timestepper, not by initiation.py: the pipe
    # length, the per-event uplift latch, and the t_uh / heave-ever
    # diagnostics. Each starts minimal and takes the broadcast realization
    # shape on the first update.
    l_current = np.asarray(l_ini_m, dtype=np.float64)
    uplift_ever = np.asarray(False)
    heave_ever = np.asarray(False)
    t_uh = np.asarray(np.nan)

    trajectory: list[NDArray[np.float64]] | None = [] if store_trajectory else None

    for k in range(n_steps):
        # (a) aquifer head at the exit point, then (b) the un-reduced blanket
        # overpressure that drives uplift and heave.
        h_aq = head_model.step(float(h_river[k]), dt_s)
        delta_h_blanket = h_aq - z_toe_m

        # (c) erosion driver: the crack-resistance-reduced head, kept as its
        # own variable and never fed to the initiation kernels (spec §5).
        h_erosion = delta_h_blanket - CRACK_RESISTANCE_FACTOR * d_bl

        # (d, e) uplift limit state (un-reduced head) and its running latch.
        uplift_now = z_uplift(delta_h_blanket, gamma_bl_sub, d_bl) < 0.0
        uplift_ever = uplift_ever | uplift_now

        # (f, g, h) heave limit state (un-reduced head), checked
        # instantaneously. errstate guards the exit-gradient division for the
        # no-blanket (D_bl = 0) lab box: there delta_h / 0 -> +/-inf or nan,
        # and Z_heave < 0 still resolves to the intended "heave active iff
        # overpressure > 0" with no warning and no NaN leaking into the gate.
        with np.errstate(divide="ignore", invalid="ignore"):
            heave_now = z_heave(delta_h_blanket, gamma_bl_sub, d_bl) < 0.0

        # t_uh diagnostic: first uplift+heave co-occurrence (NOT Pol's
        # three-way sand-boil proxy; module docstring).
        co_occurrence = uplift_now & heave_now
        first_co = co_occurrence & np.isnan(t_uh)
        t_uh = np.where(first_co, k * dt_s, t_uh)
        heave_ever = heave_ever | heave_now

        # (i) erosion-indicator gate (M5). The l_current > 0 clause is the
        # compound-event resumption gateway (spec §3); within one event the
        # uplift latch already carries the memory.
        i_er = erosion_indicator(uplift_ever, l_current > 0.0, heave_now)

        # (j) equilibrium head and progression rate. The positive-part operator
        # is enforced twice: inside progression_rate via max(0, H_erosion -
        # H_eq), and again by gating dl on I_er here.
        h_eq = equilibrium_head(l_current, h_c, l_c, seepage_length_m)
        rate = progression_rate(h_erosion, h_eq, c_e_arr, k_aq, seepage_length_m)
        dl = np.where(i_er, rate, 0.0) * dt_s

        # Forward Euler with the absorbing breach clip at L.
        l_next = np.minimum(l_current + dl, seepage_length_m)

        # Internal monotonicity invariant (spec §11 validation test 4): dl >= 0
        # and l_current <= L, so the clip can only raise l toward L -- the pipe
        # length is non-decreasing at every step.
        assert np.all(
            l_next >= l_current
        ), "M7 timestepper produced a decrease in pipe length"
        l_current = l_next

        if trajectory is not None:
            trajectory.append(np.array(l_current))

    # Conform the scalar-seeded diagnostics to the final realization shape R
    # (= l_current.shape) so every per-realization field shares one shape.
    realization_shape = l_current.shape
    l_trajectory = np.stack(trajectory) if trajectory is not None else None
    return ProgressionResult(
        l_final_m=l_current,
        l_trajectory_m=l_trajectory,
        uplift_occurred=np.broadcast_to(uplift_ever, realization_shape).copy(),
        heave_occurred=np.broadcast_to(heave_ever, realization_shape).copy(),
        t_uh_s=np.broadcast_to(t_uh, realization_shape).copy(),
    )
