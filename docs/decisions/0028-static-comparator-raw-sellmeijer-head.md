# ADR-0028: Static Sellmeijer Comparator Uses the Raw Gross Head (r_e Removed) — Completing ADR-0027

Date: 2026-07-07
Status: Accepted (completes ADR-0027; the static-branch counterpart)

## Context

ADR-0027 removed r_e from the transient erosion-driving head (Pol SIE 2024
Eq. (6), raw head), keeping r_e on the transient uplift/heave gate (Eq. (10)).
That left the **static** comparator still using the r_e-attenuated head
`Z_static = H_c − r_e·(h_peak − z_toe)` (the spec §3 step 4 / ADR-0007
convention, chosen when both branches were symmetric in r_e). ADR-0027 flagged
the resulting static-attenuated / transient-raw asymmetry as a new, material
head-convention component of the static–transient gap, and deferred the static
question to a deliberate decision. This ADR is that decision.

## Evidence — Sellmeijer 2011, read directly (2026-07-07)

`sellmeijer_2011.pdf`, extracted and read:

- **Symbol list:** *"Hc [m] : critical hydraulic head **across structure**"*.
- **§ test description:** *"the upstream water level is gradually increased,
  resulting in a **hydraulic head across the dike** … If a critical hydraulic
  head is exceeded, the erosion does not stop anymore, but gradually continues,
  until the channel has reached the upstream side."*

Sellmeijer's `H_c` is the critical value of the **gross head difference across
the structure** (upstream water level − downstream exit level), applied
directly. There is **no response factor, no blanket leakage, no damping**
anywhere in Sellmeijer 2011 — `r_e` is entirely a Pol/USACE/TAW field-application
addition. Comparing a gross-head-calibrated `H_c` against an r_e-attenuated
head is a mismatch on Sellmeijer's own terms (it makes the static branch
artificially optimistic).

## Reasoning

1. **Sellmeijer used as intended.** `H_c` is compared to the raw gross head
   across the structure. That is the native, author-intended comparand.
2. **Consistent with Pol.** In Pol's model r_e is a *blanket pore-pressure*
   quantity driving uplift/heave (Eq. (10)) — i.e. whether the blanket
   *ruptures*. Sellmeijer's static model has no blanket-uplift step; it assumes
   an existing unfiltered exit (a post-breach picture), for which Pol uses the
   raw head (Eq. (6)). So the static piping check — the same mechanism minus the
   time axis — should use the raw head too.
3. **Clean gap decomposition.** With both piping heads raw, r_e drops out of
   both, and the head-convention component of the static–transient gap
   (spec §12 fm4) returns to **exactly the 0.3·D_bl crack term** (transient
   only) — the spec's original FM4 framing — instead of a large r_e confound
   that would masquerade as a temporal effect (the FM4 error the spec warns
   against). The comparison isolates the temporal mechanism, as intended.
4. **Repo precedent.** Mirrors ADR-0017: keep the baseline symmetric; make any
   asymmetry an opt-in decomposition axis.

The fairness principle stated by the project owner: use Sellmeijer's model
exactly as Sellmeijer intended and Pol's model exactly as Pol intended, or the
static-vs-transient comparison is not a fair one.

## Decision

The static Sellmeijer comparator uses the **raw gross head across the
structure**:

    Z_static = H_c − (h_peak − z_toe)        (no r_e, no 0.3·D_bl)

`r_e` therefore drives **only** the transient uplift/heave gate (Eq. (10)); the
static branch is entirely r_e-independent. Both piping heads (static gross,
transient crack-reduced) are raw and differ by exactly `0.3·D_bl`.

## What is NOT changed

- **The `0.3·D_bl` crack term stays transient-only.** It is a Pol/TAW blanket
  addition (SIE Eq. (6)), not part of Sellmeijer 2011, so the static branch
  carries no crack reduction. The 0.3·D_bl difference is the legitimate,
  documented head-convention gap component.
- **Riverside-foreland partial attenuation is not modelled.** Physically the
  riverside foreland blanket still attenuates the seepage head even post-breach,
  but *neither* Sellmeijer *nor* Pol Eq. (6) resolves that partial effect (both
  use the full head). Raw-static inherits a simplification Pol already made; it
  introduces no new one. A partial-r_e schematization would deviate from both
  calibrations and is out of scope.

## Consequences

- **Static P_f rises (branch more conservative).** At damped sections the static
  load rises by ~1/r_e (KP 62.0 r_e≈0.33 → static load ~×3), so the static
  transition moves to a much lower stage. The static branch now matches the
  traditional Sellmeijer gross-head design check. Combined with ADR-0027 both
  branches use the raw piping head; the gap is temporal + 0.3·D_bl +
  H_eq-conservatism + (optional) dimensional. **Re-sweep required** to quantify
  (none run).
- **The static branch is r_e-independent.** `foreland_treatment` / open-entry
  (ADR-0025) and any r_e change no longer affect the static failure matrix
  (locked by `test_foreland_open_zeroes_entry_length_default_unchanged` and
  `test_foreland_treatment_threaded_and_recorded`, updated to assert static
  invariance and transient-only response). r_e is retained in
  `EvaluationResult` as a diagnostic.
- **ADR-0002 (shared sample) intent preserved.** Both branches still consume the
  same θ_j through one M8 call; the gap remains a same-sample comparison. The
  ADR-0002 phrasing "the same r_e feeds both" is now moot for the static branch
  (r_e simply does not enter it) — noted in the M8 docstring; the contract's
  purpose (same sample, one call, no independent tracks) is intact.
- **Toy test grids re-tuned.** `tests/test_run.py` `_GRID`/`_TOY_GRID` moved down
  to bracket the now-lower static transition (~6.5) alongside the transient
  (~9); the module comments record the new interior ranges.
- **Optional future axis.** If a "vs current damped-practice" comparison is
  wanted, add an opt-in `r_e`-on-static toggle (ADR-0017 pattern) to measure the
  head-convention/practice component — not built here.

## Code

- `bep_reliability_engine/evaluator.py`: both `evaluate_realization` and
  `evaluate_batch` static branches use `h_peak − z_toe`; docstrings updated
  (static is r_e-independent; the two piping heads differ by 0.3·D_bl only).
- No change to M4/M5/M6/M7, the transient branch, or the M8 signature.
- Tests: the head-convention M8 tests assert both heads raw differing by
  0.3·D_bl; the foreland tests assert static r_e-invariance; toy grids re-tuned.

## References

- Sellmeijer et al. (2011), "critical hydraulic head across structure" (symbol
  list; test §); `docs/references/sellmeijer_2011.pdf`.
- ADR-0027 (raw erosion head; this ADR is its static counterpart), ADR-0007
  (superseded), ADR-0002 (shared sample), ADR-0017 (opt-in-override precedent),
  ADR-0025 (foreland treatment — static now insensitive), ADR-0009 (gap
  components), spec §12 fm4.
- `docs/validation/pol-meeting-2026-07-07-dispositions.md`.
