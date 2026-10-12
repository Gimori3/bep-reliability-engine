# ADR-0058: Alternative readings are ranked by the first-breach share

Date: 2026-10-11

## Status
Accepted (owner decision, 2026-10-11, final thesis audit session 1). Amends
ADR-0057 decision 3 ("the alternative-reading companions keep the
summed-contribution share as their ranking measure"). No kernel, config, prior,
persisted sweep, posterior, curve or annual system probability changes; the
summed-contribution share `P_BEP / sum_j P_j` (`dominance_share`,
`rq4_annual.csv` `share_bep`) stays a persisted field.

---

## Context

ADR-0057 made the first-breach split the reported share of the adopted
configuration and kept the summed-contribution share for ranking the
alternative readings (grain size, conductivity means, foreland credit, gravel
and grading allowances, the bounded seepage-length prior, the steady-state
criterion, correlation length). The thesis consequently used "lead" for two
quantities: the first-breach share in Table 7.1 and the RQ3 answer, the summed
share in Table 7.2, the conductivity and gravel figures and every sentence
saying that an alternative gives or removes piping's lead (final-audit first
scan, section 2).

`first-breach-alternatives-study.md` put every alternative on the adopted
definition, each with its own pipe breach times traced against the overflow
failure times, on the adopted conditioning of ADR-0056 (all gates passed: the
adopted re-trace reproduces the committed time order exactly, every breach
re-run reproduces M8's end state, every alternative's annual system
probability reproduces its committed value). No cell of any alternative changes
its leading mechanism between the two measures; values move, most at KP 62.0
under warming (regional-upper conductivity 0.89 to 0.99, steady-state criterion
0.70 to 0.90, correlation lengths 100 and 40 m 0.61 and 0.73 to 0.56 and 0.78,
bounded seepage tail 0.38 to 0.24).

## Decision

1. Every mechanism share and every statement that a reading gives, keeps or
   removes piping's lead is on the **first-breach share** of ADR-0057, with
   the adopted conditioning of ADR-0056 unless the statement names another.
   Numbers of record: `first-breach-alternatives-study.json` /cells and
   /orderings; the resistance-ladder break-even in
   /resistance_ladder_break_even.
2. The summed-contribution share is reported only where no first-breach value
   exists (the alternate canonical event, whose overflow curve is not
   re-derived, and the overflow rating-seam companion), and is named there.
3. A cell within about 0.1 of one half is not called resolved; the fraction of
   hazard resamples in which piping leads is quoted where a cell is close.

## Alternatives Considered

### Keep the summed share for alternatives, named at every use
Two meanings of one word in one argument, which is what the audit set out to
remove. Rejected by the owner.

### Report both shares in the alternatives table
Most explicit, but doubles a dense table for no change in any ordering.
Rejected.

## Rationale
"Which mechanism leads" should mean the same thing for the adopted inputs and
for every alternative, and the first-breach split is the one that answers it
(ADR-0057). Measured on all alternatives, the change of measure moves values,
not orderings, so no conclusion of record changes.

## Consequences
- Thesis Table 7.2, Figure 7.3 (conductivity bracket) and the C.3 resistance
  figure are re-derived on the first-breach share with the adopted
  conditioning; the KP 62.0 warming paragraph of Section 7.2 quotes first-breach
  values.
- `scripts/adopted_alternatives_figures.py --share first_breach` draws the
  conductivity figures; the gravel ladder uses the study's break-even.
- ADR-0057 decision 3 carries a dated pointer to this record.

## References
- `docs/decisions/first-breach-alternatives-study.md` and its JSON
- ADR-0056, ADR-0057
