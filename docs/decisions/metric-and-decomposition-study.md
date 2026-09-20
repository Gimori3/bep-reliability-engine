# What the two RQ1 metrics do and do not share, and what the ladder attributes

Single-topic study. **No default, prior, physics kernel, comparator, config
field or persisted sweep changes.** What changes is a false general statement
about the two metrics, the justification attached to one pre-registered
criterion, and the marker rule on one figure.

Driver: `scripts/metric_decomposition_study.py` (pure post-processing).
Evidence: `docs/decisions/metric-and-decomposition.json`.
Gate: `tests/test_metric_decomposition.py`.
Date of the measurement: 2026-09-16.

Companion to ADR-0040 (the comparator ladder and the R1/R2 criteria),
ADR-0045 (the model factor), ADR-0049 (the critical pipe length) and ADR-0051
(the equal-head convention). It corrects statements made in
`docs/rq1_beta_reexpression_2026-08-28.md` and in the thesis; the superseded
wording is quoted here rather than deleted.

---

## 1. The relationship between B and delta beta

With `B = P_static / P_transient` and `beta = -Phi^-1(P_f)`,

    dbeta = beta_trans - beta_static = Phi^-1(P_static) - Phi^-1(P_transient)
          = Phi^-1(B * P_transient) - Phi^-1(P_transient).

`dbeta` is a function of **both** branch probabilities. There is no map from
`B` alone, and the following was therefore wrong wherever it was written:

> "Cancellation is metric-independent: inputs cancel in both B and dbeta, or
> in neither." (thesis Chapter 8, superseded 2026-09-16)

> "the resolution criteria R1 ... and R2 ... stay defined on the probability
> ratio B exactly as pre-registered, because they map monotonically too."
> (`scripts/rq1_beta_analysis.py` module docstring, superseded 2026-09-16)

**The counterexample is the production anchor's own ratio.** Hold
`B = 1696/63 = 26.9206` and slide the pair along the tail: `dbeta` runs from
0.715 at `P_trans = 1e-6` to 2.750 at `P_trans = 3e-2`, a factor of 3.85. One
value of `B` carries a whole range of `dbeta`.

**What does hold is a restriction.** With **either** absolute probability held
fixed, `dbeta` is a strictly increasing function of `B`:

    d(dbeta)/dB = P_t / phi(Phi^-1(B P_t))          at fixed P_transient
    d(dbeta)/dB = P_s / (B^2 phi(Phi^-1(P_s / B)))  at fixed P_static

Both are positive on the whole admissible range, and both were checked against
a central difference to a maximum relative error of 1.9e-6. This restricted
monotonicity is what makes the two metrics agree on direction, which is all the
thesis ever needed from them, and it is not enough to move a width criterion
between them.

**"Cancels" names two different conditions, one per metric.** An input that
multiplies both branch probabilities by one factor leaves `B` exactly invariant
and moves `dbeta`: at the KP 62.0 anchor a common factor of 0.1 takes `dbeta`
to 0.866 of its value and a factor of 10 to 1.221, with `B` unchanged to
machine precision. An input that adds one shift to both reliability indices
leaves `dbeta` exactly invariant and moves `B`: a shift of -0.5 takes `B` to
0.656 of its value and +0.5 to 1.533. Neither condition implies the other, so
a cancellation claim must name its metric. The *mechanism* argument the thesis
makes, that an input cancels only if it reaches both branches through the same
channel and only that channel, is untouched by this; what fails is the
assertion that the resulting verdict is the same in both metrics.

**Why the two metrics rank stages and sections differently.** For small `p`,
`beta ~ sqrt(2 ln(1/p))` and `d ln p / d beta ~ -beta`, so `dbeta ~ ln(B)/beta`.
At fixed `B` the index gap therefore shrinks as the tail deepens. That is the
arithmetic behind the reported contrast, `B` decaying toward 1 with stage while
`dbeta` is shallowly U-shaped, and it is a consequence of the definitions
rather than a separate finding.

---

## 2. The two criteria, traced to their estimands

ADR-0040 s1.1 pre-registered both on the ratio:

* **R1** `k_trans >= 30`. Its estimand is the transient failure **count**.
* **R2** the 95 per cent interval on `B` has multiplicative width `<= 2.0`,
  fixed so that "an interval of multiplicative width 2.0 cannot straddle a
  decade", the granularity the ratio claim is quoted to.

