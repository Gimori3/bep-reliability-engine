# Phase 2 Report: Bayesian Reliability Updating Against the 2016 Survival

Status: written 2026-07-12, at the close of the one-shot Phase 2 build;
**production addendum added 2026-07-13 (section 11)** — the full N = 1e5
campaign across all 8 strata has now run, every verification exact.
Sections 1-10 are preserved as the build-time record; where the self-test
numbers (N = 4000) and production numbers differ, **section 11 is
authoritative**.
Companions: ADR-0034 (Phase 1 surface extensions), ADR-0035 (observed-event
ingestion), ADR-0036 (updating architecture), the package README
(`bayesian_reliability_updating/README.md`), and the operational Phase 1
contract (`docs/phase2_interface.md`).

---

## 1. Executive summary

The complete Phase 2 framework is built, tested and importable:
`bayesian_reliability_updating`, ten modules, 44 dedicated tests (398
passing across both phases), one documented command against future
production sweeps. The 2016 event data drop contained everything needed
(the section 6 stop condition did not trigger): hourly observed stage at
the Obihiro gauge through the full four-typhoon window, plus the
September 2016 flood-trace survey giving field-surveyed peak levels at
every study KP. The self-test at N = 4000 on the two reachable sections
produced a physically coherent update with three headline findings:

1. **The transient model is comfortably consistent with the 2016
   survival.** The no-breach criterion rejects 5.2 percent of the prior
   at KP 58.8 and 3.3 percent at KP 60.0. The rejection concentrates
   overwhelmingly in the fast-progression corner (the top prior decile of
   C_e times k_aq is rejected at 6.0 to 8.0 times the overall rate), and
   the posterior C_e mean drops 4.0 and 3.6 percent: the
   laminar-conservatism signature the thesis predicted, measurable
   already at small N.
2. **The marginal transient informativeness of the 2016 survival is
   zero at both sections**: every transient-rejected row is also
   static-rejected (the transient failure set is nested inside the
   static one under this loading). The discrimination question of spec
   section 8 therefore resolves in the direction opposite to the
   headline-grabbing one: the 2016 survival does not constrain the
   progression mechanism beyond what peak-head resistance already
   implies. What the survival DOES discredit is the static comparator's
   absolute calibration: 58 and 74 percent of the prior "fails" the
   static Sellmeijer check at a peak the levees demonstrably survived,
   consistent with the Japanese validation campaign's static-conservative
   4-of-4 verdict.
3. **The full-transient replay is load-bearing, not cosmetic.** Reading
   the survival constraint off the Phase 1 fragility curve at the
   observed peak level (the peak-based practice of WBI+, Zethof et al.
   2023 appendix C) would reject 16.5 and 13.2 percent, a factor of 3.2
   to 4.0 more than the true replay. The 2016 event was much less
   erosive than the canonical d4PDF shape scaled to the same peak (6 to
   31 hours above the toe versus the canonical compound event's longer
   exposure), and only the time-resolved replay sees that.

The masked-matrix and re-evaluation posterior-fragility paths agree
EXACTLY (zero flag mismatches over 3793 x 29 and 3868 x 30
row-level re-evaluations) on the real d4PDF path, closing the strongest
available integrity loop over the whole chain.

---

## 2. Data inventory and classification (stop-condition assessment)

`data/digitized/2016_event_data/` (188 MB, now gitignored; compact
extracts committed under `data/processed/2016_event/`) was inventoried
exhaustively on 2026-07-12:

**Relevant to constructing h_2016(t)** (extracted):

| Source | Content | Use |
|---|---|---|
| `36_2016.8.20-8.31/観測所水位・流量データ/H_Q_2016.8.20-8.31.xlsx` | Hourly observed stage and published discharge, 30 stations, August and September 2016 | The loading time series (Obihiro gauge) |
| `36_2016.8.20-8.31/洪水痕跡水位/H28_kon.xlsx` | September 2016 post-flood trace survey: left/right levee peak elevations at 0.2 km spacing, plus design HWL, all rivers | Per-section peak anchors and datum cross-checks |

**Context-only** (inventoried, not extracted):

