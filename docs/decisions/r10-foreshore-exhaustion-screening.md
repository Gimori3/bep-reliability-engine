# Foreshore-exhaustion screening indicator (review item R10, Tier 1)

Companion note to the scoping note `docs/scoping_bank_retreat_mechanism.md`.
Date: **2026-07-28**. Status: **executed, Tier 1 only**.

**Changes no input value, no config, no default, and no Phase 3 number.** No ADR
is consumed: this is a study, and the new code is unwired from the composition
by construction and by test. Tiers 2 (a probabilistic retreat fragility joining
the Phase 3 series system) and 3 (morphodynamic coupling) are **declined by the
project owner**; Tier 2 would require ADR-0047 before any code.

Driver: `scripts/foreshore_exhaustion_study.py` → evidence JSON
`docs/decisions/r10-foreshore-exhaustion-screening.json`, figure
`docs/figures/r10_foreshore_exhaustion.png`. Indicator:
`system_integration/foreshore_exhaustion.py` (pure, physics-free, forcing
injected — the `convergence.py` / `sensitivity.py` pattern). Tests:
`tests/test_foreshore_exhaustion.py` (19).

---

## 1. What triggered this

Phase 3 composes three mechanisms per segment: BEP (engine-derived), overflow
(Uemura P1) and fluvial scour (Uemura P2). Under the ADR-0042 decision 9
dimensionally-corrected conversion, **P2 returns exactly zero at all 114 segments
in both climate scenarios**. Meanwhile the documented failure record for this
system is:

| Event | Location | Official attributed cause |
|---|---|---|
| 2016-08 | Otofuke KP 21.2 L | falling-limb channel migration; bank + embankment erosion |
| 2016-08 | Satsunai KP 40.5 L | falling-limb channel migration; bank + embankment erosion |
| 2016-08 | Satsunai KP 25.0 L | landside overtopping from a Tottabetsu breach |
| 2011-09 | Otofuke KP 18.2 | high-water-bed erosion advancing into the embankment, ~5 m of levee length per hour, no revetment present |

So the mechanism with the strongest empirical claim to having caused levee
failure in this basin contributes nothing to the composition, while the
mechanism that dominates it (BEP) has never been observed to breach here. That
asymmetry is the largest single qualification on the RQ3 dominance conclusion.

P2 cannot be repaired by recalibration (established 2026-07-28, not re-derived
here): its shear comes from a uniform-flow Manning velocity keyed on *floodplain
inundation depth*, and `SegmentSurfaceInputs` carries no thalweg position, no
bend curvature and no foreshore width — so it has no state in which a receding
flood is more dangerous than a peak one, yet three of the four failures above
occurred on the falling limb.

This indicator does not close that gap. It **quantifies which study segments are
even exposed to the mechanism**, which converts an admission in the Discussion
into a measured statement.

## 2. Method

The state variable the represented mechanism set lacks is the **remaining
high-water-bed width**, and the failure condition is its exhaustion:

```
mobilising window  T_mob  = time the stage stands above the high-water-bed surface
cumulative retreat        = v_lat * T_mob
time to exhaustion        = B_f / v_lat
exposure ratio            = cumulative retreat / B_f   =   T_mob / (B_f / v_lat)
critical retreat rate v*  = B_f / T_mob
```

`exposure_ratio >= 1` is the screening flag. `v*` is the same statement with the
assumption moved onto one axis: **the rate it would take** to consume the bed.

**State variables.** `B_f` is the OYO 様式-3 高水敷幅 (high-water-bed width) of
`data/processed/tokachi_bep_inputs.csv` — source-verified 4/4 verbatim, equal to
the USACE $L_1$, and retained over the MLIT 2008 profile by
`docs/decisions/adr0025-foreshore-width-and-sensitivity.md`. This is the *right*
variable for this question and it is already source-verified, because the 2011
Otofuke failure was precisely the consumption of the 高水敷.

The mobilisation threshold `z_mob` is the high-water-bed surface elevation, taken
from `floodplain_m_msl` of `data/processed/uemura_segments/segment_inputs.csv`
(Uemura's `df_river` `FloodplaneHeight`, T.P. m MSL — the same datum as every
other stage in the three packages, and the committed table already used for the
Phase 3 surface curves). Justification: below the terrace the flood is confined
to the 低水路 and lateral attack proceeds at ordinary-flow rates, which the 2011
datum does not describe; above it, the flood engages the terrace across its full
width. This is a **choice**, so it is bracketed (§3).

**Forcing** is never invented. Three families, all from records that already
exist and are already verified:

1. `event_2016` — the observed August 2016 consecutive-typhoon record at each
   section, via `bayesian_reliability_updating.events.observed_event_record`
   (ADR-0035; hourly, 744 h window).
2. `design_hwl` / `conditioning_grid` — the Phase 1 conditioning records via
   `run.conditioning_hydrographs_for_config` (ADR-0020 canonical d4PDF shape
   scaled per level, ADR-0030 225 s grid). The design-class reading is the grid
   level nearest each section's own design HWL.
3. `d4pdf_ensemble` — the mobilising duration of every annual-maximum ensemble
   event, historical (HPB, 3,000 y) against +4K (HFB, 5,400 y), through the
   Phase 3 `hazard.load_reach_hazard` with the exposure datum set to `z_mob`.
   Under ADR-0023 the event *shape* is climate-invariant, so this is the only
   place a climate signal can appear for this indicator.

**Coverage.** `B_f` is measured only at the four confined OYO cross-sections, so
**4 of the 114 registry segments are screenable and 110 are not**. No width is
interpolated for the other 110 — the honest answer is the gap, reported as such
by `foreshore_coverage`. KP 63.4 (`B_f = 0`, "river-tight") lies outside both the
production population and the Phase 3 study reach and is therefore not a study
row; it is covered as the boundary case in the test suite instead, and ADR-0025
§8 already records that the MLIT 2008 profile reads ≈28 m there against the
CSV's 0.

## 3. The three brackets

None of the three inputs below is measured, so each is bracketed rather than
picked.

**(a) Retreat rate — the weak link.** There is no calibrated lateral retreat rate
for this mechanism on this river. The one documented datum is the 2011 Otofuke
KP 18.2 account of ~5 m of levee length per hour. Two things about it must be
said plainly and are said in the code, the JSON and here: it is **one observation
from a prose account in a flood-control history, not a calibrated rate**, and it
is a **longitudinal** rate (loss of levee *length*), not a lateral retreat rate.
It is carried into the bracket **unconverted**, as the labelled `narrative_2011`
member — a stated assumption, not a derivation. The bracket spans two orders of
magnitude:

| member | v_lat [m/h] |
|---|---|
| `low` | 0.1 |
| `central` | 1.0 |
| `narrative_2011` | 5.0 |
| `high` | 10.0 |

**(b) Mobilisation threshold — ±1.0 m.** The magnitude is not invented: at
KP 62.0 the OYO 1998 様式-5 高水敷高 reads **45.00 m T.P.** while the
MLIT-derived `df_river` reads **43.82 m** — a 1.18 m cross-source spread on the
same terrace, from sources 10–20 years apart.

**(c) Rate law.** The retreat rate is held constant while the bed is mobilised.
That is the **bounding** treatment: any monotone depth-dependent law calibrated
to the same peak rate erodes less over the same event. The size of that softening
is reported per case as `mean_excess_depth_m / peak_excess_depth_m`, measured at
**0.27–0.46** over the 2016 event — i.e. a depth-linear law would give exposure
ratios roughly 2–4× smaller than those below.

## 4. Results

### 4.1 The four screenable sections

Primary threshold, per forcing case (`T_mob` = mobilising hours; `v*` = critical
lateral retreat rate; ratio at the `central` 1 m/h member):

| Section | B_f [m] | z_mob [m MSL] | forcing | T_mob [h] | v* [m/h] | ratio @1 m/h |
|---|---|---|---|---|---|---|
| KP 57.4 | 200 | 36.41 | 2016 event | 46.0 | 4.35 | 0.230 |
| KP 57.4 | 200 | 36.41 | design HWL | 66.6 | 3.00 | 0.333 |
| KP 58.8 | 325 | 37.53 | 2016 event | 72.0 | 4.51 | 0.222 |
| KP 58.8 | 325 | 37.53 | design HWL | 84.4 | 3.85 | 0.260 |
| KP 60.0 | 600 | 40.25 | 2016 event | 22.0 | **27.27** | 0.037 |
| KP 60.0 | 600 | 40.25 | design HWL | 61.4 | **9.77** | 0.102 |
| KP 62.0 | **44** | 43.82 | 2016 event | 17.0 | **2.59** | 0.386 |
| KP 62.0 | **44** | 43.82 | design HWL | 61.4 | **0.72** | **1.395** |

**Sanity anchor met.** KP 62.0 (44 m) and KP 60.0 (600 m) separate by **10.5×**
under the 2016 event and **13.6×** at the design HWL, against a 13.6× width
contrast — asserted in the driver against a 5× floor, so the study cannot report
a result that has lost the separation.

