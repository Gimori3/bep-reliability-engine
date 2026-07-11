# Japanese case validation 2: Yabe River 2012 — breach (R7.3k) vs survivals (R11.86k, L16.10k)

**Status: complete (2026-07-11). Verdict: the transient race condition ranks all
three sites in the observed outcome order (P_breach 0.061 / 0 / 0.0052 for
breach / survival / survival), and the Pol rate law brackets the observed
6.3 h initiation-to-breach interval across the committee's own As-permeability
case ladder — upper-tail at the central k, centred at intermediate k, robustly
reproduced (P≈0.90) at the coarse trench-As k that the committee itself
identified as the physical pathway. The first field test of M7/C_e passes,
conditional on the pre-registered k hinge.**

Source: 矢部川堤防調査委員会報告書 (Yabe River Levee Investigation Committee
report, March 2013; `docs/references/houkokusyo_compressed.pdf` — text layer
extractable via PyMuPDF). Harness: `scripts/validate_yabe.py` (pre-registered
design in the module docstring; results in
`results/validation_yabe/validation_results.json`); figures:
`scripts/plot_validation_yabe.py` → `docs/figures/validation_yabe_*.png`.
Standalone: frozen public APIs only; per-site `evaluate_batch` cross-checks and
a forced-loop Δt-halving guard passed on every run.

## 1. The case

July 2012 northern-Kyushu rains. Right bank 7.3k (delta lowland, clay levee on
Ariake clays) breached at **13:15–13:30 JST on 2012-07-14** (CCTV + firefighter
+ resident accounts; 13:20 adopted) **without overtopping** — the committee
excluded overtopping (CCTV/witnesses/trace levels), erosion, and
through-embankment seepage, attributing the breach to foundation piping through
the **As sand layer** (1–1.5 m in borings, 1.8–1.9 m at the excavation)
sandwiched between the Fc cover clay and the Ac clayey silt, connected to the
riverbed via the floodplain Fg gravel at the riverside toe. Two further sites
initiated but survived the same flood: **R11.860k** (boils + toe settlement;
Dg sand-gravel aquifer ~10 m under 2.4 m cover) and **L16.100k** (boils, no
levee deformation; Dg ~5 m under ~1.6 m cover).

The observed timeline at 7.3k: hinterland wells surging from **~07:00**
(resident interview — independently matching the committee case-2 FEM's G/W<1
onset at 07:00; their case-4 model with the trench-confirmed Fg–As connection
gives 02:00); committee summary: pressure sufficient to rupture the cover and
form a water path **~1 h before breach** (~12:20, the case-4 G/W minimum);
surface boil observed **13:00–13:10**; crest asphalt already slumped ~0.5 m on
the firefighters' arrival; vertical collapse of a <1 m-wide section at
**13:15–13:20**; widening upstream to ~50 m by 15:30. River at 7.3k (committee
unsteady-flow computation): above HWL (T.P. 7.225) from ~08:00 for ~6 h, peak =
trace level 8.36 at ~12:00, falling below HWL ~14:00.

## 2. Design (pre-registered; user steer applied)

Two isolated tests, because Gounokawa showed the M5 gate fires ~2.3× early and
must not set the progression clock for the first real C_e test:

* **T1 timeline (M7/C_e isolation, 7.3k):** the gate is FORCED open at a
  committee-documented anchor (A1 02:00 case-4 G/W<1; **A2 07:00 primary**,
  case-2 G/W<1 + wells; A3 12:20 committee water-path statement; A4 13:05
  surface boil), and the Pol rate law runs on the digitized stage record.
  Endpoints: t(l≥l_c), t(l≥L/2) (cavity under the crest — the field's
  structural proxy), t(l≥L) (engine breach). Implemented with the public
  `progression_rate`/`equilibrium_head` kernels; the positive-part operator
  means forcing the gate never manufactures overload.
* **T2 discrimination (full chain, all three sites):** engine's own gate;
  N = 10⁵ LHS per site (thesis CoVs, ADR-0026 C_e, two-population coupling,
  open entry); P_breach, P_static-exceeded, l_e distributions vs outcomes.

