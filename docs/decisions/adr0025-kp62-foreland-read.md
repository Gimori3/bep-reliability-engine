# Analysis: KP 62.0 foreland confining-layer read (OYO 様式-3 sheet)

Supporting analysis for ADR-0025 (KP 62.0 foreland confinement). Companion
to `adr0006-leakage-boundary-ratios.md` (§5.3) and the ADR-0006 amendment.

> Provenance note: §§1–4 record the author's read of the OYO transverse sheet
> as delivered on 2026-07-05. §5 (repo reconciliation, same day) records an
> independent re-render of `docs/references/R062.000.pdf` at high zoom plus
> the 様式-4/-5/-6 sheets, which **corroborates the central conclusion**
> (no boring on the foreshore; bracket rather than point estimate) while
> **correcting two particulars**: the sheet is not fully blank riverward of
> B-7, and i_v = 0.97 is not evidence of an open foreland.

## 1. Is the Ac blanket continuous across the 44 m foreshore?

The sheet doesn't answer this — it contains no borehole within the
foreshore. Reading left to right: the channel is drawn schematically (mean
bed level 平均河床高 = 38.4 m) rising to the foreshore terrace at roughly
EL+45 m, with a drafting scale-break marking where the drawing stops being
literal about horizontal distance. The 高水敷幅 = 44 m annotation sits above
the terrace. Colored/hatched stratigraphy begins in earnest at borehole
**B-7** (depth 16.50 m, collar EL+47.77 m), whose collar sits 2–3 m above
the terrace — on the levee's riverside slope/toe, not out on the terrace.
B-8 (5.50 m, EL+48.77, crest) and B-9 (12.50 m, EL+46.55, landside) are
further landward still. There is no borehole anywhere within the 44 m
foreshore: on the ground truth of confinement the sheet is silent, not
negative.

## 2. Where is confinement lost — 4A, 4B, or partial?

Not determinable from this sheet: no data exists at any point along the
foreshore to say where confinement is present in the first place. The one
indirect hint is the Ac legend entry itself (地質凡例, 記事 column): at
KP 62.0, Ac is "標高45m付近に層厚0.3〜0.6m程度で薄く分布する" (distributed
thinly, 0.3–0.6 m, near EL 45) — mainly clay with some rounded gravel,
consistent with a marginal, easily-pinched-out unit and with the corrected
D_bl = 0.45 m.

## 3. Is KP 62.0 typical or anomalous for the reach?

All four neighbours (KP 57.4/58.8/60.0/65.0) show the identical structural
pattern: stratigraphy resolved at the levee borings, the open foreshore
compressed through a scale-break. None of the five OYO sheets independently
resolves foreshore blanket continuity — a reach-wide investigation-scope
limit (borings sited to characterize the levee, not the foreshore). So
KP 62.0 is **typical in data coverage** but **anomalous in consequence**:
its 44 m foreshore is six to fourteen times narrower than the others', which
is exactly why the data gap is inert elsewhere (tanh(B_f/λ_out) ≈ 0.96–1.00)
and bites at KP 62.0 (tanh ≈ 0.81).

## 4. Bottom line on defensibility (as delivered)

Model 4A at KP 62.0 is a modeling convenience (the ADR-0005
hinterland-proxy), not something the sheet's foreshore data support. Treat
the confinement state as unresolved rather than assumed and bracket it
(r_e ≈ 0.33 blanketed vs ≈ 0.45 open, the ~37% head difference) until an
independent read arrives — a foreshore test pit/GPR line, the HDB GIS/CAD
data, or the 様式-5 logs behind B-7. A genuine missing-input problem, not a
formula problem — the same character as the hinterland-extent gap on the
other side of the levee.

## 5. Repo reconciliation (2026-07-05): the 様式-4/-5/-6 read

Independent high-zoom render of `R062.000.pdf` (all five sheets), done in
response to the ADR-0025(a) instruction. Corroborations and corrections:

1. **Corroborated:** no boring on the foreshore; no lab sample from B-7 at
   all (様式-4 lists only the three B-9 samples; the one spanning the Ac
   elevation, 1.0–2.0 m ≈ EL 45.6–44.6, is 43.9% gravel / 37.5% sand /
   13.7% silt / 4.9% clay — gravelly, no competent clay); B-7's columnar log
   shows gravelly texture through the Ac elevation. The cheap B-7 read
   therefore **cannot collapse the bracket to a number**.
2. **Correction (sheet content):** the 様式-3 drawing is **not fully blank
   riverward of B-7**. A thin band between parallel boundary lines at the
   Ac elevation (EL ≈ 44–45), texture-matched to the band the "Ac" label
   points to on the landside, is drawn beneath a substantial stretch of the
   foreshore riverward of B-7, stopping short of the channel scale-break.
   Read as mapped Ac continuing over part — not all — of the 44 m. This is
   positive (drawn) evidence *for* confinement at and riverward of the
   riverside toe, absent from §1's "shows nothing" reading; the outer
   foreshore remains uninvestigated, so the bracket stands with its
   evidence weight shifted toward the blanketed side (a partial-cover
   middle anchor computes to r_e ≈ 0.37).
3. **Correction (i_v interpretation):** OYO's own seepage analysis (様式-5
   conditions + 様式-6 results) used a **fully blanketed** model — a
   continuous cohesive layer ② (粘性土, k = 3.00E-04 cm/s = 3.0e-6 m/s,
   ~1.8–2 m thick, the same lumped layer the D_bl correction rejected as an
   aquitard thickness) across the entire 594 m FE domain **including the
   foreshore** — and still produced 局所動水勾配 i_v = 0.97 (vertical) /
   0.66 (horizontal) under the design flood (41.60 → 46.68 m MSL).
   **i_v = 0.97 is therefore what a blanketed model yields and is not
   evidence of an open foreland**; §4's "would be the expected signature of
   Model 4B" lean, and any earlier use of i_v = 0.97 as pro-open evidence,
   are corrected accordingly.
4. **Disposition (author, 2026-07-05, ADR-0025):** on this evidence the
   §4 "bracket until data arrive" recommendation was superseded by option
   iii — the **blanketed foreland is adopted as the KP 62.0 baseline**, and
   the open-entry end (r_e ≈ 0.45, +37%) is recorded as an
   evidence-disfavored, on-demand sensitivity (one config flag,
   `foreland_treatment: open_entry`), to be run only if foreshore ground
   truth (test pit / GPR / HDB GIS-CAD) later arrives. The channel (bed
   EL 38.4 m) fully penetrates the aquifer, so entry resistance exists only
   across whatever fraction of the 44 m the Ac actually covers — the one
   quantity no in-repo data can pin, and the one that would re-open this.
