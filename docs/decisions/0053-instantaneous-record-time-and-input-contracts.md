# ADR-0053: Instantaneous record time and public input contracts

Date: 2026-09-15

## Status
Accepted. Corrects the record-to-integrator boundary and trajectory interpretation
in ADR-0010/0011; supersedes ADR-0014 activation claims for the public pipeline.
It does not change the forward-Euler scheme or either driving head.

---

## Context

For N instantaneous observations at t[0] through t[N-1], there are N-1
intervals. Forward Euler evaluates the load and state at each interval start
and stores the updated state at its end. Conversely N explicitly supplied
left-endpoint interval loads describe N updates. These are different interfaces.
A constant postcritical equilibrium head gives the independent analytic check
l(T) = min(L, l_ini + v T). An active last observation discriminates the two
interpretations; a last observation below the toe is an inert extra update.

The pre-correction record evaluator supplied all N observations to the N-load
kernel and associated N end states with the N observation times. Thus its final
state could include an extra interval, and its trajectory omitted the initial
state. A completing step was reported one timestep early for zero-origin records.
The compound-event demonstration already uses interval loads correctly.

---

## Decision

- M3 records denote instantaneous, uniformly spaced observations. A single
  observation has zero duration. Stages, optional duck-typed time arrays, peak
  and native timestep must be finite; timestep must be positive and supplied
  times must match it. Validate public boundaries, including both batch backends.
- M7 retains its explicit N interval-load interface and N interval-end states.
  M8 passes record.h[:-1] and prepends the initial state to stored trajectories.
  The terminal observation still records uplift/heave onset, without progression.
  Breach times are elapsed times at the first completing end state.
- Direct record callers follow the same conversion. Sustained-duration drivers
  use an initial node plus one node per intended interval. No universal replacement
  of timestep loops is justified.
- Public aquifer_lag_active=True is rejected, including when storage is supplied.
  Production metadata names the instantaneous head model and time convention.
  Low-level research head classes remain available; this is no validation of a
  lagged aquifer study. Existing instantaneous results remain readable with their
  original provenance. Old active-lag labels do not establish lagged physics.
- This is a demonstrated baseline contract correction, not a default-off
  sensitivity. Configuration hashes of supported defaults remain unchanged;
  new output metadata identifies the corrected source convention. Historic
  arrays must not be relabelled as reruns.

---

## Alternatives Considered

Changing every M7 loop would break legitimate interval-load callers, including
compound events. Giving an instantaneous final observation a duration changes
the stated record span. Enabling a new lagged aquifer pathway would require a
separate physical validation study. Keeping the defects behind default-off
switches would leave the baseline contract incorrect. These alternatives are
rejected in favour of explicit boundary conversions and unsupported-option errors.

---

## Rationale

The independent constant-rate relationship distinguishes time interfaces without
assuming that a self-consistent implementation proves the physics. Production
invariance requires actual loading and sample evidence, not the toy experiment.
Preserving the interval kernel minimizes impact on valid callers.

---

## Consequences

### Verification and propagation

Analytic regression tests cover active/inactive terminal observations, zero-span
records, exact initial/end states, crossing time, refinement, nonzero time origin,
nonfinite duck-typed inputs and NumPy/Numba evaluation. Field drivers are rerun.
The companion endpoint proof reconstructs actual configuration/sample/loading
inputs and records their hashes. It proves final-state invariance only where
finite positive inputs and final loading below the toe establish an inert step.
It cannot establish invariance for an active sustained hold. That requires a
separate production-sample recomputation. ADR-0040's finite Euler barrier-step
caveat remains separate and is not resolved by correcting observation times.

Numerical and delivery verification is recorded in the dated S01 evidence report.

### Primary station attribution correction

Inspection on this date of the local primary station workbook
Uncertainty_HQrelation.xlsx, sheet TokachiRiv._Obihiro, confirms KP 56.73.
The first observation has coefficients (87.41, -31.17); later observations
include (135.36, -32.62), matching the adopted committed station rating.
The September 13 first-row attribution in ADR-0035 and phase2_report is
superseded by this clarification. The adopted gauge node and rating do not change.
The confidential workbook remains local.


---

## References

- ADR-0010, ADR-0011 and ADR-0014: prior interface contracts.
- ADR-0035: observed-event construction and its dated gauge amendment.
- ADR-0039 and ADR-0040: timestep convergence and barrier-step caveat.
- `tests/test_time_contract.py`: independent analytic and boundary regressions.
- `adr0053-time-contract-evidence.json`: dated propagation evidence.
