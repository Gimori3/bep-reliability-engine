# The foreland seepage-length credit: how large it is, and whether it cancels

**Status:** Accepted. Companion measurement for ADR-0052, which wires the knob.
No `Config` default changed, no production sweep re-run, no persisted production
artifact touched.

**Date:** 2026-09-13
**Driver:** `scripts/foreland_credit_bracket_study.py` (Phase 1),
`scripts/foreland_credit_annualisation.py` (Phase 3)
**Evidence:** `adr0052-foreland-credit-companion.json` and
`adr0052-foreland-credit-annualisation.json` beside this note
**Pre-registration:** `adr0052-foreland-credit-prereg.md`, its SHA-256 pinned in
the companion JSON
**Arms:** `results/sensitivity/adr0052_foreland_credit/` (12 full-N sweeps)
**Tests:** `tests/test_foreland_seepage_credit.py`
**Parents:** ADR-0052 (the knob), ADR-0005/0006 (the foreland entry length),
ADR-0028 (the clause this amends), ADR-0047 §4.5 and
`epistemic-bracket-synthesis.md` (the cancellation test and its vocabulary),
ADR-0049 and ADR-0050 (the two single-branch knobs this one is the opposite of)

---

## 1. What this closes

The engine carries a foreland entry resistance in `r_e` and declines it in
Sellmeijer's rule. Since ADR-0028 that is the whole asymmetry: `r_e` reaches the
uplift and heave gate and nothing else, both piping heads are gross, and both
limit states evaluate `H_c` at the under-levee `L`. At the prior means the
declined entry resistance is 29 to 43 per cent of the total series resistance.

ADR-0028 justified the arrangement with a sentence that is wrong on both
premises, and that clause is now amended in place there. TR Zandmeevoerende
Wellen (1999) §4.4.2 permits the credit and does not require it, so declining it
is a recognised conservative simplification rather than an omission. What the
repository lacked was the measurement. This note is it.

## 2. The arms

| arm | `phi` | what it is |
|---|---|---|
| `credit_half` | 0.5 | a partial credit, so the response is shown to be graded |
| `credit_full` | 1.0 | exactly the TR Zmw 1999 §4.4.2 displacement `L'_v` |

Neither arm is a counterfactual: the upper arm is the credit the source
licenses, and the baseline (credit declined) is the other edge.

## 3. Method

Four matrix sections, both arms, production N = 1e5 on the committed
conditioning grids.

**The gate.** Each section's committed YAML is re-run with
`foreland_seepage_credit=None` set *explicitly*, and both whole failure matrices
are required to be bit-identical to the persisted production sweep before any
arm number at that section is reported. **All four passed.** One run discharges
two obligations: the knob is inert when off, and the baseline has not drifted.

**The cancellation test** is the ADR-0047 §4.5 paired-bootstrap ratio of ratios,

    rho = (P_static / P_transient)_arm / (P_static / P_transient)_baseline

2000 replicates over the 16 joint pattern counts, null pinned at `rho = 1.0`, a
level counted resolved only when the 95 % interval excludes it. The statistic is
imported from `scripts/dem_cross_section_study.py`, not re-implemented.

**What the driver refuses to assume.** Unlike ADR-0049 and ADR-0050, this knob
is expected to move the static column, so the driver cannot assert invariance.
It asserts instead the one thing that must hold — a raised `H_c` can only remove
failures, never create them — and **counts** the static cells that move.

## 4. The prior-mean series split

Computed through the engine's own kernels from each committed config's prior
means (`prior_mean_baseline` in the driver; reproduced in the companion JSON):

| section | `lambda_in` | `lambda_out_eff` | `L` | `Sigma` | entry share | `r_e` | `H_c(L)` | `H_c(L_eff)` | `kappa` |
|---|---|---|---|---|---|---|---|---|---|
| KP 57.4 | 102.470 | 98.418 | 33.0 | 233.887 | 42.08 % | 0.4381 | 2.034 | 7.082 | 3.481 |
| KP 58.8 | 116.619 | 115.737 | 35.0 | 267.356 | 43.29 % | 0.4362 | 2.130 | 7.954 | 3.734 |
| KP 60.0 | 87.464 | 87.464 | 34.8 | 209.728 | 41.70 % | 0.4170 | 1.956 | 6.062 | 3.099 |
| KP 62.0 | 38.730 | 31.491 | 40.0 | 110.221 | 28.57 % | 0.3514 | 3.214 | 5.409 | 1.683 |

