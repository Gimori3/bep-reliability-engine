"""Sellmeijer (2011) critical head and critical pipe length (module M6).

Implements the revised Sellmeijer backward-erosion-piping resistance model

    H_c = L * F_r * F_s * F_g

published as the adapted piping rule of Sellmeijer, Lopez de la Cruz,
van Beek & Knoeff (2011), "Fine-tuning of the backward erosion piping
model through small-scale, medium-scale and IJkdijk experiments", EJECE
15(8):1139-1154 (formula [6] in that paper), and restated as Eq. (12) of
Pol, Kanning, Jonkman & Kok (2024), "Time-dependent reliability analysis
of flood defenses under cumulative internal erosion", Structure and
Infrastructure Engineering -- the Eq. (12) numbering is the one used by
the project spec.

The critical pipe length follows Pol et al. (2024, SIE) Eq. (13),

    l_c / L = 0.5 * tanh(2 * D_aq / L)

valid for homogeneous aquifers, where it agrees with 2D numerical piping
simulations (Sellmeijer 2006; Rosenbrand et al. 2022).

This module is the single source of H_c and l_c for both limit states
(spec section 1, M6): the static Sellmeijer comparison and the equilibrium
curve H_eq(l) of the Pol progression ODE (M7) must both obtain H_c here so
the two uses cannot drift apart. The optional ``alpha_exponent`` argument
is the sensitivity hook of spec section 12 (failure mode 4) for
substituting the 3D hole-type-exit scale exponent alpha = -1/2 for the 2D
plane-strain value alpha = -1/3; it enters through the scale factor F_s,
which is where the -1/3 exponent of the published rule lives.

All computations are in strict SI base units (m, s, m/s, radians); unit
weights are in kN/m^3, consistent with ``constants.GAMMA_W``.
"""

import logging
import math
from typing import NamedTuple

import numpy as np
import numpy.typing as npt

from .constants import GAMMA_W, GRAVITY

logger = logging.getLogger(__name__)

__all__ = [
    "GAMMA_W",
    "ETA_WHITE",
    "THETA_REPOSE_DEFAULT",
    "GAMMA_P_SUB_DEFAULT",
    "D_R_MEAN",
    "C_U_MEAN",
    "KAS_MEAN",
    "D_70_MEAN_M",
    "NU_WATER_M2_PER_S",
    "SellmeijerResult",
    "compute_critical_head",
    "compute_critical_head_vectorized",
    "compute_critical_pipe_length",
]

# --- Physical constants ----------------------------------------------------

# White's drag coefficient eta [-] (Sellmeijer 2011, formula [6]; Pol 2024
# SIE, Eq. (12)). An alternate calibrated value of 0.30 exists in Dutch
# assessment practice; 0.25 is the value of both source papers.
ETA_WHITE: float = 0.25

# Bedding (repose) angle of the sand, deterministic at 37 degrees per spec
# section 7. Stored in radians per docs/conventions.md section 2.
THETA_REPOSE_DEFAULT: float = math.radians(37.0)

# Submerged unit weight of the aquifer sand particles gamma'_p [kN/m^3],
# deterministic (Tokachi basin-wide value from the A_g specific gravities;
# thesis "Fixed Parameters"). Per ADR-0016 this particle weight is what enters
# the Sellmeijer resistance factor F_r; it is distinct from, and must not be
# confused with, the stochastic submerged blanket weight gamma_bl_sub of the
# theta vector, which drives the M5 uplift and heave limit states only.
GAMMA_P_SUB_DEFAULT: float = 16.87

# --- Sellmeijer (2011) experimental mean values -----------------------------
# Means of the small-scale test programme used to normalize the regression
# ratio terms in F_r and F_s (Sellmeijer 2011, Table 2; restated below
# Eq. (12) of Pol et al. 2024 SIE). D_R_MEAN doubles as the in-situ
# relative-density *default* (the Pol base case sits at the experimental mean,
# making the F_r ratio term exactly 1); the separate run-value duplicate
# D_R_DEFAULT was retired per the ADR-0015 cleanup mandate once config's
# ``relative_density_insitu`` threading landed — the run value is config-owned,
# and this normalization mean is the sole 0.725 constant in M6.

