# Companion note: re-measuring the seepage length L from the 2025 GSI DEM5A surface

Date: 2026-07-28. Status: **evidence for ADR-0047**
(`docs/decisions/0047-dem-surveyed-seepage-length.md`). **No input value changed in
this pass** — `data/processed/tokachi_bep_inputs.csv` and `configs/*.yaml` are
read-only to this study, and adoption is deferred to an explicit project-owner
decision (ADR-0047 Decision 5). **That decision has since been taken (2026-07-29):
KP 62.0 was adopted, `L_m` 47.0 → 40.0 m, and KP 57.4 / 58.8 / 60.0 were held —
see §7 Close-out, which governs where it differs from §§1–6.**

Driver: `scripts/dem_cross_section_study.py`
(`datum | profiles | fragility | ratio | figure | all`).
Evidence: `docs/decisions/adr0047-dem-seepage-length.json` (measurement +
fragility) and `adr0047-dem-seepage-length-ratio.json` (the §4.5 ratio study).
Figure: `docs/figures/adr0047_dem_seepage_length.png`.
Tests: `tests/test_dem_cross_section.py`.
Sampled profiles: `data/raw/geometry/dem_cross_sections/kp*_profile.csv`
(gitignored, regenerable from the tiles alone).
Source surface: GSI 基盤地図情報 **DEM5A**, secondary mesh **644331**, `devDate`
**2025-06-20**, `orgMDId` R05GC0022, 100 tiles, mosaicking to 2250 × 1500 cells at
6.18 m N–S × 4.53 m E–W, **0.00 % nodata**, elevations 25.83–132.33 m T.P.

---

## 0. Why this study

`L` is the input worth measuring, on three lines that all point the same way:
ADR-0033's GSA ranks it the **top total-effect input for every QoI at every
level** (ST_L ≈ 0.49–0.78); the 2026-07-19 seepage-length L study measured the
transient shoulder P_f as **3–4× sensitive to CoV(L)** and showed the 2016 survival
**cannot** tighten it (posterior mean +0.5–1.4%, against ≈ −4% for k_aq and C_e);
and provenance §3.1 concedes the four production values are *"explicit
engineering-judgement estimates, not surveyed values of L"*, read off 1998 OYO
dimension chains. The 2026-07-28 foreshore-width resolution (ADR-0025 amendment)
closed out with exactly this hand-off: **`B_f` is inert and `L` is the input
actually worth measuring.**

---

## 1. Method

### 1.1 The whole path is in code

No GUI step. QGIS cannot open JPGIS(GML) `.xml` natively, and a manual transect in
the middle of a thesis pipeline is not reproducible; the GML DEM is a trivially
parseable text grid, so the extraction lives in a committed script like every other
input path in this repo. No geospatial dependency is added — the EPSG:2455 inverse
transverse Mercator is implemented in-repo and round-trips **below a millimetre**
(pinned by `test_plane_projection_round_trips_below_a_millimetre`), four orders of
magnitude finer than the 5 m posting.

Tile parsing handles the `gml:startPoint` offset defensively (a tile may begin
part-way; the head is padded with nodata rather than shifted). All 100 shipped
tiles are complete, so that branch is exercised only by a synthetic tile in the
test suite — which is precisely why it is tested: a silently misaligned tile would
translate part of the mosaic.

### 1.2 The alignment and the KP anchor

The Tokachi right-bank levee alignment is chained from five of Uemura's
`SECTIONS.shp` polylines, part-aware (several records are multi-part, and joining
parts blindly inserts spurious jump segments — `scripts/build_section_table.py`
compensates for that with its `DOUBLE_TRACED` correction; here the parts are kept
separate instead). Consecutive parts join to **< 1 m**, giving one 5501 m
alignment. Arc length is mapped to KP by the ADR-0043 section spans, and each
polyline's arc length is asserted against its span before use.

The alignment is a **crest line**: the picked crest sits +5.3 ± 3.1 m landward of
it on average, and the crest is the profile maximum at every station.

**The anchor is good but not exact.** Cross-correlating the DEM crest, landside
ground and riverside terrace against the 2019 and Uemura longitudinals gives broad,
shallow minima (residual sd varying only 0.68–0.83 over ±500 m) with best shifts at
0 and −100 m — the design-crest ramp is too nearly linear to localise chainage
better than ≈ **±150 m**. This is treated as a measured uncertainty, not papered
over: every section is re-measured over a ±300 m window (§1.4). An independent
corroboration is visible in the DEM at KP 62.0, where a sluice outfall channel
crosses the levee within ~50 m of the anchored station — consistent with the
chisuishi record placing 伏古樋門 at exactly KP 62.0.

### 1.3 The toe rule, stated in full

1. **Crest** = the maximum within ±40 m of the alignment point. The *crest band* is
   the contiguous run within 0.5 m of it; its extent is the reported crest width.
2. **Toes.** From each crest-band edge, walk outward. The outward slope is the
   elevation difference over the next 5 m *of outward travel*, per metre —
   evaluated in the direction of travel on **both** sides. The toe is the first
   offset that is ≥ 1.5 m below the crest and at which the outward slope stays
   ≥ −0.10 (1:10) over 8 m: the first place the embankment face stops descending
   and stays stopped.
