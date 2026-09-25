# Climate attribution and system composition: what the decomposition is, and what the shares are shares of

**Status:** Accepted (study note; no default, prior, config field, persisted
sweep, posterior, annual number, mechanism share or fragility curve changed).
**No ADR:** nothing here decides anything. Three statements built on the Phase 3
record were arithmetically wrong or over-reaching, and this note replaces them
with the exact identities and measures the distance between the two.

> **Re-based under ADR-0054, 2026-09-25.** The evidence this note reads was regenerated on the re-based
> matrix d70 (0.70 / 0.53 / 0.26 / 0.70 mm became 0.90 / 0.65 / 0.74 /
> 0.75 mm at KP 57.4 / 58.8 / 60.0 / 62.0; bulk unchanged). The committed
> JSON is the re-based record. Where the prose below quotes a matrix-reading
> number it is the pre-rebase value, kept as written; the re-based values are
> in the JSON, tabulated in `bimodal-foundation-d70-study.md` Part 3 and in
> the dated addenda of `docs/phase2_report.md` and `docs/phase3_report.md`.

**Date:** 2026-09-17.
**Driver:** `scripts/climate_attribution_decomposition.py`.
**Record:** `docs/decisions/climate-attribution-and-composition-study.json`.
**Gate:** `tests/test_climate_attribution_decomposition.py` (20 tests).
**Parents:** ADR-0023 (shape-invariant climate axis), ADR-0038 (Phase 3
composition and annualisation), ADR-0042/0043 (Uemura surface curves),
`annualisation-hazard-sampling-uncertainty.md` (the estimator, seed and
pattern-stratified draw are imported from its driver, not re-implemented).

**Scope on every interval below.** Hazard-sampling uncertainty only, the
finite-ensemble spread of the d4PDF peak-stage distribution with the fragility
curves held fixed. The aquifer-conductivity bracket is far wider and does not
cancel. Point quantities are exact arithmetic on committed artifacts and carry
no such qualification.

---

## 0. Summary

1. **The climate ratio is a mixture, not a product.** Chapter 7 wrote the
   warming-to-historical annual ratio as the long-duration frequency factor
   times the within-stratum severity factor. That product is the change in the
   long stratum's **contribution**, one addend of the exact two-term mixture.
   It overshoots the total by **2.26** at KP 57.4 and lands within 5 per cent
   at the other three, for a reason with a closed form.
2. **Frequency does not dominate over both strata.** Inside the long stratum it
   does, at all four sections. Over both strata a symmetric attribution puts
   frequency at **18 to 50 per cent** of the log ratio, and at the two sections
   whose strata clear the pre-registered occupancy floor the interval straddles
   a half: **0.503 [0.426, 0.589]** at KP 58.8 and **0.440 [0.355, 0.538]** at
   KP 60.0. Neither channel resolvably leads. The reason the old reading missed
   this is that the short stratum's own conditional probability rises by 5.1 to
   14.0, a severity increase the long-stratum product discards.
3. **Mechanism shares normalise by the sum of the marginals, not by the union.**
   The gap runs 1.000 to **1.314** over the eight production cells, largest at
   the KP 62.0 warming cell that carries the 0.500 tie. **The tie is invariant**
   to the choice of denominator, because both mechanisms share it.
4. **The independence assumption in the composition is not non-conservative by
   construction.** With the marginals fixed, conditional dependence can move the
   union only inside the Frechet bracket, a factor of **0.658 to 1.314** at that
   same cell, and independence sits strictly inside it, above the positively
   dependent end. The non-conservative channel is a different one: physical
   coupling that changes a **marginal**, such as a scour front shortening the
   seepage path. Two channels, opposite signs.
5. **The sixty-year non-breach check reproduces, except its threshold.** The
   series union 1.0754e-2, the 0.645 expected failures and the 0.523 no-failure
   probability all reproduce exactly. The exclusion threshold does not: the
   exact one-sided 95 per cent limit for zero successes in sixty trials is
   **4.87e-2**, and 5.0e-2 is the rule-of-three approximation `3/n`. Two silent
   assumptions are named, and **both run in the model's favour**.

---

## 1. The partition identity, and why it is exact

`annualize` averages the composed curve over the ensemble peaks and
`stratified_annual_p_f` averages the **same** per-event vector inside and
outside a predicate stratum. Over a partition of one finite set,

    P = w_in p_in + (1 - w_in) p_out                                      (1)

