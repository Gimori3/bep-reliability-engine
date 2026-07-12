# ADR-0037: Length-Effect Autocorrelation Length lambda_ac and Config-Gated Segment Upscaling

Date: 2026-07-13

## Status
Accepted (closes the architecture.md "lambda_ac undetermined" open decision; reversible by construction — one config field, OFF by default)

---

## Context

The thesis upscales per-cross-section conditional failure probabilities to
Uemura's 200 m segment grid through the weakest-link relation
`P_f,seg(h) = 1 - (1 - P_f,cs(h))^n_eff` with `n_eff = L_seg / lambda_ac`
(methodology chapter, "Length Effect Upscaling"; Kanning 2012; Hoffmans 2014).
`fragility.upscale_length_effect(p_f, n_eff)` has implemented the transform
since M9 was built, but `run.py` never calls it because the autocorrelation
length lambda_ac of the governing parameters (D_bl, k_aquifer) was
undetermined — the last open item in architecture.md §12 "Genuine open
decisions" blocking segment-level output. Phase 3 (ADR-0038) consumes
segment-level BEP fragility, so the value must now be fixed.

Two constraints shape the choice:

1. **The committed empirical route cannot resolve the scale that matters.**
   The thesis (§"The Length Effect and Spatial Autocorrelation") plans an
   empirical estimate from the OYO cross-sections, supplemented by the
   report-appendix longitudinal soil profile (土層縦断図). That profile is
   **not in the secured dataset**. The five committed OYO sections
   (`data/processed/tokachi_bep_inputs.csv`) sit 1.2–2.0 km apart and their
   D_bl (0.80/0.85/0.85/0.45/1.0 m) and k_aq (3e-3…6e-5 m/s) values swing
   strongly between neighbours, i.e. the parameters have substantially
   decorrelated at every observable lag. That bounds lambda_ac from above
   (lambda_ac << 1.2 km) but says nothing about the 40–300 m band that
   decides n_eff for a 200 m segment.

2. **The literature must therefore carry the sub-kilometre structure.** Both
   relevant sources are now local and verifiable:
   * Kanning (2012), Table 4-7 (p. 90): horizontal correlation distances for
     the piping mechanism — **layer (blanket) thickness 200–300 m** (his own
     Lexmond case study, §4.7.3: significant autocorrelation at 150 m lag,
     correlation distance "in the order of 200 m to 300 m", nugget caveat);
     **d_70: 180 m** (Vrouwenvelder & Steenbergen 2003B; Kanning's own Vianen
     case §4.8.2 found *no significant correlation pattern*); **ln k:
     25–50 m** (Rehfeldt et al. 1992 / JCSS 2006), **k: ~40 m** (Fenton &
     Vanmarcke 1990) up to **600 m** (Vrouwenvelder & Steenbergen 2003B, the
     Dutch practice value).
   * Schweckendiek (2014), Table 7.1 (p. 160): blanket thickness as the one
     random-field parameter in his piping updating example, Gaussian
     autocorrelation, **correlation length delta = 200 m**, adopted "after
     Kanning (2012)".

## Decision

1. **Primary value: lambda_ac = 250 m** — the midpoint of Kanning's own
   empirical blanket-thickness correlation distance (200–300 m), consistent
   with Schweckendiek's 200 m adoption of the same source. The blanket
   thickness anchors the choice because it is (a) the first governing
   parameter named by the thesis, (b) the only parameter with a defensible
   *empirical* correlation structure in the mechanism literature (Kanning's
   d_70 case found none; k spans 25–600 m across sources), and (c) the gate
   parameter through which every transient failure must pass (M5).
   For the 200 m segment this gives `n_eff = max(1, 200/250) = 1.0`:
   **no amplification** — one OYO cross-section is statistically
   representative of its 200 m segment.
2. **Conservative sensitivity bracket: lambda_ac = 100 m (n_eff = 2) and
   lambda_ac = 40 m (n_eff = 5).** The 40 m floor is the short-scale
   aquifer-conductivity reading (Fenton & Vanmarcke ~40 m; Rehfeldt 25–50 m),
   relevant because the GSA (ADR-0033) puts k_aq (with C_e and L) at the top
   of the transient variance budget, so a k-governed weak spot is the
   physically conservative reading. Segment results under the bracket are
   reported next to the primary, never silently substituted.
3. **n_eff is clamped at 1.0 from below** (`lambda_ac > L_seg` means the
   segment behaves as one cross-section; a segment cannot contain less than
   one). `upscale_length_effect` keeps its `n_eff >= 1` contract.
