# Defence brief, 2026-08-22

**What this is.** Twelve questions the committee is most likely to press, each with
the answer the document can actually carry and the evidence that carries it. It is
written for the defence of `d:\repositories\msc-thesis` as it stands on 2026-08-22,
after the whole-document submission gate of the same date.

**Scope and honesty rules.** Every answer below is traceable to a named section,
float or evidence artifact. Where the document cannot support a confident answer,
the entry says so and is marked **KNOWN EXPOSURE**. A confident paragraph that
collapses under one follow-up is worse than a stated limit, and three of the twelve
entries end in a stated limit. **Amended 2026-08-23: two do.** The Q12 exposure was
closed by a thesis edit of that date; it is marked closed in place below and removed
from the summary table, and the paragraph that recorded it is left standing.

**Why no page numbers.** The committed `report.pdf` was built on 2026-08-15 and
predates the edits of 2026-08-20 to 2026-08-22. Page numbers taken from it would be
wrong. Every pointer below is therefore by chapter, section title, float label or
engine artifact, all of which are stable across a rebuild. Fill the page numbers in
from the fresh Overleaf build (submission checklist, item 2).

**Prior art.** `msc-thesis/scratch/DEFENCE_BRIEF_2026-08-06.md` (gitignored, local
only) ranks the five weakest claims and lists twenty shorter questions. It is not
superseded by this document; the two are complementary. Where the two disagree on a
number, this one is later and was checked against the engine artifacts.

---

## Q1. Why the Sellmeijer rule and the Pol progression law, rather than another formulation?

**Answer.** Because of what each candidate *returns*, not because of its statutory
standing. The empirical creep tradition (Bligh 1910; Lane 1935) returns a
permissible head at a fixed geometry through a coefficient fitted to surveyed
structures. It carries no progression rate and no record of how far a pipe has
already advanced, so a loading of finite duration has nothing in it to act on, and
duration is the whole of the question here. The same objection disqualifies it as
the static comparator.

The positive case for the recalibrated critical-head rule is that the progression
law is *built on it*: the equilibrium curve `H_eq(l)` supplying the resistance side
of the rate equation is anchored on that rule's critical head. One critical head
therefore serves both limit states, which is what makes the paired comparison a
comparison of **loading treatments** rather than of resistance models. A different
backbone on either side would confound the two irrecoverably.

**The cost, stated first if asked.** The regression behind the rule was fitted on
sands of experimental mean diameter 0.208 mm with a validated range reaching
0.430 mm, and three of the four study cross-sections lie above that range even on
the finer of the two gradation readings. Selecting a different formulation does not
avoid the limit: the alternatives are calibrated on the same experimental base or
on none. It is carried explicitly, as two co-primary gradation readings whose
separation measures how far the rule may be trusted in a gravel-dominated
foundation.

**Evidence.**
- Thesis Ch. 2, "The Dutch Progression-Based Sellmeijer Model and the Regional
  Probabilistic Framework"; Table `tab: model selection` (six formulations against
  what each returns); Table `tab: framework comparison`.
- Thesis Ch. 4, "Static Limit State" and Eq. `eq: pol ode`.
- Engine: ADR-0002 (shared-sample contract, one theta through one evaluator call);
  `bep_reliability_engine/sellmeijer.py` is the **single source of H_c for both
  limit states**; `docs/architecture.md` M6/M7.

---

## Q2. Why is the headline factor quoted against the steady-state rule as calibrated on the gross head, rather than against the crack-reduced comparator an assessment instrument actually applies? And what is the factor against the latter?

**Answer, part one.** The `0.3 D_bl` crack-resistance term is a resistance internal
to the *transient* formulation (Pol SIE 2024, Eq. 6). Sellmeijer's critical head is
defined and calibrated on the head across the structure. Crediting the steady-state
rule with a reduction its own calibration does not contain would build a hybrid
comparator representing neither the published rule nor Dutch assessment practice,
and it would also break the single-source critical head that makes the comparison a
comparison of loading treatments. The gross-head form is therefore the production
comparator, and the difference between the two conventions is **isolated and
measured** as the head-convention component rather than absorbed into the baseline.

**Answer, part two, and this is the number to have ready.** Against the
crack-reduced comparator (variant `C_1` of the comparator ladder), *no design-level
row resolves at all*: 4 and 15 failing transient realizations at KP 62.0 (design
level and 11 cm above it) and none at KP 57.4. Where the counts support a ratio it
is **6.0 at 47.00 m** and **3.9 at 39.50 m**, decaying to 1.4 and 1.0 at the tops
of the two attainable ranges. So the honest statement is: 26.9 against the rule as
calibrated, about 6 against the comparator an instrument applies, and the
design-level row of the latter is unresolved.

