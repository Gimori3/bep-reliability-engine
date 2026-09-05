# Examiner red team, 2026-09-03 (closed 2026-09-04)

**Status.** All fifteen attacks are answered on the page, and **three of the five residues
are closed too**. The seven attacks that were not answered (six ANSWERED BUT BURIED, one
NOT ANSWERED) were closed by eight prose additions; residues R1 to R3 were closed on
2026-09-04 by three further additions. All eleven were paid for by twelve measured
restatements in the same chapters, at **zero page cost**: the main body stands at 99 pages
with References on 100, chapter for chapter identical to the pre-edit baseline, on 774
labels and 815 citation instances also identical to it. Section 2 lists the additions,
Section 4 the offsetting cuts and the seven-build page-count proof, and Section 3 the
residues, of which R4 and R5 remain open by construction. The R1 to R3 record is
`docs/decisions/examiner-residues-closed-2026-09-04.md`.


**What this is.** An adversarial reading of `msc-thesis` as it stands
on 2026-09-03, after the shortening campaign closed at 99 pages and after the three
reviewer-triage work packages of 2026-08-29 landed
(verdicts and execution recorded in `docs/project_log.md`, entry of that date). Fifteen
questions a committee could actually land, ranked by the damage an unanswered version
would do; for each, where the answer already lives, verbatim; a grade; and, where the
grade was ANSWERED BUT BURIED or ANSWERED ONLY IN AN APPENDIX, the smallest edit that
moves the answer to where the objection forms.

**Relation to `defence_brief_2026-08-22.md`.** That brief predates the RQ1
reliability-index campaign (2026-08-28), the equal-head-convention comparison
(ADR-0051), the terminology/evidence audit (2026-08-29) and the shortening campaign
(2026-09-02). Its twelve questions remain sound; six of them recur here in sharpened
form (Q2 to A2, Q3 to A7, Q4 and Q6 and Q7 to A1, Q5 to A4, Q8 to A5, Q9 inside A4).
Nine of the fifteen below are not in it. Where the two disagree on a number, this one
is later and was checked against the current source.

**Honesty rule.** Every quotation below is verbatim from the current source. Where the
thesis cannot support a confident answer, the entry says so and the residue is listed
in Section 3 with what evidence would close it. Nothing was weakened to deflect an
attack; where a claim is already correctly hedged it is left alone and the hedge's
justification is what moved.

---

## 1. The fifteen attacks

### A1. "Piping dominates at four segments out of 114, both of your top two are evaluated as if drains that exist were absent, your scour branch returns identically zero, the mechanism your own basin record blames is not in the model at all, and your conductivity bracket spans three orders of magnitude. What is the dominance claim worth?"

**Grade: FULLY ANSWERED IN PLACE, and volunteered.** This is the hardest question in the
defence and the thesis answers every prong of it before being asked. The answer is not
that the objection fails; it is that the claim has already been narrowed to exactly
what survives.

*Coverage.* Ch. 7, `subsec: Extent of the Mechanism Comparison`: "of the 114 evaluation
segments exactly four carry a piping branch... Their annual probabilities are therefore
explicit lower bounds on the system quantity, missing a mechanism entirely rather than
estimating it as small, and no statement about relative dominance is available at any of
them." And the circularity is conceded rather than defended: "That coincidence is not
evidence that the uninvestigated segments are safe. It is a direct consequence of the
coverage pattern: the piping branch is the largest contributor wherever it exists, and it
exists only where a borehole program happened to be run."

*The zero scour branch.* Ch. 8, `subsec: The Surface-Mechanism Model Set`: "Because the
composition attributes to piping essentially whatever is not attributed to overflow, a
branch contributing nothing mechanically inflates the piping share. Two levees in this
system failed by erosion in 2016, so a model returning identically zero is not describing
the world... Piping therefore dominates *among the mechanisms represented*, and the
represented set omits the mechanism with the strongest empirical claim to having caused
failure here."

*The drains.* Ch. 7 conditions register, "Remediation state not credited": the annual
system probability falls from 7.4e-3 to 4.2e-3 at KP 58.8 and 1.8e-3 to 6.4e-4 at
KP 60.0 on the measured berm alone.

*The bracket.* Ch. 7, `subsec: Dominance and the Conductivity Bracket`: "Under the
conservative reading piping's lead survives it at one of the four sections in the
historical climate and at none of the four under warming... Across the two readings
together no cell keeps its leading mechanism." Then the defence: "The bracket is
two-sided, the production configuration sits inside it and not at either end, and its
upper arm strengthens the lead rather than weakening it."

*The answer to give.* The dominance claim is worth exactly this: at the only four
segments where the question can be posed at all, under the conservative gradation and at
the adopted conductivity, piping carries 70 to 100 per cent of the summed annual
contribution; the ordering is contested at the low end of a two-sided bracket whose
centre and upper end support it; and the represented mechanism set omits bank retreat, so
the share is an upper bound on piping's true share among all mechanisms. Every one of
those five qualifications is printed.

**Edit made.** One prong was answered only in Chapter 8 and not where the shares are
first stated. The commensurability asymmetry (eight stochastic inputs and two brackets on
the piping branch against three published terms and none on overflow, in a range where
wider uncertainty raises a computed probability) appears in the Summary, in Ch. 8
`subsec: Commensurability of the Mechanism Probabilities` and in Ch. 9, but is **absent
from Chapter 7's eight-row standing-conditions register and from the paragraph that
states the shares.** One sentence added at the end of Ch. 7 `subsec: Piping Dominates`:

> They are also shares between branches computed to different completeness, only the
> piping one carrying an epistemic bracket, and in this range a wider uncertainty raises
> a computed probability (Section~\ref{subsec: Commensurability of the Mechanism
> Probabilities}).

---

### A2. "Your static comparator uses the gross head, which you concede no assessment instrument applies. Is the whole comparison against a straw man?"

**Grade: FULLY ANSWERED IN PLACE.** The thesis makes this its own finding rather than a
concession, in four places, and quantifies the alternative.

*Why the gross head.* Ch. 4, `sec: Static Limit State: Sellmeijer Steady-State Benchmark`:
"The gross-head form is retained as the production comparator because that reduction is a
resistance internal to the transient formulation, and crediting the steady-state rule
with it would give the rule a resistance its own calibration does not contain... The
status of the term is that of an assessment convention rather than a term either author's
calibration contains, and this thesis treats it as contested for that reason."

*The provenance is traced, not asserted.* Appendix H, `app subsec: Crack-Resistance
Provenance`: "The term is not part of \textcite{sellmeijer_2011}'s own calibration: that
rule is fitted throughout on the gross head and carries no crack, blanket or cover head
loss in any form... No step in that chain is a calibration against erosion experiments."

