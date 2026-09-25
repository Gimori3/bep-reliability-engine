# Study: the coefficient of uniformity, resistance to piping, and internal stability

Date: 2026-09-25 (Green Light item 1)
Status: Complete. Part 1 (source facts and pre-registration) was committed (7d3593a) before any arm was
computed. Part 2 records the outcome.

Evidence: `uniformity-coefficient-study.json`, driver
`scripts/uniformity_coefficient_study.py`, data
`data/processed/oyo_1999_gradations_by_layer.csv` and the per-specimen matrix
gradations of `bimodal-foundation-d70-study.json` (Green Light item 4).

The supervisors' note: the coefficient of uniformity belongs in the Discussion,
because well-graded soils resist piping, the Tokachi foundation is well graded,
and the thesis discusses grain size but not grading.

## Part 1: source facts (read on the page) and pre-registration

### 1.1 Where C_u sits in the model

- The Sellmeijer (2011) resistance factor carries `(C_u / C_u,m)^0.13`,
  `C_u,m = 1.81` (`sellmeijer.C_U_MEAN`, `_factor_Fr(uniformity_cu=...)`). It is
  evaluated at the mean for every realization, so the ratio is exactly 1
  (ADR-0015 keeps C_u and KAS as module constants). The same is true of the
  relative density and angularity terms.
- The factor multiplies the **single-source** `H_c`, so it reaches the static
  comparator and the transient equilibrium anchor identically (the same
  structure as the ADR-0045 model factor, but deterministic).
- The Pol progression rate has no C_u term; its fitted domain is stated as
  `2 <= C_u <= 3` (`progression.py` module docstring, after Pol CompGeo 2024).

### 1.2 What the literature on disk says (page references are to the printed page)

1. **Sellmeijer et al. (2011), EJECE 15(8).** The exponent 0.13 is a
   multivariate-regression weight fitted to 38 small-scale tests (Table 1,
   p. 1145). Table 2 (p. 1146) restricts the rule to U = 1.3 to 2.6, mean 1.81,
   and the text requires that "the adapted piping rule may be only applied
   within the limits of the involved parameters during testing" (p. 1146).
   Section 8 (p. 1152): "The influence of the parameters U and angularity is of
   the order of the scatter in the tests." Inside the tested range the factor
   spans `(1.3/1.81)^0.13 = 0.958` to `(2.6/1.81)^0.13 = 1.048`, i.e. -4 to +5 %
   on `H_c`.
2. **Van der Zee (2011), Deltares/TU Delft MSc** (on disk as `Influence of sand
   characteristics on the piping process.pdf`; not in the thesis bibliography).
   The SBW small-scale set behind the regression is dominated by one sand
   (Baskarp, 18 tests), so C_u was barely varied; he recommends varying it more.
   In the De Wit series C_u and d70 are correlated at r = 0.99 (his Table 2-9),
   so their effects cannot be separated there.
3. **Van Beek (2015), PhD thesis.**
   - p. 40: in the revised rule "the uniformity coefficient and grain angularity
     proved to have a negligible effect on the critical gradient in the tested
     range".
   - p. 20, reporting Townsend et al. (1988): graded and gap-graded soils "did
     not undergo pipe formation but sheet flow"; non-uniform sands (d60/d10 > 5)
     did not fail at all up to the set-up's maximum gradient of 1.2.
   - p. 41, Schmertmann (2000) weights C_u heavily, but "the number of
     experiments with higher uniformity coefficients is limited and often other
     phenomena such as sheet flow have often been observed".
   - p. 83: in De Wit's data "the uniformity coefficient increased with grain
     size", so the two effects could not be distinguished.
   - pp. 87 to 88 (section 4.7.3, the only direct test): fines added to a sieved
     Itterbeck sand "resulted in significantly stronger samples", with three
     caveats stated there: permeability also changed, fines migration may need
     longer test durations than used, and bridging of migrating fines lowered
     the downstream permeability; "the range of uniformity coefficients tested
     in this series was relatively small", and for higher-C_u sands "other
     processes, such as filtering of fines, may affect the critical gradient".
     The removal of fines lowers the critical gradient (Richards and Reddy 2012,
     cited there).
   - p. 107 and section 6.3.3 (p. 139): an increase in C_u raises the critical
     head (the same fines-addition series).
   - p. 186 (section 6.9.6, conclusions on grain-scale incipient motion): "It is not yet
     possible to determine the effect of the uniformity coefficient since no
     laminar flow experiments have been conducted with non-uniform sands."
