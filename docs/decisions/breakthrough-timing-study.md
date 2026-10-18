# Study: when transient breakthroughs complete, relative to the flood peak

Date: 2026-10-16
Status: complete; no default, config, prior, kernel, persisted sweep, Phase 2
posterior or Phase 3 table changes.

> **Re-based at KP 57.4 under ADR-0059, 2026-10-17.** KP 57.4's aquifer-thickness
> prior mean was corrected from 7 m (the A_g gravel alone) to 12 m (the combined
> A_g + N_s thickness) and the evidence this note reads was regenerated (`breakthrough-timing-study.json`).
> Every KP 57.4 value in the prose below, and every range, ordering or count that
> includes KP 57.4, predates the correction and is kept as written; the committed
> JSON is the record and governs. Values at KP 58.8, 60.0 and 62.0 are unchanged. Summary and headline values:
> `0059-kp57-aquifer-thickness-correction.md` and the dated addenda of
> `docs/phase2_report.md`, `docs/phase3_report.md` and `docs/stage6_6_report.md`.

Evidence: `breakthrough-timing-study.json`, driver
`scripts/breakthrough_timing_study.py`. Inputs: the persisted production prior
sweeps `results/tokachi_kp*_historical_matrix.h5`. Only the adopted transient
branch is timed; the static comparator of record (ADR-0055) does not enter.

## 1. Question

The thesis (`msc-thesis-final` Section 8.5) argues that a check judged only up
to the end of the high-water period can miss pipes that are still crossing when
the river turns. The first-breach shares of ADR-0057/0058 already time each
failing realization's breakthrough against overflow, but no record gave the
timing against the peak itself. The question: for the adopted transient
criterion, what share of breakthroughs completes before the peak, while the
peak load acts, and later on the falling limb?

An earlier unquantified wording ("the progression model places the critical
instant after the peak") was too strong; this study replaces it with measured
shares.

## 2. Method

Matrix reading, prior realizations, KP 58.8 and KP 60.0 as if undrained,
canonical event `HPB_m064_1987` scaled to each grid stage, 225 s integration.
For every stored transient failure at the stage, the M7 kernel is re-run with
trajectory storage on the per-row inputs M8 computes
(`results_annotations_study._pipe_breach_times`); the re-run end states must
equal M8's and every stored failure must be re-timed, or the driver stops.
Breakthrough time follows the record time contract (ADR-0053): the end of the
hourly loading interval in which the pipe first reaches L. With `t_p` the peak
observation of the scaled record:

* before: `t <= t_p`;
* peak hour: `t_p < t <= t_p + 1 h` (completed while the peak load acts);
* after: `t > t_p + 1 h` (completed on the falling limb).

Every failing realization is timed (no subsampling).

## 3. Result

Shares of the transient failures at each stage, per cent.

| KP | Stage (m T.P.) | Failures in 1e5 | Before | Peak hour | After |
|---|---|---|---|---|---|
| 57.4 | 40.00 | 1,809 | 28.1 | 23.3 | 48.6 |
| 57.4 | 40.50 | 13,377 | 40.5 | 18.6 | 40.9 |
| 57.4 | 41.00 | 35,726 | 51.6 | 14.8 | 33.6 |
| 57.4 | 41.50 | 58,726 | 62.6 | 11.3 | 26.1 |
| 58.8 | 41.00 | 19,736 | 44.7 | 13.4 | 42.0 |
| 58.8 | 41.50 | 41,240 | 54.3 | 11.5 | 34.3 |
| 58.8 | 42.00 | 61,331 | 62.8 | 9.0 | 28.1 |
| 58.8 | 42.50 | 75,949 | 70.3 | 7.2 | 22.5 |
| 60.0 | 42.75 | 5,579 | 30.9 | 14.2 | 54.9 |
| 60.0 | 43.25 | 16,841 | 38.2 | 12.7 | 49.1 |
| 60.0 | 43.75 | 33,185 | 44.7 | 11.4 | 43.9 |
| 60.0 | 44.25 | 50,062 | 51.7 | 9.8 | 38.6 |
| 62.0 | 46.50 | 13 | 23.1 | 0.0 | 76.9 |
| 62.0 | 47.00 | 411 | 21.7 | 16.1 | 62.3 |
| 62.0 | 47.50 | 2,760 | 26.0 | 16.6 | 57.5 |
| 62.0 | 48.00 | 8,951 | 33.9 | 14.1 | 51.9 |

KP 57.4's design-grid stage (39.25 m) has no transient failure in 1e5 and
KP 62.0's (46.50 m) only 13, below the 30-failure count floor, so their lowest
quotable stages lie 0.79 and 0.61 m above the design levels.

Reading: at the design-grid stages of KP 58.8 and KP 60.0, 42.0 and 54.9 per
cent of breakthroughs complete more than an hour after the peak. A pipe whose
erosion head exceeds its critical head by a wide margin completes on the rising
limb; one that exceeds it only slightly is still crossing when the river turns
and completes while the falling river still exceeds the equilibrium head of the
lengthened pipe. Higher up the curves more pipes finish on the rising limb, so
the later share falls at every section (to 22.5 to 51.9 per cent at the
highest stages listed). The shares describe the canonical waveform only; they
are a model property, not an observed timing.

## 4. Verification

* The KP 58.8 41.00 m and KP 60.0 42.75 m rows reproduce, count for count, the
  thesis session S38 computation (`s38_breach_timing.py`, same helper, all
  rows); its 20,000-row subsamples at the larger stages agree within sampling
  error (KP 57.4 41.50 m: 62.4 / 11.5 / 26.2 against 62.6 / 11.3 / 26.1).
* An independent route through the frozen scalar API (`evaluate_realization`
  with `store_trajectory=True`, called per row with the sampled L as Phase 2
  does) reproduces the shares exactly on every row at KP 57.4 40.00 m (1,809),
  KP 58.8 41.00 m (19,736) and KP 60.0 42.75 m (5,579); its 5,000-row
  subsamples at KP 57.4 41.50 m, KP 58.8 41.50 m and 42.00 m agree within
  sampling error (for example 61.6 / 11.6 / 26.9 against 62.6 / 11.3 / 26.1).
  The scalar check is a session record, not a tracked driver.

## 5. Scope and limits

Prior branch only (the 2016 update rejects 16 of 1e5 realizations at KP 57.4
and none at KP 62.0, and the drained sections are not conditioned). One
canonical waveform; the shorter alternative event was not timed. The timing
resolution is one hourly loading interval. KP 57.4 values are subject to the
aquifer-thickness re-base the owner decided on 2026-10-16 (thesis ISSUES I278).