| Source | Content | Why not needed |
|---|---|---|
| `水位流量（HQ式）/` (4 workbooks) | Flow-capacity diagrams, H28 end-of-year channel | The engine's rating source stays the Phase 1 `HQrelation_*Riv_2017.csv` files (ADR-0019 section 5), keeping Phase 2 on the identical conversion |
| `計算データ/` (1019 files) | Non-uniform flow model runs (4 rivers, pre/post 2016 works), incl. solver executables | Model outputs, not observations; the trace survey supersedes them as the local peak evidence |
| `計算条件/`, rainfall and radar workbooks, dam operation records | Boundary conditions and meteorology | Not stage observations at the study reach |

**Stop condition**: NOT triggered. The essential per-segment stage time
series is constructible (one mainstem gauge inside the study band plus a
trace survey at every study KP); the build proceeded.

**Known source anomalies** (documented in the extract README):

- The September stage sheet (`時刻水位201609`) is a corrupted duplicate
  of the September discharge sheet. September stage is unavailable; the
  window therefore ends 2016-09-01T00:00. This is proven harmless: the
  window-end stage sits 0.43 to 2.06 m BELOW every section's landside
  toe (last toe exceedance 5.6 to 7.4 hours before the window end), and
  below the toe the ADR-0027 erosion head is negative and progression is
  identically zero.
- The Kumaushi stage column is the closed-station sentinel throughout;
  the loader treats gaps as loud errors, never interpolation.
- The pre-typhoon low-flow stage sits up to 0.82 m below the 2017
  flood-rating datum (the rating has no low-flow validity); such samples
  invert to zero discharge, with a 2.0 m excursion guard against genuine
  datum errors.

**Datum evidence** (all three checks pass, see the extract README): the
low-flow stage sits just above the KP 56.6 rating datum term; the
observed peak (38.07 m, 2016-08-31T04:00) sits 0.07 m below the 38.14 m
MSL design HWL matching the ADR-0019 record; the trace table's design-HWL
column reproduces the config HWL values exactly (41.03 m at KP 58.8).

---

## 3. Gauge assignment and the construction of h_2016(t) (ADR-0035)

One reference gauge serves all four study sections: Obihiro (帯広),
Tokachi KP 56.6, the ADR-0019 validation-anchor station, 0.8 to 5.4 km
downstream of the sections with no major tributary in between. This
mirrors the Phase 1 d4PDF band structure exactly (the KP 056.20 to 061.80
band carries one discharge series for the whole reach; the gauge sits
inside it).

Construction per section: (1) invert the observed gauge stage through
the gauge's own Eq. 4.19 rating (exact at the gauge by construction);
(2) re-rate at the section's own KP through the verbatim M3 path;
(3) anchor the peak to the surveyed right-bank flood trace at the section
KP by the same stage-domain amplitude rule the Phase 1 conditioning sweep
uses (trough floor pinned at the translated base-flow stage). Step 3
exists because the 2017 rating and the observed 2016 stage-discharge
pairs disagree by up to ~1.1 m at the peak (post-flood channel change and
loop-rating effects); the surveyed trace is the strongest local
observation of what actually occurred at the levee line. The unanchored
translation stays available as a sensitivity (`--anchor rating`).

| KP | z_toe [m MSL] | 2016 peak (trace) [m MSL] | rating-only peak | design HWL | hours at or above toe |
|---|---|---|---|---|---|
| 57.4 | 38.30 | 39.658 | 39.230 | 39.21 | 9 |
| 58.8 | 38.50 | 40.750 | 40.992 | 41.03 | 24 |
| 60.0 | 40.00 | 42.296 | 41.817 | 42.75 | 31 |
| 62.0 | 44.90 | 45.729 | 46.886 | 46.39 | 6 |

The full August window is used verbatim: all four typhoon peaks
(numbers 7, 11, 9 and the decisive number 10 with its 2016-08-31T04:00
crest), the inter-peak troughs, no smoothing, no clipping, no
rescaling to conditioning levels. The loader is fully reusable: a 2011
event drops in as a new `ObservedEventSource` over its own extracts.

---

## 4. Mathematical formulation and its justification

**Against Schweckendiek (2014).** The update is the direct method of
section 4.2.2: P(F | epsilon) = P(F and epsilon) / P(epsilon)
(Eq. 4.10), with survival as inequality information (section 4.2.3,
Eq. 4.12). The evidence is epsilon = {Z_transient(h_2016(t), theta) > 0}
evaluated by the same solver that defines the failure model, so the
observation function and the limit state are one physics (his h(x) and
g(x) share the model). The Monte Carlo realization is exact for
indicator evidence: accepted rows ARE the posterior sample, and posterior
failure probabilities are failure fractions among accepted rows.
Section 4.2.2's caution that updating introduces or changes correlations
is honored structurally (rejection is joint, on full 7-tuples including
C_e; mission invariant 2) and reported explicitly: the 2016 constraint
induces a Spearman shift of -0.05 between k_aq and C_e at KP 58.8
(negative dependence: surviving rows cannot have both large), which any
downstream use of posterior marginals as independents would silently
discard. His boundary-case footnote (P(epsilon) = 0 makes the update
undefined) maps to the all-rejected guard, which raises rather than
emitting an empty posterior.

