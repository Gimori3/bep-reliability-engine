# bep-reliability-engine

A time-dependent **backward erosion piping (BEP)** reliability engine for the
Tokachi and Satsunai levees near Obihiro, Hokkaido, built as the computational
evidence base for an MSc thesis.

It quantifies the bias between the **static** limit state (Sellmeijer 2011) and
the **transient** one (Pol, SIE 2024) by Monte Carlo fragility analysis, updates
the result against the observed survival of the 2016 typhoon, and composes it
with the other levee failure mechanisms into a system reliability per 200 m
segment under a historical and a +4K climate.

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

## Install

`pyproject.toml` is the single source of truth for dependencies. There is no
`requirements.txt`.

```powershell
.\.venv\Scripts\Activate.ps1     # Python 3.11 only (requires-python >=3.11,<3.12)
pip install -e .[dev]            # package + dev tooling
pip install -e .[accel]          # optional Numba backend (ADR-0029, opt-in)
```

## The three commands

```powershell
python scripts/generate_configs.py                      # configs/ from the geotech CSV
python scripts/run_sweep.py configs/kp*_matrix.yaml     # Phase 1 fragility sweeps
python -m bayesian_reliability_updating results/*_historical_*.h5 --verify
python -m system_integration                            # Phase 3 composition
```

The whole campaign is sequenced by one idempotent, resumable driver:

```powershell
python scripts/production_campaign.py    # configs -> sweeps -> Phase 2 -> Stage 6.6
                                         # -> Phase 3 -> companions -> figures (gates G1-G7)
```

PowerShell does not glob-expand arguments to external programs -- splat a
`Get-ChildItem` array rather than passing `*.h5` literally.

## Where things live

| Path | What it is |
|---|---|
| `docs/architecture.md` | **The authoritative implementation spec.** Implement against it; deviate only with a documented justification. |
| `docs/decisions/` | Architecture Decision Records `NNNN-slug.md` (0001-0048), their `adrNNNN-*` companion notes and evidence JSONs, and un-numbered studies. See `docs/conventions.md` for the naming grammar. |
| `docs/conventions.md` | Coding conventions, the thesis-text rule, the documentation and results-retention conventions. |
| `docs/*_report.md` | Reports of record: Phase 2, Phase 3, Stage 6.6. Later addenda are authoritative where they differ from earlier sections. |
| `docs/*_YYYY-MM-DD.md` | Closed one-shot audit and campaign artifacts, dated in the filename. |
| `docs/validation/` | Japanese case-validation notes and the Pol-meeting dispositions. |
| `docs/figures/` | The 52 tracked publication figures. Written directly by their drivers and staleness-gated by G7 -- never copied by hand. |
| `docs/tokachi_bep_inputs_provenance.md` | Per-cell audit trail for the geotechnical input CSV. |
| `configs/` | The 8 generated run configs. **Generated, not hand-edited** -- re-run `generate_configs.py` after any CSV change. |
| `notebooks/` | Thin drivers only. Physics never lives in notebook cells. |

## Not in a fresh clone

`results/`, `data/raw/`, `docs/references/` and the Uemura fragility-curve drop
are gitignored and machine-local. Scripts that need them skip rather than fail;
everything tracked under `docs/` is expected to be present, and tests assert it.

Thesis prose lives **only** in `d:\repositories\msc-thesis`, never here
(`docs/conventions.md` section 8, enforced by `tests/test_repo_hygiene.py`).

## Gates

CI runs exactly three checks on Python 3.11, and all three must pass:

```powershell
ruff check .
black --check .
pytest
```
