# Literature-carried claim calibration: the nine items of the D-series

Date: 2026-08-29. Status: evidence record. No engine default changed, no engine code
touched. Seven thesis passages edited; the edits are listed in section 12.

## 1. Scope and why this document exists

The number-reconciliation pass of 2026-08-21
(`docs/thesis_number_reconciliation_2026-08-21.md`) traced 431 claim groups in the thesis
to computed artifacts and explicitly did **not** verify the 58 values carried by a
literature citation. This pass verified nine of those, chosen because each carries an
argument rather than decoration. Each item below records what the source actually says,
verbatim and with a page or line locator, so the check does not have to be repeated.

Two items closed **open flags** left by the 2026-08-21 pass: the Abashiri duration
(section 8 here, its section 3.2) and the conductivity "factor of about 2.9"
(section 9 here, its section 3.1).

## 2. D1: the Pol reduction range is 5 to more than 10^6, not 10 to 10^6

Source: `docs/references/pol_sie_2024.pdf` (Pol, Kanning, Jonkman, Kok, *Structure and
Infrastructure Engineering*, 2024).

**Abstract, p. 2, verbatim:**

> The findings show that, particularly in coastal areas, incorporating time-dependence
> significantly reduces the computed failure probability. Reductions vary widely, ranging
> from a factor of 5 to more than 10^6, depending on flood duration and levee properties.

**Section 3.4 "Influence of levee characteristics", p. 14, verbatim:**

> The effect of time-dependent pipe growth is large in the coastal levee cases; it ranges
> from Ftd ~ 5 for coarse sand with a thin blanket and short seepage length up to
> Ftd > 10^6 for large seepage lengths and fine sand. Although effects are much smaller
> for the river levee cases, they can still be considerable (factor of 10-100) for
> particular situations such as fine sand combined with a large seepage length. In other
> situations with river levees (coarse sand and thin blanket) effects are limited
> (Ftd < 5) and the current assumption of instantaneous failure can be considered
> realistic.

Three corrections follow. The lower end is **5**, not 10. The 5 to 10^6 span is the
**coastal** range specifically, and within it the span is set by **configuration**
(seepage length, grain size, blanket thickness), not by the coastal load alone: the
factor-5 end is coarse sand under a thin blanket on a short path and the 10^6 end is fine
sand on a long one. The **river** cases span a separate and much smaller range, 10 to 100
at their worst and below 5 for coarse sand under a thin blanket.

The section 3.4 parameter grid, p. 13: L = 50, 100, 150 m; d70 = 200 and 400 um;
k_aq = 1e-4 and 4e-4 m/s (coupled to d70); D_bl = 1 and 5 m; N_s = 1e4; no flood fighting,
no strength recovery. F_td is defined for the year 2050 (their Eq. 18), so it is a
**cumulative-to-2050** probability ratio, not a per-event conditional ratio at a stage.
That is a different estimand from this thesis's duration factor, and any comparison
between the two must say so.

## 3. D2: the corroboration the source supports, and its exact limits

The last sentence quoted in section 2 is the one that matches the Tokachi configuration:
a coarse gravel aquifer under a 0.45 to 0.85 m cohesive blanket, on river loading. The
source's expectation for that class is **F_td < 5**, with the conventional instantaneous
assumption judged realistic.

The thesis's own measured pure-duration factor is 1 to about 6 wherever the failure counts
support the statement (Chapter 6, `tab: gap components`, last column). The two agree in
magnitude.

**What this is not.** It is an independent published expectation matching a measurement,
not a validation. The estimands differ (per-event conditional ratio at a stage here;
cumulative-to-2050 ratio there), the sections differ, and the source's blanket thicknesses
(1 and 5 m) bracket the Tokachi 0.45 to 0.85 m from above only. One sentence was added at
one site, in Chapter 8 section 1, and nowhere else.

## 4. D3: what the nine-month recovery test actually showed

Source: `docs/references/pol_thesis_2022.pdf`, section 4.4.4 "Additional experiment on
strength recovery" (chapter 4, pp. 88-89 of the printed thesis).

**Chapter 4 abstract, verbatim:**

