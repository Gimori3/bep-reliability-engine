# Study: why the Tokachi sections showed no piping in 2016 (Pol comment 8)

Date: 2026-10-07 (Pol feedback, session 4 of 6)
Status: Part 1 (the question, the sources, the arithmetic done from them and
the pre-registration) is committed on its own, before any engine number of this
study was computed. Part 2 records the outcome.

Evidence: `why-no-piping-2016-study.json`, driver
`scripts/why_no_piping_2016_study.py`, gate
`tests/test_why_no_piping_2016_study.py`. Run artifacts: gitignored
`results/why_no_piping_2016/`. Comparator of record: ADR-0055 (same head and
same gate). Matrix reading, adopted conductivity, canonical event; KP 58.8 and
KP 60.0 as if undrained unless a configuration is named.

No production default, config, prior, kernel, persisted sweep, Phase 2
posterior or Phase 3 table changes. Every arm below is a named diagnostic, not
an adopted input.

## 1. The question

Joost Pol's written comment 8 on the pre-Green-Light thesis (2026-10-06):

> "Tokachi case: piping (initiation?) predicted by OYO but didn't happen in
> 2016. Question is why? What makes the two river cases so different? subsoil,
> delayed groundwater, timedependence, reinforcement? Can you explain that now?
> Timedependent pipe growth can only explain it when we have sand boils
> (initiation)."

**Which two cases.** What he read (`msc-thesis` tag `pre-greenlight-2026-09-24`)
set the Tokachi against the Tokoro under one heading, Chapter 3 "Levee
Performance: Tokoro River versus the Tokachi and Satsunai Study Reaches", which
opens "The evidential value of the 2016 survival rests on a contrast between two
Hokkaido river systems"; his Summary's first paragraph does the same, and
Chapter 3 concluded that "Tokoro demonstrates that these foundations permit
initiation under 2016-class loading, excluding an absent regional hazard as the
explanation for survival". The two cases are therefore the Tokachi study
sections (no recorded boil) and the Tokoro (boils, no breach). Not asked of the
owner: the text he commented on settles it.

**His logic**, adopted here as a premise to test, not assumed: a time-dependent
pipe-growth model explains a survival only where an exit opened. With no
recorded boil, the explanation must lie before progression (load, works, toe
pressure, blanket, aquifer) or in the record.

The final thesis (`msc-thesis-final` at `34e8bca`) still frames its motivation
as "whether that survival reflects strong foundations, or floods too short for
an erosion failure to complete" (Section 1.1), and its Section 6.5 (session 3)
already shows that finite duration holds back a breach in 2016 for 25 % of KP
58.8's foundations, 5 % of KP 60.0's and almost none elsewhere
(`initiation-evidence-2016-study.md` section 4).

## 2. Sources read for this study (page references to the printed page)

