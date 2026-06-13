# M7 Physics Note: Pol ODE Reference Equations and Test Values

Date: 2026-06-12 (updated 2026-06-13: digitized figure data committed; M4 datum cross-check; B25-245 C_e resolved to 0.010; tanh-l_c open question; M7 implemented and B25-245 demoted to a qualitative gate with the quantitative rate gate moved to the in-domain L = 3 m case, §4 / §5D)
Status: Reference note (pre-implementation, M7 `progression.py`). Not an ADR — no decision is taken here; this note fixes the paper-traceable equations and numbers that M7 code and tests must reproduce.

Sources (page numbers refer to the article/book pagination, not PDF pages):

- **[CG24]** Pol, Noordam & Kanning (2024), *A 3D time-dependent backward erosion piping model*, Computers and Geotechnics 167, 106068.
- **[SIE24]** Pol, Kanning, Jonkman & Kok (2024), *Time-dependent reliability analysis of flood defenses under cumulative internal erosion*, Structure and Infrastructure Engineering.
- **[T22]** Pol (2022), *Time-dependent development of backward erosion piping*, PhD thesis, TU Delft.

Convention in this note: a value is given only if it appears as **text or a table** in a source. Values that exist **only in a figure** are identified as such and are *not* quoted from the figures directly. Update 2026-06-13: every figure-only series flagged in §5 has since been manually digitized against the publisher PDFs and committed under `data/digitized/` (provenance in `data/digitized/MANIFEST.md`); digitized landmark values quoted in this note are marked *(digitized)* and are reliable to ≤2 significant figures only.

---

## 1. The progression-rate equation (coefficient 89, exponent 0.81)

**[SIE24] Eq. (5)** (identically [T22] Eq. (6.5)):

```
dl/dt = 89 · C_e · ( k · (H(t) − H_eq(l)) / L )^0.81     if I_er = true
dl/dt = 0                                                 else
```

with `C_e` erosion coefficient [−], `k` hydraulic conductivity [m/s], `H` imposed head difference [m], `H_eq` equilibrium head [m], `L` seepage length [m]; dl/dt in [m/s]. "89 and 0.81 are regression coefficients" ([SIE24] §2.3, citing [CG24]).

**Origin: [CG24] Eq. (15)** (identically [T22] Eq. (5.18)) — a regression for the *instantaneous* progression rate fitted on DgFlow finite-element simulations:

```
dl/dt(t) = 89 · C_e · ( k · (H(t) − H_eq(l)) / L )^0.81      [m/s]
```

Derivation basis ([CG24] §4.4; [T22] §5.4.4):

- Fitted on **hole-type-exit** DgFlow simulations: four base cases (sands S22 and S42; seepage lengths L = 3 m and 30 m), with variations in overloading and C_e; 31 simulations giving 3100 data points (seepage length divided into 100 segments). 80 % used for fitting, 20 % for validation; **R² = 0.94**.
- Equivalent d₅₀-based form: [T22] Eq. (5.16)/(5.17) (coefficient 1.3·10⁵, d₅₀^1.65); Eq. (5.18) replaces d₅₀ by k "with virtually the same result" (R² = 0.94). Form is Kézdi (1979)-like, extended with an overloading term and an exponent on the seepage velocity.
- Stated validity domain (for the companion average-rate regression [T22] Eq. (5.15), derived from the same simulation campaign): hole-type (localized) exits, homogeneous aquifers with **D/L = 1/3**, **0.2 ≤ d₅₀ ≤ 0.4 mm**, **2 ≤ C_u ≤ 3**, overloading up to **H/H_c ≤ 1.4**; scales spanned L = 0.9–90 m. Plane-exit cases are captured in order of magnitude only ([CG24] §4.4; deviating plane-exit configurations under-predicted by a factor 1.5–3, [T22] p. 111).
- Regression-vs-simulation scatter: [CG24] Fig. 13 / [T22] Fig. 5.15 plot 1:1 and 1:3 guide lines; individual cases deviate from the regression by up to roughly a factor 3. **Tests must not assert tight agreement between Eq. (15) and individual DgFlow table values** (see §5).

Implementation remarks (consistent with spec §3/§5 and `docs/conventions.md`):

- **Dimensional, SI-only formula.** Because the velocity group is raised to 0.81, the coefficient 89 carries implicit units (m/s)^0.19. Inputs must be strict SI (k in m/s, H and L in m); output is m/s. No unit conversion may occur inside the kernel.
- **Erosion threshold.** The papers define erosion only for H > H_eq ("a threshold below which no erosion occurs as the grains in the pipe are in equilibrium", [SIE24] §2.1). The spec's `max(0, H_erosion − H_eq)` positive-part operator is the implementation of this threshold; combined with the I_er gate it makes l(t) monotonically non-decreasing.
- The gate I_er is [SIE24] Eq. (7) / [T22] Eq. (6.6); its repo realization (flood-fighting clause omitted, Terzaghi collapse) is governed by M5 and ADR-0008, not by this note.

---

## 2. Equilibrium curve H_eq(l) and critical pipe length l_c

**Anchors — [SIE24] Eq. (11)** (identically [T22] Eq. (6.10), where H_c is written H_c,p):

```
H_eq(0)   = 0
H_eq(l_c) = H_c
H_eq(L)   = 0.9 · H_c
```

with linear interpolation between the three points. The 0.9·H_c end anchor and the straight segments are "a conservative estimate based on equilibrium curves following from the numerical simulations in Pol et al. (2024)" ([SIE24] §2.3; [T22] p. 126 referencing Fig. 5.7). Physical basis ([CG24] §4.2, Fig. 7; [T22] §5.4.2): for 3D **hole-type** exits H_eq rises to the maximum H_c at the critical pipe length and "decreases only slightly" beyond it; plane-type exits show steadily decreasing H_eq (initiation-dominated) and are *not* represented by this curve.

