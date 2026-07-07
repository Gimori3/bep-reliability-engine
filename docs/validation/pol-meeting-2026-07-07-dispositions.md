# Pol meeting 2026-07-07 — author-feedback dispositions

Record of Joost Pol's answers (author of the time-dependent BEP formulation) to
the questionnaire in `docs/joost_pol_meeting_vragen.md`, classified and
dispositioned 2026-07-07. The meeting summary is reconstructed from memory; items
noted below as awaiting written confirmation are flagged. Two answers drove
engine/config changes (ADR-0026, ADR-0027); the rest are author confirmations
documented against existing decision records.

## Classification and disposition (per answer)

| # | Claim | Class | Disposition |
|---|-------|-------|-------------|
| 1a | Stochastic r_e (USACE/TAW leakage lengths) is correct/appropriate | RECORD-CONFIRMATION | Endorsed; noted in ADR-0027 / ADR-0007 lineage. |
| 1b | r_e should not be in the erosion head after heave (blanket ruptured) | **REQUIRES-CHANGE → implemented** | Matches Pol's published Eq. (6). Engine changed: **ADR-0027** (r_e removed from H_erosion, retained on uplift/heave). Closes the OPEN reference anchor #4. |
| 2a | Use `C_e ~ Lognormal(0.055, 0.043)` for field reliability | **REQUIRES-CHANGE → implemented** | **ADR-0026**; configs regenerated; drift guard re-pinned. |
| 2b | B25-245 is 0.010 or 0.014 | INSUFFICIENT | Pol acknowledged, deferred ("looking into origin"). Awaiting his email; does not gate ADR-0026. |
| 2c | C_e absorbing laminar-vs-turbulent uncertainty legitimate? | RECORD-CONFIRMATION (corrective) | Pol: **not** legitimate; Sellmeijer's ~12% model factor nominally covers it (debatable). C_e stays stochastic on intrinsic-uncertainty grounds. Recorded in ADR-0026. |
| 3 | 0.9·H_c conservatism at field scale | RECORD-CONFIRMATION (qualitative) | ADR-0009 author-confirmation section; no number, no code. Owner to send Pol the L=3m/1.95× calc. |
| 4 | k_aq–d_70 decoupling is the only viable option | RECORD-CONFIRMATION | ADR-0012 author-confirmation stub. |
| 5 | Use α = −1/3 (2D; thin blankets); 3D → Discussion | RECORD-CONFIRMATION | ADR-0017 author-confirmation stub; confirms the default, −1/2 stays Discussion-only. |
| 6 | l_c 2D-vs-3D under-prediction is a known limitation; stay 2D | RECORD-CONFIRMATION | ADR-0009 note (Discussion); no 3D-calibrated form exists. |
| 7 | r_l = 0 / full compound-event memory is sound | RECORD-CONFIRMATION | architecture §13 row annotated. |
| 8 | Omit the flood-fighting clause (safer/conservative) | RECORD-CONFIRMATION | ADR-0008 author-confirmation stub. |
| 9 | Don't over-emphasize the low-P_f raw-tail framing | RECORD-CONFIRMATION (caution) | ADR-0024 author-caution stub; thesis-framing only, no code. |

## The two implemented changes

- **ADR-0027 (engine physics).** The transient erosion-driving head uses the raw
  outer level `(h - z_toe) - 0.3·D_bl` (Pol Eq. (6)); r_e retained on the
  uplift/heave gate (Eq. (10)). Supersedes ADR-0007, closes reference anchor #4.
  **Material effect:** transient P_f rises at damped sections (erosion head
  ~×1/r_e; KP 62.0 r_e≈0.33 → ~3×), the static–transient gap and the ADR-0024
  KP 62.0 finding may shift.
- **ADR-0028 (engine physics; follow-up decision, owner-approved 2026-07-07).**
  The static Sellmeijer comparator also uses the raw gross head
  `H_c − (h_peak − z_toe)` — Sellmeijer 2011 defines H_c as the "critical
  hydraulic head across structure" (gross, no r_e), read directly from the paper.
  r_e now drives ONLY the uplift/heave gate; the static branch is r_e-independent
  and both piping heads differ by exactly 0.3·D_bl (clean temporal gap). Static
  P_f rises at damped sections (static load ~×1/r_e). Principle: each model used
  exactly as its author intended, or the comparison is unfair. Both changes
  test-first; full suite green; **no sweep run** — a re-sweep is required.
- **ADR-0026 (config).** `C_e ~ Lognormal(0.055, 0.043)` (Pol SIE 2024 Table 2),
  replacing `(0.014, 0.50)`. C_e stays stochastic on intrinsic-uncertainty
  grounds (not laminar/turbulent absorption — Pol, 2c). Amends ADR-0001's prior.

## Open / awaiting Pol's email

- **1b wording** (belt-and-suspenders): the resolution rests on Pol's printed
  Eq. (6) (decisive); a one-line email confirming the verbal "r_e off after the
  blanket ruptures" statement locks the corroboration. Not blocking.
- **2b**: correct B25-245 C_e and the source of the 0.010/0.014 inconsistency.
- **3**: field-scale behaviour of the 0.9·H_c conservatism, after the owner
  sends Pol the L=3m inversion.

## Not covered by this meeting

Any separate head-*datum* question the owner is resolving with Pol by email is
distinct from reference anchor #4 (the r_e-on-erosion-head convention closed
here) and is unaffected by these dispositions.
