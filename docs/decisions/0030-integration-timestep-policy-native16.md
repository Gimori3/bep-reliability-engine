# ADR-0030: Phase 1 Integration Timestep = Native/16 (225 s) via the ADR-0013 Resample Hook — Superseding the ADR-0022 Native-3600 s Acceptance

Date: 2026-07-10
Status: Accepted (implemented and used for the first end-to-end sweep;
supersedes ADR-0022 decision 1)

## Context

ADR-0022 accepted the native d4PDF 3600 s resolution as the Phase 1
forward-Euler integration timestep, on evidence measured 2026-07-03 (halving
Δt shifted P_f,trans ~1.3% relative at the most active level; ≤0.05% flag
flips). It carried an explicit revalidation clause: *"if the rate law, the
H_eq curve, or the hydrograph source changes materially, the check should be
re-run before relying on this ADR."* ADR-0026 (C_e mean 0.014 → 0.055, ~4×)
and ADR-0027 (raw erosion head, ~1/r_e larger at damped sections) are exactly
such material rate-law changes.

The first end-to-end sweep under the new physics (2026-07-10, N = 10⁵,
canonical HPB_m064_1987 shape) surfaced the failure through a consistency
property, not the ADR-0022 protocol: rows failing **transient but not
static**. Under the shared-sample contract that is impossible in continuous
time — H_eq(l) peaks at H_c at l = l_c, and the transient erosion head
(h − z_toe) − 0.3·D_bl is strictly below the static gross head h − z_toe, so
a pipe whose driving head never exceeds H_c stalls at the equilibrium length
l* < l_c and can never breach. Any such row is therefore a **discrete
forward-Euler step jumping the H_eq equilibrium barrier**: with dl/dt up to
~10⁻³–10⁻² m/s in the hot C_e·k_aq tail, a single 3600 s step advances the
pipe metres past l* and past l_c, after which the descending H_eq branch
gives runaway to breach.

## Evidence (2026-07-10, production priors and seed, N = 10⁵ per point)

Trans-and-not-static rows at 3600 s: KP 57.4 up to 1.7% of all rows at one
level (1691/100000 at h = 39.75), KP 58.8 up to 0.43%, KP 60.0 0.025%,
KP 62.0 8×10⁻⁵ (thick blanket ⇒ larger 0.3·D_bl offset ⇒ least affected).

Δt-halving ladder at the affected shoulder (P_f,trans, KP 57.4):

| h [m MSL] | 3600 s | 1800 s | 900 s | 450 s | 225 s | 112.5 s |
|---|---|---|---|---|---|---|
| 39.50 | 0.01691 | 0.00277 | 0.00094 | 0.00064 | 0.00062 | 0.00062 |
| 40.00 | 0.08041 | 0.04434 | 0.03726 | 0.03619 | 0.03616 | 0.03619 |
| 41.00 | 0.49069 | 0.46690 | 0.46317 | 0.46301 | 0.46306 | 0.46314 |
| 43.25 | 0.96522 | 0.96470 | 0.96448 | 0.96443 | 0.96437 | 0.96432 |

At 3600 s the transition shoulder is inflated up to ~27× and even 900 s is
not converged at the deepest shoulder level; the ladder converges (≤1%
relative, the spec §11 criterion, met with margin) at **225 s**, where the
trans-and-not-static fraction collapses to ≤6×10⁻⁵. KP 62.0 converges by
900–1800 s (checked at h = 47.0/48.0/50.5; ≤0.5% relative at 1800 s already).
The ADR-0022 protocol itself was re-run first and **passed at the top levels**
(−0.1…−0.5% relative, ≤0.25% flips) — the top levels are dominated by
genuinely supercritical rows, which is why the original acceptance protocol
missed the artifact region; the consistency property (transient ⊆ static,
which holds exactly in the continuum for the single-source H_c baseline) is
the sharper diagnostic and is adopted below.

## Decision

1. **Phase 1 fragility sweeps integrate at Δt = native/16 = 225 s**, set as
   `timestepper.target_dt_seconds: 225.0` in every generated config
   (generator constant `TARGET_DT_SECONDS`, emitted with an ADR-0030 header
   note). Chosen on the ladder above: first step with ≤1% relative change
   under halving at every checked level, with the worst (shoulder) level flat
   to MC precision.
