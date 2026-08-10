# Repository structural audit — 2026-07-31

**Status:** Phase 1 deliverable (read-only inventory and proposal), **approved and
executed 2026-07-31**. Sections 1 to 8 below record the tree *as audited*, before
execution, and are left unedited so the measurements that justified each verdict
stay legible. What was actually done, with three owner amendments, is recorded in
section 11 at the end of this document and in the commit series it names.

When this document was produced it was strictly read-only: no file outside it was
created, moved, renamed or deleted while producing it.

**Baseline.** Working tree verified clean before any inspection
(`git status --porcelain` returned 0 lines). Branch `feature/tokachi-chisuishi-review`,
HEAD `88d55ddab1412790e4a88afaa819ac7f8e926bec`. 371 tracked files, 15.9 MB tracked.

**Scope note.** Per the task guardrails this audit never touches `data/`,
`docs/references/`, `results/`, `.git/`, any numbered ADR or evidence JSON. Where a
finding lands inside one of those, it is recorded here as a flag for the owner and
nothing more.

---

## 1. Tracked footprint by directory

| Directory | Files | Size |
|---|---:|---:|
| `docs/decisions/` | 88 | 2 631 KB |
| `docs/figures/` | 52 | 6 840 KB |
| `docs/` (top level) | 19 | 679 KB |
| `docs/validation/` | 8 | 78 KB |
| `docs/work packages/` | 2 | 28 KB |
| `scripts/` | 44 | 840 KB |
| `tests/` | 40 | 635 KB |
| `bep_reliability_engine/` | 19 | 508 KB |
| `bayesian_reliability_updating/` | 13 | 134 KB |
| `system_integration/` | 11 | 118 KB |
| `configs/` (+ 2 stub dirs) | 10 | 38 KB |
| `data/processed/` (+ 4 subdirs) | 23 | 1 987 KB |
| `data/digitized/` (+ 1 subdir) | 21 | 417 KB |
| `figures/` (repo root) | 11 | 932 KB |
| `notebooks/` | 2 | 4 KB |
| `.github/workflows/`, `.vscode/`, root | 8 | 12 KB |
| **Total** | **371** | **15.9 MB** |

`project-notes.md` sits at the repository root but is **gitignored** (`.gitignore:239` — the
task brief said `:237`; the line has drifted by two). It is therefore absent from
every count above and from every diff.

---

## 2. The path-coupling map (measured, not assumed)

This is the constraint that governs every MOVE/RENAME verdict below. Four distinct
mechanisms bind behaviour to file paths.

### 2.1 `tests/test_figure_pass.py` — document paths hard-coded

**A correction to the task brief's framing, and it changes the risk direction.** The
brief states that renaming one of these documents makes the test "fail on a
file-not-found". That is true for three of them and *false* for the other five, which
is worse:

| Document path | Test | Behaviour if moved |
|---|---|---|
| `docs/architecture.md` | `test_the_tilted_sampler_...`, `test_the_cancellation_rule_...` | **Hard failure** — `read_text()` with no guard |
| `docs/decisions/0029-timestepper-acceleration-and-tail-estimator.md` | `test_the_tilted_sampler_...` | **Hard failure** |
| `docs/decisions/0048-prior-mean-epistemic-scenarios.md` | `test_the_cancellation_rule_...` | **Hard failure** |
| `docs/decisions/epistemic-bracket-synthesis.md` | `test_the_cancellation_rule_...` | **Hard failure** |
| `docs/production_campaign_2026-07-29.md` | `test_every_euler_flip_claim_...` | **SILENT SKIP** (`pytest.skip` at line 243) |
| `docs/stage6_6_report.md` | same | **SILENT SKIP** |
| `docs/decisions/0040-stage6-6-comparator-ladder-gap-decomposition.md` | same | **SILENT SKIP** |
| `docs/decisions/adr0047-dem-seepage-length.md` | same | **SILENT SKIP** |
| `docs/decisions/0047-dem-surveyed-seepage-length.md` | same | **SILENT SKIP** |

`test_every_euler_flip_claim_carries_the_N_at_which_it_holds` is parametrised over
`EULER_CLAIM_FILES` and opens with `if not path.is_file(): pytest.skip(...)`. Moving
any of those five turns its guard into a no-op **and the suite still reports green**.
The N-qualification claim it protects was added on 2026-07-30 precisely because the
unqualified form had survived unnoticed in five documents. A move that disables the
guard silently re-opens that hole.

Two evidence JSONs are also read by path: `docs/decisions/adr0040-hwl-bias-resolution.json`
and `docs/decisions/epistemic-bracket-synthesis.json` (both skip-guarded), plus
`docs/decisions/adr0039-timestep-stress.json` and `docs/figures/*.png` via glob.

### 2.2 Gate G7 — `FIGURE_DRIVERS` in `scripts/production_campaign.py`

19 declared drivers, each carrying `requires` / `produces` / `sources` **as literal
path strings**. 16 distinct `docs/` paths appear:

```
docs/decisions/adr0012-kaq-d70-analysis.md      docs/decisions/adr0039-timestep-stress.json
docs/decisions/adr0025-foreshore-sensitivity.json  docs/decisions/adr0040-hwl-bias-resolution.json
docs/decisions/adr0029-tail-cov-study.json      docs/decisions/adr0044-event-closure-bound.json
docs/decisions/adr0031-convergence-study.json   docs/decisions/adr0047-dem-seepage-length.json
docs/decisions/adr0031-convergence-study*.json  docs/decisions/epistemic-bracket-synthesis.json
docs/decisions/adr0032-aquifer-response-diagnostic.md
docs/decisions/adr0033-gsa-study-kp58_8_matrix.json   docs/decisions/r10-foreshore-exhaustion-screening.json
docs/decisions/adr0033-gsa-study-kp60_0_matrix.json   docs/decisions/seepage-length-L-study.md
docs/decisions/adr0033-gsa-study*.json                docs/figures/
```

Two tests enforce that these resolve (`test_declared_figure_sources_resolve_to_real_paths`,
`test_figure_driver_requires_paths_exist_or_are_gitignored_data`) — but **only for
patterns beginning `docs/`**; `results/` and `data/raw/` are exempt as gitignored.
A `docs/` move that is not mirrored into `FIGURE_DRIVERS` fails loudly. Good.

`test_every_tracked_publication_figure_is_declared` asserts **52 of 52** tracked
figures are declared. Adding or removing a file under `docs/figures/` without touching
`FIGURE_DRIVERS` fails.

### 2.3 `results/production_campaign_manifest.json` — SHA-256 locks

The manifest records SHA-256 for its stage outputs. Beyond `results/`, it hashes:

* **8 config YAMLs** — `configs/kp{57_4,58_8,60_0,62_0}_historical_{matrix,bulk}.yaml`
* **4 tracked evidence JSONs** — `docs/decisions/adr0025-foreshore-sensitivity.json`,
  `adr0044-event-closure-bound.json`, `adr0047-dem-seepage-length.json`,
  `r10-foreshore-exhaustion-screening.json`
* **7 figure basenames** under `docs/figures/`

Those 12 tracked paths must not move or change content. This alone forecloses any
`docs/decisions/` reorganisation that relocates evidence JSONs.

### 2.4 Dual-write, and the `untracked-supporting-files/` blind spot

Figure drivers write **both** `results/<study>/figures/` and tracked `docs/figures/`
(`scripts/_figstyle.py::save`, pinned by `test_figstyle_save_writes_the_tracked_publication_copy`;
`stage6_6_gap_decomposition._write_figure`, pinned by
`test_the_stage6_6_driver_writes_the_tracked_publication_copy`). This is the structural
fix for the human-copy failure that let the KP 62.0 set go stale twice. **Not touched
by any proposal below.**

`untracked-supporting-files/` holds 15 guides across 30+ files. **18 guide files cite
`docs/decisions/` paths across 132 lines.** The directory is gitignored, so no diff
and no test covers it — a stale guide pointer is invisible. One such pointer already
exists (§5.2).

