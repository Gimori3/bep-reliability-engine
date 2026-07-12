# ADR-0036: Phase 2 Accept-Reject Updating Architecture

Date: 2026-07-12

## Status
Accepted (supersedes ADR-0022 decision 2, the 1800 s Phase 2 replay timestep)

---

## Context

Phase 2 implements the thesis's Bayesian reliability updating: Monte Carlo
Accept-Reject filtering of the Phase 1 prior realization set against the
documented survival of the study segments during the August 2016
consecutive typhoons, following the direct reliability updating of
Schweckendiek (2014) Eq. 4.10/4.12 with survival as inequality
information, realized on the sample as the accepted subset (thesis
methodology chapter, Accept-Reject Filtering section; spec section 8).
The package `bayesian_reliability_updating` was built 2026-07-12 as one
uninterrupted campaign; this ADR records its load-bearing decisions.
Companion records: ADR-0034 (the Phase 1 surface it stands on) and
ADR-0035 (the observed-event ingestion).

## Decisions

### 1. Replay timestep: the run's own ADR-0030 grid (225 s); ADR-0022 decision 2 superseded

The observed record (hourly native) is refined onto the Phase 1 run's own
`timestepper.target_dt_seconds` grid (225 s in every production config)
via the M3 `resample_record` hook before the replay. ADR-0022 decision 2
prescribed 1800 s for the Phase 2 replay, but it predates ADR-0030's
finding that coarse forward-Euler steps jump the H_eq equilibrium barrier
and produce spurious per-row transient failures: exactly the artifact an
Accept-Reject filter must not contain, because each spurious failure
wrongly deletes a prior row. Using the run's own grid also keeps the
replay and the retained failure matrices on one convergence footing,
which decision 4 depends on. (The architecture.md revision note of
2026-07-12 flagged this re-check; this ADR resolves it.)

### 2. Acceptance criteria

Baseline (`no_breach`, the thesis criterion): accept row j iff
Z_transient(h_2016(t), theta_j) > 0 with l_ini = 0 and recovery r_l = 0;
the boundary Z = 0 counts as failure (ADR-0008), so survival is the
strict complement of the retained failure flag. Rejection is row-wise on
the full joint 7-tuple including C_e; no per-parameter rejection exists,
so the posterior retains every constraint-induced correlation
(Schweckendiek 2014 section 4.2.2), which `analysis.correlation_shift`
reports explicitly.

Stricter optional variant (`no_breach_no_initiation`, config-gated, OFF
by default): additionally reject rows whose uplift-plus-heave gate
latched under h_2016, reflecting the committee-documented absence of sand
boils at the study reaches. Caveats, documented and load-bearing: the M5
gate models blanket uplift/heave initiation, not boil visibility at the
surface; the no-boil observation is a reach-scale survey, not a
per-section instrument record; and under the ADR-0008 Terzaghi collapse
the gate is deliberately conservative. The baseline therefore remains
no-breach, and the strict variant exists for sensitivity.

### 3. Identical-assumptions replay, provenance-verified

The replay reconstructs the Phase 1 run entirely from the persisted
artifact: the Config is rebuilt from the metadata snapshot and its hash
must equal the recorded `config_hash`; the retained theta matrix must be
regenerated bit for bit from the snapshot through the M2 sampler
(refused otherwise); the stochastic seepage lengths are regenerated
through `run.seepage_length_samples_for_config` so L_j pairs with
theta_j exactly as in the sweep; and every deterministic evaluation
setting (Sellmeijer inputs, foreland treatment, backend) is threaded from
the snapshot into `evaluate_batch_diagnostics`. The M3 MSL datum guard
runs before any evaluation.

### 4. Posterior fragility: masked-matrix default, exact re-evaluation verification

Default path: P_f_post(h_i) = mean over accepted rows of the RETAINED
failure matrix column i, per branch, both branches conditioned on the
same transient-survival evidence: the Monte Carlo form of Schweckendiek
Eq. 4.12, with no re-running of the conditioning sweep. Uncertainty
mirrors ADR-0024: always-on Clopper-Pearson CIs at n_accepted plus
percentile bootstrap bands over accepted rows (seed derived from the
Phase 1 config seed via SeedSequence with a Phase 2 salt); M9's
`fit_lognormal_fragility` attaches Optional datum-anchored fits under the
same criteria as Phase 1.

Verification mode (optional flag): accepted rows are re-evaluated through
`evaluate_batch` on the run's own conditioning records
(`run.conditioning_hydrographs_for_config`) and the recomputed flags must
equal the retained matrix entries bit for bit, hence the curves exactly.
Any deviation raises: it would prove the reconstructed context is not the
Phase 1 context, invalidating the whole update. Verified exact on the
real KP 58.8 and KP 60.0 paths (2026-07-12 self-test).

### 5. Sequential updating: masks over original rows

