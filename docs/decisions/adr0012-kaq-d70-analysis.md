# Analysis: empirical `k_aq`–`d_70` log-correlation from the OYO paired records

Supporting analysis for ADR-0012 (`0012-kaq-d70-log-correlation.md`).
Auditable without rerun. Companion figure:
`../figures/adr0012-kaq-d70-scatter.png`.

> Provenance note: this document records the analysis as performed on
> 2026-07-02 **without repo access**; §0 and §5 flag what could not be
> verified then. §6 (added 2026-07-03) reconciles those flags against the
> actual repository. The analysis content (§§1–4) is unchanged.

## 0. Findability check (stated up front, per task instructions)

Three things the task asked me to locate were **not present** in this environment;
I flag them rather than assume:

- **Repo ADR examples (ADR-0006/0015/0020) and the exact house template — NOT FOUND.**
  I could not read a real ADR from `docs/decisions/`. The draft ADR-0012 therefore
  uses the standard **Status / Context / Decision / Consequences** structure (the
  pattern the task itself hints at) and the filename convention given in the task
  (`0012-<slug>.md`). **This structure must be reconciled against a real repo ADR
  before merge.**
- **Spec §7 as a standalone file — NOT FOUND.** However, the coupling requirement it
  encodes is fully documented in the project methodology chapter (Section
  "Model Applicability at Gravel Grain Sizes" and "Cross-correlation between
  k_aquifer and d_70", incl. the pre-registered *Diagnostic A* and its two outcomes).
  I use that as the authoritative statement of what §7 requires and cite it as such.
- **Config generator / sampling module source — NOT FOUND.** The consumption of
  `rho_log_kaq_d70` (a scalar ρ plus a `correlated`/`two_population` coupling-mode
  flag) is taken from the methodology description, not from reading code. The
  code-scoping note is written at that level and marked accordingly.

One further finding dominates everything below and must be read first:

- **OYO reports no `d_70` on any specimen.** Only d60, d50, d20, d10 are tabulated
  (verified against the 様式-4 soil-test sheets, files R057_400/R058_800/R060_000/
  R062_000.pdf, and the project appendix `tab:app_grainsize`). The correlation named
  `rho_log_kaq_d70` therefore **cannot** be computed on a measured d70. It is
  estimated on the available descriptors that bracket d70, i.e. **d60** (nearest
  single percentile) and **d10** (the Hazen permeability control), exactly as
  Diagnostic A prescribes.

## 1. Data inventory

Source: OYO (1999), 平成10年度 十勝川中流部堤防強化対策検討業務 報告書（調査・解析編),
grain-size logs + density-adjusted constant-head lab permeability, 様式-4 soil-test
sheets. Pairs are formed **per specimen** (same borehole + same depth interval),
which is the only clean pairing available: the *field* permeability tests sit at
7.4–9.5 m depth with no co-located grain-size sample, so they cannot be depth-matched
and are excluded from the correlation (they remain valid for the absolute-magnitude
`k_aq` prior, a separate question).

Valid same-specimen pairs (grain size **and** lab k both present): **8 total, 6
in-scope** (the four config sections KP 57.4/58.8/60.0/62.0); 2 more at KP 63.4
(out of scope, used only for a pooled sensitivity).

| KP | Sample | Gravel % | d60 (mm) | d10 (mm) | k_lab (m/s) | class |
|----|--------|---------:|---------:|---------:|------------:|-------|
| 57.4 | B-2-2 | 38.0 | 1.47 | 0.0057 | 2.69e-5 | gravel ⟨GF⟩ |
| 58.8 | B-4-2 | 53.1 | 7.10 | 0.0152 | 9.16e-6 | gravel ⟨GF⟩ |
| 58.8 | B-4-3 | 68.9 | 11.10 | 0.192 | 2.84e-5 | gravel [G-F] |
| 60.0 | B-6-1 | 4.2 | 0.228 | 0.0053 | 5.59e-4 | **SAND ⟨SF⟩** |
| 60.0 | B-6-2 | 85.3 | 13.20 | 0.530 | 1.83e-4 | gravel (GW) |
| 62.0 | B-9-1 | 43.9 | 3.46 | 0.016 | 1.08e-5 | gravel ⟨GF⟩ |
| 63.4 | B-2-2 | 57.0 | 10.92 | 0.240 | 7.14e-6 | ⟨SG⟩ (o.o.s.) |
| 63.4 | B-3-2 | 39.0 | 1.67 | 0.110 | 1.96e-5 | ⟨SG⟩ (o.o.s.) |

