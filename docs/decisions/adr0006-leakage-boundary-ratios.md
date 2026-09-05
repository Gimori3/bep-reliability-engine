# Analysis: leakage lengths and seepage boundary ratios for the r_e validity question

Supporting analysis for the ADR-0006 resolution (the r_e / Mazure
schematization question; input to the Pol consultation). Companion to the
2026-07-04 r_e source-provenance report.

> Provenance note: §§1–4 below record the author's analysis as delivered on
> 2026-07-04, authored **without repo access**; its own caveats 1–4 flag the
> unverified points. §5 (added 2026-07-04, with repo access) reconciles the
> numbers against the current geotech CSV and the engine's naming convention
> — **the §1–4 leakage lengths for KP 57.4/58.8/60.0 use pre-correction D_bl
> values and are superseded by §5.1**; the structural findings (which lengths
> exist, which are missing, which ratios govern) are unaffected.

---

## 1. Inputs and leakage lengths (as delivered)

All leakage lengths use λ = √(k_aq·D_aq·D_bl/k_bl); the computed λ is
strictly the **landside/hinterland** value (it uses the landside D_bl), with
λ_riverside = λ_landside assumed absent separate foreshore-blanket data — a
flagged assumption, not a measurement.

| KP | k_aq (m/s) | D_aq (m) | D_bl (m) | k_bl (m/s) | λ (m) |
|----|-----------:|---------:|---------:|-----------:|------:|
| 57.4 | 3.0e-3 | 7 | 2.5 | 1.6e-6 | **181** |
| 58.8 | 2.0e-3 | 8 | 2.0 | 1.0e-6 | **179** |
| 60.0 | 1.0e-3 | 9 | 1.6 | 1.0e-6 | **120** |
| 62.0 | 1.0e-3 | 10 | **0.45** | 3.0e-6 | **39** |

With L = the under-levee base width (TAW L₂ = 33 / 35 / 34.8 / 47 m):
L/λ = 0.18 / 0.20 / 0.29 / **1.21**. The KP 62.0 value changed with the D_bl
correction (2.0 → 0.45 m: λ 82 → 39 m, L/λ 0.58 → 1.21); any prior r_e
baseline built on L/λ ≈ 0.58 at KP 62.0 is stale.

## 2. Foreland and hinterland extents, kept strictly distinct from L

**Foreland (riverside toe → open channel), the analysis's "L_in".** This is
the foreshore width, a *measured* OYO quantity, physically distinct from L:
200 / 325 / 600 / 44 m at KP 57.4 / 58.8 / 60.0 / 62.0 (OYO 様式-3/-5).

Physical caveat: the foreshore blanket is not continuous. At **KP 62.0** the
Ac is thin and mapped only in the central-to-landside zone, so the 44 m
foreshore is effectively **unconfined** — the river recharges the aquifer
directly across it and the aquifer head at the riverside toe approaches the
full river head. This is more severe than the bare extent/λ ratio implies.
The wide-foreshore sections more plausibly retain partial foreshore blanket,
but this is not confirmed in the dataset.

**Hinterland (landside toe → next polder hydraulic boundary), the analysis's
"L_out".** **Not in the OYO dataset** — the borehole transects do not reach a
landside drainage/blanket-extent boundary. From site knowledge: the
hinterland is the urban Obihiro plain, the confining Ac continues landward
under the city, and no drainage cut is documented at the toe, so the
hinterland is treated as **effectively semi-infinite (extent ≥ 3λ)** — the
standard assumption when no boundary is found within a few λ. The weak point
is wherever "semi-infinite" demands several hundred metres of uninterrupted
blanketed hinterland in an urban area that may carry drainage ditches or
sluice-fed channels (伏古川 drainage, the 樋門 through-levee gates) within
that distance. If such a boundary sits at ~1λ, the hinterland contribution is
materially truncated. **This is the single input most worth pinning against a
drainage-network/site map before finalizing r_e.**

## 3. Governing ratios (as delivered, uniform-λ assumption)

| KP | L/λ (structure) | foreland extent/λ | hinterland extent/λ |
|----|----------------:|------------------:|--------------------:|
| 57.4 | 0.18 | **1.10** | ≥ 3 (assumed semi-infinite) |
| 58.8 | 0.20 | **1.82** | ≥ 3 (assumed) |
| 60.0 | 0.29 | **5.00** | ≥ 3 (assumed) |
| 62.0 | 1.21 | **1.14** (→ 0 if foreland unconfined) | ≥ 3 (assumed) |

## 4. Caveats carried by the original analysis

1. TAW 2004 (Model 4A) / USACE 2000 (Case 7) were not available to it; the
   ratios above are the model-agnostic dimensionless inputs those
   formulations consume, but the exact hyperbolic arrangement was unverified.
2. λ_riverside = λ_landside is an assumption; a thinner or absent foreshore
   blanket lengthens λ_riverside (or opens the entry) — directionally worse,
   most relevant at KP 62.0.
3. The hinterland extent is inferred, not measured; a landside ditch/canal
   within ~1–2λ would truncate it. Priority item to confirm against a
   drainage map.
4. The subscripts must be reconciled with the config/spec before wiring —
   done in §5.2 below.

