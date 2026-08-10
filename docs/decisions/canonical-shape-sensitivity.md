# Canonical-shape sensitivity: measuring what the pinned d4PDF event is worth

**Status:** Part 1 pre-registered 2026-08-10 before any number existed. Part 2 to follow.
**Scope:** defence-brief item A1, "every conditional curve conditions on one canonical
ensemble event", which the brief calls the largest absence in the work. Discharges the
sensitivity Chapter 4's canonical-shape subsection promises and never delivers.
**Parents:** `canonical-shape-invariance.md` (the free half: what cannot move),
ADR-0020 (canonical event pinning), ADR-0023 (shape-invariant climate axis),
ADR-0040/0041 (Stage 6.6 ladder), ADR-0035/0036 (Phase 2 replay), ADR-0042 (Uemura
surface curves), ADR-0024 (tail deliverable), ADR-0047 (the L adoption, whose ratio
method this study reuses).
**Driver:** `scripts/canonical_shape_sensitivity_study.py`.
**Evidence:** `canonical-shape-sensitivity.json` beside this note.

---

## Part 1: pre-registration

Written and saved in full before the first arm was run. Part 2 evaluates these rules
against these inputs and records the outcome; it may not re-tune anything below. Where
Part 2 contradicts Part 1, Part 1 stands as written and the contradiction is the
finding.

### 1.1 The question, and why it is genuinely open

Every transient conditional probability in this thesis is computed by scaling one
pinned d4PDF member, `HPB_m064_1987`, to each conditioning level. The companion
invariance note settled, from source, *which* results that choice can reach: the
static branch cannot move at all, nor can six of the ten Stage 6.6 comparators, nor
the Phase 2 rejection fractions. What it could not settle without running something is
the **magnitude and the sign** of the transient response.

The approved alternate is pinned as `canonical_event_ids[1]` in all eight configs:
`HPB_m067_1978`, an isolated single peak, the largest HPB peak of the band, recorded
with a 32 h rise. Two channels act in opposite directions and the repository records
nothing that decides between them, which is what makes this a prediction rather than a
confirmation.

**Channel 1, the compound second episode.** `m064` carries a secondary peak at
stage-shape 0.777 and an inter-peak trough at 0.4962, both above the landside toe at
the informative anchors, so it presents one continuous above-toe window rather than
two episodes. Because `l` is monotonically non-decreasing, that second episode's
contribution to the final pipe length is non-negative: an alternate without it can
only lose erosion, moving every transient probability down.

**Channel 2, crest breadth.** The comparison is not "m064 with its second peak
deleted". `m067` is a different primary peak, and its one recorded comparable number,
a 32 h rise, is **longer** than m064's 23 h rising limb and its 18 h 10-to-90 % rise.
Failure requires the pipe to cross the barrier at `l_c`, which happens only at heads
close to the crest, so a broader crest buys erosion exactly where it is decisive.

### 1.2 The predicted direction, and the mechanism it rests on

**Prediction P1: the transient failure probability RISES under `HPB_m067_1978`.**
Channel 2 beats channel 1. The reasoning is an inequality on the model's own
equilibrium curve, not an intuition about hydrographs.

On the rising branch `l < l_c` the equilibrium head `H_eq(l)` increases linearly to
`H_c` at `l_c`, so a pipe under a receding load stalls at `l_eq(t) = l_c *
H_erosion(t) / H_c`, which is monotone increasing in the instantaneous head. A later
episode whose head is **lower** than the primary peak therefore has a **lower** stall
target and cannot advance a pipe that already reached its primary-peak stall point.
The second episode can only act on rows that had already crossed `l_c` and then
stalled on the descending branch, where `H_eq` falls from `H_c` to `0.9 * H_c`.

Write `e` for the peak excess above the toe, `c = 0.3 * D_bl` for the crack term and
`f` for the secondary peak's fraction of the primary excess. Restarting a row stalled
on the descending branch needs `f*e - c > 0.9 * H_c`, while being past the barrier at
all needs `H_c < e - c`. At the informative anchors `f = 0.581` (KP 58.8) and `0.607`
(KP 60.0), and `f*e - c > 0.9*(e - c)` requires `-(1 - f)*e > -0.1*c`, which is false
for every positive `e` and `c`. So **the second episode is structurally inert for
every row that is only marginally past the barrier**, which is precisely the band of
rows that decides a probability near the transition. It can act only where
`H_c < (f*e - c)/0.9`, a strictly smaller set whose members carry a large primary
overload and are therefore likely to have breached during the primary peak anyway.
Channel 1 is real but confined to a thin, rate-limited sliver. Channel 2 acts on the
whole marginal band.