---

## 3. Verdicts

### 3.1 DELETE — root `figures/` (11 tracked PNGs, 932 KB)

**Established by grep, not assumed.** Three independent lines:

1. **Nothing writes to it.** `scripts/gsa_study.py:155-156` writes
   `results/figures/{name}.png` **and** `docs/figures/{name}.png`.
   `scripts/plot_validation_yabe.py:23` and `plot_validation_shikaga.py` set
   `FIG_DIR = REPO / "docs" / "figures"`. No script in the repository resolves to a
   bare root `figures/`.
2. **Nothing reads it.** A repo-wide path scan over 371 tracked files + 30 guide files
   + `project-notes.md` + the msc-thesis tree returns **zero** references to root `figures/`.
   The seven apparent hits are all false positives: four are the *thesis's own*
   `figures/` directory (msc-thesis carries its own copies and includes them as
   `figures/...` relative to *its* root), one is
   `bayesian_reliability_updating/pipeline.py:130` building `out_dir / "figures"` under
   `results/`, and two are prose. Every `../figures/` in `docs/decisions/*.md` resolves
   to `docs/figures/`.
3. **Every byte is duplicated.** SHA-256 compared 11/11 against
   `docs/figures/<same name>`: **IDENTICAL, 11 of 11.**

They are frozen at mtime 2026-07-12 (commits `c3126b6`, `f284da8`) while
`docs/figures/` is regenerated by gate G7 — identical today, guaranteed to diverge
silently at the next regeneration. They are also **outside G7's coverage**: G7 gates
`docs/figures/` only, so a stale root copy would never be caught.

| Verdict | Surviving copy | Regenerated by |
|---|---|---|
| DELETE (`git rm`) ×9 `gsa_*.png` | `docs/figures/<same>` | `python scripts/gsa_study.py --plot-only` |
| DELETE (`git rm`) `validation_yabe_timeline.png` | `docs/figures/<same>` | `python scripts/plot_validation_yabe.py` |
| DELETE (`git rm`) `validation_shikaga_m4_pattern.png` | `docs/figures/<same>` | `python scripts/plot_validation_shikaga.py` |

Reference-update cost: **zero files**. Risk: **none identified.**

### 3.2 DELETE — `notebooks/notebooks/` (empty, untracked)

Confirmed empty (`0` entries, recursive, `-Force`) and **untracked** — git does not
track empty directories, so it appears in no `git ls-files` output and `git rm` does
not apply. Removal is an untracked-directory removal, not a tracked-file deletion.
Zero references. Cost: zero.

### 3.3 DELETE (optional) — `configs/base/.gitkeep`, `configs/experiments/.gitkeep`

Two scaffold directories from 2026-05-21 that never received content. **Zero
references anywhere** (searched `.py`, `.md`, `.yaml`, `.toml`, `.ipynb` — `NONE`).
Configs are generated flat into `configs/` by `scripts/generate_configs.py`; the
`base/` + `experiments/` split was never implemented. Leaving them invites a future
session to assume configs belong there.

The other five tracked `.gitkeep` files (`docs/`, `docs/decisions/`, `notebooks/`,
`scripts/`, `data/processed/`) sit in directories that now hold 23 / 87 / 2 / 44 / 7
entries respectively. They are inert. `data/processed/.gitkeep` is untouchable.
**Recommendation: remove only the two `configs/` stubs; leave the rest** — removing
inert placeholders from populated directories buys nothing and costs a commit.

### 3.4 MARK SUPERSEDED — 6 documents

The default verdict for obsolete-but-meaningful material. Content unchanged; each
gains a dated header naming its replacement. No moves, so **no path coupling is
touched**.

| File | Cited by | Header should point to |
|---|---:|---|
| `docs/close_out_2026-07-12.md` | 2 tracked, 4 guides | §3 blocker manifest superseded by `docs/phase3_report.md` §9; campaign superseded by `docs/production_campaign_2026-07-29.md` |
| `docs/phase2_interface.md` | 4 tracked | Interface as-built: `docs/phase2_report.md` + `bayesian_reliability_updating/README.md`. Carries 4 stale `results/tokachi_kp58_historical.*` paths (§5.4) |
| `docs/work_packages/dem-seepage-length.md` | **0** | Work completed: ADR-0047 + `docs/decisions/adr0047-dem-seepage-length.md`; adoption executed 2026-07-29 |
| `docs/pol_meeting_briefing.md` | **0** | Meeting held 2026-07-07; outcomes in `docs/validation/pol-meeting-2026-07-07-dispositions.md` and ADR-0026/0027/0028 |
| `docs/joost_pol_meeting_vragen.md` | 1 tracked | same |
| `docs/validation/reference-anchor-worksheet.md` | **0** | Superseded by `docs/validation/reference-anchor-status.md` (cited by 4) |

### 3.5 MARK SUPERSEDED (status header only) — 2 `docs/validation/` items

Both flagged in the task brief; neither should be deleted, and **neither should be
renamed**.

* **`head-datum-re-convention-CLOSED.md`** — the filename carries a rename artifact
  (`OPEN-` → `-CLOSED`, commit `08267ee`, `R100` = 100 % similarity). *Recommend
  leaving the filename alone* and adding a status header instead. Renaming it would
  require editing **ADR-0027, which guardrail 3 forbids** (§5.1), and the file is
  already cited under its current name by 2 tracked files + 1 guide.
* **`tokoro-case-plan.md`** — a plan for a deferred case. Its two "dangling" paths
  (`scripts/validate_tokoro.py`, `docs/validation/tokoro-case.md`) are *prospective*,
  not broken. A `PLANNED — NOT EXECUTED` header converts them from apparent rot into
  declared future work.

### 3.6 DOCUMENT INSTEAD — `docs/decisions/` restructure (**recommend against**)

The four naming grammars are real:

| Grammar | Count | Example |
|---|---:|---|
| Numbered ADR `NNNN-slug.md` | 48 | `0047-dem-surveyed-seepage-length.md` |
| Companion `adrNNNN-slug.{md,json}` | 32 | `adr0040-hwl-bias-resolution.json` |
| Un-numbered study | 5 | `seepage-length-L-study.md`, `r10-foreshore-exhaustion-screening.{md,json}`, `m7-pol-ode-reference-values.md` |
| Un-numbered synthesis | 2 | `epistemic-bracket-synthesis.{md,json}` |
| Template + `.gitkeep` | 2 | `ADR_TEMPLATE.md` |

ADR numbering is **complete and gap-free, 0001–0048**. The grammar is already
documented and internally consistent (numbered = decision, `adr`-prefixed = evidence
for that decision, un-numbered = study that changed no default — a distinction
`seepage-length-L-study.md` states in its own header).

**Measured cost of any restructure:**

| Reference class | Files | Lines |
|---|---:|---:|
| Tracked files citing `docs/decisions` | 66 | 161 |
| `untracked-supporting-files/` files citing it | 18 | 132 |
| **Total** | **84** | **293** |

plus: **12 SHA-256-locked manifest entries** (§2.3, of which 4 are decisions JSONs),
**16 G7 `requires`/`sources` literals** (§2.2), **6 hard-coded paths in
`test_figure_pass.py`** of which 3 fail loudly and 3 skip silently (§2.1), and the
thesis Appendix C ADR register. `scripts/` alone contains **19 drivers that construct
`docs/decisions/` output paths at runtime** (`hwl_bias_resolution.py` at 6 sites,
`production_campaign.py` at 25).

**Recommendation: do not restructure. Document the grammar in `docs/conventions.md`
instead.** 293 lines of edits across 84 files, four of them SHA-256-locked, to make a
consistent-and-already-explained convention look tidier, is a bad trade in a
defence evidence base. The convention is not the problem; the absence of a written
statement of it is, and that costs one paragraph.

### 3.7 DOCUMENT INSTEAD — `docs/audits/` subdirectory (**recommend against**)

