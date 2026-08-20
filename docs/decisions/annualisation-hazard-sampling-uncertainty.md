# Hazard-sampling uncertainty on the Phase 3 annualised results

**Status: Part 1 pre-registered 2026-08-20, before Part 2 existed and before a
single interval was computed. Part 2 records the outcome and may not re-tune
anything in Part 1.** Un-numbered companion study: it adds no `Config` field,
changes no default and alters no persisted production result, so it consumes no
ADR number. See section 1.8 for that judgement in full.

---

## Scope of the claim

**Every number this study produces is hazard-sampling uncertainty only: the
finite-ensemble spread of the d4PDF peak-stage distribution with the fragility
curves held fixed, which is not the total uncertainty and is far smaller than
the aquifer-conductivity bracket that dominates it and does not cancel.**

That sentence is not a footnote. It travels in the same sentence as every
interval, in this note, in the evidence record, in the figure and in the thesis
handoff. The bracket it defers to is measured in
`conductivity-bracket-annualisation.md`: at KP 58.8 historical, prior side,
matrix reading, the conductivity arms move the annual piping contribution from
8.39e-3 to 4.65e-7 per year, a factor of about 1.8e4. Any hazard-sampling
interval below is a fraction of one production value; the conductivity bracket
is four orders of magnitude of it.

---

## 0. What the live artifacts say

Executed 2026-08-20, before Part 1 was written, precisely so the pre-registered
estimator would be chosen against measured ensemble structure rather than
against an assumption about it. Nothing here is a bootstrap result.

### 0a. No annualised uncertainty exists anywhere. Confirmed.

`system_integration/annualize.py::AnnualizedResult` carries six fields plus
`coverage`: scenario, `n_years`, `p_f_annual_system`,
`p_f_annual_per_mechanism`, `mechanisms`, `sources`. None of them is an
uncertainty of any kind, and `coverage` is the HKV-audit item 2 clamp
diagnostic, not a spread. `annualize()` returns `float(np.mean(...))` over the
ensemble peaks and nothing else. `rq4_annual.csv` has 20 columns and 2,280
rows; no column carries a spread, a standard error or an interval.

The only confidence intervals anywhere in Phase 3 are the Clopper-Pearson
binomial bands on the **conditional** Phase 1 fragility, loaded into
`system_integration/bep_input.py` as `ci_lower` / `ci_upper` and then **never
read again**: `compose()` consumes `MechanismCurve.p_f` alone and `annualize()`
consumes `SystemFragility.p_sys` alone. The conditional uncertainty that does
exist is dropped at the composition boundary. Every other `binomial_ci` call in
the repository (`scripts/hwl_bias_resolution.py`, `qa_re_halved_member.py`,
`stage6_6_gap_decomposition.py`, `thesis_figure_gaps.py`,
`canonical_shape_sensitivity_study.py`, `plot_fragility_curves.py`,
`epistemic_bracket_synthesis.py`, `dem_cross_section_study.py`) is on a
conditional per-level probability. No script computes an annualised one.

Chapter 7 concedes it in prose: *"No sampling uncertainty is attached to these
annual probabilities or to the ratios formed from them."*

### 0b. The ensemble is nested, and the nesting is exactly balanced.

Read from the 228 cached node files under
`results/system_integration/hazard_cache/`.

| Scenario | Events | Structure | Blocks | Years per block |
|---|---|---|---|---|
| historical (HPB) | 3,000 | `HPB_mNNN_YYYY`, 50 members x 60 calendar years 1951 to 2010 | **50** | 60 |
| +4K (HFB) | 5,400 | `HFB_SST_mNNN_YYYY`, 6 SST patterns (CC, GF, HA, MI, MP, MR) x 15 members x 60 years 2051 to 2110 | **90** | 60 |

The simulated years are nested inside ensemble members, perfectly balanced at
60 per member with no ragged block. **An i.i.d. bootstrap over years is
therefore not a resample of the ensemble's independent units and is the wrong
estimator.** A block bootstrap over members is used instead; the block is the
(SST-pattern, member) pair, which is 50 blocks historical and 90 warming.

All 114 nodes carry the **identical event-id sequence** in both scenarios, both
rivers included, so one block draw per scenario applies at every node and every
between-node comparison can be paired.

Measured intra-cluster correlation of the actual estimand, `P_sys(peak_j)`,
on the matrix / posterior curves (design effect in brackets):

| Section | Scenario | by member | by calendar year | by SST pattern |
|---|---|---|---|---|
| KP 57.4 | historical | -0.0008 (1.00) | -0.0026 (1.00) | n/a |
| KP 57.4 | +4K | +0.0035 (1.21) | +0.0031 (1.28) | +0.0032 (**3.84**) |
| KP 58.8 | historical | +0.0036 (1.21) | +0.0024 (1.12) | n/a |
| KP 58.8 | +4K | +0.0049 (1.29) | +0.0083 (1.74) | +0.0089 (**9.00**) |
| KP 60.0 | historical | +0.0014 (1.09) | -0.0016 (1.00) | n/a |
| KP 60.0 | +4K | +0.0050 (1.30) | +0.0050 (1.45) | +0.0056 (**5.99**) |
| KP 62.0 | historical | -0.0007 (1.00) | -0.0024 (1.00) | n/a |
| KP 62.0 | +4K | +0.0032 (1.19) | +0.0032 (1.28) | +0.0035 (**4.16**) |

Two facts follow, and they pull in opposite directions, so both are stated.
The member clustering is weak on this estimand (design effect 1.00 to 1.30), so
the member block will not differ greatly from the naive i.i.d. estimator: the
structural correctness of the block choice is an argument about validity, not a
promise of a much wider interval. But the +4K **SST-pattern** grouping carries a
design effect of 3.8 to 9.0, because 5,400 events sit in only six SST families.
That axis is treated in section 1.6 and is deliberately not the headline.

### 0c. The stratified counts. Confirmed.

From `rq4_attribution.json`, historical, long-duration stratum
(`hours_above_datum > 24`): KP 57.4 **n = 3**, KP 58.8 n = 152, KP 60.0
n = 105, KP 62.0 n = 19. Under +4K: 42, 727, 531, 186. The compound stratum
historically: 5, 35, 27, 10. Chapter 7's claim that the KP 57.4 long-duration
stratum rests on three simulated years is exactly right, and the KP 57.4
compound stratum rests on five.

### 0d. The KP 62.0 tie. Confirmed.

Matrix, posterior, 250 m, primary, +4K: `share_bep` = 0.500336129664227,
`share_overflow` = 0.499663870335773, so 0.500 against 0.500 to three decimals
as the thesis table prints. The production margin
`p_annual_bep / p_annual_overflow` = **1.00135**, which the thesis rounds to
1.0013. Both claims reproduce. The posterior and prior arms are identical to
full precision at KP 62.0, as expected: the 2016 update rejects 0.00 % there.

