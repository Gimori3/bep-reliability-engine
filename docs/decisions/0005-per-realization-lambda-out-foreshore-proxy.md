# ADR-0005: Per-Realization λ_out with Hinterland Blanket Proxy for Foreshore Properties

Date: 2026-06-11
Status: Accepted

## Context
The response factor r_e = λ_in/(λ_out,eff + L + λ_in) requires a riverside (entry) leakage length λ_out = √(k_aq·D_aq·D_fore/k_fore), which shares the sampled transmissivity k_aq·D_aq with λ_in. Treating λ_out as a fixed scalar would silently break spec Property 3 (the hydraulic translation is stochastic) on the foreland side while honoring it on the hinterland side, which is incoherent. The site investigation data characterizes the hinterland blanket (the A_c unit), not the foreshore blanket separately.

## Decision
λ_out is computed per realization, exactly like λ_in, from the sampled k_aq and D_aq together with deterministic foreshore blanket properties (D_fore, k_fore) carried in the geometry config. Configs populate (D_fore, k_fore) with the hinterland A_c blanket values as a proxy unless separate foreland data exists.

Sections without an effective foreshore require no special-case "λ_out ≈ 0" rule: with the finite-foreshore correction of ADR-0006, λ_out,eff → 0 automatically as the foreshore width B_f → 0.

## Consequences
*   r_e remains stochastic through all four of its sampled inputs on both the entry and exit sides, consistent with Property 3 and the shared-sample contract (ADR-0002).
*   The hinterland-as-foreshore proxy is a documented modeling assumption recorded here — not a code comment — and is revisited if foreland-specific blanket data becomes available.
*   The geometry contract carries (foreshore_width, D_fore, k_fore); the former `lambda_out_params` placeholder is retired.
