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

---

## Part 2: outcome (2026-09-25)

Run: `python scripts/criterion_consequence_study.py --results-root
D:/repositories/bep-reliability-engine/results` from the worktree, one record
(`criterion-consequence-and-2016-evidence-study.json`). Gate 1 reproduced all
912 production Phase 3 rows field for field (four arms, 228 rows each); gate 2
held every surface-only segment identical across all ten branch passes; the
hazard cache was unchanged. The gross-head replays took 17 to 22 s per section
and reproduced the production static survival row for row.

### 2.1 Verdicts on the predictions

| | Prediction | Outcome |
|---|---|---|
| A1 | S-prior ≥ T-prior annual, and share, at every cell | **Confirmed**, 16 of 16 cells, in 100 % of paired replicates |
| A2 | prior annual S/T in 1.5 to 30, smallest at KP 58.8, ordered as design-level B | **Range confirmed** (1.86 to 6.03). Smallest at KP 58.8 historically (2.63) but at KP 62.0 under warming (1.86). **Ordering refuted**: KP 60.0 carries the largest ratio (6.03), not KP 57.4 |
| A3 | under S-prior KP 60.0 ranks above KP 62.0 historically | **Refuted.** KP 62.0 stays second; KP 60.0 rises from last to **third**, above KP 57.4 (95 % of replicates historically; under warming the two tie at 1.62e-2) |
| A4 | under S-prior piping leads all eight cells | **Confirmed.** The KP 62.0 +4 K tie (piping share 0.48 [0.46, 0.51], piping ahead in 7.5 % of replicates) becomes a piping lead of 0.72 [0.69, 0.75] in 100 % |
| A5 | static climate ratio smaller at every section | **Confirmed**: quotient 0.58 to 0.79, every interval below 1 |
| P1 | S-post lowers KP 58.8 by more than 2×; T-post by at most 10 % | **Confirmed** on the primary (raw) evaluation: ×0.43 [0.33, 0.52]; T-post ×0.90. On the fitted evaluation the factor is 0.55, so the "more than two" margin depends on the evaluation |
| P2 | posterior S/T at KP 58.8 below half its prior value | **Confirmed** on the primary evaluation (1.26 against 2.63); 1.59 on the fitted one. Static still higher in 99.9 % of replicates |
| E1 | head convention carries more than half of ln LR at KP 58.8, either order | **Refuted.** Head-first 0.48, head-last 0.08, two-order average 0.28 |
| E2 | joint LR at most 2.5 under any dependence | **Confirmed**: 1.76 (comonotone), 2.07 (independent), 2.45 (Fréchet lower) |
| E3 | one survival at KP 58.8's attainable top carries LR ≥ 10 | **Confirmed**: 16.9 at 42.75 m |

### 2.2 The fit of the static self-posterior

A survival under the static rule removes every row with `H_c < h_peak - z_toe`,
so the static posterior is exactly zero at and below the survived stage and
rises steeply above it. The lognormal cannot follow that: at KP 58.8 it departs
from its own raw points by up to 0.176 in probability (0.057 at KP 60.0), while
the static prior's fit departs by at most 0.0016. The pre-registered fallback
therefore applies: **S-post is the raw (probit-interpolated) evaluation**, and
the fitted one is recorded as `S-post-fit`. An all-raw robustness pass
(`T-prior-raw`, `T-post-raw`, `S-prior-raw`) moves no verdict: the prior ratios
become 2.72 to 7.17 historically and 1.92 to 3.96 under warming. The production
transient fits themselves sit up to 0.033 from their raw points at KP 58.8; that
is production's evaluation policy and is left as it is.

### 2.3 What the choice of criterion does to the annual numbers

Matrix reading, λ_ac = 250 m, primary surface set. Brackets are the 95 %
flood-ensemble sampling interval (hazard only, curves fixed), paired across
branches.

| | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| Annual, transient prior, hist. | 4.98e-4 | 6.85e-3 | 3.22e-4 | 9.17e-4 |
| Annual, steady-state prior, hist. | 1.76e-3 | 1.80e-2 | 1.94e-3 | 2.96e-3 |
| ratio S/T, hist. | 3.53 [3.02, 4.50] | 2.63 [2.35, 3.00] | 6.03 [5.36, 7.05] | 3.23 [2.64, 4.10] |
| ratio S/T, +4 K | 2.13 [1.99, 2.30] | 2.07 [1.99, 2.15] | 3.79 [3.49, 4.15] | 1.86 [1.73, 2.01] |
| annual Δβ, hist. | 0.37 | 0.37 | 0.52 | 0.36 |
| annual Δβ, +4 K | 0.29 | 0.36 | 0.49 | 0.25 |
| climate ratio T / S | 15.3 / 9.2 | 5.6 / 4.4 | 13.3 / 8.3 | 13.4 / 7.7 |
| Annual, transient posterior, hist. (deliverable) | 4.98e-4 | 6.18e-3 | 3.15e-4 | 9.17e-4 |
| Annual, steady-state self-posterior, hist. | 1.59e-3 | 7.81e-3 | 9.63e-4 | 2.95e-3 |
| ratio S/T, posterior, hist. | 3.19 [2.80, 3.86] | 1.26 [1.11, 1.38] | 3.06 [2.33, 3.45] | 3.22 [2.64, 4.10] |
| ratio S/T, posterior, +4 K | 2.01 | 1.34 | 2.62 | 1.86 |
| annual Δβ, posterior, hist. | 0.34 | 0.08 [0.04, 0.12] | 0.32 | 0.36 |
| climate ratio T / S, posterior | 15.3 / 9.6 | 5.8 / 6.1 | 13.4 / 11.5 | 13.4 / 7.7 |

