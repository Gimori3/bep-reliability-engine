# Hinterland L₃ Resolution — Landside Boundary Findings for r_e / ADR-0006

Date: 2026-07-05
Status: Site-data findings for the ADR-0006 r_e resolution (folded into the
ADR-0006 amendment of 2026-07-05). Baseline decision recorded here; two
sections (KP 57.4, KP 62.0) carry a named, bounded conservatism. Primary
source: Hokkaido Development Bureau (帯広開発建設部) official facility
register giving KP chainages for every gate/bridge on the Tokachi right bank
(帯広市 side), reach KP 53–66, mirrored from info-dam.hdb.hkd.mlit.go.jp.
This supersedes the earlier national-river-dataset and plan-view estimates
(which mis-scaled distances and mis-oriented the bank); the chainage register
is chainage-native and matches the model's own coordinate system.

> Provenance note: §§1–3 record the owner's findings as delivered on
> 2026-07-05, computed against the **pre-correction D_bl leakage lengths**
> (λ_in = 181/179/120/39 m). §4 (repo reconciliation) restates the
> thresholds with the corrected-D_bl λ_in (102/117/87/39 m); **every verdict
> is threshold-insensitive and unchanged**.

## 1. Purpose

ADR-0006 (amended) resolved that the r_e ratio form is the exact USACE Case
7a / TAW Model 4A solution, that L/λ_in is NOT the validity ratio (category
error), and that the one genuinely open landside item was the hinterland
extent L₃: the engine assumes the landside hinterland semi-infinite
(x₃ = λ_in, matching Pol Eq. 7.13's "infinitely long polder blanket"), which
holds only if the confining blanket continues uninterrupted for ≥ 3·λ_in
landward of the toe with no aquifer-daylighting boundary. This note records
what the official register shows, per section.

## 2. Right-bank (帯広市) facility register, KP 53–66

| KP | Facility | Type |
|----|----------|------|
| 56.6 | 十勝大橋 | bridge |
| 57.3 | 木賊原樋門 | sluice gate |
| 60.8 | 平原大橋 | bridge |
| 61.7 | 伏古樋門 (伏古川) | sluice gate |
| 62.0 | 西士狩樋門 | sluice gate |
| 64.7 | 西帯広樋門 | sluice gate |
| 65.3 | 西帯広第2樋門 | sluice gate |

No registered structure exists between 57.3 and 60.8, or between 62.0 and
64.7.

## 3. Per-section findings (as delivered; pre-correction thresholds)

| KP | λ_in (m) | 3·λ_in (m) | Nearest registered gate | Distance | Verdict | Direction if the boundary daylights the aquifer |
|----|---------:|-----------:|-------------------------|---------:|---------|--------------------------------------------------|
| 57.4 | 181 | ~543 | 木賊原樋門 @ KP 57.3 | ~100 m | VIOLATED, inside 1λ | Open exit → lowers r_e → engine CONSERVATIVE |
| 58.8 | 179 | ~537 | 木賊原樋門 @ 57.3 (1.5 km) | ≥ 1,500 m | HOLDS | n/a |
| 60.0 | 120 | ~360 | nearest gate ≥ 0.8 km (平原大橋 @ 60.8 is a bridge, not a boundary) | ≥ 800 m | HOLDS | n/a |
| 62.0 | 39 | ~117 | 西士狩樋門 @ KP 62.0 (+ 伏古樋門 @ 61.7, ~300 m) | ~0 m | VIOLATED | Open exit → lowers r_e → engine CONSERVATIVE |

Key conclusions:

1. **Nothing found makes the engine under-conservative at any section.**
   Both confirmed violations (KP 57.4, KP 62.0) are open exits
   (through-levee sluice gates draining landside channels), so the
   semi-infinite assumption OVER-estimates r_e there: the engine over-states
   driving head and failure probability. Conservative, not unsafe, at both.
2. **KP 62.0 hinterland is VIOLATED** (revised from the earlier "holds").
   The official register surfaced 西士狩樋門 sitting essentially AT KP 62.0,
   missed in the plan-view read. Against KP 62.0's small threshold, a gate at
   ~0 m is a clear violation. NOTE: KP 62.0 is the governing section and now
   carries TWO stacked boundary simplifications — the possibly-unconfined
   foreland (raises riverside head; ADR-0025) and this open-exit hinterland
   (semi-infinite over-states it). They push r_e in opposite directions;
   KP 62.0's r_e is bracketed by two defensible-but-unmeasured boundary
   conditions and should be described as such in the thesis.
3. **KP 58.8 and KP 60.0 are genuinely clean** (medium-high confidence):
   nearest registered gate ≥ 1.5 km and ≥ 0.8 km respectively, both well past
   their thresholds. This corrects the earlier plan-view read that wrongly
   flagged 58.8 as highest priority.

## Baseline decision and recommended treatment

- BASELINE: retain the semi-infinite hinterland assumption (x₃ = λ_in) for
  all four sections, matching Pol Eq. 7.13. No r_e physics change for the
  baseline; the violations are conservative, so the baseline is safe.
- DOCUMENT the KP 57.4 (木賊原樋門, ~100 m) and KP 62.0 (西士狩樋門, ~0 m)
  open-exit boundaries as known, bounded conservatisms: the
  finite-hinterland correction x₃ = λ_in·tanh(L₃/λ_in) would LOWER r_e and
  LOWER P_f at both, so the baseline over-states failure probability there.
- SENSITIVITY (data-gated, optional): a finite-hinterland run at KP 57.4 and
  KP 62.0 to quantify the conservatism, IF the channel-bed elevations
  confirm the gates daylight the aquifer (see residual item). Not a baseline
  blocker.

## Residual uncertainty — the one remaining data item

The register confirms a gate EXISTS at each chainage but not the channel-bed
depth behind it, i.e. whether the landside drainage cuts down to the confined
Ag aquifer or sits shallow in the Bc fill / Ac blanket. The finite-hinterland
correction only applies if the boundary genuinely daylights the aquifer; a
shallow O&M ditch leaves the confined condition (and semi-infinite) intact.
So the two VIOLATED verdicts are "violated IF the channel cuts to the
aquifer." The definitive resolution is the channel-bed elevation at 西士狩樋門
(and 木賊原樋門) from 帯広開発建設部. Either way the baseline is protected:
shallow → semi-infinite holds, no change; deep → correction lowers r_e,
engine was conservative. No reading makes the engine under-conservative.

## Explicitly NOT part of r_e (carry separately in the thesis)

The through-levee box-culvert gates at KP 57.4 (木賊原樋門) and KP 62.0
(西士狩樋門, 伏古樋門) are also a distinct BEP mechanism: preferential
seepage along the structure–soil interface. This is a separate thesis
limitation, NOT an r_e / aquifer-boundary term, and must not be folded into
the response factor. Its presence at the governing section (KP 62.0) is
worth an explicit sentence.

## 4. Repo reconciliation (2026-07-05): corrected-D_bl thresholds

The §3 λ_in values predate the D_bl correction (provenance §3.8). With the
current CSV (D_bl = 0.80/0.85/0.85/0.45 m), λ_in = 102/117/87/39 m and the
semi-infinite thresholds shrink to 3·λ_in ≈ **307/350/262/116 m**:

| KP | λ_in corrected (m) | 3·λ_in (m) | Distance to boundary | Verdict (unchanged) |
|----|-------------------:|-----------:|---------------------:|---------------------|
| 57.4 | 102 | 307 | ~100 m (≈ 1·λ_in) | violated — conservative |
| 58.8 | 117 | 350 | ≥ 1,500 m | holds |
| 60.0 | 87 | 262 | ≥ 800 m | holds |
| 62.0 | 39 | 116 | ~0 m | violated — conservative |

The corrected thresholds make the two clean sections cleaner (their margins
grow ~1.5–2×) and leave both violations violations. The engine's
`metadata['leakage_geometry']` block auto-generates the per-run λ_in medians
and 3·λ_in thresholds, so future re-checks read them from the run record
rather than recomputing by hand.