**Prediction P2: `m067` holds the stage above the toe for LESS total time than `m064`,
and yet still raises the transient probability.** m064's measured 55 h at or above
half amplitude spans *both* peaks, because its inter-peak trough sits at 0.4962,
essentially on the 50 % threshold; its upper-quartile duration is bought entirely at
heads between half and three-quarters of the primary excess, where the barrier is not
in play. If P1 and P2 both hold, the finding is that **above-toe duration is the wrong
summary statistic for this model** and time near the crest is the right one. If P2
fails and m067 is simply the longer event on every measure, P1 is confirmed for a
duller reason and must be reported as such.

**Prediction P3: the peak-shortcut over-rejection factor moves AWAY from one.**
Its exposure is one-sided through the numerator, the prior transient curve read at the
observed 2016 peak; the denominator is the Phase 2 rejection fraction, which the
invariance note proves exactly invariant. P1 raises the numerator, so 2.75 (KP 58.8)
and 3.90 (KP 60.0) both increase. **This is the headline at risk and the reason the
study is pre-registered**: the thesis currently argues the factor would move *toward*
one under a shorter event, and P1 says the pinned alternate is not that event.

**Prediction P4: the design-level static-to-transient bias FALLS.** It has the
opposite one-sidedness, an invariant numerator over a conditional denominator, so the
same swap that raises the peak-shortcut factor lowers 26.9 at KP 62.0 and the
`B >= 148` bound at KP 57.4. P3 and P4 moving in opposite directions under one swap is
a construction result, not an empirical claim, and a Part 2 in which they move the
same way indicts the harness.

**Prediction P5: in the Stage 6.6 ladder, `temporal_net` FALLS in probability units
and the head-convention SHARE RISES.** The head-convention and initiation-gate
components are exactly invariant in probability units; the shares are not, because
their denominator ends at a transient comparator. A rise in `C4` shrinks the total gap
without touching the numerator.

**Prediction P6: the Phase 3 BEP annual probability and the BEP dominance share both
RISE**, the latter only if the surface curves are held on the same member as the BEP
curves. Overflow is a duration-above-crest mechanism conditioned on the *same* pinned
event, so a BEP-only swap would confound shape with mechanism in exactly the quantity
RQ3 reports.

**Prediction P7: the effect is largest at mid-grid and compresses at both ends.** Deep
in the tail almost nothing fails under either shape, and above the transition
everything fails under both, so the shape can only act where the outcome is
rate-limited. The same stage-dependence the conductivity bracket shows.

### 1.3 What would falsify this reading

* **F1.** The transient probability FALLS at the transition midpoint in three or more
  of the four matrix strata. Then channel 1 dominates, the inequality in 1.2 is not
  the binding mechanism, and P3 to P6 all invert.
* **F2.** The sign differs between sections. Then no single mechanism governs, the
  result is section-conditional, and every number must be reported per section with
  no basin-wide direction claimed.
* **F3.** The largest resolved `|delta P_f|` over the whole grid is smaller than the
  Clopper-Pearson half-width at the same level. Then the shape effect is below the
  study's own statistical resolution, and A1 is answered as "measured and immaterial"
  rather than as a direction.
* **F4.** The peak-shortcut factor moves by more than a factor of two at either
  informative stratum. Then a thesis *claim* rather than a thesis *number* is at
  stake, and this is escalated to the owner before any prose is written.
* **F5.** A quantity the invariance note proves invariant moves by one bit. Then the
  harness is wrong and the run is void; nothing is reported.

### 1.4 Gates, asserted rather than reported

Every one of these is a consequence the invariance note derived from source. They are
assertions in the driver, not findings in Part 2.

* **Gate 1.** Each baseline arm reproduces its persisted production sweep bit-for-bit
  on both raw probability vectors. A sensitivity against a drifted baseline is refused.
  Eight strata.
