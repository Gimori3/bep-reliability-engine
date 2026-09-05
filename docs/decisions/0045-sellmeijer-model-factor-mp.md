# ADR-0045: Opt-In Sellmeijer Model Factor m_p on the Single-Source Critical Head

Date: 2026-07-18
Status: Accepted (amends ADR-0008 consequence 3; resolves the ADR-0026 wording tension)

## Context

The HKV Fragility Curve Creator audit (2026-07-18) surfaced an internal
tension: ADR-0026 and spec §7 defend the C_e prior with Pol's position that
laminar-vs-turbulent model-form uncertainty "is nominally covered by
Sellmeijer's own ~12% model factor, and it is not C_e's to launder" — while
the engine carried that factor **nowhere**. ADR-0008 (consequence 3) had
deliberately dropped both of Pol's model factors (m_u and m_p), concentrating
model-uncertainty calibration into the stochastic C_e; ADR-0026 then took the
uncertainty back *out* of C_e's justification without putting it anywhere
else. The uncertainty was claimed but not carried.

External reference points that do carry it:

- **Pol SIE 2024 Table 2**: m_p ~ Lognormal(mean 1.0, σ 0.12) on the critical
  head.
- **HKV** (`class_probpiping.py:174`): `Z_p = m_p·H_c − (h − h_exit −
  r_c·D_cover)` with stochastic m_p — standard WBI probabilistic practice.

Measured effect (audit, reproduced by `scripts/mp_model_factor_companion.py`):
at KP58.8 matrix production priors, m_p ~ Ln(1, 0.12) multiplies the static
shoulder P_f by ≈ 2.2× (P_f ~ 2e-3) fading to ≈ 1× above the transition — the
omission is tail-optimistic exactly in the regime the ratio-based deliverables
quote.

## Companion results (2026-07-18, production N = 1e5, both informative matrix sections)

Full-sweep companion vs the frozen baselines
(`docs/decisions/adr0045-mp-companion.json`; companion FragilityResults under
`results/sensitivity/adr0045_mp/`, baselines untouched):

| Section | Branch | Deepest resolved ratio | P_f ≈ 2–5e-3 | P_f ≈ 0.1 | Above transition |
|---|---|---|---|---|---|
| KP58.8 matrix | static | 5.3× (39.25 m, 3e-5 → 1.6e-4) | 2.17× | 1.28× | 0.98–1.00× |
| KP58.8 matrix | transient | 1.67× (39.75 m) | 1.47× | 1.15× | 0.99–1.00× |
| KP60.0 matrix | static | 6.0× (40.75 m, 2e-5 → 1.2e-4) | 2.43× | 1.27× | 0.98–1.00× |
| KP60.0 matrix | transient | 2.50× (41.25 m) | 1.46× | 1.09× | 0.99–1.00× |

Reading: the factor inflates the deep tail (up to ~5–6× at the deepest
nonzero baseline levels, where the raw-tail CP-CI presentation of ADR-0024
applies), ~2.2–2.4× at the static shoulder, and is immaterial (±2%) above
the transition. The transient branch moves too — through the m_p-scaled
H_eq anchor — at roughly half the static tail amplification, so the
static–transient *ratio* deliverables are themselves mildly m_p-sensitive
in the shoulder. Quote these as the bounded model-form sensitivity band
alongside the baseline curves.

## Decision

1. **m_p is carried as an opt-in stochastic Lognormal(mean 1.0, CoV 0.12)
   model factor on the Sellmeijer critical head** — the Pol SIE 2024 Table 2
   / HKV value — gated by the new optional config block
   `sellmeijer_model_factor: {enabled, mean, cov}`. **Default OFF**: a config
   without the block (or with `enabled: false`) is bit-identical to
   pre-ADR-0045 behaviour, and the None case is dropped from
   `Config.to_metadata()` so pre-ADR-0045 config hashes are preserved (the
   Phase 2 replay hash gate keeps passing — the ADR-0037 pattern).

