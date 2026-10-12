# The time-dependence factor on one head and one gate (Pol comments 1 and 2)

Companion to **ADR-0055** (`0055-same-head-same-gate-steady-state-comparator.md`).
Evidence: `docs/decisions/time-dependence-factor-study.json`.
Driver: `scripts/time_dependence_factor_study.py` (parts `event`, `larms`, `uarms`,
`brackets`, `evidence`, `annual`, `timescale`, `polriver`, `figures`, `report`).
Gate: `tests/test_time_dependence_factor.py`.
Run artifacts: gitignored `results/time_dependence_factor/` (regenerable).
Date: 2026-10-06. Matrix reading unless stated; KP 58.8 and KP 60.0 as if undrained.

No production default, config, prior, kernel, persisted sweep, Phase 2 posterior,
Phase 3 table or published transient number changes. What changes is which steady-
state rule the thesis compares the transient model against.

---

## 1. The question

Joost Pol's written comments on the pre-Green-Light thesis (2026-10-06):

1. "effect of cover layer resistance: why not only present results with the same
   head convention? Now it is confusing. It is not necessary to present everything
   you have done but the things that are relevant."
2. "magnitude of factor due to TD: 'duration alone produces a factor of one to about
   six' --> other parts mention a factor 30. what's the right metric? If its really
   B=1-6, how does this relate to results for NL where we find these factors for
   Rhine river with flood duration of weeks?"

The version he read headlined B = 26.9 at KP 62.0's design level and B >= 148 at
KP 57.4 against the **gross-head** static rule (ADR-0028), and in the same paragraph
"duration alone ... one to about six", the Stage 6.6 ratio C3b/C4b. The two are
different comparisons: the first mixes the exit head loss `0.3 D_bl` and the
initiation gate into the time effect, the second does not. The real problem was
therefore larger than presentation: the thesis's headline criterion difference was
not the effect of time, and its comparison with Pol's factor set a per-event
quantity beside his cumulative one.

## 2. Sources read for this study

| Source | Page | What it says |
|---|---|---|
| Pol et al. (2024, SIE) | Eq. (18), §3.2, Table 3, §3.4, Fig. 13 | `F_td = P_f,stat / P_f,td`, "stat" = the same model with instantaneous pipe growth (same Eq. 6 head, same uplift and heave). River base case: 17 (method A) / 26 (B) in 2025, 4.0 / 5.4 cumulative to 2050, **with** flood fighting; case 3d (h_p ~ Gumbel(3, 0.25), no flood fighting) 6.5 in 2025 and 2.8 in 2050, against 38 / 11 for case 2d at the same loading with flood fighting. Fig. 13 (2050, no flood fighting): river about 1.4 to 4.5 for coarse sand or short paths; about 24 to 2,000 for fine sand with long paths (read from the figure). Text: "flood fighting ... explains the majority of the difference" for river levees. |
| Pol et al. (2024, SIE) | Table 2 (rendered page 8; the text layer is readable) | L 50 (sd 5), D_aq 20 (0.5), D_bl 3 (0.5), gamma_sat 18 (1), i_c,h 0.7 (0.1), d70 0.150 mm (CoV 0.1), k 1e-4 (CoV 0.5), r_e 0.6, m_u 1 (0.1), m_p 1 (0.12), C_e 0.055 (0.043), river D_p 48 (24) h, all lognormal; base D_0 = 240 + 3 D_p h (§3.1.2, Fig. 6b). |
| Schweckendiek (2014) | Eq. (3.14) p. 26; §3.2.5 p. 27 | `Z_p = m_p H_c - (h - h_p - 0.3 d)`; piping failure is the intersection of uplift, heave and piping, a parallel system. |
| TAW (1999), TR Zandmeevoerende Wellen | p. 32; Table 4.2 p. 38 | Fluidised sand-column tests (Sellmeijer 1981) lost about 0.6 times the column height; the rule credits it with "een veiligheidsfactor van ongeveer 2", i.e. 0.3 d; Table 4.2 applies `(ΔH - 0.3 d)` to the Sellmeijer criterion. This corrects `equal-head-convention-study.md` §1.5 (the report had not been read there) and the thesis sentence "No step in this chain calibrates the coefficient". |
| Sellmeijer (2011) | as in the equal-head study §1.1 | Gross head across the structure, no blanket term. |