Read across the bracket:

- **Under the 2016 event, no section is exposed at 0.1 or 1 m/h.** At the
  unconverted `narrative_2011` 5 m/h, **three of the four flip to exposed**
  (KP 62.0 ratio 1.93, KP 57.4 1.15, KP 58.8 1.11) and KP 60.0 does not (0.18).
- **At the design HWL, KP 62.0 is exposed already at 1 m/h** (ratio 1.40); every
  other section needs 3–10 m/h.
- At the top of each conditioning grid, KP 62.0 reaches ratio 2.42 at 1 m/h
  (`v*` = 0.41 m/h) while KP 60.0 is still at 0.14.

**The bracket straddles the verdict at every section.** Every critical rate in
the table — 0.72 to 27.3 m/h — sits inside or at the edge of the assumed 0.1–10
m/h range. Per Step 4 of the task framing, *that is the finding*: this indicator
does not deliver a clean verdict, and reporting the central value alone would
manufacture one. What it does deliver is a **robust ordering** and an
**order-of-magnitude scale**: the rate needed to consume the bed differs by
~38× across the four sections (0.72 → 27.3 m/h at the design HWL), and the
section whose narrow bed makes it the outlier — KP 62.0 — is the same section the
BEP branch already identifies as governing.

### 4.2 Threshold sensitivity (±1.0 m)

| Section | forcing | v* at z_mob−1 m | v* at z_mob | v* at z_mob+1 m |
|---|---|---|---|---|
| KP 57.4 | 2016 event | 1.79 | 4.35 | 11.76 |
| KP 58.8 | 2016 event | 1.35 | 4.51 | 14.77 |
| KP 60.0 | 2016 event | 7.69 | 27.27 | 66.67 |
| KP 62.0 | 2016 event | 0.80 | 2.59 | 6.29 |
| KP 62.0 | design HWL | 0.53 | 0.72 | 1.43 |

The threshold band moves `v*` by a factor of ~2–3 in each direction — **the same
order as the difference between the bracket's `central` and `narrative_2011`
members**. The threshold choice is therefore not a second-order detail; it is
co-equal with the retreat rate as a source of uncertainty here. The *ordering* of
the sections is unchanged across the whole band.

### 4.3 Climate (d4PDF ensemble, `z_mob` datum)

Share of simulated annual-maximum years in which the bed is engaged at all:

| Section | historical (3,000 y) | +4K (5,400 y) |
|---|---|---|
| KP 57.4 | 35.1% | 50.9% |
| KP 58.8 | 68.8% | 76.9% |
| KP 60.0 | 13.8% | 29.3% |
| KP 62.0 | 29.4% | 45.1% |

Mobilising-window p99 rises from 49/78/28/44 h to 62/89/42/56 h respectively.
Share of ensemble events tripping the screening flag (**an ensemble frequency of
a deterministic flag, not an annual failure probability**):

| Section | 1 m/h hist → +4K | 5 m/h hist → +4K | 10 m/h hist → +4K |
|---|---|---|---|
| KP 57.4 | 0% → 0% | 2.9% → 7.5% | 14.9% → 28.8% |
| KP 58.8 | 0% → 0% | 4.0% → 8.3% | 27.9% → 40.9% |
| KP 60.0 | 0% → 0% | 0% → 0% | 0.03% → 0.09% |
| KP 62.0 | **1.2% → 3.6%** | 23.2% → 38.7% | 27.4% → 43.0% |

Two readings. **KP 62.0 is the only study section whose flag trips at all at the
central rate, in either climate.** And the climate signal enters this indicator
exactly where the Phase 3 campaign already located it — through **duration**, not
through the stage dependence: the frequency of a bed-mobilising year roughly
doubles at three of the four sections under +4K, while the indicator's own
stage→ratio mapping is climate-invariant by ADR-0023.

(Ensemble durations are quantised to the native 1 h d4PDF cadence, the
conditioning records to 225 s; immaterial at these magnitudes.)

## 5. What this establishes — and what it does not

**Establishes.** Of the 114 Phase 3 segments, 4 carry a measured high-water-bed
width, and among those the exposure to a foreshore-exhaustion mechanism spans
roughly an order and a half of magnitude, ordered by bed width and modulated by
mobilising duration. KP 62.0 — 44 m of bed — is exposed at the design level for
any assumed lateral retreat rate above ~0.7 m/h and is the only section flagged
at the 1 m/h central rate in either climate; KP 60.0 — 600 m — would need ~10–27
m/h and is flagged in essentially no ensemble event. The mechanism omitted from
the composition is therefore **not uniformly relevant across the study reach**:
it concentrates on the same narrow-foreshore section the BEP branch already
identifies as governing, which sharpens the RQ3 qualification rather than
diffusing it.

