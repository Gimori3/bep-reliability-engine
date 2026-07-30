# Stage 6.6: Static-Transient Bias Quantification and Gap Decomposition

Date: 2026-07-17
Status: Complete. Design: ADR-0040 (comparator ladder), ADR-0041 (equilibrium
end-factor override). Code: `bep_reliability_engine/gap_decomposition.py`,
driver `scripts/stage6_6_gap_decomposition.py`, tests
`tests/test_gap_decomposition.py`. Evidence: `results/stage6_6/` (HDF5
comparator matrices with JSON sidecars, analysis JSONs, duration-ladder JSONs,
figures; regenerable in full via the driver). Committed copies of the
number-bearing evidence follow the repository convention:
`docs/decisions/adr0040-stage6-6-*.json` (analysis, duration ladders,
summary with the verification statuses) and `docs/figures/stage6_6_*.png`.
Every number below traces to those files.

## 1. Scope and headline

This stage quantifies the total bias between the static Sellmeijer (2011)
comparator, representing conventional practice, and the transient Pol (2024)
progression model, and decomposes it into named components on the governing
section KP62.0 and the contrast section KP57.4 (matrix d70 interpretation,
N = 100 000 per section, the production 225 s integration grid, the canonical
d4PDF loading shape).

Headline result, per event at the design flood level (HWL):

- KP62.0 (HWL 46.39 m MSL): conventional static P_f = 2.1e-4
  (95 percent Clopper-Pearson interval 1.3e-4 to 3.2e-4) against a production
  transient P_f = 1.0e-5 (2.5e-7 to 5.6e-5): the static criterion
  overestimates the per-event failure probability by a factor of about 21.
  [**Superseded — see section 9 (authoritative).** This figure belongs to the
  withdrawn L = 47.0 m geometry and rests on 1 failing row. Under the adopted
  L = 40.0 m and N = 1e6 the design-HWL bias is **26.9 (95 % CI 21.6 to 35.3)**,
  statistically resolved on 63 failing rows.]
- KP57.4 (HWL 39.21 m MSL): conventional static P_f = 1.18e-3
  (9.8e-4 to 1.4e-3) against a transient P_f of exactly zero failures in
  100 000 realizations (upper bound 3.7e-5): an overestimation factor of at
  least 32 at 95 percent confidence.
  [**Superseded — see section 9 (authoritative).** At N = 1e6 the same level
  carries 2 failing transient rows, tightening the bound to **B ≥ 148**. The
  factor is still not statistically resolved there; the resolved figure to quote
  at this section is **42.7 (95 % CI 39.4 to 46.6) at 39.50 m MSL**.]

The bias decays toward parity as the conditioning level rises: the total
static-to-transient ratio falls from 15 at 47.0 m to 1.9 at 50.5 m (KP62.0)
[**superseded — under the adopted L = 40.0 m the same cell pair reads 10.5 at
47.0 m and 1.4 at 50.5 m; see section 8**]
and from 13.5 at 39.75 m to 1.04 at 43.25 m (KP57.4). At design-relevant
levels conventional practice is an order of magnitude conservative for these
sections; at extreme overload levels the two criteria converge because almost
every realization that exceeds the critical head also has time to breach.

Attribution, in one sentence per section: at KP62.0 the production gap is
carried by the temporal mechanism (about 76 percent at 48.0 m) with the crack
head convention carrying the rest and the initiation gate contributing nothing;
at KP57.4 the head convention carries more (42 percent at 40.5 m, and the
entirety of the small gap at HWL) because the thicker blanket (D_bl mean
0.8 m against 0.45 m) makes the 0.3 D_bl crack term bite harder, while the
initiation gate again contributes almost nothing to the production gap.

## 2. Head-datum verification (the mandatory gate)

Verified against the verbatim text of Pol SIE 2024 (extracted from the
project copy of the paper), before any new code was written:

- Eq. (5) drives dl/dt with the overload H(t) minus H_eq(l).
- Eq. (6) defines H = h minus h_e minus 0.3 D_bl, with h the outer water
  level and h_e the polder level at the exit point. The crack term is
  subtracted once, on the load side of the balance.
- Eq. (8) defines the uplift head as u_it minus h_e with no crack term, and
  Eq. (10) gives u_it = h_e + r_e (h minus h_e).
- Eq. (11) anchors H_eq(l) at (0, 0), (l_c, H_c), (L, 0.9 H_c); H_eq and H
  are head differences on the same h_e datum.

The repository implements exactly this: `progression.py` computes
H_erosion = (h(t) minus z_toe) minus 0.3 D_bl on the raw outer level with
z_toe identified with h_e (ADR-0007 datum note, ADR-0027 raw-head form),
compares it against the Eq. (11) curve anchored at the M6 H_c (a pure head
difference, no datum of its own), and keeps the gate heads unreduced and
r_e-attenuated per Eqs. (8) to (10). The crack term appears exactly once, at
the correct point in the balance; H_erosion and H_eq share the h_e = z_toe
datum. The pre-existing numerical pins (`tests/test_progression.py`, datum
block with a deliberately nonzero z_toe = 2.0 m so a datum error cannot
cancel) all pass. One documented deviation is retained knowingly: the paper's
Eq. (8) as printed reads load minus resistance, which together with the
Eq. (7) trigger min Z_u < 0 would invert the physics; the repository uses the
resistance minus load reading (ADR-0008), which makes Eq. (7) correct. The
gate therefore **passes**: the decomposition below is built on the verified
datum. This closes the open physics flag for the thesis.

## 3. Methodology

### 3.1 Comparator ladder on one shared sample

Ten comparators (ADR-0040) are evaluated on the identical theta matrix and
identical stochastic seepage-length draw per section, so comparator
differences are physical rather than sampling noise. The static variants are
C0 (raw gross head against H_c at alpha = -1/3, the production static
branch), C0b (raw head, alpha = -1/2), C1 (crack-reduced head, -1/3) and C2
(crack-reduced head, -1/2). The pseudo-static variants C3b and C3a apply the
exact sustained-peak limit at the two exponents. The transient variants are
C4b (production), C4a (transient-only alpha = -1/2, the ADR-0017 hook), and
C4c and C4d (equilibrium end factor 1.0 at each exponent, the ADR-0041
override). Two telescoping ladders are reported: the engine ladder
C0 to C1 to C3b to C4b decomposes the production gap; the physics ladder
C0 to C1 to C2 to C3a to C4a ends at the 3D-consistent transient. The
mission's single five-comparator ladder was split this way because the
production transient runs at alpha = -1/3: a ladder whose C2 carries -1/2 but
whose endpoint is the production engine would re-cross the dimensional axis
inside the temporal step, which is precisely the Failure Mode 4 conflation
the specification prohibits.

### 3.2 The pseudo-static comparator is an exact limit, not a long run

Under a constant outer level the transient model's failure indicator has a
closed form: failure occurs if and only if the heave gate is open at that
level and the crack-reduced erosion head strictly exceeds H_c,transient, the
maximum of the H_eq curve (proof in ADR-0040: below the maximum the pipe
stalls on the rising branch at l_eq at or below l_c; above it the overload is
bounded away from zero along the whole path). Two corollaries follow. First,
C3 equals C2 intersected with the gate, exactly, so the C2 to C3 step
isolates precisely the initiation gate; the mission's C2/C3 consistency check
becomes a provable nesting rather than an empirical hope. Second, the 0.9 H_c
end anchor drops out of the sustained indicator entirely, so the ADR-0009
H_eq-conservatism component lives inside the temporal step and is bounded
there by the C4c/C4d comparators.

