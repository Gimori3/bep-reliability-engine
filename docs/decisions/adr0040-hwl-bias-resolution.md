# Resolving the design-HWL static-vs-transient bias (companion to ADR-0040)

**Status:** Pre-registration written 2026-07-30, before any new number was computed.
Outcome sections are appended below it, unedited above.

**Type:** Companion note to ADR-0040 / ADR-0041. **Not** a new numbered ADR: no `Config`
default changes, no physics changes, no `configs/*.yaml` or CSV edit, no persisted
production sweep replaced. Everything here *adds* artifacts.

**Parent decision:** the 2026-07-29 production campaign's decision 6 ("design-HWL bias
resolution method") arrived as an unfilled placeholder and was recorded as an open item
(`docs/production_campaign_2026-07-29.md` §12). The author has since chosen the
method: **brute-force N = 1e6 at KP 62.0 first, use it as ground truth to validate tilted
importance sampling, then apply the validated estimator at KP 57.4.**

**Drivers:** `scripts/hwl_bias_resolution.py` (new).
**Evidence:** `docs/decisions/adr0040-hwl-bias-resolution.json` (new).
**Tests:** `tests/test_hwl_bias_resolution.py` (new).

---

# PART 1 — PRE-REGISTRATION

*Written and committed before Stage A ran. Nothing in this part was edited afterwards;
every criterion below is evaluated verbatim in Part 2 and following.*

## 1.0 The quantity

The **conventional-practice bias** at a conditioning level h is

    B(h) = P_f,static(h) / P_f,transient(h)

evaluated as the ADR-0040 comparators **C0** (production static branch, raw gross head
against H_c at alpha = -1/3, ADR-0028) and **C4b** (production transient branch, canonical
d4PDF loading, alpha = -1/3, end factor 0.9, ADR-0027) **on one shared sample** (ADR-0002:
the same theta matrix and the same independent stochastic-L draw feed both). This is the
same quantity `docs/stage6_6_report.md` §8 and `docs/production_campaign_2026-07-29.md`
§6.1 tabulate, and the same one the thesis's Sub-question 1 headline quotes.

## 1.1 The resolution criterion

The design-HWL bias is declared **RESOLVED** at a section if and only if **both** hold at
that section's design-HWL anchor:

* **R1 — count.** The transient comparator carries **k_trans >= 30** failing
  realizations at that level.
* **R2 — interval width.** The 95 % confidence interval on B has **multiplicative width
  `hi/lo` <= 2.0**.

Both, not either. If only R1 holds the result is reported as **PARTIALLY RESOLVED** with
both numbers stated; if neither holds it is **UNRESOLVED**.

**Why R1 = 30.** Below about 30 events a binomial count behaves as a rare-event counting
process: the Clopper-Pearson interval is strongly asymmetric, the normal approximation to
`log B` is not serviceable, and a paired bootstrap over row indices cannot manufacture
information the sample does not contain (with k = 4, as at KP 62.0 today, a large fraction
of bootstrap replicates resample a materially different failing set). Thirty is the
conventional floor at which the relative standard error of a count, `1/sqrt(k)` ~ 18 %,
becomes a usable statement rather than an order-of-magnitude one. It is *not* the ADR-0031
N-sufficiency criterion (empirical CoV < 5 %, which needs `P_f*N` of several hundred);
that criterion governs a *probability* deliverable, and this is a *ratio quoted to one or
two significant figures*, a weaker demand deliberately stated as such.

**Why R2 = 2.0.** The thesis claim this number carries is an order-of-magnitude claim:
Sub-question 1 currently reads "conventional practice overestimates per-event BEP failure
probability by one to one-and-a-half orders of magnitude". An interval of multiplicative
width 2.0 cannot straddle a decade, so it supports a claim quoted to one significant
figure; an interval of width 10 cannot support any such claim, and an interval between the
two supports only a "within a factor of a few" statement. R2 is therefore anchored to what
the claim needs, not to what the data is expected to deliver. Note R1 and R2 are close to
equivalent in practice (k = 30 alone gives `hi/lo` ~ 2.1 for a Poisson-like count, k = 40
gives ~1.9), so R2 is the binding criterion and R1 the structural guard; both are stated so
that a lucky-looking narrow interval on a tiny count cannot pass.

**The interval on B.** By **paired bootstrap over realization rows** (ADR-0040 Decision 6
and ADR-0047 §4.5), never as two independent binomials: C0 and C4b are evaluated on the
same rows, C4b is nested within C0 in continuous time, and treating them as independent
would overstate the width. B = 1e4 replicates for the ratio (raised from the ladder's 1e3
because a ratio percentile in a small-count regime needs more replicates than a
difference), percentile method, seed recorded. Where the tilted estimator supplies the
numbers (Stage B onward) the bootstrap is the **weighted** paired bootstrap of §1.4.

**If N = 1e6 does not meet the criterion.** Stated in advance, in order:

1. Report the failure against R1/R2 explicitly, with `k_trans` and the interval.
2. Proceed to Stage B anyway and validate the tilted estimator at the levels where Stage A
   *does* satisfy R1 (they exist: KP 62.0 carries 130 failing rows at 46.75 m and 499 at
   47.00 m already at N = 1e5, so at N = 1e6 there will be several validation levels with
   k in the thousands).
3. Apply the validated estimator at the design-HWL anchor and re-test R1/R2 against its
   Kish `n_eff`-corrected interval.
4. If that also fails, **declare the design-HWL bias unquotable as a single number** and
   recommend the thesis lead with the resolved anchor above HWL (KP 62.0: 10.5 at 47.0 m
   MSL). This is a permitted and expected outcome, not a failure of the exercise.

## 1.2 The level being resolved, unambiguously

Stage 6.6 evaluates 39 levels at KP 62.0: the 38-level generated sweep grid plus the exact
section HWL inserted by `prepare_config(extra_levels=(HWL,))`. Two nearby levels have both
been called "the design-HWL bias" in this repository, and they are different levels:

| anchor | KP 62.0 | KP 57.4 | provenance |
|---|---|---|---|
| **A1 — inserted design HWL** | **46.39 m MSL** | **39.21 m MSL** | `configs/kp62_0_historical_matrix.yaml` / `kp57_4_historical_matrix.yaml`, key `geometry.HWL`, read programmatically. Carries 4 (KP 62.0) and 0 (KP 57.4) transient failing rows at N = 1e5. `stage6_6_report.md` §8 and campaign §6.1 anchor here. |
| **A2 — nearest production grid level** | **46.50 m MSL** | **39.25 m MSL** | the generated `mc.conditioning_grid`. Carries 15 (KP 62.0) transient rows at N = 1e5. The 2026-07-30 epistemic-bracket synthesis anchored its `design_hwl` row here (nearest grid level to HWL). |

**Decision, pre-registered: resolve BOTH, report BOTH, and never again quote one as the
other.** They are affordable together because they are two columns of the same ladder run:
the marginal cost of A2 is zero. Every HWL number in Part 2 onward is labelled A1 or A2.

Every HWL value is read from `configs/*.yaml` `geometry.HWL` at runtime by the driver and
asserted against the value tabulated above; no HWL is taken from a prose document. A test
pins this.

## 1.3 What would falsify the exercise

Stated before seeing any number. Any one of these means **the design-HWL bias cannot be
quoted as a single figure**, and the deliverable becomes a recommendation to lead with a
resolved anchor above HWL:

* **F1 — statistical.** N = 1e6 fails R1/R2 at A1 *and* the validated tilted estimator
  also fails R1/R2 at A1 (the §1.1 fallback chain exhausted).
* **F2 — anchor knife-edge.** The bias at A1 and at A2 differ by more than their joint
  95 % intervals permit, i.e. the two intervals do not overlap. A quantity that changes
  resolvably over 0.11 m of stage is not "the bias at the design water level"; it is the
  bias at one arbitrarily chosen level on a steep curve, and must be quoted with its level
  or not at all.
* **F3 — epistemic swamping.** The **epistemic** band on B at the anchor, measured in
  Stage D as the ratio-of-ratios rho across the ADR-0045/0046/0047/0048 arms, exceeds the
  **statistical** 95 % interval width on B by more than a factor of **10** in
  multiplicative width. A statistical interval that is a tenth the width of the epistemic
  one is false precision: the correct deliverable is then the epistemic band, with the
  statistical interval reported inside it as a subordinate quantity.

