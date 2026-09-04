# Task: build the R10 Tier 1 foreshore-exhaustion screening indicator

## What you are building, in one sentence

A deterministic, per-segment screening indicator that answers: **how long does a
given flood take to erode away the high-water bed in front of a levee, and how
does that compare with how long the flood actually lasts?**

This is **Tier 1 only** of `docs/scoping_bank_retreat_mechanism.md`. Tier 2 (a
probabilistic fragility joining the Phase 3 composition) and Tier 3 (morphodynamic
coupling) are **explicitly declined by the author**. Do not build them, do not
add a mechanism to the Phase 3 series composition, and do not touch any
production default.

Read `docs/scoping_bank_retreat_mechanism.md` in full before starting. This work package
assumes it.

---

## Why this exists (the argument you are serving)

Phase 3 composes BEP, overflow and fluvial scour per segment. Under the
ADR-0042 decision 9 dimensionally-corrected conversion the scour branch returns
**exactly zero at all 114 segments in both climate scenarios**. Yet the documented
failure record for this system is:

| Event | Location | Official attributed cause |
|---|---|---|
| 2016-08 | Otofuke KP21.2 L | falling-limb channel migration; bank + embankment erosion |
| 2016-08 | Satsunai KP40.5 L | falling-limb channel migration; bank + embankment erosion |
| 2016-08 | Satsunai KP25.0 L | landside overtopping from a Tottabetsu breach |
| 2011-09 | Otofuke KP18.2 | high-water-bed erosion advancing into the embankment, ~5 m of levee length per hour, no revetment present |

So the mechanism with the strongest empirical claim to having caused levee failure
here contributes nothing, while the mechanism that dominates the composition (BEP)
has never been observed to breach here. Your indicator does not close that gap —
Tier 2 would — but it **quantifies which segments are even exposed to it**, which
converts an admission in the Discussion into a measured statement.

**Established 2026-07-28, do not re-derive:** Uemura's P2 cannot be repaired by
recalibration. Structurally it *is* lateral (accumulated horizontal erosion versus
levee body width), but its shear comes from a uniform-flow Manning velocity driven
by *floodplain inundation depth*, and `SegmentSurfaceInputs` carries no thalweg
position, no bend curvature and no foreshore width. It therefore has no state in
which a receding flood is more dangerous than a peak one — yet three of the four
failures above happened on the falling limb. See
`docs/tokachi_basin_document_review_2026-07-27.md` and Chapter 7 of the thesis.

---

## Step 1 — Orient

1. architecture and decision records — the repo contract.
2. Apply the repository's tracked change-control, architecture, operations,
   analysis, and documentation rules before starting.
3. `docs/scoping_bank_retreat_mechanism.md` — the task definition.
4. **`docs/decisions/adr0025-foreshore-width-and-sensitivity.md`** — critical.
   It source-verifies the exact variable you are consuming. Key results you must
   not contradict: `foreshore_width_m` **is** 高水敷幅, the high-water-bed width;
   it equals the USACE $L_1$; the OYO 1998 values 200 / 325 / 600 / 44 / 0 m are
   **verified and retained**, with an MLIT 2008 profile recorded as corroboration
   only. This matters enormously for you, because the 2011 Otofuke failure was
   *precisely* the consumption of the 高水敷 — so your state variable is the
   right one and is already source-verified.
5. `scripts/foreshore_width_study.py` — an existing companion driver. It asks a
   **different** question (does $B_f$ matter for BEP fragility, via the $r_e$
   foreland credit). **No collision, but read it: it is the house pattern for a
   study driver in this repo** — argparse, JSON evidence output, explicit
   assertions, nothing persisted to `results/`.

---

## Step 2 — What to compute

For each segment, and for each forcing case, integrate a lateral retreat rate over
the time the flood is capable of mobilising the high-water bed, and compare the
cumulative retreat against the available foreshore width.

```
time_to_exhaustion  =  B_f / (mean lateral retreat rate while mobilising)
exposure_ratio      =  cumulative retreat over the event / B_f
```

`exposure_ratio >= 1` means the event is, on this bounding treatment, capable of
consuming the foreshore and reaching the embankment. Report both quantities; the
ratio is the screening flag, the time is the interpretable number.

**Design decisions are yours**, but these are the constraints:

- **Forcing.** Use stage series that already exist and are already verified. The
  2016 event comes from
  `bayesian_reliability_updating.events.observed_event_record` (verified exact
  against the official record at four gauges on 2026-07-28). Design-scale and
  climate cases come from `run.conditioning_hydrographs_for_config`. Do not
  invent a hydrograph.
- **Mobilisation threshold.** The high-water bed erodes when it is engaged by the
  flow. Choose and *justify* a threshold — the natural candidate is the stage at
  which the high-water bed is inundated. `hydrographs.flood_timescales` gives you
  duration statistics on a record if useful.
- **Retreat rate.** This is the weak link and you must treat it as such (see
  Step 4). The one documented datum is the 2011 Otofuke figure. **Note carefully:
  ~5 m per hour is a rate of loss of levee *length* (longitudinal), not lateral
  retreat.** You cannot use it as a lateral rate without an explicit, stated
  conversion assumption — or, better, without treating it as one point in a
  bracket. Do not quietly equate the two.
- **Bracket rather than calibrate.** Run a low / central / high retreat-rate
  bracket spanning at least an order of magnitude and report the indicator across
  it. A single number here would be false precision.

