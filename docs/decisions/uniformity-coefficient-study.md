# Study: the coefficient of uniformity, resistance to piping, and internal stability

Date: 2026-09-25 (Green Light item 1)
Status: Part 1 (source facts and pre-registration) committed before any arm was
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
