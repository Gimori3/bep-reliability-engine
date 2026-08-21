# The critical-pipe-length bracket: how large it is, and whether it cancels

**Status:** Accepted. Companion measurement for ADR-0049, which wires the knob.
No `Config` default changed, no production sweep re-run, no persisted production
artifact touched.

**Date:** 2026-08-21
**Driver:** `scripts/critical_length_bracket_study.py`
**Evidence:** `adr0049-critical-length-companion.json` beside this note
**Arms:** `results/sensitivity/adr0049_critical_length/` (12 full-N sweeps)
**Tests:** `tests/test_critical_length_factor.py` (20)
**Parents:** ADR-0049 (the override), ADR-0009 / ADR-0041 (the other anchor of
the same curve), ADR-0040 (the ladder this component belongs to), ADR-0047 §4.5
and `epistemic-bracket-synthesis.md` (the cancellation test and its vocabulary)

---

## 1. What this closes

The equilibrium curve of Pol SIE 2024 Eq. (11) has two anchors. Its **end**
value `0.9·H_c` was named a gap component by ADR-0009, given an opt-in override
by ADR-0041, and measured at field scale by Stage 6.6. Its **critical pipe
length** `l_c`, Eq. (13), had neither. The register of limitations in the thesis
carried the asymmetry in as many words: "critical pipe length not isolated as a
sensitivity, though the equilibrium-curve end anchor is", direction not
resolved, quantified no.

This note is the measurement. ADR-0049 is the knob it required.

## 2. The bracket, and where its range comes from

Multiplicative on Eq. (13), two arms:

| arm | factor | what it is |
|---|---|---|
| lower | **0.643** | the reciprocal of the upper arm: a mirrored counterfactual |
| upper | **1.556** | measured: DgFlow's 3D hole-exit critical length `1.36 m` for the in-domain S2-2 case (`L = 3 m`, `D = L/3`), Pol 2022 thesis Fig. 5.9 caption, over Eq. (13)'s `0.874 m` at the same geometry |

Eq. (13) states its own basis as agreement with **2D** numerical simulations
(SIE 2024 §2.3). The 3D case published beside it disagrees by 1.556, and this
repository already records that disagreement, as a caution against
cross-validating the formula against it (`m7-pol-ode-reference-values.md` §2).
The caution is right and is not withdrawn: 1.36 m is one case, not a re-fitted
rule. What it does support is a **band** on a formula whose own stated
validation is in a different number of dimensions from the model it feeds.

The lower arm is stated as what it is. No published case places the true
critical length below Eq. (13). A second one places it further above: the
B25-245 small-scale box measured `l_c = 0.197 m` against Eq. (13)'s `0.0905 m`,
a factor **2.18**. That case is out of the fitted domain and is a qualitative
gate only, so it is reported as a direction check and deliberately not used to
widen the band. Both empirical anchors sit on the **upper** side, which makes
this bracket asymmetric in evidence even though it is symmetric in construction.

## 3. Method

Four matrix sections, both arms, production N = 1e5 on the committed
conditioning grids, quoted at the five anchors of
`epistemic-bracket-synthesis.md` so the result reads straight into that ranking
table.

**The gate.** Each section's committed YAML is re-run with
`critical_length_factor=None` set *explicitly*, and both whole failure matrices
are required to be bit-identical to the persisted production sweep before any
arm number at that section is reported. **All four passed.** One run discharges
two obligations: the knob is inert when off, and the baseline has not drifted.

**The cancellation test** is the ADR-0047 §4.5 paired-bootstrap ratio of ratios,

    rho = (P_static / P_transient)_arm / (P_static / P_transient)_baseline

2000 replicates over the 16 joint pattern counts, null pinned at `rho = 1.0`, a
level counted resolved only when the 95 % interval excludes it. The statistic is
imported from `scripts/dem_cross_section_study.py`, not re-implemented.

## 4. The channel reading, made before the numbers

| channel | where | branches |
|---|---|---|
| the `(l_c, H_c)` breakpoint of the piecewise-linear `H_eq(l)` | `progression.equilibrium_head` | transient only |