Six findings.

1. **The annual gap is much smaller than the design-level gap, and not because
   anything cancels.** Per event at the design level the criteria differ by
   Δβ 0.85 to 1.22 and B 3.1 to at least 37; per year by Δβ 0.36 to 0.53 and a
   factor of 2.6 to 6.0. The annual number is earned above the design level: at
   KP 57.4 and KP 62.0 essentially all of it (share of the annual probability
   from years whose peak exceeds the design level: 1.00 and 1.00), with the
   probability-weighted peak 1.3 and 1.8 m above it; at KP 58.8 and KP 60.0,
   0.70 and 0.43 historically. There B has already fallen to about 3 to 6, and
   the annual ratio sits close to B at the probability-weighted stage (KP 57.4:
   B 3.4 at 40.50 m against the annual 3.5; KP 60.0: 6.3 at 42.75 m against
   6.0). Because annual probabilities are small, the same ratio is a smaller
   index difference.
2. **Ranking.** Transient, both climates, both sides of the update:
   58.8 > 62.0 > 57.4 > 60.0 (100 % of replicates). Steady-state prior:
   58.8 > 62.0 > 60.0 > 57.4 historically (95 %), with KP 60.0 and KP 57.4 tied
   under warming. After each criterion is updated on 2016 in its own terms, the
   steady-state ranking is the transient one again (100 %).
3. **Dominance.** The criterion moves piping's share upward everywhere and
   changes one ordering: KP 62.0 under warming, where the transient tie becomes
   a steady-state piping lead of 0.72. Under the bulk reading it also changes
   one (KP 57.4 +4 K, overflow to piping, share 0.38 to 0.57), and moves KP 60.0
   to first place historically (57 % of replicates).
4. **Climate ratio.** The transient criterion is the more climate-sensitive
   one: its ratio is 1.3 to 1.7 times the steady-state one before updating.
   After each criterion is updated on 2016, the two come within about 6 % at
   KP 58.8 (5.8 against 6.1; quotient 1.06 [0.97, 1.20] primary, 0.95 fitted,
   0.98 all-raw). At KP 60.0 the quotient rises from 0.63 to 0.85 [0.75, 1.13]
   on the primary evaluation, but only to 0.73 [0.67, 0.80] fitted and 0.72
   [0.65, 0.85] all-raw, so "no longer separated" there is evaluation-dependent
   and is not quoted. The gap persists at the two sections the survival does
   not reach.
5. **The survival update roughly halves the ratio where it is informative**
   (by 2.0 to 2.1 on the primary evaluation, 1.5 to 1.9 on the fitted and
   all-raw ones).
   The steady-state self-update removes 45 % and 13 % of the static prior at
   KP 58.8 and KP 60.0 and lowers its annual probability to 0.43 and 0.50 of the
   prior; the transient update lowers its own by 10 % and 2 %. The posterior
   ratio falls from 2.63 to 1.26 at KP 58.8 and from 6.03 to 3.06 at KP 60.0.
   **Much of the steady-state rule's extra probability at the informative
   section is probability that the 2016 survival itself rules out**, and an
   assessor who applied the steady-state rule and then updated on the survival
   in its own terms would land much nearer the transient answer.
6. **The deliverable's conditions carry over unchanged**: the conductivity
   bracket, the as-if-undrained treatment of KP 58.8 and KP 60.0, the declined
   foreland credit and the one canonical shape apply to both branches. The
   ratios in this table are not invariant to them (conductivity alone moves B
   by up to ×46 at KP 62.0); they are measured here at the production values
   only.

### 2.4 What the 2016 survival says between the two criteria

| | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| rejection, steady-state (gross head) | 2.73 % | 45.22 % | 12.83 % | 0 |
| rejection, steady-state (crack-reduced head) | 0.42 % | 28.36 % | 5.18 % | 0 |
| rejection, transient, gross head | 0.15 % | 8.01 % | 0.73 % | 0 |
| rejection, transient (production) | 0.016 % | 3.81 % | 0.23 % | 0 |
| LR transient / steady-state [95 %] | 1.03 [1.03, 1.03] | **1.76 [1.75, 1.77]** | **1.14 [1.14, 1.15]** | 1.00 |
| LR transient / crack-reduced steady-state | 1.004 | 1.34 | 1.05 | 1.00 |
| LR on the measured berm, gross / crack-reduced | | 1.29 / 1.13 | 1.03 / 1.01 | |
| berm rejection, steady-state / transient | | 23.2 % / 0.90 % | 2.69 % / 0.014 % | |