F3 is deliberately set on a quantity that is **not yet known**. The 2026-07-30 synthesis
measured the *maximum over the grid* of rho (k_aq up to x163) and the transient-P_f span at
the A2 anchor (unbounded at KP 62.0), but it did **not** measure rho **at the design-HWL
anchor specifically**, which is what F3 tests. The distinction matters because rho is
strongly stage-dependent and the anchor sits in the steep part of both curves.

**I am willing to reach the F-conclusion.** The record this note joins contains four
precedents where the convenient claim lost: ADR-0029's refutation of the spec's own LHS
tail-variance expectation, ADR-0031's LHS/crude-MC parity finding, ADR-0047 §4.5's
non-cancellation result, and the 2026-07-30 synthesis's refutation of ADR-0048's
consequence 3. A defensible "quote 10.5 at 47.0 m MSL instead" is a better thesis sentence
than an indefensible headline at 46.39 m.

## 1.4 The tilted-estimator validation criterion

`bep_reliability_engine.tail_sampling` (ADR-0029) supplies `sample_theta_tilted`,
`cross_entropy_shift` and `importance_estimate`. Design constraints, fixed here:

* **One tilt, all comparators.** A single tilted theta sample and a single log-weight
  vector; *every* comparator is evaluated on it. The shared-sample contract (ADR-0002) is
  preserved by construction. Tilting per comparator is forbidden: it would destroy the
  pairing that both the ratio and its bootstrap depend on.
* **The shift targets the transient region.** The CE shift is selected against the **C4b**
  failure indicator at the anchor level. The static branch inherits the same weights
  untilted. Consequence, stated in advance rather than assumed negligible: a proposal
  optimised for the transient region is *not* optimal for the static region, which at the
  anchor carries one to two orders of magnitude more failures. The static estimator will
  therefore have a **larger** variance under the tilt than it does under plain LHS. This is
  acceptable only because the static count is large (hundreds of rows at A1 already at
  N = 1e5), but it must be **measured and reported**, not assumed: Stage B reports the
  static estimator's own CoV and Kish `n_eff` under the tilt alongside the transient's, and
  if the static CoV under the tilt exceeds its plain-LHS CoV at N = 1e6 the estimator is
  reported as unsuitable for the ratio and only the transient side is taken from it.
* **The ratio's variance is derived, not assumed.** B is a ratio of two *weighted*
  estimators on a *correlated* sample. Its interval comes from a **weighted paired
  bootstrap**: resample row indices once per replicate, carry the weights with the rows,
  and recompute both weighted means from the same resampled rows. This replaces the
  ADR-0047 §4.5 unweighted bootstrap over 16 joint pattern counts, which is invalid under
  weights (the pattern counts are no longer sufficient statistics once rows carry unequal
  weight).
* **Kish `n_eff` is reported per level beside every interval.** An `n_eff` of 40 is not
  1e6 rows and will never be presented as if it were.
* **Self-gate, asserted, not assumed.** `sample_theta_tilted(shift_z=None,
  stratified=True)` must reproduce `sample_theta` **bit for bit** (the ADR-0029 property).
  Asserted in the driver at the section's own config. If it fails, the task stops.
* **No weighted estimate enters a `FragilityResult`** (ADR-0029 constraint), and none is
  persisted as a production number.

**Validation criterion V, pre-registered.** Let S be the set of Stage A levels at KP 62.0
with `k_trans >= 30` at N = 1e6. The tilted estimator is **VALIDATED** if and only if all
four hold:

* **V1 — self-gate.** Zero-shift stratified draws reproduce `sample_theta` bit for bit.
* **V2 — no level disagrees.** At every level in S, the tilted 95 % interval for
  P_f,transient overlaps the Stage A Clopper-Pearson 95 % interval.
* **V3 — no systematic offset.** At every level in S with `k_trans >= 100`, the ratio of
  the tilted point estimate to the Stage A point estimate lies within **[1/1.5, 1.5]**;
  and across all of S the signs of `log(P_IS/P_A)` are not all identical (an unbiased
  estimator's deviations must not march in one direction; identical signs at >= 5 levels
  is evidence of a bug in the weights, not of noise).
* **V4 — the estimator is actually buying something.** At the A1 anchor the Kish `n_eff`
  of the transient failure-region weights is **>= 200**, and the tilted estimator's CoV at
  A1 is at most **half** the plain-LHS CoV at the same N. An estimator that agrees with
  brute force but is no more efficient does not justify carrying a weighted number into the
  thesis; brute force would then be reported instead.

If V fails, **that is the finding**: it is reported as a documented negative on the
estimator, brute force is used for everything it can reach, and KP 57.4 is reported as a
bound rather than a point estimate. A documented negative is worth more than an
unvalidated estimator carrying the thesis's headline number.

## 1.5 Stage A gates (each stops the task on failure)

* **G-A1 — drift guard bit-identical.** The **N = 1e5** arm must still reproduce the
  persisted production sweep matrices exactly at every common grid level (38 at KP 62.0,
  23 at KP 57.4), with identical theta. A change here means the harness moved, not the
  statistics, and invalidates everything downstream. (This gate applies to the N = 1e5 arm
  only: `prepare_config` documents that changing `n_samples` yields an entirely different
  LHS sample, so the N = 1e6 arm cannot and must not be bit-compared to a 1e5 artifact.)
* **G-A2 — Euler flips exactly 0.** Every one of the five flip diagnostics
  (`c4b_not_c0`, `c4b_not_c3b`, `c4a_not_c3a`, `c4c_not_c4b`, `c4d_not_c4a`) must be
  exactly 0 at every level of the N = 1e6 run, as it is at N = 1e5. A nonzero count is a
  numerical-convergence red flag (ADR-0030), not a physics finding.
* **G-A3 — consistency with N = 1e5.** At every level where the N = 1e5 count is adequate
  (`k >= 30`), the N = 1e6 point estimate must lie inside the N = 1e5 Clopper-Pearson 95 %
  interval. A systematic offset across levels is a bug, not a refinement; it would mean the
  two samples are not drawn from the same population.
* **G-A4 — convergence reported.** `metadata['mc_convergence']`-equivalent per-level CoV of
  the estimator is computed and reported against the spec §11 5 % target, for both branches,
  at both N.

## 1.6 The Stage A pilot, and the scope rule fixed in advance

At N = 1e5 the KP 62.0 ladder takes ~25 min and writes a 45 MB HDF5. Ten comparators x 1e6
rows x 39 levels of boolean state is 390 MB for the comparator dict alone, and the joblib
level-results list holds another 390 MB before assembly; the `bootstrap_comparator_means`
`stacked` array is a further 390 MB with a same-size fancy-index gather per replicate. The
machine has 15.8 GB RAM (3.3 GB free at the time of writing) and 12 logical CPUs.

**Pilot: N = 2e5, KP 62.0, measured for wall time and peak RSS, extrapolated to 1e6 before
committing.** The scope rule, fixed now:

* If projected peak RSS <= **8 GB** and projected wall time <= **6 h**: run the **full ten-
  comparator ladder** at N = 1e6.
* Else if the binding constraint is the **bootstrap** (peak RSS or time dominated by
  `bootstrap_comparator_means`): keep the full ten-comparator ladder for the failure
  matrices, and restrict the bootstrap to the **anchor levels plus the validation set S**,
  which reduces its `stacked` array proportionally. This is a reduction in the *analysis*,
  not in the *physics*, and loses nothing this note needs.
* Else if the binding constraint is the **ladder run itself**: chunk over levels (the level
  loop is embarrassingly parallel and results are assembled by level index, so chunked ==
  whole, and `run_comparator_ladder` is deterministic given the config).
* Only if both of those fail: fall back to the **reduced engine ladder** C0 -> C1 -> C3b ->
  C4b, which carries the headline bias and the full engine-ladder decomposition, and say so
  explicitly with the measurement that forced it.

The chosen branch, and the measurement that selected it, are reported in Part 2. Scope is
not reduced silently and not guessed.

## 1.7 Stage D — the epistemic band on the ratio, at the anchor

Stage D measures rho = (P_static/P_transient)_arm / (P_static/P_transient)_baseline **at the
resolved design-HWL anchor**, not the maximum over the grid (which is what the 2026-07-30
synthesis reports). Arms:

* **`m_p` first, as a negative control / smoke test.** ADR-0045 §2 applies m_p to the
  single-source H_c in *both* of its uses, so it is pure common-mode by construction and
  the 2026-07-30 synthesis measured it at rho = 1.07 to 1.22. **Pre-registered pass
  condition: the machinery must return rho within [1/1.5, 1.5] for m_p.** If it does not,
  the machinery is wrong and no other arm is trusted or reported.
* the four ADR-0048 `k_aq` / `gamma_bl_sub` prior-mean scenarios,
* `z_toe` +/- 0.30 m (ADR-0046) — the synthesis found this is the **second-largest** knob
  at KP 62.0's design HWL (x184 on P_f, ahead of L at x15), because the A2 anchor sits
  0.11 m above HWL on 15 failing rows,
* the ADR-0047 DEM-L arm.

Every arm keeps its knob **OFF in production** (campaign decision 3). These are
measurements on top of the frozen baseline, never sweep members. No `Config` default moves.

---

# PART 2 — EXECUTION AND OUTCOME

## 2.1 Gates G-A1 and G-A2: the harness has not moved

Re-ran the ten-comparator ladder at **N = 1e5** from the committed YAML at both
sections, before touching anything at higher N.

| gate | KP 62.0 | KP 57.4 |
|---|---|---|
| **G-A1** C0/C4b vs the persisted production sweep | **bit-identical, 38 levels** | **bit-identical, 23 levels** |
| `theta_matrix` identical | yes | yes |
| **G-A2** all five Euler-flip diagnostics | **0 at every one of 39 levels** | **0 at every one of 24 levels** |
| wall (39 / 24 levels, `n_jobs=6`) | 600 s | 883 s |

So the statistics below are measured on the same harness that produced the
production campaign's numbers. The N = 1e5 anchors reproduce
`docs/production_campaign_2026-07-29.md` §6.1 exactly:

| anchor | level | P_f static (k) | P_f transient (k) | B | 95 % CI | width | resolved |
|---|---|---|---|---|---|---|---|
| KP 62.0 **A1** | 46.39 | 1.790e-3 (179) | 4.0e-5 (**4**) | 44.75 | [21.1, 180.0] | 8.5× | **no (R1, R2)** |
| KP 62.0 **A2** | 46.50 | 3.930e-3 (393) | 1.50e-4 (15) | 26.20 | [17.1, 49.6] | 2.9× | **no (R1, R2)** |
| KP 57.4 **A1** | 39.21 | 1.180e-3 (118) | 0 (**0**) | ∞ | undefined | ∞ | **no** |
| KP 57.4 **A2** | 39.25 | 2.070e-3 (207) | 0 (**0**) | ∞ | undefined | ∞ | **no** |

Two facts worth stating plainly before any new compute. First, **KP 57.4 carries
zero transient failures at *both* candidate anchors**, not just at the exact HWL —
so the "zero-row bound" problem there is not an artefact of the inserted level.
Second, the apparent 44.75-vs-26.20 gap between KP 62.0's two anchors, 0.11 m
apart, is exactly the conflation criterion F2 exists to test.

## 2.2 The Stage A pilot, and the scope decision it produced

Measured at **N = 2e5**, KP 62.0, 39 levels, `n_jobs=6`, with a sampling probe
over the **whole process tree** (the parent's own working set under-reports by
roughly the worker count, which would have made the projection meaningless):

| quantity | measured at N = 2e5 | linear projection to N = 1e6 | pre-registered threshold |
|---|---|---|---|
| wall time | **1909 s** (31.8 min) | **2.65 h** | 6 h |
| peak RSS (process tree) | **1.30 GB** | **6.48 GB** | 8 GB |
| comparator array alone | — | 0.36 GB | — |
| Euler flips | 0 at all 39 levels | — | 0 |

Both projections clear their thresholds, so the pre-registered §1.6 rule selects
the **full ten-comparator ladder**; no scope was reduced, and neither the
level-chunking nor the reduced-engine-ladder fallback was needed.

**Two honest caveats on the projection, stated rather than smoothed.**

1. **The wall time between N = 1e5 and N = 2e5 scaled super-linearly** (600 s →
   1909 s, a factor 3.18 for a factor 2 in N), which taken at face value would
   project 7.4 h and *fail* the threshold. That reading is contaminated: other
   work (the test suite, two pre-flight scripts) was running on the same 12
   logical cores during the pilot and not during the N = 1e5 run. The physics is
   O(N · T) per level and the persistence is O(N), so linear is the defensible
   model. The decision therefore rests on the linear projection, the
   contamination is recorded here, and the Stage A run was executed with nothing
   else competing so its own wall time is a clean third data point.
2. **The RSS projection is a deliberate over-estimate.** A fixed interpreter and
   library footprint (~150 MB) sits in every worker regardless of N, so scaling
   the whole 1.30 GB linearly inflates the constant part sevenfold. The
   incremental cost is small — 1.1 GB of that was already present at N = 1e5 —
   so the true figure is nearer 2.5 GB. The linear number is reported because it
   is the one the pre-registered threshold was applied to.

## 2.3 Method as executed

Everything runs from one driver, `scripts/hwl_bias_resolution.py`, which is
physics-free in the `convergence.py` / `sensitivity.py` sense: every failure
indicator comes from the production machinery, either the ADR-0040 comparator
ladder or M8 `evaluate_batch` directly.

**The statistic.** B = P_f,static(C0) / P_f,transient(C4b) at a level, on one
shared sample. Its interval comes from a **paired bootstrap over realization
rows** (never two independent binomials), implemented once, in two exact regimes
selected automatically:

* *Unweighted.* K boolean columns take at most 2^K joint patterns, and resampling
  N rows with replacement makes the pattern counts exactly
  `Multinomial(N, p_hat)`. The multinomial draw is therefore not an
  approximation of the index resample — it is the same distribution, at
  O(B · 2^K). At K = 4 this **is** the 16-cell contingency of the ADR-0047 §4.5
  kernel; a test compares the two directly and requires the point estimate to
  agree to 1e-12 and the interval endpoints to 5 %, so the accepted statistic
  behind the published L non-cancellation numbers is reproduced rather than
  re-invented.
* *Weighted* (importance sampling). Pattern counts stop being sufficient
  statistics once rows carry unequal weight, so this is the pre-registered
  replacement. It is still exact and still avoids an O(B · N) gather, via the
  **active-row reduction**: a row whose every column is False contributes
  exactly zero to every weighted mean whatever its weight, so only rows where
  some column fires need their bootstrap multiplicity tracked, and all the silent
  rows collapse into one lumped multinomial category. A test checks this against
  a literal O(B · N) index resample carrying the same weights.

**The estimator.** One tilted θ sample, one weight vector, **all ten comparators
evaluated on it** — the ADR-0002 shared-sample contract preserved by
construction. This required one additive seam: `run_comparator_ladder` gained a
keyword-only `theta_override`, default `None` and bit-identical to the previous
behaviour, so an alternative *proposal* population can be pushed through the
identical comparator machinery. A run using it stamps
`metadata['theta_override']` with an explicit warning that the raw column means
are proposal frequencies, not probabilities, so a proposal-population ladder can
never masquerade as a baseline one. The independent stochastic-L draw is
deliberately **not** overridden: L is drawn from the prior under both proposal
and target, which is what keeps the importance weight exact. Four tests pin the
seam (default bit-identity, echo-the-config's-own-θ bit-identity, the metadata
stamp, shape validation).

**The tilt.** Targeted at `{k_aq, C_e}` (the fm7 interaction direction, ADR-0029
§4), selected by one cross-entropy step from a seeded conservative pilot
(ν = 1.0 on both) at the A1 anchor rather than from the baseline's own handful of
failing rows. The shift is chosen against the **transient** branch; the static
branch inherits the same weights untilted, and §1.4 committed in advance to
*measuring* rather than assuming the variance that costs — reported in §2.5.

**The grid.** The tilted estimator is evaluated on the **full** conditioning grid
(38 levels plus the inserted HWL), not on an anchor neighbourhood. Narrowing it
would have quietly excluded the levels far above the anchor where an
anchor-optimised tilt is expected to be poor — that is, exactly the levels most
likely to falsify V2/V3.

