# Study note: first-breach shares under the alternative readings (final audit, session 1)

Date: 2026-10-11. Status: **Part 1 pre-registered** before the annual
composition was run; Part 2 records the outcome.
Driver: `scripts/first_breach_alternatives_study.py` (`trace`, `annual`).
Evidence: `first-breach-alternatives-study.json`. Companion only: no default,
config, prior, kernel, persisted sweep, posterior or production annual result
changes. Whether the thesis reports alternatives on this share is the owner's
decision (it changes what a reported quantity means).

## Part 1. Pre-registration

### 1.1 The question

ADR-0057 made the first-breach split the reported mechanism share of the
adopted configuration: a year in which piping and overflow would both fail is
credited to the mechanism that breaks through first on the canonical flood
scaled to its peak. The alternative readings the thesis uses to say whether
piping "leads" (thesis Table 7.2, Figure 7.3, Sections 7.2, 7.2.1, 7.4, 7.6, 9.1,
the Summary, C.3, C.4) are still ranked by the summed-contribution share
`P_BEP / (P_BEP + P_overflow)`, which counts a both-fail year once for each
mechanism. The thesis therefore uses one word for two quantities (final-audit
first scan, section 2). This study puts every alternative on the adopted
definition, with the adopted conditioning of ADR-0056, so that the two can be
compared cell by cell.

### 1.2 What is computed

For each alternative and section, `pi(h)` (the probability that the pipe breaks
through before the overflow model fails, both failing at stage `h`) from the
alternative's own failing rows, by the ADR-0057 machinery
(`results_annotations_study._time_order_section`: M7 re-run with trajectory
storage on up to 4,000 failing rows per stage, gated bit for bit against M8's
end state; seeded overflow failure times from cumulative work). Rows: the
alternative's own 2016 survivors at KP 57.4 and 62.0, all rows at KP 58.8 and
60.0 (ADR-0056). Then the first-breach split year by year in the production
annualisation with the alternative's curve swapped in, with the member-block
hazard bootstrap (10,000 replicates, warming draw stratified by pattern).

Alternatives: bulk d70; the three conductivity means (matrix) and the same
three under bulk; foreland credit half and full; critical head x 1.8 (Dutch
gravel); the seepage-length prior bounded at 0.85 of its mean; the steady-state
criterion on the same head and gate (instantaneous growth: breach when the exit
is open and the erosion head first exceeds `H_c`; before any update, as thesis
Table 7.4); correlation lengths 100 and 40 m (n_eff = 2 and 5 independent
stretches; the segment's pipe breaks through at its earliest failing stretch,
`P(T_seg < t) = 1 - (1 - p F(t))^n`).

Gates (any failure stops the run): the adopted re-trace reproduces the
committed `time_order` of `drained-section-conditioning-adopted.json` exactly
(same seed and draw order; **held** at the trace step, before this note); every
breach re-run reproduces M8's end state; the adopted table's system probability
and first-breach share are reproduced; every alternative's annual system
probability equals its committed value; the hazard cache is unchanged.

### 1.3 Predictions

- **F1.** Every cell whose summed piping share lies below 0.4 or above 0.6
  keeps its leading mechanism under the first-breach share.
- **F2.** Where the two differ, the first-breach share lies below the summed
  share at KP 62.0 (where overtopping wins the race above the bank) and above
  it at KP 57.4 (where the pipe usually wins).
- **F3.** The thesis's universals about the alternatives hold under the
  first-breach share: no section-and-climate cell keeps its leading mechanism
  across the matrix conductivity bracket; half the foreland credit leaves
  piping leading in none of the eight cells; the bulk reading gives overflow the
  lead in five of the eight cells.
- **F4.** The steady-state criterion gives piping the first-breach lead at
  KP 62.0 under warming (share above 0.5), because instantaneous growth breaks
  through as soon as the erosion head exceeds the critical head, before
  overtopping erosion has accumulated.
- **F5.** The 40 m correlation length gives piping the first-breach lead at
  KP 62.0 under warming; the 100 m length does not.
- **F6.** The critical head x 1.8 keeps piping leading in six of the eight
  cells under the first-breach share, losing KP 62.0 historically, with
  KP 62.0 under warming overflow's.

A prediction that fails is reported as failed.

## Part 2. Outcome

Run 2026-10-11 and 12 on the production artifacts and the persisted
alternative sweeps (matrix and bulk ADR-0048 conductivity arms and their
Phase 2 replays, the ADR-0052 foreland arms, the gravel-ladder arms of
`gravel_grading_resistance_study.py`, the uniformity-term arms of
`time_dependence_factor_study.py`), 10,000 member-block hazard resamples with
the warming draw stratified by pattern. Gates, all passed: the adopted re-trace
reproduces the committed `time_order` of
`drained-section-conditioning-adopted.json` stage by stage; the adopted table's
system probability and first-breach share are reproduced to the six
significant figures the committed record holds; every breach re-run
reproduces M8's end state and loses no breach; every alternative's annual
system probability reproduces its committed value (conductivity and foreland
cells of `drained-section-conditioning-alternatives.json` and the bulk
conductivity records, the gravel cells of `gravel-grading-resistance-study.json`,
`seepage-length-lower-tail-adopted.json`, the uniformity cells of
`uniformity-coefficient-study.json`, and the 100 and 40 m factors); the
hazard cache is unchanged. Three groups of arms were added after the
pre-registration and before their annual composition: the bulk reading's two lower conductivity
means and the rest of the gravel ladder (1.25, 1.5, 2.2, 2.7, which the thesis
figure draws), and the uniformity-term arms with their prior baseline.

