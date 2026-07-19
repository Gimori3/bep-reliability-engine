# ADR-0026 companion note: the C_e prior — forensic reconciliation and propagation study

Date: 2026-07-19. Status: **study note (no decision change)** — the production
prior `C_e ~ Lognormal(mean 0.055, std 0.043)` of ADR-0026 is **retained**; this
note supplies the forensic reconciliation and the quantified propagation that
ADR-0026's "quantify on the next sweep" left open, and records a sourced
recommendation.

Decision record: `0026-ce-prior-sie2024-field-value.md`. Script:
`scripts/ce_prior_study.py` (`prior` / `propagate` / `phase2`). Machine-readable
records: `results/sensitivity/ce_prior/*.json` (gitignored, regenerable).
Figures: `docs/figures/ce_prior_{reconciliation,fragility_propagation,phase2_sensitivity}.png`.

---

## 1. The two numbers, verbatim from Pol

### 1a. Pol CompGeo 2024 (the "lab" values) — per-test calibrations

Table 1 reports the **calibrated** C_e for each experiment (verbatim, in Table 1
column order B25-232 / B25-245 / B25-248 / FS35-238 / FS35-240 / FS35-242 / FPH):

> `C_e — 0.012  0.010  0.030  0.018  0.007  0.018  0.014`

The calibration **target** is stated explicitly (p. 6, §3.1.1):

> "The erosion coefficient 𝐶ₑ is calibrated to resemble the **pipe length
> development over time**."

And the summary (p. 8, §3.2.3):

> "Calibration on the different small-scale experiments yields **0.007 < 𝐶ₑ <
> 0.030 (average: 0.016)**. Calibration of the large-scale experiment yields
> **𝐶ₑ = 0.014**. It is a promising result that this is close to the average 𝐶ₑ
> value from the small-scale experiments."

The linearity that makes propagation trivial (p. 9, §4.3.3):

> "The simulated progression rate relates linearly to the erosion coefficient
> 𝐶ₑ. Hence, uncertainties in 𝐶ₑ can be easily translated in terms of
> progression rate."

**0.007–0.030 is a *value range* — the min/max of seven point calibrations — not
a coefficient of variation.** Their empirical scatter (computed in `prior`):

| set | mean | CoV = std/mean | min–max |
|---|---|---|---|
| 6 small-scale | 0.0158 | **0.518** | 0.007–0.030 |
| all 7 (incl. FPH) | 0.0156 | **0.483** | 0.007–0.030 |

### 1b. Pol SIE 2024 (the "field" prior) — the reliability base case

Table 2 ("Distributions of random variables for the base case") lists, verbatim:

> `Erosion coefficient  Ce  –  0.055  σ=0.043  Ln`

(the same table gives `Model factor crit. head mp – 1 σ=0.12 Ln`, the ADR-0045
factor, and `Model factor uplift mu – 1 σ=0.1 Ln`). The provenance, verbatim
(p. 9, §3.1):

> "The choice of random variables aims to yield realistic values for the strength
> and load variables of levees across The Netherlands that are susceptible to BEP.
> However, given the large variation in properties across levees encountered in
> the field, **these values are only indicative**. … The distributions of the
> erosion coefficient 𝐶ₑ is **based on calibration with multi-scale piping
> experiments (Pol, 2022)**."

So `(0.055, 0.043)` is **`CoV = 0.043/0.055 = 0.782`** — and it is *not* a field
back-analysis of observed levee failures. It is an indicative base-case prior
whose mean traces (via the thesis) to the **same** experiments as CompGeo, under
a **different calibration target** (§2b below), plus a spread Pol adopts to
represent the coefficient's uncertainty.

---

## 2. Forensic reconciliation

### 2a. The work package's premise corrected

The tension is often stated as "0.055/0.78 (field) vs 0.014/0.03 (lab) — 4× lower
mean and vastly tighter." **The "vastly tighter" half is a misreading**: `0.03`
is the *upper value* of the lab range, and the lab per-test scatter is CoV ≈ 0.48–
0.52 — the *same order* as the field CoV 0.78, not two orders tighter. ADR-0001
already encoded this correctly, choosing CoV 0.50 to span the 0.007–0.030 range;
its p05–p95 is 0.006–0.027, bracketing the CompGeo range. **The genuine
difference between the two priors is almost entirely in the mean (≈4×), not the
spread.**

