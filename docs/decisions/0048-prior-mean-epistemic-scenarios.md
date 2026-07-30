# ADR-0048: Prior-mean epistemic scenarios (k_aq field-vs-Form-5 bracket, gamma'_bl lower bound)

Date: 2026-07-28

## Status

**Accepted; consequence 3 superseded 2026-07-30** (see the Amendment at the end — the
"largely cancels in the static-vs-transient ratio" claim was refuted by measurement at all
four matrix sections; every decision and every measured number below stands).

**Accepted** — the mechanism (`config.prior_mean_scenario`), its two instantiations, and
the decision **not** to change any production prior mean are recorded here. Amends
`docs/tokachi_bep_inputs_provenance.md` §3.6 (whose "no impact on the CSV" disposition of
the OYO field permeabilities is no longer neutral) and adds §8 there. Companion to
**ADR-0045** (m_p) and **ADR-0046** (z_toe), whose default-OFF / bit-identical-baseline /
hash-preserving pattern this follows exactly. Parent decisions unchanged; no production
sweep is re-run and no persisted result is altered.

---

## Context

Every cell of `data/processed/tokachi_bep_inputs.csv` traced to a **single** source, the
OYO Corporation (1999) investigation, until 2026-07-28. On that date six Kunijiban (PWRI)
borehole logs from **two independent campaigns** — 2013/14 十勝川上流地質調査業務
(大地コンサルタント) and 2005/06 十勝川上流堤防点検業務 (北開水工コンサルタント) — were
transcribed into `data/raw/borehole_and_soil_survey/` and analysed against the production
inputs (provenance §8).

Most of what they produced is corroboration that changes nothing: `D_aq` at KP 58.8 agrees
to −2.5%, the aquifer base is identified as the Nagareyama Formation at three consistent
elevations, `relative_density_insitu = 0.725` is confirmed (and shown mildly conservative)
by an SPT-derived D_r ≈ 78%, and the two 2013/14 holes turn out to sit ~300 m riverward of
the levee, which disqualifies them from bearing on `D_bl` or `z_toe` at all.

Two findings do **not** resolve into corroboration, and both have the same shape: a
production prior **mean** is contradicted, or bounded, by a measurement population that
the marginal's CoV cannot absorb.

**1. `k_aq` — a systematic, cross-campaign population disagreement.** The production
means (1.0e-3 to 3.0e-3 m/s) are the OYO 様式-5 *analysis constants*. Provenance §3.6
already recorded four OYO **field** permeability tests one to two orders lower, and
disposed of them with "no impact on the CSV, since `k_aq_mps` is anchored to the Form 5
analysis constants, not the field tests." That was defensible while the field tests were
a single-campaign minority. The 2005/06 campaign supplies two more — 5.15e-4 m/s at a
**landside toe** and 8.61e-5 m/s on the **riverside** — that land squarely inside the OYO
field range. The field population is now **six members, two contractors, two decades**,
geometric mean 5.94e-5 m/s: a **17× to 51×** offset below the adopted constants that
reproduces independently.

The offset cannot be absorbed by the existing spread. Under Lognormal(mean, CoV 0.50) the
lower field value sits **5.0σ (KP 60.0/62.0) to 7.3σ (KP 57.4)** below the prior median —
effectively outside the prior's support. The CoV carries aleatory scatter; this is an
epistemic disagreement about the mean.

Neither population is "true". Single-borehole tests (JGS 1314) sample a small radius
around the screen and are biased **low** relative to bulk horizontal conductivity in a
heterogeneous gravel aquifer; Form-5 constants for a seepage FEM are chosen to represent
bulk horizontal k and are deliberately **high**. They bracket the answer. `k_aq` is also
not a minor input: it drives the Mazure λ_in/λ_out and hence r_e and the uplift/heave
gate, and it enters the Sellmeijer critical head — so a 1.5-order mean shift is a
first-order sensitivity, and ADR-0033 already flags `C_e × k_aq` as carrying the fm7
interaction gap.

