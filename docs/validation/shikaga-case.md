# Japanese case validation 3 (Case A): Gounokawa Shikaga L28.75k — M4/M5 separation

**Status: complete (2026-07-11). Verdict: the FEM cross-check exonerates the
M5 criterion and localizes the onset conservatism in M4. With FEM-true heads,
the weight-only Terzaghi gate is essentially unbiased at observed boiling
(FEM i_v 0.91 vs critical 0.876, ratio 1.04) — despite a lab cohesion of
40.8 kPa that demonstrably did not act. The engine's instantaneous Mazure
translation over-predicts the FEM peak toe overpressure by 1.15–1.55× here,
completing a four-point cross-case pattern (1.13× → 2.7×) that tracks
aquifer connectedness/storage state, not the ADR-0032 elastic Π. Production
judgment: NOT a Tokachi blocker — expected Tokachi M4 error is at the
well-matched end of the pattern (~1.0–1.15×), the residual bias direction is
conservative and shoulder-concentrated, and the ADR-0032 blind spot is
documented rather than triggered. One QA sensitivity run (r_e halved) is
recommended at re-sweep time.**

Source: Sako, Kurata, Mori, Nakagawa, Ohori & Kageyama (2019), 土木学会論文集
B1（水工学）75(1), 279–290 (open access; fetched to
`docs/references/sako_2019_gounokawa_75_279.pdf`). Harness:
`scripts/validate_shikaga.py` (pre-registered purpose and choices in its
docstring; results in `results/validation_shikaga/validation_results.json`);
figure: `docs/figures/validation_shikaga_m4_pattern.png`.

## 1. The case and the instrument

Gounokawa left bank 28.75k (Shikaga district), July 2018 — the same flood as
the Shimohara case, 13 km upstream on the opposite bank. Boils in the
hinterland paddies and at the landside toe (the toe replacement gravel was
ejected together with Ums sand), berm cracks; no breach. The paper models the
section with a calibrated 2D saturated–unsaturated FEM driven by the observed
flood (Kawamoto shape shifted to the local trace level) and reports the
**FEM triplet at the observed load**: hinterland i_v = 0.91 and G/W = 0.99
(the two are algebraically the same statement, verified: 18.4/(9.81·1.91) =
0.98), replacement-gravel top i_v = 1.31, block-top i_h = 0.49. This triplet
is the one instrument in the case set that measures the *heads themselves* at
a boiling site — which is what separates M4 from M5.

Anchored inputs: peak stage 31.23 m T.P. (trace, Fig. 11 inset; HWL 31.64),
hinterland ground ≈ 24.5 (Fig. 10 elevation axis), Ums cover 3.0 m
(24.3→21.3), Us-g 6.0 m (k 8.59e-5 m/s) over Usg 4.5 m (3.1e-4), Ums k
1.26e-6, γt 18.4 (all Fig. 14b table values); d70(Ums/boil family) ≈
0.35 mm (Fig. 12); L = 40 m base width (READ-OFF, 30–50); open entry (the
riverside slope is sheeted; entry through the bed into Us-g/Usg).

## 2. Results

**M5 with FEM-true heads — exonerated.** At the moment boils were observed
the FEM gradient across the Ums is 0.91 against the Terzaghi weight-only
critical 0.876: ratio 1.04, i.e. unbiased within the γt read-off. The
corollary matters as much: the Ums has a *measured* lab cohesion of 40.8 kPa
(Fig. 14b), which would forbid boiling at G/W ≈ 1 if it acted — it did not,
consistent with the trench's sand-vein/pocket fabric (Fig. 16) providing
cohesionless preferential paths. Combined with Yabe (boils at FEM G/W minima
0.65–0.88; nothing at ≥ 1.06), the five FEM-anchored instances say:
**weight-only Terzaghi with correct heads separates boiling from
non-boiling cleanly. The engine's onset conservatism does not live in the M5
criterion.** This also retires the "blanket cohesion closes the gap"
candidate from the Gounokawa F2 budget: lab cohesion is not a reliable field
resistance through vein-fabric blankets.

**M4 factor at Shikaga: 1.15× (Us-g-only) to 1.55× (composite baseline).**
Engine peak Δh = r_e·(31.23 − 24.5) = 3.14–4.22 m vs FEM 0.91·3.0 = 2.73 m.
Stable across L 30–50 and both exit datums (grid in the results JSON).

**Cross-case M4 pattern (the figure):**

| Site | M4 factor | Character |
|---|---|---|
| Yabe R11.86k | 1.13 | thick (10 m) transmissive Dg, channel-connected |
| **Shikaga L28.75k** | **1.15–1.55** | 6–10.5 m Us-g/Usg, sheeted slope, bed entry |
| Yabe R7.3k | 1.97 | thin (1.5 m) dead-ended As, floodplain-mediated entry |
| Yabe L16.10k | 2.67 | Dg under fan levee (z_toe read-off uncertain) |

