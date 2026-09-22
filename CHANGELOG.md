# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The engineering record at the level of individual decisions is not duplicated
here. It lives in three places, all tracked:

* `docs/decisions/` — 53 Architecture Decision Records, gap-free, every one
  Accepted but ADR-0007, which is superseded in place by ADR-0027, plus their
  companion evidence notes and JSON artifacts;
* `docs/project_log.md` — a dated narrative of what was learned and when,
  including the claims that were later withdrawn or corrected;
* `docs/*_report.md` — the reports of record for Phases 2 and 3 and for the
  Stage 6.6 gap decomposition.

---

## [1.1.0] — 2026-09-22

The Green Light release: the state of the engine and its evidence base at the
end of the correction campaign that followed submission. Everything in 1.0.0
is here; what this release adds is one opt-in study knob, one corrected
contract at the record-to-integrator boundary, the Obihiro-gauge re-run that
followed it, seven measurement studies that tested claims the thesis had been
arguing rather than measuring, and a publication-figure pass. **This is the
release the thesis numbers were produced by**, and it is the one to cite.

### Added

* **ADR-0052, `foreland_seepage_credit`** — an opt-in credit of a fraction φ of
  each realization's own foreland entry length to the seepage length the
  Sellmeijer rule is evaluated at, and nothing else: the critical pipe length,
  the traverse, the transient limit state, the equation (5) denominator and the
  entrance-resistance factor all keep the physical length. It is scaled in M6,
  so it works on both progression backends, and because the critical head is
  single-source **both** limit states move with it. Default off. TR
  Zandmeevoerende Wellen (1999) §4.4.2 permits the credit and production
  declines it; the knob exists so the decline is bracketed rather than
  asserted, on both grain-size readings and on both sides of the 2016 update.
* **ADR-0053, `bep_reliability_engine/time_contract.py`** — the record time
  contract as an explicit, tested module: for `N` instantaneous observations
  there are `N − 1` intervals, stored trajectories begin at the initial state,
  and a breach time is the elapsed time at the first completing end state.
* Seven studies, each with a driver, an evidence JSON and a test gate:
  binomial interval coverage under the production Latin hypercube design; the
  two RQ1 metrics and the order-dependence of the index ladder; what the 2016
  survival actually constrains, including the seepage length; four
  physical-model statements the thesis had argued instead of measuring; the
  climate ratio as a mixture rather than a product; the retreat law the
  foreshore softening factor belongs to; and a whole-document claim synthesis.
* `scripts/migrate_breach_clock.py` and
  `scripts/verify_time_contract_propagation.py`, the migration and verification
  path for the ADR-0053 correction.

### Changed

* **The 2016 replay is anchored at the Obihiro gauge**, not at the reference
  point it had been using. The whole pipeline was re-run and every record that
  moved was updated; the above-toe durations of the 2016 excursion are 9, 21,
  28 and 6 h at the corrected node.
* **Breach clocks are corrected by +225 s** in 80 persisted posteriors, with
  the originals archived. Production failure probabilities are **unchanged** —
  proven per row on all eight strata, plus the exact 64-day 2011 hold — and the
  forward-Euler scheme and both driving heads are untouched. Evidence:
  `docs/decisions/adr0053-remediation-verification.md`.
* **`aquifer_lag_active = True` is now refused at configuration load.** Public
  evaluation is instantaneous only; the lagged-head kernel survives as the
  pre-registered screen's tested alternative. No production configuration used
  it — the instantaneous verdict is evidenced at all eight strata (ADR-0032) —
  but a configuration that set it is no longer silently accepted.
* **The warming hazard bootstrap is stratified inside the six prescribed SST
  patterns**, 15 member blocks in each. The patterns are a prescribed CMIP5
  design the estimand conditions on at equal weight, not a sample, and a pooled
  draw over all 90 blocks reweights them. Point estimates and the whole
  historical half are exactly invariant; the warming interval half-widths are
  8 to 19 per cent.
