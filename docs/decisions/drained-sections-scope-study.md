# The as-if-undrained deliverable at KP 58.8 and KP 60.0: what it represents, why it is not the present-day levee, and the measured-berm companion

Study of record for Green Light item 3 (2026-09-24). No production default,
config, CSV cell, persisted sweep or published production number changed.

Evidence record: `drained-sections-scope-study.json`. Driver:
`scripts/drained_sections_scope_study.py` (post-processing only). Tests:
`tests/test_drained_sections_scope.py`. Builds on ADR-0050 and its companion
`adr0050-drained-configuration-bracket.md`, whose persisted arms it reads.

---

## 1. The question, and what the problem actually was

The supervisors asked, at the Green Light meeting, that the undrained treatment
of KP 58.8 and KP 60.0 be made more explicit, and that it be made unmistakable
that the results as they stand do not describe the present-day cross-sections.
In the meeting they also asked why the drains were not simply added to the
model instead of evaluating the 1998 configuration.

Three findings, in order of weight.

1. **The scope statement exists and is widespread; its defence did not.** The
   as-if-undrained reading is stated in about 25 places (Summary, the Chapter 1
   scope register and technical scope, Chapter 3, the Chapter 6 and 7
   conditions registers, figure and table captions, Chapter 8, Chapter 9, two
   appendices). What the thesis never said is *why* the present-day structure
   is not the modelled object, on the merits. It said no as-built record exists,
   which answers "why not a drain model" only for a reader who already knows
   what a drain model would need.
2. **Four claim sites carry a KP 58.8/60.0 number into a conclusion with no
   scope attached** (section 2), and one Chapter 1 sentence misdescribes the
   works (it gives KP 58.8 and KP 60.0 toe drains only; they received berms and
   drains).
3. **Part of the present-day configuration was already computed and not
   presented as such.** ADR-0050's measured-berm arm is the one reading of the
   present-day geometry that rests on measurement, and it was carried through
   the survival update and the annualisation, at the corrected gauge node, a
   month ago. It sat in Chapter 8 and an appendix as a bracket end, not beside
   the numbers it qualifies. Its reliability-index consequence for the first
   sub-question had never been computed (section 6.1).

"The results do not apply to the current cross-sections" is right for
sub-questions 3 and 4 and the section ranking, only partly right for
sub-question 2, and **wrong in the direction that matters for sub-question 1**:
the index separation of the two criteria is almost unchanged by the measured
berm and only grows with credited drainage (section 6.1).

## 2. Explicitness audit

Every thesis passage that states or implies something about KP 58.8 and KP 60.0,
grouped. "Scoped" means a reader cannot take it as a present-day statement.

| Site | Content | Verdict before this study |
|---|---|---|
| Summary ¶2 | the two sections "evaluated as undrained, representing the foundation hazard" | scoped, but never says "not the present-day structure" |
| Summary ¶3 | "The two drained sections give Δβ = 1.22 and 1.87" | **mislabel risk**: reads as a drained-configuration result |
| Summary ¶5 | 5.51 / 3.24 % rejection, "as-if-undrained updates" | scoped |
| Summary ¶6 | piping 81 to 100 % "at all four segments"; three ordering conditions listed | **unscoped**: drainage is a fourth ordering condition (share at KP 58.8 falls to 0.009 at the strongest arm) |
| Summary ¶7 | KP 58.8 largest absolute and smallest relative increase "on the as-if-undrained reading" | scoped |
| Ch1 scope register, technical scope | as-if-undrained, "remains the deliverable" | scoped; **the technical scope omits the berms at KP 58.8/60.0** |
| Ch3 §1998 record, §remediation | foundation hazard of the unremediated configuration; different configuration from the 2008 classification | scoped; no merits-based defence |
| Ch6 conditions register, Table 6.x captions, §design-level, §2016 update | as-if-undrained throughout | scoped; one mixed estimand (below) |
| Ch6 compatibility paragraph | "34 per cent static ... against 5.4 per cent transient" under the berm | **defect**: 5.4 % is the canonical-shape grid value at 40.75 m, the adjacent 5.5/3.2 % are replay rejections; the berm replay gives **1.5 %** |
| Ch7 conditions register, table/figure captions | as-if-undrained | scoped |
| Ch7 longitudinal view | "KP 58.8 has the largest computed segment probability in both climates" | **unscoped** in the sentence |
| Ch7 §ratios | "smallest climate ratio ... by a factor of four over the next section historically and three under warming ... already high on its curve" | **unscoped**: the factor of four is to KP 60.0, itself as-if-undrained; on the berm reading the margin is to KP 62.0 |
| Ch8 §What the model represents, register | the bracket; "protected-configuration scenarios, not bounds" | scoped; the survival-likelihood row says "Quantified: no" though the berm replay quantifies its rejection |
| Ch9 RQ3 conclusion | "Piping ... governs all characterized sections under adopted conductivity and conservative foundation gradation. Both inputs have brackets." | **unscoped**: drainage conditions two of the four |
| Ch9 RQ4 | "KP 58.8 has the smallest ratio but highest absolute probability ... because it already lies highest on its curve" | **unscoped** |
| Ch9 recommendations, ranking paragraph | "KP 60.0 falls from second to last when only the measured berm is credited" | scoped, but **overstated**: historically KP 60.0 is last in only 89 % of flood-ensemble resamples (section 6.4) |
| Ch9 future-research register | drain boundary condition | scoped; the data needed are not named |