### 0e. Two claims that need their arm named, found while verifying.

Neither is an error in the thesis, but both would be misquoted by a later
session that assumed one arm throughout, so they are recorded here.

* The **43-fold margin at KP 58.8** is the **prior**-side number (43.0079).
  On the posterior side, which is what Table `tab: system annual` prints, the
  same margin is **37.61**. The thesis quotes 43 in the sentence that hands off
  to the conductivity bracket, and the conductivity companion is prior-side, so
  the arms are consistent where they are used. This study reports the interval
  on both.
* The four climate ratios 12.7 / 5.5 / 7.9 / 12.7 are **system** ratios
  (12.658, 5.514, 7.867, 12.701 posterior side). The neighbouring sentence's
  12.6 / 5.5 / 7.9 / 9.8 are **piping-only** ratios. Different quantities,
  correctly distinguished in the text; the handoff keeps them apart.

---

## 1. Pre-registration

### 1.1 The estimator and its resampling unit

For one node and one scenario the production estimator is

    P_annual = (1/n) * sum_{j=1..n} P(peak_j),   n = 3000 or 5400,

with `P` the composed system curve or one mechanism's curve, evaluated at the
event peak stage through the production interpolators. The fragility curves are
**held fixed** at their production values throughout. Only the hazard is
resampled.

**The resampling unit is the d4PDF ensemble member**, the (SST-pattern, member)
block: 50 blocks historical, 90 warming, 60 events each, exactly balanced.
A replicate draws K blocks with replacement and recomputes the same mean over
the resampled 60K events. Implemented as block multiplicities drawn from
`Multinomial(K, uniform)`, which is exactly the with-replacement draw and makes
each replicate one matrix product against the per-block sums.

Justified by section 0b: the years are nested inside the members, so they are
not n independent draws, and the member is d4PDF's unit of independent
integration.

**One block draw per scenario, shared across all 114 nodes.** Every node carries
the identical event sequence (0b), so the same multiplicities apply everywhere.
This leaves each node's marginal interval untouched, since its R replicate means
are still i.i.d. draws from its own bootstrap distribution, and makes every
between-node difference **paired** -- which Q1 needs, and which this
repository's own paired-bootstrap practice (ADR-0040 decision 6) requires of any
difference measured on a shared sample.

**The two scenarios are drawn independently**, from separate seeded streams,
because the two ensembles are disjoint. The climate ratio is formed **inside**
each replicate,

    ratio_r = P_annual_warming_r / P_annual_historical_r,

so the reported interval is an interval on the ratio and never a quotient of two
marginal intervals.

**Point estimates are always the unresampled production values**, never a
bootstrap mean. The bootstrap supplies the interval and nothing else.

### 1.2 Replicates

**R = 10,000 per scenario**, fixed now. Above the 2,000 floor, because the
multiplicity formulation makes the marginal cost of a replicate one row of a
(R x K) by (K x C) product, and because at R = 10,000 the 95 % percentile ends
are order statistics 250 and 9,750 rather than 50 and 1,950, which matters for
the near-tie decisions in Q2 and Q3.

Seed: fixed integer constant recorded in the evidence record. The study is
deterministic given it, and re-running it must reproduce the record.

### 1.3 Interval type

**Two-sided 95 % percentile interval**, endpoints at the 2.5th and 97.5th
percentiles of the replicate distribution. Not BCa: the estimand set spans
means, shares and ratios at 114 nodes, and the acceleration constant would have
to be estimated per node per quantity from the same 50 or 90 blocks that are
already the binding resource. A percentile interval on a mean of a bounded
[0, 1] quantity is the honest, checkable choice, and its known weakness (it does
not correct for skew) is in the conservative direction for a quantity whose
replicate distribution is right-skewed.

### 1.4 Resolution criteria

**Q1. Are the four per-section climate ratios resolvably different from one
another?**

Statistic: for each of the six unordered pairs (i, j) of {KP 57.4, KP 58.8,
KP 60.0, KP 62.0}, the **paired** difference `D_ij,r = ratio_i,r - ratio_j,r`,
formed with the same historical multiplicities and the same warming
multiplicities at both sections in replicate r.

Rule: pair (i, j) **resolves** iff the 95 % percentile interval of `D_ij`
excludes 0. The global answer to Q1 is YES only if all six pairs resolve;
otherwise the answer is the explicit list of which pairs do.

**Q2. Is the KP 62.0 warming mechanism split resolvably distinguishable from a
tie?**

Statistics, both paired inside a replicate at the KP 62.0 node under +4K:
`D_r = P_bep,r - P_overflow,r`, and the dominance share
`S_r = P_bep,r / (P_bep,r + P_overflow,r + P_scour,r)`.

Rules:

1. The split is resolvably **not** a tie iff the 95 % interval of `D` excludes 0.
2. The three-decimal quotation "0.500 against 0.500" is **supported** iff the
   two endpoints of the 95 % interval of `S` round to the same third decimal.
   If they do not, the third decimal is not an estimated digit and the thesis
   must print fewer.

**Q3. Are the historical mechanism shares (81 to 100 per cent) resolvable as a
lead?**

Statistic: per section, historical, the share `S_r` as in Q2.

Rules:

1. Piping's **lead** at a section is resolved iff the lower endpoint of the
   95 % interval of `S` exceeds 0.5.
2. A quoted share is supported at the precision printed iff both interval
   endpoints round to that same printed value (0.81 and 0.97 at two decimals;
   1.000 exactly for a structurally degenerate section, see rule 3).
3. **Degenerate sections are classified apart, not reported as a resolved
   share.** KP 57.4 and KP 60.0 historical carry `p_annual_overflow` exactly 0
   because no simulated historical year loads the overflow branch at all. Their
   share interval is [1, 1] in every replicate. That is a statement about
   coverage, not a zero-width confidence statement about a probability, and it
   is recorded with that wording. Pre-registered because the state is known in
   advance from section 0d's arm table.

### 1.5 What would make each question unanswerable at this ensemble size

Named now, so the verdict cannot be redefined after the numbers are seen.

* **Q1 unanswerable** if two or fewer of the six pairs resolve. In that case the
  four ratios are not distinguishable at this ensemble size, and the thesis must
  say so rather than rank sections by ratio. A named partial outcome: if exactly
  the three pairs involving KP 58.8 resolve, the only defensible claim is that
  KP 58.8's ratio is the smallest of the four, and nothing finer -- in
  particular not an ordering among the other three, and not the near-equality of
  the two 12.7s as a finding.
* **Q2 is answerable either way and cannot be unanswerable.** A non-exclusion is
  the positive finding that the split is a statistical tie, which is what
  Chapter 7 already argues on the separate grounds of the canonical-event
  sensitivity. An exclusion at a production margin of 1.00135 would be the
  surprising outcome and would have to be reported as such, with the
  contradiction against the canonical-event flip stated rather than smoothed.
  What *would* be unanswerable is the finer question of which mechanism leads:
  if rule 1 does not fire, no lead may be asserted at KP 62.0 under warming in
  either direction.