The dated one-shot audit artifacts are a real and growing category (6 files, 281 KB):

| File | Cited by |
|---|---:|
| `production_campaign_2026-07-29.md` | 4 tracked (incl. `test_figure_pass.py`), 1 guide |
| `number_audit_2026-07-30.md` | 1 tracked, 1 guide |
| `thesis_number_inventory_2026-07-30.md` | 1 tracked, 1 guide |
| `thesis_fragment_retirement_2026-07-29.md` | **0** |
| `tokachi_basin_document_review_2026-07-27.md` | 7 tracked |
| `tokachi_chisuishi_full_review_2026-07-27.md` | 1 tracked |

They have the best claim of any group to their own home. **I still recommend against
moving them**, on one specific finding: `docs/production_campaign_2026-07-29.md` is in
`EULER_CLAIM_FILES`, and that test **skips silently** on a missing path (§2.1). Moving
it disables a guard installed one day ago to close a hole that had gone unnoticed
across five documents — and the suite stays green, so nothing tells you.

The cost is not merely the 13 inbound citations; it is that the *cheapest* mitigation
(update the test's constant) is also the one a future session will forget, because the
failure mode gives no signal. The dated-filename convention (`<topic>_<YYYY-MM-DD>.md`)
already sorts these together in a directory listing and already distinguishes them from
the six documents of record.

**Recommendation: state the two-category convention in `docs/conventions.md`** — that
undated `docs/*.md` are documents of record and dated `docs/*_YYYY-MM-DD.md` are
closed one-shot artifacts — and leave the files where they are. If the owner
nonetheless wants the move, it must be paired with hardening
`test_every_euler_flip_claim_carries_the_N_at_which_it_holds` to **fail** rather than
skip on a missing path; I would not execute the move without that change.

### 3.8 DOCUMENT INSTEAD — `docs/work packages/` (2 files, 0 inbound refs)

`build_r10_tier1_foreshore_exhaustion.md` and `mine_tokachi_chisuishi_816pp.md` are the
task briefs that produced the R10 screening indicator and the 816-page Chisuishi
review. Nothing cites them, but both are cited *outward* by their products
(`r10-foreshore-exhaustion-screening.md`, `tokachi_basin_document_review_2026-07-27.md`).
They are provenance for two executed studies. Leave; note the directory's purpose in
`docs/conventions.md`.

### 3.9 KEEP

* **`notebooks/gsa_study.ipynb`** — assessed against the "thin drivers only, no
  physics in cells" rule. **Compliant, and unusually explicit about it**: cell 1
  states "Thin driver (spec section 9: no physics in notebooks)". The four code cells
  load JSONs from `results/gsa/`, call `gsa_study._plot_section` (a *script* function),
  display images, and tabulate with pandas. No physics.
* All of `bep_reliability_engine/`, `bayesian_reliability_updating/`,
  `system_integration/`, `tests/`, `scripts/`, `configs/*.yaml`, `.github/`, `.vscode/`,
  `pyproject.toml`, `.pre-commit-config.yaml`, `CITATION.cff`, `LICENSE`.
* `docs/architecture.md`, `conventions.md`, `phase2_report.md`, `phase3_report.md`,
  `stage6_6_report.md`, `tokachi_bep_inputs_provenance.md` — the six documents of
  record, correctly located. `architecture.md`'s revision note is **current** through
  ADR-0048 plus the two non-numbered companions (checked; not stale).
* `docs/figures/` (52 PNGs) — canonical publication location, G7-gated, 52/52 declared.
* `docs/validation/` — 8 files, all load-bearing negative/validation records.
* All of `data/` — untouchable by guardrail and correct as-is.

### 3.10 KEEP, but README.md is materially incomplete

`README.md` is **4 lines** and describes only the install command. It does **not**
describe the as-built three-package repository. For a defence evidence base whose
entire value is traceability, the front door does not say what the repository
contains, that `bep_reliability_engine` / `bayesian_reliability_updating` /
`system_integration` are three packages in one dependency direction, that
`docs/architecture.md` is the authoritative spec, or that `results/` and `data/raw/`
are gitignored and machine-local.

This is the one **addition** I would propose rather than a rearrangement, and it is
the highest-value item in this audit. Roughly 40 lines: the three packages and their
direction, the three entry-point commands, where the documents of record live, and
what is gitignored. Purely additive; no path coupling touched.

---

## 4. Files nothing references (candidates, not verdicts)

Determined by scanning the whole tracked tree + `untracked-supporting-files/` + `project-notes.md` +
msc-thesis for each file's basename. **A zero here is a signal to check, not grounds
to delete** — a terminal record legitimately has no inbound pointers.

| File | Assessment |
|---|---|
| `figures/*.png` ×11 | **Genuinely unreferenced.** → DELETE (§3.1) |
| `docs/work_packages/dem-seepage-length.md` | Completed handoff → MARK SUPERSEDED (§3.4) |
| `docs/pol_meeting_briefing.md` | Meeting held → MARK SUPERSEDED (§3.4) |
| `docs/validation/reference-anchor-worksheet.md` | Superseded by `-status.md` → MARK SUPERSEDED (§3.4) |
| `docs/thesis_fragment_retirement_2026-07-29.md` | **KEEP.** Terminal record of a closed action whose rule now lives in tracked `docs/conventions.md` §8 and `tests/test_repo_hygiene.py`. Zero inbound is correct here. |
| `docs/work packages/*.md` ×2 | Provenance for two executed studies → KEEP (§3.8) |
| `configs/base/.gitkeep`, `configs/experiments/.gitkeep` | Inert scaffold → DELETE, optional (§3.3) |

---

## 5. References pointing at paths that do not exist

A repo-wide scan produced 67 raw candidates; after removing template placeholders
(`NNNN`, `00NN`, `adrXXXX`), line-wrap truncations, gitignored `results/` and
`data/raw/` targets, and paths relative to the gitignored Uemura drop
(`data/df_river.csv`), **five genuine classes remain.**

### 5.1 ADR-0027 → a file renamed 18 days ago  *(blocked by guardrail 3)*

```
docs/decisions/0027-raw-outer-head-erosion-driver.md:27
docs/decisions/0027-raw-outer-head-erosion-driver.md:153
    -> docs/validation/OPEN-head-datum-re-convention.md
```

The file was renamed to `docs/validation/head-datum-re-convention-CLOSED.md` in commit
`08267ee` (`R100`, a pure rename). Both pointers have been dangling since.

**This is a genuine defect and I cannot fix it under the stated guardrails** —
guardrail 3 forbids touching any numbered ADR "at all". It is a two-line pointer
correction inside ADR-0027's Context and References sections, changing no decision, no
number and no status. **It needs an explicit owner decision to proceed.** Flagging it
rather than silently leaving it, because ADR-0027 is one of the load-bearing head-datum
decisions and a reader following its own References section currently hits nothing.

### 5.2 A stale `untracked-supporting-files/` pointer *(fixable, invisible to every test)*

```
untracked-supporting-files/bep-thesis-writeup-campaign/stale-numbers.md:80
untracked-supporting-files/bep-thesis-writeup-campaign/stale-numbers.md:81
    -> docs/decisions/ce-prior-study.md          (actual: adr0026-ce-prior-study.md)
```

Exactly the failure mode the task brief warned about: `untracked-supporting-files/` is gitignored,
so this appears in no diff and no test. Two occurrences, both in the same table.

### 5.3 Stale illustrative paths in `docs/architecture.md`

```
docs/architecture.md:476 -> configs/tokachi_kp58.yaml
docs/architecture.md:478 -> results/tokachi_kp58_historical.h5
```

Example paths in the §9 package-layout section, written before the
`kp58_8_historical_matrix` naming settled. Cosmetic; they illustrate a shape rather
than cite an artifact. Low priority — but `architecture.md` is the authoritative spec,
so a two-token correction is cheap.

### 5.4 Stale artifact paths in `docs/phase2_interface.md` (×4)

Lines 44, 45, 138, 408 cite `results/tokachi_kp58_historical.h5` / `.json`, which never
existed under that name. Covered by the MARK SUPERSEDED header proposed in §3.4 — the
header explains the document pre-dates the built Phase 2 package, which is the real
fix; rewriting its body is out of scope (guardrail 5).

### 5.5 Prospective paths in `docs/validation/tokoro-case-plan.md` (×2)

`scripts/validate_tokoro.py`, `docs/validation/tokoro-case.md`. Not rot — deferred
work. Covered by the status header in §3.5.

### 5.6 Two non-defects, recorded so they are not re-investigated

* `docs/number_audit_2026-07-30.md:364,379` → `docs/decisions/adr0033-gsa-study.json`
  is **not dangling**: the document is explicitly *recording that this path does not
  exist* (the GSA evidence is per-section), which is why the G7 driver pointed at a
  dead `requires` and silently skipped its nine figures.
* `tests/test_hydrographs.py:3` → `tests/test_m3.py` is a correct past-tense reference
  to a deleted predecessor suite ("These tests supersede the interface-first
  `tests/test_m3.py` suite").

---

## 6. Flags — items I may not touch, recorded for the owner

### 6.1 `data/processed/2006_event/` — undocumented where a reader will look

Confirmed present with five Japanese-named subdirectories, four empty and one holding
a single `rain.xlsx`. **Untouchable** (guardrail 3, and gitignored at
`.gitignore:252`).

Its status **is** documented — in ADR-0044, thoroughly (lines 17, 27, 39-40, 88, 140:
closed "for lack of any constructible observation"). It is **not** mentioned anywhere
in `docs/tokachi_bep_inputs_provenance.md` (zero hits for "2006").

The real asymmetry is narrower and more actionable than "undocumented": its two
sibling event directories each carry a **tracked** README —
`data/processed/2011_event/README.md` and `data/processed/2016_event/README.md` — and
`2006_event/` does not. A future session that opens the tree before reading ADR-0044
sees two documented event drops and one bare directory of empty Japanese-named folders.
**Recommend the owner add `data/processed/2006_event/README.md`** (three lines: drop
received, stage record empty, closed by ADR-0044). I have not created it.

### 6.2 A docstring/code mismatch in `tests/test_repo_hygiene.py`

`test_no_thesis_source_anywhere_in_the_tracked_tree`'s docstring states
"`docs/references/` is excluded because it holds gitignored reference PDFs", but
`skip_dirs` is `{".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}`
— `docs/references/` is **not** excluded. The test passes only because that directory
happens to contain no `.tex`/`.bib`/`.cls`/`.sty`/`.bbl`. Harmless today; the docstring
claims a guarantee the code does not implement. Not in scope for a structural cleanup;
recorded so it is not mistaken for correct.

### 6.3 A cosmetic naming inconsistency inside one companion pair

`docs/decisions/adr0029-tail-cov-study.json` and
`docs/decisions/adr0029-tail-variance-study.md` are the evidence and note for the same
study under two different slugs. The JSON name is load-bearing (G7 `requires` and
`sources`, §2.2). **Recommend leaving both**; renaming either buys nothing and the JSON
is gate-coupled.

---

## 7. UNCERTAIN

| Item | What is unresolved |
|---|---|
| ADR-0027's two dangling pointers (§5.1) | Whether guardrail 3 may be relaxed for a two-line pointer fix that changes no decision. **Owner decision required.** |
| `results/superseded_*` retention | 15 directories exist (the brief said 13 — two more were created 2026-07-31 during the figure pass). 11 of 15 are **completely empty**. Whether the empty ones are a `production_campaign.py` defect (creating a preservation directory before knowing there is anything to preserve) or intended provenance markers is **not established**; I did not read the preservation code path closely enough to assert either. Phase 3 proposal treats them conservatively. |

---

## 8. Verdict summary

| Verdict | Items | Reference-update cost |
|---|---:|---|
| KEEP | 349 tracked files | — |
| DELETE (`git rm`) | 11 root PNGs + 2 optional `.gitkeep` | 0 files |
| DELETE (untracked dir) | `notebooks/notebooks/` | 0 files |
| MARK SUPERSEDED | 8 documents (6 in `docs/`, 2 in `docs/validation/`) | 0 files (headers only, no moves) |
| DOCUMENT INSTEAD | `docs/decisions/` grammar; the dated-audit convention; `docs/work packages/` purpose | 1 file (`docs/conventions.md`) |
| MOVE / RENAME | **none proposed** | — |
| UNCERTAIN | 2 | — |

**No MOVE or RENAME is proposed.** Every candidate was measured against §2 and none
cleared the bar. The three groups that looked most movable — the audit artifacts, the
`docs/decisions/` grammars, and the `-CLOSED` rename artifact — are each recommended
against with the specific cost named in §3.6, §3.7 and §3.5.

---

## 9. Recommended execution order (zero-risk first)

1. **`git rm` the 11 root `figures/*.png`.** Zero references, byte-identical survivors,
   three regeneration commands recorded. Then `pytest`.
2. **Remove the empty untracked `notebooks/notebooks/`.** Zero coupling.
3. **`git rm` the two `configs/` `.gitkeep` stubs** (optional).
4. **Add the 8 superseded headers.** Content-only edits, no moves, no path coupling.
5. **Fix the `untracked-supporting-files/` stale pointer** (§5.2) — 2 lines, invisible to CI, so it
   will not be caught later.
6. **Fix `docs/architecture.md`'s two stale example paths** (§5.3) — optional.
7. **Write the conventions additions** (§3.6, §3.7, §3.8) + the Phase 3 retention policy
   into `docs/conventions.md`.
8. **Expand `README.md`** to describe the as-built three-package repository (§3.10).
9. **Path-integrity gate**: `pytest` (**628 expected — measured 2026-07-31, not the 625
   of 2026-07-30**; the figure pass added three), `ruff check .`, `black --check .`,
   `python scripts/production_campaign.py` manifest/dry-run with G7 resolving, every
   `scripts/*.py --help`, every relative path in `docs/`, ADRs, `README.md`, `project-notes.md`
   and `untracked-supporting-files/*.md`.

Steps 1-3 are independent and reversible. Steps 4-8 touch no path that any test, gate
or manifest binds to.

---

## 10. Phase 3 — `results/` retention policy (proposal only; nothing deleted)

`results/` is gitignored and machine-local: **723 files, 2 119 MB.**

| Category | Files | MB | Regenerable by | Recommended retention |
|---|---:|---:|---|---|
| **8 production sweeps** (`tokachi_kp*.h5` + `.json`) | 16 | 88.6 | `python scripts/run_sweep.py configs/kp*_matrix.yaml` (~hours) | **PERMANENT — must survive to the defence.** SHA-256-locked in the manifest. Every Phase 2/3 number descends from these. |
| `production_campaign_manifest.json` + `production_campaign/` | 50 | 1.9 | `python scripts/production_campaign.py` | **PERMANENT.** The document of record's machine-readable half. |
| `hwl_bias_resolution/` (two N = 1e6 ladders) | 32 | **839.3** | `python scripts/hwl_bias_resolution.py` (~2.5 h/section) | **PERMANENT until the defence.** Largest single category, and the *most* expensive to reproduce; it carries the resolved 26.9 [21.6, 35.3] and the tilted-IS validation failure. |
| `sensitivity/` (ADR-0045/0046/0048, `ce_prior`, `seepage_length`, `foreshore_exhaustion`) | 86 | 394.9 | each companion driver, individually | **PERMANENT until the defence.** Headline numbers in `epistemic-bracket-synthesis.md` cite these. |
| `phase2/` (16 posteriors) | 60 | 93.1 | `python -m bayesian_reliability_updating results/*_historical_*.h5 --verify` | **PERMANENT.** SHA-256-locked. |
| `phase2_anchor_rating/`, `phase2_no_initiation/` | 16 | 88.8 | same, with documented variant flags | **PERMANENT.** Both are documented campaign variants. |
| `stage6_6/` (two N) | 26 | 81.0 | `python scripts/stage6_6_gap_decomposition.py` | **PERMANENT.** |
| `system_integration/` (+ `hazard_cache/`) | 256 | 48.7 | `python scripts/phase3_campaign.py` (~10 s cached; ~4 min cold) | **Campaign outputs PERMANENT; `hazard_cache/` is a pure cache — deletable, rebuilds in ~4 min.** |
| `gsa/`, `convergence/`, `diagnostics/`, `validation_*/`, `figures/` | 29 | 3.1 | respective drivers | **PERMANENT** (tiny). |
| `phase2_selftest/`, `phase2_test_xs_historical.*` | 23 | 2.8 | `python scripts/run_phase2_selftest.py` | **Deletable after the defence.** Development-time self-test at reduced N. |
| **`superseded_*` ×15** | **125** | **476.6** | not regenerable (they *are* the pre-supersession state) | see below |

**Superseded directories — the actual shape of the problem.** 11 of the 15 are
**completely empty** (0 files, 0 MB): `20260729T162432`, `20260729T180217`,
`20260729T194638`, `20260729T210506`, `20260729T210701`, `20260730T194447`,
`20260730T194906`, `20260730T195259`, `20260730T202420`, `20260731T001807`,
`20260731T002747`. All 476.6 MB sits in the remaining **four**:
`20260729T162451` (88.7 MB), `20260729T180243` (177.6 MB), `20260729T192449` (80.9 MB),
`superseded_adr0047_L47` (129.4 MB).

Proposed policy:

* **`superseded_adr0047_L47` — PERMANENT until the defence.** It is the pre-adoption
  L = 47 m state that ADR-0047's withdrawn-arm numbers were measured against, and a
  committee question about the adoption decision is foreseeable.
* **The three non-empty timestamped directories — retain until the defence**, then
  review. They are the pre-campaign state that gate G1 compared against; the campaign
  document of record already reports the comparison, but the raw inputs to that
  comparison are not otherwise recoverable.
* **The 11 empty directories — safe to remove at any time**, but see §7: whether they
  are a driver defect or intentional markers is unresolved, so the policy should record
  the observation and defer the removal to the owner rather than assume.
* **Rule going forward:** a `superseded_*` directory is retained until the artifact that
  superseded it has been quoted in a defended chapter, then for one further campaign
  cycle.

**Immediately reclaimable without touching anything load-bearing:** `hazard_cache/`
(rebuilds in ~4 min) and the 11 empty directories. **Nothing under `results/` has been
deleted, moved or modified by this audit.**

---

*Sections 1 to 10 produced 2026-07-31 against HEAD
`88d55ddab1412790e4a88afaa819ac7f8e926bec`, working tree clean. Read-only at the
time of writing: no file outside this document was created, moved, renamed or
deleted while producing them.*

---

## 11. Execution record (2026-07-31)

Approved with three amendments. Executed in the order below; every commit is on
`feature/tokachi-chisuishi-review`. **Recovery point for anything deleted:
`3608e04ae9f93844898925ca56137f71d9683f5a`.**

### 11.1 Commits

| SHA | Group | Effect |
|---|---|---|
| `3608e04` | Amendment 1 | Hardened 13 silent-skip guards across 3 test files |
| `c8844c3` | DELETE | 11 root PNGs + 2 `.gitkeep` stubs `git rm`'d; empty `notebooks/notebooks/` removed |
| `6c02a75` | MARK SUPERSEDED | 6 dated headers, no body prose rewritten, nothing moved |
| `a96b1ec` | Reference integrity | ADR-0027's 2 dangling pointers corrected (authorised exception) |
| `41aa610` | Additive docs | `README.md` expanded; `data/processed/2006_event/README.md` created |
| (this commit) | Amendment 3 | `docs/conventions.md` sections 9 and 10; 11 empty `superseded_*` removed |

### 11.2 Amendment 1 — the hardening was larger than the move question

13 guards across 3 files gated on a **tracked** path via `pytest.skip` /
`skipif`, so a move, rename or deletion disabled them while the suite stayed
green. Classified and acted on as instructed:

* **Tracked, now asserted (13):** 8 in `tests/test_figure_pass.py` (`_require`),
  3 in `tests/test_dem_cross_section.py` and 2 in
  `tests/test_epistemic_bracket_synthesis.py` (`_require_tracked`).
* **Genuinely optional, `skipif` retained (11):** every gitignored `data/raw/`
  drop guard in `test_dem_cross_section.py`, `test_foreshore_exhaustion.py`,
  `test_hydrographs.py`, `test_phase2_end_to_end.py`, `test_phase2_events.py`
  (`requires_rating`) and `test_system_integration.py`. Each already carries
  "untracked" in its `reason` string, so the distinction was already legible; no
  edit was needed.
* **Line 247 inverted as instructed.** The Euler-flip guard skipped when the
  claim was *absent from the text*, so deleting the claim made its own guard
  pass. It now asserts the claim is present and skips only for a named
  `EULER_CLAIM_EXEMPT` set, which is empty by design.
* **New structural guard:** `test_no_guard_in_this_file_skips_on_a_tracked_path`
  parses the file with `ast` (not `grep` — a string check matched its own
  explanation, twice) and fails if a `skipif` returns or a second `pytest.skip`
  appears.

**Listed, not fixed, exactly one case.** `tests/test_phase2_events.py`
`requires_processed` (line 31) gates on
`data/processed/2016_event/stage_hourly_Tokachi_201608.csv`, which **is tracked**
— so it is a real instance of the anti-pattern. It is a module-level mark applied
at **9 decorator sites, 4 of them unpaired** with the legitimately-optional
`requires_rating` (**count corrected 2026-07-31 from the "12 sites, 6 unpaired"
first written here; `ast`-parsed, not eyeballed**). Converting it changes
test-collection structure rather than a line, so it is reported rather than
executed. **CLOSED 2026-07-31 — see section 11.6.**

### 11.3 Amendment 2 — authorised exceptions

**(a) ADR-0027.** Two pointer strings corrected
(`OPEN-head-datum-re-convention.md` → `head-datum-re-convention-CLOSED.md`,
renamed in `08267ee`, dangling since), plus one dated line recording that a
pointer was corrected and no decision changed. Diff verified to be exactly that:
8 insertions, 2 deletions, no Status line, no decision, no consequence touched.

**(b) `data/processed/2006_event/README.md`** created, matching the two sibling
event READMEs in form. **One thing the amendment did not anticipate:**
`.gitignore:252` ignored `data/processed/2006_event/` *entirely*, so the new
README would have been invisible — defeating its purpose. The line now uses the
2011 sibling's pattern (`.../2006_event/*/`), which ignores subdirectories while
tracking root files. Verified scoped: the README became trackable and
`観測所雨量データ/rain.xlsx` remained ignored. `.gitignore` is at the repo root, not
under `data/`; nothing under `data/` was modified.

### 11.4 Amendment 3 — retention policy

`docs/conventions.md` gained **section 9** (repository layout conventions: the
two document kinds, the three `docs/decisions/` grammars with the measured cost
of unifying them, the figure dual-write, and the skip-versus-assert rule) and
**section 10** (the `results/` retention policy).

`hwl_bias_resolution/` is stated in 10.2 as **evidence, not a regenerable
convenience** — a 170-minute re-run is not a substitute for the artifact a
reviewer may ask to see, and a regenerated file is not the file the manifest
hashed.

**11 of 15 `superseded_*` directories removed**, each asserted empty immediately
before its own removal in the same operation. The 4 non-empty
(`20260729T162451`, `20260729T180243`, `20260729T192449`, `superseded_adr0047_L47`,
476.6 MB) were retained. This also resolves UNCERTAIN item 2 in section 7: the
empty directories are a **driver artifact** — `production_campaign.py` creates the
preservation directory before knowing whether it has anything to preserve.

### 11.5 Gate results

| Gate | Result |
|---|---|
| `pytest` | **629 passed**, 7 warnings (628 at start + 1 new structural guard) |
| `ruff check .` | All checks passed |
| `black --check .` | 125 files unchanged |
| `production_campaign.py --dry-run` | Manifest path completes; all 11 stages resume as already-passed |
| Gate G7 resolution | **52 of 52** tracked figures declared; 0 unresolved `requires`/`sources`; **0 stale**; 1 declared waiver (ADR-0032, no artifact to bind to) |
| `scripts/*.py` | **43 of 43** compile; 20 of 20 argparse scripts print usage; 23 have no argparse and are compile-checked only (invoking them would start real work) — **superseded 2026-07-31 by section 11.6: 42 of 42 drivers now carry argparse and answer `--help` inertly** |
| Relative paths in `docs/`, ADRs, `README.md`, `project-notes.md`, `untracked-supporting-files/*.md` | All markdown links resolve; no live reference to any removed path |
| msc-thesis | No engine-path reference broken; its `figures/` are its own copies |

**Untouched, as required:** no `Config` default, no physics module, no
`configs/*.yaml`, no CSV, no persisted production sweep, no figure content.

---

## 12. Follow-up closure (2026-07-31): four defects the audit left open

Four items documented above but out of scope of what section 11 executed. None
changes physics, a default, a config, the CSV or any persisted result.

### 12.1 `scripts/assess_2011_2006_closure.py` ran when probed

It had **no argparse at all**, so `python scripts/assess_2011_2006_closure.py
--help` executed the whole 8-stratum study and rewrote its **tracked** evidence
JSON `docs/decisions/adr0044-event-closure-bound.json`. That is how the section 11
`--help` sweep triggered the stray run recorded in section 11.4's by-product note
(diffed key by key: `runtime_seconds` only, restored from git).

Fixed with the surface the other drivers already use — `--strata` (choices, the
`foreshore_width_study.py` `--sections` shape) and `--out` (default = the tracked
record, so the campaign's no-argument invocation is byte-unchanged). A `--strata`
subset now **merges into** the existing record instead of truncating it to the
strata just run: that is the `prior_mean_scenario_companion.py` precedent, and
writing it any other way would have re-introduced the overwriting-per-section
writer the 2026-07-30 hardening sweep had to fix twice. Verified: one-stratum
re-run against a scratch copy preserved all 8 entries in `STRATA` order with zero
substantive diffs.

### 12.2 Sweep of all 43 scripts for the same two shapes

**Shape (a) — no argparse, so any argument runs the tool: 22 drivers, all fixed.**
Each gained the same three lines at the top of `main()` (an
`ArgumentParser(description=__doc__.splitlines()[0])` whose `parse_args()` is
reached before any work), plus `import argparse`.
`scripts/seepage_length_figures.py` had no `main()` at all — its work ran directly
under the `__name__` guard — and gained one. The 43rd file, `scripts/_figstyle.py`,
is a shared style **module** with no entry point and is correctly left alone.

Measured, not assumed: all 43 compile; all 42 drivers exit 0 on `--help`; and
`git status` is clean of artifact churn after the full sweep, which also proves
no script does I/O at import time.

**Shape (b) — unconditional write to a tracked `docs/` path with no
`--overwrite` guard.** Three classes, only the first of which is a defect:

* **A driver that wrote before it could be asked what it does** — exactly one,
  section 12.1, fixed. With `--help` inert everywhere, every remaining tracked
  write now happens only on a deliberate run.
* **Publication figures under `docs/figures/`** (`phase3_figures`,
  `plot_fragility_curves`, `stage6_6_gap_decomposition`, `seepage_length_figures`,
  the three `plot_validation_*`, and the figure paths of `gsa_study`,
  `convergence_study`, `hwl_bias_resolution`, `dem_cross_section_study`,
  `tail_variance_study`, `foreshore_exhaustion_study`,
  `aquifer_response_diagnostic`). **Not fixed, and must not be:** overwriting in
  place is the dual-write contract the figure pass installed deliberately, and
  gate G7 re-renders them unconditionally and then fails on staleness. An
  `--overwrite` refusal here would break G7 and reopen the copy problem.
* **Evidence JSONs written to a hard-coded tracked path with no `--out`** —
  `mp_model_factor_companion`, `prior_mean_scenario_companion`,
  `ztoe_sensitivity_study`, `tail_variance_study`. **Listed, not fixed:** writing
  that record is the driver's whole purpose, none is invoked by
  `production_campaign.py` (the ADR-0045/0046/0048 knobs stay OFF per campaign
  decision 3), so none can churn a tracked file during a campaign. The cheap
  future improvement is to give each an `--out` default, as
  `foreshore_width_study.py` has, so the campaign could compare rather than
  rewrite.

**One pre-existing observation, not a script defect.** `dem_cross_section_study.py`
and `foreshore_exhaustion_study.py` raise `UnicodeEncodeError` on `--help` when
stdout is a cp1252 pipe: their `description=__doc__` help text carries the
deliberate Japanese source terms (`高水敷幅`, `様式-5`) that `docs/conventions.md`
section 8 keeps in the repository. Both exit 0 under a UTF-8 stdout
(`PYTHONIOENCODING=utf-8`), nothing is written either way, and the two candidate
"fixes" are worse than the symptom (strip the CJK the convention requires, or add
a stdout-reconfiguration idiom nothing else here uses).

### 12.3 `tests/test_repo_hygiene.py` — docstring corrected to the code

Lines 56–57 claimed `docs/references/` was excluded from the tree scan; line 59's
`skip_dirs` never excluded it. **The code was right.** `skip_dirs` holds only
directories that are *not ours* (git database, venv, third-party packages, build
caches); `docs/references/` is curated, the stated reason for exempting it
(gitignored PDFs) buys nothing since a `.pdf` cannot match `THESIS_SUFFIXES`, and
being gitignored is not an exemption elsewhere in the same scan (`results/`,
`data/` are covered on the same footing). The docstring now says so, with the
withdrawn claim named so it cannot be reinstated as a "fix".

### 12.4 `requires_processed` — the last member of the silent-skip class

Converted per the Amendment 1 rule. **Final split, `ast`-parsed:**

| | Before | After |
|---|---|---|
| `requires_processed` sites (tracked path) | 9 `skipif` (4 unpaired, 5 paired) | 9 **asserting**, same sites |
| `requires_rating` sites (untracked `data/raw/`) | 5 `skipif` | 5 `skipif`, **unchanged** |

`requires_processed` is now `pytest.mark.usefixtures("tracked_2016_extracts")`,
whose fixture asserts both committed extracts
(`stage_hourly_Tokachi_201608.csv`, `flood_trace_2016.csv`) and names the
regeneration command. No decorator site moved: only the outcome flipped from skip
to fail, so this was a one-mark change rather than the collection-structure change
section 11.2 feared. `requires_rating` keeps `skipif` and gained a comment saying
why (`.gitignore:224` ignores `data/raw/`). New structural guard
`test_no_existence_skip_in_this_file_gates_on_a_tracked_path` `ast`-parses this
module and fails if any `skipif`/`pytest.skip` condition other than
`not _RATING_CSV.exists()` appears — the `test_figure_pass.py` pattern, parsed
rather than grepped for the same reason.

### 12.5 `docs/architecture.md` section 9 — two stale example paths

Section 5.3, item 6 of the recommended order, deliberately not executed there.
`configs/tokachi_kp58.yaml` → `configs/kp58_8_historical_matrix.yaml` and
`results/tokachi_kp58_historical.h5` →
`results/tokachi_kp58.8_historical_matrix.h5`. Prose only: no decision, no table
row, no section 13 entry touched.

### 12.6 Gate results

| Gate | Result |
|---|---|
| `pytest` | **630 passed**, 7 warnings (**629 → 630**; +1 = the new structural guard in 12.4. The `requires_processed` conversion changed no count: 9 sites in, 9 sites out) |
| `ruff check .` | All checks passed |
| `black --check .` | 125 files unchanged |
| `production_campaign.py --dry-run` | Completes; all 11 stages resume as already-passed |
| Gate G7 | **52 of 52** declared, 0 unmapped, **51 staleness-gated with 0 stale**, 1 declared waiver (ADR-0032) |
| `scripts/*.py` | **43 of 43** compile; **42 of 42 drivers answer `--help`, exit 0**; `git status` clean of artifacts afterwards |
| Figure drivers re-run | 6 touched drivers re-executed; **0 figure bytes changed** |

**Untouched:** no `Config` default, no physics, no `configs/*.yaml`, no CSV, no
persisted production sweep, no figure content, no ADR.

### 12.7 Stale internal cross-references in the provenance record — CLOSED 2026-08-09

Four pointer defects closed as pointer substitutions only: provenance §7.3's
"Section 4.1" → **6.1** (the dated chronology) and "section 4.3 above" → **6.3**
(the countermeasure → engine-quantity map), the same §4.3 → **6.3** target in
`tokachi_basin_document_review_2026-07-27.md` register item R8, and the orphan
heading "4.6 Kasumi-tei coincidence audit" renumbered to **7.5**, where it
physically sits (between 7.4 and section 8, inside the 2026-07-28 full-volume
review). The pre-sweep claim that no inbound reference to §4.6 existed was
**wrong by one**: `system_integration/segments.py`'s `KASUMI_TEI_CSV` comment
cites it, and was updated with the heading — comment text only, no code. A fifth
of the same class was found on the line directly above R8 and closed in the same
pass on the owner's authorisation: register item **R7's "provenance §4.4" → §6.4**
(the Chiyoda regional band, whose own text recommends exactly the ADR-0046-pattern
bounding scenario R7 names). Correct and deliberately not
touched: `tokachi_chisuishi_full_review_2026-07-27.md`'s §4.3/§4.6 (internal to
its own numbering) and `bep_reliability_engine/sensitivity.py`'s five §4.3/§4.6
(Saltelli et al. 2008, *The Primer*).

### 12.8 The silent-skip class in a *driver* gate — CLOSED 2026-08-10

**This is not something the 2026-07-31 audit missed. It is a scope boundary the
audit drew, now extended.** Amendment 1 and section 12.4 closed the class for
`tests/`: 13 guards that gated on a tracked path via `pytest.skip`/`skipif` were
converted to assert, and two AST guards
(`test_no_guard_in_this_file_skips_on_a_tracked_path`,
`test_no_existence_skip_in_this_file_gates_on_a_tracked_path`) keep the pattern
out. Both are **per-test-file** by construction — each parses the module it
lives in — so neither could ever have seen a driver. Driver gates were never in
scope, and the sweep of all 43 scripts in 12.2 looked for two *other* shapes
(no-argparse, and unguarded tracked writes), not for a gate that records a
failure and continues.

**The defect.** `scripts/stage6_6_gap_decomposition.py::verify_against_production`
implements ADR-0040 gate (i) — C0 and C4b bit-identical to the persisted
production sweep. On four outcomes it set a `status` string and **returned**:
`skipped_missing_production_file`, `skipped_config_mismatch_beyond_length_effect`,
`skipped_n_mismatch`, and — the one not in the enumeration, because it produced no
status at all — a pilot run, since `main` called the guard only `if args.n is
None`. The driver then persisted `results/stage6_6/`, dual-wrote the tracked
`docs/figures/` copies and exited 0 regardless. So a run that never verified
replaced the guarded record *and the publication figures* with unguarded
evidence, and nothing said so at the time. The campaign's own G3 gate does check
the status, but only after the driver has already overwritten everything.

The pilot case is the sharpest of the four: `--n 10000` writes to exactly the same
paths as a production run, could never be bit-identical, and was the one path that
skipped the guard entirely rather than recording why.

**The fix.** The driver now **refuses** — exit 1, before persisting anything and
before writing any figure — when a section's `production_verification` status is
anything but `bit_identical`, including absent. `--allow-unverified` permits it
(named for what it permits, the `system_integration --allow-stub` precedent); when
passed, the summary records `allowed_unverified: true` beside the status, so a
permitted run is still legible afterwards and G3 still fails on it.

Three details worth keeping:

* **The gate runs before the write here, and that is the opposite of the
  2026-07-30 hardening on purpose.** That hardening made two sibling functions
  persist *then* gate, after a gate discarded 2.5 h of freshly computed evidence
  it was raised about. The rule it encodes is "do not let a gate destroy
  evidence", and it is direction-dependent: there the write *created* evidence,
  here the write *overwrites a guarded record*. The distinction is stated in
  `verification_blocks_write`'s docstring so the next reader does not reverse it.
* **The cheap outcomes are caught before the ladder starts.** Three of the four
  are decidable from the config alone, so `production_comparability` was factored
  out of `verify_against_production` and is called once before the run. A
  never-verifiable run is refused in seconds rather than after a twenty-minute
  ladder — one implementation, two call sites, no parallel rules.
* **`--figures-only` cannot reach the gate.** It is a read-only redraw of
  already-persisted evidence; a test replaces all three gate entry points with
  raisers and asserts the redraw still completes.

**Campaign path asserted, not assumed.** The campaign invokes the driver with
`--n-jobs N --skip-figures` and no opt-out, and its recorded status is
`bit_identical` at both sections (38 and 23 levels). Replaying the refactored
guard over the persisted ladders reproduces both records **key-for-key in the same
order with the same values**, so `stage6_6_summary.json` is byte-unchanged and the
refusal never fires there.

**Tests:** `tests/test_stage6_6_driver_gate.py` (9). The named pair is
`test_gate_refuses_a_mismatched_config_before_anything_is_written` and
`test_gate_passes_on_the_production_path`, both end to end on the stub hydrograph
path at N = 400. `test_every_status_the_driver_can_write_is_classified` AST-parses
the driver and fails if a fifth non-verifying status is ever added without being
classified — the generalisation of the per-test-file guards to this driver.
Nothing skips on a tracked path; the one `skipif` is on gitignored
`results/stage6_6/` and says "untracked".

**Gates:** `pytest` **692 passed** (685 → 692), `ruff check .` clean,
`black --check .` clean, `--help` inert with `git status` unchanged. No physics,
no `Config` field, no ADR, no persisted result, no figure content.

**Not extended to the other drivers.** 12.2's sweep shape (c) — a gate that
records and continues — has not been swept for across all 43 scripts. This
closure is the one instance the 2026-08-09 canonical-shape review surfaced, not a
class sweep; `docs/conventions.md` section 9.4 now states the rule for drivers so
the next one is written correctly.

### 12.9 The same class in the campaign's own G6 gate — CLOSED 2026-08-10

**Third instance, and the first with no write anywhere in it.** 12.4 closed the
class for `tests/` (13 guards, skip → assert) and 12.8 closed it for a driver
gate (Stage 6.6 recording a non-verifying status and continuing). Neither could
have caught this one, and not by oversight: both AST guards
(`test_no_guard_in_this_file_skips_on_a_tracked_path`,
`test_no_existence_skip_in_this_file_gates_on_a_tracked_path`) parse **only the
test module they live in**, and 12.8's fix is a predicate inside a different
driver. Nothing in either closure can see the campaign's own gate records.

**The defect.** `scripts/production_campaign.py::enumerate_companions` greps
`scripts/`, `tests/` and the three packages for files that both reference a
persisted production sweep and assert bit-identity or a config hash — the census
of who depends on the artifacts the campaign produces. Its result was passed to
`gates.note`, never `gates.check`. G6's only assertion was that every companion
which *runs* completes. So a hit that was neither run nor excluded would be
written into the manifest as `UNCLASSIFIED -- investigate` and could not fail
anything. **Three accumulated across four sessions.**

**Enumeration reproduced before anything was changed** (17 hits / 5 covered /
9 excluded / 3 unclassified / 4 run-but-unmatched) — every figure in the brief
confirmed by calling the function directly, so the work started from measurement
rather than from the brief's summary.

**One brief premise did not reproduce, and the difference is the finding.** The
brief stated that `results/production_campaign_manifest.json` "lists the three as
UNCLASSIFIED". **It does not — it never recorded them at all.** Its G6 detail
carries **14 hits**, none of them the three, and a `found_but_not_run_here` that
is a plain **list** rather than the path → reason dict the function returns today:
an older return shape, from the 2026-07-29 campaign. `git log` puts
`epistemic_bracket_synthesis.py` at 2026-07-30 and `hwl_bias_resolution.py` at
2026-08-04, i.e. **after** that run. So the three did not slip past a gate that
saw them; they accumulated in the window since the last campaign, and the
note-only wiring is what guaranteed the *next* run would have recorded and passed
them. The instruction to leave the manifest alone stands, and for a stronger
reason than the one given: it is an accurate record of an enumeration that ran
before these consumers existed, and rewriting it would fabricate history rather
than merely refresh a view. **It was left untouched** (mtime 2026-08-04, verified
after the change).

#### The three classifications

Question (a) — *should this RUN as a campaign companion?* — was answered first in
each case, since an exclusion is only correct once that answer is genuinely no.
All three answered no, and **none of them on cost**; the runtimes are recorded
below so the owner can overrule.

| Hit | (a) Run it? | (b) What actually excludes it |
|---|---|---|
| `bayesian_reliability_updating/pipeline.py` | No | Not a driver — the shipped Phase 2 module, which the campaign already executes as **three of its own stages** (`phase2_baseline`, `phase2_anchor_rating`, `phase2_no_initiation`), each under **G2**. The 12.8-style answer: name the gate that runs it instead. Its regex match is the replay hash it *stamps* into the posterior sidecar; the gate consuming that hash lives in `replay.py` and is what `--verify` exercises. Structurally unreachable anyway — `COMPANION_COMMANDS` keys resolve to `scripts/<name>.py`. |
| `scripts/epistemic_bracket_synthesis.py` | No | Synthesises the 16 persisted ADR-0045/0046/0048 arm sweeps the campaign **deliberately does not produce** (knobs OFF, campaign decision 3) — the same substantive ground as the three companion entries beside it. Running it would be worse than redundant: on a missing arm it records `available: false` and continues, so without those gitignored sweeps it exits 0 and G6's completion check would pass on a synthesis with **every epistemic arm missing**. Would add ~20 min (recorded 249/293/322/359 s of fresh baseline sweeps). |
| `scripts/hwl_bias_resolution.py` | No | **A cheap verification-only mode does exist**, so this is explicitly *not* a cost exclusion: `verify` costs ~25 min (recorded 883.4 + 600.1 s). It is excluded because that mode **imports `stage6_6_gap_decomposition.verify_against_production`** and calls it at `kp62_0` and `kp57_4` — G3's own function, at G3's own two sections — and its G-A2 flip check is G3's third check. Its remaining stages are the N = 1e6 evidence (`brute` alone 10 188.9 + 4 781.5 s = 4.2 h), which conventions section 10.2 classifies as evidence rather than a regenerable cache, and `verify` overwrites files inside that directory. Its `figures` subcommand **is already run by the campaign**, in the figures stage under G7. |

The ADR-0045/0046/0048 entries beside them say their hash gates survive a config
change because each reconstructs its `Config` from the sidecar's own config
block. **That sentence was deliberately not reused** for
`epistemic_bracket_synthesis.py`, which reads the current `configs/*.yaml`
instead — it reads well and would have been false.

#### The structural fix

`enumerate_companions` now returns `unclassified` and
`exclusions_with_no_file_on_disk`, and a new `gate_companion_classification`
turns both into `gates.check`. **The note is kept**: the note is the evidence,
the check is the enforcement. Both directions gate, because both silently
classify nothing — a hit no rule mentions, and a reason naming a file that no
longer exists (which would also mask the renamed file's reappearance as a hit).
The check runs **before** the companion subprocesses: the verdict is decidable
from source, so an unclassified consumer refuses in milliseconds instead of after
~40 minutes, and since nothing has been written there is no evidence for the gate
to destroy — this is not 9.4's persist-then-gate case. Per the 2026-07-29
asymmetric-allowlist precedent, a **new** hit fails loudly rather than passing
silently.

**The gate's first live catch was the test file written to guard it.**
`tests/test_companion_enumeration_gate.py` quotes both the f-string stem and the
phrase "bit-identity" in its docstrings, so it became a hit the moment it
existed — the same self-matching trap the AST guards were written around. It was
**classified, not exempted by narrowing the pattern**, and a test pins that it
stayed classified.

#### The blind spot (decided, not inherited)

`scripts/conductivity_annualisation_study.py` raises on `config_hash` drift and
asserts against the persisted `rq4_annual.csv`, yet did not match: it composes
its stem as `f"tokachi_kp{kp:.1f}_historical_{D70}"`, and the pattern
`tokachi_kp[0-9]` wanted a digit where the f-string places `{`. **Decision:
widen** — the path half drops the digit requirement. Measured first: the minimal
widening pulls in **exactly two** files, at the brief's ask-first threshold and
so decided rather than escalated. Both were then classified in the same pass,
leaving no fresh crop:

* `scripts/conductivity_annualisation_study.py` — recorded as a deliberate
  non-entry when built (2026-08-10) on the decision-3 ground; now the exclusion
  key is one that is actually read. Cheap in itself (8.0 s) but it raises
  `FileNotFoundError` on a missing arm, so on a machine without those gitignored
  sweeps it would fail the campaign at a stage unrelated to the production
  deliverable. Its arm-independent Gate 1 has no gate-only entry point today;
  adding one is the cheap route if that is ever wanted.
* `scripts/generate_configs.py` — produces `configs/`; run as the campaign's
  **first stage**, gated by the empty-diff assertion. Its `config_hash` match is
  a round-trip of what it just wrote, not a check against a persisted sweep.

**The widening does not make the regex a census, and the docstring now says so.**
Both halves are textual and either can be evaded — a stem built from smaller
parts still escapes the path half, and a bit-identity check reached through a
differently-named helper escapes the assertion half. Recorded as
`detection_is_a_floor_not_a_census` in the enumeration payload as well as in the
docstring, so the manifest carries the caveat with the evidence.

**`run_but_not_matched_by_the_regex` examined and found benign**, not left alone
unexamined. The four members (`segment_fragility`, `foreshore_exhaustion_study`,
`assess_2011_2006_closure`, `gsa_study`) are run by the stage while failing one
half of the regex — `segment_fragility.py` globs `tokachi_*_historical_*.h5` and
asserts nothing the pattern recognises. That is the superset direction: running
something undetected costs coverage, never correctness. The direction that
matters is a consumer neither detected nor run, which is what the widening
narrows. Pinned by a test so the list stays a recorded fact.

**Tests:** `tests/test_companion_enumeration_gate.py` (12). The gate is proved by
being **fired**, not by being asserted to exist — a classification is removed and
`GateFailure` must be raised, both tables are emptied so every hit becomes
unclassified, and a stale exclusion key is injected (with the pass/FAIL order
checked, so it is the stale-key check that fails and not the other one). Nothing
skips on a tracked path.

**Gates:** `pytest` **723 passed** (711 → 723), `ruff check .` clean,
`black --check .` clean, `--dry-run` completes with all 11 stages resumed,
`enumerate_companions()` reports **20 hits / 5 covered / 15 classified / 0
unclassified / 0 stale** (the 20th hit is the new guard file itself). **`results/production_campaign_manifest.json` was
deliberately left untouched** (see the premise correction above). No `Config`
field, no default, no physics, no config YAML, no CSV, no persisted sweep, no
Phase 2 posterior, no figure content, no ADR, no `.tex`.
