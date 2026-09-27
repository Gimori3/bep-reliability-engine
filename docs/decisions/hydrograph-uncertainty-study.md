# Water-level and hydrograph uncertainty (Green Light item 5)

Status: completed companion study, 2026-09-27. No production default changes.
Part 1 was committed before computation as `588c7b8`; Part 2 is the outcome.

## Part 1: questions and protocol, before computation

The baseline is ADR-0054 matrix d70, integration step 225 s, the existing
as-if-undrained deliverable, plus item 3's measured-berm companion at KP 58.8
and KP 60.0 (drain credited at zero). Main-checkout raw data and results are
read-only. All new arrays belong in this worktree's results/hydrograph_uncertainty.

1. **Rating error.** Uemura's event-constant additive stage error is Normal
   with mean -0.160 m and standard deviation 0.294 m on the Tokachi. A
   peak convolution of the fixed-base canonical curve changes h(t) by
   epsilon*s(t), whereas the published error changes it by epsilon. They
   coincide only at the peak. Test both at the four sections, both geometry
   readings where applicable. The uniform offset can be evaluated exactly
   by lowering the exit reference by epsilon, keeping the original river
   record: every head difference is identical. This is an algebraic loading
   device, not a claim that the ground elevation is uncertain by that amount.
   Use 9-point normal Gauss-Hermite quadrature, check against 17 points on
   the cheap convolution, and 17-point direct evaluation if the 9-point
   direct annual estimate is not stable within 5%. Prior-side companion,
   with static and transient paired. Use 8192 rows selected without replacement
   from the persisted production population (seed 20260927), their exact L
   draws, and the full conditioning grid. Check representative zero-offset
   columns against the persisted failure matrices. Fit-free interpolation
   and explicit below/above-grid coverage. No fitted extrapolation.
   Prediction R1: the negative mean reduces annual piping at most sections,
   but spreading may increase the low-probability shoulder. R2: peak
   convolution understates the uniform-offset displacement somewhere by >5%.
   These are predictions, not acceptance thresholds for a production change.

2. **Event shapes.** Screen actual ensemble events, preserving each peak's
   own shape rather than mixing independent marginal peaks and durations.
   Stratify by peak-discharge quantiles at 0, .5, .8, .9, .95, .98, .99,
   .995, 1; sample four events without replacement per nonempty stratum,
   or census a stratum with fewer than four events. Historical is one
   climate stratum; warming is six prescribed SST strata weighted equally.
   Fixed seed 20260927, same event identities across sections. Compare the
   actual record against the pinned shape at that event's peak, using the
   same 8192 soil rows and L draws as above. Evaluate overflow on both
   records with the existing surface model and shared random draws; scour
   remains as documented and is checked on the sampled records. Report the
   stratified weighted annual probabilities, piping shares and climate
   ratios for both arms, and a paired within-stratum event bootstrap
   (2000 replicates). This interval measures this numerical event subsample,
   not the published member-block hazard-sampling uncertainty, soil
   uncertainty, or climate-model error. Prediction S1: the ensemble-shape
   annual piping is lower than the pinned upper-duration-quartile shape.
   S2: the climate ratio need not cancel. If the interval cannot distinguish
   a displacement, report it unresolved; do not enlarge the study after
   seeing a convenient sign. Check N=16384 on the highest-contributing
   sampled event per section/climate and both arms; report >5% residuals.

3. **Observation check.** Read Uemura's original Figure 3.17, printed p. 68,
   and the rainfall-dependent calibration on pp. 66 to 67. Audit whether the
   available event workbooks reproduce the published historical discharge
   summaries. Do not invent an observed stage series or treat synthetic
   ensemble years as dates paired to observed years. Record independently
   verified distributional summaries and all unresolved provenance limits.

The result is an uncertainty inventory and explicitly scoped sensitivity,
not a full predictive distribution. Production adoption requires an owner
decision. Inventory includes unquantified sources rather than assigning
them zero magnitude. Existing studies are read from their current evidence
JSON, not pre-ADR-0054 prose numbers.

## Part 2: findings and disposition, 2026-09-27

### Verdict

The primary method is a valid **conditional experiment**: soil fragility under
one specified waveform, integrated over simulated peak stages. It is not a
complete uncertainty propagation from climate forcing to toe head. The main
problem was fragmented documentation and two overclaims: that marginal shape
similarity established an unbiased climate ratio, and that the rating seam
had only been addressed by removing the overflow term. This study closes the
second direction as a prior sensitivity and screens actual ensemble waveforms.
It does not license replacing production annual probabilities.

