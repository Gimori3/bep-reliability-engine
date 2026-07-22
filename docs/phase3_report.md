# Phase 3 Report — Multi-Mechanism System Integration (RQ3 + RQ4)

Session: 2026-07-17/18, branch `feature/phase3-uemura-integration`.
Mission: one-shot execution of Phase 3 — feed the ADR-0038 skeleton the
real Uemura surface-failure data, run the full RQ3 (multi-mechanism
dominance) and RQ4 (climate-shifted annualized failure probability)
campaigns on the real d4PDF ensembles, validate, document, commit.

Headline results are in §5–§7; §9 is the updated blocker manifest.
Machine-readable results: `results/system_integration/phase3/`;
figures: `docs/figures/phase3_*.png`; decisions: ADR-0042, ADR-0043.

---

## 1. Phase A census of the 2026-07-17 data drop (GO)

Drop location: `data/digitized/uemura_fragility_curves/` (~140 MB, now
gitignored like the 2016-event drop; committed extracts under
`data/processed/`). File-by-file verdicts:

| File | Verdict |
|---|---|
| `Uemura et al., 2024.pdf` (Proc. IAHS 386) | **Authoritative** for the overflow (P1) model semantics: MC over rating error, per-KP crest error, turf critical velocity; Dean cumulative-work threshold; sine T=30 h fragility construction; section rules Eqs. 14–18. Read in full. |
| `Uemura_Fumihiko.pdf` (PhD thesis, Japanese, 122 pp) | §4.2–4.3 read (text layer intact): confirms the paper's equations verbatim (4.6–4.11), the erosion model per USACE, N=10,000, and per-gauge rating-uncertainty structure (Fig. 4.12 — Tokachi gauges only). |
| `WP2 - Report Flood Risk and Climate Change Hokkaid...pdf` (HKV PR3983, June 2024) | **Authoritative** for the fluvial-scour (P2) model (§5: Manning velocity, USACE f_c, k/tau_c Table 1, effective-width criterion), the segment/section architecture (Ch. 2–3), and the event-based system results (Tables 3–6) used as validation anchors. Read in full. |
| `data/df_river.csv` | **The load-bearing input**: Uemura's consolidated per-KP table on the exact 0.2 km study-reach grid (Tokachi 53.8–62.8, Satsunai 3.2–17.2), all levee/channel parameters. `HQ_a`/`HQ_b` **numerically identical** to the local M3 rating files — the stage axis is already the ADR-0021 T.P. m MSL datum. Committed verbatim + adapted (`data/processed/uemura_segments/`). |
| `ErosionModel_231019.py` | Uemura's own scour implementation (authoritative over the report's imperial-constant typo); transcribed into `system_integration/uemura_models.py` with a pinned equivalence test. |
| `2021-11-19 Description WP2 Work week 3.ipynb` | The WP2 team's full workflow incl. the vectorized overflow reference implementation (`count_failures`) and the section-combination code; an embedded output dump supplied ten verbatim node→section assignments (ADR-0043 anchors). |
| `Description WP2 Work week 3.ipynb`, `Work package 2.html` | Earlier copies of the same notebook; the old copy's survey dump is the source of the 66-segment coverage count used as independent validation. |
| `2021-11-23 Analyse representative hydrograph shape...ipynb` | Hydrograph-shape exploration; superseded by the M3 canonical-shape machinery (their own notebooks mark the shape as a WP1/WP3 placeholder). Not used. |
| `Probability of Overtopping_ObihiroKP56.73.xlsx` (97 MB) | **2020-era prototype** (single-time-step peak-velocity judgment, generic sigma_crest = 0.7), superseded by the Dean cumulative model. Classified qualitative-only; not an anchor. |
| `output/check*.csv`, `output/test.csv` | 2020 prototype MC dumps belonging to the xlsx generation. Not used. |
| `data/HydroData_HFB_*.csv` | CSV copies of the same three HFB discharge ensembles already secured as workbooks under `data/raw/hydrographs/`. Redundant; the M3 workbook path is used. |
| `Riverline/` shapefile | MLIT W05 river-network layer (not the section classification). Not used — the section geometry was already local (`data/raw/gis/SECTIONS.shp`). |

