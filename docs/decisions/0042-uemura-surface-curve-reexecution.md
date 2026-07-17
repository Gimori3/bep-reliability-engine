# ADR-0042: Uemura Surface-Fragility Curves by Faithful Re-Execution of His Own Models on His Own Inputs

Date: 2026-07-17

## Status
Accepted (reversible: every interpretive choice below is one constant or one
regeneration flag; the contract CSVs regenerate from committed raw inputs
with one command)

---

## Context

RQ3 needs the two pre-calculated surface-failure fragility curves (overflow,
fluvial scour) as machine-readable `P_f,i(h)` per 200 m segment — the class-D
blocker D1 of `docs/close_out_2026-07-12.md`, with the arrival contract fixed
by ADR-0038 decision 5. The 2026-07-17 data drop
(`data/digitized/uemura_fragility_curves/`, gitignored raw) contains Uemura's
WP2 workproduct but **no final machine-readable curve tables**. What it does
contain, censused file by file:

* **The models themselves.** Overflow (P1): the Dean et al. (2010)
  cumulative-work model, published in Uemura et al. (2024, Proc. IAHS 386)
  and Uemura's PhD thesis §4.2 (Japanese; equations verified verbatim), with
  the WP2 team's vectorized reference implementation in
  `2021-11-19 Description WP2 Work week 3.ipynb` (`count_failures`).
  Fluvial scour (P2): the USACE (2007) Erosion Toolbox excess-shear model,
  Uemura's own script `ErosionModel_231019.py`, documented in the WP2 final
  report (HKV PR3983, June 2024, §5) and thesis §4.3.
* **The exact per-segment input table.** `data/df_river.csv`: all levee and
  channel parameters per 0.2 km node over exactly the thesis study reaches
  (Tokachi KP 53.8–62.8, Satsunai KP 3.2–17.2; the 3 rows with survey gaps,
  Satsunai KP 16.8–17.2, lie outside the registry). Its `HQ_a`/`HQ_b`
  columns are **numerically identical** to the committed M3 rating files
  (`data/raw/rating_curves/HQrelation_*Riv_2017.csv`), so the stage axis is
  already the ADR-0021 T.P. m MSL datum — no datum conversion exists to get
  wrong. Its bank-height statistics (`Average_bh`, `Sig_bh`) match the
  committed `data/raw/bank_heights/BankHeight_AveSig_*.csv` files.
* **The published parameterization.** Overflow: rating-error
  N(mu=0.6, sigma=0.38) m at Obihiro (paper Eq. 10; workbook
  `Uncertainty_HQrelation.xlsx` is absent from the drop — see decision 6);
  per-KP crest error N(`Average_bh`, `Sig_bh`) (paper Eqs. 11–12); turf
  critical velocity N(1.80, 0.38) m/s "good" cover (paper Table 1); Dean
  threshold 0.492e6; friction f = 0.08; N_MC = 10,000. Scour: k = 0.021
  ft^3/(lb·hr) CoV 1.101, tau_c = 1.058 psf CoV 0.560 (WP2 Table 1 — its
  "Variance" column header is a misnomer; Uemura's script implements them as
  CoV and the script is authoritative), Manning n = 0.030, k_b = 0.157 ft,
  water density 1000 kg/m^3, N_MC = 10,000 (WP2 §5.4.3).
* **Anchors, not tables.** The `Probability of Overtopping_ObihiroKP56.73.xlsx`
  workbook is the **2020-era peak-velocity prototype** (single-time-step
  judgment, generic sigma_crest = 0.7), superseded by the Dean cumulative
  model — classified qualitative-only. The WP2 report Tables 3/4 give
  event-based annual failure probabilities per breach location under *their*
  WFLOW/RRI hydrology — order-of-magnitude anchors only.

The thesis (Methodology §"Imported Surface Failure Fragility Curves") fixes
the semantics this ADR must serve: conditional `P_f,i(h)` per 200 m segment,
overflow "accounts for uncertainty in the stage-discharge rating curve, the
levee crest height, and the grass cover quality"; scour "in the hydraulic bed
roughness and the geotechnical erosion susceptibility"; curves "used as
received" with consistent hydraulic boundary conditions across mechanisms.

