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
