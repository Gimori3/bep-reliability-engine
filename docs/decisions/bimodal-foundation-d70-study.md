# Study: the bimodal foundation, the operative d70 and the distribution chosen for it

Date: 2026-09-24 (Green Light item 4)
Status: Part 1 (pre-registration) committed before any matrix d70 was computed.
Part 2 records the outcome.

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