### 2.1 Leading mechanism, summed against first-breach

No cell of any alternative changes its leading mechanism between the summed
and the first-breach share (`orderings`). Values move most at KP 62.0 under
warming (summed / first-breach):

| Alternative | KP 62.0 +4 K | piping leads in, of 10,000 resamples |
|---|---|---|
| adopted | 0.48 / 0.39 [0.35, 0.44] | 0 |
| regional-upper conductivity | 0.89 / 0.99 [0.98, 0.99] | 10,000 |
| steady-state criterion (before any update) | 0.69 / 0.90 [0.89, 0.91] | 10,000 |
| correlation length 100 m | 0.61 / 0.56 [0.52, 0.61] | 9,990 |
| correlation length 40 m | 0.73 / 0.78 [0.75, 0.81] | 10,000 |
| seepage tail bounded at 0.85 | 0.38 / 0.24 [0.21, 0.28] | 0 |
| landside-toe conductivity | 0.23 / 0.12 | 0 |
| gravel x 1.8 | 0.09 / 0.02 | 0 |

Elsewhere the two measures differ by at most 0.10 in any cell, at KP 57.4
under warming (bulk with the regional-upper mean 0.81 / 0.92; adopted
0.89 / 0.96), where the pipe usually wins the race.
Counts the thesis states hold on the first-breach share: the bulk reading
gives overflow the lead in five of the eight cells; the field-test mean removes
the piping lead in seven (overflow leads five, two have no computed failure);
the landside-toe test reverses KP 57.4 under warming (0.26) and KP 62.0
historically (0.45; piping leads in 3,630 of 10,000 resamples); under bulk the
regional-upper mean restores piping at four of the five overflow-led cells
(KP 62.0 historically at 0.55, piping leading in 7,480); half the foreland
credit leaves piping leading in none of the eight cells; the gravel allowance
keeps piping leading in six of eight (KP 57.4 under warming at 0.55, in 8,181),
and the critical-head multiplier at which overflow first leads at KP 57.4,
58.8 and 60.0 is 2.2 to 2.7 on both measures (`resistance_ladder_break_even`).

### 2.2 Predictions

- **F1 held.** No cell whose summed share lies below 0.4 or above 0.6 changes
  its leader; no cell changes at all.
- **F2 failed.** The direction of the difference is set by how fast the pipes
  of the alternative cross, not by the section. Where pipes are slow (adopted,
  landside-toe conductivity, foreland credit, gravel, bounded tail, the bulk
  regional-upper reading at KP 62.0 under warming) the first-breach share lies
  below the summed share at KP 62.0, as predicted; where they are fast
  (regional-upper conductivity, steady-state criterion, 40 m correlation
  length) it lies above it. At KP 57.4 under warming it is above for the
  adopted and fast readings but below for bulk (0.38 / 0.34) and the
  landside-toe test (0.33 / 0.26).
- **F3 held** (2.1).
- **F4 held.** 0.90 [0.89, 0.91]: an instantaneous pipe breaks through as soon
  as the erosion head exceeds the critical head, before overtopping erosion has
  accumulated.
- **F5 failed in its second half.** 40 m gives piping the lead (0.78); so does
  100 m (0.56 [0.52, 0.61], within 0.1 of one half).
- **F6 held.** Six of eight at x 1.8, KP 62.0 lost in both climates.

### 2.3 The uniformity-term arms (prior, no update at any section)

On the prior at all four sections, as `uniformity-coefficient-study.md` and the
thesis state them, the first-breach share keeps every leader of the summed
share: the tested maximum and the sand-fraction arms change no ordering, and
the whole-matrix arm hands KP 62.0's historical lead to overflow (0.30,
piping leading in 1,073 of 10,000 resamples), as on the summed share. The prior
baseline reproduces the adopted shares to 0.01 (it differs only by the 16
rows the 2016 update removes at KP 57.4).

### 2.4 Consequence

The owner adopted the first-breach share for the alternatives (ADR-0058). In
the thesis: Table 7.2 and Figure 7.3 are on the first-breach share with the
adopted conditioning; the KP 62.0 warming paragraph of Section 7.2 and the
static-criterion sentence of 7.4 quote first-breach values (0.56, 0.78, 0.99,
0.90, 0.24); the C.3 resistance figure draws first-breach shares on the
adopted conditioning; the two values with no first-breach counterpart (the
alternate canonical event, 0.36, and the rating-seam companion, 0.44, both on
the summed share) and the actual-waveform screen (0.48 to 0.41) are named as
summed shares. No stated ordering or count changed.
