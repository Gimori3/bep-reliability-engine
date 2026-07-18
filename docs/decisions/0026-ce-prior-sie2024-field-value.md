# ADR-0026: C_e Prior = Lognormal(mean 0.055, std 0.043), Pol's SIE 2024 Field Value — Amends ADR-0001

Date: 2026-07-07 (meeting); 2026-07-08 (follow-up email — derivation + B25-245 resolved)
Status: Accepted (amends the C_e prior of ADR-0001; C_e remains a stochastic RV)

## Context

ADR-0001 promoted the erosion coefficient C_e to a stochastic variable and set
its prior to `Lognormal(mean = 0.014, COV = 0.50)`, anchored on Pol's
small-scale/FPH *calibrated* values, with the stated intent that "Phase 2
Bayesian filtering ... will directly constrain this uncertainty" and give "the
engine computational room to adjust this tail." Pol's own reliability paper
(SIE 2024, Table 2) instead uses `Lognormal(mean = 0.055, std = 0.043)` — a mean
~4× higher than the calibrated values. The discrepancy, and whether C_e may
legitimately absorb laminar-vs-turbulent model uncertainty, were open questions
put to Pol.

## Evidence (Pol meeting 2026-07-07)

- **Prior value.** Pol recommends `Lognormal(mean = 0.055, std = 0.043)` for
  levee reliability calculations. The lower calibrated values (0.010, 0.014)
  are small-scale; 0.055 was determined later by incorporating large-scale
  experiments and is his recommended value for practical field application. He
  cites SIE 2024 Table 2 as the reference.
- **On C_e as an uncertainty absorber (the ADR-0001 rationale).** Pol stated it
  is **not** legitimate to use the C_e uncertainty to absorb laminar-vs-turbulent
  model uncertainty. In his view Sellmeijer's own model factor (~0.12 / 12%)
  nominally accounts for that laminar-vs-turbulent uncertainty (he noted this is
  itself debatable). C_e should still be treated **stochastically**, because it
  carries high uncertainty in his experience — but justified by that intrinsic
  uncertainty, not by standing in for a model-form uncertainty it should not
  represent.
- **B25-245 (0.010 vs 0.014) — RESOLVED (email 2026-07-08).** Pol confirmed
  the correct calibrated value is **0.010** ("Dit moet inderdaad 0.01 zijn"):
  Table 1 is right, the Fig. 5 caption's 0.014 is the error. This matches the
  value already adopted in the repo (`tests/test_progression.py::B25_C_E =
  0.010`, which had hypothesised the caption 0.014 was an FPH copy-paste). No
  code change; the hypothesis is now author-confirmed.

## Follow-up email (Pol, 2026-07-08): the derivation of 0.055, and why the factor 3–4

Pol explained the provenance of C_e = 0.055 (thesis §5.4.4 and end of §5.5.2;
Appendix E). Two *different* calibration targets sit behind the two families of
values, which is the key nuance for the thesis:

1. **Detailed time-dependent pipe development (small scale) → C_e ≈ 0.016.**
   Reproducing the pipe growth *over time* in the small-scale tests needs
   C_e = 0.010 (B25-245) or 0.014 (FPH) — thesis Table 5.1; mean 0.016
   small-scale, 0.014 FPH. This is the target closest to what this engine does
   (it integrates dl/dt over the hydrograph).
2. **Mean post-critical growth rate across many tests → C_e ≈ 0.044 → 0.055.**
   Pol then checked how well the *mean* growth rate (after the critical head is
   exceeded) is predicted across 14 progression-dominated tests (7 older + the 7
   from CG 2024), using a regression formula for the average speed (thesis
   Eq. 5.15), because for the older tests only an average speed is known. With
   C_e = 0.016 the mean rate is **under**-predicted (fig 5.13b); matching the
   mean rate across the 14 tests needs C_e ≈ 0.044. Repeating the analysis over
   *all* his tests (Appendix E) gives **C_e = 0.055**.

**The factor 3–4 between the two (0.016 vs 0.044–0.055) is unexplained** — Pol
has no direct explanation, and notes the mean-rate regression (Eq. 5.15) itself
fits the model calculations very well (fig 5.13a), including the runs known to
match small-scale tests at C_e = 0.016. So the discrepancy is genuine and open.

**Field-scale recommendation (unchanged):** *"Met die 0.055 zit je in ieder
geval aan de veilige kant qua faalkans en die is gebaseerd op de grootste set
validatieproeven, dus zelf zou ik dat aanhouden."* — 0.055 is the safe
(conservative, higher failure probability) side and rests on the largest
validation set, so Pol would use it. Which value truly belongs at field scale
"depends on the explanation for the factor 3–4," which remains open.