2. **Mechanism: the ADR-0013 resample-at-record-construction hook is
   implemented on the canonical path** (`hydrographs.resample_record`, called
   by `run._hydrograph_for_level` when the policy is set): linear
   interpolation onto **integer subdivisions** of the native grid only, so
   every native sample remains a node (bit-exact), max(h)/`peak` are
   preserved, and the loading signal is unchanged — the hourly d4PDF signal
   stays the resolved signal (ADR-0019 §6 is untouched); only the integration
   grid is refined. Coarsening and non-nested grids are refused.
   `native_dt` remains the single authoritative Δt at the M8 boundary
   (ADR-0013); the frozen M8 signature is untouched.
3. **Timestep is physics-fidelity, not data-fidelity.** Pol's own
   integrations use 10–100 s; 3600 s was only ever a data-resolution
   acceptance. Refining the Euler grid moves the engine *toward* the
   continuous model both authors specify; the equilibrium-stall behaviour at
   sub-critical heads is the model's intent (H_eq is an equilibrium curve).
4. **Convergence re-acceptance protocol amended**: future revalidations must
   include shoulder levels (raw 10⁻³ ≤ P_f,trans ≤ 10⁻¹) and report the
   trans-and-not-static fraction per level (≈0 in the continuum for the
   single-source H_c baseline), not only the most active levels.

## What is NOT changed

- The forward-Euler scheme (spec §13; no solve_ivp, no equilibrium clamping —
  a clamp would deviate from Pol's own scheme and needs author confirmation).
- The hourly native resolution of the data (ADR-0019 §6 "final") and the
  ADR-0022 Phase 2 native/2 = 1800 s replay decision (its mechanism is this
  same hook; whether Phase 2 should also move to 225 s is a separate check —
  the per-realization Accept–Reject filter is *more* Δt-sensitive, so the
  ladder should be re-run row-wise for the 2016 record before Phase 2).
- The kernel-level 600↔300 s scheme guard test.

## Consequences

- **The 3600 s first sweep of 2026-07-10 is superseded** (its transient
  shoulder was artifact-inflated up to ~27×; its static branch — timestep-free
  — was already correct). All sweeps from here run at 225 s.
- Sweep cost rises ~16× on the transient branch; measured ~2–4 min per
  section at N = 10⁵ on the restructured numpy path — acceptable without the
  Numba backend.
- The transient fragility transition steepens and its lower shoulder drops
  substantially at the thin-blanket sections; the static–transient gap at low
  P_f widens accordingly. Curves fitted on 3600 s runs must not be compared
  against 225 s runs.
- `metadata` records the policy via the config snapshot
  (`timestepper.target_dt_seconds`) and per-record provenance
  (`resampled_from_native_dt_s`, `resample_factor`).

## Code

- `bep_reliability_engine/hydrographs.py`: new public `resample_record`.
- `bep_reliability_engine/run.py`: `_hydrograph_for_level` applies the policy
  on the canonical path.
- `bep_reliability_engine/config.py`: docstrings updated (the hook is no
  longer a forward requirement).
- `scripts/generate_configs.py`: `TARGET_DT_SECONDS = 225.0` emitted into all
  generated configs; configs regenerated.
- Tests: `tests/test_hydrographs.py` (`resample_record` node preservation,
  identity, refusal cases), `tests/test_run.py`
  (`test_canonical_record_resampled_to_target_dt`).

## References

- ADR-0013 (Δt ownership; the record-construction hook), ADR-0022 (superseded
  decision 1; the revalidation clause that triggered this), ADR-0026/0027
  (the material rate-law changes), ADR-0019 §6 (hourly source, unchanged),
  ADR-0010 (`peak` verbatim), spec §11 (convergence criterion), §12 failure
  mode 3 (Euler overshoot on steep limbs — realized here as overshoot across
  the H_eq barrier).
- Measurement scripts (session scratchpad, 2026-07-10): dt ladder + trans-not-
  static counts; numbers reproduced in this ADR's Evidence table.