---

## Decision

1. **Derivation route: re-execute Uemura's models, faithfully, on his own
   committed inputs.** A quarantined module
   `system_integration/uemura_models.py` reimplements P1 and P2 exactly as
   published (equation-for-equation against the 2024 paper, thesis §4.2–4.3,
   the WP2 report §4–5, and his two reference implementations), vectorized
   over MC draws, deterministic under a seeded RNG. The adapter scripts (raw
   drop → `data/processed/uemura_segments/segment_inputs.csv` →
   `data/processed/uemura_surface_curves/*.csv`) never hand-edit raw files
   and stamp per-value provenance. This is the strongest available reading
   of "as received": his models, his parameters, his input table, his
   rating, machine precision — versus digitizing 9 section-level figure
   curves that cover neither all segments nor both mechanisms.

2. **Stage-axis semantics: `stage_m_msl` = the median-rating stage.** The
   curves condition on the event's peak stage under the node's own Eq. 4.19
   rating — exactly the axis the Phase 3 hazard side produces
   (`hazard.py` peak stages come through the same rating). Uemura's
   rating-error term (his Eq. 10) stays **inside** the overflow curve as
   load-side scatter around that axis, which is precisely the thesis
   sentence "accounts for uncertainty in the stage-discharge rating curve".
   The BEP curve, by contrast, treats its conditioning stage as the realized
   water level (Phase 1 semantics). This seam is inherent to composing
   "as received" curves with engine curves and is carried as a documented
   limitation (the measured Phase 2 anchor sensitivity, close-out §2.3,
   bounds the same kind of stage-axis uncertainty at first order).

3. **Conditioning hydrograph: the production canonical d4PDF shape**
   (`HPB_m064_1987`, the ADR-0020 shape that conditioned every Phase 1/2
   BEP curve), loaded per node via verbatim M3 `load_canonical_shape` and
   scaled per level by `conditioning_record_for_level` — the same G1 rule.
   All three mechanisms are thereby conditioned on the *same* event at the
   same peak stage, which (a) realizes the thesis's "consistent hydraulic
   boundary conditions" claim, (b) makes the conditional-independence-
   given-h composition clean (the event shape is deterministic given h, so
   no shared duration randomness couples the mechanisms), and (c) fills the
   "hydrograph selected in WP3" slot Uemura's own notebook left open — his
   sine/cosine shapes were explicit placeholders. Two labeled companions
   quantify this choice: a sine-T=30 h overflow set (Uemura's published
   fragility construction, thesis Eq. 4.11) and an event-based validation
   run at the 9 section-representative KPs (ADR-0043) against the full
   ensembles.

4. **Scenario labeling: identical curves for `historical` and `+4K`.** The
   canonical-shape conditioning is scenario-invariant by construction (the
   same HPB shape drives both, exactly as in Phase 1 — ADR-0020/0023);
   climate enters Phase 3 only through the hazard side. Both scenario
   labels are carried explicitly with identical curve values so the
   ADR-0038 loader semantics are unchanged (committed as one contract CSV
   per scenario label to respect the repo's 500 KB hygiene guard; each
   file validates independently and the campaign merges them). If the event-based companion
   shows a material scenario-shape effect, that is the revision trigger for
   scenario-specific curves.

5. **Monotonicity by common random numbers.** Each (node, mechanism) uses
   one MC draw set across all conditioning levels. Both models are
   pointwise monotone in the peak stage given fixed draws (overflow: crest
   exceedance depth grows with h; scour: floodplain depth grows and the
   effective levee width shrinks with h), so the estimated `P_f(h)` is
   exactly non-decreasing — the ADR-0038 loader's monotonicity contract is
   met by construction, not by post-hoc isotonic massaging. Seeds derive
   from `numpy.random.SeedSequence(20260717, node_index, mechanism_index)`.

