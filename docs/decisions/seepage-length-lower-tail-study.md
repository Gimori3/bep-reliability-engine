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
