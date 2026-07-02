# 0021: Per-section landside toe elevations (MSL / T.P.)

* **Date:** 2026-07-02
* **Status:** Accepted (values carry a +/-0.3 m reading uncertainty; see Caveats)
* **Scope:** Confined Tokachi right-bank cross-sections KP 57.4, 58.8, 60.0, 62.0
* **Supersedes:** the placeholder use of the foreshore crest level as the exit
elevation `h\_e` (flagged below for the engineer to action)

## Decision

The landside-toe ground-surface elevation (the natural hinterland ground level at
the landside toe, i.e. the seepage exit elevation), read from the OYO (1999)
transverse soil sections (様式-3, scale 1:200) and referenced to Tokyo Peil (T.P.,
mean sea level), is adopted per section as:

|KP|Landside toe elevation (T.P., m)|Uncertainty|
|-|-|-|
|57.4|38.3|+/-0.3 m|
|58.8|38.5|+/-0.3 m|
|60.0|40.0|+/-0.3 m|
|62.0|44.9|+/-0.3 m|

These values are on the same vertical datum (T.P./MSL) as the attached bank-height
CSV data; the datum consistency was verified via the HWL cross-check below.

## Context and purpose

The initiation limit states (uplift, heave) and the piping exit are evaluated at
the **landside toe**, where the confined aquifer overpressure is released at the
natural ground surface. The model therefore needs the landside-toe ground elevation on MSL to serve a dual role: as both the head-translation datum `z\_toe` and the exit / polder reference `h\_e`. The thesis text currently takes the
exit elevation as the *foreshore crest level* (a riverside quantity, Table
`tab:oyo\_inventory`); that is a conservative placeholder, not the physical landside
exit level. This record establishes the physically correct landside values and
cross-checks them against the independent 2019 bank-height survey.

## Method

1. **Primary source (OYO 様式-3).** For each section the transverse soil section
was rendered at high DPI and the natural hinterland ground surface (the top of
the gravel-hatched foundation, landward of the levee toe) was read against the
sheet's own elevation axis (T.P. gridlines at 50.0 / 40.0 / 30.0 / 20.0 m). The
pixel scale (\~106 px/m, consistent across all four same-template sheets) was set
from the axis endpoints (EL 50.0 top, EL 20.0 bottom) and confirmed against the
labelled landside-borehole collar elevations.
2. **Landside borehole anchor.** The landside borehole (the rightmost of the three;
river/foreshore is on the left in every sheet) provides a precisely labelled
collar elevation that anchors the datum. The natural toe sits \~2 to 2.5 m below
each collar (the borehole is collared on the levee berm, not on natural ground).
3. **Cross-check (bank-height CSVs).** Datum consistency and physical plausibility
were checked against `BankHeight\_TokachiRiv\_2019.csv` (HWL and design crest, MSL)
and `BankHeight\_AveSig\_Tokachi.csv` (per-200 m segment average/sigma).

## Results with provenance

|KP|Landside borehole (collar T.P.)|Toe ground read (T.P.)|Basis on 様式-3|
|-|-|-|-|
|57.4|B-2  (+40.81)|38.3|natural ground \~1.5 to 1.8 m below the 40.0 gridline|
|58.8|B-4  (+42.82)|38.5|natural ground \~1.4 to 1.5 m below the 40.0 gridline|
|60.0|B-6  (+43.61)|40.0|toe meets natural ground essentially at the 40.0 gridline|
|62.0|B-9  (+46.55)|44.9|natural ground \~5 m below the 50.0 gridline; consistent with the mapped Ac at \~EL 45 (see DR on D\_bl)|

Internal consistency: the toe elevation decreases monotonically downstream
(62.0 -> 60.0 -> 58.8 -> 57.4: 44.9 -> 40.0 -> 38.5 -> 38.3), giving a longitudinal
ground gradient of \~6.6 m over the 4.6 km from KP 62.0 to KP 57.4 (\~1/700), which is
physically reasonable for this high-gradient reach.

## Cross-check against the bank-height MSL data

**Datum (the key check).** The OYO 1998 HWL sits a *consistent* \~0.30 m above the
2019 design HWL at every section, which confirms the two datasets share the same
T.P./MSL datum (a datum shift would be inconsistent or much larger; everything else
aligns). The \~0.30 m is a design-HWL revision between 1998 and 2019, not a datum
difference, and it does **not** apply to the physical ground/toe elevations.

