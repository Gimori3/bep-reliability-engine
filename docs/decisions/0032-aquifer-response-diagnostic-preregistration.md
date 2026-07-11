# ADR-0032: Aquifer-Response Diagnostic (M4 Lag Gate) — Pre-Registration and Outcome

Date: 2026-07-11
Status: Accepted (Part 1 pre-registration reviewed; Part 2 executed 2026-07-11 —
verdict: **instantaneous default retained**, lag stays off for the production
sweep). See the Outcome section and the companion note
`adr0032-aquifer-response-diagnostic.md`.

## Context

The M4 hydraulic translator exposes the landside aquifer head h_aq(t) in two
interchangeable forms behind one interface (`AquiferHeadModel`): the
**instantaneous** quasi-static translation h_aq = z_toe + r_e·(h − z_toe) —
the Phase 1 default — and a gated **first-order linear-reservoir lag**,
advanced by the exact exponential update (ADR-0004). Which form is active is a
*global-per-run* decision that spec §11 assigns to the **aquifer-response
diagnostic**. That diagnostic **does not yet exist**: `aquifer_response_time`
is called only from tests, and `config.aquifer_lag_active` /
`config.specific_storage_per_m` are honest deferred-consumer metadata fields
whose *named but unbuilt* runtime consumer is precisely this diagnostic
(ADR-0014). Every production sweep to date has run instantaneous by default,
never by demonstration.

This ADR builds that demonstration. It matters because the outcome decides
whether **every** subsequent production run uses instantaneous or lagged
hydraulic translation — it feeds the transient branch's gate head
Δh_blanket(t), so it can move transient P_f and hence the static–transient
gap that is the scientific deliverable of Phase 1.

The methodological hazard is reverse-engineering: if the specific-storage
range, the comparison timescale, or the pass/fail threshold were chosen *after*
seeing τ_aq, the "instantaneous is justified" conclusion (or its opposite)
would be unfalsifiable. **This ADR therefore commits the inputs and the
thresholds before Part 2 computes a single τ_aq.** Part 2 will only evaluate
the pre-registered rules against the pre-registered inputs and record the
outcome; it may not re-tune anything below.

The relevant physics of the diagnostic quantity (from ADR-0004, verified in
`hydraulics.py::aquifer_response_time`):

```
τ_aq = S_s · D_aq · D_bl / k_bl  ≡  λ_in² · S_s / k_aq
```

k_aq **cancels** (higher k_aq speeds diffusion but lengthens λ_in equally), so
τ_aq depends on only three of the seven sampled variables — D_aq, D_bl, k_bl —
times the deterministic specific storage S_s. τ_aq is a per-realization vector
once the lag is active; for the *gating decision* it is evaluated at
representative parameter values to set the one global flag.

---

## Decision

Pre-register the diagnostic as four committed elements. Numbers that depend on
data not yet read (rise time, plateau width) are committed as **operational
definitions** with a fixed extraction recipe, not as free parameters.

### D1. The diagnostic (two independent checks; the lag activates if **either** fails)

**Check A — time-constant ratio.** Form the ratio

```
Π  =  τ_aq / T_flood ,     τ_aq = S_s · D_aq · D_bl / k_bl
```

and compare against the threshold in D3. Rationale for the denominator (D2)
and the threshold (D3) below.

**Check B — native temporal resolution.** Confirm that the native d4PDF
sampling interval resolves the flashy rising-limb / peak-plateau feature that
defines the loading regime. This is a property of the **native** data
(Δt_native = 3600 s, frozen by ADR-0019 §6), *not* of the ADR-0030 integration
grid (225 s): resampling onto integer subdivisions of the native grid refines
the forward-Euler grid but **cannot recover sub-native-grid information**, so a
1 h data cadence that fails to resolve a ~1.5 h plateau is a data-fidelity
limitation the 225 s integration Δt does not repair.

### D2. The comparison timescale T_flood (operational definition)

The physically correct denominator for a first-order **fill** lag is the
timescale over which the forcing rises, not the multi-hour total event
duration (which would understate the lag and is the wrong quantity to compare a
fill time constant against). This ADR therefore *sharpens* spec §11's
"characteristic flood duration" to:

- **Primary: T_rise** — the base-flow-to-peak rising-limb time of the governing
  flashy peak. Extracted in Part 2 from the canonical d4PDF shape
  (`hydrographs.load_canonical_shape`, the same pinned HPB event that drives the
  production sweep) mapped to real time via `native_dt`, and cross-checked
  against the 2016 event hydrograph. This is the committed denominator of Π.
