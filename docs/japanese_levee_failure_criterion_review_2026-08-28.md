# The Japanese levee failure criterion, and the "safe below HWL" claim

Date: 2026-08-28. Status: evidence record; the edit plan in Sections 5 and 7 was
approved and applied the same day. No engine default changed. See Section 11 for
what landed.

## 1. The question, and the verdict

The thesis asserts, in three places including the first sentence of the Summary, that
under conventional Japanese practice a levee counts as safe as long as the river stays
below the Planned High Water Level (HWL). The author's Japanese professor states that
this is false.

**The professor is right.** The claim is wrong in three separate ways, and the third is
a flat contradiction of the governing national standard, in terms.

1. **Polarity.** The binary HWL rule that genuinely exists in Japanese practice is a
   *failure* condition, not a safety condition. In flood-hazard analysis the inundation
   onset stage is, in principle, the HWL, and a breach is *assumed* once the
   corresponding discharge arrives. That convention is deliberately conservative. The
   thesis states its mirror image and presents it as permissive, so it inverts the
   direction of the conservatism it sets out to criticise.
2. **Category.** Below the HWL, safety is a *requirement to be demonstrated*, not a
   verdict conferred by the stage. A transient seepage verification with explicit
   allowable values is mandatory across the whole directly managed network, and
   **40.8 per cent of that network fails it.**
3. **Direct contradiction.** The current Technical Standards state that a levee built to
   the standard "does not possess absolute safety against floods at or below the planned
   high water level", and the reason they give is **flood duration**. The 2002 Design
   Guideline says the same in the past tense: structural distress under floods at or
   below the HWL has occurred in large numbers, and present levees cannot be said to
   have sufficient reliability.

The correction is not a retreat. Point 3 is the strongest possible warrant for this
thesis: the Japanese standard itself names loading duration as the reason that
below-HWL safety is not absolute, and offers no limit state capable of expressing it.
Section 6 sets out how to convert the correction into a stronger motivation.

Note also that Chapter 2 Section "Levee Safety Verification Practice" (Appendix G) and
Chapter 2 lines 287 to 293 **already carry an accurate account**. The defect is confined
to the three headline framings, which currently contradict the thesis's own appendix.

## 2. What Japanese practice actually is

The HWL (計画高水位) does four distinct jobs. The thesis collapses them into one.

### J1. Channel planning: the HWL is a conveyance stage

The HWL is the stage at which the design high-water discharge (計画高水流量) is conveyed
by the improved channel. The crest is then HWL plus a freeboard (余裕高) fixed by the
Structural Ordinance as a function of design discharge.

> 堤防は計画高水流量以下の流水を越流させないよう設けるべきものであり [...] 洪水時及び
> 高潮時等における風浪、うねり及び跳水等による一時的な水位上昇への対応、巡視、水防活動
> を実施する場合の安全の確保並びに流木等流下物への対応等その他の種々の要素をカバーする
> ために、構造令で定める値を構造上の余裕として加える

(河川砂防技術基準 設計編 技術資料 第1章第2節 2.5)

The freeboard covers wind waves, swell, hydraulic jump, patrol and flood-fighting safety,
and floating debris. **It is explicitly not a water-retaining allowance.** This is why
the warning system's 氾濫危険水位 (Level 4 evacuation trigger) is set at crest minus
freeboard, that is, at about the HWL for a levee built to plan.

### J2. Structural requirement: the HWL is the design load

Cabinet Order on Structural Standards for River Administration Facilities
(河川管理施設等構造令), Article 18:

> 堤防は、護岸、水制その他これらに類する施設と一体として、計画高水位以下の水位の流水の
> 通常の作用に対して安全な構造とするものとする

"A levee shall, together with revetments, groynes and similar facilities, be of a
structure safe against the ordinary action of flowing water at water levels **at or
below** the planned high water level."

The HWL is therefore the *upper bound of the loading the levee is required to survive*.
It is not a verdict, and nothing in it says the levee is safe at any particular stage.

