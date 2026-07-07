# ADR-0029: M7 Timestepper Acceleration (numpy fast path + opt-in Numba) and the Tilted Importance Sampler for the Deep Tail

Date: 2026-07-07
Status: Accepted

## Context

Two performance/estimation questions were opened together because they gate
the same deliverables (the per-section production sweeps, the Δt/2 and
sensitivity re-runs after ADR-0026/0027/0028, and the spec §12 fm5
verification study):

1. **Sweep wall-clock.** A full N = 10⁵ × 29-level KP58.8 sweep (canonical
   d4PDF path) was profiled at 70 s serial: **46 s (66%) in the M7
   timestepper** (`integrate_progression` via `evaluate_batch`), 19 s (27%)
   in the M9 bootstrap, 5 s loading the canonical band workbook. Inside the
   timestepper, one production level (N = 10⁵, T = 192 hourly steps) cost
   ~1.45 s: 0.47 s in `progression_rate` (dominated by the fractional power
   `x**0.81`, evaluated for *all* N at *every* step even where the I_er gate
   is closed), 0.39 s of per-step loop body (`np.where`/`minimum`/latches),
   0.25 s in `equilibrium_head` (re-deriving time-invariant slopes each
   step), 0.26 s in `z_uplift`+`z_heave` (re-deriving time-invariant
   thresholds each step). The M4/M6 preamble is negligible (< 3%).
2. **Tail estimation.** Spec §12 fm5 flags that the deep transient failure
   tail is governed by the multiplicative C_e×k_aq interaction (fm7), which
   LHS — a marginal-stratification scheme — does not stratify. The claimed
   LHS tail-variance advantage over crude MC was explicitly *unverified*,
   and the spec asks for a variance-reduction scheme "targeted at the joint
   tail (importance sampling or subset simulation)" for the lowest
   conditioning levels, with "the sampler interface open to substitution".

Hard constraints honored throughout: forward Euler exactly as Pol uses it
(spec §10 — no `solve_ivp`); strict SI kernels; the scalar
`evaluate_realization` signature and `EvaluationResult` field set are a
frozen Phase 2 contract (`tests/test_evaluator_phase2_surface.py`); and
`evaluate_batch` must stay bit-identical to looping the scalar path
(`tests/test_run.py::test_orchestration_matches_reference_loop`).

## Decision

### 1. Default engine: restructured numpy timestepper, bit-identical

`integrate_progression` keeps its signature and its numpy character but the
loop body is restructured with three transformations, each **provably
value-preserving** (same operands, same operation order, same IEEE
rounding):

- **Hoisted time-invariant subexpressions** — `0.3·D_bl`, the z_uplift
  resistance `(γ'·D_bl)/γ_w`, the z_heave critical gradient `γ'/γ_w`, the
  rate coefficient `89·C_e`, and the H_eq falling slope
  `(0.9−1)·H_c/(L−l_c)` — computed once instead of once per timestep.
- **Gate-masked fractional power** — `x**0.81` is evaluated only where
  `I_er ∧ (overload > 0)`; elsewhere the power is exactly `+0` anyway
  (IEEE `pow(+0, 0.81) = +0`, and the I_er gate zeroes the rest), so a
  zero-filled `np.power(..., where=...)` reproduces the original chain bit
  for bit while skipping the pow on the (typically dominant) inactive
  fraction.
- **Whole-step skip below z_toe** (instantaneous head model only, `type is
  InstantaneousHead`, never at step 0): when `h(t) ≤ z_toe`, monotone IEEE
  rounding gives `Δh_blanket ≤ 0`, neither gate can fire, latches/t_uh are
  untouched and `dl = 0` — the step is a no-op and is elided. Lagged head
  models never skip (their state must advance every step).

The M5/M6 kernels (`z_uplift`, `z_heave`, `equilibrium_head`,
`progression_rate`) remain the documented single sources; the loop inlines
them, and `tests/test_progression_fastpath.py` pins **exact bitwise
equality** against a verbatim reference loop over the public kernels across
batch/scalar shapes, sub-toe troughs, D_bl = 0, l_ini > 0, stochastic L, and
the lagged model. `evaluate_batch` ↔ scalar-loop bit-identity is therefore
untouched (both routes flow through the same restructured function).

### 2. Opt-in backend: Numba kernel, `< 1e-10` equivalence, config-recorded

