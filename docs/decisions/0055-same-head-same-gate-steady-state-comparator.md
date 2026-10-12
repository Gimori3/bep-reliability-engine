# ADR-0055: The steady-state comparator of record uses the transient model's own head and gate

Date: 2026-10-06

## Status
Accepted (owner decision, 2026-10-06, answering supervisor comments 1 and 2 of
Joost Pol on the pre-Green-Light thesis). Supersedes ADR-0028 **as the choice of
comparator for the RQ1 comparison and every static-side number the thesis
reports**; ADR-0028's code decision (the production static branch evaluates the
gross head) is unchanged and still governs the persisted `failure_matrix_static`
of every sweep. Supersedes the ADR-0051 "Alternatives Considered" verdict that
rejected the crack-reduced static comparator as the headline. No production
default, config, prior, kernel, persisted sweep, posterior or annual result
changes.

---

## Context

Since ADR-0027/0028 the two piping branches read different driving heads: the
static comparator the gross head `h_peak - z_toe` (Sellmeijer 2011, "each model
as its author intended"), the transient branch the crack-reduced head
`h(t) - z_toe - 0.3 D_bl` (Pol SIE 2024 Eq. 6). The static branch also has no
uplift/heave gate. The thesis therefore reported the static-transient
difference as a mixture of three things (head convention, gate, finite time)
and then took it apart four ways: an equal-gross-head experiment (ADR-0051), a
crack-reduced equal-head reading, head-first and head-last ladders (ADR-0040),
and a probability-share waterfall. Its Summary set a design-level ratio of 26.9
(at least 148 at KP 57.4) beside "duration alone produces a factor of one to
about six".

Joost Pol's written comments on that version (2026-10-06):

1. "effect of cover layer resistance: why not only present results with the same
   head convention? Now it is confusing. It is not necessary to present
   everything you have done but the things that are relevant."
2. "magnitude of factor due to TD: 'duration alone produces a factor of one to
   about six' --> other parts mention a factor 30. what's the right metric? If
   its really B=1-6, how does this relate to results for NL where we find these
   factors for Rhine river with flood duration of weeks?"

Three primary sources, read on the page for this decision:

- **Pol et al. (2024, SIE), Eq. (18) and section 3.2.** The effect of time
  dependence is `F_td = P_f,stat / P_f,td`, where the "stationary" model is the
  same failure model "without time-dependence (instantaneous pipe growth)": the
  same Eq. (6) head, the same uplift and heave conditions, failure as soon as
  the critical head is exceeded. Its reference is therefore neither Sellmeijer's
  gross head nor a gate-free rule.
- **Schweckendiek (2014), Eq. (3.14), p. 26, and section 3.2.5, p. 27.** The
  Dutch assessment limit state is `Z_p = m_p H_c - (h - h_p - 0.3 d)`, and
  piping failure "can only occur if the uplift, heave and piping limit states
  are all exceeded", a parallel system `F = F_u ∩ F_h ∩ F_p`.
- **TR Zandmeevoerende Wellen (TAW 1999), p. 32 and Table 4.2, p. 38.** The
  term has a measured basis: laboratory tests on a fluidised sand column
  (Sellmeijer 1981) found a head loss of about 0.6 times the column height; the
  rule credits half of it ("een veiligheidsfactor van ongeveer 2") as 0.3 d over
  the uplift channel, and Table 4.2 applies `(ΔH - 0.3 d)` to the Sellmeijer
  criterion. This corrects `equal-head-convention-study.md` section 1.5 (the
  report had not been read there) and the thesis sentence that no step
  calibrates the coefficient.

The head loss in the exit is a property of the exit, not of how fast the pipe
behind it grows. A comparison that gives it to one branch only counts it as part
of the time effect, which is the confusion Pol names.

---

## Decision

The steady-state comparator of record is the Stage 6.6 comparator **C3b**
(ADR-0040 Decision 2): failure iff the uplift/heave gate is open at the event
peak and `h_peak - z_toe - 0.3 D_bl > H_c`, with the single-source `H_c`. It is
the adopted transient model with instantaneous pipe growth, so it is Pol's
stationary model and the Dutch parallel-system check (with the Terzaghi heave
gradient of ADR-0008). Against the adopted transient branch C4b the criterion
ratio is exactly Pol's `F_td` per event, and the index difference
`dbeta = beta(C4b) - beta(C3b)` is its primary register.

It is evaluated in closed form from the M8 diagnostics of a constant-stage
record on the persisted realizations, gated level by level on reproducing the
persisted gross-head static column bit for bit, by
`scripts/time_dependence_factor_study.py`. Evidence:
`docs/decisions/time-dependence-factor-study.md` / `.json`.

Sellmeijer's gross-head, gate-free form (C0) stays the persisted production
static branch and is reported once, as the calibrated form of the rule.

---

## Alternatives Considered

### Keep the gross-head comparator (ADR-0028) as the headline
Faithful to Sellmeijer's calibration, but the comparison then charges a
measured exit head loss and the initiation gate to "time", which is what the
comment objects to. Rejected.

### Crack-reduced head without the gate (C1)
Identical to C3b at every level at KP 62.0, because there the gate is open
wherever the crack-reduced head exceeds `H_c`. At KP 58.8 and 60.0 the gate
binds a little on the lower shoulder (995 against 922 failures in 1e5 at
KP 58.8, 40.00 m) and almost not at the design levels (44 964 against 44 957
and 21 636 against 21 634); near KP 57.4's design level it binds more (695
against 561 in 1e6 at 39.50 m).
It is not Pol's reference, so the ratio would not be `F_td`. Rejected as the
comparator; the gate's small contribution is reported beside it.

