# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The engineering record at the level of individual decisions is not duplicated
here. It lives in three places, all tracked:

* `docs/decisions/` — 51 Architecture Decision Records, gap-free, every one
  Accepted, plus their companion evidence notes and JSON artifacts;
* `docs/project_log.md` — a dated narrative of what was learned and when,
  including the claims that were later withdrawn or corrected;
* `docs/*_report.md` — the reports of record for Phases 2 and 3 and for the
  Stage 6.6 gap decomposition.

---

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

[1.0.0]: https://github.com/Gimori3/bep-reliability-engine/releases/tag/v1.0.0
[0.0.1]: https://github.com/Gimori3/bep-reliability-engine/releases/tag/v0.0.1
