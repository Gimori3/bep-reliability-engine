# Thesis number reconciliation, 2026-08-30: the reliability-index block

**What this is.** A claim-by-claim traceability record for the block of material
added to `d:\repositories\msc-thesis` by the supervisor-directed campaign of
2026-08-28 to 2026-08-29, which the 2026-08-21 pass
(`docs/thesis_number_reconciliation_2026-08-21.md`) predates and therefore never
covered. It follows that pass's method and verdict vocabulary exactly, and it is
a permanent record. It supersedes nothing; the 2026-08-21 register stands for
everything outside this block.

**Scope of this pass.**

1. The reliability-index re-expression of the RQ1 comparison: every
   `\Delta\beta` value in the thesis, its intervals, and every statement about
   how `\Delta\beta` behaves with stage.
2. The additive comparator ladder in index terms: `tab: gap components beta`
   in `mainmatter/6.` and the waterfall figure `fig: gap waterfall` beside it.
3. The equal-head-convention comparison: `tab: equal convention`,
   `sec: The Two Criteria on One Head Convention`, and every restatement of
   the retained-fraction range.
4. Every restatement of 1 to 3 in `frontmatter/summary.tex`,
   `mainmatter/8. Discussion.tex` and
   `mainmatter/9. Conclusions and Recommendations.tex`.
5. The Chapter 6 standing-conditions register (`tab: piping conditions
   register`) and the Chapter 7 one (`tab: system conditions register`), both
   rebuilt in the same campaign.
6. The Chapter 9 answers register (`tab: answers register`).
7. The five campaign commits' own edits, verified against the artifacts they
   claim (`git log` in the thesis repository: `943d6f9`, `bc59c62`, `7387ca6`,
   `2ce2e0a`, `90d69e6`, `5579bbf`, `6970ded`).

**Sources of record used.**

| Source | Covers |
|---|---|
| `docs/rq1_beta_reexpression_2026-08-28.md` and `docs/decisions/rq1-beta-reexpression.json` | every `\Delta\beta`, every additive ladder step, the epistemic arms in index terms, the canonical-event displacement, the stage behaviour |
| `docs/decisions/equal-head-convention-study.md`, `docs/decisions/adr0051-equal-head-convention.json`, `docs/decisions/0051-crack-resistance-factor-equal-head-convention.md` | the equal-convention table, the retained fractions, the two readings, the flip counts |
| `docs/decisions/adr0040-hwl-bias-resolution.json` | `B` and its bootstrap intervals, the resolution criteria, the `\geq 148` bound |
| `results/hwl_bias_resolution/stage_d_epistemic.json` | the epistemic arms at both sections |
| `docs/decisions/adr0050-drained-configuration-bracket.json` | the drained bracket in the Chapter 6 and Chapter 7 registers |
| `docs/decisions/0048-prior-mean-epistemic-scenarios.md` | the factor-46 conductivity displacement |
| `docs/literature_claim_calibration_2026-08-29.md` (as cited by the campaign) | the nine literature-carried claims |

**Verdict vocabulary.** Unchanged from 2026-08-21.

| Code | Meaning |
|---|---|
| `EXACT` | Agrees with the named artifact to every digit printed. |
| `ARITH` | Internal-arithmetic check; consistent with the other printed numbers. |
| `ROUND` | A rounding, truncation or interval-informed restatement of an artifact number, not a copy. Recorded, not an error. |
| `FIXED` | Diverged; corrected in the thesis on this date. |
| `FLAG` | Not reconcilable from any artifact, or reconcilable only approximately. Text left alone; listed for the owner. |
| `CITED` | A literature or official-record value carried by a `\parencite`, not produced by this engine. Not verifiable here. |

---

## 1. Headline statistics

Counts are of rows in the section 5 register, which is the unit at which a
divergence would be actionable. A row may carry two verdicts, so the tag counts
sum to more than the row count.

| | Count |
|---|---|
| Claim-groups in the register (section 5) | **95** |
| Carrying `EXACT` | **71** (58 alone, 11 with `ARITH`, 1 with `CITED`, 1 with `FIXED`) |
| Carrying `ARITH` | **22** (9 alone, 11 with `EXACT`, 1 with `FIXED`, 1 alongside a closed flag) |
| Carrying `ROUND` | **1** |
| Carrying `FIXED` | **11 rows, 7 distinct corrections** (the retained-fraction denominator alone is one correction at four sites) |
| Carrying `CITED` | **4** |
| **New `FLAG`: not reconcilable, text left alone** | **0** |
| Untraceable to any artifact and not a cited value | **0** |

The one `FLAG` token in the register marks the *closing* of a 2026-08-21 flag,
not the opening of a new one. The six internal-arithmetic checks of section 3
and the six whole-document gates of section 4 are counted in neither table;
they are reported in full there.

The two `FLAG` rows carried by the 2026-08-21 pass are both closed, neither of
them by this pass:

* §3.1, the "factor of about 2.9" conductivity spread, was corrected by campaign
  commit `2ce2e0a` to 2.5 either side of the median with the construction stated
  (`exp(1.96 \sigma_{\ln}) = 2.52` at `\sigma_{\ln} = 0.472`, percentile span
  6.4). Re-derived here from `CoV(k_aq) = 0.50`: `\sigma_{\ln} = 0.47238`,
  `exp(1.96\sigma) = 2.5238`, `exp(3.92\sigma) = 6.372`. `ARITH`, both sites
  (`mainmatter/8...:1081`, `appendix/appendix-e.tex:217`).
* §3.2, the 234-hour Abashiri duration, is recorded by the same commit as
  confirmed verbatim in the cited 2008 inspection maps. `CITED`, closed.

No new `FLAG` was opened. Every number in the block resolves to an artifact.

---

## 2. The seven corrections

All seven are defects introduced or left standing by the campaign. None requires
re-running the engine; none changes a measured value.

### 2.1 The retained and removed fractions used different denominators (4 sites)

* **Files / lines (post-edit):** `frontmatter/summary.tex:10`;
  `mainmatter/6...:1649`; `mainmatter/8. Discussion.tex:64`;
  `mainmatter/9...:66`.
* **Was:** the head convention "removes ... only **17 to 46** per cent" of the
  reliability-index difference.
