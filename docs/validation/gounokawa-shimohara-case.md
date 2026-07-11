# Japanese case validation 1: Gounokawa right bank, Shimohara district (2018/2020/2021)

**Status: complete (2026-07-11). Verdict: initiation gate ~2.3x conservative under the
mechanistically correct pressure path; erosion/resistance sub-models consistent with
survival only when parameterized on the erodible sand layer, not the pressure-carrying
gravel; the single-k_aq aquifer schematization is the decisive model choice in a
layered (sand-over-gravel) foundation.**

Sources: Okamura, Mori, Ishihara, Maeda et al. (2025), *Soils and Foundations* 65,
101656 (open access); Waseda companion dataset doi:10.20556/0002006234 (in
`data/digitized/Gounokawa_River_Levee_Okamura/`). Harness:
`scripts/validate_gounokawa_shimohara.py` (results in
`results/validation_gounokawa/validation_results.json`); figures:
`scripts/plot_validation_gounokawa.py` -> `docs/figures/validation_gounokawa_*.png`.
The harness is standalone: it never touches `configs/` or the generator, and drives
only frozen public APIs (M2 `sample_theta`, M4 kernels, M6 vectorized Sellmeijer, M7
`integrate_progression`, M8 `evaluate_realization`/`evaluate_batch`). Two built-in
fidelity guards passed on every run: the analytic onset stage brackets the engine's
own `t_uh`, and `evaluate_batch` reproduces the harness-derived failure flags
bit-identically on a 2,000-row subsample per configuration.

## 1. The case and its observables

A 9 m levee (crest ~T.P. 23.4 m, base width 75 m) on the Gounokawa River, Shimane,
protecting a mountain-bounded pocket of paddies at T.P. 12.9-14 m. Foundation:
~0.4 m cultivation clay + 4-6 m silty sand (blanket; 3.1 m at the trench), over 1-3 m
sand, over thick gravel that crops out in the riverbed (open entry). Three floods
produced large sand ejecta at four fixed locations along the toe; **no breach**. A
December 2020 trench under the largest volcano found **no BEP pipes** at the
silty-sand/sand interface; grain-size forensics attribute most ejecta volume to
**suffusion of the gap-graded gravel** (Kenney-Lau H/F = 0.5) - a mechanism outside
this engine, so ejecta volumes and recurrence dynamics are *not* validation targets.

Observables used (2018 = virgin state, the quantitative core):

| # | Observable | Value | Provenance |
|---|---|---|---|
| O1 | Onset head at first sand ejection | site stage 19.5-19.9 m T.P. = dH 6.6-7.0 m over ground (12.9 m); 6.2-6.6 m in the paper's pond datum | Eyewitness window 05:30-05:54 JST 07-07; paper sec. 3.4; dataset stages |
| O2 | No-initiation bound | virgin onset dH > 4.23 m | Dataset Fig. 4: largest pre-2018 stage (1999, Tanijugo 16.73 + 0.4 site offset) with **no ejecta ever reported** ("the 2018 event was the first") |
| O3 | Survival | no breach, 3 events | Paper throughout |
| O4 | Trench null | no pipe at the erodible interface; vein/clod complex in the blanket within ~3.4 m of the crater | Paper sec. 4.3, Figs. 15-16 |
| O5 | Re-ejection at declining heads | dH 6.4 -> ~5.8 -> ~5.0 m | Paper Fig. 9 (2020/2021 contaminated by sheet pile + established pathways) |

O2 is this note's addition: it converts the paper's "2018 was the first event" plus
the dataset's annual-maxima series into a hard lower bound on the virgin onset head,
and it is immune to the "surface ejecta lag behind base rupture" objection because
the 1999 stage was sustained and no ejecta *ever* appeared.

Datum note: the paper's dH 6.2-6.6 nets the river against the ponded paddy (~T.P.
13.3); against dry ground (12.9, the primary engine datum per the approved design)
the same observation is 6.6-7.0. Both bands are carried everywhere.

## 2. Inputs and assumptions

Hydrographs: hourly Tanijugo stages for all three events from the companion dataset
(+0.40 m site offset), alignment verified against three paper anchors (peak 19.567 at
07-07 06:00; 12.9-crossing 20-21h 07-06; 8 h >= T.P. 19). Resampled to 225 s
(ADR-0030 hook). The ADR-0032 diagnostic on the 2018 record gives Pi = tau_aq/T_rise
= 0.002-0.009 (corner90 <= 0.025) << 0.1: the instantaneous M4 form is justified here
too.

