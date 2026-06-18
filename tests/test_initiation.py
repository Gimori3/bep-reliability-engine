"""Tests for M5 initiation gating (``bep_reliability_engine.initiation``).

Executable contract for the approved M5 interface (ADR-0008), written before
the implementation: every physics test is expected to fail with
``NotImplementedError`` until ``initiation.py`` is filled in. The interface
and signature-guard tests at the bottom pass already and must keep passing.

Coverage required by the design review:
(1) the complete eight-row I_er truth table,
(2) the symbolic boundary cases Z_uplift = 0 at
    Delta_h_blanket = gamma'_bl * D_bl / gamma_w and Z_heave = 0 at
    Delta_h_blanket / D_bl = gamma'_bl / gamma_w (the same overpressure —
    the ADR-0008 collapse, pinned explicitly),
(3) vectorized array inputs, and
(4) a signature guard confirming no function in the module accepts or
    computes any crack-reduced head (the 0.3 * D_bl term is M7-only).

Parameter values are Tokachi-representative and match the M4 test
conventions: gamma'_bl ~ 10 kN/m3 (theta column ``gamma_bl_sub``), D_bl of
order meters. The 8.19 kN/m3 case is Pol's SIE 2024 base case
(gamma_bl,sat = 18 kN/m3 minus gamma_w).
"""

import ast
import inspect

import numpy as np
import pytest

from bep_reliability_engine import initiation
from bep_reliability_engine.constants import GAMMA_W
from bep_reliability_engine.initiation import erosion_indicator, z_heave, z_uplift

# Symbolic boundary cases: (gamma_bl_sub [kN/m3], d_bl [m]).
BOUNDARY_CASES = [
    (10.0, 3.0),  # Tokachi-representative (M4 test theta convention)
    (8.19, 0.5),  # Pol SIE 2024 base case blanket, thin
    (11.5, 8.0),  # heavy blanket, thick
]

# Head perturbation for the one-sided sign-convention checks [m].
EPS_M = 1.0e-6

# Complete I_er truth table:
# (uplift_ever, pipe_length_positive, heave_now) -> (u | p) & h
TRUTH_TABLE = [
    (False, False, False, False),
    (False, False, True, False),
    (False, True, False, False),
    (False, True, True, True),
    (True, False, False, False),
    (True, False, True, True),
    (True, True, False, False),
    (True, True, True, True),
]


def _delta_h_uplift_threshold_m(gamma_bl_sub: float, d_bl: float) -> float:
    """Overpressure at which the uplift resistance is exactly balanced."""
    return gamma_bl_sub * d_bl / GAMMA_W


# ---------------------------------------------------------------------------
# (1) I_er truth table, all eight rows
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "uplift_ever, pipe_length_positive, heave_now, expected",
    TRUTH_TABLE,
    ids=[f"u={int(u)},p={int(p)},h={int(h)}" for u, p, h, _ in TRUTH_TABLE],
)
def test_erosion_indicator_truth_table(
    uplift_ever: bool,
    pipe_length_positive: bool,
    heave_now: bool,
    expected: bool,
) -> None:
    """I_er = (uplift_ever OR pipe_length_positive) AND heave_now, row by row."""
    result = erosion_indicator(uplift_ever, pipe_length_positive, heave_now)
    assert bool(result) == expected


def test_erosion_indicator_truth_table_vectorized_single_call() -> None:
    """All eight truth-table rows evaluated elementwise in one array call."""
    uplift_ever, pipe_length_positive, heave_now, expected = (
        np.array(column) for column in zip(*TRUTH_TABLE)
    )
    result = erosion_indicator(uplift_ever, pipe_length_positive, heave_now)
    assert result.shape == (8,)
    assert result.dtype == np.bool_
    np.testing.assert_array_equal(result, expected)


def test_erosion_indicator_random_vectors_match_python_logic() -> None:
    """Elementwise semantics on long boolean vectors (no short-circuiting)."""
    rng = np.random.default_rng(58)  # deterministic seed (conventions)
    uplift_ever = rng.random(256) < 0.5
    pipe_length_positive = rng.random(256) < 0.2
    heave_now = rng.random(256) < 0.5
    expected = np.array(
        [
            (u or p) and h
            for u, p, h in zip(uplift_ever, pipe_length_positive, heave_now)
        ]
    )
    result = erosion_indicator(uplift_ever, pipe_length_positive, heave_now)
    assert result.dtype == np.bool_
    np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# (2) Symbolic boundary cases and the resistance-minus-load sign convention
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma_bl_sub, d_bl", BOUNDARY_CASES)
def test_z_uplift_zero_at_symbolic_threshold(gamma_bl_sub: float, d_bl: float) -> None:
    """Z_uplift = 0 exactly at Delta_h_blanket = gamma'_bl * D_bl / gamma_w."""
    delta_h = _delta_h_uplift_threshold_m(gamma_bl_sub, d_bl)
    assert float(z_uplift(delta_h, gamma_bl_sub, d_bl)) == pytest.approx(
        0.0, abs=1.0e-12
    )


