# Conductivity bracket propagated through the Phase 3 annualisation

**Status:** Part 1 (pre-registration) written 2026-08-10 before any number was
computed. Part 2 (outcome) appended after execution; it evaluates the
pre-registered rules against the pre-registered inputs and re-tunes nothing.

**Date:** 2026-08-10
**Driver:** `scripts/conductivity_annualisation_study.py`
**Evidence:** `docs/decisions/conductivity-bracket-annualisation.json`
**Figure:** `docs/figures/conductivity_bracket_annual.png`
**Tests:** `tests/test_conductivity_annualisation.py`
**Companion study, not an ADR.** No `Config` default, no configuration axis, no
physics, no persisted production sweep and no production Phase 3 artifact is
changed. Follows the `seepage-length-L-study.md` /
`epistemic-bracket-synthesis.md` / `r10-foreshore-exhaustion-screening.md`
grammar.

**Scope, stated first because every number below inherits it. Every number in
Part 2 is matrix-d70 and prior-side only; every number in Part 3 is bulk-d70 and
prior-side only. The two grain-size readings are co-primary deliverables, not a
result and a sensitivity, and the d70 half of the original scope was closed on
2026-08-10 by Part 3. The prior-side half stands: no Phase 2 posterior exists for
any conductivity arm under either reading.** Every quotation of any figure in
this note must carry the reading it came from.

---

## Part 1 — Pre-registration

*Written and committed before the study driver existed. Nothing below was
adjusted after seeing a result; where a prediction failed, Part 2 says so and
the text here is left standing.*

### 1.1 What this closes

Defence-brief item A2 and the Chapter 7 concession that the conductivity
bracket "was not tested at this level at all".

ADR-0048 established `k_aq` as the largest single epistemic knob quantified in
this project, and `epistemic-bracket-synthesis.md` extended that to all four
matrix sections and refuted ADR-0048's own consequence 3 (the bracket does not
cancel in the static-vs-transient ratio; it amplifies it). Both of those
measurements stop at the **conditional** fragility curve. Everything the thesis
answers for RQ3 and RQ4 is **annualised** — an integral of that curve against
the d4PDF peak-stage distribution — and no conductivity arm has ever been
carried across that integral. The largest declared unknown in the study has
therefore never been shown to matter, or not to matter, where the study's
headline claims live.

### 1.2 Hypothesis

Annualisation is a weighted average of the conditional curve over the ensemble
peak-stage distribution, so it samples only the part of the curve the hazard
actually reaches. Two competing effects follow, and they are the whole content
of the hypothesis:

* **Compression.** The synthesis §4(a) stage-dependence property says the
  conductivity spread is enormous at low stage and collapses toward unity where
  P_f saturates. Annual numbers are dominated by the frequent low and moderate
  peaks, so they sit in the *wide* part of the bracket, not the collapsed part.
  This argues the annualised bracket stays large.
