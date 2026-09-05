# Claim-logic audit, 2026-09-03: does every conclusion follow, at the strength stated?

**What this is.** A claim-by-claim audit of the *internal logic* of
`msc-thesis`: whether each declarative claim in Chapter 9 and
the Summary follows from what the thesis itself measured, at the strength
stated. It is not an arithmetic pass; `docs/thesis_number_reconciliation_2026-09-03.md`
and its two predecessors cover value-versus-artifact traceability, and this
pass takes their verdicts as given. It is not a prose pass either: nothing was
re-worded that passes.

**Scope.** Thesis at commit `d6f91dd`, working tree clean at the start.
Every declarative claim in `mainmatter/9. Conclusions and Recommendations.tex`
and `frontmatter/summary.tex` was traced to the passage in Chapters 5, 6, 7 or
8 that carries it, and checked for strength match. Additionally: a full sweep
of announced enumerations across the main body and all eleven appendices; the
prohibited-claim register of this repository's architecture and decision records checked at
every site; the conditionality register checked against every number it
attaches to; and the 2026-08-29 terminology decisions checked for creep-back.

**Verdicts.** `OK` = the supporting passage carries the claim at the stated
strength. `FIXED` = a defect found and repaired by the smallest edit that
repairs the logic. Findings F1 to F12 were repaired under the original brief,
which forbade adding or removing a number; F13 to F15 needed that restriction
lifted and were repaired after the author lifted it.

**Result in one line.** Fifteen defects found, at seventeen sites, and **all
fifteen fixed**. Twelve were repaired under the original brief; three (F13, F14
and F15 below) were handed off in the first draft of this record and closed on
the author's authorisation of 2026-09-03, which lifted the no-new-number
restriction. The record keeps the two rounds numbered separately so they stay
legible. The document builds to the same chapter map. (The first draft of this
paragraph said twelve found and ten fixed; that was a miscount of its own
sections, corrected here.)

---

## 0. Integrity of the edits

Verified on an isolated faithful build (sources copied to a scratch directory
per the msc-thesis project rules, `latexmk -xelatex` run there), baseline against
post-edit:

| Gate | Result |
|---|---|
| Main body extent | **99 pages**, References on 100, unchanged. Ceiling 100 respected with one page of margin |
| Per-chapter page map | Ch1 6, Ch2 10, Ch3 12, Ch4 12, Ch5 11, Ch6 18, Ch7 12, Ch8 11, Ch9 7, **every chapter boundary unchanged**. The `report.toc` differs from the baseline in exactly one line, section 6.4's heading moving from page 64 to 65 inside Chapter 6's unchanged 18 pages, which is the restored passage of F13 being absorbed |
| `report.lof` / `report.lot` | byte-identical |
| Total document | 193 pages, unchanged |
| Undefined references / citations | 0 / 0 |
| Overfull `\hbox` warnings | the identical set of 12, at the identical widths, as the baseline. No new typesetting warning |
| `\label`, `\ref`, `\parencite`, `\textcite` keys | multiset identical per file (45/110/7 in Ch6, 21/90/27 in Ch8, 13/45/1 in Ch9) |
| Numeric tokens | Chapters 8 and 9 **multiset identical**. Chapter 6 gains exactly the eight tokens of the F13 restoration (`6.0`, `47.00`, `1.4`, `62.0`, `3.9`, `39.50`, `1.0`, `57.4`); the Summary gains exactly `1.11` and `1.67` from F14. Nothing else moved, and nothing anywhere was removed |
| Em dash / `---` scan | 0 hits |
| Japanese script scan | 0 hits |

Files touched: `frontmatter/summary.tex`, `mainmatter/6...tex`,
`mainmatter/8...tex`, `mainmatter/9...tex`. Nothing in `report.tex`,
`references.bib` or the class file.

---

## 1. Findings fixed under the original brief (F1 to F12)

### F1. `Two things prevent this` introduces three (known defect, Ch. 6)

**Site.** `mainmatter/6...tex`, Section "The Equilibrium-Head Anchor and the
Scale Exponent".
**What was wrong.** The announcement said two; the list ran to three, the third
opening `Third,`. Cause traced: thesis commit `6d6584e` (2026-08-21, task 2)
inserted the `Third,` item, on the plane-strain anchor being the progression
model author's endorsed baseline, and never updated the count.
**Fix.** `Two things` to `Three things`, and the unmarked second item (`And at
KP~57.4 and KP~62.0 both gradation readings...`) given the `Second,` marker the
third already had. The first item stays unmarked, which is the form Chapter 4
and Appendix G already use.

### F2. `Two features of that pattern` delivers only a marked first (Ch. 6)

**Site.** `mainmatter/6...tex`, Section "How Much the Survival Rejects, and
Where".
**What was wrong.** "Two features of that pattern matter more than the numbers
themselves. The first is that the update is informative at only two of the
eight strata..." and no second was ever marked. Cause traced: the sentence
"The second is the width of the reading." opened the following paragraph until
the shortening campaign (`ad8fc2c`) removed it; the paragraph it introduced,
on the rating-anchored reconstruction moving the rejection, is still there.
**Fix.** The deleted sentence restored verbatim at the head of that paragraph.
No claim added: it is the original text and the material it labels is unchanged.

### F3. `against 5.4 for the transient one` drops its unit (known defect, Ch. 6)

