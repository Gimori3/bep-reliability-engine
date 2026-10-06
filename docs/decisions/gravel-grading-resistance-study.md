# Study: sand-based models in a gap-graded gravel, grading, and what extra resistance would change (Pol comments 4 and 5)

Date: 2026-10-06 (Pol feedback, session 2 of 6)
Status: Part 1 (sources and pre-registration) written and committed before any
arm was computed. Part 2 records the outcome.

Evidence: `gravel-grading-resistance-study.json`, driver
`scripts/gravel_grading_resistance_study.py`, gate
`tests/test_gravel_grading_resistance_study.py`. Run artifacts: gitignored
`results/gravel_grading/`. Comparator of record: ADR-0055 (same head and same
gate; `time-dependence-factor-study.md`). Matrix reading, KP 58.8 and KP 60.0 as
if undrained, unless stated.

No production default, config, prior, kernel, persisted sweep, Phase 2
posterior or Phase 3 table changes.

## 1. The question

Joost Pol's written comments on the pre-Green-Light thesis (2026-10-06):

4. "gravel aquifers: models (Sellmeijer & Pol) are derived for sand. How does
   that affect results and conclusions? E.g., in Dutch practice, we increase the
   critical head from Sellmeijer by a factor 1.8 in case of gravels."
5. "particle size distribution shape: I think the grading (very high Uc values
   in Appendix A.3) may explain why BEP doesn't happen here. We know from
   experiments that the critical head increases strongly with the ratio
   d60/d10. Also, the lab tests indicate low permeability (10^-5) combined with
   coarse grains, which increases piping resistance."

