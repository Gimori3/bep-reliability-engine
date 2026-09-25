# Study: the bimodal foundation, the operative d70 and the distribution chosen for it

Date: 2026-09-24 (Green Light item 4)
Status: Complete. Part 1 (pre-registration) was committed (ed0f59f) before any
matrix d70 was computed; Part 2 records the outcome. **The owner adopted the
outcome as a production change: ADR-0054** (all four matrix means re-based, clip
ceiling 2 mm, bulk unchanged). Part 3 records the production cascade that
ADR-0054 triggered (2026-09-25) and what it moved.

Evidence: `bimodal-foundation-d70-study.json`, driver
`scripts/bimodal_foundation_d70_study.py`, data
`data/processed/oyo_1999_gradations_by_layer.csv`.

## Part 1: what was found in the source before computing, and what is predicted

### 1.1 Source facts established by reading the pages (not by computation)

1. **The OYO 1999 report tabulates its laboratory results per layer**
   (report p. 51, PDF page 56: "results are compiled per layer in Tables
   4-3-1 to 4-3-5"). Table 4-3-1 (report p. 52) is headed "Tokachi right
   bank, embankment fill" and holds the fill layers Bg (gravelly), Bs (sandy)
   and Bc (cohesive). Table 4-3-2 (report p. 53) is headed "Tokachi right
   bank, foundation" and holds Ac (blanket), Ag (aquifer gravel), Ns (lower
   gravel) and K1p (volcanic ash). The purpose of the laboratory programme is
   stated on report p. 27: to characterise "the embankment fill material and
   the gravelly soils".
2. **All three specimens behind the adopted matrix d70 means are embankment
   fill.** The specimens the thesis and the provenance call B-2-1 (KP 57.4),
   B-4-1 (KP 58.8) and B-6-1 (KP 60.0) are, in OYO's own numbering, 57.4,
   58.8 and 60.0 (sheet 4 labels 57.4-1, 58.8-1, 60.0-1, no borehole entered).
   Table 4-3-1 files them under Bc, Bs and Bs respectively. The per-borehole
   soil logs (Figure 4-3-1, report pp. 56 to 64) place each at 0.50 to 1.00 m
   inside a fill column 3.5, 4.4 and 3.8 m deep. They are not at the
   blanket-aquifer transition; they sit about 3 to 4 m above the aquifer top.
3. **The thesis relabels the sheet-4 specimens one position down.** Sheet 4
   numbers the shallow specimen by section (57.4-1) and the deeper two B-2-1,
   B-2-2; the thesis table `tab:app_grainsize` and the provenance call them
   B-2-1, B-2-2, B-2-3. Depths and values travel with the relabelled rows, so
   no number is displaced, except as in item 4.
4. **At KP 58.8 the two laboratory conductivities are attached to the wrong
   specimens** in `tab:app_grainsize`, `tab:app_lab_perm` (to be confirmed)
   and the ADR-0012 companion analysis. Sheet 4 (image checked) and Table
   4-3-1 agree: 9.16e-4 cm/s belongs to the 0.50 to 1.00 m specimen (24.0 %
   gravel, d60 0.459 mm) and 2.84e-3 cm/s to the 2.30 to 3.00 m specimen
   (53.1 % gravel, d60 7.1 mm). The deep 6.50 to 7.00 m aquifer specimen has
   no laboratory conductivity. The ADR-0012 table pairs 9.16e-6 m/s with
   d60 7.10 mm and 2.84e-5 m/s with d60 11.10 mm.
5. **Every one of the six in-scope ADR-0012 diagnostic pairs is embankment
   fill** (Table 4-3-1 holds all six laboratory conductivities). No aquifer
   specimen has a laboratory conductivity. Table 4-3-2's Ag conductivity
   column carries the in-situ field test beside the nearest specimen, and its
   "estimated k" column is a grain-size-derived estimate, so neither can serve
   as an independent pairing.
6. **The deep "framework" specimens are a mixture of strata.** Thesis B-6-2
   (KP 60.0, 85.3 % gravel, 2.00 to 3.00 m) is fill (Bg). Thesis B-9-1
   (KP 62.0) and 62.0-1 are fill (Bg). Thesis B-2-2 and B-4-2 are fill (Bc).
   Only thesis B-2-3, B-4-3, B-6-3 and B-9-2 are aquifer (Ag). The bulk
   co-primary values (5.5, 13, 1.3, 13.5 mm) are extrapolated from exactly
   these four Ag specimens, so the bulk reading does describe the aquifer.
