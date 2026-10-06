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

Gates (all held): the closed-form gate reproduces every stored 2016 initiation
flag in all 18 section-configuration replays (as if undrained, bulk, measured
berm, berm with 20 to 80 % relief); no breach lies outside initiation or
outside same-head failure; the no-breach posterior curve rebuilt from row
weights is identical to production (p_raw exactly, fit to 1e-12); the
annualisation reproduces the production table (912 rows, 20 fields) and the
rebuilt no-breach arm reproduces it field for field; surface-only segments and
the hazard cache are untouched.

### 4. What the model expected at the exit in 2016 (comment 7)

Matrix reading, prior, the replayed record. Decomposition of every prior
foundation's 2016 outcome on one head and one gate:

| | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| Exit opened (initiation), as if undrained | **0.664** | **0.996** | **0.993** | **0.396** |
| no exit | 0.336 | 0.0043 | 0.0070 | 0.605 |
| exit opened, erosion head at the peak not above H_c (pipe stalls) | 0.660 | 0.712 | 0.941 | 0.396 |
| fails the steady-state rule, survives the transient one (held only by duration) | 0.0037 | 0.245 | 0.049 | 0 |
| breach | 0.00016 | 0.038 | 0.0023 | 0 |
| median hours with the exit open, initiated rows | 2 | 6 | 7 | 1 |
| measured berm, inert drain | | 0.993 | 0.986 | |
| berm, 20 / 40 / 60 / 80 % exit-gradient relief | | 0.92 / 0.47 / 0.014 / 0 | 0.88 / 0.39 / 0.009 / 0 | |

Initiation is identical under the bulk d70 reading (not a function of d70)
and barely moves under the no-breach update (breaches are a subset of
initiations: 0.664 / 0.996 / 0.993 / 0.396 among survivors). Toe overpressure
over-predicted by a factor f (as if undrained): f = 1.13 gives 0.42 / 0.98 /
0.97 / 0.22, f = 1.5 gives 0.047 / 0.73 / 0.68 / 0.020, f = 2 gives 0.0006 /
0.19 / 0.15 / 0.0002, f = 2.67 gives 0 / 0.007 / 0.005 / 0. A breach in the
model always opens an exit and grows a pipe, so "initiation" here is an exit
that would eject sand.

