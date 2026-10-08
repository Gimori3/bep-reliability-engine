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
</content>
</invoke>