The analytic limit was verified against finite-hold ODE integrations
(duration ladder, N = 10 000, holds of 24, 96, 384 and 1536 hours, three
levels per section, both exponents; `stage6_6_*_duration_ladder.json`): the
integrated indicator converges to the analytic limit monotonically from
below and agrees with it exactly (zero disagreements out of 10 000 rows at
every checked level) at the 1536 hour hold, with zero rows ever failing the
ODE without failing the analytic limit (no forward-Euler barrier jumps under
sustained load at 225 s).

### 3.3 Statistical treatment

Every comparator carries per-level Clopper-Pearson 95 percent intervals on
the raw points (the ADR-0024 presentation; at tail levels the ratios quoted
here are the deliverable, not fitted curves). Every component delta carries a
paired bootstrap interval (B = 1000 joint realization resamples, one index
draw shared by all comparators per replicate), which reflects the discordant
sets rather than independent binomials. Components whose interval covers
zero are reported as statistically unresolved. The design-flood evaluation
point is the section HWL, inserted exactly into the conditioning grid; the
KP62.0 levels at and above 51.0 m MSL are the ADR-0024 hypothetical
fit-stabilizers and are shaded as such in the figures.

### 3.4 Verification gates

All gates passed at production N: (i) C0 and C4b are bit-identical to the
persisted production sweep matrices at every common grid level (38 levels at
KP62.0, 23 at KP57.4) with identical theta matrices, so the Stage 6.6
implementation provably evaluates the production engine; (ii) the
continuous-time nesting diagnostics (C4b within C0, C4 within C3 at matched
exponent, end-factor 1.0 within 0.9) hold with exactly zero violating rows
at every level of both sections, extending the ADR-0030 consistency property
across the whole ladder at 225 s; (iii) the algebraically exact nestings
(C1 within C0, C3 within C2 at matched exponent) are asserted inside every
level task; (iv) the full pre-existing test suite stays green alongside the
15 new tests.

## 4. Results

### 4.1 The production gap and its components (engine ladder)

KP62.0 (evidence: `stage6_6_kp62_0_analysis.json`):

| Level [m MSL] | C0 | C4b | Total gap | Head convention | Initiation gate | Temporal (net) |
|---|---|---|---|---|---|---|
| 46.39 (HWL) | 2.1e-4 | 1.0e-5 | +2.0e-4 | +1.7e-4 (85%) | 0 (unresolved) | +3e-5 (unresolved) |
| 48.00 | 0.245 | 0.036 | +0.208 | +0.050 (24%) | 0 (unresolved) | +0.158 (76%) |
| 50.50 | 0.944 | 0.496 | +0.447 | +0.011 (3%) | 0 (unresolved) | +0.436 (97%) |

KP57.4 (evidence: `stage6_6_kp57_4_analysis.json`):

| Level [m MSL] | C0 | C4b | Total gap | Head convention | Initiation gate | Temporal (net) |
|---|---|---|---|---|---|---|
| 39.21 (HWL) | 1.18e-3 | 0 (k=0) | +1.2e-3 | +1.1e-3 (97%) | ~0 (unresolved) | 0 (unresolved) |
| 40.50 | 0.616 | 0.206 | +0.410 | +0.173 (42%) | +2e-4 (resolved, negligible) | +0.237 (58%) |
| 43.25 | 0.9997 | 0.964 | +0.035 | +3e-4 (1%) | 0 (unresolved) | +0.035 (99%) |

Reading: the production gap is a two-component story. The temporal mechanism
dominates through the fragility shoulder and takes over completely toward
saturation; the head convention (exactly the 0.3 D_bl crack term since
ADR-0027/0028 removed r_e from both piping heads) dominates the deep tail at
design levels, the more so the thicker the blanket. The initiation gate
contributes essentially nothing to the production gap at either section:
realizations loaded above H_c at alpha = -1/3 essentially always have the
heave gate open. The pure temporal ratio between the sustained-peak limit
and the real-hydrograph transient, P(C3b)/P(C4b), runs from 7.9 at 47.0 m
down to 1.9 at 50.5 m at KP62.0 [**superseded — under the adopted
L = 40.0 m: 6.0 at 47.0 m down to 1.4 at 50.5 m; see section 8**], and from
3.2 at 39.75 m down to 1.04 at 43.25 m at KP57.4.