3. **Outer landside toe** = the first offset beyond the crest at which the profile
   has come down to within 0.5 m of the landside far-field ground (40th percentile
   over 60–350 m landward) and stays there, capped at 40 m beyond the embankment
   toe. Where there is no berm the two coincide.
4. **L** = riverside toe to landside toe, crest width included.

> **A note on the slope convention.** An earlier iteration evaluated one signed
> forward-difference array on both sides. That is subtly wrong: on the riverside
> the window then lies on the crest side of the probe, and the toe is pushed 3–4 m
> too far out. The fix moved every measured `L` down by ≈4 m. Recorded here because
> the two versions are indistinguishable on a landside-only synthetic test.

**Both landside conventions are carried.** The outer toe is primary: a landside
berm is fill resting on the same blanket, so it lengthens the confined path, and it
is the convention the 1998 chains used — provenance §3.1 records KP 62.0 as
"toe-to-toe **incl. landside berm**, 18 + 29.1". The embankment-only toe is
reported beside it. `test_pick_cross_section_walks_past_a_landside_berm` pins the
behaviour on a synthetic levee: a constructed 15 m berm moves the outer toe out by
exactly 15 m, while the embankment-only convention stops on the berm *shoulder* and
so comes out **shorter than the unbermed levee** (32 m against 36 m). That is why
the outer toe is primary rather than a refinement of the other: on a bermed section
the embankment-only reading is not merely conservative, it is wrong in sign.

**Known bias: ≈ −2 m, conservative.** The finite forward-difference window declares
a toe up to `5 m × threshold / face_slope` early — 1 m per side for a 1:3 face at
threshold 0.10 on 1 m posts. `test_pick_cross_section_recovers_a_synthetic_trapezoid`
pins this exactly against a trapezoid of known `L`. A shorter `L` raises P_f, so the
bias is reported rather than removed by an ad hoc offset.

### 1.4 Window statistics and the two clean-station screens

Each section is measured at **31 stations over ±300 m at 20 m spacing**. This
brackets the ±150 m anchor uncertainty *and* delivers the along-levee spread of `L`
— an empirical CoV where the seepage-length L study had none.

Two screens, applied identically at every section and both referenced to
independent committed data (neither is tuned per section):

* **Landside structure** — a separate embankment ≥ 1.5 m above the landside ground
  reference, standing ≥ 10 m clear of the outer toe and within 150 m of it. Catches
  a road or second-line levee *beside* the levee.
* **Raised crest** — crest more than 0.5 m from the *window's own median* excess
  over the 2019 `DesignBankHeight_R`. Catches fill sitting *on* the levee, which
  the first screen cannot see because there is no gap. Anchoring to the window
  median rather than to design matters: an as-built crest is routinely a few tenths
  above design along a whole reach (measured reach mean +0.30 m) and that uniform
  over-build is not contamination.

The headline is the **median over surviving stations**.

---

## 2. Gate: the datum (ADR-0047 Decision 4)

GSI 標高 is orthometric height on T.P.; the repo's `z_toe` and stage grids are
m T.P./MSL. They must agree, so this is a hard gate — a failure raises and stops
the run rather than warning. Measured over **551 stations, KP 57.3–62.9**:

| Comparison | mean | sd | verdict |
|---|---|---|---|
| DEM crest vs 2019 `DesignBankHeight_R` | **+0.30 m** | 0.55 | PASS |
| DEM landside ground vs Uemura `ground_m_msl` | **−0.65 m** | 0.68 | PASS |
| DEM riverside terrace vs Uemura `floodplain_m_msl` | **−0.24 m** | 0.73 | PASS |

Tolerance 1.0 m. Three independent series, two of them from a different provider
than the third. The datum is sound.

---

## 3. Gate: does the extraction reproduce what is already known?

Both checks are independent of the answer being sought.

**ADR-0021 `z_toe` (surveyed landside toe, ±0.3 m).** DEM landside outer-toe
elevation minus the surveyed toe:

| Section | `z_toe` | DEM outer toe | residual |
|---|---|---|---|
| KP 57.4 | 38.3 | 37.45 | **−0.85** |
| KP 58.8 | 38.5 | 38.35 | **−0.15** |
| KP 60.0 | 40.0 | 39.62 | **−0.38** |
| KP 62.0 | 44.9 | 45.26 | **+0.36** |

Three of four land within about a decimetre of the ±0.3 m band, on a 5 m raster
whose own reach-scale scatter is ±0.55–0.73 m. The outlier is KP 57.4 — which the
screens independently flag as contaminated (§4.1), so the two diagnostics agree.

**Perpendicularity.** A profile off-perpendicular by θ inflates a toe-to-toe length
by 1/cos θ — +6 % already at 20°, which would read as a real widening. Scanning the
azimuth ±30° and locating the `L` minimum (which *is* the true perpendicular) puts
the adopted alignment normal within **2°** at KP 57.4 / 58.8 / 62.0 and **6°** at
KP 60.0, i.e. obliquity inflation **1.001 / 1.001 / 1.006 / 1.001**. The artefact
is measured and absent. `test_an_oblique_profile_inflates_the_picked_length_by_one_over_cos`
pins that the extraction would in fact show it if it were present.

**Threshold sensitivity** (L over the ladder 0.05 → 0.20):

