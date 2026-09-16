# Study note: what the 2016 survival constrains, and what it cannot establish

**Date:** 2026-09-16
**Driver:** `scripts/survival_information_study.py` (`--part
conditioning|nesting|future|excursions|all`)
**Evidence:** `docs/decisions/survival-information-and-nesting-study.json`
**Gate:** `tests/test_survival_information.py` (12 checks, 1.8 s)
**Companion study, not an ADR.** No `Config` field, no default, no prior, no
physics kernel, no persisted sweep, no posterior and no annual number changes.
The one engine addition, `analysis.seepage_length_update`, records a property
of already-computed values; it changes nothing a baseline run computes, which
is the `bep-change-control` section 1 test (the HKV item-2 precedent).

**What prompted it.** An external examiner review raised two inference claims.
Both were re-derived from the model definition here *before* the review's own
probe or its numbers were consulted, and then measured through the engine's own
kernels and committed arrays. One is confirmed, one is half right and half
wrong, and the measurement changes the remedy in both cases.

---

## 1. The seepage length is conditioned by the survival, and the impossibility claim is false

### 1.1 The derivation, which is three lines

The prior is independent by construction: `L` is drawn under its own
`SeedSequence` salt and is not a `theta` column (ADR-0001,
`sampling.sample_seepage_length`). With survival evidence `S`,

    pi(L | S) = pi(L) * P(S | L) / P(S),   P(S | L) = integral 1_S(theta, L) pi(theta) d theta.

So `pi(L|S) = pi(L)` **if and only if** `P(S | L)` is constant in `L`. It is
not: `L` sets the critical head `H_c = L F_r F_s F_g`, the rate denominator in
Eq. (5), and the breach criterion `Z_transient = L - l_e` itself. Independence
in the prior is simply not preserved by conditioning, and no property of the
sampler can make it so. Rejection in `filtering.apply_survival_filter` is
row-wise on the joint draw, so the engine has always retained the conditioned
`L` correctly; what was missing was any diagnostic that looked at it.

**The discriminating object is the acceptance profile, not the mean shift.** A
conditioned marginal can have an unmoved mean (reject both tails symmetrically)
and still have lost a fifth of its variance. `seepage_length_update` therefore
reports `P(S | L)` over deciles of the prior draw as its object of record.

### 1.2 What the 2016 survival actually did

Measured on the eight production posteriors at the corrected KP 56.73 gauge,
N = 100,000 per stratum. `acceptance spread` is the range of `P(S | L)` across
the ten prior deciles.

| stratum | rejection % | mean L shift | CoV shift | Var(L) ratio | acceptance spread | Spearman(L, k_aq) prior -> post |
|---|---:|---:|---:|---:|---:|---|
| KP 57.4 matrix | 0.063 | +0.022 % | -0.098 % | 0.99849 | 0.0057 | +0.0018 -> +0.0033 |
| KP 58.8 matrix | 5.512 | **+1.339 %** | **-3.566 %** | **0.95502** | **0.2772** | +0.0018 -> **+0.0747** |
| KP 60.0 matrix | 3.244 | **+0.519 %** | **-1.617 %** | **0.97800** | **0.1369** | +0.0018 -> **+0.0430** |
| KP 60.0 bulk | 0.023 | +0.006 % | -0.030 % | 0.99952 | 0.0019 | +0.0018 -> +0.0024 |
| KP 57.4 / 58.8 / 62.0 bulk, KP 62.0 matrix | 0.000 | 0.000 % | 0.000 % | 1.00000 | 0.0000 | unmoved |

The profile at KP 58.8 runs **0.7224** in the lowest `L` decile to **0.9996** in
the highest, monotonically. `P(S|L)` is therefore steeply non-constant and the
conditioned marginal is demonstrably not the prior. The mean shift is small, but
smallness is a property of this event, not a theorem about survival evidence.

**The largest dependence the update induces is not inside `theta`.**
`correlation_shift` reports a maximum induced rank correlation of **-0.051**
(`k_aq` x `C_e`, the quantity the thesis quotes as "about -0.05", correctly).
The induced `Spearman(L, k_aq)` is **+0.0747**, half again as large, and no
diagnostic computed it before this note, because `prior_posterior_summary` and
`correlation_shift` both iterate `param_names`. That blind spot is the same one
that let "the filter operates on the seven-parameter soil vector" be read as
"the filter does not condition `L`".

### 1.3 The counterexample that settles the universal claim

