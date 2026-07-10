"""M4 ``hydraulic_translator``: river stage to landside aquifer piezometric head.

Single responsibility (spec §1, M4): given a realization's sampled subsoil
parameters and the cross-section geometry, compute the Mazure leakage lengths
and the response factor r_e, and expose the aquifer head h_aq(t) at the
landside exit point in one of two forms behind a single interface:

1. **Instantaneous translation** (the default form)::

       h_aq(t) = z_toe + r_e * (h_river(t) - z_toe)

   This is Pol SIE 2024 Eq. (10) with phi_it = h_aq and h_e = z_toe. It embeds
   the quasi-static assumption: the aquifer head responds without time lag to
   the river stage.

2. **Linear-reservoir lag** (gated)::

       dh_aq/dt = (1/tau_aq) * [z_toe + r_e * (h_river(t) - z_toe) - h_aq(t)]

   advanced per timestep with the exact exponential update (ADR-0004)::

       h_aq <- h_aq + (1 - exp(-dt/tau_aq)) * (h_aq_inst - h_aq)

Which form is active, and why: the instantaneous form is the default; the lag
form is activated per run by the aquifer-response diagnostic of spec §11
(tau_aq / T_flood at representative parameter values), and the outcome is
recorded in run metadata (``aquifer_lag_active``, ``tau_aq``). The
instantaneous default is *not* assumed permanent. Downstream modules (M5
initiation, M7 progression) consume h_aq(t) through :class:`AquiferHeadModel`
identically in both cases, so activating the lag changes one config flag and
no downstream code (spec §6).

The module is stateless: every kernel is a pure function, including the
lag-state advance :func:`advance_lag_state`, which takes the previous h_aq
and returns the next. The only state in this module is the per-event h_aq
held by the thin :class:`LaggedHead` wrapper that adapts the pure kernel to
the :class:`AquiferHeadModel` protocol.

Hydraulic schematization and provenance (ADR-0006, amended 2026-07-05): the
three-term ratio ``r_e = lambda_in / (lambda_out_eff + L + lambda_in)`` is
the **exact closed form** of USACE (2000) EM 1110-2-1913 Appendix B blanket
theory (Case 7a; landside head factor x3/(x1 + L2 + x3), Eqs. B-3/B-5/B-7)
and of TAW (2004) Model 4A (total resistance = the sum of the subregion
resistances L_n/kD of foreland, dike and hinterland; head linear in the
resistances). Pol (2022) thesis Eq. (7.13), r_e = lambda/(L + lambda), is
its special case with no riverside blanket and an infinitely long polder
blanket; Pol SIE 2024 / CG24 take r_e as a bare deterministic input (0.6).

Under this schematization L (= USACE L2, the levee base width) is the exact
*linear* horizontal-resistance term of the under-levee segment: it is never
inside a tanh and carries **no smallness condition** — there is no "in-L
hyperbolic form" to fall back to (the former L/lambda_in validity monitor
was a category error, withdrawn by the ADR-0006 amendment). The genuine
finite-extent (tanh) corrections apply to the *foreland and hinterland
extents*: the foreland is handled in-model through the effective entry
length ``lambda_out_eff = lambda_out * tanh(B_f / lambda_out)`` (USACE Eq.
B-7; TR Zandmeevoerende Wellen 1999 Eq. (19); TAW 2004 App. I Eq. (A.I.9);
ADR-0006 Decision 1), while the hinterland is taken semi-infinite
(x3 = lambda_in, USACE Eq. B-3, matching Pol Eq. (7.13)) — a site-data
assumption whose status is recorded per run in
``metadata['leakage_geometry']`` (see ADR-0006 Consequences and the
companion note ``docs/decisions/adr0006-leakage-boundary-ratios.md``).

Units and datum
---------------
Strict SI base units throughout (m, s, m/s). Unit conversion happens only in
M1 config loading or M3 hydrograph loading, never inside this module. All
heads and elevations are in meters above one common vertical datum.
``z_toe_m`` is the polder surface elevation at the landside exit point and
equals h_e in Pol SIE 2024 Eqs. (6) and (8) (ADR-0007).

All kernels are vectorized: parameters accept scalars or ``(N,)`` arrays and
broadcast per NumPy rules across realizations (spec §6).

References
----------
Pol (2022), doctoral thesis, Eq. (7.13), p. 158 — derivation of the response
factor. Pol, Kanning, Jonkman & Kok (2024), Structure and Infrastructure
Engineering, Eq. (10) — usage. TR Zandmeevoerende Wellen (TAW, 1999), §4.4.1
Eq. (19). TR Waterspanningen bij dijken (TAW, 2004), App. I Eq. (A.I.9).
USACE EM 1110-2-1913 (2000). ADR-0004 through ADR-0007.
"""