4. **Dutch assessment form.** Schweckendiek (2014), p. 26, Eq. (3.16), the revised
   rule as "supposed to be used for safety assessments in the Netherlands",
   writes `F1 = eta (gamma_s/gamma_w - 1) tan(theta)` with **no** relative
   density, uniformity or angularity term. Pol et al. (SIE 2024, below Eq. 12)
   state that the effect of D_r, C_u and KAS "is neglected by choosing their
   values equal to the mean values". The TR Zandmeevoerende Wellen (1999)
   Appendix II (pp. A.II.6 to A.II.7) uses U only to estimate permeability (Den Rooijen formula), not
   resistance.
5. **Japanese practice.** In the PWRI guide (`pwri_2014`, syousasekkei_point
   1407), the uniformity coefficient appears only in permeability estimation
   (p. 21 section 5.4, and appendix A5 to A7: Hazen coefficient, Fukuda-Uno
   method). The piping verification criteria (local gradient 0.5, G/W 1.0;
   project memory and thesis Chapter 2) carry no grading term.
6. **Internal stability (suffusion).**
   - Okamura et al. (2025), Soils and Foundations 65, p. 14: at Gounokawa most
     of the large sand ejecta "originated from the gravel layer" by suffusion;
     "sandy gravel with a gap-graded grain size distribution, having less than
     approximately 25 % finer grains, exhibits internal instability" (after
     Skempton and Brogan 1994); Kenney-Lau (H/F)min = 0.5, unstable grains 0.3 to
     2 mm.
   - Ronnqvist (2017), EWG-IE Delft, pp. 14 to 19: unless the finer fraction is
     below about 35 %, a widely graded soil is probably not susceptible to
     suffusion, because the coarse particles float in the finer fraction, "however,
     such a soil can still be vulnerable to backward erosion"; the Kenney-Lau
     boundary H/F = 1 is conservative, and for silt-sand-gravel soils
     0.68 <= H/F < 1 marks potential stability, 0.45 <= H/F < 0.68 potential
     instability and H/F < 0.45 the suffusive region.
   - Ronnqvist and Viklander (2014), Geomaterials 4(4), 129 to 140 (read online,
     DOI 10.4236/gm.2014.44013): H is the mass fraction between D and 4D, F the
     fraction finer than D; the minimum is taken over F = 0 to 20 % for a widely
     graded material and 0 to 30 % for a uniformly graded one; boundary H = F.

### 1.3 Which C_u (from item 4's per-specimen reconstruction)

Section medians over the 28 Ag specimens: whole-specimen Uc 44 / 34 / 80 / 46
(printed); matrix finer than 2 mm, 46 / 42 / 66 / 42 (dominated by the fines
tail); sand fraction 0.075 to 2 mm, 6.4 / 4.5 / 5.3 / 5.4. Every candidate lies
above the tested maximum of 2.6: the sand-matrix value by a factor 1.7 to 2.4,
the others by 13 to 30.

### 1.4 Arms (fixed before computing)

Implemented in memory, `persist=False`, production seed (common random
numbers), N = 1e5, matrix reading, historical, by replacing `theta_repose_deg`
with `atan(c tan 37 deg)`: `theta_repose` enters `F_r` and nothing else, so this
multiplies the single-source `H_c` by exactly `c` in both branches (checked:
`_factor_Fr(theta_repose_rad=...)` equals `_factor_Fr(uniformity_cu=2.6)` to
2.2e-16). No config field is added and no knob is built.

| Arm | C_u | c = (C_u/1.81)^0.13, KP 57.4 / 58.8 / 60.0 / 62.0 |
|---|---|---|
| `cap` | 2.6, the tested maximum | 1.048 at all four |
| `sand` | sand-fraction median | 1.178 / 1.125 / 1.150 / 1.154 |
| `matrix` | matrix (finer than 2 mm) median | 1.521 / 1.505 / 1.595 / 1.503 |

The `matrix` arm is numerically the same lever as the whole-specimen Uc
(1.46 to 1.64), which is the "well graded" reading taken at face value.

