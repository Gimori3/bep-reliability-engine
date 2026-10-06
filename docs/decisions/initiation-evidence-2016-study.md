# Study: what the 2016 flood shows about initiation, the update and piping's dominance (Pol comments 3, 6, 7, 9 and 11)

Date: 2026-10-07 (Pol feedback, session 3 of 6)
Status: Part 1 (sources, the observation record and the pre-registration) is
committed on its own, before any conditioning, annual or return-period number of
this study was computed. Part 2 records the outcome.

Evidence: `initiation-evidence-2016-study.json`, driver
`scripts/initiation_evidence_2016_study.py`, gate
`tests/test_initiation_evidence_2016_study.py`. Run artifacts: gitignored
`results/initiation_evidence_2016/`. Comparator of record: ADR-0055 (same head
and same gate). Matrix reading, adopted conductivity, canonical event; KP 58.8
and KP 60.0 as if undrained unless a configuration is named.

No production default, config, prior, kernel, persisted sweep, Phase 2
posterior or Phase 3 table changes. The adopted observation stays no breach
(ADR-0036); the owner was not asked to change it (see Part 2).

## 1. The questions

Joost Pol's written comments on the pre-Green-Light thesis (2026-10-06):

3. "the piping dominance in the total risk: How does this piping-dominance
   relate to the finding that conditioning on 2016 changes the result only
   marginally? And even no initiation in 2016. Was this event so much lower
   than the overflow height?"
6. "the finding that the effect of reliability updating is modest: this holds
   only for the TD model, right?"
7. "suggestion: add probability of initiation from TD model. Does that match
   with the fact that no boils were observed?"
9. "Monte Carlo Accept-Reject filtering: survival is defined as 'no failure'
   but there was even no initiation (no sand boils). So if you would look at
   initiation for the filtering, would that filter out even more parameter
   space?"
11. "please include a graph of the 2016 hydrograph"

What he read (`msc-thesis` tag `pre-greenlight-2026-09-24`): no graph of the
2016 record (Chapter 6 carried only the rejection bar chart, the KP 58.8
fragility update and the peak-shortcut figure); the strict no-initiation filter
as one bar group in that chart; Chapter 3 saying the sections had "no recorded
post-disaster sand boil" (citing the 2017 committee report) and that this
"rests on missing records rather than a dedicated survey".

## 2. What the record says about seepage at KP 57.4 to 62.0 in 2016

Every source on disk was searched (text layer where present, rendered pages
where not).

| Source | What it says about the study sections |
|---|---|
| Tokachi River Levee Investigation Committee (2017), `fns6al0000006eu2.pdf`, 77 pp., partial text layer | The committee was set up for the three breaches only (Satsunai KP 25.0 and 40.5 left, Otofuke KP 21.2 left; foreword). Its no-boil statements (sections 4-3-1, 4-3-4, 4-4, 5-3-1, 5-3-4 and 5-4, printed pp. 4-7, 4-16, 4-17, 5-9, 5-17 and 5-18) all read "決壊区間の上下流において" or "決壊区間及びその周辺" (upstream and downstream of the breach section; the breach section and its surroundings): post-flood field surveys there found no piping (sand boils) and no slope sliding. The Tokachi main stem right bank at KP 57 to 62 does not appear in the report. It does establish that no other levee in the directly managed Tokachi system breached. |
| Zoku Tokachi-gawa Chisuishi (2023), `inr9av000000b2i3.pdf`, 816 pp. | No flood-induced boil or piping on any Tokachi levee in the whole volume (`tokachi_chisuishi_full_review_2026-07-27.md` section 4.1, re-checked here for 漏水, 噴砂, 水防活動, 月の輪, 巡視). Printed p. 574: 2016 flood fighting comprised drainage pumping (Makubetsu, Sarubetsu gate), emergency bank protection by contractors and fire-brigade work in flooded streets; the photographs show no seepage flood fighting and none is located at the study sections. Printed p. 240: a column by a former river-works engineer who "carried out river patrol as an expert" during the August 2016 flood and, around the Obihiro urban area, "did not feel danger despite a considerable rise in water level". A recollection, not a seepage record, and not specific to KP 57 to 62. |
| JSCE 2016 disaster survey summary (`no648_disaster.pdf`) | Tokachi system: breaches on the Satsunai, bank erosion on tributaries; "sand-gravel levees and foundations are strong against seepage failure but weak against lateral and overflow erosion". No observation at the study sections. |
| Kawajiri et al. (2025) | Tokoro River only. |
| River improvement plan draft (2009), `inr9av0000006kyo.pdf` p. 23 | Flood-time patrol is standard practice ("迅速かつ的確な巡視を行う"). The patrol and post-flood inspection results, and the river ledger with its leakage and sand-boil category (`tokachi_basin_document_review_2026-07-27.md` item 7), have not been obtained. |
| Owner (asked 2026-10-07) | Holds no patrol, flood-fighting or river-ledger record for these sections. |

