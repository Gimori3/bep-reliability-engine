# The drained configuration at KP 58.8 and KP 60.0: how wide the bracket is, and what survives it

Companion note to ADR-0050. Pre-registered 2026-08-21 (commit `ae8e07d`,
before the first arm ran); measured and closed 2026-08-22.

Evidence records:

* `adr0050-drained-configuration-bracket.json` (Phase 1, 24 full-N sweeps),
* `adr0050-drained-bracket-annualisation-matrix-posterior.json`,
* `adr0050-drained-bracket-annualisation-bulk-posterior.json` (Phase 3),
* arm posteriors under gitignored
  `results/sensitivity/adr0050_drained_bracket/phase2/`.

Drivers: `scripts/drained_configuration_bracket.py`,
`scripts/drained_bracket_posterior_replay.py`,
`scripts/drained_bracket_annualisation.py`. Tests:
`tests/test_toe_gradient_relief.py` (26),
`tests/test_phase2_verification_threading.py` (5).

---

## 1. What this closes

KP 58.8 and KP 60.0 were fitted with a side berm plus a landside toe drain
between 1999 and 2003. The engine represents no drain, so every probability at
those two sections has been an as-if-undrained statement. That caveat appears in
six places in the thesis and carried no number anywhere, which made it the most
exposed interpretive claim in the work: the two sections it qualifies are the top
two entries of the prioritisation ranking that closes Chapter 9.

The thesis itself named the route, in Section 8.9.4: Japanese guidance names the
physical quantity each countermeasure acts upon, every one maps onto a quantity
already in the model, and a bracketing sensitivity perturbing those quantities in
the indicated directions is the most direct route to a defensible statement about
the remediated configuration. This is that sensitivity.

**It is a bracket on a configuration. It is not a drain model and not a design
evaluation, and the as-if-undrained number remains the deliverable.**

---

## 2. The mapping, and exactly how much of it is grounded

PWRI (2014) Table 7.1.1, printed p. 33, for 盤ぶくれ・パイピング specifically.
Read from `docs/references/tokachi_river_basin/syousasekkei_point1407.pdf` for
this note, not only from the repository's transcription of it
(`docs/tokachi_bep_inputs_provenance.md` §6.3).

| Recorded work | PWRI-stated effect | Engine quantity | Magnitude |
|---|---|---|---|
| 断面拡大工法 section enlargement (the berm) | ① 浸透路長の延長（動水勾配の低下）lengthen the seepage path, lowering the gradient | `geometry.L` | **measured** |
| ドレーン工法 landside toe drain | ① 裏のり尻部の動水勾配の低減 reduce the hydraulic gradient at the landside toe | `i_exit` in the M5 heave limit state | **not grounded** |

**The berm magnitude is measured.** ADR-0047 read the 2025 GSI DEM5A surface at
42.0 m (KP 58.8, 31 of 31 clean stations, along-levee CoV 0.073) and 43.0 m
(KP 60.0, 31 of 31, CoV 0.184) against the modelled 1998 values 35.0 and 34.8 m.
ADR-0047 held both, on the explicit ground that adopting the longer path while
the engine models no toe drain "is not an improvement" because it imports only
the anti-conservative half of the works. **This study is the configuration in
which that objection lapses**, because both halves move together. The held
bracket is spent here and nowhere else; the production deliverable still runs on
the 1998 lengths.

**The drain magnitude is not grounded, and none was invented.** PWRI gives a
design rule at printed p. 42: the drain *width* is sized so the average hydraulic
gradient stays below 0.3. That criterion governs the drain body. The guidance
states no equivalence between it and the foundation blanket exit gradient, and
provenance §7.3 records that the basin's toe-drain programme has three distinct
documented rationales of which only one is seepage, concluding that *a `drained`
label identifies a physical feature, not a design intent* and warning that "a
seismically motivated drain need not have been sized against the seepage exit
gradient". The secured dataset holds no drain-capacity data. **The relief
fraction is therefore a swept axis and its response curve is the deliverable.**
The 0.3 figure is recorded in the evidence JSON as a sourced observation and is
pinned by test to never become an arm.

The distinction matters more than it might look. The response curve turns out to
be strongly non-linear in the relief fraction (§4), so any single invented drain
performance would have landed on one arbitrary point of it and been reported as
the answer.

