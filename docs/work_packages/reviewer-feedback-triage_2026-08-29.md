# Reviewer feedback triage and execution plan

Date: 2026-08-29. Status: verified plan, no thesis file edited in this session.
Source: reviewer report `Tokachi_piping_review_major_minor_EN.pdf` (Hokkaido
University full professor, non-BEP specialist; reviewed the **first draft**
Abstract and final chapter only, no numerical reproduction).

**Governing context for every verdict.** Between the draft the reviewer saw and
today, three revision campaigns already landed in `msc-thesis`:

1. **2026-08-24** OYO 1998 framing review (`docs/oyo_1998_framing_review_2026-08-24.md`)
2. **2026-08-28** Japanese levee failure criterion correction, applied in full
   (`docs/japanese_levee_failure_criterion_review_2026-08-28.md` §11) — Summary,
   Ch1, Ch2, Ch3, Appendix G rewritten against the primary MLIT/PWRI sources
3. **2026-08-28/29** RQ1 beta re-expression + equal-head-convention comparison +
   terminology/evidence audit (`docs/rq1_beta_reexpression_2026-08-28.md`,
   ADR-0051; unbiasedness withdrawn in 5 places, Yabe reframed
   ordering-not-magnitude)

Much of the reviewer's feedback independently converges on those campaigns, so
several comments are **valid against the draft he read but already implemented**.
The plan below covers only the verified residuals.

---

## 1. Verdicts on every point

### Major comments

| # | Topic | Verdict | Residual work |
|---|---|---|---|
| MC1 | Japanese practice framing / novelty | **Valid — already addressed** (2026-08-28 correction went further than his suggestion) | One stale sentence in Ch9 Overall Conclusion |
| MC2 | Comparison, not correction of an error | **Partially valid** | Targeted neutral-verb pass on headline claims; keep the defined term B |
| MC3 | Separate total difference from progression time | **Valid — already fully implemented** | None (verify only) |
| MC4 | Mechanism ranking, asymmetric uncertainty, 4/114 | **Partially valid — substantively addressed** | One clause in the Summary; his proposed new analyses dropped |
| MC5 | 2016 survival + Yabe moderation | **Partially valid — largely addressed** | Summary Yabe sentence; "unsafe" wording sharpened |
| MC6 | Climate attribution + hydrograph shape | **Partially valid — largely addressed** | Summary "frequency rather than severity"; make the existing two-event shape sensitivity explicit |
| MC7 | Conditional phrasing of crest-raising recommendation | **Partially valid** | Reframe the "fixed footprint means height" policy characterization conditionally |

**MC1 — Valid, already addressed.** The professor is right that Japanese
practice checks piping and considers time-varying loading; our own 2026-08-28
review established this from the primary sources (Cabinet Order Art. 18, 2002
Design Guideline, current Technical Standards) and the corrected framing was
applied to Summary/Ch1/Ch2/Ch3/App G in one commit. The current framing is in
fact *stronger* than his suggested wording, because the standard itself names
flood duration as the reason below-HWL safety is not absolute. **Residual:**
Ch9 Overall Conclusion still says "The mechanism that conventional practice in
this basin excludes from levee assessment altogether", which contradicts the
corrected Ch1/Ch2 (piping initiation *is* checked at standard level; what is
absent is time-dependent progression, and piping is absent from the basin's
*system-scale* multi-mechanism assessment). Align with the Summary's already
correct "absent from current system-scale assessment".

**MC2 — Partially valid.** The direction (static ≥ transient) is a *theorem*
under the nested formulations, so "yields a higher estimated probability" is
provably true while "overestimates" presumes the transient branch is truth —
and the thesis itself concedes the transient branch has only one hedged
out-of-sample case. Much is already moderated (Ch9 RQ1 opens "lowers the
estimated…"; the comparator conditionality is stated; unbiasedness was
withdrawn 2026-08-29). **Residuals:** naked claim-verbs "overestimates /
overstates / correcting" where the subject is practice or the criterion, in
Summary ¶3, Ch6 design-level paragraph, Ch8 opening, Ch9 Overall Conclusion and
one-sentence summary; "margin built into a steady-state assessment" phrasing;
plus a one-sentence definitional caveat where B is defined. **Not adopted:**
renaming the overestimation factor B. It is a defined technical symbol in ~40
places, the nomenclature, and figure axes; the direction it names is
structural, not empirical; and the supervisor-approved Δβ-first re-expression
already demoted it to the secondary register. A definitional caveat achieves
the reviewer's aim at a fraction of the risk.

