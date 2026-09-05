# Number-consistency audit, 2026-07-30

**Scope.** Every quoted quantitative claim in `docs/architecture.md`,
`docs/conventions.md`, `docs/phase2_report.md`, `docs/phase3_report.md`,
`docs/stage6_6_report.md`, `docs/production_campaign_2026-07-29.md`,
`docs/tokachi_bep_inputs_provenance.md`, all 65 files in `docs/decisions/`,
architecture and decision records, and every msc-thesis chapter and appendix, verified against the
artifact it should trace to.

> **Addendum 2026-07-31.** The original pass had a blind spot: it contained no
> ADR-0032 row at all — grepping it for "aquifer" returned nothing — so the
> aquifer-response claims were never checked. **Section M** closes that gap.

**Method.** Headline and quotable claims were verified *programmatically* against
the current artifacts (`results/production_campaign_manifest.json`,
`results/system_integration/phase3/rq4_annual.csv`,
`results/stage6_6/stage6_6_*_analysis.json`, `results/phase2/*_posterior.json`,
`docs/decisions/*.json`) rather than against other prose. Where a number is
reported below as a "current value" it was recomputed in this pass.

**Verdicts.**

| verdict | meaning | action |
|---|---|---|
| **current** | matches the artifact it traces to | none |
| **superseded-and-labelled** | outdated, but carries an inline marker or sits in a dated addendum with a forward pointer to the authoritative section | none (deliberate historical record) |
| **superseded-and-unlabelled** | outdated with no marker: a reader would take it as current | **fixed** |
| **untraceable** | cannot be tied to an artifact, or is ambiguous as written | **fixed** |

## Row counts

Counted mechanically over the ID'd rows of sections A to H and M (`python`-parsed
from this file, so the audit's own arithmetic is checkable). Section M was added
2026-07-31; the A-to-H figures below are unchanged by it:

| verdict | rows | of which section M | which |
|---|---|---|---|
| current | 45 | 6 | — (includes G3, whose cell records an outcome rather than one of the four verdicts) |
| superseded-and-labelled | 8 | 0 | A1 A2 A5 A7 A13 D1 D2 D3 |
| **superseded-and-unlabelled** | **26** (all fixed) | 0 | A3 A4 A10 A11 A12 · B1–B8 · C2 · D6 D7 D8 · E1–E6 · F4 F5 · G4 |
| **untraceable** | **7** (all fixed) | 3 | C1 E15 G1 H1 · M1 M2 M4 |
| flagged, not fixed | 1 | 0 | H11 (msc-thesis em dashes, a house rule rather than a number) |
| **total claim rows** | **87** | **9** | |

Section J adds **8** figure-compliance rows (all compliant), section K adds **10**
driver rows for the hardening sweep, and section I records three documents with
nothing to correct. **95 verified rows in total**, of which **33 needed fixing**.

---

## A. The design-HWL bias (sweep a)

The two anchors are **different levels and must never be quoted as one another**:
Stage 6.6 evaluates 39 levels at KP 62.0 = the 38-level generated grid **plus** the
exact section HWL inserted by `prepare_config(extra_levels=(HWL,))`.

| anchor | KP 62.0 | KP 57.4 | rows at N = 1e5 | rows at N = 1e6 |
|---|---|---|---|---|
| **A1** inserted design HWL | 46.39 m | 39.21 m | 4 / 0 | 63 / 2 |
| **A2** nearest grid level | 46.50 m | 39.25 m | 15 / 0 | 176 / 10 |

