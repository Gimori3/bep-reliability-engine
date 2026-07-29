# Retirement of the `_thesis_*` fragments (2026-07-29)

**Status:** closed. **Recovery commit:** `b015997`
(`b0159975eb29438384b90a760dbe061248653a37`) is the last commit in which all
seven files exist; `45a4487` removes them. Restore any of them with
`git show b015997:_thesis_methodology.tex`.

**Why this file is here.** This is the authoritative, tracked copy of the audit
that justified deleting seven tracked files. A working copy sits at
`msc-thesis/scratch/THESIS_FRAGMENT_AUDIT.md`, but `scratch/` is gitignored in
that repository (`.gitignore:8`), so that copy is machine-local and would not
survive a fresh clone. Per `docs/conventions.md` section 8, work products of
record belong in `docs/`. The content below is a snapshot and is not maintained;
where it disagrees with an ADR or a report of record, those govern.

**Retired files:** `_thesis_studyarea.tex` (551 lines), `_thesis_methodology.tex`
(836), `_thesis_gsa.tex` (543), `_thesis_validation_japan.tex` (382),
`_thesis_system_integration.tex` (238), `_thesis_gsa.bib` (127),
`_thesis_validation_japan.bib` (70).

**Outcome in one line:** nothing was integrated into the thesis; 305 of 334
substantive paragraphs were already present, 14 of the 15 genuinely absent ones
were false against the current engine, and the sole results-chapter fragment was
staged rather than written because Chapter 7 is deliberately unwritten.

---


Date: 2026-07-29
Engine repo: `d:\repositories\bep-reliability-engine` (branch `feature/tokachi-chisuishi-review`, clean at audit time)
Thesis repo: `d:\repositories\msc-thesis` (4 uncommitted chapter mods present at audit time; read from disk, not from memory)

Companion to `scratch/MANIFEST.md` (the fact manifest). This document answers only the
three-way disposition question for the seven `_thesis_*` files; MANIFEST remains the
thesis-to-engine fact trace.

## Method

Q1 was settled by paragraph-level semantic comparison (token-Jaccard plus sequence
ratio of LaTeX-stripped paragraphs, every fragment paragraph against every chapter
paragraph, low scorers then read by hand) **plus** a topic-coverage sweep, because
Chapter 4 is a complete as-built rewrite and therefore scores low lexically even where
the content is fully present. Q2 was settled against the current engine: ADRs in
`docs/decisions/`, the three reports of record including their dated addenda, and the
persisted campaign artifacts. Q3 applies the stated bar: main body only where the
passage is needed to understand, justify or defend a claim the thesis makes.

Chapter numbering below is the compiled numbering: Ch. 3 Study Area, Ch. 4 Methodology,
Ch. 5 Verification/Validation/Sensitivity, Ch. 6 Results Subsurface Piping, Ch. 7
Results System Integration, Ch. 8 Discussion, Ch. 9 Conclusions. (Filenames are offset
by one from Ch. 6 onward; `report.tex` documents this.)

## Bucket summary

| Fragment | Substantive paras | Q1 present | Q1 absent | Q2 still true | Q3 to main body | Q3 to appendix | Q3 staged | Q3 dropped |
|---|---|---|---|---|---|---|---|---|
| `_thesis_validation_japan.tex` | 23 | 23 | 0 | n/a | 0 | 0 | 0 | 0 |
| `_thesis_gsa.tex` | 29 | 29 | 0 | n/a | 0 | 0 | 0 | 0 |
| `_thesis_studyarea.tex` | 125 | 111 | 14 | 0 | 0 | 0 | 0 | 14 |
| `_thesis_methodology.tex` | 143 | 142 | 1 | 1 | 0 | 0 | 0 | 1 |
| `_thesis_system_integration.tex` | 14 sections/paras | 0 | 14 | 4 | 0 | 0 | 14 | 0 |
| **Total** | **334** | **305** | **29** | **5** | **0** | **0** | **14** | **15** |

**Nothing is proposed for integration into the main body or appendices.** The single
migration is `_thesis_system_integration.tex` to `scratch/`, per the task's own
instruction that Ch. 7 is not to be written.

---

