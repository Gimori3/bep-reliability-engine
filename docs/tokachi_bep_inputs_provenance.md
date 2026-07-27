# Provenance and Flags: Tokachi BEP Geotechnical Input Table

Companion document to `tokachi_bep_inputs.csv`. It records, for every cell in the table,
where the value came from (which OYO form, which borehole), every unit conversion applied,
every stratigraphic judgment call left open, every resolved inconsistency, and every
remaining data gap. It is the defensible audit trail for supervisors and committee.

Sources: OYO Corporation (1999) levee-strengthening investigation, Tokachi River right
bank KP 56.0 to 66.2, transcribed into the thesis Study Area chapter and the Geotechnical
Dataset appendix; Fukuda current-state and remediation documentation
(`fukuda_2025_internal`); and the engineer's seepage-length determination memo
(`Seepage_Length_L_Final_Determination.md`).

Reference convention: `Form 5` is the OYO 様式-5 specified soil constants (thesis Table
`tab:form5` / appendix `tab:app_form5`); `grain-size table` is Table `tab:grainsize` /
`tab:app_grainsize`; `thickness table` is Table `tab:strat_thickness`; `inventory` is
Table `tab:oyo_inventory`; `L memo` is the seepage-length determination file.

Revision note: this version incorporates the engineer's resolutions to the field-
permeability and HWL inconsistencies, the seepage-length determination, the remediation-
state allocation, the confirmation of the gamma definition, and the NaN convention for
k_bl at KP 63.4. It also raises one new open inconsistency (section 3.8).

---

## 1. Cross-section inventory

| Row | KP | River | Bank | Boreholes (landside toe / crest / riverside) | A_g sample series |
|-----|------|---------|-------|-----------------------------------------------|-------------------|
| 1 | 57.40 | Tokachi | right | B-1, H8-B-3, B-2 | B-2-1, B-2-2, B-2-3 |
| 2 | 58.80 | Tokachi | right | B-3, H8-B-4, B-4 | B-4-1, B-4-2, B-4-3 |
| 3 | 60.00 | Tokachi | right | B-5, H8-B-5, B-6 | B-6-1, B-6-2, B-6-3 |
| 4 | 62.00 | Tokachi | right | B-7, B-8, B-9 | 62.0-1, B-9-1, B-9-2 |
| 5 | 63.40 | Tokachi | right | NO-1, NO-2, NO-3 (lab series B-2, B-3) | B-2-2, B-2-6, B-3-2, B-3-4 |

Count: 5 cross-sections, all Tokachi right bank, KP 57.40 to 63.40, within the OYO survey
strip KP 56.0 to 66.2.

### Scope note (whole-reach)

No borehole or laboratory data exist in the provided sources for lower Tokachi right bank
KP 53.8 to 56.0, or for any of Satsunai left bank KP 3.2 to 16.6. No rows were created for
these reaches; they are handled by the inflated-uncertainty interpolation rule in the
methodology, which is a modeling step, not data transcription.

---

## 2. Column-by-column sourcing and conversions

| Column | Source | Conversion | Notes |
|--------|--------|------------|-------|
| `kp` | OYO evaluation station | none | |
| `river` | study-reach definition | none | Tokachi all rows |
| `bank` | OYO survey side | none | right all rows |
| `L_m` | L memo, sections 3 and 6 | none (already m) | under-levee confined-path convention; pre-remediation 1998 geometry; see 3.1 |
| `D_aq_m` | thickness table | none | combined A_g + N_s to K_1p base |
| `k_aq_mps` | Form 5, A_g layer | cm/s to m/s, divide by 100 | analysis constants, not field/lab |
| `d70_m` | derived, not measured | mm to m, x 1e-3 | matrix-fraction interpretation; see 3.3 |
| `D_bl_m` | thickness table, corrected against OYO 図4-1-X legends | none | A_c thickness at landside toe; all four confined sections corrected to the mapped competent A_c (57.4 = 0.80, 58.8 = 0.85, 60.0 = 0.85, 62.0 = 0.45 m), see 3.8 |
| `k_bl_mps` | Form 5, A_c layer | cm/s to m/s, divide by 100 | NaN at KP 63.4 (A_c absent); see 3.4 note and 4 |
| `gamma_sub_kNm3` | grain-size table rho_s | (G_s - 1) x 9.81 | per-section particle submerged weight; confirmed; see 3.4 |
| `foreshore_width_m` | inventory | none | KP 63.4 "river-tight" encoded 0; see 3.5 |
| `remediation_state` | Fukuda landside-type map | none | KP allocation; see 3.2 |

Unit conversions applied silently in the CSV values:

1. Conductivity (`k_aq_mps`, `k_bl_mps`): OYO cm/s divided by 100 to m/s.
2. Grain size (`d70_m`): matrix d_70 in mm multiplied by 1e-3 to m.
3. Submerged unit weight (`gamma_sub_kNm3`): from dimensionless G_s as (G_s - 1) x gamma_w,
   gamma_w = 9.81 kN/m3.

No conversion was needed for `L_m`, `D_aq_m`, `D_bl_m`, or `foreshore_width_m` (already in
metres).

---

## 3. Flags, resolutions, and open items

### 3.1 RESOLVED: seepage length `L_m`

Source: the seepage-length determination memo. L is defined as the under-levee confined
seepage path from riverside toe to landside toe. The foreland (foreshore) and hinterland
are carried separately as leakage zones through the response factor r_e, not inside L;
folding the foreshore into L would double-count the foreland resistance already in r_e.
The landside boundary is set at the toe with no credit for unverified hinterland blanket
continuity, which is conservative for progression (Z = L - l_e(t), so shorter L is
conservative).

| KP | L_m (CSV) | Basis | Confidence (base-width) |
|------|-----------|-------|--------------------------|
| 57.4 | 33 | 様式-5 dimension chain 11.09 + 7.50 + 2.82 + 4.50 + 7.01 = 32.92 m | medium-high |
| 58.8 | 35 | 様式-5 model span and 様式-7 base, 31 to 40 m, adopt 35 | medium |
| 60.0 | 34.8 | 様式-6 footprint 10.0 + 9.5 + 4.0 + 2.5 + 8.8 = 34.8 m; gradient cross-check | medium-high |
| 62.0 | 47 | toe-to-toe incl. landside berm, 18 + 29.1 m; range 40 to 55 | medium |
| 63.4 | 26.9 | FORCED PROXY only; unconfined, mechanism mismatch; see below and 4 | mechanism N/A |