| Section | 0.05 | 0.075 | 0.10 | 0.15 | 0.20 | spread |
|---|---|---|---|---|---|---|
| KP 57.4 | 91 | 72 | 68 | 67 | 66 | 25 |
| KP 58.8 | 40 | 38 | 36 | 34 | 33 | 7 |
| KP 60.0 | 61 | 42 | 41 | 39 | 37 | 24 |
| KP 62.0 | 39 | 36 | 35 | 34 | 33 | 6 |

The two clean sections are tight (6–7 m); the 0.05 rung walks onto adjacent flats at
KP 57.4 and KP 60.0. Values above are the nominal station; the deliverable is the
window median (§4).

---

## 4. Results

### 4.1 The measured lengths

Clean-station window medians, ±300 m at 20 m:

| Section | `remediation_state` | CSV 1998 | **DEM 2025** | Δ | clean | along-levee CoV | range |
|---|---|---|---|---|---|---|---|
| KP 57.4 | berm-only | 33.0 | *(no resolvable change)* | — | 6/31 | 0.60 | 34–106 |
| KP 58.8 | drained | 35.0 | **42** | +7 | 31/31 | 0.073 | 36–47 |
| KP 60.0 | drained | 34.8 | **43** | +8 | 31/31 | 0.184 | 37–71 |
| KP 62.0 | unreinforced | 47.0 | **40** | −7 | 28/31 | 0.102 | 34–47 |

**KP 57.4 carries no adoptable number and none is offered.** Its screened median
is 36.5 m against the CSV's 33.0 m, but it rests on **6 surviving stations of 31**
with an along-levee CoV of **0.60** (34, 34, 35, 38, 41 and one 106 m outlier;
excluding the outlier, median 35.0, CoV 0.084). The apparent +3.5 m is smaller than
the rule's own ≈ −2 m bias (§1.3) and far inside the station scatter: **the
difference is not resolvable, and the section is reported as "no change
measurable", not as "+3 m".** What KP 57.4 *does* deliver is a negative result, and
it is the more valuable one — see below.