## 1. `_thesis_validation_japan.tex` (382 lines, 23 substantive paragraphs)

**Q1: 23 of 23 present.** Zero paragraphs fell below the 0.55 similarity threshold
against Ch. 5. The fragment was integrated wholesale during the 2026-07-19 sprint as
Ch. 5 Section "Validation Against Japanese Field Cases" (Ch. 5 L195 to L549), which is
a strict superset: it adds the subsection structure (initiation unbiased conditional on
calibrated heads; hydraulic translation over-predicts in a bounded way; the race
condition has field support; directional static conservatism; two structural findings;
transfer to the Tokachi sections) and updates the r_e-halved QA member from "registered"
to executed.

**Q2/Q3:** not reached. **Verdict: DROP.**

## 2. `_thesis_gsa.tex` (543 lines, 29 substantive paragraphs)

**Q1: 29 of 29 present.** 28 matched directly. The one low scorer (fragment L147 to
L162, "Uncertainty and convergence", jac 0.46) is covered by Ch. 5 L669 "Uncertainty,
convergence, and machinery validation", which contains every element of the fragment
paragraph (the Student-t and row-bootstrap interval pair, the agreement health check,
the N-ladder, the pre-registered 0.02 drift criterion) **and adds** the four analytical
benchmarks, the two bit-identity guards, and the P_f = 0.263 cross-check against the
N = 1e5 production sweep. The chapter version supersedes the fragment.

**Q2/Q3:** not reached. **Verdict: DROP.**

## 3. `_thesis_studyarea.tex` (551 lines, 125 substantive paragraphs)

**Q1: 111 present, 14 absent** (a 15th low scorer, fragment L172 to L174, is a bare
section heading and is not substantive). Ch. 3 mirrors the fragment structure and is
consistently the later, corrected text.

Every one of the 14 absent passages fails Q2. They are the pre-analysis-plan and
pre-as-built text that MANIFEST section 11 lists as "thesis-side factual corrections
REQUIRED", and the corrections have since been made in Ch. 3.