**MC3 — Valid but already fully implemented.** Everything he asks for exists in
the current draft: the additive Δβ ladder (head 0.36 / gate 0.00 / temporal
0.55 at KP 62.0), the 75 to 97 per cent head-convention share stated in
probability *and* index registers, "duration alone accounts for a factor of one
to about six", the scale-exponent conditionality, the components table
(`tab: gap components beta`), and stage/CI/bound status on every factor
(`tab: answers register`). His feared misreading ("26.9 is the duration
effect") is pre-empted in Summary ¶4 and the Overall Conclusion. **Dropped as
new work; verification only.**

**MC4 — Partially valid, substantively addressed.** The asymmetric-uncertainty
point is exactly the thesis's own Commensurability section ("the shares rank
the mechanisms as this assessment knows them rather than as failures are to be
expected") plus the limitations-register entry "piping branch propagates a
fuller uncertainty account… inflates the piping share". Coverage (4 of 114,
explicit lower bounds, "not evidence that the uninvestigated segments are
safe") is stated in Summary, Ch3, Ch9. **Dropped:** his three suggested
analyses (central-value comparison, symmetric propagation, P(piping>overflow)).
The two-sided bracket propagation already delivers a *stronger* robustness
statement — the ordering's non-invariance is mapped cell by cell across the
conductivity and gradation brackets — and equalizing uncertainty treatment
would require rebuilding Uemura's surface models, out of scope. **Residual:**
the Summary's fifth qualification states the bracket asymmetry but not the
propagation asymmetry; extend by one clause (also discharges Minor 10).

**MC5 — Partially valid, largely addressed.** Ch5 already hedges Yabe exactly
as he asks ("One case cannot establish the claim… What is reproduced is the
ordering. A probability of 0.061 at a site that did breach is not in itself a
confirmation of the magnitude"), and the 0.65-in-60-years statement is already
compatibility-framed ("consistent with"). The as-if-undrained upper-bound /
counterfactual framing is in RQ2 and the Summary. **Residuals:** Summary ¶3
still opens the Yabe sentence "A single out-of-sample test supports the
progression physics", stronger than the chapter it summarizes — align. And
"the error is unsafe" (Summary ¶5, Ch2, Ch9 rec 1, Summary ¶7) is sharpened to
his more precise "biases the inference in the non-conservative direction" —
the direction *is* established (over-rejection → posterior P_f biased low), so
this is a precision fix, not a retreat.

**MC6 — Partially valid, largely addressed.** His central factual claim
(amplitude, not shape elongation; longer above-toe loading is a consequence of
a taller event of invariant shape) is *already the thesis's own finding*, stated
in Summary ¶6, Ch7, Ch8 and Ch9 RQ4, together with the non-separability
limitation he requests ("peak magnitude and load duration are not separable
inputs… duration enters as a stratifier of the hazard rather than as an
argument of the fragility"). His requested shape simulations effectively
already exist: the two approved canonical events differ in duration/shape, the
effect is measured (transient probabilities fall 24 to 42 per cent at
mid-curve, bias roughly triples, and the KP 62.0 warming piping-overflow cell
changes hands to overflow under the shorter event — precisely his
"sharper peaks favor overflow" conjecture, quantified) and carried as a
bracket. **Residuals:** the Summary still says "making the climate signal one
of frequency rather than severity", which Ch9 deliberately avoids — replace
with the precise attribution; and add one or two sentences connecting the
canonical-event bracket explicitly to hydrograph-shape sensitivity, with an
independent shape-varying ensemble named as future work.

**MC7 — Partially valid.** The recommendation is already hedged ("indicates the
sensitivity without evaluating a design… simulates no structural
intervention… ranks priorities rather than evaluating designs"). But the policy
characterization overreaches: "an increase in conveyance capacity, which for a
levee of fixed footprint means additional height" ignores river-channel
excavation and the other measures in the official program (the reviewer's
practice note is consistent with our own Chisuishi record), and "the basin is
embarked on the pathway for which the maladaptation concern is most acute" is
too strong. **Fix:** the reviewer's conditional form — *where* the added design
discharge is accommodated locally by crest raising at unchanged seepage-path
length, susceptibility increases — which preserves the full quantitative
content (the 7 m / order-of-magnitude sensitivity) while dropping the claim
about what Tokachi policy is.

### Minor comments

| # | Topic | Verdict |
|---|---|---|
| m1 | "Risk" without consequences | **Partially valid** — ~8 loose uses in Ch8/Ch9 where the quantity is annual failure probability; targeted reword. Title does not contain "risk" (his paraphrase did) |
| m2 | Comparator definition consistency | **Already addressed** — gross-head-as-calibrated vs crack-reduced Dutch instrument stated in Summary, Ch9 RQ1, one-sentence conclusion; the equal-convention comparison (ADR-0051) quantifies exactly this distinction. Drop |
| m3 | Stage-specific reporting, bounds vs estimates | **Already addressed** — every factor carries its stage; B ≥ 148 explicitly a bound with the resolved 42.7 quoted beside it. Drop |
| m4 | Nested failure sets stated once, early | **Valid, small** — the nesting first appears structurally in Ch5/Ch6; add 1 to 2 sentences in Ch4 where the comparator is defined, cross-referenced from later restatements |
| m5 | "Evaluated as if undrained" in figures/tables | **Valid, small** — the framing is thorough in prose but absent from figure/table captions; add to captions carrying KP 58.8 / KP 60.0 deliverables |
| m6 | 110 uncharacterized segments | **Already addressed in prose**; fold a caption clause into the m5 pass for the dominance-profile figure. |
| m7 | Zero scour caveats | **Already addressed** — "the corrected branch has no independent validation of its own: its zero belongs to the model and its inputs". Drop |
| m8 | Limitations placement | **Already addressed** by the rewrite (register table; qualifications adjacent to each answer). Drop |
| m9 | Repetition in final chapter | **Partially valid, owner-taste** — the repetition is now deliberate architecture (answers + register + overall + one-sentence). Optional: split the ~180-word "one sentence" summary. Default: skip |
| m10 | Abstract balance sentence | **Largely addressed**; residual clause folded into MC4 fix |

**Wording table:** subsumed item-by-item into MC2/MC5/MC6/MC7 above; his
neutral alternatives are used as drafting guides where the fix was accepted.

**Suggested overall positioning paragraph:** **not adopted wholesale.** The
current Overall Conclusion already carries every conditionality he lists
(head convention, scaling, cross-section, foundation parameters, 4-of-114,
asymmetric treatment) with the measured numbers attached, which is stronger
than his qualitative paragraph. His closing thought ("rather than a universally
superior replacement") is already present as "Keep the screening rule and the
reliability statement apart… Neither substitutes for the other".

---

## 2. The plan

Three work packages, each sized for one independent review pass.

| Package | Addresses | Content |
|---|---|---|
| **P1 — Neutral register pass** | MC2, MC5 (wording), MC1 residual, m1 | Claim-verb softening in Summary/Ch2/Ch6/Ch8/Ch9; B definitional caveat; Ch9 "excludes altogether" fix; unsafe→non-conservative; risk→failure probability |
| **P2 — Adaptation and climate framing** | MC7, MC6 residual | Conditional reframe of the crest-raising policy characterization (Ch8, Ch9 rec 3, Summary); "frequency rather than severity" replacement; explicit shape-sensitivity connection |
| **P3 — Structure and labeling** | m4, m5, m6, MC4/m10 residual | Ch4 early nesting statement; as-if-undrained caption pass; lower-bound caption clause; Summary fifth-qualification clause |

Ordering: P1 → P2 → P3. P1 touches the most files and settles the register the
other two write into. Collisions are minimal (all three touch the Summary, but
different paragraphs). P3 is independent of P2 but goes last because the
caption pass is lowest-risk.

**Dropped, with reasoning:** MC3 (implemented in full — Δβ ladder, two-register
composition, duration factor 1 to 6, all with stage/CI/bound status); MC4's new
analyses (bracket propagation already stronger; symmetric propagation out of
scope); m2, m3, m7, m8 (implemented); m9 beyond the optional flag (deliberate
architecture); the positioning paragraph (current conclusion stronger and
measured); wholesale B renaming (structural direction, defined symbol,
supervisor-approved Δβ-first register already demotes it).

---

## 3. Execution sequence — ready-to-use work packages

Run in order. After each chat: review `git -C D:\repositories\msc-thesis diff`,
satisfy yourself, keep the commit, then start the next fresh chat. No chat
compiles LaTeX or pushes.

### Work package 1 of 3 — neutral register pass

```
Read the architecture and decision records in D:\repositories\msc-thesis first and treat it as the binding
style contract (no em dashes, ranges written "X to Y", no Japanese script,
match the surrounding "per cent" usage). Work only in D:\repositories\msc-thesis.
Do not compile LaTeX, do not push, do not change any number, CI, or citation.

Context: a reviewer (major comments 1, 2 and 5 of the review of the first
draft) asked that the static-transient comparison be phrased as a comparison
between model formulations rather than as the correction of an established
error, since the transient formulation is not validated ground truth (the
thesis itself says so in Chapter 5). The direction static >= transient is
structural (the transient failure set is nested in the static set by
construction), so neutral phrasing loses nothing. The defined symbol B
("overestimation factor") is kept everywhere; only naked claim-verbs change.
A separate 2026-08-28 correction already established that Japanese
standard-level practice DOES check piping initiation, so one leftover
"excluded altogether" sentence must also be fixed.

Make exactly these wording edits (locate by the quoted anchors, not line
numbers; adapt replacement grammar to context):

1. frontmatter/summary.tex, paragraph 3, first sentence: "The steady-state
   criterion overestimates the per-event conditional probability of piping at
   every cross-section and stage examined" -> "The steady-state criterion
   returns a higher estimated per-event conditional probability of piping than
   the time-dependent one at every cross-section and stage examined". Keep the
   rest of the sentence.
2. Same paragraph: "A single out-of-sample test supports the progression
   physics:" -> "A single out-of-sample case is consistent with the progression
   physics, reproducing an ordering rather than confirming a magnitude:".
   (This aligns the Summary with the hedged framing of Chapter 5,
   "The Transient Race Condition: Support from a Single Field Case".)
3. frontmatter/summary.tex, paragraph 5: "and in both cases the error is
   unsafe" -> "and in both cases the bias is in the non-conservative
   direction".
4. frontmatter/summary.tex, paragraph 7: "gave an unsafe result" -> "biased
   the inference in the non-conservative direction".
5. mainmatter/"2. Theoretical and Empirical Foundations.tex": "which is why a
   peak-referenced assessment of either is structurally unsafe" -> "which is
   why a peak-referenced assessment of either is structurally non-conservative".
6. mainmatter/"6. Results - Subsurface Piping Assessment.tex": "conventional
   steady-state practice overestimates the per-event conditional probability of
   backward erosion piping there by a factor of about 27" -> "a conventional
   steady-state assessment there returns a per-event conditional probability of
   backward erosion piping about 27 times the time-resolved one".
7. mainmatter/"8. Discussion.tex", opening section: "the steady-state
   criterion overestimates the per-event conditional probability of piping at
   the unreinforced section" -> "the steady-state criterion returns a per-event
   conditional probability of piping ... times the time-dependent value at the
   unreinforced section" (rework the sentence so the factor 26.9 and both
   intervals survive verbatim). Then grep the whole of mainmatter/ for
   "overestimates|overstates|overstate " and fix any further instance where
   the SUBJECT is practice, the criterion, or the assessment asserting error;
   leave the defined term "overestimation factor" and instances about
   sampling/estimation artifacts (e.g. "the smaller sample overstated the
   bias") untouched. Chapter 5's subsection title "The Static Comparator
   Overstates Failure at the Surviving Sites" may become "The Static Comparator
   Is Conservative at the Surviving Sites" (do not change its \label).
8. mainmatter/"9. Conclusions and Recommendations.tex", Overall Conclusion:
   "The correction does not displace piping from the risk picture." ->
   "The time-dependent treatment does not displace piping from the hazard
   picture." And in the one-sentence summary: "correcting it leaves piping the
   governing mechanism" -> "accounting for progression time leaves piping the
   governing mechanism".
9. Same file, one-sentence summary: "a steady-state criterion overstates the
   per-event reliability index of backward erosion piping in this basin by
   between $\Delta\beta$ 0.9 and at least 1.9" -> "a steady-state criterion
   returns a per-event reliability index for backward erosion piping in this
   basin between $\Delta\beta$ 0.9 and at least 1.9 lower than the
   time-dependent criterion" (this also fixes a latent direction ambiguity:
   the static criterion UNDERSTATES the index / overstates the hazard).
10. Same file: "The mechanism that conventional practice in this basin
    excludes from levee assessment altogether is the one that governs" ->
    "The mechanism absent from the basin's current system-scale assessment is
    the one that governs". (Japanese standard-level verification does check
    piping initiation; what is absent is the mechanism from the system-scale
    multi-mechanism assessment. The Summary already uses this correct form.)
11. Definitional caveat: find where the overestimation factor B is first
    DEFINED in mainmatter/"6. Results - Subsurface Piping Assessment.tex"
    (near "with the overestimation factor" / its defining equation) and append
    one sentence stating that the name records the guaranteed direction of the
    ratio under the nested formulations and does not assert the
    progression-based value as ground truth, both branches remaining model
    estimates. One sentence, thesis voice, no citation needed.
12. "Margin" phrasing: in frontmatter/summary.tex ("the margin built into a
    steady-state assessment reads largest under the present climate") and in
    Chapter 9's Overall Conclusion ("the margin implicit in a steady-state
    assessment being at its maximum under the present climate"), replace
    "margin ..." with "relative conservatism of a steady-state assessment ..."
    (keep the surrounding logic and numbers). Leave "the margin the two
    criteria disagree on" as is; it is already relational.
13. "Risk" pass (reviewer minor comment 1; no consequences are modeled): in
    Chapters 8 and 9 replace "risk" with "annual failure probability",
    "failure probability" or "hazard" ONLY where it denotes the computed
    probability quantity: "ordering of the risk", "risk concentrated/
    concentrates" (2 places in Ch9, 1 in Ch8), "largest absolute risk",
    "highest-risk segments". Keep "maladaptation risk", "residual risk under
    the revised design", and any use where risk-as-concept is meant. If a
    section heading in Chapter 2 or 8 contains "Levee Failure Risk", retitle
    to "Levee Failure Probability" WITHOUT changing the \label key.

Done means: (a) grep -rn "the error is unsafe|structurally unsafe" mainmatter
frontmatter returns nothing; (b) grep for "excludes from levee assessment"
returns nothing; (c) every numeric value, interval and \label in the diff is
byte-identical to before; (d) no em dash and no CJK character introduced
(the repo has checks; also verify by grep); (e) a single commit in msc-thesis
titled "Neutral comparison register for the static-transient claims
(reviewer MC2/MC5, MC1 residual)". Show me the full diff stat and the list of
changed sentences before committing.
```

**Verify after chat 1:** read the diff; confirm no number changed
(`git diff --word-diff` and scan for digits); confirm the Ch9 one-sentence
summary still parses as intended.

### Work package 2 of 3 — adaptation policy and climate-signal framing

```
Read the architecture and decision records in D:\repositories\msc-thesis first and treat it as the binding
style contract (no em dashes, ranges "X to Y", no Japanese script, match
surrounding "per cent" usage). Work only in D:\repositories\msc-thesis. Do not
compile, do not push, do not change any number or citation. Background you may
consult read-only: D:\repositories\bep-reliability-engine\docs\
tokachi_chisuishi_full_review_2026-07-27.md.

Context: a reviewer (major comments 6 and 7) made two requests. (1) The
crest-raising discussion characterizes the adopted Tokachi adaptation as
height-only ("an increase in conveyance capacity, which for a levee of fixed
footprint means additional height"); official planning in fact combines
channel excavation, levee improvement, flood-control facilities and seepage
works, so the recommendation must be phrased conditionally, about the
crest-raising COMPONENT of any such program, without claiming Tokachi policy
is the opposite of the recommendation. (2) The Summary phrase "frequency
rather than severity" is too binary, since peak amplitude itself increases;
Chapter 9 RQ4 already carries the precise attribution and the Summary should
match it. The reviewer also asked for discussion of sensitivity to sharper
hydrograph shapes; that sensitivity is ALREADY measured in this thesis via the
two approved canonical events (the shorter event lowers transient
probabilities 24 to 42 per cent at mid-curve, roughly triples the
static-to-transient bias, and hands the KP 62.0 warming piping-overflow cell
to overflow) and only needs to be named as such.

Edits:

1. mainmatter/"8. Discussion.tex", section "Crest Heightening vs. Berm
   Widening": replace "The adaptation already adopted is therefore an increase
   in conveyance capacity, which for a levee of fixed footprint means
   additional height, and that direction degrades seepage performance while
   improving overflow performance. The basin is embarked on the pathway for
   which the maladaptation concern of this thesis is most acute." with a
   conditional formulation along these lines (adapt to the paragraph): the
   revised policy accommodates the larger design discharge through a program
   of measures of which local crest raising is one; wherever the added
   conveyance is provided by raising the crest at unchanged footprint, the
   applied head rises at unchanged seepage-path length, and it is to that
   component that the maladaptation concern of this thesis attaches. Keep the
   6,800 to 9,700 m3/s numbers and the \parencite{tokachi_chisuishi_2023}
   citation. Do not assert what share of the program each measure carries
   unless the Chisuishi review document explicitly supports it.
2. Same section: leave the Fukuoka vulnerability-index argument, the 7 m /
   order-of-magnitude sensitivity, and the "not a design evaluation" scope
   sentence untouched.
3. mainmatter/"9. Conclusions and Recommendations.tex", recommendation 3:
   change the bold lead "Prefer horizontal widening to crest heightening
   wherever seepage governs." to "Weigh the seepage path explicitly wherever
   crest raising is evaluated, and prefer widening where seepage governs."
   In the body, replace "while the adaptation already adopted here runs the
   other way" and the following "which for a fixed footprint means height"
   reasoning with the same conditional formulation as edit 1, compressed to
   one clause. Keep both mechanisms' agreement and all numbers.
4. frontmatter/summary.tex, final paragraph: rephrase "Second, where seepage
   governs, horizontal widening should be preferred to crest heightening, yet
   the adaptation adopted here does the opposite: shortening the confined
   seepage path..." to the conditional register, e.g. "Second, where seepage
   governs, crest-raising alternatives should be weighed against their effect
   on the seepage path, which the adopted design-discharge increase makes
   concrete: shortening the confined seepage path at the unremediated section
   by seven meters increases its conditional transient failure probability at
   the design level by roughly an order of magnitude." Keep every number.
5. frontmatter/summary.tex, paragraph 6: replace "making the climate signal
   one of frequency rather than severity" with wording matching Chapter 9 RQ4,
   e.g. "so the increase arrives more through the frequency of years with
   prolonged above-toe loading than through the conditional danger of such
   years". Keep the 2.7 to 7.8 factor sentence unchanged.
6. mainmatter/"8. Discussion.tex": in the section discussing the canonical
   event or its limitation entry (search "the shorter of the two approved
   events"), add one to two sentences naming the two-event comparison as a
   measured hydrograph-shape sensitivity: a shorter, sharper event of equal
   peak lowers every transient probability, raises the static-to-transient
   difference about threefold, and moves the one contested mechanism ordering
   toward overflow, which is the direction a sharper flood regime would push
   the comparison; an ensemble varying shape independently of amplitude is
   future work. First check whether the surrounding text already says this;
   add only what is missing, and do not duplicate numbers already present in
   the same passage. If a sentence fits better in the future-research register
   of Chapter 9 (table "future research"), you may instead add it there as one
   clause on an existing row; do not add a new row.

Done means: the phrases "fixed footprint means additional height", "does the
opposite", "embarked on the pathway", and "frequency rather than severity" no
longer appear (grep); all numbers and citations byte-identical; no em dash or
CJK introduced; one commit titled "Conditional adaptation framing and precise
climate attribution (reviewer MC6/MC7)". Show the diff before committing.
```

**Verify after chat 2:** grep the four banned phrases; read the new Ch8
paragraph once for tone (it must not concede the maladaptation argument, only
scope it).

### Work package 3 of 3 — structural statement and labeling

```
Read the architecture and decision records in D:\repositories\msc-thesis first and treat it as the binding
style contract (no em dashes, ranges "X to Y", no Japanese script, match
surrounding "per cent" usage). Work only in D:\repositories\msc-thesis. Do not
compile, do not push, do not change any number or citation.

Context: a reviewer asked for three small structural improvements. (1) The
containment of the transient failure set inside the static one is a structural
property of the formulations; it is currently first stated in Chapters 5 and 6
and should be stated once, early, where the comparator is defined (minor
comment 4). (2) The two toe-drained sections KP 58.8 and KP 60.0 are evaluated
as if undrained; the prose says so thoroughly but figure and table captions do
not (minor comment 5). (3) The 110 segments without a piping branch are lower
bounds; the dominance-profile figure caption should say so (minor comment 6).
Also one clause in the Summary (major comment 4 / minor comment 10).

Edits:

1. mainmatter/"4. Methodology.tex": locate where the static Sellmeijer
   comparator is introduced against the transient criterion (search for the
   static comparator subsection or "shared realizations"). Add one to two
   sentences stating, as a property of the formulations and before any result:
   a transient breach requires the erosion head to exceed the same critical
   head the static rule compares against, so the transient failure set is
   contained in the static failure set by construction, for every realization
   and every loading; consequences of this nesting recur in Chapters 5, 6 and
   9. First check the surrounding text and Chapter 4 as a whole to be sure an
   equivalent early statement does not already exist; if one does, strengthen
   it in place instead of adding a duplicate.
2. Caption pass for "evaluated as if undrained": in mainmatter/"6. Results -
   Subsurface Piping Assessment.tex", mainmatter/"7. Results - System
   Integration and Climate Sensitivity.tex" and mainmatter/"9. Conclusions and
   Recommendations.tex", find every \caption (and longtable \caption) that
   presents KP 58.8 or KP 60.0 fragility curves, annual probabilities,
   rankings or mechanism shares as a deliverable, and add a short clause such
   as "KP 58.8 and KP 60.0 are evaluated as if undrained" (or "; drained
   sections evaluated as if undrained" where both appear among others). Use
   the short caption [] argument only if the clause would otherwise appear in
   the list of figures. Do not add it to captions that already carry it or to
   figures where those sections do not appear. Aim for the deliverable
   figures/tables, not every diagnostic; typically this is roughly 4 to 8
   captions. List each caption you touch.
3. In the caption of the reach-wide dominance/composition figure in Chapter 7
   (search "dominance profile"), add a clause that the 110 segments without a
   piping branch are surface-only lower bounds, omitting a mechanism rather
   than estimating it as small, if the caption does not already say so.
4. frontmatter/summary.tex, paragraph 5 of the composed-system paragraph
   ("Fifth, only the piping branch is bracketed, so these shares rank the
   represented mechanisms rather than all mechanisms failures may follow."):
   extend to also name the propagation asymmetry, e.g. "Fifth, only the piping
   branch is bracketed, and it propagates a fuller account of its epistemic
   uncertainty than the surface branches do, which in this range raises a
   computed probability, so these shares rank the represented mechanisms as
   this assessment knows them rather than all mechanisms failures may follow."
   Keep it one sentence.

Done means: the Ch4 nesting statement exists exactly once in that chapter; the
caption list you report covers every deliverable figure/table showing the two
drained sections in Ch6/Ch7/Ch9; no number, \label or \ref changed; no em dash
or CJK introduced; one commit titled "Early nesting statement and
as-if-undrained caption labels (reviewer m4/m5/m6, MC4 residual)". Show the
diff before committing.
```

**Verify after chat 3:** skim the list of figures/tables (`output.lof`/`.lot`
regenerate only on Overleaf compile — instead check the short-caption []
arguments in the diff); compile once on Overleaf and check the page budget and
that no caption overflows.

### Optional work package 4 (owner's taste, skip by default)

Minor comment 9: the "In one sentence" paragraph closing Chapter 9's Overall
Conclusion runs about 180 words. If you want it split into two or three
sentences with a single consistent certainty level, run a small dedicated chat
for that one paragraph; otherwise the repetition across 9.1 / register table /
9.2 is deliberate architecture and should stand.

---

## 4. Post-campaign bookkeeping

After all three chats: one Overleaf compile to confirm the page budget (the
2026-08-28 close was 112 pages against a 115 ceiling; these edits add well
under half a page net), then a dated entry in
`bep-reliability-engine/docs/project_log.md` noting the reviewer triage and
pointing at this file.