### J3. Verification: safety below the HWL is demonstrated, not assumed

Since the 1997 revision of the Technical Standards and the 2002 河川堤防設計指針
(MLIT River Bureau Flood Control Division, 12 July 2002, last revised 23 March 2007),
safety at that load must be shown. Section 5(2)1) of the Design Guideline:

- **照査外水位 (verification stage)** = 計画高水位, the HWL
- **照査降雨 (verification rainfall)** = 計画規模の洪水時の降雨, the design-scale flood rainfall
- **Method** = 非定常浸透流計算及び円弧滑り安定計算, unsteady seepage-flow computation
  plus circular-slip stability analysis

Allowable values:

| Check | Criterion |
|---|---|
| Landside slope sliding | `Fs >= 1.2 * a1 * a2` (a1 = 1.2 / 1.1 / 1.0 by construction-history complexity; a2 = 1.1 with damage history or a 要注意地形, else 1.0) |
| Riverside slope sliding | `Fs >= 1.0` |
| Foundation piping, no blanket | `i < 0.5` (max local hydraulic gradient near the landside toe) |
| Foundation piping, blanket present | `G/W > 1` (blanket weight over uplift force on its base) |

The current Technical Standards carry the same structure. Table 2-1 of 設計編 技術資料
第1章第2節 gives, for the flood condition, seepage resistance
(耐浸透性能: すべり、パイピング) with the river stage set as
**「計画降雨波形に基づき設定した水位波形」**, a stage hydrograph derived from the design
rainfall waveform, not a static level. Section 2.7.2(4) makes setting allowable values
against both sliding and piping a 標準-level (standard) requirement, and states:

> 照査の結果、安全性能を満足しない場合には、強化工法の検討を行うことを基本とする

The verification of sliding and piping is performed at the instant the high-water
duration ends (PWRI 2013/2014, Section 7.2), not at the hydrograph peak.

**The outcome, nationally.** PWRI Figure 6.3.1, 治水課調べ, January 2011, over the
roughly 10,000 km of directly managed levee:

| Verdict | Share |
|---|---|
| All checks OK | 59.2 % |
| All NG | 1.5 % |
| Landside slope and piping NG | 9.5 % |
| Landside and riverside slope NG | 2.0 % |
| Riverside slope and piping NG | 0.3 % |
| Landside slope only NG | 13.1 % |
| **Piping only NG** | **13.8 %** |
| Riverside slope only NG | 0.5 % |

So **40.8 per cent of the national directly managed levee length is deficient in at least
one respect, and 25.1 per cent carries a deficiency involving piping.** A regional
cross-check: Kinki Regional Bureau, 263.9 km deficient of 734.7 km inspected, about 36 %.

A levee is therefore emphatically *not* deemed safe by virtue of the water being below
the HWL. Two fifths of the network is on record as not being safe there.

### J4. The standard's own disclaimer, and it names duration

河川砂防技術基準 設計編 技術資料 第1章第2節 2.2.1 機能:

> 堤防は、通常起こり得る現象である「計画高水位以下の水位の流水の通常の作用及び降雨による
> 浸透」に対して安全に造られるべきである。**但し、洪水は自然現象であるため、既往洪水による
> 被害の実態や河川の特性を踏まえた計画規模の洪水と比較して、継続時間が著しく長いもの等が
> 発生しないとは限らない。そのため、このような考え方に基づき造られた堤防が計画高水位以下の
> 洪水に対して絶対的な安全性を有するものではないことに留意すべきである。**

"A levee should be built to be safe against the normally occurring phenomenon of the
ordinary action of flowing water at levels at or below the planned high water level, and
of seepage from rainfall. However, because floods are natural phenomena, it cannot be
ruled out that floods occur whose duration is markedly longer than the design-scale
flood, judged against actual damage from past floods and the characteristics of the
river. **It should therefore be noted that a levee built on this basis does not possess
absolute safety against floods at or below the planned high water level.**"