All new results below are ADR-0054 matrix **prior**, adopted conductivity,
N=8192 exact shared production rows and original L draws, 225 s. Baseline
KP 58.8/60.0 remains as-if-undrained; the separate measured-berm companion
uses L=42/43 m and zero drain credit, matching item 3's current configuration.
The conductivity bracket applies to every absolute probability and comparison.
This study does not claim the drained baseline describes the present levees.

Evidence: `hydrograph-uncertainty-study.json` beside this note. It retains
event identities, stratum populations/weights, event probabilities, full-grid
rating results, interpolation coverage, input digests, numerical checks and
current inherited evidence. Compact JSON keeps the tracked file below 500 kB.

### Rating error

Uemura et al. (2024), pp. 70 to 71, equations (9) and (10), defines observed
minus rating-derived level and explicitly neglects discharge dependence and
within-event variation. The source workbook's Tokachi mean/std are
-0.1601260504/0.2937254970 m; the antecedent implementation's rounded
-0.160/0.294 m are retained. This term belongs to **overflow only**;
scour has no corresponding level-error draw. A uniform stage displacement is
therefore the source-consistent companion. Peak convolution is not identical
because it leaves the trough pinned: epsilon*s(t) rather than epsilon.
Lowering z_toe by epsilon is an exact algebraic evaluation device for the
uniform river shift, verified against directly shifted records; it is not
an added ground-elevation prior. No core module or Config is modified.

| Section / geometry | Annual piping factor, historical | +4K | System climate ratio, baseline to rating arm |
|---|---:|---:|---:|
| KP 57.4 baseline | 0.826 | 0.870 | 16.05 to 17.00 |
| KP 58.8 as-if-undrained | 0.864 | 0.877 | 5.77 to 5.86 |
| KP 60.0 as-if-undrained | 0.853 | 0.852 | 15.23 to 15.23 |
| KP 62.0 baseline | 0.832 | 0.878 | 14.19 to 15.51 |
| KP 58.8 measured berm | 0.861 | 0.877 | 6.78 to 6.91 |
| KP 60.0 measured berm | 0.953 | 0.856 | 29.88 to 26.91 |

Factors compare the same N=8192 population; their denominators are not the
100,000-row production posterior. The negative mean dominates annual piping
at every case (R1 supported). System composition changes only the piping
marginal, retains the primary overflow curve and conditional independence.
It is **not** joint integration over a common hydraulic error. No ordering
reverses; the largest absolute piping-share movement is 0.034. The static
and transient marginal curves, and thus conditional B and Delta-beta, change:
at attainable baseline grid levels with >=30 failures and survivors in both
unshifted branches, B is multiplied by 0.72 to 1.09 and Delta-beta decreases
by 0.035 to 0.184. This is a loading sensitivity, not common-mode cancellation.

All six cases passed zero-offset comparisons with persisted static/transient
flags at a shoulder and high grid level, Numba/Numpy flag equality there, and
the uniform-shift identity. Direct 17-point versus 9-point quadrature changes
annual piping by <0.12% at the four baseline sections, and at most 1.83% in
the historical KP60 measured-berm case. Running 17 points at all sections
strengthened the preregistered minimum check without selecting by result.
Peak convolution at 33 points differs from the uniform-offset annual result
by <=1.42% at the baselines and 6.24% at historical KP60 measured berm. Thus
R2 clears 5% only in the least resolved companion tail; no broad claim that
convolution is numerically poor follows. All unshifted peaks lie within the
grid. Soil-tail precision is separate from quadrature convergence.

No random-error replay is added to Phase 2. Its flood-trace anchor already
conditions on observed information rather than the simulated-event rating
residual. Adopting a new posterior requires consistent uncertain loading in
the survival likelihood and the fragility, and defensible error dependence
across event times and mechanisms. The existing anchor/datum brackets remain
the appropriate identified epistemic alternatives.

### Ensemble waveforms

The screen retains actual peak-waveform dependence, including each event's
base stage, rising and falling limbs and multiple peaks. It is not an isolated
duration perturbation. Historical: 32 events; warming: 192 events in six
equally weighted SST patterns. Four draws per nonempty peak-rank stratum,
without replacement, with finite-population weights; same soil rows and
event IDs across cases. Both arms reevaluate surface models with shared
N=10,000 draws, overflow's existing rating term and **USACE scour conversion**.
The report driver recomputes every scour result explicitly; preliminary
KP57.4/58.8 cache summaries used the retired default conversion and must NOT
be cited. The final evidence supersedes those summaries. Accumulated scour
does not reach the failure criterion on the sampled records; this does not
mean bed erosion never engages. Event-wise system composition precedes
annual averaging.