7. **Table 4-3-2 holds 28 Ag gradations at the four modelled sections**
   (7 / 7 / 6 / 8 at KP 57.4 / 58.8 / 60.0 / 62.0) and 11 Ns gradations,
   against the 4 Ag specimens the thesis tabulates. Each carries gravel, sand,
   silt and clay fractions, maximum size, d60, d50, d30, d20, d10, Uc and Uc'.
   No full grading curve is in the PDF (the back matter is the survey forms
   and borehole logs), so a matrix gradation must be derived from these
   points.
8. **The aquifer top carries sand-rich material at two of the nine
   borings.** At KP 58.8 B-4 a 0.45 m sand unit lies directly beneath the
   blanket (D4-4: 0 % gravel, 89 % sand, d60 0.261 mm, Uc 4.5). At KP 62.0
   B-8 the first aquifer specimen below the gravel top is sand-dominated
   (D8-5: 36.7 % gravel, 53.3 % sand, d60 1.27 mm). At KP 60.0 B-6 a
   sand-dominated interbed occurs inside the gravel at 7 to 8 m (B6-2).

Aquifer-top depths read from the soil logs (scanned at 150 dpi, about
+/-0.1 m): B-1 3.70, B-2 3.50 (no separate silt), B-3 3.85, B-4 5.25 (sand)
/ 5.70 (gravel), B-5 5.50, B-6 4.50, B-7 3.00, B-8 4.80, B-9 2.65 m.

### 1.2 Pre-registered method (fixed before computing)

- **Gradation reconstruction.** For each specimen, the cumulative
  percent-passing curve is built from the tabulated points: (0.005 mm, clay),
  (0.075 mm, silt + clay), (d10, 10), (d20, 20), (d30, 30), (d50, 50),
  (d60, 60), (2.0 mm, 100 - gravel), (dmax, 100), and is interpolated
  linearly in percent passing against log size. Points that violate
  monotonicity are dropped and reported.
- **Matrix definitions.** Primary: **M2**, all material finer than 2 mm (the
  JGS sand-gravel boundary), renormalised to 100 %; the matrix d70 is the size
  at which the full curve passes 0.7 x P(2 mm). Alternatives: **S2**, the sand
  fraction 0.075 to 2 mm alone (fines excluded as non-erodible by a pipe tip,
  or washed out); **M4.75**, material finer than 4.75 mm (P(4.75 mm)
  interpolated). The gap is not a pre-registered boundary because the
  tabulated points cannot locate it; its position is discussed, not used.
- **Section statistic.** The median over the section's Ag specimens
  (primary); secondary, the pipe-horizon subset, the uppermost Ag specimen of
  each boring.
- **Agreement rule.** An adopted mean is reproduced if adopted / derived
  median lies within [1/1.34, 1.34], one sigma_ln (0.294) of the adopted
  prior. Above 1.34 the adopted value is coarser than the aquifer matrix
  (non-conservative for both branches); below 1/1.34 it is finer
  (conservative).
- **Consequence.** In-memory variant, `persist=False`, production configs
  otherwise untouched, same seed (common random numbers), N = 1e5, matrix
  reading, historical: d70 means replaced by the aquifer-derived M2 section
  medians. Reported: P_s, P_t, B and delta-beta at each section's
  design-level anchor, against the production baseline.

### 1.3 Predictions (stated before computing)

- **P1.** The M2 matrix d70 of the gravelly Ag specimens lies between 0.6 and
  1.5 mm, because P(2 mm) is 20 to 40 % and 0.7 of it falls between the
  tabulated d20 and d30 (0.4 to 1.8 mm).
- **P2.** The section medians are at or above the adopted means at all four
  sections, so the adopted means are conservative, and outside the band at
  KP 60.0 (adopted 0.26 mm from a silty fill specimen).
- **P3.** KP 62.0's aquifer-derived median lies inside the band around the
  transferred 0.70 mm: the transfer is not refuted.
- **P4.** Re-pairing the KP 58.8 conductivities leaves the pooled ADR-0012
  r-squared below 0.3 on both descriptors, so the diagnostic's outcome does
  not change, though its population (all fill) does.
- **P5.** A coarser d70 lowers P_s and P_t together; B moves by less than a
  factor 2 at the KP 62.0 anchor, much less than the k_aq bracket.

