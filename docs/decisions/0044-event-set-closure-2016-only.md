# ADR-0044: Survival Evidence Set Closed at the 2016 Event; 2011 and 2006 Assessed and Set Aside

> **Re-based under ADR-0054, 2026-09-25.** The evidence this note reads was regenerated on the re-based
> matrix d70 (0.70 / 0.53 / 0.26 / 0.70 mm became 0.90 / 0.65 / 0.74 /
> 0.75 mm at KP 57.4 / 58.8 / 60.0 / 62.0; bulk unchanged). The committed
> JSON is the re-based record. Where the prose below quotes a matrix-reading
> number it is the pre-rebase value, kept as written; the re-based values are
> in the JSON, tabulated in `bimodal-foundation-d70-study.md` Part 3 and in
> the dated addenda of `docs/phase2_report.md` and `docs/phase3_report.md`.

Date: 2026-07-18

## Status
Accepted (author decision of 2026-07-18, recorded with the evidence
that grounded it)

---

## Context

The Phase 2 report (section 10, "the 2011 flag") kept open whether the
September 2011 and 2006 floods should join the 2016 event as sequential
survival constraints, and listed the data that would be needed. On
2026-07-18 the corresponding agency drops arrived
(`data/processed/2011_event/`, `data/processed/2006_event/`). Exhaustive
inventory found:

- Both drops mirror the 2016 archive's folder structure, but the gauge
  stage/discharge directories (`観測所水位・流量データ/`) are EMPTY in
  both (directory timestamps October 2019: empty at the source or lost
  before delivery). Without an observed stage series the transient
  Accept-Reject replay cannot be constructed for either event, and the
  the author reports the missing workbooks are not easily obtainable.
- The 2011 drop DOES carry the complete H23.9 post-flood trace survey
  (six rivers, 0.2 km spacing, m MSL); the 2006 drop carries hourly
  rainfall only (no trace, no stage; every column of its `rain.xlsx` is a
  rain gauge, including the ones named after towns with stage gauges).
- The surveyed 2011 right-bank peaks at the study sections are KP 57.4 =
  37.329, KP 58.8 = 39.229, KP 60.0 = 41.403, KP 62.0 = 43.735 m MSL:
  BELOW the landside toe at KP 57.4 (-0.97 m) and KP 62.0 (-1.17 m), and
  0.73 m / 1.40 m above it at KP 58.8 / KP 60.0. The 2016 peaks exceed
  the 2011 peaks by 1.4 to 2.0 m at every section.

## Decision

1. **The Phase 2 posterior conditions on the 2016 event alone.** The 2011
   and 2006 events are closed as survival constraints: 2011 on the
   measured bound below, 2006 for lack of any constructible observation.
2. **The closure is evidence-based, not data-availability-based.** The
   sustained-peak upper bound (`scripts/assess_2011_2006_closure.py`,
   evidence file `docs/decisions/adr0044-event-closure-bound.json`) holds
   the surveyed 2011 trace peak constant for 64 days (the ADR-0040
   convention at which the forward-Euler trajectory provably reaches the
   analytic sustained-peak limit) and replays it through the frozen M8
   evaluator via the Phase 2 pipeline at the production N = 1e5, per
   stratum. Because the real 2011 event was weaker than this hold at
   every instant, the result bounds the rejection of ANY faithful 2011
   time series from above:

   | Stratum | 2011 trace vs toe | Bound rejection | Beyond the 2016 rejection |
   |---|---|---|---|
   | KP 57.4 matrix and bulk | -0.97 m | 0 / 100000 | 0 |
   | KP 58.8 matrix and bulk | +0.73 m | 0 / 100000 | 0 |
   | KP 60.0 matrix | +1.40 m | 908 (0.908%) | 316 (0.316%) [**superseded 2026-09-20: 326 (0.326%)**] |
   | KP 60.0 bulk | +1.40 m | 0 / 100000 | 0 |
   | KP 62.0 matrix and bulk | -1.17 m | 0 / 100000 | 0 |

   Seven of eight strata bound at exactly zero, including KP 58.8, the
   basin's governing segment: even an infinite hold at the surveyed 2011
   peak clears no realization's transient limit state there. The single
   nonzero stratum bounds the marginal information any 2011 hydrograph
   could add beyond 2016 at 0.316 percent of the prior [**superseded
   2026-09-20: 0.326 percent**], under a hold
   incomparably more erosive than any real flood (the real 2016 event
   held its own peak region for roughly a day, not 64; the measured
   canonical-versus-real shape factor of 3 to 4 from the Phase 2 report
   section 6.3 indicates the true marginal would be a small fraction of
   the bound).