That is the entire list. `l_c` does not appear in Eq. (12), so it does not reach
`H_c`; it does not reach the leakage lengths, `r_e`, or the uplift and heave
gate; and the static comparator does not read it. **Zero common-mode
channels** — the opposite end of the register from `m_p`, the one knob measured
to cancel.

It is **not the first zero-common-mode input**, and the note says so rather
than claiming a novelty it does not have: `gamma_bl_sub` reaches the uplift and
heave gate and nothing else, so it too leaves the static branch exactly
unchanged (`epistemic-bracket-synthesis.md` §2.5 measured that as an identity
at all 98 levels). What is new is where it lands. `gamma_bl_sub` departs by
1.15, 1.29, 1.22 and **1.00** at the four sections, so it is inert at the
governing one; `l_c` departs by up to 1.67 there. Of the two inputs that cannot
cancel by construction, this is the one that matters at KP 62.0.

Two predictions follow, and both were written before the arms were run:

* **P1.** The bracket cannot cancel in the static-to-transient ratio.
* **P2.** Stronger, and the reason this knob is worth measuring even though it
  is small: because the static branch is not merely nearly invariant but
  *exactly* so, the displacement of the ratio must equal the **reciprocal** of
  the displacement of the transient probability, level by level, to machine
  precision.

The driver enforces the premise rather than assuming it: it compares the whole
static failure matrix, cell by cell, and refuses to report if one cell moves. No
cell moved, at any level, at any section, in either arm.

## 5. Result

### 5.1 The effect on the transient conditional probability

Multiplicative width of the bracket (largest arm over smallest, baseline
included) at the five anchors:

| section | lowest reachable | rising limb | transition midpoint | **design HWL** | grid top |
|---|---|---|---|---|---|
| KP 57.4 | 1.32 | 1.32 | 1.10 | *no failing rows* | 1.01 |
| KP 58.8 | 1.33 | 1.33 | 1.10 | **1.16** | 1.00 |
| KP 60.0 | 1.57 | 1.49 | 1.10 | **1.17** | 1.00 |
| KP 62.0 | 1.00 | 1.70 | 1.12 | **2.08** | 1.00 |

The shape is the familiar one: widest in the tail, collapsing to unity as the
curve saturates. The largest value in the table is **2.08 at KP 62.0's design
high water**, where the baseline carries 15 failing rows out of 1e5.

**Direction: a longer critical length raises the transient probability.** The
upper arm multiplies transient `P_f` by 1.19 to 1.67 at the tail anchors and the
lower arm by 0.80 to 0.93. That is not the intuitive sign, and it is worth
setting out, because "the barrier is further away" reads as harder.

Write the traverse to breach as two integrals in the reduced coordinates of each
branch. On the rising branch `H_eq = H_c·l/l_c`, so with `u = l/l_c` the time to
reach the barrier is `l_c·A`, where `A` averages the inverse rate over overloads
running from `H` down to `H − H_c`. Beyond the barrier `H_eq` falls from `H_c`
to `0.9·H_c` over `L − l_c`, so with `v = (l − l_c)/(L − l_c)` the remainder is
`(L − l_c)·B`, where `B` averages the inverse rate over overloads running from
`H − H_c` up to `H − H_c + 0.1·H_c`. Total,

    T = l_c·A + (L − l_c)·B = L·B + l_c·(A − B).

Every overload entering `B` sits at the *bottom* of the range entering `A`, so
`B > A` and `T` **decreases** in `l_c`. The descending branch is the slow part
of the journey, and a longer critical length buys a shorter one. Checked
numerically over `H/H_c` from 1.05 to 2.0: `A/B` runs 0.34 to 0.77 and `T` falls
by 11 % across the bracket at the marginal `H/H_c = 1.05`.

The same algebra says why the knob is **small**. `l_c/L` is 0.206, 0.219, 0.241
and 0.236 in the mean at the four sections, so about four fifths of the traverse
lies on a branch the bracket does not move, and the bracket can only act on the
`l_c·(A − B)` term.

### 5.2 The cancellation verdict

**It does not cancel, and it propagates into the ratio exactly.** Largest
resolved ratio-of-ratios departure factor:

| arm | KP 57.4 | KP 58.8 | KP 60.0 | KP 62.0 |
|---|---|---|---|---|
| `l_c` lower (×0.643) | 1.111 | 1.122 | 1.166 | 1.226 |
| `l_c` upper (×1.556) | 1.194 | 1.238 | 1.275 | **1.667** |

Resolved at 16/16, 21 to 22/22, 22/22 and 28 to 29/29 evaluated levels: the
departure is real at essentially every level where the comparison can be made at
all, in both arms, at all four sections.

**P2 confirmed to machine precision.** The largest discrepancy between the
measured `rho` and the reciprocal of the measured transient displacement, over
all 89 evaluated levels and both arms, is **2.2e-16**. The ratio displacement
is therefore not merely non-cancelling but *identically* the transient
displacement, which follows from the static branch being exactly invariant
rather than approximately so. `gamma_bl_sub` shares that property for the same
structural reason; no other knob in the register does.

### 5.3 Where this sits among the other brackets

At the two anchors that carry the thesis's claims, against the
`epistemic-bracket-synthesis.md` ranking:

| bracket | ρ departure, KP 62.0 | transient span, KP 62.0 design HWL |
|---|---|---|
| `k_aq` prior mean | 2.24 to 45.6 | unbounded |
| `z_toe` ±0.3 m | 2.09 to 2.15 | 184 |
| L measurement | 2.11 | 15 |
| **`l_c` (this note)** | **1.23 to 1.67** | **2.08** |
| `gamma_bl_sub` | 1.00 | 1.00 |
| `m_p` | 1.07 | 2.80 |

`l_c` is a **small** knob. It is also, and separately, a **fully
non-cancelling** one. Those two facts are independent, and the pair
`l_c`-against-`m_p` is the cleanest illustration in the register of why: the
model factor departs by 1.07 to 1.22 across the four sections and the
shorter-`l_c` arm by 1.11 to 1.23, which are the same size, and they get there
by opposite routes. `m_p` moves each branch a great deal and the movements
nearly cancel; `l_c` moves one branch a little and nothing cancels. A departure
factor says how much of a comparison an input displaces and nothing on its own
about whether the input is influential or whether it is common-mode. Both
questions have to be put to the formulation.

## 6. Two riders

**The bracket is a duration effect, not a threshold effect.** Under an
indefinitely held head the ADR-0040 closed form for failure is
`gate ∧ H_erosion > H_c,trans`, in which `l_c` does not appear: `H_eq` peaks at
`H_c` at `l_c` whatever `l_c` is. So the critical pipe length cannot change
whether a realization is *capable* of breaching, only how long the traverse
takes. It therefore lives inside the temporal step of the comparator ladder,
exactly where the equilibrium end anchor lives, and it is not a fifth component
of the gap. Pinned by test at two conditioning levels, one where the finite hold
has converged and one deep in the tail where it has not.

**The invariance above is a bracket property, not a universal one.** On the
development stub a factor-four shortening (`l_c × 0.25`, far outside anything
published) does move the held-head indicator, by 2 rows in 400, through
forward-Euler barrier jumping: with the barrier at a quarter of its distance a
single step can clear it. The study arms do not. The production check is
stronger and is clean: **zero rows fail transiently but not statically** at any
of the 89 evaluated levels, in either arm, at any section, against a baseline
that also carries zero. The ADR-0030 discreteness diagnostic is therefore
undisturbed by the bracket at Δt = 225 s.

## 7. What this licenses, and what it does not

* The static-to-transient bias figures are now **`l_c`-conditional as well as
  L-conditional and `k_aq`-conditional**. The `l_c` conditioning is the
  narrowest of the three, at 1.11 to 1.67 against `k_aq`'s 2.24 to 163.
* The limitation is closed as *quantified*, not as *removed*. The bracket is a
  band on a formula, and both empirical anchors sit above the formula, so the
  band's evidenced half is the one that **raises** transient probability and so
  **lowers** the static-to-transient ratio.
* Nothing here changes a production number. The production configuration
  continues to carry Eq. (13) as published, and ADR-0049 §Decision records why.