**Does it match "no boils"?** As if undrained, no: at KP 58.8 and 60.0 the
model gives a 0.4 and 0.7 % chance that no exit opened. It matches on the
berm with 60 % relief or more (99 % no exit), or with toe pressure
over-predicted twofold (81 to 85 % no exit), or if the record is incomplete.
At KP 57.4 and 62.0 the record is unremarkable (34 and 60 % no exit). Within
the model, survival at the drained sections is mostly resistance, not
duration: of the 99.6 % that open an exit at KP 58.8, 71 percentage points
stall because the erosion head never exceeds H_c, 25 survive only because the
flood fell, 3.8 breach. Pol's logic holds in the model: duration explains a
survival only where an exit opened and H_c was exceeded (25 % of KP 58.8's
foundations, 5 % of KP 60.0's, almost none elsewhere).

### 5. Conditioning on no initiation (comment 9)

The strict filter keeps 33,611 / 432 / 696 / 60,448 rows. It selects low
conductivity and heavy, thick, permeable blankets: at KP 58.8 the retained
mean k_aq is 27 % lower, D_bl 29 % higher, k_bl 170 % higher and L 11 %
longer (KP 57.4: -13 / +11 / +37 / +3.5 %; KP 62.0: -15 / +5 / +18 / +3.7 %).
H1 held: no count-qualified stage rises at any section. At the design-grid
stage the transient probability falls from 0.166 to 0.025 at KP 58.8 and from
0.054 to 0.013 at KP 60.0, **but these rest on 11 and 9 failing rows**, below
the R1 floor of 30 (reached only from 41.25 and 43.25 m); the strict posterior
is not quotable at the drained sections' design stages.

A detection probability p_d for an opened exit gives every row the likelihood
0 (breach), 1 - p_d (exit, no breach) or 1 (no exit). H3 held as a theorem:
no probability moves by more than 1/(1 - p_d). Because 99.3 to 99.6 % of the
drained sections' foundations open an exit, a soft observation hardly moves
them: at p_d = 0.5 the KP 58.8 design-grid probability is 0.1649 against
0.1655, at p_d = 0.9 it is 0.160. The no-boil record matters at the drained
sections only if p_d exceeds about 0.98 (figure panel b).

### 6. Annual consequence and mechanism ordering (comments 3 and 9)

Historical annual piping relative to the adopted no-breach posterior, matrix
reading (flood-ensemble intervals in the JSON):

| | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| p_d = 0.5, as if undrained | 0.89 | 0.998 | 0.996 | 0.80 |
| p_d = 0.9 | 0.67 | 0.98 | 0.97 | 0.57 |
| strict, as if undrained | **0.56** | 0.40 (thin) | 0.24 (thin) | **0.49** |
| strict, +4 K | 0.74 | 0.49 (thin) | 0.36 (thin) | 0.63 |
| strict, measured berm | | 0.17 (709 rows) | 0.031 (1,366 rows) | |
| no-breach, berm with 60 % relief | | 0.225 | 0.057 | |
| strict, berm with 60 % relief | | 0.219 | 0.055 | |

H2 held (0.56 and 0.49 at the usable sections). **H4 held: under the strict
filter and under p_d = 0.5 piping keeps the lead in every section-and-climate
cell where it leads now.** KP 62.0 historical falls from a share of 0.79 to
0.65 (piping leads in 98.8 % of resamples); KP 62.0 under warming, a tie with
overflow's point estimate ahead, moves from 0.48 to 0.37. Overflow is zero in
every historical year at KP 57.4 and 60.0, so no piping reduction can hand it
those cells. The relief rows show the other reading of a missing boil: with
working drains the strict filter is nearly vacuous (98.6 and 99.2 % of rows
retained) and the annual piping probability is set by the relief itself.

### 7. Where the update is modest, and why (comment 6)

Each criterion conditioned on 2016 in its own terms (same head and gate,
`time-dependence-factor-study.json`): historical annual system probability
after the update as a share of its own prior, 1.000 / 0.901 / 0.978 / 1.000
for the transient rule against 0.969 / 0.577 / 0.633 / 0.998 for the
steady-state rule; prior rejected 0.016 / 3.81 / 0.23 / 0 % against 0.39 /
28.33 / 5.17 / 0 %. The update is modest for the transient rule only. The
steady-state rule judges the recorded peak as if held indefinitely, so the
survival excludes every foundation whose critical head lies below the
erosion head at that peak; the transient rule credits the 21 hours the river
actually stood above the toe and excludes only foundations fast enough to
cross in them. Under the strict no-initiation observation the two rules keep
exactly the same rows (both require an open exit), and both fall to 0.56 /
0.37 / 0.23 / 0.60 (transient) and 0.63 / 0.50 / 0.31 / 0.66 (steady state)
of their own priors; their annual ratio is then 2.30 / 2.43 / 4.42 / 2.98,
larger than the prior 2.05 / 1.82 / 3.32 / 2.68 because the retained
foundations are less conductive and their pipes slower.

### 8. Where annual probability is earned against 2016 (comment 3)

On the ensemble's own rating axis the 2016 flood is a 75-year event at all
four nodes (40 of 3,000 historical years exceed it; 422 of 5,400 under +4 K,
13 years). The trace-anchored peaks the replay uses carry local effects the
rating does not (rating-anchored peaks 39.02 / 40.78 / 41.65 / 46.64 m against
39.66 / 40.75 / 42.30 / 45.73 m); read on them, the return periods are 150 /
70 / 176 / 20 years, which is where H5's pre-registered 10-to-100-year range
fails at KP 57.4 and KP 60.0. H5's share half held: 100 / 81 / 99 / 99 % of
the historical annual piping probability (adopted posterior; 99.6 / 82 / 90 /
100 % on the trace axis) and 92 to 100 % of overflow's comes from years whose
flood exceeded 2016.

The 2016 peaks stood 1.05 / 1.78 / 1.95 / 2.16 m below the design crest
(design level plus 1.5 m) and 2.67 / 3.63 / 2.81 / 2.91 m below the overflow
model's mean crest (the design crest plus the surveyed bank-height excess,
SD 0.002 to 1.31 m, KP 58.8 the wide one). On the canonical flood at the 2016
peak the overflow model gives 0 / 0.0014 / 0 / 0 and the posterior piping
branch 0.0036 / 0.098 / 0.015 / 3e-7. Piping reaches 1e-2 at 39.82 / 40.13 /
42.20 / 47.05 m, overflow at 41.95 / 41.57 / 44.71 / 48.25 m.

**The coherent answer to comment 3.** Piping carries most of the modelled
annual probability because it engages 1.2 to 2.5 m below overflow, and almost
all of that probability is earned in floods larger than 2016. The 2016 flood
reached the band where piping is possible and overflow is not only at KP 58.8
and 60.0, and even there the transient model expected a breach of only 3.8
and 0.2 % over the record's 21 and 28 hours, so survival had little to remove.
The no-boil record, if complete, would lower annual piping 1.8 to 4.2 times
historically but would not change which mechanism leads, because overflow is
remote. It weakens the absolute piping probabilities, not the ordering. Its
weight is low on the evidence: no inspection record exists, the drained
sections' missing boil is equally what working drains (60 % relief or more) or
a twofold over-prediction of toe pressure would produce, and a soft likelihood
moves the drained sections only if an opened exit would have been seen and
recorded with probability above about 0.98.

### 9. What stays as it was

The adopted observation stays no breach (ADR-0036); strict and soft readings
are named alternatives. The owner holds no patrol or river-ledger record
(asked 2026-10-07). The river-ledger leakage and sand-boil category and the
post-flood inspection results for KP 57 to 62 right bank would settle the
observation's completeness and are the data request. Session 4 (why no
piping) receives the decomposition and the pressure-factor sweep above.

### 10. Corrections made with this study

* ADR-0036 section 2 and `phase2_report.md` sections 4 and 5 point 6: dated
  corrections. The committee's no-boil statements concern the three breach
  sites only; the observation at the study sections is "no boil recorded", of
  unknown completeness. The no-breach baseline is unchanged; the reason it
  stays the baseline is now the evidence above.