Verdict-critical choices, flagged in advance: (i) the As permeability — the
committee's own case ladder spans 3.4e-4 m/s (case 2/4 central, D20-based) to
3.1e-3 m/s (case 3/5, the coarse gravel-mixed trench-As **actually connected to
the Fg at the breach front**); run as a three-step variant ladder. (ii) As d70
= 0.35 mm from the toe-boring family of Fig. 4.2.50-③ (the trench family is
2–20 mm — a within-layer matrix/framework split; committee-k + matrix-d70 is
the ADR-0012 pairing); (iii) z_toe/D_bl/γ from the committee models'
initial-head and cover-weight arithmetic (G ≈ 18 kPa over 1.05 m at 7.3k, both
reproduced by their case-1/case-2 G/W values); (iv) hydrographs digitized as
control points against text anchors. Survival-site Dg d70 ≈ 5 mm is far
outside the Sellmeijer domain — those H_c are extrapolations, but the
direction (coarse → high resistance → stall) is the committee's own mechanism
(p4-106: survival because the Dg's "larger grain size and greater thickness"
made void progression slower — a progression-rate explanation, i.e. exactly
the transient race condition).

Inputs per site (committee values unless marked): see `SITES` in the harness.
7.3k: k_aq 3.4e-4, d70 3.5e-4 (READ-OFF), D_aq 1.5, D_bl 1.05, k_bl 1e-7
(ASSUMED, Bc/Ac class), γ'_bl 7.3, z_toe 3.2, L 30 (READ-OFF 20–40).
11.86k: k 1.3e-4, d70 5e-3 (READ-OFF), D_aq 10, D_bl 2.4, z_toe 8.3, L 35.
16.10k: k 4e-4 (avg ASSUMED from max 9.4e-4), d70 5e-3, D_aq 5, D_bl 1.6,
z_toe 7.5, L 40.

## 3. Results

**T1 timeline (primary anchor A2 = 07:00; observed interval 6.33 h):**

| As k [m/s] | P(l≥l_c) | t_lc med | P(l≥L) | t_full med [5–95%] | P(breach ≤ observed 6.33 h) |
|---|---|---|---|---|---|
| 3.4e-4 (case 2/4 central) | 0.72 | 2.2 h | 0.060 | 6.1 [3.4–13.3] h | 0.035 |
| 1.0e-3 (intermediate) | 0.99 | 0.7 h | 0.53 | 4.9 h | 0.41 |
| 3.1e-3 (case 3/5 coarse trench-As) | 1.00 | 0.2 h | 0.96 | 2.6 h | 0.90 |

The observed breach time sits **inside the predicted band across the
committee's documented k range**: ~96th percentile at central k, ~50–60th at
intermediate, ~10th (model faster than observed) at coarse. From A3 (12:20,
1 h to breach), the point of no return l_c is reached within the hour by
55–93% of realizations across the ladder — the committee's "water path forms
~1 h before breach" narrative is consistent with the engine's l_c timing even
at central k. The structural proxy l≥L/2 behaves like l≥L (0.12/0.67/0.98 by
the observed time across the ladder from A2).

**T2 discrimination:**

| Site | Observed | P_init | P(transient breach) | P(static exceeded) | H_c med | l_e med/90% |
|---|---|---|---|---|---|---|
| R7.3k | **breach 13:20** | 1.00 | **0.061** | 0.82 | 4.3 m | 3.6 / 21.4 m |
| R11.86k | boils + toe settlement | 1.00 | **0.000 (0/10⁵)** | 0.000 | 12.6 m | 1.6 / 2.2 m |
| L16.10k | boils only | 1.00 | **0.0052** | 0.126 | 11.5 m | 3.7 / 5.0 m |

Both branches rank the three sites in the observed order; the transient branch
is 12× sharper at the survival end (7.3k:16.10k breach-probability ratio 12 vs
static 6.5, and 16.10k static leaves 12.6% exceedance mass at a site with no
levee deformation). All three sites initiate with probability ~1 — matching
the field (boils everywhere) and confirming initiation-level indicators cannot
separate the outcomes (the committee's own G/W minima agree: 0.62 breached vs
0.65 survived). The separation lives in the progression physics: fine thin As
(H_c ≈ 4.3 m < peak head 5.16 m ⇒ the race can run) vs coarse thick Dg
(H_c ≈ 11–13 m ≫ head ⇒ stall at metres). **This is the core-thesis result:
time-dependent progression, not initiation severity, separates breach from
survival on the Yabe, and the committee's own mechanistic reasoning says the
same thing.**

Mean-θ verdict scan over the read-off hinges (k × d70 × L, 27 cells): the
breach/no-breach verdict flips inside the plausible box exactly as
pre-registered — breach at all L for the coarse k; breach at L=20 m for
central k; stall for the case-1 field-test k (2e-5, the model the committee
itself effectively rejected because it kept G/W > 1). The engine puts 7.3k on
the breach margin at central parameters and deep in the breach zone along the
committee's own preferred (coarse-pathway) axis.

