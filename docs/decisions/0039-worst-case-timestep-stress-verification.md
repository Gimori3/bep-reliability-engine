# ADR-0039: Worst-Case Single-Realization Timestep Stress Verification — Native 3600 s Re-Refuted, 225 s Confirmed for the Fragility Deliverable, 112.5 s Required for l_e-Magnitude Consumers

Date: 2026-07-13
Status: Accepted (verification executed 2026-07-13; production Δt unchanged)

## Context

Spec §11 prescribes a *literal* worst-case timestep convergence test that had
never been executed in that form: integrate the Pol ODE on a genuinely flashy
rising limb with the parameter combination drawn from the
high-progression-rate tail that most stresses explicit Euler — high k_aq,
high C_e, low D_bl — and require the terminal eroded length l_e at Δt and
Δt/2 to agree within 1%. ADR-0030 superseded the native 3600 s acceptance on
**population-level P_f ladders** (shoulder inflated ~27×, trans-not-static
consistency violation) and pinned Δt = 225 s; ADR-0031 then verified
statistical (N) convergence at that grid. What remained open is the sharpest
probe: does the *single worst-case realization* on the *worst real loading
shape* converge, and at which rung? This ADR records that verification
(`scripts/timestep_convergence_stress.py`, executed 2026-07-13).

## Method (production code paths only; deterministic, no RNG)

- **Event**: all 3,000 HPB members of the Tokachi KP056.20–061.80 band were
  ranked at each section node by the **largest one-native-step rise of the
  normalized stage shape** — exactly the head jump a single native Euler step
  integrates across after the G1 conditioning scaling. Chosen:
  **HPB_m049_2001**, which climbs **25.2% of its full event amplitude in one
  native hour** (10–90% rise time 4 h, rising limb 7 h). For comparison the
  production canonical shape HPB_m064_1987 carries 8.0% per hour (10–90% rise
  18 h) and ranks **#2281 of 3000** on this metric — the production sweep
  loads one of the *smoothest* members, so this test is a genuine stressor,
  not a re-run.
- **Worst-case θ** (spec §13 row "Convergence-test worst-case θ"), from each
  section's own generated priors via the M2 moment-matching arithmetic:
  p99 k_aq, p99 C_e (0.216 ≈ 5× the median 0.043), p01 D_bl, medians for the
  other four. KP58.8: k_aq = 5.37e-3 m/s, D_bl = 0.570 m → H_c = 1.51 m,
  l_c = 7.45 m, r_e = 0.436. KP57.4: k_aq = 8.05e-3 m/s, D_bl = 0.536 m →
  H_c = 1.44 m, l_c = 6.58 m, r_e = 0.457. Joint marginal exceedance
  ~1e-6 — slightly beyond what one N = 1e5 population typically contains,
  i.e. bounding-but-plausible.
- **Sections**: KP58.8 (governing pair member) primary, KP57.4 (ADR-0030's
  worst shoulder offender, thinnest blanket) confirmatory. A **low-L stress
  variant** (L at p01 of its production lognormal: 21.65 m / 20.41 m) guards
  the stochastic-L axis.