**Why this is a strength, not a concession.** The head convention accounts for
three quarters of the probability difference at KP 62.0 and 97 per cent at
KP 57.4. That is the thesis's own finding and it is stated in the Summary, in
Ch. 6, in Ch. 8 and in Ch. 9. The document does not lead with 26.9 and hide the
6.0; both appear in the Summary's third paragraph and in the one-sentence
conclusion of Ch. 9.

**Evidence.**
- Thesis Ch. 4, "Static Limit State", the paragraph beginning "Dutch assessment
  instruments compare that same critical head"; Table `tab: comparator ladder`.
- Thesis Ch. 6, "The Production Gap"; Table `tab: gap components`; Figures
  `fig: gap waterfall`, `fig: gap fractions`, `fig: gap ladder`.
- Thesis Ch. 9, `subsec: Conclusion RQ1` and the one-sentence overall conclusion.
- Engine: ADR-0027 / ADR-0028 (raw erosion head; raw static gross head; r_e drives
  only the uplift/heave gate), superseding ADR-0007; `docs/stage6_6_report.md`.

---

## Q3. The central Bayesian result is a zero. Why is that a positive finding rather than a failed experiment, and exactly what does it license?

**Answer.** The zero is the **marginal transient rejection**: the fraction of
realizations that survive the static criterion and fail the time-dependent one. It
is exactly zero in all eight strata and all sixteen runs at N = 1e5, and it is a
structural property, not a sampling outcome. A transient breach requires the
erosion head to exceed the same critical head the static rule compares against, so
the transient failure set is contained in the static one by construction. The zero
therefore holds under both signs of the exit-datum scenario and under every
erosion-coefficient prior examined, while the rejection fractions themselves move
by factors of two to ten.

**What it licenses.**
1. A statement about the *structure* of the two limit states, verified rather than
   assumed: the two failure sets are nested at this loading, and the nesting is
   exact under every variant tested.
2. The calibration reading, which is the substantive result. The static comparator
   asserts that **58 and 73 per cent** of the prior should have failed at a load the
   levee demonstrably withstood; the transient model says **5.7 and 3.4 per cent**.
   That is the quantified form of the empirical paradox the thesis opens with.
3. The separate, non-zero measurement of what the time-resolved replay adds: a
   peak-only reading of the same survival over-rejects by **2.75 and 3.90** under
   the canonical compound event and **1.45 and 1.57** under the shorter approved
   event, always in the unsafe direction. This is method against method on one
   sample, and it is the finding with the clearest practice implication.

**What it does not license.**
- It is not evidence *for* the time-dependent mechanism specifically. The
  prior-to-posterior shift cannot be offered as such, because at this loading the
  transient criterion rejects nothing the static one does not.
- It is not a validation of the progression physics. The only out-of-sample test of
  that physics in the whole work is the Yabe three-site discrimination (0.061 at
  the section that breached; 0 in 1e5 and 0.005 at the two that survived, against
  committee uplift-ratio minima of 0.62 and 0.65 that cannot separate them).
- The posterior parameter shifts are an **upper bound**: the survival was produced
  by a drained structure while the likelihood is evaluated on the undrained
  foundation, which breaches more readily.
- Three ceilings bound the instrument: the filter cannot reach the seepage length
  (moved 1.4 per cent or less while holding 0.49 to 0.78 of the transient
  variance); the update redistributes weight inside an assumed prior population and
  leaves the epistemic band exactly as wide as it found it; and the evidence set is
  closed at 2016 on measured grounds (a bounding 2011 replay places its marginal
  information at 0.316 per cent in the one stratum where it is non-zero).

**Evidence.**
- Thesis Ch. 6, "How Much the Survival Rejects" and "What the Replay Adds";
  Figures `fig: phase2 survival update`, `fig: peak shortcut`,
  `fig: seepage length ceiling`.
- Thesis Ch. 8, "Bayesian Calibration as a Bridge Between Static Theory and Field
  Evidence"; Ch. 9, `subsec: Conclusion RQ2`.
- Engine: `docs/phase2_report.md`;
  `docs/decisions/phase2-survival-update-per-stratum.json` and `.csv`;
  `docs/decisions/phase2-peak-shortcut.json`; ADR-0044 (event set closed at 2016);
  ADR-0046 (z_toe scenario, marginal transient rejection stays zero).

---

## Q4. The mechanism-dominance answer rests on four cross-sections out of 114. Why is that defensible, and what are the other 110?