D_R_MEAN: float = 0.725  # mean relative density D_r,m [-]
C_U_MEAN: float = 1.81  # mean uniformity coefficient C_u,m [-]
KAS_MEAN: float = 0.498  # mean angularity KAS_m [-]
D_70_MEAN_M: float = 2.08e-4  # mean grain size d_70,m [m]

# Kinematic viscosity of water at 10 degC [m^2/s], entering the intrinsic
# permeability kappa = k_aq * nu / g (Pol et al. 2024 SIE, Eq. (12)).
NU_WATER_M2_PER_S: float = 1.3e-6

# Canonical theta-vector column order (spec section 2, M2 contract).
_PARAM_NAMES: list[str] = [
    "k_aq",
    "d_70",
    "D_aq",
    "D_bl",
    "k_bl",
    "gamma_bl_sub",
    "C_e",
]


class SellmeijerResult(NamedTuple):
    """Critical head and critical pipe length from one M6 evaluation.

    Fields hold floats when produced by :func:`compute_critical_head` and
    (N,)-shaped float64 arrays when produced by
    :func:`compute_critical_head_vectorized`.
    """

    H_c: float | npt.NDArray[np.float64]
    l_c: float | npt.NDArray[np.float64]


def _factor_Fr(
    gamma_p_sub_kn_m3: float | npt.NDArray[np.float64] = GAMMA_P_SUB_DEFAULT,
    theta_repose_rad: float = THETA_REPOSE_DEFAULT,
    relative_density: float = D_R_MEAN,
    uniformity_cu: float = C_U_MEAN,
    angularity_kas: float = KAS_MEAN,
    eta: float = ETA_WHITE,
) -> float | npt.NDArray[np.float64]:
    """Resistance factor F_r of the revised Sellmeijer model.

    F_r = eta * (gamma'_p / gamma_w) * tan(theta)
          * (D_r / D_r,m)^0.35 * (C_u / C_u,m)^0.13 * (KAS / KAS_m)^-0.02

    per Sellmeijer (2011) formula [6] / Pol (2024 SIE) Eq. (12).

    Parameters
    ----------
    gamma_p_sub_kn_m3 : float or ndarray, optional
        Submerged unit weight of the aquifer sand particles
        gamma'_p = (rho_s - rho_w) * g [kN/m^3]. Deterministic on the
        production path (default ``GAMMA_P_SUB_DEFAULT``, ADR-0016); it is
        *not* read from the theta vector and is distinct from the stochastic
        blanket weight ``gamma_bl_sub``. It enters as the dimensionless ratio
        gamma'_p / gamma_w. Reference-case tests override it with the
        case-specific particle weight.
    theta_repose_rad : float, optional
        Bedding (repose) angle of the sand [rad]. Deterministic, default
        37 degrees (spec section 7).
    relative_density : float, optional
        In-situ relative density D_r [-], the F_r ratio numerator. Default
        ``D_R_MEAN`` (the run value equals the experimental mean, the Pol
        base case) makes the regression ratio term equal to 1; the run value
        is config-owned (``relative_density_insitu``, ADR-0015).
    uniformity_cu : float, optional
        Uniformity coefficient C_u = d_60/d_10 [-]. Default ``C_U_MEAN``
        makes the regression ratio term equal to 1.
    angularity_kas : float, optional
        Particle roundness KAS [-]. Default ``KAS_MEAN`` makes the
        regression ratio term equal to 1.
    eta : float, optional
        White's drag coefficient [-], default ``ETA_WHITE`` = 0.25.

    Returns
    -------
    float or ndarray
        Dimensionless resistance factor F_r [-], broadcasting over
        ``gamma_p_sub_kn_m3``.

    Notes
    -----
    The empirical exponents 0.35, 0.13 and -0.02 are the multivariate
    regression weights of Sellmeijer (2011), Table 1; they are valid only
    inside the tested parameter limits (Table 2). With all three optional
    arguments left at the experimental means this reduces to the classical
    F_r = eta * (gamma'_p / gamma_w) * tan(theta).
    """
    return (
        eta
        * (gamma_p_sub_kn_m3 / GAMMA_W)
        * math.tan(theta_repose_rad)
        * (relative_density / D_R_MEAN) ** 0.35
        * (uniformity_cu / C_U_MEAN) ** 0.13
        * (angularity_kas / KAS_MEAN) ** -0.02
    )


