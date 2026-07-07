# Stage 6 Reference-Anchor Extraction Worksheet

Purpose: supply **owner-extracted published values** so the physics reference
check runs against real anchors instead of repo transcriptions. Fill every
`EXTRACT:` field by reading the named source in `docs/references/` (page
pointers are PDF page indices, 0-based, from a text-search locate pass — the
printed page number may differ by the front-matter offset). The "repo carries"
column shows what the engine/tests currently assume and its provenance chain —
**do not copy it; read the paper**. Where your extraction disagrees with the
repo value, that disagreement is itself a finding.

Rules (fixed): thresholds below are the pass bars and are not softened at run
time. No engine physics changes in the check. Reproduced-vs-published margins
are reported for every anchor, pass or fail.

---

## 1. Sellmeijer 2011 — IJkdijk critical heads

**What the check licenses:** the M6 implementation of formula [6]
(H_c = L·F_r·F_s·F_g) against (a) the paper's own evaluation of its rule and
(b) the observed critical heads.

### 1.1 Shared model constants (confirm from the formula [6] block and Table 2, `sellmeijer_2011.pdf` PDF pp. 7–8)

| Constant | Repo carries (provenance) | EXTRACT: paper value | Where |
|---|---|---|---|
| η (White drag) | 0.25 (test/docstring) | EXTRACT: | formula [6] text |
| θ bedding angle used in rule evaluation | 37° (spec §7) | EXTRACT: (confirm the paper evaluates [6] at 37° or per-sand θ) | formula [6] text / §7 |
| D_r,m / C_u,m / KAS_m / d70,m | 0.725 / 1.81 / 0.498 / 208 µm (Table 2 transcription) | EXTRACT: all four | Table 2, PDF pp. 7–8 |
| Regression exponents (D_r, C_u, KAS terms) | 0.35 / 0.13 / −0.02 (Table 1 transcription) | EXTRACT: | Table 1, PDF p. 7 |
| Kinematic viscosity ν used by the paper | 1.3e-6 m²/s (assumed 10 °C) | EXTRACT: (state if paper prints ν or T) | formula [6] text |
| Regression scatter (the physics tolerance) | 13.2% noise / ~13.4% drift (§6 transcription) | EXTRACT: exact printed % and wording | §6, PDF p. 9 |
| Coarse-sand deviation statement | "25%" (§8/§9 transcription) | EXTRACT: exact sentence | PDF p. 15 |

### 1.2 Per-case fixture (IJkdijk §7, PDF pp. 10–14; Figs. 5–7). Cross-source: Pol thesis App. A Table A.3, `pol_thesis_2022.pdf` PDF p. 217 — record WHICH source each value came from.

Fill one block per test. The engine inputs are exactly:
`L, D_aq, d_70, k_aq, γ'_p (from ρ_s), D_r, C_u, KAS` (+ the shared constants
above; F_r ratio terms use per-case D_r/C_u/KAS if the paper's own prediction
did — extract what the paper used).

```yaml
ijkdijk_case_1:            # fine sand, silt-corrected test (Fig. 5)
  test_id:            EXTRACT   # paper's test label
  L_m:                EXTRACT   # repo: 15.0
  D_aq_m:             EXTRACT   # repo: 3.00
  d70_m:              EXTRACT   # repo: 180e-6
  k_aq_mps:           EXTRACT   # repo: 8.0e-5 (source: thesis Tab. A.3, NOT Sellmeijer)
  rho_s_kgm3:         EXTRACT   # repo: 2500 -> gamma'_p = 14.715 kN/m3 (thesis A.3 footnote)
  D_r:                EXTRACT   # per-case if printed; else state "means used"
  C_u:                EXTRACT
  KAS:                EXTRACT
  silt_correction:    EXTRACT   # repo comment: 5%; state how the paper applied it
  H_c_observed_m:     EXTRACT   # repo: 2.30 (source: thesis Tab. A.3)
  H_c_paper_predicted_m: EXTRACT_OR_NONE  # if Sellmeijer prints its own [6] value
  source_pages:       EXTRACT
ijkdijk_case_2:            # coarse sand (Fig. 6); repo: d70=260e-6, D=2.85, k=1.4e-4, H_c=1.75
  ...same fields...
ijkdijk_case_3:            # fine sand, no silt (Fig. 7); repo: as case 1, H_c=2.10
  ...same fields...
```