* **Q3 unanswerable at a section** if that section's share interval straddles
  0.5, in which case the lead there is not resolved and the "81 to 100 per cent"
  range must be replaced by an interval-bearing statement at that section.
  **Unanswerable outright** if all four straddle 0.5, in which case the
  annualised dominance claim does not survive hazard-sampling uncertainty and
  must be withdrawn as an annualised claim (it would survive as a conditional
  one, which is a different and weaker statement). A third, specific failure:
  if the two degenerate sections are the only ones whose lead resolves, the
  range statement rests entirely on coverage rather than on measurement, and
  must be worded that way.

### 1.6 Pre-registered sensitivities on the resampling unit

Reported in the evidence record, never quoted as the headline interval. Their
purpose is to show what the choice of block is worth rather than to leave the
reader to wonder.

* **S1, i.i.d. over events.** The naive estimator the production numbers
  implicitly assume. Quantifies what the nesting is worth.
* **S2, calendar-year block** (60 blocks in both scenarios). The crossed axis:
  in HPB all 50 members share the *observed* SST of a given calendar year, so
  the year is a shared-forcing group even though the member is the nesting
  parent.
* **S3, SST-pattern block, +4K only** (6 blocks). Declared **in advance** as
  structural climate-model uncertainty rather than hazard-sampling noise: the
  six SST patterns are a deliberate design spanning CMIP5 structural spread, not
  a random sample, and a percentile interval from six units is not trustworthy
  at its ends. It is reported because section 0b measured it as the largest
  hazard-side grouping by a wide margin, and suppressing the largest measured
  structure would be the more misleading choice. It is never presented as the
  hazard-sampling interval.

### 1.7 Gates

A gate failure aborts; it is never tabulated and worked around.

0. **Internal consistency.** For every node, scenario and curve, the
   unresampled mean of this study's per-event probability matrix must equal the
   corresponding `AnnualizedResult` field **exactly**, so the bootstrap is
   provably resampling the production quantity and not a lookalike.
1. **Reproduces the production table, string-identically.** The unresampled
   baseline must reproduce `results/system_integration/phase3/rq4_annual.csv`
   field for field, as strings, over all 228 matrix / prior / 250 m / primary
   rows -- and, because that is the arm Chapter 7's table actually prints, over
   the 228 matrix / posterior rows as well, plus both bulk arms: **912 rows**
   in total. Load-bearing: without it the study is not measuring the production
   quantity and no interval may be reported.
2. **The hazard cache is byte-unchanged.** SHA-256 of every cache file before
   and after; no workbook may be streamed.
3. **Nothing outside the study's own output directory is written**, apart from
   this note, its evidence record and the one figure it amends.

### 1.8 What this study is not, and the ADR judgement

It resamples the **hazard only**. The fragility curves are fixed, so this is
not the total uncertainty and never will be. It says nothing about the
conductivity bracket, the grain-size reading, the canonical event, the seepage
length or the model-factor knobs, each of which is measured elsewhere and each
of which is larger.

It re-runs no Phase 1 sweep, no Phase 2 update and no hazard extraction. It
consumes the persisted artifacts and the warm hazard cache read-only. The
composition step is **imported** from `scripts/phase3_campaign.py`, never
re-implemented, so gate 1 exercises the production code path; a test forbids a
second copy.

**No numbered ADR.** Judged against `bep-change-control` section 1, whose
distinguishing question is *"can this change what a baseline run computes,
under any setting a user can reach"*. It cannot: no `Config` field is added, no
default changes, no persisted production result is altered, and no knob exists
to turn on. It is the same class as the HKV-audit item 2 coverage diagnostics,
which recorded something about already-computed values and consumed no number,
and the same class as the `conductivity-bracket-annualisation` companion, which
propagated an existing bracket through an existing composition. Un-numbered
companion note plus evidence JSON, under the `docs/conventions.md` section 9.2
descriptive-name grammar. Recorded here so the judgement is explicit rather
than inferred from the absence of an ADR.

---

## 2. Outcome

Executed 2026-08-20 by `scripts/annualisation_uncertainty_study.py`, R = 10,000,
seed 20260820, about 45 s. Evidence:
`docs/decisions/annualisation-hazard-sampling-uncertainty.json`; the full
114-segment table is under gitignored
`results/sensitivity/annualisation_uncertainty/reach_intervals.json`. Section 1
was not touched after the numbers were seen.

**The scope sentence at the top of this note applies to every number below.**

### 2.1 Gates

All four passed. Gate 0: every per-event probability vector's unresampled mean
equals its `AnnualizedResult` field exactly, at every node, scenario and curve
of all four arms, with no tolerance. Gate 1: **912 published rows reproduced
field for field, 20 fields each** -- 228 rows in each of matrix/prior,
matrix/posterior, bulk/prior and bulk/posterior at 250 m and the primary surface.
Gate 2: all 228 hazard-cache files byte-unchanged, no workbook streamed. Gate 3:
every file under `results/system_integration/phase3/` byte-unchanged.

### 2.2 The headline intervals

Matrix, posterior, 250 m, primary -- the arm Chapter 7's system annual table
prints. 95 % percentile, hazard-sampling only.

| Section | historical | +4K | climate ratio |
|---|---|---|---|
| KP 57.4 | 7.53e-4 [3.46e-4, 1.22e-3] | 9.53e-3 [7.51e-3, 1.16e-2] | 12.7 [7.3, 28.1] |
| KP 58.8 | 7.42e-3 [5.39e-3, 9.66e-3] | 4.09e-2 [3.65e-2, 4.54e-2] | 5.51 [4.13, 7.73] |
| KP 60.0 | 1.80e-3 [1.13e-3, 2.55e-3] | 1.42e-2 [1.20e-2, 1.64e-2] | 7.87 [5.34, 12.9] |
| KP 62.0 | 1.01e-3 [5.33e-4, 1.57e-3] | 1.28e-2 [1.02e-2, 1.55e-2] | 12.7 [7.7, 24.8] |

Relative half-widths run **29 to 58 % historically and 11 to 21 % under
warming**, the warming numbers being tighter because the ensemble is 5,400 years
against 3,000 and because more of it loads the section at all. **Every absolute
annual probability in Chapter 7 is therefore quoted to about one significant
figure of sampling precision, and the second digit is not an estimated digit.**

The KP 58.8 dominance margin, prior side, is **43.0 [33.9, 57.9]**; the same
margin on the posterior side is **37.6 [30.2, 49.4]**.

### 2.3 Q1. The four climate ratios: PARTIAL, 5 of 6 pairs resolve