* **Now:** "**17 to 37** per cent".
* **Artifact:** `docs/decisions/adr0051-equal-head-convention.json`,
  `delta_beta_eq` against `delta_beta_production` at the four design anchors.
* **Reasoning.** The removed fraction is by construction `100 -` the retained
  fraction, and the thesis states its retained fraction as **63 to 83 per cent
  at the four design levels, taking KP 57.4 against its bound** (six sites,
  each carrying that qualifier since commit `7387ca6`). The four retained
  values on that convention are 63.26, 66.32, 71.79 and 83.02, whose
  complements are 36.74, 33.68, 28.21 and 16.98, that is **17 to 37**. The
  printed 46 is `100 - 54.06`, which uses KP 57.4's *point* estimate 1.558 as
  denominator, the below-floor value the same campaign commit deliberately
  removed from the retained-fraction range and which the thesis elsewhere
  refuses to quote. Commit `7387ca6` changed "54 to 83" to "63 to 83" at seven
  sites and did not carry the change into the complement, leaving one paragraph
  in each of four chapters asserting both conventions at once.

### 2.2 The `\Delta\beta` interval was described as a mapped Clopper-Pearson interval

* **File / lines (post-edit):** `mainmatter/6...:421-426`.
* **Was:** "`\Delta\beta` is a monotone re-expression of `B`'s two ingredients,
  not an independent measurement, **and its confidence intervals are the same
  exact Clopper-Pearson intervals mapped through that transform**."
* **Now:** "... not an independent measurement. Each branch's own `\beta`
  interval is the exact Clopper-Pearson interval on its failure count mapped
  through that transform; the intervals on `\Delta\beta` and on `B` are paired
  bootstraps over the shared realization set."
* **Artifact:** `docs/decisions/rq1-beta-reexpression.json`, `metric`
  (`delta_beta_interval_method: paired percentile bootstrap over the shared
  realization set`, `n_bootstrap: 1000`) and
  `design_anchors.kp62_0.delta_beta_ci_source: paired_bootstrap`;
  `docs/decisions/adr0051-equal-head-convention.json`, `metric_definitions`
  (10 000 replicates for the equal-convention arm);
  `docs/decisions/adr0040-hwl-bias-resolution.json`,
  `preregistered_criteria.bootstrap_replicates: 10000` for `B`.
* **Reasoning.** The claim is false as printed and is the one methodological
  statement in the block that a reader can test. At KP 62.0's anchor the naive
  Clopper-Pearson difference is `[0.8284, 0.9834]` while the reported interval
  is `[0.8516, 0.9693]`; the first is the artifact's
  `delta_beta_lower_bound` construction, not its interval. The per-branch
  statement *is* true and is verified exactly here (check C2 below), so the
  correction keeps it and adds what was missing. Chapter 4's own methodology
  sentence, "an interval on `P_f` maps to one on `\beta` by exchanging its
  endpoints", is about a single branch and needed no change.

### 2.3 The epistemic-arm span was attributed to conductivity alone (2 sites)

* **File / lines (post-edit):** `mainmatter/6...:1667-1670`;
  `mainmatter/9...:86-88`.
* **Was:** "**conductivity alone** displaces `B` at the KP 62.0 anchor by a
  factor of 10.5 across its resolved arms and the same arms in `\Delta\beta` by
  only 0.11".
* **Now:** "the resolved epistemic arms span a factor of 10.5 in `B` at the
  KP 62.0 anchor, the conductivity arm setting their lower end, and only 0.11
  in `\Delta\beta`".
* **Artifact:** `docs/rq1_beta_reexpression_2026-08-28.md` §5 and
  `results/hwl_bias_resolution/stage_d_epistemic.json`. The four arms clearing
  the R1 floor are `m_p` (B 27.20, `\Delta\beta` 0.970),
  `k_aq_regional_upper` (2.59, 0.863), `gamma_bl_sub_lower` (26.92, 0.904) and
  `z_toe_minus0.30m` (13.87, 0.880). Their span is `27.20/2.59 = 10.50` and
  `0.970 - 0.863 = 0.107`.
* **Reasoning.** 10.5 and 0.11 are the span across *all* resolved arms, whose
  upper end is the Sellmeijer model factor, not a conductivity arm. Conductivity
  alone moves `B` from the production 26.92 to 2.59, a factor of 10.4, and
  moves `\Delta\beta` from 0.904 to 0.863, that is by 0.04, not 0.11. The
  chapter's own careful statement three hundred lines earlier
  (`mainmatter/6...:638-642`, "restricted to arms with adequate counts it runs
  from 2.59 to 27.2 ... the same arms span `\Delta\beta` 0.86 to 0.97") is
  correct and was left alone, as were the identical statements at
  `mainmatter/5...:976` and `mainmatter/8...:364`.

### 2.4 The same mis-attribution in the Chapter 9 answers register

* **File / line (post-edit):** `mainmatter/9...:322` (`tab: answers register`, row 1,
  "Conditional on" column).
* **Was:** "Aquifer conductivity, up to a factor of 46 at KP 62.0
  **(0.11 in `\Delta\beta`)**".
* **Now:** "... (the resolved arms spanning `\Delta\beta` 0.86 to 0.97)".
* **Artifact:** the factor 46 is `docs/decisions/0048-prior-mean-epistemic-scenarios.md`,
  the `k_aq_field_geomean` resolved departure 45.6 at KP 62.0; the index figures
  are the `stage_d` resolved arms above. The two are different arm sets and
  different quantities, so the parenthetical had to name what it belongs to.

### 2.5 A conductivity-scoped sentence used the model-factor endpoint

* **File / line (post-edit):** `mainmatter/9...:501`.
* **Was:** "At KP 62.0's design level the index moves by **0.86 to 0.97**
  depending on which aquifer conductivity is the right one, against a
  probability factor of 2.59 to 26.9".
* **Now:** "... the index moves by **0.86 to 0.90** ...".
* **Artifact:** as 2.3. The sentence's own probability range, 2.59 to 26.9, is
  the conductivity range (regional-upper arm against the production prior
  mean), so its index counterpart is 0.863 to 0.904. The 0.97 endpoint belongs
  to the `m_p` arm, which is not a conductivity reading.

### 2.6 "One of them" understated how many epistemic arms are one-sided

* **File / lines (post-edit):** `mainmatter/6...:641-644`.
* **Was:** "(0.76 to 0.97 including three point estimates below the resolution
  floor, **one of them itself only a one-sided bound**, `\Delta\beta \geq 0.49`)".