Each arm's baseline must be bit-identical to the persisted production sweep
(else abort).

### 1.5 Predictions

- **P1 (monotonicity, could fail through the progression).** At every level,
  every row failing an arm also fails the baseline, in both branches.
- **P2 (static stretch, a theorem).** The static failure indicator is
  `h - z_toe > c H_c`, so the stage above the toe at any static quantile scales
  by exactly c. Checked on the curves by interpolation.
- **P3 (the two metrics disagree, opposite to m_p).** A deterministic
  multiplier on a near-lognormal `H_c` shifts both reliability indices by about
  the same amount, so Delta-beta is nearly invariant while B moves. Predicted at
  quotable levels (attainable, all four marginal counts >= 30): |Delta-Delta-beta|
  < 0.10 for `cap` and `sand`, < 0.20 for `matrix`; B moves by more than the
  index does, rho > 1 (B rises as the curves move deeper into the tail at a
  fixed stage).
- **P4 (lever size against the grain-size bracket).** On the median `H_c`, the
  `matrix` arm (1.50 to 1.60) is a larger lever than the matrix-to-bulk d70
  bracket at KP 60.0 (analytically about `(1.3/0.74)^0.4 = 1.25`) and smaller at
  the other three (about 2.1, 3.3 and 3.2). The `sand` arm is smaller than the
  bulk bracket everywhere.
- **P5 (annual, prior side, 250 m, primary surface).** `cap` changes annual
  piping probability by less than a factor 1.5 and no mechanism ordering;
  `sand` reduces it by 1.5 to 5 and reverses at most KP 62.0 historical;
  `matrix` reduces it by more than 10 at KP 58.8 and KP 60.0 and reverses at
  least two of the eight section-and-climate cells.
- **P6 (internal stability).** Kenney-Lau (H/F)min over F <= 20 % on the
  reconstructed whole-specimen curves is below 1.0 for at least 20 of the 24
  gravel specimens (finer than 2 mm below 50 %), and the four sand-rich
  specimens are above 1.0. Because log-linear interpolation fills any gap, the
  reconstruction biases H upward; a rigorous upper bound over every monotone
  curve through the tabulated points is also computed, and "unstable" is claimed
  robustly only where that bound is below 1.0 (predicted: at least half of the
  gravels).
- **P7 (descriptive).** The fraction finer than 2 mm, a proxy for the finer
  fraction of a gap-graded soil, is below 35 % in at least 16 of the 24 gravels.

### 1.6 Decision rules

- The production treatment (C_u at the regression mean) changes only if the
  evidence establishes the sign **and** size of the C_u effect for gap-graded
  sand-gravel outside 1.3 to 2.6. If it does not, C_u is reported as a
  one-sided bracket and a limitation, the owner is not asked to change a prior,
  and no knob or ADR is added (an in-memory variant is sufficient for a
  sensitivity that is measured once and adopted nowhere).
- A mechanism ordering is "reversed" when the leading mechanism of the arm
  differs from the baseline's in that cell.

## Part 2: outcome (2026-09-25)

Run: `python scripts/uniformity_coefficient_study.py --n-jobs 10` (about 40 min).
Every baseline was bit-identical to its persisted production sweep; the Phase 3
baseline reproduced all 228 matrix / prior / 250 m / primary rows of
`rq4_annual.csv` field for field, both from the persisted curves and again from
the in-memory baseline curves (so the in-memory route is the production one);
the 110 segments without a piping source are identical in every arm.

### 2.1 Prediction scoring

