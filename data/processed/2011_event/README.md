# 2011 event drop and the committed trace extract

The raw September 2011 (H23.9) agency drop was received 2026-07-18. Its
subdirectories are gitignored (only this README and the committed extract
below are tracked); the sibling `data/processed/2006_event/` drop is
gitignored entirely.

## Committed extract

`flood_trace_2011.csv` (produced by `scripts/extract_2011_event.py`, which
needs `xlrd` for the .xls sources): the H23.9 post-flood trace survey
(洪水痕跡縦断図データ) for the two study rivers at 0.2 km spacing. Columns:
per-KP left/right trace elevations, current levee crest heights, and
deepest/mean bed elevations, all m MSL. Non-surveyed cells are empty.

## Why the 2011 and 2006 events are NOT survival constraints (ADR-0044)

Both drops mirror the 2016 archive's folder structure, but the gauge
stage/discharge directories (`観測所水位・流量データ/`) are EMPTY in both,
and the 2006 trace directory is empty too. Without an observed stage time
series the Phase 2 transient Accept-Reject replay cannot run, and the
2026-07-18 assessment (ADR-0044) closed both events on evidence:

- The surveyed 2011 right-bank peaks at the study sections (KP 57.4 =
  37.329, KP 58.8 = 39.229, KP 60.0 = 41.403, KP 62.0 = 43.735 m MSL) sit
  BELOW the landside toe at KP 57.4 and KP 62.0 (constraint vacuous by
  construction) and only 0.73 m / 1.40 m above it at KP 58.8 / KP 60.0.
- The ADR-0044 sustained-peak bound (the most erosive hydrograph any 2011
  time series could be, held at the surveyed peak for 64 days, replayed
  through M8 at production N = 1e5) shows the maximal possible 2011
  rejection is negligible and nested inside the 2016 rejection set; see
  `docs/decisions/adr0044-event-closure-bound.json`.
- The 2006 drop carries no stage record and no trace survey, and the
  event was smaller than 2016 (the modern record for the basin); nothing
  usable can be constructed from rainfall alone.

The Phase 2 posterior therefore conditions on the 2016 event alone. The
sequential machinery stays built and tested; if the stage workbooks that
belong in the empty directories ever surface, either event drops in as a
new `ObservedEventSource` with zero framework changes.

## Remaining raw contents (gitignored)

- `洪水痕跡水位/02_{river}_kon_201109.xls`: the six-river trace survey
  (source of the extract; Otofuke, Shihoro, Tobetsu and Sarubetsu are not
  extracted, as no production BEP section lies on them).
- `観測所雨量データ/rain.xlsx`: hourly rainfall, 189 stations, September
  2011 (context only; every column is a rain gauge, including the ones
  named after towns with stage gauges).
- `観測所水位・流量データ/`, `ダム操作記録/`, `レーダ雨量データ/`: empty
  in the received drop (directory timestamps October 2019, i.e. already
  empty at the source or lost before delivery).