A prediction that fails is reported as failed in Part 2.

## Part 2: outcome

### 2.1 What is in the data, specimen by specimen

The full transcription (Tables 4-3-1 and 4-3-2, the four modelled sections,
every layer: 28 fill, 6 blanket, 28 aquifer, 12 lower-gravel specimens) is
`data/processed/oyo_1999_gradations_by_layer.csv`. The driver's consistency
checks flag three printing defects (D1-1 and D3-2 in fill, percentiles out of
order; the KP 57.4 shallow specimen's d10 printed 0.0019 in Table 4-3-1 and
0.019 on sheet 4, the latter reproducing its Uc) and two depth misprints
(D1-3, D9-2) corrected from the soil logs. None touches an aquifer d70. Sheet 4
at KP 62.0 prints the shallow specimen's particle density and water content
(2.666, 23.7 %) identical to KP 60.0's; Table 4-3-1 gives 2.685 and 12.9 %, so
sheet 4 carries a copy error there. It affects no modelled value.

Which specimens fed which prior, and what each distribution represents:

| Model quantity | Represents physically | Specimens behind it, before ADR-0054 | After ADR-0054 |
|---|---|---|---|
| matrix d70 mean | the eroding sand matrix at the pipe tip | three fill specimens (Bc, Bs, Bs), KP 62.0 borrowed | 28 Ag specimens, 6 to 8 per section |
| matrix d70 CoV 0.30 | place-to-place variability of that matrix along and across the section | none (judgment, "within-section grading") | measured: pooled within-section sigma_ln 0.293, CoV 0.300 |
| bulk d70 | the whole gravel, if the framework controlled entrainment | one Ag specimen per section, extrapolated from d60 | unchanged |
| k_aq | the transmissive gravel framework (seepage path) | OYO analysis constants (not specimens) | unchanged |
| ADR-0012 diagnostic | whether k and d co-vary as one soil | six fill specimens (all Table 4-3-1) | uninformative about the aquifer; decision stands on physics |
| gamma'_p (deterministic 16.87) | aquifer particle weight | 12 sheet-4 specimens, mostly fill | Ag mean G_s 2.725 gives 16.92 kN/m3: unaffected |

### 2.2 The adopted means against the aquifer matrix (the pre-registered test)

Matrix d70 (finer than 2 mm), per section over the Ag specimens:

| KP | n | median (mm) | range (mm) | sigma_ln | adopted | adopted / median | verdict |
|---|---|---|---|---|---|---|---|
| 57.4 | 7 | 0.90 | 0.71 to 1.05 | 0.12 | 0.70 | 0.78 | reproduced |
| 58.8 | 7 | 0.65 | 0.41 to 1.48 | 0.48 | 0.53 | 0.81 | reproduced |
| 60.0 | 6 | 0.74 | 0.42 to 0.88 | 0.27 | 0.26 | **0.35** | adopted 2.9x finer (conservative) |
| 62.0 | 8 | 0.75 | 0.60 to 1.11 | 0.19 | 0.70 (transfer) | 0.93 | reproduced; transfer corroborated |

Alternatives: sand-only matrix (0.075 to 2 mm) medians 1.05 / 0.80 / 0.93 /
0.93 mm; finer than 4.75 mm 1.92 / 1.69 / 1.32 / 1.81 mm. One interpolation
caveat: the one clean sand (D4-4, KP 58.8, 0 % gravel) has no tabulated point
between d60 and its 2 mm maximum, so its d70 is 0.43 mm by interpolation and
about 0.29 mm by extrapolating its d50-to-d60 slope; the section median does not
depend on that choice.

Across all 28 specimens the median is 0.77 mm, the between-section differences
are not significant (one-way ANOVA on ln d70, p = 0.31), ln d70 passes
Shapiro-Wilk (p = 0.23; untransformed p = 0.09), and the pooled within-section
sigma_ln is 0.293.

Prediction scoring. **P1 partly failed**: 25 of the 28 matrix d70 lie between
0.6 and 1.5 mm, but three gravels have finer matrices (0.41, 0.42, 0.46 mm),
because their passing-2-mm share falls between their d10 and d20. **P2 held**
(all four medians at or above the adopted means; outside the band only at
KP 60.0). **P3 held** (KP 62.0 ratio 0.93). **P4 held** (corrected r^2 0.02 and
0.08). **P5 held at three sections and failed at KP 60.0**: the in-memory
variant moved KP 60.0's design-level B from 2.92 to 6.37, beyond the factor of 2
predicted, and delta-beta from 1.87 to 1.22.

