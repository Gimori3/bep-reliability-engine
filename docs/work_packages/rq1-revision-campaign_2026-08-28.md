# RQ1 revision campaign — plan of record (2026-08-28)

Owner instruction: resolve three supervisor criticisms of the RQ1 (static-vs-transient)
treatment in one complete pass — (1) replace probability-ratio comparisons with
reliability-index (beta) differences wherever feasible; (2) establish precisely what the
head-convention difference between the two models is, and add an equal-head-convention
comparison run alongside the as-published/as-practiced one; (3) deepen the fundamental
comparison of the two models where genuinely useful. End state: engine work committed and
pushed, thesis RQ1 text fully rewritten and integrated, net thesis length ~unchanged.

## 1. Findings of the investigation (before any new work)

### 1.1 The head-convention difference is exactly 0.3·D_bl, and nothing else — CONFIRMED

The owner's working hypothesis ("the 0.3×Cd factor") is confirmed, with precision the
engine already pins:

- Both piping driving heads are measured on the raw outer level against the same landside
  toe datum `z_toe`, and neither contains r_e (ADR-0027/0028). The static comparator head
  is `h_p − z_toe`; the transient erosion driver is `(h(t) − z_toe) − 0.3·D_bl`
  (Pol SIE 2024 Eq. 6). Both branches consume the identical single-source H_c.
- The two heads therefore differ by exactly the crack-resistance decrement `0.3·D_bl`
  (`progression.CRACK_RESISTANCE_FACTOR = 0.3`), pinned to rel=1e-12 by
  `tests/test_evaluator.py::test_head_convention_both_raw_differ_by_crack_term`.
- There is no residual head-convention difference: datum shared, r_e in neither, H_c
  single-source. The peak-vs-history distinction is the *temporal* axis, counted
  separately; the 0.9·H_c equilibrium end anchor is resistance-side, counted separately.
- Its measured effect: the C0−C1 ladder step accounts for 75 % (KP 62.0) and 97 %
  (KP 57.4) of the design-level probability gap (stage 6.6, ADR-0040), i.e. 0.135 m and
  0.240 m of head against total design driving heads of 1.49 m and 0.91 m.
- Provenance (to be verified verbatim from the PDFs by WP-E1 before the thesis states
  it): the 0.3·d term is **not** in Sellmeijer (2011); it is the Dutch assessment-rule
  reduction adopted into Pol's transient formulation via SIE 2024 Eq. (6). The thesis
  already cites `schweckendiek_2014, pol_sie_2024` for the practice; any further
  provenance citation must come from sources already in `references.bib` or be flagged
  to the owner — never invented, and `references.bib` is not edited without approval.

### 1.2 What already exists, and the one thing that does not

- A **crack-reduced static comparator (C1)** exists (stage 6.6) — the "Dutch practice"
  equal-convention comparison (both sides crack-reduced) — measured at N=1e5 and N=1e6
  at KP 57.4/62.0, and already quoted (thinly) in the thesis.
- A **crack-free (gross-head) transient** does **not** exist. ADR-0040 explicitly
  declined to build the hook. That is exactly the supervisors' requested experiment:
  remove the contested 0.3·d from the transient so both models run on the raw head.
- All production artifacts needed for the beta re-expression are on disk
  (`results/tokachi_*.h5`, `results/hwl_bias_resolution/ladder_*_n1000000.h5`,
  `results/stage6_6/*`).

### 1.3 Beta re-expression: verified arithmetic, and a genuine reframing

With β(h) = −Φ⁻¹(P_f(h)) per branch and Δβ = β_trans − β_static (paired, shared sample):

| Anchor | β_static | β_trans | Δβ | B (ratio) |
|---|---|---|---|---|
| KP 62.0 design 46.39 m (1e6) | +2.93 | +3.83 | **0.90** | 26.9 |
| KP 57.4 design 39.21 m (1e6) | +3.05 | ≥ 4.34 | **≥ 1.28** | ≥ 148 |
| KP 57.4 39.50 m (1e6) | +2.01 | +3.28 | **1.27** | 42.7 |
| KP 58.8 design (1e5) | −0.59 | +0.63 | **1.22** | 2.75 |
| KP 60.0 design (1e5) | −1.39 | +0.49 | **1.87** | 2.92 |
| KP 62.0 48.00 m | +0.14 | +1.28 | 1.14 | 4.4 |
| KP 62.0 50.50 m (top) | −2.14 | −0.50 | 1.65 | 1.4 |
| KP 57.4 43.25 m (top) | −3.43 | −1.80 | 1.63 | 1.04 |

