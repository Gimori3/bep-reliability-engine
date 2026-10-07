# Study note: piping credited in floods that overtop the crest (Pol round 2, A19)

Date: 2026-10-07. Status: **Part 1 pre-registered**; Part 2 records the outcome.
Driver: `scripts/results_annotations_study.py crest`. Evidence:
`crest-attribution-study.json`. Companion only until the owner decides on
the reported share; no default, config, prior, kernel, persisted sweep,
posterior or production annual result changes.

## Part 1. Pre-registration

### 1.1 The question

Pol, on the version of 11 September (p. 5), beside the statement that 11.8 % of
KP 62.0's warming piping contribution rests on stages above the section's
"attainable range": *"above the crest level? it would be more realistic to
remove the contribution above the crest in a total risk figure."*

Three crests exist per section, all in `data/processed/uemura_segments/segment_inputs.csv`:
the design crest (design level + 1.5 m), the crest the overflow model carries
(design crest + the surveyed bank excess `crest_err_mu_m`, standard deviation
`crest_err_sigma_m`, 1.31 m at KP 58.8 and below 0.01 m elsewhere), and, at KP 62.0
only, the "attainable maximum" 50.5 m, which is the top of the approved grid
before the ADR-0024 extension and lies 1.86 m above that section's overflow crest.
The per-event "attainable maxima" used by the RQ1 drivers (43.25 / 42.75 / 44.25 /
50.5 m) are not one definition: two are grid tops above the overflow crest
(KP 57.4, 62.0), two sit at or just above the design crest (KP 58.8, 60.0).

### 1.2 What is computed

From the production Phase 3 pipeline (rebuilt and gated field for field against
`rq4_annual.csv`; matrix reading, posterior piping, adopted conductivity, 250 m,
primary surface curves), per section, scenario and simulated year `y`, the
conditional probabilities `p_b(h_y)`, `p_o(h_y)` at that year's peak.

1. The share of every reported piping-only quantity carried by years whose peak
   exceeds (a) the design crest, (b) the mean overflow crest: annual piping, the
   piping share, the piping climate ratio, the annual steady-state over transient
   factor on piping (same-head static branch, prior and own-update), and the
   "earned above the design level" statements of thesis 7.4 and 8.3.
2. Four attributions of each year's system probability `p_sys = 1 - (1-p_b)(1-p_o)`
   (scour is zero at these sections), each summing exactly to `p_sys`:
   overflow first `[p_b(1-p_o), p_o]`; piping first `[p_b, p_o(1-p_b)]`; the
   symmetric split; and a **time-ordered** split, in which the overlap `p_b p_o`
   is divided by `pi(h)`, the probability that the pipe breaks through before the
   overflow model fails, given that both fail under the canonical flood scaled to
   `h`. Plus a crest truncation (piping set to zero in years above the crest).
3. `pi(h)`: pipe breach times from the M7 kernel run with trajectory storage on
   the failing posterior rows at each grid stage where both mechanisms fail
   (subsampled, seeded), gated bit for bit against M8's end state; overflow
   failure times from the cumulative work of the seeded overflow draws on the same
   canonical record, gated against the committed overflow curve at its own levels.
   Both clocks start at the canonical record start.
4. Hazard-sampling intervals (member-block bootstrap, stratified warming draw, the
   production seed) on each attributed share.

### 1.3 Predictions

Descriptive numbers already computed in exploration (not predictions): the shares
of annual piping from years above the design crest (0.35 / 0.08 / 0 / 0.72
historical, 0.78 / 0.27 / 0.19 / 0.84 warming, KP order) and above the mean overflow
crest (0 / 0 / 0 / 0.21 historical, 0.16 / 0.03 / 0 / 0.61 warming); the overflow-first,
symmetric and piping-first piping shares of the KP 62.0 warming system probability,
0.32 / 0.47 / 0.63. The time-ordered quantity `pi(h)` has not been computed.

- **C1 (check).** Every attribution reproduces the production system probability
  exactly; only shares and per-mechanism contributions move.
- **C2.** At KP 62.0, `pi(h) > 0.5` within 0.5 m above the mean overflow crest and
  `pi(h) < 0.5` from 1.5 m above it, because a pipe that started on the rising limb
  can finish before the overtopping erosion accumulates near the crest, but not
  once the river is far above it.
- **C3.** The time-ordered piping share of KP 62.0's warming system probability lies
  between the overflow-first and symmetric values (0.32 to 0.47), and its sampling
  interval excludes 0.5: an overflow lead, not a tie.
- **C4.** At the other seven section-and-climate cells every attribution moves the
  piping share by less than 0.02 from the reported value, and no leading mechanism
  changes.
- **C5.** The annual steady-state over transient piping factor changes by less than
  10 % when years above the mean overflow crest are removed, except at KP 62.0 under
  warming.

A prediction that fails is reported as failed.
