# Thesis number reconciliation, 2026-09-03: the material the two earlier passes never covered

**What this is.** A claim-by-claim traceability record for the quantitative
material in `d:\repositories\msc-thesis` that neither of this repository's two
earlier reconciliation passes covered. It follows their method and verdict
vocabulary exactly and is a permanent record.

**The coverage hole it fills.** `docs/thesis_number_reconciliation_2026-08-21.md`
audited the whole document *as it then stood*, at thesis commit `cb590c7`.
`docs/thesis_number_reconciliation_2026-08-30.md` audited only the
reliability-index block added by the campaign of 2026-08-28 to 2026-08-29. The
pre-push gate of 2026-09-02 compared numeric-token **sets** across the
shortening campaign and never checked a value against an artifact. Everything
introduced between those two passes, and not part of the reliability-index
block, had therefore never been traced. That set is what this pass covers,
plus every `FLAG` either earlier pass left open.

**Scope, stated as commits.** The thesis commits inside the hole are
`aab832f` (the conductivity bracket across the survival update), `66a8386`
(critical pipe length and composition seam), `19f6523` (the drained-configuration
bracket), `39ec7ba`, `5981f70`, the 2026-08-23 page-budget campaign,
`3b31ec1` (commensurability and the base-rate check), `e8d8a1a` (the 1998
evaluation criteria), and the 2026-08-27 to 2026-08-28 set `2123f52`,
`2d40fb4`, `ae54b1b`, `b2ba10c`, `e5a8e6c`. Two later additions are included
because no numeric pass had reached them either: the 2016 above-toe durations
that `3443085` substituted on 2026-08-31, and the numbers the shortening
campaign moved between chapters. Every check is against the **current** file
state, at thesis commit `7fdc3ed` plus this pass's six corrections.

**Sources of record used.**

| Source | Covers |
|---|---|
| `docs/decisions/adr0050-drained-configuration-bracket.json` and `.md`, `adr0050-drained-bracket-annualisation-{matrix,bulk}-posterior.json`, `0050-toe-gradient-relief-drained-bracket.md` | the drained-configuration bracket, conditional and annual, and its ranking |
| `docs/decisions/adr0049-critical-length-companion.json`, `adr0049-critical-length-bracket.md`, `0049-critical-pipe-length-override.md` | the critical-pipe-length bracket |
| `docs/decisions/composition-seam-rating-error.json` and `.md` | the Phase 3 axis seam |
| `docs/decisions/conductivity-bracket-posterior-side{,-bulk}.json`, `conductivity-bracket-posterior-side.md` | the conductivity bracket measured across the 2016 update |
| `docs/decisions/conductivity-bracket-annualisation{,-bulk}.json` and `.md` | the conductivity bracket through the annualisation |
| `docs/decisions/annualisation-hazard-sampling-uncertainty.json` and `.md` | every flood-ensemble sampling interval |
| `docs/decisions/r10-foreshore-exhaustion-screening.json` and `.md` | the foreshore-exhaustion indicator |
| `docs/decisions/adr0044-event-closure-bound.json` | the 2011 marginal bound |
| `docs/japanese_levee_failure_criterion_review_2026-08-28.md` | the Japanese-practice block |
| `docs/oyo_1998_framing_review_2026-08-24.md` | the 1998 evaluation criteria and the post-drain toe gradients |
| `docs/phase2_report.md`, `docs/decisions/phase2-survival-update-per-stratum.csv` | above-toe durations, rejection fractions |
| `docs/project_log.md` (2026-08-28), `results/tokachi_kp*.h5`, `results/phase2/*_posterior.h5` | the initiation-gate curve |
| `docs/decisions/canonical-shape-sensitivity.md` | the alternate-event displacement |

**Verdict vocabulary.** Unchanged from 2026-08-21.

| Code | Meaning |
|---|---|
| `EXACT` | Agrees with the named artifact to every digit printed. |
| `ARITH` | Internal-arithmetic check; consistent with the other printed numbers. |
| `ROUND` | A rounding, truncation or interval-informed restatement of an artifact number, not a copy. Recorded, not an error. |
| `FIXED` | Diverged; corrected in the thesis on this date. |
| `FLAG` | Not reconcilable from any artifact, or reconcilable only approximately, or a judgment call. Text left alone; listed for the owner. |
| `CITED` | A literature or official-record value carried by a `\parencite`, not produced by this engine. Not verifiable here. |

---

## 1. Headline statistics

A claim-group is one table, one register row, one figure caption or one
sentence's set of numbers read from the same artifact field in one operation.
A row may carry two verdicts, so the tag counts sum to more than the row count.

| | Count |
|---|---|
| Claim-groups traced (section 5) | **88** |
| Carrying `EXACT` | **70** |
| Carrying `ARITH` | **18** |
| Carrying `ROUND` | **4** |
| Carrying `CITED` | **11** |
| **Diverged and corrected (`FIXED`)** | **7 rows, 6 distinct corrections** (the conductivity-range correction has two sites) |
| **Flagged and left standing (`FLAG`)** | **0** |
| Untraceable to any artifact **and** not a cited value | **0** |

**Two rounds, on one date.** The pass first made the two corrections of section 2
and raised four judgment calls, leaving their text alone for an owner ruling. The
owner ruled on the same date that all four be closed, so section 3 records each
as a correction rather than as an open flag. Every correction in both rounds is a
smallest-possible edit that makes a printed claim agree with its artifact; none
adds a number the thesis did not already carry, none touches a `\label` or a
citation key, and the rebuild after them reproduces the chapter map page for page.

**The one unlocated claim is located.** The Overall Conclusion's base-rate check
(0.65 expected failures in sixty years, 0.52 that none is observed, 0.38 and
0.69 crediting the berm, an aggregate 1.07e-2 per year, 0.091 at 2016 stages)
rests on no artifact of its own. It is an internal arithmetic construction over
the annual piping probabilities and the Phase 2 rejection fractions, introduced
by thesis commit `3b31ec1` of 2026-08-24, whose own message describes it as "a
base-rate check ... added as a positive result". Section 2 reproduces the
arithmetic; two of its six figures did not survive it.

The two `FLAG` rows carried since 2026-08-21 were both closed by the 2026-08-30
pass and neither is reopened here. The 2026-08-30 pass's single residual, the
unplaced figure asset `figures/rq1_beta_curves.png`, **is still open**: the file
exists, the other four figures that commit added are all placed, and no
`\includegraphics` anywhere in the document references it. Nothing numeric turns
on it.

---