**Answer.** The four are not a sample of the 114; they are the entire population at
which the question can be posed. A piping branch is attached to a segment only
where a borehole-based parameter prior exists, and none is interpolated between
investigated cross-sections. The other 110 are composed from the surface mechanisms
alone. They are therefore **explicit lower bounds that omit a mechanism rather than
estimating it as small**, and no dominance statement exists at any of them. The
answer is a four-section answer and the reach-wide distribution is reported as
context, not as a result. The thesis says this in the scope register of Ch. 1, in
the coverage section of Ch. 7, in the limitations register of Ch. 8 and in the
answers register of Ch. 9.

**The follow-up to expect, and the answer.** "The four highest-risk segments in the
basin are your four investigated ones. Isn't that circular?" It is a coincidence
that follows from where boreholes were drilled, and the thesis states it as such:
it is not evidence that the uninvestigated segments are safe. Resolving it is the
fifth item of the future-research register, and what it would settle is precisely
"whether the coincidence is a fact about the reach or about the survey".

**Evidence.**
- Thesis Ch. 1, "Geographical Scope" and Table `tab: scope register`, row "Piping
  population".
- Thesis Ch. 7, "Extent of the Mechanism Comparison"; Table
  `tab: mechanism coverage`.
- Thesis Ch. 8, Table `tab: limitations register`, row "Piping quantified at 4 of
  114 evaluation segments".
- Thesis Ch. 9, `subsec: Conclusion RQ3`, second paragraph; Table
  `tab: future research`, row 5.

---

## Q5. Two independent measurement populations bracket the adopted aquifer conductivity from opposite sides. Why was it retained, and what follows for every number in the thesis?

**Answer, why retained.** Because neither population estimates the quantity the
seepage path requires, which is the **bulk horizontal conductivity at the scale of
the path**. The six in-situ determinations, across two contractors and two decades,
have a geometric mean 17 to 51 times below the adopted analysis constants and 5.0
to 7.3 standard deviations below the prior median, but a single-borehole test is
biased low. The regional band lies above the prior's 95th percentile, but it
belongs to a different setting and the analysis constant was chosen high. Adopting
either would substitute one unmeasured quantity for another. The priors are
therefore retained and the disagreement is reported as a **bounding scenario**, run
against the frozen production sweeps, rather than absorbed into a widened
coefficient of variation that the evidence does not support.

**Answer, what follows.** This is the honest and slightly uncomfortable half, and
it should be given without prompting.
- Conductivity is the largest epistemic knob at every section and every anchor, by
  three to five orders of magnitude over anything else. At KP 62.0's transition
  midpoint it spans a factor of **6.6e3** against a Clopper-Pearson span of 1.01 on
  the same estimate.
- Production sits **inside** the bracket and at neither end. At KP 62.0's design
  level it sits at 26 per cent of the logarithmic bracket, with an upside of about
  three orders of magnitude and a downside of a factor of 15. Reading only the
  field-test arms would license the comfortable and wrong conclusion that the
  adopted prior is conservative.
- It does **not** cancel in the static-to-transient ratio, and it amplifies it:
  displacements of up to 82, 66, 163 and 46 across the four sections, and
  1.1 to 1.8 decades of ratio movement per decade of conductivity.
- Propagated through the annualization it contests the mechanism ordering at three
  of four sections historically and at all four under warming, that is at **seven
  of the eight** section-and-climate cells. The field-population arm reverses six
  and collapses one; KP 60.0 historically is the single robust cell, and it is
  robust only because its overflow branch is exactly zero.
- Carried across the 2016 survival constraint, the bracket narrows by a factor of
  up to 2.81, **from its upper end alone** (the constraint rejects a
  high-conductivity prior 11.6 to 25.8 times more heavily than the adopted one),
  and all sixteen ordering verdicts are reproduced.
- The single measurement that would most improve the credibility of every absolute
  number in the thesis is a field determination of bulk horizontal conductivity at
  the scale of the seepage path.

**Evidence.**
- Thesis Ch. 5, "The Aquifer Conductivity Prior under Scrutiny"; Table
  `tab:kaq_scenarios`; Figures `fig: epistemic bracket ranking`,
  `fig: epistemic vs statistical`.
- Thesis Ch. 7, "The Ordering Is Also Conditional on the Aquifer Conductivity";
  Figures `fig: conductivity annual`, `fig: conductivity both readings`.
- Thesis Ch. 8, "The Deliberate Narrowness of the Aquifer Conductivity Prior" and
  "Not Every Epistemic Knob Cancels in a Ratio".