is the law of total expectation on a finite average, so it is exact and not a
model. Gate 0 measures it against the published `p_annual_system` at all eight
cells: worst relative deviation **3.4e-16**, which is summation order.

The stratum is defined on `EventSummary.hours_above_datum > 24 h`. The strata
are **labels on events, not model covariates**: every mechanism's conditional
curve is a function of peak stage alone, built by integrating one canonical
member (`HPB_m064_1987`) scaled to each level, for BEP and for both surface
mechanisms alike (`scripts/generate_uemura_surface_curves.py`). Duration enters
the fragility only through that one shape, identically for every event of the
same peak. Table 1 is therefore a decomposition of the **hazard**, and the
concentration factor measures the peak separation between duration strata, not
a fragility response to duration.

## 2. The ratio is a mixture

With `C_k = w_k p_k` and `s_in = C_in / P`,

    R = P'/P = s_in R_in + (1 - s_in) R_out                               (2)
    R_in = (w'_in / w_in) (p'_in / p_in) = f g                            (3)

Gate 2 reproduces (2) to 1.6e-16 and gate 4 reproduces (3) to 0.0 at all four
sections. Production arm (matrix / posterior / primary / 250 m):

| section | R (total) | `f g` = R_in | R_out | s_in (hist.) | `f g` / R |
|---|---:|---:|---:|---:|---:|
| KP 57.4 | 12.658 | 28.602 | 10.243 | 0.1316 | **2.260** |
| KP 58.8 | 5.508 | 5.617 | 4.622 | 0.8903 | 1.020 |
| KP 60.0 | 7.858 | 7.473 | 13.109 | 0.9318 | 0.951 |
| KP 62.0 | 12.701 | 12.122 | 13.517 | 0.5853 | 0.954 |

The error has a closed form, which the gate pins:

    R_in - R = (1 - s_in)(R_in - R_out).                                  (4)

So the product approximates the total when the long stratum carries nearly all
the historical probability **or** when the two strata's contribution ratios
happen to coincide. KP 58.8 and KP 60.0 are the first case. **KP 62.0 is the
second, and a share test alone would get it wrong**: its share is only 0.585,
and the product is still within 5 per cent because 12.12 and 13.52 are close.
KP 57.4 is neither, and there the product is 2.26 times the total.

Sampling intervals at the two sections that clear the floor: `f g / R` is
**1.020 [0.970, 1.092]** at KP 58.8 and **0.951 [0.888, 1.069]** at KP 60.0,
both containing one. The product is an acceptable stand-in for the total
**there**, within hazard-sampling noise, and nowhere is that true by
construction.

## 3. Frequency against severity, and the order the split depends on

The split of (2) between the weight vector and the conditional vector is
counterfactual: it needs an order. Writing `P(w, p)` for (1) and the four
corners `P(w,p)`, `P(w',p)`, `P(w,p')`, `P(w',p')`, the frequency term is
`log P(w',p) - log P(w,p)` taken first and `log P(w',p') - log P(w,p')` taken
last, and the Shapley value is their average. Gate 3 confirms the two terms sum
to `log R` exactly at all three readings.

| section | freq. first | freq. last | Shapley | additive Shapley | inside the long stratum |
|---|---:|---:|---:|---:|---:|
| KP 57.4 | 0.250 | 0.116 | **0.183** | 0.176 | 0.612 |
| KP 58.8 | 0.529 | 0.478 | **0.503** | 0.503 | 0.566 |
| KP 60.0 | 0.479 | 0.401 | **0.440** | 0.445 | 0.514 |
| KP 62.0 | 0.502 | 0.230 | **0.366** | 0.351 | 0.679 |

No reading anywhere exceeds **0.529**, and the four of the sixteen that exceed
a half at all do so by less than 0.03: frequency is never more than a bare
majority of the total, and the Shapley interval at the two resolved sections
straddles a half. The last
column is the claim that does survive: **inside the long stratum** frequency
exceeds severity everywhere, carrying 51 to 68 per cent of `log R_in`.

What the old reading missed is in the short stratum, where `p_out` rises by
**10.31 / 5.07 / 14.03 / 13.91**. Short-duration years become far more dangerous
too, and at KP 57.4 they carry 87 per cent of the historical total.