`docs/decisions/seepage-length-L-study.md` section 3 stated that the `ST_L`
share is "essentially irreducible by survival evidence, a floor that no amount
of additional survival events can lower", and the thesis carried it as "no
number of additional survival observations would lower it". One counterexample
suffices, and it costs no simulation.

Phase 1's persisted `failure_matrix_trans` is the transient failure indicator of
every prior row at every conditioning level, computed under the shared-sample
contract with that row's **own paired `L`**. Column `k` is therefore exactly the
survival set of a hypothetical event peaking at grid level `h_k`, and the ladder
is verified perfectly nested (`0` non-monotone survival pairs at all eight
strata), so a higher column is a strictly stronger observation. At KP 58.8
matrix:

| survived level [m T.P.] | P(S) | mean L shift | CoV | Var(L) ratio |
|---:|---:|---:|---:|---:|
| 40.00 | 0.9952 | +0.152 % | 0.19882 | 0.9913 |
| 40.50 | 0.9253 | +1.809 % | 0.19053 | 0.9407 |
| **40.75** (the 2016 peak, canonical shape) | 0.8440 | **+3.418 %** | 0.18522 | **0.9174** |
| **41.25** | 0.6220 | **+7.600 %** | **0.17663** | **0.9031** |
| 41.75 | 0.4050 | +12.130 % | 0.17157 | 0.9254 |

Two readings, and the second is the more careful one:

* a survival **0.50 m above** the observed 2016 peak would move the retained
  mean **5.7 times** as far as 2016 did and take more than twice as much
  variance out of `L`. The universal claim is false, at every stratum.
* at the **same** peak as 2016 but under the canonical conditioning shape, the
  shift is already +3.418 % against 2016's +1.339 %. So the weakness of the
  2016 update is a property of that record's *duration*, not only of its
  height, which is the same shape effect the peak-only comparison measures
  from the other side.

### 1.4 What survives, and must be preserved

**The thesis's substantive point is correct and is strengthened, not weakened,
by measuring it.** The variance ratio is U-shaped along the ladder: it bottoms
out and then rises back through 1 as the survivor set becomes the extreme upper
tail of `L`. The minimum, i.e. the most a *single* survival observation could
achieve, is tabulated below. **Attainability is applied here, not afterwards:**
three of the eight unrestricted minima sit above their section's attainable
maximum (ADR-0024: KP 57.4 43.25, KP 58.8 42.75, KP 60.0 44.25, KP 62.0 50.5 m
T.P.), so the ladder is cut at that stage before the minimum is taken and the
unrestricted value is shown only for completeness.

| stratum | attainable best level | Var(L) floor | unrestricted floor |
|---|---:|---:|---:|
| KP 57.4 matrix | 40.75 | 0.8948 | 0.8948 |
| KP 57.4 bulk | 43.25 | **0.8881** | 0.8881 |
| KP 58.8 matrix | 41.25 | 0.9031 | 0.9031 |
| KP 58.8 bulk | 42.75 | 0.9918 | 0.9113 at 45.00, unattainable |
| KP 60.0 matrix | 42.75 | 0.9394 | 0.9394 |
| KP 60.0 bulk | 44.25 | 0.9256 | 0.9250 at 44.75, unattainable |
| KP 62.0 matrix | 48.75 | 0.9091 | 0.9091 |
| KP 62.0 bulk | 50.50 | 0.9932 | 0.8905 at 56.00, unattainable |

So **no single survival at any attainable stage removes more than 11.2 % of
`Var(L)`** (KP 57.4 bulk, the binding case, and it is attainable), against the
4.5 % the 2016 event removed at KP 58.8. Survival evidence is a weak and
bounded instrument for the seepage length. It is not a powerless one, and the
recommendation to survey the geometry is properly justified by that weakness
plus the sensitivity ranking, not by an impossibility theorem.

**On the Sobol index.** `ST_L = 0.49 to 0.78` (ADR-0033) is a share of the
variance of a specified output under a specified input distribution, estimated
by the Jansen 1999 estimator. It is not a bound on posterior uncertainty, not a
fraction of uncertainty immune to evidence, and not a value-of-information
result. Conditioning changes the very distribution the index is defined over, so
"that share is irreducible" does not follow from the index at all, independently
of how weak the observed update happens to be. The index and the update are not
commensurable quantities.

---

## 2. Failure-set nesting is a theorem of the head convention

### 2.1 The derivation

