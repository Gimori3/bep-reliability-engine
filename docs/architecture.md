# Phase 1 Computational Architecture: Time-Dependent BEP Reliability Engine

## Authoritative Specification for Implementation

---

## 0. Framing and Architectural Principles

This document is the complete specification for the Phase 1 computational engine. It supersedes prior drafts and incorporates all decisions reached through prior discussion: the seven-dimensional stochastic parameter vector with C_e as a random variable, LHS as the sampling strategy throughout, the shared-sample contract between static and transient limit states, the mandatory Nataf correlation coupling k_aq and d_70, the separation of the erosion-driving head from the uplift and heave head, the lag-capable hydraulic-translation interface gated by the aquifer-response diagnostic, and the explicit handoff design for Phase 2 Bayesian filtering.

Four structural properties shape every downstream choice and warrant being stated upfront.

**Property 1, asymmetric limit state cost.** The static limit state is scalar-in, scalar-out per realization: sample θ, compute H_c via Sellmeijer, compare against the r_e-translated peak. The transient limit state is scalar-in, trajectory-out: sample θ, integrate the Pol ODE across the full multi-peak h(t), compare final l_e to L. The transient branch is roughly T times more expensive than the static, where T is the number of timesteps per hydrograph (about 500 to 5000). All optimization effort must focus on the transient timestepper; the static branch is essentially free.

**Property 2, shared-sample contract.** Both limit states must consume the same θ_j and the same r_e within each realization. Independent draws would conflate physical bias with sampling noise and destroy the scientific deliverable of Phase 1, namely static-versus-transient bias quantification. This is non-negotiable and constrains the engine architecture more than any other single requirement.

**Property 3, r_e is stochastic.** Because the Mazure leakage length λ_in depends on k_aq, D_aq, D_bl, and k_bl, which are four of the seven random variables, r_e cannot be precomputed once and reused. It lives inside the per-realization loop. This is a frequent source of confusion in Pol-style implementations.

**Property 4, irreducibly serial inner loop.** The compound event memory model creates a hard sequential dependency along the time axis: l(t+Δt) depends on l(t) via the positive-part operator and the running uplift latch. You can vectorize across realizations and across conditioning water levels, but inside a single realization the timestepper is serial. This determines exactly where numpy broadcasting works and where it fails. If the aquifer-lag option (M4) is activated, the aquifer head h_aq becomes a second serial state alongside l, advanced by one extra line at the top of each timestep; the serial structure is otherwise unchanged.

---

## 1. Module Decomposition and Single Responsibilities

The architecture decomposes into nine logical modules. Each has one clear responsibility. Whether each becomes a .py file or class is addressed in §9.

**M1, `config`** holds all deterministic inputs for a single run: cross-section geometry (L, foreshore width, HWL, z_toe), the conditioning grid {h_1, ..., h_Nh}, Monte Carlo settings (N = 10^5, RNG seed, LHS scheme), timestepper settings (Δt, integration scheme, aquifer-lag flag and τ_aq if active), and the prior distribution specifications for the seven random variables (family, mean, COV) together with the correlation structure imposed at sampling. This is a pure data object with no logic. Its purpose is reproducibility: one config object fully determines one fragility curve pair. Validate at load time using pydantic or equivalent to catch unit errors (for example COV = 50 versus 0.50) before a multi-hour run begins.

**M2, `prior_sampler`** generates the N by 7 matrix of θ samples via Latin Hypercube Sampling. Single responsibility: converting marginal distribution specifications into a stratified sample matrix in physical units, with the mandatory k_aq–d70 Nataf correlation (and any further empirically identified correlations) imposed on the LHS draws. Returns a structured array or DataFrame keyed by parameter name so that downstream modules never index into raw column numbers. Does not know anything about limit states.

**M3, `hydrograph_loader`** ingests the d4PDF hydrograph ensemble and exposes it as a clean object: for each event, a (t, h(t)) array plus metadata (event ID, duration, peak, scenario tag, historical or +4K). Also exposes the conditioning grid extraction logic: for the static comparison you need a representative scalar h_peak per event, but for the transient you need the full h(t). This module isolates all input/output and units handling, and records the native temporal resolution so the timestep and the rising-limb resolution can be checked against the flashy peaks that define the loading regime.

**M4, `hydraulic_translator`** computes, given a θ sample and cross-section geometry, the response factor r_e and returns h_aquifer(t). Single responsibility: river stage to landside aquifer piezometric head. This is where λ_in = √(k_aq · D_aq · D_bl / k_bl) and the full Mazure r_e formula live. The module exposes h_aquifer(t) through a unified interface that can produce it in either of two forms: the algebraic instantaneous translation h_aq(t) = z_toe + r_e · (h_river(t) − z_toe), which is the default, or a first-order linear-reservoir lag state dh_aq/dt = (1/τ_aq)·[z_toe + r_e·(h(t) − z_toe) − h_aq(t)]. The choice between the two is made by the aquifer-response diagnostic described in §11, which compares τ_aq ~ λ_in² · S_s / k_aq against the flood duration; the downstream limit state and progression modules consume h_aquifer(t) identically in both cases and require no restructuring. The module docstring must state which form is active and why, and must not assume the instantaneous form is permanent.

