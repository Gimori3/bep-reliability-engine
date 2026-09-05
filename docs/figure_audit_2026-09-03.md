# Figure audit, 2026-09-03

**Scope.** The 30 bitmap figures and the TikZ figures of the main body, read as
images against five standards (numbers, notation, orthography, house style,
convention consistency), plus each figure's caption against what the figure
actually draws. Every previous audit of this thesis read `.tex` source only;
the PNGs were invisible to all of them. This is the first pass to open them.

**Authorisation used.** Figure-generating scripts under `scripts/` were edited,
the affected PNGs re-rendered from persisted records, copied into
`msc-thesis/figures/`, and two figure captions corrected. No computed value was
changed, no production sweep, Phase 2 replay or Phase 3 campaign was run, and
no thesis prose outside those two captions was touched. The follow-up pass of
section 10 extends the same authorisation to six appendix figures, which the
sweep for two of its items reached.

**Method for every regeneration.** The figure was first re-rendered from the
committed record with the script unedited and pixel-diffed against the
committed PNG; only where that baseline came back byte-identical was the edit
applied and the figure re-rendered a second time. Every diff below is against
the pre-audit committed PNG.

---

## 1. Inventory and provenance

### 1.1 Main-body bitmap figures (30) and their generators

| # | Ch | Figure | Generator |
|---|----|--------|-----------|
| 1 | 3 | `study_reach_map.jpg` | **none traced** (see 1.3) |
| 2 | 3 | `adr0047_dem_seepage_length.png` | `scripts/dem_cross_section_study.py` |
| 3 | 5 | `adr0039-timestep-stress.png` | `scripts/timestep_convergence_stress.py` |
| 4 | 5 | `validation_shikaga_m4_pattern.png` | `scripts/plot_validation_shikaga.py` |
| 5 | 5 | `validation_yabe_timeline.png` | `scripts/plot_validation_yabe.py` |
| 6 | 5 | `gsa_indices_kp58_8_matrix.png` | `scripts/gsa_study.py` |
| 7 | 5 | `gsa_interaction_kp58_8_matrix.png` | `scripts/gsa_study.py` |
| 8 | 5 | `gsa_levels_kp58_8_matrix.png` | `scripts/gsa_study.py` |
| 9 | 5 | `epistemic_bracket_ranking.png` | `scripts/thesis_figure_gaps.py` |
| 10 | 5 | `epistemic_vs_statistical.png` | `scripts/hwl_bias_resolution.py` |
| 11 | 6 | `fragility_per_section.png` | `scripts/plot_fragility_curves.py` |
| 12 | 6 | `initiation_fragility.png` | `scripts/plot_initiation_fragility.py` |
| 13 | 6 | `fragility_comparison.png` | `scripts/plot_fragility_curves.py` |
| 14 | 6 | `fragility_tail_log.png` | `scripts/plot_fragility_curves.py` |
| 15 | 6 | `rq1_hwl_dbeta_resolved.png` | `scripts/rq1_beta_analysis.py` |
| 16 | 6 | `rq1_kp57_4_dbeta_bound.png` | `scripts/rq1_beta_analysis.py` |
| 17 | 6 | `rq1_beta_waterfall.png` | `scripts/rq1_beta_analysis.py` |
| 18 | 6 | `stage6_6_fractions_kp62_0.png` | `scripts/stage6_6_gap_decomposition.py` |
| 19 | 6 | `rq1_delta_beta_vs_stage.png` | `scripts/rq1_beta_analysis.py` |
| 20 | 6 | `phase2_survival_update.png` | `scripts/thesis_figure_gaps.py` |
| 21 | 6 | `phase2_fragility_update_kp58_8_matrix.png` | `bayesian_reliability_updating/plots.py` |
| 22 | 6 | `phase2_peak_shortcut.png` | `scripts/thesis_figure_gaps.py` |
| 23 | 6 | `seepage_length_system_and_ceiling.png` | `scripts/seepage_length_figures.py` |
| 24 | 7 | `phase3_system_fragility_bep_sections.png` | `scripts/phase3_figures.py` |
| 25 | 7 | `conductivity_bracket_annual.png` | `scripts/conductivity_annualisation_study.py` |
| 26 | 7 | `conductivity_bracket_both_d70.png` | `scripts/conductivity_annualisation_study.py` |
| 27 | 7 | `phase3_rq4_four_sections.png` | `scripts/phase3_figures.py` |
| 28 | 7 | `rq4_sensitivity_brackets.png` | `scripts/thesis_figure_gaps.py` |
| 29 | 7 | `phase3_rq4_attribution.png` | `scripts/phase3_figures.py` |
| 30 | 8 | `r10_foreshore_exhaustion.png` | `scripts/foreshore_exhaustion_study.py` |

### 1.2 TikZ figures: there are four in the main body, not three

| Ch | Figure | Source |
|----|--------|--------|
| 1 | thesis roadmap (`fig: thesis roadmap`) | inline `tikzpicture` |
| 2 | STPH failure chain (`fig: stph chain`) | inline `tikzpicture` |
| 2 | annotated cross-section (`fig: annotated cross section`) | `\input{figures/annotated_cross_section}` |
| 4 | three-phase framework (`fig:conceptual_framework`) | inline `tikzpicture` |

All four are **clean on all five standards**. Their descriptive subscripts are
already upright (`\gamma'_\mathrm{bl}`, `D_\mathrm{bl}`, `I_\mathrm{er}`,
`Z_\mathrm{static}`, `z_\mathrm{toe}`, `k_\mathrm{aq}`, `\lambda_\mathrm{in}`,
`\lambda_\mathrm{out}`), they carry no dash, no `x` multiplier, no `%`, and no
Japanese script, and their numbers agree with the text
(`h = 46.39`~m T.P., `z_toe = 44.90`, `D_bl = 0.45`, `L = 40`, `B_f = 44`,
`r_e = 0.351`).

### 1.3 Figures that cannot be traced to a generator in this repository

* **`study_reach_map.jpg`** (Chapter 3, Figure 3.1). No script under
  `scripts/` writes it; it is a hand-composed satellite/alignment graphic. It
  cannot be regenerated here, so its two defects are reported only (section 5).
* **`annotated_cross_section.tex`** is generated, but by
  `msc-thesis/scratch/figures/make_annotated_cross_section.py`, which sits in
  the thesis repository's **gitignored** `scratch/`. The generator of a
  main-body figure is therefore under version control in neither repository.
  Flagged; nothing was changed.

