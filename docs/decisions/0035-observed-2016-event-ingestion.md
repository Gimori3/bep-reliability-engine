# ADR-0035: Ingestion of the Observed 2016 Event as Per-Section Loading Records

Date: 2026-07-12

## Status
Accepted

---

## Context

Phase 2 needs the deterministic 2016 typhoon hydrograph h_2016(t) at each
study cross-section (Tokachi KP 57.4, 58.8, 60.0, 62.0), on the m MSL
datum of the Phase 1 engine, at the hourly native cadence, through the
Phase 1 `HydrographRecord` interface (spec section 8; phase2_interface.md
section 3.1). The agency data drop `data/digitized/2016_event_data/`
(inventoried 2026-07-12; extraction script `scripts/extract_2016_event.py`,
committed extracts in `data/processed/2016_event/`) supplies:

- Hourly observed stage and published discharge at 30 stations, August
  and September 2016. The only Tokachi mainstem gauge near the study
  reach is Obihiro (KP 56.6), the ADR-0019 section 4 validation-anchor
  station, 0.8 to 5.4 km downstream of the sections. The September STAGE
  sheet of the source workbook is a corrupted duplicate of the September
  discharge sheet, so observed stage exists for August only.
- The September 2016 post-flood trace survey: surveyed maximum water
  levels on both banks at 0.2 km spacing, m MSL, including all four study
  KPs (right bank, the study levees' bank per the R-prefixed OYO section
  drawings).

Three datum checks tie the gauge series to m MSL: the low-flow stage sits
a few decimetres above the KP 56.6 rating datum term (-b = 32.49 m), the
observed peak (38.07 m, 2016-08-31T04:00) sits 0.07 m below the 38.14 m
MSL design HWL consistent with the ADR-0019 "~0.2 m below HWL" record,
and the trace table's design-HWL column reproduces the config HWL values
(41.03 m at KP 58.8).

Two measured complications shape the construction:

1. The observed (Q, h) pair at the gauge does NOT sit on the 2017 rating:
   Eq. 4.19 with the published peak discharge (6,334 m^3/s) over-predicts
   the observed peak stage by ~1.1 m (post-flood channel geometry and
   loop-rating effects). Feeding published discharge through the rating
   would overstate the loading, which for survival updating is
   anti-conservative (it would over-tighten the posterior).
2. The pure stage translation (observed gauge stage inverted through the
   gauge rating, re-rated at the section KP) lands within -0.5 to +1.2 m
   of the surveyed traces at the four sections, with the largest error
   (+1.16 m over-prediction) at KP 62.0, the section where decimetres
   matter most.

## Decision

Per-section records are built by the reusable loader
`bayesian_reliability_updating.events` as follows:

1. **Gauge assignment**: one reference gauge per reach, Obihiro (KP 56.6)
   for all four Tokachi sections. This mirrors the Phase 1 d4PDF band
   structure exactly: the band workbook KP 056.20 to 061.80 that drives
   these sections in Phase 1 carries one discharge series for the whole
   reach, and the Obihiro gauge sits inside that band (the Satsunai and
   Otofuke confluences bracket the reach outside it).
2. **Stage-anchored inverse rating**: the rating-equivalent discharge
   Q_eq(t) = a_g (h_obs(t) + b_g)^2 is computed from the OBSERVED STAGE
   at the gauge (not the published discharge) and re-rated at the study
   section's own KP through the verbatim M3 path
   (`build_hydrograph_record`, Eq. 4.19). The inverse-then-forward
   composition reproduces the observed series exactly at the gauge, and
   along the reach the rating acts only differentially, so its absolute
   bias largely cancels.
3. **Trace anchoring (default)**: the translated series is rescaled in
   stage domain so its peak equals the surveyed right-bank trace at the
   section KP verbatim, with the trough floor pinned at the translated
   base-flow stage: h(t) = h_base + (trace - h_base) * shape(t), the
   same G1 rule as the Phase 1 conditioning sweep
   (`normalize_stage_shape`). The unanchored translation stays available
   as `anchor='rating'` (sensitivity), plus `anchor='trace_left'`.
