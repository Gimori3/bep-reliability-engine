# What the Clopper-Pearson interval's coverage rests on under the production design

> **Re-based under ADR-0054, 2026-09-25.** The evidence this note reads was regenerated on the re-based
> matrix d70 (0.70 / 0.53 / 0.26 / 0.70 mm became 0.90 / 0.65 / 0.74 /
> 0.75 mm at KP 57.4 / 58.8 / 60.0 / 62.0; bulk unchanged). The committed
> JSON is the re-based record. Where the prose below quotes a matrix-reading
> number it is the pre-rebase value, kept as written; the re-based values are
> in the JSON, tabulated in `bimodal-foundation-d70-study.md` Part 3 and in
> the dated addenda of `docs/phase2_report.md` and `docs/phase3_report.md`.

**Date 2026-09-17. Status: study, no default changed.** Audit item F5. Driver
`scripts/interval_coverage_study.py`; statistics in
`bep_reliability_engine.convergence` (`interval_coverage`,
`coverage_lower_limit`); gate `tests/test_interval_coverage.py`; records
`docs/decisions/binomial-interval-coverage-kp58_8_matrix.json` and
`...-kp60_0_matrix.json`.

Nothing here changes a `Config` field, a default, a prior, a physics kernel, a
persisted sweep or a production number. What changes is what the repository and
the thesis are entitled to say about the interval they already report.

---

## 1. The claim under repair

Every raw fragility point is delivered with a two-sided 95 per cent
Clopper-Pearson interval (ADR-0024), and `fragility.binomial_ci`'s docstring
said, without qualification:

> "Exact (conservative) coverage."

The endpoints *are* exact: they invert the exact binomial law rather than a
normal approximation, which is what "exact" means in Clopper and Pearson's
sense. The coverage guarantee behind the word is a different object. It is
derived from `K ~ Binomial(n, p)`, and the production sample is a randomized
Latin hypercube, whose **rows are dependent**. So the guarantee does not
transfer from the construction to this design as a matter of course.

The thesis drew one inference from the existing evidence that the evidence does
not support. Chapter 5 said the measured LHS-to-crude *variance* parity in the
deep tail "justifies exact binomial intervals on raw tail points". Variance
parity is a statement about dispersion. Coverage is a different functional of
the same distribution, and one does not imply the other.

## 2. What was already known, and what it does and does not settle

Two facts were in hand before this study, and neither is a coverage statement.

**The estimator is exactly unbiased under LHS.** With scipy's scrambled design
each coordinate is `(perm_j(i) - 1 + U_ij)/n` with `perm` uniform and
independent of `U`, so every row is marginally the target distribution and
`E[K] = n p` exactly. This is Owen's Theorem 10.1 and its immediate corollary
(A. B. Owen, *Monte Carlo theory, methods and examples*, chapter 10 "Advanced
variance reduction", draft, `artowen.su.domains/mc/Ch-var-adv.pdf`, read
2026-09-17).

**Its dispersion is bounded, and was measured.** Owen's Proposition 10.4, proof
attributed there to Owen (1997), gives `Var(mu_LHS) <= sigma^2 / (n - 1)` for
any square-integrable integrand, so LHS variance is at worst `n/(n-1)` times the
iid variance: at `n = 1e5` that is an excess of one part in `1e5`. Proposition
10.1, attributed to Stein (1987), gives the asymptotic form
`Var = (1/n) * integral e(x)^2 dx + o(1/n)` with `e = f - f_add`, so **the
additive part of the integrand drops out**. That is, independently, the exact
mechanism ADR-0031 measured: LHS beats crude Monte Carlo 1.40 to 1 in the bulk
and falls to parity in the deep transient tail, where the multiplicative
`C_e x k_aq` interaction is nearly all of the integrand and its additive part is
nearly nothing. ADR-0031's R = 50 replicate ladder measured that dispersion
directly.

**Neither settles coverage.** A bound on `Var(K)` constrains how far the count
spreads; the probability that `[L(K), U(K)]` contains `p` depends on the whole
law of `K`, not on its second moment. Nor does it follow that coverage must be
*worse* under dependence. Owen's own chapter says the practical route: "The most
straightforward way is to use some independent replicates of the Latin hypercube
sample." That is what was done.

## 3. The design, and the rule fixed before it ran

Registered in a dated pre-registration note before the first replicate was
drawn, and reproduced verbatim in the driver's `decision_rule` block, which is
what the two companion JSONs carry.

* **Production arm.** Exactly the production design:
  `sample_theta_tilted(shift_z=None, stratified=True)`, bit-identical to M2
  `sample_theta`, plus the production 1-D LHS seepage length. `N = 1e5`.
  Replicates differ only in seed.