READ-OFF values (digitized from paper figures, NOT in the dataset - the dataset
contains no grain sizes or permeabilities): k_gravel 3e-2 m/s, k_sand 5e-4 m/s, k_bl
3e-6 m/s (Fig. 2d band centres); d70_sand 0.35 mm (Fig. 17). ASSUMED: gamma'_bl 7.5
kN/m3; D_gravel 8 m (borings end in gravel). D_bl 3.1 m (trench). CoVs carried from
the thesis prior table (stated assumption); C_e keeps the ADR-0026 prior. L: the
75 m base width vs the ~150 m implied by the paper's Fig. 9 dH/L axis is unresolved
by the dataset (the DEM is a 34 x 41 m patch); per the approved design L = 150 m
(hydraulic, entry at the riverbed-gravel contact) is baseline and 75 m the
sensitivity. z_toe = 12.9 m primary, 13.3 m (pond) sensitivity. `foreland_open=True`
(documented gravel-riverbed connection - the first physically-grounded use of the
ADR-0025 open-entry path). N = 1e5 LHS, seed 20260711, two-population coupling.

**Aquifer schematizations (the central axis).** The engine has one k_aq driving M4
(lambda_in, r_e), M6 (F_s via kappa^(1/3)) and M7 (dl/dt ~ (k_aq * overload / L)^0.81).
The foundation has two candidate layers. Four schematizations:

| Name | k_aq | D_aq | d70 | Reading |
|---|---|---|---|---|
| framework_gravel | 3e-2 | 10 m | sand | ADR-0012 framework analog, gravel everywhere |
| single_soil_sand | 5e-4 | 2 m | sand | erodible layer is the whole aquifer |
| composite | 2.4e-2 | 10 m | sand | transmissivity-weighted (collapses to the gravel pole) |
| hybrid_gravel_pressure | M4: gravel/10 m; M6+M7: sand/2 m | | sand | pressure via gravel, erosion via sand (harness-level; added after round 1 - see sec. 4) |

## 3. Results

Tier 2 (N = 1e5, 2018 record, z_toe = 12.9). Onset quantities are analytic
(gate-exact under the ADR-0008 collapse); l_e and flags from the M7/M8 kernels.

| Schematization | L | r_e (med) | H_c (med) | onset dH med [5-95%] | P(onset>4.23) O2 | P(onset in O1 band) | P_breach | P(static exceeded) | l_e med |
|---|---|---|---|---|---|---|---|---|---|
| framework_gravel | 150 | 0.79 | 2.6 | 3.0 [2.3-4.0] | 0.025 | 0.000 | **0.92** | **1.00** | 150 (breach) |
| framework_gravel | 75 | 0.88 | 1.4 | 2.7 [2.0-3.5] | 0.004 | 0.000 | **1.00** | **1.00** | 75 (breach) |
| composite | 150 | 0.77 | 2.8 | 3.1 [2.3-4.1] | 0.037 | 0.000 | **0.87** | **1.00** | 150 (breach) |
| composite | 75 | 0.87 | 1.5 | 2.7 [2.0-3.6] | 0.005 | 0.000 | **1.00** | **1.00** | 75 (breach) |
| single_soil_sand | 150 | 0.18 | 15.2 | 13.4 [8.3-22.3] | 1.000 | 0.005 | 0.000 | 0.000 | 0.0 |
| single_soil_sand | 75 | 0.30 | 8.1 | 7.9 [5.2-12.5] | 0.994 | 0.078 | 0.001 | 0.247 | 0.0 |
| hybrid | 150 | 0.79 | 15.2 | 3.0 [2.3-4.0] | 0.025 | 0.000 | 0.000 | 0.000 | 0.80 |
| hybrid | 75 | 0.88 | 8.1 | 2.7 [2.0-3.5] | 0.004 | 0.000 | 0.001 | 0.247 | 1.50 |

Tier 1 (mean-theta) agrees throughout; the mean hybrid row initiates at t = 114.9 h
(07-06 23:52), 5.6 h before the eyewitness window, at stage 15.9 vs observed
19.5-19.9. Pond-datum sensitivity shifts every onset stage up by only 0.4 m. The
2020/2021 records change nothing structural (virgin onset is stage-threshold-only).

Figures: `validation_gounokawa_hydrograph_2018.png` (record vs onset bands),
`validation_gounokawa_onset_intervals.png` (the schematization axis vs O1/O2).

## 4. Findings

**F1 - the single-k schematization is decisive, and both single-soil poles fail.**
The gravel-k poles (framework, composite) are falsified in *both* directions: onset
entirely below the 1999 no-ejecta bound (P(O2) <= 0.04), and near-certain breach plus
certain static exceedance in 2018 against an observed survival (O3). The sand pole
survives O2/O3 but only by breaking the pressure mechanism: r_e ~ 0.18-0.30
contradicts the paper's field-established gravel-fed pressure propagation, and at
L = 150 m it also fails O1 in the opposite direction (predicts essentially no
initiation at a load that visibly boiled: P(init) = 1.3%). Its apparent onset
agreement at L = 75 m (median 7.9 vs 6.6-7.0 observed) is two errors cancelling -
under-translated pressure compensating an under-resistant gate.