**Critical head H_c — [SIE24] Eq. (12)** (= [T22] Eq. (6.11)): the revised Sellmeijer 2011 model, H_c = L·F_r·F_s·F_g. Single source in this repo is M6 `sellmeijer.py`; M7 receives H_c, never recomputes it. Experimental-mean constants quoted with Eq. (12): D_r,m = 0.725, d₇₀,m = 2.08·10⁻⁴ m, C_u,m = 1.81, KAS_m = 0.498.

**Critical pipe length — [SIE24] Eq. (13)** (identically [T22] Eq. (6.12)):

```
l_c / L = (1/2) · tanh( 2 · D / L )
```

with D the aquifer depth [m]. Stated basis: "For homogeneous aquifers, this function agrees well with **2D** numerical piping model simulations such as those from Sellmeijer (2006) and Rosenbrand et al. (2022)" ([SIE24] §2.3).

> **Caution — do not cross-validate Eq. (13) against the DgFlow 3D critical length.** [T22] Fig. 5.9 caption states the DgFlow critical length for the L = 3 m, S2-2 hole-exit case is **l = 1.36 m** (l/L ≈ 0.45), while Eq. (13) with that geometry (D = L/3) gives l_c = 0.5·tanh(2/3)·L ≈ 0.29·L ≈ 0.87 m. The tanh formula is a simplified 2D-anchored proposal adopted by [SIE24] for the reliability model; the spec adopts it as-is (M6). A test pinning Eq. (13) must test the formula algebraically, not against 1.36 m.

---

## 3. Head datum of [SIE24] Eqs. (6) and (8), and where 0.3·D_bl enters

**[SIE24] Eq. (6)** (in-text in [T22] §6.2.2, p. 126):

```
H = h − h_e − 0.3 · D_bl
```

"where h is outer water level, h_e polder level at the exit point and D_bl polder blanket thickness." The imposed head difference "is reduced by a head loss over the blanket (vertical pipe) due to resistance of the fluidized sediment (e.g. Schweckendiek, Vrouwenvelder, & Calle, 2014; TAW, 1999)".

**[SIE24] Eq. (8)** (= [T22] Eq. (6.7)) — uplift limit state — and its companions:

```
Z_u(t) = D_bl · (γ_bl,sat − γ_w)/γ_w − (φ_it(t) − h_e)        (8)   [resistance − load reading; see note below]
Z_h(t) = i_c,h − (φ_it(t) − h_e)/D_bl                          (9)
φ_it(t) = h_e + r_e · ( h(t) − h_e )                           (10)
```

where φ_it [m] is the aquifer head at the inner levee toe, r_e the head response factor, γ_bl,sat the saturated blanket weight [kN/m³], i_c,h the critical heave gradient [−].

> **Sign-convention note.** The printed term order in [SIE24] Eqs. (8)–(9) / [T22] Eqs. (6.7)–(6.8) reads load-minus-resistance, which contradicts the `Z < 0` criticality tests inside the papers' own I_er definition (Eq. (7)/(6.6)). The resistance-minus-load reading is the only interpretation found to be internally consistent with the Z<0 criticality tests and is therefore adopted in ADR-0008. It was confirmed against the paper copy on 2026-06-12 and is recorded in **ADR-0008** (which also documents the repo's i_c,h = γ'_s/γ_w substitution and the resulting I_er collapse). This note quotes the confirmed reading.

**Precise datum statement.** Every head in Eqs. (6), (8), (9), (10) is referenced to **h_e, the polder surface level at the landside exit point**:

- In Eq. (6), H is the head *difference* between the outer (river/sea) water level h and the polder level h_e, both elevations above a common vertical datum (m +NAP in the papers); the absolute datum cancels in the difference, and the landside reference is the polder surface at the exit — not a ditch level, not the aquifer head at the toe.
- In Eqs. (8)–(9), the load is φ_it − h_e: the aquifer head at the inner toe *in excess of the same polder level*. Eq. (10) shows the r_e translation also pivots about h_e.
- H_eq(l) and H_c are compared directly against H (Eq. (5)) and therefore live on the same datum: head differences relative to h_e.

**Where 0.3·D_bl enters the balance.** Exactly once, on the load side of the *erosion* balance: it is subtracted from the gross head difference (h − h_e) to form the erosion-driving head H of Eq. (6), which is then compared against H_eq(l) inside Eq. (5) (and inside the H > H_eq clause of the t_uh definition). It does **not** enter the uplift load (Eq. (8)) or the heave gradient (Eq. (9)) — both use the un-reduced φ_it − h_e — and it does not modify H_eq or H_c. It is a constant head loss across the vertical crack through the blanket (fluidized-sand resistance), adopted by Pol from TAW (1999) / Schweckendiek et al. (2014); the chapters of [T22] reviewed here state it identically with the same citations rather than re-deriving the 0.3 factor.

**Verification of the repo convention (cross-checked against the implemented M4, 2026-06-13).** The implemented M4 (`hydraulics.py`) returns the **absolute aquifer head** h_aq(t) [m above datum] through the `AquiferHeadModel.step()` interface; its instantaneous kernel `translate_instantaneous` implements `h_aq = z_toe + r_e·(h_river − z_toe)`, which is Eq. (10) verbatim with φ_it ≡ h_aq and h_e ≡ z_toe (so stated in the M4 docstrings, per ADR-0007). The blanket overpressure is then formed downstream as

```
Δh_blanket(t) = h_aq(t) − z_toe      (spec §3 step b)  ≡  φ_it(t) − h_e of Eqs. (8)–(9)
```