### 4.2 The dimensional component (physics ladder)

Switching the resistance scaling to the 3D hole-exit exponent moves a lot of
probability: the dimensional step C1 to C2 is -0.563 (paired 95 percent
interval -0.566 to -0.560) at KP62.0, 48.0 m, and -0.501 (-0.504 to -0.498)
at KP57.4, 40.5 m. The sign is negative throughout the resolved range under
the matrix d70 interpretation: the 3D critical head is lower at these
gradations and seepage lengths, so a 3D-consistent model fails more often
and the dimensional axis opposes the other components. At the 3D endpoint
the temporal step grows correspondingly (+0.517 at KP62.0, 48.0 m), and the
two nearly cancel: the physics-ladder total gap C0 minus C4a is +0.004 at
that level against an engine-ladder total of +0.208. Whether the thesis
should present the static-transient bias as large (engine ladder, both
branches at the Pol-endorsed -1/3 baseline) or as nearly zero (physics
ladder, transient at its calibration exponent) is exactly the ADR-0017
Discussion question; the decomposition quantifies both without collapsing
them.

The bulk d70 sensitivity (N = 10 000, `stage6_6_*_bulk_analysis.json`)
reverses the sign: at coarse framework gradations the Sellmeijer scale group
d_70 cubed over (kappa L) crosses unity and the alpha = -1/2 exponent then
raises rather than lowers F_s, making the dimensional component +0.40 at
KP62.0 (56.5 m) and +0.37 at KP57.4 (43.25 m). The sign of the dimensional
bias is therefore interpretation-dependent, not a universal property of the
3D correction; both d70 readings sit outside the Sellmeijer validity range
(150 to 430 micrometers), so this is a sensitivity statement, not a
calibrated finding.

### 4.3 The initiation gate

At matched exponent and matched crack-reduced head, C3 equals C2 minus the
gate-blocked rows, exactly. At KP62.0 the gate binds almost nowhere (thin
blanket, high r_e: the gate-blocked fraction P(C2 and not C3a) peaks below
0.01): C2 and C3a coincide visually across the whole grid. At KP57.4 the
gate is the dominant suppressor near the design level in the physics ladder:
+0.0825 (0.081 to 0.084) at HWL, larger than the temporal step there
(+0.0102), with the gate-blocked fraction peaking around 0.155 near 39.5 m
before collapsing at higher levels. In the engine ladder the same gate is
negligible at both sections because rows above the higher -1/3 critical head
essentially always heave. The gate evaluated at the sustained peak is the
most favorable case for initiation, so these are lower bounds on gate
suppression under real loading; the remainder (gate timing within the
hydrograph) sits inside the temporal step by construction.

### 4.4 The H_eq-conservatism bound (ADR-0009, closed at the indicator level)

The 0.9 H_c end anchor inflates the production transient P_f by +0.0084
(23 percent of C4b) at KP62.0, 48.0 m, +0.045 (9 percent) at 50.5 m, and
+0.035 (17 percent) at KP57.4, 40.5 m; expressed against the temporal step
it is 5 to 15 percent of the temporal component. The rate-level factor of
about 1.95 established at L = 3 m therefore compresses to a 10 to 25 percent
indicator-level effect at field scale under real hydrographs: most
realizations either breach comfortably or stall comfortably, and only the
marginal band is sensitive to the descending-branch discount. ADR-0009's
open field-scale question is hereby answered at the level that matters for
fragility: the component is real, resolved, and secondary. It slightly
inflates C4 and therefore slightly masks the temporal suppression; the pure
time-constraint bound P(C3) minus P(C4 at end factor 1.0) is 5 to 15 percent
larger than the temporal-net numbers of Section 4.1.

