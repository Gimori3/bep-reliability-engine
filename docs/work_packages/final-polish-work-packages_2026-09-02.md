# Final-polish work package set for the thesis, 2026-09-02

Written after a full read of `d:\repositories\msc-thesis` at commit `87df338` (main
body 99 pages, References on 100, 193 pages in all, 106 citation keys, 387 labels,
working tree clean and pushed) and of the audit record in this repository.

**What this is.** Nine work packages for independent review passes, ranked by
expected value, to run before the owner's own final read-through. Each is
self-contained and assumes a cold start. None of them runs a new sweep, adds an
analysis, or takes the main body past 100 pages.

**What it is not.** It is not a campaign authorisation. Each work package carries its
own narrow scope; the surgical default of the msc-thesis project rules is otherwise in
force.

---

## 1. Assessment: where the thesis actually stands

The document is in unusually good condition. Six audit campaigns have already
landed on it: a whole-document number reconciliation (2026-08-21), a
reliability-index reconciliation (2026-08-30), three citation-audit passes
(2026-08-30 to 08-31, 37+ attribution defects fixed), a terminology and evidence
audit (2026-08-29), a reviewer-feedback triage (2026-08-29), and a shortening
campaign closed at 99 pages with a two-stage pre-push gate (2026-09-02). The
mechanical state is clean: zero undefined references, zero undefined citations,
zero em dashes, zero Japanese script, no float-only pages, twelve overfull hboxes
none above 15.4 pt.

The science is honestly presented. Every headline number carries its bracket, the
null result of Phase 2 is reported as a null result and then reframed on defensible
grounds, the dominance claim is bounded at 4 of 114 segments and contested from
both ends, and the two results chapters each open with a standing-conditions
register. The main body carries no software content, which the architecture and decision records rule
requires and which most engineering theses fail.

**What remains is concentrated in four places, and one of them is a genuine defect
in a headline figure.**

### 1.1 The figures have never been audited

Every prior pass read `.tex`. The 30 bitmap figures in the main body are PNGs and
were invisible to all of them. Reading them as rendered turns up four classes of
defect, one of which is material:

- **`figures/rq1_hwl_dbeta_resolved.png` contradicts the text on the thesis's
  headline number.** The right-hand panel annotates the design-HWL anchor as
  `Δβ = 0.90 [0.85, 0.98]`. The text of Section 6.2.1, Table 9.1, the Summary and
  the Chapter 8 discussion all say `[0.85, 0.97]`. The cause is traceable:
  `docs/decisions/rq1-beta-reexpression.json` carries **three** paired-bootstrap
  draws of that same interval, `[0.8465, 0.9655]`, `[0.8516, 0.9693]` and
  `[0.8498, 0.9751]`; `scripts/rq1_beta_analysis.py` plots the third and the
  thesis quotes the second. The 2026-08-30 reconciliation verified the text
  against the artifact and never looked at the figure.
- **British spellings baked into figure text**, in a document that is uniformly
  American: `neighbourhood` (`scripts/rq1_beta_analysis.py:1985`,
  `scripts/hwl_bias_resolution.py:1804`), `stabiliser` (`scripts/_figstyle.py:202`,
  so it appears in every figure that shades the hypothetical extension),
  `characterised` (`phase3_rq4_four_sections.png`), `normalised`.
- **Italic descriptive subscripts** in figure math, against a *settled* notation
  decision in the msc-thesis project rules: `$k_{aq}$`, `$z_{toe}$`, `$\gamma'_{bl}$`,
  `$\lambda_{ac}$`, `$\beta_{trans}$`, `$\beta_{static}$`. The thesis body is
  uniform on `\mathrm{}` at 111 sites for `bl` alone.
- **House-style violations the prose forbids**: `--` used as a dash inside figure
  annotations, `6.4x wider` where the prose writes "times", `95%` where the prose
  writes "per cent".

Everything is regenerable. `results/` and `.venv` are present, the generating
scripts are in `scripts/`, and `_figstyle.py` is a single shared style module, so
the `stabiliser` fix is one line for every affected figure.

### 1.2 One numeric block has never been reconciled

The coverage map has a dated hole:

| Pass | Date | Covers |
|---|---|---|
| `thesis_number_reconciliation_2026-08-21.md` | 2026-08-21 | whole document as it then stood |
| `thesis_number_reconciliation_2026-08-30.md` | 2026-08-30 | the reliability-index block only |
| `PREPUSH_GATE_2026-09-02*.md` | 2026-09-02 | numeric-token *set* diff, not values |

So every number introduced between 2026-08-21 and 2026-08-28 that is not part of
the reliability-index block has never been traced to an artifact. That is the
ADR-0050 drained bracket (accepted 2026-08-22, and it reaches Chapter 3, both
results chapters, the Chapter 8 limitations register, the Chapter 9
recommendations and the Summary), the ADR-0049 critical-pipe-length bracket, the
composition-seam study, the conductivity posterior-side study, the annualisation
hazard-sampling intervals, the foreshore-exhaustion indicator, and the
Japanese-practice reframing. These are not minor: the drained bracket is what
makes the Chapter 9 ranking quotable, and the hazard-sampling intervals appear in
every bracketed entry of Table 7.2.

One number in the Overall Conclusion could not be traced to any artifact in a
first search: "0.65 expected failures in sixty years", with its companions 0.52,
0.38, 0.69 and 0.091. It may exist; it should be found or flagged.

### 1.3 Two enumeration and reference defects survived every pass

Found by reading, not by any scan:

- `mainmatter/6...tex:~925`: "**Two things** prevent this from being reported as
  the answer" is followed by three, the third introduced with "Third,".
- `mainmatter/8...tex:~122`: "conditional on the adopted aquifer conductivity and
  seepage lengths, on the conservative grain-size reading, and on the decision not
  to credit the installed toe drainage; **neither** cancels between the branches"
  uses "neither" for four antecedents.
- `mainmatter/8...tex:~118`: "That split is a duration channel, untouched and the
  one the climate argument below rests on, against a stage channel, just
  re-scoped." Near-unparseable, and a shortening-campaign artifact.
- `mainmatter/6...tex:~1140`: "condemning 34 per cent of the prior ... against 5.4
  for the transient one" drops the unit that the parallel Chapter 8 sentence
  carries.
- **Appendix J promises a repository that no page names.** Its opening footnote
  says the source code is "archived in the project repository indicated on the
  title page". The title page names no repository. There is no `github`,
  `gitlab`, `zenodo` or `4TU` string anywhere in the document.

### 1.4 The story loses its close, and the thesis never states its contribution

