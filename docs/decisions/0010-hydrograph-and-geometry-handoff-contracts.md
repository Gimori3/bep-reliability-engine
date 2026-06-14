# ADR-0010: Canonical HydrographRecord and Geometry-Dict Schemas (M3/M1 Handoff Contracts)

Date: 2026-06-14
Status: Accepted

## Context
M8 `evaluate_realization` (`evaluator.py`) is the first implemented module that consumes a `HydrographRecord` (produced by M3 `hydrographs.py`) and a `geometry` dict (produced by M1 `config.py`). Both M3 and M1 are still unimplemented, so M8 had to assume the shape of each input. These assumptions are load-bearing for the Phase 2 import path (spec §8) and must be pinned now, before M3 and M1 are built, so those modules conform rather than forcing a later M8 change (the `evaluate_realization` signature is a frozen contract).

A subsidiary question was whether M8's assumed `geometry` keys conflict with keys already committed by an upstream module. Investigation of the consumed modules:

- **M4 `hydraulics.py` reads no geometry dict.** Every kernel takes unpacked scalars (`leakage_length_in(k_aq_mps, d_aq_m, d_bl_m, k_bl_mps)`, `leakage_length_out(k_aq_mps, d_aq_m, d_fore_m, k_fore_mps, foreshore_width_m)`, `response_factor(...)`, `InstantaneousHead(r_e, z_toe_m)`, `LaggedHead(r_e, z_toe_m, tau_aq_s)`). M4 therefore commits **no** geometry dict key names; M8 unpacks the dict into these scalars.
- **M6 `sellmeijer.py` reads exactly `geometry["L"]`** in both `compute_critical_head` and `compute_critical_head_vectorized`. M8 matches this. M6's docstring additionally lists `z_toe`, `foreshore_width`, `lambda_out_params` as "accepted and ignored" keys — a stale hint at a nested foreshore grouping, but not a functional commitment (M6 reads none of them).

So the only committed cross-module geometry key is `L`, which M8 already uses; M8 is the de-facto definer of the rest of the schema.

---

## Decision

### Canonical `HydrographRecord` contract (M3 must conform)
M8 consumes exactly three fields by duck typing; M3 must populate them as follows, in strict SI (M3 owns all unit conversion, spec §1):

- **`h`** — river stage series, ndarray shape `(T,)`, metres above the common vertical datum, **uniformly sampled at `native_dt`**.
- **`peak`** — scalar static comparator level h_peak, metres above datum, defined as the **maximum instantaneous river stage of the record** (`peak == max(h)`). It is authoritative: M8 uses `record.peak`, not a recomputed `max(h)`. Defining it in M3 leaves room for a future non-max anchor (e.g. a conditioning level) without touching M8.
- **`native_dt`** — the **authoritative integration timestep** dt_s, seconds. M8 uses `native_dt` directly, not `diff(t)`; M3 must guarantee `h` is sampled uniformly at this spacing.

The full record may additionally carry `t`, `duration_hours`, `scenario`, `event_id` (spec §2); M8 ignores them. M3 is free to emit them for other consumers.

### Canonical `geometry` dict schema (M1 must conform)
Flat keys, strict SI:

- **`L`** — seepage length across the structure [m]. (Also read by M6.)
- **`z_toe`** — polder surface elevation at the landside exit point [m above datum]; ≡ h_e in Pol SIE 2024 Eqs. (6) and (8) (ADR-0007).
- **`foreshore_width`** — foreshore width B_f [m] (ADR-0006).
- **`D_fore`** — deterministic foreshore blanket thickness [m] (ADR-0005).
- **`k_fore`** — deterministic foreshore blanket vertical conductivity [m/s] (ADR-0005).

M1 emits geometry with exactly these keys; M8 unpacks them into the M4/M6 scalar signatures.

---

## Alternatives Considered

### Nested `lambda_out_params` grouping for the foreshore inputs
Group `D_fore`, `k_fore`, `foreshore_width` under one `geometry["lambda_out_params"]` sub-dict, as M6's docstring hints.
- Pros: clusters the ADR-0005/0006 foreshore/lambda_out inputs.
- Cons: inconsistent with the flat `L`/`z_toe` keys; `foreshore_width` is a geometric quantity, not naturally a "lambda_out param"; M8 already implemented and tested against flat keys. **Rejected.**

### Derive dt from `diff(t)` instead of `native_dt`
- Cons: ill-defined for single-sample records (`T = 1`, used in M8's deterministic tests); redundant with the M3-recorded native resolution; risks silent disagreement if `t` spacing and `native_dt` ever differ. **Rejected** — `native_dt` is authoritative.

### Recompute `max(h)` for the static peak instead of using `record.peak`
- Cons: duplicates the representative-peak definition that belongs to M3 (spec §1) and forecloses a future non-max conditioning anchor. **Rejected** — `record.peak` is authoritative.

---

## Rationale
Pinning the contracts now lets M3 and M1 be written to a fixed target and keeps the `evaluate_realization` signature frozen for Phase 2. The flat geometry schema is chosen for consistency with the already-committed `L` key and the flat `z_toe`, and because M8 is the only module that actually reads the foreshore keys, so no existing code is contradicted (only M6's "accepted and ignored" docstring example, which carries no behaviour). Authoritative `native_dt`/`peak` keep M3 the single owner of temporal resolution and the representative-peak definition, matching the module-responsibility split.

---

## Consequences
- **M3** conforms to the field contract above: `peak = max(h)`, `h` uniformly sampled at `native_dt`, all SI. When M3 lands, `HydrographRecord` becomes the concrete type behind M8's forward-reference annotation and the test stand-in in `tests/test_evaluator.py` can be swapped for it.
- **M1** emits the flat geometry schema; this also resolves spec ambiguity 4 noted in the `evaluator.py` module docstring.
- **M6 follow-up (docstring only):** `sellmeijer.py`'s docstring example currently lists `lambda_out_params` among the accepted-ignored keys. It should be updated to the canonical flat keys to avoid drift. This is a documentation change with no behavioural effect (M6 still reads only `L`); deferred to avoid an unrequested edit to a committed module.
- **M8** is unchanged: its assumed keys already match the canonical schema and the one committed key (`L`); no signature change.
- Ties to ADR-0005 / ADR-0006 (foreshore/lambda_out inputs), ADR-0007 (z_toe ≡ h_e datum).

---

## References
- Phase 1 architecture spec §1 (M1, M3, M8), §2 (HydrographRecord and M8 I/O contracts), §8 (Phase 2 handoff).
- ADR-0005 (per-realization lambda_out, foreshore proxy), ADR-0006 (foreshore tanh correction), ADR-0007 (r_e-translated erosion head and z_toe ≡ h_e datum).
- Pol (2024, SIE) Eqs. (6), (8).
