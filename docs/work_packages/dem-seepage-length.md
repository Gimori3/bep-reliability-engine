# Work package: re-measure the seepage length L from a GSI DEM cross-section

> **SUPERSEDED -- WORK COMPLETED (header added 2026-07-31; content unchanged).**
> This is the task brief that launched the measurement, retained as its
> provenance. The work it commissions has been executed and closed:
>
> * decision: [`docs/decisions/0047-dem-surveyed-seepage-length.md`](decisions/0047-dem-surveyed-seepage-length.md) (ADR-0047, Accepted);
> * companion note + evidence: [`adr0047-dem-seepage-length.md`](decisions/adr0047-dem-seepage-length.md),
>   `adr0047-dem-seepage-length.json`, `adr0047-dem-seepage-length-ratio.json`;
> * driver: `scripts/dem_cross_section_study.py`; tests: `tests/test_dem_cross_section.py`.
>
> Outcome, so this brief is not mistaken for open work: L was **adopted at
> KP 62.0 alone** (47.0 to 40.0 m, 2026-07-29) on the principle *adopt where the
> 1998 value is wrong, hold where it is merely old*; KP 57.4/58.8/60.0 are held
> with their DEM values carried as an unadopted bracket.

Use everything below the line as the measurement procedure in
`d:\repositories\bep-reliability-engine`, together with the DEM-derived cross-section
file(s). Written 2026-07-28 as the follow-on to the foreshore-width resolution
(`docs/decisions/adr0025-foreshore-width-and-sensitivity.md`), which established that
**B_f is inert and L is the input actually worth measuring**.

**The DEM is already downloaded and verified — no QGIS step is required.** The original
plan routed the profile extraction through QGIS; that turned out to be unnecessary and
undesirable. QGIS cannot open JPGIS(GML) `.xml` natively (which is why it appeared to fail),
and a GUI step in the middle of a thesis pipeline is not reproducible. The GML DEM is a
trivially parseable text grid, so the extraction belongs in a committed script like every
other input path in this repo.

### What is already on disk and verified (checked 2026-07-28)

`data/raw/geometry/FG-GML-644331-DEM5A-20250620/` — 100 tiles, 53 MB, secondary mesh
**644331**, DEM5A (airborne LiDAR), `devDate` **2025-06-20**, source `orgMDId R05GC0022`.

- **Coverage: 42.916667–43.000000 N, 143.125–143.250 E** (9.3 × 10.2 km), mosaicking to
  2250 × 1500 cells at **6.18 m N-S × 4.53 m E-W**, **0.00 % nodata**, elevations
  25.83–132.33 m T.P.
- **All four Tokachi production sections are fully inside**, verified by inverse-projecting
  `data/raw/gis/SECTIONS.shp` (JGD2000 / Japan Plane Rectangular CS XIII, EPSG:2455) to
  lat/lon: the Tokachi polylines KP 56.4 / 58.0 / 59.6 / 61.4 / 62.4 span
  42.930–42.943 N, 143.140–143.241 E, i.e. inside the tile envelope with 0.7–1.9 km margin
  on every side. KP 57.4, 58.8, 60.0 and 62.0 are bracketed by those polylines.
- **Not covered, and not needed here:** Satsunai KP 6.4 and KP 7.0 fall south of the mesh
  (KP 5.2 is partial). `L` is only defined at the four Tokachi OYO sections, so this does
  not affect the task. If Satsunai geometry is ever wanted, download mesh **644321**.
- **The datum check in hard constraint 5 already PASSES.** A trial transect across the
  KP 62.0 levee (lon 143.1480) returns a crest of **48.44 m** against the OYO B-8 crest
  collar of **48.77 m**, and foreland/landside ground at **44.4–45.7 m** against
  高水敷高 **45.00 m** and `z_toe` **44.9 m**. GSI 標高 and the engine's m T.P. datum agree
  to a few tenths of a metre. Re-run this check yourself before trusting anything, but it is
  expected to pass.

### The GML format, so you do not have to reverse-engineer it

Each tile is one `<DEM>` with:
- `<gml:Envelope srsName="fguuid:jgd2024.bl">` → `<gml:lowerCorner>lat lon`, `<gml:upperCorner>lat lon`
  (note: **latitude first**, and the horizontal datum is **JGD2024**, while `SECTIONS.shp`
  is JGD2000 — sub-metre difference, irrelevant to a toe-to-toe length but worth stating).
- `<gml:high>nx-1 ny-1</gml:high>` → 225 × 150 per tile.
- `<gml:tupleList>` → `類型,標高` lines (`地表面,57.65`), row-major under
  `<gml:sequenceRule order="+x-y">`, i.e. **first row is the northernmost**, x increasing east.
- `<gml:startPoint>` is an offset into the grid: tiles may start part-way, so pad the head
  with nodata (−9999) rather than assuming a full `nx*ny` list. (All 100 tiles here are
  complete, but write the loader defensively.)

### What remains

Note the DEM survey vintage (**2025-06-20**) in the ADR — this is a 2025 surface against a
1998 geometry, which is the whole point of the vintage-mismatch constraint below.

Locating the KP stations: `data/raw/gis/SECTIONS.shp` gives Uemura's section polylines
directly (use those, they are already in the repo). The plan sheet
`docs/references/81_十勝川水系十勝川_01堤防現況平面図_007.pdf` covers KP 56–64 with the
KP 57.40 / 58.80 / 60.00 / 62.00 / 62.80 stations marked against named landmarks
(十勝川大橋, 木賊原樋門, 平原大橋, 伏古樋門, 中島橋) and is the independent cross-check.

---