---

## 3. The channel reading, made before the numbers

| channel | where | branches |
|---|---|---|
| `Δh_blanket` → `i_exit` → the uplift/heave gate | `initiation.z_uplift`, `z_heave` | transient only |

That is the whole list for the relief arm. Since ADR-0028 the r_e-attenuated
blanket overpressure reaches the gate and nothing else: it is not in `H_c`, not
in the raw erosion head, and not in the static comparator. The prediction was
that the static failure matrix must be **bit-identical** under any relief.

**Measured: exactly 0.0 displacement at every level, every arm, all four cases.**
The driver refuses to report if a single static cell moves relative to the berm
arm, at which the seepage length is identical and the relief is the only
difference. Nothing moved. This is the ADR-0028 separation confirmed a third
time, after ADR-0048's `gamma_bl_sub` arm and ADR-0049's `l_c` arm.

The berm arm is deliberately **not** gate-only and is marked so in the record: L
enters `H_c` through the Sellmeijer scale and damping factors and enters
`Z = L − l_e` directly, so it moves both branches. Conflating the two would make
the static-invariance result meaningless.

---

## 4. The conditional bracket

Matrix reading, N = 10⁵, Δt = 225 s, historical, at each section's design water
level. All four baseline gates reproduced their persisted production sweep
**bit-identically on both whole failure matrices**.

| configuration | KP 58.8 (41.03 m) | KP 60.0 (42.75 m) |
|---|---|---|
| as-if-undrained (the deliverable) | 0.2627 | 0.3143 |
| berm at its measured 2025 length | 0.1084 | 0.1111 |
| berm + 20 % gradient relief | 0.1048 | 0.1055 |
| berm + 40 % | 0.0754 | 0.0731 |
| berm + 60 % | 0.0064 | 0.0069 |
| berm + 80 % | 0 | 0 |

Two sections of different geometry agree closely at every rung, which is what a
physical axis looks like and a numerical one usually does not.

**The relief shifts the curve right; it does not scale it down.** The lowest
stage at which the mechanism initiates at all:

| configuration | KP 58.8 | KP 60.0 |
|---|---|---|
| as-if-undrained | 39.75 | 41.25 |
| berm only | 39.75 | 41.50 |
| berm + 40 % | 40.50 | 42.25 |
| berm + 80 % | **42.00** | **43.50** |