which in the instantaneous default equals r_e·(h(t) − z_toe). When the lag form is active (`LaggedHead` / `advance_lag_state`, ADR-0004), Δh_blanket = h_aq(t) − z_toe still holds with h_aq the lag state — the instantaneous identity with r_e·(h − z_toe) is then only the steady-state limit, but the **datum is unchanged**, because the lag state is initialized and advanced in absolute head about the same z_toe. The erosion driver H_erosion(t) = Δh_blanket(t) − 0.3·D_bl (spec §3 steps c, j) therefore **shares the datum of Eqs. (6) and (8)**: heads in excess of the polder surface at the exit point, with the crack-resistance loss applied only to the erosion driver and the un-reduced Δh_blanket feeding uplift/heave. The one deliberate deviation, documented in **ADR-0007**, is that Eq. (6) uses the *untranslated* outer level h while the repo applies the r_e translation before subtracting 0.3·D_bl; in the calibration configurations of §4 below the outer water acts directly on the aquifer (r_e = 1), so the two conventions coincide there, which is what the M7 head-datum verification test must exploit.

**t_uh definitional difference (diagnostic only).** In [SIE24] Eq. (7), t_uh is the first time that uplift, heave **and erosion (H > H_eq)** co-occur (proxy for sand-boil formation), feeding the flood-fighting clause. The repo's t_uh diagnostic (spec §2, M8 output) is the first uplift+heave co-occurrence, without the H > H_eq clause, and the flood-fighting clause is deliberately omitted (spec M5). When comparing diagnostics against Pol's published event traces, the two t_uh definitions must not be conflated.

---

## 4. Calibration cases: parameters and calibrated C_e

From **[CG24] Table 1** (identically [T22] Table 5.1) plus text values as noted. The calibrated parameters are **DgFlow model calibrations**: η, w/a, i_tip,c were calibrated (small scale) on the critical condition, C_e on the pipe-length development over time; for the large-scale test only w/a and C_e were calibrated, with η = 0.4 from measured critical shear stress and i_tip,c = 1.1 translated from the measured critical gradient of 0.28 over 80 cm spacing via the secant-gradient relation [CG24] Eq. (14) / [T22] Eq. (5.14).

| Quantity | Unit | B25-245 (small-scale, loose) | FPH (large-scale) | Source |
|---|---|---|---|---|
| d₅₀ | mm | 0.228 | 0.185 | Table 1 / 5.1 |
| ρ_s | kg/m³ | 2650 | 2610 | Table 1 / 5.1 |
| ρ_w | kg/m³ | 1000 | 1000 | Table 1 / 5.1 |
| κ (intrinsic) | 10⁻¹¹ m² | 3.16 | 1.2 | Table 1 / 5.1 |
| n (porosity) | − | 0.402 | 0.383 | Table 1 / 5.1 |
| θ (bedding angle) | ° | 29.36 | 31.06 | Table 1 / 5.1 |
| μ (viscosity) | Pa·s | 0.001 | 0.00133 | Table 1 / 5.1 |
| η (White) | − | 0.3 (calibrated) | 0.4 (input) | Table 1 / 5.1 |
| i_tip,c | − | 0.9 (calibrated, 1 cm grid) | 1.1 (input, 5 cm grid) | Table 1 / 5.1 |
| w/a (pipe width/depth) | − | 25 (calibrated) | 700 (calibrated) | Table 1 / 5.1 |
| **C_e (calibrated)** | − | **0.010** (resolved — see below) | **0.014** | Table 1 / 5.1; resolution below |
| Seepage length L | m | 0.352 | 7.2 | [T22] §3.2.1 ("The seepage length L equals 0.352 m"); [CG24] §3.2.2 / [T22] p. 104 ("straight pipe length of 7.2 m") |
| Max. head difference | m | ≈ 0.063 *(digitized peak of `B25-245_head-BC_Hcorr.csv`; figure-only in the sources)* | 1.8 | [T22] Summary (text); §5C |
| k = κ·ρ_w·g/μ (derived, g = 9.81) | m/s | 3.10·10⁻⁴ *(derived; confirmed by the printed k = 3.1·10⁻⁴ in [T22] Table 3.2)* | 8.85·10⁻⁵ *(derived, not printed)* | computed from κ, μ above; [T22] Table 3.2 |
| DgFlow pipe grid Δx / timestep Δt | m / s | 0.01 / 10 | 0.05 / 100 | [CG24] §3.1.1–3.1.2 |

**B25-245 measured results and box geometry ([T22] Chapter 3, read 2026-06-13 — closes the B25-245 half of the §5C "remaining gap").** From [T22] Table 3.2 (text table, test "B25_245": D_r = 0.577, loading L1) and §3.2.1/§3.3.3 (text):

| Quantity | Unit | Value | Source |
|---|---|---|---|
| Corrected critical head H_c,corr | m | **0.054** (5.4 cm) | [T22] Table 3.2 |
| Measured critical pipe length l_c | m | **0.197** (19.7 cm) | [T22] Table 3.2 |
| Critical tip gradient i_c,tip | − | 0.43 | [T22] Table 3.2 |
| Average post-critical progression rate v_c,avg = (L − l_c)/(t_end − t_c) | m/s | **6.14·10⁻⁵** | [T22] Table 3.2, definition §3.3.3 |
| Hydraulic conductivity k | m/s | 3.1·10⁻⁴ | [T22] Table 3.2 |
| Box (sample) dimensions | m | 0.48 × 0.30 × 0.1 | [T22] §3.2.1 |
| Sand layer depth D | m | 0.1 | [T22] §3.2.1 (Fig. 3.2: D = 0.1) |
| Exit | − | 6 mm diameter hole in 10 mm acrylate cover | [T22] §3.2.1 |

