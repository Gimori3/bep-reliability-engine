# ADR-0009: H_eq-Conservatism as a Fourth Component of the Static–Transient Gap

Date: 2026-06-14
Status: Accepted (finding); the field-scale magnitude is an open verification with Pol.

## Context
The Phase 1 scientific deliverable is the bias between the static (Sellmeijer 2011) and transient (Pol 2024) limit states. The spec's bias decomposition (architecture §12, Failure Mode 4) warns that this gap must not be attributed wholesale to the time-dependent mechanism, and names **three** contributors:

1. temporal — the time-dependence the study exists to isolate;
2. 2D-vs-3D dimensional — Sellmeijer's α = −1/3 plane-strain scaling vs the 3D α = −1/2;
3. head-convention — the transient branch applies the 0.3·D_bl crack reduction (ADR-0007) while the static comparator uses the gross peak head.

Implementing and validating M7 surfaced a **fourth, non-temporal contributor** that §12 does not yet name.

## The finding (quantified — M7 note §5D)
Reproducing the in-domain L = 3 m S2-2 DgFlow case (CG24 Fig. 10 / thesis Fig. 5.10) with the M7 integrator at the calibrated C_e = 0.08 over-predicts DgFlow's published post-critical average rate (Table A.5: **7.08·10⁻⁵ m/s**; digitized 7.25·10⁻⁵) by **≈ 1.95×** — the integrated [L/2, L] average is **1.3825·10⁻⁴ m/s**, Δt-converged to 0.1 %. This is **not** a coefficient error (89/0.81 are validated exactly by the pinned-worked-value unit test) and **not** a peak-vs-average artifact (it is the Δt-converged phase average, *larger* than the l_c-pinch hand estimate that earlier read ~1.4×).

Inverting Eq. (15) along the digitized DgFlow trajectory backs out DgFlow's **effective post-critical equilibrium head H_eq/H_c ≈ 1.01–1.04** (the digitized SIE 2024 Fig. 3 *simulated* equilibrium curve independently reads ≈ 0.978 over l/L > 0.5). The reliability model's piecewise-linear H_eq (SIE 2024 Eq. (11)) instead ramps from H_c at l_c down to **0.90·H_c at L**. The lower equilibrium head inflates the overload (H − H_eq) by up to ≈ 2× in the progressive phase and, through the 0.81 power, inflates dl/dt by ≈ 1.8–2.2× (1.78× at l = 1.6 m → 2.23× at l = 2.2 m). SIE 2024 §2.3 introduces the 0.9·H_c end anchor explicitly as "a conservative estimate based on equilibrium curves following from the numerical simulations." So the over-prediction is a **designed-in conservatism of Eq. (11)**, faithfully implemented in M7 — not a defect, and distinct from the head-convention offset of ADR-0007 (which acts on the load head, whereas this acts on the equilibrium/resistance curve).

## Decision
The static–transient gap decomposition **carries a fourth component, H_eq-conservatism**, alongside the temporal, 2D-vs-3D dimensional, and head-convention components. Stage 6's bias decomposition and the eventual discussion must attribute the portion of the gap arising from Eq. (11)'s conservative equilibrium curve to this component, so it is not over-attributed to the temporal effect — precisely the Failure Mode 4 error the spec warns against. The magnitude established here (**≈ 1.95× progressive-phase rate inflation** at L = 3 m, D/L = 1/3, ~10 % overload) is the documented in-domain anchor.

## Open question — verify with Pol
The decomposition assumes DgFlow's effective equilibrium head is ≈ 1.0·H_c in the progressive phase, established here from one in-domain case (L = 3 m) via inversion plus the generic SIE Fig. 3 curve. **Whether DgFlow's effective H_eq stays ≈ 1.0·H_c at field scale (L of tens of metres, the Tokachi sections) is the open question.** If it does, the ≈ 1.95× conservatism is roughly scale-invariant and the gap component is sizeable at every scale; if the equilibrium curve flattens or steepens with scale, the component is scale-dependent and the field-scale attribution shifts. Confirm against Pol's equilibrium-curve data, or with Pol directly, before the Stage 6 decomposition is finalized.

## Alternatives considered
- **Substitute DgFlow's ~1.0·H_c equilibrium curve for Eq. (11) in M6/M7.** Would remove the component, but is **out of scope**: Eq. (11) is the published SIE 2024 reliability-model choice the spec adopts, and replacing it is itself a decision requiring its own ADR. Eq. (11) stays; the consequence is documented instead.
- **Absorb the 1.95× into the S2-2 rate tolerance.** Rejected: that would hide a real, scientifically meaningful bias inside a test tolerance — the exact failure this ADR exists to prevent. The S2-2 test instead pins the actual integrated rate as an explicitly-labelled regression guard and states it is not a Pol-validated absolute rate.

## Consequences
- **M7's transient branch runs ≈ 2× faster than a DgFlow-faithful model in the progressive phase**, so the transient limit state is *more conservative* (higher P_f) than DgFlow by design. Acceptable (it is Pol's own conservatism), but now a named, quantified part of the gap rather than a hidden one.
- The in-domain test `test_s2_2_in_domain_shape_and_rate` gates the progressive-phase **shape** against DgFlow (Pol-anchored, ≤ 0.10 normalized; measured 0.064) and **pins the actual integrated rate 1.3825·10⁻⁴ m/s as a regression guard** encoding this ≈ 1.95× offset; its docstring states the pin is *not* a Pol-validated absolute rate.
- B25-245's progressive phase is not gated (out of domain, §4 note), so S2-2's shape gate is the only quantitative progressive-phase validation in M7 and is treated as load-bearing.
- Cross-reference: M7 reference note §5D (the integration, the Eq.-(15) inversion, and the shape numbers); architecture §12 Failure Mode 4 (extended here from three components to four).

## References
- Pol SIE 2024, Eq. (11) and §2.3 ("a conservative estimate"); Eq. (15) rate law.
- Pol, Noordam & Kanning (CG24) 2024, Fig. 10 and Table A.5 (L = 3 m S2-2; 7.08·10⁻⁵ m/s).
- `docs/decisions/m7-pol-ode-reference-values.md` §5D (quantified finding and inversion).
- `docs/architecture.md` §12, Failure Mode 4 (three-component decomposition this extends).
- ADR-0007 (head-convention component — distinct from this equilibrium-curve component).
