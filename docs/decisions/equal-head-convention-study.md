# The equal-head-convention comparison, and where the 0.3·D_bl term comes from

Companion to **ADR-0051** (`0051-crack-resistance-factor-equal-head-convention.md`).
Evidence: `docs/decisions/adr0051-equal-head-convention.json`.
Driver: `scripts/equal_head_convention_study.py`.
Run artifacts: gitignored `results/equal_head_convention/` (regenerable).

Date of the measurement: 2026-08-28.

---

## 1. Provenance of the crack-resistance term, verbatim

Every quote below was read from the PDF text layer in the gitignored
`docs/references/` on 2026-08-28 with PyMuPDF. Page numbers are the **printed**
page of each document; where the PDF page index differs it is given in
parentheses. Nothing here is paraphrased into a number, and nothing that could
not be found is asserted.

### 1.1 Sellmeijer (2011) contains no such term

`sellmeijer_2011.pdf`, 17 pages, text layer intact (31 230 characters). Searched
case-insensitively for `0.3`, `crack`, `blanket`, `cover`, `reduc`,
`critical head`, `head difference`.

- **No hit for `crack` and no hit for `blanket` anywhere in the paper.**
- The paper's head is the gross head across the structure. p. 1141 (PDF p. 4):

  > "In the previous century, an empirical rule relating the hydraulic head
  > across the structure, Hc, to the length of seepage, L, was formulated."

- "cover" appears three times and never as a head loss: p. 1141 (PDF p. 4),
  "Note that the cohesive dike forms a 'cover' over the erosion channel,
  allowing the channel to exist. Without roofing the conceptual model has no
  potential."; p. 1142 (PDF p. 5) on 1970s laboratory tests "by fabricating
  holes through a cover layer on top of a confined layer"; p. 1149 (PDF p. 12)
  on the IJkdijk membrane.
- The only "reduction" in the paper is a measurement correction, p. 1152
  (PDF p. 15):

  > "In test 1, a 5% reduction is assessed and in test 2, a reduction of 10%."

  That is silt sedimentation at the upstream side of two IJkdijk tests, not a
  blanket head loss.

**Conclusion.** The static comparator this engine runs (ADR-0028: `H_c` against
the raw gross head `h_peak − z_toe`) is Sellmeijer's own convention. The
`0.3·D_bl` decrement is not in the 2011 paper in any form.

### 1.2 Pol SIE (2024) adopts it by citation, in Eq. (6)

`pol_sie_2024.pdf`, journal p. 4 (PDF p. 5 of 18), immediately after Eq. (5):

> "The imposed head difference is reduced by a head loss over the blanket
> (vertical pipe) due to resistance of the fluidized sediment (e.g.
> Schweckendiek, Vrouwenvelder, & Calle, 2014; TAW, 1999):
> H = h − h_e − 0.3 D_bl   (6)
> where h is outer water level, h_e polder level at the exit point and D_bl
> polder blanket thickness."

So Eq. (6) is introduced by **citation, not derivation**, and the two sources
cited are, in full from the same paper's reference list (PDF p. 18):

> "Schweckendiek, T., Vrouwenvelder, A. C. W. M., & Calle, E. O. F. (2014).
> Updating piping reliability with field performance observations. Structural
> Safety, 47, 13-23. doi:10.1016/j.strusafe.2013.10.002"

> "TAW. (1999). Technical report on sand boils (piping) (Tech. Rep. No.
> TAW99-26). Rijkswaterstaat."

The **same** pair is cited for the uplift and heave limit states, and those do
**not** carry the crack term. Same page:

> "The limit states for uplift (Zu) and heave (Zh) are given by (e.g.
> Schweckendiek et al., 2014; TAW, 1999):
> Zu(t) = (φ_it(t) − h_e) − D_bl (γ_bl,sat − γ_w)/γ_w   (8)
> Zh(t) = (φ_it(t) − h_e)/D_bl − i_c,h   (9)
> φ_it(t) = h_e + r_e (h(t) − h_e)   (10)"

This is the paper-level confirmation of the engine's ADR-0027/0028 split: the
crack term belongs to Eq. (6) and to nothing else; Eqs. (8)-(10) are
`r_e`-attenuated and crack-free.

Its physical role is stated once more, journal p. 12 (PDF p. 13):

> "Thick blankets also result in a high resistance in the vertical pipe due to
> the 0.3Dbl-reduction in Equation (6); in that way, the erosion process stops
> earlier when the flood level is falling."

