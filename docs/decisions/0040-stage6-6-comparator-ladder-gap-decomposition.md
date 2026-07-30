# ADR-0040: Stage 6.6 Comparator-Ladder Decomposition of the Static-Transient Gap

Date: 2026-07-17

## Status
Accepted

---

## Context

The headline Phase 1 deliverable is the quantified bias between the static (Sellmeijer
2011, raw gross head, ADR-0028) and transient (Pol 2024 ODE, raw crack-reduced head,
ADR-0027) fragility curves. Spec §12 Failure Mode 4 and ADR-0009 commit the project to
decomposing this gap into named components rather than attributing it wholesale to the
temporal mechanism: **temporal**, **2D-vs-3D dimensional** (α = −1/3 vs −1/2),
**head-convention** (the 0.3·D_bl crack term, exactly, since ADR-0027/0028 removed r_e
from both piping heads), and **H_eq-conservatism** (the 0.9·H_c end anchor of Pol SIE
2024 Eq. (11), ≈1.95× progressive-phase rate inflation at L = 3 m, field-scale
magnitude open per ADR-0009).

The Stage 6.6 mission brief prescribes a five-comparator ladder (C0 static gross 2D →
C1 static crack-reduced 2D → C2 static crack-reduced 3D → C3 sustained-peak transient →
C4 real-hydrograph transient) with C2 vs C3 as a consistency check, on the governing
section KP62.0 and the contrast section KP57.4, and invites improvement of the frame
where justified. Three facts about the as-built engine force adjustments:

1. **The production transient runs at α = −1/3** (single-source H_c, spec §1/§4;
   ADR-0017's `alpha_exponent_transient = −1/2` is an opt-in Discussion-only
   sensitivity, Pol-endorsed baseline −1/3). A ladder whose C2 carries −1/2 but whose
   C4 is the production engine would silently re-cross the dimensional axis between C3
   and C4, conflating dimensional with temporal — the precise Failure Mode 4 error.
2. **The sustained-peak transient limit has an exact closed form** (proof in
   Decision 2), so the "pseudo-static comparator" does not need an arbitrary hold
   duration at production N; the ODE is needed only to *verify* convergence to the
   limit.
3. **The H_eq-conservatism component provably vanishes from the sustained-head failure
   indicator** (same proof): the 0.9·H_c anchor lowers the descending branch of
   H_eq(l), which changes progression *speed*, never the sustained-head breach
   *condition* (the binding barrier is the curve maximum H_c at l_c). It is therefore
   structurally inside the temporal step of any indicator-level ladder and needs its
   own opt-in isolation (ADR-0041).

---

## Decision

### 1. Comparator set — two coherent ladders on one shared sample

All comparators are evaluated on the **identical** (N, 7) theta matrix and the
identical independent stochastic-L draw (the run's own seed recipe, regenerated via the
public `sample_theta` / `run.seepage_length_samples_for_config` seams exactly as the
Phase 2 replay does), so every difference is physical, not sampling noise (ADR-0002
extended across comparators). Ten comparators per section, each an (N, N_h) boolean
failure matrix over the conditioning grid (the generated config grid plus the exact HWL
level inserted as the design-flood evaluation point):

| ID  | Branch                      | Load head            | α (H_c)      | H_eq end factor | Loading            |
|-----|-----------------------------|----------------------|--------------|------------------|--------------------|
| C0  | static                      | raw gross            | −1/3         | —                | peak               |
| C0b | static                      | raw gross            | −1/2         | —                | peak               |
| C1  | static                      | crack-reduced        | −1/3         | —                | peak               |
| C2  | static                      | crack-reduced        | −1/2         | —                | peak               |
| C3b | pseudo-static (analytic)    | crack (Eq. 6)        | −1/3         | (none binds)     | sustained peak     |
| C3a | pseudo-static (analytic)    | crack (Eq. 6)        | −1/2         | (none binds)     | sustained peak     |
| C4b | transient                   | crack (Eq. 6)        | −1/3         | 0.9 (production) | canonical d4PDF    |
| C4a | transient                   | crack (Eq. 6)        | −1/2         | 0.9              | canonical d4PDF    |
| C4c | transient                   | crack (Eq. 6)        | −1/3         | 1.0 (ADR-0041)   | canonical d4PDF    |
| C4d | transient                   | crack (Eq. 6)        | −1/2         | 1.0 (ADR-0041)   | canonical d4PDF    |