**The differences track the remediation history.** The two `drained` sections —
where provenance §3.2's Fukuda type map records berm + toe-drain works after 1998 —
measure +7 and +8 m longer on the 2025 surface. The `unreinforced` section does not
lengthen at all. Provenance §3.1 predicted exactly this pattern ("for the
`unreinforced` node KP 62.0 the 1998 value stands"), and the DEM reproduces it from
an independent surface. That is the strongest single result in this study.

**The KP 57.4 negative result.** Its nominal station sits on a road interchange
embankment: the crest stands **+1.6 m above the 2019 design crest** over a ~200 m
band, and a second embankment stands 40–100 m landward of the toe further
downstream. Taking every station gives a window median of **67 m** — a doubling of
the CSV value that would look like a spectacular confirmation of §3.1's "+10 to
+30 m" berm-only prediction, and that is **road fill, not levee**. The finding is
therefore that **§3.1's "+10 to +30 m" prediction does not hold for the levee
proper**: wherever the levee can be measured free of road fill, its 2025 footprint
is indistinguishable from the 1998 value. Both readings were driven through the
engine (§4.3) so the extraction ambiguity is bracketed by measurement rather than
argued — but neither is offered as an adoptable `L`.

Adding back the ≈ −2 m rule bias (§1.3) would put the three measurable values at
roughly 44 / 45 / 42 m.

### 4.1b KP 62.0: is there a berm at all? (resolved — there is not)

The KP 62.0 result exposes a contradiction *inside* the provenance document, and it
has to be resolved before the 40 m can be read either as a bracket endpoint or as a
correction:

* **§3.1** records the 1998 `L = 47 m` as *"toe-to-toe **incl. landside berm**,
  18 + 29.1 m; range 40 to 55"*.
* **§3.2** records KP 62.0 as `unreinforced`, **confirmed 2026-07-22 on three
  independent lines**.

A section with no landside works should not have a berm inside its seepage length.
The 2025 surface answers this directly, and the answer is **(c): there is no berm**.

**Evidence 1 — the profiles.** At all **28 clean stations**, the picked outer toe
**equals** the embankment toe: the walk never had a berm to step past. The landside
shape is the same everywhere — crest, a uniform ~1:3 face, a toe at +21 to +33 m,
then level ground. Representative clean stations (offset: elevation, m T.P.):

| station | crest | face → toe | beyond the toe |
|---|---|---|---|
| ds +160 | 48.55 | +15 47.59 → +25 45.05 | +30…+130 flat 45.10–45.28 |
| ds +200 | 48.70 | +15 47.86 → +25 45.26 | +35…+130 flat 44.94–45.54 |
| ds +260 | 48.84 | +15 48.13 → +25 45.27 | +35…+130 flat 45.03–45.49 |
| ds −240 | 47.93 | +15 46.00 → +25 43.20 | +35…+130 flat 43.59–43.72 |

There is **no bench, no shelf, no intermediate step** — the profile goes crest →
face → toe → flat ground. (The dips at +50…+95 at ds −20 and ds 0 are the 伏古樋門
outfall channel, landward drainage, not a berm.)

**Evidence 2 — the cap did not hide one.** The outer-toe walk is capped 40 m beyond
the embankment toe, so the obvious objection is that a wide berm was clipped. It was
not: raising the cap leaves the clean-station median flat, and only inflates the
*mean* and *max* as a few stations run off into unrelated landside terrain.

| cap | clean n | median L | mean | max | still capped |
|---|---|---|---|---|---|
| 40 m (adopted) | 28 | **40.0** | 40.4 | 47 | 4 |
| 60 m | 28 | **40.0** | 43.8 | 95 | 2 |
| 80 m | 28 | **40.0** | 46.3 | 111 | 1 |
| 120 m | 28 | **41.0** | 49.6 | 129 | 0 |
| 200 m | 30 | 42.5 | 58.2 | 182 | 0 |

The median is stable at 40–41 m across a threefold change in the cap. **The 40 m is
not an artefact of the rule.**

**Evidence 3 — which of the three §3.2 lines bear on a berm.** All three do, and the
*drain* is the one left open — the reverse of the natural worry that the 2026-07-22
confirmation only addressed the drain:

1. The 1998 OYO 様式-5 for KP 62.0 *"models a plain trapezoidal levee and leaves the
   浸透対策工 row blank: **no landside berm was credited** even at the time of the
   deficiency rating"* — and this is **the very sheet the L memo read its dimension
   chain from**.
2. DEM5A profiles at ~ten chainages show *"a consistent unbermed geometry at every
   station … **no intermediate bench**"*. The present study reproduces that
   independently, with a stated rule, at 28 stations.
3. The 側帯 annotated near KP 62 on the 1996 様式-2 sheet is a 第二種側帯 — an
   emergency-earth stockpile pad, **not a seepage countermeasure** — which explains
   away the only plan-sheet feature that looked like a berm.

§3.2's own stated residual is *"a buried landside toe **drain** cannot be excluded
from remote elevation data"*. So berm absence is the well-evidenced part; drain
presence is the open part; and a buried drain would only *lower* computed P_f.

**Conclusion.** The 1998 `L = 47 m` credits a landside berm that its own source
sheet did not model, that the `unreinforced` label denies, and that the 2025 surface
does not show. The DEM's **40 m** is the internally coherent reading, and it sits at
the bottom of the memo's own quoted "40 to 55" range. Accordingly this is **not a
bracket endpoint at KP 62.0 — it is a finding that the production model is
under-conservative at the governing section**, by the factors in §4.3: transient P_f
raised at every level where the baseline is positive, 1.02–15×.

Two honest caveats. First, a berm could in principle have been removed between 1998
and 2025 — but §3.2 line 1 shows none was credited in 1998 either, so the simpler
explanation is that the L memo attributed one that was never there. Second, the
arithmetic is consistent with a small over-count rather than a gross one: the DEM
splits as ≈16 m riverside + ≈23 m landside against the memo's 18 + 29.1, i.e. the
landside limb is ~6 m long, about the width a modest berm would have added.

### 4.2 The 高水敷幅 by-product — recorded, and inert

Measured riverside toe → low-water-channel shoulder break, reported **beside** `L`
and never inside it (pinned by
`test_high_water_bed_width_is_reported_beside_L_and_never_inside_it`, because
folding it into `L` would double-count the foreland resistance already carried by
`λ_out` inside `r_e`):

| Section | 1998 様式-3 (ADR-0025 verified) | DEM 2025 | ratio |
|---|---|---|---|
| KP 57.4 | 200 | 102 | 0.51 |
| KP 58.8 | 325 | 288 | 0.89 |
| KP 60.0 | 600 | 546 | 0.91 |
| KP 62.0 | **44** | **236** | **5.4** |

Three sections agree in magnitude and direction. KP 62.0 does not — its 2025
terrace is far broader than the 1998 annotation or the MLIT 2008 digitisation
(≈34 m).

**This does not reopen ADR-0025**, for a reason that ADR already measured rather
than argued: at KP 62.0 the foreland tanh is **saturated** — "any B_f ≳ 100 m is
numerically identical, so 44 vs 250 m is worth 5e-5" — and the full open-entry
excursion `B_f → 0` moves transient P_f by only **0.00023** there, with static P_f
**exactly 0**. A *wider* foreshore lies on the saturated side, so the DEM reading is
worth less than 5e-5. It is a morphological observation (the 2025 surface shows a
broader terrace than the 1998 and 2008 sheets, plausibly post-2016), not an input
question, and the ADR-0025 source decision stands.

### 4.3 What the DEM L would do to the production fragility

Each section's **baseline arm was asserted bit-identical** to its persisted
`results/tokachi_kp*_historical_matrix.h5` sweep before any comparison was reported;
a drifted baseline raises rather than producing a reassuring number. Matrix d70
interpretation, N = 1e5, 225 s, `geometry.L` overridden in memory only.

| Section | CSV L | arm | DEM L | ΔL | max \|ΔP_f\| transient | at stage | max \|ΔP_f\| static | at stage | direction | transient P_f ratio range |
|---|---|---|---|---|---|---|---|---|---|---|
| KP 57.4 | 33.0 | clean median | 36.5 | +3.5 | **0.132** | 41.25 | 0.135 | 40.50 | ↓ | 0.19 – 0.97 |
| KP 57.4 | 33.0 | all stations (road fill) | 67.0 | +34.0 | **0.749** | 42.25 | 0.770 | 41.00 | ↓↓ | 0.00 – 0.34 |
| KP 58.8 | 35.0 | clean median | 42.0 | +7.0 | **0.232** | 41.75 | 0.240 | 40.75 | ↓ | 0.07 – 0.97 |
| KP 60.0 | 34.8 | clean median | 43.0 | +8.2 | **0.279** | 43.50 | 0.304 | 42.25 | ↓ | 0.00 – 0.95 |
| KP 62.0 | 47.0 | clean median | 40.0 | −7.0 | **0.201** | 50.00 | 0.214 | 48.25 | ↑ | 1.02 – **15.0** |

Stages in m MSL. Every baseline arm bit-identical to its persisted production
sweep (asserted, not assumed). Runtime 319–466 s per section.

**A free cross-check on ADR-0048.** Unrelated work landed in the working tree while
this study ran: ADR-0048's `config.prior_mean_scenario`, with edits to `config.py`,
`run.py` and `bayesian_reliability_updating/replay.py`. Those changes were already
present when these arms were executed, so **every baseline arm reproducing its
persisted sweep bit-for-bit is direct evidence that ADR-0048 is baseline-neutral** —
its default-`None` field really is dropped from `to_metadata()`, and its presence
really does leave the sampled θ, the stochastic L draw and both failure matrices
untouched. The ratio stage (§4.5) strengthens this further: it asserts the whole
`(1e5, N_h)` failure matrices match, not merely their column means.

**Read three things off this table.**

1. **`L` is roughly two orders of magnitude more consequential than `B_f`.** The
   ADR-0025 foreshore sensitivity — the immediately preceding question on this same
   geometry — measured max |ΔP_f,trans| of 0.00111 / 0.00170 / 0.00440 / **0.00023**
   at KP 57.4 / 58.8 / 60.0 / 62.0 with static **exactly 0**, and that was the
   *bounding* `B_f → 0` excursion. Here a 3.5–8 m change in `L`, well inside the
   prior's own CoV 0.20 band, moves both branches by 0.13–0.28. Section by section
   the ratio is **119× / 137× / 64× / 874×**. The ADR-0025 close-out judgement that
   "`B_f` is inert and `L` is the input actually worth measuring" is confirmed
   quantitatively, by two to three orders of magnitude.
2. **Both branches move together.** Unlike `B_f` (which since ADR-0028 touches only
   the uplift/heave gate and leaves the static comparator exactly invariant), `L`
   enters `H_c`, the rate denominator, `r_e`, and the progression criterion
   `Z = L − l_e` — so static and transient shift by nearly the same amount. This is
   why adoption is a **re-run**, not an amendment: no persisted number survives it.
3. **The sign at KP 62.0 is the one that matters for safety.** It is the only
   section where the DEM is *shorter* than the adopted value, and it is the
   governing `unreinforced` section. Its transient P_f rises everywhere the
   baseline is positive — by up to **15×** in the tail, and by +0.20 absolute at
   50.00 m MSL.

**Where these maxima sit.** All of them lie above the design HWL, which is expected
— the maximum *absolute* ΔP_f falls near the fragility transition, and at these
sections the transition sits above HWL. Per section (HWL / design crest, m MSL):
KP 57.4 39.21 / 40.71; KP 58.8 41.03 / 42.53; KP 60.0 42.75 / 44.25; KP 62.0
46.39 / 47.89. The KP 62.0 maximum at 50.00 m MSL therefore falls **above the crest,
inside the ADR-0024 hypothetical fit-stabiliser extension of that section's grid,
and must never be plotted as attainable**; the design-relevant statement there is the
ratio range (P_f raised at *every* level with a positive baseline, 1.02–15×), not the
absolute maximum.

### 4.5 Does the static-vs-transient bias ratio survive the L change? **No.**

> **Dated correction, 2026-07-30.** Everything this section measures about **L** stands
> unchanged and has since been reproduced independently
> (`epistemic-bracket-synthesis.md` §2.5, three ways). What does **not** stand is the
> *contrast* drawn below: this section repeatedly cites ADR-0048's k_aq bracket as the
> example of a knob that "largely cancels", and argues that L is unusual in not doing so.
> ADR-0048 consequence 3 was **refuted by measurement on 2026-07-30**
> (`epistemic-bracket-synthesis.md` §4(c)): k_aq's maximum resolved ratio-of-ratios
> departure is ×82 / ×66 / ×163 / ×46 at KP 57.4 / 58.8 / 60.0 / 62.0 — **larger** than
> L's. Read every "unlike k_aq" and "the k_aq analogy fails" below as historical: the
> correct statement is that **neither** bracket cancels, k_aq less so than L, and the only
> knob measured to cancel is `m_p` (×1.07–1.22), which does so by ADR-0045 §2
> construction. The mechanism argument given below for L — a transient-only channel on top
> of the shared `H_c` — is exactly right, and is now the general rule; k_aq has *two* such
> channels where L has one.

This is the question that decides whether adoption is optional. The thesis defends
**ratios** — the Stage 6.6 conventional-practice bias, the WBI+ peak-shortcut
over-rejection — not absolute probabilities, and ADR-0048 established the idiom: its
k_aq bracket *"dwarfs the §11 MC CoV"* in absolute P_f but *"largely cancels in the
Stage 6.6 static-vs-transient ratio (shared sample, fixed k_aq)"*, so the comparative
claims stay robust while the absolute ones do not.

**The L bracket does not behave that way.** Evidence:
`docs/decisions/adr0047-dem-seepage-length-ratio.json`; driver stage
`python scripts/dem_cross_section_study.py ratio`.

*Method.* Per section and conditioning level, the quantity is the **ratio of
ratios** ρ = (P_f,static/P_f,trans)_DEM ÷ (P_f,static/P_f,trans)_CSV. The four
indicators at a level are functions of the same realizations — the ADR-0002
shared-sample contract, and the CSV and DEM arms share the seed so their θ rows are
the same draws — so their 16 joint pattern counts are a sufficient statistic and the
**paired bootstrap** (2000 replicates, the ADR-0040 Decision 6 recipe) is exact. A
level is called **resolved** only when the 95 % interval excludes 1.0; an interval
covering 1.0 is reported as unresolved, never as a finding. The null case is pinned:
feeding the baseline in as its own arm returns ρ = 1.0 exactly with zero levels
resolved. Baselines here are gated harder than in §4.3 — the **whole (1e5, N_h)
failure matrices** must equal the persisted sweep, not merely their column means.

*Result at design HWL* (the stage the Stage 6.6 headline is quoted at):

| Section | ΔL | S/T ratio, CSV → DEM | ρ | 95 % CI | resolved |
|---|---|---|---|---|---|
| KP 57.4 | +3.5 | 35.97 → 80.92 | **2.250** | [1.471, 4.465] | yes |
| KP 57.4 *(road-fill arm)* | +34.0 | 4.26 → 45.67 | **10.720** | [6.897, 22.792] | yes |
| KP 58.8 | +7.0 | 2.75 → 4.51 | **1.642** | [1.617, 1.667] | yes |
| KP 60.0 | +8.2 | 2.92 → 6.49 | **2.226** | [2.193, 2.261] | yes |
| KP 62.0 | −7.0 | **27.87 → 13.23** | **0.475** | [0.263, 0.724] | yes |

*Result over the whole grid.* **Every one of the 87 evaluated levels across the four
adoption-relevant arms is resolved** (16 / 21 / 22 / 28), with ρ spanning
1.034–2.250 (KP 57.4), 1.034–1.823 (KP 58.8), 1.053–3.219 (KP 60.0) and
0.475–0.979 (KP 62.0). At KP 62.0 the departure is not a tail artefact: ρ sits
steadily at 0.64–0.70 from just above HWL to well above crest, i.e. the bias is
compressed by about a third across the whole reachable range and by half at HWL.

*Mechanism, and why the k_aq analogy fails.* `k_aq` shifts both branches through
channels they share, so it largely cancels. `L` does not: both branches share `H_c`,
but the transient branch alone carries `L` in the **progression distance**
`Z = L − l_e(t)` and in the ODE rate denominator. Changing `L` is therefore **not a
common-mode shift** — it suppresses (or releases) the transient branch harder than
the static one, so the gap between them widens with longer `L` and compresses with
shorter `L`. That is exactly the sign pattern measured: ρ > 1 at the three sections
where the DEM is longer, ρ < 1 at the one where it is shorter.

**Answer, in the ADR-0048 idiom.** *The static-vs-transient bias claim is **not**
robust to the L bracket in the sense that it is robust to the k_aq bracket. The k_aq
bracket cancels in the ratio; the L bracket does not, moving the static/transient
P_f ratio at design HWL by ×2.25, ×1.64, ×2.23 and ×0.475 at KP 57.4 / 58.8 / 60.0 /
62.0 — every level, at every section, resolved at 95 %.* The Stage 6.6 headline
numbers (~21× at KP 62.0, ≥32× at KP 57.4 per event at HWL) are therefore
**L-conditional and must be quoted as such**: under the DEM geometry the KP 62.0
bias roughly halves and the KP 57.4 bias roughly doubles.

*ADR-0024 deliverable form.* The premise that KP 62.0 might flip from
`raw_tail_binomial` to `fitted_lognormal` does not apply: **all four matrix
transients are already `fitted_lognormal`** at baseline, with the transition
bracketed (max raw P_f 0.9644 / 0.9878 / 0.9843 / 0.9698). Under DEM-L KP 62.0 stays
`fitted_lognormal` (max raw P_f rises to 0.9901). The **only** form change anywhere
is the contaminated KP 57.4 road-fill arm, where P_f falls far enough to *lose* its
bracket (`fitted_lognormal` → `raw_tail_binomial`) — and that arm is not a candidate
for adoption.

There is nevertheless a real presentational consequence at KP 62.0 that the form
label hides. Its transition is bracketed only inside the ADR-0024 **hypothetical
above-crest extension**, which must never be plotted as attainable. Shortening `L`
moves probability mass down into the attainable range: at HWL P_f,trans goes
0.00015 → 0.00130 (**×8.7**) and at design crest 0.0194 → 0.0622 (×3.2). So what
changes is not the form but how much of the curve is defensibly plottable.

### 4.4 CoV(L): confirmed, not narrowed

The measured along-levee spread — **0.073 (KP 58.8), 0.184 (KP 60.0), 0.102
(KP 62.0)** — brackets the **0.08–0.16** that `seepage-length-L-study.md` §1.2
derived from the memo's own base-width ranges, and sits below the assigned 0.20 at
two of three. That is a real measurement where the study had none, and it
**confirms the base-width component of the prior**.

It does **not** license narrowing 0.20/0.15. That study established that the
padding above the base-width term covers the **unverified landside blanket
boundary** and the possibility that the effective exit lies a short distance beyond
the toe — neither of which a bare-earth lidar surface can observe. A surveyed
footprint converts one term of a lumped allowance from judgement into measurement
and leaves the other intact. The correct statement is: *the DEM removes the
reading-error excuse for CoV(L) = 0.20; the epistemic exit-position term remains,
and it is the term the 土層縦断図 (still not obtained) would address.*

Note also that the along-levee spread and the at-a-section uncertainty are not the
same quantity: the former mixes real geometric variation along the levee with
extraction scatter, and a length-effect consumer wants the former while the
fragility prior wants the latter. They happen to agree in magnitude here.

---

## 5. Limitations

1. **Vintage.** A 2025 surface against 1998 geometry. Where they differ, the
   remediation history (§3.2) is the leading explanation, and the DEM alone cannot
   prove that — it can only show that the difference has the sign and the sections
   that the remediation record predicts.
2. **KP 57.4 cannot be measured cleanly.** Road fill is fused with the levee at the
   nominal station. The screened value (36 m) rests on 6 surviving stations, one of
   which is a 106 m outlier; the median is robust to it, but the section's `L`
   should be quoted as "≈36 m, levee proper, road fill excluded", never as a
   survey-grade number.
3. **Chainage ±150 m.** Absorbed into the window, not eliminated. A 距離標 (KP
   marker) survey or a georeferenced plan sheet would remove it; the raster plan
   sheet `81_十勝川水系十勝川_01堤防現況平面図_007.pdf` has no text layer and was
   not digitised for this pass.
4. **The DEM sees topography, not the blanket.** The dominant residual uncertainty
   in `L` — the landside blanket boundary and the effective exit position — is
   invisible to it. This study does not close the §3.1 standing data gap; it closes
   the *post-remediation cross-section* half of it.
5. **`remediation_state` is a label, not physics.** The engine evaluates the
   unremediated foundation everywhere. Adopting a longer 2025 `L` at KP 58.8 and
   KP 60.0 — geometry that exists *because* of drainage works the model does not
   represent — while continuing to model no drain is a defensible conservative
   choice, but it is a choice and must be stated as one.
6. **Satsunai is out of scope**: KP 6.4 and 7.0 fall south of mesh 644331 (KP 5.2
   partial). `L` is only defined at the four Tokachi OYO sections, so this does not
   affect the study; mesh 644321 would be needed if Satsunai geometry were ever
   wanted.

---

## 6. Recommendation

The measurement is recorded; **the adoption decision is the project owner's** and
is deliberately left open (ADR-0047 Decision 5). Two results from §4.1b and §4.5
change the shape of that decision relative to a plain "carry it as a bracket":

1. **The comparative claims are not insulated.** §4.5 shows the static-vs-transient
   ratio moves by ×1.6 to ×2.3 at the three lengthening sections and **halves** at
   KP 62.0, every level resolved. So "keep the CSV and carry the DEM as a bracket"
   does **not** leave the thesis safe as written — the Stage 6.6 bias figures become
   L-conditional statements either way, and that conditioning has to be stated
   whether or not the values are adopted.
2. **KP 62.0 is not a bracket endpoint.** §4.1b shows there is no berm to justify
   the 1998 47 m, so the DEM's 40 m is the internally coherent value and the
   production model is under-conservative at the governing section.

What the evidence supports:

* **KP 62.0** — the DEM (40 m) is *shorter* than the CSV (47 m), and §4.1b shows
  the 47 m rests on a berm that the 1998 source sheet did not model, that the
  `unreinforced` label denies, and that the 2025 surface does not show. This is the
  one section where the case is not "bracket" but "correction": adopting it raises
  P_f at the governing section (×8.7 at HWL) and compresses the static-vs-transient
  bias by half.
* **KP 58.8 / KP 60.0** — the DEM is longer (+7, +8 m), and the reason is
  post-1998 landside works the model does not otherwise represent. Adopting these
  lengths lowers P_f at the two sections that carry the informative Phase 2 update.
  Retaining 1998 is the conservative reading; adopting 2025 is the "current
  geometry" reading. This is the substantive choice.
* **KP 57.4** — **no resolvable change** (6 clean stations, CoV 0.60, apparent
  difference smaller than the rule bias). No case for change either way; the
  section's contribution is the negative result about §3.1's berm-only prediction,
  not a number.

**The "retain and carry as a bracket" course is available but is no longer free.**
It was the natural analogue of the ADR-0025 `B_f` disposition, and it remains
defensible for KP 58.8 and KP 60.0, where the DEM difference has a remediation
explanation and the direction is *conservative* (the model keeps the shorter 1998
path). But §4.5 removes its main attraction: the bracket is not inert **and does not
cancel in the ratio**, so the thesis must in either case state its comparative
headline numbers as conditional on `L`. And §4.1b makes KP 62.0 a different case
from the other three — there the disagreement is not vintage, it is an internal
inconsistency in the 1998 record at the governing section, in the unsafe direction.

The narrowest change that addresses the substantive finding is therefore
**adoption at KP 62.0 alone**, leaving KP 57.4 (no resolvable change), KP 58.8 and
KP 60.0 on their 1998 values. That still triggers the full re-run — one changed CSV
cell moves that section's config hash and every artifact built on it — but it
confines the *interpretive* change to the section where the evidence is a
correction rather than a vintage difference.

The re-run cost, if adoption is chosen, is tabulated in ADR-0047 Consequences: the
CSV edit, `generate_configs.py`, `tests/test_configs.py`, 8 Phase 1 sweeps, the
Phase 2 posterior, the Phase 3 campaign, and ten companion studies that assert
bit-identity against the persisted sweeps, plus the documents of record that quote
their numbers.

---

## 7. Close-out (2026-07-29)

### 7.1 What was adopted, and what was held

**Adopted: KP 62.0 only**, `L_m` 47.0 → **40.0 m** — one CSV cell. The 1998 value
credited a landside berm that the 1998 OYO 様式-5 sheet did not model, that the
`unreinforced` classification denies, and that 28 of 28 clean stations do not show
(stable under a 40 → 120 m outer-toe cap sweep). The berm was not there in 1998
either, so this is a **defect**, and it was under-conservative at the governing
section.

**Held: KP 57.4, KP 58.8, KP 60.0.** KP 57.4 shows no resolvable change. KP 58.8 and
KP 60.0 show a genuine +7/+8 m produced by the 1999–2003 remediation earthworks —
merely *old*, not wrong — and adopting the longer path while the engine still models
no toe drain would import only the anti-conservative half of those works into an
otherwise consistent 1998 baseline. Their DEM values stand as the measured,
unadopted epistemic bracket, with the asymmetry stated: **the bracket lowers P_f at
three sections and raises it at the governing one.**

`seepage_length_cov` unchanged everywhere (0.20; 0.15 at KP 60.0). No `Config`
field, no `to_metadata()` or hash-surface change. The adopted 40 m is the
**conservative end** of the measurement (the rule's ≈ −2 m bias is deliberately not
corrected). KP 63.4's forced proxy untouched.

### 7.2 A corroboration worth recording

This outcome **confirms provenance §3.2's `unreinforced` classification** rather than
challenging it — the DEM survey is a **fourth** independent line, and the first
rule-based and quantified one. What it overturned was §3.1's seepage length, which
had quietly assumed a structure §3.2 says is absent. Note also that all three of
§3.2's original confirmation lines bear on **berm** presence; the **toe drain** is
its stated residual, and a buried drain would only lower computed P_f.

### 7.3 Every artifact regenerated, and every consumer re-pinned

Consumers were enumerated **programmatically**, not from memory. Seven candidates;
all handled. The executed table is in ADR-0047 Consequences. Gates that passed:
config diff confined to two files and one field; Phase 1 sweeps re-run; Stage 6.6
drift guard bit-identical at 38 levels with all Euler-flip counts 0; Phase 2
masked-vs-re-evaluation verification exact; Phase 3 containment 20/2280 rows, all
KP 62.0; `foreshore_exhaustion_study` byte-identical; the three held sections'
foreshore-width numbers reproduce exactly.

**An independent validation fell out of the re-run.** The regenerated production
sweep reproduces the ADR-0047 §4.3 `dem_clean_median` arm to within 1e-12 at every
level — the arm was computed weeks earlier by overriding `geometry.L` in memory, and
the real sweep from the edited CSV lands on the same numbers. The measurement chain
and the adoption path agree.

**A second free cross-check** (see §4.3): ADR-0048's `config.py` / `run.py` /
`replay.py` changes were already in the tree throughout, so every baseline arm
reproducing its persisted sweep — and, in the ratio stage, the **whole failure
matrices** matching — is direct evidence that ADR-0048 is baseline-neutral.

### 7.4 Headline numbers that moved

| Quantity | before (L = 47.0) | after (L = 40.0) |
|---|---|---|
| transient P_f at design HWL | 1.5e-4 | **1.3e-3** (×8.7) |
| Stage 6.6 bias at HWL *(unresolved, 1 and 4 rows)* | 21.0 | 44.7 |
| Stage 6.6 bias at 47.0 m MSL *(resolved)* | 15.0 | **10.5** |
| Phase 2 rejection, both strata | 0.00 % | **0.00 %** |
| RQ3 BEP share, historical | 0.637 | **0.812** |
| RQ3 BEP share, +4K | 0.344 | **0.500** (overflow no longer leads) |
| RQ4 annual system P_f, historical | 5.24e-4 | **1.01e-3** |
| RQ4 +4K / historical ratio | 19.5 | **12.7** |
| ADR-0025 `B_f → 0` excursion | 0.00023 | 0.00024 (still inert) |
| ADR-0044 2011 bound | 0/100 000 | **0/100 000** |

Two corrections to documents of record came out of the re-run, neither caused by it:
`phase3_report.md` §5 claimed KP 62.0's BEP number was flagged
`bep_clamped_above_grid` "in every output row" — **it is False in all 20 KP 62.0
rows, before and after**, and the flag actually fires on 16 rows at KP 57.4/58.8
under bulk d70 (withdrawn in §11.3); and `stage6_6_report.md`'s "factor of about 21"
was never statistically resolved even under the geometry it describes (§8).

### 7.5 Final state

`ruff check .` and `black --check .` clean; **pytest 556 passed** (22 in
`tests/test_dem_cross_section.py`, including the ratio estimator's exact null-case
pin and its ability to return *unresolved* for a common-mode change).
