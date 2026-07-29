# Epistemic bracket synthesis: one ranking, and which brackets cancel

**Status:** Accepted (synthesis note; amends the accepted ADR-0045, ADR-0046 and
ADR-0048 by extending their coverage, and consumes ADR-0047 §4.5). No new numbered
ADR, no `Config` default changed, no production sweep re-run.

**Date:** 2026-07-30
**Driver:** `scripts/epistemic_bracket_synthesis.py`
**Evidence:** `docs/decisions/epistemic-bracket-synthesis.json`
**Tests:** `tests/test_epistemic_bracket_synthesis.py`
**Companion records extended in place:** `adr0045-mp-companion.json`,
`adr0046-ztoe-companion.json`, `adr0048-prior-mean-companion.json`

---

## 1. What this closes

Before this note, the three epistemic-sensitivity companions covered **KP 58.8 and
KP 60.0 only**. ADR-0047's execution log says so explicitly ("ADR-0045/0046/0048
companions checked and NOT re-run — KP 58.8 + KP 60.0 only"), which left **KP 62.0,
the governing section, with no measurement of any of the three** — and KP 62.0 is
where the numbers matter most:

* ADR-0048 calls the `k_aq` prior-mean bracket the largest single epistemic knob
  quantified in the project.
* KP 62.0's transient fragility rose ×8.7 at design HWL under the ADR-0047 L adoption.
* KP 62.0 drives the RQ3 dominance result (BEP 0.500 at +4K) and the RQ4 climate ratio
  (12.7).
* KP 62.0 is the `unreinforced` section — no remediation credit to argue about — so it
  is the one the thesis leans on hardest.

The thesis intends to state that absolute P_f must never be quoted without the `k_aq`
bracket attached. That bracket did not exist where the thesis needs it most. It does now.

All three companions were re-run across **all four** matrix sections, not just the two
new ones: the KP 58.8 / KP 60.0 outputs dated from 2026-07-18/28 and were produced
against pre-campaign parents. The 2026-07-29 production campaign's G1 gate proved the
failure matrices are bit-identical, so their numbers were still valid — but their
recorded provenance predated the campaign, and one coherent companion set carrying
current hashes is worth more than four valid-but-differently-aged ones.

## 2. Method

### 2.1 Baseline gating

Every section's baseline is **re-run fresh from its committed YAML and asserted
bit-identical to its persisted production sweep on the whole failure matrices** — not on
the column means, so a drift that happened to preserve P_f would still fail — before any
number at that section is reported. That single gate covers every arm at that section,
because all arms are compared against those same persisted matrices.

The three companion drivers additionally reconstruct each run's `Config` from the
sidecar's own `config` block and check it against the recorded `config_hash`. This was
**confirmed rather than assumed**: all four matrix sidecars round-trip to their recorded
hash *and* match the on-disk `configs/*.yaml` post-campaign, so the campaign's hash
changes do not break them.

### 2.2 Anchor levels — and a terminology hazard worth naming

The table is quoted at five conditioning levels per section. It deliberately **does not
use the word "shoulder"**, because ADR-0045 and ADR-0048 both quote factors "at the
shoulder" and **mean different stages**:

| Anchor | Definition | Whose "shoulder" |
|---|---|---|
| `lowest_reachable` | lowest level with any transient failure | — |
| `rising_limb` | nearest transient P_f = 2e-3 | **ADR-0045's** |
| `transition_midpoint` | nearest transient P_f = 0.5 | **ADR-0048's** |
| `design_hwl` | nearest the section's design high water | — |
| `grid_top` | last grid level | — |

This is not a guess. ADR-0045's text names P_f ~ 2e-3 for its shoulder; ADR-0048's
published KP 58.8 field-toe "shoulder" ratio of ×0.088 was traced to 41.50 m MSL, where
baseline transient P_f = 0.4915. Quoting "×2.2 at the shoulder" (ADR-0045) beside "×1.99
at the shoulder" (ADR-0048) as if they described the same stage would be wrong by roughly
two orders of magnitude in P_f. A test pins the separation
(`test_the_two_shoulder_conventions_are_kept_apart`).

### 2.3 The comparable magnitude: `span`