- **Stress denominator: T_plateau** — the peak-plateau width (spec §11
  characterizes the flashy peaks as "on the order of a 1.5 hour plateau").
  Π is *also* reported against T_plateau as a tighter, more demanding
  cross-check. T_plateau ≈ 1.5 h = 5400 s is the pre-registered nominal;
  Part 2 substitutes the measured value.

Both timescales come from M3; neither is a free knob.

### D3. Thresholds (committed)

**Check A threshold — Π\* = 0.10.**

Justification (committed independently of any τ_aq value): for a linear
reservoir dh/dt = (h_inst − h)/τ tracking a ramp forcing of rate R, the
steady lag is exactly τ, so the head deficit at the top of a rise of duration
T_rise and amplitude ΔH = R·T_rise is R·τ = ΔH·(τ/T_rise) for τ ≲ T_rise. The
fractional under-prediction of the peak driving head is therefore ≈ Π. A
threshold Π\* = 0.10 caps the neglected-lag bias on the **peak** gate/erosion
head at ~10%. Above it, the quasi-static assumption biases the transient peak
head by more than the ~5% Monte-Carlo tolerance we already hold P_f to (§11),
so the lag must be modelled. Below it, neglecting the lag is a ≤10% bias in the
**conservative** direction (no attenuation ⇒ over-predicted head ⇒
over-predicted transient P_f), and the instantaneous default is justified and
recorded.

- **Primary rule:** using **S_s at the upper bound** of the D4 range and each
  governing section's **central (prior-mean) θ**, activate the global lag iff
  **Π = τ_aq/T_rise > 0.10** at *either* governing section (D5). Otherwise the
  instantaneous default stands.
- **Secondary rule (committed robustness; activation-only — it can never clear
  something the primary rule flagged):** also evaluate τ_aq at the
  **90th-percentile-τ_aq corner** (high D_aq, high D_bl, low k_bl:
  mean·(1 + 1.28·COV) for D_aq, D_bl; mean·(1 − 1.28·COV) for k_bl, using the
  prior COVs D_aq 0.10, D_bl 0.167, k_bl 0.50). If this corner exceeds 0.10 at
  either governing section while the central case does not, the section is in a
  grey zone and the decision is made by a **direct lag-on vs lag-off transient
  P_f comparison** at that section: activate if any conditioning level's P_f
  shifts by more than that level's §11 P_f CoV. This uses a different, direct
  instrument for the marginal case and cannot relax the primary threshold.

**Check B threshold — Nyquist resolution.** The native resolution is adequate
iff

```
Δt_native ≤ T_feature / 2     (equivalently, ≥ 2 native samples span T_feature)
```

with T_feature = the measured rising-limb/plateau characteristic time (≈1.5 h
nominal). At Δt_native = 3600 s and T_feature ≈ 5400 s this is **expected to be
marginal-to-insufficient** (~1.5 samples across the plateau) — but Part 2 must
measure T_feature and report the actual sample count rather than pre-judge. If
Check B is insufficient, then per spec §11 the response is twofold: (i) record
a **loading-fidelity caveat** (the coarse native cadence, frozen by ADR-0019,
under-resolves the flashy plateau and this is not repairable by ADR-0030
resampling), and (ii) activate the lag, whose low-pass action reduces the
transient branch's sensitivity to the exact — and under-resolved — plateau
shape.

### D4. Specific-storage range S_s (dense Tokachi sand–gravel framework)

**Committed range: S_s ∈ [1×10⁻⁵, 1×10⁻⁴] m⁻¹; decision-driver value = upper
bound 1×10⁻⁴ m⁻¹.**

Basis. Specific storage S_s = γ_w·(α + n·β) with γ_w ≈ 9.81×10³ N/m³, α the
vertical compressibility of the granular skeleton [Pa⁻¹], n porosity, and
β = 4.4×10⁻¹⁰ Pa⁻¹ the compressibility of water. For a **dense sand–gravel
framework** — the Tokachi/Satsunai alluvial-fan deposit is a coarse,
dense braided-river gravel — the skeletal compressibility is bracketed by the
sand and gravel rows of the Domenico & Mifflin (1965) table (as reproduced in
Freeze & Cherry 1979 Table 2.5 and Domenico & Schwartz 1990): α ≈ 1×10⁻⁹ m²/N
(dense, gravel-dominated, stiff) to ≈ 1×10⁻⁸ m²/N (looser, sand-rich). With
n ≈ 0.25–0.30 the water term γ_w·n·β ≈ 1×10⁻⁶ m⁻¹ is negligible against the
skeleton term, giving:

