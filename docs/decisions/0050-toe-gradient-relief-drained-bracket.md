# ADR-0050: Opt-In Landside-Toe Gradient Relief for the Drained-Configuration Bracket

Date: 2026-08-21

## Status
Accepted

---

## Context

`remediation_state` is a provenance label with no physics behind it. Two of the
four confined sections carry the label `drained`: KP 58.8 and KP 60.0 were fitted
with a side berm plus a landside toe drain between 1999 and 2003 (Fukuda type map
④+⑤; `docs/tokachi_bep_inputs_provenance.md` §3.2, §6.1). Those same two sections
carry the largest annual system failure probabilities in the basin,
7.42e-3 and 1.80e-3 historically and 4.09e-2 and 1.42e-2 under +4 K, and they are
the top two entries of the prioritisation ranking that closes the thesis.

The engine represents no drain. Every probability at those two sections is
therefore an as-if-undrained statement, which the thesis states in six places and
never numbers. That is the single most exposed interpretive caveat in the work:
the ranking's top two entries are the two entries the model is least entitled to
rank.

Three pieces of already-recorded material make the caveat tractable rather than
merely acknowledged, and this ADR spends them.

**1. The guidance mapping.** PWRI (2014) 河川堤防の浸透に対する照査・設計のポイント,
Table 7.1.1 (printed p. 33), names the physical quantity each countermeasure acts
upon, for 盤ぶくれ・パイピング specifically. Transcribed in
`docs/tokachi_bep_inputs_provenance.md` §6.3 and
`docs/tokachi_basin_document_review_2026-07-27.md` §1.12, and re-read from the
source PDF for this ADR:

| Countermeasure | PWRI-stated effect on heave/piping | Engine quantity |
|---|---|---|
| 断面拡大工法 section enlargement (the berm) | ① lengthen the seepage path, lowering the hydraulic gradient | `geometry.L` |
| ドレーン工法 landside toe drain | ① reduce the hydraulic gradient at the landside toe | the exit gradient `i_exit` in the M5 heave limit state |

Those are the two works recorded at KP 58.8 and KP 60.0, and both map onto a
quantity the engine already carries.

**2. The engine makes the drain half of that mapping one-to-one.** The landside
exit gradient appears in exactly one place: `initiation.z_heave`, as
`i_exit = Δh_blanket / D_bl` against the Terzaghi critical gradient
`i_c = γ'_bl/γ_w`. Since ADR-0028 the r_e-attenuated `Δh_blanket` reaches the
uplift/heave gate and nothing else: both piping heads are r_e-independent and the
static comparator is entirely r_e-independent. A perturbation of `Δh_blanket`
therefore perturbs exactly the quantity the guidance names, and nothing else. The
static branch must be *exactly* invariant under it, which makes the mapping
claim falsifiable rather than asserted.

**3. The berm half is already measured.** ADR-0047 re-measured L at all four
sections from a 2025 GSI DEM5A lidar surface. At the two `drained` sections the
2025 path is 42.0 m (KP 58.8, 31 of 31 clean stations, along-levee CoV 0.073) and
43.0 m (KP 60.0, 31 of 31, CoV 0.184), against the modelled 1998 values 35.0 and
34.8 m. ADR-0047 **held** both, and gave a specific reason:

> the two `drained` sections' +7/+8 m is genuine post-1998 remediation geometry,
> and adopting only its anti-conservative half while the engine still models no
> toe drain is not an improvement.

That reason is exactly what this ADR removes. A bracket that moves the path
length and the exit gradient together is the one configuration in which the held
half is legitimately spent, because both halves of the recorded works are then
present at once.

**The counterweight, and why no magnitude is assumed.** Provenance §7.3 records
that the toe-drain programme in this basin has three distinct documented
rationales, of which only one is seepage, and concludes that *a `drained` label
identifies a physical feature, not a design intent*, warning that "a seismically
motivated drain need not have been sized against the seepage exit gradient". The
secured dataset holds no post-remediation geometry and no drain-capacity data;
the transmissivity of the post-1999 berm fill is recorded as difficult to obtain
and the post-remediation cross-sections lie outside the OYO dataset. PWRI's own
drain design rule (printed p. 42, §9.1) sizes the drain *width* so that the
average hydraulic gradient stays below 0.3, but that criterion governs the drain
body, not the foundation blanket exit gradient, and the guidance states no
equivalence between the two. **The magnitude of the exit-gradient relief is
therefore not grounded in anything recorded, and this ADR does not invent one.**
What is grounded is the direction, the quantity acted upon, and the measured
path length. The relief fraction is consequently a *swept* axis whose response
curve is the deliverable, not a fitted or assumed drain performance.