**Occupancy.** Intervals are reported only where **both** scenarios clear the
pre-registered floor of 20 carrying member blocks. KP 57.4's long stratum holds
3 years in 3 blocks and KP 62.0's 19 years in 14; their point values stand and
their intervals are withheld, following the same rule as the parent study.

**Cross-check on the estimator.** The total-ratio intervals this driver
produces, 4.176 to 7.690 at KP 58.8 and 5.402 to 12.825 at KP 60.0, reproduce
the parent study's committed climate-ratio intervals digit for digit, which is
what identifies the imported draw as the same draw.

## 4. What a mechanism share is a share of

`SystemFragility.dominance_share` and `AnnualizedResult.dominance_share` both
compute `P_i / sum_j P_j`. The composed probability is the union
`1 - prod_j (1 - P_j)`. Annualised, production arm:

| cell | union | sum of marginals | sum / union | BEP share (sum) | BEP / union |
|---|---:|---:|---:|---:|---:|
| KP 57.4 hist. | 7.530e-4 | 7.530e-4 | 1.000 | 1.000 | 1.000 |
| KP 57.4 +4K | 9.531e-3 | 1.040e-2 | 1.091 | 0.912 | 0.995 |
| KP 58.8 hist. | 7.445e-3 | 7.558e-3 | 1.015 | 0.974 | 0.989 |
| KP 58.8 +4K | 4.101e-2 | 4.307e-2 | 1.050 | 0.941 | 0.989 |
| KP 60.0 hist. | 1.809e-3 | 1.809e-3 | 1.000 | 1.000 | 1.000 |
| KP 60.0 +4K | 1.421e-2 | 1.423e-2 | 1.001 | 0.998 | 1.000 |
| KP 62.0 hist. | 1.006e-3 | 1.057e-3 | 1.051 | 0.812 | 0.853 |
| **KP 62.0 +4K** | 1.278e-2 | 1.680e-2 | **1.314** | **0.500** | **0.658** |

The gap is nil wherever one mechanism is loaded alone and is largest exactly
where two are loaded equally, which is the tie cell. The shares are a ranking,
not a partition of the system probability: as fractions of the union the two
mechanisms there are 0.658 and 0.657, and they sum to 1.314 rather than to one.
**The tie survives either normalisation** because the denominator cancels out of
a comparison between two marginals, and so does every dominance ordering in the
record.

`composition.py`'s `dominance_share` docstring said "share of the union failure
probability", which the expression has never computed. Corrected the same day;
the `AnnualizedResult` twin already said "summed annual contributions".

## 5. Dependence against coupling: two channels, opposite signs

Chapter 8 states that the composition treats the mechanisms as conditionally
independent given the stage, gives a scour front shortening the seepage path as
the excluded coupling, and calls the exclusion non-conservative. Two different
things are being merged.

**Channel A, dependence with the marginals held fixed.** Frechet:

    max_i P_i  <=  P_union  <=  min(1, sum_i P_i).

Independence sits strictly inside. Positive residual dependence given the stage,
which is what shared soil and geometry uncertainty would produce, moves the
union **down** toward `max_i P_i`, so assuming independence **over-states** the
union: conservative, not the reverse. At the KP 62.0 warming cell the bracket is
8.403e-3 to 1.680e-2 around an independent 1.278e-2, a factor of **0.658 to
1.314**. At the other seven cells it is far narrower, because one mechanism
carries the cell.

**Channel B, physical coupling that changes a marginal.** A scour front
shortening the seepage path raises `P_bep` itself. That is not a dependence
structure over fixed marginals, it is a different marginal, and its omission is
non-conservative.

The direction is therefore not universal, and the existing non-conservative
statement belongs to channel B, where the thesis's own example already sits.

## 6. The sixty-year non-breach check

Composing the four characterized segments in series under independence:

| quantity | value |
|---|---|
| per-section historical annual piping | 7.530e-4 / 7.363e-3 / 1.809e-3 / 8.580e-4 |
| series union | 1.07541e-2 (prints as 1.08e-2) |
| sum of the four | 1.07828e-2 |
| largest single section | 7.363e-3 |
| expected failures in 60 years | 0.6452 |
| P(no failure), independent years | 0.5227 |
| exact one-sided 95 % upper limit, 0 in 60 | **4.870e-2** |
| rule-of-three `3/n` | 5.0e-2 |
| exact limit / reported value | **4.53** (5.0e-2 gives 4.65) |