## 3. What a landside toe drain does to backward erosion piping, and what this model can represent

Sources read for this study, page by page:

* **PWRI (2014)**, `syousasekkei_point1407.pdf`. Table 7.1.1 (printed p. 33):
  for heave and piping the drain method acts by "reducing the hydraulic
  gradient at the landside toe"; a separate method, landside foundation
  drainage, acts by "reducing uplift pressure at the landside toe". §9.1
  (printed p. 42): the drain is a high-permeability zone replacing the
  landside toe of the embankment, 0.5 m or more thick, its width set so the
  average gradient stays below 0.3, with a filter against suction of
  **embankment** soil on the embankment side. §9.2 (printed p. 43): its effect
  is governed by the **embankment** conductivity (strong at 10⁻³ to 10⁻⁴ cm/s,
  weak at 5×10⁻² and 5×10⁻⁵). The Japanese toe drain is designed first as an
  embankment-seepage drain.
* **USACE EM 1110-2-1913 (2000)**. §5-8 (p. 5-10): a pervious toe "will provide
  a ready exit for seepage through the embankment"; it controls shallow
  underseepage only in combination with a partially penetrating toe trench.
  §5-5 (pp. 5-3, 5-4): where the pervious stratum is thick, a trench of any
  practicable depth attracts only a small portion of the flow and underseepage
  bypasses it. §5-4 (pp. 5-2, 5-3): a landside seepage berm acts by weight and
  by length, lowering uplift at the berm toe; an impervious berm raises the
  pressure beneath the top stratum at the levee toe.
* **TRZmw (1999)**. §5.4.1 (p. 62): four principles, of which "preventing sand
  wash-out" is one. §5.4.4 (pp. 63, 64): the piping berm prevents uplift within
  the critical seepage length, sized by weight. §5.4.7 (pp. 65, 66): a filter
  at the exit prevents piping only if it is sand-tight, if it sits at the known
  exit point (the cover layer cut through), and if it is more permeable than
  the subsoil.
* **OYO (1999)**, Table 7-5-1 (report p. 174), re-read from the scanned page for
  this study: the 1998 design computed the local vertical gradient after a
  cut-in drain **above** the cover layer and after one **through** it. Above:
  KP 58.8 1.30 → 1.13, KP 60.0 0.50 → 0.48 (relief 13 and 4 %); through (KP 58.8
  and KP 62.0 only): 1.30 → 0.30 and 0.97 → 0.23 (77 and 76 %). KP 60.0 was
  secured by the above-cover drain; KP 58.8 needed the penetrating one. This is
  the case without land acquisition, i.e. without the berm that was built.
* **Fukuda (2026)**, `帯広市街地の堤防の現状.pdf` p. 1 (the RIC note of May 2026)
  and p. 2 (the type map). Type ⑤ places drain material (ドレン材) at the toe of
  the original landside slope, beneath side-berm fill. The note states that
  the levee geometry and soil data now differ from the 1998 report, that the
  current cross-sections are published by the Development Bureau, and that
  soil data for the berm fill are expected to be hard to obtain.

**What follows.** A toe drain can act on backward erosion piping in three
physically distinct ways, and which one applies at KP 58.8 and KP 60.0 depends
on details that are not on record: whether the drain penetrates the 0.85 m
blanket, whether its material is filter-compatible with the foundation sand
(PWRI specifies the filter against the embankment), and its present condition.

