# ADR-0051: Opt-In Crack-Resistance Override, and the Equal-Head-Convention Comparison

Date: 2026-08-28

## Status
Accepted

---

## Context

The engine's static-vs-transient bias (RQ1) compares two limit states that are fed
one shared sample through one M8 call (ADR-0002) and one single-source `H_c`
(spec §1, M6). Since ADR-0027/0028 both piping heads are measured on the **raw**
outer level against the same landside-toe datum, and `r_e` reaches neither of
them. What is left between the two piping heads is one term and nothing else:

| quantity | formula | crack term |
|---|---|---|
| static comparator head | `h_peak - z_toe` | no |
| transient erosion driver | `(h(t) - z_toe) - 0.3·D_bl` | **yes** |

`tests/test_evaluator.py::test_head_convention_both_raw_differ_by_crack_term`
pins that difference at exactly `0.3·D_bl` to `rel=1e-12`. It is the clean
head-convention component of the ADR-0009 four-component gap, and Stage 6.6
measured it (as the C0 to C1 ladder step) as 75 % of the design-level probability
gap at KP 62.0 and 97 % at KP 57.4.

The supervisors' criticism is that the two models are therefore not being compared
on the same head convention, and that the term doing most of the work is the one
term the *static* model's own author never wrote. The provenance check confirms
that reading (verbatim quotes in
`docs/decisions/equal-head-convention-study.md` §1):

- **Sellmeijer (2011)** contains no blanket, crack or exit-hole head reduction
  anywhere. Its head is "the hydraulic head across the structure, `H_c`" (p. 1141);
  the only "reduction" in the paper is a 5 %/10 % silt-sedimentation correction
  applied to two IJkdijk test readings (p. 1152).
- **Pol SIE 2024 Eq. (6)** introduces it by citation, not derivation: "The imposed
  head difference is reduced by a head loss over the blanket (vertical pipe) due
  to resistance of the fluidized sediment (e.g. Schweckendiek, Vrouwenvelder, &
  Calle, 2014; TAW, 1999): H = h − h_e − 0.3 D_bl" (journal p. 4).
- **Pol (2022) thesis** states the same expression with no citation at all
  (p. 126) and characterises it, in the Strijenham failure-case appendix, as
  practice rather than mechanics: "The 0.3 D_bl correction for exit hole
  resistance is used in current levee safety assessments in the Netherlands"
  (p. 198).
- **Schweckendiek (2014)**, the source Pol cites, puts the same term on the
  **static** Sellmeijer limit state: `Zp = mp·Hc − (h − hp − 0.3d)` (Eq. 3.14,
  p. 26), noting the limit state "is supposed to be used for safety assessments in
  the Netherlands in the near future".

So the term is a Dutch assessment-rule convention that Dutch practice applies to
*both* limit states, and that Pol carried into the transient formulation while
this engine's static comparator — deliberately, per ADR-0028 — uses Sellmeijer's
own gross head. Both of those choices are defensible as "each model as its author
intended"; neither is a like-for-like model comparison.

One half of the like-for-like comparison already existed. Stage 6.6's comparator
**C1** is the crack-reduced static comparator: both sides reduced, the Dutch
practice reading. The other half — a **crack-free (gross-head) transient**, both
sides raw, the contested term removed — did not, and ADR-0040 explicitly declined
to build the hook. That is exactly the experiment the supervisors asked for.

---

## Decision

Add a keyword-only `crack_resistance_factor: float | None = None` override of the
Eq. (6) coefficient, on the established additive pattern (ADR-0017, ADR-0041,
ADR-0045, ADR-0049, ADR-0050):

- `progression.resolve_crack_resistance_factor` is the one definition both
  backends read; `progression.integrate_progression` and
  `progression_numba.integrate_progression_numba` take the keyword;
- `evaluator.evaluate_realization`, `evaluate_batch` and
  `evaluate_batch_diagnostics` take it and forward it (the `EvaluationResult` /
  `BatchDiagnostics` **field sets** are untouched, which is what ADR-0011
  freezes);
- a `Config.crack_resistance_factor` field, threaded by `run.py` through
  `_EvalSettings`, **dropped from `to_metadata()` when None** so every
  pre-ADR-0051 `config_hash` is byte-identical to what its persisted run
  recorded;
- `bayesian_reliability_updating.replay` (batch and scalar) and
  `fragility_update`, so a Phase 1 run carrying the knob replays under its own
  assumption instead of silently reverting to 0.3.

`None` resolves to the module constant `CRACK_RESISTANCE_FACTOR = 0.3` through the
identical expression, so an un-overridden call is **bit-identical**. `0.0` removes
the term, giving `H_erosion = h(t) − z_toe`: the same head the static comparator
uses, to the last bit. Negative factors are refused — a negative coefficient would
raise the erosion head *above* the gross outer level, which no source licenses.

Unlike the ADR-0041 end factor, the knob is **not refused on the numba backend**:
the coefficient is passed into the JIT kernel as an argument rather than baked in.

