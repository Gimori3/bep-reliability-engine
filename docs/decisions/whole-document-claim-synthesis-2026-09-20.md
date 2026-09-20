# Whole-document scientific claim synthesis

Date: 2026-09-20. Evidence baseline: engine 7c9603457e7bceca60384bc496f7b20f4747d65d; thesis deb075797efbba5109512f01d4912fa462685e8a, with intermediate synthesis incorporated by the owner in 171d376f7406a8b7e79625ff31bd4f4c28bc0629 and ed780d55efaca5afb93c5f20fa961d885514263b.

This interpretation companion changes no physics, priors, defaults, samples, seeds or production arrays. It supersedes the specific universal claims below, not the measurements in the cited companions. Scientific conclusions remain conditional on the matrix scenario, physical seepage length, conductivity prior, omitted drainage, canonical hydrograph and partial mechanism coverage.

## Metric cancellation and comparator attribution

For positive branch probabilities, B = ps/pt and delta beta = Phi^-1(ps) - Phi^-1(pt). Between two settings B is invariant exactly when ps'/ps = pt'/pt. Delta beta is invariant exactly when the two indices change equally. Parameter-path counts prove neither condition. A distinct-path counterexample is ps(x)=2x, pt(x)=x for 0<x<0.5: B is identically two. A shared resistance input need not induce equal relative changes in two different limit-state probabilities.

This supersedes the necessity assertion in metric-and-decomposition-study.md section 1 that cancellation requires one shared channel and no other channel. Its measured model-factor departures of 1.07 to 1.22 in B and 0.166 to 0.273 in delta beta remain evidence of approximate ratio cancellation only. Components of a telescoping comparator ladder depend on order; its total does not. Equal-head retention of 63 to 83 percent applies to the three resolved design anchors; KP57.4 supplies an at-most 66 percent retention because its original denominator is a bound.

The same study's four 'contingency cells' are four marginal failure counts (baseline static/transient and arm static/transient). scripts/metric_decomposition_study.py::_displacement_ci forms them by multiplying the 16-pattern counts by the indicator matrix. The legacy min_cell_failures field names the smallest marginal count; its calculation and the thirty-failure gate are unchanged.

## Survival information and physical qualifications

Bayes gives pi(L|S) proportional to pi(L) P(S|L), even when L was sampled independently of the other parameters. Prior Sobol total effects quantify output variance, not irreducible posterior Var(L). survival-information-and-nesting-study.md and its evidence support weak measured updating and the evaluated future-survival grid, not a universal information ceiling.

Under a shared critical-head barrier and nonnegative crack resistance, the continuous transient failure set is nested in the static failure set. Finite forward Euler can jump that barrier even in exact arithmetic. Production containment is therefore a checked numerical result, not an unconditional consequence of the discrete algorithm. Containment does not imply the transient survival posterior contains no information about progression parameters.

Protective drainage can shrink the failure set with other inputs fixed. Set inclusion bounds rejection counts, not arbitrary conditional means or variances: deleting a subset can move a mean either way. Undrained posterior shifts are scenario-conditional, not upper bounds on real parameter shifts. Similarly, zero recovery bounds retained pipe length against reset-only alternatives; it does not bound risks from all omitted degradation mechanisms.

The uplift resistance term is submerged blanket weight per area, proportional to thickness. The uplift margin also subtracts pressure loading, which depends on thickness through the hydraulic response. Holding that pressure fixed clarifies the direct effect; it is not the complete cross-section comparison.

## Climate, dependence and field evidence

For long-stratum frequency w and conditional probabilities pL,pS, P = w pL + (1-w)pS. The climate ratio is sL RL + (1-sL)RS, with sL the historical long-stratum contribution share and RL, RS the warming/historical ratios of the respective annual contributions (frequency times conditional probability), not conditional-probability ratios alone. Production annualization evaluates peak-indexed fragility using one canonical shape. Duration and clustering classify the hazard; they are not independently varied causal fragility inputs.