Caveats carried with these values:

- All values are 1998 pre-remediation geometry. They interact with `remediation_state`
  (3.2): for `berm-only` nodes the current under-levee path is longer (memo estimates
  order +10 to +30 m, to be confirmed from current cross-sections), so the tabulated L
  for KP 57.4 is a conservative lower bound, not the current geometry. For `drained`
  nodes (KP 58.8, 60.0) the model sets the exit head to zero and BEP probability is near
  zero regardless of L, so the tabulated L there is effectively a placeholder. For the
  `unreinforced` node KP 62.0 the 1998 value stands.
- KP 63.4 L = 26.9 m is the memo's "if a single number is unavoidable" geometric proxy
  (11.0 m foreshore + 15.9 m base, cross-checked by H/D back-calc), carried only so the
  row parses. The memo recommends excluding KP 63.4 from the confined-BEP population
  entirely (unconfined, A_c absent). Replace with NaN or drop the row once the KP 63.4
  decision is finalised.
- These are explicit engineering-judgement estimates, not surveyed values of L. The memo
  recommends a modest per-section lognormal (CoV 0.15 at KP 60.0, 0.20 elsewhere) and a
  one-sided upward sensitivity case; those belong to the CoV and sensitivity layers of
  the model, not to this mean-value table.

Standing data gap that would refine L: the along-levee soil profile (土層縦断図, OYO
appendix, about report p.247) directly maps the lateral blanket boundaries and was not
available. Obtaining it plus the post-remediation cross-sections (via Obihiro Kaiken /
Fukuda-san) would let the landside boundary be verified and the priors tightened. The
analysis does not depend on it: the under-levee convention is a conservative lower bound.

### 3.2 RESOLVED: `remediation_state`

Source: Fukuda landside cross-section type map and longitudinal sheet (縦断図), with state
defined by the landside treatment, not the riverside (the riverside is near-continuously
revetted, 高水護岸, KP 56.8 to 62.0). KP allocation anchored to posts and bridges
(平原大橋 about KP 60.5 to 61, 伏古樋門 about KP 61.5 to 62, 中島橋 about KP 63).

| KP | Fukuda reach and type | State (CSV) | Note |
|------|------------------------|-------------|------|
| 57.4 | KP 56.0 to 58.0, type ⑥ (側帯盛土 only) | berm-only | toe-bounded 1998 L is a conservative lower bound; current L larger (3.1) |
| 58.8 | KP 58.0 to 61.0, types ④ + ⑤ (berm + ドレン材 toe-drain) | drained | exit head set to zero in model; BEP near-zero; L moot |
| 60.0 | KP 58.0 to 61.0, types ④ + ⑤ | drained | same as 58.8 |
| 62.0 | KP 61.0 to 62.8, revetment, no mapped 側帯 | unreinforced | CLOSED 2026-07-22 on three independent lines; see below |
| 63.4 | beyond urban works | unreinforced | anomalous, unconfined; section may be excluded |

CLOSED sub-item, KP 62.0 (2026-07-22). The memo had labelled the KP 61.0 to 62.8 reach
"unreinforced / berm-uncertain": revetment is present but no side-berm (側帯) is mapped, so
the landside state could not be pinned to berm-only vs unreinforced from the type map
alone. `unreinforced` was carried as the conservative best estimate. It is now positively
confirmed on three independent lines, and the CSV value is unchanged:

1. The 1998 OYO evaluation section for KP 62.0 (様式-5, 十勝川右岸 62.0 km) models a plain
   trapezoidal levee and leaves the 浸透対策工 row blank: no landside berm was credited
   even at the time of the deficiency rating.
2. GSI DEM5A (5 m airborne lidar) cross-section profiles at about ten chainages within the
   segment show a consistent unbermed geometry at every station: crest about 3 to 4 m above
   landside ground, uniform landside slope about 1:3, a toe channel about 1 m below the
   adjacent surface, level ground beyond, no intermediate bench. Ground-level imagery along
   the crest agrees.
3. The 側帯 annotated near KP 62 on the 1996 様式-2 plan sheet (built 平成 3 to 4) is a
   第二種側帯. Under 河川管理施設等構造令施行規則 第14条 that class is for stockpiling
   emergency earth, with length limited to roughly the volume of a 10 m length of levee;
   it is the 第一種側帯 that is sited at 漏水箇所 (leakage locations) for embankment
   stability. So the annotated feature is a short local stockpile pad, not a seepage
   countermeasure — reconciling the plan-sheet marking with items 1 and 2.

Residual: a buried landside toe drain cannot be excluded from remote elevation data; a
functioning drain would only lower the computed failure probability. This mattered because
KP 62.0 is the governing piping section (narrowest foreshore, 1998 i_v = 0.97).

Consequence worth noting for interpretation: the drained treatment at KP 58.8 and KP 60.0
drives their modelled BEP probability to near zero, so two of the five OYO sections are
effectively removed from the active piping population by remediation, while the governing
section (KP 62.0) is the one whose remediation state is least certain. Toe drains exist
only on the Tokachi right bank (type ⑤); the Satsunai types carry berms but no drains
(not in scope here).

### 3.3 JUDGMENT (engineer-approved): representative grain size `d70_m`

d_70 is reported on no specimen; only d_60, d_50, d_20, d_10 are tabulated. The CSV
carries the matrix-fraction interpretation, approved by the engineer: d_70 taken from the
fine sand matrix of the shallow blanket-aquifer transition samples, extrapolated up the
grading curve from the matrix d_60, placing values inside or adjacent to the Sellmeijer
validated range (mean 0.208 mm, validated to about 0.430 mm). The bulk-gravel co-primary
alternative is retained below because H_c scales as roughly d_70^0.4 and the choice
propagates into the fragility curves.

| KP | CSV value (matrix, m) | matrix basis | bulk-gravel co-primary (mm) |
|------|------------------------|--------------|------------------------------|
| 57.4 | 7.0e-4 | B-2-1 d_60 = 0.635 mm, extrapolated | 5.5 |
| 58.8 | 5.3e-4 | B-4-1 d_60 = 0.459 mm, extrapolated | 13 |
| 60.0 | 2.6e-4 | B-6-1 d_60 = 0.228 mm, extrapolated (inside validated range) | 1.3 |
| 62.0 | 7.0e-4 | by analogy, no clean matrix sample at this KP | 13.5 |
| 63.4 | 7.0e-4 | by analogy | 9.5 |