The 2002 Design Guideline, Section 2(1), states the same fact from the damage record and
uses it as the reason the verification programme was introduced:

> 既往の被災事例をみても、計画高水位以下の洪水により漏水など構造上の課題となる現象が
> 数多く発生しており、現在の堤防が必ずしも防災構造物としての安全性について十分な信頼性を
> 有するとはいえない。

"Looking at past damage cases, phenomena constituting structural problems, such as
leakage, have occurred in large numbers under floods at or below the planned high water
level, and it cannot be said that present levees necessarily possess sufficient
reliability in their safety as disaster-prevention structures."

### J5. Where a binary HWL rule does exist, it is a failure rule

MLIT 洪水浸水想定区域図作成マニュアル（第4版）, July 2015, PDF revision 2017-10-06,
Section 2.4(1):

> 各断面に氾濫開始流量以上の流量が流下した時に破堤による氾濫が生じるものとする
>
> 氾濫開始水位は、**原則、計画高水位とする**

"It shall be assumed that breach-induced inundation occurs when a discharge at or above
the inundation-onset discharge passes each cross-section. The inundation-onset stage
shall in principle be the planned high water level."

The general rule for banked reaches is the current crest height minus the design
freeboard (the difference between the design crest and the HWL in the basic river plan),
capped at the HWL and floored at the landside ground level; where the current crest
matches the design crest this equals the HWL exactly. For unbanked reaches it is the
landside ground level. In every case the onset stage is at or below the HWL, never the
crest.

This is exactly the convention the Japanese-Dutch collaboration set out to replace, and
all three of its own statements say so:

- Uemura and Curran, WP2 2024, Section 1.1: "flood control planning in Japan, where
  calculations are traditionally based on a binary threshold: i.e. **a breach will occur
  if the water level exceeds the planned level**."
- Uemura et al., IAHS 2024, Section 1: "In Japan, the commonly used criterion for dike
  failure conditions is the Planned High Water Level (HWL) in flood control plans.
  However, actual dike failures can result from factors like overtopping, erosion, and
  seepage [...] Numerous cases have been reported where levees didn't breach despite
  water levels exceeding the HWL."
- Uemura PhD 2025, Section 4.1.1 (translated): "In flood analysis for the purpose of
  creating flood hazard maps, etc., a deterministic method is used in which the condition
  for levee failure is when the planned high water level (HWL) is reached [...] the
  inundation depth of the flood hazard map was evaluated by **setting the conditions for
  levee failure on the safer side**."

### J6. What the field record says

MLIT (2020), Technical Study Committee on River Levees after Typhoon No. 19 (Hagibis),
3rd meeting, Document 2:

- 142 breaches: overtopping 122 (86 %), erosion 12 (9 %), **seepage 2 (1 %)**, unknown 6 (4 %).
- 14 breaches on nationally managed rivers, 128 on prefecturally managed rivers.
- **Overtopping was confirmed at 72 nationally managed sites. 14 breached (19 %).
  58 did not (81 %).**

The 81 per cent figure disposes of a deterministic "overtopping implies failure" rule as
well, and Uemura's PhD cites it for exactly that purpose.

## 3. Where the thesis claim came from

The claim is a misreading of one sentence in Uemura's PhD, Section 4.1.1 (translated):

> "In terms of river planning, HWL is the range in which the safety of levees is
> guaranteed, but when assessing the risk of flooding in flood plains, it is necessary to
> evaluate the qualitative strength of these levees."

That sentence describes **J2**, the design *requirement*: the HWL bounds the range within
which the levee is *required* to be safe. The thesis converted a statement about the
guaranteed design range into a statement about the assessment verdict, and simultaneously
dropped the surrounding context, which is that in the *failure-condition* convention the
polarity is the opposite (J5) and that levees in fact survive well above the HWL (J6).

The HKV WP2 wording ("a breach will occur if the water level exceeds the planned level")
is unambiguous and was read backwards. So the recollection that the claim came from
Uemura and from the WP2 report is correct; the sources say the opposite of what the
thesis attributes to them, so the citations as they stand do not support the sentence.