- Engine: ADR-0048; `docs/decisions/conductivity-bracket-annualisation.md` (and its
  2026-08-21 correction on the seven-versus-eight cell count);
  `docs/decisions/conductivity-bracket-posterior-side.md`;
  `docs/decisions/epistemic-bracket-synthesis.md`;
  `docs/decisions/epistemic-bracket-ranking.csv`.

---

## Q6. The fluvial scour model returns identically zero. Why is that a corrected result rather than a broken one, and what is the corrected branch's own validation status?

**Answer, why corrected.** The erodibility coefficient of the excess-shear
formulation is a bed erosion rate per unit shear stress. The received implementation
converts it to SI with a factor approximately **105.6 times larger** than the
dimensionally consistent one. Under the consistent conversion the critical bed
shear stress of roughly 51 Pa exceeds the sheet-flow shear on the high-water bed
throughout the loading range, so the mechanism never engages against a levee body
tens of meters wide within a multi-day flood. The zero is a substantive statement
about an imported model under a corrected unit conversion, not a rounding artifact,
and the correction is made on dimensional grounds rather than on the grounds that
it produces a preferred answer.

**Answer, validation status, and this is the honest part.** The corrected branch has
**no independent validation of its own**. The equivalence gate on the re-execution
tests the re-implementation against the *received* implementation, so it certifies
faithfulness of re-execution and nothing about the corrected physics. Its zero
belongs to the model and its inputs, not to the conditioning. The one thing that
*is* established is that the zero is not an artifact of the conditioning: the
event-based re-execution returns zero both curve-based and event-based at every
section node.

**The consequences, stated in full.**
- The as-received conversion is retained as a labeled companion. At the four
  characterized sections it is immaterial (at most 8 per cent at KP 57.4, 2 per
  cent or less at KP 58.8 and KP 60.0, 22 per cent at KP 62.0 historically) and
  changes no dominance ordering. Across the remaining 110 surface-only segments it
  changes the picture completely, making scour dominant at 97 of 114 segments
  historically and 66 under warming. So the conversion conditions the ordering
  *among the surface mechanisms*, not the comparison against piping.
- The source study's erosion-dominant headline does not reproduce under the
  corrected conversion, and the thesis says so plainly.
- Because the composition attributes to piping essentially whatever is not
  attributed to overflow, a branch contributing nothing mechanically **inflates the
  piping share**. Piping therefore dominates *among the mechanisms represented*.
- Two levees in this system failed by erosion in 2016, so a model returning
  identically zero is not describing the world. The mismatch is one of mechanism,
  not of calibration: the model keys erosion to submergence depth of the high-water
  bed and contains no thalweg position, no bend curvature and no foreshore width,
  while the documented failures were near-bank attack from a relocating channel on
  the falling limb.

**Evidence.**
- Thesis Ch. 7, "Fluvial Scour Is Identically Zero"; Table `tab: mechanism coverage`
  (as-received erodibility columns).
- Thesis Ch. 8, "The Surface-Mechanism Model Set as a Conditioning Assumption";
  Figure `fig: foreshore exhaustion`.
- Thesis Appendix G, "Event-Based Validation of the Surface Curves".
- Engine: ADR-0042 decision 9 (amended); `docs/phase3_report.md` and its dated
  addenda; `docs/decisions/r10-foreshore-exhaustion-screening.md`.

---

## Q7. Why are the two highest-risk segments reported as if their drains were absent?

**Answer.** Because the drainage function is not represented in the physics, and
representing it would require a landside-exit boundary condition that no secured
material fixes. The 1999 to 2003 works are recorded per segment, but the dataset
holds neither the post-remediation geometry nor the drain capacity, and Japanese
guidance sizes the drain body rather than the foundation it sits on. Rather than
select one arbitrary drain performance, the computed fragility at KP 58.8 and
KP 60.0 quantifies **the foundation hazard the drains were installed to suppress**,
which is a well-defined quantity, and that as-if-undrained figure remains the
deliverable.

**What has changed, and it should be volunteered.** The treatment is no longer
merely stated; it is bracketed. The two quantities Japanese guidance names for the
recorded countermeasures were perturbed, the seepage path (post-works length
measured from the 2025 surface) and the landside exit gradient (swept, because no
recorded material fixes it), carried through the survival update and the annual
numbers under both gradation readings, against bit-identical baselines.
- Conditional, at the design level, on the measured berm alone: 0.263 to 0.108 at
  KP 58.8 and 0.314 to 0.111 at KP 60.0; to zero once a drain removes about four
  fifths of the exit gradient.
