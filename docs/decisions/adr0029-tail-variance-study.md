# ADR-0029 companion: the spec §12 fm5 tail-variance study

Date: 2026-07-07 (data: `adr0029-tail-cov-study.json`; figure:
`../figures/adr0029-tail-cov.png`; script: `scripts/tail_variance_study.py`)

## Question

Spec §12 failure mode 5: LHS stratifies marginals, but the deep transient
failure tail is governed by the multiplicative C_e×k_aq interaction (fm7),
so the assumed LHS tail-variance advantage over crude Monte Carlo at the
same N "is not assumed; it is verified empirically against crude Monte
Carlo at the operating N, evaluated on the failure tail specifically rather
than on the bulk." This note is that verification, plus the measurement of
the ADR-0029 tilted importance sampler as the targeted mitigation.

## Protocol

KP58.8 historical/matrix production config (canonical d4PDF shape,
stochastic L, two-population coupling), transient branch, operating
N = 10⁴ (the fm5 reduced-N regime), R = 40 replicate seeds per scheme per
level, all reproducible from the config seed. Three estimators at identical
N per replicate: **LHS** (the production M2 design, raw fraction), **crude
MC** (iid, the spec §13 debug fallback, raw fraction), **tilted IS**
(LHS-stratified, Z-space mean shift on {k_aq, C_e} staged by cross-entropy
level to level, exact weights). Study levels were placed by a
strong-shift IS probe to hit P_f ≈ {0.3, 10⁻², 10⁻³, 10⁻⁴}; the deepest
level (39.375 m) is off the production grid because the grid's 0.25 m
spacing jumps from P ≈ 3·10⁻⁶ to 6·10⁻⁴ between 39.25 and 39.5 m.
Evaluation used the ADR-0029 numba backend (failure indicators identical to
the numpy reference at production scale).

## Results (empirical replicate CoV of P̂_f)

| h [m] | P_f (≈) | LHS | crude MC | tilted IS | MC/LHS | MC/IS | LHS/IS |
|---|---|---|---|---|---|---|---|
| 41.000 | 2.8·10⁻¹ | 0.012 | 0.014 | 0.011 | 1.13 | 1.21 | 1.09 |
| 40.000 | 1.6·10⁻² | 0.080 | 0.063 | 0.041 | 0.79 | 1.54 | 1.95 |
| 39.500 | 6.0·10⁻⁴ | 0.421 | 0.392 | 0.102 | 0.93 | 3.86 | 4.13 |
| 39.375 | 1.0·10⁻⁴ | 0.806 | 0.869 | 0.251 | 1.08 | 3.47 | 3.21 |

Supporting diagnostics (JSON):

- **Zero-failure (blind) replicates** at P_f ≈ 10⁻⁴: LHS 30%, crude MC
  28%, tilted IS 0%. At this depth an unweighted run at the operating N is
  a coin flip away from reporting P̂_f = 0.
- **LHS behaves exactly like iid in the tail**: its empirical CoV matches
  the binomial (iid) prediction there (0.421 vs 0.430 at 6·10⁻⁴; 0.806 vs
  0.859 at 10⁻⁴), while in the bulk it *beats* the binomial prediction
  (0.012 vs 0.016) — the stratification benefit is real where main effects
  carry the variance and vanishes where the interaction does.
- **Staged CE shifts** grew from (ν_kaq, ν_Ce) = (0.70, 0.47) at the bulk
  to (1.57, 2.29) at 10⁻⁴ — the tilt direction rotates toward C_e with
  depth, consistent with fm7's C_e-dominated tail amplification.
- **IS weight health**: Kish effective failure counts 3275 → 512 → 101 →
  25 across the four levels; the analytic within-run CoV of the IS
  estimator tracks its replicate CoV closely (0.102 vs 0.102 at 6·10⁻⁴),
  so the reported IS precision is trustworthy at these depths.

## Verdict on fm5

**The naive LHS tail-variance claim is refuted; the fm5 caveat is
confirmed.** With R = 40 replicates the CoV-ratio standard error is ≈ 0.16,
so the tail ratios (0.79, 0.93, 1.08) are statistically indistinguishable
from 1: LHS delivers **no detectable CoV advantage over crude Monte Carlo
anywhere in the failure tail** (P_f ≲ 10⁻²) at the operating N. The modest
bulk advantage (ratio 1.13, i.e. ~22% variance reduction) is consistent
with LHS removing the additive part of the indicator's variance — exactly
the part the multiplicative C_e×k_aq tail does not have.

This does **not** dethrone LHS as the production sampler: the sweep needs
the whole curve (bulk levels included), the Phase 2 handoff requires the
plain prior θ-matrix with unweighted failure matrices (spec §2/§8), and LHS
costs nothing extra. The correction is to the *interpretation*: raw tail
points from the sweep carry crude-MC-grade uncertainty, and the ADR-0024
Clopper–Pearson intervals (which assume exactly that) are the right
uncertainty statement for them.

**The tilted IS delivers the targeted mitigation.** In the deep tail it
cuts the replicate CoV 3.2–4.1× versus both LHS and crude MC at the same
N — equivalently, ~10–17× fewer transient evaluations for equal precision —
and it eliminates blind (zero-failure) runs outright. Where a tail P_f
below the grid's raw-resolvable range is needed (e.g. the sub-toe-adjacent
levels, or KP62.0's unreachable transition), the tilted estimator with its
n_eff diagnostic is the tool; its numbers are weighted estimates and stay
out of FragilityResult failure matrices (ADR-0029 Consequences).

## Caveats

- One cross-section (KP58.8, matrix d_70) at one operating N; the ratios'
  replicate noise is ±0.16. The qualitative structure (bulk advantage
  decaying to parity in the tail) follows the variance decomposition
  argument and is expected to transfer; the study script reruns per config
  in ~15 s if a per-section record is wanted.
- The IS probe estimates at near-certain levels can exceed 1 in finite
  samples (unbiased, non-self-normalized estimator under a strong shift);
  probe values are used only to place study levels, never reported as
  probabilities.
- The iid-formula standard error reported by `importance_estimate` is
  mildly conservative for the LHS-stratified proposal in the bulk and
  essentially exact in the tail (see the LHS-vs-binomial comparison above).