Two consequences the rewrite must carry honestly rather than cosmetically:

1. **The section ordering reverses.** In ratio terms the tail sections (KP 57.4/62.0)
   carry the huge bias and the drained sections a modest 2.75/2.92; in Δβ terms the
   drained sections carry the *larger* shift (1.22/1.87 vs 0.90/≥1.28). The
   "four sections span a factor of fifty" framing collapses to a Δβ band of ~0.9 to 1.9.

   > **Correction, 2026-08-29 (claim-calibration pass).** The band is right; the
   > *reversal* is wrong, and it was wrong here before it reached the thesis. The
   > measured Δβ ordering is **KP 60.0 (1.87) > KP 57.4 (≥1.27) > KP 58.8 (1.22) >
   > KP 62.0 (0.90)** against the B ordering **KP 57.4 (≥148) > KP 62.0 (26.9) >
   > KP 60.0 (2.92) > KP 58.8 (2.75)**. KP 58.8's 1.22 is *below* KP 57.4's bound of
   > 1.27, so the drained sections do **not** both carry the larger shift and the
   > berm-only section outranks one of them. It is a **re-ordering, not a reversal**:
   > KP 62.0 falls from second to last, KP 60.0 rises from third to first, KP 57.4
   > slips only from first to second. Second, the top of the Δβ range is **not** a
   > bound: 1.87 at KP 60.0 is fully resolved, so "0.9 to at least 1.9" is wrong;
   > the "at least" attaches to the ratio (B ≥ 148) alone. Both errors were
   > propagated into the Summary and Chapters 6, 8 and 9 and corrected there on
   > 2026-08-29. No measured value changes; only the reading of the table in
   > `docs/rq1_beta_reexpression_2026-08-28.md` §2, which was and remains correct.