**2. `gamma_bl_sub` — a lower bound from three in-situ densities.** Three
sand-replacement tests give γ_t − γ_w = 5.98 / 6.28 / 8.44 kN/m³, which **bracket** the
6.90 kN/m³ prior mean. All three are on *moist, unsaturated embankment fill*, not the
mapped natural A_c, so they bound rather than measure. Only the lower end is interesting,
because γ'_bl drives uplift and heave directly (and under the Terzaghi collapse
`Z_heave = Z_uplift/D_bl`), i.e. the unsafe direction.

---

## Decision

**1. No production prior mean changes.** `tokachi_bep_inputs.csv`, the generated configs
and all eight persisted production sweeps are untouched. `k_aq` stays on the Form-5
constants; `gamma_bl_sub` stays at 6.90 kN/m³.

**2. Carry the epistemic range as an opt-in, default-OFF scenario axis.** New optional
`Config.prior_mean_scenario` (`PriorMeanScenario`: `enabled`, `label`, `factors`) applies
**multiplicative factors to named theta prior means** and nothing else — families, CoVs,
bounds, the coupling, the seed and the LHS design are untouched, so a scenario draw is an
exact multiplicative shift of the baseline population under the same design.

**3. One shared definition of what gets sampled.** `Config.effective_marginal_specs()` is
the single source of the marginals actually drawn; both `run._sample_prior` and the
Phase 2 replay's bit-for-bit theta regeneration call it. A scenario run therefore replays
as itself rather than silently regenerating the baseline population.

