# The aquifer-conductivity bracket measured on the posterior side of the update

**Status:** Part 1 (pre-registration) written 2026-08-21 **before any arm was
replayed**. Part 2 (outcome) is appended after execution; it evaluates the
pre-registered rules against the pre-registered inputs and re-tunes nothing.

**Date:** 2026-08-21
**Driver:** `scripts/conductivity_annualisation_study.py --side posterior`
**Evidence:** `docs/decisions/conductivity-bracket-posterior-side.json` (matrix),
`docs/decisions/conductivity-bracket-posterior-side-bulk.json` (bulk)
**Tests:** `tests/test_conductivity_annualisation.py`
**Companion study, not an ADR.** No `Config` default, no configuration axis, no
physics, no persisted production sweep and no production Phase 3 artifact is
changed. Follows the `conductivity-bracket-annualisation.md` grammar, of which
this is the direct continuation.

**Scope, stated first because every number below inherits it. This note measures
the same four arms, the same four sections and the same two grain-size readings
as the prior-side record, carried one stage further: through the Phase 2
Accept-Reject survival update against the 2016 typhoon record, and only then
through the Phase 3 composition and annualisation. Phase 1 is not re-run; the
persisted ADR-0048 arm sweeps are consumed read-only, exactly as the prior-side
study consumes them. Both climates are covered and come free, because Phase 1
and Phase 2 are historical-only by ADR-0023 shape invariance and the climate
axis enters at the Phase 3 hazard.**

---

## Part 1 — Pre-registration

*Written and committed before the first Phase 2 arm replay existed. Nothing
below was adjusted after seeing a result; where a prediction failed, Part 2 says
so and the text here is left standing.*

### 1.1 What this closes

