# ADR-0031 companion: the Phase 1 statistical convergence study

Date: 2026-07-10 (data: `adr0031-convergence-study.json`; figures:
`../figures/adr0031-convergence-n-ladder.png`,
`../figures/adr0031-tail-lhs-vs-crude.png`; module:
`bep_reliability_engine/convergence.py`; driver:
`scripts/convergence_study.py`)

## Question

Two spec questions, one replicate design:

1. **Estimator convergence (spec §11).** Standard practice (Schweckendiek
   2014) targets `CoV(P̂_f) < 5%` across the relevant failure range, and the
   spec states this sufficiency "is verified directly for each cross-section
   once the engine runs rather than assumed." Does `N = 10⁵` deliver it at a
   *governing* section, and down to what failure probability? The per-run
   `metadata['mc_convergence']` block records only the *analytic binomial*
   CoV at the single operating N — it never tests whether the production LHS
   sampler actually obeys that binomial law.
2. **Tail variance (spec §12 fm5).** LHS stratifies marginals; the deep
   transient failure tail is governed by the *multiplicative* C_e×k_aq
   interaction (fm7). Does LHS beat crude Monte Carlo *in the tail*, or only
   in the bulk? ADR-0029 measured this once (KP58.8, N = 10⁴) and folded the
   refutation into fm5; this note is the full N-ladder verification under the
   current physics (C_e = 0.055, raw heads, Δt = 225 s), packaged as a
   reusable module.

## Governing section

**KP58.8 (matrix d_70).** From the four production sections (existing
sweeps), transient P_f at the design HWL is: KP57.4 ≈ 7·10⁻⁵, **KP58.8 ≈
0.27**, KP60.0 ≈ 0.31, KP62.0 ≈ 8·10⁻⁵. KP62.0 is the foreshore-suppressed
section the spec warns against (transition median 50.6 m sits ~4 m above any
attainable stage); KP57.4 only reaches BEP well above HWL. KP58.8 and KP60.0
are the two where BEP is genuinely reachable at the design level (both bracket
the transition with fitted-lognormal deliverables). KP58.8 was chosen: it
resolves the transient tail cleanly to P_f ≈ 4·10⁻⁴ on its own grid, and it is
the ADR-0029 fm5 baseline, so this study *refreshes* that decision under the
current physics rather than opening a new one. (KP60.0 reruns in ~10 min via
the driver if a second record is wanted.)

## Protocol

Four production-grid transient conditioning levels span bulk → deep tail
(P_f ≈ {0.26, 0.025, 5·10⁻³, 4·10⁻⁴}). At each level, across the ladder
`N ∈ {10³, 3·10³, 10⁴, 3·10⁴, 10⁵, 3·10⁵}`, `R = 50` independent replicate
seeds per sampler produce the empirical replicate CoV of P̂_f. Two samplers,
both from `sample_theta_tilted` with **no tilt** — **LHS** (`stratified=True`,
bit-identical to production M2) and **crude MC** (`stratified=False`, the spec
§13 debug fallback) — share the *same* iid seepage-length L per replicate
index, so they differ **only** in the θ design (the fm5 isolation, matching
ADR-0029). Both branches are recorded; the transient branch is the fm5/fm7
story, the static branch (no C_e, ADR-0001) is the control. Evaluation used
the ADR-0029 numba backend (failure indicators identical to numpy at this
scale). Everything is reproducible from the config seed; runtime 573 s.

## Objective 1 results — estimator convergence (transient, LHS)

| h [m] | P_f | CoV @10⁴ | CoV @3·10⁴ | CoV @10⁵ | CoV @3·10⁵ | N for 5% |
|---|---|---|---|---|---|---|
| 41.00 | 2.6·10⁻¹ | 0.011 | 0.007 | **0.004** | 0.002 | 1.1·10³ |
| 40.25 | 2.5·10⁻² | 0.055 | 0.033 | **0.015** | 0.010 | 1.6·10⁴ |
| 40.00 | 4.7·10⁻³ | 0.132 | 0.074 | **0.041** | 0.026 | 8.5·10⁴ |
| 39.75 | 3.0·10⁻⁴ | 0.547 | 0.336 | **0.165** | 0.118 | 1.3·10⁶ |

- **1/√N holds.** Within the resolvable regime the empirical CoV falls as
  1/√N (e.g. h = 40.00: 0.132 → 0.041 from N = 10⁴ → 10⁵, a factor 3.2 ≈
  √10). See the parallel-slope figure.
- **The LHS CoV tracks — and mildly beats — the binomial law.** At the deep
  tail its empirical CoV equals the iid formula (0.165 vs 0.177 at P_f ≈
  3·10⁻⁴, N = 10⁵); in the bulk it *beats* it (0.0038 vs 0.0053 at P_f ≈
  0.26, ≈ 28% below). So the engine's existing analytic `mc_convergence`
  block is a trustworthy, mildly conservative convergence statement — no
  correction needed to it.