- Annual: 7.4e-3 to 4.2e-3 to a lower bound of 2.0e-4 per year at KP 58.8, and
  1.8e-3 to 6.4e-4 to zero at KP 60.0. The span at KP 58.8 is a factor of 37.
- The response is strongly non-linear: the first 20 per cent of relief is worth a
  factor of 1.03, the step from 40 to 60 per cent a factor of 12.
- The static comparator is **exactly invariant** under the exit-gradient relief,
  because that gradient reaches the initiation criterion and nothing else. That
  makes the mapping testable rather than asserted, and it did not move at any
  conditioning level.

**The ranking consequence, which is the sharpest thing this produced.** KP 58.8
holds its lead across the whole range in both climates and loses it only where the
drain is credited with removing four fifths of the exit gradient. KP 60.0 does not:
it falls from second place to last as soon as the *measured* berm is credited, which
requires no assumption about the drain at all. KP 60.0's second place is therefore
an artifact of the as-if-undrained treatment; KP 58.8's lead is not.

**The limit.** This is a range for a configuration, not an estimate of present-day
reliability. The strongest arm's annual figures are lower bounds, not estimates,
its transition having left the conditioning grid.

**Evidence.**
- Thesis Ch. 1, "Technical Scope"; Table `tab: scope register`, row "Remediation
  state".
- Thesis Ch. 8, "What the Model Represents at a Cross-Section"; Table
  `tab: limitations register`, row "Toe drainage at KP 58.8 and KP 60.0 not
  represented".
- Thesis Ch. 6 and Ch. 7 standing-conditions registers, "Remediation state not
  credited" rows; Ch. 9 ranking paragraph.
- Engine: ADR-0050 (`0050-toe-gradient-relief-drained-bracket.md`);
  `docs/decisions/adr0050-drained-configuration-bracket.md` and its JSON;
  `docs/decisions/adr0050-drained-bracket-annualisation-{matrix,bulk}-posterior.json`.

---

## Q8. Why is the plane-strain scale exponent the baseline when the progression law was calibrated against a three-dimensional one, and what happens to the headline under the alternative?

**Answer, why baseline.** Both production branches share a single critical head, so
the scale exponent is absent from the production comparison by construction. The
plane-strain anchor is the baseline the progression model's author endorses for a
two-dimensional Sellmeijer-based model at blanket thicknesses such as these. Making
the exponent differ between the two branches would reintroduce a resistance
difference into a comparison whose entire purpose is to isolate the treatment of
loading.

**Answer, what happens under the alternative, given without softening.** Re-anchoring
the transient branch at the three-dimensional exponent its progression law was
calibrated against moves a great deal of probability, and in the opposite direction
to every other component. The step alone is **-0.43 at 47.00 m and -0.47 at
48.00 m at KP 62.0, and -0.50 at 40.50 m at KP 57.4**, all resolved. The physics
ladder's total gap then nearly vanishes: **-0.05, +0.06 and -0.04** at those three
stages, against production-ladder totals of +0.05, +0.34 and +0.41. Under a fully
three-dimensional reading of the resistance scaling, most of the static margin
disappears.

**Why it is nonetheless a bounded sensitivity rather than the answer.** Three
reasons, and all three are in the text.
1. Under the co-primary bulk gradation reading the dimensional component **reverses
   sign**, reaching +0.37 at the top of KP 57.4's grid and +0.61 at the top of
   KP 62.0's, because the scale group in the critical-head expression crosses unity
   at coarse gradations. The alternative is therefore not uniformly favourable to
   the sceptical reading either.
2. At KP 57.4 and KP 62.0 both gradation readings lie outside the grain-size range
   over which the static rule was calibrated, so the exponent question is being
   asked outside the domain that would settle it.
3. It is quantified explicitly, at every stage and both sections, so neither
   presentation can be adopted silently. That is the correct treatment of a
   modelling choice that moves the headline.

**Do not say** that the three-dimensional reading is wrong. Say that it is
unadopted, measured, sign-unstable across the gradation bracket, and out of
calibration domain at half the sections.

**Evidence.**
- Thesis Ch. 6, "The Equilibrium-Head Anchor and the Scale Exponent"; Figure
  `fig: gap ladder`; Table `tab: comparator ladder` (physics ladder rows).
- Thesis Ch. 8 and Ch. 9, `subsec: Conclusion RQ1`, final conditional sentence.
- Engine: ADR-0017 (`config.alpha_exponent_transient`, None by default, preserving
  the single-source H_c); `docs/stage6_6_report.md`;
  `docs/decisions/adr0033-*` for the sensitivity context.

