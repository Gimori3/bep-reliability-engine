# ADR-0041: Opt-In Equilibrium End-Factor Override for the H_eq-Conservatism Isolation

Date: 2026-07-17

## Status
Accepted

---

## Context

ADR-0009 established the fourth, non-temporal component of the static-transient gap:
Pol SIE 2024 Eq. (11) anchors the equilibrium curve at H_eq(L) = 0.9·H_c, an
intentionally conservative fit that inflates the progressive-phase rate ≈1.95× at the
L = 3 m in-domain anchor (Pol-confirmed qualitatively, field-scale magnitude open).
Spec §12 fm4 and ADR-0017 both note the isolation "remains an unthreaded module
constant" (`progression.EQUILIBRIUM_END_FACTOR`) whose wiring, if needed, "would follow
this same opt-in-override pattern".

Stage 6.6 (ADR-0040) needs it: the sustained-head indicator is provably end-factor
invariant, so the H_eq-conservatism component lives entirely inside the temporal step
of the comparator ladder and can only be bounded by re-running the real-hydrograph
transient with the conservatism removed (end factor 1.0 flattens the descending branch
at H_c, the DgFlow-faithful effective equilibrium being ≈1.00-1.04·H_c per ADR-0009's
inversion).

---

## Decision

Add a keyword-only `equilibrium_end_factor: float | None = None` to:

- `progression.equilibrium_head` (the public kernel),
- `progression.integrate_progression` (replaces the constant in the hoisted
  `falling_slope`; everything else untouched),
- `evaluator.evaluate_batch_diagnostics` and `evaluate_batch` (threaded through to M7).

`None` (the default everywhere) resolves to the module constant
`EQUILIBRIUM_END_FACTOR = 0.9` through the identical expression, so an un-overridden
call is **bit-identical** to prior behavior (pinned by test). The override:

- is **not** a `Config` field — analysis-only, per the ADR-0040 alternatives ruling;
  Eq. (11) as published remains the one production equilibrium curve (ADR-0009);
- is **refused on the numba backend** (`ValueError`): the JIT kernel hard-codes the
  constant, and the sensitivity has no performance case;
- does **not** touch the frozen scalar `evaluate_realization` (Phase 2 contract,
  ADR-0011): Stage 6.6 consumes the batch path only.

Setting 1.0 removes the designed-in conservatism bound-style (H_eq(l ≥ l_c) = H_c,
descending branch flat); it is a bound, not a calibrated replacement — DgFlow's
effective ≈1.01-1.04 would make failures rarer still by a sliver.

---

## Alternatives Considered

### Substitute a DgFlow-calibrated equilibrium curve
Rejected by ADR-0009 already: Eq. (11) is the published SIE 2024 reliability-model
choice the spec adopts; a replacement is out of scope. This ADR adds an opt-in bound,
not a replacement.

### Monkeypatch the module constant in the study driver
Rejected: silently global, thread-unsafe under joblib, invisible in metadata, and
bypasses the hoisted `falling_slope` inside the fast path (a patched constant after
import would not even take effect there consistently).

### Thread through `Config` like `alpha_exponent_transient`
Rejected for now: ADR-0017's config threading was justified by a run-from-config
decomposition; Stage 6.6 drives the evaluator directly and records the override in its
own result metadata. Config threading can follow later, additively, if a config-driven
run ever needs it.

---

## Rationale

Exactly the ADR-0017 additive-override pattern: default-None keyword, bit-identical
baseline, opt-in relaxation of one published constant for one named gap component,
recorded in the consuming study's metadata.

---

## Consequences

- `EvaluationResult`/`BatchDiagnostics` field sets unchanged (no new diagnostics; the
  override affects only the transient trajectory/flags).
- Tests: default-None bit-identity against pre-change behavior; 0.9-explicit equals
  default; 1.0 changes only post-l_c behavior (rising branch pinned); numba refusal.
- Stage 6.6 gains comparators C4c/C4d (ADR-0040), turning the ADR-0009 open component
  into a measured indicator-level bound at field scale (per level, with CIs) for the
  first time.

---

## References

- ADR-0009 (H_eq-conservatism component; 0.9 anchor provenance), ADR-0017 (the
  opt-in override pattern), ADR-0029 (backend split), ADR-0040 (consumer).
- Pol SIE 2024 Eq. (11) and §2.3; Pol, Noordam & Kanning (2024) CG24 (DgFlow).
- `bep_reliability_engine/progression.py` (`EQUILIBRIUM_END_FACTOR`).