- **N = 10⁵ resolves transient P_f down to ≈ 5·10⁻³** (h = 40.00 lands at
  CoV = 4.1%, just inside target). The transition midpoint (P_f ~ 0.5) and
  the whole bracketed curve sit at CoV ≪ 1%. Below ≈ 10⁻³ the CoV degrades
  (16.5% at P_f ≈ 3·10⁻⁴), and holding 5% there would need ≈ 1.3·10⁶
  realizations — 13× the operating N for one more tail decade.
- **The static branch never binds** — at every level its CoV is far below the
  transient's (e.g. at h = 39.75 the static P_f = 0.021 already sits at CoV =
  1.8% at N = 10⁵). Transient is always the limiting branch.

## Objective 2 results — LHS vs crude MC (transient)

Ladder-mean variance-reduction ratio `CoV_MC / CoV_LHS` per level (mean over
the six N rungs ± SE; the ratio is N-invariant in expectation):

| P_f (transient) | CoV_MC / CoV_LHS | vs parity |
|---|---|---|
| 2.6·10⁻¹ (bulk) | **1.40 ± 0.09** | ≈ 4.7σ advantage |
| 2.5·10⁻² | 1.07 ± 0.04 | ~1.6σ (weak) |
| 4.7·10⁻³ | 1.16 ± 0.09 | ~1.9σ (noisy) |
| 3.0·10⁻⁴ (deep tail) | **1.00 ± 0.06** | 0σ — no advantage |

- **Strong bulk advantage, decaying to exact parity.** In the bulk LHS cuts
  the estimator CoV ~28% (ratio 1.40 ⇒ crude MC needs ≈ 2× the samples for
  equal precision). The advantage falls monotonically and, in the deep tail,
  LHS behaves *exactly* like crude MC (ratio 1.00 ± 0.06, and its CoV equals
  the iid binomial value).
- **The mechanism is C_e×k_aq (fm7), confirmed by the static control.** The
  static branch — identical to the transient in every sampled input *except
  it has no C_e* (ADR-0001) — keeps an LHS advantage of ladder-mean **1.14 –
  1.34 across its entire resolved range**, including its deepest level
  (P_f = 0.021, ratio 1.14). The only branch that *loses* the LHS benefit as
  P_f falls is the one exposed to the multiplicative C_e×k_aq interaction.
  This is direct evidence that fm7's interaction — which LHS's marginal
  stratification does not sample any better than iid — is what defeats LHS in
  the transient tail (fm5).