@pytest.mark.parametrize("gamma_bl_sub, d_bl", BOUNDARY_CASES)
def test_z_uplift_sign_convention_resistance_minus_load(
    gamma_bl_sub: float, d_bl: float
) -> None:
    """Below the threshold Z_uplift > 0 (safe); above it Z_uplift < 0.

    This pins the confirmed resistance-minus-load reading (ADR-0008
    convention note): the printed term order in Pol SIE 2024 Eqs. (8)-(9)
    is flipped and must not be reproduced.
    """
    delta_h = _delta_h_uplift_threshold_m(gamma_bl_sub, d_bl)
    assert float(z_uplift(delta_h - EPS_M, gamma_bl_sub, d_bl)) > 0.0
    assert float(z_uplift(delta_h + EPS_M, gamma_bl_sub, d_bl)) < 0.0


@pytest.mark.parametrize("gamma_bl_sub, d_bl", BOUNDARY_CASES)
def test_z_heave_zero_at_symbolic_threshold(gamma_bl_sub: float, d_bl: float) -> None:
    """Z_heave = 0 exactly where the exit gradient equals gamma'_bl / gamma_w.

    The critical overpressure (gamma'_bl / gamma_w) * D_bl is the uplift
    threshold: the two limit states share their boundary by construction
    (ADR-0008).
    """
    delta_h = (gamma_bl_sub / GAMMA_W) * d_bl
    assert float(z_heave(delta_h, gamma_bl_sub, d_bl)) == pytest.approx(
        0.0, abs=1.0e-12
    )


@pytest.mark.parametrize("gamma_bl_sub, d_bl", BOUNDARY_CASES)
def test_z_heave_sign_convention_resistance_minus_load(
    gamma_bl_sub: float, d_bl: float
) -> None:
    """Below the critical gradient Z_heave > 0 (safe); above it Z_heave < 0."""
    delta_h = (gamma_bl_sub / GAMMA_W) * d_bl
    assert float(z_heave(delta_h - EPS_M, gamma_bl_sub, d_bl)) > 0.0
    assert float(z_heave(delta_h + EPS_M, gamma_bl_sub, d_bl)) < 0.0


def test_adr0008_collapse_identity() -> None:
    """Z_heave is identically Z_uplift / D_bl (the ADR-0008 algebra).

    Consequence pinned alongside the identity: the two limit states change
    sign at the same instant, so heave activity implies uplift exceedance
    at that same timestep and I_er reduces to heave_now under the baseline
    parameterization.
    """
    rng = np.random.default_rng(2016)  # deterministic seed (conventions)
    delta_h = rng.uniform(0.0, 6.0, 512)
    gamma_bl_sub = rng.normal(10.0, 0.5, 512)
    d_bl = rng.lognormal(np.log(3.0), 0.2, 512)

    z_u = z_uplift(delta_h, gamma_bl_sub, d_bl)
    z_h = z_heave(delta_h, gamma_bl_sub, d_bl)

    np.testing.assert_allclose(z_h, z_u / d_bl, rtol=1.0e-12, atol=1.0e-15)
    np.testing.assert_array_equal(z_h < 0.0, z_u < 0.0)


# ---------------------------------------------------------------------------
# (3) Vectorized array inputs
# ---------------------------------------------------------------------------


def test_z_functions_vectorized_match_scalar_loop() -> None:
    """(N,) array evaluation agrees with N scalar calls, for both kernels."""
    rng = np.random.default_rng(42)  # deterministic seed (conventions)
    delta_h = rng.uniform(0.0, 6.0, 32)
    gamma_bl_sub = rng.normal(10.0, 0.5, 32)
    d_bl = rng.lognormal(np.log(3.0), 0.2, 32)

    for func in (z_uplift, z_heave):
        vec = func(delta_h, gamma_bl_sub, d_bl)
        assert vec.shape == (32,)
        assert vec.dtype == np.float64
        scalar = [float(func(delta_h[i], gamma_bl_sub[i], d_bl[i])) for i in range(32)]
        np.testing.assert_allclose(vec, scalar, rtol=1.0e-14)


