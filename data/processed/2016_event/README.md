# Processed 2016 typhoon event observations

Compact, committed extracts from the raw agency data drop
`data/digitized/2016_event_data/` (188 MB, gitignored), produced by
`scripts/extract_2016_event.py`. These files are the input surface of the
Phase 2 observed-event loader (`bayesian_reliability_updating.events`).
Re-run the script after any change to the raw drop; do not hand-edit.

## Files

| File | Content |
|---|---|
| `stage_hourly_{river}_201608.csv` | Hourly observed river stage [m MSL], August 2016 (744 samples, 2016-08-01T01:00 to 2016-09-01T00:00 JST), one ASCII station column per gauge |
| `discharge_hourly_{river}_201608.csv` | Hourly published discharge [m^3/s], August 2016, same stations |
| `discharge_hourly_{river}_201609.csv` | Hourly published discharge [m^3/s], September 2016 (recession; sparse after 2016-09-06) |
| `flood_trace_2016.csv` | Post-flood trace survey (September 2016): per-KP left/right levee trace elevations [m MSL] and design HWL, 0.2 km spacing |

Rivers extracted: Tokachi (十勝川) and Satsunai (札内川), the two study
rivers. Station column names are romanized ASCII; the Japanese originals and
the mapping live in `scripts/extract_2016_event.py` (`STATION_ASCII`).

## Sources within the raw drop

- `36_2016.8.20-8.31/観測所水位・流量データ/H_Q_2016.8.20-8.31.xlsx`
  (hourly gauge stage and discharge, 30 stations).
- `36_2016.8.20-8.31/洪水痕跡水位/H28_kon.xlsx` (洪水痕跡標高一覧表, the
  flood-trace elevation survey of September 2016).

## Datum evidence (m MSL)

The stage series and trace elevations share the m MSL datum of the Phase 1
engine (ADR-0019 section 3, ADR-0021). Evidence:

1. At the Obihiro gauge (帯広, Tokachi KP 56.6) the pre-event base stage is
   32.74 m; the Eq. 4.19 rating datum term at KP 56.6 is `-b_kp = 32.49 m`
   (`data/raw/rating_curves/HQrelation_TokachiRiv_2017.csv`), i.e. the
   low-flow stage sits a few decimetres above the rating datum, exactly as
   an MSL-referenced series must.
2. The observed August peak at Obihiro is 38.07 m (2016-08-31T04:00)
   against the 38.14 m MSL design HWL of ADR-0019 section 4 ("the 2016
   record peak came ~0.2 m below design HWL").
3. The trace table's design HWL column reproduces the ADR-0018 bank-height
   HWL values in the generated configs (e.g. 41.03 m at Tokachi KP 58.8).

## Known source anomalies

- The workbook sheet `時刻水位201609` (September stage) is a corrupted
  duplicate of the September discharge sheet (header row and values are
  discharge). September stage is therefore not extractable. This does not
  affect Phase 2: the erosive part of the event ends inside the August
  window (the recession is below every study section's landside toe well
  before 2016-09-01T00:00; the loader records the end-of-window margin).
- The 熊牛 (Kumaushi) stage column carries the sentinel 閉局 (station
  closed) throughout; sentinels become empty cells in the CSVs.
