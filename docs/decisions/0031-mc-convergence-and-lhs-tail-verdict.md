# ADR-0031: Monte-Carlo Convergence — N = 10⁵ Sufficiency and the LHS-vs-Crude-MC Tail-Variance Verdict

Date: 2026-07-10
Status: Accepted

---

## Context

Two spec claims about the Monte-Carlo machinery were verifiable-but-unverified
on the current physics (C_e = 0.055, raw heads ADR-0027/0028, Δt = 225 s
ADR-0030):

1. **Spec §11 convergence.** The field standard (Schweckendiek 2014) is
   `CoV(P̂_f) < 5%` across the relevant failure range, and the spec is explicit
   that "sample sizes of order 10⁵ typically achieve this, and this sufficiency
   is verified directly for each cross-section once the engine runs rather than
   assumed." Every run records the *analytic binomial* CoV at the single
   operating N in `metadata['mc_convergence']`, but nothing measured the
   empirical CoV across a ladder of N, nor tested whether the production LHS
   sampler actually obeys the binomial law it assumes.
2. **Spec §12 fm5.** The deep transient failure tail is governed by the
   multiplicative C_e×k_aq interaction (fm7); LHS stratifies marginals only, so
   any LHS tail-variance advantage over crude Monte Carlo "is not assumed; it is
   verified empirically." ADR-0029 ran this once (KP58.8, N = 10⁴, R = 40) and
   folded the refutation into fm5. This ADR is the full N-ladder verification of
   both claims together, on a governing section, packaged as reusable engine
   code.

Hard constraints honoured: LHS remains the production sampler and the Phase-2
handoff needs the plain unweighted θ-matrix (spec §2/§8); the study touches no
physics (evaluation is injected) and reuses the validated
`sample_theta_tilted` so its LHS arm is bit-identical to M2 and its crude-MC
arm is the spec §13 fallback.

---

## Decision

**1. Governing sections: KP58.8 and KP60.0 (both matrix d_70).** Of the four
production sections, transient P_f at the design HWL is KP57.4 ≈ 7·10⁻⁵,
KP58.8 ≈ 0.27, KP60.0 ≈ 0.31, KP62.0 ≈ 8·10⁻⁵. KP62.0 is foreshore-suppressed
(transition ~4 m above any attainable stage) and KP57.4 reaches BEP only well
above HWL; KP58.8 and KP60.0 are the reachable pair, so both were run (KP58.8
first, as the ADR-0029 fm5 baseline — this *refreshes* that decision rather
than opening a new one; KP60.0 second, as an independent confirmation). Both
resolve the transient tail to P_f ≈ 10⁻⁴–10⁻⁵ on their own grids and, at R = 50
each, reproduce the same bulk-to-tail decay to within ~1σ (companion note
§"Second section: KP60.0").

**2. New reusable code.** `bep_reliability_engine/convergence.py` (statistical
primitives: `empirical_cov`, `binomial_cov`, `n_for_cov_target`,
`run_replicates`; no physics — evaluation and the seepage-length draw are
injected), the thin driver `scripts/convergence_study.py`, and
`tests/test_convergence.py`. Reproducible from the config seed; numba backend.
Artifacts to `results/` (working, gitignored) and `docs/` (tracked): data
`adr0031-convergence-study.json`, figures `adr0031-convergence-n-ladder.png`
and `adr0031-tail-lhs-vs-crude.png`, full write-up
`adr0031-convergence-study.md`.

**3. N-sufficiency finding — N = 10⁵ is retained.** At R = 50 replicates over
`N ∈ {10³ … 3·10⁵}`, the empirical LHS CoV of the transient P̂_f falls as 1/√N
and:

- meets the 5% target across the whole bracketed fragility curve and for
  per-level transient P_f down to ≈ 5·10⁻³ (CoV = 4.1% at P_f = 4.7·10⁻³ at
  N = 10⁵; the transition midpoint sits at CoV ≪ 1%);
- degrades below ≈ 10⁻³ (16.5% at P_f = 3·10⁻⁴), where holding 5% would need
  ≈ 1.3·10⁶ realizations — 13× the operating N per additional tail decade;
- tracks and mildly *beats* the analytic binomial value (bulk CoV ≈ 28% below
  it, tail CoV equal to it), so the existing `mc_convergence` block is a
  trustworthy, mildly conservative diagnostic.

Raising N is therefore the wrong tool for the deep tail (the deliverable does
not need it, and one decade of tail costs a decade of N); the deep tail is the
ADR-0024 raw-tail-with-binomial-CI regime by design, and sub-decade point
estimates come from the ADR-0029 tilted estimator.

