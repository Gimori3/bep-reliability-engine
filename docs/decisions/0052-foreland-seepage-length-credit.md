# ADR-0052: Opt-In Foreland Seepage-Length Credit, and the Bracket on Declining It

Date: 2026-09-13

## Status
Accepted

---

## Context

The engine reads the gross head across the structure as three resistances in
series: the foreland entry length `lambda_out_eff`, the under-levee path `L`, and
the hinterland exit length `lambda_in`. That split is implemented in
`hydraulics.response_factor` as

    r_e = lambda_in / (lambda_out_eff + L + lambda_in)

which its own docstring identifies as the USACE EM 1110-2-1913 Appendix B
**Case 7a** landside head factor `x3 / (x1 + L2 + x3)`, with `x1` the finite
foreland (Eq. B-7), `L2` the levee base width and `x3` the semi-infinite
hinterland (Eq. B-3). The entry term is the engine's own addition, made by
ADR-0005/0006: Pol (2022) thesis p. 158 states that his Eq. 7.13 assumes "an
infinitely long polder blanket and no riverside blanket", and Sellmeijer (2011)
Fig. 1 shows the river in direct contact with the sand at the riverside dike toe.
Neither source carries a foreland entry resistance; this repository added one
because these cross-sections have measured foreshores.

Since ADR-0028, `r_e` drives **only** the uplift and heave gate. Both piping
heads are gross: the static comparator takes `H_c - (h - z_toe)`
(`evaluator.py:1036`) and the transient erosion driver takes
`(h - z_toe) - 0.3*D_bl` (`progression.py:608`). Both limit states evaluate
Sellmeijer's critical head at the under-levee `L` alone.

So the entry resistance is **carried in the gate and declined in the rule**. At
the prior means it is not a small term. Computed this session through the
engine's own kernels (`scripts/foreland_credit_bracket_study.py`,
`prior_mean_baseline`):

| section | `lambda_in` | `lambda_out_eff` | `L` | `Sigma` | entry share | `r_e` |
|---|---|---|---|---|---|---|
| KP 57.4 | 102.470 | 98.418 | 33.0 | 233.887 | 42.08 % | 0.4381 |
| KP 58.8 | 116.619 | 115.737 | 35.0 | 267.356 | 43.29 % | 0.4362 |
| KP 60.0 | 87.464 | 87.464 | 34.8 | 209.728 | 41.70 % | 0.4170 |
| KP 62.0 | 38.730 | 31.491 | 40.0 | 110.221 | 28.57 % | 0.3514 |

The entry resistance is 29 to 43 per cent of the total series resistance, and it
attenuates neither piping load.

**This is a defensible reading, and the ADR says so first.** Gross head over the
under-levee length is Sellmeijer's own calibration geometry — the Dutch
*schaardijk* case, a levee standing directly in the river with no foreland at
all. Pairing a gross head with an under-levee `L` is what Sellmeijer 2011 itself
does. What is *not* inherited from either source is the foreland entry term the
gate uses, and therefore the asymmetry between the two uses of the same
geometry. The defect, where there is one, is in the justification ADR-0028 gave,
not in the pairing; that clause is amended in place there.

The alternative is not speculative. TR Zandmeevoerende Wellen (1999) — the TAW
technical report, cited in the thesis as `TRZmw1999` and present at
`docs/references/tr-15_technischrapportzandmeevoerendewellen.pdf` — states it
directly. Section 4.4.1 gives the entry-point displacement as Eq. (19),

    L'_v = lambda_1 * th(L_v / lambda_1)

with Eq. (20) defining `th` as the hyperbolic tangent; `L_v` is the foreland
width and `lambda_1` the foreland spreading length. That is the **same tanh** the
engine already uses for `lambda_out_eff` (`leakage_length_out`, ADR-0005/0006,
whose docstring already cites §4.4.1 Eq. (19)). Section 4.4.2 then extends it to
piping, verbatim (verified this session against the PDF page image, printed
page 44):

> **4.4.2 Invloed voorland op het mechanisme Piping**
>
> Net als bij opbarsten is het effect van voorland dat het theoretische
> intreepunt, ten opzichte van een situatie zonder voorland, in de richting van
> het buitenwater wordt verplaatst, volgens dezelfde formule. Daardoor wordt de
> theoretische kwelweglengte met L'_v vergroot.
>
> Zowel in de klassieke regels van Bligh of Lane, als bij de regel van
> Sellmeijer mag de toename van de kwelweg in rekening worden gebracht.

