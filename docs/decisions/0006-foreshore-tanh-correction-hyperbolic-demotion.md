# ADR-0006: Finite-Foreshore tanh Correction in the Baseline; Full Hyperbolic Mazure Form Demoted to a Logged Diagnostic

Date: 2026-06-11
Status: Accepted

## Context
The Mazure ratio r_e = λ_in/(λ_out + L + λ_in) traces to Pol (2022) thesis Eq. (7.13), where it is exact — not a first-order approximation in L/λ_in — under the stated schematization: steady horizontal flow in a leaky aquifer, vertical leakage through the blankets, semi-infinite blankets, equivalent to USACE (2000) blanket theory case 7a / TAW (2004) model 4A. The genuine validity conditions are therefore (i) blanket extent long relative to its leakage length and (ii) quasi-static response (the §11 τ_aq/T_flood diagnostic).

Across the study reach, foreshore width varies six-fold (44 m at KP62.0 to 600 m at KP60.0) and is the dominant source of cross-section heterogeneity. With λ_out plausibly several hundred meters, even the 600 m foreshore is not semi-infinite, and the 44 m foreshore is nowhere near it. Separately, at Tokachi scale, L (tens of meters) ≪ λ_in (hundreds of meters) holds for the bulk of the prior, and neither Pol paper provides a reference case against which a full in-L hyperbolic implementation could be validated.

## Decision
1.  **Baseline finite-foreshore correction.** Phase 1 applies the effective entry length λ_out,eff = λ_out · tanh(B_f/λ_out), with B_f the foreshore width. Limits: B_f → ∞ recovers the semi-infinite λ_out; B_f → 0 gives λ_out,eff ≈ B_f → 0, deriving (rather than asserting) the no-foreshore treatment at KP62.0. This handles all cross-sections uniformly.
2.  **Full hyperbolic form demoted.** The full hyperbolic Mazure solution in L/λ_in is demoted from automatic fallback to a per-realization validity diagnostic plus documented extension: implement the simplified ratio, compute and log L/λ_in per realization, warn if a material fraction of realizations violates L ≪ λ_in, and implement the full form against a proper source only if that warning triggers. This supersedes the earlier per-realization L/λ_in fallback recommendation and is a documented deviation from the specification language implying the full Mazure formulation is applied.

## Consequences
*   The monitored validity quantities for the hydraulic translation are B_f/λ_out (handled in-model by the tanh correction) and τ_aq/T_flood (handled by the §11 diagnostic); the L/λ_in ratio is logged, not corrected.
*   Test obligations: tanh-limit checks (B_f → ∞ recovers semi-infinite λ_out; B_f → 0 drives λ_out,eff → 0) alongside the closed-form Mazure check of §11.

## References
Verified by the project owner against the sources before locking the form:
*   TR Zandmeevoerende Wellen (TAW, 1999), §4.4.1 Eq. (19): L'_v = λ₁·tanh(L_v/λ₁); §4.4.2 confirms this exact term extends the seepage length for backward erosion piping, with the asymptotic limits L'_v ≈ L_v (narrow) and L'_v ≈ λ₁ (wide) stated in the text.
*   TR Waterspanningen bij dijken (TAW, 2004), Appendix I Eq. (A.I.9) and Appendix 4 p. b4-5 — local copy `docs/references/TAW 2004.pdf` (gitignored).
*   USACE EM 1110-2-1913 (2000), blanket theory — local copy `docs/references/USACE 2000.pdf` (gitignored).
*   Pol (2022), doctoral thesis, Eq. (7.13), p. 158 — local copy `docs/references/pol_thesis_2022.pdf` (gitignored).