What he read: the pre-Green-Light Appendix A "Complete Grain-Size Analysis"
(`msc-thesis` tag `pre-greenlight-2026-09-24`, `tab:app_grainsize`): whole-
specimen U_c 24.9 to 467, d60 up to 13 mm, laboratory constant-head conductivity
9.2e-6 to 5.6e-4 m/s, under a heading that called them aquifer specimens. Green
Light item 4 (ADR-0054, `bimodal-foundation-d70-study.md`) later showed that the
shallow paired grading-and-conductivity specimens are embankment fill, and
re-based the matrix d70 on the 28 aquifer gradations. The final thesis answers
the grading point in Section 8.3.2 with an argument against it ("the expectation
that a well-graded soil resists piping does not apply either, because the high
coefficients record a gap between matrix and framework"), resting on the
Kenney-Lau screen of `uniformity-coefficient-study.md` section 2.5 and on
Townsend's sheet flow as reported by van Beek (2015).

## 2. Sources read for this study (page references are to the printed page)

| Source | Page | What it says |
|---|---|---|
| van Beek (2015), PhD thesis | p. 20 | Townsend et al. (1988), UF flume: "The graded and gap-graded soils did not undergo pipe formation but 'sheet flow' ... in the non-uniform sand types (d60/d10>5), there was no failure at all in the range of the gradient used in the set-up (the maximum gradient was 1.2)"; Townsend concluded that "a higher gradient is required to induce piping in a well-graded cohesion-less soil than in a uniform cohesion-less soil". |
| van Beek (2015) | p. 40, p. 41 | In Sellmeijer's revised rule the uniformity coefficient and angularity "proved to have a negligible effect ... in the tested range". Schmertmann (2000) "emphasises the uniformity coefficient as one of the most influential factors", with few high-C_u experiments, often with sheet flow. |
| van Beek (2015) | pp. 86 to 88, Fig. 4.24; p. 107; p. 139 (section 6.3.3) | Fines added to a sieved Itterbeck sand "resulted in significantly stronger samples"; caveats: permeability also changed, fines migration needs longer durations, bridging lowered downstream permeability. Fig. 4.24 (read from the figure): d60/d10 about 1.7 gives H_c/L about 0.28 and 0.33; about 2.4 gives about 0.61; about 3.2 gives about 0.44 and 0.60 (dense samples). Summary p. 107: "An increase in the uniformity coefficient leads to an increase in the critical head." |
| Allan (2018), PhD thesis, UNSW Sydney (open access, CC BY-NC-ND 3.0) | pp. 289 to 290; Fig. 8.20 p. 311; pp. 320 to 321; pp. 406 to 411; pp. 420 to 421 | 92 large flume tests. Eight poorly and well graded soils, C_u 2.6 to 8.8, designed internally stable (Wan and Fell probability below 0.3). Critical gradient rises with C_u; exponential fit 0.13 exp(0.32 C_u), R^2 = 0.87 (circle exit, Fig. 8.20). Mix 1 (C_u 6.8) formed no backward-eroding channel and channels in Mix 4 (C_u 8.8) did not progress at gradients near 3; Mixes 3 and 8 (C_u 6.2, 6.4) did fail, so "susceptibility ... is likely to not be a function of uniformity coefficients alone". Internally stable mixes had critical gradients "up to 52% lower" than the internally unstable gap-graded soils of Townsend and Shiau (1986), whose tests stopped before critical: "it appears internally stable soils are more susceptible to backward erosion than internally unstable soils", attributed to fines migrating downstream and lowering local permeability where erosion initiates. For "non standard dike" soils (coarse uniform sands and graded sands) the Sellmeijer et al. (2011) formula "often underestimate[s] the observed critical gradients"; refitting with C_u 1.3 to 8.6 and d70 0.24 to 4.6 mm raised the C_u exponent from 0.13 to 0.5 and lowered the d70 ratio exponent from 0.6 to 0.04 (R^2 0.01 to 0.75). Tip progression was faster, and in bursts, in more widely graded soils (p. 320). |
| Robbins, Stephens, Leavell, Lopez-Soto and Montalvo-Bartolomei (2018), Can. Geotech. J. 55(11), 1552 to 1563; read as the accepted manuscript cgj-2016-0350.R1 | abstract; Table 3; Fig. 11; pp. 14, 16 to 18 | Sixteen horizontal flume tests on a poorly graded fine gravel (d10 4.67, d60 7.79 mm, C_u 1.67, d50 7.2 mm): critical horizontal gradient 0.30 (loose) to 0.51 (dense). Fig. 11 (read from the figure): Sellmeijer et al. (2011) with its multivariate adjustment predicts about 0.11 to 0.19 against 0.30 to 0.52 observed, i.e. underpredicts by about 2.5 to 3; the original Sellmeijer form overpredicts (about 1.3 to 1.6). Erosion progressed "very quickly ... 1-4 cm/s". Natural gravels "more broadly graded with higher coefficients of uniformity ... more resistant to BEP than those tested". |
| Rijkswaterstaat (2023), Handleiding Overstromingskansanalyse Dijken/dammen deel 2: Piping, groene versie december 2023 | pp. 21 to 22; p. 36; p. 42; p. 43 (section 5.3.3.4) | Calibration band of the Sellmeijer rule: d70 150 to 500 um, uniformity d60/d10 1.5 to 2.5, no fines (Deltares 2012). Outside the band: "Bij hogere waarden voor de uniformiteitscoefficient (d60/d10) neemt de sterkte tegen piping toe. Daarbij blijkt dat bij d60/d10 > 6,8 zand niet meer bezwijkt op terugschrijdende erosie (Allan, 2018). Het werken met de rekenregel van Sellmeijer is dus conservatief. Bij zeer hoge waarden van d60/d10 kan het zand intern instabiel worden, en kunnen andere erosiemechanismen (suffosie) relevant worden." Larger d70: "waarschijnlijk conservatief" (Shields). Fines raise resistance; tidal-channel deposits use a factor 1.4 on the critical head. Gravel (section 5.3.3.4): "Onderzoek (Deltares, 2019d) laat zien dat meer weerstand tegen terugschrijdende erosie verwacht mag worden voor grind en grindhoudende zanden", to be credited "door het kritiek verval te verhogen"; Deltares (2019d) = "Pipinggevoeligheid grind en grindhoudende zanden maasvallei", 11202002-002-GEO-0005. No factor is printed. |
| Deltares (2022), Rode Draden Piping (March 2022) | p. 7, Table 1; p. 27 | Limburg: thin permeable blanket, "wel veel kwel ... maar weinig zandmeevoerende wellen"; "De grotere korrels, de hoge uniformiteitscoefficient en mogelijk verkitting dragen naar verwachting bij aan een hogere erosieweerstand." p. 27: the applicability of Sellmeijer for gravel and less uniform sand is "nog een kennisleemte". |
| van Dijk, Koopmans and Aguilar Lopez (2024), Water Matters 19, pp. 34 to 37 (TU Delft MSc van Dijk 2023 for Arcadis) | p. 35; p. 37 (sources) | "De Limburgse bodem bestaat op veel plekken uit grofzandige en grindhoudende lagen, die een hogere weerstand tegen piping hebben. Daarom past het waterschap een extra vermenigvuldigingsfactor van 1,8 toe" [5]; source [5] = Van Beek (2018), "Grind en grindhoudende lagen in de Maasvallei", Deltares memo 11202002-002-GEO-0002, unpublished. July 2021: water to the crest in places, "maar dertien wellen" along the Maas in Limburg and Brabant. Their own calibrated groundwater-model study proposes 1.56 on F_s for d70 100 to 900 um. |
| Zethof et al. (2023), HKV, Continu Inzicht WBI+ (`hkv_2023`) | printed p. 19, section 6.4 (the brief's "p. 18" is section 6.1 to 6.3) | Fragility scripts for sections "met een grindlaag in de schematisatie, waarbij het kritieke verval met een factor 1,8 wordt vermenigvuldigd conform de werkwijze die in de beoordeling is gehanteerd". |
| Deltares (2018), Korrelgroottes en heterogeniteit van rivierafzettingen in het licht van piping, 1210060-002-BGS-0001 | p. 16; p. 75 | Two WBI d70 definitions (sand-and-gravel fraction; full distribution). "Gegradeerde afzettingen zijn daardoor niet zo gevoelig voor piping"; yet "ook bij grindafzettingen piping kan optreden bij relatief lage gradienten (Robbins et al.) en alleen korrelgrootte zegt dus niet voldoende". |

What could not be read: the two Deltares Limburg memos (11202002-002-GEO-0002,
2018; -GEO-0005, 2019) are unpublished. What the 1.8 represents is therefore
known from the secondary sources above (extra resistance of coarse-sandy and
gravel-bearing layers in the Limburg Meuse, applied to the Sellmeijer critical
head where the schematization has a gravel layer), but not its derivation, nor
which d70 it is applied with.

## 3. Arms

An exact multiplier `c` on the single-source H_c, in both criteria, through the
bedding angle `theta' = atan(c tan 37 deg)` (theta enters F_r and nothing else;
`uniformity_coefficient_study.theta_for_factor`). In-memory config override, the
production seed and sample (N = 1e5, matrix), persisted only under the
gitignored `results/gravel_grading/`. Ladder `c = 1.25, 1.5, 1.8, 2.2, 2.7`:

- 1.8 is the Dutch gravel reading (the named alternative).
- 1.5 to 1.6 is where the Green Light item 1 "matrix" uniformity arm sits, and
  1.58 to 1.88 is what Allan's refitted exponent 0.5 gives on the sand-fraction
  coefficients (4.5 to 6.4).
- 2.5 to 3 is the order of the underprediction of uniform fine gravel by the
  revised rule in Robbins et al. (2018).

Each arm goes through the 2016 replay (production Phase 2 settings, read from
the production sidecar) and through the production Phase 3 annualisation with
the member-block bootstrap of `annualisation_uncertainty_study`.

Gates: (i) every arm's single-source H_c equals `c` times production row for
row (relative 1e-12); (ii) the arm's persisted gross-head static column is
recomputed bit for bit (ADR-0040 gate i, as in the ADR-0055 driver); (iii) the
baseline annual rows reproduce `rq4_annual.csv` field for field.

## 4. Predictions (written before any arm was computed)

- **P1 (nesting, near-theorem).** No row fails an arm without failing the
  baseline, on either criterion. The 2016 initiation indicator is identical to
  the baseline bit for bit in every arm, because the uplift and heave gate does
  not read H_c.
- **P2 (design grid).** At c = 1.8 the transient design-grid probability falls
  below 0.01 at KP 58.8 (baseline 0.197; the 1.50 uniformity arm gave 0.021) and
  below 1e-3 at KP 60.0; KP 57.4 and KP 62.0 have no transient failure at their
  design-grid stages in 1e5.
- **P3 (criterion comparison).** Delta-beta falls monotonically in `c` at every
  common count-qualified stage (the crack decrement and the gate do not scale
  with H_c); F_td moves either way.
- **P4 (2016).** At c = 1.8 the transient rejection at KP 58.8 falls below
  0.2 % and is zero at the other three sections; the likelihood ratio between
  the criteria is below 1.01 everywhere.
- **P5 (annual, posterior side, c = 1.8).** Piping loses the lead at KP 58.8 and
  KP 62.0 in both climates and at KP 57.4 under warming; it keeps the historical
  cells of KP 57.4 and KP 60.0 only because overflow is exactly zero there;
  KP 60.0 under warming goes to overflow. Piping leads in 2 or 3 of the 8 cells.
- **P6 (break-even multipliers).** Piping first loses the lead at c = 1.25 in
  the KP 62.0 warming cell, at 1.5 in the KP 62.0 historical and KP 57.4 warming
  cells, and at 1.8 to 2.2 at KP 58.8.
- **P7 (climate ratio).** The annual climate ratio rises with `c` at every
  section.
