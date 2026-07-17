"""Faithful reproductions of Uemura's two surface-failure models (ADR-0042).

Quarantined **external** model physics: these are re-executions of the WP2
overflow (P1) and fluvial-scour (P2) failure-judgment models exactly as
published by Uemura — they import nothing from the BEP engine kernels and no
engine module imports them. Sources, equation for equation:

* **Overflow (P1)** — Uemura et al. (2024, Proc. IAHS 386) Eqs. (1)–(5),
  (10)–(13); thesis §4.2; the WP2 team's vectorized reference
  implementation (``count_failures`` in the 2021-11-19 notebook). Dean et
  al. (2010) cumulative-work criterion with threshold 0.492e6 for good
  grass cover; roughness f = 0.08; MC over the rating error, the per-KP
  crest error, and the turf critical velocity.
* **Fluvial scour (P2)** — ``ErosionModel_231019.py`` (Uemura, Oct 2023);
  WP2 final report (HKV PR3983) §5; USACE (2007) Erosion Toolbox
  excess-shear model. MC over the erodibility coefficient k and the
  critical shear stress tau_c (both normal, resampled to positive — his
  while-loops). Two deliberate script-over-report readings, documented in
  ADR-0042: Manning's velocity uses the SI form ``(1/n) R^(2/3) S^(1/2)``
  (the report prints the imperial 1.49/n factor; the script computes in
  SI), and the k unit conversion reproduces the script's
  ``0.3048/0.45359237`` factor verbatim (ADR-0042 decision 9 — ~106x the
  dimensionally-correct stress-based conversion, carried as a flagged
  finding with :data:`SCOUR_K_CONVERSION_USACE` as the corrected
  companion).

Both models are pointwise monotone in the driving stage series for fixed MC
draws, which is what makes the ADR-0042 common-random-numbers fragility
curves exactly non-decreasing.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "GRAVITY_MPS2",
    "OVERFLOW_FRICTION_F",
    "OVERFLOW_DAMAGE_THRESHOLD",
    "OVERFLOW_GRASS_UC_MPS",
    "OVERFLOW_GRASS_UC_SIGMA_MPS",
    "SCOUR_MANNING_N",
    "SCOUR_BED_ROUGHNESS_KB_M",
    "SCOUR_MIN_DEPTH_M",
    "SCOUR_K_MEAN_IMPERIAL",
    "SCOUR_K_COV",
    "SCOUR_TAU_C_MEAN_PSF",
    "SCOUR_TAU_C_COV",
    "SCOUR_K_CONVERSION_SCRIPT",
    "SCOUR_K_CONVERSION_USACE",
    "PSF_TO_PA",
    "SegmentSurfaceInputs",
    "load_segment_inputs",
    "OverflowDraws",
    "ScourDraws",
    "draw_overflow",
    "draw_scour",
    "overflow_failure_fraction",
    "scour_failure_fraction",
]

GRAVITY_MPS2 = 9.81

# --- Overflow (P1) constants: Uemura et al. (2024), Dean et al. (2010) ---
OVERFLOW_FRICTION_F = 0.08
OVERFLOW_DAMAGE_THRESHOLD = 0.492e6  # (m/s)^3 * s, good grass cover (Eq. 5)
OVERFLOW_GRASS_UC_MPS = 1.80  # paper Table 1, "good"
OVERFLOW_GRASS_UC_SIGMA_MPS = 0.38

# --- Scour (P2) constants: ErosionModel_231019.py / WP2 report Table 1 ---
SCOUR_MANNING_N = 0.030
SCOUR_BED_ROUGHNESS_KB_M = 0.157 * 0.3048  # ft -> m (= 0.04786 m)
SCOUR_K_MEAN_IMPERIAL = 0.021  # ft^3/(lb*hr) = ft/hr per psf
SCOUR_K_COV = 1.101  # the report table's "Variance" column is a CoV
SCOUR_TAU_C_MEAN_PSF = 1.058
SCOUR_TAU_C_COV = 0.560
PSF_TO_PA = 47.8803

# ADR-0042 decision 10: erosion contributes only at floodplain depths of at
# least this value. The USACE f_c log-law diverges at d = k_b/30 (~1.6 mm);
# below ~7 mm tau(d) is on the singular branch. At 0.05 m the shear is
# ~1 Pa (vs tau_c ~50 Pa), so the floor only removes the unphysical sliver.
SCOUR_MIN_DEPTH_M = 0.05

# k conversion factors (per hour, applied to tau in Pa). The script's factor
# is reproduced verbatim as primary (ADR-0042 decision 9); the USACE factor
# is the dimensionally correct ft/hr-per-psf -> m/hr-per-Pa conversion,
# used only by the flagged sensitivity companion.
SCOUR_K_CONVERSION_SCRIPT = 0.3048 / 0.45359237
SCOUR_K_CONVERSION_USACE = 0.3048 / PSF_TO_PA


@dataclass(frozen=True)
class SegmentSurfaceInputs:
    """Per-segment inputs for both surface models (ADR-0042 adapter output).

    All elevations in T.P. m MSL (the ADR-0021 datum; the adapter proved the
    rating identity). Fields mirror
    ``data/processed/uemura_segments/segment_inputs.csv``.
    """

    river: str
    bank: str
    kp: float
    crest_design_m_msl: float
    crest_err_mu_m: float
    crest_err_sigma_m: float
    ground_m_msl: float
    floodplain_m_msl: float
    crest_width_m: float
    slope_h_per_v: float
    water_surface_gradient_inv: float
    wl_err_mu_m: float
    wl_err_sigma_m: float

    @property
    def slope_angle_rad(self) -> float:
        """Levee slope angle alpha = arctan(1/n) for the n:1 slope."""
        return float(np.arctan(1.0 / self.slope_h_per_v))

    @property
    def water_surface_slope(self) -> float:
        """S = 1 / Gradient_WaterSurface (his script's convention)."""
        return 1.0 / self.water_surface_gradient_inv


def load_segment_inputs(
    path: str | Path,
) -> dict[tuple[str, float], SegmentSurfaceInputs]:
    """Read the committed segment-inputs CSV keyed by (river, kp)."""
    inputs: dict[tuple[str, float], SegmentSurfaceInputs] = {}
    with open(path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            seg = SegmentSurfaceInputs(
                river=row["river"],
                bank=row["bank"],
                kp=float(row["kp"]),
                crest_design_m_msl=float(row["crest_design_m_msl"]),
                crest_err_mu_m=float(row["crest_err_mu_m"]),
                crest_err_sigma_m=float(row["crest_err_sigma_m"]),
                ground_m_msl=float(row["ground_m_msl"]),
                floodplain_m_msl=float(row["floodplain_m_msl"]),
                crest_width_m=float(row["crest_width_m"]),
                slope_h_per_v=float(row["slope_h_per_v"]),
                water_surface_gradient_inv=float(row["water_surface_gradient_inv"]),
                wl_err_mu_m=float(row["wl_err_mu_m"]),
                wl_err_sigma_m=float(row["wl_err_sigma_m"]),
            )
            inputs[(seg.river, round(seg.kp, 3))] = seg
    if not inputs:
        raise ValueError(f"{path}: no segment inputs found.")
    return inputs


@dataclass(frozen=True)
class OverflowDraws:
    """One MC draw set for the overflow model (common across levels).

    ``wl_err_m``: rating-error draws N(mu_WL, sigma_WL) [m] (paper Eq. 10);
    ``crest_m_msl``: crest draws design + N(mu_DH, sigma_DH) [m MSL]
    (Eq. 12); ``u_c_mps``: turf critical velocity draws N(1.80, 0.38)
    (Eq. 13, no truncation — his implementation draws the plain normal).
    """

    wl_err_m: NDArray[np.float64]
    crest_m_msl: NDArray[np.float64]
    u_c_mps: NDArray[np.float64]


@dataclass(frozen=True)
class ScourDraws:
    """One MC draw set for the scour model (common across levels).

    ``k_si_per_hr_pa``: erodibility draws, already unit-converted (script
    factor by default); ``tau_c_pa``: critical shear draws [Pa]. Both are
    resampled-to-positive normals (his while-loops).
    """

    k_si_per_hr_pa: NDArray[np.float64]
    tau_c_pa: NDArray[np.float64]


def _positive_normal(
    rng: np.random.Generator, mean: float, sigma: float, n: int
) -> NDArray[np.float64]:
    """Normal draws resampled until positive (his rejection while-loop)."""
    out = rng.normal(mean, sigma, size=n)
    bad = out <= 0.0
    while np.any(bad):
        out[bad] = rng.normal(mean, sigma, size=int(bad.sum()))
        bad = out <= 0.0
    return out


def draw_overflow(
    rng: np.random.Generator, inputs: SegmentSurfaceInputs, n_mc: int
) -> OverflowDraws:
    """Draw the overflow MC set for one segment."""
    return OverflowDraws(
        wl_err_m=rng.normal(inputs.wl_err_mu_m, inputs.wl_err_sigma_m, size=n_mc),
        crest_m_msl=inputs.crest_design_m_msl
        + rng.normal(inputs.crest_err_mu_m, inputs.crest_err_sigma_m, size=n_mc),
        u_c_mps=rng.normal(
            OVERFLOW_GRASS_UC_MPS, OVERFLOW_GRASS_UC_SIGMA_MPS, size=n_mc
        ),
    )


def draw_scour(
    rng: np.random.Generator,
    n_mc: int,
    *,
    k_conversion: float = SCOUR_K_CONVERSION_SCRIPT,
) -> ScourDraws:
    """Draw the scour MC set (k and tau_c; segment-independent)."""
    k_imperial = _positive_normal(
        rng, SCOUR_K_MEAN_IMPERIAL, SCOUR_K_MEAN_IMPERIAL * SCOUR_K_COV, n_mc
    )
    tau_c_pa = _positive_normal(
        rng,
        SCOUR_TAU_C_MEAN_PSF * PSF_TO_PA,
        SCOUR_TAU_C_COV * SCOUR_TAU_C_MEAN_PSF * PSF_TO_PA,
        n_mc,
    )
    return ScourDraws(k_si_per_hr_pa=k_imperial * k_conversion, tau_c_pa=tau_c_pa)


def overflow_failure_fraction(
    stage_m_msl: NDArray[np.float64],
    dt_seconds: float,
    inputs: SegmentSurfaceInputs,
    draws: OverflowDraws,
) -> float:
    """Fraction of MC draws in which the overflow model declares dike failure.

    Vectorized transcription of the WP2 ``count_failures`` reference
    implementation (which itself transcribes paper Eqs. (1)–(5)):

    1. per-draw water level series ``wl(t) = h(t) + wl_err`` (Eq. 10),
    2. crest-exceedance depth ``d = max(wl - crest, 0)``,
    3. overtopping discharge ``q = sqrt(g d) * d`` (Eqs. 1–2),
    4. landside-slope terminal velocity
       ``u = (8 g q sin(alpha) / f)^(1/3)`` (Eq. 3),
    5. cumulative work ``D = sum(max(u^3 - u_c^3, 0)) * dt`` (Eq. 4),
    6. failure iff ``D > 0.492e6`` (Eq. 5).

    Parameters
    ----------
    stage_m_msl : numpy.ndarray, shape (T,)
        The conditioning stage series h(t) [m MSL] (median-rating stage —
        the ADR-0042 decision 2 axis).
    dt_seconds : float
        Series time step [s].
    inputs : SegmentSurfaceInputs
        The segment's committed inputs.
    draws : OverflowDraws
        The MC draw set (shared across levels for monotonicity).

    Returns
    -------
    float
        n_failure / n_mc.
    """
    h = np.asarray(stage_m_msl, dtype=np.float64)
    wl = h[:, None] + draws.wl_err_m[None, :]  # (T, N)
    depth = np.maximum(wl - draws.crest_m_msl[None, :], 0.0)
    q_ov = np.sqrt(GRAVITY_MPS2 * depth) * depth
    v_toe = (
        8.0 * GRAVITY_MPS2 * q_ov * np.sin(inputs.slope_angle_rad) / OVERFLOW_FRICTION_F
    ) ** (1.0 / 3.0)
    damage = (
        np.sum(np.maximum(0.0, v_toe**3 - draws.u_c_mps[None, :] ** 3), axis=0)
        * dt_seconds
    )
    return float(np.mean(damage > OVERFLOW_DAMAGE_THRESHOLD))


def scour_failure_fraction(
    stage_m_msl: NDArray[np.float64],
    dt_seconds: float,
    inputs: SegmentSurfaceInputs,
    draws: ScourDraws,
) -> float:
    """Fraction of MC draws in which the scour model declares dike failure.

    Vectorized transcription of ``ErosionModel_231019.py``:

    1. floodplain water depth ``d = clip(h - z_fp, 0, z_crest - z_fp)``,
    2. Manning velocity ``v = (1/n) d^(2/3) S^(1/2)`` (SI form — the
       script's computation; the report prints the imperial constant),
    3. friction ``f_c = 2 (2.5 ln(30 d / k_b))^(-2)`` (USACE), shear
       ``tau = 0.5 rho f_c v^2``,
    4. per-step erosion ``k (tau - tau_c)+ * (dt/3600)`` [m], zero while
       the floodplain depth is below the ADR-0042 decision-10 floor
       (``h < z_fp + SCOUR_MIN_DEPTH_M``), accumulated over time,
    5. effective levee width ``w(t) = w_crest + (z_crest - h(t)) * n``
       (floor ``w_crest`` during overtopping),
    6. failure iff cumulative erosion exceeds ``w(t)`` at any time with
       ``h(t) > z_ground`` (his ``-999`` mask: breach can only be declared
       while the landside ground in the embankment is loaded).

    Parameters and return as :func:`overflow_failure_fraction`. The stage
    series enters deterministically (his scour MC randomizes only k and
    tau_c — no rating-error or crest term, WP2 §5.3).
    """
    h = np.asarray(stage_m_msl, dtype=np.float64)
    z_crest = inputs.crest_design_m_msl
    z_fp = inputs.floodplain_m_msl

    depth = np.clip(h - z_fp, 0.0, z_crest - z_fp)  # (T,)
    velocity = (
        (1.0 / SCOUR_MANNING_N) * depth ** (2.0 / 3.0) * inputs.water_surface_slope**0.5
    )
    with np.errstate(divide="ignore"):
        log_term = np.log(30.0 * depth / SCOUR_BED_ROUGHNESS_KB_M)
    f_c = np.where(depth > 0.0, 2.0 * (2.5 * log_term) ** (-2.0), 0.0)
    tau_pa = 0.5 * 1000.0 * f_c * velocity**2  # (T,)

    excess = np.maximum(0.0, tau_pa[:, None] - draws.tau_c_pa[None, :])  # (T, N)
    # His mask1 (no erosion below the floodplain), extended by the ADR-0042
    # decision-10 depth floor that removes the f_c log-law singularity.
    excess[h < z_fp + SCOUR_MIN_DEPTH_M, :] = 0.0
    erosion = np.cumsum(
        draws.k_si_per_hr_pa[None, :] * excess * (dt_seconds / 3600.0), axis=0
    )

    width = np.where(
        h > z_crest,
        inputs.crest_width_m,
        inputs.crest_width_m + (z_crest - h) * inputs.slope_h_per_v,
    )  # (T,)
    margin = erosion - width[:, None]
    margin[h < inputs.ground_m_msl, :] = -np.inf  # his mask3 (-999)
    return float(np.mean(np.max(margin, axis=0) > 0.0))