- **Chapter 6's Synthesis is three sentences with no number in it**, ending an
  18-page chapter that resolves two research questions. The repository's own
  pre-push gate named this the single change it would undo. Chapter 7's is three
  short paragraphs, also numberless. There is exactly one page of margin under the
  ceiling.
- **The thesis never says what it contributes.** Zero occurrences of
  "contribution", "novel", "first study", "to the author's knowledge". Chapter 2
  states a gap; Chapter 9 answers questions; nothing asserts what the field gains.
  The work has at least three defensible contributions and claims none of them.
- **An open owner ruling is still open.** `figures/rq1_beta_curves.png` was
  committed on 2026-08-28, shows both branches on the reliability-index axis at
  all four sections, and is referenced by no `\includegraphics`. The project log
  flagged it as "either a dropped placement or a surplus file" and nobody ruled.
  It is the natural companion to a chapter that now leads in `β`.

### 1.5 Lower-order, real, cheap

- `artifact` 8 sites, `artefact` 8 sites. `favour` twice in typeset prose.
- `unremediated` 11, `unreinforced` 11; `berm-widened` 5, `berm-only` 4. Two
  synonym pairs at near-equal counts, for the same two sections.
- 28 stacked-label groups, one of which (`sec: Pre-Calculated Surface Failure
  Fragility Curves from Uemura (2025)`, stacked onto Section 3.7) names something
  no section is about. Two dead labels on Table 3.1.
- Mean sentence length 25 to 30 words per chapter, 34 in the Summary, 80
  sentences over 55 words in the main body.

---

## 2. The work packages

Run them in this order. Work packages 1 to 3 find defects, 4 to 7 improve the document,
8 normalises, 9 gates. Work packages 5, 6 and 7 share one page of budget; work package 9 must
be last.

---

### Work package 1. Audit the figures as rendered, and repair them at source

**Why first.** It is the only unaudited surface in the document, it holds a
confirmed contradiction with the thesis's headline number, and every fix is
verifiable by pixel diff.

```
You are auditing the 30 bitmap figures and 3 TikZ figures of an MSc thesis that is
otherwise finished, and repairing what you find at source. Two repositories are in
play:

  d:\repositories\msc-thesis            the LaTeX thesis (an Overleaf mirror)
  d:\repositories\bep-reliability-engine the engine that generates every figure

READ FIRST, COMPLETELY, IN THIS ORDER
  1. the msc-thesis project rules, all of it. The "Settled notation decisions" and
     "Writing-style rules" sections are the standard you are auditing against.
  2. this repository's architecture and decision records, all of it.
  3. bep-reliability-engine/scripts/_figstyle.py, all of it. It is the shared
     style module and several defects live in it.

WHAT NOBODY HAS DONE
Every audit this thesis has had read .tex source. The figures are PNGs and were
invisible to all of them. You are the first pass to open them.

YOUR AUTHORISATION AND SCOPE
You may edit figure-generating scripts under bep-reliability-engine/scripts/,
regenerate the affected PNGs, copy them into msc-thesis/figures/, and edit a
figure CAPTION in msc-thesis where the audit shows the caption is wrong or is
compensating for something the figure should carry itself. You may NOT edit any
other thesis prose, may NOT change any computed value, and may NOT run a
production sweep, a Phase 2 replay or a Phase 3 campaign. Everything you need is
already in bep-reliability-engine/results/ and docs/decisions/. Regeneration is
re-rendering, not re-analysis; if a script wants to recompute a result rather than
read a persisted one, stop and report it instead.

CONSTRAINTS THAT NOTHING LIFTS
  - The main body is 99 pages and the ceiling is 100, hard. No figure may change
    size or aspect ratio in a way that moves a page. Verify by the documented
    method: build an ISOLATED copy (copy report.tex, tudelft-report.cls,
    references.bib, frontmatter/, mainmatter/, appendix/, figures/ into a scratch
    directory outside the repo and run latexmk -xelatex THERE; never use -outdir
    against the working tree, which silently reads the stale report.bbl) and read
    page extents off the \contentsline entries of the fresh .toc.
  - No em dashes and no "---" in any .tex you touch. Ranges are "X to Y".
  - No Japanese script anywhere.
  - Preserve every \label and every citation key exactly.

WHAT TO DO

Step 1. Enumerate. List every \includegraphics in mainmatter/ and appendix/, and
every TikZ figure. For each, record the source script in the engine that generates
it (grep the output filename under scripts/). Report any figure you cannot trace
to a generator.

Step 2. Read each main-body figure as an image and check it against five
standards, recording a verdict per figure:

  (a) NUMBERS. Every number annotated inside the figure must agree with every
      place the thesis states the same quantity. THERE IS AT LEAST ONE KNOWN
      FAILURE, and you must confirm and fix it: figures/rq1_hwl_dbeta_resolved.png
      annotates the KP 62.0 design-HWL anchor as "Δβ = 0.90 [0.85, 0.98]" while
      the thesis says [0.85, 0.97] at every site. The cause is that
      docs/decisions/rq1-beta-reexpression.json carries three paired-bootstrap
      draws of that interval, [0.8465, 0.9655], [0.8516, 0.9693] and
      [0.8498, 0.9751]; scripts/rq1_beta_analysis.py reads the third and the
      thesis quotes the second ([0.852, 0.969], per
      docs/thesis_number_reconciliation_2026-08-30.md correction 2). Decide which
      record is canonical, make the figure and the text agree, and say in your
      report which one you moved and why. Then check every other figure for the
      same class of disagreement, including the 46.50 m anchor, the KP 57.4
      anchors, the equal-convention values and every annual probability.
  (b) NOTATION. The msc-thesis project rules require descriptive subscripts to be upright:
      k_\mathrm{aq}, \gamma'_\mathrm{bl}, z_\mathrm{toe}, \lambda_\mathrm{ac},
      I_\mathrm{er}, h_\mathrm{obs}, D_{r,\mathrm{m}}, C_{u,\mathrm{m}}. The
      figures use italic: $k_{aq}$, $z_{toe}$, $\gamma'_{bl}$, $\lambda_{ac}$,
      $\beta_{trans}$, $\beta_{static}$. Bring the figures onto the document's
      settled convention.
  (c) ORTHOGRAPHY. The thesis is uniformly American. Figures carry "neighbourhood"
      (scripts/rq1_beta_analysis.py:1985 and scripts/hwl_bias_resolution.py:1804),
      "stabiliser" (scripts/_figstyle.py:202, which reaches every figure that
      shades the hypothetical extension), "characterised", "normalised". Sweep all
      of scripts/ for figure-facing strings, not just these.
  (d) HOUSE STYLE. Figures use "--" as a dash, "6.4x wider" for "times", "95%" for
      "per cent". The prose forbids all three. Bring the figure text into line.
  (e) CONVENTION CONSISTENCY. The ADR-0024 rule is that KP 62.0's grid above
      50.5 m is a hypothetical fit stabiliser and must never be plotted as
      attainable. figures/rq1_beta_curves.png shades it; figures/fragility_tail_log.png
      does not, and its caption spends four lines compensating. Report, do not
      unilaterally change, whether the unshaded panel should carry the band, since
      that caption is deliberate. Flag any other figure whose x-axis crosses its
      section's attainable maximum without the band.

Step 3. Read each caption against its figure. A caption must be true of what the
figure actually draws, must name every panel the figure has, and must not promise
a mark the figure does not carry. Report mismatches; fix only the unambiguous ones.

Step 4. Fix, regenerate, prove. For every change: edit the script, regenerate only
that figure, and PIXEL-DIFF the new PNG against the committed one to demonstrate
that only the intended region changed. Report the diff extent per figure. If a
regeneration changes a plotted value rather than a label, stop: that means the
underlying record moved and it is a reconciliation problem, not a figure problem.

Step 5. Prove the document is unmoved. Isolated build. Report: undefined
references (expect 0), undefined citations (expect 0), citation keys (expect 106),
labels (expect 387), main body pages (expect 99, References on 100), per-chapter
map (expect 6, 10, 12, 12, 11, 18, 12, 11, 7), appendices A to K (expect 7, 8, 7,
3, 12, 4, 5, 13, 5, 7, 3 = 74), total 193, overfull hboxes (expect 12 or fewer,
none above 15.4 pt).

DELIVERABLE
A report at bep-reliability-engine/docs/figure_audit_2026-09-XX.md with one row
per figure and per standard, the fixes applied, the pixel-diff evidence, and a
list of anything you found and deliberately did not change. Commit the engine and
thesis changes separately, with messages naming this work package. Do not push.

BEFORE YOU FINISH
State plainly: did any figure disagree with the text on a number besides the known
one, and is the thesis's headline confidence interval now identical in the figure,
the equation, Table 9.1, the Chapter 8 restatement and the Summary?
```

