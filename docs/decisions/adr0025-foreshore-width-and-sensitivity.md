# Foreshore width B_f: source verification, definition, and measured fragility sensitivity

Companion note to **ADR-0025** (KP 62.0 foreland confinement). Date: **2026-07-28**.
Supersedes nothing; **changes no input value, no config, and no default**. It closes
ADR-0025's registered on-demand sensitivity with a measured number, verifies the
`foreshore_width_m` column against its source and against an independent second source,
and corrects a Study Area narrative claim that the engine does not support.

Driver: `scripts/foreshore_width_study.py` → evidence JSON
`docs/decisions/adr0025-foreshore-sensitivity.json`.

---

## 1. What triggered this

A 2026-07-27 review question: Google Earth shows roughly **200–300 m** between the
KP 62.0 right-bank levee and the water, but `data/processed/tokachi_bep_inputs.csv`
records `foreshore_width_m = 44` and the provenance flags it "narrowest" — the pillar of
the Study Area argument that KP 62.0 combines the thinnest blanket with the least foreland
attenuation. Four hypotheses were on the table: (a) the OYO source is wrong, (b) the
earlier extraction from the OYO report was wrong, (c) the 1998 value is stale
(channel migration + 樹林化 over ~28 years), (d) 44 m is a high-water value and 200–300 m
the normal-flow one.

**All four are refuted.** The value, the extraction, and the quantity are correct; the
Google Earth reading is also correct but measures a different feature.

## 2. The definition — the whole discrepancy in one term

The OYO 様式-3 sheet annotation reads **高水敷幅 = 44m**. 高水敷 (*kōsuishiki*) is the
**high-water bed**: in a compound-section (複断面) river, the terrace *one step above* the
低水路 (*teisuiro*, low-water channel). It is **dry in normal flow** and inundates only
during events. Standard Japanese river-engineering usage, per the Niigata and Miyagi
prefectural river glossaries: *複断面の形をした河川で、平常時に水の流れている部分が低水路、
それより一段高い部分が高水敷*.

The KP 62.0 sheets give the geometry explicitly:

| Feature | Elevation [m T.P.] | Source |
|---|---|---|
| 高水敷高 (terrace surface) | **45.00** | 様式-5, 河川水位波形 annotation |
| Base-flow water level | **41.60** | 様式-5, hydrograph table (point A/F) |
| 平均河床高 (mean bed) | **38.4** | 様式-3 channel schematic |
| Design HWL | 46.68 | 様式-3 / 様式-5 |
| `geometry.z_toe` (landside toe) | 44.9 | ADR-0021 |

The terrace stands **3.4 m above normal water** and ~6.6 m above mean bed. The Tokachi
here is a braided gravel-bed reach (河道分類 **セグメント 1** on the MLIT profile), so the
低水路 is hundreds of metres wide and mostly **dry gravel bar** at low flow. From imagery
one therefore sees: levee → 44 m of vegetated berm → a step down → a few hundred metres of
pale braid plain carrying the water threads. Measuring "levee to water's edge" sweeps up
the braid plain and lands at 200–300 m. Both numbers are real; they are different
features.

Incidental consistency check: `z_toe` = 44.9 m and 高水敷高 = 45.00 m coincide within
0.1 m at KP 62.0, read from two different sheets — which is why the retired
"foreshore-crest exit elevation" placeholder (ADR-0021) happened to be nearly harmless at
this section specifically, and materially wrong at the others.

## 3. Source verification — the extraction was correct

All five OYO 様式-3 sheets were re-rendered from
`docs/references/R0*/81_十勝川水系十勝川_R0*_03堤防横断方向土質調査結果図.pdf` (raster, no
text layer) and the annotation read directly:

| KP | 様式-3 annotation | CSV `foreshore_width_m` |
|---|---|---|
| 57.4 | 高水敷幅 = 200m | 200 ✓ |
| 58.8 | 高水敷幅 = 325m | 325 ✓ |
| 60.0 | 高水敷幅 = 600m | 600 ✓ |
| 62.0 | 高水敷幅 = 44m | 44 ✓ |

Four of four verbatim. There is no extraction error and no transcription error.

## 4. Independent corroboration — a second, later, MLIT source

`docs/references/81_十勝川水系十勝川_R_02堤防現況縦断図_007.pdf` (MLIT 堤防現況縦断図,
整理番号 8/13, KP 56–64) carries **row 4)② 高水敷幅 Bfp(m)** as a longitudinal plot. Its
detailed-inspection row 12) reproduces the same per-section 局所動水勾配 values as the OYO
study (KP 62.0 `Iv=0.970 ih=0.660`), confirming it covers this reach and bank. The
inspection vintage is **2008-03** (`docs/references/tokachi_river_basin/ctll1r0000001cmh.pdf`:
*今回の調査につきましては、平成２０年３月時点の結果となります*) — a decade after OYO.

