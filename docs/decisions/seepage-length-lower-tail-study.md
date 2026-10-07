# Study note: the lower tail of the seepage-length prior (Pol round 2, A35 and A34)

Date: 2026-10-07. Status: **Part 1 pre-registered**; Part 2 records the outcome.
Driver: `scripts/results_annotations_study.py seepage`. Evidence:
`seepage-length-lower-tail-study.json`. Companion until the owner decides; no
default, config, prior, kernel, persisted sweep, posterior or production annual
result changes here. Builds on `seepage-length-L-study.md` and ADR-0047.

## Part 1. Pre-registration

### 1.1 The question

Pol, p. 37, on CoV(L) = 0.20: *"standard deviation of 7 m implies a lower
characteristic value of around 20 m. Is this realistic?"* And p. 36, on excluding
the foreshore from L: *"in case of thick clayey foreshores, L may include part of
the foreshore. But in this case with blankets < 1 m, I agree to exclude it from L
since there are likely cracks in it that facilitate a hydraulic shortcut."*

L is lognormal around the toe-to-toe footprint (33 / 35 / 34.8 / 40 m, CoV 0.20 /
0.20 / 0.15 / 0.20); its 5th percentiles are about 23 to 28 m. By definition L runs
from the riverside levee toe to the landside exit, and the L memo sets the landside
boundary at the toe; the CoV padding above the reading scatter was assigned for an
exit *beyond* the toe (`seepage-length-L-study.md` 1.1 to 1.2), an upward
uncertainty. A path much shorter than the footprint needs an entry or an exit inside
the embankment. The downward uncertainty the evidence supports is the footprint
itself: the 1998 reading range at KP 58.8 (31 to 40 m) and the along-levee variation
on the 2025 lidar, whose shortest clean station within 300 m either side is
0.85 to 0.86 of the local median at all three resolvable sections (34/40, 36/42,
37/43 m; ADR-0047 JSON), before the extraction rule's known 2 m short bias.

### 1.2 What is computed

L is sampled independently of theta, so the prior truncated below at `t * mean(L)`
is sampled exactly by keeping the persisted rows with `L_j >= t * mean(L)` (the
regenerated `run.seepage_length_samples`). No new physics run. Truncation points
`t` = 0.70, 0.80, **0.85** (the measured along-levee minimum), 0.90 and **1.00** (the
definitional bound: no entry or exit inside the footprint). For each, matrix reading,
KP 58.8 and 60.0 as if undrained:

1. Per flood: transient and same-head static probabilities on the stage grid, the
   index difference and time-dependence factor at the design anchors (with paired
   intervals and the count floor), the lower-shoulder ratio to the adopted value.
2. The 2016 update: rejected share among retained rows, likelihood ratio.
3. Annual: the truncated posterior curve rebuilt as M9 and annualised by the
   production pipeline (gated); system, piping, shares, ordering, climate ratios,
   the annual steady-state over transient factor; hazard-sampling intervals.
4. Sensitivity ranking: the first-order correlation ratio of the transient failure
   indicator on each input at the GSA stages, truncated and not (the
   `seepage-length-L-study.md` probe, validated against the Sobol first-order index).

### 1.3 Predictions

- **S1.** At t = 0.85 the lower-shoulder transient probability falls to 0.4 to 0.8 of
  the adopted value; at t = 1.00 to 0.15 to 0.5. The same-head static probability falls
  less than the transient one at every quotable stage.
- **S2.** At t = 0.85 the design-anchor index difference changes by less than 0.10
  and the time-dependence factor by a factor of 0.8 to 1.4; neither changes sign.
- **S3.** At t = 0.85 the 2016 rejection at KP 58.8 falls from 3.8 % to between 2.0 and
  3.3 %, because rejections concentrate among short paths.
- **S4.** At t = 0.85 the historical annual piping probability falls to 0.6 to 0.9 of
  the adopted value at every section; at t = 1.00 to 0.3 to 0.7.
- **S5.** At t = 0.85 no leading mechanism changes; at t = 1.00 the KP 62.0 warming cell
  moves toward overflow and no other cell changes.