---

## Decision

Add a keyword-only `toe_gradient_relief_factor: float | None = None`
multiplicative relief on the landside-toe exit gradient, threaded on the additive
pattern ADR-0041, ADR-0045 and ADR-0049 established:

- `evaluator.evaluate_realization`, `evaluate_batch` and
  `evaluate_batch_diagnostics`. The `EvaluationResult` and `BatchDiagnostics`
  **field sets are untouched**, which is what ADR-0011 freezes;
- a `Config.toe_gradient_relief_factor` field, threaded by `run.py` through
  `_EvalSettings`, and **dropped from `to_metadata()` when None** so every
  pre-ADR-0050 `config_hash` is byte-identical to what its persisted run
  recorded;
- `bayesian_reliability_updating.replay`, in both the batch and the scalar call,
  so a Phase 1 run carrying the knob replays under its own assumptions instead of
  silently reverting to the undrained foundation.

Bounded to `(0, 1]`. The mapping is one-sided by construction: the guidance
states the countermeasure *reduces* the gradient, so a value above 1 would be an
aggravation the mapping does not license. `None` and `1.0` are both the
undrained baseline.

**Where it applies.** The factor scales the response factor handed to the M4 head
model, and therefore scales `Δh_blanket(t)` and `i_exit(t)` by exactly the same
factor at every timestep. This is correct for both head models (the lag state is
linear in the equilibrium target, so `advance_lag_state` scales too) and for both
progression backends (the JIT kernel receives `r_e` directly and inlines the same
translation).

**What it does not touch.** `EvaluationResult.r_e` and `BatchDiagnostics.r_e`
keep reporting the *physical, unrelieved* M4 response factor. r_e is a property of
the blanket-aquifer system; the relief is a credit for a structure. Conflating
them would make a scenario run's leakage diagnostics unreadable. The factor is
recorded separately in run metadata.

---

## Pre-registration

Written and committed **before the first arm was run**, per the repository's
hypothesis-first practice. Everything below is a prediction, not a result.

### The arms

At KP 58.8 and KP 60.0, both `d70` readings, historical, production N = 1e5 and
Δt = 225 s. `L_dem` is the ADR-0047 clean-station median: 42.0 m at KP 58.8,
43.0 m at KP 60.0.

| Arm | `geometry.L` | `toe_gradient_relief_factor` | What it represents |
|---|---|---|---|
| `gate` | committed 1998 | None, set explicitly | the production baseline; a bit-identity check, not a result |
| `berm_only` | `L_dem` | None | the measured half of the works, credited alone |
| `joint_0.8` … `joint_0.2` | `L_dem` | 0.8, 0.6, 0.4, 0.2 | both halves, at a swept relief fraction |

### Predictions

- **P1. The static branch is exactly invariant in the relief factor at fixed L.**
  Bit-identical failure matrices, not merely equal column means. *Falsifier:* any
  moved cell means a channel exists that the mapping does not know about, and the
  claim that the drain acts on the gate alone is wrong. The driver refuses to
  report if this fails.