4. **Wiring is config-gated and OFF by default.** New M1 block
   `length_effect: {enabled: false, lambda_ac_m: 250.0, segment_length_m:
   200.0}` on every generated config (drift-guarded in `tests/test_configs.py`).
   When `enabled`, `run.py` records a `metadata['length_effect']` block —
   lambda_ac, n_eff, and the segment-level raw curves per branch obtained by
   applying the transform to the per-level raw P_f and to both Clopper-Pearson
   CI bounds (valid by monotonicity of the transform) — **without touching**
   the persisted cross-section FragilityResult curves or the HDF5 schema.
   Phase 2/Phase 3 consumers apply the same public transform to posterior
   curves at read time. No behaviour changes while `enabled: false`, which is
   the generated default: the Phase 1 deliverable remains the cross-section
   curve, exactly as before this ADR.

---

## Alternatives Considered

### Alternative 1: wait for the OYO longitudinal soil profile (土層縦断図)
Pros: the thesis's preferred empirical basis; sub-section resolution.
Cons: not in the secured dataset, retrieval date unknown; blocks Phase 3
indefinitely on external data. Rejected as the blocker, retained as the
**revision trigger**: when the profile arrives, re-estimate lambda_ac
(method of moments per Kanning eqn. 4.20-4.21) and update this ADR's value —
one config field, no code change.

### Alternative 2: k_aq-anchored primary (lambda_ac ~ 40 m, n_eff = 5)
Pros: conservative; k_aq tops the theta-side GSA ranking.
Cons: the k literature spans 25–600 m with the Dutch practice value at the
top of that range; picking the short end as *primary* would build a factor-5
amplification on the least-constrained number in the table. Kept as the
bracket floor instead.

### Alternative 3: Dutch WBI trajectory-level length-effect calibration
Pros: national practice.
Cons: WBI's a/b length-effect factors are calibrated for multi-kilometre
trajectory assessments, not a 200 m segment grid, and no WBI source is in
the local reference set to verify the numbers against. Rejected — the thesis
methodology fixes the n_eff = L_seg/lambda_ac form anyway.

---

## Rationale

The decision uses the strongest locally verifiable evidence (two independent
sources agreeing on 200–300 m for the blanket layer), acknowledges honestly
that the empirically best-constrained answer is "no amplification at 200 m",
and carries the conservative reading as an explicit, reported bracket rather
than a hidden safety factor. Everything is reversible: the transform is a
pure post-processing function, the value is one config field, and the default
is OFF so no existing result changes silently.

---

## Consequences

* Phase 1 output remains cross-section fragility by default; segment curves
  appear in run metadata only when `length_effect.enabled` is set, and via
  `scripts/segment_fragility.py` for existing result files.
* Under the primary value the segment correction is the identity (n_eff = 1);
  the thesis should state this as a *finding* (the OYO section spacing and
  the blanket-anchored literature both argue the 200 m segment is within one
  correlation length), not as an omission.
* The conservative bracket multiplies deep-tail P_f by up to n_eff = 5 —
  material for KP62.0's raw-tail presentation (ADR-0024) and carried through
  Phase 3's mechanism-dominance comparison as a sensitivity band.
* The borehole-free reaches (KP53.8–56.0, Satsunai) would need their own
  literature-assigned lambda_ac with inflated uncertainty (thesis §3); that
  remains Phase 3 scope, out of this ADR.
* Supersession path: OYO longitudinal profile arrival triggers an empirical
  re-estimate (Alternative 1).

---

## References

- Kanning, W. (2012). *The Weakest Link — Spatial Variability in the Piping
  Failure Mechanism of Dikes.* PhD thesis, TU Delft. Table 4-7 (p. 90),
  §4.7.3 (p. 92), §4.8.2 (p. 95-96). Local copy
  `docs/references/PhDthesis_Kanning.pdf`.
- Schweckendiek, T. (2014). *On Reducing Piping Uncertainties — A Bayesian
  Decision Approach.* PhD thesis, TU Delft. Table 7.1 (p. 160). Local copy in
  `docs/references/`.
- Thesis methodology chapter, "Length Effect Upscaling: From Cross-Section to
  200-Metre Segment" (msc-thesis repo).
- Hoffmans (2014) — via the thesis's methodology citation (not local; form of
  the transform only, no numeric value taken).
- `data/processed/tokachi_bep_inputs.csv` (OYO section spacing bound).