---

### Work package 2. Reconcile the numeric blocks no pass has covered

**Why second.** A wrong number in a results chapter is the most damaging defect
available, and there is a dated, provable coverage hole.

```
You are performing a claim-by-claim numeric reconciliation of the parts of an MSc
thesis that no previous reconciliation pass covered. Two repositories:

  d:\repositories\msc-thesis            the thesis
  d:\repositories\bep-reliability-engine the engine and every artifact of record

READ FIRST, COMPLETELY
  1. the msc-thesis project rules
  2. this repository's architecture and decision records, especially "Quoting results"
  3. bep-reliability-engine/docs/thesis_number_reconciliation_2026-08-21.md
     (method, verdict vocabulary, and its 2026-08-23 addendum)
  4. bep-reliability-engine/docs/thesis_number_reconciliation_2026-08-30.md
     (the same method applied to the reliability-index block; do not redo it)

THE COVERAGE HOLE YOU ARE FILLING
The 2026-08-21 pass covered the whole document as it then stood. The 2026-08-30
pass covered only the reliability-index block. The 2026-09-02 pre-push gate
compared numeric-token SETS across the shortening campaign and never checked a
value against an artifact. Therefore every number introduced between 2026-08-21
and 2026-08-28 that is not part of the reliability-index block has never been
traced. Your scope is exactly that set, plus anything either earlier pass marked
FLAG that is still open.

THE BLOCKS IN SCOPE, WITH THEIR ARTIFACTS
  - ADR-0050 drained-configuration bracket (accepted 2026-08-22, so wholly after
    the 08-21 pass). Artifacts: docs/decisions/adr0050-drained-configuration-bracket
    .{md,json}, adr0050-drained-bracket-annualisation-{matrix,bulk}-posterior.json,
    0050-toe-gradient-relief-drained-bracket.md. Thesis sites: the Chapter 6 and
    Chapter 7 standing-conditions registers, Section 8.9.5 "What the Model
    Represents", the Chapter 8 limitations register, the Chapter 9 annual ranking
    and recommendations, and the Summary. Values to trace include 0.263 to 0.108,
    0.314 to 0.111, 7.4e-3 to 4.2e-3 to a lower bound of 2.0e-4, 1.8e-3 to 6.4e-4
    to zero, the fractions 0.57 and 0.35, the 0.027, the factor 37, the "34 per
    cent against 5.4", the 1.30 to 0.30 and 0.97 to 0.23 toe gradients with their
    77 and 76 per cent relief, and the 0.7 to 1.0 m displacement of the lowest
    initiating stage.
  - ADR-0049 critical pipe length: adr0049-critical-length-bracket.md,
    adr0049-critical-length-companion.json, 0049-critical-pipe-length-override.md.
    Trace 1.00 to 2.08, 1.11 to 1.67, the split 1.11 to 1.23 / 1.19 to 1.67, the
    "eighty-nine levels", and the exact-reciprocal claim to 2.2e-16.
  - Composition seam: composition-seam-rating-error.{md,json}. Trace 1.0013 to
    0.858, 1.16 to 1.26, at most 1.07, at most 0.039, the share 0.500 to 0.462,
    and the reach counts 31 to 8 and 109 to 69.
  - Conductivity on the posterior side: conductivity-bracket-posterior-side.{md,json}
    and -bulk.json. Trace the factor up to 2.81, the 11.6 to 25.8, the 65.5 and
    86.9 per cent against 5.7 and 3.4, and "all sixteen ordering verdicts reproduce".
  - Conductivity through the annualisation: conductivity-bracket-annualisation
    .{md,json} and -bulk.json. Trace 69 to 185, 1.5 to 37, 0.986 and 0.892, the
    "3 of 4 historically and 4 of 4 under warming", the 234 and 671, and the 3.4
    to 7.3.
  - Hazard-sampling intervals: annualisation-hazard-sampling-uncertainty.{md,json}.
    Trace EVERY bracketed interval in Table 7.2, the half-widths 29 to 58 and 11
    to 21 per cent, the four ratio intervals, the KP 57.4 / KP 62.0 non-separation,
    the shares 0.48 to 0.53 and 0.69 to 0.98, and the 1.6 to 2.4 widening.
  - Foreshore exhaustion: r10-foreshore-exhaustion-screening.{md,json}. Trace the
    44 m, the 1 m/h central rate, and "roughly an order and a half of magnitude".
  - Event closure: adr0044-event-closure-bound.json. Trace the 0.316 per cent.
  - The Japanese-practice block, from docs/japanese_levee_failure_criterion_review
    _2026-08-28.md: 40.8 per cent, 25.1 per cent, 10,000 km, the roughly 3 m
    cohesive-cover waiver and the "factor of three to seven short".
  - ONE UNLOCATED CLAIM. The Overall Conclusion states "0.65 expected failures in
    sixty years against zero observed", with a probability 0.52 that none is
    observed, 0.38 and 0.69 crediting the berm, an aggregate annual piping
    probability of 1.07e-2 across the four segments, and 0.091 for the failure of
    at least one of the four at 2016 stages. A first search did not find the
    artifact behind these. Find it, or open a FLAG saying it is an internal
    arithmetic construction and show the arithmetic.

METHOD
Use the 2026-08-21 verdict vocabulary exactly: EXACT, ARITH, ROUND, FIXED, FLAG,
CITED. The unit of the register is a claim-group, not a token. For each group
record the thesis site or sites, the artifact and the key inside it, and the
verdict. Prefer the machine-readable .json over the .md companion where they
differ, and say so when they do.

YOUR AUTHORISATION AND SCOPE
You may correct a diverging number in msc-thesis prose, a table cell or a caption,
by the SMALLEST edit that makes it agree with its artifact. You may not rewrite a
sentence that is already correct, may not add a number the thesis does not carry,
may not change a computed value in the engine, and may not run a sweep, a replay
or a campaign. If a divergence is a judgment call rather than an error, open a
FLAG and leave the text alone.

CONSTRAINTS THAT NOTHING LIFTS
  - Main body 99 pages, ceiling 100 and hard. Verify with an isolated build, per
    the method in the msc-thesis project rules; never latexmk -outdir against the working
    tree.
  - No em dashes or "---". Ranges "X to Y". No Japanese script.
  - Preserve every \label and every citation key.
  - A corrected number must be corrected at every site it is STATED and at every
    site it is IMPLIED. This is the repository's own hard-won lesson: the
    2026-08-30 pass found a figure that had been corrected at seven sites and left
    wrong in its own complement, and the 2026-08-31 citation pass found a fix
    whose second site had been missed. After each fix, search the pre-fix wording
    across all .tex.

DELIVERABLE
bep-reliability-engine/docs/thesis_number_reconciliation_2026-09-XX.md, in the
form of its two predecessors, with headline counts, the register, and an explicit
statement of what it does and does not supersede. Then the whole-document gates
from the 08-30 pass: label count with zero duplicates and zero dangling refs
(USE A NEWLINE-TOLERANT MATCHER; a naive one reports 32 false positives from
line-wrapped \ref arguments), zero em dashes, zero Japanese script, zero
hyphen or en-dash ranges, 106 citation keys with zero unresolved, and eleven
appendices agreeing between Chapter 1's roadmap figure, Section 1.6 and report.tex.

BEFORE YOU FINISH
State plainly how many claim-groups you traced, how many diverged, and whether any
number in a results chapter or the Summary is still not traceable to an artifact.
```