- **S6.** The climate ratios rise by a factor of 1.0 to 1.3, because the truncation
  suppresses historical stages more than warming ones.
- **S7.** At t = 0.85, L remains the largest first-order input at KP 58.8's design
  stage; at t = 1.00 conductivity overtakes it.

A prediction that fails is reported as failed.

## Part 2. Outcome

Run 2026-10-07 on the persisted rows (10^5 per section; the 10^6 ladders of
`results/hwl_bias_resolution/` for the KP 57.4 and KP 62.0 anchors, truncated on
their own persisted L). Gates: the untruncated arm reproduces the production
annual table field for field; the sampled L means lie within 1 % of the adopted
means; the hazard cache is unchanged.

### 2.1 What the prior's lower tail is

| Section | mean L (m) | CoV | 5th pct (m) | shortest sampled (m) | rows kept at t = 0.85 / 1.00 |
|---|---|---|---|---|---|
| KP 57.4 | 33.0 | 0.20 | 23.4 | 13.4 | 76.5 % / 46.1 % |
| KP 58.8 | 35.0 | 0.20 | 24.8 | 14.3 | 76.5 % / 46.1 % |
| KP 60.0 | 34.8 | 0.15 | 26.9 | 17.8 | 84.5 % / 47.0 % |
| KP 62.0 | 40.0 | 0.20 | 28.3 | 16.3 | 76.5 % / 46.1 % |

The shortest clean lidar station within 300 m of each resolvable section measures
34, 36 and 37 m (KP 62.0, 58.8, 60.0) against local medians of 40, 42 and 43 m:
0.85 to 0.86 of the median, before the extraction rule's 2 m short bias. No
mechanism in the L memo places an entry or exit inside the embankment footprint.
At t = 0.85 the bounded prior keeps every path down to 28 / 30 / 30 / 34 m.

### 2.2 Per flood (matrix reading, as if undrained, prior)

| Quantity | adopted | t = 0.85 | t = 1.00 |
|---|---|---|---|
| KP 58.8 design grid 41.00 m: P_trans / P_static | 0.197 / 0.450 | 0.106 / 0.337 | 0.045 / 0.205 |
| KP 58.8: Δβ [95 %], F_td | 0.72 [0.72, 0.73], 2.28 | 0.83 [0.82, 0.84], 3.20 | 0.88 [0.86, 0.89], 4.59 |
| KP 60.0 design 42.75 m: P_trans / P_static | 0.0558 / 0.216 | 0.0298 / 0.159 | 0.0098 / 0.081 |
| KP 60.0: Δβ, F_td | 0.81 [0.80, 0.82], 3.88 | 0.88 [0.87, 0.90], 5.33 | 0.94 [0.91, 0.97], 8.26 |
| KP 62.0 design 46.39 m, 10^6: k_static / k_trans | 350 / 51 | 3 / 0 | 0 / 0 |
| KP 62.0 46.75 m, 10^6: k_static / k_trans | 6,089 / 972 | 419 / 26 | 42 / 1 |
| KP 57.4 39.50 m, 10^6: k_static / k_trans | 561 / 163 | 14 / 1 | 1 / 0 |
| lowest stage with 30 transient failures: P_trans ratio to adopted (KP order) | 1 | 0.04 / 0.04 / 0.23 / 0.03 | 0.015 / 0.018 / 0.055 / 0 |

Over the 49 attainable stages where every count reaches 30, t = 0.85 multiplies
F_td by 1.02 to 2.44 and raises Δβ by 0.04 to 0.17 (t = 1.00: 1.06 to 3.06, +0.04
to +0.20). The lower shoulder of the transient curve, and the design levels of the
two sections loaded deepest in their tails, rest almost entirely on paths shorter
than any measured footprint; the time effect grows when they are removed,
because short paths are where pipes cross fastest and both rules fail together.

### 2.3 The 2016 update (as if undrained)

KP 58.8 rejection 3.813 % → 1.013 % (t = 0.85) → 0.287 % (t = 1.00); LR
1.34 → 1.20 → 1.09. KP 60.0 0.226 → 0.058 → 0.013 %. The exit still opens in
99.5 % (KP 58.8) and 99.2 % (KP 60.0).