In-memory consequence (N = 1e5, production seed, each baseline bit-identical to
the persisted sweep; the `consequence` block of the JSON):

| KP | d70 mean (mm) | curve shift at P = 0.1 (static / transient) | design anchor | B | delta-beta |
|---|---|---|---|---|---|
| 57.4 | 0.70 to 0.90 | +0.12 / +0.12 m | 39.25 m | 0 transient failures either way | unresolved |
| 58.8 | 0.53 to 0.65 | +0.12 / +0.13 m | 41.00 m | 2.75 to 3.09 | 1.224 to 1.133 |
| 60.0 | 0.26 to 0.74 | +0.77 / +0.78 m | 42.75 m | 2.92 to 6.37 | 1.866 to 1.223 |
| 62.0 | 0.70 to 0.75 | +0.07 / +0.06 m | 46.50 m | 26.2 to 22.0 (15 and 13 rows) | 0.96 to 0.89 |

These in-memory arms kept the 1 mm clip; the production re-basing (ADR-0054)
uses 2 mm, so its numbers differ slightly and are the ones of record (section
2.6).

### 2.3 The explanation the thesis owes

- **Why a lognormal.** d70 is positive, grain sizes vary multiplicatively and
  are read on logarithmic sieve scales, the 28 aquifer matrix values are
  consistent with a lognormal (Shapiro-Wilk on ln d70, p = 0.23), and the family
  matches every other geotechnical input and Pol's reliability
  parameterisation.
- **What the CoV represents.** Place-to-place (aleatory, spatial) variability of
  the matrix d70 the pipe tip meets within a section: the scatter between the
  section's aquifer specimens. It is *not* the contrast between the matrix and
  the gravel framework, and not the uncertainty about which fraction governs.
  The 0.30 is now measured rather than judged: pooled within-section sigma_ln
  0.293. The thesis wording "within-section grading heterogeneity between the
  matrix and framework fractions" mixed the bimodality of each sieve curve into
  the spread of a unimodal distribution and is replaced.
- **Why not a bimodal (mixture) distribution for d70.** The bimodality is in
  each specimen's sieve curve (a gap-graded sand-gravel: whole-specimen d60 of
  4.8 to 25 mm in the gravels against a matrix d70 of 0.4 to 1.5 mm), not in the
  population of the operative quantity. The matrix d70 across the 28 specimens
  is unimodal. The genuinely two-valued question, whether the pipe tip is
  controlled by the matrix or by the whole gravel, is epistemic (which physics
  governs), not a location-to-location frequency. A mixture would need a
  weight no data supply and would hide the model question inside a
  probability, so it is carried as the two co-primary readings. The
  location-mixture case (sand at some locations, a gravel's matrix at others)
  does occur: D4-4 is a clean sand directly beneath the blanket at KP 58.8. It
  is represented by the matrix lognormal's lower tail rather than by a separate
  mode: D4-4's d70 (0.29 to 0.43 mm) lies 1.3 to 2.6 sigma_ln below KP 58.8's
  prior median, so 0.5 to 10 per cent of that section's draws are as fine.
- **What the choice cannot capture.** (1) A laterally continuous sand layer at
  the aquifer top (as at B-4) is a stratigraphic feature, not a random draw: it
  would change the seepage geometry and the conductivity contrast, which a
  single-aquifer schematisation does not represent. (2) Local covariation of
  matrix d70 and conductivity with gravel content is removed by the
  decoupling. (3) Whether the matrix can migrate through the framework's pore
  throats (internal stability, Green Light item 1) is not tested by any d70.
  (4) The matrix definition (fines in or out, 2 or 4.75 mm) moves the median by
  up to a factor of about 2; the finer-than-2 mm matrix is the finest, so the
  most conservative, of the three. (5) The matrix d70 is reconstructed from
  summary percentiles, not measured on a full curve.
- **KP 62.0.** No longer a transfer: its own eight aquifer specimens give
  0.75 mm, 7 per cent above the transferred 0.70 mm. The condition registered on
  every KP 62.0 result in Chapters 6, 7 and 9 is retired.

### 2.4 Hand-off to Green Light item 1 (uniformity and internal stability)

Per Ag specimen the JSON carries the whole-specimen Uc (printed), the M2 matrix
d10 / d60 / d70 / Cu, and the S2 (sand-only) matrix d10 / d60 / d70 / Cu.
Section medians: whole Uc 44 / 34 / 80 / 46; M2 matrix Cu 46 / 42 / 66 / 42
(dominated by the fines tail); S2 sand-matrix Cu 6.4 / 4.5 / 5.3 / 5.4. The
passing-2-mm share (the matrix fraction by mass) is 18 to 46 per cent in 24
specimens and 54 to 100 per cent in the four sand-rich ones (D7-4, D8-5, B6-2,
D4-4). Item 1 should use the Ag rows only; the fill rows describe the levee
body.

### 2.5 Other records corrected by this study

- ADR-0012 companion table: the KP 58.8 laboratory k was shifted one specimen
  too deep, and all six pairs are fill. Corrected with the superseded rows kept;
  re-paired r = -0.13 (d60) and +0.28 (d10). Decision unchanged; ADR-0012
  amended.
- Thesis `tab:app_grainsize` and `tab:app_lab_perm`: the same KP 58.8 shift, and
  every specimen labelled aquifer. Corrected in the thesis with a layer column.
- Provenance section 3.3, the per-section entries and section 8.8: marked
  superseded or resolved.


## Part 3: the production cascade under ADR-0054 (2026-09-25)

The owner's decision (re-base all four sections, raise the clip to 2 mm, keep
bulk, write to the main `results/` with the old tree archived) was executed as
a full production campaign. The superseded tree is
`results/superseded_d70rebase_20260924T163630/`; every study below was re-run
unchanged in method against the re-based production, and its committed JSON is
the re-based record. Each affected note carries a dated pointer to this Part.

