# Thesis number reconciliation, 2026-08-21

**What this is.** A claim-by-claim traceability record for every quantitative
statement in `msc-thesis`, checked against this repository's
evidence artifacts. It is a permanent record: it says, for each claim, which
artifact carries it, whether the printed figure reconciles, and where the
relationship is a rounding or an interval-informed restatement rather than a
copy. It supersedes nothing. `docs/number_audit_2026-07-30.md` audited the
thesis for *stale* values before Chapters 6 and 7 were drafted, and
`docs/thesis_number_inventory_2026-07-30.md` manifested numbers *awaiting* a
home. This pass audits the drafted document for *correctness*.

**Scope.** `frontmatter/summary.tex`, all nine `mainmatter/*.tex`, all seven
`appendix/*.tex`. Conditional and annual failure probabilities, overestimation
factors, confidence and sampling intervals, percentages, shares, realization and
segment counts, stages in m T.P., stage offsets, return periods, ratios, Sobol'
indices, and every entry of every table.

**Method.** Every claim was resolved to a named artifact (a
`docs/decisions/*.json` or `*.csv`, a report of record under `docs/`,
`data/processed/tokachi_bep_inputs.csv`, a `configs/*.yaml`, or a `results/`
file) and the number read out of that artifact. Where no artifact carries a
claim, that is recorded as such rather than assumed correct. Internal-arithmetic
checks (table self-consistency, ratios equal to their quotients, return periods
equal to reciprocals) were run without reference to any artifact, because a
failure there is unambiguous.

**Verdict vocabulary.**

| Code | Meaning |
|---|---|
| `EXACT` | Agrees with the named artifact to every digit printed. |
| `ARITH` | Internal-arithmetic check; consistent with the other printed numbers. |
| `ROUND` | A rounding, truncation or interval-informed restatement of an artifact number, not a copy. Recorded, not an error. |
| `FIXED` | Diverged; corrected in the thesis on this date. |
| `FLAG` | Not reconcilable from any artifact, or reconcilable only approximately. Text left alone; listed for the author. |
| `CITED` | A literature or official-record value carried by a `\parencite`, not produced by this engine. Not verifiable here. |

---

## 1. Headline statistics

| | Count |
|---|---|
| Claims or claim-groups checked | **431** |
| Reconciled exactly against a named artifact (`EXACT`) | **268** |
| Internal-arithmetic checks passed (`ARITH`) | **74** |
| Rounding or restatement relationships recorded (`ROUND`) | **26** |
| Corrected this pass (`FIXED`) | **3** |
| Flagged, not reconcilable, text left alone (`FLAG`) | **2** |
| Literature or official-record values, outside this engine (`CITED`) | **58** |
| Untraceable to any artifact **and** not a cited value | **2** (the two `FLAG` rows) |

A "claim-group" is one table row, one figure caption, or one sentence's set of
numbers where those numbers are read from the same artifact field in one
operation. Individual printed figures number roughly 1,900; the group is the
unit at which a divergence would be actionable.

---

## 2. The three corrections

### 2.1 Chapter 9 Section 9.1.3: the piping share range

* **File / line:** `mainmatter/9. Conclusions and Recommendations.tex:142`
* **Was:** "backward erosion piping accounts for between 81 and 100 per cent of
  the summed annual failure contribution in the historical climate"
* **Now:** "backward erosion piping accounts for about 70 to 100 per cent ..."
* **Artifact:** `docs/decisions/annualisation-hazard-sampling-uncertainty.json`,
  `preregistration_outcome.Q3.sections`. Point shares 1.000 (KP 57.4), 0.9741
  (KP 58.8), 1.000 (KP 60.0), 0.8115 (KP 62.0); KP 62.0's 95 % flood-ensemble
  sampling interval is `[0.6903, 0.9795]`.
* **Reasoning.** 81 is the KP 62.0 **point estimate** and sets the lower end of
  the range only if the sampling interval is discarded. The engine's own quoting
  rule records KP 62.0's 0.812 share as one of three quotations the ensemble
  does not support on its own. Chapter 7 already builds the range the other way
  and says so in the same sentence that prints the 81: "81 per cent at KP 62.0,
  on a 95 per cent flood-ensemble sampling interval of 69 to 98 per cent **that
  sets the lower end of the range above**". The Summary, Chapter 7 twice,
  Chapter 9's answers register and Chapter 9's overall conclusion all already
  carry "about 70 to 100". The interval-informed reading is therefore the
  document's own construction, is the conservative one, and is what five of six
  sites carry. Section 9.1.3 was the sole outlier and is now uniform with them.
* **Other sites checked and already correct:** `frontmatter/summary.tex:112`,
  `mainmatter/7...:382`, `mainmatter/7...:1177`, `mainmatter/9...:324`
  (answers register), `mainmatter/9...:394`.

### 2.2 Chapter 7 Table `tab: system annual`: two sampling-interval endpoints

* **File / lines:** `mainmatter/7. Results - System Integration and Climate
  Sensitivity.tex:367` and `:372`
* **Was:** KP 57.4 `+4`K system `[7.51, 11.6]e-3`; KP 62.0 historical system
  `[0.53, 1.57]e-3`
* **Now:** `[7.50, 11.6]e-3` and `[0.53, 1.56]e-3`
* **Artifact:** `docs/decisions/annualisation-hazard-sampling-uncertainty.json`.
  `sections["KP 57.4"]["matrix/posterior"]["+4K"].p_annual_system.ci_low` =
  `0.0075049285620437355` -> 7.50.
  `sections["KP 62.0"]["matrix/posterior"]["historical"].p_annual_system.ci_high`
  = `0.0015647030626748505` -> 1.56. Confirmed identical in
  `results/production_campaign/companions/annualisation-hazard-sampling-uncertainty.json`.
* **Reasoning.** The other fourteen interval endpoints in the table are
  nearest-rounded to the artifact, so no outward-rounding convention explains
  these two, and the two departures run in opposite directions (one narrows the
  interval, one widens it). Chapter 7's own derived text confirms the artifact
  values: the return periods at `:774-777` are "86 to 133" (= 1/1.16e-2 and
  1/7.5049e-3) and "817 to 2,891" (= 1/1.2240e-3 and 1/3.4591e-4), both computed
  from the unrounded numbers. Simple transcription slips.

### 2.3 Chapter 7 "Dominance and the Conductivity Bracket": the count of reversed cells

* **File / line:** `mainmatter/7...:540`
* **Was:** "It hands the lead to overflow at seven of them."
* **Now:** "It hands the lead to overflow at six of them."
* **Artifact:** `docs/decisions/conductivity-bracket-annualisation.json`,
  `sections[*][*].arms.k_aq_field_geomean.leading_mechanism`. Under that arm the
  lead is `overflow` at exactly six of the eight section-and-climate cells
  (KP 57.4 `+4`K, KP 58.8 both climates, KP 60.0 `+4`K, KP 62.0 both climates),
  `not defined` at KP 57.4 historical (both mechanisms exactly zero), and `bep`
  at KP 60.0 historical (`ordering_verdict: ROBUST`).