The knob is transient-erosion-only **by construction**, not by measurement. The
coefficient is read at exactly one place, the step-(c) erosion driver inside the
M7 loop. It does not reach the static comparator, the uplift/heave gate heads
(which never carry the crack term — ADR-0027/0028), `H_eq`, or `l_c`. The static
failure matrix is therefore exactly invariant under it, and the study refuses to
report if a single static cell moves.

Production configs never carry it set.

### Pre-registration (recorded before the measurement was run)

Registered from the campaign plan `docs/work_packages/rq1-revision-campaign_2026-08-28.md` §4.
Deviation from any of these is a finding to be run down, not adjusted away.

1. **E1** — the static branch is bit-identical to the persisted production sweep
   at every level of every section.
2. **E2** — the gross-head transient failure set nests inside the static set at
   every level, up to forward-Euler barrier-jump rows (ADR-0030), which are
   counted and reported rather than assumed absent.
3. **E3** — the equal-convention design-level factor `B_eq = P_static/P_trans,gross`
   falls in ~4 to 12 at KP 62.0 and ~1.5 to 3 at the drained sections
   (KP 58.8, KP 60.0), i.e. `Δβ_eq ≈ 0.2 to 0.7`.
4. **E4** — the sustained-peak limit of the gross-head transient is exactly
   `C0 ∧ gate`, checked in closed form on the run's own diagnostics.
5. **E5** — the equal-convention gap is more canonical-event-exposed than the
   production gap, its head-convention floor being gone. Stated as a
   conditionality with the existing alternate-member measurement cited for
   direction, not re-measured here.

### Scope of the measurement

Matrix reading only, all four production sections at N = 1e5 over the full
production conditioning grid, plus N = 1e6 at KP 57.4 and KP 62.0 at the design
anchors and their neighbours, on the same seed recipe as the persisted 1e6
campaign. Bulk reading is skipped on the ADR-0040 §4 precedent — it is degenerate
at the stages where the head convention matters — and that is stated, not silent.

---

## Alternatives Considered

### Leave the term fixed and argue the point in prose
Rejected. The term carries 75 to 97 % of the design-level gap; a comparison whose
dominant component is a convention the compared models do not share is not a model
comparison, and no amount of prose converts it into one. The supervisors asked for
the experiment, and the experiment is one keyword.

### Add the crack term to the static comparator instead (make C1 the headline)
Rejected as the *only* answer, kept as a corroborating one. Crack-reducing the
static side is the Dutch-practice reading and is exactly what Schweckendiek (2014)
Eq. (3.14) does, so it is a legitimate equal-convention comparison — and it
already exists as Stage 6.6's C1, measured at N = 1e5 and N = 1e6. But it removes
the contested term from neither side: it doubles down on it. Reporting both
readings (gross-vs-gross new, reduced-vs-reduced existing) brackets the answer
from both directions, and if they agree the head convention is shown not to be
carrying the surviving gap.

### Change the production default to 0.0
Rejected outright. Each model is used as its author intended (ADR-0027/0028), and
Eq. (6) is what Pol's transient model *is*. The as-published comparison stays the
deliverable; the equal-convention run is a co-equal reading beside it, not a
replacement.

### Make the coefficient stochastic
Rejected on the ADR-0049 ground: this is model-form/convention uncertainty on a
deterministic rule, not aleatory scatter in a field quantity, and the repository
keeps the two apart. A stochastic coefficient would also confound the very
comparison this ADR exists to make clean.

### Apply the override at the Config level only, without a kernel keyword
Rejected. Phase 2's replay and the Stage 6.6-style analysis drivers both drive M8
directly; a Config-only knob would silently revert to 0.3 in exactly the paths
that most need to honour it.

---

## Rationale

This is the sixth use of the additive-override pattern and the first that opens a
constant whose *provenance* — not whose value — is the question. The pattern is
what makes the experiment cheap and safe: default-`None` keyword, bit-identical
baseline, hash-preserving metadata, the exercised value recorded in the study's own
artifact.

Setting the factor to `0.0` rather than adding a separate "gross head" code path
matters for the same reason ADR-0049 scaled `l_c` in M6 rather than in M7: there is
one expression, so the reported behaviour and the computed behaviour cannot
disagree, and the equal-convention claim is a property of the code rather than of a
parallel implementation that has to be kept in step.

---

## Consequences

- `EvaluationResult` / `BatchDiagnostics` field sets unchanged; ADR-0011 intact.
- Every existing `config_hash` survives; the Phase 2 replay gate is unaffected.
- Both progression backends accept the knob (numpy bit-identical when off; numba
  agrees to `< 1e-10`, ADR-0029).
- The static branch is **exactly** invariant under it, by construction and by
  measurement (gate E1).
- Tests: `tests/test_crack_resistance_factor.py` pins bit-identity when off at
  every layer (M7 kernel, both backends, scalar M8, batch M8, a full
  `run_fragility_analysis` sweep), the factor-0 head equality against the static
  comparator head, the metadata drop and hash preservation, the negative refusal,
  the nesting expectation, and the closed-form sustained-peak identity.