from __future__ import annotations

from typing import Any, Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = [
    "AQUIFER_RESPONSE_GOVERNING_SECTIONS",
    "AQUIFER_RESPONSE_PI_THRESHOLD",
    "AQUIFER_RESPONSE_SS_DRIVER_PER_M",
    "AQUIFER_RESPONSE_SS_RANGE_PER_M",
    "AquiferHeadModel",
    "InstantaneousHead",
    "LaggedHead",
    "advance_lag_state",
    "aquifer_response_diagnostic",
    "aquifer_response_time",
    "leakage_length_in",
    "leakage_length_out",
    "make_head_model",
    "response_factor",
    "translate_instantaneous",
]

# --- ADR-0032 pre-registered aquifer-response diagnostic (spec §11) ----------
# These four values are the Part-1 pre-registration, committed BEFORE any τ_aq
# was computed and applied unchanged in Part 2. They are the single source of
# truth for both the production-run metadata block and the offline study script
# (scripts/aquifer_response_diagnostic.py), so the two can never drift.
AQUIFER_RESPONSE_SS_RANGE_PER_M: tuple[float, float] = (1.0e-5, 1.0e-4)
"""Specific-storage range S_s [1/m] for the dense Tokachi sand-gravel (ADR-0032 D4)."""
AQUIFER_RESPONSE_SS_DRIVER_PER_M: float = 1.0e-4
"""Decision-driver S_s [1/m] — the range upper bound (worst case, τ_aq ∝ S_s)."""
AQUIFER_RESPONSE_PI_THRESHOLD: float = 0.10
"""Activate the lag if τ_aq / T_rise exceeds this (ADR-0032 D3)."""
AQUIFER_RESPONSE_GOVERNING_SECTIONS: tuple[str, ...] = ("KP58.8", "KP60.0")
"""Sections that govern the global gate (ADR-0032 D5): longest τ_aq AND reachable."""

# 90th-percentile standard-normal deviate for the pre-registered τ_aq corner
# (ADR-0032 D3: high D_aq, high D_bl, low k_bl). Hard-coded so this module
# needs no scipy import for the one fixed quantile.
_Z_P90: float = 1.2815515594457412


def _lognormal_quantile(mean: float, cov: float, z: float) -> float:
    """Quantile of a lognormal (arithmetic mean, CoV) at standard-normal deviate z."""
    sigma = np.sqrt(np.log1p(cov * cov))
    mu = np.log(mean) - 0.5 * sigma * sigma
    return float(np.exp(mu + sigma * z))