### 2b. Not a contradiction — two calibration targets (Pol, 2026-07-08 email; ADR-0026)

Pol's own decomposition of the factor ~4 (recorded in ADR-0026):

1. **Time-dependent pipe development (small scale) → C_e ≈ 0.014–0.016.**
   Reproducing the pipe growth *over time* — exactly what this engine integrates
   (`dl/dt = 89·C_e·k·((H−H_eq)/L)^0.81`, SIE Eq. 5) — needs the CompGeo Table 1
   values.
2. **Mean post-critical growth rate across ~14 tests → C_e ≈ 0.044 → 0.055.**
   Matching the *average* rate via the thesis regression Eq. 5.15 (Appendix E,
   over all tests) needs 0.055.

> "**The factor 3–4 between the two (0.016 vs 0.044–0.055) is unexplained** — Pol
> has no direct explanation." (ADR-0026, quoting the 2026-07-08 email.)

So `0.055/0.78` and `0.016/0.48` are **the same coefficient calibrated to two
different quantities**, not a contradiction. The mean gap is the target gap; the
field CoV (0.78 vs 0.48) is modestly wider, and the extra width plausibly encodes
the *epistemic* uncertainty about *which target belongs at field scale* — the very
factor 3–4 Pol cannot resolve.

### 2c. Is the ADR-0026 "not absorbing model uncertainty" claim defensible?

Yes. ADR-0026 records Pol's position that laminar-vs-turbulent (model-form)
uncertainty is nominally Sellmeijer's ~12% model factor `m_p`, **not** C_e's to
absorb — and `m_p ~ Ln(1, 0.12)` is now carried explicitly (ADR-0045, verbatim
from the *same* SIE Table 2). The C_e CoV 0.78 is therefore left to represent (i)
genuine between-experiment scatter in the erosion coefficient (CoV ≈ 0.48, an
intrinsic-uncertainty quantity) plus (ii) the unexplained factor-3–4 *epistemic*
gap between calibration targets. Neither is a laminar/turbulent model-form
uncertainty. The claim is defensible; the one honest refinement is that a portion
of the 0.78 is epistemic-about-target rather than aleatory-about-the-coefficient —
which is exactly what the Phase 2 update is meant to reduce.

---

## 3. Propagation to fragility (`propagate`; KP58.8/KP60.0, N = 3·10⁴, numba)

Five candidate priors, contrasted by **common random numbers on the C_e column**:
each remaps the *same* standard-normal image of the C_e LHS stratum recovered from
the production draw (`z6 = (ln C_e − μ_f)/σ_f`), so the other six θ columns and the
independent L draw are byte-identical and only the C_e marginal moves. For the
lognormal candidates this is bit-identical to re-running M2 with a different C_e
`PriorSpec`.

**Structural-zero validation (asserted in-run):** the static P_f is **byte-identical
across all five priors** at every level and both sections — the static branch has
no C_e exposure (ADR-0001/0028, ADR-0033 GSA structural zero). The C_e prior moves
*only* the transient branch.

Transient P_f as a multiple of the production (field ADR-0026) value:

**KP58.8** (shoulder 40.25 m, P_f,prod 0.025 · transition 41.50 m, 0.49 · design/HWL 41.00 m, 0.265):

| prior (mean) | shoulder | transition | design/HWL |
|---|---|---|---|
| CompGeo lab Ln(0.016, 0.48) | ×0.17 | ×0.44 | ×0.33 |
| ADR-0001 lab Ln(0.014, 0.50) | ×0.13 | ×0.38 | ×0.27 |
| Field mean, lab CoV Ln(0.055, 0.50) | ×1.09 | ×1.07 | ×1.09 |
| **Field ADR-0026 Ln(0.055, 0.782)** | **×1.00** | **×1.00** | **×1.00** |
| Reconciled mixture (mean 0.0355) | ×0.62 | ×0.77 | ×0.71 |

**KP60.0** (shoulder 42.00 m, 0.049 · transition 43.25 m, 0.53 · design/HWL 42.75 m, 0.317):