**Does not establish.** It is **order-of-magnitude screening**. It is not a
probability, not a failure rate, and it cannot enter the series composition. It
carries:

- **no planform** — no bar dynamics, no bend migration, no sediment supply;
- **no near-bank hydraulics** — the rate is assumed, not computed from a velocity
  field, and there is nothing in it that makes a *receding* flood more dangerous
  than a peak one, which is precisely the signature of three of the four
  documented failures;
- **no explanation of exposure** — nothing represents *why* a thalweg approaches
  one bank rather than another, so it cannot discriminate between two segments of
  equal bed width;
- **no validation** — the two 2016 bank-erosion failures (Otofuke KP 21.2,
  Satsunai KP 40.5) lie outside both modelled study reaches, so the falsification
  test that makes Tier 2 scientifically worthwhile (reproduce those failures while
  the study sections survive) **cannot be run at Tier 1** and has not been.

It answers "is there enough high-water bed to survive this flood at this assumed
retreat rate", never "will this levee fail".

## 6. Scope discipline actually observed

- No `Config` field, no configuration axis, no production default touched.
- `data/processed/tokachi_bep_inputs.csv`, `configs/` and every persisted sweep
  untouched; the driver **asserts** the four `foreshore_width_m` values still read
  200 / 325 / 600 / 44 m before reporting anything, because an edit there would
  invalidate all 8 Phase 1 sweeps and the Phase 2 replay hash gate.
- No mechanism added to `system_integration.composition`;
  `tests/test_foreshore_exhaustion.py::test_screening_module_is_not_wired_into_the_phase_3_composition`
  pins that structurally. The Phase 3 campaign was re-run after this work and all
  twelve output artifacts are **byte-identical** (SHA-256) to the pre-work
  baseline.
- Nothing persisted to `results/` as a deliverable; the evidence JSON lands in
  `docs/decisions/`. The optional ensemble arm caches its per-event tables under
  the gitignored study-local `results/sensitivity/foreshore_exhaustion/hazard_cache/`,
  never the production Phase 3 hazard cache (the exposure datum differs).

## 7. What would re-open this

- **A retreat-rate measurement.** Anything that converts the 2011 narrative into
  a lateral rate — repeat aerial/satellite planform surveys across the 2016
  event, the MLIT 河道変化 series, or the Chiyoda experimental-channel campaign —
  would collapse the dominant bracket and could turn the screening flag into a
  defensible statement.
- **Foreshore widths at more than four nodes.** The MLIT 2008 堤防現況縦断図 row
  4)② carries 高水敷幅 longitudinally but **clips at ~150 m** (ADR-0025 §4), so it
  can only extend coverage where the bed is narrow — which, for this indicator,
  is exactly where it matters. Digitizing the KP 60.3–63.9 reach (17–35 m
  throughout) would extend the screening to the whole narrow-bed zone.
- **A decision to build Tier 2.** That adds a mechanism to a closed campaign,
  needs ADR-0047, must be default-OFF and bit-identical at baseline, and belongs
  in a quarantined module in the ADR-0042 sense. Its value is the falsification
  test in §5, not the extra number.
- Tier 3 (morphodynamic coupling) is **declined in writing** and recorded as
  further work.

## References

- Scoping note `docs/scoping_bank_retreat_mechanism.md` (Tier definitions; the
  owner's Tier 1 / decline decision).
- `docs/decisions/adr0025-foreshore-width-and-sensitivity.md` — the B_f
  definition (高水敷幅 = USACE $L_1$), the 4/4 verbatim source verification, the
  MLIT 2008 corroboration, the OYO-retention decision, and the KP 62.0
  高水敷高 = 45.00 m T.P. reading behind this note's ±1 m threshold band.
- **ADR-0042** decision 9 (the dimensionally-corrected scour conversion that
  zeroes P2), **ADR-0043** (the Phase 3 section table), **ADR-0038** (the
  registry), **ADR-0035** (the 2016 observed record), **ADR-0020**/**ADR-0030**
  (the conditioning records), **ADR-0023** (climate shape invariance).
- `docs/tokachi_basin_document_review_2026-07-27.md` §10.2 (review item R10) and
  the 2011/2016 failure attributions; 続十勝川治水史 (2023) for the 堤防防御ライン
  required-high-water-bed-width methodology and the Otofuke KP 18.2 account.