### 3.1 What moved in the fragility (Phase 1)

| Quantity (matrix, historical, N = 1e5) | Superseded | Re-based |
|---|---|---|
| Design level (nearest grid level), static / transient, KP 57.4 (39.25 m) | 2.1e-3 / 0 | 5.1e-4 / 0 |
| KP 58.8 | 0.722 / 0.263 | 0.609 / 0.197 |
| KP 60.0 | 0.917 / 0.314 | 0.353 / 0.056 |
| KP 62.0 (46.50 m grid level) | 3.9e-3 / 1.5e-4 | 2.8e-3 / 1.3e-4 |
| B at the drained design levels | 2.75 / 2.92 | 3.09 / 6.34 |

KP 60.0 moves most (its matrix mean rose 2.8-fold, 0.26 to 0.74 mm) and its
transient curve shifts about 1.5 m to higher stages. The shape of every other
claim follows from that single fact.

### 3.2 What changed in kind, not only in value

1. **Phase 2 is informative at one stratum, not two.** KP 60.0 rejects 226
   realizations (0.23 %) and moves no mean by more than 0.4 %.
2. **KP 60.0 is the least likely of the four to fail in a year**, in both
   climates, as if undrained and on its berm; it was second.
3. **The KP 62.0 warming split tips to overflow's point estimate** (margin
   0.922, share 0.48 [0.46, 0.51]), still a statistical tie. The canonical
   alternate and the composition seam, which each used to reverse this cell,
   now only widen overflow's lead: no ordering anywhere depends on either.
4. **The conductivity bracket leaves no cell's ordering intact** under the
   conservative reading (it left one): the lowest arm now drives KP 60.0's
   historical piping to exactly zero, and the upward arm reverses KP 62.0 +4K.
5. **Severity leads frequency at KP 60.0** in the climate attribution, both
   inside the long stratum and over both strata (0.37 [0.29, 0.47]).
6. **The climate ratios are 15.3 / 5.8 / 13.4 / 13.4**; the pair the ensemble
   cannot separate is now KP 60.0 / KP 62.0.
7. **Only KP 58.8 exceeds 1e-3 per year** historically; the surface-only
   KP 62.2 ranks above KP 57.4 and KP 60.0 in the reach.
8. **The berm's effect on the index gap is no longer resolved** at either
   drained section (it was a resolved -0.016 and -0.058).

### 3.3 Diagnostics the cascade surfaced

- **Forward-Euler barrier jumps at KP 57.4** (the `c4b_not_c3b` class): 1 row
  at N = 1e5 (40.50 m) and 14 at 1e6 (39.75 to 41.0 m), at most 0.14 % of the
  transient failures at any level and none at an anchor. The campaign gates
  now apply a share rule (at most 1 % per level) to that one documented class
  (ADR-0040 amendment; `scripts/hwl_bias_resolution.py`,
  `tests/test_hwl_bias_resolution.py`).
