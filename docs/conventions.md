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
    *   Unit Weights ($\gamma'_\mathrm{bl}, \gamma'_\mathrm{p}, \gamma_w$): Kilonewtons per cubic meter ($kN/m^3$) or Newtons per cubic meter ($N/m^3$). *Note: Maintain absolute internal consistency to eliminate factor-of-1000 conversion slips between Pascal / kPa values during calculation.*
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

## 8. Thesis text does not live in this repository

Between 2026-07-12 and 2026-07-29 this repository accumulated seven `_thesis_*.tex`
and `_thesis_*.bib` files at its root. They were audited and retired on 2026-07-29
(`git rm`; content recoverable from history; audit at
`msc-thesis/scratch/THESIS_FRAGMENT_AUDIT.md`). The audit found that essentially
none of their content was still both absent from the thesis and true: the two
Chapter 5 fragments were already integrated in superset form, and the Study Area and
Methodology fragments had silently become **the pre-as-built drafts**, still
asserting an r_e-translated static head (ADR-0028 reversed it), the native
integration timestep (ADR-0030), the L/lambda_in validity alarm (withdrawn as a
category error), the foreshore-width control on risk (refuted, ADR-0025 amendment),
and the expected LHS tail-variance advantage (refuted, fm5). A thesis fragment
maintained here is a second copy of the record that drifts out of date silently and
invisibly, because nothing in this repository's test suite or ADR process governs it.

The rules below prevent a recurrence. `tests/test_repo_hygiene.py` enforces the
first one.

**No `.tex`, `.bib` or thesis-prose file is ever created in this repository.** The
sole authoritative thesis is `d:\repositories\msc-thesis`.

**Findings reach the thesis by a targeted edit to the relevant msc-thesis chapter,
made only when the finding is genuinely needed there.** Do not stage thesis prose
here first. Work products of record belong in `docs/`: reports of record, ADRs in
`docs/decisions/`, companion notes, and the provenance documents. That is where a
finding is written down; the thesis then cites or restates whatever part of it the
argument actually needs.

**The msc-thesis report is compiled with XeLaTeX via Overleaf; the local clone is a
Git-synced mirror.** Never introduce a package or command incompatible with XeLaTeX,
and never compile locally. Read the current on-disk state of any chapter before
editing it, since the author may have written in Overleaf since the last session.

**No Japanese script (kanji, hiragana, katakana) in the thesis report** -- main
body, appendices, figures, captions or bibliography. Japanese source names, place
names, document titles and technical terms are romanised or translated there, with
the original script recorded in this repository's provenance documents instead
(`docs/tokachi_bep_inputs_provenance.md` and the review notes are the right home for
the original 様式-3, 高水敷幅, 土層縦断図 and similar terms; they are used freely
here and must not travel). One exception, agreed 2026-07-29: `references.bib`
entries for Japanese-language sources may retain the original title alongside the
romanised form, because the original is the accurate bibliographic record of the
source. That exception covers `references.bib` only and does not extend to any
`.tex` file. Verified 2026-07-29: zero CJK characters in typeset msc-thesis `.tex`
content. The check that keeps it that way is documented in `msc-thesis/project-notes.md`.

**No em dashes; ranges are written "X to Y", never "X-Y" or an en dash.** See
`msc-thesis/project-notes.md` for the full style contract (citation-key preservation,
`\label{}` preservation, minimal surgical edits, plan-and-approve for multi-chapter
tasks). That contract is binding on any edit to that repository.
