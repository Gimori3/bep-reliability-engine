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

**Scope, stated first because every number below inherits it: this result is
matrix-d70 and prior-side only. A bulk-d70 conductivity arm has never been run,
and no Phase 2 posterior exists for any conductivity arm.** Every quotation of
any figure in this note must carry that sentence.

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
probability by 0.02 % to 1.4 % and changes no ordering anywhere, against
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