- **One finite-hold straggler.** In the Stage 6.6 duration ladder at KP 62.0,
  46.50 m, alpha = -1/2, one realization of 1,517 satisfies the sustained-peak
  limit but has not breached after the longest hold, 1536 h. The limit is
  exact at the other five levels; the reverse disagreement count is still zero
  everywhere. It is a traverse slower than 64 days, not a disagreement.
- **GSA levels re-read.** The ADR-0033 levels are defined by target transient
  P_f read off each section's curve; the curves moved, so the levels were
  re-read at the grid points nearest the same targets (KP 58.8 40.25 / 41.00 /
  41.75 / 42.75 m; KP 60.0 42.50 / 42.75 / 44.25 / 45.50 m) and the ladder was
  raised one rung to 2^14, as ADR-0033 §3 permits at shoulder levels.
  **Outcome.** At 2^14 every interpreted index meets the 0.02 drift criterion
  except the transient indicator at KP 58.8's shoulder (40.25 m), whose total
  effects still drift 0.024 between 2^13 and 2^14 (first-order 0.012); those
  indices are read to one decimal only, which is how the thesis now quotes
  them. The static indicator at the two upper levels of each section is
  saturated (P_f 0.99) and, as before, not interpreted. Design-level transient
  rankings: KP 58.8 L 0.65, k_aq 0.59, C_e 0.32, d70 0.31 (C_e ahead of d70 and
  resolved), first-order sum 0.55; KP 60.0, whose design level now sits on the
  lower shoulder of its curve (P_f 0.056), k_aq 0.75, L 0.64, C_e 0.42 and d70
  0.42 tied, first-order sum 0.34. The seepage-length total effect on the
  transient indicator spans 0.49 to 0.81 across the eight levels. The bulk
  companion is unchanged (bulk not re-based); the two correlated companions,
  rerun at the design level, keep the ranking at P_f 0.17 against 0.199 under
  independence. The static margin is level-invariant as before (sum S 0.98).
- **Coverage and convergence levels at KP 60.0** were re-read the same way
  (43.75 / 42.75 / 42.00 / 41.75 m).
- **Two hard-coded pre-ADR-0054 anchors** in the equal-head and metric drivers
  (the 1696 / 1132 static counts and the 1696 / 63 anchor ratio) were re-read
  from the regenerated N = 1e6 ladder; the equal-head seed-recipe gate had
  refused to run on the stale constant, as it should.
- **Evidence left behind.** The committed Stage 6.6 copies
  (`adr0040-stage6-6-*.json`) and the ADR-0047 ratio record are hand-installed
  and were not rewritten by the campaign; both were refreshed here. The
  drained-configuration record's rerun was matrix-only and had dropped its two
  bulk blocks; they were restored from the committed file (bulk is unchanged).

### 3.4 The RQ1 comparison

Design anchors (`rq1-beta-reexpression.json`, `design_anchors`):

| Anchor | Superseded | Re-based |
|---|---|---|
| KP 62.0, 46.39 m, N = 1e6 | dbeta 0.90 [0.85, 0.97], B 26.9 | **dbeta 0.85 [0.79, 0.93], B 23.6 [18.6, 32.0]** (1,203 static / 51 transient) |
| KP 57.4, 39.21 m, N = 1e6 | dbeta >= 1.27, B >= 148 | **dbeta >= 0.88, B >= 37** (302 / 2); upper bound 1.63, point 1.18 withheld |
| KP 57.4 resolved anchor, 39.50 m | 1.27, B 42.7 | **1.20 [1.16, 1.24], B 51.2 [44.4, 60.2]** (163 transient) |
| KP 58.8 / KP 60.0 design, N = 1e5 | 1.22 / 1.87, B 2.75 / 2.92 | **1.13 / 1.22, B 3.09 / 6.34** |

- Resolved dbeta now spans **0.85 to 1.22** (was 0.9 to 1.9 where it
  resolved). The B ranking is 57.4 > 62.0 > 60.0 > 58.8 and the index ranking
  60.0 > 58.8 > 62.0 with KP 57.4 bounded between 0.88 and 1.63, so KP 62.0
  still falls from second to last, and the KP 57.4 bound no longer separates
  that section from either drained one. At the resolved anchors KP 57.4's 1.20
  and KP 60.0's 1.22 overlap, so "largest ratio and largest index at different
  sections" is no longer established.
