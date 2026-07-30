# Production Campaign — 2026-07-29

**The definitive Phase 1 + Phase 2 + Phase 3 execution. Every number in the
thesis report traces to this one run.**

Driver: `scripts/production_campaign.py`. Manifest:
`results/production_campaign_manifest.json` (per stage: command, start/end,
runtime, output paths with SHA-256, and the pass/fail of every gate).

This document is the manifest in prose. Where it differs from an earlier
report of record, this document is authoritative for the artifacts as they
now stand on disk; §11 lists exactly which earlier numbers it changes.

---

## 1. Why the campaign was re-run

Six of the eight persisted Phase 1 sweeps carried config hashes that no longer
matched `configs/*.yaml`. Before running anything, the campaign re-proved that
the difference is *exactly* the three physics-inert ADR-0037 `length_effect`
keys, by loading each persisted sidecar, rebuilding the `Config` from
`configs/`, and diffing `to_metadata()` key by key:

| Stratum | persisted hash | current hash | differing keys |
|---|---|---|---|
| KP 57.4 matrix | `57a8c1fc` | `ad5ace0a` | `length_effect.{enabled,lambda_ac_m,segment_length_m}` |
| KP 57.4 bulk | `47816ba5` | `a06bf4aa` | same three |
| KP 58.8 matrix | `7f2a5710` | `02870c4b` | same three |
| KP 58.8 bulk | `da9ea36b` | `e6460d56` | same three |
| KP 60.0 matrix | `184069b2` | `6e964397` | same three |
| KP 60.0 bulk | `daf0b575` | `6f7bd978` | same three |
| KP 62.0 matrix | `613add6c` | `613add6c` | **none** |
| KP 62.0 bulk | `7d8661b3` | `7d8661b3` | **none** |

The mechanism: `Config.to_metadata()` drops `length_effect` when it is `None`
(`config.py`, the ADR-0037/0045/0048 hash-preservation rule), so the
pre-ADR-0037 sidecars hash without the block and the current generated configs
hash with it. `run.py` consumes the block only when `enabled` is true, and it
lands in metadata only. KP 62.0 already matched because both its strata were
re-run at the ADR-0047 adoption on 2026-07-29.

Consequently the re-run had to reproduce the failure matrices **bit-identically**
— that is gate G1 below, and it is a requirement, not an expectation. It also
independently re-tests ADR-0048's baseline-neutrality claim, because the
ADR-0048 `config.py`/`run.py`/`replay.py` changes are in the tree.

## 2. The driver

`scripts/production_campaign.py` contains **no physics**. Like
`scripts/phase3_campaign.py` it only sequences existing entry points, preserves
what it is about to supersede, checks the gates, and writes the manifest. It is
idempotent and resumable: the manifest records a status per stage, a stage
already recorded `passed` is skipped unless `--force` is given, and a gate
failure is terminal (the manifest is flushed and the process exits non-zero
rather than continuing into a stage that would consume a suspect artifact).

