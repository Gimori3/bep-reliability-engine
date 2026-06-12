# Digitized figure data - Pol et al. BEP papers

Manual digitization of figures for thesis test-configuration assignment. Each dataset was extracted from the publisher PDFs (rendered at 400 DPI), axis-calibrated against detected tick marks / gridlines, and verified against an overlay (see `verification_overlays/`).

> **Repository note (added on commit, 2026-06-13).** Digitized manually by the project owner against his copies of the publisher PDFs; added to the repository under `data/digitized/` as reference data for the M7 validation tests (see `docs/decisions/m7-pol-ode-reference-values.md` §5C for usage rules and caveats). The `verification_overlays/` referenced above are kept local-only and are not committed. Two typos in the original manifest were corrected on commit: the CG24 author list (was "Pol, Pol et al."), and `i_up,c` → `i_tip,c` in two FPH table rows.

## Sources

- **CG24** = Pol, Noordam & Kanning (2024) *A 3D time-dependent backward erosion piping model*, Computers & Geotechnics 167, 106068.
- **SIE24** = Pol et al. (2024) *Time-dependent reliability analysis of flood defences under cumulative internal erosion*, Structure & Infrastructure Engineering.
- Thesis-figure equivalences: CG24 Fig.5(c)=thesis 5.5(c); CG24 Fig.5(a)=thesis 5.5(a); CG24 Fig.6(b)=thesis 5.6(b); CG24 Fig.10=thesis 5.10 (same L=3 m S2-2 simulation).

## Accuracy

Digitization error is approximately 1-2% of the relevant axis range (pixel/anti-alias limited). Staircase/continuous curves were thinned (~every 3rd pixel column) and lightly median-smoothed; discrete markers/circles are individual detections. Use as trajectory/shape references, not to >2 sig. figs.

## Files

| CSV | Source | Test config | Series | Columns (units) | N | Notes / caveats |
|-----|--------|-------------|--------|-----------------|---|-----------------|
| `B25-245_pipelength_l-model.csv` | CG24 Fig.5(c) (=thesis-equiv) | Small-scale exp. B25-245 | l_model(t) simulated pipe length | t_s [s], l_m [m] | 401 | left y-axis; thinned ~3px |
| `B25-245_pipelength_l-exp.csv` | CG24 Fig.5(c) | B25-245 | l_exp(t) measured pipe length (circles) | t_s [s], l_m [m] | 61 | left y-axis |
| `B25-245_head-BC_Hcorr.csv` | CG24 Fig.5(c) | B25-245 | H_corr(t) imposed head BC (dashed) | t_s [s], H_m [m] | 175 | RIGHT y-axis (0-0.1 m) |
| `B25-245_head-profile_experiment_DO-NOT-USE.csv` | CG24 Fig.5(a) | B25-245 | Head profile h(x) experiment | x_m [m], h_m [m] | 20 | ** FLAGGED DO NOT USE per request; pipe tip at x=0.322 m ** |
| `B25-245_head-profile_simulation_DO-NOT-USE.csv` | CG24 Fig.5(a) | B25-245 | Head profile h(x) simulation | x_m [m], h_m [m] | 153 | ** FLAGGED DO NOT USE ** |
| `FPH_xtip_measured.csv` | CG24 Fig.6(b) | Large-scale FPH | x_tip(t) MEASURED (circles) | t_h [h], xtip_m [m] | 9 | key validation data; last 3 pts stacked at t~38 h |
| `FPH_xtip_model_exit200mm_wa600.csv` | CG24 Fig.6(b) | Large-scale FPH (i_tip,c=1.1) | x_tip(t) model orange: exit 200 mm, k_mean, w/a=600 | t_h [h], xtip_m [m] | 188 | x-axis right border = 42 h (40-tick is interior) |
| `FPH_xtip_model_exit500mm_wa500.csv` | CG24 Fig.6(b) | Large-scale FPH (i_tip,c=1.1) | x_tip(t) model green: exit 500 mm, k_mean, w/a=500 | t_h [h], xtip_m [m] | 176 | x-axis right border = 42 h (40-tick is interior) |
| `FPH_xtip_model_exit13mm_wa350-700.csv` | CG24 Fig.6(b) | Large-scale FPH (i_tip,c=1.1) | x_tip(t) model blue+gray band: exit 13 mm (w/a=700 & w/a=350 overlap) | t_h [h], xtip_m [m] | 226 | x-axis right border = 42 h (40-tick is interior) |
| `L3m_S2-2_pipelength_l-t.csv` | CG24 Fig.10 (=thesis Fig.5.10) | L=3 m, S2-2 sand (d50=0.20mm), H=0.157 m, Hc=0.143 m | l(t) modeled pipe length | t_s [s], l_m [m] | 445 | BREACH (l=L=3m) at t=32539 s; crosses l_c=1.36 m at t=9773 s; H,Hc are constant params (not curves) |
| `SIE_equilibrium_simulated.csv` | SIE24 Fig.3 | Equilibrium model (homogeneous aquifer) | H_eq/H_c vs l/L simulated (circles) | l/L [-], Heq/Hc [-] | 35 | down to Heq/Hc~0.03 |
| `SIE_equilibrium_simplified.csv` | SIE24 Fig.3 | Equilibrium model | simplified relation (= SIE Eq.11/13, analytic) | l/L [-], Heq/Hc [-] | 240 | piecewise-linear ~(0,0)->(0.4,1)->(1,0.9) |
| `SIE_coastal-example_waterlevel.csv` | SIE24 Fig.4 | Coastal levee base case (Dp=4h, hp=6 m+NAP, l_ini=0) | water level h(t) (blue) | t_h [h], waterlevel [m+NAP] | 330 | LEFT axis |
| `SIE_coastal-example_pipelength.csv` | SIE24 Fig.4 | Coastal base case | pipe length l/L(t) (orange) | t_h [h], l/L [-] | 249 | RIGHT axis; plateau ~0.08 |
| `SIE_coastal-example_events.csv` | SIE24 Fig.4 | Coastal base case | event markers (uplift/heave/critical head/intervention/failure) | event, t_h, waterlevel [m+NAP] | 5 | t_ff between uplift(~-14h) and intervention(~-3h) |

## Key caveats

- **Fig.5(a) head profile** (`*_DO-NOT-USE.csv`): included for completeness only and flagged per your instruction not to use these.
- **Fig.6(b) FPH**: the blue (exit 13 mm, w/a=700) and gray (exit 13 mm, w/a=350) model curves overlap almost exactly and are delivered as a single band file. The x-axis right border is t = 42 h (the 40 h tick is interior), which is accounted for in the calibration.
- **Fig.10 (L=3 m, S2-2)**: H = 0.157 m and Hc = 0.143 m are constant scalar parameters (not plotted curves); the only plotted line is l(t) plus a horizontal dashed critical length l_c = 1.36 m. Breach (l = L = 3 m) at t = 3.25e4 s.
- **SIE Fig.3 simplified relation**: equals SIE Eq.(11)/(13) analytically (piecewise-linear through ~(0,0)-(0.4,1)-(1,0.9)); the CSV is the digitized trace of that line.
- **SIE Fig.4**: dual-axis. Water level uses the LEFT axis [m+NAP]; pipe length uses the RIGHT axis [l/L]. Event-marker rows give (time, water level at that event). No failure occurs in this example (l/L plateaus ~0.1 < 1).
