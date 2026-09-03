# The three examiner-redteam residues, closed

Date: 2026-09-04. Companion evidence: `examiner-residues-closed-2026-09-04.json`.
Parent record: `docs/examiner_redteam_2026-09-03.md`, Section 3.

**What this is.** The red-team pass of 2026-09-03 answered fourteen of its fifteen
attacks on the page and left three residues that it judged unclosable from existing
evidence. The owner asked for those three to be pursued. All three close. **None needed a
new sweep, a new module, a config field or an ADR**: two were settled by read-only
recomputation against committed artifacts and one by a deduction the repository had
already written down but the thesis had not.

No engine module, config, persisted sweep, geotechnical CSV, figure or measured
production value was touched. Three thesis sentences changed (Ch. 4, Ch. 6, Ch. 8) and
the main body stayed at 99 pages.

---

## R1. The direction of the peak-only over-rejection

**The residue.** Chapter 6 states: "The peak-only reading over-rejects under either
loading, and the direction of the error is therefore a property of the method." The
"therefore" generalises from two conditioning events to the method. Both approved
canonical members hold the stage above the toe longer than the real 2016 record at the
same peak, which is what produces the over-rejection, so the sign should reverse for a
conditioning wave shorter than the survival event. That case appeared untested, and the
red team recommended a third member drawn from the short tail of the ensemble's t50
distribution.

**Verdict: CLOSED, and the residue's own premise was false.** No third member is needed,
because the alternate approved member already *is* the short-tail member, and at the two
informative sections it is already shorter above the toe than the survival event.

### The ensemble distribution, recomputed

ADR-0023's shape diagnostic was reproduced from source over all 3,000 HPB members at the
KP 58.8 rating, under its own stated definitions (hours at or above a normalized-stage
fraction; peaks by `scipy.signal.find_peaks(shape, height=0.3, prominence=0.2)`). Every
figure matches:

| Quantity | ADR-0023 | Recomputed |
|---|---|---|
| t50 median | 40 h | 40 h |
| t50 interquartile range | [32, 54] h | [32, 54] h |
| peaks, median / mean | 1 / 1.10 | 1 / 1.10 |
| compound fraction (>= 2 peaks) | 9.6 per cent | 9.6 per cent |

t50 spans 17 h to 183 h across the ensemble. The two approved members sit at:

| Member | Role | t50 | t50 quantile | Peaks |
|---|---|---|---|---|
| `HPB_m064_1987` | production | 55 h | **0.756** | 2 |
| `HPB_m067_1978` | alternate | 21 h | **0.005** | 1 |

**The alternate is in the lowest half per cent of the ensemble's duration distribution**,
against an ensemble minimum of 17 h. There is almost nothing shorter to test: a
hypothetical third member could buy at most four hours of t50 below the one already
approved.

This also verifies, independently and exactly, the two quantities the 2026-09-04 thesis
edit put into Chapter 4: the production member is in the upper duration quartile
(quantile 0.756) and among the roughly one member in ten that carries a second peak
(9.6 per cent).

### The decisive measurement

The peak-only factor is `P_f,trans(canonical curve at the observed 2016 peak)` divided by
the 2016 replay rejection. It exceeds one iff the canonical event, rescaled to the
observed peak, drives more failures than the real record did. The operative comparison is
therefore between the *conditioning* wave and the *survival* wave at one common peak, and
it must be made on one counting rule.

Both sides were counted as `(samples with h > z_toe) * dt`, on the native hourly grid, the
real record built through the committed ADR-0035 ingestion and the members through the
verbatim `conditioning_record_for_level` path. **The reconstruction reproduces the
thesis's own 9 / 24 / 31 / 6 h for the real record exactly**, which is what makes the
ratios commensurable.