**Against Zethof et al. (2023).** Appendix C gives the WBI+ closed form
for updating a fragility curve by a survived PEAK level: truncate and
renormalize the critical-level CDF below h_obs. That practice exists
precisely because complex limit-state models make full re-evaluation
expensive; the thesis commits to bypassing it because the BEP mechanism
is time-dependent, and the 1D ODE solver makes the full transient replay
affordable. The self-test turned this from a methodological preference
into a measurement: the peak-based reading of the constraint would
reject 3.2 to 4.0 times too many realizations at the study sections
(section 6.3 below). One WBI+ result transfers unchanged: survival
updating can only lower the failure probability, and both posterior
branches sit at or below their priors at every conditioning level, as
they must.

**The criterion.** Accept row j iff Z_transient(h_2016(t), theta_j) > 0
with l_ini = 0 and r_l = 0; the boundary Z = 0 counts as failure
(ADR-0008), so survival is the strict complement of the retained flag.
The stricter documented variant (`no_breach_no_initiation`, OFF by
default) additionally rejects rows whose uplift-plus-heave gate latched
under h_2016, reflecting the committee-documented absence of sand boils;
its caveats (the M5 gate models blanket initiation, not boil visibility;
reach-scale survey; deliberately conservative Terzaghi collapse) are in
ADR-0036 and keep it a sensitivity, not the baseline.

---

## 5. Architectural decisions (full list in ADR-0034/0035/0036)

1. **Zero physics reimplementation.** All evaluation goes through the
   Phase 1 M8 batch twin `evaluate_batch_diagnostics` (ADR-0034: the one
   batch implementation, delegation from `evaluate_batch`, row-wise bit
   identity with the frozen scalar API pinned by test) and the scalar
   `evaluate_realization` for trajectory tracing.
2. **Identical-assumptions replay, provenance-verified.** Config rebuilt
   from the snapshot and hash-checked; theta regenerated bit for bit
   through M2 (refused otherwise); stochastic L regenerated through the
   public ADR-0034 seam so L_j pairs with theta_j exactly; every
   deterministic setting threaded from the snapshot; MSL datum guard
   before any evaluation.