## Decision

1. **Adopt `C_e ~ Lognormal(mean = 0.055, std = 0.043)`** (CoV = 0.043/0.055 ≈
   0.782), i.e. Pol's SIE 2024 Table 2 field-reliability prior, replacing the
   ADR-0001 `(0.014, 0.50)`.
2. **C_e stays a stochastic random variable** (the ADR-0001 7-D vector and the
   shared-sample contract are unchanged). Its stochastic treatment is now
   justified by its intrinsic high uncertainty, **not** by absorbing
   laminar-vs-turbulent model uncertainty (Pol: that is covered, nominally, by
   Sellmeijer's ~12% model factor). Phase 2 still Bayesian-filters C_e against
   the 2016 survival record, but the defensibility narrative is corrected: the
   filter tightens a genuinely-uncertain physical coefficient, it is not the
   mechanism that launders a model-form uncertainty into C_e.

## Consequences

- **Configs/generator.** `scripts/generate_configs.py`: `C_E_MEAN = 0.055` and
  `FIXED_COVS["C_e"] = 0.043/0.055`; all 8 configs regenerated. The drift guard
  `tests/test_configs.py` pins the new mean (0.055) and CoV (0.782), so the
  decision cannot silently regress.
- **Transient fragility shifts up.** The rate is exactly linear in C_e, so a ~4×
  higher mean scales progression rates ~4× (before the tail/COV change). The
  transient branch becomes markedly more aggressive; combined with ADR-0027
  (raw erosion head) the transient P_f rises substantially versus the prior
  engine. Both are corrections toward Pol's own model. Quantify on the next
  sweep (none run with these changes yet).
- **ADR-0001 amended, not withdrawn.** The promotion of C_e to a stochastic RV
  (the substantive ADR-0001 decision) stands; only its prior *parameters* and
  the *justification* for stochasticity are updated here. ADR-0001 is marked
  "Accepted (C_e prior amended by ADR-0026)".
- **Thesis defensibility (Sub-question on model uncertainty).** The Discussion
  must state Pol's position: laminar-vs-turbulent uncertainty is (nominally)
  in Sellmeijer's model factor, not in C_e; C_e is stochastic because it is
  genuinely uncertain. **[ADR-0045, 2026-07-18: the "nominally" is now
  concrete — the engine carries m_p ~ Ln(1.0, CoV 0.12) as an opt-in factor
  on the single-source H_c (default off; the production baseline and its
  deliverables exclude it, and the companion run quantifies what it adds:
  ≈2.2× on the static shoulder P_f at KP58.8). The Discussion should cite
  the companion numbers rather than implying the factor is inside the
  baseline curves.]** It should also record the **two calibration targets**
  (detailed time-dependent development → 0.016 vs mean post-critical rate →
  0.055) and that the **factor 3–4 between them is unexplained even by Pol** —
  a genuine open point. Because this engine integrates dl/dt over time (the
  "detailed development" target, ~0.016), adopting the mean-rate field value
  (0.055) is a deliberate, Pol-endorsed conservatism; the Phase 2 Bayesian
  update against the 2016 survival record is what reconciles the two against
  the actual field record, and should be framed as such (not as evidence for
  either calibration being "wrong").

## Alternatives considered

- **Keep 0.014 as the Phase-1 prior, carry 0.055 as a sensitivity.** Rejected:
  Pol explicitly recommends 0.055 as the field value and cites SIE 2024 Table 2;
  using his own reliability prior is the defensible baseline. (A 0.014 sensitivity
  run remains available on demand.)
- **Adopt 0.055 but keep COV 0.50.** Rejected: Pol gave the paired (mean, std) =
  (0.055, 0.043); using his std (CoV 0.782) keeps the whole prior his, not a
  spliced mean-only change.

## References

- Pol SIE 2024, Table 2 (`C_e ~ Lognormal(0.055, 0.043)`); CG 2024, Table 1
  (calibrated 0.007–0.030, FPH 0.014); Sellmeijer model factor m_p (~0.12).
- Pol thesis (2022): §5.4.4 and end of §5.5.2 (the two calibration analyses),
  Table 5.1 (0.010 B25-245 / 0.014 FPH), Eq. 5.15 (mean-rate regression),
  fig 5.13a/b, Appendix E (0.055 over all tests). Cited by Pol in the
  2026-07-08 email.
- ADR-0001 (stochastic C_e promotion; prior amended here).
- `scripts/generate_configs.py`, `tests/test_configs.py`,
  `tests/test_progression.py` (`B25_C_E = 0.010`).
- `docs/validation/pol-meeting-2026-07-07-dispositions.md` (Answers 2a, 2b, 2c).