### 2.4 Annual (adopted conditioning, ADR-0056; part `seepage_adopted`)

| Cell | annual piping, t = 0.85 / adopted [95 %] | t = 1.00 / adopted | climate ratio, adopted → t = 0.85 |
|---|---|---|---|
| KP 57.4 hist | 0.51 [0.40, 0.57] | 0.22 | 15.3 → 22.3 |
| KP 58.8 hist | 0.69 [0.64, 0.73] | 0.44 | 5.6 → 6.2 |
| KP 60.0 hist | 0.60 [0.55, 0.64] | 0.24 | 13.3 → 16.4 |
| KP 62.0 hist | 0.51 [0.45, 0.55] | 0.23 | 13.4 → 18.6 |
| +4 K, KP order | 0.74 / 0.77 / 0.75 / 0.66 | 0.52 / 0.56 / 0.43 / 0.40 | |

Leading mechanism at t = 0.85: unchanged in seven cells; KP 62.0 under +4 K
becomes an overflow lead under every split (summed 0.38, overflow-first 0.20,
piping-first 0.49). At t = 1.00 KP 62.0 historically becomes a tie (summed 0.47).
The annual steady-state over transient piping factor rises from 2.05 / 1.84 /
3.32 / 3.12 to 2.53 / 2.08 / 3.95 / 4.09 historically (posterior at all four; part
`seepage`).

### 2.5 Sensitivity ranking (first-order correlation ratio of the transient indicator)

KP 58.8 design 41.00 m: L 0.24, k_aq 0.20 (adopted); k_aq 0.23, L 0.08 (t = 0.85);
k_aq 0.20, L 0.03 (t = 1.00). KP 60.0 design: k_aq 0.16, L 0.10 → k_aq 0.16, L 0.03.
KP 58.8 at 40.25 m: L 0.076, k_aq 0.060 → k_aq 0.031, L 0.004. Once the
unmeasured short paths are removed, aquifer conductivity is the leading input.

### 2.6 Predictions

All seven failed or partly failed in size, every one in the same direction: the
lower tail matters more than predicted.

- **S1 failed in size.** At t = 0.85 the lower-shoulder transient probability is
  0.03 to 0.23 of adopted (predicted 0.4 to 0.8); at t = 1.00 0 to 0.055 (predicted
  0.15 to 0.5). The static probability falls proportionally less at every quotable
  stage, as predicted.
- **S2 partly failed.** Δβ rises by 0.107 at KP 58.8 (predicted below 0.10) and by
  0.077 at KP 60.0; F_td by ×1.40 and ×1.37 (inside 0.8 to 1.4); no sign change. The
  KP 57.4 and KP 62.0 design anchors become unresolved.
- **S3 failed.** KP 58.8 rejection 1.01 % (predicted 2.0 to 3.3 %).
- **S4 failed at KP 57.4 and 62.0** (0.51 against a predicted floor of 0.6) and, at
  t = 1.00, at three sections.
- **S5 failed.** At t = 0.85 KP 62.0 under +4 K turns to overflow; at t = 1.00 KP 62.0
  historically ties.
- **S6 failed at KP 57.4 and 62.0** (×1.46 and ×1.39 against at most 1.3).
- **S7 failed.** At t = 0.85 conductivity, not L, leads at KP 58.8's design stage.

### 2.7 Recommendation and decision

Recommended to the owner, and decided on 2026-10-07: the adopted prior is kept;
the prior bounded at the shortest measured footprint (t = 0.85) is a named
alternative, and the unbounded lower tail joins the piping-favouring adopted
choices. Adopting it would move every result of Chapters 5 to 7 and leave the
KP 57.4 and KP 62.0 design comparisons unresolved.

The foreshore is excluded from L because the thin foreland cover (less than a
metre at these sections, discontinuous in the later boreholes) is unlikely to
seal the aquifer from the river across the high-water bed; this is the study's
own physical argument, stated without a citation, as no source read for it
(TR Zandmeevoerende Wellen 1999 sections 4.2.1 and 4.4.2 only permit a foreland
credit) makes it.
