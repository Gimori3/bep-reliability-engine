# ADR-0034: Additive Phase 1 Surface Extensions for the Phase 2 Survival Replay

Date: 2026-07-12

## Status
Accepted

---

## Context

Phase 2 (Bayesian reliability updating, package
`bayesian_reliability_updating`) must re-run the Phase 1 M8 evaluator over
every prior row against the observed 2016 hydrograph under assumptions
identical to the Phase 1 sweep (spec section 8 point 4). Three things the
as-built Phase 1 surface did not expose stood in the way:

1. The vectorized production path `evaluator.evaluate_batch` deliberately
   returns only the two boolean failure columns (spec section 12 failure
   mode 6). The Phase 2 replay needs, for every row, the continuous
   margins (Z_static, Z_transient), the terminal pipe length, the
   uplift-plus-heave latches (for the stricter optional acceptance
   criterion) and t_uh, at production speed. The scalar
   `evaluate_realization` returns all of them but integrates one Python
   row at a time: at N = 1e5 rows times ~1.2e4 timesteps of the 225 s
   2016 replay, a scalar loop is hours, the batch kernels seconds to
   minutes.
2. The stochastic seepage length L_j that paired with theta row j in the
   sweep is deliberately not persisted in the FragilityResult; it is
   regenerated from `config.mc.seed` through a private SeedSequence salt
   in `run.py`. Phase 2 must obtain the exact same vector without
   copying the seed recipe.
3. The Phase 2 posterior-fragility verification mode must re-evaluate
   accepted rows on the exact per-level loading records the sweep used;
   the record construction lived in private `run.py` helpers.

## Decision

Three additive public entry points, no frozen contract touched:

1. `evaluator.evaluate_batch_diagnostics(...) -> BatchDiagnostics`: the
   single batch M8 implementation. `evaluate_batch` now delegates to it
   and returns the same two flag columns as before, so exactly one batch
   code path exists and the two entry points cannot drift.
   `BatchDiagnostics` is the array twin of `EvaluationResult` (minus the
   trajectory): Z_static, Z_transient, l_e_final, H_c, H_c_transient,
   l_c, lambda_in, r_e, t_uh, both failure flags, both initiation
   latches, all shape (N,).
2. `run.seepage_length_samples_for_config(config)`: public regeneration
   of the run's exact stochastic-L draw (delegates to the existing
   private sampler; returns None when L is deterministic, exactly like
   the run).
3. `run.conditioning_hydrographs_for_config(config)`: rebuilds the
   sweep's per-level loading records (canonical shape loaded once,
   datum-guarded, ADR-0030 timestep refinement applied), in grid order.

The exact-`__all__` interface pin in `tests/test_evaluator.py` is extended
by the two new evaluator names; everything else in the Phase 1 suite is
untouched and green.

---

## Alternatives Considered

### Reuse `gsa_qoi.evaluate_qoi_batch` for the Phase 2 diagnostics
Pros: already exists, drift-guarded. Cons: it exposes neither t_uh nor
the uplift/heave latches (needed for the stricter acceptance variant), its
docstring explicitly scopes it to GSA drivers ("the Phase 2 replay
continues to use M8 directly"), and extending it would create a second
diagnostics-bearing mirror of M8 next to the one being added here.

### Scalar `evaluate_realization` loop for the replay
Pros: zero Phase 1 changes; the documented Phase 2 idiom. Cons: runtime
(hours at production N for the 225 s replay); the batch path exists
precisely because the sweep needed it, and it is pinned bit-identical to
the scalar loop, so nothing is gained by the slow route. The scalar API
remains the frozen contract and is still used for the per-row trajectory
tracing of rejected realizations.

### A third M8-mirroring adapter inside the Phase 2 package
Pros: zero Phase 1 changes. Cons: violates the zero-physics-
reimplementation invariant in spirit: a mirror of the shared preamble and
branch dispatch living outside Phase 1 is exactly the drift risk the
mission forbids; the sanctioned route is a minor additive Phase 1 change.

---

## Rationale

The refactor keeps a single batch implementation (delegation, not
duplication), so the bit-identity guarantee of the production path
transfers to the diagnostics path by construction and is additionally
pinned row for row against the scalar evaluator by
`tests/test_evaluator_batch_diagnostics.py` (including the stochastic-L
pairing). The two `run.py` helpers expose existing private behavior
unchanged, keeping seed recipes and record construction in exactly one
place each.

---

## Consequences

- Phase 2 evaluates through M8 only; no physics or orchestration is
  mirrored outside `bep_reliability_engine`.
- `evaluate_batch`'s public contract, return type and numerical output
  are unchanged (the full Phase 1 suite passes unmodified apart from the
  extended `__all__` pin).
- The L draw and the conditioning-record construction have exactly one
  implementation each, now reachable publicly; any future change
  propagates to Phase 2 automatically.
- Memory: `BatchDiagnostics` adds ~13 (N,) arrays (~10 MB at N = 1e5),
  negligible next to the failure matrices.

---

## References

- Spec section 8 (Phase 2 handoff), section 12 failure mode 6.
- ADR-0011 (M8 orchestration contract), ADR-0029 (batch backends),
  ADR-0030 (integration timestep).
- `tests/test_evaluator_batch_diagnostics.py` (the pin tests).
- Mission invariant 1 (zero physics reimplementation; surgical additive
  Phase 1 changes documented here).