### 4.5 Path dependence, confronted

The static {head convention, dimensional} lattice is complete, so both
orderings and their exact two-toggle Shapley average are reported
(`static_pair_shapley` blocks). At KP62.0, 48.0 m the ordering matters
modestly: the head component is +0.050 taken first and +0.037 taken second
(interaction +0.013, resolved). At KP57.4, 40.5 m it matters a lot: +0.173
taken first against +0.030 taken second (interaction +0.143, resolved), a
factor of almost six, because at the lower 3D critical head most
crack-marginal rows are already failed, leaving the crack term little to
remove. The reported ladders fix the head step first (conventional practice
loads before resistance scaling); the Shapley values (+0.101 head, -0.430
dimensional at KP57.4, 40.5 m) are the order-free compromise. The gate and
temporal steps cannot be reordered against the others (both exist only
inside the transient machinery), so no further path freedom exists to
report. Component magnitudes in Section 4.1 are therefore order-conditional
statements, and at KP57.4 materially so; any thesis text quoting a single
head-convention number must name the ladder it comes from.

### 4.6 Order of magnitude against Pol SIE 2024's Dutch cases

Pol's river-levee cases report cumulative time-effect factors F_td of 10 to
100 for fine sand with long seepage lengths, and below 5 for coarse sand
with thin blankets, where the instantaneous assumption is called realistic;
the coastal base case shows a conditional single-event factor of 300 (0.6
against 0.002) and a first-year factor of 1000. The Tokachi sections are
coarse sand (matrix d70 about 0.7 mm), moderate seepage lengths (33 to
47 m) and long-duration floods (median rising limb 18 h, plateau 9 h,
ADR-0032), so Pol's framework predicts a small-to-moderate temporal factor.
The measured pure temporal ratios (C3 over C4, 1.0 to 8) sit exactly in
that band, and the total conditional bias at design levels (13 to 32 and
beyond) is consistent in magnitude with Pol's conditional single-event
illustrations once the non-temporal components are included. Nothing in the
decomposition is anomalous against the source model's own case studies.

## 5. Physical interpretation

Why the temporal component dominates the shoulder and dies at saturation:
near the shoulder the erosion head exceeds the equilibrium barrier by
centimeters to decimeters for most failing rows, progression rates scale as
the 0.81 power of that small overload, and the canonical flood (a day-scale
peak, not weeks) recedes before mid-speed pipes traverse 33 to 47 m; at
saturation levels the overload is large, the 0.81 power is forgiving, and
the same day-scale peak suffices for almost every row, so time stops
binding. Why the head convention dominates the deep tail: at design levels
only the extreme resistance tail fails at all, the failing set sits within
0.3 D_bl (14 to 24 cm of head) of the threshold for a large share of rows,
and a fixed head decrement removes a disproportionate share of a steep
tail. Why the gate matters only at KP57.4 and only in the physics ladder:
gate suppression requires rows loaded above the (lower, -1/2) critical head
whose blanket overpressure nevertheless stays below the Terzaghi threshold,
which needs a thick blanket and a damped response factor; KP57.4 has both
(D_bl 0.8 m, 200 m foreshore), KP62.0 has neither. The loading regime
qualification from ADR-0032 matters here: the Tokachi flood is not flashy,
so these temporal factors are on the low side of what flashier basins would
show; the temporal component measured here is a property of this loading
shape as much as of the sections.

## 6. Limitations

- The pseudo-static gate is evaluated at the sustained peak, so the gate
  component is a lower bound and gate-timing effects are folded into the
  temporal step by construction.
- The dimensional comparators are an idealized scale-exponent substitution
  (ADR-0017), not a validated 3D model, and both d70 interpretations sit
  outside the Sellmeijer grain-size validity range; the sign reversal under
  the bulk interpretation shows the component is not transferable across
  gradation readings.