---

## 5. Repo reconciliation (added 2026-07-04, with repo access)

### 5.1 Corrected leakage lengths and ratios (current geotech CSV)

The §1 table uses **pre-correction D_bl** at KP 57.4/58.8/60.0 (2.5/2.0/1.6 m
vs the corrected CSV 0.80/0.85/0.85 m — commit d72803b). With the current
`data/processed/tokachi_bep_inputs.csv` prior means:

| KP | D_bl (m) | λ (m) | L/λ | foreland extent/λ | "semi-infinite" hinterland needs ≥ 3λ (m) |
|----|---------:|------:|----:|------------------:|-------------------------------------------:|
| 57.4 | 0.80 | **102** | 0.32 | **1.95** | ≥ 308 |
| 58.8 | 0.85 | **117** | 0.30 | **2.79** | ≥ 350 |
| 60.0 | 0.85 | **87** | 0.40 | **6.86** | ≥ 262 |
| 62.0 | 0.45 | **39** | 1.21 | **1.14** (→ 0 if unconfined) | ≥ 116 |

(These match the engine's own per-realization medians recorded by the wired
ADR-0006 monitor: median L/λ_in 0.32/0.30/0.40/1.23.) Consequences of the
correction: the foreland ratios roughly double at the first three sections —
their tanh factors are 0.96/0.99/1.00, i.e. the foreland is effectively
semi-infinite there and the finite-width correction only bites at KP 62.0
(tanh(1.14) = 0.81, a ~19% reduction of λ_out) — and the demanded
"semi-infinite" hinterland shrinks to ~260–350 m at the first three sections
(§2's several-hundred-metre concern is softened but not removed).

### 5.2 Subscript reconciliation (binding for any wiring)

The original analysis uses "L_in" for the **foreland** (riverside) extent and
"L_out" for the **hinterland** — the **inverse** of the repo convention,
where `λ_in` is the hinterland/landside (exit) leakage length and `λ_out`
the riverside/foreland (entry) one (ADR-0005/0006; `hydraulics.py`). To kill
the ambiguity, any wiring must avoid bare L_in/L_out entirely:

| Quantity | This analysis | Repo pairing | Engine status |
|---|---|---|---|
| Foreland extent (riverside toe → open water) | "L_in" | pairs with **λ_out**; IS `geometry.foreshore_width` (B_f) | **present** — already applied in-model via λ_out,eff = λ_out·tanh(B_f/λ_out) |
| Hinterland extent (landside toe → next polder boundary) | "L_out" | pairs with **λ_in**; proposed name `hinterland_extent_m` | **absent** — no config/CSV field; λ_in is computed bare (semi-infinite) |
| Levee base width | L (TAW L₂) | `geometry.L` | present; enters r_e linearly, never inside a tanh |

### 5.3 Engine mapping of the remaining caveats

- The uniform-λ assumption (§4.2) **is** the engine's ADR-0005 proxy
  (`D_fore = D_bl`, `k_fore = k_bl` in the generated configs), so it is
  already a documented modeling assumption — now load-bearing at KP 62.0,
  where the §2 unconfined-foreland caveat applies: with the proxy,
  r_e ≈ 0.33 at the prior means; with an open foreland (λ_out,eff → 0),
  r_e = λ_in/(L + λ_in) ≈ 0.45 — ~37% higher driving head at the governing
  section. This is a foreland-characterization question for Pol/site data,
  not a formula question.
- The hinterland extent (§2) was the one genuinely missing input; it has
  since been resolved from site data — see §6.

## 6. Hinterland extents resolved (2026-07-05, HDB facility register)

The §2 open item is closed by the author's follow-up analysis
(`adr0006-hinterland-l3-resolution.md`; Hokkaido Development Bureau
chainage-native facility register, right bank KP 53–66), read against the
§5.1 corrected thresholds (3·λ_in ≈ 307/350/262/116 m):

- **KP 57.4: VIOLATED** — 木賊原樋門 (sluice gate) at KP 57.3, ~100 m from
  the section (inside ~1·λ_in). Open exit → the semi-infinite assumption
  over-states r_e → engine **conservative** there.
- **KP 58.8: HOLDS** — nearest registered gate ≥ 1.5 km (≫ 350 m).
- **KP 60.0: HOLDS** — nearest gate ≥ 0.8 km (平原大橋 at 60.8 is a bridge,
  not a hydraulic boundary).
- **KP 62.0: VIOLATED** — 西士狩樋門 essentially AT KP 62.0 (plus 伏古樋門 at
  61.7). Open exit → **conservative**. This revises §2's expectation and the
  earlier plan-view read; note KP 62.0 now carries two opposing boundary
  simplifications (this conservative hinterland one, and the potentially
  non-conservative foreland one of ADR-0025).

**Net: no reading makes the engine under-conservative on the landside.** The
baseline retains semi-infinite x₃ = λ_in at all four sections; the two
violations are documented, bounded conservatisms. Residual (data-gated,
optional): channel-bed elevations at the two gates decide whether they
daylight the aquifer — shallow ditches leave the confined condition intact;
deep cuts would justify a finite-hinterland sensitivity that only lowers
P_f. Not a baseline blocker.