**Site.** `mainmatter/6...tex`, Section "How the Constraint Divides Between the
Two Criteria".
**What was wrong.** The parallel sentence in Chapter 8 ("condemning 34~per cent
of the prior at KP~58.8's 2016 peak against 5.4~per cent for the transient
model") carries the unit; the Chapter 6 instance reads "against 5.4 for the
transient one", where a bare 5.4 beside a factor-heavy chapter invites reading
as a factor.
**Fix.** `against 5.4` to `against 5.4~per cent`.

### F4. `neither` with four antecedents (known defect, Ch. 8)

**Site.** `mainmatter/8...tex`, close of Section 8.1.
**What was wrong.** "conditional on the adopted aquifer conductivity and
seepage lengths, on the conservative grain-size reading, and on the decision
not to credit the installed toe drainage; **neither** cancels between the
branches despite the shared sample." Four antecedents, one `neither`. This is
not only a grammatical defect: repairing it as `none of these` would assert
non-cancellation for the grain-size reading and the drainage decision, which
Chapter 6's standing-conditions register does **not** establish. That register
gives the grain-size statistic as governing "every absolute probability
reported here" and the remediation state as governing "the probabilities at the
two drained sections", neither as a bracket on the ratio.
**Fix.** The antecedent restored to what the sentence was written for. Traced:
before commit `bc59c62` the text read "Neither the conductivity nor the seepage
lengths cancels between the branches despite the shared sample", which is
exactly Chapter 6's own scope ("The ratio remains conditional on conductivity
and seepage length, neither of which cancels") and Chapter 5's. That wording is
restored inline.

### F5. The unfollowable duration-versus-stage-channel sentence (known defect, Ch. 8)

**Site.** `mainmatter/8...tex`, Section 8.1.
**What was wrong.** "That split is a duration channel, untouched and the one
the climate argument below rests on, against a stage channel, just re-scoped."
Cause traced: commit `8bb2756` compressed two sentences into one and lost the
predicate. The original read: "Two channels produce that split. The duration
channel, a longer flood raising the transient probability at fixed stage and
narrowing the gap in both metrics, is untouched and is what the climate
argument below rests on; the stage channel, the change in the gap as loading
moves a section up its own curve, is the one just re-scoped."
**Fix.** Rewritten as one sentence carrying exactly that content and no more:
"That split re-scopes the stage channel alone; the duration channel, on which
the climate argument below rests, is untouched." Four characters shorter than
what it replaces.

### F6. The low conductivity arm does not hand the lead to overflow at three of four sections historically (Ch. 9 and Summary)

**Sites.** `mainmatter/9...tex`, Overall Conclusion; `frontmatter/summary.tex`,
paragraph 5, qualification "Fourth".
**What was wrong.** Both said, of the conductivity bracket, that at its low end
**overflow leads at three of the four sections historically**. Chapter 7 says
something different and says it deliberately: "Under the conservative reading
piping's lead survives it at one of the four sections in the historical climate
and at none of the four under warming", and, of the lowest arm, "changes the
answer at seven of the eight section and climate cells and **hands the lead to
overflow at six of them**. At KP~57.4 in the historical climate it drives both
mechanisms to exactly zero, so no share exists there at all. **That says
something about the section, not that overflow leads there.**"

Historically, per arm, the leading mechanism is: KP 57.4 **not defined** (both
mechanisms exactly zero), KP 58.8 overflow, KP 60.0 piping (robust), KP 62.0
overflow. **Overflow leads at two of four, not three.** The count of three is
the *contested* count, not the overflow-leads count.

This is the exact misreading the engine's own study pre-registered against and
recorded: `docs/decisions/conductivity-bracket-annualisation.md` §2.1,
"P5 held and is worth stating separately, because it is the one place a naive
reading of the verdicts would be wrong ... Part 1 fixed 'NOT DEFINED' as a
third category precisely so this could not be reported as 'overflow leads'."
That note also records the conflation reaching Chapter 7 once and being
corrected there on 2026-08-21; the Overall Conclusion and the Summary were not
corrected with it.

**Fix.** Chapter 9: "its low arm **contests the lead** at three of the four
sections historically and at all four under warming", which is Chapter 9's own
wording in Section 9.1.3 and Chapter 7's in its standing-conditions register.
Summary: "at the low end, **piping loses the lead** at three of four sections
historically and all four under warming", which is true at all three (piping
leads at none of them afterwards) and does not assert that overflow leads.
Both keep the number three.

### F7. The four investigated segments are the four highest only in the historical climate (Ch. 9)

**Site.** `mainmatter/9...tex`, Section 9.1.3, coverage paragraph.
**What was wrong.** "Those four segments also have the highest annual system
failure probabilities among the 114 evaluation segments." Chapter 7 states the
same fact with a scope Chapter 9 dropped: "The four segments at which all three
mechanisms are quantified on the same footing are also, **in the historical
climate**, the four segments with the highest annual system failure probability
among the 114 evaluation segments."

The scope is load-bearing. From `results/system_integration/phase3/rq4_annual.csv`
(matrix, posterior, lambda_ac 250 m, primary surface), the four highest annual
system probabilities are:

| rank | historical | +4 K |
|---|---|---|
| 1 | KP 58.8, 7.42e-3 | KP 58.8, 4.09e-2 |
| 2 | KP 60.0, 1.80e-3 | KP 60.0, 1.42e-2 |
| 3 | KP 62.0, 1.01e-3 | KP 62.0, 1.28e-2 |
| 4 | KP 57.4, 7.53e-4 | **segment KP62.4 at 62.2 km, 1.10e-2, surface-only** |
| 5 | KP62.4 at 62.2 km, 5.15e-4 | KP 57.4, 9.53e-3 |

Under warming a surface-only segment displaces KP 57.4 from the top four, so
the unscoped claim is false.
**Fix.** ", in the historical climate," inserted, matching Chapter 7's wording.

### F8. The 70-to-100-per-cent share is the historical one (Ch. 9)

