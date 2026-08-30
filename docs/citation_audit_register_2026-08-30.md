# Claim-level citation register (generated 2026-08-30)
Generated from `d:\repositories\msc-thesis` at commit `b4f1669`.
Total citation instances: **660** across **106** distinct keys.

Status meanings:

- **SOURCE-READ** the source document was opened in one of the two audit passes and its
  load-bearing claims were checked. It does **not** mean every instance below was read.
- **UNTOUCHED** the source was never opened in either pass. Every instance is unchecked.
- **UNTOUCHED (named)** as above, and explicitly listed as deferred in a prior register.

| Status | Keys | Instances |
|---|---|---|
| SOURCE-READ | 40 | 478 |
| UNTOUCHED (named) | 6 | 38 |
| UNTOUCHED | 60 | 144 |


## Why this register exists

Two audit passes ran on 2026-08-30 and each kept its own record in an ephemeral session
scratchpad. Both records are **key-level**: they say which source documents were opened,
not which of the 660 individual citation instances were read. This file merges both
records and adds the instance-level checklist that neither had, so a third pass can close
the remainder without re-doing settled work and without relying on a scratchpad that no
longer exists.

The instance checklists below are generated mechanically from the thesis at `b4f1669`.
Ticking one means: the sentence was read, the source passage it depends on was located,
and the two agree.

---

# Appendix 1: record of audit pass 1 (session 5fd88150)

# Citation accuracy audit — final state

106 cited keys, 652 citation instances. All 106 have bib entries; 0 cited keys lack one;
0 duplicate bib keys. 52 bib entries are uncited (harmless under biblatex).

Commits: `1bb9698`, `62150a1` on `main`, pushed to Overleaf.

## Verified against the primary source this session (claims checked and correct)

| key | what was checked |
|---|---|
| sellmeijer_2011 | Eq. [6] F_R/F_S/F_G in full; exponents 0.35/0.13/-0.02/0.6/0.28/0.04; Table 2 means Dr 0.725, U 1.81, KAS 0.498, d70m 208 um; validity 150 to 430 um; IJkdijk 25 % test-2 deviation; the 13.2 % SD vs 13.4 % drift |
| pol_sie_2024 | Eqs. (5) (6) (8) (9) (10) (11) (12) (13) and the equation numbers the thesis cites them by; Table 2 (m_p 0.12, C_e 0.055/0.043, eta 0.25, theta 37, r_e 0.6, k CoV 0.5) |
| pol_compgeo_2024 | regression constants 89 and 0.81, R2 0.94; mass-balance + laminar-transport basis; alpha ~ -1/2 from 3D, and van Beek's -0.45 to -0.2 |
| van_beek_2015 | initiation- vs progression-dominated regimes |
| kanning_2012 | Table 4-7 and section 4.7.3: 200 to 300 m, Lexmond clay layer, discretization caveat |
| schweckendiek_2014 | m_p ~ LN(1.0,0.12) from observed vs predicted (p.31); Table 3.4 deterministics; the fictitious 200 m (section 7.4, Table 7.1 footnote); piping dominance due to ground-condition uncertainty (p.2) |
| TRZmw1999 | p.44 and Eq. (A.1.9): L = lambda*th(Lv/lambda) + L2 + lambda_m — the exact r_e denominator |
| TAW2004 | Bijlage 4 p.145 three-region blanket theory, lambda = sqrt(kD*c) |
| pwri_2014 | Fig. 6.3.1 p.34: 59.2 % all-OK so 40.8 % deficient; 1.5+9.5+0.3+13.8 = 25.1 piping-involving; 13.8 piping-only. p.21 conductivity several-to-ten and density +/-0.1 g/cm3. 10 m / 3 m waiver |
| jice_2019 | 200 m survey and t* spacing; G/W <= 1 and i >= 0.5; 3 m cover-layer exclusion (section 5.3) |
| mlit_2020_breach | 120/140 overflow 86 %, 2/140 seepage 1 %, 12 + 128 = 140; 70 overtopping sites, 12 breached, 58 not, 83 % |
| vanbaars_2009 | 337 events, 1,735 failures, 1134 to 2006, piping 1 %, two-thirds inner slope/crest |
| kimura_2018 | 260 million USD, 40,258 ha, four named typhoons |
| furuichi_2018 | Karikachi 352 mm/24 h and 507 mm/72 h at 110 and 109 years (from 34 years of record) |
| mizuta_2017 | d4PDF: 60 km global / 20 km regional, 50 x 60 = 3,000 historical years, six SST patterns x 15 x 60 = 5,400 |
| fukuoka_2019 | 10^-11 m/s consolidated peat permeability; Moiwa 10,870 vs design 13,700 m3/s; the 1 m above HWL scope; 15 % gravel exclusion |
| tokachi_levee_committee_2017 | three breach sites; section 5-4 Table 5-5 attributes to erosion, rates seepage/piping low |
| dean_2010 | three bases examined, work selected; wave-overtopping scope |
| saltelli_primer_2008 | file identity confirmed as the Wiley 2008 Primer despite the 2007 filename |
| GSA set | sobol_1993 (ANOVA-HDMR), saltelli_2002 (N(k+2) radial design), saltelli_2010 (estimators), jansen_1999 (total-effect form), owen_1997 (scrambling), archer_1997 (bootstrap), homma_saltelli_1996 (total index), mara_tarantola_2012 + kucherenko_2012 (dependent inputs) |
| lane_1935 | abstract only ("more than two hundred masonry dams"); body paywalled |

## Defects found and FIXED (12)

1. `i_c >= 0.5` symbol collision, 3 sites (Ch3 x2, App A) — one site new.
2. Sellmeijer 13 % relabelled: 13.2 % scatter vs 13.4 % drift, both now named (App G).
3. Conductivity half-band vs span, 2 sites (Ch8, App E).
4. Lane "278 cases" -> "more than two hundred surveyed dams" (Ch2).
5. Schweckendiek "adopts 200 m from the same source" -> assumed in a fictitious case (Ch3).
6. van Beek cited for alpha = -1/2 when the source gives -0.45 to -0.2 (Ch4).
7. Hagibis breach total 142 -> 140 (Ch8).
8. Overtopping survival 72 sites / 81 % -> 70 / 83 %, recited (App G).
9. m_p "12 per cent regression scatter" -> model uncertainty from observed vs predicted (App E).
10. Dean "time-integrated velocity" -> the work index (Ch3).
11. Fukuoka 1 m above HWL extent conflation (App D).
12. theta "angle of repose" harmonised to "bedding angle" in body text (Ch3, App E), nomenclature keeps both names since Pol uses both.

## NOT individually re-verified — residual work

These rest on the engine repo's own provenance documents, not on my own reading of the
primary this session. No defect found in them, but no independent check either.

| key | instances | why deferred |
|---|---|---|
| oyo_1999 | 49 | traced per-cell in `docs/tokachi_bep_inputs_provenance.md`; 86 MB scanned PDF |
| tokachi_chisuishi_2023 | 39 | mined in `docs/tokachi_chisuishi_full_review_2026-07-27.md`; 816 pp |
| uemura_phd_2025 | 29 | Japanese doctoral thesis, numbers must be read in the original |
| fukuda_2025_internal | 14 | internal document, remediation history for the ADR-0050 berm claims |
| uemura_wp2_2024 | 14 | usage split from `wp2_report_2022` looks right but unchecked in the documents |
| kawajiri_2025 | 12 | grain-size and site-count claims |
| tokorogawa_2017 | 11 | sand-boil site counts and the 0.70 / 0.87 exit gradients |
| hkv_2023 | 11 | Dutch WBI+ report |
| obihiro_levee_inspection_2008 | 9 | Abashiri 234 h already verified 2026-08-29; the rest not |
| ~40 low-count keys | 1 to 8 each | single-claim sources |


---

# Appendix 2: record of audit pass 2 (session ed829470)

# Citation accuracy audit — state after the residual pass (2026-08-30)

106 cited keys, 0 unresolved. 373 labels, 0 duplicates, 0 dangling.
Commits: `1bb9698`, `62150a1` (first pass), **`b4f1669`** (residual pass), all pushed to Overleaf.

## Verified against the primary source — first pass (see the predecessor list)

sellmeijer_2011, pol_sie_2024, pol_compgeo_2024, van_beek_2015, kanning_2012,
schweckendiek_2014, TRZmw1999, TAW2004, pwri_2014, jice_2019, mlit_2020_breach,
vanbaars_2009, kimura_2018, furuichi_2018, mizuta_2017, fukuoka_2019,
tokachi_levee_committee_2017, dean_2010, saltelli/GSA set, lane_1935 (abstract only).

## Verified in the residual pass (2026-08-30)

| key | how | outcome |
|---|---|---|
| oyo_1999 | engine `docs/oyo_1998_framing_review_2026-08-24.md` (page-level reading of the scanned report) + `tokachi_bep_inputs_provenance.md` + the 様式-3 sheets rendered from the Fukuda PDF | 3 defects |
| tokachi_chisuishi_2023 | full text layer extracted from `inr9av000000b2i3.pdf` (816 pp) and searched verbatim | 4 defects |
| uemura_phd_2025 | Japanese original `Uemura_Fumihiko.pdf`, sections 3.4 and 4.2 to 4.3 | 3 defects |
| uemura_wp2_2024 | `WP2 - Report ..._260406_215649.pdf` (Uemura & Curran, PR3983, June 2024) | 1 defect (Eq. 14 belongs to the IAHS paper); Table 4, the nine sections, the 0.2 km segments and the seepage-as-future-work claim all confirmed |
| uemura_iahs_2024 | Proc. IAHS 386, 69-74 | Eq. (7) rating form and Eq. (14) section maximum confirmed verbatim |
| fukuda_2025_internal | 7 pages rendered at 150 dpi and read | 2 defects; the 1999 to 2003 dating and the two 1998 criteria confirmed verbatim ("H11〜H15", "局所動水勾配、裏法すべり") |
| kawajiri_2025 | full text | 1 defect (which survey resolved the loosened zones) |
| tokorogawa_2017 | full text of `icrceh00000032zs_compressed.pdf` | 2 defects; 0.70/0.87 at KP26.8, the 0.24 to 0.45 range, 1,930 km2 and 120 km all confirmed |
| hkv_2023 | Appendix C read in full | 1 defect (the closed form is exact, not an approximation); both equations and the P(F|e) <= P_A <= P(F) ordering confirmed verbatim |
| obihiro_levee_inspection_2008 | `ctll1r0000001cmh.pdf` | 1 defect (census date); 398.2/359.8/66.7 km confirmed |
| morita_2018 | full text | volume/pages confirmed; the 38 h total above the planned level confirmed |

## Defects found and FIXED in the residual pass (16)

1. Field-vs-laboratory permeability "systematically 2 to 50 times" — false; 2 of 6 pairs invert. 3 sites (Ch3 text, Ch3 caption, App A).
2. "the gradient-failing sections are those with narrower foreshores" — contradicted by the table beside it (Ch3).
3. "every surveyed cross-section" rated deficient — the surveyed population is six and KP 65.0 passes. 3 sites (Ch8 x2, App G).
4. Inundation-area population 168,000 -> 158,000 and area 617.4 -> 617.7 km2 (App D, Ch3).
5. Agricultural share 22 -> 26 per cent; the 304 billion yen and the 47/33 per cent crop shares are not in the cited source and were replaced by figures that are (App D, Ch3).
6. "115-year record" at a station whose record starts January 1907 -> 109 years (App D).
7. Tokachi Ohashi constriction presented as current; the Kino set-back levee removed it in 1998 (App D).
8. Runoff model: "storage-function" -> the distributed two-stage tank model; the five reproduction events span 1981 to 2013 and the 2016 flood is held OUT of the fit (App F, Ch3).
9. Rating relation "established from non-uniform flow computations" — that computation supplies the discharge-to-velocity relation, not the H-Q (App F, Ch3, Ch4).
10. Eq. (14) attributed to the unpublished WP2 report -> the IAHS paper, where it is verbatim (Ch4).
11. "Kinohara sluice gate" -> Tokusabara (木賊原樋門), KP 57.3, 1976 (App D).
12. "transmissivity of the post-1999 berm fill" -> the berm-fill soil data, permeability included (Ch3).
13. Tokoro comparison sections "farther upstream" — they are downstream; and they are the Shibayamazawa breach and the Hiyoshi No. 30 sluice, not KP 18.9 / KP 22.6 (Ch3, App D).
14. Tokoro channel "narrows to a width of only 100 to 200 m" — 100 to 200 m is the narrowing relative to the reaches above and below (App D).
15. Kawajiri loosened zones attributed to the surface-wave survey -> trenching plus dynamic cone penetration (App D).
16. Obihiro inspection census "end of the 1998 fiscal year" -> end of the 2007 fiscal year (App A). Also the WBI+ closed form is exact, the peak-based scalar is the approximation (Ch2), and the antecedent curves are conditional on peak discharge, not water level (Ch2).

## Open, not fixed

- **The 34 h / 24 h high-water durations attributed to `fukuda_2025_internal`** (Ch3 §2016) are not in the 7-page secured PDF, which is a meeting note plus the current-state map plus four OYO 様式-3 sheets. The communication may have carried more. Cannot verify, cannot disprove.
- **`fukuda_2025_internal` is dated 2025 in the bib; the meeting note is headed R8.5 = May 2026.** Owner ruling needed: the key name and every in-text year would change.
- **Satsunai 400 to 450 m corridor / one third of levee length cutting former channels** (App A) and **"the majority of disaster causes on the Satsunai were bank erosion"** (App G) are not locatable in the Chisuishi text layer; they may live in figure-embedded text. Uncontradicted, unverified.
- **ENW2017, mlit_design_standard_2025, nakatsugawa_2017, terzaghi1943, sellmeijer_1988, pol_thesis_2022** and the remaining 1-to-3-count keys were not individually re-verified.

## Traps worth carrying forward

- **Bash heredocs collapse doubled backslashes even when quoted.** `\\ref` becomes `\ref`, which Python then reads as a carriage return, and the edit silently fails to match. Write fix scripts with the Write tool.
- The Chisuishi's own numbers appear twice at different chainages (38.14 at KP 56.6 vs 38.26 at the KP 56.7 gauge; 11.61 vs 11.63 at Moiwa; 79.22 vs 79.31 at Nantaibashi). The thesis's tables use the event-chapter values consistently and correctly.
- `uemura_wp2_2024` (Docon/HKV report) and `uemura_iahs_2024` (Proc. IAHS) are different documents describing the same model. The report defers to the paper for the overtopping model, so numbered equations belong to the paper.


---

# Instance checklist


## UNTOUCHED (60 keys, 144 instances)

### `kyuka_2020` (8)

