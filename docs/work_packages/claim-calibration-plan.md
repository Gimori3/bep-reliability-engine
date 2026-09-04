# Claim-calibration audit and fix plan

Date: 2026-08-29. Status: audit complete, **no file edited in this session**.
Scope: the whole of `d:\repositories\msc-thesis` (Summary, Chapters 1 to 9,
Appendices A to H), audited for claims that are miscalibrated relative to the
evidence behind them, in **both** directions (too strong and too weak).

Evidence consulted: `d:\repositories\bep-reliability-engine` (`docs/`,
`docs/decisions/`, persisted result artifacts) and the reference PDFs in
`docs/references/`.

---

## 0. How this audit relates to the passes that came before it

Three campaigns already went through this text, and this audit deliberately does
not re-open what they settled:

| Pass | Date | What it covered |
|---|---|---|
| Thesis number reconciliation | 2026-08-21 | 431 claim groups traced to artifacts; 3 fixes landed; 2 items left open |
| Japanese levee failure criterion correction | 2026-08-28 | Summary, Ch1, Ch2, Ch3, App G reframed against primary MLIT/PWRI sources |
| RQ1 beta re-expression + equal-head convention + terminology/evidence audit | 2026-08-28/29 | Delta-beta metric introduced; "validation" renamed "field evaluation"; unbiasedness withdrawn in five places |
| Reviewer feedback triage (Hokkaido professor) | 2026-08-29 | MC1 to MC7 and the minors, executed in `msc-thesis` commits `2d40fb4`..`829364c` |

**Two coverage gaps that this audit exploits.** First, the 2026-08-21
reconciliation explicitly did not verify the 58 `CITED` literature values
against their sources ("that is the provenance documents' job"). Second, it
predates the RQ1 campaign by a week, so every reliability-index number, the
additive ladder table, and the equal-head-convention table entered the thesis
**after** the last reconciliation and have never been traced to an artifact by
an independent pass. Findings D and G below live in those two gaps.

---

## 1. Findings log

38 findings. `TS` = too strong, `TW` = too weak, `IC` = internally inconsistent
or factually wrong, `PROV` = provenance/attribution.

### Category A. Internal numeric and factual inconsistencies