def leakage_length_in(
    k_aq_mps: ArrayLike,
    d_aq_m: ArrayLike,
    d_bl_m: ArrayLike,
    k_bl_mps: ArrayLike,
) -> NDArray[np.float64]:
    """Hinterland (polder-side) Mazure leakage length lambda_in.

    Implements::

        lambda_in = sqrt(k_aq * D_aq * D_bl / k_bl)

    Parameters
    ----------
    k_aq_mps : array_like of float
        Aquifer horizontal hydraulic conductivity [m/s]. Sampled (theta).
    d_aq_m : array_like of float
        Aquifer thickness [m]. Sampled (theta).
    d_bl_m : array_like of float
        Hinterland blanket thickness [m]. Sampled (theta).
    k_bl_mps : array_like of float
        Hinterland blanket vertical hydraulic conductivity [m/s].
        Sampled (theta).

    Returns
    -------
    numpy.ndarray of float
        Leakage length lambda_in [m], broadcast over the inputs.

    Notes
    -----
    Mathematical assumptions (Pol 2022 thesis Eq. (7.13) schematization):
    steady horizontal Darcy flow in a leaky aquifer, vertical leakage through
    the blanket, semi-infinite hinterland blanket. lambda_in is the distance
    scale over which excess aquifer head decays landward of the exit point.
    """
    k_aq = np.asarray(k_aq_mps, dtype=np.float64)
    d_aq = np.asarray(d_aq_m, dtype=np.float64)
    d_bl = np.asarray(d_bl_m, dtype=np.float64)
    k_bl = np.asarray(k_bl_mps, dtype=np.float64)
    return np.sqrt(k_aq * d_aq * d_bl / k_bl)


def leakage_length_out(
    k_aq_mps: ArrayLike,
    d_aq_m: ArrayLike,
    d_fore_m: ArrayLike,
    k_fore_mps: ArrayLike,
    foreshore_width_m: ArrayLike,
) -> NDArray[np.float64]:
    """Effective riverside (entry) leakage length lambda_out_eff.

    Implements the semi-infinite foreshore leakage length with the
    finite-width hyperbolic-tangent correction (ADR-0005, ADR-0006)::

        lambda_out     = sqrt(k_aq * D_aq * D_fore / k_fore)
        lambda_out_eff = lambda_out * tanh(B_f / lambda_out)

    Parameters
    ----------
    k_aq_mps : array_like of float
        Aquifer horizontal hydraulic conductivity [m/s]. Sampled (theta);
        the same draw feeds :func:`leakage_length_in` per the shared-sample
        contract (ADR-0002).
    d_aq_m : array_like of float
        Aquifer thickness [m]. Sampled (theta).
    d_fore_m : array_like of float
        Foreshore blanket thickness [m]. Deterministic geometry input; per
        ADR-0005 populated with the hinterland A_c value as proxy unless
        separate foreland data exists.
    k_fore_mps : array_like of float
        Foreshore blanket vertical hydraulic conductivity [m/s].
        Deterministic geometry input (A_c proxy, ADR-0005).
    foreshore_width_m : array_like of float
        Foreshore width B_f [m]. ``numpy.inf`` recovers the semi-infinite
        lambda_out; ``0.0`` yields 0, deriving (rather than asserting) the
        no-foreshore treatment (ADR-0006).

    Returns
    -------
    numpy.ndarray of float
        Effective entry leakage length lambda_out_eff [m].

    Notes
    -----
    The tanh correction is TR Zandmeevoerende Wellen (1999) §4.4.1 Eq. (19)
    (there ``L'_v = lambda_1 * tanh(L_v / lambda_1)``), corroborated by TAW
    (2004) App. I Eq. (A.I.9). Asymptotics: lambda_out_eff -> B_f for narrow
    foreshores and -> lambda_out for wide ones. The vanishing-lambda_out
    limit is guarded: it returns 0.0 without dividing by zero.
    """
    k_aq = np.asarray(k_aq_mps, dtype=np.float64)
    d_aq = np.asarray(d_aq_m, dtype=np.float64)
    d_fore = np.asarray(d_fore_m, dtype=np.float64)
    k_fore = np.asarray(k_fore_mps, dtype=np.float64)
    b_f = np.asarray(foreshore_width_m, dtype=np.float64)

    lam_out = np.sqrt(k_aq * d_aq * d_fore / k_fore)
    # Guard lambda_out -> 0 (e.g. a vanishing foreshore blanket): the
    # effective length is then 0 regardless of B_f, without dividing by zero.
    lam_safe = np.where(lam_out > 0.0, lam_out, 1.0)
    lam_eff = lam_out * np.tanh(b_f / lam_safe)
    return np.where(lam_out > 0.0, lam_eff, 0.0)