---

### Work package 3. Audit the claims for internal logic and evidence strength

**Why third.** The numbers can all be right while an inference overstates what
they support. No pass has checked inferential validity.

```
You are auditing an otherwise finished MSc thesis for internal logic: whether each
claim follows from what the thesis itself measured, at the strength stated. You
are NOT checking arithmetic, which a separate pass covers, and you are NOT
improving prose.

  d:\repositories\msc-thesis            the thesis
  d:\repositories\bep-reliability-engine the engine

READ FIRST, COMPLETELY
  1. the msc-thesis project rules, all of it, especially binding rules 1 and 2.
  2. this repository's architecture and decision records, especially "Quoting results", which lists
     the claims this project has already got wrong and the exact form each must
     now take.
  3. msc-thesis/mainmatter/9. Conclusions and Recommendations.tex, in full.
  4. msc-thesis/frontmatter/summary.tex, in full.

WHAT YOU ARE LOOKING FOR
  (a) A conclusion stated more strongly than the chapter that supports it. Take
      every declarative claim in Chapter 9 and in the Summary and find the passage
      in Chapters 5, 6 or 7 that carries it. Check the strength matches: a bound
      quoted as an estimate, a range quoted without the condition its own register
      attaches, a "the only" or "at every" or "the largest" that the supporting
      table does not license, a share quoted against a denominator the reader
      cannot see.
  (b) Enumerations that do not deliver what they announce. FOUR ARE ALREADY KNOWN
      AND YOU MUST FIX THEM:
        - mainmatter/6...tex, in the scale-exponent subsection: "Two things
          prevent this from being reported as the answer" is followed by three
          items, the third opening "Third,".
        - mainmatter/8...tex, at the close of Section 8.1: "conditional on the
          adopted aquifer conductivity and seepage lengths, on the conservative
          grain-size reading, and on the decision not to credit the installed toe
          drainage; NEITHER cancels between the branches" uses "neither" for four
          antecedents.
        - mainmatter/8...tex, Section 8.1: "That split is a duration channel,
          untouched and the one the climate argument below rests on, against a
          stage channel, just re-scoped." This is not followable. Rewrite it to
          say what it means, in one or two sentences, adding no claim.
        - mainmatter/6...tex, in "How the Constraint Divides": "condemning 34 per
          cent of the prior at KP 58.8's observed peak against 5.4 for the
          transient one" drops the unit that the parallel Chapter 8 sentence
          carries.
      Then sweep for every other case: every "Two", "Three", "Four", "Five", "Six"
      that introduces a list, and every "First,"/"Second,"/"Third," chain.
  (c) Claims the project has explicitly forbidden. this repository's architecture and decision records
      forbids, among others: quoting the static-vs-transient bias without its four
      brackets; saying the section ordering "reverses" in the RQ1 comparison when
      it re-orders without reversing; writing "0.9 to at least 1.9" for the index
      range; quoting the retained fraction 54 per cent without the clause naming
      it a below-floor point estimate; pairing 63 to 83 per cent with any
      complement other than 17 to 37; attributing the 10.5-in-B / 0.11-in-Δβ
      epistemic span to conductivity alone. Check each, at every site. Note that
      "the ordering reverses" IS legitimate for the mechanism-dominance claim
      under the resistant gradation, and must not be edited there.
  (d) A conditional that has drifted from its number. Every absolute probability
      must carry the conductivity bracket; every ratio must additionally carry
      seepage length, canonical event and critical pipe length; every KP 58.8 and
      KP 60.0 number must be as-if-undrained; the KP 62.0 warming annual value and
      its ratio must carry the 11.8 per cent above-attainable share. Check that
      each caveat still sits with its number after the shortening campaign moved
      material between chapters and appendices.
  (e) Terminology that carries an evidence claim. The 2026-08-29 terminology audit
      renamed the Japanese campaign a FIELD EVALUATION, withdrew unbiasedness in
      five places, and reframed Yabe as ordering-not-magnitude. Confirm none of
      that has crept back, in the main body, the appendices, the Summary or any
      caption.

YOUR AUTHORISATION AND SCOPE
You may edit prose in mainmatter/ and appendix/ where an audit finding requires it,
by the smallest edit that repairs the logic. You may not restructure, may not
re-word a passage that passes, may not add or remove a number, may not add a
citation, and may not touch report.tex, references.bib or the .cls.

CONSTRAINTS THAT NOTHING LIFTS
  - Main body 99 pages, ceiling 100 and hard; verify with an isolated build.
  - No em dashes, no "---", ranges "X to Y", no Japanese script.
  - Preserve every \label and every citation key.
  - If you think a claim is wrong rather than merely overstated, STOP and report
    it. Do not silently weaken a result.

DELIVERABLE
A report at bep-reliability-engine/docs/claim_logic_audit_2026-09-XX.md listing
every claim examined, its supporting passage, the verdict, and the edits made.
Separate findings you fixed from findings you are handing to the owner.

BEFORE YOU FINISH
State plainly: is there any sentence in Chapter 9 or the Summary that a careful
examiner could show the results chapters do not support?
```