| | Prediction | Outcome |
|---|---|---|
| P1 | no row fails an arm without failing the baseline | **held**: zero in both branches at every level of all 12 arm-section pairs; nesting intact (zero transient-not-static rows) |
| P2 | static stage above the toe scales by c | **held**: 1.037 to 1.057 for c = 1.048, and within 0.015 of c for every other arm (grid interpolation) |
| P3 | delta-beta nearly invariant, B moves | **failed in its central claim.** B rises (rho > 1) as predicted, but delta-beta **falls**, and by more than predicted. The two metrics move in opposite directions (section 2.3) |
| P4 | matrix arm larger than the d70 bracket at KP 60.0 only | **held**: static lever of the bulk reading 2.06 / 3.31 to 3.35 / 1.25 / 3.18; matrix arm 1.52 / 1.51 / 1.60 / 1.50 |
| P5 | annual reductions and reversals | **partly failed.** cap reduces annual piping probability by 1.10 to 1.32 and reverses nothing (held); sand by 1.29 to 2.45 (four cells below the predicted 1.5) and reverses nothing (held); matrix by 2.86 to 43.7, above 10 at KP 60.0 only (predicted at KP 58.8 too), and reverses **one** cell, KP 62.0 historical (predicted at least two) |
| P6 | Kenney-Lau unstable | **partly failed.** Reconstructed curve, F <= 20 %: all 24 gravels below 1 (held). Robustly (every consistent curve): 9 of 24 (predicted at least 12, failed). The four sand-rich specimens are also below 1 on the whole curve (predicted above, failed); their minima sit in the silt (section 2.5) |
| P7 | finer than 2 mm below 35 % in >= 16 gravels | **held**: 18 of 24 (5 below 25 %) |

### 2.2 The fragility curves and the design levels (matrix, historical, N = 1e5)

Curve shift at P = 0.1, static / transient (m): cap 0.09 to 0.10 / 0.08 to 0.12;
sand 0.21 to 0.35 / 0.20 to 0.38; matrix 0.85 to 1.32 / 0.84 to 1.35 (largest
at KP 60.0 in every arm). The matrix-to-bulk transient shift at the same
quantile is 1.71 / 3.84 / 0.57 / 5.24 m, so only at KP 60.0 does the matrix-C_u
arm move the transient curve further than the bulk reading does.

Design levels (nearest grid level):

| KP, level | Baseline P_s / P_t, B, dbeta | cap | sand | matrix |
|---|---|---|---|---|
| 58.8, 41.00 m | 0.609 / 0.197, 3.09, 1.13 | 0.542 / 0.164, 3.30, 1.08 | 0.434 / 0.120, 3.61, 1.01 | 0.103 / 0.021, 4.89, 0.77 |
| 60.0, 42.75 m | 0.353 / 0.056, 6.34, 1.22 | 0.283 / 0.041, 6.84, 1.16 | 0.167 / 0.021, 7.79, 1.06 | 0.0097 / 0.00088, 11.0, 0.79 |
| 57.4, 39.25 m | 5.1e-4 / 0 | 2.3e-4 / 0 | 3e-5 / 0 | 0 / 0 |
| 62.0, 46.50 m | 2.8e-3 / 1.3e-4 (13 rows) | 1.7e-3 / 4e-5 | 4.2e-4 / 1e-5 | 1e-5 / 0 |

KP 57.4 and KP 62.0 do not resolve the design-level comparison at N = 1e5 in any
arm (as at baseline); their comparison is read at the quotable levels below.

### 2.3 The comparison: C_u does not cancel in either metric, and the two metrics disagree in direction