## 2. The two arithmetic corrections

These two are the defects the trace itself turned up: a printed figure that
disagrees with the arithmetic it is drawn from. Section 3 carries four more
corrections, all made on the owner's ruling later the same date, none of which
changes a digit. Both corrections below are in the same paragraph of
`mainmatter/8. Discussion.tex` (§ "The Erosion-Limited Consensus", the base-rate
check), and both are character-count-neutral, so no line reflows and no page
moves.

### 2.1 The probability that no failure is observed in sixty years, crediting the berm

* **File / line (post-edit):** `mainmatter/8. Discussion.tex:893`
* **Was:** "crediting the measured berm gives 0.38 and **0.69**."
* **Now:** "... 0.38 and **0.68**."
* **Artifacts:** `annualisation-hazard-sampling-uncertainty.json`
  `sections[*]["matrix/posterior"].historical.p_annual_bep.point` for KP 57.4
  (7.5295e-4) and KP 62.0 (8.58019e-4);
  `adr0050-drained-bracket-annualisation-matrix-posterior.json`
  `per_section[*].scenarios.historical.arms.berm_only.p_annual_bep` for KP 58.8
  (4.13042e-3) and KP 60.0 (6.3946e-4).
* **Reasoning.** Composed independently in series, as the paragraph's own first
  sentence specifies, those four give `p = 6.3699e-3` per year. Over sixty years
  every construction the paragraph could be using returns 0.68, not 0.69:
  `(1 - p)^60 = 0.68153`; `exp(-60p) = 0.68236`; `exp(-60 x sum(p_i)) = 0.68192`.
  To print 0.69 the expected count would have to be at most 0.3785, against the
  0.3822 to 0.3834 these inputs give, and the paragraph's own companion figure
  0.38 is that same count. The as-if-undrained pair is internally consistent and
  needed no change: `p = 1.07216e-2`, expected count `-60 ln(1-p) = 0.6468` and
  `60 x sum(p_i) = 0.6450`, both printing 0.65, with `(1-p)^60 = 0.5237` printing
  0.52. Applying either of those two constructions to the berm arm gives 0.68.

### 2.2 The probability of at least one failure at the stages 2016 reached

* **File / line (post-edit):** `mainmatter/8. Discussion.tex:895`
* **Was:** "the transient model assigns **0.091** to the failure of at least one
  of the four"
* **Now:** "... assigns **0.089** ..."
* **Artifact:** `docs/decisions/phase2-survival-update-per-stratum.csv`,
  `baseline / no_breach` rows, `transient_reject_pct`: 0.065, 5.673, 3.363, 0.000
  per cent. The rejection fraction *is* the prior conditional transient failure
  probability at the anchored 2016 stage
  (`conductivity-bracket-posterior-side.md` §1.3 step 1).
