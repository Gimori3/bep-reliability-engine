# ADR-0033: Variance-Based Global Sensitivity Analysis of the Phase 1 Engine (Stage 6.5)

Date: 2026-07-12

## Status
Accepted

---

## Context

The Phase 1 engine produces fragility curves from an eight-dimensional
stochastic input space (the seven-dimensional θ vector of ADR-0001 plus the
independently sampled stochastic seepage length L, `seepage_length_cov = 0.2`
in every generated config), but nothing in the repository quantifies *which*
inputs drive the failure probabilities, *how much* of the static–transient
bias is attributable to which parameter, or *how strongly* the multiplicative
C_e×k_aq interaction (spec §12 fm7, empirically implicated by ADR-0029/0031)
shows up as genuine interaction variance rather than main effects. Stage 6.5
adds a global sensitivity analysis (GSA), theoretically grounded in the
variance-based framework of Saltelli, Tarantola et al., *Global Sensitivity
Analysis: The Primer* (Wiley 2008; `docs/references/saltelli2007.pdf`):
first-order Sobol' indices S_i (the Factor Prioritization setting, Primer
§1.2.9/§4.3) and total-effect indices ST_i (the Factor Fixing setting, Primer
§1.2.13/§4.5), with the ST_i − S_i gap as the interaction diagnostic
(Primer p. 166–167).

The GSA **wraps the engine and does not modify it**: the 7D vector, the
ADR-0012 coupling resolution, the ADR-0027/0028 head separation, and the
shared-sample contract (ADR-0002) are all fixed inputs to this analysis.
Four methodological forks have no default-correct answer and are resolved
here explicitly.

---

## Decision

### 1. Scalar quantities of interest (QoIs)

Sobol' analysis needs a scalar output per input draw. Four QoIs are adopted,
all computed in one engine pass per conditioning level h_i from the same
sample (the shared-sample contract extended to the GSA):

| QoI | Definition | Type | Role |
|---|---|---|---|
| Y1 | 1{Z_transient ≤ 0} at h_i | binary | **primary** — decomposes Var = P_f(1−P_f) of the transient deliverable |
| Y2 | 1{Z_static ≤ 0} at h_i | binary | static comparator; bias attribution by contrast with Y1 |
| Y3 | l_e,final / L at h_i | continuous on [0, 1] | progression-dynamics measure; retains signal below the failure threshold |
| Y4 | Z_static = H_c − (h_i − z_toe) | continuous | pure Sellmeijer resistance GSA; **level-independent** up to an additive constant, so one analysis serves all levels |

Levels: per section, four conditioning levels spanning shoulder → design HWL
→ transition → upper bulk, read off the section's own production fragility
curve (KP58.8: 40.25 / 41.00 / 41.50 / 42.50 m MSL, transient P_f ≈ 0.025 /
0.26 / 0.49 / 0.81; KP60.0: 42.00 / 42.75 / 43.25 / 44.25, P_f ≈ 0.049 /
0.31 / 0.53 / 0.82).

**Rejected QoIs.** *Median time-to-breach*: breach time is defined only on
the breached subset (≈ 26% at the KP58.8 design level); conditioning the
output on the output breaks the ANOVA-HDMR decomposition over the full input
space (the Primer's framework requires Y square-integrable and defined a.e.
on Ω^k, Primer §4.3), and any imputation of non-breach rows (e.g. +∞ or
event length) manufactures variance that the indices would then decompose.
*Per-draw static–transient bias factor*: the bias is a population functional
(a ratio of fragility curves), not a per-realization random variable; a
per-draw ratio of margins Z_static/Z_transient mixes incommensurable margins
and degenerates where either crosses zero. The bias attribution is instead
delivered structurally: Y1 and Y2 are evaluated on the **same input sample**,
so the difference in their index vectors decomposes *which inputs* the
transient limit state is sensitive to that the static one is not (C_e, D_bl,
γ'_bl, k_bl enter only the transient branch — structural zeros in Y2/Y4 that
the GSA must reproduce, which doubles as a machinery validation).

