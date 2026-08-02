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

## 9. Repository layout conventions

Recorded 2026-07-31 by the structural audit (`docs/repo_audit_2026-07-31.md`).
Each of these describes a convention already in force. They are written down
because they were legible only by inspection, and because the audit measured the
alternative -- reorganising the tree to make them self-evident -- and found it
costs far more than it earns. **Any of these could be made tidier; none should
be.** The measured costs are in the audit, sections 3.6 and 3.7.

### 9.1 Two kinds of document live in `docs/`

* **Undated `docs/<name>.md` are documents of record** and stay current:
  `architecture.md` (the authoritative spec), `conventions.md`,
  `phase2_report.md`, `phase3_report.md`, `stage6_6_report.md`,
  `tokachi_bep_inputs_provenance.md`. When a later run outdates one, append a
  dated addendum section stating it is **authoritative where it differs**, rather
  than rewriting the body (`phase2_report.md` sections 11 to 14 are the pattern).
* **Dated `docs/<name>_YYYY-MM-DD.md` are closed one-shot artifacts** -- a
  campaign, an audit, a document review. They are frozen records of a session and
  are never updated in place; a later pass writes a new dated file and supersedes
  the old one by pointer.

They share a directory deliberately. Moving the dated artifacts into a
subdirectory was proposed and **declined**: `docs/production_campaign_2026-07-29.md`
is named by path in `tests/test_figure_pass.py`, and that guard's failure mode on
a missing path used to be a silent skip. The guard now asserts (2026-07-31
hardening), so a move would fail loudly rather than silently -- but the 13 inbound
citations still buy nothing.

### 9.2 `docs/decisions/` has three filename grammars, and they mean different things

| Grammar | Meaning |
|---|---|
| `NNNN-slug.md` | A numbered **decision** (ADR). 0001 to 0048, gap-free. Superseded ADRs stay in place with their Status line updated; they are never deleted or renamed. |
| `adrNNNN-slug.md` / `.json` | **Evidence for** the ADR of that number: a companion analysis note, an evidence JSON, or both. Note the grammar differs from the ADR's own filename (lowercase `adr` prefix, no separating dash). |
| `<topic>-study.md`, `<topic>-synthesis.md` | An **un-numbered study**: work that produced a finding but changed no default and therefore consumed no ADR number (`seepage-length-L-study.md`, `r10-foreshore-exhaustion-screening.md`, `epistemic-bracket-synthesis.md`, `m7-pol-ode-reference-values.md`). |

Do not "unify" these. The audit measured a restructure at **293 reference lines
across 84 files** (66 tracked, 18 in the gitignored `untracked-supporting-files/` library),
plus 12 paths whose SHA-256 is recorded in
`results/production_campaign_manifest.json`, 16 literal path strings in gate G7's
`FIGURE_DRIVERS`, six paths hard-coded in `tests/test_figure_pass.py`, and the
thesis Appendix C ADR register. The grammar is consistent and already meaningful;
what was missing was this table.

### 9.3 Figures are written by their drivers, never copied by hand

`docs/figures/` is the canonical publication location and the only one gate G7
checks. Every figure driver dual-writes: the study-local copy under
`results/<study>/figures/` and the tracked copy under `docs/figures/`
(`scripts/_figstyle.py::save`, `stage6_6_gap_decomposition._write_figure`). This
is the structural fix for a real failure -- a human copying figures between the
two let the KP 62.0 set go stale twice, on 2026-07-29 and 2026-07-30. Adding a
figure means adding it to `FIGURE_DRIVERS`; `test_every_tracked_publication_figure_is_declared`
requires every tracked PNG to be declared.

A root-level `figures/` directory existed until 2026-07-31 holding 11 byte-identical
duplicates that nothing wrote and nothing read. It was deleted; if one reappears,
it is a mistake.

### 9.3.1 A rendered figure title carries no ADR number and no project-process statement

Thirty of these figures are placed in the **main body** of the thesis, whose binding
rules exclude both ADR identifiers and any narration of the project's own evolution.
A caption can be rewritten in the thesis repository; **text rendered into the PNG
cannot**, so it has to be right here. A title states what the figure shows, in the
vocabulary of the physics.

**Open, and the fix is a re-render.** Three of the 57 rendered titles violate this,
established by reading every `suptitle` and `set_title` on 2026-08-02:

| Driver, line | Figure | Rendered title contains | Placed |
|---|---|---|---|
| `dem_cross_section_study.py:2044` | `adr0047_dem_seepage_length.png` | `"ADR-0047: …"` **and `"measurement only, no input value changed"`** | thesis main body |
| `timestep_convergence_stress.py:902` | `adr0039-timestep-stress.png` | `"(spec §11; ADR-0039)"` | thesis main body |
| `ce_prior_study.py:388` | `ce_prior_reconciliation.png` | `"(ADR-0026)"` | thesis appendix |