| Pair | difference | 95 % interval | resolved |
|---|---|---|---|
| KP 57.4 - KP 58.8 | +7.14 | [+2.58, +21.1] | yes |
| KP 57.4 - KP 60.0 | +4.79 | [+1.54, +15.9] | yes |
| **KP 57.4 - KP 62.0** | **-0.04** | **[-1.00, +3.83]** | **no** |
| KP 58.8 - KP 60.0 | -2.35 | [-5.44, -0.97] | yes |
| KP 58.8 - KP 62.0 | -7.19 | [-17.7, -3.04] | yes |
| KP 60.0 - KP 62.0 | -4.83 | [-12.5, -2.01] | yes |

Five of six resolve, which is above the pre-registered unanswerable threshold of
two, so Q1 is answered rather than abandoned. The one that does not is exactly
the pair the thesis prints as two identical 12.7s. **That is the useful finding
and it is a negative one: KP 57.4 and KP 62.0 rise by a factor this ensemble
cannot tell apart, so their near-equality is not a property of the two sections.
It must not be read as one.** Everything else in the ordering survives, including
the claim Chapter 7 actually rests on, that KP 58.8 has the smallest ratio of the
four.

Two mechanical points. The differences are **paired on all 10,000 replicates**:
every one of the 114 nodes carries the identical event sequence, so one block
draw serves them all and the difference reflects the discordance between two
sections rather than the variance of two independent estimates. Had the pairing
been dropped, every one of these six intervals would have been wider and the
verdict weaker for a reason with no physical content. And no replicate had an
undefined ratio at any of the four sections, so nothing was discarded.

### 2.4 Q2. The KP 62.0 warming split: a TIE, and the third decimal is not real

Paired inside each replicate at KP 62.0 under +4K:

* `p_bep - p_overflow` = +1.13e-5, 95 % interval **[-9.23e-4, +9.07e-4]**. The
  interval contains zero by two orders of magnitude of its own width, so
  pre-registered rule 1 does not fire.
* `share_bep` = 0.500, 95 % interval **[0.476, 0.532]**. The endpoints round to
  0.476 and 0.532, not to a common third decimal, so pre-registered rule 2 does
  not fire either.
* The margin `p_bep / p_overflow` = 1.0013, 95 % interval **[0.909, 1.139]**.

**Verdict: the split is not distinguishable from level, and the three-decimal
quotation "0.500 against 0.500" is not supported by the data behind it.** The
thesis already reads the KP 62.0 tie as a knife edge on the separate ground that
the canonical event flips it; this is an independent second reason, and the
stronger one, because it does not depend on choosing an event. The right way to
print the number is one decimal, or "level", with the interval attached.

Q2 was pre-registered as answerable either way, and it was: the non-exclusion is
the answer, not a failure to get one.

### 2.5 Q3. The historical shares: the lead resolves at four of four, two only by coverage

| Section | share | 95 % interval | lead resolved | classification |
|---|---|---|---|---|
| KP 57.4 | 1.000 | [1.000, 1.000] | yes | **structurally degenerate** |
| KP 58.8 | 0.974 | [0.968, 0.980] | yes | measured |
| KP 60.0 | 1.000 | [1.000, 1.000] | yes | **structurally degenerate** |
| KP 62.0 | 0.812 | [0.690, 0.980] | yes | measured |

Piping's historical lead clears 0.5 at every section, so the dominance claim
survives hazard-sampling uncertainty. Two qualifications travel with it, both
pre-registered.

**The two 1.000s are coverage, not measurement.** At KP 57.4 and KP 60.0 the
overflow branch returns exactly zero at every one of the 3,000 simulated years,
so the share is 1.000 in every replicate. That is a statement about what the
ensemble loads, not a zero-width confidence statement about a probability, and
the record says so in those words.

**Neither measured share supports the precision Chapter 7 prints.** KP 58.8's
0.974 is [0.968, 0.980], which rounds to 0.97 or 0.98 depending on the endpoint;
"about 97 per cent" is right, "97 per cent" overstates. KP 62.0's 0.812 is
**[0.690, 0.980]**, so **the "81" that forms the lower end of the thesis's "81 to
100 per cent" range is a one-significant-figure quantity at best**: the honest
range statement is "69 to 100 per cent", or "81 per cent, 95 % interval 69 to 98
per cent". This is the one place where a headline number in Chapter 7 needs
rewording rather than merely annotating.

### 2.6 The resampling unit was worth little, and the SST design is worth a lot

Relative half-width of the annual system probability, primary arm, per unit:

| Unit | blocks (hist / +4K) | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|---|
| **member** (the estimator), historical | 50 | 56.4 % | 29.1 % | 40.2 % | 49.9 % |
| member, +4K | 90 | 21.1 % | 10.6 % | 15.2 % | 19.9 % |
| S1 i.i.d. over events, historical | 3,000 | 59.7 % | 26.9 % | 39.0 % | 52.3 % |
| S1 i.i.d. over events, +4K | 5,400 | 19.7 % | 9.5 % | 13.8 % | 18.9 % |
| S2 calendar year, historical | 60 | 55.9 % | 28.7 % | 38.0 % | 49.0 % |
| S2 calendar year, +4K | 60 | 22.0 % | 12.3 % | 16.4 % | 21.3 % |
| S3 sea-surface pattern, +4K | 6 | 35.0 % | 25.0 % | 30.6 % | 34.8 % |

**The nesting is worth almost nothing on this estimand.** The member block is
within about 10 % of the naive i.i.d.-over-events width, in both directions, and
the measured intra-cluster correlation behind that is 0.00 to 0.005. **The member
block is used because it is the valid estimator, not because it is the wider
one**, and stating that plainly is more useful than implying the correction
mattered: it means a reader who mentally applied the naive binomial intuition to
these numbers was not far wrong about their width, only about their justification.

**The sea-surface-pattern grouping is a different matter.** Under warming the
5,400 events sit in six SST families, and resampling those six widens the
interval by a factor of 1.6 to 2.4 (for example KP 58.8, 25.0 % against 10.6 %).
That number is reported and is deliberately **not** the headline, for the reason
pre-registered in section 1.6: the six patterns are a design spanning CMIP5
structural spread, not a random sample, so resampling them measures
climate-model structural uncertainty rather than hazard-sampling noise, and a
percentile interval from six units is untrustworthy at its ends. It is recorded
because it is the largest measured grouping in the ensemble and suppressing it
would be the more misleading choice. **If a reader wants one sentence: the
warming intervals here would roughly double if the choice of climate model's
sea-surface pattern were treated as sampled rather than given.**

### 2.7 Where this does not reach