C0 is the production static branch and C4b the production transient branch; both are
drift-guarded bit-identical against `evaluate_batch` flags, and against the persisted
production sweep matrices at every common grid level at production N.

**Engine ladder E** (endpoint = the production gap, both branches at −1/3):
`C0 → C1 → C3b → C4b`, components: head-convention (C0−C1), initiation gate (C1−C3b),
temporal net of H_eq-conservatism (C3b−C4b, with the H_eq share bounded by C4c−C4b).
There is *no* dimensional step inside ladder E — the production branches share one H_c
by the single-source contract, so the dimensional axis contributes exactly zero to the
production gap; it enters only when the transient is re-anchored at its calibration
exponent (ADR-0017), which ladder P measures.

**Physics ladder P** (endpoint = 3D-consistent transient, the ADR-0017 sensitivity):
`C0 → C1 → C2 → C3a → C4a`, components: head-convention (C0−C1), dimensional (C1−C2,
expected *negative*: the 3D critical head is lower, so this component opposes the
others), initiation gate (C2−C3a), temporal net of H_eq-conservatism (C3a−C4a, H_eq
share bounded by C4d−C4a).

### 2. The pseudo-static comparator is the exact sustained-head limit

Under a constant outer level h held indefinitely, the transient model's failure
indicator has a closed form. Proof: the gate heads are time-invariant, so I_er is
constant (≡ heave-now under the ADR-0008 Terzaghi collapse). H_eq(l) is piecewise
linear through (0, 0), (l_c, H_c,trans), (L, 0.9·H_c,trans), hence H_eq(l) ≤ H_c,trans
for all l with equality only at l_c. If H_erosion = (h − z_toe) − 0.3·D_bl >
H_c,trans, the overload is bounded below by H_erosion − H_c,trans > 0 along the whole
path, dl/dt is bounded away from zero, and the pipe reaches L in finite time. If
H_erosion ≤ H_c,trans, the overload vanishes at l_eq = l_c·H_erosion/H_c,trans ≤ l_c
on the rising branch and the pipe stalls there (monotone approach, never crossing l_c).
Therefore:

    C3 failure  ⇔  heave gate open at peak  ∧  H_erosion(peak) > H_c,transient

The comparison uses strict `>` (equality stalls asymptotically at l_c), versus the
engine's `Z ≤ 0` static convention; the boundary set has measure zero under continuous
priors. Two corollaries anchor the mission's C2/C3 "consistency check" as an exact
statement rather than an empirical hope:

- **Nesting:** at matched α and matched (crack-reduced) head, C3 = C2 ∩ {gate}, so
  C3 ⊆ C2 exactly and the C2−C3 step isolates precisely the uplift/heave initiation
  gate. Any C3 row outside C2 is a bug (or a boundary-equality row).
- **H_eq-conservatism drops out:** the 0.9 anchor does not appear in the condition, so
  the sustained-head indicator is end-factor-invariant. The component survives only in
  finite-time (rate) behavior, i.e. inside the temporal step, where C4c/C4d bound it.