`progression_numba.integrate_progression_numba` is a
`@njit(parallel=True, cache=True, error_model="numpy")` kernel with the loop
nest swapped — realizations outer (`prange`), time inner — so each
realization's state stays in registers and the whole level is one pass over
memory. Selected via **`config.timestepper.progression_backend =
'numba'`** (default `'numpy'`; threaded `run.py → _EvalSettings →
evaluate_batch`), never via the frozen scalar API. Numba ships as the
optional `[accel]` extra; requesting the backend without it raises with the
install hint.

**Bit-identity caveat (why it is opt-in and config-owned).** The kernel's
per-element arithmetic matches the numpy chain operation for operation, so
every add/sub/mul/div/min/max and every gate comparison rounds identically;
the single non-reproducible operation is `x**0.81` (numpy's pow loop vs the
LLVM-lowered platform `pow`), which may differ in the last ulp. The
contract, proven by `tests/test_progression_numba.py`, is: floats within
1e-10, booleans/latches/t_uh exactly equal (the gate logic is power-free, so
latch timing cannot drift). Because the backend *can* change bits, it lives
in Config — one config fully determines one result — and is stamped into
`metadata['progression_backend']` (plus the config snapshot), so a numba
result can never masquerade as the numpy reference. Empirically, on the
development machine (Windows/ucrt), the deviation observed at N = 10⁵ over
the full KP58.8 grid was **exactly 0.0** with zero failure-flag mismatches —
the caveat is contractual headroom for other platforms/toolchains, not an
observed error. Restrictions, both enforced: instantaneous head model only
(config refuses `numba` + `aquifer_lag_active`), no trajectory storage
(numpy path only).

### 3. JAX rejected, now with measurements

Spec §10 already listed JAX under "Avoid". A standalone `lax.scan` float64
kernel of the same math confirms the rejection empirically (N = 10⁵,
T = 192, CPU): 0.235 s vs Numba's 0.042 s (5.6× slower), deviation from the
numpy path 5.5e-07 — four orders of magnitude outside the 1e-10 equivalence
bound (XLA fuses/reorders and substitutes its own transcendental
implementations, so the deviation is not reducible to a pow-ulp) — and
current JAX releases require numpy ≥ 2.0 against the project's
`numpy>=1.26,<2.0` pin. No autodiff/GPU benefit exists for this workload.

### 4. Deep-tail estimator: Z-space tilted importance sampling, not subset simulation

`tail_sampling.sample_theta_tilted` is the substitutable sampler of spec
§12 fm5: the exact M2 pipeline (LHS design → Φ⁻¹ → copula → marginal map →
fm2 bounds clip) with an optional mean shift ν per parameter applied to the
**independent standard-normal columns, upstream of the copula**, and the
exact log-likelihood ratio `log w = Σ(−ν·z′ + ν²/2)` returned alongside.
Because the tilt lives in Z-space and everything downstream (copula,
lognormal map, bounds clip) is a deterministic transform applied identically
under prior and proposal, the weights are exact in all pipeline modes —
correlated or two-population coupling, with or without bounds, LHS or iid.
Targeting is the fm7 interaction direction `{k_aq, C_e}` (for a lognormal
marginal a Z-shift ν is a physical scale factor `exp(ν·σ_ln)`), with the
shift chosen by one cross-entropy step from a pilot
(`cross_entropy_shift`). The estimator (`importance_estimate`) is the
unbiased non-self-normalized `P̂_f = (1/N)Σ w·I` with iid SE, CoV, and the
Kish effective failure size as the degeneracy diagnostic. With zero shift
the sampler reproduces M2 `sample_theta` **bit for bit** (stratified,
two-population) or degrades to the spec §13 crude-MC debug fallback
(`stratified=False`) — both pinned by `tests/test_tail_sampling.py`.

Subset simulation was considered and rejected: its adaptive MCMC levels
would break the engine's front-loaded-RNG reproducibility-by-construction
(spec: parallel ≡ serial because all stochasticity precedes the sweep), sit
awkwardly with the fixed (N, N_h) failure-matrix contract, and buy
generality the problem does not need — the transient limit state is monotone
in both C_e and k_aq (each enters the Pol rate multiplicatively), so a
mean-shift proposal along exactly that direction is well-posed and one-shot.

**The production sweep is unchanged.** Phase 2's Accept-Reject filtering
needs the plain LHS prior θ-matrix and unweighted failure matrices (spec §2,
§8 — non-negotiable), and ADR-0024's binomial CIs assume unweighted
indicators. The tilted sampler is a *tail estimator* for the lowest
conditioning levels and for the fm5 study — a supplement, never a
replacement population.