*The number against the instrument's own comparator.* Ch. 6, `subsec: The Production Gap`:
against the crack-reduced variant C1 "it resolves at neither design level, on four,
fifteen and zero failing transient realizations, and where the counts do support the
comparison the factor against it runs from 6.0 at 47.00~m to 1.4 at the top of the
attainable range at KP~62.0, and from 3.9 at 39.50~m to 1.0."

*And the fair-footing deliverable.* Ch. 6, `sec: The Two Criteria on One Head Convention`,
Table `tab: equal convention`: reading both criteria on the identical raw gross head
retains 63 to 83 per cent of the as-published Δβ, "with KP~57.4 at most 66~per cent
because its denominator in the table is the bound". And the honest non-uniqueness: "There
is no unique equal convention... At KP~62.0 the two readings agree within 24~per cent...
at KP~57.4's thin-count design level they diverge, 23.1 against 12.0 on two realizations,
so the honest statement there is a band of roughly 5 to 23."

*The answer to give.* No, because the comparison is run on both conventions and both are
reported. The gross-head baseline is the calibrated rule; the crack-reduced variant is the
instrument; the equal-convention comparison removes the contested term from both sides.
Under the last of these the time dimension and the initiation gate alone are still worth
Δβ 0.57 to 1.55 at the four design levels. The straw-man charge would land only if the
26.9 were quoted alone, and the Summary's third paragraph already carries the equal-head
retention beside it.

---

### A3. "Your headline result is that a transient criterion gives lower failure probabilities than a static one. You say yourself the direction is a theorem. What did you actually find?"

**Grade: FULLY ANSWERED IN PLACE.** Stated four times, at the right four places, and
since 2026-08-29 stated before any result rather than after.

Ch. 4, `sec: Transient Limit State`, before any number: "a transient breach requires the
erosion head to exceed the same critical head the static rule compares against, and it
does so on the smaller of the two driving heads of Table~\ref{tab: head conventions}, so
the transient failure set is contained in the static one by construction, for every
realization and every loading."

Ch. 6, `sec: Prior BEP Fragility Curves`: "That ordering is guaranteed by the formulation
rather than tested by it... what is measured here, and could not have been derived, is how
large the separation is and how it is composed."

Ch. 8 opening: "its direction is a theorem of the nested formulations, and only the size is
a finding."

*The answer to give, in one breath.* Four things were found that could not have been
derived. First, the size and its section-dependence: Δβ 0.90 [0.85, 0.97] at KP 62.0's
design level, at least 1.27 at KP 57.4, 1.22 and 1.87 at the drained sections, spanning
0.9 to 1.9 in index terms against more than fiftyfold in probability terms, and ranking the
sections differently on the two metrics. Second, the composition: at KP 62.0's design
level the additive ladder is head convention 0.36, gate exactly 0.00, temporal 0.55, so
duration is the larger of the two surviving terms in index space while accounting for only
a factor of one to about six in probability space. Third, the direction of variation with
severity: B decays by a factor of 29 to 269 toward parity while Δβ is U-shaped and peaks at
the top of the attainable range, which is the opposite reading of "most conservative at
design levels". Fourth, and methodologically the most transferable, that the comparison's
epistemic brackets do not cancel (A4).

---

### A4. "Your bulk horizontal conductivity is contradicted from both sides by measurement, you keep the contradicted mean, and the bracket spans three orders of magnitude in predicted probability. Is any absolute number in this thesis quotable?"

**Grade: FULLY ANSWERED IN PLACE.** Ch. 5, `sec: The Aquifer Conductivity Prior under
Scrutiny` is written as the answer to this question and Ch. 6 and Ch. 7 carry it forward
as a standing condition on every number.

*Why retained.* "Neither population estimates the bulk horizontal conductivity the seepage
path requires: the single-borehole test is biased low, the analysis constant was chosen
high, and the regional band belongs to a different setting."

*Where production sits, stated against the candidate's own interest.* "At KP~62.0 the
position is worse than mid-range: production sits at 26~per cent of the logarithmic
failure-probability bracket at the design level, with an upside of roughly three orders of
magnitude if the regional band is right, against a downside of a factor of 15 if the field
population is. Reading only the field-test scenarios would license the comfortable and
wrong conclusion that the adopted prior is conservative."

*The comparative claims do not escape it either, and that was tested rather than assumed.*
"it was supposed that displacing the conductivity mean would move both limit states
together and largely cancel... Run at all four characterized sections and at every
conditioning level, it fails... Two of its three channels are transient-only, so it could
not have canceled... the comparison does not merely fail to cancel, it amplifies."

*What is quotable.* Ch. 6 opening: "Every absolute probability is conductivity-conditional;
every ratio is additionally conditional on the adopted seepage lengths, canonical event and
critical pipe length." And the one register in which the band is not overwhelming: "In
reliability-index terms the same KP~62.0 arms span $\Delta\beta$ 0.86 to 0.97, comparable
in width to the anchor's own statistical interval $[0.85,\ 0.97]$: the band does not shrink
under the re-expression, but its size relative to what it brackets does."

*The answer to give.* Absolute probabilities are quotable only with the bracket, and the
thesis never quotes one without it. Comparative claims in index terms are quotable with a
band comparable to the statistical one. The single measurement that would change this is
named as recommendation four, and the defence brief's own caveat applies: concede the
ordering criterion of the future-research register rather than defend the rank.

---

### A5. "You report a plane-strain exponent as your baseline and admit that at the three-dimensional exponent your gap nearly vanishes. Why is the baseline the one that flatters your result?"

**Grade: FULLY ANSWERED IN PLACE.** Three independent defences, all printed, and the
adverse number is given without softening.

Ch. 6, `subsec: The Dimensional Axis`: "the step alone is $-0.43$ at 47.00~m and $-0.47$ at
48.00~m at KP~62.0 and $-0.50$ at 40.50~m at KP~57.4, all resolved... Under a fully
three-dimensional reading of the resistance scaling, in other words, most of the static
margin disappears."

Then: (i) "Under the bulk grain-size reading... the dimensional component reverses sign,
reaching $+0.37$... because the scale group in the critical-head expression crosses unity
at coarse gradations"; (ii) "at KP~57.4 and KP~62.0 both gradation readings lie outside the
grain-size range over which the static rule was calibrated"; (iii) "the plane-strain anchor
the two production branches share is the baseline the progression model's author endorses
for a two-dimensional Sellmeijer-based model at blanket thicknesses such as these."

