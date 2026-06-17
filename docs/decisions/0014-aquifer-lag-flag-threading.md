# ADR-0014: Threading the Aquifer-Lag Flag from Config through M8 to M4 (Phase 1)

Date: 2026-06-17
Status: Accepted

## Context
Spec §1 places the **aquifer-lag flag and τ_aq (if active)** in M1 `config`'s timestepper settings; spec §11 defines the gating diagnostic (τ_aq/T_flood at representative parameter values), makes the activation flag **global per run** and τ_aq a **per-realization vector once active** (ADR-0004); spec §13 commits the **instantaneous Mazure r_e as the Phase 1 default**, with the linear-reservoir lag "retained in M4, activated if the τ_aq/T_flood diagnostic requires."

The capability is fully built in M4: `make_head_model(r_e, z_toe, *, lag_active, tau_aq_s)` dispatches between `InstantaneousHead` and `LaggedHead`, and `aquifer_response_time(D_aq, D_bl, k_bl, specific_storage_per_m)` produces the per-realization τ_aq (`hydraulics.py`). But **M8 hard-wires the instantaneous form** — `head_model = InstantaneousHead(r_e, z_toe_m)` (`evaluator.py`, its ambiguity #5) — and the frozen `evaluate_realization(theta_row, hydrograph, geometry, l_ini, store_trajectory)` signature (ADR-0011) carries no lag flag, no τ_aq, and no S_s. So a config lag flag presently has **no path to the evaluator**, and the §11 diagnostic that would set it has not yet been run for any Tokachi cross-section.

**Consumer build-state (verified 2026-06-17).** The §11 aquifer-response diagnostic **does not exist**. `aquifer_response_time` (the τ_aq kernel) is called only from `tests/test_hydraulics.py`; no production module, orchestrator, or diagnostic routine consumes it, and `config.py`/`hydrographs.py`/`fragility.py` are empty stubs. This matters because it changes what "not orphan" can honestly mean for the config fields below: today there is **no live consumer** of `aquifer_lag_active` or `S_s`.

---

## Decision
**Phase 1: commit the instantaneous form in M8 (no threading), and place the lag *decision inputs* in config as metadata-recorded fields with a deferred consumer — the unbuilt §11 diagnostic — rather than claiming a live one.** Pre-commit the threading channel so the later activation is mechanical.

Concretely:
- M8 keeps building `InstantaneousHead`; the frozen signature is untouched (ADR-0011). This matches the §13 Phase 1 default.
- M1 config **owns** `aquifer_lag_active` (default `False`) and `specific_storage_per_m` (S_s, deterministic literature value, ADR-0004). In Phase 1 these are **metadata-only** (the §8 attrs `aquifer_lag_active`, `tau_aq`): they are written into provenance but read by no engine code today. Their intended runtime consumer is the **§11 diagnostic, which is unbuilt**; when it is written (in the orchestrator/M3-fed driver, spec §11) it will estimate τ_aq ~ S_s·D_aq·D_bl/k_bl against the characteristic flood duration and set the global flag. Until then, treat them as deferred-consumer fields, not active ones.
- **Pre-committed activation channel (for when the diagnostic triggers):** thread `aquifer_lag_active`, `specific_storage_per_m` (and hence per-realization τ_aq) through the **`geometry`/run-settings dict** — the same dict channel ADR-0010 established for M1→M8 — so M8 can switch to `make_head_model(..., lag_active=…, tau_aq_s=…)` **without changing its positional signature**. This stays a documented extension until §11 flags a governing section.

---

## Alternatives Considered

### Alternative 1 (accepted) — Instantaneous in M8; config carries the decision inputs as deferred-consumer metadata; thread later via the dict channel
- Pros: matches §13 Phase 1 default; frozen M8 signature and Phase 2 surface untouched (ADR-0011); activation later is a localized M8 edit, not a contract change; the fields are honestly scoped (provenance now, §11-diagnostic consumer later).
- Cons: the fields have **no live consumer** in Phase 1 — they are metadata-only until the §11 diagnostic is built, so the original "not orphan" justification is weaker than first stated and is corrected here; the M4 lag path, though built and tested, stays unexercised by M8.

### Alternative 2 — Thread the lag through the geometry/run-settings dict now and build the M4 head model via `make_head_model` in M8
- Pros: fully realizes the spec capability immediately; gives the fields a live runtime consumer; no signature change (dict-valued).
- Cons: activates a Phase-1-unneeded path (§13 says instantaneous is the default until the diagnostic says otherwise); puts S_s and a hydraulic-policy flag inside a dict named "geometry" (semantic stretch — they are material/run properties, not geometry); adds an untested branch and a per-realization τ_aq compute into M8 before the diagnostic justifies it.

### Alternative 3 — Add a new keyword-only `config`/`head_model` parameter to `evaluate_realization`
- Pros: cleanest separation (inject the M4 head model or a settings object).
- Cons: changes the frozen Phase 2 signature, requiring a superseder to ADR-0011 for a capability Phase 1 does not yet need. **Rejected for Phase 1**; revisit only if injection becomes the preferred long-term design.

---

## Rationale
The spec's own baseline is instantaneous (§13) and conditions lag activation on a per-cross-section diagnostic (§11) that has not been built or run. Wiring the lag into M8 now would exercise an unneeded path and either stretch the geometry dict's meaning or break the frozen surface — costs with no Phase 1 benefit. The reconciliation flagged a config flag with *no consumer*; the honest resolution is not to manufacture a consumer but to scope the fields correctly — provenance/metadata now, with the §11 diagnostic as the named but unbuilt runtime consumer — and to pre-name the activation channel so flipping the lag on later is a one-line M8 change rather than a contract renegotiation.

---

## Consequences
- M8 unchanged in Phase 1; `InstantaneousHead` remains the committed default; ADR-0011's frozen signature holds.
- M1 emits `aquifer_lag_active` (default `False`) and `specific_storage_per_m`; both flow to metadata. **Neither is read by engine code until the §11 diagnostic is built** — they are deferred-consumer fields, documented as such so a future reviewer does not mistake them for live inputs or, conversely, prune them as dead.
- When the §11 diagnostic is written, it (not M8) becomes the first consumer of S_s; if it flags a governing section, activation proceeds by passing the flag + S_s through the geometry/run-settings dict and having M8 call `make_head_model`. That step is governed by this ADR's activation clause (or a superseder if injection is chosen instead).
- Couples to ADR-0004 (lag form, exact exponential update, global-flag/per-realization-τ_aq, S_s deterministic), ADR-0010 (dict channel), ADR-0011 (frozen signature). S_s placement is shared with ADR-0015 (deterministic-input scope).

---

## References
- Phase 1 architecture spec §1 (M1 timestepper settings), §6 (lag insertion line), §11 (aquifer-response diagnostic, global flag, per-realization τ_aq), §13 (instantaneous default; lag hook retained in M4), §8 (`aquifer_lag_active`, `tau_aq` metadata attrs).
- ADR-0004, ADR-0010, ADR-0011; ADR-0015 (deterministic-input scope).
- `bep_reliability_engine/hydraulics.py` (`make_head_model`, `aquifer_response_time`, `LaggedHead`), `bep_reliability_engine/evaluator.py` (ambiguity #5); `config.py`/`hydrographs.py`/`fragility.py` (empty stubs as of 2026-06-17); `tests/test_hydraulics.py` (sole caller of `aquifer_response_time`).
