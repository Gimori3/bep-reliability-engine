# bayesian_reliability_updating: Phase 2 Bayesian Reliability Updating

Monte Carlo Accept-Reject filtering of the Phase 1 BEP prior realization
set against observed levee survival, producing calibrated posterior
parameter distributions and posterior fragility curves for the Tokachi
study sections. This package is Phase 2 of the thesis; the physics engine
is Phase 1 (`bep_reliability_engine`) and is never reimplemented here:
every limit-state evaluation goes through the Phase 1 M8 evaluator.

## Theory in one paragraph

Survival of the August 2016 consecutive-typhoon event is inequality
evidence in the sense of Schweckendiek (2014, sections 4.2.2 to 4.2.4):
the evidence is epsilon = {Z_transient(h_2016(t), theta) > 0}, and the
posterior parameter distribution is the prior restricted to the survival
region, pi_post(theta) proportional to pi_prior(theta) times the survival
indicator (thesis methodology chapter, Accept-Reject Filtering section).
On the Monte Carlo sample this is exact: replay every prior row through
the same time-stepping solver used in Phase 1 with the observed h_2016(t)
as the boundary condition (l_ini = 0, recovery r_l = 0), reject rows that
predict the unobserved breach, keep the survivors as the joint posterior
sample. Posterior failure probabilities follow Schweckendiek Eq. 4.12,
P(F | epsilon) = P(F and epsilon) / P(epsilon), realized as failure
fractions among accepted rows of the retained Phase 1 failure matrices.
Unlike the WBI+ practice of updating through the survived PEAK level only
(Zethof et al. 2023, appendix C), the constraint here is the full
transient hydrograph; the 2026-07-12 self-test measured that the
peak-level shortcut would overstate the rejection by a factor of 3 to 4
at the study sections, so the full replay is load-bearing, not cosmetic.

Because the static Sellmeijer branch is evaluated on the same rows in the
same M8 call, every update also reports the survival-discrimination
decomposition (spec section 8): how much of the rejection is already
implied by the static (peak-head) criterion, and how much is the marginal
information of the time-dependent mechanism.

## The one command

Against production Phase 1 sweep outputs (one PosteriorResult pair plus
figures per input file, written to `results/phase2/`):

```powershell
python -m bayesian_reliability_updating results/*_historical_*.h5 --verify
```

`--verify` additionally re-evaluates the accepted rows on the run's own
conditioning records and requires exact agreement with the masked-matrix
posterior curves (slower; recommended once per campaign). Other options:
`--criterion no_breach_no_initiation` (the stricter documented variant),
`--anchor rating` (the unanchored ingestion sensitivity),
`--no-breach-times`, `--no-figures`, `--n-bootstrap`, `--backend numba`,
`--overwrite`. See `python -m bayesian_reliability_updating --help`.

The self-test (genuine small-N Phase 1 runs plus the full update at
KP 58.8 and KP 60.0):

```powershell
python scripts/run_phase2_selftest.py --n 4000 --n-jobs 4
```

## What a run does

1. **Load and verify** the Phase 1 `FragilityResult` (`replay.py`): the
   Config is rebuilt from the embedded snapshot and hash-checked; the
   retained theta matrix must regenerate bit for bit through the M2
   sampler; the stochastic seepage lengths are regenerated through the
   ADR-0034 seam so L_j pairs with theta_j exactly as in the sweep.
2. **Build the observed event** at the run's own section (`events.py`,
   ADR-0035): observed Obihiro stage inverted through the gauge's own
   Eq. 4.19 rating, re-rated at the section KP through the verbatim M3
   path, peak anchored to the surveyed 2016 flood trace on the study
   bank; full multi-peak structure preserved verbatim; window-closure
   diagnostic recorded.
3. **Replay M8** over every prior row on the run's ADR-0030 225 s grid
   (`evaluate_batch_diagnostics`), retaining margins, terminal pipe
   lengths, initiation latches and t_uh.
4. **Filter and decompose** (`filtering.py`): strict Z > 0 acceptance on
   joint 7-tuples including C_e; the full two-by-two static/transient
   decomposition; scale-aware posterior-size diagnostics.
5. **Posterior fragility** (`fragility_update.py`): masked-matrix curves
   (no re-sweep needed), Clopper-Pearson CIs at n_accepted, bootstrap
   bands, Optional M9 lognormal fits; optional exact re-evaluation
   verification.
6. **Analyse, persist, plot**: prior-versus-posterior marginals with the
   C_e laminar-conservatism headline, correlation-shift report,
   `PosteriorResult` HDF5 + JSON sidecar with full provenance (Phase 1
   SHA-256s, config hash, seeds, event chain, decomposition), and the
   figure set.

Additional survival events (for example September 2011) compose
sequentially (`sequential.py`): masks over the original prior rows, so
A-then-B equals B-then-A equals the joint filter exactly; supply extra
records via `pipeline.run_survival_update(..., event_records=[...])` or a
new `ObservedEventSource` for the 2011 extracts.

## Module map

| Module | Responsibility |
|---|---|
| `events.py` | Observed-event ingestion (reusable; 2016 built in) |
| `replay.py` | Phase 1 loading, provenance verification, M8 replay |
| `filtering.py` | Accept-Reject criteria, decomposition, diagnostics |
| `fragility_update.py` | Posterior curves, CIs, bands, verification |
| `sequential.py` | Posterior-in posterior-out event composition |
| `posterior.py` | `PosteriorResult` artifact, HDF5 + JSON persistence |
| `analysis.py` | Prior/posterior marginals, C_e headline, correlations |
| `plots.py` | Figure set (repo dataviz style) |
| `pipeline.py` | End-to-end orchestration, `Phase2Settings` |
| `cli.py` / `__main__.py` | The one-command entry point |

## Decisions and documentation

- ADR-0034: the additive Phase 1 surface extensions this package stands on.
- ADR-0035: the 2016 observed-event ingestion (gauge assignment, trace
  anchoring, datum evidence, window closure).
- ADR-0036: the updating architecture (225 s replay superseding ADR-0022
  decision 2, criteria, masked-matrix + verification, sequential
  composition, thresholds, persistence schema).
- `docs/phase2_report.md`: the full analytical report (data inventory,
  self-test results, limitations, the production checklist and the 2011
  assessment).
- `docs/phase2_interface.md`: the Phase 1 handoff contract this package
  consumes.

## References

- Schweckendiek, T. (2014). On Reducing Piping Uncertainties: A Bayesian
  Decision Approach. PhD thesis, TU Delft. (Direct reliability updating,
  Eq. 4.10/4.12; survival of extreme loads, chapter 5.)
- Zethof, M. et al. (2023). Continuous Insight WBI+ Final Report, HKV
  PR3959.92. (Appendix C: reliability updating of fragility curves with
  survived water levels; the peak-based practice contrasted here.)
- Thesis methodology chapter, Phase 2 sections; `docs/architecture.md`
  section 8.