There is also a structural reason the committee will not have anticipated, in Ch. 4: the
exponent is absent from the production comparison **by construction**, because both
branches share one critical head. Making it differ between branches is the one place the
single-source contract is deliberately relaxed, and it is relaxed only inside the
decomposition.

*The answer to give, and the brief's wording is right:* do not say the 3D reading is wrong.
Say it is unadopted, measured at every stage, sign-unstable across the gradation bracket,
out of calibration domain at half the sections, and endorsed against by the progression
law's own author for this configuration.

---

### A6. "Your grain sizes are outside the calibration range of the resistance rule at three of four sections. Why should I believe any absolute number?"

**Grade: ANSWERED BUT BURIED.** The applicability argument is complete, and it is the best
answer in the thesis to a hostile question, but it lives in Ch. 2 and Ch. 3 and is not
restated where the absolute numbers are quoted.

Ch. 2, `subsec: The Dutch Progression-Based Sellmeijer Model`: "The regression behind the
rule was fitted on sands of experimental mean diameter 0.208~mm, with a validated range
reaching 0.430~mm, and three of the four study cross-sections lie above that range even on
the finer of the two readings... **Selecting a different formulation would not avoid the
limit, the alternatives being calibrated on the same experimental base or on none.** It is
carried explicitly instead, as two co-primary gradation readings whose separation measures
how far the rule may be trusted."

Ch. 3, `subsec: Model Applicability at Gravel Grain Sizes`, per section: "KP~60.0 lies
inside the validated range, KP~58.8 stands 23~per cent above its 0.430~mm upper limit, and
KP~57.4 and KP~62.0 stand 63~per cent above it."

