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

*Part 2 is written after the driver has run. It evaluates the section 1 rules
against the section 1 statistics and records the outcome. It may not re-tune
anything above.*
