# OPEN validation item — head-datum r_e-on-erosion-head convention

Status: **OPEN — pending direct confirmation from Pol.**
Opened: 2026-07-07 (Stage 6 reference-anchor check).
Owner action required: confirm the convention with Pol; then close here.
Scope: modeling-convention question, **not** a code defect. No engine change
is authorized by this item; it records an unvalidated assumption.

## The precise open question

Is applying the response factor r_e to the **progression-driving** head — the
engine's

    H_erosion(t) = r_e · (h(t) − z_toe) − 0.3 · D_bl

— the intended field-application convention, versus Pol SIE 2024 Eq. (6) as
written,

    H = h − h_e − 0.3 · D_bl        (raw outer water level h, no r_e)

where Pol applies r_e **only** to the uplift/heave head via Eq. (10),
φ_it(t) = h_e + r_e·(h(t) − h_e)?

## Why it is OPEN (cannot be closed from the repo or the papers)

- **Print-confirmed (SIE 2024 p.4, read visually 2026-07-07):** Eq. (6) uses
  the raw outer water level h with no r_e; Eqs. (8)–(10) put r_e only on the
  uplift/heave head φ_it. The engine additionally applies r_e to the erosion
  head — the documented **ADR-0007** deviation.
- **Confirmed numerically:** engine H_erosion equals Eq. (6) **exactly at
  r_e = 1** (diff 0.000 m) and deviates by **exactly the r_e factor**
  otherwise (e.g. r_e = 0.6: −1.2 m at h = 3 m, −2.0 m at h = 5 m).
- **The self-reference is irremovable from the available sources.** The
  0.3·D_bl crack term appears **only** in the SIE field model, where
  r_e = 0.6; the calibration experiments that have r_e = 1 (B25-245, FPH)
  have **D_bl = 0** (no blanket, no crack term). So **no published
  configuration combines an active 0.3·D_bl term with the r_e = 1 case where
  the engine and Eq. (6) coincide.** A test against Eq. (6) "as written"
  shows the ADR-0007 deviation, not a validation; a test at r_e = 1 with a
  hand-typed `h − h_e − 0.3·D_bl` merely relocates the self-reference. **No
  fixture was built**, by design.

## What IS externally confirmed (so this item is narrowly scoped)

Against SIE 2024 Eq. (6) print, all confirmed and matching the engine:
- the crack coefficient **0.3** (`CRACK_RESISTANCE_FACTOR = 0.3`);
- the datum **h_e = polder level at the exit point** (`z_toe ≡ h_e`,
  ADR-0007);
- the composition **subtract 0.3·D_bl from the head difference** (after, not
  inside);
- the **uplift/heave** head is r_e-damped (Eq. 10), which the engine matches
  exactly.

The **only** unconfirmed element is whether r_e should also multiply the
erosion-head difference (h − h_e) before the 0.3·D_bl subtraction.

## The two positions

- **Engine / ADR-0007:** the head that drives flow toward the pipe is the
  head actually present in the aquifer at the exit, i.e. the r_e-attenuated
  aquifer head; Eq. (6) is written for Pol's r_e = 1 validation geometry
  where outer water acts directly on the aquifer, and field application
  composes Eq. (6) with the response-factor machinery (Eq. 10).
- **Pol SIE 2024 as written:** Eq. (6) uses the raw outer level for
  progression; r_e appears only in the uplift/heave limit states.

## Impact if the convention is wrong

If Pol confirms the raw-head convention for progression, the engine currently
**understates** the erosion-driving head by the factor r_e at every damped
section (r_e < 1), i.e. it is **conservative** on progression there (lower
H_erosion → slower dl/dt → lower transient P_f). At Tokachi the production
r_e values are ~0.33 (KP 62.0) to higher elsewhere, so the potential effect
on the transient branch is material and section-dependent. Direction is
toward conservatism, so it is not a safety risk, but it would change the
static-vs-transient gap decomposition (this is a head-convention component of
the gap, spec §12 fm4 / ADR-0007) and must be resolved before the gap is
finalized.

## Closure criteria

Close this item when **either**:
1. Pol confirms the r_e-translated erosion head is the intended field
   convention → record his confirmation here, mark CLOSED, cite it in
   ADR-0007; **or**
2. Pol indicates Eq. (6)'s raw head is intended for progression → this
   becomes a **DISCREPANCY**; open an ADR to supersede ADR-0007 and change
   the erosion-head composition (r_e removed from H_erosion; retained on
   uplift/heave), with re-validation of the affected transient results.

Until then this remains the **one unvalidated physics convention** in the
engine (alongside the separately-tracked B25-245 rate-magnitude and P3
timestep items).

## References

- SIE 2024 Eqs. (6), (8)–(10): `docs/references/pol_sie_2024.pdf` p.4
  (rendered/read 2026-07-07).
- ADR-0007 (`docs/decisions/0007-re-translated-erosion-head.md`) — the
  deviation this item questions.
- `docs/validation/reference-anchor-status.md` §4 — full Stage 6 disposition.
- Spec §12 failure mode 4 — head-convention component of the
  static-vs-transient gap.
