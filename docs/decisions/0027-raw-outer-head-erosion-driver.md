# ADR-0027: Erosion-Driving Head Uses the Raw Outer Level (r_e Removed), Superseding ADR-0007

Date: 2026-07-07 (meeting); email-confirmed 2026-07-08
Status: Accepted (supersedes ADR-0007). Pol confirmed the convention in writing
on 2026-07-08 ("Ja klopt" — once heave/uplift breaches the blanket, progression
uses the full un-attenuated outer head; r_e applies only to uplift/heave), so
the closure no longer rests on the meeting recollection.

Pointer correction 2026-07-31: the two references to the validation note were
updated from its pre-closure filename (`OPEN-head-datum-re-convention.md`) to
its current one (`head-datum-re-convention-CLOSED.md`), renamed in commit
`08267ee`; both had been dangling since. Pointer strings only -- no decision,
status, rationale or consequence is changed by this edit.

## Context

ADR-0007 applied the Mazure response factor r_e to the **erosion-driving**
head of the transient branch:

    H_erosion(t) = r_e * (h(t) - z_toe) - 0.3 * D_bl        (ADR-0007, retired)

deviating from Pol SIE 2024 Eq. (6) as printed, which uses the **raw** outer
water level h(t) with no r_e:

    H = h - h_e - 0.3 * D_bl                                 (SIE 2024 Eq. (6))

r_e appears in Pol's model **only** on the uplift/heave head, via Eq. (10):
`u_it(t) = h_e + r_e*(h(t) - h_e)` (Eqs. (8)-(9) consume `u_it`). ADR-0007's
rationale was that Eq. (6) is written for Pol's r_e = 1 validation geometry and
that field application should compose r_e onto the erosion head. That reasoning
was flagged as the **one unvalidated physics convention in the engine** and
tracked as the OPEN reference anchor #4
(`docs/validation/head-datum-re-convention-CLOSED.md`), because it could not be
closed from the papers alone: the 0.3·D_bl crack term appears only in the SIE
field model (r_e = 0.6), while every r_e = 1 calibration case (B25-245, FPH)
has D_bl = 0, so no published configuration combines an active crack term with
the r_e = 1 case where the engine and Eq. (6) coincide. Its stated closure
criterion #2 was: *"Pol indicates Eq. (6)'s raw head is intended for
progression → this becomes a DISCREPANCY; open an ADR to supersede ADR-0007 and
change the erosion-head composition (r_e removed from H_erosion; retained on
uplift/heave), with re-validation of the affected transient results."*

## Evidence (Pol meeting 2026-07-07, plus his published equations)

Two independent lines, both pointing the same way:

1. **Pol's published equations (decisive, memory-independent).** SIE 2024
   Eq. (6) uses the raw outer water level h for the erosion head; Eqs. (8)-(10)
   put r_e only on the uplift/heave head. Re-read from the PDF on 2026-07-07
   (`pol_sie_2024.pdf`, equation block extracted: Eq. (6) `H = h - h_e - 0.3
   D_bl`, Eq. (10) `u_it = h_e + r_e*(h - h_e)`). The engine's ADR-0007
   composition was the deviation; the fix aligns the engine with Pol's own
   model.
