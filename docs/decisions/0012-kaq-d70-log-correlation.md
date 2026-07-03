# ADR-0012: Empirical k_aq–d_70 Coupling — Two-Population Decoupling (Effective ρ = 0), Not a Nataf Correlation

Date: 2026-07-02 (analysis); Accepted 2026-07-03
Status: Accepted

Supporting analysis: `adr0012-kaq-d70-analysis.md` (companion provenance
document); figure `../figures/adr0012-kaq-d70-scatter.png`.

## Context

Spec §7 makes the coupling of aquifer permeability `k_aq` and representative
grain size `d_70` **mandatory by default**: the two must not be sampled
independently, because an incoherent high-`k_aq` / low-`d_70` draw
simultaneously inflates progression velocity and lowers the entrainment
threshold, overstating prior transient fragility (spec §12, Failure Mode 7).
Spec §7 and §13 also pre-register the escape branch this ADR exercises: "if
those records show the matrix grain size and bulk conductivity to be
statistically decoupled, a two-population soil model — in which the erodible
matrix is treated separately from the armouring gravel framework — replaces
the single correlated population." The thesis methodology encodes the same
rule as *Diagnostic A*, with pre-registered outcomes.

The coupling coefficient `rho_log_kaq_d70` has carried a **provisional value
of 0.6** in every generated config (`scripts/generate_configs.py`
`PROVISIONAL_RHO_LOG`), and since 2026-07-03 every run's metadata has carried
the marker `correlation_rho_k_d70_status: provisional_pending_adr_0012` so no
provisional-ρ result could silently feed Phase 2. No production sweep has run
under the provisional value. This ADR — the number reserved for the empirical
ρ since the M2 build — replaces the guess with the empirical result and
resolves the open two-population question (single pooled ρ vs. per-section
vs. fallback).

Two facts constrain what is possible:

1. **OYO reports no `d_70`.** Only d60/d50/d20/d10 exist (verified against
   the 様式-4 sheets). The correlation is therefore estimated on d60 (nearest
   percentile) and d10 (the Hazen control), per Diagnostic A.
2. **Paired records are sparse.** Only same-specimen (grain-size +
   lab-permeability) pairs are valid; field permeabilities have no
   depth-matched grain size. This yields **8 pairs total, 6 in-scope**
   (KP 57.4 N=1, 58.8 N=2, 60.0 N=2, 62.0 N=1).

Diagnostic A pre-registers the decision rule: a Hazen-consistent slope
(within ~2× of 2) with pooled r² ≳ 0.5 selects a single-population Nataf
copula (ρ = r); r² < 0.3 or a bimodal structure selects the two-soil model
(decoupled, Σ_{k,d} = 0).

## Decision

**Adopt the two-soil model (Diagnostic A, Outcome 2) — the spec §7/§13
two-population fallback. Set the coupling mode to `two_population` with
effective ρ = 0 (Σ_{k,d} = 0). Retire the provisional 0.6.** A single mode
flag applies to all four sections; **no per-section ρ is adopted**, because
the data cannot support one.

Supporting statistics (log variables, natural log; details in the companion
analysis):

- Pooled in-scope (N=6): ln k vs ln d60 **r = −0.50** (r² = 0.25, p = 0.32);
  ln k vs ln d10 **r = +0.11** (r² = 0.01, p = 0.84), OLS slope **+0.09**
  against a Hazen target of **+2**. Both r² are below the 0.3 threshold; the
  pooled correlation is statistically indistinguishable from zero and, on
  d60, negative.
- The single sand-matrix specimen (KP 60.0 B-6-1) has the finest grain yet
  the highest permeability — the reconstituted-specimen inversion that marks
  two mixed populations. The gravel-only subset alone is positive (r = +0.76)
  but excludes the matrix fraction and is not the population the model's
  `d_70` represents.

Rationale: the operative model `d_70` is the sand-**matrix** diameter that
governs the Sellmeijer resistance factors, while `k_aq` is the
gravel-**framework** conductivity that governs the seepage rate and Pol
progression velocity. These are physically distinct soils in distinct model
components; the data show they do not co-vary as one population. Decoupling
(each parameter governing its own physics, drawn from its own marginal) is
therefore both the empirically indicated and the physically correct
treatment. It is **not** the naive independent sampling that Failure Mode 7
warns against, because under the two-soil model the two draws are not two
conflicting descriptions of one soil.

**Two-population question — resolved:** neither per-section nor per-soil-unit
correlations are estimable (max N per section = 2; matrix population N = 1).
The resolution is not "pooled ρ" but "no coupling correlation": the
meaningful partition is matrix vs. framework, and the response to it is the
two-soil decoupling above. There is consequently no fallback-ρ rule to
define, because no section receives a nonzero ρ.

## Code scoping (verified against the repo, 2026-07-03)

The original analysis was written without repo access; its code-scoping was
inference. Verified against the actual source before wiring:

- **The sampler needs zero changes.** `sampling.sample_theta` already
  implements the `two_population` coupling mode: the Gaussian-copula step is
  one guarded block (`if coupling == "correlated": ...`) that the mode skips
  entirely. The mode is reachable from config (`CorrelationSpecs.coupling`),
  threaded by `run.py`, and covered by an existing test
  (`test_two_population_fallback_decouples_kaq_and_d70`).
- **`two_population` and a Nataf link at ρ = 0 are numerically identical in
  this implementation** — verified empirically, not just algebraically: at
  N = 50,000 with the production KP 62.0 marginals, bounds and seed
  20260626, the two modes produce bit-identical theta matrices (the LHS
  design is drawn before the coupling step, and `0·z_kaq + √1·z_d70` is the
  identity). The only differences are provenance: `metadata['coupling']` and
  `metadata['rho_imposed']` (False in `two_population` mode), and hence the
  config hash.
- **ρ is recorded but never imposed in `two_population` mode** (and not
  range-validated by the sampler in that mode; the config layer still
  validates it into the open (−1, 1)). The configs therefore carry
  `rho_log_kaq_d70: 0.0` so the recorded value reads truthfully.
- In `two_population` mode **both** `k_aq` and `d_70` retain perfect
  one-point-per-stratum LHS coverage; the k_aq-anchor stratification question
  the M2 build flagged for this ADR is moot under decoupling (it becomes
  relevant only if a correlated mode is ever reinstated).

## Consequences

- **Configs/generator:** `scripts/generate_configs.py` retires
  `PROVISIONAL_RHO_LOG = 0.6` and emits, in every generated config's
  `correlation:` block, `coupling: "two_population"` and
  `rho_log_kaq_d70: 0.0` (the field is required by `CorrelationSpecs`;
  0.0 is retained for schema/audit only and is not imposed). ρ leaves the
  generator's PROVISIONAL list (the seed stays provisional). Configs are
  regenerated, never hand-edited; the drift guard (`tests/test_configs.py`)
  pins the new coupling mode and ρ value so the decision cannot silently
  regress. No per-section field is added.
- **Sampler:** unchanged (see Code scoping). `d_70` → Sellmeijer resistance
  factors, `k_aq` → seepage/progression, as separate marginals.
- **Run metadata:** the `correlation_rho_k_d70_status:
  provisional_pending_adr_0012` marker in `run.py` is retired in favour of a
  status citing this ADR; `metadata['sampling']` already records `coupling`
  and `rho_imposed: False` per draw.
- **Prior fragility:** the decoupling removes the physically incompatible
  high-k/low-d70 tail that ρ = 0.6 partially suppressed; the change to the
  `C_e · k_aq` hand-off tail should be quantified in the first
  post-acceptance sweep.
- **Runs predating this ADR:** any run executed under ρ = 0.6 carries the
  provisional marker in its metadata and is not retroactively re-blessed by
  this record. (No production sweep was run under the provisional value.)
- **Auditability / provenance:** OYO (1999) report, 様式-4 soil-test sheets
  (files R057_400/R058_800/R060_000/R062_000.pdf) and appendix
  `tab:app_grainsize` / `tab:app_lab_perm`; N = 6 in-scope same-specimen
  pairs; no `d_70` in source (d60/d10 proxies used); computed 2026-07-02.
- **Revisit trigger:** obtain matrix-fraction sieve + permeability pairs at
  the governing sections (KP 62.0, KP 63.4). If a Hazen-consistent single
  population is ever demonstrated there, re-open under Outcome 1. Until then
  the two-soil decoupling stands.

## Open items explicitly NOT decided here

- Absolute-magnitude `k_aq` prior (field-vs-lab anchor) — separate ADR.
- The `d_70` matrix-vs-bulk interpretation itself — both interpretations
  remain co-primary runs (spec §7/§13); this ADR only concerns their
  coupling.

## References

- Spec §7 (mandatory coupling and the two-population fallback), §12 (Failure
  Modes 5 and 7), §13 (single decisions: coupling row).
- Thesis methodology, "Cross-correlation between k_aquifer and d_70"
  (Diagnostic A, pre-registered outcomes) and "Model Applicability at Gravel
  Grain Sizes".
- `adr0012-kaq-d70-analysis.md` (companion analysis, data table, statistics,
  sanity checks); `docs/figures/adr0012-kaq-d70-scatter.png`.
- `bep_reliability_engine/sampling.py` (`sample_theta`, coupling modes),
  `bep_reliability_engine/config.py` (`CorrelationSpecs`),
  `scripts/generate_configs.py`, `tests/test_sampling.py`
  (`test_two_population_fallback_decouples_kaq_and_d70`).
- OYO (1999), 平成10年度 十勝川中流部堤防強化対策検討業務 報告書（調査・解析編）, 様式-4.