| # | Location | Claim (quoted or close paraphrase) | Class | Why it is miscalibrated | Evidence that resolves it |
|---|---|---|---|---|---|
| A1 | `frontmatter/summary.tex:4` | "Remedial works were installed at three of the rated sections before the flood, **though not at the one with the worst exit gradient**" | IC / TS | The thesis's own `tab:oyo_1998` gives KP 58.8 a vertical exit gradient of **1.300**, the worst of the five, and KP 58.8 **was** fitted with toe drains. The unremediated section is KP 62.0, at 0.970 vertical (though it does carry the highest *horizontal* gradient, 0.660). As written the sentence is false on the measure the thesis tabulates as the headline gradient. | Thesis wording only, against `tab:oyo_1998` and `tab: section inputs` |
| A2 | `mainmatter/4. Methodology.tex:1225` | Obihiro gauge peak of 38.07 m T.P. "sits **0.07 m** below the gauge's design high-water level" | IC | Ch 3 (`:50`), Appendix D (`:238`) and Appendix F (`:81`) all say **0.19 m**, below a design level of 38.26 m. Ch 4 is the lone outlier. (0.07 m corresponds to the 38.14 m revision at a different chainage; the engine's KP 56.6 value.) | Thesis wording, plus `docs/tokachi_chisuishi_full_review_2026-07-27.md` on the 38.14 / 38.26 / 38.44 / 38.56 set |
| A3 | `mainmatter/1. Introduction.tex:202` | "nine chapters ... followed by **seven appendices**" and "The seven appendices hold the supporting material" | IC | `report.tex` inputs eight: A to H. Appendix H (The Reach-Wide Surface Composition) was added by the scope-narrowing campaign and the count was not updated. The Chapter 1 roadmap figure (`fig: thesis roadmap`) likewise names only A to G. | Thesis wording only, against `report.tex` |
| A4 | `mainmatter/6. ...tex:382-384` vs `:164`, `:731`, `:780`, and `mainmatter/7. ...tex:232`, `:814` | "the top of the attainable range at **50.5 m**" against "The largest stage any member of either ensemble reaches at this section is **51.47 m**, so every extension level **from 51.5 m upward** describes a loading the section cannot experience" | IC | Two incompatible definitions of "attainable" coexist. If 50.5 m is the top of the attainable range, then 51.0 m is *not* attainable, and Ch 6:384 says the opposite. Ch 7 compounds it: 7 warming years peak *above* 50.5 m, which under the 50.5 m definition are unattainable loadings carrying 11.8 per cent of a reported annual number. | Engine: `attainable_max_m` in the KP 62.0 config/metadata, and the ensemble peak-stage distribution at that node |
| A5 | `mainmatter/8. Discussion.tex:1004` | "Overflow caused 86 per cent of the **140** levee breaches recorded during the 2019 Typhoon Hagibis event and seepage 1 per cent" | IC | The engine's verbatim reading of the source (MLIT 2020, 3rd committee meeting, Document 2) gives **142** breaches: overtopping 122 (86 per cent), erosion 12, seepage 2, unknown 6. 122/142 = 86 per cent; 122/140 = 87 per cent. The denominator and the percentage are not mutually consistent as printed. | `docs/japanese_levee_failure_criterion_review_2026-08-28.md` section J6 |
| A6 | `mainmatter/3. ...tex:131` and `mainmatter/4. ...tex:480` | "the correction is **saturated at every production section**: the realized tanh credits are 0.969, 0.995, 1.000 and **0.835**" / "the tanh correction is saturated at every production section, so r_e is insensitive to foreshore width" | TS / IC | A credit of 0.835 is not saturation, and the sentence contradicts its own list two clauses later. The substantive point survives (the KP 62.0 narrow foreshore raises r_e by only about 6 per cent against an infinitely wide one, and the open-entry bound is a 39 per cent r_e increase worth at most 2.4e-4 in P_f), but "saturated at every production section" overstates it. | `docs/decisions/adr0025-foreshore-sensitivity.json` (credits 0.9686 / 0.9946 / 1.0000 / 0.8350; B_f=300 m arm gives r_e ratio 1.055) |
| A7 | `mainmatter/5. ...tex:760` | "a revised prior re-weights the decomposition **without re-ordering it**, as the companions above show" | TS / IC | The bulk-gradation companion in the same subsection re-orders the third and fourth inputs: d70 rises to S_T = 0.40 while C_e falls to 0.16, reversing their matrix ordering (C_e 0.34 > d70 0.28). Only the *leading pair* is unchanged, which is what the companion paragraph actually says. | Thesis wording, against its own preceding paragraph and `docs/decisions/adr0033-gsa-study.md` |
| A8 | `mainmatter/6. ...tex:19-21` (standing conditions register) | "**nine conditions** govern how every number here is to be read" | TS (understated conditionality) | The register omits the **critical pipe length** bracket, which the same chapter's own synthesis (`:1614`), Ch 8 `subsec: Not Every Epistemic Knob Cancels in a Ratio`, and Ch 9 RQ1 all list as one of the four brackets every ratio in the chapter is conditional on (it displaces the comparison by 1.11 to 1.67 and has zero common-mode channels). | `docs/decisions/0049-critical-pipe-length-override.md`, `adr0049-critical-length-companion.json` |
| A9 | `mainmatter/7. ...tex:~1127`, `mainmatter/9. ...tex:~176`, `appendix/appendix-h.tex:95-105` | "The as-received conversion would change **which surface mechanism leads** at 97 of the 114 segments in the historical climate" | TS | Appendix H's own next sentence says "Most of those 97 are segments that have no failure probability at all under the primary set", so at most of them there is no leading mechanism to change: the change is from "no mechanism loaded" to "scour". The main-body phrasing implies a re-ordering of two live mechanisms. | `appendix/appendix-h.tex` `tab: mechanism coverage`; Phase 3 reach-wide artifact |
| A10 | `mainmatter/6. ...tex` `tab: piping conditions register`, exit-datum row | "A 0.30 m shift **lowers** the KP 62.0 ratio from 26.9 to 13.9" | TS / incomplete | The bracket is two-sided: `z_toe_minus0.30m` gives B = 13.87 and `z_toe_plus0.30m` gives B = 38.00. Only the downward arm is reported, in a register whose whole purpose is to state the direction each condition moves the result. The upward arm is below the R1 resolution floor (2 transient rows), which is a legitimate reason to prefer the resolved arm but should be said. | `results/hwl_bias_resolution/stage_d_epistemic.json` |
| A11 | `mainmatter/3. ...tex:20` | "Because that agreement holds at independent chainages and under independent freeboard constants, it **establishes**, and does not merely assume, that Tokyo Peil and the meters-above-mean-sea-level datum of the engine **coincide** at this reach" | TS (precision) | Tokyo Peil *is* the Japanese mean-sea-level datum by definition, so "the two datums coincide" is not the proposition the freeboard agreement tests. What the agreement establishes is that the **engine's ingested elevations** are on the official datum rather than on an offset one. The evidence is good; the proposition it is attached to is the wrong one. | Thesis wording only, against `docs/tokachi_chisuishi_full_review_2026-07-27.md` (T.P. identity verified) |

### Category B. The reliability-index ordering claim (one overreach, five sites)

| # | Location | Claim | Class | Why it is miscalibrated | Evidence |
|---|---|---|---|---|---|
| B1 | `frontmatter/summary.tex:8`; `mainmatter/6. ...tex:670-673` and `:1608-1610`; `mainmatter/8. Discussion.tex:34` and `:580`, `:1015`; `mainmatter/9. ...tex:53-55` | "in reliability-index terms ... **the ordering reverses**, the drained sections carrying the larger index shift despite the smaller ratio" | TS | It does not reverse, and the drained sections do not both carry the larger shift. Measured design-level Delta-beta: KP 60.0 **1.87**, KP 57.4 **at least 1.27** (point estimate **1.56**), KP 58.8 **1.22**, KP 62.0 **0.90**. In B the order is KP 57.4 > KP 62.0 > KP 60.0 > KP 58.8; in Delta-beta it is KP 60.0 > KP 57.4 > KP 58.8 > KP 62.0. KP 57.4 (berm-only) is second in both, and it outranks the drained KP 58.8 in the index. What actually happens is that **KP 62.0 falls from second to last while KP 60.0 rises from third to first**: a re-ordering, not a reversal, and not one the drained/undrained split explains. | `docs/rq1_beta_reexpression_2026-08-28.md` section 2 (design-level anchor table) and section 4 (`tab: gap components beta` source rows: KP 57.4 at 39.21 m, Delta-beta 1.56) |
| B2 | `mainmatter/8. Discussion.tex:580` and `:1015`; `mainmatter/9. ...tex:492` | "the same four sections span only **0.9 to at least 1.9**" | TS | The "at least" is a mis-transfer from probability space. In B the top of the range **is** the bound (KP 57.4, at least 148). In Delta-beta the top of the range is KP 60.0's **resolved 1.87**, and the bound (KP 57.4, at least 1.27) sits in the *middle*. "0.9 to at least 1.9" asserts an open-ended upper end that the measurement closes. The Summary and Ch 6 get this right ("0.9 to 1.9"); three sites do not. | Same source as B1 |

### Category C. The equal-head-convention retained fraction

| # | Location | Claim | Class | Why it is miscalibrated | Evidence |
|---|---|---|---|---|---|
| C1 | `frontmatter/summary.tex:8`; `mainmatter/6. ...tex:~995` and `:1622`; `mainmatter/8. Discussion.tex:45`; `mainmatter/9. ...tex:68` | "the equal-convention comparison **retains 54 to 83 per cent** of the as-published Delta-beta" (54 per cent being KP 57.4) | TS / not reproducible | The 54 per cent is `0.842 / 1.558`, where 1.558 is the KP 57.4 design-level Delta-beta **point estimate resting on two failing transient realizations in 1e6**, below the thesis's own pre-registered resolution floor of 30. The table printed directly above the sentence (`tab: equal convention`) shows the *bound*, "at least 1.27" and "at least 148", from which a reader computes 66 per cent, not 54. So the low end of the headline range is (a) not reproducible from the thesis's own table and (b) derived from a quantity the thesis elsewhere refuses to quote as a point estimate ("The point estimate that a resampling of two realizations would produce is not reported"). | `docs/decisions/equal-head-convention-study.md` section 4.2 (which uses B = 566 and Delta-beta = 1.558 for KP 57.4) against `mainmatter/6.` `tab: equal convention` |
| C2 | `frontmatter/summary.tex:8` | "no single such convention is unique; **two readings agree within about a quarter**" | TS | True at KP 62.0 only (7.34 against 8.03, 10 to 24 per cent). At KP 57.4 the two readings split **23.1 against 12.0**, roughly a factor of two, which is why Ch 6 instructs "quote KP 62.0 as 7 to 8, KP 57.4 as about 5 to 23". The Summary compresses a two-section result into the friendlier of its two halves. | `docs/decisions/equal-head-convention-study.md` section 4.3; `mainmatter/6. ...tex:~999` |

### Category D. Literature-anchored claims (never verified against sources)

| # | Location | Claim | Class | Why it is miscalibrated | Evidence |
|---|---|---|---|---|---|
| D1 | `mainmatter/2. ...tex:19` | "short-duration hydraulic loads such as coastal storm surges **reduce the failure probability by a factor of 10 to 10^6** relative to steady-state assumptions" | IC / TS | The source abstract reads "Reductions vary widely, ranging from a factor of **5 to more than 10^6**". Two errors: the lower endpoint (10 against 5) and the dropped "more than". Third, the range in the source spans **both** coastal and river configurations; attributing all of it to coastal surge misstates the source's own structure. | `docs/references/pol_sie_2024.pdf`, abstract and section 3.4 (verified verbatim this session) |
| D2 | `mainmatter/2. ...tex:19` and everywhere the "factor of one to about six" duration result is quoted (Ch 6, Ch 8, Ch 9, Summary) | **Missing corroboration.** Pol SIE 2024 section 3.4 states: "In other situations with river levees (**coarse sand and thin blanket**) effects are limited (F_td < 5) and the current assumption of instantaneous failure can be considered realistic." | TW | That is the Tokachi configuration exactly (coarse A_g aquifer, 0.45 to 0.85 m blanket), and it is an independent, published, pre-existing statement that the time-dependence effect there is small. The thesis's own central duration result, "flood duration alone accounts for a factor of one to about six", is currently presented as a standalone measurement and reads as a deflation of its own premise. It is in fact **corroborated by the source model's author on the same configuration class**, which is a materially stronger position than the text takes. | `docs/references/pol_sie_2024.pdf` section 3.4, p. 12 |
| D3 | `mainmatter/2. ...tex:~187` | "The recovery experiments of Pol (2022) ... found that reloading a partially formed pipe after nine months of rest produced a 20 per cent lower critical head and a 140 per cent higher progression rate, through irreversible damage in the foundation. For closely spaced events ... subsurface erosion **consequently** behaves as a strictly cumulative, irreversible process with r_l = 0" | TS (inference, not number) | The two numbers are **exact** against the source. The inference is not. The same passage says "the erosion process **had to start all over again**" and "there was **partial recovery** over a period of nine months". The experiment therefore evidences *carried damage to the resistance*, and evidences *loss of the pipe geometry*; r_l = 0 carries the **geometry** forward and holds the resistance fixed, which is the opposite pairing. The thesis knows this (Ch 4: "The irreversibility is exclusively geometric"; Ch 5 records the Gounokawa disagreement as memory held in the blanket) but Ch 2's "consequently" does not follow from the cited experiment. The real support is the short inter-peak interval plus the model author's confirmation, not the nine-month test. | `docs/references/pol_thesis_2022.pdf` (chapter abstract and the recovery-test discussion, both verified verbatim this session); `docs/joost_pol_meeting_vragen.md` item 7 |
| D4 | `mainmatter/2. ...tex:~300` | "the weighted form of Lane (1935), which credits vertical path segments more heavily than horizontal ones **on the evidence of 278 cases**" | unverified | The count is not traced to any artifact and Lane (1935) is not in `docs/references/`. Commonly cited figures for that study vary. | Web or library check of Lane, E. W. (1935), *Security from under-seepage: masonry dams on earth foundations* |
| D5 | `mainmatter/2. ...tex:~40` | "previous geotechnical assessments identified critical exit gradients (**i_c >= 0.5**) at the landside toe" | IC (notation) | The same subsection defines `i_c = gamma'_bl / gamma_w` (Terzaghi), which for the study blanket is about 0.70. The 0.5 here is the **Japanese allowable-gradient screening criterion**, a different object with the same symbol. Ch 3 and Appendix G use 0.5 correctly as the national criterion. As printed, Ch 2 asserts a Terzaghi critical gradient of 0.5. | `docs/oyo_1998_framing_review_2026-08-24.md` (the OYO criterion text) and the thesis's own `tab:oyo_1998` caption |
| D6 | `mainmatter/2. ...tex:~186`; `appendix/appendix-g.tex:~1378` | "It excludes cross-sections whose embankment **gravel content averages 15 per cent or more**" / "very low seepage-failure risk where embankment gravel content **exceeds 15 per cent**" | unverified + internally inconsistent | "averages 15 per cent or more" and "exceeds 15 per cent" are different thresholds, and neither is traced to an artifact. Source is `pwri_4300_2015` / `fukuoka_2019`. | `docs/references/2019-suiko-fukuoka.pdf`; PWRI 4300 (2015) if obtainable |
| D7 | `mainmatter/2. ...tex:189`; `mainmatter/8. Discussion.tex:100-101`; `appendix/appendix-g.tex:~217` | "On the Abashiri River the September 2001 flood held the stage above the warning level for **234 continuous hours**, some ten days" | open item | Flagged by the 2026-08-21 reconciliation and still open. It is a `CITED` value from `obihiro_levee_inspection_2008`, unverifiable in the engine, and Chapter 8 uses it as a **quantitative counterweight to a computed result** (the flashiness argument), which is the one place a cited duration does argumentative work against an engine number. | `docs/thesis_number_reconciliation_2026-08-21.md` section 3.2; the source document |
| D8 | `mainmatter/8. Discussion.tex:~1067`; `appendix/appendix-e.tex:~214` | "The adopted coefficient of variation places the **central 95 per cent** of the conductivity prior **within a factor of about 2.9**" | open item | Direct computation from CoV = 0.50 gives 2.52 (P97.5 / median), 6.36 (P97.5 / P2.5) or about 2.6 (tightest mean-relative). **None is 2.9.** Stated twice; the reconciliation left it for an owner ruling. | `docs/thesis_number_reconciliation_2026-08-21.md` section 3.1 |
| D9 | `mainmatter/5. ...tex:40-46`; `appendix/appendix-g.tex:239-250` | "reproduces the IJkdijk fine-tuning cases ... to within 2 to 15 per cent, **the widest being the coarse-sand test the source itself reports as deviating by 25 per cent**: for **the first** IJkdijk test the rule evaluates to 2.07 m against the observed 2.30 m" | TS (reads as a non-sequitur) | The example given immediately after "the widest" is the **first** test (10 per cent), not the coarse-sand **second** test (15 per cent) the clause names. Appendix G has all three right; Ch 5 juxtaposes them in a way that reads as though 2.07 against 2.30 were the 25 per cent case. Also worth re-checking that the 25 per cent figure is genuinely the source's own statement for that test. | `docs/references/sellmeijer_2011.pdf`; `appendix/appendix-g.tex:239-250` |

### Category E. Interpretive calibration

| # | Location | Claim | Class | Why it is miscalibrated | Evidence |
|---|---|---|---|---|---|
| E1 | `mainmatter/8. Discussion.tex:17-18` | "Based on Chapter 6, **the premise is correct**, but its size depends on the metric asked." | TS | The premise, as Chapter 1 states it, is that flashy flood waves recede before seepage erosion can breach, "so that levees on steep Japanese rivers are **protected against backward erosion piping by the hydrology itself**". What Chapter 6 establishes is a weaker proposition: the transient probability is lower than the static one (a theorem, not a finding), by an amount of which **duration alone is a factor of one to about six**, most of the rest being a head-convention difference. And Chapter 7 finds piping governs the annual system risk wherever it can be compared. "The premise is correct" is contradicted by the thesis's own next two paragraphs and by Ch 7. | Thesis-internal: `mainmatter/6.` `tab: gap components` "pure duration" column; `mainmatter/7.` `tab: system annual` |
| E2 | `frontmatter/summary.tex:16` | "Compound clustering is present but **doesn't appear to drive** the increase" | TW | Ch 7, Ch 8 and Ch 9 all state this as a measured null: the compound stratification's historical sampling intervals (0.3 to 9.3 and 0.1 to 18.4) both include one, while the duration split resolves a concentration of about 150 and about 380; and the compound verdict is floor-sensitive where the duration verdict is not. "Is present but is not the channel" is the chapters' own phrasing and is what the measurement supports. The Summary hedges a result the body reports as resolved. | `mainmatter/7. ...tex:~1085`; `mainmatter/8. Discussion.tex:~335`; `mainmatter/9. ...tex:~250` |
| E3 | `mainmatter/6. ...tex:~1330`; `mainmatter/8. Discussion.tex:~207` | "The survival therefore **discredits the absolute level of the static comparator** while remaining comfortably consistent with the transient one" | TS | The 58 and 73 per cent static rejection is computed on the **undrained** foundation, while the survival that supplies the evidence was produced by a **drained** structure. The thesis applies exactly this confound to the posterior tightness two pages earlier ("The posterior is tighter than the observation licenses"), and it applies with equal force here: part of the static comparator's apparent over-rejection is the un-credited drainage, not miscalibration. The verdict may well survive, but it currently carries the caveat in one place and not the other. | Thesis-internal (`mainmatter/6. ...tex:~1240`, the as-if-undrained bias paragraph); `docs/decisions/0050-toe-gradient-relief-drained-bracket.md` |
| E4 | `mainmatter/8. Discussion.tex:~184` | "Nesting means the static criterion **was never wrong in the permissive direction at this loading**." | TW | Three sentences later the same paragraph proves the general result: "Transient failure therefore implies static failure **for every input and every hydrograph**, and no flood of any duration can break the containment." The opening restriction "at this loading" understates a containment the paragraph itself establishes unconditionally. | Thesis-internal, same paragraph; `mainmatter/4. ...tex:~813` |
| E5 | `frontmatter/summary.tex:16` | "annual system failure probability ... rises by factors of 5.5 to 12.7 ... **reaching about one per cent per year**" | TW / imprecise | The largest warming value is **4.1e-2 per year** at KP 58.8, which the same Summary paragraph later gives correctly as "rising from about 0.7 to 4 per cent". Ch 7 says "of order 1e-2 per year". "Reaching about one per cent" understates the top of the range by a factor of four. | `mainmatter/7.` `tab: system annual` |
| E6 | `frontmatter/summary.tex:12` | "the filter cannot reach seepage length, which holds **half to three-quarters** of the transient variance" | TW / imprecise | The measured total-effect share is **0.49 to 0.78**. 0.78 is above three-quarters. Ch 6 and Ch 8 both quote "0.49 to 0.78". | `docs/decisions/adr0033-gsa-study.md`; `mainmatter/6. ...tex:~1540` |
| E7 | `frontmatter/summary.tex:12` | "**The record supplies no second event** to test further." | TS | The chapters say something more precise and better supported: two candidate events were examined for admissibility and closed on **measured** grounds (2011's marginal information bounded at 0.316 per cent of realizations in one stratum of eight; 2006 has no constructible loading). "Supplies no second event" reads as an absence of data rather than a measured closure, and gives away the strength of ADR-0044. | `docs/decisions/0044-event-set-closure-2016-only.md`; `mainmatter/4. ...tex:~1205` |
| E8 | `mainmatter/1. Introduction.tex:18` | "**It has never had to be tested**, because the criterion in use judges a single instant and cannot represent duration at all" | TS | Chapter 2 establishes something more careful: Japanese verification **does** run two-dimensional transient saturated-unsaturated seepage analysis driven by real hydrographs, and judges at the instant the high-water period ends; what it lacks is a state variable, not duration in the loading. "Cannot represent duration at all" overstates in a way the 2026-08-28 correction campaign specifically set out to remove elsewhere. | `mainmatter/2. ...tex:~222` and `tab: framework comparison`, last column ("On the loading side only") |
| E9 | `mainmatter/1. Introduction.tex:18` | "National levee-failure statistics **appear to support** that premise" | TW | The statistics are unambiguous on their own terms (Hagibis: overtopping 86 per cent, seepage 1 per cent), and Ch 8 quotes them without hedge. If the hedge is meant to signal that aggregate statistics do not settle a per-section question, that is a different and better sentence, and Ch 8 already writes it ("a failure record is a record of competing risks"). | `docs/japanese_levee_failure_criterion_review_2026-08-28.md` section J6; `mainmatter/8. Discussion.tex:~1004` |

### Category F. Provenance of unpublished-consultation claims

| # | Location | Claim | Class | Why it is miscalibrated | Evidence |
|---|---|---|---|---|---|
| F1 | `mainmatter/4. ...tex:583`, `:693`, `:899`; `mainmatter/6. ...tex:1072` | "a choice **the model's author confirmed** as appropriate for flashy typhoon rivers"; "a choice **endorsed by the progression model's author**"; "**The model's author confirmed it** as the realistic assumption"; "the baseline the progression model's author endorses" | PROV | Four main-body claims rest on an unpublished consultation and carry **no in-text attribution of any kind**. Each is genuinely supported in the engine record, but a reader of the thesis has no way to see that a source exists. Appendix C states the convention generically ("Decisions confirmed or endorsed by the progression model's author during the project consultations are marked accordingly in the repository records") without a pointer from the four sites. | `docs/joost_pol_meeting_vragen.md` items 4 (2D formula), 7 (r_l = 0), 8 (flood-fighting clause), and the k-d70 question; all four verified present this session |
| F2 | `appendix/appendix-g.tex:261` | "evaluated at the **author-confirmed** calibrated coefficient for that test, C_e = 0.010; the value 0.014 printed in the source figure caption is a **confirmed erratum**" | PROV | Same issue, and higher stakes: the thesis asserts that a published figure caption is wrong, on the strength of an unattributed private communication. | `docs/decisions/` M7 reference-values note; `docs/references/pol_compgeo_2024.pdf` |


**Work package 5 executed 2026-08-29** (`msc-thesis` commit `6970ded`). Both findings were verified as supported before anything was edited. F2's "confirmed erratum" is carried by the 2026-07-08 follow-up recorded in `docs/validation/pol-meeting-2026-07-07-dispositions.md`, **not** by the answer in `docs/joost_pol_meeting_vragen.md`, which records the inconsistency only as acknowledged and under investigation. Convention chosen: a single `@misc` entry `pol_2026_pers_comm` cited with `\parencite`, matching the existing `fukuda_2025_internal` register and costing the least typeset space of the three candidates. A **sixth site** of the same class was attributed with it, the k_aq-d_70 endorsement at `mainmatter/3. ...tex:352`, which this table's evidence column named and its location column omitted.

### Category G. Coverage gap

| # | Scope | Class | Why it matters |
|---|---|---|---|
| G1 | Every number introduced by the 2026-08-28/29 RQ1 campaign: all Delta-beta values, `tab: gap components beta`, `tab: equal convention`, the additive-ladder prose in Ch 6, and their restatements in the Summary, Ch 8 and Ch 9 | unverified | The last full number reconciliation (`docs/thesis_number_reconciliation_2026-08-21.md`) predates this material by a week. Findings B1, B2 and C1 were all found inside it, which is direct evidence that the block has not been independently traced. |

---

## 2. Categories, and why they group this way

The grouping is by **what kind of evidence settles the finding**, because that is
what determines what a fixing session has to do and how long it takes.

| Category | Findings | Settled by | Repos touched |
|---|---|---|---|
| **A. Internal consistency** | A1 to A11 | Reading the thesis against itself, plus three cheap artifact look-ups | msc-thesis (+ two engine JSONs) |
| **B. The RQ1 ordering register** | B1, B2 | One engine document (`rq1_beta_reexpression_2026-08-28.md`) | msc-thesis |
| **C. The equal-convention fraction** | C1, C2 | One engine document (`equal-head-convention-study.md`) | msc-thesis |
| **D. Literature** | D1 to D9 | Reference PDFs and the web | msc-thesis (+ engine provenance notes) |
| **E. Interpretive calibration** | E1 to E9 | Judgment against results already in the thesis | msc-thesis |
| **F. Provenance of consultations** | F1, F2 | A convention decision by the owner, then a mechanical edit | msc-thesis |
| **G. Reconciliation of the newest block** | G1 | Systematic trace of every post-2026-08-21 number to an artifact | msc-thesis + engine |

B and C are separated from A in the log but are **executed together**: they are
the same set of sentences in the same four files (Summary paragraph 3, Ch 6
sections `subsec: Why the Two Sections Differ` / `sec: The Two Criteria on One
Head Convention` / `sec: Piping Results Synthesis`, Ch 8 sections 1 and 7, Ch 9
RQ1 and Overall Conclusion), and splitting them would put two review passes into the
same paragraphs.

---

## 3. The fix plan: six work packages, in order

**Read this before sending any of them.**

- Every work package is self-contained and ready to paste. Do not edit them.
- Each ends with commit and push. `msc-thesis` is your Overleaf mirror, so a
  push updates Overleaf; each work package says so explicitly.
- the msc-thesis project rules carry a standing rule that multi-chapter tasks must be
  planned and approved before editing. Each work package below **lists every passage it
  will touch**, so sending the work package is the approval. Each work package states this,
  so the review pass does not stall waiting for you.
- After each review pass, run the checkpoint under it before sending the next.

---

### WORK PACKAGE 1 of 6: The RQ1 headline register (findings B1, B2, C1, C2)

```
I am finishing an MSc thesis and doing a final claim-calibration pass before
submission. You are fixing one specific, cross-chapter miscalibration.

## The thesis

Title: "Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems: A Case Study of the Tokachi River Basin in
Hokkaido, Japan" (TU Delft MSc, civil engineering).

LaTeX source: D:\repositories\msc-thesis  (a Git-synced Overleaf mirror; read
files from disk, never compile locally)
Model and analysis code, and all evidence: D:\repositories\bep-reliability-engine

What the thesis does: it compares a time-dependent backward-erosion-piping (BEP)
progression criterion (Pol 2024) against a conventional steady-state criterion
(Sellmeijer 2011), on one shared Monte Carlo sample, at four confined
cross-sections of the Tokachi right bank (KP 57.4, KP 58.8, KP 60.0, KP 62.0).
Two sections carry toe drains and are evaluated as if undrained; KP 57.4 has a
side berm; KP 62.0 is unreinforced. The headline comparison is reported first as
a conditional reliability-index difference, Delta-beta = beta_transient -
beta_static, with the probability ratio B = P_static / P_transient carried
alongside. That reliability-index re-expression was added on 2026-08-28 and has
not been through an independent number check since.

## What is wrong

Four claims about the *register* of that comparison are miscalibrated. They
recur across the Summary and Chapters 6, 8 and 9.

### B1. "The ordering reverses" is false as stated (5 sites)

Current wording, in various forms:
  "in reliability-index terms the ordering reverses, the drained sections
   carrying the larger index shift despite the smaller ratio"

Sites:
  frontmatter/summary.tex:8            ("with the ordering reversed")
  mainmatter/6. Results - Subsurface Piping Assessment.tex:670-673
  mainmatter/6. Results - Subsurface Piping Assessment.tex:1608-1610
  mainmatter/8. Discussion.tex:34
  mainmatter/8. Discussion.tex:580
  mainmatter/8. Discussion.tex:1015
  mainmatter/9. Conclusions and Recommendations.tex:53-55

The measured design-level values are (see verification below):
  KP 60.0 (drained)      Delta-beta 1.87   B 2.92
  KP 57.4 (berm-only)    Delta-beta at least 1.27, point estimate 1.56   B at least 148
  KP 58.8 (drained)      Delta-beta 1.22   B 2.75
  KP 62.0 (unreinforced) Delta-beta 0.90   B 26.9

So the B ordering is 57.4 > 62.0 > 60.0 > 58.8 and the Delta-beta ordering is
60.0 > 57.4 > 58.8 > 62.0. KP 57.4 is second in BOTH. It is a re-ordering, not a
reversal, and the berm-only section outranks a drained one in the index. What
actually happens, and what the text should say, is that KP 62.0 falls from second
to last while KP 60.0 rises from third to first.

### B2. "0.9 to at least 1.9" puts the bound at the wrong end (3 sites)

Sites:
  mainmatter/8. Discussion.tex:580
  mainmatter/8. Discussion.tex:1015
  mainmatter/9. Conclusions and Recommendations.tex:492

In probability terms the top of the range IS a bound (KP 57.4, B at least 148).
In reliability-index terms the top of the range is KP 60.0's fully resolved 1.87,
and the bounded value (KP 57.4, at least 1.27) sits in the middle. "0.9 to at
least 1.9" therefore asserts an open upper end that the measurement closes. The
Summary and Chapter 6 already write "0.9 to 1.9" correctly; these three sites do
not.

### C1. The "54 per cent" retained fraction is not reproducible from its own table

Current wording, in various forms:
  "the equal-convention comparison retains 54 to 83 per cent of the as-published
   Delta-beta at the four design levels"

Sites:
  frontmatter/summary.tex:8
  mainmatter/6. Results - Subsurface Piping Assessment.tex (in the subsection
    labelled "sec: The Two Criteria on One Head Convention", the paragraph
    beginning "At the design level the head convention accounts for most")
  mainmatter/6. Results - Subsurface Piping Assessment.tex:1622 (synthesis)
  mainmatter/8. Discussion.tex:45
  mainmatter/9. Conclusions and Recommendations.tex:68

The 54 per cent belongs to KP 57.4 and is 0.842 / 1.558, where 1.558 is that
section's design-level Delta-beta POINT ESTIMATE resting on two failing transient
realizations in 1e6 -- below the thesis's own pre-registered resolution floor of
30 failing realizations. The table printed immediately above the sentence
(label "tab: equal convention") shows the BOUND instead, "at least 1.27" and "at
least 148", from which a reader computes 66 per cent, not 54. The thesis
elsewhere explicitly refuses to quote that point estimate ("The point estimate
that a resampling of two realizations would produce is not reported").

### C2. "Two readings agree within about a quarter" is true at one section only

Site: frontmatter/summary.tex:8, the clause
  "(no single such convention is unique; two readings agree within about a
   quarter)"

At KP 62.0 the gross-vs-gross and reduced-vs-reduced equal-convention readings do
agree within 10 to 24 per cent (7.34 against 8.03). At KP 57.4 they split 23.1
against 12.0, roughly a factor of two. Chapter 6 instructs exactly this: "quote
KP 62.0 as 7 to 8, KP 57.4 as about 5 to 23". The Summary keeps only the
flattering half.

## Verification you must do first

Read these two engine documents in full and confirm every number above against
them. Do not take my figures on trust.

  D:\repositories\bep-reliability-engine\docs\rq1_beta_reexpression_2026-08-28.md
    -- section 2 has the design-level anchor table (Delta-beta and B per section)
    -- section 4 has the additive ladder, including the KP 57.4 39.21 m row whose
       Delta-beta total is 1.56 on two failing realizations
    -- section 5 has the epistemic arms at the KP 62.0 anchor

  D:\repositories\bep-reliability-engine\docs\decisions\equal-head-convention-study.md
    -- section 4.2 has the retained fractions (63 / 54 / 72 / 83 per cent) and
       shows which denominators they use
    -- section 4.3 has the two-reading comparison at both sections

If a persisted artifact is needed to settle a number, the traceability table at
the end of rq1_beta_reexpression_2026-08-28.md names the HDF5 and JSON files. You
do not need to re-run the engine for this task; if you conclude that you do, stop
and tell me instead.

## What to change

Fix each claim so that it is truthful and calibrated to what was measured. Some
guidance, not a script:

- For B1, replace "the ordering reverses / the drained sections carry the larger
  index shift" with an accurate statement of what the re-ordering is. Keep it
  short; this claim appears seven times and the thesis is at a hard page budget.
  The substantive point that survives -- that a fifty-fold spread in probability
  is a spread of about one reliability-index unit, and that the section carrying
  the largest ratio is not the one carrying the largest index shift -- is worth
  keeping.
- For B2, the three "at least 1.9" sites should match the Summary's and Chapter
  6's already-correct "0.9 to 1.9". Check whether the surrounding sentence
  intended the "at least" to attach to the ratio (where it is correct) and
  restructure minimally if so.
- For C1, decide between two honest options and apply it at all five sites:
  either (a) state the range against the resolved denominators and say what the
  KP 57.4 entry rests on, or (b) keep 54 per cent and add the one clause the
  reader needs ("against that section's below-floor point estimate"). Whichever
  you choose, the number in the text must be reproducible from the table printed
  next to it, or the table must be made to carry what the text divides by.
- For C2, the Summary should not claim an agreement that holds at one of two
  sections. Chapter 6's own instruction is the model.

## Constraints

- This work package lists every passage you will touch, so it is your approval to make
  these multi-chapter edits directly. Do not stop to ask for a plan; the standing
  "plan first" rule in the msc-thesis project rules is discharged by this work package.
- Read the current file state from disk before editing. Do not work from memory
  of any earlier version.
- Make the smallest edit that fixes the claim. Do not re-word neighbouring prose.
- Style rules, all hard: no em dashes in any form (neither the character nor
  "---"); ranges are written "X to Y", never "X-Y"; no Japanese script anywhere in
  a .tex file; preserve every \label and every citation key exactly; XeLaTeX.
- Do not compile.
- If a claim turns out to be correct as written, LEAVE IT UNCHANGED and report
  that back to me with the evidence. Do not edit for the sake of editing.

## Done means

1. Every one of the four claims (B1, B2, C1, C2) has been checked against the two
   engine documents and is either corrected or reported back as already correct,
   at every site listed.
2. You have re-read the corrected sentences in place and confirmed no
   cross-reference, no \ref, and no adjacent claim has been broken.
3. You have grepped the whole of frontmatter/, mainmatter/ and appendix/ for any
   further site of the same four claims that my list missed, and fixed those too.
4. The em-dash and Japanese-script checks pass over every file you touched.
5. You have written me a short report: for each claim, what you found, what you
   changed, and where.
6. You have committed the changes in D:\repositories\msc-thesis with a descriptive
   message and pushed to origin (this updates Overleaf). If you also changed
   anything in the engine repo, commit and push that too.
```

**Checkpoint before Work package 2.** Open the Overleaf project and read the Summary's
third paragraph, Chapter 6's synthesis, Chapter 8 section 1, and Chapter 9's RQ1
answer. Confirm: (a) no sentence still says the ordering "reverses" without
saying what the re-ordering actually is; (b) "at least 1.9" is gone from all
three sites; (c) the retained-fraction sentence and the table beside it now agree
arithmetically. If the review pass reported any claim as already correct, check that
one yourself against the anchor table in `rq1_beta_reexpression_2026-08-28.md`.

---

### WORK PACKAGE 2 of 6: Literature-anchored claims (findings D1 to D9)

```
I am finishing an MSc thesis and doing a final claim-calibration pass before
submission. Your task is to verify a set of claims against the literature they
cite, and correct the ones that do not survive the check.

## The thesis

Title: "Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems: A Case Study of the Tokachi River Basin in
Hokkaido, Japan" (TU Delft MSc, civil engineering).

LaTeX source: D:\repositories\msc-thesis  (a Git-synced Overleaf mirror; read
files from disk, never compile locally)
Model, analysis code, provenance documents: D:\repositories\bep-reliability-engine
Reference PDFs: D:\repositories\bep-reliability-engine\docs\references\
  (this directory is gitignored and machine-local; the PDFs you need are there.
   Use PyMuPDF (`import fitz`) to extract text. If a PDF's text layer is broken,
   rasterize and read the pages.)

What the thesis does: it compares a time-dependent backward-erosion-piping
progression criterion (Pol 2024) against a conventional steady-state criterion
(Sellmeijer 2011) at four cross-sections of the Tokachi right bank, then composes
the result with overflow and scour into a system failure probability under
historical and +4 K climate ensembles.

Context you need: a full number-reconciliation pass over this thesis was run on
2026-08-21 and traced 431 claim groups to computed artifacts. It explicitly did
NOT verify the 58 values carried by a literature citation. That is what you are
doing now.

## The claims to check

### D1 (likely wrong). Chapter 2, the Pol reduction range

File: mainmatter/2. Theoretical and Empirical Foundations.tex, line ~19
Current: "Probabilistic analyses by \textcite{pol_sie_2024} bear out that
intuition for typical scenarios: short-duration hydraulic loads such as coastal
storm surges reduce the failure probability by a factor of 10 to $10^6$ relative
to steady-state assumptions."

Source: docs/references/pol_sie_2024.pdf
Check the abstract and section 3.4. My reading is that the abstract says
"a factor of 5 to more than 10^6", and that section 3.4 splits the range by
configuration rather than by coastal-versus-river alone. Confirm or refute, and
correct the sentence to what the source actually says, including whether the
attribution to coastal storm surges is accurate for the whole range.

### D2 (a corroboration the thesis is entitled to and does not use)

Same source, section 3.4, near the discussion of the factor F_td. My reading is
that it says, of river levees: "In other situations with river levees (coarse
sand and thin blanket) effects are limited (F_td < 5) and the current assumption
of instantaneous failure can be considered realistic."

That is the Tokachi configuration exactly: a coarse gravel aquifer under a 0.45
to 0.85 m cohesive blanket. The thesis's own central duration result is that
"flood duration alone accounts for a factor of one to about six wherever the
failure counts support the statement" (Chapter 6, the "pure duration" column of
the table labelled "tab: gap components"; restated in Chapter 8 section 1,
Chapter 9 RQ1, and the Summary). At present that result is presented as a
standalone measurement and reads as a deflation of the thesis's own premise.

Verify the source statement verbatim. If it holds, find the ONE best place to
note that the thesis's measured duration factor is consistent with what the
progression model's own authors report for this configuration class, and add a
single sentence there with the existing citation key. Do not add it in more than
one place, and do not overstate it: it is an independent published expectation
matching a measurement, not a validation.

### D3 (numbers correct, inference too strong). Chapter 2, the r_l = 0 justification

File: mainmatter/2. Theoretical and Empirical Foundations.tex, line ~187
Current: "The recovery experiments of \textcite{pol_thesis_2022}, however, found
that reloading a partially formed pipe after nine months of rest produced a
20~per cent lower critical head and a 140~per cent higher progression rate,
through irreversible damage in the foundation. For closely spaced events such as
consecutive typhoons, subsurface erosion consequently behaves as a strictly
cumulative, irreversible process with $r_l = 0$..."

Source: docs/references/pol_thesis_2022.pdf. The two numbers are exact; I checked
them. The problem is the "consequently". Search the same passage for what the
recovery test showed about the pipe GEOMETRY. My reading is that it says the
erosion process "had to start all over again" and describes "partial strength
recovery" over nine months, i.e. the pipe closed and the resistance was reduced.
The thesis's r_l = 0 does the opposite pairing: it carries the pipe LENGTH
forward and holds the resistance fixed within a realization (see mainmatter/4.
Methodology.tex, the subsection labelled "sec: Compound Event Modelling").

Confirm this reading against the source. If it holds, rewrite the inference so
that the nine-month experiment supports what it actually supports, and let the
real justification carry the weight: the inter-peak interval in a consecutive
typhoon sequence is hours to days, not nine months, and Chapter 5 already records
that the one field observation bearing on cross-event memory points to memory
held in the blanket rather than in the pipe. Chapter 4 already states the
distinction correctly ("The irreversibility is exclusively geometric"), so this
is a Chapter 2 fix, not a doctrine change.

### D4. Chapter 2, the Lane (1935) case count

File: mainmatter/2. Theoretical and Empirical Foundations.tex, in the paragraph
beginning "Two questions precede the adoption of that model"
Current: "the weighted form of \textcite{lane_1935}, which credits vertical path
segments more heavily than horizontal ones on the evidence of 278 cases"

Lane (1935) is not in docs/references/. Search the web for the primary source
(Lane, E. W., "Security from under-seepage: masonry dams on earth foundations",
Transactions ASCE, 1935) and establish the case count Lane actually analysed. If
you cannot establish it from a reliable source, say so and tell me the options
rather than substituting a number. NEVER invent a citation or a figure.

### D5 (notation collision). Chapter 2, "i_c >= 0.5"

File: mainmatter/2. Theoretical and Empirical Foundations.tex, in the subsection
labelled "subsec: The Sequential STPH Failure Mechanism"
Current: "since previous geotechnical assessments identified critical exit
gradients ($i_c \geq 0.5$) at the landside toe \parencite{oyo_1999}"

The same subsection defines $i_c = \gamma'_\mathrm{bl}/\gamma_w$ as the Terzaghi
critical heave gradient, which for this blanket is about 0.70. The 0.5 in the
sentence above is the Japanese allowable-gradient screening criterion, a
different object. Chapter 3 and Appendix G both use 0.5 correctly as the national
criterion (see the caption of the table labelled "tab:oyo_1998"). Confirm with
D:\repositories\bep-reliability-engine\docs\oyo_1998_framing_review_2026-08-24.md,
which quotes the OYO criterion text, then fix the symbol collision without
changing the physics or the value.

### D6 (unverified, and internally inconsistent). The 15 per cent gravel threshold

Sites:
  mainmatter/2. Theoretical and Empirical Foundations.tex (near the end of the
    subsection labelled "subsec: Historical Field Evidence: Initiation Without
    Completion"): "It excludes cross-sections whose embankment gravel content
    averages 15~per cent or more"
  appendix/appendix-g.tex (in the subsection labelled "app subsec:
    Erosion-Limited Consensus"): "very low seepage-failure risk where embankment
    gravel content exceeds 15~per cent"

"averages 15 per cent or more" and "exceeds 15 per cent" are different
thresholds. Check both against docs/references/2019-suiko-fukuoka.pdf (the
Fukuoka 2019 vulnerability-index paper) and, if you can obtain it, PWRI Report
4300 (2015). Make the two statements consistent with each other and with the
source. The document is in Japanese; that is expected. Remember: no Japanese
script may appear in any .tex file, so romanise or translate anything you carry
across, and put any original-script provenance in the engine repo instead.

### D7 (open item, flagged for an owner ruling in 2026). The Abashiri duration

Sites:
  mainmatter/2. Theoretical and Empirical Foundations.tex, line ~189
  mainmatter/8. Discussion.tex, lines ~100-101
  appendix/appendix-g.tex, in the subsection labelled "app subsec: Japanese
    Empirical Advances and the Regional Field Record"
Current: "On the Abashiri River the September 2001 flood held the stage above the
warning level for 234 continuous hours, some ten days"

Carried by \parencite{obihiro_levee_inspection_2008}. The 2026-08-21
reconciliation flagged it (see section 3.2 of
D:\repositories\bep-reliability-engine\docs\thesis_number_reconciliation_2026-08-21.md)
because Chapter 8 uses it as a quantitative counterweight to a computed result,
which is the one place a cited duration does argumentative work against an engine
number. Attempt to verify it: look for the source in
docs/references\ and its subdirectories (the tokachi_river_basin subdirectory and
the compressed PDFs are candidates), and search the web for the Abashiri River
September 2001 flood duration. If you can verify it, say so and leave the text
alone. If you cannot, tell me exactly what you searched and what the options are;
do not weaken the text on the strength of a failed search.

### D8 (open item). The conductivity prior spread of "about 2.9"

Sites:
  mainmatter/8. Discussion.tex, in the subsection labelled "subsec: Conductivity
    Prior Limitation"
  appendix/appendix-e.tex, around line 214
Current: "The adopted coefficient of variation places the central 95~per cent of
the conductivity prior within a factor of about 2.9"

The prior is lognormal with CoV = 0.50, so sigma_ln = sqrt(ln 1.25) = 0.4724.
Direct computation gives 2.52 for P97.5 / median, 6.36 for P97.5 / P2.5, and
about 2.6 for the tightest mean-relative interval containing 95 per cent. None is
2.9. See section 3.1 of the reconciliation document named in D7. Its role in both
passages is a comparison against Japanese guidance characterising ordinary
measured scatter as "a factor of several to about ten", which survives any of
those values. Pick the construction that matches what the sentence claims (it
says "the central 95 per cent ... within a factor of"), compute it, correct both
sites to the same number, and state the construction in the appendix so the
figure is reproducible.

### D9 (juxtaposition reads as a non-sequitur). The IJkdijk deviations

File: mainmatter/5. Verification, Validation, and Global Sensitivity Analysis.tex,
lines ~40-46
Current: "The critical-head formulation reproduces the IJkdijk fine-tuning cases
of \textcite{sellmeijer_2011} to within 2 to 15~per cent, the widest being the
coarse-sand test the source itself reports as deviating by 25~per cent: for the
first IJkdijk test the rule evaluates to 2.07~m against the observed 2.30~m."

Appendix G (subsection "app subsec: Reference-Case Verification of the Kernels")
has all three tests right: test 1 is 2.07 against 2.30 (10 per cent), test 3 is
2.07 against 2.10 (2 per cent), and the coarse-sand test 2 is 2.01 against 1.75
(15 per cent). Chapter 5 names "the widest" and then illustrates with the FIRST
test, which is not the widest. Fix the juxtaposition. While you are in
docs/references/sellmeijer_2011.pdf, also confirm that the 25 per cent figure is
genuinely the source's own reported deviation for that test, and that the
approximately 13 per cent regression scatter Appendix G borrows as an acceptance
band is correctly described as belonging to the small and medium-scale set.

## Constraints

- This work package lists every passage you will touch, so it is your approval to make
  these multi-chapter edits directly. Do not stop to ask for a plan; the standing
  "plan first" rule in the msc-thesis project rules is discharged by this work package.
- NEVER invent a number, a citation, or a source. If a value cannot be
  established, report that and stop for that item.
- Read the current file state from disk before editing.
- Make the smallest edit that fixes the claim. Do not re-word neighbouring prose.
- Style rules, all hard: no em dashes in any form (neither the character nor
  "---"); ranges are written "X to Y", never "X-Y"; no Japanese script anywhere in
  a .tex file (references.bib is the sole exception and you are not editing it);
  preserve every \label and every citation key exactly; XeLaTeX; do not compile.
- If a claim turns out to be correct as written, LEAVE IT UNCHANGED and report
  that back to me with the source passage that confirms it.

## Done means

1. All nine items (D1 to D9) have been checked against their sources, and each is
   either corrected, confirmed correct, or reported as unverifiable with a
   specific account of what you searched.
2. Any value you corrected is traceable: you quote the source passage in your
   report.
3. For D2, either one sentence has been added in one place, or you have told me
   why the source does not support it.
4. Where a check produced provenance worth keeping (a verbatim source quotation,
   a page number, a Japanese-language passage), you have recorded it in
   D:\repositories\bep-reliability-engine\docs\ in the style of the existing
   provenance documents there, so the next reader can find it. No thesis prose,
   no .tex and no .bib files may be created in the engine repository.
5. The em-dash and Japanese-script checks pass over every .tex file you touched.
6. You have written me a short report, item by item.
7. You have committed and pushed both repositories: D:\repositories\msc-thesis
   (which updates Overleaf) and D:\repositories\bep-reliability-engine.
```

**Checkpoint before Work package 3.** Read the review report item by item. Confirm
that D1's replacement range matches the Pol abstract verbatim, and decide whether
you accept the D2 sentence (this is the one item where the review pass adds a claim
rather than trimming one, so read it in place). Check that D4, D7 and D8 were
either resolved with a source or reported as unresolved, and rule on any that
came back unresolved before continuing.

---

### WORK PACKAGE 3 of 6: Interpretive calibration (findings E1 to E9)

```
I am finishing an MSc thesis and doing a final claim-calibration pass before
submission. Your task is nine interpretive claims that are pitched wrong relative
to the thesis's own evidence: five overreach, four are more cautious than the
results warrant.

## The thesis

Title: "Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems: A Case Study of the Tokachi River Basin in
Hokkaido, Japan" (TU Delft MSc, civil engineering).

LaTeX source: D:\repositories\msc-thesis  (a Git-synced Overleaf mirror; read
files from disk, never compile locally)
Model, analysis code, evidence: D:\repositories\bep-reliability-engine

What the thesis does: at four confined cross-sections of the Tokachi right bank
it evaluates backward erosion piping under a time-dependent progression criterion
and under a conventional steady-state one, on one shared Monte Carlo sample;
conditions the result on the documented survival of the August 2016 typhoon
sequence; and composes the fragility with overflow and fluvial scour into an
annual system failure probability under historical and +4 K climate ensembles.

Almost every item below is settled by reading the thesis against itself. Where
an engine artifact is needed I name it.

## The claims

### E1 (too strong). "The premise is correct"

File: mainmatter/8. Discussion.tex, lines 17-18
Current: "Based on Chapter~\ref{chap: Results: Subsurface Piping Assessment}, the
premise is correct, but its size depends on the metric asked."

The premise, as Chapter 1 sets it out (mainmatter/1. Introduction.tex, section
"Research Problem"), is that flashy flood waves recede before seepage erosion can
develop into a breach, so that these levees are protected against backward
erosion piping by the hydrology itself. What Chapter 6 establishes is weaker in
two ways the same Discussion section then spells out:
  - the direction (transient below static) is a THEOREM of the nested
    formulations, not a finding: the thesis proves it in mainmatter/4.
    Methodology.tex at the end of the subsection labelled "sec: Transient Limit
    State"; and
  - of the measured gap, flood duration alone is worth a factor of one to about
    six, most of the rest being a head-convention difference between two models
    that were never intended to share a driving head.
And Chapter 7 finds that piping accounts for about 70 to 100 per cent of the
summed annual failure contribution at every section where the comparison exists.

Re-pitch that opening sentence so it says what was found. The paragraph that
follows it is already well calibrated, so the fix is one sentence.

### E2 (too weak). The Summary hedges a measured null

File: frontmatter/summary.tex, paragraph 6
Current: "Compound clustering is present but doesn't appear to drive the
increase; clustered years are more dangerous mainly because they keep the stage
above the critical level longer."

Chapters 7, 8 and 9 all state this as a measured result, not an impression: the
compound stratification's historical flood-ensemble sampling intervals (0.3 to
9.3 and 0.1 to 18.4 at the two well-populated sections) both include one, while
the duration stratification resolves concentrations of about 150 and about 380;
and the compound verdict is floor-sensitive where the duration verdict is not.
"Is present but is not the channel" is the body's own phrasing. Bring the Summary
up to the register the body supports. Check the body first
(mainmatter/7. Results - System Integration and Climate Sensitivity.tex,
subsection "subsec: The Duration Channel"; mainmatter/8. Discussion.tex, the
section on compound events; mainmatter/9., RQ4).

### E3 (too strong, missing a caveat it applies elsewhere). "Discredits"

Sites:
  mainmatter/6. Results - Subsurface Piping Assessment.tex, subsection labelled
    "subsec: How the Constraint Divides", the paragraph beginning "This is a
    positive result"
  mainmatter/8. Discussion.tex, the closing paragraph of the section labelled
    "sec: The Nesting of the Two Failure Sets"
Current, in both: "Survival evidence therefore discredits the absolute level of
the static comparator while remaining comfortably consistent with the transient
one."

The 58 and 73 per cent static rejection is computed on the UNDRAINED foundation
at KP 58.8 and KP 60.0, while the survival that supplies the evidence was
produced by a structure with toe drains installed in 1999 to 2003. Chapter 6
applies exactly this confound to the posterior tightness a page earlier ("The
survival that supplies the evidence was produced by a drained structure, while
the likelihood is evaluated on the undrained foundation... The posterior is
tighter than the observation licenses"). It applies with the same force to the
static comparator's apparent over-rejection, and is not restated there.

The verdict may well survive: check the size of the effect against
D:\repositories\bep-reliability-engine\docs\decisions\0050-toe-gradient-relief-drained-bracket.md
and its companion JSONs (the measured post-works berm alone takes the design-level
conditional transient probability from 0.263 to 0.108 at KP 58.8 and from 0.314 to
0.111 at KP 60.0). Then either attach the caveat where the claim is made, or, if
the bracket shows the verdict is robust to it, say that instead. Do not simply
delete the claim.

### E4 (too weak). The nesting paragraph undersells its own proof

File: mainmatter/8. Discussion.tex, in the section labelled "sec: The Nesting of
the Two Failure Sets", the paragraph beginning "The second consequence runs the
other way"
Current opening: "Nesting means the static criterion was never wrong in the
permissive direction at this loading."

Three sentences later the same paragraph proves the general result: "Transient
failure therefore implies static failure for every input and every hydrograph,
and no flood of any duration can break the containment." The opening restriction
"at this loading" is weaker than what the paragraph goes on to establish, and the
containment is a construction-level property (see mainmatter/4. Methodology.tex,
end of the subsection labelled "sec: Transient Limit State"). Align the opening
with the proof.

### E5 (too weak / imprecise). The Summary understates the top annual value

File: frontmatter/summary.tex, paragraph 6
Current: "annual system failure probability at the four characterized sites rises
by factors of 5.5 to 12.7, against a flood-ensemble sampling interval of roughly a
factor of two, and an aquifer conductivity range that is far wider still, reaching
about one per cent per year."

The largest warming-scenario value is 4.1e-2 per year at KP 58.8, which the same
paragraph later gives correctly as "rising from about 0.7 to 4 per cent". Chapter
7 says "of order 1e-2 per year". Check the table labelled "tab: system annual" in
mainmatter/7. and fix the clause.

### E6 (imprecise). "Half to three-quarters"

File: frontmatter/summary.tex, paragraph 5
Current: "the filter cannot reach seepage length, which holds half to
three-quarters of the transient variance and moves by only 1.4~per cent"

The measured total-effect share is 0.49 to 0.78, which Chapters 6 and 8 both
quote as "0.49 to 0.78". 0.78 is above three-quarters. Fix.

### E7 (too strong, and gives away a strength). "No second event"

File: frontmatter/summary.tex, paragraph 5
Current: "The record supplies no second event to test further."

The body says something more precise and better supported: two candidate
supplementary events (September 2011 and 2006) were examined for admissibility
and the evidence set was closed on MEASURED grounds, not assumed ones. A bounding
replay holding the surveyed 2011 flood trace peak for 64 days at production sample
size rejects zero realizations in seven of eight strata and bounds 2011's marginal
information at 0.316 per cent of realizations in the eighth; 2006 has no
constructible loading at all. See mainmatter/4. Methodology.tex (the paragraph
beginning "The 2016 event is the sole survival constraint") and
D:\repositories\bep-reliability-engine\docs\decisions\0044-event-set-closure-2016-only.md.
The Summary currently reads as an absence of data. Make it read as the measured
closure it is, in one clause.

### E8 (too strong). "Cannot represent duration at all"

File: mainmatter/1. Introduction.tex, line 18
Current: "It has never had to be tested, because the criterion in use judges a
single instant and cannot represent duration at all, though the standard has
demanded regard to it since the 1970s."

Chapter 2 establishes something more careful, and did so deliberately: Japanese
verification DOES run two-dimensional transient saturated-unsaturated seepage
analysis driven by real flood hydrographs, and evaluates at the instant the
high-water period ends, so a longer high-water period does yield a higher phreatic
surface and steeper toe gradients. What it lacks is a state variable recording
accumulated erosion, so an exceedance of finite duration is indistinguishable from
one of unbounded duration. See mainmatter/2., the subsection labelled "subsec:
Japanese Levee Verification Practice", and the last column of the table labelled
"tab: framework comparison". A 2026-08-28 correction campaign removed exactly this
class of overstatement elsewhere in the thesis; this site was missed. Align
Chapter 1 with Chapter 2 without lengthening it.

### E9 (too weak). "Appear to support"

File: mainmatter/1. Introduction.tex, line 18 (the same long paragraph as E8)
Current: "National levee-failure statistics appear to support that premise."

The statistics are unambiguous on their own terms: of 142 levee breaches recorded
after the 2019 Typhoon Hagibis event, overtopping accounts for 86 per cent and
seepage for 1 per cent. Chapter 8 quotes them without a hedge and then makes the
sharper point that a failure record is a record of competing risks. Decide which
of two things the hedge is doing, and write that instead: either the statistics do
support the premise on their face (in which case drop the hedge), or the caveat is
that aggregate statistics cannot settle a per-section question (in which case say
that, which is Chapter 8's own move). Do not leave a vague "appear to".

## Constraints

- This work package lists every passage you will touch, so it is your approval to make
  these multi-chapter edits directly. Do not stop to ask for a plan; the standing
  "plan first" rule in the msc-thesis project rules is discharged by this work package.
- The Summary is a hard two pages and the main body is over a hard page budget, so
  every edit must be at most length-neutral. Prefer replacements that are shorter
  than what they replace.
- Read the current file state from disk before editing. Two earlier review passes in
  this campaign may already have touched the Summary and Chapters 6, 8 and 9.
- Make the smallest edit that fixes the claim. Do not re-word neighbouring prose.
- Style rules, all hard: no em dashes in any form (neither the character nor
  "---"); ranges are written "X to Y", never "X-Y"; no Japanese script anywhere in
  a .tex file; preserve every \label and every citation key exactly; XeLaTeX; do
  not compile.
- If a claim turns out to be correctly pitched as written, LEAVE IT UNCHANGED and
  report that back to me with the reasoning.

## Done means

1. All nine items (E1 to E9) are corrected or reported back as already correct.
2. For each of the four "too weak" items (E2, E4, E6, E9) you have confirmed the
   stronger statement against the body or the artifact BEFORE strengthening it.
   Do not strengthen a claim you have not checked.
3. You have confirmed that no edit contradicts a statement elsewhere in the
   thesis. In particular, E1's replacement must not contradict Chapter 8's own
   next paragraph, and E3's must not contradict the as-if-undrained framing that
   runs through Chapters 6, 7, 8 and 9.
4. The em-dash and Japanese-script checks pass over every file you touched.
5. You have written me a short report: for each item, what the evidence said, what
   you changed, and whether the edit lengthened or shortened the passage.
6. You have committed and pushed D:\repositories\msc-thesis (this updates
   Overleaf), and the engine repository if you changed anything there.
```

**Checkpoint before Work package 4.** Read the new Chapter 8 opening sentence (E1) and
the new Summary paragraphs 5 and 6 (E2, E5, E6, E7) in place, as prose. These are
the four highest-visibility sentences in the thesis and they need to read as
yours. Then confirm the review pass did not lengthen the Summary past two pages.

---

### WORK PACKAGE 4 of 6: Internal consistency sweep (findings A1 to A11)

```
I am finishing an MSc thesis and doing a final claim-calibration pass before
submission. Your task is eleven internal inconsistencies: places where the thesis
contradicts itself, or states a fact that its own table refutes.

## The thesis

Title: "Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems: A Case Study of the Tokachi River Basin in
Hokkaido, Japan" (TU Delft MSc, civil engineering).

LaTeX source: D:\repositories\msc-thesis  (a Git-synced Overleaf mirror; read
files from disk, never compile locally)
Model, analysis code, evidence: D:\repositories\bep-reliability-engine

What the thesis does: at four confined cross-sections of the Tokachi right bank
(KP 57.4, KP 58.8, KP 60.0, KP 62.0) it evaluates backward erosion piping under a
time-dependent progression criterion and under a steady-state one; conditions the
result on the documented survival of the August 2016 typhoons; and composes the
fragility with overflow and fluvial scour into an annual system failure
probability at 4 of 114 levee segments, under historical and +4 K climate
ensembles. Two of the four sections carry toe drains installed in 1999 to 2003
and are evaluated as if undrained; KP 57.4 has a side berm; KP 62.0 is
unreinforced.

## The eleven items

### A1. The Summary names the wrong section as unremediated-and-worst

File: frontmatter/summary.tex, paragraph 1
Current: "Remedial works were installed at three of the rated sections before the
flood, though not at the one with the worst exit gradient, so the field record
does not resolve which interpretation is correct."

The thesis's own table (label "tab:oyo_1998", in mainmatter/3.) gives the 1998
vertical exit gradients as KP 57.4: 0.040, KP 58.8: 1.300, KP 60.0: 0.500,
KP 62.0: 0.970, KP 63.4: 0.280. The worst is KP 58.8, which WAS fitted with toe
drains. The unremediated section is KP 62.0, which is second on the vertical
gradient (though it does carry the highest horizontal gradient, 0.660 against
KP 58.8's 0.620). Check both tables ("tab:oyo_1998" and "tab: section inputs")
and rewrite the clause so it is true. The point the sentence is making (that
remediation confounds the survival evidence) is sound and must be preserved.

### A2. Chapter 4 disagrees with three other places on one number

File: mainmatter/4. Methodology.tex, line ~1225
Current: "the hourly stage series of the Obihiro gauge (KP~56.6), the only
Tokachi mainstem gauge adjacent to the sections, whose peak of 38.07~m~T.P. on
31 August 2016 sits 0.07~m below the gauge's design high-water level."

Three other places say 0.19 m below a design level of 38.26 m:
  mainmatter/3. Study Area, Geological Setting, and Data.tex, line ~50
  appendix/appendix-d.tex, line ~238
  appendix/appendix-f.tex, line ~81
Establish which is right. Background: the basin's official record carries a
38.14 / 38.26 / 38.44 / 38.56 m T.P. set that is two plan revisions at two
chainages, not four different values at one; see
D:\repositories\bep-reliability-engine\docs\tokachi_chisuishi_full_review_2026-07-27.md.
Make all four sites agree, and make sure the sentence names the chainage the
design level belongs to.

### A3. The appendix count is stale

File: mainmatter/1. Introduction.tex, line 202
Current: "This thesis is organized into nine chapters, one per stage of the
research, followed by seven appendices... The seven appendices hold the
supporting material the main body refers to but does not reproduce, and the
figure names each."

report.tex inputs eight appendices, A to H. Appendix H ("The Reach-Wide Surface
Composition") was added by a later scope-narrowing campaign and this count was
not updated. The roadmap figure in the same section (label "fig: thesis roadmap")
also lists only A to G in its appendix node. Fix both the count and the figure
node. The figure is TikZ; keep the node's text width and do not disturb its
layout more than the extra entry requires.

### A4. Two incompatible definitions of "attainable" at KP 62.0

Sites:
  mainmatter/6. Results - Subsurface Piping Assessment.tex, lines ~164, ~347,
    ~382-384, and the two table row headers at ~731 and ~780
  mainmatter/7. Results - System Integration and Climate Sensitivity.tex, lines
    ~232 and ~814
The thesis says in most places that 50.5 m T.P. is "the top of the attainable
range" at KP 62.0, and that the grid above it is hypothetical. But Chapter 6 also
says "The largest stage any member of either ensemble reaches at this section is
51.47~m, so every extension level from 51.5~m upward describes a loading the
section cannot experience", which implies 51.0 m IS attainable. And Chapter 7
reports that 7 of the 5,400 warming years peak ABOVE 50.5 m, carrying 11.8 per
cent of that section's annual piping contribution, and that "The shaded region
lies above the maximum stage attained anywhere in the warming-scenario ensemble,
51.47~m at KP~62.0."

Establish what the engine actually uses. Look for the attainable-maximum field in
the KP 62.0 configuration and run metadata under
D:\repositories\bep-reliability-engine (configs\kp62_0_*.yaml and the
results\*.json sidecars), and for the ensemble peak-stage distribution at that
node used by the Phase 3 composition. Then make the thesis use ONE definition
consistently, and make sure the Chapter 7 caveat ("about a tenth of that annual
number rests on stages above the section's attainable range") remains coherent
with whichever definition you adopt. This is the item most likely to need an
artifact look-up rather than a wording fix, so do the look-up.

### A5. The Hagibis breach count

File: mainmatter/8. Discussion.tex, line ~1004
Current: "Overflow caused 86~per cent of the 140 levee breaches recorded during
the 2019 Typhoon Hagibis event and seepage 1~per cent
\parencite{mlit_2020_breach}"

The engine's verbatim reading of the source (MLIT 2020, Technical Study Committee
on River Levees after Typhoon No. 19, 3rd meeting, Document 2) records 142
breaches: overtopping 122 (86 per cent), erosion 12 (9 per cent), seepage 2
(1 per cent), unknown 6 (4 per cent). See section J6 of
D:\repositories\bep-reliability-engine\docs\japanese_levee_failure_criterion_review_2026-08-28.md.
122/142 = 86 per cent; 122/140 = 87 per cent, so the printed denominator and
percentage are not mutually consistent. Confirm against that review and fix.

### A6. "Saturated at every production section" contradicts its own list

Sites:
  mainmatter/3. Study Area, Geological Setting, and Data.tex, line ~131:
    "First, the correction is saturated at every production section: the realized
     $\tanh$ credits are $0.969$, $0.995$, $1.000$ and $0.835$."
  mainmatter/4. Methodology.tex, in the section labelled "sec: Hydraulic
    Translation": "the tanh correction is saturated at every production section,
    so $r_e$ is insensitive to foreshore width across the entire range the reach
    presents."

A credit of 0.835 (KP 62.0) is not saturation. The substantive point survives and
is measured: the narrow KP 62.0 foreshore raises r_e by only about 6 per cent
relative to an infinitely wide one, and the open-entry bound raises r_e by about
39 per cent and is worth at most 2.4e-4 in transient failure probability there.
Verify against
D:\repositories\bep-reliability-engine\docs\decisions\adr0025-foreshore-sensitivity.json
(the median_foreland_tanh_credit fields and the B_f=0m / B_f=100m / B_f=300m arms
at KP 62.0) and rewrite both sentences so the generalisation matches the list.

### A7. "Without re-ordering it" is contradicted by the companion it cites

File: mainmatter/5. Verification, Validation, and Global Sensitivity Analysis.tex,
end of the subsection labelled "subsec: GSA Interpretation"
Current: "All of these indices are properties of the model and its prior jointly,
so a revised prior re-weights the decomposition without re-ordering it, as the
companions above show."

The bulk-gradation companion two paragraphs earlier reports that d70 rises to a
total effect of 0.40 while C_e falls to 0.16, which reverses their matrix ordering
(C_e 0.34, d70 0.28 in the design-level table). Only the LEADING PAIR is
unchanged, which is what that companion paragraph actually says. Fix the
generalisation.

### A8. The Chapter 6 conditions register is missing a bracket it later relies on

File: mainmatter/6. Results - Subsurface Piping Assessment.tex, lines ~19-21 and
the table labelled "tab: piping conditions register"
Current: "nine conditions govern how every number here is to be read".

The register omits the CRITICAL PIPE LENGTH bracket. The same chapter's synthesis
(near line 1614), Chapter 8's subsection "subsec: Not Every Epistemic Knob Cancels
in a Ratio", and Chapter 9's RQ1 answer all list it as one of the four brackets on
which every ratio in the chapter is conditional. Its measured effect is a factor of
1.00 to 2.08 on the transient conditional probability and 1.11 to 1.67 on the
comparison between the two criteria, and it has ZERO common-mode channels, so the
static branch is exactly invariant under it and the displacement of the comparison
is exactly the reciprocal of the transient displacement. See
D:\repositories\bep-reliability-engine\docs\decisions\0049-critical-pipe-length-override.md
and its companion JSON. Add the row, update the count, and keep the row's prose to
the same length as its neighbours: the chapter is at a hard page budget.

### A9. "Changes which surface mechanism leads" overstates what the counts show

Sites:
  mainmatter/7. Results - System Integration and Climate Sensitivity.tex, the
    synthesis: "The as-received conversion would change which surface mechanism
    leads at 97 of the 114 segments in the historical climate"
  mainmatter/9. Conclusions and Recommendations.tex, the RQ3 answer, same claim
  appendix/appendix-h.tex, lines 95-105

Appendix H's own next sentence says "Most of those 97 are segments that have no
failure probability at all under the primary set", so at most of the 97 there is
no leading mechanism to change: the change is from "no mechanism loaded" to
"scour leads". Check the coverage table in appendix-h.tex (label "tab: mechanism
coverage") for the exact split, and make the two main-body sentences say what the
appendix says.

### A10. The exit-datum row reports one arm of a two-sided bracket

File: mainmatter/6. Results - Subsurface Piping Assessment.tex, the table labelled
"tab: piping conditions register", the "Exit-point datum" row
Current: "A 0.30~m shift lowers the KP~62.0 ratio from 26.9 to 13.9 and moves the
rejection by about a factor of two"

The bracket is two-sided: the minus-0.30 m arm gives B = 13.87 and the plus-0.30 m
arm gives B = 38.00. See
D:\repositories\bep-reliability-engine\results\hwl_bias_resolution\stage_d_epistemic.json.
The plus arm sits below the pre-registered resolution floor (2 transient failing
realizations against the required 30), which is a legitimate reason to lead with
the resolved arm, but a register whose stated purpose is to give the direction each
condition moves the result should not report a two-sided band as one-directional.
Add the other arm and its resolution status in as few words as possible.

### A11. A precision slip about the vertical datum

File: mainmatter/3. Study Area, Geological Setting, and Data.tex, line ~20
Current: "Because that agreement holds at independent chainages and under
independent freeboard constants, it establishes, and does not merely assume, that
Tokyo Peil and the meters-above-mean-sea-level datum of the engine coincide at
this reach."

Tokyo Peil IS the Japanese mean-sea-level datum by definition, so "the two datums
coincide" is not the proposition the freeboard agreement tests. What the agreement
actually establishes, and it is a good check, is that the ELEVATIONS THIS STUDY
INGESTED are on the official datum rather than on an offset local one. See section
on the T.P. identity in
D:\repositories\bep-reliability-engine\docs\tokachi_chisuishi_full_review_2026-07-27.md.
Re-point the sentence at the proposition its evidence supports.

## Constraints

- This work package lists every passage you will touch, so it is your approval to make
  these multi-chapter edits directly. Do not stop to ask for a plan; the standing
  "plan first" rule in the msc-thesis project rules is discharged by this work package.
- Read the current file state from disk before editing. Three earlier review passes in
  this campaign may already have touched the Summary and Chapters 6, 8 and 9.
- The main body is over a hard page budget, so A3 and A8, which add material, must
  be paid for inside the same paragraph or table wherever possible. Do not start a
  general page trim; that is not your task.
- Make the smallest edit that fixes each item. Do not re-word neighbouring prose.
- Style rules, all hard: no em dashes in any form (neither the character nor
  "---"); ranges are written "X to Y", never "X-Y"; no Japanese script anywhere in
  a .tex file; preserve every \label and every citation key exactly; XeLaTeX; do
  not compile.
- If an item turns out to be correct as written, LEAVE IT UNCHANGED and report that
  back to me with the evidence.

## Done means

1. All eleven items (A1 to A11) are corrected or reported back as already correct.
2. For A2 and A4 you have established the right value from an artifact or a
   provenance document, not chosen one of the two competing numbers by preference,
   and you say in your report which artifact settled it.
3. Where a number appears at more than one site (A2, A4, A6, A9), ALL sites now
   agree. Grep to confirm rather than assuming.
4. A3's figure node renders as valid TikZ (check the syntax by eye; do not
   compile).
5. The em-dash and Japanese-script checks pass over every file you touched.
6. You have written me a short report, item by item, naming the artifact that
   settled each numeric item.
7. You have committed and pushed D:\repositories\msc-thesis (this updates
   Overleaf), and the engine repository if you changed anything there.
```

**Checkpoint before Work package 5.** Grep the whole thesis for `38.07` and confirm
every site now carries the same offset and the same design level. Grep for
`saturated at every production section` and confirm it is gone or qualified. Open
Chapter 6's conditions register and count the rows against the number the prose
claims. Confirm the Chapter 1 roadmap figure still looks structurally sound in
the source.

---

### WORK PACKAGE 5 of 6: Attribution of unpublished-consultation claims (findings F1, F2)

```
I am finishing an MSc thesis and doing a final claim-calibration pass before
submission. This is a small, self-contained task about how five claims are
sourced.

## The thesis

Title: "Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems: A Case Study of the Tokachi River Basin in
Hokkaido, Japan" (TU Delft MSc, civil engineering).

LaTeX source: D:\repositories\msc-thesis  (a Git-synced Overleaf mirror; read
files from disk, never compile locally)
Model, analysis code, consultation records: D:\repositories\bep-reliability-engine

The thesis implements the time-dependent backward-erosion-piping progression
framework of Pol (2022, 2024). During the project the author consulted the
progression model's own author on several modelling choices, and the answers are
recorded in the engine repository at
D:\repositories\bep-reliability-engine\docs\joost_pol_meeting_vragen.md
(question-and-answer form) and
D:\repositories\bep-reliability-engine\docs\pol_meeting_briefing.md
(the questions as put).

## The problem

Five main-body and appendix claims rest on that unpublished consultation and carry
NO in-text attribution of any kind. A reader has no way to see that a source
exists at all. The claims are all genuinely supported in the engine record, so
this is an attribution problem, not a truth problem.

The sites:

1. mainmatter/4. Methodology.tex, line ~583, on omitting the flood-fighting clause
   of the erosion indicator:
     "The omission yields an unconditional upper bound on the transient failure
      probability, a choice the model's author confirmed as appropriate for flashy
      typhoon rivers."
   Support: joost_pol_meeting_vragen.md, question 8.

2. mainmatter/4. Methodology.tex, line ~693, on retaining the plane-strain scale
   exponent alpha = -1/3:
     "The plane-strain value is retained as the production baseline, a choice
      endorsed by the progression model's author for a two-dimensional
      Sellmeijer-based model at sub-meter blanket thicknesses..."
   Support: joost_pol_meeting_vragen.md, the question on the 2D-versus-3D critical
   pipe length and scale exponent.

3. mainmatter/4. Methodology.tex, line ~899, on the zero-recovery assumption:
     "The model's author confirmed it as the realistic assumption for peaks as
      closely spaced as consecutive typhoon landfalls."
   Support: joost_pol_meeting_vragen.md, question 7.

4. mainmatter/6. Results - Subsurface Piping Assessment.tex, line ~1072, the same
   plane-strain endorsement restated:
     "the plane-strain anchor the two production branches share is the baseline the
      progression model's author endorses..."

5. appendix/appendix-g.tex, line ~261, the highest-stakes one, because it asserts
   that a published figure caption is wrong:
     "evaluated at the author-confirmed calibrated coefficient for that test,
      $C_e = 0.010$; the value 0.014 printed in the source figure caption is a
      confirmed erratum."

Appendix C (appendix/appendix-c.tex, lines 13-15) already states the convention
generically: "Decisions confirmed or endorsed by the progression model's author
during the project consultations are marked accordingly in the repository
records." Nothing at the five sites points to it.

## What to do

1. First, verify each of the five claims against the consultation record in the
   engine repository. Quote the supporting answer in your report. If any of the
   five is NOT supported by that record, say so plainly and do not paper over it.

2. Then apply a single consistent attribution convention across all five sites.
   Options, in what I take to be increasing order of formality:
   (a) an in-text signal at each site plus a pointer to Appendix C, e.g. "(private
       communication; Appendix~\ref{app: Decision Register})";
   (b) a proper BibLaTeX @misc entry for the consultation, cited with \parencite
       at each site;
   (c) a footnote at the first site defining the convention, with the other four
       carrying a short cross-reference.
   Choose the one that fits the thesis's existing register and apply it uniformly.
   State in your report which you chose and why. NOTE: if you choose (b) you must
   edit references.bib, which is otherwise off limits; that is permitted for this
   task and for this entry only, and you must not alter any existing entry in that
   file.

3. For site 5 specifically, an appendix asserting that a published caption is an
   erratum needs its source visible. Make sure the reader can see that this rests
   on a communication with the paper's author, not on the thesis author's
   inference. If the engine record does not actually support "confirmed erratum",
   downgrade the wording to what it does support.

## Constraints

- This work package lists every passage you will touch, so it is your approval to make
  these edits directly. Do not stop to ask for a plan.
- Read the current file state from disk before editing. Four earlier review passes in
  this campaign may already have touched Chapters 4 and 6 and Appendix G.
- The main body is over a hard page budget. Whichever convention you choose must
  add as little typeset material as possible; that is a real constraint on the
  choice, not a footnote to it.
- Style rules, all hard: no em dashes in any form (neither the character nor
  "---"); ranges are written "X to Y", never "X-Y"; no Japanese script in any .tex
  file; preserve every \label and every existing citation key exactly; XeLaTeX; do
  not compile.
- If you conclude the current unattributed form is acceptable for a TU Delft MSc
  thesis and should stand, say so with your reasoning and change nothing. That is
  a legitimate outcome here and I would rather have the argument than a cosmetic
  edit.

## Done means

1. All five claims verified against the consultation record, with the supporting
   answer quoted in your report.
2. One attribution convention chosen, justified, and applied uniformly at all five
   sites, OR a reasoned recommendation to leave them as they are.
3. If you added a bibliography entry, no existing entry in references.bib was
   touched, and the new key does not collide.
4. The em-dash and Japanese-script checks pass over every file you touched.
5. A short report: the five claims, their support, the convention chosen, and the
   page cost.
6. You have committed and pushed D:\repositories\msc-thesis (this updates
   Overleaf), and the engine repository if you changed anything there.
```

**Checkpoint before Work package 6.** Read the convention the review pass chose at one of
the Chapter 4 sites and decide whether you are happy with it appearing five
times. This is the one item in the campaign that is a matter of taste as much as
of calibration, so overrule it now if you want something different: Work package 6 will
lock the text.

---

### WORK PACKAGE 6 of 6: Reconcile the post-2026-08-21 material to its artifacts (finding G1)

```
I am finishing an MSc thesis and this is the closing audit of a claim-calibration
campaign. Five earlier review passes have just made targeted edits across the thesis.
Your task is to verify a block of material that has never been through a number
reconciliation, and to confirm that the campaign's own edits did not break
anything.

## The thesis

Title: "Time-Dependent Reliability Assessment of Levees against Backward Erosion
Piping in High-Gradient River Systems: A Case Study of the Tokachi River Basin in
Hokkaido, Japan" (TU Delft MSc, civil engineering).

LaTeX source: D:\repositories\msc-thesis  (a Git-synced Overleaf mirror; read
files from disk, never compile locally)
Model, analysis code, artifacts of record: D:\repositories\bep-reliability-engine

What the thesis does: at four confined cross-sections of the Tokachi right bank
it evaluates backward erosion piping under a time-dependent progression criterion
(Pol 2024) and under a steady-state one (Sellmeijer 2011) on one shared Monte
Carlo sample; conditions the result on the documented survival of the August 2016
typhoon sequence; and composes the fragility with overflow and fluvial scour into
an annual system failure probability under historical and +4 K climate ensembles.

## The gap you are closing

A full number-reconciliation pass over this thesis exists:
  D:\repositories\bep-reliability-engine\docs\thesis_number_reconciliation_2026-08-21.md
It traced 431 claim groups to persisted artifacts and is the model for the method
you should use here: read its section 2 (the verdict vocabulary EXACT / ARITH /
CITED / FLAG), its section 4 (internal-arithmetic checks), and its section 5 (the
per-chapter register).

That pass ran on 2026-08-21. One week later a supervisor-directed campaign added a
substantial new block of material to the thesis, and it has never been reconciled.
The new block is:

- The reliability-index re-expression of the RQ1 comparison. Every Delta-beta
  value in the thesis, its confidence intervals, and the statements about how
  Delta-beta behaves with stage. Source of record:
  D:\repositories\bep-reliability-engine\docs\rq1_beta_reexpression_2026-08-28.md
- The additive comparator ladder in reliability-index terms: the table labelled
  "tab: gap components beta" in mainmatter/6., and the waterfall figure beside it.
  Same source of record, section 4.
- The equal-head-convention comparison: the table labelled "tab: equal convention"
  in mainmatter/6., the subsection labelled "sec: The Two Criteria on One Head
  Convention", and every restatement of its retained-fraction range. Source of
  record:
  D:\repositories\bep-reliability-engine\docs\decisions\equal-head-convention-study.md
  and D:\repositories\bep-reliability-engine\docs\decisions\adr0051-equal-head-convention.json
  and D:\repositories\bep-reliability-engine\docs\decisions\0051-crack-resistance-factor-equal-head-convention.md
- Every restatement of the above in frontmatter/summary.tex, mainmatter/8.
  Discussion.tex and mainmatter/9. Conclusions and Recommendations.tex.
- The Chapter 6 standing-conditions register (label "tab: piping conditions
  register") and the Chapter 7 one (label "tab: system conditions register"),
  which were rebuilt in the same campaign.
- The Chapter 9 answers register (label "tab: answers register").

## What to do

1. Reconcile every number in that block to a persisted artifact or a report of
   record, using the verdict vocabulary of the 2026-08-21 pass. The traceability
   table at the end of rq1_beta_reexpression_2026-08-28.md names the HDF5 and JSON
   files behind each quantity. Do NOT re-run the engine unless a number cannot be
   settled any other way; if you conclude a re-run is needed, stop and tell me
   what you would run and why, and wait.

2. Run the internal-arithmetic checks that do not need an artifact, in the style
   of section 4 of the earlier pass. At minimum:
   - every Delta-beta equals beta_transient minus beta_static from the same row;
   - every Delta-beta confidence interval is the monotone image of the
     corresponding probability interval under beta = -Phi^{-1}(P_f);
   - the three additive ladder steps in "tab: gap components beta" sum exactly to
     the total in the same row;
   - every retained-fraction percentage equals the equal-convention Delta-beta
     divided by the as-published Delta-beta printed beside it, and you state which
     denominator each uses;
   - every B value equals the ratio of the two failure counts printed with it, at
     the stated sample size;
   - the two conditions registers state a condition count that matches their own
     row count.

3. Verify the campaign's own edits. Five earlier review passes in this campaign
   changed:
   - the reliability-index ordering claim and the "0.9 to at least 1.9" range
     (Summary, Chapters 6, 8, 9);
   - the equal-convention retained fraction and the two-readings claim (Summary,
     Chapters 6, 8, 9);
   - nine literature-anchored claims (Chapter 2, Chapter 5, Chapter 8, Appendices
     E and G);
   - nine interpretive claims (Summary, Chapters 1, 6, 8);
   - eleven internal inconsistencies (Chapter 1, 3, 4, 5, 6, 7, 8, Appendix H);
   - the attribution convention for five consultation-sourced claims (Chapter 4,
     Chapter 6, Appendix C, Appendix G).
   Read `git log` in D:\repositories\msc-thesis to see exactly what landed.
   Confirm for each that (a) the value it now states is the value the artifact
   carries, and (b) it does not contradict any other statement in the thesis.

4. Run the whole-document consistency gates:
   - every \label referenced by a \ref still exists, and no \label was duplicated;
   - no em dash in any form (neither the U+2014 character nor "---") in typeset
     .tex content, skipping "%" comment lines for the "---" form only and skipping
     the gitignored scratch/ directory;
   - no Japanese script (kanji, hiragana, katakana) in any .tex file, skipping "%"
     comment lines; references.bib is exempt and is not part of this check;
   - no range written with a hyphen or en dash where "X to Y" is required;
   - the appendix count stated in Chapter 1 matches the number report.tex inputs;
   - every headline number that appears in more than one chapter has the same
     value at every site. Build that list by grepping rather than from memory.

5. Write the result as a dated reconciliation record in
   D:\repositories\bep-reliability-engine\docs\, in the same form as
   thesis_number_reconciliation_2026-08-21.md: a verdict table, the
   internal-arithmetic checks, a per-chapter register, and an explicit statement
   of what the pass did NOT do. Name any residual that needs a ruling from me.

6. Fix anything you find that is wrong, subject to the constraints below. Report,
   do not fix, anything that would require re-running the engine or that turns on
   a judgment I have not already made.

## Constraints

- This work package authorises the multi-chapter edits described. Do not stop to ask for
  a plan; the standing "plan first" rule in the msc-thesis project rules is discharged by
  this work package.
- Read the current file state from disk. Do not work from memory of any version.
- Never invent a number. If a claim cannot be traced, record it as FLAG and tell
  me.
- Make the smallest edit that fixes a defect. Do not re-word prose that is
  correct, and do not start a page trim.
- Style rules, all hard: no em dashes in any form; ranges "X to Y"; no Japanese
  script in a .tex file; preserve every \label and citation key; XeLaTeX; do not
  compile.
- No thesis prose, no .tex and no .bib files may be created in the engine
  repository; the reconciliation record is a Markdown document of record and
  belongs in its docs/ directory.

## Done means

1. Every number in the post-2026-08-21 block carries a verdict against a named
   artifact, and the verdicts are written up in the dated record.
2. All six internal-arithmetic checks in step 2 have been run and their results
   recorded, pass or fail.
3. All five whole-document gates in step 4 pass, or the failures are listed with
   what is needed to close them.
4. Every defect found is either fixed or recorded as needing my ruling, with no
   third category.
5. You have written me a short report naming: what you reconciled, what you fixed,
   what still needs a ruling, and your judgment on whether the thesis's numeric
   claims are now internally consistent and traceable end to end.
6. You have committed and pushed both repositories: D:\repositories\msc-thesis
   (which updates Overleaf) and D:\repositories\bep-reliability-engine.
```

**Final checkpoint.** Read the dated reconciliation record the review pass wrote.
Anything it lists as needing a ruling is yours to settle. Then compile in
Overleaf, confirm zero undefined references, and check the page count against
your 115-page ceiling: Work packages 4 and 5 add a small amount of material (one
register row, one appendix entry, an attribution convention at five sites) and
Work package 3 was constrained to be length-neutral or shorter, so the net should be
near zero, but it is worth a look.

---

## 4. Execution summary

| Order | Work package | Findings | Chapters touched | Why here |
|---|---|---|---|---|
| 1 | RQ1 headline register | B1, B2, C1, C2 | Summary, 6, 8, 9 | The most clearly wrong claims, and the ones every later review pass would otherwise have to work around. They also share paragraphs, so they must move together. |
| 2 | Literature | D1 to D9 | 2, 5, 8, App E, App G | Independent of 1. Placed before 3 because D2 may supply a published corroboration that changes how E1's replacement sentence should be written. |
| 3 | Interpretive calibration | E1 to E9 | Summary, 1, 6, 8 | Depends on 1 (the Summary paragraph 3 wording) and on 2 (D2). This is the review pass whose output you most need to read as prose. |
| 4 | Internal consistency | A1 to A11 | 1, 3, 4, 5, 6, 7, 8, App H | Mechanical and mostly independent; placed after the three wording review passes so it grepping-verifies text that has stopped moving. |
| 5 | Attribution convention | F1, F2 | 4, 6, App C, App G, possibly references.bib | Small, isolated, and a matter of taste; placed late so it is the last thing to change the text before the audit. |
| 6 | Reconciliation of the new block | G1, plus verification of 1 to 5 | whole document | Must run last: it audits everything the campaign landed. |

**One conflict you should know about.** The engine repository's own guidance
carries a standing rule that `msc-thesis` is never pushed from a review pass, because
it is an Overleaf mirror you own. Your instruction for this campaign is that each
session commits and pushes. The work packages follow your instruction and say so
explicitly. Both repositories are currently in sync with their remotes, and the
recent history shows earlier campaigns did push, so this should be uneventful,
but if you would rather review diffs in Overleaf before they land, strike the
push clause from the "Done means" block of each work package and push them yourself
between checkpoints.