- **Ladder**: Δt = 3600/2^k s, k = 0…8 (native down to 14.0625 s — below
  Pol's own 10–100 s practice), all via the ADR-0013/0030 `resample_record`
  hook and the frozen M8 `evaluate_realization`; the loading signal never
  changes, only the Euler grid. Grids: the production conditioning grid plus
  a **0.05 m refined grid** across the breach-threshold band.
- **Criterion**: successive-halving relative change in terminal l_e ≤ 1%
  *off* the stall-vs-breach bifurcation, **zero** stall/breach branch flips,
  and a stationary breach-threshold stage h\*(Δt). Near the barrier l_e is
  discontinuous in h, so flips are reported separately rather than smeared
  into the relative metric.

## Evidence (docs/decisions/adr0039-timestep-stress.json; figure docs/figures/adr0039-timestep-stress.png)

Terminal l_e [m] at the three diagnostic levels (refined grid):

| Section | h [m MSL] | 3600 s | 1800 s | 900 s | 450 s | 225 s | 112.5 s | 28.125 s | 14.0625 s |
|---|---|---|---|---|---|---|---|---|---|
| KP58.8 (L=35) | 39.45 | **35.00** | 22.55 | 11.16 | 5.58 | 3.862 | 3.851 | 3.847 | 3.847 |
| KP58.8 | 40.20 | **35.00** | **35.00** | **35.00** | 12.03 | 11.60 | 11.64 | 11.69 | 11.70 |
| KP58.8 | 40.25 | 35.00 | 35.00 | 35.00 | 35.00 | 35.00 | 35.00 | 35.00 | 35.00 |
| KP57.4 (L=33) | 39.15 | **33.00** | **30.34** | 14.92 | 7.39 | 3.681 | 3.152 | 3.146 | 3.146 |
| KP57.4 | 39.90 | **33.00** | **33.00** | **33.00** | 7.92 | 6.607 | 6.578 | 6.572 | 6.571 |
| KP57.4 | 39.95 | 33.00 | 33.00 | 33.00 | 33.00 | 33.00 | 33.00 | 33.00 | 33.00 |

(Bold = spurious breach: a pipe the continuum stalls at 3–12 m is stepped
across the H_eq barrier to full breach.)

Successive-halving worst relative l_e change (refined grid, off-bifurcation)
and breach threshold h\*:

| Pair | KP58.8 rel (flips) | KP57.4 rel (flips) |
|---|---|---|
| 3600→1800 | — (13 flips) | — (7 flips) |
| 1800→900 | 134% (2) | 103% (8) |
| 900→450 | 115% (1) | 153% (1) |
| 450→225 | 44.5% (0) | 101% (0) |
| **225→112.5** | **0.39% (0) ✓** | **16.8% (0) ✗** |
| 112.5→56.25 | 0.28% (0) ✓ | 0.13% (0) ✓ |
| 56.25→28.125 | 0.14% (0) ✓ | 0.045% (0) ✓ |
| 28.125→14.0625 | 0.07% (0) ✓ | 0.012% (0) ✓ |

- **Native 3600 s is not converged — badly.** The breach threshold sits
  **0.80 m of stage too low at both sections** (KP58.8: h\* = 39.45 vs
  converged 40.25 m MSL; KP57.4: 39.15 vs 39.95), and 12 refined levels per
  section fail **transient-but-not-static** at native (impossible in the
  continuum; the ADR-0030 diagnostic reproduced at single-row level). The
  count is 0 from 900 s onward.
- **The converged threshold honors the physics.** h\*(Δt→0) lands within one
  0.05 m grid step of the continuum barrier stage z_toe + H_c + 0.3·D_bl
  (KP58.8: 40.25 vs 40.18; KP57.4: 39.95 vs 39.90) — the fine-grid solution
  respects the H_eq equilibrium barrier that coarse Euler steps jump (spec
  §12 failure mode 3, confirmed mechanistically).
- **h\* is stationary from 450 s** at both sections (no flip anywhere on the
  0.05 m grid between 450 s and 14.0625 s), so the **failure indicator** —
  the production quantity behind P_f, the fragility curves, and the Phase 2
  Accept–Reject decisions — is Δt-converged at 225 s with one rung of margin.
- **The literal l_e criterion passes at 225 s at KP58.8 (0.39%, ~2.6×
  margin) but fails at KP57.4 (16.8%)**: at sub-breach staircase levels
  (h = 39.15, pipe stalling near 3.1 m against l_c = 6.6 m) the 225 s grid
  still overshoots the equilibrium length by ~0.53 m. First rung passing
  everywhere: **112.5 s** (0.13%). No failure flag changes anywhere in this
  regime — the error lives entirely in the *magnitude* of a stalled pipe.
- **Low-L variants** (p01): same verdicts at both sections (KP58.8 pass at
  225 s; KP57.4 3.7% at 225→112.5, pass from 112.5 s).
- **The reference is certified**: 28.125→14.0625 s changes ≤ 0.07%
  everywhere, two orders under the criterion.

## Decision

1. **The Phase 1 production integration timestep stays Δt = 225 s
   (ADR-0030 unchanged).** The production deliverable is the failure
   indicator (P_f, fragility curves, Phase 2 Accept–Reject); under the
   worst case that indicator is Δt-stationary at 225 s — breach threshold
   fixed from 450 s, zero stall/breach flips on a 0.05 m stage grid down to
   14 s. No re-sweep; the existing 225 s campaign (8 sweeps, Phase 2
   posterior, ADR-0031/0032/0033 studies) remains valid.
2. **Analyses that consume l_e magnitudes (not failure flags) at
   partial-progression levels must integrate at Δt ≤ 112.5 s** — the first
   rung meeting the literal spec §11 1% criterion at every tested level,
   section, and L variant. This rider binds trajectory
   diagnostics/visualisation subsets and any future l_e-based quantitative
   deliverable. (ADR-0033's l_e/L GSA QoI is unaffected in its conclusions:
   all rows shared one grid, and input *rankings* are insensitive to a
   worst-row shoulder bias that flips no indicator; revisit only if l_e
   magnitudes become a deliverable.)
3. **Native 3600 s is re-refuted at the single-realization level** and the
   spec §11 worst-case test is recorded as executed. Future rate-law changes
   (the ADR-0022/0030 revalidation clause) re-run
   `scripts/timestep_convergence_stress.py` (one command, ~4 min) alongside
   the population ladder.

## Alternatives considered

- **Move production to 112.5 s.** Rejected: doubles transient sweep cost to
  satisfy a criterion whose violation at 225 s flips no failure flag,
  invalidates bit-comparability with the entire existing 225 s campaign
  (including the Phase 2 replay contract, ADR-0036), and buys nothing for
  any current deliverable.
- **Judge convergence on the raw l_e criterion alone (no flip/threshold
  split).** Rejected: l_e is discontinuous in h at the stall/breach
  bifurcation, so *no* Δt passes a pointwise 1% test on a fine enough stage
  grid — the split (magnitude off-bifurcation + threshold stationarity) is
  the well-posed reading of the spec §11 test, and it is also the stricter
  one: it exposed the KP57.4 sub-breach failure a pure threshold test would
  have missed.
- **Use the production canonical shape (HPB_m064_1987).** Rejected: it ranks
  #2281/3000 on limb steepness; a stress test on a smooth limb certifies
  nothing (and this is exactly why the ADR-0022 top-level protocol
  originally missed the artifact region).

## Consequences

- ADR-0030's 225 s stands with sharper, single-realization evidence behind
  it; the "safe timestep" statement is now split by consumer: **225 s for
  indicator/P_f quantities, 112.5 s for l_e magnitudes**.
- The trans-not-static consistency property is confirmed as the sharpest
  cheap diagnostic (12 spurious levels at native, 0 from 900 s) and stays in
  the revalidation protocol (ADR-0030 decision 4).
- The stress driver is reusable: `--config`/`--confirm-config` accept any
  generated section YAML; evidence JSON and the four-panel figure are
  regenerated deterministically.

## Code

- `scripts/timestep_convergence_stress.py` (new; ~4 min end-to-end).
- Evidence: `docs/decisions/adr0039-timestep-stress.json`.
- Figure: `docs/figures/adr0039-timestep-stress.png`.
- No package code changed; no config changed.

## References

- ADR-0030 (population-level 225 s pin; superseded ADR-0022 decision 1),
  ADR-0031 (N-convergence at 225 s), ADR-0026/0027 (the material rate-law
  changes that made native fail), ADR-0036 (Phase 2 replay on the run's own
  grid), ADR-0033 (l_e/L GSA QoI).
- Spec §11 (the worst-case test protocol; the <1% criterion), §12 failure
  mode 3 (Euler overshoot across the H_eq barrier), §13 ("Convergence-test
  worst-case θ").
- Pol CompGeo/SIE 2024 (Δt = 10 s small-scale, 100 s large-scale practice).