**R1 does govern both metrics, and the reason is not a map between them.** Both
estimators are functions of the same two counts on the same rows, so a floor on
one of those counts governs any estimator built from them. Stating it that way
costs nothing and is true.

**R2 does not transfer.** A width condition on a ratio carries no width verdict
to a difference of indices. Holding the `B` interval at `[5, 10]`, a factor of
2.00 that passes R2 exactly, the directly evaluated `dbeta` interval width runs
0.152 at `P_trans = 1e-6` to 0.675 at `5e-2`, a factor of 4.43. The converse
fails too: a fixed `dbeta` width of 0.12 corresponds to `B`-interval factors
from 1.17 to 1.63 over the same range.

### 2.1 The replacement, derived rather than chosen

`R2_beta`: the **directly evaluated** 95 per cent paired-bootstrap interval on
`dbeta` has additive width `<= 0.30` index units.

The threshold comes from R2's own rule, not from the results. R2 = 2.0 was set
so the interval occupies `log10(2) = 0.301` of the one decade the ratio claim
is quoted to. The index claim's granularity is the span the four design-level
`dbeta` values are quoted over, 0.90 to 1.87, so one index unit; the same
fraction of one index unit is **0.30**.

**It is strictly stricter than R1-and-R2, which is the direction that matters.**
Over the 102 grid levels in `rq1-beta-reexpression.json`:

| | index-space resolved | index-space unresolved |
|---|---|---|
| **ratio-space resolved** | 60 | **14** |
| **ratio-space unresolved** | **0** | 28 |

No level passes in index space and fails on the ratio. The 14 that go the other
way are **all** of KP 62.0's hypothetical above-crest extension, 53.0 to
56.5 m at `N = 1e5` and 54.0 to 56.5 m at `N = 1e6`, where the static branch
fails in every realization, so `dbeta` has no interval at all and its width is
undefined. ADR-0024 already forbids presenting those stages as attainable.

**No design anchor is reclassified.** KP 62.0 (46.39 m), KP 58.8 (41.00 m) and
KP 60.0 (42.75 m) are resolved under both readings; KP 57.4 (39.21 m) is
unresolved under both, on two failing transient rows, and stays a one-sided
bound. Anchor interval widths are 0.118, 0.020 and 0.026 index units against
the 0.30 ceiling.

The figure `rq1_hwl_dbeta_resolved.png` and `rq1_kp57_4_dbeta_bound.png` now
mark a level by the index-space verdict, because their axis is `dbeta`. Only
the first changed: six markers inside the shaded hypothetical band flipped from
resolved to unresolved, and every marker in the attainable range, both anchor
callouts and all four other RQ1 figures are byte-identical.

**The published intervals were never affected.** `delta_beta_bootstrap`
(`scripts/rq1_beta_analysis.py`) draws one row resample per replicate and forms
`beta(mean_trans) - beta(mean_static)`, so every interval on record is a direct
paired bootstrap on `dbeta`. The KP 62.0 anchor's published `[0.85, 0.97]` is
`[0.8516, 0.9693]` from that bootstrap, and is **not** the naive
Clopper-Pearson difference, which is `[0.8284, 0.9834]` and is the separate
`delta_beta_lower_bound` construction. Regenerating the whole record with the
corrected criteria changed exactly one value, the generation date, and added
1048 keys.

---

## 3. The ladder telescopes; its components do not commute

The additive ladder's **total** is order-independent, because it telescopes.
Its **components** are path-dependent, the same way the shares of a probability
difference are. Two legitimate orders over the same toggles, on identical
`N = 1e6` rows:

* **Order A**, the published one, head convention first:
  `C0 -> C1 -> C3b -> C4b`.
* **Order B**, head convention last: `C0 -> C4b_gross -> C4b`. Its first step
  is the equal-head-convention comparison of ADR-0051 read as a ladder step,
  and its second is the crack decrement applied to the transient branch.

The pairing was gated, not assumed: the equal-head arm's static column is
bit-identical to the ladder's `C0` and its stored production transient to
`C4b`, at 10 of 10 shared levels across the two sections.

