# ADR-0054: The matrix d70 prior is taken from the aquifer's own matrix gradation

Date: 2026-09-24

## Status
Accepted (owner decision, Green Light item 4, 2026-09-24). Changes a production
prior mean at all four confined sections and the matrix d70 clip ceiling.
Amends provenance section 3.3 and the matrix half of the ADR-0012 record; the
two-population coupling itself is unchanged. The bulk co-primary is unchanged.

---

## Context

The matrix-reading d70 means (0.70 / 0.53 / 0.26 / 0.70 mm at KP 57.4 / 58.8 /
60.0 / 62.0) were extrapolated (about 1.1 x d60) from three shallow specimens
described as "sand-dominated specimens at the blanket-aquifer transition", with
KP 62.0 (and the excluded KP 63.4) taking KP 57.4's value by analogy.

Reading OYO (1999) report Tables 4-3-1 and 4-3-2 (report pp. 52 to 53), which
compile every laboratory result by layer, established that all three source
specimens are **levee embankment fill** (layers Bc, Bs, Bs), sampled 0.50 to
1.00 m into a fill column 3.5 to 4.4 m deep, 3 to 4 m above the aquifer top.
Table 4-3-2 holds 28 gradations of the aquifer itself (layer Ag) at the four
sections, 6 to 8 per section, which the model had never used. Evidence:
`bimodal-foundation-d70-study.md` / `.json`, driver
`scripts/bimodal_foundation_d70_study.py`, data
`data/processed/oyo_1999_gradations_by_layer.csv`.

The matrix d70 derived from those specimens (the material finer than 2 mm,
renormalised; the pre-registered primary definition) has section medians of
0.90 / 0.65 / 0.74 / 0.75 mm. By the pre-registered rule (agreement within one
sigma_ln = 0.294 of the adopted prior) KP 57.4, 58.8 and 62.0 were reproduced
and KP 60.0 was not: its 0.26 mm was 2.9 times finer than its own aquifer's
matrix. In-memory variants (N = 1e5, production seed, baselines bit-identical
to the persisted sweeps) put the consequence at +0.12 / +0.12 / +0.78 / +0.06 m
on the fragility curves and moved KP 60.0's design-level delta-beta from 1.87
to 1.22.

## Decision

1. **The matrix d70 prior mean at each confined section is the median matrix
   d70 of that section's own Ag specimens**, matrix = aquifer material finer
   than 2 mm: KP 57.4 **0.90 mm** (7 specimens), KP 58.8 **0.65 mm** (7),
   KP 60.0 **0.74 mm** (6), KP 62.0 **0.75 mm** (8). The KP 62.0 transfer from
   KP 57.4 is retired: every section now has its own basis. KP 63.4 (no config,
   no Ag specimen in the per-layer tables) carries the four-section pooled
   median 0.77 mm, inert.
2. **The matrix d70 clip ceiling is raised from 1.0 to 2.0 mm**, the ceiling
   the matrix definition itself implies. Under a 1 mm clip up to 31 per cent
   of the re-based KP 57.4 draws would sit on the cap, silently narrowing the
   distribution below the spread the data support. The 50 um floor stays.
3. **The CoV stays 0.30**, now with a measured basis: the pooled within-section
   sigma_ln of the 28 aquifer matrix d70 values is 0.293 (equivalent CoV
   0.300). It represents place-to-place variability of the matrix the pipe tip
   meets, not the matrix-versus-framework contrast, which remains carried by
   the co-primary bulk reading.
4. **The bulk co-primary is unchanged** (owner decision). Its KP 60.0 value
   (1.3 mm) is recorded as extrapolated from the one sand-rich Ag specimen at
   that section, so it is not a gravel-framework value there.

## Alternatives Considered

### Keep the fill-specimen means and carry the aquifer means as a sensitivity
No re-run; but a production prior known to rest on the wrong stratum, with the
largest resolved delta-beta in the thesis resting on it. Declined by the owner.

### Re-base KP 60.0 only
The same cascade for the one section that failed the rule, leaving three means
on fill specimens that happen to agree. Declined: one rule for all four
sections, and no transfer.

### The sand-only matrix (0.075 to 2 mm) or the finer-than-4.75 mm material
Pre-registered as alternatives. Sand-only medians are 17 to 26 per cent
coarser (0.80 to 1.05 mm), the 4.75 mm definition about twice as coarse. Both
are less conservative; the finer-than-2 mm matrix keeps the fines, which a
matrix-controlled pipe tip does not armour against, and uses the JGS
sand-gravel boundary that the tabulated fractions resolve exactly.

## Rationale

The matrix reading asserts that the eroding fraction at the pipe tip is the
aquifer's sand matrix. Its mean must therefore describe the aquifer's matrix.
The per-layer tables make that possible at every section, with 6 to 8
specimens instead of one borrowed specimen, and the between-section
differences are not significant (ANOVA p = 0.31), so the four medians are
mutually consistent. The ln d70 values pass a normality test (Shapiro-Wilk
p = 0.23), supporting the lognormal family.

## Consequences

- `data/processed/tokachi_bep_inputs.csv` `d70_m` and
  `scripts/generate_configs.py` `D70_BOUNDS["matrix"]` changed; the four matrix
  configs regenerated (bulk configs byte-identical); `tests/test_configs.py`
  pins the new ceiling.
- Every matrix-reading artifact is superseded: the four matrix sweeps, the
  Phase 2 matrix posteriors and their variants, Stage 6.6, the N = 1e6 ladders,
  the Phase 3 campaign and every companion study. The live store was preserved
  first in `results/superseded_d70rebase_20260924T163630/`. Bulk artifacts are
  unaffected.
- All four matrix means now exceed Sellmeijer's validated 0.430 mm limit (by
  51 to 109 per cent); none lies inside it.
- Every thesis number on the matrix reading is re-derived.

## References
- OYO (1999), report Tables 4-3-1 and 4-3-2 (pp. 52 to 53), Figure 4-3-1 soil
  logs, sheet 4 per section.
- ADR-0012 (two-population coupling; amended 2026-09-24).
- Sellmeijer (2011) validated range.