* **Now:** "(... each defensible only as a one-sided bound, the lowest at
  `\Delta\beta \geq 0.47`)".
* **Artifact:** `docs/decisions/rq1-beta-reexpression.json`,
  `epistemic.sections.kp62_0.arms`. All three below-floor arms are reported as
  bounds in the source of record: `k_aq_field_toe` `\geq 0.4685`,
  `z_toe_plus0.30m` `\geq 0.4903`, `L_withdrawn_1998` `\geq 0.6464`. The
  printed 0.49 belonged to the middle one while the parenthetical's 0.76
  endpoint is the first one's point estimate, so a reader would attach the bound
  to the wrong arm.

### 2.7 Two display-rounding gaps a reader can check by adding the printed digits

* **File / lines (post-edit):** `mainmatter/6...:736-739` (caption of
  `tab: gap components beta`).
* **Was:** "the three steps sum to `\Delta\beta_\mathrm{total}` regardless of
  order."
* **Now:** "... regardless of order, every entry being rounded independently so
  that a printed row may differ from its printed total by 0.01."
* **Reasoning.** The steps sum to the total exactly in the unrounded artifact at
  all nine rows (check C3 below, residual 0.00e+00 everywhere), but at two
  decimal places four rows do not add up on the page: 46.39 m and 46.50 m at
  KP 62.0 print `0.36 + 0.00 + 0.55 = 0.91` against a total of 0.90; 50.50 m
  prints 1.66 against 1.65 in both the step sum and the endpoint difference;
  40.50 m at KP 57.4 prints a step sum of 1.11 against 1.12. No number changes;
  the caption now states the convention rather than inviting the check to fail.

---

## 3. Internal-arithmetic checks

Script: `scratchpad/final_checks.py` of this session, reading only
`docs/decisions/rq1-beta-reexpression.json` and
`docs/decisions/adr0051-equal-head-convention.json`. All six requested checks
were run. Result: **no failures.**

| # | Check | Result |
|---|---|---|
| C1 | Every `\Delta\beta` equals `\beta_transient - \beta_static` from the same row | **Pass, 21 of 21.** Residual exactly 0 at all nine ladder rows and all four design anchors (the artifact stores the difference, not an independently computed field); residual at most 4e-6 at the eight equal-convention cells, which store `\beta` rounded to six figures. |
| C2 | Every `\beta` interval is the monotone image of the corresponding Clopper-Pearson interval on `P_f` | **Pass for every per-branch `\beta` interval, 8 of 8**, to 1e-9, endpoints exchanged. **Does not hold, and is not claimed to, for `\Delta\beta` and for `B`:** both are paired percentile bootstraps over the shared realization set. This distinction is the subject of correction 2.2; before it, the thesis asserted the mapped-interval construction for `\Delta\beta`. |
| C3 | The three additive ladder steps sum exactly to the total in the same row | **Pass, 9 of 9, residual 0.00e+00 unrounded.** Four rows differ by 0.01 in printed digits; see correction 2.7. |
| C4 | Every retained-fraction percentage equals `\Delta\beta_eq / \Delta\beta_published` printed beside it, with the denominator stated | **Pass, with the denominator now uniform.** KP 62.0 0.5721/0.9044 = 63.26 (point); KP 57.4 0.8423/1.27 = 66.32 (**bound**, hence "at most 66"); KP 58.8 0.8787/1.2239 = 71.79 (point); KP 60.0 1.5490/1.8657 = 83.02 (point). Against KP 57.4's point estimate 1.558 the figure is 54.06, quoted once in Chapter 6 and named for what it rests on. Complements 37, 34, 28, 17. |
| C5 | Every `B` equals the ratio of the two failure counts printed with it, at the stated sample size | **Pass, 12 of 12**, each within 0.6 per cent of the printed value: 1696/63 = 26.92; 1696/231 = 7.342; 1132/49 = 23.10; 24/2 = 12.0; 506/63 = 8.032; 72 206/26 273 = 2.748; 72 206/38 601 = 1.871; 91 650/31 427 = 2.916; 91 650/43 366 = 2.113; 179/4 = 44.75; 22 249/521 = 42.70; 1132/48 = 23.58 (the flip-excluded figure). |
| C6 | Each conditions register states a condition count matching its own row count | **Pass, 2 of 2.** `tab: piping conditions register`: 10 rows against "ten conditions" (the tenth, critical pipe length, added by `5579bbf` A8). `tab: system conditions register`: 8 rows against "Eight conditions". |

Two further arithmetic relations were checked and hold:

* The KP 57.4 one-sided bound is the exact monotone image of the ratio bound it
  restates. `B \geq 148` is `P_static` Clopper-Pearson lower over `P_transient`
  Clopper-Pearson upper, `1.067e-3 / 7.225e-6 = 147.7`; the index bound is
  `\beta(7.225e-6) - \beta(1.067e-3) = 4.3369 - 3.0709 = 1.2660`, printed 1.27.
  `ARITH`.
* The four `\Delta\beta` design anchors 0.90, `\geq` 1.27, 1.22 and 1.87 span
  "0.9 to 1.9", and the ratio ranking (KP 57.4, KP 62.0, KP 60.0, KP 58.8)
  re-orders to (KP 60.0, KP 57.4, KP 58.8, KP 62.0): KP 62.0 second to last,
  KP 60.0 third to first, KP 57.4 first to second. Both statements in the
  thesis are exactly this. `ARITH`.

---

## 4. Whole-document consistency gates

Scripts: `scratchpad/gates.py`, `gates2.py`, `cites.py` of this session, over
all 23 tracked `.tex` files, skipping the gitignored `scratch/`. All five
requested gates pass, plus one added.