| section | stage | total `dbeta` | head, order A | head, order B | share A | share B | interaction (95 %) |
|---|---|---|---|---|---|---|---|
| KP 62.0 | **46.39** | 0.9044 | 0.3574 | 0.3323 | 0.395 | 0.367 | +0.025 [-0.032, +0.077] |
| KP 62.0 | 46.50 | 0.9037 | 0.3165 | 0.3271 | 0.350 | 0.362 | -0.011 [-0.041, +0.020] |
| KP 62.0 | 47.00 | 0.9592 | 0.2530 | 0.2211 | 0.264 | 0.230 | +0.032 [+0.025, +0.040] |
| KP 62.0 | 48.00 | 1.1286 | 0.1700 | 0.1445 | 0.151 | 0.128 | +0.026 [+0.024, +0.027] |
| KP 62.0 | 50.50 | 1.6544 | 0.0960 | 0.0761 | 0.058 | 0.046 | +0.020 [+0.017, +0.023] |
| KP 57.4 | 39.21 | 1.5582 | 1.0119 | 0.7159 | 0.649 | 0.459 | +0.296 [+0.081, +0.514] |
| KP 57.4 | **39.50** | 1.2696 | 0.8124 | 0.6149 | 0.640 | 0.484 | +0.198 [+0.176, +0.218] |
| KP 57.4 | 40.00 | 1.1169 | 0.5706 | 0.4924 | 0.511 | 0.441 | +0.078 [+0.074, +0.082] |
| KP 57.4 | 43.25 | 1.6261 | 0.1769 | 0.1523 | 0.109 | 0.094 | +0.025 [+0.006, +0.048] |

Every row telescopes to the same total under both orders, to machine precision.

**The document was already printing both orders without saying so.** The
"40 and 64 per cent of the index difference" attributed to the head convention
is order A at KP 62.0's design level (0.395) and KP 57.4's resolved anchor
(0.640). The "63 to 83 per cent of the index difference survives equalization"
is one minus order B's share. At KP 62.0 the two orders differ by less than
their own interval, so nothing there is at stake beyond the wording. At
KP 57.4's resolved anchor the difference is 16 percentage points of the total
and is resolved, so the order has to be named.

**The two-toggle Shapley value on `{head, rest}`** is the average of the two
orders, the same construction `gap_decomposition.static_pair_shapley` already
uses on the static `{head, alpha}` lattice: 0.345 at KP 62.0's design level
(38 per cent of the total) and 0.714 at KP 57.4's resolved anchor (56 per
cent). It is reported as the order-free summary; it does not replace either
order, and the existing static-pair Shapley, whose measured interaction runs to
+0.14 at KP 57.4, is unchanged.

The initiation-gate step is exactly 0.0000 at every KP 62.0 level, because `C1`
and `C3b` carry identical counts there, and runs 0.178 down to 0.000 at
KP 57.4. That component is order A's and is stated as such.

---

## 4. What the shared sample buys

The claim under repair:

> "A shared sample guarantees the absence of sampling noise between the
> branches, and nothing else." (thesis Chapter 8, superseded 2026-09-16)

It reduces that noise. It does not remove it.

Exact delta-method variances, available in closed form because the transient
failure set is contained in the static one on every row the engine reaches, so
the joint failure probability is exactly `P_t` and
`Cov = P_t (1 - P_s) / n`:

    Var_paired(dbeta)      = a_s^2 V_s + a_t^2 V_t + 2 a_s a_t Cov
    Var_independent(dbeta) = a_s^2 V_s + a_t^2 V_t
        a_s = +1/phi(Phi^-1(P_s)),  a_t = -1/phi(Phi^-1(P_t))

The sensitivities have opposite signs and the covariance is positive, so the
cross term is negative and pairing always helps. For `log B` the algebra
collapses further: the paired variance is the **difference** of the two
per-branch terms where the unpaired one is their sum.

Measured over the eight levels the two `N = 1e6` sections resolve, and
confirmed by the paired bootstrap to within bootstrap noise:

* variance reduction on `dbeta`: **1.03 to 1.56**;
* variance reduction on `log B`: 1.02 to 1.33;
* paired standard error on `dbeta`: **0.0017 to 0.0304 index units**, strictly
  positive everywhere. At the KP 62.0 design anchor it is 0.0304 against an
  estimate of 0.904, which reproduces the published interval's half-width.

The sentence's second clause is also weaker than the repository's own position:
the shared sample is what makes the row-level containment meaningful, and that
containment is the nesting theorem of
`survival-information-and-nesting-study.md`.