## 3. The comparator and its gates

The comparator of record (ADR-0055) is C3b: gate open at the peak and
`h_peak - z_toe - 0.3 D_bl > H_c`. It is evaluated in closed form from the M8
diagnostics of a four-sample constant-stage record at every level, exactly as
`gap_decomposition._evaluate_ladder_level` does.

- **Static gate.** At every level of every evaluated run (8 production strata,
  32 bracket arms) the recomputed gross-head column equals the persisted
  `failure_matrix_static` bit for bit, or the driver refuses.
- **Containment.** No C4b row outside C3b anywhere at N = 1e5 matrix; at N = 1e6
  KP 57.4 the 14 documented forward-Euler barrier-jump rows (39.75 to 41.0 m, at
  most 0.14 % of transient failures at a level, none at an anchor). In the 2016
  replay, no same-head survivor fails transiently in any stratum or on the berm.
- **Reproduction gate.** The bracket part recomputes the published gross-head
  ratio-of-ratios departures of `epistemic-bracket-synthesis.json` with the
  ADR-0047 kernel: 24 of 24 reproduce exactly (factor and level count).
- **Annual gate 1.** The transient prior and posterior arms reproduce the
  production Phase 3 table on all 912 rows; the 110 surface-only segments are
  identical across every branch; the hazard cache is unchanged.

## 4. Per event

Design anchors (N as stated; brackets are paired 95 % intervals):

| Anchor | N | k static | k transient | Δβ | F_td |
|---|---|---|---|---|---|
| KP 57.4, 39.21 m (design) | 1e6 | 4 | 2 | 0 to 0.77 (containment; count endpoints) | >= 1; unresolved |
| KP 57.4, 39.50 m | 1e6 | 561 | 163 | 0.34 [0.30, 0.37] | 3.44 [3.02, 3.94] |
| KP 58.8, 41.00 m | 1e5 | 44 957 | 19 736 | 0.72 [0.72, 0.73] | 2.28 [2.25, 2.30] |
| KP 60.0, 42.75 m | 1e5 | 21 634 | 5 579 | 0.81 [0.79, 0.82] | 3.88 [3.79, 3.97] |
| KP 62.0, 46.39 m (design) | 1e6 | 350 | 51 | 0.50 [0.44, 0.57] | 6.86 [5.47, 9.31] |
| KP 62.0, 46.50 m | 1e6 | 967 | 130 | 0.55 [0.51, 0.59] | 7.44 [6.38, 8.80] |

All R1, R2 and R2β-quotable except KP 57.4's design level. Sellmeijer's gross-head
form (C0) at the same anchors: factors over C3b of 75 (KP 57.4 design, 302 against
4), 14.9 (39.50 m), 1.35, 1.63, 3.44 and 2.90; it adds 0.35 to 0.41 to Δβ at the
three resolved design anchors and 0.86 at KP 57.4's 39.50 m. The gate alone (C1
against C3b) binds at KP 57.4 (695 against 561 at 39.50 m) and on the lower
shoulders of KP 58.8 and 60.0 (995 against 922 at KP 58.8 40.00 m), by less than
0.1 % at the design levels of KP 58.8, 60.0 and 62.0, and never at KP 62.0.

**Severity.** Over attainable stages with at least 30 transient failures, F_td
falls from 3.18 / 3.83 / 5.82 / 6.23 at the lowest such stage to 1.06 / 1.20 /
1.76 / 1.46 at the attainable top (KP order), while Δβ rises from 0.40 / 0.46 /
0.61 / 0.59 to 1.21 / 1.17 / 1.19 / 1.46. Survival at the tops: same-head 0.3 to
11.7 %, transient 5.6 to 49.9 %. The index difference is monotone in stage here; the
U-shape of the gross-head comparison came from the head term.