`r_e` reproduces the four values the thesis prints in §3.3.2 (0.438 / 0.436 /
0.417 / 0.351), which is the setup check the measurement was gated on.

## 5. Result

### 5.1 The design level: both branches go to zero

Failing realizations of 1e5 at each section's design HWL grid point:

| section | stage [m MSL] | baseline static | baseline transient | half credit | full credit |
|---|---|---|---|---|---|
| KP 57.4 | 39.25 | 207 | 0 | 0 / 0 | 0 / 0 |
| KP 58.8 | 41.00 | 72 206 | 26 273 | 0 / 0 | 0 / 0 |
| KP 60.0 | 42.75 | 91 650 | 31 427 | 224 / 0 | 0 / 0 |
| KP 62.0 | 46.50 | 393 | 15 | 0 / 0 | 0 / 0 |

**The independent audit's claim is confirmed**: under the full credit the design
level carries 0 failing realizations of 1e5 on **both** branches at **all four**
sections. It is confirmed for the half credit too, with one exception the audit
did not have: KP 60.0 keeps **224** static rows at `phi = 0.5`, and none
transient.

The KP 58.8 row is the one to quote. A credit of **half** the entry-point
displacement takes 72 206 static and 26 273 transient failures to exactly zero —
a collapse of at least four orders of magnitude in each branch, from a section
whose baseline design-level static probability is 0.72.

### 5.2 The cancellation test

`rho > 1` at **every resolved level, of every section, in both arms** — 101
resolved levels, 101 above unity, none below, none unresolved-but-evaluated:

| section | arm | levels evaluated | resolved | `rho` range | static cells moved |
|---|---|---|---|---|---|
| KP 57.4 | half | 8 | 8 | 2.005 to 10.220 | 962 648 |
| KP 57.4 | full | 1 | 1 | 8.726 | 1 187 918 |
| KP 58.8 | half | 12 | 12 | 1.399 to 12.262 | 1 160 356 |
| KP 58.8 | full | 5 | 5 | 6.120 to 20.607 | 1 750 478 |
| KP 60.0 | half | 16 | 16 | 1.138 to 51.783 | 820 746 |
| KP 60.0 | full | 10 | 10 | 2.749 to 65.412 | 1 576 024 |
| KP 62.0 | half | 26 | 26 | 1.010 to 2.279 | 421 982 |
| KP 62.0 | full | 23 | 23 | 1.031 to 2.811 | 790 935 |

The bracket does **not** cancel, and it is not close to cancelling: the smallest
resolved departure anywhere is 1.010 and the largest is 65.4.

No `trans_not_static` row appears in any baseline or arm at any level, so no
ADR-0030 forward-Euler barrier jump contaminates the comparison.

### 5.3 Pre-registered prediction against outcome

The prediction was frozen in `adr0052-foreland-credit-prereg.md` before any
credited arm ran; its SHA-256 is pinned in the companion JSON and by test.

| | prediction | outcome |
|---|---|---|
| **P1** | neither branch invariant; the static matrix *will* move | **HELD.** Between 4.2e5 and 1.75e6 static cells move per section-arm. |
| **P2** | the bracket does not cancel, `rho != 1` where both branches resolve | **HELD.** 101 of 101 resolved levels exclude unity. |
| **P3** | `rho > 1`: the credit *widens* the static-to-transient bias | **HELD, without exception.** Every resolved `rho` is above 1, at both arms and all four sections. |
| **P4** | the per-section displacement orders by `kappa`: KP 58.8 > KP 57.4 > KP 60.0 > KP 62.0 | **FAILED.** Observed max `rho` orders KP 60.0 (65.4) > KP 58.8 (20.6) > KP 57.4 (8.7) > KP 62.0 (2.8). Only the last place held. |
| **P5** | `rho` unresolvable at most levels; the design level a pair of zero counts | **HELD.** 1 to 26 levels resolve out of 23 to 38, and every design level is 0/0 under the full credit. |

**P4 is the informative failure and is reported as one.** The reasoning behind it
was that a bigger `kappa` must buy a bigger displacement of the ratio. It does
not, because `rho` is a ratio of two tail probabilities and what decides its size
is where the section's *baseline* curves sit relative to the stages that remain
resolvable after the credit, not how far the credit pushes `H_c`. KP 60.0 has the
third-largest `kappa` and much the largest `rho` because its baseline transient
curve is the steepest through the band where both arms still carry countable
failures. The lesson is the one ADR-0049 already recorded in a different form:
**a `rho` departure is not a mechanism, and it cannot be read off an input's
own magnitude.**