**F2 - with the pressure path right, the initiation gate is ~2.3x conservative.**
The hybrid keeps the field-confirmed gravel pressure path (r_e ~ 0.79-0.88) and then
shows the M5 gate (Terzaghi threshold on the r_e-attenuated head) opening at median
dH 2.7-3.0 m - factor 2.2-2.5 below the observed 6.6-7.0 m, and below even the 1999
bound with probability ~0.97. This is the sharpest quantitative result of the case:
**in this high-transmissivity, gravel-fed setting the engine's initiation onset is
biased low by a factor ~2.3, and the bias sits in the exit-resistance side of the
gate, not in the schematization choice** (it persists across every schematization
with a credible r_e). Budget for the ~2.9 m missing resistance (at the blanket base,
median r_e 0.79: observed ~5.3 m vs Terzaghi 2.37 m):

- Pond surcharge (paper datum): ~0.4 m. Modeled-out by design (z_toe = 12.9 primary).
- Blanket cohesion + finite-diameter exit: the measured 2-5 kPa unconfined strength
  gives s_u ~ 1-2.5 kPa; a plug of diameter d resisting by perimeter shear adds
  ~4 s_u D_bl / (gamma_w d) = 1.0-2.5 m (d = 1 m) to 2.5-6.3 m (d = 0.4 m, the
  observed exit diameter). **This alone can close the gap for sub-metre exits.** The
  1D infinite-strip uplift balance has no scale; real breakthrough is a 3D plug/crack
  problem in a cohesive blanket.
- Lateral drainage: Location A sits ~25 m from the Yourotani channel; a lateral drain
  the 1D Mazure section cannot see lowers the true toe head (real r_e < modeled).
  Countervailing: the mountain-blocked landward boundary raises it. Net unquantified
  in 1D. **Cross-site theme:** the same finite-hinterland violation was found
  independently at Tokachi KP57.4/KP62.0 (sluice/culvert within one leakage length).
- Ejecta-vs-rupture definitional lag: real, but bounded by O2 (1999: sustained stage
  1.9 m above the predicted onset, no ejecta ever).

**F3 - resistance and erosion must come from the erodible layer.** H_c built on
gravel k is 1.4-2.8 m (certain static failure, near-certain transient breach);
on sand k it is 8-15 m and both branches are consistent with three survivals. The
Sellmeijer/Pol k is not "the aquifer's k" in a layered foundation - it is the k of
the layer whose grains erode. Using the pressure-carrying layer's k in F_s and in
the dl/dt velocity group wildly over-predicts both. This extends the ADR-0012
two-population logic across modules: framework k belongs to M4, matrix/erodible
properties to M6/M7. For Tokachi this is directly actionable wherever the OYO logs
show coarse framework over/around the eroding matrix.

**F4 - trench null vs predicted stalled pipe: marginal, not decisive.** The hybrid
predicts a stalled equilibrium pipe of median 0.8 m (L = 150) to 1.5 m (L = 75)
(96% of realizations > 1 m at L = 75). The trench found no pipe at the interface but
did find a sand-clod/vein complex within ~3.4 m of the crater in the blanket above
it. A decimetre-to-metre stalled pipe is not clearly excluded by one 9 m trench dug
two years and one remediation later; a 5-10 m pipe would have been. Verdict:
compatible-to-mildly-overpredicting; the observation lacks the power to separate.

**F5 - re-ejection memory (O5) is outside the engine's memory model - expected,
now documented.** Under the ADR-0008 collapse the re-initiation threshold is
`heave_now` only: the engine predicts an *unchanged* onset head across events, while
the field re-ejected at 6.4 -> 5.8 -> 5.0 m despite a sheet pile installed to *lower*
heads. The declining threshold is blanket-pathway memory (the trench's vein/clod
system re-used as the exit), a different state variable from the pipe length l the
engine retains (r_l = 0). Directionally both express no-healing; mechanistically the
engine cannot reproduce O5 and should not be tuned to.

**Static-vs-transient bias, Japanese data point:** at the hybrid L = 75 m
configuration the static branch exceeds in 24.7% of realizations against three
observed survivals, while the transient branch breaches in 0.13% - a ~190x per-event
gap in the direction of the thesis hypothesis (static conservatism), though a single
survival cannot make this quantitative.

## 5. Limitations

Read-off inputs (k bands, d70, D_gravel, gamma'_bl) carry figure-digitization
uncertainty - the k_gravel and D_bl values matter most for F2's factor (a +-50%
k_gravel band moves the hybrid median onset by ~0.2 m; D_bl 3.1 -> 5 m moves it
+1.6 m to ~4.6 m, still ~1.5x below observed). L remains ambiguous (150 vs 75 m) but no
finding flips across it. gamma'_p stays at the basin default 16.87 kN/m3 (no site
value). The hybrid is a harness construct, not an engine mode; making it one would
need a second conductivity in theta or a config-level split (a candidate ADR if the
Tokachi sections warrant it). Suffusion (the dominant observed ejecta mechanism) is
unmodeled by design; all comparisons above are BEP-side only.

## 6. Reproduction

```powershell
python scripts/validate_gounokawa_shimohara.py   # ~2 min, writes results JSON
python scripts/plot_validation_gounokawa.py      # writes the two PNGs
```