---

## Q9. Why does a shared sample not make a comparative claim robust to an input bracket?

**Answer.** Because a shared sample removes sampling noise between the branches and
nothing else. An epistemic bracket cancels in a ratio only if the input is
**pure common-mode**: it must reach both models through the same channel and only
through that channel. Whether it does is a property of the structure of the two
limit states, not of the width of the bracket, and it has to be established input
by input, before any number is computed, by reading the channels off the two
formulations.

**The four worked cases, which are the whole argument.**

| Input | Channels into static | Channels into transient | Displacement of the ratio | Cancels? |
|---|---|---|---|---|
| Sellmeijer model factor `m_p` | H_c | H_c (same single source) | 1.07 to 1.22; 1.010 at KP 62.0 | Yes, by construction |
| Aquifer conductivity | H_c | H_c, response factor of the uplift/heave gate, growth-rate law | up to 82, 66, 163, 46; 1.1 to 1.8 decades per decade | No, and it amplifies |
| Seepage length | H_c | H_c plus one transient-only channel | 1.02 to 3.22 at all 87 comparable levels | No |
| Critical pipe length | none | equilibrium curve only | 1.11 to 1.67, exactly the reciprocal of the transient displacement, at all 89 levels | No, and the static side is exactly invariant |

**The instructive pair.** The model factor and the critical pipe length displace the
ratio by the *same amount* and arrive there by opposite routes: the model factor
moves each criterion a great deal and the movements nearly cancel; the critical
pipe length moves one criterion a little and nothing cancels. The size of a
displacement therefore says nothing about whether an input is common-mode, and
reading the mechanism off the size would invert these two.

**Why this is a contribution and not a caveat.** It generalizes to any paired-model
comparison on one shared sample, and it is the seventh and final recommendation of
Ch. 9 for that reason. It is also the result the author should offer as the least
expected methodological finding of the work.

**Evidence.**
- Thesis Ch. 8, "Not Every Epistemic Knob Cancels in a Ratio"; Appendix G,
  "Non-Cancellation Mechanism" (channel by channel, with the test construction).
- Thesis Ch. 9, `subsec: Establishing Bracket Cancellation Input by Input`.
- Engine: ADR-0045 section 2 (`m_p` common-mode by construction); ADR-0047
  (the L bracket does not cancel; rho measured at 87/87 levels); ADR-0049
  (critical-length override, static branch exactly invariant); ADR-0048 and
  `docs/decisions/epistemic-bracket-synthesis.md` (which refuted ADR-0048's own
  cancellation consequence on measurement).

---

## Q10. What is the compound-event memory model, and why does it enter and leave the thesis untested against field observation?

**Answer, what it is.** The eroded pipe length is a state variable carried across
the whole hydrograph. It is monotonically non-decreasing: erosion accumulates while
the initiation gate is open and is retained, not reversed, when the gate closes
during an inter-peak trough. Recovery is set to zero, so a second peak arrives at a
pipe the model does not permit to heal. The staircase trajectories this produces
during troughs are the intended behaviour, not a numerical artifact. This is the
only channel through which compound structure can act in this system, because the
alternative channel the literature proposes, a pressure lag shortened by antecedent
saturation, was screened and found absent: the elastic response time of the
confined aquifer is of order ten minutes against a median rising limb of 18 hours,
a ratio of about one hundredth against a pre-registered activation threshold of one
tenth.

**Answer, why untested. KNOWN EXPOSURE.** No observation in this work tests it, and
the thesis says so in exactly those words. The reasons are structural, not
oversight:
- The one field record available is a **survival**. A survival can falsify a model
  that predicts failure; it cannot discriminate a memory assumption that only ever
  raises the computed probability, because the conservative assumption and the true
  one both survive.
- The two documented 2016 bank-erosion failures in this basin lie outside both
  modeled reaches, so the falsification test that would make the question decidable
  cannot be run at this resolution.
- Zero recovery bounds the error in the conservative direction, which is the right
  default for a limit state, but a bound is not a validation.

**What can still be said in its favour.** The measured consequence of compound
structure is small and is not the channel of the climate signal. Stratifying the
simulated years on the number of separate excursions above the toe separates them
by 3.7 and 6.5 at the two well-populated sections, neither resolvably above one,
against about 150 and about 380 for the duration stratification of the same years.
Compound years are dangerous mainly because they are long. So even if the memory
model were wrong in magnitude, the RQ4 attribution does not rest on it.