* **Gate 2.** `P_f_static_raw` is EXACTLY equal between the two shape arms at every
  level of every stratum. The static comparator consumes the scalar conditioning level
  verbatim and never touches the loading record. One bit of movement voids the run.
* **Gate 3.** `C0`, `C0b`, `C1`, `C2`, `C3a` and `C3b` are bit-identical between the
  two shape arms, and so is the entire static Shapley lattice. Only `C4a` to `C4d`
  consume a hydrograph.
* **Gate 4.** The Phase 3 hazard cache is unchanged by this study. The hazard side
  streams every ensemble member and does not know which one is canonical.

### 1.5 Method, fixed in advance

* **Selection is in memory only.** `run.py` selects `canonical_event_ids[0]`, that
  field is inside the config hash, and the drift guard pins the committed ordered
  list, so reordering a committed config is forbidden three ways. The arm loads the
  YAML, replaces the one key, revalidates through `Config`, and runs with
  `persist=False` into a study-local directory. The committed configs are never
  written; a test asserts it.
* **Both arms share one prior.** The theta draw and the independent seepage-length
  draw are seed-driven and shape-independent, so the comparison is exactly paired and
  every difference is physical.
* **Resolution rule.** A difference is reported as resolved only where a paired
  bootstrap interval over realization resamples, B = 2000, shared row indices across
  both arms, excludes zero. Unresolved differences are reported as unresolved, never
  as findings.
* **Anchors, named in advance and never called "the shoulder".** Per stratum: the
  design-level anchor, meaning the grid level nearest the section design high water;
  the transition midpoint, meaning the grid level whose baseline transient probability
  is nearest 0.5; the observed 2016 peak, which is the peak-shortcut anchor; and the
  grid top. The maximum absolute difference over the whole grid is reported with the
  level it occurs at.
* **Shape statistics are definition-matched.** The alternate's rise, half-amplitude
  duration and above-toe hours are measured with the same function that produced
  m064's published 23 h, 18 h, 10 h and 55 h, so the two are commensurable. The
  recorded 32 h is of unstated definition and is treated as provenance, not as a
  measurement.
* **Coverage.** Phase 1 at all eight strata. The ladder at the two ADR-0040 sections.
  Phase 3 with the surface curves regenerated on the alternate member, so the
  dominance ratio is not confounded; if that regeneration proves materially more
  expensive than declared, every dominance number is scoped to the piping side in the
  same sentence and the reason is stated.
* **Nothing production is touched.** No config, no CSV, no persisted sweep, no
  `rq4_annual.csv`, no Phase 2 posterior, no ADR decision, no default. The alternate
  is an approved provenance entry being exercised, not a new input.

### 1.6 Published numbers predicted to move

| Number | Where it is published | Predicted |
|---|---|---|
| Peak-shortcut factor 2.75 (KP 58.8), 3.90 (KP 60.0) | `phase2_report.md` section 11.1; `phase2-peak-shortcut.json`; thesis Ch 6, Ch 8, Ch 9, Summary | Rises (P3) |
| Design-level bias 26.9 [21.6, 35.3] at KP 62.0 | `adr0040-hwl-bias-resolution.md`; thesis Ch 6 | Falls (P4) |
| Bound `B >= 148` at KP 57.4 | same | Falls |
| `temporal_net` share 0.58 to 0.81 at the shoulder levels | `stage6_6_report.md` | Falls (P5) |
| Head-convention share 0.75 to 0.97 at design level | same | Rises, while the component in probability units does not move at all (P5) |
| RQ3 piping dominance share, RQ4 annual system probability | `phase3_report.md`; thesis Ch 6 | Rise (P6) |

Predicted NOT to move, by construction rather than by measurement: every static
number, the Phase 2 rejection fractions and the nesting, the head-convention and
initiation-gate components in probability units, and the static Shapley lattice.

---

## Part 2: outcome

Executed 2026-08-10 against the rules of Part 1, unchanged. **The headline prediction
P1 is REFUTED**, and it is refuted because a number Part 1 leaned on turned out not to
be a measurement. That correction is section 2.1 and it drives everything after it.

### 2.1 The premise that failed: the alternate is the SHORTER event, on every measure