Per-section paired counts: **KP57.4 N=1, KP58.8 N=2, KP60.0 N=2, KP62.0 N=1**.

Exclusions: no numeric outliers dropped; no censored/non-detect values in the paired
set. The KP63.4 field recovery value 4.2e-3 m/s (flagged an outlier elsewhere) is a
*field* test and is already outside the paired set. Units: k in cm/s converted to m/s
(÷100); d in mm. The Pearson r is invariant to unit scaling and to log base, so
cm/s-vs-m/s and log10-vs-ln do not affect any r below (natural log used throughout).

## 2. Statistics (log-transformed variables)

Pearson r on (ln grain-size, ln k); 95% CI via Fisher z; OLS slope of ln k on ln d
(Hazen predicts +2 against d10).

**Pooled, in-scope (N=6):**

| pair | r | r² | p | 95% CI | slope |
|------|----:|----:|----:|--------|------:|
| ln k vs ln d60 | **−0.50** | 0.25 | 0.32 | [−0.93, +0.53] | −0.53 |
| ln k vs ln d10 | **+0.11** | 0.01 | 0.84 | [−0.77, +0.84] | +0.09 |

**Pooled incl. KP63.4 (N=8, sensitivity):** d60 r=−0.51 (p=0.19); d10 r=−0.11
(p=0.80). Adding the two out-of-scope points does not change the picture.

**Per section:** not computable. N=1 at KP57.4 and KP62.0 (no correlation possible);
N=2 at KP58.8 and KP60.0 (any two points are trivially collinear, r=±1 with no
meaning). **A per-section ρ cannot be estimated from this dataset at any section.**
Practical minimum I would want before quoting a per-section ρ is ~8–10 paired
specimens per section; the data provide at most 2.

**Soil-type split (the physically meaningful partition):**
- matrix/sand (G<15%): only **1** specimen (KP60.0 B-6-1) — cannot fit.
- gravel framework (G≥15%, N=5): ln k vs ln d10 **r=+0.76** (r²=0.58, p=0.14,
  slope +0.47); ln k vs ln d60 r=+0.43.

## 3. Interpretation against the pre-registered Diagnostic A

Diagnostic A (methodology §"Cross-correlation") selects:
- **Outcome 1 (Nataf copula, single population, ρ=r):** requires a Hazen-consistent
  slope (within ~2× of 2) **and** r² ≳ 0.5 pooled.
- **Outcome 2 (two-soil model, decoupled, Σ_{k,d}=0):** r² < 0.3 pooled, or bimodal.

The pooled in-scope result gives slope **+0.09** against a Hazen target of **+2**, and
**r²=0.01** (d10) / **0.25** (d60) — **both below 0.3**. Diagnostic A therefore
selects **Outcome 2**. The result is not marginal: the pooled correlation is
statistically indistinguishable from zero (p≥0.32, CI spans zero widely) and, on the
d60 descriptor closest to a nominal d70, is **negative**.

The mechanism is visible in the figure and is a textbook two-population signature.
The single sand-matrix specimen (KP60.0 B-6-1: finest grain, d60=0.228 mm) has the
**highest** measured permeability (5.59e-4 m/s), while the coarse gravels have k one
to two orders lower. This inverts the natural grain-size→k relationship because these
are **reconstituted, density-adjusted** specimens: a clean fine sand repacks to high
k, whereas a reconstituted gravel with its fines redistributed into the voids packs
to low k. Pooling the matrix and framework populations thus yields ≈0/negative r;
**within the gravel framework alone** the correlation is positive and physical
(r=+0.76) but (i) excludes the matrix and (ii) is irrelevant to the coupling the
config controls, because the operative model `d_70` is the *matrix* diameter
(0.26–0.70 mm) while `k_aq` is the *framework* conductivity. They are literally two
different soils occupying two different model components.

## 4. Sanity check (sign and magnitude)

Soil mechanics expects coarser → more permeable, i.e. a **positive** ln k–ln d
correlation (Hazen: k ∝ d10², slope +2). The pooled empirical result **fails this
check**: near-zero on d10 (slope +0.09) and negative on d60. Rather than accept a
counter-intuitive pooled number, the physically correct reading is that the pooled
sample violates the single-population premise — it mixes two soils — which is
precisely the condition Outcome 2 is designed for. The one subset that *does* satisfy
the expected sign, the gravel-only fit (+0.76, slope +0.47), still falls well short
of the Hazen slope, consistent with a reconstituted-specimen dataset that is a weak
guide to in-situ conductivity in the first place.

