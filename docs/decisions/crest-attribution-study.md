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

## Part 2. Outcome

Run 2026-10-07 on the production artifacts (matrix reading, adopted
conductivity, 250 m, primary surface curves, 10,000 member-block resamples with
the warming draw stratified by pattern). Gates: the rebuilt pipeline reproduces
all four production arms of `rq4_annual.csv` field for field; every breach-time
re-run reproduces M8's end state bit for bit; every overflow re-run reproduces
the model's failure fraction exactly; the union of the interpolated marginals is
within 0.07 % of the interpolated system curve (the largest departure, KP 62.0
under +4 K, is interpolation between grid stages); the hazard cache is
unchanged. Part 2 numbers are the posterior at all four sections, as the
production table was when the study was registered; the adopted configuration
of ADR-0056 changes them only at the drained sections (see 2.5).

### 2.1 Which stages are physically meaningful

| Section | Design level | Design crest | Overflow crest (mean, sd) | Grid "attainable" top | Largest +4 K peak |
|---|---|---|---|---|---|
| KP 57.4 | 39.21 | 40.71 | 42.33 (0.003) | 43.25 | 43.18 |
| KP 58.8 | 41.03 | 42.53 | 44.38 (1.31) | 42.75 | 44.95 |
| KP 60.0 | 42.75 | 44.25 | 45.11 (0.005) | 44.25 | 44.93 |
| KP 62.0 | 46.39 | 47.89 | 48.64 (0.002) | 50.50 | 51.47 |

m T.P. The overflow model's crest is the surveyed bank, 0.75 to 1.85 m above the
design crest. KP 62.0's 50.5 m is a grid top, not a physical limit; above the
bank the channel rating is an extrapolation that ignores spill. The per-event
"top attainable stage" of the RQ1 drivers is a grid convention: it lies above the
overflow crest at KP 57.4 (by 0.9 m) and KP 62.0 (by 1.9 m), at the design crest
at KP 60.0 and 0.2 m above it at KP 58.8.

### 2.2 How much rests on years that overtop

Share of the annual piping contribution from years whose peak exceeds:

| Section | design crest, hist / +4 K | overflow crest, hist / +4 K | years above overflow crest, hist / +4 K |
|---|---|---|---|
| KP 57.4 | 0.35 / 0.78 | 0 / 0.16 | 0 / 7 |
| KP 58.8 | 0.08 / 0.27 | 0 / 0.03 | 0 / 5 |
| KP 60.0 | 0 / 0.19 | 0 / 0 | 0 / 0 |
| KP 62.0 | 0.72 / 0.84 | 0.21 / 0.61 | 2 / 62 |

Removing the years above the overflow crest: the piping climate ratio of
KP 62.0 falls from 10.1 to 5.1 and of KP 57.4 from 15.1 to 12.7 (others within
3 %); the annual steady-state over transient piping factor rises at KP 62.0 under
+4 K from 2.47 to 3.21 and changes by at most 6 % elsewhere. The system
probability does not change in any form: a year above the crest fails by
overflow in the composition whatever piping does.

### 2.3 Which mechanism breaks through first

`pi(h)`, the probability that the pipe breaks through before the overflow model
fails, both failing under the canonical flood scaled to `h` (posterior rows,
up to 4,000 traced per stage):

- KP 62.0: 0.43 at 48.0 m, 0.40 at 48.75 m (0.1 m above the overflow crest),
  0.38 at 49.0, 0.27 at 49.5, 0.16 at 50.0, 0.09 at 50.5, 0.05 at 51.5 m.
  Once the river stands well above the bank, overtopping erosion completes
  within hours of the crest being passed, before most pipes have crossed.
- KP 57.4: 0.69 to 0.83 from 41.5 to 43.25 m. Piping engages about three metres
  below this crest, so most pipes are already far along when the bank overtops.
- KP 58.8: 0.14 to 0.30 below 41 m (only low crest draws overflow there), rising
  to 0.62 at 45.0 m; KP 60.0: 0.61 falling to 0.35 at 46.75 m.

The adopted table (`drained-section-conditioning-adopted.json`) re-traces `pi(h)`
with an independent subsample of failing rows (seed + 1) and the drained sections'
prior rows; at KP 57.4 and KP 62.0 its values differ from these by at most 0.021
and 0.015 (KP 62.0: 0.37 to 0.43 up to 0.4 m above the bank, 0.10 at 50.5 m). The
thesis quotes the adopted run.

### 2.4 The attributions

Piping share of the annual system probability (posterior at all four sections):

| Cell | summed (reported) | overflow first | symmetric | **time-ordered** [95 %] | piping first | truncate at overflow crest |
|---|---|---|---|---|---|---|
| KP 57.4 +4 K | 0.892 | 0.880 | 0.935 | **0.962** [0.939, 0.985] | 0.990 | 0.874 |
| KP 58.8 hist | 0.969 | 0.968 | 0.977 | **0.975** | 0.985 | 0.969 |
| KP 58.8 +4 K | 0.933 | 0.929 | 0.957 | **0.957** | 0.985 | 0.931 |
| KP 62.0 hist | 0.793 | 0.783 | 0.808 | **0.803** [0.673, 0.978] | 0.833 | 0.751 |
| KP 62.0 +4 K | 0.480 | 0.319 | 0.473 | **0.387 [0.346, 0.436]** | 0.628 | 0.266 |

KP 57.4 and KP 60.0 historically and KP 60.0 under +4 K stay at 1.00 (overflow is
zero or below 0.5 %). With the overflow failure time shifted by one hour either
way, KP 62.0 under +4 K is 0.36 to 0.41. Piping leads the time-ordered split in
0 of 10,000 resamples there and in every resample of the other seven cells.

### 2.5 Predictions

- **C1 held.** Every attribution sums to the two-branch union; the system
  probability is unchanged.
- **C2 failed in its first half.** Within 0.5 m above the overflow crest at
  KP 62.0, `pi(h)` is 0.38 to 0.43, not above 0.5: overtopping wins the race even
  near the crest. The second half held (0.16 and below from 1.4 m above it).
- **C3 held.** 0.387 [0.346, 0.436]: between 0.32 and 0.47, interval excluding 0.5.
- **C4 failed in size, held in direction.** At KP 57.4 under +4 K the time-ordered
  share is 0.07 above the reported one and at KP 58.8 under +4 K 0.024 above, both
  toward piping, because the pipe there usually wins; no leading mechanism changes
  outside KP 62.0 under +4 K.
- **C5 held.** Removing years above the overflow crest changes the annual
  steady-state over transient factor by at most 6 % outside KP 62.0 under +4 K
  (+30 % there).

### 2.6 Recommendation and decision

Recommended to the owner, and adopted on 2026-10-07 as ADR-0057: report the
time-ordered (first-breach) split as the adopted mechanism share. With ADR-0056
(drained sections unconditioned) the adopted shares are 1.00 / 0.98 / 1.00 / 0.80
historical and 0.96 / 0.96 / 1.00 / 0.39 [0.35, 0.44] under +4 K; numbers of record
in `drained-section-conditioning-adopted.json`. The alternative-reading shares
keep the summed-contribution measure, labelled.