### 1.4 Orphans

`rq1_beta_curves.png`, `adr0040_hwl_bias_resolved.png` and
`adr0040_kp57_4_bound.png` exist in `msc-thesis/figures/` but no `.tex`
includes them. This matters for one item in the audit brief: the brief cites
`rq1_beta_curves.png` as the figure that *does* shade the ADR-0024 extension
next to `fragility_tail_log.png`, which does not. It does shade it, but it is
not in the document, so the contrast the brief draws is not one a reader of the
thesis can see. The shading contrast that *is* in the document is described in
section 4.

---

## 2. Per-figure verdicts

Key: **N** numbers, **No** notation, **O** orthography, **H** house style,
**C** convention consistency. `.` = pass, `X` = defect found, `X→f` = defect
found and fixed, `!` = flagged, deliberately not changed, `!→f` = flagged
in the first pass and fixed in the follow-up of section 10.

| Figure | N | No | O | H | C | What was found |
|---|:-:|:-:|:-:|:-:|:-:|---|
| `study_reach_map.jpg` | . | . | . | X! | . | Ranges as `KP53.8〜KP62.0`, `KP3.2〜KP16.6` (CJK wave dash). No generator; not fixable here |
| `adr0047_dem_seepage_length.png` | **X→f** | . | . | X!→f | . | **Labelled the adopted 2025 lidar value 40.0 m as "1998 survey"**; the 1998 value is 47 m, as the figure's own bottom panel says. Fixed. House style, and an inverted static/transient hue, fixed in section 10.3 |
| `adr0039-timestep-stress.png` | . | X→f | . | X→f | . | `k_aq`/`C_e`/`D_bl`/`l_c`/`l_e`/`l(t)` as ASCII; "1% criterion"; ensemble member ids in the legend (fixed, section 10.1). Caption named no panel and described a plot that is not drawn (fixed, section 3) |
| `validation_shikaga_m4_pattern.png` | . | . | . | . | . | clean |
| `validation_yabe_timeline.png` | X! | X→f | X→f | X→f | . | "modelled"; `5-95%`, `25-75%`; `P(reach)` collides with a different quantity in the text (section 6) |
| `gsa_indices_kp58_8_matrix.png` | . | X→f | . | X→f | . | `k_{aq}`, `D_{aq}`, `D_{bl}`, `k_{bl}`, `\gamma'_{bl}` italic against the caption's own upright forms; `l_e/L`, `Z_static` ASCII; "95% CI" |
| `gsa_interaction_kp58_8_matrix.png` | . | X→f | . | . | . | same subscripts; `$C_e \times k_{aq}$` |
| `gsa_levels_kp58_8_matrix.png` | . | X→f | . | . | . | same subscripts |
| `epistemic_bracket_ranking.png` | . | X→f | . | X→f | ! | `k_{aq}`, `z_{toe}`, `\gamma'_{bl}`; `--` as a dash |
| `epistemic_vs_statistical.png` | . | X→f | . | X→f | . | `k_{aq}`, `z_{toe}`, `\gamma'_{bl}`; "6 to 9x", "6.4x wider"; "criterion F3" left (section 5) |
| `fragility_per_section.png` | . | X→f | . | X→f | ! | `k_{bl}` italic; "95% Clopper–Pearson" (en dash + `%`); run seed and member id in the stamp (fixed, section 10.1) |
| `initiation_fragility.png` | . | . | . | . | . | clean |
| `fragility_comparison.png` | . | X→f | . | X→f | ! | `z_{toe}`, `k_{bl}`; en dash; run seed and member id in the stamp (fixed, section 10.1); x-axis passes the KP 62.0 attainable maximum with no band (caption says so) |
| `fragility_tail_log.png` | . | X→f | . | X→f | ! | `z_{toe}`, `k_{bl}`; "95% binomial CIs"; run seed and member id in the stamp (fixed, section 10.1); unshaded band, caption compensates (section 4) |
| `rq1_hwl_dbeta_resolved.png` | **X→f** | X→f | X→f | . | . | **`Δβ = 0.90 [0.85, 0.98]` against `[0.85, 0.97]` at six sites in the text.** `\beta_{trans}`, `\beta_{static}`; "neighbourhood"; "stabiliser" (from `_figstyle`) |
| `rq1_kp57_4_dbeta_bound.png` | . | X→f | . | X→f | . | `\beta_{trans}`, `\beta_{static}`; three `--` dashes. Caption said the anchor is labelled with its interval on `B`; it is labelled on `Δβ` (fixed, section 3) |
| `rq1_beta_waterfall.png` | . | . | . | . | . | clean; 0.36 / 0.00 / 0.55 and 1.01 / 0.18 / 0.37 both reconcile (section 6) |
| `stage6_6_fractions_kp62_0.png` | . | . | . | . | ! | unshaded above 50.5 m, caption compensates |
| `rq1_delta_beta_vs_stage.png` | . | X→f | . | . | . | `\beta_{trans}`, `\beta_{static}`, `P_{f,static}/P_{f,trans}` |
| `phase2_survival_update.png` | . | . | . | . | . | clean; eight strata reconcile to the text digit for digit |
| `phase2_fragility_update_kp58_8_matrix.png` | . | . | . | X! | . | "CP 95% CI"; generator is a package module, outside the authorised edit surface |
| `phase2_peak_shortcut.png` | . | . | . | X→f | . | `x2.75`, `x3.90`, `x7.46`, `x6.12` as the letter x |
| `seepage_length_system_and_ceiling.png` | . | X→f | X→f | X→f | . | `\lambda_{ac}`, `k_{aq}`, `D_{bl}`; "centre" against the caption's "center"; `1.2-2.0 km`, `1.4-1.7x` |
| `phase3_system_fragility_bep_sections.png` | . | . | . | . | ! | panel titles "Tokachi KP 60"/"KP 62" (fixed to one decimal); band drawn at the +4 K ensemble maximum 51.47 m, not the ADR-0024 50.5 m (caption states both) |
| `conductivity_bracket_annual.png` | . | . | . | . | . | Figure note said "Open circles mark the production value" while an open marker means the warming scenario in the same figure; the mark is a ring. Fixed |
| `conductivity_bracket_both_d70.png` | . | . | . | . | . | clean |
| `phase3_rq4_four_sections.png` | . | X→f | X→f | X→f | . | `\lambda_{ac}`; "characterised"; `12.7x`, `5.5x`, `7.9x` |
| `rq4_sensitivity_brackets.png` | . | X→f | X→f | X→f | . | `\lambda_{ac}`; "characterised", "labelled"; `--` as a dash |
| `phase3_rq4_attribution.png` | . | X→f | . | X→f | . | `P_f` as ASCII; `>=`, `<=`; "KP60"/"KP62" tick labels lost their decimal |
| `r10_foreshore_exhaustion.png` | . | X→f | . | X!→f | . | `v_{lat}`, `T_{mob}` italic against the appendix's own upright forms; "kosuishiki-haba" (fixed, section 10.4) |

