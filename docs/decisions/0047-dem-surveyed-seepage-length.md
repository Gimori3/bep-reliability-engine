# ADR-0047: DEM-surveyed seepage length L — adopted at KP 62.0, held elsewhere

Date: 2026-07-28 (adoption decision 2026-07-29)

## Status

**Accepted in part** (project-owner decision of 2026-07-29, recorded with the
evidence that grounded it). The measurement and its method are accepted in full.
The adoption is **partial and deliberate**:

* **KP 62.0 — ADOPTED.** `data/processed/tokachi_bep_inputs.csv` `L_m` 47.0 → **40.0**
  (one cell). The full campaign re-run was executed; the scope is tabulated in
  Consequences.
* **KP 57.4, KP 58.8, KP 60.0 — HELD at their 1998 values.** Their DEM measurements
  are carried as the measured, unadopted epistemic bracket on `L`.
* `seepage_length_cov` is **unchanged everywhere** (0.20; 0.15 at KP 60.0), and no
  `Config` field, `to_metadata()` key or hash surface was added or altered.

Companion to **ADR-0033**
(GSA: L is the top total-effect input), the **seepage-length L study**
(`docs/decisions/seepage-length-L-study.md`, which kept the L model unchanged and
named better data as the only route to reducing its variance share), **ADR-0021**
(surveyed `z_toe`) and **ADR-0025** (foreshore width, which established that `B_f`
is inert and `L` is the input actually worth measuring). Parent decisions unchanged.

---

## Context

`L` is the highest-value poorly-constrained input in the model, on three independent
lines:

1. **ADR-0033 (GSA)** ranks the stochastic seepage length the **top total-effect
   input for every QoI at every conditioning level**, ST_L ≈ 0.49–0.78.
2. The **seepage-length L study** (2026-07-19) measured the transient shoulder P_f
   as **3–4× sensitive to CoV(L)** over 0.10–0.40, with deterministic-L
   under-predicting the shoulder 3–5×.
3. That same study established the **Phase 2 ceiling**: the 2016 survival barely
   moves L (production posterior mean +0.5–1.4%, CoV −1.7 to −3.6%) while k_aq and
   C_e shift ≈ −4%. The L variance share is therefore **irreducible by the θ-only
   Accept–Reject filter**. Better data is the only route.

Meanwhile `docs/tokachi_bep_inputs_provenance.md` §3.1 concedes in as many words
that the four production values — 33.0 / 35.0 / 34.8 / 47.0 m at KP 57.4 / 58.8 /
60.0 / 62.0 — are *"explicit engineering-judgement estimates, **not surveyed values
of L**"*, read off 1998 OYO 様式-5/-6 dimension chains.

A GSI 基盤地図情報 **DEM5A** airborne-lidar surface (secondary mesh 644331,
`devDate` **2025-06-20**, `orgMDId` R05GC0022, 100 tiles) covering all four sections
is now on disk. This ADR records what it measures, how, and what that would do to
the production fragility.

**The vintage mismatch is the substance, not a nuisance.** The DEM surface is 2025;
the CSV geometry is 1998, pre-remediation. Provenance §3.2 records the landside
works between those dates (Fukuda type map: KP 57.4 `berm-only` 側帯盛土; KP 58.8
and KP 60.0 `drained`, types ④+⑤ berm + toe drain; KP 62.0 `unreinforced`), and
§3.1 predicts that for `berm-only` nodes the current path is longer "order +10 to
+30 m", while "for the `unreinforced` node KP 62.0 the 1998 value stands". A
DEM-vs-CSV difference is therefore a **testable prediction**, not simply an error.

Two hard constraints frame any such measurement:

* **`L` is the under-levee confined path only** — riverside levee toe to landside
  levee toe. The foreland is carried separately through `λ_out` inside `r_e`
  (ADR-0005/0006), so folding the foreshore into `L` would double-count the
  foreland resistance. The 高水敷幅 must be reported *beside* `L`, never inside it.
* **`geometry.L` is inside `Config.to_metadata()` and therefore inside
  `config_hash()`**, and `bayesian_reliability_updating/replay.py::load_phase1_run`
  refuses hash drift. Changing the CSV invalidates all 8 persisted Phase 1 sweeps,
  the Phase 2 production posterior, and the Phase 3 campaign built on them.

---

## Decision