- Component magnitudes are order-conditional (Section 4.5); only the
  telescoped totals are order-free.
- The engine-ladder decomposition at HWL rests on 0 to 21 failing rows per
  comparator; those statements are carried by exact binomial intervals and
  ratios, not by fitted curves (ADR-0024), and the unresolved flags in the
  analysis files mark exactly which steps the data cannot separate.
- Everything here is per event and conditional on stage; annualization and
  the climate axis live in Phase 3 (ADR-0023/0038) and were not touched.
- The 225 s grid is validated for failure indicators (ADR-0030/0039), which
  is all the ladder consumes; l_e magnitudes (not used here) would need
  112.5 s (ADR-0039).

## 7. Implications for Sub-question 1

Sub-question 1 asks how large the bias of conventional static assessment is
against time-resolved physics and where it comes from. The answer for the
Tokachi sections: at design flood levels conventional practice overestimates
per-event BEP failure probability by one to one-and-a-half orders of
magnitude (**both figures superseded; see section 9**: KP 62.0's design-HWL bias
is **26.9 [21.6, 35.3]**, resolved at N = 1e6, and KP 57.4's is bounded at
**B ≥ 148** with a resolved anchor of 42.7 at 39.50 m), but
the label "temporal" belongs to only part of it. Through the fragility
shoulder the time constraint is the dominant mechanism (58 to 76 percent of
the production gap, pure temporal ratios of 2 to 8); in the deep tail at
design levels the crack head convention carries most of the gap (85 to
97 percent); the initiation gate is immaterial to the production comparison;
the H_eq-conservatism inflates the transient side by 10 to 25 percent of
itself and is now quantified rather than open; and the dimensional axis is
absent from the production gap by construction, while re-anchoring the
transient at its 3D calibration exponent would erase most of the static
margin (physics-ladder totals near zero through the shoulder) under the
matrix d70 reading and widen it under the bulk reading. The thesis statement
"static practice is conservative because it ignores time" survives, but
only with the qualifier "at these sections, in this loading regime, and
after netting a head-convention term that has nothing to do with time"; the
decomposition supplies the numbers for each clause, with confidence
intervals, at every conditioning level.

---

## 8. KP 62.0 SEEPAGE-LENGTH ADOPTION ADDENDUM (2026-07-29; ADR-0047)

> **Note added 2026-07-30: section 9 supersedes this section's HWL figures.** The
> geometry adopted here is unchanged and everything below about *L* stands; what
> section 9 replaces is the statistical status of the HWL cell — 44.7 on 4 rows
> becomes **26.9 [21.6, 35.3] on 63 rows** at N = 1e6.

**What changed.** KP 62.0's `geometry.L` was adopted from the ADR-0047 DEM survey,
47.0 → **40.0 m**, because the 1998 value credited a landside berm that never
existed. KP 57.4 was **not** adopted, so **every KP 57.4 number in sections 1 to 7
stands unchanged**. The KP 62.0 ladder was re-run in full at N = 1e5.

**Gates re-passed.** The production drift guard is **bit-identical at all 38 common
levels** against the re-run KP 62.0 sweep, and **every Euler-flip count is exactly 0
at N = 1e5** across all five diagnostics at all 39 levels — the same gates section 3
defines. (KP 62.0 stays clean at N = 1e6 too; KP 57.4 does not — see section 9.)

**The headline number, and a correction to how it should be quoted.** Section 1
reports the KP 62.0 conventional-practice bias at HWL as *"a factor of about 21"*.
Under the adopted geometry the same cell reads **44.7** (C0 static 1.79e-3 against
C4b transient 4.0e-5). **Neither figure is statistically resolved, and the
apparent doubling is an artefact of counting noise**: at HWL the transient
comparator rests on **1 failing row out of 100 000** before adoption and **4** after,
with Clopper-Pearson intervals (2.5e-7 to 5.6e-5, and 1.1e-5 to 1.0e-4) that overlap
heavily. Section 6 already warned that the HWL decomposition rests on 0 to 21 failing
rows per level; this re-run demonstrates the consequence concretely.