---

## 3. Caption findings

Every caption was read against its figure. Two were wrong; both are fixed.
The rest are true of what their figure draws.

1. **Chapter 5, `fig: timestep stress`.** The caption described
   "breach-threshold stage against integration timestep", which no panel draws,
   and named none of the figure's four panels. Rewritten at the same length to
   name (a) to (d) and to say where the breach threshold is actually read.
2. **Chapter 6, `fig: kp57 bias bound`.** "the quotable resolved anchor at
   39.50~m is labeled with its interval on $B$" — the figure labels it with its
   interval on `Δβ` (`1.27 [1.25, 1.29]`); the `B` interval is in the text, not
   the figure. Changed to `$\Delta\beta$`.

Two further caption/figure tensions were found and **left alone**, because the
caption is deliberate and the resolution is the author's call:

3. `fig: fragility per section` and `fig: fragility tail log` label KP 58.8 and
   KP 60.0 **"drained"** on the panel while the caption says both are
   "evaluated as if undrained". The panel label is the as-built remediation
   state and the caption is the modelling treatment, so neither is false, but a
   reader who does not reach the caption will take the curve for a
   drained-section curve.
4. Four main-body captions carry vocabulary the figure does not: the figures
   count "rows", the captions count "realizations" (section 5, item B).

---

## 4. Convention consistency: the ADR-0024 attainable maximum

Four main-body figures have an x-axis that crosses their section's attainable
maximum. Reported, not changed, per the brief.

| Figure | Axis reaches | Band drawn at | Caption |
|---|---|---|---|
| `rq1_hwl_dbeta_resolved.png` | 56.5 m | 50.5 m | states it |
| `fragility_per_section.png` | 56.5 m | 50.5 m | states it |
| `fragility_tail_log.png` | 56.5 m | **none** | four lines of compensation |
| `fragility_comparison.png` | `h − z_toe` 8 m | **none** | one line of compensation |
| `stage6_6_fractions_kp62_0.png` | 56.5 m | **none** | states it |
| `phase3_system_fragility_bep_sections.png` | 56.5 m | **51.47 m** | states both |

Two observations for the author's decision.

* `fragility_comparison.png` plots four sections on a **relative** axis
  (`h − z_toe`), so a single band would be read as applying to all four when
  only KP 62.0 crosses. The textual note in its footer is arguably the right
  call there and the shading is not.
* `phase3_system_fragility_bep_sections.png` shades from **51.47 m**, the
  largest peak in the +4 K ensemble, where every other figure shades from
  **50.5 m**, the ADR-0024 attainable maximum. Both are labelled for what they
  are and the caption already reconciles them explicitly, but the document does
  contain two different lines called "max attainable" for the same section.

---

## 5. Found and deliberately not changed

> **Amended 2026-09-03, later the same day.** The author directed that items
> **A**, **D**, **H** and **I** be fixed in full. They are, and section 10
> records the work. Their entries below are kept as the finding, each with
> its resolution appended. **B**, **C**, **E**, **F**, **G** and **J** stand
> as written.

**A. Run identifiers and a seed baked into four main-body figures.**
`fragility_per_section`, `fragility_comparison` and `fragility_tail_log` stamp
`seed 20260626` and `canonical d4PDF shape HPB_m064_1987`;
`adr0039-timestep-stress` names `HPB_m049_2001` and `HPB_m064_1987` in its
legend. `_figstyle`'s own house rule bans a run identifier in a main-body
figure, and the thesis names none of these. Removing them is a provenance
decision, not a defect fix, so it was left to the author. All four figures write
at a fixed canvas size, so the change would be dimension-free.
**Fixed (section 10.1).** A fifth instance was found while fixing these four:
`adr0031-tail-lhs-vs-crude.png` and its KP 60.0 twin, in Appendix E, printed
the raw run identifier `tokachi_kp58.8` in their title.

**B. "rows" where the captions say "realizations".** `rq1_hwl_dbeta_resolved`
("transient failing rows", "R1 floor = 30 rows"), `rq1_kp57_4_dbeta_bound`,
`phase2_peak_shortcut` ("5,673 rejected rows") and `epistemic_knobs_mp_ztoe`
count matrix rows; the captions and the running text count realizations. This
is implementation vocabulary under `docs/conventions.md` §9.3.1. Not changed:
the strings sit in rotated y-labels and legend entries where lengthening them
would move the tight bounding box, and the captions already gloss the term.

**C. "criterion F3" in `epistemic_vs_statistical.png`.** A pre-registration tag
in a main-body figure. Left because the caption deliberately says "labeled F3
in the figure".

**D. ADR numbers in an appendix figure.** `stage6_6_heq_kp62_0.png` and
`stage6_6_heq_kp57_4.png` (Appendix H) title themselves
"H_eq-conservatism bound (ADR-0009/0041)". Outside the audited main-body set;
the house rule is written for the main body only. Flagged.
**Fixed (section 10.2), and the class turned out to be five figures, not two.**
`epistemic_knobs_mp_ztoe.png` (Appendix I) named ADR-0045, ADR-0021 and
ADR-0046; `adr0040_tilted_is_validation.png` (Appendix E) named ADR-0029;
`adr0029-tail-cov.png` (Appendix E) named ADR-0029 and carried the
failure-mode tag `fm5` and an **em dash**; `adr0032_aquifer_response.png`
(Appendix E) carried the specification pointer `spec §11`; and
`adr0031-tail-lhs-vs-crude.png` and its twin carried `fm5` and two em dashes.

**E. `KP57.4` against `KP 57.4`.** The `thesis_figure_gaps` and `stage6_6`
families render the section without the space; `_figstyle.section_label` and
the thesis render it with one. Cosmetic and pervasive; changing it would touch
tracked evidence CSVs for no reader-visible gain. The related change that *was*
made is different in kind: `phase3_rq4_attribution` and
`phase3_system_fragility_bep_sections` rendered "KP60" and "KP62", dropping a
significant digit rather than a space, and are now "KP 60.0" and "KP 62.0".