**GO basis:** the minimum viable dataset (per-segment conditional failure
information for both mechanisms as a function of water level, placeable on
the 0.2 km grid and the T.P. datum) exists — not as curve tables but as
*models + exact inputs + published parameterization*, which is stronger:
re-execution covers all 114 segments × 2 mechanisms at machine precision
with per-value provenance. The section-aggregation scheme (D2) was fully
recoverable from `SECTIONS.shp` + the notebook anchors.

## 2. Decisions and findings

* **ADR-0042 (surface curves by faithful re-execution).** Primary curves:
  Uemura's P1/P2 models re-executed per segment, conditioned per stage
  level on the production canonical d4PDF shape (`HPB_m064_1987`, the same
  G1 rule that conditioned every BEP curve), common random numbers across
  levels (curves exactly monotone by construction), N_MC = 10,000.
  Scenario labels carry identical curves (climate enters through the
  hazard side only — the ADR-0023 structure). Companions: sine-T=30 h
  overflow set (his published construction) and an as-received script-k
  scour set (`scour_script_k`).
* **Finding 1 — the scour k unit conversion (ADR-0042 decision 9, amended
  2026-07-21).** `ErosionModel_231019.py` converts k = 0.021 ft³/(lb·hr) to
  SI with the factor `0.3048/0.45359237` (≈0.672) — a linear ft→m times a
  pound-*mass*→kg factor. k is an erosion rate per unit *stress*, so the
  dimensionally correct factor is `0.3048/47.8803` (≈0.00637), **105.6×
  smaller**. The script factor is indefensible under any reading (and its
  converted value is moreover *unused* in his own MC loop — dead code — so
  it is a slip, not a calibration). **The primary curves now use the
  corrected USACE conversion**, under which fluvial scour is negligible at
  every one of the 114 nodes (0 failures / 10,000 draws); the as-received
  script factor is retained as the labeled `scour_script_k` sensitivity
  companion. His published WP2 erosion-dominance rests on the large,
  dimensionally-wrong rate and is not reproduced here (a documented, not
  hidden, divergence — §7). Reversal rationale in ADR-0042 (amended) and §8.