> The recovery test shows partial strength recovery after nine months of rest: the erosion
> process had to start all over again, albeit with 20% lower critical head and 140% higher
> progression rate.

**Section 4.4.4, verbatim:**

> The critical head difference between the sensor furthest upstream in the aquifer (nr. 12)
> and sensor furthest downstream (nr. 2) decreased from 1.15 m in 2018 to 0.90 m in 2019,
> so up to 80% of strength was recovered.

> It is interesting that the progression in the recovery test develops again from
> downstream to upstream, i.e. it starts over again albeit quicker and with a lower
> critical head. In case of a hydraulic shortcut being present, instead of this gradual
> development one expects a quick response of the pressures at the upstream side, which is
> not observed.

> Together, these observations show that there was partial recovery over a period of nine
> months: the levee was weaker than originally but not as weak as expected with a hydraulic
> shortcut.

**Chapter 4 conclusions, verbatim:**

> The recovery experiment, in which the levee was reloaded after 9 months, showed partial
> recovery of the pipe strength. The erosion process started all over again, albeit with
> lower critical head and higher progression rate. This is a promising finding for concerns
> regarding cumulative degradation in the long term.

The two numbers the thesis quotes are exact. The inference drawn from them was not. The
experiment shows the **pipe geometry did not survive** the nine-month interval (erosion
restarted from the downstream exit; the absence of a fast upstream pressure response is the
explicit evidence that no open shortcut remained) while the **resistance was permanently
reduced**. The engine's `r_l = 0` does the opposite pairing: it carries the pipe **length**
forward and holds the sampled resistance fixed within a realization
(`mainmatter/4. Methodology.tex`, `sec: Compound Event Modelling: Cumulative Memory and
Irreversible Pipe Growth`: "The irreversibility is exclusively geometric"). Chapter 2's
"consequently" therefore did not follow from the cited experiment.

The justification that does carry the weight, and which the Chapter 2 rewrite now states:
the inter-peak interval in a consecutive-typhoon sequence is hours to days, not nine
months, so no closure mechanism of the kind the test measured has time to act. The
Gounokawa observation of Chapter 5 (`subsec: Transfer to the Tokachi Sections`) points the
same way, to memory held in the blanket rather than in an open pipe.

The source also names the mechanisms it thinks produced the closure, which is why nine
months is not transferable to hours: settlement of a levee only one year old under a thin
clay cover, and, in the field, traffic loads, siltation, biological activity and
temperature and groundwater fluctuation.

## 5. D4: the Lane (1935) case count is NOT established. No edit made.

Lane, E. W., "Security from under-seepage: masonry dams on earth foundations",
*Transactions ASCE* 100 (1935), pp. 1235-1272; discussion closure pp. 1334-1351. Not in
`docs/references/`.

The primary source could not be obtained. The ASCE Library copy is paywalled
(HTTP 403 without a subscription); the Internet Archive holdings of Transactions vol. 100
that carry the paper body are lending-restricted (HTTP 401 on the djvu text); the freely
downloadable `transactionsofam100112amer` item is an **index** volume only, which confirms
the citation (`"Security from Under-Seepage - Masonry Dams on Earth Foundations," E. W.
Lane, 100:1235 (1935)`) but carries no page of the paper.

The reliable secondary literature **disagrees**, and the disagreement is not about
rounding:

| Count | Source | Verbatim |
|---|---|---|
| 278 case histories | US Army Corps of Engineers, ERDC/GSL TN-14-3 (Robbins, Nov 2014), p. 3 | "In order to revise Bligh's rule, Lane reviewed 278 dam case histories, some of which failed due to piping." |
| 247 dams, 21 failed | Stark et al., "Predicting underseepage of masonry dams", p. 1 | "In 1934, E.W. Lane published 'Security from Under-Seepage: Masonry Dams on Earth Foundations.' He collected and analyzed information concerning 247 masonry dams founded on soil. Twenty-one of these dams failed." |
| 278 reviewed, 251 usable, 21 failed | secondary accounts in the Robbins and van Beek historical-review lineage | "Of the 278 dams reviewed, Lane considered 251 of them to have sufficient data to compute the creep ratios. Of the remaining 251 dams, only 21 of the dams had failed." |