Under the strongest arm the mechanism does not initiate anywhere at or below
0.97 m (KP 58.8) and 0.75 m (KP 60.0) **above** the design water level. That is
prediction P4 confirmed, and it has a clean cause: `i_exit` is proportional to
`h − z_toe` while the Terzaghi critical gradient is very nearly deterministic
(CoV(γ'_bl) = 0.056), so a fixed relief fraction buys progressively less as the
stage rises.

**Under the bulk gradation reading the bracket has almost nothing to say at
KP 58.8**, because the design level already sits below the reachable range there
(as-if-undrained transient P_f is 0 at the design level). Any conditional
statement from this bracket is matrix-conditional and must be quoted as such.

---

## 5. Prediction P5 was refuted, and the refutation is the point

P5 predicted the gate arm would outweigh the berm arm, on the reasoning that the
gate is a necessary condition for any erosion whereas L only lengthens and slows
the traverse. **There is no single verdict.** At KP 58.8's design level:

* berm alone: ×2.42 reduction,
* the first 20 % of relief on top of it: ×1.03, essentially nothing,
* 60 %: ×41,
* 80 %: the mechanism is gone.

At weak relief the measured berm dominates completely; at strong relief the gate
dominates completely. The crossover is sharp and sits between 40 % and 60 %.
Reported as a refutation rather than smoothed away, because it is the strongest
argument in this note for having swept the axis instead of choosing a value.

---

## 6. The survival update, and a number Chapters 6, 8 and 9 were missing

Those three chapters each record that the 2016 evidence is evaluated on the
undrained foundation while the survival was produced by a drained structure, that
the posterior is therefore tighter than the observation licenses, and that the
reported shifts are an upper bound. None attaches a number. Replaying the arms
through the ordinary Phase 2 entry point, settings gated equal to production, is
the configuration in which that mismatch is absent.

Prior rejected by the 2016 survival (matrix):

| configuration | KP 58.8 | KP 60.0 |
|---|---|---|
| as-if-undrained (production) | 5.673 % | 3.363 % |
| berm only, measured | 1.551 % | 0.555 % |
| berm + 20 % | 1.329 % | 0.442 % |
| berm + 40 % | 0.611 % | 0.165 % |
| berm + 60 % | 0.013 % | 0.002 % |
| berm + 80 % | 0.000 % | 0.000 % |

On the **measured berm geometry alone**, requiring no assumption about the drain
at all, the same evidence rejects 3.7 times less at KP 58.8 and 6.1 times less at
KP 60.0. Under strong relief the update becomes vacuous, which is the physically
correct reading: a structure the model says was never close to failing is barely
constrained by its survival.

**The marginal transient rejection stays exactly 0.000 in all 24 arm replays**,
so the nesting result Chapter 6 calls structural survives the entire bracket.

---

## 7. The annual numbers, the shares, the climate ratios and the ranking

Matrix, posterior, λ_ac = 250 m, primary surface set: the configuration every
RQ3 and RQ4 headline is quoted at. Gate 1 reproduced all 228 published
`rq4_annual.csv` rows field for field; gate 2 confirmed all 1120 untouched
segment-and-scenario cells unmoved in every arm.

Annual system failure probability:

| configuration | KP 58.8 hist | KP 58.8 +4 K | KP 60.0 hist | KP 60.0 +4 K |
|---|---|---|---|---|
| as-if-undrained | 7.42e-3 | 4.09e-2 | 1.80e-3 | 1.42e-2 |
| berm only, measured | 4.25e-3 | 2.67e-2 | 6.40e-4 | 6.51e-3 |
| berm + 40 % | 1.71e-3 | 1.46e-2 | 7.45e-5 | 1.94e-3 |
| berm + 80 % | 1.97e-4 † | 2.80e-3 † | 0 † | 2.98e-5 † |

† The strongest arm's transient transition is no longer bracketed, so its
deliverable form flips to the raw tail (ADR-0024) and the curve holds its last
value above the grid. **Those four numbers are lower bounds, not estimates.**

**Three further results.**

*The mechanism ordering is bracket-dependent.* At KP 58.8 the BEP share falls
from 0.974 to 0.955 on the berm arm and to 0.009 at the strongest, where
**overflow leads instead**. Prediction P7 confirmed: "BEP dominates three of four
sections" is itself as-if-undrained-conditional at two of those three.

*Crediting the drainage raises the climate ratio.* KP 58.8 goes from 5.51 to 6.29
(berm) to 14.22; KP 60.0 from 7.87 to 10.18 to 26.01. The protected configuration
sits lower on its own fragility curve, where the curve is steeper, so the same
warming shift buys proportionally more. This is not an artefact: it says the
warming sensitivity reported for these two sections is *understated* by the
as-if-undrained treatment, which runs opposite to the direction the caveat is
usually read in.

*The ranking.* This is the object Chapter 9 closes on.

| configuration | historical order | +4 K order |
|---|---|---|
| as-if-undrained | 58.8 > 60.0 > 62.0 > 57.4 | 58.8 > 60.0 > 62.0 > 57.4 |
| berm only, measured | **58.8 > 62.0 > 57.4 > 60.0** | **58.8 > 62.0 > 57.4 > 60.0** |
| berm + 20/40/60 % | 58.8 > 62.0 > 57.4 > 60.0 | 58.8 > 62.0 > 57.4 > 60.0 |
| berm + 80 % | 62.0 > 57.4 > 58.8 > 60.0 | 62.0 > 57.4 > 58.8 > 60.0 |

Two statements survive this, and they point in opposite directions:

1. **KP 58.8 keeps the top of the ranking across the whole bracket except its
   strongest arm**, in both climates. Its lead is robust to everything short of a
   drain that removes the mechanism.
2. **KP 60.0 leaves second place for last under every arm**, in both climates,
   **including the one that credits only the measured berm and assumes nothing
   about the drain.** Its second place is an artefact of the as-if-undrained
   treatment, and this is the one ranking change the bracket establishes without
   any ungrounded input at all.

---

## 8. Two things that had to be fixed, both found by gates rather than by reading

**(a) The pre-registered P2 fired, and was a discretisation artifact.** Exact
one-sidedness is the right claim about the continuous problem and the wrong one
about a forward-Euler solution of it. One row in 10⁵ at KP 58.8 bulk (row 22 790,
43.25 m, 2.2 m above design) failed at relief 0.80 having survived the berm arm.
At Δt = 225 s the relieved arm returns `Z_transient = 0.00000` exactly, the
signature of one step traversing the whole remaining length; at 112.5 s and
56.25 s the inversion is gone and the two arms agree to five decimals. The row
sits at C_e = 0.314 and k_aq = 6.6e-3, deep in the two tails ADR-0030 names.

There is a mechanism, and it is specific to this axis: **relief delays the gate,
so a relieved realization meets its first active timestep at a higher driving
head and takes a larger first step.** A gradient-relief axis is a more sensitive
probe of the ADR-0030 discretisation limit than the production configuration is.
Consistently, the artifact count grows with relief strength (1, 5, 6, 17 rows at
the four rungs) and occurs only at KP 58.8 bulk, where the transient probability
is near zero anyway.

The gate was made **stronger, not looser**: every violation is re-integrated at
112.5 s and 56.25 s and the driver refuses if a single one survives. That tests
the continuous-time claim rather than its discrete approximation, and it does not
care how many artifacts there are, only whether any is real. 29 violations, 29
verified artifacts, 0 survivors. The pre-registered text stands in ADR-0050 with
a dated amendment beside it.

At Phase 3 the same artifacts reappear as annualised inversions of +1.2e-08 and
+1.9e-08 against 2.57e-03. Demanding that an integral remove a discretisation
artifact is not a test anyone can pass, so gate 3 bounds the inversion by
`n_artifact / N`, which is the largest annual increase those rows can produce and
is **derived rather than chosen**: each artifact row raises the conditional
probability by exactly `1/N` where it fires, annualisation is a weighted mean with
weights at most one, and the series composition is monotone in each mechanism.
Anything larger, or any inversion at all where Phase 1 recorded none, still
refuses.

**(b) A latent Phase 2 defect, not mine, affecting three ADRs.**
`fragility_update.verify_posterior_fragility_by_reevaluation` re-runs M8 over the
accepted rows and asserts the flags match the retained matrices. It forwarded the
geometry, the Sellmeijer exponents and the foreland treatment, but **none of the
three optional M8 keywords**: the ADR-0045 model-factor draws, the ADR-0049
critical-length factor and the ADR-0050 relief. It therefore re-evaluated a
different model from the one that wrote the matrices and reported the parent run
as unverifiable.

The signature was diagnostic: transient flag mismatches scaling with relief
strength (2 481 at 0.80 up to 1 008 624 at 0.20) with the static mismatch exactly
0, which is a transient-only keyword going unforwarded. Production never tripped
it because all three knobs default to absent, which is exactly why it survived
this long. Fixed for all three; `tests/test_phase2_verification_threading.py`
pins it and was verified to fail on three of its four arms without the fix.

---

## 9. What this licenses, and what it does not

**Licensed.** A range for the protected configuration at KP 58.8 and KP 60.0, on
the conditional curves, on the survival update, on the annual system
probabilities, on the mechanism shares, on the climate ratios and on the
prioritisation ranking. The statement that KP 60.0's second place does not
survive the measured berm geometry alone, which rests on lidar and on the
guidance mapping and on nothing else.

**Not licensed.**

* Any claim about *where in the bracket the truth sits*. The relief fraction is
  swept precisely because no recorded material fixes it. The response curve is
  strongly non-linear across the swept range (§5), so an interior point is not a
  best estimate.
* Any reading of the strongest arm's annual numbers as estimates. They are
  lower bounds by ADR-0024 (§7).
* Any conditional statement under the bulk gradation reading at KP 58.8, where
  the design level is below the reachable range (§4).
* Any transfer to KP 57.4, whose recorded work is a berm alone, or to KP 62.0,
  which has none. The bracket is deliberately confined to the two `drained`
  sections and Phase 3 gate 2 enforces that the other 112 segments do not move.
* Any statement that the drains *do* perform at some level. Provenance §7.3
  stands: a `drained` label identifies a physical feature, not a design intent.

**Unchanged.** No production default, no CSV cell, no committed config, no
persisted production sweep, and no headline of record. The eight production
config hashes are byte-identical, verified against all eight committed YAMLs and
their persisted sidecars.