---

### Work package 4. Red-team the thesis as an examiner, and close the gaps that land

**Why fourth.** Everything above verifies what is written. This finds what is
missing, and it is the work package most directly aimed at the grade.

```
You are an adversarial examiner reading a finished MSc thesis for its defence.
Your job is to find the attacks that would actually land, and then to close the
ones that a sentence or two of existing evidence would close.

  d:\repositories\msc-thesis            the thesis (READ ALL NINE CHAPTERS)
  d:\repositories\bep-reliability-engine the evidence base

READ FIRST, COMPLETELY
  1. the msc-thesis project rules
  2. All nine main-body chapters and the Summary.
  3. bep-reliability-engine/docs/defence_brief_2026-08-22.md (it predates the RQ1
     reliability-index campaign and the shortening campaign, so treat it as a
     starting point, not as current).
  4. bep-reliability-engine/docs/work_packages/reviewer-feedback-triage_2026-08-29.md, which
     records a real reviewer's major-revision review and what was done about it.

PHASE 1: ATTACK
Produce the fifteen hardest questions a committee could ask, ranked by how much
damage an unanswered version would do. Be genuinely adversarial. The obvious
lines of attack, which you should sharpen rather than merely list:
  - "Your headline result is that a transient criterion gives lower failure
    probabilities than a static one. You say yourself the direction is a theorem.
    What did you actually find?"
  - "Your static comparator uses the gross head, which you concede no assessment
    instrument applies. Is the whole comparison against a straw man?"
  - "Your Bayesian update rejects nothing the static criterion does not. Isn't
    Phase 2 a null result?"
  - "Piping dominates at four segments out of 114, both of your top two are
    evaluated as if drains that exist were absent, and your conductivity bracket
    spans three orders of magnitude. What is the dominance claim worth?"
  - "Your grain sizes are outside the calibration range of the resistance rule at
    three of four sections. Why should I believe any absolute number?"
  - "You report a plane-strain exponent as your baseline and admit that at the
    three-dimensional exponent your gap nearly vanishes. Why is the baseline the
    one that flatters your result?"
For each attack, find where in the thesis the answer already lives, quote it, and
grade the answer: FULLY ANSWERED IN PLACE, ANSWERED BUT BURIED, ANSWERED ONLY IN
AN APPENDIX, or NOT ANSWERED.

PHASE 2: CLOSE
For every attack graded ANSWERED BUT BURIED or ANSWERED ONLY IN AN APPENDIX, and
only where the answer already exists in the thesis or in a named engine artifact,
make the smallest edit that puts the answer where the attack lands: usually one
sentence, or a pointer, at the place the reader forms the objection.

For every attack graded NOT ANSWERED, do NOT invent an answer. Report it to the
owner with what evidence would be needed.

YOUR AUTHORISATION AND SCOPE
Prose edits in mainmatter/ and appendix/ only, and only the additions Phase 2
licenses. No restructuring, no new analysis, no new citation, no new number that
is not already in the document or in a named artifact.

CONSTRAINTS THAT NOTHING LIFTS
  - Main body 99 pages, ceiling 100 and hard. You share that one page with two
    other work packages, so keep your total additions under about 15 typeset lines and
    PROVE the page count with an isolated build. If an addition costs a page, find
    the offsetting restatement in the same chapter, or hand the addition to the
    owner instead of taking it.
  - No em dashes, no "---", ranges "X to Y", no Japanese script.
  - Preserve every \label and citation key.
  - Do not weaken a result to deflect an attack. A correctly hedged claim stays as
    it is; the fix is to put the hedge's justification where the reader needs it.

DELIVERABLE
bep-reliability-engine/docs/examiner_redteam_2026-09-XX.md: the fifteen attacks,
their grades, the quoted existing answers, the edits made, and the unanswered
residue with what each would need. This document is also the owner's defence
preparation, so write the answers out in full even where you changed nothing.

BEFORE YOU FINISH
State plainly which single attack you would least want asked, and why.
```

---

### Work package 5. Give Chapters 6 and 7 back their closes, and rule the open float

**Why fifth.** The repository's own pre-push gate named Chapter 6's synthesis as
the one thing it would undo. This is the largest available reading improvement per
line of ink.