Part 1's channel 2 rested on one recorded figure, a "32 h rise" for the alternate,
which `scripts/generate_configs.py` carried as provenance and which the companion
invariance note quoted as the single directly comparable number available. **It does
not reproduce.** Measured with the same function that produced the production member's
published timescales, and cross-checked against four onset thresholds in both the
discharge and the stage domain:

| Definition-matched statistic | Compound event (production) | Single-peak alternate |
|---|---|---|
| Rising limb, 10 per cent of amplitude to peak | 23.0 h | **16.0 h** |
| 10 to 90 per cent rise | 18.0 h | **14.0 h** |
| Plateau, within 10 per cent of the peak | 10.0 h | **5.0 h** |
| Width at half amplitude | 55.0 h | **21.0 h** |
| Significant peaks | 2 | **1** |
| Hours at or above shape 0.25 / 0.50 / 0.75 / 0.90 / 0.95 | 80 / 55 / 20 / 10 / 7 | **44 / 21 / 10 / 5 / 4** |

Discharge-domain rise from onset thresholds of 2, 5, 10 and 50 per cent of amplitude
gives 23 / 19 / 15 / 8 h for the production member against **16 / 14 / 13 / 4 h** for
the alternate. No threshold, in either domain, yields 32 h. The figure is withdrawn and
the comment in `generate_configs.py` corrected in place; the configs regenerate
byte-identical, since only a comment changed.

**The reconciliation Part 1 anticipated is confirmed and then some.** The production
member's upper-quartile duration is bought by its second episode, whose trough sits at
0.4962, essentially on the half-amplitude threshold, so the whole double-peak complex
counts as one 55 h window. But the alternate is not merely shorter *there*: it is
shorter at every shape fraction, including 0.90 and 0.95, where the barrier actually
binds. Part 1's channel 2 therefore does not exist, and both channels point the same
way.

### 2.2 Phase 1: unanimous, resolved, and large

All eight strata, both arms, N = 100,000. **Gate 1 passed at all eight**, each baseline
arm bit-identical to its persisted production sweep on both raw probability vectors, and
**Gate 2 passed at all eight**, the raw static probabilities exactly equal between the
arms at every level. The committed configs are byte-identical afterwards.

**The transient failure probability FALLS at every stratum, and the direction is
unanimous: 8 resolved negative, 0 positive.**

| Stratum | Transition midpoint | Production | Alternate | Ratio | Max abs difference |
|---|---|---|---|---|---|
| KP 57.4 matrix | 41.00 | 0.4631 | 0.3025 | 0.653 | 0.176 at 41.50 |
| KP 57.4 bulk | 43.25 | 0.3775 | 0.2851 | 0.755 | 0.092 at 43.25 |
| KP 58.8 matrix | 41.50 | 0.4915 | 0.3226 | 0.656 | 0.181 at 41.75 |
| KP 58.8 bulk | 45.00 | 0.1523 | 0.1113 | 0.731 | 0.041 at 45.00 |
| KP 60.0 matrix | 43.25 | 0.5289 | 0.3065 | 0.579 | 0.236 at 43.75 |
| KP 60.0 bulk | 45.00 | 0.4880 | 0.3164 | 0.648 | 0.190 at 45.50 |
| KP 62.0 matrix | 49.50 | 0.4727 | 0.2883 | 0.610 | 0.208 at 50.25 |
| KP 62.0 bulk | 56.50 | 0.4265 | 0.3135 | 0.735 | 0.113 at 56.50 |

Stages are m MSL. Between 12 and 29 of each stratum's 23 to 38 levels are resolved by
the paired bootstrap.

**F3 does not fire, decisively.** At the transition midpoint the shape difference is 13
to 72 times the Clopper-Pearson half-width on the production point, so this is not a
number sitting inside its own statistical noise. **F2 does not fire either**: the sign
is the same at all eight strata, so nothing here is section-conditional.

**P7 is confirmed.** The effect compresses where the outcome stops being rate-limited:
at the matrix grid tops the ratio is 0.93 to 0.96 against 0.58 to 0.66 at the midpoint,
and at the design-level anchors of the two damped sections both arms are identically
zero. The shape can only act where time, rather than head, decides the outcome.