These five values (L = 0.352 m, H_c,corr = 0.054 m, l_c = 0.197 m, k = 3.1·10⁻⁴ m/s, v_c,avg = 6.14·10⁻⁵ m/s) are the **verified B25-245 anchors** for the replay test. v_c,avg is independently confirmed: the digitized `B25-245_pipelength_l-exp.csv` yields (L − l_c)/(t_end − t_c) = 6.13·10⁻⁵ m/s, matching the Table 3.2 print to three figures — a mutual check on both the digitization and the l_c anchor.

Datum/measurement notes: H_c,corr is the head drop **over the sample** (measured H_c minus upstream-filter and exit losses, ≈ 6.1 and 5.6 mm at critical; [T22] §3.3.3) — the same correction convention as the digitized `H_corr (=BC)` series, so the two are directly compatible. l_c is defined as x_tip,c − x_exit, the pipe length when the head reaches H_c.

**Anchor decision for the B25-245 replay (deliberate isolation of the rate law from the l_c formula).** Anchor H_eq on the *measured* pair (H_c,corr = 0.054 m, l_c = 0.197 m), **not** on Eq. (13). Canonical l_c comparison for this box (used identically in §6): **measured l_c = 0.197 m (l_c/L = 0.56) versus tanh Eq. (13) l_c = 0.092 m (l_c/L = 0.5·tanh(2·0.1/0.352) ≈ 0.26) — a factor ~2.2 under-prediction.** Feeding the measured l_c isolates what this test is meant to exercise — the rate law Eq. (5) and the H_eq interpolation Eq. (11) — from the separate, and here clearly inaccurate, 2D tanh l_c formula Eq. (13). A replay anchored on the tanh l_c would put the H_eq peak at less than half the true critical length and conflate an l_c-formula error with a rate-law error. Eq. (13) is still tested algebraically and in isolation (§5A.3); its physical accuracy at this and field scale is raised as an open question (§6).

> **✅ RESOLVED 2026-06-13 — B25-245 calibrated C_e = 0.010; the figure caption's 0.014 is a copy-paste error from the FPH caption.** The discrepancy is real in both publications: [CG24] Table 1 and [T22] Table 5.1 give the B25-245 calibration as **C_e = 0.010** (full calibrated row, both sources: B25-232 = 0.012, **B25-245 = 0.010**, B25-248 = 0.030, FS35-238 = 0.018, FS35-240 = 0.007, FS35-242 = 0.018, **FPH = 0.014**), while the best-fit figure captions ([CG24] Fig. 5, [T22] Fig. 5.5) print "C_e = 0.014". Four independent lines of evidence resolve it to **0.010**:
> 1. The calibration *tables* are the authoritative record of the calibration result and give 0.010; the η = 0.3 and i_tip,c = 0.9 printed in the *same caption* match the table exactly, so only the C_e digit is corrupted in the caption.
> 2. [CG24] §3.2.1 calls Fig. 5 "the best-fit result for test B25-245", i.e. the table's calibrated value.
> 3. The erroneous caption value 0.014 is *identical to the FPH value* and to the FPH best-fit caption ([CG24] Fig. 6 / [T22] Fig. 5.6, also "C_e = 0.014") — a copy-paste between the two adjacent best-fit-figure captions is the most parsimonious explanation.
> 4. Digitized-fit consistency (next block): with C_e = 0.010 the plotted DgFlow l_model *under*-predicts the measured post-critical rate by a factor ~2; raising C_e to 0.014 would only increase DgFlow's rate and *worsen* that under-prediction, which contradicts 0.014 being the best fit.
>
> **FPH (large-scale) C_e = 0.014** is consistent across table and caption and is unaffected. **The B25-245 replay uses C_e = 0.010**, stated with this resolution in the test docstring.

**B25-245 is a QUALITATIVE shape-and-behavior gate; the quantitative rate-band gate lives on an in-domain case (§5D). Decided 2026-06-13 after implementing M7.** The original intent (a factor-2 rate band on B25-245) was abandoned once the scalar implementation revealed it cannot be both honest and demanding for this case. The reasoning, quantified from the digitized Fig. 5(c) (`B25-245_pipelength_l-exp.csv`, `…_l-model.csv`) and the M7 replay:

- **Measured**: v_c,avg = (L − l_c)/(t_end − t_c) = **6.13·10⁻⁵ m/s** from the digitized l_exp, matching **6.14·10⁻⁵ m/s** of [T22] Table 3.2 to three figures.
- **Pol's own calibrated DgFlow** (the plotted l_model) reaches **3.14·10⁻⁵ m/s = 0.51× measured** — his published best-fit FE model already under-predicts this box by ≈ 2× on the rate, though its *shape* fit is tight (3.8 % RMS / 6.2 % max of L).
- **Our M7 (Eq. (5) regression) reaches 2.21·10⁻⁵ m/s = 0.36× measured** at the calibrated C_e = 0.010, and **does not breach** (l stalls at ≈ 0.233 m; 71 % of the record is spent pre-critical; front-loading l_c/l_final = 0.84 vs the measured 0.55). Eq. (5)/DgFlow = 0.71×, i.e. a 29 % under-prediction of Pol's own model — squarely inside the §1 factor-~3 regression scatter, but on the slow side. The §1 hand estimate (~1.2×) that earlier justified factor-2 was wrong: it used the instantaneous **peak** overload (~0.01 m, giving the ~1·10⁻⁴ m/s peak rate the implementation confirms) as if it were the **end-to-end average**, which actually averages in the sub-threshold troughs and the non-breaching plateau.
- B25-245 sits **below** the regression's fitted scale range (L = 0.352 m vs 0.9–90 m). Eq. (5) carries the regression scatter **on top of** Pol's DgFlow calibration gap, so the honest envelope is the compound (≈ factor-3), not the factor-2 I derived last turn from the DgFlow gap alone — that was a mis-derivation.

