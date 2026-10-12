# Study note: should the drained sections' survival condition an undrained model? (Pol round 2, A13)

Date: 2026-10-07. Status: **Part 1 pre-registered**; Part 2 records the outcome.
Driver: `scripts/results_annotations_study.py drained`. Evidence:
`drained-section-conditioning-study.json`. Companion until the owner decides;
no default, config, prior, kernel, persisted sweep, posterior or production annual
result changes here.

## Part 1. Pre-registration

### 1.1 The question

Pol, p. 5, beside the update at the drained sections: *"you could also argue that
you shouldnt apply conditioning on the cases with drains."*

The adopted posterior at KP 58.8 and 60.0 conditions the as-if-undrained foundation
on survival of the 2016 record replayed through a levee without berm or drain. The
levee that survived in 2016 had both: the berms and toe drains were built in 1999 to
2003 (`docs/tokachi_bep_inputs_provenance.md` 3.2). The survival likelihood of a
foundation therefore depends on what the drains did, which is unrecorded
(`drained-sections-scope-study.md`). An inert drain on the measured berm gives the
smallest survival probability any physically present configuration can give; any
relief raises it (relief acts on the shared gate, ADR-0050).

### 1.2 What is computed

For KP 58.8 and 60.0, matrix reading, adopted conductivity, the same 10^5 rows:

1. The as-if-undrained foundation (the deliverable) under three conditionings:
   the prior (no update), the berm-inert likelihood (rows that survive 2016 on the
   measured berm with an inert drain, ADR-0050 replay; rows aligned by theta and the
   L uniforms, gated), and the adopted as-if-undrained update. Also the berm with
   40, 60 and 80 % relief as likelihoods.
2. For each: rejected share, retained parameter means, design-grid transient and
   same-head static probability, likelihood ratio between the criteria, annual
   system and piping probability (production pipeline, gated), mechanism shares,
   rank among the four sections, climate ratio, the annual steady-state over
   transient factor on each criterion's own update, with hazard-sampling intervals.
3. What every place that quotes the update would read under the prior at the drained
   sections: RQ2, the likelihood ratio, the parameter shifts, the annual tables and
   dominance.

### 1.3 Predictions

The prior and adopted-posterior annual values already exist in `rq4_annual.csv`
(matrix/prior and matrix/posterior arms); they are not predictions.

- **D1.** Conditioning the as-if-undrained foundation on the berm-inert likelihood
  rejects at most 1.0 % at KP 58.8 and 0.02 % at KP 60.0, and its historical annual
  piping probability lies within 4 % of the prior at KP 58.8 and within 0.5 % at KP 60.0.
- **D2.** With the drained sections on the prior, no leading mechanism and no rank
  among the four sections changes in either climate.
- **D3.** With the drained sections on the prior, the largest transient rejection at
  any section is below 0.1 % of the prior, so no section is updated materially by the
  standard of thesis 6.2 (at least 500 rejected rows).
- **D4.** The annual steady-state over transient factor after each criterion's own
  update at KP 58.8 stays above 1.1 under the berm-inert likelihood, since the static
  rule still rejects about 12 % there.

A prediction that fails is reported as failed.

## Part 2. Outcome

Run 2026-10-07. Gates: the berm and relief arms carry the adopted rows (theta
identical, L a constant multiple of the adopted L at every row); the rebuilt
as-if-undrained arm reproduces the production posterior rows and the rebuilt
prior arm the production prior rows; the hazard cache is unchanged.

### 2.1 Per flood (matrix reading, design-grid stage 41.00 / 42.75 m)

| Likelihood | rejected, 58.8 / 60.0 | static rejected | LR, 58.8 / 60.0 | P_trans design, 58.8 / 60.0 |
|---|---|---|---|---|
| prior (none) | 0 / 0 | 0 / 0 | 1 / 1 | 0.197 / 0.0558 |
| berm, inert drain | 0.899 % / 0.014 % | 11.9 / 0.80 % | 1.13 / 1.01 | 0.190 / 0.0557 |
| berm, 40 % relief | 0.391 % / 0.007 % | 7.7 / 0.55 % | 1.08 / 1.01 | 0.194 / 0.0557 |
| berm, 60 % relief | 0.011 % / 0.001 % | 0.37 / 0.03 % | 1.00 / 1.00 | 0.197 / 0.0558 |
| berm, 80 % relief | 0 / 0 | 0 / 0 | 1 / 1 | 0.197 / 0.0558 |
| as if undrained (adopted until now) | 3.813 % / 0.226 % | 28.3 / 5.17 % | 1.34 / 1.05 | 0.166 / 0.0537 |