**The design-level bias at the two drained sections, where it is fully resolved.**
The static branch is invariant by gate 2, so the bias at any level follows from the
record without further computation. At the drained sections the design level sits near
the middle of the transient curve, so both arms carry tens of thousands of failing rows
and the ratio is a measurement rather than a count of a handful:

| Section | Design level | Static | Transient | Failing rows | Bias |
|---|---|---|---|---|---|
| KP 58.8 | 41.00 | 0.72206 | 0.26273 to 0.14828 | 26,273 / 14,828 | **2.75 to 4.87** |
| KP 60.0 | 42.75 | 0.91650 | 0.31427 to 0.15210 | 31,427 / 15,210 | **2.92 to 6.03** |

The production column reproduces the published 2.75 and 2.92 exactly. The same
quantity at the two sections whose design level sits deep in the tail is **not**
resolvable at this sample size: KP 62.0 carries 15 failing rows at its nearest grid
level and 4 at its design level, and KP 57.4 carries none under either loading. So the
bias rises under the shorter event wherever it can be measured at all, by a factor of
about 1.8 to 2.1 at the drained sections and about 3 at the two ladder sections
(section 2.4), and nowhere does it fall.

### 2.3 The peak-only shortcut: the headline moves, the claim survives

Phase 2 was not re-run. The denominator is the replay rejection fraction, which the
invariance note proves shape-invariant because the replay drives the observed 2016
record; it is carried over from the committed slice verbatim and asserted equal. This
study's own baseline reproduces the published peak-only numerator **exactly** at every
stratum before any alternate number is reported.

| Stratum | Rejected rows | Factor, production event | Factor, single-peak event |
|---|---|---|---|
| KP 58.8 matrix | 5,673 | 2.749 | **1.448** |
| KP 60.0 matrix | 3,363 | 3.899 | **1.568** |
| KP 57.4 matrix | 65 | 7.459 | 3.072 |
| KP 60.0 bulk | 23 | 6.121 | 2.200 |
| four remaining strata | 0 | not defined | not defined |

The two small-number strata stay in the record and out of the headline band, and the
four strata that reject nothing under either reading are **not defined**, never 1.0 and
never agreement.

**Headline: 2.75 to 3.90 becomes 1.45 to 1.57.** The direction of the claim survives
under both events, and the peak-only reading over-rejects under both. What does not
survive is the number as an unconditioned property of the method: at KP 60.0 the factor
falls by a factor of 2.49, which fired falsifier F4 and was escalated before any prose
was written. The disposition adopted is to **quote it as a measured two-event bracket,
with the conditioning event named in the same sentence**.

That is the physically honest reading rather than a retreat. The factor measures how
much above-toe and near-crest exposure the canonical event carries beyond its own peak,
so an event carrying less exposure must produce a smaller factor. **The size of the
over-rejection is a property of the conditioning event as much as of the method; the
sign is a property of the method alone.**

### 2.4 The comparator ladder: the components hold, the shares and the bias do not

The production ladder was not re-run. `results/stage6_6/` already holds it, verified
bit-identical to the persisted production sweep by its own driver, so the alternate arm
is compared against the published record itself rather than against a second derivation
of it, and the persisted matrices are first checked to reproduce the persisted analysis
table. Nothing was written to `results/stage6_6/` and no tracked figure was touched: the
Stage 6.6 driver has no shape axis and no output directory, and it correctly refuses a
mismatched config rather than skipping. That refusal was respected rather than bypassed;
the ladder kernel was driven directly instead.

**Gate 3 passed at both sections.** `C0`, `C0b`, `C1`, `C2`, `C3a` and `C3b` are
bit-identical between the arms, and so is every expression in the static Shapley
lattice. Exactly one telescoping step in each ladder is shape-exposed, as constructed.
Euler barrier-jump counts are **0 in both arms at both sections, at N = 100,000**.

The auxiliary deltas reproduce the predicted partition without a single exception:

| Auxiliary quantity | Exactly invariant? | Largest change |
|---|---|---|
| Resistance-scale toggle at the static comparator | **yes** | 0 |
| Resistance-scale toggle at the sustained-peak limit | **yes** | 0 |
| Resistance-scale toggle at the transient comparator | no | 0.123 / 0.156 |
| Equilibrium-anchor conservatism, both ladders | no | 0.0133 / 0.0138 |
| Both ladder totals | no | 0.208 / 0.221 |

