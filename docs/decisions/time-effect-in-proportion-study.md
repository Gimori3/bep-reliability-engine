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

## 4. Outcome (Part 2, computed after Part 1 was committed in `3bd8b3c`)

Factors `P(alternative) / P(adopted)` on the historical annual system
probability (KP 57.4 / 58.8 / 60.0 / 62.0). "none" is no computed failure in any
simulated year, an unbounded factor; a dash means the row does not apply.

| Alternative | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| **Steady-state criterion (the time effect)** | **2.05** | **1.82** | **3.32** | **2.68** |
| Conductivity: field-test mean | none | 0.029 | none | 0.22 |
| Conductivity: landside-toe test | 0.0047 | 0.11 | 0.13 | 0.38 |
| Conductivity: regional upper value | 5.4 | 4.7 | 38.7 | 14.2 |
| Grain size: whole sand-gravel (bulk) | 0.0042 | 0.029 | 0.22 | 0.22 |
| Gravel allowance, H_c x1.8 | 0.020 | 0.12 | 0.0057 | 0.24 |
| Foreland credit, half | none | 0.029 | none | 0.33 |
| Foreland credit, full | none | 0.028 | none | 0.23 |
| Measured berm, drain inert | - | 0.51 | 0.18 | - |
| Measured berm, 80 % relief | - | 0.029 | none | - |
| Seepage length bounded below | 0.51 | 0.70 | 0.60 | 0.61 |
| Shorter canonical flood | 0.58 | 0.66 | 0.49 | 0.58 |
| Correlation length 40 m | 3.69 | 2.61 | 4.37 | 3.29 |

Conductivity span (largest over smallest arm): unbounded / 165 / unbounded / 66
historically; 23 / 45 / 2716 / 8.0 under +4 K. The time effect under +4 K is
1.60 / 1.64 / 2.59 / 1.65.

**Verdicts.**

- **P1 held.** The historical conductivity span is 90 and 24 times the time
  effect at KP 58.8 and 62.0 and unbounded at KP 57.4 and 60.0.
- **P2 held.** The largest historical displacement is 240-fold for the grain
  size (KP 57.4), 177-fold for the gravel allowance (KP 60.0), and no computed
  failure for full foreland credit (KP 57.4, 60.0) and 80 % drain relief
  (KP 60.0), against a largest time effect of 3.3.
- **P3 held.** The seepage-length tail (factors 0.51 to 0.70) and the shorter
  canonical flood (0.49 to 0.66) displace the annual probability by less than the
  time effect at every section.
- **P4 held,** at all four sections: the 40 m correlation length raises the
  annual probability 2.6 to 4.4 times, more than the time effect at each.
- **P5 held.** Under +4 K the conductivity span is 4.8 (KP 62.0) to 1048
  (KP 60.0) times the time effect.
- **P6 held.** The time effect lowers the annual probability at every section in
  both climates.

**What it means, and what it does not.**

- On the quantity a levee manager would use, the effect of modelling the time a
  pipe needs (a factor of 1.8 to 3.3 historically, 1.6 to 2.6 under +4 K) is
  smaller than the effect of the uncertain aquifer conductivity at every
  section, and at three sections smaller than each of the grain-size, gravel,
  foreland and drain alternatives. Measuring the conductivity at the scale of
  the seepage path and establishing what the drains do would change the
  assessment more than modelling duration does.
- **KP 62.0 is the exception for the piping-side alternatives.** Overflow
  carries part of its annual probability, so the grain-size, gravel and
  foreland alternatives move its system probability only 3 to 5 times
  historically, the size of the time effect there (2.7), and under +4 K, where
  overflow leads, by factors of 1.4 to 1.5, less than the time effect (1.65).
  Its conductivity span (66 historically, 8.0 under +4 K) still exceeds the time
  effect.
- The two choices of the seven piping-favoring ones that act through the
  loading or the path geometry rather than the material, the seepage-length tail
  and the flood shape, are each smaller than the time effect, and the
  correlation length moves the other way by more than it. So the time effect is
  not negligible beside every input: it is of the size of the smaller tested
  alternatives and one to two orders of magnitude below the largest.
- Per design flood the same ordering holds where the sample resolves it: at the
  design-grid levels of KP 58.8 and 60.0 the time effect is 2.28 and 3.88,
  whereas the regional upper conductivity raises the transient probability from
  0.197 to 0.88 and from 0.056 to 0.95 and the field-test mean leaves no failure
  in 10^5 draws (`time-dependence-factor-study.md`, thesis 5.4).
- Separate alternatives are not a joint band and are not multiplied. The OYO
  toe-pressure diagnostic has no annual value and is not a row; per design
  flood it lowers KP 60.0's transient probability 69-fold.
- Conductivity also sets the size of the time effect (F_td x0.22 to 27 per
  flood), so measuring it would show how much duration matters as well.

The thesis carries this as Figure 8.x in 8.4.1 and in the opening of
Chapter 9, 9.2 and the Summary (owner decision, 2026-10-08).