3. **Replay timestep 225 s** (the run's own ADR-0030 grid), superseding
   ADR-0022 decision 2 (1800 s): the Euler H_eq overshoot is a per-row
   artifact and per-row is exactly what an Accept-Reject filter
   adjudicates.
4. **Masked-matrix posterior fragility by default** (mission invariant
   7): posterior curves are failure fractions among accepted rows of the
   RETAINED matrices; the optional verification mode re-evaluates
   accepted rows on the run's own conditioning records and requires
   bit-exact agreement. Uncertainty mirrors ADR-0024 (Clopper-Pearson at
   n_accepted, bootstrap bands, Optional M9 fits).
5. **Sequential composition as masks over original rows**: replays
   evaluate all N rows per event and masks AND together, making
   A-then-B equal B-then-A equal the joint filter as an array identity
   (pinned by test) while keeping per-event decompositions reportable
   against the full prior. Each event replays from a virgin blanket
   (independent constraints; cross-event pipe memory deliberately out of
   scope per the Pol recovery evidence).
6. **Scale-aware posterior-size diagnostics**: warning below 50 percent
   of the prior (the spec section 11 CoV headroom argument), error-level
   collapse diagnostic below min(1000 rows, 1 percent of N); near-zero
   rejection at drained segments is correct behavior and silent.
7. **Persistence**: one `PosteriorResult` per Phase 1 file (= per
   segment per scenario per d70 interpretation), HDF5 + JSON sidecar, no
   pickle, carrying the full provenance chain (Phase 1 file SHA-256s,
   config hash, seeds, package versions, event chain with construction
   provenance, decomposition, marginal summary, warnings).

---

## 6. Self-test results (N = 4000, KP 58.8 and KP 60.0, matrix, historical)

Generated by `scripts/run_phase2_selftest.py` (genuine production
configs at reduced N through the real Phase 1 engine; outputs and the
figure set under `results/phase2_selftest/`; raw numbers in
`selftest_summary.json`).

### 6.1 Headline numbers

| Quantity | KP 58.8 | KP 60.0 |
|---|---|---|
| Prior rows N | 4000 | 4000 |
| Accepted (no-breach) | 3793 | 3868 |
| Transient rejection | 5.2% | 3.3% |
| Static rejection (same replay) | 58.1% | 73.8% |
| Marginal transient rejection (survives static, fails transient) | 0.0% | 0.0% |
| Fails static, survives transient | 52.9% | 70.5% |
| Posterior C_e mean shift | -4.0% | -3.6% |
| Posterior k_aq mean shift | -4.1% | -3.1% |
| All other parameter mean shifts | under 1% | under 1% |
| Top C_e x k_aq decile rejection | 30.8% | 26.5% |
| Rejection concentration ratio | 5.9 | 8.0 |
| Induced Spearman shift (k_aq, C_e) | -0.050 | -0.046 |
| Re-evaluation verification | exact | exact |
| Phase 2 runtime (incl. verification, tracing, figures) | 20 s | 19 s |

### 6.2 The survival-discrimination decomposition, read carefully

The two-by-two is dominated by its off-diagonal static-only cell. Three
statements, in decreasing order of strength:

1. The transient failure set is NESTED inside the static one here
   (marginal transient rejection identically zero at both sections, 4000
   rows each). Structurally this is expected under long-duration
   loading: the transient breach requires the erosion head to clear the
   H_eq barrier, whose ceiling is 0.9 H_c, while the static criterion
   compares the peak head against H_c itself with the two heads
   differing only by the 0.3 D_bl crack term; a row that outruns H_eq
   over 24 hours above the toe essentially always also exceeds the
   static threshold at peak. The thesis's marginal-informativeness
   question (spec section 8) is therefore answered honestly: at these
   sections and this loading, 2016 survival adds NO rejection beyond the
   static criterion, and the prior-to-posterior shift must not be
   presented as confirmation of the time-dependent mechanism alone.
2. What the transient criterion does carry is the CALIBRATION of the
   rejection: 5.2 percent (transient) versus 58.1 percent (static) at
   KP 58.8. Taken as a predictive model of the observed event, the
   static comparator asserts that most of the prior should have failed
   at a load the levee survived; the transient model asserts a small
   tail should have. Survival evidence therefore discredits the static
   comparator's absolute level while remaining comfortably consistent
   with the transient one, in line with the validation campaign's
   static-conservative 4-of-4 verdict and the ADR-0009 gap analysis.
   (Formally, updating BY the static criterion would also be valid
   Bayesian conditioning; it would simply be conditioning a model
   already known to be miscalibrated in absolute terms, and the thesis
   deliberately updates through the transient limit state.)
3. The rejected 5.2 percent are the genuinely informative rows: their
   breach times cluster on the final (typhoon 10) rising limb and crest
   (figure `*_breach_times.png`), they occupy the fast corner of the
   prior (top C_e times k_aq decile rejected at 6 to 8 times the overall
   rate), and their removal shifts C_e and k_aq down by 3 to 4 percent
   each while every other marginal moves under 1 percent. The update
   acts exactly where the physics says the 2016 evidence has power, and
   nowhere else.

### 6.3 The shape effect: why the full transient replay matters

Interpolating the Phase 1 prior transient fragility at the observed peak
gives P_f = 16.5 percent (KP 58.8) and 13.2 percent (KP 60.0); the true
replay rejects 5.2 and 3.3 percent. The Phase 1 curves condition on the
canonical d4PDF compound shape scaled to each level, and that shape
carries far more above-toe exposure than the real 2016 event did at the
same peak. A peak-based survival update (the WBI+ shortcut) would
therefore have over-rejected by a factor of 3.2 to 4.0, biasing the
posterior unsafe. This measured factor is the quantitative justification
for the thesis's methodological commitment to the time-resolved
constraint.

### 6.4 Figures (under `results/phase2_selftest/figures/`)

Per section: `*_marginals.png` (seven prior/posterior marginals, C_e
called out with mean lines), `*_fragility_update.png` (prior versus
posterior, both branches, CP CIs and bootstrap bands, toe and 2016-peak
markers; the posterior peels away from the prior exactly around the
survived level and reconverges above it), `*_decomposition.png` (the
two-by-two), `*_rejection_scatter.png` (accept/reject in the k_aq x C_e
plane), `*_record.png` (the constructed h_2016 with toe and trace
markers), `*_breach_times.png` (when the rejected rows breach, against
the stage record).

---

## 7. Section 4 invariants, self-checked

1. Zero physics reimplementation: all evaluation through M8
   (`evaluate_batch_diagnostics` / `evaluate_realization`); the one
   Phase 1 change is additive, surgical, ADR-documented (ADR-0034), and
   the full Phase 1 suite is green. VERIFIED (grep: no Sellmeijer
   factors, Mazure lengths or Pol ODE terms exist in the Phase 2
   package).
2. Row-wise joint rejection on full 7-tuples including C_e; no
   per-parameter rejection anywhere. VERIFIED (filtering operates only
   on whole-row masks).
3. Baseline criterion Z_transient > 0, l_ini = 0, r_l = 0, observed
   hydrograph used as-is (never rescaled to conditioning levels; the
   ADR-0035 trace anchoring is part of constructing the local observed
   record, not a scaling of the constraint). VERIFIED (pinned by
   acceptance-logic tests).
4. Static verdict recorded for every realization in the same M8 call;
   both masks retained and persisted. VERIFIED.
5. Trajectory diagnostics for the 2016 replay: terminal pipe lengths
   retained for all rows, breach times traced for all rejected rows via
   the scalar M8 with `store_trajectory=True`. VERIFIED.
6. Decomposition reported per segment stratum with (a), (b), (c);
   the marginal set (c) is a first-class output (its own cell, figure
   bar, and headline row). VERIFIED.
7. Posterior fragility computable without re-running the grid
   (masked-matrix default); full re-evaluation implemented as the
   verification mode and confirmed to agree EXACTLY on both stub and
   real paths. VERIFIED.
8. Mandatory diagnostics: rejection fraction, posterior size, and the
   justified warning thresholds (ADR-0036 section 7). VERIFIED.
9. Stricter no-initiation variant behind a flag, disabled by default,
   caveats documented. VERIFIED.
10. Repository conventions: no em dashes in the documents produced,
    ranges written as "X to Y", ruff/black/pytest green, ADR template
    followed. VERIFIED.

---

## 8. Known limitations

1. **Construction uncertainty of h_2016.** The trace anchoring absorbs
   the rating bias at the peak, but intermediate peaks scale with the
   same amplitude factor and the trace itself carries survey uncertainty
   (order 0.1 m) plus wind/wave setup ambiguity. The `--anchor rating`
   sensitivity bounds the construction's effect; at KP 62.0 (the largest
   anchor correction, -1.16 m) the sensitivity is worth running once
   production results exist.
