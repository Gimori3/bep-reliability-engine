# bep-reliability-engine

[![CI](https://github.com/Gimori3/bep-reliability-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/Gimori3/bep-reliability-engine/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3119/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4121/8ffa1f3e--942e--4852--b02a--a259b9d6d00d-blue.svg)](https://doi.org/10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d)

A time-dependent **backward erosion piping (BEP)** reliability engine for the
Tokachi and Satsunai levees near Obihiro, Hokkaido, built as the computational
evidence base for an MSc thesis in Hydraulic Engineering at Delft University of
Technology.

It quantifies the bias between the **static** limit state (Sellmeijer 2011) and
the **transient** one (Pol, SIE 2024) by Monte Carlo fragility analysis on a
shared sample, updates the result against the observed survival of the 2016
typhoon, and composes it with the other levee failure mechanisms into an
annualised system reliability per 200 m segment under a historical and a +4 K
climate scenario.

**Status.** Version 1.0.0 is the frozen state of the engine at MSc thesis
submission (September 2026). It is published so the work can be read, checked
and re-run; it is not under active development, and no further research
results are expected from it.

> **Reading the results.** Every headline comparison in this repository is
> conditional, and the conditions do not cancel. The reports of record state the
> brackets each number carries; `docs/project_log.md` records the claims that
> were tested and withdrawn along the way. Please quote from those, not from
> a curve read off a figure.

## Three packages, one direction of dependency

```
bep_reliability_engine          Phase 1 -- the fragility engine (modules M1-M9)
        |                       LHS prior -> two limit states on one shared
        |                       sample -> per-section fragility curves
        v
bayesian_reliability_updating   Phase 2 -- Accept-Reject updating of the Phase 1
        |                       prior against the 2016 survival record
        v
system_integration              Phase 3 -- multi-mechanism series composition
                                and annualisation over the d4PDF hazard
```

`bep_reliability_engine` never imports from the other two. Phase 2 imports Phase
1's frozen `evaluate_realization` surface and replays persisted runs; Phase 3
consumes persisted Phase 1/2 artifacts through typed seams. **Do not introduce a
reverse import.**

### Module map

| Module | File | Responsibility |
|---|---|---|
| M1 | `config.py` | Typed configuration, unit conversion, the configuration hash |
| M2 | `sampling.py` | Latin hypercube sampling of the 7-dimensional prior |
| M3 | `hydrographs.py` | d4PDF discharge ingest, H-Q stage translation, resampling |
| M4 | `hydraulics.py` | Blanket hydraulics, finite-foreshore correction, aquifer response |
| M5 | `initiation.py` | Uplift and heave gate |
| M6 | `sellmeijer.py` | Critical head — **the single source for both limit states** |
| M7 | `progression.py` | Forward-Euler pipe progression after Pol (2024) |
| M8 | `evaluator.py` | The shared-sample evaluator; the frozen Phase 2 surface |
| M9 | `fragility.py` | Fragility-curve assembly and bootstrap confidence bands |
| — | `run.py` | Orchestrator. **Contains no physics** — everything goes through M8 |

## Install

`pyproject.toml` is the single source of truth for dependencies. There is no
`requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Python 3.11 only (requires-python >=3.11,<3.12)
pip install -e .[dev]            # package + dev tooling
pip install -e .[accel]          # optional Numba backend (ADR-0029, opt-in)
```

On Linux or macOS the same commands work with `source .venv/bin/activate`.
See **Platform** below for the one respect in which the platform matters.

## Running it

```powershell
python scripts/generate_configs.py                      # configs/ from the geotech CSV
python scripts/run_sweep.py configs/kp*_matrix.yaml     # Phase 1 fragility sweeps
python -m bayesian_reliability_updating results/*_historical_*.h5 --verify
python -m system_integration                            # Phase 3 composition
```

The whole campaign is sequenced by one idempotent, resumable driver, and every
number in the thesis traces to one execution of it:

```powershell
python scripts/production_campaign.py            # all stages, resuming
python scripts/production_campaign.py --dry-run  # print the plan and stop
python scripts/production_campaign.py --stage phase1
```

Its eleven stages run configuration generation, the 8 Phase 1 sweeps, three
Phase 2 variants, the Stage 6.6 gap decomposition, Phase 3, the companion
studies, the figures and the diagnostics, behind seven gates — of which **G1**
requires the re-run sweeps to reproduce the superseded failure matrices
bit-for-bit.

> PowerShell does not glob-expand arguments to external programs. Splat a
> `Get-ChildItem` array rather than passing `*.h5` literally.

## Reproducibility

The production configuration is 8 sweeps: 4 confined cross-sections
(KP 57.4 / 58.8 / 60.0 / 62.0) × 2 grain-size interpretations, at
N = 10⁵ realizations and Δt = 225 s, on the historical hazard scenario.

* **Configurations are generated, never hand-edited.** Re-run
  `scripts/generate_configs.py` after any change to the geotechnical CSV. The
  geometry values are inside the configuration hash, so a hand-edited YAML is
  detected by the Phase 2 replay gate rather than silently accepted;
  `tests/test_configs.py` is the drift guard.
* **Seeds are deterministic everywhere.** The configuration seed fully
  determines the sampled matrix and, through independent seed sequences, the
  separately drawn seepage length and model factor.
* **Optional knobs are default-off and bit-identical when off**, and each is
  dropped from the metadata when unset so pre-existing configuration hashes
  survive.
* **Nothing needs a GPU, a cluster or a licence.** A full campaign is hours, not
  days, on one workstation.

### What a fresh clone does and does not have

| Present | Absent (gitignored, machine-local) |
|---|---|
| All source, tests, configurations and generated inputs | `results/` — 3.7 GB of persisted runs |
| `data/processed/` — the geotechnical source of truth and event extracts | `data/raw/` — the third-party source drop |
| `docs/decisions/*.json` — measured evidence behind every ADR | `docs/references/` — copyrighted reference PDFs |
| `docs/figures/` — the 71 publication figures | |

**The test suite passes on a fresh clone.** It runs on synthetic and committed
fixtures throughout; the few tests that can also exercise the raw drop or a
persisted run are guarded and skip rather than fail when it is absent, and no
test asserts on anything untracked. Scripts behave the same way.
`data/raw/README.md` is tracked and documents that drop's required layout,
per-source provenance and SHA-256 manifest, so a holder of the same data can
verify they have the right one.

## Where things live

| Path | What it is |
|---|---|
| `docs/architecture.md` | **The authoritative implementation spec.** Implement against it; deviate only with a documented justification. |
| `docs/decisions/` | 51 Architecture Decision Records `NNNN-slug.md`, gap-free and all Accepted, plus `adrNNNN-*` companion notes, evidence JSONs, and un-numbered studies. `docs/conventions.md` gives the naming grammar. |
| `docs/project_log.md` | Dated narrative of what was learned and when — including what was later withdrawn. |
| `docs/*_report.md` | Reports of record: Phase 2, Phase 3, Stage 6.6. Later addenda are authoritative where they differ from earlier sections. |
| `docs/*_YYYY-MM-DD.md` | Closed one-shot audit and campaign artifacts, dated in the filename. |
| `docs/validation/` | Case-validation notes against Japanese levee failures, and the model-author consultation dispositions. |
| `docs/conventions.md` | Coding conventions, repository layout, and the results-retention policy. |
| `docs/figures/` | The 71 tracked publication figures. Written directly by their drivers and staleness-gated — never copied by hand. |
| `docs/tokachi_bep_inputs_provenance.md` | Per-cell audit trail for the geotechnical input CSV. |
| `configs/` | The 8 generated run configurations. |
| `data/processed/` | The geotechnical source of truth, the 2016 event extract, and the Phase 3 segment tables. |
| `notebooks/` | Thin drivers only. Physics never lives in a notebook cell. |

Thesis prose lives only in the separate `msc-thesis` repository, never here
(`docs/conventions.md` section 8, enforced by `tests/test_repo_hygiene.py`).

## Gates

CI runs exactly three checks on Python 3.11 on `windows-latest`, and all three
must pass:

```powershell
ruff check .          # E, F, I
black --check .       # line length 88
pytest                # 919 tests (912 fast + 7 slow)
```

`pytest -m "not slow"` skips the seven expensive reference-reproduction and
timestep-convergence tests.

## Platform

The code is ordinary Python and runs anywhere Python 3.11 and the pinned
dependencies do. **Windows is nonetheless the platform of record**: every
persisted result, every figure and every number in the thesis was produced
there, and CI runs on `windows-latest` so it reproduces that environment.

One consequence is worth stating plainly. The vectorized `evaluate_batch` path
and the scalar `evaluate_realization` loop are bit-identical on the platform of
record, and the headline gate that pins this,
`tests/test_run.py::test_orchestration_matches_reference_loop`, holds on Linux
as well. But four finer-grained diagnostics comparisons — in
`test_evaluator_batch_diagnostics.py`, `test_gsa_qoi.py` and
`test_model_factor.py` — assert exact equality on individual floats, and on
Linux those differ in the last representable bit (about 1 part in 10^16). That
is the ordinary consequence of numpy taking different SIMD and libm paths for
arrays than for scalars; it is far below any reported precision and changes no
failure indicator, but it means those four tests fail on a Linux runner. They
are left exact rather than relaxed, so the difference stays visible.

## Citing this work

Cite the **archived release**, not the repository URL. Version 1.0.0 is
permanently archived at 4TU.ResearchData:

> Rietman, G. M. (2026). *bep-reliability-engine* (Version 1.0.0) [Software].
> 4TU.ResearchData. <https://doi.org/10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d>

The DOI is the stable identifier: this repository is the development home and
can be renamed or moved, the deposit cannot. `CITATION.cff` carries the same
record in machine-readable form, and GitHub renders it as a ready-made citation
in the sidebar.

## Licence

MIT — see [LICENSE](LICENSE). The licence covers the code and the documentation
in this repository. It does **not** cover the third-party source data described
in `data/raw/README.md`, none of which is redistributed here, nor the reference
publications under `docs/references/`.