**The Stage D arms, as constructed.** Each is built from the section's own
committed YAML by the same `model_copy` route the accepted companion driver for
that knob uses, so an arm here is the same object that driver would sweep:

| arm | bracket | construction | owning decision |
|---|---|---|---|
| `m_p` (**first, the control**) | `m_p` | `sellmeijer_model_factor` enabled, Lognormal(1.0, CoV 0.12) | ADR-0045 |
| `k_aq_field_toe` | `k_aq_prior_mean` | prior mean → 5.15e-4 m/s | ADR-0048 |
| `k_aq_field_geomean` | `k_aq_prior_mean` | prior mean → 5.94e-5 m/s | ADR-0048 |
| `k_aq_regional_upper` | `k_aq_prior_mean` | prior mean → 1.0e-2 m/s | ADR-0048 |
| `gamma_bl_sub_lower` | `gamma_bl_sub_prior_mean` | prior mean → 6.0 kN/m³ | ADR-0048 |
| `z_toe_plus0.30m` / `z_toe_minus0.30m` | `z_toe` | surveyed toe ± 0.30 m | ADR-0046 |
| `L_withdrawn_1998` (KP 62.0) | `L_measurement` | `geometry.L` 40.0 → 47.0 m | ADR-0047 |
| `L_dem_clean_median`, `L_dem_all_stations_median` (KP 57.4) | `L_measurement` | 33.0 → 36.5 m, → 67 m | ADR-0047 |

Eight arms at KP 62.0, nine at KP 57.4. The L arms come from
`epistemic_bracket_synthesis.seepage_length_arms`, imported rather than
re-derived, so the arm-selection rule is the accepted one — including the detail
that it is fed the config's *live* `geometry.L` rather than the `csv_L_m` in the
stale ADR-0047 record, which at KP 62.0 still names the withdrawn 47 m. KP 57.4's
`L_dem_all_stations_median` is the **road-fill-contaminated** arm ADR-0047
identifies as not adoptable; it is carried because it bounds the arm, not because
it is a candidate value. Four tests pin this construction: m_p is first, every
required bracket is present, no arm mutates the baseline `Config`, and each arm's
`config_hash` really does differ from the baseline's.

**One addition to the pre-registered F2 test, declared as an addition.** §1.3
defines F2 by whether the A1 and A2 **95 % intervals overlap**. That form treats
the two anchors as independent estimates, which they are not: the failure set at
46.39 m is nested inside the one at 46.50 m *on the same rows*, so an overlap
test is the conservative instrument and will under-detect a real difference. The
sharper **paired** comparison is therefore reported alongside it — the same
ratio-of-ratios statistic with "arm" = the A1 column and "baseline" = the A2
column, null pinned at rho = 1. The pre-registered overlap verdict is reported
first and is the one F2 is judged on; the paired result is reported as extra
information about the *stage-sensitivity of the bias*. Adding a sharper test
after the fact could only ever make F2 easier to fire, so it is declared here
rather than quietly substituted, and both numbers are given.

**What this work does not touch.** No `Config` default, no physics module, no
`configs/*.yaml`, no `data/processed/tokachi_bep_inputs.csv`, no persisted
production sweep, and no numbered ADR. The existing N = 1e5 Stage 6.6 artifacts
under `results/stage6_6/` are untouched and still reproducible — this study
**adds** arms under `results/hwl_bias_resolution/`, never replaces one. Every
Stage D knob stays OFF in production, per campaign decision 3; the arms exist
only as in-memory `Config` copies. The one code change to a shipped module is the
additive, default-`None`, bit-identical `theta_override` seam described above.

**Stage D goes direct, not through the ladder.** The epistemic arms need the
ADR-0045 m_p draw threaded, and the comparator ladder does not currently support
it (`gap_decomposition` predates ADR-0045 and calls
`priors.to_marginal_specs()` rather than `effective_marginal_specs()`, so it is
also scenario-blind). Stage D therefore calls `evaluate_batch` directly for the
two production branches, which is exactly where the ladder gets C0 and C4b, with
every knob threaded the way `run.py` threads it and `effective_marginal_specs()`
as the marginal source. This is gated, not asserted: the direct route is required
to reproduce the persisted production sweep's failure matrices **bit-identically**
at the A2 anchor before any arm at that section is reported. It does, at both
sections.

## 2.4 Stage A: the brute-force ground truth, and the answer

**N = 1e6, KP 62.0, all ten comparators, all 39 levels. 169.8 min wall, 3.23 GB
peak.** The measured wall time came in 7 % above the linear projection (159 min)
and the measured memory at half the linear upper bound, which settles the §2.2
question: the pilot's apparent super-linear scaling *was* contamination from
concurrent work, and the linear model that the scope decision rested on was the
right one.

**Every gate passed.**

| gate | result |
|---|---|
| **G-A2** Euler flips | **0** on all five diagnostics at all 39 levels |
| **G-A3** consistency with N = 1e5 | **PASS** — 31 levels / 59 branch comparisons where the N = 1e5 count was adequate; **0 failing**. No systematic offset. |
| **G-A4** spec §11 CoV | reported per level: 29/31 static and 28/32 transient levels with a defined CoV meet the < 5 % target |

**The design-HWL bias, resolved at both anchors:**

| anchor | level | P_f static (k) | P_f transient (k) | **B** | 95 % CI | width | R1 | R2 | **verdict** |
|---|---|---|---|---|---|---|---|---|---|
| **A1** (design HWL) | 46.39 | 1.696e-3 (1696) | 6.30e-5 (**63**) | **26.9** | [21.6, 35.3] | 1.63× | ✓ | ✓ | **RESOLVED** |
| **A2** (nearest grid) | 46.50 | 3.793e-3 (3793) | 1.760e-4 (**176**) | **21.6** | [18.8, 25.2] | 1.34× | ✓ | ✓ | **RESOLVED** |

So the pre-registered criterion is met at the exact design water level, on 63
failing rows rather than 4, and the fallback chain of §1.1 was not needed.

**The N = 1e5 figure was high by two-thirds, and that is the headline correction.**
At N = 1e5 the A1 cell read **44.7** on 4 rows; at N = 1e6 it reads **26.9** on 63.
The two are statistically consistent — the N = 1e6 transient P_f of 6.30e-5 sits
inside the N = 1e5 Clopper–Pearson interval [1.09e-5, 1.02e-4], which is exactly
what G-A3 tests and passes — so this is not a bug but the counting noise
`stage6_6_report.md` §8 warned about, now removed. The same happens at A2:
26.2 on 15 rows becomes 21.6 on 176. **Every published "44.7" is superseded by
26.9, and the direction of the error is that the small-sample figure
*overstated* the bias.**

## 2.5 Criterion F2: not fired, but the anchors do differ

The pre-registered F2 test asks whether the A1 and A2 intervals overlap. They do
— [21.6, 35.3] against [18.8, 25.2] — at both N = 1e6 and N = 1e5. **F2 does not
fire, and the exercise is not falsified on that ground.**

The sharper paired comparison declared in §2.3 tells a more precise story:

| N | paired rho (A1 / A2) | 95 % CI | resolved |
|---|---|---|---|
| 1e6 | **1.249** | [1.039, 1.556] | **yes** |
| 1e5 | 1.708 | [0.877, 6.078] | no |

At N = 1e6 the bias really is about **25 % larger at 46.39 m than at 46.50 m**,
and the difference is resolved — over 11 cm of stage. At N = 1e5 the same
comparison could not be resolved at all, which is one more illustration of what
4 and 15 failing rows can and cannot support.

**What that means for how the number is quoted.** It does not make the bias
unquotable: F2's pre-registered condition is not met, the two anchors agree
within their intervals, and both individually satisfy R1 and R2. It does mean the
number is **stage-specific at the decimetre scale**, so it must always be quoted
with the level it belongs to. "26.9 at 46.39 m MSL" is a defensible sentence;
"about 27" without a level is not, because 11 cm lower or higher moves it
resolvably.

## 2.6 Stage B: the tilted estimator is NOT validated — a documented negative

This is the first time the ADR-0029 tilted sampler has been pointed at the gap
decomposition. **It fails its pre-registered validation.** Reported as the finding,
per §1.4, rather than patched until it passes.