Digitized off the raster (axis calibrated on the 50 m / 100 m gridlines and the 0.5 km
verticals; **±~5 m, and the row clips at ~150 m**):

| KP | MLIT Bfp (digitized, 2008) | OYO 高水敷幅 (1998) |
|---|---|---|
| 57.4 | ≥148 (clipped) | 200 |
| 58.8 | ≥148 (clipped) | 325 |
| 60.0 | ≥148 (clipped) | 600 |
| **62.0** | **≈34** | **44** |
| 63.4 | ≈28 | 0 ("river-tight", see §8) |
| 60.3–63.9 reach | 17–35 throughout | — |

The narrow-foreshore character of KP 62.0 and the whole KP 60.3–63.9 reach is
independently confirmed, and the wide sections are confirmed to exceed the readable range.
**Hypothesis (c) is refuted directly**: over 1998 → 2008 the KP 62.0 foreshore did not
widen; if anything it reads slightly narrower, within digitization error.

## 5. Why 高水敷幅 is the correct quantity for B_f

`foreshore_width` enters exactly one kernel — `hydraulics.leakage_length_out`, as
`lambda_out_eff = lambda_out * tanh(B_f / lambda_out)` (ADR-0006 Decision 1) — and thence
`r_e`. Since **ADR-0028**, `r_e` drives *only* the uplift/heave gate; both piping heads are
raw. Nothing else in any of the three packages consumes it.

The governing definition is USACE (2000) EM 1110-2-1913 App. B ¶h, verbatim:

> The effective source of seepage entry into the pervious substratum (point A in
> Figure B-1) is defined as that line riverward of the levee where **a hypothetical open
> seepage entry face fully penetrating the pervious substratum** and with **an impervious
> top stratum between this line and the levee** would produce the same flow and
> hydrostatic pressure beneath and landward of the levee as will occur for the actual
> conditions riverward of the levee.

with `L1` = "Distance from river to riverside levee toe", `x1 = tanh(c·L1)/c`.

At KP 62.0 the low-water channel bed (38.4 m) lies ~6 m below the Ac base (~44 m), so the
channel **fully penetrates the aquifer** — it *is* the entry face (ADR-0025 Evidence 3
states this). The braid-plain gravel riverward of the terrace is scoured aquifer material
at outcrop and contributes **zero** entry resistance; including it in B_f would be wrong.
The blanket exists only on the 高水敷. **B_f = 高水敷幅 is exactly the USACE L1.**

**On the "at high water it must be 0" intuition.** B_f is not a distance to a waterline.
It is the length of low-permeability blanket between the levee toe and the aquifer-entry
face — a geometric/stratigraphic property, **stage-independent**. During a flood the
foreland is submerged and the river head stands *on top of* the blanket across its full
width, which is precisely the configuration blanket theory assumes. `B_f = 0` means "no
blanket riverward of the toe" (the ADR-0025 `open_entry` case), not "water touches the
levee".

Corroborating mechanism from Japanese practice: PWRI (2014) 河川堤防の浸透に対する照査・
設計のポイント attributes the 2012 Yabe River breach partly to 高水敷の砂礫層（Fg 層）と
As 層が繋がっていた — foreshore gravel connected to the aquifer, i.e. exactly the
`open_entry` end of this bracket.

## 6. Measured sensitivity — ADR-0025's open item, closed

Production matrix configs, N = 1e5, Δt = 225 s. **Every baseline arm is asserted
bit-identical to its persisted production sweep** before any comparison is reported
(`scripts/foreshore_width_study.py::_assert_baseline_bit_identical`), so this is
drift-guarded. Full numbers in `docs/decisions/adr0025-foreshore-sensitivity.json`.

**B_f → 0 (the ADR-0025 `open_entry` bound, x1 = 0) at every confined section:**

| Section | B_f [m] | tanh credit | max abs ΔP_f,trans | at stage [m MSL] | max abs ΔP_f,static |
|---|---|---|---|---|---|
| KP 57.4 | 200 | 0.969 | 0.00111 | 40.00 | **0.00000** |
| KP 58.8 | 325 | 0.995 | 0.00170 | 40.50 | **0.00000** |
| KP 60.0 | 600 | 1.000 | 0.00440 | 42.75 | **0.00000** |
| **KP 62.0** | **44** | 0.835 | **0.00023** | 53.00 | **0.00000** |