## 4. Claim inventory: every site, with a verdict

Line numbers are against the working tree at commit `2d40fb4` (2026-08-28). Note that
`msc-thesis` is an Overleaf mirror and synced during this review; re-read before editing.

| # | Site | Text | Verdict |
|---|---|---|---|
| 1 | `frontmatter/summary.tex:4` s1 | "A Japanese levee is generally judged safe if the river stays below the Planned High Water Level." | **FALSE. Replace.** Highest visibility: first sentence of the document. |
| 2 | `mainmatter/1. Introduction.tex:9` s2 | "Under conventional practice a levee counts as ``safe'' as long as the river stays below the Planned High Water Level." | **FALSE. Replace.** |
| 3 | `mainmatter/1. Introduction.tex:9` s3 | "It can therefore pass as adequate while its residual failure risk goes unquantified." | Conclusion TRUE, warrant false. **Re-warrant.** |
| 4 | `mainmatter/2. Theoretical...tex:9` s3 | "A levee is judged adequate if the river water level remains below the planned high water level (HWL)." | **FALSE. Replace.** |
| 5 | `mainmatter/2. Theoretical...tex:9` s4 | "Where the water level surpasses the crest, overflow and subsequent failure are assumed to occur deterministically \parencite{uemura_iahs_2024}." | **INACCURATE and mis-cited. Replace.** The hazard convention assumes breach at the HWL, not the crest; Uemura's own model does not assume it (cumulative work on the slope decides); and 81 % of observed overtopping sites in 2019 did not breach. |
| 6 | `mainmatter/2. Theoretical...tex:9` last s | "Levee safety is thus treated as a threshold exceedance problem rather than as a probabilistic assessment..." | TRUE but imprecise. **Sharpen** to name the two distinct thresholds. |
| 7 | `mainmatter/1. Introduction.tex:26` | "a ``safe'' water-level reading could still precede a catastrophic breach" | Keep. **Re-anchor** the scare-quoted "safe" and support it with the standard's own disclaimer instead of an assertion against practice. |
| 8 | `mainmatter/1. Introduction.tex:24` | "Japanese verification applies sophisticated, time-varying seepage analysis to critical sections, yet ultimately judges safety against a single question: whether a local exit gradient has been exceeded..." | **TRUE and now fully verified.** Optional sharpening only. |
| 9 | `mainmatter/2. Theoretical...tex:9` s2 | "Levee safety is evaluated against a specified design external force, such as a rainfall event with an annual exceedance probability of 1/150" | **TRUE**, and now verifiable: the verification loading is the HWL stage together with the design-scale rainfall. Optional sharpening to name both components. |
| 10 | `mainmatter/2. Theoretical...tex:9` limitation 1 | "It does not quantify the residual probability of failure below the design threshold" | **TRUE. Keep**, and it can now be cited to the standard rather than asserted. |
| 11 | `mainmatter/2. Theoretical...tex:293` | "system-wide assessment remains dominated by overflow-based judgment, non-overflow mechanisms being treated as secondary where the flood level does not exceed the crest or the planned high water level" | TRUE for basin-scale probabilistic assessment. "the crest or the planned high water level" is loose. **Optional sharpening.** |
| 12 | `mainmatter/3. Study Area...tex:50` | "a loading Japanese practice treats as the limiting case" | **TRUE.** Optional sharpening to "the design load against which its verification is carried out". |
| 13 | `mainmatter/1. Introduction.tex:7` | "calibrated around isolated design events and deterministic safety criteria" | **TRUE. Keep.** |
| 14 | `mainmatter/1. Introduction.tex:9` s4 (BEP clause) | "Backward erosion piping (BEP) is not itself overlooked, since national practice requires every directly managed levee reach to be verified against it..." | **TRUE and already corrected** in commit `2d40fb4`. Keep. |
| 15 | `appendix/appendix-g.tex:17--120` | The full account of Japanese verification practice | **Already accurate.** Two additions recommended so it carries the evidence the openings will cite: the standard's own disclaimer (J4) and the hazard-mapping convention (J5). |