**What is known:** no breach at the four sections (the committee report lists
the only three breaches in the system, none by seepage); no record of
seepage, leakage or a boil at KP 57 to 62 in any source on disk; flood-time
patrols took place in the region, and one patroller recalls no danger around
Obihiro. **What is not known:** whether any inspection looked for seepage at
these sections, and what the river ledger records. The observation is
therefore "no boil recorded", of unknown completeness. It is not "no boil
observed by a survey" (the engine's ADR-0036 section 2 and
`phase2_report.md` sections 4 and 5 said "committee-documented absence of sand
boils at the study reaches"; that scope was already found wrong on 2026-08-28,
project log, but those two documents were not corrected; dated corrections are
added in Part 2). Nor is it "there was no dedicated seepage inspection", the
final thesis's wording since the rewrite: no source establishes that either.

## 3. Pre-registration (written before the numbers below were computed)

Known before this study (persisted records): the transient no-breach update
rejects 0.016 / 3.813 / 0.226 / 0 % of the matrix prior; the strict
no-initiation filter rejects 66.4 / 99.6 / 99.3 / 39.6 % (identical under
bulk); the same-head static rule fails 2016 at 0.39 / 28.33 / 5.17 / 0 %.

Definitions. *Initiation in 2016*: the uplift and heave gate opened at some
time in the replayed record (the stored `initiation` flag; under the ADR-0008
collapse this is `r_e (h_peak - z_toe) > (gamma'_bl / gamma_w) D_bl`). A
*detection probability* `p_d` is the probability that an exit opened in 2016
would have produced a boil that was seen and recorded. The likelihood of the
record "no breach, no boil recorded" for row j is 0 if j breaches, `1 - p_d` if
j initiates without breaching, and 1 otherwise. `p_d = 0` is the adopted
no-breach update; `p_d = 1` is the strict filter.

| | Prediction | Basis |
|---|---|---|
| H1 | Conditioning on no initiation lowers the transient posterior failure probability against the no-breach posterior at every count-qualified stage at KP 57.4 and 62.0. | The gate selects low `r_e (h - z_toe) / D_bl`: low k_aq (which also raises H_c and slows growth), thick or heavy blankets. |
| H2 | At KP 57.4 and 62.0 the strict no-initiation posterior's historical annual piping probability is 0.3 to 0.9 times the no-breach posterior's. | Initiation at the 2016 peak correlates with piping at higher stages only through k_aq, L and D_bl. |
| H3 | Theorem, checked numerically: for any `p_d < 1` every posterior probability lies within `[1 - p_d, 1 / (1 - p_d)]` times the no-breach posterior. So the no-boil record can change any piping probability by more than a factor of two only if an opened exit would have been seen and recorded with probability above one half. | The weights lie in `[1 - p_d, 1]` on the no-breach set. |
| H4 | Under the strict filter at KP 57.4 and 62.0 and under `p_d = 0.5` at all four sections, piping keeps the lead in every cell it now leads, except possibly at KP 62.0. | Overflow is zero or remote except at KP 62.0. |
| H5 | At every section at least 80 % of the historical annual piping contribution (no-breach posterior) comes from years whose peak exceeds that section's 2016 peak, and the 2016 peaks have historical return periods between 10 and 100 years. | Table 7.1: 70 to 100 % comes from above the design level; the 2016 peaks lie 0.28 to 0.66 m below it at three sections. |
| H6 | With exit-gradient relief of 60 % or more on the measured berm, the probability that no exit opened in 2016 is at least one half at both drained sections, against below 1 % as if undrained. | At KP 58.8 `r_e (h - z_toe)` is about 0.95 m against a weight head of about 0.59 m at the prior means. |

Comment 6 needs no new prediction: the static self-update and the transient
update are both persisted (`time-dependence-factor-study.json`); this study
adds the same comparison under the no-initiation observation.

## Part 2: outcome

(Written after the runs.)
