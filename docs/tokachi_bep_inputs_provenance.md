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
| `D_bl_m` | thickness table | none | A_c thickness at landside toe; KP 62.0 corrected to 0.45 m (0.3 to 0.6 m), see 3.8 |
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
| 62.0 | KP 61.0 to 62.8, revetment, no mapped 側帯 | unreinforced | OPEN: memo marks this reach "berm-uncertain"; see below |
| 63.4 | beyond urban works | unreinforced | anomalous, unconfined; section may be excluded |

Open sub-item, KP 62.0. The memo labels the KP 61.0 to 62.8 reach "unreinforced /
berm-uncertain": revetment is present but no side-berm (側帯) is mapped, so the landside
state cannot be pinned to berm-only vs unreinforced from the available sheets. The CSV
carries `unreinforced` as the best estimate because it is the value the memo lists first
and because it is the conservative choice for BEP (a credited berm would add seepage
length and lower the failure probability). Confirm from the current-state cross-section
before relying on it. This matters because KP 62.0 is the governing piping section
(narrowest foreshore, 1998 i_v = 0.97).

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

### 3.4 CONFIRMED: `gamma_sub_kNm3`

The engineer has confirmed this column is the particle submerged unit weight of the
aquifer sand, gamma'_s = (G_s - 1) x gamma_w, which is the quantity consumed by F_r, and
that per-section values are wanted (not a single basin-wide constant). The definitional
question raised in the prior revision is therefore closed.

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

### 3.8 KP 62.0 RESOLVED; KP 57.4/58.8/60.0 pending: blanket thickness `D_bl_m` vs the OYO geological-section A_c thickness

Cross-referencing the L memo against the thesis thickness table surfaced a material
disagreement on the A_c blanket thickness, which is the `D_bl_m` column. The two documents
differ by roughly a factor of 2 to 3:

| KP | `D_bl_m` in CSV (thesis thickness table) | A_c thickness in the L memo (sections 3 and 4) | Ratio |
|------|------------------------------------------|------------------------------------------------|-------|
| 57.4 | 2.5 | about 0.8 | about 3 |
| 58.8 | 2.0 | about 0.85 | about 2.4 |
| 60.0 | 1.6 | 0.85 to 1.35 | about 1.2 to 1.9 |
| 62.0 | 0.45 (corrected from 2.0) | 0.3 to 0.6 (図4-1-4 legend, report p.37) | about 1 |
| 63.4 | 1.0 (nominal, A_c absent) | none | n/a |

Status after review of the latest Chapter 3 (file
`3__Study_Area__Geological_Setting__and_Data.tex`):

INTERNAL CONSISTENCY: RESOLVED. The latest chapter integrates the seepage-length memo as a
new subsection (Definition and Determination of the Seepage Length) but does not import the
memo's thin A_c figures. It continues to carry `D_bl` = 2.5 / 2.0 / 1.6 / 2.0 / 1.0 m in
both the thickness table (`tab:strat_thickness`) and the prior-means table (mu_ln of 0.903,
0.679, 0.456, 0.679, -0.014), and it describes the blanket only as "thin relative to the
aquifer it overlies (Table strat_thickness)". The conservative no-hinterland-credit
argument is rested on lateral continuity being unverified, plus the B-4 gravel-dominated
landside specimen at KP 58.8 as evidence of a possibly breached blanket, not on absolute
thinness. A reader of Chapter 3 alone therefore sees one consistent set of A_c thicknesses;
the clashing pair no longer appears inside the thesis.

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

OTHER SECTIONS: NOT YET VERIFIED. KP 57.4 (2.5 vs ~0.8), 58.8 (2.0 vs ~0.85), and 60.0
(1.6 vs 0.85 to 1.35) still carry the thick thickness-table values. Their thin readings come
from the same OYO geological-section legends (図4-1-1/-1-2/-1-3) that proved authoritative at
KP 62.0, so the same over-thickening very likely applies to all three and should be verified
identically (read each section's 図4-1-X 地質凡例 Ac row and cross-check the landside borehole)
before the first fragility run. The teeth are unchanged: D_bl feeds the uplift limit state and
heave gradient directly, both scaling inversely with blanket thickness, so any uncorrected
over-thickness biases initiation toward false safety. The continuity-based L argument is
unaffected (it does not depend on absolute thickness).

CSV STATUS: the CSV KP 62.0 row is corrected to D_bl_m = 0.45; rows 57.4/58.8/60.0 are left at
the thickness-table values pending the verification above. The CSV is therefore aligned with
the chapter for KP 62.0 and flagged as provisional for the other three confined sections.

---

## 4. Per-cross-section detail

### KP 57.40
- `L_m` 33: L memo, 様式-5 dimension chain (32.92 m, adopted 33). State `berm-only`, so the
  current under-levee path is longer than this 1998 value; the tabulated L is a
  conservative lower bound.
- `D_aq_m` 7, `D_bl_m` 2.5: thickness table. D_bl conflicts with L memo A_c about 0.8 m
  (3.8).
- `k_aq_mps` 3.0e-3, `k_bl_mps` 1.6e-6: Form 5, cm/s divided by 100.
- `d70_m` 7.0e-4: matrix, from B-2-1 (d_60 = 0.635 mm). Bulk co-primary 5.5 mm.
- `gamma_sub_kNm3` 16.84: from B-2-1/2/3 G_s.
- `foreshore_width_m` 200. `remediation_state` berm-only (Fukuda type ⑥).

### KP 58.80
- `L_m` 35: L memo, 様式-5/7 base. State `drained`, so the model sets exit head to zero and
  BEP is near zero regardless of L; L is a placeholder here.
- `D_aq_m` 8, `D_bl_m` 2.0: thickness table. D_bl conflicts with L memo A_c about 0.85 m
  (3.8).
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
- `D_aq_m` 9, `D_bl_m` 1.6: thickness table. D_bl vs L memo A_c 0.85 to 1.35 m is the
  closest agreement of the five, but still flagged (3.8).
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
- `foreshore_width_m` 44 (narrowest). `remediation_state` unreinforced (OPEN: memo marks
  the reach berm-uncertain; 3.2).

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

Open items requiring the engineer's action:

- `D_bl_m` discrepancy: internal consistency resolved in the latest Chapter 3 (it carries
  2.0 to 2.5 m throughout and omits the memo's thin figures), but the underlying A_c
  thickness vs the L memo (0.3 to 1.4 m) is not reconciled and still feeds uplift and heave,
  non-conservative if the larger values are wrong. CSV matches the chapter. Resolve the
  absolute thickness against 様式-3 and 様式-5 before the first fragility run (3.8). Most
  important open item; worst at the governing section KP 62.0.
- KP 62.0 `remediation_state`: berm-uncertain; confirm berm-only vs unreinforced from the
  current-state cross-section. Governing section (3.2).
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