def test_z_functions_broadcast_scalar_head_over_theta_arrays() -> None:
    """A scalar timestep head broadcasts over (N,) sampled-parameter arrays.

    This is the M7 calling pattern: one Delta_h_blanket per timestep when
    r_e is folded in upstream, against per-realization gamma'_bl and D_bl.
    """
    rng = np.random.default_rng(7)  # deterministic seed (conventions)
    gamma_bl_sub = rng.normal(10.0, 0.5, 16)
    d_bl = rng.lognormal(np.log(3.0), 0.2, 16)
    delta_h = 2.5

    for func in (z_uplift, z_heave):
        vec = func(delta_h, gamma_bl_sub, d_bl)
        assert vec.shape == (16,)
        scalar = [float(func(delta_h, gamma_bl_sub[i], d_bl[i])) for i in range(16)]
        np.testing.assert_allclose(vec, scalar, rtol=1.0e-14)


# ---------------------------------------------------------------------------
# (4) Interface and signature guards (these pass before implementation)
# ---------------------------------------------------------------------------

# Substrings forbidden in any function parameter name in the module.
FORBIDDEN_PARAM_SUBSTRINGS = ("erosion", "crack", "reduced")

# Identifiers forbidden anywhere in the module source (the public function
# name ``erosion_indicator`` is legitimate and matches none of these).
FORBIDDEN_IDENTIFIER_SUBSTRINGS = (
    "h_erosion",
    "erosion_head",
    "head_erosion",
    "crack",
)

# Numeric fingerprint of the crack-resistance term H = dh - 0.3 * D_bl.
CRACK_COEFFICIENT = 0.3


def _module_functions() -> list:
    """All functions defined in the initiation module (public or not)."""
    return [
        func
        for _, func in inspect.getmembers(initiation, inspect.isfunction)
        if func.__module__ == initiation.__name__
    ]


def test_public_interface_is_exactly_the_approved_one() -> None:
    """The module exposes exactly the three approved kernels."""
    assert set(initiation.__all__) == {"erosion_indicator", "z_heave", "z_uplift"}
    expected_signatures = {
        "z_uplift": ("delta_h_blanket_m", "gamma_bl_sub_knpm3", "d_bl_m"),
        "z_heave": ("delta_h_blanket_m", "gamma_bl_sub_knpm3", "d_bl_m"),
        "erosion_indicator": ("uplift_ever", "pipe_length_positive", "heave_now"),
    }
    for name, expected_params in expected_signatures.items():
        func = getattr(initiation, name)
        params = tuple(inspect.signature(func).parameters)
        assert params == expected_params, name


def test_no_crack_reduced_head_in_signatures() -> None:
    """No function in the module accepts a crack-reduced head.

    The 0.3 * D_bl reduction belongs exclusively to the M7 erosion driver;
    uplift and heave act on the full Delta_h_blanket (spec §5).
    """
    functions = _module_functions()
    assert functions, "no functions found in the initiation module"
    for func in functions:
        for param in inspect.signature(func).parameters:
            offending = [
                sub for sub in FORBIDDEN_PARAM_SUBSTRINGS if sub in param.lower()
            ]
            assert not offending, f"{func.__name__}({param}) matches {offending}"


def test_no_crack_reduced_head_computed_in_module_source() -> None:
    """The module source never computes a crack-reduced head.

    AST-based so it keeps guarding after implementation: numeric constants
    are scanned for the 0.3 crack coefficient (docstrings are string
    constants and cannot false-positive), and every identifier — function
    names, arguments, variables, attributes — is scanned for crack-head
    names. ``erosion_indicator`` itself matches none of the forbidden
    patterns.
    """
    source = inspect.getsource(initiation)
    tree = ast.parse(source)

    numeric_constants = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    ]
    offending_constants = [
        value for value in numeric_constants if abs(value - CRACK_COEFFICIENT) < 1e-12
    ]
    assert not offending_constants, (
        "crack coefficient 0.3 found in initiation module code; "
        "H_erosion = dh_blanket - 0.3 * D_bl is M7-only (spec §5)"
    )

    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id.lower())
        elif isinstance(node, ast.arg):
            identifiers.add(node.arg.lower())
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identifiers.add(node.name.lower())
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr.lower())
    offending_identifiers = {
        ident
        for ident in identifiers
        if any(sub in ident for sub in FORBIDDEN_IDENTIFIER_SUBSTRINGS)
    }
    assert not offending_identifiers, (
        f"crack-reduced-head identifiers in initiation module: "
        f"{sorted(offending_identifiers)}"
    )