2. **Single-gauge temporal structure.** All sections inherit the Obihiro
   timing; hysteresis and tributary timing differences along the 5.4 km
   are not represented. Given 0.2 km rating spacing and no major
   tributary inside the reach, this is second order against the anchor
   uncertainty.
3. **Zero marginal transient rejection limits what 2016 alone can say
   about progression.** The 2016 constraint tightens the fast tail of
   C_e times k_aq but cannot, by itself, separate progression-time
   explanations from static-resistance explanations of survival (that
   separation is exactly what the decomposition now quantifies rather
   than assumes).
4. **Small-N self-test.** 5.2 percent rejection at N = 4000 is 207 rows;
   marginal-shift estimates carry sampling noise of order 1 percent.
   Production N = 1e5 shrinks this by a factor of 5.
5. **The initiation variant's observational basis** (no sand boils) is
   reach-scale, not per-section; it stays a sensitivity.
6. **Survival evidence is treated as certain.** No likelihood softening
   for the possibility of unobserved distress; with the committee report
   explicit about the study reaches, this is the thesis's stated
   position.

---

## 9. Production checklist (once the Stage 7 sweep exists)

1. Run the sweep (`scripts/run_sweep.py configs/kp*_matrix.yaml` and the
   bulk variants) to produce the eight production FragilityResults, plus
   the registered KP 58.8 r_e-halved QA member (ADR-0032 scope).
2. One command per file set:
   `python -m bayesian_reliability_updating results/*_historical_*.h5 --verify`
   (add `--backend numba` for the ~4x replay speedup if the accel extra
   is installed; expect minutes per section at N = 1e5, dominated by the
   replay, the breach tracing and the verification sweep).
