# ADR-0006: Finite-Foreshore tanh Correction in the Baseline; the L/λ_in "Validity Monitor" Withdrawn as a Category Error (2026-07-05 Amendment)

Date: 2026-06-11 (amended 2026-07-05)
Status: Accepted (amended: Decision 2's L/λ_in diagnostic was a category error — corrected below with the citation trail re-anchored to the primary sources. The amendment did NOT itself close all r_e questions: the KP 62.0 foreland confinement was left open — see the Open Item section — and was resolved the same day by ADR-0025: blanketed baseline adopted, open-entry logged as an evidence-disfavored on-demand sensitivity.)

> **Note (2026-07-28), Decision 1 unchanged.** The tanh correction retained here
> was measured for the first time on 2026-07-28 (ADR-0025 amendment; companion
> `adr0025-foreshore-width-and-sensitivity.md`). Two facts a reader of this ADR
> should carry: (i) the correction is **saturated at every production section** —
> tanh credits are 0.835 (KP 62.0) and 0.969–1.000 elsewhere, and above
> B_f ≈ 2.5·λ_out the term is numerically indistinguishable from the
> semi-infinite limit; (ii) removing the foreland entirely (B_f → 0) moves
> transient P_f by ≤ 0.0044 at every section and static P_f by **exactly zero**
> (the latter is the expected ADR-0028 consequence and is asserted by the
> driver). Decision 1 stands — the term is correct, cheap, and the conservative
> choice — but it is not a load-bearing driver of the fragility deliverable, and
> should not be presented as one. The `foreshore_width_m` inputs it consumes
> were verified verbatim against the OYO 様式-3 高水敷幅 annotations on the same
> date.

## Context (amended)

The engine's response factor is the three-term ratio

    r_e = λ_in / (λ_out,eff + L + λ_in)

**Provenance, corrected against the primary sources (2026-07-04 source
analysis):** this is the **exact closed form** of USACE (2000) EM 1110-2-1913
Appendix B blanket theory — Case 7a, landside head factor x₃/(x₁ + L₂ + x₃)
with x₁ the effective foreland entry length (Eq. B-7), L₂ the **base width of
levee and berm** (App. B §e) and x₃ the effective hinterland exit length
(Eqs. B-3/B-5) — and of TAW (2004) Model 4A, where the total resistance is
"the sum of the resistances W_n = L_n/(kD) of the subregions foreland, dike
and hinterland" and the head is linear in the resistances. **Pol (2022)
thesis Eq. (7.13), r_e = λ/(L + λ) at the exit, is the special case with no
riverside blanket and an infinitely long polder blanket** ("equivalent to
case 7a from the USACE blanket theory or model 4A from Dutch guidelines",
thesis p. 158); Pol SIE 2024 (Eq. 10, Table: "Aquifer response r_e – 0.6 –
Det") and CG24 take r_e as a bare deterministic input. The original ADR text
attributed the three-term form to Pol Eq. (7.13) directly; that was
imprecise and is corrected here.

**The exactness statement, sharpened:** the ratio is exact **for any L**. L
(= USACE L₂) is the exact *linear* horizontal-resistance term of the sealed
under-levee segment; it sits in the plain sum x₁ + L₂ + x₃ and **is never
inside a tanh** in any of the source formulations. There is no "full
hyperbolic form in L/λ_in" to fall back to — that object does not exist in
the sources. The genuine finite-extent (hyperbolic) corrections act on the
**foreland extent** (x₁ = λ_out·tanh(B_f/λ_out), USACE Eq. B-7) and the
**hinterland extent** (x₃ = λ_in·tanh(L₃/λ_in) for a finite open exit,
Eq. B-5; x₃ = λ_in for L₃ = ∞, Eq. B-3).

Across the study reach, foreshore width varies fourteen-fold (44 m at KP 62.0
to 600 m at KP 60.0) and is the dominant source of cross-section
heterogeneity — the motivation for Decision 1, which stands unchanged.

## Decision

1. **Baseline finite-foreshore correction (unchanged from 2026-06-11).**
   Phase 1 applies the effective entry length λ_out,eff = λ_out ·
   tanh(B_f/λ_out), with B_f the foreshore width. Limits: B_f → ∞ recovers
   the semi-infinite λ_out; B_f → 0 gives λ_out,eff → 0, deriving (rather
   than asserting) the no-foreshore treatment. This is exactly USACE Eq. B-7
   / TR ZW 1999 Eq. (19) and handles all cross-sections uniformly.

2. **(Amended 2026-07-05; replaces the original Decision 2.)** The original
   Decision 2 instituted a per-realization **L/λ_in** "validity diagnostic"
   on the premise that the simple ratio required L ≪ λ_in. That premise was
   a **category error**: it compared the levee base width (the exact linear
   L₂ term, no smallness condition) against the hinterland leakage length,
   two quantities whose ratio gates nothing in the source formulations. The
   alarm it raised on the production configs ("median L/λ_in ≈ 1.23 at
   KP 62.0, 100% of realizations outside the small-L domain") is
   **withdrawn**; no r_e physics change follows from it, and the ratio form
   stays as built. The genuine validity conditions of the schematization
   are:
   - **foreland extent B_f/λ_out** — handled *in-model* by Decision 1's tanh
     correction;
   - **hinterland extent L₃/λ_in** — the semi-infinite assumption
     (x₃ = λ_in, matching Pol Eq. 7.13's "infinitely long polder blanket");
     L₃ is a site-data quantity, not an engine input, resolved per section
     below;
   - **quasi-static response** — the §11 τ_aq/T_flood diagnostic, unchanged.
   The wired monitor is **repurposed, not removed**: the run-level block now
   records the descriptive leakage geometry behind r_e — median λ_in and
   λ_out,eff, the foreland tanh credit, the median shares of the three
   denominator terms, the (descriptive, ungated) L/λ_in, and the hinterland
   assumption status with its 3·λ_in extent threshold — under
   ``metadata['leakage_geometry']``, warning about nothing.

## Hinterland extents L₃ — resolved per section (2026-07-05, HDB facility register)

The owner's site resolution (companion note
`adr0006-hinterland-l3-resolution.md`; primary source the Hokkaido
Development Bureau chainage-native facility register, right bank KP 53–66)
established, against the corrected-D_bl thresholds (λ_in = 102/117/87/39 m,
3·λ_in ≈ 307/350/262/116 m at KP 57.4/58.8/60.0/62.0):

| KP | Nearest registered landside boundary | Distance | Verdict |
|----|--------------------------------------|---------:|---------|
| 57.4 | 木賊原樋門 (sluice gate) @ KP 57.3 | ~100 m (< 1·λ_in) | **violated — open exit** |
| 58.8 | nearest gate ≥ 1.5 km | ≫ 3·λ_in | holds |
| 60.0 | nearest gate ≥ 0.8 km (平原大橋 is a bridge, not a boundary) | ≫ 3·λ_in | holds |
| 62.0 | 西士狩樋門 essentially AT KP 62.0 (+ 伏古樋門 @ 61.7) | ~0 m | **violated — open exit** (revises the earlier plan-view "holds") |

**Both violations are open exits (through-levee sluice gates draining
landside channels), so the semi-infinite assumption is CONSERVATIVE at every
section**: a finite-hinterland correction x₃ = λ_in·tanh(L₃/λ_in) would
*lower* r_e and *lower* P_f at KP 57.4 and KP 62.0. No reading of the
register makes the engine under-conservative on the landside. **Baseline:
retain semi-infinite x₃ = λ_in at all four sections** (matching Pol Eq.
7.13); the KP 57.4 and KP 62.0 open-exit boundaries are documented, bounded
conservatisms. **Residual (data-gated, optional, not a blocker):** the
register confirms gate locations but not channel-bed depth — the correction
applies only if the drainage genuinely daylights the Ag aquifer; a shallow
ditch leaves the confined condition intact. A finite-hinterland sensitivity
at KP 57.4/62.0 is warranted only if the bed elevations (帯広開発建設部)
confirm aquifer daylighting. Either way the baseline is safe-side.

## Open item — NOT closed by this amendment (resolved same-day by ADR-0025)

This amendment closes the citation trail, the L/λ_in category error, and the
hinterland extents (conservative). It does **not** close the **KP 62.0
foreland confinement**, which was at amendment time a live, potentially
**non-conservative** item: if the 44 m foreshore were effectively
unblanketed rather than the modeled leaky cover, r_e at the governing
section would rise from ≈ 0.33 toward ≈ 0.45 (+23–37% on the driving head).
That item was quantified, evidenced and dispositioned in **ADR-0025**
(accepted 2026-07-05, after the B-7/様式-5 read: blanketed baseline adopted;
open-entry logged as an evidence-disfavored, on-demand sensitivity via
``config.foreland_treatment``) and was deliberately kept out of this
documentation cleanup so the two could not be conflated.

## Consequences (amended)

- The monitored quantities for the hydraulic translation are **B_f/λ_out**
  (in-model, Decision 1), the **hinterland extents** (resolved above;
  conservative), and **τ_aq/T_flood** (§11). The former L/λ_in gate is
  withdrawn; `hydraulics.leakage_ratio_diagnostic` and its constants are
  removed, and the run-level record is `metadata['leakage_geometry']`
  (descriptive only). Runs persisted before 2026-07-05 carry the old
  `leakage_ratio_diagnostic` block, whose "flagged_fraction" should be
  disregarded.
- Test obligations: the tanh-limit checks of Decision 1 stand
  (`tests/test_hydraulics.py`); the repurposed record is pinned at the run
  level (`tests/test_run.py::test_leakage_geometry_recorded_without_warning`,
  which also proves the false alarm is gone); the two tests of the removed
  diagnostic are retired with it.
- No change to `response_factor`, `leakage_length_in`, `leakage_length_out`
  or any r_e physics arises from this amendment.

## References

Original (2026-06-11) references, re-verified 2026-07-04 with page/equation
numbers:
*   USACE EM 1110-2-1913 (2000), Appendix B: §e (L₂ = base width of levee
    and berm), Eq. B-3 (x₃ = 1/c = λ for L₃ = ∞), Eq. B-5
    (x₃ = tanh(cL₃)/c, finite open exit), Eq. B-7 (x₁ = tanh(cL₁)/c) —
    local copy `docs/references/USACE 2000.pdf` (gitignored).
*   TR Waterspanningen bij dijken (TAW, 2004), Bijlage 4, Model 4A/4B (sum
    of subregion resistances W_n = L_n/kD; dike segment linear) — local copy
    `docs/references/TAW 2004.pdf` (gitignored).
*   Pol (2022), doctoral thesis, Eq. (7.13), p. 158 ("equivalent to case 7a
    … or model 4A"; no riverside blanket, infinitely long polder blanket) —
    local copy `docs/references/pol_thesis_2022.pdf` (gitignored).
*   Pol SIE 2024, Eq. (10) and the stochastic-variable table (r_e = 0.6,
    deterministic input).
*   TR Zandmeevoerende Wellen (TAW, 1999), §4.4.1 Eq. (19):
    L'_v = λ₁·tanh(L_v/λ₁) (Decision 1's foreshore correction).
*   Companion notes: `adr0006-leakage-boundary-ratios.md` (leakage lengths
    and boundary ratios, corrected D_bl), `adr0006-hinterland-l3-resolution.md`
    (HDB facility register, per-section verdicts); ADR-0025 (KP 62.0
    foreland — resolved: blanketed baseline, open-entry logged sensitivity).
