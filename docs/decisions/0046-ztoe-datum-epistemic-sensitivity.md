# ADR-0046: Surveyed Exit-Datum Uncertainty (z_toe ± 0.3 m) as an Epistemic Scenario

Date: 2026-07-18
Status: Accepted

## Context

Every head in the engine references the landside-toe elevation z_toe: the
static load `h_peak − z_toe`, the uplift/heave gate head `r_e·(h − z_toe)`,
the erosion head `(h − z_toe) − 0.3·D_bl`, the fragility fit datum
(`LognormFragility.datum_m`), and the Phase 2 window-closure check against
the observed 2016 record. The ADR-0021 toes are surveyed values from the OYO
1999 transverse sections with a stated uncertainty of about **±0.3 m** — an
uncertainty the 8-D GSA (ADR-0033) never saw, and which the HKV audit
(2026-07-18, item 3) flagged as order-of-magnitude-capable in the fragility
tail (the audit's KP58.8 table moves static P_f ~50× between loads 1.0 and
1.5 m). HKV's own tool carries the exit boundary (`h_exit`) as a stochastic
variable; that treatment was examined and rejected here (below).

## Decision

1. **z_toe uncertainty is a systematic, per-section epistemic scenario —
   never a stochastic sampler column.** A survey datum error is common to
   every realization at a section; an i.i.d. per-realization column (HKV's
   `h_exit ~ Normal` treatment) would model it as aleatory row-to-row
   scatter, understating its systematic effect and perturbing the frozen
   7-D contract for the wrong physics. The baseline z_toe stays the ADR-0021
   surveyed deterministic value **everywhere**.

2. **Phase 1 companion sweeps at z_toe ± 0.3 m** quantify the fragility
   shift at the informative sections: `scripts/ztoe_sensitivity_study.py`
   reconstructs each baseline's config from its own hash-checked metadata
   snapshot, shifts only `geometry.z_toe`, and re-runs the full sweep
   (theta, L, hydrographs identical) into
   `results/sensitivity/adr0046_ztoe/`. The script also measures the
   residual against the first-order reading (a pure ±0.3 m horizontal curve
   translation) — the transient branch need not translate exactly, because
   the canonical hydrograph shape is anchored at the base-flow stage, not
   at the toe.

3. **Phase 2 scenario path (`z_toe_delta_m`).** `load_phase1_run` (and
   `Phase2Settings` / the `--ztoe-delta` CLI flag) accept an epistemic
   datum offset applied to the **replay geometry only**: the config
   snapshot, its hash check, the theta/L/m_p regeneration and the retained
   Phase 1 matrices are untouched, so the knob isolates the **evidence
   channel** (how much the h_2016 anchoring datum alone moves the
   Accept-Reject outcome). Scenario outputs are name-suffixed
   (`_ztoe_plus0.30m` / `_ztoe_minus0.30m`) and stamped
   (`metadata['phase2']['z_toe_scenario']`) so they can never masquerade as
   the baseline posterior. Default 0.0 is bit-identical baseline
   (test-pinned).

4. **The fully consistent scenario** — the datum shifted end to end — is
   Phase 2 run **on the shifted Phase 1 companion files with delta 0**:
   their configs carry the shifted toe, so prior matrices, window closure
   and replay all see the same world. The companion script runs both forms
   and reports them side by side; the fully consistent form is the headline
   epistemic band, the replay-only form its evidence-channel decomposition.
   (In the replay-only form the posterior-fragility fit datum deliberately
   stays the baseline toe — the masked matrices ARE baseline-datum
   objects.)

## Alternatives Considered

### Promote z_toe to an 8th stochastic column (HKV's h_exit treatment)
Rejected — see Decision 1. Also breaks the frozen (N, 7) contract and every
persisted theta matrix for a quantity that is not row-aleatory.

### Post-hoc horizontal curve shift only (no re-runs)
Cheaper, but only first-order: it cannot capture the hydrograph-shape
anchoring asymmetry or the Phase 2 propagation, and the full re-run costs
seconds per section. Kept only as the *check* inside the companion script.

### Nothing (documentation-only caveat)
Rejected by the author: the datum enters the h_2016 anchoring, so the
sensitivity must propagate through the Bayesian updating and be reported
with numbers.

## Companion results (2026-07-18, production N = 1e5)

Full artifacts in `docs/decisions/adr0046-ztoe-companion.json` (regenerable:
`scripts/ztoe_sensitivity_study.py`, ~12 min; companion sweeps and posteriors
under gitignored `results/sensitivity/adr0046_ztoe/`); Phase 2 report §13
carries the tabulated reading.

- **Phase 1:** the curves translate horizontally by the datum offset — max
  residual vs a pure ±0.3 m translation ≤ 0.008 (static) / ≤ 0.018
  (transient) absolute P_f at both informative sections. The small transient
  residual is the canonical-shape base-flow anchoring (not toe-anchored).
- **Phase 2 (2016, `no_breach`):** the transient rejection and posterior
  tightening move by ≈ ×2 per 0.3 m. KP58.8 matrix transient rejection
  1.68% / **5.67%** / 12.99% at z_toe +0.3 / baseline / −0.3; posterior
  C_e mean shift −1.5% / **−4.1%** / −8.0%. KP60.0 matrix 0.81% /
  **3.36%** / 8.99%; C_e −1.2% / **−3.7%** / −8.2%.
- **Marginal transient rejection stays exactly 0** in every scenario (both
  signs, both sections, full N): the nesting headline (§11) is robust to the
  exit-datum uncertainty.
- **Replay-only ≡ end-to-end** for the acceptance masks (structural: the
  outcome depends only on θ, L, the observed record and the replay geometry,
  which both forms share). The two ADR-0046 forms produced bit-identical
  rejection and posterior-θ numbers; they differ only in which prior
  fragility the posterior masks (baseline- vs shifted-datum curves).

## Consequences

- Baseline behaviour, outputs, posteriors: unchanged (delta 0.0 bit-identical,
  test-pinned by `tests/test_ztoe_scenario.py`; scenario outputs
  name-segregated).
- New surface: `load_phase1_run(z_toe_delta_m=...)`, `Phase1Run.z_toe_delta_m`,
  `Phase2Settings.z_toe_delta_m`, CLI `--ztoe-delta`,
  `metadata['phase2']['z_toe_scenario']`, `scripts/ztoe_sensitivity_study.py`.
- The thesis Discussion should quote the ±0.3 m band alongside the baseline
  curves and posterior, as a bounded epistemic (not aleatory) uncertainty
  statement, and note the GSA scope limitation (datum uncertainty is outside
  the 8-D input space by design).

## References

- ADR-0021 (surveyed toe elevations, ±0.3 m), ADR-0033 (GSA input space),
  ADR-0035 (h_2016 anchoring), ADR-0045 (companion-run precedent).
- HKV Fragility Curve Creator `class_probpiping.py:77-87, 326` (stochastic
  `h_exit` — the examined-and-rejected treatment).
- HKV audit (2026-07-18), recommendation 3.