| Source | What it supplies |
|---|---|
| OYO (1999), per-section forms 様式-5 (evaluation conditions) and 様式-6 (seepage result), `docs/references/R0*/81_..._05安全性の詳細評価条件図.pdf` and `_06浸透流計算結果図.pdf`, rendered and read for all four sections | The 1998 check was a **transient** saturated-unsaturated seepage computation (様式-6 shows wetting surfaces at six times), with 100 mm antecedent rain at 1 mm/h and 246 mm flood rain at 10 mm/h, and a design water-level waveform: base stage, a linear rise over about 40 h, **1.5 h at the 1998 design level**, fall at 0.29 m/h. Base / design stages [m T.P.]: KP 57.4 34.00 / 39.51; KP 58.8 36.80 / 41.33; KP 60.0 37.80 / 43.06; KP 62.0 41.60 / 46.68. Maximum local gradients (様式-6): 0.04 / 0.05, 1.30 / 0.62, 0.50 / 0.40, 0.97 / 0.66 (vertical / horizontal). Foundation k in 様式-5 at KP 58.8: cohesive cover 1e-6 m/s, gravel 2e-3 m/s. |
| OYO (1999) report §6-1 (p. 139), 表6-3-1 (p. 151), 表7-5-1 (p. 174), §8 (as transcribed in `docs/oyo_1998_framing_review_2026-08-24.md`, which read the rendered pages) | Criterion `i >= 0.5` at the landside toe, applied also at the blanketed sections where current guidance uses G/W; KP 58.8, 60.0 and 62.0 named 基盤漏水によるパイピング; designed drains: cut through the A_c layer at KP 58.8 (1.30 to 0.30, **77 % relief**) and KP 62.0 (0.97 to 0.23), on top of the cover at KP 60.0 (0.50 to 0.48, **4 %**). As-built geometry not on record. |
| `docs/tokachi_bep_inputs_provenance.md` 7.1, 3.10 | Today's design levels (2019 table, 2007 plan) are 0.30 m below OYO's 1998 levels (the 1966/1983 plan), T.P. equal to the engine datum. |
| Tokoro River Levee Investigation Committee (2017), `docs/references/icrceh00000032zs.pdf`, text layer, pp. 2-11, 5-15, 5-17, 5-19 to 5-21, 5-24, 7-5 | At the Futochanae gauge (KP 18.9) the stage exceeded the design high water level 12.38 m for **32 h 40 min**, peak in the committee's waveform **14.22 m** (1.84 m above it); peak discharge about 1,700 m³/s against a 1,500 m³/s plan target, the largest on record. "The water level of the boil reach exceeded the design level for a long time" (p. 5-15). Boils at old channels and tributary confluences where sand and gravel layers are thick (p. 5-15); boil sand matches the As1 sandy soil 1 to 2 m below the landside ground (p. 5-17). The committee's seepage model of the boiling site KP 26.8, loaded with that waveform: As k = 1e-5 m/s, surface cohesive soil k = 1e-7 m/s, local gradients 0.70 vertical and 0.87 horizontal against 0.5 (pp. 5-19, 5-20). Test pits: no pipe or water path, countless sand-filled cracks; "boils tend to originate where the surface cover is thin" (p. 5-21). Mechanism (p. 5-24, and the third meeting, p. 7-5): "under the influence of the long-lasting high external water level", pressure propagated through loose zones and broke out at weak spots such as thin cover. |
| Kawajiri et al. (2025), pp. 31 to 38 | Largest boil (2.0 m wide, 0.5 m high) at the landside toe of Tokoro KP 24.6; there a sand layer with the boil's grading, about 1.0 m thick under the levee and 0.4 to 0.6 m elsewhere, runs continuously from the riverside, where the bank exposes it, beneath about 1.0 m of fine-grained cover (40 to 60 % silt and clay). At KP 26.2 the sand lies 1.1 to 1.55 m deep and the landside silt thickens to 1.5 to 1.8 m. |
| Kunijiban logs `data/raw/borehole_and_soil_survey/TRANSCRIPTION_layers.csv` with provenance 8.1 and 8.7 | At the Satsunai confluence the base-flow water table, 31.71 to 31.73 m, lies 0.70 m (landside toe hole), 1.02 m (crest hole) and 2.77 m (KP 2.1L-1) below the top of the gravel. |
| ADR-0032 and its 2026-07-11 scope amendment | The elastic aquifer-response screen (response time minutes, rise about 18 h) does not cover an aquifer whose top is unsaturated when the flood arrives ("initial heads well below the exit datum ... needs a transient-fill assessment"). |

## 3. Arithmetic from the sources (done before this pre-registration)