The three are reconcilable in principle (a set reviewed, a smaller subset with computable
creep ratios, a failure count inside it), but no source read here states the reconciliation
authoritatively, and the two candidate "reviewed" totals, 278 and 247, are not the same
number. Note that the Stark team entered Lane's own tabulated data into a database, so
their 247 is derived from Lane's tables rather than repeated from a review.

**Status: the thesis text is left unchanged at "278 cases."** It is directly supported by a
USACE technical note, which is a citable source, and no number was substituted for it. The
options for the owner:

1. Leave it. Defensible, supported by ERDC/GSL TN-14-3, but the count Lane actually
   *analysed* may be smaller than the count he *reviewed*, and the thesis says "on the
   evidence of."
2. Obtain Lane (1935) through the TU Delft ASCE subscription and settle it from the
   primary. This is the only way to close it.
3. Reword to avoid the count, for example "on the evidence of a large body of
   masonry-dam case histories". Loses nothing the argument needs, since the sentence exists
   only to say the creep ratio is empirical.

## 6. D5: the i_c symbol collision at the 0.5 screening value

The thesis defines `i_c = gamma'_bl / gamma_w` as the Terzaghi critical heave gradient,
which for the study blanket is about 0.70. The 0.5 in the Chapter 2 sentence is the
Japanese allowable-gradient screening criterion, a different object that happens to be
written `Ic` in the OYO source. The evidence is already recorded verbatim in
`docs/oyo_1998_framing_review_2026-08-24.md` sections 3.1 and 3.3; the load-bearing
quotations are the criterion statement in report section 6-1 and the mechanism statement in
section 7-2, which uses the phrase "the critical gradient Ic = 0.5".

Chapter 2 is corrected to name the value as a national screening threshold and to drop the
symbol. **One further site was found and NOT edited, because it lies outside the approved
list:** `mainmatter/3. Study Area, Geological Setting, and Data.tex`, in the paragraph
beginning "A formal seepage and slope safety evaluation", writes "fail the local
exit-gradient check against $i_c \geq 0.5$". That is the same collision. The caption of
`tab:oyo_1998` two paragraphs earlier writes it correctly as "$i \geq 0.5$", and so does
the guidance sentence that follows ("absent, the local gradient $i < 0.5$"). Flagged for an
owner decision.

## 7. D6: the 15 per cent gravel threshold belongs to Fukuoka, not to PWRI 4300

### 7.1 What Fukuoka (2019) says

Source: `docs/references/2019-suiko-fukuoka.pdf`, p. 5, section (2) "検討条件". Verbatim:

> 礫分含有率が15%以上の堤防では浸透破壊危険性が極めて小さいことが，大型堤防模型実験に
> より確認されている9)．よって，図-7 に示すように礫分含有率の堤体内平均値が15%以上で，
> 平均透水係数の大きい左岸32.6～37k，右岸23～25k，31～33kの堤防は，堤防脆弱性指標t*の値
> が大きく算定されても浸透破壊の危険性が低く，検討対象から除外した．

Translation: "It has been confirmed by large-scale levee model experiments that levees with
a gravel content of 15 % or more have an extremely small risk of seepage failure [ref. 9].
Accordingly, as shown in Fig. 7, the levees at left bank 32.6 to 37 km and right bank 23 to
25 km and 31 to 33 km, whose in-embankment **average** gravel content is 15 % or more and
whose average hydraulic conductivity is large, were excluded from the analysis, because
their risk of seepage failure is low even where a large value of the levee vulnerability
index t* is computed."

His reference 9 is: 独立行政法人土木研究所 地質・地盤研究グループ土質・振動チーム,
「浸透に起因する河川堤防ののり尻からの進行性破壊現象に関する実験」, 土木研究所資料第4300号,
2015. That is PWRI Technical Note No. 4300, "Experiments on the progressive failure
phenomenon from the landside toe of river levees caused by seepage", Soil Mechanics and
Dynamics Team, Geology and Geotechnical Engineering Research Group, February 2015.