**M4 cross-check against the committee FEMs** (peak toe overpressure over
ground): engine (median r_e, instantaneous) vs FEM: 7.3k 3.6 vs 1.85 m
(2.0×); 11.86k 2.7 vs 2.4 m (1.13×); 16.10k 6.9 vs 2.6 m (2.7×). The
instantaneous Mazure translation over-predicts the toe head by ~2–2.7× at the
thin/dead-ended aquifers (7.3k As terminates mid-hinterland; both models use a
landside canal boundary ~100–120 m out) and nearly matches at the thick
transmissive Dg (11.86k). This **partially re-attributes the Gounokawa F2
conservatism**: part of that ~2.3× "gate bias" is M4 over-translation under
transient/finite-aquifer filling, not exit resistance alone — exactly what the
queued Shikaga M4-vs-FEM cross-check should separate. ADR-0032 diagnostic:
Π = 0.018/0.26/0.04 — 11.86k formally flags the lag (Π > 0.1), yet is the
*best*-matched site, and 7.3k/16.10k pass the Π screen yet over-translate:
the governing damping here is unsaturated/finite-aquifer filling, which the
S_s-based τ_aq does not capture. Noted for the ADR-0032 scope; instantaneous
retained everywhere (conservative, and common-mode across the three sites).

## 4. Findings

**Y1 — first field pass of the transient race condition.** Breach vs survival
under one flood is reproduced in ranking and (conditional on the k hinge) in
probability mass, with the committee's own explanation of the survivals being
the same rate mechanism. The engine's discriminating variable (H_c vs peak
erosion head, i.e. d70/D_aq through F_s/F_g) coincides with the committee's
"larger grains, thicker layer".

**Y2 — the Pol rate law is not falsified on the only observed
initiation-to-breach clock in the set; C_e at the fast end.** At committee-
central k the observed full breach is upper-tail (P ≈ 0.04–0.06); the
mechanistically favoured coarse-pathway k reproduces it robustly. Under the
ADR-0026 C_e prior this reads as: the Yabe event sits on the fast side of the
prior — consistent with Pol's field prior being a conservative mean over a
wide range and with cavity growth by fines washout plausibly outpacing
grain-by-grain pipe elongation. No re-calibration is warranted from one event;
Phase 2's C_e filtering direction (survival ⇒ slower) should simply note that
the one breach observation pulls the other way.

**Y3 — within-layer two-population split, third occurrence.** The As layer
itself carries a fine matrix (d70 0.35 mm, in-domain) and a coarse
gravel-mixed framework (trench; k up to 3.1e-3 m/s) — and the breach verdict
hinges on pairing the committee's framework k with the matrix d70 (ADR-0012
logic). After Gounokawa (sand-over-gravel) and the survival sites' Dg, every
Japanese case so far demands the framework/matrix distinction somewhere in the
chain.

**Y4 — morphology: no discrete pipe, third case.** The committee's mechanism
is fines washout (≤0.1 mm mobile at their computed velocities) growing
voids/cavities under the levee → settlement → washout; the post-repair
excavation found the As sandwich and observed seepage-with-sand-transport, not
a pipe remnant (breach zone washed out, scour pond formed). With Gounokawa
(veins/clods, no pipe) and Tokoro (networked sand-filled cracks, no pipe),
**no Japanese case in this set documents a discrete Sellmeijer/Pol-style
pipe**. The Pol single-equilibrium-pipe abstraction is doing its work as an
effective rate model, not as literal morphology — synthesis line, and a reason
the l≥L endpoint should be read as an analog of "cavity system spans the
foundation", with l≥L/2 (undermined crest) the closer structural proxy.

**Y5 — M4 over-translation at thin/dead-end aquifers (2.0–2.7×), near-exact at
thick ones.** See §3; feeds the Gounokawa F2 re-attribution and sharpens what
Case A (Shikaga) must test.

## 5. Limitations

Digitized hydrographs (control points in the harness; text anchors honoured);
L read off small sections (±10 m; verdicts stable except the pre-registered
central-k L=20 flip); k_bl for Fc assumed (1e-7 m/s, Bc/Ac class); survival
sites' H_c far out of the Sellmeijer calibration domain (direction robust,
magnitude not); the l≥L breach endpoint is a mechanism analog (Y4); the
timeline test conditions on committee FEM anchor times, inheriting their model
error at A1/A2 (mitigated by the independent 07:00 well observation and by
reporting all four anchors); single flood, three sections — no claim of
statistical power beyond ranking + one timeline.

## 6. Reproduction

```powershell
python scripts/validate_yabe.py        # ~4 min: T1 ladder + T2 + guards
python scripts/plot_validation_yabe.py # writes the two PNGs
```