### 5.4 Stage displacement of the sustained-peak bound

Under the credited arms the transient transition leaves the reachable grid at
every section, so the displacement is measured on the ADR-0040 closed-form
sustained-peak upper bound `gate AND H_erosion > H_c,trans`, which is defined at
every stage. Scanned at 0.05 m, five times finer than the 0.25 m production
grids, through `evaluate_batch_diagnostics` on a held-peak record so the gate
latch, `H_c` and the crack term all come from the engine's own shared preamble.

Stage at which the bound's exceedance probability reaches each anchor, and the
shift from baseline [m]:

| section | anchor | baseline [m MSL] | half credit | shift | full credit | shift |
|---|---|---|---|---|---|---|
| KP 57.4 | 1e-3 | 39.45 | 41.46 | +2.02 | 43.20 | +3.76 |
| KP 57.4 | 1e-2 | 39.64 | 41.81 | +2.17 | 43.70 | +4.05 |
| KP 57.4 | 0.1 | 39.99 | 42.33 | +2.34 | 44.43 | +4.44 |
| KP 57.4 | 0.5 (median) | 40.58 | 43.11 | +2.54 | 45.49 | +4.92 |
| KP 58.8 | 1e-3 | 39.71 | 42.08 | +2.37 | 44.07 | +4.35 |
| KP 58.8 | 1e-2 | 39.92 | 42.44 | +2.52 | 44.60 | +4.68 |
| KP 58.8 | 0.1 | 40.28 | 43.00 | +2.72 | 45.40 | +5.12 |
| KP 58.8 | 0.5 (median) | 40.89 | 43.82 | +2.93 | 46.57 | +5.67 |
| KP 60.0 | 1e-3 | 41.22 | 42.92 | +1.69 | 44.34 | +3.12 |
| KP 60.0 | 1e-2 | 41.41 | 43.20 | +1.79 | 44.74 | +3.33 |
| KP 60.0 | 0.1 | 41.72 | 43.64 | +1.92 | 45.36 | +3.64 |
| KP 60.0 | 0.5 (median) | 42.24 | 44.30 | +2.06 | 46.25 | +4.01 |
| KP 62.0 | 1e-3 | 46.45 | 47.28 | +0.82 | 48.05 | +1.60 |
| KP 62.0 | 1e-2 | 46.78 | 47.68 | +0.90 | 48.53 | +1.75 |
| KP 62.0 | 0.1 | 47.33 | 48.33 | +1.00 | 49.28 | +1.95 |
| KP 62.0 | 0.5 (median) | 48.25 | 49.34 | +1.09 | 50.42 | +2.16 |

Summarised, the shift of the bound across the four anchors:

| section | half credit | full credit |
|---|---|---|
| KP 57.4 | +2.02 to +2.54 m | +3.76 to +4.92 m |
| KP 58.8 | +2.37 to +2.93 m | +4.35 to +5.67 m |
| KP 60.0 | +1.69 to +2.06 m | +3.12 to +4.01 m |
| KP 62.0 | +0.82 to +1.09 m | +1.60 to +2.16 m |

The independent audit that opened this question expected +1.6 to +2.2 m at
KP 62.0, +3.2 to +4.0 at KP 60.0, +4.4 to +4.7 at KP 58.8 and +3.8 at
KP 57.4 for the full credit. **KP 62.0 and KP 57.4 reproduce exactly**; KP 60.0
reproduces to within 0.08 m at its low end; and KP 58.8's upper end is larger
here (+5.67 against +4.7) because this table carries the median anchor, which
that range did not. Nothing in it is contradicted.

**These are displacements of an indicator, never attainable stages.** The
credited crossings sit above every section's attainable maximum (ADR-0024), and
KP 62.0's grid above 50.5 m is a hypothetical fit-stabiliser.

### 5.5 Phase 3: the credit carried through the annualisation

`scripts/foreland_credit_annualisation.py`, matrix reading, prior side. The
composition and annualisation steps are **imported** from
`scripts/conductivity_annualisation_study.py`, which imports them from the
campaign, so the production code path is what runs. Gate 1 (the baseline pass
reproduces `rq4_annual.csv` exactly, 228 rows x 20 fields) and gate 3 (the 220
non-BEP segment rows bit-identical across every arm) both passed.

