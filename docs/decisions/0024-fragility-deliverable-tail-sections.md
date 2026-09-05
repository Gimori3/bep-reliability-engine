# ADR-0024: Per-Branch Fragility Deliverable — Raw Tail Points with Binomial CIs Where the Transition Is Not Bracketed

Date: 2026-07-03
Status: Accepted (decision and implementation mechanics approved by the author, 2026-07-03; execution of the implementation is scheduled and held with all r_e-dependent work pending the ADR-0006/Mazure resolution)

## Context

The 2026-07-03 health assessment (finding 1) and the follow-up grid probe
established that at KP 62.0 the transient fragility transition is physically
unreachable: P_f,transient reaches 0.5 only at ≈ 67 m MSL (N = 20,000,
stochastic L), which is ~15 m above the maximum peak stage produced by any of
the 8,400 d4PDF members at the KP 62.0 rating (51.47 m MSL) and ~19 m above
the design crest (47.89 m). The approved grid tops out at HWL + 4 m = 50.5 m,
where P_f,transient ≈ 1.0e-3 at N = 1e5.

Probe (KP 62.0, N = 20,000, stochastic L):

| level [m MSL] | 50.5 | 52 | 53.5 | 55 | 56.5 | 58 | 61 | 64 | 67 |
|---|---|---|---|---|---|---|---|---|---|
| P_f,static | .031 | .119 | .251 | .401 | **.543** | .661 | .819 | .909 | .954 |
| P_f,transient | .0009 | .0053 | .020 | .046 | .086 | .136 | .254 | .375 | **.486** |

A lognormal fitted to such a tail and quoted as a curve is an extrapolation
artifact: the retired ln(h) fit placed the transient median capacity at
56.6 m MSL, where the measured P_f is ≈ 0.09 — wrong by roughly a factor of
five in probability at the quoted median. (The datum-anchored weighted fit of
2026-07-03 extrapolates far better — median 65.6 m vs the probed ≈ 67 m — but
an extrapolated median 15 m past the data remains a statement about the fit,
not the site.) Separately, M9 currently *requires* a successful fit per
branch (`fit_lognormal_fragility` raises with fewer than two interior
points), so a branch with an empty or one-point tail can still abort assembly.

## Decision (author, 2026-07-03)

Sections whose transient (or static) transition is not bracketed by the
conditioning grid report **raw tail points with binomial confidence
intervals** as that branch's fragility deliverable, rather than a fitted
lognormal extrapolated far past the data. The fitted-lognormal deliverable is
unchanged at branches whose transition the grid brackets. A modest upward
grid extension is applied at KP 62.0 **only to bracket the static transition**
(~56 m MSL); no grid chases the transient transition.

**The anticipated primary result — not a fallback.** On the probe evidence,
the transient transition is expected to be unreachable across the attainable
stage range at all sections, in which case the primary transient deliverable
of Phase 1 is the raw exceedance probabilities with binomial CIs over that
range, reported against the static curve as **per-level probability ratios**
— and that is the intended presentation of the static-versus-transient bias,
not a degraded substitute for a median-capacity comparison. A transient
full-breach probability that stays low across all attainable stages is
itself a substantive finding for the thesis's central question: it means the
time-dependent mechanism shows the levees far safer against
through-progression than the static benchmark implies, because no attainable
flood lasts long enough to complete the pipe — a scientific result about the
temporal mechanism, not a fitting inconvenience.

## Implementation (mechanics approved 2026-07-03; execution held with the r_e resolution)

1. **Bracketing criterion (per branch, per section, data-driven).** A branch
   counts as *transition-bracketed* iff `max(P_f_raw) >= 0.5` on the grid —
   i.e. the median capacity lies inside the data. Computed in M9 from the raw
   point estimates; no external "attainable stage" input needed.

2. **Binomial CIs computed always, for every section.** M9 attaches
   Clopper–Pearson (exact) 95% intervals on the raw per-level point estimates
   of both branches, from the failure counts `k_i = P_f_i · N` (via
   `scipy.stats.beta`). New additive `FragilityResult` field
   `binomial_ci = {'static': (lo, hi), 'transient': (lo, hi)}`, persisted as
   HDF5 datasets alongside the bootstrap bands. Cheap, exact for rare-event
   counts, and useful at healthy sections too. (The existing bootstrap bands
   quantify uncertainty of the *fitted curve*; the binomial CIs quantify the
   *raw points* — complementary, both kept.)