| Role of the drain | Condition | Effect on the model's limit states | Closest reading |
|---|---|---|---|
| inert for the foundation | sits on an intact blanket (above-cover drain) | none on the aquifer head; exit at the berm toe | **measured-berm arm**; OYO's own design implies 4 % gradient relief at KP 60.0 |
| relief and filter | penetrates the blanket and is sand-tight against the foundation sand | lowers the aquifer head (both piping drivers, not only the gate) and blocks transport at its own exit | the relief ladder's strong end, and beyond it (the ladder relieves the gate only) |
| unfiltered exit | penetrates the blanket but is not sand-tight | an open exit at the former toe, near the 1998 seepage length, with the blanket gate bypassed | close to the as-if-undrained configuration at the design level, where the gate is already 0.999 open |

The engine's gate relief (ADR-0050) represents the first row's small
residual and the uplift part of the second row. It does not represent the
second row's lowering of the piping driver, which would need the head field of
a two-dimensional seepage solution: the Sellmeijer rule and the Pol ODE both
take one exit at the downstream end of a single path and one head difference
across it, and neither can place a relief line inside the path. Gate relief is
therefore a direction-correct parametric proxy, not a drain model, which is
what ADR-0050 said. What this study adds is that **the physically possible
present-day states span the whole bracket, including its as-if-undrained
end**: the as-if-undrained number is not merely the 1998 state, it is also
close to the present-day state in which the drain provides an unfiltered exit.

## 4. Why the present-day levee is not the deliverable, on the merits

**What is known about the present day.** The berm footprint (2025 lidar, 31 of
31 clean stations at each section), the works type (Fukuda type ⑤), and the 2008
classification of the reaches as seepage-secured.

**What is not.** The drain's position relative to the blanket, its gradation
against the foundation sand, its present condition, the berm fill's
permeability and weight, and whether the blanket beneath the berm is intact
(the KP 58.8 landside borehole shows gravel where the blanket should be;
provenance §4).

**What the 1998 configuration buys.**

1. Internal consistency: the only site-specific geotechnical data (the 1998 OYO
   boreholes and laboratory tests) describe exactly the configuration evaluated.
2. A well-defined object: every input is either measured or carries a stated
   prior. A present-day deliverable would rest on the drain's role, which the
   records leave open across the whole bracket (section 3).
3. It quantifies what the works were built against, which is the quantity a
   manager needs to decide whether the drains are safety-critical: what the
   section does if the drain does not work as a filter and relief.
4. The first sub-question is a comparison of two criteria on one foundation, and
   it is where the undrained treatment matters least (section 6.1).

**What it costs.** Sub-questions 3 and 4 and the ranking at these two sections
are not present-day statements; the 2016 likelihood at the two informative
strata is evaluated on a structure other than the one that survived, which
over-excludes; and the two sections at the top of the ranking are the two whose
present-day state the model knows least.

**Was it the right call?** For the deliverable, yes: the alternative would swap
a transparent, well-defined configuration for a precise number resting on an
assumption about the drain. What was missing was the presentation: the
measured-berm reading, which is the best-grounded reading of the present-day
geometry, was not carried beside the numbers it qualifies. That is what the
decision below corrects.

## 5. Options put to the author, and the decision

Asked on 2026-09-24, one question, recommended option first.

| Option | Cost | Consequence |
|---|---|---|
| **A + measured-berm companion** (recommended, **chosen**) | this session; no production re-run | keep the deliverable, defend it, fix the explicitness sites, and carry the measured-berm reading beside every KP 58.8/60.0 claim that drives a conclusion |
| A only | this session | fixes the sites, answers the meeting question less directly |
| C: present-day as production | 1 to 2 weeks; 4 sweeps, new Phase 2 hash gate, Phase 3 recomposition, about 15 figures, every study measured on these two sections re-run or re-scoped | the deliverable would rest on an ungrounded drain assumption; the 2016 update becomes nearly vacuous everywhere |
| D: obtain as-built data first | weeks to months, outside this project | unlikely before November; the thesis can be finished without it |

The data request that would unlock a real drain model (for the author's
supervisors, section 8) is recorded either way.

## 6. The measured-berm companion reading