Checked and clean: Chapters 4 to 9 do not restate the claim. Chapter 8's "most directly
transferable conclusion of this thesis for Japanese practice" (line 463) concerns
peak-referenced assessment and is *reinforced*, not threatened, by the correction.

## 5. Proposed replacement wording

Candidates only. Style constraints observed: no em dashes, ranges written "X to Y", no
Japanese script, citation keys preserved, minimal surgical edits.

### 5.1 Summary, sentence 1 (site 1)

Replace:

> A Japanese levee is generally judged safe if the river stays below the Planned High
> Water Level.

with:

> A Japanese levee must be shown safe against river levels up to the Planned High Water
> Level, by a verification that checks slope stability, piping and heave against allowable
> values under a design stage hydrograph and the design rainfall.

Then in sentence 2, "checked within that judgment" becomes "checked within that
verification".

### 5.2 Introduction, paragraph 2 (sites 2 and 3)

Replace sentences 2 and 3 with:

> In that tradition the Planned High Water Level carries the judgment in two ways, neither
> of them probabilistic. It is the load a levee must be shown to withstand, through a
> national verification of slope stability, piping and heave against allowable values under
> a design stage hydrograph and the design rainfall \parencite{mlit_teibou_sekkei_2007,
> pwri_2014}; and in flood-hazard analysis it is the stage at which a breach is assumed to
> occur \parencite{mlit_shinsui_manual_2015, uemura_iahs_2024}. Neither use returns a
> failure probability, and the standard is explicit that the first confers no guarantee: a
> levee built on that basis is not absolutely safe against floods at or below the planned
> level, the reason given being that floods lasting markedly longer than the design event
> cannot be ruled out \parencite{mlit_design_standard_2025}.

Then the existing BEP sentence follows unchanged.

A shorter variant, if the paragraph is at its length limit:

> In that tradition the Planned High Water Level is the load a levee must be shown to
> withstand, not a stage below which it is presumed safe: national verification checks
> slope stability, piping and heave against allowable values under a design stage
> hydrograph and the design rainfall, and returns a pass or a fail rather than a
> probability \parencite{mlit_teibou_sekkei_2007, pwri_2014}. The standard adds that a
> levee built on that basis is not absolutely safe against floods at or below the planned
> level, because floods lasting markedly longer than the design event cannot be ruled out
> \parencite{mlit_design_standard_2025}.

### 5.3 Chapter 2, paragraph 1 (sites 4, 5, 6, and optionally 9)

Replace sentences 3 and 4 with:

> The planned high water level (HWL) is that design load: a levee must be shown safe
> against the ordinary action of flowing water at levels at or below it, by verifying
> slope stability, piping and heave against allowable values under a design stage
> hydrograph and the design rainfall \parencite{mlit_teibou_sekkei_2007}. Safety below the
> HWL is therefore demonstrated rather than presumed, and across the roughly 10{,}000~km of
> directly managed levee the demonstration fails on 40.8 per cent of the length
> \parencite{pwri_2014}. Where a binary rule on the HWL does operate it runs the other way:
> flood-hazard analysis assumes a breach once the river reaches that stage
> \parencite{mlit_shinsui_manual_2015, uemura_iahs_2024}, a deliberately conservative
> convention that the 2019 record contradicts at 81 per cent of the nationally managed
> sites where overtopping was actually observed \parencite{mlit_2020}.

And replace the closing sentence of the paragraph with:

> Levee safety is thus resolved by two threshold judgments at a single design stage, a
> structural pass or fail and an assumed breach, rather than as a probabilistic assessment
> of failure likelihood across the full distribution of hydraulic loading.

### 5.4 Introduction, line 26 (site 7)

Change "a ``safe'' water-level reading could still precede a catastrophic breach" to