4. **Low-flow flooring**: gauge readings below the flood-rating datum
   (up to 0.82 m during the pre-typhoon weeks; the rating has no
   validity at low flow) invert to zero discharge; an excursion beyond
   2.0 m still raises as a datum error. Floored samples translate to the
   section's own rating datum, several metres below every landside toe,
   hydraulically inert for BEP.
5. **Window**: the full August observation window (2016-08-01T01:00 to
   2016-09-01T00:00 JST, 744 hourly samples) is used unmodified: no
   smoothing, no clipping, all four typhoon peaks and troughs verbatim.
   The truncated September recession is proven inert per section by the
   `window_closure_diagnostic` (the window-end stage sits 0.4 to 2.1 m
   BELOW each section's landside toe, where the ADR-0027 erosion head is
   negative and progression is identically zero); the replay logs a
   warning if any future event record ends above the toe.

Constructed peaks and closure at the four sections (right-bank traces):

| KP | z_toe [m MSL] | trace peak [m MSL] | rating-only peak | end margin below toe [m] | hours at or above toe |
|---|---|---|---|---|---|
| 57.4 | 38.30 | 39.658 | 39.230 | +1.98 | 9 |
| 58.8 | 38.50 | 40.750 | 40.992 | +0.70 | 24 |
| 60.0 | 40.00 | 42.296 | 41.817 | +0.43 | 31 |
| 62.0 | 44.90 | 45.729 | 46.886 | +2.06 | 6 |

---

## Alternatives Considered

### Published discharge through the section rating (the raw M3 idiom)
Pros: byte-level reuse of the d4PDF pathway. Cons: reproduces the ~1.1 m
peak-stage over-prediction measured at the gauge, overstating the observed
loading; overstated survival loading biases the posterior unsafe. Rejected
as the default; recoverable by passing published discharge to
`build_hydrograph_record` directly if ever needed.

### Pure stage translation without trace anchoring
Pros: single data source; no amplitude adjustment of any kind. Cons:
leaves the measured -0.5 to +1.2 m per-section peak errors in the
constraint, with the sign varying by section (over-tightening at KP 62.0,
under-informing at KP 60.0), when a direct field survey of the actual
peak AT the levee line exists. Retained as the `anchor='rating'`
sensitivity.

### Anchoring by an additive datum shift instead of amplitude rescaling
Pros: also hits the trace peak. Cons: shifts the base-flow floor and the
inter-peak troughs by the full correction, distorting the memory-model
recessions; the G1 amplitude rule pins the trough floor exactly as the
Phase 1 sweep does.

### Extending the window into September via published discharge
Pros: full final recession. Cons: mixes two inconsistent discharge
definitions at the month boundary (observed-stage-equivalent vs
published); unnecessary, because the closure diagnostic proves the lost
recession is below-toe and inert at every section.

---

## Rationale

The construction honors the strongest local observation (the surveyed
trace at the levee line) for the peak, the gauge record for the full
temporal structure, and the Phase 1 M3 machinery for every conversion, so
datum and unit handling exist in one place. The 2016 record is the
empirical constraint and is never rescaled to conditioning levels; the
trace anchoring is part of constructing the best estimate of what
actually occurred at each section, not a scaling of the event.

---

## Consequences

- One reusable loader: a 2011 (or any further) event drops in as a new
  `ObservedEventSource` pointing at its own processed extracts; if no
  trace survey exists for that event, `anchor='rating'` applies and the
  anchoring uncertainty must be discussed instead.
- The committed extracts make the ingestion testable on fresh clones;
  only record construction (rating CSVs in untracked `data/raw`) skips.
- The rating-vs-trace deltas are recorded per record in provenance
  (`anchor_minus_translated_m`) so the anchoring magnitude stays visible
  in every downstream artifact.
- The KP 62.0 anchoring delta (-1.16 m versus the rating route) is the
  construction's largest lever; the `anchor='rating'` sensitivity bounds
  its effect on the posterior if ever questioned.

---

## References

- ADR-0019 (Eq. 4.19, datum, the Obihiro anchor), ADR-0020 (band
  structure), ADR-0021 (toe elevations).
- `data/processed/2016_event/README.md` (extraction provenance and the
  September stage-sheet anomaly).
- Thesis methodology chapter, "The Historical Constraint" section.
- Mission section 6 (ingestion mandate).