Annual system probability at the four BEP sections:

| section | scenario | baseline | half credit | full credit | full / baseline |
|---|---|---|---|---|---|
| KP 57.4 | historical | 7.548e-04 | 0 | 0 | 0 |
| KP 57.4 | +4K | 9.542e-03 | 9.724e-04 | 9.114e-04 | 0.0955 |
| KP 58.8 | historical | 8.467e-03 | 2.034e-04 | 1.951e-04 | 0.0230 |
| KP 58.8 | +4K | 4.462e-02 | 3.391e-03 | 2.532e-03 | 0.0568 |
| KP 60.0 | historical | 2.025e-03 | 1.939e-06 | 0 | 0 |
| KP 60.0 | +4K | 1.534e-02 | 4.829e-04 | 2.433e-05 | 0.0016 |
| KP 62.0 | historical | 1.006e-03 | 3.228e-04 | 2.099e-04 | 0.2087 |
| KP 62.0 | +4K | 1.278e-02 | 9.155e-03 | 8.475e-03 | 0.6633 |

**The RQ3 dominance statement does not survive the credit.** Piping's share of
the summed annual contribution, historically:

| section | baseline | half credit | full credit |
|---|---|---|---|
| KP 57.4 | 1.000 | 0.000 | 0.000 |
| KP 58.8 | 0.977 | 0.043 | 0.000 |
| KP 60.0 | 1.000 | 1.000 | 0.000 |
| KP 62.0 | 0.812 | 0.407 | 0.059 |

The published claim is that piping accounts for **81 to 100 per cent** of the
summed annual contribution at these four sections historically, and the baseline
pass reproduces exactly that (1.000, 0.977, 1.000, 0.812). Under the full credit
the same four shares are **0.000, 0.000, 0.000, 0.059**: piping stops being the
leading mechanism everywhere, and overflow carries the number. Across all eight
section-and-climate cells the full credit leaves **0 of 8** inside the published
band, the half credit 2 of 8.

This is the largest single displacement of an RQ3 headline any knob in the
register has produced. It is **not** a refutation of the published result — the
published result declines a permissive credit, which is the conservative side —
but it is the strongest available statement of how much that choice is worth,
and the dominance claim must never be quoted without it.


### 5.6 The posterior side, and why it is the same

**Added 2026-09-14.** Section 5.5 above annualises the **prior** side. The
published RQ3 and RQ4 headline does not: `scripts/phase3_campaign.py` defaults
to `bep_source = posterior`, and the thesis's KP 58.8 historical
7.45e-3 is the posterior row of `rq4_annual.csv` (the prior row is 8.47e-3). So
the prior-side table qualified numbers the thesis does not print, and the
like-for-like comparison had to be measured on the side the claim lives on.

It was, through `scripts/foreland_credit_annualisation.py --side posterior`
after replaying all eight ADR-0052 arms through the ordinary Phase 2 CLI. Gate 1
(the baseline pass reproduces `rq4_annual.csv` field for field, 228 rows x 20
fields) and gate 3 (220 non-BEP rows bit-identical across every arm) both
passed.

**The arm values are bit-for-bit identical to the prior side at all 8 of 8
cells.** That is not a coincidence and it is the finding:

> **Under the credit, the 2016 survival record rejects nothing.** All eight arm
> replays return `accepted 100,000 of 100,000 rows (rejection 0.00%)` — both
> arms, all four sections. The credited `H_c` is so far above the observed
> loading that no realization fails under it, so the posterior *is* the prior
> and the survival constraint carries no information at all.

Only the *baseline* differs between the two sides, because only the baseline is
actually filtered by the 2016 record. The consequence for the headline is
therefore that the RQ3 verdict is **unchanged** on the side that matters:

| section | baseline (posterior) | half credit | full credit |
|---|---|---|---|
| KP 57.4 | 1.000 | 0.000 | 0.000 |
| KP 58.8 | 0.974 | 0.043 | 0.000 |
| KP 60.0 | 1.000 | 1.000 | 0.000 |
| KP 62.0 | 0.812 | 0.407 | 0.059 |