**M5, `initiation_evaluator`** evaluates Z_uplift(t) and Z_heave(t) at each timestep given Δh_blanket(t) from M4 and the sampled (D_bl, γ'_s). Both checks use the un-reduced aquifer overpressure Δh_blanket(t), not the erosion-driving head, because uplift and heave respond to the full pore pressure on the blanket base. The module exposes (a) the boolean indicator I_er(t) per Pol's formulation, true once the running minimum of Z_uplift has gone negative AND heave is currently active, OR if l_ini > 0 AND heave is currently active, and (b) the time t_uh of first co-occurrence. Single responsibility: STPH gating logic. Note that Pol's third I_er clause, which suspends progression once organised flood fighting is deployed, is deliberately omitted; this yields an unconditional upper bound on transient failure whose conservatism grows under the elongated +4K hydrographs.

**M6, `sellmeijer_static`** implements the full revised Sellmeijer 2011 critical head: H_c = L · F_r · F_s · F_g, with the three factors computed per equation (12) of the 2011 paper. Inputs: θ vector plus geometry. Output: scalar H_c. Used in two places, once for the static limit state evaluation and once inside the transient progression model because H_c parameterizes the equilibrium curve H_eq(l). Centralizing it in one place prevents drift between the two uses. Also computes l_c via the Pol SIE 2024 formula l_c/L = 0.5 · tanh(2 · D_aq/L). The module retains an optional scale-exponent argument so that the 3D hole-exit value α = −1/2 can be substituted for the 2D value in a sensitivity decomposition of the static-transient gap (§12, Failure mode 4).

**M7, `pol_ode_progression`** is the time-dependent ODE integrator. Given θ (including C_e), the aquifer head time series h_aquifer(t), the initiation indicator series I_er(t), and the H_c and l_c from M6, it integrates dl/dt = 89 · C_e · (k_aq · (H_erosion(t) − H_eq(l))/L)^0.81 forward in time using forward Euler. The erosion-driving head is H_erosion(t) = Δh_blanket(t) − 0.3·D_bl, the crack-resistance-reduced head of Pol SIE 2024 Eq. (6); this is distinct from the un-reduced Δh_blanket(t) that drives uplift and heave in M5. The equilibrium curve H_eq(l) is constructed by piecewise linear interpolation between (0, 0), (l_c, H_c), and (L, 0.9·H_c). The positive-part operator is enforced inside the timestepper. Output: full l(t) trajectory and final l_e.

**M8, `limit_state_evaluator`** orchestrates both limit states for a single realization. Receives one θ sample, the hydrograph, the geometry, and an optional l_ini, and returns the pair (Z_static, Z_transient). This is the module that enforces the shared-sample contract: the same θ is fed into both branches. Also returns auxiliary diagnostics, namely H_c, l_c, λ_in, peak r_e, and time-to-breach if failure occurred, because Phase 2 Bayesian filtering needs trajectory information, not just binary pass or fail, and because the survival-discrimination decomposition (§8) needs both the static and transient rejection under h_2016. This module must be importable cleanly by Phase 2.

**M9, `fragility_assembler`** takes the raw N by N_h indicator matrices (one for static, one for transient) and fits lognormal fragility curves separately for each. Computes confidence bands via bootstrap on the realizations. Output: a FragilityResult object containing both fitted curves, raw point estimates, and, critically, the full θ matrix and failure matrix retained for Phase 2.

---

## 2. Data-Flow and Interface Contracts

`config` (M1) flows into every other module as a read-only object. No module mutates it.

`prior_sampler` (M2) consumes `config.prior_specs` and `config.correlation_specs` and emits:

```
theta_matrix: ndarray shape (N, 7)
param_names:  ['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_s_sub', 'C_e']
```

Contract: rows are LHS draws with the mandatory k_aq–d70 Nataf correlation imposed (see §7), and any further empirically identified correlations applied through the same transform; columns are physical-units parameter values; and the RNG seed in config fully determines the matrix. All downstream modules access columns by name via `theta_matrix[:, param_names.index('k_aq')]` or, preferably, via a thin wrapper that exposes named access.

`hydrograph_loader` (M3) emits:

```
hydrographs: dict[event_id -> HydrographRecord]
HydrographRecord:
  t:               ndarray (T,)         # seconds or hours, units in metadata
  h:               ndarray (T,)         # river stage [m above datum]
  peak:            float
  duration_hours:  float
  scenario:        str                  # 'historical' or '+4K'
  event_id:        str
  native_dt:       float                # native temporal resolution, for the rising-limb check
```

The core inner contract, and the one needing the most care, is the signature of `limit_state_evaluator` (M8):

```
Input:
  theta_row:    ndarray (7,)            # one realization's parameter vector
  hydrograph:   HydrographRecord
  geometry:     dict                    # L, z_toe, foreshore_width, lambda_out_params
  l_ini:        float                   # initial pipe length (default 0)
  store_trajectory: bool                # default False to save memory

Output: EvaluationResult dataclass
  Z_static:        float
  Z_transient:     float
  l_e_final:       float
  l_trajectory:    ndarray (T,) or None
  H_c:             float
  l_c:             float
  lambda_in:       float
  r_e:             float
  t_uh:            float or NaN          # time of first uplift+heave co-occurrence
  failure_static:  bool
  failure_trans:   bool
  uplift_occurred: bool                  # latched within event
  heave_occurred:  bool                  # latched within event
```

The optional `l_trajectory` storage matters for memory: 10^5 realizations times about 1000 timesteps times 8 bytes is about 800 MB per cross-section. For Phase 2 you only need the final l_e under the 2016 hydrograph specifically, so default to off and toggle on for diagnostic runs and for the 2016 calibration sweep.

`fragility_assembler` (M9) consumes the full N by N_h matrices of `failure_static` and `failure_trans` booleans and emits the FragilityResult, the handoff artifact to Phase 2:

```
FragilityResult:
  conditioning_grid:    ndarray (N_h,)
  P_f_static_raw:       ndarray (N_h,)        # MC point estimates
  P_f_trans_raw:        ndarray (N_h,)
  P_f_static_fit:       LognormFragility       # fitted (mu, sigma)
  P_f_trans_fit:        LognormFragility
  bootstrap_bands:      dict[curve -> (lo, hi)]
  theta_matrix:         ndarray (N, 7)         # RETAINED for Phase 2
  param_names:          list[str]
  failure_matrix_stat:  ndarray (N, N_h) bool  # RETAINED for diagnostics and decomposition
  failure_matrix_tran:  ndarray (N, N_h) bool  # RETAINED for Phase 2
  metadata:             dict                    # config snapshot, runtime, version,
                                                # c_e_stochastic flag, d70_interpretation,
                                                # remediation_state, segment_id
```

Retaining `theta_matrix` and `failure_matrix_tran` is non-negotiable. Phase 2's Accept-Reject filtering re-runs M8 on the surviving θ rows against h_2016(t); it needs the raw prior matrix, not just the fitted curve. Retaining `failure_matrix_stat` is what makes the survival-discrimination decomposition of §8 possible. Persist via HDF5 (h5py) for the large arrays and a JSON sidecar for metadata. One HDF5 file per cross-section per scenario.

---

## 3. Logical Execution Sequence

Three nested levels, with order chosen for both correctness and performance:

**Outermost loop, conditioning water levels h_i.** Fully parallelizable across cores. Each h_i is independent; for each, the static evaluation uses h_i as h_peak, while the transient evaluation uses either an actual d4PDF hydrograph anchored at peak h_i (for ensemble-driven fragility) or a synthetic scaled hydrograph (for fragility curve construction).

**Middle loop, realizations j in {1, ..., N}.** All N realizations at a given h_i share the same hydrograph but use independent θ_j rows. This is the loop where numpy broadcasting yields the largest gains.

**Innermost loop, timesteps t_k.** Irreducibly serial within a realization. Vectorized across realizations within a single timestep (see §6).

The per-realization, per-conditioning-level pseudocode:

```
SHARED PREAMBLE (computed once per θ_j):
  1. Read θ_j from theta_matrix
  2. Compute H_c(θ_j) and l_c(θ_j) via M6
  3. Compute λ_in(θ_j) and r_e(θ_j) via M4

STATIC BRANCH:
  4. H_load_peak = r_e · (h_i − z_toe)          [gross peak head; no 0.3·D_bl reduction]
  5. Z_static = H_c − H_load_peak
  6. failure_static = (Z_static <= 0)

TRANSIENT BRANCH (full timestep loop):
  7. Initialize l_current = l_ini, uplift_ever = False
  8. For each timestep t_k:
       a. h_aq(t_k)        = z_toe + r_e · (h(t_k) − z_toe)
                              [instantaneous default; if the τ_aq/T_flood diagnostic
                               activates the lag, h_aq is advanced as a linear-reservoir
                               state instead, see M4]
       b. Δh_blanket(t_k)  = h_aq(t_k) − z_toe        [= r_e · (h(t_k) − z_toe)]
       c. H_erosion(t_k)   = Δh_blanket(t_k) − 0.3 · D_bl     [erosion driver only]
       d. Z_uplift(t_k)    = (γ'_s · D_bl)/γ_w − Δh_blanket(t_k)   [uses Δh_blanket]
       e. uplift_ever     |= (Z_uplift(t_k) < 0)
       f. i_exit(t_k)      = Δh_blanket(t_k) / D_bl
       g. Z_heave(t_k)     = γ'_s/γ_w − i_exit(t_k)              [uses Δh_blanket]
       h. heave_now        = (Z_heave(t_k) < 0)
       i. I_er(t_k)        = (uplift_ever OR l_current > 0) AND heave_now
       j. If I_er(t_k):
            H_eq = piecewise_linear(l_current, anchors=[(0,0), (l_c, H_c), (L, 0.9·H_c)])
            overload = max(0, H_erosion(t_k) − H_eq)      [H_erosion, not Δh_blanket]
            dldt = 89 · C_e · (k_aq · overload / L)^0.81
            l_current = l_current + dldt · Δt             [positive part enforced by max(0, overload)]
          Else:
            l_current unchanged                            [positive-part operator]
  9. Z_transient = L − l_current
  10. failure_trans = (Z_transient <= 0)
```

Three subtle points worth highlighting. First, in step 4 the static comparator uses r_e · (h_peak − z_toe), the translated aquifer head, not the raw river peak. Both limit states share the hydraulic translation; this is a direct consequence of the shared-sample contract. Second, the transient branch drives the progression rate with H_erosion = Δh_blanket − 0.3·D_bl (step c, used in step j), while the uplift and heave checks (steps d and g) use the un-reduced Δh_blanket; the static comparator (step 4) uses the gross peak head. The difference in head convention between the static and transient branches is intentional and is accounted for in the bias decomposition (§12, Failure mode 4), not silently absorbed. Third, in step 8i the clause `(uplift_ever OR l_current > 0)` is what enables compound-event progression to resume on subsequent peaks without re-triggering uplift, the gateway condition for the memory model.

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

A consequence worth flagging: the static branch has no exposure to C_e at all. C_e is a transient-branch parameter only. The static limit state depends only on the six geotechnical variables (k_aq, d_70, D_aq, D_bl, k_bl, γ'_s) plus the deterministic θ_repose and D_r. Phase 2 filtering will therefore tighten C_e only through the transient branch, which is exactly the desired behavior: Phase 2 is calibrating laminar-flow conservatism, which lives only in the ODE. A second consequence, introduced by the head separation, is that the static and transient branches do not use an identical driving head: the static uses the gross peak head, the transient applies the 0.3·D_bl crack-resistance reduction. This is a deliberate fidelity choice (the static branch represents conventional deterministic practice, which does not apply Pol's crack term) and is one of the three components of the static-transient gap discussed in §12.

---

## 5. Compound Event Memory Model: State Variable Management

This is the most error-prone part of the implementation. The memory model demands that pipe length l carry across peaks within a single d4PDF event record, with the positive-part operator preventing healing.

The state variable is **`l_current: float`**, initialized to `l_ini` at the start of each event. For prior fragility curve construction in Phase 1, l_ini = 0. For Phase 2 (where the 2016 hydrograph is replayed for filtering) l_ini also starts at 0 because the 2016 event is the calibration event itself. The hook for non-zero l_ini exists to support sensitivity studies and the architectural flexibility to feed event sequences. If the aquifer-lag option is active, a second state h_aq_current carries across timesteps as well, but it does not carry across events (only the pipe length does).

Inside the timestepper, l_current is updated as:

```
if I_er(t):
    H_erosion = delta_h_blanket(t) - 0.3 * D_bl
    overload  = max(0, H_erosion - H_eq(l_current))
    dldt      = 89 * C_e * (k_aq * overload / L)**0.81
    l_current += dldt * dt
else:
    l_current unchanged
```

The `max(0, overload)` enforces the positive-part operator at the level of the driving force; combined with `dldt >= 0` and the absence of any negative-progression term, this guarantees l_current is monotonically non-decreasing. There is no separate "reset between peaks" step; that is the whole point of the memory model. The hydrograph is fed in as one continuous time series spanning the entire compound event, and l_current evolves monotonically across the whole record.

**Traps to watch for:**

When h(t) drops below the uplift threshold during inter-peak troughs, I_er goes false, dl/dt = 0, and l_current stays flat. Trajectory plots will show staircase-shaped growth, with flat segments during troughs and growth segments during peaks. This is correct. Do not "fix" it.

The "min{Z_u(τ): τ <= t} < 0" clause in I_er is a running minimum. Implement it as a single scalar `uplift_ever_occurred: bool` that latches to True the first time Z_u goes negative and stays True for the rest of the event. This avoids confusion with the instantaneous Z_h check and is correct because uplift represents a one-way structural failure of the blanket.

The `l_ini > 0` clause in I_er means a pre-existing pipe makes the uplift gate effectively bypassed for that event. This is correct physics, since an existing pipe means the blanket is already breached, but be aware it changes the gating logic between events with and without prior pipes.

Do not subtract the 0.3·D_bl crack resistance from the uplift or heave heads. That reduction belongs only to the erosion driver H_erosion; the uplift and heave checks act on the full Δh_blanket. Mixing them is a common error that would make initiation appear harder than it is.

For r_l (long-term strength recovery between events): in Phase 1 set r_l = 0 always, per thesis scope. The hook should exist in the API (`l_ini_next_event = (1 − r_l) · l_e_prev`) but it lives outside the timestepper, between event evaluations.

---

## 6. Vectorization and Parallelization Strategy

Vectorization opportunities decompose along the three loop levels.

**Across realizations (middle loop), partially vectorizable.** The shared preamble, namely sampling θ and computing H_c, λ_in, and r_e, is fully numpy-vectorizable. Compute these as N-length arrays in one shot:

```python
H_c_vec     = sellmeijer_vectorized(theta_matrix)        # shape (N,)
l_c_vec     = 0.5 * L * np.tanh(2 * theta_matrix[:, idx_D_aq] / L)
lambda_in   = np.sqrt(k_aq_vec * D_aq_vec * D_bl_vec / k_bl_vec)
r_e_vec     = lambda_in / (lambda_out + L + lambda_in)
```

The static limit state is fully vectorizable: a single boolean comparison across N realizations. The static branch is essentially O(N) with a tiny constant and runs in seconds for N = 10^5.

**Across timesteps (inner loop), not vectorizable in time.** Path dependency. But within a single timestep you can vectorize across all N realizations simultaneously:

```python
# At time t_k, advance all N realizations one step
h_t                = h_river[k]                                            # scalar
delta_h_vec        = r_e_vec * (h_t - z_toe)                              # shape (N,)
H_erosion_vec      = delta_h_vec - 0.3 * D_bl_vec                         # erosion driver only
Z_u_vec            = (gamma_s_sub_vec * D_bl_vec) / gamma_w - delta_h_vec
uplift_ever_vec   |= (Z_u_vec < 0)
i_exit_vec         = delta_h_vec / D_bl_vec
Z_h_vec            = gamma_s_sub_vec / gamma_w - i_exit_vec
heave_now_vec      = (Z_h_vec < 0)
I_er_vec           = (uplift_ever_vec | (l_current_vec > 0)) & heave_now_vec

# Piecewise linear H_eq with per-realization breakpoints
H_eq_vec = np.where(
    l_current_vec < l_c_vec,
    H_c_vec * l_current_vec / l_c_vec,
    H_c_vec + (0.9 * H_c_vec - H_c_vec) * (l_current_vec - l_c_vec) / (L - l_c_vec)
)
overload_vec       = np.maximum(0.0, H_erosion_vec - H_eq_vec)   # H_erosion, not delta_h
dldt_vec           = 89.0 * C_e_vec * (k_aq_vec * overload_vec / L)**0.81
dldt_vec           = np.where(I_er_vec, dldt_vec, 0.0)
l_current_vec     += dldt_vec * dt
```

If the aquifer-lag option is active, insert one line before `delta_h_vec` that advances the lag state, `h_aq_vec += (dt / tau_aq_vec) * (z_toe + r_e_vec * (h_t - z_toe) - h_aq_vec)`, and then set `delta_h_vec = h_aq_vec - z_toe`. The rest of the loop is unchanged, which is the point of the unified M4 interface.

Total operation count: N times T elementwise ops, all in numpy. For N = 10^5 and T about 1000, that is about 10^8 fused operations, well within numpy's reach in minutes.

**Across conditioning water levels (outer loop), embarrassingly parallel.** Each h_i is independent; parallelize with joblib.Parallel across CPU cores. For N_h about 30 and 8 to 16 cores, near-linear speedup.

**Where broadcasting breaks down:**

Variable-length hydrographs across d4PDF events. Different events have different durations; you cannot stack into a uniform (N_events, T) array without padding. Process events one at a time, since they are independent across the conditioning loop.

The piecewise linear H_eq interpolation: breakpoints (l_c, H_c) differ per realization, so scipy.interpolate.interp1d will not broadcast cleanly. Implement manually with np.where as shown above. This is fine; the two-segment piecewise linear is trivial to express.

The first-uplift-time bookkeeping requires sequential updates along time but vectorizes across realizations (`uplift_ever_vec |= Z_u_vec < 0`).

**Numba note:** if profiling shows the per-timestep elementwise loop is a bottleneck (it should not be with pure numpy, but might be if you add complexity), `@numba.njit(parallel=True)` on the timestepper gives another factor of 3 to 5 without code changes. Do not pre-optimize; write numpy first, profile, and only reach for Numba if wall-clock demands it.

**Budget estimate:** about 5 min per h_i times 30 h_i is about 2.5 hr single-threaded; about 15 to 30 min with 8-core parallelism. Comfortable for iterative thesis development.

---

## 7. The Seven-Dimensional Stochastic Parameter Vector

Random variables sampled via LHS:

| Symbol | Description | Distribution | Mean | COV | Source |
|---|---|---|---|---|---|
| k_aq | Aquifer hydraulic conductivity [m/s] | Lognormal | (site-specific) | 0.50 | OYO 1999 field tests |
| d_70 | Representative grain size [m] | Lognormal | (site-specific) | 0.10 | OYO 1999 grain-size curves |
| D_aq | Aquifer thickness [m] | Lognormal | (site-specific) | 0.20 | OYO 1999 borehole logs |
| D_bl | Blanket thickness [m] | Lognormal | (site-specific) | 0.20 | OYO 1999 borehole logs |
| k_bl | Blanket vertical conductivity [m/s] | Lognormal | (site-specific) | 0.50 | OYO 1999 (or proxy) |
| γ'_s | Submerged unit weight [kN/m^3] | Normal | (site-specific) | 0.05 | OYO 1999 lab tests |
| C_e | Erosion coefficient [-] | Lognormal | 0.014 | 0.50 | Pol 2024 calibration |

Fixed within every realization:

- θ_repose = 37 degrees (angle of repose, enters Sellmeijer F_r)
- D_r = 0.725 (Pol base case)
- C_u, KAS evaluated at experimental mean values per Sellmeijer 2011 convention

The C_e promotion is the substantive update from a six-dimensional formulation. The justification, in brief: Pol's ODE is calibrated against laminar-regime experiments (Re < 2100); prototype-scale pipe flow frequently transitions to turbulent regime (Okamura 2022, 2025), introducing friction that reduces progression rates. Rather than modify the ODE with empirically unvalidated turbulence corrections, the laminar-flow conservative bias is encoded as prior uncertainty on C_e, and Phase 2 Bayesian filtering against 2016 survival empirically constrains it. The COV of 0.50 spans the small-scale calibration range of 0.007 to 0.030 reported by Pol 2024.

**Correlation structure (mandatory, not optional).** Sampling proceeds via LHS on all seven marginals, with one mandatory correlation imposed. The aquifer conductivity k_aq and the grain size d_70 are not sampled independently. The baseline parameterization takes d_70 from the sand matrix (to stay near the validated Sellmeijer grain-size range) while k_aq is anchored to the bulk gravel framework, so independent draws would pair a fine-matrix grain size with a coarse-framework conductivity inside a single realization, describing a soil that does not physically exist and inflating the prior progression rate. The two are therefore coupled through a Nataf transformation using the empirical correlation ρ(ln k_aq, ln d_70) estimated from the paired OYO 1999 grain-size and permeability records. If those records show the matrix grain size and bulk conductivity to be statistically decoupled, a two-population soil model, in which the erodible matrix is treated separately from the armouring gravel framework, replaces the single correlated population. Both the matrix and the bulk d_70 interpretations are carried as primary runs, not as a single nominal choice, so the dependence of the fragility curves on the grain-size definition is reported explicitly and recorded in `metadata.d70_interpretation`. Any further significant correlations found in the OYO 1999 dataset are imposed through the same Nataf procedure. Implementation: generate the stratified uniform LHS design on the unit hypercube, then apply the Nataf transform to introduce the correlation while preserving the marginals, then map to physical units.

**A note on the C_e times k_aq product:** both enter multiplicatively in dl/dt and both are Lognormal with COV about 0.50, so their product has COV about 0.71. The high-C_e, high-k_aq corner of the prior produces progression rates several times the deterministic baseline. This is physically defensible (these are realizations that should fail) but means the prior transient fragility curve will sit above what deterministic-C_e analysis would predict. The Phase 2 posterior will pull this tail back in, producing a larger prior-to-posterior shift than a deterministic-C_e analysis would show. Be prepared to explain this in the discussion: the apparent strength of Bayesian calibration partly reflects giving the filter more parameter freedom to act on, not solely the informativeness of the 2016 survival observation. Note also that this product is an interaction, which bears directly on the sampling-variance discussion in §12, Failure mode 5.

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
from bep_phase1.evaluator import evaluate_realization

results_2016 = [
    evaluate_realization(theta_matrix[j], h_2016, geometry, l_ini=0.0)
    for j in range(N)
]
surviving_mask_trans  = np.array([r.Z_transient > 0 for r in results_2016])
surviving_mask_static = np.array([r.Z_static    > 0 for r in results_2016])
theta_posterior = theta_matrix[surviving_mask_trans]
```

**Survival-discrimination decomposition.** Because M8 returns both Z_static and Z_transient under h_2016, the filtering step yields two rejection sets, not one. Realizations rejected by the static criterion would have failed even at peak head, so their rejection reflects geometry, material resistance, or sub-critical loading, not any time constraint. The marginal informativeness of the 2016 survival for the time-dependent mechanism is therefore the additional rejection produced by the transient criterion beyond the static one, evaluated within the remediation state assigned to each segment. Record both rejection fractions side by side. This is the artifact that answers the survival-discrimination question (whether 2016 survival genuinely constrains progression or is already explained by simpler physics), and the `metadata.remediation_state` and `metadata.d70_interpretation` fields exist so the decomposition can be stratified across remediation states and grain-size interpretations.

For this to work, M8 must be importable without notebook context, which directly motivates the architecture recommendation in §9.

**Persistence format:** HDF5 via h5py for the large arrays; JSON sidecar for config metadata. Avoid pickle for long-term storage (Python version brittleness); avoid CSV for matrices (slow, lossy for floats). One HDF5 file per cross-section per scenario is a reasonable granularity. Recommended schema:

```
/theta_matrix             (N, 7)  float64
/param_names              (7,)    string
/conditioning_grid        (N_h,)  float64
/failure_matrix_static    (N, N_h) bool
/failure_matrix_trans     (N, N_h) bool
/P_f_static_raw           (N_h,)  float64
/P_f_trans_raw            (N_h,)  float64
/attrs:
    config_hash, runtime_seconds, c_e_stochastic=True,
    prior_means, prior_covs, correlation_rho_k_d70, d70_interpretation,
    remediation_state, lhs_seed, cross_section_id, segment_id,
    scenario, code_version, hydrograph_source, aquifer_lag_active, tau_aq
```

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

```
bep_phase1/
├── bep_phase1/                       # importable package
│   ├── __init__.py
│   ├── config.py                     # M1: pydantic dataclasses
│   ├── sampling.py                   # M2: LHS sampler + Nataf correlation
│   ├── hydrographs.py                # M3: d4PDF loader
│   ├── hydraulics.py                 # M4: r_e, λ_in, optional lag state
│   ├── initiation.py                 # M5: uplift, heave, I_er logic
│   ├── sellmeijer.py                 # M6: H_c, l_c, optional 3D scale exponent
│   ├── progression.py                # M7: Pol ODE timestepper, H_erosion
│   ├── evaluator.py                  # M8: combined limit state evaluator
│   ├── fragility.py                  # M9: curve fitting, FragilityResult
│   └── io.py                         # HDF5 persistence
├── tests/
│   ├── test_sellmeijer.py            # vs Pol/Sellmeijer published cases
│   ├── test_progression.py           # vs Pol 2024 small-scale calibration
│   ├── test_hydraulics.py            # vs Mazure analytical solutions
│   └── test_evaluator.py             # integration test, deterministic case
├── notebooks/
│   ├── 01_prior_distributions.ipynb  # visualize 7D priors and k_aq-d70 correlation
│   ├── 02_single_realization.ipynb   # trace one θ end-to-end
│   ├── 03_fragility_run.ipynb         # driver: full N=10^5
│   ├── 04_static_vs_transient.ipynb   # analysis: bias quantification
│   └── 05_compound_event_study.ipynb  # 2016 typhoon trace, sanity
├── data/                             # geotech inputs, hydrographs
├── results/                          # FragilityResult HDF5 files
├── configs/                          # YAML config files per cross-section
├── requirements.txt
└── README.md
```

Notebooks become thin drivers: they import from `bep_phase1`, configure a run, execute, and visualize. They do not contain physics. The notebook for a fragility run is essentially:

```python
from bep_phase1 import Config, run_fragility_analysis, plot_fragility
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
- **numba**, held in reserve. Only if profiling demands it.

**Avoid:** TensorFlow, PyTorch, JAX (overkill, no autodiff benefit here). Also avoid scipy.integrate.solve_ivp for the timestepper, since forward Euler is what Pol uses and adaptive integrators fight the I_er discontinuities.

---

## 11. Convergence and Validation Strategy

**Convergence diagnostic.** Monitor the coefficient of variation of P_f-hat at the lowest failure probability of interest as N increases. Standard practice (Schweckendiek 2014) targets CoV < 5% across the relevant failure range; sample sizes of order 10^5 typically achieve this, and this sufficiency is verified directly for each cross-section once the engine runs rather than assumed. For levels where P_f-hat < 10^-4, monitor CoV explicitly and increase N if needed. Bootstrap resampling of the realization set provides confidence bands on fitted fragility curves.

**Aquifer-response diagnostic (gates the M4 lag option).** For each governing cross-section, estimate τ_aq ~ λ_in² · S_s / k_aq using a literature specific-storage range for the dense sand-gravel, and compare it against the characteristic flood duration for the 2016 event and representative d4PDF members. Separately, confirm from M3 that the native d4PDF temporal resolution resolves the flashy peaks (on the order of a 1.5 hour plateau). If τ_aq/T_flood is non-negligible at any governing section, or the resolution is insufficient, activate the linear-reservoir lag form in M4; otherwise the diagnostic itself justifies the instantaneous default. Record the outcome and τ_aq in metadata.

**Timestep convergence test.** Because forward-Euler overshoot is most severe on steep rising limbs, run this test on a genuinely flashy d4PDF rising-limb event, not a smooth design hydrograph, with the parameter combination drawn from the high-progression-rate tail that most stresses the scheme: high k_aq, high C_e, and low D_bl. Compare l_e at Δt and Δt/2 and confirm it differs by less than 1%. Pol uses Δt = 10 s for small-scale and 100 s for large-scale. For field-scale typhoons, 600 s (10 min) is likely safe but verify. Native d4PDF resolution is the starting default.

**Physics validation tests** (pytest):

1. **Sellmeijer reproduction.** Compute H_c for the IJkdijk test cases reported in Sellmeijer 2011 Table 1; require agreement within reported regression scatter.
2. **Pol small-scale reproduction.** Run progression.py against Pol 2024 B25-245 and FPH calibration cases; require l_e(t) agreement within experimental scatter using Pol's calibrated C_e. As part of this test, verify that the H_c anchoring H_eq and the erosion-driving head H_erosion = Δh_blanket − 0.3·D_bl share the head datum of Pol SIE 2024 Eqs (6) and (8), so the crack-resistance term is applied at the correct point in the balance.
3. **Mazure analytical check.** For an idealized cross-section (no foreshore, λ_in computable in closed form), require r_e agreement with hand calculation to machine precision. If the lag option is active, also confirm that as τ_aq goes to zero the lag state reproduces the instantaneous translation.
4. **Conservation and monotonicity.** Assert l_current is monotonically non-decreasing across every timestep in every realization. Assert l_e <= L at termination. Assert I_er never goes from true to false except via heave inactivation.
5. **Degenerate-case smoke tests.** A toe-drained segment with the exit head forced to z_toe must yield Z_u, Z_h >= 0 for all stages and P_f going to 0. Note that this zero-exit-head idealization represents as-designed drain performance and assumes continued drain functionality; it is optimistic rather than conservative with respect to clogging or degradation, and a degraded-drain sensitivity is a planned run, not part of the baseline. A cross-section with C_e going to 0 must yield Z_trans going to L − l_ini regardless of hydrograph.

---

## 12. Failure Modes and Architectural Tradeoffs

**Failure mode 1, silent unit inconsistency in r_e.** Mazure mixes hydraulic conductivity [m/s], geometric lengths [m], and dimensionless factors. A factor-of-86400 error from m/s versus m/day produces λ_in values that look plausible but are off by orders of magnitude. Mitigation: single-realization integration test against a published Mazure analytical case before trusting any fragility output. Use pydantic with units annotations in config.

**Failure mode 2, H_c non-physical for extreme θ tails.** Lognormal sampling with COV = 0.5 on k_aq produces a heavy right tail. Combined with small d_70 samples, F_s can produce H_c values near zero or unstable values via F_g. Mitigation: clip θ samples to physically defensible bounds (for example d_70 within [50 μm, 1 mm]) at the sampler stage. Add an assertion in `sellmeijer_static` that H_c > 0; log and skip realizations that fail, tracking the skip rate. A skip rate above 1% indicates priors need re-bounding.

**Failure mode 3, forward Euler timestep too large for steep rising limbs.** For typhoon peak rising limbs in flashy rivers, the effective time constant of the dl/dt response can be short. If Δt is too large, l_e can overshoot. Mitigation: the timestep convergence test in §11, run on a flashy rising limb with a high-progression-rate θ.

**Failure mode 4, static-vs-transient bias conflates three physical effects.** The intended finding "static overestimates because it ignores time" is partly conflated with two non-temporal effects. First, the static Sellmeijer assumes 2D plane-strain and inherits the 2D scale exponent α = −1/3, while the Pol ODE was calibrated against 3D experiments carrying α = −1/2; at field seepage lengths the 3D critical head can be roughly half the 2D value, a magnitude comparable to the temporal effect. Second, the transient branch applies Pol's crack-resistance reduction H_erosion = Δh_blanket − 0.3·D_bl, while the static comparator uses the gross peak head, faithful to conventional deterministic practice; this introduces a smaller non-temporal head-convention offset. The static-transient gap therefore combines a temporal component, a 2D-versus-3D dimensional component, and a head-convention offset. Mitigation: do not claim the entire gap is purely temporal; provide a hook in M6/M7 to substitute the 3D scale exponent α = −1/2 in the equilibrium curve for a sensitivity decomposition, report the head-convention difference explicitly, and acknowledge all three components in the discussion.

**Failure mode 5, LHS variance reduction in the tails.** LHS improves the coverage of each marginal axis, so it is expected to tighten the coefficient of variation of P_f-hat relative to crude Monte Carlo at the same N, which is advantageous for the sensitivity studies and cross-section sweeps that run at reduced N (typically 10^4). This expectation carries a caveat specific to this problem and partly in tension with Failure mode 7: the deepest part of the failure tail is governed not by a single marginal but by the multiplicative interaction C_e times k_aq, and LHS stratifies marginals, not interactions. The realized tail-variance advantage is therefore not assumed; it is verified empirically against crude Monte Carlo at the operating N, evaluated on the failure tail specifically rather than on the bulk. Mitigation: design the engine around LHS from the start and treat crude MC as a debug fallback; if the advantage proves weak in the deep tail, a variance-reduction scheme targeted at the joint tail (importance sampling or subset simulation) is considered for the lowest conditioning levels, so leave the sampler interface open to substitution.

**Failure mode 6, memory explosion from storing all l(t) trajectories.** 10^5 times 1000 times 8 bytes is about 800 MB per cross-section per scenario. Across 5 cross-sections by 2 scenarios by static/transient you can blow past 16 GB. Mitigation: default `store_trajectories=False`; retain only Z values and scalar diagnostics. Enable trajectory storage only for the 2016 calibration run and for a 100-realization visualization subset.

**Failure mode 7, C_e times k_aq multiplicative tail amplification.** Both Lognormal with COV about 0.50; the product has COV about 0.71. The high-C_e, high-k_aq corner produces progression rates several times the deterministic baseline, dominating the transient failure tail. This is physically correct but means the prior transient fragility sits above deterministic-C_e predictions and the Phase 2 posterior shift looks more dramatic than under deterministic C_e. It is also the interaction that undermines the naive LHS variance claim in Failure mode 5. Mitigation: explain in the discussion that the apparent strength of Bayesian calibration partly reflects giving the filter more parameter freedom, not solely the informativeness of 2016 survival. Plot prior and posterior marginals for all seven parameters, with C_e called out specifically, and report how much of the posterior shift is informativeness versus this tail artifact.

**Tradeoff 1, sequential timestepper, numpy versus JIT.** Pure numpy vectorized across realizations is clean and gets to about 30 min runs. Numba-JIT gets to about 5 min but introduces debugging headaches (poor error messages, type-inference regressions). Recommendation: numpy first, ship the thesis with numpy, leave Numba as optimization for any follow-up paper.

**Tradeoff 2, storing failure_matrix for Phase 2 versus recomputing.** Storing costs about 3 MB (N by N_h bools); recomputing costs about 30 min. Store it. The recompute path should still exist as a code path for reproducibility but should not be the default.

**Tradeoff 3, coupling to Uemura's discretization.** The thesis is committed to the 200 m segment grid and KP boundaries. Fragility output dimensions are fixed by external data, not computational convenience. Architect the FragilityResult to carry segment_id as a first-class index from day one; do not try to retrofit when integrating with Uemura's curves in Phase 3.

---

## 13. Summary of Single Decisions

For quick reference during implementation, the architectural decisions that should not be re-litigated mid-build:

| Decision | Setting |
|---|---|
| Stochastic parameter vector dimensionality | 7 (includes C_e) |
| C_e prior | Lognormal, mean 0.014, COV 0.50 |
| Sampling scheme | Latin Hypercube, 7-dimensional |
| k_aq–d70 correlation | Mandatory Nataf coupling from OYO 1999 pairs; two-population fallback if decoupled |
| d_70 interpretation | Matrix and bulk both run as primary; recorded in metadata |
| Sample size per cross-section | N = 10^5 |
| Conditioning grid size | N_h about 30 (refine as needed) |
| Shared sampling for static/transient | Mandatory, single θ_j feeds both |
| Hydraulic translation | Instantaneous Mazure r_e by default; linear-reservoir lag hook retained in M4, activated if the τ_aq/T_flood diagnostic requires |
| Erosion-driving head | H_erosion = Δh_blanket − 0.3·D_bl in the ODE only; uplift and heave use the un-reduced Δh_blanket |
| Static comparator hydraulic input | r_e · (h_peak − z_toe), gross peak head, not raw h_peak and not reduced by 0.3·D_bl |
| ODE integrator | Forward Euler |
| Timestep | Native d4PDF resolution, validated by Δt/2 test on a flashy rising limb |
| Convergence-test worst-case θ | High k_aq, high C_e, low D_bl |
| Recovery rate r_l (Phase 1) | 0 (zero recovery within events) |
| Trajectory storage | Off by default; on for 2016 calibration and viz subsets |
| Persistence format | HDF5 with JSON metadata sidecar |
| Code organization | .py package with thin notebook drivers |
| Phase 2 handoff payload | theta_matrix, failure_matrix_trans, failure_matrix_static, and metadata, all in FragilityResult |
| Phase 2 survival decomposition | Record static and transient rejection separately under h_2016; report marginal transient informativeness |
| Filter dimensionality in Phase 2 | 7 (C_e included; this is the whole point) |

This is the complete, authoritative specification. Implement against this document; deviate from it only with a documented justification.