Events compose as successive indicator constraints on the same prior:
each event is replayed over ALL N original rows and acceptance masks
compose by logical AND, so A-then-B equals B-then-A equals the joint
filter as an array identity (pinned by test), per-event decompositions
stay reportable against the full prior, and the physical posterior-in
posterior-out reading is recovered exactly (rows alive after the chain
are those accepted by every event). Each event replays from a virgin
blanket (l_ini = 0, r_l = 0): events years apart are independent
constraints, consistent with the Pol thesis inter-flood recovery
evidence; cross-event pipe-length memory is deliberately out of scope.

### 6. Survival-discrimination decomposition: the full two-by-two

Because the two failure sets are not strictly nested in general
(different driving heads, ADR-0027/0028), the full cross-tabulation is
reported per stratum file: both-survive, transient-only-reject (the
marginal informativeness of survival for the time-dependent mechanism,
a first-class output), static-only-reject, both-reject. Stratification
follows spec section 8: one Phase 1 file is one
(segment, remediation_state, d70_interpretation) stratum, so the
decomposition is computed once per file and tabulated across files.

### 7. Posterior sample-size diagnostics

Scale-aware floors, logged and persisted in metadata: a warning below 50
percent of the prior (the spec section 11 CoV target needs order 8e4
effective rows at production N = 1e5, and the anticipated ~20 percent
rejection leaves that headroom; deeper cuts degrade the posterior tail
below the Phase 1 standard), and an error-level collapse diagnostic below
min(1000 rows, 1 percent of N). Near-zero rejection at drained segments
is correct behavior and produces no diagnostic.

### 8. Artifact and layout

One `PosteriorResult` per Phase 1 file (= per segment per scenario per
d70 interpretation), HDF5 arrays plus JSON sidecar, no pickle: full theta
matrix, regenerated L samples, the operative and per-event masks, the
per-event replay diagnostics and rejected-row breach times (traced
through the scalar M8 with trajectories, the one sanctioned trajectory
run), posterior curves with CIs, bands and Optional fits, prior-curve
copies, and a provenance block carrying the Phase 1 file SHA-256 pair,
config hash, seeds, package versions, the event chain with construction
provenance, the decomposition, and the prior-to-posterior marginal
summary with the C_e headline. Entry point:
`python -m bayesian_reliability_updating <phase1.h5> ...`.

---

## Alternatives Considered

### Replay at 1800 s (ADR-0022 decision 2 as written)
Pros: 8 times cheaper. Cons: the ADR-0030 overshoot mechanism acts
per row, and rows near the breach boundary are precisely the rows the
filter adjudicates; measured at the fragility level the overshoot
inflated shoulder P_f up to ~27 times at 3600 s. Rejected.

### Physically shrinking the sample between sequential events
Pros: marginally cheaper replays later in the chain. Cons: masks over
shifting index bases are the classic provenance bug; the full-N replay
cost is identical for the first event and small thereafter, and the
array-identity composition test only exists in the masks-over-original
form. Rejected.

### Weighted (likelihood-based) updating instead of hard Accept-Reject
Pros: generalizes to non-indicator evidence (measurement error on the
observed loading). Cons: the thesis commits to the exact benchmark
Accept-Reject method (Schweckendiek 2014) with survival as crisp
inequality evidence; loading uncertainty is handled at the ingestion
level (ADR-0035 anchoring variants), not by softening the criterion.
Out of scope by design; the sampler-side hook for it would be importance
weights on rows, which the PosteriorResult schema could carry additively
if ever needed.

---

## Rationale

Every choice traces to one of: the thesis's committed method (criterion,
posterior definition), a Phase 1 contract that must be honored
identically in the replay (timestep, L pairing, settings threading), or a
reproducibility guarantee (hash-verified provenance, deterministic seeds,
exact verification). Where Phase 1 already solved a problem (persistence
split, CI presentation, fit criteria, seed derivation), Phase 2 reuses
the solution rather than inventing a second one.

---

## Consequences

- Running Phase 2 against the production sweep is one documented command
  per file set; runtime is minutes per section at N = 1e5 (dominated by
  the 225 s replay and, when enabled, the breach tracing and the
  verification sweep).
- The posterior deliverable inherits the ADR-0024 presentation logic:
  where the posterior point set no longer brackets the transition, the
  raw points with CIs are the deliverable and the fit is absent by
  design.
- 2026-07-12 self-test (N = 4000, KP 58.8 and KP 60.0, matrix): transient
  rejection 5.2 and 3.3 percent, static rejection 58 and 74 percent,
  marginal transient rejection 0.0 at both sections (the transient
  failure set nested inside the static one under the real 2016 loading),
  posterior C_e mean down 4.0 and 3.6 percent, verification exact. See
  `docs/phase2_report.md` for the interpretation.

---

## References

- Schweckendiek (2014), sections 4.2.2 to 4.2.3 and chapter 5 (direct
  reliability updating; survival of extreme loads).
- Zethof et al. (2023), appendix C (the WBI+ peak-based closed form this
  thesis deliberately bypasses with the full transient replay).
- Thesis methodology chapter, Phase 2 sections; spec section 8.
- ADR-0008, ADR-0022 (decision 2 superseded here), ADR-0024, ADR-0027,
  ADR-0028, ADR-0030, ADR-0034, ADR-0035.