**Do not claim** that the memory model is validated, or that its conservatism has
been measured. It has been bounded in direction and its effect has been shown to be
subordinate to duration. That is the whole of it.

**Evidence.**
- Thesis Ch. 4, the pipe-length state variable and the recovery convention.
- Thesis Ch. 8, "Compound Events, Antecedent Saturation, and the Channel of the
  Climate Signal", final paragraph; Table `tab: limitations register`, row
  "Compound-event memory model unvalidated against field observation".
- Thesis Appendix G, "Aquifer-Response Screening".
- Engine: ADR-0032 (aquifer-response diagnostic, Pi = 0.01 against Pi* = 0.10,
  instantaneous default retained on evidence); `bep_reliability_engine/progression.py`
  (positive-part operator, uplift latch, r_l = 0 in Phase 1).

---

## Q11. How would the framework transfer to another basin, and which of its numbers would not?

**Answer, what transfers.** The method, in four parts, none of which depends on the
Tokachi geology: a shared-sample comparison between a steady-state and a
time-resolved criterion; a decomposition attributing the resulting difference to
named modelling ingredients rather than to duration by default; a
survival-conditioned filter applied to the full loading record rather than to its
peak; and a series composition against an ensemble hazard. Plus one structural
lesson, the cancellation rule of Q9, which is a property of any paired-model
comparison.

**Answer, what does not transfer: every number.** The overestimation factor is not a
constant of the mechanism. It varied from 2.75 to at least 148 across four sections
less than five kilometers apart, governed by where each section's design level falls
on its own fragility curve, and it rises by about a factor of two again under a
shorter canonical event. The composition of the difference is likewise
section-specific, and the mechanism-dominance result is conditional on a surface
model set and a gradation interpretation particular to this study.

**The two prerequisites most easily assumed rather than checked.**
1. The confining blanket must overlie an aquifer in hydraulic continuity with the
   channel and saturated at base flow. Both the instantaneous hydraulic translation
   and the uplift and heave gate depend on it. Outside that regime the translation
   over-predicts the head delivered to the toe, by a measured factor of up to 2.7
   in the Japanese field cases.
2. The loading must be long enough for the race to be decidable. If the time above
   the critical head is far shorter than the pipe traverse time nothing progresses;
   if it is far longer everything that initiates completes. Establishing that a
   candidate reach lies between the two is a prerequisite, not a result. The natural
   screening quantity is the section's above-toe duration distribution.

**Evidence.**
- Thesis Ch. 8, "Transferability of the Framework to Other High-Gradient River
  Systems"; Table `tab: transferability` (six conditions, the observation
  establishing each, and the consequence of failing it).
- Thesis Ch. 5, the Japanese validation campaign; Table
  `tab: japanese validation campaign overview`; Figures
  `fig: m4 overtranslation pattern`, `fig: yabe timeline test`; Appendix G,
  Figures `fig: gounokawa hydrograph`, `fig: gounokawa onset`,
  `fig: yabe discrimination`.
- Engine: `docs/validation/` case notes (Gounokawa, Yabe, Shikaga).

---

## Q12. With six more months, what would you do, ordered by how much of the present uncertainty each item would remove?

**Answer, the thesis's own ordering** (Ch. 9, Table `tab: future research`), with
what each would settle:

1. **A migration-capable bank-retreat mechanism in the surface set.** Promote the
   existing deterministic foreshore-exhaustion indicator to a stage-conditioned
   fragility, with bank erodibility, lateral retreat rate and foreshore width
   stochastic and a near-bank velocity replacing the mobilizing duration. Settles
   whether the dominance result survives a surface set containing the mechanism
   this basin's failure record identifies, and supplies a genuine falsification
   test: the model must reproduce that Otofuke KP 21.2 and Satsunai KP 40.5 failed
   under the 2016 loading while the four study sections did not.
2. **A physical representation of the installed toe drainage.** Needs the
   post-remediation geometry and drain capacity the secured dataset lacks. The
   range is already established and is wide (up to a factor of 37 at KP 58.8);
   what a capacity measurement supplies is the *position within* that range.
3. **A limit state for the buried sluice conduits** at KP 62.0 and KP 57.3, whose
   conduits (28 and 27 m) are shorter than the modeled seepage paths (40 and 33 m).
4. **A field determination of bulk horizontal aquifer conductivity at the scale of
   the seepage path.** The largest epistemic bracket in the study.
5. **Extension of the piping population to the borehole-free reaches.**
6. **Field validation of the critical pipe length.**

