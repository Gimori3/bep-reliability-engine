# Phase 1 Computational Architecture: Coding Conventions

## 1. Naming Standards
*   **Packages, Modules, Variables, and Functions:** `snake_case` (e.g., `theta_matrix`, `evaluate_realization`, `sellmeijer_static`).
*   **Classes and Pydantic Data Models:** `PascalCase` (e.g., `FragilityResult`, `HydrographRecord`, `Config`).
*   **Constants:** `SCREAMING_SNAKE` (e.g., `GAMMA_W`, `THETA_REPOSE_DEFAULT`).

## 2. Unit System and Structural Boundaries
*   **Internal Computation Core:** All engineering and scientific logic MUST process in strict **SI Base Units**:
    *   Lengths / Thicknesses / Diameters: Meters ($m$)
    *   Time / Timesteps ($\Delta t$): Seconds ($s$)
    *   Hydraulic Conductivities ($k_{aq}, k_{bl}$): Meters per second ($m/s$)
    *   Unit Weights ($\gamma'_s, \gamma_w$): Kilonewtons per cubic meter ($kN/m^3$) or Newtons per cubic meter ($N/m^3$). *Note: Maintain absolute internal consistency to eliminate factor-of-1000 conversion slips between Pascal / kPa values during calculation.*
    *   Erosion Coefficient ($C_e$): Dimensionless ($-$)
*   **Angles:** Must be maintained as **Radians** internally.
*   **I/O Boundaries:** Conversions from standard site data units (e.g., permeability in $m/\text{day}$, grain size in $mm$, or angles in degrees) must happen *exclusively* inside `M1 (config)` loading or `M3 (hydrograph_loader)`. No hidden adjustments are permitted inside physics kernels.

## 3. Inline Documentation Code
All public functions and module APIs must use the **NumPy Docstring Style**. Every docstring for a physics module must explicitly detail its mathematical assumptions.

### Example Template:
```python
def calculate_response_factor(k_aq: float, D_aq: float, D_bl: float, k_bl: float, lambda_out: float, L: float) -> float:
    """
    Computes the instantaneous response factor (r_e) using the Mazure leakage length.

    Parameters
    ----------
    k_aq : float
        Aquifer horizontal hydraulic conductivity [m/s].
    D_aq : float
        Aquifer layer thickness [m].
    D_bl : float
        Blanket layer thickness [m].
    k_bl : float
        Blanket vertical hydraulic conductivity [m/s].
    lambda_out : float
        Outflow length scale parameter [m].
    L : float
        Seepage length across the embankment structure [m].

    Returns
    -------
    float
        Dimensionless response factor r_e [-].

    Notes
    -----
    This calculation embeds the explicit architectural assumption of instantaneous
    hydraulic translation (no transient seepage time lag through the blanket).
    """
    import math
    lambda_in = math.sqrt((k_aq * D_aq * D_bl) / k_bl)
    return lambda_in / (lambda_out + L + lambda_in)
```

## 4. Strict Type Definitions
Type hints are mandatory on all public function signatures to maintain structural integrity across Phase 1 and Phase 2 transitions. Use explicit types from the `typing` module or native types, along with `numpy.ndarray` structural annotations where applicable.

## 5. Explicit Dimensional Naming
Variables and parameters should expose units where ambiguity exists.
*   *Good:* `pressure_pa`, `permeability_mps`, `duration_seconds`, `timestep_seconds`
*   *Bad:* `pressure`, `permeability`, `duration`

## 6. Numerical Philosophy
*   Prioritize vectorized NumPy operations across realizations.
*   Avoid premature optimization; profile before introducing Numba.
*   Maintain strict reproducibility through deterministic RNG seeds.

## 7. Testing Philosophy
Every physics module must eventually pass deterministic smoke tests, analytical validation checks (e.g., checking against Mazure analytical solutions), and monotonicity assertions. Pytest execution is mandatory.