Deleting the *entire* foreshore at every section moves transient P_f by at most
**0.0044**, and the static branch by **exactly zero** — the latter is asserted, not merely
observed, and is the expected ADR-0028 consequence (the static comparator has no foreland
dependence).

**Tanh saturation at KP 62.0** (λ_out ≈ 38.7 m at the prior means). Analytic r_e:

| B_f [m] | r_e | vs 44 m |
|---|---|---|
| 0 (open entry) | 0.4518 | +36.7% |
| **44 (adopted)** | **0.3304** | — |
| 100 | 0.3123 | −5.5% |
| 250 / 300 / 600 / ∞ | 0.3112 | −5.8% |

Above ~100 m ( ≈ 2.5·λ_out ) the tanh has saturated: 250 m, 600 m and infinity are
numerically the same answer. The measured arms agree: 44 → 100 m gives max abs ΔP_f,trans =
**0.00004** and 44 → 300 m gives **0.00005** — indistinguishable, which is the saturation
showing up in the fragility. So the entire "44 vs 200–300 m" question is worth ~5e-5 in
P_f, in the *conservative* direction (the adopted narrow value gives the higher r_e).

Note the two tanh figures quoted in this note are consistent but not identical: the table
above is evaluated **at the prior means** (tanh(44/38.7) = 0.813), while the run tables
report the **median over the N = 1e5 sampled realizations** (0.835), because λ_out is
stochastic through k_aq, D_aq and k_bl. Neither is a correction of the other; quote the
median when citing a run and the mean-value figure when citing the analytic table.

**Why so small at the governing section.** r_e drives only the uplift/heave gate. At
KP 62.0 the Terzaghi heave threshold is D_bl·γ'_bl/γ_w = 0.45 × 6.9/9.81 ≈ **0.32 m**,
while at the lowest stage where any failure occurs (46.25 m MSL) the transmitted head is
r_e·(h − z_toe) ≈ 0.33 × 1.35 ≈ **0.45 m**. The gate is already open with margin across
the whole failure-relevant stage range, and both piping heads are r_e-independent, so
r_e is effectively **inert** there. This is section-specific: the ADR-0032/close-out
r_e-halved QA member at KP 58.8 produced max ΔP_f = 0.181 precisely because halving r_e
(−50%, far outside the B_f bracket) pushes that section's transmitted head down onto its
0.60 m threshold.

**Consequence for ADR-0025:** the open-vs-blanketed foreland question at KP 62.0 is
bounded at ΔP_f ≤ 2.3e-4 and no longer needs foreshore ground truth to be decision-safe.
The trigger in ADR-0025 "Data that would re-open this item" is retained for completeness
but is now known to be immaterial to the fragility deliverable.

## 7. Source decision: OYO 1998 retained, MLIT recorded as corroboration

Considered and **rejected**: switching `foreshore_width_m` to the MLIT 2008 profile values
on the grounds that they are more recent, more authoritative, and post-remediation.
Reasons, in order of weight:

1. **The MLIT source cannot supply three of the four values.** Its Bfp row clips at
   ~150 m; KP 57.4 / 58.8 / 60.0 all read only "≥148". Switching would *lose* 200 / 325 /
   600 and leave only KP 62.0 readable.
2. **Precision is worse, not better.** OYO gives stated numerals; the MLIT values are a
   raster digitization off a scanned plot (±~5 m). More recent ≠ more precise.
3. **Vintage consistency.** Every other column in the row (`L_m`, `D_aq_m`, `k_aq_mps`,
   `d70_m`, `D_bl_m`, `k_bl_mps`, `gamma_sub_kNm3`) is OYO 1998/1999. B_f additionally
   pairs with `D_fore`/`k_fore`, which are the ADR-0005 proxies copied from the 1998
   `D_bl`/`k_bl`; mixing a 2008 width into that pairing is internally inconsistent.
4. **"Post-remediation" does not apply to this column.** The reach's remediation is
   landside (berms, toe drains; Fukuda types ④/⑤/⑥) and extends `L`, not 高水敷幅. The
   1998 → 2008 comparison at KP 62.0 (44 → ≈34, within digitization error) shows no
   systematic change.
