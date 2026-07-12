# ADR-0033 companion note: the Stage 6.5 GSA study record

Date: 2026-07-12. Status: complete (both governing sections + companions).
Decision record: `0033-variance-based-global-sensitivity-analysis.md`.
Machine-readable records: `adr0033-gsa-study-kp58_8_matrix.json`,
`adr0033-gsa-study-kp60_0_matrix.json`,
`adr0033-gsa-study-kp58_8_matrix_companions.json` (tracked copies of
`results/gsa/*_gsa.json`). Thesis text: `_thesis_gsa.tex` (+ `.bib`).

## 1. What was measured

Sobol' first-order (S_i) and total-effect (ST_i) indices of the
eight-dimensional production input space — the seven θ parameters plus the
stochastic seepage length L (lognormal, CoV 0.20; the 8th generator, never
an 8th θ column) — for four QoIs per conditioning level:

| QoI | Definition | Regime |
|---|---|---|
| Y1 | 1{Z_trans ≤ 0} | primary; V = P_f(1−P_f) |
| Y2 | 1{Z_stat ≤ 0} | comparator (bias attribution by contrast) |
| Y3 | l_e,final / L | continuous progression measure |
| Y4 | Z_stat = H_c − (h−z_toe) | continuous static margin; level-invariant |

Sections and levels (shoulder / design HWL / transition / upper, from each
production fragility curve): KP58.8 matrix {40.25, 41.00, 41.50, 42.50} and
KP60.0 matrix {42.00, 42.75, 43.25, 44.25} m MSL.

Method (ADR-0033): Owen-scrambled Sobol' radial design (cost 10N per
replicate), Saltelli-2010 S_i + Jansen ST_i, N = 2^13 with R = 25
independent scramblings per level (~2.0M engine realizations per level),
N-ladder 2^10..2^13, replicate-t 95% CIs (primary) + row-bootstrap B = 500
(cross-check), numba backend, Δt = 225 s (ADR-0030). Runtime: 389 s
(KP58.8) + 282 s (KP60.0) + 213 s (companions) on the dev machine.

Machinery validation (before the engine): Ishigami (|err| < 0.01),
g-function k=8 (< 0.015), linear-Gaussian threshold indicator vs quadrature
(< 0.02), correlated-copula closed form (< 0.015) — `tests/test_sensitivity.py`;
bit-identity pins of the generator→physical map to M2 `sample_theta` and of
the QoI adapter flags to M8 `evaluate_batch` — `tests/test_gsa_qoi.py`.
In-run cross-check: GSA-recovered P_f matches the production sweep at every
level (e.g. KP58.8 design 0.2633 vs sweep 0.2627).

## 2. Headline results

**1. The stochastic seepage length L is the top- or co-top-ranked input for
every QoI at KP58.8 and top-three everywhere.** Y1 design-level ST: L 0.63 >
k_aq 0.57 > C_e 0.34 > d_70 0.28 (KP58.8); k_aq 0.61 > L 0.49 ≈ C_e 0.48 >
d_70 0.25 (KP60.0 — leadership is section-dependent, membership is not).
L acts through H_c (resistance), the rate denominator, r_e, and the failure
criterion Z = L − l_e itself. Since Phase 2 Accept–Reject filters only the
7-column θ matrix, survival evidence cannot reduce this dominant geometric
uncertainty — a hard ceiling on posterior tightening.

**2. Structural zeros are exact.** C_e, D_bl, k_bl, γ'_bl return identically
0.0 on Y2/Y4 (no static pathway, ADR-0001/0016/0028), and Y4's decomposition
is bit-stable across levels (the level only shifts the mean). Free
validation of both the machinery and the head-separation architecture.

**3. The fm7 interaction is measured, and it explains ADR-0031.** At the
fragility shoulder the transient indicator is ~76% interaction variance
(Σ S_i = 0.24 at KP58.8 40.25; 0.32 at KP60.0 42.00), with ST−S gaps of
0.6–0.7 on L and k_aq and ~0.4 on C_e and d_70. LHS stratifies marginals —
the additive variance component — so the measured near-total absence of
additive structure in the tail-classification output is the mechanism
behind the ADR-0029/0031 finding that the LHS-vs-crude variance ratio decays
to parity in the deep tail. C_e's influence is persistently interactive
(S 0.07 vs ST 0.34 at the KP58.8 design level): the 2016 survival evidence
constrains the joint high-rate corner (C_e, k_aq, L, d_70), not the C_e
marginal — expect the Phase 2 posterior to contract along the fm7 direction
and marginal posterior std-devs to understate the information gained.