- The measured result, the provenance quotes and the comparison against the
  pre-registered expectations live in
  `docs/decisions/equal-head-convention-study.md`, with the per-level evidence in
  `docs/decisions/adr0051-equal-head-convention.json`. §11 of that note is the
  dated measurement record and is authoritative where it differs from this ADR's
  pre-registration.

---

## Measurement addendum (2026-08-28; authoritative where it differs from the pre-registration above)

Executed by `scripts/equal_head_convention_study.py`; full numbers, the
provenance quotes and the per-level tables in
`docs/decisions/equal-head-convention-study.md`, per-level evidence in
`docs/decisions/adr0051-equal-head-convention.json`.

Design-level anchors, matrix reading, historical scenario:

| section | N | stage [m MSL] | B as published | **B equal convention** | 95 % CI | Δβ as published | **Δβ equal convention** | 95 % CI |
|---|---|---|---|---|---|---|---|---|
| KP 62.0 | 1e6 | 46.39 | 26.9 | **7.34** | [6.52, 8.30] | 0.904 | **0.572** | [0.540, 0.605] |
| KP 57.4 | 1e6 | 39.21 | 566 | **23.1** | [18.0, 31.3] | 1.558 | **0.842** | [0.780, 0.915] |
| KP 58.8 | 1e5 | 41.00 | 2.75 | **1.87** | [1.86, 1.88] | 1.224 | **0.879** | [0.871, 0.887] |
| KP 60.0 | 1e5 | 42.75 | 2.92 | **2.11** | [2.10, 2.13] | 1.866 | **1.549** | [1.537, 1.561] |

Gates: E1 held (whole-matrix static identity at all four sections at N = 1e5,
with the knob off and again with it on; the persisted ADR-0040 ladder's C0 and
C4b counts reproduced at all ten N = 1e6 levels, including the pre-named 1696
and 1132). E2 held (zero nesting violations anywhere at N = 1e5; 10
forward-Euler flip rows at KP 57.4 N = 1e6, counted and reported, none at
KP 62.0). E4 held with a Δt rider: the closed form `C0 ∧ gate` is exact at seven
of the eight checked cells, and the eighth is a single row of 100 000 at
KP 58.8 41.00 m whose breach vanishes at Δt/2 (the ADR-0030 barrier jump; the
head there sits 3.04 mm below `H_c`).

**E3 is a partial deviation and is recorded as a finding, not smoothed.** Its
ratio half is confirmed at every section it covers (KP 62.0 in 4 to 12; the
drained sections in 1.5 to 3). Its β half, `Δβ_eq ≈ 0.2 to 0.7`, holds only at
KP 62.0: it was derived from the ratio band by a conversion that is not
stage-independent, because `Δβ` depends on where on the normal scale the two
probabilities sit, not on their ratio alone. At KP 60.0's design level a ratio of
2.11 *is* a `Δβ` of 1.549. E3c was arithmetically inconsistent with E3a/E3b from
the start; nothing in the measurement is adjusted for it.

Two results worth carrying forward. First, the head convention accounts for most
but nowhere near all of the as-published gap: the equal-convention comparison
retains 63 % (KP 62.0), 54 % (KP 57.4), 72 % (KP 58.8) and 83 % (KP 60.0) of the
as-published `Δβ`. Second, **there is no unique equal convention**: equalising on
the gross head (this ADR) and equalising on the crack-reduced head (Stage 6.6's
C1 against C4b) give 7.34 against 8.03 at the KP 62.0 design level, agreeing to
within 10 to 24 % at every KP 62.0 level, but 23.1 against 12.0 at the KP 57.4
design level where the reduced-vs-reduced reading rests on two rows. Quote
KP 62.0 as 7 to 8 and KP 57.4 as a band of roughly 5 to 23.

---

## References

- ADR-0027 / ADR-0028 (the two raw heads and the `r_e` scope), ADR-0009 (the
  four-component gap), ADR-0040 / ADR-0041 (Stage 6.6, the C1 crack-reduced static
  comparator, the sustained-peak closed form, and the declined hook), ADR-0011
  (what "frozen" means), ADR-0017 / ADR-0045 / ADR-0049 / ADR-0050 (the override
  pattern this copies), ADR-0029 (backend split), ADR-0030 (Euler barrier jumps).
- Sellmeijer, López de la Cruz, van Beek & Knoeff (2011), EJECE 15, pp. 1139-1154.
- Pol, Kanning, Jonkman & Kok (2024), Structure and Infrastructure Engineering,
  Eqs. (6), (8)-(10).
- Pol (2022), doctoral dissertation, §6.2.4 (p. 126) and Appendix A (p. 198).
- Schweckendiek, Vrouwenvelder & Calle (2014), and Schweckendiek (2014) doctoral
  dissertation Eq. (3.14), p. 26.
- TAW (1999), Technical report on sand boils (piping), Tech. Rep. TAW99-26,
  Rijkswaterstaat — the rule's cited origin; **not held in `docs/references/`**,
  so its own text is unverified here.
- `docs/work_packages/rq1-revision-campaign_2026-08-28.md` §4 (the pre-registered expectations).