- **Blind (zero-failure) replicates** appear for the deep-tail level only at
  small N: at P_f ≈ 3·10⁻⁴, 78% (LHS) / 68% (MC) of R = 50 replicates saw
  zero failures at N = 10³, 38% / 42% at N = 3·10³, ≤ 2% by N = 10⁴, none at
  the operating N. (The deeper P_f ≈ 10⁻⁴ regime where ADR-0029 found ~30%
  blind runs even at N = 10⁴ is below this section's grid.)

## Verdict (thesis-ready)

> **N = 10⁵ sufficiency.** For the governing Tokachi cross-section (KP58.8,
> matrix d_70), a ladder of independent Latin-Hypercube runs (R = 50
> replicates per rung) confirms that the coefficient of variation of the
> Monte-Carlo failure-probability estimator falls as 1/√N and meets the
> Schweckendiek (2014) `CoV < 5%` standard across the entire bracketed
> fragility curve and for per-level transient failure probabilities down to
> ≈ 5·10⁻³ (CoV = 4.1% at P_f = 4.7·10⁻³). The empirical LHS CoV tracks, and
> in the bulk beats by ~28%, the analytic binomial value, so the per-run
> convergence diagnostic already recorded in the result metadata is a
> trustworthy, mildly conservative statement. Below P_f ≈ 10⁻³ the estimator
> CoV rises above 5% (16.5% at P_f = 3·10⁻⁴) and holding the target there
> would require of order 10⁶ realizations for each additional tail decade;
> this is the raw-tail regime that the fragility deliverable reports with
> exact binomial (Clopper–Pearson) confidence intervals rather than a point
> estimate. **N = 10⁵ is therefore retained**: it resolves the Phase-1
> deliverable, and resolving the deep tail is a job for a variance-reduction
> estimator, not a larger fixed sample.

> **LHS versus crude Monte Carlo in the tail.** Latin Hypercube delivers a
> real and robust variance reduction in the bulk (CoV ratio 1.40 ± 0.09 at
> P_f ≈ 0.26, i.e. ≈ 2× fewer samples for equal precision) but this advantage
> decays monotonically to statistical parity in the deep transient tail
> (ratio 1.00 ± 0.06 at P_f ≈ 3·10⁻⁴), where its estimator variance is
> indistinguishable from iid sampling. The cause is the multiplicative
> C_e×k_aq interaction that governs the transient tail: LHS stratifies
> marginals, not interactions. This is isolated cleanly by the static limit
> state, which shares every sampled input but carries no C_e and retains its
> LHS advantage (ratio ≈ 1.1–1.3) throughout its range. The naive expectation
> that LHS tightens the failure tail is therefore refuted where it matters,
> confirming the spec's fm5 caveat; LHS nonetheless remains the production
> sampler (a genuine bulk advantage at zero extra cost, and the Phase-2
> handoff requires the plain unweighted θ-matrix). Sub-decade tail
> probabilities are quantified instead by the cross-entropy-tilted importance
> sampler (`tail_sampling.sample_theta_tilted`, ADR-0029), which cuts
> deep-tail CoV 3–4×; the sampler interface remains open to such a joint-tail
> scheme at the lowest conditioning levels, as this study confirms is needed.

## Second section: KP60.0 (matrix d_70) — confirmation

KP60.0 is the other section where BEP is genuinely reachable at HWL
(transient P_f ≈ 0.31 there). The identical protocol was re-run (R = 50,
same N-ladder), with four levels picked from KP60.0's own production grid to
span the same bulk → deep-tail range (`--config kp60_0_historical_matrix.yaml
--levels 42.75,42.00,41.50,41.25`; data
`adr0031-convergence-study-kp60_0_matrix.json`, figures
`adr0031-convergence-n-ladder-kp60_0_matrix.png`,
`adr0031-tail-lhs-vs-crude-kp60_0_matrix.png`).

| h [m] | P_f (transient) | CoV @ N=10⁵ | N for 5% | ladder-mean ratio CoV_MC/CoV_LHS |
|---|---|---|---|---|
| 42.75 (bulk) | 3.15·10⁻¹ | 0.003 | 8.7·10² | **1.48 ± 0.06** |
| 42.00 | 4.89·10⁻² | 0.011 | 7.8·10³ | 1.11 ± 0.07 |
| 41.50 | 1.92·10⁻³ | 0.065 | 2.1·10⁵ | 1.07 ± 0.06 |
| 41.25 (deep tail) | 7.49·10⁻⁵ | 0.381 | 5.3·10⁶ | **1.01 ± 0.04** |

Both findings reproduce cleanly on the second section:

- **N-sufficiency.** N = 10⁵ meets the 5% CoV target down to P_f ≈ 4.9·10⁻²
  comfortably and sits just above it at P_f ≈ 1.9·10⁻³ (CoV = 6.5%,
  N-for-target ≈ 2.1·10⁵ — close to, not far from, the operating N). This is
  consistent with KP58.8's crossing (5% at P_f ≈ 4.7·10⁻³) to within the
  expected section-to-section variation in exactly where the tail begins.
- **Tail-variance decay.** The ladder-mean ratio falls from **1.48 ± 0.06
  (bulk)** to **1.01 ± 0.04 (deep tail)** — reproducing the KP58.8 pattern
  (1.40 → 1.00) point for point, including the bulk value being if anything
  slightly *larger* here (both consistent with each other within ~1σ) and the
  deep-tail value again indistinguishable from parity. Two independent
  sections now agree: LHS's tail advantage vanishes, not just weakens.

This corroborates the verdict above rather than just repeating it: the
bulk-to-tail decay and the C_e×k_aq attribution are section properties of the
transient limit state, not an artifact of one grid or one seed.

## Relationship to ADR-0029

ADR-0029's fm5 study (KP58.8, N = 10⁴, R = 40) and this one agree on the
headline: **no LHS advantage in the deep tail.** This study sharpens the bulk
number — it measures a larger bulk advantage (ladder-mean 1.40 here vs the
single-N 1.13 there), attributable to the current physics (raw heads, C_e =
0.055, Δt = 225 s), the R = 50 replicates, and averaging the N-invariant ratio
over the whole ladder rather than reading it at one N. The tail conclusion is
unchanged, and the two studies are complementary: ADR-0029 additionally
measured the *tilted-IS mitigation* (3.2–4.1× deep-tail CoV cut), which this
study does not re-run but cites as the designated tool.

## Caveats

- Two governing sections (KP58.8, KP60.0; both matrix d_70) at the production
  seed — the only two Tokachi sections where BEP is reachable at HWL. Both
  reproduce the same qualitative structure (bulk advantage decaying to tail
  parity; the static-branch control on KP58.8), so the finding is not a
  one-grid or one-seed artifact. Neither bulk d_70 configs nor KP57.4/KP62.0
  (BEP unreachable at HWL on either) were run; the driver reruns per config in
  ~15–17 min for a further record if wanted.
- The middle-level ratios (KP58.8: 1.07, 1.16; KP60.0: 1.11, 1.07) are within
  ~1–2σ of parity and of each other; the study resolves the *endpoints* (bulk
  ≈ 1.4–1.5, deep tail ≈ 1.0) decisively, not the precise shape of the decay
  between them.
- Ratios use the iid replicate-SE; the ladder-mean ± SE is the reported
  statistic. R = 50 gives a per-rung ratio SE ≈ 1/√49 ≈ 0.14, tightened to
  ≈ 0.04–0.09 by averaging the six N-invariant rungs.