2. **The severity story changes.** B decays monotonically to ~1 at the top of the range;
   Δβ does not decay — it is roughly stage-uniform to mildly increasing. The "converge
   toward parity at extreme overload" claim is true of P_f and false of P_survival
   (at KP 62.0's top level: static survival 1.6 % vs transient 31 %). β sees both tails.
   The existing claim "conventional practice is most conservative exactly at design
   levels" is a ratio-space statement and must be re-scoped, not deleted.
   Lognormal intuition: for two fitted curves with medians m_s < m_t and dispersions
   σ_s ≈ σ_t, Δβ ≈ ln(m_t/m_s)/σ = constant; the stage variation of Δβ is the
   second-order dispersion difference. The metric-free stage offset between medians
   (0.74 to 1.49 m along the reach) already in the thesis stays the anchor description.

## 2. Decisions

- **D1 — β metric.** β(h) = −Φ⁻¹(P̂_f(h)); CIs by monotone mapping of the existing exact
  Clopper-Pearson intervals (no new statistical machinery, no new pre-registration
  pretence: the resolution criteria R1/R2 were registered on the ratio and are kept;
  β/Δβ is a monotone re-expression of the same estimates and intervals). Zero-failure
  levels give one-sided β bounds. P_f > 0.5 gives negative β — reported as such.
- **D2 — presentation.** Δβ leads every RQ1 comparison; the ratio B is retained
  parenthetically where it is load-bearing (pre-registered anchors, concrete
  "one in six hundred vs one in sixteen thousand" readings). Ladder components are
  additionally reported as additive Δβ steps (β telescopes additively along the ladder,
  which dissolves the current share-vs-factor tangle; shares of ΔP_f remain as
  secondary framing).
- **D3 — equal-head-convention run.** New opt-in knob `crack_resistance_factor`
  (Config-threaded, default None ⇒ 0.3 unchanged, dropped from `to_metadata()` when
  None — hash-preserving; ADR-0051). Value 0.0 gives the gross-head transient. Both
  progression backends. Static branch untouched by construction — verified bit-identical
  as a consistency gate. Runs: matrix reading, all four sections, N=1e5 full grid;
  plus N=1e6 design-level resolution at KP 57.4 and KP 62.0 on the same seed recipe as
  the existing 1e6 anchors. Bulk reading skipped on the ADR-0040 §4 precedent
  (degenerate at the stages where the head convention matters); stated, not silent.
- **D4 — both comparisons in the thesis.** Keep the as-published/as-practiced
  comparison (C0 headline + C1 practice variant) exactly as the deliverable it is; add
  the equal-convention comparison as a co-equal reading: gross-vs-gross (new run,
  supervisor-endorsed, contested term removed) corroborated by reduced-vs-reduced (C1,
  already measured). Expected and pre-registered (§4): the equal-convention gap is the
  gate + temporal remainder, ≈ the pure-duration factor (1 to ~6 where counts support
  it), i.e. Δβ ≈ 0.2 to 0.7 at quotable stages; if the measured values leave that
  band the discrepancy is investigated, not smoothed.
- **D5 — deeper fundamental comparison.** Carried by (a) the equal-convention run,
  (b) the β-space re-expression including the additive Δβ ladder, (c) the
  survival-probability reading at overload, (d) a sharpened statement of the crack
  term's provenance/contested status. No further comparison methods forced; the
  existing ladder/dimensional/H_eq/l_c machinery already covers the ground.
- **D6 — repos.** Engine: work on the current feature branch, commit + push to origin.
  Thesis: commit locally, **never push** (Overleaf mirror; owner reviews diffs and
  pushes back) — flagged in the close-out. No `.tex` in the engine repo; numbers reach
  the thesis via the brief of WP-A.

## 3. Work packages

- **WP-E1 (engine):** ADR-0051 + `crack_resistance_factor` knob + tests
  (default-off bit-identity, factor-0 head equality with static, metadata drop), the
  runs of D3 with nesting/Euler-flip diagnostics, crack-term provenance verification
  from the reference PDFs, companion study doc + evidence JSON.
- **WP-E2 (engine):** β re-expression analysis script + tables of record
  (per-level β/Δβ with mapped CIs for all 8 production strata, 1e6 anchors, ladder
  components as Δβ steps, C1-comparison in Δβ), extended to the WP-E1 artifacts when
  they land; regenerated/new figures (β axis on tail figure, Δβ-vs-stage, β-space
  waterfall, equal-convention comparison figure) in `docs/figures/` and copied to
  `msc-thesis/figures/`.
- **WP-A (integration):** consolidate E1+E2 outputs into a definitive thesis numbers
  brief; reconcile every superseded claim.
- **WP-W (thesis, two waves):** rewrite Ch 4 (metric definition; ladder table
  extension; crack-term provenance; equal-convention experiment), Ch 6 (design-level
  bias in Δβ; composition with Δβ steps; new equal-convention subsection; severity
  section rewritten under both metrics; synthesis), then propagate: Ch 1 (light),
  Ch 5 (epistemic-vs-statistical wording), Ch 8, Ch 9, Summary, nomenclature (β row).
  Net length ~constant: the share-vs-factor tangle, the ratio-decay prose and the
  superseded framings are compressed to pay for the additions. All msc-thesis style
  rules binding (no em dashes, ranges "X to Y", no ADR numbers in main body, no
  software content, labels preserved).
- **WP-V (verification):** consistency pass (style gates, cross-refs, number
  spot-checks against artifacts), docs-of-record updates (project_log, architecture and decision records,
  architecture reconciliation note), commits, engine push, close-out report.

## 4. Pre-registered expectations for the equal-convention run

1. Static branch bit-identical to production at every level (zero-channel claim).
2. Gross-head transient failure set nests inside the static set at every level up to
   Euler-flip rows (continuous-time argument unchanged; the sustained-peak limit of the
   gross-head transient is exactly C0 ∧ gate).
3. Equal-convention design-level factor at KP 62.0 in the range ~4 to 12 (the measured
   pure-duration column); at the drained sections ~1.5 to 3; Δβ_eq ≈ 0.2 to 0.7.
4. The equal-convention gap is more canonical-event-exposed than the production gap
   (its head-convention floor is gone); stated as a conditionality, with the existing
   alternate-member measurement cited for direction.

Deviation from any of these is a finding to be run down, not adjusted away.