**Scale exponent (1e6).** Transient-only α = -1/2 (C3b against C4a): Δβ at
KP 62.0's design level -1.10 (11 091 transient against 350 static failures);
KP 57.4 -1.20 at its design level. Symmetric (C3a against C4a): +1.05 at KP 62.0's
design level; +0.64 to +1.08 at KP 57.4 from the design level to 43.25 m, each on
at least 545 transient failures.

**Bulk.** Only KP 60.0 is measurable at its design level: 0.042 static against
0.011 transient, F_td 3.94 [3.75, 4.15], Δβ 0.57.

## 5. Brackets on the effect of duration

Ranges over attainable levels where all four cells reach 30 failures (R1); the
ADR-0047 floor of 10 is also recorded in the JSON.

| Arm | F_td factor | Δβ change | Note |
|---|---|---|---|
| Conductivity, regional upper | 0.22 to 0.95 | -0.05 to +0.32 | faster pipes shrink the effect |
| Conductivity, landside-toe test | 1.67 to 3.56 | -0.07 to +0.03 | |
| Conductivity, six-test mean | 25.5 to 27.0 | -0.12 to -0.09 | 4 stages, KP 57.4 and 62.0 only |
| Shorter canonical event | 1.10 to 2.98 | +0.26 to +0.53 | C3b exactly invariant |
| DEM seepage length | 1.01 to 1.72 | -0.04 to +0.01 | |
| Critical length x0.643 / x1.556 | 0.73 to 1.18 | -0.10 to +0.07 | C3b exactly invariant |
| Model factor m_p | 0.94 to 1.11 | -0.19 to +0.08 | multiplies H_c in both |
| Lighter blanket | 0.97 to 1.00 | -0.01 to 0 | gate only, shared |

At the design-grid levels of KP 58.8 and 60.0 no conductivity arm moves Δβ by more
than 0.03; the shorter event moves it by +0.38 at both (F_td 2.28 to 4.09 and 3.88
to 8.89). In ratio terms conductivity is the largest lever on the effect of
duration; among inputs that raise Δβ the flood shape is the largest, and only the
extrapolated uniformity term and strong drain relief (below) move it further,
downward. The published gross-head departures
(conductivity 67 / 56 / 72 / 46) were computed at the ADR-0047 floor of 10, not
the thesis's R1 floor of 30 (40 / 46 / 49 / 34 at 30): the thesis table quoted
them as "count-qualified", which was true only of the weaker floor.

### 5.1 Uniformity, exit datum, drainage and r_e on one head and gate

Every number here is in `derived` or `halved_r_e` of the JSON, computed from the
stored per-level counts; the arm runs are the Green Light item 1 uniformity arms
(re-run into `results/time_dependence_factor/u_arms/` and gated against that
study), the ADR-0046 exit-datum companions and the ADR-0050 drained ladder.

| Arm | F_td factor | Δβ change | Δβ at design grid KP 58.8 / 60.0 |
|---|---|---|---|
| none (adopted) | 1 | 0 | 0.72 / 0.81 |
| C_u tested maximum 2.6 | 0.90 to 1.05 | -0.10 to -0.03 | 0.67 / 0.75 |
| C_u sand fraction | 0.82 to 1.16 | -0.28 to -0.07 | 0.60 / 0.66 |
| C_u whole matrix | 0.79 to 1.44 | -0.63 to -0.27 | 0.36 / 0.38 |
| exit datum -0.30 m | 0.80 to 0.98 | +0.01 to +0.08 | |
| exit datum +0.30 m | 1.03 to 1.24 | -0.08 to -0.04 | |

The uniformity term multiplies the H_c both criteria share, so Δβ falls in every
arm while F_td moves either way. On the gross-head comparison the same arms gave
B x0.97 to 1.90 and Δβ -0.03 to -0.63: the index change survives the change of
comparator, the ratio change does not (it now straddles one). The matrix arm
(an exponent applied at C_u 42 to 66 against a calibrated maximum of 2.6) is the
largest Δβ lever among the soil inputs.