3. Run the two documented sensitivities once: `--anchor rating`
   (construction) and `--criterion no_breach_no_initiation` (evidence
   strength), and report them next to the baseline.
4. Tabulate the decomposition across the eight strata (segment x d70
   interpretation; remediation_state per file) per spec section 8; the
   `analysis` blocks of the sidecars carry everything needed.
5. Confirm the posterior-size diagnostics stay silent (expected:
   rejection well under 20 percent everywhere based on the self-test;
   drained sections near zero, which is correct behavior).
6. Hand the posterior transient curves (fits where bracketed, raw points
   with CIs in the tails, per ADR-0024 semantics) to the Phase 3
   series-system integration; the `PosteriorResult` sidecar's
   `posterior_fragility` block plus the HDF5 curves are the interface.
7. If the thesis text quotes the marginal-informativeness finding,
   re-verify the zero at production N (a nonzero but tiny marginal cell
   may appear at N = 1e5; its size IS the answer, either way).

## 10. THE 2011 FLAG: a second sequential survival constraint

**Assessment: moderately valuable, worth requesting, not blocking.**

The architecture is sequential-ready today (section 5, decision 5): a
2011 event is one `ObservedEventSource` over its own extracts plus one
extra record in `event_records`; masks compose exactly and the
PosteriorResult already persists per-event arrays and the chain.