**Load against what OYO assessed.** The 2016 trace-anchored peaks (39.658 /
40.750 / 42.296 / 45.729 m) against OYO's 1998 levels: +0.15 / -0.58 / -0.76 /
-0.95 m (against today's levels +0.45 / -0.28 / -0.45 / -0.66 m). Hours above
today's landside toe (38.30 / 38.50 / 40.00 / 44.90 m) in OYO's design waveform,
linear between its tabulated points: about 14.5 / 38.5 / 35.9 / 22.2 h, against
9 / 21 / 28 / 6 h in 2016. At all three sections OYO flagged, 2016 was both
lower and shorter than the flood OYO assessed.

**OYO's own gradients at the 2016 heads**, scaled in proportion to the head
above today's landside toe (the scaling the adopted translation uses; OYO's own
toe datum differs by a few decimetres, which moves no verdict below): vertical
0.045 / 1.03 / 0.375 / 0.45, horizontal 0.056 / 0.49 / 0.30 / 0.31. Against
OYO's criterion 0.5 and the heave gradient of the cover at the prior mean
(gamma'_bl / gamma_w = 6.9 / 9.81 = 0.70): **only KP 58.8 exceeds either.**
With OYO's designed drains (scaled likewise): KP 58.8 0.24, KP 60.0 0.36,
KP 62.0 (designed, not built) 0.11. Because 2016 was also shorter above the toe
than OYO's design flood, the scaling cannot understate OYO's 2016 value through
duration.

**The engine against OYO at the same head** (`physical-model-qualifications-study.json`,
prior means, under-levee path): the engine's toe gradient is 16.57 / 1.117 /
3.003 / 1.433 times OYO's. This is the same kind of comparison as the four
Japanese field cases (instantaneous translation against the investigators'
seepage model, 1.13 to 2.67), now at the Tokachi sections themselves.

## 4. Arms and definitions

* **OYO-matched toe pressure.** Each section's toe overpressure divided by its
  factor f_s above (16.57 / 1.117 / 3.003 / 1.433), as if undrained; through
  the engine this is the ADR-0050 relief knob at `1 / f_s`, which acts on the
  gate only. Initiation in 2016 and the same-head failure are closed form on
  the persisted rows; the 2016 breach under the reduced gate is an M8 replay of
  the recorded flood with that relief. A diagnostic: OYO's FEM is a design
  model (continuous blanket including the foreshore, unsaturated start), not a
  measurement.
* **OYO's drain designs** on the measured berm: 77 % relief at KP 58.8, 4 % at
  KP 60.0 (closed form on the persisted berm replays).
* **Blanket.** Landside D_bl x 1.5 and x 2 with its own leakage length
  (lambda_in scales as sqrt(D_bl); the foreshore blanket is a fixed geometry
  input), and gamma'_bl x 1.25; closed form, as if undrained.
* **Conductivity and resistance.** Session 2's numbers, quoted, not rerun.
* **Antecedent stage.** The 2016 record at each section in the 48 h before the
  final rise crossed the landside toe.
* **Design-level consequence.** Static (closed form) and transient (one M8 call
  on the canonical event at the design-grid stage) under OYO-matched pressure.

## 5. Predictions (written before any of the numbers in section 4 was computed)

| | Prediction | Basis |
|---|---|---|
| P1 | Under OYO-matched toe pressure the probability that an exit opened in 2016 is below 5 % at KP 57.4, 60.0 and 62.0 and above 90 % at KP 58.8. | At the prior means the divided gate head falls well below the weight head at three sections and stays above it at KP 58.8. |
| P2 | On the measured berm, OYO's 77 % drain relief leaves the 2016 exit share at KP 58.8 below 1 %; the 4 % top-of-cover design leaves KP 60.0's above 95 %. | Session 3: 60 % relief gives 1.4 %, 80 % gives 0; 20 % relief gives 88 % at KP 60.0. |
| P3 | Doubling D_bl lowers the 2016 exit share at every section but leaves it above 25 % at both drained sections; x 1.5 leaves it above 80 % there. A 25 % heavier blanket lowers it less than doubling D_bl. | Weight head doubles, but r_e rises because lambda_in grows by sqrt(2). |
| P4 | In the 48 h before the final rise crossed each landside toe, the mean stage stood no more than 1.5 m below that toe at every section, so the aquifer was largely filled before the final rise. | The earlier typhoon rises approached the toes (thesis Figure 6.1). |
| P5 | Under OYO-matched pressure the design-grid transient probability falls by more than a factor 10 at KP 60.0 (from 0.056) and by less than 25 % at KP 58.8 (from 0.197). | At KP 60.0's design stage the divided prior-mean gate head is 0.38 m against a 0.60 m weight head; at KP 58.8 it is 0.99 m against 0.60 m. |
| P6 | Under OYO-matched pressure the 2016 share held back only by duration (fails the same-head steady-state rule, survives the transient) is below 1 % at KP 57.4, 60.0 and 62.0, and KP 58.8's breach share stays within 10 % of its adopted 3.8 %. | Both require an open exit. |

A failed prediction is reported as failed; none of them decides an adopted
input.

## Part 2: outcome (2026-10-07)

Gates (all held): the closed-form 2016 gate, and the blanket formula at
multiplier one, reproduce every stored initiation flag in the six
section-configuration replays (four as if undrained, two on the measured berm);
an M8 replay of 2016 without relief reproduces the persisted breach and
initiation flags at all four sections; at each design-grid stage an M8 call on
its canonical record reproduces the persisted transient column, and one on the
held stage reproduces the same-head static column, before any arm is
evaluated; the relieved replay's gate equals the closed form; no breach lies
outside same-head failure in any arm.

### 6. What happened at the exit in 2016, per section and reading

Shares of each section's 1e5 prior foundations, matrix reading, recorded 2016
flood. "Duration" is the share that fails the same-head steady-state rule but
survives because the flood fell.

| | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| 2016 peak against today's design level / OYO's 1998 level (m) | +0.45 / +0.15 | -0.28 / -0.58 | -0.45 / -0.76 | -0.66 / -0.95 |
| hours above the toe, 2016 / OYO's design flood | 9 / 14.5 | 21 / 38.5 | 28 / 35.9 | 6 / 22.2 |
| OYO's toe gradient at the 2016 head (criterion 0.5, heave 0.70) | 0.045 | **1.03** | 0.38 | 0.45 |
| exit opened, adopted (as if undrained) | 66 % | 99.6 % | 99.3 % | 40 % |
| exit opened, OYO-matched toe pressure (factor 16.6 / 1.12 / 3.0 / 1.43) | **0** | 98 % | **0.07 %** | **3.3 %** |
| exit opened, toe pressure / 1.13 and / 2.67 (field-case range) | 42 % / 0 | 98 % / 0.7 % | 97 % / 0.5 % | 22 % / 0 |
| exit opened, measured berm with OYO's drain design | | **0** (77 % relief) | 98 % (4 %) | |
| exit opened, D_bl x 1.5 / x 2 / gamma'_bl x 1.25 | 12 / 0.8 / 24 % | 88 / 52 / 94 % | 86 / 47 / 92 % | 6.0 / 0.4 / 11 % |
| exit opened, field-test conductivity mean (session 2) | 1.5 % | 55 % | 62 % | 0.1 % |
| duration, adopted / OYO-matched | 0.37 / 0 % | 24.5 / 24.5 % | 4.9 / 0.01 % | 0 / 0 |
| breach, adopted / OYO-matched | 0.016 / 0 % | 3.81 / 3.65 % | 0.23 / 0 % | 0 / 0 |

Verdicts: **P1 held** (0 / 98.2 / 0.07 / 3.3 %). **P2 held** (0 % at KP 58.8;
97.8 % at KP 60.0). **P3 held** (x 2: 0.8 / 51.5 / 47.1 / 0.4 %; x 1.5 above 80 %
at the drained sections; the heavier blanket always above x 2). **P4 failed**:
the mean stage over the 48 h before the final rise crossed the toe stood 2.67 /
1.63 / 1.37 / 2.58 m below it (minimum 3.76 / 2.26 / 1.87 / 3.59 m), after
coming within 0.21 / 0.05 / 0.09 / 0.21 m of each toe during the preceding week.
**P5 held** (below). **P6 held** (duration 0 / 24.5 / 0.01 / 0 %; KP 58.8
breach 3.65 % against 3.81 %).

### 7. Design-grid consequence of OYO-matched toe pressure (P5)

| | KP 57.4 (39.25 m) | KP 58.8 (41.00 m) | KP 60.0 (42.75 m) | KP 62.0 (46.50 m) |
|---|---|---|---|---|
| exit at the peak, adopted / OYO-matched | 7.7 / 0 % | 99.9 / 99.5 % | 99.9 / **1.3 %** | 99.0 / 82.9 % |
| P_static, adopted / OYO-matched | 0 / 0 | 0.450 / 0.449 | 0.216 / **0.0049** | 0.00106 / 0.00106 |
| P_trans, adopted / OYO-matched | 0 / 0 | 0.197 / 0.196 | 0.056 / **0.00081** (81 rows) | 1.3e-4 / 1.3e-4 (13 rows) |

At KP 60.0 the toe-pressure reading moves the design-level transient
probability 69-fold, comparable with the conductivity bracket there; the
criterion comparison keeps its direction (F_td 6.0, delta-beta 0.57 on 81
transient rows, against 3.88 and 0.81). At KP 58.8 and KP 62.0 the gate
already opens in nearly every failing foundation and nothing moves. Not carried
to annual results: it is a diagnostic on a design model, not a measured toe
pressure.

### 8. The explanation, per section

Pol's logic holds in the model. A pipe that never started cannot be held back
by the flood's short duration, and finite duration explains a non-breach in
2016 only for the 24.5 % of KP 58.8's foundations (4.9 % at KP 60.0, almost
none elsewhere) whose exit opened and whose erosion head exceeded H_c. For the
absence of a recorded boil, the explanation lies before progression:

* **KP 57.4.** The only section loaded above its design level in 2016, but the
  one OYO never flagged for foundation leakage (toe gradient 0.04 at its 1998
  level; 0.045 at the 2016 head; its 1998 deficiency was a rising phreatic
  surface in the landside slope). The model's 66 % exits rest on a toe
  pressure 16.6 times OYO's; nearly every one stalls below H_c. A berm was
  added after 1998. Explained by: no foundation-piping load on OYO's own
  model; in the engine, resistance, not duration.
* **KP 58.8.** The one section where OYO's own model (1.03, above the 0.5
  criterion and the 0.70 heave gradient) and the engine (99.6 %, 98 % with
  OYO's toe pressure) both expect an exit at the 2016 head without works. OYO
  designed a drain cut through the cover that lowers its toe gradient by 77 %,
  which in the model removes every 2016 exit. Explained by: the works, if built
  as designed (the as-built drain is not on record); otherwise a boil would
  have been expected and the record could have missed it. This is also the
  only section where duration matters for the outcome.
* **KP 60.0.** OYO's model gives 0.38 at the 2016 head, below its criterion and
  below heave, and the drain it judged sufficient sat on top of the cover (4 %
  relief, which leaves 98 % exits in the model). The model's 99 % exits come
  from a toe pressure three times OYO's. Explained by: the load (0.45 m below
  today's design level, 0.76 m below OYO's) together with the toe pressure;
  not the drain as designed and not duration.
