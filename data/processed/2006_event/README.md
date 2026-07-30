# 2006 event drop -- nothing constructible, closed by ADR-0044

This directory looks empty because it very nearly is. The agency drop mirrors
the 2016 archive's folder structure, but the gauge stage/discharge directory
(`観測所水位・流量データ/`) and the trace-survey directory (`洪水痕跡水位/`) both
arrived EMPTY, so no observed stage time series and no surveyed flood trace
exist for 2006. Only `観測所雨量データ/rain.xlsx` (hourly rainfall, context
only) carries data. All subdirectories are gitignored; this README is the only
tracked file here.

Without a stage record the Phase 2 transient Accept-Reject replay cannot run,
and rainfall alone cannot construct one. **ADR-0044 (2026-07-18) closed the
survival-evidence set at the 2016 event**, setting 2006 aside for lack of any
constructible observation (2011 was closed separately, on a measured
sustained-peak bound). See:

- `docs/decisions/0044-event-set-closure-2016-only.md` -- the decision;
- `docs/decisions/adr0044-event-closure-bound.json` -- the evidence;
- `data/processed/2011_event/README.md` -- the sibling drop, which documents
  both events' closure in full.

If the stage workbooks that belong in the empty directories ever surface, the
event drops in as a new `ObservedEventSource` with zero framework changes; the
sequential machinery stays built and tested.
