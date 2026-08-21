# ADR-0049: Opt-In Critical-Pipe-Length Override for the Eq. (13) Form Bracket

Date: 2026-08-21

## Status
Accepted

---

## Context

The transient equilibrium curve of Pol SIE 2024 Eq. (11) is fixed by two anchors:
its **end** value `H_eq(L) = 0.9·H_c`, and the **critical pipe length** `l_c` of
Eq. (13) at which `H_eq` attains its maximum `H_c`. The two anchors are not
symmetric in the engineering meaning of the curve: the end factor sets how quickly
the barrier falls away once a pipe is past `l_c`, while `l_c` itself sets *where the
barrier is*, and therefore how far a pipe must travel before the race is won or lost
(spec §1, M7; `docs/decisions/m7-pol-ode-reference-values.md` §2).

Only one of them had a hook. ADR-0009 named the 0.9 end anchor a gap component,
ADR-0041 wired it as an opt-in keyword-only override, and Stage 6.6 (ADR-0040)
measured it at field scale as comparators C4c/C4d. `l_c` had neither: it was
computed unconditionally by `sellmeijer.compute_critical_pipe_length` and threaded
into M7 with no way to vary it. The thesis's register of limitations carried that
asymmetry explicitly, as "critical pipe length not isolated as a sensitivity,
though the equilibrium-curve end anchor is", direction "not resolved", quantified
"no".

The gap is not academic. Eq. (13) states its own basis as agreement with **2D**
numerical piping simulations (Pol SIE 2024 §2.3), while the one **3D** hole-exit
critical length published alongside it sits well above what the formula returns at
the same geometry. That discrepancy is already recorded in this repository as a
caution against cross-validating the formula against it (m7 note §2). A caution is
not a measurement, and the quantity it cautions about is the one that decides
whether a realization stalls or breaches.

---

## Decision

Add a keyword-only `critical_length_factor: float | None = None` multiplicative
override on Eq. (13), threaded on the same additive pattern as ADR-0041 and
ADR-0045:

- `sellmeijer.compute_critical_pipe_length` (the kernel; scales the returned
  `l_c`), and both M6 entry points `compute_critical_head` and
  `compute_critical_head_vectorized`, which forward it so the two paths cannot
  drift apart;
- `evaluator.evaluate_realization`, `evaluate_batch` and
  `evaluate_batch_diagnostics` (ADR-0045's precedent for a default-`None` keyword
  on the frozen scalar: the `EvaluationResult` **field set** is untouched, which is
  what ADR-0011 freezes, and `tests/test_evaluator_phase2_surface.py` still pins
  the import surface);
- a `Config.critical_length_factor` field, threaded by `run.py` through
  `_EvalSettings`, and **dropped from `to_metadata()` when None** so every
  pre-ADR-0049 `config_hash` is byte-identical to what its persisted run recorded.
  Verified against all committed configs and all persisted sidecars;
- `bayesian_reliability_updating.replay`, in both the batch and the scalar call, so
  a Phase 1 run carrying the knob replays under its own assumptions instead of
  silently reverting to the published formula.

`None` everywhere resolves to the published Eq. (13) through an early return, so an
un-overridden call is **bit-identical** to prior behavior. A non-positive factor is
refused: `l_c <= 0` has no rising `H_eq` branch and would divide by zero in the M7
equilibrium curve.

The scaling is applied **in M6, upstream of the timestepper**. Two consequences
follow, and both are deliberate. First, the reported `l_c` diagnostic and the value
the M7 curve is built on are the same number by construction, so a scaled run can
never report an unscaled `l_c`. Second, unlike the ADR-0041 end factor, the knob is
**not refused on the numba backend**: the JIT kernel hard-codes
`EQUILIBRIUM_END_FACTOR` but receives `l_c` as an input array, so both backends see
the same curve. This is the `model_factor_samples` situation, not the
`equilibrium_end_factor` one.

Production configs never carry it set. It is a companion-sensitivity knob, exactly
as `sellmeijer_model_factor` and `prior_mean_scenario` are.

### The bracket, and where its range comes from

Two arms, both multiplicative on Eq. (13):

| arm | factor | provenance |
|---|---|---|
| upper | **1.5558** | The DgFlow 3D hole-exit critical length `l = 1.36 m` for the in-domain S2-2 case (`L = 3 m`, `D = L/3`), Pol 2022 thesis Fig. 5.9 caption, divided by Eq. (13) at the same geometry (`0.874 m`). |
| lower | **0.6428** | The reciprocal. A mirrored counterfactual, not a measurement. |