### 2. Correlated inputs

**Primary analysis: independent inputs, exactly.** The mission framing
("mandatory k_aq–d_70 Nataf correlation") reflects the pre-ADR-0012 spec.
ADR-0012 resolved the coupling **empirically** as the two-population
decoupling (`coupling: two_population`, ρ recorded 0.0 and never imposed;
Pol-endorsed): matrix d_70 and framework k_aq are distinct soils drawn from
their own marginals. L is independent of θ by construction (M2). Under the
production prior, therefore, **all eight inputs are mutually independent and
the ANOVA-HDMR decomposition (Primer Eq. 4.11, footnote 5) holds exactly** —
standard Sobol' indices are unambiguous, and the Primer's own §1.3 counsel
(work with independent inputs wherever defensible) is satisfied not by
assumption but by the adopted production prior.

**Companion analysis: Nataf dependence bounded via the Rosenblatt/generator
route (Mara–Tarantola).** The `correlated` mode (Gaussian copula in log
space) remains a supported sensitivity configuration, and a reader may ask
what dependence would do to the ranking. The GSA therefore runs one bounding
companion at ρ_log(k_aq, d_70) = 0.6 (the retired pre-ADR-0012 provisional
value — deliberately conservative, ~6× the empirical pooled estimate). The
treatment extends the Primer deliberately: the analysis is performed **in the
space of the independent standard-normal copula generators** (the Rosenblatt
transform of the dependent pair). With k_aq as anchor, the generators are
(z_kaq, η_d70) with z_d70 = ρ·z_kaq + √(1−ρ²)·η_d70 — exactly M2's
construction — so Sobol' indices in generator space are exact
(independent inputs), and:

- the index of η_d70 is the **independent (uncorrelated) contribution** of
  d_70 — its effect purged of the part explainable through k_aq
  (Mara & Tarantola 2012's decorrelated indices);
- the index of z_kaq is the **full contribution** of k_aq, *including* the
  part of d_70's effect carried by the correlation.

Running the mirrored ordering (d_70 as anchor) gives the complementary pair.
This is exact for a Gaussian copula (no approximation), costs two ordinary
Sobol' runs, and reduces bit-identically to the primary analysis at ρ = 0.
Silently running independent-input formulas on correlated physical samples —
the trap the Primer's footnote 5 (p. 162) warns invalidates Eq. (4.11) — is
thereby avoided; interpretation of the companion is stated in the report in
Kucherenko/Mara–Tarantola full-vs-independent terms.

### 3. Estimators, sampling scheme, and budget

- **Design**: the Saltelli (2002) two-matrix scheme of Primer §4.6 in its
  Saltelli et al. (2010) radial form — base matrices A, B and the k matrices
  A_B^(i) (A with column i replaced from B), cost N(k+2) = 10N model runs
  per level per replicate for k = 8.
- **Sample generator**: Sobol' low-discrepancy sequences (the Primer §4.6
  explicitly recommends quasi-random sequences for these matrices), drawn in
  2k dimensions and split A|B, with **Owen scrambling** (scipy
  `qmc.Sobol(scramble=True)`) so that independent replicates provide unbiased
  randomized-QMC error estimation.
- **First-order estimator**: Ŝ_i = (1/N)·Σ_j y_B(j)·[y_ABi(j) − y_A(j)] / V̂
  (Saltelli et al. 2010, the refinement of the Primer's Eq. (4.21); strictly
  better behaved for small indices because the f0² subtraction cancels by
  construction).
- **Total-effect estimator**: Jansen (1999):
  ŜT_i = (1/2N)·Σ_j [y_A(j) − y_ABi(j)]² / V̂ (the Saltelli-2010 best
  practice; non-negative numerator by construction, unlike the Primer's
  Eq. (4.23) which can go negative for small ST_i — Primer p. 170 notes the
  negative-estimate pathology).
- V̂ and f̂0 are computed from the pooled (y_A, y_B) sample (the Primer
  p. 166 accuracy note).