**Pass bars (fixed):**
- vs `H_c_paper_predicted_m` (if printed): |Δ| ≤ 3% (input-rounding budget) —
  this is the *implementation* anchor and closes the transcription risk.
- vs `H_c_observed_m`: |Δ| ≤ the extracted regression scatter for fine sand
  (repo's 15% stands only if your extraction confirms ~13%); case 2 ≤ the
  paper's own printed coarse-sand deviation (repo: 25%).

---

## 2. Pol 2024 — B25-245 and FPH progression

**What the check licenses:** the M7 rate law Eq. (5)/(15) + H_eq Eq. (11)
magnitude at the calibrated C_e — replacing the shape-only digitized-curve
check with printed-number magnitude gates.

### 2.1 B25-245 (small-scale). Sources: CG24 Table 1 (`pol_compgeo_2024.pdf` PDF pp. 4–5), thesis Table 3.2 + §3.2.1 (`pol_thesis_2022.pdf` PDF pp. 64/68), thesis Table 5.1 (PDF pp. 118–119).

> RESOLVED (Pol email 2026-07-08): the correct B25-245 C_e is **0.010** (Table 1);
> the Fig. 5 caption's 0.014 is the error. Repo already uses 0.010. See
> `reference-anchor-status.md` §3 and ADR-0026.

```yaml
b25_245:
  # calibration constants (CG24 Table 1 column B25-245; cross-check T22 Tab 5.1)
  C_e_table:          EXTRACT   # repo: 0.010 (Table 1) — CONFIRMED correct by Pol
  C_e_caption:        EXTRACT   #   Fig. 5 caption 0.014 = the error (Pol, 2026-07-08)
  kappa_m2:           EXTRACT   # repo: 3.16e-11
  d50_mm:             EXTRACT   # repo: 0.228
  eta:                EXTRACT   # repo: 0.3 (calibrated)
  i_tip_c:            EXTRACT   # repo: 0.9
  w_over_a:           EXTRACT   # repo: 25
  mu_Pas:             EXTRACT   # repo: 0.001
  # geometry + measured anchors (thesis Table 3.2 row B25_245; §3.2.1)
  L_m:                EXTRACT   # repo: 0.352
  D_m:                EXTRACT   # repo: 0.1
  k_mps:              EXTRACT   # repo: 3.1e-4 (printed in Tab 3.2)
  H_c_corr_m:         EXTRACT   # repo: 0.054
  l_c_measured_m:     EXTRACT   # repo: 0.197
  v_c_avg_mps:        EXTRACT   # repo: 6.14e-5  <- THE magnitude anchor
  t_c_s:              EXTRACT_OR_NONE   # if Tab 3.2 / text prints t_c, t_end
  t_end_s:            EXTRACT_OR_NONE
  breach_observed:    EXTRACT   # did the measured pipe reach L?
  # loading: EITHER extract the printed head-step schedule (if tabulated),
  # OR confirm >=6 points of the digitized head BC 'B25-245_head-BC_Hcorr.csv'
  # against Fig. 5(a)/(b) so its provenance becomes owner-confirmed.
  loading_source:     EXTRACT   # "printed schedule (where)" | "digitized confirmed"
  confirmed_head_points: EXTRACT_OR_NONE   # [(t_s, H_m), ...] >= 6 points
  # scatter statement that sets the tolerance (CG24, PDF p. 5 area)
  scatter_statement:  EXTRACT   # exact sentence, e.g. "differences up to a factor 3"
```

**Pass bars (fixed):**
- **Magnitude (new, replaces shape-only):** M7 post-critical average rate
  v_c,avg at the extracted calibrated C_e, driven by the confirmed loading and
  anchored on the measured (H_c_corr, l_c), within the **extracted scatter
  factor** of `v_c_avg_mps` (repo expectation: factor ~3; current replay sits
  at 0.36× = inside a factor-3 band, near its edge — the check will show the
  margin honestly).
- Breach/no-breach at the calibrated C_e must match `breach_observed`? NO —
  the documented finding is that even Pol's own calibrated DgFlow does not
  reproduce this box's full breach; the gate is the rate magnitude above.
  (State this in the report, never hide it.)
- Shape checks are retained only as secondary diagnostics once the digitized
  curves are owner-confirmed (or dropped if you decline to confirm them).

### 2.2 FPH (large-scale). Sources: CG24 Table 1 + §3.2.2 (PDF pp. 4–6), thesis Summary (PDF p. 11) + Ch. 4 (FPH test description, PDF pp. ~66–73) + p. 191 area for the 0.3 m/h statement.

```yaml
fph:
  C_e:                EXTRACT   # repo: 0.014 (table AND caption agree)
  kappa_m2:           EXTRACT   # repo: 1.2e-11
  mu_Pas:             EXTRACT   # repo: 0.00133 -> repo-derived k = 8.85e-5 m/s (not printed)
  L_m:                EXTRACT   # repo: 7.2
  eta:                EXTRACT   # repo: 0.4
  i_tip_c:            EXTRACT   # repo: 1.1
  w_over_a:           EXTRACT   # repo: 700
  # the two items that unlock a FORWARD replay (currently missing from repo):
  aquifer_depth_D_m:  EXTRACT   # thesis Ch. 4 (§4.2) geometry
  head_sequence:      EXTRACT   # printed loading steps H(t) or (level, duration) list
  max_head_m:         EXTRACT   # repo: 1.8 (thesis Summary)
  # the magnitude anchor:
  v_progressive_mps:  EXTRACT   # repo: "~0.3 m/hour" (thesis Summary/p. 191) = 8.3e-5 m/s
                                #   extract the exact sentence + any printed rate figure
  # optional: confirm >=5 of the 9 digitized x_tip points vs CG24 Fig. 6(b)
  confirmed_xtip_points: EXTRACT_OR_NONE
```

**Pass bar (fixed):** M7 forward replay (extracted geometry + head sequence,
C_e = 0.014) progressive-phase average rate within the extracted scatter
factor of `v_progressive_mps`. If Ch. 4 does not yield a usable head sequence,
the FPH gate is reported **not runnable** with that stated reason — not
silently passed.

---

## 3. Head-datum verification — non-self-referential redesign

**The flaw being fixed:** the current test computes its expected value
(h − h_e − 0.3·D_bl) with the same convention as the code, so a shared error
in the 0.3 factor, the datum, or the composition order would pass. The fix
anchors the whole head chain on **numbers printed in Pol SIE 2024**
(`pol_sie_2024.pdf`), which is the paper that defines Eqs. (6)–(11) and their
datum.

### 3.1 Primary anchor — SIE 2024 worked example replay (full chain: datum + 0.3·D_bl + H_eq + rate)

The paper's example (dune/coastal storm case; Table 2 at PDF p. 8, example
figures around PDF pp. 5–7 and 9; the repo already holds digitized
`SIE_coastal-example_{waterlevel,pipelength,events}.csv` of unconfirmed
provenance) is Pol's own published model output computed with Eq. (6)'s
datum. Reproducing his pipe-length trace with our M7, r_e injected as the
paper's bare 0.6, is the strongest available closure.