* **Reasoning.** Under the independent series composition the paragraph states,
  `1 - prod(1 - r_i) = 0.089045`. The printed 0.091 is the **sum**,
  `0.065 + 5.673 + 3.363 + 0.000 = 9.101` per cent, which is the expected number
  of failing sections and an upper bound on the union, not the probability that
  at least one fails. The paragraph distinguishes the two quantities correctly
  two clauses earlier ("0.65 expected failures **and** a probability of 0.52 that
  none is observed"), so the mislabel is local. Nothing in the argument turns on
  it: survival remains the modal outcome at 0.911 either way.
* **Owner note.** If the sum was deliberate, the fix is to relabel rather than to
  restore the digits, because "the failure of at least one of the four" has one
  value under the stated composition and it is 0.089.

**Propagation checked.** `0.69` and `0.091` were swept across all 26 tracked
`.tex` files after the edit. The two surviving `0.69` occurrences are unrelated
(a Sobol' index at `mainmatter/5...:523` and the KP 62.0 historical share
interval at `mainmatter/7...:334`); no `0.091` remains. The 0.65 and 0.52 pair is
restated at `mainmatter/8...:584` and `mainmatter/9...:425` and is unchanged at
both, correctly.

---

## 3. The four judgment calls, raised and then closed

Each was raised as a `FLAG` in the first round, with the text left alone and the
smallest available fix named. The owner ruled on the same date that all four be
applied, so each entry below carries its **Now** line. None of the four changes a
number: each supplies the scope a printed number already required, or removes a
grammatical ambiguity around one.

### 3.1 "Every critical rate lies inside the assumed bracket"

* **Site:** `mainmatter/8. Discussion.tex:815-817`.
* **Artifact:** `r10-foreshore-exhaustion-screening.json`,
  `sections[*].{event_2016,design_hwl}.thresholds.z_mob.critical_retreat_rate_m_per_h`.
  At the design water level the four critical rates are 3.00, 3.85, 9.77 and
  0.72 m/h, all inside the assumed 0.1 to 10 m/h bracket, and the sentence is
  exactly true. Under the observed 2016 loading they are 4.35, 4.51, **27.27**
  and 2.59 m/h, and KP 60.0's sits a factor of 2.7 **above** the bracket, so at
  that section under that forcing the indicator does return a verdict.
* **Was:** "**Every critical rate** lies inside the assumed bracket, so the
  indicator delivers an exposure ordering and not a screening verdict."
* **Now:** "**Every design-level critical rate** lies inside the assumed bracket,
  so the indicator delivers an exposure ordering and not a screening verdict."
* **Reasoning.** The engine's own note hedges the same claim ("sits inside **or
  at the edge of** the assumed 0.1-10 m/h range", `r10-...-screening.md` §4.1);
  the thesis dropped the hedge instead of the scope. The design-HWL row set is
  the one the preceding sentences use and the one on which the claim is exactly
  true, so naming it costs a single word and no number. `FIXED`.

### 3.2 The conductivity bracket quoted as "69 to 185" (2 sites)

* **Sites:** `mainmatter/8. Discussion.tex:593` (limitations register) and
  `:905` (§ The Commensurability of the Mechanism Probabilities).
* **Artifact:** `conductivity-bracket-annualisation.json`,
  `sections[*][*].conductivity_span_p_annual_system`. Both endpoints are
  `EXACT`: 69.08 at KP 62.0 historical and 184.83 at KP 58.8 historical. But the
  spans across all eight cells are 27.6, 184.8, 48.6, **4.4e5**, 2762, 69.1, 8.27
  and one undefined, so "69 to 185" is not the range the artifact carries.
* **Was:** "a conductivity bracket worth **69 to 185 annually**" (register) and
  "spanning **its annual probability by a factor of 69 to 185**"
  (§ Commensurability).
* **Now:** "a conductivity bracket worth 69 to 185 annually **at two of the four
  sections historically and more at the other two**" and "spanning its
  **historical** annual probability by a factor of 69 to 185 **at two of the four
  sections and by more at the other two**".
* **Reasoning.** Chapter 7 states it correctly and completely at `:548-551`
  ("spans 69 at KP 62.0 and 185 at KP 58.8 **in the historical climate under the
  conservative grain-size reading**, and more at the other two"), and Chapter 8
  had compressed that into a bare range, dropping both the climate scope and the
  qualifier. Both are needed: without the climate scope the range is false under
  warming, where the four spans are 8.27, 27.6, 48.6 and 2762 and none lies
  between 69 and 185. The correction adds no number; it restores the scope
  Chapter 7 carries. `FIXED` at both sites.

### 3.3 "The two sections whose lowest arm produces no failures at all"

* **Site:** `mainmatter/7. Results - System Integration and Climate
  Sensitivity.tex:551`. The sentence predates `cb590c7`, so it fell outside this
  pass's declared scope; 3.2 sent me to it and the owner ruled it in.
* **Artifact:** `conductivity-bracket-annualisation.json`. At KP 57.4 historical
  the `k_aq_field_geomean` arm gives `p_annual_system` and `p_annual_bep` of
  exactly 0.0, and the span is undefined. At KP 60.0 historical the same arm
  gives 5.17e-8, non-zero, and the span is 4.4e5. It is a clamped lower bound
  (`bep_clamped_cells`), but it is not "no failures at all", and Chapter 7 itself
  prints that value fifty lines earlier ("At the lowest arm that means an annual
  probability of 5.2e-8").
* **Was:** "and more at **the two sections whose lowest arm produces no failures
  at all**."
* **Now:** "and more at **the other two**."
* **Reasoning.** An internal inconsistency of one clause, in a sentence whose
  numbers are all correct. "The other two" is exactly what the artifact supports:
  the span at KP 57.4 historical is undefined and at KP 60.0 historical it is
  4.4e5, both greater than the 185 the sentence has just quoted, whatever the
  mechanism. The correction is the only one of the four that makes the sentence
  shorter, by eight words. `FIXED`.

### 3.4 "25.1 per cent carries a deficiency involving piping, of which 13.8 per cent ..."

* **Site:** `appendix/appendix-f.tex:107-110`.
* **Artifact:** `docs/japanese_levee_failure_criterion_review_2026-08-28.md`
  §J3, transcribing PWRI Figure 6.3.1. Every one of the three figures is a share
  of the **whole** directly managed network: deficient in at least one respect
  40.8 per cent (= 100 - 59.2), piping-involving 25.1 (= 1.5 + 9.5 + 0.3 + 13.8),
  piping-only 13.8.
* **Was:** "25.1~per cent carries a deficiency involving piping, **of which**
  13.8~per cent fails the piping check alone while passing both slope checks".
* **Now:** "25.1~per cent carries a deficiency involving piping. **Of the total
  length,** 13.8~per cent fails the piping check alone while passing both slope
  checks".
* **Reasoning.** The numbers are `EXACT`; "of which" was the problem. Read
  conventionally it makes 13.8 a share of the 25.1, which would be 3.5 per cent
  of the network rather than 13.8; the correct fraction-of-25.1 figure is 55 per
  cent. The correction names the denominator instead of leaving it to be
  inferred, and changes no digit. `FIXED`.

---

## 4. Internal-arithmetic checks

All run without reference to any artifact, or over artifact values only.

| # | Check | Result |
|---|---|---|
| C1 | Table 7.2 `tab: system annual`, all 48 entries against `annualisation-hazard-sampling-uncertainty.json` `sections[*]["matrix/posterior"]` | **Pass, 48 of 48**, each nearest-rounded to the artifact. The two endpoints the 2026-08-21 pass corrected (7.50 and 1.56) are still correct after the shortening campaign moved the table. |
| C2 | Table 7.2 shares equal each contribution over the system total; shares sum to 1.000 per row | **Pass at all 16.** |
| C3 | The four climate-ratio intervals equal `climate_ratio.{ci_low, ci_high}` | **Pass, 8 of 8 endpoints:** 7.3003/28.066, 4.1280/7.7350, 5.3425/12.881, 7.7128/24.766. |
| C4 | Relative half-widths bound the printed "29 to 58" and "11 to 21" per cent | **Pass.** Historical 0.2882 to 0.5831; warming 0.1080 to 0.2165. The upper warming endpoint is truncated, not rounded, which the 2026-08-21 pass already records. `ROUND`. |
| C5 | SST-pattern widening factor = `sst` relative half-width over `member` | **Pass.** 1.659, 2.367, 2.011, 1.744, that is 1.6 to 2.4; the worked example "10.6 to 25.0 per cent" is KP 58.8 warming, 0.10578 and 0.25043. |
| C6 | KP 62.0 warming tie: printed difference and its interval | **Pass.** `difference_p_annual_bep_minus_overflow` point 1.129e-5 (printed 1e-5) on `[-9.232e-4, +9.075e-4]` (printed +/- 9e-4); share 0.500336 on `[0.4763, 0.5325]` (printed 0.48 to 0.53). |
| C7 | Drained-bracket response curve: 1.03, 12, and a cumulative 41 | **Pass.** At KP 58.8's 41.00 m: `berm_only`/`joint_0.80` = 0.10839/0.10481 = 1.034; `joint_0.60`/`joint_0.40` = 0.0754/0.00635 = 11.87; as-if-undrained over `joint_0.40` = 0.26273/0.00635 = 41.4. The cumulative figure is measured from the as-if-undrained baseline, not from the berm arm. |
| C8 | Drained-bracket annual span "up to a factor of 37" | **Pass.** 0.00741954 / 0.000196673 = 37.72 at KP 58.8; the same quotient is `ratio_to_as_if_undrained` 0.0265, printed 0.027. |
| C9 | Post-drain toe-gradient relief, 77 and 76 per cent | **Pass.** 1 - 0.30/1.30 = 76.9; 1 - 0.23/0.97 = 76.3. `oyo_1998_framing_review_2026-08-24.md` §4.2 computes the same two, 76.9 and 76.3. |
| C10 | The strongest arm's lowest initiating stage, 0.7 to 1.0 m above design level | **Pass.** Lowest grid stage with `p_f_trans_arm > 0` in `joint_0.20`: 42.00 m against HWL 41.03 (+0.97) and 43.50 m against 42.75 (+0.75). |
| C11 | ADR-0049 level counts: "eighty-nine levels" | **Pass.** `cancellation[*].levels_evaluated` sums to 16 + 22 + 22 + 29 = 89 on the upper arm, which is the arm the note's identity statement spans. Resolved counts are 16, 21 to 22, 22, 28 to 29. |
| C12 | ADR-0049 displacement ranges | **Pass.** `max_resolved_departure_factor`: lower arm 1.111 to 1.226, upper arm 1.194 to 1.667, so 1.11 to 1.23, 1.19 to 1.67 and 1.11 to 1.67. `max_reciprocal_identity_error` = 2.22045e-16 at all four sections and both arms. |
| C13 | Composition-seam displacements | **Pass.** Overflow displacement at the five loaded cells 1.1645, 1.1677, 1.2220, 1.2400, 1.2629 (1.16 to 1.26), zero at the sixth (KP 60.0 warming, whose whole 2.3e-5 the artifact carries); system displacement max 1.0705 (at most 1.07); share displacement max 0.038684 (at most 0.039). |
| C14 | Posterior-side narrowing factors | **Pass.** Reciprocals of `span_ratio_p_annual_system`: 1.963 and 2.807 historically (1.96 and 2.81), 1.492 and 1.974 under warming (1.49 and 1.97). Rejection ratios 0.6553/0.05673 = 11.55 and 0.86881/0.03363 = 25.83. |
| C15 | The 1998 evaluation table against its own stated criteria | **Pass at all 20 entries.** Every bold cell fails the criterion the caption states (`F_s` < 1.2 landside, < 1.1 riverside; `i` >= 0.5 either direction) and no unbolded cell does. |
| C16 | The leakage geometry in the Chapter 2 figure caption | **Pass.** Recomputed read-only through `bep_reliability_engine.hydraulics` at the prior means: KP 62.0 `lambda_in` 38.73 m (printed approximately 39), `r_e` 0.3514, `Delta h_blanket` 0.5236 m (printed 0.52) on a head difference of 46.39 - 44.90 = 1.49 m; the other three sections `lambda_in` 102.5, 116.6, 87.5 m (printed 87 to 117) at `L` 33, 35, 34.8 m (printed 33 to 35). |
| C17 | The initiation gate against the two piping branches | **Pass.** Reproduced read-only from the persisted Phase 1 matrices and Phase 2 response factors, exactly as `scripts/plot_initiation_fragility.py` does. The gate reaches 0.99 at 40.328, 40.660, 42.243 and 46.504 m against transient medians at 41.077, 41.521, 43.180 and 49.611 m, that is 0.749 to 3.107 m below them (printed 0.75 and 3.11). At KP 62.0's design level 46.39 m, linear interpolation of the raw grid points gives a gate probability of 0.974 (printed 0.97) at a transient probability of 8.8e-5 (printed 9e-5). |
| C18 | The base-rate construction | See section 2. Four of its six figures pass; two did not. |

---

## 5. The register

Rows are claim-groups. "Artifact" names the file and, where useful, the field.

### 5.1 The drained-configuration bracket, ADR-0050 (15 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| A1 | `6...:113-119` register row "Remediation state not credited" | transient 0.263 to 0.108 at KP 58.8, 0.314 to 0.111 at KP 60.0, to zero at four fifths relief | `adr0050-...-bracket.json` `arms.berm_only.levels` at 41.00 and 42.75; `arms.joint_0.20` | EXACT |
| A2 | `7...:116-127` register row "Remediation state not credited" | annual 7.4e-3 to 4.2e-3 and 1.8e-3 to 6.4e-4 on the berm alone; crediting drainage raises the climate ratio | `adr0050-...-annualisation-matrix-posterior.json` (7.41954e-3 to 4.24719e-3; 1.80178e-3 to 6.3946e-4); ratios 5.51 to 6.29 and 7.87 to 10.18 on the berm arm | EXACT + ARITH |
| A3 | `8...:984-987` § What the Model Represents | the same conditional pair | as A1 | EXACT |
| A4 | `8...:987-991` | annual 7.4e-3 to 4.2e-3 to a lower bound of 2.0e-4; 1.8e-3 to 6.4e-4 to zero | `...-annualisation-matrix-posterior.json` `joint_0.20` 1.96673e-4 and 0.0 | EXACT (2.0e-4 `ROUND`) |
| A5 | `8...:991-993` | the strongest arm's lowest initiating stage 0.7 to 1.0 m above each design level | check C10 | ARITH |
| A6 | `8...:975-979` | toe gradient 1.30 to 0.30 and 0.97 to 0.23, a relief of 77 and 76 per cent | `oyo_1998_framing_review_2026-08-24.md` §4.2 (表7-5-1); the percentages check C9 | EXACT + ARITH; underlying values CITED (`oyo_1999`) |
| A7 | `8...:964-968` | the 2025 surface gives 42 and 43 m against the 1998 tables' 35 and 34.8 m, at 31 of 31 usable stations | `adr0050-...-bracket.json` `seepage_length_dem_m`, `seepage_length_1998_m`, `grounding.berm_magnitude_source` | EXACT |
| A8 | `8...:651-655` limitations register | the berm takes the annual probability to 0.57 and 0.35 of the reported value; four fifths of relief to a lower bound of 0.027 and to zero | `ratio_to_as_if_undrained`: 0.572434, 0.354904, 0.0265074, 0.0 | EXACT (0.027 `ROUND`) |
| A9 | `6...:1151`, `8...:174-176` | static condemns 34 per cent against the transient model's 5.4 under the measured berm; 57.6 against 15.6 as-if-undrained | `adr0050-...json` KP 58.8 at 40.75 m: 0.33622 / 0.05434 against 0.57634 / 0.15596 | EXACT (already `EXACT` on 2026-08-30) |
| A10 | `9...:491-501` | annual ranking KP 58.8, KP 60.0, KP 62.0, KP 57.4; KP 58.8 keeps the lead until four fifths of relief; KP 60.0 falls from second to last on the berm alone and stays there | `...-annualisation-matrix-posterior.json` `ranking`, both climates, six arms | EXACT |
| A11 | `9...:549-551` future-research register | KP 58.8 spans up to a factor of 37 annually, its lower end a lower bound | check C8; `joint_0.20.bep_clamped_above_grid` true | ARITH |
| A12 | `appendix-i.tex:392-399` | the first 20 per cent of relief worth 1.03, the step from 40 to 60 per cent worth 12, cumulative 41 | check C7 | ARITH |
| A13 | `appendix-i.tex:391-399` | the conditional pair and the annual triples restated | as A1, A4 | EXACT |
| A14 | `appendix-k.tex:93` drainage-study row | annual span up to a factor of 37 at KP 58.8, to zero at KP 60.0; lead survives, second place does not | as A8, A10 | EXACT |
| A15 | `appendix-k.tex:81` ADR-0050 row | gate-only, the static comparator exactly invariant | `adr0050-...json` `ratio_static` = 1.0 at every arm and level except `berm_only`, where the seepage path also moves | EXACT |

### 5.2 The critical-pipe-length bracket, ADR-0049 (9 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| B1 | `6...:83-90` register row "Critical pipe length" | transient 1.00 to 2.08, ratio 1.11 to 1.67, ratio moves by the reciprocal of the transient displacement | `adr0049-critical-length-bracket.md` §5.1 and §5.2; checks C11, C12 | EXACT |
| B2 | `6...:902-911` § The Dimensional Axis | 1.00 to 2.08; a longer critical length raises the probability; an ingredient of the temporal step, not a fifth component | ADR-0049 §5.1 and §6 | EXACT |
| B3 | `8...:346-357` § Not Every Epistemic Knob Cancels | no common-mode channel; exact reciprocal at all eighty-nine levels; 1.11 to 1.23 and 1.19 to 1.67 | checks C11, C12; `channel_reading` | EXACT |
| B4 | `8...:719-722` limitations register | 1.00 to 2.08 and 1.11 to 1.67 | as B1 | EXACT |
| B5 | `8...:358-362`, `9...:610-613` | the same size as the model factor's 1.07 to 1.22, arrived at by opposite routes | `epistemic-knobs-mp-ztoe.csv` (traced 2026-08-21); ADR-0049 §5.3 | EXACT |
| B6 | `appendix-h.tex:209-228` | factor 1.56 between the 3D case and the relation; 1.00 to 2.08; the critical length is about a fifth of the seepage length | `bracket.upper_factor` 1.55575; `l_c/L` 0.206, 0.219, 0.241, 0.236 | EXACT |
| B7 | `appendix-i.tex:98-128` | eighty-nine levels; 1.11 to 1.23 and 1.19 to 1.67; blanket unit weight departs by 1.15, 1.29, 1.22 and 1.00 | ADR-0049 §4 and §5.2 | EXACT |
| B8 | `appendix-k.tex:80,91` | the ADR row and the critical-length study row | as B1 | EXACT |
| B9 | `9...:314` answers register | critical pipe length named as a condition on the RQ1 answer | ADR-0049 §7 | EXACT |

### 5.3 The composition seam (7 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| C1 | `7...:86-90` register row "Canonical event" | changes the leader at one of eight cells, whose production margin is 1.0013 | `composition-seam-rating-error.json` `kp62_warming_crossing.primary.margin_bep_over_overflow` 1.0013454 | EXACT |
| C2 | `7...:271-289` § Composed Conditional Fragility | every piping quantity unchanged to every digit; system moves by at most 1.07 and a share by at most 0.039; overflow-leading segments 31 to 8 historically and 109 to 69 under warming | `displacement.p_annual_bep` = 1.0 at all eight; check C13; `reach_dominance_counts` | EXACT |
| C3 | `7...:384-406` § Piping Dominates | margin 1.0013; contributions differ by 1e-5 inside +/- 9e-4; the seam lifts overflow by 1.17 to 9.80e-3 against 8.40e-3; margin 0.858; share 0.500 to 0.462 | seam JSON `kp62_warming_crossing`; check C6 | EXACT |
| C4 | `8...:621-630` limitations register | 1.16 to 1.26 on the annual overflow contribution, at most 1.07 on the system probability, at most 0.039 on a share | check C13 | EXACT |
| C5 | `9...:153-157` | the same cell changes hands, margin 1.0013 to 0.858, every piping number untouched | seam JSON | EXACT |
| C6 | `appendix-h.tex:503-521` § The Composition Seam | five of six loaded cells rise by 1.16 to 1.26, the sixth loses its whole 2.3e-5; 31 to 8 and 109 to 69 | check C13; `sections[6].primary.p_annual_overflow` 2.30365e-5 | EXACT |
| C7 | `appendix-k.tex:92` seam-study row | every piping quantity unchanged; 1.16 to 1.26; one ordering reverses | seam JSON | EXACT |

### 5.4 The conductivity bracket on the posterior side (7 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| D1 | `7...:575-579` | the constraint rejects a high-conductivity prior 11.6 to 25.8 times more heavily; 65.5 and 86.9 per cent against 5.7 and 3.4 | `conductivity-bracket-posterior-side.json` `survival_update.by_section`; check C14 | EXACT |
| D2 | `7...:580-583` | closes from the upper end alone, by 1.96 and 2.81 historically and 1.49 and 1.97 under warming; no arm below the adopted mean moves more than 2.8 per cent | `posterior_vs_prior[*][*].span_ratio_p_annual_system`; `P4.largest_downward_arm_movement` 0.0278 | EXACT |
| D3 | `7...:584-587` | what remains is still a factor of 94 at KP 58.8; about a factor of two off a range spanning two to five orders of magnitude | `posterior_span_p_annual_system` 94.137, and 1.58e5 at KP 60.0 historical | EXACT + ROUND |
| D4 | `8...:612-620` limitations register | narrows by a factor of up to 2.81, from its upper end alone, and changes no ordering | as D2; `P6.cells_unchanged` 8 of 8 | EXACT |
| D5 | `9...:217-221` § RQ3 | narrows by up to 2.81; rejects 11.6 to 25.8 times more heavily; all sixteen ordering verdicts reproduced | matrix and bulk `P6`, 8 + 8 = 16 | EXACT |
| D6 | `9...:334`, `9...:352` answers register and short synthesis | up to 2.81 from its upper end; all verdicts reproduce | as D5 | EXACT |
| D7 | `appendix-k.tex:89` update-study row | 11.6 to 25.8; up to 2.81; no downward arm beyond 2.8 per cent; sixteen verdicts; two to five orders of magnitude residual | as D1 to D5 | EXACT |

### 5.5 The conductivity bracket through the annualisation (7 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| E1 | `7...:70-75` register row "Grain-size statistic" | annual system probability down by 1.5 to 37; overflow leads at 2 of 4 | `rq4_annual.csv` bulk against matrix (traced 2026-08-21) | EXACT |
| E2 | `7...:63-68` register row "Aquifer conductivity" | lower arms contest the ordering at 3 of 4 historically and 4 of 4 under warming | `conductivity-bracket-annualisation.json` `ordering_verdict`: COLLAPSED, REVERSED, ROBUST, REVERSED historically; REVERSED x 4 under warming | EXACT |
| E3 | `7...:505-508`, `9...:198-201`, `9...:343` | the regional upper bound takes the KP 62.0 piping share to 0.986 historically and 0.892 under warming | `arms.k_aq_regional_upper.share_bep` 0.9857289 and 0.8920358 | EXACT |
| E4 | `7...:704-712` § The Climate Ratios | downward arms reach 234 at KP 57.4 and 671 at KP 60.0; the upward arm gives 3.4 to 7.3 | `climate_ratio_plus4k_over_historical`: 234.144, 671.184; 3.432, 4.178, 5.039, 7.253 | EXACT |
| E5 | `8...:903-908` § Commensurability | a conductivity bracket worth 69 to 185 on the annual probability; a second gradation reading worth 1.5 to 37; the model factor multiplying the transient branch by up to 2.8 | both endpoints EXACT; the range now carries its scope, see 3.2 | EXACT endpoints, **FIXED** scope |
| E6 | `8...:592-595` limitations register | the same three figures | as E5 | EXACT endpoints, **FIXED** scope (same correction, second site) |
| E7 | `7...:531` | historically the bracket narrows from 185 to 4.4 under the resistant reading | matrix 184.827 against bulk 4.398 at KP 58.8 historical | EXACT |
| E8 | `7...:548-551` | the bracket spans 69 at KP 62.0 and 185 at KP 58.8 historically under the conservative reading, and more at the other two | `conductivity_span_p_annual_system` 69.08 and 184.83; undefined at KP 57.4 historical and 4.4e5 at KP 60.0 historical | EXACT; **FIXED** the qualifier, see 3.3 |

### 5.6 The flood-ensemble sampling intervals (11 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| F1 | `7...:345-352` Table 7.2, system column | 8 point values and 16 interval endpoints | check C1 | EXACT, 24 of 24 |
| F2 | `7...:345-352` Table 7.2, mechanism columns | 8 piping values, 8 overflow values, 16 shares | check C1, C2 | EXACT, 32 of 32 |
| F3 | `7...:320-335` Table 7.2 caption | 11.8 per cent above the attainable maximum; exactly zero overflow in all 3,000 simulated years; the KP 62.0 shares 0.69 to 0.98 and 0.48 to 0.53 | `frac_of_annual_piping_above_attainable_max` 0.11787; `n_years` 3000; Q3 `[0.6903, 0.9795]`; Q2 `[0.4763, 0.5325]` | EXACT |
| F4 | `7...:694-697` | ratios 12.7, 5.5, 7.9 and 12.7 on intervals 7.3 to 28.1, 4.1 to 7.7, 5.3 to 12.9 and 7.7 to 24.8 | check C3 | EXACT |
| F5 | `7...:723-726`, `appendix-e.tex:386-388` | half-widths 29 to 58 per cent historically and 11 to 21 under warming | check C4 | ROUND (upper warming endpoint 21.65 truncated) |
| F6 | `7...:739-743`, `8...:765` | treating the six SST patterns as sampled widens the warming intervals by 1.6 to 2.4 | check C5 | EXACT |
| F7 | `7...:746-760` | 7 of 5,400 warming years, 0.13 per cent, above 50.5 m; 4 of the 7 above the first hypothetical level; 11.8 per cent of the contribution; exactly zero historically and at KP 57.4 in both climates | hazard CSV and `driving_stage_band` (traced 2026-08-21; re-verified in place after the shortening campaign) | EXACT |
| F8 | `appendix-e.tex:452-455` | the widening worked at one cell, 10.6 to 25.0 per cent | check C5, KP 58.8 warming | EXACT |
| F9 | `9...:428-432` | 5.5 to 12.7, each on a sampling interval of roughly a factor of two, the two outer sections not distinguishable from each other | `Q1.pairs["KP 57.4 - KP 62.0"].resolved` false, 5 of 6 pairs resolve | EXACT |
| F10 | `7...:378-383` | the KP 62.0 warming split is a tie, third decimal not an estimated digit | `Q2.resolvably_not_a_tie` false, `three_decimal_quotation_supported` false | EXACT |
| F11 | `7...:363-370`, `9...:149-151` | piping about 70 to 100 per cent historically; 97 at KP 58.8; 81 at KP 62.0 on 69 to 98 | `Q3`; `rq4_annual.csv` (traced 2026-08-21) | EXACT |

### 5.7 The foreshore-exhaustion indicator (5 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| G1 | `8...:807-811` | exposure spans roughly an order and a half of magnitude; KP 62.0, with 44 m of high-water bed, is the only section whose flag trips at 1 m/h in either climate | `r10-...-screening.md` §5 (~38x across the four sections and the two design-class forcings, 0.72 to 27.3 m/h); §4.4 ensemble flag shares 1.2 to 3.6 per cent at KP 62.0 against 0 per cent at the other three; `foreshore_width_m` 44.0 | EXACT |
| G2 | `8...:815-817` | every design-level critical rate lies inside the assumed bracket, so the indicator delivers an ordering and not a verdict | design-HWL `critical_retreat_rate_m_per_h` 3.00, 3.85, 9.77, 0.72, all inside 0.1 to 10; see 3.1 | **FIXED** scope |
| G3 | `8...:824-833` figure caption | a retreat-rate bracket spanning two orders of magnitude; the critical rate that exactly consumes the bed | `retreat_rate_bracket_m_per_h` 0.1 to 10.0; `v* = B_f / T_mob` | EXACT |
| G4 | `9...:591` | ordering robust across two orders of magnitude of retreat rate and a one-meter band on the mobilization threshold; coverage at 4 of 114 | `threshold_offsets_m` [-1.0, 0.0, +1.0]; `coverage.n_screened` 4 of 114; §4.2 ordering unchanged across the band | EXACT |
| G5 | `appendix-i.tex:226-256` | the construction; the 2011 datum of roughly five meters of levee length per hour | `not_a_probability`, `retreat_rate_provenance`, `narrative_2011` 5.0 | EXACT; the 2011 datum CITED (`tokachi_chisuishi_2023`) |

### 5.8 The event-set closure bound (1 group)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| H1 | `frontmatter/summary.tex:12`, `6...`, `9...:463` | a bounding 2011 replay adds at most 0.316 per cent | `adr0044-event-closure-bound.json` `strata[*].marginal_beyond_2016_fraction`, maximum 0.00316 at KP 60.0 matrix, 0.0 at the other seven | EXACT |

### 5.9 The Japanese-practice block (6 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| I1 | `2...:12` | safety below the HWL is demonstrated, not presumed, and the demonstration fails on 40.8 per cent of the directly managed network | `japanese_levee_failure_criterion_review_2026-08-28.md` §J3 (100 - 59.2) | EXACT; underlying CITED (`pwri_2014`) |
| I2 | `appendix-f.tex:102-106` | of approximately 10,000 km, 8,800 km verified by March 2008 and the remainder by the end of fiscal 2009 | review §J3 | CITED (`mlit_river_management_2009`) |
| I3 | `appendix-f.tex:107-110` | 40.8 per cent deficient, 25.1 per cent piping-involving, 13.8 per cent piping-only, all of the total length | review §J3 table: 1.5 + 9.5 + 0.3 + 13.8 = 25.1 | EXACT + ARITH; **FIXED** denominator, see 3.4 |
| I4 | `appendix-f.tex:95-99`, `8...` | verification waived where a cohesive blanket of approximately 3 m or more overlies the foundation and the height does not exceed 10 m; the four study sections are a factor of three to seven short | review §J2; blankets 0.45 to 0.85 m, so 3/0.85 = 3.5 and 3/0.45 = 6.7 | CITED + ARITH |
| I5 | `appendix-f.tex:117-120` | of the 72 nationally managed sites at which overtopping was confirmed in 2019, 58, or 81 per cent, did not breach | review, project log 2026-08-28; 58/72 = 0.806 | CITED + ARITH |
| I6 | `8...:881-884`, `appendix-i.tex:365`, `appendix-a.tex:610-617` | 25.1 per cent restated twice; the Obihiro regional comparator 359.8 of 398.2 km inspected (90 per cent), 66.7 km deficient (19 per cent) | review §J3; `obihiro_levee_inspection_2008` | EXACT + CITED; 90 and 19 per cent ARITH |

### 5.10 The base-rate check in the Overall Conclusion (7 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| J1 | `8...:887-890` | the four characterized segments compose in series to an annual piping probability of 1.07e-2 | series of the four `p_annual_bep` points = 1.07216e-2 (the sum, 1.07502e-2, would print 1.08e-2) | ARITH |
| J2 | `8...:891-892` | 0.65 expected failures over sixty years | `-60 ln(1-p)` = 0.6468, `60 x sum(p_i)` = 0.6450 | ARITH (the narrowest reading, `60 p`, gives 0.643; the construction is the expected count, not the expected number of failing years) |
| J3 | `8...:892-893` | a probability of 0.52 that none is observed | `(1-p)^60` = 0.5237 | ARITH |
| J4 | `8...:893` | 0.38 crediting the measured berm | `60 x sum(p_i)` = 0.3829 | ARITH |
| J5 | `8...:893` | 0.69 that none is observed, crediting the berm | every construction gives 0.68 | **FIXED**, see 2.1 |
| J6 | `8...:894-896` | 0.091 assigned to the failure of at least one of the four at 2016 stages | series of the four rejection fractions = 0.089045 | **FIXED**, see 2.2 |
| J7 | `8...:584-585`, `9...:424-426` | the register and Chapter 9 restatements of 0.65 in sixty years against zero observed | as J2 | ARITH |

### 5.11 Residual claims inside the hole, belonging to no named block (12 groups)

| # | Site | Claim | Artifact | Verdict |
|---|---|---|---|---|
| K1 | `6...:224-226` | the uplift and heave gate is effectively certain 0.75 to 3.11 m below the level at which the transient branch reaches one half | `docs/project_log.md` entry of 2026-08-28; reproduced here, check C17 | EXACT |
| K2 | `6...:226-228` | at KP 62.0 the gate already stands at 0.97 where the transient probability is 9e-5 | check C17, interpolated to the design level 46.39 m as the thesis does elsewhere | EXACT + ARITH |
| K3 | `2...:134-137` figure caption | the 0.45 m blanket; the whole 1.49 m head difference | `tokachi_bep_inputs.csv` `D_bl_m`; HWL 46.39 minus `z_toe` 44.90 | EXACT + ARITH |
| K4 | `2...:142-143` figure caption | the 0.52 m surviving at the landside toe is the gate head | check C16 (`r_e` 0.3514 x 1.49 = 0.5236) | EXACT |
| K5 | `2...:157-158` figure caption | both leakage lengths drawn at approximately 39 m | check C16 (`lambda_in` 38.73 m) | EXACT |
| K6 | `2...:158-160` figure caption | at the other three sections the foreshore is 200 to 600 m, the leakage lengths 87 to 117 m, and L stays between 33 and 35 m | CSV `foreshore_width_m`; check C16; `L_m` 33, 35, 34.8 | EXACT |
| K7 | `appendix-a.tex:624-650` `tab:app_safety_summary` | 20 entries plus the two criteria and their thresholds | `oyo_1998_framing_review_2026-08-24.md` §4.2 (`i_v` 0.04, 1.30, 0.50, 0.97, 0.28) and §8.2 (`F_s` 1.104 at KP 57.4); check C15 | EXACT for the traced cells, CITED for the rest (`oyo_1999`); ARITH for the bolding |
| K8 | `appendix-a.tex:652-673` `tab:app_safety_slipcircle` | five rows of Form 7 slip-circle detail; the landside and riverside `F_s` reproduce the summary table | internal cross-check against `tab:app_safety_summary`, all 10 values identical | ARITH; underlying CITED |
| K9 | `8...:693-696`, `8...:1034-1037` | the shorter approved event moves the peak-only factor to 1.45 to 1.57 and raises the static-to-transient bias about threefold | `canonical-shape-sensitivity.md` §2.4 ("rises, and roughly triples"; 13.2 to 41.0 and 13.5 to 32.3 at the two ladder sections) and §2.2 (1.8 to 2.1 at the drained sections) | EXACT |
| K10 | `appendix-i.tex:357-366` | 1 per cent of an estimated 1,735 Dutch dike failures 1134 to 2006 attributed to piping and two thirds to inner-slope or crest erosion; overflow caused 86 per cent of the 140 Hagibis breaches and seepage 1 per cent | `vanbaars_2009`, `mlit_2020_breach`; the 140 count corrected from 142 by the 2026-08-31 citation pass | CITED |
| K11 | `3...:44` | the 2016 event holds the stage above the landside toe for 9, 24, 31 and 6 hours; the 1998 design plateau lasts 1.5 hours against 6 to 31 hours here | `docs/phase2_report.md` §, hours-at-or-above-toe column: 9, 24, 31, 6; `appendix-d.tex` design waveform | EXACT (substituted by `3443085`; not previously traced by any numeric pass) |
| K12 | `2...` model-lineage table, and `appendix-b.tex` | the Sellmeijer regression fitted on sands of experimental mean diameter 0.208 mm | `sellmeijer_2011` | CITED |

---

## 6. Whole-document gates

Run over all 26 tracked `.tex` files, skipping the gitignored `scratch/`.
Scripts were session scratch files; every number they read is named here.

| Gate | Result |
|---|---|
| Every `\ref` resolves; no `\label` duplicated | **Pass.** 387 labels, 292 distinct referenced labels, **0 dangling, 0 duplicates**. 95 labels are defined and never referenced, which is normal for sectioning labels. **Two matcher traps, not one.** Newline normalization inside `\ref{...}` is required: without it a naive scan reports 24 false dangling references at this document state. And this thesis's labels **contain commas** (`chap: Study Area, Geological Setting, and Data`), so a matcher that comma-splits `\ref` arguments the way it must split `\cite` arguments reports a further 14 false positives. Split for `\cite` and `\cref`; never for `\ref`. |
| No em dash in any form in typeset content | **Pass.** 0 occurrences of U+2014; 0 occurrences of `---` outside `%` comment lines. |
| No Japanese script in any `.tex` file | **Pass.** 0 hiragana, katakana or CJK ideographs on any non-comment line. `references.bib` is exempt by the standing agreement and was not scanned. |
| No range written with a hyphen or en dash | **Pass.** 0 en dashes anywhere. 15 hyphen-joined numeric pairs survive the filter and none is a range: 11 `\cmidrule(lr){a-b}` column specifications, the borehole identifier `62.0-1` at `appendix-a.tex:338` and `:435`, the expression `$(1 - 1/K)^{K}$` at `appendix-e.tex:399`, and a date inside the Appendix K register. |
| Every `\cite` key resolves in `references.bib` | **Pass.** **106** distinct keys cited, 158 bib entries, **0 unresolved**. |
| Eleven appendices agree across the roadmap figure, Section 1.6 and `report.tex` | **Pass.** `report.tex` inputs `appendix-a` to `appendix-k`, eleven files; the roadmap figure's appendix node names **A** to **K** in four groups; Section 1.6 says "eleven appendices". |
| *(added)* Isolated faithful build | **Pass, run twice, before and after the section 3 corrections, with an identical result.** Copied `report.tex`, the class, `references.bib`, `frontmatter/`, `mainmatter/`, `appendix/` and `figures/` into a scratch directory and ran `latexmk -xelatex` there, per the standing method. **Main body 99 pages, References on 100**; Ch1 6, Ch2 10, Ch3 12, Ch4 12, Ch5 11, Ch6 18, Ch7 12, Ch8 11, Ch9 7; eleven appendices to page 193. **Zero undefined references and zero undefined citations.** The only log warnings are the recorded IPAexMincho italic substitution in the bibliography and five cosmetic biber legacy-month notices. The ceiling of 100 is met with one page of margin. The section 2 corrections are character-count-neutral; the section 3 corrections add about twenty words to Chapter 8 and remove eight from Chapter 7, and the rebuild reproduces every chapter's first page exactly, so none of them cost a page. |

---

## 7. What this pass did and did not do

* **It did not re-run the engine.** No sweep, no Phase 2 replay, no Phase 3
  composition, no campaign. Two read-only reproductions were made from persisted
  artifacts, because the claims they check have no companion file: the
  initiation-gate curve (check C17, reading `results/tokachi_kp*.h5` and
  `results/phase2/*_posterior.h5` exactly as `scripts/plot_initiation_fragility.py`
  does) and the leakage geometry of the Chapter 2 figure (check C16, calling
  `bep_reliability_engine.hydraulics` at the prior means). Neither wrote anything.
* **It did not change a computed value in the engine.** No `Config` default, no
  artifact, no ADR, no figure.
* **It did not re-audit the reliability-index block.** That is
  `docs/thesis_number_reconciliation_2026-08-30.md`, whose verdicts stand. Where
  a claim in this pass touches that block (A9, B5, B9), the row says so.
* **It did not re-audit anything the 2026-08-21 pass covered**, except where a
  number the shortening campaign moved had to be re-checked in its new position:
  Table 7.2 in full (checks C1 and C2), the Chapter 7 attainable-range paragraph
  (F7), and the Chapter 6 design-level fragility table.
* **It did not verify `CITED` values against their sources.** The Japanese
  official-record figures and the OYO 1998 tabulations are recorded as
  transcribed in this repository's provenance and review documents, not as
  independently re-read. The citation audits of 2026-08-30 and 2026-08-31 are the
  record for that.
* **It did not touch page budget or layout.** The two arithmetic corrections
  replace a digit with a digit; the four scope corrections were measured against a
  rebuild that reproduces the chapter map page for page.

---

## 8. What is still open

**One residual, carried from 2026-08-30, and it is not numeric.**
`figures/rq1_beta_curves.png` is present in the repository and referenced by no
`\includegraphics`. Place it or remove it.

**No flag is left standing.** The four judgment calls this pass raised were all
closed on the owner's ruling of the same date and are recorded as corrections in
section 3. None of them changed a number: 3.1 and 3.2 supply a scope a printed
figure already required, 3.3 replaces a mechanism claim by the plain count it was
standing in for, and 3.4 names a denominator the sentence left to be inferred.

**Nothing else.** Every number in a results chapter and in the Summary that this
pass examined resolves to a named artifact or to arithmetic over other printed
numbers. Combined with the two earlier passes, no quantitative claim anywhere in
`msc-thesis` is now untraced.

---

## 9. Provenance of this record

* Date of pass: 2026-09-03.
* Thesis state read: `msc-thesis` at `7fdc3ed`, plus the six corrections of
  sections 2 and 3, all made on this date, in
  `mainmatter/8. Discussion.tex` (four sites),
  `mainmatter/7. Results - System Integration and Climate Sensitivity.tex` and
  `appendix/appendix-f.tex`.
* Engine state read: `bep-reliability-engine`, branch
  `feature/critical-length-and-composition-seam`.
* Every check is reproducible from the artifacts named in the register, by the
  JSON path or the document section given beside each claim.