- **Budget**: base N = 2^13 = 8192 per replicate with R = 25 independent
  scramblings per level (≈ 2.0×10^6 engine realizations per level), justified
  a posteriori by the convergence ladder below rather than a round number;
  the ADR-0029/0030 accelerated engine (numba backend, Δt = 225 s) evaluates
  one replicate batch (81,920 realizations) in ≈ 0.1 s, so the full
  two-section study is minutes, not hours. Tail/shoulder levels may double N
  (2^14) where the indicator variance P(1−P) is small; the driver takes
  per-level N.

### 4. Convergence demonstration and uncertainty statement

- **Primary uncertainty**: replicate spread over the R = 25 independent Owen
  scramblings — mean index, standard error, and a Student-t 95% CI per index.
  This is the honest error statement for QMC designs (bootstrap resampling of
  QMC rows breaks the low-discrepancy balance the estimator variance depends
  on, biasing CI width; replication does not).
- **Bootstrap CIs** (the Primer's recommendation, p. 166, following Archer
  et al.): within each replicate, B = 500 row-bootstrap resamples of the
  paired (y_A, y_B, y_AB1..k) rows, percentile 95% CIs, pooled across
  replicates. Reported alongside the replicate CIs; agreement between the two
  is itself a convergence check. Every reported index carries both.
- **Convergence ladder**: N ∈ {2^10, 2^11, 2^12, 2^13} (to 2^14 where
  needed) at fixed R; the acceptance criterion is (a) monotone CI shrinkage
  consistent with the expected rate and (b) index drift between the two
  finest rungs below 0.02 in absolute index units for every reported index.
- **Sanity invariants** recorded per run: Σ S_i ≤ 1 + noise, ST_i ≥ S_i − noise,
  structural zeros (C_e, D_bl, k_bl, γ'_bl on Y2/Y4) statistically
  indistinguishable from zero, and negative small-index estimates within CI
  of zero (the Primer p. 170 explains these are expected for noninfluential
  factors).

### 5. Machinery validation before engine use

`tests/test_sensitivity.py` validates the estimator stack against analytical
benchmarks with known indices **before** it touches the engine:

1. **Ishigami function** (A = 7, B = 0.1; the Primer's own example,
   §4.6/Ch. 5 Ex. 2) — analytic S = (0.3139, 0.4424, 0), ST = (0.5576,
   0.4424, 0.2437); exercises interactions and a pure-interaction factor.
2. **Sobol' g-function** at k = 8, a = [0, 1, 4.5, 9, 99, 99, 99, 99] (the
   Primer Ch. 5 Ex. 3 coefficient set) — analytic indices at the engine's
   dimensionality, strong factor-importance contrast.
3. **Linear-Gaussian threshold indicator** Y = 1{Σ c_i X_i > τ} — ground
   truth by 1-D Gauss–Hermite quadrature; validates the binary-QoI case (Y1/Y2)
   the engine analysis leans on.
4. **Correlated bilinear Gaussian** (analytic full/independent indices under
   a correlated pair) — validates the §2 Rosenblatt companion machinery, at
   ρ = 0 collapsing to the independent case.

The engine adapter (`gsa_qoi.evaluate_qoi_batch`, which returns the
continuous outputs `evaluate_batch` discards) is pinned to M8 by a
drift-guard test: its derived failure flags must be **bit-identical** to
`evaluate_batch` on the same inputs (numpy backend), and its physical-units
input map must be **bit-identical** to M2's `sample_theta` given the same
underlying design.

### 6. Scenario axis

Per ADR-0023 the climate axis is shape-invariant: one canonical HPB shape
drives all scenarios and `conditioning_record_for_level` is scenario-blind
by construction, so a "+4K GSA" at matched conditioning level is
**definitionally identical** to the historical one (the driver verifies this
bit-identity once and records it). The climate-relevant sensitivity statement
is instead the **level-dependence** of the indices: +4K shifts the hazard
(peak-stage distribution), i.e. moves probability mass along the h_i axis,
so how the index picture rotates from shoulder to upper levels *is* the +4K
story. The report states this explicitly rather than running a redundant
sweep.