Implementation: one `evaluate_batch_diagnostics` call per level on a short constant
record (the engine's own kernels produce the gate latches, H_c_transient, r_e), then
the closed-form indicator from those diagnostics plus the per-row D_bl and crack
constant (`progression.CRACK_RESISTANCE_FACTOR`). A finite-duration ODE verification
ladder (hold durations doubling from 1 to 64 days, pilot N = 10^4, three levels per
section) demonstrates convergence of the integrated indicator to the analytic limit and
quantifies the residual near-critical slow rows; the residual is reported, not hidden.

### 3. Initiation gating stays in the pseudo-static comparator

The gate is part of the transient physics being compared, and removing it would fold
the gate effect invisibly into the temporal step. Keeping it makes C2−C3 the named
"initiation gate" component. (The gate evaluated at sustained peak is the most
favorable case for initiation — if heave cannot occur at the peak held forever, it
cannot occur under the real hydrograph — so the gate component is a lower bound on the
gate's effect under real loading; the remainder appears inside the temporal step via
gate timing. Stated as a limitation in the report.)

### 4. d70 interpretation

Matrix is the primary decomposition run (N = 10^5, both sections, full grid + HWL).
Bulk runs as a reduced-N (10^4) sensitivity: the ADR-0033 GSA found the bulk-d70 space
largely degenerate (P_f ≈ 0 at design levels), so a full-N bulk decomposition would
mostly decompose zeros; the sensitivity documents where that holds on the grid and
reports fractions only where the total gap is resolved.

### 5. Attribution and path dependence

The **canonical presentation is ladder P**, defended: it starts at conventional
practice (C0), ends at the transient model on its own calibration scaling (C4a), and
each step toggles exactly one modeling axis in the order load convention → resistance
scale → initiation physics → time. The gate and temporal steps cannot be reordered
(both exist only inside the transient machinery; there is no "temporal before gate"
comparator), so path freedom lives only on the static side and in where the dimensional
toggle is evaluated. That freedom is quantified, not assumed away:

- The {head, α} static 2×2 lattice is complete (C0, C0b, C1, C2): both orderings of
  the two components are reported, plus their exact two-toggle Shapley values (the
  average of the two orderings) and the interaction (difference of conditional steps).
- The dimensional toggle is evaluated at three ladder positions — static (C1−C2),
  sustained (C3b−C3a), and full transient (C4b−C4a) — exposing its interaction with the
  gate and temporal axes directly.
- Ladder E and ladder P are both reported in full; the report states explicitly that
  component magnitudes are order-conditional and by how much.

### 6. Statistical treatment

- Per comparator per level: raw P_f with always-on Clopper-Pearson 95% CIs
  (`fragility.binomial_ci`, the ADR-0024 presentation; at tail-only levels these ARE
  the deliverable and per-level probability *ratios* are reported alongside
  differences).
- Per component per level: ΔP_f with **paired** bootstrap CIs (B = 1000 realization
  resamples, percentile 95%; pairing exploits the shared-sample contract — the same
  resampled rows are used for every comparator, so the CI reflects the discordant
  set, not two independent binomials).
- A component whose paired-bootstrap CI contains zero is reported as **statistically
  unresolved at that level**, never as a finding.
- Design-flood evaluation point: the section HWL (2019 bank-height data, ADR-0018),
  inserted exactly into the grid. Waterfall charts at HWL and at the top attainable
  grid level; KP62.0 levels ≥ 51.0 m MSL are the ADR-0024 hypothetical fit-stabilizers
  and are flagged as such, never presented as attainable.

### 7. Built-in consistency gates

(i) C0 == production static flags and C4b == production transient flags, bit-identical,
at every common level against the persisted sweep HDF5 files; (ii) Euler-flip
diagnostics: per-level counts of C4 rows outside C3 (same α) and of C4b rows outside C0
— both are impossible in continuous time (the ADR-0030 argument) and are reported per
level (expected 0 at 225 s **at the production N = 1e5**; amended 2026-07-30 —
at N = 1e6 KP 57.4 carries 4 `c4b_not_c3b` rows at 39.50 / 40.25 / 40.75 m, a rate
of 4e-6 whose expected count at N = 1e5 is 0.4, so "0" is a statement about the
sample size and not about the discretisation being exact; see
`adr0040-hwl-bias-resolution.md` §2.7. KP 62.0 stays clean at both N);
(iii) the finite-T sustained ladder of Decision 2;
(iv) the full pre-existing test suite stays green.

---

## Alternatives Considered

### Literal mission ladder (single ladder, C2 at −1/2, C4 = production −1/3)
Pros: five comparators only. Cons: silently re-crosses the dimensional axis between C3
and C4, so "temporal" would absorb minus-one dimensional component; C2/C3 mismatch
would conflate three causes. Rejected as exactly the Failure Mode 4 conflation.

### Finite sustained-peak ODE runs at production N as the C3 deliverable
Pros: no closed-form reasoning needed. Cons: an arbitrary hold duration; near-critical
rows converge arbitrarily slowly, so any finite T misclassifies a duration-dependent
sliver and the "time constraint never binds" definition is never actually attained;
cost ~10× the rest of the campaign. Rejected: the analytic limit is the *definition* of
the sustained comparator; the ODE ladder verifies the engine converges to it.

### Full four-toggle Shapley attribution (16-vertex lattice)
Pros: symmetric attribution. Cons: requires comparators that are not physically
meaningful models (e.g. gross-head ODE, which would need a crack-term hook solely to
fill lattice vertices) and several extra transient sweeps to decorate an attribution
nobody can interpret physically. Rejected in favor of the complete static sub-lattice
plus the dimensional toggle at three positions plus dual ladders.

### Wire the H_eq end factor into `Config`
Rejected: it is an analysis variant, not a production axis (ADR-0009 keeps Eq. (11)
as published); the override stays a keyword-only evaluator argument (ADR-0041),
mirroring how ADR-0017 began.

---

## Rationale

The two-ladder frame is the minimal structure that (a) reports the mission's three
components with uncertainty, (b) honors ADR-0009's fourth component instead of burying
it in "temporal", (c) keeps the production gap (the thesis headline) decomposed
end-to-end without ever crossing an axis twice, and (d) turns the mission's C2/C3
consistency check into a provable nesting plus a measured gate component. The analytic
sustained limit removes the largest arbitrary choice (hold duration) from the
production path and is verified empirically where it matters.

---

## Consequences

- New module `bep_reliability_engine/gap_decomposition.py` (comparator construction,
  analytic sustained limit, paired bootstrap, persistence), driver
  `scripts/stage6_6_gap_decomposition.py`, tests `tests/test_gap_decomposition.py`.
- New opt-in `equilibrium_end_factor` override in M7/M8-batch (ADR-0041).
- Results under `results/stage6_6/` (HDF5 comparator matrices + JSON sidecar +
  derived component tables); report `docs/stage6_6_report.md`; figures
  `docs/figures/stage6_6_*.png`.
- The static comparators C1/C2/C0b are **analysis variants**; the production static
  comparator remains the raw gross head (ADR-0028 untouched).
- Expected signs (checked at runtime): C1 ⊆ C0, C2 ⊇ C1, C3 ⊆ C2 (matched α),
  C4 ⊆ C3 and C4b ⊆ C0 up to Euler flips, C4c ⊆ C4b (higher barrier, fewer failures);
  the dimensional component is negative (gap-narrowing) wherever resolved.
- KP62.0's transient transition stays unbracketed (ADR-0024): transient-side components
  at KP62.0 are tail statements carried by CP CIs and ratios, not fitted curves.

---

## References

- Mission brief: Stage 6.6 static-transient bias quantification (2026-07-13).
- `docs/architecture.md` §12 Failure Mode 4; §13 (committed decisions).
- ADR-0002 (shared sample), ADR-0008 (gate collapse), ADR-0009 (H_eq-conservatism),
  ADR-0017 (transient-only α), ADR-0024 (tail deliverable), ADR-0027/0028 (raw heads),
  ADR-0030 (225 s; the trans-not-static diagnostic), ADR-0033 (GSA; bulk degeneracy),
  ADR-0041 (end-factor override).
- Pol SIE 2024 Eqs. (5), (6), (7)-(10), (11); Sellmeijer (2011) formula [6];
  van Beek (2015) (α divergence).