def response_factor(
    lambda_in_m: ArrayLike,
    lambda_out_eff_m: ArrayLike,
    seepage_length_m: ArrayLike,
) -> NDArray[np.float64]:
    """Aquifer head response factor r_e at the landside exit point.

    Implements::

        r_e = lambda_in / (lambda_out_eff + L + lambda_in)

    Parameters
    ----------
    lambda_in_m : array_like of float
        Hinterland leakage length [m], from :func:`leakage_length_in`.
    lambda_out_eff_m : array_like of float
        Effective riverside leakage length [m], from
        :func:`leakage_length_out`.
    seepage_length_m : array_like of float
        Seepage length L across the levee base [m]. Geometry input.

    Returns
    -------
    numpy.ndarray of float
        Response factor r_e [-], in the open interval (0, 1) for physical
        inputs.

    Notes
    -----
    Exact — for any L — under the USACE (2000) Case 7a / TAW (2004) Model 4A
    schematization: steady horizontal Darcy flow in a leaky aquifer, vertical
    leakage through the blankets, quasi-static response. This is the USACE
    landside head factor x3/(x1 + L2 + x3) with x1 = ``lambda_out_eff_m``
    (finite foreland, Eq. B-7), L2 = ``seepage_length_m`` (levee base width,
    an exact linear resistance never inside a tanh — the retired L/lambda_in
    "validity" monitor compared the wrong two lengths, ADR-0006 amendment)
    and x3 = ``lambda_in_m`` (semi-infinite hinterland, Eq. B-3; the
    hinterland-extent assumption is a recorded site-data item). Pol (2022)
    Eq. (7.13) is the x1 = 0 special case. r_e is stochastic: it depends on
    four of the seven sampled variables through the leakage lengths and must
    be computed per realization, never precomputed once (spec Property 3).
    """
    lam_in = np.asarray(lambda_in_m, dtype=np.float64)
    lam_out_eff = np.asarray(lambda_out_eff_m, dtype=np.float64)
    length = np.asarray(seepage_length_m, dtype=np.float64)
    return lam_in / (lam_out_eff + length + lam_in)


def aquifer_response_time(
    d_aq_m: ArrayLike,
    d_bl_m: ArrayLike,
    k_bl_mps: ArrayLike,
    specific_storage_per_m: float,
) -> NDArray[np.float64]:
    """Aquifer response time tau_aq for the linear-reservoir lag option.

    Implements::

        tau_aq = S_s * D_aq * D_bl / k_bl

    which is identically ``lambda_in**2 * S_s / k_aq``: k_aq cancels, so
    tau_aq depends on three of the seven sampled variables (D_aq, D_bl,
    k_bl) times the deterministic specific storage (ADR-0004).

    Parameters
    ----------
    d_aq_m : array_like of float
        Aquifer thickness [m]. Sampled (theta).
    d_bl_m : array_like of float
        Hinterland blanket thickness [m]. Sampled (theta).
    k_bl_mps : array_like of float
        Hinterland blanket vertical hydraulic conductivity [m/s].
        Sampled (theta).
    specific_storage_per_m : float
        Specific storage S_s of the aquifer [1/m]. Deterministic literature
        value from config — not an eighth random variable (ADR-0004); S_s
        uncertainty is handled as a bounded sensitivity run.

    Returns
    -------
    numpy.ndarray of float
        Response time tau_aq [s], one value per realization.

    Notes
    -----
    Feeds the spec §11 aquifer-response diagnostic (tau_aq / T_flood,
    evaluated at representative values to set the run-global lag flag) and,
    when the lag is active, :class:`LaggedHead` per realization.
    """
    d_aq = np.asarray(d_aq_m, dtype=np.float64)
    d_bl = np.asarray(d_bl_m, dtype=np.float64)
    k_bl = np.asarray(k_bl_mps, dtype=np.float64)
    return specific_storage_per_m * d_aq * d_bl / k_bl


