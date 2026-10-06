# Study: sand-based models in a gap-graded gravel, grading, and what extra resistance would change (Pol comments 4 and 5)

Date: 2026-10-06 (Pol feedback, session 2 of 6)
Status: Complete. Part 1 (sources and pre-registration) was committed, as its own commit, before any
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

## Part 2: outcome (2026-10-06)

### 5. What the sources establish (no computation)

**5.1 Grading.** The direction is established, the size for these soils is not.
Every experiment read raises the backward-erosion critical gradient with the
uniformity coefficient: van Beek's fines series (factor about 1.5 to 2 from
d60/d10 1.7 to 2.4 to 3.2), Townsend's flume (non-uniform sands, d60/d10 > 5,
did not fail up to i = 1.2) and Allan's eight internally stable graded soils
(exponential rise over C_u 2.6 to 8.8; no backward erosion at C_u 6.8 and 8.8).
Rijkswaterstaat's 2023 manual states the same and calls the rule conservative
there. Allan's refit of the Sellmeijer formula raises the uniformity exponent
from 0.13 to 0.5; on the sand-fraction coefficients (4.5 / 6.4 / 5.3 / 5.4, KP
order) that alone is a factor (C_u/1.81)^0.5 = 1.58 / 1.88 / 1.71 / 1.73 on
H_c. Her refit also lowers the d70 ratio exponent from 0.6 to 0.04, which for
d70 above the 208 um calibration mean would raise H_c further; neither change is
adopted here. No experiment covers a gap-graded sand-gravel at whole-grading
C_u 34 to 80.

**5.2 The gap grading does not cancel the grading effect.** The thesis argued
(Section 8.3.2 until 2026-10-06, after `uniformity-coefficient-study.md` 2.6
item 2) that because the high C_u records a gap between matrix and framework,
"the expectation that a well-graded soil resists piping does not apply". The
evidence read does not support that inference for backward erosion: Allan found
internally stable graded soils up to 52 % weaker than internally unstable
gap-graded ones (fines migrating to the exit lower the local permeability), and
Townsend's graded and gap-graded sands sheet-flowed rather than piped. Internal
instability opens suffusion, a separate mechanism with a two-sided effect; it
is not evidence of lower backward-erosion resistance. Pol's comment is right in
direction, and the thesis's argument against it is withdrawn (dated correction
in `uniformity-coefficient-study.md` 2.6).

**5.3 Grain size.** Mixed. The revised rule over-predicted the one large-scale
coarse-sand test (Sellmeijer 2011: 25 %; the thesis's own reproduction 2.01
against 1.75 m) but under-predicted a uniform fine gravel by about 2.5 to 3
(Robbins et al. 2018, Fig. 11, read from the figure; the original 1988 form
over-predicts the same gravel by about 3). Allan finds the rule under-predicts
coarse uniform and graded sands generally. Robbins et al. attribute the
discrepancies to turbulence in the pipe and expect natural, broadly graded
gravels to resist more than their uniform one.