Similar marginal normalized-shape statistics do not establish identical joint distributions of peaks, shapes and failure-relevant load trajectories. Nor does a shorter median duration impose a pointwise hydrograph ordering. The measured alternate-shape effect at equal peak therefore cannot prove either zero differential climate bias or a universal conservative sign for the climate ratio. This supersedes section 7 of climate-attribution-and-composition-study.md to that extent. The shared-shape experiment and its exact mixture decomposition remain useful conditional results.

For fixed marginal mechanism probabilities, Frechet bounds separate residual dependence from physical coupling that changes the marginals. Shared exposure does not prove positive residual dependence after conditioning. The non-breach calculation additionally assumes complete event ascertainment and stationary independent years conditional on a fixed annual probability. Its binomial exclusion limit is conditional on those assumptions. Jensen's inequality for persistent uncertain p remains valid under that conditional-year model; neither it nor the historical compatibility calculation validates absolute field probabilities.

## Bootstrap occupancy and figure scope

The corrected warming bootstrap samples 15 members within each of six fixed patterns. One carrying member is omitted with probability (14/15)^15 = 0.355264; the historical 50-member value is (49/50)^50 = 0.364170. With mg carrying blocks among Kg in pattern g, omission of all carrying blocks is the product of (1-mg/Kg)^Kg, bounded above by exp(-sum mg). The existing twenty-block floor remains conservative; pooled K=90 is not this sampling design.

The right panel of epistemic_vs_statistical.png uses _knob_departure in scripts/hwl_bias_resolution.py, taking max_resolved_departure_factor over the full computed grid in epistemic-bracket-synthesis.json. These are statistically resolved departures, without an attainable-stage or thirty-failure restriction. Its KP57.4 L bar (10.7196) is not the restricted, quotable L range of 1.02 to 3.22. The thesis caption now states the different scope; no raster or array is relabelled as a new run. The left panel retains its explicit adequate-count band and its separate sampling size.

## Dependency boundary

These corrections change interpretation and captions only. Persisted fragilities, posteriors, annualized outputs, statistical intervals and figure rasters are invariant because none of their input data, executable drivers or parameters is changed. Historical evidence is preserved, with the dated supersession pointers below. Layout and thesis-wide source validation are recorded separately in the delivery evidence, not inferred from historical page counts.

## Primary-source and remaining echo checks

Zethof et al. (2023), *Continu Inzicht WBI+: Definitief Eindrapport*, PR3959.92, appendix C, printed pages 51 to 53, defines the approximation PA by integrating the unupdated fragility only above the survived level. The updated CDF (F(h)-F(hobs))/(1-F(hobs)) is no greater than F(h), so integration establishes P(F|survival) <= PA <= P(F) within that static threshold model. PA is not the peak-conditioned posterior itself. Appendix C now defines it accordingly, retaining the citation key and inequality.

The foreland-credit companion section 6.2 reports no rejected realization under either credit arm; that explains equal prior/posterior arm values. It does not establish identity between the credited and survival-rejected sets. ADR0050's static invariance is relative to the corresponding berm geometry for gradient-relief changes; changing the berm length moves both branches. These distinctions are now explicit in the appendix summaries.

The independence assumption used for Sobol analysis is the sampling model, not a conclusion established by six paired specimens. A decomposition in independent copula-generator coordinates is a decomposition in those coordinates; it is not an unqualified set of indices for the correlated physical inputs. Field compatibility, prior-variance allocation and generator-coordinate sensitivity remain separate estimands.

The historical gradient-check description does not establish a blanket-uplift verification. Current covered-layer guidance explicitly specifies a weight-to-uplift check, so the thesis no longer claims that neither framework includes it. A damaged drain also need not equal an absent drain or restore pre-remediation berm geometry; the undrained model is not a direct measurement of such a damaged structure.