3. **The fit becomes tolerant, closing the last post-sweep abort.**
   `P_f_static_fit` / `P_f_trans_fit` become `LognormFragility | None`:
   `None` when a branch has fewer than two interior points (today a raised
   `ValueError` that can still kill assembly after the sweep). Where the fit
   exists but the branch is unbracketed, the fit is still computed and stored
   — labelled extrapolative, not the deliverable. Persistence handles `None`
   in the datum-attr style (absent attrs → `None` on load; old files load
   unchanged). Bootstrap bands are computed only where the fit exists;
   raw-tail branches rely on the binomial CIs.

4. **Metadata flags the deliverable form per branch** (the coexistence
   mechanism the analysis layer reads):

   ```
   metadata['fragility_deliverable'] = {
     'static':    {form: 'fitted_lognormal' | 'raw_tail_binomial',
                   transition_bracketed: bool, max_p_f_raw: float},
     'transient': {...},
     'ci_method': 'clopper_pearson', 'ci_level': 0.95,
   }
   ```

5. **KP 62.0 grid extension (static bracketing only).** Extend the approved
   grid above 50.5 m in 0.5 m steps to 56.5 m MSL (12 added levels,
   N_h 26 → 38; the probe gives P_f,static ≈ 0.54 at 56.5). Emitted by
   `scripts/generate_configs.py`; drift guard updated to the new approved
   grid. The added levels are documented as fit-stabilizing hypothetical
   loads — they exceed the maximum attainable stage (51.5 m) and the crest
   (47.9 m), which is harmless in the fragility × hazard composition (the
   hazard carries zero weight there) **[Pointer added 2026-08-10: the
   parenthetical immediately above is superseded on the +4K hazard side — see
   the dated note at the end of this file. Nothing else in this item
   changes.]** but must not be plotted as attainable
   states.

6. **Anticipated classification** (decided by the criterion at sweep time,
   not hardcoded): static fitted at all four sections (KP 62.0 after the
   extension); transient raw-tail at KP 62.0 and, on the probe evidence,
   anticipated raw-tail at the other sections as well (KP 57.4's transient
   tops at ≈ 0.11 on its grid). Per the Decision above, that outcome is the
   anticipated **primary result**: the static–transient bias is then
   presented as per-level probability ratios with CIs over the attainable
   stage range — the intended headline comparison, with median-capacity
   shifts reported only where both branches are bracketed.

7. **Contract note.** The additive field and the `Optional` fits are a spec
   §2 contract change in the ADR-0017 precedent style: additive, pinned by
   interface tests, safe for Phase 2 (which reads by attribute and filters
   via the retained matrices, not the fitted curves). The raw matrices —
   the actual Phase 2 payload — are untouched.

## Alternatives considered

- **Extend the grid to bracket the transient transition (~67 m).** Rejected:
  conditioning levels ~15 m above anything the loading model can produce are
  physically meaningless, and the fitted curve there would describe the fit,
  not the levee.
- **Report the fitted lognormal everywhere with a warning label.** Rejected:
  the 56.6 m-vs-67 m error above is exactly the artifact the author's decision
  removes; a label does not stop a downstream reader integrating the curve.
- **A separate result type for tail sections.** Rejected: fragments the
  Phase 2 handoff; one `FragilityResult` with per-branch deliverable flags
  keeps a single artifact schema.

## References

- 2026-07-03 health assessment finding 1; the KP 62.0 grid probe and the
  full-N run (P_f table above; max ensemble stage 51.47 m MSL; crest
  47.89 m, ADR-0021 cross-check table).