| # | Fragment lines | Passage | Q1 | Q2 verdict | Settled by | Q3 |
|---|---|---|---|---|---|---|
| 3.1 | L168 | Drain-equipped segments implemented by setting the exit head boundary to zero, so I_er never activates and near-zero BEP is "physically accurate" | absent | **FALSE** — no drain physics exists; `remediation_state` is a label | `phase2_report.md` caveat; MANIFEST 11.1; Ch. 3 L128 and L229 carry the corrected framing | drop |
| 3.2 | L170 | Berm fill transmissivity; post-remediation L "taken from the post-remediation geometry" | absent | **FALSE** — ADR-0047 holds L at the 1998 values at KP 57.4/58.8/60.0 and adopts a *shorter* 40.0 m at KP 62.0 | ADR-0047 (adopted 2026-07-29) | drop |
| 3.3 | L458 | m_u and m_p "not carried in the baseline parameterization" | absent | **PARTLY FALSE** — m_p is an opt-in knob with a measured companion (static shoulder x2.2 to x2.4) | ADR-0045 | drop (Ch. 3 L757 corrected) |
| 3.4 | L469 | Two remediation strategies for k-d70, chosen by "Diagnostic A of the pre-analysis plan" | absent | **FALSE** — resolved | ADR-0012 two-population | drop |
| 3.5 | L478 to L479 | Conductivity priors anchored to Form-5 constants, with the cross-correlation caveat | absent | **SUPERSEDED** — anchoring is retained but is now one end of a measured epistemic bracket (field geomean 17x to 51x below, 5.0 to 7.3 sigma) | ADR-0048 | drop (Ch. 3 L777 corrected) |
| 3.6 | L484 | "This subsubsection states the pre-analysis diagnostic that resolves the dependence structure" | absent | **FALSE** — executed | ADR-0012 | drop |
| 3.7 | L488 | Outcome 1 (Nataf copula), full 7x7 Sigma | absent | **FALSE** — not the outcome | ADR-0012 | drop |
| 3.8 | L490 | Outcome 2 (two-soil model), stated as a contingency | absent | **TRUE in substance, wrong in mood** — this is the adopted model, but Ch. 3 L787 states it as resolved fact rather than as a branch | ADR-0012 | drop |
| 3.9 | L492 | "must be entered as a named configuration parameter before any Phase 1 run is executed" | absent | **FALSE** — done; 8 production sweeps closed | close-out 2026-07-13 | drop |
| 3.10 | L497 to L498 | C_e field prior 0.055 / 0.043, two calibration targets | absent lexically | **TRUE** but present in corrected form at Ch. 3 L794 | ADR-0026 + `adr0026-ce-prior-study.md` | drop |
| 3.11 | L500 | C_e stochastic on intrinsic-uncertainty grounds, not to absorb model form; m_p double-count warning | absent lexically | **TRUE** but present at Ch. 3 L794 | ADR-0026, ADR-0045 | drop |
| 3.12 | L502 to L503 | KP 63.4 pooled "if its Phase 1 conditional P_f falls within the bootstrap band" (pre-registered criterion) | absent | **FALSE** — resolved by exclusion from the generated population (unconfined, mechanism mismatch) | MANIFEST 11.16; `generate_configs.py` | drop |
| 3.13 | L505 to L506 | Lower Tokachi and Satsunai carry "interpolated prior means with deliberately inflated CoVs" | absent | **FALSE** — never built; Phase 3 `exact` BEP-source policy means borehole-free segments carry surface mechanisms only | ADR-0038; MANIFEST 11.12 | drop |
| 3.14 | L541, L543 | Uemura curves "imported directly", "pre-calculated fixed inputs", "overflow curves used as received" | absent | **FALSE** — curves are re-executed from his models; and the *primary* is now the dimensionally-corrected conversion, under which fluvial scour is exactly zero at all 114 segments | ADR-0042 incl. decision 9 (amended 2026-07-21) | drop (Ch. 3 L834 corrected) |
| 3.15 | L549, L551 to L552 | lambda_ac "estimated empirically from the variability of these parameters across the surveyed cross-sections"; data-gap segments get literature lambda_ac and "higher uncertainty" | absent | **FALSE** — five cross-sections 1.2 to 2.0 km apart cannot resolve lambda_ac; the anchor is literature (Kanning 250 m primary), and n_eff = 1 at that value is a finding | ADR-0037; Ch. 3 L843 to L847 | drop |

Additional defect noted in passing: fragment L549 contains what was intended to be the
Japanese term for the soil-layer longitudinal profile but is stored as **mojibake**
(UTF-8 bytes decoded as Latin-1). Ch. 3 L463 romanises it correctly as "doso judanzu".
A further reason not to migrate this file.

**Verdict: DROP all.**

## 4. `_thesis_methodology.tex` (836 lines, 143 substantive paragraphs)

Ch. 4 is a complete as-built rewrite (PLAN.md decision, Ch. 4 target structure 4.1 to
4.10), so lexical similarity is uninformative: 111 of 143 paragraphs score below 0.55
and 108 below 0.40 purely because the prose was rewritten. Q1 was therefore settled by
reading all 111 low scorers and by a 26-topic coverage sweep of Ch. 4.

**Q1: 142 of 143 present.** Every topic in the fragment has a home. The two topics
returning zero hits in Ch. 4 both live elsewhere by design:

* the lateral decay of aquifer overpressure landward of the toe and its Tokoro
  distal-boil corroboration is literature and site evidence, and sits in Ch. 2 L58 to
  L62 and Ch. 3 L122 and L314 (both richer than the fragment);
* the STPH weakest-link min() formulation sits in Ch. 1 L81 and Ch. 3 L843.