To pass `l_c` the pipe needs `H_erosion > H_eq(l_c) = H_c`, `H_eq` reaching its
maximum `H_c` at `l_c` (Pol SIE 2024 Eq. 11). The erosion head is
`H_erosion(t) = (h(t) - z_toe) - 0.3 D_bl` (Eq. 6), so
`max_t H_erosion = (h_peak - z_toe) - 0.3 D_bl`. Hence

    transient failure  =>  (h_peak - z_toe) > H_c + 0.3 D_bl
                       =>  Z_static = H_c - (h_peak - z_toe) < -0.3 D_bl < 0
                       =>  static failure.

Strict inclusion `F_transient subset F_static`, with a guaranteed margin of one
crack decrement. The initiation gate only shrinks `F_transient` further, so it
cannot break the implication. `H_c` is single-source for both branches (M6), so
every knob that scales `H_c` (`m_p`, the foreland credit, `critical_length_factor`)
preserves it, and `toe_gradient_relief_factor` is gate-only and preserves it too.

### 2.2 What the measurement adds

| stratum | transient failures | marginal transient | worst `Z_static + 0.3 D_bl` [m] | P(S) transient | P(S) static | ratio |
|---|---:|---:|---:|---:|---:|---:|
| KP 57.4 matrix | 63 | **0** | -0.0239 | 0.99937 | 0.93742 | 1.066 |
| KP 58.8 matrix | 5,512 | **0** | -0.1903 | 0.94488 | 0.42366 | 2.230 |
| KP 60.0 matrix | 3,244 | **0** | -0.1957 | 0.96756 | 0.26685 | 3.626 |
| KP 60.0 bulk | 23 | **0** | -0.1662 | 0.99977 | 0.98158 | 1.019 |
| KP 57.4 / 58.8 / 62.0 bulk, KP 62.0 matrix | 0 | **0** | n/a | 1.00000 | 1.00000 | 1.000 |

Every one of the 8,842 transient-failing rows clears the static threshold by a
whole crack decrement, with no exception. **Across the eight production
conditioning sweeps the violation count is 0 out of 24,000,000 row-level
evaluations** (100,000 rows x 23 to 38 levels). ADR-0030 measured the same
quantity at the native 3600 s step, where forward Euler jumps the equilibrium
barrier and produces up to 1.7 % violating rows at one level, and `<= 6e-5` at
225 s on the 2026-07-10 configuration; at the current production configuration
it is exactly zero.

**So the empty cell is a verification result, and the two-by-two table is a
discretization diagnostic.** It stays in the output because two settings can
genuinely break the implication: `alpha_exponent_transient` (ADR-0017)
decouples the two critical heads, and `crack_resistance_factor = 0` (ADR-0051)
shrinks the margin to zero. The `filtering` module docstring claimed the two
sets "are not strictly nested", which was wrong for every setting production
reaches; it is corrected, and `tests/test_survival_information.py` now pins both
the implication and the knob that breaks it.

### 2.3 What the survival does and does not establish about the two comparators

Three quantities are routinely conflated and are distinguished here.

1. **Set inclusion.** `F_transient subset F_static`: a theorem, above. It says
   the transient criterion rejects no realization the static one would keep, so
   the rejection *set* carries no membership information specific to the
   time-dependent mechanism. This reading is sound and should be kept.
2. **Parameter conditioning.** The retained sample differs from the prior:
   `C_e` and `k_aq` means fall about 4 %, `L` rises 1.3 %, and the joint
   `C_e x k_aq` corner is rejected at 5.4 and 7.8 times the overall rate. Real,
   and measured.
3. **Model compatibility.** The same observation has probability 0.945 and
   0.968 under the transient comparator against 0.424 and 0.267 under the
   static one. The observation is markedly more compatible with the transient
   comparator. That is a defensible statement about compatibility under the
   adopted priors and observation treatment.

**What it is not is a demonstrated calibration defect.** A single survival with
model probability 0.42 or 0.27 is an unremarkable observation; nothing in a
sample of one can establish a general calibration failure. The thesis's own
drained bracket makes this sharper than any external argument: crediting the
measured berm leaves **34 %** static failure at KP 58.8's observed peak, so
under the as-built configuration the static comparator assigns the observation
probability **0.66**. The four sections are one flood at four locations, not
four independent replicates, so no joint calibration test is available either.
"Shown to be miscalibrated in absolute terms" is therefore withdrawn; the
relative statement stands.

No Bayes factor, model prior or formal model-selection apparatus is introduced
by this note, and none should be: the survival probabilities are reported as
what they are.

---

## 3. Fixed scenario weights are an analysis choice, not a non-identifiability result

The thesis states that the update "redistributes weight within an assumed prior
population rather than choosing between candidate populations, leaving the
epistemic band on that choice as wide as it found it". Holding the matrix/bulk
and conductivity-arm weights fixed is a legitimate and clearly-declared analysis
choice. The universal reading is false, and this repository already measured the
counter-evidence.