6. **Satsunai rating-error values: adopt the Tokachi/Obihiro pair
   (mu = 0.6 m, sigma = 0.38 m).** The WP2 notebook reads the Satsunai
   (Nantai) values from `Uncertainty_HQrelation.xlsx`, which is absent from
   the drop; no published table carries them (checked: paper, WP2 report,
   thesis §4.2 — the thesis Fig. 4.12 plots Tokachi gauges only). The
   Obihiro pair is the only measured value in hand and the two rivers share
   the provider's rating methodology. Class-D blocker entry: one workbook
   (two cells) replaces this assumption; the generator takes it as a
   parameter. Applies to the overflow curve only (his scour model carries
   no rating-error term).

7. **`Sig_bh` is used as the per-node crest standard deviation, verbatim.**
   That is what both of his implementations do (`randn * Sig + Average +
   DesignBankHeight`). The values (0.001–0.2 m) are small enough to suggest
   a standard error rather than a point sigma, but second-guessing his
   published calibration would violate "as received"; noted as a
   limitation, not corrected.

8. **Grid and coverage.** Conditioning levels per node: 0.2 m steps from
   just above the scour onset (floodplain elevation) to crest + 3 m
   (covering the crest-error and rating-error upper tails); the contract
   loader's >= 2-samples rule is satisfied everywhere. All 114 registry
   nodes get both mechanisms' curves (the drop's 3 incomplete rows lie
   outside the study reaches). N_MC = 10,000 per (node, mechanism), his
   published count.

9. **The scour k unit conversion follows Uemura's script verbatim, and the
   discrepancy is flagged as a finding.** `ErosionModel_231019.py` converts
   k = 0.021 ft^3/(lb·hr) to SI via `0.3048/0.45359237` (one linear
   ft->m factor and a pound-*mass*->kg factor). The dimensionally correct
   conversion of an erosion rate per unit *stress* (ft/hr per lbf/ft^2 ->
   m/hr per Pa) is `0.3048/47.8803`, a factor **105.6 smaller** — his
   script's erosion rate is ~106x the USACE-intended value. His published
   WP2 results (scour probabilities 1e-3–1e-2/yr, scour dominating
   overtopping) are consistent with the script's conversion having been
   used throughout; under the corrected conversion scour becomes
   negligible at these stresses and could not dominate. Because the thesis
   commits to "used as received" and this repo's discipline forbids
   overriding the source's own workproduct, the **primary curves reproduce
   the script's conversion**, a **labeled companion set**
   (`uemura_surface_curves_scour_usace_k.csv`) carries the corrected
   conversion, and the discrepancy is a top-priority owner/Uemura
   confirmation item in the Phase 3 blocker manifest. Every RQ3/RQ4
   product states which conversion its scour input used.