Each bracket is collapsed to one number per anchor: `span`, the multiplicative width the
knob spans at that level — the largest transient P_f any of its arms produces divided by
the smallest, baseline included. One number, same units for an epistemic bracket and for
a statistical band, which is what makes the ranking readable. Where an arm drives P_f to
**exactly zero** the span is reported as `unbounded` rather than as a finite number,
because a finite figure there would understate the knob.

### 2.4 The cancellation test

ADR-0048's carried property (c) — that an epistemic bracket which dominates the absolute
probabilities largely cancels in the static-vs-transient ratio — is what licenses the
thesis's *comparative* claims. It was established at two sections where L was **not**
adopted, and it was argued rather than measured.

It is tested here per level with the **ADR-0047 §4.5 paired-bootstrap ratio-of-ratios**:

rho = (P_static / P_transient)_arm ÷ (P_static / P_transient)_baseline

with 2000 bootstrap replicates over the 16 joint pattern counts, the null pinned at
rho = 1.0 exactly, and a level counted `resolved` only when the 95% interval excludes it.
The statistic is **reused, not re-implemented** — the driver imports it from
`scripts/dem_cross_section_study.py`, and a test refuses a second copy
(`test_ratio_kernel_is_the_adr0047_one_not_a_copy`).

The pairing is legitimate: an ADR-0048 scenario moves only a prior *mean*, leaving family,
CoV, name and ordering untouched, so row j is the same LHS stratum in both arms. The two
arms are therefore coupled by common random numbers, which is exactly what makes the
16-cell joint contingency the sufficient statistic for the bootstrap.

**Resolution is not magnitude.** At N = 1e5 the intervals are tight enough that a 2%
departure resolves. Every claim below therefore leads with the departure *factor* and
uses `resolved` only to say whether the departure is real.

### 2.5 Gates

All 19 pass. Four baselines re-run and bit-identical to their persisted sweeps on the
**whole** failure matrices; four `config_hash` values matching both the sidecar and the
on-disk YAML; N = 1e5 everywhere; and the ADR-0028 static/gate separation reconfirmed as a
by-product — `gamma_bl_sub_lower` moves the static branch by **exactly 1.000 at all 98
levels** with a defined ratio, across all four sections.

Re-running the two previously-covered sections was not wasted: the extended records
reproduce the pre-campaign ones **exactly** (max |diff| = 0.0 across every P_f vector at
KP 58.8 and KP 60.0, both ADR-0045 and ADR-0048). That is an independent confirmation of
the campaign's G1 bit-identity gate, and it establishes that the old numbers were valid all
along — only their recorded provenance was stale, which is what this re-run fixes.

The method also reproduces ADR-0047 §4.5 independently, three ways:

| Check | This study | ADR-0047 published |
|---|---|---|
| KP 60.0 L arm, ρ at HWL | **2.226** | 2.226 |
| KP 57.4 L clean arm, max departure | **2.250** | 2.250 |
| KP 62.0 L arm, max departure (my arm runs 40→47, the inverse of theirs) | **2.106** | 1/0.475 = 2.105 |
| KP 62.0 fragility rise from the L adoption at 46.75 m MSL | **×8.67** | ×8.7 |

## 3. The ranking table

Transient P_f **span factor** per bracket per anchor — the multiplicative width the knob
spans at that level. `unbnd` means some arm (or the baseline) sits at exactly zero
failures, so the relative span is unbounded.

**KP 62.0 — the governing section**

| bracket | lowest reachable | rising limb | transition midpoint | **design HWL** | grid top |
|---|---|---|---|---|---|
| `k_aq` prior mean | unbnd | unbnd | **6.65e3** | **unbnd** | 6.07 |
| `z_toe` ±0.3 m | unbnd | 66.9 | 1.43 | **184** | 1.00 |
| L measurement | unbnd | 8.67 | 1.68 | **15** | 1.02 |
| CoV(L) 0.10–0.40 | unbnd | 803 | 1.18 | unbnd | 1.03 |
| `m_p` | 2.00 | 1.60 | 1.01 | **2.80** | 1.00 |
| `gamma_bl_sub` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| *MC CoV (spec §11)* | unbnd | 1.41 | 1.01 | *3.05* | 1.00 |
| *Clopper–Pearson* | 220 | 1.42 | 1.01 | *2.95* | 1.00 |

Baseline transient P_f at those anchors: 1e-5 (1 row) / 1.3e-3 (130) / 0.473 (47270) /
**1.5e-4 (15 rows)** / 0.990 (99011).

