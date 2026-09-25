# What the choice of piping criterion does to the numbers a levee manager uses, and what the 2016 survival says between the two criteria

Study of record for Green Light item 2 (2026-09-25). Companion study, not an
ADR: no `Config` field, default, prior, physics kernel, persisted sweep,
posterior or published production number changes. Driver
`scripts/criterion_consequence_study.py` (post-processing plus one in-memory
Phase 2 replay of the existing ADR-0051 gross-head arms); evidence
`criterion-consequence-and-2016-evidence-study.json`; gate
`tests/test_criterion_consequence.py`. Every matrix number belongs to the
ADR-0054 re-based production of 2026-09-24.

---

## Part 1: pre-registration (written before any number below was computed)

### 1.1 The question as the supervisors put it, and what it actually asks

The Green Light note: "discuss the differences in the results of the static
and transient models better and more in depth: their effects on the
calculated failure probabilities, and whether or not the 2016 survival
validates the use of the transient model over the static model."

A reading of Chapter 6 end to end, then Chapters 5, 7, 8, 9 and the Summary,
as a reader without the engine, finds three things the text leaves that
reader unable to answer.

1. **What the criterion does to the numbers that are used.** The main
   research question asks how the time-dependent treatment "alters estimated
   levee failure probability". The thesis answers per event, at a stage
   (design-level probabilities, Δβ, B, their decomposition and severity
   dependence). Chapter 7 composes and annualises the transient branch only;
   the word "static" does not occur in it. What the steady-state criterion
   would give for the annual system probability, the section ranking, the
   mechanism shares and ordering, and the climate ratio, prior or posterior,
   has never been computed. `system_integration.bep_input.load_bep_curve`
   can expose either branch; the Phase 3 campaign hard-codes the transient
   one.
2. **Whether 2016 supports the transient criterion, in one place and in one
   plain sentence.** The substance exists but is spread over Chapter 5 §5.3.4,
   Chapter 6 §6.4.2, Chapter 8 §§8.2 to 8.3, the sub-question 2 conclusion and
   the Summary, and it was written on the superseded matrix d70. On the
   re-based production the static survival probability at KP 60.0 is
   1 - 0.1283 = 0.872 against the transient 0.998, so the "markedly more
   compatible" wording that was built on 0.267 against 0.968 now rests on a
   ratio of about 1.14 there. The berm-reading numbers are inconsistent across
   chapters (transient berm rejection at KP 58.8 printed as 0.90 %, 1.5 % and
   5.4 %; the 34 % static figure is pre-rebase).
3. **What part of the evidence concerns time at all.** The design-level gap
   is mostly head convention in probability terms. Whether the survival
   favours the transient criterion *because of* the finite-duration mechanism
   or because of the crack decrement has not been asked.

### 1.2 Estimands and method (fixed now)

**Annual consequence.** Four piping branches, each composed with the
production surface curves (primary set, λ_ac = 250 m) and annualised over the
same 3,000 historical and 5,400 +4 K peaks through the production
composition code path:

| label | curve | survival conditioning |
|---|---|---|
| T-prior | transient, Phase 1 | none |
| T-post | transient, Phase 2 posterior (the production deliverable) | 2016 replay, transient criterion |
| S-prior | static, Phase 1 | none |
| S-post | static, masked by the rows that **survive the static criterion** at the 2016 record | 2016, static criterion |

S-post is the self-consistent static assessment: the posterior an analyst
who believed the steady-state rule would compute from the same observation.
It is not the static branch of the production posterior, which is masked by
the *transient* survival set and so mixes the two criteria. It is built with
`fragility_update.posterior_fragility_from_matrices` on the persisted
`accept_static` mask, so no update logic is re-implemented. Evaluation
follows the production ADR-0024 policy (fitted lognormal where the transition
is bracketed, probit interpolation otherwise); because a static survival
truncates the resistance distribution at the survived stage, the fit of
S-post is checked against its raw points and, if it misrepresents the
truncation, the raw-interpolated evaluation is reported beside it.

Intervals: the published d4PDF member-block bootstrap, stratified inside the
six SST patterns, seed 20260820, 10,000 replicates, one draw per scenario
shared by all branches and sections, so every between-branch and
between-section comparison is paired. Hazard-sampling only, fragility curves
fixed, and far narrower than the conductivity bracket. Gates: the T-post pass
reproduces `rq4_annual.csv` exactly; the hazard cache is unchanged; the
per-event means reproduce each branch's annual number bit for bit.

Reported per section, scenario and branch: annual system probability, piping
share, leading mechanism, rank among the four sections, climate ratio, and
the ratio S/T of annual system probability on each side of the update.
Matrix is primary; bulk is reported where it computes.

**2016 evidence.** Per section, the likelihood ratio of the observed survival
under the two criteria, `LR = P(S | transient) / P(S | static)`, with
`P(S | c) = 1 - rejection_c` on the shared prior rows; a paired row bootstrap
(2,000 replicates) gives its interval. Three static comparators are read:
the production gross-head static rule; the crack-reduced static rule (C1,
`Z_static + 0.3 D_bl` at the replayed peak, the assessment-practice head); and
the head-equalised transient (the ADR-0051 gross-head arm, replayed through
`run_survival_update(..., persist=False)` at production settings), so that
`ln LR` splits into a head-convention part and a finite-duration part in both
orders. Joint evidence over the four sections is bounded over dependence
structures (Fréchet bounds, the same structure imposed under both criteria).
The measured-berm reading is read from the persisted `berm_only` arm
replays.

**What would discriminate.** From the Phase 1 matrices, the likelihood ratio
a single survival (`(1 - P_t) / (1 - P_s)`) and a single breach
(`P_t / P_s = 1/B`) would carry at each conditioning level under the
canonical shape, up to the attainable maximum.

### 1.3 Predictions (stated before computing)

- **A1 (theorem, checked).** S-prior annual ≥ T-prior annual at every section
  and scenario, and the static piping share ≥ the transient one, because the
  raw static curve dominates the transient one pointwise and the composition
  and annualisation are monotone. A violation could only come from a fitted
  tail crossing; if one occurs it is reported, not smoothed.
- **A2.** The prior annual ratio S/T lies between 1.5 and 30 at every cell,
  smallest at KP 58.8 (already high on its curve) and ordered across sections
  as the design-level B is (57.4 > 62.0 > 60.0 > 58.8).
- **A3.** Under S-prior, KP 60.0 ranks above KP 62.0 historically.
- **A4.** Under S-prior, piping leads at all eight section-and-climate cells,
  including KP 62.0 +4 K, where the transient reading is a tie.
- **A5.** The static climate ratio is smaller than the transient one at every
  section.
- **P1.** S-post lowers the static annual probability at KP 58.8 by more than
  a factor of two, against at most ten per cent for T-post; at KP 57.4 and
  KP 62.0 the update is small on both.
- **P2.** At KP 58.8 the posterior ratio S/T falls to less than half its prior
  value. The sign of `S/T - 1` on the posterior side is not predicted: nesting
  does not hold between two posteriors conditioned on different survival
  sets.
- **E1.** Arithmetic from the published rejections, not a prediction:
  LR = 1.76, 1.14, 1.03 and 1.00 at KP 58.8, 60.0, 57.4 and 62.0.
  **Prediction:** the head convention carries more than half of `ln LR` at
  KP 58.8, in either order.
- **E2.** The joint likelihood ratio over the four sections is at most 2.5
  under any dependence structure.
- **E3.** A single survival at KP 58.8's attainable maximum would carry a
  likelihood ratio of at least 10.

Both directions of every prediction will be reported.