| # | claim | document + line | source artifact | current value | verdict |
|---|---|---|---|---|---|
| A1 | KP 62.0 HWL bias "a factor of about 21" | `stage6_6_report.md:29` | `adr0040-hwl-bias-resolution.json` `stages.A_brute_kp62_0.anchor_A1` | 26.9 [21.6, 35.3] at 46.39 m, 63 rows | superseded-and-labelled (inline banner to §9) |
| A2 | KP 57.4 "at least 32 at 95 percent confidence" | `stage6_6_report.md:37` | same, `A_brute_kp57_4.anchor_A1` | **B ≥ 148**; quotable anchor 42.7 [39.4, 46.6] at 39.50 m | superseded-and-labelled (inline banner to §9) |
| A3 | "total static-to-transient ratio falls from 15 at 47.0 m to 1.9 at 50.5 m (KP62.0)" | `stage6_6_report.md:44` | `results/stage6_6/stage6_6_kp62_0_analysis.json` C0/C4b | **10.5 at 47.0 m, 1.4 at 50.5 m** | **superseded-and-unlabelled → FIXED** |
| A4 | "P(C3b)/P(C4b) runs from 7.9 at 47.0 m down to 1.9 at 50.5 m" | `stage6_6_report.md:191` | same, C3b/C4b | **6.0 at 47.0 m, 1.4 at 50.5 m** | **superseded-and-unlabelled → FIXED** |
| A5 | §8 adoption table 46.39 m row `21.0 \| 44.7 \| (not resolved)` | `stage6_6_report.md:397` | as A1 | 26.9, resolved | superseded-and-labelled (§9 follows and states "quote 26.9") |
| A6 | §9 resolution block: 26.9, 21.6, B ≥ 148, 42.7, ρ = 1.249 | `stage6_6_report.md:417+` | `adr0040-hwl-bias-resolution.json` | matches exactly | current |
| A7 | §6.1 KP 62.0 table rows 44.7 / 26.2 | `production_campaign_2026-07-29.md:263-264` | as A1/A2 | 26.9 / 21.6 | superseded-and-labelled (banner at :250) |
| A8 | §12 closure note 26.9, B ≥ 148, tilted-not-validated | `production_campaign_2026-07-29.md:695+` | `adr0040-hwl-bias-resolution.json` | matches | current |
| A9 | Failure-mode-4 paragraph: 26.9 [21.6, 35.3] on 63 rows; B ≥ 148; 21.6 / 10.5 / 6.3 / 2.4 by stage; ρ = 1.249 | `architecture.md:538` | same | matches; this is the location ADR-0040 §3.4 item 9 called *wrong* rather than stale, and the fix landed correctly | current |
| A10 | "Stage 6.6 headline bias figures (~21x at KP 62.0, ≥32x at KP 57.4 per event at HWL)" | `decisions/0047-dem-surveyed-seepage-length.md:394` | as A1/A2 | 26.9 resolved / B ≥ 148 | **superseded-and-unlabelled → FIXED** (pointer added to the ADR's 2026-07-30 amendment) |
| A11 | "Stage 6.6 conventional-practice bias: nominal HWL value 21.0 → 44.7, but neither is resolved" | `decisions/0047-dem-surveyed-seepage-length.md:454` | same | as above; the *relative* claim (bias falls ~⅓ where counts are adequate) is sound and unaffected | **superseded-and-unlabelled → FIXED** (same amendment) |
| A12 | "~21x at KP 62.0, ≥32x at KP 57.4 per event at HWL" | `decisions/adr0047-dem-seepage-length.md:484` | same | as above | **superseded-and-unlabelled → FIXED** (second dated correction added to the §4.5 banner) |
| A13 | §8 table row "Stage 6.6 bias at HWL (unresolved, 1 and 4 rows) 21.0 \| 44.7" | `decisions/adr0047-dem-seepage-length.md:680` | same | as above | superseded-and-labelled (dated addendum, now with an explicit pointer from A12's banner) |
| A14 | A1-vs-A2 conflation check across all documents | all of the above | `configs/kp*_historical_matrix.yaml` `geometry.HWL`; `stage6_6_kp62_0.h5` `conditioning_grid` | HWL 46.39 / 39.21 read from the configs; grid contains 46.50 / 39.25 and **not** 46.39 / 39.21 | **no conflation found**: campaign §6.1 tabulates both rows separately, ADR-0040 labels every figure A1 or A2, and the 2026-07-30 synthesis states that its `design_hwl` row is the *nearest grid level* | current |

## B. "Every Euler-flip count is exactly 0" (sweep b)

Gate G-A2 **fired** at KP 57.4 at N = 1e6: 4 `c4b_not_c3b` barrier-jump rows in
1e6, at **39.50 / 40.25 / 40.75 m**. The rate is 4e-6, so the expected count at the
production N = 1e5 is **0.4** — which is why every earlier run saw zero. Six
locations stated the claim without its N.

**The uncomfortable detail, carried:** the recommended KP 57.4 quotable anchor at
**39.50 m is itself one of the flip levels**, carrying 1 barrier-jump row out of its
521 transient failures (0.19 %). A spurious transient failure inflates
P_transient and therefore *deflates* B, so the artifact biases 42.7 **downward** by
about 0.2 % — negligible against the 1.18x interval, and conservative in direction.
This is propagated wherever the anchor is.

| # | claim | document + line | current value | verdict |
|---|---|---|---|---|
| B1 | "G3 every Euler-flip count exactly 0" | `production_campaign_2026-07-29.md:109` | 0 **at N = 1e5**; 4 rows at N = 1e6 at KP 57.4 | **superseded-and-unlabelled → FIXED** (N qualifier + pointer to §12) |
| B2 | "every Euler-flip count exactly 0 across all five diagnostics at both sections" | `production_campaign_2026-07-29.md:244` | same | **superseded-and-unlabelled → FIXED** |
| B3 | "every Euler-flip count is exactly 0 across all five diagnostics at all 39 levels" | `stage6_6_report.md:374` | same (KP 62.0 clean at both N) | **superseded-and-unlabelled → FIXED** |
| B4 | "at KP 62.0 every Euler-flip count is 0 at all 39 levels" | `stage6_6_report.md:444` | true at both N for KP 62.0; §9 now carries the KP 57.4 firing, the flip levels, and the anchor caveat | **superseded-and-unlabelled → FIXED** |
| B5 | "reported per level (expected 0 at 225 s)" | `decisions/0040-...gap-decomposition.md:184` | expected 0 **at N = 1e5**; "0" is a statement about sample size, not about the discretisation being exact | **superseded-and-unlabelled → FIXED** |
| B6 | "drift guard bit-identical at 38 levels with all Euler-flip counts 0" | `decisions/adr0047-dem-seepage-length.md:655` | same | **superseded-and-unlabelled → FIXED** |
| B7 | "drift guard bit-identical at 38 levels; all Euler flips 0" | `decisions/0047-dem-surveyed-seepage-length.md:438` | same | **superseded-and-unlabelled → FIXED** |
| B8 | architecture and decision records campaign + Stage 6.6 bullets, "all Euler flips 0" / "every Euler flip 0" | historical project notes, lines 64, 76 and 78 | same | **superseded-and-unlabelled → FIXED** (N qualifier in the new bullet and in place) |
| B9 | ADR-0040 note's own G-A2 statements | `decisions/adr0040-hwl-bias-resolution.md:287,472,862` | correct as written: each is scoped to its N | current |

## C. The tilted sampler's scope (sweep c)

ADR-0029 is **not** contradicted. Its measured claims (3.2 to 4.1x deep-tail CoV
reduction on a single P_f, zero-failure replicates eliminated at P_f ~ 1e-4, exact
weights under any coupling) are reproduced or unchallenged; the 4.66x transient-side
reduction measured at the design HWL is at the favourable end of that range. What
fails is a **new application to a different estimand**.

| # | claim | document + line | current status | verdict |
|---|---|---|---|---|
| C1 | "for sub-decade tail quantification use the substitutable Z-space cross-entropy-tilted importance sampler" | `architecture.md:540` (failure mode 5) | true for a **single-branch** tail P_f; **not** valid for a ratio between branches (V2 and V4 fail; static-side CoV inflation 1.50x at the anchor rising to 940x at saturation) | **untraceable as written → FIXED** (scope note added, with the mechanism and the measured inflation) |
| C2 | "Tail P_f numbers ... **must** come from the tilted estimator with its n_eff diagnostic reported" | `decisions/0029-...tail-estimator.md` consequence 5 | over-reaches twice: brute force at larger N is admissible (and is what resolved the design HWL), and the recommendation is single-branch-scoped | **superseded-and-unlabelled → FIXED** ("must" → "may", plus a dated scope amendment recording the documented negative) |
| C3 | ADR-0029 §4 "a *tail estimator* for the lowest conditioning levels and for the fm5 study — a supplement, never a replacement population" | same, §4 | accurate; no change needed | current |
| C4 | `appendix-b.tex:90,420` "Deep-tail estimator; never enters the production deliverables" / "the tilted importance sampler exists for tail quantification" | msc-thesis | accurate but silent on the ratio exclusion | current (gap recorded in the thesis inventory, not a defect) |

## D. The cancellation claim (sweep d) — verified independently

Re-grepped the withdrawn claim that epistemic brackets "largely cancel" in the
static-vs-transient ratio. **Every occurrence is either struck through, carries a
dated withdrawal, or is narrative setup immediately followed by its refutation.**

| # | location | state | verdict |
|---|---|---|---|
| D1 | `decisions/0048-prior-mean-epistemic-scenarios.md:220` consequence 3 | struck through in place with "SUPERSEDED 2026-07-30 — REFUTED BY MEASUREMENT", plus a full Amendment section | superseded-and-labelled |
| D2 | `decisions/0047-dem-surveyed-seepage-length.md:375,497` | Amendment "the k_aq contrast is withdrawn; the L result is not" | superseded-and-labelled |
| D3 | `decisions/adr0047-dem-seepage-length.md:419-425,433,471,481` | §4.5 opens with a dated correction banner covering every "unlike k_aq" below it | superseded-and-labelled |
| D4 | `tokachi_bep_inputs_provenance.md:242-245` | states the L bracket does not cancel and that the k_aq counter-example "was **refuted**" | current |
| D5 | `architecture.md:538` failure mode 4 | fully rewritten: names both non-cancellations (L ρ 2.25/1.64/2.23/0.475; k_aq ×82/×66/×163/×46), the mechanism, and `m_p` as the only canceller. **Step 4 flagged this as the one location whose prose was wrong rather than stale; the fix landed correctly.** | current |
| D6 | `architecture.md:361` §7 L-model paragraph | said only "Stage 6.6's bias headlines are therefore L-conditional", which reads as if L were the whole conditionality — the exact error ADR-0047 §4.5 itself made | **superseded-and-unlabelled → FIXED** (k_aq named as larger, surviving common-mode rule stated) |
| D7 | `architecture.md:602` decisions table, seepage-length row | same shape | **superseded-and-unlabelled → FIXED** |
| D8 | `architecture.md:11` revision note "reconciled with the accepted ADRs 0001–0046" while the same note folds in 0047 and 0048 | self-contradictory as written | **superseded-and-unlabelled → FIXED** (0001–0048, plus the two 2026-07-30 companion notes) |
| D9 | `mainmatter/5. Verification...tex:1184-1198` and `7. Discussion.tex:99,105-120` | both set the supposition up and refute it in the same passage, with the ×82/66/163/46 numbers and the "only if pure common-mode" rule; the Discussion carries a dedicated subsection | current |
| D10 | surviving rule stated wherever the old claim was | ADR-0048 amendment, ADR-0047 (both files), `architecture.md` (3 places after D5–D7), `epistemic-bracket-synthesis.md` §4(c), thesis Ch. 7 | present in all | current |

## E. Phase 3 (RQ3 / RQ4)

Recomputed from `results/system_integration/phase3/rq4_annual.csv` (matrix,
posterior, λ_ac = 250 m, primary surface variant).

| # | claim | document + line | current value | verdict |
|---|---|---|---|---|
| E1 | "Segments above 1e-3/yr go from **2 to 45 of 114**" | `phase3_report.md:250` | **3 to 45** (KP 62.0 crossed 1e-3 when the L adoption raised its historical annual probability 5.24e-4 → 1.006e-3) | **superseded-and-unlabelled → FIXED** |
| E2 | "At the BEP sections the system ratio is 5.5–19.5x ... KP62.0 19.5" | `phase3_report.md:253-255` | **5.5 to 12.7x**; KP 62.0 **12.70** | **superseded-and-unlabelled → FIXED** |
| E3 | λ_ac = 40 m bracket at KP 62.0, "x3.1/x1.6" | `phase3_report.md:261` | **x3.29 / x1.93** | **superseded-and-unlabelled → FIXED** |
| E4 | bulk d70 cut at KP 62.0, "historical x2.6, +4K x1.2" | `phase3_report.md:266` | **x5.05 / x1.52** | **superseded-and-unlabelled → FIXED** |
| E5 | `scour_script_k` raises KP 62.0 "by ~45% (5.24e-4 → 7.59e-4)" | `phase3_report.md:275` | **~22 %** historical (1.006e-3 → 1.225e-3); +9 % at +4K | **superseded-and-unlabelled → FIXED** |
| E6 | `overflow_sine30h` lowers KP 62.0 "~19–27%" | `phase3_report.md:278` | **~12 to 13 %** (historical 1.006e-3 → 8.843e-4; +4K 1.278e-2 → 1.117e-2) | **superseded-and-unlabelled → FIXED** |
| E7 | prior-vs-posterior "~12% at KP58.8 historical (8.47e-3 → 7.42e-3)" | `phase3_report.md:270` | prior/posterior = 1.141, i.e. −12.4 % | current |
| E8 | median annual system P_f "0 historically to 3.7e-4"; mean 1.0e-4 → 1.9e-3 (~18x) | `phase3_report.md:245-249` | median 0 → 3.672e-4; mean 1.082e-4 → 1.917e-3 (17.7x) | current |
| E9 | segments above 1e-2/yr "0 to 4" | `phase3_report.md:250` | 0 → 4 | current |
| E10 | §11.1 RQ3 KP 62.0 BEP share hist 0.812, +4K 0.500 | `phase3_report.md:429+` | 0.8115 / 0.5003 | current |
| E11 | §11.2 RQ4 KP 62.0 annual 1.01e-3, ratio 12.7 | `phase3_report.md:447+` | 1.006e-3, 12.70 | current |
| E12 | §11.3 the `bep_clamped_above_grid` withdrawal ("False in all 20 KP 62.0 rows; fires only on 16 KP57.4/58.8 bulk rows") | `phase3_report.md:464+` | verified False in all 8 primary KP 62.0 rows and in all 20 campaign rows | current |
| E13 | RQ4 climate ratios 12.7 / 5.5 / 7.9 / 12.7 | `production_campaign_2026-07-29.md`, architecture and decision records | 12.66 / 5.51 / 7.87 / 12.70 | current |
| E14 | RQ3 "BEP dominant 81–100 % historically, leading 3 of 4 under +4K, KP 62.0 level at 0.500/0.500" | same | shares hist 1.000/0.974/1.000/0.812; +4K 0.912/0.941/0.998/0.500 | current |
| E15 | `phase3_climate_shift.png` presented as the RQ4 result | figure caption | 110 of 114 segments carry `bep_source = None` and are surface-only lower bounds, so the distribution is **reach context** | **untraceable as presented → FIXED** (figure re-captioned; new `phase3_rq4_four_sections.png` is the RQ4 headline; §6.1 prose updated) |

## F. Phase 2

Recomputed from `results/production_campaign_manifest.json` (`per_stratum` blocks)
and cross-checked against the eight `results/phase2/*_posterior.json` sidecars.

| # | claim | document + line | current value | verdict |
|---|---|---|---|---|
| F1 | matrix rejection KP57.4 0.07 / KP58.8 5.67 / KP60.0 3.36 / KP62.0 0.00 % | `phase2_report.md` §11, architecture and decision records | 0.0650 / 5.6730 / 3.3630 / 0.0000 % | current |
| F2 | bulk rejection "≤ 0.02 %" | architecture and decision records | max bulk = 0.0230 % (KP 60.0); the others exactly 0 | current (0.023 rounds to 0.02 at the stated precision; noted, not changed) |
| F3 | marginal transient rejection exactly 0 in every stratum | `phase2_report.md` §11, §14, `production_campaign_2026-07-29.md` | `f_marginal_transient = 0.0` in **all 16** runs (8 baseline + 4 anchor-rating + 4 no-initiation) | current |
| F4 | anchor-rating KP 62.0 "0.00% -> 0.01%" | `phase2_report.md:537` | **0.047 %** (the 0.01 % belongs to the withdrawn L = 47.0 m Phase 1) | **superseded-and-unlabelled → FIXED** |
| F5 | no-initiation KP 62.0 "30.46%" | `phase2_report.md:546` | **39.552 %** | **superseded-and-unlabelled → FIXED** |
| F6 | anchor-rating KP57.4 0.00 / KP58.8 10.81 / KP60.0 0.34 % | `phase2_report.md:536-537` | 0.0000 / 10.8140 / 0.3370 % | current |
| F7 | no-initiation KP57.4 66.4 / KP58.8 99.57 / KP60.0 99.30 %, posteriors 432 and 696 rows | `phase2_report.md:544-546` | 66.389 / 99.568 / 99.304 %; n_accepted 432 and 696 | current |
| F8 | §14 "×8.7 at design HWL (1.5e-4 → 1.3e-3)", rejection 0.00 % both KP 62.0 strata, verification exact | `phase2_report.md:691+` | matches the sidecars and the ADR-0047 record | current |
| F9 | WBI+ peak-shortcut over-rejection 2.75 to 3.9x | `phase2_report.md` §11, architecture and decision records | unchanged by this pass's work; traces to the same sidecars | current |

## G. ADR-0047's stale record set (carried-forward item 5a)

| # | claim | artifact | current state | verdict |
|---|---|---|---|---|
| G1 | KP 62.0 `baseline_L_m` = 47.0 with a `dem_clean_median` arm | `decisions/adr0047-dem-seepage-length.json` | now `baseline_L_m` 40.0, arm `withdrawn_1998`, max \|ΔP_f,trans\| 0.20106 (published 0.201) | **untraceable (contradicted the CSV) → FIXED** by `dem_cross_section_study.py all --overwrite` |
| G2 | `datum_check` block | same | **present** (`tolerance_m`, `n_stations`, `kp_range`, `comparisons`, `passed`), 3 series x 551 stations, all PASS | current after G1 |
| G3 | figure rendered from the pre-adoption payload | `docs/figures/adr0047_dem_seepage_length.png` | re-rendered from the new payload in the same command | fixed atomically with G1 |
| G4 | `csv_L_m` 47.0 at KP 62.0 | `decisions/adr0047-dem-seepage-length-ratio.json` | now 40.0; KP 62.0 arm runs 40 → 47 giving max departure **×2.106 = 1/0.475**, reproducing the published inverse | **superseded-and-unlabelled → FIXED** by the `ratio --overwrite` re-run |
| G5 | published ρ values 2.250 / 1.823 / 3.219 / 2.106 (max departure) and 2.25 / 1.64 / 2.23 / 0.475 (at HWL) | same | re-run reproduces 2.250 / 1.823 / 3.219 / 2.106 exactly | current |
| G6 | the campaign's copy under `results/production_campaign/companions/` | — | confirmed **not** a drop-in replacement (no `datum_check`); it was correctly never copied over | current |

## H. msc-thesis

Chapters 6 (`Results: Subsurface Piping Assessment`) and 7 (`Results: System
Integration and Climate Sensitivity`) are section skeletons of **84 and 73 words**
— four `\section` headings each and no body text. The audit therefore found **no
stale copies there**, which is a gap and not a clean bill of health; see
`docs/thesis_number_inventory_2026-07-30.md`.

| # | claim | document + line | current value | verdict |
|---|---|---|---|---|
| H1 | `tab:kaq_scenarios` middle column headed "Shoulder" | `5. Verification...tex:1155` | the values (0.088 / 0.395 / 1.99 / 1.89) are ADR-0048's **transition midpoint** (P_f ≈ 0.5); ADR-0045 quotes its factors at a *different* shoulder (P_f ≈ 2e-3), two orders of magnitude lower in probability | **untraceable → FIXED** (header renamed "Transition midpoint"; caption now defines it and names the second anchor) |
| H2 | k_aq scenario ratios 198 / 2428 / 0.088 / 0.395 / 0.024 / 0.743 / 0.082 / 0.924 / 1.29 / 1.50 | `5. Verification...tex:1156-1166` | match `adr0048-prior-mean-companion.json` | current |
| H3 | non-cancellation "82 at KP 57.4, 66 at KP 58.8, 163 at KP 60.0 and 46 at KP 62.0" | `5. Verification...tex:1197`, `7. Discussion.tex:118` | match `epistemic-bracket-synthesis.json` (82.2 / 65.6 / 162.9 / 45.6) | current |
| H4 | m_p cancellation "1.07 to 1.22" | `7. Discussion.tex:102` | matches | current |
| H5 | L non-cancellation "2.25, 1.64 and 2.23 ... and by 0.475" over "eighty-seven conditioning levels" | `7. Discussion.tex:133-135` | matches the ADR-0047 §4.5 published table; re-verified by the regenerated ratio JSON | current |
| H6 | seepage-length prior row L = 40 m, μ_ln 3.669 at KP 62.0 | `3. Study Area...tex` | matches `data/processed/tokachi_bep_inputs.csv` (`L_m` 40.0) and `configs/kp62_0_*.yaml` | current |
| H7 | ADR-0039 timestep-stress numbers (0.80 m, 225 s, 112.5 s, 16.8 %) | `5. Verification...tex:84-128` | match `adr0039-timestep-stress.json` | current |
| H8 | GSA Sobol' indices (C_e 0.066 / 0.338, 0.163 / 0.486; interaction gap 0.66) | `5. Verification...tex:711+` | match `adr0033-gsa-study-*.json` | current |
| H9 | Japanese-case validation numbers (0.061 / 0 / 0.0052; 0.62) | `5. Verification...tex:368+` | match `results/validation_*/validation_results.json` | current |
| H10 | Ch. 6 and Ch. 7 bodies | both stub files | no quantitative claim exists to be stale | current (gap, see the thesis inventory) |
| H11 | **house-rule finding, not a number:** typeset em dashes, which msc-thesis architecture and decision records forbids unconditionally | `3. Study Area...tex:23`; `5. Verification...tex:1127,1129`; `7. Discussion.tex:58,62,93,95,133,134`; `8. Conclusions...tex:24` | 10 typeset lines (comment-line rules in `appendix-a.tex` are not typeset and are not violations) | **flagged, not fixed** — prose I was not asked to touch; the author's contract says flag rather than silently smooth |

## M. ADR-0032 aquifer response (added 2026-07-31)

**Why this section exists.** The 2026-07-30 pass never touched ADR-0032: the
word "aquifer" did not appear anywhere in this file. The claims below were
therefore unchecked, and one of them — the margin — had quietly acquired two
different published values that nothing distinguished.

Two Π quantities and two T_rise denominators are in circulation. Verified
against `results/production_campaign_manifest.json`
→ `stages.diagnostics.per_run.*.aquifer_response` (all eight strata) and the run
sidecars:

| quantity | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| τ_aq central (S_s = 1e-4) | 350.0 s | 680.0 s | 765.0 s | 150.0 s |
| τ_aq corner90 | 988.8 s | 1921.2 s | 2161.3 s | 423.8 s |
| `t_rise_s` (canonical event) | 82 800 s | 82 800 s | 82 800 s | 82 800 s |
| `pi_central` | 0.004227 | 0.008213 | 0.009239 | 0.001812 |
| `pi_corner90` | 0.011943 | 0.023203 | 0.026103 | 0.005118 |
| Π\*/Π_central | 23.66 | 12.18 | 10.82 | 55.20 |
| **`margin_vs_threshold` = Π\*/Π_corner90** | **8.37** | **4.31** | **3.83** | **19.54** |

| ID | claim | where | artifact / current value | verdict |
|---|---|---|---|---|
| M1 | "Π = τ_aq/T_rise ≈ 0.010–0.012" | `architecture.md:35,516`, `decisions/0032-...-preregistration.md:294`, `decisions/adr0032-...md:67`, historical project notes, line 54 | **reproduces exactly** at the denominator the study used: 680/64 800 = 0.0105 and 765/64 800 = 0.0118, T_rise = the **ensemble-median** rising limb (18 h). The per-run stamp divides the *same* τ_aq by the run's own canonical-event rise (23 h) and reads 0.00821 / 0.00924. Not a discrepancy; a denominator that was never stated | **untraceable as written → FIXED** (every occurrence now names its denominator; reconciled in the companion note's "Two margins" section) |
| M2 | "~10× margin" | `architecture.md:582`, `decisions/0032-...:298,314,359`, `decisions/adr0032-...:93`, historical project notes, line 54 | = Π\*/Π_**central** at the 18 h denominator: **9.53** (KP 58.8) / **8.47** (KP 60.0). Three different margins are computable from the same gate and all three appear in the repo | **untraceable as written → FIXED** (each occurrence now says which Π and which T_rise) |
| M3 | per-stratum margins "3.8 to 19.5 ×" | `production_campaign_2026-07-29.md:434`, historical project notes, line 78 (G5) | **current**: 8.37 / 4.31 / 3.83 / 19.54 = `pi_threshold / pi_corner90`, reproduced from the manifest for all eight strata | current |
| M4 | those margins are "at the conservative `S_s` corner" | `production_campaign_2026-07-29.md:435` | **wrong corner.** `S_s` is at its upper bound in *both* Π columns, so it cannot be what separates them; the corner is the pre-registered **90th-percentile τ_aq** corner (high D_aq, high D_bl, low k_bl — ADR-0032 D3) | **untraceable → FIXED** (renamed; the mislabel is recorded in place) |
| M5 | threshold "Π\* = 0.10" | `architecture.md:516,582`, `decisions/0032-...:119`, historical project notes, line 54 | **current**: `hydraulics.AQUIFER_RESPONSE_PI_THRESHOLD` = 0.1, and `pi_threshold` = 0.1 in all eight sidecars — one source of truth, never redefined in the driver | current |
| M6 | "the τ_aq-bounding governing pair KP 58.8 / KP 60.0" | `architecture.md:516,582`, `decisions/0032-...:194` (D5), historical project notes, line 54 | **current, and now confirmed on data it was pre-registered against.** τ_aq central 765 s (KP 60.0) and 680 s (KP 58.8) are the two largest of the four, ahead of 350 s (KP 57.4) and 150 s (KP 62.0); the pair carries the smallest margins (3.83, 4.31 vs 8.37, 19.54). D5 argued this from the priors *before* any τ_aq existed | current (**positive result** — recorded as a dated confirmation in ADR-0032 D5 and the companion note) |
| M7 | "median T_rise 18 h, plateau 9 h", retiring spec §11's "~1.5 h plateau" | `architecture.md:516`, `decisions/adr0032-...:81`, historical project notes, line 54 | **current**, and these are ensemble medians over ~140 HPB members, matching M1's denominator. The run stamps the canonical event's own values, `t_rise_s` 82 800 s (23 h) and `t_plateau_s` 36 000 s (10 h); `rise_10_90_s` is 64 800 s and `fwhm_s` 198 000 s (55 h) | current (the 18 h / 9 h pair is the *population* characterisation; do not read it off a sidecar) |
| M8 | "Check B passes: the 3600 s cadence carries ~9 samples across the peak" | `architecture.md:516`, `decisions/adr0032-...:83` | **current**: `native_dt_s` 3600 s ≤ T_feature/2 (16 200 s on the 9 h median, 18 000 s on the run's 10 h), and `check_b_native_resolves` is true in 8 of 8 strata | current |
| M9 | verdict "`instantaneous`, retained everywhere on evidence" | `architecture.md:35,516,582`, historical project notes, line 54, `production_campaign_2026-07-29.md:427-430` | **current**: `verdict` = `instantaneous` and `check_a_instantaneous_justified` true in **8 of 8** strata, at **both** Π definitions | current |

**Net:** no aquifer-response number changed. Three rows were ambiguous or
mislabelled as written and are fixed by naming the quantity; six are current,
one of them a pre-registered prediction that held when extended to all eight
strata.

## I. Documents with nothing to correct

| document | finding |
|---|---|
| `docs/conventions.md` | carries **no** quantitative claims (naming, units, typing, testing philosophy, and the §8 thesis-text rule). Nothing to audit. |
| `docs/tokachi_bep_inputs_provenance.md` | per-cell audit trail; the cancellation passage (§ on L) already records the k_aq refutation. Input values re-checked against `data/processed/tokachi_bep_inputs.csv` (KP 62.0 `L_m` = 40.0, foreshore widths 200/325/600/44). current |
| `docs/decisions/` (65 files) | the 2026-07-30 amendments in ADR-0029, ADR-0040, ADR-0047 (both files) and ADR-0048 now carry every withdrawal. Older ADRs whose numbers were superseded by later ADRs carry Status lines and supersession pointers per house practice. |

## J. ADR-0024 compliance of the regenerated figures

Checked on every regenerated figure whose x axis crosses KP 62.0's attainable
maximum. `attainable_max_m` = **50.5 m** (`results/stage6_6/stage6_6_kp62_0_analysis.json`
and `scripts/stage6_6_gap_decomposition.py`), so the hypothetical fit-stabiliser
extension is the eight levels **51.0 to 56.5 m MSL** — not "50.0 to 56.5" as the
brief's phrasing implied, and the shading boundary is drawn at 50.5.

| figure | treatment | verdict |
|---|---|---|
| `fragility_per_section.png` | KP 62.0 panel shades 50.5 to 56.5 and labels it "fit-stabilizer levels (above max attainable stage)" | compliant |
| `fragility_comparison.png`, `fragility_tail_log.png` | same shading | compliant |
| `stage6_6_*_kp62_0.png` (5) | shade + "hypothetical (ADR-0024)" annotation from `attainable_max_m` | compliant |
| `adr0040_hwl_bias_resolved.png` (new) | both panels shade beyond 50.5 via `_figstyle.mark_hypothetical`; the zoom panel stops at 47.35 m so never reaches it | compliant |
| `adr0040_tilted_is_validation.png` (new) | both panels shade + label | compliant |
| `epistemic_vs_statistical.png` (new) | no stage axis; anchors are named levels, all attainable | compliant (n/a) |
| `phase3_rq4_four_sections.png` (new) | no stage axis (annual probabilities) | compliant (n/a) |
| `adr0047_dem_seepage_length.png` | max \|ΔP_f\| at KP 62.0 occurs at 50.00 m, below the extension | compliant |

**No violation found**; no figure needed correcting on this ground.

## L. A free confirmation from the regeneration itself

The brief's inventory listed `results/stage6_6/figures/*_kp57_4.png` (dated
2026-07-17) as stale against the 2026-07-29 Stage 6.6 re-run. Regenerating them
produced **byte-identical output** — all five KP 57.4 figures reproduce their
committed versions exactly, while all five KP 62.0 figures changed.

That is the expected pattern and it is worth stating: the ADR-0047 adoption touched
**KP 62.0 alone**, so KP 57.4's ladder was re-run to bit-identical data (which the
campaign's G1 and G3 gates asserted) and its figures were **timestamp-stale but
content-current**. The regeneration is therefore an independent, incidental
re-confirmation of that bit-identity gate, obtained for free from the figure pass.

Of the 52 tracked-or-new figures in `docs/figures/`: **13 changed content**
(5 KP 62.0 Stage 6.6, 4 Phase 3, 3 seepage-length, 1 ADR-0047), **7 are new**
(3 from this pass's HWL/epistemic work, 1 Phase 3 RQ4, 3 Phase 1 fragility copies
that previously lived only under gitignored `results/`), and the remainder
reproduced byte-identically.

---

## What was fixed, in one list

1. `stage6_6_report.md` — §1 ratio pair (A3), §4.1 C3b/C4b pair (A4), two Euler-flip
   claims (B3, B4) plus a new paragraph recording the KP 57.4 firing, the three flip
   levels, and the 39.50 m anchor's own 1-row contamination.
2. `production_campaign_2026-07-29.md` — G3 gate row and §6 prose (B1, B2).
3. `phase3_report.md` — §6.1 segment count and ratio range (E1, E2), §6.2 four KP 62.0
   brackets (E3–E6), plus a superseded banner on §6.1 pointing at §11.2 and the
   reach-context caption for `phase3_climate_shift.png` (E15).
4. `phase2_report.md` — §11.3 anchor-rating and no-initiation KP 62.0 figures (F4, F5).
5. `architecture.md` — failure mode 5 scope note (C1), §7 and the decisions table
   (D6, D7), revision note (D8).
6. `decisions/0029-...tail-estimator.md` — "must" → "may" and a dated scope amendment (C2).
7. `decisions/0040-...gap-decomposition.md` — the flip-gate clause (B5).
8. `decisions/0047-dem-surveyed-seepage-length.md` — Euler-flip qualifier (B7) and a
   bias-magnitude supersession note (A10, A11).
9. `decisions/adr0047-dem-seepage-length.md` — Euler-flip qualifier (B6) and a second
   dated correction on §4.5 (A12).
10. `decisions/adr0047-dem-seepage-length.json`, `...-ratio.json` and
    `docs/figures/adr0047_dem_seepage_length.png` — regenerated as one matched set (G1, G3, G4).
11. architecture and decision records — Euler-flip qualifiers and the new dated bullet (B8).
12. msc-thesis `5. Verification, Validation, and Sensitivity.tex` — `tab:kaq_scenarios`
    column header and caption (H1).

Added 2026-07-31, closing the ADR-0032 gap this audit had entirely omitted:

13. `decisions/adr0032-aquifer-response-diagnostic.md` — the table's denominator
    stated, a "Two margins, both correct" section reconciling Π\*/Π_central at the
    ensemble-median T_rise against the per-run Π\*/Π_corner90, and a dated
    confirmation that the pre-registered τ_aq-bounding pair holds at all eight
    strata (M1, M2, M6).
14. `decisions/0032-aquifer-response-diagnostic-preregistration.md` — Check A and
    the S_s-does-not-bind bullet now name Π_central and their denominator (M1, M2);
    D5 gained the dated confirmation (M6).
15. `architecture.md` — §M4 prose, the §11 diagnostic paragraph, the §13 decisions
    row and the pseudocode comment now distinguish the two margins (M1, M2).
16. `production_campaign_2026-07-29.md` — §9.2 margin column labelled
    Π\*/Π_corner90, the "conservative `S_s` corner" mislabel corrected in place,
    and the ~10× figure related to it (M2, M3, M4).
17. architecture and decision records — the ADR-0032 bullet and the campaign bullet's G5 clause (M1–M4).

## K. Hardening sweep of the long-running drivers

Step 4 found and fixed two anti-patterns in its own driver. Both are cheap to have
elsewhere, so every long-running driver was checked for the same two shapes:
**(i)** validation that can raise *before* its expensive result is persisted, and
**(ii)** per-section output paths that could collide or silently drop a sibling.

| driver | shape (i) gate-before-persist | shape (ii) per-section collision | action |
|---|---|---|---|
| `hwl_bias_resolution.py` `cmd_brute` | already fixed by Step 4 (writes the HDF5 and diagnostics JSON unconditionally, then gates; `flip_summary` records offending levels) | n/a | none |
| `hwl_bias_resolution.py` `cmd_epistemic` | n/a | already fixed by Step 4 (merges into any existing record) | none |
| **`hwl_bias_resolution.py` `cmd_verify`** | **PRESENT** — `raise SystemExit("GATE G-A1/G-A2 FAILED")` sat *before* `result.save()` and before `_write(stage_a_verify.json)`, so a failure discarded a ~15 min ladder per section and the diagnostics that would explain it. On a two-section run, section 2's failure also discarded section 1's already-verified record, because the JSON was never written. **Exactly the defect Step 4 documented, still live in its sibling.** | **PRESENT** — `_write` overwrote, so `--sections kp62_0` dropped KP 57.4 | **FIXED** (persist both artifacts first, collect failures across sections, merge into any existing record, raise after the loop) |
| **`stage6_6_gap_decomposition.py`** | absent (the driver persists per phase) | **PRESENT** — `summary = {"sections": {}}` was rebuilt from scratch, so `--sections kp62_0` deleted KP 57.4's entry. The campaign's **G3 gate asserts both sections are present**, so a partial re-run would have failed the next campaign for a reason unrelated to the physics | **FIXED** (merge) |
| `timestep_convergence_stress.py` | the two `raise ValueError`s are input validation on the config, fired at the start of each section's work before any compute | **PRESENT but NOT fixed** — `--skip-confirm` and `--quick` both write a *reduced* payload to the same default JSON path, overwriting the two-section production record. Not fixed because merging is **ambiguous here**: `--quick` writes a deliberate smoke payload, and merging a smoke result into the production record would be worse than overwriting it. The right fix is a distinct output path per mode, which changes the CLI contract | **listed** |
| `production_campaign.py` | absent, and the design is correct: `GateFailure` is caught in `main`, which records the failure entry and **saves the manifest** before stopping | absent (per-stage keys; `--stage` is a filter and each stage writes its own key) | none |
| `run_sweep.py` | absent (no gates; `run.py` already writes `<output>.raw.h5` *before* M9 fitting, the documented crash-recovery pattern) | absent (one output path per config, `--overwrite` refusal guard) | none |
| `phase3_campaign.py` | absent (no raises between compute and write; `campaign_summary.json` written last, after every per-arm file) | absent (filenames keyed by `(d70, source)`; no subset CLI flag exists) | none |
| `gsa_study.py` | absent (no raises or asserts at all) | absent (`_paths(slug)` per config; `--plot-only` reads and never writes a JSON) | none |
| `convergence_study.py` | absent | absent (slug per config) | none |

**One incidental finding while wiring the figure stage**, worth recording because it
is the same class of silent-skip: a driver entry whose `requires` path can never
exist becomes dead code. `docs/decisions/adr0033-gsa-study.json` does not exist (the
GSA evidence is per-section, `adr0033-gsa-study-kp58_8_matrix.json` and
`...-kp60_0_matrix.json`), so the GSA figure driver skipped silently and its nine
figures went unchecked until the staleness gate caught them on the next pass. A test
now forbids a `docs/`-rooted `requires` path that does not exist.

## Not resolved

* **H11**, the 10 typeset em dashes in four msc-thesis chapters. Flagged rather than
  fixed: they are prose I was not asked to touch, and the repository's own contract
  says to flag inconsistencies rather than smooth them. Six of the ten sit in the
  uncommitted Ch. 7 block written by the preceding step.
* **msc-thesis carries uncommitted work** from the epistemic-bracket-synthesis step
  (Ch. 5 and Ch. 7). It was neither committed nor pushed here, per the repository's
  Overleaf-mirror rule.
* **The GSA evidence JSONs are per-section**, so `docs/decisions/adr0033-gsa-study.json`
  does not exist; the figure stage's `requires` now points at
  `adr0033-gsa-study-kp58_8_matrix.json`. Worth knowing before someone writes another
  path against the un-suffixed name.