|KP|OYO 1998 HWL|2019 CSV HWL|Diff|2019 design crest (R)|Toe below HWL|Crest above toe|
|-|-|-|-|-|-|-|
|57.4|39.51|39.21|+0.30|40.71|1.2 m|2.4 m|
|58.8|41.33|41.03|+0.30|42.53|2.8 m|4.0 m|
|60.0|43.06|42.75|+0.31|44.25|3.1 m|4.2 m|
|62.0|46.68|46.39|+0.29|47.89|1.8 m|3.0 m|

Every section satisfies toe < HWL < design crest, and the levee stands 2.4 to 4.2 m
above the landside toe, all physically consistent.

**Secondary (AveSig file).** `BankHeight\_AveSig\_Tokachi.csv` gives a per-200 m
segment `Average` of \~1.62 / 1.85 / 0.86 / 0.75 m at KP 57.4 / 58.8 / 60.0 / 62.0
with `Sig` its spatial std. These read as a freeboard-like crest-above-HWL height
(design freeboard is 1.50 m in the 2019 file) and broadly corroborate the crest-HWL
relationship, but the file carries **heights/differences, not MSL elevations**, so
it is not used as a datum reference. Two incidental notes: KP 60.0 and 62.0 show
sub-design average freeboard (\~0.75 to 0.86 m), and KP 58.8 has an anomalously large
`Sig` (\~1.31, vs \~0.005 elsewhere) indicating a highly non-uniform crest in that
segment (near the Kinohara sluice transition). These concern the crest, not the toe,
and are logged only for the overtopping/length-effect work.

## Uncertainty and caveats

* **Reading precision +/-0.3 m.** Source is a 1:200 scanned drawing; the natural
ground line is read against printed gridlines. This is adequate for `h\_e` but
should not be quoted to better than 0.1 m.
* **Toe vs collar.** The tabulated toe is the *natural ground* at the landside toe,
\~2 to 2.5 m below the landside borehole collar. Do not substitute the collar
elevation for `h\_e`.
* **KP 62.0 (governing section).** Toe \~44.9 m is consistent with the corrected thin
Ac blanket mapped at \~EL 45 (see the D\_bl decision record). Because this section
drives the reach-level result, confirm the toe against the post-remediation
current cross-section (development bureau) if/when obtained, together with the
remediation-state check already flagged for KP 62.0.
* **Borehole-order note.** In each 様式-3 the river/foreshore is on the left, so the
landside borehole is the last-listed (B-2 / B-4 / B-6 / B-9). The appendix table
`tab:app\_borehole\_summary` parenthetically labels the order "landside / crest /
riverside", which is reversed relative to the sheets; the elevations are correct,
only the side-label ordering in that note should be checked.

## Downstream use / recommendation

1. Adopt the four toe elevations as both the head-translation datum `z\_toe` and the exit / polder reference `h\_e` for uplift, heave, and the piping exit, replacing the foreshore-crest placeholder. Lowering `h\_e` to the true (lower) landside toe increases the head available at the exit and is the physically correct, less-conservative-in-the-right-direction choice; re-run the affected sections after the change.
2. Keep the OYO ground/toe elevations as-is (T.P.); do **not** apply the 0.30 m HWL
offset to them. Apply the 0.30 m only if mixing 1998 and 2019 *HWL/crest* design
values in the same computation, and document which design HWL vintage is used.
3. Carry the +/-0.3 m as a minor geometric uncertainty; it is small relative to the
D\_bl and d70 uncertainties and need not be made stochastic.
4. **Hydrograph trough baseline:** For the G1 canonical hydrograph shapes, ensure that the base-flow MSL stage (derived via Eq. 4.19 based on 75.44 m³/s per section) is used as the trough baseline. Do not mistakenly use the landside toe elevation as the hydrograph recession floor.

## Sources

* OYO (1999), 平成10年度 十勝川中流部堤防強化対策検討業務 報告書（調査・解析編）:
様式-3 堤防横断方向土質調査結果図 for KP 57.4, 58.8, 60.0, 62.0 (files R057\_400.pdf,
R058\_800.pdf, R060\_000.pdf, R062\_000.pdf, sheet 1 of each), scale 1:200, datum T.P.
* `BankHeight\_TokachiRiv\_2019.csv` (River, KP, HWL, DesignBankHeight\_L/R; MSL).
* `BankHeight\_AveSig\_Tokachi.csv` (per-200 m segment Average/Sig; heights).
