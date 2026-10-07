# ADR-0057: Mechanism shares divide the annual system probability by first breach

Date: 2026-10-07

## Status
Accepted (owner decision, 2026-10-07, answering annotation A19 of Joost Pol on
the pre-Green-Light thesis). Amends ADR-0038 **for the reported mechanism share of
the adopted configuration**: the share is no longer `P_m / sum_j P_j` (the
summed-contribution share, `AnnualizedResult.dominance_share`) but each
mechanism's part of the annual system probability when every year's overlap is
assigned to the mechanism that breaks through first. No composition, system
probability, kernel, curve or persisted result changes; `dominance_share` and
`rq4_annual.csv` are unchanged and remain the ranking measure for the
alternative-reading companions.

---

## Context

The Phase 3 composition is a series system with conditional independence at a
stage (ADR-0038): for a year peaking at `h`,
`p_sys = 1 - (1 - p_b)(1 - p_o)` (scour is zero at the four sections). The share
the thesis reported, `P_b / (P_b + P_o)`, counts a year in which both mechanisms
would fail once for each, so it is not a fraction of the annual failure
probability: their sum exceeds the system probability by 31 % at KP 62.0 under
+4 K and by at most 11 % elsewhere.

Pol (annotation on p. 5 of the 11 September version, beside "rests on
hypothetical stages above the section's attainable range"): *"above the crest
level? it would be more realistic to remove the contribution above the crest in a
total risk figure."* `crest-attribution-study.md` found:

- KP 62.0's "attainable maximum" of 50.5 m is the top of the approved grid before
  the ADR-0024 extension, 2.6 m above the design crest and 1.86 m above the crest
  the overflow model carries (design crest plus the surveyed bank excess).
- Years whose peak exceeds that overflow crest carry 21 % (historical) and 61 %
  (+4 K) of KP 62.0's annual piping contribution, 16 % of KP 57.4's under +4 K,
  and at most 3 % elsewhere. The system probability does not double count them;
  the shares do.
- In a year in which both mechanisms fail, the one that breaks through first is
  measurable: pipe breach times from the M7 kernel on the failing rows (gated bit
  for bit against M8) and overflow failure times from the cumulative work of the
  seeded overflow draws (gated against the committed curve), on the same canonical
  record. The probability that the pipe breaks through first, `pi(h)`, is 0.43 at
  48.0 m at KP 62.0, 0.38 at 49.0 m and 0.09 at 50.5 m, but 0.69 to 0.83 at
  KP 57.4, where piping engages about three metres below the crest.

## Decision

1. The reported mechanism share of the adopted configuration (thesis Table 7.1
   and the RQ3 answer) is the **first-breach split**: per simulated year,
   piping is credited `p_b (1 - p_o) + pi(h) p_b p_o` and overflow
   `p_o (1 - p_b) + (1 - pi(h)) p_b p_o`, which sum exactly to the two-branch
   union; shares divide by that union. `pi(h)` is interpolated linearly in stage
   between the grid levels at which both mechanisms fail.
2. The marginal contributions `P_m` (the annual probability if `m` were the only
   mechanism) are still reported beside the share.
3. The alternative-reading companions keep the summed-contribution share as their
   ranking measure, labelled as such; a cell within about 0.1 of one half is not
   called resolved on it.
4. Every per-event statement at a section's "top attainable stage" names whether
   that stage lies above the overflow crest (it does at KP 57.4 and KP 62.0).

## Alternatives Considered

### Keep the summed-contribution share
Simple and already used throughout. Rejected for the adopted table: it credits
piping in years the levee would overtop first and is not a fraction of the
annual failure probability.

### Overflow-first or piping-first split
Each assumes one mechanism always fails first. The measured `pi(h)` contradicts
both: overflow first at KP 62.0 above its crest, piping first at KP 57.4.

### Truncate piping at the crest (Pol's literal suggestion)
Drops every piping contribution above the overflow crest (KP 62.0 under +4 K:
0.27). Too blunt where the pipe breaks through before the crest is reached, and
the design crest is the wrong limit where the surveyed bank stands higher.

## Rationale
The first-breach split answers the question the share is read as answering,
which mechanism fails the levee in a year it fails, and it does what Pol asked
for the years above the crest without discarding piping where it wins the race.

## Consequences
- Adopted shares (with ADR-0056): historical 1.00 / 0.98 / 1.00 / 0.80,
  +4 K 0.96 / 0.96 / 1.00 / **0.39 [0.35, 0.44]** (KP order). KP 62.0 under +4 K
  changes from a statistical tie (summed 0.48) to an **overflow lead** in every
  hazard resample; no other leading mechanism changes. Shifting the overflow
  failure time by one hour either way gives 0.36 to 0.41 there.
- The system probability, its intervals, the climate ratios and every ranking of
  sections are unchanged.
- `pi(h)` rests on the canonical waveform, conditional independence of the two
  breach clocks at a stage, and the overflow model's hourly damage sum.

## References
- `docs/decisions/crest-attribution-study.md` and its JSON;
  `drained-section-conditioning-adopted.json` (the adopted table)
- ADR-0024 (grid extension and the attainable maximum), ADR-0038, ADR-0056
- Pol, annotation A19 (round-2 triage, `pol_feedback_2026-10-06/annotations_triage.md`)
