# Pol meeting 2026-07-07 — author-feedback dispositions

Record of Joost Pol's answers (author of the time-dependent BEP formulation) to
the questionnaire in `docs/joost_pol_meeting_vragen.md`, classified and
dispositioned 2026-07-07, plus his **follow-up email answers (2026-07-08)** that
confirm the memory-reconstructed items and resolve the two that were deferred
(see "Follow-up email" below). Three answers drove engine/config changes
(ADR-0026, ADR-0027, ADR-0028); the rest are author confirmations documented
against existing decision records.

## Classification and disposition (per answer)

| # | Claim | Class | Disposition |
|---|-------|-------|-------------|
| 1a | Stochastic r_e (USACE/TAW leakage lengths) is correct/appropriate | RECORD-CONFIRMATION | Endorsed; noted in ADR-0027 / ADR-0007 lineage. |
| 1b | r_e should not be in the erosion head after heave (blanket ruptured) | **REQUIRES-CHANGE → implemented; email-confirmed** | Matches Pol's published Eq. (6). Engine changed: **ADR-0027** (r_e removed from H_erosion, retained on uplift/heave). Closes the OPEN reference anchor #4. Pol confirmed in writing 2026-07-08 ("Ja klopt"). |
| 2a | Use `C_e ~ Lognormal(0.055, 0.043)` for field reliability | **REQUIRES-CHANGE → implemented** | **ADR-0026**; configs regenerated; drift guard re-pinned. Derivation of 0.055 supplied in the 2026-07-08 email (see below). |
| 2b | B25-245 is 0.010 or 0.014 | **RESOLVED (email 2026-07-08)** | Pol: correct value is **0.010** ("Dit moet inderdaad 0.01 zijn"); Fig. 5 caption's 0.014 is the error. Matches the repo's existing `B25_C_E = 0.010`. No code change. |
| 2c | C_e absorbing laminar-vs-turbulent uncertainty legitimate? | RECORD-CONFIRMATION (corrective) | Pol: **not** legitimate; Sellmeijer's ~12% model factor nominally covers it (debatable). C_e stays stochastic on intrinsic-uncertainty grounds. Recorded in ADR-0026. |
| 3 | 0.9·H_c conservatism at field scale | RECORD-CONFIRMATION (qualitative) | ADR-0009 author-confirmation section; no number, no code. Owner to send Pol the L=3m/1.95× calc. |
| 4 | k_aq–d_70 decoupling is the only viable option | RECORD-CONFIRMATION | ADR-0012 author-confirmation stub. |
| 5 | Use α = −1/3 (2D; thin blankets); 3D → Discussion | RECORD-CONFIRMATION | ADR-0017 author-confirmation stub; confirms the default, −1/2 stays Discussion-only. |
| 6 | l_c 2D-vs-3D under-prediction is a known limitation; stay 2D | RECORD-CONFIRMATION | ADR-0009 note (Discussion); no 3D-calibrated form exists. |
| 7 | r_l = 0 / full compound-event memory is sound | RECORD-CONFIRMATION | architecture §13 row annotated. |
| 8 | Omit the flood-fighting clause (safer/conservative) | RECORD-CONFIRMATION | ADR-0008 author-confirmation stub. |
| 9 | Don't over-emphasize the low-P_f raw-tail framing | RECORD-CONFIRMATION (caution) | ADR-0024 author-caution stub; thesis-framing only, no code. |

## The three implemented changes

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

## Follow-up email (Pol, 2026-07-08)

- **Q1 — C_e derivation and B25-245.** Pol supplied the provenance of 0.055
  (thesis §5.4.4, end of §5.5.2, Appendix E): C_e ≈ 0.016 reproduces the
  *detailed time-dependent* pipe development in small-scale tests (Table 5.1;
  0.010 B25-245 / 0.014 FPH), while matching the *mean post-critical growth
  rate* across 14+ tests via the regression Eq. 5.15 needs 0.044 → 0.055
  (Appendix E). The **factor 3–4 between the two is unexplained even by Pol**.
  Field recommendation stands at 0.055 (safe side, largest validation set).
  **B25-245 = 0.010** confirmed. All folded into ADR-0026.
- **Q2 — erosion-head r_e (1b).** Confirmed in writing ("Ja klopt"): once
  heave/uplift breaches the blanket, progression uses the full un-attenuated
  outer head (Eq. 6); r_e applies only to uplift/heave (Eq. 10). Locks ADR-0027
  and the reference-anchor #4 closure (no longer memory-dependent).
- **Q3 — compound events / r_l = 0 (Answer 7).** Re-confirmed in writing:
  little is known about recovery, so zero recovery is a realistic assumption,
  *especially for peaks so close together*. Noted at architecture §13.

## Still open (owner action, not Pol-blocked)

- **3**: field-scale behaviour of the 0.9·H_c conservatism — Pol gave
  qualitative guidance (ADR-0009) but no number; awaiting the owner sending him
  the L=3m inversion / 1.95× calc.

## Not covered by this meeting

Any separate head-*datum* question the owner is resolving with Pol by email is
distinct from reference anchor #4 (the r_e-on-erosion-head convention closed
here) and is unaffected by these dispositions.