CE pilot: seeded shift ν = 1.0 on `{k_aq, C_e}` at N = 2e4 gave 26 transient
failures at A1, and the one CE step returned
**ν = {k_aq 3.168, C_e 0.897}** — a strong shift on `k_aq` and almost none on
`C_e`. That is itself worth recording: at the design water level the transient
failure region is reached overwhelmingly through extreme aquifer conductivity, not
through extreme `C_e`. The production tilt then ran at N = 1e5 on the full 39-level
grid.

| criterion | verdict | evidence |
|---|---|---|
| **V1** self-gate | **PASS** | zero-shift stratified draws reproduce `sample_theta` bit for bit; log-weights all zero |
| **V2** no level disagrees | **FAIL** | 1 of 30 levels in S disagrees resolvably: at 46.75 m the IS interval [8.31e-4, 1.05e-3] does not overlap the ground-truth CP interval [1.190e-3, 1.331e-3] |
| **V3** no systematic offset | **PASS** | every level with k ≥ 100 lies within [1/1.5, 1.5] (range 0.745 to 1.155); signs are mixed, not uniform |
| **V4** efficiency | **FAIL** | Kish `n_eff` = **86.9** at the anchor, below the pre-registered floor of 200 — although the CoV half passed handsomely: 0.107 tilted against 0.500 plain LHS at the same N, a **4.66× reduction** |
| **VALIDATED** | **NO** | V2 and V4 both fail |

**The diagnosis, and why it is not a tuning problem.** Look at the low end of the
ladder: the IS estimate is *consistently* below truth at the three lowest levels
in S — ×0.921 (46.39), ×0.812 (46.50), ×0.745 (46.75) — then recovers to ≈1.0
through the middle. A consistent deficit in exactly the regime the estimator was
built for is the signature of **weight degeneracy**: the CE shift concentrated the
proposal on high `k_aq`, so failures reached by other routes (moderate `k_aq`,
high `C_e` — and note the CE step barely tilted `C_e` at all) carry tiny weights
and are almost never drawn. The estimator remains unbiased *in expectation*, but
with `n_eff` ≈ 87 out of 1e5 the typical realisation under-estimates. **The Kish
diagnostic did its job**: it flagged a defect that V3's tolerance test alone would
have passed.

**The decisive measurement is the one §1.4 committed to taking.** I pre-registered
that tilting against the transient region would cost the *static* branch variance,
that this must be measured rather than assumed, and that if the static CoV under
the tilt exceeded its plain-LHS value the estimator would be "reported as
unsuitable for the ratio". It does, everywhere, and by a growing margin:

| level | static CoV, tilted | static CoV, plain LHS | **inflation** | `n_eff` static |
|---|---|---|---|---|
| 46.39 (A1) | 0.1117 | 0.0747 | **1.50×** | 80 |
| 46.50 (A2) | 0.0930 | 0.0503 | **1.85×** | 116 |
| 47.00 | 0.0696 | 0.0135 | 5.16× | 206 |
| 48.00 | 0.1115 | 0.0035 | 31.5× | 80 |
| 49.50 | 0.1009 | 0.00095 | 106× | 98 |
| 50.50 | 0.0982 | 0.00040 | 247× | 104 |
| 52.00 | 0.0982 | 0.00010 | 940× | 104 |

`n_eff` for the static branch plateaus near 104 no matter how many rows actually
fail, which is the same degeneracy seen from the other side.

**The methodological finding, which generalises beyond this study.** ADR-0029 built
this sampler to estimate **one** deep-tail failure probability, and on that job it
delivers here too — the transient side alone is 4.7× more precise, squarely
consistent with ADR-0029's measured 3.2–4.1×. But the Stage 6.6 deliverable is a
**ratio between two branches**, and a proposal optimised for one branch is
structurally the wrong instrument for that: it buys precision on the numerator's
denominator while degrading the other side by up to three orders of magnitude.
This is not a tuning failure to be fixed with a better ν; it is a mismatch between
what the estimator optimises and what the deliverable is.

**Consequences, applied.** Brute force is used for everything it can reach — which
turns out to be everything this study needs, because Stage A already resolved both
KP 62.0 anchors. Stage C therefore runs KP 57.4 by brute force at N = 1e6 as well,
and **Stage D was re-planned to run every epistemic arm unweighted at N = 1e6**
rather than through the estimator. No weighted number enters any headline, and
none enters a `FragilityResult` (the ADR-0029 constraint).

**What would be needed to rescue the estimator, recorded but not done.** The
diagnosis points at a specific fix — iterate the CE step (the pre-registration
committed to *one* step), or tilt a wider parameter set so the non-`k_aq` failure
routes keep usable weight, or use a defensive mixture proposal that retains a
fraction of the untilted prior. Any of those is a change of method *after* seeing
it fail, so none was applied here; they belong to a future study with its own
pre-registration.

**A note on scope, so this negative is not over-read.** Nothing here contradicts
ADR-0029. That ADR's claims — 3.2–4.1× deep-tail CoV reduction on a single P_f,
zero-failure replicates eliminated at P_f ≈ 1e-4, exact weights under any coupling
— are reproduced or unchallenged by this study; the 4.66× transient-side reduction
measured here is if anything at the favourable end of its range. What fails is a
*new application* of that machinery to a *different estimand*. The correct
statement is that the tilted sampler remains validated for what ADR-0029 built it
for, and is **not** validated for the static-vs-transient ratio.

## 2.7 Stage C at KP 57.4: gate G-A2 fired, and it is a real finding

The first KP 57.4 brute-force run at N = 1e6 **failed gate G-A2**:

```
per_diagnostic_totals: {c4b_not_c0: 0, c4b_not_c3b: 4,
                        c4a_not_c3a: 0, c4c_not_c4b: 0, c4d_not_c4a: 0}
```

Four realizations out of 1e6 fail the real-hydrograph transient comparator (C4b)
without failing the **sustained-peak analytic limit** (C3b). Under the ADR-0040
Decision 2 closed form that is impossible in continuous time: if the crack-reduced
erosion head never exceeds `H_c,transient`, the pipe stalls at `l_eq ≤ l_c` under a
head held *forever*, so it cannot breach under a head merely applied for a few
days. A nonzero count is therefore the ADR-0030 barrier-jump fingerprint — a
numerical artefact of the discrete forward-Euler step, not a physics result.

**Why it appears here and not before.** The rate is 4 in 1e6 = 4e-6. At the
production N = 1e5 the expected count is 0.4, so seeing zero there — as every
previous Stage 6.6 run, the campaign, and this study's own G-A2 at N = 1e5 did —
is exactly what one would expect from a population containing this artefact at
this rate. **It took the 10× larger sample to make it visible.** That KP 57.4 is
where it surfaces is consistent rather than surprising: ADR-0039 already
identified KP 57.4 as the timestep-sensitive section, the one where the literal
1 % l_e criterion needs Δt ≤ 112.5 s while 225 s suffices for indicators. This is
the indicator-level counterpart of that rider, visible only at 1e6 sampling depth.

**What it does and does not touch.**

* It does **not** invalidate any production result. Every persisted sweep, the
  Phase 2 posterior and the Stage 6.6 deliverable run at N = 1e5, where this
  study's own G-A2 passed with exactly zero flips at both sections, and the
  N = 1e5 drift guard is bit-identical to the persisted matrices.
* It does **not** touch KP 62.0. That section's N = 1e6 run passed G-A2 with zero
  flips on all five diagnostics at all 39 levels, so the resolved 26.9 and 21.6 of
  §2.4 stand untouched.
* It **does** mean a KP 57.4 ground truth at N = 1e6 needs the flip located before
  its numbers are believed — which is what the re-run establishes.

**A driver defect this exposed, and fixed.** The gate raised *before* persisting,
so the first run discarded 2.5 h of comparator matrices and left nothing to
diagnose. That is a bad gate design: the alarm destroyed the evidence it was
raised about. `cmd_brute` now writes the HDF5 and the diagnostics JSON
**unconditionally**, then gates; and `flip_summary` now records the offending
*levels and counts*, not just a total, so a future alarm says where it happened.
The gate still stops the task exactly as pre-registered — it just stops it with
the evidence on disk.

## 2.8 Stage D at KP 62.0: the epistemic band on the ratio, at the anchor

Run **unweighted at N = 1e6**, for the Stage B reason. Two gates first, both
passed: the direct M8 route is bit-identical to the persisted production sweep at
N = 1e5, **and** the N = 1e6 baseline is bit-identical to the Stage A ladder's own
C0/C4b columns — so every arm is compared against the exact ground truth whose
gates passed, not a differently-drawn population.

