# Assumptions, conclusion robustness and Green Light revision close-out

Date: 2026-09-27. Green Light item 6. Documentation synthesis and arithmetic
on existing evidence; no physics, prior, configuration or production output
changes. Evidence: `assumptions-overview-study.json` beside this note.

## Investigation and verdict

Engine baseline `4b67286`, thesis baseline `2579e92`. Read the five completed
study notes, their September 24 to 27 project-log entries, and both integration
histories before editing. Item 4's ADR-0054 cascade supersedes the matrix
numbers in the original item 3 study. Items 1, 2 and 5 are companion studies,
not production adoption decisions. Their scope must remain visible.

The requested information largely existed, but a reader had to assemble it
from the scope, piping conditions, system conditions, limitations and answers
registers. The limitations register omitted several choices and usually did
not say whether an answer survived. Adding a sixth independent register would
not solve that problem.

The Discussion now uses the existing `tab: limitations register` label for
one 28-row assumption-to-conclusion overview, grouped into soil/geometry,
piping formulation, hydraulics/observations, loading/climate, and system/use.
It explicitly maps Q1 to Q4 and the main question, distinguishes measured
effects from knowledge gaps, and states the scope of every survival verdict.
The former detailed qualifications remain in Appendix I with a pointer from
the overview. All original labels and citations are retained. Chapters 1, 6,
7 and 9 point to this common overview. No page ceiling was applied.

No tornado plot is added: an annual system probability, conditional index
gap, resistance multiplier, below-floor bound and missing physical process
cannot honestly share one ranked axis. Existing common-metric figures remain.

## Evidence discipline and inexpensive gaps

The JSON records source paths and hashes. Latest regenerated evidence governs
over old study prose, as prescribed by the ADR-0054 addenda. The overview
does not interpret an unmeasured effect as zero or call a tested alternative
the entire plausible range. Cancellation is metric-specific. An unfiltered
drain outlet is not bounded by a gate-relief proxy.

Three gaps require arithmetic, not new evaluations, and have no result-selection
step or empirical prediction:

1. At the measured approximate relative-density mean 0.78, the deterministic
   Sellmeijer multiplier against adopted 0.725 is `(0.78/0.725)^0.35`, about
   1.026. This is only a resistance comparison, not a propagated probability
   bound; the underlying site mean is itself censored. KAS remains below
   0.8 percent effect on resistance over its tested range. No new citation.
2. The current composition record gives the KP 62.0 warming fixed-marginal
   annual union bounds as **0.6816 to 1.3100** of the independent composition,
   replacing the thesis's stale lower endpoint 0.66. These are bounds, not
   estimates or a physical-coupling calculation.
3. Item 1 already stores annual system probabilities under every uniformity
   arm in both climates. Their quotients close its unreported Q4 column:
   matrix/prior, 250 m correlation length, primary surface set, fixed canonical
   waveform and adopted conductivity. Baseline climate ratios are
   15.25/5.58/13.29/13.43 (KP 57.4/58.8/60.0/62.0); tested-maximum C_u ratios
   16.88/5.78/14.65/14.76; sand-fraction ratios 22.71/6.11/18.31/18.19;
   extrapolated matrix-C_u ratios 59.56/8.05/58.75/31.65. They are prior-side
   scenario arithmetic, not the production posterior ratios or confidence
   intervals. Warming still increases probability; the magnitude does not
   cancel. The extrapolated arms do not establish a calibrated field range.

The Appendix I model-factor paragraph formerly quoted deep-tail maxima below
the thesis's count floor and called two matrix sections informative. From the
current `adr0045-mp-companion.json`, require at least 30 failures and survivors
in both arms of each branch and an attainable stage. Sectionwise static maxima
are 2.94/2.54/2.51/2.23 and transient maxima 1.68/1.61/1.93/1.76. These occur
at different stages and are not a common-stage ranking. The paragraph now
states this restriction rather than quoting the below-floor maxima.

## Cross-document repairs

