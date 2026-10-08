# Study: the loading the thesis relies on, shown and set in context (Pol round 2, A25, A29, A32)

Date: 2026-10-08 (Pol feedback round 2, session 8 of 9)
Status: Part 1 (the questions, the sources, the checks already made and the
pre-registration) is committed on its own, before any statistic of Part 2 was
computed. Part 2 records the outcome.

Evidence: `loading-context-study.json`, driver `scripts/loading_context_study.py`,
gate `tests/test_loading_context_study.py`. New committed data extract:
`data/processed/2016_event/stage_hourly_Tokoro_201608.csv`, written by
`scripts/fetch_tokoro_2016_stage.py`.

No production default, config, prior, kernel, persisted sweep, Phase 2
posterior or Phase 3 table changes. Everything below is descriptive loading
evidence and two figures.

## 1. The questions

Joost Pol annotated the 11 September 2026 thesis (49 notes). Three of them ask
the thesis to show the loading it relies on:

- **A25** (p. 14, the August 2016 typhoons): "Would be very helpful to have a
  figure of the 2016 hydrograph for the 3 rivers mentioned." The three rivers
  are the Tokachi, the Satsunai and the Tokoro. Pol session 4
  (`why-no-piping-2016-study.md` section 9) found the decisive Tokachi-Tokoro
  difference to be the load relative to each levee's design level, about 2 m;
  the thesis states it but shows it only for the Tokachi (Figure 6.1).
- **A29** (p. 25, the d4PDF ensemble): "It would be helpful to include a figure
  with typical/average hydrographs from this dataset for the current and future
  climate." Thesis 7.5.1 rests on the claim that warming makes floods larger
  while the normalized shape and the number of peaks hardly change (ADR-0023).
- **A32** (p. 32, "Four typhoons reached Hokkaido within a 15-day window"): "is
  this very exceptional, or the new normal in the climate projections?" The
  thesis gives the 2016 flood's return period (about 75 years, about 13 under
  +4 K) but nothing on its multi-typhoon, multi-peak character.

## 2. Sources and the checks made before this pre-registration

| Source | What it supplies |
|---|---|
| `data/processed/2016_event/stage_hourly_Satsunai_201608.csv` | Hourly August 2016 stage at the Satsunai gauge (KP 4.0, column `satsunai`) and at Nantaibashi (KP 15.0, column `nantaibashi`). Nantaibashi is lost after 03:00 on 31 August. |
| Basin history (`tokachi_chisuishi_2023`, 2016 flood chapter, as transcribed in `docs/tokachi_basin_document_review_2026-07-27.md` section 2.5) | Nantaibashi's cable was severed; its highest recorded level was 79.38 m T.P. at 02:00 on 31 August, above the 79.31 m design high water level; the observed Satsunai peak is therefore a lower bound. Station chainages (section 2.2): Satsunai gauge KP 4.0, Nantaibashi KP 15.0. |
| `data/processed/2016_event/flood_trace_2016.csv` | Design high water level per KP on both rivers (the same values as the 2019 bank-height record used for the Tokachi sections). |
| MLIT Water Information System (www1.river.go.jp), station Futochanae, Tokoro River, ID 301111281108060, hourly water level, August and September 2016, retrieved 2026-10-08 | The Tokoro record. The station page gives the gauge zero as T.P. 0.000 m, so readings are T.P. elevations. Extracted verbatim to the new CSV; no value is missing or flagged. |
| Tokoro River Levee Investigation Committee (2017), as read by Pol session 4 (pp. 5-15, 5-20) | Futochanae (KP 18.9) design high water level 12.38 m; above it for 32 h 40 min; committee peak 14.22 m. |
| `data/raw/hydrographs/Hydro Data, HPB/HFB, Tokachi Riv. KP056.20-KP061.80.xlsx` | 3,000 historical and 5,400 +4 K annual-maximum discharge series for the band that feeds all four sections. |
| `results/system_integration/hazard_tokachi_kp*_{historical,plus4K}.csv` | Per year: peak stage, hours above the landside toe, number of separate excursions above it. |
| Yamada et al. (2018), p. 391 (English abstract and introduction) | 2016 was the first time in recorded history that three typhoons made landfall in Hokkaido within one week; four typhoons within two weeks. |
| Hoshino and Yamada (2023), p. 7 | On the same downscaled ensemble for the Tokachi basin: the event data start five days before the heavy rainfall and "may not fully account" for preceding rainfall such as 2016's. |
| Kimura et al. (2018), pp. 1 and 14 | The literature implies more, and multiple successive, typhoons may reach mid-latitudes in future; without the three preceding typhoons the main-stem 2016 peaks were 4 to 24 % lower. No quantified recurrence. |