### Both on the gross head (ADR-0051 experiment)
Removes the term from the transient model instead, so the comparison is no
longer against the transient branch that every posterior, annual system
probability, mechanism share and climate ratio uses, and contradicts the
convention of the transient model's own author. Kept as a recorded experiment.

### Change the production static branch in `evaluator.py`
Would rewrite every persisted static matrix, the Phase 2 static rejections and
the gates that pair against them, for no change in any adopted result. The
companion evaluation gives the same numbers with a bit-identity gate. Rejected.

---

## Rationale

One head and one gate make the criterion difference the time effect and
nothing else, which is both what RQ1 needs to report as "the effect of finite
duration" and what makes it comparable, like for like, with the factor the
transient model's author publishes. The measured basis of the 0.3 term removes
the argument that it is a bare assessment convention to be withheld from the
static side.

---

## Consequences

- **Per event (matrix, as if undrained):** design-level `F_td` 6.86
  [5.47, 9.31] and dbeta 0.50 [0.44, 0.57] at KP 62.0 (N = 1e6); 2.28 and 0.72
  at KP 58.8, 3.88 and 0.81 at KP 60.0 (N = 1e5); KP 57.4's design level is
  unresolved (4 against 2 failures in 1e6), with 3.44 and 0.34 at 39.50 m. The
  factor falls toward 1.06 to 1.76 at the attainable tops while dbeta rises to
  1.2 to 1.5. The superseded design ratios were 3.09 to 51.2.
- **2016:** the likelihood ratio between the criteria becomes 1.34 at KP 58.8
  and 1.05 at KP 60.0 (was 1.76 and 1.14), 1.34 to 1.45 jointly.
- **Annual:** the steady-state over time-dependent annual piping probability is
  1.8 to 3.3 historically before updating (was 2.6 to 6.0 system).
- **Containment holds and tightens:** C4b ⊂ C3b ⊂ C1 ⊂ C0 by construction;
  the only C4b-not-C3b rows are the documented forward-Euler barrier jumps at
  KP 57.4 at N = 1e6.
- **Robustness brackets** re-measured on the new metric (conductivity means,
  blanket weight, model factor, critical length, seepage length, canonical
  event); C3b is exactly invariant under the critical-length and event arms.
- **Shared-gate arms move both criteria.** Blanket weight, exit-gradient relief
  (ADR-0050) and r_e reach C3b through the gate, where they never reached the
  gross-head branch. One reading reverses: the drained-section ladder put the
  as-if-undrained gap at the LOW end of its bracket on the gross head (dbeta
  1.13 / 1.22 rising to 2.26 / 1.94 at 60 % relief); on one head and gate it is
  at or within 0.02 of the TOP (0.72 / 0.81, falling to 0.55 / 0.77 at 60 %
  relief). Halving r_e drops C3b from 0.450 to 0.203 at KP 58.8, 41.00 m. The
  uniformity arms keep their dbeta change (-0.03 to -0.63) but their ratio
  factor now straddles one (0.79 to 1.44; was B x0.97 to 1.90). Values in the
  study note section 5.1 and the JSON `derived` and `halved_r_e` blocks.
- ADR-0028's Status line and ADR-0051's alternative are marked with dated
  pointers to this record. No frozen surface, config hash or Phase 2 replay
  gate is touched.

---

## References
- Pol, Kanning, Jonkman & Kok (2024), Structure and Infrastructure Engineering,
  Eqs. (6), (7), (18), section 3.2, Table 3.
- Schweckendiek (2014), doctoral dissertation, Eq. (3.14) p. 26, section 3.2.5
  p. 27.
- TAW (1999), Technisch Rapport Zandmeevoerende Wellen, TAW99-26, p. 32 and
  Table 4.2 p. 38 (`docs/references/tr-15_technischrapportzandmeevoerendewellen.pdf`).
- Sellmeijer et al. (2011).
- ADR-0008, ADR-0027, ADR-0028, ADR-0040, ADR-0051.