- Spec §2 (FragilityResult contract), §11 (CoV target — recorded per run in
  `metadata['mc_convergence']` since 2026-07-03, and structurally unmeetable
  at tail-only branches, which this ADR's deliverable form acknowledges).
- ADR-0017 (precedent for additive contract changes), ADR-0022 (timestep
  acceptance; same health-assessment lineage).
- `bep_reliability_engine/fragility.py` (`fit_lognormal_fragility`,
  `assemble_fragility`, `_bootstrap_bands`, `mc_cov_of_pf`).

## Author caution (Pol, 2026-07-07)
Pol advised against over-investing in the low-P_f raw-tail framing: from a
practical standpoint extremely small failure probabilities carry little
meaningful information, so presenting them as a major substantive finding may be
unnecessary. This tempers the "intended primary presentation / substantive
finding" language of the Decision above; the binomial-CI / raw-tail machinery is
unaffected. Whether to soften the thesis emphasis is a decision from the author. NB: the
ADR-0027 change (raw erosion head) raises transient P_f and may make the KP 62.0
transition reachable, which would also bear on this framing — re-check on the
next sweep. See `docs/validation/pol-meeting-2026-07-07-dispositions.md`,
Answer 9.

## Dated note (2026-08-10): the hypothetical extension is NOT weightless on the +4K hazard side

**Status of this note:** a back-pointer and a factual correction to one
parenthetical. **The Decision above is unaffected** — raw tail points with
binomial CIs where the transition is not bracketed, and a static-bracketing grid
extension at KP 62.0, both stand exactly as decided. Nothing in Implementation
items 1 to 4, 6 or 7 is touched. What is corrected is a forward-looking
assertion inside Implementation item 5 about how those added levels would behave
once composed against a hazard — an assertion made on 2026-07-03, **ten days
before Phase 3 existed** (ADR-0038, 2026-07-13) and 26 days before the ADR-0047
KP 62.0 seepage-length adoption raised that section's transient fragility by
×8.7 at design HWL.

**The parenthetical that no longer holds.** Implementation item 5 says the added
levels "exceed the maximum attainable stage (51.5 m) and the crest (47.9 m),
which is harmless in the fragility x hazard composition (**the hazard carries
zero weight there**) but must not be plotted as attainable states." The final
clause stands and is if anything more important than when written. **The
parenthetical does not.**

**Measured (2026-08-10, from the committed Phase 3 hazard for KP 62.0; no sweep
re-run):**

| quantity | historical (3,000 yr) | +4K (5,400 yr) |
|---|---|---|
| highest ensemble peak stage | 48.78 m MSL | **51.47 m MSL** |
| years peaking above the attainable maximum, 50.5 m | 0 | **7 (0.13 %)** |
| years peaking above 51.0 m, the **first added level** | 0 | **4 (0.07 %)** |
| share of the section's annual piping probability they carry | 0.0 | **11.8 %** |

So under the +4K ensemble the hazard carries **non-zero** weight on the
hypothetical extension: four member-years land on or above the first added
level, and because the fragility is near saturation up there the seven
above-attainable years contribute about an eighth of KP 62.0's annual piping
probability. The historical ensemble does carry zero weight there, as item 5
assumed, and KP 57.4 carries exactly zero in both climates — the assumption was
correct for every case that existed when it was written.

**Why this is not a coverage-clamp problem, which is the point worth carrying.**
The HKV-audit diagnostics on `AnnualizedResult.coverage` detect peaks landing
*outside* the composition grid. Here nothing leaves the grid: the highest peak
is 51.47 m against a grid top of 56.5 m, so `lower_bound_clamp` and
`below_grid_unresolved` are correctly False in every KP 62.0 row. The exposure is
to the part of the grid that is *inside* it and physically unreachable, which
this ADR created deliberately and which no flag can see. **A clean coverage-flag
set is therefore not by itself a statement that an annualized number rests only
on attainable stages.** A consumer must read `coverage` together with the
section's attainable maximum.

**Where this is flagged in place.** Implementation item 5 carries a bracketed
pointer beside the superseded parenthetical, which is itself left standing
verbatim; that item is otherwise byte-identical to the 2026-07-03 text.

**What a reader of this ADR should do.** Treat 50.5 m MSL as KP 62.0's attainable
maximum (it is the last non-hypothetical conditioning level, pinned as
`attainable_max_m` in `scripts/stage6_6_gap_decomposition.py` and
`scripts/hwl_bias_resolution.py`), and where an annualized number is quoted for
that section under +4K, quote the 11.8 % exposure with it. The "must not be
plotted as attainable states" instruction is unchanged and unrelaxed.

**Provenance.** Surfaced by the conductivity-bracket annualisation companion,
`docs/decisions/conductivity-bracket-annualisation.md` section 2.5 and its
evidence JSON (`sections.KP 62.0.*.baseline.driving_stage_band`). Promoted to
`docs/phase3_report.md` **caveat 8 of section 8**, which is the standing caveat
list Phase 3 consumers are told to carry; that caveat and this note say the same
thing. The exposure is a property of the **production** deliverable and is
identical under every sensitivity arm of that study, so it changes no comparison
there.
