# Canonical-shape invariance: which results depend on the pinned d4PDF event, and which cannot

**Status:** Accepted (construction/audit note). **No ADR, no code, no figure, no
evidence JSON, nothing written to `results/`.** No sweep, study driver, campaign or
figure regeneration was executed for this note; every claim below is read off source
or off already-committed records.

**Date:** 2026-08-09
**Scope:** defence-brief item A1 ("every conditional curve conditions on one canonical
ensemble event").
**Parents:** ADR-0020 (canonical event pinning), ADR-0023 (shape-invariant climate
axis), ADR-0040/0041 (Stage 6.6 ladder), ADR-0035/0036 (Phase 2 replay), ADR-0042
(Uemura surface curves).
**Sources read:** `bep_reliability_engine/{run,hydrographs,evaluator,gap_decomposition,config}.py`,
`bayesian_reliability_updating/{replay,events}.py`, `scripts/{generate_configs,thesis_figure_gaps,foreshore_width_study,stage6_6_gap_decomposition,phase3_campaign,generate_uemura_surface_curves}.py`,
`tests/test_configs.py`, `docs/decisions/phase2-peak-shortcut.json`,
`docs/decisions/adr0032-aquifer-response-diagnostic.md`.

---

## 0. Summary

The pinned canonical event `HPB_m064_1987` reaches the results through exactly one
channel: it supplies the **time series** `h(t)` that the M7 timestepper integrates. It
does **not** supply the peak. `conditioning_record_for_level` sets
`peak = level_m` verbatim (`hydrographs.py:731`), and M8's static branch reads
`hydrograph.peak` and nothing else off the record (`evaluator.py:874-877`).

Everything that consumes only `peak` is therefore **exactly** invariant to the choice
of canonical member, not approximately so. That is a much larger part of the thesis
than the limitations register currently concedes: the entire static branch, six of the
ten Stage 6.6 comparators, the whole static sub-lattice and its Shapley attribution,
and the entire Phase 2 rejection result.

Three of the four claims put to this audit are confirmed as stated. **C2 is confirmed
for the component magnitudes and refuted as stated for the reported percentages**: the
head-convention component is exactly invariant in probability units, but its *share*
(0.75 to 0.97 at design level) is a fraction whose denominator contains `C4`, so the
shares are shape-conditional. Section 2 gives the correction.

---

## 1. What is shape-conditional and what is not

`peak`-only ⇒ invariant. Anything that reads `record.h` ⇒ conditional.

| Result | Invariant? | What settles it |
|---|---|---|
| **Phase 1 static branch** `P_f_static_raw`, its lognormal fit, its Clopper-Pearson band, `Z_static` | **Exactly invariant** | `evaluator.py:874-877` (batch) and `542-545` (scalar) read `float(hydrograph.peak)` and never `record.h`; `hydrographs.py:731` sets `peak=level` verbatim; `resample_record` carries `peak=record.peak` through unchanged (`hydrographs.py:804`) |
| `H_c`, `H_c_transient`, `l_c`, `lambda_in`, `r_e`, `metadata['leakage_geometry']` | **Exactly invariant** | All are functions of theta, geometry and the deterministic Sellmeijer inputs only; no record argument reaches M6 or M4 |
| **Phase 1 transient branch** `P_f_trans_raw`, its fit, `l_e`, `t_uh`, `metadata['mc_convergence']` (transient) | Conditional | `evaluator.py:881` passes `np.asarray(hydrograph.h)` into `integrate_progression` |
| Stage 6.6 `C0`, `C0b`, `C1`, `C2` | **Exactly invariant** | `gap_decomposition.py:367-374`: `raw_load_m = float(record.peak) - z_toe_m`, `crack_load_m = raw_load_m - CRACK_RESISTANCE_FACTOR * d_bl_m`, compared against `diag_b.H_c` / `diag_a.H_c_transient` |
| Stage 6.6 `C3a`, `C3b` (analytic sustained-peak limit) | **Exactly invariant** | `gap_decomposition.py:353-360` builds the gate from `sustained_peak_record(level_m, ...)`, a *constant* record synthesised from the grid level; `375-376` combines that gate with `crack_load_m` and `H_c` |
| Stage 6.6 `C4a`, `C4b`, `C4c`, `C4d` | Conditional | `gap_decomposition.py:334-348, 377-380`: four `evaluate_batch_diagnostics` calls on the canonical `record` |
| Stage 6.6 `static_pair_shapley` (both orderings, both Shapley values, the interaction) | **Exactly invariant** | `gap_decomposition.py:871-879`: every expression is a linear combination of `C0`, `C0b`, `C1`, `C2` only |
| Stage 6.6 Euler-flip counts (all five) | Conditional | `gap_decomposition.py:401-407`: every counter has a `C4*` term |
| **Phase 2 rejection fractions** (5.673 % KP 58.8, 3.363 % KP 60.0) and **marginal transient rejection = 0 at all eight strata** | **Exactly invariant** | `events.py:442-450` builds the record from the observed Obihiro gauge series through the section rating, then `475-484` anchors it to the surveyed trace; `replay.py:387-400` evaluates that record. `replay.py` imports neither `load_canonical_shape` nor `conditioning_record_for_level` (`replay.py:42-51`) |
| Phase 2 **posterior fragility curves** | Conditional (transient branch only) | The posterior masks the retained Phase 1 failure matrices; the transient matrix carries the shape |
| Peak-shortcut over-rejection factor (2.75, 3.90) | Conditional **through the numerator only** | `scripts/thesis_figure_gaps.py:499` numerator; `:500` denominator. See section 3 |
| `metadata['aquifer_response']` `pi_central`, `margin_vs_threshold`, `rise_10_90_s`, `fwhm_s` | Conditional | `run.py:747-752` calls `flood_timescales(canonical.source_record.h, ...)`. The *published* Pi over the ensemble-median `T_rise` = 18 h is not conditional; the per-run stamp is |
| ADR-0033 GSA on the static indicator and `Z_static` | **Exactly invariant** | Same static path; the record enters only via `peak` |
| ADR-0033 GSA on the transient indicator and `l_e/L` | Conditional | `scripts/gsa_study.py:242` builds the record via `_hydrograph_for_level(level, cfg, canonical)` |
| Phase 3 hazard side (annual-max stage distribution, climate signal) | Invariant of the canonical choice | `system_integration/hazard.py:311-322` streams **all** members of each workbook; the canonical member is not consulted |
| Phase 3 BEP curves, RQ3 dominance shares, RQ4 annual probabilities | Conditional | They consume the Phase 1/Phase 2 transient curves |
| Phase 3 **Uemura surface curves** | Conditional, **on the same member** | `scripts/generate_uemura_surface_curves.py:69` `CANONICAL_EVENT = "HPB_m064_1987"`, a hard-coded module constant. This is the confound named in section 4 |
| R10 `v*` at design HWL | Conditional | `scripts/foreshore_exhaustion_study.py:266` uses `conditioning_hydrographs_for_config` |
| R10 `v*` under the 2016 record and under the d4PDF ensemble | Invariant of the canonical choice | Different forcings entirely |
| ADR-0045 / 0046 / 0047 / 0048 companion arms, **static side** | **Exactly invariant** (and their static `ratio == 1.000` assertions are structural, not empirical luck) | Same static path |
| ADR-0025 foreshore sensitivity, static side (`max abs Delta P_f,static` exactly 0) | **Exactly invariant** | ADR-0028 removed `r_e` from the static branch; the static branch is additionally record-free apart from `peak` |

**One caveat that is about executability, not values.** The shape-invariant results
still cannot be *computed* without the workbook: `run.py:314-320` loads the canonical
shape before any level is evaluated, and `gap_decomposition.py:597` calls
`conditioning_hydrographs_for_config` unconditionally. Invariance is a property of the
numbers, not a claim that the static branch runs on a fresh clone.

### C1: confirmed

> The static branch is exactly invariant to the canonical shape, because the static
> comparator consumes the scalar conditioning level `h_i` verbatim and never touches a
> loading record.

Confirmed, with the chain of custody made explicit:

- `hydrographs.py:728-737` returns the level record with `peak=level` (the docstring at
  `:682-684` states "`peak` is set to `level_m` **verbatim**", and the normalisation at
  `:586-594` is what makes `max(h)` agree to within one ulp);
- `hydrographs.py:801-808` preserves `peak` bit-for-bit across the ADR-0030 225 s
  refinement;
- `evaluator.py:874-877` computes `h_peak_m = float(hydrograph.peak)`,
  `static_head = h_peak_m - z_toe_m`, `z_static = h_c - static_head`,
  `failure_static = z_static <= 0.0`. `record.h` is not read until line 881, inside the
  transient branch. The module docstring already fixes this as policy
  (`evaluator.py:105-107`: "the static branch uses `hydrograph.peak` ... not a
  recomputed `max(h)`; `peak` is treated as authoritative", ADR-0010).

So `P_f_static_raw` is a pure function of `(theta, L, m_p, geometry, deterministic
Sellmeijer inputs, conditioning grid)`. Swapping the canonical member cannot move a
single static failure flag.

### C3: confirmed

The Phase 2 record is built from the observed 2016 Obihiro stage series, inverted
through the gauge rating and pushed forward through the section's own rating
(`events.py:422, 442-450`), then amplitude-anchored to the surveyed flood trace
(`events.py:475-484`). The canonical d4PDF shape appears nowhere in that path, and
`replay.py` does not import the functions that would produce it (`replay.py:42-51`).
The rejection fractions and the nesting result are therefore invariant.

Two boundary points worth stating rather than leaving implicit:

- The replay reconstructs the Phase 1 `Config` from the persisted snapshot and
  hash-checks it (`replay.py:220-228`). `canonical_event_ids` is inside that hash, so a
  shape-variant Phase 1 run replays **as itself**, self-consistently. The hash gate is
  not a barrier to a shape study; it is a barrier to *editing the committed configs*
  (section 4).
- The **posterior fragility curves** are not invariant. They are masks over the
  retained Phase 1 matrices, and the transient matrix carries the shape. The invariant
  object is the rejection fraction, i.e. the evidence, not the updated curve.

---

## 2. The one ladder step the shape can reach, and what that does to Chapter 6's shares

### The step

The ladder definitions are literal (`gap_decomposition.py:148-168`):

```
PHYSICS: head_convention C0-C1 | dimensional C1-C2 | initiation_gate C2-C3a | temporal_net C3a-C4a
ENGINE:  head_convention C0-C1 |                     initiation_gate C1-C3b | temporal_net C3b-C4b
```

Cross-referencing against the invariance column of section 1: `C0`, `C1`, `C2`, `C3a`
and `C3b` are all invariant, so in **each** ladder exactly one telescoping step,
`temporal_net`, touches the shape. Everything else in the decomposition that moves is
outside the telescoping chain:

| Auxiliary (`gap_decomposition.py:160-168`) | Shape-exposed? |
|---|---|
| `dimensional_at_static` (C1-C2), `dimensional_at_sustained` (C3b-C3a) | No |
| `heq_conservatism_engine` (C4b-C4c), `heq_conservatism_physics` (C4a-C4d) | Yes |
| `dimensional_at_transient` (C4b-C4a) | Yes |
| `total_gap_engine` (C0-C4b), `total_gap_physics` (C0-C4a) | Yes (they are the ladder sums) |

So the claim as put is right, with the two ladder totals added to the exposed list.
This is a strong result and it is worth saying why it holds rather than treating it as
luck: **ADR-0040 Decision 2 made the pseudo-static comparator an exact closed form**
(`gap_decomposition.py:285-297`, `flags = gate_open & (h_erosion > h_c_transient)`)
precisely so it would not need an arbitrary hold duration. A by-product of that design
choice is that `C3` never integrates anything, and therefore the initiation-gate
component of the gap is shape-free by construction.

### The correction to C2

C2 says the head-convention component "which the report puts at 75 to 97 per cent of
the design-level gap" is shape-invariant by construction. **The component is; the
percentage is not.** `component_table` computes

```python
total = p_f["C0"] - p_f[endpoint]                     # gap_decomposition.py:796
fraction = np.where(total_resolved, delta / total, np.nan)   # :811
```

with `endpoint` in `("C4a", "C4b")` (`:792-795`). The numerator `delta` for
`head_convention` is `P_f(C0) - P_f(C1)`, exactly invariant. The denominator contains a
`C4`, which is not. So under a shape swap:

- the head-convention component in **probability units** does not move by one bit;
- the head-convention **share** moves, and moves *upward* if the alternate member
  delivers less erosion (smaller `C4`, smaller total gap, same numerator over a smaller
  denominator).

Applied to `tab: gap components` in Chapter 6 (`mainmatter/5. Results of the System
Integration and Climate Sensitivity Analysis.tex:538-575`), column by column:

| Column | Status |
|---|---|
| `C0` static | Exactly invariant |
| `C4b` transient, `Transient failures` | Conditional |
| `Total gap` | Conditional (through `C4b`) |
| `head` share 0.75 / 0.97 | Conditional (invariant numerator, conditional denominator) |
| `gate` share (0.00 to 0.03) | Conditional (same structure); the *component* is invariant |
| `temporal` share | Conditional in numerator and denominator |
| `Pure duration` `P(C3b)/P(C4b)` | Conditional **through the denominator only** |

The clean, defensible sentence is not "the head-convention component is 75 to 97 per
cent whatever the event", but: **the head-convention and initiation-gate components are
exactly invariant in probability units; the shares they carry are not, because the
denominator is the total gap and the total gap ends at a transient comparator.**

That is still a substantial strengthening. At KP 62.0's design HWL the head component is
0.75 x 1.8e-3 = 1.35e-3 and at KP 57.4's it is 0.97 x 1.2e-3 = 1.16e-3, and neither
number can move under any canonical event whatsoever.

### One further construction result the brief did not ask for

The design-HWL **bias** `B = P_static / P_transient` (ADR-0040 HWL resolution: 26.9
[21.6, 35.3] at KP 62.0, bound `B >= 148` at KP 57.4) has an **invariant numerator and
a conditional denominator**. The peak-shortcut factor has the opposite structure
(section 3). Therefore under one and the same shape swap the two headline factors move
in **opposite directions**: a member with less above-toe exposure lowers
`P_transient`, which *raises* `B`, and lowers the peak-only numerator, which *lowers*
the peak-shortcut factor. Any future shape study must report both, or it will look like
it confirmed one thing and broke another.

---

## 3. The peak-shortcut factor

### C4: confirmed

`scripts/thesis_figure_gaps.py`:

```python
peak = float(record["event_chain"][-1]["record"]["peak_m_msl"])      # :497
grid = np.asarray(result.conditioning_grid, dtype=float)             # :498
peak_only = float(np.interp(peak, grid, np.asarray(result.P_f_trans_raw)))  # :499
replay   = float(record["posterior"]["rejection_fraction"])          # :500
...
"over_rejection_factor": (peak_only / replay) if replay > 0.0 else None      # :519
```

The numerator is the Phase 1 **prior transient** raw curve, interpolated at the observed
2016 peak: shape-conditional by section 1. The denominator is the Phase 2 rejection
fraction: shape-invariant by C3. The observed peak `peak` itself comes from the Phase 2
event chain, also invariant. So the factor is exposed **one-sidedly, through the
numerator alone** - confirmed exactly as stated.

### Expected sign under `HPB_m067_1978`

`scripts/generate_configs.py:257-265` records the two members:

- `HPB_m064_1987` (production, first entry, the one `run.py:318` uses): compound;
  3rd-largest HPB peak 7,214 m3/s at t = 37 h; secondary peak **64 % of max** at
  t = 75 h; inter-peak trough **30 %**. Independently measured shape statistics:
  rising limb 23 h, 10-90 % rise 18 h, plateau (>=90 %) 10 h, FWHM (>=50 %) 55 h
  (`docs/decisions/adr0032-aquifer-response-diagnostic.md:66`), stage-domain
  inter-peak trough 0.498 and t50 = 55 h against an HPB ensemble median t50 of
  40 h [32-54] (ADR-0023 lines 31-45).
- `HPB_m067_1978` (approved alternate, second entry): isolated single peak, **largest
  HPB peak 7,581 m3/s**, **32 h rise**. Nothing else is recorded anywhere in the repo -
  no t50, no FWHM, no plateau, and the definition behind "32 h rise" is not stated.

**A reconciliation, so the two trough figures are not mistaken for a contradiction.**
The 30 % (generate_configs, discharge domain) and the 0.498 (ADR-0023, stage domain) are
the same quantity under the Eq. 4.19 rating. Because `h + b = sqrt(Q/a)`, the
stage-domain shape fraction depends only on discharge ratios:
`s(Q) = (sqrt(Q) - sqrt(Q_base)) / (sqrt(Q_peak) - sqrt(Q_base))` with
`Q_base = 75.44 m3/s` (ADR-0020 Decision 1) and `Q_peak = 7,214`. At `Q = 0.30 Q_peak`
this gives **0.4962** against ADR-0023's independently measured **0.498**. The same
arithmetic puts the secondary peak (`0.64 Q_peak`) at **s2 = 0.777** in the stage
domain. (Arithmetic on recorded numbers, cross-checked against an independent
measurement; not a model evaluation.)

**Where the anchors sit on that shape.** From `docs/decisions/phase2-peak-shortcut.json`
and the persisted run sidecars (`metadata['hydrograph']['h_base_m_msl']`, gitignored):

| Stratum | Anchor peak | `z_toe` | `h_base` | Toe as a shape fraction | Secondary peak, scaled |
|---|---|---|---|---|---|
| KP 58.8 matrix | 40.750 | 38.50 | 36.517 | 0.468 | 39.81 m, i.e. **1.31 m above the toe** (58 % of the primary excess) |
| KP 60.0 matrix | 42.296 | 40.00 | 38.293 | 0.426 | 41.40 m, i.e. **1.40 m above the toe** (61 % of the primary excess) |

The inter-peak **trough** (shape 0.4962) lands at 38.62 m at KP 58.8 and 40.28 m at
KP 60.0, i.e. **above the landside toe at both anchors**. So at the two levels that
produce the published 2.75 and 3.90, the canonical member does not present "two
episodes with a gap"; it presents one continuous above-toe window spanning both peaks,
roughly 55 h wide at half amplitude. That is the mechanism the committed slice's own
note asserts (`thesis_figure_gaps.py:545-549`), now quantified.

**Sign: likely negative (the factor moves toward one), but NOT determined.** Two
channels act in opposite directions.

1. *Compound structure* (Chapter 6's channel). Because `l_current` is monotonically
   non-decreasing, the second episode's contribution to `l_final` is non-negative:
   deleting it can only lower the transient `P_f`, hence lower the numerator, hence move
   the factor toward one. This channel is live at both anchors - the secondary peak sits
   1.3 to 1.4 m above the toe, not below it.
2. *Crest and limb breadth.* The comparison is not "m064 with its second peak deleted".
   m067 is a different primary peak. Its recorded **32 h rise is longer than m064's
   23 h rising limb** (and than its 18 h 10-90 % rise). Near the shoulder - and the
   anchors are the shoulder, `P_f` 0.13 to 0.16 - failure is decided by time spent above
   a barrier that is only exceeded close to the crest, so a broader single crest can
   deliver more erosion than a narrower double one. The rate law's 0.81 exponent does
   not saturate this away.

Channel 2 is not a rounding correction, and nothing recorded in the repo decides which
channel wins. The honest statement is: **the direction is likely toward one, on the
strength of channel 1 plus the fact that m064 sits in the ensemble's upper duration
quartile (t50 = 55 h against a median 40 h), but it is not determined, and the one
directly comparable number that exists points the other way.**

### Does the source support Chapter 6's assertion?

Chapter 6 (`...Analysis.tex:1136-1139`) says:

> a canonical event of shorter duration above the toe would move it toward one. The
> direction therefore follows from the mechanism

**The conditional is sound; its antecedent is not established for the pinned
alternate.** As a mechanism statement - *if* the alternate holds the stage above the
toe for less time, *then* the factor falls - the sentence is correct and follows from
the monotone-`l` construction. But the thesis is read as saying the pinned alternate
*is* such an event, and the repo does not record that. What it records is a **longer**
rise (32 h against 23 h) and no duration-above-toe figure at all. The 32 h number is
also of unstated definition, so it may not even be commensurable with the 23 h rising
limb measured by `flood_timescales`.

Two safe repairs, neither needing a run: state the mechanism as a conditional and say
the antecedent is unverified for the pinned alternate; or drop the appeal to the
alternate and instead state the *structural* result of section 2 - that the exposure is
one-sided, numerator-only, and that the entire denominator (the Phase 2 evidence) is
invariant. The second is stronger, because it converts an unquantified worry into a
bounded one.

---

## 4. What remains genuinely unmeasured, and what it would cost

Unmeasured, and only measurable by running something:

1. **The magnitude** of the transient response to the shape swap: `P_f_trans_raw` at
   every level and section, and hence the peak-shortcut numerator, the Stage 6.6
   `temporal_net` step and both ladder totals, the `heq_conservatism` and
   `dimensional_at_transient` auxiliaries, the design-HWL bias denominator, and the
   Phase 3 BEP curves.
2. **The sign**, per section 3.
3. Whether m067's above-toe duration at the anchors is in fact shorter than m064's -
   which is a property of the workbook, not of the engine, and is the cheapest thing on
   this list.

### Phase 1: about 40 minutes, on an existing pattern, with nothing new to build

`scripts/foreshore_width_study.py:80-89` is the pattern:

```python
data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
data["geometry"]["foreshore_width"] = float(foreshore_width_m)   # -> canonical_event_ids
config = Config.model_validate(data)
return run_fragility_analysis(config, n_jobs=n_jobs, progress=False, persist=False)
```

The committed YAML is never written; `persist=False` writes no `results/` artifact; and
`:92-105` asserts the baseline arm bit-identical to the persisted production sweep
before any sensitivity is reported. For a shape study the edited key is
`data["hydrograph_source"]["canonical_event_ids"] = ["HPB_m067_1978", "HPB_m064_1987"]`.

Cost: the eight persisted sweeps record `runtime_seconds` summing to **1,156 s
(19.3 min)**, so a baseline-plus-swap pair of arms across all eight strata is about
**39 min**; the four matrix strata alone are about 20 min. Nothing else is needed - no
new module, no config field, no ADR.

### Why "reorder the config list" does not work

`generate_configs.py:263-264` proposes it ("a sensitivity config reorders the list;
selection stays config-side"). Three things block it:

1. **`run.py:318`** hard-codes the first entry:
   `event_id=source.canonical_event_ids[0]`. Reordering is the only way to select
   through the config, so the list *is* the selector.
2. **`canonical_event_ids` is inside the config hash.** `config.py:753` declares it on
   `HydrographSource`; `config.py:1090-1097` builds the snapshot with
   `model_dump(mode="json")` and drops only the three `None`-valued optional blocks
   (`length_effect`, `sellmeijer_model_factor`, `prior_mean_scenario`) - the
   hydrograph block is never dropped; `config.py:1110-1111` hashes that snapshot. So
   reordering a committed YAML changes `config_hash()`, and `replay.py:222-228`
   **refuses to replay** a Phase 1 file whose reconstructed hash does not match. That
   invalidates the Phase 2 posterior for that stratum.
3. **`tests/test_configs.py:257`** pins the exact ordered list:
   `assert list(src.canonical_event_ids) == ["HPB_m064_1987", "HPB_m067_1978"]`
   (with the same assertion at `tests/test_config.py:447` and `tests/test_run.py:971`).
   A reordered committed config fails the drift guard.

The in-memory route defeats all three: the selector is still `[0]`, but of an in-memory
list; the hash changes only for an object that is never persisted; and the committed
YAML the test reads is untouched.

### Stage 6.6 and Phase 3: both need work before they can be swapped

Neither driver has a variant axis or an output directory, so neither can produce a
shape arm without overwriting the production record.

- `scripts/stage6_6_gap_decomposition.py:57-58` fixes `OUT_DIR = results/stage6_6` and
  `FIG_DIR = OUT_DIR/figures` as module constants; the CLI (`:647-665`) offers
  `--sections`, `--n`, `--n-jobs`, `--bootstrap`, `--n-pilot`, four `--skip-*` flags and
  `--figures-only`, and **no `--out-dir` and no shape axis**. A shape run would
  overwrite `stage6_6_kp62_0.h5` / `_analysis.json` **and** dual-write over the tracked
  `docs/figures/stage6_6_*.png` (`:8-10`).
  There is a second, sharper hazard: `verify_against_production` (`:162-217`) **skips
  rather than fails** when the config differs by more than the `length_effect` block
  (`:187-190`, `status = "skipped_config_mismatch_beyond_length_effect"`). A
  shape-variant config differs exactly that way, so the ADR-0040 gate (i) would go
  quiet, not red, and the run would persist unguarded evidence over the guarded record.
  Minimum work: an `--out-dir` and a variant suffix, plus making the drift guard's skip
  path explicit in the summary.
- `scripts/phase3_campaign.py:152` calls `ArgumentParser(...).parse_args()` with **no
  arguments defined at all**. Same requirement.

### The Phase 3 confound, which is the real reason a BEP-only swap is not enough

`scripts/generate_uemura_surface_curves.py:69` sets
`CANONICAL_EVENT = "HPB_m064_1987"` as a hard-coded module constant, and the committed
contract CSVs record it (`data/processed/uemura_surface_curves/provenance.md:12`). The
overflow and scour curves therefore condition on the **same** member as the BEP curves.
Swapping only the BEP side would change the numerator of the RQ3 dominance share while
leaving the denominator's other terms on the old shape - confounding shape with
mechanism in exactly the quantity RQ3 reports. A defensible Phase 3 shape arm must swap
both sides, which means re-running `generate_uemura_surface_curves.py` under the
alternate member as well.

The Phase 3 **hazard** side is not affected: `system_integration/hazard.py:311-322`
streams every member of each workbook, so the annual-max stage distribution and the
climate signal do not know which member is canonical.

### Recommendation

The Phase 1 arm is cheap, uses an existing pattern, and settles the sign of the two
headline factors. **It is the one thing here worth measuring.** Stage 6.6 and Phase 3
should not be attempted until their drivers grow an out-dir and a variant axis; and the
Phase 3 arm should not be attempted at all until the Uemura curves can be regenerated
on the same alternate member. Per the terms of this task, nothing was run.

---

## 5. What the thesis can be strengthened to say, with no new run

**This repository holds no thesis prose (`docs/conventions.md` section 8). Nothing below
was edited.** Targets are named by file, line and label in `d:\repositories\msc-thesis`.

The three the brief names (the first two are the same paragraph, reached two ways):

1. **Ch 6 section 5.1, "What the Time-Resolved Replay Adds"** -
   `mainmatter/5. Results of the System Integration and Climate Sensitivity Analysis.tex:1130-1142`
   (`\label{subsec: What the Replay Adds}`). Currently: "the quantity in this thesis
   most exposed to the choice of canonical event ... the direction therefore follows
   from the mechanism; the magnitude does not". Can become: the exposure is
   **one-sided, through the numerator only** - the denominator, the Phase 2 rejection
   fraction, is exactly invariant because the replay drives the observed 2016 record
   (section 1, C3). And the mechanism sentence should be repaired per section 3: the
   conditional is sound, but the pinned alternate is not shown to satisfy its
   antecedent, and its one recorded comparable number (32 h rise against 23 h) points
   the other way.
2. **Ch 7 limitations register, the canonical-event row** -
   `mainmatter/7. Discussion.tex:709-714`. Currently the Affected column reads "Every
   conditional and annual probability; the peak-only factor most directly". That is
   too broad and gives away results the code protects. It can be narrowed to: every
   **transient** conditional probability and everything downstream of one; the static
   branch, the Stage 6.6 head-convention and initiation-gate components in probability
   units, the whole static Shapley lattice, and the Phase 2 rejection result are
   **exactly invariant by construction**. The Resolution column should carry the
   corrected direction statement, and should note that the peak-shortcut factor and the
   design-level bias move in **opposite** directions under one swap (section 2).
3. **Ch 6 section 3.1 and `tab: gap components`** -
   `...Analysis.tex:530-575`. The `C0` column and the head-convention and gate
   components in probability units are exactly invariant; the **shares** and the
   `Pure duration` column are not, because their denominators end at `C4`. The caption
   already carries "order-conditional"; it needs "and the shares, unlike the components
   themselves, are conditional on the canonical event".

Three more that the same argument reaches:

4. **Ch 6 section 2, "The Magnitude of the Bias at the Design Water Level"** -
   `...Analysis.tex:284-509`. The bias is an invariant numerator over a conditional
   denominator; state that, and state that this is the opposite one-sidedness from the
   peak-shortcut factor.
5. **Ch 5 section on GSA, the scenario-invariance paragraph** -
   `mainmatter/5. Verification, Validation, and Sensitivity.tex:487-492`. "would
   evaluate an identical loading record" is weaker than the truth: it **is** the same
   record by construction (`hydrographs.py:669-737`, the two calls differ only in the
   `scenario` string), and `scripts/gsa_study.py:343-360` checks it. Also: the static
   GSA QoIs (`Z_static`, static failure indicator) are shape-invariant, so half the
   "L is the top total-effect input everywhere" headline is unconditional.
6. **Ch 4, the canonical-shape subsection** -
   `mainmatter/4. Methodology.tex:1031-1054`
   (`\label{subsec: Conditioning Sweep and the Canonical Hydrograph Shape}`). This is
   where the invariance property belongs as a positive statement, so the later chapters
   can cite it instead of re-arguing it: `peak = h_i` verbatim, the static comparator
   reads only `peak`, therefore the shape reaches the results through the timestepper
   and nowhere else.

The register row should keep saying the magnitude is unquantified. What changes is the
**scope**: from "every conditional curve" to "every transient conditional curve", with
the invariant set enumerated and traceable to source.