| prior (mean) | shoulder | transition | design/HWL |
|---|---|---|---|
| CompGeo lab Ln(0.016, 0.48) | ×0.08 | ×0.33 | ×0.21 |
| ADR-0001 lab Ln(0.014, 0.50) | ×0.06 | ×0.27 | ×0.16 |
| Field mean, lab CoV Ln(0.055, 0.50) | ×1.05 | ×1.10 | ×1.10 |
| **Field ADR-0026 Ln(0.055, 0.782)** | **×1.00** | **×1.00** | **×1.00** |
| Reconciled mixture (mean 0.0355) | ×0.58 | ×0.72 | ×0.65 |

Readings:

- **Mean dominates, CoV barely matters for P_f magnitude.** Adopting the lab mean
  (0.014–0.016) cuts transient P_f **3–6× at the shoulder, 2–3× at the transition,
  3–6× at design/HWL** — largest where P_f is rate-limited, compressing toward the
  transition where most rows breach regardless. Holding the mean at 0.055 and only
  tightening the CoV (0.782 → 0.50) moves P_f by ≤ ±10%. **The four-fold prior gap
  is a mean gap, and the fragility feels the mean.** (Minor note: the wider field
  CoV is marginally *less* conservative on P_f — the extra low-C_e mass fails to
  breach — so the ADR-0026 std choice is not a hidden conservatism on P_f.)
- The reconciled two-target mixture (mean 0.0355) lands at ×0.6–0.8, i.e. ~25–40%
  below production — the honest "we don't know which target" answer.

---

## 4. Propagation to Phase 2 (`phase2`; 2016 survival replay, full N = 10⁵)

The replay reproduces the production posterior exactly at the field prior (KP58.8
transient rejection 5.673%, KP60.0 3.363%, both marginal-transient 0 — matches
`docs/phase2_report.md` §11). Swapping only the C_e column:

**KP58.8 / KP60.0**, 2016 survival:

| prior (mean) | trans. rejection | marginal-transient | posterior C_e pull |
|---|---|---|---|
| CompGeo lab Ln(0.016) | 0.54% / 0.12% | **0.0% / 0.0%** | −0.4% / −0.1% |
| ADR-0001 lab Ln(0.014) | 0.40% / 0.08% | **0.0% / 0.0%** | −0.3% / −0.1% |
| Field mean, lab CoV Ln(0.055, 0.50) | 5.96% / 3.13% | **0.0% / 0.0%** | −2.0% / −1.7% |
| **Field ADR-0026 Ln(0.055, 0.782)** | **5.67% / 3.36%** | **0.0% / 0.0%** | **−4.1% / −3.7%** |
| Reconciled mixture (mean 0.0355) | 3.28% / 1.61% | **0.0% / 0.0%** | −3.1% / −2.1% |

Two robustness findings and one sensitivity:

- **The nesting conclusion is completely prior-robust.** Marginal-transient
  rejection (survives static, fails transient) is **exactly 0 under every C_e
  prior**, at both sections. Whatever C_e believes, every row that fails transient
  under the real 2016 loading also fails static: the 2016 event is far enough
  below the breach-within-window threshold that failure is static-dominated, so
  C_e rescales *how many* rows fail but never lifts a static-survivor into
  transient failure. The load-bearing Phase 2 claim — *the full-transient replay
  is nested in the static shortcut under 2016* — does **not** depend on the C_e
  prior.
- **The ~4% C_e pull is a field-prior artifact, ≈10× weaker under the lab prior.**
  Survival informs C_e only where the prior places C_e in a *failing* region:
  under the field prior ~5.7% of rows fail (the high-C_e tail), and rejecting them
  pulls the mean −4.1%; under the lab prior only ~0.5% fail, and the pull collapses
  to −0.3%. The "posterior pulls C_e down ~4%" headline should be reported as
  **conditional on the ADR-0026 field prior**, not as an unconditional property of
  the 2016 evidence.
- **The CoV width sets the pull, not the rejection.** At fixed mean 0.055,
  widening CoV 0.50 → 0.782 barely changes the rejection (5.96% → 5.67%) but
  doubles the C_e pull (−2.0% → −4.1%): the wide upper tail is precisely what the
  survival filters. This is the GSA fm7 picture (ADR-0033: C_e is interactive,
  S 0.07 vs ST 0.34) seen from the posterior side — the marginal std understates
  the information gained.

---

## 5. New findings