| Gate | Result |
|---|---|
| Every `\label` referenced by a `\ref` exists; no `\label` duplicated | **Pass.** 373 labels, 279 distinct referenced labels, **0 dangling refs, 0 duplicates**. Line-wrapped `\ref{...}` arguments were normalized before matching; without that normalization a naive scan reports 32 false dangling references. 94 labels are defined and never referenced, which is normal for sectioning labels. |
| No em dash in any form in typeset content | **Pass.** 0 occurrences of U+2014 anywhere; 0 occurrences of `---` outside `%` comment lines. |
| No Japanese script in any `.tex` file | **Pass.** 0 hiragana, katakana or CJK-ideograph characters on any non-comment line of any `.tex` file. `references.bib` is exempt by the standing agreement and was not scanned. |
| No range written with a hyphen or en dash where "X to Y" is required | **Pass.** 0 en dashes anywhere. Three hyphen-joined numeric pairs survive the filter and none is a range: the borehole identifier `62.0-1` at `appendix-a.tex:320` and `:414`, and the expression `$(1 - 1/K)^{K}$` at `appendix-g.tex:597`. |
| The appendix count stated in Chapter 1 matches the number `report.tex` inputs | **Pass.** `report.tex` inputs eight appendix files, `appendix-a` to `appendix-h`; Chapter 1 says "eight appendices" at both sites (line 202), corrected from seven by `5579bbf` A3. |
| *(added)* Every `\cite` key resolves in `references.bib` | **Pass.** 106 distinct keys cited, 158 bib entries, **0 unresolved**. Includes the new `pol_2026_pers_comm` added by `6970ded` at six sites. |

### Cross-chapter headline-number consistency

Built by grepping, not from memory (`scratchpad/headline.py`, 21 anchor
patterns swept across `frontmatter/`, `mainmatter/` and `appendix/`). Every
headline quantity of the new block that appears in more than one chapter now
carries the same value at every site:

| Quantity | Value | Sites |
|---|---|---|
| KP 62.0 design anchor | `\Delta\beta` 0.90 [0.85, 0.97], `B` 26.9 [21.6, 35.3] | Summary, 6 (x4), 8 (x2), 9 (x3) |
| KP 57.4 bound and resolved anchor | `\geq` 1.27 (`B \geq` 148); 1.27 (`B` 42.7 [39.4, 46.6]) at 39.50 m | Summary, 6 (x4), 8 (x4), 9 (x4) |
| Drained-section anchors | 1.22 and 1.87 (`B` 2.75 and 2.92) | Summary, 6 (x4), 8 (x2), 9 (x2) |
| Section spread in index terms | 0.9 to 1.9 | Summary, 6 (x2), 8 (x2), 9 (x2) |
| Retained fraction | 63 to 83 per cent | Summary, 6, 8, 9 (x3) |
| Removed fraction | 17 to 37 per cent (**was 17 to 46 at four sites**) | Summary, 6, 8, 9 |
| Equal-convention `\Delta\beta` range | 0.57 to 1.55 | Summary, 6 (x2), 8, 9 (x2) |
| `B` at the top of each attainable range | 1.04 to 1.43 | 6 (x2), 9 (x2) |
| Stage behaviour of `\Delta\beta` | dip at most 0.14, rise up to 0.76 | 6 (x2), 8, 9 (x2) |
| Head-convention probability share | 75 to 97 per cent (three quarters and 97) | Summary, 6 (x2), 8, 9 |
| Canonical-event widening | 0.41 and 0.54 | 6 (x2), 9 |
| Pure duration effect | one to about six | Summary, 6, 8, 9 |
| Epistemic arms in index terms | 0.86 to 0.97 across the resolved arms | 5, 6 (x2), 8, 9 (x2, **one re-scoped, one re-anchored**) |

---

## 5. Per-chapter register

Rows are claim-groups. "Artifact" names the file that carries the number.

### 5.1 `frontmatter/summary.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| Index shift 0.90, CI 0.85 to 0.97, on 1e6; factor 26.9, CI 21.6 to 35.3 | `rq1-beta-reexpression.json` `design_anchors.kp62_0`; `adr0040-hwl-bias-resolution.json` `A_brute_kp62_0.anchor_A1` | EXACT |
| At least 1.27 (at least 148) at the design level, resolving to 1.27 (42.7) 29 cm higher | `design_anchors.kp57_4.delta_beta_lower_bound` = 1.2660; `A_brute_kp57_4` bias table at 39.50 | EXACT + ARITH (39.50 - 39.21 = 0.29) |
| Drained sections 1.22 and 1.87 (2.75 and 2.92), widening under the shorter event | `design_anchors.kp58_8`, `kp60_0`; `canonical_event` strata | EXACT |
| Probability factor of more than fifty, index span 0.9 to 1.9, largest ratio and largest index shift at different sections | 148/2.75 = 53.8; the four anchors | ARITH |
| Shared head convention retains 63 to 83 per cent; time dimension and gate worth 0.57 to 1.55 | `adr0051-equal-head-convention.json` `delta_beta_eq` at the four anchors | EXACT + ARITH |
| Two readings agree within about a quarter at the unremediated section, differ by about a factor of two at the berm-widened one | `equal-head-convention-study.md` §4.3: 7.34 against 8.03 (9.4 %); 23.1 against 12.0 (1.93) | ROUND |
| Head convention removes three quarters to 97 per cent of the probability difference but only 17 to 37 per cent in index terms | `tab: gap components` shares 0.75 / 0.97; complements of the retained fractions | **FIXED** (was 17 to 46) |
| Probability difference decays 26.9, 10.5, 4.4, 1.4; index difference does not decay | 26.9 from 1e6, the rest from the 1e5 ladder, as recorded in the 2026-08-21 register line 204 | EXACT |
| Yabe 0.061 / zero in 1e5 / 0.005, committee 0.62 and 0.65 | `docs/validation/` Yabe case | EXACT (2026-08-21) |
| Rejections 5.67 and 3.36 per cent, at most 0.07 elsewhere; static 58 and 73 against transient 5.7 and 3.4 | Phase 2 report; `mainmatter/6...:1244` (6.26, 57.63, 73.31, 0.00) | EXACT |
| Peak-only over-rejection 1.45 to 3.90 across the two approved events | union of Chapter 6's 2.75 to 3.90 and 1.45 to 1.57 | ARITH |
| Piping about 70 to 100 per cent; climate ratios 5.5 to 12.7; about four per cent per year | `annualisation-hazard-sampling-uncertainty.json`; `tab: system annual` | EXACT (2026-08-21) |