- [ ] `1. Introduction.tex:18` The Tokachi basin is a textbook case, its floods historically brief but intense and followed by a rapid fall in stage \parencite{kyuka_2020}.
- [ ] `2. Theoretical and Empirical Foundations.tex:16` Japanese river systems are distinguished by steep topographical gradients and rapid hydrological responses, and the Tokachi River basin is historically characterized as such a `flashy' system \parencite{kyuka_2020}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:18` Steep channel gradients then concentrate the runoff rapidly, and the result is a regime of abrupt water-level rise and short flood durations, the defining attributes of a flashy system \parencite{kyuka_2020}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:27` These rivers are also morphodynamically active: mid-channel bars deflect flow toward the embankments and drive lateral bank erosion that has produced breaches independently of overtopping \parencite{kyuka_2020}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:38` The pattern of damage was spatially differentiated in a manner that directly motivates the multi-mechanism scope of this thesis: sediment-related debris flows and bank erosion in the steep headwater catchments, and rapid lateral channel migration in the Otofuke River that produced levee breaches without overtopping, with the water level remaining below the crest throughout \parencite{furuichi_2018
- [ ] `appendix-d.tex:133` The Tokachi tributaries were originally multi-thread braided gravel-bed rivers; flow regulation, channelization, and embankment construction progressively transformed many reaches into single-thread channels with vegetated floodplains \parencite{kyuka_2020}.
- [ ] `appendix-d.tex:167` Notable floods nonetheless occurred: a 28-hour rainfall event in August 1981 delivered 331~mm at Kamisatsunai, then among the largest events in the local record \parencite{furuichi_2018}, and a further large flood in September 2011 drove documented morphological change in the Otofuke tributary \parencite{kyuka_2020}.
- [ ] `appendix-d.tex:192` In the Otofuke River, four flood peaks within 15 days drove rapid lateral channel migration and meander shift, producing levee breaches at seven locations without overtopping, as the water level remained below the crest throughout \parencite{kyuka_2020}; the official inventory of breaches within the directly managed Tokachi system, which records one breach on the Otofuke, is given in Section~\ref{

### `hoshino2023spatiotemporal` (8)

- [ ] `1. Introduction.tex:22` Projections for the Tokachi basin indicate that warming will raise peak discharge, make compound events driven by heavy antecedent rainfall more frequent, and may alter hydrographs in time \parencite{yamada_iahr_2020, hoshino2023spatiotemporal}.
- [ ] `2. Theoretical and Empirical Foundations.tex:207` This allows extreme flood events to be characterized statistically at return periods far exceeding any observational record, and permits direct comparison of the full distributions of hydrograph characteristics between the two climates \parencite{yamada_iahr_2020, hoshino2023spatiotemporal}.
- [ ] `2. Theoretical and Empirical Foundations.tex:209` The projections indicate that warming alters flood dynamics along several dimensions at once \parencite{yamada_iahr_2020, hoshino2023spatiotemporal}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:18` Even at a fixed rainfall total the spatial concentration of rainfall modulates the hydrograph strongly: peak discharge at a given gauge differs by more than a factor of two across events of equivalent volume \parencite{hoshino2023spatiotemporal}.
- [ ] `appendix-d.tex:36` The principal tributaries relevant to the study reach are the Otofuke River entering from the north and the Satsunai River entering from the south-west, both joining the mainstem in the KP~53 to KP~56 reach; the largest tributary, the Toshibetsu River, enters further downstream near KP~29 \parencite{hoshino2023spatiotemporal, fukuoka_2019}.
- [ ] `appendix-d.tex:39` Runoff from the headwaters reaches the downstream plain with a lag of only several hours \parencite{kimura_2018}, and river planning in the basin adopts a 72-hour rainfall duration because peak discharge generally occurs within that window of the onset of rainfall \parencite{hoshino2023spatiotemporal}.

### `jice_manual_2012` (8)

- [ ] `1. Introduction.tex:24` Japanese verification applies sophisticated, time-varying seepage analysis at a representative cross-section of each levee reach, yet ultimately judges safety against a single question: whether a gradient or uplift threshold is exceeded at one instant of the computed pressure field, rather than whether erosion can actually retrogress across the full seepage path before the flood recedes \parencite
- [ ] `2. Theoretical and Empirical Foundations.tex:221` There engineers perform two-dimensional transient saturated-unsaturated seepage analysis driven by actual flood hydrographs, and extract from the resulting pore-pressure field a slope stability factor and two seepage measures \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}.
- [ ] `2. Theoretical and Empirical Foundations.tex:232` Japanese verification practice models the loading as a dynamic process and then judges safety on a single instant of it \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}; the Dutch progression-based framework judges the outcome the mechanism must actually reach, but strips the loading of its time dependence \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:287` Despite the use of transient hydraulic analysis, the failure criterion therefore remains initiation-based: the limit state function $Z_\mathrm{init} = i_c - i_\mathrm{max}$ identifies whether sand boiling can begin, but does not model pipe progression or the conditions required for retrogressive breakthrough \parencite{terzaghi1943, jice_manual_2012}.
- [ ] `2. Theoretical and Empirical Foundations.tex:298` Explicit progression models are not generally embedded in Japanese national design verification procedures \parencite{mlit_design_standard_2025, jice_manual_2012}, which helps explain why the gap persists at the system scale.
- [ ] `3. Study Area, Geological Setting, and Data.tex:139` 0$ of cover-layer weight to the uplift force on its base \parencite{jice_manual_2012}.
- [ ] `appendix-a.tex:577` 0$ of cover-layer weight to uplift force where one is \parencite{jice_manual_2012}, and the four confined study sections carry a blanket of 0.
- [ ] `appendix-g.tex:53` Japanese practice reaches its detailed structural verification of that section through two-dimensional transient saturated-unsaturated seepage analysis driven by an actual flood hydrograph, following the practical procedures of the Manual for Structural Examination of River Levees \parencite{jice_manual_2012}.

### `yabegawa_2013` (7)

- [ ] `2. Theoretical and Empirical Foundations.tex:127` Localized complexities introduce spatial heterogeneity, but the prevailing bipartite $A_c$/$A_g$ arrangement is analogous to the conditions that contributed to the 2012 Yabe River levee collapse, which occurred through localized piping without concurrent overflow \parencite{yabegawa_2013, Yoshikawa2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:179` That branch alone is drawn as a broken line: the foundation route through heave and foundation sand boiling is drawn solid, and the 2012 Yabe River breach re-examined in Chapter~\ref{chap: Verification, Validation, and Sensitivity} is a completion on it \parencite{yabegawa_2013}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:160` This section confronts the framework with four documented Japanese cases of foundation sand boiling and backward erosion piping that occupy exactly this high-gradient, gravel-dominated setting: the repeated sand ejecta at Gounokawa Shimohara \parencite{Okamura2025_gounokawa}; the boils and levee damage at Gounokawa Shikaga \parencite{Sako2019}; the piping-attributed breach of the Yabe River right
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:231` 06 wherever nothing happened \parencite{yabegawa_2013}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:320` The separation is in the progression physics, thin fine sand against thick coarse gravel, and the committee's own explanation of the survivals is the same rate argument \parencite{yabegawa_2013}.
- [ ] `appendix-g.tex:204` Post-disaster government reviews of the Tokoro, Yabe and Kinu River failures have demonstrated the vulnerability of layered foundation geologies to piping \parencite{Takizawa2018, tokorogawa_2017, yabegawa_2013}.
- [ ] `appendix-g.tex:981` 3k breached between 13:15 and 13:30 in July 2012 without overtopping, and the breach is attributed to piping by the investigating committee \parencite{yabegawa_2013}.

### `pol_2026_pers_comm` (7)

- [ ] `3. Study Area, Geological Setting, and Data.tex:352` The two-soil model is therefore adopted as the production coupling mode, a choice subsequently endorsed by the progression model's author \parencite{pol_2026_pers_comm}, and the two parameters are drawn from their marginal lognormal distributions with no imposed correlation.
- [ ] `4. Methodology.tex:586` The omission yields an unconditional upper bound on the transient failure probability, a choice the model's author confirmed as appropriate for flashy typhoon rivers \parencite{pol_2026_pers_comm}.
- [ ] `4. Methodology.tex:698` The plane-strain value is retained as the production baseline, a choice endorsed by the progression model's author for a two-dimensional Sellmeijer-based model at sub-meter blanket thicknesses such as those of Table~\ref{tab: section inputs} \parencite{pol_2026_pers_comm}, with the three-dimensional reading belonging to the discussion of the result rather than to the baseline.
- [ ] `4. Methodology.tex:905` The model's author confirmed it as a realistic assumption for peaks as closely spaced as consecutive typhoon landfalls \parencite{pol_2026_pers_comm}.
- [ ] `6. Results - Subsurface Piping Assessment.tex:1097` Third, the plane-strain anchor the two production branches share is the baseline the progression model's author endorses for a two-dimensional Sellmeijer-based model at blanket thicknesses such as these \parencite{pol_2026_pers_comm}, the three-dimensional reading belonging to the discussion of the result rather than to the baseline.
- [ ] `appendix-c.tex:16` Decisions confirmed or endorsed by the progression model's author during the project consultations are marked accordingly in the repository records, and are cited in the text as \parencite{pol_2026_pers_comm}.
- [ ] `appendix-g.tex:270` 014 printed in the source figure caption is an erratum the paper's lead author confirmed in writing \parencite{pol_2026_pers_comm}.

### `final_report_2022` (6)

- [ ] `1. Introduction.tex:9` These 2016 floods sharpened interest in moving from Japan's deterministic, hazard-based design philosophy toward a probabilistic, risk-based approach to levee safety \parencite{final_report_2022, uemura_iahs_2024}.
- [ ] `1. Introduction.tex:11` A Japanese-Dutch research collaboration builds on that complementarity \parencite{final_report_2022}, combining Japan's large-ensemble climate projections, most notably the d4PDF dataset \parencite{mizuta_2017}, with Dutch probabilistic levee-safety methods to support forward-looking flood-risk assessment under a changing climate.
- [ ] `2. Theoretical and Empirical Foundations.tex:9` Levee safety is evaluated against a specified design external force, such as a rainfall event with an annual exceedance probability of 1/150 \parencite{final_report_2022}.
- [ ] `2. Theoretical and Empirical Foundations.tex:11` Within the resulting collaboration, estimating levee failure probabilities $P_f$ under transient hydraulic loads and extending the framework to seepage failure mechanisms are identified as explicit research priorities \parencite{final_report_2022, project_plan_2025}.
- [ ] `2. Theoretical and Empirical Foundations.tex:293` At the basin scale, system-wide assessment remains dominated by overflow-based judgment, non-overflow mechanisms being treated as secondary \parencite{uemura_iahs_2024, uemura_phd_2025, final_report_2022}.
- [ ] `appendix-d.tex:48` Within the deterministic Japanese flood-safety framework reviewed in Chapter~\ref{chap: Theoretical and Empirical Foundations}, the basin is managed to a planning-scale return period in the range of 100 to 200 years \parencite{final_report_2022, wp1_report_2021}; at the Obihiro, Moiwa, Otofuke and Memuro reference points the design scale is specifically an annual exceedance probability of $1/150$

### `yamada_iahr_2020` (5)

- [ ] `1. Introduction.tex:22` Projections for the Tokachi basin indicate that warming will raise peak discharge, make compound events driven by heavy antecedent rainfall more frequent, and may alter hydrographs in time \parencite{yamada_iahr_2020, hoshino2023spatiotemporal}.
- [ ] `2. Theoretical and Empirical Foundations.tex:11` Japan contributes a complementary strength in large-ensemble climate projection, most notably the d4PDF dataset \parencite{mizuta_2017}, which supports statistical characterization of extreme weather events and their transient hydrological responses \parencite{yamada_iahr_2020}.
- [ ] `2. Theoretical and Empirical Foundations.tex:207` This allows extreme flood events to be characterized statistically at return periods far exceeding any observational record, and permits direct comparison of the full distributions of hydrograph characteristics between the two climates \parencite{yamada_iahr_2020, hoshino2023spatiotemporal}.
- [ ] `2. Theoretical and Empirical Foundations.tex:209` The projections indicate that warming alters flood dynamics along several dimensions at once \parencite{yamada_iahr_2020, hoshino2023spatiotemporal}.

### `Sako2019` (5)

- [ ] `2. Theoretical and Empirical Foundations.tex:189` Levees on the Gounokawa River, under prolonged and repeated extreme flooding, likewise suffered severe sand boiling and localized subsidence yet survived \parencite{Sako2019, Okamura2025_gounokawa}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:158` This section confronts the framework with four documented Japanese cases of foundation sand boiling and backward erosion piping that occupy exactly this high-gradient, gravel-dominated setting: the repeated sand ejecta at Gounokawa Shimohara \parencite{Okamura2025_gounokawa}; the boils and levee damage at Gounokawa Shikaga \parencite{Sako2019}; the piping-attributed breach of the Yabe River right
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:241` At Shikaga boils occurred through a cover whose measured laboratory cohesion would have prevented them by a wide margin had it been mobilized \parencite{Sako2019}, and the Gounokawa trenches show why: the blankets are threaded by sand veins that provide effectively cohesionless preferential paths.
- [ ] `appendix-g.tex:228` The Gounokawa River supplies the complementary observation of severe sand boiling and localized subsidence under prolonged and repeated extreme flooding without catastrophic breach \parencite{Sako2019, Okamura2025_gounokawa}; that site is analyzed as a validation case in Appendix~\ref{app subsec: Gounokawa Shimohara Case}.
- [ ] `appendix-g.tex:949` 75k during the same 2018 flood, without a breach \parencite{Sako2019}.

### `Okamura2025_gounokawa` (5)

- [ ] `2. Theoretical and Empirical Foundations.tex:189` Levees on the Gounokawa River, under prolonged and repeated extreme flooding, likewise suffered severe sand boiling and localized subsidence yet survived \parencite{Sako2019, Okamura2025_gounokawa}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:157` This section confronts the framework with four documented Japanese cases of foundation sand boiling and backward erosion piping that occupy exactly this high-gradient, gravel-dominated setting: the repeated sand ejecta at Gounokawa Shimohara \parencite{Okamura2025_gounokawa}; the boils and levee damage at Gounokawa Shikaga \parencite{Sako2019}; the piping-attributed breach of the Yabe River right
- [ ] `appendix-g.tex:228` The Gounokawa River supplies the complementary observation of severe sand boiling and localized subsidence under prolonged and repeated extreme flooding without catastrophic breach \parencite{Sako2019, Okamura2025_gounokawa}; that site is analyzed as a validation case in Appendix~\ref{app subsec: Gounokawa Shimohara Case}.
- [ ] `appendix-g.tex:887` 8k reach in the floods of 2018, 2020, and 2021, and the levee did not breach in any of them \parencite{Okamura2025_gounokawa}.

### `schweckendiek_2016` (5)

- [ ] `2. Theoretical and Empirical Foundations.tex:402` The foundational framework was established by \textcite{schweckendiek_2014, schweckendiek_2016, schweckendiek_2017} and is institutionalized within the Dutch WBI+ methodology \parencite{hkv_2023}, where the updating is implemented in closed form on the fragility curve and conditioned on a survived historical peak water level.
- [ ] `3. Study Area, Geological Setting, and Data.tex:88` This updating admits a closed form for the posterior fragility curve which depends on the survived level but not on its exceedance frequency, and which makes the peak-based approximation of standard WBI+ practice provably conservative \parencite{hkv_2023, schweckendiek_2016}.
- [ ] `4. Methodology.tex:1207` Using the full transient record rather than a peak-level scalar is the methodological core: a peak-based survival constraint of the closed-form WBI+ type \parencite{schweckendiek_2016, hkv_2023} cannot represent the load duration that governs progression and would falsely exonerate future long-duration events with sub-2016 peaks.
- [ ] `appendix-d.tex:294` The posterior fragility curve derived by \textcite{hkv_2023} is the truncated and renormalized prior, \begin{equation} F_{H_c^{*}}(h_c) = \begin{cases} \dfrac{F_{H_c}(h_c) - F_{H_c}(h_\mathrm{obs})}{1 - F_{H_c}(h_\mathrm{obs})}, & h_c \geq h_\mathrm{obs}\\[8pt] 0, & h_c < h_\mathrm{obs} \end{cases} \end{equation} which depends on the survived level $h_\mathrm{obs}$ but not on its exceedance freque

### `mlit_teibou_sekkei_2007` (4)

- [ ] `1. Introduction.tex:9` The Planned High Water Level is the load a levee must be shown to withstand, not a stage below which it is presumed safe \parencite{mlit_teibou_sekkei_2007}.
- [ ] `2. Theoretical and Empirical Foundations.tex:9` The planned high water level (HWL) is that design load: a levee must be shown safe against the ordinary action of flowing water at levels at or below it, by verifying slope stability, piping and heave against allowable values \parencite{mlit_teibou_sekkei_2007}.
- [ ] `appendix-g.tex:67` The Design Guideline reaches the same conclusion from the damage record, noting that structural problems such as leakage have occurred in large numbers under floods at or below that level, and gives that as the reason for introducing the verification programme \parencite{mlit_teibou_sekkei_2007}.
- [ ] `appendix-g.tex:77` Where a blanket is present, the governing measure is instead the heave ratio $G/W$, the weight of the blanket layer divided by the uplift pressure acting on its base, with $G/W \leq 1$ marking the deficient condition \parencite{mlit_teibou_sekkei_2007, pwri_2014, jice_2019}.

### `vandenboer_2019` (4)

- [ ] `2. Theoretical and Empirical Foundations.tex:172` Coarser sands and gravels progress considerably faster than fine sands \parencite{van_klaveren_2020}, and under the extreme peak discharges characteristic of flashy systems the applied head $H$ may substantially exceed the critical head $H_c$, with progression velocity increasing with the overloading ratio $H/H_c$ \parencite{vandenboer_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:200` where $T_\text{load}$ is the duration for which hydraulic head exceeds the initiation threshold and $v_\text{progression}$ is a function of hydraulic conductivity $k$ and hydraulic overloading $H/H_c$ \parencite{van_beek_2015, vandenboer_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:302` That the critical-head formulations offer no rate at all, and the one duration-conditional predecessor only a constant, reflects how recently pipe growth has been measured through time \parencite{robbins_2017, vandenboer_2019, pol_2021}.
- [ ] `4. Methodology.tex:736` Progression-Dominated Behavioral Regimes}, that race can be expressed conceptually as failure occurring when the loading duration exceeds the time the pipe needs to traverse the remaining seepage path at a progression velocity increasing with conductivity and hydraulic overload \parencite{van_beek_2015, vandenboer_2019}.

### `hoffmans_2014` (3)

- [ ] `1. Introduction.tex:83` Because piping is a weakest-link mechanism, the per-cross-section conditional failure probabilities are related to the 200-meter segment level through the spatial autocorrelation length of the governing foundation parameters \parencite{hoffmans_2014, kanning_2012}.
- [ ] `2. Theoretical and Empirical Foundations.tex:202` The spatial autocorrelation of parameters such as blanket thickness and aquifer conductivity supplies the basis for correcting it \parencite{hoffmans_2014}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:381` The resulting spatial scale effect is accounted for by relating per-cross-section conditional failure probabilities to the 200-meter segment level through the effective number of independent cross-sections $n_\mathrm{eff} = \max(1,\, L_\mathrm{seg}/\lambda_\mathrm{ac})$, where $\lambda_\mathrm{ac}$ is the spatial autocorrelation length of the governing foundation parameters \parencite{hoffmans_201

### `bezuijen_2017` (3)

- [ ] `2. Theoretical and Empirical Foundations.tex:170` where $k_\mathrm{bl}$ is the vertical hydraulic conductivity of the confining blanket \parencite{bezuijen_2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:189` And where the velocity within a developing pipe falls below the critical sediment transport threshold, eroded particles settle and clog the channel, a counter-mechanism termed self-healing or sedimentation arrest \parencite{bezuijen_2017}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:178` With a thin, low-conductivity $A_c$ blanket confining a thick, highly conductive $A_g$ aquifer, the hinterland leakage length \begin{equation} \lambda = \sqrt{\frac{k_\mathrm{aq}\cdot D_\mathrm{aq}\cdot D_\mathrm{bl}}{k_\mathrm{bl}}} \end{equation} is large \parencite{bezuijen_2017}, so elevated aquifer pressures act substantially landward of the levee toe rather than being confined to its immedia

### `pwri_4300_2015` (3)

- [ ] `2. Theoretical and Empirical Foundations.tex:187` It excludes cross-sections whose embankment gravel content averages 15~per cent or more, since the conductivity-dominated index would otherwise flag gravel-rich embankments as the most hazardous despite the absence of any damage record \parencite{fukuoka_2019, pwri_4300_2015, jice_2019}.
- [ ] `8. Discussion.tex:988` There is nonetheless a defensible version of it, since in a coarse, unconfined gravel deposit the mechanism genuinely is unlikely, and that is why Japanese practice excludes gravel-rich embankments from index assessment altogether \parencite{pwri_4300_2015, fukuoka_2019}.
- [ ] `appendix-g.tex:1386` Japanese experimental work finds very low seepage-failure risk in embankment materials with a high gravel content and a coarse grain size \parencite{pwri_4300_2015}, and on that basis both the national screening procedure and the vulnerability-index analysis exclude embankments whose average gravel content is 15~per cent or more from index assessment altogether \parencite{jice_2019, fukuoka_2019}.

### `vanderLinde2025` (3)

- [ ] `2. Theoretical and Empirical Foundations.tex:313` The Dutch family has been evaluated as a family \parencite{van_beek_hoffmans_2017} and its numerical branch reviewed separately \parencite{vanderLinde2025}; the test applied here is narrower, and asks only which formulation can express a race between pipe progression and flood recession.
- [ ] `2. Theoretical and Empirical Foundations.tex:353` A constant rate does not respond to overloading, grain size or aquifer conductivity, which are the dependences that decide the race in a coarse foundation \parencite{pol_sie_2024} \\ \addlinespace[4pt] Numerical erosion simulation \parencite{vanderLinde2025} & Coupled groundwater and pipe flow with an explicit erosion criterion, resolved in two or three dimensions & Not evaluated per realization.
- [ ] `4. Methodology.tex:836` Fully coupled transient finite-element alternatives were rejected on tractability grounds: resolving macro-scale groundwater flow alongside micro-scale erosion is computationally prohibitive at reliability sample sizes \parencite{vanderLinde2025}.

### `USACE2000` (3)

- [ ] `3. Study Area, Geological Setting, and Data.tex:129` So defined, it is precisely the riverside blanket length $L_1$ of blanket theory \parencite{USACE2000}, and it enters the model through the finite-width correction $\lambda_\mathrm{out,eff} = \lambda_\mathrm{out}\tanh(B_f/\lambda_\mathrm{out})$ on the entry leakage length, and thence the response factor $r_e$ (Figure~\ref{fig: annotated cross section}).
- [ ] `4. Methodology.tex:417` The hydraulic translation computes, per realization, the fraction of the external river head difference transmitted to the aquifer base at the landside toe, following the leaky-aquifer blanket-theory schematization of \textcite{USACE2000} and \textcite{TAW2004}, which in the no-riverside-blanket special case reduces to the leakage-length formulation of \textcite[Eq.
- [ ] `4. Methodology.tex:453` The response factor is then \begin{equation} r_e = \frac{\lambda_\mathrm{in}} {\lambda_\mathrm{out,eff} + L + \lambda_\mathrm{in}}, \label{eq: response factor} \end{equation} which is the exact closed-form solution of the blanket-theory configuration with a riverside blanket, an under-levee aquifer path, and a semi-infinite hinterland blanket \parencite{USACE2000, TAW2004}.

### `yamada_2018` (3)

- [ ] `3. Study Area, Geological Setting, and Data.tex:366` The ensemble is dynamically downscaled to a 5~km regional model over the basin and converted to discharge through a distributed tank-model runoff chain whose storage parameters are set as a function of the 72-hour basin-averaged rainfall, fitted across five historical floods, so that the many small members of the ensemble are not routed with parameters optimized to a large one \parencite{mizuta_20
- [ ] `appendix-f.tex:32` 75\textdegree{}N, with the domain extended southward over the Pacific to capture the development of approaching typhoons \parencite{yamada_2018}.
- [ ] `appendix-f.tex:37` To make the downscaling of so large an ensemble computationally tractable, the simulation for each event is confined to a 15-day window bracketing the date of the annual-maximum basin-averaged rainfall, comprising a 5-day spin-up followed by the 5 days preceding and the 5 days following the event peak \parencite{yamada_2018}.

### `mlit_river_management_2009` (3)

- [ ] `appendix-g.tex:40` The levee provisions of the MLIT Technical Standards for River and Sabo Works make the setting of allowable values against both sliding failure and piping failure a standard-level requirement, and the Design Guideline for River Levees extends it to existing levees as well as new ones \parencite{mlit_design_standard_2025, mlit_river_management_2009}.
- [ ] `appendix-g.tex:49` That section is modeled from three borings in principle, and only sections failing the resulting check attract remedial works \parencite{pwri_2014, jice_2019, mlit_river_management_2009}.
- [ ] `appendix-g.tex:108` The detailed inspection programme ran across the whole directly managed network: of approximately 10{,}000~km of levee, 8{,}800~km had been verified by March 2008 and the remainder by the end of fiscal 2009 \parencite{mlit_river_management_2009}.

### `minienv_2017` (2)

- [ ] `1. Introduction.tex:11` Probabilistic flood-risk methods, developed internationally and particularly in the Netherlands, evaluate levee systems by failure probability rather than by deterministic exceedance criteria alone \parencite{minienv_2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `mlit_2020` (2)

- [ ] `1. Introduction.tex:18` National levee-failure statistics support that premise \parencite{mlit_2020}.
- [ ] `2. Theoretical and Empirical Foundations.tex:20` National post-disaster analyses lend empirical weight to the traditional prioritization: investigations following the 2019 Typhoon Hagibis event confirmed that overflow remains the primary driver of documented levee failure in Japan \parencite{mlit_2020}.

### `mlit_shinsui_manual_2015` (2)

- [ ] `2. Theoretical and Empirical Foundations.tex:9` Where a binary rule on the HWL does operate it runs the other way: flood-hazard analysis assumes a breach once the river reaches that stage \parencite{mlit_shinsui_manual_2015, uemura_iahs_2024}.
- [ ] `appendix-g.tex:122` Flood-inundation mapping takes the inundation onset stage to be the planned high water level in principle, and assumes breach-induced inundation once the corresponding discharge arrives \parencite{mlit_shinsui_manual_2015}.

### `Yoshikawa2017` (2)

- [ ] `2. Theoretical and Empirical Foundations.tex:127` Localized complexities introduce spatial heterogeneity, but the prevailing bipartite $A_c$/$A_g$ arrangement is analogous to the conditions that contributed to the 2012 Yabe River levee collapse, which occurred through localized piping without concurrent overflow \parencite{yabegawa_2013, Yoshikawa2017}.

### `fukuoka_tabata_2018` (2)

- [ ] `2. Theoretical and Empirical Foundations.tex:183` The dimensionless levee vulnerability index $t^*$ of \textcite{fukuoka_tabata_2018, fukuoka_2019} makes flood duration and levee base width explicit governing variables of a seepage safety measure.
- [ ] `appendix-g.tex:162` The formulation of \textcite{fukuoka_tabata_2018} reproduced above is the derivation of record and is the version used throughout this thesis.

### `bligh_1910` (2)

- [ ] `2. Theoretical and Empirical Foundations.tex:300` The empirical tradition is the creep ratio, relating a permissible head difference linearly to the length of the seepage path through a coefficient read off surveyed structures: the percolation factor of \textcite{bligh_1910}, and the weighted form of \textcite{lane_1935}, which credits vertical path segments more heavily than horizontal ones on the evidence of more than two hundred surveyed dams.
- [ ] `2. Theoretical and Empirical Foundations.tex:324` 430\textwidth}} \toprule Formulation & What it returns & Standing in this study \\ \midrule Empirical creep ratio \parencite{bligh_1910, lane_1935} & A permissible head for a given seepage length, through a coefficient fitted to surveyed structures & Set aside.

### `pol_2021` (2)

- [ ] `2. Theoretical and Empirical Foundations.tex:302` That the critical-head formulations offer no rate at all, and the one duration-conditional predecessor only a constant, reflects how recently pipe growth has been measured through time \parencite{robbins_2017, vandenboer_2019, pol_2021}.
- [ ] `2. Theoretical and Empirical Foundations.tex:367` One model of this class is the upstream source of the rate law below, whose regression form carries those results into samples of the size a tail probability requires \parencite{pol_compgeo_2024} \\ \addlinespace[4pt] Transient progression law \parencite{pol_compgeo_2024, pol_sie_2024} & An instantaneous pipe extension rate $dl/dt$ in the transient head, the aquifer properties and the pipe length,

### `hayashi_2008` (2)

- [ ] `3. Study Area, Geological Setting, and Data.tex:29` \textcite{fukuoka_2019} attribute the absence of foundation leakage and piping in the gently sloping reach downstream to one specific cause: the peaty soft ground beneath those levees has consolidated under the weight of the large embankment to a final-state permeability of order $10^{-11}$~m~s\textsuperscript{-1} \parencite{fukuoka_2019, hayashi_2008}.
- [ ] `appendix-d.tex:401` The second, and the one pertinent to the piping mechanism, concerns the foundation: the authors record that neither foundation leakage nor piping damage was observed, and attribute this specifically to the fact that the peaty soft ground beneath those levees has been consolidated by the weight of the large embankment to a final-state permeability of order $10^{-11}$~m~s\textsuperscript{-1} \parenc

### `pol_ress_2023` (2)

- [ ] `4. Methodology.tex:1416` Following \textcite{pol_ress_2023}, the three mechanisms are treated as conditionally independent given the loading $h$, and the segment failure probability is composed as \begin{equation} P_{f,\mathrm{segment}}(h) = 1 - \prod_{i\,\in\,\{\mathrm{overflow,\;scour,\;BEP}\}} \bigl(1 - P_{f,i}(h)\bigr).
- [ ] `7. Results - System Integration and Climate Sensitivity.tex:140` The composition operates on the 200~meter segment grid inherited from \textcite{uemura_phd_2025}, 114 segments spanning the Tokachi right bank and the Satsunai left bank, and treats the three mechanisms as conditionally independent pathways of a series system at each stage \parencite{pol_ress_2023}.

### `gsi_dem5a` (2)

- [ ] `appendix-d.tex:465` Second, elevation profiles cut across the levee at approximately ten chainages within the segment, taken from the 5~meter airborne-lidar digital elevation model of the Geospatial Information Authority of Japan \parencite{gsi_dem5a}, show a consistent unbermed geometry at every profiled station: a crest standing some 3 to 4~meters above the landside ground, a uniform landside slope of roughly 1:3,
- [ ] `appendix-e.tex:44` 0, is a surveyed value obtained from the 5~meter airborne-lidar digital elevation model of the Geospatial Information Authority of Japan, acquired in June 2025 \parencite{gsi_dem5a}.

### `VanGasteren2000` (1)

- [ ] `1. Introduction.tex:18` ``This is not a river, but a waterfall,'' the Dutch engineer Johannis de Rijke is said to have remarked of a Japanese river during the Meiji period \parencite{VanGasteren2000}.

### `klijn_2015` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `kind_2014` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `vnk2016` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `schweckendiek_2018` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `van_mierlo_2007` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `jongejan_maaskant_2015` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `westerhof_2022` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` These combine conceptual and economic frameworks \parencite{klijn_2015, kind_2014} with operational implementation in national flood risk assessment \parencite{vnk2016}, statutory engineering safety tools \parencite{minienv_2017, schweckendiek_2018}, system-wide failure probability evaluation \parencite{van_mierlo_2007}, and the quantification of risk under deep uncertainty \parencite{jongejan_maa

### `project_plan_2025` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:11` Within the resulting collaboration, estimating levee failure probabilities $P_f$ under transient hydraulic loads and extending the framework to seepage failure mechanisms are identified as explicit research priorities \parencite{final_report_2022, project_plan_2025}.

### `rongen_iahr_2020` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:18` That exclusion rests on the assumption that flood waves in flashy rivers pass too quickly for time-dependent seepage mechanisms to develop to the point of structural breach \parencite{rongen_iahr_2020, wp2_report_2022}.

### `wp2_report_2022` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:18` That exclusion rests on the assumption that flood waves in flashy rivers pass too quickly for time-dependent seepage mechanisms to develop to the point of structural breach \parencite{rongen_iahr_2020, wp2_report_2022}.

### `Ali2025` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:20` Such aggregation may nonetheless obscure residual cases driven by localized erosional or geotechnical mechanisms, and recent investigations identify instances in which conventional verification insufficiently accounted for conductivity contrasts between levee bodies and their foundations, underestimating seepage-induced failure risk \parencite{Ali2025}.

### `van_klaveren_2020` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:172` Coarser sands and gravels progress considerably faster than fine sands \parencite{van_klaveren_2020}, and under the extreme peak discharges characteristic of flashy systems the applied head $H$ may substantially exceed the critical head $H_c$, with progression velocity increasing with the overloading ratio $H/H_c$ \parencite{vandenboer_2019}.

### `uemura_iahr_2020` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:207` Projections of future flood risk in the Tokachi basin are grounded in the d4PDF large-ensemble climate dataset \parencite{mizuta_2017}, dynamically downscaled for Hokkaido through a 5-km regional climate model \parencite{uemura_phd_2025, uemura_iahr_2020}.

### `Nakashima2021` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:211` Japanese geotechnical studies demonstrate that repeated water level fluctuations progressively alter spatial permeability distributions, weaken foundation soils and lower the critical gradient required to initiate particle movement \parencite{Nakashima2021, Nakashima2025, Yoshida2025}.

### `Nakashima2025` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:211` Japanese geotechnical studies demonstrate that repeated water level fluctuations progressively alter spatial permeability distributions, weaken foundation soils and lower the critical gradient required to initiate particle movement \parencite{Nakashima2021, Nakashima2025, Yoshida2025}.

### `Yoshida2025` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:211` Japanese geotechnical studies demonstrate that repeated water level fluctuations progressively alter spatial permeability distributions, weaken foundation soils and lower the critical gradient required to initiate particle movement \parencite{Nakashima2021, Nakashima2025, Yoshida2025}.

### `robbins_2017` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:302` That the critical-head formulations offer no rate at all, and the one duration-conditional predecessor only a constant, reflects how recently pipe growth has been measured through time \parencite{robbins_2017, vandenboer_2019, pol_2021}.

### `van_beek_hoffmans_2017` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:312` The Dutch family has been evaluated as a family \parencite{van_beek_hoffmans_2017} and its numerical branch reviewed separately \parencite{vanderLinde2025}; the test applied here is narrower, and asks only which formulation can express a race between pipe progression and flood recession.

### `sellmeijer_koenders_1991` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:332` It judges an average gradient at a fixed geometry and carries neither a progression rate nor an eroded length, so a loading of finite duration has nothing in it to act on \\ \addlinespace[4pt] Analytical grain-equilibrium critical head \parencite{sellmeijer_1988, sellmeijer_koenders_1991} & The head at which grains at the pipe bottom reach limit equilibrium, from two-dimensional pipe and groundwat

### `vorogushyn_2009` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:345` It judges an average gradient at a fixed geometry and carries neither a progression rate nor an eroded length, so a loading of finite duration has nothing in it to act on \\ \addlinespace[4pt] Analytical grain-equilibrium critical head \parencite{sellmeijer_1988, sellmeijer_koenders_1991} & The head at which grains at the pipe bottom reach limit equilibrium, from two-dimensional pipe and groundwat

### `schweckendiek_2017` (1)

- [ ] `2. Theoretical and Empirical Foundations.tex:402` The foundational framework was established by \textcite{schweckendiek_2014, schweckendiek_2016, schweckendiek_2017} and is institutionalized within the Dutch WBI+ methodology \parencite{hkv_2023}, where the updating is implemented in closed form on the fragility curve and conditioned on a survived historical peak water level.

### `wp1_report_2021` (1)

- [ ] `appendix-d.tex:48` Within the deterministic Japanese flood-safety framework reviewed in Chapter~\ref{chap: Theoretical and Empirical Foundations}, the basin is managed to a planning-scale return period in the range of 100 to 200 years \parencite{final_report_2022, wp1_report_2021}; at the Obihiro, Moiwa, Otofuke and Memuro reference points the design scale is specifically an annual exceedance probability of $1/150$

### `kouzourei_kisoku_1976` (1)

- [ ] `appendix-d.tex:476` Third, the side berm annotated near KP~62 on the 1996 plan sheet, constructed in 1991 to 1992, is classified there as a Class~2 side berm, which under Article~14 of the enforcement regulations of the Structural Ordinance for River Management Facilities is the class provided for stockpiling emergency earth, its length limited to what is required to store approximately the volume of a 10~meter lengt

### `masuya2019spatiotemporal` (1)

- [ ] `appendix-f.tex:52` The downscaled RCM5 precipitation fields, whose spatiotemporal distribution over this basin is analyzed by \textcite{masuya2019spatiotemporal}, are converted to river discharge hydrographs by the distributed two-stage tank model used operationally for flood forecasting in this basin, run on a 1~kilometer grid, with a nonlinear storage equation for the surface and interflow components over a linear

### `Okamura2022` (1)

- [ ] `appendix-g.tex:201` Prototype-scale work has documented a transition from laminar to turbulent pipe flow that introduces an overestimation bias in laminar-derived progression models, which is one motivation for treating the empirical erosion coefficient $C_e$ as a random variable rather than a constant \parencite{Okamura2022, Okamura2025_prediction}.

### `Okamura2025_prediction` (1)

- [ ] `appendix-g.tex:201` Prototype-scale work has documented a transition from laminar to turbulent pipe flow that introduces an overestimation bias in laminar-derived progression models, which is one motivation for treating the empirical erosion coefficient $C_e$ as a random variable rather than a constant \parencite{Okamura2022, Okamura2025_prediction}.

### `Takizawa2018` (1)

- [ ] `appendix-g.tex:204` Post-disaster government reviews of the Tokoro, Yabe and Kinu River failures have demonstrated the vulnerability of layered foundation geologies to piping \parencite{Takizawa2018, tokorogawa_2017, yabegawa_2013}.

### `Tabata2017` (1)

- [ ] `appendix-g.tex:207` And, recognizing the limitations of purely static initiation criteria, recent studies have proposed fatigue-curve concepts based on the combined effect of hydraulic gradient magnitude and loading duration \parencite{Tabata2017, Sawamura2023}, and have emphasized the necessity of stochastic evaluation given the spatial uncertainty of foundation permeability and local stratigraphy \parencite{Nishimu

### `Sawamura2023` (1)

- [ ] `appendix-g.tex:207` And, recognizing the limitations of purely static initiation criteria, recent studies have proposed fatigue-curve concepts based on the combined effect of hydraulic gradient magnitude and loading duration \parencite{Tabata2017, Sawamura2023}, and have emphasized the necessity of stochastic evaluation given the spatial uncertainty of foundation permeability and local stratigraphy \parencite{Nishimu

### `Nishimura2019` (1)

- [ ] `appendix-g.tex:209` And, recognizing the limitations of purely static initiation criteria, recent studies have proposed fatigue-curve concepts based on the combined effect of hydraulic gradient magnitude and loading duration \parencite{Tabata2017, Sawamura2023}, and have emphasized the necessity of stochastic evaluation given the spatial uncertainty of foundation permeability and local stratigraphy \parencite{Nishimu

## UNTOUCHED (named) (6 keys, 38 instances)

### `mlit_design_standard_2025` (8)

- [ ] `1. Introduction.tex:9` The national standard cautions that a levee meeting that requirement is not absolutely safe against floods at or below the planned level, since floods of markedly longer duration than the design event cannot be ruled out \parencite{mlit_design_standard_2025}.
- [ ] `1. Introduction.tex:24` Japanese verification applies sophisticated, time-varying seepage analysis at a representative cross-section of each levee reach, yet ultimately judges safety against a single question: whether a gradient or uplift threshold is exceeded at one instant of the computed pressure field, rather than whether erosion can actually retrogress across the full seepage path before the flood recedes \parencite
- [ ] `2. Theoretical and Empirical Foundations.tex:221` There engineers perform two-dimensional transient saturated-unsaturated seepage analysis driven by actual flood hydrographs, and extract from the resulting pore-pressure field a slope stability factor and two seepage measures \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}.
- [ ] `2. Theoretical and Empirical Foundations.tex:232` Japanese verification practice models the loading as a dynamic process and then judges safety on a single instant of it \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}; the Dutch progression-based framework judges the outcome the mechanism must actually reach, but strips the loading of its time dependence \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:298` Explicit progression models are not generally embedded in Japanese national design verification procedures \parencite{mlit_design_standard_2025, jice_manual_2012}, which helps explain why the gap persists at the system scale.
- [ ] `appendix-g.tex:40` The levee provisions of the MLIT Technical Standards for River and Sabo Works make the setting of allowable values against both sliding failure and piping failure a standard-level requirement, and the Design Guideline for River Levees extends it to existing levees as well as new ones \parencite{mlit_design_standard_2025, mlit_river_management_2009}.
- [ ] `appendix-g.tex:63` They state that a levee built on this basis does not possess absolute safety against floods at or below the planned high water level, and identify floods of markedly longer duration than the design event as the reason \parencite{mlit_design_standard_2025}.

### `ENW2017` (7)

- [ ] `2. Theoretical and Empirical Foundations.tex:30` Consistent with the Dutch treatment of internal erosion \parencite{ENW2017}, the mechanism does not develop as a single instantaneous event but through the sequential prerequisite sub-mechanisms of the Sellmeijer-based composite STPH pathway, set out in Figure~\ref{fig: stph chain}.
- [ ] `2. Theoretical and Empirical Foundations.tex:34` Because the complete mechanism requires all three sub-processes in sequence, the governing conditional failure probability at a given water level is set by whichever sub-mechanism has the lowest individual failure probability \parencite{ENW2017}: $$P_{f,\mathrm{STPH}}(h) = \min\!\bigl(P_{f,\mathrm{uplift}}(h),\; P_{f,\mathrm{heave}}(h),\; P_{f,\mathrm{pipe}}(h)\bigr)$$ The governing condition in t
- [ ] `2. Theoretical and Empirical Foundations.tex:235` Japanese verification practice models the loading as a dynamic process and then judges safety on a single instant of it \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}; the Dutch progression-based framework judges the outcome the mechanism must actually reach, but strips the loading of its time dependence \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:298` This model gives an analytical estimate of the critical head difference $H_c$ above which a pipe retrogressed across the full seepage path is physically possible, and hence the limit state function $Z_\mathrm{static} = H_c - H_\mathrm{load,peak}$ \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:339` It judges an average gradient at a fixed geometry and carries neither a progression rate nor an eroded length, so a loading of finite duration has nothing in it to act on \\ \addlinespace[4pt] Analytical grain-equilibrium critical head \parencite{sellmeijer_1988, sellmeijer_koenders_1991} & The head at which grains at the pipe bottom reach limit equilibrium, from two-dimensional pipe and groundwat
- [ ] `4. Methodology.tex:595` Because the complete STPH mechanism requires initiation and progression in sequence, the governing conditional failure probability at a given level is bounded by the weaker of the two stages \parencite{ENW2017}.
- [ ] `appendix-g.tex:134` The WBI framework evaluates the same composite mechanism, but carries the retrogressive stage into the limit state through the progression-based Sellmeijer rule, which returns the critical head difference above which a fully developed pipe is possible, and combines the three sub-mechanisms by the sequential rule of Section~\ref{subsec: The Sequential STPH Failure Mechanism} \parencite{sellmeijer_1

### `pol_thesis_2022` (7)

- [ ] `2. Theoretical and Empirical Foundations.tex:181` Large-scale physical experiments by \textcite{pol_thesis_2022} demonstrate that exceedance of a critical head does not trigger instantaneous failure: progression is constrained by the sediment transport capacity of the pipe.
- [ ] `2. Theoretical and Empirical Foundations.tex:211` The recovery experiments of \textcite{pol_thesis_2022} confirm only partial recovery after an initial piping event.
- [ ] `2. Theoretical and Empirical Foundations.tex:377` The bridge between dynamic, hydrograph-driven loading and the progression-based probabilistic treatment of piping is the time-dependent framework developed by \textcite{pol_thesis_2022} and formalized in subsequent studies \parencite{pol_compgeo_2024, pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:397` The recovery experiments of \textcite{pol_thesis_2022} bound how much strength returns over a long rest: reloading after nine months produced a 20~per cent lower critical head and a 140~per cent higher progression rate, but the channel itself had closed and erosion restarted from the downstream exit, so what the test attests is a weakened foundation rather than a surviving pipe.
- [ ] `3. Study Area, Geological Setting, and Data.tex:185` In the leakage-length formulation adopted here, following \textcite{pol_thesis_2022} and \textcite{pol_sie_2024}, the foreland and hinterland are instead represented by the leakage lengths $\lambda_\mathrm{out}$ and $\lambda_\mathrm{in}$ and combined with the under-levee path in the response factor $r_e$, which already translates river stage into the aquifer overpressure beneath the levee.
- [ ] `4. Methodology.tex:419` The hydraulic translation computes, per realization, the fraction of the external river head difference transmitted to the aquifer base at the landside toe, following the leaky-aquifer blanket-theory schematization of \textcite{USACE2000} and \textcite{TAW2004}, which in the no-riverside-blanket special case reduces to the leakage-length formulation of \textcite[Eq.~7.13]{pol_thesis_2022}.
- [ ] `4. Methodology.tex:901` The choice is grounded in the large-scale recovery experiments of \textcite{pol_thesis_2022}, in which reloading a partially formed pipe after nine months of rest produced a 20~per cent lower critical head and a 140~per cent higher progression rate.

### `terzaghi1943` (6)

- [ ] `2. Theoretical and Empirical Foundations.tex:34` Should uplift occur, a concentrated seepage exit can form at the landside toe, where the local hydraulic gradient $i_\mathrm{exit}$ may exceed the critical heave gradient $i_c = \gamma'_\mathrm{bl}/\gamma_w$ of \textcite{terzaghi1943}, a condition assessed through $Z_\mathrm{heave} = i_c - i_\mathrm{exit}$.
- [ ] `2. Theoretical and Empirical Foundations.tex:287` Despite the use of transient hydraulic analysis, the failure criterion therefore remains initiation-based: the limit state function $Z_\mathrm{init} = i_c - i_\mathrm{max}$ identifies whether sand boiling can begin, but does not model pipe progression or the conditions required for retrogressive breakthrough \parencite{terzaghi1943, jice_manual_2012}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:336` The critical heave gradient is not a separate calibrated input: consistent with $i_c = \gamma'_\mathrm{bl}/\gamma_w$ \parencite{terzaghi1943} it is computed within each realization from the sampled $\gamma'_\mathrm{bl}$.
- [ ] `4. Methodology.tex:539` Heave is evaluated instantaneously on the exit gradient $i_\mathrm{exit}(t) = \Delta h_\mathrm{blanket}(t)/D_\mathrm{bl}$ against the Terzaghi critical gradient $i_c = \gamma'_\mathrm{bl}/\gamma_w$ \parencite{terzaghi1943}: \begin{equation} Z_\mathrm{heave}(t) = \frac{\gamma'_\mathrm{bl}}{\gamma_w} - \frac{\Delta h_\mathrm{blanket}(t)}{D_\mathrm{bl}}, \end{equation} active while $Z_\mathrm{heave}(
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:224` The initiation gate tests the Terzaghi weight-only balance \parencite{terzaghi1943, pol_sie_2024}: uplift and heave activate when the blanket overpressure exceeds $\gamma'_\mathrm{bl} D_\mathrm{bl}/\gamma_w$, with no cohesion or model factor.
- [ ] `appendix-e.tex:400` The critical heave gradient is likewise not carried as a separate calibrated input: consistent with the formulation $i_c = \gamma'_\mathrm{bl}/\gamma_w$ of Chapter~\ref{chap: Methodology} \parencite{terzaghi1943}, it is computed within each Monte Carlo realization directly from the sampled $\gamma'_\mathrm{bl}$, so that its uncertainty is inherited entirely from that parameter's coefficient of var

### `nakatsugawa_2017` (6)

- [ ] `3. Study Area, Geological Setting, and Data.tex:55` At the Futochanae observatory the design high-water level was exceeded for roughly six hours on 18 August and for approximately 32 hours across 20 to 22 August \parencite{tokorogawa_2017, nakatsugawa_2017, morita_2018}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:57` First, boils at a distance from the embankment may not be directly connected to breaching \parencite{nakatsugawa_2017}.
- [ ] `8. Discussion.tex:971` They are consequently strong against seepage failure and weak against lateral bank erosion and overflow erosion, so that countermeasures should prioritize revetments and groynes \parencite{nakatsugawa_2017}.
- [ ] `appendix-d.tex:314` The JSCE investigation team records the same loading in comparable terms, noting that at Futochanae the design high-water level was exceeded for roughly six hours on 18 August and for approximately 32 hours across 20 to 22 August, and was approached again on 23 August \parencite{nakatsugawa_2017}.
- [ ] `appendix-d.tex:357` The JSCE investigation team observed that the scale and location of sand boiling is strongly governed by the properties of the surrounding ground, and that boils occurring at a distance from the embankment may not be directly connected to breaching; they further noted that at locations which did not breach the soil possessed greater cohesion and that ponded interior water may have suppressed toe e
- [ ] `appendix-g.tex:1377` The post-2016 investigation of the basin states the physical argument directly: because the rivers of the Tokachi system have deposited sand-gravel widely around their channels, levees and foundations composed of that material possess large hydraulic conductivity and high shear strength, and are consequently strong against seepage failure such as piping and slope sliding but weak against lateral b

### `sellmeijer_1988` (4)

- [ ] `2. Theoretical and Empirical Foundations.tex:235` Japanese verification practice models the loading as a dynamic process and then judges safety on a single instant of it \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}; the Dutch progression-based framework judges the outcome the mechanism must actually reach, but strips the loading of its time dependence \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:298` This model gives an analytical estimate of the critical head difference $H_c$ above which a pipe retrogressed across the full seepage path is physically possible, and hence the limit state function $Z_\mathrm{static} = H_c - H_\mathrm{load,peak}$ \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:332` It judges an average gradient at a fixed geometry and carries neither a progression rate nor an eroded length, so a loading of finite duration has nothing in it to act on \\ \addlinespace[4pt] Analytical grain-equilibrium critical head \parencite{sellmeijer_1988, sellmeijer_koenders_1991} & The head at which grains at the pipe bottom reach limit equilibrium, from two-dimensional pipe and groundwat
- [ ] `appendix-g.tex:134` The WBI framework evaluates the same composite mechanism, but carries the retrogressive stage into the limit state through the progression-based Sellmeijer rule, which returns the critical head difference above which a fully developed pipe is possible, and combines the three sub-mechanisms by the sequential rule of Section~\ref{subsec: The Sequential STPH Failure Mechanism} \parencite{sellmeijer_1

## SOURCE-READ (40 keys, 478 instances)

### `oyo_1999` (49)

- [ ] `1. Introduction.tex:20` The Tokachi and Satsunai levees, by contrast, came through the same event without a recorded sand boil \parencite{tokachi_levee_committee_2017}, even though several cross-sections along the Tokachi right bank had already been formally rated as seepage-deficient years earlier \parencite{oyo_1999}.
- [ ] `1. Introduction.tex:81` The geotechnical dataset \parencite{oyo_1999} covers only part of the Tokachi reach with boreholes.
- [ ] `1. Introduction.tex:85` A further complexity of the study reach is the structural heterogeneity left by the remediation works of roughly 1999 to 2003, carried out in response to the 1998 safety assessment \parencite{oyo_1999, fukuda_2025_internal}.
- [ ] `2. Theoretical and Empirical Foundations.tex:38` 5 \parencite{oyo_1999}.
- [ ] `2. Theoretical and Empirical Foundations.tex:127` The basin features a highly permeable alluvial gravel aquifer, denoted locally as the $A_g$ layer and $N_s$ terrace deposits, confined beneath a thin, low-permeability clayey silt blanket designated the $A_c$ layer \parencite{oyo_1999}.
- [ ] `2. Theoretical and Empirical Foundations.tex:177` The 2016 consecutive typhoons produced severe seepage distress on the Tokoro River levees and none at the Tokachi and Satsunai study segments, which share the identical bipartite stratigraphy \parencite{kawajiri_2025, tokorogawa_2017, tokachi_levee_committee_2017, oyo_1999}.
- [ ] `2. Theoretical and Empirical Foundations.tex:287` 2, conducted in 1998 under the predecessor framework to the 2002 national guidelines, rated multiple cross-sections structurally deficient against that criterion and against a landside slope stability factor \parencite{oyo_1999}.
- [ ] `2. Theoretical and Empirical Foundations.tex:406` Prior deterministic evaluations warned of critical piping instability at the study segments on account of the $A_c/A_g$ stratigraphy \parencite{oyo_1999}, yet those same levees survived the most extreme compound flood event in the modern regional record \parencite{tokachi_levee_committee_2017}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:25` The embankments were first raised in 1937 and enlarged through successive reinforcement campaigns, so the present cross-sections embody a patchwork of gravelly, sandy, and cohesive fills over the relict substrate \parencite{kimura_2018, oyo_1999, fukuda_2025_internal}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:34` Notable floods nonetheless occurred, and the basin's levees have also been repeatedly tested by seismic loading \parencite{fukuoka_2019, oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:66` \begin{table}[htbp] \centering \footnotesize \caption[1998 deterministic safety evaluation of the five cross-sections]{1998 deterministic safety evaluation of the five study cross-sections \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:84` The juxtaposition of a formal deterministic deficiency rating \parencite{oyo_1999} with a documented survival of the most extreme compound flood in the regional record \parencite{tokachi_levee_committee_2017} is precisely the type of informative observation that Bayesian reliability updating exploits \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:109` \begin{table}[htbp] \centering \footnotesize \caption[Consolidated per-section model inputs at the five cross-sections]{Consolidated per-section model inputs for the five worked-up OYO cross-sections on the Tokachi right bank \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:131` 04$) is therefore not a demonstration of foreshore control: those values are outputs of OYO's own finite-element model, which schematized a continuous cohesive layer across the entire domain \emph{including} the foreshore \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:137` A formal seepage and slope safety evaluation of the study cross-sections was conducted in 1998 under the predecessor framework to the 2002 national levee design guidelines \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:139` 0 the recorded cause of instability is the toe phreatic rise \emph{together with piping caused by foundation leakage}, attributed to the cohesive $A_c$ layer capping highly permeable ground \parencite{oyo_1999}, so the deficiency at those three is against the under-levee foundation and not through-embankment seepage alone.
- [ ] `3. Study Area, Geological Setting, and Data.tex:152` The foundation stratigraphy of the Tokachi right bank, as logged by \textcite{oyo_1999}, conforms closely to the idealized bipartite configuration that predisposes a levee to the composite STPH failure pathway reviewed in Chapter~\ref{chap: Theoretical and Empirical Foundations} and drawn in Figure~\ref{fig: annotated cross section}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:157` \begin{table}[htbp] \centering \footnotesize \caption[Per-section stratigraphy and model-layer thicknesses]{Per-section stratigraphy and model-layer thicknesses on the Tokachi right bank \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:229` The geotechnical dataset underpinning the prior distributions was acquired during a levee strengthening investigation commissioned for fiscal year 1998 by the Obihiro Development and Construction Department and executed by OYO Corporation \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:242` \begin{table}[htbp] \centering \footnotesize \caption[Field permeability of the $A_g$ aquifer]{Field (in-situ) permeability of the $A_g$ aquifer \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:267` \begin{table}[htbp] \centering \footnotesize \caption[Specified soil constants for the blanket and aquifer units]{Specified soil constants for the blanket ($A_c$) and aquifer ($A_g$) units used in the 1998 seepage computations \parencite{oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:366` The historical safety assessments of the basin adopt a single deterministic design hydrograph \parencite{oyo_1999}.
- [ ] `4. Methodology.tex:432` Since the \textcite{oyo_1999} dataset contains no separate foreland blanket investigation, the foreshore blanket thickness and conductivity take the hinterland $A_c$ values as a proxy, an assumption recorded explicitly as a modeling limitation.
- [ ] `4. Methodology.tex:1202` The event is selected as the calibration constraint for three reasons: it is the most severe compound hydraulic loading in the modern regional record; the study segments came through it without a breach, and the official post-disaster investigation attributed every breach that did occur in the directly managed system to a mechanism other than seepage \parencite{tokachi_levee_committee_2017}; and t
- [ ] `8. Discussion.tex:227` Every one of the five study cross-sections was rated deficient in 1998, three of them with piping caused by foundation leakage named as a cause \parencite{oyo_1999}.
- [ ] `8. Discussion.tex:993` The 1998 evaluation rated all five of the study cross-sections deficient, and named piping caused by foundation leakage as a cause of instability at three of them \parencite{oyo_1999}.
- [ ] `8. Discussion.tex:1128` 23, a relief of 77 and 76~per cent \parencite{oyo_1999}.
- [ ] `appendix-a.tex:11` 2 \parencite{oyo_1999}, together with the independent cross-validation campaigns against which it has been checked.
- [ ] `appendix-a.tex:40` The dataset was acquired during a levee strengthening investigation commissioned for fiscal year 1998 by the Obihiro Development and Construction Department of the Hokkaido Regional Development Bureau and executed by OYO Corporation \parencite{oyo_1999}.
- [ ] `appendix-a.tex:116` \begin{table}[H] \centering \footnotesize \caption[Summary of the OYO borehole program at the five cross-sections]{Summary of the OYO (1999) borehole program at the five evaluated cross-sections \parencite{oyo_1999}.
- [ ] `appendix-a.tex:168` The principal stratigraphic units logged by \textcite{oyo_1999} and their roles in the present model are summarized in Table~\ref{tab:strat_nomenclature}.
- [ ] `appendix-a.tex:181` \begin{table}[H] \centering \footnotesize \caption[Stratigraphic nomenclature and the role of each unit]{Stratigraphic nomenclature of the Tokachi right bank foundation, after the OYO geological legend \parencite{oyo_1999}, with the role assigned to each unit in the present BEP framework.
- [ ] `appendix-a.tex:256` \begin{table}[H] \centering \footnotesize \caption[Complete grain-size analysis results for all samples]{Complete grain-size analysis results for all samples, all boreholes, from the OYO (1999) investigation \parencite{oyo_1999}.
- [ ] `appendix-a.tex:397` \begin{table}[H] \centering \footnotesize \caption[Laboratory permeability results for the $A_g$ aquifer]{Laboratory permeability results for density-adjusted constant-head tests on $A_g$ aquifer specimens \parencite{oyo_1999}.
- [ ] `appendix-a.tex:434` \begin{table}[H] \centering \footnotesize \caption[In-situ field permeability test results for the $A_g$ aquifer]{In-situ field permeability test results for the $A_g$ aquifer \parencite{oyo_1999}.
- [ ] `appendix-a.tex:465` \begin{table}[H] \centering \footnotesize \caption[Consolidated-undrained triaxial shear results for the $A_g$ aquifer]{Consolidated-undrained (CU) triaxial shear test results for $A_g$ aquifer specimens \parencite{oyo_1999}.
- [ ] `appendix-a.tex:505` \begin{table}[H] \centering \footnotesize \caption[Form 5 soil constants for the 1998 computations]{Specified soil constants (Form 5) used in the 1998 seepage and slope-stability computations \parencite{oyo_1999}.
- [ ] `appendix-a.tex:573` Both thresholds are stated in the report's own account of what was computed, and the reach summary form carries those two criteria as its four numeric columns; no uplift or heave criterion appears in either \parencite{oyo_1999}.
- [ ] `appendix-a.tex:612` \begin{table}[H] \centering \footnotesize \caption[1998 safety evaluation: gradient and slope stability]{Results of the 1998 deterministic safety evaluation of the five study cross-sections \parencite{oyo_1999}.
- [ ] `appendix-a.tex:638` \begin{table}[H] \centering \footnotesize \caption[Slope-stability slip-circle detail from Form~7]{Slope-stability slip-circle detail from the 1998 evaluation (Form~7) \parencite{oyo_1999}.
- [ ] `appendix-d.tex:136` 0, a roughly fourteen-fold range within nine kilometers \parencite{oyo_1999}.
- [ ] `appendix-d.tex:170` The basin's levees have also been repeatedly tested by seismic loading, with the 1968 and 2003 Tokachi-oki and the 1993 Kushiro-oki earthquakes each causing embankment damage and motivating the progressive cross-section enlargement program of the lower Tokachi \parencite{fukuoka_2019, oyo_1999}.
- [ ] `appendix-d.tex:214` At the study segments the loading is referenced to the upstream Obihiro gauge rather than to the downstream Moiwa section \parencite{oyo_1999}, and lies within the directly managed reach that rose above the planned high-water level in 2016 \parencite{fukuoka_2019}.
- [ ] `appendix-d.tex:426` The geotechnical foundation for the Tokachi right bank is drawn from the levee strengthening investigation executed by OYO Corporation for the Obihiro Development and Construction Department of the Hokkaido Regional Development Bureau \parencite{oyo_1999}.
- [ ] `appendix-d.tex:463` 0 models a plain trapezoidal levee and leaves the seepage-countermeasure works row blank, so no landside berm was credited even at the time of the deficiency rating \parencite{oyo_1999}.
- [ ] `appendix-e.tex:27` The quantity that the available forms do constrain reliably is the under-levee base width, which is dimensioned on the evaluation cross-section models (Form 5) and reproduced to within a fraction of a meter by the corresponding seepage meshes (Form 6) \parencite{oyo_1999}.
- [ ] `appendix-f.tex:133` \begin{table}[!ht] \centering \footnotesize \caption[External loading conditions from the Form 5 records]{External loading conditions from the Form 5 evaluation records for each cross-section \parencite{oyo_1999}.
- [ ] `appendix-g.tex:1396` Against it stands the 1998 evaluation of the study cross-sections, which rated all five of them deficient and three of the five deficient in exit gradient, with piping caused by foundation leakage named as a cause at each of those three \parencite{oyo_1999}, on the same reach and for the same foundation.

### `pol_sie_2024` (46)

- [ ] `2. Theoretical and Empirical Foundations.tex:18` Probabilistic analyses by \textcite{pol_sie_2024} bear out that intuition for typical scenarios: under short-duration hydraulic loads such as coastal storm surges the reduction relative to steady-state assumptions ranges from a factor of 5, for coarse sand under a thin blanket on a short seepage path, to more than $10^6$ for fine sand on a long one.
- [ ] `2. Theoretical and Empirical Foundations.tex:200` Assessing reliability therefore requires a framework that evaluates the instantaneous progression rate $dl/dt$ rather than only the initiation threshold \parencite{pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:238` That asymmetry is the motivation of this thesis, since neither established framework combines a transient load with a progression criterion, and the third row is that combination \parencite{pol_compgeo_2024, pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:302` The progression law does not merely coexist with it but is built on it: the equilibrium curve $H_\mathrm{eq}(l)$ supplying the resistance side of the rate equation is anchored on the critical head of that rule \parencite{pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:350` A constant rate does not respond to overloading, grain size or aquifer conductivity, which are the dependences that decide the race in a coarse foundation \parencite{pol_sie_2024} \\ \addlinespace[4pt] Numerical erosion simulation \parencite{vanderLinde2025} & Coupled groundwater and pipe flow with an explicit erosion criterion, resolved in two or three dimensions & Not evaluated per realization.
- [ ] `2. Theoretical and Empirical Foundations.tex:362` One model of this class is the upstream source of the rate law below, whose regression form carries those results into samples of the size a tail probability requires \parencite{pol_compgeo_2024} \\ \addlinespace[4pt] Transient progression law \parencite{pol_compgeo_2024, pol_sie_2024} & An instantaneous pipe extension rate $dl/dt$ in the transient head, the aquifer properties and the pipe length,
- [ ] `2. Theoretical and Empirical Foundations.tex:377` The bridge between dynamic, hydrograph-driven loading and the progression-based probabilistic treatment of piping is the time-dependent framework developed by \textcite{pol_thesis_2022} and formalized in subsequent studies \parencite{pol_compgeo_2024, pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:391` Progression is gated by an indicator $I_\mathrm{er}(t)$ that admits erosion only where the transient conditions simultaneously support blanket uplift, active sand heave, and the absence of successful flood-fighting intervention \parencite{pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:404` \textcite{pol_sie_2024} distinguishes aleatory uncertainty, in the time-variant loads, from epistemic uncertainty, in time-invariant levee properties such as $k_\mathrm{aq}$ and $D_\mathrm{bl}$.
- [ ] `3. Study Area, Geological Setting, and Data.tex:185` In the leakage-length formulation adopted here, following \textcite{pol_thesis_2022} and \textcite{pol_sie_2024}, the foreland and hinterland are instead represented by the leakage lengths $\lambda_\mathrm{out}$ and $\lambda_\mathrm{in}$ and combined with the under-levee path in the response factor $r_e$, which already translates river stage into the aquifer overpressure beneath the levee.
- [ ] `3. Study Area, Geological Setting, and Data.tex:289` The stochastic geotechnical parameters are represented by lognormal distributions, consistent with the reliability framework of \textcite{pol_sie_2024} and with standard practice in probabilistic levee assessment.
- [ ] `3. Study Area, Geological Setting, and Data.tex:303` Prior means are sourced from the OYO dataset; coefficients of variation are adopted, wherever a direct correspondence exists, from the base-case reliability parameterization of \textcite{pol_sie_2024}, and otherwise by analogue as recorded in Appendix~\ref{app sec: Data Gaps and Judgment Calls Behind the Priors}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:309` Means are sourced from the OYO dataset as indicated; CoV values are adopted from \textcite{pol_sie_2024} where a direct correspondence exists, and by analogue otherwise (Appendix~\ref{app sec: Data Gaps and Judgment Calls Behind the Priors}).
- [ ] `3. Study Area, Geological Setting, and Data.tex:316` 472 & OYO analysis constant ($A_g$) & \textcite{pol_sie_2024} \\ $d_{70}$ & Lognormal & 0.
- [ ] `3. Study Area, Geological Setting, and Data.tex:318` 100 & OYO borehole panels ($A_g$/$N_s$) & \textcite{pol_sie_2024}, rescaled \\ $D_\mathrm{bl}$ & Lognormal & 0.
- [ ] `3. Study Area, Geological Setting, and Data.tex:319` 166 & OYO borehole panels ($A_c$) & \textcite{pol_sie_2024}, absolute $\sigma$ \\ $k_\mathrm{bl}$ & Lognormal & 0.
- [ ] `3. Study Area, Geological Setting, and Data.tex:321` 056 & OYO Form~5 $\rho_t$ ($A_c$), $\gamma'_\mathrm{bl} = \gamma_\mathrm{sat,bl} - \gamma_w$ & \textcite{pol_sie_2024} ($A_c$ blanket parameterization) \\ $C_e$ & Lognormal & 0.
- [ ] `3. Study Area, Geological Setting, and Data.tex:322` 691 & \textcite{pol_sie_2024} field prior (mean 0.
- [ ] `3. Study Area, Geological Setting, and Data.tex:330` The erosion coefficient $C_e$ is adopted as basin-uniform at the field-reliability base case of \textcite{pol_sie_2024}, and its width warrants specific justification because it is the largest coefficient of variation in the vector.
- [ ] `3. Study Area, Geological Setting, and Data.tex:336` 25$ \parencite{pol_sie_2024}, and the submerged unit weight of the aquifer sand particles $\gamma'_\mathrm{p} = 16.
- [ ] `4. Methodology.tex:380` $h(t)$ is the river stage, $h_p$ its event peak, and $z_\mathrm{toe}$ the landside toe elevation, which serves as both the head-translation datum and the seepage exit reference $h_e$ of \textcite{pol_sie_2024}.
- [ ] `4. Methodology.tex:419` In \textcite{pol_sie_2024} the resulting response factor enters as a prescribed scalar input (their Eq.
- [ ] `4. Methodology.tex:554` The gating condition for pipe progression at timestep $t$ is the binary erosion indicator \begin{equation} I_\mathrm{er}(t) = \Bigl[\min_{0\le\tau\le t}\{Z_\mathrm{uplift}(\tau)\} < 0 \;\cup\; l(t) > 0\Bigr]\;\cap\;\bigl[Z_\mathrm{heave}(t) < 0\bigr], \label{eq: erosion indicator} \end{equation} following \textcite{pol_sie_2024}: progression requires that uplift has occurred at some earlier moment
- [ ] `4. Methodology.tex:640` 3\,D_\mathrm{bl}$ of Equation~\eqref{eq: erosion head} \parencite{schweckendiek_2014, pol_sie_2024}.
- [ ] `4. Methodology.tex:657` The reduction enters through Dutch levee-safety assessment practice instead: \textcite{schweckendiek_2014} applies it to the static limit state itself, in the criterion stated for near-future Dutch assessments, and \textcite{pol_sie_2024} adopts the same reduction into the transient erosion head of Equation~\eqref{eq: erosion head} by citing that practice rather than deriving it.
- [ ] `4. Methodology.tex:719` 12)$ \parencite{pol_sie_2024} is enabled, it multiplies this single-source $H_c$ in both of its uses, one model-form belief per realization.
- [ ] `4. Methodology.tex:765` ~(6) of \textcite{pol_sie_2024}.
- [ ] `4. Methodology.tex:789` Following \textcite{pol_sie_2024}, it is parameterized by piecewise linear interpolation between three anchors, \begin{equation} H_\mathrm{eq}(0) = 0,\qquad H_\mathrm{eq}(l_c) = H_c,\qquad H_\mathrm{eq}(L) = 0.
- [ ] `4. Methodology.tex:829` The progression ODE is integrated by forward Euler, consistent with \textcite{pol_compgeo_2024} and \textcite{pol_sie_2024}.
- [ ] `4. Methodology.tex:898` Between separate events the general formulation scales the residual length by a recovery parameter, $l_{\mathrm{ini},\,n+1} = (1 - r_l)\cdot l_{e,\,n}$ \parencite{pol_sie_2024}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:58` ~(6) and~(8) of \textcite{pol_sie_2024}, that the erosion-driving head and the equilibrium curve share the exit datum $h_e = z_\mathrm{toe}$, and that the crack-resistance term is subtracted exactly once, on the load side.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:224` The initiation gate tests the Terzaghi weight-only balance \parencite{terzaghi1943, pol_sie_2024}: uplift and heave activate when the blanket overpressure exceeds $\gamma'_\mathrm{bl} D_\mathrm{bl}/\gamma_w$, with no cohesion or model factor.
- [ ] `8. Discussion.tex:71` That magnitude is consistent with an independent published expectation for this configuration class: \textcite{pol_sie_2024} report that the effect of time-dependence stays below five for river levees on coarse sand beneath a thin blanket, and that the conventional assumption of instantaneous failure can be considered realistic there.
- [ ] `8. Discussion.tex:79` 3\,D_\mathrm{bl}$ is, in any case, a genuine resistance within the transient formulation, the head loss incurred by vertical seepage through the fluidized sediment column above the pipe \parencite{pol_sie_2024}, but the static rule of \textcite{sellmeijer_2011} has no counterpart to it, not because the term is implausible but because it is absent from that rule's own calibration: the reduction ent
- [ ] `8. Discussion.tex:83` 3\,D_\mathrm{bl}$ is, in any case, a genuine resistance within the transient formulation, the head loss incurred by vertical seepage through the fluidized sediment column above the pipe \parencite{pol_sie_2024}, but the static rule of \textcite{sellmeijer_2011} has no counterpart to it, not because the term is implausible but because it is absent from that rule's own calibration: the reduction ent
- [ ] `appendix-e.tex:251` 056$ adopted directly from the blanket parameterization of \textcite{pol_sie_2024}.
- [ ] `appendix-e.tex:264` The bedding angle, the relative density, the uniformity coefficient, and the grain angularity are held deterministic, the latter three being set to their experimental mean values so that their contributions to the Sellmeijer resistance factor reduce to unity, following the conventions of \textcite{sellmeijer_2011} and \textcite{pol_sie_2024}.
- [ ] `appendix-e.tex:330` 25$ \parencite{pol_sie_2024}, and the submerged unit weight of the aquifer sand particles $\gamma'_\mathrm{p}$.
- [ ] `appendix-e.tex:383` Pol's uplift model factor $m_u$ \parencite{pol_sie_2024} is deliberately not carried: the field-case campaign of Chapter~\ref{chap: Verification, Validation, and Sensitivity} finds no detectable bias in the weight-only uplift criterion when it is supplied with calibrated seepage heads, so softening or widening it with an uncalibrated factor is not supported by the evidence available.
- [ ] `appendix-e.tex:388` 12)$ \parencite{schweckendiek_2014, pol_sie_2024}, which represents the model uncertainty of the revised critical-head rule, fitted to observed against predicted critical heads and centred on unity because that rule is practically unbiased, is carried as an optional, independently drawn multiplier on the single-source critical head, applied identically to the static comparator and to the transient
- [ ] `appendix-e.tex:487` The blanket conductivity $k_\mathrm{bl}$ has no entry in the reliability parameterization of \textcite{pol_sie_2024}, which fixes the response factor $r_e$ deterministically; because the present framework instead derives $r_e$ from $k_\mathrm{bl}$ through the Mazure leakage-length relation, a conductivity coefficient of variation equal to that of $k_\mathrm{aq}$ is adopted.
- [ ] `appendix-e.tex:505` This is the field-reliability base case of \textcite{pol_sie_2024} and, following the model author's own recommendation, it is retained as the production prior; the two calibration targets behind it, and the reason the width is a mean ambiguity rather than a measured spread, are set out in Section~\ref{subsec: Distributional Family and Lognormal Transform}.
- [ ] `appendix-g.tex:278` ~(6) and~(8) of \textcite{pol_sie_2024}: the erosion-driving head and the equilibrium curve share the exit datum $h_e = z_\mathrm{toe}$, and the crack-resistance term is subtracted exactly once and on the load side.

### `tokachi_chisuishi_2023` (40)

- [ ] `1. Introduction.tex:18` It has never had to be tested, because the criterion in use judges a single instant and carries no record of erosion already done, though the standard has demanded regard to duration since the 1970s \parencite{tokachi_chisuishi_2023}.
- [ ] `2. Theoretical and Empirical Foundations.tex:289` The provision on leakage prevention in the Technical Standards for River and Sabo Works, as applied in this basin from the late 1970s, requires that a levee be so structured as not to give rise to quicksand or piping phenomena, having regard to the embankment material, the foundation material, the water level, \emph{and the duration of high water} \parencite{tokachi_chisuishi_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:18` The consequence side of the risk is correspondingly concentrated: some 158{,}000 people reside within the assumed inundation area, and the basin accounts for roughly 26 per cent of Hokkaido's agricultural output by value, the largest share of any region in the prefecture \parencite{tokachi_chisuishi_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:20` The basin is managed to an annual exceedance probability of $1/150$ at the Obihiro reference point, and the planned high-water level that this design scale supports, referred to hereafter as the design high water level, is the reference stage against which every fragility curve in this thesis is read \parencite{tokachi_chisuishi_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:50` That reach lies on the outer bank of a bend, where superelevation raises the level above the section-averaged value a one-dimensional rating returns \parencite{tokachi_chisuishi_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:59` The strongest form of the observation is that the mechanism did not produce a breach anywhere in the directly managed Tokachi system: the Tokachi River Levee Investigation Committee attributed each of the three breaches that did occur to a mechanism other than seepage \parencite{tokachi_chisuishi_2023, tokachi_levee_committee_2017}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:180` Japanese design guidance identifies levees founded along, or cutting across, former river channels as a leading cause of elevated leakage risk, and both configurations are documented in this basin \parencite{pwri_2014, tokachi_chisuishi_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:370` on 31 August 2016, reproducing the officially published peak stage exactly, as do the concurrent record maxima at the three downstream stations \parencite{tokachi_chisuishi_2023}.
- [ ] `7. Results - System Integration and Climate Sensitivity.tex:775` The design flood scale adopted for this basin is 1 in 150 years \parencite{tokachi_chisuishi_2023}, an exceedance frequency of a discharge.
- [ ] `8. Discussion.tex:525` This raises the basic high-water discharge at Obihiro from 6{,}800 to 9{,}700~m\textsuperscript{3}/s \parencite{tokachi_chisuishi_2023}.
- [ ] `8. Discussion.tex:927` The state variable the represented set lacks is the remaining high-water-bed width, which is the variable Japanese practice on this river already uses to manage the mechanism \parencite{tokachi_chisuishi_2023}, and which is already surveyed at the four cross-sections.
- [ ] `8. Discussion.tex:1156` 3, with conduits of 28 and 27~m against modeled under-levee seepage paths of 40 and 33~m \parencite{tokachi_chisuishi_2023}.
- [ ] `8. Discussion.tex:1163` Leakage is represented through the foundation alone, whereas the official characterization describes a compound regime involving the embankment as well \parencite{tokachi_chisuishi_2023}.
- [ ] `9. Conclusions and Recommendations.tex:548` The revised policy raises the basic high-water discharge at Obihiro from 6{,}800 to 9{,}700~m\textsuperscript{3}/s at an unchanged $1/150$ design scale \parencite{tokachi_chisuishi_2023}, an increase that has to be accommodated, and wherever it is accommodated by raising the crest the applied head rises at an unchanged seepage length.
- [ ] `appendix-a.tex:205` Groundwater observation and drawdown prediction undertaken for those works characterize the floodplain aquifer as a sand-gravel unit of 15 to 20~m thickness with a hydraulic conductivity of $10^{-1}$ to $10^{0}$~cm~s\textsuperscript{-1}, that is $10^{-3}$ to $10^{-2}$~m~s\textsuperscript{-1}, and record a hinterland groundwater table standing only 2 to 4~m below the ground surface \parencite{tokac
- [ ] `appendix-a.tex:212` Separately, the same investigation documents that the Chiyoda weir induces a pronounced bypass seepage circulation, with the river recharging the hinterland upstream of the weir and the hinterland draining toward the river downstream of it \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-a.tex:232` In the Otofuke urban reach levees were in many places constructed longitudinally along former channels, which is recorded as the explicit reason that reach was assigned high leakage risk and high remediation priority from 1976 onward; and on the Satsunai, the confinement of a formerly braided channel into a 400 to 450~meter levee corridor over some seventeen years left reaches in which the levees
- [ ] `appendix-d.tex:24` 7~km\textsuperscript{2}, and the basin accounts for about 26 per cent of Hokkaido's agricultural output by value, the largest share of any region in the prefecture, on some 260{,}000~hectares of cropland growing wheat, sugar beet, potato and pulses at a local food self-sufficiency ratio of about 1{,}340 per cent \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:25` Land use is approximately 63 per cent forest, 29 per cent agricultural and 1 per cent urban \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:50` Within the deterministic Japanese flood-safety framework reviewed in Chapter~\ref{chap: Theoretical and Empirical Foundations}, the basin is managed to a planning-scale return period in the range of 100 to 200 years \parencite{final_report_2022, wp1_report_2021}; at the Obihiro, Moiwa, Otofuke and Memuro reference points the design scale is specifically an annual exceedance probability of $1/150$
- [ ] `appendix-d.tex:57` 8~mm because the design scale changes from $1/150$ to $1/100$ across the Totabetsu confluence \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:70` , and the September 2022 revision retains that value unchanged, reasoning explicitly that raising the planned level would increase disaster potential in a built-up reach \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:95` This yields design rainfall depths of 297~mm over 48~hours at Obihiro and 247~mm over 48~hours at Moiwa, and the resulting basic high-water peak discharges are set at 9{,}700~m\textsuperscript{3}/s at Obihiro and 21{,}000~m\textsuperscript{3}/s at Moiwa, against 6{,}800 and 15{,}200~m\textsuperscript{3}/s in the preceding plan \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:98` The revised figures are established from a combination of frequency analysis with the rainfall factor applied, ensemble projected rainfall waveforms drawn from climate models under the 2\,\textdegree C scenario, and stretching of historical flood hydrographs \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:139` Three further attributes of the reach, all documented in the official flood-control history of the basin, bear on how the results should be read \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:156` 7 (1980), and the Nakajima Bridge \parencite{fukuda_2025_internal, tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:208` \ with corresponding peak discharges of 1{,}195, 1{,}951 and 6{,}334~m\textsuperscript{3}~s\textsuperscript{-1} \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:211` 84~m reached during the August 1981 flood, itself the largest event on the main stem since 1922 \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:219` After \textcite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:251` The reach was formerly constricted as well, where the Kino levee projected into the channel at the Tokachi Ohashi and left a width of 370~m against a planned 500~m, but that constriction was removed by the set-back levee and bridge replacement completed in 1998, eighteen years before the event \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:279` 31~m \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:375` The Tokachi River Levee Investigation Committee attributed each to a mechanism other than seepage \parencite{tokachi_chisuishi_2023, tokachi_levee_committee_2017}.
- [ ] `appendix-f.tex:94` That observed peak reproduces the officially published peak stage for the event exactly, as do the concurrent record maxima at Memurobuto, Chiyoda and Moiwa \parencite{tokachi_chisuishi_2023}, which verifies the head of the Phase~2 loading chain against an independent published source.
- [ ] `appendix-g.tex:357` The hydrological analysis supporting the 2022 revision of the basin's fundamental river management policy estimates flood concentration times at the Obihiro reference point over seventeen gauged floods spanning 1961 to 2016, obtaining 11 to 19~hours (mean 15) by the Kadoya formula and 7 to 47~hours (mean 24) by a kinematic-wave method \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-g.tex:1380` The official basin flood-control history reaches the same conclusion for the Satsunai specifically, recording that the majority of disaster causes there, including breaching, were attributable to bank erosion \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-g.tex:1402` The empirical component is recorded in the same history: all three levee breaches in the directly managed Tokachi system in 2016 were officially attributed to mechanisms other than seepage, two to channel migration and bank erosion during the falling limb and one to landside overtopping following a tributary breach \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-g.tex:1433` 0 by landside overtopping following a tributary breach \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-g.tex:1438` The full-scale experiments run on the Chiyoda experimental channel, commissioned to explain the 2016 breaches, examined a related pathway: scour developing behind the low-water revetment at the outer bank of a bend once the stage approaches the planned high-water level, and its propagation landward into the embankment \parencite{tokachi_chisuishi_2023}.
- [ ] `appendix-g.tex:1478` The retreat rate is the weak link: no calibrated lateral rate exists here, and the one documented datum is the 2011 account of an Otofuke levee losing roughly five meters of length per hour to high-water-bed erosion \parencite{tokachi_chisuishi_2023}.

### `pwri_2014` (31)

- [ ] `1. Introduction.tex:9` Backward erosion piping (BEP) is verified separately, reach by reach across the directly managed levee network \parencite{mlit_design_standard_2025, pwri_2014}, but that verification returns a pass or a fail at one design stage.
- [ ] `2. Theoretical and Empirical Foundations.tex:9` 8~per cent of the directly managed levee network \parencite{pwri_2014}.
- [ ] `2. Theoretical and Empirical Foundations.tex:122` Japanese design guidance describes the same sequence in the same order, from toe gradient and sand boiling through blanket heave and rupture to the progressive formation of a pipe-shaped flow path toward the riverside \parencite{pwri_2014}.
- [ ] `2. Theoretical and Empirical Foundations.tex:221` Japanese levee safety verification employs advanced transient hydraulic analysis, and applies it reach by reach rather than profile by profile: a continuous levee is subdivided by foundation soil, microtopography and embankment shape, and the cross-section most severe for seepage is verified as representative of each subdivision \parencite{pwri_2014, jice_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:223` Verification of both sliding and piping is performed at the instant at which the high-water duration terminates rather than at the hydrograph peak, so a longer high-water period does yield a higher phreatic surface and steeper toe gradients \parencite{pwri_2014}.
- [ ] `2. Theoretical and Empirical Foundations.tex:232` Japanese verification practice models the loading as a dynamic process and then judges safety on a single instant of it \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}; the Dutch progression-based framework judges the outcome the mechanism must actually reach, but strips the loading of its time dependence \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:291` Verification against piping and heave is in principle waived where a cohesive blanket of approximately 3~m or more overlies the foundation of a levee no more than 10~m high \parencite{pwri_2014, jice_2019}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:98` It is also the spacing at which the national seepage-screening procedure specifies that cross-section survey data be collected and the levee vulnerability index be evaluated \parencite{jice_2019, pwri_2014}, so the adopted discretization matches the resolution at which the governing data are acquired.
- [ ] `3. Study Area, Geological Setting, and Data.tex:180` Japanese design guidance identifies levees founded along, or cutting across, former river channels as a leading cause of elevated leakage risk, and both configurations are documented in this basin \parencite{pwri_2014, tokachi_chisuishi_2023}.
- [ ] `8. Discussion.tex:485` Verification against piping and heave is waived where levee height is under 10~m and a cohesive blanket of approximately 3~m or more is present \parencite{pwri_2014}.
- [ ] `8. Discussion.tex:1020` 1~per cent of the roughly 10{,}000~km of directly managed levee \parencite{pwri_2014}.
- [ ] `8. Discussion.tex:1085` That span, and not the half-band, is the quantity comparable to the factor of several to about ten by which Japanese guidance characterizes ordinary measured scatter \parencite{pwri_2014}, and it sits inside that range rather than below it.
- [ ] `8. Discussion.tex:1109` Japanese guidance names the physical quantity each countermeasure acts upon, and every one maps onto a quantity already in the model \parencite{pwri_2014}.
- [ ] `9. Conclusions and Recommendations.tex:537` 85~m, fall a factor of three to seven short of the roughly 3~m of cohesive cover that waives verification \parencite{pwri_2014}, so this reach is not sheltered by the exemption.
- [ ] `9. Conclusions and Recommendations.tex:650` The bracketing sensitivity on the model quantities Japanese guidance names \parencite{pwri_2014} has been carried out and is no longer the gap & How much of the bracket at KP~58.
- [ ] `appendix-a.tex:226` Japanese design guidance identifies levees founded along former river channels as a leading cause of elevated leakage risk, because a buried palaeochannel provides a high-permeability path beneath or beside the embankment, and it identifies the complementary configuration, in which a low-permeability layer beneath the landside toe forms a blocked or dead-end foundation, as promoting leakage and pi
- [ ] `appendix-d.tex:366` The corresponding caution in Japanese design guidance is that field records of leakage carry two distinct meanings: clear-water leakage indicates no piping risk and can in fact be used to back-calculate embankment permeability, whereas turbid, sediment-carrying leakage indicates internal erosion and, in the worst case, an existing cavity \parencite{pwri_2014}.
- [ ] `appendix-d.tex:414` The national procedure for seepage screening specifies that cross-section survey data be collected at intervals of approximately 200~meters and that the levee vulnerability index be evaluated at the distance markers, 200~meter spacing being the standard, while borehole investigations exist at 200 to 400~meter spacing where survey density is high \parencite{jice_2019, pwri_2014}.
- [ ] `appendix-e.tex:213` 056$ closely \parencite{pwri_2014}.
- [ ] `appendix-e.tex:215` For hydraulic conductivity, the same guidance characterizes the ordinary scatter of measured values as spanning a factor of several to about ten \parencite{pwri_2014}.
- [ ] `appendix-g.tex:29` As the river stage rises and the hydraulic gradient near the landside toe increases, seepage failure occurs and sand boiling begins; where a blanket overlies the landside foundation, pressure acts on its underside and produces heave once sufficiently large; further pressure ruptures the blanket and leakage with sand boiling follows; and where such boiling continues, a pipe-shaped flow path is prog
- [ ] `appendix-g.tex:49` That section is modeled from three borings in principle, and only sections failing the resulting check attract remedial works \parencite{pwri_2014, jice_2019, mlit_river_management_2009}.
- [ ] `appendix-g.tex:58` An initial-rainfall seepage computation establishes the pre-flood condition; a second computation is then driven by the design stage hydrograph together with the design rainfall; and the phreatic surface that results supplies the pore pressures from which the safety measures are evaluated \parencite{pwri_2014, jice_2019}.
- [ ] `appendix-g.tex:77` Where a blanket is present, the governing measure is instead the heave ratio $G/W$, the weight of the blanket layer divided by the uplift pressure acting on its base, with $G/W \leq 1$ marking the deficient condition \parencite{mlit_teibou_sekkei_2007, pwri_2014, jice_2019}.
- [ ] `appendix-g.tex:87` The verification of both sliding and piping is performed at the instant at which the high-water duration terminates rather than at the instantaneous hydrograph peak \parencite{pwri_2014}.
- [ ] `appendix-g.tex:90` And because the computed local gradient is mesh-dependent, the guidance prescribes a seepage-flow element size no larger than approximately one tenth of the levee height and requires the evaluation point to lie beneath the phreatic line \parencite{pwri_2014}.
- [ ] `appendix-g.tex:101` Where the levee height does not exceed 10~m and a cohesive blanket of approximately 3~m or more overlies the foundation, verification against piping and heave is in principle waived, and the section is excluded from the foundation-leakage screening even where a permeable layer is known to lie beneath the blanket \parencite{pwri_2014, jice_2019}.
- [ ] `appendix-g.tex:112` 8~per cent fails the piping check alone while passing both slope checks \parencite{pwri_2014}.
- [ ] `appendix-g.tex:114` Landside slope sliding and landside-toe piping are the two most frequent grounds nationally for requiring structural works \parencite{pwri_2014}.

### `uemura_phd_2025` (31)

- [ ] `1. Introduction.tex:13` Within that collaboration, \textcite{uemura_phd_2025} developed a Monte Carlo levee-failure framework for the Tokachi and Satsunai reaches around Obihiro, but limited it to the surface failure mechanisms of overflow and fluvial scour.
- [ ] `1. Introduction.tex:41` \item Formulate a unified multi-mechanism levee risk profile, integrating the calibrated posterior piping probabilities with the overflow and fluvial-scour surface fragilities of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024} through series-system joint-probability equations.
- [ ] `1. Introduction.tex:81` To integrate cleanly with the baseline multi-mechanism risk profile of \textcite{uemura_phd_2025}, the study adopts his discretization and works within his spatial boundaries.
- [ ] `1. Introduction.tex:90` The climatological boundary is set by the hydrographs available in the dynamically downscaled d4PDF ensemble of \textcite{uemura_phd_2025}: the 5-km regional climate model (RCM5) outputs for the Hokkaido region.
- [ ] `1. Introduction.tex:195` In Phase 3 the calibrated piping fragility is combined with the overflow and fluvial scour mechanisms of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024}, obtained by re-executing the original failure-judgment models on their own per-node inputs (Chapter~\ref{chap: Methodology}).
- [ ] `2. Theoretical and Empirical Foundations.tex:207` Projections of future flood risk in the Tokachi basin are grounded in the d4PDF large-ensemble climate dataset \parencite{mizuta_2017}, dynamically downscaled for Hokkaido through a 5-km regional climate model \parencite{uemura_phd_2025, uemura_iahr_2020}.
- [ ] `2. Theoretical and Empirical Foundations.tex:293` At the basin scale, system-wide assessment remains dominated by overflow-based judgment, non-overflow mechanisms being treated as secondary \parencite{uemura_iahs_2024, uemura_phd_2025, final_report_2022}.
- [ ] `2. Theoretical and Empirical Foundations.tex:372` The most relevant antecedent for regional probabilistic assessment is the Monte Carlo levee failure evaluation model for the Tokachi and Satsunai Rivers developed by \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:411` Components of transient, probabilistic and progression-based piping assessment exist in isolation, in the transient progression framework \parencite{pol_compgeo_2024}, the pre-calculated surface failure models for the Tokachi basin \parencite{uemura_phd_2025}, and the Bayesian updating mechanisms \parencite{schweckendiek_2014}, but their integration remains largely absent from operational system-s
- [ ] `3. Study Area, Geological Setting, and Data.tex:27` That pathway enters the integrated framework through the pre-calculated scour fragility of \textcite{uemura_phd_2025}, so the present work can isolate the contribution of backward erosion piping.
- [ ] `3. Study Area, Geological Setting, and Data.tex:38` These morphodynamic and fluvial-scour failures are represented in the integrated framework through the pre-calculated surface fragility of \textcite{uemura_phd_2025}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:366` The ensemble is dynamically downscaled to a 5~km regional model over the basin and converted to discharge through a distributed tank-model runoff chain whose storage parameters are set as a function of the 72-hour basin-averaged rainfall, fitted across five historical floods, so that the many small members of the ensemble are not routed with parameters optimized to a large one \parencite{mizuta_20
- [ ] `3. Study Area, Geological Setting, and Data.tex:368` This confirms that the temporal and spatial concentration of rainfall, and not merely its magnitude, governs the resulting loading \parencite{uemura_phd_2025}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:370` The discharge hydrographs are converted to stage at each cross-section through the station-specific rating relation carried with the antecedent framework \parencite{uemura_phd_2025}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:374` To generate a multi-mechanism risk profile without redeveloping the surface-mechanism physics, the overflow and fluvial scour assessments of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024} are incorporated into the Phase~3 integration.
- [ ] `4. Methodology.tex:19` Phase~3 integrates the resulting posterior BEP curves with the surface failure fragility curves of \textcite{uemura_phd_2025} through series-system joint-probability mathematics.
- [ ] `4. Methodology.tex:78` 7cm of history] (uemura_curves) {\textbf{Surface Failure Models}\\(Overflow \& Scour)\\ \textit{[\cite{uemura_phd_2025}]}}; % Column 2: Physical & System Processes \node [process, right=0.
- [ ] `4. Methodology.tex:277` 9) {\textbf{Surface Fragility Curves}\\ \mdseries(Overflow \& Scour,\\re-executed)\\ \textit{[\cite{uemura_phd_2025}]}}; \node (out) [final_output] at (0, -14.
- [ ] `4. Methodology.tex:329` Phase~3: the posterior BEP curve is integrated with the re-executed overflow and scour fragilities of \textcite{uemura_phd_2025} via series-system joint-probability mathematics, yielding the unified system fragility $P_{f,\mathrm{sys}}$.
- [ ] `4. Methodology.tex:1113` All ingestion of the loading data and all unit handling, including the conversion of discharge to stage through the per-node rating relation $h = \sqrt{Q/a_\mathrm{kp}} - b_\mathrm{kp}$ of the antecedent framework \parencite{uemura_phd_2025, uemura_iahs_2024}, is performed at a single boundary of the framework.
- [ ] `4. Methodology.tex:1358` It takes the Phase~1 and Phase~2 fragility curves, the re-executed surface fragility curves, and the d4PDF hazard, and composes them on the 200-meter segment grid inherited from \textcite{uemura_phd_2025}.
- [ ] `4. Methodology.tex:1390` The overflow and fluvial scour curves are produced by re-executing Uemura's own failure-judgment models on his own consolidated per-segment inputs: the overflow model applies cumulative damage theory to the time-integrated overtopping flow velocity \parencite{dean_2010, uemura_phd_2025} and the scour model a time-integrated excess bed shear formulation following USACE practice, both as established
- [ ] `7. Results - System Integration and Climate Sensitivity.tex:23` And the surface mechanisms enter as re-executions of the failure-judgment models of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024} on their own per-segment inputs, adapted in the two respects of Section~\ref{sec: Pre-Calculated Surface Failure Fragility Curves from Uemura (2025)} and conditioned on the same canonical loading shape and delivered on the same stage axis as the piping branc
- [ ] `7. Results - System Integration and Climate Sensitivity.tex:137` The composition operates on the 200~meter segment grid inherited from \textcite{uemura_phd_2025}, 114 segments spanning the Tokachi right bank and the Satsunai left bank, and treats the three mechanisms as conditionally independent pathways of a series system at each stage \parencite{pol_ress_2023}.
- [ ] `appendix-d.tex:198` These morphodynamic and fluvial-scour failures are represented in the integrated framework through the pre-calculated surface fragility of \textcite{uemura_phd_2025}.
- [ ] `appendix-e.tex:45` The levee alignment is chained from the section geometry of the antecedent framework \parencite{uemura_phd_2025}, profiles are cut perpendicular to the local tangent at 1~meter spacing, and the crest and both toes are picked by a stated slope-break rule: a crest band of 0.
- [ ] `appendix-f.tex:55` The downscaled RCM5 precipitation fields, whose spatiotemporal distribution over this basin is analyzed by \textcite{masuya2019spatiotemporal}, are converted to river discharge hydrographs by the distributed two-stage tank model used operationally for flood forecasting in this basin, run on a 1~kilometer grid, with a nonlinear storage equation for the surface and interflow components over a linear
- [ ] `appendix-f.tex:59` \textcite{uemura_phd_2025} measures that effect rather than asserting it: optimized to the September 2011 flood alone the model returns a median annual-maximum peak discharge of 1{,}294~m\textsuperscript{3}/s over the 3{,}000 historical cases, and optimized to the August 2016 flood alone 2{,}542~m\textsuperscript{3}/s, against 647~m\textsuperscript{3}/s observed.
- [ ] `appendix-f.tex:76` The discharge hydrographs are converted to time series of river stage at each evaluation cross-section through a station-specific stage-discharge rating relation of the form $h = \sqrt{Q/a_\mathrm{kp}} - b_\mathrm{kp}$, whose per-kilometer-post coefficients are those carried with the antecedent framework \parencite{uemura_phd_2025, uemura_iahs_2024}.
- [ ] `appendix-f.tex:84` 03$ at the interface with riparian tree stands, the latter delineated as dead-water zones from aerial-photograph interpretation \parencite{uemura_phd_2025}.

### `sellmeijer_2011` (30)

- [ ] `1. Introduction.tex:37` Benchmark the time-dependent BEP framework against a static application of the \textcite{sellmeijer_2011} model on one shared sample of realizations, and decompose the bias into the modeling ingredients that generate it: the finite duration of the flood loading, the differing driving-head conventions of the two limit states, the initiation gate, the plane-strain versus three-dimensional scale expo
- [ ] `2. Theoretical and Empirical Foundations.tex:235` Japanese verification practice models the loading as a dynamic process and then judges safety on a single instant of it \parencite{mlit_design_standard_2025, jice_manual_2012, pwri_2014}; the Dutch progression-based framework judges the outcome the mechanism must actually reach, but strips the loading of its time dependence \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:298` This model gives an analytical estimate of the critical head difference $H_c$ above which a pipe retrogressed across the full seepage path is physically possible, and hence the limit state function $Z_\mathrm{static} = H_c - H_\mathrm{load,peak}$ \parencite{sellmeijer_1988, sellmeijer_2011, ENW2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:302` That reduction is the positive case for the rule of \textcite{sellmeijer_2011}.
- [ ] `2. Theoretical and Empirical Foundations.tex:304` 430~mm \parencite{sellmeijer_2011}, and three of the four study cross-sections lie above that range even on the finer of the two readings of the foundation gradation.
- [ ] `2. Theoretical and Empirical Foundations.tex:339` It judges an average gradient at a fixed geometry and carries neither a progression rate nor an eroded length, so a loading of finite duration has nothing in it to act on \\ \addlinespace[4pt] Analytical grain-equilibrium critical head \parencite{sellmeijer_1988, sellmeijer_koenders_1991} & The head at which grains at the pipe bottom reach limit equilibrium, from two-dimensional pipe and groundwat
- [ ] `2. Theoretical and Empirical Foundations.tex:389` The equilibrium curve $H_\mathrm{eq}(l)$ represents the resistance side, anchored on the critical head $H_c$ of the \textcite{sellmeijer_2011} model and interpolated between initiation, the critical pipe length and the upstream boundary.
- [ ] `3. Study Area, Geological Setting, and Data.tex:229` Critically, the representative diameter $d_{70}$, which the revised Sellmeijer model \parencite{sellmeijer_2011} requires for the scale factor $F_s$, is not reported anywhere in the dataset.
- [ ] `3. Study Area, Geological Setting, and Data.tex:336` The relative density, the uniformity coefficient and the angularity are fixed at the experimental means of \textcite{sellmeijer_2011}, so the corresponding ratio terms in the resistance factor equal unity.
- [ ] `3. Study Area, Geological Setting, and Data.tex:341` 430~mm \parencite{sellmeijer_2011}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:343` This is consistent with the grain-stability basis of the Sellmeijer formulation, in which the eroding particle is the one that must resist the flow forces while the finer particles around it are carried away \parencite{sellmeijer_2011}, and it is the interpretation adopted here.
- [ ] `4. Methodology.tex:401` The static Sellmeijer rule, in turn, is defined and calibrated on the gross head difference across the structure \parencite{sellmeijer_2011}.
- [ ] `4. Methodology.tex:618` The static branch applies the revised Sellmeijer critical head criterion \parencite{sellmeijer_2011} to the peak of each loading event, exactly as the rule is defined and calibrated: against the raw gross head difference across the structure, with no response-factor attenuation and no crack-resistance reduction, \begin{equation} Z_\mathrm{static} = H_c - \bigl(h_p - z_\mathrm{toe}\bigr), \qquad \t
- [ ] `4. Methodology.tex:628` \label{eq: static limit state} \end{equation} The convention follows from using each model as its author intended: the critical head of \textcite{sellmeijer_2011} is defined and calibrated on the head across the structure.
- [ ] `4. Methodology.tex:652` The term itself is not part of \textcite{sellmeijer_2011}'s own calibration: that rule is fitted throughout on the gross head and carries no crack, blanket or cover head loss in any form.
- [ ] `4. Methodology.tex:690` The relative density, uniformity, and angularity ratios are evaluated at the experimental means of the \textcite{sellmeijer_2011} regression ($D_{r,\mathrm{m}} = 0.
- [ ] `4. Methodology.tex:708` The empirical grain-size adaptation restricts the rule's validity to $d_{70}$ between 150 and 430~$\mu$m \parencite{sellmeijer_2011}, which is the model-applicability argument behind the matrix grain-size interpretation of Chapter~\ref{chap: Study Area, Geological Setting, and Data}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:41` The critical-head formulation reproduces the IJkdijk fine-tuning cases of \textcite{sellmeijer_2011} to within 2 to 15~per cent, the widest being the coarse-sand test the source itself reports as deviating by 25~per cent, where the rule evaluates to 2.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:417` The critical heads computed for the coarse Japanese survivor foundations lie far outside the \textcite{sellmeijer_2011} calibration domain, so only their direction is used.
- [ ] `6. Results - Subsurface Piping Assessment.tex:387` Which end is correct is a question about the applicability of a grain-stability rule calibrated on sand to a gravel-dominated foundation \parencite{sellmeijer_2011}, not a question a Monte Carlo experiment can answer.
- [ ] `6. Results - Subsurface Piping Assessment.tex:1094` 0 both gradation readings lie outside the grain-size range over which the static rule was calibrated \parencite{sellmeijer_2011}.
- [ ] `8. Discussion.tex:43` 3\,D_\mathrm{bl}$ crack-resistance reduction of Equation~\eqref{eq: erosion head}, a term absent from \textcite{sellmeijer_2011}'s own calibration and adopted from Dutch assessment practice rather than derived (Section~\ref{sec: Static Limit State: Sellmeijer Steady-State Benchmark}).
- [ ] `8. Discussion.tex:80` 3\,D_\mathrm{bl}$ is, in any case, a genuine resistance within the transient formulation, the head loss incurred by vertical seepage through the fluidized sediment column above the pipe \parencite{pol_sie_2024}, but the static rule of \textcite{sellmeijer_2011} has no counterpart to it, not because the term is implausible but because it is absent from that rule's own calibration: the reduction ent
- [ ] `8. Discussion.tex:644` 320\textwidth}} \toprule Condition & Established by & Consequence of failing it \\ \midrule A confining blanket over an aquifer connected to the channel and saturated at base flow & Borehole logs showing a low-permeability cover over a transmissive unit in continuity with the channel bed & The instantaneous translation over-predicts the head at the toe; the uplift and heave gate loses its basis \\
- [ ] `appendix-e.tex:264` The bedding angle, the relative density, the uniformity coefficient, and the grain angularity are held deterministic, the latter three being set to their experimental mean values so that their contributions to the Sellmeijer resistance factor reduce to unity, following the conventions of \textcite{sellmeijer_2011} and \textcite{pol_sie_2024}.
- [ ] `appendix-e.tex:339` 498$ are fixed at the experimental means of the multivariate regression of \textcite{sellmeijer_2011}, so that the corresponding ratio terms in $F_r$ equal unity.
- [ ] `appendix-e.tex:414` 430~mm \parencite{sellmeijer_2011}.
- [ ] `appendix-e.tex:418` 4}$, and the coarse-sand behavior that \textcite{sellmeijer_2011} themselves flag as poorly understood, their single coarse-sand validation test deviating by 25 per cent, is precisely the regime a bulk-gravel $d_{70}$ would invoke.
- [ ] `appendix-g.tex:134` The WBI framework evaluates the same composite mechanism, but carries the retrogressive stage into the limit state through the progression-based Sellmeijer rule, which returns the critical head difference above which a fully developed pipe is possible, and combines the three sub-mechanisms by the sequential rule of Section~\ref{subsec: The Sequential STPH Failure Mechanism} \parencite{sellmeijer_1
- [ ] `appendix-g.tex:240` The critical-head kernel is checked against the IJkdijk fine-tuning tests of \textcite{sellmeijer_2011}.

### `fukuoka_2019` (26)

- [ ] `2. Theoretical and Empirical Foundations.tex:183` The dimensionless levee vulnerability index $t^*$ of \textcite{fukuoka_tabata_2018, fukuoka_2019} makes flood duration and levee base width explicit governing variables of a seepage safety measure.
- [ ] `2. Theoretical and Empirical Foundations.tex:187` Under design-scale loading several sections approach or exceed $10^{-2}$, so the survival does not extrapolate to design or climate-intensified conditions \parencite{fukuoka_2019}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:18` 37, exceptionally large among major Japanese rivers \parencite{kimura_2018, fukuoka_2019}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:29` \textcite{fukuoka_2019} attribute the absence of foundation leakage and piping in the gently sloping reach downstream to one specific cause: the peaty soft ground beneath those levees has consolidated under the weight of the large embankment to a final-state permeability of order $10^{-11}$~m~s\textsuperscript{-1} \parencite{fukuoka_2019, hayashi_2008}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:34` Notable floods nonetheless occurred, and the basin's levees have also been repeatedly tested by seismic loading \parencite{fukuoka_2019, oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:48` On the main stem the resulting peak discharge reached approximately 79 per cent of the design high-water discharge at the Moiwa reference section \parencite{fukuoka_2019}.
- [ ] `8. Discussion.tex:505` \textcite{fukuoka_2019} find, through a distinct recession formulation of their index, that the critical instant for embankment seepage failure falls after the hydrograph peak, and the present work finds the same displacement for foundation piping through an entirely different physical route.
- [ ] `8. Discussion.tex:535` The first is the vulnerability index of \textcite{fukuoka_2019}, subject to the mechanism qualification of Section~\ref{sec: The Initiation-Progression Distinction: Implications for Japanese Practice}.
- [ ] `8. Discussion.tex:988` There is nonetheless a defensible version of it, since in a coarse, unconfined gravel deposit the mechanism genuinely is unlikely, and that is why Japanese practice excludes gravel-rich embankments from index assessment altogether \parencite{pwri_4300_2015, fukuoka_2019}.
- [ ] `9. Conclusions and Recommendations.tex:519` } Two independent routes place the critical instant after the hydrograph peak: the vulnerability index of \textcite{fukuoka_2019} for through-embankment seepage, and the present work for foundation piping (Section~\ref{sec: The Initiation-Progression Distinction: Implications for Japanese Practice}).
- [ ] `appendix-d.tex:36` The principal tributaries relevant to the study reach are the Otofuke River entering from the north and the Satsunai River entering from the south-west, both joining the mainstem in the KP~53 to KP~56 reach; the largest tributary, the Toshibetsu River, enters further downstream near KP~29 \parencite{hoshino2023spatiotemporal, fukuoka_2019}.
- [ ] `appendix-d.tex:170` The basin's levees have also been repeatedly tested by seismic loading, with the 1968 and 2003 Tokachi-oki and the 1993 Kushiro-oki earthquakes each causing embankment damage and motivating the progressive cross-section enlargement program of the lower Tokachi \parencite{fukuoka_2019, oyo_1999}.
- [ ] `appendix-d.tex:183` Water levels exceeded the planned high-water level along most of the directly managed reach without overtopping it, and stood roughly 1~m above that level at the lower-reach reference section \parencite{fukuoka_2019}.
- [ ] `appendix-d.tex:196` Along the Satsunai and its Tottabetsu tributary, a levee breach caused approximately 50~ha of inundation \parencite{fukuoka_2019}.
- [ ] `appendix-d.tex:215` At the study segments the loading is referenced to the upstream Obihiro gauge rather than to the downstream Moiwa section \parencite{oyo_1999}, and lies within the directly managed reach that rose above the planned high-water level in 2016 \parencite{fukuoka_2019}.
- [ ] `appendix-d.tex:256` The downstream exceedance of roughly 1~m reported by \textcite{fukuoka_2019} is a separate matter again, applying to the gauge records at Chiyoda and Moiwa, where the observed peaks of 18.
- [ ] `appendix-d.tex:392` \textcite{fukuoka_2019} report two distinct findings for the gently sloping levee reach extending from the river mouth to KP~37.
- [ ] `appendix-d.tex:401` The second, and the one pertinent to the piping mechanism, concerns the foundation: the authors record that neither foundation leakage nor piping damage was observed, and attribute this specifically to the fact that the peaty soft ground beneath those levees has been consolidated by the weight of the large embankment to a final-state permeability of order $10^{-11}$~m~s\textsuperscript{-1} \parenc
- [ ] `appendix-g.tex:141` The central analytical tool of \textcite{fukuoka_2019} is the dimensionless levee vulnerability index $t^*$, a mechanically derived measure of embankment through-seepage, \[ t^* = \frac{5}{2} \frac{k H t'}{\lambda b^2}, \] where $k$ is the spatially averaged hydraulic conductivity of the levee body, $H$ is the applied river head above the floodplain level, $t'$ is the flood duration after the wate
- [ ] `appendix-g.tex:156` 4$ \parencite{fukuoka_2019}.
- [ ] `appendix-g.tex:177` The corresponding second form of the index is \[ t^* = \frac{5}{2} \frac{k H_\mathrm{max} t'}{\lambda b'^2}, \] in which $H_\mathrm{max}$ is the migrating maximum phreatic height and $b'$ the correspondingly shortened horizontal distance to the landside toe, both obtained from the condition that outflow through the riverside face balances the change in stored volume within the embankment \parencit
- [ ] `appendix-g.tex:185` The vulnerability index describes water that has entered the embankment through the riverside face, migrated through the levee body and emerged on the landside slope, and its calibrated thresholds are accordingly stated in terms of landside slope sliding and, at higher values, breach following that sliding \parencite{fukuoka_2019}.
- [ ] `appendix-g.tex:1390` Japanese experimental work finds very low seepage-failure risk in embankment materials with a high gravel content and a coarse grain size \parencite{pwri_4300_2015}, and on that basis both the national screening procedure and the vulnerability-index analysis exclude embankments whose average gravel content is 15~per cent or more from index assessment altogether \parencite{jice_2019, fukuoka_2019}.

### `pol_compgeo_2024` (20)

- [ ] `1. Introduction.tex:35` It integrates the local soil conditions into the time-dependent progression methodology of \textcite{pol_compgeo_2024}, advancing a deterministic time-stepping solution within each stochastic realization.
- [ ] `2. Theoretical and Empirical Foundations.tex:18` However, \textcite{pol_compgeo_2024} caution that the margin shrinks drastically where foundations are highly permeable or the hydraulic overloading $H/H_c$ is severe, which is the combination the Tokachi basin presents.
- [ ] `2. Theoretical and Empirical Foundations.tex:181` Localized detachment of grains temporarily raises flow resistance, halting erosion at the tip until the laminar flow clears the debris \parencite{pol_compgeo_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:238` That asymmetry is the motivation of this thesis, since neither established framework combines a transient load with a progression criterion, and the third row is that combination \parencite{pol_compgeo_2024, pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:359` One model of this class is the upstream source of the rate law below, whose regression form carries those results into samples of the size a tail probability requires \parencite{pol_compgeo_2024} \\ \addlinespace[4pt] Transient progression law \parencite{pol_compgeo_2024, pol_sie_2024} & An instantaneous pipe extension rate $dl/dt$ in the transient head, the aquifer properties and the pipe length,
- [ ] `2. Theoretical and Empirical Foundations.tex:362` One model of this class is the upstream source of the rate law below, whose regression form carries those results into samples of the size a tail probability requires \parencite{pol_compgeo_2024} \\ \addlinespace[4pt] Transient progression law \parencite{pol_compgeo_2024, pol_sie_2024} & An instantaneous pipe extension rate $dl/dt$ in the transient head, the aquifer properties and the pipe length,
- [ ] `2. Theoretical and Empirical Foundations.tex:377` The bridge between dynamic, hydrograph-driven loading and the progression-based probabilistic treatment of piping is the time-dependent framework developed by \textcite{pol_thesis_2022} and formalized in subsequent studies \parencite{pol_compgeo_2024, pol_sie_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:379` To render those coupled three-dimensional mechanisms tractable for reliability analysis, \textcite{pol_compgeo_2024} used the three-dimensional finite element model DgFlow to derive a simplified empirical ordinary differential equation, giving the instantaneous pipe extension rate $dl/dt$ as a continuous function of the transient head, the properties of the aquifer and the geometry of the progress
- [ ] `2. Theoretical and Empirical Foundations.tex:411` Components of transient, probabilistic and progression-based piping assessment exist in isolation, in the transient progression framework \parencite{pol_compgeo_2024}, the pre-calculated surface failure models for the Tokachi basin \parencite{uemura_phd_2025}, and the Bayesian updating mechanisms \parencite{schweckendiek_2014}, but their integration remains largely absent from operational system-s
- [ ] `3. Study Area, Geological Setting, and Data.tex:328` The aquifer conductivity governs both the leakage length and, through the overloading term of the Pol progression ODE, the pipe progression velocity \parencite{pol_compgeo_2024}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:330` 016$ \parencite{pol_compgeo_2024}, whereas fitting the mean post-critical progression rate across the full validation set yields approximately 0.
- [ ] `3. Study Area, Geological Setting, and Data.tex:348` The Sellmeijer scale factor contains the kinematic permeability coefficient, so $k_\mathrm{aq}$ and $d_{70}$ appear together inside the same physics, and the Pol progression ODE likewise carries $k_\mathrm{aq}$ in the pipe-growth velocity \parencite{pol_compgeo_2024}.
- [ ] `4. Methodology.tex:738` The formal treatment replaces this scalar approximation with the time-resolved kinematic limit state of \textcite{pol_compgeo_2024}, \begin{equation} Z_\mathrm{transient} = L - l_e(t_\mathrm{end}), \qquad \text{failure for } Z_\mathrm{transient} \leq 0, \end{equation} where $l_e(t_\mathrm{end})$ is the cumulative eroded pipe length at the end of the hydrograph, obtained by integrating the instanta
- [ ] `4. Methodology.tex:747` The instantaneous progression rate is derived by \textcite{pol_compgeo_2024} from a sediment mass balance coupling laminar pipe flow with grain stability at the pipe tip, and is fitted to three-dimensional DgFlow simulations: \begin{equation} \frac{dl}{dt} = \begin{cases} 89\cdot C_e\cdot\left(k_\mathrm{aq}\cdot \dfrac{H_\mathrm{erosion}(t) - H_\mathrm{eq}(l)}{L}\right)^{0.
- [ ] `4. Methodology.tex:829` The progression ODE is integrated by forward Euler, consistent with \textcite{pol_compgeo_2024} and \textcite{pol_sie_2024}.
- [ ] `4. Methodology.tex:846` The positive-part operator belongs to the sediment mass balance of \textcite{pol_compgeo_2024} and forbids any simulated decrease of the eroded length: partially eroded pipes remain open when the instantaneous head drops below the equilibrium head between sub-peaks.
- [ ] `4. Methodology.tex:940` The second is \emph{dimensional}: the Sellmeijer rule inherits the 2D plane-strain scale exponent $\alpha = -1/3$, while the progression law was calibrated against three-dimensional hole-type-exit simulations whose modelled scale effect is stronger, $\alpha \approx -1/2$ \parencite{pol_compgeo_2024}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:48` The progression integrator is checked against the calibration cases of \textcite{pol_compgeo_2024}.
- [ ] `appendix-e.tex:232` The aquifer conductivity $k_\mathrm{aq}$ governs both the leakage length and, through its appearance inside the overloading term of the Pol progression ODE, the pipe progression velocity \parencite{pol_compgeo_2024}; its mean is taken from the synthesized analysis constant of Table~\ref{tab:form5} rather than from the laboratory tests, for the reasons established in Section~\ref{subsec: Field Perm
- [ ] `appendix-g.tex:265` The progression kernel is checked against the calibration cases of \textcite{pol_compgeo_2024} at three levels of stringency.

### `schweckendiek_2014` (20)

- [ ] `2. Theoretical and Empirical Foundations.tex:268` Retrogression of the pipe across the whole seepage path, $Z_\mathrm{static} = H_c - H_\mathrm{load,peak}$, the peak head being taken net of a resistance proportional to the thickness of the cover layer at the exit \parencite{schweckendiek_2014} & Absent.
- [ ] `2. Theoretical and Empirical Foundations.tex:402` The foundational framework was established by \textcite{schweckendiek_2014, schweckendiek_2016, schweckendiek_2017} and is institutionalized within the Dutch WBI+ methodology \parencite{hkv_2023}, where the updating is implemented in closed form on the fragility curve and conditioned on a survived historical peak water level.
- [ ] `2. Theoretical and Empirical Foundations.tex:406` Documented survival of that kind bounds the plausible space of parameter combinations \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `2. Theoretical and Empirical Foundations.tex:411` Components of transient, probabilistic and progression-based piping assessment exist in isolation, in the transient progression framework \parencite{pol_compgeo_2024}, the pre-calculated surface failure models for the Tokachi basin \parencite{uemura_phd_2025}, and the Bayesian updating mechanisms \parencite{schweckendiek_2014}, but their integration remains largely absent from operational system-s
- [ ] `3. Study Area, Geological Setting, and Data.tex:84` The juxtaposition of a formal deterministic deficiency rating \parencite{oyo_1999} with a documented survival of the most extreme compound flood in the regional record \parencite{tokachi_levee_committee_2017} is precisely the type of informative observation that Bayesian reliability updating exploits \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:88` The present work consequently conditions on the full transient hydrograph through Monte Carlo Accept-Reject filtering, the exact benchmark updating method of \textcite{schweckendiek_2014}, formalized in Section~\ref{sec: Accept-Reject Filtering: Procedure and Posterior Parameter Distributions}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:383` The autocorrelation length is therefore anchored to the literature: \textcite{kanning_2012} infers a horizontal correlation distance of the order of 200 to 300~m for the thickness of a clay layer over sand at a piping-sensitive Dutch delta site, noting that the estimate remains sensitive to the discretization, and \textcite{schweckendiek_2014} assumes 200~m for blanket thickness in his worked pipi
- [ ] `4. Methodology.tex:640` 3\,D_\mathrm{bl}$ of Equation~\eqref{eq: erosion head} \parencite{schweckendiek_2014, pol_sie_2024}.
- [ ] `4. Methodology.tex:655` The reduction enters through Dutch levee-safety assessment practice instead: \textcite{schweckendiek_2014} applies it to the static limit state itself, in the criterion stated for near-future Dutch assessments, and \textcite{pol_sie_2024} adopts the same reduction into the transient erosion head of Equation~\eqref{eq: erosion head} by citing that practice rather than deriving it.
- [ ] `4. Methodology.tex:1192` Phase~2 constrains this uncertainty against the documented survival of the study sections during the August 2016 consecutive typhoons, using the exact benchmark updating method of \textcite{schweckendiek_2014}: Monte Carlo Accept-Reject filtering of the prior realizations against the full transient hydrograph $h_{2016}(t)$.
- [ ] `4. Methodology.tex:1204` The event is selected as the calibration constraint for three reasons: it is the most severe compound hydraulic loading in the modern regional record; the study segments came through it without a breach, and the official post-disaster investigation attributed every breach that did occur in the directly managed system to a mechanism other than seepage \parencite{tokachi_levee_committee_2017}; and t
- [ ] `4. Methodology.tex:1296` The posterior is the prior sample restricted to the accepted set, \begin{equation} \pi_\mathrm{post}(\boldsymbol{\theta}) \propto \pi_\mathrm{prior}(\boldsymbol{\theta})\cdot P\!\left(\mathrm{Survival}\mid\boldsymbol{\theta},\,h_{2016}(t)\right), \end{equation} where the survival likelihood is the binary indicator of the replay \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:111` At $N = 10^5$ it meets the 5~per cent target of standard practice \parencite{schweckendiek_2014} across the bracketed portion of the curve and down to per-level transient failure probabilities of approximately $5\times10^{-3}$, degrading to roughly 16~per cent at $3\times10^{-4}$.
- [ ] `6. Results - Subsurface Piping Assessment.tex:1208` The constraint is the documented survival of the study sections during the August 2016 consecutive typhoons \parencite{tokachi_levee_committee_2017}, applied by Accept-Reject filtering of the prior realizations against the reconstructed transient record at each section \parencite{schweckendiek_2014}.
- [ ] `6. Results - Subsurface Piping Assessment.tex:1424` The strict reading is nevertheless not licensed by the observation, and the benchmark method itself says so: in the field-observation taxonomy of \textcite{schweckendiek_2014}, the evidence that uplift did not occur is an observed absence of seepage, not of sand boils, and seepage without erosion licenses no conclusion at all about the heave limit state, because heave is necessary but not sufficie
- [ ] `8. Discussion.tex:83` 3\,D_\mathrm{bl}$ is, in any case, a genuine resistance within the transient formulation, the head loss incurred by vertical seepage through the fluidized sediment column above the pipe \parencite{pol_sie_2024}, but the static rule of \textcite{sellmeijer_2011} has no counterpart to it, not because the term is implausible but because it is absent from that rule's own calibration: the reduction ent
- [ ] `8. Discussion.tex:237` That is the configuration in which a survival observation is informative, and the configuration the Accept-Reject formulation of \textcite{schweckendiek_2014} is designed to exploit.
- [ ] `8. Discussion.tex:1010` Piping is likewise the dominant contributor to the computed failure probability of Dutch river dikes, which \textcite{schweckendiek_2014} attributes to the size of the uncertainty in ground conditions rather than to the frequency of the mechanism, while the observed record there assigns 1~per cent of an estimated 1{,}735 dike failures between 1134 and 2006 to piping and two thirds to erosion of th
- [ ] `appendix-e.tex:388` 12)$ \parencite{schweckendiek_2014, pol_sie_2024}, which represents the model uncertainty of the revised critical-head rule, fitted to observed against predicted critical heads and centred on unity because that rule is practically unbiased, is carried as an optional, independently drawn multiplier on the single-source critical head, applied identically to the static comparator and to the transient

### `jice_2019` (17)

- [ ] `2. Theoretical and Empirical Foundations.tex:122` The national procedure for designating flood-fighting locations formalizes that pathway as a branching progression diagram \parencite{jice_2019}, and both are reproduced in Appendix~\ref{app subsec: Levee Safety Verification Practice}.
- [ ] `2. Theoretical and Empirical Foundations.tex:179` In compiling the progression pathways used to designate flood-fighting locations across the directly managed river network, \textcite{jice_2019} record that leakage and sand boiling issuing from the embankment have been observed, but that no case has been confirmed in which such deformation progressed as far as crest settlement.
- [ ] `2. Theoretical and Empirical Foundations.tex:183` The operational manual reaches the same conclusion from the opposite direction, noting that the maximum within a flood commonly occurs shortly after peak stage \parencite{jice_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:187` It excludes cross-sections whose embankment gravel content averages 15~per cent or more, since the conductivity-dominated index would otherwise flag gravel-rich embankments as the most hazardous despite the absence of any damage record \parencite{fukuoka_2019, pwri_4300_2015, jice_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:221` Japanese levee safety verification employs advanced transient hydraulic analysis, and applies it reach by reach rather than profile by profile: a continuous levee is subdivided by foundation soil, microtopography and embankment shape, and the cross-section most severe for seepage is verified as representative of each subdivision \parencite{pwri_2014, jice_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:291` Verification against piping and heave is in principle waived where a cohesive blanket of approximately 3~m or more overlies the foundation of a levee no more than 10~m high \parencite{pwri_2014, jice_2019}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:98` It is also the spacing at which the national seepage-screening procedure specifies that cross-section survey data be collected and the levee vulnerability index be evaluated \parencite{jice_2019, pwri_2014}, so the adopted discretization matches the resolution at which the governing data are acquired.
- [ ] `8. Discussion.tex:504` The national screening procedure keeps the two separate on this basis \parencite{jice_2019}.
- [ ] `appendix-d.tex:414` The national procedure for seepage screening specifies that cross-section survey data be collected at intervals of approximately 200~meters and that the levee vulnerability index be evaluated at the distance markers, 200~meter spacing being the standard, while borehole investigations exist at 200 to 400~meter spacing where survey density is high \parencite{jice_2019, pwri_2014}.
- [ ] `appendix-g.tex:33` The national procedure for designating flood-fighting locations formalizes the same pathway as a branching progression diagram, distinguishing the blanket-present route through heave and foundation piping from the no-blanket route directly to foundation sand boiling \parencite{jice_2019}.
- [ ] `appendix-g.tex:49` That section is modeled from three borings in principle, and only sections failing the resulting check attract remedial works \parencite{pwri_2014, jice_2019, mlit_river_management_2009}.
- [ ] `appendix-g.tex:58` An initial-rainfall seepage computation establishes the pre-flood condition; a second computation is then driven by the design stage hydrograph together with the design rainfall; and the phreatic surface that results supplies the pore pressures from which the safety measures are evaluated \parencite{pwri_2014, jice_2019}.
- [ ] `appendix-g.tex:77` Where a blanket is present, the governing measure is instead the heave ratio $G/W$, the weight of the blanket layer divided by the uplift pressure acting on its base, with $G/W \leq 1$ marking the deficient condition \parencite{mlit_teibou_sekkei_2007, pwri_2014, jice_2019}.
- [ ] `appendix-g.tex:101` Where the levee height does not exceed 10~m and a cohesive blanket of approximately 3~m or more overlies the foundation, verification against piping and heave is in principle waived, and the section is excluded from the foundation-leakage screening even where a permeable layer is known to lie beneath the blanket \parencite{pwri_2014, jice_2019}.
- [ ] `appendix-g.tex:161` 01$ as the extraction threshold \parencite{jice_2019}.
- [ ] `appendix-g.tex:190` The national screening procedure keeps the two apart on exactly this basis, applying $t^*$ to embankment leakage while assigning foundation leakage to the heave ratio $G/W$ and the local exit gradient \parencite{jice_2019}.
- [ ] `appendix-g.tex:1390` Japanese experimental work finds very low seepage-failure risk in embankment materials with a high gravel content and a coarse grain size \parencite{pwri_4300_2015}, and on that basis both the national screening procedure and the vulnerability-index analysis exclude embankments whose average gravel content is 15~per cent or more from index assessment altogether \parencite{jice_2019, fukuoka_2019}.

### `fukuda_2025_internal` (14)

- [ ] `1. Introduction.tex:85` A further complexity of the study reach is the structural heterogeneity left by the remediation works of roughly 1999 to 2003, carried out in response to the 1998 safety assessment \parencite{oyo_1999, fukuda_2025_internal}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:25` The current-state classification of the reach as overlying former river course and floodplain deposits \parencite{fukuda_2025_internal} is therefore not incidental; it is the surface expression of exactly the depositional environment that produces uplift- and heave-prone layered foundations.
- [ ] `3. Study Area, Geological Setting, and Data.tex:48` For the Tokachi right-bank segments the documented high-water-level duration is approximately 34~hours over KP~56 to KP~57 and approximately 24~hours from KP~58 onward \parencite{fukuda_2025_internal}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:137` The collective deficiency rating is the documented basis for the formal deficiency classification of the reach \parencite{fukuda_2025_internal}, and it is representative rather than exceptional, on the national inspection figures of Section~\ref{subsec: Japanese Levee Verification Practice: Advanced Hydraulics, Static Failure Criterion}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:141` Following the 1998 rating, a remediation program was implemented along affected sections between 1999 and 2003, comprising side-berm widening and the installation of landside toe drains along the Kita-Obihiro levee on the Tokachi right bank \parencite{fukuda_2025_internal}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:143` No post-remediation geometry or drain-capacity data exist in the secured dataset: the soil data for the post-1999 side-berm fill, its permeability included, are recorded as difficult to obtain, and the post-remediation cross-sections lie outside the OYO dataset \parencite{fukuda_2025_internal}.
- [ ] `appendix-a.tex:175` The depositional origin of this configuration is recorded directly in the flood-control geomorphological classification of the reach, namely former river course and floodplain deposits \parencite{fukuda_2025_internal}: the thin clayey $A_c$ cap is the overbank fines deposited atop the coarse fluvial $A_g$ channel fill.
- [ ] `appendix-d.tex:156` 7 (1980), and the Nakajima Bridge \parencite{fukuda_2025_internal, tokachi_chisuishi_2023}.
- [ ] `appendix-d.tex:439` Supplementary geotechnical data for these reaches are anticipated from the Obihiro Development and Construction Department through the Japanese research partners \parencite{fukuda_2025_internal}, and their arrival is the registered trigger for extending the BEP population.
- [ ] `appendix-d.tex:446` Following the 1998 deficiency rating, a remediation program was implemented along affected sections of the reach between 1999 and 2003 \parencite{fukuda_2025_internal}.
- [ ] `appendix-d.tex:454` Three intervention states are distinguished and allocated to the study sections from the current-state landside cross-section type map \parencite{fukuda_2025_internal}: KP~57.

### `kawajiri_2025` (13)

- [ ] `1. Introduction.tex:20` The August 2016 typhoons produced severe sand boiling and piping along the nearby Tokoro River, confirming that the region's layered foundations are physically vulnerable to seepage-driven erosion \parencite{kawajiri_2025, tokorogawa_2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:28` Field investigations along Hokkaido levees by \textcite{kawajiri_2025} document sand boils ejecting material with grain size characteristics identical to the sandy foundation layer at the blanket-foundation interface, and infer subsurface loosened zones from cone penetration data.
- [ ] `2. Theoretical and Empirical Foundations.tex:170` That prediction is consistent with the distal sand boil locations documented along the Tokoro River during the 2016 extreme events \parencite{kawajiri_2025}.
- [ ] `2. Theoretical and Empirical Foundations.tex:177` The 2016 consecutive typhoons produced severe seepage distress on the Tokoro River levees and none at the Tokachi and Satsunai study segments, which share the identical bipartite stratigraphy \parencite{kawajiri_2025, tokorogawa_2017, tokachi_levee_committee_2017, oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:57` The grain-size composition of the ejected material matched the shallow sandy foundation layer rather than the embankment fill, and that source layer is confined beneath a low-permeability silt-clay cap logged in a nomenclature consistent with the bipartite stratigraphy of the Tokachi study reach \parencite{kawajiri_2025, morita_2018}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:152` The thin clayey $A_c$ cap is the overbank fines deposited atop the coarse fluvial $A_g$ channel fill, the classic uplift- and heave-prone arrangement, mechanistically analogous to the layered stratigraphy that contributed to the severe sand boiling observed along the Tokoro River in 2016 \parencite{kawajiri_2025, tokorogawa_2017}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:178` That prediction is corroborated in the field by the distal sand boil locations documented along the Tokoro River in 2016 \parencite{kawajiri_2025}.
- [ ] `appendix-d.tex:307` In its affected downstream reach the channel is 100 to 200~m narrower than the reaches above and below it as it threads a constricted mountain pass, a geometry that promotes prolonged elevation and retention of the flood stage at the levees \parencite{kawajiri_2025, tokorogawa_2017}.
- [ ] `appendix-d.tex:332` The grain-size composition of the ejected material matches the shallow sandy foundation layer rather than the embankment fill \parencite{kawajiri_2025}, and detailed geotechnical investigation of the boiling reach confirms that this sandy source layer is confined beneath a low-permeability silt-clay surface cap, logged in the regional cohesive, sand and sand-gravel ($A_c$/$A_s$/$A_g$) nomenclature
- [ ] `appendix-d.tex:340` Two distinct boil-occurrence patterns are resolved \parencite{kawajiri_2025, morita_2018}: where the sandy source layer is continuous from the riverside to the landside, the largest boils form directly at the landside toe, the point of easiest pressure release; whereas where a thicker landside silt layer interrupts this path and acts as a dead-end low-permeability barrier, the boils instead emerge
- [ ] `appendix-d.tex:347` In the latter case, test trenching identified no cavity and no sand pipe, while the three-dimensional field of dynamic cone penetration blow counts resolved a network of loosened zones rather than a single continuous channel \parencite{kawajiri_2025}.
- [ ] `appendix-d.tex:368` The surveys also characterized conditions following boil formation and document seepage-driven initiation and partial foundation disturbance rather than a completed retrogressive breach traversing the full seepage length \parencite{kawajiri_2025}, which is the distinction between initiation and through-breach that the time-dependent framework of this thesis is designed to resolve.

### `uemura_wp2_2024` (13)

- [ ] `1. Introduction.tex:26` This is precisely the assessment that \textcite{uemura_wp2_2024} flags as future work, and that this thesis sets out to develop.
- [ ] `1. Introduction.tex:41` \item Formulate a unified multi-mechanism levee risk profile, integrating the calibrated posterior piping probabilities with the overflow and fluvial-scour surface fragilities of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024} through series-system joint-probability equations.
- [ ] `1. Introduction.tex:195` In Phase 3 the calibrated piping fragility is combined with the overflow and fluvial scour mechanisms of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024}, obtained by re-executing the original failure-judgment models on their own per-node inputs (Chapter~\ref{chap: Methodology}).
- [ ] `2. Theoretical and Empirical Foundations.tex:372` The most relevant antecedent for regional probabilistic assessment is the Monte Carlo levee failure evaluation model for the Tokachi and Satsunai Rivers developed by \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:374` To generate a multi-mechanism risk profile without redeveloping the surface-mechanism physics, the overflow and fluvial scour assessments of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024} are incorporated into the Phase~3 integration.
- [ ] `7. Results - System Integration and Climate Sensitivity.tex:24` And the surface mechanisms enter as re-executions of the failure-judgment models of \textcite{uemura_phd_2025} and \textcite{uemura_wp2_2024} on their own per-segment inputs, adapted in the two respects of Section~\ref{sec: Pre-Calculated Surface Failure Fragility Curves from Uemura (2025)} and conditioned on the same canonical loading shape and delivered on the same stage axis as the piping branc
- [ ] `7. Results - System Integration and Climate Sensitivity.tex:448` Aggregating the segments into the nine consequence sections of \textcite{uemura_wp2_2024}, by that study's own within-section maximum applied at a common discharge, takes the result up one level of spatial resolution.
- [ ] `appendix-d.tex:409` The 200~meter evaluation interval adopted from \textcite{uemura_wp2_2024} coincides with Japanese practice for levee assessment.
- [ ] `appendix-d.tex:420` The segments are aggregated into larger sections, numbered 1 to 5 for the Tokachi River and 1 to 4 for the Satsunai River, on the basis of shared inundation characteristics, each section being represented by the segment used to compute its flood consequences \parencite{uemura_wp2_2024}.
- [ ] `appendix-g.tex:1324` 0, within roughly 20~per cent \parencite{uemura_wp2_2024}.
- [ ] `appendix-g.tex:1382` The same view underlies the erosion-dominant headline of the surface-mechanism study whose models are re-executed here \parencite{uemura_wp2_2024}.

### `tokorogawa_2017` (12)

- [ ] `1. Introduction.tex:20` The August 2016 typhoons produced severe sand boiling and piping along the nearby Tokoro River, confirming that the region's layered foundations are physically vulnerable to seepage-driven erosion \parencite{kawajiri_2025, tokorogawa_2017}.
- [ ] `2. Theoretical and Empirical Foundations.tex:177` The 2016 consecutive typhoons produced severe seepage distress on the Tokoro River levees and none at the Tokachi and Satsunai study segments, which share the identical bipartite stratigraphy \parencite{kawajiri_2025, tokorogawa_2017, tokachi_levee_committee_2017, oyo_1999}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:55` At the Futochanae observatory the design high-water level was exceeded for roughly six hours on 18 August and for approximately 32 hours across 20 to 22 August \parencite{tokorogawa_2017, nakatsugawa_2017, morita_2018}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:57` 45 \parencite{tokorogawa_2017}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:152` The thin clayey $A_c$ cap is the overbank fines deposited atop the coarse fluvial $A_g$ channel fill, the classic uplift- and heave-prone arrangement, mechanistically analogous to the layered stratigraphy that contributed to the severe sand boiling observed along the Tokoro River in 2016 \parencite{kawajiri_2025, tokorogawa_2017}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:162` This section confronts the framework with four documented Japanese cases of foundation sand boiling and backward erosion piping that occupy exactly this high-gradient, gravel-dominated setting: the repeated sand ejecta at Gounokawa Shimohara \parencite{Okamura2025_gounokawa}; the boils and levee damage at Gounokawa Shikaga \parencite{Sako2019}; the piping-attributed breach of the Yabe River right
- [ ] `appendix-d.tex:304` The Tokoro River is an entirely separate river system in eastern Hokkaido, draining a catchment of approximately 1{,}930~km\textsuperscript{2} over a trunk stream of some 120~km to the Sea of Okhotsk, passing the city of Kitami, and shares the steep, flashy hydrological character of eastern Hokkaido rivers \parencite{tokorogawa_2017}.
- [ ] `appendix-d.tex:307` In its affected downstream reach the channel is 100 to 200~m narrower than the reaches above and below it as it threads a constricted mountain pass, a geometry that promotes prolonged elevation and retention of the flood stage at the levees \parencite{kawajiri_2025, tokorogawa_2017}.
- [ ] `appendix-d.tex:320` During the August 2016 event the Tokoro levee system sustained extensive seepage-related distress along the KP~16 to KP~27 reach: numerous sand boils and concentrated leakage were recorded, two tributary levees breached, including a 100~m breach of the Shibayamazawa levee, and overflow with associated landside slope failure occurred at several sections, producing inundation of roughly 500~ha \pare
- [ ] `appendix-d.tex:331` 45 \parencite{tokorogawa_2017}.
- [ ] `appendix-g.tex:204` Post-disaster government reviews of the Tokoro, Yabe and Kinu River failures have demonstrated the vulnerability of layered foundation geologies to piping \parencite{Takizawa2018, tokorogawa_2017, yabegawa_2013}.
- [ ] `appendix-g.tex:1043` 1 produced foundation-leakage boils under the August 2016 typhoons without breaching \parencite{tokorogawa_2017}.

### `tokachi_levee_committee_2017` (12)

- [ ] `1. Introduction.tex:20` The Tokachi and Satsunai levees, by contrast, came through the same event without a recorded sand boil \parencite{tokachi_levee_committee_2017}, even though several cross-sections along the Tokachi right bank had already been formally rated as seepage-deficient years earlier \parencite{oyo_1999}.
- [ ] `2. Theoretical and Empirical Foundations.tex:177` The 2016 consecutive typhoons produced severe seepage distress on the Tokoro River levees and none at the Tokachi and Satsunai study segments, which share the identical bipartite stratigraphy \parencite{kawajiri_2025, tokorogawa_2017, tokachi_levee_committee_2017, oyo_1999}.
- [ ] `2. Theoretical and Empirical Foundations.tex:406` Prior deterministic evaluations warned of critical piping instability at the study segments on account of the $A_c/A_g$ stratigraphy \parencite{oyo_1999}, yet those same levees survived the most extreme compound flood event in the modern regional record \parencite{tokachi_levee_committee_2017}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:59` No sand boil or piping event at the study cross-sections appears anywhere in the post-disaster record \parencite{tokachi_levee_committee_2017}, despite the 1998 evaluation having rated every one of the five surveyed cross-sections deficient, three of them naming piping caused by foundation leakage as a cause of instability (Table~\ref{tab:oyo_1998}).
- [ ] `3. Study Area, Geological Setting, and Data.tex:84` The juxtaposition of a formal deterministic deficiency rating \parencite{oyo_1999} with a documented survival of the most extreme compound flood in the regional record \parencite{tokachi_levee_committee_2017} is precisely the type of informative observation that Bayesian reliability updating exploits \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `4. Methodology.tex:1200` The event is selected as the calibration constraint for three reasons: it is the most severe compound hydraulic loading in the modern regional record; the study segments came through it without a breach, and the official post-disaster investigation attributed every breach that did occur in the directly managed system to a mechanism other than seepage \parencite{tokachi_levee_committee_2017}; and t
- [ ] `6. Results - Subsurface Piping Assessment.tex:1206` The constraint is the documented survival of the study sections during the August 2016 consecutive typhoons \parencite{tokachi_levee_committee_2017}, applied by Accept-Reject filtering of the prior realizations against the reconstructed transient record at each section \parencite{schweckendiek_2014}.
- [ ] `8. Discussion.tex:229` The reach then withstood the most extreme compound flood in its record without a recorded sand boil \parencite{tokachi_levee_committee_2017}.
- [ ] `appendix-a.tex:663` Second, the apparent paradox between this deterministic warning and the documented survival of these exact segments during the 2016 event, with no seepage-attributed breach anywhere in the directly managed system and no sand boil recorded at the study segments \parencite{tokachi_levee_committee_2017}, is precisely the empirical constraint that the Bayesian reliability updating of Chapter~\ref{chap
- [ ] `appendix-d.tex:375` The Tokachi River Levee Investigation Committee attributed each to a mechanism other than seepage \parencite{tokachi_chisuishi_2023, tokachi_levee_committee_2017}.
- [ ] `appendix-g.tex:1404` No sand boil was recorded anywhere along the study reaches in that event \parencite{tokachi_levee_committee_2017}.

### `hkv_2023` (11)

- [ ] `2. Theoretical and Empirical Foundations.tex:402` The foundational framework was established by \textcite{schweckendiek_2014, schweckendiek_2016, schweckendiek_2017} and is institutionalized within the Dutch WBI+ methodology \parencite{hkv_2023}, where the updating is implemented in closed form on the fragility curve and conditioned on a survived historical peak water level.
- [ ] `2. Theoretical and Empirical Foundations.tex:406` Documented survival of that kind bounds the plausible space of parameter combinations \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:84` The juxtaposition of a formal deterministic deficiency rating \parencite{oyo_1999} with a documented survival of the most extreme compound flood in the regional record \parencite{tokachi_levee_committee_2017} is precisely the type of informative observation that Bayesian reliability updating exploits \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:88` This updating admits a closed form for the posterior fragility curve which depends on the survived level but not on its exceedance frequency, and which makes the peak-based approximation of standard WBI+ practice provably conservative \parencite{hkv_2023, schweckendiek_2016}.
- [ ] `4. Methodology.tex:1204` The event is selected as the calibration constraint for three reasons: it is the most severe compound hydraulic loading in the modern regional record; the study segments came through it without a breach, and the official post-disaster investigation attributed every breach that did occur in the directly managed system to a mechanism other than seepage \parencite{tokachi_levee_committee_2017}; and t
- [ ] `4. Methodology.tex:1207` Using the full transient record rather than a peak-level scalar is the methodological core: a peak-based survival constraint of the closed-form WBI+ type \parencite{schweckendiek_2016, hkv_2023} cannot represent the load duration that governs progression and would falsely exonerate future long-duration events with sub-2016 peaks.
- [ ] `4. Methodology.tex:1296` The posterior is the prior sample restricted to the accepted set, \begin{equation} \pi_\mathrm{post}(\boldsymbol{\theta}) \propto \pi_\mathrm{prior}(\boldsymbol{\theta})\cdot P\!\left(\mathrm{Survival}\mid\boldsymbol{\theta},\,h_{2016}(t)\right), \end{equation} where the survival likelihood is the binary indicator of the replay \parencite{schweckendiek_2014, hkv_2023}.
- [ ] `6. Results - Subsurface Piping Assessment.tex:1476` The consequence for practice is direct: a peak-based survival update of the kind current probabilistic assessment instruments prescribe \parencite{hkv_2023} would have removed between one and a half and four times as much of the prior as the observation actually licenses, a range that spans the two approved canonical events.
- [ ] `8. Discussion.tex:253` Since that peak-referenced form is what current probabilistic assessment instruments prescribe \parencite{hkv_2023}, the factor measures, in the non-conservative direction, what the time-resolved replay is worth.
- [ ] `appendix-d.tex:283` The posterior fragility curve derived by \textcite{hkv_2023} is the truncated and renormalized prior, \begin{equation} F_{H_c^{*}}(h_c) = \begin{cases} \dfrac{F_{H_c}(h_c) - F_{H_c}(h_\mathrm{obs})}{1 - F_{H_c}(h_\mathrm{obs})}, & h_c \geq h_\mathrm{obs}\\[8pt] 0, & h_c < h_\mathrm{obs} \end{cases} \end{equation} which depends on the survived level $h_\mathrm{obs}$ but not on its exceedance freque
- [ ] `appendix-d.tex:294` The posterior fragility curve derived by \textcite{hkv_2023} is the truncated and renormalized prior, \begin{equation} F_{H_c^{*}}(h_c) = \begin{cases} \dfrac{F_{H_c}(h_c) - F_{H_c}(h_\mathrm{obs})}{1 - F_{H_c}(h_\mathrm{obs})}, & h_c \geq h_\mathrm{obs}\\[8pt] 0, & h_c < h_\mathrm{obs} \end{cases} \end{equation} which depends on the survived level $h_\mathrm{obs}$ but not on its exceedance freque

### `obihiro_levee_inspection_2008` (9)

- [ ] `2. Theoretical and Empirical Foundations.tex:189` The levee did not breach \parencite{obihiro_levee_inspection_2008}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:61` Following the detailed inspection program conducted under the 2002 national design guidance, all reaches containing the cross-sections assessed here were classified as of March 2008 as reaches in which seepage safety is secured \parencite{obihiro_levee_inspection_2008}.
- [ ] `8. Discussion.tex:107` The September 2001 Abashiri flood held the stage above the warning level for 234 continuous hours without breaching \parencite{obihiro_levee_inspection_2008}.
- [ ] `8. Discussion.tex:1107` The computed fragility at the drained sections evaluates the unremediated foundation, while the official inspection maps classify those reaches as seepage-secured as of March 2008, following the works of 1999 to 2003 \parencite{obihiro_levee_inspection_2008}.
- [ ] `appendix-a.tex:596` 7~km, or 19 per cent, was found to fall below the seepage safety standard under design-scale rainfall \parencite{obihiro_levee_inspection_2008}.
- [ ] `appendix-a.tex:603` The published program results deliberately caution against reading them as an evaluation of overall flood safety, since they address only the levee's own resistance at the design water level and many reaches remained deficient in height or width on separate grounds \parencite{obihiro_levee_inspection_2008}.
- [ ] `appendix-d.tex:387` Following the detailed inspection program conducted under the 2002 national design guidance, the Obihiro Development and Construction Department published levee detailed-inspection result information maps classifying each managed reach into three seepage-safety classes: safety insufficient, safety secured, and inspection pending \parencite{obihiro_levee_inspection_2008}.
- [ ] `appendix-g.tex:220` On the Abashiri River at the Sumiyoshi and Hongo districts, the September 2001 flood held the river stage above the warning level for 234 continuous hours, some ten days, creating a recognized risk of breach; leakage from the embankment occurred, an evacuation advisory was issued, and emergency ring-levee works were constructed at seven locations with monitoring at a further ten \parencite{obihiro
- [ ] `appendix-g.tex:225` 5~m drain \parencite{obihiro_levee_inspection_2008}.

### `kimura_2018` (9)

- [ ] `3. Study Area, Geological Setting, and Data.tex:18` 37, exceptionally large among major Japanese rivers \parencite{kimura_2018, fukuoka_2019}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:25` The embankments were first raised in 1937 and enlarged through successive reinforcement campaigns, so the present cross-sections embody a patchwork of gravelly, sandy, and cohesive fills over the relict substrate \parencite{kimura_2018, oyo_1999, fukuda_2025_internal}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:36` Its compound character is measured, not inferred: a counterfactual simulation by \textcite{kimura_2018} that removes the antecedent rainfall reduces downstream water-stage peaks by approximately 4 to 24~per cent across gauging stations.
- [ ] `3. Study Area, Geological Setting, and Data.tex:48` The first three delivered approximately 60 per cent of the total precipitation and exhausted the shallow surface storage of the basin before the most intense rainfall arrived \parencite{kimura_2018}.
- [ ] `appendix-d.tex:17` The Tokachi River drains approximately 9{,}010~km\textsuperscript{2} of southeastern Hokkaido with a mainstem length of around 156~km, discharging to the North Pacific \parencite{kimura_2018}.
- [ ] `appendix-d.tex:37` Runoff from the headwaters reaches the downstream plain with a lag of only several hours \parencite{kimura_2018}, and river planning in the basin adopts a 72-hour rainfall duration because peak discharge generally occurs within that window of the onset of rainfall \parencite{hoshino2023spatiotemporal}.
- [ ] `appendix-d.tex:43` Flood peaks are attenuated by the Tokachi Dam on the upper mainstem and the Satsunai River Dam on the Satsunai tributary; adaptive pre-release operation at the Tokachi Dam demonstrably reduced downstream water-stage peaks during the 2016 event \parencite{kimura_2018}.
- [ ] `appendix-d.tex:175` Typhoon Lionrock followed an unusual eastward track that drove intense orographic rainfall against the eastern slopes of the mountains, delivering more than 500~mm over three days at the heaviest locations \parencite{kimura_2018, furuichi_2018}; at the Karikachi gauge, the maximum 24-hour (352~mm) and 72-hour (507~mm) totals correspond to recurrence intervals of roughly 110 and 109~years respectiv
- [ ] `appendix-d.tex:179` The event caused agricultural damage exceeding 40{,}000~ha and economic losses of around 260~million~USD across Hokkaido \parencite{kimura_2018}, and at the Moiwa reference gauge the reconstructed mainstem discharge reached approximately 10{,}870~m\textsuperscript{3}/s against the design discharge of 13{,}700~m\textsuperscript{3}/s.

### `furuichi_2018` (9)

- [ ] `3. Study Area, Geological Setting, and Data.tex:34` As a sub-boreal region, Hokkaido has historically been less frequently affected by intense typhoons than the main island of Japan, and flood-defense design evolved under that assumption \parencite{furuichi_2018}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:38` The pattern of damage was spatially differentiated in a manner that directly motivates the multi-mechanism scope of this thesis: sediment-related debris flows and bank erosion in the steep headwater catchments, and rapid lateral channel migration in the Otofuke River that produced levee breaches without overtopping, with the water level remaining below the crest throughout \parencite{furuichi_2018
- [ ] `appendix-d.tex:127` Mountain glaciers occupied the Hidaka Range through the last glacial stage, and large volumes of poorly sorted periglacial and fluvial sediment were transported downstream, building extensive alluvial fans and fill-top fluvial terraces across the eastern footslopes and the Tokachi plain \parencite{furuichi_2018}.
- [ ] `appendix-d.tex:163` As a sub-boreal region, Hokkaido has historically been less frequently affected by intense typhoons than the main island of Japan, and flood-defense design evolved under that assumption \parencite{furuichi_2018}.
- [ ] `appendix-d.tex:165` Notable floods nonetheless occurred: a 28-hour rainfall event in August 1981 delivered 331~mm at Kamisatsunai, then among the largest events in the local record \parencite{furuichi_2018}, and a further large flood in September 2011 drove documented morphological change in the Otofuke tributary \parencite{kyuka_2020}.
- [ ] `appendix-d.tex:175` Typhoon Lionrock followed an unusual eastward track that drove intense orographic rainfall against the eastern slopes of the mountains, delivering more than 500~mm over three days at the heaviest locations \parencite{kimura_2018, furuichi_2018}; at the Karikachi gauge, the maximum 24-hour (352~mm) and 72-hour (507~mm) totals correspond to recurrence intervals of roughly 110 and 109~years respectiv
- [ ] `appendix-d.tex:177` Typhoon Lionrock followed an unusual eastward track that drove intense orographic rainfall against the eastern slopes of the mountains, delivering more than 500~mm over three days at the heaviest locations \parencite{kimura_2018, furuichi_2018}; at the Karikachi gauge, the maximum 24-hour (352~mm) and 72-hour (507~mm) totals correspond to recurrence intervals of roughly 110 and 109~years respectiv
- [ ] `appendix-d.tex:187` In the steep granitic headwater catchments of the western basin, the dominant processes were sediment-related: \textcite{furuichi_2018} document disastrous debris flows and bank erosion in weakly cohesive periglacial deposits, with total sediment discharge on the order of $5\times10^{6}$~m\textsuperscript{3} to the downstream reaches.
- [ ] `appendix-e.tex:366` The Tokachi Plain sediments are documented as poorly sorted periglacial and fluvial deposits derived from the Hidaka granitic and volcanic ranges \parencite{furuichi_2018}, and the matrix fines may contain a proportion of pumiceous or vesicular volcanic-glass particles whose effective specific gravity can fall substantially below the quartz-sand reference of approximately 2.

### `uemura_iahs_2024` (8)

- [ ] `1. Introduction.tex:9` These 2016 floods sharpened interest in moving from Japan's deterministic, hazard-based design philosophy toward a probabilistic, risk-based approach to levee safety \parencite{final_report_2022, uemura_iahs_2024}.
- [ ] `1. Introduction.tex:92` The d4PDF event set was processed under an Annual Maximum rainfall framework calibrated for peak discharge and overflow analysis \parencite{uemura_iahs_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:9` Where a binary rule on the HWL does operate it runs the other way: flood-hazard analysis assumes a breach once the river reaches that stage \parencite{mlit_shinsui_manual_2015, uemura_iahs_2024}.
- [ ] `2. Theoretical and Empirical Foundations.tex:293` At the basin scale, system-wide assessment remains dominated by overflow-based judgment, non-overflow mechanisms being treated as secondary \parencite{uemura_iahs_2024, uemura_phd_2025, final_report_2022}.
- [ ] `2. Theoretical and Empirical Foundations.tex:372` It applies Monte Carlo simulation to the major surface failure mechanisms, overflow and fluvial scour, driven by transient hydrographs from the d4PDF ensemble, and generates pre-calculated fragility curves giving conditional failure probability as a function of peak discharge for both overflow \parencite{dean_2010} and scour, on segments spaced at 200 meters and grouped into consequence sections \
- [ ] `4. Methodology.tex:1113` All ingestion of the loading data and all unit handling, including the conversion of discharge to stage through the per-node rating relation $h = \sqrt{Q/a_\mathrm{kp}} - b_\mathrm{kp}$ of the antecedent framework \parencite{uemura_phd_2025, uemura_iahs_2024}, is performed at a single boundary of the framework.
- [ ] `4. Methodology.tex:1407` ~(14) of \textcite{uemura_iahs_2024}, is applied conditional on discharge: the member segments are compared at a common discharge through each segment's own rating relation, because a naive maximum over absolute stages would compare levels on different local datums.
- [ ] `appendix-f.tex:76` The discharge hydrographs are converted to time series of river stage at each evaluation cross-section through a station-specific stage-discharge rating relation of the form $h = \sqrt{Q/a_\mathrm{kp}} - b_\mathrm{kp}$, whose per-kilometer-post coefficients are those carried with the antecedent framework \parencite{uemura_phd_2025, uemura_iahs_2024}.

### `saltelli_primer_2008` (7)

- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:456` This section quantifies that with a variance-based global sensitivity analysis in the framework of \textcite{saltelli_primer_2008}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:472` For a square-integrable model output $Y = f(X_1, \ldots, X_k)$ with mutually independent inputs, the variance admits the unique orthogonal (ANOVA-HDMR) decomposition $V(Y) = \sum_i V_i + \sum_{i<j} V_{ij} + \ldots$ \parencite{sobol_1993, saltelli_primer_2008}, from which \begin{equation} S_i \;=\; \frac{V\!\left[\,\mathbb{E}(Y \mid X_i)\,\right]}{V(Y)}, \qquad S_{Ti} \;=\; \frac{\mathbb{E}\!\left[
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:484` $S_i$ is the main-effect share of the output variance; $S_{Ti}$ adds every interaction term involving $X_i$, so $S_{Ti} \geq S_i$ always, $\sum_i S_i = 1$ characterizes an additive model, and $S_{Ti} \approx 0$ is necessary and sufficient for $X_i$ to be noninfluential \parencite{homma_saltelli_1996, saltelli_primer_2008}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:512` Applying independent-input formulas to correlated samples would instead silently invalidate the decomposition \parencite{saltelli_primer_2008}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:566` Small negative first-order estimates for noninfluential inputs are the expected estimator behavior near zero \parencite{saltelli_primer_2008}.
- [ ] `appendix-g.tex:693` The sample design is the two-matrix scheme of \textcite{saltelli_2002}, as presented by \textcite{saltelli_primer_2008}, in its radial form: base matrices $A$ and $B$ and the $k$ spliced matrices $A_B^{(i)}$, that is $A$ with column $i$ taken from $B$, at a cost of $N(k+2) = 10N$ evaluations per replicate.
- [ ] `appendix-g.tex:715` Every reported index carries two independently constructed 95~per cent confidence intervals: a Student-t interval over the $R = 25$ scramblings, which is the unbiased randomized quasi-Monte-Carlo error statement, and a row bootstrap of the paired design outputs \parencite{archer_1997, saltelli_primer_2008} with 500 resamples pooled across replicates.

### `van_beek_2015` (6)

- [ ] `2. Theoretical and Empirical Foundations.tex:194` The framework needed to interpret this field evidence is provided by \textcite{van_beek_2015}, who classifies piping failure into two behavioral regimes.
- [ ] `2. Theoretical and Empirical Foundations.tex:200` where $T_\text{load}$ is the duration for which hydraulic head exceeds the initiation threshold and $v_\text{progression}$ is a function of hydraulic conductivity $k$ and hydraulic overloading $H/H_c$ \parencite{van_beek_2015, vandenboer_2019}.
- [ ] `2. Theoretical and Empirical Foundations.tex:298` One theoretical tension warrants acknowledgement: the static model predicts that piping resistance decreases as the seepage length $L$ increases, which contrasts with the Shields-Darcy suggestion that scale effects on progression velocity become negligible once the aquifer exceeds a threshold length \parencite{van_beek_2015}.
- [ ] `2. Theoretical and Empirical Foundations.tex:300` A creep ratio delivers a verdict on a fixed geometry at an average gradient across the structure, and carries no rate of pipe growth and no record of how far a pipe has already advanced \parencite{van_beek_2015}.
- [ ] `4. Methodology.tex:736` Progression-Dominated Behavioral Regimes}, that race can be expressed conceptually as failure occurring when the loading duration exceeds the time the pipe needs to traverse the remaining seepage path at a progression velocity increasing with conductivity and hydraulic overload \parencite{van_beek_2015, vandenboer_2019}.
- [ ] `4. Methodology.tex:943` 2$ \parencite{van_beek_2015}, a range that does not reach $-1/2$, so the dimensional component is carried here as a bracket rather than as a determination.

### `morita_2018` (6)

- [ ] `3. Study Area, Geological Setting, and Data.tex:55` At the Futochanae observatory the design high-water level was exceeded for roughly six hours on 18 August and for approximately 32 hours across 20 to 22 August \parencite{tokorogawa_2017, nakatsugawa_2017, morita_2018}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:57` The grain-size composition of the ejected material matched the shallow sandy foundation layer rather than the embankment fill, and that source layer is confined beneath a low-permeability silt-clay cap logged in a nomenclature consistent with the bipartite stratigraphy of the Tokachi study reach \parencite{kawajiri_2025, morita_2018}.
- [ ] `appendix-d.tex:310` The loading there was both severe and sustained: at the Futochanae observatory the river stage exceeded the design high-water level on multiple occasions across the compound sequence and, during the most intense peak, remained continuously above that level for a period on the order of tens of hours \parencite{morita_2018}.
- [ ] `appendix-d.tex:322` The boils were concentrated within an approximately 4~km span of the affected reach, and no leakage or sand boiling had been recorded at these locations during previous floods \parencite{morita_2018}.
- [ ] `appendix-d.tex:336` The grain-size composition of the ejected material matches the shallow sandy foundation layer rather than the embankment fill \parencite{kawajiri_2025}, and detailed geotechnical investigation of the boiling reach confirms that this sandy source layer is confined beneath a low-permeability silt-clay surface cap, logged in the regional cohesive, sand and sand-gravel ($A_c$/$A_s$/$A_g$) nomenclature
- [ ] `appendix-d.tex:340` Two distinct boil-occurrence patterns are resolved \parencite{kawajiri_2025, morita_2018}: where the sandy source layer is continuous from the riverside to the landside, the largest boils form directly at the landside toe, the point of easiest pressure release; whereas where a thicker landside silt layer interrupts this path and acts as a dead-end low-permeability barrier, the boils instead emerge

### `mizuta_2017` (5)

- [ ] `1. Introduction.tex:11` A Japanese-Dutch research collaboration builds on that complementarity \parencite{final_report_2022}, combining Japan's large-ensemble climate projections, most notably the d4PDF dataset \parencite{mizuta_2017}, with Dutch probabilistic levee-safety methods to support forward-looking flood-risk assessment under a changing climate.
- [ ] `2. Theoretical and Empirical Foundations.tex:11` Japan contributes a complementary strength in large-ensemble climate projection, most notably the d4PDF dataset \parencite{mizuta_2017}, which supports statistical characterization of extreme weather events and their transient hydrological responses \parencite{yamada_iahr_2020}.
- [ ] `2. Theoretical and Empirical Foundations.tex:207` Projections of future flood risk in the Tokachi basin are grounded in the d4PDF large-ensemble climate dataset \parencite{mizuta_2017}, dynamically downscaled for Hokkaido through a 5-km regional climate model \parencite{uemura_phd_2025, uemura_iahr_2020}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:366` The ensemble is dynamically downscaled to a 5~km regional model over the basin and converted to discharge through a distributed tank-model runoff chain whose storage parameters are set as a function of the 72-hour basin-averaged rainfall, fitted across five historical floods, so that the many small members of the ensemble are not routed with parameters optimized to a large one \parencite{mizuta_20
- [ ] `appendix-f.tex:17` The d4PDF database provides a very large ensemble of climate simulations produced by a 20~km regional atmospheric model, hereafter RCM20 \parencite{mizuta_2017}.

### `kanning_2012` (5)

- [ ] `1. Introduction.tex:83` Because piping is a weakest-link mechanism, the per-cross-section conditional failure probabilities are related to the 200-meter segment level through the spatial autocorrelation length of the governing foundation parameters \parencite{hoffmans_2014, kanning_2012}.
- [ ] `2. Theoretical and Empirical Foundations.tex:202` Piping is a weakest-link mechanism: the probability of encountering a locally critical condition increases monotonically with the length of the levee segment, so evaluating a single representative cross-section tends to underestimate the failure probability of a finite-length segment \parencite{kanning_2012}.
- [ ] `3. Study Area, Geological Setting, and Data.tex:381` The resulting spatial scale effect is accounted for by relating per-cross-section conditional failure probabilities to the 200-meter segment level through the effective number of independent cross-sections $n_\mathrm{eff} = \max(1,\, L_\mathrm{seg}/\lambda_\mathrm{ac})$, where $\lambda_\mathrm{ac}$ is the spatial autocorrelation length of the governing foundation parameters \parencite{hoffmans_201
- [ ] `3. Study Area, Geological Setting, and Data.tex:383` The autocorrelation length is therefore anchored to the literature: \textcite{kanning_2012} infers a horizontal correlation distance of the order of 200 to 300~m for the thickness of a clay layer over sand at a piping-sensitive Dutch delta site, noting that the estimate remains sensitive to the discretization, and \textcite{schweckendiek_2014} assumes 200~m for blanket thickness in his worked pipi
- [ ] `appendix-e.tex:155` The literature anchor adopted in its absence, $\lambda_\mathrm{ac} = 250$~m from the 200 to 300~m correlation distance reported for blanket thickness in comparable alluvial levee foundations \parencite{kanning_2012}, is corroborated in its order of magnitude by the along-levee picks above: the station-to-station variation in the picked footprint at KP~58.

### `TAW2004` (5)

- [ ] `4. Methodology.tex:417` The hydraulic translation computes, per realization, the fraction of the external river head difference transmitted to the aquifer base at the landside toe, following the leaky-aquifer blanket-theory schematization of \textcite{USACE2000} and \textcite{TAW2004}, which in the no-riverside-blanket special case reduces to the leakage-length formulation of \textcite[Eq.
- [ ] `4. Methodology.tex:438` Because a finite foreshore of width $B_f$ does not behave as a semi-infinite blanket, the entry length is corrected through the hyperbolic-tangent relation of the Dutch design guidance \parencite{TRZmw1999, TAW2004}, \begin{equation} \lambda_\mathrm{out,eff} = \lambda_\mathrm{out}\cdot \tanh\!\left(\frac{B_f}{\lambda_\mathrm{out}}\right), \end{equation} which recovers the semi-infinite value for w
- [ ] `4. Methodology.tex:453` The response factor is then \begin{equation} r_e = \frac{\lambda_\mathrm{in}} {\lambda_\mathrm{out,eff} + L + \lambda_\mathrm{in}}, \label{eq: response factor} \end{equation} which is the exact closed-form solution of the blanket-theory configuration with a riverside blanket, an under-levee aquifer path, and a semi-infinite hinterland blanket \parencite{USACE2000, TAW2004}.
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:55` The response factor is checked against a closed-form Mazure configuration to machine precision, and the finite-foreshore correction against the Dutch design-guidance formulation \parencite{TAW2004, TRZmw1999}.
- [ ] `appendix-g.tex:283` The hydraulic translation is checked against a closed-form Mazure configuration to machine precision, the finite-foreshore correction against the Dutch design-guidance formulation \parencite{TAW2004, TRZmw1999}, and the dormant lag formulation against its two limits, reproducing the instantaneous translation as the aquifer time constant vanishes and remaining stable for arbitrarily large timesteps

### `dean_2010` (4)

- [ ] `2. Theoretical and Empirical Foundations.tex:372` It applies Monte Carlo simulation to the major surface failure mechanisms, overflow and fluvial scour, driven by transient hydrographs from the d4PDF ensemble, and generates pre-calculated fragility curves giving conditional failure probability as a function of peak discharge for both overflow \parencite{dean_2010} and scour, on segments spaced at 200 meters and grouped into consequence sections \
- [ ] `3. Study Area, Geological Setting, and Data.tex:374` The overflow model applies cumulative damage theory through the work index of \textcite{dean_2010}, which accumulates the product of erosive work above a threshold and time, the basis that source found to agree best with its steady-flow erosion data, while the scour model uses a time-integrated bed shear stress exceedance formulation following USACE practice.
- [ ] `3. Study Area, Geological Setting, and Data.tex:376` First, the scour model's erodibility coefficient represents a bed-erosion rate per unit shear stress and is applied here in dimensionally consistent SI units, following \textcite{dean_2010} and USACE practice, whereas the received implementation applies a unit conversion approximately 105.
- [ ] `4. Methodology.tex:1390` The overflow and fluvial scour curves are produced by re-executing Uemura's own failure-judgment models on his own consolidated per-segment inputs: the overflow model applies cumulative damage theory to the time-integrated overtopping flow velocity \parencite{dean_2010, uemura_phd_2025} and the scour model a time-integrated excess bed shear formulation following USACE practice, both as established

### `TRZmw1999` (3)

- [ ] `4. Methodology.tex:438` Because a finite foreshore of width $B_f$ does not behave as a semi-infinite blanket, the entry length is corrected through the hyperbolic-tangent relation of the Dutch design guidance \parencite{TRZmw1999, TAW2004}, \begin{equation} \lambda_\mathrm{out,eff} = \lambda_\mathrm{out}\cdot \tanh\!\left(\frac{B_f}{\lambda_\mathrm{out}}\right), \end{equation} which recovers the semi-infinite value for w
- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:55` The response factor is checked against a closed-form Mazure configuration to machine precision, and the finite-foreshore correction against the Dutch design-guidance formulation \parencite{TAW2004, TRZmw1999}.
- [ ] `appendix-g.tex:283` The hydraulic translation is checked against a closed-form Mazure configuration to machine precision, the finite-foreshore correction against the Dutch design-guidance formulation \parencite{TAW2004, TRZmw1999}, and the dormant lag formulation against its two limits, reproducing the instantaneous translation as the aquifer time constant vanishes and remaining stable for arbitrarily large timesteps

### `lane_1935` (2)

- [ ] `2. Theoretical and Empirical Foundations.tex:300` The empirical tradition is the creep ratio, relating a permissible head difference linearly to the length of the seepage path through a coefficient read off surveyed structures: the percolation factor of \textcite{bligh_1910}, and the weighted form of \textcite{lane_1935}, which credits vertical path segments more heavily than horizontal ones on the evidence of more than two hundred surveyed dams.
- [ ] `2. Theoretical and Empirical Foundations.tex:324` 430\textwidth}} \toprule Formulation & What it returns & Standing in this study \\ \midrule Empirical creep ratio \parencite{bligh_1910, lane_1935} & A permissible head for a given seepage length, through a coefficient fitted to surveyed structures & Set aside.

### `vanbaars_2009` (2)

- [ ] `8. Discussion.tex:1014` Piping is likewise the dominant contributor to the computed failure probability of Dutch river dikes, which \textcite{schweckendiek_2014} attributes to the size of the uncertainty in ground conditions rather than to the frequency of the mechanism, while the observed record there assigns 1~per cent of an estimated 1{,}735 dike failures between 1134 and 2006 to piping and two thirds to erosion of th
- [ ] `8. Discussion.tex:1030` Attribution runs against a mechanism whose surface expression is a sand crater and whose collapse is recorded as a slope or crest failure \parencite{vanbaars_2009}, and a failure record is a record of competing risks: a levee low enough to overflow does so before its foundation has time to matter.

### `mlit_2020_breach` (2)

- [ ] `8. Discussion.tex:1017` Overflow caused 86~per cent of the 140 levee breaches recorded during the 2019 Typhoon Hagibis event and seepage 1~per cent \parencite{mlit_2020_breach}, while the national detailed inspection attributes a deficiency involving piping to 25.
- [ ] `appendix-g.tex:125` That convention is deliberately conservative, and the field record is well to its safe side: of the 70 nationally managed sites at which overtopping was confirmed in 2019, 58, or 83~per cent, did not breach \parencite{mlit_2020_breach}.

### `mara_tarantola_2012` (2)

- [ ] `appendix-g.tex:829` In that construction the anchored variable's index is its full contribution, including the correlated share, and the other pair member's index is its independent contribution, which recovers the dependent-input indices of \textcite{mara_tarantola_2012} and \textcite{kucherenko_2012} exactly for a Gaussian copula while reusing the independent-input estimator stack unchanged.
- [ ] `appendix-g.tex:847` A full index smaller than the corresponding independent index is a signature of dependent inputs \parencite{mara_tarantola_2012, kucherenko_2012} and would be uninterpretable, or silently wrong, if independent-input formulas were applied to correlated physical samples.

### `kucherenko_2012` (2)

- [ ] `appendix-g.tex:829` In that construction the anchored variable's index is its full contribution, including the correlated share, and the other pair member's index is its independent contribution, which recovers the dependent-input indices of \textcite{mara_tarantola_2012} and \textcite{kucherenko_2012} exactly for a Gaussian copula while reusing the independent-input estimator stack unchanged.
- [ ] `appendix-g.tex:847` A full index smaller than the corresponding independent index is a signature of dependent inputs \parencite{mara_tarantola_2012, kucherenko_2012} and would be uninterpretable, or silently wrong, if independent-input formulas were applied to correlated physical samples.

### `sobol_1993` (1)

- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:472` For a square-integrable model output $Y = f(X_1, \ldots, X_k)$ with mutually independent inputs, the variance admits the unique orthogonal (ANOVA-HDMR) decomposition $V(Y) = \sum_i V_i + \sum_{i<j} V_{ij} + \ldots$ \parencite{sobol_1993, saltelli_primer_2008}, from which \begin{equation} S_i \;=\; \frac{V\!\left[\,\mathbb{E}(Y \mid X_i)\,\right]}{V(Y)}, \qquad S_{Ti} \;=\; \frac{\mathbb{E}\!\left[

### `homma_saltelli_1996` (1)

- [ ] `5. Verification, Validation, and Global Sensitivity Analysis.tex:484` $S_i$ is the main-effect share of the output variance; $S_{Ti}$ adds every interaction term involving $X_i$, so $S_{Ti} \geq S_i$ always, $\sum_i S_i = 1$ characterizes an additive model, and $S_{Ti} \approx 0$ is necessary and sufficient for $X_i$ to be noninfluential \parencite{homma_saltelli_1996, saltelli_primer_2008}.

### `saltelli_2002` (1)

- [ ] `appendix-g.tex:692` The sample design is the two-matrix scheme of \textcite{saltelli_2002}, as presented by \textcite{saltelli_primer_2008}, in its radial form: base matrices $A$ and $B$ and the $k$ spliced matrices $A_B^{(i)}$, that is $A$ with column $i$ taken from $B$, at a cost of $N(k+2) = 10N$ evaluations per replicate.

### `owen_1997` (1)

- [ ] `appendix-g.tex:697` The matrices are drawn from an Owen-scrambled Sobol' low-discrepancy sequence in $2k$ dimensions \parencite{owen_1997}.

### `saltelli_2010` (1)

- [ ] `appendix-g.tex:698` The estimators are those of \textcite{saltelli_2010}, \begin{equation} \widehat{S}_i = \frac{\frac{1}{N}\sum_{j=1}^{N} y_B^{(j)}\left(y_{A_B^{(i)}}^{(j)} - y_A^{(j)}\right)}{\widehat{V}}, \qquad \widehat{S}_{Ti} = \frac{\frac{1}{2N}\sum_{j=1}^{N} \left(y_A^{(j)} - y_{A_B^{(i)}}^{(j)}\right)^2}{\widehat{V}}, \label{eq:estimators} \end{equation} the total-effect form being Jansen's \parencite{jansen

### `jansen_1999` (1)

- [ ] `appendix-g.tex:707` The estimators are those of \textcite{saltelli_2010}, \begin{equation} \widehat{S}_i = \frac{\frac{1}{N}\sum_{j=1}^{N} y_B^{(j)}\left(y_{A_B^{(i)}}^{(j)} - y_A^{(j)}\right)}{\widehat{V}}, \qquad \widehat{S}_{Ti} = \frac{\frac{1}{2N}\sum_{j=1}^{N} \left(y_A^{(j)} - y_{A_B^{(i)}}^{(j)}\right)^2}{\widehat{V}}, \label{eq:estimators} \end{equation} the total-effect form being Jansen's \parencite{jansen

### `archer_1997` (1)

- [ ] `appendix-g.tex:715` Every reported index carries two independently constructed 95~per cent confidence intervals: a Student-t interval over the $R = 25$ scramblings, which is the unbiased randomized quasi-Monte-Carlo error statement, and a row bootstrap of the paired design outputs \parencite{archer_1997, saltelli_primer_2008} with 500 resamples pooled across replicates.