def _factor_Fs(
    d_70_m: float | npt.NDArray[np.float64],
    k_aq_mps: float | npt.NDArray[np.float64],
    seepage_length_m: float,
    alpha_exponent: float = -1.0 / 3.0,
) -> float | npt.NDArray[np.float64]:
    """Scale factor F_s of the revised Sellmeijer model.

    F_s = (d_70^3 / (kappa * L))^(-alpha) * (d_70,m / d_70)^0.6,
    with the intrinsic permeability kappa = k_aq * nu / g [m^2].

    At the default 2D Sellmeijer exponent alpha = -1/3 this reduces
    exactly to formula [6] of Sellmeijer (2011) / Eq. (12) of Pol (2024
    SIE):  F_s = d_70 / (kappa * L)^(1/3) * (d_70,m / d_70)^0.6.

    Parameters
    ----------
    d_70_m : float or ndarray
        Representative grain size d_70 [m]. The empirical grain-size
        correction (d_70,m / d_70)^0.6 restricts validity to the tested
        range 150e-6 to 430e-6 m (Sellmeijer 2011, Table 2).
    k_aq_mps : float or ndarray
        Aquifer hydraulic conductivity [m/s].
    seepage_length_m : float
        Seepage length L across the structure [m].
    alpha_exponent : float, optional
        Scale exponent alpha [-]. Default -1/3 (2D plane strain);
        substitute -1/2 for the 3D hole-type-exit scaling.

    Returns
    -------
    float or ndarray
        Dimensionless scale factor F_s [-], broadcasting over the array
        arguments.

    Notes
    -----
    The alpha substitution is applied through the dimensionless group
    d_70^3 / (kappa * L) so that any alpha yields a dimensionless F_s and
    alpha = -1/3 reproduces the published rule identically. At field
    seepage lengths d_70^3 / (kappa * L) << 1, so the 3D value alpha =
    -1/2 lowers F_s and hence H_c, consistent with van Beek (2015). This
    is a sensitivity hook for the bias decomposition of spec section 12
    (failure mode 4), not a validated 3D model.
    """
    kappa_m2 = k_aq_mps * NU_WATER_M2_PER_S / GRAVITY
    scale_group = d_70_m**3 / (kappa_m2 * seepage_length_m)
    return scale_group**-alpha_exponent * (D_70_MEAN_M / d_70_m) ** 0.6


def _factor_Fg(
    D_aq_m: float | npt.NDArray[np.float64],
    seepage_length_m: float,
) -> float | npt.NDArray[np.float64]:
    """Geometrical shape factor F_g of the revised Sellmeijer model.

    F_g = 0.91 * (D_aq / L)^( 0.28 / ((D_aq / L)^2.8 - 1) + 0.04 )

    per Sellmeijer (2011) formula [6] / Pol (2024 SIE) Eq. (12).

    Parameters
    ----------
    D_aq_m : float or ndarray
        Aquifer (sand layer) thickness D [m].
    seepage_length_m : float
        Seepage length L across the structure [m].

    Returns
    -------
    float or ndarray
        Dimensionless geometrical shape factor F_g [-], broadcasting over
        ``D_aq_m``.

    Notes
    -----
    Valid for a sand layer of constant thickness (Sellmeijer 2011). The
    exponent has a removable singularity at D_aq / L = 1; that point is
    handled explicitly by substituting the finite limit value
    0.91 * exp(0.1) * (D_aq/L)^0.04 rather than relying on floating-point
    evaluation of 0.28 / 0.
    """
    thickness_ratio = np.asarray(D_aq_m, dtype=np.float64) / seepage_length_m
    denom = thickness_ratio**2.8 - 1.0
    with np.errstate(divide="ignore"):
        exponent = 0.28 / denom + 0.04
    f_g = 0.91 * np.where(
        denom == 0.0,
        math.exp(0.1) * thickness_ratio**0.04,
        thickness_ratio**exponent,
    )
    if f_g.ndim == 0:
        return float(f_g)
    return f_g


