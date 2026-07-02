# ADR 0020: Hydrograph-Source Config Block and KP -> Band-File Resolution

Date: 2026-07-02 (Accepted 2026-07-03)
Status: Accepted
Module: M1 (config.py), M3 (hydrographs.py), orchestrator (run.py)

## Context

M3 is built (ADR-0019) but unreachable from a `Config`: the model has no
fields for where the d4PDF data lives, which river/KP a cross-section is on
(the KP is only embedded in the `cross_section_id` string), which rating CSV
applies, or how a scenario tag selects an experiment. The d4PDF workbooks are
split by river and KP band with the band range enumerated in the filename
(e.g. `Hydro Data, HPB, Tokachi Riv. KP056.20-KP061.80.xlsx`), so a study
node's KP must be routed to the correct band file — including the ADR-0019 §7
proxy routing for KP 62.0-62.8, whose discharge source is KP 61.8.

Per the audit decision on gap G1, Phase 1 fragility stays
conditioning-level-driven: the orchestrator scales a canonical real d4PDF
event shape to each level h_i. The config must therefore also pin *which*
event(s) supply the canonical shape, deterministically (the parallel == serial
guarantee of `run.py` requires event selection to be a pure function of the
config).

## Decisions

### 1. New optional `Config.hydrograph_source` block (M1)

A pydantic sub-model with fields:

- `data_root` (str, directory): root of the raw data drop; the loader expects
  `{data_root}/hydrographs/` (workbooks) and `{data_root}/rating_curves/`
  (rating CSVs) beneath it. Default `data/raw`.
- `river` (str, `'Tokachi'` | `'Satsunai'`): explicit, not parsed out of
  `cross_section_id` (string parsing of IDs is banned as fragile).
- `kp` (float): the study node's KP. Explicit for the same reason.
- `canonical_event_ids` (list[str], non-empty, **ordered**): the verbatim
  d4PDF member headers whose shapes drive the conditioning-level scaling (per
  the approved G1 baseline rule, this field explicitly pins the chosen events,
  ensuring the baseline and configuration are recorded in the same place
  rather than managed separately). The **first** entry is the shape the run
  uses; subsequent entries are approved alternates recorded for provenance
  (a shape-sensitivity run is a config whose list is reordered — selection
  stays config-side so one config still fully determines one result). The G1
  scaling rule is: stage-domain normalization of the event under the
  section's local rating, rescaled as `h(t) = h_base + (h_i - h_base) *
  shape(t)` with the trough baseline pinned at the section's **base-flow MSL
  stage h_base** (Eq. 4.19 at Q = 75.44 m^3/s under the local rating) — NOT
  at the landside toe z_toe (ADR-0021 Downstream-use item 4) — and
  `peak = h_i` exactly (the authoritative conditioning anchor, ADR-0010).

The block is **optional** (`None` default): a config without it can only run
the synthetic-stub path, and the orchestrator must refuse the real-hydrograph
path without it. This keeps every existing config valid.

### 2. Rating-file naming convention

`{data_root}/rating_curves/HQrelation_{river}Riv_2017.csv`, i.e. derived from
`river`, not configured per file. One convention, one place.

### 3. Scenario -> experiment mapping

`historical` -> `HPB`, `+4K` -> `HFB` (ADR-0019 §9), fixed in M3 as the single
source of that mapping. The orchestrator selects the workbook experiment from
`config.scenario`; no config field duplicates it.

### 4. KP -> band-file resolution (M3)

A resolver function in `hydrographs.py`:

1. Apply `resolve_discharge_source_kp(kp)` first, so KP 62.0-62.8 route to
   the KP 61.8 band (ADR-0019 §7) while keeping their own rating KP.
2. Scan `{data_root}/hydrographs/` for filenames matching
   `Hydro Data, (HPB|HFB), (Tokachi|Satsunai) Riv. KP{lo}-KP{hi}.xlsx`
   (KP fields `\d{3}\.\d{2}`), parsed — not hardcoded — so a future data drop
   with new bands needs no code change.
3. Select the unique file whose river and experiment match and whose
   `[lo, hi]` contains the (proxied) source KP. Zero or multiple matches
   raise `ValueError` loudly (no silent nearest-band fallback).

### 5. Determinism

File resolution and event selection are pure functions of the config: the
directory scan is sorted, the matched file is unique, and the canonical event
IDs are explicit config values. No RNG, no filesystem-order dependence. This
preserves the `run.py` reproducibility-by-construction guarantee (its module
docstring's "M3-stub determinism constraint").

## Alternatives considered

- **Explicit workbook path per config.** Rejected: every config would carry
  two paths (HPB + HFB) that must agree with `scenario`, duplicating the
  mapping 16 times and breaking on a re-organized data drop.
- **Hardcoded band table in M3.** Rejected: the bands are provider-defined
  and may be extended (Uemura: the Dropbox export is complete *today*); a
  table would need a code edit per data drop, while the filename already
  encodes the range.
- **Deriving river/KP from `cross_section_id`.** Rejected: ID strings are
  labels, not data; parsing `"tokachi_kp62.0"` couples the physics path to a
  naming convention that nothing validates.

## Consequences

- `scripts/generate_configs.py` emits the block per section (river and KP come
  from the geotech CSV rows); `tests/test_configs.py` grows the drift guard.
- The G1 orchestrator seam (`_hydrograph_for_level`'s replacement) reads the
  canonical shapes through this block once per run, in the main process.
- The datum guard `validate_datum_consistency` (audit gap G2) is called at
  that same seam before any real record reaches M8, so an unresolved
  provisional `z_toe = 0.0` fails loudly rather than producing ~35 m heads.
- The conditioning grid is redefined onto the MSL datum as part of this coupled work.
- Per ADR-0021, the landside-toe elevations serve as **both** the
  head-translation datum `z_toe` and the exit reference `h_e` (ADR-0007
  `z_toe == h_e`; one `geometry.z_toe` value, one code path), and the
  canonical-shape trough baseline is the base-flow stage `h_base`, **not**
  `z_toe` (ADR-0021 Downstream-use item 4; the G1 rule recorded in Decision 1
  above).
- `FragilityResult.metadata` gains the resolved source facts (workbook file,
  rating file, canonical event IDs and their member provenance) — audit gap
  G5.

## References

- ADR-0019 (M3 data facts, §1 band split, §7 proxy, §9 scenario tags).
- ADR-0018 (HWL / MSL datum; provisional z_toe — retired by ADR-0021).
- ADR-0021 (landside-toe elevations, MSL: the values serving as both `z_toe`
  and `h_e`; its Downstream-use item 4 fixes `h_base` — not `z_toe` — as the
  canonical-shape trough baseline).
- ADR-0007 (`z_toe == h_e` datum identity), ADR-0010 (`peak` authoritative).
- Audit gaps G1, G3, G4, G5 (2026-07-02 M3 integration audit).
- `run.py` module docstring (reproducibility by construction).
