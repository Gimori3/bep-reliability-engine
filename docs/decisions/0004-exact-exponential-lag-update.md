# ADR-0004: Exact Exponential Update for the M4 Aquifer-Lag State

Date: 2026-06-11
Status: Accepted

## Context
The optional M4 aquifer lag advances h_aq through the linear-reservoir ODE dh_aq/dt = (1/τ_aq)·[z_toe + r_e·(h(t) − z_toe) − h_aq(t)], with τ_aq = λ_in²·S_s/k_aq ≡ S_s·D_aq·D_bl/k_bl. Note that k_aq cancels: τ_aq depends on three of the seven sampled variables (D_aq, D_bl, k_bl) times the deterministic S_s. This is physically sensible — higher k_aq speeds up diffusion but also lengthens λ_in, and the two effects cancel at the leakage-length scale.

The specification's §6 sketch advanced this state with one explicit forward-Euler line, `h_aq += (Δt/τ_aq)·(h_inst − h_aq)`. Explicit Euler on this equation overshoots for Δt > τ_aq and diverges for Δt > 2·τ_aq. Because τ_aq is per-realization, individual realizations with low D_aq·D_bl/k_bl can have τ_aq below the native d4PDF timestep even when the run-level lag activation is justified, making those rows unstable mid-run. The §11 requirement that the lag reproduce the instantaneous translation as τ_aq → 0 is also unattainable under explicit Euler: at fixed Δt the update factor diverges instead of converging.

## Decision
Advance the lag state with the exact solution of the linear-reservoir ODE under piecewise-constant forcing:

```
h_aq ← h_aq + (1 − exp(−Δt/τ_aq)) · (h_aq,inst − h_aq),   h_aq,inst = z_toe + r_e·(h(t) − z_toe)
```

Companion decisions on the lag mechanism:

*   **Initialization:** h_aq(0) = z_toe + r_e·(h(0) − z_toe), i.e., equilibrium with the initial river stage. The aquifer has been at base stage long before the event; the steady-state response to constant forcing is exactly the instantaneous translation. Initializing at z_toe would inject a spurious filling transient at t = 0 that delays the loading for the entire event and has no physical basis.
*   **S_s** is a deterministic literature value in config, not an eighth random variable. Promoting it would expand the parameter space Phase 2 filters over and contaminate the clean 7D design for a gated second-order correction. If the lag activates and proves consequential, S_s uncertainty is handled as a bounded low/high sensitivity run.
*   **The lag flag is global per run**, decided by the §11 τ_aq/T_flood diagnostic evaluated at representative parameter values. A per-realization flag would make the modeled mechanism itself realization-dependent, muddying the static–transient comparison and the Phase 2 filter interpretation.
*   **τ_aq is a per-realization vector** once the lag is active (deterministic S_s times stochastic D_aq·D_bl/k_bl).

Scope: this ADR concerns only the M4 lag state. The M7 pipe-progression ODE remains forward Euler, matching Pol (spec §13); that decision is untouched.

## Consequences
*   Unconditionally stable: the update factor lies in (0, 1) for all Δt, τ_aq > 0. Reduces to the Euler form when Δt ≪ τ_aq, and is exact — not approximate — for the assumed piecewise-constant forcing.
*   The §11 lag-collapse test passes exactly rather than only in a limit: as τ_aq → 0 the factor → 1 and h_aq ≡ h_aq,inst.
*   Required tests: (1) stability — a realization with τ_aq = 0.1·Δt must remain bounded and track the instantaneous head; (2) collapse — τ_aq → 0 reproduces the instantaneous translation; (3) equilibrium-initialization guard — under a constant hydrograph h(t) = h₀, the lagged output must equal the instantaneous output exactly at every timestep, not just asymptotically.
*   One-line deviation from the literal §6 sketch of the specification; §6 has been updated to the exponential form with reference to this ADR.