**F. "95%" in compact axis and tick labels.** Normalised to "per cent" only
where the figure text is a running sentence. Left as `%` where it is a unit or
a bracketed qualifier, which is the convention the figures' own axis labels
already use (`rejected [%]`). One attempt to change
`Clopper-Pearson (95%)` to `(95 per cent)` in `epistemic_bracket_ranking.png`
widened the PNG from 2700 to 2751 px, because it is a left-side tick label that
drives the tight bounding box; it was reverted on that evidence.

**G. `study_reach_map.jpg`.** Two ranges use the CJK wave dash `〜`
(`Tokachi KP53.8〜KP62.0`, `Satsunai KP3.2〜KP16.6`). The wave dash is
punctuation, not kanji, hiragana or katakana, so it does not breach the
Japanese-script rule; it does breach "ranges are written X to Y". The figure
has no generator in this repository and cannot be re-rendered here.

**H. `adr0047_dem_seepage_length.png` does not use the house style.** Default
matplotlib palette, boxed legends, all four spines, `alpha=0.3` grid. Bringing
it onto `_figstyle` would move every element of a twelve-panel figure; out of
scope for a labelling audit.
**Fixed (section 10.3).** The restyle also corrected a substantive defect the
style masked: the figure drew the **transient** branch blue and the **static**
branch orange, the reverse of the assignment fixed for the whole thesis.

**I. "OYO kosuishiki-haba" in `r10_foreshore_exhaustion.png`.** A romanised
Japanese term that the thesis itself never uses: Chapter 8, Chapter 9 and
Appendix I all say "high-water-bed width". The usual romanisation of 高水敷 is
also *kosuijiki*, not *kosuishiki*. Both a redundancy and a probable
mis-romanisation, but correcting or deleting it is a terminology decision.
**Fixed (section 10.4):** the bracket now reads `(OYO survey)`.

**J. `phase2_fragility_update_kp58_8_matrix.png`** carries "CP 95% CI". Its
generator is `bayesian_reliability_updating/plots.py`, a package module under
test, outside the `scripts/` edit surface the brief authorises.

---

## 6. Number checks in full

Every number rendered inside a main-body figure was located in the thesis and
compared. Beyond the two findings below, all agree.

**Finding 1, the known one — fixed.** `rq1_hwl_dbeta_resolved.png` annotated
the KP 62.0 design-HWL anchor `Δβ = 0.90 [0.85, 0.98]`; the thesis says
`[0.85, 0.97]` at six sites (Chapter 5, the epistemic-band section; Chapter 6, `eq: kp62 bias` and the
section contrasting the two metrics; Chapter 8; Table 9.1; and the Summary).

`docs/decisions/rq1-beta-reexpression.json` carries three paired-bootstrap
draws of that one estimand (46.39 m, `N = 10^6`, 1000 replicates):

| record path | interval | to 2 dp |
|---|---|---|
| `design_anchors.kp62_0.delta_beta_ci` | `[0.85162, 0.96926]` | `[0.85, 0.97]` |
| `grids.kp62_0[9].delta_beta_ci` | `[0.84981, 0.97513]` | `[0.85, **0.98**]` |
| `ladder.kp62_0.by_n.1000000.stages[0].total_delta_beta_ci` | `[0.84652, 0.96555]` | `[0.85, 0.97]` |

**`design_anchors` is canonical, and the figure was moved onto it.** Three
reasons. It is the entry purpose-built for the anchor, and the only one
carrying `artifact` and `section` provenance fields. It is the entry
`docs/thesis_number_reconciliation_2026-08-30.md` correction 2.2 names as "the
reported interval" when it verifies the paired-bootstrap construction. And the
thesis quotes `[0.852, 0.969]` from it at all six sites, so moving the text
would mean six edits to prose that is already correct, against one edit to a
figure that was reading a per-level sweep where it should have read the anchor.
`scripts/rq1_beta_analysis.py::figure_hwl_dbeta_resolved` now takes the A1
callout's interval from `design_anchors` and everything else from the sweep.

One residual, stated rather than hidden: the shaded 95 % band in that figure is
still the per-level sweep, so its upper edge at 46.39 m is 0.9751 where the
annotation now reads 0.969. The two are independent 1000-replicate draws of the
same estimand and differ by 0.006, which is 0.5 % of the right-hand panel's
vertical extent, about two pixels. The band is a curve and the annotation is a
quotation; they are correctly sourced differently.