def aquifer_response_diagnostic(
    *,
    segment_id: str,
    d_aq_mean_m: float,
    d_bl_mean_m: float,
    k_bl_mean_mps: float,
    d_aq_cov: float,
    d_bl_cov: float,
    k_bl_cov: float,
    t_rise_s: float | None,
    t_plateau_s: float | None,
    native_dt_s: float | None,
    s_s_per_m: float = AQUIFER_RESPONSE_SS_DRIVER_PER_M,
) -> dict[str, Any]:
    """Evaluate the pre-registered ADR-0032 aquifer-response gate for one section.

    Applies the Part-1 pre-registration (spec §11) unchanged: forms τ_aq at the
    section's central (prior-mean) parameters and at the 90th-percentile-τ_aq
    corner (high D_aq, high D_bl, low k_bl), both at the decision-driver
    specific storage; forms Π = τ_aq / T_rise (Check A) against the threshold
    :data:`AQUIFER_RESPONSE_PI_THRESHOLD`; and forms the Nyquist native-
    resolution test (Check B). Assembles the descriptive record stamped into
    run metadata as ``metadata['aquifer_response']``.

    This is the pure **analytic** core (means, CoVs, timescales in → verdict
    out); the orchestrator additionally enriches the block with empirical τ_aq
    percentiles from the drawn prior sample.

    Parameters
    ----------
    segment_id : str
        Section identifier (e.g. ``'KP58.8'``); flags whether this section is
        one of the pre-registered governing pair.
    d_aq_mean_m, d_bl_mean_m, k_bl_mean_mps : float
        Prior means of aquifer thickness, blanket thickness and blanket
        conductivity — the three variables τ_aq depends on (k_aq cancels).
    d_aq_cov, d_bl_cov, k_bl_cov : float
        Their coefficients of variation, for the lognormal corner quantiles.
    t_rise_s : float or None
        Characteristic rising-limb time [s] (the Π denominator). ``None`` when
        the loading timescales are unavailable (e.g. the synthetic-stub path);
        Π and the verdict then degrade gracefully.
    t_plateau_s : float or None
        Peak-plateau width [s], for the Check-B feature size.
    native_dt_s : float or None
        Native sampling interval [s] of the loading record.
    s_s_per_m : float, optional
        Specific storage [1/m] used for τ_aq. Defaults to the pre-registered
        decision-driver (range upper bound); pass a different value only for an
        explicit S_s sensitivity.

    Returns
    -------
    dict
        The ADR-0032 record: S_s range/driver, threshold, the central and
        corner τ_aq [s], the timescales, Π central/corner, the Check-A and
        Check-B booleans, the governing-section flag and the per-section
        ``verdict`` (``'instantaneous'`` / ``'lag_indicated'`` /
        ``'timescales_unavailable'``). All values are JSON-native.

    Notes
    -----
    The verdict is *descriptive* — the run's actual translation form is the
    global ``config.timestepper.aquifer_lag_active`` flag, stamped separately as
    ``metadata['aquifer_lag_active']``. For a production run under the ADR-0032
    verdict the two agree (instantaneous); a deliberate S_s/lag sensitivity run
    would show them diverge, which is the intended, legible signal.
    """
    tau_central = float(
        aquifer_response_time(d_aq_mean_m, d_bl_mean_m, k_bl_mean_mps, s_s_per_m)
    )
    tau_corner = float(
        aquifer_response_time(
            _lognormal_quantile(d_aq_mean_m, d_aq_cov, _Z_P90),
            _lognormal_quantile(d_bl_mean_m, d_bl_cov, _Z_P90),
            _lognormal_quantile(k_bl_mean_mps, k_bl_cov, -_Z_P90),
            s_s_per_m,
        )
    )
    block: dict[str, Any] = {
        "diagnostic": "adr_0032_aquifer_response",
        "s_s_range_per_m": list(AQUIFER_RESPONSE_SS_RANGE_PER_M),
        "s_s_driver_per_m": float(s_s_per_m),
        "pi_threshold": AQUIFER_RESPONSE_PI_THRESHOLD,
        "governing_section": segment_id in AQUIFER_RESPONSE_GOVERNING_SECTIONS,
        "tau_aq_central_s": tau_central,
        "tau_aq_corner90_s": tau_corner,
        "t_rise_s": None if t_rise_s is None else float(t_rise_s),
        "t_plateau_s": None if t_plateau_s is None else float(t_plateau_s),
        "native_dt_s": None if native_dt_s is None else float(native_dt_s),
    }

    if t_rise_s is not None and t_rise_s > 0.0:
        pi_central = tau_central / t_rise_s
        block["pi_central"] = float(pi_central)
        block["pi_corner90"] = float(tau_corner / t_rise_s)
        check_a: bool | None = bool(pi_central <= AQUIFER_RESPONSE_PI_THRESHOLD)
    else:
        block["pi_central"] = None
        block["pi_corner90"] = None
        check_a = None
    block["check_a_instantaneous_justified"] = check_a

    if t_plateau_s is not None and t_rise_s is not None and native_dt_s is not None:
        t_feature = min(t_plateau_s, t_rise_s)
        check_b: bool | None = bool(native_dt_s <= t_feature / 2.0)
    else:
        check_b = None
    block["check_b_native_resolves"] = check_b

    if check_a is None:
        block["verdict"] = "timescales_unavailable"
    elif check_a and (check_b is None or check_b):
        block["verdict"] = "instantaneous"
    else:
        block["verdict"] = "lag_indicated"
    return block