The operative word is **mag** — *may*, not *must*. The credit is permissive, so
declining it is a recognised conservative simplification and not an error. What
the repository lacked was any measurement of what declining it is worth.

---

## Decision

Add an optional **foreland seepage-length credit**, `phi` in `[0, 1]`, which when
enabled evaluates the Sellmeijer critical head at

    L_eff = L + phi * lambda_out_eff

while leaving the traverse length, the `Z_transient = L - l_e` criterion, the
`L` in the Eq. (5) rate denominator, the `L` in `r_e`, the leakage lengths
themselves and the critical pipe length `l_c` on the **physical under-levee L**.
`phi = 1.0` is exactly the TR Zmw 1999 §4.4.2 displacement `L'_v`.

Threaded on the same additive pattern as ADR-0041/0045/0049/0050/0051:

- `sellmeijer.resolve_effective_seepage_length` (new, exported) returns `L`
  itself — the same object — when the credit is `None`, and `L + credit`
  otherwise; both M6 entry points `compute_critical_head` and
  `compute_critical_head_vectorized` take a keyword-only
  `seepage_length_credit_m` and forward it, so the two paths cannot drift apart;
- `evaluator.evaluate_realization`, `evaluate_batch` and
  `evaluate_batch_diagnostics` take `foreland_seepage_credit` (the fraction) and
  resolve the credit from **this realization's own** `lambda_out_eff`. The
  `EvaluationResult` and `BatchDiagnostics` **field sets are untouched**, which
  is what ADR-0011 freezes, and `tests/test_evaluator_phase2_surface.py` still
  pins the import surface;
- a `Config.foreland_seepage_credit` field, threaded by `run.py` through
  `_EvalSettings`, and **dropped from `to_metadata()` when None** so every
  pre-ADR-0052 `config_hash` is byte-identical to what its persisted run
  recorded. Verified against all eight committed configs and re-verified by
  re-running the Phase 2 verification over the existing production runs;
- `bayesian_reliability_updating.replay` (batch and scalar) and
  `fragility_update`, so a Phase 1 run carrying the knob replays under its own
  assumptions instead of silently reverting.

`None` everywhere is the declined credit and is **bit-identical** to prior
behaviour — proven against the persisted production sweeps, not by inspection.
`phi = 0.0` is accepted and is a value-identical no-op. Values outside `[0, 1]`
are refused: §4.4.2 licenses exactly the displacement `L'_v` and no more, and a
negative credit would be a shortening no source mentions.

The scaling is applied **in M6, upstream of the timestepper**, so the knob works
on both progression backends, exactly as ADR-0049's `critical_length_factor`
does and unlike ADR-0041's end factor.

**The production baseline is unchanged.** This is a companion-sensitivity knob.
Production configs never carry it set, and no production value moved.

### The arms

| arm | `phi` | what it is |
|---|---|---|
| `credit_half` | 0.5 | a partial credit, so the response is shown to be graded rather than read off one endpoint |
| `credit_full` | 1.0 | exactly the TR Zmw 1999 §4.4.2 entry-point displacement `L'_v` |

Unlike ADR-0049's bracket, neither arm is a mirrored counterfactual: the upper
arm is the credit the source actually licenses, and the baseline (`phi` absent)
is the other edge. The bracket is one-sided **in construction** because the
permission is one-sided — §4.4.2 offers an increase in seepage length and
nothing else.

---

## Alternatives Considered

### Adopt the credit as the production baseline
Rejected. The permission is optional, the production baseline is the
conservative side of it, and ADR-0047 already fixed this repository's rule for
such choices: *adopt where the current value is wrong, hold where it is merely
conservative*. Nothing here shows the declined credit to be wrong. Adopting it
would also invalidate every committed `config_hash` and all eight sweeps.

### Credit the seepage length everywhere, including the traverse and the rate
Rejected, and this is the substantive modelling decision inside the ADR. §4.4.2
credits the **theoretical** seepage length in Sellmeijer's *rule*; it does not
assert that a pipe physically has to erode backwards across the foreland. The
transient model integrates a real pipe across a real distance, so crediting the
traverse would change what `Z_transient = L - l_e` means and would silently
lengthen every realization's race. Keeping `l_c`, the traverse, the criterion and
the rate denominator on the physical `L` is pinned by test.

### Move the credit into `r_e` instead
Rejected. `r_e` already carries the entry resistance — that is the asymmetry this
ADR is about. Adding the same foreland twice would double-count it, which is
precisely the error the original review of this question made (see *Errors
corrected* below).

