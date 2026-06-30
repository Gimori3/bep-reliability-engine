# ADR-0017: Asymmetric Scale Exponent — a Transient-Only H_c for the Dimensional-Bias Decomposition

Date: 2026-07-01
Status: Accepted

## Context
The Phase 1 scientific deliverable is the bias between the static (Sellmeijer 2011) and transient (Pol 2024) limit states. The architecture spec (§12, Failure Mode 4) warns that this gap is **not** purely temporal and names a 2D-vs-3D **dimensional** component: the static Sellmeijer critical head inherits the 2D plane-strain scale exponent α = −1/3, while the Pol progression ODE was calibrated against 3D hole-exit DgFlow simulations carrying α ≈ −1/2; at field seepage lengths the 3D critical head can be roughly half the 2D value. The spec prescribes the remedy explicitly: provide a hook to substitute α = −1/2 into the Sellmeijer scale factor F_s "applied **exclusively to the H_c governing the transient progression branch while the static comparator retains α = −1/3**; without this asymmetric treatment, both branches would shift simultaneously, conflating the dimensional bias with the temporal bias this study is designed to isolate."

A prior step (review item #6) threaded the deterministic Sellmeijer inputs — including `alpha_exponent` — from M1 config through M8 to M6, fixing the bug where a config override was silently ignored. But that `alpha_exponent` feeds the **single shared H_c** (the single-source-H_c convention of spec §1/§4: M6 is the one place H_c is computed, and the same value feeds the static comparator and the transient H_eq anchor, preventing drift). So a single α is **symmetric** — α = −1/2 shifts *both* branches together, which is exactly the conflation Failure Mode 4 warns against. The decomposition therefore could not be run.

## Decision
Add an optional **transient-only** scale-exponent override, `alpha_exponent_transient`, that recomputes a **separate transient critical head** at the 3D exponent while the static comparator retains the baseline `alpha_exponent`. This **relaxes the single-source-H_c convention in exactly one controlled, opt-in way** for the dimensional-bias sensitivity run.

Mechanics (M8 `evaluate_realization` and `evaluate_batch`):
- `alpha_exponent` is the **static / baseline** exponent (sets the static H_c, and the transient H_c too unless overridden).
- `alpha_exponent_transient` defaults to `None` → the transient H_c **is** the static H_c (single source preserved, no second M6 call, **bit-identical to the prior behaviour**). When set (e.g. −1/2), M6 is called a second time at that exponent and the result anchors the transient H_eq curve; the static comparator is untouched.
- `l_c` is scale-exponent-independent (Pol SIE 2024 Eq. 13, no α), so it is computed once and shared.
- The M8 `EvaluationResult` gains an `H_c_transient` diagnostic field. It equals `H_c` in the default/symmetric case and is lower than `H_c` only under the asymmetric decomposition, so the two heads are both visible.
- Threaded end to end: `config.alpha_exponent_transient` → `run.py` (`_EvalSettings`) → `evaluate_batch`. Recorded in run metadata as `alpha_exponent_transient` and `dimensional_decomposition_active`.

The decomposition is then run as a pair: a baseline run (`alpha_exponent_transient = None`, both branches at −1/3) and a sensitivity run (`alpha_exponent_transient = -1/2`, static −1/3, transient −1/2). The static fragility is identical between the two; the change in the static–transient gap isolates the dimensional component from the temporal one.

## Why this does not violate ADR-0002 or the shared-sample contract
ADR-0002 (the shared-sample contract) requires the **same θ_j and the same r_e** to feed both branches; that is **untouched** — θ_j and r_e are still computed once and shared. What is relaxed is the *separate* single-source-**H_c** convention (spec §1/§4), and only along the α axis, only when explicitly requested. The relaxation is principled (it isolates a named physical bias the spec asks to isolate), not accidental drift, which is the failure the single-source convention exists to prevent. In the default/production configuration the convention holds exactly.

## Consequences
- **Baseline-neutral.** With `alpha_exponent_transient = None` (the default, and all production configs) there is no second M6 call and the transient H_c is the static H_c object — bit-identical to pre-ADR behaviour. The full existing suite (including the scalar↔batch bit-identity and orchestration reference-loop tests) is unaffected.
- **Contract change (additive).** `EvaluationResult` gains `H_c_transient` (a new field, after `H_c`). Phase 2 reads results by attribute name and does not construct `EvaluationResult`, so this is safe for the Phase 2 import surface; `tests/test_evaluator.py::test_public_interface` is updated to pin the new field and the new keyword-only parameter. `evaluate_realization` / `evaluate_batch` gain a keyword-only `alpha_exponent_transient` defaulting to `None` (additive; the frozen five leading positional parameters are unchanged).
- **Decomposition is now runnable** from config alone, satisfying the spec §12 fm4 prescription. The static branch is provably unshifted (locked by `test_asymmetric_alpha_decomposition_isolates_transient_Hc` and the run-level `test_dimensional_decomposition_run_wiring`, which assert the static margin / static failure matrix are identical to baseline while the transient branch moves).
- **Production configs leave it `None`.** `scripts/generate_configs.py` does not set it; the sensitivity is a dedicated run the analyst configures explicitly.
- **Scope.** This delivers only the **dimensional** isolation. The other two non-temporal gap components — the head-convention term (0.3·D_bl → 0) and the equilibrium-head conservatism (0.9·H_c → ≈1.0, ADR-0009) — remain unthreaded module constants (`CRACK_RESISTANCE_FACTOR`, `EQUILIBRIUM_END_FACTOR`) and are still "planned extensions". Their isolation, if wired, would follow this same opt-in-override pattern.
- **Idealization, not a 3D model.** As the spec notes, the α substitution is an idealized scale-exponent sensitivity, not a validated 3D hole-exit model; it is not expected to reproduce Pol's actual DgFlow critical heads. The decomposition reports a *contribution to the gap*, not an absolute 3D fragility.

## Alternatives considered
- **A second global α with two separate engine passes (static-only and transient-only runs), no shared H_c plumbing.** Rejected: it would duplicate the whole sweep, double the cost, and break the shared-θ/shared-r_e guarantee between the static and transient numbers being differenced — reintroducing sampling noise into the very gap the decomposition measures.
- **Keep α symmetric and document the limitation only (the prior state).** Rejected here because the user requested the decomposition be wired; the symmetric form cannot isolate the dimensional bias from the temporal one (Failure Mode 4).
- **Make `alpha_exponent` itself transient-only and add `alpha_exponent_static`.** Rejected: it would silently change the meaning of the existing `alpha_exponent` field (a symmetric override is a legitimate, simpler use), breaking backward compatibility. Adding the transient override as the new, opt-in field preserves both behaviours.
- **Do not add `H_c_transient` to `EvaluationResult` (compute the transient H_c internally, unexposed).** Rejected: the decomposition is about transparency over the dimensional bias; a diagnostic result that hides the transient critical head while it differs from the static one would obscure exactly what the run is measuring.

## References
- `docs/architecture.md` §12, Failure Mode 4 (the prescribed transient-only α hook); §1/§4 (single-source H_c).
- ADR-0002 (shared-sample contract — untouched here); ADR-0015 (deterministic Sellmeijer inputs); ADR-0009 (the H_eq-conservatism gap component, a sibling non-temporal contributor not addressed here).
- `bep_reliability_engine/evaluator.py` (`evaluate_realization`, `evaluate_batch`, `EvaluationResult.H_c_transient`); `config.py` (`alpha_exponent_transient`); `run.py` (`_EvalSettings`, metadata).
- `tests/test_evaluator.py::test_asymmetric_alpha_decomposition_isolates_transient_Hc`, `::test_asymmetric_alpha_batch_matches_scalar_and_default_is_unchanged`; `tests/test_run.py::test_dimensional_decomposition_run_wiring`.
- Pol, Noordam & Kanning (2024), Computers and Geotechnics (3D hole-exit DgFlow, α ≈ −1/2); van Beek (2015) (2D/3D scale-exponent divergence); Sellmeijer et al. (2011) (the 2D rule, α = −1/3).