Full credit leaves **0 of 8** section-and-climate cells inside the published
81-to-100-per-cent band, exactly as on the prior side. §5.5's conclusion stands;
what changes is that it now rests on the comparison the thesis actually makes.

There is a second-order point worth keeping. The credit and the 2016 update
both push in the same direction — both remove failing realizations — but they
cannot compound, because the credit removes the very realizations the update
would have rejected. A study that credited the foreland *and* claimed the
survival constraint as additional evidence would be counting the same evidence
twice. Here it is measured to be exactly zero the second time.

## 6. What this does and does not license

- It does **not** change the production baseline, any default, or any published
  number. The credit stays declined.
- It **does** put a two-sided bound on the conservatism of declining it, at the
  conditional curves, at the design level, on the bias ratio and through the
  annualisation.
- The bracket is **one-sided in construction**, because §4.4.2 offers an
  increase in seepage length and nothing else. There is no counterfactual arm
  below the baseline, and none is invented.
- ~~Every number here is matrix-reading.~~ **Closed 2026-09-14**: the bulk
  reading is §7, and it agrees in direction while resolving over a much
  smaller window.

---

## 7. The bulk d70 reading

**Added 2026-09-14**, closing §6's stated omission. Twelve further full-N
sweeps, `python scripts/foreland_credit_bracket_study.py --reading bulk`;
evidence `docs/decisions/adr0052-foreland-credit-companion-bulk.json`. **All
four gates passed bit-identical** against the persisted bulk production sweeps.

`kappa` is identical to the matrix reading at every section (3.481 / 3.734 /
3.099 / 1.683), which is expected and worth stating: the credit is
`phi * lambda_out_eff`, and `lambda_out_eff` depends on `k_aq`, `D_aq` and the
foreshore geometry, not on `d_70`. The two readings differ only in where the
baseline curves sit, not in how far the credit moves them.

### 7.1 Design level

Failing realizations of 1e5 at each section's design HWL grid point:

| section | baseline static / transient | half credit | full credit |
|---|---|---|---|
| KP 57.4 | 0 / 0 | 0 / 0 | 0 / 0 |
| KP 58.8 | 1 / 0 | 0 / 0 | 0 / 0 |
| KP 60.0 | 9 264 / 1 054 | 0 / 0 | 0 / 0 |
| KP 62.0 | 0 / 0 | 0 / 0 | 0 / 0 |

The matrix conclusion carries over: under either credit the design level holds
**0 failing realizations of 1e5 on both branches at all four sections**. Under
bulk it is a weaker statement, because three of the four baselines are already
at or near zero — only KP 60.0 has a design-level population to remove.

### 7.2 Cancellation

`rho > 1` at **every level where it resolves: 18 of 18**, range 1.13 to 12.25.
So the direction is the same as under matrix and P3 holds again.

**P2 fails under bulk, and the reason is resolution rather than physics.** Of
21 evaluated levels only 18 resolve; at three levels (KP 62.0, half credit) the
95 % interval covers unity. That does **not** demonstrate cancellation at those
levels — it means the bulk baseline carries too few failing realizations there
for the test to exclude it either way. Stated the other way round: under bulk
the bracket is measured over a much smaller resolvable window (18 levels
against the matrix reading's 101), because the bulk curves sit far lower.

P1, P3 and P5 hold as under matrix; P4 fails again, and more emphatically --
the observed order is KP 60.0 > KP 62.0 > KP 57.4 = KP 58.8 (the last two
having no resolvable level at all), against a `kappa` order of KP 58.8 >
KP 57.4 > KP 60.0 > KP 62.0. This is the second independent confirmation that
the displacement of the ratio is set by where the baseline curves sit, not by
the size of the input's own perturbation.

### 7.3 Stage displacement

Under bulk the sustained-peak bound is pushed so far that the credited curve
often leaves even the extended scan range: the median crossing is undefined
under full credit at KP 57.4, KP 58.8 and KP 62.0, and under half credit at
KP 58.8. Where both crossings exist, the full-credit shift at the 1e-3 anchor
is **+8.59 m** (KP 57.4), **+6.06 m** (KP 60.0) and **+5.25 m** (KP 62.0),
against the matrix reading's +3.76, +3.12 and +1.60 m. The credit is worth
*more* stage under bulk, not less, because the bulk curves are flatter in the
band the bound crosses.

**These are displacements of an indicator, never attainable stages**, and under
bulk several of them sit above the top of the scan, which is itself well above
any attainable level.