**The negative control passes, so the machinery is trustworthy.** `m_p` gives
rho = **1.010** [0.791, 1.245] at A1 and 0.925 [0.806, 1.053] at A2 — neither
resolved, both inside the pre-registered [1/1.5, 1.5]. Exactly what a knob that is
pure common-mode by ADR-0045 §2 construction must give. It was run first, and no
other arm would have been trusted had it failed.

Bias ratio B under each arm, at the design HWL (46.39 m), N = 1e6:

| arm | P_f static | P_f transient (k) | **B** | rho vs baseline | resolved |
|---|---|---|---|---|---|
| **baseline** | 1.696e-3 | 6.30e-5 (63) | **26.9** | — | — |
| `m_p` *(control)* | 4.080e-3 | 1.500e-4 (150) | 27.2 | 1.010 | no |
| `gamma_bl_sub_lower` | 1.696e-3 | 6.30e-5 (63) | 26.9 | **1.000** | no |
| `L_withdrawn_1998` | 2.660e-4 | 9.00e-6 (9) | 29.6 | 1.098 | no |
| `k_aq_field_toe` | 8.200e-5 | 3.00e-6 (3) | 27.3 | 1.015 | no |
| `z_toe_plus0.30m` | 7.600e-5 | 2.00e-6 (2) | 38.0 | 1.412 | no |
| **`z_toe_minus0.30m`** | 1.250e-2 | 9.010e-4 (901) | **13.9** | **0.515** | **yes** |
| **`k_aq_regional_upper`** | 4.966e-1 | 1.916e-1 (191 600) | **2.59** | **0.096** | **yes** |
| `k_aq_field_geomean` | **0** | **0** (0) | *indeterminate* | — | — |

**Three readings, and one correction to an assumption I nearly made.**

1. **`k_aq_field_geomean` is indeterminate, not infinite.** At the field-test
   geometric-mean conductivity, KP 62.0 produces **zero failures on *both*
   branches** at the design water level in 1e6 realizations — the static
   comparator fails no more often than the transient one, because neither fails at
   all. B is 0/0, undefined. It would have been easy, and wrong, to record this
   arm as "unbounded bias"; the honest statement is that under that conductivity
   the question does not arise at this stage, because the section is safe on both
   criteria.
2. **The `k_aq` bracket does not cancel — measured at the anchor the thesis
   quotes.** `k_aq_regional_upper` moves the ratio by a resolved factor of **10.4**
   (rho = 0.096), collapsing B from 26.9 to 2.59 because at high conductivity both
   branches saturate (P_static 0.497, P_transient 0.192) and the ratio compresses.
   This is a direct, anchor-specific confirmation of the Part 0 refutation, at the
   one level the 2026-07-30 synthesis had not evaluated.
3. **`z_toe` is the second knob, as the synthesis predicted, and asymmetric.**
   −0.30 m of datum is resolved at rho = 0.515 (B → 13.9); +0.30 m is unresolved on
   2 rows. `gamma_bl_sub_lower` is **exactly inert** (rho = 1.000, the identical
   63-row failure set) — a free re-confirmation of ADR-0028's static/gate
   separation.

### Criterion F3: **does not fire**

| quantity | value |
|---|---|
| statistical 95 % width on B at A1 | **1.63×** |
| epistemic band on B, arms with a defined B | 2.59 to 38.0 = **14.7×** |
| epistemic band, arms with adequate counts (k ≥ 30) only | 2.59 to 27.2 = **10.5×** |
| **ratio, epistemic / statistical** | **9.0** (or 6.4 on adequately-counted arms) |
| F3 threshold | 10 |

F3 was pre-registered to fire above 10. It does not — narrowly on the widest
reading, comfortably on the defensible one. So the statistical interval is **not**
false precision in the sense §1.3 defined: the design-HWL bias may be quoted as a
number with an interval, **provided the epistemic band is quoted with it**, because
that band is still 6 to 9 times wider than the statistical one. Quoting
[21.6, 35.3] alone would understate total uncertainty by roughly an order of
magnitude.

## 2.9 KP 57.4 at N = 1e6: still unresolved, but the bound improves 4.6×

The re-run persisted its evidence before gating, so the alarm is now diagnosable.

**Where the flips are — and they are not at the anchors.** The four `c4b_not_c3b`
rows sit at **39.50 m (1), 40.25 m (2) and 40.75 m (1)**. Neither design-HWL
anchor (39.21, 39.25) carries one. The artifact is real and G-A2 stops the task as
pre-registered, but it does **not** contaminate the anchor statements.

**G-A3 passed** (34 branch comparisons, 0 failing), so the N = 1e6 population is
consistent with the N = 1e5 one wherever the latter had adequate counts.

| level | P_f static (k) | P_f transient (k) | B | 95 % CI | width | resolved |
|---|---|---|---|---|---|---|
| 39.00 | 3.00e-5 (30) | 0 (**0**) | ∞ | — | — | no |
| **39.21 (A1, design HWL)** | 1.132e-3 (1132) | 2.00e-6 (**2**) | 566 | [221, 1178] | 5.3× | **no (R1)** |
| **39.25 (A2)** | 1.943e-3 (1943) | 1.00e-5 (**10**) | 194 | [115, 481] | 4.2× | **no (R1)** |
| **39.50** | 2.225e-2 (22 249) | 5.210e-4 (521) | **42.7** | [39.4, 46.6] | 1.18× | **yes** ← lowest resolved |
| 39.75 | 9.898e-2 | 6.860e-3 (6 860) | 14.4 | [14.1, 14.8] | 1.05× | yes |
| 40.00 | 2.467e-1 | 3.578e-2 | 6.89 | [6.83, 6.96] | 1.02× | yes |
| 40.50 | 6.165e-1 | 2.062e-1 | 2.99 | [2.98, 3.00] | 1.01× | yes |

**The design-HWL bias at KP 57.4 is NOT resolvable by brute force at N = 1e6.**
Two failing transient rows at A1 and ten at A2; R1 fails at both. Ten times the
production sample moved the count from 0 to 2. Reaching R1's 30 rows at A1 would
need roughly **N = 1.5e7**, about 40 h of the same compute — and the estimator that
was supposed to avoid that did not validate.

**What can be said, honestly.** A conservative one-sided bound built from
Clopper–Pearson intervals rather than from a 2-row bootstrap (which can only
resample the two rows it has, and whose [221, 1178] interval should not be
trusted):

| anchor | P_s 95 % lower | P_t 95 % upper | **B ≥** |
|---|---|---|---|
| A1 39.21 | 1.067e-3 | 7.225e-6 | **148** |
| A2 39.25 | 1.858e-3 | 1.839e-5 | **101** |

This supersedes the published *"an overestimation factor of at least 32 at 95 %
confidence"*, which came from **zero** failing rows at N = 1e5. The bound is now
**≥ 148**, a 4.6× improvement, and it is the strongest defensible statement about
KP 57.4 at its design water level.

**The recommended quotable anchor at KP 57.4 is 39.50 m: B = 42.7 [39.4, 46.6]**,
on 521 transient rows, width 1.18×. One caveat attaches and is stated rather than
hidden: 39.50 m is *also* one of the flip levels, carrying **1 barrier-jump row out
of 521** (0.19 %). A spurious transient failure inflates P_transient and therefore
*deflates* B, so the artifact biases 42.7 downward by about 0.2 % — negligible
against the 1.18× interval, and conservative in direction.

## 2.10 Stage D at KP 57.4, and what the negative control revealed

Because KP 57.4's two design-HWL anchors are unresolved (2 and 10 rows), Stage D
also evaluated the **lowest resolved level, 39.50 m** — an addition made on
measured evidence and declared as such, since an epistemic band on an unresolved
ratio says nothing. At KP 62.0 that level coincides with A1, so the addition costs
nothing and is not a second bite at the anchor question.

**The m_p control failed at KP 57.4's A1 (rho = 1.707) — and diagnosing that
honestly matters more than the arm results.** §1.7 committed that if the control
misses [1/1.5, 1.5], "the machinery is wrong and no other arm is trusted or
reported". Taken at face value that would void the whole section. It is not the
right reading, and here is the evidence:

| anchor | baseline transient rows | m_p rho | control |
|---|---|---|---|
| KP 57.4 A3 (39.50 m) | 521 | **0.901** | **PASS** |
| KP 62.0 A2 (46.50 m) | 176 | **0.925** | **PASS** |
| KP 62.0 A1 (46.39 m) | 63 | **1.010** | **PASS** |
| KP 57.4 A2 (39.25 m) | 10 | 1.550 | FAIL |
| KP 57.4 A1 (39.21 m) | 2 | 1.707 | FAIL |

The control is **monotone in the row count**: it passes at every anchor carrying
63 rows or more and fails only at the two anchors that R1 had *already* declared
unresolved, where its interval spans 1.0 enormously ([0, 6.20] at A1). That is a
counting-noise failure, not a machinery failure — the same 2 and 10 rows that make
those anchors unquotable make the control uninformative there. **Consequence
applied: the KP 57.4 A1 and A2 arm results are discarded and not reported as
findings.** Only the A3 column below is used. The machinery stands, on the strength
of three independent passes at adequate counts.

**KP 57.4 at 39.50 m (baseline B = 42.7 on 521 rows):**

| arm | P_f static | P_f transient (k) | **B** | rho | resolved |
|---|---|---|---|---|---|
| **baseline** | 2.225e-2 | 5.210e-4 (521) | **42.7** | — | — |
| `k_aq_regional_upper` | 3.142e-1 | 4.119e-2 (41 191) | **7.63** | 0.179 | yes |
| `z_toe_minus0.30m` | 1.232e-1 | 1.058e-2 (10 576) | **11.6** | 0.273 | yes |
| `gamma_bl_sub_lower` | 2.225e-2 | 6.450e-4 (645) | 34.5 | **0.808** | yes |
| `m_p` *(control)* | 3.567e-2 | 9.270e-4 (927) | 38.5 | 0.901 | yes |
| `L_dem_clean_median` | 9.384e-3 | 1.510e-4 (151) | 62.1 | 1.455 | yes |
| `z_toe_plus0.30m` | 9.850e-4 | 2.00e-6 (2) | 492 | 11.5 | yes* |
| `k_aq_field_toe` | 1.50e-5 (15) | **0** | **unbounded** | — | — |
| `k_aq_field_geomean` | **0** | **0** | indeterminate | — | — |

\* resolved on 2 rows; not reportable, listed for completeness.

**Criterion F3 FIRES at KP 57.4 — the opposite verdict to KP 62.0.** Under
`k_aq_field_toe` the static comparator still produces 15 failures in 1e6 while the
transient model produces **none**: the overestimation factor is genuinely
unbounded, not merely large. Against a statistical width of 1.18× that is an
unbounded ratio, far past the threshold of 10. (Restricting to adequately-counted
finite arms gives 7.63 to 62.1 = 8.1×, i.e. 6.9× the statistical width — still the
dominant uncertainty.) Following the house convention that an arm driving P_f to
exactly zero is reported as unbounded rather than as a convenient finite number,
**F3 fires here and does not at KP 62.0** — the difference being that KP 62.0's
zero-count arm zeroes *both* branches, so its ratio is indeterminate rather than
infinite.

**One arm behaves differently from KP 62.0, and consistently with ADR-0048.**
`gamma_bl_sub_lower` is *exactly* inert at KP 62.0 (rho = 1.000, identical failure
set) but moves the ratio a resolved 19 % at KP 57.4's 39.50 m (rho = 0.808). That
is what ADR-0048 predicts: the blanket unit weight bites only near the bottom of a
section's reachable range, and 39.50 m sits there for KP 57.4 while 46.39 m does
not for KP 62.0. KP 57.4's thicker blanket (D_bl 0.8 m against 0.45 m) is the same
property that makes its head-convention component dominant in §4.1.

---

# PART 3 — VERDICT

## 3.1 Outcome against each pre-registered criterion

| criterion | pre-registered in | outcome |
|---|---|---|
| **R1** k_trans ≥ 30 | §1.1 | **MET** at KP 62.0 A1 (63 rows) and A2 (176) |
| **R2** CI width ≤ 2.0× | §1.1 | **MET** — 1.63× at A1, 1.34× at A2 |
| **Resolution verdict** | §1.1 | **RESOLVED at KP 62.0, both anchors** |
| **F1** statistical falsifier | §1.3 | **did not fire** — brute force met R1 and R2 directly; the §1.1 fallback chain was never entered |
| **F2** anchor knife-edge | §1.3 | **did not fire** — the A1 and A2 intervals overlap. (Paired test, declared as an addition: rho = 1.249 [1.039, 1.556], resolved — a real 25 % change over 11 cm) |
| **F3** epistemic swamping | §1.3 | **section-specific: did NOT fire at KP 62.0** (9.0 against a threshold of 10); **FIRED at KP 57.4** (unbounded — the field-`k_aq` arm gives static failures with zero transient failures) |
| **V1** self-gate | §1.4 | **PASS** |
| **V2** no level disagrees | §1.4 | **FAIL** (1 of 30 levels) |
| **V3** no systematic offset | §1.4 | **PASS** |
| **V4** efficiency | §1.4 | **FAIL** (n_eff 86.9 < 200) |
| **Estimator verdict** | §1.4 | **NOT VALIDATED** — reported as a documented negative; brute force used throughout |
| **G-A1** drift guard | §1.5 | **PASS** — bit-identical, 38 + 23 levels |
| **G-A2** Euler flips | §1.5 | **PASS at KP 62.0** (0/39 levels); **FAILED at KP 57.4 N = 1e6** (4 rows in 1e6) |
| **G-A3** N-consistency | §1.5 | **PASS** — 59 branch comparisons, 0 failing |
| **G-A4** convergence | §1.5 | reported |
| **m_p control** | §1.7 | **PASS at all three anchors carrying ≥ 63 rows** (1.010, 0.925, 0.901); **FAIL at the two anchors carrying ≤ 10 rows** (1.550, 1.707), whose arm results are discarded in consequence |

## 3.2 Is the design-HWL bias quotable as a single number?

**At KP 62.0: yes — with three conditions stated inline, and never without its level.**

The number is **26.9**, 95 % CI **[21.6, 35.3]**, on 63 failing transient rows out of
1e6, at **46.39 m MSL**. It supersedes the 44.7 that appears in
`stage6_6_report.md` §8, `production_campaign_2026-07-29.md` §6.1 and
`adr0047-dem-seepage-length.md`, which rested on 4 rows and overstated the bias by
a factor of 1.66.

The conditions are not decoration; each is measured:

1. **Level.** The bias falls resolvably with stage — 26.9 at 46.39 m, 21.6 at
   46.50 m, and the paired test resolves that 25 % difference over 11 cm. A figure
   without its level is meaningless at the precision now available.
2. **Epistemic band, 6.4 to 7.2× the statistical one** (corrected 2026-09-04; see the addendum at the end of this note, which supersedes the "6 to 9×" this line carried). B runs from 2.59 (regional
   upper `k_aq`) through 26.9 (production) to 27–38 (the low-`k_aq` and +datum
   arms), and is indeterminate under the field-geomean conductivity where neither
   branch fails. `k_aq` dominates; `z_toe` is second; `m_p` cancels; `gamma_bl_sub`
   is exactly inert.
3. **Interpretation and geometry.** Matrix d70; the adopted L = 40.0 m (ADR-0047);
   `k_aq`-conditional per the Part 0 amendment and confirmed here at this very
   anchor.

**At KP 57.4: no.** Two failing transient rows at the design HWL out of 1e6. R1
fails, the estimator that was meant to close the gap did not validate, and the
honest deliverable is a **bound (B ≥ 148 at 95 %)** plus a **resolved anchor above
HWL: 42.7 [39.4, 46.6] at 39.50 m MSL**. The thesis should lead with the latter at
this section and quote the former as a bound, never 566 as a point estimate.

## 3.3 The sentences the thesis should use

Written out, with the conditionality inline. Two sentences, because the two
sections genuinely differ in what the data supports.