```
You are restoring the closes of the two results chapters of a finished MSc thesis,
and ruling one open figure question. This is a scoped, authorised content change,
not a campaign.

  d:\repositories\msc-thesis            the thesis
  d:\repositories\bep-reliability-engine the evidence base

READ FIRST, COMPLETELY
  1. the msc-thesis project rules, all of it, including the whole page-budget history in
     binding rule 4.
  2. bep-reliability-engine (or msc-thesis/scratch)/PREPUSH_GATE_2026-09-02.md,
     Section 8 "Verdict B", which diagnoses exactly this problem and is the
     authority for the change.
  3. mainmatter/6. Results - Subsurface Piping Assessment.tex, all of it.
  4. mainmatter/7. Results - System Integration and Climate Sensitivity.tex, all
     of it.

THE PROBLEM, AS THE PROJECT'S OWN GATE STATES IT
Chapter 6 is 18 pages and resolves two research questions. Its Synthesis is three
sentences containing no number: "Conditional failure probabilities differ
substantially...", "The 2016 survival constrains the fragility modestly and
locally.", and a hand-off. The gate report calls this "a reading cost, not a rigour
cost", says "I would not have taken Chapter 6's down that far", and names Chapter
7's three substantive paragraphs as the model for the right length. Chapter 7's
own synthesis is also numberless.

WHAT TO DO

1. Rewrite Chapter 6's Synthesis so that a reader who has read the chapter can
   leave it holding the two answers. It must:
     - answer sub-question 1 and sub-question 2 explicitly, in that order;
     - carry the design-level anchors with their stages: Δβ = 0.90 [0.85, 0.97]
       and B = 26.9 [21.6, 35.3] at 46.39 m T.P. at KP 62.0, the bound
       Δβ ≥ 1.27 (B ≥ 148) at KP 57.4's 39.21 m with the resolved 1.27 (42.7) at
       39.50 m, and 1.22 and 1.87 at the two drained sections;
     - state the composition in one clause (head convention, gate, temporal) and
       the equal-convention retained fraction;
     - state the Phase 2 answer with the zero marginal rejection and the 5.67 and
       3.36 per cent, and the peak-only factor;
     - carry the standing conditions by pointer, not by restating the register;
     - introduce NO number that is not already in the chapter.
   Target three to four substantive paragraphs, matching Chapter 7's register.

2. Do the same, more lightly, for Chapter 7's Synthesis: give it the annual
   ratios, the dominance shares, and the duration-channel finding, each with the
   condition it must carry.

3. Rule the open float. bep-reliability-engine/docs/project_log.md records, still
   open, that figures/rq1_beta_curves.png was committed on 2026-08-28 and is
   referenced by no \includegraphics, so it is "either a dropped placement or a
   surplus file". It draws both branches on the reliability-index axis at all four
   sections, with the attainable band shaded. Chapter 6 now LEADS in β and shows
   β-space only as Δβ. Recommend, with your reasoning, whether it belongs in
   Chapter 6 beside the fragility figures; if you recommend placement, write the
   caption and prove the page cost. Do NOT place it if the page cannot be paid for.

CONSTRAINTS THAT NOTHING LIFTS
  - The main body is 99 pages and the ceiling is 100, HARD, and you share the one
    page of margin with two other work packages. Prefer to pay for your additions inside
    Chapters 6 and 7 by compressing restatement, and prove the result with an
    isolated build (copy report.tex, the .cls, references.bib, frontmatter/,
    mainmatter/, appendix/, figures/ to a scratch directory outside the repo and
    run latexmk -xelatex there; never -outdir against the working tree). Read page
    extents off the fresh .toc's \contentsline entries. Report the per-chapter map.
  - Where you compress to pay, cut only passages that restate something already
    established in the same chapter. Nothing that is stated once may be cut. No
    result, figure, number, caveat or interval may leave the document.
  - No em dashes, no "---", ranges "X to Y", no Japanese script.
  - Preserve every \label and every citation key. Do not touch report.tex,
    references.bib or the .cls.
  - Every number you write must already exist in the chapter you write it in.
    Verify each by locating it before you use it.

DELIVERABLE
The edits, plus a short note recording the per-chapter page map before and after,
what you compressed to pay for what you added, and your ruling on the float with
its reasoning.

BEFORE YOU FINISH
Read your new Chapter 6 Synthesis cold, as a reader who has skipped to it. State
plainly whether it answers both sub-questions on its own.
```

---

### Work package 6. State the contribution, and fix the broken reproducibility promise

**Why sixth.** The thesis never claims what it adds, and it points the reader at a
repository that no page names. Both are cheap and both are visible to a grader.

```
You are making two additions to a finished MSc thesis, each small, each closing a
gap that is visible to an examiner.

  d:\repositories\msc-thesis            the thesis
  d:\repositories\bep-reliability-engine the engine

READ FIRST, COMPLETELY
  1. the msc-thesis project rules, all of it, especially binding rules 1, 2, 3 and 4.
  2. mainmatter/1. Introduction.tex and mainmatter/2. Theoretical and Empirical
     Foundations.tex Section 2.3.5 "Synthesis: The Multi-Mechanism Knowledge Gap".
  3. mainmatter/9. Conclusions and Recommendations.tex, in full.
  4. appendix/appendix-j.tex, its opening paragraph and footnote.
  5. frontmatter/title-thesis.tex.

GAP 1: THE THESIS NEVER STATES ITS CONTRIBUTION
The document contains zero occurrences of "contribution", "novel", "first study"
or "to the author's knowledge". Chapter 2 states a gap. Chapter 9 answers four
questions. Nothing asserts what the field gains. The work has at least these
defensible contributions, and you should establish which are actually defensible
before writing any of them:
  - a transient, progression-based BEP fragility framework carried to a complete
    prior deliverable and composed into a multi-mechanism system probability for a
    Japanese river reach, which the source study identified as future work;
  - a shared-sample decomposition of the static-versus-transient difference into
    named ingredients, which shows that most of the design-level difference is a
    head convention and not flood duration, a result the tradition does not
    predict;
  - the measured demonstration that a peak-referenced survival update, of the form
    current probabilistic assessment instruments prescribe, over-rejects by 1.45
    to 3.90 and does so in the non-conservative direction;
  - the general rule that an epistemic bracket cancels in a paired-model
    comparison only if it is common-mode, established input by input rather than
    assumed, which Chapter 9 already calls "the least expected methodological
    result of the work" without ever claiming it as a contribution.

Write a contribution statement of at most eight typeset lines. Place it where it
serves Chapter 1's role as the common thread: either closing Section 1.3
(Objectives) or opening Section 1.6 (Thesis Structure). It must be hedged exactly
as strongly as the evidence allows, must claim nothing the thesis does not
deliver, must not use the word "novel" as a substitute for an argument, and must
name for each contribution the chapter that delivers it. Consider also one or two
sentences in Chapter 9's Overall Conclusion that name what transfers, but only if
the page budget allows both.

GAP 2: APPENDIX J POINTS AT A REPOSITORY NO PAGE NAMES
appendix/appendix-j.tex opens with a footnote stating that "the complete source
code, test suite, configuration files, and machine-readable decision records are
archived in the project repository indicated on the title page". The title page
indicates no repository. There is no github, gitlab, zenodo or 4TU string anywhere
in the document. As it stands the thesis makes a reproducibility promise it does
not keep, and a reader or a repository check will find that.

ASK THE OWNER, before writing anything, what the correct disposition is. The
options are: a named public repository or archive with its URL or DOI; a statement
that the code and data are available from the author on request; or a statement
that the geotechnical dataset is confidential (oyo_1999 and fukuda_2026_internal
are internal documents) while the code is available. Do NOT invent a URL, a DOI or
an availability status. Once told, write a short data-and-code availability
statement, place it where TU Delft practice puts it, and correct the Appendix J
footnote so that it points at something real.

CONSTRAINTS THAT NOTHING LIFTS
  - Main body 99 pages, ceiling 100 and HARD, shared with two other work packages. Prove
    the page count with an isolated build. If Chapter 1 cannot absorb the addition,
    find the offsetting restatement inside Chapter 1 (its own campaign log says
    restatement is where this document accumulates ink) or report that the page
    cannot be paid for.
  - No em dashes, no "---", ranges "X to Y", no Japanese script.
  - No software or computer-science content in Chapters 1 to 9. A contribution
    statement describes what was established, not what was built in code.
  - Preserve every \label and every citation key. You may edit
    frontmatter/title-thesis.tex for gap 2 only, and only as the owner directs.
  - Invent nothing. If a contribution cannot be traced to a chapter, drop it.

BEFORE YOU FINISH
State plainly, in one sentence each, the contributions you claimed and the chapter
that delivers each, and confirm that the reproducibility promise now resolves.
```