**The decisive point — why no rate band fits.** With Eq. (5), the *caption-error* C_e = 0.014 lands at 0.59× (inside a factor-2 band), while the *correct calibrated* C_e = 0.010 lands at 0.36× (outside it). Any band wide enough to pass the correct 0.010 here would be drawn around our own output rather than Pol's data — an 8 %-margin factor-3 band is a blind gate, not a test. So B25-245 is disqualified as a quantitative rate gate **regardless of the band**, and gating absolute rate on it would be self-referential. (This does not revisit the C_e resolution: 0.010 is Pol's calibrated value, a fact about the source; the under-prediction is a fact about Eq. (5) out of domain.)

**What B25-245 *does* gate (demanding, out-of-domain-robust):** the test `test_b25_245_qualitative_shape_and_behavior` asserts (1) entry into the progressive phase (l crosses the measured l_c); (2) strict monotone non-decrease with a visible staircase (flat trough + growth peak steps); (3) shape vs the digitized measured curve restricted to what survives out of domain — no overshoot beyond 0.15·L and regressive-phase tracking within 0.18·L (the progressive-phase absolute divergence, up to ≈ 0.34·L, is *not* gated, by the reasoning above); (4) the breach threshold for this box pinned two-sided as a sharp rate-law guard — no breach at C_e = 0.020, breach at C_e = 0.022 (true transition ≈ **0.0215**, not the loosely-quoted earlier "0.028"); and (5) post-critical rate strictly increasing along the calibrated C_e row (dl/dt linear in C_e). Items (4) and (5) pin the rate-law *magnitude and behavior* without an absolute band. Trajectory curvature beyond the regressive phase remains a Step-4 diagnostic-plot check (complementary, not a substitute).

**C_e context across the sources** (for interpreting test values, not for re-litigating the ADR-0001 prior):

- DgFlow calibration on Pol's own experiments: small-scale range **0.007 < C_e < 0.030 (average 0.016)**; large-scale FPH **C_e = 0.014** ([CG24] §3.2.3 / [T22] §5.3.2). These are a factor ≈ 3–10 below the Shields-based a-priori C_e = 0.08 of [CG24] Eq. (13), attributed to the straight-rectangular-channel idealization.
- Comparing the average-rate regression against the wider historical-experiment compilation (Pol et al. 2019) gives higher values: measured rates of the 7 progression-dominated tests are a factor 3–5 above predictions with C_e = 0.016, leading to Ln(mean 0.044, σ 0.048) used in [T22] Ch. 6, updated to **Ln(mean 0.055, σ 0.043)** with all experiments ([T22] p. 112, App. E) — the latter is the [SIE24] Table 2 base-case distribution.
- The repo prior (ADR-0001: Lognormal, mean 0.014, COV 0.50) is anchored on the DgFlow-calibrated experiment values, spanning the 0.007–0.030 calibration range. Reference-case tests must use the **per-experiment calibrated C_e**, not the prior mean.

---

## 5. Quantitative outcomes usable as numerical test targets

Grouped by reliability. Only group A values support exact assertions.

### A. Exact targets (algebraic, from the quoted equations)

1. **Coefficient/exponent pinning.** One worked evaluation of Eq. (15) to guard against transcription errors (this arithmetic is derived here, not printed in the papers): with C_e = 0.08, k = 2.158·10⁻⁴ m/s (S2-2: κ = 2.2·10⁻¹¹ m², μ = 0.001 Pa·s), H − H_eq = 0.0144 m, L = 3 m: dl/dt = 89·0.08·(2.158·10⁻⁴·0.0144/3)^0.81 ≈ **1.01·10⁻⁴ m/s**.
2. **H_eq anchors.** H_eq(0) = 0; H_eq(l_c) = H_c; H_eq(L) = 0.9·H_c; piecewise-linear in between (Eq. (11)), with per-realization breakpoints.
3. **l_c formula.** Eq. (13): for D/L = 1/3, l_c/L = 0.5·tanh(2/3) ≈ 0.2914 (algebraic check; see §2 caution — not 1.36 m).
4. **Head-datum test (ADR-0007 consequence).** For a paper-configuration geometry with r_e = 1 and z_toe = h_e, the implemented H_erosion must equal Eq. (6)'s H = h − h_e − 0.3·D_bl exactly, while the uplift/heave loads remain the un-reduced φ_it − h_e. The test docstring must state the datum: *all heads in excess of the polder surface level at the landside exit point (h_e ≡ z_toe), per [SIE24] Eqs. (6), (8), (10)*.
5. **Linearity in C_e.** dl/dt is exactly proportional to C_e in Eq. (15) (and DgFlow showed approximately linear dependence, [CG24] §4.3.3) — cheap property test.

### B. Approximate targets (text/table values; assert order of magnitude or stated tolerance)