So the threshold **is** stated as "15 % or more" (15%以上), and the exclusion criterion
**is** stated on the in-embankment **average** (堤体内平均値). Chapter 2's "excludes
cross-sections whose embankment gravel content averages 15 per cent or more" is exactly
right and was left unchanged. Fukuoka's exclusion also carries a second conjunct, "and
whose average hydraulic conductivity is large", which the thesis does not state; that is a
simplification, not an error, because the gravel is what produces the conductivity.

### 7.2 What PWRI 4300 actually says

PWRI 4300 was located and read (295 pages; retrieved from
`https://www.pwri.go.jp/team/smd/pdf/report4300.pdf`, 58 MB, not committed to this
repository). It contains **no 15 per cent gravel threshold anywhere**. Its own summary
(section 4 まとめ, printed p. 171) states, verbatim:

> また、礫分を10％以上含み60%粒径の大きいケースでは、動水勾配の最大値が0.5 程度の今回の
> 実験の範囲においては進行性破壊が生じなかった。

Translation: "Furthermore, in the cases containing **10 % or more** gravel and having a
large 60 % grain size, progressive failure did not occur within the range of this
experiment, in which the maximum hydraulic gradient was about 0.5."

Two further statements bound the reading. From the medium-scale series (printed p. 90):

> 礫分含有率が少ない堤体材料で、崩壊が発生しているケースが多く確認された。また、礫分含
> 有率が33%程度でも崩壊が発生することが確認された。

"Collapse was confirmed in many cases with embankment materials of low gravel content. It
was also confirmed that collapse occurs even at a gravel content of about 33 %."

And from the small-scale series (printed p. 170):

> 進行性破壊が生じなかったCase10、13 は、礫分含有率が69.1%と多くの礫を含む材料であった。

"Cases 10 and 13, in which progressive failure did not occur, were materials containing a
great deal of gravel, at a gravel content of 69.1 %."