**The production ladder, component against share.** The head-convention and
initiation-gate components are exactly invariant in probability units at every level;
their shares are not, because the denominator is the total gap and the total gap ends at
a transient comparator. Both are quoted below, because they are different quantities.

| Section, level | Head-convention component | Its share | Time component | Its share |
|---|---|---|---|---|
| KP 62.0, 46.75 | 0.00873, **unchanged** | 0.549 to 0.520 | 0.00717 to 0.00805 | 0.451 to 0.480 |
| KP 62.0, 49.50 | 0.01981, **unchanged** | 0.0446 to 0.0315 | 0.4239 to 0.6083 | 0.955 to 0.969 |
| KP 57.4, 39.75 | 0.07418, **unchanged** | 0.810 to 0.774 | 0.01598 to 0.02023 | 0.175 to 0.211 |
| KP 57.4, 41.00 | 0.09597, **unchanged** | 0.241 to 0.172 | 0.3018 to 0.4623 | 0.759 to 0.828 |

Stages are m MSL. The physics ladder's components are equally invariant, but its
*shares* are not quotable near the design level: its total gap passes through zero there
because the resistance-scale component is large and negative, so the fractions diverge.
The production ladder is the one whose endpoint is the reported gap and is the one
reported here.

**The static-to-transient bias rises, and roughly triples.** It has the opposite
one-sidedness from the peak-only factor, an invariant numerator over a conditional
denominator, so the same swap that pushes the factor toward one pushes the bias up.

| Section, level | Failing rows, production / alternate | Bias |
|---|---|---|
| KP 62.0, 46.75 | 130 / 42 | **13.2 to 41.0** |
| KP 57.4, 39.75 | 731 / 306 | **13.5 to 32.3** |
| KP 62.0, 49.50 | 47,270 / 28,830 | 1.94 to 3.18 |
| KP 57.4, 41.00 | 46,306 / 30,254 | 1.86 to 2.85 |

**Neither section's design-level anchor is quotable at this sample size, and that is a
property of the deliverable rather than of this study.** At KP 62.0's design high water
the production arm carries 4 failing rows and the alternate 3, so the apparent 44.8 to
59.7 is counting noise of the kind that already had to be corrected once when a
higher-sample run turned an unresolved 44.7 into a resolved 26.9. At KP 57.4 both arms
are identically zero and no ratio exists at all. The two levels above are therefore
reported instead, chosen by the lowest level at which **both** arms carry at least 30
failing rows, which is the same resolution criterion the design-level resolution work
pre-registered. Resolving the shape effect at the design anchor itself would need the
alternate arm re-run at ten times the sample size, which was not attempted.

The consequence for the reported bias is direct: **it is conditional on the canonical
event as well as on the seepage length and on the aquifer conductivity**, and of those
three the conductivity remains the largest.

### 2.5 Phase 3: one dominance ordering changes

Both mechanism families were re-conditioned on the alternate member, so the dominance
share compares like with like. The overflow model is a duration-above-crest mechanism
driven by the same pinned event, and swapping only the piping side would have moved the
numerator of the share while leaving the rest of the denominator on the old shape. The
regeneration took 25.5 minutes of wall time against the 5 to 10 declared, but it ran
concurrently with sixteen production-scale sweeps on the same machine, so the excess is
contention and not cost. The committed contract set is asserted unchanged.

The baseline pass reproduces the published annual table over all **228** rows of the
matrix, prior-side, 250 m, primary slice, and **Gate 4 holds**: the hazard cache is
untouched, as it must be, because the hazard side streams every ensemble member and
does not know which one is canonical.

| Section and climate | Annual system probability | Piping share |
|---|---|---|
| KP 57.4 historical | 7.55e-4 to 4.39e-4 | 1.000 to 1.000 |
| KP 57.4 warmed | 9.54e-3 to 6.71e-3 | 0.912 to 0.886 |
| KP 58.8 historical | 8.47e-3 to 5.58e-3 | 0.977 to 0.968 |
| KP 58.8 warmed | 4.46e-2 to 3.17e-2 | 0.946 to 0.929 |
| KP 60.0 historical | 2.03e-3 to 9.95e-4 | 1.000 to 1.000 |
| KP 60.0 warmed | 1.53e-2 to 8.46e-3 | 0.999 to 0.998 |
| KP 62.0 historical | 1.01e-3 to 5.82e-4 | 0.812 to 0.743 |
| KP 62.0 warmed | 1.28e-2 to 1.03e-2 | **0.500 to 0.380** |