* **A mechanism share's denominator is named on the axis that carries it.**
  `dominance_share` normalises by the sum over mechanisms, not by the composed
  union probability; the tie and every dominance ordering are invariant to the
  choice, but the documentation and one figure axis had said otherwise.
* All 71 publication figures went through one printed type scale, one legend
  convention and the main-body house style, and the three failure mechanisms
  received a palette of their own. Every redraw was gated on a byte-identity
  determinism check against its committed copy.
* Documentation counts brought current: 53 Architecture Decision Records and
  1086 tests.

### Fixed

* **Continuous integration on a fresh clone.**
  `test_climate_attribution_decomposition.py` read a gitignored `results/` path
  with no existence guard, so it passed locally forever and failed on every
  clone. It is guarded by the repository's own written rule
  (`docs/conventions.md` §9.4) and is not weakened: with the artifact present it
  still asserts every field.
* **Two figures that were stale in the engine and in the thesis at once**, and
  therefore invisible to a digest comparison between the two copies. Found by
  re-rendering unchanged and comparing bytes; the rule that a digest gate proves
  only that two copies agree, never that either agrees with the data, is
  recorded in `docs/project_log.md`.
* Four figure labels that named something the figure did not draw, and the
  2011 closure marginal, which is 0.326 per cent and had been carried at 0.316
  in two records after the gauge correction regenerated it.

### Withdrawn

Claims the campaign measured and could not sustain are withdrawn in place, each
with a dated pointer to what replaced it, rather than deleted:

* that Accept-Reject updating cannot tighten the seepage length, and that its
  Sobol total-effect index is an irreducible floor — Accept-Reject rejects
  **rows**, each of which carries its own paired length;
* that the two failure sets are not strictly nested — nesting is a theorem, with
  zero violations in 24,000,000 row-level evaluations;
* that the static-versus-transient comparison cancels in both the ratio and the
  index metric or in neither — the two metrics rank a common-mode input and a
  transient-only input oppositely;
* that the annual probability rises mainly because long floods become more
  frequent — frequency leads inside the long stratum only, and the short
  stratum's own conditional probability rises by 5.1 to 14.0;
* that importance sampling cannot estimate a ratio between the two branches —
  the pre-registered negative is a verdict on one proposal;
* that the foreshore softening factor applies to any monotone depth-dependent
  retreat law — it belongs to a linear one, and only the bounding direction is
  general.

## [1.0.0] — 2026-09-05

Archived at 4TU.ResearchData: <https://doi.org/10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d>

The thesis-submission release. The engine, its evidence base and its
documentation as they stood when the MSc thesis was handed in. Everything below
this heading was developed between 2026-05-19 and 2026-09-05 on the `develop`
line; this release is the first to be published on `main`.

### Phase 1 — fragility engine (`bep_reliability_engine`)

* Modules M1 to M9 and the `run.py` orchestrator: configuration, Latin
  hypercube sampling of a 7-dimensional prior, d4PDF hydrograph ingest and H-Q
  stage translation, blanket hydraulics with a finite-foreshore correction,
  uplift and heave initiation, the Sellmeijer (2011) critical head as the single
  source for **both** limit states, forward-Euler progression after Pol (2024),
  the shared-sample evaluator, and fragility-curve assembly with bootstrap
  confidence bands.
* The **shared-sample contract**: one sampled parameter vector feeds both limit
  states through one evaluator call, so every comparison between them is paired.
* Two driving heads, each used as its author intended, differing by exactly the
  crack-resistance decrement; the uplift and heave gate is the only consumer of
  the entrance-resistance attenuation.
* Integration timestep fixed at 225 s (native / 16) after forward Euler was
  measured jumping the equilibrium barrier at the native hourly step.
* Persistence as HDF5 arrays with a JSON metadata sidecar; the parameter matrix
  and both failure matrices are retained as the Phase 2 handoff payload.