- **P2. The transient branch is one-sided and monotone**: lowering the relief
  factor never raises `P_f,trans` at any level. The gate is a necessary condition
  for erosion and a row that never latches never erodes. *Falsifier:* any level
  where a smaller factor raises the transient probability.
  **AMENDED 2026-08-21, after this prediction fired.** P2 as written above is
  **falsified**, and the pre-registered text is left standing because that is
  what a pre-registration is for. At KP 58.8 under the bulk gradation reading,
  one realization in 100 000 (row 22 790, stage 43.25 m, 2.2 m above the design
  level) fails at relief 0.80 having survived the berm arm. It is a **forward-
  Euler barrier jump**, ADR-0030's pathology, not a physical inversion: at
  Δt = 225 s the relieved arm returns `Z_transient = 0.00000` exactly, the
  signature of one step traversing the whole remaining length, and the
  inversion disappears completely at Δt = 112.5 s and 56.25 s, where the two
  arms agree to five decimals. The realization sits at C_e = 0.314 and
  k_aq = 6.6e-3, deep in the tails of the two inputs ADR-0030 names.

  There is a mechanism, and this axis makes it more likely than the baseline
  does: relief **delays** the gate, so a relieved realization meets its first
  active timestep at a higher driving head and takes a larger first step. A
  gradient-relief axis is therefore a more sensitive probe of the ADR-0030
  discretisation limit than the production configuration is.

  The surviving claim, and the one the driver now enforces, is stronger than a
  tolerance on the count: **every violation must vanish under timestep
  refinement.** Each violating row is re-integrated at 112.5 s and 56.25 s on
  the ADR-0013 integer-subdivision hook, and the driver refuses if a single one
  survives. That tests the continuous-time claim rather than the discrete
  approximation of it, and it does not care how many artifacts there are, only
  whether any of them is real.

- **P3. The berm arm moves both branches.** L enters `H_c` and `Z = L − l_e`, so
  `berm_only` is not a gate-only arm and must not be described as one. It is the
  one arm of this bracket that is not r_e-mediated.