**All four sections, at the two anchors that carry the thesis's claims**

| | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| **transition midpoint** | | | | |
| `k_aq` | unbnd | unbnd | 9.99e3 | 6.65e3 |
| L (clean arm only) | 1.39 | 1.82 | 2.05 | 1.68 |
| `z_toe` | 2.02 | 1.79 | 1.68 | 1.43 |
| `m_p` | 1.01 | 1.00 | 1.00 | 1.01 |
| *Clopper–Pearson* | 1.01 | 1.01 | 1.01 | 1.01 |
| **design HWL** | | | | |
| `k_aq` | n/d | unbnd | 9.94e4 | unbnd |
| L | n/d | 2.42 | 2.83 | 15 |
| `z_toe` | n/d | 3.09 | 2.58 | 184 |
| `m_p` | n/d | 1.04 | 1.02 | 2.80 |
| *Clopper–Pearson* | n/d | 1.02 | 1.02 | 2.95 |

`n/d` at KP 57.4's design HWL is **not** a gap in the table: that anchor (39.25 m MSL)
carries **zero transient failures out of 1e5**, so every multiplier there is undefined.
That is a fact about the section, and it corroborates the production campaign's own
observation that KP 57.4 has no failing rows at design HWL.

Two orderings are worth stating plainly:

* **`k_aq` is the largest knob at every section and every anchor** — ADR-0048's headline
  survives extension to the governing section, by three to five orders of magnitude over
  anything else.
* **At KP 62.0's design HWL, `z_toe` (×184) is the second-largest knob, ahead of L
  (×15).** ADR-0046 had never measured KP 62.0. The datum bracket is large there because
  the anchor sits 0.11 m above HWL on 15 failing rows, so a ±0.3 m datum shift moves the
  section across its own threshold. `z_toe` is not the minor knob its two-section record
  suggested.

## 4. ADR-0048's three carried properties, tested at the governing section

### (a) Strong stage dependence — **CONFIRMED**, with one qualification

`k_aq` transient P_f ratios at KP 62.0 collapse toward unity exactly as ADR-0048
describes: `regional_upper` ×1.07e4 → ×357 → ×2.11 → ×1.01 across lowest-reachable →
rising-limb → midpoint → grid-top; `field_toe` 0 → ×0.023 → ×0.396 → ×0.95. Same shape at
KP 57.4.

The qualification: the collapse needs the *arm* to saturate, not just the baseline. At
KP 57.4 the grid stops at 43.25 m MSL, where `field_geomean` still sits at ×0.00137 — a
span of 757 at the top of the grid. KP 62.0 collapses cleanly only because its ADR-0024
hypothetical extension runs to 56.5 m MSL. **Quoting a single "k_aq factor" without the
stage remains meaningless**, and "it collapses at the top" is a property of KP 62.0's
extended grid, not a general one.

### (b) The bracket dwarfs the statistical uncertainty — **CONFIRMED for `k_aq` only; must not be generalised**

For `k_aq` it holds overwhelmingly: ×6.65e3 against a Clopper–Pearson span of 1.01 at the
KP 62.0 midpoint. But the property is about `k_aq`, and it **fails for the smaller
knobs at exactly the stages where P_f is small**:

| | `m_p` span | MC CoV span | CP span |
|---|---|---|---|
| KP 62.0 design HWL | **2.80** | 3.05 | 2.95 |
| KP 62.0 lowest reachable | 2.00 | unbnd | 220 |
| KP 60.0 lowest reachable | 2.50 | 5.51 | 4.56 |
| KP 57.4 rising limb | 1.61 | 1.66 | 1.67 |

At the governing section's design stage the **entire m_p bracket is narrower than the
Clopper–Pearson band around the baseline**. So "epistemic uncertainty dwarfs sampling
noise" is true of `k_aq`, `z_toe` and L, and **false of `m_p`** in the deep tail. The
thesis should attach the `k_aq` bracket to absolute P_f, but must not claim the general
form of this property.

### (c) It largely cancels in the static-vs-transient ratio — **REFUTED**

This is the important one, and it fails — not only at KP 62.0 but at **all four sections,
including the two where ADR-0048 asserted it**. Maximum resolved ratio-of-ratios
departure factor:

| arm | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| `k_aq_field_geomean` | **82.2** | **65.6** | **162.9** | **45.6** |
| `k_aq_field_toe` | 9.31 | 6.96 | 3.40 | 2.24 |
| `k_aq_regional_upper` | 4.74 | 8.36 | 33.35 | 11.73 |
| `z_toe` ±0.3 m | 3.15–4.47 | 3.34–4.79 | 3.48–3.52 | 2.09–2.15 |
| L measurement | 2.25 | 1.82 | 3.22 | **2.11** |
| `gamma_bl_sub_lower` | 1.15 | 1.29 | 1.22 | 1.00 |
| `m_p` | 1.14 | 1.14 | 1.22 | 1.07 |

Every `k_aq` arm resolves away from ρ = 1 at essentially every evaluated level (e.g.
27/27 levels at KP 62.0 for `field_toe`). The departures are **larger than the L
bracket's**, which ADR-0047 §4.5 already established as non-cancelling.

**The mechanism, read from the code rather than fitted afterwards.** ADR-0048's argument
was that "a common shift in the k_aq mean moves both branches together". That accounts for
exactly one of `k_aq`'s three channels:

| channel | where | branches |
|---|---|---|
| `H_c` via `_factor_Fs(d_70, k_aq, L, α)` | `sellmeijer.py` | **both** — common mode |
| `r_e` via the Mazure leakage lengths → uplift/heave gate | ADR-0028 | **transient only** |
| the erosion rate itself, `dl/dt = 89·C_e·(k_aq·max(0, H_erosion − H_eq)/L)^0.81` | `progression.py` | **transient only** |

`k_aq` has **two** transient-only paths where L has one. It could not have cancelled. The
sign test confirms the direction both ways: lowering `k_aq` drops the transient branch far
more than the static one (KP 57.4 midpoint, ×0.022 vs ×0.143), and raising it lifts
transient more (×1.99 vs ×1.16).

**The one knob that does cancel is the one built to.** `m_p` stays within ×1.07–1.22 at
every section, because ADR-0045 §2 deliberately applies it to the single-source `H_c` in
*both* its uses — one model-form belief per realization. That is a pure common-mode knob
by construction, and it is the only one here that behaves as ADR-0048 assumed all of them
would. `gamma_bl_sub` is inert for a different reason (it never touches the static branch
at all).

**A prediction I made and must report as not confirmed.** Before running the numbers I
pre-registered that KP 62.0 would cancel *better* than KP 58.8, because ADR-0025 measured
its heave gate already saturated (so the r_e channel should be inert there). The raw
departures do order that way — ×2.24 (KP 62.0) < ×6.96 (KP 58.8) < ×9.31 (KP 57.4) — but
that ordering is **an artifact of unequal shift size**: an ADR-0048 scenario is an absolute
*target* mean, so `k_aq` moves ×0.17 at KP 57.4 but only ×0.515 at KP 62.0. Normalised per
decade of input movement the ordering largely dissolves:

| arm | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| ρ decades per decade of `k_aq` | 1.12–1.29 | 1.19–1.43 | 1.52–1.84 | 1.07–1.35 |

KP 62.0 is at the low end, consistent with gate saturation but not evidence for it — and
KP 60.0, not KP 57.4, is highest, which the gate argument does not explain. **The honest
statement is that non-cancellation is section-independent at roughly 1.1 to 1.8 decades of
ρ per decade of `k_aq`.** That the figure exceeds 1.0 everywhere is itself the finding: the
ratio does not merely fail to cancel, it *amplifies* — the transient branch is more than an
order of magnitude more `k_aq`-sensitive than the static branch, per decade.

### Consequence for the thesis

ADR-0048's conclusion that "the thesis's comparative claims are robust to this knob while
its absolute probabilities are not" **does not hold** and should be withdrawn. Combined
with ADR-0047 §4.5, the rule that survives is narrower:

> A bracket cancels in the static-vs-transient ratio **only if it is pure common-mode**.
> `m_p` qualifies by construction. `k_aq`, `z_toe` and L each carry a transient-only
> channel and none of them cancels. Cancellation must be measured per knob, never assumed
> from "shared sample, fixed parameter".

The Stage 6.6 bias headlines are therefore conditional on `k_aq` as well as on L — and the
`k_aq` conditionality is the larger of the two.

## 5. Where production sits inside each bracket

