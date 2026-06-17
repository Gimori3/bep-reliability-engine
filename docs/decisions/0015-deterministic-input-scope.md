# ADR-0015: Scope of "All Deterministic Inputs" — Config Fields versus Module Constants

Date: 2026-06-17
Status: Accepted

## Context
Spec §1 says M1 `config` holds "**all deterministic inputs** for a single run." Taken literally this is too broad: several deterministic quantities are *model-defining empirical constants* whose change would mean the kernel is implementing a different calibrated model, not running a different configuration. Today these live as module constants/defaults, while a few genuinely run-varying deterministic inputs have no config home. The reconciliation flagged nine quantities needing classification:

Current homes:
- **θ_repose** — `THETA_REPOSE_DEFAULT = radians(37)`, M6 (`sellmeijer.py`); spec §7 "fixed within every realization."
- **D_r** — `D_R_DEFAULT = 0.725` (the run value) *and* `D_R_MEAN = 0.725` (the regression-normalization mean), M6; spec §7 "Pol base case."
- **C_u** — `C_U_MEAN = 1.81`, M6; spec §7 "evaluated at experimental mean values per Sellmeijer 2011 convention," so the run value is pinned to the mean and the F_r ratio term is 1.
- **KAS** — `KAS_MEAN = 0.498`, M6; same Sellmeijer convention as C_u.
- **α exponent hook** — `alpha_exponent = -1/3` function default in M6; −1/2 is the §12-fm4 3D sensitivity value; not threaded through M8 (its ambiguity #6).
- **D_fore, k_fore** — geometry-dict keys (ADR-0010), deterministic foreshore-blanket properties (ADR-0005).
- **S_s** — `specific_storage_per_m` M4 function argument; no config home yet (shared with ADR-0014).
- **Prior bounds** — optional `bounds` argument to M2 `sample_theta`, the §12-fm2 tail clip; M2 already records them in metadata.

For contrast, the unambiguous *model constants* also living in code: the experimental means used to normalize the Sellmeijer regression (`D_R_MEAN`, `C_U_MEAN`, `KAS_MEAN`, `D_70_MEAN_M`), White's drag `ETA_WHITE = 0.25`, kinematic viscosity `NU_WATER`, the F_r/F_g regression exponents, the Pol coefficients (89, 0.81), `CRACK_RESISTANCE_FACTOR = 0.3`, `EQUILIBRIUM_END_FACTOR = 0.9`, and `constants.py` (`GAMMA_W`, `GRAVITY`).

---

## Decision
Adopt a **principled split** rather than the literal reading:

> A deterministic quantity belongs in **config** if it is a *run-varying scientific input* — something a different cross-section, scenario, or sensitivity run legitimately changes and whose value must be recorded in metadata for provenance. It stays a **module constant** if it is a *constant of the calibrated model* — changing it means using a different model than the kernel implements, i.e. a code/version change, not a config change.

Applying it to the nine:

| Quantity | Decision | Reason |
|---|---|---|
| **θ_repose** | **config** (default 37°) | soil property; per-site deterministic input; enters F_r; reported |
| **D_r** (in-situ run value) | **config** field `relative_density_insitu` (default 0.725) | site/material relative density; documented sensitivity dimension — see the split resolution below |
| **C_u** | **module constant** (= experimental mean); optional config override for sensitivity only | pinned to the mean by Sellmeijer convention (ratio = 1); off-mean values leave the validated range |
| **KAS** | **module constant** (= experimental mean); optional config override for sensitivity only | same Sellmeijer convention as C_u |
| **α exponent** | **config selector** (−1/3 baseline / −1/2 sensitivity); threading via the ADR-0014 channel | run-varying §12-fm4 decomposition selector; recorded in metadata |
| **D_fore** | **config (geometry dict)** — already settled by ADR-0010 | deterministic foreshore property (ADR-0005) |
| **k_fore** | **config (geometry dict)** — already settled by ADR-0010 | deterministic foreshore property (ADR-0005) |
| **S_s** | **config (run setting)** | per-site literature value; feeds τ_aq and the (unbuilt) §11 diagnostic (ADR-0004, ADR-0014) |
| **prior bounds** | **config (optional)** | run-tunable §12-fm2 safety clip; already metadata-recorded by M2 |

The **experimental-mean normalization constants** (`D_R_MEAN`, `C_U_MEAN`, `KAS_MEAN`, `D_70_MEAN_M`), `ETA_WHITE`, `NU_WATER`, the regression exponents, the Pol coefficients, `CRACK_RESISTANCE_FACTOR`, `EQUILIBRIUM_END_FACTOR`, and `constants.py` **stay module constants** — they are the calibrated model.

### Resolution of the D_r split (binding)
`D_r` denotes **two distinct quantities** that share the value 0.725 only by coincidence:

1. the **in-situ / run relative density** of the cross-section's aquifer sand — the *numerator* of the F_r regression ratio `(D_r / D_r,m)^0.35`; and
2. the **Sellmeijer experimental-programme mean** `D_r,m` — the *denominator / normalization* baked into the calibrated F_r.

**Config carries only (1)**, exposed as the unambiguously named field
**`relative_density_insitu`** (resolved 2026-06-17 during the `config.py` build).
The name is deliberate: a bare `relative_density` could be read as either role,
so the field spells out that it is the in-situ run value (the F_r *numerator*).
It maps to M6's `relative_density` argument (today defaulting to `D_R_DEFAULT`).
**`D_R_MEAN` (2) stays a pinned module constant — alongside the equally pinned
`C_U_MEAN`/`KAS_MEAN` — and is never exposed by, or settable from, config.** Only
the in-situ value is ever run-varying; the normalization mean is fixed by the
calibration and changing it would be a code/version change, not a config edit.
The two equal 0.725 today only because the Pol base case sits at the Sellmeijer
experimental mean, which makes the ratio term exactly 1 — the numeric
coincidence that hides the distinction and would otherwise surface as a "I tuned
D_r and only half the engine moved" bug. A config `relative_density_insitu =
0.80` must make `(0.80/0.725)^0.35 ≠ 1` and move all of F_r, with `D_r,m`
unchanged.

**Why a named field rather than a second config field for the mean:** exposing
`D_r,m` in config (even pinned) would contradict the principle above — it is a
calibrated-model constant, not a run input — so the split is resolved by *naming
the one run value unambiguously* and keeping the mean in code, not by adding a
second config field.

**Cleanup mandated by this ADR:** retire `D_R_DEFAULT` (the run-value duplicate
of 0.725) once config supplies `relative_density_insitu`, leaving `D_R_MEAN` as
the sole 0.725 constant in M6 (the normalization). Removing the duplicate is what
makes the two roles impossible to conflate in code.

### Accepted expansion of the M8 boundary
θ_repose, D_r, and the α-selector currently reach M6 *only* as `compute_critical_head` defaults, and M8 calls `compute_critical_head(theta_row, geometry)` with no slot for them. Accepting this ADR therefore **commits the project to threading these three from config through M8 to M6 via the ADR-0014 `geometry`/run-settings dict channel** — a deliberate, accepted enlargement of M8's responsibilities: M8 gains the job of forwarding three deterministic Sellmeijer inputs it does not see today. This is accepted consciously. It is **baseline-neutral** — Phase 1 values equal the present M6 constants, so no behavioural change until a run overrides them — and localized to the dict unpack plus the `compute_critical_head` call (the frozen positional signature is untouched, per ADR-0010/0011). The α-selector threading is the same deferral noted in M8 ambiguity #6.

---

## Alternatives Considered

### Alternative 1 — Maximalist config (literal "all deterministic inputs")
Move every deterministic quantity, including the experimental means and drag coefficient, into config.
- Pros: literal spec §1 compliance; everything tunable.
- Cons: the experimental means and `ETA_WHITE` are not "inputs," they *are* the calibrated Sellmeijer regression; exposing them invites silent miscalibration and decouples config from the model it claims to describe; bloats config and metadata with constants no run should vary. **Rejected.**

### Alternative 2 — Minimalist config (geometry + priors + seed only)
Leave θ_repose, D_r, α, S_s, bounds as constants/args.
- Pros: smallest config; nothing to thread.
- Cons: blocks legitimate sensitivity runs (α −1/2, off-base D_r); leaves S_s and prior bounds homeless (the exact mismatch flagged); contradicts §7, which lists θ_repose and D_r as run-level deterministic values. **Rejected.**

### Alternative 3 (accepted) — Principled split with C_u/KAS pinned-by-convention as overridable constants
- Pros: config carries what a run actually varies and what provenance needs; the calibrated model stays in code; honours §7 (θ_repose, D_r) and §12 (α, bounds); S_s gets a home; optional C_u/KAS overrides leave a sensitivity door open without putting them in the baseline config surface.
- Cons: needs a clear written boundary (this ADR) so the split is principled rather than ad hoc; θ_repose/D_r/α require the ADR-0014 threading channel and the accepted M8-boundary expansion above.

---

## Rationale
"All deterministic inputs" is best read as "all deterministic *inputs that a run legitimately sets*," not "every deterministic number the kernels use." The discriminator — would changing this value mean a different configuration, or a different model? — cleanly separates run inputs (geometry, θ_repose, D_r, α-selector, S_s, bounds) from calibrated constants (experimental means, drag, regression and Pol coefficients). Keeping the latter in code protects the validated Sellmeijer/Pol calibration from accidental config drift, while config still captures everything a cross-section, scenario, or sensitivity sweep needs and everything metadata must record.

---

## Consequences
- M1 `config` fields: `theta_repose_deg` (default 37°), `relative_density_insitu` (the in-situ D_r run value, default 0.725; the normalization mean `D_r,m` is **not** a config field — it stays the pinned constant `sellmeijer.D_R_MEAN`), `alpha_exponent` (default −1/3, selector), `specific_storage_per_m` (S_s; shared with ADR-0014), optional per-parameter `bounds`; plus the geometry dict `D_fore`/`k_fore` already fixed by ADR-0010. All recorded in metadata.
- C_u and KAS stay as M6 constants at the experimental means; an optional config override is exposed only for sensitivity runs, not part of the baseline config surface.
- The calibrated-model constants remain in `sellmeijer.py`/`progression.py`/`constants.py`; changing one is a code/version change accompanied by an ADR, not a config edit.
- **M6 cleanup:** retire `D_R_DEFAULT` once config supplies `relative_density_insitu`; `D_R_MEAN` remains the sole 0.725 normalization constant. Done when config threading lands, not before (avoids an orphaned default).
- **M8-boundary expansion accepted:** θ_repose, D_r, and α are threaded config→M8→M6 via the ADR-0014 dict channel; baseline-neutral, frozen signature intact. Live only once the dict channel and config exist; until then M6 defaults govern, unchanged.
- Couples to ADR-0005 (D_fore/k_fore), ADR-0010 (geometry dict), ADR-0011 (frozen M8 signature), ADR-0014 (S_s home and the threading channel; deferred §11 consumer).

---

## References
- Phase 1 architecture spec §1 ("all deterministic inputs"), §7 (fixed-per-realization θ_repose, D_r; C_u/KAS at experimental means), §11 (S_s in the aquifer-response diagnostic), §12 (failure mode 2 prior bounds; failure mode 4 α = −1/2 sensitivity), §8 (metadata attrs).
- ADR-0004 (S_s deterministic), ADR-0005 (foreshore D_fore/k_fore), ADR-0010 (geometry dict), ADR-0011 (frozen M8 signature), ADR-0014 (aquifer-lag threading; shared S_s placement and dict channel).
- `bep_reliability_engine/sellmeijer.py` (M6 constants, `D_R_DEFAULT`/`D_R_MEAN`, α default), `bep_reliability_engine/sampling.py` (`bounds`), `bep_reliability_engine/constants.py`.