The nine Uemura section aggregates are intervalled in the record as well, because
Chapter 7 quotes Tokachi 4 alongside the segment numbers and it is a different
node's curve: **7.48e-3 [5.44e-3, 9.72e-3] historically and 4.10e-2 [3.67e-2,
4.55e-2] under warming, ratio 5.49 [4.12, 7.68]**. Six of the nine have a
historical value at or near zero; two of those (Satsunai KP 5.2 and KP 4.2) are
exactly zero in every replicate and have no ratio at all, and three more
(Tokachi KP 61.4, Satsunai KP 7.0 and KP 6.4) have an undefined ratio in 5 to
13 % of replicates. **Those ratios are not quotable and the record marks them
so**, which is consistent with Chapter 7 already calling them "arithmetically
enormous and uninformative".

Nothing here touches the stratified entries of the RQ4 attribution table. The
KP 57.4 long-duration stratum still rests on three simulated years (section 0c),
and a three-year conditional mean is not rescued by an interval on a different
quantity. It should continue to be presented as the thesis presents it, with the
count visible.

Nothing here is total uncertainty. The intervals above are between about 10 and
60 per cent of a production value. The conductivity bracket at the same sections
spans four orders of magnitude and reverses the mechanism ordering. **A reader
who takes the interval and forgets the bracket has the uncertainty backwards.**

---

# Part two: the stratified entries of the RQ4 attribution table

**Status: section 3 pre-registered 2026-08-20, before any stratified interval
was computed and before the driver carried a line of stratified code. Section 4
records the outcome and may not re-tune anything in section 3.** Same study,
same estimator, same record; this extends the companion rather than opening a
second one.

Section 2.7 above closed with a refusal: *"Nothing here touches the stratified
entries of the RQ4 attribution table. The KP 57.4 long-duration stratum still
rests on three simulated years, and a three-year conditional mean is not rescued
by an interval on a different quantity."* That sentence is right about KP 57.4
and wrong as a statement about the table, because it generalises a count
argument from the sparsest cell to seven others that are not sparse. Section 3.2
measures the occupancy of every cell; two of the eight duration cells carry more
ensemble members than there are SST patterns in the whole warming ensemble by an
order of magnitude, and refusing them an interval on KP 57.4's grounds is the
mirror image of quoting KP 57.4 as though it had one.

**The scope sentence at the top of this note applies to every number in this
part too.** These are hazard-sampling intervals with the fragility curves held
fixed, and the conductivity bracket remains four orders of magnitude wider.

---

## 3. Pre-registration, part two

### 3.1 The question

Table `tab: rq4 attribution` in Chapter 7 prints, per section and climate, a
conditional annual probability inside and outside a duration stratum, their
ratio (the concentration factor), and the share of the annual total the long
stratum contributes. The concentration-factor row is quoted as the range **151
to 378** in the Summary, in Chapter 7 twice, in Chapter 8 twice and in Chapter 9
four times, and the share row supplies the **"89 and 93 per cent"** claim at
KP 58.8 and KP 60.0. None of them carries an interval. This part asks which of
them can be given one, and states in advance the occupancy at which the answer
becomes no.

### 3.2 The counts, measured before the floor was fixed

Executed 2026-08-20 from the 8 cached node files at the four characterised
sections, read-only through `system_integration.hazard._read_cache`. Nothing
here is a bootstrap result; these are properties of the ensemble as simulated.
A **carrying member** is a d4PDF ensemble member, the study's resampling unit
from section 1.1, holding at least one event of the stratum. There are 50
members historically and 90 under warming.

Long-duration stratum, `hours_above_datum > 24`:

| Section | Scenario | Years | Carrying members | of | SST patterns | Largest member's share |
|---|---|---|---|---|---|---|
| KP 57.4 | historical | **3** | **3** | 50 | 1 | 33.3 % |
| KP 58.8 | historical | 152 | 46 | 50 | 1 | 5.3 % |
| KP 60.0 | historical | 105 | 43 | 50 | 1 | 5.7 % |
| KP 62.0 | historical | 19 | **14** | 50 | 1 | 15.8 % |
| KP 57.4 | +4K | 42 | 33 | 90 | 6 | 7.1 % |
| KP 58.8 | +4K | 727 | 90 | 90 | 6 | 2.3 % |
| KP 60.0 | +4K | 531 | 88 | 90 | 6 | 2.6 % |
| KP 62.0 | +4K | 186 | 72 | 90 | 6 | 4.3 % |

Compound stratum, `n_peaks_above_datum >= 2`, which supplies the separate
"3.7 to 91 historically" and "1.6 to 23 under warming" ranges in the same
subsection:

| Section | Scenario | Years | Carrying members | of | Largest member's share |
|---|---|---|---|---|---|
| KP 57.4 | historical | **5** | **5** | 50 | 20.0 % |
| KP 58.8 | historical | 35 | 23 | 50 | 8.6 % |
| KP 60.0 | historical | 27 | 20 | 50 | 7.4 % |
| KP 62.0 | historical | 10 | **9** | 50 | 20.0 % |
| KP 57.4 | +4K | 29 | 25 | 90 | 6.9 % |
| KP 58.8 | +4K | 131 | 71 | 90 | 5.3 % |
| KP 60.0 | +4K | 101 | 58 | 90 | 5.0 % |
| KP 62.0 | +4K | 72 | 53 | 90 | 6.9 % |

The complement stratum is never the binding one: the short-duration stratum
holds 2,848 to 5,214 years and 50 or 90 carrying members in every cell.

Three things follow, and they are the reason a floor is needed rather than a
blanket verdict in either direction.

* The year counts confirm section 0c and the chapter's own text. KP 57.4's
  long-duration stratum is 3 years in **3 distinct members**, so a bootstrap
  over members has three carrying blocks to work with, not three years' worth of
  something better.
* KP 58.8 and KP 60.0 historically carry 46 and 43 of the 50 members. The
  chapter already singles out exactly this pair as *"the two sections where the
  historical loading is frequent enough for the stratification to be well
  populated"*, and it is that pair which carries the 89 and 93 per cent claim.
  The chapter's own qualitative judgement and the measured block occupancy agree.
* KP 62.0 historically sits between them at 19 years in 14 members, and is the
  one cell where the verdict will depend on where the line is drawn rather than
  being obvious from either end.

### 3.3 The floor, fixed now

**A stratified quantity is reported with a 95 % interval only where both of the
following hold, evaluated on the smaller of the two strata forming it.**

> **F1, occupancy.** At least **20 distinct member blocks** carry at least one
> event of the stratum.
>
> **F2, concentration.** No single member block holds more than **20 %** of the
> stratum's events.

**Justification of F1, stated without reference to any section.** The resampling
unit is the member block, so a stratum's information is carried by the m blocks
that hold at least one of its events, not by its year count. Two independent
requirements both land on the same number.