> **KP 62.0 (governing section).** Under the matrix *d*₇₀ interpretation and the
> adopted 40 m seepage length, the conventional static Sellmeijer criterion
> overestimates the per-event conditional probability of backward erosion piping at
> the planned high water level of 46.39 m T.P. by a factor of **26.9** (95 per cent
> confidence interval 21.6 to 35.3, from a paired bootstrap over 10⁶ realisations
> carrying 63 transient failures). The factor is specific to that stage — it falls
> to 21.6 only 0.11 m higher — and is conditional on the adopted aquifer
> conductivity and exit datum: the bounding scenarios of
> Section~\ref{sec: The Aquifer Conductivity Prior under Scrutiny} move it from 2.6
> at the upper regional conductivity to beyond 27 at the field-test values, a band
> six to nine times wider than the statistical interval.

> **KP 57.4 (contrast section).** At the planned high water level of 39.21 m T.P.
> the transient model yields two failures in 10⁶ realisations, too few to estimate
> the overestimation factor; the criterion is bounded below by a factor of **148**
> at 95 per cent confidence. The lowest stage at which the factor is statistically
> resolved is 39.50 m T.P., where it is **42.7** (95 per cent confidence interval
> 39.4 to 46.6).

**What must not be written.** "About 21" and "44.7" at KP 62.0, and "at least 32"
at KP 57.4, are all superseded. Neither "26.9" nor "42.7" may be quoted without its
stage. No figure from the tilted estimator may be quoted at all.

## 3.4 Everything this work supersedes

| # | Where | Superseded number | Replacement |
|---|---|---|---|
| 1 | `stage6_6_report.md` §1, §7 | KP 62.0 HWL bias *"about 21"* | **26.9 [21.6, 35.3]** at 46.39 m (already flagged superseded by §8; now resolved) |
| 2 | `stage6_6_report.md` §8 (table + prose) | **44.7** on 4 rows, "not resolved" | **26.9** on 63 rows, **resolved** |
| 3 | `stage6_6_report.md` §1, §7 | KP 57.4 *"at least 32 at 95 % confidence"* (zero rows) | **B ≥ 148**; quotable anchor **42.7 [39.4, 46.6] at 39.50 m** |
| 4 | `stage6_6_report.md` §4.1 KP 62.0 HWL row | C0 2.1e-4 / C4b 1.0e-5 (pre-adoption L = 47 m) | superseded twice over: ADR-0047 adoption, then N = 1e6 (1.696e-3 / 6.30e-5) |
| 5 | `production_campaign_2026-07-29.md` §6.1 KP 62.0 table | 46.39 m row: 44.7, resolved **no** | **26.9, resolved yes** (§12 closure note added; the §6.1 table stands as the N = 1e5 record) |
| 6 | `production_campaign_2026-07-29.md` §6.1 KP 57.4 table | 39.21 m row: *"lower bound only"* | bound quantified: **B ≥ 148** |
| 7 | `production_campaign_2026-07-29.md` §12 | decision 6 **open** | **CLOSED** |
| 8 | `adr0047-dem-seepage-length.md` §8 table row | "Stage 6.6 bias at HWL *(unresolved, 1 and 4 rows)* 21.0 → 44.7" | both entries superseded; the post-adoption value is **26.9, resolved** |
| 9 | `architecture.md` §12 Failure-mode-4 paragraph | "the HWL figure rests on single-digit rows and is not statistically resolved"; "KP57.4 … retains ≥32× at HWL, itself a zero-row bound" | KP 62.0 **is** now resolved (26.9); KP 57.4's bound is **≥ 148** |
| 10 | architecture and decision records Stage 6.6 and campaign bullets | "~21× KP62.0, ≥32× KP57.4 at HWL" | as above; new bullet added |

Item 9 is the only one whose prose is *wrong* rather than merely superseded, since
KP 62.0's resolution status has flipped; the rest are numeric replacements. Items
1–4 and 8–10 are documentation-only — **no persisted production artifact changes**,
because every production sweep runs at N = 1e5 and this study added arms rather
than replacing any.

**Fixed in this pass:** items 2–3 (`stage6_6_report.md` §9), 5–7
(`production_campaign_2026-07-29.md` §12 closure note), 9 (`architecture.md`,
rewritten because its resolution-status claim was wrong, not merely stale), and 10
(architecture and decision records bullet). Items 1, 4 and 8 sit inside dated addenda that already carry
a forward pointer to the authoritative section, so they are left legible as
historical record per house practice.

**Not touched, and deliberately.** The msc-thesis Chapter 6 that would host this
headline (`5. Results of the System Integration and Climate Sensitivity
Analysis.tex`, `\label{chap: Results: Subsurface Piping Assessment}`) is still a
**stub** — four `\section` headings and no body text. There is therefore no stale
copy of this number in the thesis to correct, and writing the results chapter is
outside this task's scope. §3.3 gives the two sentences ready to drop in when that
chapter is written.

## 3.5 What this study changed in the repository

**Nothing in production.** No `Config` default, no physics module, no
`configs/*.yaml`, no `data/processed/tokachi_bep_inputs.csv`, no persisted
production sweep, no numbered ADR. All Stage D knobs remain OFF (campaign decision
3); the arms exist only as in-memory `Config` copies. The existing N = 1e5 Stage 6.6
artifacts are untouched and still reproducible.

**Added:** `scripts/hwl_bias_resolution.py`, `tests/test_hwl_bias_resolution.py`
(25 tests), this note, `docs/decisions/adr0040-hwl-bias-resolution.json`, and the
N = 1e6 ladders and stage records under `results/hwl_bias_resolution/` (gitignored).

**One change to a shipped module:** `gap_decomposition.run_comparator_ladder`
gained a keyword-only `theta_override`, default `None`, bit-identical to previous
behaviour and pinned by four tests. It exists so a proposal population can be
pushed through the identical comparator machinery; a run using it stamps
`metadata['theta_override']` with a warning that the column means are proposal
frequencies, not probabilities.

**Two driver defects found and fixed in flight**, both worth recording because both
were bad practice rather than bad luck: a gate that raised *before* persisting
(destroying the 2.5 h of evidence it was raised about — now persist-then-gate, with
offending levels recorded), and a per-section writer that rebuilt its payload from
scratch and so silently dropped the other section's results (now merges).


---

## Addendum, 2026-09-04: the epistemic band is 6.4 to 7.2x, not 6 to 9x

Raised by the submission gate of that date
(`msc-thesis/scratch/SUBMISSION_GATE_2026-09-04.md`, finding 8): the thesis
quoted "6 to 9 times" at eight sites while the figure the same sentences cite,
`epistemic_vs_statistical.png`, annotates 6.4x, 7.2x and 6.9x. A reader
checking the figure could not find a 9 in it.

**Recomputed from this note's own evidence file**, over the arms that meet the
pre-registered R1 (at least 30 failing transient rows) and R2 (interval width
at most a factor of two):

| anchor | resolved arms | band | statistical CI | band / CI |
|---|---:|---:|---:|---:|
| KP 62.0, 46.39 m (A1) | 4 | 10.49 | 1.630 | **6.44** |
| KP 62.0, 46.50 m (A2) | 4 | 9.67 | 1.341 | **7.21** |
| KP 57.4, 39.50 m (A3) | 5 | 8.15 | 1.186 | **6.87** |

At A1 the resolved arms are `k_aq_regional_upper` 2.59 on 191,600 rows,
`z_toe_minus0.30m` 13.87 on 901, `gamma_bl_sub_lower` 26.92 on 63 and `m_p`
27.20 on 150.

**Where the 9 came from, and why it does not stand.** Section 2 above builds the
band as "2.59 through 26.9 to 27-38", and the 27-38 arms rest on 2, 3 and 9
failing transient rows. 2.59 to 38.0 is a factor of 14.7, which against the
1.630 CI gives 9.0. Those arms are below the thirty-row floor this study
discards on exactly that ground: the `m_p` negative control passes at all three
anchors with at least 63 rows and fails at the two with at most 10, monotone in
row count. **Quoting 9 therefore contradicts the study's own resolution
criteria.** The swamping test's verdict is unaffected either way, 9.0 and 6.4
both falling below the threshold of ten, so nothing downstream changes.

Chapter 6 of the thesis already carried the full derivation, "2.59 to 38.0, or
2.59 to 27.2 when restricted to adequate counts, which is 9.0 or 6.4 times the
statistical width of 1.63", and 6.9 for KP 57.4. The defect was only in the
compressed shorthand, which read as a range across anchors when it was two
readings at one anchor. All eight thesis sites and the figure title now carry
6.4 to 7.2, the reading restricted to adequate counts.