**4. Hash preservation.** `prior_mean_scenario` is dropped from `to_metadata()` when
`None`, so every pre-ADR-0048 persisted run reconstructs to a byte-identical
`config_hash` and the Phase 2 replay gate keeps passing. `scripts/generate_configs.py`
deliberately does **not** emit the block (unlike ADR-0037's `length_effect`), so no
production config hash moves at all.

**5. Unmissable when exercised.** An enabled scenario stamps
`metadata['prior_mean_scenario']` with label, factors, and both baseline and effective
means; a baseline run carries no such key. Companion outputs are name-segregated under
`results/sensitivity/adr0048_prior_means/`.

**6. An enabled-but-empty scenario is a config error**, not a silent no-op.

**7. The four instantiations measured** (`scripts/prior_mean_scenario_companion.py`,
evidence `docs/decisions/adr0048-prior-mean-companion.json`): `k_aq_field_toe`
(target 5.15e-4 m/s, the landside-toe test), `k_aq_field_geomean` (target 5.94e-5 m/s,
the six-member field geometric mean), `k_aq_regional_upper` (target 1.0e-2 m/s, the upper
end of the Chiyoda new-channel regional band — the *unconservative* end, and the bounding
run the thesis Discussion had already recommended as follow-on work), and
`gamma_bl_sub_lower` (target 6.0 kN/m³).

---

## Alternatives Considered

### A. Re-anchor `k_aq` to the field-test population
Pros: uses direct measurement rather than a consultant's analysis constant; six members
now, across two campaigns. Cons: single-borehole tests are known to be biased low for
bulk horizontal k, which is the quantity the seepage path needs; adopting them would
swap one defensible-but-partial population for another and force a full campaign re-run
(8 sweeps, Phase 2, Phase 3). Rejected — the honest state is a bracket, not a new mean.

### B. Widen `CoV(k_aq)` to swallow the range
Pros: no new config axis. Cons: misrepresents an epistemic mean offset as aleatory
scatter, would silently inflate the tails of every production result, breaks the
`tests/test_configs.py` CoV pin (which traces to the thesis prior table), and destroys
comparability with every persisted sweep. Rejected.

### C. Per-parameter dedicated blocks (a `k_aq_scenario` and a `gamma_bl_scenario`)
Pros: each self-documenting. Cons: two near-identical mechanisms for one question shape;
a third such finding would add a third. Rejected in favour of one general mechanism whose
`label` carries the meaning.

### D. Do nothing and record the finding in prose only
Pros: zero code. Cons: leaves the largest unquantified epistemic knob in the model
unmeasured, and leaves §3.6's set-aside resting on an argument its own evidence base has
outgrown. Rejected.

---

## Rationale

The default-OFF/bit-identical/hash-preserving pattern is chosen because it is the only one
that lets the thesis **state a measured range** without invalidating a closed production
campaign. It follows ADR-0045 and ADR-0046 line for line, so the repo gains no new idiom.

Scaling the *mean* while holding the CoV, family and seed fixed makes the scenario
interpretable: for a lognormal under a fixed LHS design it is an exact multiplicative
shift of every realization, which the test suite pins directly. That keeps the comparison
attributable to the mean alone rather than to a re-drawn population.

Routing both Phase 1 and the Phase 2 replay through `effective_marginal_specs()` is what
prevents the subtle failure mode where a scenario run's provenance verification silently
compares it against the baseline population and either false-fails or, worse, passes for
the wrong reason.

---

## Consequences

**Implementation.** New `PriorMeanScenario` model and `Config.prior_mean_scenario` field
(`config.py`); `Config.effective_marginal_specs()`; `run._sample_prior` and
`bayesian_reliability_updating/replay.py` both route through it; metadata stamp in
`run.py`. No physics module is touched; M4-M8 never learn the scenario exists. The frozen
ADR-0011 Phase 2 surface (`evaluate_realization`, `EvaluationResult`) is **not** widened.

**Tests.** `tests/test_prior_mean_scenario.py` (12 tests) pins: absent-block and
disabled-block bit-identity of both the theta matrix and the end-to-end failure matrices;
`to_metadata()` omission of the None case; means-only application with every sibling spec
unchanged; the exact multiplicative column shift; metadata stamped only for a scenario
run; and the three validation refusals.

**Measured effect — the headline.** Ratio = scenario P_f,trans / baseline P_f,trans,
N = 1e5, matrix d70. The `k_aq` ladder runs low-to-high across the full epistemic range;
the fourth scenario, `k_aq_regional_upper` at 1.0e-2 m/s, is the upper end of the Chiyoda
new-channel regional band and was added because the thesis Discussion had already
identified it as beyond the prior's 95th percentile and recommended exactly this
bounding run as follow-on work.

| Section | scenario (k_aq mean) | lowest reachable stage | shoulder | grid top |
|---|---|---|---|---|
| KP 58.8 | `field_geomean` 5.94e-5 (÷34) | 0 | 0 | ×0.024 |
| KP 58.8 | `field_toe` 5.15e-4 (÷3.9) | 0 | ×0.088 | ×0.743 |
| KP 58.8 | **baseline** 2.0e-3 | — | — | — |
| KP 58.8 | `regional_upper` 1.0e-2 (×5) | **×198** | ×1.99 | ×1.01 |
| KP 60.0 | `field_geomean` 5.94e-5 (÷17) | 0 | ×1.9e-4 | ×0.082 |
| KP 60.0 | `field_toe` 5.15e-4 (÷1.9) | 0 | ×0.395 | ×0.924 |
| KP 60.0 | **baseline** 1.0e-3 | — | — | — |
| KP 60.0 | `regional_upper` 1.0e-2 (×10) | **×2428** | ×1.89 | ×1.016 |

`gamma_bl_sub_lower` (6.0 vs 6.90 kN/m³) for comparison: transient ×1.29 (KP 58.8) /
×1.50 (KP 60.0) at the lowest reachable stage, decaying to ×1.00 by the shoulder;
static **exactly** ×1.000 at every level.

`k_aq` is confirmed as **the largest single epistemic knob quantified in this project**,
by a wide margin — larger than ADR-0045's m_p (static shoulder ×2.2–2.4) or ADR-0046's
z_toe. The mechanism is monotone and one-directional: higher k_aq lengthens the Mazure
leakage length (raising r_e and so the head reaching the exit, an easier uplift/heave
gate) *and* lowers the Sellmeijer critical head, both pushing P_f the same way.

**Scientific interpretation — state the bracket, not one end of it.** The production
configuration sits **inside** the epistemic bracket, roughly mid-range on a log scale,
not at either extreme. Reading only the two field-test scenarios would license the
comfortable but **wrong** conclusion that production is conservative; the regional upper
end is a factor of 5–10 above the adopted means and amplifies low-stage transient P_f by
two to more than three orders of magnitude.

Three properties of the bracket matter for how results may be quoted:

1. **It is strongly stage-dependent.** The spread is enormous at the low-stage end
   (where P_f is small and the exponential-like sensitivity bites) and collapses toward
   unity in the design tail, simply because P_f saturates at 1. Quoting a single
   "k_aq uncertainty factor" is therefore meaningless without the stage.
2. **It dwarfs the reported statistical uncertainty.** The spec §11 Monte Carlo CoV
   (<5%) and the ADR-0024 Clopper–Pearson bands describe sampling noise only. Absolute
   P_f levels **must never be quoted as absolute risk without this epistemic range
   attached.**
3. ~~**It leaves the comparative results intact.** The static-vs-transient bias of Stage 6.6
   is a *ratio* computed on a shared sample at fixed k_aq, so a common shift in the k_aq
   mean moves both branches together and largely cancels. The thesis's headline
   comparative claims are therefore robust to this knob in a way its absolute
   probabilities are not — which is the single most important consequence to carry into
   the Discussion.~~
   **SUPERSEDED 2026-07-30 — REFUTED BY MEASUREMENT. See the Amendment below.** The
   replacement is: *the k_aq bracket does **not** cancel in the static-vs-transient ratio;
   it amplifies it, by 1.1 to 1.8 decades of ρ per decade of k_aq at all four matrix
   sections.* Do not carry the struck text into the Discussion.

`gamma_bl_sub` is the opposite: nearly inert. The static branch is **exactly** invariant
(ratio 1.000 at every level — an independent confirmation of the ADR-0028 separation, in
which the static Sellmeijer comparator has no uplift/heave exposure at all), and the
transient effect is confined to the very bottom of the grid (+29% at the lowest reachable
level, decaying to +0.2% by the shoulder). The lower-bound density reading is therefore
**not** a threat to any conclusion.

**Runtime/reproducibility.** Zero cost when off (one `is None` check). Persisted results,
config hashes and the Phase 2 replay gate are all unaffected; the full suite is green.

**Not done, deliberately.** No production re-sweep; no Phase 2 or Phase 3 re-run under a
scenario; no change to `d70_m`, `D_bl_m` or `z_toe`. Whether the k_aq bracket should
propagate to the Phase 3 annualized numbers is left open — it would multiply the campaign
by the number of scenarios and is a project-owner call.

---

## Amendment — 2026-07-30: consequence 3 refuted; the cancellation rule narrowed

**Status of this amendment:** Accepted. It changes no decision, no default and no
measured number of this ADR; it withdraws one *interpretive consequence* that later
measurement refuted. Decisions 1 to 7 and the measured ratio table stand unchanged.

**What was withdrawn.** Consequence 3 above (struck through in place) asserted that the
k_aq bracket "largely cancels" in the Stage 6.6 static-vs-transient ratio, and called
that the single most important consequence for the Discussion. It was **argued, never
measured** — the argument being that a shift in a prior mean applied to a shared sample
must move both branches together.

**What refuted it.** `docs/decisions/epistemic-bracket-synthesis.md` §4(c) (2026-07-30,
driver `scripts/epistemic_bracket_synthesis.py`, evidence
`docs/decisions/epistemic-bracket-synthesis.json`) measured the cancellation directly,
using the ADR-0047 §4.5 paired-bootstrap ratio-of-ratios
ρ = (P_static/P_transient)_arm ÷ (P_static/P_transient)_baseline — 2000 replicates over
the 16 joint pattern counts, null pinned at ρ = 1.0 exactly, baselines gated bit-identical
on the whole failure matrices. Maximum **resolved** departure factor:

| arm | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| `k_aq_field_geomean` | **82.2** | **65.6** | **162.9** | **45.6** |
| `k_aq_field_toe` | 9.31 | 6.96 | 3.40 | 2.24 |
| `k_aq_regional_upper` | 4.74 | 8.36 | 33.35 | 11.73 |
| `m_p` (the control) | 1.14 | 1.14 | 1.22 | 1.07 |

The refutation holds at **all four** matrix sections, including KP 58.8 and KP 60.0 — the
two this ADR itself measured — and resolves at essentially every evaluated level. The
departures are **larger than the L bracket's**, which ADR-0047 §4.5 had already
established as non-cancelling.

**Why it could never have cancelled — the mechanism, read from the code.** Consequence 3
accounted for exactly one of k_aq's three channels into the limit states:

| channel | implementation | branches reached |
|---|---|---|
| `H_c` via `_factor_Fs(d_70, k_aq, L, α)` | `sellmeijer.py` | **both** — common mode |
| `r_e` via the Mazure leakage lengths → uplift/heave gate | `hydraulics.py`, ADR-0028 | **transient only** |
| the erosion rate `dl/dt = 89·C_e·(k_aq·max(0, H_erosion − H_eq)/L)^0.81` | `progression.py` | **transient only** |

Two transient-only channels against one shared channel. Normalised for the unequal shift
sizes the scenarios impose (a scenario sets an absolute *target* mean, so k_aq moves ×0.17
at KP 57.4 but ×0.515 at KP 62.0), non-cancellation is section-independent at **1.1 to 1.8
decades of ρ per decade of k_aq** — above 1.0 everywhere, meaning the ratio does not merely
fail to cancel, it **amplifies**: the transient branch is more than an order of magnitude
more k_aq-sensitive than the static branch, per decade.

**The rule that replaces it, and that must be carried into the Discussion instead:**

> A bracket cancels in the static-vs-transient ratio **only if it is pure common-mode**.
> `m_p` qualifies **by construction**, because ADR-0045 §2 applies it to the single-source
> `H_c` in *both* of its uses — one model-form belief per realization. `k_aq`, `z_toe` and
> `L` each carry at least one transient-only channel, and **none of them cancels**.
> Cancellation must be **measured per knob**, never assumed from "shared sample, fixed
> parameter".

**Consequence for how this ADR's numbers may be quoted.** Consequences 1 (strong stage
dependence) and 2 (the bracket dwarfs the statistical uncertainty) survive, the latter
**confirmed for `k_aq` only** — at KP 62.0's design HWL the entire `m_p` bracket (×2.80) is
narrower than the Clopper–Pearson band (×2.95) around the same baseline, so the general
form of consequence 2 must not be claimed either. The Stage 6.6 bias headlines are
therefore conditional on **`k_aq` as well as on `L`**, and the k_aq conditionality is the
larger of the two. `gamma_bl_sub` remains inert in the ratio for an unrelated reason: it
never touches the static branch at all (ADR-0028), so its static ratio is exactly 1.000 at
all 98 evaluated levels.

---

## References

- `docs/decisions/epistemic-bracket-synthesis.md` and `.json` (2026-07-30) — the
  measurement that refuted consequence 3; `scripts/epistemic_bracket_synthesis.py`.
- ADR-0047 §4.5 — the paired-bootstrap ratio-of-ratios statistic reused here, and the
  first measured non-cancellation (the L bracket).
- `docs/tokachi_bep_inputs_provenance.md` §3.6 (amended), §8 (new).
- `data/raw/borehole_and_soil_survey/` — PDFs, `TRANSCRIPTION_*.csv`, `SOURCE_METADATA.md`.
- ADR-0045 (m_p), ADR-0046 (z_toe) — the default-OFF companion pattern imitated here.
- ADR-0033 (GSA) — `C_e × k_aq` interaction; ADR-0028 — static/gate separation.
- ADR-0012 — two-population k_aq/d_70 decoupling (untouched by the mean shift).
- JGS 1314-2003, single-borehole permeability test (the low-bias argument).
- `scripts/prior_mean_scenario_companion.py`, `docs/decisions/adr0048-prior-mean-companion.json`.