**One ordering changes, at exactly the cell that was already balanced.** KP 62.0 under
the warmed climate stands at 0.500 on the production event, the knife edge the seepage
length adoption left it on; under the single-peak event piping falls to 0.380 and
overflow leads. Nothing else changes side: piping still leads at three of four sections
under the warmed climate and at all four historically.

**The climate ratios rise rather than fall**, 12.64 to 15.28, 5.27 to 5.69, 7.58 to 8.50
and 12.70 to 17.75 at KP 57.4, 58.8, 60.0 and 62.0. The historical number falls
proportionally more than the warmed one, because the warmed hazard reaches stages where
the conditional curves are closer to saturation and the shape has less room to act. The
same stage-dependence as P7, seen through the integral. These are prior-side ratios and
match the conductivity companion's own baseline.

### 2.6 Every prediction, disposed of

| | Prediction | Verdict |
|---|---|---|
| P1 | Transient probability rises | **REFUTED.** It falls, unanimously at 8 of 8 strata. The premise behind it was the withdrawn 32 h rise. |
| P2 | Alternate holds the stage above the toe for less time, and yet still raises the probability | **Split. The duration half is CONFIRMED and strengthened**, shorter on every measure and not merely in total; **the conjunction is REFUTED** with P1. |
| P3 | Peak-only factor moves away from one | **REFUTED in direction.** It moves toward one, 2.75 to 3.90 becoming 1.45 to 1.57. |
| P4 | Design-level bias falls | **REFUTED in direction.** See section 2.4. |
| P5 | Temporal component falls, head-convention share rises | **REFUTED in direction.** See section 2.4. |
| P6 | Piping annual probability and dominance share rise | **REFUTED in direction.** Both fall, and one ordering changes. |
| P7 | The effect is largest at mid-grid and compresses at both ends | **CONFIRMED.** |

**What was predicted structurally, rather than in direction, all held.** The exposure of
the peak-only factor is one-sided through its numerator; the design-level bias has the
opposite one-sidedness; and the two therefore move in **opposite** directions under one
and the same swap, which they do. Gates 1 to 4 all passed, so F5 never came into play.

**The lesson worth keeping is about the pre-registration, not about hydrology.** Part 1
reasoned correctly from a recorded number that was wrong, and reached the wrong
direction by a defensible argument. Because the direction was committed in advance, the
error surfaced as a refutation rather than as a rationalisation; had the prediction been
written after the arms ran, the same mechanism section would have been written with its
sign reversed and would have read just as convincingly.

## What the thesis must change

Every item below is a measurement replacing a conditional, not a caveat being added.

1. **The canonical-event exposure passage, Chapter 6.** The direction is no longer
   undetermined. State the measurement: the approved alternate is the shorter event on
   every definition-matched statistic, and under it the peak-only factor falls to 1.45
   to 1.57 while every conditional transient probability falls by 24 to 42 per cent at
   the transition.
2. **Every quotation of the peak-only factor**, in Chapter 6, Chapter 8, Chapter 9 and
   the Summary, becomes the two-event bracket **1.45 to 3.90**, with the conditioning
   event named in the same sentence, per the adopted disposition.
3. **The limitations register row** for the canonical event: the Quantified cell becomes
   yes, the Affected column narrows to transient conditionals and what descends from
   them, and the Resolution column carries the measured bracket and the invariant set.
4. **Chapter 4's canonical-hydrograph subsection**, which promises this sensitivity,
   states the invariance property positively and points to the measured bracket.
5. **Chapter 6's gap components**: the component in probability units and the share are
   different quantities and must be quoted as such.
6. **The dominance narrative** must record that the one warmed-climate cell standing at
   0.500 changes side under the alternate event.
7. **The durable half**, which belongs wherever the sensitivity is discussed: the static
   branch, the survival-update rejection fractions and their nesting, and five of the
   six peak-referenced comparators are invariant **by construction**, not by
   measurement.
