# ADR-0016: Split of gamma'_s into a deterministic particle weight and a stochastic blanket weight

Date: 2026-06-19
Status: Accepted

## Context
Spec section 7 carries a single submerged unit weight gamma'_s as the sixth entry of the theta vector, and the original implementation used that one stochastic entry in two physically distinct places:

* M6 (`sellmeijer.py`) read it as the **aquifer particle** weight gamma'_p in the resistance factor F_r of the critical head H_c.
* M5 (`initiation.py`, via M7) read the **same** entry as the **blanket** submerged bulk weight gamma'_bl in the uplift and heave limit states.

These are different soils: the eroding sand grain at the pipe tip (gamma'_p ~ 16.87 kN/m^3 for the Tokachi A_g framework) versus the confining A_c clay blanket (gamma'_bl ~ 6.9-10 kN/m^3). Conflating them was both a modelling error and a latent bug: the production config sets the entry to a blanket-like ~10 kN/m^3, so an end-to-end run fed ~10 into F_r as if it were the particle weight, underpredicting H_c and overpredicting static failure. The reference-case M6 tests, meanwhile, supplied particle weights of 14.715-16.19 in the same slot, so the two test suites silently assumed two different physical meanings for one column.

The thesis (Study Area chapter "Stochastic Parameter Vector" / "Fixed Parameters", and the Methodology chapter) resolves this by separating the symbols: gamma'_p is a deterministic basin-wide constant feeding Sellmeijer F_r, while gamma'_bl is the stochastic theta entry feeding uplift and heave. This ADR brings the code into line with that resolution.

## Decision
Split the single gamma'_s into two quantities, named consistently across code, tests, configs, and docs:

1. **gamma'_p — deterministic, M6 only.** A module constant `GAMMA_P_SUB_DEFAULT = 16.87` kN/m^3 (Tokachi basin-wide value from the A_g specific gravities; thesis "Fixed Parameters") is added to `sellmeijer.py`. `_factor_Fr`, `compute_critical_head`, and `compute_critical_head_vectorized` take `gamma_p_sub_kn_m3` as an optional argument defaulting to that constant; they no longer read the theta vector for the weight. The critical head H_c therefore no longer carries stochastic exposure to the sixth theta variable. Reference-case tests override the argument with the case-specific particle weight (14.715 IJkdijk, 16.1865 Pol S2-2) to reproduce published H_c.

2. **gamma'_bl — stochastic, theta vector, M5 only.** The sixth canonical theta column is renamed `gamma_s_sub` -> `gamma_bl_sub` everywhere (`sampling.PARAM_NAMES`, `sellmeijer._PARAM_NAMES`, `config` field and family map, the YAML key, M8 extraction, M7 and M5 kernel arguments `gamma_bl_sub_knpm3`, all tests, scripts, and the doc naming contracts). It drives only the uplift and heave limit states (M5), consistent with ADR-0008.

## Consequences
* The static branch's H_c is now independent of the sixth theta variable; it depends on the five stochastic geotechnical variables (k_aq, d_70, D_aq via H_c and D_bl, k_bl via r_e) plus the deterministic gamma'_p. This matches the thesis static-branch statement and is a deliberate results change from the pre-split code (production H_c rises from the ~10-fed value to the 16.87 particle weight).
* `gamma_bl_sub` adopts the thesis blanket prior: Lognormal, mean 6.9 kN/m^3 (gamma_sat,bl - gamma_w from the OYO 1999 A_c design density), COV 0.056. This replaces the earlier provisional Normal(10.0, 0.05) and makes the canonical vector all-Lognormal -- a deliberate deviation from the Normal of spec §7, applied in `CANONICAL_FAMILY`, the example config, and the M2/M1 tests.
* This supersedes the single-gamma'_s treatment of spec section 7 for the F_r particle weight; the spec's narrative is left intact per the project's documented-deviation pattern (cf. ADR-0007), with this ADR as the authoritative record. The spec's `param_names` contract and the uplift/heave example were updated to the `gamma_bl_sub` name so the contract still matches the code.
* M6 reference-case reproducibility is preserved through the `gamma_p_sub_kn_m3` override; only the production default changed.

## References
- Pol, Kanning, Jonkman & Kok (2024), SIE, Eqs. (8), (9), (12)
- Sellmeijer, Lopez de la Cruz, van Beek & Knoeff (2011), EJECE, formula [6]
- ADR-0001 (stochastic C_e, 7D vector), ADR-0008 (Terzaghi heave gradient, uplift/heave on gamma'_bl)
- Thesis chapters 3 (Study Area: Stochastic Parameter Vector, Fixed Parameters) and 4 (Methodology)