**Segments.** Use `system_integration.segments.build_registry()` (114 segments).
`foreshore_width_m` lives per OYO cross-section in
`data/processed/tokachi_bep_inputs.csv`, so only the four confined sections have a
measured width. State plainly how you handle segments without one — reporting the
indicator only where a measured width exists is an entirely acceptable and honest
answer, and is preferable to interpolating a width you do not have.

**Sanity anchor.** KP 62.0 has 44 m of foreshore; KP 60.0 has 600 m. If your
indicator does not separate those two by more than an order of magnitude,
something is wrong — go and find out what before writing it up.

---

## Step 3 — Scope discipline (non-negotiable)

This is a **study**, not an engine change. Concretely:

- **Nothing is persisted to `results/`.** Write evidence JSON to
  `docs/decisions/` or a study output path, following the house pattern.
- **No new `Config` field.** No new configuration axis at all. If you find
  yourself wanting one, you have drifted into Tier 2 — stop and say so.
- **Do not modify** `data/processed/tokachi_bep_inputs.csv`, anything in
  `configs/`, or any production default. The CSV is drift-guarded by
  `tests/test_configs.py::test_config_matches_csv_and_thesis_priors`, and a change
  there invalidates all 8 production sweeps, the Phase 2 replay hash gate, and
  the Phase 3 campaign.
- **Do not add a mechanism to `system_integration.composition`.** The Phase 3
  headline numbers must be bit-identical after your work.
- **No ADR required** provided it stays a study. If your design forces an
  architectural decision, stop and ask rather than writing ADR-0047 unwork packageed.
- Physics-free where it can be: the indicator is a screening calculation, so keep
  it pure and inject the forcing, following the `convergence.py` / `sensitivity.py`
  precedent of stats-and-logic modules with physics passed in.

---

## Step 4 — Intellectual honesty requirements

This indicator rests on a **single narrative observation** of a retreat rate. That
is thin, and the write-up must say so without being asked twice. Specifically:

- State that the 2011 figure is one observation from a prose account in a
  flood-control history, not a calibrated rate, and that it is longitudinal not
  lateral.
- Present the result as **order-of-magnitude screening**, never as a probability
  and never as a failure rate.
- Say explicitly what the indicator **cannot** do: it has no planform, no bend
  mechanics, no sediment supply, and no representation of *why* a thalweg
  approaches one bank rather than another. It answers "is there enough foreshore
  to survive this flood at this assumed retreat rate", not "will this levee fail".
- If the bracket spans a range in which the answer flips from "no segment exposed"
  to "most segments exposed", **that is the finding** — report it as such rather
  than picking the central value and presenting a clean verdict. A negative or
  indeterminate result honestly reported is a success here.

---

## Step 5 — Deliverables

1. **`scripts/foreshore_exhaustion_study.py`** — the driver. Argparse, JSON
   evidence output, docstring stating the method and its limits, following the
   `scripts/foreshore_width_study.py` pattern.
2. **Evidence JSON** with the per-segment / per-section results across the
   retreat-rate bracket and the forcing cases.
3. **A companion note**, `docs/decisions/r10-foreshore-exhaustion-screening.md`,
   in house style: what triggered it, method, the bracket, results, what it does
   and does not establish, and what would re-open it. Cross-reference
   `docs/scoping_bank_retreat_mechanism.md` and ADR-0025's companion.
4. **Tests** in `tests/` for whatever pure logic you add — the arithmetic of the
   indicator, the threshold handling, and the boundary cases ($B_f = 0$ at
   KP 63.4; zero-duration forcing). Match the house test style.
5. **A figure** if it earns its place — the natural one is exposure ratio versus
   foreshore width across the bracket, which would show the KP 62.0 / KP 60.0
   separation at a glance. Save to `docs/figures/`.
6. **Thesis integration** in `d:\repositories\msc-thesis`. The result belongs in
   Chapter 7 §"Limitations and Sources of Uncertainty", in the subsection on the
   surface-mechanism model set, which currently ends by saying that extending the
   surface set is the most consequential improvement available and is recommended
   in Chapter 8. Your indicator turns the preceding admission into a quantified
   exposure statement — integrate it there, and update the Chapter 8
   recommendation to reflect that Tier 1 now exists and Tier 2 is the remaining
   step. Add `references.bib` entries only if you cite something new; romanise
   Japanese titles with a bracketed English gloss rather than pasting raw CJK.

---

## Step 6 — Verification before you report

- `pytest -m "not slow"` green. **Baseline is 496 passed, 7 deselected.**
- `ruff check .` and `black --check .` clean.
- **Prove the Phase 3 numbers did not move.** Re-run the Phase 3 campaign or the
  composition path and confirm the headline outputs are unchanged. Say explicitly
  in your report that you checked this.
- Thesis: `latexmk -pdf -interaction=nonstopmode report.tex`. Do **not** pass
  `-halt-on-error` — a pre-existing font-expansion warning in Chapter 4 stops the
  build spuriously. Success: a PDF is produced and `grep -c "undefined" report.log`
  returns **0**. There are ~168 pre-existing `Unicode character` errors from CJK in
  the bibliography; confirm you have not increased the count.

## Definition of done

A study driver, evidence JSON, companion note, tests, and a Chapter 7 paragraph
that states — with a number and a stated bracket — which study segments have
enough high-water bed to survive a 2016-class and a design-class flood at the
assumed retreat rates, and which do not. Both repos green. No production default
touched, no Phase 3 number moved.

Work autonomously. Ask only if the design would require a `Config` field, an ADR,
or a change to a production default — all three mean you have left Tier 1.