10. **Scour erosion-onset depth floor: 0.05 m** (regularization, found in
    execution). The USACE friction factor `f_c = 2 (2.5 ln(30 d / k_b))^-2`
    **diverges** at floodplain depth d = k_b/30 ≈ 1.6 mm (log-law
    breakdown), so an hour of cm-scale sheet flow can contribute an
    unbounded shear impulse; his script computes the same expression and
    inherits the singularity (rarely sampled in event-based runs; on the
    conditioning ladder it produced a +0.35 single-level artifact at
    Satsunai KP 3.2, caught by the contract loader's monotonicity check).
    The re-execution therefore zeroes the erosion contribution of any time
    step with floodplain depth < 0.05 m: physically, centimetre sheet flow
    does not drive lateral levee erosion (tau(0.05 m) ≈ 1 Pa versus
    tau_c ≈ 50 Pa — the floor changes nothing outside the singular
    sliver); numerically, tau(d) is on its monotone branch for
    d > 7.2 mm, so the common-random-numbers curves are exactly
    non-decreasing again. Pinned by a dedicated test; the only deliberate
    behavioural deviation from his script, and it is a strict
    regularization of an unphysical divergence.

---

## Alternatives Considered

### Alternative 1: digitize the figure curves from the thesis / WP2 report
Pros: zero model reimplementation; visually "as received".
Cons: figures exist only per section (9), only vs discharge, mostly for
overflow, at screen resolution; would not cover 114 segments x 2 mechanisms
x stage axis; every value would carry a digitization flag. Rejected.

### Alternative 2: event-based empirical curves (bin the full d4PDF ensembles by peak stage)
Pros: closest to the WP2 final report's event-based method; captures the
duration–peak correlation per scenario; per-scenario curves arise naturally.
Cons: mixes conditioning semantics with the BEP curve (canonical-shape
conditioned); binning noise at 114 nodes; and it *weakens* the thesis's
conditional-independence-given-h assumption (shared duration randomness
couples the mechanisms within a stage bin). Retained as the **validation
companion** at the 9 section KPs, not the deliverable.

### Alternative 3: Uemura's sine-T=30 h shape as the primary conditioning
Pros: literally his published fragility construction.
Cons: his own notebook marks the shape as a placeholder pending the WP1/WP3
hydrograph selection; a 30 h symmetric pulse under-represents the measured
d4PDF durations (median rise 18 h, plateau 9 h, 192 h records) that the
scour mechanism integrates over; and it would condition the surface curves
on a different event than the BEP curves they compose with. Retained as the
labeled overflow companion set.

---

## Rationale

The drop contains everything needed to reproduce Uemura's curves except the
curves themselves. Re-execution on his own inputs is the only route that
covers the full segment grid and both mechanisms at machine precision, and
every constant it uses traces to a specific cell, table, or equation in his
workproduct (`data/processed/*/provenance.md` records each). The two
companions bracket the two interpretive choices (shape, conditioning) with
computed numbers instead of argument.

---

## Consequences

* `system_integration/uemura_models.py` holds reproduced **external** model
  physics. ADR-0038's "physics-free" rule is amended in scope: it bans BEP
  engine physics from Phase 3, not the quarantined reproduction of imported
  surface-mechanism models (which must live somewhere importable and
  tested). The module never touches engine kernels.
* The contract CSVs under `data/processed/uemura_surface_curves/` are
  committed (regenerable via `scripts/generate_uemura_surface_curves.py`;
  the raw drop stays gitignored, with `data/df_river.csv` mirrored verbatim
  to `data/processed/uemura_segments/` as the committed extract).
* `python -m system_integration --surface-csv
  data/processed/uemura_surface_curves/uemura_surface_curves.csv` unblocks
  RQ3 exactly as ADR-0038 designed; the D1 manifest entry closes with the
  decision-6 residual (Satsunai rating-error workbook) as its successor.
* Validation gates before results are quoted: reference-case tests on both
  models (hand-computed damage/erosion integrals), the common-random-number
  monotonicity pin, WP2 Fig. 13 qualitative features (KP 60.8 scour dip,
  Satsunai KP 7.0/12.8/16.4 high-ground zeros), and the event-based
  companion against WP2 Tables 3/4 magnitudes (their hydrology differs;
  order-of-magnitude agreement is the bar).

---

## References

- Uemura, F., Rongen, G., Masuya, S., Yoshida, T., Yamada, T. J. (2024).
  Calculating flood probability in Obihiro using a probabilistic method.
  Proc. IAHS 386, 69–74. (In the drop.)
- Uemura, F. (2025). PhD thesis, Hokkaido University, §4.2–4.3 (Japanese).
  (`Uemura_Fumihiko.pdf` in the drop.)
- HKV / Docon (2024). Flood Risk Hokkaido, WP2 Bank failure probability,
  final report PR3983 (Curran & Uemura). (In the drop.)
- Dean, R. G., et al. (2010). Erosional equivalences of levees. Ocean Eng.
  37, 104–113. (Threshold 0.492e6, u_c table — via the paper/notebook.)
- USACE (2007). Erosion Toolbox: Levee Risk Assessment Methodology, User's
  Manual. (k, tau_c, k_b, f_c formula — via the WP2 report and script.)
- ADR-0019/0020/0021 (M3 rating, canonical shape, datum), ADR-0023 (climate
  axis), ADR-0038 (Phase 3 architecture and the arrival contract).