**4. Initiation vs progression separate cleanly.** The gate variables
(D_bl, k_bl, γ'_bl through the r_e-attenuated uplift/heave check) matter
only at the shoulder (D_bl ST 0.16 at KP58.8 40.25), fading to noise above
the design level where heave is pervasively active; progression dynamics
(C_e, k_aq) and resistance (d_70, D_aq) take over. Under the ADR-0023
climate reading (a +4K GSA is definitionally the historical one at matched
level — verified bit-identical in-driver and recorded in the JSONs), the
+4K importance shift is the rightward rotation: away from blanket/initiation
variables toward the erosion-dynamics pair and L.

**5. Thresholding manufactures interactions.** Y4 is nearly additive
(Σ S_i = 0.98); its indicator Y2 at the same level has Σ S_i = 0.61 with
roughly doubled ST on the same three inputs. The indicator regime degrades
honestly at extreme P_f: Y2 at KP58.8 42.50 (P = 0.991) and KP60.0 43.25+
(P ≥ 0.98) fails the 0.02 drift criterion and is excluded from
interpretation (the degenerate-indicator regime, same grounds as ADR-0024's
raw-tail argument); Y4 carries the static conclusions there.

**6. Companions: no ranking fragility.**
- *Bulk d_70* (13 mm framework vs 0.53 mm matrix): the fragility sits ~4 m
  higher and the matrix design stage is degenerate (P_f = 0 at 41.0 m) —
  itself a finding about the co-primary interpretation. At matched curve
  position (45.0 m, P_f = 0.154) the leading pair is unchanged (L 0.69,
  k_aq 0.62) while weight shifts from rate to resistance (d_70 0.40 up from
  0.28; C_e 0.16 down from 0.34): coarse-grain failures are
  resistance-selected, not rate-selected.
- *Nataf ρ_log = 0.6* (bounding, ~6× the empirical estimate; both Rosenblatt
  orderings agree on the joint, P_f 0.2384/0.2386 vs 0.2633 independent):
  positive k_aq–d_70 correlation pairs fast-seepage draws with
  coarse-resistant draws whose H_c effects partially cancel — transient P_f
  drops, the soil-resistance variance share shrinks, and L's share grows
  (Y4 S_L 0.64 vs 0.44). Signature dependent-input effect observed: d_70's
  *full* Y4 contribution nearly vanishes (S = 0.01) while its *independent*
  contribution stays 0.18 — a full index below the independent one, exactly
  the Mara–Tarantola/Kucherenko phenomenon a naive independent-input
  treatment would have silently garbled. The Y1 ranking is preserved under
  dependence, so no conclusion rests on the ADR-0012 independence adoption.

## 3. Convergence and uncertainty evidence

- Ladder drift (final two rungs, max over inputs): ≤ 0.019 for every
  reported QoI-level pair; worst case the KP58.8 shoulder indicator (0.019),
  best the continuous Y4 (~0.001). The two pre-registered exceptions are the
  degenerate static-indicator levels noted above (recorded `converged_0p02:
  false` in the JSONs, excluded from interpretation).
- Replicate-t 95% CI half-widths at the operating design: ≤ 0.005 (S) and
  ≤ 0.004 (ST) for Y1 at the design levels; the pooled row-bootstrap CIs
  agree within ~0.005 everywhere (both interval families are stored per
  index in the JSONs).
- Invariants: ST_i ≥ S_i throughout; Σ S_i ≤ 1 within noise; small negative
  S_i only on noninfluential inputs and within CI of zero (the Primer p. 170
  expectation).

## 4. Reproduction

```
python scripts/gsa_study.py                    # both sections + companions
python scripts/gsa_study.py --plot-only        # redraw figures from JSONs
python scripts/gsa_study.py --companions-only  # companions alone
pytest tests/test_sensitivity.py tests/test_gsa_qoi.py
```

Figures (tracked under `docs/figures/`): `gsa_indices_<slug>.png`,
`gsa_levels_<slug>.png`, `gsa_interaction_<slug>.png`,
`gsa_convergence_<slug>.png`, `gsa_companions.png`. Notebook driver:
`notebooks/gsa_study.ipynb` (thin; loads JSONs, regenerates figures).
Seeds: SeedSequence off each config seed with the 0x65A0/0xB007 stream tags;
every number above is reproducible from the configs.

## 5. Cautions for reuse

- Indices are joint properties of model *and* prior: conditional on the
  ADR-0026 C_e prior (CoV 0.78, the widest), CoV(L) = 0.20, and the
  two-population coupling. Revisiting any of these re-weights the
  decomposition; the L finding in particular motivates scrutiny of the 0.20.
- Indicator indices lose meaning as P_f → 0/1; use Y3/Y4 there.
- Per-cross-section only; segment-scale importance awaits the length-effect
  λ_ac decision (spec §12 open item).
