# ADR-0011: M8 Orchestration — Shared-Sample Enforcement, Gross-Head Static Comparator, and the Pinned Phase 2 Surface

Date: 2026-06-14
Status: Accepted

## Context
M8 `evaluate_realization` (`evaluator.py`) is the single function that evaluates both limit states for one realization and is the function Phase 2 imports to filter the prior θ matrix against the 2016 hydrograph (spec §8). Three properties of its behaviour are load-bearing enough to record explicitly: how the shared-sample contract and the head-convention separation are enforced; which head the static comparator uses; and how the import surface is protected. M4–M7 are implemented and their physics is tested in isolation (ADR-0002, ADR-0007, ADR-0008); what remained was to pin the *orchestration-level* guarantees that only M8 can provide.

---

## Decision

### 1. Shared-sample contract and head separation are enforced and tested at the orchestration level
M8 computes the shared preamble — `H_c`, `l_c` (M6) and `lambda_in`, `r_e` (M4) — exactly once per realization, then feeds the *same* `theta_row` and the *same* `r_e` into both branches; the static comparison reuses the *same* `H_c` that anchors the transient `H_eq` curve (no recomputation, no drift). The two driving heads are kept distinct: the static branch consumes the gross translated head, while the transient delegates to M7 `integrate_progression`, which internally drives the rate with `H_erosion = Δh_blanket − 0.3·D_bl` and the uplift/heave gate with the un-reduced `Δh_blanket`. These are verified by `tests/test_evaluator.py` (single-Euler-step reconstruction of both Z values from the same `r_e` and `H_c`; the two driving heads asserted to differ by exactly `0.3·D_bl`; an `l_ini > 0` case proving a single `H_c` anchors both branches). M8 does **not** re-own the timestep loop — the two-head separation correctly lives inside M7, and M8 delegating to `integrate_progression` is the committed module decomposition.

### 2. The static comparator uses the gross head (committed); matched-head is a documented variant
The static limit state uses `H_load_peak = r_e·(h_peak − z_toe)`, the gross translated peak head with **no** `0.3·D_bl` crack-resistance reduction, while the transient applies the reduction. This `0.3·D_bl` head-convention offset between the branches is intentional and is one of the components of the static–transient gap (spec §12, failure mode 4). The committed rationale: the static branch represents conventional deterministic practice, which does not apply Pol's crack term. The **matched-head alternative** — subtracting `0.3·D_bl` from the static comparator too, so both branches share an identical driving head — is recorded as a documented variant for a sensitivity decomposition that isolates the temporal effect from the head-convention offset; it is not the baseline.

### 3. The erosion coefficient enters only the transient branch
`C_e` appears solely in the M7 progression rate, so `Z_static` is independent of `C_e` (ADR-0001). Phase 2 therefore tightens `C_e` through the transient branch alone — the intended behaviour, since the laminar-flow conservatism being calibrated lives only in the ODE.

### 4. The Phase 2 import surface is pinned by an interface-stability test
`tests/test_evaluator_phase2_surface.py` imports `evaluate_realization` exactly as Phase 2 will (clean top-level import, no notebook/orchestrator context), replays a small θ matrix against a synthetic 2016 stand-in, and confirms per-row results expose both `Z_static`/`Z_transient` and both failure flags so the static and transient rejection sets — and the survival-discrimination decomposition — can be formed. It also asserts the Z-based and flag-based rejection sets agree, and that a bare subprocess interpreter can import and call M8 (spec §9 point 1). It is an interface-stability test: no physical outcome is asserted.

---

## Alternatives Considered

### M8 owns the timestep loop (calling the M5/M7 kernels directly)
- Cons: duplicates M7's serial timestepper and the two-head logic, violating the M1–M9 decomposition (spec §1, §9). **Rejected** — M8 delegates to `integrate_progression`.

### Matched driving head for both branches (subtract 0.3·D_bl from the static comparator)
- Pros: removes the head-convention offset from the static–transient gap, leaving a cleaner temporal-only comparison.
- Cons: misrepresents conventional deterministic practice, which uses the gross head. **Recorded as a documented variant**, not the baseline.

### Independent static and transient evaluation tracks
- Cons: would draw `θ`/`r_e` independently per branch, conflating physical bias with sampling noise and destroying the Phase 1 deliverable (spec Property 2). **Banned** (ADR-0002).

---

## Rationale
Enforcing the shared sample and the single-source `H_c` inside one function is the only way to guarantee the static–transient comparison reflects physical bias rather than sampling noise; testing it at the orchestration level (not just in the kernels) is what makes the guarantee observable. Committing to the gross-head static comparator keeps the static branch faithful to deterministic practice while keeping the head-convention offset explicit and decomposable. Pinning the import surface protects the one cross-phase dependency that a future refactor could silently break.

---

## Consequences
- The `evaluate_realization` signature `(theta_row, hydrograph, geometry, l_ini=0.0, store_trajectory=False)` and the `EvaluationResult` field set are frozen Phase 2 contracts; changing them requires a superseding ADR.
- The matched-head variant, if run, is a sensitivity configuration reported alongside the baseline, not a replacement; its result feeds the §12 failure-mode-4 decomposition.
- `Z_static` carries no `C_e` dependence by construction; prior-to-posterior `C_e` shift is attributable to the transient branch only.
- Consumes and depends on ADR-0001 (stochastic C_e), ADR-0002 (shared-sample contract), ADR-0007 (r_e-translated erosion head, z_toe ≡ h_e), ADR-0008 (heave-gradient collapse and Z ≤ 0 sign convention), ADR-0010 (HydrographRecord and geometry handoff schemas).

---

## References
- Phase 1 architecture spec §1 (M8), §2 (M8 I/O contract), §3–§4 (shared preamble then branch; head conventions), §8 (Phase 2 handoff and survival-discrimination decomposition), §9 (importable without notebook context), §12 (failure mode 4).
- ADR-0001, ADR-0002, ADR-0007, ADR-0008, ADR-0010.
- Tests: `tests/test_evaluator.py`, `tests/test_evaluator_phase2_surface.py`.
