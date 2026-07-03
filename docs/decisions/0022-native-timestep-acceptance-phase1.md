# ADR-0022: Acceptance of the Native 3600 s Timestep for Phase 1 Fragility; Phase 2 Replay at Native/2

Date: 2026-07-03
Status: Accepted (recorded at the project owner's direction, 2026-07-03 health-assessment finding 4)

## Context

The production integration timestep is the d4PDF native resolution of 3600 s:
ADR-0019 §6 fixed the source data at 1 hour ("final; no finer timestep data
exists"), ADR-0010/0013 made the record's `native_dt` authoritative at the M8
boundary, and the canonical-shape records built by M3 carry `native_dt =
3600.0` through to the M7 forward-Euler loop.

Spec §11 requires a Δt/2 convergence test "on a genuinely flashy d4PDF
rising-limb event" with the high-progression-rate θ corner, with l_e agreement
within 1%. As built, that requirement was only partially discharged:

- The kernel-level gate
  (`tests/test_progression.py::test_timestep_convergence_on_steep_rising_limb_worst_case_theta`)
  validates 600 s against 300 s on a synthetic limb — written when 600 s was
  the presumed field default, before ADR-0019 fixed the native resolution at
  3600 s. Nothing validated 3600 s.
- The config policy fields (`timestepper.convergence_test`,
  `convergence_threshold`) have no engine consumer, and the ADR-0013
  resample-at-record-construction hook is implemented only on the synthetic
  stub path (`target_dt_seconds`); canonical d4PDF records keep native
  resolution.

The 2026-07-03 health assessment ran the missing check on real canonical
shapes (`HPB_m064_1987`) scaled to the top conditioning levels, N = 4000
realizations from the production priors, comparing dt = 3600 s against
linear-interpolated 1800 s and 900 s grids:

| Section / level | P_f,trans 3600 s | 1800 s | 900 s | breach-flag mismatch (3600 vs 1800) |
|---|---|---|---|---|
| KP 57.4, h = 43.25 | 0.04025 | 0.03975 | 0.03975 | 0.050% |
| KP 62.0, h = 50.50 | 0.00000 | 0.00000 | 0.00000 | 0.000% |

Per-realization final pipe length l_e (3600 s vs 1800 s): median difference
≈ 0.9–1.0% (at the spec §11 threshold), p95 ≈ 1.3–2.1%, individual maxima up
to ~50% for realizations near the breach boundary. The 1800 s vs 900 s
differences halve again (median ≈ 0.4–0.5%), consistent with first-order
convergence.

## Decision

1. **Phase 1 fragility runs integrate at the native 3600 s.** The acceptance
   is at the fragility-probability level, on the measured evidence above:
   halving the timestep changes P_f,trans by ~1.3% relative at the most active
   level tested and flips ≤ 0.05% of breach flags — far below the Monte Carlo
   noise of the tail levels concerned (spec §11 CoV, now computed per run in
   `metadata['mc_convergence']`). The spec §11 per-realization <1% criterion is
   met at the median but not in the tail (p95 ≈ 2%, maxima ~50% near the
   breach boundary); this is explicitly accepted for Phase 1 because the
   deliverable is P(fail | h_i) over the population, where boundary-realization
   flips are sub-noise.

2. **Phase 2 per-realization replay against h_2016 runs at native/2 =
   1800 s.** The Accept–Reject filter keeps or rejects *individual* rows, so
   the per-realization l_e tail sensitivity that is sub-noise for Phase 1 is
   load-bearing for Phase 2. The 2016 record is resampled (linear
   interpolation) onto the 1800 s grid at record construction, and the record's
   `native_dt` is set accordingly — consistent with ADR-0013 (the record stays
   the single authoritative Δt source at the M8 boundary; the frozen M8
   signature is untouched).

3. **Forward requirement:** decision 2 requires the ADR-0013
   resample-at-record-construction hook on real (M3-built) records, which today
   exists only on the synthetic-stub path. Implementing it (in M3 or the
   record-building seam, per ADR-0013's "config owns the policy, the record
   carries the Δt") is a precondition for the Phase 2 replay, not for the
   Phase 1 sweep.

## Consequences

- No Phase 1 engine change: the native 3600 s path is the as-built default.
  The kernel Δt-convergence test remains at 600↔300 s as a scheme-level guard;
  a 3600 s orchestrator-level gate can be added when the resample hook lands
  (the config `convergence_test` fields then gain their consumer).
- `docs/phase2_interface.md` §3.1 records the 1800 s replay requirement for
  Phase 2 implementers.
- The measured convergence numbers above are the documented acceptance
  evidence; if the rate law, the H_eq curve, or the hydrograph source changes
  materially, the check should be re-run before relying on this ADR.
- The ±(1–2)% per-realization l_e band at 3600 s is small against the
  dominant uncertainties (C_e·k_aq tail, H_eq conservatism ≈ 1.95×, ADR-0009)
  but should not be forgotten in any analysis that reads individual
  trajectories from a Phase 1 run (e.g. visualization subsets).

## References

- Spec §11 (timestep convergence test), §13 (native d4PDF resolution default).
- ADR-0010 (`native_dt` authoritative), ADR-0013 (Δt ownership; the resample
  hook), ADR-0019 §6 (hourly native resolution, final).
- 2026-07-03 health assessment, finding 4 (measured convergence numbers,
  N = 4000, real canonical shapes at KP 57.4 / KP 62.0).
- `tests/test_progression.py::test_timestep_convergence_on_steep_rising_limb_worst_case_theta`
  (kernel-level 600↔300 s gate).