| Section | Toe | Observed peak | Real 2016 | Production member | Alternate member |
|---|---|---|---|---|---|
| KP 57.4 | 38.3 m | 39.66 m | 9 h | 24 h (2.67x) | 10 h (1.11x) |
| **KP 58.8** | 38.5 m | 40.75 m | **24 h** | 60 h (2.50x) | **23 h (0.96x)** |
| **KP 60.0** | 40.0 m | 42.30 m | **31 h** | 62 h (2.00x) | **26 h (0.84x)** |
| KP 62.0 | 44.9 m | 45.73 m | 6 h | 15 h (2.50x) | 8 h (1.33x)  |

Against the committed peak-shortcut slice
(`docs/decisions/canonical-shape-sensitivity.json`, stage `peak_shortcut`):

| Section | Replay rejection | Factor, production | Factor, alternate |
|---|---|---|---|
| KP 58.8 matrix | 5.673 per cent | 2.749 | **1.448** |
| KP 60.0 matrix | 3.363 per cent | 3.899 | **1.568** |

**The conclusion.** At both informative sections the alternate conditioning wave stands
above the toe for *less* time than the survival event did at the same peak, 0.96 and 0.84
of it, and the peak-only reading still over-rejects, by 1.45 and 1.57. The two approved
members therefore **bracket** the survived loading's own above-toe duration, 2.50x and
2.00x above it and 0.96x and 0.84x below it, and the over-rejection holds on all four
arms. The direction is not an artefact of a conditioning wave longer than the event it is
read against, and the thesis claim stands as written with the bracketing now printed
beside it.

**Why it over-rejects even when shorter, which is the mechanism worth keeping.**
Above-toe duration is not the quantity the barrier charges in. A pipe advances only where
the erosion head exceeds the equilibrium head, that is near the crest. The real 2016
record is a multi-peak event whose 24 and 31 above-toe hours are spread over sub-peaks
most of which sit far below its own crest, while a rescaled canonical member concentrates
its above-toe time around a single crest. The alternate's t90 is 5 h against the
production member's 10 h, yet both beat the real record where it counts. This is the same
crest-concentration argument the engine's own shape stage records, and it is why the sign
survives the duration reversal.

**Thesis edit.** Chapter 6, `subsec: What the Replay Adds`, after "a factor of 1.45 to
3.90":

> That member is not merely the shorter of the two: it lies in the lowest half per cent of
> the ensemble's own duration distribution, and rescaled to the observed peak it stands
> above the toe for 0.96 and 0.84 of the time the observed record itself did at the two
> informative sections, against 2.50 and 2.00 for the production member. The two therefore
> bracket the survived loading, and the peak-only reading over-rejects on both, so the
> direction of the error is a property of the method and not of a conditioning wave longer
> than the event it is read against.

---

## R2. The power of the sixty-year base-rate check

**The residue.** Chapter 8 offers "an annual piping probability of 1.07e-2 ... 0.65
expected failures and a probability of 0.52 that none is observed" as being "stronger than
a silent record". It is, and the verb throughout is the correct one ("consistent with"),
but the *power* of the check was not stated, and a model an order of magnitude lower or a
factor of three higher would also pass it.

**Verdict: CLOSED by exact arithmetic on numbers already in the document**, and the
answer is favourable: the test has power on precisely the side the objection runs on.

With zero events observed in 60 years, the one-sided 95 per cent upper confidence bound on
a Poisson rate is `-ln(0.05)/60 = 4.993e-2` per year.

| Arm | Annual probability | Expected in 60 y | P(none observed) | Headroom to the 95 per cent bound |
|---|---|---|---|---|
| As-if-undrained series | 1.07216e-2 | 0.643 | 0.526 | **4.7x** |
| Berm-credited series | 6.3699e-3 | 0.382 | 0.682 | **7.8x** |

So the record excludes any annual probability above about 5.0e-2 per year and excludes
nothing at all below the reported value. The asymmetry is the point. The objection the
check answers is "your probabilities are implausibly high", and that is the only direction
in which sixty years of zero observations can discriminate at all. The check therefore
does the work asked of it, with a stated margin of a factor of 4.7, and it makes no claim
against a lower model, which nobody is advancing.

