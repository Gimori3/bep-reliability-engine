# Stage 6 Reference-Anchor Status (owner extractions wired / dispositioned)

Date: 2026-07-07. Analysis only — no engine physics changed, no sweep. Every
published value below was read by the owner from `docs/references/` and
independently confirmed against the PDF print during this pass (page images
rendered and read, not OCR-trusted). Reproduced values are live engine output.

## Status table

| # | Anchor | Disposition | Reproduced vs published | Margin / tolerance |
|---|--------|-------------|--------------------------|--------------------|
| 1 | Sellmeijer IJkdijk H_c | **CLOSED** (real external anchor; repo mis-cites the table) | eng 2.067 / 2.011 / 2.067 m vs obs 2.30 / 1.75 / 2.10 m | −10.1% / +14.9% / −1.6% |
| 2 | Pol dl/dt constants (89, 0.81, unit basis) | **CLOSED** (print-confirmed) | 89, 0.81, k[m/s]·H[m]/L[m] | exact match to SIE Eq (5) / CG24 Eq (15) |
| 3 | B25-245 progression magnitude | **OPEN** (target published, check not clean) | eng v_c,avg 2.21e-5 vs obs 6.14e-5 m/s | 0.36× (inside factor-3 band, at edge) |
| 4 | Head-datum (0.3·D_bl on which head) | **OPEN** (self-reference cannot be removed) | eng = Eq(6) at r_e=1 only; deviates by r_e otherwise | — (modeling choice, ADR-0007) |
| 5 | Mazure / Model-4A r_e | **CLOSED** (closed-form, unchanged) | λ_in 200.0, r_e 0.8 exact | machine precision |

## 1. Sellmeijer IJkdijk H_c — CLOSED (with a citation correction)

**Real published anchor found.** The observed critical heads live in **thesis
Table B.1** (Appendix B "Progression rates from previous laboratory
experiments", printed p.202), caption *"Progression rates in previous
experiments [Pol et al., 2019]. Sources: ... [2]=Sellmeijer et al. [2011]"*.
The three IJkdijk rows: `ijkdijk1 L=15 d70=0.180 k=8.0e-5 H_c=2.30 v=5.1e-5`,
`ijkdijk2 ... d70=0.260 k=1.4e-4 H_c=1.75 v=1.2e-4`, `ijkdijk3 ... H_c=2.10
v=6.7e-5`. These are experimental critical heads compiled by Pol, attributed
to Sellmeijer 2011.

- **The check was never self-referential**: the engine's formula-[6] output
  is compared against these externally-published observed H_c, not against
  its own path. It reproduces them at −10.1% / +14.9% / −1.6%.
- **Formula form and constants confirmed against the print** (formula [6],
  p.1146, read visually): F_R = η·(γ'_p/γ_w)·tanθ·(RD/RDm)^0.35·(U/Um)^0.13·
  (KAS/KASm)^−0.02; **F_S = d70/∛(κL) · (d70m/d70)^0.6** (cube root; the 0.6
  exponent applies ONLY to the d70m/d70 ratio); F_G = 0.91·(D/L)^[0.28/((D/L)^2.8
  −1)+0.04]. All match the engine.
- **The extraction's "F_S cancels d70" flag is a MISREAD, resolved in the
  engine's favour**: the extractor read a square root and put the whole
  bracket under ^0.6, which would cancel the case d70. The print shows a cube
  root and the exponent on the ratio only, so d70 does NOT cancel — the engine
  is correct. (Reported because the extractor explicitly asked for an
  independent check.)
- **Implementation cross-check**: the engine's formula-[6] output (2.07/2.01/
  2.07) also matches Sellmeijer's OWN formula-[6] prediction (his turquoise
  line, extractor-digitized at ~2.1/2.2/2.1) within figure-read precision —
  so our code computes Sellmeijer's rule correctly, and the ~10% gap to
  observed is Sellmeijer's model's own documented imperfection, not ours.