### Make the credit a stochastic input
Rejected, on ADR-0049's ground. It is a **model-form / code-permission** choice
about which rule to apply, not aleatory scatter. Note that the credited *length*
is nevertheless stochastic, because `lambda_out_eff` depends on the sampled
`k_aq` and `D_aq`; the knob is the deterministic fraction, the credit it resolves
to is per realization.

---

## Consequences

- `EvaluationResult` / `BatchDiagnostics` field sets unchanged. The reported
  `H_c` is the value actually used; `l_c` and `r_e` are reported unchanged,
  because they *are* unchanged.
- Every existing `config_hash` survives, checked against all eight committed
  configs and re-verified through the Phase 2 replay gate.
- Both progression backends accept the knob.
- **The static branch is NOT invariant under it.** This is the structural
  opposite of ADR-0049 and ADR-0050, and it is the reason the knob had to be
  measured rather than reasoned about: `H_c` is single-source, so the credit
  reaches both limit states. The study *counts* the static cells that move
  instead of asserting none do, and asserts instead the one thing that must hold
  — that a raised `H_c` can only remove failures, never create them.
- Under `foreland_open` (ADR-0025) the credit is identically zero, since
  `lambda_out_eff` is zero: no foreland blanket, no displaced entry point.
- Tests: `tests/test_foreland_seepage_credit.py` pins bit-identity at every
  layer, the metadata drop and hash preservation across all eight committed
  configs, the exact `L_eff` arithmetic, what stays on the physical `L`, the
  per-realization credit, the `[0, 1]` refusal, the `foreland_open` composition,
  backend agreement, and the evidence record.
- The measured result and its interpretation live in
  `docs/decisions/adr0052-foreland-seepage-credit-bracket.md`, with the
  per-level evidence in `adr0052-foreland-credit-companion.json` and the frozen
  prediction in `adr0052-foreland-credit-prereg.md`.

### Errors corrected

Two claims from the review that opened this question do not survive, and are
recorded here so they are not propagated:

1. The load-to-resistance ratios "0.032 / 0.074 / 0.129 / 0.154" were computed
   by attenuating the head **and** extending `L`, which double-counts the same
   foreland. Recomputed this session at the design HWL as
   `(HWL - z_toe) / H_c(L_eff)`, they are **0.128 / 0.318 / 0.454 / 0.275**.
2. "The only internally inconsistent pairing" is overstated. Gross head with an
   under-levee `L` is Sellmeijer's own calibration geometry. The asymmetry is
   real but it is between the *gate* and the *rule*, not inside the rule.

**Added 2026-09-16.** A third claim, made on the thesis side rather than in
this register, also does not survive: that the 1998 exit gradients
corroborate the under-levee convention because a foreshore-spanning path
would imply an average gradient too small to produce the reported local
exit gradient. A local exit gradient is a head difference across the blanket
divided by its thickness, not an average along the path, and measured
through this engine's own translation the tabulated gradients select neither
convention (the spanning path is in fact the closer of the two at three of
four sections). The convention rests on the surveyed footprint, on
Sellmeijer's calibration geometry and on the permissive wording of
TR Zmw 1999 §4.4.2, not on that back-calculation. Evidence:
`physical-model-qualifications-study.md` section 2.

---

## References

- ADR-0005/0006 (the foreland entry length and its tanh), ADR-0025 (the
  open-entry bound on the same term), ADR-0027/0028 (the raw-head reversal that
  confined `r_e` to the gate — amended in place by this ADR), ADR-0047 (adopt
  where wrong, hold where merely conservative; and the paired-bootstrap
  cancellation test), ADR-0049 (the override pattern this copies, and the
  zero-common-mode counterpart), ADR-0050 (the gate-only counterpart),
  ADR-0011 (what "frozen" means).
- TR Zandmeevoerende Wellen (1999), §4.4.1 Eqs. (19) and (20), and §4.4.2
  (`docs/references/tr-15_technischrapportzandmeevoerendewellen.pdf`; thesis key
  `TRZmw1999`).
- Sellmeijer (2011), Fig. 1 and formula [6]. Pol (2022) thesis, p. 158
  (Eq. 7.13's stated assumptions). USACE EM 1110-2-1913 (2000), Appendix B
  Case 7a, Eqs. B-3 and B-7.
- `bep_reliability_engine/sellmeijer.py`
  (`resolve_effective_seepage_length`), `hydraulics.py` (`response_factor`,
  `leakage_length_out`), `evaluator.py`.