6. **FPH average progression rate.** Measured **≈ 0.3 m/hour ≈ 8.3·10⁻⁵ m/s** ([T22] Summary, text). With the §4 FPH parameters (k = 8.85·10⁻⁵ m/s, L = 7.2 m, C_e = 0.014), the Eq.-(15) trajectory's average rate in the progressive phase should match within the regression scatter (factor ≈ 3, see §1). The measured tip trajectory is now available digitized (`FPH_xtip_measured.csv`, §5C) for piecewise-rate comparison.
7. **Small-scale rate order.** Progression rates in the small-scale tests were "in the order of 0.1–1 m/hour" ([T22] Summary) i.e. ~10⁻⁴–10⁻³ m/s expected during progression ([T22] §5.3.1) — a coarse order-of-magnitude sanity band. Note B25-245's absolute rate is **not** gated quantitatively (out of domain; §4, §5D); its measured v_c,avg = 6.14·10⁻⁵ m/s is retained as a verified anchor for context only.
8. **FPH slowdown landmark.** A temporary decrease in progression rate around the critical length, **x_tip ≈ 2.95 m**, observed in both measurement and simulation ([CG24] §3.2.2 / [T22] p. 104). Qualitative target: the Eq.-(5) trajectory exhibits reduced dl/dt near l ≈ l_c (where H − H_eq pinches), not a numeric assertion.
9. **DgFlow parametric anchors** ([CG24] Tables A.4–A.6, text tables; = [T22] App. D): e.g. S22, hole exit, w/a = 20: H_c = 0.084 m (L = 0.9 m), 0.144 m (L = 3 m), 0.254 m (L = 9 m), 0.470 m (L = 30 m), 0.864 m (L = 90 m); reference progression case (L = 3 m, S22, C_e = 0.08, 10 % overload): average dl/dt = 7.08·10⁻⁵ m/s, with Δt-sensitivity 6.93·10⁻⁵ (Δt = 5 s) and 7.38·10⁻⁵ (Δt = 20 s). **Caveat:** these are DgFlow *simulation* outputs — the data Eq. (15) was regressed on, with up to factor-3 individual scatter (my §A.1 worked value of ~1.0·10⁻⁴ m/s vs the table's 7.08·10⁻⁵ m/s for nearby conditions illustrates the gap). Use as order-of-magnitude cross-checks only; the H_c values belong to M6-adjacent scale-effect discussion, not to M7 assertions.
10. **Timestep-sensitivity context.** Doubling the DgFlow timestep (5 s → 10 s) changed the average progression rate by ~2 % ([CG24] §4.3.3). Not directly transferable to our forward-Euler-on-Eq.-(5) scheme, but a reasonable expectation scale for the spec §11 Δt/2 convergence test.

### C. Digitized figure data (committed under `data/digitized/`, 2026-06-13)

All figure-only series previously flagged here were manually digitized by the user against the publisher PDFs (400 DPI render, axis-calibrated, overlay-verified) and committed to `data/digitized/`; per-file provenance is in `data/digitized/MANIFEST.md`. Accuracy ≈ 1–2 % of the relevant axis range; continuous curves were thinned and lightly median-smoothed. Usage rules for tests:

- **Trajectory/shape references only**, never asserted beyond 2 significant figures (manifest accuracy statement).
- **Clean curve-crossing artifacts before use.** The underlying physical curves l(t) and x_tip(t) are monotone non-decreasing, so non-monotonic excursions in the digitized *model* curves are digitization artifacts where plotted curves cross. Largest offenders: `FPH_xtip_model_exit13mm_wa350-700.csv` (e.g. the dips at t ≈ 23.3 h and ≈ 29.4 h) and isolated points in `B25-245_head-BC_Hcorr.csv` (e.g. the single 0.0215 m sample at t = 1554 s between neighbours at ≈ 0.041–0.046 m — H_corr is a staircase BC, not physically monotone, but a 50 % single-sample drop-and-return is a crossing artifact). Pre-clean with a running maximum (trajectories) or a median/window filter (the head BC), and say so in the test.
- The two head-profile files are committed for completeness but remain **`DO-NOT-USE`** per the digitization request; nothing may be asserted against them. (B25-245 H_c needs no digitized value anyway — the text value H_c,corr = 0.054 m from [T22] Table 3.2, §4, is the anchor.)
- The `l_exp` / `FPH_xtip_measured` series are *measured* data carrying experimental scatter on top of digitization error; they bound the replay tolerance, they do not tighten it.

Datasets and landmark values (all *(digitized)* unless noted):

- **B25-245 ([CG24] Fig. 5(c))** — `B25-245_head-BC_Hcorr.csv` (imposed head BC, right axis), `B25-245_pipelength_l-exp.csv` (measured), `B25-245_pipelength_l-model.csv` (DgFlow). Model trajectory plateaus at l ≈ 0.354 m ≈ L (breach) from t ≈ 7.5·10³ s; head BC peaks at ≈ 0.063 m (t ≈ 6.2·10³ s). This unlocks the §11-spec "Pol small-scale reproduction" replay: drive Eq. (5) with the cleaned H_corr(t) − the datum is already the head difference over the sample, r_e = 1, no further 0.3·D_bl subtraction (the BC is corrected for filter/exit losses, [CG24] §3.1.1) − with C_e = 0.010 (§4, resolved) and the §4 factor-2 rate band.
- **FPH ([CG24] Fig. 6(b))** — `FPH_xtip_measured.csv` (9 points: (≈ 0 h, 1.28 m) → (38.3 h, 7.97 m)) plus three DgFlow variant curves. Note the measured series is tip *position* with a developed pipe already at recording start (x_tip(0) ≈ 1.3 m, not 0): the M7 replay target is rate and shape (incl. the ≈ 2.95 m slowdown, §5B.8), not the absolute origin.
- **L = 3 m S2-2 ([CG24] Fig. 10 / [T22] Fig. 5.10)** — `L3m_S2-2_pipelength_l-t.csv`. H = 0.157 m and H_c = 0.143 m are caption text (§5B.9); digitized landmarks: crosses the DgFlow critical length 1.36 m at t ≈ 9.8·10³ s, breach (l = L = 3 m, digitized plateau 2.997 m) at t ≈ 3.25·10⁴ s. Order-of-magnitude target for an Eq.-(5) replay at constant H with C_e = 0.08, within the §1 factor-3 regression scatter (this trajectory is DgFlow, not the regression).
- **[SIE24] Fig. 3** — `SIE_equilibrium_simulated.csv` + `SIE_equilibrium_simplified.csv`. The digitized simplified relation breaks at l/L ≈ 0.40 with H_eq/H_c ≈ 0.99 (nominally 1.0) and ends at ≈ 0.90 at l/L = 1 — a shape check for the Eq. (11) interpolation. Caution: the figure's geometry implies l_c/L ≈ 0.4; do **not** assume D/L = 1/3 for this figure, and the first few simplified-curve points (l/L < 0.02) are visibly noisy — exclude them from any fit.
- **[SIE24] Fig. 4 (coastal base-case example)** — `SIE_coastal-example_waterlevel.csv` (left axis, m +NAP), `SIE_coastal-example_pipelength.csv` (right axis, l/L; plateau ≈ 0.075), `SIE_coastal-example_events.csv` (heave ≈ −15.0 h, uplift ≈ −13.7 h, critical head ≈ −12.0 h, intervention ≈ −3.0 h; no failure). Qualitative integration-test template for event sequencing, with two structural caveats: (i) the repo omits the flood-fighting clause (spec M5), so a repo replay keeps eroding past the intervention marker and will **not** reproduce the post-intervention plateau — by design; (ii) the heave-before-uplift marker ordering is a realization of Pol's independent i_c,h, which the repo's collapsed Terzaghi gate (ADR-0008) deliberately does not reproduce (both latch simultaneously). Use for water-level-driven shape comparison up to the intervention time only.

Remaining gap (text, **not** a digitization request): ~~the B25-245 measured critical head and box geometry~~ — **resolved 2026-06-13**, pulled from [T22] Table 3.2 / §3.2.1 into §4 above. The **FPH aquifer geometry** ([T22] Chapter 4, §4.2) remains unread, but per §5D the in-domain quantitative gate uses the L = 3 m DgFlow case, not FPH, so this gap no longer blocks M7 validation (it would only be needed for an optional FPH replay).

### D. In-domain quantitative rate gate — recommended case (decided 2026-06-13; test pending approval)

Because B25-245 is out of domain (§4), the quantitative post-critical rate band moves to an **in-domain** case. Two candidates:

| | FPH (L = 7.2 m) | **L = 3 m S2-2 DgFlow** ([CG24] Fig. 10 / [T22] Fig. 5.10) |
|---|---|---|
| Nature | large-scale **experiment** | DgFlow **simulation** |
| In Eq. (5) fitted domain? | in range, but D/L unknown | **yes — L = 3 m is a regression base case, D/L = 1/3 exactly** (§1) |
| Geometry specified? | **no** — aquifer geometry unread ([T22] §4.2) | **yes** — L = 3, D/L = 1/3, S2-2 (d₅₀ = 0.20 mm, κ = 2.2·10⁻¹¹ → k = 2.158·10⁻⁴), H = 0.157 m, H_c = 0.143 m, C_e = 0.08 |
| Published rate anchor | only "≈ 0.3 m/h" text (approx) | **exact text-table value: average dl/dt = 7.08·10⁻⁵ m/s** ([CG24] Table A.5, §5B.9) **plus** digitized l(t) (445 pts) and a Δt-sensitivity (6.93·10⁻⁵ at 5 s, 7.38·10⁻⁵ at 20 s) |
| Cleanliness | poorly reproduced (needed w/a = 700; unexplained resistance) | controlled simulation; no experimental scatter |

**Recommendation (confirmed by the user 2026-06-13): use the L = 3 m S2-2 DgFlow case.** It is the only candidate that is in-domain, fully specified (no open geometry, unlike FPH), and carries a clean published rate (Table A.5's 7.08·10⁻⁵ m/s) plus a digitized trajectory and Δt-sensitivity. FPH is disqualified for now (aquifer geometry unread; experiment fit only with the w/a = 700 hack). H_eq anchored on the **DgFlow critical length 1.36 m** ([T22] Fig. 5.9, §2), not Eq. (13)'s 0.874 m, same logic as B25-245 (§4).

**⚠ GENUINE FINDING — Eq. (5) + Eq. (11) over-predicts the DgFlow L = 3 m rate by ≈ 1.95× in-domain (verified by integration 2026-06-13, NOT a hand estimate).** Running the scalar integrator at constant H = 0.157 m, C_e = 0.08, l_c = 1.36 m gives an average dl/dt over [L/2, L] of **1.384·10⁻⁴ m/s = 1.95× the DgFlow 7.08·10⁻⁵** (digitized DgFlow over the same window = 7.25·10⁻⁵, confirming the metric). It is **Δt-converged** (1.383–1.384·10⁻⁴ at Δt = 5/10/20 s), so this is *not* the peak-vs-average artifact that fooled the §5A.1 hand estimate — that estimate (~1.0·10⁻⁴, "factor ~1.4") was the rate at the l_c pinch where overload is smallest; the phase average is higher because overload grows past l_c, so the over-prediction is **larger** than the hand value, not smaller.

**Root cause — the conservative piecewise-linear H_eq (Eq. (11)), not the rate-law coefficients.** Inverting Eq. (15) along the digitized DgFlow trajectory gives DgFlow's *effective* post-critical H_eq/H_c ≈ **1.01–1.04** (the digitized SIE Fig. 3 *simulated* equilibrium curve independently reads ≈ 0.978 over l/L > 0.5), whereas Eq. (11) falls from H_c at l_c to **0.90·H_c at L** (0.99 → 0.95 → 0.90 across l/L = 0.5/0.75/1.0). The deliberately conservative low H_eq inflates the overload (H − H_eq) by up to ≈ 2×, and through the 0.81 power inflates dl/dt by ≈ 1.8–2.2× (growing with l: 1.78× at l = 1.6 m → 2.23× at l = 2.2 m). This is Pol's **intended** conservatism (SIE 2024 §2.3 calls the 0.9·H_c anchor "a conservative estimate"), faithfully implemented in M7 — not a bug, and not a coefficient error (89/0.81 are validated exactly by the passing pinned-worked-value unit test). The l_c anchor barely matters (1.95× at 1.36 m vs 2.09× at 0.874 m).

**Modeling consequence (flag for spec §12 bias decomposition):** because Eq. (11) is conservative, M7's transient branch runs ≈ 2× faster than a DgFlow-faithful model in the progressive phase, so the transient limit state is intrinsically *more conservative* (higher P_f) than DgFlow — a designed-in conservatism that adds to, and must not be confused with, the temporal / 2D-vs-3D / head-convention components of the static-transient gap.

**The shape, by contrast, is faithful in-domain:** normalized trajectory deviation vs digitized DgFlow is **0.064 max / 0.032 RMS**, front-loading l_c/l_final = **0.45 = 0.45** (identical) — confirming the §C premise that shape survives where absolute rate does not, and the sharp contrast with out-of-domain B25-245 (0.36 dev, 0.84 vs 0.55). So S2-2 *can* carry a demanding shape gate; it is now the only quantitative progressive-phase check in M7 (B25-245's progressive phase is no longer gated), so its shape is treated as part of the gate.

**The S2-2 gate as built (`test_s2_2_in_domain_shape_and_rate`, 2026-06-14).** Two parts, with a deliberately explicit split between what is Pol-validated and what is a regression guard — so no future reader mistakes the latter for the former:

- **(1) Shape — the Pol-anchored validation.** The normalized trajectory (rate- and breach-independent) vs the digitized DgFlow l(t) must agree within **0.10** (measured 0.064). Because B25-245's progressive phase is not gated (§4), this is the **only quantitative progressive-phase validation in M7**, so it is treated as load-bearing. The rate-law coefficients (89, 0.81) are validated separately and exactly by the pinned-worked-value unit test (§5A.1).
- **(2) Rate magnitude — a documented regression guard, NOT a Pol-validated absolute rate.** The test pins the **actual integrated [L/2, L] average dl/dt = 1.3825·10⁻⁴ m/s** (Δt-converged) with a ±5 % band. *What it is:* a guard that trips if a future rate-law or H_eq change shifts the progressive-phase magnitude. *What it is not:* a claim that M7 reproduces DgFlow's absolute rate — it does not, by the ≈ 1.95× Eq.-(11) conservatism above. The **actual integrated number is pinned, not the 7.08·10⁻⁵ × 1.95 reconstruction**, so the guard stays auditable if the 1.95 factor is ever re-derived (a future editor cannot silently "fix" the 1.95 and quietly break the pin). The ≈ 1.95× is recorded as the fourth, non-temporal component of the static-transient gap in **ADR-0009** (H_eq-conservatism), which the Stage 6 bias decomposition must carry so the gap is not over-attributed to the temporal effect (the Failure Mode 4 error). Whether DgFlow's effective H_eq stays ≈ 1.0·H_c at field scale is the open question to verify with Pol (ADR-0009).

### Not M7 targets

- B25-245 computed pipe **depth** 1 mm vs measured 0.8 mm, Re ≈ 20 ([CG24] §3.2.1): a DgFlow pipe-hydraulics result; the lumped Eq.-(5) model carries no pipe-depth state. Recorded here only to document that the calibration regime was laminar.
- The FPH **recovery** observations (nine-month reload: 20 % lower critical head, 140 % higher progression rate, [T22] Summary): Phase 1 sets r_l = 0 (spec §5); relevant to the Phase 2 discussion only.

---

## 6. Open questions / to confirm with Pol

1. **Field-scale validity of the tanh l_c formula, Eq. (13).** The 2D-anchored formula l_c/L = 0.5·tanh(2·D/L) **under-predicts the critical pipe length in every 3D hole-exit case we can check against an independent number**:
   - B25-245 small-scale box: measured l_c = 0.197 m (l_c/L = 0.56) vs tanh Eq. (13) l_c = 0.092 m (l_c/L = 0.26) — factor **~2.2** (§4 canonical statement).
   - [CG24] L = 3 m S2-2 DgFlow: l/L ≈ 0.45 vs formula 0.29 — factor **≈ 1.5** (§2; [T22] Fig. 5.9 caption l = 1.36 m).

   Both exceed the formula, consistent with it being 2D plane-strain while real hole-exit erosion is strongly 3D ([T22] §5.4.2; van Beek 2015). This is **not cosmetic**: M6 uses Eq. (13) to place the (l_c, H_c) peak of the H_eq curve, so a systematic ~1.5–2× under-prediction of l_c shifts the H_eq peak landward and changes the modeled progression dynamics (the rising segment of H_eq is steeper, so the overload H_erosion − H_eq and hence dl/dt are larger over 0 < l < l_c). **To confirm with Pol:** whether the tanh l_c was ever validated at field scale (tens-of-metres L) and for 3D hole-exit geometry, or whether a 3D-corrected l_c (or a scale-dependent multiplier) should be substituted for the Tokachi sections. Until confirmed, M6 keeps Eq. (13) as specified — it is the published [SIE24] choice and changing it is a deviation requiring its own ADR — and the B25-245 replay deliberately bypasses it (§4 anchor decision). This question feeds the spec §12 failure-mode-4 scale-exponent sensitivity, which already provides a hook to vary the static-branch scaling; an analogous l_c sensitivity may be warranted.
2. **B25-245 caption C_e (closed; recorded for traceability).** Resolved to 0.010 (§4); listed here only so the publication inconsistency is not later rediscovered as a fresh issue. No action unless Pol's raw calibration logs become available and contradict the table.