* **Finding 2 — the USACE f_c log-law singularity (ADR-0042 decision 10).**
  f_c diverges at floodplain depth k_b/30 ≈ 1.6 mm; his script inherits
  this. On the conditioning ladder it produced a +0.35 single-level
  artifact (caught by the contract loader's monotonicity gate). A 0.05 m
  erosion-onset depth floor (tau(0.05 m) ≈ 1 Pa ≪ tau_c ≈ 50 Pa) removes
  the unphysical sliver and restores exact monotonicity — the only
  deliberate behavioural deviation from his script, pinned by a test.
* **ADR-0043 (section table reconstruction).** The 9 sections (Tokachi
  KP62.4/61.4/59.6/58.0/56.4; Satsunai KP7.0/6.4/5.2/4.2 — the thesis's
  "Tokachi 1–5 / Satsunai 1–4" in upstream→downstream order) are
  reconstructed as KP ranges from Uemura's own `SECTIONS.shp` with
  executable validation: polyline arc lengths (Satsunai chain boundaries
  at KP 4.69/5.97/6.50/6.96; Tokachi midpoint tiling within one grid step
  of every polyline length) and the ten notebook anchor assignments. The
  committed table sections **66 of 114 segments — exactly the segment
  count of Uemura's own notebook assignment output**, an independent
  confirmation. Within-section rule: his Eq. 14 max (full dependence);
  his between-section upstream-failure discounting is out of scope
  (serves his basin total, not per-section RQ3/RQ4).
* **Registry fix.** `build_registry` now filters to the 0.2 km survey
  grid; the rating files also carry off-grid gauge nodes (e.g. Tokachi
  KP 56.73 = the Obihiro gauge) that are not evaluation segments. The
  registry is exactly the 114 thesis segments (46 Tokachi + 68 Satsunai).
* **Rating-error values (ADR-0042 decision 6, amended 2026-07-22).** The
  source workbook `Uncertainty_HQrelation.xlsx` arrived (gitignored,
  machine-local under `data/raw/`) and supplies both gauges' rating error:
  Obihiro (Tokachi) N(-0.16, 0.29) m, Nantai (Satsunai) N(-0.05, 0.28) m —
  replacing the interim 0.6/0.38 m for both rivers. D7 closed (§9).

## 3. Data products (committed, regenerable)

| Product | Source command |
|---|---|
| `data/processed/uemura_segments/segment_inputs.csv` (+ verbatim mirror, provenance.md) | `python scripts/adapt_uemura_inputs.py` |
| `data/processed/uemura_segments/section_table.csv` | `python scripts/build_section_table.py` |
| `data/processed/uemura_surface_curves/uemura_surface_curves_{historical,plus4K}.csv` (primary ADR-0038 contract set, split per scenario for the 500 KB hygiene guard; identical curve values; scour carries the corrected USACE conversion) + `_overflow_sine30h` + `_scour_script_k` (as-received scour) companions + generation_metadata.json | `python scripts/generate_uemura_surface_curves.py` |
| `results/system_integration/phase3/*` (rq4_annual.csv, rq3 curve/section JSONs, attribution, summary) | `python scripts/phase3_campaign.py` |
| `results/system_integration/phase3/event_based_validation.json` | `python scripts/validate_event_based_surface.py` |
| `docs/figures/phase3_*.png` | `python scripts/phase3_figures.py` |

New package code: `system_integration/uemura_models.py` (quarantined
external-model reproductions), `composition.max_within_section`,
`hazard.load_reach_hazard` (one workbook stream for all nodes),
`segments.load_section_table(allow_gaps=...)`. Tests:
`tests/test_uemura_models.py` (16), `tests/test_phase3_campaign_units.py`
(8), on top of the existing 24 system-integration tests.

## 4. Campaign design

Variant axes actually executed (per segment × scenario):

* d70: **matrix** (primary) and **bulk** (co-primary bound);
* BEP source: **Phase 2 posterior** (default) and Phase 1 prior (labeled
  companion) — transient branch, ADR-0024 evaluation semantics, ADR-0037
  length effect applied at composition;
* lambda_ac: **250 m** (primary, n_eff = 1) with the 100/40 m bracket
  (posterior members);
* surface variant: **primary** (corrected USACE scour) plus the
  `scour_script_k` (as-received scour) and `overflow_sine30h` companions
  (posterior-matrix).

Hazard: empirical annual-maximum peak-stage distribution per node and
scenario through verbatim M3 (HPB 3,000 yr / HFB 5,400 yr), streamed once
per band workbook into `results/system_integration/hazard_cache/`.
Composition grid per segment: union of the surface-curve grid and (where
present) the BEP conditioning grid; BEP curves never extrapolate above
their grid (ADR-0024 clamp, flagged per segment).

## 5. RQ3 — multi-mechanism dominance

### 5.1 At the four BEP sections (posterior, matrix d70, lambda 250 m)

Annualized per-mechanism failure probabilities and dominance shares
(`rq4_annual.csv`; figure `phase3_dominance_profile.png`,
`phase3_system_fragility_bep_sections.png`):

| Section | Scenario | P_sys [1/yr] | BEP | share | Overflow | share | Scour |
|---|---|---|---|---|---|---|---|
| KP57.4 | historical | 7.53e-4 | 7.53e-4 | **100%** | 0 (exact) | 0% | 0 |
| KP57.4 | +4K | 9.53e-3 | 9.48e-3 | **91%** | 9.11e-4 | 9% | 0 |
| KP58.8 | historical | 7.42e-3 | 7.34e-3 | **97%** | 1.95e-4 | 3% | 0 |
| KP58.8 | +4K | 4.09e-2 | 4.04e-2 | **94%** | 2.53e-3 | 6% | 0 |
| KP60.0 | historical | 1.80e-3 | 1.80e-3 | **100%** | 0 (exact) | 0% | 0 |
| KP60.0 | +4K | 1.42e-2 | 1.42e-2 | **100%** | 2.3e-5 | 0% | 0 |
| KP62.0 | historical | 5.24e-4 | 3.5e-4 | **64%** | 1.99e-4 | 36% | 0 |
| KP62.0 | +4K | 1.02e-2 | 4.40e-3 | 34% | 8.39e-3 | **66%** | 0 |

**BEP is the dominant mechanism at all four quantified sections
historically** (64–100% of the summed annual contributions) and at three of
the four under +4K. Overflow leads only at KP62.0 under +4K (66%) — the
section whose transient BEP transition sits above attainable stages
(ADR-0024 raw-tail clamp; its BEP number is a grid-clamped lower bound,
flagged `bep_clamped_above_grid` in every output row, so its true BEP share
is if anything higher). **Fluvial scour is exactly zero at every section
under the dimensionally-correct USACE conversion** (ADR-0042 decision 9,
amended); the `scour_script_k` companion quantifies what the as-received
conversion would have added — at the three BEP-dominant sections at most ~8%
(KP57.4 historical system 7.53e-4 → 8.13e-4; ≤2% at KP58.8/60.0), rising to
~45% at the overflow-reduced KP62.0 (5.24e-4 → 7.59e-4) because the surface
number there is now small (§6.2).

The conditional-curve picture (`phase3_system_fragility_bep_sections.png`)
explains the shares: at KP57.4/58.8/60.0 the posterior BEP transition
rises 1–2 m below the overflow onset (which needs crest exceedance within
the rating-error scatter), so the subsurface mechanism strikes first in
stage; at KP62.0 the order reverses only once the +4K hazard lifts peaks
into the overflow band.

### 5.2 Along the full reach (110 surface-only segments)

Per-segment dominant-mechanism counts (largest annual contribution,
posterior-matrix primary):

| Scenario | overflow | fluvial_scour | bep | none loaded |
|---|---|---|---|---|
| historical | 31 | 0 | 4 | 79 |
| +4K | 110 | 0 | 3 | 1 |

Two readings, both load-bearing:

* Under the dimensionally-correct conversion **overflow is the only surface
  mechanism that produces failures**. Historically it dominates just 31 of
  114 segments, with 79 "none loaded" — segments whose peaks never reach the
  crest under the historical hazard, so with scour removed no surface
  mechanism fires. (Under the as-received `scour_script_k` companion scour
  would instead be the historical dominant at ~70 of the surface-only
  segments — the reach-wide *surface* dominance is entirely conditional on
  the k-conversion; the overflow-vs-BEP comparison is not.)
* The +4K hazard makes overflow near-universal (110/114) because peaks
  reach the crests far more often. This sparse-historical / pervasive-+4K
  overflow split is the corrected reading; it replaces the earlier picture
  of near-universal historical overflow, which was inflated by the +0.6 m
  rating-error mean now corrected to −0.16/−0.05 m (§8, D7).
* The 110 segments without BEP curves are **surface-only lower bounds** —
  the borehole-free reaches carry unquantified BEP risk (the thesis's
  bounded-extrapolation tier; close-out manifest item 24 remains future
  work). The single riskiest segment of the whole basin in both scenarios
  is BEP-driven KP58.8 (7.4e-3 historical, 4.1e-2 +4K), so this gap is
  material, not cosmetic.

### 5.3 Uemura sections (Tokachi 1–5, Satsunai 1–4)

Discharge-aligned max-within-section (ADR-0043 decision 3;
`rq3_sections_matrix_posterior.json`):

| Section | Members | Historical [1/yr] | +4K [1/yr] | Ratio |
|---|---|---|---|---|
| KP62.4 (Tokachi 1) | 5 | 6.9e-4 | 1.2e-2 | 17 |
| KP61.4 (Tokachi 2) | 7 | 3.7e-7 | 2.4e-3 | ≫ |
| KP59.6 (Tokachi 3) | 8 | 1.8e-3 | 1.4e-2 | 8.0 |
| KP58.0 (Tokachi 4) | 8 | **7.5e-3** | **4.1e-2** | 5.5 |
| KP56.4 (Tokachi 5) | 18 | 1.7e-5 | 3.8e-3 | 225 |
| KP7.0 (Satsunai 1) | 3 | 1.1e-8 | 9.0e-4 | ≫ |
| KP6.4 (Satsunai 2) | 3 | 1.9e-7 | 1.5e-3 | ≫ |
| KP5.2 (Satsunai 3) | 6 | ~0 | 2.2e-4 | ≫ |
| KP4.2 (Satsunai 4) | 8 | ~0 | 1.1e-5 | ≫ |

(`≫` = historical annual at/near the display floor after the rating-error
correction, so the ratio is not meaningful.)

Section Tokachi 4 (KP58.0) governs the basin in both climates, and its
governing member is the BEP-dominant segment KP58.8 — the subsurface
mechanism controls the worst-consequence section, and it is essentially
unmoved by the rating-error correction (7.9e-3 → 7.5e-3 historical). The
BEP-driven Tokachi 3/4 barely move; the overflow-influenced sections
(Tokachi 1/2/5 and all four Satsunai) fall sharply, their historical annuals
now at or near the display floor, so their historical→+4K ratios are not
meaningful (marked ≫). (Execution note: a naive absolute-stage section max
was caught overstating KP56.4 by ~200x through datum mixing; the committed
rule inverts the Eq. 4.19 rating exactly and takes Uemura's Eq. 14 max
conditional on discharge.)

## 6. RQ4 — climate sensitivity and attribution

### 6.1 Annualized shift (posterior matrix, lambda 250)

Across all 114 segments (figure `phase3_climate_shift.png`): the median
annual system failure probability rises from **0 historically to 3.7e-4** —
more than half the segments carry no historical failure at all, because with
the corrected rating error historical peaks rarely reach the crest and scour
is zero — while the mean rises 1.0e-4 → 1.9e-3 (~18x). Segments above
1e-3/yr go from **2 to 45 of 114**, above 1e-2/yr from 0 to 4. The
historical→+4K contrast is carried by the many surface-only segments that
switch from exactly zero to loaded once +4K lifts their peaks over the
crest. At the BEP sections the system ratio is 5.5–19.5x (KP57.4 12.7,
KP58.8 5.5, KP60.0 7.9, KP62.0 19.5 — the last raised because its overflow
floor fell). Per-segment ratios above ~100 occur only where the historical
probability is near-floor (display floor 1e-7 marks exact zeros).

### 6.2 Sensitivity brackets

* **ADR-0037 lambda bracket** (system P_f at lambda 40 m vs 250 m):
  x3.4/x2.2 (KP57.4 hist/+4K), x2.5/x2.1 (KP58.8), x3.4/x2.7 (KP60.0),
  x3.1/x1.6 (KP62.0 — now BEP-dominant historically, so BEP upscaling
  matters here too, unlike under the pre-correction overflow dominance).
* **d70 interpretation**: the bulk co-primary cuts the BEP-driven system
  numbers (KP58.8 +4K: 4.1e-2 → 2.7e-3, x15; KP57.4 historical:
  7.5e-4 → 2.1e-6 as the historical number drops to the floor); KP62.0 now
  also gets cut (historical x2.6, +4K x1.2) since it is BEP-dominant.
* **Prior vs posterior BEP**: the 2016 constraint lowers the system number
  ~12% at KP58.8 historical (8.47e-3 → 7.42e-3) and <2% elsewhere — the
  Phase 2 result that the survival evidence is modestly informative
  propagates to the system level.
* **Surface companions**: `scour_script_k` (the as-received conversion)
  raises the three BEP-dominant sections' system numbers by at most ~8%
  (KP57.4 historical 7.53e-4 → 8.13e-4; ≤2% at KP58.8/60.0), and the now
  overflow-reduced KP62.0 by ~45% (5.24e-4 → 7.59e-4) — the as-received
  scour matters most where the corrected surface number is small.
  `overflow_sine30h` (his published sine pulse) lowers the KP62.0 system
  ~19–27% (KP62.0 +4K 1.02e-2 → 8.25e-3, historical 5.24e-4 → 3.81e-4) —
  the duration sensitivity of the Dean integral.

### 6.3 Attribution (duration / compound; `rq4_attribution.json`)

| Section | Scenario | Years loading toe | >24 h years | P_f long | P_f short | ratio |
|---|---|---|---|---|---|---|
| KP57.4 | hist → +4K | 4.3% → 14.1% | 0.1% → 0.8% | 0.099 → 0.385 | 6.6e-4 → 7.0e-3 | ~150x/55x |
| KP58.8 | hist → +4K | 24.7% → 40.8% | 5.1% → 13.5% | 0.136 → 0.285 | 9.5e-4 → 4.6e-3 | ~143x/62x |
| KP60.0 | hist → +4K | 20.5% → 36.6% | 3.5% → 9.8% | 0.048 → 0.129 | 1.3e-4 → 1.8e-3 | ~369x/72x |
| KP62.0 | hist → +4K | 10.4% → 24.3% | 0.6% → 3.4% | 0.227 → 0.312 | 9.6e-4 → 9.8e-3 | ~236x/32x |

Annual system risk concentrates two orders of magnitude in the
long-duration-loaded years, and the +4K ensemble roughly triples the
frequency of exactly those years (KP58.8: 5.1% → 13.5% of years above the
toe for >24 h) — the duration channel, not the peak channel alone, carries
the climate signal. Compound years (≥2 excursions) sit between the two
duration strata everywhere (figure `phase3_rq4_attribution.png`).

## 7. Validation

* **Internal (canonical curves vs event-based re-execution at the 9
  section nodes; figure `phase3_event_based_validation.png`)**: overflow
  agrees to a factor ~1.0–1.9 (curve-based mildly conservative, mostly
  within tens of percent — the canonical-shape conditioning is essentially
  exact for the crest-exceedance mechanism). Under the dimensionally-correct
  conversion **fluvial scour is zero both curve-based and event-based at
  every node**, so the earlier curve-vs-event scour discrepancy is moot; the
  composed system numbers are overflow/BEP-driven.
* **External (WP2 report Table 4 overtopping, +4K)**: with the corrected
  rating error the event-based +4K overflow annuals now sit close to
  Uemura's own overtopping numbers at the mid-reach Tokachi sections
  (KP56.4 3.2e-3 vs his 3.9e-3; KP58.0 1.6e-3 vs his 1.3e-3; within ~20%) —
  a genuine tightening, since he computed those with these same workbook
  rating-error values. Historical overflow is now sparse (§5.2), so the
  historical comparison is floor-limited rather than informative. Their
  headline "erosion dominates overtopping" still does **not** reproduce here
  — the more so under the corrected scour conversion, which zeroes fluvial
  scour at every node; overflow is the only surface mechanism producing
  failures. The scour-magnitude comparison to their Tables 3/4 is moot on
  our side (our scour is zero); the WP1-hydrograph-provenance question (D8)
  is retained only for completeness.
* **WP2 Fig. 13 features**: the Satsunai high-internal-ground behaviour
  (his KP7.0/12.8/16.4 remark) is reproduced mechanically (the ground gate
  is test-pinned). With fluvial scour corrected to zero the surface-mechanism
  section ordering is set by overflow rather than scour; his scour-based
  ordering reproduces only under the `scour_script_k` (as-received)
  companion.
* **Invariants, all PASS** (executed on the shipped outputs): dominance
  shares sum to 1 wherever any mechanism is loaded; series-system bounds
  max_i P_i <= P_sys <= sum_i P_i on all 2,280 annual rows; scenario rows
  of the surface CSV byte-identical (ADR-0042 decision 4 / ADR-0023
  structure); all 912 committed curves re-validated through the contract
  loader (strict monotonicity); composition algebra, section rule, and
  hazard multi-node loader pinned by unit tests against hand-computed
  cases; full suite green.

## 8. Caveats (carried explicitly on every consumer)

1. **Scour k-conversion (Finding 1)** — the primary now uses the
   dimensionally-correct USACE conversion, under which fluvial scour is
   negligible at every segment; the as-received script conversion (under
   which scour contributes) is retained as the labeled `scour_script_k`
   companion. The thesis does not claim to reproduce Uemura's WP2
   erosion-dominance result; the divergence is documented (§7), not hidden.
2. **Drained sections**: the BEP curves evaluate the unremediated
   foundation at KP58.8/KP60.0 (`remediation_state` is a label; close-out
   decision item, unratified). The system dominance of BEP at those
   sections is an as-if-undrained statement.
3. **KP62.0 raw-tail clamp**: its BEP contribution is a lower bound above
   the conditioning grid (never extrapolated, ADR-0024); its true BEP
   share may be higher than 12–17%.
4. **Canonical-shape conditioning**: shared by all three mechanisms
   (deliberately — clean conditional independence given h); quantified
   against event-based re-execution in §7 (exact for overflow, 2–15x
   conservative for scour).
5. **Stage-axis semantics**: the composed curves condition on the
   median-rating stage; Uemura's rating-error term lives inside the
   overflow curve (his published semantics, thesis-blessed), while the
   BEP curve treats the same axis as realized stage — an inherent seam of
   composing "as received" curves, first-order-bounded by the Phase 2
   anchor sensitivity (close-out §2.3).
6. **Surface-only segments** (110 of 114) are lower bounds missing the
   BEP mechanism entirely; the borehole-free-reach prior extension
   (manifest item 24) remains future work with its own ADR.
7. **Rating-error values now measured for both gauges** (ADR-0042
   decision 6, amended 2026-07-22) from `Uncertainty_HQrelation.xlsx` —
   Obihiro N(-0.16, 0.29) m, Nantai N(-0.05, 0.28) m — replacing the interim
   0.6/0.38 m; both rivers now carry `wl_err_assumed=False`. No longer a
   limitation; retained here for traceability of the correction (D7 closed).

## 9. Blocker manifest (updated; supersedes close-out items D1/D2)

* **D1 — CLOSED** by ADR-0042 re-execution. The scour k-conversion question
  (former residual (i)) is **resolved 2026-07-21** (ADR-0042 decision 9
  amended): the primary adopts the dimensionally-correct USACE conversion on
  dimensional grounds, with the as-received conversion retained as a labeled
  `scour_script_k` companion; no owner confirmation is pursued (the author
  disclaimed hydraulics expertise and deferred the unit question, and the
  channel was judged unproductive). Residual: (ii) if his final curve tables
  ever materialize, they drop into the same contract CSV and everything
  regenerates in minutes.
* **D2 — CLOSED** by ADR-0043 reconstruction (validated against his own
  geometry and assignments). Residual: an owner-supplied authoritative
  table replaces one committed CSV verbatim.
* **D7 — CLOSED 2026-07-22.** `Uncertainty_HQrelation.xlsx` arrived
  (gitignored, machine-local under `data/raw/`) and is the direct
  implementation of paper Eqs. (9)/(10). Both gauges' measured rating error is now wired
  (`scripts/adapt_uemura_inputs.py`; ADR-0042 decision 6 amended): Obihiro
  (Tokachi) (-0.160, 0.294) m, Nantai (Satsunai) (-0.051, 0.283) m — the
  interim 0.6/0.38 traced to his demo notebook, not Eq. 10. Overflow curves
  regenerated; the KP62.0 dominance flip and the reduced reach-wide overflow
  are reflected in §5–§7.
* **NEW D8 — WP2 WP1-hydrograph provenance question** (not blocking):
  which discharge ensembles (duration, member count) fed their Tables
  3/4 — was needed to close the residual scour-magnitude gap in §7, now
  largely moot since the corrected scour is zero; retained for completeness.
* Unchanged from the close-out: D3 (2011 record), D4 (OYO longitudinal
  profile), D5 (Pol confirmations), D6 (Tokoro gauge), the
  drained-section presentation decision, and manifest item 24
  (borehole-free-reach priors ADR).

## 10. Reproduction

```powershell
python scripts/adapt_uemura_inputs.py          # raw drop -> committed inputs
python scripts/build_section_table.py          # SECTIONS.shp -> section table
python scripts/generate_uemura_surface_curves.py   # ~15 min, seeded
python scripts/phase3_campaign.py              # ~10 s (hazard cached; ~5 min cold)
python scripts/validate_event_based_surface.py # ~3 min
python scripts/phase3_figures.py
```

Full gates at close: `pytest` (all tests), `ruff check .`, `black
--check .` — green. Raw drop files were never modified.