def compute_critical_head(
    theta_row: npt.NDArray[np.float64],
    geometry: dict,
    alpha_exponent: float = -1.0 / 3.0,
    gamma_p_sub_kn_m3: float = GAMMA_P_SUB_DEFAULT,
    theta_repose_rad: float = THETA_REPOSE_DEFAULT,
    relative_density: float = D_R_MEAN,
) -> SellmeijerResult:
    """Critical head H_c and critical pipe length l_c, one realization.

    H_c = L * F_r * F_s * F_g  (Sellmeijer 2011 formula [6]; Pol 2024 SIE
    Eq. (12)), the critical hydraulic head difference across the structure
    at which backward erosion progresses to failure, together with the
    critical pipe length l_c of Pol (2024 SIE) Eq. (13).

    Parameters
    ----------
    theta_row : ndarray, shape (7,)
        One realization's parameter vector in the canonical column order
        ``['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']``
        (spec section 2). Consumed here: ``k_aq`` [m/s], ``d_70`` [m] and
        ``D_aq`` [m]. The submerged particle unit weight gamma'_p enters via
        the deterministic ``gamma_p_sub_kn_m3`` argument, not from the theta
        vector (ADR-0016); ``D_bl``, ``k_bl``, the blanket weight
        ``gamma_bl_sub`` and ``C_e`` do not enter H_c -- the static branch
        has no C_e exposure by design (ADR-0001).
    geometry : dict
        Cross-section geometry; only ``geometry['L']`` (seepage length
        [m]) is read here. The other canonical keys (``z_toe``,
        ``foreshore_width``, ``D_fore``, ``k_fore``; ADR-0010) are accepted
        and ignored.
    alpha_exponent : float, optional
        Scale exponent alpha [-] passed to the scale factor F_s. Default
        -1/3 (2D Sellmeijer); -1/2 substitutes the 3D hole-type-exit
        value for the sensitivity decomposition of spec section 12,
        failure mode 4.
    gamma_p_sub_kn_m3 : float, optional
        Submerged aquifer particle unit weight gamma'_p [kN/m^3] for the
        resistance factor F_r. Deterministic (default
        ``GAMMA_P_SUB_DEFAULT``, ADR-0016); reference-case tests override it
        with the case-specific particle weight.
    theta_repose_rad : float, optional
        Bedding (repose) angle [rad] entering F_r through tan(theta).
        Deterministic, run-owned (ADR-0015); default ``THETA_REPOSE_DEFAULT``
        (37 deg). Threaded from ``config.theta_repose_rad`` by M8 so a run can
        override it without editing the module constant.
    relative_density : float, optional
        In-situ relative density D_r [-], the numerator of the F_r ratio
        ``(D_r / D_r,m)^0.35`` (ADR-0015). Defaults to ``D_R_MEAN`` (the run
        value equals the regression-mean denominator D_r,m, so the ratio is
        1 — the Pol base case); the run value is config-owned
        (``relative_density_insitu``) and threaded here by M8.

    Returns
    -------
    SellmeijerResult
        Named tuple ``(H_c, l_c)`` with the critical head H_c [m] and the
        critical pipe length l_c [m], both floats.

    Raises
    ------
    ValueError
        If H_c is not strictly positive (including NaN), with the
        offending parameter values in the message. Per spec section 12
        (failure mode 2) such realizations indicate priors that need
        re-bounding; the caller logs and skips them.

    Notes
    -----
    Mathematical assumptions: 2D plane-strain groundwater flow under a
    dike of constant sand-layer thickness; relative density, uniformity
    and angularity fixed at the Sellmeijer experimental means so their
    regression ratio terms equal 1 (spec section 7); deterministic repose
    angle of 37 degrees; kinematic viscosity at 10 degC in kappa = k_aq *
    nu / g. The empirical grain-size adaptation restricts validity to
    d_70 in [150e-6, 430e-6] m (Sellmeijer 2011, Table 2). H_c is a head
    *difference* across the structure and carries no datum of its own;
    the caller (M8) is responsible for comparing it against the
    r_e-translated load head.
    """
    seepage_length_m = geometry["L"]
    k_aq_mps = float(theta_row[_PARAM_NAMES.index("k_aq")])
    d_70_m = float(theta_row[_PARAM_NAMES.index("d_70")])
    D_aq_m = float(theta_row[_PARAM_NAMES.index("D_aq")])

    h_c = (
        seepage_length_m
        * _factor_Fr(
            gamma_p_sub_kn_m3,
            theta_repose_rad=theta_repose_rad,
            relative_density=relative_density,
        )
        * _factor_Fs(d_70_m, k_aq_mps, seepage_length_m, alpha_exponent)
        * _factor_Fg(D_aq_m, seepage_length_m)
    )
    # "not (h_c > 0)" instead of "h_c <= 0" so that NaN from pathological
    # theta values is rejected as well.
    if not (h_c > 0.0):
        raise ValueError(
            f"Non-positive critical head H_c={h_c} for k_aq={k_aq_mps} m/s, "
            f"d_70={d_70_m} m, D_aq={D_aq_m} m, "
            f"gamma_p_sub={gamma_p_sub_kn_m3} kN/m^3, L={seepage_length_m} m, "
            f"alpha_exponent={alpha_exponent}; re-bound the priors "
            "(spec section 12, failure mode 2)."
        )
    l_c = compute_critical_pipe_length(D_aq_m, seepage_length_m)
    return SellmeijerResult(H_c=float(h_c), l_c=float(l_c))