Spot checks confirmed the as-built versions are supersets, not summaries. Three
examples: the flood-fighting omission (Ch. 4 L663 adds the model author's confirmation
and the climate-differential argument); the r_l = 0 justification (Ch. 4 L950 adds the
20 per cent lower critical head alongside the fragment's 140 per cent higher rate); the
FORM exclusion (Ch. 2 L226 carries the discontinuity argument that mandates simulation).

**Q1 absent (1):**

| # | Fragment lines | Passage | Q2 | Q3 |
|---|---|---|---|---|
| 4.1 | L726 to L730 | Two localized complexities excluded from the model domain: 1950s clean-sand levee cores and soft peat lower-basin foundations `\parencite{tsai_2018}`, with the statement that "these exclusions are not bounding in a single direction" | **TRUE** — the engine models a bipartite A_c/A_g stratigraphy with neither feature | **drop** (discretionary; see note) |

Note on 4.1: this is the only passage in four fragments that is simultaneously absent
and true. Ch. 1 L101 already excludes "localized bio-geotechnical anomalies" and asserts
"continuous, geologically defined soil strata", and Ch. 4 L1426 to L1433 already carries
the non-conservative-exclusion register to the Discussion, so the passage refines rather
than supplies. `tsai_2018` exists in `references.bib` and is currently uncited (harmless
under biblatex). Recommended verdict is drop; this is the one call in the audit that a
reasonable reader could take the other way.

**Q2 traps found in the "present" bucket.** These matter more than the absences: 13
distinct claims in the fragment are *false against the current engine* and are the
reason the file must not be treated as a fallback source. All are already corrected in
Ch. 4.

| Fragment claim | Current engine |
|---|---|
| Static comparator uses the r_e-translated head, "applying it to the raw river stage would conflate the bias" | **ADR-0028**: static uses the raw gross head; the static branch is entirely r_e-independent |
| H_erosion = Delta_h_blanket − 0.3 D_bl (crack term applied after r_e) | **ADR-0027**: raw head, H_erosion = (h − z_toe) − 0.3 D_bl |
| Integration timestep = native d4PDF resolution | **ADR-0030**: 225 s = native/16 |
| Drain segments implemented by zero exit head | not implemented |
| L/lambda_in recorded as a validity diagnostic with an escalation trigger | withdrawn as a category error (ADR-0006 amendment): L is the exact linear USACE L2 term, never inside a tanh |
| Foreshore width is "a dominant source of heterogeneity in r_e"; KP 60.0 suppresses r_e toward zero; KP 62.0 transmits near-completely; fourteen-fold variation drives risk | **refuted** (ADR-0025 amendment): KP 62.0 has the *lowest* r_e of the four (0.330); full B_f to 0 is worth 2.3e-4 there; the 0.45 m blanket governs |
| Instantaneous-transmission validity "treated as an explicit diagnostic to be resolved prior to production runs" | **ADR-0032**: executed, Pi about 0.010 to 0.012 against Pi\* = 0.10; S_s did not bind; loading is not flashy (median T_rise 18 h, plateau 9 h) |
| LHS "is expected to tighten the CoV ... verified empirically ... should the advantage prove weak" | **refuted** (fm5, ADR-0029 and ADR-0031): no detectable tail advantage; parity in the deep tail on two sections |
| Fragility fitted lognormal in h | **ADR-0024**: fit in load excess h − z_toe, Optional per branch, always-on Clopper-Pearson CIs, raw-tail-binomial as the intended primary transient presentation where the transition is unreachable |
| N = 1e5 "adopted on the basis of standard practice ... verified once the engine is operational" | **ADR-0031**: executed N-ladder, R = 50 |
| Uemura curves imported as pre-calculated inputs | **ADR-0042**: re-executed from his models; primary uses the dimensionally-correct conversion; fluvial scour exactly zero at all 114 segments |
| C_e lab-vs-field gap is "a factor of three to four that the model author does not fully explain" | explained: two distinct calibration targets, not a spread difference (`adr0026-ce-prior-study.md`) |
| tau_aq presented as an unresolved screening quantity | executed as Pi = tau_aq / T_rise with a pre-registered threshold |

**Verdict: DROP.**

## 5. `_thesis_system_integration.tex` (238 lines)

**Q1: 0 present.** Destination Ch. 7 "Results: System Integration and Climate
Sensitivity" is a four-heading skeleton with no prose. Nothing has been integrated,
deliberately: PLAN.md decision 2 declared the results chapters off-limits for the
2026-07-19 sprint, and that decision stands for the prose.

**Q2: mixed, and the file says so itself.** An earlier session inserted a
`% STALE NUMBERS (flagged 2026-07-29, not yet reconciled)` block at L86 to L97 marking
everything from the dominance section to the end of the +4K section as predating the
2026-07-22 D7 rating-error correction and the 2026-07-29 ADR-0047 adoption. That flag is
accurate and slightly conservative; the closing limitations paragraph is also affected.

Verified current (4):

| Fragment lines | Claim | Confirmed against |
|---|---|---|
| L62 to L63 | KP 62.0 BEP carries 81 per cent historically, half under +4K | `phase3_report.md` 11.1: 0.812 / 0.500 |
| L64 to L69 | Annualized 7.5e-4, 7.4e-3, 1.8e-3, 1.0e-3 per year at the four sections; basin max is KP 58.8 | `phase3_report.md` 5.1 and 11.2 (7.53e-4, 7.42e-3, 1.80e-3, 1.006e-3) |
| L58 to L61, L229 to L232 | KP 62.0's transient transition is bracketed only inside the hypothetical above-crest grid extension and must never be read as attainable | ADR-0047 4.5; `phase3_report.md` 11.3 parenthetical |
| L199 to L205 | Duration channel carries the climate signal; +4K roughly triples >24 h years (KP 58.8 5.1 to 13.5 per cent) | `phase3_report.md` 6.3 |

Superseded (10):

| Fragment lines | Claim | Current |
|---|---|---|
| L44 to L49 | The corrected scour conversion is a "flagged companion"; "the primary curves reproduce the source implementation as received" | **Inverted.** ADR-0042 decision 9 (amended 2026-07-21) makes the dimensionally-correct conversion the primary; `scour_script_k` is the companion |
| L99 to L107 + Table | BEP dominant at 3 of 4; overflow dominates KP 62.0 at 79 per cent; scour "never exceeds 9 per cent" | BEP dominant at **all four** historically (100/97/100/81 per cent); scour **exactly zero** everywhere |
| L120 to L123 | Dominance table values | superseded row by row (`phase3_report.md` 5.1, 11.1) |
| L138 to L139 | Tokachi 4 governs at 8.0e-3 per year | 7.5e-3 |
| L161 to L164 | Median 6.3e-5 to 2.8e-3, factor 44; segments >1e-3 14 to 80; >1e-2 0 to 19 | median **0 to 3.7e-4**; mean 1.0e-4 to 1.9e-3 (about 18x); >1e-3 **2 to 45**; >1e-2 **0 to 4** |
| L165 to L167 | BEP-section system ratios 5.4 to 12.6; KP 58.8 max 4.3e-2 | **5.5 to 12.7** (KP 62.0 12.7 post-ADR-0047); 4.09e-2 |
| L167 to L172 | lambda_ac 40 m bracket "leaves overflow-dominated KP 62.0 nearly unchanged" | KP 62.0 is now BEP-dominant; bracket x3.1 / x1.6 there |
| L172 | Bulk d70 cuts 4 to 25x | about 5 to 15x |
| L173 to L174 | Posterior lowers KP 58.8 by 11 per cent | about 12 per cent |
| L189 to L196 | BEP retains 74 to 95 per cent under +4K; KP 57.4 overflow 0.4 to 20 per cent; surface dominance flips scour 71/114 to overflow 82/114 | **91 to 100 per cent**; KP 57.4 overflow 0 to 9 per cent; scour zero, overflow 31 to 110 |
| L235 to L237 | Scour "2 to 15x conservative" in event-based validation | zero both curve-based and event-based |

**Q3: STAGE.** Ch. 7's content will be re-derived from a campaign that has not run;
writing it now is out of scope and the task instructs staging. Destination
`scratch/staged_results_system_integration.tex` with a dated provenance header.

The five figures it references
(`phase3_system_fragility_bep_sections`, `phase3_dominance_profile`,
`phase3_climate_shift`, `phase3_rq4_attribution`, `phase3_event_based_validation`)
are **not** present in `msc-thesis/figures/`; they exist only in the engine repo under
`docs/figures/`. They must be copied when Ch. 7 is actually written, not now.

---

## 6. Bibliography inventory

**`_thesis_gsa.bib` (11 keys): all 11 already present in `references.bib` under the
same key names.** `saltelli_primer_2008`, `saltelli_2002`, `saltelli_2010`,
`jansen_1999`, `sobol_1993`, `homma_saltelli_1996`, `mara_tarantola_2012`,
`kucherenko_2012`, `owen_1997`, `archer_1997`, `schweckendiek_2014`. All except
`homma_saltelli_1996` are cited in Ch. 5. **Nothing to merge.**

**`_thesis_validation_japan.bib` (5 keys):**

| Fragment key | Status | Thesis key | Cited in Ch. 5 |
|---|---|---|---|
| `okamura_gounokawa_2025` | present under a different name | `Okamura2025_gounokawa` | yes, L206 |
| `sako_gounokawa_2019` | present under a different name | `Sako2019` | yes, L208 and L277 |
| `yabe_levee_committee_2013` | present under a different name | `yabegawa_2013` | yes, L210, L280, L386 |
| `tokoro_levee_committee_2017` | present under a different name | `tokorogawa_2017` | yes, L213, L285 |
| `waseda_gounokawa_dataset_2025` | **genuinely absent** | none | **no** |

**Nothing to merge.** The four mapped keys are already cited under the thesis's own key
names; migrating the fragment keys would create duplicate entries for the same sources
and would alter citation keys, which `msc-thesis/project-notes.md` forbids.

`waseda_gounokawa_dataset_2025` is the only genuinely new entry. It is **not cited
anywhere** in the thesis, so it is not needed. **Flagged, not migrated:** its DOI
(`10.20556/0002006234`) has not been verified against the publisher, and an
uncited, unverified dataset DOI is exactly the kind of entry that should not enter a
thesis bibliography on an audit's initiative. If the Gounokawa companion dataset is
ever cited, verify the DOI first.

**Both `.bib` files also carry a rule conflict:** `_thesis_validation_japan.bib` has
Japanese script in three `titleaddon` fields (Sako, Yabe committee, Tokoro committee).
Under the no-Japanese rule being installed, these must not be migrated as-is. They are
not needed, since the corresponding thesis entries already exist.

---

## 7. Unresolved tensions

1. **The no-CJK premise is false as stated.** The task states that zero CJK characters
   currently exist in any tracked msc-thesis `.tex` or `.bib` file. Measured on disk:
   **24 lines carry CJK.** One is a LaTeX comment in Ch. 3 (L469, a `% TODO(GIJS)`
   naming the soil-layer longitudinal profile; the prose above it at L463 already
   romanises the term, so nothing typesets). The other **23 are live bibliography
   entries in `references.bib`** (Japanese titles, one author name, two note fields,
   across roughly 12 entries including `uemura_phd_2025`, `tokorogawa_2017`,
   `yabegawa_2013`, `oyo_1999`, `obihiro_levee_inspection_2008`). These do typeset, in
   the bibliography. Installing an unconditional whole-document rule therefore puts the
   repository in immediate violation, and remediating it would mean editing
   bibliography entries, which `msc-thesis/project-notes.md` places off-limits and which is
   also a scholarly-integrity question (the Japanese title is the accurate record of a
   Japanese-language source). **This needs the owner's decision and is raised at the
   checkpoint rather than resolved here.**

2. **Ch. 3 L314** still reads "combined with the foreshore-width variation of
   Section ..., this renders r_e ... strongly dependent on the section-specific
   stratigraphy". This is a residue of the refuted foreshore-control argument. It is
   weaker than the refuted claim and is not itself false, and the surrounding passages
   (L30, L193, L305) carry the correction explicitly. Flagged, not smoothed; outside
   this task's scope.

3. **`msc-thesis/scratch/MANIFEST.md` is itself partly stale** on Phase 3. Its
   section 6 and section 9b carry the pre-2026-07-22 RQ3/RQ4 numbers (BEP 88 to 99.9
   per cent, median 6.3e-5 to 2.8e-3 at 44x, segments >1e-3 14 to 80, KP 62.0
   overflow-dominant). These were superseded by the D7 rating-error correction and again
   by ADR-0047. MANIFEST is a working manifest rather than a document of record, and the
   authoritative source is `phase3_report.md` sections 5, 6 and 11; a correction note is
   appended to MANIFEST rather than rewriting its tables.