**Tolerance honesty.** The paper gives NO numeric tolerance for the IJkdijk
fine-sand tests (1, 3) — only "agree quite well". The only paper-stated bands
are the small/medium-scale regression scatter (13.2% / 13.4% / 13%) and the
**explicit "test 2 coarse sand deviates by 25%"** (p.1152/1154). So: case 2
passes a **paper-stated** 25% (+14.9%); cases 1 and 3 pass the ~13% small-scale
scatter **applied by extension** to large-scale fine sand (the paper does not
authorise this specific band). Margins are what they are; the fine-sand
tolerance basis is extrapolated, stated here so it isn't mistaken for
paper-fixed.

**Two findings to correct (no value change, no physics change):**
1. The test docstrings cite *"Pol (2022) thesis Appendix A, Table A.3"* — that
   table is the **Strijenham failure case**, not IJkdijk. The correct
   citation is **thesis Table B.1** (Appendix B). The values were right;
   the pointer was wrong.
2. `D_aq` is NOT in Table B.1. The repo's 3.00 m (cases 1, 3) matches
   Sellmeijer §7.1's "3 m deep pit"; the **2.85 m for case 2 is unsourced**,
   but its effect is negligible (D_aq 2.85→3.0 shifts H_c by only −1.17%,
   2.011→1.987 m — still +13.5% vs observed, inside 25%).

## 2. Pol dl/dt constants — CLOSED

Read from **SIE 2024 Eq. (5)** (p.4, visual): `dl/dt = 89·C_e·(k·(H−H_eq)/L)^0.81
if I_er, else 0`, with *"k hydraulic conductivity [m/s], H imposed head
difference [m], ... L seepage length [m], 89 and 0.81 are regression
coefficients"*. Identical to CG24 Eq. (15). The coefficient **89**, exponent
**0.81**, and the **unit basis** (k in m/s, H and L in m, so the velocity
group k·ΔH/L is m/s and 89 carries the implicit (m/s)^0.19) all match the
engine's `POL_RATE_COEFFICIENT` / `POL_RATE_EXPONENT` / `velocity_group`
exactly. The worked-value arithmetic (89·0.08·(2.158e-4·0.0144/3)^0.81 =
1.01e-4 m/s) is deterministic given these print-confirmed inputs. Not
self-referential: the constants come from the paper, not the engine.

## 3. B25-245 progression magnitude — OPEN

**Target confirmed published**: thesis **Table 3.2** (printed p.47), row
`B25_245`: D_r 0.577, Load L1, k 3.1e-4, H_c,corr 5.4 cm, l_c 19.7 cm,
i_c,tip 0.43, **v_c,avg 6.14e-5 m/s** — a held source, matching the repo.

**Why the CHECK is not clean (three independent reasons):**
1. **Out of domain.** Eq. (15) is fitted on synthetic S22/S42 sands at
   L = 3–30 m (CG24 §4.4, "31 simulations / 3100 points"). B25-245 is
   L = 0.352 m real lab sand — the regression was never fit to it; CG24
   reproduced this box with the *full FE model*, not Eq. (15).
2. **Loading input unconfirmed.** Table 3.2 gives only the loading *type*
   ("L1" = gradual ramp to H_c then hold); the actual H(t) curve exists only
   as Fig. 5(c) (CG24), i.e. the **unconfirmed digitized** `B25-245_head-BC`
   CSV. The magnitude check's driving input therefore cannot be made external.
3. **Edge of band.** The engine reaches v_c,avg = 2.21e-5 = **0.36× measured**,
   inside a factor-3 band [2.05e-5, 1.84e-4] but at its lower edge; even Pol's
   own calibrated DgFlow reaches only 0.51×. A factor-3 band that passes 0.36×
   is drawn around our own output, not Pol's data — the repo already demoted
   B25-245 to a qualitative gate for exactly this reason.

**No in-domain EXPERIMENTAL magnitude anchor exists in the sources.** The only
in-domain quantitative check (S2-2, L = 3 m) targets a DgFlow **model** output
(7.08e-5 m/s), which the engine reproduces at the documented 1.95× ADR-0009
H_eq-conservatism — a model-vs-model check, not experiment-vs-model. So the
rate law's *constants* are validated (anchor 2), but its *absolute magnitude
against experiment* is not cleanly closable from these papers. The B25-245
shape check stays shape-only with unconfirmed digitized provenance.

