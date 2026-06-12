"""M5 ``initiation_evaluator``: uplift and heave limit states and the I_er gate.

Single responsibility (spec §1, M5): STPH gating logic. Given the un-reduced
blanket overpressure Delta_h_blanket(t) from M4 and the sampled (gamma'_s,
D_bl), evaluate the uplift and heave limit states (spec §3 steps d and g) and
combine the caller-held gate booleans into the erosion indicator I_er(t)
(step 8i) that switches the M7 progression rate on and off.

Sign convention
---------------
Both limit states are resistance minus load: **critical when Z < 0**. The
printed term order in Pol SIE 2024 Eqs. (8)-(9) / thesis Eqs. (6.7)-(6.8)
reads load minus resistance, which is inconsistent with the "< 0" tests in
the papers' own I_er definition (Eq. (7) / Eq. (6.6)); the
resistance-minus-load reading implemented here is the only coherent one,
matches thesis Eq. (7.14) and the Schweckendiek/TAW convention, and was
confirmed against the paper copy on 2026-06-12 (ADR-0008, convention note).

Driving head
------------
Every head consumed here is the un-reduced, r_e-translated blanket
overpressure from M4::

    Delta_h_blanket(t) = h_aq(t) - z_toe

(instantaneous default r_e * (h_river(t) - z_toe), or the ADR-0004 lag
state). The crack-resistance-reduced erosion head
H_erosion = Delta_h_blanket - 0.3 * D_bl belongs exclusively to the M7
progression driver: no function in this module accepts or computes any
crack-reduced head (spec §5 lists mixing them as a known error; this is
enforced by a signature-guard test).

Statelessness
-------------
Every kernel is a pure function, vectorized over realizations (scalars or
``(N,)`` arrays, NumPy broadcasting). All time-running state is owned by the
M7 timestepper: the uplift latch ``uplift_ever`` (the single-scalar
implementation of Pol's running minimum min_{0..t} Z_u < 0, spec §5), the
pipe-length state behind ``pipe_length_positive``, and the t_uh bookkeeping.
The latch is per-event; cross-event memory travels only through pipe length
(l_ini), never through the latch.

I_er and the omitted flood-fighting clause
------------------------------------------
:func:`erosion_indicator` implements the first two clauses of Pol SIE 2024
Eq. (7) / thesis Eq. (6.6). Pol's third clause, t < t_uh + t_ff/I_ff, which
suspends progression once organized flood fighting succeeds, is deliberately
omitted (spec §1, M5): the transient limit state is an unconditional upper
bound on failure, with no operational-intervention credit, whose
conservatism grows under the elongated +4K hydrographs.

ADR-0008 collapse
-----------------
With the Terzaghi critical gradient gamma'_s/gamma_w in place of Pol's
independent i_c,h, the two limit states are one threshold at two scales::

    Z_heave = Z_uplift / D_bl

so they change sign at the same instant and I_er reduces to ``heave_now``
under the baseline parameterization. Diagnostics showing ``uplift_occurred``
and ``heave_occurred`` latching at the same timestep are correct, not a bug.
The full three-input gate is nonetheless retained: it becomes load-bearing
the moment i_c,h is decoupled from gamma'_s/gamma_w (e.g. a sensitivity run
with Pol's Lognormal(0.7, 0.1)). See ADR-0008 for the algebra and the
conservatism consequence.

t_uh diagnostic
---------------
The t_uh reported by M8 is defined in this engine as the first timestep at
which uplift and heave co-occur (Z_uplift < 0 and Z_heave < 0
simultaneously). This is *not* Pol's three-way sand-boil proxy (uplift and
heave and H > H_eq, SIE 2024 below Eq. (7)): the erosion clause is dropped.
With the flood-fighting clause omitted, t_uh is purely diagnostic; its
bookkeeping requires running-time state and therefore lives in the M7
timestepper, not here.

Units and datum
---------------
Heads and lengths in strict SI (m). Unit weights are passed in the units of
``constants.GAMMA_W`` (kN/m3, per the spec §7 theta contract): only the
dimensionless ratio gamma'_s/gamma_w enters the kernels, so the ratio is
unit-safe as long as the two share units. Delta_h_blanket is an overpressure
relative to z_toe, the polder surface elevation at the landside exit point,
identical to Pol's h_e datum of Eqs. (6) and (8) (ADR-0007).

References
----------
Pol, Kanning, Jonkman & Kok (2024), Structure and Infrastructure
Engineering, Eqs. (7)-(10) and Table 2. Pol (2022), doctoral thesis,
Eqs. (6.6)-(6.9) and Eq. (7.14). Schweckendiek et al. (2014); TAW (1999).
ADR-0007 (head datum), ADR-0008 (Terzaghi heave gradient and I_er collapse).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from bep_reliability_engine.constants import GAMMA_W

__all__ = [
    "erosion_indicator",
    "z_heave",
    "z_uplift",
]


def z_uplift(
    delta_h_blanket_m: ArrayLike,
    gamma_s_sub_knpm3: ArrayLike,
    d_bl_m: ArrayLike,
) -> NDArray[np.float64]:
    """Uplift limit state Z_u at the blanket base (spec §3 step d).

    Implements::

        Z_uplift = (gamma_s_sub * D_bl) / gamma_w - delta_h_blanket

    with gamma_w = ``constants.GAMMA_W``. Resistance minus load: negative
    where the blanket overpressure exceeds the submerged blanket weight.

    Parameters
    ----------
    delta_h_blanket_m : array_like of float
        Un-reduced blanket overpressure Delta_h_blanket = h_aq - z_toe [m]
        from the M4 head model (spec §3 step b). Never the crack-reduced
        erosion head, which is M7-only (module docstring, Driving head).
    gamma_s_sub_knpm3 : array_like of float
        Submerged (effective) blanket unit weight
        gamma'_s = gamma_bl,sat - gamma_w [kN/m3]. Sampled (theta). Must
        share units with ``constants.GAMMA_W``; only the ratio
        gamma'_s/gamma_w enters.
    d_bl_m : array_like of float
        Hinterland blanket thickness D_bl [m]. Sampled (theta).

    Returns
    -------
    numpy.ndarray of float
        Z_uplift [m], broadcast over the inputs. Uplift is critical where
        Z_uplift < 0.

    Notes
    -----
    Mathematical assumptions: quasi-static vertical force balance of a
    rigid blanket column over a unit area; no shear, cohesion, or model
    factor (Pol's m_u is deliberately not carried; model-uncertainty
    calibration concentrates in the stochastic C_e, ADR-0008). This is Pol
    SIE 2024 Eq. (8) / thesis Eq. (6.7) with gamma'_s = gamma_bl,sat -
    gamma_w, in the resistance-minus-load reading (the printed term order
    is flipped; module docstring, Sign convention). The running-minimum
    latch min_{0..t} Z_u < 0 is the caller's responsibility: M7 latches
    ``uplift_ever`` from this kernel's sign once per timestep, per event.
    """
    delta_h = np.asarray(delta_h_blanket_m, dtype=np.float64)
    gamma_s_sub = np.asarray(gamma_s_sub_knpm3, dtype=np.float64)
    d_bl = np.asarray(d_bl_m, dtype=np.float64)
    return (gamma_s_sub * d_bl) / GAMMA_W - delta_h


def z_heave(
    delta_h_blanket_m: ArrayLike,
    gamma_s_sub_knpm3: ArrayLike,
    d_bl_m: ArrayLike,
) -> NDArray[np.float64]:
    """Heave limit state Z_h at the exit point (spec §3 steps f and g).

    Implements::

        i_exit  = delta_h_blanket / D_bl
        Z_heave = gamma_s_sub / gamma_w - i_exit

    with gamma_w = ``constants.GAMMA_W``. Resistance minus load: negative
    where the exit gradient exceeds the Terzaghi critical gradient.

    Parameters
    ----------
    delta_h_blanket_m : array_like of float
        Un-reduced blanket overpressure Delta_h_blanket = h_aq - z_toe [m]
        from the M4 head model (spec §3 step b). Never the crack-reduced
        erosion head, which is M7-only (module docstring, Driving head).
    gamma_s_sub_knpm3 : array_like of float
        Submerged (effective) blanket unit weight
        gamma'_s = gamma_bl,sat - gamma_w [kN/m3]. Sampled (theta). Must
        share units with ``constants.GAMMA_W``; only the ratio
        gamma'_s/gamma_w enters.
    d_bl_m : array_like of float
        Hinterland blanket thickness D_bl [m]. Sampled (theta).

    Returns
    -------
    numpy.ndarray of float
        Z_heave [-] (a gradient margin), broadcast over the inputs. Heave
        is active where Z_heave < 0.

    Notes
    -----
    Mathematical assumptions: linear head loss across the blanket
    thickness, so the exit gradient is i_exit = Delta_h_blanket / D_bl
    (spec §3 step f); the critical gradient is the Terzaghi fluidization
    value i_c = gamma'_s/gamma_w, substituted for Pol's independent
    empirical i_c,h ~ Lognormal(0.7, 0.1) (Schweckendiek et al. 2014; SIE
    2024 Table 2) per ADR-0008. The substitution makes this kernel
    identically ``z_uplift(...) / D_bl``: both limit states flip sign at
    the same instant, I_er collapses to ``heave_now``, and Pol's
    hysteresis band (sustain window between 0.7*D_bl and ~0.83*D_bl of
    overpressure) is erased — a small, documented loss of conservatism in
    the sustain phase of each peak (ADR-0008). Heave is checked
    instantaneously, never latched: its deactivation is the only mechanism
    that switches I_er off (spec §11, validation test 4). This is Pol SIE
    2024 Eq. (9) / thesis Eq. (6.8) in the resistance-minus-load reading
    (module docstring, Sign convention).
    """
    delta_h = np.asarray(delta_h_blanket_m, dtype=np.float64)
    gamma_s_sub = np.asarray(gamma_s_sub_knpm3, dtype=np.float64)
    d_bl = np.asarray(d_bl_m, dtype=np.float64)
    i_exit = delta_h / d_bl
    return gamma_s_sub / GAMMA_W - i_exit


def erosion_indicator(
    uplift_ever: ArrayLike,
    pipe_length_positive: ArrayLike,
    heave_now: ArrayLike,
) -> NDArray[np.bool_]:
    """Erosion indicator I_er gating pipe progression (spec §3 step 8i).

    Implements, elementwise over boolean arrays::

        I_er = (uplift_ever | pipe_length_positive) & heave_now

    Parameters
    ----------
    uplift_ever : array_like of bool
        Per-event uplift latch: True from the first timestep at which
        Z_uplift < 0 within the current event, latched for the rest of the
        event. Held and advanced by the M7 timestepper — this module is
        stateless. Implements Pol's running-minimum clause
        min_{0..t} Z_u < 0 (spec §5). Does not carry across events.
    pipe_length_positive : array_like of bool
        True where the pipe-length state l_current > 0. Under the
        monotone non-decreasing pipe length (positive-part operator) this
        is equivalent to Pol's printed l_ini > 0 clause: a pre-existing
        pipe means the blanket is already breached and the uplift gate is
        bypassed; within an event started at l_ini = 0 the clause is
        redundant because growth requires the latch first. It is the
        gateway for compound-event resumption on later peaks without
        re-triggering uplift (spec §3, third subtle point).
    heave_now : array_like of bool
        Instantaneous heave activity, Z_heave < 0 at the current timestep.
        Deliberately unlatched: heave deactivation is the only way I_er
        returns False (spec §11, validation test 4).

    Returns
    -------
    numpy.ndarray of bool
        I_er, broadcast elementwise over the inputs. M7 zeroes dl/dt where
        False (l_current unchanged — the staircase troughs of spec §5).

    Notes
    -----
    First two clauses of Pol SIE 2024 Eq. (7) / thesis Eq. (6.6); the
    third (flood-fighting) clause is deliberately omitted, making the
    transient limit state an unconditional upper bound (module docstring).
    Under the baseline ADR-0008 parameterization the gate reduces to
    ``heave_now``, because Z_heave = Z_uplift / D_bl makes ``heave_now``
    imply ``uplift_ever`` from the same timestep onward. The full
    three-input structure is retained on purpose: it becomes load-bearing
    the moment i_c,h is decoupled from gamma'_s/gamma_w (e.g. a
    sensitivity run with Pol's Lognormal(0.7, 0.1)). Do not simplify it
    away (ADR-0008).
    """
    uplift = np.asarray(uplift_ever, dtype=np.bool_)
    pipe = np.asarray(pipe_length_positive, dtype=np.bool_)
    heave = np.asarray(heave_now, dtype=np.bool_)
    return (uplift | pipe) & heave