def compute_critical_head_vectorized(
    theta_matrix: npt.NDArray[np.float64],
    geometry: dict,
    alpha_exponent: float = -1.0 / 3.0,
    gamma_p_sub_kn_m3: float = GAMMA_P_SUB_DEFAULT,
    theta_repose_rad: float = THETA_REPOSE_DEFAULT,
    relative_density: float = D_R_MEAN,
) -> SellmeijerResult:
    """Critical head H_c and critical pipe length l_c for all N
    realizations at once.

    Vectorized evaluation of :func:`compute_critical_head` across the rows
    of the theta matrix (spec section 6, shared preamble). Columns are
    extracted by name from the canonical parameter order, never by
    hard-coded position. Produces results identical to calling the scalar
    function row by row (for realizations with valid, positive H_c).

    Parameters
    ----------
    theta_matrix : ndarray, shape (N, 7)
        LHS sample matrix in the canonical column order
        ``['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']``
        (spec section 2), physical units as in
        :func:`compute_critical_head`.
    geometry : dict
        Cross-section geometry; only ``geometry['L']`` (seepage length
        [m]) is read here.
    alpha_exponent : float, optional
        Scale exponent alpha [-] (see :func:`compute_critical_head`).
    gamma_p_sub_kn_m3 : float, optional
        Deterministic submerged aquifer particle unit weight gamma'_p
        [kN/m^3] for F_r (default ``GAMMA_P_SUB_DEFAULT``, ADR-0016).
    theta_repose_rad : float, optional
        Bedding (repose) angle [rad] for F_r (see
        :func:`compute_critical_head`); default ``THETA_REPOSE_DEFAULT``.
    relative_density : float, optional
        In-situ relative density D_r [-] for F_r (see
        :func:`compute_critical_head`); default ``D_R_MEAN`` (ratio term 1).

    Returns
    -------
    SellmeijerResult
        Named tuple ``(H_c, l_c)`` of (N,)-shaped float64 arrays.

    Raises
    ------
    ValueError
        If any row of the H_c array is NaN, Inf or non-positive. The
        offending row indices and rate are logged at ERROR level before
        raising.

    Notes
    -----
    Same mathematical assumptions as :func:`compute_critical_head`. This
    is the production path for N = 1e5 fragility runs; the scalar variant
    exists for single-realization tracing and for the Phase 2 evaluator
    import path (M8). ``geometry['L']`` may be a scalar (deterministic
    seepage length) or an ``(N,)`` array (stochastic per-realization L, drawn
    independently of theta); every term broadcasts, so H_c and l_c become
    per-realization in L as well as in the theta columns. The whole output
    batch is validated before returning: an invalid row indicates a theta
    draw that escaped the sampler-stage prior clipping of spec section 12
    (failure mode 2), and aborts the run rather than propagating silently.
    The prescribed fix is prevention -- re-bound the priors in M2 -- not
    skipping here.
    """
    seepage_length_m = geometry["L"]
    k_aq_mps = theta_matrix[:, _PARAM_NAMES.index("k_aq")]
    d_70_m = theta_matrix[:, _PARAM_NAMES.index("d_70")]
    D_aq_m = theta_matrix[:, _PARAM_NAMES.index("D_aq")]

    h_c = (
        seepage_length_m
        * _factor_Fr(
            gamma_p_sub_kn_m3,
            theta_repose_rad=theta_repose_rad,
            relative_density=relative_density,
        )
        * _factor_Fs(d_70_m, k_aq_mps, seepage_length_m, alpha_exponent)
        * _factor_Fg(D_aq_m, seepage_length_m)
    )
    # isfinite & (> 0) in one mask: rejects NaN, +/-Inf and non-positive
    # rows alike (a bare "h_c <= 0" comparison would miss NaN and +Inf).
    invalid_rows = np.flatnonzero(~(np.isfinite(h_c) & (h_c > 0.0)))
    if invalid_rows.size > 0:
        logger.error(
            "Invalid critical head (NaN, Inf or <= 0) in %d of %d "
            "realizations (%.2f%%), row indices %s; re-bound the priors at "
            "the sampler stage (spec section 12, failure mode 2).",
            invalid_rows.size,
            h_c.size,
            100.0 * invalid_rows.size / h_c.size,
            invalid_rows,
        )
        raise ValueError(
            f"Invalid critical head (NaN, Inf or <= 0) in "
            f"{invalid_rows.size} of {h_c.size} realizations, row indices "
            f"{invalid_rows}; re-bound the priors at the sampler stage "
            "(spec section 12, failure mode 2)."
        )
    l_c = compute_critical_pipe_length(D_aq_m, seepage_length_m)
    return SellmeijerResult(H_c=h_c, l_c=l_c)