### 7. Scope

Sections: **KP58.8 and KP60.0, matrix d_70** (the governing reachable pair,
ADR-0031 §1) in full; one **bulk-d_70 companion** at the KP58.8 design level
(ranking robustness to the co-primary interpretation, spec §13); the **Nataf
companion** of §2 at the KP58.8 design level. KP57.4/KP62.0 are excluded
from the indicator QoIs (transient P_f ≈ 10^−4–10^−5 at attainable stages
makes indicator GSA structurally non-convergent there — the same regime
argument as ADR-0024/0031); their static-resistance GSA (Y4) is covered by
the section-independent structure of Y4.

New code: `bep_reliability_engine/sensitivity.py` (designs, estimators,
generator→physical maps, bootstrap — physics-free, evaluation injected,
following the `convergence.py` pattern), `bep_reliability_engine/gsa_qoi.py`
(the thin M8-mirroring continuous-output batch adapter),
`scripts/gsa_study.py` (driver + figures), `tests/test_sensitivity.py` +
`tests/test_gsa_qoi.py`. Artifacts: JSON records under `results/gsa/` with
tracked copies `docs/decisions/adr0033-gsa-study*.json`, figures under
`docs/figures/`, companion note `docs/decisions/adr0033-gsa-study.md`,
report section `_thesis_gsa.tex` (+ `.bib`).

---

## Alternatives Considered

### QoI: median time-to-breach
Pros: directly interpretable as an early-warning quantity. Cons: defined only
conditionally on breach (≈ 26% of draws at the design level); imputation or
conditioning both destroy the unconditional variance decomposition the
framework rests on (Primer §4.3). Rejected; the l_e/L fraction (Y3) carries
the progression-dynamics information unconditionally.

### QoI: per-draw bias factor
Cons: the static–transient bias is a functional of the two fragility curves,
not a per-draw random variable; ratios of margins degenerate at zero
crossings. Rejected in favor of same-sample index contrast (Y1 vs Y2).

### Correlated inputs: Kucherenko conditional-sampling estimators on the physical space
Pros: gives full/independent indices directly. Cons: needs conditional
distribution sampling and doubles the estimator machinery; for a *Gaussian
copula* the Rosenblatt/generator route is mathematically identical, reuses
the independent-input estimator stack unchanged, and is exact. Rejected as
redundant for this copula (the generator route *is* the Kucherenko
decomposition here, obtained more simply).

### Correlated inputs: run independent-input Sobol' on the ρ = 0.6 physical sample and caveat it
Cons: exactly the silent-invalidity trap the Primer footnote 5 (p. 162)
warns about — the estimators' interpretation as variance shares fails and
Σ S_i can exceed 1 without any diagnostic. Rejected outright.

### Estimators: the Primer's original Eq. (4.21)/(4.23) (Sobol'-Homma-Saltelli)
Pros: exactly what the Primer prints. Cons: the f0² subtraction in (4.21)
inflates variance for small S_i, and (4.23) lacks Jansen's non-negativity;
Saltelli et al. (2010) — by the Primer's own first author — supersedes both
as best practice. Adopted the 2010 forms and documented the extension, per
the mission's instruction to extend deliberately where warranted.

### Estimators: FAST / Random Balance Designs (Primer §4.7)
Pros: all first-order indices from N runs. Cons: no total-effect indices
(RBD) or fragile frequency selection (FAST); ST_i is half the deliverable
(the interaction diagnostic). Rejected.

### Sampling: plain LHS for the A/B matrices
Cons: LHS stratification benefits do not survive the column-splicing of the
radial design (the A_B^i matrices break the marginal stratification), and
ADR-0029/0031 measured LHS's advantage vanishing exactly in the interaction-
dominated regime this GSA probes. Scrambled Sobol' is the Primer's own
recommendation for this design. Rejected.

### Metamodel-based GSA (Primer Ch. 5 HDMR/emulators)
Pros: fewer engine runs. Cons: unnecessary — the ADR-0029 accelerated engine
makes direct double-loop-free estimation trivially affordable; a metamodel
would add approximation error requiring its own validation. Rejected.