`docs/decisions/conductivity-bracket-posterior-side.md` (addendum 2026-09-14)
records rejection under `k_aq_regional_upper` of **65.0 %** and **86.5 %** at
KP 58.8 and KP 60.0 against production's 5.5 % and 3.2 %. The same observation
therefore has probability **0.350** and **0.135** under the upper arm against
0.945 and 0.968 under production: the survival is **2.70** and **7.17** times
more probable under the adopted population than under the upward arm. The same
record measures the output band narrowing on the posterior side by **1.95x**
(KP 58.8 historical) and **2.79x** (KP 60.0 historical), so a claim that the
posterior curves move by "nearly the same factor" as the prior ones holds only
at KP 57.4 and KP 62.0, where the update is near-vacuous.

The **conclusion** that the band remains wide is correct and unaffected:
post-update spans are still 94 and 1.6e5. What is withdrawn is the impossibility
framing, not the magnitude.

---

## 4. The 2016 loading contains no inter-peak interval for memory to act across

The thesis says the 2016 update's "information acts through within-event
memory" and calls the record "a multi-peak loading whose information content
flows through that mechanism". Measured at the mechanism's own datum, the
landside toe, that is not what the reconstructed records are.

| section | z_toe [m T.P.] | peak | hours above toe | excursions above toe | excursions above `z_toe + 0.3 D_bl` (median) |
|---|---:|---:|---:|---|---|
| KP 57.4 | 38.30 | 39.66 | 9 | **1** (9 h) | 1 (7 h) |
| KP 58.8 | 38.50 | 40.75 | 21 | **1** (21 h) | 1 (17 h) |
| KP 60.0 | 40.00 | 42.30 | 28 | 2 (4 h, then 24 h, 170 h apart) | **1** (21 h) |
| KP 62.0 | 44.90 | 45.73 | 6 | **1** (6 h) | 1 (5 h) |

Three of the four sections see a **single continuous excursion**. The fourth has
a 4-hour precursor 170 hours earlier which disappears once the crack decrement
is applied at the median blanket thickness, leaving one 21-hour window. The four
typhoons are real in the rainfall and in the discharge; at the stage datum that
governs this mechanism they merge into one sustained loading.

**Consequence for the proposed reset ablation.** A
reset-between-excursions counterfactual has no interval at which to act at three
of four sections, and a 4-hour precursor at the fourth. It would return the null
result by construction, so it is **not run**, and this is recorded as a closed
scope decision rather than an outstanding experiment. The defensible repair is
to scope the claim: the 2016 information is carried by the finite duration of a
single sustained excursion, and the compound-event memory model remains
untested, which the thesis already says in Chapter 5 and Chapter 8. Within-event
memory in the weaker sense (the pipe length is retained while the overload falls
below `H_eq` and the trajectory staircases) does operate and is unaffected by
this finding; what does not operate in 2016 is damage carried *between peaks*.

**Stale numbers found here (D03).** The above-toe durations of record, **9, 24,
31 and 6 hours**, are the superseded KP 56.6 gauge. Rebuilt through the
committed ADR-0035 loader at the corrected KP 56.73 node they are **9, 21, 28
and 6 hours**; both nodes were run in the same process to confirm the
attribution. `docs/phase2_report.md` section 3's table carried the stale row and
its own 2026-09-14 gauge addendum did not include it; it is corrected there with
a dated pointer.

---

## 5. What a later session must not reintroduce

* That survival filtering "operates on the seven-column matrix only" and
  therefore cannot condition `L`. It conditions the joint draw row-wise; the
  acceptance profile at KP 58.8 runs 0.72 to 1.00 across `L` deciles.
* That a Sobol total-effect share bounds what updating can achieve. It is a
  variance share under a fixed input distribution, and conditioning changes that
  distribution.
* That "no number of additional survival observations" could tighten `L`. One
  survival 0.50 m higher would tighten it 5.7 times as much.
* That the empty marginal-transient cell is an empirical finding about the 2016
  event, or that the two failure sets "are not strictly nested".
* That the static comparator has been "shown to be miscalibrated in absolute
  terms" by this observation.
* That the 2016 update's information flows through between-peak memory.
* The above-toe durations 24 and 31 hours.

**And what must be preserved.** The update is genuinely weak and local; `L` is
genuinely the dominant fragility input; the epistemic band genuinely remains
wide; the drainage confound genuinely bounds what the observation licenses; the
shared-sample implementation is verified correct, and the nesting is real.