### 1.3 Pol (2022) states it without citation, and calls it Dutch practice

`pol_thesis_2022.pdf`, p. 126 (PDF p. 144), §6.2.4:

> "The imposed head difference is reduced by a head loss over the blanket
> (vertical pipe) due to resistance of the fluidized sediment:
> H = h − h_e − 0.3D_bl, where h is outer water level, h_e polder level at the
> exit point and D_bl polder blanket thickness."

**No citation is attached** in the thesis; the SIE 2024 paper added one. The
thesis's own bibliography carries TAW [2004] (`Technisch Rapport
Waterspanningen bij Dijken`) but **no TAW 1999 entry**.

What the status of the rule is, the thesis says plainly in Appendix A
(the Strijenham 1894 failure case), p. 198 (PDF p. 216):

> "From a stationary point of view, the effective head difference which led to
> the failure is given by: H = H_c = (h − h_p) − 0.3D_bl, in which h = water
> level, h_p = polder water level, D_bl = blanket thickness. The 0.3D_bl
> correction for exit hole resistance is used in current levee safety
> assessments in the Netherlands."

Two things follow. First, the rule is characterised as **assessment practice**,
not as a derived or calibrated mechanical result. Second, note that Pol there
applies it to the **static** critical-head comparison `H = H_c` as well.

The thesis also states the effect qualitatively, p. 138 (PDF p. 156):

> "Thick blankets also result in a high resistance in the vertical pipe (heave,
> 0.3D_bl-reduction), therefore the erosion process stops earlier when the flood
> level is falling."

### 1.4 The cited source puts the same term on the static limit state

`Schweckendiek (2014) - On Reducing Piping Uncertainties`, p. 26 (PDF p. 40):

> "Zp = gp(X) = mpHc − H = mpHc − (h − hp − 0.3d)   (3.14)"

with `d` defined in the same list as "thickness of the blanket layer", and the
corresponding critical water level

> "hc,p = mpHc + hp + 0.3d   (3.15)"

followed by

> "This limit state (Eqs. 3.14-3.16) is supposed to be used for safety
> assessments in the Netherlands in the near future and will be employed in the
> remainder of this thesis."

No derivation of the 0.3 coefficient is given there either; searching the whole
285-page document for `0.3d` returns only these two equations.

### 1.5 What could not be verified

`TAW (1999), Technical report on sand boils (piping), TAW99-26` — the report
Pol cites as the rule's origin — is **not held in `docs/references/`**, so its
own text has not been read here. Everything above about the rule's origin is
therefore what the three *available* sources say about it; the primary document
remains unverified. The repository holds `TAW 2004.pdf` (a different report:
`Technisch Rapport Waterspanningen bij Dijken`, the blanket-theory source for
M4), which is not the cited one.

### 1.6 Summary of the provenance finding

| claim | status |
|---|---|
| The `0.3·D_bl` term is in Sellmeijer (2011) | **False.** No crack, blanket or cover head loss appears anywhere in that paper. |
| It is a Dutch assessment-rule convention | **Supported**, in Pol's own words: "used in current levee safety assessments in the Netherlands" (Pol 2022, p. 198). |
| Pol derives or calibrates it | **No.** SIE 2024 introduces it by citation; the 2022 thesis states it with no citation at all. |
| Dutch practice applies it to the static Sellmeijer limit state too | **Yes.** Schweckendiek (2014) Eq. (3.14), p. 26, and Pol (2022) p. 198. |
| The uplift/heave limit states carry it | **No.** Pol SIE 2024 Eqs. (8)-(10) are crack-free and `r_e`-attenuated, which is exactly the engine's ADR-0027/0028 split. |
| The primary source (TAW 1999) was read here | **No** — not held in the repository. |

The engine's production configuration is therefore each model as its author
intended, and the surviving head-convention difference between the branches is
exactly the term that neither author of the *static* model wrote. That is the
comparison ADR-0051 opens.

---

## 2. What was measured, and how

`crack_resistance_factor = 0.0` (ADR-0051) removes the Eq. (6) term from the
transient erosion driver, so `H_erosion = h(t) − z_toe` is bit-for-bit the head
the static comparator uses. Every other input is held: same config, same seed,
same theta, same L draw, same grid, same hydrographs, so the arm is coupled to
the production baseline by common random numbers row for row.

- **N = 1e5**, all four matrix sections, the full production conditioning grid.
  A gate run with the knob explicitly `None` is compared against the persisted
  production sweep, then the gross-head arm is run.
- **N = 1e6**, KP 57.4 and KP 62.0, at the design anchor and the neighbouring
  levels the existing 1e6 campaign carries, evaluated through `evaluate_batch`
  on the same seed recipe the ADR-0040 ladder used, and gated on reproducing
  that ladder's counts exactly.
- **Bulk reading skipped**, on the ADR-0040 §4 precedent: the GSA found the
  bulk-d70 space largely degenerate (`P_f ≈ 0`) at exactly the design stages
  where the head convention matters, so a bulk arm would mostly decompose
  zeros. Stated, not silent.
- **Historical scenario only**, on the ADR-0023 shape invariance.

Metrics, per campaign-plan decision D1:

- `B = P_static / P_transient` at one level, with the ADR-0040 paired-bootstrap
  `bias_ratio` estimator and its pre-registered R1 (at least 30 transient rows)
  and R2 (interval width factor at most 2) criteria, **imported unchanged** from
  `scripts/hwl_bias_resolution.py`.
- `β = −Φ⁻¹(P_f)` per branch, interval by the monotone image of the exact
  Clopper-Pearson interval on the raw count. No new statistical machinery.
- `Δβ = β_transient − β_static`, paired: one row resample per replicate feeds
  both branches, 10 000 replicates, percentile method. Reported only where both
  branches carry at least 10 failing rows.

A second equal-convention reading is carried alongside and was **not re-run**:
Stage 6.6's comparator **C1** is the crack-reduced *static* comparator, so
`C1 / C4b` is the both-sides-reduced comparison, which is what Dutch practice
actually does (§1.4). It exists at KP 57.4 and KP 62.0 only; Stage 6.6 never ran
at the drained sections, and that column is `n/d` there rather than omitted.

Driver: `scripts/equal_head_convention_study.py` (`n1e5`, `n1e6`, `dtcheck`,
`report`). Recorded runtime **2462 s (41.0 min)** at N = 1e5 for the four
sections (gate sweep, gross-head sweep and the two 64-day sustained-peak holds
each; KP 57.4 296.6 s, KP 58.8 664.1 s, KP 60.0 613.9 s, KP 62.0 650.5 s, plus a
237 s first pass at KP 57.4 whose sweeps the recorded pass reused) and
**966 s (16.1 min)** at N = 1e6 for the two sections and both arms (KP 62.0
603.1 s, KP 57.4 362.9 s). The §5 timestep diagnosis adds about 3 min.

---

## 3. Consistency gates

| section | N | (i) static bit-identical | (ii) gross-not-static rows | (ii) production-not-gross rows | (iii) sustained-peak closed form |
|---|---|---|---|---|---|
| KP 57.4 | 1e5 | yes, whole matrix | 0 | 0 | exact at 39.25 m and 43.25 m |
| KP 58.8 | 1e5 | yes, whole matrix | 0 | 0 | 1 row of 100 000 at 41.00 m (see §5); exact at 45.00 m |
| KP 60.0 | 1e5 | yes, whole matrix | 0 | 0 | exact at 42.75 m and 46.75 m |
| KP 62.0 | 1e5 | yes, whole matrix | 0 | 0 | exact at 46.50 m and 56.50 m |
| KP 57.4 | 1e6 | ladder C0 reproduced at all 5 levels | 10 | 0 | not run (1e5 only) |
| KP 62.0 | 1e6 | ladder C0 reproduced at all 5 levels | 0 | 0 | not run (1e5 only) |

Gate (i) is stronger than it looks. The N = 1e5 comparison is on the **whole**
failure matrix, not the column means, against the persisted production sweeps,
first with the knob off and then again with it on. The N = 1e6 comparison
reproduces the persisted ADR-0040 ladder's C0 **and** C4b counts at every level,
including the two counts the campaign brief named in advance: **1696 of 1e6 at
KP 62.0, 46.39 m** and **1132 of 1e6 at KP 57.4, 39.21 m**. Both reproduced
exactly, which is what licenses pairing the new gross-head transient against the
existing static population.

The nesting direction was also checked the other way: the production transient
set nests inside the gross-head one at every level of every section (removing a
head loss can only help a pipe), with **zero** exceptions anywhere.

---

## 4. Results

### 4.1 Design-level anchors

`B_prod` and `Δβ_prod` are the as-published comparison (the deliverable);
`B_eq` and `Δβ_eq` are the gross-vs-gross equal-convention comparison;
`B_C1/C4b` is the reduced-vs-reduced corroboration where Stage 6.6 provides it.

| section | N | stage [m MSL] | k_static | k_trans prod | k_trans gross | B_prod | **B_eq** | B_eq 95 % CI | B_C1/C4b | Δβ_prod | **Δβ_eq** | Δβ_eq 95 % CI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KP 62.0 | 1e6 | 46.39 | 1696 | 63 | 231 | 26.9 | **7.34** | [6.52, 8.30] | 8.03 | 0.904 | **0.572** | [0.540, 0.605] |
| KP 57.4 | 1e6 | 39.21 | 1132 | 2 | 49 | 566 | **23.1** | [18.0, 31.3] | 12.0 | 1.558 | **0.842** | [0.780, 0.915] |
| KP 58.8 | 1e5 | 41.00 | 72 206 | 26 273 | 38 601 | 2.75 | **1.87** | [1.86, 1.88] | n/d | 1.224 | **0.879** | [0.871, 0.887] |
| KP 60.0 | 1e5 | 42.75 | 91 650 | 31 427 | 43 366 | 2.92 | **2.11** | [2.10, 2.13] | n/d | 1.866 | **1.549** | [1.537, 1.561] |

Resolution under the pre-registered R1 and R2 criteria: `B_eq` is **resolved** at
all four anchors except KP 57.4 at N = 1e5 (9 rows). Note the direction of that
result: at KP 57.4 the equal-convention comparison is resolved at N = 1e6 on 49
transient rows, where the as-published comparison is **not** (2 rows). Removing
the contested term is what brings the design-level anchor into the pre-registered
resolution criteria at the section where the as-published bias never reached
them.

The N = 1e5 anchors are the nearest grid level to the design HWL: 39.25 m at
KP 57.4 (HWL 39.21 m), 41.00 m at KP 58.8 (HWL 41.03 m), 42.75 m at KP 60.0
(exactly on the grid) and 46.50 m at KP 62.0 (HWL 46.39 m). The two 1e6 sections
carry the exact HWL because the ADR-0040 ladder inserted it.

### 4.2 The headline reading

At the design level the head convention accounts for most, but nowhere near all,
of the as-published gap:

- **KP 62.0**: 26.9 collapses to **7.34** [6.52, 8.30]. In β terms 0.904 becomes
  **0.572** [0.540, 0.605]: the equal-convention comparison retains **63 %** of
  the as-published Δβ.
- **KP 57.4**: 566 collapses to **23.1** [18.0, 31.3]; Δβ 1.558 becomes **0.842**
  [0.780, 0.915], retaining **54 %**.
- **KP 58.8**: 2.75 to **1.87**; Δβ 1.224 to **0.879**, retaining **72 %**.
- **KP 60.0**: 2.92 to **2.11**; Δβ 1.866 to **1.549**, retaining **83 %**.

So the ratio-space collapse is dramatic at the tail sections and modest at the
drained ones, while in β terms the surviving fraction is large everywhere and
*largest* at the drained sections. That is the campaign plan §1.3 ordering
reversal reappearing inside the equal-convention experiment: it is not an
artefact of the as-published convention.

### 4.3 The two equal-convention readings bracket each other

There is no unique "equal convention": the two models can be equalised on the
gross head (this study) or on the crack-reduced head (Stage 6.6's C1 against
C4b). They do not give the same number, because the two branches have different
head sensitivities, so a common decrement is not a common-mode shift.

| section | N | stage | B_eq gross-vs-gross | B reduced-vs-reduced |
|---|---|---|---|---|
| KP 62.0 | 1e6 | 46.39 | 7.34 | 8.03 |
| KP 62.0 | 1e6 | 46.50 | 6.49 | 8.02 |
| KP 62.0 | 1e6 | 47.00 | 5.75 | 6.18 |
| KP 62.0 | 1e6 | 48.00 | 3.41 | 3.70 |
| KP 62.0 | 1e6 | 50.50 | 1.37 | 1.42 |
| KP 57.4 | 1e6 | 39.21 | 23.1 | 12.0 (2 rows; unresolved) |
| KP 57.4 | 1e6 | 39.25 | 18.2 | 4.90 (10 rows) |
| KP 57.4 | 1e6 | 39.50 | 5.76 | 4.58 |
| KP 57.4 | 1e6 | 40.00 | 2.59 | 2.92 |
| KP 57.4 | 1e6 | 43.25 | 1.03 | 1.04 |

At KP 62.0 the two readings agree to within 10 to 24 % at every level, so the
equal-convention answer there is robust to which head the models are equalised
on: **the design-level equal-convention factor is 7 to 8**. At KP 57.4 they
diverge in the deep tail, where the reduced-vs-reduced reading rests on 2 and 10
rows and is not resolvable; at the first level where both are adequately counted
(39.50 m, 521 and 3861 rows) they are 5.76 against 4.58, 26 % apart. The honest
statement at KP 57.4 is therefore a **band of roughly 5 to 23** at and just above
the design level, not a point.

### 4.4 Per-level tables

All-zero levels are dropped. `flips` is the count of gross-head transient
failures with no static failure on the same row, i.e. forward-Euler barrier
jumps (§5). The complete tables, including the Clopper-Pearson intervals on every
count and the reduced-vs-reduced comparison at every ladder level, are in
`docs/decisions/adr0051-equal-head-convention.json`.

**KP 57.4, N = 1e6** (the design anchor and its neighbours)

| stage | k_stat | k_tr prod | k_tr gross | k_C1 | B_prod | B_eq | B_eq 95 % CI | B_C1/C4b | Δβ_prod | Δβ_eq | Δβ_eq 95 % CI | flips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 39.21 | 1132 | 2 | 49 | 24 | 566 | 23.1 | [18.0, 31.3] | 12.0 | 1.558 | 0.842 | [0.780, 0.915] | 1 |
| 39.25 | 1943 | 10 | 107 | 49 | 194 | 18.2 | [15.3, 22.2] | 4.90 | 1.378 | 0.815 | [0.770, 0.865] | 1 |
| 39.50 | 22 249 | 521 | 3861 | 2388 | 42.7 | 5.76 | [5.60, 5.93] | 4.58 | 1.270 | 0.655 | [0.645, 0.664] | 5 |
| 40.00 | 246 683 | 35 782 | 95 188 | 104 642 | 6.89 | 2.59 | [2.58, 2.60] | 2.92 | 1.117 | 0.625 | [0.622, 0.627] | 3 |
| 43.25 | 999 692 | 963 940 | 974 451 | 999 418 | 1.04 | 1.03 | [1.03, 1.03] | 1.04 | 1.626 | 1.474 | [1.444, 1.505] | 0 |

**KP 62.0, N = 1e6**

| stage | k_stat | k_tr prod | k_tr gross | k_C1 | B_prod | B_eq | B_eq 95 % CI | B_C1/C4b | Δβ_prod | Δβ_eq | Δβ_eq 95 % CI | flips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 46.39 | 1696 | 63 | 231 | 506 | 26.9 | 7.34 | [6.52, 8.30] | 8.03 | 0.904 | 0.572 | [0.540, 0.605] | 0 |
| 46.50 | 3793 | 176 | 584 | 1411 | 21.6 | 6.49 | [6.05, 7.02] | 8.02 | 0.904 | 0.577 | [0.556, 0.599] | 0 |
| 47.00 | 52 152 | 4890 | 9077 | 30 237 | 10.7 | 5.75 | [5.64, 5.85] | 6.18 | 0.959 | 0.738 | [0.731, 0.745] | 0 |
| 48.00 | 443 698 | 102 004 | 130 144 | 377 685 | 4.35 | 3.41 | [3.39, 3.43] | 3.70 | 1.129 | 0.984 | [0.981, 0.987] | 0 |
| 50.50 | 984 183 | 689 555 | 715 903 | 979 962 | 1.43 | 1.37 | [1.37, 1.38] | 1.42 | 1.654 | 1.578 | [1.572, 1.585] | 0 |

**KP 58.8, N = 1e5** (drained section; no Stage 6.6 ladder, so no C1 column)

| stage | k_stat | k_tr prod | k_tr gross | B_prod | B_eq | B_eq 95 % CI | Δβ_prod | Δβ_eq | Δβ_eq 95 % CI |
|---|---|---|---|---|---|---|---|---|---|
| 39.50 | 211 | 0 | 5 | inf | 42.2 | [21.5, 196] | inf | 1.029 | n/d |
| 39.75 | 2105 | 42 | 266 | 50.1 | 7.91 | [7.11, 8.91] | 1.307 | 0.754 | [0.719, 0.792] |
| 40.00 | 9008 | 477 | 2076 | 18.9 | 4.34 | [4.18, 4.51] | 1.252 | 0.698 | [0.682, 0.714] |
| 40.25 | 22 300 | 2518 | 7126 | 8.86 | 3.13 | [3.07, 3.19] | 1.195 | 0.704 | [0.694, 0.715] |
| 40.50 | 39 963 | 7470 | 15 630 | 5.35 | 2.56 | [2.53, 2.59] | 1.187 | 0.755 | [0.747, 0.764] |
| 40.75 | 57 634 | 15 596 | 26 683 | 3.70 | 2.16 | [2.14, 2.18] | 1.204 | 0.815 | [0.807, 0.823] |
| **41.00** | 72 206 | 26 273 | 38 601 | **2.75** | **1.87** | [1.86, 1.88] | **1.224** | **0.879** | [0.871, 0.887] |
| 41.50 | 89 998 | 49 150 | 60 401 | 1.83 | 1.49 | [1.48, 1.50] | 1.303 | 1.018 | [1.007, 1.028] |
| 42.00 | 96 918 | 68 133 | 76 177 | 1.42 | 1.27 | [1.27, 1.28] | 1.397 | 1.157 | [1.142, 1.172] |
| 43.00 | 99 773 | 89 198 | 92 152 | 1.12 | 1.08 | [1.08, 1.08] | 1.601 | 1.423 | [1.383, 1.466] |
| 44.00 | 99 981 | 96 442 | 97 458 | 1.04 | 1.03 | [1.02, 1.03] | 1.749 | 1.601 | [1.497, 1.744] |
| 45.00 | 100 000 | 98 779 | 99 117 | 1.01 | 1.01 | [1.01, 1.01] | inf | inf | n/d |

**KP 60.0, N = 1e5** (drained section)

| stage | k_stat | k_tr prod | k_tr gross | B_prod | B_eq | B_eq 95 % CI | Δβ_prod | Δβ_eq | Δβ_eq 95 % CI |
|---|---|---|---|---|---|---|---|---|---|
| 41.00 | 219 | 0 | 2 | inf | 110 | [41.2, 240] | inf | 1.258 | n/d |
| 41.25 | 2625 | 8 | 86 | 328 | 30.5 | [25.1, 38.1] | 1.836 | 1.196 | [1.138, 1.261] |
| 41.50 | 12 206 | 204 | 988 | 59.8 | 12.4 | [11.7, 13.1] | 1.707 | 1.166 | [1.144, 1.189] |
| 41.75 | 30 278 | 1362 | 4337 | 22.2 | 6.98 | [6.79, 7.18] | 1.692 | 1.196 | [1.183, 1.210] |
| 42.00 | 51 787 | 4870 | 11 169 | 10.6 | 4.64 | [4.56, 4.72] | 1.702 | 1.262 | [1.252, 1.273] |
| 42.25 | 70 403 | 11 408 | 20 768 | 6.17 | 3.39 | [3.35, 3.43] | 1.741 | 1.351 | [1.341, 1.360] |
| 42.50 | 83 683 | 20 679 | 31 932 | 4.05 | 2.62 | [2.60, 2.64] | 1.799 | 1.451 | [1.441, 1.462] |
| **42.75** | 91 650 | 31 427 | 43 366 | **2.92** | **2.11** | [2.10, 2.13] | **1.866** | **1.549** | [1.537, 1.561] |
| 43.25 | 98 173 | 52 893 | 63 464 | 1.86 | 1.55 | [1.54, 1.55] | 2.018 | 1.747 | [1.728, 1.766] |
| 44.00 | 99 837 | 76 611 | 82 797 | 1.30 | 1.21 | [1.20, 1.21] | 2.216 | 1.996 | [1.950, 2.046] |
| 45.00 | 99 997 | 91 553 | 93 780 | 1.09 | 1.07 | [1.06, 1.07] | 2.637 | 2.476 | [2.273, 2.734] |
| 46.75 | 100 000 | 98 433 | 98 865 | 1.02 | 1.01 | [1.01, 1.01] | inf | inf | n/d |

The N = 1e5 tables for KP 57.4 and KP 62.0 are in the evidence JSON; their
design-level cells are `B_eq` 23.0 [13.4, 54.0] at KP 57.4 39.25 m (9 transient
rows, unresolved, which is why the 1e6 run exists) and 6.55 [5.27, 8.47] at
KP 62.0 46.50 m, both consistent with the 1e6 values above.

**KP 62.0 attainability caveat.** Levels above 50.5 m in the KP 62.0 grid are the
ADR-0024 hypothetical fit stabiliser and must never be presented as attainable;
`attainable_max_m` is 50.5 m. The rows above it in the evidence JSON exist for
curve fitting only.

### 4.5 Δβ does not decay, and the sections reorder

`B_eq` decays monotonically toward 1 as the stage rises, exactly as `B_prod`
does. `Δβ_eq` does not: it is flat to mildly increasing with stage at every
section.

| section | N | Δβ_eq minimum over the grid | Δβ_eq at the top of the (attainable) grid |
|---|---|---|---|
| KP 57.4 | 1e5 | 0.61 at 39.75 m | 1.47 at 43.25 m |
| KP 58.8 | 1e5 | 0.70 at 40.00 m | 1.99 at 44.75 m |
| KP 60.0 | 1e5 | 1.17 at 41.25 m | 2.48 at 45.50 m |
| KP 62.0 | 1e5 | 0.58 at 46.50 m | 1.58 at 50.50 m (attainable max) |

This is the plan's §1.3 point, now measured on the equal-convention comparison
rather than inferred from the as-published one: the "the two models converge
toward parity at extreme overload" statement is true of `P_f` and false of
`P_survival`. At KP 62.0's attainable top, `B_eq` is 1.37 while static survival
is 1.6 % against transient survival 28.4 %.

---

## 5. The one deviation, run down rather than smoothed

Gate (iii) failed in exactly one cell of the whole study: at KP 58.8, 41.00 m,
under the 64-day sustained hold, **1 row of 100 000** breached while the closed
form says it must stall. The direction is the diagnostic one: `observed and not
analytic`, i.e. the finite-Δt integrator over-predicts.

The discriminating experiment is the ADR-0039 timestep ladder on that row alone
(`python scripts/equal_head_convention_study.py dtcheck`;
`results/equal_head_convention/stage_dtcheck.json`):

| Δt [s] | l_e [m] | breach |
|---|---|---|
| 225.0 | 35.1714 | yes (= L) |
| 112.5 | 7.82809 | no |
| 56.25 | 7.80256 | no |
| 28.125 | 7.80192 | no |

Row 22246: `L = 35.171 m`, `H_c = 2.50304 m`, `l_c = 7.811 m`, gross head
`2.50000 m`. The head sits **3.04 mm** (0.12 %) *below* the barrier, and the row
is in the most erosive corner of the prior (`C_e = 0.876` against a prior mean of
0.055; `k_aq = 1.32e-3 m/s`). At the production Δt of 225 s a single Euler step
clears the `H_eq` maximum at `l_c`; halve the step and the trajectory converges
to `l_e = 7.80 m`, i.e. it stalls at `l_c` exactly as the closed form requires.

This is the ADR-0030 barrier-jump signature and the ADR-0039 rider, and it is a
property of the **artificial 64-day hold**, not of the deliverable: under the
real hydrographs the nesting counts are **0 at every level of all four sections**
at N = 1e5. It does appear under real loading at N = 1e6 at KP 57.4 (10 rows
across 5 levels, §3), where the sample is ten times larger and the gross head is
0.3·D_bl higher than the production one: 1 row of the 49 gross-head failures at
the design anchor, 1 of 107, 5 of 3861 and 3 of 95 188. Excluding the single flip
at 39.21 m would move `B_eq` from 23.10 to 23.58, well inside its [18.0, 31.3]
interval, so the design-level number is not carried by it. The flips are recorded
per level in the tables and in the evidence JSON; they are a stated caveat on the
KP 57.4 1e6 counts, not a correction applied to them.

---

## 6. Against the pre-registered expectations (campaign plan §4)

| # | expectation | verdict |
|---|---|---|
| E1 | Static branch bit-identical to production at every level | **Held.** Whole-matrix identity at all four sections at N = 1e5, with the knob off and again with it on; ladder C0 reproduced at all 10 levels at N = 1e6, including the two named counts 1696 and 1132. |
| E2 | Gross-head transient nests inside the static set up to Euler-flip rows | **Held.** Zero exceptions at N = 1e5 anywhere. 10 flip rows at KP 57.4 N = 1e6, counted and reported (§5); zero at KP 62.0 N = 1e6. |
| E3a | `B_eq` at KP 62.0 design in ~4 to 12 | **Held.** 7.34 [6.52, 8.30], with the reduced-vs-reduced reading at 8.03. |
| E3b | `B_eq` at the drained sections in ~1.5 to 3 | **Held.** 1.87 at KP 58.8, 2.11 at KP 60.0. |
| E3c | `Δβ_eq ≈ 0.2 to 0.7` | **Failed at three of four sections.** 0.572 at KP 62.0 (inside), 0.842 at KP 57.4, 0.879 at KP 58.8, 1.549 at KP 60.0. See below. |
| E4 | Sustained-peak limit of the gross-head transient is exactly `C0 ∧ gate` | **Held, with a Δt rider.** Exact at 7 of the 8 checked cells; the eighth is 1 row of 100 000 that vanishes at Δt/2 (§5). |
| E5 | The equal-convention gap is more canonical-event-exposed than the production gap | **Not measured here**, stated as a conditionality (§7). |

### Why E3c failed, and why it is not a correction to the numbers

E3c was derived from E3a and E3b by an implicit ratio-to-β conversion, and that
conversion is stage-dependent. `Δβ` is not a function of `B` alone: it depends on
where on the normal scale the two probabilities sit. A factor of 2 between two
probabilities of order 1e-3 is a small β step; the same factor between
probabilities of order 0.4 is a large one, because the normal density is at its
maximum there. At KP 60.0's design level `P_static = 0.917` and
`P_trans,gross = 0.434`, so `β_static = −1.383` and `β_trans = +0.167`: a ratio of
2.11 and a `Δβ` of 1.549 are the *same* measurement.

The pre-registration's ratio half is therefore confirmed at every section it
covers, and its β half was arithmetically inconsistent with it from the start.
This is the campaign plan's own §1.3 warning ("the section ordering reverses";
"Δβ does not decay") applied to the plan's own §4, and it strengthens rather than
weakens the case for leading with Δβ: the two metrics genuinely rank the sections
differently, and E3c is a worked example of reading one off the other and getting
it wrong.

---

## 7. Scope and conditionality

- **Matrix reading only.** Bulk is skipped on the ADR-0040 §4 precedent (§2).
- **Historical scenario only** (ADR-0023 shape invariance).
- The equal-convention numbers inherit **every** conditionality the as-published
  bias carries: the seepage length L (ADR-0047), the aquifer conductivity k_aq
  (ADR-0048, the largest and the one that amplifies), the canonical event
  (2026-08-10 study) and the critical pipe length l_c (ADR-0049). None of these
  was re-measured on the equal-convention arm.
- **E5, stated not measured.** The as-published gap has a head-convention floor:
  even a hydrograph that dwells arbitrarily long at the peak cannot make the
  transient branch reach the static one while the transient head is 0.3·D_bl
  lower. The equal-convention gap has no such floor, so it should be *more*
  exposed to the canonical-event choice, which sets the dwell time. The direction
  is given by the existing alternate-member measurement (`HPB_m067_1978`, which
  roughly triples the as-published ratio); it was not re-run here, and no number
  should be quoted for it from this study.
- The `Δβ_eq` intervals are **statistical only**, on a fixed prior. Like every
  other interval in this repository they are dwarfed by the k_aq bracket, and
  that scope belongs in the same sentence as the number.

---

## 8. Artifacts

| what | where |
|---|---|
| Decision and pre-registration | `docs/decisions/0051-crack-resistance-factor-equal-head-convention.md` |
| This note | `docs/decisions/equal-head-convention-study.md` |
| Evidence JSON (all per-level tables, both N, both readings, the Δt diagnosis) | `docs/decisions/adr0051-equal-head-convention.json` |
| Driver | `scripts/equal_head_convention_study.py` |
| Tests | `tests/test_crack_resistance_factor.py` |
| N = 1e5 gate and arm sweeps, N = 1e6 raw payloads, stage JSONs | gitignored `results/equal_head_convention/` (regenerable by re-running the driver) |
| The N = 1e6 static and C1 populations paired against | gitignored `results/hwl_bias_resolution/ladder_kp{57_4,62_0}_n1000000.h5` |
