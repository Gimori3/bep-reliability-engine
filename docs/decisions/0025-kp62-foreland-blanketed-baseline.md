# ADR-0025: KP 62.0 Foreland Confinement — Blanketed Baseline Adopted; Open-Entry Recorded as an Evidence-Disfavored, On-Demand Sensitivity

Date: 2026-07-05 (amended 2026-07-28)
Status: Accepted (owner decision 2026-07-05, option iii: blanketed baseline with logged
sensitivity; the B-7/様式-5 read below is the converging evidence). **Amended 2026-07-28:
the logged on-demand sensitivity has been EXECUTED — it is no longer pending, and it no
longer depends on foreshore ground truth arriving.** The decision below (blanketed
baseline adopted, open entry evidence-disfavored) stands unchanged; what changes is that
the open-entry end is now *measured* rather than only bounded on r_e, at
max |ΔP_f,trans| = 2.3e-4 (KP 62.0, matrix, N = 1e5) with the static branch exactly
invariant. See "Sensitivity executed" below and the companion note
`adr0025-foreshore-width-and-sensitivity.md`.

**Second amendment 2026-07-28 (borehole evidence; ADR-0048 drop).** New independent
evidence bears directly on the phrase "evidence-disfavored", and the honest position is
that it **weakens that phrase while leaving the decision untouched**. Kunijiban borehole
H25TK-B5 sits in the floodplain ~300 m riverward of the levee at **KP 61.00** — one
kilometre downstream of the governing section — and logs river gravel from 0.10 m depth
with **no cover layer whatsoever** (9.95 m of 砂礫 straight to the Nagareyama tuffaceous
sandstone). Its companion H25TK-B4, same campaign and same riverward position at KP 58.80,
logs 2.80 m of homogeneous silt. So the foreland blanket in this reach is demonstrably
**discontinuous**, present at one station and wholly absent 2.2 km upstream, rather than
the continuous sheet the blanketed-tanh baseline schematizes.

What this does and does not change:

- It **does** remove the basis for calling open entry evidence-*free*. A zero-cover
  foreland is now an observed condition in this reach, not a hypothetical.
- It **does not** change the adopted baseline, for two independent reasons. First,
  neither hole is at KP 62.0 and neither is at the entry point x₁ itself (both are
  mid-floodplain), so they do not establish the condition *at the governing section*.
  Second, and decisively, the open-entry sensitivity has since been **executed**: it moves
  KP 62.0 transient P_f by at most 2.3e-4, so even if the KP 62.0 foreland were fully
  unblanketed the consequence for the deliverable is immaterial.
- The `D_fore`/`k_fore` = landside-`D_bl`/`k_bl` proxy (ADR-0005) is separately shown
  **conservative at KP 58.8**, where measured foreland cover is 2.80 m against the 0.85 m
  proxy — a thicker entry blanket means more entry resistance and a lower r_e.

Net: the wording "evidence-disfavored" is downgraded to "not established at KP 62.0"; the
baseline, the default, and every persisted number stand. See
`docs/tokachi_bep_inputs_provenance.md` §8.6 and ADR-0048.

## Context

The 2026-07-04 r_e source analysis (ADR-0006 amendment) closed the ratio-form
provenance and the hinterland extents, and surfaced exactly one potentially
non-conservative item: **the KP 62.0 foreland confinement**. The engine models
the 44 m foreshore as a leaky Ac blanket (ADR-0005 hinterland proxy: D_fore =
D_bl = 0.45 m, k_fore = k_bl = 3.0e-6 m/s) with the ADR-0006 tanh correction,
giving λ_out,eff ≈ 31.5 m and r_e ≈ 0.330 at the prior means. If the foreshore
were effectively unblanketed, the USACE Case 7a entry length x₁ → 0 (radial
entry: x₁ ≈ 3–10 m) and r_e would rise to ≈ 0.41–0.45 — **+23% to +37% on r_e
and on the driving head, the non-conservative direction, at the governing
section**. The wide-foreshore sections are immune (tanh credits 0.96–1.00);
KP 62.0 is the one section narrow enough for the uninvestigated zone to
matter.

## Evidence (OYO R062.000, read 2026-07-05; companion note `adr0025-kp62-foreland-read.md`)

1. **No boring exists on the foreshore, reach-wide.** All three KP 62.0
   borings sit on/behind the levee (B-7 riverside slope, collar EL+47.77;
   B-8 crest; B-9 landside). The same investigation-scope limit holds at all
   five OYO sections; KP 62.0 is typical in coverage, anomalous in
   consequence (44 m vs 200–600 m foreshores).