### 5.2 `mainmatter/4. Methodology.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| `\beta(h) = -\Phi^{-1}(P_f(h))`, `\Delta\beta = \beta_trans - \beta_static` (eq. `reliability index`) | `rq1-beta-reexpression.json` `metric` | EXACT |
| Additive telescoping identity (eq. `additive delta beta ladder`), C0 to C1 to C3b to C4b | same, `ladder.*.stages[].steps` | EXACT |
| "An interval on `P_f` maps to one on `\beta` by exchanging its endpoints" | verified numerically, check C2 | ARITH |
| Comparator ladder row `C4e` (full hydrograph, raw gross head, `-1/3`, `0.9 H_c`) | ADR-0051 `crack_resistance_factor = 0.0` | EXACT |

### 5.3 `mainmatter/5. Verification, Validation, and Global Sensitivity Analysis.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| KP 62.0 arms span `\Delta\beta` 0.86 to 0.97, comparable in width to the anchor's statistical interval | `rq1-beta-reexpression.json` `epistemic.sections.kp62_0.arms` (resolved arms 0.8635 to 0.9699); anchor CI [0.8516, 0.9693] | EXACT |
| IJkdijk widest deviation 2.01 m against observed 1.75 m (coarse-sand test 2) | `sellmeijer_2011.pdf` via `literature_claim_calibration_2026-08-29.md` | CITED |

### 5.4 `mainmatter/6. Results - Subsurface Piping Assessment.tex`

**`tab: piping conditions register`** (10 rows, rebuilt by `943d6f9` and `5579bbf`)

| Row | Claim | Artifact | Verdict |
|---|---|---|---|
| Aquifer conductivity | ratio displaced up to a factor of 46 at KP 62.0; resolved arms span `\Delta\beta` 0.86 to 0.97 | `0048-prior-mean-epistemic-scenarios.md` (45.6); `stage_d_epistemic.json` | EXACT |
| Grain-size statistic | resistant reading shifts every curve up by 1.3 to 5.2 m at `P_f = 1e-1` | Chapter 6 body, ADR-0024 deliverable tables | EXACT (2026-08-21) |
| Operative grain size at KP 62.0 | `H_c` scales as about `d_70^{0.4}` | `sellmeijer.py` `_factor_Fs` exponent product | EXACT |
| Canonical event | transient down 24 to 42 per cent mid-curve; drained factors 2.75 and 2.92 to 4.87 and 6.03; `\Delta\beta` widens 0.41 and 0.54 | `canonical-shape-sensitivity.md` §2.2; `rq1-beta-reexpression.json` `canonical_event` | EXACT |
| Adopted seepage lengths | ratio displaced by 1.02 to 3.22 at all 87 resolvable levels | ADR-0047 §4.5 | EXACT (2026-08-21) |
| Critical pipe length | transient displaced 1.00 to 2.08, ratio 1.11 to 1.67, static exactly invariant | ADR-0049 | EXACT |
| Exit-point datum | 26.9 to 13.9 and to 38.0, the latter unresolved on 2 realizations | `stage_d_epistemic.json` `z_toe_minus0.30m` 13.870, `z_toe_plus0.30m` 38.0, `k_transient` 2 | EXACT |
| Plane-strain scale exponent | most of the difference disappears at the 3D alternative | Stage 6.6 physics ladder | EXACT (2026-08-21) |
| Sellmeijer model factor | cancels; displaces the ratio by 1.010 at KP 62.0 and 1.07 to 1.22 across four sections | `stage_d_epistemic.json` `m_p` 27.20/26.92 = 1.0104; ADR-0045 | EXACT + ARITH |
| Remediation not credited | transient 0.263 to 0.108 at KP 58.8 and 0.314 to 0.111 at KP 60.0 on the measured berm; zero at four fifths relief | `adr0050-drained-configuration-bracket.json` `arms.berm_only.levels` at 41.00 and 42.75 | EXACT |

**Design-level fragility and the resolved anchors**

