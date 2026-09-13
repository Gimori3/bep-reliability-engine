# Pre-registration: the foreland seepage-length credit and whether it cancels

Written 2026-09-13, BEFORE any credited arm was run. Fixed at this text; the
SHA-256 below is pinned in the ADR-0052 evidence record.

## The channel reading

The credit reaches exactly one quantity: the seepage length at which the
Sellmeijer critical head is evaluated, `L_eff = L + phi * lambda_out_eff`.
It therefore reaches `H_c` and nothing else. The complete channel list:

| channel | where | branches |
|---|---|---|
| static comparator `Z_static = H_c - (h_peak - z_toe)` | `evaluator` | static |
| `H_eq(l)` anchor (`H_eq(l_c) = H_c`, `H_eq(L) = 0.9 H_c`) | `progression.equilibrium_head` | transient |

Deliberately NOT scaled, and asserted so by test: the critical pipe length
`l_c` of Eq. (13), the traverse length and the `Z_transient = L - l_e`
criterion, the `L` in the Eq. (5) rate denominator, the `L` in `r_e`, the
leakage lengths themselves, the erosion head `H_erosion`, and the uplift and
heave gate. The credit is a credit in Sellmeijer's *rule*, which is what
TR Zandmeevoerende Wellen 1999 section 4.4.2 permits; it is not a claim that
the pipe is physically longer.

So the knob is **two-channel and common-mode in direction**: both branches see
the same raised `H_c`, and both failure probabilities must fall. That places it
between `m_p` (ADR-0045, pure common-mode, measured to cancel) and
`critical_length_factor` (ADR-0049, zero common-mode, exactly non-cancelling).

## The predictions

* **P1.** Neither branch is invariant. Unlike ADR-0049's `l_c` and ADR-0050's
  toe relief, the static failure matrix WILL move, at every section and every
  level where it is not saturated at 0 or 1.

* **P2.** The bracket does **not** cancel: `rho != 1` at levels where both
  branches resolve. The reason it cannot is that the two branches read the same
  raised `H_c` through different functionals. The static branch is a pure
  threshold on `H_c` (fails iff `H_c <= h_peak - z_toe`), while the transient
  branch must clear a barrier `0.3 * D_bl` higher in head AND traverse `L`
  within the flood, the traverse rate falling as `H_eq` rises. Cancellation
  would require the two to share one tail exponent in `H_c`, which the extra
  crack term, the uplift/heave gate and the time constraint all break.

* **P3 (the directional call).** `rho > 1` wherever it resolves: the credit
  **widens** the static-to-transient bias rather than shrinking it. Raising
  `H_c` by a factor `kappa` costs the transient branch strictly more than the
  static one, because the transient branch pays for it twice -- once in the
  barrier it must exceed, and again in the rate `max(0, H_erosion - H_eq)^0.81`
  that decides whether it traverses in time.

* **P4 (magnitude ordering).** The per-section displacement should order by the
  section's own `kappa = H_c(L_eff)/H_c(L)` at the prior means, largest at
  KP 58.8 (3.734), then KP 57.4 (3.481), then KP 60.0 (3.099), smallest at
  KP 62.0 (1.683). The bracket will therefore be far wider than ADR-0049's
  `l_c` bracket (x1.11 to x1.67 on the ratio).

* **P5 (resolution).** Because `kappa` is this large, most conditioning levels
  will have zero failing realizations on one or both branches under the credited
  arm, so `rho` will be **unresolvable at most levels**, and the design-level
  statement will be a pair of zero counts rather than a ratio. This is a
  prediction about what can be measured, not about physics, and it is stated in
  advance so that a sparse result table is not read afterwards as a failure of
  the study.