**Thesis edit.** Chapter 8, `subsec: The Erosion-Limited Consensus`, after "crediting the
measured berm gives 0.38 and 0.68":

> The check has power on one side only, and it is the side the objection runs on: zero
> observations in sixty years exclude an annual probability above 5.0e-2 at 95 per cent
> confidence, a factor of 4.7 above the reported value, and exclude nothing below it.

---

## R3. The decoupled heave gradient

**The residue.** Chapter 4 justified retaining the full `I_er` gate structure partly
because "it becomes load-bearing again the moment a sensitivity analysis decouples the
critical heave gradient from the Terzaghi value". No such sensitivity is reported anywhere
in the main body or the appendices, so the justification read as a promise about work not
done.

**Verdict: CLOSED as a deduction, which is what it always was.** The claim does not need a
sensitivity run, and running one would not strengthen it, because the conclusion follows
from independence rather than from a magnitude.

Under the adopted substitution `i_c = gamma'_bl/gamma_w` (ADR-0008), the heave threshold is
a deterministic function of *the same sampled* `gamma'_bl` that sets the uplift threshold.
That is what makes `Z_heave = Z_uplift / D_bl` identically, so the two limit states change
sign at the same instant and the uplift latch is provably redundant within an event, as
Chapter 4 already states.

Any decoupling replaces that deterministic tie with a separate draw. Two independently
drawn thresholds cannot change sign at the same instant except on a set of measure zero,
so under *any* decoupling the two separate, and the latch binds in every realization where
the drawn gradient falls below `gamma'_bl/gamma_w`. That is the whole content of
"load-bearing", and it is settled by the independence, not by a measured effect size.

The repository already held both halves of this. ADR-0008
(`0008-terzaghi-heave-gradient-collapse.md`) records the alternative it displaced, Pol's
independent `i_c,h ~ Lognormal(mu = 0.7, sigma = 0.1)` after Schweckendiek et al. 2014 and
Pol SIE 2024 Table 2, and its decision 2 makes the same forward-looking claim in the same
words. Its section on consequences records the direction: Pol's gradient sits below the
uplift gradient, opening a sustain window during recession that the collapse removes, "a
small, documented loss of conservatism". **Chapter 4 already carries that direction**, and
Appendix B already carries the spread comparison, the alternative's coefficient of
variation of 0.143 against the 0.056 the substitution inherits from `gamma'_bl`. What was
missing was only the reason the latch returns, which is one clause.

**Thesis edit.** Chapter 4, `subsec: The Erosion Indicator and Composite STPH Failure`:

> ...and because any decoupling of the critical heave gradient restores it: a separately
> drawn gradient cannot change sign with the uplift threshold, so the latch binds wherever
> the two draws separate (Appendix~\ref{app sec: Deterministic Inputs}).

**What was deliberately not done.** No `i_c,h` knob was added. It would be an eighth
random variable, breaking the seven-dimensional vector of ADR-0001, for a component whose
consequence is already bounded in direction and known to be small on flashy hydrographs;
ADR-0008 weighed and refused exactly that trade. The residue was a wording defect, not a
missing measurement, and it is fixed as one.

---

## Reproduction

Two read-only scripts, run from the repository root against the committed data drop and
the committed artifacts. Neither writes into the repository.

* the ensemble scan and the member quantiles: `scipy.signal.find_peaks(shape, height=0.3,
  prominence=0.2)` over `load_hydrograph_ensemble` for the HPB Tokachi KP 056.20 to 061.80
  band at the KP 58.8 rating;
* the above-toe comparison: `observed_event_record` from
  `bayesian_reliability_updating.events` against `conditioning_record_for_level` for both
  members, one counting rule, at all four sections.

Both are recorded in `examiner-residues-closed-2026-09-04.json` together with the peak-only
factors read back from `canonical-shape-sensitivity.json`. The R2 arithmetic is a
two-line Poisson evaluation and is recorded in the same file.