## 4. Head-datum verification — OPEN (self-reference is irremovable here)

**What IS confirmed against the print** (SIE 2024 Eq. (6), p.4, visual):
`H = h − h_e − 0.3·D_bl`, *"h outer water level, h_e polder level at the exit
point, D_bl polder blanket thickness"*. So the **0.3 coefficient**, the
**h_e = exit-point datum**, and the **composition** (subtract 0.3·D_bl from the
head difference) are externally confirmed. The engine's `CRACK_RESISTANCE_FACTOR
= 0.3`, `z_toe ≡ h_e`, and subtract-after order all agree.

**What is NOT closable — the irremovable self-reference.** Eq. (6) uses the
**raw outer water level h** (no r_e). Eqs. (8)–(10) put r_e **only** on the
uplift/heave head: `φ_it = h_e + r_e·(h − h_e)`. The engine instead applies
r_e to the **progression** head too: `H_erosion = r_e·(h − z_toe) − 0.3·D_bl`.
This is the **documented ADR-0007 deviation**, now print-confirmed:
- engine H_erosion **= Eq. (6) exactly at r_e = 1** (verified: diff 0.000 m);
- engine H_erosion **deviates by exactly the r_e factor otherwise** (verified:
  at r_e = 0.6, −1.2 m at h = 3 m, −2.0 m at h = 5 m).

The 0.3·D_bl term appears **only** in the SIE field model, where r_e = 0.6 —
never in a calibration experiment (B25-245/FPH have r_e = 1 but D_bl = 0, so
no crack term at all; extraction-confirmed "no blanket in the small-scale
tests"). **Therefore no published configuration combines an active 0.3·D_bl
term with the r_e = 1 case where the engine and Eq. (6) coincide.** A test
checking engine H_erosion against Eq. (6) "as written" would show the
ADR-0007 deviation, not a validation; a test at r_e = 1 with a hand-typed
`h − h_e − 0.3·D_bl` would relocate the self-reference the owner warned
against. **No confident fixture was built.**

**The specific question to confirm with Pol directly:** is applying r_e to the
progression-driving head — `H_erosion = r_e·(h − z_toe) − 0.3·D_bl` — the
intended field-application convention, versus Eq. (6)'s raw `h − h_e − 0.3·D_bl`
(with r_e applied only to uplift/heave, Eq. 10)? ADR-0007 argues the
r_e-attenuated aquifer head is the physically correct driver at a
foreland/blanket-damped exit and that Eq. (6) is written for Pol's r_e = 1
validation geometry; Pol's papers as written do not apply r_e to progression.
This is a **modeling-convention question, not a code bug**, and it cannot be
resolved from the repo or the papers alone.

## 5. Mazure / Model-4A r_e — CLOSED (unchanged)

Form print-verified in the ADR-0006 amendment (USACE App. B Eqs. B-3/B-5/B-7,
TAW Model 4A, Pol Eq. 7.13 as the x1 = 0 case); numeric check exact to machine
precision (λ_in = 200.0, r_e = 0.8, tanh limits). No external anchor needed;
optional USACE worked-example (x3 = 167 m) remains an available strengthening.

## Bottom line

The engine is **physically validated on the static critical-head law and the
progression rate constants** (anchors 1, 2, 5 CLOSED against real published
values), and **not yet physically validated on two specific points**:
- **anchor 3** — no clean experimental validation of the progression rate's
  absolute *magnitude* (the only experiment, B25-245, is out of domain with an
  unconfirmed loading input; in-domain S2-2 is model-vs-model); and
- **anchor 4** — the head-datum r_e-on-erosion-head convention (ADR-0007)
  cannot be validated against Pol's published numbers and needs Pol's direct
  confirmation.

Neither open anchor is a discrepancy forcing an engine change; both are
"cannot be closed from the available sources" gaps. The timestep-gate failure
(P3, prior session) remains separately open.