2. **Pol's physical rationale (meeting, author-confirmed).** He stated that
   after heave occurs there is a hole in the blanket, so r_e no longer plays a
   role and should not be present in the erosion-head equation thereafter. This
   is exactly the SIE 2024 §2.1 mechanism ("excess pore pressure at the
   downstream levee toe can lead to uplift and rupture of a cohesive blanket,
   creating an unfiltered exit point"): once the blanket ruptures the exit is
   unfiltered and the full outer head drives progression. r_e models the
   intact-blanket damping and therefore belongs only to the uplift/heave head
   that governs whether/when the blanket ruptures.

The temporal phrasing ("r_e off *after* heave") and Eq. (6)'s unconditional raw
head are **numerically identical in this engine**: erosion runs only when
`I_er` is true, which requires `heave_now` (ADR-0008 collapse), so `H_erosion`
influences the rate only at timesteps where heave is active. Using the raw head
unconditionally (Eq. (6)) therefore reproduces "r_e dropped once the blanket
ruptures" exactly, with no explicit post-heave latch needed.

## Decision

Adopt the raw-outer-level erosion head, matching Pol SIE 2024 Eq. (6):

    H_erosion(t) = (h(t) - z_toe) - 0.3 * D_bl               (r_e removed)

r_e is **retained** on the uplift/heave gate (`Delta_h_blanket(t) = r_e*(h(t) -
z_toe)`, Eq. (10)) and on the static comparator (see below). This closes the
OPEN reference anchor #4 via its own closure criterion #2.

Scope: **the transient erosion-driving (rate) head only.** The uplift/heave
gate and the static comparator are unchanged.

## What is NOT decided here (flagged for the owner)

- **The static comparator** was left r_e-attenuated by this ADR and flagged as
  a separate decision. **RESOLVED by ADR-0028 (2026-07-07):** Sellmeijer 2011
  defines `H_c` as the critical "hydraulic head across structure" (gross, no
  r_e), so the static comparator was moved to the raw head too. r_e now drives
  only the uplift/heave gate; both piping heads are raw and differ by exactly
  0.3·D_bl. The large r_e head-convention component this ADR introduced is
  therefore removed — see the updated Consequences note below and ADR-0028.
- **Lag interaction.** Phase 1 always uses `InstantaneousHead`; the erosion head
  is taken from the raw river stage `h_river[k]` directly (Eq. (6)'s outer
  level), independent of the M4 head model. If the linear-reservoir lag
  (ADR-0004) is ever activated, whether Eq. (6)'s h should carry that aquifer
  lag needs its own decision. Inert in Phase 1.

## Consequences

- **Transient branch is materially less conservative at damped sections.** At
  r_e < 1 the erosion head rises from `r_e*(h - z_toe) - 0.3·D_bl` to `(h -
  z_toe) - 0.3·D_bl`, i.e. by the factor ~1/r_e on the head-difference term
  (KP 62.0 production r_e ≈ 0.33 → the erosion head roughly triples). Through
  the 0.81 power this raises dl/dt and the transient failure probability
  substantially. The engine was previously **conservative** on progression at
  every damped section (OPEN item "Impact" section); that conservatism is
  removed. **This changes the core Phase 1 deliverable** (the static–transient
  gap) and may make transient transitions reachable where ADR-0024 found them
  unreachable (e.g. KP 62.0) — to be quantified on the next sweep (none run with
  this change yet).
- **The head-convention gap component.** This ADR alone (static still
  attenuated) would have made the component **both** the r_e attenuation and the
  0.3·D_bl crack loss — a large confound. **ADR-0028 resolves this**: the static
  comparator also moved to the raw head, so r_e drops out of both piping heads
  and the head-convention component returns to **exactly the 0.3·D_bl crack
  term** (the spec §12 fm4 original framing). The gap is then a clean temporal
  comparison. See ADR-0028.
- **r_e now reaches the transient branch only through the uplift/heave gate.**
  The transient *rate* head is r_e-independent; r_e enters the transient branch
  solely via `Delta_h_blanket` in the gate. Consequently the transient failure
  set is **no longer monotone in r_e** (a higher r_e opens the gate at a
  superset of timesteps, but forward-Euler overshoot in the rising-H_eq phase
  can locally reduce l_final). `test_run.py::test_foreland_treatment_threaded_
  and_recorded` is updated: static failures stay a strict superset under
  open-entry (higher r_e), the transient branch is asserted to respond (the
  matrices differ) but not as a superset.
- **Shared-sample contract (ADR-0002) untouched.** θ_j and the single computed
  r_e are still shared across both branches; only how the transient rate head
  *uses* r_e changed (it no longer does), exactly as ADR-0017 relaxed the
  single-source-H_c convention without touching the shared θ/r_e.
- **Reference cases unaffected.** B25-245, S2-2 and FPH are r_e = 1
  configurations, where raw ≡ attenuated, so every M7 reference test is
  bit-identical. Confirmed: the full suite is green after the change.
- **Tests.** New discriminating M7 tests at r_e < 1
  (`test_erosion_head_uses_raw_outer_level_not_re_attenuated`,
  `test_gate_still_uses_re_attenuated_head_not_raw`) pin raw-rate-head +
  r_e-attenuated-gate; the r_e = 1 head-datum tests are unchanged. M8 tests
  that reconstructed the retired `r_e*(h)-0.3·D_bl` rate head are updated to the
  raw head.

## Code

- `bep_reliability_engine/progression.py`: `integrate_progression` step (c)
  computes `h_erosion = (h_river[k] - z_toe) - 0.3*d_bl` (was
  `delta_h_blanket - 0.3*d_bl`); module + kernel docstrings updated.
- `bep_reliability_engine/evaluator.py`: docstrings updated to describe the
  static-attenuated / transient-raw split as the head-convention component.
- No change to M4/M5/M6, the static branch, or the M8 signature.

## References

- Pol SIE 2024, Eqs. (6), (8)-(10), §2.1 (blanket rupture / unfiltered exit);
  `docs/references/pol_sie_2024.pdf`.
- ADR-0007 (superseded); ADR-0008 (I_er ≡ heave_now collapse — why "raw always"
  equals "raw after heave"); ADR-0002 (shared sample, untouched); ADR-0009 (the
  head-convention gap component, extended here); ADR-0017 (the opt-in-override
  precedent); ADR-0024 (KP 62.0 raw-tail finding, may shift).
- `docs/validation/head-datum-re-convention-CLOSED.md` (closed by this ADR via
  criterion #2); `docs/validation/reference-anchor-status.md` §4.
- `docs/validation/pol-meeting-2026-07-07-dispositions.md` (Answer 1).