**Model factor and exit datum, per branch** (count-qualified: at least 30
failures and 30 survivors in both arms, attainable stages). m_p multiplies the
same-head probability by at most 2.19 / 2.24 / 2.42 / 2.22 (KP order) and the
transient by 1.68 / 1.61 / 1.93 / 1.76; on the gross head the static maxima were
2.94 / 2.54 / 2.51 / 2.23. The figure `same_head_mp_ztoe.png` replaces
`epistemic_knobs_mp_ztoe.png` in the thesis, whose static panels are gross-head.
At KP 62.0's 46.75 m grid stage (0.36 m above the 46.39 m design level, the
lowest with at least 30 transient failures; adopted 629 / 101, F_td 6.23,
Δβ 0.59): m_p 6.94 / 0.67; exit datum -0.30 m 5.59 / 0.67; regional upper k_aq
1.53 / 0.58; lighter blanket identical; datum +0.30 m and the landside-toe test
leave 7 and 3 transient failures; the six-test mean none on either branch.

**Drained ladder at the design grid** (KP 58.8 41.00 m / KP 60.0 42.75 m):

| Configuration | P_trans | F_td | Δβ | Δβ change [95 %] |
|---|---|---|---|---|
| as if undrained | 0.197 / 0.0558 | 2.28 / 3.88 | 0.72 / 0.81 | |
| measured berm, inert drain | 0.0736 / 0.00875 | 3.11 / 6.65 | 0.71 / 0.81 | -0.017 [-0.029, -0.004] / -0.000 [-0.025, +0.025] |
| berm, 20 % relief | 0.0716 / 0.00860 | 3.17 / 6.74 | 0.71 / 0.81 | -0.010 / +0.004 |
| berm, 40 % relief | 0.0522 / 0.00714 | 3.52 / 7.23 | 0.72 / 0.82 | -0.001 / +0.014 |
| berm, 60 % relief | 0.00484 / 0.00095 | 4.29 / 10.4 | 0.55 / 0.77 | -0.18 [-0.20, -0.15] / -0.03 [-0.09, +0.03] |
| berm, 80 % relief | 0 / 0 | | | |

Relief acts on the exit gradient, which both criteria share, so the same-head
static falls with it; the gross-head static did not (ADR-0050: "static exactly
invariant"). The consequence reverses the drained reading the thesis gave: on the
gross head the as-if-undrained gap was the LOW end of the bracket (1.13 / 1.22
rising to 2.26 / 1.94 at 60 % relief); on one head and gate it is at or within
0.02 of the TOP, and 60 % relief lowers Δβ (by 0.18 at KP 58.8). Over all R1
stages the 80 % relief arm moves Δβ by -0.90 to -0.93 (two stages, KP 58.8) and
-0.73 (one stage, KP 60.0): the largest single-stage Δβ displacement measured,
but a drain scenario, not a soil input.

**Halved r_e** (= relief 0.5 on the gate, `rehalf` part, KP 58.8 matrix): the
gate share at 41.00 m falls from 0.999 to 0.368 and the same-head probability
from 0.450 to 0.203 (the largest drop on the grid, 0.247); no realization
starts failing. The transient side (0.197 to 0.073) is the published test; the
gross-head static is unchanged by construction.

**Pairing.** Over the 53 attainable R1 matrix levels pairing lowers the variance
of Δβ by factors of 1.14 to 2.48 (delta method on the four joint cells), against
1.04 to 1.60 quoted for the gross-head pair.

## 6. What 2016 says between the criteria

| Stratum | rejected transient | rejected same-head | LR [95 %] | LR against gross head |
|---|---|---|---|---|
| KP 57.4 | 0.016 % | 0.39 % | 1.004 | 1.03 |
| KP 58.8 | 3.813 % | 28.33 % | 1.342 [1.337, 1.347] | 1.756 |
| KP 60.0 | 0.226 % | 5.17 % | 1.052 [1.051, 1.054] | 1.145 |
| KP 62.0 | 0 | 0 | 1.000 | 1.000 |
| KP 58.8 berm | 0.899 % | 11.91 % | 1.125 | 1.29 |
| KP 60.0 berm | 0.014 % | 0.80 % | 1.008 | 1.03 |

Jointly: 1.34 comonotone, 1.42 independent, 1.45 at the Fréchet lower bound. Relief
acts on the shared gate, so no drain role can raise the KP 58.8 berm LR above
1/(1 - 0.119) = 1.14. One survival at each section's attainable top would carry
22, 9.4, 4.3 and 11.4. The ratio between the same-head and gross-head LRs (1.31 at
KP 58.8) is the exit head loss.

## 7. Annual

Steady-state (same head and gate) over transient, matrix, both curves fitted as
production fits them; the static self-posterior is the raw evaluation (a lognormal
cannot follow the survival truncation; the fitted form deviates by up to 0.135).

| Section | prior, hist. system | prior, +4 K | prior Δβ hist. | own-update hist. | own-update +4 K |
|---|---|---|---|---|---|
| KP 57.4 | 2.05 [1.98, 2.17] | 1.60 [1.53, 1.67] | 0.21 | 1.99 [1.92, 2.05] | 1.58 |
| KP 58.8 | 1.82 [1.72, 1.95] | 1.64 [1.60, 1.68] | 0.22 | 1.17 [1.03, 1.27] | 1.25 |
| KP 60.0 | 3.32 [3.21, 3.42] | 2.59 [2.46, 2.75] | 0.34 | 2.15 [1.57, 2.47] | 2.13 |
| KP 62.0 | 2.68 [2.28, 3.25] | 1.65 [1.56, 1.77] | 0.30 | 2.68 [2.27, 3.23] | 1.65 |

Piping alone, historical: 2.05 / 1.84 / 3.32 / 3.12. This is the like-for-like
counterpart of Pol's first-year factor without flood fighting (one annual maximum,
intact blanket, no intervention). The gross-head equivalents were 2.6 to 6.0 prior
and 1.26 to 3.22 after the own update. Rankings: the prior steady-state branch puts
KP 60.0 third historically in 73 % of resamples (1.07e-3 against KP 57.4's
1.02e-3) and last under warming; it turns the KP 62.0 warming tie into a piping
share of 0.70 [0.67, 0.73]; under the bulk reading it no longer moves KP 57.4's
warming cell to piping (0.48). The transient climate ratio is 1.29 / 1.11 / 1.28 /
1.62 times the steady-state one before updating. Raw evaluation of every branch:
prior factors 2.17 / 1.88 / 3.89 / 2.94; posterior at KP 58.8 1.31 (fitted static
posterior 1.41).

