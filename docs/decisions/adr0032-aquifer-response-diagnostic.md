# ADR-0032 companion: the aquifer-response diagnostic (Part 2 execution)

Date: 2026-07-11 (figure: `../figures/adr0032_aquifer_response.png`; driver:
`scripts/aquifer_response_diagnostic.py`; package: `hydraulics.py`
`aquifer_response_diagnostic` + `AQUIFER_RESPONSE_*` constants,
`hydrographs.flood_timescales`; wiring: `run.py` `_aquifer_response_block` →
`metadata['aquifer_response']`)

This is the numeric backing for ADR-0032's Outcome section. ADR-0032 itself
holds the pre-registration (Part 1) and the verdict (Part 2); this note records
how the numbers were obtained, so the run can be reproduced and re-read.

## Question

Spec §11 gates the M4 hydraulic-translation form on a diagnostic that compares
the aquifer response time τ_aq ~ λ_in²·S_s/k_aq (≡ S_s·D_aq·D_bl/k_bl; k_aq
cancels) against a characteristic flood duration, plus a separate check that the
native d4PDF cadence resolves the flashy peaks. The M4 lag machinery (ADR-0004,
`LaggedHead`) and the config fields (`aquifer_lag_active`, `specific_storage_per_m`)
were built long ago (ADR-0014) with this diagnostic named as their deferred
consumer — but the diagnostic had never been run for any Tokachi section. Should
the production sweep use the instantaneous default or the linear-reservoir lag?

The decision is a one-way conservative gate, so the methodology was split: all
discretionary inputs (S_s range, the T_rise denominator, the threshold, the
governing set) were **pre-registered** before any τ_aq was computed (ADR-0032
D1–D5), then applied unchanged here.

## Method

- **τ_aq** from the production LHS prior (N = 10⁵), the same
  `run._sample_prior` call the sweep makes, at the pre-registered decision-driver
  S_s = 1×10⁻⁴ m⁻¹ (range upper bound — worst case, τ_aq ∝ S_s). Reported as the
  central (prior-mean) value, the 90th-percentile-τ_aq corner (high D_aq, high
  D_bl, low k_bl, via lognormal quantiles), and the empirical sample percentiles.
- **Flood timescales** from `hydrographs.flood_timescales` on the pinned
  canonical event `HPB_m064_1987` and a peak-discharge-stratified spread of ~140
  HPB members, each built at the node's own Eq. 4.19 rating (stage domain — what
  M5/M7 consume). T_rise = base(10%)-to-peak on the final rising limb (the Π
  denominator); T_plateau = width within 10% of the peak (the Check-B feature).
- **Rules** (`hydraulics.aquifer_response_diagnostic`): Check A activates the lag
  if Π = τ_aq/T_rise > 0.10 at either governing section (central θ, driver S_s),
  with a secondary activation-only grey-zone rule on the 90th-pct corner; Check B
  requires Δt_native ≤ T_feature/2 (Nyquist).

## Governing sections

KP58.8 and KP60.0 (ADR-0032 D5): the two drained sections carry the thickest
blankets (0.85 m) over the lowest blanket conductivity (1×10⁻⁶ m/s), so the group
D_aq·D_bl/k_bl that sets τ_aq is largest there and **upper-bounds** KP57.4 and
KP62.0; they are also the two sections whose transient transition the grid
brackets (ADR-0031), so they are where an activated lag would perturb the
deliverable. KP63.4 has no blanket data (k_bl = NaN) and is excluded.

## Result (S_s = 1×10⁻⁴ m⁻¹, driver; `--members 150`, seed 20260626)

| quantity | KP58.8 | KP60.0 |
|---|---|---|
| τ_aq central (prior means) | 680 s (0.19 h) | 765 s (0.21 h) |
| τ_aq 90th-pct corner | 1921 s (0.53 h) | 2161 s (0.60 h) |
| τ_aq sample p50 / p90 / p99 / max | 745 / 1440 / 2453 / 6617 s | 838 / 1619 / 2760 / 7444 s |
| T_rise (10%→peak) median / 10th-pct | 18 h / 10 h | 18 h / 10 h |
| T_rise 10%→90% median | 14 h | 13 h |
| T_plateau (≥90%) median | 9 h | 9 h |
| T_fwhm (≥50%) median | 37 h | 36 h |
| canonical HPB_m064_1987 rise / plateau / FWHM | 23 / 10 / 55 h | 23 / 10 / 55 h |
| **Π central** | **0.010** | **0.012** |
| Π corner90 | 0.030 | 0.033 |
| Π stress (sample p99 / flashiest T_rise) | 0.068 | 0.077 |
| Check A (Π ≤ 0.10) | PASS | PASS |
| Check B (3600 s ≤ T_feature/2 = 16200 s) | PASS | PASS |

Every Π in this table divides by the **ensemble-median T_rise, 18 h = 64 800 s**
— the population figure, and the more conservative of the two available
denominators. See "Two margins" below before quoting any of these against the
per-run `margin_vs_threshold`.

## Verdict

**Instantaneous default retained** for the production sweep, at both governing
sections and — by the bounding argument — everywhere. τ_aq is 1–2 orders of
magnitude below the flood rising-limb time; the grey-zone rule is not triggered.

Two findings worth carrying into the write-up:

1. **The loading is not flashy at the governing (Tokachi-mainstem) nodes.** The
   spec's "~1.5 h plateau" worry does not survive contact with the routed d4PDF
   hydrographs: median rising-limb 18 h, plateau 9 h, FWHM 37 h (left panel of
   the figure — every member sits far right of the 1.5 h marker). The large-basin
   routing plus the √-rating broaden the stage peak. This makes both checks pass
   comfortably; any genuinely flashy loading would be a smaller-tributary
   (Satsunai) question, and no BEP governing section here is on that tributary.