2. **様式-4 contains no B-7 samples** — all three KP 62.0 lab samples are
   B-9 (landside); the B-9 sample spanning the Ac elevation (1.0–2.0 m,
   EL 45.6–44.6) is 43.9% gravel / 37.5% sand / 13.7% silt / 4.9% clay:
   gravelly, no competent clay. B-7's columnar log likewise shows gravelly
   texture through the Ac elevation, with no lab confirmation either way.
3. **The 様式-3 sheet is not blank riverward of B-7**: a thin band between
   parallel boundary lines at the Ac elevation (EL ≈ 44–45), texture-matched
   to the labeled Ac, is drawn beneath a substantial stretch of the foreshore
   riverward of B-7 before the drawing goes bare toward the channel
   scale-break. Read as mapped Ac continuing over part (not all) of the
   44 m. The channel itself (mean bed EL 38.4 m) fully penetrates the
   aquifer — the Ac can only add entry resistance across the foreshore
   width, which is exactly what the tanh term models.
4. **OYO's own seepage model was fully blanketed — and still produced
   i_v = 0.97.** The 様式-5 evaluation-conditions sheet shows a continuous
   cohesive layer ② (粘性土, k = 3.00E-04 cm/s = 3.0e-6 m/s, ~1.8–2 m)
   spanning the whole 594 m FE domain including the foreshore, under the
   design flood (41.60 → 46.68 m MSL). The near-critical vertical gradient
   at the toe is therefore what even a generously-blanketed model yields,
   and **i_v = 0.97 must not be cited as evidence of an open foreland**.

