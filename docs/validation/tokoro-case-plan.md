# Tokoro main-stem boil sites — case plan (DRAFT, not yet executed)

Status: **PLAN ONLY** (drafted 2026-07-13 during the final-campaign
close-out). The Japanese validation campaign (2026-07-11) deliberately
weighted Tokoro as a *corroboration anchor* — the committee's own
uplift-criterion result and test pits, no independent engine run
(`_thesis_validation_japan.tex`, campaign table). This plan specifies what a
full fourth engine case would require, so the author can decide whether the
marginal evidence justifies the digitization effort.

## Source status — better than assumed

The committee report **is local**:
`docs/references/icrceh00000032zs_compressed.pdf` = 常呂川堤防調査委員会
報告書 (Tokoro River Levee Investigation Committee, March 2017, 74 pp).
Relevant sections (from the TOC):

* §2.3.5 — foundation-leakage boils on the Tokoro main stem (噴砂 at
  KP 24.6–27.1; the 2016 typhoon sequence, same storms as the Tokachi
  constraint).
* §5.3 — boil-site investigation: locations (5.3.1), investigations incl.
  the surface-wave profiling and seepage analysis (5.3.2), causal factors
  (5.3.3).
* §7.2 / §7.3 — test-pit and levee-opening surveys (the networked
  sand-filled cracks / thin-cover observations already cited in the
  synthesis).

So the case is **not blocked on the report** (previously assumed class D);
it is blocked on the *digitization effort* and two data gaps listed below.

## What the case would test (pre-registered purpose, per house rules)

1. **M5 gate, third independent instance:** the committee's seepage
   analysis found uplift violated exactly where boils appeared *only when
   the thin surface clay was modeled explicitly*. Reproducing that with the
   engine's Terzaghi gate on the committee's own heads would extend the
   "initiation unbiased conditional on FEM heads" finding from 5 to 6-7
   instances, including away-from-toe exits.
2. **M4 connectedness pattern, fifth point:** Tokoro's boils sit on
   paleochannels/thin-cover windows; the M4 instantaneous-translation
   factor measured against the committee's seepage heads would add the
   decisive fifth point to the 1.13-2.7x connectedness pattern
   (shikaga-case.md §3) — the pattern that currently rests on four points
   from two river systems.
3. **No-breach transient consistency:** boils but no BEP breach on the
   main stem in 2016; the engine should place these sites in the
   initiated-but-not-progressed regime (the Yabe R11.86k/L16.10k analog).

## Required inputs (and their status)

| input | source | status |
|---|---|---|
| Boil-site locations + cover thickness | report §5.3.1, test pits §7.2 | local (digitize) |
| Committee seepage-analysis heads/gradients at boil sites | report §5.3.2 | local (digitize; resolution unknown — may be figure-only) |
| Foundation stratigraphy + k values at sites | report §5.3 / §2.1.2 | local (digitize; completeness unknown) |
| 2016 stage hydrograph at the nearest Tokoro gauge (太茶苗 or equivalent) | NOT in repo | **class D — author must supply** (same workbook family as the 2016 Tokachi drop, event window 2016-08-17 to 09-05) |
| d70 / grain-size at boil sites | report §5.3 (if present) | unknown until digitization |

## Effort estimate and recommendation

Comparable to the Shikaga case (~1 day: pre-registered harness +
digitization + note). Recommendation: **defer** unless a reviewer
challenges the M4 connectedness pattern's sample size — the synthesis
already uses Tokoro's committee result as corroboration, and the marginal
scientific gain (points 1-3) does not currently gate any thesis claim. If
executed, follow the house pattern: pre-registered
`scripts/validate_tokoro.py` harness, figure-digitized values flagged
READ-OFF, note in `docs/validation/tokoro-case.md`.