The pattern tracks **connectedness and storage state** — how directly and
continuously the aquifer communicates with the channel, and how much
unsaturated/finite storage must fill during the event — not the ADR-0032
elastic Π (which passes 7.3k/16.10k yet those over-translate, and flags
11.86k which matches best). Fitting the observed damping requires an
effective storativity of order 1e-2–1e-1, i.e. partial unsaturated
participation, ~100× the elastic S_s·D_aq the diagnostic screens on.

**Full chain (secondary):** initiation fires (observed ✓); survival:
P(breach) = 0.004 (Us-g-only) / 0.15 (composite) vs observed no-breach —
consistent-to-conservative; the static comparator exceeds in 62–99% of
realizations at a surviving site, the transient branch keeps survival at
85–99.6% — the fourth Japanese data point in the static-conservatism
direction.

## 3. Production judgment (the deliverable)

**Not a production concern for the Tokachi sweep; documented as a
characterized, conservative, shoulder-concentrated validation-scale bias
with one recommended QA run.** Grounds:

1. **Expected Tokachi M4 error is small.** The four Tokachi sections are
   confined, perennially channel-connected, saturated-at-base-flow coarse
   aquifers with transmissivity 8e-3–1.6e-2 m²/s — an order of magnitude
   above Yabe 11.86k, the best-matched (1.13×) site. The over-translating
   sites are the opposite type (thin, dead-ended, floodplain-mediated entry,
   large storage deficits at flood onset). The sweep additionally initializes
   the conditioning records at base-flow stage with the aquifer in
   equilibrium, so there is no Yabe-style fill transient to mis-model.
2. **The residual direction is conservative and confined to the gate.** Since
   ADR-0027/0028, r_e drives ONLY the uplift/heave gate — neither piping
   head. An over-translated Δh opens I_er earlier and holds it open longer;
   it never inflates the erosion driver itself. Quantified bound (harness,
   `tokachi_exposure`): halving r_e moves the mean-value onset head from
   ≈1.3 m to ≈2.6–2.9 m against HWL heads of 0.9–2.8 m — i.e. even a 2×
   M4 error (well beyond the expected ~1.1×) relocates the fragility curve's
   *lower shoulder*, not its body: at conditioning levels well above onset
   the gate is open under either r_e for most of the record.
3. **The ADR-0032 blind spot is real but not triggered.** Π_elastic =
   0.002–0.012 at all four sections (instantaneous verdict stands **on the
   physics it screens**). With the Japanese-FEM-implied effective
   storativity (1e-2–1e-1) the hypothetical Π_eff would be 0.02–1.3 — but
   that storativity scale belongs to initially-unsaturated/dead-ended
   systems, which no Tokachi section is. Recommendation: an ADR-0032
   companion amendment noting the screen's scope (elastic leaky-confined
   response only; does not detect unsaturated/finite-fill damping; verify
   channel-connected saturated initial state per section — all four confirmed
   by the OYO logs' confined-section classification). Document-only.
4. **Recommended QA run:** one r_e-halved sensitivity sweep member on the
   governing section (KP58.8) at the next production re-sweep, to convert
   point 2's bound into a measured ΔP_f on the shoulder. Not blocking.

## 4. Cross-case threads (synthesis inputs)

* **No discrete pipe, three for three (standalone finding).** Gounokawa
  Shimohara (trench: veins/clod, no pipe at the erodible interface), Tokoro
  (test pits: networked sand-filled cracks, no water path), Yabe (fines-
  washout cavities; excavation found no pipe remnant). Across every
  well-investigated Japanese site in this set, the field object is a
  vein/crack/cavity system, not a discrete Sellmeijer/Pol pipe. The Pol
  abstraction earns its keep as an **effective rate model** — which it does
  well (Yabe timeline) — and this is exactly why the l ≥ L/2 structural
  proxy is the honest breach endpoint and why pipe-morphology observables
  (trench nulls) can only weakly constrain l.
* **C_e out-of-sample direction (logged for Phase 2).** The single observed
  initiation-to-breach interval (Yabe) sits on the *fast* side of the
  ADR-0026 prior (upper tail at committee-central k, centred at the coarse-
  pathway k). Phase 2's survival-driven filtering will pull C_e *down*; the
  one breach observation pulls the other way. No recalibration on one event
  — but the Phase 2 discussion should cite this as evidence the prior's
  width is carrying real, needed mass at the fast end.
  (See `docs/validation/yabe-case.md` finding Y2.)

## 5. Limitations

The FEM benchmark is one deterministic model (case 3) of a section the
committee itself modeled with parameter ladders elsewhere; D_Ums = 3.0 m is a
figure read-off and the FEM Δh benchmark is linear in it; the loading shape
is approximate (peak exact, timing from Kawamoto) — irrelevant for the M4
factor (peak-based) and onset arithmetic, mildly relevant for P_breach; the
Shikaga M4 factor range straddles the aquifer-variant choice (Us-g vs
composite), reported as a range rather than resolved; the Tokachi exposure
argument is an engineering-judgment transfer along the observed pattern, not
a Tokachi-site FEM comparison (none exists).

## 6. Reproduction

```powershell
python scripts/validate_shikaga.py        # <1 min
python scripts/plot_validation_shikaga.py # writes the PNG
```
