# BEP Reliability Engine — Model Briefing (prepared for meeting with Joost Pol, 2026-07-06)

This is a full refresher on `bep_reliability_engine`: what each of its nine modules does mechanically, how they hand data to one another, and how every equation traces back to a specific numbered equation in `pol_sie_2024.pdf` (SIE24), `pol_compgeo_2024.pdf` (CG24), or `pol_thesis_2022.pdf` (T22). The last two sections are the actual meeting agenda: where the implementation makes a call Pol's own papers leave open, and concrete questions worth asking him directly.

> **SUPERSEDED (header added 2026-07-31; content unchanged).** Meeting-preparation
> material for the 2026-07-06/07 meeting with Joost Pol, retained as the record
> of what was asked and why. The meeting was held and its outcomes are recorded
> in:
>
> * [`docs/validation/pol-meeting-2026-07-07-dispositions.md`](validation/pol-meeting-2026-07-07-dispositions.md)
>   -- the author-feedback dispositions;
> * **ADR-0026** (C_e field prior), **ADR-0027** (raw erosion head, superseding
>   ADR-0007) and **ADR-0028** (raw static Sellmeijer head).
>
> The model description below therefore predates the raw-head reversal: where it
> describes an r_e-attenuated erosion head, or r_e around 0.6 feeding a piping
> head, that convention was **overturned** by ADR-0027/0028. r_e now drives only
> the uplift/heave gate. Current description: [`docs/architecture.md`](architecture.md).

## 1. What the model computes, in one paragraph

A Monte Carlo fragility engine for the Tokachi/Satsunai levees (Obihiro, Hokkaido): for each of five real cross-sections, it draws N=100,000 stochastic realizations of 7 soil/erosion parameters, runs **every single realization through both** Sellmeijer's static critical-head check (2011) and Pol's time-dependent progression ODE (2024), against d4PDF-derived flood hydrographs at a grid of conditioning river stages, and fits a lognormal fragility curve (P_f vs. stage) to each of the two resulting failure-probability curves. The gap between the static and transient curves — quantified per cross-section — is the thesis's core deliverable, and the retained sample matrix + failure matrices are the handoff to a Phase 2 that Bayesian-filters the transient branch against the fact these levees survived the 2016 typhoon.

## 2. How the modules fit together (data flow)

```
M1 config.py           → Config (validated YAML): geometry, 7 prior specs, MC/timestep/output
                          settings, deterministic Sellmeijer inputs, hydrograph source block
        │
        ▼
M2 sampling.py          → theta_matrix (N×7), LHS-stratified, k_aq–d_70 coupling applied
                          (or skipped, two-population mode) — ONCE, in the main process
        │                 also: sample_seepage_length() → optional (N,) stochastic L, independent draw
        ▼
M3 hydrographs.py       → HydrographRecord per conditioning level: {t, h, peak, native_dt, …}
                          loaded/scaled ONCE per run (canonical d4PDF shape) or synthesized (stub)
        │
        ▼
run.py (orchestrator)   → sweeps the conditioning grid (joblib, one task per level h_i);
                          for each level calls M8.evaluate_batch(theta_matrix, hydrograph_i, geometry)
        │
        ├──▶ M8 evaluator.py  — shared preamble, then branches:
        │        ├─ M6 sellmeijer.py   → H_c, l_c  (same call feeds both branches)
        │        ├─ M4 hydraulics.py   → λ_in, λ_out_eff, r_e (same r_e feeds both branches)
        │        ├─ static branch: Z_static = H_c − r_e·(h_peak − z_toe)          [O(1)]
        │        └─ transient branch: M7 progression.py timestepper              [O(T)]
        │                 └─ M5 initiation.py  → Z_uplift, Z_heave, I_er (called every timestep)
        ▼
run.py aggregates       → two (N, N_h) boolean failure matrices (failure_matrix_stat/tran)
        │
        ▼
M9 fragility.py         → assemble_fragility(): per-column P_f, lognormal fits (Optional),
                          bootstrap bands, Clopper-Pearson CIs → FragilityResult → HDF5 + JSON
```

Two invariants hold this together, both enforced in exactly one place (M8, never re-derived in `run.py`):
- **Shared-sample contract (ADR-0002):** the same θ_j (row j of theta_matrix) and the same computed r_e feed *both* limit states. This is what makes a per-realization static-vs-transient gap physically meaningful instead of sampling noise.
- **Single-source H_c (spec §1/§4):** M6 is called once per realization; the same H_c anchors both the static comparison and the transient equilibrium curve H_eq(l) — except under the one opt-in override described in §3.8.