Net evidence: **partial-to-substantial foreland confinement is the
better-supported reading** (drawn Ac at and riverward of the riverside toe;
OYO's own blanketed schematization; no positive evidence of absence); the
open end is not excluded by hard data (no foreshore boring) but is
evidence-disfavored.

## Decision (owner, 2026-07-05 — option iii)

**The blanketed foreland is the KP 62.0 baseline.** The engine's current
treatment (ADR-0005 proxy + ADR-0006 tanh, r_e ≈ 0.330 at the prior means)
stands as the production physics; the question is closed as converged on the
evidence above.

**The open-entry end is a documented, evidence-disfavored sensitivity — not
a co-equal bracket member carried through downstream.** For the record, the
quantified anchors at the prior means:

| Foreland treatment | λ_out,eff / x₁ | r_e | vs. baseline |
|---|---|---|---|
| **Blanketed tanh (adopted baseline)** | 31.5 m | **0.330** | — |
| Partial cover (Ac to ~mid-foreshore; informative middle) | ~18 m | ~0.372 | +13% |
| Open entry (x₁ = 0; bounding sensitivity) | 0 | 0.452 | +37% |

The sensitivity is to be run **only if foreshore ground truth is later
obtained** (test pit / GPR line across the 44 m terrace, or Hokkaido
Development Bureau GIS/CAD for the KP 62.0 works). Note KP 62.0
simultaneously carries the *conservative* open-exit hinterland
simplification (ADR-0006 amendment, 西士狩樋門 at ~KP 62.0): the two boundary
uncertainties push r_e in opposite directions, and the thesis describes
KP 62.0's boundary conditions in those terms.

## Implementation (landed with this ADR)

- **Config:** `foreland_treatment: Literal["blanketed_tanh", "open_entry"]
  = "blanketed_tanh"` (ADR-0015 run-varying input; recorded in run metadata
  as `foreland_treatment`). One flag runs the sensitivity later; the default
  is the adopted baseline and is baseline-neutral (bit-identical behaviour).
- **Engine:** threaded run.py `_EvalSettings` → `evaluate_batch` /
  `evaluate_realization` as the additive keyword-only `foreland_open`
  (default False; ADR-0017 precedent, frozen positional signature
  untouched). When open, the M8 preamble zeroes the effective entry length
  (x₁ = 0) in both scalar and batch paths; the measured
  `geometry.foreshore_width` is never mutated, and the
  `metadata['leakage_geometry']` record reflects the physics actually run.
- **Sweep: NO `_openfore` variants are generated.** The production sweep
  stays at 8 configs; the drift guard pins `foreland_treatment ==
  "blanketed_tanh"` on every sweep member and the filename pattern rejects
  any variant file. An on-demand sensitivity run is a hand-derived copy of a
  KP 62.0 config with `foreland_treatment: open_entry`, a distinct
  `cross_section_id`/output path, and its metadata stamp keeps its results
  from masquerading as baseline.

## Sensitivity executed (amendment, 2026-07-28)

The sensitivity logged above as "to be run only if foreshore ground truth is
later obtained" **was run without waiting for that data**, because the cost of
running it turned out to be minutes rather than a field campaign. Driver
`scripts/foreshore_width_study.py`, evidence
`docs/decisions/adr0025-foreshore-sensitivity.json`, narrative companion
`adr0025-foreshore-width-and-sensitivity.md`. Production matrix configs,
N = 1e5, Δt = 225 s; **every baseline arm asserted bit-identical to its
persisted production sweep** before comparison.

| Section | B_f [m] | tanh credit | max abs ΔP_f,trans at B_f → 0 | max abs ΔP_f,static |
|---|---|---|---|---|
| KP 57.4 | 200 | 0.969 | 0.00111 | **0.00000** |
| KP 58.8 | 325 | 0.995 | 0.00170 | **0.00000** |
| KP 60.0 | 600 | 1.000 | 0.00440 | **0.00000** |
| **KP 62.0** | **44** | 0.835 | **0.00023** | **0.00000** |

Three findings that change how this ADR should be read:

1. **The +37% r_e figure in the Context above does not propagate.** At KP 62.0
   the full open-entry end moves transient P_f by ≤ 2.3e-4 and static P_f by
   exactly 0. r_e drives only the uplift/heave gate (ADR-0028), and at this
   section the gate is open with margin across the whole failure-relevant stage
   range: heave threshold D_bl·γ'_bl/γ_w ≈ 0.32 m against a transmitted head
   r_e·(h − z_toe) ≈ 0.45 m already at the lowest failing level (46.25 m MSL).
   r_e is effectively **inert at KP 62.0** — which is *not* a general result
   (the r_e-halved QA member at KP 58.8 moved P_f by 0.181, because −50% pushes
   that section onto its 0.60 m threshold).
2. **The tanh has saturated at every section.** At KP 62.0 (λ_out ≈ 38.7 m) any
   B_f ≳ 100 m gives r_e = 0.3112 identically; 250 m, 600 m and infinity are
   numerically the same answer. The adopted 44 m is the *conservative* end of
   its own uncertainty range.
3. **KP 62.0 is not the section where the foreland matters most.** Its measured
   B_f effect is the *smallest* of the four, and its r_e (0.330) is the *lowest*
   of the four — i.e. it transmits the least head, not the most. The narrative
   consequence is recorded in the companion note §8.

## Data that would re-open this item

Superseded by the amendment above. The original trigger — a foreshore boring,
test pit, or GPR line across the 44 m terrace, or HDB GIS/CAD cross-sections,
showing the Ac absent or pinched out — would still resolve the *stratigraphic*
question, but it can no longer change a decision: the open end of that bracket
is measured at ΔP_f ≤ 2.3e-4. Such data is therefore **no longer a blocker for
anything**, and this ADR does not need to be superseded when it arrives. The
様式-5 / B-7 in-repo read is **done** (2026-07-05): it bounded the question in
the blanketed direction and no further in-repo data can move it.

The `foreshore_width_m` column itself was independently verified on 2026-07-28
(all four 様式-3 高水敷幅 annotations re-read verbatim; MLIT 2008 堤防現況縦断図
row 4)② corroborates); the OYO 1998 source is retained over the later MLIT
values for the reasons in the companion note §7.

## References

- ADR-0005 (foreland proxy — the baseline this ADR confirms as adopted),
  ADR-0006 (amended 2026-07-05; its Open Item is resolved by this record),
  ADR-0021 (KP 62.0 governing-section context).
- Companion notes: `adr0025-kp62-foreland-read.md` (the OYO sheet read:
  owner's read §§1–4 + repo reconciliation §5),
  `adr0025-foreshore-width-and-sensitivity.md` (2026-07-28: B_f source
  verification, the 高水敷幅 definition, and the executed sensitivity;
  evidence `adr0025-foreshore-sensitivity.json`),
  `adr0006-leakage-boundary-ratios.md` §5.3,
  `adr0006-hinterland-l3-resolution.md` (the opposing conservative
  hinterland item at the same section).
- USACE (2000) EM 1110-2-1913 App. B Eqs. B-7/B-8 (x₁ for open and blocked
  entries); TAW (2004) Model 4B (radial entry, the unblanketed-foreland
  form).
- OYO (1999) R062.000: 様式-3 (transverse section, B-7/B-8/B-9), 様式-4
  (B-9 samples only), 様式-5 (evaluation conditions: continuous cohesive
  layer ②, k = 3.0e-6 m/s), 様式-6 (浸透流計算: 594 m FE domain, design
  flood 41.60→46.68 m, 局所動水勾配 i_v = 0.97 / i_h = 0.66).