| Claim | Artifact | Verdict |
|---|---|---|
| `tab: design level fragility` `\Delta\beta` column: `\geq` 0.87, 1.22, 1.87, 0.96 | `rq1_beta_reexpression_2026-08-28.md` §4 (KP 57.4 1e5 bound 0.87); `design_anchors`; `canonical_event.kp62_0` at 46.50 (0.9573) | EXACT |
| One-sided upper bound `3.7e-5` on a zero of 1e5 | Clopper-Pearson `k = 0, n = 1e5`: 3.6888e-5 | ARITH |
| Eq. `kp62 bias`: `\Delta\beta` 0.90 [0.85, 0.97], `B` 26.9 [21.6, 35.3], width factor 1.63, 1696 and 63 of 1e6 | `adr0040-...json` `anchor_A1` (ci 21.558 to 35.256, width 1.6354) | EXACT |
| 3.83 against 2.93 at 46.39 m; 3.57 against 2.67 at 46.50 m; both `\Delta\beta` 0.90 | `ladder.kp62_0.by_n.1000000` `beta` | EXACT |
| 46.50 m reads `B` 21.6 [18.8, 25.2] on 176 rows; paired ratio 1.249 [1.039, 1.556] | `adr0040-...json` `anchor_A2` | EXACT (2026-08-21) |
| 1e5 reads `B` 44.7 and `\Delta\beta` 1.03 on four rows; overstated by two thirds and by 0.13 | 179/4 = 44.75; 44.75/26.92 = 1.662; 1.03 - 0.90 = 0.13 | ARITH |
| Eq. `kp57 bound`: `\Delta\beta \geq` 1.27 (`B \geq` 148) | `1.067e-3 / 7.225e-6 = 147.7`; `\beta(7.225e-6) - \beta(1.067e-3) = 1.2660` | EXACT + ARITH |
| Eq. `kp57 anchor`: 1.27 (`B` 42.7 [39.4, 46.6]), width 1.18, 521 rows | `A_brute_kp57_4` bias table at 39.50 (42.7044, 39.3699, 46.6285, 1.1844) | EXACT |
| Four Euler flips at 1e6 at KP 57.4, at 39.50, 40.25, 40.75; 42.7 deflated by about 0.2 per cent; expected count 0.4 at 1e5 | `adr0040-...json` `euler_flips`; 4/1e6 x 1e5 = 0.4 | EXACT + ARITH |
| KP 62.0 band 2.59 to 38.0 and 2.59 to 27.2, that is 9.0 or 6.4 times the width 1.63 | `stage_d_epistemic.json`; 14.67/1.639 = 8.95; 10.50/1.639 = 6.41 | EXACT + ARITH |
| Same arms span `\Delta\beta` 0.86 to 0.97; 0.76 to 0.97 including three below-floor point estimates, each only a one-sided bound, lowest `\geq` 0.47 | `epistemic.sections.kp62_0.arms`: bounds 0.4685, 0.4903, 0.6464 | **FIXED** (was "one of them ... `\geq` 0.49") |
| KP 57.4 band unbounded: field-test conductivity gives 15 static failures in 1e6 and none transient; finite arms 7.63 to 62.1, about 6.9 times the width | `stage_d_epistemic.json` `A3_lowest_resolved`: `k_aq_field_toe` 15/0; 7.629 and 62.146; 8.146/1.1844 = 6.88 | EXACT + ARITH |
| Blanket unit weight moves KP 57.4's 39.50 m anchor by 19 per cent, 42.7 to 34.5 | same, `gamma_bl_sub_lower` 34.4946; 1 - 34.49/42.70 = 0.192 | EXACT + ARITH |
| The four anchors re-order: KP 62.0 second to last, KP 60.0 third to first, KP 57.4 first to second; span 0.9 to 1.9 | the four anchors | ARITH |
| `\Delta\beta` interval provenance | `metric.delta_beta_interval_method`, `delta_beta_ci_source` | **FIXED** (was "mapped Clopper-Pearson") |
| **`tab: gap components beta`**, 9 rows x 7 numeric columns | `ladder.{kp62_0,kp57_4}.by_n.1000000.stages[]` `beta`, `steps`, `total_delta_beta`, `resolved` | **EXACT, 63 of 63 entries**, every one matching the artifact to two decimals |
| Caption: steps sum to the total regardless of order | residual 0.00e+00 unrounded at all nine rows | ARITH; **FIXED** caption to state independent rounding |
| `fig: gap waterfall` caption: bars sum exactly, initiation-gate bar zero-width at both stages | `steps.initiation_gate.delta_beta = 0.0` at every KP 62.0 stage | EXACT |
| `tab: gap components` (probability reading, 9 rows) counts and probabilities at 1e5 | Stage 6.6 ladder counts 179/4, 393/15, 5223/499, 44 347/10 127, 98 439/68 962, 118/0, 2230/62, 61 561/20 568, 99 969/96 437 | EXACT + ARITH |
| Head convention worth 0.135 m at KP 62.0 and 0.240 m at KP 57.4; 26 and 9 per cent of the driving head | `0.3 x 0.45` and `0.3 x 0.80`; 0.240/0.91 = 0.264; 0.135/1.49 = 0.091 | ARITH |
| Head and gate steps invariant to the canonical event; only the temporal step and the total move, by 0.41 and 0.54 | `canonical_event` strata; `rq1...md` §6 | EXACT |
| Initiation gate identically zero at KP 62.0 in probability and index; at most 0.18 at KP 57.4's design level | `steps.initiation_gate` | EXACT |
| **`tab: equal convention`**, 4 rows x 4 numeric columns | `adr0051-equal-head-convention.json` `B_production`, `B_eq`, `delta_beta_production`, `delta_beta_eq` | **EXACT, 16 of 16 entries** |
| Retained 63, 72, 83 and at most 66 per cent; 54 against the point estimate | check C4 | EXACT + ARITH |
| Static bit-identical; zero nesting exceptions at 1e5; ten flips at 1e6; 23.10 to 23.58 | ADR-0051 §3 and §5; 1132/48 = 23.583 | EXACT + ARITH |
| Two readings agree within 24 per cent at KP 62.0 (`mainmatter/6...:1010`), 7.34 against 8.03, quotable as 7 to 8; band of roughly 5 to 23 at KP 57.4, 23.1 against 12.0 on two realizations | `equal-head-convention-study.md` §4.3; 24/2 = 12.0 | **FIXED** (was "within 10 to 24 per cent"; the measured departures over the five KP 62.0 levels are 3.6 to 23.6 per cent) |
| Reduced-vs-reduced corroboration `\Delta\beta` 0.55 at KP 62.0 and 0.46 at KP 57.4's 39.50 m | `rq1...md` §4, `equal_convention_delta_beta` 0.5470 and 0.4572 | EXACT |
| `B` falls by a factor of 29 to 269 over the attainable range, to 1.04 to 1.43 | per-stratum computation from `production.*.levels`: 29.4, 43.1, 268.8, 34.7; 1.0366, 1.1631, 1.2205, 1.4274 | EXACT |
| `\Delta\beta` dips at most 0.14 and rises up to 0.76 | dips 0.1158, 0.1194, 0.1444, 0.0295; rises 0.5136, 0.3841, 0.6092, 0.7634 | EXACT |
| Static survival 0.03 to 1.56 per cent against transient 3.6 to 31.0 per cent at the top attainable level | `rq1...md` §3 survival table | EXACT |
| Temporal term grows 0.55 to 1.56 at KP 62.0 | `steps.temporal` at 46.39 and 50.50 | EXACT |
| Chapter synthesis: resolved epistemic arms span 10.5 in `B` and 0.11 in `\Delta\beta` | as 2.3 | **FIXED** (was "conductivity alone") |
| Drainage confound: static condemns 34 per cent against transient 5.4 under the measured berm, 57.6 against 15.6 as-if-undrained | `adr0050-drained-configuration-bracket.json` KP 58.8 at 40.75 m: `p_f_static_arm` 0.33622, `p_f_trans_arm` 0.05434, baselines 0.57634 and 0.15596 | EXACT |

### 5.5 `mainmatter/7. Results - System Integration and Climate Sensitivity.tex`

**`tab: system conditions register`** (8 rows, rebuilt by `943d6f9` and `5579bbf`)