## 8. Time scales

For every realization failing C3b at a stage: the held-peak traverse time (the
integral of dl / v with the engine's Eq. 5 and Eq. 11, Chebyshev-clustered at both
ends of the two H_eq branches; checked against the forward-Euler kernel to 2 % in
the gate test) and the hours the canonical record keeps the stage above both the
erosion threshold `z_toe + 0.3 D_bl + H_c` and the gate threshold. Medians:

| Section, stage | transient failures: traverse / available | saved by duration: traverse / available |
|---|---|---|
| KP 57.4, 39.75 m | 2.3 / 5.2 h | 8.9 / 2.7 h |
| KP 58.8, 41.00 m | 4.0 / 11.6 h | 16.8 / 6.0 h |
| KP 60.0, 42.75 m | 5.0 / 11.2 h | 21.5 / 5.8 h |
| KP 62.0, 46.75 m | 3.9 / 6.8 h | 18.2 / 3.6 h |

Median foundation of each prior at 10 % / 50 % overload: 10.5 / 3.8 h (KP 57.4),
15.7 / 5.7 h, 21.9 / 8.0 h, 26.0 / 9.4 h. Pol's river base case, same calculation:
199.8 / 74.9 h; at the stage where its stationary probability is 0.1 (h_p 4.1 m,
D_p 48 h), median traverse 164 h against 67 h of head above critical (ratio 2.4).

## 9. Pol's river base case through this engine

Table 2 sampled crude-MC (N = 1e5, seed 20263030), r_e = 0.6, the engine's M6
for H_c (times m_p) and l_c, the numba M7 kernel at 225 s on the Fig. 6b trapezoid
from h0 = 0; D_p integrated by 7-point Gauss-Hermite on its lognormal plus a
separate 48 h column; h_p on a 0.1 m grid from 2.0 to 7.0 m. Deviations, stated:
Terzaghi heave gradient instead of i_c,h ~ LN(0.7, 0.1); no m_u; γ'_p = 16.87;
no flood fighting.