* **KP 62.0.** Unreinforced, 0.66 m below today's level and 0.95 m below
  OYO's, above its toe for 6 h against 22 h in OYO's design flood; OYO's
  gradient 0.45. In the model 40 % of exits open and every one stalls: no
  foundation's erosion head reached H_c. Explained by: the load. Its survival
  says nothing about whether the works elsewhere were needed or whether this
  foundation is strong.

Across sections:

* **Delayed groundwater.** Elastic lag is excluded (response in minutes, rises
  of hours; ADR-0032). Refilling of an aquifer drained below the blanket is
  not: before the final rise the river stood 1.4 to 2.7 m below the toes on
  average for two days (P4 failed), the Satsunai-confluence base-flow water
  table lies 0.7 to 2.8 m below the top of the gravel, and OYO's design flood
  starts 1.7 to 4.3 m below the toes. The engine's instantaneous translation
  assumes the aquifer full when the river reaches the toe and cannot represent
  the refill; OYO's saturated-unsaturated FEM does. Direction: fewer and later
  exits. Size: not measured. The OYO factor bundles this with OYO's continuous
  foreland blanket, its own cover thicknesses and its geometry; it cannot be
  attributed to any one of them.
* **Blanket.** Thickness matters more than weight because a thicker cover also
  passes more pressure (r_e rises): doubling it nearly removes exits at KP 57.4
  and 62.0 but leaves half at the drained sections. The mapped A_c is the
  adopted thickness; OYO's lumped computational layer is thicker at KP 58.8 and
  62.0, and the landside-toe borings show gravel with fines and no clay at the
  A_c level, so continuity at the exit is uncertain in both directions.