**Definition, and what it is not.** Seepage length at the 2025 lidar value
(42.0 m at KP 58.8, 43.0 m at KP 60.0), the drain credited at zero. It is the
first row of the table in section 3: an assumption that the drain is inert for
the foundation, and that the berm prevents uplift throughout its footprint
(TRZmw §5.4.4's design condition, unverified here). **It is not a present-day
estimate**; it is the present-day reading that uses only measured geometry. It
is matrix-only: under the bulk reading KP 58.8's design level lies below the
reachable range (ADR-0050 §4).

### 6.1 The first sub-question: the index separation is robust, the ratio is not

Not computed by ADR-0050. At the design-level grid point (41.00 m and 42.75 m),
N = 10⁵, paired bootstrap over the shared rows (1,000 replicates, the
`rq1_beta_analysis.py` construction), the arms sharing their θ rows so the
displacement is paired too:

| Reading | KP 58.8 B | KP 58.8 Δβ [95 %] | KP 60.0 B | KP 60.0 Δβ [95 %] |
|---|---|---|---|---|
| as-if-undrained (deliverable) | 2.75 | 1.224 [1.215, 1.233] | 2.92 | 1.866 [1.853, 1.879] |
| measured berm | 4.51 | 1.208 [1.198, 1.219] | 6.49 | 1.808 [1.797, 1.820] |
| displacement | ×1.64 | −0.016 [−0.027, −0.005] | ×2.22 | −0.058 [−0.073, −0.043] |
| berm + 20 % relief | 4.67 | 1.228 | 6.84 | 1.838 |
| berm + 40 % | 6.49 | 1.410 | 9.87 | 2.040 |
| berm + 60 % | 77.1 | 2.465 | 104.7 | 3.050 |
| berm + 80 % | transient 0 | undefined | transient 0 | undefined |

The measured berm moves Δβ by at most 0.06 while it moves B by 1.6 and 2.2
times: the berm lengthens the path for both criteria, so both indices rise
nearly together. Relief then acts on the transient branch alone (the static
branch is exactly invariant, ADR-0050 P1) and only widens the separation. **The
as-if-undrained Δβ at these two sections is therefore the lower end of the
index separation across the whole bracket.** No pre-registration: computed
during this study from persisted matrices; both directions would have been
reported.

### 6.2 The second sub-question: the 2016 update

Rejection of the prior by the replayed 2016 record, corrected gauge node
(KP 56.73) on every row:

| Reading | KP 58.8 | KP 60.0 |
|---|---|---|
| as-if-undrained (production) | 5.512 % | 3.244 % |
| measured berm | 1.497 % | 0.531 % |
| berm + 20 / 40 / 60 / 80 % | 1.298 / 0.593 / 0.013 / 0 % | 0.419 / 0.161 / 0.001 / 0 % |

The survival is the structure's; on the
measured geometry the same record rejects 3.7 and 6.1 times less, which is the
size of the over-exclusion the thesis states qualitatively. Marginal transient
rejection stays zero in every replay (ADR-0050 §6).

### 6.3 Sub-questions 3 and 4: annual probability, share, climate ratio

Matrix, posterior, λ_ac = 250 m, primary surface set. Intervals: d4PDF
member-block bootstrap stratified inside the SST patterns, 10,000 replicates,
the published estimator and seed; **hazard-sampling only, fragility curves
fixed, far narrower than the conductivity bracket**. The as-if-undrained
intervals reproduce the published record exactly (tested).

| Section, reading | historical | +4 K | ratio [95 %] | piping share hist / +4 K |
|---|---|---|---|---|
| KP 58.8 as-if-undrained | 7.45 [5.41, 9.69]e-3 | 4.10 [3.76, 4.44]e-2 | 5.51 [4.18, 7.69] | 0.974 / 0.941 |
| KP 58.8 measured berm | 4.26 [2.94, 5.72]e-3 | 2.67 [2.41, 2.95]e-2 | 6.28 [4.59, 9.25] | 0.955 / 0.911 |
| KP 58.8 berm + 80 % (lower bound) | 1.97e-4 | 2.80e-3 | 14.2 | 0.009 / 0.147, overflow leads |
| KP 60.0 as-if-undrained | 1.81 [1.13, 2.56]e-3 | 1.42 [1.24, 1.62]e-2 | 7.86 [5.40, 12.8] | 1.000 / 0.998 |
| KP 60.0 measured berm | 6.40 [3.70, 9.48]e-4 | 6.52 [5.45, 7.66]e-3 | 10.2 [6.58, 18.0] | 1.000 / 0.996 |
| KP 60.0 berm + 80 % (lower bound) | 0 | 2.98e-5 | undefined | overflow leads under warming |

On the measured berm piping still leads at both sections in both climates; the
dominance claim at these two sections becomes conditional only under strong
credited relief. Crediting drainage raises the climate ratio (ADR-0050 §7).

### 6.4 The ranking, with the intervals it never had

| Reading | order | resolved? |
|---|---|---|
| as-if-undrained, both climates | 58.8 > 60.0 > 62.0 > 57.4 | in 100 % of replicates |
| measured berm, +4 K | 58.8 > 62.0 > 57.4 > 60.0 | in 100 % of replicates |
| measured berm, historical | 58.8 > 62.0 > {57.4, 60.0} | 58.8 first and 62.0 second in 100 %; KP 60.0 last in **89 %**, KP 57.4/KP 60.0 = 1.18 [0.88, 1.39] |

KP 58.8's lead over the second section is 4.23 [3.19, 6.17] historically and
2.09 [1.91, 2.32] under warming on the berm reading (against 4.12 and 2.89 over
KP 60.0 as-if-undrained). **Correction to the thesis:** "KP 60.0 falls from
second to last when only the measured berm is credited" holds under warming and
is not resolved historically; what is resolved in both climates is that KP 60.0
falls below KP 62.0. ADR-0050 §7 made the same statement without intervals.

## 7. Defects found and corrected

1. **ADR-0050 companion note §6 and ADR-0050's Outcome** printed the Phase 2
   arm rejections at the superseded KP 56.6 gauge node (5.673 → 1.551 % and
   3.363 → 0.555 %) with no marker, although the arm replays were re-run at the
   corrected node on 2026-09-15 (5.512 → 1.497 %, 3.244 → 0.531 %). Marked in
   place with dated pointers; §7's annual values likewise (7.42e-3 → 7.45e-3,
   4.25e-3 → 4.26e-3, 1.80e-3 → 1.81e-3).