Ch. 6, `subsec: The Tail and the Grain Size Bracket` gives the bracket's width, one-sidedness
and irreducibility, and ends on the right note ("Choosing between the readings requires
judging the applicability to gravel of a grain-stability rule calibrated on sand, not
further Monte Carlo sampling") but never states that the reading behind every printed
number is itself out of domain at three of four sections. Ch. 9's Overall Conclusion does,
in its last sentence, ninety pages later.

**Edit made (addition 7).** One clause appended in Ch. 6,
`subsec: The Tail and the Grain Size Bracket`:

> ...not further Monte Carlo sampling, and three of the four sections stand above that
> calibration range on the matrix reading itself.

It cost Chapter 6 a page on first measurement and was paid for by cuts C6 to C9 of
Section 4.

*The answer to give.* Because no formulation avoids the limit, the study does not choose;
it reports both admissible readings as co-primary and lets their separation measure the
model risk. The separation is large and it is stated as such: 1.3 to 5.2 m of upward shift
at a conditional probability of 1e-1, and a reversal of the dominance ordering at two of
four sections historically.

---

### A7. "Your Bayesian update rejects nothing the static criterion does not. Isn't Phase 2 a null result?"

**Grade: FULLY ANSWERED IN PLACE.** Ch. 6, `subsec: How the Constraint Divides` names the
objection and answers it in both directions:

"This is a positive result, and reading it as a null one would be a mistake in both
directions. Its first consequence is a constraint on what may be claimed: at these sections
and under this loading, the 2016 survival adds no rejection beyond what the static criterion
already delivers, so the prior-to-posterior shift cannot be presented as evidence for the
time-dependent mechanism specifically. Its second consequence is what the transient
criterion does contribute, which is the calibration of the rejection and not its
membership."

Then the substantive finding: "the static comparator asserts that 58~per cent of the prior
at KP~58.8 and 73~per cent at KP~60.0 should have failed at a load the levee demonstrably
survived, while the transient model asserts that 5.7 and 3.4~per cent should have."

*And the obvious follow-up is pre-empted.* "The drainage confound above does not rescue it.
The toe drain acts on the initiation gate alone, under which the static branch is exactly
invariant, and crediting the measured post-works berm still leaves the static comparator
condemning 34~per cent of the prior at KP~58.8's observed peak against 5.4~per cent for the
transient one, so the discrepancy widens across the drained bracket rather than closing."

*The non-null half.* The measured, non-zero Phase 2 result is the peak-only over-rejection
(A12), which is method against method on one sample and is the finding with the clearest
implication for practice.

---

### A8. "Every transient probability in this thesis is conditioned on one hydrograph out of three thousand. How was it chosen, and is your finding that duration matters simply a consequence of choosing a long wave?"

**Grade: the *sensitivity* is ANSWERED IN PLACE; the *selection* was NOT ANSWERED. Closed
by edit from a named engine artifact.**

The sensitivity is thorough. Ch. 6, `subsec: What the Replay Adds`, measures the whole
conditioning sweep on the alternate approved member at full production sample size: "at the
middle of each curve it lowers the transient failure probability by 24 to 42~per cent, at
all eight strata, with no exception in sign", and raises the drained-section design-level
factors from 2.75 and 2.92 to 4.87 and 6.03. And the invariance half is stronger still:
"every static probability in this thesis, together with the critical head, the critical pipe
length and the response factor, is the same number under any canonical event whatever. Six
of the ten comparators... The survival update is untouched for a different reason: its
rejection fractions... are computed against the reconstructed 2016 record and never against
a canonical event."

The second prong is also answered, in Ch. 8 `sec: The Time-Dependent Race Condition`:
"measured at the timescale governing pipe progression the Tokachi flood is not flashy...
That is why the measured duration factors sit at the low end of what a progression-based
framework predicts: the race is close at these sections not because the flood is brief but
because the seepage paths are short and the aquifer coarse."

**What was missing.** Ch. 4 said only that the production member is "a real, pinned ensemble
event" and "a compound, multi-peak member of the historical ensemble". No selection
criterion appeared anywhere in the document, and Appendix H's canonical-event provenance
compares the two approved members to each other but never to the ensemble. A committee that
asks "how did you pick it, and did you pick the one that gives your answer?" would have got
no printed reply.

**Edit made (addition 6), and it is the most important one in this pass.** Source:
`docs/decisions/0023-shape-invariant-climate-axis.md` ("the production canonical shape
HPB_m064_1987 (t50 = 55 h, 2 significant peaks, trough 0.498) sits in the ensemble's upper
duration quartile"; HPB median t50 40 h [32 to 54]; compound fraction 9.6 per cent over the
3,000 historical members). It replaces the paragraph's closing restatement in Ch. 4,
`subsec: Conditioning Sweep and the Canonical Hydrograph Shape`:

> The compound member is pinned for its structure, not its size: it sits in the upper
> duration quartile of the ensemble's normalized shapes and among the roughly one member in
> ten carrying a second peak, so the conditioning is realistic compound loading that
> exercises the cumulative-memory formulation rather than a synthetic design wave that
> avoids it.

It cost Chapter 4 a page on first measurement and was paid for by cuts C1 to C5 of
Section 4. **The 55-hour half-amplitude width and the two-peak structure of this member were
already printed in Appendix H; what is new is the comparison against the ensemble, so the
author should confirm the quartile and the one-in-ten fraction against ADR-0023 before
submission.** This is the only statement the thesis gained in this pass that it did not
previously make somewhere.

*The answer to give.* The member was pinned to exercise the compound-memory formulation,
not to flatter a result, and the direction of that choice is against the headline: a longer
conditioning wave raises the transient probability and therefore **narrows** the
static-to-transient gap. The shorter approved member widens Δβ by 0.41 and 0.54 at the two
drained sections. The 55-hour half-amplitude width of the member in use is already printed
in Appendix H; the ensemble comparison is now printed in Ch. 4.

---

### A9. "The entire out-of-sample support for your progression physics is one flood at three sites on a different river, where you assign 6 per cent to a section that actually breached. That is not support."

**Grade: ANSWERED BUT BURIED (in Ch. 5 and the Summary; the hedge was missing from the
Overall Conclusion).**

Ch. 5, `subsec: The Transient Race Condition Has Field Support`, is exemplary: "One case
cannot establish the claim, and neither exercise below is treated as doing so... What is
reproduced is the ordering. A probability of 0.061 at a site that did breach is not in
itself a confirmation of the magnitude, and three sites under one flood cannot supply one."
And the timeline half is hedged harder still: "The outcome is therefore that the rate law is
not refuted by the one clock available, across a permeability range the committee itself
documents, rather than that it agrees with it: a band that wide is a weak constraint."

The Summary carries the hedge, since the 2026-08-29 pass: "A single out-of-sample case is
consistent with the progression physics, reproducing an ordering rather than confirming a
magnitude."

**Chapter 9's Overall Conclusion did not.** It called Yabe "the only occasion on which the
framework was asked to separate a real breach from real survivals", gave the three numbers,
and went straight to the discriminating claim. One clause added:

> What that reproduces is an ordering, not a magnitude, which three sites under one flood
> cannot supply.

*The answer to give.* The claim being made is discrimination, not calibration: initiation
indicators give 0.62 at the breached site and 0.65 at a surviving one and cannot separate
them, while the progression chain gives 0.061 against 0 in 1e5 and 0.005. That is an
ordering reproduced on one flood, and Chapter 5 is titled "field evaluation" rather than
validation precisely so this cannot be read as more.

---

### A10. "Chapter 5 concedes that what you did is not validation. On what authority do you then recommend changes to a national assessment standard?"

**Grade: FULLY ANSWERED IN PLACE, and the concession is volunteered in the chapter's own
opening.**

Ch. 5 opening: "It is not called a validation. Validation in its strict sense requires
measured system response quantities with quantified uncertainty on both sides of the
comparison, and this set contains none: there is no piezometry in it, its quantitative
references are other investigators' calibrated models, and what remains is outcomes, boils
or none and breach or none, at five sites in two river systems. Such evidence can refute a
schematization, and in one case here it does, but it cannot certify a framework. Every
finding below is accordingly a direction or a bound, not a measured model error."

*Why the recommendations survive that.* They are directional and each rests on something
other than the unvalidated magnitude. Ch. 8, `sec: The Initiation-Progression Distinction`:
"\textcite{fukuoka_2019} place the critical instant for embankment seepage after the
hydrograph peak through a recession formulation, and this work does so for foundation piping
through different physics. Two independent mechanisms displacing the critical instant
strengthen the case against peak-referenced assessment, the most transferable conclusion for
Japanese practice." And the screening recommendation is explicitly non-overturning: "The
results prioritize sections already admitted by the screen, not overturn it."

*The answer to give.* None of the four recommendations asks practice to adopt a number. They
ask for the recession rather than the peak (supported independently by a Japanese
peer-reviewed index on a different mechanism), for the screening rule and the reliability
statement to be kept apart, for the seepage path to be weighed where crest raising is
evaluated, and for above-toe duration to be carried in hazard characterization. Each is a
statement about what to measure, and none requires the transient magnitudes to be correct.

---

### A11. "Your answer to RQ4's first clause is a negative: the ensemble shows no elongation. But your own ensemble is extracted in a fifteen-day window around an annual-maximum rainfall date. Is the negative a property of the climate or of your extraction?"

**Grade: ANSWERED BUT BURIED (Appendix D and Ch. 8; the linkage to the negative finding
was never made).**

The limitation is documented. Appendix D, `app sec: Structure of the d4PDF Ensemble`: "The
15-day window is the origin of one limitation carried through this thesis: the ensemble is
constructed on an annual-maximum framework calibrated for peak discharge rather than for the
load duration that governs backward erosion piping, so a hypothetical long-duration event
whose peak falls outside the extracted window is not represented." Ch. 8,
`subsec: What the Framework Cannot Separate`, carries it, and the limitations register lists
it with "Quantified: no."

But both statements are about the **frequency of long-duration years**, and the elongation
finding is a statement about **normalized shape**. The two are never joined, so the negative
result, which is what licenses one conditioning shape for both climates and therefore the
whole Phase 3 climate architecture, is left standing without its own scope condition.

**Edit made.** Ch. 7, `subsec: What the Ensemble Shifts`:

> That is a property of the extracted ensemble, whose annual-maximum window is built around
> peak discharge rather than duration (Section~\ref{subsec: What the Framework Cannot
> Separate}).

*The answer to give.* The claim as printed is already scoped to "this ensemble for this
basin"; it is not a claim about the climate. The extraction is identical in both
experiments, so a window artifact would have to act differentially between them to
manufacture the invariance, and the measured difference runs the other way (the +4K shapes
are marginally *shorter*, not equal). What would settle it is an ensemble extracted on a
duration criterion, which does not exist for this basin.

---

### A12. "The peak-only over-rejection factor of 2.75 to 3.90 is the mismatch between your assumed conditioning wave and the real 2016 event. That is a statement about your canonical choice, not about the assessment instrument."

**Grade: mostly ANSWERED IN PLACE; the direction claim is a residue (Section 3, R1).**

The thesis concedes almost all of this before being asked. Ch. 6, `subsec: What the Replay
Adds`: "The mechanism is the shape of the loading, not its height. The prior curves condition
on the canonical compound ensemble shape scaled to each level, and that shape holds the
stage above the toe for far longer than the real 2016 event did at the same peak; a reading
that sees only the peak cannot tell the two apart." And: "the choice reaches the numerator
of the factor and not its denominator... The peak-only reading over-rejects under either
loading, and the direction of the error is therefore a property of the method; its size is a
property of the conditioning event as much as of the method, and is quoted here with the
event named."

The band is also correctly narrowed to the strata that can carry it: four of eight reject
nothing under either reading ("which is a different statement from agreement"), two more are
excluded as ratios of small counts.

*What does not fully close.* The direction is asserted as "a property of the method" on the
evidence of two conditioning events, both of which are longer than the 2016 record at the
same peak. If a conditioning event were shorter than the survival event, the peak-only
reading would under-reject. The claim's structural half is sound (a peak reading carries no
duration information at all, so it can be right only by accident), but the *sign* is
established empirically on two members and generalized. See R1.