2. **Both-branches propagation (the author's chosen interpretation).**
   Because H_c is single-source (spec §1/§4: one M6 value feeds the static
   comparator AND anchors the transient H_eq curve), m_p multiplies H_c in
   **both** places it appears: `Z_static = m_p·H_c − (h_peak − z_toe)` and the
   H_eq curve anchored at `(l_c, m_p·H_c)` with end anchor `0.9·m_p·H_c`. One
   per-realization draw of Sellmeijer model-form error moves the critical
   head consistently everywhere; applying it to only one branch — the same
   realization believing two different things about its critical head — is
   explicitly rejected. **Note**: this propagation extends past what any
   single source individually specifies. Sellmeijer 2011 and HKV are
   static-only; Pol SIE 2024 prescribes m_p on the critical head within his
   transient model but has no shared-H_c static comparator. The
   both-branches rule is the only reading consistent with the ADR-0002
   shared-sample contract and the single-source H_c. l_c (Pol Eq. (13)) is
   geometric and is NOT scaled; under the ADR-0017 asymmetric-alpha
   decomposition both the static and the recomputed transient H_c are scaled
   by the same draw.

3. **Sampling slots in as a third independent draw, not an eighth theta
   column.** m_p is drawn by `sampling.sample_model_factor` — a standalone
   1-D LHS with its own SeedSequence salt (`_MODEL_FACTOR_SEED_SALT`),
   exactly the ADR "stochastic L" pattern. The 7-D theta LHS, its seed
   consumption, and the L draw are untouched: enabling m_p never shifts the
   existing draws (test-pinned). The draw is not persisted; it regenerates
   through the public `run.model_factor_samples_for_config`, and the Phase 2
   replay regenerates and threads it exactly like L, so an m_p-enabled run
   replays under identical assumptions.

4. **Companion-only for this thesis.** Production configs never carry the
   block; the frozen production sweeps, the Phase 2 posterior and the Phase 3
   campaign all remain the m_p-off baseline. The quantified effect is a
   companion deliverable (`scripts/mp_model_factor_companion.py` →
   `docs/decisions/adr0045-mp-companion.json`), presented as a bounded
   model-form sensitivity alongside the baseline curves.

## Alternatives Considered

### Textual reconciliation only (no code)
Keep the omission; amend the thesis wording. Rejected by the author:
the ~2× tail effect is material to the deliverables' quoted regime, and the
factor is cheap to carry correctly.

### m_p as an eighth theta column
Rejected: perturbs the frozen (N, 7) contract, every persisted theta matrix,
and the Phase 2 Accept-Reject surface, for zero benefit over the independent
draw (m_p is independent of the soil vector by construction).

### Static-branch-only m_p (HKV's literal scope)
Rejected: violates the single-source H_c — the same realization would hold
two beliefs about its critical head, and the static-transient gap would
absorb a spurious model-uncertainty component. See Decision 2.

### Deterministic m_p sensitivity (scale H_c by a constant)
Rejected as the primary form: a constant factor shifts the curve without the
variance contribution, which is precisely the part the audit showed matters
(CoV(H_c) 0.269 → 0.296; tail ratio ~2.2×). The stochastic form contains the
deterministic one (set cov→0 does not exist here; use mean≠1 with the
smallest admissible cov if ever needed).

## Rationale

- **Consistency of the thesis argument.** ADR-0026's "not C_e's to launder"
  now points at a factor the engine actually carries (opt-in), not an
  aspirational one.
- **External corroboration.** Both trusted references (Pol Table 2, HKV/WBI)
  carry stochastic m_p; the engine can now measure what their convention
  implies for the Tokachi sections without adopting it as baseline.
- **Architecture fit.** The independent-draw pattern is the established,
  test-pinned mechanism for exactly this shape of extension (stochastic L,
  ADR-0034 regeneration seams).

## Consequences

- Baseline behaviour, outputs, config hashes, persisted sweeps, Phase 2
  posteriors: **unchanged** (bit-identical; test-pinned by
  `tests/test_model_factor.py`).
- New surface: `SellmeijerModelFactorSettings` (M1),
  `sample_model_factor` (M2), `model_factor_mp` /
  `model_factor_samples` keyword-only M8 arguments (default None),
  `model_factor_samples_for_config` (orchestrator), Phase1Run
  `model_factor_samples` (Phase 2 replay threading),
  `metadata['sellmeijer_model_factor']` stamped only when the block is
  present (never on baseline runs).
- The numba backend needs no change: the factor is applied upstream of the
  M7 kernel, so both backends see the factored H_eq anchor identically.
- When a companion run is enabled, the reported `H_c` / `H_c_transient`
  diagnostics carry the factored values actually used by the limit states.
- ADR-0008 consequence 3 is amended: m_u remains not carried (the uplift
  gate keeps its clean Terzaghi form); m_p is now available opt-in via this
  ADR. ADR-0026's Thesis-defensibility paragraph and spec §7 are updated to
  state where the factor lives.
- The static branch is no longer structurally m_p-free *when the block is
  enabled*; the ADR-0033 GSA structural zeros (C_e etc. on static QoIs)
  remain valid for the baseline and for the 8-D input space it analyzed.

## References

- Pol SIE 2024, Table 2 (m_p ~ Lognormal(1.0, 0.12)); Sellmeijer (2011)
  (~12% regression scatter behind the value).
- HKV Fragility Curve Creator, `probabilisticpiping/class_probpiping.py`
  lines 174 (m_p·H_c) and 330 (stochastic m_p) — the WBI-practice reference.
- HKV audit (2026-07-18, this repo's audit session): effect-size
  quantification; `docs/decisions/adr0045-mp-companion.json`.
- ADR-0008 (consequence 3, amended), ADR-0026 (wording tension resolved),
  ADR-0002 (shared sample), ADR-0017/ADR-0041 (opt-in override precedent),
  ADR-0037 (to_metadata None-drop hash preservation).
