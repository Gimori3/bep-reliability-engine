# ADR-0023: Shape-Invariant Climate Axis — One Canonical Shape Drives Both Scenarios; Event-Derived Workbook Selection Supersedes the ADR-0020 §3 Wording

Date: 2026-07-03
Status: Accepted (design and config disposition approved by the author, 2026-07-03)

## Context

The 2026-07-03 health assessment (finding 3) surfaced that the climate axis of
the 16-config sweep is inert as built: the historical and +4K configs differ
only in the `scenario` metadata tag, both pin the same HPB canonical events
(`HPB_m064_1987`, `HPB_m067_1978`), and the fragility results are therefore
bit-identical. Two written commitments sat in tension with this:

- **ADR-0020 §3** says "the orchestrator selects the workbook experiment from
  `config.scenario`". As built, `load_canonical_shape` selects the band
  workbook from the **canonical event's own experiment**, parsed from its
  header (`hydrographs.py`; the design rationale lived only in docstrings).
- **Spec §1 (M5)** warns the omitted flood-fighting clause's conservatism
  "grows under the elongated +4K hydrographs" — implying +4K events are
  longer, a shape effect the transient limit state is genuinely sensitive to
  and which a shared HPB shape could not express.

Whether +4K shapes actually differ was an empirical question. It was answered
on 2026-07-03 by a full-ensemble comparison at KP 57.4 (all 3,000 HPB and all
5,400 HFB members of the Tokachi KP056.20–061.80 band — the band feeding all
four study sections), each member converted to stage under the local rating
and normalized exactly as the G1 conditioning-level rule normalizes the
canonical shape. Peaks counted by `scipy.signal.find_peaks` (height 0.3,
prominence 0.2 on the 0–1 shape); durations in hours at/above shape fractions.

| | t50 (med [IQR]) | t90 (med) | peaks (med / mean) | compound (≥2 peaks) | inter-peak trough (med) |
|---|---|---|---|---|---|
| HPB (historical) | 40 h [32–54] | 10 h | 1 / 1.10 | 9.6% | 0.435 |
| HFB (+4K) | 35 h [27–49] | 8 h | 1 / 1.10 | 10.1% | 0.407 |

**+4K shapes are not longer and not more compound** — at the normalized-shape
level they are marginally *shorter*, with an identical compound fraction and
trough depth. Where the climate signal actually lives is **peak intensity**:
at the KP 62.0 rating the HFB peak stages run max 51.47 / p99 48.75 m MSL
against HPB's 48.78 / 46.94 (≈ +1.8 m at the 99th percentile).

Incidentally verified: the production canonical shape `HPB_m064_1987`
(t50 = 55 h, 2 significant peaks, trough 0.498) sits in the ensemble's upper
duration quartile — a conservative choice for exercising the spec §5
compound-event memory model.

## Decision

1. **The shape-invariant climate axis is adopted.** The conditioning-level
   fragility P(fail | h_i) is driven by one config-pinned canonical event
   shape (ADR-0020 Decision 1) for **all** climate scenarios. Climate enters
   the analysis exclusively through the loading (peak-stage) distribution
   downstream — the Phase 3 fragility × hazard composition — not through the
   fragility shape. The diagnostic above is the empirical basis: the
   experiments differ in peak intensity, not in normalized shape structure.

2. **ADR-0020 §3's wording is superseded to match the code.** Band-workbook
   selection for the canonical shape is by the **event's own experiment**
   (parsed from the `HPB_`/`HFB_` header of `canonical_event_ids[0]`), not by
   `config.scenario`. The scenario → experiment map
   (`hydrographs.experiment_for_scenario`, ADR-0019 §9) remains the single
   source of that mapping for any consumer that does select by scenario
   (e.g. future full-ensemble loading for the hazard work); it is simply not
   the selector for the canonical fragility shape. ADR-0020 is otherwise
   unchanged; its text is not edited (a one-line status cross-reference may
   be added upon author approval).

3. **The spec §1 (M5) elongation concern is discharged for this data drop:**
   the +4K elongation it anticipates is not present in the Tokachi band at
   the normalized-shape level, so no shape-driven conservatism differential
   between scenarios is being missed by the shared shape.

## Consequences

- **The +4K fragility equals the historical fragility, and this identity is
  a result, not an omission.** It follows from the shape-invariance finding:
  the fragility P(fail | h_i) conditions on the peak stage, the normalized
  shape statistics of the two experiments are indistinguishable (table
  above), and the shape is config-pinned — so recomputing the curves under
  the +4K tag would reproduce the historical numbers bit-for-bit. There is
  exactly one fragility result per (section, d70 interpretation), and no +4K
  run may be presented as independent evidence.
- **Scenario differentiation moves to the Phase 3 hazard side, with the
  schema field retained.** The climate signal lives in the peak-stage
  (loading) distribution — HFB runs ≈ +1.8 m above HPB at the 99th
  percentile at the KP 62.0 rating — and enters the risk chain through the
  fragility × hazard composition, not through the fragility curve. The
  `scenario` config field and the `'+4K'` literal remain in the Config
  schema: `scenario` stays the run identity (the 2016 replay is
  `historical`) and the literal remains available to any future
  scenario-differentiated work (e.g. hazard-side ensemble loading).
- **Config disposition (approved 2026-07-03): the 8 `*_plus4k_*` configs are
  dropped.** `scripts/generate_configs.py` emits the historical scenario
  only (16 → 8 configs), because (i) the +4K runs were bit-identical
  recomputations whose separate artifacts invite misreading as independent
  results and create a provenance trap (two files differing only in one
  metadata tag); (ii) the Phase 3 climate comparison needs one fragility
  file per section paired with per-scenario hazard, so scenario bookkeeping
  belongs to the hazard side, where HFB actually differs. The drift guard
  (`tests/test_configs.py`) pins the historical-only sweep and rejects a
  reappearing `*_plus4k_*` file as a regression.
- **Validity scope:** the diagnostic covers the Tokachi KP056.20–061.80 band
  (all four study sections, including the KP 61.8-proxied KP 62.0). If a
  study node on another band or river is ever added, re-run the shape
  comparison before extending this ADR to it.

## References

- ADR-0019 §9 (scenario tags; HPB/HFB), ADR-0020 §1 (canonical event pinning)
  and §3 (the superseded wording), ADR-0010 (`peak` authoritative).
- 2026-07-03 health assessment, finding 3, and the same-day shape diagnostic
  (full-ensemble metrics quoted above).
- `bep_reliability_engine/hydrographs.py` (`load_canonical_shape`,
  `experiment_for_scenario`, `conditioning_record_for_level`).
- Spec §1 (M5 flood-fighting conservatism note), §12/§13 (scenario axis).