---

### Work package 7. The first ninety seconds: Summary, and the entry to each chapter

**Why seventh.** Four committee members read the Summary before anything else, and
it is currently the densest prose in the document.

```
You are making a targeted readability pass on the parts of a finished MSc thesis
that a reader meets first. This is NOT a general prose pass, which the repository
explicitly forbids.

  d:\repositories\msc-thesis

READ FIRST, COMPLETELY
  1. the msc-thesis project rules, all of it. Note in particular: "The main body and the
     Summary have been through a line-level prose pass... do not 'improve' them
     again on your own initiative. If you think a passage still reads badly, say
     so and leave it." THIS WORK PACKAGE IS THE EXCEPTION THAT INSTRUCTION ANTICIPATES,
     and it is narrow. Outside the scope below, that instruction still binds.
  2. frontmatter/summary.tex, in full.
  3. The opening paragraph of each of the nine main-body chapters.

THE MEASURED STARTING POINT
The Summary runs to exactly two pages, eight paragraphs, about 58 sentences with a
mean of 34 words, four of them over 55 words, carrying 70 distinct numbers. Every
one of those numbers is verified present in the main body, so the content is
sound. The problem is density: a reader meeting the work for the first time has to
hold four brackets and two metrics in mind by the third sentence of paragraph
three.

YOUR SCOPE, AND NOTHING BEYOND IT
  1. The Summary. At UNCHANGED length (it must stay exactly two pages) and with
     the SAME set of numbers, improve its readability by:
       - splitting the four sentences over 55 words, and any sentence carrying
         more than three numbers, into sentences that each do one job;
       - making the first sentence of each of the eight paragraphs a topic
         sentence that says what the paragraph establishes;
       - ensuring the first paragraph reaches the research problem within its
         first three sentences.
     You may not remove a number, a caveat, a bracket or a conditional. You may
     not add one. You may reorder within a paragraph; do not reorder paragraphs.
  2. The nine chapter openings. Each should tell a reader, in its first two
     sentences, what the chapter establishes and which question it serves. Most
     already do. Edit only those that do not, and say which you left alone.

CONSTRAINTS THAT NOTHING LIFTS
  - The Summary must remain exactly two pages and the main body exactly 99, with
    References on 100. Prove both with an isolated build; a Summary that runs to a
    third page is a failure of this work package even if it reads better.
  - No em dashes, no "---". Ranges "X to Y". No Japanese script.
  - Preserve every \label and every citation key. The Summary carries no \ref;
    keep it that way.
  - Match the existing register: formal academic English, American spelling.
  - Do not simplify a hedge into a claim. Every conditional in the Summary is
    load-bearing and several were fought for; if splitting a sentence would orphan
    a caveat from its number, do not split it.

DELIVERABLE
The edits, plus a before-and-after table of per-paragraph sentence count, mean
sentence length and longest sentence, and the page proof.

BEFORE YOU FINISH
Read the Summary aloud, cold. State plainly whether a supervisor who reads only
this page and a half comes away knowing what was found, at what four sections,
under what conditions, and why it matters.
```

---

### Work package 8. One consistency sweep: orthography, terminology, notation, pointers

**Why eighth.** Individually trivial, collectively the difference between a
careful document and a meticulous one. Run it after all content edits.

```
You are running a single mechanical consistency sweep over a finished MSc thesis.
Every finding below was measured on the current source; confirm each before acting,
because earlier work packages in this sequence may have changed the counts.

  d:\repositories\msc-thesis
  d:\repositories\bep-reliability-engine   (for figure-facing strings only)

READ FIRST, COMPLETELY
  the msc-thesis project rules, all of it, especially "Settled notation decisions", which
  lists three questions that are CLOSED and two apparent defects that must NOT be
  changed (the one bare "+4K" inside a \label, and the MSL nomenclature row).

WHAT TO SWEEP

1. ORTHOGRAPHY. The document is American throughout except:
     - "artifact" at 8 sites and "artefact" at 8 sites, both in typeset prose,
       across mainmatter/ and appendix/. Pick one, apply it everywhere, and say
       which you picked.
     - "favour" in typeset prose at mainmatter/8. Discussion.tex (Section 8.8) and
       appendix/appendix-f.tex.
     - "modelled"/"modelling" survive only inside \label and \ref arguments, where
       they are invisible and must NOT be touched. Verify before editing.
     - "Behaviour" survives only inside a \label. Do not touch it.
   Sweep for any variant these four patterns miss.

2. TERMINOLOGY. Two synonym pairs denote the same two sections at near-equal
   frequency: "unremediated" (11) and "unreinforced" (11) for KP 62.0, and
   "berm-widened" (5) and "berm-only" (4) for KP 57.4. A reader has to infer the
   identity. Either normalise onto one term per section, or, if both are load-
   bearing in different registers, state the equivalence once where the sections
   are introduced in Chapter 3 and leave the usage alone. Recommend before acting;
   the figures also carry "berm-only" and "unreinforced" as panel labels, so a
   rename in prose alone would create a new mismatch.

3. NOTATION. Confirm the three closed decisions still hold: \mathrm{bl} upright
   with none italic, k_\mathrm{aq} everywhere, and upright descriptive subscripts
   on I_er, h_obs, D_{r,m} and C_{u,m}. Report any drift; do not re-open the
   decisions.

4. NOMENCLATURE. frontmatter/nomenclature.tex defines N as "Monte Carlo sample
   size per cross-section (10^5)", but the two design-level anchors are simulated
   at 10^6 and the thesis says so repeatedly. Correct the parenthetical. Then check
   every symbol used in the main body against the table in both directions:
   symbols used but not listed, and symbols listed but no longer used.

5. CROSS-REFERENCE TRUTH. There are 28 stacked-label groups, created mostly by the
   shortening campaign's heading consolidation. Each means several \ref targets
   resolve to one number, and a pointer may now land on a section that does not
   contain what the citing sentence promised. The pre-push gate found exactly this
   defect once and its own follow-up found the gate's section number wrong, so do
   not trust either. For EVERY \ref in the document: resolve it against
   report.aux, open the target, and confirm the target actually contains what the
   citing sentence says it contains. Two known cases to start from:
     - "sec: Pre-Calculated Surface Failure Fragility Curves from Uemura (2025)"
       is stacked onto Section 3.7 "The d4PDF Climate Ensemble", which is not what
       the label names. Chapter 7 line 25 points at it; the target's last paragraph
       does carry the claim, so the pointer resolves correctly and only the label
       NAME is misleading. Confirm, then decide whether to leave it (it is inside
       a \label and renaming it breaks the \ref) or to comment it.
     - Table 3.1 carries three labels, of which "tab:oyo_inventory" and
       "tab:seepage_length" are referenced nowhere. Report dead labels; remove one
       only after proving it is unreferenced with a NEWLINE-TOLERANT matcher (a
       naive one produces 32 false positives from line-wrapped \ref arguments).

CONSTRAINTS THAT NOTHING LIFTS
  - Main body 99 pages, References on 100, ceiling 100 and hard. A pure
    orthography sweep should move nothing; prove it with an isolated build anyway,
    because a word-length change can reflow a paragraph.
  - Preserve every \label that is referenced. Never rename a label to fix a
    spelling; the \ref would break.
  - No em dashes, no "---", ranges "X to Y", no Japanese script.
  - Do not "tidy" whitespace, line wrapping or formatting. Diffs must stay
    readable in Overleaf history.

DELIVERABLE
A short report listing each category, what you found, what you changed, and what
you deliberately left alone with the reason.
```