**5.4 Progression.** Pol's rate law was fitted on simulated sands with d50 0.2
to 0.4 mm, C_u 2 and 3 and permeabilities equivalent to about 7e-5 to 7e-4 m/s
(Pol CompGeo 2024 Table 2, converted with the paper's own viscosity); the
adopted Tokachi conductivity (1e-3 to 3e-3 m/s) is above that range, so the
rate is extrapolated in k. Once the critical head is exceeded, pipes advance
faster in coarse sand (van Klaveren 2020), in more widely graded soils, in
bursts (Allan 2018 p. 320), and very fast in fine gravel, 1 to 4 cm/s (Robbins
et al. 2018); Pol et al. (2024) note that a locally stronger layer raises H_c
but gives faster progression once exceeded. Faster growth than the law predicts
would shrink the time effect.

**5.5 The Dutch factor of 1.8.** Basis: Deltares memos for Waterschap Limburg
(Van Beek 2018, 11202002-002-GEO-0002; Deltares 2019, -GEO-0005), both
unpublished and not read. What it represents, from the sources that are public:
the higher piping resistance of the "grofzandige en grindhoudende lagen" of the
Limburg Meuse (van Dijk et al. 2024), expected from "de grotere korrels, de hoge
uniformiteitscoefficient en mogelijk verkitting" (Deltares 2022), applied as a
multiplier on the Sellmeijer critical head for sections whose schematization
has a gravel layer (HKV 2023 p. 19) and endorsed in principle, without the
number, by Rijkswaterstaat (2023 section 5.3.3.4). It is therefore a bundled
allowance for coarse grains, wide grading and possible cementation, not a
calibrated uniformity correction, and must not be combined with the
uniformity arms. Which d70 accompanies it in the Limburg assessments is not
stated in any public source. Application here: to the **matrix** reading, whose
eroding material is the coarse sand of a gravel-bearing layer, the case the
factor addresses; not to the bulk reading, which already credits the gravel
through d70^0.4 and leaves most design-stage counts at zero. Cross-check: van
Dijk et al. (2024) report only 13 sand-carrying wells along the Limburg and
Brabant Meuse in July 2021 with water to the crest in places, the field
observation behind the regional view that the factor may still be conservative.

**5.6 Low conductivity with coarse grains.** The premise rests partly on fill:
the paired laboratory specimens Pol saw (9.2e-6 to 5.6e-4 m/s) are embankment
fill (ADR-0054), and the whole-specimen U_c values he saw above 200 (216, 258,
408, 467) are fill specimens too; the aquifer's own whole-specimen U_c is 4.46
to 192 (section medians 34 to 80). The aquifer's six in-situ tests point the
same way as his premise (geometric mean 5.94e-5 m/s), whereas OYO's own
grain-size estimates for the 28 aquifer specimens (`k_est_cms` in the
transcription) have geometric mean 8.1e-4 m/s (section means 3.9e-4 to 1.6e-3),
close to the adopted analysis constants. Within the models the combination is
coherent and strongly resistance-raising: H_c grows as k^(-1/3) (a factor 2.6 to
3.7 at the field-test mean) and the rate falls as k^0.81, and the lower
transmitted pressure also suppresses initiation. That reading is the persisted
ADR-0048 field-test arm (section 8 below gives its 2016 numbers; its annual
side is in conductivity-bracket-posterior-side.md).

### 6. Run and gates

Run (worktree, main venv, `PYTHONPATH=.`): `arms --n-jobs 10` (20 sweeps, 94
to 406 s each), the 2016 replay of every arm with the production Phase 2
settings (the `replay` part's settings builder, four replays at a time), then
`event`, `annual`, `resistant`, `report`, `figures`.

- Gate (i): H_c of every arm equals `c` times production row for row
  (largest relative deviation 4.4e-16).
- Gate (ii): every arm's persisted gross-head static column is reproduced bit
  for bit at every level (inside `same_head_flags`).
- Gate (iii): the baseline annual rows reproduce `rq4_annual.csv` on all 912
  rows (matrix and bulk, prior and posterior), field for field; the 110
  surface-only segments are identical across every arm and branch; the hazard
  cache is unchanged.
- Nesting (P1): no row fails an arm without failing the baseline, on the
  transient criterion, the same-head criterion or the gross head, in any of
  the 20 arms. The 2016 initiation indicator is identical to the baseline bit
  for bit in all 20.
- Containment: 17 row-level forward-Euler barrier jumps (a transient failure
  outside the same-head set) over all 20 arms, at most 2 at a level, at KP 57.4
  and KP 58.8 only, none at a design-grid stage, at most 0.48 % of a level's
  transient failures except one level with 78 (1 row, 1.3 %). The documented
  ADR-0030 / ADR-0055 class, counted, not removed.

### 7. Per event (matrix, N = 1e5, design-grid stages)

| Multiplier | KP 58.8 41.00 m: P_t / P_s, dbeta [95 %], F_td | KP 60.0 42.75 m: P_t / P_s, dbeta [95 %], F_td |
|---|---|---|
| 1 (adopted) | 0.197 / 0.450, 0.72 [0.72, 0.73], 2.28 | 0.056 / 0.216, 0.81 [0.79, 0.82], 3.88 |
| 1.25 | 0.071 / 0.166, 0.50 [0.49, 0.51], 2.34 | 0.0108 / 0.0427, 0.58 [0.56, 0.60], 3.95 |
| 1.5 | 0.0218 / 0.0488, 0.36 [0.35, 0.38], 2.24 | 0.0019 / 0.0063, 0.40 [0.36, 0.44], 3.31 |
| **1.8** | **0.0046 / 0.0097, 0.26 [0.24, 0.29], 2.09** | 1.6e-4 / 5.7e-4 (16 transient rows, below R1) |
| 2.2 | 5.3e-4 / 1.0e-3, 0.19 [0.14, 0.25], 1.94 | 1e-5 / 3e-5 |
| 2.7 | 2e-5 / 4e-5 | 0 / 0 |

KP 57.4 and KP 62.0 have no transient failure at their design-grid stages in
any arm (as at baseline for KP 57.4). Over every attainable stage at which both
the arm and the baseline have at least 30 transient failures:

| Multiplier | shared levels | change in dbeta | factor on F_td |
|---|---|---|---|
| 1.25 | 49 | -0.15 to -0.38 | 0.84 to 1.25 |
| 1.5 | 45 | -0.18 to -0.62 | 0.78 to 1.42 |
| **1.8** | 39 | **-0.39 to -0.82** | **0.73 to 1.53** |
| 2.2 | 33 | -0.52 to -1.01 | 0.75 to 1.55 |
| 2.7 | 23 | -0.64 to -1.14 | 0.88 to 1.48 |

dbeta falls at every shared level in every arm; F_td straddles one. The 1.5
row matches the Green Light item 1 matrix uniformity arm (multipliers 1.50 to
1.60: -0.27 to -0.63, F_td 0.79 to 1.44).

### 8. 2016, and the material-side numbers for sessions 3 and 4

2016 full-record replay, prior N = 1e5 (rejected share transient / same-head;
initiation = the exit opened at some time in 2016):

| Reading | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| adopted | 0.016 % / 0.39 %; init 66.4 % | 3.81 % / 28.3 %; 99.6 % | 0.23 % / 5.2 %; 99.3 % | 0 / 0; 39.6 % |
| H_c x 1.25 | 0.002 % / 0.016 % | 0.98 % / 7.9 % | 0.023 % / 0.52 % | 0 / 0 |
| H_c x 1.5 | 0 / 0.003 % | 0.23 % / 1.8 % | 0.002 % / 0.04 % | 0 / 0 |
| **H_c x 1.8** | **0 / 0** | **0.037 % / 0.26 %** | **0 / 0.003 %** | **0 / 0** |
| H_c x 2.2 and 2.7 | 0 | at most 0.002 % | 0 | 0 |
| bulk d70 | 0 / 0; 66.4 % | 0 / 0; 99.6 % | 0.023 % / 0.51 %; 99.3 % | 0 / 0; 39.6 % |
| field-test k mean | 0 / 0; **1.5 %** | 0 / 0; **54.6 %** | 0 / 0; **62.0 %** | 0 / 0; **0.13 %** |
| landside-toe k test | 0; 29.0 % | 0.025 % / 1.1 %; 96.8 % | 0.008 % / 0.53 %; 98.0 % | 0; 17.9 % |
| regional upper k | 2.2 % / 12.5 %; 87.8 % | 58.7 % / 92.7 %; 99.97 % | 62.1 % / 94.5 %; 99.96 % | 0.004 % / 0.14 %; 98.5 % |
| measured berm | | 0.90 % / 11.9 %; 99.3 % | 0.014 % / 0.80 %; 98.6 % | |

The likelihood ratio between the criteria (transient over same-head survival)
falls from 1.34 at KP 58.8 to 1.075, 1.016, **1.002** and 1.0001 along the
ladder, and is 1.000 to 1.005 elsewhere from 1.25 up (P4). Initiation is
unchanged by every multiplier and by the bulk reading (neither reaches the
gate), and falls sharply only with conductivity (the transmitted head r_e
falls with the leakage length).

Per-event transient probability at the design-grid stage under the resistant
readings (KP 58.8 / KP 60.0): field-test k 0 / 0; landside-toe k 0.0052 /
0.0059; bulk 0 / 0.0105; berm 0.074 / 0.0088; x1.8 0.0046 / 1.6e-4.

### 9. Annual (posterior side, flood-ensemble 95 % intervals, 10,000 member-block resamples)

At x1.8, historical: annual piping 9.9e-6 / 6.7e-4 / 1.8e-6 / 2.3e-5 (KP
order), lower than adopted by 50 / 9.0 / 173 / 33; annual system 9.9e-6 /
8.5e-4 / 1.8e-6 / 2.2e-4 (lower by 50 / 7.3 / 173 / 4.2). +4 K: piping lower by
6.9 / 5.0 / 23 / 9.3, system by 4.8 / 4.2 / 21 / 1.4. Prior side (no update),
historical piping: lower by 50 / 10.0 / 177 / 33.

Leading mechanism (piping share of the summed contributions; fraction of
resamples in which piping leads, where not 1.00 or 0.00):

| Cell | adopted | x1.25 | x1.5 | **x1.8** | x2.2 | x2.7 |
|---|---|---|---|---|---|---|
| KP 57.4 hist | 1.00 (overflow 0) | 1.00 | 1.00 | **1.00** | 1.00 | 1.00 |
| KP 58.8 hist | 0.97 | 0.94 | 0.89 | **0.78** | 0.50; 0.37 | 0.15 |
| KP 60.0 hist | 1.00 (overflow 0) | 1.00 | 1.00 | **1.00** | 1.00 | 1.00 |
| KP 62.0 hist | 0.79 | 0.58; 0.84 | 0.32; 0.11 | **0.10; 0.01** | 0.02 | 0.00 |
| KP 57.4 +4K | 0.89 | 0.82 | 0.71 | **0.54; 0.86** | 0.31; 0.01 | 0.11 |
| KP 58.8 +4K | 0.93 | 0.90 | 0.84 | **0.73** | 0.54 | 0.29 |
| KP 60.0 +4K | 0.99 | 0.99 | 0.96 | **0.89** | 0.59; 0.95 | 0.15; 0.03 |
| KP 62.0 +4K | 0.48; 0.08 (tie) | 0.32 | 0.19 | **0.09** | 0.03 | 0.01 |

At the Dutch factor piping keeps the lead in 6 of the 8 cells (2 of them
because overflow is exactly zero) and loses it at KP 62.0 historically; KP
57.4 under warming becomes a near tie (0.54, piping ahead in 86 % of
resamples). Break-even (first ladder value at which the leading mechanism
changes): KP 62.0 historical at 1.5; KP 58.8 historical and KP 57.4 +4 K at
2.2; KP 58.8 and KP 60.0 +4 K at 2.7. The ranking among the four (system,
historical) is unchanged (KP 58.8, 62.0, 57.4, 60.0) up to 2.2; under warming
at 1.8 KP 58.8 and KP 62.0 are level (8.6e-3 against 8.5e-3, the order held in
55 % of resamples).

The annual criterion factor (steady-state over transient, prior, piping alone)
falls from 2.05 / 1.84 / 3.32 / 3.12 to 1.68 / 1.80 / 2.40 / 2.29 at x1.8
historically (annual dbeta 0.21 to 0.35 down to 0.12 to 0.20). The climate
ratio rises: 15.3 / 5.8 / 13.4 / 13.4 to 161 / 10.1 / 111 / 38.8 at x1.8 (P7),
because extra resistance suppresses the low historical stages most.

### 10. Prediction scoring

| | Prediction | Outcome |
|---|---|---|
| P1 | nesting; initiation unchanged | **held** (zero violations; initiation bit-identical in all 20 arms) |
| P2 | x1.8 design grid: KP 58.8 < 0.01, KP 60.0 < 1e-3, zero at KP 57.4 and 62.0 | **held** (0.0046; 1.6e-4; zero) |
| P3 | dbeta falls monotonically; F_td either way | **held** (every shared level, every arm; F_td 0.73 to 1.55) |
| P4 | x1.8 2016 rejection < 0.2 % at KP 58.8, zero elsewhere; LR < 1.01 | **held** (0.037 %; zero; 1.002) |
| P5 | piping leads in 2 or 3 of 8 cells at x1.8 | **failed**: it leads in 6 (KP 58.8 in both climates, KP 60.0 and narrowly KP 57.4 under warming, beside the two zero-overflow cells). The prediction carried KP 60.0's large reductions over to KP 58.8 and ignored how remote overflow is there (historical overflow 1.95e-4 against piping 6.1e-3 at baseline, so piping must fall about thirtyfold) |
| P6 | break-even 1.25 / 1.5 / 1.8 to 2.2 | **partly failed**: KP 62.0 historical 1.5 (held); KP 62.0 +4 K was already overflow's point estimate; KP 57.4 +4 K 2.2 (predicted 1.5); KP 58.8 2.2 historically (held) and 2.7 under warming (predicted 1.8 to 2.2) |
| P7 | climate ratio rises with c | **held** at every section |

### 11. What this means for the thesis's answers

1. **Robust, by construction:** the direction of the criterion comparison. Any
   resistance factor the two criteria share keeps every transient failure a
   steady-state failure (P1), so no grading or gravel allowance can make the
   time-dependent rule the more pessimistic.
2. **Conditional:** absolute probabilities (per event and annual, by one to two
   orders of magnitude at x1.8), the size of the time effect (dbeta lower by
   0.39 to 0.82 at x1.8, the largest soil lever measured on it; F_td either
   way; annual factor 1.7 to 2.4), the climate ratio (several-fold higher) and,
   at KP 62.0, the mechanism ordering. Faster growth in coarse, graded material
   than the sand-fitted law predicts (section 5.4) would shrink the time effect
   further; not quantified.
3. **Less conditional than the other resistance readings:** the piping lead at
   KP 57.4, 58.8 and 60.0. Overflow is remote there, so piping keeps the lead up
   to multipliers of 2.2 (KP 58.8 historical, KP 57.4 +4 K) to 2.7, beyond the
   Dutch allowance and Allan's sand-fraction refit; the conductivity bracket,
   the bulk reading and the foreland credit remain the readings that remove it.
4. **2016 cannot tell the readings apart.** Every resistant reading makes the
   survival more probable (rejection 3.8 % at KP 58.8 adopted, 0.04 % at x1.8,
   zero at the field-test k mean), so the record favours them only by
   1/0.962 = 1.04 at KP 58.8 and less elsewhere. The resistance arguments are
   physically supported and point one way, but the survival record cannot
   confirm them. What a resistant reading cannot do in this model is suppress
   initiation: an H_c multiplier and the bulk d70 leave the 2016 initiation
   probability at 66 / 99.6 / 99.3 / 40 %; only a lower conductivity (or drain
   relief) lowers it, to 1.5 / 55 / 62 / 0.1 % at the field-test mean. Whether
   a widely graded gravel would eject sand at an opened exit, rather than clear
   water, is outside the model (Deltares 2022 on Limburg: "wel veel kwel ...
   maar weinig zandmeevoerende wellen").

**Decision.** The x1.8 reading is a **named companion**, not an adopted input:
its basis is unpublished and regional (the Limburg Meuse), it bundles grading,
grain size and possible cementation without a published derivation, which d70
it accompanies is undocumented, and the thesis's design carries interpretive
alternatives as named readings beside an adopted configuration that is
deliberately at the piping-favoring end. Adopting it would move every adopted
result and is the owner's decision; this study does not recommend it.

### 12. Artifacts

| What | Where |
|---|---|
| This note | `docs/decisions/gravel-grading-resistance-study.md` |
| Evidence | `docs/decisions/gravel-grading-resistance-study.json` |
| Driver | `scripts/gravel_grading_resistance_study.py` |
| Gate | `tests/test_gravel_grading_resistance_study.py` |
| Figure | `docs/figures/resistance_multiplier.png` |
| Corrected record | `docs/decisions/uniformity-coefficient-study.md` 2.6 (dated correction) |
| Arm sweeps, replays, stage files | gitignored `results/gravel_grading/` (regenerable; copied to `pol_feedback_2026-10-06/artifacts/session2_gravel_grading/`) |