*The answer to give.* The size is event-conditional and is quoted with the event named; the
direction is established on both approved members and is what a duration-blind reading of a
duration-governed mechanism should be expected to produce, since the conditioning event in
any real assessment is a design-like wave and the survival is whatever the field supplied.
Do not claim the direction is a theorem.

---

### A13. "Your model makes KP 62.0 the most resistant of the four on a common load-excess axis. The only site-specific assessment ever performed at these sections rated it among the worst, at an exit gradient of 0.97. You are motivated by that assessment and you contradict it."

**Grade: ANSWERED BUT BURIED (the two halves are in Ch. 3 and Ch. 6 and are never joined).**

Ch. 3, `subsec: Per-Section Stratigraphy`: "KP~62.0's 0.45~m blanket gives it the worst-case
configuration for initiation among the confined sections, consistent with its failing 1998
uplift and gradient ratings. The blanket thickness alone accounts for this, and it acts in
both directions. The same thin, conductive $A_c$ that minimizes the uplift and heave
resistance also shortens $\lambda_\mathrm{in}$, so it gives KP~62.0 the lowest response
factor of the four and transmits the *least* head to its toe, not the most."

Ch. 3, `subsec: The 1998 Deterministic Safety Evaluation`, on the criterion: "The 1998
evaluation used the uncovered-case criterion at every section, including the four with a
0.45 to 0.85~m blanket, so the uplift condition that the initiation gate of
Chapter~\ref{chap: Methodology} represents went unverified under either framework."

Ch. 6, `subsec: Section Contrast Is Geometric`, on the model's own ordering: "KP~62.0 is
displaced from that cluster by about 1.1~m on the static branch and 1.5~m on the transient
one... Its seepage path is the longest of the four at 40~m... and its confining blanket is
the thinnest at 0.45~m."

And Ch. 6 on why the two orderings need not agree: "Initiation is therefore not the
controlling sub-mechanism at any of the four sections, and the margin that governs is the
progression margin."

**Edit made (addition 8).** The reconciling clause was added one sentence from where the
reader forms the objection, in Ch. 6 `sec: Prior BEP Fragility Curves`:

> ...and the margin that governs is the progression margin, so the 1998 exit-gradient
> ordering, a judgment on that gate alone, does not carry over to these curves.

Paid for by cuts C6 to C9 of Section 4.

*The answer to give.* There is no contradiction, because the two assessments judge different
stages of the same chain. The 1998 rating is an initiation judgment, computed with the
no-cover criterion at sections that have cover, and this work finds initiation
non-controlling at all four. On initiation the model agrees with 1998: the 0.45 m blanket is
the worst configuration of the four. On progression it disagrees, and the reason is the same
geometry read at the other end, the thin blanket also giving the section the lowest response
factor and the longest path giving it the highest critical head.

---

### A14. "Under warming you report annual failure probabilities of order one per cent per year at every characterized section, and you refuse to compare them with any acceptability benchmark. Are those numbers credible?"

**Grade: ANSWERED BUT BURIED.** The credibility check exists, is a good one, and is
performed only on the historical numbers and only in Chapter 8.

Ch. 8, `subsec: The Erosion-Limited Consensus`: "Composed independently in series, the four
characterized segments carry an annual piping probability of $1.07\times10^{-2}$ in the
historical climate on the as-if-undrained deliverable. Across the sixty years since the 1966
basic plan fixed the present design level, that gives 0.65 expected failures and a
probability of 0.52 that none is observed; crediting the measured berm gives 0.38 and 0.68.
The one event the field supplied reads the same way: at the stages 2016 reached the transient
model assigns 0.089 to the failure of at least one of the four, so the observed survival is
the modal outcome under the model rather than an observation it has to accommodate."

The refusal to benchmark is deliberate and stated: Ch. 7, `subsec: The Climate Ratios`: "No
acceptable-probability benchmark is adopted anywhere in this thesis, so these values are read
against one another, against their own climate counterparts and against the conditional curves
they come from, and never against a target."

**Edit made.** A pointer at the place the objection forms, Ch. 7 `subsec: The Climate Ratios`:

> Their historical counterparts are set against this reach's own sixty-year failure record in
> Section~\ref{subsec: The Erosion-Limited Consensus}.

*The answer to give.* The historical numbers pass a record check that a much larger set would
fail: 0.65 expected failures in sixty years against zero observed, and 2016 itself as the
modal outcome. The warming numbers are that same model under a lifted hazard, and they carry
three separate reductions on the table: the drained bracket (0.57 and 0.35 on the measured
berm alone at the two largest), the gradation bracket (a factor of 1.5 to 37), and the
conductivity bracket. *Concede without argument* that the record check is a consistency
test and not a discriminating one: a model with half or twice this probability would also
pass it.

---

### A15. "You re-measured the seepage length from 2025 lidar, adopted the new value at exactly the section where it raises your headline probability by an order of magnitude, and kept 1998 values everywhere else. On what principle?"

**Grade: ANSWERED BUT BURIED (Ch. 3 gives the principle for KP 62.0 and KP 57.4 only; the
direction at the other two is in Ch. 8 and Ch. 5).**

Ch. 3, `subsec: Definition and Determination of the Seepage Length`, on the adoption: "That
departure is a correction, not an update: the 1998 reading of 47~m credited a landside berm
that has never existed. A longer path suppresses both the initiation gradient and the
pipe-growth criterion, so the error lay in the unconservative direction at that section." And
the figure caption on KP 57.4: "the nominal station falls on a road interchange embankment and
no adoptable value is resolved."

Ch. 8, `subsec: What the Model Represents`, gives the missing halves: "the 2025 surface gives
42 and 43~m against the 35 and 34.8~m of the 1998 tables, at 31 of 31 usable stations in each
case", the difference being the enlargement works.

Ch. 5, `sec: The Aquifer Conductivity Prior under Scrutiny`, confirms the alternative is
carried, not discarded: "The seepage-length arm sets each adopted length against its unadopted
counterpart, the 2025 measurement at the three sections that retain the 1998 footprint and the
withdrawn 1998 value at KP~62.0... and it displaces the ratio by factors of 1.02 to 3.22 at
every one of the 87 levels."