*The estimator must be defined in every replicate.* A bootstrap replicate omits
a given block with probability `(1 - 1/K)^K`, which is 0.364 at K = 50 and 0.367
at K = 90, so the probability that a replicate contains none of the m carrying
blocks is about `e^-m`. At m = 10 that is 4.5e-5, which at R = 10,000 is an
expected 0.45 replicates with an empty stratum and an undefined conditional
mean. At m = 20 it is 2.1e-9, an expected 2e-5. This matters because this
study's existing practice discards undefined replicates (`ratio_replicates`
holds them as `nan` and the interval is taken over the rest), and an interval
computed after discarding is silently conditioned on the stratum being
non-empty. A floor that permits discarding is not a floor.

*No single block may carry more leverage than the project's own tolerance.* Each
carrying block's expected multiplicity is 1, so under roughly even occupancy a
block's weight in the stratum's conditional mean is about `1/m`, and dropping it
moves that mean by `1/m` of its deviation. Requiring that leverage to sit at or
below the project's standing 5 % Monte Carlo tolerance, the Schweckendiek (2014)
figure this repository already uses in ADR-0031 and ADR-0032, gives
`1/m <= 0.05` and therefore **m >= 20**.

**Justification of F2.** F1 bounds the *average* block weight, and an average
hides concentration: a stratum can clear m >= 20 while one member holds most of
its events, in which case the interval's endpoint is a two-atom object, that
block present or absent, wearing a percentile's clothes. F2 caps the most
influential block at four times the weight F1 permits a uniform one. It is
expected **not** to bind at the occupancies section 3.2 measures, and section 4
will say plainly whether it bound, in the ADR-0032 idiom where a pre-registered
conservative pole that turns out not to bind is itself the reportable outcome.

**This floor is not blind and does not claim to be.** Section 3.2 was measured
before it was written, exactly as section 0 preceded section 1, so a reader can
see that the counts were known. The defence is therefore not ignorance of the
counts but two things that are checkable: the justification above names no
section and would read identically had the counts come out differently, and
section 3.6 pre-registers a **sensitivity of the verdict to the floor itself**,
reported at 10 and at 30 blocks alongside the fixed 20, so that any verdict which
depends on the exact value is visible as such rather than presented as robust.

**Scope of the floor.** Every stratified entry of Table `tab: rq4 attribution`,
both stratifications, both climates, all four sections. It is not extended to
the annual quantities of part one, which are means over the whole ensemble at 50
or 90 carrying blocks and were never in question.

### 3.4 What is printed below the floor

A cell that fails F1 or F2 is reported as **the count and no number**:

> its year count, its carrying-member count out of 50 or 90, the failing
> criterion, and the production point estimate labelled as count-limited.

No interval, no half-width, no relative width, and no resolution verdict of any
kind. The production point estimate stays visible, because it is arithmetically
exact for the ensemble as simulated and it is the value the thesis prints, but
**it may not be an endpoint of any range quoted as measured**, and no statement
of the form "resolvably larger than" or "not distinguishable from" may be made
about it. A count-limited cell may be compared with an intervalled one only in
the one direction that costs nothing: whether its point estimate falls inside
the other's interval, reported as a consistency observation and never as a
measurement.

### 3.5 The quantities and their estimator

No change of method. Same block bootstrap over d4PDF ensemble members, same
R = 10,000, same seed 20260820, same two-sided 95 % percentile interval, same
**shared multiplicity draw**, so every stratified quantity is paired with every
other one and with the annual quantities of part one on the replicate index. The
point estimate is always the unresampled production value and never a bootstrap
mean. The arm is **matrix / posterior / 250 m / primary**, which is the only arm
`rq4_attribution.json` exists for, so the reported numbers are the production
quantity rather than a variant of it.

Stratum membership is a property of the event and is carried through the
resample with it. Inside replicate r, with block multiplicities `c_b`:

    p_in,r   = sum_b c_b * S_in,b  / sum_b c_b * n_in,b
    p_out,r  = sum_b c_b * S_out,b / sum_b c_b * n_out,b
    C_r      = p_in,r / p_out,r                       (the concentration factor)
    share_r  = sum_b c_b * S_in,b  / sum_b c_b * S_all,b

with `S_.,b` the per-block sum of the composed system probability over the
events of that stratum in that block and `n_.,b` the per-block event count. Both
the ratio and the share are formed **inside** the replicate, so each interval is
an interval on the quantity itself and never a quotient of two marginal
intervals, which is the same rule part one applied to the climate ratio.

### 3.6 Resolution criteria

**Q4. Is the concentration-factor range "151 to 378" supported?**

1. The defensible range is the envelope of the cells that clear the floor, at
   the printed precision their intervals support. A cell below the floor is
   named alongside it with its count and is never an endpoint.
2. Two clearing cells are **resolvably different** iff the 95 % percentile
   interval of their **paired** difference excludes zero. If the two historical
   clearing cells do not resolve, the range collapses and must be replaced by a
   single statement covering both.
3. A quoted value is supported at the precision printed iff both endpoints of
   its interval round to that same printed value.

**Q5. Is the "89 and 93 per cent" share claim supported?**

Same three rules applied to the share of the annual total from the long stratum,
with rule 3 evaluated at the two significant figures the chapter prints.

**Q6, the floor sensitivity.** Q4 and Q5 are additionally scored at floors of 10
and 30 carrying blocks. Reported, never used to choose. The pre-registered
verdict is the one at 20.

### 3.7 What would make this unanswerable

Named now, so the verdict cannot be redefined afterwards.

* **Unanswerable outright** if fewer than two cells clear the floor, in which
  case there is no range to defend and the concentration factor must be quoted
  per cell with its count, with no range statement anywhere in the thesis.
* **The range collapses**, rather than being unanswerable, if two or more cells
  clear but no pair of them resolves. The honest statement is then a single
  concentration factor with one interval covering the clearing cells, and the
  present four-number spread is an artifact of reading point estimates as
  measurements.
* **Q5 unanswerable at a section** whose share interval is wider than the gap
  between the two printed shares, in which case "89 and 93" must become one
  number for both.
* A cell that clears F1 but fails F2 is **below the floor**, not a special case.
  It is reported under section 3.4 with F2 named as the failing criterion.

### 3.8 Gates

Additional to the four of section 1.7, which are re-asserted unchanged.

4. **Reproduces `rq4_attribution.json` exactly.** Every field of every one of
   the 8 section-and-climate entries, by float equality with no tolerance: the
   two conditional probabilities and the stratum size of both stratifications,
   the loading fractions, the median duration and the year count. Load-bearing
   in the same way gate 1 is: without it the bootstrap is not resampling the
   published stratified quantity.
5. **The stratified pass changes no number in part one.** The multiplicity draw
   is the one already made; every interval in sections 2.2 to 2.7 must come out
   unchanged, which is what proves the extension added a quantity rather than
   perturbing the estimator.

---

## 4. Outcome, part two

