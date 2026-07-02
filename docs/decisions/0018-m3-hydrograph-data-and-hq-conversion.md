# ADR 0007: M3 Hydrograph Data, H-Q Conversion, and Loader Contract

Date: 2026-07-02
Status: Accepted
Module: M3 (hydrographs.py)

## Context

M3 ingests the d4PDF discharge ensemble provided by Uemura (Docon) via the
project Dropbox and converts it to the stage hydrographs h(t) that drive the
Phase 1 engine. This ADR records the authoritative facts about that dataset and
the conversion, established from Uemura's thesis (Eq. 4.19) and email
correspondence of July 2026, so that the loader is built once, correctly,
against a fixed specification.

## Decisions

### 1. Source data format

Discharge hydrographs are Excel (.xlsx) files, one sheet named `QT` each:
- Column 1, header `Time`: integer hours, 1 to 192 (a ~8-day event window).
- Each subsequent column: one ensemble member's discharge series Q(t) in m^3/s.
- Files are split by river and KP band, not by KP. A single discharge column
  applies across the whole band; per-KP differentiation enters only at the
  H-Q conversion step.

Column headers encode provenance and MUST be parsed and retained:
- Past experiment: `HPB_mXXX_YYYY` (member ID, calendar year). 3,000 columns.
- Future experiment: `HFB_{SST}_mXXX_YYYY`, where SST is one of
  CC, GF, HA, MI, MP, MR (six prescribed sea-surface-temperature patterns),
  15 members each. 5,400 columns.

This 50-flat-member past structure versus six-SST-pattern future structure is
preserved in per-realization metadata so provenance stays traceable
(consistent with Chapter 3).

### 2. H-Q conversion (Uemura thesis Eq. 4.19) — AUTHORITATIVE

    h_t = sqrt( Q_t / a_kp ) - b_kp

where h_t is stage, Q_t is discharge (m^3/s), and a_kp, b_kp are per-KP
coefficients from non-uniform flow computation. This is NOT a power law
h = a*Q^b; the email's one-line summary was a compression. The literal
power-law reading is wrong by ~120 orders of magnitude and must never be used.

- `-b_kp` acts as an additive datum/reference-elevation term, which is why b
  varies smoothly with bed elevation along the reach (approx -29 at KP53.8 to
  -41.7 at KP62.8 on the Tokachi).
- Q must be in m^3/s (as supplied). No unit scaling on Q.
- Guard: `Q_t / a_kp` must be non-negative before the square root. It always is
  for physical Q >= 0 and a_kp > 0, but assert it to catch bad inputs.

### 3. Datum

Stage h(t) is referenced to mean sea level (MSL), per Uemura. This is the SAME
datum as the HWL values in `BankHeight_{Tokachi,Satsunai}Riv_2019.csv`, so
converted stages are directly comparable to HWL with no reconciliation.

### 4. Anchor / ground-truth check

At Obihiro (Tokachi KP56.6): a = 140.33, b = -32.49, HWL = 38.14 m MSL.
Chapter 3 states the 2016 record peak came 0.19 m below design HWL (~37.95 m).
Eq. 4.19 reproduces this: a peak discharge of ~4,180 m^3/s gives h = 37.95 m
MSL, and realistic flood peaks of 3,000-7,500 m^3/s give 37.1-39.8 m MSL.
This is the validation anchor for the conversion.

### 5. Rating coefficient files

`HQrelation_TokachiRiv_2017.csv` and `HQrelation_SatsunaiRiv_2017.csv`:
- Shift-JIS encoded (NOT UTF-8; loader must specify encoding explicitly).
- Header cells `HQ_a`, `HQ_b` contain full-width characters.
- Columns: River, KP, a, b. Coefficients at 0.2 km spacing.
- Coverage: full study reach and beyond. Tokachi runs to KP62.8+, Satsunai to
  KP48. So rating coefficients EXIST for every study node, including the upper
  Tokachi nodes KP62.0-62.8.

### 6. Temporal resolution

Native resolution is 1 hour and this is final; Uemura confirmed no finer
timestep data exists. Therefore:
- native_dt = 3600 s, derived from the Time column, not hardcoded.
- Time array is converted to SECONDS internally (SI convention). A common bug
  is leaving it in hours; assert seconds.
- The timestep-convergence validation (Failure Mode 3) can only sub-sample the
  hourly forcing by interpolation, not request finer source data.

### 7. Discharge coverage gap: upper Tokachi KP62.0-62.8

Discharge hydrograph files stop at KP61.80, but rating coefficients extend to
KP62.8. Decision: for the five upper nodes (KP62.0, 62.2, 62.4, 62.6, 62.8),
proxy the discharge series from KP61.8 and apply each node's OWN local a_kp,
b_kp. Rationale: no major tributary enters between KP61.8 and 62.8, so Q varies
only gradually, whereas the rating is intensely local and must stay per-node.
KP62.0 is the narrow-foreshore (44 m) worst-case confined section, so this
proxy is flagged explicitly in the thesis text and is provider-confirmed
(Uemura: Dropbox contains the complete export). Mark proxied records in
metadata (e.g. `discharge_proxied_from = "KP61.8"`).

### 8. Crest capping (from Eq. 4.19 thesis passage)

Uemura's failure model replaces stage with levee crest height when stage
exceeds the crest, because only erosion breaching is evaluated and overtopping
interaction is excluded. For THIS study: the BEP engine consumes the full
uncapped stage as its hydraulic boundary condition; capping is a property of
the overflow/surface mechanism imported from Uemura, not of the seepage
loading. Do NOT cap stage inside M3. Record this as a deliberate difference so
it is not mistaken for an omission.

### 9. Scenario tags

Two scenario tags flow to FragilityResult metadata and drive the climate
comparison: `historical` (HPB) and `+4K` (HFB). Both must be produced and
tested.

## HydrographRecord contract (per architecture spec)

Each record carries: time array (seconds), stage array h(t) (m MSL), peak,
duration, scenario tag, native_dt, and provenance (SST pattern where
applicable, member ID, year, KP, discharge_proxied_from where applicable).

## Consequences

- The conversion is fixed and validated; M3 tests assert the Obihiro anchor.
- The file-reading seam is kept thin and separable from the pure conversion and
  record-construction logic so the physics-adjacent parts are testable without
  the large Excel files.
- The 2016 observed hydrograph loads through the same HydrographRecord
  interface (required by Phase 2 replay).