**Site.** `mainmatter/9...tex`, Overall Conclusion.
**What was wrong.** "the time-dependent branch still accounts for about 70 to
100~per cent of the summed annual failure contribution at every segment where
all three are quantified together", unscoped. Under warming Chapter 7 gives 91,
94, 100 and **0.50** at KP 62.0, so the range runs to a half, not to 70 per
cent. Chapter 9's own answers register attaches the scope ("Historically about
70 to 100~per cent; warming lead at 3 of 4, KP~62.0 an unresolved tie"), and
Section 9.1.3 attaches it too; the Summary attaches it by naming the warming
case in the same sentence. Only the Overall Conclusion drops it.
**Fix.** ", in the historical climate," inserted.

### F9. The 2016 survival does narrow the epistemic band (Ch. 9)

**Site.** `mainmatter/9...tex`, Section 9.1.2, third limit.
**What was wrong.** "the update redistributes weight within an assumed prior
population rather than choosing between candidate populations, leaving the
epistemic band **exactly as wide as it found it**." Chapter 7 measures the
opposite: "Carried through the 2016 survival constraint the bracket narrows and
the ordering does not move ... The bracket therefore closes from its upper end
alone, by a factor of 1.96 at KP~58.8 and **2.81** at KP~60.0 historically and
1.49 and 1.97 under warming." Chapter 9's *own answers register*, forty lines
below the sentence, says "Conductivity narrows by up to 2.81 from its upper
end". The claim is therefore contradicted inside its own section.
**Fix, in its final form.** The clause now names the object it is true of:
"leaving the epistemic band **on that choice** as wide as it found it." What
the update cannot narrow is the choice between candidate input populations,
which it leaves untouched exactly; what it does narrow, by up to 2.81, is the
propagated bracket on the annual numbers, which this section's own answers
register already carries. This is the same object Chapter 6 now names (F15) and
the one the Summary already named ("the epistemic **input** band"), so the
three statements are now about one thing and none contradicts Chapter 7.

### F10. The 0.86-to-0.97 index span is not conductivity's (Ch. 9 register, and Summary)

**Sites.** `mainmatter/9...tex`, Table "answers register", row 1, `Conditional
on` column; `frontmatter/summary.tex`, final paragraph.
**What was wrong.** The register cell read "Conductivity, up to factor 46 at
KP~62.0 **(resolved $\Delta\beta$ 0.86 to 0.97)**", attaching the index span to
the conductivity item. The Summary read "The plausible range of bulk horizontal
aquifer conductivity ... **It makes** the epistemic band on the
static-to-transient probability ratio 6 to 9 times wider than its statistical
interval; in reliability-index terms the two intervals are comparable."

Both attribute to conductivity alone a span that belongs to the whole resolved
arm set. From `docs/rq1_beta_reexpression_2026-08-28.md` §5, the four arms that
clear the R1 floor at the KP 62.0 anchor are `m_p` (0.97), `gamma_bl_sub_lower`
(0.90), `z_toe_minus0.30m` (0.88) and `k_aq_regional_upper` (0.86): the **lower**
end is conductivity's, the **upper** end is the model factor's. Conductivity
alone moves B by 10.4 and $\Delta\beta$ by 0.04, against the anchor's own
statistical width of 0.12. This is the standing prohibition in
this repository's architecture and decision records ("that span is **not** conductivity's
alone"). Chapters 5 and 6 both say it correctly ("the same KP~62.0 arms",
"the defined arms span"), and so does Chapter 9's running text ("the resolved
epistemic arms span a factor of 10.5 in $B$ ... the conductivity arm setting
their lower end").

**Fix.** Register: the parenthetical moved off the conductivity item and onto
the band sentence, which is where it belongs: "Epistemic/statistical interval:
6 to 9 on $B$, comparable on $\Delta\beta$, whose resolved arms span 0.86 to
0.97." Summary: "It makes the epistemic band" to "**It dominates an** epistemic
band", which is the claim Chapter 5 supports (conductivity is "the largest knob
at every section and every anchor") and the form Chapter 9's Overall Conclusion
already uses ("dominated by the aquifer conductivity"). Both numbers kept.

### F11. `The bracket narrows by more than an order of magnitude` generalises one cell (Ch. 9)

**Site.** `mainmatter/9...tex`, Section 9.1.3, the two-bracket paragraph.
**What was wrong.** Stated as a general property. Chapter 7 measures it at one
cell: "At KP~58.8 historically the bracket narrows from a factor of 185 to one
of 4.4" (a factor of 42). The engine's own record shows it is not general:
`conductivity-bracket-annualisation.md` §3.2.3 B9 gives the bulk-versus-matrix
system spans at the six cells where both are finite as 4.54/27.6, 4.40/185,
3.53/48.6, 1865/2762, 2.07/69.1 and 1.16/8.27, that is narrowing factors of
6.1, 42, 13.8, **1.48**, 33.4 and 7.1. Three of the six are below an order of
magnitude.
**Fix.** "The bracket narrows, **by more than an order of magnitude where it is
measured**, once the gradation reading has left the surface mechanisms
supporting the number." The mechanism, which Chapter 7 does establish
generally, is untouched; only the magnitude is scoped to where the chapter
measures it.

### F12. A single span factor quoted for a bracket the thesis says has none (Ch. 9 register)