- **P4. The relief needed to close the gate grows with stage.** `i_exit` is
  proportional to `h − z_toe` while `i_c` is very nearly deterministic
  (CoV(γ'_bl) = 0.056), so a fixed relief fraction buys proportionally less at
  high stage: the fragility curve shifts right rather than scaling down, and the
  bracket is widest at low stage and narrowest in the tail.
- **P5. The gate arm outweighs the berm arm** at the same section, because the
  gate is a necessary condition for any erosion at all whereas L only lengthens
  and slows the traverse.
- **P6. Phase 2 rejection stays 0.00 per cent** at both strata. Production
  marginal transient rejection is already 0 there; every arm here makes the prior
  strictly less failure-prone, so rejection cannot rise. *Falsifier:* any nonzero
  rejection.
- **P7. The BEP share at KP 58.8 falls below one half at some arm.** Historical
  share is 0.974. If it crosses 0.5, then "BEP dominates three of four sections"
  is itself as-if-undrained-conditional at two of those three, which the thesis
  does not currently say.

### What would falsify the whole reasoning

If the joint arm at the strongest relief does not materially reduce the annual
probability, then the landside exit gradient is not the binding quantity at these
sections and the guidance mapping does not transfer to this model. The bracket
would then be reported as a negative result and the caveat would stay
unquantified.

---

## Alternatives Considered

### Alternative 1: model the drain as a hydraulic boundary condition
Rejected. It needs the drain geometry, the fill transmissivity and the filter
condition, none of which exist in the secured dataset. It would also be a design
evaluation, which Table `tab: scope register` excludes. This ADR produces a
bracket on a configuration, not a model of a structure.

### Alternative 2: adopt PWRI's 0.3 design gradient as the relief endpoint
Rejected as an *input*. The 0.3 criterion sizes the drain width against the
average gradient in the drain body; the guidance states no equivalence between
that quantity and the foundation blanket exit gradient, and provenance §7.3 warns
that these drains need not have been sized against the seepage exit gradient at
all. Using it would be exactly the invented parameterisation the thesis says it
declined to make. It is recorded in the companion note as a sourced consistency
observation and is not an arm.

### Alternative 3: adopt the ADR-0047 DEM lengths at these two sections
Rejected, and this ADR does not reopen that decision. Adoption would move the
production deliverable; the bracket carries the measured length as a scenario arm
instead, leaving the as-if-undrained result exactly where it is.

---

## Rationale

The axis is the narrowest one that carries both recorded countermeasures, it
perturbs precisely the quantity the guidance names, its central structural claim
is falsifiable by a bit-identity check the driver enforces, and its one
ungrounded degree of freedom is swept rather than assumed. The alternative
available today is the status quo: a caveat repeated in six places with no number
attached to it.

---

## Outcome (measured 2026-08-22)

Full result in the companion note. The headlines, all matrix / posterior /
λ_ac = 250 m / primary, the configuration every RQ3 and RQ4 headline is quoted
at:

- **All four Phase 1 gates bit-identical**; **static invariance exactly 0.0** at
  every level and arm (P1 confirmed, the mapping's falsifier survived);
- conditional at the design level: KP 58.8 **0.2627 → 0.1084** on the measured
  berm alone **→ 0** at 80 % relief; KP 60.0 **0.3143 → 0.1111 → 0**;
- the relief **shifts the curve right rather than scaling it down** (P4): the
  lowest initiating stage moves from 39.75 to 42.00 m (KP 58.8) and 41.25 to
  43.50 m (KP 60.0), both above the design level;
- annual system P_f, historical: KP 58.8 **7.42e-3 → 4.25e-3 → 1.97e-4** (the
  last a lower bound, ADR-0024 raw tail); KP 60.0 **1.80e-3 → 6.40e-4 → 0**;
- 2016 survival rejection: KP 58.8 **5.673 % → 1.551 %** on the measured berm
  alone, KP 60.0 **3.363 % → 0.555 %**; **marginal transient rejection stays
  exactly 0.000 in all 24 replays**;
- **the climate ratio RISES** with credited drainage (KP 58.8 5.51 → 14.22,
  KP 60.0 7.87 → 26.01): the as-if-undrained treatment *understates* warming
  sensitivity at these two sections;
- **the ranking**: KP 58.8 keeps the top under every arm but the strongest, in
  both climates; **KP 60.0 leaves second place for last under every arm,
  including the measured-berm-only arm that assumes nothing about the drain.**

**P2 falsified** (see the amendment above) and **P5 refuted**: there is no single
verdict on berm-versus-gate, because the response is strongly non-linear in the
relief fraction (×2.42 from the berm, ×1.03 from the first 20 % of relief, ×41 at
60 %). That is the strongest argument for having swept the axis rather than
choosing a value.

---

## Consequences

- The thesis can state a range for the protected configuration at KP 58.8 and
  KP 60.0. The as-if-undrained number remains the deliverable in every place it
  is quoted; the bracket qualifies it rather than replacing it.
- The limitations-register row "Toe drainage at KP 58.8 and KP 60.0 not
  represented" moves from quantified `No` to `Yes`.
- The future-research entry "A physical representation of the installed toe
  drainage" loses its second route, the bracketing sensitivity, and retains the
  first, a boundary condition requiring drain-capacity data.
- One new opt-in field, default `None`, dropped from `to_metadata()` when unset.
  No production config carries it. No existing `config_hash` moves; verified
  against all eight committed configs and all persisted sidecars.
- `scripts/drained_configuration_bracket.py` is a companion driver with its own
  bit-identity gate, registered in `production_campaign.COMPANION_EXCLUSIONS` on
  the same ground as the ADR-0045/0046/0048/0049 companions.
- Nothing about the production deliverable changes. No CSV edit, no config
  regeneration, no re-run of the eight sweeps.
- **A latent defect in `fragility_update.verify_posterior_fragility_by_reevaluation`
  was found and fixed in passing**: it forwarded none of the optional M8
  keywords, so the ADR-0045, ADR-0049 and ADR-0050 arms all re-evaluated a
  different model from the one that wrote the matrices they were checking.
  Invisible in production because all three default to absent. Pinned by
  `tests/test_phase2_verification_threading.py`.

---

## References

- PWRI (2014), 河川堤防の浸透に対する照査・設計のポイント, Table 7.1.1 (printed
  p. 33) and §9.1 (printed p. 42);
  `docs/references/tokachi_river_basin/syousasekkei_point1407.pdf`.
- `docs/tokachi_bep_inputs_provenance.md` §6.3 (the countermeasure map), §7.3
  (the three drain rationales), §3.2 (the intervention allocation).
- `docs/tokachi_basin_document_review_2026-07-27.md` §1.12 and register item R8.
- ADR-0008 (the Terzaghi gate and the I_er collapse), ADR-0028 (the static
  comparator's r_e-independence), ADR-0047 (the DEM seepage lengths and the hold
  decision), ADR-0011 (the frozen Phase 2 surface).
- Companion note `docs/decisions/adr0050-drained-configuration-bracket.md`;
  evidence `docs/decisions/adr0050-drained-configuration-bracket.json`.