| end | α [m²/N] | S_s = γ_w·(α + nβ) [m⁻¹] |
|---|---|---|
| stiff / gravel-dominated (dense end) | 1×10⁻⁹ | ≈ 1×10⁻⁵ |
| looser / sand-rich end | 1×10⁻⁸ | ≈ 1×10⁻⁴ |

Cross-check via confined storativity S = S_s·D_aq: for D_aq ≈ 8–10 m this range
gives S ≈ 1×10⁻⁴ to 1×10⁻³, squarely the textbook confined-aquifer band (Todd
& Mays 2005; Freeze & Cherry 1979). The decision-driver is the **upper bound**
(1×10⁻⁴ m⁻¹) because τ_aq ∝ S_s, so the longest lag is the worst case for the
gate — using it means a "clear" (Π ≤ 0.10) result is robust rather than an
artefact of an optimistically small S_s. Consistent with ADR-0004, S_s is a
deterministic literature value, not an eighth random variable; its uncertainty
is carried as this bounded range and, if the lag proves consequential, as a
low/high S_s sensitivity run.

> **⚠ Sanity-check flag (for the user, and a candidate question for the
> soil-mechanics collaborator).** This range is *my reading of the standard
> compressibility literature for the generic "dense sand–gravel" class*, not a
> site-measured value. The Tokachi/Satsunai fan gravel could plausibly sit at
> the **stiff/low** end (denser, coarser ⇒ smaller S_s ⇒ shorter lag), or be
> pushed **higher** by interbedded sand/silt lenses or a less-consolidated
> framework. Two things to verify before Part 2's number is trusted: (1) whether
> any OYO 1999 consolidation / oedometer / compressibility data exist for the
> aquifer unit that would pin α directly; (2) the collaborator's view on the
> representative in-situ density/consolidation state. If the true S_s is an
> order of magnitude off, Π scales linearly with it — this is the single input
> most worth confirming.

### D5. Governing cross-sections: KP58.8 and KP60.0

Selected on two criteria that **coincide** at these two sections:

1. **Worst case for the lag (bounds the global activation decision).** τ_aq
   scales with the group D_aq·D_bl/k_bl. By inspection of the section priors
   (geotech CSV, central values only — no τ_aq computed), the two **drained**
   sections carry the thickest blankets (D_bl = 0.85 m) over the lowest blanket
   conductivity (k_bl = 1×10⁻⁶ m/s) on the thickest aquifers (D_aq = 8–9 m), so
   this group is **largest** at KP58.8 and KP60.0 and **strictly smaller** at
   KP57.4 (thinner 0.80 m blanket, higher k_bl 1.6×10⁻⁶) and KP62.0 (thin
   0.45 m blanket, 3× higher k_bl 3×10⁻⁶). The two drained sections therefore
   **upper-bound τ_aq over all reachable sections**: if the lag is negligible
   there, it is negligible everywhere, so the global flag can be decided from
   this pair alone.
2. **Deliverable relevance.** KP58.8 and KP60.0 are the two sections whose
   transient fragility transition the conditioning grid actually brackets — the
   reachable production sections of the ADR-0031 convergence study — so they are
   where an activated lag would actually perturb the reported transient P_f.
   KP62.0's transient transition is unbracketed (raw-tail deliverable, ADR-0024)
   and KP57.4 is berm-only; both are bounded from above on τ_aq by the governing
   pair and are reported for completeness in Part 2, not used to set the flag.

KP63.4 is excluded by default and has no blanket conductivity (k_bl = NaN in the
CSV), so τ_aq is undefined there — consistent with its exclusion.

---

## Alternatives Considered

### Alternative 1 (accepted) — Pre-register S_s range, timescale, and thresholds; compute τ_aq only in Part 2
Pros: eliminates the reverse-engineering hazard the task flags; the
"instantaneous justified" (or "lag required") conclusion becomes falsifiable
against fixed criteria; conservative by construction (upper-bound S_s,
fastest-timescale denominator, τ_aq-maximizing sections). Cons: commits a
threshold (0.10) and an S_s range before seeing the data, so a genuinely
borderline result cannot be nudged — which is the intended discipline, not a
defect.