**What *is* resolved is the opposite of the nominal HWL move.** At every level where
the transient comparator carries adequate counts, the bias factor **falls** by
roughly a third:

| level [m MSL] | C4b rows, L = 47.0 | C4b rows, L = 40.0 | bias, L = 47.0 | bias, L = 40.0 |
|---|---|---|---|---|
| 46.39 (HWL) | 1 | 4 | 21.0 | 44.7 | *(not resolved)* |
| 46.75 | 15 | 130 | 27.9 | 13.2 | *(marginal)* |
| 47.00 | 101 | 499 | 15.0 | **10.5** |
| 47.50 | 886 | 3 286 | 9.9 | **6.3** |
| 48.00 | 3 627 | 10 127 | 6.7 | **4.4** |
| 48.50 | 9 252 | 21 141 | 4.9 | **3.1** |
| 49.00 | 17 684 | 34 172 | 3.7 | **2.4** |
| 49.50 | 28 144 | 47 270 | 2.8 | **1.9** |

That is a consistent factor of ≈ 0.65, and it agrees with the independent
paired-bootstrap measurement in ADR-0047 §4.5, which puts the ratio-of-ratios at
0.64–0.70 across the reachable range (0.475 at the nearest production level to HWL,
95 % CI [0.263, 0.724], resolved).

**How to quote the KP 62.0 bias from now on.** Quote it at a level where it is
resolved, with its level stated — e.g. *"a factor of 10.5 at 47.0 m MSL"* — or quote
the HWL figure explicitly as unresolved with its row count. Do **not** quote "about
21" as a current number: it belongs to the superseded L = 47.0 m geometry, and it was
never resolved even there.

Superseded artifacts under `results/superseded_adr0047_L47/stage6_6/`.

---

## 9. DESIGN-HWL BIAS RESOLVED AT N = 1e6 (2026-07-30; authoritative where it differs from sections 1 to 8)

Companion note `docs/decisions/adr0040-hwl-bias-resolution.md` (pre-registered
before any number was computed), driver `scripts/hwl_bias_resolution.py`, evidence
`docs/decisions/adr0040-hwl-bias-resolution.json`, tests
`tests/test_hwl_bias_resolution.py`. This closes the 2026-07-29 production
campaign's open decision 6.

**Why.** Section 8 and campaign §6.1 both reported the design-HWL bias as *not
statistically resolved*: 4 failing transient rows at KP 62.0 and **0** at KP 57.4
out of 100 000. The owner chose the method — brute force at N = 1e6 first, then
validate tilted importance sampling against it. Both were executed.

**The KP 62.0 headline is now resolved, and the previous figure was an
overstatement.**

| | N = 1e5 (section 8) | **N = 1e6 (this section)** |
|---|---|---|
| 46.39 m (design HWL) | 44.7 on **4** rows, unresolved | **26.9, 95 % CI [21.6, 35.3], on 63 rows — RESOLVED** |
| 46.50 m | 26.2 on 15 rows, unresolved | **21.6, [18.8, 25.2], on 176 rows — RESOLVED** |

The two are statistically consistent (the N = 1e6 transient P_f of 6.30e-5 lies
inside the N = 1e5 Clopper–Pearson interval), so **44.7 was counting noise on four
rows, not a different answer** — it overstated the bias by a factor of 1.66.
**Quote 26.9 at 46.39 m MSL.** Do not quote 44.7 or "about 21".

**Gates.** The N = 1e5 drift guard is bit-identical to the persisted sweeps at 38
and 23 levels with identical theta; at KP 62.0 every Euler-flip count is 0 at all
39 levels **at both N = 1e5 and N = 1e6**; the N = 1e6 result is consistent with
N = 1e5 at all 59 adequately counted branch comparisons.

