# Water-level and hydrograph uncertainty (Green Light item 5)

Status: pre-registered companion study, 2026-09-27. No production default changes.

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
