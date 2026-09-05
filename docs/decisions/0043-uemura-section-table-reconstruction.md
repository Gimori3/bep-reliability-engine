# ADR-0043: Reconstruction of Uemura's Section-Aggregation Table from His Committed Geometry

Date: 2026-07-17

## Status
Accepted (reversible: the table is one committed CSV consumed through the
existing `load_section_table` seam; an author-supplied table replaces it
verbatim)

---

## Context

Class-D blocker D2 (`docs/close_out_2026-07-12.md`): Uemura aggregates the
0.2 km segments into 9 consequence sections (Tokachi x5, Satsunai x4, named
by the representative breach segment: KP56.4/58.0/59.6/61.4/62.4 and
KP4.2/5.2/6.4/7.0) with **full dependence within a section** (section
fragility = max over member segments, his Eq. 14) and ordered partial
dependence between sections. The membership itself was never published as a
table; his notebook assigns each surveyed node to the nearest same-river
section polyline (500 m cutoff) from a `SECTIONS.shp` layer.

What is on disk:

* `data/raw/gis/SECTIONS.shp` — **the very shapefile his notebook used**
  (9 named polylines, JGD2000 Plane CS XIII, secured in the local
  `data/raw` drop on 2026-07-02; `data/raw` is gitignored by repo
  convention, the reconstructed table is the committed product).
* Ten of his own node->section assignments, embedded in a notebook output
  (Satsunai KP 3.4–4.0 -> KP4.2; Tokachi KP 62.0–62.8 -> KP62.4).
* The WP2 report: sections consist of ~5–10 (elsewhere 8–15) consecutive
  segments; coverage focuses on the Obihiro-facing reaches.

The levee-node coordinate layer his notebook used is *not* in the drop, so
the literal 500 m nearest-polyline rule cannot be replayed for all 114
nodes. But the polyline geometry itself pins the KP spans:

* The four Satsunai polylines form one contiguous chain starting at the
  KP 3.2 node (39 m offset): cumulative arc lengths place the section
  boundaries at KP ~4.69, ~5.97, ~6.50, ~6.96.
* The Tokachi polyline lengths (KP62.4: 0.84 km; KP61.4 and KP59.6:
  double-traced pairs of ~1.5 km; KP58.0: 1.56 km; KP56.4: the remaining
  downstream sprawl) match a midpoint-boundary tiling of the reach between
  the representative KPs to within one 0.2 km grid step at every boundary.
* His ten known assignments are all reproduced by those spans.

---

## Decision

1. **Commit a reconstructed KP-range table**
   (`data/processed/uemura_segments/section_table.csv`, the ADR-0038 D2
   contract format) built by `scripts/build_section_table.py`:
   * Satsunai (chain-derived boundaries, snapped to the 0.2 km grid):
     KP4.2 = [3.2, 4.6], KP5.2 = [4.8, 5.8], KP6.4 = [6.0, 6.4],
     KP7.0 = [6.6, 7.0]. Satsunai KP 7.2–16.6 stays **unsectioned** (his
     scheme defines no consequence sections there — an honest gap, not an
     omission).
   * Tokachi (midpoint boundaries between representative KPs, validated
     against the polyline lengths): KP56.4 = [53.8, 57.2],
     KP58.0 = [57.4, 58.8], KP59.6 = [59.0, 60.4], KP61.4 = [60.6, 61.8],
     KP62.4 = [62.0, 62.8].
   The build script parses `SECTIONS.shp` itself and **fails** if any
   reconstructed span disagrees with its polyline length by more than
   0.3 km, or if any of the ten known assignments is violated — the
   validation is executable, not narrative.
2. **`load_section_table` gains an explicit `allow_gaps` mode** (default
   False, preserving the strict tiling check): segments outside every range
   in a touched reach keep `section_id=None` instead of raising. The
   Satsunai table legitimately covers only KP 3.2–7.0.
3. **Section-level composition follows Uemura's own rule, aligned by
   discharge**: his Eq. 14 max is conditional on the discharge q, and the
   member curves live on their own nodes' stage datums (the water surface
   falls metres across a multi-kilometre section), so the max is taken by
   inverting the representative node's Eq. 4.19 rating exactly
   (`q = a(h+b)^2`), mapping q to each member's own local stage, and
   evaluating the member curves there
   (`composition.max_within_section_rated`; execution amendment — a naive
   absolute-stage max was measured to overstate the KP56.4 section
   probability by ~50x by evaluating downstream low-crest curves at
   upstream stages). His between-section ordered scenario correction
   (upstream-failure discounting) is *not* reproduced — it serves his
   basin-total flood probability, not the thesis's per-section RQ3/RQ4
   questions; noted as out of scope.
4. **Naming**: section IDs keep his KP names (`KP56.4` … `KP7.0`). The
   thesis's "Tokachi Sections 1–5 / Satsunai 1–4" map to these in
   upstream-to-downstream order (Tokachi 1 = KP62.4 … 5 = KP56.4;
   Satsunai 1 = KP7.0 … 4 = KP4.2), the order of his own composition lists.

---

## Alternatives Considered

### Alternative 1: full geometric replay (reconstruct all 114 node coordinates via river-chainage from the Riverline layer, then nearest-polyline @ 500 m)
Pros: replays his rule literally.
Cons: requires reprojecting the geographic Riverline layer and
re-deriving KP chainage with no committed KP-zero anchor; the section
polylines' own lengths already pin the boundaries to one grid step, so the
extra machinery cannot change any assignment by more than one node.
Rejected as over-engineering; the executable length/anchor validation
captures the same evidence.

### Alternative 2: wait for the author-supplied table (keep D2 open)
Pros: zero interpretation.
Cons: blocks section-level RQ3/RQ4 indefinitely while the evidence on disk
(his own shapefile) determines the answer to within one grid step.
Rejected; the seam remains — an author CSV drops in verbatim.

---

## Rationale

The shapefile is Uemura's own section definition; only the segment-list
rendering of it was missing. Every reconstructed boundary is doubly
validated (polyline arc length, known assignments), the two genuinely
ambiguous boundary nodes (Satsunai KP 4.6/4.8 split at the chain's 4.69,
Tokachi one-step boundary tolerances) move one 0.2 km segment at most, and
the whole table is one CSV any author correction replaces.

---

## Consequences

* Section-level RQ3/RQ4 reporting (Tokachi 1–5, Satsunai 1–4) unblocks now;
  D2 closes with the residual "author may supply the authoritative table"
  note in the Phase 3 report manifest.
* `load_section_table(..., allow_gaps=True)` is an interface extension;
  existing strict behaviour is the default and existing tests keep passing.
* The within-section max rule enters `system_integration` as a small pure
  function with its own tests; dominance shares at section level are
  reported at the argmax segment.
* Should the author's table differ, every downstream product regenerates
  from CSVs (`scripts/phase3_campaign.py`); nothing hard-codes the spans.

---

## References

- Uemura et al. (2024), §2.4 (segment/section integration, Eq. 14).
- HKV/Docon WP2 final report PR3983 (2024), Ch. 3 (segments and sections)
  and Ch. 6 (system approach).
- `data/raw/gis/SECTIONS.shp` (+ .dbf names) — committed 2026-07-02.
- Notebook `Description WP2 Work week 3.ipynb` (assignment rule + the ten
  embedded node assignments), gitignored drop.
- ADR-0038 decision 2 (the D2 seam and contract), ADR-0042 (the drop
  census this reconstruction belongs to).