The first four rows confirm the published figures. The threshold does not: the
thesis prints 5.0e-2 and 4.6, which are `3/n` and its ratio, while the exact
inversion `1 - 0.05^(1/60)` gives 4.87e-2 and 4.53. A thesis that insists on
exact binomial endpoints elsewhere should not quote a Poisson approximation
here.

Two assumptions are silent, and **naming them strengthens the check rather than
weakening it**:

* **Inter-section independence.** The four sections see one flood, so positive
  dependence is expected; under it the reach union falls toward the largest
  single-section value, a factor of **1.46** below the independent composition.
  Independence therefore over-states the reach probability, over-states the
  expected count, and under-states the no-failure probability.
* **Persistent epistemic uncertainty.** The sixty years are treated as
  independent trials at a known `p`. The soil and conductivity uncertainty is
  one draw held fixed across all sixty. `(1-p)^60` is convex in `p`, so
  `E[(1-p)^60] >= (1-E[p])^60` by Jensen: 0.523 is a **lower** bound on the
  no-failure probability a persistent-epistemic treatment would give.

Both push the same way, so the record is at least as consistent with the model
as the published figures say. The check still constrains over-prediction only:
it excludes nothing below its threshold and is not a calibration.

## 7. One canonical shape: what the invariance measurement does and does not license

ADR-0023 measured normalized shape statistics over the full band ensembles:
median `t50` **40 h [32 to 54]** historical against **35 h [27 to 49]** warming,
identical compound fractions (9.6 against 10.1 per cent) and trough depths. Two
different claims can be built on that, and only one of them follows.

* **Differential, and it follows.** Using one shape for both ensembles
  introduces no *between-climate* bias, because the shape distributions do not
  differ systematically. This is what justifies running the conditioning sweep
  once.
* **Level, and it does not follow.** That one shape reproduces either
  ensemble's mean fragility is a separate statement, and the same ADR refutes
  it: the pinned member has `t50` = 55 h, above the historical interquartile
  range, chosen deliberately to exercise the memory model. The level effect of
  the shape choice is measured by the second approved member, not by the
  invariance finding.

**A direction that is determinable and was not stated.** Warming shapes are
marginally *shorter*, and the shape companion measures that a shorter, sharper
event at equal peak **lowers** transient probabilities. A shape-matched
treatment, each ensemble under its own shapes, would therefore lower the warming
fragility relative to the historical one and **reduce** the climate ratio. The
shared historical shape is conservative for the ratio. The magnitude is not
quantified here and would need a shape-distribution study, which is recorded as
future work rather than as an uncompleted correction: the existing companion is
a matched-peak comparison of two pinned members, and a third member would add a
third point, not a distribution.

## 8. Reproducing

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/climate_attribution_decomposition.py
pytest tests/test_climate_attribution_decomposition.py
```

About eight seconds against the warm hazard cache. Gate 6 asserts that neither
the cache nor the Phase 3 output directory is written. The driver imports the
composition step from `scripts/phase3_campaign.py` and the estimator from
`scripts/annualisation_uncertainty_study.py`, so gate 1 exercises the production
code path rather than a copy of it.

## 9. What must not be reintroduced

* the total climate ratio as the product of the long-stratum frequency and
  severity factors;
* "frequency exceeds severity" as a statement about the total rather than about
  the long stratum;
* an unqualified causal reading of the duration strata: they are labels on
  events, and no mechanism's fragility takes duration as an input;
* mechanism shares described as fractions of the union, or as disjoint
  attributable parts of the system probability;
* a universal direction for the conditional-independence assumption;
* `3/n` quoted as an exact 95 per cent exclusion limit;
* the inference from between-climate shape invariance to one canonical shape
  representing the ensemble mean fragility.


## Interpretation correction, 2026-09-20

The no-differential-bias and universal conservative-sign assertions in section 7 are superseded by [whole-document synthesis](whole-document-claim-synthesis-2026-09-20.md): marginal shape summaries do not establish joint trajectory ordering. Shared exposure does not prove residual positive dependence, and the non-breach calculation remains conditional on complete detection and stationary independent years given p. The measured decomposition, conditional Frechet bounds and Jensen inequality remain unchanged.