def compute_critical_pipe_length(
    D_aq: float | npt.NDArray[np.float64],
    L: float,
) -> float | npt.NDArray[np.float64]:
    """Critical pipe length l_c per Pol et al. (2024, SIE) Eq. (13).

    l_c = 0.5 * L * tanh(2 * D_aq / L)

    The pipe length at which the equilibrium curve H_eq(l) attains its
    maximum H_c; beyond l_c, progression is unstable under constant head.
    Anchors the (l_c, H_c) breakpoint of the piecewise-linear H_eq used by
    the progression ODE (M7, spec section 1).

    Parameters
    ----------
    D_aq : float or ndarray
        Aquifer (sand layer) thickness [m].
    L : float
        Seepage length across the structure [m].

    Returns
    -------
    float or ndarray
        Critical pipe length l_c [m], bounded by 0 < l_c < 0.5 * L.
        Broadcasts over ``D_aq``.

    Notes
    -----
    Valid for homogeneous aquifers, for which Pol et al. (2024, SIE)
    report good agreement with 2D numerical piping simulations
    (Sellmeijer 2006; Rosenbrand et al. 2022). The formula is smooth and
    cheap, and broadcasts through ``np.tanh`` unchanged, so no separate
    vectorized variant is needed.
    """
    return 0.5 * L * np.tanh(2.0 * D_aq / L)


if __name__ == "__main__":
    # Hand-checkable decomposition for IJkdijk test 1 (IJkfs01):
    # L = 15 m, D_aq = 3.00 m, d_70 = 180 um, k_aq = 8.0e-5 m/s,
    # gamma'_p = 14.715 kN/m^3 (Pol 2022 thesis, Appendix A, Table A.3;
    # Sellmeijer 2011 section 7). Observed H_c = 2.30 m; formula [6]
    # evaluates to ~2.07 m (-10%, inside the ~13% regression scatter).
    theta_ijkfs01 = np.array([8.0e-5, 180e-6, 3.00, 4.0, 1.0e-7, 14.715, 0.014])
    result = compute_critical_head(theta_ijkfs01, {"L": 15.0})
    print("IJkdijk test 1 (IJkfs01), L = 15.0 m")
    print(f"  F_r = {_factor_Fr(14.715):.6f}   (hand value 0.28258)")
    print(f"  F_s = {_factor_Fs(180e-6, 8.0e-5, 15.0):.6f}   (hand value 0.36235)")
    print(f"  F_g = {_factor_Fg(3.00, 15.0):.6f}   (hand value 1.3458)")
    print(f"  H_c = {result.H_c:.6f} m (= L*Fr*Fs*Fg; observed 2.30 m)")
    print(f"  l_c = {result.l_c:.6f} m (= 0.5*L*tanh(2*D_aq/L))")