What 2011 would add scientifically: the 2016 constraint acts at one
point of the severity spectrum, and its rejection region is the fast
corner ABOVE the 2016 exposure. A second survived event with a LOWER
peak but potentially LONGER above-toe duration would cut a differently
shaped region (slow-but-persistent progression rows that 2016's short
exposure spared). The measured shape effect (section 6.3, factor 3 to 4)
shows exactly this axis matters, so the value of 2011 hinges on its
duration structure, not its peak. If the September 2011 flood at
Obihiro was a broad low event, its marginal rejection beyond 2016 could
be non-trivial; if it was a smaller spike, it will add essentially
nothing (its rejection set will nest inside 2016's).

What the user must supply to run it (in order of importance):

1. Hourly observed stage at the Obihiro gauge for the 2011 event window
   (roughly 2011-08-25 to 2011-09-20 to bracket the early-September
   flood), same workbook family as the 2016 drop.
2. Confirmation of the survival observation itself for the study
   reaches in 2011 (no breach; ideally also the boil/no-boil record if
   the stricter criterion is ever to be used on it).
3. If available, a 2011 flood-mark or maximum-stage record at or near
   the study KPs (an H23 trace survey analog). Without it the
   construction runs with `anchor='rating'` and the anchoring
   uncertainty must be carried explicitly, which weakens but does not
   invalidate the constraint.

Recommendation: request items 1 and 2 now; run 2011 as a sequential
second event when they arrive; do not delay the production Phase 2
campaign for it. The 2016-only posterior is complete and defensible on
its own.

---

## 11. PRODUCTION CAMPAIGN ADDENDUM (2026-07-13; authoritative where it differs from sections 1 to 10)

The section 9 checklist has been executed in full: the 8 production
sweeps exist (4 sections x matrix/bulk, N = 1e5, 225 s grid), the Phase 2
update ran on all 8 with `--verify`, and both documented sensitivities
ran on the 4 matrix members. **Every masked-vs-reevaluation verification
was EXACT** (zero flag mismatches over 1e5 rows x 23 to 38 levels per
file). Artifacts: `results/phase2/` (baseline),
`results/phase2_anchor_rating/`, `results/phase2_no_initiation/`.

### 11.1 Baseline (trace-anchored, no-breach), all 8 strata

| Stratum | Transient rej. | Static rej. | Marginal transient | Static-only | Top C_e x k_aq decile rej. | Concentration |
|---|---|---|---|---|---|---|
| KP57.4 matrix | 0.07% | 6.26% | **0.000** | 6.19% | 0.58% | 8.9 |
| KP58.8 matrix | 5.67% | 57.63% | **0.000** | 51.96% | 30.19% | 5.3 |
| KP60.0 matrix | 3.36% | 73.31% | **0.000** | 69.95% | 25.97% | 7.7 |
| KP62.0 matrix | 0.00% | 0.00% | **0.000** | 0.00% | 0.00% | n/a |
| KP57.4 bulk | 0.00% | 0.00% | 0.000 | 0.00% | — | n/a |
| KP58.8 bulk | 0.00% | 0.00% | 0.000 | 0.00% | — | n/a |
| KP60.0 bulk | 0.02% | 1.84% | 0.000 | 1.82% | 0.22% | 9.6 |
| KP62.0 bulk | 0.00% | 0.00% | 0.000 | 0.00% | — | n/a |

Posterior marginal shifts at the informative sections: C_e mean -4.1%
(KP58.8) / -3.7% (KP60.0), k_aq -4.2% / -3.0%, every other parameter
under 1%, induced Spearman(k_aq, C_e) -0.052 / -0.047. C_e headline at
KP58.8: prior mean 0.0550 -> posterior 0.0528 (ratio 0.959).

**The section 9.7 question is answered: the marginal transient rejection
is EXACTLY ZERO at N = 1e5 in every stratum.** The transient failure set
is nested inside the static one under the real 2016 loading at
production resolution; the self-test finding was not a small-N artifact.

**Shape effect at production N** (prior transient curve at the observed
peak vs the replay rejection): KP58.8 15.6% vs 5.67% (factor 2.75),
KP60.0 13.1% vs 3.36% (factor 3.90), KP57.4 0.48% vs 0.07% (factor
7.5, small-number regime). The WBI+ peak shortcut remains biased unsafe
by a factor of roughly 3 to 4 where the update is informative.

### 11.2 Where the information landed (and the tiering caveat)

The bulk-d70 strata are essentially uninformative (the bulk
interpretation is the resistant reading; nothing approaches failure under
the 2016 loading), and the matrix updates land at **KP58.8 and KP60.0 —
the drained sections — while KP62.0 (unreinforced, the thesis's
governing live-BEP section) and KP57.4 receive (near-)vacuous updates.**
KP62.0's transition sits ~4 m above any attainable stage (ADR-0031), so
2016 could not reject anything there; that is a *finding about where the
2016 evidence has power*, not a defect. The caveat to carry into the
thesis text: the engine evaluates the **unremediated foundation**
everywhere — `remediation_state` is a provenance label, drains are not
modeled — so the thesis's statement that the drained sections' "exit head
is set to zero and the prior BEP probability is already near zero"
describes an intended presentation-layer tiering, not the computed
posterior in these files. The engine posteriors at KP58.8/60.0 are the
as-if-undrained constraint; the drain credit is a separate argument.

### 11.3 Sensitivities (matrix members)

**Anchor (`--anchor rating`, construction sensitivity):** KP57.4
0.07% -> 0.00%, KP58.8 5.67% -> 10.81% (rating peak 40.99 m vs trace
40.75 m), KP60.0 3.36% -> 0.34%, KP62.0 0.00% -> 0.01%. The
h_2016 construction is a first-order term in the rejection rate
(factor ~2 up at KP58.8, ~10 down at KP60.0, direction section-specific)
— the trace-anchored baseline (ADR-0035) and this bracket must be
reported together.

**Criterion (`--criterion no_breach_no_initiation`, evidence-strength
sensitivity):** rejects 66.4% at KP57.4 (below the 50% headroom floor,
warned), 99.57% at KP58.8 and 99.30% at KP60.0 (posteriors collapsed to
432 and 696 rows, auto-flagged statistically meaningless), and 30.46% at
KP62.0 — the one usable-size strict posterior, and an interesting reading
on its own: the uplift/heave gate latches for ~30% of the KP62.0 prior
under the 2016 loading even though breach rejection there is exactly
zero, i.e. the initiation margin and the progression margin separate
cleanly at the governing section. As documented in ADR-0036 and
section 5, the strict no-initiation reading of the reach-scale no-boil
survey is far too strong for these gate priors; it stays a qualitative
sensitivity and is not a deliverable posterior.

### 11.4 Downstream artifacts produced with these posteriors

* ADR-0037 segment-level fragility tables (primary lambda_ac = 250 m,
  n_eff = 1; bracket 100/40 m): `results/segment_fragility_adr0037.json`.
* Phase 3 first composition + hazard run (ADR-0038, BEP-only, posterior
  transient curves): `results/system_integration/` — annualized BEP
  P_f rises historical -> +4K by factors 5.5 (KP58.8) to 12.5
  (KP57.4/62.0), entirely through the d4PDF stage-frequency (ADR-0023).

Sections 6.1 to 6.4 (self-test) remain as the build-time record; the
production numbers above supersede them wherever they differ.
