# Phase 1 Computational Architecture: Time-Dependent BEP Reliability Engine

## Authoritative Specification for Implementation

---

## 0. Framing and Architectural Principles

This document is the complete specification for the Phase 1 computational engine. It supersedes prior drafts and incorporates all decisions reached through prior discussion: the seven-dimensional stochastic parameter vector with C_e as a random variable (prior amended by ADR-0026), LHS as the sampling strategy throughout, the shared-sample contract between static and transient limit states, the k_aq–d_70 coupling question (resolved empirically as the two-population decoupling, ADR-0012), the separation of the raw piping heads from the r_e-attenuated uplift/heave head (ADR-0027/ADR-0028), the lag-capable hydraulic-translation interface gated by the aquifer-response diagnostic (executed 2026-07-11: instantaneous retained, ADR-0032), and the explicit handoff design for Phase 2 Bayesian filtering.

> **Revision note (2026-07-07; re-reconciled 2026-07-12 through ADR-0033; 2026-07-22 through ADR-0046; 2026-07-28 through ADR-0048; 2026-07-30 through the two non-numbered companion notes `epistemic-bracket-synthesis.md` and `adr0040-hwl-bias-resolution.md`).** This text has been reconciled with the accepted ADRs 0001–0048 (`docs/decisions/`). Every superseding decision through ADR-0033 — notably the raw-head reversal (ADR-0027/0028, superseding ADR-0007), the C_e field prior (ADR-0026), the two-population coupling (ADR-0012), the γ' split (ADR-0016), the shape-invariant climate axis (ADR-0023), the per-branch fragility deliverable (ADR-0024), the M7 acceleration / tail estimator (ADR-0029), the 225 s integration timestep (ADR-0030, superseding ADR-0022 decision 1), the two-section N-sufficiency verification and LHS tail verdict (ADR-0031), the executed aquifer-response diagnostic with the instantaneous verdict (ADR-0032), and the variance-based GSA (ADR-0033) — is folded into the prose and pseudocode below. The 2026-07-22 pass folds in ADRs 0034–0046: the built Phase 2 Accept-Reject package (ADR-0034/0035/0036 — the additive `evaluate_batch_diagnostics` twin, the 2016 stage anchoring, and the replay on the run's own 225 s grid superseding ADR-0022 decision 2), the length effect wired-but-OFF at λ_ac = 250 m / n_eff = 1 (ADR-0037), the Phase 3 `system_integration` package (ADR-0038), the executed worst-case Δt stress test (ADR-0039), the Stage 6.6 static–transient gap decomposition and its `equilibrium_end_factor` isolation (ADR-0040/0041), the Uemura surface-curve re-execution and section table (ADR-0042/0043), the event-set closure at 2016 (ADR-0044), the optional Sellmeijer model factor m_p (ADR-0045), and the z_toe datum epistemic sensitivity (ADR-0046). A 2026-07-28 pass folds in ADR-0047 (DEM-surveyed seepage length L — measured and recorded; **adopted at KP 62.0 alone on 2026-07-29**, `L_m` 47.0 → 40.0 m, with KP 57.4/58.8/60.0 held and their DEM values carried as an unadopted bracket — the "not adopted" wording first written here belongs to the 2026-07-28 measurement pass and is superseded) and ADR-0048 (prior-mean epistemic scenarios: the optional `config.prior_mean_scenario`, default OFF and hash-preserving, carrying the k_aq field-test-vs-Form-5 bracket and the gamma'_bl in-situ lower bound; **no production prior mean changed**). Where a future ADR and this text conflict, the ADR governs and this text must be re-reconciled.

Four structural properties shape every downstream choice and warrant being stated upfront.

**Property 1, asymmetric limit state cost.** The static limit state is scalar-in, scalar-out per realization: sample θ, compute H_c via Sellmeijer, compare against the raw gross peak head h_peak − z_toe (ADR-0028). The transient limit state is scalar-in, trajectory-out: sample θ, integrate the Pol ODE across the full multi-peak h(t), compare final l_e to L. The transient branch is roughly T times more expensive than the static, where T is the number of timesteps per hydrograph (about 500 to 5000). All optimization effort must focus on the transient timestepper; the static branch is essentially free.

**Property 2, shared-sample contract.** Both limit states must consume the same θ_j within each realization, through one M8 call; independent static/transient execution tracks are banned (ADR-0002). Independent draws would conflate physical bias with sampling noise and destroy the scientific deliverable of Phase 1, namely static-versus-transient bias quantification. This is non-negotiable and constrains the engine architecture more than any other single requirement. (The original "and the same r_e" clause is now moot for the static branch: since ADR-0027/0028 r_e drives only the transient uplift/heave gate and neither piping head, so the static branch is r_e-independent. r_e is still computed exactly once per realization and the shared-sample intent is unchanged.)

**Property 3, r_e is stochastic.** Because the Mazure leakage length λ_in depends on k_aq, D_aq, D_bl, and k_bl, which are four of the seven random variables (plus L when L is sampled stochastically), r_e cannot be precomputed once and reused. It lives inside the per-realization loop. This is a frequent source of confusion in Pol-style implementations. Note that since ADR-0027/0028 its sole consumer is the uplift/heave gate (Pol SIE 2024 Eq. (10)); it remains per-realization all the same.

**Property 4, irreducibly serial inner loop.** The compound event memory model creates a hard sequential dependency along the time axis: l(t+Δt) depends on l(t) via the positive-part operator and the running uplift latch. You can vectorize across realizations and across conditioning water levels, but inside a single realization the timestepper is serial. This determines exactly where numpy broadcasting works and where it fails. If the aquifer-lag option (M4) is activated, the aquifer head h_aq becomes a second serial state alongside l, advanced by one extra line at the top of each timestep; the serial structure is otherwise unchanged.

---

## 1. Module Decomposition and Single Responsibilities

The architecture decomposes into nine logical modules. Each has one clear responsibility. Whether each becomes a .py file or class is addressed in §9.

**M1, `config`** holds all *run-varying* deterministic inputs for a single run (the principled config-vs-model-constant split is ADR-0015): cross-section geometry (L, foreshore width, HWL — sourced from the 2019 bank-height data, ADR-0018 — and z_toe, the ADR-0021 landside-toe MSL elevations), the conditioning grid {h_1, ..., h_Nh}, Monte Carlo settings (N = 10^5, RNG seed, LHS scheme), timestepper settings (resolution *policy* per ADR-0013 — the operative Δt at the M8 boundary is the record's `native_dt`, and every generated config pins the integration-Δt policy `target_dt_seconds: 225.0`, ADR-0030; integration scheme; the aquifer-lag flag and S_s — decision inputs whose §11 diagnostic is now built and executed (ADR-0032: instantaneous retained on evidence), with the ADR-0014 activation channel kept pre-committed; the M7 `progression_backend` selector, ADR-0029), the `hydrograph_source` block pinning the canonical d4PDF events (ADR-0020), the deterministic Sellmeijer inputs (θ_repose, `relative_density_insitu`, the α-exponent selectors, ADR-0015/0017), the `foreland_treatment` flag (ADR-0025), the optional seepage-length CoV, and the prior distribution specifications for the seven random variables (family, mean, COV) together with the coupling mode applied at sampling (ADR-0012). This is a pure data object with no logic. Its purpose is reproducibility: one config object fully determines one fragility curve pair. Validate at load time using pydantic or equivalent to catch unit errors (for example COV = 50 versus 0.50) before a multi-hour run begins.

**M2, `prior_sampler`** generates the N by 7 matrix of θ samples via Latin Hypercube Sampling. Single responsibility: converting marginal distribution specifications into a stratified sample matrix in physical units, with the k_aq–d_70 coupling applied per ADR-0012 — the empirical OYO paired-record analysis selected the **two-population decoupling** (`coupling: two_population`; ρ recorded as 0.0 but never imposed, matrix d_70 and framework k_aq drawn from their own marginals); the Nataf `correlated` mode remains supported for sensitivity runs. M2 also draws the independent stochastic seepage length L (`sample_seepage_length`, lognormal, seeded via SeedSequence from the same config seed) — L is *not* an 8th θ column and is never coupled to the θ vector. Returns a named-column container (`ThetaSample`) keyed by parameter name so that downstream modules never index into raw column numbers. Does not know anything about limit states. The substitutable deep-tail sampler `tail_sampling.sample_theta_tilted` (ADR-0029) wraps this exact pipeline with an upstream Z-space mean shift; the production sweep uses plain LHS only. The GSA generator→physical map (`sensitivity.GsaInputSpace`, ADR-0033) mirrors this same pipeline and is pinned bit-identical to `sample_theta` by a drift-guard test.

**M3, `hydrograph_loader`** ingests the d4PDF hydrograph ensemble (band workbooks, the Eq. 4.19 stage rating at the node's own KP, the KP 62.0–62.8 discharge proxy — ADR-0019) and exposes it as a clean object: for each event, a (t, h(t)) array plus metadata (event ID, duration, peak, scenario tag, historical or +4K). Also owns the canonical-shape machinery for the conditioning sweep (ADR-0020): `load_canonical_shape` resolves the band workbook from the pinned event's *own* experiment header (ADR-0023 superseded the ADR-0020 §3 select-by-scenario wording) and `conditioning_record_for_level` rescales the normalized shape per level with the trough pinned at the base-flow stage and `peak = h_i` verbatim. For the static comparison you need a representative scalar h_peak per event, but for the transient you need the full h(t). This module isolates all input/output and units handling, and records the native temporal resolution (1 h = 3600 s, final for this data drop, ADR-0019 §6). Two later additions also live here: `resample_record` (the ADR-0013 record-construction hook, realized by ADR-0030 as the integration-Δt refinement — linear interpolation onto integer subdivisions of the native grid only, every native sample a node, `peak` preserved, so the loading signal is untouched and only the forward-Euler grid is refined) and `flood_timescales` (the §11 loading-timescale extraction, ADR-0032). The latter settled the loading-regime question empirically: at the governing mainstem nodes the flood is **not** flashy — median rising limb 18 h, peak plateau 9 h, FWHM 37 h — so the hourly cadence resolves the peak with ~9 native samples, and the spec's earlier "flashy ~1.5 h plateau" characterization is retired. Per ADR-0023 the climate axis is **shape-invariant**: one canonical HPB shape drives the fragility for all scenarios, and climate differentiation lives on the Phase 3 hazard (peak-stage) side.

**M4, `hydraulic_translator`** computes, given a θ sample and cross-section geometry, the response factor r_e and returns h_aquifer(t). Single responsibility: river stage to landside aquifer piezometric head. This is where λ_in = √(k_aq · D_aq · D_bl / k_bl), the per-realization λ_out = √(k_aq · D_aq · D_fore / k_fore) (sampled transmissivity, deterministic foreshore blanket properties; ADR-0005), the finite-foreshore correction λ_out,eff = λ_out · tanh(B_f / λ_out) (ADR-0006), and the response factor r_e = λ_in / (λ_out,eff + L + λ_in) live. The ratio is the **exact** closed form of USACE (2000) blanket theory Case 7a / TAW (2004) Model 4A — L is the exact *linear* under-levee resistance term and is never inside a tanh; Pol thesis Eq. (7.13) is its no-riverside-blanket special case (ADR-0006 as amended 2026-07-05: the former L/λ_in "validity monitor" was withdrawn as a category error, and the run-level record is the descriptive `metadata['leakage_geometry']` block; hinterland extents resolved semi-infinite = conservative). The ADR-0025 `foreland_treatment: open_entry` sensitivity zeroes the effective entry length (x₁ = 0) at M8; the blanketed tanh form is the adopted baseline. **That sensitivity is now executed (2026-07-28; `scripts/foreshore_width_study.py` → `docs/decisions/adr0025-foreshore-sensitivity.json`, companion `adr0025-foreshore-width-and-sensitivity.md`): removing the foreland entirely (B_f → 0) moves transient P_f by ≤ 0.0044 at every confined section (KP 62.0: 2.3e-4) and static P_f by exactly 0, the latter asserted by the driver as the ADR-0028 consequence. The tanh is saturated everywhere (credits 0.835 at KP 62.0, 0.969–1.000 elsewhere), so B_f is a real but non-load-bearing input; its `foreshore_width_m` values are the OYO 様式-3 高水敷幅 (high-water-bed width) annotations, verified verbatim and corroborated by the MLIT 2008 堤防現況縦断図, and are NOT levee-to-waterline distances.** Note r_e is not monotone in "foreshore narrowness" across sections: KP 62.0 has the narrowest foreshore *and* the lowest r_e (0.330 vs 0.417–0.438), because the same thin blanket that costs it uplift resistance also shortens λ_in. Since ADR-0027/0028 the translated head h_aquifer(t) feeds **only the uplift/heave gate** (Pol SIE 2024 Eq. (10)); both piping heads use the raw outer level. The module exposes h_aquifer(t) through a unified interface that can produce it in either of two forms: the algebraic instantaneous translation h_aq(t) = z_toe + r_e · (h_river(t) − z_toe), which is the default, or a first-order linear-reservoir lag state dh_aq/dt = (1/τ_aq)·[z_toe + r_e·(h(t) − z_toe) − h_aq(t)], advanced by the exact exponential update h_aq ← h_aq + (1 − exp(−Δt/τ_aq))·(h_aq,inst − h_aq) and initialized in equilibrium with the initial river stage (ADR-0004). The choice between the two is made by the aquifer-response diagnostic described in §11 — **now executed (ADR-0032)**: with every discretionary input pre-registered at its conservative pole, Π = τ_aq/T_rise ≈ 0.010–0.012 at the governing pair (central θ over the *ensemble-median* T_rise = 18 h) against the committed threshold Π\* = 0.10, so the **instantaneous default is retained everywhere**, as an evidenced decision rather than an inherited assumption. The gate logic and constants live in M4 (`aquifer_response_diagnostic`, `AQUIFER_RESPONSE_*`) and the outcome is stamped per run into `metadata['aquifer_response']`. The lag hook stays in place unchanged (the downstream limit state and progression modules consume h_aquifer(t) identically in both forms and require no restructuring), with one scope caveat (ADR-0032 amendment): the Π screen detects *elastic leaky-confined* response only — a section whose aquifer is not channel-connected and saturated at base flow (dead-ended lenses, entry through an elevated dry foreland, initial heads well below the exit datum) falls outside its scope and needs a transient-fill assessment, not a larger S_s; where violated, the instantaneous form over-translates the gate head (measured 1.15–2.7× at the Japanese FEM validation sites), which post-ADR-0027/0028 is gate-only and conservative for transient P_f. All four production sections pass the connectedness check.

**M5, `initiation_evaluator`** evaluates Z_uplift(t) and Z_heave(t) at each timestep given Δh_blanket(t) from M4 and the sampled (D_bl, γ'_bl). Both checks use the un-reduced, r_e-attenuated aquifer overpressure Δh_blanket(t) = r_e·(h(t) − z_toe), not the erosion-driving head, because uplift and heave respond to the full pore pressure on the blanket base and r_e models the intact-blanket damping that governs whether/when the blanket ruptures (ADR-0027). The heave threshold is the Terzaghi critical gradient γ'_bl/γ_w, not Pol's independent i_c,h — a deliberate choice that keeps the 7D vector and, under this parameterization, collapses the gate to `I_er(t) ≡ heave_now(t)` (Z_heave ≡ Z_uplift/D_bl; ADR-0008). The full gate structure (uplift latch, `l_current > 0` clause, instantaneous heave) is retained even though it currently collapses, so it becomes load-bearing the instant i_c,h is decoupled in a sensitivity run. The module exposes (a) the boolean indicator I_er(t), true once the running minimum of Z_uplift has gone negative AND heave is currently active, OR if l_current > 0 AND heave is currently active, and (b) the time t_uh of first co-occurrence. Single responsibility: STPH gating logic. Pol's third I_er clause, which suspends progression once organised flood fighting is deployed, is deliberately omitted; this yields an unconditional upper bound on transient failure (Pol-confirmed 2026-07-07 as the safer choice for flashy typhoon rivers where organised flood fighting is infeasible; ADR-0008). The spec's earlier expectation that this conservatism "grows under the elongated +4K hydrographs" is discharged for this data drop: ADR-0023 found +4K shapes are not longer at the normalized-shape level, so no shape-driven conservatism differential is missed.

**M6, `sellmeijer_static`** implements the full revised Sellmeijer 2011 critical head: H_c = L · F_r · F_s · F_g, with the three factors computed per equation (12) of the 2011 paper. Inputs: θ vector plus geometry. Output: scalar H_c. The particle submerged weight in F_r is the **deterministic** basin-wide γ'_p = 16.87 kN/m³ (`GAMMA_P_SUB_DEFAULT`), not a θ column — the sixth θ entry is the *blanket* weight γ'_bl and feeds only the M5 uplift/heave gate (the γ'_s split, ADR-0016); H_c therefore has no exposure to the sixth θ variable. Used in two places, once for the static limit state evaluation and once inside the transient progression model because H_c parameterizes the equilibrium curve H_eq(l). Centralizing it in one place prevents drift between the two uses. Also computes l_c via the Pol SIE 2024 formula l_c/L = 0.5 · tanh(2 · D_aq/L). The module retains an optional scale-exponent argument so that the 3D hole-exit value α = −1/2 can be substituted for the 2D value in a sensitivity decomposition of the static-transient gap (§12, Failure mode 4); the *transient-only* isolation is wired as `alpha_exponent_transient` at M8 (ADR-0017), which recomputes a separate transient H_c while the static comparator keeps α = −1/3 (the Pol-endorsed baseline; ADR-0017).

**M7, `pol_ode_progression`** is the time-dependent ODE integrator. Given θ (including C_e), the raw river stage h(t), the aquifer head time series h_aquifer(t) (for the gate), the H_c and l_c from M6, it integrates dl/dt = 89 · C_e · (k_aq · (H_erosion(t) − H_eq(l))/L)^0.81 forward in time using forward Euler, gated by the M5 erosion indicator I_er(t). The erosion-driving head is H_erosion(t) = (h(t) − z_toe) − 0.3·D_bl, the crack-resistance-reduced head on the **raw outer level** (Pol SIE 2024 Eq. (6); **no r_e** — ADR-0027, superseding ADR-0007): once uplift/heave ruptures the cohesive blanket the exit is unfiltered, so the full outer head drives progression, while r_e models only the intact-blanket damping in the gate. This raw H_erosion is distinct from the un-reduced, r_e-attenuated Δh_blanket(t) that drives uplift and heave in M5; because erosion runs only where heave is active (the ADR-0008 collapse), "raw head always" and "r_e dropped once the blanket ruptures" are numerically identical here. The equilibrium curve H_eq(l) is constructed by piecewise linear interpolation between (0, 0), (l_c, H_c), and (L, 0.9·H_c) — the 0.9·H_c end anchor is Pol's own intentional conservatism (ADR-0009). The positive-part operator is enforced inside the timestepper. Output: full l(t) trajectory and final l_e. The loop is restructured for speed (hoisted time-invariant factors, gate-masked `**0.81`, sub-toe whole-step skip) **bit-identically** to the straightforward kernel loop, with an opt-in Numba backend (ADR-0029) selected by `config.timestepper.progression_backend` that is equivalent to < 1e-10.

**M8, `limit_state_evaluator`** orchestrates both limit states for a single realization. Receives one θ sample, the hydrograph, the geometry, and an optional l_ini, and returns the pair (Z_static, Z_transient). This is the module that enforces the shared-sample contract: the same θ is fed into both branches through one call (ADR-0002/ADR-0011). Also returns auxiliary diagnostics, namely H_c, H_c_transient (equal by default; diverges only under the ADR-0017 decomposition), l_c, λ_in, r_e, the latched uplift/heave flags and t_uh, because Phase 2 Bayesian filtering needs trajectory information, not just binary pass or fail, and because the survival-discrimination decomposition (§8) needs both the static and transient rejection under h_2016. Two entry points share one physics: the frozen scalar `evaluate_realization` (the Phase 2 API) and the vectorized `evaluate_batch` (the production sweep, bit-identical to looping the scalar path). This module must be importable cleanly by Phase 2.

**M9, `fragility_assembler`** takes the raw N by N_h indicator matrices (one for static, one for transient) and fits lognormal fragility curves separately for each. Fits are **anchored to the load excess h − z_toe** with inverse-variance probit weights (`LognormFragility.datum_m`), and are **Optional** per branch (ADR-0024): a branch whose transition the conditioning grid does not bracket (max raw P_f < 0.5) yields `None` and is carried instead by its raw points with always-on Clopper–Pearson binomial CIs — the intended primary transient presentation where the transition is physically unreachable, not a fallback; `metadata['fragility_deliverable']` flags the form per branch. Computes confidence bands via bootstrap on the realizations (degenerate replicates skipped, not raised), and the spec §11 CoV of P_f per level (`metadata['mc_convergence']`). Output: a FragilityResult object containing both fitted curves (or `None`), raw point estimates, binomial CIs, and, critically, the full θ matrix and both failure matrices retained for Phase 2. `upscale_length_effect(p_f, n_eff)` (the weakest-link transform) is implemented and **wired behind `config.length_effect`** (ADR-0037), OFF by default in every generated config: at the resolved λ_ac = 250 m the 200 m segment gives n_eff = 1 (the correction is the identity — the ADR-0037 finding, stated as such), and when enabled the transform lands in `metadata['length_effect']` only — the persisted cross-section curves never change (see §12).

---

## 2. Data-Flow and Interface Contracts

`config` (M1) flows into every other module as a read-only object. No module mutates it.

`prior_sampler` (M2) consumes `config.prior_specs` and `config.correlation_specs` and emits:

```
theta_matrix: ndarray shape (N, 7)
param_names:  ['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']
```

Contract: rows are LHS draws with the k_aq–d_70 coupling applied per the mode in config — the empirical result is the **two-population decoupling** (ADR-0012; ρ recorded 0.0, never imposed), with the Nataf `correlated` mode available for sensitivity runs (see §7); columns are physical-units parameter values; and the RNG seed in config fully determines the matrix. The independent stochastic seepage length L is drawn alongside (SeedSequence off the same seed) but is *not* a θ column. All downstream modules access columns by name via `theta_matrix[:, param_names.index('k_aq')]` or, preferably, via the named-access wrapper (`ThetaSample`). Note the sixth column is `gamma_bl_sub` (the blanket weight, ADR-0016), not the aquifer particle weight.

`hydrograph_loader` (M3) emits:

```
hydrographs: dict[event_id -> HydrographRecord]
HydrographRecord:
  t:               ndarray (T,)         # SECONDS (M3 converts all units at this boundary)
  h:               ndarray (T,)         # river stage [m above MSL], uniformly sampled at native_dt
  peak:            float                # = max(h); authoritative static comparator level (ADR-0010)
  duration_hours:  float
  scenario:        str                  # 'historical' or '+4K'
  event_id:        str
  native_dt:       float                # AUTHORITATIVE integration timestep [s] (ADR-0010/0013).
                                        # Source data is 3600 s (ADR-0019 §6); production canonical
                                        # records are refined to native/16 = 225 s at construction
                                        # via resample_record (ADR-0030), so the record M8 sees
                                        # carries 225.0. Phase 2 replay runs on the run's own 225 s
                                        # grid (ADR-0036, superseding ADR-0022 decision 2's 1800 s)
  provenance:      dict                 # ADR-0019 member/KP provenance; resample provenance
                                        # (resampled_from_native_dt_s, resample_factor) when refined
```

M8 consumes exactly three fields structurally by duck typing — `.h`, `.peak`, `.native_dt` (ADR-0010) — so any structural stand-in stays valid alongside the concrete `hydrographs.HydrographRecord`.

The core inner contract, and the one needing the most care, is the signature of `limit_state_evaluator` (M8):

```
Input:
  theta_row:    ndarray (7,)            # one realization's parameter vector
  hydrograph:   HydrographRecord
  geometry:     dict                    # flat keys L, z_toe, foreshore_width, D_fore, k_fore
                                        # (ADR-0010; ADR-0005 foreshore); z_toe = polder surface
                                        # elevation at the landside exit point, ≡ h_e in Pol SIE
                                        # 2024 Eqs. (6) and (8) (ADR-0007 datum note; the r_e-on-
                                        # erosion-head part of 0007 is superseded by ADR-0027)
  l_ini:        float                   # initial pipe length (default 0)
  store_trajectory: bool                # default False to save memory
  # keyword-only, all defaulting to the pinned M6 constant / baseline (ADR-0015/0017/0025):
  alpha_exponent, alpha_exponent_transient, theta_repose_rad, relative_density,
  gamma_p_sub_kn_m3, foreland_open

Output: EvaluationResult dataclass
  Z_static:        float                 # H_c − (h_peak − z_toe): RAW gross head (ADR-0028)
  Z_transient:     float
  l_e_final:       float
  l_trajectory:    ndarray (T,) or None
  H_c:             float                 # static comparator's critical head
  H_c_transient:   float                 # anchors the transient H_eq; == H_c unless the
                                         #   ADR-0017 α-decomposition is active
  l_c:             float
  lambda_in:       float
  r_e:             float                 # drives the uplift/heave gate ONLY (ADR-0027/0028)
  t_uh:            float or NaN          # time of first uplift+heave co-occurrence
  failure_static:  bool
  failure_trans:   bool
  uplift_occurred: bool                  # latched within event
  heave_occurred:  bool                  # latched within event
```

The scalar `evaluate_realization` signature and the `EvaluationResult` field set are a **frozen Phase 2 contract** (ADR-0011); the additive `H_c_transient` field and the keyword-only overrides were introduced in the ADR-0017 additive-change style.

The optional `l_trajectory` storage matters for memory: 10^5 realizations times about 1000 timesteps times 8 bytes is about 800 MB per cross-section. For Phase 2 you only need the final l_e under the 2016 hydrograph specifically, so default to off and toggle on for diagnostic runs and for the 2016 calibration sweep.

`fragility_assembler` (M9) consumes the full N by N_h matrices of `failure_static` and `failure_trans` booleans and emits the FragilityResult, the handoff artifact to Phase 2:

```
FragilityResult:
  conditioning_grid:    ndarray (N_h,)
  P_f_static_raw:       ndarray (N_h,)        # MC point estimates
  P_f_trans_raw:        ndarray (N_h,)
  P_f_static_fit:       LognormFragility | None  # fitted (mu, sigma, datum_m); None if the
  P_f_trans_fit:        LognormFragility | None  #   branch is unbracketed (ADR-0024)
  bootstrap_bands:      dict[curve -> (lo, hi)]  # uncertainty of the fitted curve (where it exists)
  binomial_ci:          dict[curve -> (lo, hi)]  # always-on Clopper–Pearson CIs on the RAW
                                                # points; the deliverable at tail-only branches (ADR-0024)
  theta_matrix:         ndarray (N, 7)         # RETAINED for Phase 2
  param_names:          list[str]
  failure_matrix_stat:  ndarray (N, N_h) bool  # RETAINED for diagnostics and decomposition
  failure_matrix_tran:  ndarray (N, N_h) bool  # RETAINED for Phase 2
  metadata:             dict                    # config snapshot, runtime, version,
                                                # c_e_stochastic flag, d70_interpretation,
                                                # remediation_state, segment_id, fragility_deliverable,
                                                # fragility_fit, mc_convergence, leakage_geometry,
                                                # aquifer_response (ADR-0032), progression_backend,
                                                # foreland_treatment, hydrograph,
                                                # length_effect (ADR-0037, present only when enabled)
```

The Optional fits and the additive `binomial_ci` are an ADR-0024 spec §2 contract extension (additive, safe for Phase 2, which reads by attribute and filters via the retained matrices, not the fitted curves). The HDF5 dataset names use `failure_matrix_static`/`failure_matrix_trans` while the object fields are `failure_matrix_stat`/`failure_matrix_tran` — the spec is inconsistent between §2 and §8, and `save`/`load` map between the two namings.

Retaining `theta_matrix` and `failure_matrix_tran` is non-negotiable. Phase 2's Accept-Reject filtering re-runs M8 on the surviving θ rows against h_2016(t); it needs the raw prior matrix, not just the fitted curve. Retaining `failure_matrix_stat` is what makes the survival-discrimination decomposition of §8 possible. Persist via HDF5 (h5py) for the large arrays and a JSON sidecar for metadata. One HDF5 file per cross-section per scenario.

---

## 3. Logical Execution Sequence

Three nested levels, with order chosen for both correctness and performance:

**Outermost loop, conditioning water levels h_i.** Fully parallelizable across cores (joblib, in `run.py`). Each h_i is independent; for each, the static evaluation uses h_i as h_peak, while the transient evaluation uses one of two config-selected loading records (ADR-0020): the **canonical d4PDF shape** rescaled to peak h_i (production — a real pinned event shape normalized in stage domain, trough pinned at the base-flow stage, `peak = h_i` verbatim, then refined onto the 225 s integration grid at record construction via `resample_record`, ADR-0030), or the clearly-marked **synthetic two-peak stub** (plumbing/dev only). The whole sweep is reproducible-by-construction: all stochasticity is front-loaded into the single prior-sampling call, so parallel ≡ serial regardless of `n_jobs`.

**Middle loop, realizations j in {1, ..., N}.** All N realizations at a given h_i share the same hydrograph but use independent θ_j rows. This is the loop where numpy broadcasting yields the largest gains.

**Innermost loop, timesteps t_k.** Irreducibly serial within a realization. Vectorized across realizations within a single timestep (see §6).

The per-realization, per-conditioning-level pseudocode:

```
SHARED PREAMBLE (computed once per θ_j):
  1. Read θ_j from theta_matrix
  2. Compute H_c(θ_j) and l_c(θ_j) via M6
  3. Compute λ_in(θ_j) and r_e(θ_j) via M4

STATIC BRANCH:
  4. H_load_peak = h_i − z_toe                   [RAW gross head across the structure;
                                                  NO r_e, NO 0.3·D_bl reduction — ADR-0028]
  5. Z_static = H_c − H_load_peak
  6. failure_static = (Z_static <= 0)

TRANSIENT BRANCH (full timestep loop):
  7. Initialize l_current = l_ini, uplift_ever = False
  8. For each timestep t_k:
       a. h_aq(t_k)        = z_toe + r_e · (h(t_k) − z_toe)
                              [instantaneous form — the executed ADR-0032 diagnostic
                               retained it (Π_central ≈ 0.01 ≪ 0.10); the dormant lag hook
                               would advance h_aq as a linear-reservoir state, see M4]
       b. Δh_blanket(t_k)  = h_aq(t_k) − z_toe        [= r_e · (h(t_k) − z_toe); gate head]
       c. H_erosion(t_k)   = (h(t_k) − z_toe) − 0.3 · D_bl   [RAW outer level, NO r_e — ADR-0027;
                                                             erosion rate driver only]
       d. Z_uplift(t_k)    = (γ'_bl · D_bl)/γ_w − Δh_blanket(t_k)   [uses r_e-attenuated Δh_blanket]
       e. uplift_ever     |= (Z_uplift(t_k) < 0)
       f. i_exit(t_k)      = Δh_blanket(t_k) / D_bl
       g. Z_heave(t_k)     = γ'_bl/γ_w − i_exit(t_k)             [uses Δh_blanket; Terzaghi i_c, ADR-0008]
       h. heave_now        = (Z_heave(t_k) < 0)
       i. I_er(t_k)        = (uplift_ever OR l_current > 0) AND heave_now   [≡ heave_now, ADR-0008]
       j. If I_er(t_k):
            H_eq = piecewise_linear(l_current, anchors=[(0,0), (l_c, H_c), (L, 0.9·H_c)])
            overload = max(0, H_erosion(t_k) − H_eq)      [RAW H_erosion, not Δh_blanket]
            dldt = 89 · C_e · (k_aq · overload / L)^0.81
            l_current = min(L, l_current + dldt · Δt)     [positive part via max(0, overload); breach clip at L]
          Else:
            l_current unchanged                            [positive-part operator]
  9. Z_transient = L − l_current
  10. failure_trans = (Z_transient <= 0)
```

Three subtle points worth highlighting, stated in their **current (ADR-0027 + ADR-0028, Pol-confirmed 2026-07-07)** form; these two ADRs superseded the earlier r_e-attenuated head conventions and each model is now used exactly as its author intended. First, **r_e drives only the uplift/heave gate** (steps d–g, via Δh_blanket = r_e·(h − z_toe), Pol SIE 2024 Eq. (10)); it enters *neither* piping head. The static Sellmeijer comparator (step 4) uses the **raw gross head** h_peak − z_toe (Sellmeijer 2011's "critical hydraulic head across structure", no r_e — ADR-0028), so the static branch is entirely r_e-independent. Second, the transient branch drives the progression rate with the **raw** erosion head H_erosion = (h − z_toe) − 0.3·D_bl (step c, used in step j; Pol SIE 2024 Eq. (6), no r_e — ADR-0027: once heave ruptures the blanket the exit is unfiltered), while the uplift and heave checks (steps d and g) keep the un-reduced, r_e-attenuated Δh_blanket. The two piping heads therefore differ by **exactly 0.3·D_bl** — the clean head-convention component of the §12 fm4 decomposition, with r_e dropped out of both, leaving the static–transient gap a clean temporal comparison. The shared-sample contract still holds (the same θ_j feeds both branches through one M8 call). Third, in step 8i the clause `(uplift_ever OR l_current > 0)` is what enables compound-event progression to resume on subsequent peaks without re-triggering uplift, the gateway condition for the memory model; under the Terzaghi collapse (ADR-0008) the gate reduces to `heave_now`, but the full structure is retained for the i_c,h sensitivity.

---

## 4. Organization of the Two Parallel Limit States

The two limit states share three computations and diverge on a fourth. The architectural pattern is "shared preamble, then branch":

```
SHARED PREAMBLE  (per θ_j, O(1) cost):
  - sample θ_j               (M2)
  - compute H_c(θ_j), l_c    (M6)
  - compute λ_in, r_e(θ_j)   (M4)

DIVERGENT EVALUATION:
  Static branch:    scalar comparison       O(1)
  Transient branch: T-step ODE integration  O(T)
```

This pattern makes the cost asymmetry explicit. Implementation must not be tempted to write `run_static()` and `run_transient()` as fully independent functions; they must consume the same θ_j and the same r_e. Implement them as a single function (M8) that returns both Z values, with internal flags controlling which diagnostics get retained.

A consequence worth flagging: the static branch has no exposure to C_e at all. C_e is a transient-branch parameter only. The static limit state H_c depends on the geotechnical variables that enter Sellmeijer F_r/F_s/F_g (k_aq, d_70, D_aq) plus the deterministic θ_repose, D_r and the basin-wide particle weight γ'_p = 16.87 kN/m³ (ADR-0016) — it carries **no** exposure to the sixth θ column γ'_bl (the blanket weight, which feeds only the M5 gate) and, since ADR-0028, **no** exposure to r_e (hence none to D_bl or k_bl through r_e). Phase 2 filtering will therefore tighten C_e only through the transient branch, which is exactly the desired behavior: Phase 2 is calibrating laminar-flow conservatism, which lives only in the ODE. A second consequence, introduced by the head separation, is that the static and transient branches do not use an identical driving head: both now use the **raw** head (no r_e, ADR-0027/0028), and the transient additionally applies the 0.3·D_bl crack-resistance reduction. This is a deliberate fidelity choice (the static branch is conventional Sellmeijer gross-head practice, which does not apply Pol's crack term) and is the head-convention component of the static-transient gap discussed in §12 — now cleanly exactly 0.3·D_bl, with r_e no longer confounding it.

---

## 5. Compound Event Memory Model: State Variable Management

This is the most error-prone part of the implementation. The memory model demands that pipe length l carry across peaks within a single d4PDF event record, with the positive-part operator preventing healing.

The state variable is **`l_current: float`**, initialized to `l_ini` at the start of each event. For prior fragility curve construction in Phase 1, l_ini = 0. For Phase 2 (where the 2016 hydrograph is replayed for filtering) l_ini also starts at 0 because the 2016 event is the calibration event itself. The hook for non-zero l_ini exists to support sensitivity studies and the architectural flexibility to feed event sequences. If the aquifer-lag option is active, a second state h_aq_current carries across timesteps as well, but it does not carry across events (only the pipe length does).

Inside the timestepper, l_current is updated as:

```
if I_er(t):
    H_erosion = (h(t) - z_toe) - 0.3 * D_bl      # RAW outer level, NO r_e (ADR-0027)
    overload  = max(0, H_erosion - H_eq(l_current))
    dldt      = 89 * C_e * (k_aq * overload / L)**0.81
    l_current = min(L, l_current + dldt * dt)    # breach clip: l absorbing at L
else:
    l_current unchanged
```

The `max(0, overload)` enforces the positive-part operator at the level of the driving force; combined with `dldt >= 0` and the absence of any negative-progression term, this guarantees l_current is monotonically non-decreasing. There is no separate "reset between peaks" step; that is the whole point of the memory model. The hydrograph is fed in as one continuous time series spanning the entire compound event, and l_current evolves monotonically across the whole record.

**Traps to watch for:**

When h(t) drops below the uplift threshold during inter-peak troughs, I_er goes false, dl/dt = 0, and l_current stays flat. Trajectory plots will show staircase-shaped growth, with flat segments during troughs and growth segments during peaks. This is correct. Do not "fix" it.

The "min{Z_u(τ): τ <= t} < 0" clause in I_er is a running minimum. Implement it as a single scalar `uplift_ever_occurred: bool` that latches to True the first time Z_u goes negative and stays True for the rest of the event. This avoids confusion with the instantaneous Z_h check and is correct because uplift represents a one-way structural failure of the blanket.

The `l_ini > 0` clause in I_er means a pre-existing pipe makes the uplift gate effectively bypassed for that event. This is correct physics, since an existing pipe means the blanket is already breached, but be aware it changes the gating logic between events with and without prior pipes.

Do not subtract the 0.3·D_bl crack resistance from the uplift or heave heads. That reduction belongs only to the erosion driver H_erosion; the uplift and heave checks act on the full Δh_blanket. Mixing them is a common error that would make initiation appear harder than it is. Note also the head asymmetry introduced by ADR-0027/0028: the erosion driver uses the **raw** outer level (h − z_toe), while the uplift/heave checks use the **r_e-attenuated** Δh_blanket — do not "unify" these onto one head.

For r_l (long-term strength recovery between events): in Phase 1 set r_l = 0 always, per thesis scope. The hook should exist in the API (`l_ini_next_event = (1 − r_l) · l_e_prev`) but it lives outside the timestepper, between event evaluations.

---

## 6. Vectorization and Parallelization Strategy

Vectorization opportunities decompose along the three loop levels.

**Across realizations (middle loop), partially vectorizable.** The shared preamble, namely sampling θ and computing H_c, λ_in, and r_e, is fully numpy-vectorizable. Compute these as N-length arrays in one shot:

```python
H_c_vec     = sellmeijer_vectorized(theta_matrix)        # shape (N,)
l_c_vec     = 0.5 * L * np.tanh(2 * theta_matrix[:, idx_D_aq] / L)
lambda_in   = np.sqrt(k_aq_vec * D_aq_vec * D_bl_vec / k_bl_vec)
lambda_out  = np.sqrt(k_aq_vec * D_aq_vec * D_fore / k_fore)    # per realization (ADR-0005)
lambda_out_eff = lambda_out * np.tanh(B_f / lambda_out)         # finite foreshore (ADR-0006)
r_e_vec     = lambda_in / (lambda_out_eff + L + lambda_in)
```

The static limit state is fully vectorizable: a single boolean comparison across N realizations. The static branch is essentially O(N) with a tiny constant and runs in seconds for N = 10^5.

**Across timesteps (inner loop), not vectorizable in time.** Path dependency. But within a single timestep you can vectorize across all N realizations simultaneously:

```python
# At time t_k, advance all N realizations one step
h_t                = h_river[k]                                            # scalar
delta_h_vec        = r_e_vec * (h_t - z_toe)                              # shape (N,); GATE head only
H_erosion_vec      = (h_t - z_toe) - 0.3 * D_bl_vec                       # RAW outer level, NO r_e (ADR-0027)
Z_u_vec            = (gamma_bl_sub_vec * D_bl_vec) / gamma_w - delta_h_vec  # gate uses r_e-attenuated delta_h
uplift_ever_vec   |= (Z_u_vec < 0)
i_exit_vec         = delta_h_vec / D_bl_vec
Z_h_vec            = gamma_bl_sub_vec / gamma_w - i_exit_vec
heave_now_vec      = (Z_h_vec < 0)
I_er_vec           = (uplift_ever_vec | (l_current_vec > 0)) & heave_now_vec

# Piecewise linear H_eq with per-realization breakpoints
H_eq_vec = np.where(
    l_current_vec < l_c_vec,
    H_c_vec * l_current_vec / l_c_vec,
    H_c_vec + (0.9 * H_c_vec - H_c_vec) * (l_current_vec - l_c_vec) / (L - l_c_vec)
)
overload_vec       = np.maximum(0.0, H_erosion_vec - H_eq_vec)   # RAW H_erosion, not delta_h
dldt_vec           = 89.0 * C_e_vec * (k_aq_vec * overload_vec / L)**0.81
dldt_vec           = np.where(I_er_vec, dldt_vec, 0.0)
l_current_vec      = np.minimum(l_current_vec + dldt_vec * dt, L)   # breach clip at L (per-realization when L stochastic)
```

The as-built loop restructures this bit-identically (hoisted time-invariant factors, `**0.81` evaluated only where `I_er ∧ overload>0`, whole-step skip when `h_t ≤ z_toe`; ADR-0029) and offers an opt-in Numba backend — see the Numba note below. The static comparison in the preamble is the raw `h_peak − z_toe` (ADR-0028), r_e_vec entering only the gate above.

If the aquifer-lag option is active (dormant in production — ADR-0032 retained the instantaneous form), insert one line before `delta_h_vec` that advances the lag state with the exact exponential update, `h_aq_vec += (1 - np.exp(-dt / tau_aq_vec)) * (z_toe + r_e_vec * (h_t - z_toe) - h_aq_vec)` (explicit Euler overshoots for Δt > τ_aq and diverges for Δt > 2·τ_aq; ADR-0004), and then set `delta_h_vec = h_aq_vec - z_toe`. The rest of the loop is unchanged, which is the point of the unified M4 interface.

Total operation count: N times T elementwise ops, all in numpy. For N = 10^5 and T about 1000, that is about 10^8 fused operations, well within numpy's reach in minutes.

**Across conditioning water levels (outer loop), embarrassingly parallel.** Each h_i is independent; parallelize with joblib.Parallel across CPU cores. For N_h about 30 and 8 to 16 cores, near-linear speedup.

**Where broadcasting breaks down:**

Variable-length hydrographs across d4PDF events. Different events have different durations; you cannot stack into a uniform (N_events, T) array without padding. Process events one at a time, since they are independent across the conditioning loop.

The piecewise linear H_eq interpolation: breakpoints (l_c, H_c) differ per realization, so scipy.interpolate.interp1d will not broadcast cleanly. Implement manually with np.where as shown above. This is fine; the two-segment piecewise linear is trivial to express.

The first-uplift-time bookkeeping requires sequential updates along time but vectorizes across realizations (`uplift_ever_vec |= Z_u_vec < 0`).

**Numba note (now realized — ADR-0029):** the numpy-first advice was followed and then profiled. The restructured numpy timestepper (bit-identical to the kernel loop) already cut a KP58.8 sweep from 46 s to 10 s; an **opt-in** `@njit(parallel=True)` backend (`progression_numba`, the `[accel]` extra, selected by `config.timestepper.progression_backend='numba'`) gives a further ~4× (sweep → 2.7 s). The Numba backend is equivalent to the numpy reference only to < 1e-10 (platform `pow` ulp on `x**0.81`), so it is config-owned and stamped into `metadata['progression_backend']`; it is refused with the aquifer lag and never touches the frozen scalar `evaluate_realization`. After acceleration the next bottleneck is the M9 bootstrap (~19 s Python loop), untouched.

**Budget estimate:** about 5 min per h_i times 30 h_i is about 2.5 hr single-threaded; about 15 to 30 min with 8-core parallelism. Comfortable for iterative thesis development.

---

## 7. The Seven-Dimensional Stochastic Parameter Vector

Random variables sampled via LHS:

| Symbol | Description | Distribution | Mean | COV | Source |
|---|---|---|---|---|---|
| k_aq | Aquifer hydraulic conductivity [m/s] | Lognormal | (site-specific) | 0.50 | OYO 1999 field tests |
| d_70 | Representative grain size [m] | Lognormal | (site-specific) | 0.30 | OYO 1999 grain-size curves (thesis prior; was 0.10) |
| D_aq | Aquifer thickness [m] | Lognormal | (site-specific) | 0.10 | OYO 1999 borehole logs (thesis prior; was 0.20) |
| D_bl | Blanket thickness [m] | Lognormal | (site-specific) | 0.167 | OYO 1999 borehole logs (thesis prior; was 0.20) |
| k_bl | Blanket vertical conductivity [m/s] | Lognormal | (site-specific) | 0.50 | OYO 1999 (or proxy) |
| γ'_bl | Blanket submerged unit weight [kN/m^3] | Lognormal | 6.9 | 0.056 | OYO 1999 Form 5 (A_c sat. density); the *blanket* weight (γ'_s split, ADR-0016) — feeds only the M5 gate, not F_r |
| C_e | Erosion coefficient [-] | Lognormal | 0.055 | 0.782 | Pol SIE 2024 Table 2 field prior (ADR-0026; was 0.014 / 0.50) |

Fixed within every realization:

- θ_repose = 37 degrees (angle of repose, enters Sellmeijer F_r; `theta_repose_deg` run input, ADR-0015)
- D_r,in-situ = 0.725 (Pol base case; config `relative_density_insitu` — distinct from the pinned normalization mean D_r,m = 0.725, ADR-0015)
- γ'_p = 16.87 kN/m³ (deterministic basin-wide aquifer particle weight in F_r; ADR-0016)
- C_u, KAS evaluated at experimental mean values per Sellmeijer 2011 convention

**Optional Sellmeijer model factor m_p (ADR-0045, off by default).** The critical-head model factor m_p ~ Lognormal(mean 1.0, CoV 0.12) of Pol SIE 2024 Table 2 (Sellmeijer's ~12% regression scatter; HKV/WBI practice carries it stochastically) is available via the optional config block `sellmeijer_model_factor`. It is **not** an eighth theta column: like the stochastic L it is an independent standalone 1-D LHS draw under its own SeedSequence salt, so enabling it never shifts the theta or L draws. When enabled, M8 multiplies the **single-source** H_c by m_p in *both* its uses — the static comparator and the transient H_eq anchor — one model-form-error belief per realization (applying it to one branch alone is rejected; ADR-0045 Decision 2). The production baseline and all persisted deliverables run with the factor off (bit-identical to pre-ADR-0045); the quantified effect (≈2.2× on the static shoulder P_f at KP58.8) is the `scripts/mp_model_factor_companion.py` companion deliverable. This is where the "~12% Sellmeijer model factor" invoked by the C_e justification below actually lives.

The C_e promotion is the substantive update from a six-dimensional formulation, and the promotion (C_e a random variable) stands. **The prior parameters and the justification are revised by ADR-0026 (Pol, 2026-07-07).** The prior is now `Lognormal(mean 0.055, std 0.043)` (COV ≈ 0.782) — Pol's own SIE 2024 Table 2 field-reliability value, the mean determined by incorporating large-scale experiments, ~4× above the small-scale calibrated 0.010–0.014. The **justification** is corrected: C_e is stochastic on **intrinsic-uncertainty** grounds (Pol: it carries high uncertainty in practice), **not** to absorb laminar-vs-turbulent model uncertainty — that is nominally covered by Sellmeijer's own ~12% model factor, and it is not C_e's to launder. Phase 2 Bayesian filtering against the 2016 survival record still constrains C_e, now framed as reconciling two calibration targets (detailed time-dependent development ≈ 0.016, which this dl/dt-integrating engine most resembles, vs mean post-critical rate ≈ 0.055, the adopted conservative field value) whose factor 3–4 gap Pol leaves open. The earlier "COV 0.50 spans 0.007–0.030" rationale is retired with the old prior.

**Coupling structure (resolved empirically — ADR-0012).** Sampling proceeds via LHS on all seven marginals. Spec §7 originally mandated a Nataf correlation between aquifer conductivity k_aq and grain size d_70 by default (independent draws would pair a fine-matrix grain size with a coarse-framework conductivity, a soil that does not physically exist, inflating the prior progression rate), with a pre-registered **two-population fallback** if the OYO records showed the matrix grain size and bulk conductivity to be statistically decoupled. The empirical OYO analysis (N = 6 in-scope paired records; r² well below 0.3, pooled correlation indistinguishable from zero) **selected the fallback**: the adopted mode is `two_population` (matrix d_70 governing Sellmeijer resistance and framework k_aq governing seepage/progression are drawn from their own marginals; ρ recorded as 0.0 but never imposed) — Pol-endorsed 2026-07-07. This is *not* the naive independent sampling Failure Mode 7 warns against, because under the two-soil model the two draws are not conflicting descriptions of one soil. The `correlated` Nataf mode remains implemented for sensitivity runs. Both the matrix and the bulk d_70 interpretations are carried as co-primary runs, recorded in `metadata.d70_interpretation`. Implementation: generate the stratified uniform LHS design; under `correlated`, apply the Gaussian-copula/Nataf transform (skipped entirely under `two_population`); then map to physical units.

**A note on the C_e times k_aq product:** both enter multiplicatively in dl/dt; with the ADR-0026 C_e COV ≈ 0.782 and k_aq COV 0.50 their product COV is now ≈ 0.93 (was ≈ 0.71 under the old C_e prior). The high-C_e, high-k_aq corner of the prior produces progression rates several times the deterministic baseline — the more so with the raw-head reversal (ADR-0027) and the higher C_e mean, both of which push transient P_f up. This is physically defensible (these are realizations that should fail) but means the prior transient fragility sits well above deterministic-C_e predictions, so the Phase 2 posterior shift looks more dramatic. Be prepared to explain this in the discussion: the apparent strength of Bayesian calibration partly reflects giving the filter more parameter freedom, not solely the informativeness of the 2016 survival observation. This product is also the interaction the deep tail is governed by, which bears directly on §12 Failure modes 5 and 7, the ADR-0029 tail-estimator study, and the ADR-0033 GSA that measured it (see below).

**The effective stochastic input space is 8-D, and it has been decomposed (ADR-0033).** With `seepage_length_cov` set (0.2 in every generated config), the independent L draw joins the seven θ columns as an eighth input. The Stage 6.5 variance-based GSA (Sobol' S_i / total-effect ST_i via the Saltelli-2010 radial design with scrambled-Sobol' sampling and Jansen's ST estimator; `sensitivity.py` + `gsa_qoi.py`, machinery validated on analytic benchmarks before touching the engine) decomposed four QoIs — the transient and static failure indicators, l_e/L, and Z_static — at four conditioning levels on the governing pair KP58.8+KP60.0. Headlines: **the stochastic seepage length L is the top- or co-top-ranked total-effect input for every QoI** (it acts through H_c, the rate denominator, r_e, and the criterion Z = L − l_e itself) — a hard ceiling on Phase 2 posterior tightening, since Accept–Reject filters only the 7-column θ matrix; at the fragility shoulder the transient indicator is ~76% interaction variance, with C_e's influence persistently interactive rather than marginal (S ≈ 0.07 vs ST ≈ 0.34 at the KP58.8 design level) — so the 2016 survival evidence constrains the joint high-rate corner, not the C_e marginal; and the structural zeros (C_e, D_bl, k_bl, γ'_bl on the static QoIs) come back exactly 0.0, a free validation of the head-separation architecture. Because the production prior is independent (ADR-0012 two-population + independent L), plain Sobol' indices are exact; a bounding Nataf ρ = 0.6 companion via the Rosenblatt/generator route (Mara–Tarantola full/independent indices) leaves the ranking unchanged.

**The L marginal and its independence are the adopted production model (seepage-length L study, 2026-07-19; `docs/decisions/seepage-length-L-study.md`).** Because the GSA put L on top, the model was scrutinised on three axes and **kept unchanged** (no default touched, no new binding ADR): (1) *Marginal* — CoV 0.20 (0.15 at KP60.0), lognormal, is the thesis `tab:seepage_length_prior` / L-determination-memo engineering judgement; base-width scatter alone implies CoV ≈ 0.08–0.16, so 0.20 is a padded, mildly-conservative lumped allowance (no external fitted CoV(L) exists — Dutch practice treats L deterministic). The **transient shoulder P_f is ~3–4× sensitive to CoV(L) over 0.10–0.40** while the design level is robust (≤ 1.4×), and the physically-indicated *one-sided upside* (longer L from berm/boundary) would *cut* P_f ×0.33–0.57, so the symmetric prior is conservative — **the shoulder CoV(L) band must be reported as the dominant epistemic knob there**, with the memo's one-sided-upward case as its complement. (2) *Spatial correlation* — L independent per section is correct for the production `exact` deliverable (four OYO sections 1.2–2.0 km apart ≫ any λ_ac; reach-union independent/comonotone bounds within 1.4–1.7×). The inter-segment independence over-counts by exactly λ_ac/spacing (= 1.25 at λ_ac = 250 m) — the reach-scale restatement of ADR-0037's within-segment n_eff — so a densely-populated reach (the `nearest` policy, or the future 土層縦断図) must be composed through the reach-scale length effect, never naive independence (pure helpers `system_integration.composition.length_effect_effective_count` / `reach_union`, opt-in, default = independence). (3) *Phase 2 ceiling* — the 2016 survival barely moves L (posterior mean +0.5–1.4 %, CoV −1.7–3.6 %) while it shifts k_aq/C_e ≈ 4 %, so the ST_L ≈ 0.49–0.78 total-effect share L carries is **irreducible by any θ-only survival evidence**; the Bayesian-updating claim is scoped accordingly (survival tightens θ, not the fragility-dominant geometry L). **The mean values were re-measured from a 2025 GSI DEM5A lidar surface and the result was adopted at ONE section (ADR-0047, 2026-07-28; adoption 2026-07-29; `docs/decisions/0047-dem-surveyed-seepage-length.md`).** Clean-station window medians read 36 / 42 / 43 / 40 m at KP57.4 / 58.8 / 60.0 / 62.0 against the 1998 CSV 33.0 / 35.0 / 34.8 / 47.0 m. **KP62.0 was adopted (47.0 → 40.0 m)**: its 1998 value credited a landside berm that the 1998 OYO 様式-5 sheet did not model, that provenance §3.2's `unreinforced` classification denies, and that 28 of 28 clean stations do not show — a defect, not a vintage difference, and under-conservative at the governing section. **KP57.4 / 58.8 / 60.0 are HELD at their 1998 values** (KP57.4 shows no resolvable change; the two `drained` sections' +7/+8 m is genuine post-1998 remediation geometry, and adopting only its anti-conservative half while the engine still models no toe drain is not an improvement); their DEM values are carried as the measured, unadopted epistemic bracket. The measured along-levee spread (CoV 0.073–0.184) brackets the 0.08–0.16 base-width figure above and so **confirms** that component of the prior — it does not license narrowing 0.20/0.15, which is therefore unchanged everywhere, because the padding covers the unverified landside blanket boundary and exit position that a bare-earth surface cannot see. **Crucially, the L bracket does NOT cancel in the static-vs-transient ratio** (ratio-of-ratios ×2.25 / ×1.64 / ×2.23 / ×0.475 at design HWL, all 87 evaluated levels resolved at 95%): both branches share `H_c`, but `L` additionally enters the transient side through `Z = L − l_e` and the ODE rate denominator, so it is **not a common-mode knob**. Stage 6.6's bias headlines are therefore L-conditional, and remain so for the three held sections. **L is neither the only non-cancelling knob nor the largest:** `k_aq` departs further (max resolved ×82/×66/×163/×46, `epistemic-bracket-synthesis.md` §4(c)), because it carries *two* transient-only channels (`r_e` → the uplift/heave gate, and the ODE rate) where L carries one. The surviving general rule: **a bracket cancels in the static-vs-transient ratio only if it is pure common-mode**, `m_p` being the only knob measured to qualify (by ADR-0045 §2 construction). Cancellation is measured per knob, never assumed from "shared sample, fixed parameter".

---

## 8. Output Data Structures for Phase 2 Handoff

The FragilityResult object described in §2 is the primary handoff. Think carefully about what Phase 2 actually needs.

Phase 2 Accept-Reject filtering operates on the **prior θ matrix**, not the fragility curve. The procedure: take the N by 7 prior matrix from Phase 1, run each row through the transient evaluator with the 2016 hydrograph h_2016(t), reject rows whose Z_transient < 0, and keep survivors as the posterior sample.

Phase 2 needs:

1. The raw `theta_matrix` (N by 7), to filter.
2. The `param_names` list, so column identities are unambiguous.
3. The deterministic 2016 hydrograph (separate input, not part of FragilityResult).
4. The cross-section geometry and config used in Phase 1, so filtering replays under identical assumptions. Embed a config snapshot in `metadata`.
5. The Phase 1 evaluator function M8 itself, so Phase 2 is not reimplementing physics.

The cleanest interface: expose M8 as a public function with a stable signature, and have Phase 2 import it directly. The filtering becomes:

```python
from bep_reliability_engine.evaluator import evaluate_realization

results_2016 = [
    evaluate_realization(theta_matrix[j], h_2016, geometry, l_ini=0.0)
    for j in range(N)
]
surviving_mask_trans  = np.array([r.Z_transient > 0 for r in results_2016])
surviving_mask_static = np.array([r.Z_static    > 0 for r in results_2016])
theta_posterior = theta_matrix[surviving_mask_trans]
```

**Survival-discrimination decomposition.** Because M8 returns both Z_static and Z_transient under h_2016, the filtering step yields two rejection sets, not one. Realizations rejected by the static criterion would have failed even at peak head, so their rejection reflects geometry, material resistance, or sub-critical loading, not any time constraint. The marginal informativeness of the 2016 survival for the time-dependent mechanism is therefore the additional rejection produced by the transient criterion beyond the static one, evaluated within the remediation state assigned to each segment. Record both rejection fractions side by side. This is the artifact that answers the survival-discrimination question (whether 2016 survival genuinely constrains progression or is already explained by simpler physics), and the `metadata.remediation_state` and `metadata.d70_interpretation` fields exist so the decomposition can be stratified across remediation states and grain-size interpretations.

**This handoff design is now realized (ADR-0034/0035/0036).** Phase 2 is the built `bayesian_reliability_updating` package: it replays the Phase 1 run from its metadata snapshot (config hash-checked, θ and stochastic L regenerated bit-for-bit), evaluates every realization through M8's additive batch twin `evaluate_batch_diagnostics` (which `evaluate_batch` now delegates to; ADR-0034), and Accept-Reject filters against the observed 2016 typhoon stage — h_2016 taken from the Obihiro record through the inverse gauge rating and the section rating (verbatim M3) and peak-anchored to the surveyed right-bank flood trace (ADR-0035) — on the run's own 225 s grid (ADR-0036, superseding ADR-0022 decision 2's 1800 s). The evidence set is **closed at 2016** (ADR-0044): the 2011/2006 stage records never materialized, and a sustained-peak bound rejects zero rows at seven of eight strata, so those events add no informative rejection. The z_toe exit datum is carried as a systematic per-section **epistemic scenario**, never a stochastic column, via the replay-only `z_toe_delta_m` knob (±0.3 m, default 0.0 bit-identical, outputs name- and metadata-stamped so a scenario never masquerades as baseline; ADR-0046).

For this to work, M8 must be importable without notebook context, which directly motivates the architecture recommendation in §9.

**Persistence format:** HDF5 via h5py for the large arrays; JSON sidecar for config metadata. Avoid pickle for long-term storage (Python version brittleness); avoid CSV for matrices (slow, lossy for floats). One HDF5 file per cross-section per scenario is a reasonable granularity. As-built schema (`FragilityResult.save`/`load`):

```
/theta_matrix             (N, 7)  float64
/param_names              (7,)    string
/conditioning_grid        (N_h,)  float64
/failure_matrix_static    (N, N_h) bool     # object field is failure_matrix_stat (naming maps in save/load)
/failure_matrix_trans     (N, N_h) bool     # object field is failure_matrix_tran
/P_f_static_raw           (N_h,)  float64
/P_f_trans_raw            (N_h,)  float64
/bootstrap_bands/{static,trans}_{lo,hi}     (N_h,) float64
/binomial_ci/{static,trans}_{lo,hi}         (N_h,) float64   # ADR-0024, always on
/attrs:  fit_static_{mu,sigma,datum_m}, fit_trans_{mu,sigma,datum_m}  # NaN encodes a None (unbracketed) fit
```

The full provenance block — `config_hash`, the config snapshot, `c_e_stochastic=True`, `correlation_rho_k_d70`/`_status`, `d70_interpretation`, `remediation_state`, `lhs_seed`, `cross_section_id`, `segment_id`, `scenario`, `code_version`, `hydrograph_source`+`hydrograph`, `aquifer_lag_active`, `tau_aq`, `progression_backend`, `foreland_treatment`, `alpha_exponent`(`_transient`), `fragility_deliverable`, `fragility_fit`, `mc_convergence`, `leakage_geometry`, `length_effect` (ADR-0037, when enabled), `bootstrap` — lives in the **JSON sidecar**, not in HDF5 attrs (the §8 sketch listed some of these as attrs, but HDF5 attrs cannot hold `None` (e.g. `tau_aq`) or nested dicts). The HDF5 root attrs carry only the fitted `(mu, sigma, datum_m)` per branch.

---

## 9. Recommended Package Architecture

**Recommendation: modular .py package with thin notebook drivers.** I will be specific because the distinction matters more for this project than it might seem.

Reasons against pure-notebook architecture:

1. **Phase 2 must import M8.** Notebooks can be imported via nbformat or jupytext, but it is fragile and ugly. Functions called from other code belong in .py files.
2. **Unit testing the physics.** You will want pytest coverage on `sellmeijer_static`, `pol_ode_progression`, and `hydraulic_translator`, testing against the Pol 2024 published examples and Sellmeijer 2011 fine-tuning experiments. Pytest on notebooks is painful; on .py files it is trivial.
3. **Refactoring during a long thesis.** You will discover physics bugs in month 3 and need to rerun everything. If physics is in cells, you will be copy-pasting fixes between notebooks. If it is in a module, you fix once and re-import.
4. **Version control diffs.** Git diffs on notebook JSON are unreadable; diffs on .py files are reviewable.
5. **Reproducibility for defense.** A .py package with pinned requirements and a notebook entry point is what you hand to anyone and have it just work.

**Recommended layout:**

The importable package is **`bep_reliability_engine`** (the spec drafts and some ADRs call it `bep_phase1`; the implemented, importable name is authoritative — ADR-0003). As-built layout (differs from the original sketch in the ways noted):

```
bep-reliability-engine/
├── bep_reliability_engine/           # importable package
│   ├── __init__.py
│   ├── constants.py                  # GAMMA_W, GRAVITY (calibrated-model constants)
│   ├── config.py                     # M1: pydantic models
│   ├── sampling.py                   # M2: LHS sampler + coupling (ADR-0012) + independent L
│   ├── tail_sampling.py             # deep-tail tilted-IS sampler (ADR-0029; not the sweep)
│   ├── hydrographs.py                # M3: d4PDF loader, rating, canonical-shape scaling
│   ├── bank_heights.py               # HWL loader from the 2019 tables (ADR-0018)
│   ├── hydraulics.py                 # M4: r_e, λ_in/λ_out, optional lag state
│   ├── initiation.py                 # M5: uplift, heave, I_er logic
│   ├── sellmeijer.py                 # M6: H_c, l_c, optional 3D scale exponent
│   ├── progression.py                # M7: Pol ODE timestepper (numpy fast path)
│   ├── progression_numba.py          # M7 opt-in Numba backend (ADR-0029, [accel] extra)
│   ├── evaluator.py                  # M8: combined limit-state evaluator (scalar + batch)
│   ├── fragility.py                  # M9: curve fitting, FragilityResult, HDF5+JSON persistence
│   ├── convergence.py                # N-ladder convergence statistics (ADR-0031; physics injected)
│   ├── sensitivity.py                # Sobol'/GSA designs, estimators, generator→physical map (ADR-0033; physics-free)
│   └── gsa_qoi.py                    # GSA batch QoI adapter mirroring M8 (ADR-0033; drift-guarded bit-identical)
├── run.py (in-package)               # run_fragility_analysis orchestrator (no physics)
├── tests/                            # pytest suite (Pol/Sellmeijer/Mazure reference cases + integration)
├── notebooks/                        # thin drivers only — no physics
├── configs/                          # 8 generated YAML configs (historical only, ADR-0023)
├── data/                             # geotech inputs; raw d4PDF hydrographs (gitignored)
├── results/                          # FragilityResult HDF5 + JSON sidecar files
├── scripts/                          # generate_configs.py (regenerates configs/ from the geotech CSV);
│                                     # run_sweep.py (production sweep driver, interpretation-qualified names);
│                                     # study drivers: tail_variance_study (ADR-0029), convergence_study
│                                     # (ADR-0031), aquifer_response_diagnostic (ADR-0032), gsa_study
│                                     # (ADR-0033); validate_*.py (Japanese case-validation campaign,
│                                     # docs/validation/); plot_*.py
├── pyproject.toml                    # packaging + [accel] extra; requires-python 3.11 only
└── README.md
```

Notes on drift from the original sketch: there is **no `io.py`** — HDF5+JSON persistence lives on `FragilityResult.save`/`load` in `fragility.py`. `run.py` is the concrete `run_fragility_analysis` orchestrator (it contains no physics; everything routes through M8). The added modules — `tail_sampling`, `bank_heights`, `progression_numba`, `constants`, `convergence`, `sensitivity`, `gsa_qoi` — postdate the sketch.

Notebooks become thin drivers: they import from `bep_reliability_engine`, configure a run, execute, and visualize. They do not contain physics. The notebook for a fragility run is essentially:

```python
from bep_reliability_engine import Config, run_fragility_analysis, plot_fragility
cfg = Config.from_yaml("configs/tokachi_kp58.yaml")
result = run_fragility_analysis(cfg)
result.save("results/tokachi_kp58_historical.h5")
plot_fragility(result)
```

Everything else, the 10^5-iteration machinery, is in the package.

**Pragmatic transition path:** start in a single notebook for the first two weeks while debugging the physics on small N (say 1000). Once physics is stable, refactor into the package layout. Commit to completing this refactor by the Phase 1 start week of your Gantt, not deferring indefinitely.

---

## 10. Python Package Ecosystem

**Minimal stack:**

- **numpy**, backbone for all numerics.
- **scipy.stats**, distribution sampling and lognormal fitting for fragility curves (`scipy.stats.lognorm.fit`).
- **scipy.stats.qmc.LatinHypercube**, built-in LHS sampler since SciPy 1.7. Do not reach for pyDOE. The Nataf correlation step is layered on top of the QMC uniform design.
- **pandas**, DataFrame for theta_matrix at module boundaries; convert to ndarray inside hot loops.
- **joblib**, parallelism across conditioning water levels; clean persistence via `joblib.dump`.
- **h5py**, long-term storage of large arrays.
- **matplotlib**, fragility curves and diagnostic trajectories. Add seaborn for nicer defaults.
- **pydantic**, config validation; catches unit errors at load time.
- **pytest**, non-negotiable for physics unit tests.
- **tqdm**, progress bars on the outer loop; sanity-saving on long runs.

**Optional but valuable:**

- **xarray**, labeled multi-dimensional arrays (cross-section by scenario by climate by h_i by static/transient). If you anticipate analysis growing along these dimensions, adopt from the start.
- **numba**, no longer merely "held in reserve" — profiling justified it (ADR-0029). It is the **opt-in** `[accel]` extra behind `config.timestepper.progression_backend='numba'` (default `numpy`), giving a further ~4× over the already-restructured numpy path, at the cost of < 1e-10 (non-bit-identical) equivalence. Optional; the default `numpy` path needs it not.

**Avoid:** TensorFlow, PyTorch, and **JAX** — the JAX rejection is now empirical (ADR-0029): a `lax.scan` float64 kernel of the same math ran 5.6× slower than Numba on CPU, deviated 5.5e-7 from the numpy path (four orders outside the 1e-10 bound, because XLA fuses/reorders and substitutes its own transcendentals), and current releases need numpy ≥ 2 against the project's `numpy<2.0` pin, with no autodiff/GPU benefit for this workload. Also avoid scipy.integrate.solve_ivp for the timestepper, since forward Euler is what Pol uses and adaptive integrators fight the I_er discontinuities (spec §13, ADR-scope).

---

## 11. Convergence and Validation Strategy

**Convergence diagnostic.** Monitor the coefficient of variation of P_f-hat at the lowest failure probability of interest as N increases. Standard practice (Schweckendiek 2014) targets CoV < 5% across the relevant failure range; sample sizes of order 10^5 typically achieve this, and this sufficiency is verified directly for each cross-section once the engine runs rather than assumed. This verification was carried out for **both reachable sections, KP58.8 and KP60.0** (ADR-0031, an empirical N-ladder with R = 50 replicates each; KP60.0 reproduces the KP58.8 picture point for point as an independent confirmation): the empirical LHS CoV falls as 1/√N and N = 10^5 meets the 5% target across the whole bracketed curve and for per-level transient P_f down to ≈ 5·10⁻³, degrading to ≈ 16% at P_f ≈ 3·10⁻⁴ (the raw-tail regime below); N = 10^5 is retained. The per-level CoV is now computed on every run and recorded in `metadata['mc_convergence']` — ADR-0031 confirms this analytic-binomial block tracks (and mildly beats, in the bulk) the empirical LHS CoV, so it is a trustworthy sufficiency statement. For levels where P_f-hat < 10^-4, monitor CoV explicitly; at tail-only branches this target is structurally unmeetable and the ADR-0024 raw-tail-with-binomial-CI deliverable acknowledges it (and ADR-0029's tilted importance sampler is the tool for sub-decade tail quantification). Bootstrap resampling of the realization set provides confidence bands on fitted fragility curves (degenerate replicates skipped, counted in metadata — not raised).

**Aquifer-response diagnostic (gated the M4 lag option — executed, ADR-0032).** τ_aq ~ λ_in² · S_s / k_aq (≡ S_s · D_aq · D_bl / k_bl — k_aq cancels, so τ_aq depends on three of the seven sampled variables; S_s is a deterministic config value, the activation flag is global per run, and τ_aq would be a per-realization vector once active, ADR-0004). To make the verdict falsifiable, every discretionary input was **pre-registered before any τ_aq was computed** (ADR-0032 Part 1): the literature S_s range 1×10⁻⁵–1×10⁻⁴ m⁻¹ for the dense sand–gravel with the *upper bound* as decision driver; the denominator sharpened from "characteristic flood duration" to the base-flow-to-peak rising-limb time **T_rise** (the correct comparison for a fill lag), with the plateau width T_plateau as the stress cross-check; the threshold Π\* = 0.10 anchored to a first-order head-deficit argument; and the governing pair KP58.8/KP60.0, which upper-bounds τ_aq over all reachable sections. Part 2 then applied the rules unchanged: **Π = τ_aq/T_rise ≈ 0.010–0.012 centrally — an order of magnitude under the threshold — so the instantaneous default is retained everywhere.** Quote that margin with its Π: it is Π\*/Π_central over the **ensemble-median T_rise** (18 h), i.e. 9.5 (KP58.8) / 8.5 (KP60.0). It is *not* the per-run `metadata['aquifer_response'].margin_vs_threshold`, which is the stricter Π\*/Π_corner90 over the run's own canonical-event T_rise (23 h) and reads 3.83–19.54 across the four sections. Both clear Π\* at every section; τ_aq is identical in both (680 s / 765 s), so they are one quantity under two denominators and are reconciled in the companion note, not in tension. Even the p99-τ_aq × flashiest-decile-T_rise stress conjunction stays below Π\*; **S_s did not bind** (the verdict is insensitive across and well beyond the committed range, so no uncertain input was introduced). Check B (native resolution) also passed: the measured loading is far broader than the earlier "~1.5 h plateau" characterization — median rising limb 18 h, plateau 9 h — so the 3600 s cadence carries ~9 samples across the peak. The outcome, τ_aq values, and timescales are recorded per run in `metadata['aquifer_response']` (`hydraulics.aquifer_response_diagnostic` + `hydrographs.flood_timescales`; one source of truth for the offline study and production metadata). Scope caveat (ADR-0032 amendment): the Π screen detects elastic leaky-confined response only and its verdict applies where the aquifer is channel-connected and saturated at base flow — confirmed for all four production sections; outside that regime (dead-ended lenses, dry-foreland entry, depressed initial heads) a transient-fill assessment is needed and the instantaneous form errs conservative on the gate head.

**Timestep convergence test.** Because forward-Euler overshoot is most severe on steep rising limbs, run this test with the parameter combination drawn from the high-progression-rate tail that most stresses the scheme: high k_aq, high C_e, and low D_bl. Compare l_e at Δt and Δt/2 and confirm it differs by less than 1%. Pol uses Δt = 10 s for small-scale and 100 s for large-scale. The native d4PDF *data* resolution is **3600 s (1 h), final for this data drop** (ADR-0019 §6) — but data fidelity and integration fidelity are separate concerns (ADR-0030). ADR-0022's acceptance of native 3600 s as the integration Δt was **superseded by ADR-0030** after the ADR-0026/0027 material rate-law changes triggered its own revalidation clause: the first end-to-end sweep under the new physics surfaced rows failing **transient-but-not-static** — impossible in continuous time under the shared-sample, single-source-H_c contract, and diagnostic of discrete Euler steps jumping the H_eq equilibrium barrier in the hot C_e·k_aq tail (the transition shoulder was inflated up to ~27×; the ADR-0022 protocol itself passed at the top levels and missed the artifact region). A Δt-halving ladder converges (≤1% relative at every checked level, worst shoulder level flat to MC precision) at **Δt = native/16 = 225 s**, which every generated config now pins (`timestepper.target_dt_seconds: 225.0`), applied via the ADR-0013 resample-at-record-construction hook (`hydrographs.resample_record`: linear interpolation onto integer subdivisions of the native grid — every native sample stays a node, `peak` preserved, the loading signal unchanged; only the Euler grid is refined). Future revalidations must include shoulder levels (raw 10⁻³ ≤ P_f,trans ≤ 10⁻¹) and report the per-level trans-and-not-static fraction (≈ 0 in the continuum), not only the most active levels. The **Phase 2 per-realization 2016 replay runs on the Phase 1 run's own 225 s grid** (ADR-0036, superseding ADR-0022 decision 2's 1800 s), so the Accept–Reject filter — which is *more* Δt-sensitive than the population-level P_f — shares the population sweep's convergence footing. The kernel-level Δt/2 test remains at 600↔300 s as a scheme guard. The **literal worst-case single-realization form of this test is executed (ADR-0039, 2026-07-13)**: the flashiest real ensemble member (HPB_m049_2001 — 25% of the event amplitude in one native step, vs the production canonical shape's 8%, rank #2281/3000) × the p99-k_aq/p99-C_e/p01-D_bl tail vector at KP58.8 and KP57.4, ladder 3600 → 14.0625 s on a 0.05 m refined threshold grid plus a p01-L variant (`scripts/timestep_convergence_stress.py`). Verdict: native is badly non-converged (breach threshold 0.80 m of stage too low at both sections; 12 trans-not-static levels, 0 from 900 s); the **failure indicator is Δt-stationary at 225 s** (threshold fixed from 450 s, zero stall/breach flips down to 14 s), so production stays at 225 s; but the literal ≤1% l_e criterion at sub-breach staircase levels needs **Δt ≤ 112.5 s** (KP57.4: 16.8% l_e residual at 225 s on a pipe stalled near 3 m) — binding on any consumer of l_e *magnitudes* rather than flags.

**Physics validation tests** (pytest):

1. **Sellmeijer reproduction.** Compute H_c for the IJkdijk test cases reported in Sellmeijer 2011 Table 1; require agreement within reported regression scatter.
2. **Pol small-scale reproduction.** Run progression.py against Pol 2024 B25-245 and FPH calibration cases; require l_e(t) agreement within experimental scatter using Pol's calibrated C_e (B25-245 = 0.010, author-confirmed 2026-07-08; the Fig. 5 caption's 0.014 is an error — ADR-0026). These are r_e = 1, D_bl = 0 geometries, so the raw and r_e-attenuated erosion heads coincide and every M7 reference test is bit-identical after ADR-0027. As part of this test, verify that the H_c anchoring H_eq and the erosion-driving head H_erosion = (h − z_toe) − 0.3·D_bl (the **raw** outer level, ADR-0027) share the head datum h_e = z_toe of Pol SIE 2024 Eqs. (6) and (8), so the crack-resistance term is applied at the correct point in the balance. (In-domain progressive-phase rate/shape is additionally gated by the L = 3 m S2-2 DgFlow case; ADR-0009.)
3. **Mazure analytical check.** For an idealized cross-section (no foreshore, λ_in computable in closed form), require r_e agreement with hand calculation to machine precision. If the lag option is active, also confirm that as τ_aq goes to zero the lag state reproduces the instantaneous translation.
4. **Conservation and monotonicity.** Assert l_current is monotonically non-decreasing across every timestep in every realization. Assert l_e <= L at termination. Assert I_er never goes from true to false except via heave inactivation.
5. **Degenerate-case smoke tests.** A toe-drained segment with the exit head forced to z_toe must yield Z_u, Z_h >= 0 for all stages and P_f going to 0. Note that this zero-exit-head idealization represents as-designed drain performance and assumes continued drain functionality; it is optimistic rather than conservative with respect to clogging or degradation, and a degraded-drain sensitivity is a planned run, not part of the baseline. A cross-section with C_e going to 0 must yield Z_trans going to L − l_ini regardless of hydrograph.

---

## 12. Failure Modes and Architectural Tradeoffs

**Failure mode 1, silent unit inconsistency in r_e.** Mazure mixes hydraulic conductivity [m/s], geometric lengths [m], and dimensionless factors. A factor-of-86400 error from m/s versus m/day produces λ_in values that look plausible but are off by orders of magnitude. Mitigation: single-realization integration test against a published Mazure analytical case before trusting any fragility output. Use pydantic with units annotations in config.

**Failure mode 2, H_c non-physical for extreme θ tails.** Lognormal sampling with COV = 0.5 on k_aq produces a heavy right tail. Combined with small d_70 samples, F_s can produce H_c values near zero or unstable values via F_g. Mitigation: clip θ samples to physically defensible bounds (for example d_70 within [50 μm, 1 mm]) at the sampler stage. Add an assertion in `sellmeijer_static` that H_c > 0; log and skip realizations that fail, tracking the skip rate. A skip rate above 1% indicates priors need re-bounding.

**Failure mode 3, forward Euler timestep too large — realized and fixed (ADR-0030).** The effective time constant of the dl/dt response can be short in the hot C_e·k_aq tail; if Δt is too large, a single step jumps the H_eq equilibrium barrier past l_c, after which the descending branch gives runaway to breach. This failure mode was *realized in production* at the native 3600 s (shoulder P_f,trans inflated up to ~27×, detected via the trans-but-not-static consistency property rather than the top-level convergence protocol). Mitigation, as delivered: the 225 s integration grid (ADR-0030) plus the amended §11 revalidation protocol (shoulder levels + per-level trans-and-not-static fraction).

**Failure mode 4, static-vs-transient bias conflates several physical effects.** The intended finding "static overestimates because it ignores time" is partly conflated with non-temporal effects, now **four** in total. First, the static Sellmeijer assumes 2D plane-strain and inherits the 2D scale exponent α = −1/3, while the Pol ODE was calibrated against 3D experiments carrying α = −1/2; at field seepage lengths the 3D critical head can be roughly half the 2D value, a magnitude comparable to the temporal effect (the **dimensional** component). Second, the transient branch applies Pol's crack-resistance reduction H_erosion = (h − z_toe) − 0.3·D_bl, while the static comparator uses the raw gross head with no crack term; this is the **head-convention** component. Since ADR-0027/0028 removed r_e from *both* piping heads, this component is cleanly **exactly 0.3·D_bl** — the r_e attenuation that the earlier convention would have added (a large confound that would have masqueraded as a temporal effect, the very FM4 error this section warns against) is gone. Third, Pol's Eq. (11) equilibrium curve rides its intentionally conservative 0.9·H_c end anchor, inflating the progressive-phase rate ≈ 1.95× at the in-domain L = 3 m scale — the **H_eq-conservatism** component (ADR-0009; field-scale magnitude an open verification with Pol). The static-transient gap therefore combines a temporal component plus these three non-temporal ones. Mitigation: do not claim the entire gap is purely temporal. The **dimensional** isolation is wired as the transient-only `alpha_exponent_transient` (recomputes a separate transient H_c at α = −1/2 while the static keeps −1/3 — ADR-0017; the −1/3 baseline is Pol-endorsed for the thin-blanket site, the −1/2 a Discussion-only sensitivity). The head-convention component is measured at the comparator level (the C1 crack-reduced static analysis variant of ADR-0040; `CRACK_RESISTANCE_FACTOR` itself stays unthreaded), and the H_eq-conservatism isolation is now the opt-in keyword-only `equilibrium_end_factor` override on M7/M8-batch (ADR-0041; default None ≡ 0.9 bit-identically, refused on numba, not a config field). **The full decomposition is executed (Stage 6.6, ADR-0040, 2026-07-17; `gap_decomposition.py`, `docs/stage6_6_report.md`)** on KP62.0+KP57.4 at N = 1e5 via a ten-comparator ladder on one shared sample (statics C0/C0b/C1/C2, the exact analytic sustained-peak limit C3a/C3b — failure ⇔ gate ∧ H_erosion > H_c,trans, ODE-verified to zero disagreements at 64 d holds — and transients C4a–C4d), production C0/C4b bit-identical to the persisted sweeps, all Euler-flip counts exactly 0. Headline attribution (**magnitudes updated by ADR-0047, 2026-07-29 — the decomposition structure below is unaffected, only the KP62.0 bias magnitude moved**): the total conventional-practice bias must always be quoted with its level. **Resolved at N = 1e6 (2026-07-30, `adr0040-hwl-bias-resolution.md`, closing the campaign's decision 6): at KP62.0 the design-HWL bias is 26.9 (95% CI [21.6, 35.3]) on 63 failing rows** — the "44.7 on 4 rows" of the N = 1e5 record was counting noise that overstated it 1.66×, and the withdrawn L = 47 m "~21×" is superseded twice over. Under the adopted L = 40 m the bias is 21.6 at 46.50 m, 10.5 at 47.0, 6.3 at 47.5 and 2.4 at 49.0; it falls resolvably with stage (paired ρ = 1.249 over the 11 cm between 46.39 and 46.50 m), so a figure without its level is meaningless. **KP57.4 remains unresolved even at N = 1e6 (2 failing rows): quote the bound B ≥ 148 at HWL — superseding the "≥32×" zero-row bound — and lead with 42.7 [39.4, 46.6] at 39.50 m.** At N = 1e6 KP57.4 also exposes 4 Euler barrier-jump rows in 1e6 (levels 39.50/40.25/40.75, none at an anchor); production runs at N = 1e5 where the gate passes, so no production result is affected. Every bias figure is **L-conditional and k_aq-conditional**: neither bracket cancels in the static-vs-transient ratio (L: ratio-of-ratios 2.25/1.64/2.23/0.475, all 87 evaluated levels resolved at 95%, ADR-0047 §4.5; k_aq: max resolved departure ×82/×66/×163/×46, larger still, `epistemic-bracket-synthesis.md` §4(c), which **refuted** ADR-0048's contrary claim), because each enters the transient branch through channels the static one does not — L through `Z = L − l_e` and the ODE rate denominator, k_aq through `r_e` and the rate itself. `m_p` is the only knob measured to cancel, by ADR-0045 §2 construction. The attribution itself is unchanged: temporal-dominated through the shoulder (58–76% of the production gap; pure temporal ratio C3/C4 ≈ 2–8), head-convention-dominated in the design-level tail (85–97%), initiation gate immaterial to the production gap, H_eq-conservatism +10–25% of transient P_f (secondary — the ≈1.95× rate factor compresses at the indicator level), dimensional component absent from the production gap by construction and sign-flipping between d70 interpretations (−0.5 matrix / +0.4 bulk at the shoulder). Component magnitudes are order-conditional (measured static-pair Shapley interaction up to +0.14 at KP57.4); the temporal component must still not absorb the other three.

**Failure mode 5, LHS variance reduction in the tails — the naive claim is now refuted (ADR-0029).** LHS improves the coverage of each marginal axis, so it was *expected* to tighten the CoV of P_f-hat relative to crude Monte Carlo at the same N. This expectation carried a caveat in tension with Failure mode 7: the deepest part of the failure tail is governed by the multiplicative interaction C_e times k_aq, and LHS stratifies marginals, not interactions. The empirical study the spec demanded was run (KP58.8, N = 10⁴, real physics; `scripts/tail_variance_study.py`, ADR-0029) and **refuted the naive claim**: LHS shows a real but modest CoV advantage only in the *bulk* (MC/LHS ≈ 1.13 at P_f ≈ 0.28) and **no detectable advantage anywhere in the failure tail** (P_f ≤ 1.6·10⁻², where its CoV matches the iid binomial formula). A full N-ladder verification on the current physics (ADR-0031, R = 50 replicates, `scripts/convergence_study.py`) reproduced this and sharpened it: the ladder-mean ratio decays from **1.40 ± 0.09 in the bulk** (P_f ≈ 0.26) to **1.00 ± 0.06 in the deep tail** (P_f ≈ 3·10⁻⁴) at KP58.8, **reproduced point for point on the independent second section KP60.0** (1.48 ± 0.06 → 1.01 ± 0.04), and the static branch — identical but for having no C_e — keeps a ~1.1–1.3 advantage throughout, isolating the C_e×k_aq interaction as the cause. Consequently raw sweep tail points carry crude-MC-grade uncertainty — which is exactly why ADR-0024's Clopper–Pearson presentation is the right uncertainty statement for them. Mitigation, as delivered: keep plain LHS for the production sweep (Phase 2 needs unweighted matrices), and for sub-decade tail quantification use the substitutable **Z-space cross-entropy-tilted importance sampler** (`tail_sampling.sample_theta_tilted`, ADR-0029), which cuts deep-tail CoV 3.2–4.1× (~10–17× sample efficiency) and eliminates zero-failure replicates at P_f ~ 10⁻⁴. Its weighted estimates never enter FragilityResult. **Scope, added 2026-07-30 (`adr0040-hwl-bias-resolution.md` §2.6):** that recommendation holds for a **single-branch** tail P_f, which is what ADR-0029 built and validated the sampler for. It does **not** extend to a **ratio between the two branches** (the Stage 6.6 bias, the WBI+ over-rejection factor). Pointed at the design-HWL bias for the first time, the estimator **failed its pre-registered validation** (V2: one level disagrees resolvably; V4: Kish n_eff 86.9 against a floor of 200) — not through mistuning but structurally: a tilt optimised for the transient region **inflates the static estimator's variance**, 1.50× at the anchor rising to 940× at saturation, while buying the transient side a real 4.66×. A proposal optimised for one branch is the wrong instrument for a ratio between two. Brute force is the method for that estimand; ADR-0029 is not contradicted. Subset simulation was considered and rejected (it would break the front-loaded-RNG reproducibility-by-construction).

**Failure mode 6, memory explosion from storing all l(t) trajectories.** 10^5 times 1000 times 8 bytes is about 800 MB per cross-section per scenario. Across 5 cross-sections by 2 scenarios by static/transient you can blow past 16 GB. Mitigation: default `store_trajectories=False`; retain only Z values and scalar diagnostics. Enable trajectory storage only for the 2016 calibration run and for a 100-realization visualization subset.

**Failure mode 7, C_e times k_aq multiplicative tail amplification.** k_aq is Lognormal COV 0.50 and C_e is now Lognormal COV ≈ 0.782 (ADR-0026, up from 0.50), so their product COV is ≈ 0.93 (was ≈ 0.71). The high-C_e, high-k_aq corner produces progression rates several times the deterministic baseline, dominating the transient failure tail — amplified further by the ADR-0026 ~4× higher C_e mean and the ADR-0027 raw-head reversal. This is physically correct but means the prior transient fragility sits well above deterministic-C_e predictions and the Phase 2 posterior shift looks more dramatic. It is also the interaction that the empirical study confirmed undermines the naive LHS variance claim of Failure mode 5 — and it has now been **measured directly (ADR-0033)**: at the fragility shoulder ~76% of the transient failure-indicator variance is interaction (Σ S_i ≈ 0.24–0.32, with ST − S gaps of 0.6–0.7 on L and k_aq and ~0.4 on C_e and d_70), and C_e's influence is persistently interactive rather than marginal (S ≈ 0.07 vs ST ≈ 0.34 at the KP58.8 design level). The measured near-total absence of additive structure in the tail is the mechanism behind the fm5 parity finding. Mitigation: explain in the discussion that the apparent strength of Bayesian calibration partly reflects giving the filter more parameter freedom, not solely the informativeness of 2016 survival; expect the Phase 2 posterior to contract along the joint fm7 direction rather than the C_e marginal, so marginal posterior standard deviations will understate the information gained. Plot prior and posterior marginals for all seven parameters, with C_e called out specifically, and report how much of the posterior shift is informativeness versus this tail artifact.

**Tradeoff 1, sequential timestepper, numpy versus JIT — resolved (ADR-0029).** The recommendation held: numpy first. The as-built default is the **restructured numpy** timestepper (bit-identical to the kernel loop, 4.5× faster than the pre-ADR-0029 numpy), which ships the thesis. Numba is realized as the **opt-in** `[accel]` backend (a further ~4×, < 1e-10 equivalence, config-owned and metadata-stamped) for the re-sweep campaigns, not the default — the debugging-headache concern is contained by keeping numpy the reference and pinning cross-backend equivalence in tests.

**Tradeoff 2, storing failure_matrix for Phase 2 versus recomputing.** Storing costs about 3 MB (N by N_h bools); recomputing costs about 30 min. Store it. The recompute path should still exist as a code path for reproducibility but should not be the default.

**Tradeoff 3, coupling to Uemura's discretization.** The thesis is committed to the 200 m segment grid and KP boundaries. Fragility output dimensions are fixed by external data, not computational convenience. Architect the FragilityResult to carry segment_id as a first-class index from day one; do not try to retrofit when integrating with Uemura's curves in Phase 3.

### Genuine open decisions (flagged, not resolved here)

These are live items the accepted ADRs deliberately leave open; they are *not* settled by this document and must not be treated as such:

- **Length-effect autocorrelation length λ_ac — RESOLVED (ADR-0037, 2026-07-13).** λ_ac = 250 m primary (Kanning 2012 blanket-thickness correlation distance 200–300 m, midpoint; Schweckendiek 2014 adopts 200 m from the same source), conservative bracket 100 m / 40 m; n_eff = max(1, 200/λ_ac) ⇒ **n_eff = 1 at the primary value** (no amplification — the ADR-0037 finding, to be stated as such). Wired behind `config.length_effect` (generated configs carry it with `enabled: false`; the transform is applied to metadata only, never to the persisted cross-section curves); post-hoc tables via `scripts/segment_fragility.py`. Revision trigger: arrival of the OYO longitudinal soil profile (土層縦断図) → empirical re-estimate. **Reach-scale companion — RESOLVED (seepage-length L study, 2026-07-19).** The within-segment n_eff = 1 clamp discards the between-segment correlation the same λ_ac implies: independence across 200 m segments over-counts the independent failure opportunities by exactly λ_ac/spacing (= 1.25 at 250 m; 0.5/0.2 at the 100/40 m bracket). Immaterial to the production `exact` deliverable (four OYO sections ≫ λ_ac apart; reach-union bounds within 1.4–1.7×), so the item is *latent*: a densely-populated reach (the `nearest` policy, or the 土層縦断図 arrival) must be composed through the reach-scale length effect, never naive independence — pure helpers `system_integration.composition.length_effect_effective_count`/`reach_union`.
- **KP62.0 transient transition still not bracketed.** Re-checked on the ADR-0030 225 s sweep under the current physics: the raw-head reversal (ADR-0027) and higher C_e (ADR-0026) moved the transition from ~15 m to **~4 m above any attainable stage** (ADR-0031 §1) — closer, but still unreachable, so the transient branch there remains raw tail points with binomial CIs, not a fitted curve (ADR-0024). The deliverable form stays classified by the data-driven bracketing criterion on every sweep, never hardcoded.
- **H_eq-conservatism field-scale magnitude (ADR-0009) — RESOLVED at the indicator level (Stage 6.6, ADR-0040/0041, 2026-07-17).** The ≈1.95× progressive-phase *rate* inflation compresses to a **+10–25% transient-P_f inflation** at field scale under the real canonical loading (C4 vs the end-factor-1.0 comparators, both sections, per-level paired CIs; `docs/stage6_6_report.md` §4.4): real, resolved, secondary. It provably cannot appear in any sustained-head failure indicator (the binding barrier is the H_eq maximum H_c, not the 0.9 end anchor — ADR-0040 Decision 2), so it lives inside the temporal step and slightly masks the temporal suppression. The rate-level verification with Pol remains open only for l_e-trajectory consumers.
- **Phase 2 replay timestep — RESOLVED (ADR-0036, 2026-07-12).** The replay runs on the Phase 1 run's own ADR-0030 grid (225 s), superseding ADR-0022 decision 2's 1800 s; per-row Accept–Reject decisions and the retained failure matrices share one convergence footing.
- **KP58.8 r_e-halved QA member — EXECUTED (2026-07-13).** `scripts/qa_re_halved_member.py` (baseline drift guard bit-identical at all 29 levels, N = 1e5): the effect is shoulder-concentrated — max |ΔP_f| = 0.181 at 41.25 m MSL, deep-shoulder suppression to ratios 0.002–0.09 (40.0–40.5 m), parity ≥ 0.99 above 43.5 m, zero new failures (standard r_e confirmed conservative). Per-level table: `results/qa_re_halved_kp58_8.json`; `docs/validation/shikaga-case.md` §3 updated.

(The former "re-sweep pending" flag is discharged: production sweeps under ADR-0026/0027/0028 + two-population coupling have run — the first 3600 s end-to-end sweep of 2026-07-10 was superseded by its own consistency diagnostic, and the 225 s sweeps that replaced it feed ADR-0031/0032/0033. Quantitative fragility numbers quoted in ADRs *older* than 0030 remain superseded and must not be compared against 225 s runs.)

---

## 13. Summary of Single Decisions

For quick reference during implementation, the architectural decisions that should not be re-litigated mid-build:

| Decision | Setting |
|---|---|
| Stochastic parameter vector dimensionality | 7 (includes C_e) |
| C_e prior | Lognormal, mean 0.055, COV 0.782 (ADR-0026; was 0.014 / 0.50) |
| Sampling scheme | Latin Hypercube, 7-dimensional (crude MC as debug fallback only) |
| k_aq–d70 coupling | **Two-population decoupling** adopted (ADR-0012: empirical OYO result; `two_population` mode, ρ recorded 0.0, never imposed). Nataf `correlated` mode retained for sensitivity runs |
| d_70 interpretation | Matrix and bulk both run as co-primary; recorded in `metadata.d70_interpretation` |
| γ'_s split | γ'_p = 16.87 kN/m³ deterministic in F_r; γ'_bl stochastic (6.9, COV 0.056) in the M5 gate only (ADR-0016) |
| Sample size per cross-section | N = 10^5 |
| Conditioning grid size | N_h about 30 (KP62.0: 38 after the static-bracketing extension, ADR-0024) |
| Shared sampling for static/transient | Mandatory, single θ_j feeds both through one M8 call (ADR-0002) |
| Hydraulic translation | Instantaneous Mazure r_e; linear-reservoir lag hook retained in M4 (exact exponential update, ADR-0004) but dormant; per-realization λ_out with finite-foreshore tanh correction (ADR-0005, ADR-0006); `foreland_treatment` blanketed baseline, open-entry on-demand sensitivity (ADR-0025) |
| Aquifer-lag activation | **Instantaneous retained, on evidence** (ADR-0032, executed 2026-07-11): pre-registered Π = τ_aq/T_rise vs Π\* = 0.10 at upper-bound S_s = 1×10⁻⁴ m⁻¹ gives Π ≈ 0.010–0.012 at the τ_aq-bounding pair KP58.8/KP60.0 (~10× margin — Π\*/Π_**central** over the ensemble-median T_rise = 18 h; the per-run `margin_vs_threshold` is the stricter Π\*/Π_**corner90** over that run's canonical-event T_rise = 23 h, 3.83–19.54 across the four sections, same τ_aq; S_s did not bind); recorded per run in `metadata['aquifer_response']`; scope: elastic leaky-confined, channel-connected sections only |
| r_e scope | Drives the uplift/heave gate ONLY (Pol SIE 2024 Eq. 10); neither piping head uses r_e (ADR-0027/0028) |
| Erosion-driving head | H_erosion = (h − z_toe) − 0.3·D_bl in the ODE only, on the **raw** outer level, **no r_e** (Pol SIE 2024 Eq. (6); ADR-0027 superseding ADR-0007); uplift/heave use the r_e-attenuated Δh_blanket |
| Static comparator hydraulic input | **raw gross head** h_peak − z_toe (Sellmeijer 2011 "critical head across structure"; no r_e, no 0.3·D_bl; ADR-0028) |
| Climate axis | Shape-invariant: one canonical HPB shape drives all scenarios; +4K ≡ historical fragility by shape invariance; climate lives on the Phase 3 hazard side; historical-only 8-config sweep (ADR-0023) |
| Fragility deliverable | Fitted lognormal where the grid brackets the transition; else raw tail points with Clopper–Pearson binomial CIs (Optional fits; ADR-0024) |
| ODE integrator | Forward Euler (no solve_ivp) |
| M7 backend | Restructured numpy default (bit-identical); opt-in Numba backend, < 1e-10, config-owned (ADR-0029) |
| Timestep | Δt = native/16 = 225 s for Phase 1 (ADR-0030, superseding ADR-0022's native 3600 s on the ADR-0026/0027 material rate-law changes); Phase 2 replay on the run's own 225 s grid (ADR-0036, superseding ADR-0022 decision 2); kernel Δt/2 guard 600↔300 s |
| Convergence-test worst-case θ | High k_aq, high C_e, low D_bl — executed (ADR-0039): 225 s confirmed for indicator/P_f quantities; Δt ≤ 112.5 s required for l_e-magnitude consumers |
| Recovery rate r_l (Phase 1) | 0 (zero recovery within events) — author-confirmed by Pol (meeting 2026-07-07, re-confirmed in writing 2026-07-08: little is known about recovery, so zero is realistic, *especially for peaks so close together*) (`docs/validation/pol-meeting-2026-07-07-dispositions.md`, Answer 7 / Follow-up email Q3) |
| Trajectory storage | Off by default; on for 2016 calibration and viz subsets |
| Persistence format | HDF5 with JSON metadata sidecar |
| Code organization | `bep_reliability_engine` .py package with thin notebook drivers |
| Phase 2 handoff payload | theta_matrix, failure_matrix_trans, failure_matrix_static, and metadata, all in FragilityResult |
| Phase 2 survival decomposition | Record static and transient rejection separately under h_2016; report marginal transient informativeness |
| Filter dimensionality in Phase 2 | 7 (C_e included; this is the whole point) |
| Global sensitivity analysis | Sobol' S_i/ST_i over the 8-D input space (7 θ + stochastic L): Saltelli-2010 radial design, scrambled-Sobol' sampling, Jansen ST estimator, replicate-t + row-bootstrap CIs; four QoIs at four levels on KP58.8+KP60.0; independent-input decomposition exact under the ADR-0012 prior, Nataf ρ = 0.6 bounding companion via the Rosenblatt/generator route (ADR-0033) |
| Static–transient gap decomposition (Stage 6.6) | Ten-comparator ladder on one shared sample, engine (C0→C1→C3b→C4b) + physics (C0→C1→C2→C3a→C4a) ladders, exact analytic sustained-peak limit (ODE-verified), paired-bootstrap component CIs, static-pair Shapley for path dependence; KP62.0+KP57.4 at N = 1e5, C0/C4b bit-identical to production sweeps (ADR-0040/0041; `gap_decomposition.py`, `docs/stage6_6_report.md`) |
| Length effect | λ_ac = 250 m primary (Kanning 2012 / Schweckendiek 2014 blanket-thickness anchor), bracket 100/40 m; n_eff = max(1, L_seg/λ_ac), n_eff = 1 at primary; config-gated OFF by default, metadata-only when on (ADR-0037). Reach-scale restatement (between-segment): independence over-counts by λ_ac/spacing = 1.25 at primary — pure helpers `composition.length_effect_effective_count`/`reach_union` for a densely-populated reach; never naive-independent (seepage-length L study) |
| Seepage length L | Adopted UNCHANGED (seepage-length L study, 2026-07-19; `docs/decisions/seepage-length-L-study.md`): per-section Lognormal(mean = geometry.L, CoV 0.20; 0.15 at KP60.0), sampled independently of θ and per section. Transient shoulder P_f is ~3–4× sensitive to CoV(L) (design level robust ≤ 1.4×) → report the shoulder CoV(L) band as the dominant epistemic knob + the memo's one-sided-upward case. ST_L ≈ 0.49–0.78 is L-borne and irreducible by the θ-only Phase 2 filter. CoV band already exercisable via `seepage_length_cov`; no new config field. **Re-measured from 2025 lidar (ADR-0047): DEM 36/42/43/40 m vs 1998 33.0/35.0/34.8/47.0 m. ADOPTED at KP62.0 only (47.0 → 40.0 m, 2026-07-29 — the 1998 value credited a berm that never existed); KP57.4/58.8/60.0 HELD, their DEM values carried as an unadopted bracket. CoV unchanged everywhere. The L bracket does NOT cancel in the static-vs-transient ratio (ρ ×2.25/×1.64/×2.23/×0.475 at HWL, 87/87 levels resolved) — L is not common-mode, so Stage 6.6 bias figures are L-conditional; **`k_aq` departs further still** (×82/×66/×163/×46, `epistemic-bracket-synthesis.md` §4(c)), so those figures are k_aq-conditional too, more strongly. A bracket cancels only if it is pure common-mode — `m_p` alone** |
| Phase 3 composition | Third package `system_integration` (BEP-physics-free; ADR-0038): series-system `P_sys = 1 − Π(1 − P_i)` per 200 m segment, BEP input = Phase 2 posterior transient curve (ADR-0024 evaluation policy: fits where deliverable, probit-interpolated raw points otherwise, never extrapolated above the grid), hazard = empirical d4PDF annual-max stage-frequency via verbatim M3 (climate enters ONLY here, ADR-0023), Uemura curves + section table = typed seams with validating loaders |
| Uemura surface curves (D1, closed) | Faithful re-execution of Uemura's own P1 (overflow, Dean cumulative work) and P2 (fluvial scour, USACE excess shear) models on his own committed inputs (`system_integration/uemura_models.py`, quarantined external physics; ADR-0042): canonical-shape conditioning (`HPB_m064_1987`, G1 rule), common random numbers across levels (exactly monotone), N_MC = 10⁴, stage axis = median-rating stage (his rating-error term stays inside the overflow curve); scenario labels carry identical curves; committed contract CSVs + sine-30h and as-received-script-k companions under `data/processed/uemura_surface_curves/`. Two flagged findings: the script k-conversion (≈105.6× the dimensionally correct USACE factor) — **amended 2026-07-21 (ADR-0042 dec. 9): the primary now uses the dimensionally-correct USACE conversion, under which fluvial scour is negligible at every node; the as-received script factor is the labeled `scour_script_k` companion** — and the f_c log-law singularity at d = k_b/30 (regularized by a tested 0.05 m onset floor) |
| Uemura section table (D2, closed) | 9 sections (Tokachi KP62.4/61.4/59.6/58.0/56.4, Satsunai KP7.0/6.4/5.2/4.2 = thesis "Tokachi 1–5 / Satsunai 1–4" upstream→downstream) reconstructed as KP ranges from his own SECTIONS.shp with executable length/anchor validation; 66/114 segments sectioned (= his own notebook count); within-section rule = his Eq. 14 max (`composition.max_within_section`); `load_section_table(allow_gaps=True)` for the deliberately partial Satsunai coverage (ADR-0043) |

This is the complete, authoritative specification. Implement against this document; deviate from it only with a documented justification.