def translate_instantaneous(
    h_river_m: ArrayLike,
    r_e: ArrayLike,
    z_toe_m: ArrayLike,
) -> NDArray[np.float64]:
    """Instantaneous river-stage-to-aquifer-head translation.

    Implements Pol SIE 2024 Eq. (10)::

        h_aq = z_toe + r_e * (h_river - z_toe)

    Parameters
    ----------
    h_river_m : array_like of float
        River stage [m above datum]. A scalar per timestep in the M7 loop,
        or a full ``(T,)`` series.
    r_e : array_like of float
        Response factor [-], from :func:`response_factor`.
    z_toe_m : array_like of float
        Polder surface elevation at the landside exit point [m above
        datum]; equals h_e in Pol SIE 2024 Eqs. (6) and (8) (ADR-0007).

    Returns
    -------
    numpy.ndarray of float
        Aquifer head h_aq [m above datum], broadcast over the inputs.

    Notes
    -----
    Single source of the translation formula: used by the static-branch peak
    translation (spec §3 step 4), by :class:`InstantaneousHead`, and as the
    equilibrium initial condition of :class:`LaggedHead` (ADR-0004). The
    same r_e feeds both limit-state branches per the shared-sample contract
    (ADR-0002). Assumes quasi-static aquifer response (no time lag).
    """
    h_river = np.asarray(h_river_m, dtype=np.float64)
    r_factor = np.asarray(r_e, dtype=np.float64)
    z_toe = np.asarray(z_toe_m, dtype=np.float64)
    return z_toe + r_factor * (h_river - z_toe)


def advance_lag_state(
    h_aq_prev_m: ArrayLike,
    h_river_m: ArrayLike,
    r_e: ArrayLike,
    z_toe_m: ArrayLike,
    dt_s: float,
    tau_aq_s: ArrayLike,
) -> NDArray[np.float64]:
    """Pure one-timestep advance of the linear-reservoir lag state.

    Takes the previous aquifer head and returns the next; holds no state
    itself. Implements the exact solution of the linear-reservoir ODE under
    piecewise-constant forcing (ADR-0004)::

        h_aq_next = h_aq_prev + (1 - exp(-dt/tau_aq)) * (h_inst - h_aq_prev)

    with ``h_inst = translate_instantaneous(h_river_m, r_e, z_toe_m)``.

    Parameters
    ----------
    h_aq_prev_m : array_like of float
        Aquifer head at the previous timestep [m above datum].
    h_river_m : array_like of float
        River stage at the current timestep [m above datum].
    r_e : array_like of float
        Response factor [-], from :func:`response_factor`.
    z_toe_m : array_like of float
        Polder surface elevation at the landside exit point [m above datum]
        (equals h_e in Pol SIE 2024 Eqs. (6) and (8), ADR-0007).
    dt_s : float
        Timestep [s].
    tau_aq_s : array_like of float
        Aquifer response time [s] per realization, from
        :func:`aquifer_response_time`. Must be positive.

    Returns
    -------
    numpy.ndarray of float
        Aquifer head at the current timestep [m above datum].

    Notes
    -----
    The update factor ``1 - exp(-dt/tau_aq)`` lies in (0, 1) for all
    positive ``dt_s`` and ``tau_aq_s``: unconditionally stable (the state is
    a convex combination of its previous value and the instantaneous head),
    exact for the assumed forcing, equal to the explicit-Euler form in the
    limit ``dt_s << tau_aq_s``, and collapsing to the instantaneous
    translation as ``tau_aq_s -> 0``. Explicit Euler, by contrast,
    overshoots for ``dt_s > tau_aq_s`` and diverges for
    ``dt_s > 2 * tau_aq_s`` (ADR-0004). The factor is computed as
    ``-expm1(-dt/tau_aq)`` for accuracy when ``dt_s << tau_aq_s``.
    """
    h_prev = np.asarray(h_aq_prev_m, dtype=np.float64)
    tau_aq = np.asarray(tau_aq_s, dtype=np.float64)
    h_inst = translate_instantaneous(h_river_m, r_e, z_toe_m)
    factor = -np.expm1(-dt_s / tau_aq)
    return h_prev + factor * (h_inst - h_prev)