| First year, no flood fighting | P_stat | P_td | F_td |
|---|---|---|---|
| Gumbel(3, 0.25), Pol case 3d, this engine | 6.7e-3 | 1.4e-3 | 4.7 |
| Pol case 3d, published (method B, N_s = 1e4) | 7.3e-3 | 1.1e-3 | 6.5 |
| Gumbel(3.5, 0.25), this engine | 3.5e-2 | 7.9e-3 | 4.4 |
| Gumbel(4, 0.25) (base-case loading), this engine | 0.124 | 3.1e-2 | 3.9 |

The published case rests on about 11 time-dependent failures in 1e4, and Pol's two
methods differ by 1.5 for the base case (17 against 26), so 4.7 against 6.5 is a
reproduction within his precision; the heave deviation would, if anything, make
this engine's P_td smaller, not larger. Per flood at D_p = 48 h, at stages with at
least 30 time-dependent failures: F_td 4.5 to 6.2 where P_stat is 0.002 to 0.1, 3.0
at 0.46, 1.5 at 0.97; Δβ 0.49 to 0.71 over the first range. Tokachi at the same
P_stat: F_td 2.8 to 6.2, KP 60.0 and 62.0 on the Dutch curve and KP 57.4 and 58.8
below it (`time_factor_tokachi_rhine.png`).

**Reading.** Tokachi's pipes are about 8 to 20 times faster (k 10 to 30 times
higher, coarse matrix, 33 to 40 m paths) and its floods hold the head above
critical about 6 to 25 times shorter (2.7 to 11.6 h against 67 h), so the ratio of the two times, which is what
sets the factor, is of the same order in both cases. Like for like (one flood,
intact blanket, no flood fighting, no inter-event memory) Tokachi's annual factor
1.8 to 3.3 is below Pol's 6.5 (4.7 in this engine). His cumulative "< 5" includes
multi-year growth without recovery, and his first-year 17 to 38 includes flood
fighting; neither is the same quantity as anything computed here.

## 10. Thesis consequences

The thesis's RQ1 comparison, Table 5.1, Figure 5.x set, §5.2 to §5.5, §6.3 and
Table 6.1, §7.4 and Table 7.4, §8.1, Table 8.1, §8.3.1, §9.1 to §9.3, the Summary
and Appendix C.1 to C.3 move to this comparator (thesis session S25). Retired from
the main body: the equal-gross-head table, the head-first and head-last ladders,
the waterfall, the two separate design-anchor figures and the probability-share
figure of Appendix C.1. Superseded quotable numbers (gross-head comparison): Δβ
0.85 to 1.22, B 3.09 to 51.2 / >= 37, equal-convention retention 65 to 71 %, the
"one to about seven" sustained-to-finite factor as the thesis phrased it, LR 1.76 as
the criterion LR, annual 2.6 to 6.0. They remain correct for the gross-head
comparison and stay in their own study notes.

## 11. Expectations stated before the runs

Recorded in the session log before the measurements, not committed beforehand:
containment C4b ⊂ C3b would hold (it did, up to the documented Euler class);
C3b would be exactly invariant under the critical-length and canonical-event arms
(it was, bit for bit); the gate would contribute nothing at KP 62.0 (it did not
bind at any level); Pol's river case per flood would show a factor of the same
order as Tokachi's because the time scales balance (it did; the size was not
predicted).

## 12. Artifacts

| What | Where |
|---|---|
| Decision | `docs/decisions/0055-same-head-same-gate-steady-state-comparator.md` |
| This note | `docs/decisions/time-dependence-factor-study.md` |
| Evidence | `docs/decisions/time-dependence-factor-study.json` |
| Driver | `scripts/time_dependence_factor_study.py` |
| Gate | `tests/test_time_dependence_factor.py` |
| Figures | `docs/figures/same_head_fragility_log.png`, `same_head_initiation.png`, `same_head_survival_evidence.png`, `time_factor_vs_stage.png`, `time_factor_tokachi_rhine.png` |
| Re-run arms and caches | gitignored `results/time_dependence_factor/` |