```yaml
sie_example:
  # Table 2 (PDF p. 8) — extract the ENTIRE base-case/deterministic column:
  h_e_m:              EXTRACT   # datum (repo believes 0 m NAP)
  r_e:                EXTRACT   # repo: 0.6 deterministic
  D_bl_m:             EXTRACT   # the 0.3*D_bl term's D_bl
  L_m:                EXTRACT
  D_aq_m:             EXTRACT
  k_mps_or_kappa:     EXTRACT
  d70_m:              EXTRACT
  C_e:                EXTRACT   # SIE Table 2 (thesis App E Ln(0.055, 0.043)? extract what the example RUN used)
  i_c_h:              EXTRACT   # heave criterion of the example (repo: Ln(0.7, 0.1))
  gamma_bl_sat:       EXTRACT   # for the uplift threshold
  H_c_printed_m:      EXTRACT_OR_NONE   # if the example prints its Sellmeijer H_c
  l_c_printed_m:      EXTRACT_OR_NONE
  # the trace: confirm >=6 digitized (t, l) points against the example figure,
  # AND >=6 (t, h) waterlevel points, OR extract printed event table values:
  confirmed_waterlevel_points: EXTRACT
  confirmed_pipelength_points: EXTRACT
  # any printed scalar tying head to level, e.g. "at h = X m the pipe starts
  # to grow / H = Y m" or a printed onset level:
  printed_onset_or_H_pair: EXTRACT_OR_NONE
```