**Gate G-A2 fired at KP 57.4, and only at N = 1e6.** Four `c4b_not_c3b`
barrier-jump rows out of 1e6, at **39.50 / 40.25 / 40.75 m** — a rate of 4e-6
whose expected count at the production N = 1e5 is 0.4, which is why every earlier
run (this report's sections 1 to 8, the campaign's G3, and this study's own
N = 1e5 arm) saw exactly zero. **Every unqualified "all Euler-flip counts are 0"
in this repository is an N = 1e5 statement.** No production result is affected —
all run at N = 1e5, where the gate passes and the drift guard is bit-identical.
The recommended KP 57.4 quotable anchor at 39.50 m **is itself one of the flip
levels**, carrying 1 barrier-jump row out of its 521 transient failures (0.19 %);
a spurious transient failure inflates P_transient and therefore *deflates* B, so
the artifact biases 42.7 downward by about 0.2 % — negligible against the 1.18x
interval, and conservative in direction. This is the indicator-level counterpart
of ADR-0039's KP 57.4 Δt rider.

**KP 57.4 remains unresolved, but its bound improves 4.6×.** At N = 1e6 the design
HWL carries **2** failing transient rows (A2, 39.25 m: 10). R1 still fails.
Reaching 30 rows would need N ≈ 1.5e7. The defensible statements are a
Clopper–Pearson bound **B ≥ 148** at 39.21 m (superseding *"at least 32"*, which
rested on zero rows) and a **resolved anchor above HWL: B = 42.7 [39.4, 46.6] at
39.50 m MSL** on 521 rows — the figure the thesis should lead with at this section.

**A new numerical finding at KP 57.4, visible only at 1e6.** Gate G-A2 **failed**
there: **4 rows in 1e6** fail the transient comparator without failing the
sustained-peak analytic limit, which is impossible in continuous time and is the
ADR-0030 forward-Euler barrier-jump fingerprint. They sit at 39.50 m (1), 40.25 m
(2) and 40.75 m (1) — **not** at either design-HWL anchor. At the production
N = 1e5 the expected count is 0.4, which is why every previous run, including this
study's own N = 1e5 gate, saw exactly zero. **No production result is affected**
(all run at N = 1e5, where the gate passes and the drift guard is bit-identical),
and KP 62.0 is untouched (0 flips at all 39 levels). It is the indicator-level
counterpart of ADR-0039's rider that KP 57.4 needs Δt ≤ 112.5 s for l_e magnitudes.
The recommended 42.7 at 39.50 m contains 1 such row in 521, biasing it **down** by
0.2 % — conservative, and stated.

**The tilted importance sampler was tested here for the first time and did NOT
validate.** V1 passed, V3 passed, but V2 failed (one level disagrees resolvably)
and V4 failed (Kish n_eff = 86.9 against a floor of 200). Its transient-side CoV
gain is real (4.66×, consistent with ADR-0029), but a tilt optimised for the
transient region **inflates the static branch's CoV 1.5× at the anchor and up to
940× at saturation** — fatal for a *ratio between* branches. Brute force was used
throughout; no weighted number appears in any result above. ADR-0029's own claims
are unaffected: what failed is a new application to a different estimand.

**The number is not quotable bare.** The epistemic band on the bias at 46.39 m runs
from **2.59** (upper regional `k_aq`) through 26.9 (production) to beyond 27 (the
field-`k_aq` and +datum arms), and is *indeterminate* at the field geometric mean,
where neither branch fails at all. That band is **6 to 9× wider than the
statistical interval**. `k_aq` dominates it, `z_toe` is second (rho = 0.515
resolved at −0.30 m), `m_p` cancels (rho = 1.010 — the pre-registered negative
control, which passed), and `gamma_bl_sub` is exactly inert (rho = 1.000). Section
1's attribution and all component tables are unchanged.