---

## Rationale

The variance-based framework is the Primer's central recommendation for
models with interactions and is the only mainstream GSA family that (a)
quantifies interactions explicitly via ST_i − S_i — the fm7 C_e×k_aq
question is *the* scientific motivation here — and (b) carries a
model-free decomposition guarantee under independence, which the production
prior (ADR-0012) satisfies exactly. The indicator QoI ties the indices
directly to the engine's deliverable (P_f at a conditioning level): for a
binary Y, V(Y) = P_f(1−P_f) and S_i measures the expected reduction in
classification variance from learning input i — precisely the "which
parameter should Phase 2 be expected to tighten" question. The continuous
QoIs (Y3, Y4) complement where the indicator is information-poor (shoulder
levels) or where the structure is analytic (the static branch). Replicated
scrambled QMC gives both the efficiency of low-discrepancy sampling and an
unbiased uncertainty statement, with the Primer's bootstrap retained as a
cross-check so every index carries two independently derived CIs.

---

## Consequences

- The engine is untouched; all GSA code is additive. The M8 contract is
  respected via the adapter + bit-identity drift guards.
- The production sweep artifacts (FragilityResult) are unchanged; GSA
  artifacts live in `results/gsa/` + tracked copies under `docs/`.
- The ranking and interaction structure become citable, with CIs, per
  section and per level — the quantitative basis for the thesis's
  parameter-importance claims and for Phase 2 expectations (which
  parameters the 2016 survival can and cannot inform).
- The Nataf companion bounds the cost of the ADR-0012 independence decision
  for the GSA conclusions; if the ranking were to flip at ρ = 0.6 (it does
  not — see the companion note), the two-population adoption would warrant
  a caveat in the fragility interpretation as well.
- Runtime: full study minutes-scale on the dev machine (numba backend);
  reproducible from config seeds via SeedSequence tags.

---

## References

- Saltelli, A., Ratto, M., Andres, T., Campolongo, F., Cariboni, J.,
  Gatelli, D., Saisana, M., Tarantola, S. (2008). *Global Sensitivity
  Analysis: The Primer*. Wiley. §1.2 (settings), §1.3 (nonindependent
  inputs), §4.3–4.6 (variance decomposition, S_i/ST_i, the Saltelli 2002
  design, quasi-random recommendation, bootstrap error estimation), §4.9
  (cost caveats), Ch. 5 Ex. 2–3 (Ishigami, g-function).
- Saltelli, A. (2002). Making best use of model evaluations to compute
  sensitivity indices. *Comput. Phys. Commun.* 145, 280–297.
- Saltelli, A., Annoni, P., Azzini, I., Campolongo, F., Ratto, M.,
  Tarantola, S. (2010). Variance based sensitivity analysis of model
  output. Design and estimator for the total sensitivity index.
  *Comput. Phys. Commun.* 181, 259–270.
- Jansen, M.J.W. (1999). Analysis of variance designs for model output.
  *Comput. Phys. Commun.* 117, 35–43.
- Mara, T.A., Tarantola, S. (2012). Variance-based sensitivity indices for
  models with dependent inputs. *Reliab. Eng. Syst. Saf.* 107, 115–121.
- Kucherenko, S., Tarantola, S., Annoni, P. (2012). Estimation of global
  sensitivity indices for models with dependent variables. *Comput. Phys.
  Commun.* 183, 937–946.
- Owen, A.B. (1997). Monte Carlo variance of scrambled net quadrature.
  *SIAM J. Numer. Anal.* 34, 1884–1910.
- ADR-0001 (7D vector), ADR-0002 (shared sample), ADR-0012 (two-population
  coupling — the correlated-inputs premise), ADR-0023 (shape-invariant
  climate axis — the +4K premise), ADR-0024/0029/0030/0031 (tail regime,
  acceleration, Δt, N-sufficiency).
- Spec §7 (input space), §12 fm5/fm7 (the C_e×k_aq interaction), §11
  (convergence discipline).