- Stage stability at KP 62.0: 46.50 m gives B 21.6 [18.5, 25.9] on 130 and
  dbeta 0.88; the paired ratio of the two levels is 1.09 [0.89, 1.39], so the
  earlier "B resolvably smaller 11 cm higher" no longer holds. The 1e5 anchor
  reads B 31.0 and dbeta 0.92 on four rows.
- Composition, KP 62.0 design: head 0.35, gate 0.00, temporal 0.50. KP 57.4 at
  39.50 m: 0.80 / 0.06 / 0.34. Head share, first: 0.417 and 0.669 (index),
  78 and 100 % (probability, N = 1e5); last: 0.351 and 0.548; Shapley 0.384 and
  0.608.
- Severity: B decays x20 to x101 to 1.06 to 1.85 at the attainable tops;
  dbeta dips at most 0.26 and rises at most 0.73. Top-of-range survival:
  static 0.15 to 7.27 %, transient 5.6 to 49.9 %.
- Equal convention (ADR-0051 driver): B_eq 7.20 [6.30, 8.38] and dbeta_eq
  0.552 at KP 62.0; 1.97 / 0.776 at KP 58.8 and 3.30 / 0.866 at KP 60.0;
  KP 57.4 design 15.1 / 0.678 on 20 rows (below floor). Retained share 65 / 69 / 71 %
  at the three resolved design levels, 45 % at KP 57.4's resolved anchor.
  Reduced-vs-reduced: 6.86 (dbeta 0.50) at KP 62.0, 4.26 (0.40) at KP 57.4
  39.50 m. Seven gross-arm barrier jumps at KP 57.4 at 1e6.
- Epistemic arms at the KP 62.0 anchor: adequate arms B 2.66 to 25.8, band /
  statistical width 5.6 (46.39 m), 6.7 (46.50 m) and 4.9 (KP 57.4 39.50 m),
  so F3 reads 4.9 to 6.7x (was 6.4 to 7.2x); it still does not fire at KP 62.0
  and still fires at KP 57.4 (field-test k_aq: static failures, no transient).
  dbeta over the resolved arms 0.83 to 0.93.
- Metric study: m_p quotable rho 1.09 to 1.25 against index 0.13 to 0.19;
  l_c rho 1.10 to 1.37 against index at most 0.10; m_p disagrees between
  metrics at 2 to 5 quotable levels per section, l_c at none. Pairing variance
  reduction 1.04 to 1.60 on dbeta, 1.03 to 1.32 on log B; paired SE 0.0017 to
  0.0349, 0.035 at the KP 62.0 anchor.
- Conductivity non-cancellation: maximum resolved departures 67 / 56 / 72 / 46
  (were 82 / 66 / 163 / 46); normalised 0.98 to 1.59 decades per k_aq decade,
  above one in eleven of the twelve section-and-arm pairs (the KP 62.0
  regional-upper arm is 0.975). The "exceeds 1.0 everywhere" finding of the
  2026-07-30 synthesis therefore no longer holds without that exception.
- Stage 6.6 physics ladder at KP 62.0: exponent step -2.19 / -1.72 / -1.23
  index (probability -0.37 / -0.45 / -0.51); one-branch -0.75 on 124 static /
  1,147 transient failures; symmetric 1.29 at design (1.29 to 1.49 over the
  range), KP 57.4 symmetric 1.14 to 2.11. Path dependence of the head step:
  0.063 first / 0.032 second at KP 62.0 48.00 m (interaction 0.031); 0.163 /
  0.072 at KP 57.4 40.50 m (0.091).
- Initiation gate against transient, design grid levels: 3.96 (KP 58.8) and
  4.85 (KP 60.0), three and a half to four times the steady-state shift; the
  gate probability reaches 0.999 between 0.55 and 2.72 m below the transient
  median. The gate is d70-invariant (identical probabilities before and after).

### 3.5 Thesis carry-through

Thesis commits `3c35fc0` (item 4 text) and the reconciliation commit that
follows it carry every number above into Chapters 1 and 3 to 9, the Summary and
Appendices B, E, H, I and K, with the 50 regenerated figures. A whole-document
sweep compared every numeric token removed from the result chapters against the
current text.