**Bottom line:** the provisional **ρ = 0.6 is not supported** by the OYO data. It has
the wrong sign relative to the pooled point estimate on the nearest descriptor, and
it fails the pre-registered Diagnostic A test for a single coupled population. The
data support **decoupling** (two-soil model, effective ρ = 0), not a positive Nataf
correlation.

Caveat carried forward: N=6 is small and no correlation here is statistically
significant, so the data cannot *prove* ρ=0 either. The decision rests on the
pre-registered Diagnostic A criterion plus the physical two-soil argument, not on a
significant negative estimate. It should be revisited if matrix-fraction sieve +
permeability pairs are obtained at the governing sections (KP 62.0, KP 63.4).

## 5. What would need to change in code (scoping only — no changes made)

- `rho_log_kaq_d70 = 0.6  # PROVISIONAL` in every config header is retired. Under
  Outcome 2 the sampler runs in **`two_population`** coupling mode with the log-space
  covariance term **Σ_{k,d}=0** (equivalently ρ=0.0); `k_aq` and `d_70` are drawn
  from their own marginals, with `d_70` (matrix) feeding the Sellmeijer resistance
  factors and `k_aq` (framework) feeding the seepage/progression path.
- If the sampler currently reads `rho_log_kaq_d70` as a scalar and always applies a
  Nataf link, the change is: honour the `two_population` flag and skip the Nataf
  coupling (or apply the Nataf with ρ=0, numerically identical). No per-section value
  is needed — **the data cannot support per-section ρ**, so a single mode flag
  applied to all four sections is correct and sufficient. No new per-section config
  field is required.
- Config headers to edit: the four section configs (KP57.4/58.8/60.0/62.0). Replace
  the provisional scalar with the mode flag `coupling_mode = two_population` and
  `rho_log_kaq_d70 = 0.0` (kept only for schema compatibility / audit trail).
- Any sweep already run under ρ=0.6 stays marked **provisional** in its metadata
  until this ADR is accepted (per existing project convention); it is not
  retroactively relabelled by this analysis.

## 6. Repo reconciliation (added 2026-07-03, with repo access)

The §0 findability flags and the §5 inference-level scoping, resolved against
the actual repository:

- **House ADR format:** the ADR was reconciled to the `docs/decisions/` house
  style (`# ADR-0012: …` heading, plain `Date:`/`Status:` lines,
  Context/Decision/Consequences/References sections) and accepted 2026-07-03.
- **"Spec §7" exists:** it is `docs/architecture.md` §7, and — materially —
  it pre-registers the exact fallback this analysis selects ("a two-population
  soil model … replaces the single correlated population"), restated in §13.
  Outcome 2 is therefore the spec's own branch, not a deviation.
- **Sampler (corrects the §5 conditional):** `sampling.sample_theta` already
  implements the `two_population` mode — the Gaussian-copula step is one
  guarded block that the mode skips — reachable from config
  (`CorrelationSpecs.coupling`, field name `coupling`, not `coupling_mode`),
  threaded by `run.py`, and covered by
  `test_two_population_fallback_decouples_kaq_and_d70`. **Zero sampler
  changes were needed.** The "or apply the Nataf with ρ=0, numerically
  identical" clause was verified empirically: bit-identical theta matrices at
  N = 50,000 (production marginals/bounds, seed 20260626); in
  `two_population` mode ρ is recorded but never imposed
  (`metadata['rho_imposed'] = False`).
- **Configs are generated, not hand-edited:** the edit lands in
  `scripts/generate_configs.py` (retiring `PROVISIONAL_RHO_LOG = 0.6`), and
  the generated configs — 16 at analysis time; 8 after ADR-0023 dropped the
  redundant +4K set — are regenerated from it. The drift guard
  (`tests/test_configs.py`) pins `coupling: two_population` and ρ = 0.0.
- **Provisional-run marking existed as anticipated:** every run since
  2026-07-03 carried `correlation_rho_k_d70_status:
  provisional_pending_adr_0012` in its metadata; the marker is retired with
  the wiring of this ADR. No production sweep ran under ρ = 0.6.