The lower arm is stated as what it is. No published case places the true critical
length *below* Eq. (13); the bracket is one measured deviation and one mirror of
it, so that the band is two-sided. Corroborating the direction but deliberately
**not** used to widen the range: the B25-245 small-scale box measured
`l_c = 0.197 m` against Eq. (13)'s `0.0905 m`, a factor 2.18, also above. That case
is out of the fitted domain and is a qualitative gate only (m7 note §5D), so it is
reported as a direction check.

---

## Alternatives Considered

### Substitute the DgFlow 3D critical length as the production value
Rejected on the same ground ADR-0009 rejected substituting a calibrated equilibrium
curve. Eq. (13) is the published SIE 2024 reliability-model choice the spec adopts,
and 1.36 m is one case, not a re-fitted rule. This ADR adds a bracket, not a
replacement.

### Make `l_c` a stochastic input, an eighth θ column or a separate draw
Rejected. It is a **model-form** uncertainty on a deterministic geometric formula,
not aleatory scatter in a field quantity, and the repository already distinguishes
the two (ADR-0045 for `m_p` is the model-form pattern; `seepage_length_cov` is the
aleatory one). A stochastic `l_c` would also perturb the (N, 7) contract and every
persisted θ matrix.

### Analysis-only keyword, no `Config` field (the strict ADR-0041 scope)
Rejected here, and ADR-0041 anticipated the reason: it said Config threading "can
follow later, additively, if a config-driven run ever needs it". This one does. The
bracket has to be measured as full fragility sweeps over the production
conditioning grid at production N, which is `run_fragility_analysis` from a config;
driving `evaluate_batch` level by level would reimplement the orchestrator to avoid
one field.

### Vary the end anchor and `l_c` together as one "equilibrium-curve" knob
Rejected. They answer different questions and their channels differ: the end factor
changes the descending branch only and is provably inert for the sustained-peak
indicator (ADR-0040), while `l_c` moves the rising branch and the barrier location.
Confounding them would make neither attributable.

---

## Rationale

The additive-override pattern is the repository's established way to open one
published constant for one named component without touching the production path:
default-`None` keyword, bit-identical baseline, hash-preserving metadata, recorded
in the consuming study's own record. This is its fourth use (ADR-0017, ADR-0041,
ADR-0045, here), and the first where the opened constant sits on the *rising* side
of the equilibrium curve.

The bracket range is taken from the repository's own reference material rather than
invented. That is the whole reason the m7 reference note records the 1.36 m value
and the caution attached to it.

---

## Consequences

- `EvaluationResult` / `BatchDiagnostics` field sets unchanged; the reported `l_c`
  is the value actually used.
- Every existing `config_hash` survives, checked against all committed configs and
  all persisted sidecars. The Phase 2 replay gate is unaffected.
- Both progression backends accept the knob and agree to `< 1e-10`.
- The static branch is **exactly** invariant under it. `l_c` reaches nothing but
  `H_eq(l)`; it does not enter `H_c` (Eq. (12) has no `l_c`), the leakage lengths,
  `r_e`, or the static comparator. The bracket study asserts this on the whole
  static failure matrix and refuses to report if a single cell moves.
- Tests: `tests/test_critical_length_factor.py` (18) pins bit-identity at every
  layer, the metadata drop and hash preservation, the exact scaling, the
  non-positive refusal, backend agreement, and the static-invariance claim.
- The measured result and its interpretation live in
  `docs/decisions/adr0049-critical-length-bracket.md`, with the per-level evidence
  in `adr0049-critical-length-companion.json`.

---

## References

- ADR-0009 (the `H_eq` end anchor as a gap component), ADR-0041 (the override
  pattern this copies), ADR-0045 (default-`None` keyword on the frozen scalar),
  ADR-0011 (what "frozen" means), ADR-0017 (the original additive-override
  precedent), ADR-0029 (backend split), ADR-0047 §4.5 and
  `docs/decisions/epistemic-bracket-synthesis.md` (the cancellation test this
  bracket is measured with).
- Pol, Kanning, Jonkman & Kok (2024) SIE, Eqs. (11), (12), (13) and §2.3.
- Pol (2022) thesis, Fig. 5.9 caption (the DgFlow 3D critical length) and
  Table 3.2 (the B25-245 measured `l_c`).
- `docs/decisions/m7-pol-ode-reference-values.md` §2 and §5D.
- `bep_reliability_engine/sellmeijer.py` (`compute_critical_pipe_length`),
  `progression.py` (`equilibrium_head`).