1. **Corrected premise.** The lab and field priors are **not** "4× lower mean and
   vastly tighter." They are ≈4× apart in **mean** with **comparable spread**
   (lab CoV ≈ 0.48–0.52 vs field 0.78). `0.007–0.030` is a value range, not a CoV.
2. **Two calibration targets, not a contradiction.** CompGeo Table 1 = per-test
   *time-dependent pipe-development* calibration (0.014–0.016), the target this
   engine's ODE literally integrates; SIE Table 2 = *mean post-critical growth
   rate* over the full validation set (0.055, thesis Eq. 5.15 / Appendix E). The
   factor 3–4 between them is a genuine, Pol-acknowledged open point.
3. **The static branch is C_e-invariant** (byte-identical P_f across all priors) —
   a free architectural validation of the ADR-0001/0028 head separation.
4. **Fragility feels the mean, not the CoV.** Lab-vs-field is a 3–6× swing in
   transient P_f at the shoulder/design levels; the CoV alone is a ≤10% effect.
5. **The nesting (marginal-transient = 0) is prior-robust**; the **−4% Phase 2
   C_e pull is field-prior-conditional** (−0.3% under lab) and **CoV-driven**.
6. The ADR-0026 "C_e is not a laminar/turbulent absorber" claim is **defensible**,
   now that `m_p ~ Ln(1, 0.12)` carries that model-form uncertainty explicitly
   (ADR-0045); the honest caveat is that part of the 0.78 CoV is epistemic-about-
   which-target, which the Phase 2 update reduces.

### Recommendation (sourced)

**Retain `C_e ~ Lognormal(mean 0.055, std 0.043)` as the production prior.** It is
Pol's explicit field-reliability recommendation, rests on the largest validation
set, and is the conservative (higher-P_f) side — *"Met die 0.055 zit je in ieder
geval aan de veilige kant qua faalkans … zelf zou ik dat aanhouden"* (ADR-0026).
Because the study shows the fragility difference is a **mean** effect and the
static branch is untouched, this choice is transparent and its cost is bounded and
quantified above. No config change: `scripts/generate_configs.py` keeps
`C_E_MEAN = 0.055` and the `tests/test_configs.py` drift guard keeps pinning
`(0.055, 0.782)`.

Carry as **documented sensitivities**, not defaults:

- the **CompGeo lab prior `Ln(0.016, 0.48)`** (the engine's own dl/dt target) as
  the *lower bound* — transient P_f ÷3–6 at design; the 2016 survival is then
  nearly uninformative about C_e (−0.3% pull), which is itself the finding that
  *the levee's survival tells us little about C_e if the lab value is right*;
- the **reconciled two-target mixture** as the epistemically honest middle for the
  Discussion of the unexplained factor 3–4 — but **not** the baseline, since it is
  less conservative and is not a form Pol uses.

Report the Phase 2 "−4% C_e pull" as **conditional on the field prior**, and the
"transient failure nested in static under 2016" as **prior-robust**.

---

## 6. Reproduction

```
python scripts/ce_prior_study.py prior       # forensic densities + moments (no engine)
python scripts/ce_prior_study.py propagate    # transient fragility vs C_e prior (~1.7 min)
python scripts/ce_prior_study.py phase2        # 2016 survival sensitivity (~0.4 min)
python scripts/ce_prior_study.py all
```

Seeds and physics come straight from the production configs and the persisted
production sweeps (`results/tokachi_kp5{8.8,60.0}_historical_matrix.h5`); every
number above regenerates from them. All C_e-column remaps trace to Pol's papers;
no C_e value is invented.

## 7. References

- Pol, Noordam & Kanning, *Computers and Geotechnics* 167 (2024) 106068
  (CompGeo 2024): Table 1 (per-test C_e), §3.1.1, §3.2.3, §4.3.3.
- Pol, Kanning, Jonkman & Kok, *Structure and Infrastructure Engineering* (2024,
  SIE): Table 2 (base-case distributions), §3.1, Eq. (5), Eq. (17).
- Pol (2022) PhD thesis: §5.4.4, end §5.5.2, Table 5.1, Eq. 5.15, Appendix E
  (the two calibration analyses; cited via ADR-0026's 2026-07-08 email record).
- ADR-0001 (stochastic C_e promotion; prior amended), ADR-0026 (field prior),
  ADR-0033 (GSA fm7), ADR-0045 (m_p model factor), `docs/phase2_report.md` §11.