The first is the one that matters, and it is **not only a register problem**: the
title asserts *no input value changed*, which was true of the measurement study but
was overtaken when ADR-0047 was **adopted at KP 62.0** and `L_m` went 47.0 to 40.0 in
`data/processed/tokachi_bep_inputs.csv`. A main-body thesis figure therefore renders a
statement this repository's own record contradicts. Fix that title first.

A file *name* beginning `adr…` is not a violation: it never appears in the compiled
PDF. Only rendered text does. A contemporaneous claim that
`adr0031-convergence-n-ladder.png` also carries an ADR number is **wrong** and should
not be propagated; its title reads `"fm5 tail-variance: LHS vs crude MC"`.

**When to act.** Next time a session re-renders any of these three, fix the title in
the same edit; it is one string each. The figures are otherwise content-current, so
none of this justifies a re-run of its own. Re-rendering changes only the PNG, so the
thesis needs no edit: the filenames and captions there are unaffected.

### 9.4 A test may only skip on something that is genuinely optional

`pytest.skip` / `skipif` is correct for a gitignored machine-local artifact
(`data/raw/` drops, `results/` files, the reference PDFs) -- absence there means a
fresh clone. Its `reason` string should say so; every such mark in `tests/` now
contains the word "untracked".

**A tracked artifact must be asserted, never skipped.** Skipping on a committed
path means a move, rename or deletion silently disables the guard while the suite
still reports green. Eight guards in `tests/test_figure_pass.py` had this shape
until 2026-07-31, and the worst of them skipped when a *claim was absent from a
document*, so deleting the claim made its own guard pass.
`test_no_guard_in_this_file_skips_on_a_tracked_path` keeps the pattern out of
that file.

## 10. Retention policy for `results/`

`results/` is gitignored and machine-local: roughly 2.1 GB across 723 files as of
2026-07-31. Nothing in it is recoverable from git, so the policy is about what
must survive to the defence, not about disk.

### 10.1 Retained until the defence, without exception

These are the artifacts a thesis number traces to. Several are recorded with
SHA-256 in `results/production_campaign_manifest.json`, so they must not move or
change content either.

| Category | Regenerated by | Note |
|---|---|---|
| The 8 production sweeps, `tokachi_kp*_historical_{matrix,bulk}.{h5,json}` | `python scripts/run_sweep.py configs/kp*_matrix.yaml` (hours) | Every Phase 2 and Phase 3 number descends from these. Manifest-hashed. |
| `production_campaign_manifest.json` + `production_campaign/` | `python scripts/production_campaign.py` | The machine-readable half of the campaign document of record. |
| `hwl_bias_resolution/` (about 839 MB, two N = 1e6 ladders) | `python scripts/hwl_bias_resolution.py`, about 170 min | **See 10.2 -- this one is not a convenience.** |
| `sensitivity/` (ADR-0045/0046/0048, `ce_prior`, `seepage_length`, `foreshore_exhaustion`) | each companion driver | The epistemic-bracket headline numbers cite these. |
| `phase2/`, `phase2_anchor_rating/`, `phase2_no_initiation/` | `python -m bayesian_reliability_updating ... --verify` | The posteriors and both documented variants. Manifest-hashed. |
| `stage6_6/` (two N) | `python scripts/stage6_6_gap_decomposition.py` | |
| `system_integration/phase3/`, `gsa/`, `convergence/`, `diagnostics/`, `validation_*/` | respective drivers | |

### 10.2 `hwl_bias_resolution/` is evidence, not a cache

It carries the resolved design-HWL bias at KP 62.0 (26.9, 95% CI [21.6, 35.3], on
63 failing rows) and the pre-registered validation *failure* of the ADR-0029
tilted sampler for a ratio between branches. **A 170-minute re-run is not a
substitute for the artifact a reviewer may ask to see**, and a regenerated file
is not the file the manifest hashed. Retain it until the defence regardless of
its size.

### 10.3 Regenerable, deletable at any time

* `system_integration/hazard_cache/` -- a pure cache; rebuilds in about 4 minutes.
* `phase2_selftest/`, `phase2_test_xs_historical.*` -- development-time self-test
  at reduced N; deletable after the defence.

### 10.4 `superseded_*` directories

`scripts/production_campaign.py` preserves what it supersedes into
`results/superseded_<timestamp>/`. These are **not** regenerable: they *are* the
pre-supersession state.

* `superseded_adr0047_L47/` is retained until the defence. It is the pre-adoption
  L = 47 m state that ADR-0047's withdrawn-arm numbers were measured against, and
  a question about the adoption decision is foreseeable.
* A timestamped `superseded_*` directory is retained until the artifact that
  superseded it has been quoted in a defended chapter, then for one further
  campaign cycle.
* **Empty ones may be removed at any time.** The driver creates the directory
  before knowing whether it has anything to preserve, so most are empty: 11 of 15
  on 2026-07-31, all of which were removed after asserting each was empty in the
  same operation. Assert emptiness immediately before removing; never remove a
  `superseded_*` directory that contains files without checking it against this
  policy first.