3. **The usable 2011 observation is preserved**: the trace survey is
   extracted to the committed
   `data/processed/2011_event/flood_trace_2011.csv`
   (`scripts/extract_2011_event.py`; Tokachi and Satsunai, with crest and
   bed elevations), and the raw drops are gitignored below the folder
   roots, mirroring the 2016 raw-drop policy.
4. **The sequential machinery stays built, tested and documented.** If
   the stage workbooks that belong in the empty directories ever
   surface, either event drops in as one `ObservedEventSource` with zero
   framework changes (for 2011 even the trace anchor is already in
   place); this ADR then simply gets a successor recording the reopening.

---

## Alternatives Considered

### Invest significant effort to obtain the stage records from research partners
Pros: would allow the full transient replay for 2011 (and possibly
2006), completing the thesis's original supplementary-updating sentence
literally. Cons: the bound proves the obtainable information is at most
0.32 percent of the prior at one stratum and exactly zero at seven,
before shape realism shrinks it further; the effort would purchase a
result already known to be immaterial. Rejected by the author on
this evidence.

### Construct a 2011 hydrograph from an assumed shape under the trace peak
Pros: cheap; would let the sequential pipeline run. Cons: manufactures
exactly the information the event is supposed to supply; the Phase 2
report section 6.3 measured a factor 3 to 4 sensitivity to the shape
assumption at fixed peak, larger than the entire effect being estimated.
Rejected.

### Use the 2011 trace peak as a peak-based (WBI+-style) constraint
Pros: needs no time series. Cons: the peak-based reading over-rejects
(measured 3.2 to 4.0 times at the 2016 event), which for survival
updating is anti-conservative; it also contradicts the thesis's central
methodological commitment to the time-resolved constraint. Rejected.
(The sustained-peak BOUND used here is the opposite construction: it is
deliberately an over-rejection and is used only to prove immateriality,
never as a posterior.)

---

## Rationale

A survival constraint informs the posterior only where its survival
region cuts rows the existing evidence accepts. The 2016 event loaded
every section harder than 2011 at the peak by 1.4 to 2.0 m, and the
sustained-peak bound closes the one remaining channel (duration) by
showing that even infinite duration at the 2011 level rejects nothing at
seven strata and at most 0.32 percent beyond 2016 at the eighth. Closing
the event set on a measured bound converts the missing data from a
limitation into a demonstrated-immaterial factor, which is the stronger
scientific position.

---

## Consequences

- The thesis methodology text no longer promises the 2011 sequential
  step; the paragraph now records the assessment and its bound
  (`_thesis_methodology.tex`), and the Phase 2 report carries the closure
  as section 12.
- The committed trace extract doubles as independent evidence in the
  thesis narrative (the 2011 flood stayed at or below the toe at half the
  study sections).
- No Phase 2 code changes: the assessment ran entirely through the
  existing public pipeline (`load_phase1_run`, `replay_event`,
  `apply_survival_filter`), which is itself a demonstration that a future
  event integrates without refactoring.
- The 2006 event is closed without a bound (nothing constructible); any
  future 2006 claim would need its stage record first.

---

## References

- ADR-0035 (2016 ingestion), ADR-0036 (updating architecture), ADR-0040
  (the sustained-peak convention and its ODE-exactness evidence).
- `docs/decisions/adr0044-event-closure-bound.json` (the measured bound).
- `docs/phase2_report.md` sections 10 to 12; `data/processed/2011_event/
  README.md` (drop inventory and extract provenance).
- Schweckendiek (2014) section 4.2.3 (inequality evidence; the
  intersection form for multiple observations).

---

## Correction, 2026-09-20: the marginal is 0.326 per cent at the corrected gauge

The two figures marked **superseded** above were computed at the KP 56.6 Obihiro
node. ADR-0035's 2026-09-14 amendment moved the node to KP 56.73 and
`scripts/assess_2011_2006_closure.py` was re-run, regenerating
`adr0044-event-closure-bound.json` in engine commit `adfc848`. That artifact now
holds, at KP 60.0 matrix, `bound_reject_count = 908`,
`marginal_beyond_2016_count = 326` and `marginal_beyond_2016_fraction = 0.00326`
against `reject_2016_count = 3244`, the corrected 2016 transient rejection.

**Nothing about the decision changes.** The bound is still exactly zero at seven
of eight strata including KP 58.8, the total bound at KP 60.0 matrix is still
0.908 per cent, and the event set is still closed at 2016 on the same argument:
the marginal a 2011 hydrograph could add beyond 2016 is bounded, by a hold
incomparably more erosive than any real flood, at a third of a per cent of the
prior in one stratum and at zero everywhere else. Only the third decimal of that
one figure moved, with the transient rejection it is measured against.

The thesis already prints 0.326 at all six of its sites: the Summary,
Chapter 4, Chapter 6, Chapter 8 and Chapter 9 twice. `docs/phase2_report.md`
section 12 carried the same stale 0.316 and now carries a matching dated
correction.