**Pass bars (fixed):**
- With the extracted inputs and the paper's own r_e = 0.6 and i_c,h (the
  engine's Terzaghi gate is matched WITHOUT physics change by setting
  γ'_bl = i_c,h·γ_w in the replay — the documented ADR-0008 equivalence; the
  uplift-latch difference this leaves is quantified in the report), the M7
  trace must reproduce the confirmed pipe-length points within **10% of L**
  at each confirmed time, and the onset time/level within one loading step.
- If `printed_onset_or_H_pair` exists: engine H_erosion at that printed h must
  equal the printed H to print precision (±0.01 m) — the direct, single-number
  closure of the 0.3·D_bl-with-datum trap.

### 3.2 Secondary anchor — H_eq curve (SIE Fig. 3, simplified curve)

The repo holds `SIE_equilibrium_simplified.csv` (digitized). Confirm ≥4 points
(l/L, H_eq/H_c) of the *simplified* (Eq. 11) curve from the figure, plus the
caption's H_c/l_c/L. Pass: engine `equilibrium_head` reproduces the confirmed
points within figure-reading precision (±0.03 in H_eq/H_c) — this anchors
Eq. (11) (including the 0.9 end factor and the l_c breakpoint) independently
of our transcription of it.

```yaml
sie_fig3:
  H_c_m: EXTRACT;  l_c_m: EXTRACT;  L_m: EXTRACT
  confirmed_points: EXTRACT   # [(l_over_L, Heq_over_Hc), ...] >= 4
```

---

## 4. Mazure / Model 4A r_e — verdict: CLOSED, one optional strengthening

The r_e check is **not** self-referential in the way the head-datum test is:
the 2026-07-04 source analysis verified the *form* against the printed
equations (USACE EM 1110-2-1913 App. B Eqs. B-3/B-5/B-7 with L₂ linear; TAW
2004 Model 4A resistance sum; Pol thesis Eq. 7.13 as the x₁ = 0 case — quoted
with page/eq numbers in the amended ADR-0006), and the numeric test then
checks the implementation against that verified closed form at machine
precision (λ_in = 200.0 exactly, r_e = 0.8 exactly, tanh limits exact). Form:
print-verified. Algebra: exact. **No further anchor is required.**

Optional (cheap, recommended): USACE App. B contains a **worked numerical
example** (PDF pp. 7–8 of `USACE 2000.pdf`: the x₃ computations "= 167 m" /
"= 551 ft", and the x₁ example around Eq. B-7). Extract the example's inputs
and its printed x₁/x₃ (and head ratio if printed):

```yaml
usace_example:
  inputs:  EXTRACT   # k_f, k_b, z_b, d, L1, L2, L3 as printed
  x3_printed: EXTRACT   # e.g. "167 m" case
  x1_printed: EXTRACT_OR_NONE
  h_toe_printed: EXTRACT_OR_NONE
```

Pass: engine kernels reproduce the printed x₁/x₃ within 1% (their print
rounding). This makes even the effective-length algebra externally anchored.

---

## Handback format

Fill the YAML blocks in place (or a copy) and hand the file back. I will turn
each block into a pinned test fixture, run the reference check, and report
reproduced-versus-published margins per anchor against the fixed bars above —
including any disagreement between your extractions and the repo-carried
values, which will be listed as findings, not silently adopted.