class AquiferHeadModel(Protocol):
    """Unified per-timestep interface for the aquifer head at the exit point.

    The downstream initiation (M5) and progression (M7) modules hold one
    instance and call :meth:`step` once per timestep; the instantaneous and
    lagged forms are interchangeable behind this protocol, so activating the
    lag changes one config flag and no downstream code (spec §6).

    State management contract (spec §5): model state is re-initialized per
    event via :meth:`reset` and carries across timesteps within one event
    only. Pipe length is the sole cross-event state in the engine; the
    aquifer head is not.
    """

    def reset(self, h_river_initial_m: float) -> None:
        """Re-initialize the model state for a new event.

        Parameters
        ----------
        h_river_initial_m : float
            River stage at the first sample of the event hydrograph
            [m above datum].
        """
        ...

    def step(self, h_river_m: float, dt_s: float) -> NDArray[np.float64]:
        """Advance one timestep and return the aquifer head.

        Parameters
        ----------
        h_river_m : float
            River stage at the current timestep [m above datum].
        dt_s : float
            Timestep [s]. Ignored by the instantaneous form.

        Returns
        -------
        numpy.ndarray of float
            Aquifer head h_aq at the landside exit point [m above datum];
            shape ``(N,)`` for per-realization (vector) r_e, scalar for
            scalar r_e.
        """
        ...


class InstantaneousHead:
    """Instantaneous (quasi-static) aquifer head model — the default form.

    Stateless: :meth:`step` returns
    ``translate_instantaneous(h_river_m, r_e, z_toe_m)`` and ignores
    ``dt_s``; :meth:`reset` is a no-op retained for interface symmetry with
    :class:`AquiferHeadModel`.

    Parameters
    ----------
    r_e : array_like of float
        Response factor [-] per realization, from :func:`response_factor`.
    z_toe_m : float
        Polder surface elevation at the landside exit point [m above datum]
        (equals h_e in Pol SIE 2024 Eqs. (6) and (8), ADR-0007).
    """

    def __init__(self, r_e: ArrayLike, z_toe_m: float) -> None:
        self._r_e = np.asarray(r_e, dtype=np.float64)
        self._z_toe_m = z_toe_m

    def reset(self, h_river_initial_m: float) -> None:
        """No-op (stateless model); see :class:`AquiferHeadModel`."""

    def step(self, h_river_m: float, dt_s: float) -> NDArray[np.float64]:
        """Return the instantaneous translation; ``dt_s`` is ignored."""
        return translate_instantaneous(h_river_m, self._r_e, self._z_toe_m)


