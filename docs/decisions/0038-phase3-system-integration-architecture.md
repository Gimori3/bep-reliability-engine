# ADR-0038: Phase 3 System-Integration Architecture (package, hazard side, external seams)

Date: 2026-07-13

## Status
Accepted

---

## Context

RQ3 and RQ4 of the thesis require a composition layer that does not yet
exist: (RQ3) integrate the BEP fragility (Phase 2 posteriors) with Uemura's
pre-calculated overflow and fluvial-scour fragility curves in a series-system
joint-probability framework at the 200 m segment level, and (RQ4) drive the
integrated profile with the d4PDF historical (HPB, 3,000-year) versus +4K
(HFB, 5,400-year) stage-frequency at each section, attributing the shift to
hydrograph characteristics (peak, duration, compound sequencing). The
methodology chapter fixes the math: conditional independence given h (after
Pol RESS 2023), `P_sys(h) = 1 - prod_i (1 - P_i(h))`, applied per segment
and per scenario; climate differentiation lives entirely on this hazard side
because the Phase 1 fragility is shape-invariant (ADR-0023).

Two external inputs are **not on disk** and are owned by others: Uemura's
per-segment fragility curves (his thesis PDF is local, but no
machine-readable curves), and any basin-level event-frequency data beyond
the d4PDF ensembles themselves. The architecture must make their arrival a
plug-in, not a rebuild.

## Decisions

### 1. Third top-level package `system_integration`, physics-free

Mirrors the `bayesian_reliability_updating` precedent: a separate package
beside `bep_reliability_engine`, importing only public engine interfaces.
It contains **no physics** — it consumes persisted artifacts (Phase 1
FragilityResult, Phase 2 PosteriorResult), the M3 hydrograph machinery
(ensemble loading, rating conversion, band-workbook resolution), and the
public ADR-0037 length-effect transform. Any new physics would be an engine
change with its own ADR.

Modules: `segments.py` (registry), `bep_input.py` (BEP curve provider),
`surface_curves.py` (Uemura seam), `hazard.py` (d4PDF stage-frequency),
`composition.py` (series system), `annualize.py` (event-based/annual
probabilities), `cli.py`/`__main__.py` (one documented command).

### 2. Segment registry from the committed rating/bank-height grid

The 200 m evaluation nodes are the rating-curve KP grid already committed
(`data/raw/rating_curves/HQrelation_*.csv`, 0.2 km spacing), bounded to the
thesis reaches: Tokachi right bank KP 53.8-62.8, Satsunai left bank KP
3.2-16.6. Each segment carries `river`, `bank`, `kp` (its center node) and
an optional `bep_source` — the OYO cross-section whose (posterior) BEP
fragility it inherits. Default policy `exact`: only the four OYO sections'
own segments get BEP curves; every other segment's BEP curve is `None`
(honest data gap, per the thesis "bounded extrapolation" tiering — the
interpolated-prior extension for borehole-free reaches is future work, not
silently faked by nearest-neighbour). An explicit `nearest` policy exists
for sensitivity exploration and stamps itself into provenance.

Uemura's aggregation of segments into Sections (Tokachi 1-5, Satsunai 1-4)
is an **owner-supplied table** (seam, class D): `section_table.csv` with
columns `river,bank,kp_from,kp_to,section_id`; a validating loader checks
contiguity and coverage. Until supplied, results are reported per segment.

### 3. Hazard side: empirical annual-maximum stage-frequency from the d4PDF ensembles (ADR-0023 compliance)

Each band-workbook member column is one annual-maximum flood event of one
simulated ensemble-year (HPB: 3,000; HFB: 5,400 — ADR-0019). The hazard at
a node is therefore the **empirical annual-maximum peak-stage distribution**:
per member, stage via the node's own Eq. 4.19 rating (verbatim M3
`load_hydrograph_ensemble`, including the ADR-0019 §7 KP 62.x discharge
proxy); the annual exceedance probability of level h is the ensemble
fraction of years whose peak stage exceeds h (Weibull plotting positions
for the return-period axis). No parametric flood-frequency fit is imposed —
the ensembles are large enough that the empirical curve carries the thesis
range, and any fit would be a new modeling decision.

Event characteristics for the RQ4 attribution are computed per member with
the existing M3 `flood_timescales` plus above-toe exposure duration and
peak count; stratified comparisons (peak-matched duration classes etc.)
operate on these per-event tables.

