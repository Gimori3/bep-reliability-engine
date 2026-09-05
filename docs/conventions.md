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
sole authoritative thesis is `msc-thesis`.

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
content. The check that keeps it that way is documented in the msc-thesis project rules.

**No em dashes; ranges are written "X to Y", never "X-Y" or an en dash.** See
the msc-thesis project rules for the full style contract (citation-key preservation,
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
  campaign, an audit, a document review. They are frozen records of one pass and
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
| `NNNN-slug.md` | A numbered **decision** (ADR). 0001 to 0051, gap-free. Superseded ADRs stay in place with their Status line updated; they are never deleted or renamed. |
| `adrNNNN-slug.md` / `.json` | **Evidence for** the ADR of that number: a companion analysis note, an evidence JSON, or both. Note the grammar differs from the ADR's own filename (lowercase `adr` prefix, no separating dash). |
| `<topic>-study.md`, `<topic>-synthesis.md` | An **un-numbered study**: work that produced a finding but changed no default and therefore consumed no ADR number (`seepage-length-L-study.md`, `r10-foreshore-exhaustion-screening.md`, `epistemic-bracket-synthesis.md`, `m7-pol-ode-reference-values.md`). |

Do not "unify" these. The audit measured a restructure at **293 reference lines
across 84 files** (66 tracked, 18 in the gitignored untracked supporting files),
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

### 9.3.1 A main-body figure prints no engine-internal identifier and no em dash

Thirty of these figures are placed in the **main body** of the thesis. Its binding
rules exclude ADR identifiers, any narration of the project's own evolution, and all
software and computer-science vocabulary from Chapters 1 to 9, and its style rules
forbid the em dash "anywhere" while stating explicitly that they cover "figures,
figure and table captions". A caption can be rewritten in the thesis repository;
**text rendered into the PNG cannot**, so it has to be right here. The thesis's own
prescribed scans are `.tex` scans and cannot see inside a PNG, which is why this went
unnoticed for seven drafting sessions.

**The rule.** No text rendered into a main-body figure (title, suptitle, axis label,
tick label, legend entry, annotation, in-plot text) carries any of:

| Offence | Rendered instead |
|---|---|
| `ADR-00xx`, `spec §N` | the physical or statistical reason the decision encodes |
| module identifiers `M1` to `M9` | the thesis's own name for the step (`M4` is "hydraulic translation") |
| failure-mode tags `fm5`, `fm7` | the effect itself ("the C_e x k_aq interaction") |
| file and data formats `CSV`, `HDF5`, `JSON` | the source ("1998 survey", "tabulated value") |
| run and config identifiers `tokachi_kp58.8`, a policy name, a `.png` filename | `KP 58.8`, via `scripts/_figstyle.py::section_label` |
| snake_case record field names | plain English, via a per-driver display map |
| "engine" meaning the implementation | "model", "production", or drop |
| literal em dash U+2014 | a comma, colon or full stop; ranges become "X to Y" |

**A record field name is never renamed to satisfy this.** The keys are the evidence
JSON's own schema and are load-bearing; the substitution happens at render time
through a display map beside the plotting code (`ARM_DISPLAY_NAMES`,
`LADDER_DISPLAY_NAMES`, `CASE_DISPLAY_NAMES`, `RUN_DISPLAY_NAMES`). One of these
was caught by `test_thesis_figure_gaps.py` precisely because the first attempt
edited the field rather than its rendering.

A file *name* beginning `adr…` is not a violation: it never appears in the compiled
PDF, and renaming one would break `\includegraphics` in two chapters plus every
`FIGURE_DRIVERS` `produces` entry. Only rendered text is in scope.

**Executed 2026-08-04** across all 30 main-body figures: 22 were dirty, 8 clean, and
all 30 now pass a visual re-read. The rule is **not** enforced by a test, because a
PNG holds no extractable text; the source-side sweep in that session's record is
necessary and not sufficient, so a new main-body figure must be opened and read.

**Amended 2026-08-05, and the gap is instructive.** That sweep enumerated *plan
section 3.2's* 30 figures, and the five Phase 2 figures promoted two days earlier
(2026-08-02) were not in that list, so they were never inspected. Two of them
reached the main body carrying exactly the offences the table forbids:
`phase2_fragility_update_kp58_8_matrix.png` printed the run stem
`tokachi_kp58.8_historical_matrix` as its suptitle, and `phase2_peak_shortcut.png`
printed the repository path `docs/phase2_report.md section 11.1` in a footnote.
Both are fixed. **The lesson is that "the 30 figures" is a list, not a set closed
under promotion**: promoting a figure into the main body brings it into scope, and
the same sentence already says so for appendix figures.

The package-side substitution mirrors `section_label` rather than importing it, since
`bayesian_reliability_updating` must not depend on `scripts/`:
`pipeline.STEM_DISPLAY_NAMES` plus `pipeline.display_label`, keyed on the same run
stems as `PUBLICATION_FIGURES`, with **an unrecognised stem returned unchanged**.
That last property is load-bearing twice: the six non-promoted strata keep their
stem in the run-local diagnostic title, and an ADR-0046 `z_toe` scenario (whose stem
carries a `_ztoe_*` suffix) keeps the suffix in its title as well as finding no
publication entry, so a scenario cannot be mistaken for the baseline on either axis.

**Appendix figures are out of scope** and deliberately still carry these items:
`adr0031-tail-lhs-vs-crude*.png` (em dash, `fm5`), `epistemic_knobs_mp_ztoe.png`,
`stage6_6_heq_*.png` and `adr0040_tilted_is_validation.png` (ADR numbers), and
`ce_prior_reconciliation.png` (`(ADR-0026)`). Binding rules 2 and 3 are scoped to
Chapters 1 to 9, and an ADR pointer in an appendix figure has been judged acceptable.
If one of those figures is ever promoted to the main body, it comes into scope.

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

**The same rule binds a driver gate, added 2026-08-10.** A gate in `scripts/`
that records a "did not verify" status and then continues is the same defect
wearing different clothes, and the two AST guards above cannot see it -- each
parses only the test file it lives in. If a driver checks something before
overwriting a guarded artifact, a non-verifying outcome must **refuse**: non-zero
exit, before the write. Permitting it anyway is an explicit opt-out flag named
for what it permits (`--allow-unverified`, `--allow-stub`), never a default, and
the run's own record says the flag was used.

Which side of the write the gate sits on is direction-dependent, and both
directions are in force here. Gate **after** the write when the write *creates*
evidence -- the 2026-07-30 hardening, applied twice after a gate discarded 2.5 h
of a run it was raised about. Gate **before** the write when the write
*overwrites* a guarded record, as `stage6_6_gap_decomposition.py` does over
`results/stage6_6/` and the tracked `docs/figures/` copies. The rule underneath
both is the same: never let a gate destroy the evidence it exists to protect.

**A recorded unresolved outcome needs a paired check, added 2026-08-10.** The
two paragraphs above are both scoped to a write, and the third instance of this
class had none: `production_campaign.py::enumerate_companions` greps for
consumers of the persisted sweeps and reached the manifest only through
`gates.note`, so a hit it could not classify was written down as `UNCLASSIFIED
-- investigate` and could never fail anything. Three accumulated across four
sessions. Where a gate framework distinguishes an observation from an
assertion, **keep both and pair them**: the note carries the evidence into the
manifest, the check refuses. A field whose value can say "I found something
nobody has accounted for" is an assertion wearing a note's clothes. Prefer the
cheap side -- a verdict decidable from source alone belongs before the
subprocesses it guards, where refusing costs milliseconds and destroys nothing.

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