* Appendix I retained the pre-rebase design B range 2.75 to at least 148 and
  index range 0.9 to 1.9. They now read 3.09 to at least 37 and 0.85 to 1.22
  where resolved.
* The former Discussion conductivity row reversed the historical/warming
  low-arm counts; it now agrees with Chapters 7 and 9: all four historical,
  three warming, with the high arm returning the fourth warming cell to piping.
* The survival-likelihood row names the drained sections instead of two
  informative strata. The applicability table says negligible updating at
  three sections rather than vacuous updating at two.
* The shorter-shape design-ratio multiplier at KP 60.0 is about 2.3, not 2.1
  (14.5/6.34). The primary probabilities remain unchanged.
* Appendix K's indistinguishable climate-ratio pair is KP 60.0/KP 62.0, not
  the two outer sections.
* Physical coupling and fixed-marginal dependence are explicitly distinguished
  in the supporting register, matching the existing Discussion argument.
* Summary and Chapter 9 now carry item 5's limited waveform/rating findings:
  the waveform screen does not justify a production climate-ratio correction.
  Item 1's explicit decision to leave uniformity out of the Summary is respected.
* Availability statements name v1.2.0 and distinguish the published GitHub
  release from the reserved, unpublished 4TU deposit. No new bibliography key.

## Release and remaining owner action

Version **1.2.0** is required because item 4 changed production inputs and
numbers, and the revision added study code. Follow v1.1.0's annotated-tag,
version-metadata and changelog practice. The Bayesian package version stays
0.1.0 because it is a persisted-posterior provenance stamp. Only `develop`
and the topic branch receive commits; `origin/main` is untouched.

The DOI is consistent across README, CITATION.cff, package metadata and thesis:
`10.4121/8ffa1f3e-942e-4852-b02a-a259b9d6d00d`. Both the DOI resolver and public
DataCite lookup returned 404 on 2026-09-27, consistent with the owner's reserved
draft. This does not verify the private draft's contents or ownership. No 4TU
authenticated session is available. The release archive and metadata are
prepared for the author to upload to the existing draft; no submission or
publication is performed. A public thesis identifier is not yet recorded and
must be added after thesis publication rather than invented.

## Validation and release readiness (2026-09-28)

* `ruff check .`: pass. `black --check .`: 183 Python files unchanged.
* Full `pytest -q` with the available raw and production fixtures copied into
  the isolated worktree: **1124 passed, zero skipped**, nine warnings. Eight
  are the expected sparse-grid bootstrap warnings; one reports a restarted
  joblib worker during the overnight interruption. No test failed. The logged
  8 h 26 min wall time spans that interruption and is not a runtime benchmark.
* Faithful isolated PowerShell `latexmk -xelatex` build converged. All 418 labels
  are unique and preserved, all references and 109 used bibliography keys
  resolve, and the em-dash/Japanese-script checks pass. No TeX error or overfull
  box. Template/package/font warnings remain, recorded verbatim in the JSON.
* Main-body chapter page counts, Chapters 1 to 9: **6, 10, 13, 13, 11, 20, 14,
  14, 8**; total **109**, References start on 110. No length-driven cut.
  The Discussion overview occupies printed pages 94 to 96. The rendered
  overview and the new Appendix I climate-ratio table were inspected.
* All **59 engine-produced images** included in the thesis match byte for byte.
  Successful redraw commands cover all 59 and reproduce the committed bytes.
  Four external images are the study map and three institutional logos.
  No stale image was found; equality alone was not used as a freshness claim.
* Build source identity, figure digests, source digests and numerical derivations
  are in the companion JSON. The built PDF and working logs are outside both
  repositories at `D:/repositories/g6-closeout/`; no build product is committed.

The release tag v1.2.0 identifies this tested source state. Its GitHub release
notes summarize all six items. The prepared deposit instructions are in
`docs/release-v1.2.0-deposit.md`; the archive manifest is generated from the tag
so its release commit and checksum cannot become self-referential. The final
remote SHA checks and upload-ready files are retained in the external handoff
folder after publication. No source, prior or default was changed in item 6.