**Edit made.** Ch. 3, immediately after "The other three sections retain their 1998 values":

> At KP~58.8 and KP~60.0 the retained value is the shorter of the two available readings, the
> 2025 surface giving 42 and 43~m there because the enlargement works lengthened the path
> (Section~\ref{subsec: What the Model Represents}), so the retention is the conservative
> choice; the unadopted readings are carried as a bracket
> (Section~\ref{sec: The Seepage-Length Model under Scrutiny}).

*The answer to give.* The principle is: adopt where the old value is *wrong*, hold where it is
merely *old*. At KP 62.0 the 1998 figure credited a berm that the surface shows has never
existed, and correcting it moved the number against the study's own interest. At KP 58.8 and
KP 60.0 the two readings differ because the 1999 to 2003 works genuinely lengthened the path,
so the 1998 figure describes the unremediated configuration the whole analysis is conducted on,
and it is the shorter and therefore the more onerous of the two. At KP 57.4 no adoptable
station exists. In all three retained cases the unadopted reading is carried as the
seepage-length bracket and reported as not cancelling in the comparison.

---

## 2. Edits taken

**All eight additions are in the document, at zero page cost.** The author authorised
offsetting concision on 2026-09-04; the three that had been priced at a page each were
paid for out of six measured restatements in the same two chapters. The main body stands
at 99 pages with References on 100, chapter for chapter identical to the pre-edit
baseline. No number, `\label` or citation key changed: both builds define 774 labels and
815 citation instances, and both carry zero overfull `\hbox` and zero underfull `\vbox`.
No result, figure, interval or caveat left the document.

| # | File and place | What it closes | Status |
|---|---|---|---|
| 1 | Ch. 3, `subsec: Definition and Determination of the Seepage Length` | A15, direction of the retained 1998 lengths | taken |
| 2 | Ch. 7, `subsec: Piping Dominates` | A1, commensurability asymmetry at the shares | taken |
| 3 | Ch. 7, `subsec: What the Ensemble Shifts` | A11, scope of the elongation negative | taken |
| 4 | Ch. 7, `subsec: The Climate Ratios` | A14, pointer to the record check | taken |
| 5 | Ch. 9, Overall Conclusion, Yabe paragraph | A9, ordering-not-magnitude hedge | taken |
| 6 | Ch. 4, `subsec: Conditioning Sweep and the Canonical Hydrograph Shape` | **A8**, canonical-member selection criterion | taken, paid for in Ch. 4 |
| 7 | Ch. 6, `subsec: The Tail and the Grain Size Bracket` | A6, calibration domain at the printed numbers | taken, paid for in Ch. 6 |
| 8 | Ch. 6, `sec: Prior BEP Fragility Curves` | A13, the 1998 ordering is an initiation judgment | taken, paid for in Ch. 6 |

Additions 6 to 8, verbatim:

6. Ch. 4, replacing "The fragility curves are therefore conditioned on realistic compound
   loading rather than a synthetic design wave.":
   > The compound member is pinned for its structure, not its size: it sits in the upper
   > duration quartile of the ensemble's normalized shapes and among the roughly one member
   > in ten carrying a second peak, so the conditioning is realistic compound loading that
   > exercises the cumulative-memory formulation rather than a synthetic design wave that
   > avoids it.

   It lands in the paragraph that introduces the pinning and immediately before "The pinned
   member therefore reaches the results through one channel only", so the objection and its
   answer are now adjacent. Quantities from ADR-0023, as quoted in A8.

7. Ch. 6, extending the paragraph's closing sentence:
   > ...not further Monte Carlo sampling, and three of the four sections stand above that
   > calibration range on the matrix reading itself.

8. Ch. 6, extending the initiation sentence:
   > ...and the margin that governs is the progression margin, so the 1998 exit-gradient
   > ordering, a judgment on that gate alone, does not carry over to these curves.

The five taken in the first pass, verbatim:

1. Ch. 3, after "The other three sections retain their 1998 values.":
   > At KP~58.8 and KP~60.0 the retained value is the shorter of the two available readings,
   > the 2025 surface giving 42 and 43~m there because the enlargement works lengthened the
   > path (Section~\ref{subsec: What the Model Represents}), so the retention is the
   > conservative choice; the unadopted readings are carried as a bracket
   > (Section~\ref{sec: The Seepage-Length Model under Scrutiny}).

2. Ch. 7, ending the shares paragraph:
   > They are also shares between branches computed to different completeness, only the
   > piping one carrying an epistemic bracket, and in this range a wider uncertainty raises
   > a computed probability
   > (Section~\ref{subsec: Commensurability of the Mechanism Probabilities}).

3. Ch. 7, after "not present in this ensemble for this basin.":
   > That is a property of the extracted ensemble, whose annual-maximum window is built
   > around peak discharge rather than duration
   > (Section~\ref{subsec: What the Framework Cannot Separate}).

4. Ch. 7, closing the no-benchmark paragraph:
   > Their historical counterparts are set against this reach's own sixty-year failure
   > record in Section~\ref{subsec: The Erosion-Limited Consensus}.

5. Ch. 9, inside the Yabe paragraph of the Overall Conclusion:
   > What that reproduces is an ordering, not a magnitude, which three sites under one flood
   > cannot supply.

Every fact in the five is already stated elsewhere in the document; the 42 and 43~m in
edit 1 are Chapter 8's own measurement, quoted there against "the 35 and 34.8~m of the 1998
tables".

---

## 3. Residue

**R1 to R3 were closed on 2026-09-04**, on the author's instruction to pursue them. Full
record: `docs/decisions/examiner-residues-closed-2026-09-04.md` and its JSON. None needed a
new sweep, module, config field or ADR. Summaries below; R4 and R5 stay open by construction.

### R1. The direction of the peak-only over-rejection. CLOSED, premise refuted

The residue held that the direction claim was generalized from two conditioning events both
*longer* than the 2016 record, so the sign would reverse for a shorter one, and recommended
a third short-tail member. **No third member is needed: the alternate approved member
already is the short-tail member, and it is already shorter than the survival event where it
matters.**

Recomputing ADR-0023's diagnostic over all 3,000 HPB members reproduces it exactly (t50
median 40 h, IQR [32, 54], peaks 1/1.10, compound 9.6 per cent) and places the alternate at
**t50 quantile 0.005**, the lowest half per cent, against an ensemble minimum of 17 h to its
own 21 h. Counted on one rule, with the real record reproducing the thesis's own 9/24/31/6 h:

| Section | Real 2016 above toe | Production | Alternate | Factor, prod. | Factor, alt. |
|---|---|---|---|---|---|
| KP 58.8 | 24 h | 60 h (2.50x) | **23 h (0.96x)** | 2.749 | **1.448** |
| KP 60.0 | 31 h | 62 h (2.00x) | **26 h (0.84x)** | 3.899 | **1.568** |

The two members therefore **bracket** the survived loading's own above-toe duration, and the
peak-only reading over-rejects on all four arms. The direction is not an artefact of a longer
conditioning wave. The mechanism: above-toe duration is not what the barrier charges in, a
pipe advancing only near the crest, and the real record spreads its above-toe hours over
sub-peaks far below its own crest while a rescaled canonical member concentrates them around
one. The bracketing is now printed in Ch. 6.

### R2. The power of the base-rate check. CLOSED, and favourably

With zero events in 60 years the one-sided 95 per cent Poisson bound is
`-ln(0.05)/60 = 4.99e-2` per year. So the record **excludes any annual probability above
about 5.0e-2 per year and excludes nothing below the reported value**: headroom 4.7x over
the as-if-undrained series (1.07e-2) and 7.8x over the berm-credited one (6.37e-3). The
asymmetry is the point, because the objection the check answers is "your probabilities are
implausibly high", which is the only side sixty years of zero observations can discriminate
on. The power statement is now in Ch. 8, one sentence.

### R3. The full erosion gate's decoupling justification. CLOSED as a deduction