* **Asymmetry against the ratio.** Unlike the Stage 6.6 static-vs-transient
  ratio, where both branches moved with `k_aq`, the mechanism-dominance ratio
  has a **fixed denominator**: overflow and fluvial scour are Uemura surface
  curves and carry no conductivity dependence whatsoever. The entire bracket
  therefore lands on the BEP numerator and is transmitted to the dominance
  share undiluted. There is no common-mode channel here at all, so the
  `epistemic-bracket-synthesis.md` cancellation rule ("a bracket cancels only
  if it is pure common-mode") predicts zero cancellation by construction.

**H1.** The conductivity bracket propagates to the annualised numbers at a
width comparable to, and not much smaller than, the conditional-curve bracket
at the stages the hazard samples, and it lands entirely on the BEP mechanism.

**H2.** Because the mechanism-dominance ordering is decided by a ratio with a
`k_aq`-free denominator, the ordering is robust only where the baseline margin
between BEP and overflow exceeds the bracket. Where the margin is small, the
ordering reverses.

### 1.3 What is fixed before measuring

**Sections and variant axis.** The four geotechnically characterised matrix
sections (KP 57.4, 58.8, 60.0, 62.0), `bep_source = prior`, λ_ac = 250 m
(ADR-0037 primary, n_eff = 1), surface variant = primary (corrected USACE
scour, ADR-0042 decision 9 amended), both scenarios (historical and +4K). The
110 segments carrying `bep_source = None` are conductivity-inert by
construction and are reported only as an invariance check.

**Why prior-against-prior is the honest comparison.** No Phase 2 posterior
exists for any conductivity arm, and building one is out of scope. `prior` is
already a documented campaign variant, so comparing arm-prior against
baseline-prior is apples-to-apples. It is also nearly costless at the section
that matters: verified from `rq4_annual.csv` before writing this, KP 62.0's
prior and posterior rows are **identical to full floating-point precision**
(system 1.006046005485643e-3, BEP share 0.8115239173288071, both scenarios),
because the 2016 update rejects 0.00 % there.

**Arms.** The four persisted ADR-0048 companion sweeps per section
(N = 1e5, written 2026-07-29/30), consumed read-only:

| arm | parameter | target mean | factor at KP 57.4 / 58.8 / 60.0 / 62.0 |
|---|---|---|---|
| `k_aq_field_geomean` | `k_aq` | 5.94e-5 m/s | ×0.0198 / ×0.0297 / ×0.0594 / ×0.0594 |
| `k_aq_field_toe` | `k_aq` | 5.15e-4 m/s | ×0.172 / ×0.258 / ×0.515 / ×0.515 |
| `k_aq_regional_upper` | `k_aq` | 1.0e-2 m/s | ×3.33 / ×5.0 / ×10 / ×10 |
| `gamma_bl_sub_lower` | `gamma_bl_sub` | 6.0 kN/m³ | ×0.870 (all) |

**Both `k_aq` ends are run, deliberately.** One arm can only report "held" or
"flipped", and neither is a robustness statement. `gamma_bl_sub_lower` is
included because it is free (the sweeps exist) and because it is the
**negative control**: the committed ADR-0048 record shows it inert to five
decimals at KP 62.0 conditionally, so if it moves an annualised number
materially, the machinery is wrong rather than the physics interesting.

**Nothing is re-swept.** No Phase 1 sweep, no Phase 2 replay, no workbook
streaming. The warm hazard cache under
`results/system_integration/hazard_cache/` is reused; it has no BEP or
conductivity dependence, and a scenario moves no `z_toe`, so every node's cache
datum still matches and nothing is rewritten.

### 1.4 Decision criteria

**The quantity under test** is the leading mechanism per section × scenario:
the mechanism with the larger annual contribution, equivalently
`share_bep > 0.5` since fluvial scour is exactly zero everywhere under the
corrected conversion.

* **ROBUST** at a section × scenario iff every one of the four arms preserves
  the baseline's leading mechanism.
* **CONTESTABLE** iff at least one arm changes the leading mechanism.
* **NOT DEFINED** iff an arm drives both mechanisms to exactly zero, in which
  case no share exists. This is reported as a fact about the section, never as
  "overflow leads" and never as 0.5.

**The margin, pre-computed from the published baseline so it cannot be tuned
afterwards.** Because the denominator is conductivity-free, the reversal
condition is exactly "BEP falls by more than `R`", where
`R = P_bep,baseline / P_overflow`:

| section | historical R | +4K R |
|---|---|---|
| KP 57.4 | ∞ (overflow exactly 0) | 10.4 |
| KP 58.8 | 43.0 | 17.5 |
| KP 60.0 | ∞ (overflow exactly 0) | 666 |
| KP 62.0 | **4.31** | **1.0013** |

These eight numbers are the pre-registered yardstick. An arm reverses the
ordering iff its BEP annual falls below `1/R` of baseline.

**Secondary quantities**, reported but not used to decide robustness: the
annual system probability, the per-mechanism decomposition, the +4K/historical
climate ratio, and the `AnnualizedResult.coverage` flags per arm.

### 1.5 Predictions

* **P1 (the briefed primary).** KP 62.0 is the only section whose **historical**
  ordering is contestable. Its margin is 4.31 against three margins that are
  either infinite or ≥ 43.
* **P2.** At KP 62.0 historical the low-conductivity `field_geomean` arm hands
  the lead to overflow.
* **P3.** At KP 62.0 +4K the ordering reverses under **both** downward arms —
  the baseline margin is 1.0013, a knife edge — and holds under
  `regional_upper`.
* **P4.** `regional_upper` reverses no ordering anywhere. It moves BEP upward
  only, and BEP already leads at all eight section × scenario cells.
* **P5.** KP 57.4 and KP 60.0 **cannot** reverse historically at any arm,
  because overflow is exactly zero there: the share is 1.000 unless BEP also
  reaches exactly zero, in which case the answer is NOT DEFINED, not a
  reversal.
* **P6 (climate ratio).** The +4K/historical system ratio **rises** under the
  downward arms and **falls** under `regional_upper`, because the downward arms
  suppress the historical number more than the +4K one: the +4K hazard samples
  higher on the fragility curve, where the synthesis §4(a) compression bites.
* **P7 (control).** `gamma_bl_sub_lower` changes no ordering and moves every
  annual system probability by less than the smallest `k_aq` arm's movement at
  the same cell, by at least an order of magnitude.

### 1.6 What would falsify this reading

* **F1.** `regional_upper` reverses an ordering. That would contradict the
  monotone one-directional mechanism ADR-0048 records (higher `k_aq` raises
  r_e and lowers H_c, both pushing P_f the same way) and would indict either
  the arms or this pipeline, not the physics.
* **F2.** A section whose overflow annual is exactly zero reports an ordering
  change. The composition would have to invent an overflow contribution;
  this is a bug signature, not a finding.
* **F3 (the falsifier for H1, and the one that would deflate this whole
  study).** If the annualised conductivity bracket is **narrower at every
  section than the ADR-0037 λ_ac bracket already reported** (×1.6 to ×3.4 in
  `phase3_report.md` §6.2), then annualisation compresses the conductivity knob
  below the smallest bracket the thesis already carries, and calling it "the
  largest declared unknown" would be true of the conditional curves and false
  of the annualised deliverable. That distinction would have to be stated
  wherever the bracket is quoted.
* **F4 (contamination).** Any arm whose conditioning grid differs from its
  baseline's, or whose `config_hash` does not round-trip, or whose sweep is not
  N = 1e5, invalidates the comparison at that section and is refused rather
  than reported.
* **F5 (the prediction most likely to fail, named in advance).** If P1 fails it
  fails at **KP 58.8 historical**, whose margin of 43.0 is the smallest finite
  one outside KP 62.0, while the conditional `field_geomean` ratio at that
  section is 0 at the shoulder and ×0.024 at the grid top — a conditional cut
  far larger than 43× over most of the sampled stage range. KP 57.4 +4K
  (margin 10.4) and KP 58.8 +4K (17.5) are the next most exposed.

### 1.7 Gates fixed in advance

* **GATE 1, non-negotiable.** Before any arm number is reported, the baseline
  prior curves are pushed through this study's own pipeline and the annualised
  results must reproduce `results/system_integration/phase3/rq4_annual.csv`
  **exactly** for every matrix / prior / 250 m / primary row. Mismatch aborts;
  it is never tolerated or tabulated. A pipeline that cannot reproduce the
  production table is not measuring the production quantity.
* **GATE 2.** Each arm's conditioning grid is asserted equal to its baseline's,
  and each arm sweep is asserted N = 1e5 with a round-tripping `config_hash`
  carrying exactly the expected `prior_mean_scenario` label (F4).
* **GATE 3.** The 110 segments with no BEP source are asserted **bit-identical**
  between baseline and every arm. A conductivity scenario cannot reach them,
  and if it appears to, the pipeline is wrong.
* **GATE 4.** The hazard cache file set is asserted unchanged across the run
  (no workbook was streamed, no cache entry rewritten).
* **GATE 5.** No production artifact is written. The study writes only under
  `results/sensitivity/conductivity_annualisation/`, its own evidence JSON, and
  its own figure.

### 1.8 Sections predicted to change

KP 62.0 under both scenarios; at most KP 58.8 historical (per F5). KP 57.4 and
KP 60.0 historical are predicted immovable in ordering for the structural
reason in P5.

---

## Part 2 — Outcome

**Headline, with its scope inside the sentence: under matrix d70 on the prior
side, the aquifer-conductivity bracket contests the mechanism-dominance
ordering at three of the four surveyed sections historically and at all four
under 4 K warming, and it is wider than every sensitivity bracket the thesis
currently reports. A bulk-d70 conductivity arm has never been run.**

### 2.1 Did the pre-registration hold?

| | statement | outcome |
|---|---|---|
| **P1** | KP 62.0 is the only section contestable historically | **FAILED** |
| P2 | the low arm hands KP 62.0's historical lead to overflow | HELD |
| P3 | KP 62.0 at +4K reverses under both downward arms, holds under the upward one | HELD |
| P4 | the upward arm reverses nothing anywhere | HELD |
| P5 | KP 57.4 and KP 60.0 cannot *reverse* historically | HELD |
| P6 | the climate ratio rises under downward arms, falls under the upward one | HELD |
| P7 | the unit-weight control is inert and changes no ordering | HELD |
| F1 | upward arm reverses something (would indict the arms) | did not fire |
| F3 | the annualised bracket is narrower than the length-effect bracket | did not fire |
| **F5** | if P1 fails, it fails at KP 58.8 historical | **FIRED** |

**P1 failed, and it failed exactly where Part 1 said it would.** The briefed
prediction rested on baseline dominance margins: KP 62.0's historical margin is
4.31 against 43.0 at KP 58.8 and infinity at the two sections whose overflow is
exactly zero. That reasoning was right about the *ordering* of exposure and
wrong about the *scale* of the bracket. The conductivity knob is large enough to
consume a 43-fold margin at KP 58.8, and at +4K it consumes KP 60.0's **666-fold**
margin as well. F5 named KP 58.8 historical in advance as the failure mode, and
that is precisely the cell that broke the prediction — the mechanism was
understood, its magnitude was underestimated.

**P5 held and is worth stating separately**, because it is the one place a naive
reading of the verdicts would be wrong. At KP 57.4 historical the lowest arm
does change the answer, but not by handing the lead to overflow: it drives
**both** mechanisms to exactly zero, so no share exists at all. Part 1 fixed
"NOT DEFINED" as a third category precisely so this could not be reported as
"overflow leads". The record classifies it `COLLAPSED`, the figure withholds it
from the dominance line, and a test pins both.

**One falsifier was worded too loosely, and I am recording that rather than
quietly rescoring it.** F2 said "a section whose overflow annual is exactly zero
reports an ordering change" would be a bug signature. KP 57.4 historical *does*
report an ordering change under that literal wording. The mechanism F2 was
actually testing — the composition inventing an overflow contribution — did not
occur: overflow stays exactly 0.0 there under every arm. F2 should have been
worded "reports overflow as the leading mechanism". It did not fire in substance.

### 2.2 Per section and scenario

Annual probabilities [1/yr], matrix d70, prior BEP, λ_ac = 250 m, primary
surface. `lead` is the mechanism carrying the larger annual contribution.
Fluvial scour is exactly zero in every cell (ADR-0042 decision 9, amended).

**KP 57.4** (design high water 39.21 m MSL)

| arm | historical system | piping | share | lead | +4K system | piping | share | lead |
|---|---|---|---|---|---|---|---|---|
| production | 7.55e-4 | 7.55e-4 | 1.000 | piping | 9.54e-3 | 9.50e-3 | 0.912 | piping |
| field geomean | **0** | 0 | — | **none** | 9.12e-4 | 8.67e-7 | 0.001 | **overflow** |
| field toe | 5.67e-6 | 5.67e-6 | 1.000 | piping | 1.33e-3 | 6.77e-4 | 0.426 | **overflow** |
| regional upper | 3.46e-3 | 3.46e-3 | 1.000 | piping | 2.51e-2 | 2.51e-2 | 0.965 | piping |
| unit-weight control | 7.58e-4 | 7.58e-4 | 1.000 | piping | 9.56e-3 | 9.52e-3 | 0.913 | piping |

**KP 58.8** (design high water 41.03 m MSL)

| arm | historical system | piping | share | lead | +4K system | piping | share | lead |
|---|---|---|---|---|---|---|---|---|
| production | 8.47e-3 | 8.39e-3 | 0.977 | piping | 4.46e-2 | 4.42e-2 | 0.946 | piping |
| field geomean | 1.96e-4 | 4.65e-7 | 0.002 | **overflow** | 2.55e-3 | 3.54e-5 | 0.014 | **overflow** |
| field toe | 1.05e-3 | 8.73e-4 | 0.817 | piping | 9.40e-3 | 7.81e-3 | 0.755 | piping |
| regional upper | 3.61e-2 | 3.61e-2 | 0.995 | piping | 1.24e-1 | 1.24e-1 | 0.980 | piping |
| unit-weight control | 8.50e-3 | 8.42e-3 | 0.977 | piping | 4.47e-2 | 4.43e-2 | 0.946 | piping |

**KP 60.0** (design high water 42.75 m MSL)

| arm | historical system | piping | share | lead | +4K system | piping | share | lead |
|---|---|---|---|---|---|---|---|---|
| production | 2.03e-3 | 2.03e-3 | 1.000 | piping | 1.53e-2 | 1.53e-2 | 0.999 | piping |
| field geomean | 5.17e-8 | 5.17e-8 | 1.000 | piping | 3.47e-5 | 1.19e-5 | 0.341 | **overflow** |
| field toe | 5.04e-4 | 5.04e-4 | 1.000 | piping | 5.40e-3 | 5.40e-3 | 0.996 | piping |
| regional upper | 2.30e-2 | 2.30e-2 | 1.000 | piping | 9.59e-2 | 9.59e-2 | 1.000 | piping |
| unit-weight control | 2.05e-3 | 2.05e-3 | 1.000 | piping | 1.55e-2 | 1.55e-2 | 0.999 | piping |

**KP 62.0, the governing section** (design high water 46.39 m MSL)

| arm | historical system | piping | share | lead | +4K system | piping | share | lead |
|---|---|---|---|---|---|---|---|---|
| production | 1.01e-3 | 8.58e-4 | 0.812 | piping | 1.28e-2 | 8.40e-3 | 0.500 | piping |
| field geomean | 1.99e-4 | 1.56e-8 | 0.000 | **overflow** | 8.39e-3 | 6.91e-6 | 0.001 | **overflow** |
| field toe | 3.78e-4 | 1.94e-4 | 0.493 | **overflow** | 9.42e-3 | 2.86e-3 | 0.254 | **overflow** |
| regional upper | 1.38e-2 | 1.38e-2 | 0.986 | piping | 6.94e-2 | 6.93e-2 | 0.892 | piping |
| unit-weight control | 1.01e-3 | 8.58e-4 | 0.812 | piping | 1.28e-2 | 8.41e-3 | 0.500 | piping |

**Bracket width and climate ratio**

| section | historical span | +4K span | length-effect yardstick (hist / +4K) | climate ratio: production, low, toe, upper |
|---|---|---|---|---|
| KP 57.4 | **unbounded** | 27.6 | 3.37 / 2.17 | 12.6 → n/d, 234, 7.25 |
| KP 58.8 | 185 | 48.6 | 2.53 / 2.07 | 5.27 → 13.1, 9.00, 3.43 |
| KP 60.0 | **4.4e5** | 2.8e3 | 3.37 / 2.65 | 7.58 → 671, 10.7, 4.18 |
| KP 62.0 | 69.1 | 8.27 | 3.29 / 1.93 | 12.7 → 42.1, 25.0, 5.04 |

`span` is the largest annual system probability any conductivity arm produces
divided by the smallest, production value included — the same multiplicative
footing `epistemic-bracket-synthesis.md` uses. **Unbounded** means an arm gives
exactly zero failures.

**P6 held in both directions at every cell where the ratio is defined**, 4 of 4
sections: the downward arms *raise* the climate ratio (KP 60.0 historical is
suppressed 39 000-fold while its +4K number falls only 442-fold, so the ratio
runs from 7.58 to 671) and the upward arm *lowers* it toward 3.4 to 7.3. **The
climate signal is not bracket-invariant either.** The mechanism is the one the
synthesis §4(a) records: the +4K hazard samples higher on the fragility curve,
where the conductivity spread has begun to compress, so a shift in conductivity
always moves the historical number further than the warmed one.

**P7, the negative control.** The unit-weight arm moves every annual system
probability by 0.009 % to 1.4 % and changes no ordering anywhere, against
conductivity movements spanning five orders of magnitude at the same cells. The
machinery is not manufacturing motion.

### 2.3 The direct answer to A2

**Is the mechanism-dominance ordering robust to the largest epistemic bracket in
the study? No, at seven of the eight section-and-climate cells.** Per section,
with the stage band that decides it (the contribution-weighted 10th to 90th
percentile of the ensemble peak stages that actually carry the annual number):

| section | historical | +4K | driving stage band, historical → +4K [m MSL] |
|---|---|---|---|
| KP 57.4 | **COLLAPSED** — the low arm leaves nothing loaded at all | **REVERSED** by both downward arms | 39.9 to 40.8 → 40.3 to 42.6 |
| KP 58.8 | **REVERSED** by the low arm | **REVERSED** by the low arm | 40.5 to 42.2 → 40.7 to 43.2 |
| KP 60.0 | **ROBUST** | **REVERSED** by the low arm | 41.8 to 43.0 → 42.0 to 43.9 |
| KP 62.0 | **REVERSED** by both downward arms | **REVERSED** by both downward arms | 47.5 to 48.7 → 47.8 to 50.5 |

**Where it is not robust, plainly.** The `field_geomean` arm — the geometric mean
of the six-member, two-contractor, two-decade field-permeability population —
changes the answer at **all eight** cells: it reverses seven and collapses the
eighth. The `field_toe` arm, a far milder shift (×0.17 to ×0.52), still reverses
three: KP 62.0 in both climates and KP 57.4 at +4K. Only the upward arm leaves
every ordering intact, and it does so trivially, by pushing piping further ahead
of a mechanism it already leads.

**KP 60.0 is the one robust cell, and it is robust for a reason that does not
generalise.** Its historical overflow is *exactly* zero, so piping leads by
construction as long as any piping failure survives; the low arm suppresses it
by a factor of 39 000 and it still leads, with an annual probability of 5.2e-8.
That is a statement about overflow's absence, not about piping's resilience. Under
+4K, where overflow becomes nonzero at 2.3e-5, even a 666-fold margin falls.

**Why annualisation does not average the bracket away** — the mechanism, read
from the driving bands rather than assumed. At every section the annual number
is carried by stages at or above the design high water, and at KP 62.0 the whole
band sits 1.1 to 2.3 m *above* it. That is the regime where the conditional
bracket is still wide: the synthesis §4(a) collapse toward unity needs the arm
to saturate, which happens far higher on these grids. The integral therefore
samples the wide part of the bracket, not the collapsed part. Compounding this,
the dominance ratio has a **conductivity-free denominator** — overflow and
fluvial scour are Uemura surface curves with no aquifer dependence — so, unlike
the Stage 6.6 static-versus-transient ratio, there is not even a partial
common-mode channel. H1 and H2 are both confirmed, and F3 did not fire: the
annualised conductivity span exceeds the published length-effect bracket at
**every** section and scenario, by factors of 4 to five orders of magnitude.

### 2.4 The comparison an examiner will make

Chapter 7 already reports that the **smaller** bracket, the bulk-versus-matrix
d70 interpretation, reverses the mechanism lead at two of four sections
historically and three of four under warming. That claim reproduces exactly from
`rq4_annual.csv` (KP 58.8 and KP 62.0 historically; KP 57.4, 58.8 and 62.0 at
+4K, identically on the prior and posterior sides). The conductivity bracket is
strictly worse on the same axis:

| bracket | sections whose lead it contests, historical | under +4K |
|---|---|---|
| bulk versus matrix d70 (reported) | 2 of 4 | 3 of 4 |
| **aquifer conductivity (this study)** | **3 of 4** | **4 of 4** |

Two differences make the comparison sharper than the counts alone:

1. **The d70 axis is two values; the conductivity axis is a two-sided bracket.**
   Bulk d70 is a single documented alternative interpretation. Conductivity has a
   low end that reverses the ordering and a high end that moves it the other way,
   so the honest statement is a range containing the production answer, not an
   alternative to it.
2. **The conductivity bracket subsumes the d70 result at every section it
   touches.** Every cell bulk d70 reverses, conductivity also reverses.

So the examiner's question — "if the smaller bracket already flips the answer,
what does the larger one do?" — now has a measured reply rather than a
concession: it flips more cells, in both climates, and it also moves the climate
ratio itself, which the d70 axis was never shown to do.

### 2.5 Coverage and clamping

**No annualised number reported here is a clamped bound.** Across the baseline
and all four arms at all four sections in both scenarios, the HKV-audit coverage
flags `lower_bound_clamp` and `below_grid_unresolved` are **False for every
system curve and every mechanism curve** — zero flagged cells. Neither a
low-conductivity arm pushing a curve below its grid bottom nor a
high-conductivity arm pushing peaks past a non-saturated grid top actually
occurs at these sections. Every figure in §2.2 is an estimate, not a bound. (The
only clamp warnings emitted during the run are the pre-existing fluvial-scour
ones at Tokachi KP 62.2 and Satsunai KP 15.2, which are surface-only segments
outside this study's four and carry `frac_peaks_above_grid` of 0.0004 against a
curve that is identically zero.)

**One genuine caveat the study surfaced, which is a property of the production
deliverable and not of the arms.** A coverage clamp is not the only way an
annualised number can rest on ground the thesis forbids plotting. At KP 62.0 the
conditioning grid runs to 56.5 m MSL, but ADR-0024 fixes the attainable maximum
at 50.5 m; the levels above it are hypothetical fit stabilisers. Under +4K, **7 of
5400 ensemble years (0.13 %) peak above 50.5 m**, and because the curve is near
saturation there they carry **11.8 % of the annual piping probability**. No
coverage flag fires, correctly, because no peak leaves the grid (the highest is
51.47 m against a grid top of 56.5 m). The historical figure is exactly 0.0, and
KP 57.4 is exactly 0.0 in both climates. This affects the published production
+4K number at KP 62.0 identically to every arm here, so it changes no comparison
in this note; it is recorded because "the clamp flags are clean" is not by itself
a statement that an annualised number rests only on attainable stages.

**Promoted 2026-08-10, and it turned out to falsify a claim rather than merely
extend one.** This caveat is now `docs/phase3_report.md` **caveat 8 of section
8**, the standing list every Phase 3 consumer is told to carry. Checking it
against ADR-0024, which created the hypothetical extension, showed that ADR's
Implementation item 5 asserting the added levels are *"harmless in the
fragility x hazard composition (the hazard carries zero weight there)"* is
measurably wrong on the +4K hazard side: **4 of the 7 exposed years peak above
51.0 m, the first added level**, so the extension is not weightless. **Decision:
ADR-0024 carries a dated back-pointer** (a note appended 2026-08-10) rather than
no pointer, because a reader arriving at that ADR would otherwise take the
parenthetical as licence to ignore the extension in any composition — the exact
opposite of the correct conclusion. Its **Decision is untouched and was asserted
byte-identical**, and Implementation item 5 is byte-identical apart from an
inserted pointer: the parenthetical itself is left standing **verbatim**, with a
bracketed `[Pointer added 2026-08-10: ...]` marker beside it sending the reader to
the dated note, in the ADR-0038 decision-4 style. A reader who stops at item 5
therefore cannot miss the correction, and nothing in that item was reworded. The
assertion was not wrong when written — it dates from 2026-07-03, ten days before
Phase 3 existed and 26 days before the ADR-0047 adoption raised KP 62.0's
fragility ×8.7 at design HWL.

### 2.6 Scope

Stated in every headline sentence above and repeated here because it is the
first thing a later reader will lose: **this result is matrix-d70 and prior-side
only.** No bulk-d70 conductivity arm has ever been run. No Phase 2 posterior
exists for any conductivity arm, so the comparison is arm-prior against
baseline-prior — exact at KP 62.0, where prior and posterior annual numbers are
identical to full floating-point precision because the 2016 update rejects
0.00 % there, and a documented campaign variant elsewhere (the 2016 evidence
moves the system number by about 12 % at KP 58.8 and less than 2 % at the other
three, `phase3_report.md` §6.2). Because the bracket spans one to five orders of
magnitude, a 12 % prior-versus-posterior difference cannot change any verdict
here, but the numbers are prior-side numbers and must be labelled as such.

### 2.7 Method, gates and decisions of record

**Nothing was re-swept.** The four arms per section are the persisted ADR-0048
companion sweeps (N = 1e5, written 2026-07-29/30), consumed read-only. Total
compute was under two minutes; the warm Phase 3 hazard cache was reused and
asserted unchanged.

**Gates, all passed.**

| gate | result |
|---|---|
| 1 — baseline reproduces `rq4_annual.csv` | **228 published rows, 20 fields each, string-identical** |
| 2 — arm provenance | grid equal to baseline, N = 1e5, config hash round-trips, expected scenario label, all 16 |
| 3 — segments with no BEP source | 880 segment-scenario cells bit-identical under every arm |
| 4 — hazard cache | file set and digests unchanged; no workbook streamed |
| 5 — production artifacts | nothing written outside this study's own outputs |

Gate 1 is the one that matters. The composition step is **imported** from
`scripts/phase3_campaign.py` rather than re-implemented, so the gate exercises
the production code path; a private duplicate could have drifted and still
"passed". A test forbids a second copy.

**Architecture decision: standalone companion, zero diff to
`phase3_campaign.py`.** The brief allowed either a `--bep-variant/--out-dir` pair
on the campaign or a standalone driver, preferring whichever leaves the campaign
smaller in diff. The standalone driver leaves it at exactly zero: the campaign's
no-argument call is byte-unchanged. Adding a variant axis would also have been
wrong on dependency grounds — the campaign would then reference gitignored
ADR-0048 arm outputs it deliberately does not produce.

**Campaign interaction, decided deliberately.**

* **Figure declared in `FIGURE_DRIVERS`: yes, and it had to be.** Gate G7 asserts
  every tracked publication figure is declared, so an undeclared figure fails the
  campaign. It is declared by **exact filename**, not a `conductivity_*` glob
  that could later claim a sibling and leave it un-redrawn. It carries a real
  redraw path (`--figures-only` re-renders from the committed record and writes no
  evidence file), so the figure stays unconditionally fresh rather than merely
  watched. **Cost:** the recorded manifest is now stale relative to the code by
  one figure entry. That is unavoidable — any new tracked figure has this cost —
  and the campaign was not re-run, per the brief.
* **Companions entry: no, and no exclusion entry either.** The G6 enumeration was
  run against the new driver and **does not flag it**: its regex looks for a
  literal `results/tokachi_kp<digit>` and this driver composes sweep paths by
  format string. There is therefore no `UNCLASSIFIED` to resolve, and
  `COMPANION_EXCLUSIONS` says in its own docstring that widening it reflexively is
  the wrong response. Adding an entry for a non-hit would be a key that is never
  read. **The substantive reason it should not be a campaign companion anyway:**
  it consumes the ADR-0048 arm sweeps, which the campaign does not produce because
  the epistemic knobs stay OFF (campaign decision 3); wiring it in would make a
  campaign gate depend on artifacts a fresh campaign never creates. **Cost of the
  choice:** this study's gate 1 is not re-checked by the campaign, so a future
  Phase 3 change could break the reproduction silently until someone re-runs this
  driver. The mitigation is that gate 1 duplicates what campaign gate G4 already
  asserts about `rq4_annual.csv`.
* **Finding, reported not fixed.** The same enumeration currently reports **three
  pre-existing `UNCLASSIFIED` hits** — `bayesian_reliability_updating/pipeline.py`,
  `scripts/epistemic_bracket_synthesis.py` and `scripts/hwl_bias_resolution.py`.
  The campaign's own comment calls that "the signal to investigate". None is
  related to this study and none is touched here.

**Deviation from the brief's specification, stated rather than silently
absorbed:** the requested `--n-jobs` flag is **not** implemented. This study
re-runs no sweep and contains no parallelisable work — the composition and
annualisation of 114 segments takes seconds against a warm cache — so the flag
would control nothing, which is the dead surface the 2026-07-31 audit removed
elsewhere. `--arms`, `--out` and `--out-dir` are implemented as specified, plus
`--no-figure` and `--figures-only`.

### 2.8 What the thesis must change

Landing instructions for a later `msc-thesis` session. **Nothing in that
repository is edited here** (conventions §8: no thesis prose in this repo). Every
number below is in `docs/decisions/conductivity-bracket-annualisation.json`.

1. **Chapter 7, lines 868 to 873** — the passage conceding that the conductivity
   bracket "was not tested at this level at all". Replace the concession with the
   result. It should now say that the bracket has been propagated through the
   annualisation at the four surveyed sections under matrix d70 on the prior
   side, that it contests the mechanism-dominance ordering at three of four
   sections historically and four of four under warming, that the field-population
   arm changes the answer at every one of the eight section-and-climate cells,
   and that the bracket is wider than the length-effect bracket everywhere. Cite
   the figure `conductivity_bracket_annual.png`.

2. **The `tab:limitations` register, conductivity row** — currently scoped "On
   conditional probabilities only". That scope is now wrong. It becomes: *on
   conditional probabilities, on annual system probabilities, on the
   mechanism-dominance ordering, and on the climate ratio* — with the residual
   limitation restated as the real one: **matrix d70 and prior side only; no
   bulk-d70 conductivity arm has been run.**

3. **Chapter 9, answers register, row 3** — currently records "the conductivity
   arms reaching no reported curve, share or ratio". That is no longer true and
   should be replaced by the measured statement: the arms now reach the reported
   annual probabilities, the dominance shares and the climate ratios, at all four
   surveyed sections in both climates. The surviving gap for that row is the
   bulk-d70 side and the posterior side.

4. **Chapter 7 §2, the dominance narrative at KP 62.0** — presently argues from
   the production value that piping leads historically (share 0.812) and that the
   two mechanisms are level at +4K (0.500/0.500). Keep that as the production
   reading and add the bracket: under the field-population arms overflow leads at
   KP 62.0 in **both** climates (share 0.000 and 0.493 historically, 0.001 and
   0.254 at +4K), while under the regional upper arm piping's lead strengthens to
   0.986 and 0.892. The 0.500/0.500 balance at +4K is a knife edge — the baseline
   margin is 1.0013 — and should not be presented as a finding that any
   conductivity value would reproduce.

5. **Wherever an absolute annual probability or a climate ratio is quoted for a
   surveyed section**, attach the bracket. ADR-0048's warning that absolute
   probabilities must never be quoted without the conductivity range attached now
   demonstrably extends to the annualised deliverable and to the climate ratio,
   which moves from 12.6 to as much as 234 at KP 57.4 and from 7.58 to 671 at
   KP 60.0 across the same bracket.

**Recommended follow-on, not done here and not blocking:** a bulk-d70
conductivity arm. It would require four new Phase 1 sweeps (bulk × the three
conductivity scenarios is twelve, or four for the field-geomean arm alone) and
would answer whether the two brackets compound or overlap. Until it exists,
every statement above carries the matrix-d70 scope.

*Executed 2026-08-10. See Part 3, which discharges the d70 half of §2.6's scope
and leaves the prior-side half standing.*

---

## Part 3 — the bulk-d70 replication

**Status:** §3.1 (pre-registration) written 2026-08-10 before any bulk arm sweep
was started and before any bulk arm number existed. §3.2 (outcome) appended after
execution; like Part 2 it evaluates the pre-registered rules against the
pre-registered inputs and re-tunes nothing.

**Driver:** the same `scripts/conductivity_annualisation_study.py`, with the d70
axis threaded through as `--d70` (matrix remains the default and its behaviour is
byte-identical).
**Evidence:** `docs/decisions/conductivity-bracket-annualisation-bulk.json`
**Figure:** `docs/figures/conductivity_bracket_both_d70.png`

**Why a dated Part 3 rather than a sibling note.** The scope sentence being
discharged is §2.6 of *this* note, and this note's own closing paragraph
registered exactly this run as the follow-on. Splitting would leave §2.6 pointing
at a recommendation that had already been executed elsewhere, and would force
every later reader to hold two documents to answer one question. The deliverable
here is moreover a *comparison across the two d70 readings*, not a second
standalone measurement, so it belongs beside the reading it is compared against.

### 3.1 Pre-registration

*Written and committed before the bulk arms existed. Nothing below was adjusted
after seeing a result; where a prediction failed, §3.2 says so and the text here
is left standing.*

#### 3.1.1 What this closes, and what it does not

§2.6 scopes every number in Part 2 to **matrix d70 and prior side**. This part
closes the **d70 half only**. The prior-side half stands: no Phase 2 posterior
exists for any conductivity arm under either d70 reading, and building one
remains out of scope.

The reason this is not a sensitivity run is that the matrix and bulk d70
interpretations are **co-primary deliverables** of the study, not a result and a
variant. Chapter 7 already reports that the bulk reading, propagated through the
annualisation, reverses the mechanism lead at two of four sections historically
and three of four under warming (Part 2 §2.4 reproduces that from
`rq4_annual.csv`). So the largest epistemic bracket in the project had been
measured on one co-primary reading and not the other, and the two brackets were
known to overlap in effect without being known to compound.

#### 3.1.2 The structural asymmetry, read from the published table before anything ran

This is the single most important fact fixed in advance, because it inverts the
study relative to Part 2. Under bulk d70 the **production lead is already
overflow at five of the eight section-and-climate cells**:

| section | scenario | production lead | `R = P_bep / P_overflow` | multiplier on piping needed to change the lead |
|---|---|---|---|---|
| KP 57.4 | historical | piping | ∞ (overflow exactly 0) | cannot flip; only COLLAPSED is reachable |
| KP 57.4 | +4K | **overflow** | 0.622 | ×1.61 **up** |
| KP 58.8 | historical | **overflow** | 0.0204 | ×49.0 **up** |
| KP 58.8 | +4K | **overflow** | 0.106 | ×9.43 **up** |
| KP 60.0 | historical | piping | ∞ (overflow exactly 0) | cannot flip; only COLLAPSED is reachable |
| KP 60.0 | +4K | piping | 69.7 | ×0.0143 **down** |
| KP 62.0 | historical | **overflow** | 8.26e-5 | ×1.21e4 **up** |
| KP 62.0 | +4K | **overflow** | 1.84e-3 | ×544 **up** |

These eight numbers are the pre-registered yardstick, computed from the published
production table exactly as Part 2 §1.4 computed its own, so they cannot be tuned
afterwards.

**The consequence, stated before measuring: under bulk the decisive arm is the
upward one.** The two downward arms can only push piping further behind at the
five cells where it is already behind; only `k_aq_regional_upper` can change a
lead there. That is the mirror image of Part 2, whose P4 recorded the upward arm
as reversing nothing anywhere. It also means the "cheap decisive single arm"
available under matrix — `field_geomean` — is **not** decisive under bulk.

#### 3.1.3 Scenario set and its cost

**All four arms, at all four sections.** Justification: (i) the upward arm is now
the decisive one, so a `field_geomean`-only run would answer nothing at five of
eight cells; (ii) a two-sided bracket is the whole point, and one arm can only
report "held" or "flipped"; (iii) `gamma_bl_sub_lower` is the negative control and
is worth more here than under matrix, because the bulk annual numbers are drawn
from lower on the fragility curve, which is exactly where Part 2's parent ADR
measured that control to be at its *largest* (+29 % to +50 % transient at the
lowest reachable level, decaying to unity by the shoulder).

Cost: 16 Phase 1 sweeps at N = 1e5. The persisted bulk production sweeps record
69 / 159 / 159 / 160 s per section, so four arms is about 37 minutes. The
propagation itself re-sweeps nothing and runs in seconds against the warm hazard
cache.

#### 3.1.4 What is fixed before measuring

Sections KP 57.4 / 58.8 / 60.0 / 62.0; `d70 = bulk`; `bep_source = prior`;
λ_ac = 250 m; surface variant = primary; both scenarios. Arms are the same four
ADR-0048 instantiations as Part 2, specified as absolute **target means**, so the
per-section factors differ from the matrix run only where the section's own bulk
prior mean differs — which it does not, since d70 and `k_aq` are independent
columns. Nothing is re-swept on the Phase 3 side; the warm hazard cache is reused
and asserted unchanged, and it is valid for both readings because the node
exposure datum is `z_toe`, identical across d70 at all four sections (38.3 / 38.5
/ 40.0 / 44.9 m MSL, verified before writing this).

#### 3.1.5 A clamping rule, fixed in advance

At **KP 57.4 and KP 58.8 the bulk BEP curve already carries
`bep_clamped_above_grid = True` in production**: its transient transition is not
bracketed (max raw P_f 0.378 and 0.152), so under ADR-0024 the raw-tail branch
holds its last value above the grid rather than extrapolating. The piping annual
numbers at those two sections are therefore **lower bounds**, in production and in
every arm alike.

The rule, fixed now so it cannot be chosen afterwards: **a reversal that depends
on a clamped piping number is reported as a bound, and a failure to reverse at a
clamped cell is weaker evidence than a reversal**, because the true piping
contribution can only be higher than the clamped one. Clamped cells are labelled
in the record, in the table and in the figure.

#### 3.1.6 Predictions, restating Part 2's under bulk

| | statement | prediction |
|---|---|---|
| **B1** | *(P1 analogue)* The contest is driven by the upward arm, not the downward ones | HOLDS |
| **B2** | *(P2 analogue)* `regional_upper` reverses KP 57.4 +4K (needs ×1.61) and KP 58.8 +4K (needs ×9.43) | HOLDS |
| **B3** | `regional_upper` does **not** reverse KP 62.0 in either climate (needs ×1.21e4 and ×544, against matrix multipliers of ×16.0 and ×8.25) | HOLDS |
| **B4** | *(P4 analogue)* "the upward arm reverses no ordering anywhere" | **FAILS to replicate** — predicted in advance |
| **B5** | *(P5 analogue)* KP 57.4 and KP 60.0 historically cannot REVERSE, overflow being exactly zero; KP 57.4 historical COLLAPSES under `field_geomean` | HOLDS |
| **B6** | `field_geomean` reverses KP 60.0 +4K (needs ÷69.7; matrix gave ÷1282); `field_toe` does not (matrix gave ÷2.84) | HOLDS |
| **B7** | *(P6 analogue)* the climate ratio rises under the downward arms and falls under the upward one | HOLDS |
| **B8** | *(P7 analogue)* the control changes no ordering, and moves every annual number by less than a few per cent — while still moving them *more* than the 0.009 % to 1.4 % it moved the matrix numbers | HOLDS |
| **B9** | *(F3 analogue)* the annualised conductivity span is **wider under bulk than under matrix** at every section and scenario, and wider than the length-effect yardstick everywhere | HOLDS |

The mechanism behind B9, stated so it is falsifiable rather than decorative: the
bulk reading cuts the piping curves, so the same hazard integral samples them
lower down, and Part 2 §2.3 established that the conductivity spread is widest
low on the curve and collapses only where an arm saturates.

#### 3.1.7 The new question: compound or overlap

Part 2 §2.4 established that under matrix the conductivity bracket **subsumes**
the d70 axis: every cell d70 flipped, conductivity flipped too. The open question
is what the two do *together*.

| | statement | prediction |
|---|---|---|
| **C1** | The two brackets do **not** simply compound. They act on the same piping numerator in **opposite directions**: the bulk reading suppresses piping, the upward conductivity arm restores it. Downward conductivity compounds with bulk; upward conductivity **offsets** it | HOLDS |
| **C2** | At least one cell whose lead bulk alone hands to overflow is **restored to piping** by `regional_upper` | HOLDS |
| **C3** | Subsumption is not symmetric: the matrix finding "conductivity subsumes d70" does not re-appear in the same form once the baseline lead has already changed | HOLDS |
| **C4** | Across the **union** of both readings and the full bracket, the only cells whose lead is invariant are KP 57.4 and KP 60.0 **historically**, and only because overflow is exactly zero there — which is a statement about overflow's absence, not about piping's resilience (the same reading Part 2 §2.3 gave KP 60.0) | HOLDS |

C4 is the one that carries the RQ3 consequence, and it is deliberately the
strongest claim here: it predicts that **no cell has a mechanism ordering that
survives the union of the two co-primary readings on its own merits**.

#### 3.1.8 What would falsify this reading

* **BF1.** Neither the upward arm nor the downward arms change any lead under
  bulk. The bracket would then be inert exactly where the curves sit lowest,
  contradicting the stage-dependence property, and would indict the pipeline
  rather than the physics.
* **BF2.** A cell whose overflow annual is exactly zero reports **overflow as the
  leading mechanism**. This is the corrected wording of Part 2's F2, which §2.1
  recorded as too loosely worded to be a clean falsifier; it is fixed here rather
  than re-scored.
* **BF3.** The annualised bulk conductivity span is narrower than the matrix span
  at every section. That refutes B9 and would mean the integral compresses the
  bracket more under the lower-fragility reading, which the stage-dependence
  mechanism forbids.
* **BF4 (contamination).** Any arm whose conditioning grid differs from its bulk
  baseline's, whose `config_hash` does not round-trip, which is not N = 1e5, or
  which does not carry the expected `prior_mean_scenario` label. Refused, not
  reported.
* **BF5 (the prediction most likely to fail, named in advance).** If B2 fails it
  fails at **KP 58.8 +4K**, which needs ×9.43 against a matrix multiplier of
  ×2.81 at the same cell — it rests entirely on bulk amplifying the arm by more
  than a factor of three. KP 57.4 +4K needs only ×1.61 and is far safer. The
  second most exposed prediction is **B3 at KP 62.0 +4K**, which needs the
  amplification to stay *below* ×66.

#### 3.1.9 Gates fixed in advance

* **GATE 1, non-negotiable.** The **bulk** baseline pass must reproduce
  `results/system_integration/phase3/rq4_annual.csv` exactly for every
  bulk / prior / 250 m / primary row, field for field, before any bulk arm number
  is reported. Mismatch aborts.
* **GATE 2.** Per arm: grid equal to its bulk baseline's, N = 1e5, round-tripping
  `config_hash`, expected scenario label.
* **GATE 3.** The segments with no BEP source are bit-identical between the bulk
  baseline and every bulk arm.
* **GATE 4.** The hazard cache file set and digests unchanged.
* **GATE 5.** No production artifact written.
* **GATE 6, new to this part.** **The matrix path is unchanged.** Re-running the
  study with its default arguments must reproduce the committed matrix evidence
  record field for field apart from its own timestamp and runtime stamps, and
  re-rendering the matrix figure must change no bytes. A d70 axis that perturbed
  the matrix answer would invalidate Part 2 rather than extend it.

### 3.2 Outcome

**Headline, with its scope inside the sentence: under bulk d70 on the prior side,
the aquifer-conductivity bracket contests the mechanism-dominance ordering at
seven of the eight section-and-climate cells, and it does so from the opposite
direction to the matrix reading. Combining the two co-primary grain-size readings
with the bracket leaves NO cell whose leading mechanism is invariant. The two
brackets do not compound: on the mechanism ordering they partly cancel, and on
the annual system probability the second one is capped by a conductivity-free
mechanism.**

#### 3.2.1 Did the pre-registration hold?

| | statement | outcome |
|---|---|---|
| **B1** | the contest is driven by the upward arm, not the downward ones | **HELD** |
| **B2** | the upward arm reverses KP 57.4 +4K and KP 58.8 +4K | **HELD** |
| **B3** | the upward arm does not reverse KP 62.0 in either climate | **FAILED** (historical) |
| **B4** | the matrix P4 does not replicate under bulk | **HELD** (i.e. P4 failed to replicate, as predicted) |
| **B5** | KP 57.4 and KP 60.0 cannot reverse historically; KP 57.4 collapses | HELD |
| **B6** | the lowest arm reverses KP 60.0 +4K, the milder downward arm does not | HELD |
| **B7** | the climate ratio rises under the downward arms, falls under the upward one | **FAILED** (KP 58.8) |
| **B8** | the control changes no ordering and moves every annual number under 2 % | HELD |
| **B9** | the annualised span is wider under bulk than under matrix | **FAILED** |
| **C1** | the two brackets act on the piping numerator in opposite directions | HELD |
| **C2** | the upward arm restores a lead the bulk reading hands to overflow | HELD |
| **C3** | conductivity changes the lead at every cell the grain-size reading flips | **FAILED** (4 of 5) |
| **C4** | the only invariant cells are those where overflow is exactly zero | held **vacuously**; the truth is stronger |
| BF1 | no arm changes any lead (would indict the pipeline) | did not fire |
| BF2 | a zero-overflow cell reports overflow as leading (bug signature) | did not fire |
| BF3 | the bulk span is narrower than the matrix span at every cell | did not fire **on the letter only** |
| **BF5** | if B2 fails it fails at KP 58.8 +4K | did not fire |

Four predictions failed and one held only vacuously. Each is reported below with
the mechanism, and **three of the failures share a single mechanism**, which is
the substantive result of this part.

**BF5 did not fire, and that is worth stating.** Part 1 named KP 58.8 +4K in
advance as the place B2 would break, because it needed a factor of 9.43 against a
matrix multiplier of 2.81. The arm delivered **×27.8** and the reversal held. The
amplification the pre-registration hoped for is real and larger than it dared
predict.

**B3 failed, and it failed by a hair at the least likely cell.** The upward arm
was predicted not to reverse KP 62.0 in either climate, because historically it
needed a piping multiplier of **×1.21e4**. It delivered **×1.434e4**, and the
piping share lands at **0.542**. That is a knife edge and is reported as one: the
cell reverses, but a 20 % smaller multiplier would leave it standing. At +4K the
same arm needed ×544, delivered ×273, and the cell does **not** reverse, which is
why KP 62.0 at +4K is the only ROBUST cell under bulk.

**C4 held vacuously, and the truth is stronger than the prediction.** C4 predicted
the invariant set would contain the two cells whose overflow is exactly zero. The
measured invariant set is **empty**: those two cells do not survive either,
because under bulk they COLLAPSE rather than hold. `all()` over an empty list is
true, so the record scores C4 as held; the honest reading is that the prediction
was too weak, not that it was confirmed.

**BF3 did not fire on the letter, and the substance largely occurred.** It was
worded "narrower at *every* cell". Two cells have an unbounded bulk span (an arm
gives exactly zero failures), which counts as wider by definition, so the
conjunction fails. At **all six cells where both spans are finite the bulk span is
narrower**, by factors of 4 to 33. The wording, not the physics, is what kept it
from firing. Recorded here rather than rescored, following Part 2's treatment of
its own loosely worded F2.

#### 3.2.2 Per section and scenario

Annual probabilities [1/yr], bulk d70, prior BEP, λ_ac = 250 m, primary surface.
Fluvial scour is exactly zero in every cell. `x piping` is the arm's piping annual
divided by the production value.

**KP 57.4** — production lead piping historically (overflow exactly 0), overflow at +4K

| arm | hist system | hist piping | hist lead | +4K system | +4K piping | x piping | +4K lead |
|---|---|---|---|---|---|---|---|
| production | 2.07e-6 | 2.07e-6 | piping | 1.22e-3 | 5.67e-4 | — | overflow |
| field geomean | **0** | 0 | **none** | 9.11e-4 | 0 | ×0 | overflow |
| field toe | **0** | 0 | **none** | 9.12e-4 | 3.37e-6 | ×0.0059 | overflow |
| regional upper | 1.26e-4 | 1.26e-4 | piping | 4.14e-3 | 3.98e-3 | **×7.02** | **piping** |
| unit-weight control | 2.07e-6 | 2.07e-6 | piping | 1.22e-3 | 5.67e-4 | ×1.00 | overflow |

**KP 58.8** — production lead overflow in both climates

| arm | hist system | hist piping | hist lead | +4K system | +4K piping | x piping | +4K lead |
|---|---|---|---|---|---|---|---|
| production | 1.99e-4 | 3.98e-6 | overflow | 2.71e-3 | 2.68e-4 | — | overflow |
| field geomean | 1.95e-4 | 0 | overflow | 2.53e-3 | 0 | ×0 | overflow |
| field toe | 1.95e-4 | 5.76e-10 | overflow | 2.53e-3 | 2.44e-6 | ×0.0091 | overflow |
| regional upper | 8.58e-4 | 6.84e-4 | **piping** | 8.93e-3 | 7.45e-3 | **×27.8** | **piping** |
| unit-weight control | 1.99e-4 | 3.98e-6 | overflow | 2.71e-3 | 2.68e-4 | ×1.00 | overflow |

**KP 60.0** — production lead piping in both climates

| arm | hist system | hist piping | hist lead | +4K system | +4K piping | x piping | +4K lead |
|---|---|---|---|---|---|---|---|
| production | 6.95e-5 | 6.95e-5 | piping | 1.62e-3 | 1.61e-3 | — | piping |
| field geomean | **0** | 0 | **none** | 2.31e-5 | 1.52e-8 | ×9.5e-6 | **overflow** |
| field toe | 5.38e-6 | 5.38e-6 | piping | 3.17e-4 | 2.98e-4 | ×0.185 | piping |
| regional upper | 7.33e-3 | 7.33e-3 | piping | 4.30e-2 | 4.30e-2 | ×26.8 | piping |
| unit-weight control | 6.95e-5 | 6.95e-5 | piping | 1.62e-3 | 1.61e-3 | ×1.00 | piping |

**KP 62.0, the governing section** — production lead overflow in both climates

| arm | hist system | hist piping | hist lead | +4K system | +4K piping | x piping | +4K lead |
|---|---|---|---|---|---|---|---|
| production | 1.99e-4 | 1.65e-8 | overflow | 8.39e-3 | 1.54e-5 | — | overflow |
| field geomean | 1.99e-4 | 0 | overflow | 8.39e-3 | 0 | ×0 | overflow |
| field toe | 1.99e-4 | 0 | overflow | 8.39e-3 | 1.01e-6 | ×0.066 | overflow |
| regional upper | 4.13e-4 | 2.36e-4 | **piping** | 9.69e-3 | 4.21e-3 | **×273** | overflow |
| unit-weight control | 1.99e-4 | 1.65e-8 | overflow | 8.39e-3 | 1.54e-5 | ×1.00 | overflow |

**B8, the negative control.** The unit-weight arm moves every annual system
probability by **0.0000 % to 0.025 %** and changes no ordering anywhere. That is
*quieter* than under matrix (0.009 % to 1.4 %), which Part 1 predicted the wrong
way round: it reasoned that bulk samples lower on the curve, where ADR-0048
measured that control at its largest conditionally. The conditional reasoning was
right and irrelevant, because at five of eight cells the system number is carried
by overflow, which the control cannot touch at all. Same mechanism as B7 and B9
below.

#### 3.2.3 The answer owed: ordering verdicts across both readings

| section | climate | matrix verdict | bulk verdict | contested from |
|---|---|---|---|---|
| KP 57.4 | historical | COLLAPSED | COLLAPSED | below, both |
| KP 57.4 | +4K | REVERSED | REVERSED | **below under matrix, above under bulk** |
| KP 58.8 | historical | REVERSED | REVERSED | **below under matrix, above under bulk** |
| KP 58.8 | +4K | REVERSED | REVERSED | **below under matrix, above under bulk** |
| KP 60.0 | historical | **ROBUST** | COLLAPSED | — / below |
| KP 60.0 | +4K | REVERSED | REVERSED | below, both |
| KP 62.0 | historical | REVERSED | REVERSED | **below under matrix, above under bulk** |
| KP 62.0 | +4K | REVERSED | **ROBUST** | below / — |

**No cell is ROBUST under both readings.** Six of eight are contested under both.
The two exceptions are each robust under exactly one reading and contested under
the other, in opposite senses: KP 60.0 historical is the matrix reading's one
robust cell and collapses to nothing under bulk, while KP 62.0 at +4K is the bulk
reading's one robust cell and reverses under matrix.

#### 3.2.4 Compound or overlap: the direct answer

**Neither, and the word that fits is *offset*.** Three measured facts, in order of
weight:

1. **On the ordering the two brackets act in opposite directions.** The bulk
   reading suppresses the piping contribution and hands the lead to overflow at
   five of eight cells. The upward conductivity arm then **restores piping's lead
   at four of those five**: KP 57.4 +4K, KP 58.8 in both climates, and KP 62.0
   historically. Under matrix the contest came entirely from the downward arms
   and the upward arm reversed nothing anywhere (Part 2, P4); under bulk it is the
   upward arm that does all the reversing and the downward arms that reverse only
   one cell between them. The same physical knob, moved the same way, changes the
   answer in opposite directions under the two readings, because it is being
   applied on opposite sides of the crossing.

2. **On the annual system probability they do not compound, because the second
   bracket is capped by a conductivity-free mechanism.** This is the mechanism
   behind three of the four failed predictions, and it is one mechanism, not
   three. Once the grain-size reading has demoted piping below overflow, the
   system probability is carried by the Uemura surface curves, which have no
   aquifer dependence at all. Every conductivity statistic about the *system* then
   collapses toward the overflow-only value:

   * **B9.** The bulk system span is **narrower** than the matrix span at all six
     cells where both are finite (4.54 against 27.6, 4.40 against 185, 3.53
     against 48.6, 1865 against 2762, 2.07 against 69.1, 1.16 against 8.27). Not
     because the bracket on the mechanism shrank, but because the mechanism it
     acts on no longer carries the number. The span on the **piping** contribution
     alone is unbounded at six of eight cells and ×2.8e6 at the seventh.
   * **B7.** At KP 58.8 the climate ratio *falls* under both downward arms
     (13.62 to 12.97) instead of rising. 12.97 is the overflow-only ratio
     (2.53e-3 / 1.95e-4 = 12.97) to three figures: the arms strip the small piping
     remainder and the ratio converges on overflow's own climate response. The
     same convergence leaves KP 62.0 unmoved at 42.11 under both downward arms.
   * **B8.** The control is quieter under bulk than under matrix for the same
     reason.

   The pre-registration's error was uniform: it reasoned about the shape of the
   *conditional piping curve*, and the recorded quantity is the *system*
   probability. Both are correct statements about different things, and the
   distinction is exactly what the union of the two brackets turns on.

3. **Subsumption is not symmetric (C3).** Under matrix, conductivity flipped every
   cell the grain-size axis flipped. Under bulk it flips **four of the five**. The
   exception is KP 62.0 at +4K, where the bulk reading has pushed piping 544-fold
   behind overflow and even a ×273 arm cannot close the gap. So "the larger
   bracket subsumes the smaller" is a property of the matrix baseline, not a
   general relation between the two.

**What this means for RQ3, which is the point of the exercise.** The
mechanism-dominance claim does not rest on either bracket alone; it rests on their
union, and in the union **no section-and-climate cell has an invariant leading
mechanism**. That is not the same as "the dominance finding collapses", and the
difference matters:

* The direction of each bracket is known and monotone. Lower conductivity and the
  bulk grain-size reading both suppress piping; higher conductivity restores it.
  Nothing here is a random spread around an unknown answer.
* **Production sits at neither end of either bracket.** ADR-0048 places the
  adopted conductivity at 55 % to 77 % of the log range spanned by the field
  population and the regional upper band, and both grain-size readings are carried
  as co-primary, with the matrix reading the conservative one. The reported
  ordering is the ordering at a mid-range input, not at a favourable extreme.
* The upper arm of the conductivity bracket **strengthens** piping's lead
  everywhere it is applied, under both readings. A reader who takes only the field
  arms away from this note has taken the comfortable half of a two-sided result.

#### 3.2.5 A caveat that is much larger under bulk, and is a property of the deliverable

Part 2 §2.5 recorded that at KP 62.0 under +4K, 7 of 5400 ensemble years (0.13 %)
peak above the ADR-0024 attainable maximum of 50.5 m MSL and carry **11.8 %** of
that section's annual piping probability, with no coverage flag firing because
nothing leaves the grid.

**Under the bulk reading the same seven years carry 81.2 %.** The bulk piping curve
at KP 62.0 is so low that almost all of its annual piping probability is drawn
from stages the section cannot reach. The consequence is specific and must travel
with the number: **KP 62.0's bulk +4K piping annual probability of 1.54e-5 is
four fifths hypothetical**, and the fact that this cell reads ROBUST is therefore
a statement about how far behind overflow the piping contribution has been pushed,
not a demonstration that its ordering is well founded. Historical is exactly 0.0,
and KP 57.4 is exactly 0.0 in both climates and both readings.

`docs/phase3_report.md` caveat 8 already states the operative rule (read the
coverage flags together with the section's attainable maximum, never the flags
alone). This part supplies the second, larger measurement of it.

#### 3.2.6 Clamping, and a qualification this part puts on Part 2

The ADR-0024 raw-tail branch holds a curve at its last raw value above the
conditioning grid rather than extrapolating, and flags the cell. Under bulk this
fires on the **production baseline** at KP 57.4 and KP 58.8 in both climates, and
on arms at KP 60.0. The piping annual probabilities there are **lower bounds**, in
production and in every arm alike; the figure tints those panels and the record
names the cells.

**The qualification on Part 2.** Running this part surfaced that the same flag
fires on **six matrix arm cells** as well: a low-conductivity arm drops the arm's
own maximum raw failure fraction below the ADR-0024 bracketing threshold, so the
arm switches to the raw-tail branch even where the production baseline is a fitted
lognormal. Part 2 §2.5 did not record this. Its claim there is still true as
written, because it is about the two `AnnualizedResult.coverage` flags, which
really are False everywhere; `bep_clamped_above_grid` is a different flag and was
not examined. The direction matters: clamping **understates** an arm's piping
contribution, and those are the arms that produce Part 2's reversals, so a
reversal declared on a clamped arm is easier to declare than it should be.

Quantified rather than left as a worry. Of the ten matrix arm-verdicts that change
a lead, four are at KP 62.0 and are **unclamped**, so the governing-section claim
is untouched. Of the six clamped ones, the margin by which the arm's piping annual
sits behind overflow is:

| cell | arm | piping is behind overflow by | at risk from the clamp? |
|---|---|---|---|
| KP 57.4 historical | field geomean | overflow is exactly 0 | no: the verdict is COLLAPSED, not a reversal |
| KP 57.4 +4K | field geomean | ×1051 | no |
| KP 57.4 +4K | field toe | **×1.35** | **yes, in attribution only** |
| KP 58.8 historical | field geomean | ×420 | no |
| KP 58.8 +4K | field geomean | ×71.5 | no |
| KP 60.0 +4K | field geomean | **×1.93** | **yes, and it is the only arm reversing this cell** |

So **one** Part 2 cell verdict is genuinely exposed: **KP 60.0 +4K**, whose
REVERSED verdict rests on a single clamped arm sitting a factor of 1.93 behind
overflow. KP 57.4 +4K is exposed only in *which* arms are credited, since the
field-geomean arm reverses it anyway at ×1051. Part 2's headline counts, three of
four sections historically and four of four under warming, are unchanged. The size
of the clamp's effect cannot be quoted, because quantifying it would mean
extrapolating a curve above its grid, which is precisely what ADR-0024 forbids;
the exposure is reported, not corrected. The matrix evidence record now carries
the clamped-cell list, and every matrix number in it was re-verified unchanged.

#### 3.2.7 Method and gates

**Sixteen new Phase 1 sweeps** (four sections × four arms, N = 1e5, bulk d70),
written to `results/sensitivity/adr0048_prior_means/` by
`scripts/prior_mean_scenario_companion.py` against the four persisted **bulk**
production sweeps consumed read-only. Their per-level record merges into
`docs/decisions/adr0048-prior-mean-companion.json` beside the matrix sections;
the merge was **verified non-destructive on a copy before it was run for real**,
and the four matrix sections are byte-identical to their committed form
afterwards. That driver also gained the `--out` flag the 2026-07-31 audit had
listed as missing, defaulting to the same tracked path so its no-argument call is
unchanged.

The propagation itself re-swept nothing and took 19 s against the warm cache.

| gate | result |
|---|---|
| 1 — the bulk baseline reproduces `rq4_annual.csv` | **228 published bulk / prior / 250 m / primary rows, 20 fields each, string-identical** |
| 2 — arm provenance | grid equal to baseline, N = 1e5, config hash round-trips, expected scenario label, **and `d70_interpretation` asserted from the arm's own config** rather than trusted from its filename, all 16 |
| 3 — segments with no BEP source | 880 segment-scenario cells bit-identical under every arm |
| 4 — hazard cache | 228 files, digests unchanged; no workbook streamed. The node exposure datum is pinned to the matrix curve, as the campaign pinned it when the cache was written, and the bulk curve's datum is asserted equal to it at all four sections |
| 5 — production artifacts | nothing written outside this study's own outputs |
| 6 — the matrix path is unchanged | **every matrix value reproduces exactly**, verified key by key against the committed record |

**GATE 6 was relaxed once, deliberately, and both departures are named.** As
pre-registered it demanded the matrix record reproduce "field for field apart from
its own timestamp and runtime stamps". It was relaxed to the production campaign's
own asymmetric metadata rule, under which an **additive** key is recorded and
passes while a **changed value** or a regression still fails. Diffed key by key
against the committed record, a fresh matrix run differs in exactly three places,
two of them beyond the timestamps:

* **One additive key**, the clamped-cell list of §3.2.6. The alternative was to
  emit it only under bulk, which would have left the matrix record silently
  omitting a real property of its own arms.
* **One changed string**, the scope sentence, which until this part read "no
  bulk-d70 conductivity arm has ever been run". That was true when written and
  false the moment these arms landed. A record may not carry a claim its own
  repository has overtaken, so the clause became a pointer to the companion
  record. A test now forbids either record claiming it again.

**Every numeric value in the matrix record is unchanged**, verified by a
key-by-key walk against its committed form, and the matrix figure re-renders
**byte-identical** (SHA-256 unchanged). No matrix conclusion moves.

#### 3.2.8 What the thesis must change

Landing instructions. **Nothing in `msc-thesis` is edited from this repository**
(conventions §8). Every number is in
`docs/decisions/conductivity-bracket-annualisation-bulk.json`.

1. **Every occurrence of the scope sentence "matrix d70 and prior side only"**
   narrows rather than disappears. The d70 half is discharged; the prior-side half
   stands, and it should now read that no Phase 2 posterior exists for any
   conductivity arm under **either** grain-size reading.
2. **The dominance narrative** gains the cross-reading verdict table of §3.2.3 and
   the statement that no cell's leading mechanism is invariant across the union of
   the two readings and the bracket, together with the two sentences that keep
   that from reading as "we do not know": the direction of each bracket is known
   and monotone, and production sits at neither end of either.
3. **The limitations register.** The conductivity row and the grain-size row are
   **no longer independent** and the register must say so: they act on the same
   piping contribution, in opposite directions on the ordering, and sub-additively
   on the annual system probability because a conductivity-free mechanism carries
   it once piping is demoted.
4. **The answers register and the sub-question 3 prose** record that the arms now
   reach the reported annual probabilities, shares and climate ratios under
   **both** co-primary readings, and that the surviving gap is the posterior side
   alone.
5. **The future-research item on bulk horizontal conductivity** is partly
   discharged: the bracket has been propagated to the deliverable under both
   readings. What remains is a measurement that would narrow it, not a
   propagation that would quantify it.