Three consequences. First, the 15 % figure is **Fukuoka's**, and PWRI 4300 does not carry
it. Second, PWRI 4300's own gravel threshold is 10 % **jointly with** a coarse D60, not
gravel content alone, which is why its own tests collapse at 33 % gravel and survive at
69.1 %. Third, PWRI 4300's mechanism is 進行性破壊, progressive failure of the landside
**slope** from the toe under seepage, not backward erosion piping in a confined
foundation; the thesis already states the scope restriction ("it applies to the embankment
body rather than to a confined foundation beneath a cohesive blanket") and that statement
is unaffected.

Appendix G was therefore corrected: the "exceeds 15 per cent" attributed to
`pwri_4300_2015` is replaced by a qualitative statement that source does support, and the
15 per cent is moved onto the screening and index exclusion where Fukuoka puts it, in the
same "15 per cent or more" form Chapter 2 uses. The two sites now agree.

## 8. D7: the Abashiri 234-hour duration is VERIFIED. No edit made.

The 2026-08-21 reconciliation flagged this (its section 3.2) because Chapter 8 uses it as a
quantitative counterweight to a computed result. It is now verified against the cited
source, verbatim.

Source: `docs/references/tokachi_river_basin/ctll1r0000001cmh.pdf`, **page 4 of 4**. Page 1
identifies the document: 堤防詳細点検結果情報図 (Levee Detailed-Inspection Result
Information Maps), 帯広開発建設部 (Obihiro Development and Construction Department),
results as of 平成20年3月 (March 2008). That is exactly the bibliography entry
`obihiro_levee_inspection_2008`.

Page 4, headed 「（参考）堤防質的整備の実施事例（網走川）」, verbatim:

> 網走川住吉・本郷地区では、平成１３年９月の洪水において警戒水位を上回る水位が２３４時間
> 継続し堤防決壊の危険が生じたため、避難勧告が出されたほか、堤体からの漏水が発生し水防活
> 動が実施された（月の輪工７箇所、経過観測１０箇所実施）。平成１４年から堤防質的整備を実
> 施している。
> ○目的： 堤内側基礎地盤のパイピング破壊及び裏のりすべりに対する安全性の確保
> ○対策工法： 断面拡大工法（裏のり1：3.0、表のり1：5.0） ドレーン工法 ... ﾄﾞﾚｰﾝ工法(L=6.5m)

Translation: "In the Sumiyoshi and Hongo districts of the Abashiri River, during the flood
of September 2001 a water level exceeding the warning level continued for **234 hours**, so
that a danger of levee breach arose; an evacuation advisory was issued, leakage from the
embankment body occurred, and flood-fighting activities were carried out (ring-levee works
at 7 locations, monitoring at 10 locations). Levee quality-improvement works have been
carried out since 2002. Purpose: securing safety against piping failure of the landside
foundation ground and against landside slope sliding. Method: section enlargement (landside
1:3.0, riverside 1:5.0) and the drain method (L = 6.5 m)."

Every element of the thesis's Appendix G passage is present in that paragraph: the two
districts, September 2001, 234 continuous hours above the warning level, the recognized
breach risk, the evacuation advisory, the embankment leakage, ring-levee works at seven
locations with monitoring at ten more, works from 2002, the stated purpose naming landside
foundation piping and landside slope sliding, the 1:3.0 and 1:5.0 slopes, and the 6.5 m
drain. Chapter 2 and Chapter 8 quote the same 234 hours from the same paragraph. "Some ten
days" is 9.75 days.

One reading note: the source says a danger of breach **arose**, not that the levee
breached. The thesis's "The levee did not breach" is supported by that plus the recorded
2002 quality-improvement works on the standing embankment, and no breach appears in the
record.

**Status: verified, text left unchanged. The 2026-08-21 flag is closed.** Chapter 8 may
continue to use the duration as a quantitative counterweight.

Note for future readers: this document is an Obihiro-jurisdiction inspection report, so an
Abashiri River case appears in it only as an explicitly labelled reference example
(参考, "for reference") of quality-improvement practice. That is why searching the
Obihiro reach material for it does not find it; it is on page 4, after three pages on the
lower Tokachi and Satsunai.

## 9. D8: the conductivity prior spread is 2.5, not 2.9

The prior is lognormal with `CoV(k_aq) = 0.50`, hence
`sigma_ln = sqrt(ln(1 + 0.50^2)) = sqrt(ln 1.25) = 0.472381`. The three constructions a
reader could mean:

| Construction | Value |
|---|---|
| P97.5 / median = `exp(1.96 * sigma_ln)` | **2.524** |
| P97.5 / P2.5 = `exp(2 * 1.96 * sigma_ln)` | 6.371 |
| tightest symmetric mean-relative factor containing 95 % | 2.589 |

None is 2.9, and no artifact in this repository carries 2.9. The sentence claims "the
central 95 per cent ... within a factor of", which is a statement about a band around a
central value, so the matching construction is the first: the central 95 per cent lies
within a factor of 2.5 either side of the median. Both sites are corrected to 2.5, and the
appendix now states the construction (`exp(1.96 sigma_ln) = 2.52` at
`sigma_ln = 0.472`) and gives the full percentile span, 6.4, so the figure is reproducible
either way.

**Flag for the owner, not acted on.** Both passages compare this figure against Japanese
guidance characterising ordinary measured scatter as "a factor of several to about ten"
(`pwri_2014`), and then conclude the adopted prior is "materially narrower than this". The
guidance figure is a **span**; 2.5 is a **half-band**. The comparable quantity is the span,
6.4, which sits inside "several to about ten" rather than materially below it. The
conclusion as written is therefore drawn between two different constructions. It is left
alone here because correcting it changes an argument, not a number.

## 10. D9: the IJkdijk deviations, and what the 13 per cent band actually is

Source: `docs/references/sellmeijer_2011.pdf`.

**The 25 per cent is the source's own reported deviation for IJkdijk test 2.** Section 8,
p. 1153, verbatim:

> The IJkdijk tests 1 and 3 are performed with fine sand (d70 = 180 um). The predictions by
> formula [6] of the critical head agree quite well with the outcome of the tests. However,
> the predictions for test 2 with coarse sand (d70 = 260 um), deviates from the experiment
> by 25%.

Section 9 (conclusions), p. 1153, verbatim:

> The new rule appears to predict well the outcome of the large-scale IJkdijk tests, when
> the subsoil is composed by fine sand. For coarse sand only one test is carried out, where
> a 25% difference is observed between prediction and test.

Confirmed. Test 2 is the coarse-sand test and is the widest of the three.

**Chapter 5's juxtaposition was wrong and is corrected.** It named "the widest" and then
illustrated with test 1 (2.07 m against 2.30 m, 10 per cent), which is not the widest.
Appendix G had all three right: test 1 2.07 against 2.30 (10 per cent), test 3 2.07 against
2.10 (2 per cent), test 2 2.01 against 1.75 (15 per cent). Chapter 5 now illustrates with
test 2.

**The 13 per cent acceptance band: set attribution correct, label not.** Appendix G calls
it "the reported regression scatter of the adapted piping rule, approximately 13 per cent"
and says it is "reported for the small and medium-scale regression set". The set
attribution is right. The source, p. 1148, verbatim:

> This difference of 13.4% is marked by the green line in Figure 2. It indicates the
> imperfection of the model for the small scale tests.

> However, a medium-scale analysis can be simulated by correcting the small-scale results
> by the scale factor in formula [6]. Then, a similar 13% drift is observed as in the case
> of the small-scale tests.

Figure 2's footnote defines the quantity: "The drift is defined as Hcmva/Hcexp - 1." So the
13.4 per cent is a systematic **drift**, the constant offset between the physically based
formula [6] and the multivariate-regression postdictions, not a scatter. Sellmeijer does
use "scatter" elsewhere ("the scatter of the measurements due to the test performances";
"the influence of the parameters U and angularity is of the order of the scatter in the
tests"), but never attached to the 13 per cent figure.

**Flag for the owner, not acted on**, because Appendix G's wording lies outside the
approved edit list: "regression scatter" should read "regression drift", a one-word change.
The band's provenance as a borrowed tolerance, and the fact that the source gives no
numeric tolerance for the large-scale tests, are already stated correctly there.

## 11. Style checks

Both hard checks were re-run over every `.tex` file in `d:\repositories\msc-thesis` after
the edits and both return clean: the em-dash scan (literal U+2014 and the `---` ligature,
excluding `%` comment lines for the ligature form and the gitignored `scratch/`) returns
`EMDASH CLEAN`, and the Japanese-script scan (CJK ideographs, hiragana, katakana, excluding
`%` comment lines) returns `CJK CLEAN`. Brace balance and math-mode `$` parity were checked
on all five edited files and are unchanged. No `.tex` or `.bib` file was created in this
repository, and no Japanese script was carried into the thesis.

## 12. The edits made

| Item | File | Change |
|---|---|---|
| D1 | `mainmatter/2. Theoretical and Empirical Foundations.tex` | "a factor of 10 to $10^6$" becomes "from a factor of 5 ... to more than $10^6$", with the configuration split named |
| D2 | `mainmatter/8. Discussion.tex`, section 8.1 | one sentence added after the pure-duration bound, citing `pol_sie_2024` for the river/coarse-sand/thin-blanket expectation |
| D3 | `mainmatter/2. Theoretical and Empirical Foundations.tex` | the recovery-experiment inference rewritten; the nine-month test now supports resistance loss, and the hours-to-days interval carries `r_l = 0` |
| D4 | none | count not established; see section 5 |
| D5 | `mainmatter/2. Theoretical and Empirical Foundations.tex` | `$i_c \geq 0.5$` becomes "at or above the national screening value of 0.5" |
| D6 | `appendix/appendix-g.tex` | the 15 per cent moved off `pwri_4300_2015` and onto the screening and index exclusion, in Chapter 2's "15 per cent or more" form |
| D7 | none | verified; see section 8 |
| D8 | `mainmatter/8. Discussion.tex`, `appendix/appendix-e.tex` | 2.9 becomes 2.5 at both sites; the appendix now states the construction and the full span |
| D9 | `mainmatter/5. Verification, Validation, and Global Sensitivity Analysis.tex` | the illustrating example changed from test 1 to test 2, which is the widest |

Four items are flagged for an owner ruling and were deliberately not edited: the Lane
count (section 5), the Chapter 3 `$i_c \geq 0.5$` twin (section 6), the half-band versus
span comparison in the conductivity passages (section 9), and Appendix G's "regression
scatter" for what the source calls a drift (section 10).