| Row | Claim | Artifact | Verdict |
|---|---|---|---|
| Aquifer conductivity | lower arms contest the ordering at 3 of 4 historically and 4 of 4 under warming | `conductivity-bracket-annualisation.json` | EXACT (2026-08-21) |
| Grain-size statistic | annual system probability down by 1.5 to 37; overflow leads at 2 of 4 historically and 3 under warming | Chapter 7 body | EXACT (2026-08-21) |
| Operative grain size at KP 62.0 | the only dominance reversal in the reach | Chapter 7 | EXACT |
| Canonical event | changes the leader at 1 of 8 cells, KP 62.0 warming, production margin 1.0013 | 2026-08-21 study; composition-seam companion | EXACT |
| Sea-surface-temperature pattern set | 5,400 events in six prescribed patterns; treating as sampled widens warming intervals by 1.6 to 2.4 | `annualisation-hazard-sampling-uncertainty.json` | EXACT (2026-08-21) |
| Spatial autocorrelation length | identity at 250 m, factor 1.9 to 3.4 at the 40 m floor, no leader change | ADR-0037 | EXACT |
| Prior against posterior | posterior lowers the annual system probability by at most 12.4 per cent | Phase 3 report | EXACT (2026-08-21) |
| Remediation not credited | 7.4e-3 to 4.2e-3 at KP 58.8; 1.8e-3 to 6.4e-4 at KP 60.0; crediting drainage raises the climate ratio | ADR-0050 (7.42e-3 to 4.25e-3; 1.80e-3 to 6.40e-4; 5.51 to 14.22 and 7.87 to 26.01) | EXACT |

### 5.6 `mainmatter/8. Discussion.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| Opening RQ1 restatement: 26.9 (0.90 [0.85, 0.97]); `\geq` 148 (`\geq` 1.27); 42.7 (1.27) 0.29 m higher; 2.75 and 2.92 (1.22 and 1.87), rising to 4.87 and 6.03 | as 5.1 | EXACT |
| Span "0.9 to 1.9", KP 62.0 second to last and KP 60.0 third to first | as 5.4 | ARITH |
| Equal convention retains 63 to 83 per cent, taking KP 57.4 against its bound; 0.57 to 1.55 against 0.90 to 1.87 | ADR-0051 | EXACT |
| Additive steps at both anchors: 0.36 / 0.00 / 0.55 and 0.81 / 0.08 / 0.38 | `ladder` at 46.39 and 39.50 | EXACT |
| Head convention 75 to 97 per cent of the probability difference, 17 to 37 per cent of the index difference | as 2.1 | **FIXED** |
| Duration effect one to about six, consistent with the published expectation below five for river levees on coarse sand beneath a thin blanket | `tab: gap components` duration column; `pol_sie_2024` | EXACT + CITED |
| Decay 26.9, 10.5, 4.4, 1.4; index dip 0.14 and rise 0.76 | as 5.1, 5.4 | EXACT |
| KP 62.0 arms span 0.86 to 0.97, comparable to [0.85, 0.97]; epistemic band 6 to 9 times the statistical interval | `stage_d_epistemic.json` | EXACT |
| Nesting: transient failure implies static failure for every input and hydrograph; the two still differ by 26.9 (`\Delta\beta` 0.90) at design loading | ADR-0028; anchor | EXACT |
| Drainage confound does not rescue the static comparator: 34 against 5.4 under the measured berm | ADR-0050 | EXACT |
| Unresolved deliverable reported as a bound; remedy about 1.5e7 realizations | `adr0040-hwl-bias-resolution.md` | EXACT (2026-08-21) |
| Conductivity prior within a factor of 2.5 either side of the median | `\sigma_{\ln} = 0.472`, `exp(1.96\sigma) = 2.52` | ARITH; closes the 2026-08-21 FLAG 3.1 |

### 5.7 `mainmatter/9. Conclusions and Recommendations.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| Sub-question 1 answer: the four anchors, the re-ordering, the 11 cm stability (`B` 21.6, `\Delta\beta` unchanged at 0.90) | as 5.1, 5.4 | EXACT |
| Additive steps; head convention 75 to 97 per cent of the probability difference, 17 to 37 per cent of the index difference | as 2.1 | **FIXED** |
| Equal convention retains 63 to 83 per cent, taking KP 57.4 against its bound; 0.57 to 1.55 | ADR-0051 | EXACT |
| `B` decays to 1.04 to 1.43; `\Delta\beta` dips 0.14 and rises 0.76 | as 5.4 | EXACT |
| Resolved epistemic arms span 10.5 in `B` and 0.11 in `\Delta\beta` | as 2.3 | **FIXED** |
| **`tab: answers register` row 1**: the four anchors, head 0.36 and 0.81 against temporal 0.55 and 0.38, retained 63 to 83 per cent (0.57 to 1.55), `B` 1.04 to 1.43, `\Delta\beta` up 0.76; conditional on conductivity to a factor of 46 (resolved arms `\Delta\beta` 0.86 to 0.97), seepage lengths, critical pipe length, canonical event (4.87 and 6.03; 0.41 and 0.54) | `rq1-beta-reexpression.json`; `adr0051-...json`; `0048-...md` | EXACT; **FIXED** parenthetical |
| `tab: answers register` rows 2 to 4 | Phase 2 report, Phase 3 report, `annualisation-hazard-sampling-uncertainty.json` | EXACT (2026-08-21) |
| Short synthesis: 0.9 and 1.9; 2.75 to at least 148; 63 to 83 per cent; index moves 0.86 to 0.90 with the conductivity against 2.59 to 26.9 | as 2.5 | **FIXED** |
| Crack-reduced comparator resolving at neither design level, standing at 6.0 and 3.9 | `adr0040-stage6-6-*-analysis.json` `p_f.C1`, `p_f.C4b` | EXACT (2026-08-21) |

### 5.8 Appendices

| Claim | Artifact | Verdict |
|---|---|---|
| Appendix C: consultation decisions cited as `pol_2026_pers_comm` | `references.bib` entry added by `6970ded`; key resolves | EXACT |
| Appendix E: conductivity prior 2.5 either side of the median, percentile span 6.4 | `\sigma_{\ln} = 0.47238` | ARITH |
| Appendix G: gravel exclusion at an average of 15 per cent or more, attributed to the screening and index procedures | `jice_2019`, `fukuoka_2019` | CITED |
| Appendix G: the `C_e = 0.010` erratum confirmed in writing by the lead author | `pol_2026_pers_comm` | CITED |
| Appendix H: reach-wide surface composition (moved there by the reframing campaign) | Phase 3 report | EXACT (2026-08-21) |

---

## 6. Verification of the campaign's own edits

Each campaign commit was read from `git log` and its claims checked against the
artifact it names. All landed as described; the divergences are the seven
corrections of section 2.

