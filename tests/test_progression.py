"""Tests for M7 progression (``bep_reliability_engine.progression``).

Executable contract for the M7 interface, written before the implementation
(same pattern as M5): every physics test is expected to fail with
``NotImplementedError`` until ``progression.py`` is filled in. The interface
test at the bottom passes already and must keep passing.

Every reference number traces to the physics note
``docs/decisions/m7-pol-ode-reference-values.md`` (sections cited per test)
and through it to Pol SIE 2024 / CG24 / the 2022 thesis. Digitized figure
data come from ``data/digitized/`` (note §5C: <= 2 significant figures,
clean curve-crossing artifacts before use).

Expensive reference-reproduction and convergence tests are marked ``slow``
(registered in pyproject.toml); run the cheap unit tests alone with
``pytest -m "not slow"``.
"""

import inspect
from pathlib import Path

import numpy as np
import pytest

from bep_reliability_engine import progression
from bep_reliability_engine.constants import GAMMA_W
from bep_reliability_engine.hydraulics import InstantaneousHead
from bep_reliability_engine.progression import (
    CRACK_RESISTANCE_FACTOR,
    EQUILIBRIUM_END_FACTOR,
    POL_RATE_COEFFICIENT,
    POL_RATE_EXPONENT,
    ProgressionResult,
    equilibrium_head,
    integrate_progression,
    progression_rate,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "digitized"

# (H_c [m], l_c [m], L [m]) triples. The first two are traced reference
# geometries; the third is a SYNTHETIC field-scale fixture (illustrative
# inputs, not a Pol reference). equilibrium_head is pure algebra, so this case
# only checks the interpolation holds at a third, field-relevant scale.
#   B25-245: H_c,corr = 0.054 m, l_c = 0.197 m (thesis Table 3.2, note §4);
#       L = 0.352 m (§3.2.1).
#   CG24 L = 3 m: H_c = 0.143 m caption text (note §5C / §5B.9); l_c = 0.874 m
#       = 0.5*tanh(2/3)*3, i.e. Eq. (13) at D/L = 1/3 (note §5A.3).
#   field-scale: (2.0, 16.6, 50.0) synthetic, not from any source.
EQ_CURVE_CASES = [
    pytest.param(0.054, 0.197, 0.352, id="B25-245-measured"),
    pytest.param(0.143, 0.874, 3.0, id="CG24-L3m"),
    pytest.param(2.0, 16.6, 50.0, id="field-scale-synthetic"),
]


def _load_csv(name: str) -> np.ndarray:
    """Load a two-column digitized CSV from data/digitized (note §5C)."""
    return np.loadtxt(DATA_DIR / name, delimiter=",", skiprows=1)


# ---------------------------------------------------------------------------
# (1) Equilibrium curve H_eq(l): anchors and segment midpoints (note §2, §5A.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("h_c, l_c, length", EQ_CURVE_CASES)
def test_equilibrium_head_anchors_and_midpoints(
    h_c: float, l_c: float, length: float
) -> None:
    """H_eq through (0, 0), (l_c, H_c), (L, 0.9*H_c), linear in between.

    Pol SIE 2024 Eq. (11) / thesis Eq. (6.10). Midpoint values are exact
    consequences of linearity: H_eq(l_c/2) = H_c/2 on the rising segment
    and H_eq((l_c + L)/2) = 0.95*H_c on the falling segment.
    """
    assert float(equilibrium_head(0.0, h_c, l_c, length)) == pytest.approx(
        0.0, abs=1e-15
    )
    assert float(equilibrium_head(l_c / 2.0, h_c, l_c, length)) == pytest.approx(
        0.5 * h_c, rel=1e-12
    )
    assert float(equilibrium_head(l_c, h_c, l_c, length)) == pytest.approx(
        h_c, rel=1e-12
    )
    assert float(
        equilibrium_head((l_c + length) / 2.0, h_c, l_c, length)
    ) == pytest.approx(0.95 * h_c, rel=1e-12)
    assert float(equilibrium_head(length, h_c, l_c, length)) == pytest.approx(
        EQUILIBRIUM_END_FACTOR * h_c, rel=1e-12
    )


def test_equilibrium_head_per_realization_breakpoints_vectorized() -> None:
    """(N,) arrays of (H_c, l_c) with per-realization breakpoints (spec §6).

    Breakpoints differ per realization, so the kernel must broadcast; the
    vectorized result must equal N scalar evaluations.
    """
    rng = np.random.default_rng(58)  # deterministic seed (conventions)
    length = 50.0
    h_c = rng.uniform(1.0, 4.0, 32)
    l_c = rng.uniform(5.0, 20.0, 32)
    pipe_length = rng.uniform(0.0, length, 32)

    vec = equilibrium_head(pipe_length, h_c, l_c, length)
    assert vec.shape == (32,)
    scalar = [
        float(equilibrium_head(pipe_length[i], h_c[i], l_c[i], length))
        for i in range(32)
    ]
    np.testing.assert_allclose(vec, scalar, rtol=1e-14)


# ---------------------------------------------------------------------------
# (2) Rate kernel: threshold, monotonicity, pinned coefficients (note §1, §5A)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deficit_m", [0.0, 0.01, 1.0], ids=["at", "below", "far"])
def test_progression_rate_zero_at_and_below_equilibrium(deficit_m: float) -> None:
    """dl/dt is exactly 0 for H_erosion <= H_eq (positive-part threshold).

    "A threshold below which no erosion occurs as the grains in the pipe
    are in equilibrium" (SIE 2024 §2.1; note §1).
    """
    h_eq = 1.5
    rate = progression_rate(h_eq - deficit_m, h_eq, 0.014, 1e-4, 50.0)
    assert float(rate) == 0.0


def test_progression_rate_monotonic_in_erosion_head_at_fixed_length() -> None:
    """dl/dt strictly increases with H_erosion at fixed l (fixed H_eq)."""
    h_eq = 1.5
    h_erosion = h_eq + np.linspace(1e-3, 2.0, 50)
    rates = progression_rate(h_erosion, h_eq, 0.014, 1e-4, 50.0)
    assert rates.shape == (50,)
    assert np.all(rates > 0.0)
    assert np.all(np.diff(rates) > 0.0)


def test_progression_rate_pinned_worked_value() -> None:
    """Coefficient/exponent transcription guard (note §5A.1, derived value).

    89 * 0.08 * (2.158e-4 * 0.0144 / 3)**0.81 = 1.0113e-4 m/s, precomputed
    in the physics note for S2-2-like inputs. Catches 89/0.81 typos without
    re-deriving the formula in the test.
    """
    rate = progression_rate(0.0144, 0.0, 0.08, 2.158e-4, 3.0)
    assert float(rate) == pytest.approx(1.0113e-4, rel=1e-3)


def test_progression_rate_exactly_linear_in_c_e() -> None:
    """dl/dt is exactly proportional to C_e (note §5A.5)."""
    base = progression_rate(0.5, 0.1, 0.014, 3e-4, 50.0)
    doubled = progression_rate(0.5, 0.1, 0.028, 3e-4, 50.0)
    assert float(doubled) == pytest.approx(2.0 * float(base), rel=1e-12)


# ---------------------------------------------------------------------------
# (3) Head-datum consistency (note §3, §5A.4; ADR-0007)
# ---------------------------------------------------------------------------

# Nonzero datum so a datum error cannot cancel: z_toe = h_e = 2.0 m.
DATUM_Z_TOE_M = 2.0
DATUM_D_BL_M = 1.0
DATUM_GAMMA_BL_SUB = 10.0
# Uplift = heave threshold overpressure (ADR-0008 collapse):
# gamma'_bl * D_bl / gamma_w = 10/9.81 = 1.0194 m.
DATUM_THRESHOLD_M = DATUM_GAMMA_BL_SUB * DATUM_D_BL_M / GAMMA_W


def _one_step(delta_h_blanket_m: float) -> ProgressionResult:
    """Run a single dt = 60 s step at constant overpressure, r_e = 1."""
    h_river = np.array([DATUM_Z_TOE_M + delta_h_blanket_m])
    return integrate_progression(
        h_river,
        60.0,
        InstantaneousHead(1.0, DATUM_Z_TOE_M),
        DATUM_Z_TOE_M,
        c_e=0.014,
        k_aq_mps=1e-4,
        d_bl_m=DATUM_D_BL_M,
        gamma_bl_sub_knpm3=DATUM_GAMMA_BL_SUB,
        h_c_m=5.0,
        l_c_m=10.0,
        seepage_length_m=50.0,
    )


def test_head_datum_growth_driven_by_crack_reduced_head() -> None:
    """One Euler step equals dt * rate(h - h_e - 0.3*D_bl) exactly.

    Datum: all heads in excess of the polder surface level at the landside
    exit point (h_e = z_toe), per Pol SIE 2024 Eqs. (6), (8), (10) and
    ADR-0007. With r_e = 1 the repo convention coincides with Eq. (6)
    verbatim (note §3), so the growth over one step from l = 0 (where
    H_eq = 0) must equal dt * progression_rate(H - 0.3*D_bl). The
    overpressure 1.2 m is chosen INSIDE the window
    (threshold, threshold + 0.3*D_bl) = (1.0194, 1.3194): the gate is open
    on the un-reduced head but would be closed on the crack-reduced head,
    so this single assertion kills both head-mixing errors of spec §5 at
    once (reduced head in the gate, or un-reduced head in the rate).
    """
    delta_h = 1.2
    assert DATUM_THRESHOLD_M < delta_h < DATUM_THRESHOLD_M + 0.3 * DATUM_D_BL_M

    result = _one_step(delta_h)
    h_erosion = delta_h - CRACK_RESISTANCE_FACTOR * DATUM_D_BL_M
    expected = 60.0 * float(progression_rate(h_erosion, 0.0, 0.014, 1e-4, 50.0))
    assert expected > 0.0
    assert float(result.l_final_m) == pytest.approx(expected, rel=1e-12)
    assert bool(result.uplift_occurred)
    assert bool(result.heave_occurred)
    assert float(result.t_uh_s) == 0.0


def test_head_datum_gate_uses_unreduced_overpressure() -> None:
    """Just below the un-reduced threshold the gate stays closed.

    Delta_h_blanket = 1.0 m < 1.0194 m: no uplift, no heave, I_er False --
    even though H_erosion = 0.7 m exceeds H_eq(0) = 0. Pins that the gate
    acts on the full overpressure with the correct threshold (spec §3
    steps d, g; note §3: the 0.3*D_bl term never enters Eqs. (8)-(9)).
    """
    result = _one_step(1.0)
    assert float(result.l_final_m) == 0.0
    assert not bool(result.uplift_occurred)
    assert not bool(result.heave_occurred)
    assert np.isnan(float(result.t_uh_s))


def test_erosion_head_uses_raw_outer_level_not_re_attenuated() -> None:
    """At r_e < 1 the rate is driven by the RAW outer level, not r_e*head.

    Pol SIE 2024 Eq. (6) defines the erosion-driving head as
    ``H = h - h_e - 0.3*D_bl`` on the RAW outer water level h, with r_e
    applied ONLY to the uplift/heave head (Eq. (10)). Physically, once heave
    ruptures the blanket the exit is unfiltered, so the full head drives
    progression (ADR-0027, superseding ADR-0007). This is the discriminating
    case the r_e = 1 head-datum tests cannot see: with r_e = 0.6 the raw and
    r_e-attenuated erosion heads differ, so one Euler step from l = 0
    (H_eq = 0) must equal ``dt * rate(raw - 0.3*D_bl)``, strictly larger than
    the retired ``dt * rate(r_e*head - 0.3*D_bl)``.
    """
    r_e = 0.6
    h_minus_toe = 3.0
    attenuated = r_e * h_minus_toe
    # Gate opens on the attenuated head (Eq. 10), so growth is non-zero and
    # the discriminator is the rate head, not the gate.
    assert attenuated > DATUM_THRESHOLD_M

    result = integrate_progression(
        np.array([DATUM_Z_TOE_M + h_minus_toe]),
        60.0,
        InstantaneousHead(r_e, DATUM_Z_TOE_M),
        DATUM_Z_TOE_M,
        c_e=0.014,
        k_aq_mps=1e-4,
        d_bl_m=DATUM_D_BL_M,
        gamma_bl_sub_knpm3=DATUM_GAMMA_BL_SUB,
        h_c_m=5.0,
        l_c_m=10.0,
        seepage_length_m=50.0,
    )

    h_erosion_raw = h_minus_toe - CRACK_RESISTANCE_FACTOR * DATUM_D_BL_M
    expected_raw = 60.0 * float(progression_rate(h_erosion_raw, 0.0, 0.014, 1e-4, 50.0))
    h_erosion_attenuated = attenuated - CRACK_RESISTANCE_FACTOR * DATUM_D_BL_M
    retired_attenuated = 60.0 * float(
        progression_rate(h_erosion_attenuated, 0.0, 0.014, 1e-4, 50.0)
    )
    # The two conventions are genuinely distinguishable here.
    assert expected_raw > retired_attenuated > 0.0
    assert float(result.l_final_m) == pytest.approx(expected_raw, rel=1e-12)
    assert bool(result.heave_occurred)


def test_gate_still_uses_re_attenuated_head_not_raw() -> None:
    """The uplift/heave gate keeps r_e (Eq. 10) even after the rate drops it.

    Companion to the test above: with r_e = 0.3 the raw overpressure (3.0 m)
    clears the heave threshold but the r_e-attenuated head (0.9 m) does not,
    so the gate must stay closed and no erosion occurs. Pins that ADR-0027
    removes r_e from the rate head (Eq. 6) ONLY -- the uplift/heave head
    (Eq. 10) remains r_e-attenuated.
    """
    r_e = 0.3
    h_minus_toe = 3.0
    assert r_e * h_minus_toe < DATUM_THRESHOLD_M < h_minus_toe

    result = integrate_progression(
        np.array([DATUM_Z_TOE_M + h_minus_toe]),
        60.0,
        InstantaneousHead(r_e, DATUM_Z_TOE_M),
        DATUM_Z_TOE_M,
        c_e=0.014,
        k_aq_mps=1e-4,
        d_bl_m=DATUM_D_BL_M,
        gamma_bl_sub_knpm3=DATUM_GAMMA_BL_SUB,
        h_c_m=5.0,
        l_c_m=10.0,
        seepage_length_m=50.0,
    )
    assert float(result.l_final_m) == 0.0
    assert not bool(result.heave_occurred)


# ---------------------------------------------------------------------------
# (4) Synthetic two-peak compound event (spec §3 step 8i, §5; ADR-0008)
# ---------------------------------------------------------------------------

# Blanket with threshold overpressure 10*2/9.81 = 2.039 m; peaks at 3.0 m
# clear it, the 1.0 m trough and the 1.5 m dead second peak do not.
TWO_PEAK_D_BL = 2.0
TWO_PEAK_GAMMA = 10.0
TWO_PEAK_STEPS = 30


def _two_peak_event(second_peak_m: float) -> ProgressionResult:
    """30 steps at h = 3.0, 30 at h = 1.0, 30 at h = second_peak (r_e = 1)."""
    h_river = np.concatenate(
        [
            np.full(TWO_PEAK_STEPS, 3.0),
            np.full(TWO_PEAK_STEPS, 1.0),
            np.full(TWO_PEAK_STEPS, second_peak_m),
        ]
    )
    return integrate_progression(
        h_river,
        600.0,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=0.014,
        k_aq_mps=1e-4,
        d_bl_m=TWO_PEAK_D_BL,
        gamma_bl_sub_knpm3=TWO_PEAK_GAMMA,
        h_c_m=5.0,
        l_c_m=10.0,
        seepage_length_m=50.0,
        store_trajectory=True,
    )


def test_two_peak_growth_plateau_and_resumption() -> None:
    """Growth on peak 1, exactly flat trough, resumption on peak 2.

    The memory model (spec §5): l carries across peaks with no reset; the
    trough (overpressure 1.0 < 2.039 m threshold) switches I_er off and the
    trajectory is a flat staircase segment -- bitwise constant, not merely
    slowly growing. Peak 2 reactivates heave and growth resumes without any
    re-initialization: within one event the uplift latch stays set through the
    trough, so I_er = (uplift_ever | l>0) & heave_now switches back on the
    instant heave returns. (The l>0 clause is the cross-event analogue of that
    latch; within this single event both are already True, which is why the
    companion dead-peak test below is what proves heave is the binding
    condition for resumption.)
    """
    result = _two_peak_event(3.0)
    trajectory = result.l_trajectory_m
    assert trajectory is not None and trajectory.shape == (3 * TWO_PEAK_STEPS,)

    peak1 = trajectory[:TWO_PEAK_STEPS]
    trough = trajectory[TWO_PEAK_STEPS : 2 * TWO_PEAK_STEPS]
    peak2 = trajectory[2 * TWO_PEAK_STEPS :]

    assert np.all(np.diff(peak1) > 0.0), "no growth during first peak"
    assert np.all(trough == peak1[-1]), "trough plateau is not exactly flat"
    assert np.all(np.diff(peak2) > 0.0), "no resumption on second peak"
    assert float(result.l_final_m) > float(peak1[-1])
    assert float(result.t_uh_s) == 0.0  # gate opens at the first sample


def test_two_peak_no_growth_when_heave_does_not_reactivate() -> None:
    """A second peak below the heave threshold produces no further growth.

    With the dead second peak at 1.5 m (< 2.039 m threshold) heave never
    reactivates after the trough, so l stays exactly at its end-of-peak-1
    value: I_er never returns True and dl/dt stays 0 (spec §3 step 8i).
    """
    result = _two_peak_event(1.5)
    trajectory = result.l_trajectory_m
    assert trajectory is not None

    end_of_peak1 = trajectory[TWO_PEAK_STEPS - 1]
    assert end_of_peak1 > 0.0
    assert np.all(trajectory[TWO_PEAK_STEPS:] == end_of_peak1)
    assert float(result.l_final_m) == float(end_of_peak1)


# ---------------------------------------------------------------------------
# (5) Structural invariants: monotonicity and the l_e <= L bound (spec §11.4)
# ---------------------------------------------------------------------------


def test_monotone_nondecreasing_and_bounded_by_seepage_length() -> None:
    """l never decreases at any step and never exceeds L, across N realizations.

    Spec §11 validation test 4, run on a rough multi-peak hydrograph with a
    wide spread of theta values (including high-rate corners that breach,
    so the clip at L is exercised) and mixed l_ini (including pre-existing
    pipes, which bypass the uplift gate via the l > 0 clause).
    """
    rng = np.random.default_rng(2016)  # deterministic seed (conventions)
    n_real, n_steps, length = 64, 200, 50.0

    t = np.arange(n_steps)
    h_river = 3.0 + 2.5 * np.sin(2.0 * np.pi * t / 80.0) + rng.normal(0.0, 0.3, n_steps)

    r_e = rng.uniform(0.2, 0.9, n_real)
    result = integrate_progression(
        h_river,
        600.0,
        InstantaneousHead(r_e, 0.0),
        0.0,
        c_e=rng.lognormal(np.log(0.014), 0.5, n_real),
        k_aq_mps=rng.lognormal(np.log(3e-4), 0.7, n_real),
        d_bl_m=rng.lognormal(np.log(1.5), 0.3, n_real),
        gamma_bl_sub_knpm3=rng.normal(10.0, 0.5, n_real),
        h_c_m=rng.uniform(0.5, 3.0, n_real),
        l_c_m=rng.uniform(5.0, 20.0, n_real),
        seepage_length_m=length,
        l_ini_m=np.where(rng.random(n_real) < 0.5, 0.0, rng.uniform(0.0, 10.0, n_real)),
        store_trajectory=True,
    )

    trajectory = result.l_trajectory_m
    assert trajectory is not None and trajectory.shape == (n_steps, n_real)
    assert np.all(np.diff(trajectory, axis=0) >= 0.0), "pipe length decreased"
    assert np.all(trajectory <= length + 1e-12), "pipe length exceeded L"
    assert np.all(result.l_final_m == trajectory[-1])


# ---------------------------------------------------------------------------
# (6) Degenerate limits (spec §11.5)
# ---------------------------------------------------------------------------


def test_vanishing_c_e_freezes_pipe_regardless_of_hydrograph() -> None:
    """C_e = 0 yields l_e = l_ini exactly, under strong sustained forcing.

    Spec §11 smoke test 5: Z_trans -> L - l_ini as C_e -> 0. Vectorized
    [0, 0.014] so the same call also shows the nonzero-C_e companion grows.
    """
    h_river = np.full(50, 5.0)
    result = integrate_progression(
        h_river,
        600.0,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=np.array([0.0, 0.014]),
        k_aq_mps=3e-4,
        d_bl_m=1.0,
        gamma_bl_sub_knpm3=10.0,
        h_c_m=2.0,
        l_c_m=10.0,
        seepage_length_m=50.0,
    )
    assert float(result.l_final_m[0]) == 0.0
    assert float(result.l_final_m[1]) > 0.0


def test_vanishing_k_aq_freezes_pipe_regardless_of_hydrograph() -> None:
    """k_aq = 0 yields zero seepage velocity and hence l_e = l_ini exactly."""
    h_river = np.full(50, 5.0)
    result = integrate_progression(
        h_river,
        600.0,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=0.014,
        k_aq_mps=np.array([0.0, 3e-4]),
        d_bl_m=1.0,
        gamma_bl_sub_knpm3=10.0,
        h_c_m=2.0,
        l_c_m=10.0,
        seepage_length_m=50.0,
    )
    assert float(result.l_final_m[0]) == 0.0
    assert float(result.l_final_m[1]) > 0.0


# ---------------------------------------------------------------------------
# (7) B25-245 QUALITATIVE shape-and-behavior gate (slow; spec §11.2; note §4).
#     B25-245 (L = 0.352 m) is OUT OF DOMAIN for the Eq. (5) regression (fitted
#     L = 0.9-90 m), so its absolute rate is NOT gated here -- the quantitative
#     rate-band gate lives on an in-domain case. See note §4/§5/§6 for the split
#     and the decisive 0.014-passes / 0.010-fails reasoning.
# ---------------------------------------------------------------------------

# Verified B25-245 anchors, thesis Table 3.2 / §3.2.1 (note §4).
B25_L_M = 0.352  # seepage length L, §3.2.1
B25_K_MPS = 3.1e-4  # hydraulic conductivity k, Table 3.2
B25_H_C_M = 0.054  # corrected critical head H_c,corr, Table 3.2
B25_L_C_M = 0.197  # measured critical pipe length l_c, Table 3.2 (l_c/L = 0.56);
# anchored on the MEASURED value, not the tanh Eq. (13) 0.092 m (l_c/L = 0.26,
# factor ~2.2 off), to isolate the rate law from the l_c formula (note §4, §6).
B25_C_E = 0.010  # calibrated C_e, [CG24] Table 1 / [T22] Table 5.1. Pol
# confirmed 0.010 in writing (email 2026-07-08): the Fig. 5 / 5.5 caption's
# 0.014 is the error (an FPH-caption copy-paste). FPH itself uses 0.014.

# Breach threshold for THIS box brackets the true transition C_e ~= 0.0215: at
# the calibrated C_e = 0.010 the box does not breach; it first breaches near
# 0.0215. Pinned two-sided as a sharp rate-law regression guard -- it fixes the
# rate magnitude at this scale WITHOUT an (out-of-domain) absolute-rate band.
B25_CE_NO_BREACH = 0.020  # l_final = 0.334 m < L (does not breach)
B25_CE_BREACH = 0.022  # l_final = L (breaches)

# Calibrated small-scale C_e range (0.007-0.030, note §4) for the
# rate-monotonicity property check: dl/dt is linear in C_e, so the
# post-critical rate must strictly increase along this row.
B25_CE_ROW = (0.007, 0.010, 0.014, 0.018, 0.024, 0.030)

# Shape envelopes vs the digitized measured curve (fractions of L). Only what
# survives out of domain is gated: the model must not OVERSHOOT the measured
# curve (a too-fast rate law would), and must TRACK it through the regressive
# phase. The progressive-phase absolute divergence (up to ~0.34*L; the model
# under-predicts and does not breach at C_e = 0.010) is deliberately NOT gated.
B25_OVERSHOOT_MAX_FRAC = 0.15  # measured max overshoot 0.10*L
B25_REGRESSIVE_ENVELOPE_FRAC = 0.18  # measured regressive max dev 0.14*L


def _b25_245_replay(
    c_e: float, store_trajectory: bool = True
) -> tuple[np.ndarray, ProgressionResult]:
    """Replay B25-245 at a given C_e with the cleaned digitized head BC.

    Configuration (note §5C): the digitized H_corr(t) is already the
    loss-corrected head difference over the sample, so r_e = 1, z_toe = 0, and
    d_bl_m = 0 selects the no-blanket laboratory convention (no 0.3*D_bl crack
    term; gate open at any positive overpressure). H_eq is anchored on the
    MEASURED (H_c,corr, l_c) = (0.054, 0.197) m. Cleaning: the single run of
    samples at 0.021-0.022 m around t = 1554-1740 s is a curve-crossing
    digitization artifact; after t = 1000 s the true BC never drops below
    ~0.03 m, so H < 0.03 m at t > 1000 s is dropped before interpolation to a
    uniform 5 s grid.
    """
    raw = _load_csv("B25-245_head-BC_Hcorr.csv")
    t_raw, h_raw = raw[:, 0], raw[:, 1]
    keep = ~((t_raw > 1000.0) & (h_raw < 0.03))
    dt_s = 5.0
    t_grid = np.arange(0.0, t_raw[-1] + dt_s, dt_s)
    h_grid = np.interp(t_grid, t_raw[keep], h_raw[keep])
    result = integrate_progression(
        h_grid,
        dt_s,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=c_e,
        k_aq_mps=B25_K_MPS,
        d_bl_m=0.0,  # no-blanket laboratory configuration
        gamma_bl_sub_knpm3=9.7,  # inert at D_bl = 0
        h_c_m=B25_H_C_M,
        l_c_m=B25_L_C_M,
        seepage_length_m=B25_L_M,
        store_trajectory=store_trajectory,
    )
    return t_grid, result


def _b25_post_critical_rate(t_grid: np.ndarray, trajectory: np.ndarray) -> float | None:
    """End-to-end post-critical rate (l_end - l_c)/(t_end - t_c) [m/s].

    Pol's v_c,avg definition (thesis §3.3.3); None if l_c is never reached.
    Used here only for the C_e-monotonicity property check, NOT as an
    absolute-rate gate (B25-245 is out of domain; note §4).
    """
    if float(trajectory.max()) <= B25_L_C_M:
        return None
    t_c = t_grid[int(np.argmax(trajectory >= B25_L_C_M))]
    growth_steps = np.flatnonzero(np.diff(trajectory) > 0.0)
    last = int(growth_steps[-1]) + 1
    if t_grid[last] <= t_c:
        return None
    return (float(trajectory[last]) - B25_L_C_M) / (t_grid[last] - t_c)


@pytest.mark.slow
def test_b25_245_qualitative_shape_and_behavior() -> None:
    """B25-245 replay: a DEMANDING qualitative gate; absolute rate NOT gated.

    B25-245 (L = 0.352 m) lies BELOW the Eq. (5) regression's fitted scale
    range (0.9-90 m), so the absolute post-critical rate is out of domain and
    deliberately not asserted: at the calibrated C_e = 0.010 our replay reaches
    only 0.36x the measured v_c,avg, and even Pol's own calibrated DgFlow
    reaches only 0.51x on this box (note §4). The decisive point: the
    caption-error C_e = 0.014 would land inside a factor-2 band while the
    correct calibrated 0.010 falls below it, so any band wide enough to pass
    0.010 would be drawn around our own output, not Pol's data -- which
    disqualifies B25-245 as a quantitative rate gate. The quantitative
    rate-band gate lives on an in-domain case instead (note §5).

    Five demanding assertions, none depending on the out-of-domain absolute
    rate:

    1. Entry into the progressive phase: l crosses the measured l_c.
    2. Strict monotone non-decrease (positive-part operator) with a visible
       staircase -- both flat (trough) and growing (peak) steps present.
    3. Shape vs the digitized measured curve (note §5C), restricted to what
       survives out of domain: the replay never OVERSHOOTS the measured curve
       by more than 0.15*L (a too-fast rate law would), and TRACKS it within
       0.18*L through the regressive phase. The progressive-phase absolute
       divergence (up to ~0.34*L) is NOT gated: the model under-predicts and
       stalls near 0.23 m, its front-loading (0.84 vs the measured 0.55)
       reflecting the out-of-domain suppression of the progressive phase.
    4. Breach threshold for this box pinned two-sided as a rate-law guard: no
       breach at C_e = 0.020, breach at C_e = 0.022 (true transition ~0.0215).
       Catches a future rate-law magnitude change with no absolute band.
    5. Post-critical rate strictly increasing along the calibrated C_e row
       (dl/dt is linear in C_e) -- a property check needing no absolute target.
    """
    t_grid, result = _b25_245_replay(B25_C_E)
    trajectory = result.l_trajectory_m
    assert trajectory is not None

    # 1. Entry into the progressive phase.
    assert float(trajectory.max()) > B25_L_C_M, "replay never reached l_c"

    # 2. Strict monotone non-decrease + staircase (positive-part operator).
    diffs = np.diff(trajectory)
    assert np.all(diffs >= 0.0), "pipe length decreased"
    assert np.any(diffs > 0.0), "no growth steps at all"
    assert np.any(diffs == 0.0), "no flat (trough) steps -- staircase absent"

    # 3. Shape vs the digitized measured curve, restricted to the parts that
    #    survive out of domain (no overshoot; regressive-phase tracking).
    l_exp = _load_csv("B25-245_pipelength_l-exp.csv")
    our_at_exp = np.interp(l_exp[:, 0], t_grid, trajectory)
    overshoot = our_at_exp - l_exp[:, 1]
    assert overshoot.max() <= B25_OVERSHOOT_MAX_FRAC * B25_L_M, (
        f"replay overshoots the measured curve by {overshoot.max() / B25_L_M:.2f}"
        f"*L (> {B25_OVERSHOOT_MAX_FRAC}*L): rate law too fast"
    )
    t_c = t_grid[int(np.argmax(trajectory >= B25_L_C_M))]
    regressive = l_exp[:, 0] <= t_c
    reg_dev = float(np.max(np.abs(overshoot[regressive])))
    assert reg_dev <= B25_REGRESSIVE_ENVELOPE_FRAC * B25_L_M, (
        f"regressive-phase shape deviates {reg_dev / B25_L_M:.2f}*L "
        f"(> {B25_REGRESSIVE_ENVELOPE_FRAC}*L) from the measured curve"
    )

    # 4. Breach-threshold bracket (sharp rate-law guard; no absolute band).
    _, res_no = _b25_245_replay(B25_CE_NO_BREACH, store_trajectory=False)
    _, res_yes = _b25_245_replay(B25_CE_BREACH, store_trajectory=False)
    assert float(res_no.l_final_m) < B25_L_M, (
        f"box breached at C_e = {B25_CE_NO_BREACH} (expected no breach); "
        "rate-law magnitude has shifted"
    )
    assert float(res_yes.l_final_m) >= B25_L_M - 1e-9, (
        f"box did not breach at C_e = {B25_CE_BREACH} (expected breach); "
        "rate-law magnitude has shifted"
    )

    # 5. Post-critical rate strictly increasing along the calibrated C_e row.
    rates = []
    for c_e in B25_CE_ROW:
        tg, res = _b25_245_replay(c_e)
        r = _b25_post_critical_rate(tg, res.l_trajectory_m)
        assert r is not None, f"C_e = {c_e} never reached l_c"
        rates.append(r)
    assert all(
        b > a for a, b in zip(rates, rates[1:])
    ), f"post-critical rate not strictly increasing in C_e: {rates}"


# ---------------------------------------------------------------------------
# (8) S2-2 in-domain quantitative gate (slow; spec §11.2; note §5D, ADR-0009).
#     The ONLY quantitative progressive-phase check in M7 (B25-245's
#     progressive phase is out of domain and not gated). Shape is the
#     Pol-anchored validation; the rate pin is a documented regression guard.
# ---------------------------------------------------------------------------

# L = 3 m S2-2 DgFlow case (CG24 Fig. 10 / thesis Fig. 5.10): constant head,
# in the Eq. (5) fit set (L = 3 m base case, D/L = 1/3). Anchors from the note.
S2_L_M = 3.0  # seepage length L (CG24 §4.1; D/L = 1/3)
S2_H_C_M = 0.143  # critical head H_c (Fig. 10 caption, note §5B.9)
S2_H_M = 0.157  # constant imposed head H (Fig. 10 caption; ~10% overload)
S2_C_E = 0.08  # DgFlow run / regression value (note §4.1, §5C)
S2_L_C_M = 1.36  # DgFlow critical length (Fig. 5.9, note §2); anchors H_eq peak
S2_K_MPS = 2.158e-4  # k = kappa(2.2e-11)*rho_w*g/mu, S2-2 sand (note §5A.1)
S2_DT_S = 10.0  # DgFlow reference timestep for L = 3 m (thesis Table 5.3)

S2_SHAPE_ENVELOPE = 0.10  # normalized-shape bound; measured 0.064

# Pinned ACTUAL integrated [L/2, L] average dl/dt (m/s), Delta-t converged to
# 0.1% (1.3825e-4 at dt = 10 s). This is the *actual integrated number*, NOT
# the reconstructed 7.08e-5 x 1.95 product -- so the guard stays auditable if
# the 1.95 conservatism factor is ever re-derived (ADR-0009; test docstring).
S2_RATE_INTEGRATED_MPS = 1.3825e-4
S2_RATE_REL = 0.05  # regression-guard band: real rate-law/H_eq changes shift
# this by tens of % (exponent 0.81->0.80 ~ 13%); trivial numerics by ~0.1%.


def _s2_2_replay(
    dt_s: float = S2_DT_S, t_max_s: float = 25000.0
) -> tuple[np.ndarray, np.ndarray]:
    """Replay the L = 3 m S2-2 DgFlow case at constant head H = 0.157 m.

    In-domain configuration (note §5D): r_e = 1, z_toe = 0, d_bl_m = 0 (DgFlow
    box, no crack term), H_eq anchored on the DgFlow critical length
    l_c = 1.36 m, C_e = 0.08. Returns (t_grid, trajectory).
    """
    t_grid = np.arange(0.0, t_max_s, dt_s)
    result = integrate_progression(
        np.full(t_grid.size, S2_H_M),
        dt_s,
        InstantaneousHead(1.0, 0.0),
        0.0,
        c_e=S2_C_E,
        k_aq_mps=S2_K_MPS,
        d_bl_m=0.0,
        gamma_bl_sub_knpm3=10.0,  # inert at D_bl = 0
        h_c_m=S2_H_C_M,
        l_c_m=S2_L_C_M,
        seepage_length_m=S2_L_M,
        store_trajectory=True,
    )
    return t_grid, result.l_trajectory_m


def _normalized_growth_curve(
    t: np.ndarray, l_series: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize (t, l) to [0, 1] x [0, 1] over the growth span.

    Rate- and breach-independent: isolates trajectory SHAPE from absolute
    magnitude and timing (note §5D).
    """
    growth = np.flatnonzero(np.diff(l_series) > 0.0)
    t0, t1 = t[growth[0]], t[growth[-1] + 1]
    span = (t >= t0) & (t <= t1)
    t_n = (t[span] - t0) / (t1 - t0)
    l_n = (l_series[span] - l_series[span][0]) / (
        l_series[span][-1] - l_series[span][0]
    )
    return t_n, l_n


@pytest.mark.slow
def test_s2_2_in_domain_shape_and_rate() -> None:
    """S2-2 (L=3m DgFlow): SHAPE is the Pol-anchored gate; the rate pin is a
    documented regression guard, NOT a Pol-validated absolute rate.

    This is the ONLY quantitative progressive-phase check in M7 -- B25-245's
    progressive phase is out of domain and not gated (§4 note) -- so the shape
    gate is deliberately demanding.

    WHAT IS POL-ANCHORED (the real validation):
      * Shape -- the normalized trajectory vs the digitized DgFlow l(t)
        (CG24 Fig. 10), within 0.10 (measured 0.064). In-domain (L = 3 m is a
        regression base case, D/L = 1/3) Eq. (5)+Eq. (11) reproduces the DgFlow
        progressive-phase DYNAMICS faithfully (front-loading 0.45 = 0.45).
      * Coefficients -- 89 and 0.81 are validated exactly by
        test_progression_rate_pinned_worked_value (not repeated here).

    WHAT THE RATE PIN IS AND IS NOT:
      It pins our ACTUAL integrated [L/2, L] average dl/dt (1.3825e-4 m/s at
      dt = 10 s) as a REGRESSION GUARD. It is NOT an independently Pol-validated
      absolute rate. Eq. (5)+Eq. (11) over-predicts DgFlow's published rate
      (7.08e-5 m/s) by ~1.95x in-domain -- a DESIGNED-IN conservatism of the
      piecewise-linear H_eq (Eq. (11)'s 0.90*H_c end anchor vs DgFlow's
      effective ~1.0*H_c; note §5D, ADR-0009), not a defect. The pin encodes
      that known ~1.95x offset so a future rate-law OR H_eq change trips it; it
      must NOT be read as M7 matching DgFlow's absolute rate. We pin the actual
      number (1.3825e-4), not the reconstructed 7.08e-5 x 1.95 product, so the
      guard stays auditable if the 1.95 factor is ever re-derived. The ~1.95x
      is a fourth, non-temporal component of the static-transient gap
      (ADR-0009) and must not be over-attributed to the temporal effect.
    """
    t, trajectory = _s2_2_replay()
    assert trajectory is not None

    # Precondition for both metrics: the box must breach under the constant
    # over-critical head (H = 0.157 > H_c = 0.143).
    assert float(trajectory.max()) >= S2_L_M * 0.999, "S2-2 replay did not breach"

    # (1) SHAPE -- Pol-anchored. Normalized trajectory vs the digitized DgFlow
    # curve (running-max cleaned for monotonicity, note §5C).
    dg = _load_csv("L3m_S2-2_pipelength_l-t.csv")
    t_dg, l_dg = dg[:, 0], np.maximum.accumulate(dg[:, 1])
    t_n, l_n = _normalized_growth_curve(t, trajectory)
    dn, dl = _normalized_growth_curve(t_dg, l_dg)
    grid = np.linspace(0.0, 1.0, 50)
    our_n = np.interp(grid, t_n, l_n)
    dg_n = np.interp(grid, dn, dl)
    shape_dev = float(np.max(np.abs(our_n - dg_n)))
    assert shape_dev <= S2_SHAPE_ENVELOPE, (
        f"normalized shape deviates {shape_dev:.3f} from the digitized DgFlow "
        f"trajectory (> {S2_SHAPE_ENVELOPE})"
    )

    # (2) RATE MAGNITUDE -- regression guard, NOT a Pol-validated absolute rate
    # (see docstring / ADR-0009). End-to-end average over [L/2, L], matching
    # Table A.5's window, pinned at its converged value.
    t_half = t[int(np.argmax(trajectory >= S2_L_M / 2.0))]
    t_breach = t[int(np.argmax(trajectory >= S2_L_M * 0.999))]
    rate = (S2_L_M - S2_L_M / 2.0) / (t_breach - t_half)
    assert rate == pytest.approx(S2_RATE_INTEGRATED_MPS, rel=S2_RATE_REL), (
        f"S2-2 integrated [L/2,L] rate {rate:.4e} m/s drifted from the pinned "
        f"{S2_RATE_INTEGRATED_MPS:.4e} m/s (rel {S2_RATE_REL}); the rate law or "
        "the H_eq curve has changed (ADR-0009)"
    )


# ---------------------------------------------------------------------------
# (9) Timestep convergence, sharpened (slow; spec §11; note §5B.10)
# ---------------------------------------------------------------------------


def _flashy_stage_m(t_s: np.ndarray) -> np.ndarray:
    """Steep synthetic typhoon limb: 0 -> 6 m in 2 h, 6 h plateau, 4 h fall."""
    return np.interp(t_s, [0.0, 7200.0, 28800.0, 43200.0], [0.0, 6.0, 6.0, 0.0])


def _run_convergence_case(dt_s: float) -> float:
    """Integrate the worst-case theta over the flashy event at one dt."""
    t_grid = np.arange(0.0, 43200.0, dt_s)
    result = integrate_progression(
        _flashy_stage_m(t_grid),
        dt_s,
        InstantaneousHead(0.6, 0.0),
        0.0,
        c_e=0.030,  # high: top of the small-scale calibration range (note §4)
        k_aq_mps=1.0e-3,  # high: ~FS35-238 k (kappa 10.2e-11, note §4); fixture
        d_bl_m=0.5,  # low: weakest gate, earliest onset
        gamma_bl_sub_knpm3=10.0,
        h_c_m=2.0,
        l_c_m=16.6,
        seepage_length_m=50.0,
    )
    return float(result.l_final_m)


@pytest.mark.slow
def test_timestep_convergence_on_steep_rising_limb_worst_case_theta() -> None:
    """l_e at dt = 600 s differs from dt = 300 s by less than 1 %.

    Spec §11 timestep convergence test, sharpened as prescribed: a steep
    rising limb (0 -> 6 m in 2 h, far flashier than a design hydrograph)
    with the high-progression-rate corner that most stresses forward Euler
    -- high k_aq, high C_e, low D_bl. dt = 600 s is the field-scale
    production candidate; both runs sample the same analytic stage curve on
    their own grids. The event is sized so l_e lands mid-domain (neither
    arrested nor breached), otherwise the comparison degenerates.
    """
    l_e_coarse = _run_convergence_case(600.0)
    l_e_fine = _run_convergence_case(300.0)

    assert 0.0 < l_e_fine < 50.0, "degenerate case: l_e must land mid-domain"
    relative_difference = abs(l_e_coarse - l_e_fine) / l_e_fine
    assert relative_difference < 0.01, (
        f"forward-Euler dt/2 test failed: l_e(600 s) = {l_e_coarse:.3f} m vs "
        f"l_e(300 s) = {l_e_fine:.3f} m ({relative_difference:.2%} > 1%)"
    )


# ---------------------------------------------------------------------------
# (10) Across-realizations equivalence (slow; spec §6 vectorization).
#      One vectorized code path -- no scalar fork -- must equal a per-row loop.
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_across_realizations_matches_scalar_loop() -> None:
    """The vectorized N-row path equals a per-row scalar loop (spec §6).

    1,000 random parameter rows across realistic prior ranges (note §7
    families/COVs) share one hydrograph. The terminal l_e from a single
    vectorized ``integrate_progression`` call -- and the t_uh and uplift
    diagnostics -- must match a per-row scalar loop to floating-point
    tolerance. There is ONE implementation, vectorized via numpy broadcasting
    (N-vector pipe lengths and latched uplift states, np.where piecewise H_eq
    over per-realization breakpoints, indicator-gated rate); this test guards
    against a scalar-only regression or an accidental second code path.

    The batch is checked to actually exercise the branches it claims (breach
    and non-breach, l_c crossing, and flat realizations), so a future seed or
    range change cannot quietly make the equivalence trivial.
    """
    rng = np.random.default_rng(12345)  # deterministic seed (conventions)
    n = 1000
    length, z_toe, dt_s = 8.0, 0.0, 600.0

    def _lognormal(median: float, cov: float, size: int) -> np.ndarray:
        sigma = np.sqrt(np.log(1.0 + cov**2))
        return median * np.exp(rng.normal(0.0, sigma, size))

    k_aq = _lognormal(3e-4, 0.5, n)  # §7 COV 0.50
    c_e = _lognormal(0.014, 0.5, n)  # §7 COV 0.50
    d_bl = _lognormal(3.0, 0.2, n)  # §7 COV 0.20
    d_aq = _lognormal(3.3, 0.2, n)  # §7 COV 0.20 (D/L ~ 1/3)
    gamma_bl_sub = np.clip(rng.normal(10.0, 0.5, n), 1.0, None)  # §7 COV 0.05
    h_c = _lognormal(1.0, 0.4, n)  # plausible field critical head
    l_c = 0.5 * length * np.tanh(2.0 * d_aq / length)  # Eq. (13) per realization
    r_e = rng.uniform(0.3, 0.8, n)
    l_ini = np.where(rng.random(n) < 0.3, rng.uniform(0.0, 2.0, n), 0.0)

    # shared two-peak hydrograph (the trough exercises the per-event latch);
    # sized so the 1,000-row batch spans breach / non-breach / l_c / flat.
    h_river = np.concatenate([np.full(40, 6.0), np.full(25, 1.5), np.full(40, 7.0)])

    vec = integrate_progression(
        h_river,
        dt_s,
        InstantaneousHead(r_e, z_toe),
        z_toe,
        c_e=c_e,
        k_aq_mps=k_aq,
        d_bl_m=d_bl,
        gamma_bl_sub_knpm3=gamma_bl_sub,
        h_c_m=h_c,
        l_c_m=l_c,
        seepage_length_m=length,
        l_ini_m=l_ini,
    )

    l_loop = np.empty(n)
    t_uh_loop = np.empty(n)
    uplift_loop = np.empty(n, dtype=bool)
    for i in range(n):
        row = integrate_progression(
            h_river,
            dt_s,
            InstantaneousHead(float(r_e[i]), z_toe),
            z_toe,
            c_e=float(c_e[i]),
            k_aq_mps=float(k_aq[i]),
            d_bl_m=float(d_bl[i]),
            gamma_bl_sub_knpm3=float(gamma_bl_sub[i]),
            h_c_m=float(h_c[i]),
            l_c_m=float(l_c[i]),
            seepage_length_m=length,
            l_ini_m=float(l_ini[i]),
        )
        l_loop[i] = float(row.l_final_m)
        t_uh_loop[i] = float(row.t_uh_s)
        uplift_loop[i] = bool(row.uplift_occurred)

    # Equivalence (expected bitwise-identical; tolerance guards platform pow).
    np.testing.assert_allclose(vec.l_final_m, l_loop, rtol=1e-12, atol=1e-12)
    assert np.array_equal(np.asarray(vec.t_uh_s), t_uh_loop, equal_nan=True)
    assert np.array_equal(np.asarray(vec.uplift_occurred), uplift_loop)

    # The batch must actually span the branches (not a degenerate all-breach or
    # all-flat draw), or the equivalence above would be vacuous.
    l_final = np.asarray(vec.l_final_m)
    assert (l_final >= length - 1e-9).any(), "no realization breached"
    assert (l_final < length - 1e-9).any(), "every realization breached"
    assert (l_final > l_c).any(), "no realization crossed l_c"
    assert np.isclose(l_final, l_ini).any(), "no realization stayed flat"


# ---------------------------------------------------------------------------
# (11) Interface guard (passes before implementation)
# ---------------------------------------------------------------------------


def test_public_interface_and_pinned_constants() -> None:
    """The module exposes the approved interface with the paper constants.

    The constant values pin the regression coefficients (89, 0.81; SIE 2024
    Eq. (5)), the crack factor (0.3; Eq. (6)) and the equilibrium end
    anchor (0.9; Eq. (11)) at module level, independent of the kernels.
    """
    assert set(progression.__all__) == {
        "CRACK_RESISTANCE_FACTOR",
        "EQUILIBRIUM_END_FACTOR",
        "POL_RATE_COEFFICIENT",
        "POL_RATE_EXPONENT",
        "ProgressionResult",
        "equilibrium_head",
        "integrate_progression",
        "progression_rate",
    }
    assert POL_RATE_COEFFICIENT == 89.0
    assert POL_RATE_EXPONENT == 0.81
    assert CRACK_RESISTANCE_FACTOR == 0.3
    assert EQUILIBRIUM_END_FACTOR == 0.9

    assert ProgressionResult._fields == (
        "l_final_m",
        "l_trajectory_m",
        "uplift_occurred",
        "heave_occurred",
        "t_uh_s",
    )

    expected_signatures = {
        "equilibrium_head": ("pipe_length_m", "h_c_m", "l_c_m", "seepage_length_m"),
        "progression_rate": (
            "h_erosion_m",
            "h_eq_m",
            "c_e",
            "k_aq_mps",
            "seepage_length_m",
        ),
        "integrate_progression": (
            "h_river_m",
            "dt_s",
            "head_model",
            "z_toe_m",
            "c_e",
            "k_aq_mps",
            "d_bl_m",
            "gamma_bl_sub_knpm3",
            "h_c_m",
            "l_c_m",
            "seepage_length_m",
            "l_ini_m",
            "store_trajectory",
        ),
    }
    for name, expected_params in expected_signatures.items():
        func = getattr(progression, name)
        assert tuple(inspect.signature(func).parameters) == expected_params, name