The residual limitation the prior-side record left open, and which the thesis
states in four places: Chapter 7 Section 7.2.3 ("the arms exist on the prior
side of the update only"), Chapter 7's synthesis ("What remains untested at this
level is the bracket on the posterior side, because no conductivity arm has been
run against the survival constraint"), Chapter 9 Section 9.1.3 ("The posterior
side remains unmeasured"), and the Chapter 8 limitations register ("prior side
only").

`conductivity-bracket-annualisation.md` §1.3 recorded the reason it was left
open: *"No Phase 2 posterior exists for any conductivity arm, and building one is
out of scope."* Nothing about that has changed except the scope. Every piece of
machinery this needs already exists: the ADR-0048 `prior_mean_scenario` knob that
produced the arms, the ADR-0048 decision-3 routing that makes the Phase 2 replay
regenerate a scenario's own shifted population rather than the baseline one, and
the Phase 3 composition and annualisation the prior-side study already drives.

### 1.2 The question, stated so that it can come out either way

Does the 2016 survival constraint **narrow**, **widen** or **leave unchanged**
the effect of the aquifer-conductivity bracket on (i) the annual system failure
probability, (ii) the mechanism ordering at each of the four characterised
sections in both climates, and (iii) the climate ratios?

### 1.3 Hypothesis and mechanism

**H1. The posterior-side bracket is narrower than the prior-side one, and the
narrowing is asymmetric: it comes almost entirely from the upper arm coming
down, not from the lower arms coming up.**

The mechanism, in four steps, each of which is a property this repository has
already measured rather than an assumption:

1. **Accept-Reject removes exactly the rows that breach under the 2016 load.**
   The rejection fraction `r` is therefore the prior conditional transient
   failure probability evaluated at the anchored 2016 stage,
   `r = P_prior(h_2016)`.

2. **The rejected set is nested inside the failing set at every higher stage.**
   `l_current` is monotonically non-decreasing, so a realization that breaches at
   `h_2016` breaches at any larger conditioning level. The Phase 2 self-test
   measured this directly: marginal transient rejection is 0 at N = 1e5 at every
   stratum. The posterior conditional curve is therefore
   `P_post(h) = (P_prior(h) - r) / (1 - r)` for `h >= h_2016`.

3. **The update's bite is set by the ratio `r / p`, not by `r` alone.** From
   step 2 the relative reduction is `r(1 - p) / (p(1 - r))`, which for small `p`
   is approximately `r / p`. The update bites hardest where an arm's own
   conditional probability over the stage band that carries the annual number is
   closest to that arm's own rejection fraction.

4. **A high-conductivity arm raises `r` by far more than it raises `p` over the
   driving band.** ADR-0048 measured the conditional amplification as strongly
   stage-dependent and decaying with stage: x198 to x2428 at the lowest reachable
   level, x1.9 to x2.0 at the shoulder, x1.0 at the grid top. The 2016 anchor
   sits at or below the tenth percentile of the contribution-weighted driving
   stage band at all four sections (39.658 against a p10 of 39.95 at KP 57.4;
   40.75 against 40.47 at KP 58.8; 42.296 against 41.82 at KP 60.0; 45.729
   against 47.50 at KP 62.0). The upward arm amplification is therefore large
   where `r` is read and small where `p` is read, so `r / p` rises with
   conductivity. The downward arms drive both `r` and `p` toward zero and are
   left essentially untouched.

Steps 1 to 4 give: **top of the bracket pulled down, bottom of the bracket
unmoved, bracket narrower.**

### 1.4 What is fixed before measuring

**Arms.** The same four persisted ADR-0048 companion sweeps per section and per
reading, consumed read-only, N = 1e5:

| arm | parameter | target mean | factor at KP 57.4 / 58.8 / 60.0 / 62.0 |
|---|---|---|---|
| `k_aq_field_geomean` | `k_aq` | 5.94e-5 m/s | x0.0198 / x0.0297 / x0.0594 / x0.0594 |
| `k_aq_field_toe` | `k_aq` | 5.15e-4 m/s | x0.172 / x0.258 / x0.515 / x0.515 |
| `k_aq_regional_upper` | `k_aq` | 1.0e-2 m/s | x3.33 / x5.0 / x10 / x10 |
| `gamma_bl_sub_lower` | `gamma_bl_sub` | 6.0 kN/m3 | x0.870 (all) |

`gamma_bl_sub_lower` is retained as the **negative control**, on the same
argument the prior-side study used: it is free, and if it moves a posterior
annual number materially the machinery is wrong rather than the physics
interesting.

**Sections, readings, climates, variant axis.** The four geotechnically
characterised sections (KP 57.4, 58.8, 60.0, 62.0); both co-primary grain-size
readings; both climates; lambda_ac = 250 m; surface variant primary;
`bep_source = posterior`. The 110 segments carrying no BEP source are inert by
construction and are reported only as an invariance check.

**Phase 2 settings, pinned to the production campaign field for field.** Anchor
`trace_right`, criterion `no_breach`, `verify_by_reevaluation` on, breach-time
tracing on, figures off, `n_bootstrap` 1000, `z_toe_delta_m` 0.0, data root
`data/raw`, processed dir `data/processed/2016_event`. An arm that differs from
production in any field other than its input path is refused, not tabulated.

**Baseline posterior numbers this is measured against**, read from
`results/system_integration/phase3/rq4_annual.csv` before anything ran, matrix
reading, and quoted here so the comparison cannot be re-based afterwards:

| section | historical prior | historical posterior | +4K prior | +4K posterior |
|---|---|---|---|---|
| KP 57.4 | 7.5479e-4 | 7.5295e-4 | 9.5425e-3 | 9.5311e-3 |
| KP 58.8 | 8.4669e-3 | 7.4195e-3 | 4.4617e-2 | 4.0913e-2 |
| KP 60.0 | 2.0250e-3 | 1.8018e-3 | 1.5341e-2 | 1.4175e-2 |
| KP 62.0 | 1.0060e-3 | 1.0060e-3 | 1.2778e-2 | 1.2778e-2 |

**Baseline rejection fractions**, likewise read before anything ran:

| section | matrix | bulk |
|---|---|---|
| KP 57.4 | 0.065 % | 0.000 % |
| KP 58.8 | 5.673 % | 0.000 % |
| KP 60.0 | 3.363 % | 0.023 % |
| KP 62.0 | 0.000 % | 0.000 % |

**Prior-side bracket spans to be beaten**, from the committed record. Matrix,
historical / +4K: KP 57.4 unbounded / 27.6, KP 58.8 185 / 48.6, KP 60.0 4.4e5 /
2.8e3, KP 62.0 69.1 / 8.27. Bulk, at the six cells where that record's B9
reports both readings finite: 4.54, 4.40, 3.53, 1865, 2.07 and 1.16.

### 1.5 Predictions

* **P1 (monotonicity).** The rejection fraction is monotone non-decreasing in the
  effective `k_aq` prior mean at every section and both readings:
  `field_geomean <= field_toe <= baseline <= regional_upper`.
* **P2 (the upward arm rejects materially more).** `k_aq_regional_upper` rejects
  more than baseline at all four sections under the matrix reading, and by more
  than a factor of two at KP 58.8 and KP 60.0.
* **P3 (the sharpest single test).** At KP 62.0 under matrix the baseline
  rejection is exactly 0.000 %, which is why the thesis currently records that
  section prior and posterior annual numbers as identical to full
  floating-point precision. `k_aq_regional_upper` is predicted to reject a
  **non-zero** fraction there, which would make the posterior side at KP 62.0
  something other than a copy of the prior side for the first time.
* **P4 (the downward arms are inert to the update).** Both downward arms reject
  no more than baseline, and their posterior annual numbers differ from their
  prior ones by less than the 12.4 % maximum shift the baseline itself shows.
* **P5 (bracket width, the headline).** The posterior span `max/min` of
  `p_annual_system` over arms is **smaller** than the prior span at every cell
  where both are finite, and the narrowing is **modest rather than
  order-of-magnitude**: less than a factor of two at every cell. The reason for
  the modesty is step 3 read the other way, that the annualisation is carried by
  stages well above `h_2016` where `p` is much larger than `r`.
* **P6 (the ordering does not move).** Every one of the sixteen ordering verdicts
  of the prior-side record (ROBUST / REVERSED / COLLAPSED, per section, climate
  and reading) is reproduced on the posterior side. Under matrix every reversal
  is driven by a **downward** arm, which P4 predicts inert; and the upward arm,
  which is the one the update bites, reverses nothing there. **Under bulk this is
  the prediction most likely to fail**, because under bulk it is the **upward**
  arm that does all the reversing, and that is exactly the arm the update
  attacks. If P6 fails it fails at KP 58.8 historical or KP 62.0 historical, the
  two bulk cells where `regional_upper` hands the lead to piping by the smallest
  margin.
* **P7 (climate ratios move less than the annual numbers).** Every arm
  +4K/historical system ratio changes by less than 20 % from its prior-side
  value, because the update applies one common subtraction to a fragility curve
  shared by both climates, which differ only in hazard weighting.
* **P8 (control).** `gamma_bl_sub_lower` rejects within a factor of two of
  baseline and changes no ordering anywhere, under either reading.

### 1.6 What would falsify this reading

* **F1 (bug signature, not a finding).** Any arm posterior annual number
  **exceeds** its prior one at any cell. Accept-Reject can only remove
  realizations, and under the step-2 nesting the conditional curve cannot rise.
  A rise indicts the pipeline and is refused rather than reported. The one
  physically admissible route to it is a failure of nesting on the transient
  branch, which the Phase 2 self-test measured as exactly zero at N = 1e5; if it
  appears here it is measured and reported as a nesting failure, not smoothed.
* **F2.** The rejection fraction is non-monotone in `k_aq` (P1 fails). That would
  indict the arms or the replay, because ADR-0048 records the conductivity
  mechanism as monotone and one-directional.
* **F3 (the falsifier for H1).** The posterior span is **wider** than the prior
  span at any cell. The only mechanism that could produce it is the update
  biting harder on a **downward** arm than on the upward one, which step 4
  predicts impossible. If observed, H1 is refuted and the thesis must say the
  survival constraint **widens** the bracket, and say by how much.
* **F4 (the deflating outcome, named in advance so it cannot be dressed up).**
  If the posterior span differs from the prior span by less than 1 % at every
  cell, then the honest result is that **the survival constraint leaves the
  bracket unchanged**, and the thesis sentence becomes a measured null. That is
  a perfectly good result and is to be reported as such, not written up as a
  narrowing that the numbers do not support.
* **F5 (contamination).** Any arm whose `config_hash` does not round-trip, whose
  N is not 1e5, whose conditioning grid differs from its baseline, whose
  grain-size reading differs from the one under test, or whose `Phase2Settings`
  differ from production in any field other than the input path. Refused at the
  gate, never reported.

### 1.7 Gates fixed in advance

* **GATE 1, non-negotiable.** Before any arm number is reported, the **baseline
  posterior** curves are pushed through this study own pipeline and must
  reproduce `results/system_integration/phase3/rq4_annual.csv` **exactly**, field
  for field, for every `posterior` / lambda_ac 250 / primary row of the reading
  under test. Mismatch aborts.
* **GATE 2.** Each arm Phase 2 run is asserted to carry `Phase2Settings`
  identical to production in every field except the input and output paths, and
  each arm sweep is asserted N = 1e5 with a round-tripping `config_hash` carrying
  the expected `prior_mean_scenario` label and the expected `d70_interpretation`.
* **GATE 3.** The 110 segments with no BEP source are asserted bit-identical
  between baseline and every arm.
* **GATE 4.** The hazard cache file set and digests are asserted unchanged across
  the run.
* **GATE 5.** No production artifact is written. The study writes only under
  `results/sensitivity/conductivity_posterior*/`, its own evidence JSON and, if
  one earns its place, its own figure.
* **GATE 6.** Every arm replay runs with theta verification on, so ADR-0048
  decision 3 is exercised: a scenario arm must regenerate **its own** shifted
  population, not the baseline one. A false pass here would be the subtlest
  possible way for this study to measure the wrong thing.
* **GATE 7.** The prior-side record is re-run unchanged as part of this campaign
  and must still reproduce its committed evidence JSON, so that any difference
  reported between the two sides is attributable to the update and not to drift
  in the pipeline between 2026-08-10 and today.

### 1.8 Cells predicted to change from the prior-side record

KP 58.8 and KP 60.0 under matrix, at every arm, because those are the two
sections where the baseline update already moves the annual number by 11 % and
12 %. KP 62.0 under matrix at `k_aq_regional_upper` only, per P3. KP 57.4 under
matrix negligibly at every arm. Under bulk, essentially nothing except at
`k_aq_regional_upper`, because the baseline bulk rejection is 0.000 % at three
of four sections and 0.023 % at the fourth.

---

## Part 1a — Amendment to GATE 2, 2026-08-21, before the campaign ran

*A pre-registration may be amended, but only in the open. This records what was
changed, what was known at the time it was changed, and why the change cannot
move any measured number. Section 1.7's GATE 2 as written above stands
everywhere except in the one field named here.*

**What changed.** `trace_breach_times` is exempted from the "identical to
production in every field other than the input path" clause, and the campaign
runs with it **off**. Every other Phase 2 setting stays gated equal, including
the two that define the acceptance rule (`anchor = trace_right`,
`criterion = no_breach`) and the one that discharges GATE 6
(`verify_by_reevaluation = True`).

**Why.** `breach_times_for_rows` (`replay.py`) re-runs the scalar M8 evaluator
with trajectory storage once per **rejected** row. Its cost is therefore linear
in exactly the quantity a high-conductivity arm inflates. Measured on the
worst-case arm, KP 58.8 matrix under `k_aq_regional_upper`:

| | rejected rows | wall clock |
|---|---|---|
| production baseline, tracing on | 5 673 | 273 s |
| this arm, tracing **on** | 65 530 | **5 902.2 s** |
| this arm, tracing **off** | 65 530 | **65.5 s** |

**A factor of 90.** Across 32 replays that is the difference between about
three quarters of an hour and about two days, and the campaign would not have
been run at all.

**Why it cannot move a number.** `run_survival_update` fixes `state.alive` in
the Accept-Reject chain and only afterwards enters the tracing block; the
posterior is `posterior_fragility_from_matrices(run, state.alive, ...)`, which
never reads the traced array. `t_breach` is persisted and, when figures are on,
plotted. Figures are off here.

The structural argument was then confirmed by measurement on the worst-case arm
above, which is the strongest available test of it: at 65 530 traced rows, any
side effect of tracing has the largest opportunity to show. The two runs agree
**bit-identically** on every quantity the Phase 3 annualisation consumes, and on
the two that define the update:

| quantity | verdict |
|---|---|
| `conditioning_grid` | identical |
| `P_f_trans_post_raw`, `P_f_static_post_raw` | identical |
| `binomial_ci` lower and upper, both branches | identical |
| fitted `mu` and `sigma`, both branches | identical |
| `rejection_fraction`, `n_accepted` | identical |
| Phase 2 settings | differ in `trace_breach_times` and `output_dir`, nothing else |

**What is lost.** The arm posteriors carry no breach-time diagnostic. That is a
diagnostic this study does not use and does not report. The production
posteriors, which do carry it, are untouched.

**Disclosure, because pre-registration discipline requires it.** At the moment
this amendment was written, one number bearing on the predictions had been
seen: the rejection fraction of KP 58.8 matrix under `k_aq_regional_upper`,
65.53 % against the baseline 5.673 %. It is consistent with P1, P2 and the
step-4 mechanism. No prediction was altered in the light of it, and the
predictions in §1.5 stand exactly as committed in `4bec61a`.

**One caveat this pilot surfaced, recorded here so Part 2 cannot bury it.** At
34 470 accepted rows the upward arm falls below the 50 % headroom floor Phase 2
warns at, so its posterior tail resolution is degraded relative to the Phase 1
spec §11 standard. That is a property of the arm, not of the amendment, and it
must be carried wherever that arm's posterior numbers are quoted.

---

## Part 2 — Outcome

*Appended after execution. Empty at pre-registration time.*