> a water-level reading still inside the design range could precede a breach, a residual
> the standard itself acknowledges but does not quantify.

### 5.5 Appendix G additions (site 15)

Two sentences, to be added at the end of the paragraph beginning "Verification against
that mechanism is required rather than discretionary":

> The standard qualifies what the verification delivers. It states that a levee built on
> this basis does not possess absolute safety against floods at or below the planned high
> water level, and identifies floods of markedly longer duration than the design event as
> the reason \parencite{mlit_design_standard_2025}. The Design Guideline reaches the same
> conclusion from the damage record, noting that structural problems such as leakage have
> occurred in large numbers under floods at or below that level
> \parencite{mlit_teibou_sekkei_2007}.

And one sentence for the national-application paragraph, after the 40.8 per cent figure:

> The binary use of the HWL lies elsewhere, in hazard rather than structural assessment:
> flood-inundation mapping takes the inundation onset stage to be the planned high water
> level in principle, and assumes breach-induced inundation once the corresponding
> discharge arrives \parencite{mlit_shinsui_manual_2015}.

## 6. Why the correction strengthens the thesis

The present framing gives a Japanese examiner an easy target and, worse, is contradicted
by the thesis's own appendix. The corrected framing is an insider critique and is
materially stronger:

1. Japanese practice **already requires** a transient seepage verification against exactly
   this mechanism, at exactly these cross-sections (the study sections fall inside the
   scope of the 3 m blanket / 10 m levee-height screening waiver by a factor of three to
   seven, as Chapter 2 already establishes).
2. It **already names loading duration** as the reason that below-HWL safety is not
   absolute.
3. It **already fails a quarter of the national network** on piping.
4. What it does not have is a limit state that can represent duration. A threshold on an
   instantaneous gradient field cannot express a requirement about how long that field
   persists. That gap is the thesis's contribution, and Chapter 2 lines 287 to 293 already
   argue it, citing the 1970s leakage-prevention provision that lists "the duration of
   high water" among the factors to be considered.

Recommendation: promote the standard's own disclaimer (J4) into Chapter 1. It converts
the motivation from "practice presumes safety it has not established", which is false,
into "the standard names the exposure and has no instrument to measure it", which is true,
documented, and precisely what this thesis builds.

## 7. Bibliography additions required

Two new entries. Both are Japanese-language MLIT documents; per the 2026-07-29 exception,
`references.bib` may retain the original title alongside the romanised form.

```
@techreport{mlit_teibou_sekkei_2007,
  author      = {MLIT},
  title       = {Kasen Teibo Sekkei Shishin [河川堤防設計指針, Design Guideline for
                 River Levees]},
  institution = {{River Bureau, Ministry of Land, Infrastructure, Transport and
                 Tourism, Flood Control Division}},
  year        = {2002},
  month       = {7},
  url         = {https://www.mlit.go.jp/river/shishin_guideline/bousai/gijyutukaihatu/pdf/teibou_sekkei.pdf},
  langid      = {japanese},
  note        = {Issued 12 July 2002; last revised 23 March 2007. In Japanese.
                 Section 5(2) sets the verification stage, verification rainfall and
                 the allowable values for sliding and piping}
}

@techreport{mlit_shinsui_manual_2015,
  author      = {MLIT},
  title       = {Kozui Shinsui Sotei Kuiki Zu Sakusei Manyuaru (Dai-4-han)
                 [洪水浸水想定区域図作成マニュアル（第4版）, Manual for Preparing Flood
                 Inundation Hazard Area Maps, 4th edition]},
  institution = {{Water and Disaster Management Bureau, Ministry of Land,
                 Infrastructure, Transport and Tourism}},
  year        = {2015},
  month       = {7},
  url         = {https://www.mlit.go.jp/river/shishin_guideline/pdf/manual_kouzuishinsui_1710.pdf},
  langid      = {japanese},
  note        = {In Japanese. Section 2.4(1) sets the inundation onset stage at the
                 planned high water level in principle}
}
```

