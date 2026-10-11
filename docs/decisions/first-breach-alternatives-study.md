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