class LaggedHead:
    """First-order linear-reservoir aquifer head model (lag form, gated).

    A thin stateful adapter: the physics lives in the pure kernel
    :func:`advance_lag_state`; this class only carries the per-event head
    between :meth:`step` calls to satisfy :class:`AquiferHeadModel`.

    The update factor lies in (0, 1) for all positive ``dt_s`` and
    ``tau_aq_s``: unconditionally stable, exact for piecewise-constant
    forcing, equal to the explicit-Euler form in the limit
    ``dt_s << tau_aq_s``, and collapsing exactly to the instantaneous
    translation as ``tau_aq_s -> 0`` (ADR-0004).

    :meth:`reset` initializes the state in equilibrium with the initial
    river stage, ``h_aq(0) = translate_instantaneous(h0, r_e, z_toe_m)``
    (ADR-0004): the aquifer has been at base stage long before the event; a
    cold start at z_toe would inject a spurious filling transient.

    State carries across timesteps within one event only and is reset per
    event; it does not carry across events (spec §5).

    Parameters
    ----------
    r_e : array_like of float
        Response factor [-] per realization, from :func:`response_factor`.
    z_toe_m : float
        Polder surface elevation at the landside exit point [m above datum]
        (equals h_e in Pol SIE 2024 Eqs. (6) and (8), ADR-0007).
    tau_aq_s : array_like of float
        Aquifer response time [s] per realization, from
        :func:`aquifer_response_time`. Must be positive.

    Raises
    ------
    ValueError
        If any ``tau_aq_s`` is not strictly positive.
    """

    def __init__(self, r_e: ArrayLike, z_toe_m: float, tau_aq_s: ArrayLike) -> None:
        tau_aq = np.asarray(tau_aq_s, dtype=np.float64)
        if np.any(tau_aq <= 0.0):
            raise ValueError("tau_aq_s must be strictly positive")
        self._r_e = np.asarray(r_e, dtype=np.float64)
        self._z_toe_m = z_toe_m
        self._tau_aq_s = tau_aq
        self._h_aq_m: NDArray[np.float64] | None = None

    def reset(self, h_river_initial_m: float) -> None:
        """Set the state to equilibrium with the initial river stage."""
        self._h_aq_m = translate_instantaneous(
            h_river_initial_m, self._r_e, self._z_toe_m
        )

    def step(self, h_river_m: float, dt_s: float) -> NDArray[np.float64]:
        """Advance the lag state by ``dt_s`` and return the aquifer head."""
        if self._h_aq_m is None:
            raise RuntimeError("LaggedHead.step() called before reset()")
        self._h_aq_m = advance_lag_state(
            self._h_aq_m, h_river_m, self._r_e, self._z_toe_m, dt_s, self._tau_aq_s
        )
        return self._h_aq_m


def make_head_model(
    r_e: ArrayLike,
    z_toe_m: float,
    *,
    lag_active: bool,
    tau_aq_s: ArrayLike | None = None,
) -> AquiferHeadModel:
    """Factory dispatching on the run-global aquifer-lag flag.

    Parameters
    ----------
    r_e : array_like of float
        Response factor [-] per realization, from :func:`response_factor`.
    z_toe_m : float
        Polder surface elevation at the landside exit point [m above datum]
        (equals h_e in Pol SIE 2024 Eqs. (6) and (8), ADR-0007).
    lag_active : bool
        Run-global flag from M1 config, set by the spec §11 tau_aq/T_flood
        diagnostic at representative parameter values (ADR-0004) and
        recorded in run metadata (``aquifer_lag_active``, ``tau_aq``).
    tau_aq_s : array_like of float, optional
        Per-realization response time [s], from
        :func:`aquifer_response_time`. Required when ``lag_active`` is True.

    Returns
    -------
    AquiferHeadModel
        :class:`InstantaneousHead` when ``lag_active`` is False, otherwise
        :class:`LaggedHead`.

    Raises
    ------
    ValueError
        If ``lag_active`` is True and ``tau_aq_s`` is None.
    """
    if lag_active:
        if tau_aq_s is None:
            raise ValueError("tau_aq_s is required when lag_active is True")
        return LaggedHead(r_e, z_toe_m, tau_aq_s)
    return InstantaneousHead(r_e, z_toe_m)