### Alternative 2 — Compute τ_aq first, then choose the threshold/S_s to match
Pros: guarantees a "clean" verdict. Cons: scientifically illegitimate — the
verdict would encode the choice of inputs, not the physics; explicitly the
failure mode this task exists to prevent. Rejected.

### Alternative 3 — Denominator = total event duration (tens of hours) rather than the rising-limb time
Pros: matches a literal reading of "flood duration"; makes Π small and the
instantaneous default easy to justify. Cons: physically wrong for a **fill**
lag — the aquifer must track the *rise*, not the whole event — so it would
systematically understate the lag and could clear it spuriously. Rejected in
favour of T_rise (with T_plateau as the tighter cross-check), a documented
sharpening of spec §11.

### Alternative 4 — Promote S_s to a random variable (8th sampled dimension)
Pros: propagates S_s uncertainty into τ_aq directly. Cons: contaminates the
clean 7D design Phase 2 filters over, for a gated second-order correction
(ADR-0004 already settled this). Rejected; S_s stays a deterministic
bounded-range literature value.

---

## Rationale

The diagnostic's job is a one-way conservative gate: prove the instantaneous
default is safe, or fall back to the lag. Every discretionary choice is
therefore committed to its conservative pole *before* the numbers: S_s at its
upper bound (longest lag), the denominator at the fast rising-limb timescale
(largest Π), and the governing sections at the τ_aq-maximizing pair (which also
happen to be the two sections where the answer matters for the deliverable).
The 0.10 threshold is anchored to a first-order head-deficit argument that ties
it to the ~5% P_f tolerance the project already enforces, and the direction of
the neglected-lag error (conservative on transient P_f) is stated so a marginal
clear is understood as safe rather than merely lucky. Separating Check B
(native resolution) from Check A keeps an honest distinction between an
aquifer-memory effect (which the lag models) and a data-cadence limitation
(which it does not repair but does damp), while still honouring spec §11's
instruction that either failure activates the lag.

---

## Outcome (Part 2, executed 2026-07-11)

Part 2 applied the rules above **unchanged** (constants imported from
`hydraulics.AQUIFER_RESPONSE_*`; driver `scripts/aquifer_response_diagnostic.py`,
companion note `adr0032-aquifer-response-diagnostic.md`, figure
`docs/figures/adr0032_aquifer_response.png`). τ_aq is from the production LHS
prior (N = 10⁵); the flood timescales are from the pinned canonical event
`HPB_m064_1987` and a peak-stratified spread of ~140 HPB members at each node's
own Eq. 4.19 rating, via `hydrographs.flood_timescales`.

**Verdict: instantaneous default retained at both governing sections — and by
the D5 bounding argument, everywhere.** τ_aq is one to two orders of magnitude
below the pre-registered threshold; no grey zone, no S_s uncertainty introduced.

| quantity (S_s = 1×10⁻⁴, driver) | KP58.8 | KP60.0 |
|---|---|---|
| τ_aq central (prior means) | 680 s (0.19 h) | 765 s (0.21 h) |
| τ_aq 90th-pct corner | 1921 s (0.53 h) | 2161 s (0.60 h) |
| τ_aq sample p99 / max (N=10⁵) | 2453 / 6617 s | 2760 / 7444 s |
| T_rise (10%→peak), median / flashiest-10th-pct | 18 h / 10 h | 18 h / 10 h |
| T_plateau (≥90%), median | 9 h | 9 h |
| **Π = τ_aq/T_rise central** | **0.010** | **0.012** |
| Π corner90 | 0.030 | 0.033 |
| Π stress (sample p99 / flashiest T_rise) | 0.068 | 0.077 |

- **Check A (central Π ≤ Π\*): PASS** at both sections, by ~10×. The 90th-pct-τ
  corner (0.030 / 0.033) also clears, so the D3 **secondary grey-zone rule is
  not triggered**. Even the deliberately adverse conjunction — the sample p99
  τ_aq over the flashiest 10th-percentile rising limb, at the upper-bound S_s —
  stays at 0.068 / 0.077, below Π\*. Only a triple-tail coincidence (≳p99.9 τ_aq
  × the flashiest events × the upper-bound S_s) reaches ~0.18–0.21 for a
  vanishing fraction of rows; since neglecting the lag over-predicts the peak
  head (conservative on transient P_f), this does not move the verdict.