**The follow-up to expect, and it is a fair one.** "You call conductivity the
largest bracket in the study and you rank it fourth." The register's own answer is
that the ordering is by *uncertainty removed by the action*, not by *uncertainty
present*: the conductivity consequences are already measured under both gradation
readings and through to the annual numbers, so a determination narrows a quantified
bracket rather than quantifying an unquantified one, whereas the bank-retreat item
would close an omission whose consequence is currently reported as "exposure only"
and could overturn the dominance answer outright.

**KNOWN EXPOSURE.** That distinction is doing real work and the table's caption does
not make it explicit. If the committee presses on the ordering, concede the
criterion rather than defending the rank: say that item 4 removes the most
uncertainty from the *absolute probabilities* and item 1 removes the most from the
*answer to sub-question 3*, and that the register orders by the latter because the
dominance ordering is the headline. Do not claim the two criteria give the same
ranking.

**Closed 2026-08-23. The paragraph above is left standing as written; what follows
is what changed under it.** The distinction is now on the page, so it no longer has
to be conceded from the floor. Both statements of the criterion in `msc-thesis`
Chapter 9 were rewritten, and the order of the six rows was not touched:

* the introducing sentence of "Recommendations for Future Research" now reads
  "ordered by how much of the uncertainty in the four answers each would remove,
  which is not the ordering by the width of the bracket each addresses. Ranked by
  the absolute probabilities alone, the fourth item would lead";
* the caption of Table `tab: future research` now reads "ordered by how much of the
  uncertainty in the four answers each would remove, not by the width of the bracket
  each addresses".

The two criteria are therefore named as different and the ordering under which item
4 leads is stated by the document rather than by the candidate. Rows 2 and 4 already
carried the reason in their own text ("the range is already established"; "what a
determination would supply is a narrowing of the bracket and not a first
quantification of it"), and that text is unchanged. **The safe form of words above is
still the right answer to give; it is now a pointer to a printed sentence and not a
concession.** The reordering option was considered and refused: item 1 is the one the
chapter develops in its own subsection and the one that can overturn a headline
answer rather than narrow it, so promoting the conductivity item would have created
the mirror-image question and contradicted `subsec: A Migration-Capable Bank-Retreat
Model`, which calls the bank-retreat mechanism "the single most consequential
extension available to the integrated framework".

**If asked what a single six-month project should be**, the defensible answer is
item 4 followed by item 1, because item 4 is the only one whose absence puts a
three-order-of-magnitude band around every number in the document, and item 1 is
the only one that can overturn a headline conclusion rather than narrow it.

**Evidence.**
- Thesis Ch. 9, "Recommendations for Future Research"; Table `tab: future research`;
  `subsec: A Migration-Capable Bank-Retreat Model`.
- Thesis Ch. 8, `subsec: What Remains Statistically Unresolved`.
- Engine: `docs/decisions/r10-foreshore-exhaustion-screening.md` (the indicator that
  already exists and what it can and cannot do); ADR-0048 and ADR-0050 for items 4
  and 2.

---

## Summary of the entries marked as known exposures

Two, as of 2026-08-23. The table held three when this brief was written.

| # | Exposure | The safe form of words |
|---|---|---|
| Q6 | The corrected fluvial-scour branch has no independent validation; its equivalence gate tests it against the received implementation only. | "The zero belongs to the model and its inputs, not to the conditioning. What is established is that it is not an artifact of the conditioning." |
| Q10 | The compound-event memory model is untested against field observation and cannot be tested with a survival record. | "Bounded in the conservative direction, subordinate to duration in the measured attribution, and not validated." |

**Removed 2026-08-23.** Q12, the future-research register's unstated ordering
criterion, is closed: Chapter 9 now states the criterion in both the caption and the
introducing sentence and names the ordering under which the conductivity item would
lead. The Q12 discussion above is left in place with a dated note; only the row is
gone.

## Three results to lead with when given the chance

1. **The static-transient difference at design levels is not a duration credit, and
   that was measured rather than assumed.** The head convention accounts for three
   quarters to 97 per cent of it; pure duration is bounded at one to about six
   wherever the counts support the statement. The thesis set out to measure the
   duration credit and reported that most of what it found was not one.
2. **A peak-referenced survival update, which is what current probabilistic
   assessment instruments prescribe, over-rejects by 1.45 to 3.90 on the one record
   the field supplied, in the unsafe direction under either canonical event.**
   Method against method, on one sample.
3. **Whether an epistemic bracket cancels in a comparative claim is a property of
   the model structure, not of the input, and it must be established input by
   input.** Four worked cases, a predicted-then-measured test, and a
   counter-example (`m_p`) that cancels exactly as the rule says it must.