Over the quotable levels (attainable, all four marginal counts >= 30; the metric
study's own paired bootstrap, 2000 resamples):

| Arm | quotable levels | rho = B_arm / B_base | Delta-Delta-beta | resolved (rho / index) |
|---|---|---|---|---|
| cap | 53 | 0.97 to 1.08 | -0.034 to -0.090 | 45 / 53 |
| sand | 52 | 1.02 to 1.31 | -0.095 to -0.272 | 47 / 52 |
| matrix | 43 | 1.05 to 1.90 | -0.276 to -0.631 | 41 / 43 |

Every quotable index displacement is resolved and negative; every resolved ratio
displacement is above 1 (the one quotable rho below 1, 0.97 at KP 62.0 46.75 m in
the cap arm, is unresolved); where the two metrics disagree on resolution (15
levels) it is always the index that resolves and the ratio that does not.

**Why, from the limit-state structure.** Static failure is `h - z_toe > c H_c`.
Under the sustained-peak limit (ADR-0040) transient failure is
`gate and (h - z_toe) - 0.3 D_bl > c H_c`, i.e.
`(h - z_toe)/c - 0.3 D_bl / c > H_c`, while the gate compares the unscaled blanket
head with the unscaled blanket weight. An arm at stage h is therefore the
baseline at the equivalent head `(h - z_toe)/c` **with the crack decrement and
the gate threshold both shrunk by c relative to the head**. Two effects follow:
(i) the equivalent head is lower, which moves the comparison deeper into the
tail, where B is larger (B decays with stage), so the ratio rises; (ii) the
head-convention and gate parts of the gap shrink, so the index difference falls.
This is the reverse of the prediction, which modelled the arm as a pure shift of
ln H_c and so forgot that the crack decrement and the gate do not scale. (The
explanation is derived from the limit states; it was not separately measured.)

**Magnitude against the measured knobs.** In the index metric the cap arm
(0.03 to 0.09) is comparable to the critical pipe length (at most 0.10) and
below the model factor (0.13 to 0.19); the sand arm (0.09 to 0.27) exceeds both;
the matrix arm (0.28 to 0.63) exceeds the conductivity bracket's index
displacement (up to about 0.45, thesis Chapter 8). In the ratio metric every arm
is far below the conductivity bracket (up to 72). **In index terms, the
extrapolated uniformity term is the largest single lever measured on the
comparison**, but only by extrapolating an empirical exponent 16 to 36 times
beyond its calibration.

### 2.4 Annual probabilities and the mechanism ordering (prior side)

Entries are the reduction factor of annual piping probability and the piping share.

| Cell | baseline piping / overflow, share | cap | sand | matrix | bulk reading |
|---|---|---|---|---|---|
| KP 57.4 hist | 4.98e-4 / 0, 1.00 | 1.24, 1.00 | 2.24, 1.00 | 12.0, 1.00 | 240 |
| KP 57.4 +4K | 7.52e-3 / 9.1e-4, 0.89 | 1.12, 0.88 | 1.53, 0.84 | 3.51, 0.70 | 13.3, overflow leads |
| KP 58.8 hist | 6.76e-3 / 1.95e-4, 0.97 | 1.14, 0.97 | 1.41, 0.96 | 4.14, 0.89 | 1700, overflow leads |
| KP 58.8 +4K | 3.77e-2 / 2.53e-3, 0.94 | 1.10, 0.93 | 1.29, 0.92 | 2.86, 0.84 | 141, overflow leads |
| KP 60.0 hist | 3.22e-4 / 0, 1.00 | 1.32, 1.00 | 2.45, 1.00 | 43.7, 1.00 | 4.6 |
| KP 60.0 +4K | 4.27e-3 / 2.3e-5, 0.99 | 1.20, 0.99 | 1.78, 0.99 | 10.3, 0.95 | 2.65 |
| KP 62.0 hist | 7.64e-4 / 1.99e-4, 0.79 | 1.21, 0.76 | 1.87, 0.67 | 8.44, **0.31, overflow leads** | 4.6e4, overflow leads |
| KP 62.0 +4K | 7.74e-3 / 8.39e-3, 0.48 (overflow's point estimate) | 1.14, 0.45 | 1.53, 0.38 | 4.05, 0.19 | 502, overflow leads |

Only the matrix arm reverses a cell, KP 62.0 historical. At KP 60.0 the matrix
arm lowers annual piping probability more than the bulk grain-size reading does
(43.7 against 4.6 historically, 10.3 against 2.65 under warming); everywhere
else the bulk reading is the larger lever, by one to four orders of magnitude.
**Posterior side not measured**: the 2016 update moves the baseline rows by at
most 11 % (KP 58.8), leaves KP 62.0 exactly unchanged and changes no ordering;
a larger H_c can only reduce the rows it rejects.

### 2.5 Internal stability of the aquifer gradations

Kenney-Lau shape analysis on the 28 reconstructed whole-specimen curves
(widely graded, F <= 20 %):

- All 24 gravel-supported specimens (finer than 2 mm: 18.5 to 46.2 %) have
  (H/F)min below 1 on the reconstruction: 0.10 to 0.63, median 0.45, 12 in the
  Ronnqvist (2017) suffusive band (< 0.45) and 12 potentially unstable (0.45 to
  0.68). The bound over every monotone curve through the tabulated points is
  below 1 for 9 of them, so those 9 are unstable whatever the curve does between
  tabulated points; for the others the reconstruction cannot decide.
- Most minima sit at D of about 0.019 mm (4D = 0.075 mm), inside the fines, where
  the curve has only the clay and fines points; they describe the flat fines
  tail. **Post hoc** (not pre-registered), restricting D to 0.075 mm and above,
  the window in which the sand matrix meets the gravel framework: 21 of 24
  gravels below 1 on the reconstruction, 8 robustly; by Ronnqvist's zones 3
  suffusive, 6 potentially unstable, 12 in the potential-stability band (0.68 to
  1.0) and 3 stable. The minima lie at 0.08 to 2.3 mm, mostly 0.35 to 1 mm,
  overlapping the size range Okamura et al. (2025) found unstable at Gounokawa
  (0.3 to 2 mm). The four sand-rich specimens (54 to 100 % finer than 2 mm) are
  stable in this window (1.25 to 2.71) or, for the one whose fines exceed 20 %,
  have no window.
- 18 of the 24 gravels have less than 35 % finer than 2 mm (5 less than 25 %),
  the range in which the coarse fraction carries the load and the finer fraction
  can be washed through it (Ronnqvist 2017; Okamura et al. 2025 after Skempton and
  Brogan 1994).
- The printed curvature coefficient Uc' lies between 1 and 3 for 17 of the 28
  specimens. A three-point classification test therefore calls many of them well
  graded, but it cannot see a gap above d30, and the shape analysis does.

Reading: the gravels sit at or below the classical internal-stability boundary,
like the Gounokawa gravel (H/F 0.5) whose ejecta were attributed to suffusion.
The reconstruction cannot settle the marginal ones; the robust nine are settled.
The sand-rich layers, including the two at the aquifer top (KP 58.8 B-4,
KP 62.0 B-8), are internally stable in the sand window and are the classic
backward-erosion material (sand-fraction C_u 2.4 and 3.9).

### 2.6 What the evidence supports

1. **The supervisors' premise is right in the direction of Sellmeijer's own
   regression and not established for these soils.** Resistance rises with C_u
   inside 1.3 to 2.6, by at most 5 % on H_c, "of the order of the scatter". No
   experiment isolates C_u above that range for backward erosion: the only
   direct series adds fines to one sand and is confounded with permeability and
   fines migration, and graded and gap-graded soils in the older flume series
   tended not to form pipes at all (sheet flow, or no failure). The Dutch
   assessment form and the progression model's reference application drop the
   term; Japanese verification uses grading only to estimate permeability, and
   its gravel-content screens concern the embankment body.
2. **"Well graded" is the wrong description of the operative material.** The
   high whole-specimen Uc of 34 to 80 comes from a gap between a sand matrix and
   a gravel framework. The sand fraction itself has C_u 4.5 to 6.4. By shape
   criteria the gravels are internally unstable or marginal, which is the
   opposite of the property the grading intuition relies on: their sand can be
   washed through the framework (suffusion), a separate mechanism the model does
   not represent, with a two-sided effect on piping resistance (fines removal
   lowers the critical gradient; bridging and filtering raise it).
3. **Production treatment retained** (decision rule 1.6): holding C_u at the
   regression mean is conservative against the regression, since every derived
   C_u lies above 1.81. No knob, no ADR, no config change. The sensitivity is
   carried as a bracket with the numbers above.
4. **What it does to each conclusion.** Absolute probabilities: lower under
   every arm, modestly at the tested maximum. RQ1: B rises and delta-beta falls,
   so the uniformity term is a condition on the comparison that does not cancel
   in either metric, and in the index metric its extrapolated value is the
   largest lever measured. RQ3: only the whole-grading arm moves an ordering (KP
   62.0 historical to overflow); the sand arm leaves every ordering in place.
   RQ2 (the survival update) is not re-run; RQ4 ratios are not re-derived.
5. **Owner decision (2026-09-25, AskUserQuestion):** carry it in the Chapter 8
   Discussion and limitations register and as a stated condition in the
   Chapter 6 conditions register and the Chapter 9 answers register for
   sub-questions 1 and 3; the Summary is not changed.

### 2.7 Records corrected

Thesis Appendix B justified the pinned C_u with "three shallow matrix proxies"
of whole-specimen Uc 33.4 to 64.6 and stated that the matrix gradation could not
be separated from the OYO percentiles. Item 4 showed those specimens are levee
embankment fill and derived the aquifer matrix gradations; the paragraph was not
updated then and is corrected now.