- **Check B (native resolution): PASS.** The empirical flood is far broader than
  spec §11's "~1.5 h plateau" characterization — median rising-limb 18 h,
  plateau 9 h, FWHM 37 h (these are Tokachi-mainstem routed hydrographs, and the
  Eq. 4.19 √-rating further broadens the stage peak). T_feature = 9 h, so
  Δt_native = 3600 s ≤ T_feature/2 = 16200 s comfortably — the peak carries ~9
  native samples. The "~1.5 h" concern is not borne out at these governing
  (mainstem) nodes; if flashy loading matters anywhere it would be on the
  smaller Satsunai tributary, which carries no BEP governing section here.
- **S_s did not bind.** Because Π clears at the *upper-bound* S_s by ~10×, the
  verdict is insensitive to S_s across (and well beyond) the pre-registered
  range: S_s would have to be ~10× the upper bound (~10⁻³ m⁻¹, outside the
  dense-gravel class) before the central Π approached Π\*. The D4
  sanity-check flag therefore does **not** gate this decision — a reassuring but
  worth-recording robustness, since it means the still-unconfirmed S_s cannot
  flip the gate within any physically defensible value.

**Consequence for the sweep.** The production configs already carry
`aquifer_lag_active: false` / `specific_storage_per_m: null`; that default is now
*evidenced*, not merely inherited. **No S_s is introduced as an uncertain input**
— the counterfactual the task asked to be explicit about: had any governing
section tripped Π\*, activating the lag (ADR-0004) would have promoted S_s to a
deterministic-but-uncertain input carried as a bounded low/high sensitivity run
(ADR-0004), the numba backend would have been refused (ADR-0029, numpy-only), and
τ_aq would have entered M8 as a per-realization state via the ADR-0014 channel.
None of that is needed. The engine's instantaneous M4 path is unchanged; the
diagnostic evidence is recorded per run in `metadata['aquifer_response']`.

---

## Consequences

- **Part 2 is now fully constrained.** It may (i) extract T_rise and T_plateau
  from M3 (canonical HPB shape + 2016 event), (ii) evaluate τ_aq at the
  committed S_s upper bound for the central and 90th-percentile θ of KP58.8 and
  KP60.0, (iii) form Π against T_rise (and against T_plateau as a cross-check),
  (iv) run Check B against Δt_native, and (v) apply D3 verbatim. It may not
  re-tune S_s, the denominator, the threshold, or the governing set.
- **Implementation, if the lag activates.** The channel is already
  pre-committed (ADR-0014): set `config.aquifer_lag_active = True` and
  `config.specific_storage_per_m`, thread the flag + S_s through the
  geometry/run-settings dict, and have M8 call `make_head_model(..., lag_active,
  tau_aq_s)` instead of hard-wiring `InstantaneousHead`. No frozen-signature
  change (ADR-0011). Note the ADR-0029 constraint: the numba backend refuses the
  lag, so a lagged sweep runs numpy-only. The outcome and τ_aq are recorded in
  metadata (`aquifer_lag_active`, `tau_aq`), giving the fields their first live
  consumer.
- **Reproducibility / interpretation.** Recording the diagnostic outcome (pass
  values, chosen S_s, T_rise, Π, Check B sample count) makes the instantaneous
  default an evidenced decision rather than an inherited assumption, and lets a
  reviewer re-run the gate under a different S_s without re-deriving the rules.
- **If S_s is later revised** (collaborator input or OYO data), Π rescales
  linearly and only the arithmetic of Part 2 repeats; the rules here are
  unaffected. As the Outcome records, a revision would have to exceed the
  dense-gravel class by ~10× to cross Π\*, so D4 — while still worth confirming —
  does not gate this particular verdict.
- **As-built wiring (2026-07-11).** The pre-registered constants and the gate
  logic live in M4 as `hydraulics.AQUIFER_RESPONSE_{SS_RANGE,SS_DRIVER,PI_THRESHOLD,
  GOVERNING_SECTIONS}` and `hydraulics.aquifer_response_diagnostic(...)`; the flood
  timescales come from `hydrographs.flood_timescales(...)` (M3). `run.py` computes
  the block once per run (`_aquifer_response_block`) and stamps it as
  `metadata['aquifer_response']` alongside the unchanged spec §8
  `aquifer_lag_active` / `tau_aq` fields. The offline study and the production
  metadata share one source of truth, so they cannot drift. Tests:
  `test_hydraulics.py` (constants + verdict logic), `test_hydrographs.py`
  (`flood_timescales`), `test_run.py` (block on both paths).
