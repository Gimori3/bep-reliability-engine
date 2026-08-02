# Numbers awaiting a home in the thesis — manifest for the chapter-drafting step

**Date:** 2026-07-30. Companion to `docs/number_audit_2026-07-30.md`.

**Why this exists.** msc-thesis **Chapter 6** (`Results: Subsurface Piping
Assessment`, file `mainmatter/5. Results of the System Integration and Climate
Sensitivity Analysis.tex`) and **Chapter 7** (`Results: System Integration and
Climate Sensitivity`, file `mainmatter/6. Results of the System Integration and
Climate Sensitivity.tex`) are section skeletons of **84 and 73 words** — four
`\section` headings each, no body text. The number audit therefore found no stale
copies in them. That is a **gap, not a clean bill of health**: every headline this
project has produced about *results* has no home yet.

**This is a manifest, not a draft.** Neither chapter is drafted here.

**How to read the columns.** *Chapter / section* names the existing `\label` the
number belongs under, so a drafter can place it without re-deciding the structure.
*Figure* says whether a figure already exists (all paths relative to
`d:\repositories\bep-reliability-engine\docs\figures\`; the thesis repo's own
`figures/` directory would need the file copied in, or the path pointed at it).

**Count: 47 numbers or number-groups awaiting a home**, of which **29 already have
a figure** and **18 do not**.

> **Addendum, 2026-07-31 -- the five named figure gaps are closed, and this
> header's arithmetic is corrected.** Ten rows gained a figure: 2.5, 2.13, 4.1,
> 4.2, 5.2, 5.4, 6.10, 7.1, 7.15 and 7.16. See the closing section for what was
> built.
>
> The "47 / 29 / 18" above **does not reconcile with a row-by-row parse** and is
> superseded. Parsing this file mechanically (`^\| \d+\.\d+ \|`) gives **74
> numbered rows**: before 2026-07-31, **45 with a figure, 24 without**, plus 3
> `n/a` and 2 already-current. After this pass: **55 with a figure, 14 without**.
> So **14 figure-less entries remain**, not 8 -- the smaller number would follow
> only from the header's own count, which no parse reproduces. The remaining 14
> are 1.3, 2.6, 4.6, 4.7, 4.8, 4.9, 4.10, 5.3, 6.12, 7.6, 7.8, 7.12, 7.13 and
> 8.3. The 47/29/18 line is left in place rather than rewritten, because it is
> what the 2026-07-30 pass recorded; this addendum is authoritative where they
> differ.

> **Addendum, 2026-08-02 -- the four gaps the approved thesis plan named are
> closed.** `msc-thesis/scratch/THESIS_PLAN_2026-08-01.md` section 3.4 carried
> rows 4.3, 4.4, 4.7 and 5.1 forward as a dependency on this repository that the
> plan could not resolve itself. All four now have a tracked publication figure.
>
> * **4.3, 4.4 and 5.1** were marked *yes* here but their figures existed only
>   under **gitignored** `results/phase2/figures/`, so they were not tracked, not
>   gated by G7, and would not have survived a fresh clone into the thesis. Four
>   of the 44 are now promoted by a dual-write seam inside the Phase 2 package
>   (`bayesian_reliability_updating.pipeline.PUBLICATION_FIGURES`); see the
>   closing section for what was selected and why.
> * **4.7** had no figure anywhere and now has `phase2_peak_shortcut.png`.
>
> Re-parsing mechanically as above: **74 numbered rows, 56 with a figure, 13
> without**, plus 3 `n/a` and 2 already-current. Only 4.7 moves the count -- the
> other three were already counted as having one. **13 figure-less entries
> remain**: 1.3, 2.6, 4.6, 4.8, 4.9, 4.10, 5.3, 6.12, 7.6, 7.8, 7.12, 7.13 and
> 8.3. Gate G7 coverage rose **57 of 57 to 62 of 62**, still 0 stale (61
> staleness-gated plus the one recorded ADR-0032 waiver).

---

## 1. Prior BEP fragility, static versus transient (Ch. 6 §1)

`\label{sec: Prior BEP Fragility Curves: Static vs. Transient Comparison}`

| # | number | source artifact | figure |
|---|---|---|---|
| 1.1 | The four prior fragility curve pairs, raw MC points with 95 % Clopper-Pearson bands plus the fitted lognormal deliverables | `results/tokachi_kp*_historical_matrix.h5` + sidecars | **yes** — `fragility_per_section.png` |
| 1.2 | All four matrix transients are ADR-0024 `fitted_lognormal` with the transition bracketed (KP 62.0 included, max raw P_f 0.9901) | sidecar `metadata['fragility_deliverable']` | **yes** (same) |
| 1.3 | The bulk-d70 co-primary curves, and the ~5 to 15x reduction in BEP-driven numbers | `results/tokachi_kp*_historical_bulk.h5` | **no** |
| 1.4 | Common load-excess presentation on `h - z_toe` (the ADR-0024 fit datum) | same | **yes** — `fragility_comparison.png` |
| 1.5 | Tail behaviour and per-level static/transient ratios on a log axis | same | **yes** — `fragility_tail_log.png` |
| 1.6 | KP 62.0's above-crest grid extension is a hypothetical fit stabiliser (51.0 to 56.5 m MSL, `attainable_max_m` = 50.5 m) and must never be plotted or read as attainable | `configs/kp62_0_historical_matrix.yaml`, `stage6_6_kp62_0_analysis.json` | **yes** (shaded in 1.1, 1.4, 1.5) |
| 1.7 | Spec §11 Monte Carlo CoV per level, and the < 5 % target met down to per-level transient P_f ≈ 5e-3 | sidecar `metadata['mc_convergence']`; ADR-0031 | **yes** — `adr0031-convergence-n-ladder*.png` |

## 2. The static-transient gap and its decomposition (Ch. 6 §2)

`\label{sec: Quantifying Scenario-Dependent Biases: Isolated vs. Compound Events}`

This is where the resolved design-HWL bias belongs. **ADR-0040's companion note
§3.3 already supplies the two sentences ready to drop in** — use them verbatim
rather than re-deriving.

| # | number | source artifact | figure |
|---|---|---|---|
| 2.1 | **KP 62.0 design-HWL bias B = 26.9, 95 % CI [21.6, 35.3], on 63 failing transient rows out of 1e6, at 46.39 m MSL — RESOLVED** | `adr0040-hwl-bias-resolution.json` `stages.A_brute_kp62_0.anchor_A1` | **yes** — `adr0040_hwl_bias_resolved.png` |
| 2.2 | The nearest grid level A2 = 46.50 m gives **21.6 [18.8, 25.2] on 176 rows**. A1 and A2 are different levels and must never be quoted as one another | same, `anchor_A2` | **yes** (same, zoom panel) |
| 2.3 | The bias is **stage-specific at the decimetre scale**: paired ρ = 1.249 [1.039, 1.556], resolved — 25 % larger 11 cm lower. No figure of B may be quoted without its stage | same, `A_anchors_F2` | **yes** (same) |
| 2.4 | **The N = 1e5 figure 44.7 on 4 rows was counting noise that overstated the bias 1.66x.** Statistically consistent (G-A3 passed 59/59) | same | **yes** (same, both N drawn together) |
| 2.5 | **KP 57.4 is unresolvable by brute force at N = 1e6** (2 rows at A1): report the Clopper-Pearson bound **B ≥ 148** and lead with the resolved anchor **42.7 [39.4, 46.6] at 39.50 m MSL** on 521 rows | same, `A_brute_kp57_4` | **yes** (2026-07-31) -- `adr0040_kp57_4_bound.png` |
| 2.6 | Reaching R1's 30 rows at KP 57.4's A1 would need N ≈ 1.5e7, about 40 h of the same compute | same | **no** |
| 2.7 | The bias decays with stage: KP 62.0 21.6 at 46.50, **10.5** at 47.0, 6.3 at 47.5, 2.4 at 49.0, 1.4 at 50.5 | `stage6_6_kp62_0_analysis.json` | **yes** — `stage6_6_ladder_kp62_0.png` |
| 2.8 | Component attribution: temporal-dominated through the shoulder (58 to 76 % of the production gap; pure temporal C3/C4 ≈ 2 to 8), head-convention-dominated in the design tail (85 to 97 %, exactly 0.3·D_bl) | `stage6_6_kp*_analysis.json` `components` | **yes** — `stage6_6_waterfall_*.png`, `stage6_6_fractions_*.png` |
| 2.9 | The initiation gate is immaterial to the production gap (binds only at KP 57.4 under α = −1/2) | same | **yes** — `stage6_6_fractions_*.png` |
| 2.10 | ADR-0009's H_eq conservatism closed at the indicator level: **+10 to 25 % of transient P_f** (the ≈1.95x rate factor compresses) | same | **yes** — `stage6_6_heq_*.png` |
| 2.11 | The dimensional component is **−0.5 under matrix d70 but sign-flips to +0.4 under bulk** (the F_s scale group crosses unity); Shapley interaction up to +0.14, so component magnitudes are order-conditional | same + `*_bulk_analysis.json` | **yes** — `stage6_6_waterfall_*.png` |
| 2.12 | The sustained-peak analytic limit is exact (ODE-verified to zero disagreements at 64 d holds) and all Euler-flip counts are 0 **at N = 1e5** | `stage6_6_kp*.h5` `flip_counts` | **yes** — `stage6_6_c2c3_*.png` |
| 2.13 | **New numerical finding:** at N = 1e6 KP 57.4 carries 4 barrier-jump rows (39.50 / 40.25 / 40.75 m), none at either design-HWL anchor; expected count at N = 1e5 is 0.4. The recommended 39.50 m anchor **is itself a flip level** (1 row in 521, biasing 42.7 down ~0.2 %, conservative) | `adr0040-hwl-bias-resolution.json` `A_brute_kp57_4.euler_flips` | **yes** (2026-07-31) -- `adr0040_kp57_4_bound.png`, flip levels drawn as carets on the row-count strip |
| 2.14 | The pre-ADR-0047 KP 62.0 bias values ("~21x", 44.7) and the KP 57.4 "at least 32" must not appear as current | audit §A | n/a |

## 3. Sampling and estimator methodology for the gap (Ch. 6 §2, or Ch. 5 §"Sampling Strategy in the Failure Tail")

| # | number | source artifact | figure |
|---|---|---|---|
| 3.1 | **The ADR-0029 tilted sampler failed its pre-registered validation for this estimand**: V1 pass, V2 fail (46.75 m disagrees resolvably, 25 % low), V3 pass, V4 fail (Kish n_eff 86.9 < 200) | `adr0040-hwl-bias-resolution.json` `B_tilt_kp62_0.validation` | **yes** — `adr0040_tilted_is_validation.png` |
| 3.2 | The transient-side gain is real, **4.66x** CoV reduction, at the favourable end of ADR-0029's measured 3.2 to 4.1x | same, `V4_detail` | **yes** (same) |
| 3.3 | A transient-optimised tilt **inflates the static estimator 1.50x at the anchor rising to 940x at saturation**; static n_eff plateaus near 104 | same, `static_branch_cost_under_transient_tilt` | **yes** (same) |
| 3.4 | The CE shift is ν = {k_aq 3.168, C_e 0.897} — at the design water level the transient failure region is reached overwhelmingly through extreme conductivity, barely through C_e | same, `ce_shift` | **yes** (same, in the panel title) |
| 3.5 | **Scope, load-bearing:** ADR-0029 is not contradicted. The sampler remains valid for a single-branch tail P_f and is not valid for a **ratio between branches** | `decisions/0029-...tail-estimator.md` amendment; `architecture.md` failure mode 5 | **yes** (same, footnote) |
| 3.6 | Brute force was used for every headline; no weighted number enters any published figure | same | n/a |

## 4. Posterior parameter distributions after Bayesian updating (Ch. 6 §3)

`\label{sec: Posterior Parameter Distributions after Bayesian Updating}`

| # | number | source artifact | figure |
|---|---|---|---|
| 4.1 | **Per-stratum rejection table at production N**: matrix KP57.4 0.065 % / KP58.8 5.673 % / KP60.0 3.363 % / KP62.0 0.000 %; bulk 0 / 0 / 0.023 % / 0 | `phase2-survival-update-per-stratum.json` (committed slice of `production_campaign_manifest.json`) | **yes** (2026-07-31) -- `phase2_survival_update.png`, table source `phase2-survival-update-per-stratum.csv` |
| 4.2 | **Marginal transient rejection exactly 0 in all eight strata** (and in all 16 runs including both documented variants): the transient failure set is nested in the static one under the real 2016 loading | same | **yes** (same; the transient bar is drawn inside the static one and the marginal is a column of exact zeros) |
| 4.3 | Posterior means: C_e −4 %, k_aq −3 to −4 % at the informative sections; induced Spearman(k_aq, C_e) ≈ −0.05 | `results/phase2/*_posterior.json` `analysis` | **yes** (2026-08-02) -- `phase2_marginals_kp58_8_matrix.png`, `phase2_marginals_kp60_0_matrix.png` (tracked; promoted by the `pipeline.PUBLICATION_FIGURES` dual-write seam) |
| 4.4 | C_e headline at KP 58.8: prior mean 0.0550 → posterior 0.0528 (ratio 0.959) | same | **yes** (same; the C_e panel carries both mean lines) |
| 4.5 | **L is barely moved** (mean +0.5 to 1.4 %, CoV −1.7 to 3.6 %), so the ST_L ≈ 0.49 to 0.78 total-effect share is **irreducible by a θ-only Accept-Reject filter** | `decisions/seepage-length-L-study.md` §3 | **yes** — `seepage_length_system_and_ceiling.png` |
| 4.6 | The informative updates land at KP 58.8 and KP 60.0; KP 62.0 and KP 57.4 are near-vacuous — **the inverse of the thesis's tiering narrative**, because the engine evaluates the unremediated foundation | `phase2_report.md` §11 | **no** |
| 4.7 | The WBI+ peak-only shortcut over-rejects by **2.75 to 3.9x**, so the full-transient replay is load-bearing | `phase2-peak-shortcut.json` (committed slice of the 8 sweeps + 8 posteriors), stated in `phase2_report.md` §11.1 | **yes** (2026-08-02) -- `phase2_peak_shortcut.png`, table source `phase2-peak-shortcut.csv` |
| 4.8 | Anchor-construction bracket: KP57.4 0.00 %, KP58.8 10.81 %, KP60.0 0.34 %, **KP62.0 0.05 %** | `phase2_anchor_rating.per_stratum` | **no** |
| 4.9 | Strict no-initiation reading: 66.4 % / 99.57 % / 99.30 % / **39.55 %**; only KP 62.0 keeps a usable posterior (60 448 rows), so the initiation and progression margins separate cleanly at the governing section | `phase2_no_initiation.per_stratum` | **no** |
| 4.10 | Event set is **closed at 2016** (ADR-0044): the 2011 marginal beyond 2016 is bounded at 0.316 %, and 2006 has nothing constructible | `decisions/adr0044-event-closure-bound.json` | **no** |

## 5. Posterior BEP fragility (Ch. 6 §4)

`\label{sec: Posterior BEP Fragility Curves: The Effect of Historical Calibration}`

| # | number | source artifact | figure |
|---|---|---|---|
| 5.1 | Posterior versus prior fragility per section; the shift is modest and concentrated at KP 58.8 / KP 60.0 | `results/phase2/*_posterior.h5` | **yes** (2026-08-02) -- `phase2_fragility_update_kp58_8_matrix.png`, `phase2_fragility_update_kp60_0_matrix.png` (tracked; the *concentration* half of this claim is carried across all eight strata by `phase2_survival_update.png`) |
| 5.2 | Masked-retained-matrices default versus exact re-evaluation verification: **exact at all eight strata**, zero flag mismatches | same slice, `flag_mismatch_*` | **yes** (same; annotated on the figure) |
| 5.3 | The KP 62.0 adoption raised transient P_f **x8.7 at design HWL** (1.5e-4 → 1.3e-3) and x3.2 at design crest, and the nesting result still held — so it was re-established, not assumed | `phase2_report.md` §14 | **no** |
| 5.4 | Propagation to the system level: the 2016 constraint lowers the annual system number **12.4 % at KP 58.8 historical** and **11.0 % at KP 60.0 historical** (8.3 % / 7.6 % under +4K), and < 0.3 % at KP 57.4 and KP 62.0. **Correction, 2026-07-31:** the *< 2 % elsewhere* written here originally is wrong -- KP 60.0 is the second informative section and moves almost as much as KP 58.8. Measured in `rq4-sensitivity-brackets.csv`, `prior_bep` arm | `phase3-sensitivity-brackets.json` (committed slice of `rq4_annual.csv`) | **yes** (2026-07-31) -- `rq4_sensitivity_brackets.png` |

## 6. System integration and climate sensitivity (Ch. 7, all four sections)

**Owner decision 5 of the 2026-07-29 campaign scopes RQ3 and RQ4 to the four
geotechnically characterised sections.** The 114-segment distribution is **reach
context**, because 110 of 114 segments carry `bep_source = None` under the
production `exact` policy and are surface-only lower bounds. Any draft must keep
that distinction.

| # | number | chapter section | source artifact | figure |
|---|---|---|---|---|
| 6.1 | **RQ4 headline: annual system P_f historical → +4K at the four sections** — 7.53e-4 → 9.53e-3 (KP57.4), 7.42e-3 → 4.09e-2 (KP58.8), 1.80e-3 → 1.42e-2 (KP60.0), 1.01e-3 → 1.28e-2 (KP62.0) | §1 and §3 | `rq4_annual.csv` | **yes** — `phase3_rq4_four_sections.png` |
| 6.2 | **Climate ratios 12.7 / 5.5 / 7.9 / 12.7** | §4 | same | **yes** (same) |
| 6.3 | **RQ3 dominance: BEP carries 81 to 100 % of summed annual contributions historically** (1.000 / 0.974 / 1.000 / 0.812) | §2 | same | **yes** — `phase3_dominance_profile.png` |
| 6.4 | Under +4K **BEP leads at 3 of 4 sections** (0.912 / 0.941 / 0.998) with **KP 62.0 level at 0.500/0.500 — overflow no longer leads anywhere** | §4 | same | **yes** (same) |
| 6.5 | **Fluvial scour is exactly zero at all 114 segments** under the dimensionally-correct USACE conversion (ADR-0042 dec. 9); the as-received `scour_script_k` companion would add ≤ 8 % at the BEP sections and dominate ~70 surface-only segments | §2 | `rq4_annual.csv`, `rq3_sections_*.json` | **yes** — `phase3_dominance_profile.png` |
| 6.6 | The composed conditional three-mechanism system fragility at the four sections | §1, §3 | `rq3_segment_curves_matrix_posterior.json` | **yes** — `phase3_system_fragility_bep_sections.png` |
| 6.7 | Reach context: median annual system P_f 0 → 3.67e-4, mean 1.08e-4 → 1.92e-3 (~18x), segments > 1e-3/yr **3 → 45** of 114, > 1e-2/yr 0 → 4 | §4 | `rq4_annual.csv` | **yes** — `phase3_climate_shift.png` (captioned reach context) |
| 6.8 | The basin's worst segment in both climates is BEP-driven **KP 58.8**, and its Uemura section (Tokachi 4 = KP 58.0) governs the basin | §2, §4 | `rq3_sections_matrix_posterior.json` | **yes** — `phase3_dominance_profile.png` |
| 6.9 | **The climate signal enters through duration**: risk concentrates ~100 to 400x in years with > 24 h above the toe, and the frequency of such years roughly triples under +4K | §4 | `rq4_attribution.json` | **yes** — `phase3_rq4_attribution.png` |
| 6.10 | Sensitivity brackets at the four sections: λ_ac = 40 m **x1.6 to 3.4**; bulk d70 cuts BEP-driven numbers **~5 to 15x**; posterior − prior −12 % at KP 58.8 | §1, §3 | `phase3-sensitivity-brackets.json` (committed slice of `rq4_annual.csv`) | **yes** (2026-07-31) -- `rq4_sensitivity_brackets.png`, table source `rq4-sensitivity-brackets.csv`. The measured λ_ac = 40 m factors on the annual *system* number are **1.93 to 3.37**; the bulk d70 factor spans 1.5x to 363x because it hits its floor wherever the historical number does |
| 6.11 | Event-based validation: overflow agrees with the curves within tens of %, scour zero both ways, +4K overflow within ~20 % of Uemura WP2 Table 4 at KP 56.4/58.0 — but **their erosion-dominance headline does not reproduce** | §2 | `event_based_validation.json` | **yes** — `phase3_event_based_validation.png` |
| 6.12 | Coverage diagnostics: `bep_clamped_above_grid` fires on **16 KP57.4/58.8 bulk rows only** and is False in every KP 62.0 row — the "KP 62.0 clamped lower bound" caveat is **withdrawn**, not merely superseded | §1 | `rq4_annual.csv`; `phase3_report.md` §11.3 | **no** |

## 7. The epistemic bracket ranking (Ch. 5 extension, and a caveat on every Ch. 6 / Ch. 7 number)

Chapter 5 §"The Aquifer Conductivity Prior under Scrutiny" currently reports
**KP 58.8 and KP 60.0 only**. The 2026-07-30 synthesis extended all three
companions to **all four matrix sections**, and the new numbers land at the
governing section.

| # | number | source artifact | figure |
|---|---|---|---|
| 7.1 | **The one ranking table**: 6 epistemic brackets plus the 2 statistical yardsticks, x 5 anchors x 4 sections, as a comparable multiplicative span | `epistemic-bracket-synthesis.json` `sections[].brackets` | **yes** (2026-07-31) -- `epistemic_bracket_ranking.png`; full 160-row table source `epistemic-bracket-ranking.csv` |
| 7.2 | **k_aq is the largest knob at every section and every anchor** — x6.65e3 at the KP 62.0 transition midpoint against a Clopper-Pearson span of 1.01 | same | **yes** — `epistemic_vs_statistical.png` |
| 7.3 | **New: at KP 62.0's design HWL, z_toe is the second-largest knob (x184), ahead of L (x15)** — the anchor sits 0.11 m above HWL on 15 failing rows, so ±0.3 m of datum moves the section across its own threshold. ADR-0046 had never measured KP 62.0 | same | **yes** (same) |
| 7.4 | Property (b) **holds for k_aq only**: at KP 62.0 design HWL the entire m_p bracket (2.80) is **narrower** than the Clopper-Pearson band (2.95) and the MC-CoV band (3.05). "Epistemic dwarfs sampling noise" must not be generalised | same | **yes** (same, right panel) |
| 7.5 | **Property (c) REFUTED at all four sections**: max resolved ratio-of-ratios departure **x82 / x66 / x163 / x46** for `field_geomean` — larger than the L bracket's own non-cancellation | same | **yes** (same) |
| 7.6 | Normalised, non-cancellation is section-independent at **1.1 to 1.8 decades of ρ per decade of k_aq** — > 1 everywhere, i.e. the ratio **amplifies**. The raw ordering is an artifact of unequal shift size (a pre-registered prediction reported as **not confirmed**) | same | **no** |
| 7.7 | The surviving rule: **a bracket cancels only if it is pure common-mode**; m_p alone qualifies, by ADR-0045 §2 construction. Measure per knob, never assume | same | already in Ch. 7 §"Not Every Epistemic Knob Cancels in a Ratio" — **current** |
| 7.8 | Production's position: **55.1 % of the log-k_aq input range at KP 62.0 but only 26.5 % in P_f space at design HWL** — upside x1800 if the regional upper band is right, x0.067 if the field population is. KP 62.0-specific (KP 58.8 gives 72.6 %, upside x3.49) | same | **no** |
| 7.9 | **Stage D at the anchor**: the epistemic band on B is **6 to 9x the statistical interval** (14.7x or 10.5x against 1.63x). Criterion F3 **does not fire at KP 62.0 (9.0 vs 10) but FIRES at KP 57.4** (unbounded — field-k_aq gives static failures with zero transient failures) | `adr0040-hwl-bias-resolution.json` `D_epistemic` | **yes** — `epistemic_vs_statistical.png` |
| 7.10 | At the anchor: `k_aq_regional_upper` collapses B from 26.9 to **2.59** (ρ = 0.096, resolved); `z_toe_minus0.30m` to **13.9** (ρ = 0.515, resolved); **m_p cancels** (ρ = 1.010); `gamma_bl_sub` **exactly 1.000** | same | **yes** (same) |
| 7.11 | `k_aq_field_geomean` at the anchor is **indeterminate, not unbounded** — both branches produce zero failures in 1e6, so B is 0/0 | same | **yes** (same, arm omitted with the footnote) |
| 7.12 | The m_p negative control is **monotone in row count**: passes at all three anchors with ≥ 63 rows (1.010 / 0.925 / 0.901), fails at the two with ≤ 10 rows (1.550 / 1.707), whose arm results were **discarded** | same, `mp_control` | **no** |
| 7.13 | ADR-0028's static/gate separation reconfirmed as a by-product: `gamma_bl_sub` moves the static branch by **exactly 1.000 at all 98 levels**, 4/4 sections | `epistemic-bracket-synthesis.json` | **no** |
| 7.14 | Two shoulders, not one: ADR-0045 quotes m_p at the rising limb (P_f ≈ 2e-3), ADR-0048 quotes k_aq at the transition midpoint (P_f ≈ 0.5). Never use the bare word "shoulder" | `epistemic-bracket-synthesis.md` §2.2 | already fixed in Ch. 5 `tab:kaq_scenarios` — **current** |
| 7.15 | The **Sellmeijer model factor m_p** companion (ADR-0045): static shoulder x2.2 to 2.4 (deep tail x5 to 6), transient shoulder x1.5 to 2.5, ±2 % above the transition. **Not in the thesis at all** | `adr0045-mp-companion.json` | **yes** (2026-07-31) -- `epistemic_knobs_mp_ztoe.png` panels A and B. The figure quotes values measured at named anchors over all four sections (static x3.0 to 6.0 at the deepest reachable level, x1.3 to 1.7 at the rising limb; transient maxima x1.6 to 2.8), because ADR-0045's headline is a two-section number at its own stage -- see 7.14 |
| 7.16 | The **z_toe ±0.3 m** companion (ADR-0046) at all four sections | `adr0046-ztoe-companion.json` | **yes** (2026-07-31) -- `epistemic_knobs_mp_ztoe.png` panels C and D, with KP 62.0's x184 span at its design-level anchor marked. Table source `epistemic-knobs-mp-ztoe.csv` |
| 7.17 | Every absolute P_f in Ch. 6 and Ch. 7 must carry the k_aq bracket; every *ratio* must be labelled **k_aq-conditional and L-conditional**, k_aq being the larger | audit §D | n/a |

## 8. ADR-0024 deliverable forms (Ch. 6 §1, methodological note)

| # | number | source artifact | figure |
|---|---|---|---|
| 8.1 | All four matrix sections are `fitted_lognormal` on **both** branches (campaign G5); `fit_role` = `deliverable` | sidecar `metadata['fragility_deliverable']` | **yes** — `fragility_per_section.png` |
| 8.2 | Raw-tail-with-Clopper-Pearson is the **intended primary presentation** where the transition is unreachable, not a fallback | ADR-0024 | **yes** (same) |
| 8.3 | `bootstrap_degenerate_replicates` = 0 in every run | sidecar | **no** |
| 8.4 | The KP 62.0 above-crest extension exists to stabilise the fit and **is never attainable** | see 1.6 | **yes** |

---

## Figure gaps worth closing before the chapters are written

Eighteen entries have no figure. The five with the highest ratio of thesis value to
effort:

1. **The Phase 2 per-stratum rejection table with the marginal-transient-zero
   result** (4.1, 4.2, 5.2) — a small table, currently existing only as manifest
   JSON. This is the central Bayesian claim of the thesis.
2. **The epistemic ranking table** (7.1) — 7 brackets x 4 sections at two anchors,
   as spans. `epistemic-bracket-synthesis.json` holds it whole; it needs formatting,
   not computing.
3. **KP 57.4's bound and its resolved anchor** (2.5) — the contrast section's whole
   story is one panel: B against stage with the two unresolved anchors marked and
   the 39.50 m anchor labelled with its 1-row flip caveat.
4. **The sensitivity-bracket panel at the four sections** (6.10) — λ_ac, d70 and
   prior-vs-posterior side by side; `rq4_annual.csv` already carries every arm.
5. **The m_p and z_toe companion curves** (7.15, 7.16) — the only two accepted
   epistemic knobs with no figure anywhere.

The Phase 2 diagnostic figures (4.3, 4.4, 5.1) exist under gitignored
`results/phase2/figures/` and would need a tracked publication copy; the Phase 2
CLI's new `--figures-only` flag regenerates them from the persisted posterior
without touching it.

---

## What was built, 2026-07-31

All five are produced by `scripts/thesis_figure_gaps.py` (`extract` then
`figures`, or `all`), declared in gate G7's `FIGURE_DRIVERS` by exact name, and
guarded by `tests/test_thesis_figure_gaps.py`.

| # | inventory rows | figure | table source (CSV, `docs/decisions/`) |
|---|---|---|---|
| 1 | 4.1, 4.2, 5.2 | `phase2_survival_update.png` | `phase2-survival-update-per-stratum.csv` |
| 2 | 7.1 | `epistemic_bracket_ranking.png` | `epistemic-bracket-ranking.csv` |
| 3 | 2.5, 2.13 | `adr0040_kp57_4_bound.png` | `adr0040-kp57_4-bias-bound.csv` |
| 4 | 6.10, 5.4 | `rq4_sensitivity_brackets.png` | `rq4-sensitivity-brackets.csv` |
| 5 | 7.15, 7.16 | `epistemic_knobs_mp_ztoe.png` | `epistemic-knobs-mp-ztoe.csv` |

**Two committed evidence slices were cut**, because figures 1 and 4 were sourced
only from gitignored artifacts and so would not have regenerated on a fresh
clone:

* `docs/decisions/phase2-survival-update-per-stratum.json` -- the 16 Phase 2 runs
  out of `results/production_campaign_manifest.json`;
* `docs/decisions/phase3-sensitivity-brackets.json` -- the 40 BEP-section rows out
  of `results/system_integration/phase3/rq4_annual.csv`.

Each records the source path and its **SHA-256**, and a test compares that digest
against the live artifact whenever the artifact is present, so the chain from
campaign run to committed slice to figure is checkable rather than asserted. Both
are rewritten by `thesis_figure_gaps.py extract`.

**One correction the figures forced**, recorded at row 5.4: the *"< 2 %
elsewhere"* written on 2026-07-30 is wrong. KP 60.0 historical drops **11.0 %**,
almost as much as KP 58.8's 12.4 % -- both are informative sections, and only
KP 57.4 and KP 62.0 are near-vacuous (< 0.3 %).

**Not done, and why.** Rows 4.3, 4.4 and 5.1 were *not* promoted. Their figures
are written by `bayesian_reliability_updating.pipeline._figures` into a single
`out_dir / "figures"`; there is no dual-write seam, so promoting them means
editing a shipped Phase 2 module rather than copying a file, and the two named
kinds alone are 16 files (44 in the directory). That is a change to a package
whose persisted posteriors are SHA-256-recorded in the campaign manifest, and it
was left for a separate decision rather than folded into a figure pass. A manual
copy is not an option: `docs/conventions.md` section 9.3 exists because a human
copying figures between `results/` and `docs/figures/` is the failure the
dual-write replaced.

---

## What was built, 2026-08-02

The separate decision the paragraph above left open was taken. All four rows the
approved thesis plan (section 3.4) named are closed.

### The Phase 2 dual-write seam (rows 4.3, 4.4, 5.1)

`bayesian_reliability_updating.plots._save` gained an optional
`publication_path`, and `pipeline._figures` passes one for the promoted figures,
so **both copies come from one figure object in one call** -- the pattern
`stage6_6_gap_decomposition._write_figure` and `plot_fragility_curves.save_both`
already use. `publication_path=None` is the default everywhere else and is
bit-identical to the pre-seam behaviour.

**Four of the 44 files are promoted**, listed in `pipeline.PUBLICATION_FIGURES`:

| tracked figure | inventory | kind |
|---|---|---|
| `phase2_marginals_kp58_8_matrix.png` | 4.3, 4.4 | prior versus posterior marginals |
| `phase2_marginals_kp60_0_matrix.png` | 4.3 | same |
| `phase2_fragility_update_kp58_8_matrix.png` | 5.1 | prior versus posterior fragility |
| `phase2_fragility_update_kp60_0_matrix.png` | 5.1 | same |

Why those four and no others:

* **Only two kinds.** The thesis asks for the posterior parameter shift and the
  prior-to-posterior fragility shift. `decomposition`, `rejection_scatter`,
  `record` and `breach_times` are run-local diagnostics and stay that way.
* **Only KP 58.8 and KP 60.0 matrix**, the two informative strata (transient
  rejection 5.67 % and 3.36 % against <= 0.07 % everywhere else,
  `phase2_report.md` section 11.1). Every number rows 4.3, 4.4 and 5.1 quote is
  measured at exactly these two. Row 5.1 also claims the shift is *concentrated*
  there, and that half is carried across all eight strata by
  `phase2_survival_update.png`, so a near-null pair at KP 57.4 or KP 62.0 would
  add a figure without adding a fact.
* **Keying on the run stem is load-bearing.** ADR-0046 suffixes a z_toe
  scenario's stem (`_ztoe_plus0.30m`); a scenario therefore finds no registry
  entry and writes nothing to `docs/figures/`. The guarantee that a scenario can
  never masquerade as the baseline now extends to the publication directory.

**The persisted posteriors were not touched.** The redraw runs through the
existing `--figures-only` path, which recomputes the posterior in memory from its
Phase 1 parent and writes no artifact. All 16 `results/phase2/*_posterior.{h5,json}`
files were asserted byte-identical (SHA-256) before and after, which matters
because the campaign manifest records their digests.

### Row 4.7: the peak-only shortcut

`phase2_peak_shortcut.png`, table source `phase2-peak-shortcut.csv`, from a third
committed slice `docs/decisions/phase2-peak-shortcut.json` cut by
`thesis_figure_gaps.py extract` from the eight sweeps and eight posteriors (it
records all 16 source paths and their SHA-256, and re-extracting must reproduce
its `strata` block).

The published statement in `phase2_report.md` section 11.1 is prose only, so the
slice recomputes it: the peak-only reading is the Phase 1 **prior transient**
curve interpolated linearly on its raw MC points at the observed 2016 peak, which
reproduces the published percentages to three decimals and the factors exactly --
KP 58.8 15.596 % against 5.673 % (**x2.75**), KP 60.0 13.114 % against 3.363 %
(**x3.90**). Both readings are transient, so this compares method against method
on one sample, not limit state against limit state.

Three things the figure refuses to blur:

* four strata reject nothing under **either** reading, so their factor is **not
  defined** -- not 1.0 (which would read as agreement) and not unbounded. They
  keep their rows and say so;
* KP 57.4 matrix (x7.46, 65 rejected rows) and KP 60.0 bulk (x6.12, 23 rows) are
  the **small-number regime** section 11.1 names. They are hatched, muted, and
  excluded from the headline band -- admitting them would widen the published
  "2.75 to 3.9x" to "2.75 to 7.5x" on the strength of 88 rows;
* the headline band spans only the two informative strata, which is the scope in
  which the number is a measurement.

### Gate G7

Coverage **57 of 57 to 62 of 62 declared, 0 stale** (61 staleness-gated plus the
one recorded ADR-0032 waiver). The four Phase 2 figures get their own
`FIGURE_DRIVERS` entry; at about 6.2 min for the two strata it is the slowest
redraw path there, because the seam sits downstream of a full 1e5-row replay.
Declaring it declaration-only would have been cheaper and wrong: a real plot-only
path exists, so the figures are kept unconditionally fresh rather than merely
watched. That entry is also the first whose command is `-m <package>` rather than
a `scripts/` path, which the driver-shape guard in `tests/test_figure_pass.py` was
widened to allow for this repository's three packages.