**Composition rule (the ADR-0023 contract):** the fragility curve is
evaluated at each event's peak stage; `P_f,annual = mean over ensemble
years of P_sys(peak_stage_year)`. Climate change enters ONLY through the
peak-stage distribution and the event-characteristic stratification, never
through a re-derived fragility. The +4K conditional fragility equals the
historical one by shape invariance (ADR-0023); if a future study finds
shape-variance material, that is an ADR-0023 supersession, not a Phase 3
edit.

### 4. BEP curve provider and the ADR-0024 evaluation policy

`bep_input.py` loads the **Phase 2 posterior transient curve as the default
BEP input** (Phase 1 prior as an option, both branches available), exposing
one `FragilityCurve` type: conditioning grid (m MSL), raw P_f points,
Clopper-Pearson CIs, optional lognormal fit with its ADR-0024 `fit_role`,
and datum. Evaluation at arbitrary h follows ADR-0024 semantics:

* where the deliverable form is `fitted_lognormal`, evaluate the fit;
* otherwise interpolate the raw points **linearly in probit space** between
  grid neighbours (monotone, tail-respecting), clamp below the grid at the
  lowest raw value's CI floor of 0, and **never extrapolate above the
  highest grid level** — evaluation above it returns the last raw value and
  raises a recorded `clamped_above_grid` flag (KP62.0's transient branch
  lives here by design).
* zero-failure grid points interpolate as 0 with their nonzero CP upper
  bounds carried alongside for uncertainty presentation.

The ADR-0037 length effect (segment upscaling) is applied by the
composition layer at the configured lambda_ac (default: the ADR-0037
primary 250 m, n_eff = 1).

### 5. The Uemura surface-curve seam (typed, validated, stubbed)

`surface_curves.py` defines the exact arrival interface for the two
pre-calculated mechanisms (class D until supplied):

* **Format**: long-form CSV (UTF-8, header row), one row per
  (segment, mechanism, scenario, stage) sample.
* **Columns** (exact names): `river` in {Tokachi, Satsunai}; `bank` in
  {right, left}; `kp` [float, the 0.2 km node]; `mechanism` in
  {overflow, fluvial_scour}; `scenario` in {historical, plus4K};
  `stage_m_msl` [float, T.P. datum = the M3/ADR-0021 m MSL datum];
  `p_f` [conditional failure probability, 0-1].
* **Validation on load**: known rivers/banks/mechanisms/scenarios; kp on
  the registry grid; stage strictly increasing and `p_f` non-decreasing
  within each (river, bank, kp, mechanism, scenario) group; p_f in [0, 1];
  at least two stage samples per group. Violations raise with the offending
  group named — the loader is the contract.
* **Datum note**: Uemura's curves must arrive in T.P. metres (m MSL). If
  they arrive crest-relative or in local datum, the conversion happens
  before the CSV, by the owner, with the offset documented — the loader
  deliberately refuses to guess.
* `synthetic_stub()` generates schema-exact fake curves so every consumer
  is tested today; results computed from stubs are stamped
  `surface_source='synthetic_stub'` and the CLI refuses to run stubs
  without an explicit `--allow-stub` flag.

### 6. Composition semantics

`composition.py` implements exactly the thesis equation
`P_sys(h) = 1 - prod_i (1 - P_i(h))` over the mechanisms present, with
per-mechanism dominance shares reported as the thesis requires (mechanism i
share at h; and at the annualized level, share of the annual P_f). Missing
mechanisms compose over the available subset and stamp which were present
(`mechanisms=['bep']` in BEP-only mode) — absence is visible, never
silently zero. Conditional independence given h is the thesis-fixed
assumption (Pol RESS 2023); the known non-conservative coupling exclusion
is carried as a documented limitation, not re-decided here.

---

## Alternatives Considered

### Alternative 1: extend `bayesian_reliability_updating` with Phase 3 modules
Pros: one fewer package. Cons: muddies the Schweckendiek-updating scope of
Phase 2, and RQ3/RQ4 consume Phase 2's *outputs* — the same artifact-boundary
argument that separated Phase 2 from Phase 1 (ADR-0036 precedent). Rejected.

### Alternative 2: parametric flood-frequency fit (e.g. GEV) on the peak stages
Pros: smooth return-period curves, extrapolation beyond the ensemble. Cons:
adds a fitted model with its own uncertainty where the thesis scope
explicitly stays inside the simulated d4PDF envelope ("does not seek to
extrapolate beyond these explicit warming boundaries"); the ensembles are
large (3,000/5,400 years). Rejected — empirical exceedance only.

### Alternative 3: nearest-neighbour BEP curves for all borehole-free segments by default
Pros: full-reach maps immediately. Cons: fakes site-specific reliability at
segments the thesis explicitly tiers as "bounded extrapolations with
deliberately inflated uncertainty"; the inflation machinery does not exist
yet. Rejected as default; `nearest` retained as an explicit, stamped option.

---

## Rationale

The package boundary mirrors the proven Phase 2 pattern (consume persisted
artifacts, hash-checked; zero physics reimplementation). The hazard side
reuses M3 verbatim, so every rating/band/proxy/datum rule that was validated
for Phase 1/2 carries over structurally. The two class-D inputs get typed,
validated, stub-tested seams so their arrival is a data drop plus one CLI
flag, not integration work.

---

## Consequences

* RQ3 becomes computable the day Uemura's CSV arrives; until then the
  BEP-only composition and the stub-driven test suite prove the plumbing.
* RQ4's hazard machinery (historical vs +4K stage-frequency and event
  characteristics per section) is computable **now** from the committed
  band workbooks; runs are minutes per node (workbook streaming dominates).
* New test modules cover the registry, seam validation, composition algebra,
  hazard statistics on synthetic ensembles, and the ADR-0024 evaluation
  policy pins; real-workbook tests skip on fresh clones (house pattern).
* `pyproject.toml` gains the package; CI unchanged (same three checks).
* The interpolated-prior extension for borehole-free reaches (thesis §3
  scope) remains future work and will need its own ADR (uncertainty
  inflation policy).

---

## References

- Thesis methodology: "Multi-Mechanism Integration: Series-System
  Joint-Probability Formulation"; "Climate Sensitivity Assessment";
  study-area chapter "Pre-Calculated Surface Failure Fragility Curves from
  Uemura (2025)" (msc-thesis repo).
- Uemura (2025) PhD thesis; Uemura et al. (2024) — local PDFs, curve data
  pending (class D).
- Pol et al. (2023), RESS — conditional-independence composition (thesis
  citation; not local).
- ADR-0019/0020 (M3 data contract), ADR-0021 (MSL datum), ADR-0023
  (shape-invariant climate axis), ADR-0024 (deliverable semantics),
  ADR-0036 (artifact-boundary precedent), ADR-0037 (length effect).