5. **Zero decision-relevance** — §6: ≤ 0.0044 even for B_f → 0.
6. **Cost is the whole campaign.** `geometry.foreshore_width` is inside
   `Config.to_metadata()` and therefore inside `config_hash()`. Changing the CSV changes
   every config hash, and `bayesian_reliability_updating/replay.py::load_phase1_run`
   refuses hash drift ("refusing to replay under drifted assumptions"). That invalidates
   all 8 persisted Phase 1 sweeps, the Phase 2 production posterior, and the Phase 3
   campaign built on them — a full re-run to chase a change measured at ≤ 0.0044.

The MLIT profile is recorded in the provenance as **independent corroboration and
change-detection evidence**, which is the role the evidence actually supports.

## 8. Corrections this forces elsewhere

**Study Area narrative (thesis Chapter 3 and `_thesis_studyarea.tex`).** The engine does
not support the "foreshore-width control on risk" claim as written:

- KP 62.0's r_e is **0.330 — the lowest of the four sections** (57.4: 0.438, 58.8: 0.436,
  60.0: 0.417). It transmits the *least* head to its toe, not "nearly the full river
  head", and it has the *most* foreland attenuation, not the least. What is true is
  narrower: its *tanh credit* is the smallest (0.835 vs 0.97–1.00), worth +5.8% on r_e
  relative to a semi-infinite foreland.
- The measured B_f effect is **largest at KP 60.0 (600 m) and smallest at KP 62.0
  (44 m)** — the inverse of the ordering the narrative implies.
- What actually makes KP 62.0 governing is the **0.45 m blanket**: it sets the uplift/heave
  resistance and the 0.3·D_bl crack term, *and* it shortens λ_in. The thin blanket does
  the work and partially offsets itself through r_e.
- The 1998 `i_v` contrast (KP 62.0 0.97 vs KP 57.4 0.04) is an OYO FE result under a
  *fully blanketed* schematization (ADR-0025 Evidence 4) and is not this engine's r_e
  ordering; it should not be presented as validating a foreshore-width control in this
  model.

**Stale sentence.** `_thesis_studyarea.tex` line 444 and thesis Chapter 3 line 627 both
still read "The exit elevation is taken as the foreshore crest level of
Table~\ref{tab:oyo_inventory}" — superseded by ADR-0021 (surveyed landside toe). The
engine fragment additionally still calls `L` deterministic, superseded by the stochastic-L
decision.

**Minor flag, no action.** The CSV encodes KP 63.4 `foreshore_width_m = 0` ("river-tight",
provenance §3.5); the MLIT profile reads ≈28 m there. KP 63.4 is excluded from the
production population by default, so this is inert — but the §3.5 justification is
contradicted by the second source and is now labelled as such.

## 9. What would re-open this

Nothing in the foreshore-width value itself: it is verified, doubly sourced, correctly
defined, and measured inert. The residual uncertainty ADR-0025 identified — whether the Ac
blanket genuinely covers the 44 m or pinches out — is subsurface, unresolvable from any
imagery, and now **bounded at ΔP_f ≤ 2.3e-4**.

Effort on manual geometry extraction should go to **`L`** instead: ADR-0033 ranks it the
top total-effect input for every QoI (ST_L ≈ 0.49–0.78), the seepage-length study measures
the transient shoulder P_f as 3–4× sensitive to CoV(L), and the provenance concedes L is
"explicit engineering-judgement estimates, not surveyed values of L". B_f is the opposite
on both axes.

## References

- **ADR-0025** (this note's parent; its on-demand sensitivity is closed here),
  **ADR-0006** (tanh correction, Decision 1), **ADR-0005** (foreland proxy),
  **ADR-0028** (raw static head → static branch is r_e-independent),
  **ADR-0021** (surveyed z_toe), **ADR-0033** (GSA: L dominates).
- Companion note `adr0025-kp62-foreland-read.md` (the 様式-3/-4/-5 read this builds on).
- USACE (2000) EM 1110-2-1913 App. B ¶d, ¶h, Eqs. B-7/B-8; TAW (2004) App. I Eq. A.I.9.
- OYO (1999) R057.400 / R058.800 / R060.000 / R062.000 / R062.800, 様式-3 高水敷幅
  annotations; R062.000 様式-5 (高水敷高 45.00 m, base flow 41.60 m).
- MLIT 堤防現況縦断図 `81_十勝川水系十勝川_R_02堤防現況縦断図_007.pdf` row 4)② 高水敷幅
  Bfp(m), 整理番号 8/13; vintage note `tokachi_river_basin/ctll1r0000001cmh.pdf` (平成20年3月).
- PWRI (2014) 河川堤防の浸透に対する照査・設計のポイント (Yabe River 2012, 高水敷 gravel
  connected to As).
- 新潟県 / 宮城県 河川用語集 (高水敷 / 低水路 definitions).