### 5. fm5 verification study

`scripts/tail_variance_study.py` runs the empirical study the spec demands:
replicate CoV of P̂_f for LHS vs crude MC vs CE-tilted IS at the reduced
operating N = 10⁴ on the real KP58.8 physics (canonical d4PDF path), at
levels spanning bulk → P_f ~ 10⁻⁴. Results:
`docs/decisions/adr0029-tail-cov-study.json`, figure
`docs/figures/adr0029-tail-cov.png`, full findings in the companion note
`docs/decisions/adr0029-tail-variance-study.md`. Verdict: **the naive LHS
tail-variance claim is refuted — the fm5 caveat is confirmed.** LHS shows a
real but modest CoV advantage in the bulk (MC/LHS ≈ 1.13 at P_f ≈ 0.28,
and it beats its own binomial prediction there) but **no detectable
advantage anywhere in the failure tail** (MC/LHS = 0.79–1.08 ≈ 1 within
replicate noise for P_f ≤ 1.6·10⁻², where its CoV matches the iid binomial
formula), while the CE-tilted IS cuts the deep-tail replicate CoV 3.2–4.1×
versus both (≈ 10–17× sample efficiency) and eliminates the ~30% of
unweighted replicates that observe zero failures at P_f ≈ 10⁻⁴. Raw sweep
tail points therefore carry crude-MC-grade uncertainty — the ADR-0024
Clopper–Pearson presentation is exactly right for them — and sub-decade
tail quantification belongs to the tilted estimator.

## Measured results (KP58.8, N = 10⁵, T = 192, 29 levels, serial)

| Stage | per mid-grid level | full sweep |
|---|---|---|
| pre-ADR-0029 numpy | 1.45 s | 46.3 s |
| restructured numpy (default, bit-identical) | 0.41 s | 10.3 s |
| numba backend (opt-in, < 1e-10) | 0.025 s | 2.7 s |

Sweep speedup: **4.5× by default with zero numerical change; 17× opt-in.**
End-to-end (load + sample + sweep + M9), 70 s → ~27 s with numba, at which
point the **M9 bootstrap (19 s, a 1000-replicate Python loop) is the next
bottleneck** — out of scope here, noted for a follow-up.

## Consequences

- Sensitivity/re-sweep campaigns (ADR-0026/0027/0028 re-runs, Δt/2
  convergence runs, the ADR-0017 decomposition) get the default 4.5× free;
  campaigns that opt into numba must carry the backend marker in their
  metadata (automatic via the config snapshot) and cannot be diffed
  bit-for-bit against numpy runs (only to < 1e-10 / identical flags).
- `progression_numba.py` duplicates the loop math by necessity (nopython
  cannot call the numpy kernels); the cross-backend equivalence test is the
  drift guard that keeps the copy honest, exactly as the fastpath drift
  guard keeps the inlined numpy loop honest against the public kernels.
- Adding the `progression_backend` field changes `config_hash` for
  regenerated configs (defaults-only change; the generated YAMLs on disk
  are untouched and still validate).
- The lag form, if ever activated (ADR-0004/0014), runs numpy-only until
  the exact exponential update is added to the kernel; config enforces this
  fail-fast rather than silently dropping the lag.
- Tail P_f numbers quoted below the grid's raw-resolvable range must come
  from the tilted estimator with its n_eff diagnostic reported, and are
  clearly weighted estimates — they never enter FragilityResult failure
  matrices or the ADR-0024 binomial CIs.

## References

- Spec §6 (vectorization; the Numba note), §10 (package do/don't list),
  §11 (CoV convergence target), §12 fm5/fm7, §13 (LHS + crude-MC fallback).
- Profile and benchmarks: this ADR §Context and §Measured results
  (2026-07-07, Windows 11 / Python 3.11 / numpy 1.26.4 / numba 0.61 /
  jax 0.4.30 CPU).
- Owen, *Monte Carlo theory, methods and examples*, ch. 9 (exponential
  tilting); Rubinstein & Kroese, *The Cross-Entropy Method*.
- Au & Beck (2001) — subset simulation (considered, rejected here).
- Companion note: `adr0029-tail-variance-study.md`;
  data `adr0029-tail-cov-study.json`; figure
  `docs/figures/adr0029-tail-cov.png`.