* **Conductivity and resistance.** The field-test conductivity mean lowers
  exits (55 and 62 % at the drained sections); no H_c allowance (grading,
  gravel, the bulk d70) changes them (session 2).
* **What the exit ejects.** Whether an opened exit in this gravel would carry
  sand or pass clear water is outside the model (session 2: Deltares 2022 on
  the Limburg gravels, much seepage, few sand-carrying boils).
* **The record.** "No boil recorded", of unknown completeness (session 3).

### 9. The Tokachi and the Tokoro

| | Tokoro boil reach, 2016 | Tokachi study sections, 2016 |
|---|---|---|
| Load | at the Futochanae gauge above the design level for 32 h 40 min, peak about 1.84 m above it; largest discharge on record | below the design level at the three sections OYO flagged (0.28 to 0.66 m; 0.58 to 0.95 m below OYO's level); above the toe 6 to 28 h |
| Eroding layer | thin sand (0.4 to 1.0 m, k about 1e-5 m/s) continuous from an exposed bank, at old channels and confluences | 7 to 10 m of gravel with a sand matrix (adopted k 1 to 3e-3 m/s; field tests about 6e-5 m/s) |
| Cover | about 1 m of cohesive soil (k 1e-7 m/s), locally thin where boils broke out | 0.45 to 0.85 m of sandy silt (k about 1e-6 m/s), gravelly at the landside toe |
| Investigators' gradient | 0.70 and 0.87 at a boiling site, under the 2016 flood | OYO's 1.03 / 0.38 / 0.45 at the 2016 heads (KP 58.8 / 60.0 / 62.0), before any works |
| Works | not examined here; flood fighting ringed the KP 24.6 boil (committee p. 5-17) | berm (57.4), berms and toe drains (58.8, 60.0), none (62.0) |
| Observation | reach surveyed by its committee, test pits | committee covered the breaches only; no record either way |

What the contrast shows: the decisive difference is the load relative to what
each levee was assessed for, about 2 m, followed by the eroding layer, the
works and the observation. What it does not show: that the Tokachi foundations
resist better, or that flood duration protected them. Where the Tokoro boiled
without breaching, duration (or resistance along the path) could be the
reason; no Tokoro calculation was made here.

### 10. What this means for the thesis

1. The 2016 survival does not say that short floods protect these levees. The
   motivation "strong foundations, or floods too short to complete" must also
   name the load (below the design level at three sections), the works and the
   toe pressure, and state that duration counts only where an exit opened.
2. The effect of duration that the thesis measures belongs to floods at and
   above the design level, where exits open in nearly every foundation as if
   undrained; that is where the annual probability is earned. Under OYO's toe
   pressure this still holds at KP 58.8 and KP 62.0 but not at KP 60.0.
3. The toe-pressure translation joins the conditions on absolute probability:
   at KP 60.0's design level a design-model toe pressure lowers the transient
   probability 69-fold. It also leans the same way as the other adopted
   choices (matrix d70, analysis-constant conductivity, uniformity at its
   calibration, no gravel allowance, drains inert): every comparison of the
   instantaneous translation with an investigators' seepage model, at the
   Japanese field sites and now at the four Tokachi sections, finds it predicts
   the higher toe pressure (1.1 to 16.6 times).
4. Appendix A.1's sentence that the Satsunai-confluence water tables are "a
   field basis for the saturated initial condition" over-reads them: they show
   a flat, river-connected water table, but 0.7 to 2.8 m below the top of the
   gravel. Corrected in the thesis. ADR-0032's scope amendment names the
   regime correctly ("initial heads well below the exit datum"), but its
   statement that all four sections were confirmed outside it rested on the
   river's base-flow trough, which lies 1.7 to 4.3 m below the toes; a dated
   note is added there.

### 11. What stays as it was

No adopted input changes. The OYO-matched toe pressure, OYO's drain designs,
the blanket arms and the antecedent check are named diagnostics. Not done: a
transient-fill (unsaturated) aquifer model, a Tokoro calculation, and carrying
the OYO-matched toe pressure to the annual results.