1. **Measure `L` from the DEM in committed, deterministic code** —
   `scripts/dem_cross_section_study.py`, no GUI step anywhere in the path. The
   script parses the JPGIS(GML) tiles into a mosaic, chains the levee alignment
   from `data/raw/gis/SECTIONS.shp` (EPSG:2455, inverse-projected in-repo — no
   geospatial dependency is added), places each profile **perpendicular to the
   local alignment tangent**, samples at 1 m posts by bilinear interpolation from
   inside the low-water channel to 400 m landward, and picks crest and toes by an
   explicit rule. Sampled profiles are written to
   `data/raw/geometry/dem_cross_sections/` (gitignored) so later steps need not
   re-parse; the mosaic cache is a pure accelerator and the whole result is
   regenerable from the tiles alone.

2. **The toe rule is stated, not hand-picked, and its sensitivity is reported.**
   The crest is the maximum within ±40 m of the alignment; the *crest band* is the
   contiguous run within 0.5 m of it. From each band edge the walk proceeds
   outward — with the slope evaluated **in the direction of travel on both sides**
   — and declares a toe at the first point that is ≥1.5 m below the crest and at
   which the outward slope stays above −0.10 (1:10) over 8 m. `L` is the resulting
   toe-to-toe distance. Two landside conventions are carried: the **outer** toe
   (walking past a berm, capped at 40 m beyond the embankment toe) is primary,
   because a berm is fill resting on the same blanket and lengthens the confined
   path — and is the convention the 1998 chains used ("toe-to-toe **incl. landside
   berm**" at KP 62.0); the embankment-only toe is reported alongside. The
   discretionary threshold is swept over {0.05, 0.075, 0.10, 0.15, 0.20} and the
   spread reported.

3. **The headline per section is a chainage-window median, not a single transect.**
   The KP anchor is reproducible (arc length along the chained SECTIONS.shp
   alignment, controlled by the ADR-0043 section spans) but not exact — the levee
   is not the river centreline the KP is measured along — and cross-correlating the
   DEM against the 2019 and Uemura longitudinals localises it only to ≈±150 m.
   Each section is therefore re-measured at 31 stations over ±300 m at 20 m
   spacing. This brackets the anchor uncertainty *and* yields the along-levee
   spread of `L`, which is an empirical CoV the seepage-length L study had no data
   for. Two uniform screens, applied identically at every section against
   independent committed data, reject stations where the levee footprint is not
   separable from adjacent or superimposed fill: a **landside-structure** screen
   (a separate embankment ≥1.5 m above landside ground standing clear of the toe)
   and a **raised-crest** screen (crest more than 0.5 m from the window's own
   median excess over the 2019 design bank height).

4. **The datum is gated before any length is believed.** The DEM crest, landside
   ground and riverside terrace are compared against three independent committed
   series over the whole reach; a mean offset above 1.0 m raises and stops the run.

5. **No input value changes in this pass.** `data/processed/tokachi_bep_inputs.csv`
   and `configs/*.yaml` are read-only to this study; the fragility arms override
   `geometry.L` in memory only, exactly as `scripts/foreshore_width_study.py`
   overrides `geometry.foreshore_width`. This is pinned structurally by
   `tests/test_dem_cross_section.py::test_the_study_never_writes_the_committed_inputs_csv_or_configs`.
   **Adoption of a DEM-surveyed `L` is a separate, explicitly authorised decision**,
   to be taken on the evidence recorded here and at the re-run cost tabulated in
   Consequences.

6. **The 高水敷幅 is a reported by-product and is never added to `L`** — pinned by
   `test_high_water_bed_width_is_reported_beside_L_and_never_inside_it`.

7. **No new `Config` field, no new knob, no production default touched.** Nothing
   here is persisted into `results/` as a deliverable, and no config hash moves.

---

## Alternatives Considered

### Alternative 1 — extract the profiles interactively in QGIS
Pros: no code to write; visual control of each transect.
Cons: QGIS cannot open JPGIS(GML) `.xml` natively (which is why the original
attempt appeared to fail); a GUI step in the middle of a thesis pipeline is not
reproducible, cannot be re-run by an examiner, and cannot carry a toe rule whose
threshold sensitivity is measurable. **Rejected** — the GML DEM is a trivially
parseable text grid and the extraction belongs in a committed script like every
other input path in this repo.

### Alternative 2 — adopt the DEM values immediately and re-run the campaign
Pros: puts the best available geometry into the model at once.
Cons: it would spend the entire persisted campaign (8 Phase 1 sweeps, the Phase 2
posterior, the Phase 3 RQ3/RQ4 results, and every companion study that asserts
bit-identity against those sweeps) on a measurement whose 1998-vs-2025 vintage
question is not resolved by the DEM itself, and at three of four sections the
difference has a **remediation** explanation rather than an error explanation.
**Rejected for this pass** — measure first, decide separately (Decision 5).

### Alternative 3 — take the DEM's riverside-toe-to-channel distance into `L`
Pros: a single "wetted path" number, superficially simpler.
Cons: double-counts the foreland resistance already carried by `λ_out` inside
`r_e` (ADR-0005/0006), and contradicts the definition every other artifact uses.
**Rejected** — this is the single most likely way to get the task wrong, so it is
pinned by a test rather than left to discipline.

### Alternative 4 — use the surveyed L to justify a narrower CoV(L) prior
Pros: CoV(L) is the dominant epistemic knob at the shoulder (3–4× over 0.10–0.40);
halving it would be worth more than moving the mean.
Cons: the seepage-length L study established that the assigned 0.20/0.15 is **not**
dominated by base-width reading error (which alone implies 0.08–0.16) but by the
**unverified position of the landside blanket boundary** and the possibility that
the effective exit lies beyond the toe — neither of which a surface DEM can see.
**Rejected as stated**: the DEM converts the base-width term from judgement into
measurement, but leaves the epistemic padding untouched. See Rationale.

### Alternative 5 — report a single nominal-station transect per section
Pros: one number per section, easy to tabulate.
Cons: hides the residual ±150 m chainage-anchor uncertainty entirely, and at
KP 57.4 the nominal station happens to sit on a road interchange embankment, so the
single transect would have reported 68 m — roughly double the CSV value — as a
survey. **Rejected** in favour of the window median plus screens (Decision 3).

---

## Rationale

### The adoption principle: adopt where the 1998 value is *wrong*, hold where it is merely *old*

The four sections do not present the same kind of disagreement, and treating them
uniformly — adopting all four or holding all four — would be the error.

**KP 62.0 is a defect, not a vintage difference.** Its 47.0 m is recorded in
provenance §3.1 as *"toe-to-toe **incl. landside berm**, 18 + 29.1"*. That berm:

* was **not modelled by the 1998 OYO 様式-5 sheet the L memo itself read the chain
  from** — that sheet models a plain trapezoidal levee and leaves 浸透対策工 blank;
* is **denied by the `unreinforced` classification**, confirmed in §3.2 on three
  independent lines, **all three of which bear on berm presence** (the toe *drain*
  is §3.2's explicitly stated residual, and a buried drain would only lower P_f);
* is **not present on the 2025 surface** — at 28 of 28 clean stations the outer toe
  equals the embankment toe, the landside shape is crest → ~1:3 face → toe → level
  ground with no bench, and the 40 m is stable under an outer-toe cap sweep from
  40 m to 120 m (median 40 / 40 / 40 / 41 m).

The berm was therefore **not there in 1998 either**. This is not a geometry that time
overtook; it is a value that was wrong when it was written, and wrong in the
**under-conservative** direction at the **governing** section. That is what makes it
adoptable on evidence rather than on preference.

**KP 58.8 and KP 60.0 are the opposite case.** Their +7 and +8 m are real, measured
on 31 of 31 clean stations each, and they have a *legitimate* explanation: the
geometry genuinely changed under the post-1998 berm-and-toe-drain works recorded in
§3.2. That raises a "which levee are we assessing?" question — and the rest of the
CSV answers it "1998", consistently, column by column. Adopting the 2025 `L` at
those two sections would also adopt **only the anti-conservative half of those
works**: the longer seepage path is credited while the engine still models **no toe
drain** (`remediation_state` is a label, not physics). A partial credit of a
remediation is not an improvement on a consistent 1998 baseline.

**KP 57.4 has nothing resolvable** — 6 clean stations of 31, CoV 0.60, an apparent
difference smaller than the extraction rule's own ≈ −2 m bias.

**A corollary worth recording: this outcome *confirms* provenance §3.2's
`unreinforced` classification rather than challenging it.** §3.2 closed that
sub-item on three independent lines; the 2025 DEM survey is a **fourth**, arrived at
independently, with a stated rule, at 28 stations, and it agrees. What it overturns
is §3.1's seepage-length entry, which had quietly assumed a structure §3.2 says is
absent.

**On not bias-correcting, and on holding CoV(L).** The extraction rule's ≈ −2 m
window bias means the true 2025 footprint is nearer 42 m than 40 m, so the adopted
**40 m is the conservative end of the measurement**. It is adopted uncorrected,
deliberately: a bias correction would be an unmeasured adjustment layered on a
measured quantity, and its direction favours safety. Similarly `seepage_length_cov`
stays **0.20**: the measured along-levee spread at KP 62.0 is 0.102, but the prior's
padding above the base-width term covers the **unverified landside blanket boundary
and exit position**, neither of which a bare-earth lidar surface can observe.
Narrowing the prior on a surface measurement would be claiming knowledge the survey
does not contain.

**The datum gate passes with room to spare**, on three independent series over 551
stations spanning KP 57.3–62.9: DEM crest vs the 2019 `DesignBankHeight_R`
**+0.30 ± 0.55 m**; DEM landside ground vs Uemura `ground_m_msl` **−0.65 ± 0.68 m**;
DEM riverside terrace vs Uemura `floodplain_m_msl` **−0.24 ± 0.73 m**. GSI 標高 and
the engine's m T.P. datum agree, so lengths measured on this surface are
trustworthy. The residual +0.30 m on the crest is the ordinary as-built over-build
above design and is exactly why the raised-crest screen is anchored to the window
median rather than to the design profile.

**The extraction is validated before its `L` is believed**, per the two checks that
do not depend on the answer:

* **`z_toe` (ADR-0021, ±0.3 m).** DEM landside outer-toe elevation minus the
  surveyed toe: **−0.15 m (KP 58.8), −0.38 (KP 60.0), +0.36 (KP 62.0), −0.85
  (KP 57.4)**. Three of four sit within about a decimetre of the ADR-0021 band on a
  5 m raster whose own reach-scale scatter is ±0.55–0.73 m; the outlier is KP 57.4,
  which the screens independently flag as contaminated.
* **Perpendicularity.** Scanning the profile azimuth ±30° and locating the `L`
  minimum — the true perpendicular — puts the adopted alignment normal within 2° at
  three sections and 6° at KP 60.0, i.e. an obliquity inflation of
  **1.001 / 1.001 / 1.006 / 1.001**. The 1/cos θ artefact that would masquerade as
  a real widening is measured and absent.

**The measured differences follow the remediation history, which is the strongest
single result here.** Window medians over clean stations, against the 1998 CSV:

| Section | `remediation_state` | CSV 1998 | DEM 2025 | Δ | clean stations | along-levee CoV |
|---|---|---|---|---|---|---|
| KP 57.4 | `berm-only` | 33.0 | *no resolvable change* | — | 6/31 | 0.60 |
| KP 58.8 | `drained` | 35.0 | **42** | +7 | 31/31 | 0.073 |
| KP 60.0 | `drained` | 34.8 | **43** | +8 | 31/31 | 0.184 |
| KP 62.0 | `unreinforced` | 47.0 | **40** | −7 | 28/31 | 0.102 |

**KP 57.4 yields no adoptable number.** Its screened median is 36.5 m against 33.0,
but on **6 surviving stations of 31** with an along-levee CoV of **0.60**; the
apparent +3.5 m is smaller than the rule's own ≈ −2 m bias and far inside the
station scatter. It is recorded as *no measurable change*, never as "+3 m".

The two `drained` sections — where the Fukuda type map records berm + toe drain
works after 1998 — show a **longer** 2025 footprint, +7 and +8 m, on 31 of 31 clean
stations each. The `unreinforced` section shows no lengthening at all; it measures
*shorter*. That is provenance §3.1's own prediction for the `drained` nodes,
arrived at from an independent 2025 surface, and it is a genuine corroboration of
the `remediation_state` column.

**KP 57.4 delivers a negative result, not a value.** Its nominal station sits on a
road interchange embankment (the crest stands +1.6 m above the 2019 design crest
over a ~200 m band, and a second embankment stands 40–100 m landward of the toe
further downstream). With every station taken, the window median is 67 m — a
doubling of the CSV value that would look like a spectacular confirmation of the
"+10 to +30 m" prediction and is **road fill, not levee**. So the finding is that
**§3.1's "+10 to +30 m" berm-only prediction does not hold for the levee proper**:
wherever the levee can be measured free of road fill its 2025 footprint is
indistinguishable from the 1998 value. Both readings are driven through the engine
as labelled arms so the ambiguity is bracketed by measurement rather than argued,
but neither is offered for adoption.

**The rule carries a known, quantified, conservative bias.** The finite
forward-difference slope window declares a toe up to
`SLOPE_WINDOW_M × threshold / face_slope` early — 1 m per side for a 1:3 face at
threshold 0.10 on 1 m posts, i.e. `L` short by ≈2 m, pinned exactly against a
synthetic trapezoid by
`test_pick_cross_section_recovers_a_synthetic_trapezoid`. The direction is
conservative for piping (a shorter `L` raises P_f), so it is reported rather than
corrected by an ad hoc offset. The threshold ladder spread is 6–7 m at the two
clean sections (KP 58.8, KP 62.0) and 24–25 m at KP 57.4 and KP 60.0, where the
0.05 rung walks onto adjacent flats.

**On CoV(L) (Alternative 4).** The along-levee spread at the clean sections is
CoV **0.073 (KP 58.8)**, **0.184 (KP 60.0)**, **0.102 (KP 62.0)** — bracketing the
0.08–0.16 that the seepage-length L study derived from base-width reading scatter
alone, and sitting below the assigned 0.20 at two of three. This is a real
measurement where there was previously none, and it **confirms the base-width
component of the prior**. It does **not** license narrowing the prior: that study
established the assigned padding to 0.20 covers the *unverified landside blanket
boundary* and the possibility that the effective exit lies beyond the toe — neither
of which a bare-earth surface can observe. The honest statement is that the DEM
converts one term of a lumped allowance from judgement into measurement and leaves
the other intact.

**The 高水敷幅 by-product is reported and is inert.** DEM widths are 102 / 288 /
546 / **236** m against the ADR-0025 verified 1998 values 200 / 325 / 600 / **44** m.
Three sections agree in magnitude and direction (all slightly narrower in 2025);
KP 62.0 is 5.4× wider. This does **not** reopen ADR-0025, for a reason that ADR
already measured: at KP 62.0 the foreland tanh is saturated, "any B_f ≳ 100 m is
numerically identical, so 44 vs 250 m is worth 5e-5", and the full open-entry
excursion B_f → 0 moves transient P_f by only 0.00023 there with static P_f exactly
0. A *wider* foreshore lies on the saturated side, so the DEM reading is worth less
than that. The observation is recorded as a morphological note (the 2025 surface
shows a broader terrace at KP 62.0 than the 1998 and 2008 sheets), not as an input
question.

---

## Consequences

**Nothing in the engine changed.** No `Config` field, no default, no config hash,
no persisted artifact. `ruff`, `black` and the full suite are green (see the
companion note for the count). The eight persisted Phase 1 sweeps remain valid and
every baseline arm in the fragility stage was asserted **bit-identical** to its
persisted sweep before any sensitivity was reported.

**The measured fragility consequence is large** — as ADR-0033 predicted, since L is
the top-ranked input. Matrix d70, N = 1e5, 225 s, `geometry.L` overridden in memory
only, every baseline arm asserted bit-identical to its persisted sweep first:

| Section | CSV L | DEM L | ΔL | max \|ΔP_f\| trans (stage, m MSL) | max \|ΔP_f\| static | direction |
|---|---|---|---|---|---|---|
| KP 57.4 | 33.0 | 36.5 | +3.5 | **0.132** (41.25) | 0.135 | ↓ |
| KP 57.4 | 33.0 | 67.0 *(road fill)* | +34.0 | **0.749** (42.25) | 0.770 | ↓↓ |
| KP 58.8 | 35.0 | 42.0 | +7.0 | **0.232** (41.75) | 0.240 | ↓ |
| KP 60.0 | 34.8 | 43.0 | +8.2 | **0.279** (43.50) | 0.304 | ↓ |
| KP 62.0 | 47.0 | 40.0 | −7.0 | **0.201** (50.00) | 0.214 | ↑, up to **15×** in the tail |

This is what the adoption decision turns on, and it is a categorically different
situation from the ADR-0025 foreshore question that preceded it. There the
*bounding* `B_f → 0` excursion moved transient P_f by 0.00111 / 0.00170 / 0.00440 /
0.00023 with static **exactly** 0, so retaining the 1998 value cost nothing
measurable. Here a change well inside the prior's own CoV 0.20 band moves **both**
branches by 0.13–0.28 — a per-section ratio of **119× / 137× / 64× / 874×** — because `L` enters `H_c`, the rate denominator,
`r_e` *and* the criterion `Z = L − l_e`, where `B_f` since ADR-0028 touches only the
uplift/heave gate. Adopting `L` is therefore a **re-run**, not an amendment: no
persisted number survives it.

Two readings must travel with those numbers. All maxima lie **above the design
HWL** (the transition sits above HWL at these sections), and the KP 62.0 maximum at
50.00 m MSL falls above the crest inside the ADR-0024 hypothetical fit-stabiliser
extension, which must never be plotted as attainable — the design-relevant statement
there is the ratio (P_f raised at every level with a positive baseline, 1.02–15×).
And the KP 62.0 sign is the safety-relevant one: it is the only section where the
DEM is *shorter* than the adopted value, and it is the governing `unreinforced`
section.

**The static-vs-transient bias ratio does NOT survive the L change — this is the
decisive result.** The thesis defends ratios, and ADR-0048 claimed that an
epistemic bracket can dominate absolute P_f while cancelling in the Stage 6.6
static-vs-transient ratio (as it believed its k_aq bracket did — **that claim was
refuted on 2026-07-30; see the amendment at the end of this ADR**). **The L bracket
does not cancel.** Ratio of ratios ρ = (P_s/P_t)_DEM ÷ (P_s/P_t)_CSV, paired bootstrap over
the joint pattern counts (2000 replicates; null case pinned at ρ = 1.0 exactly;
baselines gated on the **whole failure matrices**, not column means), at design HWL:

| Section | ΔL | S/T ratio CSV → DEM | ρ | 95 % CI |
|---|---|---|---|---|
| KP 57.4 | +3.5 | 35.97 → 80.92 | **2.250** | [1.471, 4.465] |
| KP 58.8 | +7.0 | 2.75 → 4.51 | **1.642** | [1.617, 1.667] |
| KP 60.0 | +8.2 | 2.92 → 6.49 | **2.226** | [2.193, 2.261] |
| KP 62.0 | −7.0 | **27.87 → 13.23** | **0.475** | [0.263, 0.724] |

**All 87 evaluated levels across the four adoption-relevant arms are resolved at
95 %.** The mechanism is structural, not incidental: both branches share `H_c`, but
`L` additionally enters the transient limit state through the progression distance
`Z = L − l_e(t)` and the ODE rate denominator, so a change in `L` is **not a
common-mode shift** — it moves the transient branch harder than the static one. The
Stage 6.6 headline bias figures (~21× at KP 62.0, ≥32× at KP 57.4 per event at HWL)
are consequently **L-conditional and must be quoted as such**: under the DEM
geometry the KP 62.0 bias roughly halves and the KP 57.4 bias roughly doubles.

**ADR-0024 deliverable form.** All four matrix transients are already
`fitted_lognormal` with the transition bracketed, KP 62.0 included, so no form flip
occurs there (it stays fitted, max raw P_f 0.9698 → 0.9901). The only form change
anywhere is the contaminated KP 57.4 road-fill arm losing its bracket, which is not
a candidate for adoption. The real presentational change at KP 62.0 is hidden by the
label: its transition is bracketed only inside the ADR-0024 hypothetical above-crest
extension, and shortening `L` moves mass into the attainable range — P_f,trans at
HWL 0.00015 → 0.00130 (×8.7), at design crest 0.0194 → 0.0622 (×3.2).

**KP 62.0 has no landside berm in 2025, and that makes its −7 m a correction rather
than a bracket endpoint.** §3.1 records the 1998 `L = 47 m` as "toe-to-toe **incl.
landside berm**"; §3.2 records the section as `unreinforced`, confirmed on three
independent lines. Those cannot both hold. The 2025 surface resolves it: at all 28
clean stations the outer toe **equals** the embankment toe (no berm to walk past);
the landside shape is crest → ~1:3 face → toe at +21 to +33 m → level ground, with
no bench; and the 40 m is not an artefact of the 40 m outer-toe cap — raising that
cap to 60 / 80 / 120 m leaves the clean-station median at 40 / 40 / 41 m. Moreover
**all three of the §3.2 confirmation lines bear on berm presence** (the 1998 様式-5
models a plain trapezoid with 浸透対策工 blank; the earlier DEM inspection found "no
intermediate bench"; the plan-sheet 側帯 is a 第二種 stockpile pad, not a seepage
berm) — it is the **toe drain** that §3.2 leaves explicitly unresolved, and a buried
drain would only lower computed P_f. The coherent reading is that the L memo
credited a berm that its own source sheet did not model and that has never been
there, and that **the production model is under-conservative at the governing
section**.

**Re-run scope, AS EXECUTED (2026-07-29).** The adoption at KP 62.0 was carried out
end to end. Consumers were enumerated **programmatically** (grep for the KP 62.0
sweep paths, for `results/tokachi_kp*` globs, and for the bit-identity / config-hash
assertion patterns across `scripts/`, `tests/` and the three packages) rather than
from memory; seven candidates were found and every one was re-run or re-pinned:

| Artifact | Action | Outcome |
|---|---|---|
| `data/processed/tokachi_bep_inputs.csv` | one cell edited | KP 62.0 `L_m` 47.0 → 40.0 |
| `configs/*.yaml` | `generate_configs.py` | **exactly 2 files changed, single `L` field each** (gate) |
| `tests/test_configs.py` | re-pinned | new `_SEEPAGE_LENGTH_M` absolute pin citing this ADR |
| Phase 1 sweeps | re-run | both KP 62.0 strata, N = 1e5 |
| Phase 2 posterior | re-run `--verify` | **rejection 0.00 % both strata; nesting result holds** |
| Phase 3 campaign | re-run | 20 of 2280 RQ4 rows changed, all KP 62.0 (containment gate) |
| `stage6_6_gap_decomposition.py` | re-run (kp62_0) | drift guard **bit-identical at 38 levels**; all Euler flips 0 **at the production N = 1e5** (KP 62.0 also stays clean at N = 1e6; KP 57.4 does not — 4 rows in 1e6, `adr0040-hwl-bias-resolution.md` §2.7) |
| `foreshore_width_study.py` | re-run (4 sections) | KP 57.4/58.8/60.0 reproduce exactly; KP 62.0 0.00023 → 0.00024 |
| `assess_2011_2006_closure.py` | re-run (8 strata) | **all eight reproduce exactly**, KP 62.0 still 0/100 000 |
| `segment_fragility.py` | re-run | ADR-0037 segment tables regenerated |
| `seepage_length_study.py` | re-run (`all`) | KP 62.0 now at L = 40.0; ceiling analysis unchanged |
| `foreshore_exhaustion_study.py` | re-run | **byte-identical** (physics-free, B_f only) |
| `dem_cross_section_study.py` | re-pinned + verified | drives the **withdrawn 47.0 m** arm; reproduces 0.20106 |
| ADR-0045 / 0046 / 0048 companions | checked, not re-run | **KP 58.8 + KP 60.0 only** — neither adopted |
| `qa_re_halved_member.py` | checked, not re-run | KP 58.8 only |
| Documents of record | updated | provenance §3.1/§3.2, `architecture.md` §7/§13, `phase2_report.md` §14, `phase3_report.md` §11, `stage6_6_report.md` §8, project-notes.md, msc-thesis Ch. 3 + Ch. 7 |

Superseded artifacts retained under `results/superseded_adr0047_L47/`.

**Headline numbers that moved** (all KP 62.0; every other section unchanged):

* transient P_f at design HWL **1.5e-4 → 1.3e-3** (×8.7); at design crest ×3.2;
* Stage 6.6 conventional-practice bias: nominal HWL value 21.0 → 44.7, **but neither
  is resolved** (1 and 4 failing rows); where counts are adequate the bias **falls**
  by ≈ ⅓ (15.0 → 10.5 at 47.0 m MSL, 9.9 → 6.3 at 47.5, 3.7 → 2.4 at 49.0);
* Phase 3 RQ3 dominance: BEP 0.637 → **0.812** historical; at +4K 0.344 → **0.500**,
  so **overflow no longer leads at KP 62.0 under +4K**;
* Phase 3 RQ4: annual system P_f 5.24e-4 → **1.01e-3** historical, 1.02e-2 →
  **1.28e-2** at +4K, so the **climate ratio falls 19.5 → 12.7**;
* Phase 2: rejection **unchanged at 0.00 %**.

**Original cost estimate, retained for the record** (this is what Decision 5 deferred):

| Artifact | What must be redone |
|---|---|
| `data/processed/tokachi_bep_inputs.csv` | edit `L_m`; every downstream hash changes |
| `configs/*.yaml` (8) | `python scripts/generate_configs.py` — never hand-edited |
| `tests/test_configs.py` | drift-guard pins the CSV-derived `geometry.L`; must be updated in the same change, citing this ADR |
| Phase 1 sweeps (8) | full re-run, N=1e5, 225 s (`scripts/run_sweep.py`) |
| Phase 2 posterior | full re-run across 8 strata with `--verify`; the replay hash gate refuses the old files |
| Phase 3 campaign | `scripts/phase3_campaign.py` (BEP curves change; the hazard cache does not) |
| Companion studies asserting bit-identity | `foreshore_width_study`, `seepage_length_study`, `qa_re_halved_member`, `stage6_6_gap_decomposition`, `ce_prior_study`, `mp_model_factor_companion`, `ztoe_sensitivity_study`, `gsa_study`, `assess_2011_2006_closure`, `plot_fragility_curves` — each re-run and its recorded numbers re-issued |
| Documents of record | `docs/phase2_report.md`, `docs/phase3_report.md`, `docs/stage6_6_report.md`, `docs/decisions/seepage-length-L-study.md`, ADR-0033/0037/0040–0046 quantitative statements, the `_thesis_*.tex` fragments and the msc-thesis chapters |

**Scientific interpretation, stated with its conditioning.** The DEM measures the
**2025 topographic footprint of the levee embankment**. It does not measure the
blanket boundary, the aquifer geometry, or the effective exit point, which
provenance §3.1 and the seepage-length L study both name as the dominant residual
uncertainty in `L`. A DEM-surveyed `L` would therefore be *better constrained* than
the 1998 chain reading, not *exact*; and at the two `drained` sections it would be
a **2025** geometry entering a model that evaluates the **unremediated** foundation
(`remediation_state` is a label, not physics — 2026-07-28 correction in provenance
§3.1, `docs/phase2_report.md` §11). Adopting the longer 2025 `L` at KP 58.8 and
KP 60.0 while continuing to model no drain is a defensible conservative choice, but
it is a *choice*, and it must be stated as one rather than presented as a
straightforward data improvement.

**KP 63.4** is untouched: it is excluded from the confined-BEP population and its
`L = 26.9 m` remains the flagged forced proxy of provenance §3.1.

---

## Amendment — 2026-07-30: the k_aq contrast is withdrawn; the L result is not

This ADR frames its §4.5 result by contrast with ADR-0048: L was said to be unusual
in *not* cancelling in the static-vs-transient ratio, where k_aq was believed to
cancel. **The contrast is withdrawn.** ADR-0048 consequence 3 was refuted by direct
measurement on 2026-07-30 (`docs/decisions/epistemic-bracket-synthesis.md` §4(c),
using this ADR's own §4.5 paired-bootstrap statistic, imported rather than
re-implemented): k_aq's maximum resolved ratio-of-ratios departure is
×82.2 / ×65.6 / ×162.9 / ×45.6 at KP 57.4 / 58.8 / 60.0 / 62.0 — **larger than the L
bracket's** ×2.25 / ×1.82 / ×3.22 / ×2.11 measured here.

**Nothing measured in this ADR changes.** The L ratio-of-ratios values, their CIs,
the 87/87 resolution and the adoption decision all stand, and were reproduced
independently by that later study three ways (KP 60.0 ρ = 2.226; KP 57.4 max
departure 2.250; KP 62.0 max departure 2.106 = 1/0.475).

What changes is the *generality*: §4.5's mechanism argument — that a knob fails to
cancel when it reaches the transient branch through a channel the static branch does
not have — turns out to be the **general rule**, not a peculiarity of L. k_aq has two
such channels (`r_e` → uplift/heave gate; the ODE rate) where L has one, which is why
it departs further. The only knob measured to cancel is `m_p` (×1.07–1.22), which is
pure common-mode by ADR-0045 §2 construction. Consequently the Stage 6.6 bias
headlines are **k_aq-conditional as well as L-conditional**, and the k_aq
conditionality is the larger of the two.

**Also superseded 2026-07-30: the bias magnitudes this ADR quotes.** The
"~21× at KP 62.0, ≥32× at KP 57.4" of §4.5 and the "21.0 → 44.7, but neither is
resolved" of the headline-numbers list both rest on single-digit failing rows at
N = 1e5. `adr0040-hwl-bias-resolution.md` resolved the estimand by brute force at
N = 1e6: **KP 62.0 design HWL (46.39 m) B = 26.9, 95 % CI [21.6, 35.3], on 63
failing rows, RESOLVED** — so 44.7 was counting noise that overstated the bias
1.66× — and **KP 57.4 remains unresolved (2 rows in 1e6), bounded at B ≥ 148**,
which supersedes "≥32×" (a zero-row bound). This ADR's own *relative* statement
is unaffected and was the sound one: where counts are adequate the L adoption
makes the bias **fall** by about a third (15.0 → 10.5 at 47.0 m MSL), which is
what the ratio-of-ratios ρ = 0.475 predicts.

---

## References

- `docs/decisions/epistemic-bracket-synthesis.md` (2026-07-30) — the measurement that
  withdrew the k_aq contrast above; reuses this ADR's §4.5 ratio-of-ratios statistic.
- ADR-0005 / ADR-0006 — Mazure leakage lengths and the foreland tanh; why the
  foreshore is carried in `r_e` and not in `L`.
- ADR-0021 — surveyed landside toe elevations `z_toe` (±0.3 m), used here as an
  independent check on the extraction.
- ADR-0025 (+ 2026-07-28 amendment, `adr0025-foreshore-width-and-sensitivity.md`) —
  foreshore width verified, defined as 高水敷幅, and measured inert.
- ADR-0033 (+ `adr0033-gsa-study.md`) — Sobol' GSA; L is the top total-effect input.
- ADR-0043 — the Uemura section table reconstructed from `SECTIONS.shp`; source of
  the KP spans that anchor the alignment here.
- `docs/decisions/seepage-length-L-study.md` (2026-07-19) — the L prior, its
  base-width scatter argument, and the Phase 2 ceiling.
- `docs/tokachi_bep_inputs_provenance.md` §3.1 (seepage length), §3.2 (remediation
  state), §3.9 (foreshore width).
- GSI 基盤地図情報 数値標高モデル DEM5A, secondary mesh 644331, `devDate`
  2025-06-20, `orgMDId` R05GC0022.
- USACE (2000) App. B; TAW (2004) App. I — blanket theory underlying the
  `L` / foreland split.