Retained means move by at most 0.9 % under the inert-drain berm likelihood
(k_aq −1.0 %, C_e −0.9 %, L +0.3 % at KP 58.8) against −3.1 %, −2.8 % and +1.0 % as
if undrained.

### 2.2 Annual (historical; +4 K in brackets), 10^-3 per year

| Conditioning at the drained sections | KP 58.8 system | KP 60.0 system | rank of four | leading |
|---|---|---|---|---|
| prior | 6.85 (38.3) | 0.322 (4.28) | 1 and 4, both climates | piping |
| berm, inert-drain likelihood | 6.67 (37.6) | 0.321 (4.27) | same | piping |
| as if undrained (adopted until now) | 6.18 (35.7) | 0.315 (4.22) | same | piping |

Hazard-sampling intervals: prior 6.85 [4.96, 8.94] and 0.322 [0.17, 0.50]
historical. The ranks hold in at least 99.8 % of resamples in every row.

### 2.3 Predictions

- **D1 held.** The inert-drain berm likelihood rejects 0.899 % and 0.014 %; its
  historical annual piping is 2.7 % and 0.3 % below the prior.
- **D2 held.** No leading mechanism and no rank among the four sections changes.
- **D3 held.** With the drained sections on the prior, the largest transient
  rejection anywhere is 16 rows (0.016 %, KP 57.4).
- **D4 held.** The annual steady-state over transient piping factor at KP 58.8 on
  each criterion's own inert-drain berm update is 1.54 (fitted static posterior;
  the thesis evaluates the static self-posterior on raw points).

### 2.4 Recommendation and decision

Recommended to the owner, and adopted on 2026-10-07 as ADR-0056: the drained
sections are not conditioned on the 2016 survival, for either criterion. The
as-if-undrained update is reported as the upper bound on what the survival could
teach, the inert-drain berm update as the most the levee that stood could teach.

The adopted annual quantities under ADR-0056 and ADR-0057 are recorded in
`drained-section-conditioning-adopted.json` (part `adopted`): Table 7.1 values with
intervals, first-breach shares, ranks among the four and among the 114 nodes,
the two-stratum decomposition, the drained-section readings (as if undrained,
berm, berm with 80 % relief, all unconditioned), the sixty-year non-breach check
(composed historical piping 8.34e-3, 0.50 expected failures in sixty years,
P(none) 0.61, exclusion limit 4.87e-2 = 5.8 times the composed value).
`drained-section-conditioning-alternatives.json` (part `alternatives`) re-reads
the alternative-reading companions with the prior side at the drained sections:
the summed-contribution shares change by at most 0.01; the KP 58.8 historical
conductivity span widens from 87 to 165 because no update trims the upper arm;
the bulk reading lowers the annual system probability 1.5 to 34 times at seven
cells (was 31) and 240 times at KP 57.4 historically; the 40 m correlation
length multiplies it by 1.9 to 4.4.

With the adopted conditioning the six warming patterns' own annual system
probabilities span factors of 3.08 to 6.23 at the four sections (was 3.16 to 6.23),
and resampling the six patterns instead of conditioning on them would widen the
warming intervals 1.65 to 3.10 times (was 1.65 to 2.89; KP 58.8 carries the
largest factor because its stratified interval is the narrowest). Two-stratum
terms at the drained sections, historical: long-year share 0.892 [0.84, 0.93]
and 0.971 [0.90, 1.00]; long-year concentration 155 [99, 257] and 918 [250, 10,600];
frequency share of ln R 0.50 [0.42, 0.59] and 0.375 [0.29, 0.48].
