# ADR-0007: Response Factor Applied to the Erosion-Driving Head

Date: 2026-06-11
Status: Accepted

## Context
Pol SIE 2024 Eq. (6) defines the erosion head as H = h − h_e − 0.3·D_bl with h the **untranslated** outer water level, whereas the architecture (§3, steps c and j) drives pipe progression with H_erosion = r_e·(h − z_toe) − 0.3·D_bl, the r_e-translated aquifer head. The discrepancy was surfaced during M4 design review and required an explicit decision rather than silent absorption.

Datum note: z_toe in the architecture is the polder surface elevation at the landside exit point and is identical to Pol's h_e, the head datum of Eqs. (6) and (8).

## Decision
The architecture's convention is confirmed as intentional: H_erosion(t) = r_e·(h(t) − z_toe) − 0.3·D_bl.

Rationale:
1.  **Physics.** The head available to drive flow toward the pipe is the head actually present in the aquifer at the exit; for a cross-section with foreland and blanket damping, that is the r_e-attenuated head, not the raw river stage. Eq. (6) is written for the configuration of Pol's validation experiments and basic schematization, where the outer water acts directly on the aquifer — the r_e = 1 case. The paper itself contains the response-factor machinery for field application (Eq. (10)); the architecture composes the two elements, which is the standard WBI-style assessment convention (local exit head with damping, compared against the resistance model).
2.  **Composition order.** The 0.3·D_bl term is a local head loss across the exit crack, a fixed loss independent of upstream attenuation, so it is subtracted after the r_e translation: H = r_e·(h − h_e) − 0.3·D_bl, not r_e·(h − h_e − 0.3·D_bl).
3.  **Reference cases unaffected, for a principled reason.** The B25-245, FPH, and paper Fig. 4 configurations have direct hydraulic connection to the aquifer, so r_e = 1 is the physically correct setting for those geometries. Reproducing the paper requires setting up the paper's geometry — in which the two conventions coincide — not a special "paper convention" switch in the code.

## Consequences
*   r_e applies identically to both limit-state branches (the static comparator already uses the translated peak head per §3 step 4), so this convention adds no fourth component to the static–transient gap decomposition; the head-convention component of Failure Mode 4 (§12) remains the 0.3·D_bl difference only.
*   The geometry config documents the datum explicitly: z_toe is described as "polder surface elevation at the landside exit point; equals h_e in Pol SIE 2024 Eqs. (6) and (8)."
*   The M7 head-datum verification test is written in these terms: for a paper-configuration case (r_e = 1), the implemented heads must reproduce the paper's H relative to h_e, closing the head-datum verification flag from the reference-paper guidance.