**Finding 2, new — fixed.** `adr0047_dem_seepage_length.png` labelled the
KP 62.0 reference line **"1998 survey 40.0 m"** in both the panel title and the
legend. 40.0 m is the value adopted from the 2025 lidar; the 1998 value is
47 m. The figure contradicted itself (its own bottom panel reads "withdrawn
1998 value L = 47 m"), contradicted Chapter 3 ("the 1998 reading of 47~m
credited a landside berm that has never existed") and Appendix B ("the
clean-station median is 40~m against the tabulated 47~m"), and forced its
caption to spend a sentence explaining what the line really is. The cause is
that the label hard-codes "1998 survey" in front of `record['csv_L_m']`, which
is whatever the geotechnical CSV holds *now*. The generator now derives the
source per section — a section is adopted exactly where the 1998 reading was
withdrawn — so KP 62.0 reads "adopted 40.0 m" and the other three keep
"1998 survey 33.0 / 35.0 / 34.8 m".

**A near-miss that is not a disagreement, disambiguated anyway.**
`validation_yabe_timeline.png` annotated `P(reach) = 0.06 / 0.53 / 0.96`, while
the facing text says the breach probability "rises from 0.04 at the committee's
central value to 0.90 at the coarse, trench-confirmed permeability". These are
two different quantities, both in `results/validation_yabe/`: `P(l ≥ L)` over
the whole simulated window (0.060, 0.53, 0.96) and `P(breach ≤ observed
6.33 h)` (0.035, 0.41, 0.90), and the text's "within that interval" names the
second correctly. Nothing is wrong, but a generic "P(reach)" beside "0.04 to
0.90" invites the reader to equate them. The labels now name the endpoint each
panel measures: `P(l ≥ L)` and `P(l ≥ l_c)`.

**Checks that passed.** The 46.50 m anchor (`Δβ = 0.90`, `B = 21.6`, 176 rows)
against Chapter 9; the KP 57.4 anchors (39.21 m `Δβ ≥ 1.27`, `B ≥ 148`, 2 rows;
39.25 m `Δβ ≥ 1.23`; 39.50 m `Δβ = 1.27`, `B = 42.7`, 521 rows, 1 barrier-jump
row of 4 in `10^6` at three levels) against Chapter 6; the additive ladder
(0.36 / 0.00 / 0.55 at KP 62.0 design, 1.01 / 0.18 / 0.37 at KP 57.4 design)
against Table 9.1, which quotes 0.36 / 0.81 and 0.55 / 0.38 — the second pair
being KP 57.4 at the **39.50 m** resolved anchor, which the figure labels its
panels clearly enough to keep distinct; all eight Phase 2 rejection shares
(0.065 / 5.673 / 3.363 / 0.000 transient and 6.258 / 57.634 / 73.315 / 0.000
static) against the survival-update section of Chapter 6; the peak-shortcut factors 2.75 and 3.90 against the replay section of Chapter 6; all
sixteen annual probabilities and the four climate ratios (12.7 / 5.5 / 7.9 /
12.7 with intervals 7.3–28.1, 4.1–7.7, 5.3–12.9, 7.7–24.8) against
the Chapter 7 annual table and its climate-ratio section; the DEM clean-station medians 36 / 42 / 43 / 40 m against
Appendix B; the reach-union bound "1.4 to 1.7 at 1.2 to 2.0 km" against
Appendix B; the foreshore widths 200 / 325 / 600 / 44 m against Chapter 3; the
FEM translation factors 1.13, 1.15–1.55, 1.97, 2.67 against the hydraulic-translation section of Chapter 5; and the GSA
first-order rotation 0.011 to 0.114 and total-effect `L` share against the sensitivity section of Chapter 5.
No equal-convention value is rendered inside any figure.

---

## 7. Pixel-diff evidence

35 published PNGs changed. 32 keep their exact dimensions; three change by one
to four pixels because `bbox_inches="tight"` reallocates when a y-label becomes
`$P_f$` instead of `P_f`. The isolated build (section 8) proves no page moved.

| Figure | size | new size | changed px | changed region (x0,y0,x1,y1) |
|---|---:|---:|---:|---|
| `adr0039-timestep-stress.png` | 2310x1672 | same | 11.647% | (29, 72, 2282, 1640) |
| `adr0040_hwl_bias_resolved.png` | 2108x990 | same | 0.007% | (901, 691, 925, 700) |
| `adr0040_kp57_4_bound.png` | 1547x1052 | same | 0.844% | (249, 114, 1509, 322) |
| `adr0040_tilted_is_validation.png` | 2367x974 | same | 0.006% | (1799, 715, 1823, 724) |
| `adr0047_dem_seepage_length.png` | 2576x1540 | same | 0.148% | (2045, 112, 2509, 707) |
| `conductivity_bracket_annual.png` | 2423x1153 | same | 0.316% | (684, 1118, 1741, 1135) |
| `epistemic_bracket_ranking.png` | 2700x1050 | same | 0.130% | (148, 31, 1869, 887) |
| `epistemic_knobs_mp_ztoe.png` | 2263x1318 | same | 0.019% | (181, 262, 2099, 700) |
| `epistemic_vs_statistical.png` | 2286x1203 | same | 0.247% | (178, 24, 1607, 1064) |
| `fragility_comparison.png` | 2520x1120 | same | 0.025% | (302, 979, 2127, 1109) |
| `fragility_per_section.png` | 2520x1639 | same | 0.142% | (348, 1592, 988, 1631) |
| `fragility_tail_log.png` | 2520x1639 | same | 0.220% | (536, 33, 1125, 1603) |
| `gsa_companions.png` | 1680x768 | same | 0.066% | (228, 140, 1440, 738) |
| `gsa_convergence_kp58_8_matrix.png` | 1760x752 | same | 0.221% | (25, 240, 1726, 730) |
| `gsa_convergence_kp60_0_matrix.png` | 1760x752 | same | 0.228% | (25, 184, 1726, 730) |
| `gsa_indices_kp58_8_matrix.png` | 1760x1216 | same | 4.292% | (26, 26, 1736, 1139) |
| `gsa_indices_kp60_0_matrix.png` | 1760x1216 | same | 4.451% | (26, 26, 1736, 1111) |
| `gsa_interaction_kp58_8_matrix.png` | 1184x800 | same | 1.989% | (150, 38, 1151, 778) |
| `gsa_interaction_kp60_0_matrix.png` | 1184x800 | same | 1.993% | (149, 38, 1151, 778) |
| `gsa_levels_kp58_8_matrix.png` | 1760x784 | same | 2.232% | (138, 116, 1725, 762) |
| `gsa_levels_kp60_0_matrix.png` | 1760x784 | same | 1.843% | (114, 148, 1725, 762) |
| `phase2_peak_shortcut.png` | 2267x986 | same | 1.223% | (18, 50, 2231, 764) |
| `phase3_climate_shift.png` | 1675x1102 | 1679x1102 | - | y-label `P_f` set as maths |
| `phase3_dominance_profile.png` | 1675x1304 | same | 0.006% | (685, 57, 705, 66) |
| `phase3_event_based_validation.png` | 1063x959 | 1061x958 | - | axis labels `P_f` set as maths |
| `phase3_rq4_attribution.png` | 1896x755 | 1894x755 | - | y-label `P_f` set as maths |
| `phase3_rq4_four_sections.png` | 2345x914 | same | 0.139% | (434, 16, 1612, 580) |
| `phase3_system_fragility_bep_sections.png` | 1819x1334 | same | 0.182% | (414, 769, 1482, 788) |
| `r10_foreshore_exhaustion.png` | 1840x736 | same | 0.041% | (38, 249, 979, 363) |
| `rq1_delta_beta_vs_stage.png` | 2242x1161 | same | 0.094% | (210, 276, 239, 989) |
| `rq1_hwl_dbeta_resolved.png` | 1916x990 | same | 0.227% | (49, 52, 1807, 700) |
| `rq1_kp57_4_dbeta_bound.png` | 1765x1097 | same | 0.522% | (126, 150, 1582, 617) |
| `rq4_sensitivity_brackets.png` | 2267x947 | same | 1.298% | (434, 17, 1853, 918) |
| `seepage_length_system_and_ceiling.png` | 1960x644 | same | 1.195% | (34, 13, 1784, 617) |
| `validation_yabe_timeline.png` | 1209x706 | same | 1.668% | (265, 59, 1202, 690) |

**Reading the two large numbers.** `adr0039-timestep-stress` at 11.6 % and the
`gsa_*` family at 2 to 4.5 % are not data changes. Both write at a fixed canvas
(`savefig` without `bbox_inches`), so when `k_aq` becomes `$k_\mathrm{aq}$` the
tick-label column widens, `tight_layout` reallocates the axes rectangle, and
every mark inside translates by a few pixels. Both were re-read as images
afterwards: every curve, bar and marker is in the same data position, and the
only text that differs is the text that was edited.

**Baseline fidelity.** Before any edit, each generator was run against its
committed record and the output pixel-diffed to zero:
`rq1_hwl_dbeta_resolved`, `rq1_kp57_4_dbeta_bound`, `rq1_beta_waterfall`,
`rq1_delta_beta_vs_stage`, `r10_foreshore_exhaustion` and
`adr0039-timestep-stress` all came back IDENTICAL. `phase2_survival_update`,
`seepage_length_marginal`, `seepage_length_marginal_ratio`,
`conductivity_bracket_both_d70` and `validation_yabe_discrimination` are
IDENTICAL after the edits too, because nothing in them needed changing.
Black reformatted two scripts after the fact; all ten affected figures were
re-rendered and pixel-diffed to zero against the pre-format versions.

**No plotted value moved.** Every regeneration read a persisted record. The one
generator that re-derives rather than re-reads its plotted curves,
`timestep_convergence_stress.py --figures-only`, re-integrates its showcase
trajectories from the persisted ladder selection; its unedited baseline came
back byte-identical, which is what licenses the re-render. No script was run
that would have recomputed a result, and no evidence file changed: the six
`docs/decisions/*.csv` that `thesis_figure_gaps.py figures` rewrites came back
content-identical (line endings only) and were restored.

---

## 8. Isolated build

`report.tex`, `tudelft-report.cls`, `references.bib`, `frontmatter/`,
`mainmatter/`, `appendix/` and `figures/` copied to a scratch directory outside
both repositories; `latexmk -xelatex` run there; page extents read off the
`\contentsline` entries of the fresh `.toc`.

| Gate | Expected | Measured |
|---|---|---|
| undefined references | 0 | **0** |
| undefined citations | 0 | **0** |
| multiply-defined labels | 0 | **0** |
| citation keys | 106 | **106** (aux and bbl agree) |
| labels | 387 | **387** (387 unique) |
| main body pages | 99 | **99** |
| References begins on | 100 | **100** |
| per-chapter map | 6, 10, 12, 12, 11, 18, 12, 11, 7 | **6, 10, 12, 12, 11, 18, 12, 11, 7** |
| appendices A to K | 7, 8, 7, 3, 12, 4, 5, 13, 5, 7, 3 = 74 | **7, 8, 7, 3, 12, 4, 5, 13, 5, 7, 3 = 74** |
| total pages | 193 | **193** |
| overfull hboxes | 12 or fewer | **12** |
| worst overfull | ≤ 15.4 pt | **15.386 pt** |

Appendix K's extent is arithmetic rather than a `\contentsline` difference,
K being the last chapter: it begins at printed page 177, the last absolute page
is 193 (`\@abspage@last`), and the fourteen roman front-matter pages put the
last printed page at 179, so K spans 3.

Engine checks: `ruff check .` clean, `black --check .` clean, `pytest -m "not
slow"` 903 passed, 7 deselected.

Thesis hygiene on the two edited `.tex` files: no `—`, no `---`, no CJK, line
endings preserved (Chapter 5 stays CRLF, Chapter 6 stays LF), every `\label`
and citation key untouched.

---

## 9. Answers to the two closing questions

**Did any figure disagree with the text on a number besides the known one?**
Yes, one. `adr0047_dem_seepage_length.png` (Chapter 3) labelled the adopted
2025 lidar seepage length 40.0 m as a "1998 survey" value, where the 1998 value
is 47 m — contradicting the figure's own bottom panel, Chapter 3 and
Appendix B. It is fixed at source. One further case was a near-collision rather
than a disagreement and was disambiguated anyway: the Yabe timeline figure's
`P(reach)` is a different quantity from the breach probability quoted three
lines above it in Chapter 5, and now says which endpoint it measures. Every
other rendered number in all 30 main-body figures reconciles.

**Is the headline confidence interval now identical everywhere?** Yes.
`Δβ = 0.90` with a 95 per cent interval of `[0.85, 0.97]` now reads the same in
the figure (`rq1_hwl_dbeta_resolved.png`, A1 callout), the equation
(Chapter 6, `eq: kp62 bias`), Table 9.1, the Chapter 8 restatement, the
Summary, and the two further sites in Chapter 5 and Chapter 6. Seven sites, one number, one canonical record
(`design_anchors.kp62_0` in `docs/decisions/rq1-beta-reexpression.json`).

---

## 10. Follow-up pass: items A, D, H and I closed

Directed by the author after the report above was written. Same method: the
generator was run unedited and pixel-diffed against the committed PNG first
wherever the re-render path had not already been proved, then the edit was
applied and the figure re-rendered. **All sixteen figures touched here keep
their exact pixel dimensions**, and the isolated build reproduces every gate
(section 10.6).

Two of the four items turned out to be larger than the report had them. The
audit's five standards were applied to the 30 main-body figures, so the sweep
that found items A and D had only looked there. Re-running it over every figure
that appears anywhere in the thesis, appendices included, found **five** more
instances. They are fixed too, and the sweep is now clean: no rendered text in
any figure in this document carries an ADR number, a specification pointer, a
failure-mode tag, a run identifier, a file-format name or an em dash.

### 10.1 Item A: run identifiers and the sample seed

| Figure | Was | Now |
|---|---|---|
| `fragility_per_section.png`, `fragility_comparison.png`, `fragility_tail_log.png` (Ch. 6) | "N = 10^5 Latin hypercube (seed 20260626), canonical d4PDF shape HPB_m064_1987" | "N = 10^5 Latin hypercube, canonical d4PDF compound shape" |
| `adr0039-timestep-stress.png` (Ch. 5) | legend "flashiest: HPB_m049_2001", "production shape: HPB_m064_1987" | "flashiest historical member", "canonical production shape" |
| `adr0031-tail-lhs-vs-crude.png` and its KP 60.0 twin (App. E) | title "... tokachi_kp58.8, R=50" | "Stratified against crude sampling, KP 58.8, R = 50 replicates" |

The last row is the fifth instance, found by the re-sweep. It is the exact case
`_figstyle.section_label` exists to prevent: the driver imports that helper for
its other figure and had not applied it here. "Canonical d4PDF compound shape"
is the thesis's own phrase for the loading (Chapter 6). Nothing is lost: the
seed and both member ids are in the JSON sidecar beside every persisted result,
which is where run provenance belongs, and the thesis names none of them.

### 10.2 Item D: ADR numbers, specification pointers and failure-mode tags

| Figure | Was | Now |
|---|---|---|
| `stage6_6_heq_kp62_0.png`, `stage6_6_heq_kp57_4.png` (App. H) | "H_eq-conservatism bound (ADR-0009/0041)" | "H_eq-conservatism bound" |
| `epistemic_knobs_mp_ztoe.png` (App. I) | "m_p (ADR-0045, default OFF) and the ADR-0021 surveyed exit datum +-0.3 m (ADR-0046, replay-only)"; "ADR-0045's published x1.5 to 2.5" | "the Sellmeijer model factor m_p and the surveyed exit datum +-0.3 m"; "and x1.5 to 2.5 at the two informative matrix sections alone" |
| `adr0040_tilted_is_validation.png` (App. E) | "ADR-0029 is not contradicted ... a proposal optimised for one branch", with `--` as a dash | "The single-branch gain is not contradicted ... a tilt optimized for one branch" |
| `adr0029-tail-cov.png` (App. E) | "fm5 tail-variance study **[em dash]** KP58.8"; legend "tilted IS (ADR-0029)", "crude MC (debug fallback)" | "Tail-variance study: KP 58.8"; "tilted importance sampling", "crude Monte Carlo" |
| `adr0032_aquifer_response.png` (App. E) | "~1.5 h plateau (spec section 11)" | "~1.5 h plateau (flashy-river expectation)" |
| `adr0031-tail-lhs-vs-crude.png` and twin (App. E) | "fm5 tail-variance: LHS vs crude MC **[em dash]** ..."; x-label "P_f (transient) **[em dash]** deeper tail" | "Stratified against crude sampling, ..."; "P_f (transient), deeper tail" |

Three of those carried an **em dash** baked into the PNG, which the thesis
forbids unconditionally and which no source-level check could ever have seen.

Every replacement was checked against the figure's own caption so that the two
now use one vocabulary: "crude Monte Carlo" and "the tilted importance-sampling
estimator" are the caption's words for `adr0029-tail-cov`, "Stratified against
crude sampling at KP 58.8" is the caption's own title for the tail comparison,
and "the 1.5 hour plateau a flashy river would be expected to produce" is the
caption's gloss of the line that had cited the specification.

**Kept deliberately:** the pre-registered criterion tags R1, R2, F3, V2 and V4.
They are the study's own named criteria rather than pointers into the
repository, three main-body captions name them on purpose, and the audit's item
C already ruled on F3.

### 10.3 Item H: the DEM figure on the house style

`adr0047_dem_seepage_length.png` now calls `figstyle.style()` and draws from the
house palette. The geometry is untouched: the same 3 by 4 panel grid, the same
`figsize` and `dpi`, the same 2576 by 1540 canvas, every mark in the same data
position.

| Element | Was | Now |
|---|---|---|
| **fragility bars** | transient `#1f77b4` blue, static `#ff7f0e` orange | **static `STATIC` blue, transient `TRANSIENT` red** |
| bar legend | "trans", "static" | "transient", "static" |
| profile line | `#333333` | `INK` |
| riverside and landside toe | `#1f77b4` and `#d62728` | `BLUE` and `RED` |
| crest band | `#ffd27f` at 0.45 | `YELLOW` at 0.22 |
| clean and rejected stations | `#2ca02c` and `#999999` | `GREEN` and `MUTED` |
| DEM median, model value | `#2ca02c` and `#d62728` | `GREEN` and `RED` |
| station callout | `#d62728` bold | `INK_2` bold on a surface plate |
| legends | boxed | unframed, on a surface plate where they sit over marks |
| chrome | all four spines, `alpha=0.3` grid, white ground | top and right spines off, hairline solid grid, `SURFACE` ground |

**The colour swap is the substantive part.** The figure drew the transient
branch blue and the static branch orange, the reverse of the assignment
`_figstyle` fixes for the whole thesis and that every fragility figure in
Chapters 5 to 7 uses. A reader who had learned "blue is static" from the
results chapters was reading this Chapter 3 panel backwards. The values and
their labels were always correctly paired; only the hue was inverted.

Two house devices carried the unframing without losing legibility. The two
legends and the station callout sit over marks, so they take the same
surface-plate treatment `_figstyle.mark_hypothetical` uses for its own label: a
`SURFACE` patch at 0.85 alpha with no edge. That is a plate, not a frame, and
the `legend.frameon: False` rcParam stays in force.

Left alone, because they are notation rather than style and the audit's five
standards were scoped to the main body: `T.P.` as the datum label here against
`MSL` elsewhere (Chapter 3 is where the datum is established, so `T.P.` is
right there), and `max |dP_f| vs production` as an ASCII y-label.

### 10.4 Item I: the romanised Japanese term

The `r10_foreshore_exhaustion.png` x-label, "measured high-water-bed width B_f
[m] **(OYO kosuishiki-haba)**", now reads "**(OYO survey)**". The English
translation of the term is "high-water-bed width", which the label already
carried, so the bracket would have said the same thing twice; it names the
source instead. That is also the thesis's own usage: Chapter 8, Chapter 9 and
Appendix I all write "high-water-bed width" and none romanises it.

### 10.5 Pixel-diff evidence for the follow-up

All sixteen keep their exact dimensions.

| Figure | size | changed px | changed region |
|---|---:|---:|---|
| `adr0029-tail-cov.png` | 1120x736 | 1.705% | (186, 26, 1045, 172) |
| `adr0031-convergence-n-ladder.png` | 1152x800 | **0.000%** | untouched |
| `adr0031-convergence-n-ladder-kp60_0_matrix.png` | 1152x800 | **0.000%** | untouched |
| `adr0031-tail-lhs-vs-crude.png` | 1819x814 | 3.708% | (60, 16, 1802, 796) |
| `adr0031-tail-lhs-vs-crude-kp60_0_matrix.png` | 1819x814 | 3.457% | (60, 16, 1802, 796) |
| `adr0032_aquifer_response.png` | 1430x546 | 0.635% | (338, 55, 682, 124) |
| `adr0039-timestep-stress.png` | 2310x1672 | 0.185% | (158, 292, 661, 353) |
| `adr0040_tilted_is_validation.png` | 2367x974 | 0.794% | (160, 912, 2206, 932) |
| `adr0047_dem_seepage_length.png` | 2576x1540 | 99.999% | whole canvas (restyle) |
| `epistemic_knobs_mp_ztoe.png` | 2263x1318 | 1.370% | (18, 17, 2015, 543) |
| `fragility_comparison.png` | 2520x1120 | 0.248% | (569, 1004, 1418, 1024) |
| `fragility_per_section.png` | 2520x1639 | 0.170% | (569, 1525, 1418, 1545) |
| `fragility_tail_log.png` | 2520x1639 | 0.170% | (569, 1525, 1418, 1545) |
| `r10_foreshore_exhaustion.png` | 1840x736 | 0.464% | (169, 681, 848, 700) |
| `stage6_6_heq_kp57_4.png` | 1224x714 | 0.679% | (350, 25, 963, 49) |
| `stage6_6_heq_kp62_0.png` | 1224x714 | 0.700% | (350, 25, 963, 49) |

Every extent but the DEM figure's is the strip of text that was edited, and
nothing else. The DEM figure changes on every pixel because the ground colour
moves from white to `SURFACE`; its marks are unmoved, which the unchanged
canvas and a panel-by-panel read confirm. The two
`adr0031-convergence-n-ladder` figures come from the same driver as the tail
figures and are in the table to show they were re-rendered and did not move.

**Two re-render paths were proved for the first time here.** `figure_heq_bound`
touches only `result.conditioning_grid`, so it redraws from `components.levels`
in the persisted analysis record through a two-field stand-in; that the diff is
confined to the title strip is the proof the grid was reconstructed exactly.
`aquifer_response_diagnostic.py` has no persisted record and recomputes, so it
was run unedited first: the output came back byte-identical to the committed
PNG, which is what licensed the re-render.

### 10.6 The document is still unmoved

Isolated build, same method, after all sixteen figures were copied across.

| Gate | Expected | Measured |
|---|---|---|
| undefined references | 0 | **0** |
| undefined citations | 0 | **0** |
| multiply-defined labels | 0 | **0** |
| citation keys | 106 | **106** |
| labels | 387 | **387** |
| main body pages | 99 | **99** |
| References begins on | 100 | **100** |
| per-chapter map | 6, 10, 12, 12, 11, 18, 12, 11, 7 | **identical** |
| appendices A to K | 7, 8, 7, 3, 12, 4, 5, 13, 5, 7, 3 = 74 | **identical** |
| total pages | 193 | **193** |
| overfull hboxes | 12 or fewer | **12** |
| worst overfull | 15.4 pt or less | **15.386 pt** |

`ruff check .` clean, `black --check .` clean, `pytest -m "not slow"` 903
passed, 7 deselected. No thesis prose changed in this pass: the follow-up is
figures only.

---

## 11. Addendum, 2026-09-04: the two items section 10.3 left alone are closed

The author commissioned both after the submission gate of that date
(`msc-thesis/scratch/SUBMISSION_GATE_2026-09-04.md`, findings 3 and 12). Both
were flagged here as notation rather than style and deliberately deferred; both
are now fixed at source, in the drivers, and every affected figure re-rendered
from its persisted artifact.

**The datum label is unified on `m T.P.`** Section 10.3 recorded the split as
"`T.P.` as the datum label here against `MSL` elsewhere". The thesis unified its
running text on `m~T.P.` at 23 sites and the figures were the only place `MSL`
survived, so a reader met "46.39 m T.P." in an equation and "46.39 m MSL" in the
figure above it. Twenty-nine `set_xlabel` / `set_ylabel` strings and eleven
annotation or title strings now read `m T.P.`, across thirteen drivers plus
`bayesian_reliability_updating/plots.py`. **Only figure-visible strings were
touched:** the dict keys (`level_m_msl`, `max_abs_delta_at_stage_m_msl`), the
CLI help, the generated configs, the ADR text and the engine's own markdown
reports keep `MSL`, which is what ADR-0021 calls the datum. Thirty-six tracked
figures changed; every other figure re-rendered byte-identical, which is the
evidence that the edit was confined to the label.

**The ASCII `max |dP_f| vs production` y-label is typeset.**
`dem_cross_section_study.py` now writes `r"max $|\Delta P_f|$ vs production"`.

**Two claim corrections travelled with the re-render**, both in
`hwl_bias_resolution.py`'s `epistemic_vs_statistical.png`:

- The title read **"The epistemic band is 6 to 9x the statistical interval"**
  with the letter `x`. It now reads "6.4 to 7.2 times". The **numbers**, not
  only the multiplication sign, were the defect: the figure's own three
  annotations are 6.4x, 7.2x and 6.9x, and recomputing from
  `adr0040-hwl-bias-resolution.json` reproduces them exactly as
  band / CI = 10.49/1.630, 9.67/1.341 and 8.15/1.186 over the arms that meet
  R1 and R2. **The 9 admits the arms below the thirty-row floor**, which this
  study discards elsewhere on the same ground. See the ADR addendum.
- Provenance for anyone re-deriving it: the resolved arms at KP 62.0's design
  HWL are `k_aq_regional_upper` 2.59 (191 600 rows), `z_toe_minus0.30m` 13.87
  (901), `gamma_bl_sub_lower` 26.92 (63) and `m_p` 27.20 (150).

**Verification, thesis side.** Isolated XeLaTeX build: 0 undefined references,
0 undefined citations, 0 multiply-defined labels, 106 citation keys, 193 pages,
main body 99 with References on 100, and a chapter-for-chapter and
appendix-for-appendix page map identical to the pre-fix build with all 110
section entries on their own pages. Overfull hboxes fall 12 to 11.

**Verification, engine side.** `ruff check .` and `black --check .` clean. The
Phase 2 redraw reproduced its rejection fractions exactly, 5.67 and 3.36 per
cent, so no physics moved. No `Config` default, physics module, config, CSV,
persisted sweep or evidence file was touched.