## 3. Module-by-module walkthrough

### 3.1 M1 — `config.py`: the reproducibility boundary

A frozen (immutable), `extra="forbid"` Pydantic tree — one `Config` object fully determines one run; `config_hash()` is a SHA-256 over the canonical JSON snapshot. Structure: `Geometry` (L, z_toe, foreshore_width, D_fore, k_fore, HWL), `PriorSpecs` (the 7 marginals + optional clip bounds + `d70_interpretation`), `CorrelationSpecs` (the k_aq–d_70 coupling target and mode), `MCSettings` (N, seed, conditioning grid), `TimestepperSettings` (Δt policy, aquifer-lag flags), `OutputSettings`, and an optional `HydrographSource` block (d4PDF data root, river, KP, ordered canonical event IDs). Plus top-level deterministic Sellmeijer knobs: `theta_repose_deg` (37° default), `relative_density_insitu` (0.725 default), `alpha_exponent` (−1/3 default, symmetric — shifts both branches), `alpha_exponent_transient` (None default — the ADR-0017 asymmetric override), `seepage_length_cov` (None ⇒ deterministic L), `foreland_treatment` (`blanketed_tanh` default).

`Geometry.as_evaluator_dict()` emits exactly the 5-key flat dict M8 unpacks: `{L, z_toe, foreshore_width, D_fore, k_fore}` — this is the single frozen handoff shape between config and the evaluator (ADR-0010); `HWL` is carried but has no M8 consumer.

A load-time COV guard (`MAX_COV = 2.0`) catches the "50 vs. 0.50" percentage/fraction unit slip before a multi-hour run wastes compute on garbage priors.

### 3.2 M2 — `sampling.py`: the 7-D Latin Hypercube prior

`PARAM_NAMES = ['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']` is the single canonical column order every downstream module reads by name, never by hard-coded position. `sample_theta()` does, in order:

1. Draw a stratified uniform `(N, 7)` LHS design via `scipy.stats.qmc.LatinHypercube(d=7, seed=seed)`.
2. Map columnwise to independent standard normals, `Z = Φ⁻¹(U)`.
3. **Impose the k_aq–d_70 coupling** (only in `coupling='correlated'` mode): `z'_d70 = ρ·z_kaq + √(1−ρ²)·z_d70`, anchored on k_aq. Because both marginals are lognormal, the log-space target `ρ_log_kaq_d70` *is* the Gaussian-copula correlation directly — no Nataf root-finding needed. This step is **skipped entirely** in the production mode, `coupling='two_population'` (ADR-0012): k_aq and d_70 are sampled fully independent, each retaining perfect one-point-per-stratum LHS stratification.
4. Map each standard-normal column to its physical marginal via lognormal moment-matching: `σ_ln² = ln(1+COV²)`, `μ_ln = ln(mean) − σ_ln²/2`.
5. Optional per-parameter physical clip (`bounds`), logged.
6. Wrap as `ThetaSample(theta_matrix, param_names, metadata)`.

`sample_seepage_length()` is a **separate, standalone 1-D LHS** draw for L (lognormal, mean = `geometry.L`, cov = `config.seepage_length_cov`), seeded independently via `SeedSequence` off the run seed — L is explicitly *not* an 8th θ column, because the thesis treats it as a per-section geometric parameter, not a soil property.

### 3.3 M3 — `hydrographs.py`: river stage series (brief — no Pol-paper counterpart)

Loads d4PDF discharge ensembles, converts to stage via the **Eq. 4.19 rating** `h_t = √(Q_t/a_kp) − b_kp` (a site-specific empirical rating, not from Pol), and resolves the KP→band-workbook mapping. Two paths, config-selected: (1) **canonical d4PDF shape** — one real event's shape is loaded once per run and rescaled per conditioning level, `h(t) = h_base + (h_i − h_base)·shape(t)`, trough pinned at base-flow stage, peak = h_i exactly; (2) **synthetic stub** — a deterministic two-peak raised-cosine placeholder used only for plumbing tests. Produces the `HydrographRecord` M8 consumes structurally (duck-typed) via exactly three fields: `.h` (stage series), `.peak` (static comparator level), `.native_dt` (integration Δt).

### 3.4 M4 — `hydraulics.py`: river stage → aquifer head (the Mazure translation)

Four pure, vectorized kernels plus a stateful lag wrapper:

```python
leakage_length_in(k_aq, D_aq, D_bl, k_bl)               → λ_in  = √(k_aq·D_aq·D_bl/k_bl)
leakage_length_out(k_aq, D_aq, D_fore, k_fore, B_f)     → λ_out_eff = λ_out · tanh(B_f/λ_out)
response_factor(λ_in, λ_out_eff, L)                     → r_e = λ_in / (λ_out_eff + L + λ_in)
translate_instantaneous(h_river, r_e, z_toe)            → h_aq = z_toe + r_e·(h_river − z_toe)
```

This three-term ratio is the *exact* USACE (2000) EM 1110-2-1913 App. B Case 7a form / TAW (2004) Model 4A: `x3/(x1+L2+x3)` with `x1 = λ_out_eff` (finite foreland, tanh-corrected), `L2 = L` (the levee base width — an **exact linear term, never inside a tanh**), `x3 = λ_in` (hinterland, taken semi-infinite). **T22 Eq. 7.13, p. 158** is the special case `r_e = λ/(L+λ)` with no riverside blanket and infinite polder blanket — i.e. `x1 = 0`. Every one of the four θ's feeding λ_in/λ_out (k_aq, D_aq, D_bl, k_bl) is stochastic, so `response_factor` is called **per realization**, never precomputed once. A gated but currently-inactive linear-reservoir lag form also exists (`LaggedHead`, exact exponential update, ADR-0004) behind the same `AquiferHeadModel` protocol as the default `InstantaneousHead` — Phase 1 always uses the instantaneous form.

### 3.5 M5 — `initiation.py`: uplift, heave, and the I_er gate

Three pure, stateless kernels, all consuming the **un-reduced** overpressure `Δh_blanket = h_aq − z_toe` (never the crack-reduced erosion head — enforced by a signature-guard test):

```python
z_uplift(Δh, γ'_bl, D_bl)   = γ'_bl·D_bl/γ_w − Δh              # critical when < 0
z_heave(Δh, γ'_bl, D_bl)    = γ'_bl/γ_w − Δh/D_bl               # critical when < 0
erosion_indicator(uplift_ever, pipe_length_positive, heave_now) = (uplift_ever ∨ pipe>0) ∧ heave_now
```

Sign convention is resistance-minus-load (Z<0 is critical) — the module docstring flags that SIE24's printed Eqs. 8–9 read load-minus-resistance, inconsistent with the papers' own "Z<0" test, so the resistance-minus-load reading was adopted as the only coherent one (ADR-0008). Substituting the Terzaghi gradient `γ'_bl/γ_w` for Pol's independent `i_c,h ~ Ln(0.7,0.1)` makes `z_heave ≡ z_uplift/D_bl` algebraically — both flip sign at the same instant, so `I_er` collapses to `heave_now` alone under the baseline parameterization. The full three-clause gate is kept in the code (not simplified away) because it becomes load-bearing again the moment a sensitivity run decouples i_c,h. The flood-fighting clause of SIE24 Eq. 7 (`t < t_uh + t_ff/I_ff`) is omitted entirely — Phase 1 has no flood-fighting model, so the transient limit state is an unconditional upper bound on failure.

### 3.6 M6 — `sellmeijer.py`: the critical head H_c (single source for both limit states)