* **Reasoning.** The sentence was also internally impossible: the two sentences
  that follow it assign KP 57.4 historical to "no share exists there at all" and
  KP 60.0 historical to "the one cell that holds throughout", which with seven
  overflow cells accounts for nine of eight. The claim's own source, the
  companion note, carries the same conflation once
  (`conductivity-bracket-annualisation.md`, "it reverses seven and collapses the
  eighth") while its verdict table two paragraphs earlier records six REVERSED,
  one COLLAPSED, one ROBUST. A dated correction has been added to that note on
  the same date. The note's *headline* ("No, at seven of the eight cells") is
  correct and is a different count: seven cells are **not robust**, being the six
  reversed plus the one collapsed.

---

## 3. Flagged: not reconcilable, text left alone

### 3.1 "the central 95 per cent of the conductivity prior within a factor of about 2.9"

* **Sites:** `mainmatter/8. Discussion.tex:920`; `appendix/appendix-e.tex:214`
  (the same claim, stated twice).
* **Inputs:** `CoV(k_aq) = 0.50`, hence `sigma_ln = sqrt(ln 1.25) = 0.4724`
  (`configs/kp*_historical_*.yaml`, `priors.k_aq.cov`; tabulated in
  `tab:priors_phase1`). Both inputs are `EXACT` against the configs.
* **What the direct computations give.** The 97.5th percentile divided by the
  **median** is `exp(1.96 x 0.4724) = 2.52`. The full central-95 % span,
  P97.5/P2.5, is `6.36`. Measured against the **mean** instead, the interval is
  `[mean/2.82, mean x 2.26]`, so the tightest symmetric mean-relative factor
  containing 95 % is about `2.6`. None of these is 2.9.
* **Status.** No artifact in this repository carries the figure, and the intended
  construction cannot be determined from the text. It is qualified with "about",
  and its role in both passages is a comparison against the "factor of several to
  about ten" of `pwri_2014`, which survives any of 2.5, 2.6 or 2.9. The text is
  left unchanged. **Author ruling needed** on which construction was meant, after
  which the number should be made uniform at both sites.

### 3.2 Chapter 8's 234-hour Abashiri stage duration

* **Sites:** `mainmatter/8. Discussion.tex:76-78`; `appendix/appendix-g.tex:180-188`.
* **Status.** Carried by `\parencite{obihiro_levee_inspection_2008}` and not
  produced by this engine, so it is `CITED` and not checkable here. It is listed
  under FLAG rather than CITED only because Chapter 8 uses it as a quantitative
  counterweight to a computed result (the flashiness argument), which is the one
  place a cited duration does argumentative work against an engine number. No
  action; recorded so the dependency is visible.

---

## 4. Internal-arithmetic checks (no artifact required)

All passed.

| Check | Result |
|---|---|
| Chapter 7 `tab: system annual`: system value at or below the sum of the two mechanism contributions, at all 8 entries | Pass at all 8. Equal where only one mechanism is loaded (4 entries), strictly below elsewhere. |
| Chapter 7 `tab: system annual`: each share equals its own contribution divided by the summed contributions | Pass at all 16 shares, to the precision printed. Shares sum to 1.000 in every row. |
| Climate ratios in Chapters 7, 8 and 9 equal the quotient of the two values they are drawn from | Pass. System: 9.53e-3/7.53e-4 = 12.66 -> 12.7; 4.09e-2/7.42e-3 = 5.51 -> 5.5; 1.42e-2/1.80e-3 = 7.89 -> 7.9; 1.28e-2/1.01e-3 = 12.67 -> 12.7. Piping-only: 12.6, 5.5, 7.9, 9.8. Overflow: 13 at KP 58.8, 42 at KP 62.0. |
| Chapter 7 `tab: rq4 attribution`: each concentration factor follows from the two conditional probabilities printed beside it | Pass at all 8. Two cells (KP 57.4 hist 151, KP 60.0 hist 378) differ from the quotient of the *rounded* printed pair by 1 and 2 per cent, which is what a two-significant-figure denominator supports; both match the unrounded artifact exactly. |
| Chapter 7 `tab: rq4 attribution`: each "share of the annual total" equals stratum frequency x stratum conditional probability / annual total | Pass at all 8, using the annual totals of `tab: system annual`. |
| Chapter 6 design-level failure **counts** consistent with the probabilities printed beside them at the stated N | Pass. N = 1e6: KP 62.0 46.39 m, 1696/63 -> 26.92; 46.50 m, 3793/176 -> 21.55; KP 57.4 39.21 m, 1132/2; 39.50 m, 22249/521 -> 42.70. N = 1e5 comparator ladder: 4, 15, 499, 10 127, 68 962 (KP 62.0) and 0, 62, 20 568, 96 437 (KP 57.4) all equal 1e5 x the printed probability. |
| Chapter 6 confidence intervals consistent with those counts | Pass. Every interval matches the Clopper-Pearson ratio bounds in `adr0040-hwl-bias-resolution.json`, and the printed span factors (1.63, 1.18) equal `ci_hi/ci_lo`. |
| Chapter 7 return periods are reciprocals of the annual probabilities they restate | Pass. 135 on [103, 186] = 1/7.42e-3 and its interval; 24 on [22, 27]; 1,300 on [817, 2,891]; 105 on [86, 133]. All reciprocals of the unrounded artifact values. |
| Chapter 3 `tab: section inputs` matches `data/processed/tokachi_bep_inputs.csv` field for field | Pass, 5 sections x 6 CSV-sourced fields. See 5.3. |

---

## 5. Per-chapter register

Rows are claim-groups. "Artifact" names the file that carries the number.

### 5.1 `frontmatter/summary.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| 100 000 realizations; four cross-sections; 114 segments | `configs/*.yaml` `mc.n_samples`; `rq4_annual.csv` | EXACT |
| Design-level factor 26.9, CI 21.6 to 35.3, on 1e6 realizations | `adr0040-hwl-bias-resolution.json` `A_brute_kp62_0.anchor_A1` | EXACT |
| Crack-reduced comparator resolves nothing at the design level, on four failing transient realizations; factor 61 cm higher is 6.0 | `adr0040-stage6-6-kp62_0-analysis.json` `p_f.C4b`, `p_f.C1`; 47.00 - 46.39 = 0.61 | EXACT + ARITH |
| KP 57.4 lower bound 148; resolves at 42.7 twenty-nine cm higher; 3.9 against the crack-reduced comparator | `adr0040-hwl-bias-resolution.md` bound table (1.067e-3 / 7.225e-6); `...kp57_4-analysis.json` C1/C4b at 39.50 | EXACT |
| Drained-section factors 2.75 and 2.92; 4.87 and 6.03 under the shorter event | `canonical-shape-sensitivity.md` section 2.2 table | EXACT |
| "more than a factor of fifty" across four sections | 148 / 2.75 = 53.8 | ARITH |
| 21.6 on 18.8 to 25.2 eleven cm higher | `adr0040-...json` `anchor_A2` | EXACT |
| Yabe: 0.061, zero in 1e5, 0.005; 0.62 against 0.65 | `docs/validation/` Yabe case | EXACT |
| Head convention three quarters to 97 per cent | `...kp62_0-analysis.json`, `...kp57_4-analysis.json` component shares | EXACT |
| Equilibrium anchor inflates by 1 to 39 per cent | `components.auxiliary.heq_conservatism_engine` / `p_f.C4b`, both sections | EXACT |
| Pure duration a factor of one to about six | `p_f.C3b / p_f.C4b`, adequately counted levels | EXACT |
| Decay 26.9, 10.5, 4.4, 1.4 | 26.9 from N = 1e6; 10.5 / 4.4 / 1.4 from N = 1e5 `p_f` at 47.00 / 48.00 / 50.50 | EXACT |
| Temporal 53 to 99 per cent above mid-curve | component shares, both sections | EXACT |
| Marginal transient rejection zero in all eight | `phase2-survival-update-per-stratum.csv` | EXACT |
| 5.67 and 3.36 per cent; at most 0.07 elsewhere | same | EXACT |
| Means down about 4 per cent; others within 1 per cent | `docs/phase2_report.md` section 11 | EXACT |
| Static comparator 58 and 73 against 5.7 and 3.4 | `phase2-survival-update-per-stratum.csv` | ROUND (57.634 -> 58; 73.315 -> 73) |
| Peak-only over-rejects 1.45 to 3.90 | `phase2-peak-shortcut.csv`; `canonical-shape-sensitivity.json` `peak_shortcut` | EXACT |
| L holds half to three quarters of the transient variance, moves 1.4 per cent | `adr0033-gsa-study-*.json` ST(L); `phase2_report.md` | EXACT |
| Piping about 70 to 100 per cent | `annualisation-hazard-sampling-uncertainty.json` Q3 | EXACT (interval-informed; see 2.1) |
| Comparison at 4 of 114; scour exactly zero | `rq4_annual.csv` | EXACT |
| Warming factors 5.5 to 12.7; sampling interval roughly a factor of two | `...uncertainty.json` `climate_ratio` | EXACT |
| Long years 2.7 to 7.8 times more frequent; order a hundred times more dangerous | `stratified_attribution` | EXACT |
| One drained section about seven in a thousand rising to four in a hundred | 7.42e-3 -> 4.09e-2 | ROUND |
| Shortening by seven metres raises P_f by roughly an order of magnitude | `adr0047-dem-seepage-length.json`; x8.67 | ROUND |
| Epistemic band 6 to 9 times the statistical interval | `adr0040-hwl-bias-resolution.md` F3 table | EXACT |
| Conductivity spans absolute P_f by more than three orders of magnitude | `conductivity-bracket-annualisation.json` spans | EXACT |

### 5.2 `mainmatter/1. Introduction.tex` and `2. Theoretical and Empirical Foundations.tex`

Chapter 1 carries scope counts and reach limits only: KP 53.8 to 62.8 and
KP 3.2 to 16.6, the four cross-sections, 110 of 114, the 1951 to 2010 historical
window, the 1999 to 2003 works. All `EXACT` against `rq4_annual.csv`,
`data/processed/uemura_segments/segment_inputs.csv` and
`docs/tokachi_bep_inputs_provenance.md`. Chapter 2's numbers are `CITED`
throughout (Sellmeijer 2011 regression scatter, Pol's ODE constants, van Beek
2015 regime boundaries, the Japanese national inspection statistics), with the
exception of the `0.3 D_bl` crack term and the factor 89 / exponent 0.81 of the
progression ODE, both `EXACT` against
`docs/decisions/m7-pol-ode-reference-values.md`.

### 5.3 `mainmatter/3. Study Area, Geological Setting, and Data.tex`

`tab: section inputs` against `data/processed/tokachi_bep_inputs.csv`
(thesis / CSV):

| KP | L (m) | D_bl (m) | D_aq (m) | k_aq (m/s) | B_f (m) | Verdict |
|---|---|---|---|---|---|---|
| 57.40 | 33 / 33 | 0.80 / 0.80 | 7 / 7 | 3.0e-3 / 3.0e-3 | 200 / 200 | EXACT |
| 58.80 | 35 / 35 | 0.85 / 0.85 | 8 / 8 | 2.0e-3 / 2.0e-3 | 325 / 325 | EXACT |
| 60.00 | 34.8 / 34.8 | 0.85 / 0.85 | 9 / 9 | 1.0e-3 / 1.0e-3 | 600 / 600 | EXACT |
| 62.00 | 40 / 40 | 0.45 / 0.45 | 10 / 10 | 1.0e-3 / 1.0e-3 | 44 / 44 | EXACT |
| 63.40 | 26.9 / 26.9 | 1.0 / 1.0 | 11 / 11 | 6.0e-5 / 6.0e-5 | "river-tight" / 0 | EXACT (0 rendered as the descriptive label) |

`z_toe` 38.3 / 38.5 / 40.0 / 44.9 and design HWL 39.21 / 41.03 / 42.75 / 46.39
are `EXACT` against `configs/kp*_historical_*.yaml` `geometry.z_toe` and
`geometry.HWL` (ADR-0021 and ADR-0018; these are not CSV columns). The 1998
`i_v` column and `tab:oyo_1998` are `CITED` (`oyo_1999`, transcribed in
`docs/tokachi_bep_inputs_provenance.md`). `tab:strat_thickness` D_bl and D_aq
`EXACT` against the CSV. `tab:form5` conductivities `EXACT`; densities `CITED`.
`tab:priors_phase1`: the seven CoVs 0.50 / 0.30 / 0.10 / 0.167 / 0.50 / 0.056 /
0.782 `EXACT` against every generated config; the seven `sigma_ln` values 0.472 /
0.294 / 0.100 / 0.166 / 0.472 / 0.056 / 0.691 `ARITH` (each equals
`sqrt(ln(1 + CoV^2))` to three decimals). `gamma'_bl = 6.9 kN/m3` `EXACT`;
`gamma'_p = 16.87` `EXACT` against `sellmeijer.GAMMA_P_SUB_DEFAULT`;
`theta = 37 deg`, `eta = 0.25`, `D_r = 0.725` `EXACT` against the configs.
"Roughly fourteen-fold" foreshore variation (600/44 = 13.6) `ROUND`.

### 5.4 `mainmatter/4. Methodology.tex`

Method constants only: `N = 1e5`, `Delta t = 225 s` (native/16), Latin
hypercube, forward Euler, 0.25 m conditioning steps from the surveyed toe to
HWL + 4 m, two-population coupling, `lambda_ac = 250 m`, `L_seg = 200 m`,
`CoV(L) = 0.20` (0.15 at KP 60.0), the seven-dimensional `theta` plus separately
sampled `L`, and `m_p ~ LN(1.0, 0.12)` default off. All `EXACT` against
`configs/kp62_0_historical_matrix.yaml` and its siblings. Equation constants are
`CITED`.

### 5.5 `mainmatter/5. Verification, Validation, and Global Sensitivity Analysis.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| IJkdijk: 2.07 m against 2.30 m, 13 per cent band, 10 per cent deviation | `docs/validation/`; `sellmeijer_2011` | EXACT (deviation ARITH) |
| B25-245 demoted; `C_e = 0.010` author-confirmed, 0.014 caption erratum | `m7-pol-ode-reference-values.md` | EXACT |
| Timestep: breach threshold 0.80 m too low at native; stationary from 450 s; no flip between 225 s and 14 s; the literal 1 per cent criterion needs <= 112.5 s; 16.8 per cent residual at 225 s at KP 57.4 | `adr0039-timestep-stress.json` | EXACT |
| N-ladder: 50 replicates, 1e3 to 3e5, 5 per cent met at N = 1e5 down to ~5e-3, roughly 16 per cent at 3e-4, 1.3e6 needed to hold 5 per cent there | `adr0031-convergence-study.json` / `.md` | EXACT (16.5 -> 16, ROUND) |
| Variance-reduction ratio about 1.4 at P_f near 0.26, parity in the deep tail | `adr0031-convergence-study.md` (1.40 +/- 0.09, 1.00 +/- 0.06; KP 60.0 1.48 +/- 0.06, 1.01 +/- 0.04) | EXACT |
| Field validation: uplift minima 0.62 to 0.88 and at least 1.06; onset factor about 2.3; M4 factor 1.13 to 2.67 | `docs/validation/` Gounokawa, Shikaga | EXACT |
| r_e-halved QA member: maximum change 0.181 at 41.25 m, parity above 43.5 m | `results/qa_re_halved_kp58_8.json` | EXACT |
| Yabe: 0.061, 0 in 1e5, 0.005; 0.62 against 0.65; 6.3 h and 6.1 h; 0.04 / 0.41 / 0.90 and 0.12 / 0.67 / 0.98 | `docs/validation/` Yabe | EXACT |
| Sobol' table: 8 inputs x 2 sections x (S, ST) with half-widths, plus 2 sums | `adr0033-gsa-study-kp58_8_matrix.json`, `...kp60_0_matrix.json`, last rung | EXACT, all 34 |
| P_f = 0.263 and 0.314 at the two design levels | same, `mean_y` | EXACT |
| Static margin additive, sum 0.98; L 0.44, k_aq 0.35, d70 0.19; ST - S <= 0.02 | `z_static` QoI at 41.0 | EXACT |
| Design-level static indicator sum 0.61 | `static_indicator` `sum_S` = 0.6150 | ROUND |
| Transient ranking 0.63 / 0.57 / 0.34 / 0.28 / 0.06 / 0.06; "sum to 0.59" | `trans_indicator` at 41.0, `sum_S` = 0.5849 | EXACT; the sum ROUND (0.585 -> 0.59) |
| Shoulder: sum 0.24, 76 per cent interactive, gaps 0.66 / 0.63 / 0.41 / 0.37 | same, level 40.25 | EXACT |
| C_e first-order 0.011 at the shoulder to 0.114 at the upper level | levels 40.25 and 42.5 | EXACT |
| KP 60.0 ranking 0.61 / 0.49 / 0.48 / 0.25 | `...kp60_0_matrix.json` at 42.75 | EXACT |
| Bulk companion at 45.0 m: L 0.69, k_aq 0.62, d70 0.40, C_e 0.16; whole curve about 4 m up | `...companions.json` `runs.bulk_d70` | EXACT |
| Prior-mean scenario table, 10 ratio entries | `adr0048-prior-mean-companion.json` | EXACT |
| Ratio displacements 82, 66, 163, 46 | `epistemic-bracket-ranking.csv` `max_resolved_departure_factor` (82.2186, 65.6471, 162.871, 45.5619) | EXACT |
| m_p displaces the ratio 1.07 to 1.22; the L bracket 1.02 to 3.22 at all 87 levels | `epistemic-knobs-mp-ztoe.csv`; `adr0047-dem-seepage-length-ratio.json` | EXACT |
| Epistemic band 6 to 9 times the statistical one | `adr0040-hwl-bias-resolution.md` F3 | EXACT |
| Blanket unit weight leaves the static branch at exactly 1.000 at all 98 levels | `epistemic-knobs-mp-ztoe.csv` | EXACT |
| CoV(k_aq) places the central 95 per cent within a factor of about 2.9 | none | **FLAG** (see 3.1) |

### 5.6 `mainmatter/6. Results - Subsurface Piping Assessment.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| Standing conditions: 46; 1.3 to 5.2 m; 24 to 42 per cent; 1.02 to 3.22; 26.9 -> 13.9; 1.010; 1.07 to 1.22 | `epistemic-bracket-ranking.csv`; bulk vs matrix `results/*.h5`; `canonical-shape-sensitivity.md`; `adr0047-...-ratio.json`; `adr0040-...md` Stage D | EXACT |
| Raw transient maximum 0.964 (KP 57.4) to 0.990 (KP 62.0) | `results/tokachi_kp*_historical_matrix.json` `fragility_deliverable.transient.max_p_f_raw` | EXACT |
| `tab: design level fragility`: 4 sections x (HWL, grid level, static, transient, transient median) | `results/*.h5` at the design grid level; medians by linear interpolation of the raw points to P_f = 0.5 | EXACT, all 20 |
| Design level 0.49 and 0.43 m below the median; 1.87 and 3.22 m below at the other two | same | ARITH |
| Static medians reach 0.5 within 1.98 to 2.14 m; transient within 2.78 to 3.18 m; KP 62.0 at 3.22 and 4.71 m | same, minus `z_toe` | ARITH |
| Median separation 0.74 / 0.88 / 1.20 / 1.49 m | same | ARITH |
| Bulk reading shifts curves 1.3 / 1.9 / 4.0 / 5.2 m at P_f = 1e-1 | `results/tokachi_kp*_historical_bulk.h5` against matrix, static branch, linear interpolation | EXACT (static-branch reading; the transient shifts differ by at most 0.09 m) |
| Bulk design levels: at most one failure in 1e5; KP 60.0 transient 1.1e-2 against static 9.3e-2 | `..._bulk.h5` | EXACT |
| Onset rises 39.75 -> 41.25 m and 46.25 -> 48.50 m | same | EXACT |
| Largest bulk transient 0.38 and 0.15 against 0.96 and 0.99 | same | EXACT |
| KP 62.0 resolved: 1696 / 63 -> 26.9, CI [21.6, 35.3], span 1.63 | `adr0040-hwl-bias-resolution.json` `anchor_A1` | EXACT |
| 46.50 m: 21.6 on [18.8, 25.2] on 176; paired ratio 1.249 [1.039, 1.556] | `anchor_A2`; `docs/project_log.md` | EXACT |
| N = 1e5 reads 44.7 on four rows | `p_f.C0/C4b` at 46.39 = 0.00179/0.00004 = 44.75 | ROUND (44.75 printed as 44.7) |
| KP 57.4: 1132 / 2 at 39.21 m; bound 148; 42.7 [39.4, 46.6] on 521 at 39.50 m, span 1.18 | `adr0040-hwl-bias-resolution.json` and its bound table | EXACT |
| Four Euler barrier-jump rows at 39.50 / 40.25 / 40.75; one inside the 521; bias 0.2 per cent; expected count 0.4 at 1e5 | `A_brute_kp57_4.euler_flips` | EXACT + ARITH |
| KP 62.0 epistemic band 2.59 to 38.0 and 2.59 to 27.2; 9.0 or 6.4 times 1.63; threshold ten | `adr0040-...md` F3 table | EXACT |
| Regional upper collapses B to 2.59; z_toe -0.30 m to 13.9; m_p 1.010; gamma_bl_sub inert on the same 63 rows | same Stage D table | EXACT |
| KP 57.4 band 7.63 to 62.1, about 6.9 times; control fails on 2 and 10 rows and passes at 63 or more; gamma_bl_sub moves 42.7 to 34.5 | `adr0040-...md` KP 57.4 Stage D | EXACT |
| Ladder reproduces production at all 38 and 23 shared levels | grid lengths in `configs/*.yaml` (38 and 23) plus the HWL row | ARITH |
| `tab: comparator ladder`: 9 rows x 9 columns | `adr0040-stage6-6-kp62_0-analysis.json` and `...kp57_4-analysis.json`, `p_f` and derived shares | EXACT, all 81 |
| Crack decrement 0.135 m and 0.240 m; 26 and 9 per cent of the driving head | `0.3 x D_bl`; HWL - `z_toe` | ARITH |
| Head convention 3.7 against 12; 1.7 against 6.0 | `C0/C1` and `C3b/C4b` | EXACT |
| 8.7e-3 at 46.75 m and 7.4e-2 at 39.75 m under both events | `C0 - C1`; `canonical-shape-sensitivity.json` gate 3 | EXACT |
| Head shares 0.55 -> 0.52 and 0.81 -> 0.77 under the alternate event | `canonical-shape-sensitivity.json` `ladder` | EXACT |
| Temporal 53 / 81 / 58 / 99 per cent | component shares | EXACT |
| Initiation identically zero at KP 62.0; never above 3 per cent at KP 57.4; largest 1.5e-3 out of a gap of 0.21 | `C1 == C3b` at KP 62.0; `C1 - C3b` at KP 57.4 | EXACT |
| Pure duration 12 -> 1.4 and 3.2 -> 1.0; highest adequately counted 6.0 | `C3b/C4b` | EXACT |
| Crack-reduced factor 6.0 -> 1.4 and 3.9 -> 1.0; 3.9 against 3.2 at 39.50 m | `C1/C4b` | EXACT |
| H_eq inflation 29 / 19 / 6 and 39 / 17 / 1 per cent; range 1 to 39; laboratory factor about 1.95 | `auxiliary.heq_conservatism_engine / p_f.C4b`; ADR-0009 | EXACT |
| Dimensional alone -0.43 / -0.47 / -0.50; physics totals -0.05 / +0.06 / -0.04; production totals +0.05 / +0.34 / +0.41 | `auxiliary.dimensional_at_static`, `total_gap_physics`, `total_gap_engine` | EXACT |
| Companion at 1e4: +0.37 and +0.61 at the two grid tops | `docs/stage6_6_report.md` | EXACT |
| Shapley: +0.065 / +0.029 / +0.037 and +0.173 / +0.030 / +0.143; +0.047 against -0.451 and +0.101 against -0.430 | `static_pair_shapley` at 48.00 m and 40.50 m | EXACT |
| Decay 26.9, 21.6, 10.5, 6.3, 4.4, 2.4, 1.4 (KP 62.0) and 42.7, 14.4, 6.9, 3.0, 1.04 (KP 57.4) | 1e6 for the two anchors and the KP 57.4 sequence; 1e5 `p_f` from 47.00 m up at KP 62.0 | EXACT |
| 2016 peaks 39.66 / 40.75 / 42.30 / 45.73 m; exceeds by 0.45 m, falls 0.28 / 0.45 / 0.66 m short | `phase2-peak-shortcut.csv` `event_peak_m_msl` and the HWL differences | EXACT + ARITH |
| Peak-referenced 15.60 / 13.11 / 0.48 / about zero per cent | same, `peak_only_transient_pct` | EXACT |
| Rejections 0.07 / 5.67 / 3.36 / 0.00 transient; 6.26 / 57.63 / 73.31 / 0.00 static | `phase2-survival-update-per-stratum.csv` | EXACT (73.315 -> 73.31, ROUND) |
| Bulk: no stratum rejects more than 0.02 per cent | same (maximum 0.023) | ROUND (true to the precision printed) |
| ADR-0047 L adoption raises KP 62.0 transient x8.7 without changing the rejection | `epistemic-bracket-synthesis.md` (x8.67) | EXACT |
| Anchor-rating replay 0.00 / 10.81 / 0.34 / 0.05; a factor of two up and ten down | `phase2-survival-update-per-stratum.csv` `anchor_rating` | EXACT + ARITH |
| z_toe +/- 0.3 m: KP 58.8 transient rejection spans 1.68 to 12.99 per cent | `docs/phase2_report.md` section 12 table | EXACT |
| Contingency cells 51.96 / 69.95 / 6.19 per cent | static minus transient rejection | ARITH |
| No-initiation variant 66.4 / 99.6 / 99.3 / 39.6 per cent; a few hundred survivors | `phase2-survival-update-per-stratum.csv` `no_initiation` (432 and 696) | EXACT |
| Joint upper tail rejected 5.3 and 7.7 times the overall rate | `docs/phase2_report.md` section 11 table | EXACT |
| C_e means -4.1 / -3.7, 0.0550 -> 0.0528; k_aq -4.2 / -3.0; every other parameter under 1 per cent; Spearman about -0.05 | `docs/phase2_report.md` sections 11.2 to 11.3 | EXACT |
| The laboratory prior moves it 0.3 per cent | `docs/phase2_report.md` section 11.3 | EXACT |
| Peak-only 2.75 and 3.90; 7.46 on 65 and 6.12 on 23; 1.45 and 1.57 under the alternate event | `phase2-peak-shortcut.csv`; `canonical-shape-sensitivity.json` `peak_shortcut` | EXACT |
| Alternate event shape: 16 h against 23, 5 against 10, 21 against 55, one peak against two | `canonical-shape-sensitivity.json` `shape.members` | EXACT |
| Alternate lowers transient P_f by 24 to 42 per cent at all eight strata | `canonical-shape-sensitivity.md` midpoint table (ratios 0.579 to 0.755) | EXACT |
| Design level 0.263 -> 0.148 and 0.314 -> 0.152; factors 2.75 / 2.92 -> 4.87 / 6.03 | `canonical-shape-sensitivity.md` section 2.2 | EXACT |
| L statistics move +1.4 / +0.5 per cent in the mean and -3.6 / -1.7 in CoV; ST share 0.49 to 0.78 | `docs/phase2_report.md`; `adr0033-gsa-study-*.json` | EXACT |
| 2011 marginal bounded at 0.316 per cent | `adr0044-event-closure-bound.json` | EXACT |

### 5.7 `mainmatter/7. Results - System Integration and Climate Sensitivity.tex`

| Claim | Artifact | Verdict |
|---|---|---|
| Standing conditions: 1.5 to 37 and 2 / 3 sections; 1.0013; six SST patterns and 1.6 to 2.4; 1.9 to 3.4; 12.4 per cent | bulk against matrix `rq4_annual.csv`; Q2 `production_margin`; `resampling_unit_sensitivity`; the lambda arms; the prior and posterior arms | EXACT |
| 114 segments, 200 m grid, `n_eff = 1` at 250 m | `rq4_annual.csv`; ADR-0037 | EXACT |
| Peaks above the grid at 2 of 114, both surface-only, in at most 0.04 per cent of years | `rq4_annual.csv` `system_frac_peaks_above_grid` (3.70e-4 and 1.85e-4) | EXACT |
| `tab: mechanism coverage`: 46 / 68 / 114, 4 / 0 / 4, 42 / 68 / 110; dominance 4 / 4, 31 / 109, 0 / 0, 79 / 1; as-received 4 / 4, 6 / 44, 97 / 66, 7 / 0 | `rq4_annual.csv`, primary and `scour_script_k` arms | EXACT, all 20 |
| Piping reaches 1e-2 between 1.4 and 3.2 m below overflow; crosses one half between 1.6 and 3.0 m below | `rq3_segment_curves_matrix_posterior.json`, first grid level at or above the threshold (offsets 2.25 / 1.40 / 3.15 and 1.55 / 3.00 / 2.10) | EXACT |
| Crest 1.5 m above the design level at all four | `docs/tokachi_chisuishi_full_review_2026-07-27.md` (1966 freeboard rule) | EXACT |
| Maximum warming stage 51.47 m at KP 62.0 | `results/system_integration/hazard_cache/hazard_tokachi_kp62.0_plus4K.csv` (51.4676) | EXACT |
| KP 62.0 piping reaches 1e-2 about 1.1 m below overflow; crosses one half at 49.75 m; overflow at 49.0 m | `rq3_segment_curves_matrix_posterior.json` | EXACT |
| Overflow about one per cent of the composed value at KP 58.8 at its design level | same, 0.00270 / 0.22289 | EXACT |
| `tab: system annual`: 8 rows x (system, interval, piping, share, overflow, share) | `rq4_annual.csv` and `annualisation-hazard-sampling-uncertainty.json` | EXACT at 46 of 48; **2 FIXED** (see 2.2) |
| Caption: 11.8 per cent above the attainable maximum; shares 0.69 to 0.98 and 0.48 to 0.53 | `conductivity-...json` `frac_of_annual_piping_above_attainable_max` = 0.11787; Q3 and Q2 intervals | EXACT |
| 97 per cent at KP 58.8, 81 at KP 62.0 on 69 to 98 | `rq4_annual.csv` shares; Q3 | EXACT |
| Warming 91, 94, 100 per cent; 0.50 against 0.50 | `rq4_annual.csv` | EXACT |
| Margin 1.0013; difference 1e-5 inside +/- 9e-4; share interval 0.48 to 0.53 | Q2 block | EXACT |
| The alternate event lowers the KP 62.0 warming piping share to 0.380 and is the only ordering change of the eight | `canonical-shape-sensitivity.json` `phase3.sections` (0.37987, `ordering_changes: true`) | EXACT |
| Piping ratios 12.6 / 5.5 / 7.9 / 9.8; overflow 13 and 42 | `climate_ratio_piping_only`; the overflow quotients | EXACT + ARITH |
| Governing section KP 58.8 at 7.4e-3 and 4.1e-2, 97 and 94 per cent piping | `rq4_annual.csv` | EXACT |
| Uemura sections: Tokachi 4 at 7.5e-3 and 4.1e-2 on [5.4, 9.7]e-3 and [3.7, 4.6]e-2, ratio 5.5 on 4.1 to 7.7; Tokachi 3 and 1 at 1.8e-3 and 1.1e-3; two with no ratio; three undefined in 5 to 13 per cent of resamples; warming 1.1e-5 to 3.8e-3 | `annualisation-...json` `section_aggregates` | EXACT |
| Margin over overflow 43-fold prior, 37.6-fold posterior | `rq4_annual.csv` prior and posterior arms at KP 58.8 | ARITH |
| Bulk reading: 2 per cent at KP 58.8, essentially nothing at KP 62.0, 99 per cent at KP 60.0 against 38, 10 and 0.2; the governing section moves to KP 62.0 | `rq4_annual.csv` bulk arm | EXACT |
| Bulk leads at 1 of 4 under warming and 2 historically, only where overflow is absent | same | EXACT |
| Conductivity: the lead survives at 1 of 4 historically and at none under warming | `conductivity-bracket-annualisation.json` verdicts | EXACT |
| The lowest arm changes all eight; hands overflow the lead at six; KP 57.4 historical collapses to zero; KP 60.0 historical holds at 5.2e-8 | same, `leading_mechanism` and `arms.k_aq_field_geomean.p_annual_system` | **FIXED** (seven -> six; see 2.3); 5.2e-8 EXACT |
| field_toe reverses three: KP 62.0 in both climates and KP 57.4 under warming | same | EXACT |
| KP 62.0 shares 0.000 and 0.493 historically, 0.001 and 0.254 under warming; the upper bound gives 0.986 and 0.892 | same | EXACT |
| Resistant reading: the upper bound returns the lead at 4 of the 5 conceded cells; KP 62.0 historical 0.542; KP 62.0 warming 544 behind against a 273-fold arm | `conductivity-bracket-annualisation-bulk.json` | EXACT |
| The bracket narrows from 185 to 4.4 at KP 58.8 historically; spans 69 and 185 | matrix and bulk `conductivity_span_p_annual_system` | EXACT |
| The annual number is set by stages at or above the design level; at KP 62.0 by 1.1 to 2.3 m above it | `driving_stage_band` p10 and p90 minus HWL | ARITH |
| Scour exactly zero at all 114 in both climates; the 105.6x conversion; about 51 Pa | `rq4_annual.csv`; ADR-0042 decision 9 | EXACT |
| As-received raises the system by 8, at most 2, and 22 per cent; the ordering is unchanged; dominant at 97 and 66 | `rq4_annual.csv` `scour_script_k` | EXACT + ARITH |
| KP 60.0 0.28 against KP 58.8's 0.22 at the design level; 1.8e-3 against 7.4e-3, four times smaller | `rq3_segment_curves_matrix_posterior.json` at the design grid levels 42.75 and 41.00 | EXACT + ARITH |
| The toe is reached in 24.7 and 20.5 per cent of years; above it for a day in 5.1 against 3.5 | `stratified_attribution` | EXACT |
| Ratios 12.7 / 5.5 / 7.9 / 12.7 on [7.3, 28.1], [4.1, 7.7], [5.3, 12.9], [7.7, 24.8] | `annualisation-...json` `climate_ratio` | EXACT |
| Absolute values 7.5e-4 -> 9.5e-3, 7.4e-3 -> 4.1e-2, 1.8e-3 -> 1.4e-2, 1.0e-3 -> 1.3e-2 | `rq4_annual.csv` | EXACT |
| Downward arms reach 234 and 671; the upward arm gives 3.4 to 7.3 | `conductivity-...json` P6 cells | EXACT |
| Return periods 135 [103, 186] -> 24 [22, 27]; 1,300 [817, 2,891] -> 105 [86, 133] | reciprocals of the artifact values | ARITH |
| The 1 in 150 design scale | `tokachi_chisuishi_2023` | CITED |
| Half-widths 29 to 58 and 11 to 21 per cent | `relative_half_width`, matrix/posterior | ROUND (maximum 21.65 truncated to 21; the engine's own summary carries the same range) |
| 3,000 and 5,400 years; six patterns; SST widening 1.6 to 2.4 | `ensemble_structure`; `resampling_unit_sensitivity` | EXACT |
| KP 62.0: 7 of 5,400 years (0.13 per cent) above 50.5 m, 4 of the 7 above the first hypothetical level, 11.8 per cent of the contribution; exactly zero historically and at KP 57.4 in both climates | the hazard CSV; `driving_stage_band` | EXACT |
| Five of six pairs separate; KP 57.4 and KP 62.0 do not | `preregistration_outcome.Q1` (5 of 6) | EXACT |
| The lambda floor raises by 1.9 to 3.4, the larger factors historically | `rq4_annual.csv` lambda arms (1.93 to 3.37) | EXACT |
| Bulk lowers by 15 and 8.8 under warming and 37 / 26 / 5.1 historically; KP 57.4 by 363, 7.5e-4 -> 2.1e-6 | matrix over bulk, `rq4_annual.csv` | EXACT |
| The posterior lowers by 12.4 and 11.0 historically and 8.3 and 7.6 under warming; KP 57.4 within 0.3 per cent; KP 62.0 exactly | prior over posterior, `rq4_annual.csv` | EXACT |
| Reach context: median 0 -> 3.7e-4, mean 1.1e-4 -> 1.9e-3, a factor of about 18; above 1e-3 from 3 to 45; above 1e-2 from 0 to 4; 79 unloaded; Satsunai 7.0e-5 rising to 67 of 68 loaded and reaching 6.8e-3 | `rq4_annual.csv` | EXACT |
| The 100-year return level rises by about 1.66 | Appendix F d4PDF chain | EXACT |
| `tab: rq4 attribution`: 4 sections x 2 climates x 7 rows | `annualisation-...json` `stratified_attribution` | EXACT, all 56 |
| Occupancy floor of 20 member blocks; half-widths 24 to 161 per cent | `floor.F1_min_carrying_member_blocks`; the concentration-factor relative half-widths (0.2402 to 1.6096) | EXACT |
| Toe-reaching years rise 1.7 to 3.3; medians 8 -> 10, 15 -> 19, 13 -> 17, 11 -> 14; long years 2.7 to 7.8; compound 2.1 to 4.0 | table quotients | ARITH |
| Concentration about 150 and about 380 on [98, 252] and [141, 1,358]; 221 and 151 on 19 and 3 years in 14 and 3 members; warming 35 to 72; the long stratum 56 to 91 per cent at three of four | `stratified_attribution` | EXACT |
| Compound 3.7 and 6.5 on [0.3, 9.3] and [0.1, 18.4]; 91 at KP 57.4; warming 1.6 to 23 | same | EXACT except the warming compound upper end (22.45), **ROUND** |
| A floor of 30 clears no historical compound cell; the duration range is unchanged at 10, 20 and 30 | carrying-block counts (23 and 20 historical compound; 46 and 43 duration) | ARITH |
| Frequency 2.7 / 2.8 / 5.4 / 7.8 against severity 2.1 / 2.7 / 2.2 / 3.7 | table quotients | ARITH |

### 5.8 `mainmatter/8. Discussion.tex`

Chapter 8 restates Chapters 5 to 7 and adds no new engine number. Every
restatement was matched to its source claim above and is `EXACT` or `ARITH`,
with these specifics: median rising limb 18 h and plateau 9 h `EXACT`
(`adr0032-aquifer-response-diagnostic.md`); response time "of order ten
minutes" and the ratio of about one hundredth against a threshold of one tenth
`EXACT` (680 and 765 s; Pi 0.010 and 0.012); 0.45 to 0.85 m against about 3 m,
"a factor of three to seven short", `ARITH`; "up to 2.7" in the field cases
`ROUND` (2.67); the open-entry bound worth at most 2.4e-4 at KP 62.0 `EXACT`
(`adr0025-foreshore-sensitivity.json`); the foreshore-exhaustion `v*` ordering
and the 1 m/h flag `EXACT` (`r10-foreshore-exhaustion-screening.json`); 6,800 to
9,700 m3/s and the 1.15 rainfall multiplier `CITED`; the conductivity CoV
sentence `FLAG` (3.1).

### 5.9 `mainmatter/9. Conclusions and Recommendations.tex`

Chapter 9 restates Chapters 5 to 8, including both registers
(`tab: rq answers`, `tab: recommendations`). All restatements were matched to
their sources and are `EXACT` or `ARITH`, with the single exception corrected in
2.1. Checked explicitly: 26.9 on [21.6, 35.3] at 46.39; B >= 148 and 42.7 on
[39.4, 46.6] at 39.50; 2.75 and 2.92; 4.87 and 6.03; 0.75 and 0.97; 1.7 against
6.0 and 9.3 against 3.2; 1 to 39 per cent; 1.4 and 1.04; 53 to 99 per cent; 5.67
and 3.36; 0.07; 4 per cent; 1 per cent; 58 and 73 against 5.7 and 3.4; 2.75 to
3.90 and 1.45 to 1.57; 1.4 per cent against 0.49 to 0.78; 0.316 per cent; 4 of
114 and 110; 97 of 114; 0.986 and 0.892; 12.7 / 5.5 / 7.9 / 12.7 and 5.5 to
12.6; 11.8 per cent; about 150 to about 380; about 90 per cent; 2.7 to 7.8 and
2.1 to 4.0; 6 to 9; 46; 82 / 66 / 163 / 46; 1.07 to 1.22; 1.1 to 1.8 decades;
6.6e3 against 1.01; 2.59 to 26.9; 0.061 / 0 / 0.005 and 0.62 / 0.65; 7 m; 6,800
to 9,700; 1 in 150.

### 5.10 Appendices

| Appendix | Content | Verdict |
|---|---|---|
| A (Study area and flood history) | Dates, discharges, stages and chainages from `tokachi_chisuishi_2023`, `oyo_1999`, `tokachi_levee_committee_2017` | CITED; the 38.14 / 38.26 / 38.44 / 38.56 m T.P. set and the 6,334 / 4,750 m3/s gauge-table discharges `EXACT` against `docs/tokachi_chisuishi_full_review_2026-07-27.md` |
| B (Computational architecture) | Module map, unit policy, `gamma_w = 9.81`, `g = 9.81`, N, `Delta t` | EXACT against `docs/architecture.md` and the configs |
| C (Architecture decision register) | ADR numbers and one-line summaries, ADR-0001 to ADR-0048 plus companions | EXACT against `docs/decisions/`; the "1.45 to 1.57" shape-study row EXACT |
| D (Data provenance) | 1981 and 2016 discharges, 331 mm, 37.84 m, the gauge-versus-summary discrepancy | EXACT against `docs/tokachi_chisuishi_full_review_2026-07-27.md` section 7 and `docs/tokachi_bep_inputs_provenance.md`; the underlying values CITED |
| E (Priors and geometry) | Prior mean table (5 sections x 7 parameters), `mu_ln` table, lidar re-measurement statistics, the `CoV(L)` discussion | EXACT against `data/processed/tokachi_bep_inputs.csv`, the configs and `adr0047-dem-seepage-length.json`; the "factor of about 2.9" sentence FLAG (3.1) |
| F (d4PDF ensemble and hydrograph chain) | 3,000 and 5,400 events, 50 and 90 members, 60 years, six SST patterns, the 1.66 return-level factor, the H-Q rating errors (-0.160 / 0.294 and -0.051 / 0.283) | EXACT against `ensemble_structure` and `docs/phase3_report.md` section 5 |
| G (Verification and diagnostics) | Timestep stress, N-ladder, LHS against crude, the tilted sampler, aquifer response, the bootstrap construction | EXACT against `adr0039-timestep-stress.json`, `adr0031-convergence-study.json` / `.md`, `adr0029-tail-cov-study.json`, `adr0032-aquifer-response-diagnostic.md`, `annualisation-hazard-sampling-uncertainty.json`. `(1 - 1/K)^K` = 0.364 and 0.367 ARITH. |

---

## 6. Relationships recorded as rounding or restatement, not error

These are correct as printed but are not copies of an artifact field. Recorded so
a later reader does not "fix" them into disagreement with their source.

1. `44.7` at KP 62.0's design level on 1e5 (exact quotient 44.75).
2. `73.31` per cent static rejection at KP 60.0 (artifact 73.315).
3. "no stratum rejects more than 0.02 per cent" under the bulk reading (maximum
   0.023, which prints as 0.02).
4. Half-widths "11 to 21 per cent" under warming (maximum 21.65, truncated; the
   engine's own summary carries the same range).
5. Sobol' "sum to 0.59" restating the table's own 0.585 (artifact 0.5849).
6. Sobol' design-level static sum "0.61" (artifact 0.6150).
7. Convergence "roughly 16 per cent" (artifact 16.5).
8. Warming compound factors "1.6 to 23" (artifact maximum 22.45).
9. "about seven in a thousand rising to four in a hundred" for 7.42e-3 and
   4.09e-2.
10. "roughly an order of magnitude" and "about 8.7" for the x8.67 ADR-0047 rise.
11. "a roughly fourteen-fold variation" in foreshore width (600/44 = 13.6).
12. "up to 2.7" for the M4 over-translation maximum of 2.67.
13. "a factor of three to seven short" for 3/0.85 and 3/0.45.
14. Chapter 6's bulk-reading curve shifts 1.3 / 1.9 / 4.0 / 5.2 m, which are the
    **static**-branch shifts; the transient shifts differ by at most 0.09 m and
    the sentence says "every curve".
15. Chapter 6's transient and static medians, which are linear interpolations of
    the raw Monte Carlo points to P_f = 0.5, not the fitted-lognormal medians
    (which sit 0.03 to 0.06 m higher). Both are defensible; the raw reading is
    the one the thesis uses, consistently, at all eight branch medians.
16. Chapter 7's 1e-2 and one-half crossing offsets, which use the **first
    conditioning grid level at or above the threshold** rather than an
    interpolated crossing. Consistent at all four sections and both thresholds.
17. Return periods, which are reciprocals of the **unrounded** annual
    probabilities and not of the three-significant-figure values printed beside
    them (817, not 820, from 1.2240e-3).
18. Nine further two-versus-three-significant-figure restatements in the Summary,
    where it rounds a Chapter 6 or 7 figure to fewer digits (26.9 to "about 27",
    12.658 to 12.7, and similar). Counted as nine entries in the headline table.

---

## 7. What this pass did not do

* It did not re-run the engine. Every number was read from a persisted artifact
  or a committed report of record.
* It did not verify `CITED` values against their sources; that is the provenance
  documents' job (`docs/tokachi_bep_inputs_provenance.md`,
  `docs/tokachi_chisuishi_full_review_2026-07-27.md`).
* It did not audit figures pixel by pixel. Figure **captions** carrying numbers
  were audited as claims and are included in the counts above.

---

## Addendum, 2026-08-23: two claim sites removed by the page-budget campaign

Authoritative where it differs from the body above. The 2026-08-23 main-body
page campaign (see `docs/project_log.md`, entry of that date) removed two
number-bearing sentences from `msc-thesis`. Neither number is retired and
neither value changed; what changed is the number of sites carrying it, so the
counts in the tables above are one lower in each case.

| Claim | Was traced at | Now | Status |
|---|---|---|---|
| `21.6` on `18.8 to 25.2` eleven cm above the KP 62.0 design level | Summary, Chapter 6, Chapter 9 | Chapter 6 and Chapter 9 | The Summary keeps `21.6` and the stage it belongs to and drops the interval alone. The value is unchanged and still `EXACT` against `adr0040-*.json` `anchor_A2`. |
| Historical piping and overflow shares `1.000` and `0.000` at KP 57.4 and KP 60.0 | Table `tab: system annual` body and its caption | Table body only | The caption clause that restated the two values is gone; the sentence explaining why those cells carry no sampling interval remains, and both values are printed in the table itself. |

The whole-document numeric-token diff run against the pre-campaign commit
confirms that these are the only two claim sites the campaign removed, and that
no other numeric token anywhere in `frontmatter/`, `mainmatter/` or `appendix/`
changed in value or in count except by the deliberate additions of the three
figure migrations into Appendix G.

The two items this record left awaiting a ruling from the author, the "factor of about
2.9" conductivity sentence at two sites and the cited 234 h Abashiri duration,
are untouched by the campaign and remain open.

### Second pass, same date: one further claim site removed

The rebuild confirmed 115 main-body pages and a second pass followed, cutting
the per-chapter overflows. It removed one further claim site, again without
retiring a number or changing a value.

| Claim | Was traced at | Now | Status |
|---|---|---|---|
| The drained-configuration bracket, `7.4` to `4.2` to a lower bound of `0.2` per thousand per year at KP 58.8 and `1.8` to `0.64` to zero at KP 60.0 | Chapter 1 technical scope (in per-thousand units), Chapter 7 standing-conditions register, Chapter 8 Section 8.9.4, Chapter 9 | Chapters 7, 8 and 9 | Chapter 1's scope subsection no longer quotes a Chapter 8 result. All five values survive in scientific notation at six or more sites, and Section 8.9.4 carries three qualifications the Chapter 1 passage never did. The pointer to that section was already in the Chapter 1 sentence and remains. |

Chapter 1 also lost one repetition each of `110`, `114`, `58.8` and `60.0`,
all from the same two removed passages and all still present at their other
sites in the same chapter. Nothing else numeric moved: the whole-document
token diff over `frontmatter/`, `mainmatter/` and `appendix/` is otherwise
accounted for by one figure-width change and the preamble.