**Site.** `mainmatter/9...tex`, Table "future research", conductivity row.
**What was wrong.** "The largest epistemic bracket in the study, spanning a
factor of $6.6\times10^{3}$ in conditional transient probability". Chapter 5
gives that figure with its anchor ("at the transition midpoint of KP~62.0 it
spans a factor of $6.6\times10^{3}$") and in the same subsection rules out
quoting it bare: "the bracket is stage-dependent, spanning orders of magnitude
at the low-stage end and collapsing toward unity in the design tail as the
conditional probability saturates, **so no single conductivity uncertainty
factor exists**." At the KP 62.0 *design-level* anchor the same section gives
roughly three orders of magnitude up against a factor of 15 down, a wider span
than 6.6e3.
**Fix.** "at mid-curve" appended, so the figure carries the stage class it
belongs to. "The largest epistemic bracket in the study" is untouched and is
supported: Chapter 5 has conductivity as the largest knob at every section and
every anchor.

---

## 2. Findings fixed after the author lifted the no-new-number restriction (F13 to F15)

These three were handed off in the first draft of this record because each
needed a number restored, a number added, or a scope decision the original
brief reserved to the author. The author authorised all three on 2026-09-03 and
they are now closed.

### F13. Chapter 9 quoted 6.0 and 3.9 for the crack-reduced comparator, and no results chapter reported them

**Site.** `mainmatter/9...tex`, Overall Conclusion: "against the crack-reduced
head a Dutch assessment instrument applies instead, the overestimation is
smaller, resolving at neither design level and standing at **6.0 and 3.9** at
the lowest stages above them whose counts support a ratio."

**What was wrong.** The two magnitudes appeared nowhere else in the document.
Chapter 6's corresponding passage said only that "the overestimation is
smaller", with no figure. Appendix H contains a 6.0, but as the *pure duration
effect* at 47.00 m, a different quantity that coincides there only because the
initiation gate is worth nothing at KP 62.0; at KP 57.4 the duration column
reads 3.2 against the 3.9 Chapter 9 quoted. An examiner tracing 6.0 found a
coincidence and tracing 3.9 found nothing.

**Cause.** Commit `6d6584e` (2026-08-21) put the pair into Chapter 6 and into
the Overall Conclusion together. The shortening campaign (`ad8fc2c`) removed
the Chapter 6 sentences and left the Chapter 9 one standing.

**The figures, re-verified from the artifacts for this pass** rather than taken
from the earlier reconciliations. Reading `p_f.C1` and `p_f.C4b` out of
`docs/decisions/adr0040-stage6-6-kp62_0-analysis.json` and
`...-kp57_4-analysis.json`, with the level axis anchored onto the published
Appendix H rows (0.25 m grid with the design HWL inserted as its own level):

| section | stage | `C1` | `C4b` | `C1/C4b` | transient failures in $10^5$ |
|---|---|---|---|---|---|
| KP 62.0 | 46.39 (design) | 4.80e-4 | 4e-5 | 12.0 | **4** |
| KP 62.0 | 46.50 | 1.49e-3 | 1.5e-4 | 9.93 | **15** |
| KP 62.0 | 47.00 | 3.001e-2 | 4.99e-3 | **6.01** | 499 |
| KP 62.0 | 50.50 (top of range) | 0.98025 | 0.68962 | **1.42** | 68 962 |
| KP 57.4 | 39.21 (design) | 3e-5 | 0 | undefined | **0** |
| KP 57.4 | 39.50 | 2.41e-3 | 6.2e-4 | **3.89** | 62 |
| KP 57.4 | 43.25 (top of range) | 0.99934 | 0.96437 | **1.04** | 96 437 |

So 6.0, 1.4, 3.9 and 1.0 are exact, the three design-neighbourhood rows carry
exactly four, fifteen and zero failing transient realizations, and all three
sit below the pre-registered thirty-realization floor, which is what "resolving
at neither design level" means.

**Fix.** The deleted material restored to Chapter 6, Section "The Production
Gap Is a Two-Component Story", in a form compressed from the original so it
costs less ink while carrying everything Chapter 9 leans on:

> Against the comparator an assessment instrument actually applies, rather than
> the gross-head production baseline, the overestimation is smaller, and the
> ladder measures it. The crack-reduced static variant $C_1$ of
> Table~\ref{tab: comparator ladder} applies the same exit-resistance reduction
> as the transient branch. It resolves at neither design level, on four, fifteen
> and zero failing transient realizations, and where the counts do support the
> comparison the factor against it runs from 6.0 at 47.00~m to 1.4 at the top of
> the attainable range at KP~62.0, and from 3.9 at 39.50~m to 1.0 at the top of
> the range at KP~57.4. That variant is also one of two ways to equalize the
> head convention between the criteria; Section~\ref{...} takes up both,
> including the new complementary reading that equalizes on the raw gross head
> instead.

Chapter 9 is untouched. Cost measured, not estimated: Chapter 6 absorbed the
addition entirely and still occupies 18 pages; the only layout consequence
anywhere in the document is section 6.4's heading moving one page inside it.

### F14. The Summary carried three of the four brackets on the bias

**Site.** `frontmatter/summary.tex`, final paragraph.

**What was wrong.** This repository's architecture and decision records require the
static-versus-transient bias to be quoted with four brackets, none of which
cancels: conductivity, seepage length, canonical event and **critical pipe
length**. The Summary quoted the bias figures and carried conductivity and
seepage length in the last paragraph and the canonical event in paragraph 3
("widening under the shorter approved event"). The critical pipe length, the
narrowest of the four, appeared nowhere in the Summary. Chapter 9's running
text and its answers register both carry all four.

**Fix.** The last sentence extended: "The same caveat applies to seepage length
**and to the critical pipe length, which shift the comparison by factors of
1.02 to 3.22 and 1.11 to 1.67**, effects that likewise do not cancel."

**Provenance of the added figures.** 1.11 to 1.67 is the displacement of the
static-to-transient ratio by the critical-pipe-length bracket, already in the
thesis twice: Chapter 6's standing-conditions register ("displacing the
transient probability by 1.00 to 2.08 and the ratio by 1.11 to 1.67") and
Chapter 8 ("1.11 to 1.23 for a shorter critical length and 1.19 to 1.67 for a
longer one"). It matches `docs/decisions/adr0049-critical-length-bracket.md`
line 227, "the narrowest of the three, at 1.11 to 1.67 against `k_aq`'s 2.24 to
163". No new quantity enters the document; the Summary now names a bracket the
body already carried. The front-matter page map is unchanged, so the Summary
still occupies the two pages it did.

### F15. `the update does not narrow the epistemic band` (Ch. 6) against `the bracket narrows` (Ch. 7)

**Sites.** `mainmatter/6...tex`, Section "What the Constraint Cannot Tighten":
"A third limit is that the update does not narrow the epistemic band." Against
`mainmatter/7...tex`: "Carried through the 2016 survival constraint the bracket
narrows ... by a factor of 1.96 at KP~58.8 and 2.81 at KP~60.0 historically".

**What was wrong.** The two are about different objects, and the flat clause
did not say which. Chapter 6 is arguing that the survival cannot choose between
candidate input populations, which is true and is what its own next sentences
say ("does nothing to decide which conductivity is right"; "an instrument for
the parametric uncertainty inside a model and not for the choice of the model's
own input population"). Chapter 7 measures the *propagated* bracket on the
annual numbers, where the rejection ladder is monotone in conductivity and the
upper arm comes down. As written, a reader taking the two chapters together saw
a contradiction.

**Fix.** The clause scoped to the object the paragraph goes on to argue about:
"A third limit is that the update does not narrow the epistemic band **on the
choice of input population**." Nothing else in the paragraph changed, and
Chapter 7 is untouched.

**The four sites that discuss the band now each name which object they mean**,
and no two conflict:

| Site | Object | Claim |
|---|---|---|
| Ch. 6, "What the Constraint Cannot Tighten" | the choice of input population | not narrowed |
| Ch. 9 §9.1.2, third limit | the same choice | "as wide as it found it" |
| Summary, RQ2 paragraph | "the epistemic **input** band" | unchanged |
| Ch. 7, "Also Conditional on the Aquifer Conductivity"; Ch. 9 answers register row 2 | the propagated bracket on the annual numbers | narrows by up to 2.81, "about a factor of two from a range spanning two to five orders of magnitude" |

---

## 3. Recorded, no action taken

### Chapter 8 Section 8.5 names three of the four brackets


`mainmatter/8...tex`, Section "Not Every Epistemic Knob Cancels in a Ratio",
names three of the four brackets when it states what the overestimation factors
must be quoted with (seepage lengths, conductivity, critical pipe length; the
canonical event is absent). That section's subject is epistemic *inputs* to the
two limit states, and the canonical event is a loading choice measured
elsewhere in the same chapter ("a shorter and sharper event ... raises the
static-to-transient ratio about threefold"), so the omission is defensible in
context. Chapter 6's standing-conditions register, Chapter 9's running text and
Chapter 9's answers register all carry all four.

---

## 4. What was checked and passed

### 4.1 Chapter 9, sub-question 1

| Claim | Supporting passage | Verdict |
|---|---|---|
| Lowers the probability at every section and stage; direction follows from the formulation | Ch. 6 "The Design-Level Bias"; Ch. 8 §8.1 "its direction is a theorem of the nested formulations" | OK |
| KP 62.0: $\Delta\beta$ 0.90 [0.85, 0.97], $B$ 26.9 [21.6, 35.3] at 46.39 m, on $10^6$ | Ch. 6 Eq. "kp62 bias" | OK |
| Intervals are paired bootstraps, branch intervals mapped Clopper-Pearson | Ch. 6 §"The Design-Level Bias" opening, explicit | OK. The construction the thesis asserted until 2026-08-30 is gone |
| KP 57.4: bound $\Delta\beta \geq 1.27$ ($B \geq 148$) at the design level, resolved 1.27 (42.7) 0.29 m higher | Ch. 6 Eqs. "kp57 bound", "kp57 anchor" | OK, quoted as a bound throughout |
| Drained sections $\Delta\beta$ 1.22 and 1.87; $B$ 2.75, 2.92, and 4.87, 6.03 under the shorter event | Ch. 6 conditions register, canonical-event row; Ch. 6 §"What the Replay Adds" | OK |
| Spread: more than a factor of fifty in $B$, only **0.9 to 1.9** in $\Delta\beta$ | Ch. 6 §"Why the Two Sections Differ" | OK. No site anywhere writes "0.9 to at least 1.9"; all four sites clean |
| Sections "rank differently on the two metrics"; KP 62.0 second to last, KP 60.0 third to first | Ch. 6 §"Why the Two Sections Differ" | OK. No site says the ordering "reverses" in this sense |
| Stage specificity: $B$ 21.6 at 46.50 m, $\Delta\beta$ unchanged at 0.90 | Ch. 6 §"KP 62.0: A Resolved Figure" | OK |
| Additive ladder 0.36 / 0.00 / 0.55 and 0.81 / 0.08 / 0.38 | Ch. 6 Table "gap components beta" | OK |
| Head convention: 75 to 97 per cent of the probability difference, **17 to 37** per cent of the index difference | Ch. 6 §"The Production Gap"; Ch. 8 §8.1 | OK. 17-37 appears only where 63-83 is adjacent; the two share a denominator at all four sites |
| Equal convention retains **63 to 83** per cent, KP 57.4 at most 66 because its denominator is the bound | Ch. 6 Table "equal convention" and following text | OK |
| The 54 per cent figure | Ch. 6: "against that section's point estimate of 1.56, which rests on two failing transient realizations and is carried as unresolved"; Summary: "the unresolved point estimate would give 54 per cent" | OK. Both sites name the denominator as unresolved; the figure appears nowhere bare |
| Time dimension and gate worth 0.57 to 1.55 | Ch. 6 §"The Two Criteria on One Head Convention" | OK |
| $B$ 1.04 to 1.43 at the top of each attainable range; $\Delta\beta$ dips at most 0.14 then rises up to 0.76 | Ch. 6 §"How the Bias Varies with Severity" | OK |
| Conditional on four brackets, none of which cancels | Ch. 6 conditions register; Ch. 5 §"the epistemic band"; Ch. 8 §8.5 | OK in Ch. 9. The Summary carried three: **F14** |
| Arms span 10.5 in $B$, "the conductivity arm setting their lower end", 0.11 in $\Delta\beta$ | Ch. 6 §"Why the Two Sections Differ"; `rq1_beta_reexpression_2026-08-28.md` §5 | OK, correctly attributed in the running text. The register cell was not: F10 |

### 4.2 Chapter 9, sub-question 2

| Claim | Supporting passage | Verdict |
|---|---|---|
| Rejects 5.67 and 3.36 per cent, at most 0.07 per cent at the other six strata | Ch. 6 §"How Much the Survival Rejects" (matrix 0.07 / 5.67 / 3.36 / 0.00; bulk at most 0.02) | OK |
| Erosion coefficient and conductivity means down about 4 per cent, all others within 1 per cent | Ch. 6, posterior paragraph | OK |
| Verified by full re-evaluation, zero disagreeing flags, "an equality and not an agreement within tolerance" | Ch. 6 §"What the 2016 Survival Constrains" opening | OK |
| The evidence inverts a deficiency-rating tiering; the inversion biases the update; shifts are an upper bound | Ch. 6 §"How Much the Survival Rejects" | OK, and the bias direction is stated in both places |
| Marginal transient rejection exactly zero in all eight strata and all sixteen runs; nesting is structural | Ch. 6 §"How the Constraint Divides", block quote and following | OK |
| Static comparator condemns 58 and 73 per cent against the transient 5.7 and 3.4 | Ch. 6, same section | OK |
| Peak-only over-rejection 2.75 and 3.90 (canonical), 1.45 and 1.57 (shorter) | Ch. 6 §"What the Time-Resolved Replay Adds" | OK, and both readings named as transient and on one sample |
| Seepage length within 1.4 per cent of prior mean, holding 0.49 to 0.78 of transient variance | Ch. 6 §"What the Constraint Cannot Tighten" | OK |
| Event set closed at 2016; 2011 bounded at 0.316 per cent; 2006 has no constructible loading | Ch. 6 §"The Limits of the Constraint"; Ch. 4 §"the sole survival constraint" | OK |
| The update leaves the epistemic band as wide as it found it | Ch. 6 "A third limit..."; contradicted by Ch. 7 and by Ch. 9's own register | **F9** |

### 4.3 Chapter 9, sub-question 3

| Claim | Supporting passage | Verdict |
|---|---|---|
| Reverses the ordering regional practice and the basin record would predict | Ch. 7 §"Piping Dominates" and §"Synthesis" | OK. This is the legitimate use of "reverse" |
| About 70 to 100 per cent historically at all four | Ch. 7 §"Piping Dominates" | OK in §9.1.3. Unscoped in the Overall Conclusion: **F8** |
| Warming: lead at three of four, level at KP 62.0 | Ch. 7 §"Piping Dominates" | OK |
| Shorter canonical event flips that cell alone | Ch. 7, same | OK |
| Composition seam moves the margin 1.0013 to 0.858, leaves every piping number untouched, changes that ordering alone in the reach | Ch. 7 §"Composed Conditional Fragility" and §"Piping Dominates" | OK |
| 4 of 114; the other 110 are explicit lower bounds with no dominance statement | Ch. 7 §"Where the Three Mechanisms Can Be Compared at All" | OK |
| Those four are also the highest-probability segments | Ch. 7, same, **"in the historical climate"** | **F7** |
| Scour exactly zero at all 114 in both climates; as-received conversion leads at 97, replaces nothing at 72, displaces overflow at 25, changes none of the four | Ch. 7 §"Fluvial Scour Is Identically Zero"; Appendix H §"The As-Received Erodibility Conversion across the Reach" | OK |
| Corrected branch has no independent validation of its own | Ch. 7, same; Appendix H event-based section | OK |
| Resistant gradation: share falls to 2 per cent at KP 58.8, essentially nothing at KP 62.0, piping leads at KP 60.0 alone under warming | Ch. 7 §"The Ordering Is Conditional on the Grain-Size Reading" | OK |
| Conductivity contests three of four historically, all four under warming | Ch. 7 §"Also Conditional on the Aquifer Conductivity" and its register row | OK. The Overall Conclusion's stronger form: **F6** |
| Field-population arm changes seven of eight cells | Ch. 7, same | OK |
| Upper arm takes KP 62.0 to 0.986 and 0.892 | Ch. 7, same | OK |
| Resistant reading concedes five of eight before any arm; upper arm returns four of those five | Ch. 7, same | OK |
| The two brackets leave no cell invariant; adopted values inside both | Ch. 7, same | OK |
| Bracket narrows by more than an order of magnitude once gradation carries the number | Ch. 7 gives one cell, 185 to 4.4 | **F11** |
| Survival narrows the bracket by up to 2.81; high prior rejected 11.6 to 25.8 times more heavily; all sixteen verdicts reproduce | Ch. 7, closing paragraph of that subsection | OK |

### 4.4 Chapter 9, sub-question 4

| Claim | Supporting passage | Verdict |
|---|---|---|
| Only amplitude delivered; wave elongation absent at the normalized-shape level | Ch. 7 §"What the Ensemble Actually Shifts" | OK |
| Above-toe days up 2.7 to 7.8; two-or-more excursions up 2.1 to 4.0 | Ch. 7 Table "rq4 attribution" and text | OK |
| Concentration about 150 and about 380 at the well-populated pair; 151 and 221 on 3 and 19 years | Ch. 7 §"Through Which Channel" | OK, and the thin counts are named in both places |
| Those years generate about 90 per cent of the annual total at the well-populated pair | Ch. 7, same | OK |
| Frequency exceeds severity at all four | Ch. 7, same | OK |
| Compound factors 3.7 and 6.5, neither resolvably above one | Ch. 7, same | OK |
| Annual factors 12.7, 5.5, 7.9, 12.7; order $10^{-2}$; two outer sections not distinguishable | Ch. 7 §"The Ratios at the Four Sections" | OK |
| Piping's own contribution rises 5.5 to 12.6; share falls at every section | Ch. 7 §"Piping Dominates" (12.6, 5.5, 7.9, 9.8) | OK |
| KP 62.0 pair rests to 11.8 per cent on stages above the attainable range | Ch. 7 §"The Ratios at the Four Sections"; Table "system annual" caption | OK, carried at all three Chapter 9 sites |
| KP 58.8 smallest ratio, largest absolute probability in both climates | Ch. 7, same | OK |
| Peak and duration not separable; duration stratifies the hazard | Ch. 7 closing structural qualification | OK |

### 4.5 Chapter 9, Overall Conclusion and recommendations

| Claim | Supporting passage | Verdict |
|---|---|---|
| Duration alone worth a factor of one to about six where counts support it | Ch. 6 §"The Production Gap", pure-duration column | OK |
| Crack-reduced comparator resolves at neither design level, standing at 6.0 and 3.9 | Was nowhere in Chs. 5 to 8 or the appendices; now Ch. 6 §"The Production Gap Is a Two-Component Story" | **F13** |
| Yabe: 0.061 at the breached section, 0 in $10^5$ and 0.005 at the survivors; committee minima 0.62 against 0.65 | Ch. 5 §"The Transient Race Condition: Support from a Single Field Case" | OK, and framed as ordering, not magnitude |
| "one out-of-sample test", "the only occasion" | Ch. 5: "The Yabe case is the only one in the set with a breach" | OK |
| At each design water level the composed probability is the piping probability | Ch. 7 §"Composed Conditional Fragility": overflow contributes exactly nothing at three of four and about one per cent at KP 58.8 | OK; Chapter 7 draws the same conclusion in the same words |
| Base-rate check: 0.65 expected in sixty years against zero observed; 2016 the modal outcome | Ch. 8 §"The Regional Assessment that these Levees are Erosion-Limited" | OK |
| Commensurability: only the piping branch is bracketed; shares rank mechanisms as this assessment knows them | Ch. 8 §"The Commensurability of the Mechanism Probabilities" | OK |
| Epistemic band 6 to 9 times the confidence interval, dominated by conductivity, production inside the bracket | Ch. 5 §"the epistemic band"; Ch. 6 §"Why the Two Sections Differ" | OK ("dominated by", not "made by") |
| Three scope conditions; the conservative gradation stands above the calibrated range at three of the four sections | Appendix B: "only one of the four production sections is inside the calibration domain on the matrix reading" | OK |
| Annual ranking KP 58.8, KP 60.0, then KP 62.0 and KP 57.4; KP 58.8 holds the lead except at the strongest arm; KP 60.0 falls to last on the measured berm alone | Ch. 8 §"What the Model Represents" annual ranges, with Table 7.2; ADR-0050 §Outcome | OK, and derivable from the printed numbers |
| Blankets fall a factor of three to seven short of the waiver | Ch. 8 §"The Initiation-Progression Distinction" | OK |
| Shortening KP 62.0's path by 7 m raised the design-level transient probability by roughly an order of magnitude | Ch. 8 §"Crest Heightening vs. Berm Widening"; Ch. 6 gives the factor 8.7 | OK |
| KP 58.8 spans up to factor 37 annually, its lower end a lower bound | Ch. 8 §"What the Model Represents": 7.4e-3 to 4.2e-3 to a lower bound of 2.0e-4 | OK |
| Model factor displaces the ratio 1.07 to 1.22; conductivity moves it 1.1 to 1.8 decades per decade, through two channels the static comparator lacks | Ch. 5 §"Two consequences follow"; Ch. 8 §"Not Every Epistemic Knob Cancels" | OK |
| All three investigations found distributed veins | Ch. 5 §"Two Structural Findings"; Appendix G | OK |
| Six extensions | Table has exactly six rows | OK |

### 4.6 Enumeration sweep

Every announced count in the main body, the Summary and all eleven appendices
was opened and counted. Delivering correctly: Ch. 1 (two sites), Ch. 2 (five),
Ch. 3 (three), Ch. 4 (three, one with an unmarked first item and a marked
second, which delivers), Ch. 5 (four, including the "Two Structural Findings"
subsection), Ch. 6 (three of the five), Ch. 7 (one), Ch. 8 (six, including
"Four limitations are structural"), Ch. 9 (four), Summary (three, including the
five-qualification chain and the three-consequence chain), Appendices A, B, C,
E, F, G, H, I and J (thirteen sites). Every `First,` / `Second,` / `Third,`
chain was traced to its announcement.

Two failures, both in Chapter 6, both fixed: **F1** and **F2**. The
`neither`-for-four in Chapter 8 (**F4**) and the unfollowable split sentence
(**F5**) were the other two known items.

### 4.7 Prohibited-claim register

| Prohibition (this repository's architecture and decision records) | Sites checked | Result |
|---|---|---|
| Bias quoted without its four brackets | Ch. 6 register, Ch. 8 §8.1 and §8.5, Ch. 9 §9.1.1 and register, Summary | Chapter 9 clean. The Summary carried three of four and now carries four: **F14** |
| Section ordering "reverses" in the RQ1 comparison | Every "revers*" in the document | Clean. The three live uses are the mechanism ordering under the resistant gradation (Summary, Ch. 7), the bracket-driven mechanism reversal (Ch. 7) and the median-offset-versus-deep-tail ordering (Ch. 6), all legitimate |
| "0.9 to at least 1.9" | Four sites carrying the range | Clean; all four read "0.9 to 1.9" |
| 54 per cent without the below-floor clause | Ch. 6, Summary | Clean; both name the denominator as unresolved |
| 63-83 paired with a complement other than 17-37 | Ch. 6, Ch. 8, Ch. 9, Summary | Clean; the pair is adjacent at every site |
| The 10.5-in-$B$ / 0.11-in-$\Delta\beta$ span attributed to conductivity alone | Ch. 5, Ch. 6, Ch. 9 text, Ch. 9 register, Summary | Two violations, both fixed: **F10** |
| Absolute $P_f$ without the conductivity bracket | Ch. 6 and Ch. 7 conditions registers, Ch. 7 table and figure captions, Ch. 9 register, Summary | Clean |
| KP 58.8 / KP 60.0 numbers without as-if-undrained | Summary paragraph 2 (global), Ch. 6 and Ch. 7 captions, Ch. 9 register caption, Overall Conclusion, recommendations | Clean |
| KP 62.0 warming value and ratio without the 11.8 per cent | Ch. 7 twice, Ch. 9 three times | Clean. The Summary does not single out KP 62.0; its 12.7 is a range endpoint shared with KP 57.4, which is exactly zero on this measure |
| Tilted importance sampler quoted as production | Ch. 6 §"The Design-Level Bias": "No weighted estimate enters this section" | Clean |

### 4.8 Terminology, against the 2026-08-29 audit

| Decision | Check | Result |
|---|---|---|
| The Japanese campaign is a **field evaluation**, not a validation | Chapter 5's title typesets as "Verification, **Field Evaluation**, and Global Sensitivity Analysis" (the filename and the `\label` retain the old word, correctly, since the label is referenced); §5.3 heading "Evaluation Against Japanese Field Cases"; table caption "The Japanese field-case campaign"; §5.1 says in terms "It is not called a validation" and gives the three reasons | Intact |
| Unbiasedness withdrawn | Ch. 5: "One tight instance and four sign checks establish that no bias is detectable at this resolution; they do not establish that the criterion is unbiased." Appendix G: "A single instance cannot establish that it is unbiased". The two other `unbiased` in Appendix E are the RQMC estimator, and the one in Appendix B is the published property of the Sellmeijer rule, not a claim of this work | Intact |
| Yabe reframed as ordering, not magnitude | Ch. 5: "What is reproduced is the ordering. A probability of 0.061 at a site that did breach is not in itself a confirmation of the magnitude". Summary: "reproducing an ordering rather than confirming a magnitude". Ch. 9: "Initiation-level reasoning does not tell those three sites apart" | Intact |
| IJkdijk band, and the Japanese set supporting "ordering and sign rather than magnitude" | Ch. 5 §5.3 opening | Intact |

---

## 5. The question the brief asks last

**Is there any sentence in Chapter 9 or the Summary that a careful examiner
could show the results chapters do not support?**

Before this pass, yes, and at seven sentences. Six of them are now repaired
(F6 at two sites, F7, F8, F9, F10 at two sites, F11, F12). The three that an
examiner was most likely to reach were:

1. **"its low arm hands the lead to overflow at three of the four sections
   historically"** (Overall Conclusion) and its Summary twin. Chapter 7 says
   overflow leads at six of eight *cells*, and states explicitly that the
   seventh, KP 57.4 historically, is not one of them because both mechanisms go
   to exactly zero there. Two of four, not three. Fixed.
2. **"Those four segments also have the highest annual system failure
   probabilities among the 114"** (Section 9.1.3). False under warming: a
   surface-only segment at 62.2 km carries 1.10e-2 against KP 57.4's 9.53e-3.
   Fixed by restoring Chapter 7's own climate scope.
3. **"leaving the epistemic band exactly as wide as it found it"** (Section
   9.1.2), contradicted by Chapter 7 and by Chapter 9's own answers register
   forty lines below it. Fixed.

**And a seventh, which the first round could only hand off.** Chapter 9's
Overall Conclusion quoted the crack-reduced comparator as "standing at 6.0 and
3.9 at the lowest stages above them whose counts support a ratio", and no
results chapter or appendix reported either figure in that role: an examiner
asking where 3.9 comes from would have found nothing. The numbers were correct
against the engine artifacts all along, and are re-verified in F13 above from
`p_f.C1` and `p_f.C4b` directly. The shortening campaign had removed the
Chapter 6 sentences that carried them, and those are now restored, absorbed
inside Chapter 6's existing 18 pages.

**The answer now.** No. Every declarative claim in Chapter 9 and in the Summary
traces to a passage in Chapters 5 to 8 or the appendices that carries it at the
stated strength. The four claims an examiner was most likely to reach, the
overflow-lead count, the top-four-segments coincidence, the epistemic-band
invariance and the unsupported 6.0 and 3.9, are all closed, and the last of them
is closed by restoring evidence to a results chapter rather than by weakening
the conclusion.

Two residual properties of the document are worth stating, because they are
choices rather than defects. Chapter 8 Section 8.5 names three of the four
brackets when it says what the overestimation factors must be quoted with,
which is a subset and not a contradiction, and is defensible on that section's
own subject (see Section 3). And the epistemic band is discussed as two
different objects, the choice of input population and the propagated bracket on
the annual numbers; after F15 every site names which one it means, and the
table in F15 lists all four sites so a later pass does not have to re-derive
the distinction.