```python
H_c = L · F_r · F_s · F_g
F_r = η·(γ'_p/γ_w)·tan(θ)·(D_r/D_r,m)^0.35·(C_u/C_u,m)^0.13·(KAS/KAS_m)^-0.02
F_s = (d_70³/(κL))^-α · (d_70,m/d_70)^0.6         κ = k_aq·ν/g
F_g = 0.91·(D_aq/L)^(0.28/((D_aq/L)^2.8−1) + 0.04)
l_c = 0.5·L·tanh(2·D_aq/L)
```
`compute_critical_head` consumes `k_aq`, `d_70`, `D_aq` from theta and `L` from geometry; `D_bl`, `k_bl`, `gamma_bl_sub`, `C_e` never enter H_c at all — **the static branch has zero C_e exposure by construction** (ADR-0001), which is exactly the point: Phase 2 tightens C_e uncertainty through the transient branch alone. Constants pinned as module-level (not config): `η=0.25` (White's drag), `D_r,m=0.725`, `C_u,m=1.81`, `KAS_m=0.498`, `d_70,m=2.08e-4 m`, `γ'_p=16.87 kN/m³` (basin-wide, deterministic, distinct from the stochastic blanket weight — ADR-0016 split), `ν=1.3e-6 m²/s`. `alpha_exponent` (default −1/3, the 2D Sellmeijer exponent) lives inside `F_s` as `-α`; substituting −1/2 lowers F_s (and hence H_c) at field seepage lengths, matching the 3D scale effect van Beek (2015) describes — this is a repo-added sensitivity hook, not a validated 3D model. `compute_critical_head_vectorized` is the (N,)-array twin used by the production sweep; both raise on any non-finite/non-positive H_c (a config prior-bounding failure, per spec §12 fm2) rather than silently propagating NaN. A self-test at the bottom of the file (`__main__`) hand-verifies F_r/F_s/F_g against the IJkdijk IJkfs01 case from Sellmeijer 2011 §7 / T22 Appendix A.

### 3.7 M7 — `progression.py`: the forward-Euler timestepper

The heart of the transient branch — a serial-in-time, vectorized-across-realizations loop (`integrate_progression`). Per timestep `k`:

```python
h_aq            = head_model.step(h_river[k], dt)                         # (a) M4
Δh_blanket      = h_aq − z_toe                                             # (b)
H_erosion       = Δh_blanket − 0.3·D_bl                                    # (c) crack-reduced, RATE ONLY
uplift_now      = z_uplift(Δh_blanket, γ'_bl, D_bl) < 0                    # (d) M5, un-reduced head
uplift_ever    |= uplift_now                                               # (e) latch, per-event only
heave_now       = z_heave(Δh_blanket, γ'_bl, D_bl) < 0                     # (f,g,h) M5, unlatched
I_er            = erosion_indicator(uplift_ever, l_current>0, heave_now)   # (i) M5
H_eq            = equilibrium_head(l_current, H_c, l_c, L)                 # piecewise-linear, Eq. 11
rate            = 89 · C_e · (k_aq · max(0, H_erosion − H_eq) / L)^0.81 · I_er   # (j) Eq. 5
l_current       = min(L, l_current + dt·rate)                              # forward Euler, absorbing at L
```
`equilibrium_head` implements the three-anchor piecewise-linear curve `(0,0), (l_c,H_c), (L, 0.9·H_c)` via `np.where` over the two segments (not `scipy.interpolate`, because the breakpoints (l_c, H_c) differ per realization and must broadcast). An internal assertion (`l_next >= l_current`) enforces the monotone-non-decreasing pipe-length invariant at every step — this is what makes the "staircase" trajectories through inter-peak troughs correct rather than a bug: dl/dt is a positive-part operator, so there is no mechanism for l to shrink. `d_bl_m = 0` is a valid degenerate input representing no-blanket laboratory box experiments (the B25-245 replay in the test suite): the crack term vanishes and the heave gradient division is guarded to avoid NaN. `scipy.integrate.solve_ivp` is explicitly banned here (spec §10) — adaptive step-size control fights the I_er on/off discontinuities; forward Euler is what Pol himself used.

### 3.8 M8 — `evaluator.py`: shared preamble, then branch

`evaluate_realization` (scalar, the frozen Phase 2 import surface) and `evaluate_batch` (vectorized, N-at-once — proven bit-identical to looping the scalar version, `test_orchestration_matches_reference_loop`) both do:

1. **Shared preamble, once:** `compute_critical_head(theta_row, geometry)` → `H_c, l_c`; then `leakage_length_in`, `leakage_length_out`, `response_factor` → `r_e`. (If `alpha_exponent_transient` is set, a **second** M6 call recomputes a separate `H_c_transient` at that exponent — the one place the single-source-H_c rule is deliberately relaxed, ADR-0017; by default `H_c_transient == H_c`, bit-identical.)
2. **Static branch (O(1)):** `Z_static = H_c − r_e·(h_peak − z_toe)`; `failure_static = Z_static <= 0`. Gross peak head, **no** 0.3·D_bl reduction.
3. **Transient branch (O(T)):** builds an `InstantaneousHead(r_e, z_toe)` (the *same* r_e as step 1) and calls `integrate_progression`, passing `H_c_transient` as the H_eq anchor. `Z_transient = L − l_e_final`; `failure_trans = Z_transient <= 0`.

Both branches share θ_j and r_e (ADR-0002) but deliberately use **different driving heads**: the static comparator is the gross peak head with no crack-resistance reduction; the transient rate uses the 0.3·D_bl-reduced `H_erosion`, and the transient gate uses the un-reduced `Δh_blanket`. This head-convention asymmetry between the two branches is one of the four named components of the static-transient gap (§5, item 3 below) — it is not accidentally absorbed anywhere. `EvaluationResult` (the frozen dataclass) carries both Z's, `H_c`, `H_c_transient`, `l_c`, `λ_in`, `r_e`, `t_uh`, both failure flags, and the uplift/heave latches — this exact field set and the `evaluate_realization` signature are what Phase 2's Accept-Reject filtering re-runs against the 2016 hydrograph.

### 3.9 `run.py`: the orchestrator (no physics)

Three nested loops (spec §3), mapped onto the built modules: **outer** = conditioning levels (parallel via `joblib`, one task per level); **middle** = the N realizations (one vectorized `evaluate_batch` call per level, not a Python loop); **inner** = timesteps (irreducibly serial, lives entirely inside M7, invisible here). Sequence: sample θ once and (optionally) L once in the main process → for each level, build that level's `HydrographRecord` (main process, no RNG) → dispatch `evaluate_batch` to a worker → aggregate the two `(N, N_h)` boolean matrices by `level_index` (so results are invariant to task completion order) → write a `.raw.h5` crash-recovery payload → call `assemble_fragility` → persist the final `FragilityResult`. Reproducibility across `n_jobs` holds *by construction*: every RNG draw is front-loaded into the main process before the parallel region, and every per-(level, realization) evaluation is a pure deterministic function.

### 3.10 M9 — `fragility.py`: fitting, uncertainty, and persistence

`assemble_fragility` takes the two raw `(N, N_h)` boolean matrices and, per branch (static/transient) independently:

1. Per-column failure fraction → `P_f_raw` (the Monte Carlo point estimate).
2. **Lognormal fit** in probit space, anchored at the datum `z_toe`: `P_f(h) = Φ((ln(h−z_toe)−μ)/σ)`, fit by weighted least squares on `Φ⁻¹(P_f)` vs. `ln(h−z_toe)` (a straight line for a true lognormal curve), with inverse-variance probit weights from the delta method so a P_f carried by 1–2 failing realizations doesn't dominate the fit. Requires ≥2 interior (0<P_f<1) points; **returns `None` rather than raising** if not (ADR-0024) — a completed sweep is never discarded for want of a fit.
3. **Bootstrap bands:** 1000 replicates, each resampling realization rows with replacement (applied identically to both matrices, preserving the shared-sample structure) and refitting; degenerate replicates are skipped and counted, not fatal.
4. **Clopper-Pearson exact binomial CIs**, always computed on the raw points regardless of whether a fit exists.
5. A data-driven **deliverable-form flag** per branch (ADR-0024): if `max(P_f_raw) >= 0.5` (the grid brackets the transition) and a fit exists → `fitted_lognormal` is the deliverable; otherwise → `raw_tail_binomial` (the raw points + CIs) is the deliverable, explicitly **not a fallback** — a transient P_f that stays low across every attainable flood stage is itself the substantive finding for that cross-section (this is KP62.0's situation: no attainable d4PDF stage reaches its transient transition).

`FragilityResult` (the frozen Phase 2 payload) retains the full `theta_matrix` and *both* failure matrices — non-negotiable, since Phase 2 needs to re-run `evaluate_realization` row-by-row against the 2016 record. Persisted as one HDF5 file (arrays + fitted μ/σ as root attrs, NaN-encoded when the fit is `None`) plus a JSON metadata sidecar (config snapshot, sampling provenance, the ADR-0006 leakage-geometry record, MC convergence CoVs, the fragility-deliverable flags). `upscale_length_effect` (the weakest-link segment transform `P_f,BEP = 1−(1−P_f,cs)^n_eff`) is implemented but **not called anywhere** — `n_eff = L_seg/λ_ac` needs an autocorrelation length that hasn't been estimated yet.

## 4. Every governing equation against Pol's papers

| Repo quantity | Formula | Pol source |
|---|---|---|
| H_c (critical head) | `L·F_r·F_s·F_g` | SIE24 Eq. 12 = T22 Eq. 2.7–2.10 = Sellmeijer 2011 formula [6] |
| l_c (critical pipe length) | `0.5·L·tanh(2·D_aq/L)` | SIE24 "Eq. 13" |
| r_e / leakage lengths | `λ_in/(λ_out_eff+L+λ_in)` | **T22 Eq. 7.13, p.158** (SIE24 treats r_e as fixed input 0.6 — no derivation there) |
| Progression rate dl/dt | `89·C_e·(k_aq·(H_erosion−H_eq)/L)^0.81` | SIE24 Eq. 5 = CG24 Eq. 15 = T22 Eq. 5.18/6.5 |
| Crack-resistance reduction | `H_erosion = Δh_blanket − 0.3·D_bl` | SIE24 Eq. 6 (cites TAW 1999 / Schweckendiek 2014 — never derived by Pol) |
| Equilibrium head H_eq(l) | piecewise `(0,0),(l_c,H_c),(L,0.9H_c)` | SIE24 Eq. 11 = T22 Eq. 6.10 |
| Uplift | `γ'_bl·D_bl/γ_w − Δh_blanket` | SIE24 Eq. 8 = T22 Eq. 6.7/7.14 |
| Heave | `γ'_bl/γ_w − Δh_blanket/D_bl` | SIE24 Eq. 9 = T22 Eq. 6.8 |
| I_er gate | uplift-latch ∧ heave (flood-fight clause omitted) | SIE24 Eq. 7 = T22 Eq. 6.6 |
| No-recovery pipe length | `r_l = 0`, monotone l | SIE24/T22 base case (own field-evidence review, T22 §2.2.2, finds no recovery data) |

## 5. Where the repo makes a call Pol's papers leave open

SIE24 runs one generic reliability base case; the repo runs five real, data-constrained Tokachi cross-sections, which forced several decisions Pol's own reliability paper didn't have to make:

1. **r_e: fixed 0.6 → stochastic, per-realization, geometry-derived** (M4, §3.4). The single largest structural expansion — an entire module built around the one equation (T22 Eq. 7.13) that SIE24 uses as a constant.
2. **H_erosion applies the crack loss after r_e-translation**, not on raw river stage as SIE24 Eq. 6 literally reads (M7, §3.7; ADR-0007) — the two coincide only where r_e=1.
3. **Terzaghi heave-gradient substitution** collapses `I_er ≡ heave_now`, dropping Pol's independent `i_c,h ~ Ln(0.7,0.1)` and his uplift-sustain hysteresis window (M5, §3.5; ADR-0008).
4. **α = −1/3 (2D) is the shared default**, matching Sellmeijer/SIE24, but CG24 itself finds 3D DgFlow scale effect is α≈−1/2 — a repo-added `alpha_exponent_transient` hook (M6/M8, ADR-0017) isolates this as a controlled sensitivity rather than silently living with one exponent for both branches.
5. **H_eq-conservatism, quantified.** Pol's own 0.9·H_c end anchor (explicitly called conservative in both papers) was measured against CG24's own L=3m DgFlow case to inflate the progressive-phase rate by ≈1.95× there. Whether this holds at field scale (tens of meters) is open.
6. **l_c under-predicts** measured/DgFlow critical pipe length by ~1.5–2.2× in every 3D case checked.
7. **Shape-invariant climate axis** (ADR-0023) — a repo-original empirical d4PDF finding, no Pol counterpart: +4K events aren't longer/more compound, only higher-peaked, so the +4K fragility curve is bit-identical to historical by construction.

## 6. Questions for Pol — self-contained, full context included

These are written to be asked verbatim, with no additional setup needed — each restates the relevant equation(s), the specific numeric conflict or open point, and why it matters for this implementation.

### Q1. Which C_e prior is right for a reliability analysis, and is the B25-245 calibrated value 0.010 or 0.014?

My engine implements your progression-rate ODE `dl/dt = 89·C_e·(k_aq·(H−H_eq)/L)^0.81` (SIE 2024 Eq. 5 = CG 2024 Eq. 15 = thesis Eq. 5.18/6.5), and C_e is one of my seven stochastic Monte Carlo input variables — its prior distribution directly controls how fast pipes grow across my whole 100,000-realization sample, so getting the prior right matters a lot. I've found two different C_e values in your own work and want to reconcile them:

- **SIE 2024, Table 2** (the base case of your reliability-analysis paper) specifies the prior `C_e ~ Lognormal(mean = 0.055, std = 0.043)`.
- **CG 2024** (the calibration paper), Table 1, reports *experiment-calibrated* C_e values: 0.012 (B25-232), 0.010 (B25-245), 0.030 (B25-248), 0.018 (FS35-238), 0.007 (FS35-240), 0.018 (FS35-242), and 0.014 for the large-scale FPH experiment — stated in text as "0.007 < C_e < 0.030 (average: 0.016)" for the small-scale tests and 0.014 for FPH.

I built my prior as `C_e ~ Lognormal(mean = 0.014, COV = 0.50)`, anchored on your calibrated values (close to the FPH large-scale result) rather than on your own reliability paper's base-case prior, whose mean is roughly 4× higher. **Question:** why does the reliability paper's own base case use a prior with a mean around 4× your calibrated values — is that a deliberate uncertainty inflation for the reliability context (e.g. to cover scale-up or field uncertainty beyond what the lab/FPH calibration captures), a different/earlier calibration basis, or should I actually be using something closer to 0.055 rather than 0.014 for a real reliability run?

Separately, there's an internal inconsistency in CG 2024 itself I'd like resolved: Table 1 lists the calibrated C_e for B25-245 as 0.010, but the Fig. 5 caption — which shows the B25-245 head-profile and pipe-length comparison — states the parameters used as "(i_tip,c = 0.9, η = 0.3, C_e = 0.014)". Which value is actually correct for B25-245, 0.010 or 0.014?

### Q2. Does the equilibrium-head end-anchor's conservatism (measured at ≈1.95× at L=3m) hold at field scale (tens of meters)?

Your progression ODE needs an equilibrium head curve H_eq(l), which you define (SIE 2024 Eq. 11 = thesis Eq. 6.10) as piecewise-linear through three anchor points: `H_eq(0)=0`, `H_eq(l_c)=H_c`, and `H_eq(L) = 0.9·H_c`. Both papers describe this 0.9·H_c end anchor and the two straight segments as "a conservative estimate based on equilibrium curves following from the numerical simulations" (i.e. your DgFlow FEM runs in CG 2024).

I cross-checked this against your own CG 2024 L=3m DgFlow case (the S2-2 simulation) by extracting the effective post-critical equilibrium head implied there, and found it sits at roughly H_eq/H_c ≈ 1.01–1.04 — not 0.9. Because the progression rate depends on `(H − H_eq)^0.81`, using the lower, conservative 0.9·H_c anchor instead of the ~1.0–1.04 value your own simulation implies inflates the computed progressive-phase pipe-growth rate by a factor of roughly 1.95× at that L=3m case (I confirmed this by direct, time-step-converged numerical integration, holding every other input fixed — it's not a hand estimate).

My cross-sections have field seepage lengths on the order of 40-70 m (vs. the 3-30 m DgFlow validation range). **Question:** does this ≈2× conservatism in the 0.9·H_c anchor persist, grow, or shrink as seepage length scales up to tens of meters? Do you have (or know of) DgFlow simulations at larger L that would let me calibrate a less conservative, or explicitly scale-dependent, end-anchor for a field-scale reliability run, instead of applying the same 0.9 factor derived from lab/L=3-30m-scale simulations uniformly across all my cross-sections?

### Q3. Is the l_c formula's 1.5-2.2x under-prediction (vs. 3D DgFlow) a known limitation, and is there a 3D-calibrated alternative?

I use your critical-pipe-length formula `l_c = 0.5·L·tanh(2·D_aq/L)` (SIE 2024, "Eq. 13"), which you state "agrees well with 2D numerical piping model simulations such as those from Sellmeijer (2006) and Rosenbrand et al. (2022)." This l_c value is the breakpoint of my H_eq piecewise curve above — it's where H_eq transitions from rising (0 to H_c) to falling (H_c to 0.9·H_c), so it directly controls when the progression rate stops accelerating and starts leveling off.

When I checked this formula against the 3D DgFlow hole-exit simulation cases reported in CG 2024, the tanh formula under-predicts the measured/simulated critical pipe length by roughly a factor of 1.5 to 2.2 in every 3D case I could verify — i.e. the real (3D, hole-type-exit) critical pipe length is substantially longer than the 2D formula predicts. **Question:** are you aware of this 2D-formula-vs-3D-simulation gap in l_c? Is there an updated or 3D-calibrated version of this formula, or a correction factor you'd recommend, for a hole-type-exit failure mode (which is the relevant BEP failure mechanism for a real field levee, as opposed to the 2D plane-strain assumption the tanh formula was fit to)?

### Q4. Which scale exponent (2D −1/3, 3D DgFlow −1/2, or the −0.2 to −0.45 experimental band) should I use for a field-scale confined aquifer?

Your critical-head formula's scale factor F_s carries an exponent on the dimensionless group `d_70³/(κL)`, which in the classical 2D Sellmeijer formulation (Sellmeijer 2011 formula [6], reproduced in SIE 2024 Eq. 12) is α = −1/3. However, in CG 2024 you report that your 3D DgFlow simulations show "a stronger scale effect: α ≈ −1/2 instead of α = −1/3 as obtained for pipe progression in 2D." You also cite Van Beek (2015) and Allan (2018) hole-exit experiments that bracket a weaker effect, −0.45 < α < −0.2, than either the 2D or your 3D-model value.

So there are three different scale exponents in play across your own body of work: the classical 2D value (−1/3), your 3D numerical-model value (−1/2), and the physical hole-exit experimental band (−0.2 to −0.45). I've built my model so I can run the static comparator at the baseline −1/3 while recomputing a separate transient critical head at a different exponent (e.g. −1/2), specifically so I can isolate this "2D-vs-3D dimensional" effect from the purely time-dependent effect I'm actually trying to study. **Question:** for a field-scale (tens-of-meters seepage length), confined-aquifer BEP failure mode like the one at my Tokachi cross-sections, which of these three exponents would you actually recommend trusting, and does the right choice depend on whether the real failure mode at the site is expected to be a hole-type or plane-type exit?

### Q5. What is the correct interpretation of the flood-fighting term `t_ff/I_ff` in the I_er indicator when flood fighting fails?

Your erosion indicator (SIE 2024 Eq. 7 = thesis Eq. 6.6) is defined as `I_er(t) = (min_{0..t}[Z_u(t)] < 0 ∪ l_ini > 0) ∩ (Z_h(t) < 0) ∩ (t < t_uh + t_ff/I_ff)`, where `t_uh` is the first time uplift, heave, and erosion co-occur (your sand-boil proxy), `t_ff` is the time required for organized flood fighting to succeed, and `I_ff` is an indicator equal to 1 if flood fighting succeeds and 0 if it does not. The printed text in SIE 2024 appears to state that when `I_ff = 0`, the term "becomes 1" — which reads oddly to me, since dividing by zero should mathematically send the term to infinity (meaning: no time cutoff at all, i.e. erosion is never suspended by this clause if flood fighting never succeeds).

My implementation omits this entire third clause: I have no flood-fighting model in this phase of the project, so my erosion indicator is just the first two clauses (the uplift latch AND the heave condition), which makes my transient limit state an unconditional upper bound on the failure probability — no credit is given for successful operational intervention. **Question:** can you confirm the intended reading of `t_ff/I_ff` when `I_ff = 0` — should this term go to infinity (no time limit, consistent with my reading), or is there a genuine, different "becomes 1" special case intended, and if so, what is its physical meaning? I want to confirm that dropping the whole clause, as I've done, is a safe conservative simplification and not a place where I'm missing some other essential piece of the indicator's logic.

### Q6. Should the crack-resistance head loss (0.3·D_bl) be applied to the raw river level, or to the r_e-attenuated aquifer head at the toe?

Two of your equations combine in a way I had to make an explicit choice about. Eq. 6 (SIE 2024) defines the erosion-driving head as `H = h − h_e − 0.3·D_bl`: the raw outer (river) water level `h`, minus the polder exit-point level `h_e`, minus a fixed head loss of `0.3·D_bl` representing resistance in the crack/vertical pipe through the blanket (a convention you cite to TAW 1999 / Schweckendiek et al. 2014, not derived in your own papers). Separately, Eq. 10 (SIE 2024) defines the aquifer head actually arriving at the landside levee toe as `u_it(t) = h_e + r_e·(h(t) − h_e)` — i.e. the raw river level is attenuated by the response factor r_e before it reaches the toe.

In my implementation I compute the erosion-driving head as `H_erosion = r_e·(h − h_e) − 0.3·D_bl` — i.e. I apply the 0.3·D_bl crack-resistance loss *after* the r_e attenuation, to the aquifer head that's actually present at the exit point, rather than subtracting it directly from the raw, un-attenuated river level `h` as Eq. 6's literal wording would suggest. My reasoning: physically, the head available to drive erosion at the exit point is whatever head has actually arrived there (the r_e-translated aquifer head), and the local crack-resistance loss should be subtracted from that arrived head, not from the far-field river stage. This matters concretely in my model because, unlike your reliability paper (where r_e is a fixed input of 0.6, Table 2), I treat r_e as a fully stochastic, per-realization quantity that can range well below 1 depending on sampled aquifer/blanket properties — so the two orderings (crack loss on raw h vs. crack loss on r_e-translated h) can diverge substantially. **Question:** do you agree this re-ordering (applying the crack-resistance loss after the aquifer-head translation, not to the raw river level) is the physically correct reading, or does Eq. 6's literal form implicitly assume r_e = 1 (i.e., only strictly valid in a parameterization where the aquifer response factor isn't separately modeled)?

## 7. Build state

All nine modules + orchestrator + persistence are implemented and tested (`pytest` green). The one explicitly unwired piece: `fragility.upscale_length_effect` (the weakest-link segment transform) exists but is never called — it needs an autocorrelation length λ_ac that hasn't been determined yet. Everything else described above is live production code, not a scaffold.