* **Control arm.** The same pipeline with `stratified=False` and an iid
  seepage length from the identical moment-matched lognormal. Its rows are
  independent, so its count **is** binomial; its measured coverage validates the
  apparatus. Replacing the L draw matters: `sample_seepage_length` is itself a
  1-D Latin hypercube, so leaving it in would have left the control's rows
  dependent too.
* **Sections and levels.** KP 58.8 and KP 60.0, matrix, at the ADR-0031
  conditioning levels, both branches. Those two sections are the ones ADR-0031
  chose because their fragility transitions are bracketed, so one ladder spans
  bulk to deep tail: the measured range runs from `P_f = 0.92` (static, bulk) to
  `7.7e-5` (transient, KP 60.0's deepest level), four decades, and it includes
  the raw-tail regime the ADR-0024 deliverable policy exists for.
* **Reference.** The **leave-one-out** mean of the other replicates in the same
  arm, so no replicate is tested against a target containing itself. At
  `R = 800` the residual inflation from reference noise is
  `sqrt(1 + 1/799) = 1.0006`.
* **Backend.** The numba progression backend, as ADR-0031 used, under a
  pre-registered gate: one replicate re-evaluated on the numpy production
  backend, failure **indicators** required to agree exactly.
* **Decision rule.** (1) The control's one-sided 95 per cent lower confidence
  limit on coverage must be at least 0.90 at every cell, or the study is void.
  (2) Given that, LHS coverage is *not contradicted* at a cell when the same
  limit is at least 0.90, and *contradicted* otherwise. (3) If contradicted
  anywhere, the thesis relabels the interval as approximate and reports the
  deficit; if nowhere, it keeps the interval and says coverage was measured on
  the design rather than inherited from an independent-trials model. A finite
  set of levels cannot prove coverage everywhere, and the wording must say so
  either way.

`R = 800` was set from a measured throughput probe before the run
(0.33 s per replicate at `N = 1e5` on the numba backend) and not adjusted after.

## 4. Result

Both records: `R = 800` independent randomizations per arm, `N = 1e5` each,
1656 s and 1719 s on the numba backend. The pre-registered backend gate passed
at both sections: numba and numpy failure **indicators** agreed on every one of
the 1e5 rows, both branches, zero disagreements.

**The apparatus is sound.** The iid control's measured coverage runs **0.9375 to
0.9663** over its sixteen cells, with one-sided 95 per cent lower limits of
**0.9216 to 0.9538**, every one above the pre-registered 0.90 floor. Its
empirical `Var(K)` against the binomial `n p (1 - p)` runs **0.903 to 1.111**,
centred on 1 as a genuinely binomial count must be. So the reduction, the
leave-one-out reference and the seed streams behave as a binomial reference
should, and the stratified arm can be read.

**Coverage under the production design is not contradicted anywhere.**

| section | arm | coverage range | lower-limit range | Var(K)/binomial |
|---|---|---|---|---|
| KP 58.8 | production LHS | 0.9413 to 0.9988 | 0.9257 to 0.9941 | 0.391 to 0.999 |
| KP 58.8 | iid control | 0.9425 to 0.9663 | 0.9271 to 0.9538 | 0.903 to 1.084 |
| KP 60.0 | production LHS | 0.9537 to 0.9988 | 0.9396 to 0.9941 | 0.334 to 1.026 |
| KP 60.0 | iid control | 0.9375 to 0.9637 | 0.9216 to 0.9509 | 0.943 to 1.111 |

At **15 of the 16** matched cells the stratified arm covered at least as often
as the iid one. The single exception is KP 58.8's deepest transient level,
0.9413 against 0.9600 on a mean of 31 failing realizations; its own exact
interval is **[0.9226, 0.9565]**, which contains 0.95, so that cell is not
evidence of a deficit either. Nowhere does a lower limit fall below the floor,
and the minimum over all thirty-two cells is 0.9257.

**The mechanism is visible and is the expected one.** The interval's width
depends only on the count, and the two arms' counts have the same mean, so the
two arms report intervals of essentially identical width; what differs is how
far the count spreads. In the bulk the stratified count carries **a third to
two fifths** of the binomial variance, so an interval built at binomial width
over-covers heavily (0.99 and above). Depth erodes that: by the deepest level
the variance ratio is 0.999 and 1.026 and the coverage falls back onto the iid
arm's. This is Stein's result made visible, the additive part of the integrand
dropping out of the LHS variance, and it reproduces ADR-0031's fm5 decay on an
independent design and in variance rather than CoV units. The one ratio above
unity, 1.026, is an estimate from 800 replicates whose own relative standard
error is 5.0 per cent, so it is not in tension with Owen's `n/(n-1)` bound,
which at `n = 1e5` permits an excess of one part in `1e5`.

**Two free checks came with it.** The two arms estimate the same integral, and
they agree: over the sixteen level-and-branch pairs the standardized difference
of arm means runs `|z| <= 2.00`, with one value at 2.00, which is what sixteen
comparisons produce. That is the unbiasedness of the LHS estimator confirmed
empirically rather than only derived. And the transient count never exceeded
the static count in any of the **12,800** replicate draws, the aggregate form of
the nesting theorem, on samples none of the earlier nesting evidence had seen.

**Secondary: the paired row bootstrap.** Added after the rule was fixed, so it
carries its own flag and does not move the verdict above. It is the interval the
headline `dbeta` is quoted with, and the row resample treats rows as
independent, so it raises the same question. Measured on the same replicates:
**0.9250 to 0.9788** under LHS and **0.9275 to 0.9575** under the iid control,
every lower limit above the floor, and the nesting implication holding in all
12,800 draws.

The two arms answer different halves of it. **The iid arm is the one that
under-covers**, pooling to **0.9430 over 6399 replicates** against a nominal
0.95, below nominal at five of its eight levels and with no trend in the
failure count. Its rows are independent, so that shortfall is the percentile
bootstrap's own approximation error on a proportion, not anything stratification
does. The stratified arm pools to **0.9544**, and its per-level values decay
from 0.979 in the bulk to 0.925 and 0.931 at the two deepest levels: the same
conservatism, and the same decay with depth, that the Clopper-Pearson cells
show. At those two deepest cells it lands a little **under** the iid arm, 740/800
against 760/800 and 745/800 against 752/799, and neither difference is resolved:
the exact intervals are `[0.9045, 0.9423]` against `[0.9325, 0.9640]` and
`[0.9114, 0.9478]` against `[0.9225, 0.9565]`, overlapping in both cases.

An earlier reading of these numbers, that the deep-tail dip is a small-count
effect and therefore direct support for the R1 thirty-row floor, **does not
survive the iid arm**: that arm's own minimum, 0.9275, is at a level carrying
190 failures, and its value at the 31-failure level is 0.9500. The count floor
keeps its other justifications; this measurement is not one of them.

## 5. What this licenses, and what it does not

**Licensed.** The interval stays as it is, and the thesis may say that its
coverage was **measured on the sampling design actually used**, at conditioning
levels spanning `P_f` from 0.92 down to `7.7e-5`, rather than inherited from an
independent-trials model. The bulk of that range is covered conservatively,
which is the direction an engineering deliverable wants, and the deep tail is
covered at about the nominal level.

**Not licensed, and the wording must not drift back.**

* Not "exact coverage" as a property of the design. The endpoints are exact
  functions of the count; coverage is measured, at a finite set of levels, on
  two sections.
* Not "conservative everywhere". Conservatism is a bulk property here and
  decays to parity in the deep tail, exactly where the raw-tail deliverable
  lives.
* Not the reverse claim either. Nothing here says Clopper-Pearson is invalid
  under LHS; at every cell measured, it was not contradicted.
* Not a variance argument. Neither ADR-0031's replicate CoV nor Owen's
  `n/(n-1)` bound is a coverage statement, and the Chapter 5 sentence that said
  variance parity "justifies" the interval has been replaced by what was
  actually measured.

**Scope.** Two sections, matrix reading, four levels each, both branches,
`N = 1e5`, `R = 800`. KP 57.4 and KP 62.0, whose deliverable is raw tail points
with this interval, were not separately replicated; their design-level
probabilities (`2.1e-3` static with zero transient, and `3.9e-3` with
`1.5e-4`) lie inside the measured range, and KP 60.0's deepest level at
`7.7e-5` is deeper than either. Posterior curves add a further step this study
does not reach: Accept-Reject retains a **selected** subset of an already
dependent design, so the same qualification applies to
`bayesian_reliability_updating` intervals a fortiori, and is recorded there.

## 6. Preserved

* ADR-0024's deliverable policy, unchanged: raw tail points with their interval
  where the transition is unreachable, fits where it is bracketed.
* ADR-0031's convergence verdict and its fm5 tail-variance finding, unchanged
  and now with a textbook mechanism behind them (Stein's additive-part result).
* Every persisted sweep, posterior, figure and production number.
* The pre-registered R1 and R2 criteria and the S04 index-space companion.
