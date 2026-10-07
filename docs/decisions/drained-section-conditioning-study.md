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