| Section / geometry | Historical system C to A | +4K system C to A | Climate ratio C to A |
|---|---:|---:|---:|
| KP57.4 baseline | 2.32e-4 to 1.72e-4 | 7.28e-3 to 6.00e-3 | 31.4 to 34.8 |
| KP58.8 as-if-undrained | 6.85e-3 to 5.25e-3 | 3.99e-2 to 3.26e-2 | 5.82 to 6.20 |
| KP60.0 as-if-undrained | 1.73e-4 to 1.08e-4 | 4.05e-3 to 2.91e-3 | 23.5 to 27.0 |
| KP62.0 baseline | 5.23e-4 to 3.35e-4 | 1.17e-2 to 1.02e-2 | 22.4 to 30.4 |
| KP58.8 measured berm | 3.36e-3 to 2.45e-3 | 2.40e-2 to 1.89e-2 | 7.15 to 7.69 |
| KP60.0 measured berm | 2.30e-5 to 1.24e-5 | 1.28e-3 to 8.78e-4 | 55.7 to 71.0 |

C = canonical shape rescaled to selected peak, A = actual event. S1 is
supported at every case: annual piping falls. System falls 23 to 38%
historically and 13 to 28% under warming at baseline sections. No point
ordering reverses; KP62 warming share falls 0.479 to 0.410, remaining
overflow-led. The 2000-replicate paired event-bootstrap factor bands exclude
1 in all cells, but they are **descriptive numerical subsampling bands**, not
hazard or total uncertainty intervals. With four events per bin their
coverage is not established. Climate-ratio point estimates increase (S2
does not cancel), refuting any deduction of the opposite sign from marginal
warming duration alone. Some paired bands exclude zero but do not establish
a correction to production.

The canonical reference itself reveals insufficient historical integration:
KP57's sampled 2.32e-4 is far from its full-ensemble prior 4.98e-4 and its
sampled ratio 31.4 is far from about 15.3. The actual-waveform ratio's
descriptive interval is 17.2 to 143.4 there. At N=16384 the largest weighted
piping-contribution event changes by <=5.11% at the four baselines; historical
KP60 measured berm changes 12.0% (C) and 6.0% (A). These >5% residuals are
reported, not hidden by enlarging N after seeing the sign. The finite screen
closes a meaningful sensitivity gap but not a converged ensemble integration.
Shape effects on full conditional B/Delta-beta curves and on the posterior
were not recomputed. The observed 2016 replay is unchanged by definition.

### Observation check

Read local `Uemura_Fumihiko.pdf` printed pp. 66 to 68; Figure 3.17 is PDF
page 79 and was also inspected as an image. It compares observed Obihiro
annual maxima, 1961 to 2010 (N=50), with the rainfall-dependent calibrated
experiment (N=3000). Quantiles [min, p05, median, p95, max], m3/s:

* Observed: [190, 285, 647, 2752, 4952].
* Published simulation: [95, 274, 746, 2442, 6300].
* Supplied HPB workbook: [88.91, 236.522, 652.74, 2776.916, 7581.37].

The supplied median and p95 are each about 0.9% above observed, but the export
does not reproduce the published simulated summaries. No unsupported cause
is assigned to this discrepancy. The five calibration floods overlap the
observation period; no raw observed annual-max series is available locally.
Consequently this supports discharge-distribution plausibility only, not
independent local stage-frequency, duration or rare-tail validation. Synthetic
years cannot be matched to observed dates as if they were a gauged record.
The source also contains a 2016-only-calibration median inconsistency:
Figure 3.17 reports 2542, adjacent prose 2452 m3/s. The existing thesis's
2542 is supported by the figure; no conclusion here relies on that value.

### Complete inventory and available magnitudes

The thesis inventory is in Appendix D, with a pointer in Chapter 4 and the
judgement in Chapter 8. In this record, 'unquantified' is not zero:

| Loading-chain source | Treatment and location | What is measured / not measured |
|---|---|---|
| Climate internal variability / flood amplitude | Represented aleatory HPB/HFB peak distributions, Phase 3 | Annual probabilities and ratios average all 3000/5400 peaks; conditional curves fixed |
| Finite climate ensemble | Member-block bootstrap within prescribed SSTs, annualisation-hazard-sampling-uncertainty.json | Current matrix/posterior system relative half-widths 30 to 62% historical, 9 to 21% warming; conditional curves, B, Delta-beta and rejection fixed |
| Six SST patterns | Structural bracket, same evidence | Warming annual system max/min 3.16 to 6.23; never absorbed into the member-sampling interval |
| Other climate models/pathways | Excluded | No probability distribution or bound; +4K not a demonstrated bound on +2K |
| Downscaling / rainfall bias / spatial resolution | Excluded model discrepancy | No separate quantified effect on stages, durations, annuals or ratios |
| Tank-model parameters, calibration and runoff structure | Single rainfall-dependent relation; source pp.66 to68 | Published-versus-export plausibility check above; no propagated posterior or independent tail validation |
| Annual-maximum-rainfall event extraction | Fixed 15-day window | Other events, long antecedent histories and inter-event states unavailable; duration-driven annual maximum and ratio effect unquantified |
| Band discharge transfer / local hydraulic model | Node ratings at 200m; KP62 uses KP61.8 band, ADR0019 | No section gauge between Obihiro and Memurobuto; roughness, rating hysteresis, extrapolation and spatial error not separately bracketed |
| Rating residual | Stochastic in overflow only; new piping prior companion above | Conditional probabilities/B/Delta-beta and annual marginals measured; not joint common-error composition, not new posterior |
| Future river geometry / hydraulic stationarity | Fixed present ratings | Nonstationary ratings and future morphological change excluded; magnitude unquantified |
| Hydrograph waveform / base stage / peak dependence | Fixed primary canonical, alternate-shape study and actual-event screen | Current alternate lowers midcurve 25 to38%; new annual sensitivity above; full shape-integrated posterior/B/Delta-beta excluded |
| Hourly source resolution | Fixed observation/simulation cadence, interpolation to225s | Numerical timestep studies do not quantify missing subhourly forcing |
| 2016 observation and anchor reconstruction | Trace-versus-rating epistemic bracket, ADR0035 | Matrix N100k rejection (%) trace/rating: KP57 .016/0; KP58 3.813/4.180; KP60 .226/.001; KP62 0/.005 |
| Exit datum | +/-0.3m epistemic bracket, adr0046-ztoe-companion.json | Matrix replay rejection (%) low/high toe: KP57 .351/0; KP58 9.426/.967; KP60 .955/.029; KP62 0/0; Phase1/posterior effects retained in source JSON |
| Installed drainage / berm / landside head | Baseline uncredited drain; item3 measured-berm companion | Geometry consequences owned by item3; no new drain physics or time-varying landside water series |
| River-to-toe pressure translation | Instantaneous M4 screened by ADR0032; soil/blanket priors and brackets elsewhere | Elastic response relative to rising limb measured; field translation discrepancy retained, not an independent random stage-error term |
| Design level / grid / canonical normalization | Deterministic definitions | No invented uncertainty prior; coverage/interpolation are numerical issues, not observed-stage noise |

The current inherited JSON is authoritative for the old companion magnitudes.
The older seam study's prose describes a pre-ADR0054 ordering reversal that
no longer occurs. Removing the overflow term moves annual system by <=1.08
and shares by <=0.041 at the four current sections, with no reversal. The
older hazard prose likewise had stale 29 to58% / 8 to19% widths and 3.0 to5.7
SST spread; the thesis uses the current evidence values above.

### Reproduction, validation and close-out

Drivers: `scripts/hydrograph_uncertainty_study.py` and
`scripts/hydrograph_uncertainty_report.py`. From a checkout containing the
tracked inputs, point `--data-repo` to the original checkout with ignored data
and production H5s. Run `rating` at orders9 and17 and `shapes` at order9
(the shapes filename uses that CLI tag) for each KP, adding `--berm` for the
two companions, then run the report driver with the same `--data-repo`.
No generated config is edited; all loading variants are evaluated in memory.
Raw arrays and PDF extracts are under worktree
`results/hydrograph_uncertainty/`, archived outside the removed worktree at
`D:/repositories/bep-g5-evidence/hydrograph_uncertainty/`.

Tests `tests/test_hydrograph_uncertainty.py` distinguish event-wise union from
composition after averaging, preserve prescribed SST weights despite unequal
test counts, verify population weights and no replacement, and show why
peak shift differs from whole-record shift. Full validation: 1079 passed,
45 skipped; ruff and black clean. The new drivers are explicitly classified
as manual studies in the campaign because its stages do not create their
event arrays or provide their original ignored workbook/berm inputs.

Disposition: retain all production curves, defaults and Phase 2 API. No new
knob, prior, external citation or owner decision is required for these scoped
companions. A converged joint peak-waveform integration, calibrated temporal
rating-error process, consistent posterior replay and shared-error system
composition would be separate production work requiring the owner's choice.
Item6 can build on this inventory; item3's drainage physics and items1/2's
gradation/criterion choices were not reopened.