Existing keys reused without change: `mlit_design_standard_2025`, `pwri_2014`,
`jice_2019`, `jice_manual_2012`, `mlit_2020`, `uemura_iahs_2024`, `uemura_wp2_2024`,
`uemura_phd_2025`, `mlit_river_management_2009`.

One citation to consider correcting: `mlit_design_standard_2025` is noted as the
"Integrated version as of August 2025". The passage quoted in J4 was verified in the
2026 integrated version, at 設計編 技術資料 第1章第2節 2.2.1, and in the standalone
technical-annex PDF for the levee section. The text is identical between the two, so the
existing key can stand; the section pointer is what makes the citation checkable.

## 8. Sources read

Downloaded and read in full during this review (extracted to text with PyMuPDF; all four
MLIT and PWRI documents have working text layers):

| Source | What it settles |
|---|---|
| 河川砂防技術基準 設計編 技術資料 第1章第2節 堤防 (`1-2_g.pdf`, and the same text in `sekkei_all_2026.pdf` p. 14) | J1, J2, J3, **J4** |
| 河川堤防設計指針 (2002, rev. 2007) | J3 allowable values, **J4** damage record |
| PWRI 河川堤防の浸透に対する照査・設計のポイント, 2013 and 2014 editions (already in `docs/references/`) | J3 national inspection outcome, screening waiver, end-of-duration verification |
| JICE 浸透に係る重要水防箇所設定手順（案）, 2019 (already in `docs/references/`) | J3 criteria thresholds `G/W <= 1`, `i >= 0.5` as the deficient condition |
| 洪水浸水想定区域図作成マニュアル（第4版） | **J5** |
| MLIT 2020 Hagibis committee Document 2 | **J6** |
| Uemura et al. IAHS 2024; Uemura and Curran WP2 2024; Uemura and Rongen WP2 2022; Uemura PhD 2025 (translated) | Section 3, the provenance of the thesis claim |

Not usable: `docs/references/Literature/teibou_kouzou02.pdf`, the JICE 河川堤防の構造検討
の手引き (2012). Its body text extracts as mojibake (the embedded font carries a custom
encoding with no usable ToUnicode). Its content is fully covered by the PWRI companions
and the Technical Standards, so nothing in this review depends on it. If a verbatim quote
from it is ever needed, it will have to be read by page rendering.

## 9. The initiation-without-completion claim: resolved, and corrected

Chapter 2 stated that the national record attests initiation without completion,
citing `jice_2019`. The underlying sentence is:

> 直轄河川においては、堤体からの漏水・噴砂は確認されているものの、このような変状から
> 天端陥没等の変状に至った事例は確認されていない

Its subject is **堤体からの漏水・噴砂**, leakage and sand boiling from the *embankment
body*. The open question was whether the broken line in Figure 1.1, and therefore the
no-confirmed-completion statement, also covers the foundation route. It does not.

**Resolved against the author's copy of the source, two ways.**

The figure was read directly, and the page's vector drawing objects were enumerated. The
whole of Figure 1.1 contains exactly **two dashed strokes**, both at x = 125 pt:

| Stroke | Extent (pt) | What it is |
|---|---|---|
| 1 | y 315 to 327 | arrow 漏水・噴砂 into 堤体パイピング |
| 2 | y 350 to 361 | arrow 堤体パイピング down to 天端陥没 |

x = 125 is the horizontal centre of the 堤体パイピング box (x 101 to 149) and of
漏水・噴砂 (x 108 to 141). Nothing else on the page is dashed. The foundation route,
堤内のり尻直下への浸透水の到達 to 盤膨れ to 基礎地盤・噴砂 to 基礎地盤パイピング to
天端陥没, is drawn **solid** throughout.

