# The composition seam: measuring the stage-rating error instead of bounding it

**Status:** Accepted. Un-numbered companion study: it adds no `Config` field,
changes no default, and alters no persisted production result, so it consumes no
ADR number. The arm is a labeled sensitivity companion in the sense ADR-0042
already established for `scour_script_k` and `overflow_sine30h`, and it is
governed by that ADR.

**Date:** 2026-08-21
**Driver:** `scripts/composition_seam_rating_error_study.py`
**Evidence:** `composition-seam-rating-error.json` beside this note
**Product:** `data/processed/uemura_surface_curves/uemura_surface_curves_overflow_no_rating_error.csv`
**Tests:** `tests/test_uemura_models.py` (4 added)
**Parents:** ADR-0042 (the surface-curve re-execution and its decision 6 rating
error), ADR-0038 (the composition contract), ADR-0043 (the section table)

---

## 1. What this closes

The three mechanism curves are composed on one stage axis, but they do not read
that axis the same way. Uemura's overflow model carries the paper Eq. (10)
stage-rating error as an additive per-draw term on the water level,
`wl = h + wl_err`, so its argument `h` is *the stage a rating relation would
report*. The piping curve takes the same argument as *the realized stage at the
levee*. Composing the curves as received joins two slightly different readings
of one axis.

The thesis stated the seam rather than absorbing it, and bounded it by analogy
with the Phase 2 record-reconstruction sensitivity. An analogy is not a
measurement, and the seam sits on the branch that decides the one mechanism
ordering in the reach that is close enough to turn over.

## 2. Method

The rating-error term is drawn from per-segment mean and standard-deviation
fields, `wl_err_mu_m` and `wl_err_sigma_m`, so an arm with the term suppressed
is a small and well-defined change: `draw_overflow(..., include_rating_error=
False)`. The draw is **taken and then zeroed, never skipped**, so the crest and
turf-critical-velocity draws that follow stay on the identical random stream and
the two arms are coupled by common random numbers on every input except the one
under test. The companion curve set is generated in the same pass as the primary
one, on the same node seed.

The values in force (ADR-0042 decision 6 as amended 2026-07-22, measured from
`Uncertainty_HQrelation.xlsx` for both gauges):

| river | gauge | `wl_err_mu_m` | `wl_err_sigma_m` |
|---|---|---|---|
| Tokachi | Obihiro | **-0.160** | 0.294 |
| Satsunai | Nantai | -0.051 | 0.283 |

The driver then recomposes and re-annualises with the companion overflow curves
overlaid on the otherwise unchanged primary surface set, exactly the way the
campaign handles its two existing surface variants, and imports `_compose_
segment` from the campaign driver rather than re-implementing it.

**Gate.** The primary arm is recomposed from the committed CSVs and required to
reproduce the production `rq4_annual.csv` rows before any companion number is
reported. **Passed on all 8 rows.** The reach-wide dominance counts of the
primary arm also reproduce the published table exactly (piping 4 and 4, overflow
31 and 109, scour 0 and 0, nothing loaded 79 and 1), which is an independent
reproduction of that table from a second driver.

**Regeneration was byte-clean.** The four previously committed curve CSVs are
byte-identical after the pass; only the generation metadata gained a key and a
timestamp, and the provenance gained a paragraph.

## 3. What the arm is, and what it is not

The arm removes from the overflow branch the term the piping branch does not
carry, so that both read the axis as realized stage. That is one of two
consistent treatments. The other, adding the term to the piping branch, would
require re-running Phase 1 on a perturbed loading and is not available here.
**The arm therefore measures the magnitude of the seam and one of its two
directions.** It is not a correction, and it is not the more nearly right
answer; it is the displacement between two readings of one axis.

## 4. Result

### 4.1 The piping branch does not move at all

The annual piping contribution is unchanged to every digit at all four sections
in both climates (displacement 1.000000). The thesis's statement that the seam
"acts on the overflow branch alone" is confirmed as an identity, not an
approximation.