It never needed a run. Under the Terzaghi substitution the heave threshold is a
deterministic function of *the same* sampled `gamma'_bl` that sets the uplift threshold,
which is exactly why `Z_heave = Z_uplift/D_bl` and the latch is redundant. Any decoupling
draws the gradient separately, and two independent draws cannot change sign at the same
instant except on a measure-zero set, so the latch binds wherever they separate. That is the
whole content of "load-bearing", and it follows from independence, not from an effect size.
ADR-0008 already recorded the displaced alternative (Pol's `i_c,h ~ Lognormal(0.7, 0.1)`),
Ch. 4 already carried the direction of the consequence (the sustain window the collapse
removes) and Appendix B already carried the spread comparison (0.143 against 0.056). Only
the reason was missing; Ch. 4 now states it. **No `i_c,h` knob was added**: it would be an
eighth random variable against ADR-0001's seven, a trade ADR-0008 weighed and refused.

### R4. The corrected fluvial-scour branch has no validation of its own

Carried forward unchanged from `defence_brief_2026-08-22.md` Q6, and still the correct safe
form of words: "The zero belongs to the model and its inputs, not to the conditioning. What is
established is that it is not an artifact of the conditioning." The thesis says exactly this
in Ch. 9. No edit needed; listed here so the defence does not treat it as closed.

### R5. The compound-event memory model is untested and cannot be tested with a survival record

Also carried forward from the brief, Q10, and still open by construction: a survival cannot
discriminate a memory assumption that only ever raises the computed probability. Ch. 5 and
Ch. 8 both say so. The mitigating measurement (compound stratification separates by 3.7 and
6.5 against 150 and 380 for duration, neither compound factor resolvably above one) is printed
in Ch. 7 and Ch. 8. No edit needed.

---

## 4. Page-count proof, and the nine restatements that paid for the additions

Method of record from the msc-thesis project: isolated copy of `report.tex`,
`tudelft-report.cls`, `references.bib`, `frontmatter/`, `mainmatter/`, `appendix/` and
`figures/` into a scratch directory, `latexmk -xelatex` run there, extents read from the
`\contentsline` entries of the fresh `.toc`, main body = (page of the References entry)
minus one.

**Five builds were run.**

| Build | Ch1 | Ch2 | Ch3 | Ch4 | Ch5 | Ch6 | Ch7 | Ch8 | Ch9 | Main body | Refs on |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline, pre-edit | 6 | 10 | 12 | 12 | 11 | 18 | 12 | 11 | 7 | **99** | 100 |
| All eight additions, no offsets | 6 | 10 | 12 | **13** | 11 | **19** | 12 | 11 | 7 | **101** | 102 |
| Additions compacted, no offsets | 6 | 10 | 12 | **13** | 11 | **19** | 12 | 11 | 7 | **101** | 102 |
| Five additions only | 6 | 10 | 12 | 12 | 11 | 18 | 12 | 11 | 7 | **99** | 100 |
| Eight additions, first offsets | 6 | 10 | 12 | **13** | 11 | 18 | 12 | 11 | 7 | **100** | 101 |
| Eight additions, all offsets | 6 | 10 | 12 | 12 | 11 | 18 | 12 | 11 | 7 | **99** | 100 |
| **Final: plus the R1 to R3 closures** | 6 | 10 | 12 | 12 | 11 | 18 | 12 | 11 | 7 | **99** | 100 |

The baseline reproduces the chapter map recorded by the msc-thesis project for the
2026-09-02 close exactly, chapter for chapter, so the isolated build is faithful and the
measurement can be trusted. Every build carries the same single pre-existing `undefined`
hit in `report.log`, and the final build matches the baseline on 774 defined labels, 815
citation instances, zero overfull `\hbox` and zero underfull `\vbox`.

**What the measurement established, and it is worth recording.** Chapters 4 and 6 have no
line of slack, exactly as the shortening campaign's close-out predicts ("Every main-body
chapter now occupies exactly `ceil(its own ink)`"). Three typeset lines in Chapter 4 bought
a page; compacting to 1.5 lines bought the same page; and so did a change measured at
**net minus six words**. The fourth row above is the diagnostic: two offsetting cuts worth
about 45 words returned Chapter 6 to 18 pages but left Chapter 4 at 13. Chapter 4's extra
page was therefore not ink but float placement, its three floats repacking onto a different
page under any perturbation, and it only came back when about 70 further words were
removed. **In a chapter that carries floats, the offsetting cut has to be several times the
size of the addition, and the page model does not predict it.**

**The six offsetting cuts, and where each fact still lives.** Every one is a restatement:
nothing was removed from the document, only from a second or third printing of it, and in
each case a cross-reference to the surviving instance was added or already stood.

| # | Chapter, place | What was compressed | Where the fact still stands verbatim |
|---|---|---|---|
| C1 | Ch. 4, open-entry variant | the tanh saturation credits and the 6 per cent KP 62.0 figure | Ch. 3 `subsec: Cross-Section Inventory...`, which the sentence already cited |
| C2 | Ch. 4, initiation gate close | "evaluated on the unremediated foundation at all four cross-sections... not the physics" | Ch. 4's own governing-commitments paragraph and Ch. 3 `subsec: Remediation History...`, now pointed at |
| C3 | Ch. 4, opening signpost | "Each choice is justified where it is introduced." | pure signposting, no factual content |
| C4 | Ch. 4, head-convention rationale | "; the structural consequences are stated here" | pure signposting, no factual content |
| C5 | Ch. 4, recovery convention | the nine-month reload's 20 per cent and 140 per cent figures | Ch. 2 `subsec: The Time-Dependent ODE Framework of Pol as the Bridge`, now pointed at |
| C6 | Ch. 6, conductivity band | "against a statistical interval on the same estimate spanning a factor of 1.01" | Ch. 5 `sec: The Aquifer Conductivity Prior under Scrutiny`, now pointed at |
| C7 | Ch. 6, severity close | the 46 and about-two displacements' prose restatement | kept in place, and also in Table `tab: piping conditions register`, now pointed at |
| C8 | Ch. 6, posterior curve shift | "separate around and below the survived stage, reconverge above it" | the caption of the very figure cited in that sentence |
| C9 | Ch. 6, rejection paragraph | a duplicate forward pointer to `subsec: What the Replay Adds` | the same pointer four lines later, with its claim intact |

C7 is the one to check on a read-through: the two numbers were retained in the compressed
sentence rather than delegated, so that paragraph lost only its second pointer and its
sentence break.

**Three further cuts paid for the R1 to R3 closures (2026-09-04).** The R1 addition is
about 3.4 typeset lines and Chapter 6 again had none to spare, so three more restatements
in the same section went: C10, the clause "exactly the information the peak approximation
would have fabricated", which is Chapter 4's own sentence at
`subsec: Survival Discrimination`; C11, the excluded-strata paragraph's duplication of the
caption of the figure it sits beside, and its restatement of the 2.75 to 3.90 band given
five paragraphs earlier; and C12, the "24 to 42 per cent" and "from 2.75 and 2.92" strings,
both of which the chapter's own standing-conditions register carries verbatim and which the
compressed sentence now cross-references. The R2 addition fits inside Chapter 8's existing
slack and needed no offset, and the R3 edit is net five words.

---

## 5. Also asked, and fully answered in place

Short questions a committee may reach for, each with a one-line pointer, so the candidate does
not have to hunt:

- **"Your uplift and heave limit states are the same inequality under Terzaghi, so your
  three-stage chain has two stages."** Ch. 4 states the collapse and why the full gate is
  retained; Figure `fig: stph chain`'s caption states it too. (But see R3.)
- **"Your 225 s timestep is not converged."** Ch. 5: the failure *indicator* is stationary from
  450 s down and no classification flips between 225 s and 14 s; the literal 1 per cent
  criterion on pipe-length *magnitude* needs 112.5 s and binds no deliverable.
- **"You found forward-Euler barrier-jump realizations at 1e6."** Ch. 6, `subsec: The KP 57.4
  Bound`: four in 1e6, none in either design-level anchor, one inside the 39.50 m anchor's 521,
  biasing B down by 0.2 per cent against an interval of 1.18, and conservative in direction.
- **"Your hydraulic translation over-predicts landside heads by up to 2.67."** Ch. 5: measured,
  attributed to aquifer connectedness rather than the elastic ratio, judged 1.0 to 1.15 at
  Tokachi as an explicit extrapolation, strictly conservative because r_e drives only the gate,
  and bounded by a halved-r_e full-scale run (max ΔP_f 0.181, shoulder-confined).
- **"Latin hypercube gives you nothing in the tail."** Ch. 5: measured (variance reduction 1.4
  at P_f ≈ 0.26, parity in the deep transient tail), mechanism identified as the multiplicative
  C_e × k_aq interaction by the GSA, and exact binomial intervals used instead.
- **"KP 62.0's grid runs six metres above the crest."** Ch. 6 and Ch. 7: shaded in every figure
  that draws it, never presented as attainable, and the 11.8 per cent of the warming annual
  contribution it supports is stated in the table caption, the text, the limitations register
  and the Overall Conclusion.
- **"Your three mechanisms are composed as independent."** Ch. 7: below the crest at three of
  four sections only one branch is non-zero, so the assumption is barely exercised where the
  results are read; the one place two branches are large at once is KP 62.0 above 48 m, which
  is where the only dominance reversal occurs, and the exclusion is non-conservative there.
- **"The importance sampler would have solved KP 57.4."** Ch. 6 and Ch. 8: it failed its
  pre-registered validation for a ratio *between* branches, a tilt enriching one branch
  degrading the other, so it is structurally the wrong instrument and contributes no reported
  number.

---

## 6. The one attack I would least want asked

**A8, in its sharper second half: "Every transient probability in this thesis rests on one
hydrograph. Show me that the duration finding is not a property of the wave you chose."**

Not because it is unanswerable, and no longer because the answer is missing: as of
2026-09-04 the selection rationale is printed in Chapter 4, one sentence before the
paragraph that says the pinned member reaches the results through one channel only. It is
the one I would least want asked because of where it sits in the dependency graph. This is
the only objection that reaches *all four* research questions at once.
RQ1's transient branch is conditioned on it; RQ2's peak-only factor takes it in the numerator
and not the denominator; RQ3's dominance shares descend from the transient curves and, through
the hard-coded surface-curve constant, so do the overflow ones; RQ4's climate ratios are
integrals of those same curves. Nothing else in the thesis has that reach. The conductivity
bracket (A4) is larger in magnitude but it is *measured*, two-sided and reported on every
number, so pressing it produces a printed answer. Until this pass the canonical event had a
measured sensitivity and no printed rationale, which is the worst possible combination in a
defence: a question whose answer exists, is good, and is not in the document. That
combination is now closed, and it is the single most valuable thing this pass did.

The second reason is rhetorical. The three-thousand-to-one framing is devastating to a
non-specialist committee member, and the correct reply is counterintuitive: the chosen member
is a *long* one, in the ensemble's upper duration quartile, which raises the transient
probability and therefore **shrinks** the very gap the thesis reports. The candidate must get
that inversion out in the first sentence, before the room has settled into the assumption that
a hand-picked event must be a flattering one. The one-sentence form to have ready:

> It was pinned to exercise the compound-memory formulation, not to produce a result: it sits
> in the upper duration quartile of the historical ensemble and is one of the roughly ten per
> cent of members with a second peak. That choice runs against the headline, because a longer
> wave raises the transient probability and narrows the gap; the shorter approved member
> widens Δβ by 0.41 and 0.54 at the two drained sections. And the static branch, the critical
> head, the response factor, six of the ten comparators and the entire 2016 survival result
> are the same numbers under any canonical event whatever.