- **Status Accepted.** Part 1's committed inputs and thresholds were reviewed;
  Part 2 executed against them unchanged and reached the instantaneous verdict.

## Scope amendment (2026-07-11): what the Π screen does and does not detect

The Japanese case-validation campaign (Yabe 2012 and Shikaga 28.75k, where the
engine's instantaneous M4 translation could be compared against calibrated 2D
saturated–unsaturated FEMs at four sites) exposed a scope limit of this
diagnostic. Document-only amendment; no constant, threshold, rule, or wiring
changes:

- **The screen detects elastic leaky-confined response only.** Π is built on
  τ_aq = S_s·D_aq·D_bl/k_bl with a literature elastic S_s. At the Japanese
  sites the FEM damping was governed instead by **unsaturated/finite-fill
  storage** (dead-ended lenses, floodplain-mediated entry, low initial heads):
  matching the observed FEM response requires an effective storativity of
  order 1e-2–1e-1, roughly 100× the elastic S_s·D_aq. The Π screen passed the
  two worst over-translating sites (Yabe 7.3k, 16.10k; engine/FEM 2.0–2.7×)
  and flagged the best-matched one (11.86k; 1.13×) — it does not rank this
  regime. See `docs/validation/yabe-case.md` §3 and
  `docs/validation/shikaga-case.md` §2–3.
- **Per-section applicability check (added to D3's scope).** The instantaneous
  verdict from this diagnostic is valid where the section's aquifer is
  **channel-connected and saturated at base flow**, so that the flood imposes
  no large storage-deficit fill the elastic τ_aq cannot represent. Confirmed
  for all four production sections: the OYO confined-section classification, a
  perennial gravel-bed river in direct contact with the aquifer, and the
  ADR-0020 conditioning records initialized at the base-flow trough. Any
  future section (or replay event) featuring dead-ended permeable lenses,
  entry mediated through an elevated dry foreland, or initial heads well below
  the exit datum falls outside this diagnostic's scope and needs a
  transient-fill assessment, not a larger S_s.
- **Direction if violated.** Where the scope check fails, the instantaneous
  form over-translates the toe head (measured 1.15–2.7× across the four FEM
  points). Post-ADR-0027/0028 this is gate-only and therefore conservative for
  transient P_f, concentrated at the fragility shoulder — see the production
  judgment in `docs/validation/shikaga-case.md` §3, including the registered
  KP58.8 r_e-halved QA member (`scripts/run_sweep.py`).

---

## References
- Phase 1 architecture spec §11 (aquifer-response diagnostic; global flag;
  per-realization τ_aq), §6 (lag insertion line), §1 (M1 timestepper settings).
- ADR-0004 (exact exponential lag update; τ_aq = S_s·D_aq·D_bl/k_bl; S_s
  deterministic; global flag / per-realization τ_aq), ADR-0014 (lag-flag
  threading; deferred-consumer S_s fields; pre-committed activation channel),
  ADR-0011 (frozen M8 signature), ADR-0010 (dict channel), ADR-0019 §6 (native
  3600 s resolution frozen), ADR-0030 (225 s integration Δt via resampling —
  refines the Euler grid, not the loading information), ADR-0031 (KP58.8/KP60.0
  the reachable production sections), ADR-0024 (KP62.0 raw-tail deliverable),
  ADR-0029 (numba backend refuses the lag).
- `bep_reliability_engine/hydraulics.py` (`aquifer_response_time`,
  `make_head_model`, `LaggedHead`, `advance_lag_state`);
  `bep_reliability_engine/config.py` (`TimestepperSettings.aquifer_lag_active`,
  `specific_storage_per_m`); `data/processed/tokachi_bep_inputs.csv` (section
  D_aq, D_bl, k_bl).
- Domenico & Mifflin (1965), *Water Resources Research* — granular
  compressibility; Freeze & Cherry (1979) Table 2.5; Domenico & Schwartz (1990);
  Todd & Mays (2005) *Groundwater Hydrology* — confined-aquifer storativity
  range. **Values are literature-class, not site-measured — see the D4
  sanity-check flag.**
```