Executed 2026-08-20 by the same `scripts/annualisation_uncertainty_study.py`,
R = 10,000, seed 20260820, the same multiplicity draw as part one. Evidence:
the `stratified_attribution` block and the `Q4`, `Q5`, `Q4_compound` and
`Q6_floor_sensitivity` entries of
`docs/decisions/annualisation-hazard-sampling-uncertainty.json`. Section 3 was
not touched after the numbers were seen.

**The scope sentence at the top of this note applies to every number below.**

### 4.1 Gates

All six passed. Gates 0 to 3 are re-asserted **unchanged** by the same run:
gate 1 reproduced **912 published rows**, 20 fields each, across all four
250 m / primary arms; the 228 hazard-cache files and every file under
`results/system_integration/phase3/` came out byte-unchanged.

**Gate 4**, new: all 8 section-and-climate cells of `rq4_attribution.json`
reproduced field for field through the production `stratified_annual_p_f`,
by float equality with no tolerance, over the two conditional probabilities
and the stratum size of both stratifications plus the year count, the two
loading fractions and the median duration. Its 4a half asserts that the
unresampled block estimator reproduces those conditional means; bit-identity is
**not** asserted there and is not achievable, because the block-grouped sum
reorders the addends `np.mean` adds pairwise. The bound is 1e-12 relative and
the **worst measured deviation over every cell is 2.57e-16**, which is one unit
in the last place.

**Gate 5**, new: the random stream's state is unchanged across the stratified
pass, so part one's draw is the one used. Checked directly as well: every key
of the record outside the new blocks, including all four arms' section
intervals, the nine section aggregates, Q1 to Q3 and the resampling-unit
sensitivity, is **byte-for-byte identical to the committed part-one record**.
The extension added a quantity; it moved nothing.

### 4.2 Which cells clear the floor

Applied mechanically, exactly as section 3.3 fixed it.

| Stratifier | Scenario | Clears | Below the floor |
|---|---|---|---|
| duration | historical | KP 58.8 (46 blocks), KP 60.0 (43) | KP 62.0 (14), KP 57.4 (3) |
| duration | +4K | all four (33, 90, 88, 72) | none |
| compound | historical | KP 58.8 (23), KP 60.0 (20) | KP 62.0 (9), KP 57.4 (5) |
| compound | +4K | all four (25, 71, 58, 53) | none |

**The floor's own first requirement is verified rather than assumed:
zero of the 10,000 replicates left any clearing stratum empty**, at every
clearing cell of both stratifications and both climates, so no interval below
was computed after discarding anything.

**F2 did not bind.** It fired once, at KP 57.4 historical duration, where the
single largest member block holds 33.3 % of a three-event stratum, and there F1
had already failed on 3 blocks against 20. It excluded no cell F1 admitted, and
the two 20.0 % cells (KP 57.4 and KP 62.0 compound, historically) sit exactly at
the cap rather than above it. This is the ADR-0032 pattern: a pre-registered
conservative guard that turns out not to be the binding one is a reportable
outcome, not a wasted clause.

### 4.3 The concentration factor

Duration stratum, matrix / posterior / 250 m / primary, 95 % percentile.

| Section | Scenario | Occupancy | Concentration factor |
|---|---|---|---|
| KP 57.4 | historical | 3 yr in 3 of 50 | **151, count-limited, no interval** |
| KP 58.8 | historical | 152 yr in 46 of 50 | 153 [98, 252] |
| KP 60.0 | historical | 105 yr in 43 of 50 | 378 [141, 1358] |
| KP 62.0 | historical | 19 yr in 14 of 50 | **221, count-limited, no interval** |
| KP 57.4 | +4K | 42 yr in 33 of 90 | 54 [39, 75] |
| KP 58.8 | +4K | 727 yr in 90 of 90 | 64 [51, 82] |
| KP 60.0 | +4K | 531 yr in 88 of 90 | 72 [54, 97] |
| KP 62.0 | +4K | 186 yr in 72 of 90 | 35 [25, 50] |

**Q4 historical: RANGE SUPPORTED.** Two cells clear, and their paired
difference is **-225 [-1131, -9.3]**, which excludes zero, so the two endpoints
are resolvably different from one another and the spread between them is a
measured range rather than two point estimates read as though they were.

**Q4 +4K: the range holds, the ordering inside it does not.** All four clear;
the endpoint pair KP 60.0 against KP 62.0 is **+36 [+17, +61]** and resolves, as
do KP 57.4 against KP 62.0 and KP 58.8 against KP 62.0. The three pairs that do
not resolve are the ones among KP 57.4, KP 58.8 and KP 60.0, whose factors of
54, 64 and 72 are not distinguishable from one another. The defensible warming
statement is the range 35 to 72 and the single ordering claim that KP 62.0 is
the lowest of the four; not a ranking of the other three.

**Rule 3: not one of the eight values supports the precision the table prints.**
The intervals are 24 % to 161 % of their own point in relative half-width. At
KP 58.8 historically "153" is a value between 98 and 252; at KP 60.0 "378" is a
value between 141 and 1358, uncertain by an order of magnitude. The
concentration factors are one-significant-figure quantities, and the KP 60.0
historical one is barely that.

### 4.4 The share of the annual total from long-duration years

| Section | Scenario | Share | 95 % interval |
|---|---|---|---|
| KP 57.4 | historical | 13 % | **count-limited, no interval** |
| KP 58.8 | historical | 89 % | [84, 93] |
| KP 60.0 | historical | 93 % | [83, 98] |
| KP 62.0 | historical | 59 % | **count-limited, no interval** |
| KP 57.4 | +4K | 30 % | [21, 39] |
| KP 58.8 | +4K | 91 % | [89, 93] |
| KP 60.0 | +4K | 89 % | [85, 92] |
| KP 62.0 | +4K | 56 % | [47, 65] |

**Q5 historical: COLLAPSED, and this is the finding.** The two cells that clear
are exactly the pair the chapter quotes as "89 and 93 per cent", and their
paired difference is **-0.041 [-0.101, +0.043]**, which contains zero. **The two
shares are not distinguishable from one another.** They are one number, about
90 per cent, at both sections; printing them as two invites a reader to see a
difference between KP 58.8 and KP 60.0 that this ensemble cannot resolve. Rule
3 fails as well: neither endpoint pair rounds to its printed whole percentage.

**Q5 +4K:** five of the six pairs resolve, including the endpoint pair, so the
warming range 30 to 91 per cent stands. The one pair that does not is again
KP 58.8 against KP 60.0, at **+0.022 [-0.005, +0.052]**. Across both climates,
therefore, the KP 58.8 and KP 60.0 shares are never distinguishable from each
other, which is a consistent property of the pair rather than a historical
accident.

### 4.5 The two count-limited cells, and the one comparison that is permitted

**KP 57.4 historical** fails both criteria: 3 simulated years in 3 of the 50
ensemble members, with one of them holding a third of the stratum. **KP 62.0
historical** fails F1 alone: 19 years in 14 of 50. Neither carries an interval,
a half-width or a resolution verdict, per section 3.4.

