# Study: the time effect set beside the input uncertainty (Pol round 2, A24 with A10)

Date: 2026-10-08 (Pol feedback round 2, session 9 of 9)
Status: Part 1 (the question, the common quantity, the sources and the
pre-registration) is committed on its own, before the collation of Part 2 is
run. Part 2 records the outcome.

Evidence: `time-effect-in-proportion-study.json`, driver
`scripts/time_effect_in_proportion.py`, gate
`tests/test_time_effect_in_proportion.py`, figure
`docs/figures/time_effect_in_proportion.png`.

No production default, config, prior, kernel, persisted sweep, Phase 2
posterior or Phase 3 table changes, and nothing is re-run. The driver only reads
evidence JSON already committed in `docs/decisions/` and sets its values on one
quantity.

## 1. The question

Joost Pol annotated the 11 September 2026 thesis. On its Summary (p. 5), beside
"Climate-resilient levee assessment must explicitly account for both loading
duration ...", he wrote: "Give the factor 1-6 due to duration only, you could
also conclude that it is not very important. Measuring permeability has more
impact." On p. 4, beside "duration alone produces a factor of one to about
six": "I think this is an important result."

Since ADR-0055 the time effect is measured on one head and one gate: per design
flood a factor of 2.3 to 6.9 (Delta beta 0.50 to 0.81), per year 1.8 to 3.3 on
the historical annual system probability (`time-dependence-factor-study.md`).
The thesis reports the input alternatives where each belongs (Chapters 5 and 7,
Table 8.2) but never sets the size of the time effect beside them on one
quantity, and its Table 8.2 explicitly does not rank effects because its rows
use different quantities. The owner decided on 2026-10-08 that the conclusions
should state the time effect in proportion to the input uncertainty; this study
supplies the single quantity on which that comparison is fair.

## 2. The common quantity and the rows

**Quantity of record:** the historical annual system failure probability of each
of the four investigated 200 m segments, matrix reading, adopted conductivity,
correlation length 250 m, primary surface curves, canonical event, on the
adopted conditioning (ADR-0056: 2016 update at KP 57.4 and 62.0, prior at the
drained sections). The +4 K annual system probability is reported beside it.
For every row the reported number is the factor `P(alternative) / P(adopted)`
at each section.

| Row | Alternative | Source (committed JSON) |
|---|---|---|
| Criterion | steady-state criterion (instantaneous growth on the same head and gate) instead of the time-dependent one | `time-dependence-factor-study.json`, `annual.matrix.paired_comparisons["I-prior / T-prior"]` (prior on both sides; the thesis states that each criterion's own update changes it by less than 3 % at KP 57.4 and 62.0) |
| Conductivity | prior mean replaced by the six-test field mean, the landside-toe test, the regional upper value | `drained-section-conditioning-alternatives.json`, `system_by_arm` |
| Grain size | bulk instead of matrix d70 | same, `bulk_over_matrix_system` |
| Foreland | half and full credit of `lambda_out_eff` in the Sellmeijer length | same, `foreland_half_system_ratio`, `foreland_full_system_ratio` |
| Gravel | shared H_c multiplied by 1.8 (Dutch practice) | `gravel-grading-resistance-study.json`, `annual.cells`, on the adopted conditioning |
| Drains | measured berm with an inert drain; berm with 80 % exit-gradient relief (KP 58.8 and 60.0 only) | `drained-section-conditioning-adopted.json`, `drained_readings` |
| Seepage-length tail | L bounded at 0.85 of the adopted length | `seepage-length-lower-tail-adopted.json`, `annual` `t0.85` against `t0.00` |
| Flood shape | the shorter alternative canonical event | `canonical-shape-sensitivity.json`, `phase3.sections` (prior basis, as published) |
| Correlation length | 40 m instead of 250 m (five independent stretches per segment) | `drained-section-conditioning-alternatives.json`, `lambda_ac_factors` |

Not on this quantity, and therefore not rows: the OYO toe-pressure diagnostic
(per design flood only, `why-no-piping-2016-study.json`), the far-extrapolated
uniformity term (no survival update; Table 8.2 carries it), the waveform screen
(unconverged in the historical tail). A zero alternative probability (no
computed failure in any simulated year) is an unbounded factor, reported as
such, never as a number.

Separate alternatives are never multiplied into a joint factor: no joint
distribution over them exists.

## 3. Pre-registration (written before Part 2 was computed)

The thesis already prints several of these values row by row (Chapter 7,
Table 8.2), so some outcomes are known in part. What is fixed here is the
comparison rule, so the verdicts cannot be tuned after the collation. "The time
effect at a section" is the criterion factor at that section and climate;
"larger than the time effect" compares `|log10 factor|`.

- **P1.** Historically, the conductivity bracket (largest over smallest arm,
  adopted included) exceeds ten times the time effect at every section where
  both ends are computed, and is unbounded at the others.
- **P2.** Historically, the largest displacement over the four sections of each
  of the grain-size, gravel, full foreland credit and 80 % drain-relief rows
  exceeds the largest time effect (at any section) by at least a factor of
  three in `|log10|`, i.e. each can move the annual probability by at least
  about thirty times or to no computed failure.
- **P3.** Historically, the seepage-length tail and the shorter canonical event
  each displace the annual system probability by less than the time effect at
  every section.
- **P4.** Historically, the 40 m correlation length raises the annual system
  probability by more than the time effect at at least one section.
- **P5.** Under +4 K, the conductivity bracket exceeds the time effect at every
  section where both ends are computed (no factor of ten claimed: the warming
  spans are narrower).
- **P6.** The time effect lowers the annual probability at every section in both
  climates; no tested input alternative changes the sign of the criterion
  comparison (nesting; already a theorem, recorded as a consistency check).

Part 2 states for each whether it held, failed, or partly held, and the thesis
quotes the outcome whatever it is.