### 4.2 The annual overflow contribution, and the two directions

| section | scenario | overflow, primary | overflow, arm | displacement |
|---|---|---|---|---|
| KP 57.4 | historical | 0 | 0 | not defined |
| KP 58.8 | historical | 1.951e-4 | 2.384e-4 | **1.22** |
| KP 60.0 | historical | 0 | 0 | not defined |
| KP 62.0 | historical | 1.993e-4 | 2.517e-4 | **1.26** |
| KP 57.4 | +4 K | 9.114e-4 | 1.130e-3 | **1.24** |
| KP 58.8 | +4 K | 2.529e-3 | 2.946e-3 | **1.16** |
| KP 60.0 | +4 K | 2.304e-5 | **0** | **0** |
| KP 62.0 | +4 K | 8.392e-3 | 9.799e-3 | **1.17** |

**The sign is not uniform, and that is the finding.** Suppressing the term does
two things at once: it lifts the effective water level by the mean, 0.16 m on
the Tokachi, and it removes the 0.294 m spread. Where the hazard already reaches
the crest band, the mean lift governs and overflow rises by about a fifth. Where
the crest is reached only by the favourable tail of the error, the spread is what
loads the mechanism at all, and removing it takes overflow to exactly zero. KP
60.0 under warming is that case at the characterized sections: its entire
2.30e-5 per year is carried by the upper tail of the rating error.

The reach makes the same point at scale. Segments whose largest contributor is
overflow fall from **31 to 8** historically and from **109 to 69** under warming,
and segments at which no represented mechanism loads at all rise from **79 to
102** and from **1 to 42**. Most of the reach sits deep enough in the tail that
the rating uncertainty, not the stage, is what loads the overflow branch.

### 4.3 The annual system probability and the mechanism shares

The system probability moves by 1.000 to **1.070**, the largest at KP 62.0 under
warming. The piping share falls by at most **0.039**, at KP 62.0 in both
climates; it falls by 0.019 at KP 57.4 and 0.009 at KP 58.8 under warming, by
0.006 at KP 58.8 historically, and is unchanged at the two cells where overflow
returns exactly zero.

### 4.4 The KP 62.0 warming crossing does not survive

| | piping | overflow | margin | leading |
|---|---|---|---|---|
| production | 8.403e-3 | 8.392e-3 | **1.0013** | piping |
| arm | 8.403e-3 | 9.799e-3 | **0.858** | **overflow** |

The piping share goes 0.500 to **0.462**. This is the only mechanism ordering in
the reach that changes: the other three sections keep their leading mechanism in
both climates, and the arm's own reach-wide count moves the piping-leading
segments from 4 to 3 under warming for this one reason.

Read it as the thesis already reads that cell. The displacement in the overflow
contribution, 1.41e-3 per year, is larger than the flood-ensemble sampling
interval on that entry, so the crossing genuinely fails rather than merely
blurring. But the arm's own margin is 1.17-fold, and the resulting share, 0.462,
sits just outside the 0.48 to 0.53 interval the production share carries. What
this establishes is that a production margin of 1.0013 does not survive a
first-order axis displacement, which is the third independent demonstration that
the tie is an artefact of where two curves happen to cross and not a property of
the section. The other two are the canonical event and the conductivity bracket.

## 5. What this licenses

* The seam is **quantified**: at most 1.26 on the annual overflow contribution
  and 1.07 on the annual system probability at the characterized sections, at
  most 0.039 on a mechanism share, and exactly zero on every piping quantity.
* It **does** change the KP 62.0 warming ordering, and every claim resting on
  that ordering has to be stated as the knife edge the thesis already calls it.
* It changes no other ordering, no piping number, and no climate ratio's piping
  component.
* Reach-wide it is not small, and the direction reverses. A statement about how
  many segments overflow leads is a statement about the rating uncertainty as
  much as about the stage, and should not be quoted without that.
* The production deliverable is unchanged. The arm is a labeled companion, and
  the committed primary curves came out of the regeneration byte-identical.