**Sharing a resistance parameter is not the same as an equal multiplicative
effect.** The Sellmeijer model factor multiplies the single-source `H_c` in
both branches and still displaces `B`, by resolved factors of 1.07 to 1.22.

---

## 5. Cancellation, input by input and metric by metric

Measured from the persisted arm matrices with one paired 16-cell resample per
level, so both verdicts come from the same replicate set. `rho` is the
ADR-0047 s4.5 ratio-of-ratios, cancellation being `rho = 1`; its index
counterpart is the difference-of-differences
`dbeta_arm - dbeta_baseline`, cancellation being `0`. The window is each
section's attainable range with all four contingency cells at or above the R1
floor of 30, which reproduces the published `rho` figures exactly.

| input | channels | max resolved `B` departure | max resolved abs `dbeta` departure | verdicts disagree |
|---|---|---|---|---|
| `m_p` (ADR-0045) | common-mode, both branches | **1.07 to 1.22** | **0.166 to 0.273** | 1 to 2 levels each way, per section |
| `l_c` lower (ADR-0049) | transient only | 1.11 to 1.23 | 0.045 to 0.064 | never |
| `l_c` upper (ADR-0049) | transient only | 1.19 to 1.38 | 0.070 to 0.104 | never |

Two findings, and the second is new.

1. **The input the thesis names as the only one that cancels has the largest
   index-space displacement of the three, and the input with no common-mode
   channel at all has the smallest.** The two metrics rank `m_p` against `l_c`
   in opposite orders. The mechanism reading is unaffected and remains correct:
   `m_p` moves both criteria a great deal and the movements nearly cancel *in
   the ratio*; `l_c` moves one criterion a little and nothing cancels. What
   cannot be said is that either verdict is metric-free.
2. **The two metrics' verdicts never disagree for a transient-only input** (0
   of 114 quotable levels, both arms, all four sections) **and do disagree for
   the common-mode one.** That is what the mathematics predicts: when the
   static branch is exactly invariant both statistics are monotone functions of
   one transient move, so they must agree; when both branches move, the ratio
   and the index weigh the two moves differently.

Point estimates for every other persisted arm, in both metrics, are in the
record's `cancellation_points` block.

### 5.1 Handed to S05, not taken here

The published `1.19 to 1.67` for the critical-length upper arm takes its
maximum, `1/0.6000 = 1.667` at KP 62.0, from stage 46.50 m, where the smallest
of the four contingency cells holds **14** failures, below R1's floor of 30.
The next level up, 46.75 m on 130 failures, gives **1.385**, which is the
maximum over the R1-qualified attainable window. The `rho` interval at 46.50 m
does exclude 1, so the figure is "resolved" under the ADR-0047 s4.5 rule, which
carries no count floor. Whether that rule should carry one is a rare-event
admissibility question and belongs with the bounds work, so both numbers are
recorded and neither is changed here. Nothing in this study depends on the
choice: the `m_p` against `l_c` ordering in index-space displacement holds on
either window, 0.166 against 0.104 R1-qualified and 0.381 against 0.135
unfiltered.

---

## 6. What is preserved

* Every comparator definition, and the verbatim provenance behind them:
  `C0` is Sellmeijer's own gross-head convention, `C1` the crack-reduced
  static, `C3b` the initiation-qualified analytic sustained-peak limit, `C4b`
  the production transient, `C4b_gross` the equal-head transient. No comparator
  is renamed, and none is described as Japanese regulatory practice.
* The four-component interpretation of the gap: temporal, dimensional,
  head-convention and `H_eq`-conservatism.
* Every published probability, index, ratio, interval and bound.
* The mechanism rule for cancellation, that an input cancels only if it reaches
  both branches through the same channel and only that channel, which is a
  statement about limit-state structure and survives unchanged.
* The complementary ratio evidence. `B` is not withdrawn anywhere; it is the
  metric in which the order-of-magnitude claim is quoted, and R2 remains its
  criterion.


## Interpretation correction, 2026-09-20

The same-channel necessity assertion in section 1 is superseded by the exact metric conditions and counterexample in [whole-document synthesis](whole-document-claim-synthesis-2026-09-20.md). Four contingency cells in the arm count-floor description means four marginal branch failure counts, not four cells of the 16-pattern contingency. Measurements and gates are unchanged.