2. **Provenance §3.2 table and §4 KP 58.8 / KP 60.0 notes** still said the model
   "sets exit head to zero" and that L is a placeholder there, which §3.1's own
   2026-07-28 correction had refuted for its bullet only. Marked in place.
3. **Thesis Chapter 6**: the berm-reading transient compatibility figure mixed a
   canonical-shape grid value (5.4 %) with replay rejections; corrected to the
   replay value 1.5 %.
4. **Thesis Chapter 9 (and ADR-0050 §7)**: "KP 60.0 falls to last" is resolved
   under warming only (section 6.4).
5. **Thesis Chapter 1**: the technical scope gave the drained sections toe
   drains only; they received berms and drains.

## 8. The data request that would unlock a drain model

For the Obihiro Development and Construction Department, through the Hokkaido
supervisor or the RIC contact:

1. As-built drawings of the 1999 to 2003 side-berm and landside toe-drain works
   on the Kita-Obihiro levee between KP 58.0 and KP 61.0: drain cross-section,
   depth relative to the cover layer (above it, or cut through it), length and
   outlet.
2. Drain and filter material gradations, and which soil the filter was designed
   against (embankment or foundation).
3. Berm fill quality records (density; the RIC note expects permeability to be
   unavailable).
4. **The post-works seepage verification of these sections** under the 2002
   guidelines (the FY2003 to 2007 verification the chronology records), which
   would give computed post-works toe gradients directly: the single most
   useful document.
5. Any piezometer or inspection record at the landside toe since 2003.

With items 1, 2 and 4 the drain's role in section 3 would be decided; a drain
that penetrates the blanket would then need a two-dimensional head field, a new
model component. **The thesis can be finished without any of it**: the
as-if-undrained deliverable and the measured-berm companion are complete.

## 9. Which numbers changed

**No production number changed.** New numbers, all companion readings:
Δβ on the measured berm (1.21 and 1.81, displacement −0.016 and −0.058); the
corrected-gauge berm rejections 1.50 and 0.53 % (computed 2026-09-15, first
quoted now); hazard-sampling intervals on the berm-reading annual values,
ratios and ranking (section 6.3, 6.4). Corrected statements: the Chapter 6
compatibility figure (5.4 → 1.5 %) and the KP 60.0 ranking claim.

Thesis side: `msc-thesis` commit `c63c674` (pushed to Overleaf 2026-09-24).
New Section 7.2.4 "The Two Toe-Drained Sections on Their Measured Berm"
(`subsec: Drained Sections on the Measured Berm`) and Table 7.3
(`tab: drained companion`); the merits-based defence closes Chapter 3's
remediation passage; the Summary, Chapter 1 scope, Chapters 6, 8 and 9 and
Appendices C and I carry the companion numbers at the sites of section 2.

## 10. Deliberately not done

* No drain model and no new relief arm: the role of the drain is undetermined
  (section 3), and a relief value would be invented.
* No change to the deliverable (option C declined).
* No bulk-reading companion table: ADR-0050 §4 already records that the
  bracket is matrix-only in effect.
* The Chapter 8 limitations register was touched only in its two drainage
  rows; item 6 restructures it.