Phase 1 is additionally resumable *within* the stage: it detects that
`results/` already carries sweeps stamped with the current config hashes and
re-gates them against the preserved baseline instead of reproducing identical
files. That is an exact test ("were these produced under the current
configs?"), not a heuristic.

Superseded artifacts are moved to `results/superseded_<timestamp>/`, never
overwritten blind. Because each invocation stamps its own root, the campaign
produced several; each stage's manifest entry names the root it used.

**Figures were deliberately not regenerated** (`--no-figures` /
`--skip-figures` / `--no-figure` passed through; two companions that render
figures with no skip flag have their tracked outputs restored from git and the
fact recorded). The figure pass is a separate step after the sensitivity work
lands.

```powershell
python scripts/production_campaign.py                 # resume/run everything
python scripts/production_campaign.py --stage phase1  # one stage
python scripts/production_campaign.py --dry-run       # print the plan
```

### 2.1 Stage runtimes

| Stage | Runtime | Note |
|---|---|---|
| `configs` | 2.4 s | |
| `phase1` | **1425 s** | the sweep itself; the manifest records 0.5 s for the final re-gate after the resume (§3.1) |
| `phase2_baseline` | 1218 s | |
| `phase2_anchor_rating` | 980 s | |
| `phase2_no_initiation` | 789 s | |
| `stage6_6` | 1171 s | |
| `phase3` | 24.6 s | hazard cache reused |
| `phase3_validation` | 36.8 s | |
| `companions` | 4635 s | nine studies |
| `diagnostics` | 2.2 s | plus a 57 s coverage composition on first run |
| **total** | **≈ 2.9 h** | |

## 3. Gate results

Every gate below is recorded in the manifest with its full evidence payload.

| Gate | Check | Result |
|---|---|---|
| **G0** | persisted-vs-current config diff is only the three ADR-0037 keys | **pass** (see §1) |
| **G0** | regenerated `configs/` is byte-identical | **pass** (8 files, 0 changed) |
| **G1** | re-run failure matrices element-wise identical to the superseded files | **pass** (all 8 strata) |
| **G2** | `--verify` exact, zero flag mismatches, every stratum | **pass** (baseline + both variants) |
| **G2** | every posterior replays the freshly re-run Phase 1 hash | **pass** |
| **G2** | marginal transient rejection exactly 0 in all eight strata | **pass** |
| **G3** | both sections present in the Stage 6.6 summary | **pass** |
| **G3** | production drift guard bit-identical at all common levels | **pass** (38 + 23 levels) |
| **G3** | every Euler-flip count exactly 0 | **pass** (5 diagnostics × 2 sections) |
| **G4** | `rq4_annual.csv` changed-row count vs the superseded campaign | **0 rows changed** |
| **G5** | ADR-0032 verdict `instantaneous` wherever present | **pass** (8/8) |
| **G5** | every re-run sweep carries the `aquifer_response` block | **pass** (8/8) |
| **G6** | every bit-identity companion runs to completion | see §10 |

### 3.1 G1 in detail, and one deviation from the stated allowlist

All eight strata reproduce the superseded artifacts exactly — both failure
matrices, `theta_matrix`, the conditioning grid, and both raw `P_f` vectors:

| Stratum | `failure_matrix_trans` | `failure_matrix_static` | `theta_matrix` | raw `P_f` (both) |
|---|---|---|---|---|
| all 8 | identical | identical | identical | identical |

`metadata_value_changes` and `metadata_regressions` are **empty at all eight
strata**.

The campaign's stated allowlist permitted only `config_hash`, the
`length_effect` block and timestamps to differ. The first execution tripped on
a fourth key: **`aquifer_response` was absent from the KP 57.4 / 58.8 / 60.0
*matrix* sidecars and is present on the re-run.** Cause: those three were
generated 2026-07-10, one day before ADR-0032 wired
`hydraulics.aquifer_response_diagnostic` into `run.py`; KP 62.0 matrix (re-run
at the ADR-0047 adoption) and all four bulk strata (generated 2026-07-12)
already carried it.

The gate was therefore made **asymmetric**, which is the correct rule and not a
weakening:

* a key **absent → present** is a diagnostic wired after that sweep was
  persisted — purely additive, metadata-only, no physics. It is recorded in the
  manifest (`metadata_additive_keys`) and passes.
* a key whose **value changed**, or that **regressed** present → absent, still
  fails.
* any difference in a failure matrix, `theta`, the grid or the raw `P_f`
  vectors still fails. That is what G1 is actually about, and it passed
  everywhere.

The alternative — a gate that fires every time the engine gains a diagnostic
block — would have to be silenced by hand on every future campaign, which is
worse than encoding the asymmetry once.

**Consequence for ADR-0048.** Its baseline-neutrality claim is re-confirmed
under a fresh, full re-execution: with the ADR-0048 code in the tree, every
stratum reproduced its pre-ADR-0048 failure matrices bit-for-bit.

**Side effect worth recording.** With the sweeps re-run, Stage 6.6's config
hashes now match the production sweeps *directly*. The ADR-0040 relaxation that
had to strip the `length_effect` block before comparing is no longer exercised
on the production path.

## 4. Phase 1 — the eight production sweeps

N = 100 000, Δt = 225 s (ADR-0030), forward Euler, `numpy` backend,
`length_effect.enabled: false` with λ_ac = 250 m and a 200 m segment
(decision 2), `hydrograph_source: d4pdf_scaled_canonical`. Runtime 1425 s for
all eight at `--n-jobs 8` (`n_jobs` is proven result-invariant).

### 4.1 ADR-0024 deliverable form and raw maxima

| Stratum | static form / role | max `P_f` raw | transient form / role | max `P_f` raw |
|---|---|---|---|---|
| KP 57.4 matrix | fitted_lognormal / deliverable | 0.9997 | fitted_lognormal / deliverable | 0.9644 |
| KP 58.8 matrix | fitted_lognormal / deliverable | 1.0000 | fitted_lognormal / deliverable | 0.9878 |
| KP 60.0 matrix | fitted_lognormal / deliverable | 1.0000 | fitted_lognormal / deliverable | 0.9843 |
| KP 62.0 matrix | fitted_lognormal / deliverable | 1.0000 | fitted_lognormal / deliverable | 0.9901 |
| KP 57.4 bulk | fitted_lognormal / deliverable | 0.5898 | raw_tail_binomial / extrapolative_only | 0.3775 |
| KP 58.8 bulk | raw_tail_binomial / extrapolative_only | 0.2618 | raw_tail_binomial / extrapolative_only | 0.1522 |
| KP 60.0 bulk | fitted_lognormal / deliverable | 0.9933 | fitted_lognormal / deliverable | 0.8393 |
| KP 62.0 bulk | fitted_lognormal / deliverable | 0.6393 | raw_tail_binomial / extrapolative_only | 0.4265 |

**All four matrix strata are `fitted_lognormal` on both branches**, KP 62.0
included (its transient max raw `P_f` is 0.9901 under the ADR-0047 adopted
geometry). Where the form is `raw_tail_binomial`, the raw points with their
Clopper-Pearson intervals are the intended primary presentation, quoted as
per-level ratios against the static curve — not a degraded substitute for a
fit. `extrapolative_only` means a fit exists but describes the curve beyond the
data; its median must never be quoted as an observed site number.

`bootstrap_degenerate_replicates` is **0 / 0 at every stratum** (1000
replicates each).

## 5. Phase 2 — posteriors and both documented sensitivity variants

All eight baseline posteriors with `--verify`, plus both documented variants
across all four matrix strata. Every masked-vs-re-evaluation verification was
**exact** (zero flag mismatches).

### 5.1 Baseline (trace-anchored, `no_breach`)

| Stratum | transient rej. | static rej. | marginal transient | n accepted | verified |
|---|---|---|---|---|---|
| KP 57.4 matrix | 0.07 % | 6.26 % | **0.0000** | 99 935 | exact |
| KP 58.8 matrix | 5.67 % | 57.63 % | **0.0000** | 94 327 | exact |
| KP 60.0 matrix | 3.36 % | 73.31 % | **0.0000** | 96 637 | exact |
| KP 62.0 matrix | 0.00 % | 0.00 % | **0.0000** | 100 000 | exact |
| KP 57.4 bulk | 0.00 % | 0.00 % | **0.0000** | 100 000 | exact |
| KP 58.8 bulk | 0.00 % | 0.00 % | **0.0000** | 100 000 | exact |
| KP 60.0 bulk | 0.02 % | 1.84 % | **0.0000** | 99 977 | exact |
| KP 62.0 bulk | 0.00 % | 0.00 % | **0.0000** | 100 000 | exact |

**The marginal transient rejection is exactly 0 in all eight strata**, at
production N, under the adopted KP 62.0 geometry. Every baseline number
reproduces the superseded posterior to the digit.

**Tiering caveat, carried per decision 4.** The engine evaluates the
**unremediated foundation** at KP 58.8 and KP 60.0; `remediation_state` is a
provenance label and drains are not modelled. The informative updates therefore
land at the two drained sections, while KP 62.0 (unreinforced, the governing
live-BEP section) and KP 57.4 receive near-vacuous updates. That is the inverse
of the thesis's tiering narrative and must be presented as a limitation: these
posteriors are the as-if-undrained constraint, and the drain credit is a
separate argument.

### 5.2 Sensitivity variants

| Stratum | baseline | `--anchor rating` | `--criterion no_breach_no_initiation` |
|---|---|---|---|
| KP 57.4 matrix | 0.07 % | 0.00 % | 66.39 % |
| KP 58.8 matrix | 5.67 % | 10.81 % | 99.57 % |
| KP 60.0 matrix | 3.36 % | 0.34 % | 99.30 % |
| KP 62.0 matrix | 0.00 % | **0.05 %** | **39.55 %** |

The two KP 62.0 members are the ones that were stale: both variant runs had
been left on the withdrawn L = 47 m Phase 1 (hash `e9b8760b`) and now consume
the adopted L = 40 m (`613add6c`). Every other variant member reproduces
exactly. The `no_breach_no_initiation` posteriors at KP 58.8 and KP 60.0 remain
statistically meaningless by size (432 and 696 rows) and stay a qualitative
sensitivity, not a deliverable posterior.

## 6. Stage 6.6 — the static-transient gap

Ten-comparator ladder on one shared sample at KP 62.0 and KP 57.4, matrix and
bulk, N = 100 000. Drift guard **bit-identical at all 38 (KP 62.0) and 23
(KP 57.4) common levels**; `theta_matrix` identical; **every Euler-flip count
exactly 0** across all five diagnostics at both sections.

### 6.1 Bias factor per level, with the row count that carries it

> **Superseded at the design-HWL rows (2026-07-30, see §12 and
> `docs/stage6_6_report.md` §9).** The tables below are the N = 1e5 record and are
> left unchanged as such. At N = 1e6 the KP 62.0 design-HWL bias is **26.9
> [21.6, 35.3] on 63 rows, resolved** (the 44.7 below rests on 4 rows and
> overstates it 1.66×), and KP 57.4's is bounded at **B ≥ 148**.

KP 62.0 (HWL 46.39 m MSL, attainable max 50.5 m):

| level [m MSL] | C0 static | C4b transient | C4b rows | bias | resolved |
|---|---|---|---|---|---|
| 46.25 | 4.20e-4 | 1.0e-5 | 1 | 42.0 | **no** |
| 46.39 (HWL) | 1.79e-3 | 4.0e-5 | 4 | 44.7 | **no** |
| 46.50 | 3.93e-3 | 1.50e-4 | 15 | 26.2 | marginal |
| 46.75 | 1.72e-2 | 1.30e-3 | 130 | 13.2 | yes |
| 47.00 | 5.22e-2 | 4.99e-3 | 499 | **10.5** | yes |
| 47.50 | 2.07e-1 | 3.29e-2 | 3 286 | 6.3 | yes |
| 48.00 | 4.43e-1 | 1.01e-1 | 10 127 | 4.4 | yes |
| 48.50 | 6.66e-1 | 2.11e-1 | 21 141 | 3.1 | yes |
| 49.00 | 8.24e-1 | 3.42e-1 | 34 172 | 2.4 | yes |
| 49.50 | 9.16e-1 | 4.73e-1 | 47 270 | 1.9 | yes |
| 50.50 | 9.84e-1 | 6.90e-1 | 68 962 | 1.4 | yes |

KP 57.4 (HWL 39.21 m MSL, attainable max 43.25 m):

| level [m MSL] | C0 static | C4b transient | C4b rows | bias | resolved |
|---|---|---|---|---|---|
| 39.21 (HWL) | 1.18e-3 | 0 | **0** | lower bound only | **no** |
| 39.50 | 2.23e-2 | 6.20e-4 | 62 | 36.0 | marginal |
| 39.75 | 9.89e-2 | 7.31e-3 | 731 | 13.5 | yes |
| 40.00 | 2.45e-1 | 3.62e-2 | 3 616 | 6.8 | yes |
| 40.50 | 6.16e-1 | 2.06e-1 | 20 568 | 3.0 | yes |
| 41.00 | 8.61e-1 | 4.63e-1 | 46 306 | 1.9 | yes |
| 42.00 | 9.90e-1 | 8.26e-1 | 82 614 | 1.2 | yes |
| 43.25 | 9.997e-1 | 9.64e-1 | 96 437 | 1.0 | yes |

**How to quote this.** At design HWL the bias is *not statistically resolved*
at either section: KP 62.0 rests on 4 failing transient rows out of 100 000 and
KP 57.4 on **zero**. Quote a level where it is resolved, with the level named —
"a factor of 10.5 at 47.0 m MSL" at KP 62.0, "13.5 at 39.75 m MSL" at
KP 57.4 — or quote the HWL figure explicitly as unresolved with its row count.
The values reproduce the ADR-0047 §8 addendum exactly.

**This is the open item decision 6 addresses** (see §12).

## 7. RQ3 — mechanism dominance

Per decision 5, the mechanism-dominance **answer** is the four
geotechnically characterised sections; the reach-wide comparison is supporting
context. Matrix d70, posterior BEP, λ_ac = 250 m, primary surface variant.

### 7.1 The answer: the four characterised sections

| Section | Scenario | P_sys [1/yr] | BEP | share | Overflow | share | Scour |
|---|---|---|---|---|---|---|---|
| KP 57.4 | historical | 7.530e-4 | 7.530e-4 | **1.000** | 0 | 0.000 | 0 |
| KP 57.4 | +4K | 9.531e-3 | 9.484e-3 | **0.912** | 9.114e-4 | 0.088 | 0 |
| KP 58.8 | historical | 7.420e-3 | 7.337e-3 | **0.974** | 1.951e-4 | 0.026 | 0 |
| KP 58.8 | +4K | 4.091e-2 | 4.045e-2 | **0.941** | 2.529e-3 | 0.059 | 0 |
| KP 60.0 | historical | 1.802e-3 | 1.802e-3 | **1.000** | 0 | 0.000 | 0 |
| KP 60.0 | +4K | 1.418e-2 | 1.417e-2 | **0.998** | 2.304e-5 | 0.002 | 0 |
| KP 62.0 | historical | 1.006e-3 | 8.580e-4 | **0.812** | 1.993e-4 | 0.188 | 0 |
| KP 62.0 | +4K | 1.278e-2 | 8.403e-3 | **0.500** | 8.392e-3 | 0.500 | 0 |

**BEP dominates all four characterised sections historically (81 to 100 % of
the summed annual contributions) and leads at three of four under +4K, with
KP 62.0 exactly level at 0.500 / 0.500. Overflow leads nowhere.** Fluvial
scour is exactly zero at every section under the dimensionally-correct USACE
conversion (ADR-0042 decision 9).

Neither clamp flag is set at any of the 20 KP 62.0 rows
(`bep_clamped_above_grid` and `system_lower_bound_clamp` both False,
`system_frac_peaks_above_grid` 0.0), so no KP 62.0 number here is a
grid-clamped lower bound.

### 7.2 Reach context: the full 114 segments

Supporting context, not the RQ3 answer. Per-segment dominant-mechanism counts
across the reach are unchanged from the previous campaign (G4: zero rows
changed), so `phase3_report.md` §5.2 stands as written: historically overflow
dominates 31 of 114 with 79 "none loaded"; under +4K overflow is near-universal
at 110 of 114. Under the corrected conversion overflow is the only surface
mechanism that produces failures; the as-received `scour_script_k` companion
would instead make scour the historical dominant at roughly 70 of the
surface-only segments, so the reach-wide **surface** dominance is conditional
on the k-conversion. The overflow-versus-BEP comparison at the four
characterised sections is not.

## 8. RQ4 — climate sensitivity

**Scope, per decision 5.** The RQ4 answer is the four geotechnically
characterised sections. All 114 segments are computed (RQ3 needs the reach
context and it is nearly free), and the 114-segment distribution is reported
below as clearly-labelled reach context.

### 8.1 The answer: the four characterised sections

Matrix d70, posterior BEP, λ_ac = 250 m, primary surface variant.

| Section | P_sys historical [1/yr] | P_sys +4K [1/yr] | climate ratio |
|---|---|---|---|
| KP 57.4 | 7.530e-4 | 9.531e-3 | **12.7 ×** |
| KP 58.8 | 7.420e-3 | 4.091e-2 | **5.5 ×** |
| KP 60.0 | 1.802e-3 | 1.418e-2 | **7.9 ×** |
| KP 62.0 | 1.006e-3 | 1.278e-2 | **12.7 ×** |

The system probability rises by a factor of **5.5 to 12.7** across the four
characterised sections. KP 58.8 is the worst segment in the basin in both
climates (7.4e-3 historical, 4.1e-2 under +4K), and its section (Tokachi 4 =
KP 58.0) governs the basin.

Sensitivity brackets on these four numbers: the λ_ac = 40 m bracket multiplies
them by 1.6 to 3.4; the bulk d70 co-primary cuts the BEP-driven numbers by
roughly 5 to 15 ×; the 2016 posterior lowers the KP 58.8 historical number
about 12 % against the prior. Risk concentrates roughly 100 to 400 × in years
loading the toe for more than 24 h, and +4K roughly triples the frequency of
exactly those years — the duration channel, not the peak channel alone, carries
the climate signal.

### 8.2 Reach context: the distribution over all 114 segments

**This is reach context, not the RQ4 answer.** The reason is structural:
**110 of the 114 segments carry no BEP branch at all** (`bep_source=None`
under the production `exact` policy — only the four OYO sections have the
borehole data a BEP curve requires). Their annual numbers are therefore
**surface-mechanism-only lower bounds**, and the median over the 114 is
dominated by segments switching from exactly zero to loaded once +4K lifts
their peaks over the crest.

| statistic over 114 segments | historical | +4K |
|---|---|---|
| median P_sys [1/yr] | 0 | 3.672e-4 |
| mean P_sys [1/yr] | 1.082e-4 | 1.917e-3 |
| segments > 1e-3/yr | **3** | 45 |
| segments > 1e-2/yr | 0 | 4 |
| segments at exactly 0 | 79 | 1 |
| segments with no BEP branch | 110 of 114 | 110 of 114 |

The median moving 0 → 3.7e-4 and the mean 1.0e-4 → 1.9e-3 (about 18 ×) are
statements about a population three-quarters of which is a lower bound. They
belong in the reach-context discussion, not in the RQ4 answer. The three
segments above 1e-3/yr historically are all BEP-branch segments (KP 58.8,
KP 60.0, KP 62.0), and the four highest-risk segments in the basin are exactly
the four characterised sections — which is itself the argument for scoping the
RQ4 answer as decision 5 does.

## 9. Diagnostics (G5)

### 9.1 Monte Carlo convergence (spec §11, target CoV ≤ 5 %)

| Stratum | interior levels (static) | over 5 % | interior levels (transient) | over 5 % |
|---|---|---|---|---|
| KP 57.4 matrix | 18 | 2 | 16 | 1 |
| KP 58.8 matrix | 23 | 2 | 22 | 1 |
| KP 60.0 matrix | 20 | 2 | 23 | 2 |
| KP 62.0 matrix | 26 | 3 | 30 | 3 |
| KP 57.4 bulk | 14 | 3 | 13 | 3 |
| KP 58.8 bulk | 17 | 6 | 16 | 6 |
| KP 60.0 bulk | 22 | 2 | 21 | 4 |
| KP 62.0 bulk | 22 | 8 | 21 | 9 |

`meets_cov_target_*` is False at every stratum, and this is the **expected**
ADR-0024 regime, not a defect: the exceedances are the deep-tail levels where a
handful of failing realizations out of 100 000 mechanically cannot reach 5 %
CoV. On the matrix strata only 1 to 3 interior levels per branch exceed the
target; the bulk strata (the resistant d70 reading, tiny `P_f` throughout)
exceed it more often, consistent with their `raw_tail_binomial` deliverable
form. ADR-0031 established N = 1e5 sufficiency down to per-level transient
`P_f` ≈ 5e-3, and the exceedances here sit below that. The honest uncertainty
statement at those levels is the Clopper-Pearson interval, which is persisted
for every level of every branch.

### 9.2 ADR-0032 aquifer response (Π against the pre-registered Π\* = 0.10)

| Stratum | verdict | Π central | Π corner90 | margin | check A | check B |
|---|---|---|---|---|---|---|
| KP 57.4 (both) | instantaneous | 0.0042 | 0.0119 | 8.4 × | true | true |
| KP 58.8 (both) | instantaneous | 0.0082 | 0.0232 | 4.3 × | true | true |
| KP 60.0 (both) | instantaneous | 0.0092 | 0.0261 | 3.8 × | true | true |
| KP 62.0 (both) | instantaneous | 0.0018 | 0.0051 | 19.5 × | true | true |

**All eight strata now carry the block** — the three matrix sidecars that
predated ADR-0032 gained it in this re-run (§3.1), closing a documented
local-artifact staleness gap. Every section clears the threshold with 3.8 to
19.5 × margin at the conservative `S_s` corner.

### 9.3 Bootstrap and deliverable

`bootstrap_degenerate_replicates` is 0 / 0 at all eight strata. Deliverable
forms and `fit_role` per branch are in §4.1.

### 9.4 Phase 3 coverage

`system_lower_bound_clamp` fires on **0 of 2 280** campaign rows: no annualized
system number in this campaign is a grid-clamped lower bound.
`bep_clamped_above_grid` fires on **16 rows — 8 at KP 57.4 bulk and 8 at
KP 58.8 bulk, none at KP 62.0**, reproducing `phase3_report.md` §11.3's
correction exactly.

`phase3_campaign.py` propagates only `coverage["__system__"]["lower_bound_clamp"]`
and `frac_peaks_above_grid` to `rq4_annual.csv`, so the campaign CSV alone
cannot answer `below_grid_unresolved`. The diagnostics stage therefore composes
once through `python -m system_integration` into
`results/production_campaign/coverage/` to capture the full
`AnnualizedResult.coverage` block: **8 files scanned, 0 without the block,
0 flagged curves** — neither `lower_bound_clamp` nor `below_grid_unresolved`
fires on any mechanism or on the composed `__system__` curve.

The legacy ADR-0038 BEP-only `results/system_integration/system_*.json` files
(2026-07-13) were **not** regenerated: they are superseded by the Phase 3
campaign, no consumer reads them, and they predate the HKV-audit coverage
feature.

## 10. Companions asserting bit-identity

### 10.1 The programmatic enumeration

The companion set was derived by regex over `scripts/`, `tests/` and the three
packages, requiring **both** a persisted-sweep path reference and a
bit-identity / config-hash assertion pattern — not copied from a list. The
enumeration is stored in the manifest under `companions.enumeration`.

It returned 14 hits. Five are run by this stage
(`ce_prior_study`, `dem_cross_section_study`, `foreshore_width_study`,
`qa_re_halved_member`, `seepage_length_study`). The other nine are excluded for
stated reasons, each classified in `COMPANION_EXCLUSIONS` so an unclassified
hit is a signal to investigate rather than something to wave through:

| Hit | Why it is not run as a companion |
|---|---|
| `scripts/production_campaign.py` | this driver itself |
| `scripts/run_sweep.py` | produces the sweeps; the source, not a consumer |
| `scripts/stage6_6_gap_decomposition.py` | run as its own stage under G3 |
| `scripts/mp_model_factor_companion.py` | **ADR-0045 m_p — OFF in production (decision 3)** |
| `scripts/ztoe_sensitivity_study.py` | **ADR-0046 z_toe — OFF in production (decision 3)** |
| `scripts/prior_mean_scenario_companion.py` | **ADR-0048 prior means — OFF in production (decision 3)** |
| `tests/test_config.py`, `tests/test_fragility.py`, `tests/test_phase2_end_to_end.py` | exercised by `pytest` |

**Three consumers the campaign brief's list omitted**, surfaced by the
enumeration: `mp_model_factor_companion.py` (ADR-0045),
`ztoe_sensitivity_study.py` (ADR-0046) and `prior_mean_scenario_companion.py`
(ADR-0048). All three carry a `config_hash` gate against a persisted sweep, so
they were worth checking. **They are not broken by this campaign**: each
reconstructs its `Config` from the *sidecar's own* `config` block rather than
from `configs/*.yaml`, so the reconstructed hash matches whatever that sidecar
records, before or after the re-run. They stay OFF in production per decision 3
and were not re-run (they are KP 58.8 + KP 60.0 companions).

Conversely, four scripts this stage **does** run are not matched by the regex
(`segment_fragility`, `foreshore_exhaustion_study`, `assess_2011_2006_closure`,
`gsa_study`) — they consume persisted artifacts through helper APIs rather than
literal `results/tokachi_kp*` paths. They are reported under
`run_but_not_matched_by_the_regex` so the enumeration does not silently imply
the regex is complete.

### 10.2 Results

Each companion runs its own internal bit-identity assertion; a non-zero exit is
a gate failure. **All nine ran to completion (G6 pass, 4635 s total).** Where
the driver supports `--out`, the fresh record is written to
`results/production_campaign/companions/` and compared against the committed
evidence with volatile keys stripped, so the tracked documents of record are
never overwritten by a verification run.

| Companion | Runtime | Evidence verdict |
|---|---|---|
| `segment_fragility` | 3.0 s | pass (no committed evidence to compare) |
| `qa_re_halved_member` | 434.5 s | pass — its own drift guard asserts the `scale = 1.0` branch bit-identical to the re-run KP 58.8 matrix sweep at every level |
| `foreshore_width_study` | 1760.4 s | **identical** |
| `seepage_length_study` | 272.2 s | pass — Phase 2 ceiling recomputed on the fresh posteriors: L mean **+1.37 %**, CoV **−3.63 %**, k_aq **−4.15 %** (documented: +0.5 to 1.4 %, −1.7 to 3.6 %, −4 %) |
| `foreshore_exhaustion_study` | 54.1 s | **identical plus additions** — see below |
| `assess_2011_2006_closure` | 473.2 s | **identical** (all 8 strata) |
| `dem_cross_section_study` | 1012.6 s | **declared pre-existing staleness** — see below |
| `ce_prior_study` | 54.1 s | pass — the static branch stays exactly C_e-invariant (its internal assert) |
| `gsa_study` | 566.5 s | **identical** — every Sobol' index byte-identical |

Three comparisons needed classification rather than a bare equality test, and
the same asymmetry G1 uses (§3.1) resolves all three:

* **`foreshore_exhaustion_study` — additive.** The committed R10 evidence
  carries `d4pdf_ensemble: null` (it was produced with `--no-ensemble`); this
  run filled it in. Every other field is identical, and the newly computed
  ensemble reproduces the documented figures: KP 62.0 flagged at the central
  1 m/h rate in **1.17 % → 3.59 %** of years historical → +4K, and it is the
  only section flagged in either climate.
* **`assess_2011_2006_closure` and `gsa_study` — volatile-only rewrites of
  tracked records.** Both rewrite a git-tracked evidence file. The ADR-0044
  diff was `runtime_seconds` alone (all eight strata identical:
  `reject_2016_count` 65 / 0 / 5673 / 0 / 3363 / 23 / 0 / 0, marginal beyond
  2016 zero at seven strata and 0.316 % at KP 60.0 matrix). The two ADR-0033
  GSA files differed only in `runtime_seconds` and `config_hash` — **all 6 373
  lines of Sobol' indices byte-identical**. The driver restores such files from
  git so a document of record does not churn on timing noise. `config_hash` is
  excluded from this comparison because it moves by construction in this
  campaign and is asserted directly by G0 and G1; re-failing every companion on
  it would double-count a change already proven inert.
* **`dem_cross_section_study` — a real, pre-existing staleness, declared not
  waived.** The committed ADR-0047 evidence is a **pre-adoption artifact**:

  | section | fresh baseline / arm | committed baseline / arm | baseline bit-identical to production |
  |---|---|---|---|
  | KP 57.4 | 33.0 m / `dem_clean_median`, `dem_all_stations_median` | identical | **True** |
  | KP 58.8 | 35.0 m / `dem_clean_median` | identical | **True** |
  | KP 60.0 | 34.8 m / `dem_clean_median` | identical | **True** |
  | KP 62.0 | **40.0 m / `withdrawn_1998`** | **47.0 m / `dem_clean_median`** | **True** |

  The 2026-07-29 adoption changed the CSV (KP 62.0 `L_m` 47.0 → 40.0) and
  re-pinned this driver so the adopted 40 m is the baseline and the withdrawn
  47 m the sensitivity arm — but the JSON was never regenerated, so its
  `measurements[KP62.0].csv_L_m` still reads 47.0. Three of four section blocks
  are byte-identical; only KP 62.0 moved, in exactly the direction the adoption
  dictates. **The campaign-relevant claim passes at all four sections in both
  records**: every baseline arm asserts bit-identical to its persisted
  production sweep.

  The gate treats this as a **declared** exception (`expected_changed_keys`
  with a stated reason in the driver), not a waiver: any key outside
  `{fragility, measurements}` still fails. **Remedy, which belongs to the
  figure pass because it re-renders a figure:**
  `python scripts/dem_cross_section_study.py all --overwrite`. The correct
  post-adoption content is available meanwhile at
  `results/production_campaign/companions/adr0047-dem-seepage-length.json`.

  (`datum_check` is absent from the fresh record only because this stage runs
  the `fragility` stage, not `all`; the classifier reports that separately as
  `omitted_keys` — scope, not a change.)

## 11. What this campaign changes in the reports of record

Two categories, kept separate because they carry different weight.

### 11.A Numbers this campaign actually changes

Only two, and both for the same reason: those runs had been left on the
withdrawn L = 47.0 m Phase 1 (hash `e9b8760b`) and now consume the ADR-0047
adopted L = 40.0 m (`613add6c`).

| Document | Location | Was | Is now |
|---|---|---|---|
| `phase2_report.md` | §11.3, anchor sensitivity | KP 62.0 "0.00 % → 0.01 %" | **0.00 % → 0.05 %** (0.0060 % → 0.0470 %) |
| `phase2_report.md` | §11.3, criterion sensitivity | KP 62.0 "30.46 %" strict posterior | **39.55 %** |

The surrounding claims survive: KP 62.0 remains the one usable-size strict
posterior, and the reading it supports (the initiation margin and the
progression margin separate cleanly at the governing section, since breach
rejection there is exactly zero while the gate latches for a large minority)
is unchanged in kind and slightly stronger in degree.

**Everything else in all three reports reproduces.** All eight baseline Phase 2
rejections, all six non-KP-62.0 variant members, every Phase 1 failure matrix,
every RQ3 share, every RQ4 annual number (G4: zero changed rows), and both
Stage 6.6 drift guards.

### 11.B Numbers this campaign finds already stale

These were stale *before* this campaign — the ADR-0047 adoption addenda
corrected the headline numbers but did not restate the component and bracket
tables that the same adoption moved. The campaign re-measured them.

**`docs/phase3_report.md` §6.1** (see also §8 above for the decision-5 scope
change):

| Claim | Status |
|---|---|
| "Segments above 1e-3/yr go from **2 to 45** of 114" | **3 to 45.** KP 62.0's historical annual rose 5.24e-4 → 1.006e-3 at the adoption, crossing the threshold. §11.2 tabulated that move but never revisited this count. |
| "system ratio is 5.5–**19.5**x (… KP62.0 **19.5**)" | **5.5 to 12.7 ×, KP 62.0 12.7** (already superseded by §11.2; restated here because §6.1 still carries the old range). |
| median 0 → 3.7e-4; mean 1.0e-4 → 1.9e-3 (~18 ×); >1e-2/yr 0 → 4 | values reproduce exactly; **their role changes** under decision 5 (see §8.2). |

**`docs/phase3_report.md` §6.2** — four KP 62.0 bracket numbers, all computed
against the superseded 5.24e-4 historical base:

| Bracket | Report says | Re-measured |
|---|---|---|
| λ_ac = 40 m, KP 62.0 | ×3.1 / ×1.6 | **×3.3 / ×1.9** |
| bulk d70, KP 62.0 | historical ×2.6, +4K ×1.2 | **×5.0 / ×1.5** |
| `scour_script_k`, KP 62.0 | "~45 % (5.24e-4 → 7.59e-4)" | **+22 % (1.006e-3 → 1.225e-3)** |
| `overflow_sine30h`, KP 62.0 | "−19 to −27 % (+4K 1.02e-2 → 8.25e-3, hist 5.24e-4 → 3.81e-4)" | **hist 1.006e-3 → 8.843e-4 (−12 %), +4K 1.278e-2 → 1.117e-2 (−13 %)** |

The other §6.2 numbers reproduce exactly: λ_ac brackets at KP 57.4 (×3.4/×2.2),
KP 58.8 (×2.5/×2.1) and KP 60.0 (×3.4/×2.7); bulk d70 KP 58.8 +4K
4.09e-2 → 2.71e-3 (×15) and KP 57.4 historical 7.53e-4 → 2.07e-6; prior vs
posterior −12 % at KP 58.8 historical (8.467e-3 → 7.420e-3); `scour_script_k`
KP 57.4 historical 7.530e-4 → 8.129e-4 (+8 %).

**`docs/phase3_report.md` §5.1** — already withdrawn in §11.1/§11.3 and
re-confirmed here: KP 62.0 historical BEP share is **0.812** (not 64 %), +4K is
**0.500 / 0.500** (not 34 / 66 %), the "BEP dominant at all four sections
historically" range is **81 to 100 %** (not 64 to 100 %), "overflow leads only
at KP 62.0 under +4K" no longer holds, and the `bep_clamped_above_grid`
parenthetical is false (0 of 20 KP 62.0 rows; the flag fires on 16 rows, all
KP 57.4 / KP 58.8 **bulk**).

**`docs/stage6_6_report.md`** — the KP 62.0 half of §1 and §4.1 is on the
withdrawn geometry. Every KP 57.4 number reproduces exactly, as §8 states.

| Claim | Report says | Re-measured |
|---|---|---|
| §1, KP 62.0 total ratio range | "falls from **15** at 47.0 m to **1.9** at 50.5 m" | **10.5 at 47.0 m to 1.4 at 50.5 m** |
| §4.1, KP 62.0 46.39 m (HWL) | C0 2.1e-4, C4b 1.0e-5 | **C0 1.79e-3, C4b 4.0e-5** (4 failing rows) |
| §4.1, KP 62.0 48.00 m | C0 0.245, C4b 0.036 | **C0 0.4435, C4b 0.1013** |
| §4.1, KP 62.0 50.50 m | C0 0.944, C4b 0.496 | **C0 0.9844, C4b 0.6896** |
| §4.1, KP 62.0 pure temporal C3b/C4b | "7.9 at 47.0 m down to 1.9 at 50.5 m" | **6.0 at 47.0 m down to 1.4 at 50.5 m** |
| §1/§4.1, all KP 57.4 values | 1.18e-3 / 0 at HWL; 0.616 / 0.206 at 40.5 m; 13.5 → 1.04; C3b/C4b 3.2 → 1.04 | **all reproduce exactly** |

The §4.2 (dimensional), §4.4 (H_eq-conservatism) and §4.5 (Shapley) component
values quoted at **KP 62.0, 48.0 m** rest on the same withdrawn geometry and
should be re-read from `results/stage6_6/stage6_6_kp62_0_analysis.json` before
being quoted; this campaign did not restate them because they are not headline
numbers. The KP 57.4 values in those sections stand.

**`docs/decisions/adr0047-dem-seepage-length.json`** — the ADR-0047 evidence
JSON is itself a pre-adoption artifact: its KP 62.0 block still names
`baseline_L_m = 47.0` with arm `dem_clean_median`, and its
`measurements[KP62.0].csv_L_m` still reads 47.0 against the current CSV's 40.0.
The driver was re-pinned at the adoption; the record was not regenerated. See
§10.2 for the full comparison and the one-command remedy.

**The pattern.** All four items in this section are KP 62.0 and only KP 62.0.
The ADR-0047 adoption correctly updated the headline numbers, the code and the
CSV, and correctly left KP 57.4 / 58.8 / 60.0 alone — but it did not sweep
forward the *derived* tables and records that the same change moved. Every
KP 57.4 / 58.8 / 60.0 number in all three reports reproduces exactly under this
campaign, which is the strongest available evidence that the adoption's
containment claim was sound and that the residue is purely documentary.

### 11.C Not changed, and worth stating explicitly

* The **marginal transient rejection = 0 in every stratum** headline
  (`phase2_report.md` §11.1, §14) survives at production N under the adopted
  geometry.
* The **Phase 2 tiering caveat** (§11.2) is unchanged: informative updates land
  at the drained sections KP 58.8 / KP 60.0, and the engine evaluates the
  unremediated foundation there by design (decision 4).
* The **WBI+ peak-shortcut over-rejection** factors (2.75 to 3.9 ×) are
  unaffected — they derive from the baseline rejections, which reproduce.
* The **Phase 3 event-based validation** and the §7 invariants re-ran and
  passed.

## 12. Open item — decision 6 — **CLOSED 2026-07-30**

> **Closure note (2026-07-30).** The owner supplied the method — brute force at
> N = 1e6 at KP 62.0, then validate tilted importance sampling against it, then
> apply the validated estimator at KP 57.4 — and it was executed under a written
> pre-registration: `docs/decisions/adr0040-hwl-bias-resolution.md`, driver
> `scripts/hwl_bias_resolution.py`, evidence
> `docs/decisions/adr0040-hwl-bias-resolution.json`. Outcome in one paragraph:
> **KP 62.0's design-HWL bias is now resolved at 26.9 (95 % CI 21.6 to 35.3) on 63
> failing rows**, superseding the 44.7 in §6.1 below, which rested on 4 rows and
> overstated the bias by 1.66× (the two are statistically consistent — this was
> counting noise, not a different answer). **KP 57.4 remains unresolved even at
> N = 1e6** (2 failing rows); its defensible statements are a bound **B ≥ 148** at
> the design HWL, superseding *"at least 32"*, and a resolved anchor **42.7
> [39.4, 46.6] at 39.50 m MSL**. **The tilted estimator did NOT validate** and no
> weighted number was used. §6.1's tables below are unchanged as the N = 1e5
> record; `docs/stage6_6_report.md` §9 is the authoritative reading.
>
> One finding from that work touches this campaign's own gates: at **N = 1e6**,
> KP 57.4 shows **4 Euler-flip rows in 1e6** (levels 39.50, 40.25, 40.75), which
> the campaign's G3 could not have seen at N = 1e5 where the expected count is
> 0.4. **No campaign result is affected** — every production artifact runs at
> N = 1e5, where G3 passed and the drift guard is bit-identical — but a future
> higher-N campaign at KP 57.4 should expect this gate to fire and should read
> ADR-0039's Δt rider alongside it.

The decisions-of-record block for this campaign carried decision 6 as an
unfilled placeholder: *"Design-HWL bias resolution method: `<your D-6 answer>`"*.
No method was recorded at the time, so none was applied or invented then.

Its operative clause **was** honoured: nothing forecloses a higher-N or
importance-sampled Stage 6.6 re-run. Specifically, `results/stage6_6/` carries
the full `(100 000 × 39)` and `(100 000 × 23)` comparator matrices for all ten
comparators plus `seepage_length_samples` and `param_names`, the superseded
copies are preserved under `results/superseded_<timestamp>/stage6_6/`, and the
ladder driver (`scripts/stage6_6_gap_decomposition.py`) accepts `--n` and
`--skip-run` so a higher-N arm can be added without disturbing the production
arm.

§6.1 quantifies exactly what such a re-run would have to fix: at design HWL the
transient comparator rests on **4 failing rows at KP 62.0 and 0 at KP 57.4**,
so the headline bias is unresolved at precisely the level the thesis most wants
to quote. The ADR-0029 tilted-importance-sampling machinery
(`tail_sampling.sample_theta_tilted`, `cross_entropy_shift`,
`importance_estimate`) exists and was measured to cut deep-tail CoV 3.2 to
4.1 × at `P_f` ≈ 1e-4, which is the regime in question.

## 13. Reproduction

```powershell
python scripts/production_campaign.py            # everything, resumable
python scripts/production_campaign.py --dry-run  # the plan
```

Manifest: `results/production_campaign_manifest.json`. Logs:
`results/production_campaign/logs/`. Superseded artifacts:
`results/superseded_<timestamp>/`.