* Optional, default-off study knobs, each bit-identical to the baseline when
  off: length effect, Sellmeijer model factor, prior-mean scenarios, toe-gradient
  relief, open-entry foreland, transient-only exponent, the Numba progression
  backend, critical-pipe-length scaling, and the crack-resistance factor that
  produces the equal-head-convention comparison.

### Phase 2 — survival updating (`bayesian_reliability_updating`)

* Accept-Reject updating of the Phase 1 prior against the observed survival of
  the 2016 typhoon, after Schweckendiek (2014), replaying persisted runs through
  the frozen scalar evaluator surface behind a configuration-hash gate.
* The event set is closed at 2016, with the closure argued from the absent stage
  records for the 2011 and 2006 candidates and a sustained-peak bound.

### Phase 3 — system composition (`system_integration`)

* Series composition of backward erosion piping with the other levee failure
  mechanisms per 200 m segment, and annualisation over the d4PDF hazard for a
  historical and a +4 K climate scenario.
* Hazard-sampling confidence intervals by block bootstrap over ensemble
  **members**, the simulated years being nested within them.
* A foreshore-exhaustion screening indicator, built and test-pinned but
  deliberately not wired into the composition.

### Evidence and reproducibility

* 919 tests, all passing; continuous integration runs `ruff check`,
  `black --check` and `pytest` on Python 3.11, on `windows-latest` — the
  platform every persisted result was produced on.
* One idempotent, resumable driver, `scripts/production_campaign.py`, sequences
  the whole campaign from configuration generation through to figures behind
  seven gates.
* All 8 production configurations are generated from a single geotechnical CSV
  and are covered by a drift guard; the geometry values are inside the
  configuration hash, so a hand-edit is detected rather than silently accepted.
* 71 publication figures, each written by its driver and staleness-gated; no
  figure is copied by hand.
* `data/raw/README.md` documents the layout, provenance and SHA-256 manifest of
  the third-party source drop, which is not redistributed.

### Changed in preparation for publication

* `main` now carries the finished work. The five-commit repository stub that
  previously occupied it had an unrelated history and is preserved under the
  `v0.0.1` tag.
* Packaging metadata corrected: the distribution no longer installs `tests` as a
  top-level package, the licence is declared as an SPDX expression, and the
  operating-system classifier no longer claims Windows only.
* `CITATION.cff` now carries the reserved 4TU.ResearchData DOI
  `10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d`, together with the abstract,
  keywords, licence and release date that make GitHub's citation widget useful.
  The DOI is inactive until the deposit is published, which is why it does not
  yet resolve; that is how a reserved DOI behaves and is not a defect.
* `scripts/rq1_beta_analysis.py` no longer hard-codes a machine-local path for
  its optional figure mirror; set `BEP_THESIS_FIGURES` to enable it.
* Task-brief documents under `docs/work_packages/` were retired. Their outcomes
  are carried by the ADRs, companion notes and reports they commissioned, and
  the pre-registered expectations cited by ADR-0051 are reproduced inside it.
* Continuous integration, red since 2026-07-02, is green again. Twelve tests
  read the untracked `data/raw` drop without the skip guard the rest of the
  suite uses, so they errored on any clone without it; they are guarded now,
  and where a test mixed tracked and untracked sources the untracked half was
  split into its own guarded test rather than losing the tracked half. The
  runner moved from `ubuntu-latest` to `windows-latest`, the platform of
  record; the Linux last-bit difference that motivated the move is disclosed
  in the README under **Platform** and no assertion was relaxed for it.

## [0.0.1] — 2026-05-20

Repository scaffold: licence, citation file, ignore rules, and the Phase 1
computational architecture specification.

[1.1.0]: https://github.com/Gimori3/bep-reliability-engine/releases/tag/v1.1.0
[1.0.0]: https://github.com/Gimori3/bep-reliability-engine/releases/tag/v1.0.0
[0.0.1]: https://github.com/Gimori3/bep-reliability-engine/releases/tag/v0.0.1