**4. Tail-variance verdict — the naive LHS claim is refuted where it matters.**
The ladder-mean variance-reduction ratio `CoV_MC / CoV_LHS` (transient) is
**1.40 ± 0.09 in the bulk (P_f ≈ 0.26)** at KP58.8, decaying monotonically to
**1.00 ± 0.06 in the deep tail (P_f ≈ 3·10⁻⁴)**, where the LHS CoV equals the
iid binomial value. **KP60.0 reproduces this point for point**: 1.48 ± 0.06
(bulk, P_f ≈ 0.31) decaying to 1.01 ± 0.04 (deep tail, P_f ≈ 7.5·10⁻⁵) — two
independent sections agree that the tail advantage vanishes, not merely
weakens. The static branch (KP58.8) — identical in every sampled input but
carrying no C_e (ADR-0001) — retains an LHS advantage of ratio ≈ 1.1–1.3
across its whole range, isolating the C_e×k_aq interaction (fm7) as the cause:
LHS stratifies marginals, not the multiplicative interaction that governs the
transient tail. LHS stays the production sampler (a real bulk advantage at zero
cost; the unweighted matrices are non-negotiable for Phase 2), and **the
sampler interface stays open to a joint-tail variance-reduction scheme at the
lowest levels** — already realised as `tail_sampling.sample_theta_tilted`
(ADR-0029). No new scheme is built here.

---

## Alternatives Considered

### Raise N (e.g. to 10⁶) to resolve the deep tail
Cons: ≈ 13× the sweep cost to buy a single tail decade of 5%-grade precision,
for levels the fragility deliverable already reports as raw points with exact
CIs (ADR-0024). The estimator variance of an unweighted scheme is
irreducible-by-N-alone in the tail relative to the far cheaper importance
sampler. Rejected.

### Trust the analytic `mc_convergence` block; skip the empirical study
Cons: the binomial formula *assumes* iid behaviour; without the ladder we could
not know whether LHS follows it (it does, and slightly beats it) nor measure
the LHS-vs-crude tail question at all. The study validates the cheap per-run
diagnostic rather than replacing it. Rejected as insufficient.

### Re-run the tilted-IS tail study
Cons: ADR-0029 already measured the IS mitigation (3.2–4.1× deep-tail CoV cut).
This study is scoped to the LHS-vs-crude question the spec's fm5 poses and
cites IS as the designated tool; re-running it would duplicate ADR-0029.
Rejected as redundant.

---

## Rationale

The two questions share one replicate design: independent LHS and crude-MC
draws at a ladder of N, at conditioning levels spanning bulk → deep tail, with
the seepage length held common per replicate so the schemes differ only in the
θ design. The empirical replicate CoV needs no distributional assumption, so it
simultaneously (a) reads off the N at which each P_f crosses 5% (Objective 1)
and (b) gives the LHS-vs-crude ratio and its bulk→tail decay (Objective 2). The
static branch is a free control that pins the mechanism to C_e. The finding is
consistent with ADR-0029 and with the variance-decomposition argument (LHS
removes the additive part of the indicator variance; the tail has none), so it
is expected to transfer to the other reachable sections.

---

## Consequences

- **N = 10⁵ confirmed for the Phase-1 sweep.** Deep-tail levels stay reported
  with ADR-0024 Clopper–Pearson CIs; sub-decade point estimates use the
  ADR-0029 tilted sampler with its n_eff diagnostic. No sweep parameters
  change.
- **Reusable convergence tooling** now exists (`convergence.py` + driver +
  test); a per-section record for KP60.0 (the other reachable section) is a
  ~10-minute rerun if wanted.
- **ADR-0029's bulk ratio is updated** (1.13 → ladder-mean 1.40 under the
  current physics and R = 50); the tail conclusion (parity) is unchanged. The
  spec §12 fm5 refutation stands, now on a full N-ladder.
- **Spec §11 pointer added** — the "verified directly for each cross-section"
  claim now cites this ADR for KP58.8.
- Interpretation guard reinforced: raw sweep tail points carry crude-MC-grade
  uncertainty; do not quote them as if LHS tightened them.

---

## References

- Spec §11 (convergence diagnostic, the 5% CoV target, 1/√N), §12 fm5/fm7
  (LHS-vs-crude tail variance, the C_e×k_aq interaction), §13 (LHS + crude-MC
  fallback).
- ADR-0024 (raw-tail-with-binomial-CI deliverable), ADR-0029 (tilted-IS tail
  estimator and the first fm5 study), ADR-0001 (C_e stochastic — the static
  control), ADR-0030 (Δt = 225 s), ADR-0027/0028 (raw heads).
- Schweckendiek (2014) — the `CoV < 5%` field standard.
- Companion note `adr0031-convergence-study.md`; data
  `adr0031-convergence-study.json` (KP58.8) and
  `adr0031-convergence-study-kp60_0_matrix.json` (KP60.0); figures
  `docs/figures/adr0031-convergence-n-ladder.png`,
  `docs/figures/adr0031-tail-lhs-vs-crude.png`,
  `docs/figures/adr0031-convergence-n-ladder-kp60_0_matrix.png`,
  `docs/figures/adr0031-tail-lhs-vs-crude-kp60_0_matrix.png`. Runs 2026-07-10,
  Windows 11 / Python 3.11 / numba, N-ladder 10³–3·10⁵, R = 50: KP58.8 matrix
  (1010 s) and KP60.0 matrix (1028 s).