| Commit | What it changed | Verified |
|---|---|---|
| `943d6f9` Lead RQ1 with the reliability index | Chapter 4 metric definition and ladder; Chapter 6 rewritten around `\Delta\beta`; five figures added | Values EXACT against `rq1-beta-reexpression.json`. Defects 2.2, 2.3, 2.6 and 2.7 originate here or in `bc59c62`. |
| `bc59c62` Carry the framing through 8, 9 and the Summary | Discussion, Conclusions, Summary, nomenclature | Values EXACT. Defects 2.3, 2.4 and 2.5 originate here. |
| `7387ca6` Calibrate four register claims | (1) ordering claim: "the ordering reverses, drained sections larger" replaced by the measured re-ordering at 9 sites; (2) "0.9 to at least 1.9" to "0.9 to 1.9" at 3 sites; (3) retained fraction 54 to 63 per cent at 7 sites; (4) Summary's two-readings claim | **All four verified correct.** (1) the `\Delta\beta` ranking is KP 60.0 1.87 > KP 57.4 `\geq` 1.27 > KP 58.8 1.22 > KP 62.0 0.90, so a drained section does not outrank the berm-only one and "reverses" was false. (2) in index terms the top of the range is KP 60.0's resolved 1.87, so the bound does not sit at the top. (3) 63.26 per cent is `0.5721/0.9044`, divisible straight out of `tab: equal convention`. (4) 7.34 against 8.03 at KP 62.0, 23.1 against 12.0 at KP 57.4. **This commit is the source of defect 2.1**: it moved the retained fraction to the bound convention at seven sites and left its complement on the point convention at four. |
| `2ce2e0a` Nine literature-carried claims | Pol reduction range 5 to more than 1e6; recovery-experiment pairing; the 0.5 screening value; IJkdijk 2.01 against 1.75; conductivity spread 2.5; the duration-factor corroboration; the gravel threshold | `CITED` throughout, not verifiable in this engine. The one engine-checkable item, the 2.5 spread, is `ARITH` and closes the 2026-08-21 FLAG. |
| `90d69e6` Nine interpretive claims | Chapter 1 duration framing; the drainage confound at two sites; the race-condition opening; four Summary calibrations | The two new numbers, 34 per cent against 5.4 under the measured berm and 57.6 against 15.6 as-if-undrained, are `EXACT` against `adr0050-drained-configuration-bracket.json` at KP 58.8's 40.75 m level, which is that section's 2016 peak grid level (its `p_f_static_baseline` is exactly the 57.63 per cent static rejection Chapter 6 prints). |
| `5579bbf` Eleven internal inconsistencies | A1 worst 1998 exit gradient; A2 the Obihiro gauge datum; A3 eight appendices; A4 one definition of attainable; A5 142 Hagibis breaches; A6 the tanh saturation; A7 the revised-prior ordering; A8 the tenth register row; A9 the 97-segment split; A10 the two-sided exit datum; A11 the Tokyo Peil statement | A1 `EXACT` against `tab:app_safety_summary` (KP 58.8 `i_v` 1.300 and drained, KP 62.0 0.970 and unreinforced). A3 `ARITH`, gate 5 passes. A4 `EXACT`, `attainable_max_m` 50.5. A8 `EXACT` against ADR-0049, and the register's row count now matches its stated ten (check C6). A10 `EXACT` against `stage_d_epistemic.json`. |
| `6970ded` Attribution of five consultation-sourced claims | `pol_2026_pers_comm` added and cited at six sites (Chapters 3, 4, 6, Appendices C and G) | Key resolves; the citation-key gate passes with zero unresolved keys. Two wordings weakened to match the record ("a realistic assumption"; the erratum named as author-confirmed). |

---

## 7. What this pass did NOT do

* **It did not re-run the engine.** No sweep, no ladder, no Phase 2 replay, no
  Phase 3 composition was executed. Every verdict rests on a persisted artifact
  or on arithmetic over printed numbers.
* **It did not re-audit the pre-2026-08-21 material.** Claims outside the block
  listed in the Scope above were touched only where a new statement had to be
  checked against them for consistency; their verdicts remain those of the
  2026-08-21 register.
* **It did not verify `CITED` values against their sources.** The nine
  literature-carried claims recalibrated by `2ce2e0a` are recorded here as
  landed, not as independently re-read; their evidence is
  `docs/literature_claim_calibration_2026-08-29.md`.
* **It did not compile the thesis.** Per the standing rule, `msc-thesis` is read
  from disk and never built locally. The label, reference, citation-key, dash,
  script and range gates were run as text checks over the sources, which is not
  the same as a clean XeLaTeX run: a compile could still surface a float or
  spacing problem that no text gate can see. **The edits inside a table cell and a
  caption in section 2 have not been seen in a built page.**
* **It did not re-measure any bracket on the equal-convention arm.** ADR-0051
  §7 records that the conductivity, seepage-length, canonical-event and
  critical-pipe-length conditionalities are inherited and not re-measured
  there; the thesis says so and this pass did not change that.
* **It did not touch page budget or layout.** Corrections 2.2, 2.3, 2.4 and 2.7
  each add one to three lines of text.

---

## 8. Residuals needing an owner ruling

**One.**

### 8.1 An unused figure asset

`figures/rq1_beta_curves.png` was added by commit `943d6f9` and is referenced by
no `\includegraphics` anywhere in the document. The four other figures that
commit added are all placed (`rq1_hwl_dbeta_resolved`, `rq1_kp57_4_dbeta_bound`,
`rq1_beta_waterfall`, `rq1_delta_beta_vs_stage`). Nothing numeric turns on it and
nothing is broken; the question is whether a per-branch `\beta`-against-stage
panel was meant to be placed somewhere in Section
`sec: The Design-Level Bias` and was dropped, or whether the file is simply
surplus and should be deleted. **Ruling needed:** place it or remove it.

No other residual. The two `FLAG` rows carried since 2026-08-21 are both closed
(section 1), and no claim in the new block failed to resolve to an artifact.

---

## 9. Provenance of this record

* Date of pass: 2026-08-30.
* Thesis state read: `msc-thesis` at `6970ded` plus the seven corrections of
  section 2, all made on this date.
* Engine state read: `bep-reliability-engine` at `b5f30f9`, branch
  `feature/critical-length-and-composition-seam`.
* Checks are reproducible from the artifacts named in the Sources table; the
  scripts were session scratch files and are not retained, since every number
  they read is named here with its JSON path.