In **input** space ADR-0048's characterisation holds at the governing section: production
`k_aq` = 1.0e-3 m/s sits at **55.1%** of the log range spanned by the field geometric mean
(5.94e-5) and the regional upper end (1.0e-2) — mid-range, not at either extreme (KP 57.4
76.5%, KP 58.8 68.6%, KP 60.0 55.1%).

In **P_f** space, which is what gets quoted, the picture is stage-dependent and at the
governing section it inverts:

| KP 62.0 anchor | bracket | production's position | upside if regional-upper is right | downside if the field population is right |
|---|---|---|---|---|
| rising limb | ×0.023 … ×357 | 39.1% | **×357** | ×0.023 |
| transition midpoint | ×3.2e-4 … ×2.11 | 91.5% | ×2.11 | ×3.2e-4 |
| **design HWL** | ×0.067 … ×1.8e3 | **26.5%** | **×1800** | ×0.067 |
| grid top | ×0.167 … ×1.01 | 99.4% | ×1.01 | ×0.167 |

**At design HWL — the stage the thesis defends — production sits at 26.5% of the log-P_f
bracket, not mid-range and certainly not at the conservative end.** If the field
permeability population is right the error runs *conservative*: KP 62.0's design-HWL
transient P_f falls to ×0.067 of the quoted value or below. If the regional upper band is
right it runs *drastically unconservative*: **×1800**. The asymmetry is a saturation
effect — at the midpoint P_f = 0.47 can only double, while at design HWL P_f = 1.5e-4 has
room to explode.

So ADR-0048's warning is confirmed and sharpened at the governing section: reading only the
two field-test scenarios would license the comfortable and wrong conclusion that production
is conservative. At KP 58.8 the same anchor gives 72.6% (upside only ×3.49), so **this is a
KP 62.0-specific hazard**, driven by how close that section's design HWL sits to its own
failure threshold.

## 6. Carried forward — the ADR-0047 records (deliberately not fixed here)

`docs/decisions/adr0047-dem-seepage-length.json` is stale post-adoption: its KP 62.0 block
still names 47.0 m as baseline with a `dem_clean_median` arm. I verified the campaign's
copy at `results/production_campaign/companions/` is **not** a drop-in replacement — it has
the correct post-adoption KP 62.0 block (`baseline_L_m` 40.0, arm `withdrawn_1998`) but is
**missing the entire `datum_check` block**, because the campaign ran only the
fragility-side stages. `datum_check` holds the evidence that validated the DEM extraction
chain before its L was believed. It was not copied over.

**Decision: leave all of it, and hand it forward as one unit.** The reason is that this is
not one stale file but a **matched set from the same pre-adoption run**, all committed
together in `e1e7789`:

| artifact | written | state |
|---|---|---|
| `adr0047-dem-seepage-length.json` | 2026-07-28 19:27 | stale KP 62.0 baseline |
| `docs/figures/adr0047_dem_seepage_length.png` | 2026-07-28 19:39 | rendered from that payload |
| `adr0047-dem-seepage-length-ratio.json` | 2026-07-28 23:44 | also stale (`csv_L_m` 47.0) — **not previously flagged** |

Regenerating the JSON alone would desynchronise it from the figure it depicts, creating a
new inconsistency in place of an old one. `dem_cross_section_study.py all` re-renders that
figure unconditionally, so the correct fix is atomic and belongs to the deferred figure
pass:

```powershell
python scripts/dem_cross_section_study.py all   --overwrite
python scripts/dem_cross_section_study.py ratio --overwrite `
    --out docs/decisions/adr0047-dem-seepage-length-ratio.json
```

The DEM tiles are present on this machine, so both commands are runnable now; this is a
sequencing choice, not a blocked one. Nothing in this synthesis depends on those files
being current: the L bracket here was measured fresh against post-adoption baselines, and
the only value read from the stale record is the DEM-derived `measurements` block, whose
`csv_L_m` field the driver explicitly overrides with the config's live L (pinned by
`test_seepage_length_arms_drop_the_no_op_arm_and_carry_the_withdrawn_value`).

## 7. What changed

Nothing in production. No `Config` default, no physics, no persisted production sweep, no
`configs/*.yaml`, no `data/processed/tokachi_bep_inputs.csv`. All three knobs remain OFF by
default, per decision 3 of the campaign's decisions of record. 28 companion sweeps and 4
in-memory L arms were added under `results/sensitivity/`; the three companion JSONs were
extended in place from two sections to four; this note and its evidence JSON are new.