The one comparison section 3.4 permits, because it costs nothing, is where each
count-limited point falls relative to the clearing cells' intervals. It runs in
opposite directions for the two quantities, and both directions are stated.

* **Concentration factor.** KP 57.4's 151 and KP 62.0's 221 both fall **inside
  both** clearing intervals, [98, 252] and [141, 1358]. Nothing about the
  measured cells suggests the withheld ones behave differently; they are
  unmeasured, not anomalous.
* **Share.** KP 57.4's 13 per cent and KP 62.0's 59 per cent fall **outside
  both** clearing intervals, [84, 93] and [83, 98]. That is an observation about
  where an unmeasured value sits and **not** a measurement that the sections
  differ, because these two cells have no interval with which to make one.

### 4.6 Q6, the floor sensitivity, and what it settles

Membership of the clearing set at three floors, with the point-estimate range
that follows. No interval was computed for a cell the pre-registered floor
excludes; section 3.4 forbids printing one and a declared sensitivity does not
suspend a rule fixed in advance.

| Floor | duration / historical | compound / historical |
|---|---|---|
| 10 blocks | KP 58.8, KP 60.0, KP 62.0, range **153 to 378** | KP 58.8, KP 60.0, range 4 to 7 |
| **20 blocks (pre-registered)** | KP 58.8, KP 60.0, range **153 to 378** | KP 58.8, KP 60.0, range 4 to 7 |
| 30 blocks | KP 58.8, KP 60.0, range **153 to 378** | none, no range may be quoted |

**The headline verdict does not depend on the floor.** Halving it to 10 blocks
admits KP 62.0, and the range does not move, because KP 62.0's 221 lies inside
153 to 378 rather than outside it. Raising it to 30 changes nothing at all.
Whatever a reader thinks of 20 as a number, the duration range answer is the
same across the whole span, which is the strongest available answer to the
objection that section 3.3 could have been tuned after the counts were seen.

**The compound statement is a different matter, and is genuinely
floor-sensitive**: at 30 blocks no historical cell clears and no range may be
quoted at all. Where the compound stratification is discussed, the floor value
is load-bearing and should be named.

### 4.7 The compound stratification, beyond the question that was asked

Section 3.3 fixed the floor for **every** stratified entry of the table, and
having fixed it, applying it to the compound rows as well is what "apply the
rule mechanically" means. The result is recorded here rather than left for a
later session, because the compound range carries the same defect as the
duration one in a sharper form.

| Section | Scenario | Occupancy | Compound concentration factor |
|---|---|---|---|
| KP 57.4 | historical | 5 yr in 5 of 50 | **91, count-limited, no interval** |
| KP 58.8 | historical | 35 yr in 23 of 50 | 3.7 [0.3, 9.3] |
| KP 60.0 | historical | 27 yr in 20 of 50 | 6.5 [0.1, 18.4] |
| KP 62.0 | historical | 10 yr in 9 of 50 | **17, count-limited, no interval** |
| KP 57.4 | +4K | 29 yr in 25 of 90 | 22 [10, 40] |
| KP 58.8 | +4K | 131 yr in 71 of 90 | 1.9 [1.1, 2.8] |
| KP 60.0 | +4K | 101 yr in 58 of 90 | 1.6 [0.6, 2.9] |
| KP 62.0 | +4K | 72 yr in 53 of 90 | 5.5 [2.0, 10.6] |

Three things follow, and the third is the one that matters for the argument the
chapter makes.

* **The upper endpoint of "3.7 to 91 historically" is the 5-year cell.** The 91
  is KP 57.4, 5 simulated years in 5 of 50 members, below the floor. This is the
  same defect class as the "81" in part one's "81 to 100 per cent" range and as
  the "151" in the duration range, and in this case it is the worse of the two
  endpoints: the range is more than an order of magnitude wide and its wide end
  is the least populated cell in the whole table.
* **The two clearing historical cells do not resolve from one another**,
  at **-2.9 [-9.7, +0.9]**, so the historical compound statement collapses to a
  single unresolved value.
* **Neither clearing historical interval excludes 1.** KP 58.8 is 3.7 [0.3, 9.3]
  and KP 60.0 is 6.5 [0.1, 18.4]. Historically, the compound stratification does
  not resolve *any* concentration of risk at either well-populated section.
  Under warming it does at three of the four, and only weakly. **This
  strengthens the chapter's own conclusion rather than weakening it**: the
  argument there is that compound clustering is real but discriminates the
  dangerous years less sharply than duration does, and the sharper version is
  that historically the duration stratification resolves a concentration of
  about 150 and 380 while the compound stratification at the same two sections
  cannot be told apart from no concentration at all.

### 4.8 The defensible form of the headline

The range **151 to 378** is quoted in the Summary, in Chapter 7 twice, in
Chapter 8 twice and in Chapter 9 four times. Its lower endpoint is the 3-year,
3-member cell.

**What the sections clearing the floor support** is the range **about 150 to
about 380**, carried by KP 58.8 and KP 60.0, with 95 % flood-ensemble sampling
intervals of 98 to 252 and 141 to 1358, the two being resolvably different from
one another. The printed three-figure values 153 and 378 are not supported and
should be rounded.

**How the count-limited sections should be named alongside it**, never folded
into it: KP 62.0 at 221 on 19 simulated years in 14 of the 50 ensemble members,
and KP 57.4 at 151 on 3 years in 3 members, both without an interval. That both
happen to fall inside the measured range may be said as a consistency
observation, and the fact that this is why the numerical endpoints barely move
should be stated rather than relied on silently.

The recommended wording is in the thesis handoff at
`msc-thesis/scratch/BOOTSTRAP_HANDOFF.md`, section "Part two". The change to the
range's arithmetic is almost nothing, 151 becoming about 150. **The change to
what supports it is the entire point**: the endpoint stops resting on three
simulated years in three ensemble members, and starts resting on the pair of
sections the chapter itself already identifies as the well-populated one.

### 4.9 What this still does not reach

Section 2.7's refusal was too broad but it was not empty, and what survives of
it is recorded here.

* **KP 57.4's long-duration stratum is not rescued by anything in part two.**
  Three years in three members is below the floor by an order of magnitude and
  under F2 as well. The chapter should keep printing the count exactly as it
  does.
* **These are hazard-sampling intervals only.** The fragility curves are held
  fixed inside every one of them. The conductivity bracket at the same sections
  spans four orders of magnitude and does not cancel; a stratified interval of
  98 to 252 sits inside that bracket, not beside it.
* **Nothing here re-opens the loading strata themselves.** The duration
  stratifier is `hours_above_datum > 24` on the production datum, and the
  framework's shape invariance means peak magnitude and duration are not
  separable inputs to the fragility, which Chapter 7 already states as a
  structural qualification on the whole attribution. An interval on a stratified
  mean does not touch that.
