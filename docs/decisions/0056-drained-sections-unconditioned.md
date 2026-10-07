# ADR-0056: The drained sections' as-if-undrained deliverable is not conditioned on the 2016 survival

Date: 2026-10-07

## Status
Accepted (owner decision, 2026-10-07, answering annotation A13 of Joost Pol on
the pre-Green-Light thesis). Amends ADR-0036 and ADR-0038 **for KP 58.8 and
KP 60.0 only**: the adopted annual piping branch there is the Phase 1 prior, for
both criteria; at KP 57.4 and KP 62.0 the adopted branch stays the ADR-0036
posterior. No kernel, config, prior, persisted sweep, Phase 2 posterior or
`rq4_annual.csv` row changes: the adopted rows at the drained sections are the
existing `matrix`/`prior` rows of that table. The persisted Phase 2 posteriors
at KP 58.8/60.0 remain, relabelled as the update *as if the levee had neither
berm nor drain*.

---

## Context

Since ADR-0036 the adopted piping branch at every section is the Phase 2
posterior: the prior rows that survive the recorded 2016 flood replayed through
the modelled section. At KP 58.8 and KP 60.0 the modelled section is the 1998
foundation **as if undrained** (no berm, no drain; `drained-sections-scope-study.md`),
because the drains' function is unrecorded. The update was informative only
there: it rejected 3.81 % and 0.226 % of the matrix prior, and 16 rows and none
at the other two sections.

Pol (annotation on p. 5 of the 11 September version, beside the update at the
drained sections): *"you could also argue that you shouldnt apply conditioning on
the cases with drains."*

The levee that survived in 2016 had berms and toe drains, built 1999 to 2003
(`docs/tokachi_bep_inputs_provenance.md` 3.2). The likelihood of the observation
given a foundation therefore depends on the works. `drained-section-conditioning-study.md`
measured it on the same 10^5 rows (theta and the L uniforms aligned, gated):

| Likelihood used | KP 58.8 rejected | KP 60.0 rejected | static rejected (58.8 / 60.0) | LR (58.8) |
|---|---|---|---|---|
| levee as if it had neither berm nor drain (adopted until now) | 3.813 % | 0.226 % | 28.3 / 5.17 % | 1.34 |
| measured berm, inert drain | 0.899 % | 0.014 % | 11.9 / 0.80 % | 1.13 |
| berm, 40 % exit-gradient relief | 0.391 % | 0.007 % | 7.7 / 0.55 % | 1.08 |
| berm, 60 % relief | 0.011 % | 0.001 % | 0.37 / 0.03 % | 1.00 |
| berm, 80 % relief | 0 | 0 | 0 / 0 | 1.00 |

Relief acts on the gate both criteria share, so every working drain only raises
the survival probability. The as-if-undrained update conditions the deliverable
on the survival of a structure that did not exist in 2016; the inert-drain berm,
the least protective configuration that did exist, rejects a quarter as much at
KP 58.8 and a sixteenth at KP 60.0.

## Decision

1. At KP 58.8 and KP 60.0 the adopted as-if-undrained piping branch is the
   **prior**, for the transient criterion and, wherever a static annual value is
   reported, for the static criterion too. KP 57.4 and KP 62.0 keep their
   ADR-0036 posteriors (both criteria in their own terms, ADR-0055).
2. The as-if-undrained update is reported as the **upper bound** on what the 2016
   survival could teach about those foundations, and the inert-drain berm update
   as the most that the levee that actually stood could teach.
3. Numbers of record: the adopted Phase 3 rows are the `matrix`/`prior` rows of
   `results/system_integration/phase3/rq4_annual.csv` at KP 58.8/60.0 and the
   `matrix`/`posterior` rows at KP 57.4/62.0; their hazard-sampling intervals,
   ranks, two-stratum terms and the drained-section readings are in
   `drained-section-conditioning-adopted.json` (driver
   `scripts/results_annotations_study.py adopted`, gated row for row against
   those production rows).

## Alternatives Considered

### Keep the as-if-undrained update (status quo)
It maximizes the information taken from the survival, applied to a structure
that did not exist when the survival was observed. Rejected: the deliverable is
an "as if the drains did nothing" statement about the foundation, and the
conditioning should not import a survival the works produced.

### Condition on the measured berm with an inert drain
The most a survival of the levee that stood could teach (0.90 % / 0.014 %
rejected). Historical annual system 6.67e-3 at KP 58.8 against 6.85e-3 prior
(−2.7 %) and 0.321e-3 against 0.322e-3 at KP 60.0. Rejected as the adopted
choice: it still assumes the drain did nothing, so it is itself an upper bound
on information, and the difference from the prior is far inside the
hazard-sampling interval.

### Marginalize over drain roles
No record supports weights over inert, relieving or filtering roles. Any
weighting lies between the inert-drain row and the prior.

## Rationale
The prior is consistent with the deliverable's own definition and is the
conservative choice for the failure probability; the information it forgoes is
measured and small on any configuration that existed.

## Consequences
- Historical annual system probability: KP 58.8 6.18e-3 → **6.85e-3** (+11 %),
  KP 60.0 0.315e-3 → **0.322e-3** (+2 %); +4 K 35.7e-3 → **38.3e-3**,
  4.22e-3 → **4.28e-3**. No rank among the four sections and no leading
  mechanism changes in either climate.
- RQ2: with the drained sections unconditioned, the 2016 survival constrains no
  section materially (largest rejection 16 rows, at KP 57.4). The as-if-undrained
  3.8 % rejection, its parameter shifts and the likelihood ratio 1.34 are upper
  bounds; on the levee that stood they are at most 0.9 %, and 1.13.
- The annual steady-state over transient factor no longer changes materially on
  the update: it is the prior factor at the drained sections (1.82 / 3.32
  historical) and each criterion's own update at KP 57.4/62.0 (1.99 / 2.68).
- Companion studies that annualise "the posterior" at the drained sections
  (conductivity, foreland, gravel, initiation) describe the as-if-undrained
  update; their prior-side arms are the adopted analogue.

## References
- `docs/decisions/drained-section-conditioning-study.md` and its JSON
- `docs/decisions/drained-sections-scope-study.md`; ADR-0036, ADR-0038, ADR-0050
- Pol, annotation A13 (round-2 triage, `pol_feedback_2026-10-06/annotations_triage.md`)