---

### Work package 9. The final pre-submission gate

**Why last.** Nothing in this list is finished until a build proves it.

```
You are the final gate before an MSc thesis is handed to its committee. You did
not write any of the preceding changes. Your job is to decide, on measurement,
whether the document is safe to submit, and to say what is still wrong.

  d:\repositories\msc-thesis
  d:\repositories\bep-reliability-engine

READ FIRST, COMPLETELY
  1. the msc-thesis project rules
  2. msc-thesis/scratch/PREPUSH_GATE_2026-09-02.md and
     PREPUSH_GATE_2026-09-02_P22.md. These are the method you are repeating and
     they contain traps you must not fall into. In particular: a comment-stripper
     that treats LaTeX-escaped \% as a comment start will silently delete table
     rows and produce false "lost token" findings; pdftotext drops the semicolon
     glyph in this document's body font, so extracted text shows correct sentences
     as run-ons; and a naive \ref matcher reports 32 false positives from
     line-wrapped arguments.
  3. git log from the last pushed commit to HEAD, in full, WITH PATCH. Read every
     changed line.

WHAT TO DO

Part 1, mechanical, against the baseline of the last pushed commit:
  - Build TWO isolated trees by git archive, one at the baseline and one at HEAD,
    outside the working tree, and run xelatex + biber + xelatex + xelatex in each.
    Never latexmk -outdir against the working tree.
  - Report and compare: undefined references (expect 0), undefined citations
    (expect 0), citation keys (expect 106), labels with duplicates and dangling
    refs, main-body page count and the per-chapter map, appendix extents, total
    pages, overfull hboxes with the largest, underfull vboxes, float-only pages.
  - Numeric-token diff in BOTH directions between the two trees. Every token
    gained or lost must be attributable to a specific authorised change. Any
    unattributable token is a blocking finding.
  - Run both style scans from the msc-thesis project rules verbatim, in PowerShell, from
    the repo root: the em dash and "---" scan, and the CJK scan. Both must be
    CLEAN.
  - git status --porcelain --untracked-files=all must be empty. No .md, no
    architecture and decision records, no report.tex, no references.bib, no .cls, no build artefact may
    appear in the diff unless a change explicitly authorised it.

Part 2, read the changed passages AS RENDERED PAGES, not as source. For each: does
it read, does its pointer resolve, did it cost the document anything, did any
float move or become orphaned, did any caption drift from its figure.

Part 3, the load-bearing items. Measure on whitespace-normalised full text so that
wrapped phrases are caught. Confirm that every scope clause, interval, bound and
caveat that stood at the baseline still stands: "as-if-undrained", "114 evaluation
segments", "explicit lower bounds", the [0.85, 0.97] and [21.6, 35.3] intervals,
the 148 bound, 63 to 83 per cent and its complement 17 to 37, 75 to 97 per cent,
6 to 9 times, "hazard-sampling", "fragility curves held fixed", "not the total
uncertainty", "does not cancel", 11.8 per cent, "the third decimal is not an
estimated digit", "knife edge". A caveat that lost its number is a blocking
finding.

Part 4, the figures. Confirm every \includegraphics resolves, that the headline
confidence interval is identical in figure, equation, Table 9.1, the Chapter 8
restatement and the Summary, and that no figure carries a British spelling, an
italic descriptive subscript, a "--" dash or an "x" for "times".

Part 5, submission readiness. Check the things only a final gate checks: the title
page has a defence date rather than "...", the preface is written and carries no
instruction comment block, every committee member's name and affiliation is
correct and consistently spelled, the cover credit is right, the List of Figures
and List of Tables each fit their intended extent, and the References list renders
with no broken entry.

DELIVERABLE
A report in the form of PREPUSH_GATE_2026-09-02_P22.md: a headline verdict on
whether the document is safe to submit, a second verdict on whether the changes
since the baseline improved it, then the measurements, then a numbered findings
list with each finding classed as BLOCKING, SHOULD FIX, or COSMETIC.

BEFORE YOU FINISH
State plainly, in one paragraph, what you would still change if you had one more
day, and whether any of it blocks submission.
```

---

## 3. What I deliberately did not propose

- **No new computation.** No sweep, no replay, no campaign, no additional
  sensitivity. Work package 1 re-renders figures from persisted results, which is not
  analysis; every other work package reads.
- **No lengthening.** Work packages 4, 5 and 6 add prose, share the single page of
  margin, and each is required to prove the page count and to pay for its
  additions inside its own chapter.
- **No general prose pass.** The msc-thesis project rules forbid it and the line-level
  pass has already happened. Work package 7 is a narrow, length-fixed exception aimed at
  the Summary.
- **No new citations, and no reference-list expansion.** Three citation audits have
  closed. `TAW 1999` is still absent from `docs/references/` and uncited; adding it
  would need the primary in hand, which is a data problem and not a writing one.
- **No restructuring.** The nine chapters, the eleven appendices and the
  four-group appendix architecture were measured and are sound.
