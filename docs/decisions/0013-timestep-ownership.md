# ADR-0013: Δt Ownership Between Config (M1) and the Hydrograph Record (M3)

Date: 2026-06-17
Status: Accepted

## Context
Spec §1 lists the integration timestep **Δt** among M1 `config`'s "timestepper settings." But two already-committed facts point the other way:

- **M8 sources dt from the record.** `evaluate_realization` reads `dt_s = float(hydrograph.native_dt)` (`evaluator.py`, its own ambiguity #2) and passes it to M7 `integrate_progression`. The `evaluate_realization` signature is frozen (ADR-0011) and carries no config/Δt argument.
- **ADR-0010 already declared `native_dt` authoritative.** It pins `native_dt` as "the authoritative integration timestep," with `h` guaranteed uniformly sampled at that spacing, and explicitly rejected deriving dt from `diff(t)`.

Spec §13 reinforces this physically: "Timestep: **Native d4PDF resolution**, validated by Δt/2 test on a flashy rising limb," and spec §1/§11 make M3 the recorder of the native temporal resolution against which the rising-limb check is run. So the *production* timestep is fundamentally a property of the loaded hydrograph, not a free config knob — yet §11's Δt/2 convergence test and any deliberate coarsening (e.g. to 600 s) need a way to set a timestep that differs from the native one. M7 already supports this directly: `tests/test_progression.py` resamples onto an explicit `dt_s` grid and calls `integrate_progression(dt_s=…)`, so per-call dt control exists at the kernel; the only open question is **who owns the dt that reaches M8 in a production run.**

---

## Decision
**Keep `native_dt` authoritative at the M8 boundary; give config ownership only of the resolution/convergence *policy*, applied upstream of M8 — not a second dt field consumed inside the frozen M8 signature.**

Concretely:
- The per-event authoritative Δt at evaluation time **is** `hydrograph.native_dt` (status quo; M8 and ADR-0010 unchanged).
- M1 config owns a small **resolution policy**: the §11 Δt/2 convergence-test settings (whether to run it, the <1% acceptance threshold, the worst-case θ corner) and an **optional global coarsening factor / target Δt** that the M3 loader or orchestrator applies *when it builds/resamples the record*, so the record handed to M8 already carries the intended `native_dt`. Config never hands M8 a Δt that competes with the record's.

This reads spec §1's "Δt in config" as satisfied by config setting the *policy and any resampling*, while the single authoritative value at the M8 boundary remains the record's `native_dt`.

**Build-state note (verified 2026-06-17).** M3 `hydrographs.py` is an empty stub. The coarsening/resample hook described above therefore **does not exist today**; it is a *requirement levied on M3 when it is built*, not behaviour that works now. Until M3 exists, the operative Δt is whatever native resolution a record stand-in carries, and the §11 Δt/2 test is exercised only at the M7 kernel level (`tests/test_progression.py`), not through a config policy.

---

## Alternatives Considered

### Alternative 1 — Record owns Δt outright; config has no Δt at all (pure status quo)
- Pros: simplest; matches ADR-0010 and the §13 native-resolution default; M8 untouched; single source of truth.
- Cons: literal-reads spec §1 as wrong (Δt is named a config field); leaves the §11 Δt/2 test and coarsening with no config-level home, only ad-hoc per-call dt at M7.

### Alternative 2 — Config owns Δt; M8 reads it and `native_dt` becomes informational
- Pros: literal compliance with spec §1.
- Cons: contradicts ADR-0010's authoritative `native_dt`; cannot reach M8 without breaking the frozen signature (ADR-0011); reintroduces the silent-disagreement risk ADR-0010 rejected (config Δt ≠ record spacing); demotes M3's resolution record to a dead field.

### Alternative 3 (accepted) — Record authoritative at the boundary; config owns resolution policy + optional upstream resampling
- Pros: no M8 signature change; honours spec §1 (config *can* set the operative Δt via the coarsening/resample policy) and §13 (native default) and §11 (Δt/2 test expressible) simultaneously; single authoritative dt where it matters; consistent with ADR-0010.
- Cons: "config owns Δt" becomes "config owns the policy that determines the record's Δt," a layer of indirection that must be documented so it is not mistaken for a config field M8 reads; the resample hook is a forward requirement on unbuilt M3.

---

## Rationale
The timestep is physically a property of the loading record (native d4PDF resolution), which is exactly why ADR-0010 made `native_dt` authoritative and why §13 names the native resolution the default. Putting a competing Δt inside config and feeding it to M8 would either break the frozen Phase 2 surface or create two sources of truth for one number. Routing config's legitimate control (convergence policy, deliberate coarsening) through the record-building step preserves one authoritative dt at evaluation time while still letting a run dictate resolution — which is all spec §1 actually needs.

---

## Consequences
- M8 and ADR-0010 are unchanged; the `evaluate_realization` signature stays frozen (ADR-0011).
- M1 `config` gains resolution-policy fields (Δt/2-test on/off, threshold, worst-case θ) and an optional target-Δt/coarsening factor, **recorded in metadata** for reproducibility.
- **Requirement on M3 (unbuilt):** when `hydrographs.py` is implemented it must apply config's coarsening/target-Δt at record construction, emitting a record whose `native_dt` equals the operative Δt and whose `h` is uniformly sampled at that spacing (per ADR-0010). This is the single place the config policy becomes live; it is not yet wired.
- The §11 timestep-convergence test is run at the orchestration layer by resampling and re-evaluating at Δt and Δt/2; it does not require an M8 dt argument. Today it is reachable only via direct M7 calls until the orchestrator and M3 exist.
- If a future need arises to drive M8 at a Δt decoupled from any record (e.g. synthetic-hydrograph fragility), that requires a superseding ADR touching the frozen signature — out of scope here.

---

## References
- Phase 1 architecture spec §1 (M1, M3 timestepper settings), §11 (Δt/2 convergence test, native-resolution check), §13 (native d4PDF resolution default).
- ADR-0010 (HydrographRecord schema; `native_dt` authoritative), ADR-0011 (frozen M8 signature).
- `bep_reliability_engine/evaluator.py` (ambiguity #2), `bep_reliability_engine/progression.py` (`integrate_progression(dt_s=…)`), `tests/test_progression.py` (explicit-dt convergence cases); `bep_reliability_engine/hydrographs.py` (empty stub as of 2026-06-17).