**Checks already made (so not predictions).**

- The Futochanae hourly record stands above 12.38 m for 6 h on 18 August and
  33 hourly observations from 21:00 on 20 August to 05:00 on 22 August (the
  committee's 32 h 40 min), peaking at 14.24 m at 01:00 on 21 August (the
  committee's waveform: 14.22 m). It also stood above the level for 7 h on 9 and
  10 September, outside the window the thesis discusses.
- Each supplied d4PDF discharge series is 192 hourly values long (8 days), inside
  the 15-day window over which the rainfall was downscaled.

## 3. Pre-registration (written before Part 2 was computed)

Definitions follow ADR-0023 exactly: each member's discharge converted to stage
at KP 57.4 under the local rating, normalized to [0, 1] between its own minimum
and maximum; significant peaks by `scipy.signal.find_peaks(height=0.3,
prominence=0.2)`; t50 and t90 the hours at or above half and 90 % of the rise.
"Loaded" means the peak exceeds the section's landside toe; an excursion is a
run of consecutive hours above the toe (the hazard files' own counts). The 2016
flood on the rating axis is the rating-anchored peak at each section (39.02 /
40.78 / 41.65 / 46.64 m; `initiation-evidence-2016-study.md` section 8).

| # | Prediction | Basis |
|---|---|---|
| P1 | In at least 90 % of the 3,000 historical and of the 5,400 +4 K members the annual peak lies within the first 96 h of the 192-h series, so no member can hold an earlier flood as far before its peak as 2016's second typhoon flood was before its third (about 8 days at Obihiro). | The canonical member peaks at hour 37. |
| P2 | The ADR-0023 statistics reproduce exactly: t50 median 40 h historical and 35 h under +4 K, t90 median 10 and 8 h, two or more significant peaks in 9.6 % and 10.1 % of members. Otherwise stop and diagnose. | Reproduction gate. |
| P3 | The observed 2016 Obihiro record, normalized over August, has two significant peaks by the same rule; any 192-h window that contains its maximum and starts at least one day before it contains only one. | T7 and T11+T9 peaks 34.74 and 35.57 m, T10 38.07 m on a base near 32.7 m. |
| P4 | At every section the share of loaded years with two or more separate excursions above the toe changes by less than a factor of 1.5 between the climates, while the unconditional share rises by the factor of 1.9 to 4.1 already in thesis Table 7.5. | More years reach the toe; their shape does not change. |
| P5 | Among years at least as large as 2016 on the rating axis, the share with two or more separate excursions above the toe is below 25 % at every section in both climates, and the share with two or more significant peaks (normalized) lies within 10 percentage points of the all-years share. | A large peak is not a multi-peak flood. |
| P6 | At KP 58.8, in every 0.25 m peak-stage bin holding at least 30 years in each climate, the +4 K median hours above the toe lies within 20 % of the historical median, and it is not the larger in a majority of those bins. | At fixed peak, warming shapes are not longer (t50 35 against 40 h). |

What a failure would mean. P1 failing would mean the window can hold an
earlier flood and the answer to A32 must count them. P4 or P6 failing would
mean the warming ensemble lengthens or splits floods at a fixed peak, which
would contradict the 7.5.1 claim that the duration and repeated loading at the
toe follow from larger peaks; that claim would then be corrected. P3 and P5
bear only on how 2016 is described.

## 4. Figures this study writes

- `loading_2016_three_rivers.png`: the August 2016 records of the Tokoro
  (Futochanae), the Satsunai (KP 4.0 and Nantaibashi, KP 15.0) and the four
  Tokachi sections (trace-anchored reconstructions), each relative to its own
  design high water level, the Tokachi toes marked.
- `loading_d4pdf_hydrographs.png`: (a) the normalized annual-maximum stage
  shape at KP 57.4, median and 10th to 90th percentile band, historical and
  +4 K, aligned on the peak, with the canonical and alternate members;
  (b) hours above the landside toe against annual peak stage at KP 58.8,
  binned medians and interquartile bands, both climates.

---

# Part 2: outcome (2026-10-08, after the pre-registration commit `20e2330`)

The committed Part 1 ended with two stray markup lines from the writing tool
(`</content>`, `</invoke>`); they are removed here and nothing else in Part 1
changed. Values are from `loading-context-study.json` (`stats` part of the
driver; 2,000 member-block resamples where an interval is given).

## 5. Verdicts

| # | Verdict | Outcome |
|---|---|---|
| P1 | **Held.** | Every member peaks within the first 96 h of its 192-h series: the peak sits a median 50 h (historical) and 51 h (+4 K) after the series starts, at most 83 and 89 h. |
| P2 | **Held exactly.** | t50 median 40 / 35 h, t90 10 / 8 h, two or more significant peaks 9.6 / 10.1 % (9.633 / 10.148 %). Three or more: 1 of 3,000 and 4 of 5,400. |
| P3 | **Failed (more peaks than predicted).** | Normalized over August, the Obihiro record has three significant peaks, not two: 34.74 m on 18 August 02:00, 35.57 m on 23 August 13:00 and 38.07 m on 31 August 04:00, 13 days from first to last; the last two are 183 h (7.6 days) apart. A 192-h window containing the maximum holds one or two of them depending on where it starts; a window placed as the ensemble's (at most 89 h before the peak) holds one. |
| P4 | **Failed at KP 62.0, held at the other three.** | Share of loaded years with two or more excursions, +4 K over historical: 0.97 / 1.26 / 1.16 / **1.72** (KP order; KP 62.0 rests on 10 historical years of 313 loaded). Unconditional: 3.2 / 2.1 / 2.1 / 4.0. Conditioning on reaching the toe does not hold the peak fixed, which is why the post-hoc check 7(1) holds it fixed. |
| P5 | **Held.** | Years at least as large as 2016 on the rating axis: 40 historical, 422 to 424 under +4 K. Among them two or more excursions above the toe 2.5 to 5.0 % historical, 3.8 to 6.4 % +4 K; two or more significant peaks 7.5 % and 4.7 % (all years 9.6 and 10.1 %). A large flood is not a multi-peak flood. |
| P6 | **Held.** | KP 58.8, eight bins with at least 30 years in each climate: +4 K median hours above the toe 0.83 to 1.04 times the historical, shorter in seven of eight. |

## 6. The 2016 floods on three rivers (A25)

Each record against the design high water level at its own station or section
(2019 bank-height values, as used for the Tokachi sections; committee value at
Futochanae):

| Record | Design level (m T.P.) | Peak relative to it | Hours above it |
|---|---|---|---|
| Tokoro, Futochanae (KP 18.9), gauge | 12.38 | **+1.86 m** (14.24 m, 21 Aug 01:00) | 6 (18 Aug) and 33 (20 to 22 Aug) |
| Satsunai, Nantaibashi (KP 15.0), gauge | 79.22 | **at least +0.16 m** (79.38 m, 31 Aug 02:00; lost after 03:00) | at least 3 |
| Satsunai, KP 4.0, gauge | 37.24 | -0.61 m (left-bank trace 37.19 m, -0.05 m) | 0 |
| Tokachi KP 57.4 / 58.8 / 60.0 / 62.0, trace-anchored | 39.21 / 41.03 / 42.75 / 46.39 | +0.45 / -0.28 / -0.45 / -0.66 m | 4 / 0 / 0 / 0 |

The basin history's 2016 flood chapter gives Nantaibashi's design level as
79.31 m (the 2016-era table), so its excess there is at least +0.07 m; the
figure uses the 2019 value for consistency with the Tokachi sections. The
public Futochanae record and the committee's waveform agree within 0.02 m at
the peak and within an hour above the design level.

## 7. Post-hoc checks (added after the first computation; labelled as such)

1. **Repeated excursions at a fixed peak.** Giving every warming year the
   historical multi-excursion rate of its own 0.25 m peak bin, observed over
   expected is 1.09 [0.32, 4.06] / 1.28 [0.87, 2.12] / 1.05 [0.72, 1.79] /
   1.55 [0.80, 4.04]. Every interval includes one; 354 to 1,763 warming years
   compared, 361 to 440 left out (bins above the historical range).
2. **Hours above the toe at a fixed peak**, same construction: 1.02
   [0.91, 1.11] / 0.96 [0.93, 1.00] / 0.96 [0.92, 1.00] / 1.01 [0.93, 1.06].
   Warming floods of a given height stay above the toe as long as historical
   ones, or slightly shorter. Together with P2 and P6 this supports thesis
   7.5.1: the longer and repeated loading at the toe under +4 K follows from
   the higher peaks.
3. **2016 against floods of its own height (KP 58.8).** The 42 historical years
   peaking within 0.25 m of 40.75 m stay above the toe 21 to 61 h (quartiles 23,
   28, 34 h). The 2016 record stayed 21 h, the shortest of all of them (none
   shorter, ties allowed). The canonical flood scaled to the same peak stays
   60 h, longer than 41 of the 42.
4. **The canonical flood's time above the toe at every section.** Against
   historical years within 0.25 m of the stage: longer than 80 % (KP 57.4 at
   its design level, 20 years), 86 to 98 % (KP 58.8, 39.5 to 41.0 m), 90 and
   98 % (KP 60.0, 41.0 and 41.5 m) and 89 to 96 % (KP 62.0, 45.9 m and the
   design level). The simulated floods' median is about half the canonical's.
   **Where on the rise this comes from** (normalized shape, all 3,000
   historical members): the canonical is longer than 42 / 76 / 67 / 57 / 50 %
   of members at 25 / 50 / 60 / 75 / 90 % of its rise, so it is long in the
   middle of its rise, where its trough between two peaks sits, and typical
   near its peak. The shorter alternative is shorter than 98 to 99.9 % of
   members at every fraction.

## 8. What the 2016 sequence was, in the ensemble's terms (A32)

- **Size.** About a 75-year flood now and a 13-year flood under +4 K on the
  ensemble's rating axis (`initiation-evidence-2016-study.md` section 8).
- **Sequence.** Unprecedented in the observed record: the first time three
  typhoons made landfall in Hokkaido within a week (Yamada et al. 2018, p. 391).
  At Obihiro three peaks in 13 days; only the last reached the study sections'
  toes, apart from 4 h at KP 60.0 on 23 August.
- **What the ensemble can say.** Each simulated year supplies one 192-h flood
  around its heaviest rainfall, starting at most 89 h before the peak, so no
  member can hold an earlier flood a week before its maximum, and a study of
  the same downscaled ensemble for this basin notes that events starting five
  days before the heaviest rain may not fully represent preceding rain such as
  2016's (Hoshino and Yamada 2023, p. 7). How often a 2016-like multi-typhoon
  season occurs, now or under warming, is therefore not answerable from this
  ensemble. Within the window, about one annual flood in ten has two separate
  peaks in both climates, and floods as large as 2016 are no more often
  multi-peaked. Kimura et al. (2018, p. 1) cite studies implying that more
  typhoons, and successive ones, may reach mid-latitudes in a warmer climate,
  without a quantified recurrence.
- **Its final flood was short for its height**: post-hoc check 3.

## 9. What this means for the thesis

1. A25: one figure sets the three rivers against their design levels; the
   Tokoro peaked 1.86 m above its level (the committee's waveform 1.84 m) and
   stood above it for about 32 h while the Tokachi sections
   stayed below theirs except KP 57.4 (+0.45 m for 4 h), and the Satsunai
   reached its level at Nantaibashi before that gauge failed.
2. A29: one figure shows the annual flood shape in both climates and the time
   above the toe against peak stage; the latter is the direct evidence that the
   warming increase in time above the toe follows from higher peaks.
3. A32: the 2016 flood's size is not exceptional under warming (13-year), its
   sequence is outside what the ensemble's 8-day events can represent, and its
   final flood was short for its height.
4. **The canonical flood is a long flood at the toe** (owner decision
   2026-10-08: listed as the seventh piping-favoring adopted choice in thesis
   8.4.1). Both tested alternatives lower the transient probability (the
   shorter event 32 to 38 % at mid-curve; the members' own waveforms 13 to
   38 % annually, unconverged), and the ensemble places it above 80 to 98 % of
   same-height floods in time above the toe. The shorter alternative is among
   the shortest 2 % of members, so the flood-shape lever on the index
   difference (+0.26 to +0.53) brackets toward an extreme, not a typical, flood.
5. No production value changes.