KP 62.0 and KP 63.4 d_70 are assigned by analogy: their shallowest specimens are gravelly
(62.0-1 d_60 = 7.87 mm, B-9-1 d_60 = 3.46 mm), so no section-specific sand-matrix sample
exists. This remains a judgment item even though the interpretation is approved.

### 3.4 CONFIRMED: `gamma_sub_kNm3` (audit-trail only; the engine uses 16.87 basin-wide)

This column is the particle submerged unit weight of the aquifer sand,
gamma'_p = (G_s - 1) x gamma_w, the quantity consumed by the Sellmeijer resistance
factor F_r. **Canonical-value decision (review item #10): the engine uses the basin-wide
deterministic gamma'_p = 16.87 kN/m3** (the pinned constant
`sellmeijer.GAMMA_P_SUB_DEFAULT`), consistent with the thesis Methodology, which fixes
gamma'_p as a single deterministic basin-wide value. The per-section column below is
therefore **recorded for the audit trail only and is not threaded into the engine**:
`scripts/generate_configs.py` does not read it (it has no config field, ADR-0016), and
the per-section spread (16.49 to 16.85) is < 2 % from the 16.87 basin-wide mean, so the
simplification is numerically negligible. (An earlier revision noted "per-section values
are wanted"; that is superseded by the basin-wide decision here. If per-section gamma'_p
is ever required, it would be threaded via the same M8 -> M6 channel as the other
deterministic Sellmeijer inputs, review item #6.) Do not confuse gamma'_p with the
distinct stochastic *blanket* weight gamma'_bl (6.9 kN/m3, CoV 0.056) that drives the
uplift and heave limit states and is carried in the theta vector.

| KP | A_g specimens averaged | mean G_s | gamma'_s = (G_s - 1) x 9.81 |
|------|------------------------|----------|------------------------------|
| 57.4 | B-2-1, B-2-2, B-2-3 | 2.716 | 16.84 |
| 58.8 | B-4-1, B-4-2, B-4-3 | 2.681 | 16.49 |
| 60.0 | B-6-1, B-6-2, B-6-3 | 2.705 | 16.72 |
| 62.0 | 62.0-1, B-9-1, B-9-2 | 2.712 | 16.80 |
| 63.4 | B-2-2, B-2-6, B-3-2, B-3-4 | 2.717 | 16.85 |

For reference, the thesis quotes a basin-wide deterministic mean of 16.87 kN/m3 (n = 12,
CoV about 1.6 percent); the per-section spread is only 16.49 to 16.85, so the per-section
choice is numerically minor.

Mineralogical caveat (unchanged, physical limitation, strongest at KP 62.0 and KP 63.4):
these G_s values are from the coarse gravel framework. Under the matrix-controlled erosion
interpretation the governing grain is the sand matrix, which may contain pumiceous or
vesicular volcanic-glass particles with effective G_s well below 2.65. If so the true
matrix gamma'_s could be 25 to 55 percent lower, lowering predicted H_c proportionally.
Resolving this needs matrix-fraction petrography at the thin-blanket governing sections.

k_bl NaN convention: at KP 63.4 the A_c blanket is absent, so blanket conductivity is
physically undefined. The cell is written as the literal `NaN` (engineer request) so the
Python pipeline distinguishes "undefined / not applicable" from an empty missing value.

### 3.5 JUDGMENT: KP 63.4 `foreshore_width_m` encoded as 0

The inventory records the KP 63.4 foreshore as "river-tight" (levee fronts the river
directly, effective width about 0 m), documented rather than missing, so it is encoded as
a best estimate of 0. A zero foreshore transmits near-full river head to the foundation.
Adjust to a small nominal positive value if your convention requires one. Note this is
consistent with the memo's treatment of KP 63.4 as unconfined.

### 3.6 RESOLVED: field-permeability factor-of-100 discrepancy

The engineer has verified both chapters against the OYO source forms and confirmed the
main-text Chapter 3 field-permeability values are correct and the appendix values are the
erroneous ones (the cm/s to m/s division by 100 was not applied to the pump-out and
recovery rows in the appendix). Correct field permeabilities (m/s):

| KP | Borehole | Method | Correct field k_s (m/s) |
|------|----------|--------|--------------------------|
| 57.4 | B-2 | injection | 5.09e-5 |
| 58.8 | B-4 | injection | 2.23e-6 |
| 60.0 | B-6 | pump-out | 1.24e-4 |
| 62.0 | B-9 | pump-out | 7.04e-5 |
| 63.4 | B-2 | recovery | 4.22e-3 (outlier) |
| 63.4 | B-3 | recovery | 6.25e-5 |

Action item outside this table: correct the appendix field-permeability table in the
thesis. No impact on the CSV, since `k_aq_mps` is anchored to the Form 5 analysis
constants, not the field tests.

### 3.7 RESOLVED: KP 63.4 HWL inconsistency

The engineer has confirmed the appendix HWL of 46.68 m for KP 63.4 is wrong: it is a
carry-over from the KP 62.0 row. It is incompatible with the KP 63.4 ground elevations
(+48.46 to +51.09 m), its initial water level (45.97 m), and its 52.4 m.h waveform area
and 0.20 m/h recession. The defensible figure is the main text's approximately 49.0 m
(the section's own flood peak), consistent with how HWL equals the design-event peak for
the other four sections. HWL is not a CSV column; recorded for the audit trail and as an
appendix correction item.

### 3.8 RESOLVED (all four confined sections): blanket thickness `D_bl_m` vs the OYO geological-section A_c thickness

Cross-referencing the L memo against the thesis thickness table surfaced a material
disagreement on the A_c blanket thickness, which is the `D_bl_m` column. The two documents
differ by roughly a factor of 2 to 3:

| KP | `D_bl_m` in CSV (thesis thickness table) | A_c thickness in the L memo (sections 3 and 4) | Ratio |
|------|------------------------------------------|------------------------------------------------|-------|
| 57.4 | 0.80 (corrected from 2.5) | 0.8 (図4-1-1 legend, report p.34) | about 1 |
| 58.8 | 0.85 (corrected from 2.0) | 0.85 (図4-1-2 legend, report p.35) | about 1 |
| 60.0 | 0.85 (corrected from 1.6) | 0.85 to 1.35, landside 0.85 (図4-1-3 legend, report p.36) | about 1 |
| 62.0 | 0.45 (corrected from 2.0) | 0.3 to 0.6 (図4-1-4 legend, report p.37) | about 1 |
| 63.4 | 1.0 (nominal, A_c absent) | none | n/a |

Status after review of the latest Chapter 3 (file
`3__Study_Area__Geological_Setting__and_Data.tex`):

INTERNAL CONSISTENCY: RESOLVED. The chapter now carries the corrected mapped A_c thicknesses throughout: `D_bl` = 0.80 / 0.85 / 0.85 / 0.45 / 1.0 m in both the thickness table (`tab:strat_thickness`) and the prior-means table, with mu_ln of -0.237, -0.176, -0.176, -0.812, -0.014 in `tab:priors_muln`. The thickness-table Notes and the "Two sections define the extremes of blanket-controlled vulnerability" paragraph have been rewritten so the thickest/thinnest ordering matches the corrected values (thinnest 62.0 at 0.45 m; thickest 58.8 and 60.0 at about 0.85 m; 57.4 at 0.80 m), and KP 57.4's 1998 gradient pass is now attributed to its 200 m foreshore alone rather than to a thick blanket. The conservative no-hinterland-credit L argument is unaffected (it never depended on absolute thickness). A reader of Chapter 3 alone now sees one consistent, mapped-thin set of A_c thicknesses.

RESOLUTION (KP 62.0). The governing section is resolved. The A_c blanket thickness at
KP 62.0 is 0.3 to 0.6 m, stated verbatim in the OYO geological cross-section 図4-1-4
(地質横断図, 十勝川右岸 KP62.0), 地質凡例 Ac row, 記事 column ("標高45m付近に層厚 0.3〜0.6m
程度で薄く分布する"), bound report PDF p.37 (printed p.32, scale 1:200). It is corroborated by
borehole B-9 (the landside toe) in 様式-4 (R062_000.pdf p.2): every B-9 sample classifies as
gravel-with-fines [GF]/[G-F], with clean A_g gravel only by 5 to 6 m depth, so there is no
2 m clay blanket at the exit. The earlier 2.0 m was the 様式-5 lumped computational layer
(R062_000.pdf p.3, layer 2, parameters assigned "他と比較 N=3", i.e. by analogy, not measured
here), which equals the cover-to-aquifer depth (B-9 surface EL+46.55 to A_g top EL+43.9 is
about 2.6 m), not the mapped competent aquitard. D_bl(62.0) is corrected to mean 0.45 m
(midpoint of 0.3 to 0.6); with the existing CoV = 0.167 the lognormal +/-2 sigma interval is
0.30 to 0.60 m, matching the mapped range, so the CoV is unchanged and mu_ln becomes -0.812.

RESOLUTION (KP 57.4, 58.8, 60.0). The three remaining confined sections are now resolved by the same method as KP 62.0, reading each section's OYO geological cross-section 地質凡例 Ac-row 記事 column directly. KP 57.4: A_c is "堤体下面に層厚 0.8m 程度で分布する" (homogeneous silt, about 0.8 m, N=3) in 図4-1-1 (地質横断図, 十勝川右岸 KP57.4), report PDF p.34 (printed p.29, 1:200); D_bl corrected to 0.80 m. KP 58.8: A_c is "層厚は0.85mで" (sandy silt, 0.85 m, N=5) in 図4-1-2, report PDF p.35 (printed p.30); D_bl corrected to 0.85 m. KP 60.0: A_c is "層厚は0.85〜1.35mで堤外側で厚くなる" (sandy silt, 0.85 to 1.35 m, thickening toward the riverside, N=5 to 6) in 図4-1-3, report PDF p.36 (printed p.31); because the layer thickens riverside, the landside-toe value governs D_bl, corrected to 0.85 m (not the 1.35 m maximum). Each is corroborated by its landside-toe borehole in 様式-4, all of which return sand/gravel-with-fines and no competent clay at the A_c elevation: B-2 (57.4) <SfG>/<GF>/[G-F]; B-4 (58.8) <Sfg>/<GF>/[G-F]; B-6 (60.0) <SF>/(GW clean gravel)/<Sfg>, the same gravelly signature as B-9 at KP 62.0. As at KP 62.0 the old thick figures match neither the legend nor the 様式-5 lumped cohesive layer; here, however, the 様式-5 layer is itself thin (measured about 0.6 to 1.0 m at 57.4, 1.0 to 1.5 m at 58.8, 0.75 m at 60.0, i.e. already consistent with the mapped A_c), so unlike at KP 62.0 the 様式-5 layer is NOT the source of the over-thickening; the inflated 2.5 / 2.0 / 1.6 m most nearly match the cover-to-aquifer depth at the landside borehole, not the competent aquitard. With CoV held at 0.167, mu_ln becomes -0.237 (57.4), -0.176 (58.8), -0.176 (60.0). The teeth are unchanged: D_bl feeds the uplift limit state and heave gradient directly, both scaling inversely with blanket thickness, so the prior over-thickness was biasing initiation toward false safety; the corrected thin values remove that bias. The continuity-based L argument is unaffected (it never depended on absolute thickness).

CSV STATUS: all four confined-section rows are now corrected to the mapped A_c thickness: D_bl_m = 0.80 (57.4), 0.85 (58.8), 0.85 (60.0), 0.45 (62.0). KP 63.4 remains at the nominal 1.0 m (A_c absent, excluded from the confined population). The CSV is fully aligned with the corrected chapter; no confined section remains provisional.

---

## 4. Per-cross-section detail

### KP 57.40
- `L_m` 33: L memo, 様式-5 dimension chain (32.92 m, adopted 33). State `berm-only`, so the
  current under-levee path is longer than this 1998 value; the tabulated L is a
  conservative lower bound.
- `D_aq_m` 7, `D_bl_m` 0.80 (corrected): A_c thickness about 0.8 m, read from the OYO
  geological cross-section 図4-1-1 legend (report PDF p.34, "堤体下面に層厚 0.8m 程度で分布する",
  homogeneous silt, N=3) and corroborated by landside-toe borehole B-2 in 様式-4 (shallow
  samples sand/gravel-with-fines, no clay). The earlier 2.5 m matched neither the legend nor
  the 様式-5 lumped cohesive layer (about 0.6 to 1.0 m); resolved (3.8).- `k_aq_mps` 3.0e-3, `k_bl_mps` 1.6e-6: Form 5, cm/s divided by 100.
- `d70_m` 7.0e-4: matrix, from B-2-1 (d_60 = 0.635 mm). Bulk co-primary 5.5 mm.
- `gamma_sub_kNm3` 16.84: from B-2-1/2/3 G_s.
- `foreshore_width_m` 200. `remediation_state` berm-only (Fukuda type ⑥).

### KP 58.80
- `L_m` 35: L memo, 様式-5/7 base. State `drained`, so the model sets exit head to zero and
  BEP is near zero regardless of L; L is a placeholder here.
- `D_aq_m` 8, `D_bl_m` 0.85 (corrected): A_c thickness 0.85 m, read from the OYO geological
  cross-section 図4-1-2 legend (report PDF p.35, "層厚は0.85mで", sandy silt, N=5) and
  corroborated by landside-toe borehole B-4 in 様式-4 (shallow samples gravel-with-fines, no
  clay). The earlier 2.0 m matched neither the legend nor the 様式-5 lumped cohesive layer
  (about 1.0 to 1.5 m); resolved (3.8).
- `k_aq_mps` 2.0e-3, `k_bl_mps` 1.0e-6: Form 5.
- `d70_m` 5.3e-4: matrix, from B-4-1 (d_60 = 0.459 mm). Bulk co-primary 13 mm.
- `gamma_sub_kNm3` 16.49 (lowest, B-4-1 G_s = 2.645).
- `foreshore_width_m` 325. `remediation_state` drained (Fukuda types ④ + ⑤).
- Note: L memo flags B-4 landside lab data showing 53 percent gravel where A_c should sit,
  i.e. the landside blanket may be thin or breached. Relevant to both the D_bl conflict
  (3.8) and the no-hinterland-credit L convention.

### KP 60.00
- `L_m` 34.8: L memo, 様式-6 footprint (best-constrained, with an independent exit-gradient
  consistency check). State `drained`; L is a placeholder as for 58.8.
- `D_aq_m` 9, `D_bl_m` 0.85 (corrected): A_c thickness 0.85 to 1.35 m, thickening toward the
  riverside ("層厚は0.85〜1.35mで堤外側で厚くなる"), read from the OYO geological cross-section
  図4-1-3 legend (report PDF p.36, sandy silt, N=5 to 6); the landside-toe value governs D_bl,
  so 0.85 m (not the 1.35 m riverside maximum). Corroborated by landside-toe borehole B-6 in
  様式-4 (shallow sample sand-with-fines over clean gravel, no clay). The earlier 1.6 m
  exceeded even the riverside maximum; resolved (3.8).
- `k_aq_mps` 1.0e-3, `k_bl_mps` 1.0e-6: Form 5.
- `d70_m` 2.6e-4: matrix, from B-6-1 (d_60 = 0.228 mm), only section squarely inside the
  Sellmeijer validated range. Bulk co-primary 1.3 mm.
- `gamma_sub_kNm3` 16.72. `foreshore_width_m` 600. `remediation_state` drained.

### KP 62.00 (governing piping section)
- `L_m` 47: L memo, toe-to-toe including landside berm (range 40 to 55). Failure mode in
  表6-3-1 is explicitly 基盤漏水によるパイピング (foundation-seepage piping). State
  `unreinforced` but see open sub-item.
- `D_aq_m` 10, `D_bl_m` 0.45 (corrected): A_c thickness 0.3 to 0.6 m, read directly from the
  OYO geological cross-section 図4-1-4 legend (report p.37) and corroborated by B-9 (様式-4:
  all samples gravel-with-fines, no clay). The earlier 2.0 m was the 様式-5 lumped layer /
  cover-to-aquifer depth, not the mapped blanket. Governing section; resolved (3.8).
- `k_aq_mps` 1.0e-3, `k_bl_mps` 3.0e-6: Form 5.
- `d70_m` 7.0e-4: assigned by analogy (no clean matrix sample; shallow specimens gravelly).
  Bulk co-primary 13.5 mm.
- `gamma_sub_kNm3` 16.80; pumiceous-matrix caveat strongest here and at 63.4.
- `foreshore_width_m` 44 (narrowest). `remediation_state` unreinforced (CONFIRMED
  2026-07-22 on three independent lines; 3.2).

### KP 63.40 (structurally anomalous, unconfined; engineer may exclude)
- `L_m` 26.9: FORCED PROXY only (11.0 m foreshore + 15.9 m base). The L memo recommends
  excluding this section from the confined-BEP population; the proxy is carried only so the
  row parses. Replace with NaN or drop on finalising the 63.4 decision.
- `D_aq_m` 11: thickness table, single gravelly foundation unit.
- `D_bl_m` 1.0: NOMINAL; A_c effectively absent. Both the thesis and the L memo agree there
  is no real confining blanket here, so the D_bl conflict of 3.8 does not apply to this row.
- `k_bl_mps` NaN: undefined, no A_c (engineer convention).
- `k_aq_mps` 6.0e-5: Form 5, single unit, about 1.5 orders below the others.
- `d70_m` 7.0e-4: by analogy. Bulk co-primary 9.5 mm.
- `gamma_sub_kNm3` 16.85; pumiceous caveat applies. `foreshore_width_m` 0 (river-tight).
  `remediation_state` unreinforced (beyond urban works).
- Additional anomalies on file: Shikaribetsu-referenced loading (not Obihiro), shorter
  design event, distinct borehole naming, recovery-method field permeability flagged as an
  outlier (4.22e-3), the now-resolved HWL carry-over (3.7), and the 様式-3 legend showing no
  A_c. The 1998 analysis treated it as through-embankment seepage and slope stability, the
  opposite pattern from the confined sections.

---

## 5. Status checklist

Resolved in this revision:

- `L_m`: determined for all confined sections (57.4, 58.8, 60.0, 62.0) from the seepage-
  length memo; KP 63.4 carries a flagged forced proxy (3.1).
- `remediation_state`: allocated for all five from the Fukuda landside-type map (3.2).
- `gamma_sub_kNm3`: definition confirmed (particle, per-section) (3.4).
- `k_bl_mps` at KP 63.4: written as literal NaN per engineer convention (3.4).
- `d70_m`: matrix interpretation approved (3.3).
- Field-permeability factor-100: resolved (main text correct, appendix wrong) (3.6).
- KP 63.4 HWL: resolved (appendix carry-over from KP 62.0; about 49.0 m correct) (3.7).
- `D_bl_m`: all four confined sections corrected to the mapped competent A_c from the OYO
  図4-1-X legends with landside-borehole corroboration (57.4 = 0.80, 58.8 = 0.85,
  60.0 = 0.85, 62.0 = 0.45 m); KP 63.4 nominal 1.0 m (A_c absent). mu_ln = -0.237 / -0.176 /
  -0.176 / -0.812 / -0.014 at CoV 0.167 (3.8).

Open items requiring the engineer's action:

- `L_m` post-remediation adjustment: berm-only KP 57.4 needs the larger current under-levee
  path (order +10 to +30 m) once current cross-sections are obtained; 1998 value is a
  conservative lower bound (3.1).
- KP 63.4: decide whether to retain or exclude; if excluded, NaN or drop the row (replacing
  the 26.9 proxy) (3.1, 4).
- Pumiceous-matrix petrography at KP 62.0 and KP 63.4 to confirm gamma'_s (3.4); physical
  limitation, not a transcription gap.

Standing data gap (does not block the analysis):

- The along-levee soil profile 土層縦断図 plus post-remediation cross-sections would verify
  the landside L boundary, the D_bl reconciliation, and the KP 62.0 berm question. Obtain
  via Obihiro Kaiken / Fukuda-san (3.1).

Thesis-document corrections (outside this table):

- Appendix field-permeability table (3.6) and appendix KP 63.4 HWL (3.7).

---

## 6. External corroboration added 2026-07-27 (Tokachi basin document review)

*(Numbered 6 to resolve a duplicate-heading collision with section 4,
"Per-cross-section detail"; cross-references elsewhere to "section 4.x" that
mean an item below should be read as 6.x.)*

Sources: `docs/tokachi_basin_document_review_2026-07-27.md`. The reference PDFs
live in gitignored `docs/references/tokachi_river_basin/`.

### 6.1 `remediation_state` — provenance chain now dated

The column was previously sourced only to the Fukuda landside-type map (3.2)
with no institutional chronology. The following is now on record:

| Date | Event |
|---|---|
| 2002-07 | 河川堤防設計指針 (River Levee Design Guidelines) issued |
| 2002-02 | 河川堤防の構造検討の手引き (JICE structural examination manual) |
| 2004 | 河川堤防質的整備技術ガイドライン（案） (quality-improvement guideline) |
| FY2003–2007 | Tokachi seepage countermeasures **initiated** on the basis of the seepage-resistance verification results |
| 2004 | Earthquake review finds large-section + drain effective for *both* seismic and seepage; Obihiro implements drain works |
| 2008-03 | Levee detailed-inspection maps published |

Source: 続十勝川治水史 (2023), PDF pp. 122, 241, 279.
Also relevant: side-berm fill at 北帯広築堤 (Tokachi right bank, Obihiro) was
executed 1999–2003 (ibid., PDF pp. 272–273) — reconcile against the
`remediation_state` label for the Obihiro-adjacent sections if it is ever
revisited.

### 6.2 Official 2008 seepage-safety classification of the study reaches

The Obihiro Development and Construction Department's levee detailed-inspection
result information maps (March 2008 status) classify managed reaches into three
seepage-safety classes. **All reaches containing the five cross-sections in this
CSV are classified 浸透による堤防の安全性が確保されている区間 — "seepage
safety secured"** (confirmed by the user reading the maps directly, 2026-07-27).

This is **not** in conflict with the 1998 OYO deficiency ratings: 1998
unremediated deficiency → 1999–2003 works → 2008 secured. The engine evaluates
the **unremediated** foundation, so the computed fragility and the 2008
classification describe different configurations of the same sections. Do not
present engine fragility at the drained sections as present-day reliability.

Programme context (ibid.): of the 398.2 km of levee in the Obihiro jurisdiction
targeted for detailed inspection, 359.8 km (90%) had been inspected by end
FY2007, of which **66.7 km (19%) fell below the seepage safety standard**.

### 6.3 Countermeasure → engine-quantity mapping

Japanese design guidance (河川堤防の浸透に対する照査・設計のポイント, PWRI
2014, printed p. 33 Table 7.1.1) states which physical quantity each
countermeasure acts upon. This makes the `remediation_state`-is-a-label caveat
tractable rather than merely acknowledged:

| Countermeasure | Physical effect | Engine handle |
|---|---|---|
| 断面拡大 section enlargement | lengthen seepage path | `geometry.L` |
| ドレーン工 landside-toe drain | reduce exit gradient at the toe | M5 uplift/heave gate |
| ブランケット工 foreland blanket | reduce foundation inflow + toe pressure | foreland credit → `r_e` (ADR-0025 `blanketed_tanh`) |
| 川表遮水工 riverside cutoff | lengthen path; reduce toe pressure | `geometry.L`, but **only if penetration ≥ 90% of `D_aq`** |
| 堤内基盤排水工 landside drainage | reduce uplift on blanket base | `Z_uplift` term |

Any remediation sensitivity built on this must be **opt-in, default-OFF and
bit-identical at baseline**, with `None` dropped from `Config.to_metadata()` so
the Phase 2 replay hash gate keeps passing (see `bep-change-control`).

**Construction-record note supporting the ADR-0025 baseline.** The FY1977–79
foundation-leakage works on the Otofuke–Kino levees installed sheet walls into
the sand-gravel foundation as a cutoff; the method was judged **inappropriate
for continuous cutoff in sand-gravel** and was replaced in FY1980 by a **soil
blanket on the high-water bed** (続十勝川治水史, PDF p. 280). Consistent with
PWRI 2014 printed pp. 47–48 (cutoff needs ≥90% penetration; coarse gravel
deforms sheet piles). The remediation actually adopted in this reach is
therefore a foreland blanket — the ADR-0025 `blanketed_tanh` baseline is
supported by the construction record, not only by evidence weighting.

### 6.4 Regional corroboration of `D_aq` and `k_aq` — and a prior-tail concern

The Chiyoda new-channel groundwater investigation (続十勝川治水史, PDF p. 359)
characterises the floodplain aquifer at **KP 37.6** as sand-gravel of
**15–20 m thickness** with **k = 10⁻¹ to 10⁰ cm/s = 1e-3 to 1e-2 m/s**, and a
hinterland water table 2–4 m below ground surface.

Comparison with this CSV (a different geomorphic setting ~20 km downstream, so
corroboration only — **no prior in the engine is derived from it**):

| | CSV | Chiyoda |
|---|---|---|
| `D_aq_m` | 7–11 | 15–20 |
| `k_aq_mps` | 6e-5 – 3.0e-3 | 1e-3 – 1e-2 |

**Open concern.** With mean `k_aq` = 3.0e-3 and CoV 0.50, the lognormal 95th
percentile is ≈ 5.8e-3 m/s, so the upper end of the measured band lies **beyond
the prior's upper tail**. Because H_c ∝ k_aq^(-1/3) and the progression rate
rises with k_aq, a prior that under-represents the upper tail is unconservative
in the adverse direction. PWRI 2014 (printed p. 20) separately characterises
ordinary measured permeability scatter as a factor of several to ~10, against
the factor ≈2.9 that CoV 0.50 spans. Recommended follow-up: a **bounding
scenario** at the upper measured conductivity in the ADR-0046 companion pattern
— a scenario, **not** a change of prior, and not a CSV edit (the
`tests/test_configs.py` drift guard pins the CSV to ADR-0012/0023).

The same source records that the Chiyoda weir drives a **bypass seepage
circulation** (river recharges hinterland upstream of the weir, hinterland
drains to river downstream). The hinterland head is therefore not necessarily a
passive far-field constant — a qualification on the M4 semi-infinite Mazure
schematisation (ADR-0006).

### 6.5 Corroboration of `gamma_sub_kNm3` dispersion

PWRI 2014 (printed p. 20) characterises ordinary measured soil density scatter
as ≈ ±0.1 g/cm³, which on a total unit weight near 2.0 g/cm³ is ≈5% and so
corroborates the thesis prior CoV(γ'_bl) = 0.056 closely.

---

## 7. External corroboration added 2026-07-28 (full-volume 続十勝川治水史 review)

Source: `docs/tokachi_chisuishi_full_review_2026-07-27.md`, the exhaustive
816-page pass over 続十勝川治水史 (2023) that supersedes the partial reading
recorded in section 4. Page citations are **PDF pages** of
`docs/references/tokachi_river_basin/inr9av000000b2i3.pdf` with the printed page
in parentheses. The PDF is gitignored and machine-local.

**No value in `tokachi_bep_inputs.csv` was changed by this review.** Section 5.1
verifies existing engine data against the official source; 5.2–5.4 add facts the
audit trail did not previously carry.

### 7.1 VERIFIED: the design HWL profile, the T.P. ↔ m MSL datum, and the crest rule

`geometry.HWL` in every generated config is the official 2019 design
high-water-level table (`data/raw/geometry/BankHeight_*Riv_2019.csv`, ADR-0018),
read by `bep_reliability_engine.bank_heights.load_hwl` in **m MSL**. The Japanese
sources state elevations in **T.P. (Tokyo Peil)**. The equivalence is now
established numerically rather than assumed:

| Check | Engine value | 続十勝川治水史 | Agreement |
|---|---|---|---|
| Design HWL at 基準地点帯広, KP 56.6 | 38.140 m MSL | **38.14 m T.P.** (p199 printed 179; p171 printed 151) | exact |
| Design HWL at 河口, KP 2.4 | 5.10 m MSL | **5.10 m T.P.** (p199) | exact |
| `DesignBankHeight` − `HWL`, upper Tokachi | **+1.50 m** at KP 56.6/57.4/58.8/60.0/62.0 | 堤防高 = 計画高水位 + **1.5 m** for the upper Tokachi (p150 printed 130) | exact |
| `DesignBankHeight` − `HWL`, lower Tokachi | **+2.00 m** at KP 2.4 | + **2.0 m** for the reach mouth → Sarubetsu confluence (p150) | exact |

Consequences worth recording:

1. **The datum question is closed.** T.P. and the engine's `m MSL` are the same
   datum at this reach, verified at two independent chainages plus two
   independent freeboard constants. Given this project's history with external
   data (the ≈105.6× scour-model conversion, the rating-error placeholder), this
   is checked rather than asserted.
2. **The engine is pinned to the in-force plan revision.** 38.14 m first appears
   in the 河川整備基本方針 of 2007-03 (p171) and is **retained unchanged** by the
   2022-09 revision (p199), which states explicitly that raising 計画高水位 would
   increase disaster potential and is to be avoided. The 2019 bank-height table
   reproduces that profile.
3. **The apparent 0.42 m spread across revisions is not a spread.** The four
   values in circulation are two revisions × two chainages:

   | | 基準地点, KP 56.6 | 帯広 gauge, KP 56.7 |
   |---|---|---|
   | 工事実施基本計画 (1966, 1983; 1988 changed crest width only) | 38.44 (p150, p158) | 38.56 (p73, 1981 chapter) |
   | 河川整備基本方針 (2007, retained 2022) | **38.14** (p171, p199) | **38.26** (p87, 2016 chapter) |

   Interpolating the engine's own profile between KP 56.6 (38.140) and KP 56.8
   (38.390) gives **38.265 m at the gauge chainage KP 56.7** — the 38.26 m the
   2016 flood chapter tabulates, to 5 mm. *(That the difference is a chainage
   offset is an inference; the values and the profile reproducing them are
   measured.)*
4. **The KP 62.0 design crest of 47.89 m MSL** used in the thesis is
   46.39 + 1.50, i.e. the official upper-Tokachi freeboard rule applied to the
   official design HWL.

### 7.2 NEW: buried sluice conduits at two of the four study cross-sections

The 樋門・樋管一覧表 (指定区間外区間, 帯広河川事務所, 令和4年3月末現在), p642
(printed 614), read from a rendered page image at 8× to confirm the 左右岸
column:

| 築堤 | 距離標 | Bank | 樋門 | 断面 W×H×L ~ barrels |
|---|---|---|---|---|
| 北帯広築堤 | **57.3** | **right** | 木賊原樋門 | 6.0 × 3.0 × 27.0 ~ 2 |
| 然別築堤 | 60.1 | left | 然別樋門 | 2.5 × 1.8 × 37.0 ~ 1 |
| 北帯広築堤 | **61.7** | **right** | 伏古樋門 | 2.0 × 2.0 × 28.0 ~ 1 |
| 西士狩築堤 | **62.0** | **right** | 西士狩樋門 | 1.5 × 2.0 × 28.0 ~ 1 |
| 西帯広築堤 | 64.7 | right | 西帯広樋門 | 1.5 × 1.5 × 22.0 ~ 1 |
| 西帯広築堤 | 65.3 | right | 西帯広第2樋門 | 1.5 × 2.0 × 26.0 ~ 1 |

All five study cross-sections are Tokachi **right bank**. Two coincide with a
sluice:

- **KP 62.0** — the governing piping section (narrowest foreshore 44 m, 1998 OYO
  exit gradient i_v = 0.97, `remediation_state: unreinforced`, failure mode
  named in OYO 表6-3-1 as 基盤漏水によるパイピング) — has a sluice at **exactly
  that chainage**, 28 m conduit.
- **KP 57.4** has a sluice 0.1 km away at KP 57.3 — a 27 m **two-barrel**
  6.0 × 3.0 m conduit, much the largest in the reach.

Conduit lengths (27–28 m) are the same order as the modelled under-levee seepage
lengths (`L_m` = 33 at KP 57.4, 47 at KP 62.0).

**Status: a documented scope limitation, not a data conflict and not a value
change.** The engine models foundation BEP beneath a plain trapezoidal levee
(M4–M7). A buried culvert is a separate, separately-recognised pathway
(preferential flow along the conduit, a discontinuity in the blanket, void
formation around the barrel); Japanese doctrine treats 樋門周辺の空洞化 as its
own inspection and design item. Nothing computed is invalidated; the model set
simply does not contain the feature, at two of four sections, one of which
governs.

Note that section 3.2 above already cites 伏古樋門 — but only as a **KP landmark**
for allocating `remediation_state` from the Fukuda longitudinal sheet, never as a
physical feature of the cross-section. That gap is closed here.

### 7.3 QUALIFIED: `remediation_state` — the toe drains have three documented drivers

Section 4.1 dated the institutional chronology behind this column. The
full-volume pass adds a qualification the `drained` label does not carry: the
toe-drain programme in this basin has **three distinct documented rationales**,
deployed in different reaches.

| Driver | Evidence | Reach |
|---|---|---|
| **Seepage** | p279 (printed 257): after the 2002 手引き and 2004 質的整備 guideline, 浸透に対する安全性の照査 was performed and 裏のり尻ドレーン工法 etc. implemented where required | the verification-driven works; Fukuda types ④+⑤ at KP 58.0–61.0, i.e. the CSV's `drained` rows |
| **Seismic (L2)** | p122 (printed 102), 2004 review: 大断面化（丘陵堤）＋ドレーン工 is effective "地震対策としてのみならず、浸透対策としても有効"; Obihiro deployed drains **in the liquefaction-prone lower Tokachi**. p423 (printed 401): 法尻ドレーン basin-wide under the 2007/2012 耐震性能照査指針. Round-table p709: the engineer who ordered them describes the rationale as purely seismic (perched lens liquefaction in enlarged sections) | lower Tokachi |
| **Construction-stage** | pp128/130 (printed 108/110), 2003 earthquake restoration: 裏のり尻ドレーン工 for 湧水処理, toe protection and trafficability during rapid refill | earthquake-damaged sites |

The current allocation is undisturbed — the study sections' drains are the
seepage-driven works. What changes is the confidence statement: **a `drained`
label identifies a physical feature, not a design intent.** That matters if the
label is ever converted into physics (the standing opt-in remediation
sensitivity, section 4.3 above), because a seismically-motivated drain need not
have been sized against the seepage exit gradient.

Related, same source: p122 records that 1993-damaged sites repaired with 基盤処理
and full re-excavation (統内, 東稲穂) took almost no 2003 earthquake damage,
whereas the partially re-excavated 幌岡 was damaged over nearly its full length —
sourced evidence that remediation *depth* governs recurrence.

### 7.4 NEW: gauge geometry around the study reach

From the 水位観測所一覧表 (p613 printed 585, 令和4年4月現在) and its location map
(p614), both read from rendered images:

- **There is no water-level gauge on the Tokachi main stem between 帯広
  (KP 56.7) and 芽室太 (KP 71.1).** The study sections KP 57.4–63.4 contain none;
  the nearest is Obihiro, 0.7–6.7 km downstream. This is the sourced
  justification for the structure of the M3 rating chain and quantifies its
  extrapolation distance.
- 帯広: KP 56.7, catchment 2,677.8 km², continuous record from 明40.1 =
  **January 1907**.
- **国見橋 is on the 然別川 at KP 0.6**, not on the Tokachi — relevant to the
  KP 63.4 row, whose section 4 notes record "Shikaribetsu-referenced loading
  (not Obihiro)".
- Satsunai: 竜潭上流 56.4, 上札内 41.8, 第2大川橋 20.7, 南帯橋 15.0, **札内 4.0**.
  Confirms from the official inventory the standing engine-side item that the
  札内 gauge sits *inside* the Phase 3 Satsunai reach while the rating chain uses
  Nantai, 8–11 km upstream.

Two further items supporting existing decisions:

- **p581 (printed 553)** lists 洪水痕跡調査 (flood-trace survey) among the
  standard, required 河川カルテ data items. The ADR-0035 anchoring of the 2016
  peak to a surveyed flood trace therefore rests on a routine statutory survey
  product, not an ad hoc measurement.
- **The Phase 2 loading is verified at its head.** The replay's Obihiro-datum
  2016 input peak is **38.07 m MSL**, identical to the official published T10
  peak at p87 (printed 67); the same committed record reproduces Memurobuto
  64.79, Chiyoda 18.74 and Moiwa 12.68 exactly. This verifies the *input* stage
  only, not the section-rating and trace-anchoring steps downstream of it.