The intervals are paired row bootstraps and are narrow because the rows are
shared; they do not include the epistemic brackets, which move each rejection
by factors of two to ten (record reconstruction, exit datum) and are not
common-mode between the two criteria.

1. **Direction is a theorem; only the size is evidence.** Because the transient
   failure set is nested in the steady-state one, every survival has a
   likelihood ratio of at least one in favour of the transient criterion and
   every breach at most one (it favours the steady-state rule by B). The 2016
   observation could not have come out the other way. What it supplies is how
   much.
2. **The size is small.** 1.76 at KP 58.8, 1.14 at KP 60.0, 1.03 and 1.00 at
   the two sections the flood barely reached. Jointly over the four sections,
   with the same dependence imposed under both criteria: 1.76 if the sections'
   resistances are fully dependent, 2.07 if independent, and at most 2.45 under
   any dependence. The survival is at most about twice as probable under the
   transient criterion. That shifts odds; it does not validate either model, and
   a single survival to which the steady-state rule assigns probability 0.55
   (KP 58.8) or 0.87 (KP 60.0) is an unremarkable outcome under that rule too.
3. **What there is of it concerns duration, not the head convention.** Remove
   the crack decrement from the transient branch and it still gives 1.68 at
   KP 58.8; give the crack decrement to the steady-state rule and 1.34 remains.
   The head-convention share of ln LR is 0.08 taken last and 0.48 taken first
   (two-order average 0.28; 0.33 at KP 60.0). The initiation gate is not the
   channel either: 99.8 % of the realizations on which the two criteria disagree
   about 2016 at KP 58.8 and KP 60.0 did see uplift and heave (41,318 of 41,404;
   12,571 of 12,602). They survive the transient criterion because the pipe did
   not traverse the seepage path before the recession. (At KP 57.4, where the
   flood barely engaged, 15 % of the 2,711 disagreeing rows never opened the
   gate.)
4. **The berm weakens it further.** On the measured post-works berm the ratio is
   1.29 at KP 58.8 and 1.03 at KP 60.0. The berm-reading static rejection is
   **23.2 %**, not the 34 % that Chapter 6 and this repository's earlier note
   carried (that is the superseded matrix d70), and the transient one is 0.90 %,
   not 1.5 % or 5.4 %.
5. **What would discriminate.** A survival high on the curves. Under the
   canonical shape a single survival at KP 58.8 carries a ratio of 2 at
   41.00 m, a quarter of a metre above its 2016 peak, and 16.9, 6.9, 37.6 and 14.2 at the attainable
   tops of KP 58.8, KP 60.0, KP 57.4 and KP 62.0. The 2016 peaks sat 0.28 to
   0.66 m below the design level at three sections and 0.45 m above it at
   KP 57.4, whose curves engage late, which is why they discriminate so little.
   A breach, conversely, would favour the steady-state rule by B; a boil record
   with no breach bears on the uplift and heave gate, which the two criteria do
   not separate here. Direct evidence on the traverse (piezometric records at
   the landside toe during a flood, or a post-flood investigation that finds
   partial pipes) would bear on the mechanism itself.

**The plain answer.** The 2016 survival favours the transient criterion, as any
survival must, but weakly: it is 1.76 times as probable under it at KP 58.8,
1.14 times at KP 60.0 and indistinguishable elsewhere, at most about twice as
probable over the four sections together, and 1.29 times at KP 58.8 on the
measured berm. It does not validate the transient model or invalidate the
steady-state one. What little it says concerns finite flood duration rather than
the head convention. A single survival high on the fragility curves would carry
ratios of 7 to 40.

### 2.5 What this changes elsewhere

* `survival-information-and-nesting-study.md` §2.3 decided that no Bayes factor
  or model-selection apparatus should be introduced, and that remains right for
  model selection. **The owner decided on 2026-09-25 (Green Light item 2) that
  the per-section likelihood ratio is stated in the thesis**, as the quotient of
  two survival probabilities the thesis already prints, with its joint bound
  over dependence, and with no model prior, posterior model probability or
  evidence scale. That note's §2.3 numbers (0.945 / 0.968 against 0.424 / 0.267,
  and the 34 % berm figure) are the pre-rebase values; the re-based ones are
  above.
* `system_integration/cli.py` still hard-codes the transient branch, correctly:
  the deliverable is transient. The steady-state annual numbers above are a
  labelled companion, not a production change.

### 2.6 Deliberately not done

* No steady-state reading of the Phase 3 conductivity, grain-size or seam
  brackets: the question is what the criterion does at the production inputs.
* No m_p-on static self-update. With the model factor carried per row, the
  static survival still truncates the effective resistance, because the same
  factor applies to the observation and the prediction; softening it would need
  a model error partly independent between events, which no part of this model
  carries.
* No re-evaluation of the design-level anchors: they are unchanged and already
  recorded.