2. **S_s does not bind.** Because Π_central clears at the *upper-bound* S_s by
   ~10× (Π\*/Π_central = 9.5 / 8.5 at the ensemble-median T_rise), S_s
   would have to leave the dense sand-gravel class by an order of magnitude
   (~10⁻³ m⁻¹) before the gate flipped. The D4 sanity-check flag (still worth
   confirming with the soil-mechanics collaborator on general grounds) therefore
   does not gate this verdict.

Neglecting the (small) lag over-predicts the peak head, i.e. is conservative on
transient P_f — so even the far-tail triple-conjunction (≳p99.9 τ_aq × flashiest
event × upper-bound S_s ≈ Π 0.18–0.21 for a vanishing row fraction) does not
move the decision.

## Two margins, both correct (added 2026-07-31 — a labelling gap, not a discrepancy)

Two different margin figures for this one gate circulate in the repository, and
until now nothing said they measure different things. **Neither number is
wrong.** They differ in *which Π* is divided into Π\* = 0.10, and in *which
T_rise* is divided into τ_aq:

| figure | numerator τ_aq | denominator T_rise | where it appears |
|---|---|---|---|
| **~10×** | central (prior means) | ensemble median, 18 h = 64 800 s | this note, ADR-0032, `architecture.md` §11/§13, architecture and decision records |
| **3.8–19.5×** | 90th-percentile corner | the run's own canonical event, 23 h = 82 800 s | `metadata['aquifer_response'].margin_vs_threshold`, `production_campaign_2026-07-29.md` §9.2 |

The **numerator** difference is the substantive one and is pre-registered:
ADR-0032 D3 defines the 90th-percentile τ_aq corner (high D_aq, high D_bl, low
k_bl) as the secondary grey-zone instrument, so `margin_vs_threshold` is
deliberately the *stricter* of the two. Check A itself — the decision — is
Π_central ≤ Π\*, and it is the ~10× figure that reports its margin.

The **denominator** difference is a scope difference, not a disagreement:

- This note and ADR-0032 take T_rise as the **median over ~140 HPB members**
  (18 h). That is a statement about the loading population, and it is the
  conservative choice (a shorter rise gives a larger Π).
- `run.py` stamps the diagnostic for the loading that run actually used, so its
  denominator is the pinned canonical event `HPB_m064_1987`'s own rising limb
  (23 h; the sidecar's `t_rise_s = 82800.0`).

τ_aq is **identical** in both — 680.0 s at KP 58.8, 765.0 s at KP 60.0 — so the
two Π values are the same quantity over different denominators and reproduce
each other exactly: 680/64 800 = 0.0105 → the published **0.010**, and
680/82 800 = 0.00821 → the stamped `pi_central`. The published range
"Π ≈ 0.010–0.012" is therefore **not** in tension with the measured 0.00821–0.00924;
it is the same τ_aq divided by the shorter, population-median rise. Nothing to
reconcile and no number to change — only the denominator to state, which every
occurrence now does.

Both definitions clear Π\* at every section, so the verdict is invariant to the
choice:

| section | τ_aq central | τ_aq corner90 | Π\*/Π_central (18 h) | Π\*/Π_central (run) | Π\*/Π_corner90 (run) |
|---|---|---|---|---|---|
| KP 57.4 | 350 s | 989 s | — | 23.7 | **8.37** |
| KP 58.8 | 680 s | 1921 s | **9.5** | 12.2 | **4.31** |
| KP 60.0 | 765 s | 2161 s | **8.5** | 10.8 | **3.83** |
| KP 62.0 | 150 s | 424 s | — | 55.2 | **19.54** |

(The 18 h column exists only for the two governing sections, which are the only
ones this study characterized; the run column covers all four because `run.py`
stamps the block everywhere.)

## Pre-registered bounding pair confirmed at all eight strata (2026-07-31)

ADR-0032 D5 named KP 58.8 and KP 60.0 as the τ_aq-bounding governing pair
**before any τ_aq was computed**, on the argument that they carry the thickest
blankets (0.85 m) over the lowest blanket conductivity (1×10⁻⁶ m/s), so the
group D_aq·D_bl/k_bl is largest there. The 2026-07-29 production campaign
stamped the block into all eight strata for the first time, which extends that
prediction to sections it was never checked against. It holds:

- τ_aq central 765 s (KP 60.0) and 680 s (KP 58.8) are the **two largest** of
  the four, ahead of KP 57.4 (350 s) and KP 62.0 (150 s) — a factor 2.2 and 5.1
  clear of the pair. The Π ordering is the same, since all four runs share the
  canonical event's T_rise.
- Consequently the pair also carries the **smallest** margins (Π\*/Π_corner90
  = 3.83 and 4.31 against 8.37 and 19.54), i.e. the bounding argument bounds in
  the direction claimed.
- All four sections pass at **both** Π definitions, and the verdict is
  `instantaneous` in **8 of 8** strata (both d_70 interpretations).

A pre-registered bound that held when extended to the full stratum set is worth
having on the record: nothing about the verdict rests on the two sections having
been chosen after seeing the numbers, because they were not.

## Reproduce

```
python scripts/aquifer_response_diagnostic.py            # --members 150 default
python scripts/aquifer_response_diagnostic.py --no-plot  # numbers only
```

The verdict is stamped into every production result at
`metadata['aquifer_response']` (descriptive; the active form remains the global
`metadata['aquifer_lag_active']`).