**Consequence.** The broken line, and the no-confirmed-completion statement it encodes,
belong to the embankment-piping route alone. The unqualified generalisation
"initiation is thus attested at national scale while completion is not" was therefore
too broad, and it was contradicted by the thesis's own Chapter 5, which validates the
model against the **2012 Yabe River breach, a foundation-piping completion**. MLIT's
2019 tally is consistent: seepage caused 2 of 142 breaches, so completion on the
foundation route is rare rather than absent.

The claim is now scoped in the text: initiation is attested on both routes, confirmed
completion is rare and, on the embankment route, absent. The Yabe breach is named at the
point of the claim, so Chapter 2 and Chapter 5 no longer disagree.

## 10. Verification after the edits are applied

1. `grep -rn "stays below the Planned High Water\|judged adequate if the river\|judged safe if the river" msc-thesis/` returns nothing.
2. The two new bib keys resolve; `report.bcf` has no new undefined citations.
3. Zero CJK characters in typeset `.tex` content (the repo-hygiene rule; the two new bib
   entries are inside the agreed `references.bib` exception).
4. No em dashes introduced; "10,000 km" written with the LaTeX thousands separator already
   used in Chapter 8.
5. Page budget: the Chapter 2 replacement is net about two lines longer and the
   Introduction replacement about three, so the pass adds roughly five lines of body text.
   Re-check the 112-page budget after applying it; I did not compile to confirm the
   current slack.

## 11. What was applied, 2026-08-28

Approved in full by the owner, including the short Introduction variant. Applied to
`msc-thesis` in one commit. Verified: no undefined citations (157 bib entries,
105 keys used), all 261 cross-references resolve against 360 labels, no duplicate bib
keys, em-dash check CLEAN, CJK-in-`.tex` check CLEAN.

| File | Change |
|---|---|
| `frontmatter/summary.tex` | Opening sentence: "generally judged safe if the river stays below" becomes "must be shown safe against river levels up to the Planned High Water Level, not presumed safe below it" |
| `mainmatter/1. Introduction.tex` | Paragraph 2: false claim replaced by the design-load framing plus the standard's own duration disclaimer, short variant. Line 26: the scare-quoted "safe" water-level reading becomes "a water-level reading below the design stage" |
| `mainmatter/2. Theoretical...tex` | Paragraph 1: HWL as design load, demonstrated not presumed, the 40.8 per cent national failure rate, and the correct polarity of the binary rule. Closing sentence rescoped to "threshold judgments at a single design stage". Section on initiation without completion rescoped per Section 9. Loose "crest or the planned high water level" clause dropped at the basin-scale sentence |
| `mainmatter/3. Study Area...tex` | "a loading Japanese practice treats as the limiting case" becomes "the load Japanese verification is carried out against" |
| `appendix/appendix-g.tex` | Two additions: the standard's absolute-safety disclaimer with the Design Guideline's damage-record counterpart; and the hazard-mapping convention with the 2019 counter-evidence, 58 of 72 overtopped national sites not breaching. `mlit_teibou_sekkei_2007` added as the primary source for the allowable values |
| `references.bib` | Two entries added: `mlit_teibou_sekkei_2007`, `mlit_shinsui_manual_2015` |

**Citation-year note.** `mlit_teibou_sekkei_2007` carries `year = {2007}, month = {3}`,
the last revision (平成19年3月23日), not the 2002 promulgation, so the rendered year
matches the key and the version in force. The `note` field records both dates.

**Length.** Net +794 characters of main-body prose, about +7.9 typeset lines, roughly a
fifth of a page: Summary +0.2, Chapter 1 +2.3, Chapter 2 +5.4, Chapter 3 unchanged.
Appendix G grew by three sentences and does not count toward the 115-page main-body
ceiling. **Not verified against a build**, since local compilation is out of scope. The
build was closed at 112 pages with every chapter's last page full, so Chapter 1 or
Chapter 2 may now spill a few lines onto a new page. The hard ceiling has three pages of
headroom, so this is an aesthetic check, not a budget risk. Two restatement cuts were
already taken while applying the edits, in the same paragraphs, to hold the growth down.
