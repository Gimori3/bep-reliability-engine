# 続十勝川治水史 — full-volume review (all 816 pages)

**Date:** 2026-07-27
**Artefact:** `docs/references/tokachi_river_basin/inr9av000000b2i3.pdf` —
続十勝川治水史 電子版 (*Continued History of Tokachi River Flood Control*),
北海道開発局 帯広開発建設部, 令和5年10月 (2023-10), 816 pp, 375 MB, Japanese,
working text layer. The folder is gitignored; the PDF is machine-local.
**Predecessor:** `docs/tokachi_basin_document_review_2026-07-27.md`, which
sampled ~120 pages of this volume among 11 PDFs. This review covers the whole
volume and is the register of record for it.

**Method.** Full text extraction with PyMuPDF (scratchpad tooling: extractor →
delimited text, searcher with `--count` page-list mode, page printer, per-page
condenser, region renderer). Every one of the 816 pages was (a) machine-scanned
against a 100-term relevance lexicon far broader than the mandated keyword list
and (b) read at least at heading level; blocks carrying hits were read in full;
figure-embedded tables that carry load-bearing numbers were **rendered to PNG at
3–8× and read visually**, never trusted to the text layer's column order.

**Page-number convention.** Citations are **PDF page numbers**, with the printed
page in parentheses where observed. The offset is irregular (unnumbered plates)
and was re-derived per block; in the main body it is **PDF = printed + 20**,
drifting to +28 in the back matter. Every citation below was checked against the
printed number visible on its own page.

**Datum.** Elevations in this volume are **T.P. (Tokyo Peil)**. §2.1 below
establishes by exact numerical agreement — not by assumption — that the engine's
`m MSL` and this volume's `T.P.` are the same datum at the study reach.

---

## 0. Headline

Six findings justify the pass. In order of consequence:

1. **§2.1 — The engine's design-HWL profile, its datum, and its crest heights
   are now sourced, not asserted.** The engine's 2019 bank-height HWL at
   KP 56.6 is 38.140 m; the volume's current 河川整備基本方針 gives 38.14 m T.P.
   at 基準地点帯広 (56.6 km). Exact agreement, plus three further exact matches.
   This simultaneously **verifies the T.P. ≡ m MSL equivalence**, **pins the
   engine to the in-force plan revision**, and **dissolves the "0.42 m spread
   across revisions" concern** raised by the predecessor review. Class B.
2. **§2.2 — Three right-bank sluice conduits sit at or beside the study
   cross-sections**, including one at *exactly* KP 62.0, the governing piping
   section. The engine models a plain trapezoidal levee there. New data, real
   scope limitation, no value change. Class A.
3. **§2.3 — ADR-0032's loading-timescale characterisation is independently
   corroborated** by the authority's own flood-concentration-time analysis at
   Obihiro over 17 events (Kadoya 11–19 h, mean 15 h; kinematic wave 7–47 h,
   mean 24 h). Class B.
4. **§2.4 — R1 closed by execution.** The Phase 2 replay's Obihiro-datum 2016
   input peak is 38.07 m MSL, identical to the official published peak.
5. **§2.5 — R4 closed with a clean negative.** The full kasumi-tei table was
   recovered by rendering; **no** Phase 3 segment falls in a kasumi-tei opening.
6. **§4 — The strongest negatives in the volume.** In 816 pages of the official
   flood-control history of this river, パイピング occurs **twice** (once quoting
   the national standard, once about the Teton Dam in the USA) and 噴砂 **once**
   (1993 earthquake liquefaction). No flood-induced sand boil or piping event is
   recorded anywhere in the Tokachi system. Separately, the basin's own
   full-scale levee-breach experimental channel has run overflow and erosion
   experiments for 15 years and **never a seepage experiment**.

One Class C escalation (§3), **closed 2026-07-28** by the project owner in favour
of the recommendation (retain the gauge-table discharges 6,334 / 4,750 m³/s, with
the discrepancy footnoted). No engine change; no open Class C items remain.

---

## 1. Page-coverage ledger

All 816 pages accounted for. "Condensed + flagged read" means every page in the
block was machine-scanned against the relevance lexicon and read at heading
level, and every page returning a lexicon hit was then read in full.

| PDF pages | Printed | Content | Treatment | Verdict |
|---|---|---|---|---|
| 1–8 | — | Cover, forewords (5 officials) | Read | Nothing relevant |
| 9–16 | — | Full table of contents | **Read in full** | Structural map; used to plan the pass |
| 17–20 | — | Appendix TOC, part title pages | Read | Nothing relevant |
| 21–44 | 1–24 | §1.1 Basin overview: rivers, landform, geology, climate, ecology, landscape, society | Condensed + flagged read; **p41 read in full** | **A/D:** authoritative per-river bed gradients and basin dimensions (§2.6) |
| 45–54 | 25–34 | §1.3 Municipality profiles (19 towns) | Condensed | Nothing relevant |
| 55–61 | 35–41 | §2 50 years of river administration; public investment | Condensed + flagged read | **D:** 1997 River Law revision, climate-adaptation framing |
| 62–70 | 42–50 | §3 History of Tokachi flood control; two columns | Condensed + flagged read | **D:** context; leakage countermeasures named in the 1966-plan works list (p150) |
| **71** | **51** | **既往洪水の概要 — master historical flood table** | **Rendered + read visually (2 halves)** | **A:** 11 events 1922–2016 with Motoiwa/Obihiro 3-day basin rainfall, peak Q, damage (§2.6) |
| 72–80 | 52–60 | 昭和56年8月洪水 (1981): meteorology, station table, damage, response, restoration, 2 columns | **Read in full** | **A/B:** 1981 station table (§2.6); Obihiro 37.84 m / 4,750 m³/s |
| 81–83 | 61–63 | 昭和63年11月洪水 (1988) | **Read in full** | **D:** minor event; Tokachita approached design HWL |
| 84–96 | 64–76 | 平成28年8月洪水 (2016): 4 typhoons, station table, damage, 3 breaches, response, restoration | **Read in full** | **A/B/D:** station table verified; 3 breach attributions verified verbatim (§4.2) |
| 97–102 | 77–82 | 2016 columns (3 first-hand accounts) | **Read in full** | **D:** Satsunai KP25.0 landside-breach mechanism from the engineer who handled it (§4.2) |
| 103 | 83 | 既往地震・津波の概要 | **Read in full** | **D:** 1952/1993/2003 earthquakes, tsunami |
| **104** | **84** | **1993 釧路沖地震 — the volume's only 噴砂 hit** | **Read in full** | **A (negative):** the sand boils are **seismic liquefaction**, not flood seepage (§4.1) |
| 105–120 | 85–100 | 1993 earthquake: damage, committees, emergency and permanent restoration; 2 columns | Condensed + flagged read | **D:** 20 damaged levee sites, 9,168 m; SCP and drain restoration |
| 121–131 | 101–111 | 2003 十勝沖地震: committees, damage, restoration; 2 columns | **Read in full (122, 128, 130)** | **B/D:** the 2004 finding that 丘陵堤+drain serves *both* seismic and seepage; repair-depth/recurrence contrast (§2.7) |
| 132–152 | 112–132 | 工事実施基本計画 (1966): basic/design high water, HWL, channel plan, normal flow; 2 columns | Condensed + flagged read; **137, 146, 150 read in full** | **A:** 1966 design rainfall table (§2.6); **the 1.5 m / 2.0 m freeboard rule** (§2.1); 38.44 m Obihiro HWL |
| 153–160 | 133–140 | 1983 partial revision (Urahoro-Tokachi); special contribution | Condensed + flagged read; **158 read** | **A:** HWL table unchanged at 38.44 m |
| 161–163 | 141–143 | 1988 partial revision | **Read in full** | **A:** crest-width only (Obihiro 7.0 → 8.0 m); HWL untouched |
| 164–173 | 144–153 | 河川整備基本方針 (2007-03): basic high water, verification, design discharge, HWL/width | **Read in full (169–171)** | **A:** **38.14 m at 56.6 km first appears here**; 6,800 → 6,100 m³/s (§2.1) |
| 174–182 | 154–162 | 河川整備計画 (2010-09, 2013-06 変更) | Condensed + flagged read | **D:** target-discharge and works framing |
| **183–199** | **163–179** | **河川整備基本方針 令和4年9月改定 (2022)** — the climate revision | **Read in full (185–189, 195–199)** | **A/B:** 48-h design duration; ×1.15; 297/247 mm; 9,700/21,000 m³/s; **Obihiro flood-concentration times over 17 events** (§2.3); HWL retained at 38.14 (§2.1) |
| 200–219 | 180–199 | 河川整備計画 令和5年3月変更; 流域治水 | Condensed + flagged read | **D:** climate-adjusted target flows; watershed-wide flood management |
| 220–246 | 200–226 | Hokkaido development plans; 5-year flood-control programmes | Condensed + flagged read | **D:** institutional/funding chronology only |
| 247–256 | 227–236 | 第2編 River works overview by river | Condensed + flagged read | **D:** per-river works summary |
| 257–263 | 235–241 | Dredging; 2 columns | Condensed + flagged read | Nothing relevant |
| 264–271 | 242–249 | 堤防の整備: overview, **霞堤**, 丘陵堤 | **Read in full (265); p268 rendered** | **A:** the 5-category levee-development classification incl. 基盤漏水 (§4.3); **full kasumi-tei table, R4 closed** (§2.5) |
| 272–276 | 250–254 | Urban levee reinforcement (Obihiro, Otofuke, Ikeda, Honbetsu) | **Read in full (274)** | **D:** side-berm and revetment works in the study reach |
| **277–280** | **255–258** | **漏水対策 — the leakage-countermeasure chapter** | **Read in full** | **A/D:** compound embankment+foundation leakage; 河川砂防技術基準 duration clause; sheet-wall failure in sand-gravel → blanket (§4.3) |
| 281–300 | 259–278 | High-velocity-flow protection; groynes; Mishima pitch; low-water revetment; AGS | Condensed + flagged read | **D:** Satsunai/Otofuke morphology, revetment history |
| 301–358 | 279–336 | Small tributaries; new Obihiro R.; Kino setback; Takashima; Chiyoda new channel | Condensed + flagged read | **D:** Kino setback (4,000 → 6,100 m³/s at Tokachi Ohashi) |
| **359–362** | **337–340** | **Chiyoda groundwater investigation + new-channel washout** | **Read in full** | **B:** aquifer 15–20 m, k = 10⁻¹–10⁰ cm/s, GWT 2–4 m, bypass circulation — **verified verbatim** (§2.8) |
| 363–380 | 341–358 | Ecology park; inundation-mitigation works; Aioi-Nakajima; mid-Tokachi river-making | Condensed + flagged read | **D:** community works |
| **381–393** | **359–371** | **Otofuke channel plan — the 2011 bank-erosion levee washout** | **Read in full (381–383)** | **A/D:** 2011 event quantified; erosion-to-levee mechanism (§4.4) |
| 394–404 | 372–382 | Upper-Tokachi WG; 2016 bank erosion; bank-protection policy | Condensed + flagged read | **D:** 20 m+ bank retreat where revetment absent |
| **405–415** | **383–393** | **Interior drainage: pump stations, emergency pumps** | **Read in full (406)** | **A (negative):** only 4 directly-managed pump stations basin-wide; none adjacent to the study sections (§4.5) |
| 416–425 | 394–403 | Wide-area disaster response; fibre network; **earthquake/tsunami works** | **Read in full (423)** | **B:** 法尻ドレーン as an **L2-seismic** measure (§2.7) |
| 426–470 | 404–448 | River-environment works; sakura-tsutsumi; nature-oriented river works; community councils | Condensed + flagged read | Nothing relevant |
| **471–484** | **449–462** | **十勝川千代田実験水路 — the full-scale levee experiment facility** | **Read in full (476–481)** | **A (negative):** 15-year programme covers overflow and erosion breach, **no seepage experiment** (§4.6); 2021–22 revetment-flanking scour experiments (§4.4) |
| 485–532 | 463–508 | 第3編 Dams: Tokachi Dam, Satsunai Dam (geology, grouting, materials, concrete, filling); 2 columns | Condensed + flagged read | **Judged not relevant:** grain size, permeability and Lugeon values here are *dam-site bedrock and rockfill/core materials* in the mountain headwaters — a different geology, a different material and a different quantity from the levee foundation. Deliberately not carried across |
| 533–567 | 509–543 | 第4編 Sabo (erosion control): Satsunai/Totabetsu/Iwanai works; 2 columns | Condensed + flagged read | **D:** Satsunai headwater bed gradient 1/100–1/250 |
| 568–612 | 541–584 | 第5編 River management: law, maintenance plan, **河川カルテ**, patrol, flood forecasting, **flood-fighting** | **Read in full (581, 593, 599)** | **B/D:** river-ledger data items incl. **flood-trace survey** as standard; 漏水 as a flood-fighting mobilisation trigger; 重要水防箇所 governance (§2.9) |
| **613–614** | **585–586** | **水位観測所一覧表 + station location map** | **Rendered + read visually** | **A:** full gauge inventory; **no Tokachi gauge between KP 56.7 and 71.1** (§2.9); 札内 gauge at KP 4.0 confirmed (R11) |
| 615–639 | 587–611 | Information systems; crisis management; drills; water quality | Condensed + flagged read | **D:** crisis-type water-level gauges |
| **640–654** | **612–626** | **River-management-facility inventories: 樋門・樋管, pump stations, bridges** | **Rendered + read visually (642)** | **A:** **three right-bank sluices at KP 57.3, 61.7, 62.0** (§2.2) |
| 655–682 | 627–654 | Dam management; river use; gravel extraction; environment plan; river census | Condensed + flagged read | Nothing relevant |
| 683–690 | 655–660 | 第6編 Oikamanai River (a different, designated river) | Condensed + flagged read | Nothing relevant — outside the basin |
| **691–722** | **661–690** | **第7編 座談会 (round-table, 2023-06-23), two parts, 11 senior engineers** | **Read in full (700, 709, 716, 718)** | **A (negative)/D:** the volume's 2nd パイピング hit is the **Teton Dam**, not Tokachi (§4.1); drains recounted as a **seismic** measure by the man who ordered them (§2.7); d4PDF endorsement |
| 723–730 | 691–698 | Centenary events | Condensed | Nothing relevant |
| 731–740 | — | **治水年表 (year-by-year chronology, 1816–2023)** | Condensed + flagged read | **D:** no leakage/piping event appears in the chronology (§4.1) |
| 741–763 | — | Photograph plates (river, floods, works) | Condensed | Nothing relevant; one caption names sheet-wall/blanket works (p753) |
| 764–797 | — | Personnel rosters | Condensed | Nothing relevant |
| **798–810** | — | **北海道開発局技術研究発表会 発表論文一覧 (internal technical-paper index)** | Condensed + flagged read | **A:** names five unpublished HDB reports of direct relevance — an acquisition list (§5) |
| 811–816 | 779–781 | Column author index; afterword; committee; colophon | Condensed | Nothing relevant |

**Keyword-sweep safety net.** All mandated terms were run in `--count` mode over
the extracted text. Full page lists are in §4.1 for the diagnostic ones. Terms
returning **zero** hits in 816 pages: 盤膨れ, 盤ぶくれ, 被覆土層, 動水勾配,
局所動水勾配, 均等係数, 押え盛土, 詳細点検. That absence is itself a finding
(§4.1).

---

## 2. Findings

### 2.1 The design high-water profile, the datum, and the freeboard rule — Class B

**This is the most consequential result of the pass.** It converts four
previously-asserted engine numbers into sourced ones and closes a datum risk.

**What the volume says.**

| Plan revision | Date | Obihiro 計画高水位 at 基準地点 (56.6 km) | Source |
|---|---|---|---|
| 工事実施基本計画 (改定) | 1966-07 | **38.44 m T.P.** | p150 (printed 130), rendered summary table |
| 〃 部分改定 | 1983-03 | **38.44 m T.P.** (unchanged) | p158 (printed 138) |
| 〃 部分改定 | 1988-03 | unchanged (crest **width** only, 7.0 → 8.0 m) | p161 (printed 141) |
| **河川整備基本方針** | **2007-03** | **38.14 m T.P.** | p171 (printed 151) |
| **河川整備基本方針 改定** | **2022-09** | **38.14 m T.P.** (retained) | p199 (printed 179) |

The 2022 revision states its reason for not raising it, verbatim (p171,
carried into the 2022 table):

> 計画高水位を上げることは、災害ポテンシャルを増大させることになるため、
> 沿川の市街地の張り付き状況を考慮すると避けるべきであること。

*Raising the planned high-water level would increase disaster potential, and
given the built-up situation along the river it should be avoided.*

And the freeboard rule, from the 1966 plan (p150, printed 130), 計画高水位に
加える値: **+1.5 m** for the upper Tokachi, Otofuke, Satsunai and Toshibetsu;
**+2.0 m** for the lower Tokachi (mouth → Sarubetsu confluence).

**Verification against the engine (executed, not inferred).**

| Check | Engine | 続十勝川治水史 | Agreement |
|---|---|---|---|
| Design HWL at KP 56.6 | `load_hwl('Tokachi', 56.6)` = **38.140 m MSL** | 38.14 m T.P., p199/p171 | **exact** |
| Design HWL at KP 2.4 (mouth) | first row of the 2019 CSV = **5.10 m MSL** | 5.10 m T.P., p199 | **exact** |
| Freeboard, upper reach | `DesignBankHeight` − `HWL` = **+1.50 m** at KP 56.6/57.4/58.8/60.0/62.0 | +1.5 m, p150 | **exact** |
| Freeboard, lower reach | at KP 2.4: 7.10 − 5.10 = **+2.00 m** | +2.0 m, p150 | **exact** |
| KP 62.0 design crest | 46.39 + 1.50 = **47.89 m MSL** (the figure the thesis quotes) | derived from the above | **consistent** |

**Four consequences.**

1. **T.P. ≡ m MSL at this reach is now verified numerically, not assumed.** The
   task guardrails flag this project's two prior external-data burns (a 105.6×
   unit conversion, a rating-error placeholder). Exact agreement at two
   independent chainages, plus two independent freeboard constants, is a
   stronger check than a stated equivalence.
2. **The engine is pinned to the in-force revision.** The 2019 bank-height table
   reproduces the 2007 基本方針 profile, retained by the 2022 revision. It is
   not a superseded plan.
3. **The "0.42 m spread across revisions" concern is dissolved.** The four
   values 38.14 / 38.26 / 38.44 / 38.56 are not four revisions. They are **two
   revisions × two chainages**:

   | | at 基準地点 56.6 km | at 帯広 gauge 56.7 km |
   |---|---|---|
   | Old plan (1966–1988) | 38.44 (p150, p158) | **38.56** (p73, 1981 chapter) |
   | Current plan (2007, 2022) | **38.14** (p171, p199) | **38.26** (p87, 2016 chapter) |

   The engine's own profile settles it: interpolating `load_hwl` between
   KP 56.6 (38.140) and KP 56.8 (38.390) gives **38.265 m at KP 56.7**, i.e. the
   38.26 m tabulated for the 帯広 gauge in the 2016 chapter, to 5 mm. The same
   +0.12 m chainage offset reproduces 38.56 from 38.44 in the old plan. *(The
   chainage-offset explanation is an inference; the two numbers it reproduces,
   and the profile that reproduces them, are measured.)*
4. **One thesis precision fix follows.** Ch3 line 753 currently reads "0.07 m
   below the 38.14 m MSL design high-water level **at that gauge**". 38.14 m is
   the value at the 基準地点 (KP 56.6); at the gauge (KP 56.7) it is 38.26 m, as
   Ch3 §2016 itself correctly states. Both numbers are right; the label is not.
   Fixed (§6).

### 2.2 Three right-bank sluice conduits at the study cross-sections — Class A

From the 樋門・樋管一覧表 (指定区間外区間, 帯広河川事務所, 令和4年3月末現在),
p642 (printed 614), rendered and read at 8× to confirm the 左右岸 column:

| River | 築堤 | 距離標 | Bank | 樋門 | 断面 W×H×L ~ barrels |
|---|---|---|---|---|---|
| 十勝川 | 北帯広築堤 | **57.3** | **右 (right)** | 木賊原樋門 | 6.0 × 3.0 × 27.0 ~ 2 |
| 十勝川 | 然別築堤 | 60.1 | 左 (left) | 然別樋門 | 2.5 × 1.8 × 37.0 ~ 1 |
| 十勝川 | 北帯広築堤 | **61.7** | **右 (right)** | 伏古樋門 | 2.0 × 2.0 × 28.0 ~ 1 |
| 十勝川 | 西士狩築堤 | **62.0** | **右 (right)** | 西士狩樋門 | 1.5 × 2.0 × 28.0 ~ 1 |
| 十勝川 | 西帯広築堤 | 64.7 | 右 | 西帯広樋門 | 1.5 × 1.5 × 22.0 ~ 1 |
| 十勝川 | 西帯広築堤 | 65.3 | 右 | 西帯広第2樋門 | 1.5 × 2.0 × 26.0 ~ 1 |

**Why this matters.** The study cross-sections are Tokachi **right bank** at
KP 57.4, 58.8, 60.0, 62.0. Two of them coincide with a sluice:

- **KP 62.0 — the governing piping section** (narrowest foreshore at 44 m, 1998
  OYO exit gradient $i_v$ = 0.97, `remediation_state: unreinforced`, the failure
  mode named in OYO 表6-3-1 as 基盤漏水によるパイピング) — has a sluice at
  **exactly that chainage**, with a 28 m conduit.
- **KP 57.4** has a sluice 0.1 km away at KP 57.3, with a 27 m **two-barrel**
  conduit of 6.0 × 3.0 m section — much the largest in the reach.

The conduit lengths (27–28 m) are the same order as the modelled under-levee
seepage lengths ($L$ = 33 m at KP 57.4, 47 m at KP 62.0), i.e. a conduit spans a
comparable fraction of the levee footprint.

**What is and is not claimed.** The engine models foundation BEP through the
blanket–aquifer system beneath a plain trapezoidal levee. A buried culvert is a
*separate and separately-recognised* failure pathway (preferential flow along
the conduit, a discontinuity in the blanket, void formation around the barrel);
Japanese doctrine treats 樋門周辺の空洞化 as its own inspection and design item.
This review does **not** claim the sluices invalidate anything computed — it
claims the model set does not contain them, at two of the four sections, one of
which governs.

The predecessor provenance file references 伏古樋門 only as a **KP landmark**
used to allocate `remediation_state` (§3.2), never as a physical feature of the
cross-section. That gap is now closed on the record.

**Action taken:** recorded in `docs/tokachi_bep_inputs_provenance.md` §5.2, and
stated as a scope limitation in the thesis. **No value changed; no re-run.**

### 2.3 Obihiro flood-concentration times — Class B corroboration of ADR-0032

p186 (printed 166), from the 2022 基本方針 determination of the design rainfall
duration. For 17 major floods at Obihiro, 昭和36–平成28, both a kinematic-wave
and a Kadoya-formula flood concentration time (洪水到達時間) is tabulated:

> ■Kinematic Wave 法による洪水到達時間は **7～47 時間（平均24 時間）** と推定。
> ■角屋の式による洪水到達時間は **11～19 時間（平均15 時間）** と推定。

The companion Motoiwa table (p185, printed 165) gives 23–68 h (mean 39 h) and
16–27 h (mean 21 h).

**Why this matters.** ADR-0032 retained the instantaneous M4 head translation on
a measured characterisation of the *d4PDF ensemble* loading: median $T_\text{rise}$
= 18 h, plateau 9 h, explicitly retiring the spec's earlier "~1.5 h plateau"
claim. That characterisation now has **independent corroboration from the river
authority's own hydrological analysis of the observed record** — an entirely
different data source (17 gauged floods, not a climate ensemble) and an entirely
different method (rainfall–runoff concentration time, not hydrograph shape
statistics). The 15–24 h central estimates bracket the engine's 18 h.

This does not re-derive $\Pi$ and does not touch the gate; ADR-0032 stands
exactly as accepted. It converts one of its inputs from a single-source
measurement into a two-source one.

**Also recorded, Class A:** the 2022 revision **changed the design rainfall
duration from 3 days to 48 hours** on the strength of these concentration times
and a one-rainfall-duration frequency analysis (48 h covers 80 % of rainfalls,
p185/186). Any comparison of the thesis's loading durations to "the design
event" must now use 48 h, not 72 h.

### 2.4 R1 closed — the Phase 2 2016 loading verified against the official record

The predecessor review left R1 open: *verify the Phase 2 reconstructed 2016
Obihiro peak against the official 38.07 m*. The Phase 1 artefacts and the
committed 2016 extracts are present locally, so this was executed rather than
reasoned about.

```
Phase 2 input: Obihiro observed 2016 peak stage = 38.07 m MSL  (station=obihiro)
 official 続十勝川治水史 p.87 (printed 67)      = 38.07 m  T.P.
 difference                                     = +0.000 m
```

The whole 2016 station table cross-checks at four gauges simultaneously against
the committed hourly record: Memurobuto 64.79, Obihiro 38.07, Chiyoda 18.74,
Moiwa 12.68 — every one matching p87 exactly.

The per-section reconstructions that the ADR-0035 chain then produces are, for
the record: KP 57.4 → 39.658, KP 58.8 → 40.750, KP 60.0 → 42.296,
KP 62.0 → 45.729 m MSL.

**R1 is closed: the head of the Phase 2 loading chain is verified against the
official published record.** Note the scope — this verifies the *input* stage,
not the section-rating and trace-anchoring steps downstream of it, which have no
independent published counterpart.

### 2.5 R4 closed — kasumi-tei table recovered, no Phase 3 segment affected

The predecessor review could not read the 霞堤一覧表 (p268, printed 246) because
the text layer truncates mid-table, and flagged it as a **Phase 3 correctness
item**: a kasumi-tei is an intentionally discontinuous levee, so any of the 114
series-system nodes falling in an opening would be wrongly composed. Rendered at
4.5× and read visually, the table is complete:

- **Tokachi (13):** right bank KP 63.8, 69.4, 74.6, 76.6, 80.4, 88.4, 96.4;
  left bank KP 65.8, 80.6, 85.0, 89.0, 96.0, 99.4.
- **Satsunai (13):** right bank KP 7.0, 9.2, 14.6, 29.6, 32.0, 34.2, 43.0;
  left bank KP 19.8, 24.2, 28.0, 37.8, 40.8, 43.0.
- **Otofuke (8):** right bank KP 5.2, 12.8, 16.0, 25.8; left bank KP 6.2, 17.2,
  21.4, 28.4.

Checked against the live registry (`system_integration.segments.build_registry`):

| Registry stratum | Node range | Kasumi-tei on the *same bank* inside that range |
|---|---|---|
| Tokachi **right**, 46 nodes | KP 53.8 – 62.8 | **none** (nearest is KP 63.8, 1.0 km beyond the top node) |
| Satsunai **left**, 68 nodes | KP 3.2 – 16.6 | **none** (all left-bank Satsunai kasumi are at KP ≥ 19.8) |

**R4 closes as a clean negative: no Phase 3 segment lies in a kasumi-tei
opening.** The RQ4 headline numbers are protected. One second-order caveat worth
a sentence rather than a correction: the Satsunai right-bank kasumi at KP 7.0,
9.2 and 14.6 lie **directly opposite** modelled left-bank segments, so lateral
outflow there is a local stage influence the segment model does not represent.

### 2.6 Historical loading record — Class A

**The master flood table (p71, printed 51)**, rendered and read visually. 11
events, 1922–2016, with basin-average 3-day rainfall and peak discharge at both
reference points:

| Event | Cause | Motoiwa mm/3d | Motoiwa Q | Obihiro mm/3d | Obihiro Q | Inundated area |
|---|---|---|---|---|---|---|
| 1922-08 | typhoon | 204.3 | 9,390 | 223.9 | 3,208 | 5,243 ha |
| 1962-08 | typhoon | 135.0 | 8,839 | 166.6 | 4,204 | 40,768 ha |
| 1972-09 | typhoon | 177.1 | 7,787 | 193.1 | 2,880 | 30,729 ha |
| 1975-05 | low | 106.1 | 4,167 | 91.1 | 986 | 2,698 ha |
| 1981-08 | typhoon | 209.1 | 7,671 | 283.8 | 4,952 | 7,017 ha |
| 1988-11 | low | 123.1 | 3,065 | 103.3 | 843 | 366 ha |
| 1989-06 | low | 133.7 | 2,823 | 111.0 | 833 | 3,940 ha |
| 1998-09 | typhoon | 112.0 | 4,814 | 106.0 | 1,699 | 1,907 ha |
| 2001-09 | typhoon | 163.5 | 7,227 | 157.9 | 2,595 | 298 ha |
| 2003-08 | typhoon | 177.8 | 6,700 | 171.4 | 2,189 | 369 ha |
| **2011-09** | front | 129.9 | 4,211 | 167.1 | **2,540** | 38 ha |
| **2016-08** | typhoon | 167.1 | **12,388** | 198.6 | **6,649** | 1,412 ha |

*(The 1981 and 2016 Obihiro/Motoiwa discharges in this summary table disagree
with the station tables elsewhere in the same volume — see the Class C register,
§3.)*

**The 1981 station table (p73, printed 53)** gives the operational reference
levels of that era and the observed peaks at 9 stations. Obihiro: 計画高水位
38.56, 警戒水位 35.80, 指定水位 35.30; peak 37.84 m / 4,750 m³/s. Motoiwa peak
10.19 m / 6,749 m³/s. The event is described as the largest on the main stem
since 1922; Obihiro city recorded 162 mm in 4 days, an all-time record at the
time; basin average 220 mm.

**The 17-event Obihiro peak-discharge series (p186, printed 166)** — the fullest
single record in the volume, with date, time of peak, and two concentration-time
estimates per event: S36.7 1,485; S37.8 4,204; S39.6 837; S39.8 1,088; S47.9
2,160; S48.9 937; S56.8 4,750; S63.11 824; H1.6 823; H4.9 661; H10.8 795;
H10.9 1,625; H13.9 2,110; H14.10 1,758; H15.8 1,915; H23.9 2,373; **H28.8
6,334** m³/s.

**Design rainfall, 1966 plan (p137, printed 117)**, 単位 mm/3日, 1/150 unless
noted: 茂岩 214.8, 千代田 230.0, **帯広 245.7**, 芽室 256.5, 音更 235.0,
人舞 265.0 (1/100), 利別 203.3 (1/100), 仙美里 220.8 (1/100), 南帯橋 **335.8
(1/150) and 310.8 (1/100)** — two values because the Satsunai design scale
changes across the Totabetsu confluence — 十勝ダム 268.6, 足寄ダム 224.2,
札内ダム 346.6, 佐幌ダム 254.6 (all 1/100).

This **sources the thesis's 245.7 mm figure directly** (Ch3 currently cites it
to `fukuoka_2019` / `wp1_report_2021`) and confirms it is a 3-day, 1/150 value
belonging to the **superseded** 工事実施基本計画 — superseded by 297 mm/48 h.

**Bed gradients, per river (p41, printed 21)** — more precise than the "1/200 to
1/600" the predecessor review took from a column on p392:

> 十勝川の河床勾配は、然別川合流点付近までの上流部が約**1/200～1/450**、
> 然別川合流点付近から利別川合流点付近までの中流部が約**1/600～1/1,200**、
> 利別川合流点付近から河口までの下流部が約**1/3,000～1/5,000**である。

Also: 音更川 1/150–1/200; 札内川 1/100–1/250; 利別川 1/500–1/1,400. Basin
9,010 km² (6th nationally), main stem 156 km (17th).

**The break at the Shikaribetsu confluence is visible in the engine's own data.**
The 然別樋門 is at KP 60.1, so the study sections straddle the break. Design
water-surface slopes from `load_hwl`: KP 56.6→57.4 = 1/748, 57.4→58.8 = 1/769,
58.8→60.0 = 1/698, **60.0→62.0 = 1/549**. The steepening above KP 60 matches the
documented reach change, at the flatter end of each band as expected for a
backwater profile over a steeper bed.

### 2.7 `remediation_state` — the drains have three documented drivers, Class A

The predecessor review recorded the institutional chronology behind the
`remediation_state` column (2002/2004 guidelines, FY2003–2007 initiation). The
full-volume pass adds a qualification that a `drained` label alone does not
carry: **the toe-drain programme in this basin has three distinct documented
rationales**, and they were deployed in different reaches.

1. **Seepage.** p279 (printed 257): after the 2002 手引き and 2004 質的整備
   guideline, "堤防の浸透に対する安全性の照査を実施するとともに、対策工が必要な
   箇所において、堤防の裏のり尻ドレーン工法などの堤防強化対策が実施された."
2. **Seismic.** p122 (printed 102), 2004 review: 大断面化（丘陵堤）＋ドレーン工
   is effective "地震対策としてのみならず、浸透対策としても有効" — and Obihiro
   accordingly deployed drains **in the liquefaction-prone lower Tokachi**.
   p423 (printed 401) confirms 法尻ドレーン basin-wide as an **L2-seismic**
   measure under the 2007/2012 耐震性能照査指針. The round-table (p709) has the
   engineer who ordered them describing the rationale as purely seismic —
   lens-shaped perched groundwater in enlarged sections liquefying — and being
   criticised at the time for "putting drains in a levee".
3. **Construction-stage.** pp128/130 (printed 108/110), 2003 earthquake
   restoration: 裏のり尻ドレーン工 installed for 湧水処理, toe protection and
   trafficability during rapid refill.

The seepage-driven works (1) are the ones the Fukuda landside-type map assigns
to KP 58.0–61.0 (types ④+⑤), i.e. the study sections KP 58.8 and 60.0; the
seismic-driven works (2) are lower-Tokachi. So the current allocation is not
disturbed. What changes is the confidence statement: **a `drained` label
identifies a physical feature, not a design intent**, and the intent matters if
the label is ever converted into physics (the standing R8 opt-in remediation
sensitivity).

Also recorded, for the same open item: p122 gives the repair-depth/recurrence
contrast in its own words — sites repaired in 1993 with 基盤処理 and full
re-excavation (統内, 東稲穂) took almost no 2003 damage, while the partially
re-excavated 幌岡 was damaged over nearly its full length in 2003.

### 2.8 Chiyoda aquifer measurement — independently verified, Class B

Read verbatim at p359 (printed 337), confirming the predecessor review exactly:

> 帯水層は、概ね**砂礫層（厚さ15～20m 程度）**で構成され、**透水係数は
> 10⁻¹～10⁰ cm/s** と高い（浸透しやすい）ことが確認された

= 15–20 m sand-gravel, k = 1×10⁻³ to 1×10⁻² m/s, at **KP 37.6**, groundwater
table 2–4 m below ground, with the documented weir-driven bypass circulation
(river recharges hinterland upstream of the weir, hinterland drains to river
downstream). The same page characterises the unit the new channel cuts as
"極めて透水性の高い氾濫原堆積層（砂礫層）".

Nothing changes. The predecessor review's disposition — regional corroboration,
not section data, ~20 km downstream in a different geomorphic setting, no prior
derived from it, with the standing concern that the measured upper bound exceeds
the `k_aq` prior's 95th percentile — is correct and stands. This pass confirms
the quotation is accurate and the reading is faithful.

### 2.9 Gauge and monitoring inventory — Class A

From the rendered 水位観測所一覧表 (p613, printed 585, 令和4年4月現在) and its
location map (p614):

- **There is no water-level gauge on the Tokachi main stem between 帯広
  (KP 56.7) and 芽室太 (KP 71.1).** The study sections (KP 57.4–63.4) contain
  none; the nearest is Obihiro, 0.7–6.7 km downstream. This is the sourced
  justification for the M3 rating chain's structure and quantifies its
  extrapolation distance.
- Obihiro: KP 56.7, catchment 2,677.8 km², record from **明40.1 = January 1907**.
- **国見橋 is on the 然別川 at KP 0.6**, not on the Tokachi — relevant to the
  KP 63.4 anomaly, which the provenance file records as carrying
  "Shikaribetsu-referenced loading (not Obihiro)".
- Satsunai gauges: 竜潭上流 56.4, 上札内 41.8, 第2大川橋 20.7, **南帯橋 15.0**,
  **札内 4.0**. This confirms open item **R11** from the official inventory: the
  札内 gauge at KP 4.0 sits *inside* the Phase 3 Satsunai reach (KP 3.2–16.6),
  while the rating chain uses Nantai at KP 15.0, 8–11 km upstream of the section
  nodes. Engine-side item; unchanged by this review.

Also, from the river-management chapter, two items that support existing
decisions:

- **p581 (printed 553)** lists 洪水痕跡調査 (flood-trace survey) among the
  standard, required 河川カルテ data items, alongside the a/b/c/d condition
  ranks. The ADR-0035 anchoring of the 2016 peak to a surveyed flood trace
  therefore rests on a **routine statutory survey product**, not an ad hoc
  measurement.
- **p593 (printed 565)** lists **漏水** among the conditions triggering
  flood-fighting mobilisation (溢水、漏水、法崩、洗堀), with 重要水防箇所
  prioritised for patrol — the operational counterpart of the D2 screening
  doctrine.

---

## 3. Class C conflict register

One item. It requires a decision but **no engine change and no re-run**.

### C-1. The volume's summary flood table disagrees with its own station tables on peak discharge

**1. What the engine/thesis currently use, and where it came from.**
The thesis (Ch3 §2016, and the station table `tab:tokachi_2016_stations`) uses
**6,334 m³/s** for the 2016 Obihiro peak and **4,750 m³/s** for 1981, both cited
to `tokachi_chisuishi_2023`. These are the values in the **event chapters'
station tables** — p87 (printed 67) for 2016 and p73 (printed 53) for 1981 — and
they are corroborated independently within the volume by the **2022 basic-policy
hydrological analysis table** at p186 (printed 166), which lists S56.8.5 = 4,750
and H28.8.31 = 6,334. No engine parameter depends on either number; they are
descriptive context.

**2. The competing value, characterised.**
The **既往洪水の概要 summary table at p71 (printed 51)** — the volume's own
master historical-flood table, read visually from a render — gives, in a column
headed simply 流量 (m³/s):

| | p71 summary | p73 / p87 / p185 / p186 station + analysis tables | ratio |
|---|---|---|---|
| 1981 Obihiro | **4,952** | 4,750 | 1.043 |
| 1981 Motoiwa | **7,671** | 6,749 | 1.137 |
| 2016 Obihiro | **6,649** | 6,334 | 1.050 |
| 2016 Motoiwa | **12,388** | 11,608 | 1.067 |

The p71 values are systematically **higher**, by 4–14 %, with no constant ratio.
The rainfall columns of the same p71 row *do* agree with the event chapters
(2016: 167.1 mm/3d Motoiwa, 198.6 mm/3d Obihiro, matching p88 verbatim), so this
is specifically a discharge discrepancy, not a mis-paired row.

The volume gives no definition for the p71 column and does not flag the
difference. Dam-regulation reconstruction is the obvious hypothesis but **does
not survive**: Tokachi Dam was completed 1984 and Satsunai Dam 1998, so neither
regulated the 1981 event, which nonetheless shows the largest relative
difference. A separate, smaller discrepancy of the same family appears at
pp381/382, where the 2011 Otofuke peak discharge is given as 526 and 548 m³/s
(the latter marked 暫定値) two pages apart. **I could not resolve the p71
definition from the volume and am not going to invent one.**

**3. Physical consequence of each choice.** None for the engine — no fragility,
posterior, or Phase 3 number consumes a peak discharge from this volume. The
consequence is confined to descriptive statements in Ch3. Choosing the higher
p71 values would make the observed record look ~5 % closer to the design
discharge (6,649 vs 6,334 against the superseded 6,800 m³/s: 98 % rather than
93 %), which is the *less* conservative framing for the thesis's argument that
the observed record sits well short of the design condition.

**4. Recommendation, with confidence.** **Keep 6,334 and 4,750; add a footnote
naming the p71 discrepancy.** Confidence: **high**. Three reasons: the station
tables are the event-specific records of the responsible office; the 2022
basic-policy analysis (p186) independently reproduces exactly those values in a
table built for a different purpose, giving two independent agreements against
p71's one; and the thesis's existing sentence is the conservative reading. I
recommend against silently preferring the newer-looking summary table — the
predecessor review's own retracted over-reading (§1.4) is the cautionary
precedent for treating a more official-looking presentation as authoritative.

**5. DECIDED 2026-07-28 — project owner approved the recommendation.** The
gauge-table values **6,334 m³/s (2016) and 4,750 m³/s (1981) are retained**, with
the Ch3 footnote recording the p71 discrepancy. No further edit was required: the
thesis already carried these values, and the footnote as written states the
adoption reason and is explicit that *the volume's own inconsistency remains
unexplained* — the decision settles which values this thesis uses, not what the
p71 column means. **C-1 is closed. No open Class C items remain from this
review.**

---

## 4. Negative results

A negative result on an open question is a real result, and several of the
strongest findings in this pass are negatives.

### 4.1 The observational record contains no flood-induced piping or sand boil

Complete hit lists over all 816 pages:

| Term | Hits | Pages | What they actually are |
|---|---|---|---|
| **パイピング** | **2** | 277, 700 | p277: a *quotation of the national 河川砂防技術基準* on what levees must be designed against. p700: the **1976 Teton Dam failure in the USA**, recounted in the round-table as the reason a conduit was banned beneath rockfill dams. **Neither is a Tokachi levee event.** |
| **噴砂** | **1** | 104 | The **1993 Kushiro-oki earthquake**: 法すべり、陥没、縦横断亀裂、噴砂 at 統内, 幌岡, 旅来, トイトッキ. **Seismic liquefaction, not flood seepage.** |
| **基盤漏水** | 1 | 265 | The 5-category levee-development classification (§4.3) |
| **複合漏水** | 1 | 277 | The characterisation of the upstream reach |
| 盤ぶくれ / 盤膨れ | **0** | — | — |
| 被覆土層 | **0** | — | — |
| 動水勾配 / 局所動水勾配 | **0** | — | — |
| 均等係数 | **0** | — | — |
| 詳細点検 | **0** | — | — |
| 透水係数 | 1 | 359 | The Chiyoda aquifer measurement (§2.8) |

The year-by-year 治水年表 (pp731–740, 1816–2023) records no leakage or piping
event either.

**The honest statement this licenses:** in the official 816-page flood-control
history of this river system, covering 1816–2023, there is **no record of an
observed backward-erosion-piping event or flood-induced sand boil on any Tokachi
levee**. What the volume does record is that the mechanism was taken seriously
enough to drive a named remediation programme (§4.3). This is a materially
stronger and more precisely-scoped version of the "paradox of survival" the
thesis already argues, and it is the correct empirical framing for the Phase 2
survival conditioning.

**The caveat that must accompany it, stated plainly:** a commemorative history
is not an inspection database. Absence here is evidence that no piping event was
significant enough to enter the official narrative — not proof that none
occurred. The instrument that *would* settle it is the 河川カルテ / 巡視・点検
record with its ⑫漏水・噴砂 category (open item R6), which this volume describes
(p581) but does not reproduce.

### 4.2 The 2016 breaches — all three verified, none attributed to seepage

Verified verbatim at pp91–93 (printed 71–73), each with 十勝川堤防調査委員会
attribution:

| Location | Confirmed | Length | Official cause (verbatim gist) |
|---|---|---|---|
| 音更川 KP21.2 左岸 | 08-31 17:30 | 200 m | 洪水位の低下時に流路変動が発生し河岸及び堤体の侵食により堤防が決壊 — channel migration **during the falling limb**, bank and embankment erosion |
| 札内川 KP25.0 左岸 | 08-31 05:20 | 200 m | 滞留した内水に加え、戸蔦別川の堤防決壊による氾濫水が…**堤内側から堤防を越水（痕跡あり）** — ponded interior water plus flood water from the Totabetsu breach overtopped **from the landside** (trace evidence) |
| 札内川 KP40.5 左岸 | 09-01 11:10 | 200 m | as KP21.2 — falling-limb channel migration, bank and embankment erosion |

The predecessor review's account is confirmed exactly. The full-volume pass adds
the **first-hand mechanism narrative** for the KP25.0 breach, from the engineer
who directed the emergency works (p100, printed 80):

> 戸蔦別川右岸が上流で破堤し、畑に流れ込んだ水が樋門箇所に溜まって堤内側から
> 破堤したことがわかりました。上流からの氾濫水が合流点に集まり、さらに堤防を
> 乗り越えて札内川の方へ越流したことに耐えきれず破堤した

*The Totabetsu right bank breached upstream; water flowed into the fields, ponded
at the sluice, and breached from the landside. Flood water from upstream
collected at the confluence, overtopped the levee toward the Satsunai, and the
levee failed under it.*

Note the ponding occurred **at the sluice** (戸蔦別樋門) — reinforcing §2.2's
point that sluices are locally distinctive hydraulic features the segment model
does not carry.

### 4.3 The mechanism *was* recognised and remediated — the positive complement

Two verbatim statements, both confirming the predecessor review:

**p265 (printed 243)**, item ④ of the five characteristic features of Tokachi
levee development:

> 上流域においては、堤防基盤が沖積世の氾濫原堆積物からなる極めて透水性の高い
> 地質のため、**基盤漏水**や堤体漏水により堤防の機能が失われるおそれのある箇所
> において「漏水対策」が行われた。

**p277 (printed 255)**:

> 十勝川水系の上流域においては、堤防の基礎地盤は沖積世の氾濫原堆積物からなる
> 極めて透水性が高い地質であり、堤体材も現地土を用いた砂礫土から構成されて
> いるため透水性も高く、**堤体と基盤（地盤）の複合漏水**の形態をとっていると
> 考えられた。

quoting 河川砂防技術基準 as applied from the late 1970s:

> 堤防は堤体材料、基礎地盤材料、水位、**高水の継続時間**等を考慮して、浸透水の
> しゃ断及びクイックサンド、パイピング現象を生じさせないような構造でなければ
> ならない

**Scope precision this pass adds.** The predecessor review left the impression
that the documented leakage-countermeasure works are in the study reach. They
are not, in the main: p277–278 attribute the concrete works to the **Otofuke
downstream urban reach** (from 昭和51 = 1976, sheet wall and blanket methods,
selected by ground investigation), and p280's sheet-wall failure account is the
**音更～木野築堤** works. The general characterisation (①上流域…基盤漏水) covers
the study reach; the specific construction records cited do not. That distinction
should be preserved wherever the thesis leans on these passages.

### 4.4 The erosion mechanism that actually breaks these levees is not point scour

Two independent confirmations, both new in this pass, both bearing on open item
**R10** (the corrected-USACE scour model computing exactly zero at all 114
nodes while erosion broke two levees in 2016):

1. **The 2011 Otofuke washout (pp381–383, printed 359–361).** At KP 18.2 left
   bank, "この箇所には低水護岸および高水護岸はもともと設置されておらず、洪水に
   よって高水敷が侵食され、その侵食が堤防に達したことで堤防の一部流出が生じて
   いる" — *no low-water or high-water revetment was present; the flood eroded
   the high-water bed and that erosion reached the levee.* Measured retreat
   during the flood: **~5 m per hour** of levee length lost. The event: 383 mm
   over 2–7 September at Naitai, Otofuke gauge peak 73.22 m and 548 m³/s
   (暫定値), the **third largest since 1967**.
2. **The Chiyoda experimental-channel erosion experiments, R3–R4 (2021–22)**
   (p481, printed 459), run specifically to explain the 2016 breaches:
   "特に急流河川の**湾曲外岸部で水位がHWL に近い状態**になった時に、**低水護岸
   の裏側が洗掘**され侵食が堤防にまで至ることに着目し" — *scour behind the
   low-water revetment at the outer bank of a bend when the stage approaches
   HWL, propagating to the levee.*

Both are **revetment-flanking / high-water-bed erosion propagating laterally to
the levee**, driven by planform migration. A USACE point-scour formulation does
not represent either. This is direct, sourced support for stating the Phase 3
RQ3 BEP-dominance conclusion as **conditional on the surface-mechanism model
set**, and for naming precisely which mechanism is missing — which the thesis
Ch7 already does, and can now do with a citation.

### 4.5 No directly-managed pump station adjacent to the study sections

p406 (printed 384): the basin has **four** directly-managed drainage pump
stations — 帯広 (帯広川 KP 0.7 right, 1972), 下牛首別 (十勝川 KP 18.9 right,
1977), 池田 (利別川 KP 6.6 left, 1983), 育素多 (十勝川 KP 21.7 left, 1988).
None is on the Tokachi main stem between KP 53.8 and 62.8. The Satsunai KP25.0
landside-overtopping mechanism required ponded interior water plus a tributary
breach; the study reach has neither a pump station nor a mapped equivalent
ponding configuration in this volume. A useful negative for bounding the
model-scope gap the predecessor review raised.

### 4.6 Japan's full-scale levee-breach facility, on this river, has never run a seepage experiment

The 十勝川千代田実験水路 (pp471–484, printed 449–462) is a **full-scale**
experimental channel on the Tokachi at Chiyoda, ≥150 m³/s controllable supply,
advised by a committee of Tsujimoto, Yamada, Shimizu, Izumi, Watanabe et al. The
long-term programme (p477–478, printed 455–456) has six research themes; theme I
is 堤防・保護工の機能評価技術の向上, whose sub-themes are:

> 1. 越水破堤に対するハード・ソフト対策技術の向上
> 2. 保護工の適切な設計方法・評価方法の提案

The executed-experiment timeline (p480, printed 458) covers H20–R4 (2008–2022):
overflow-breach widening mechanism, breach-widening suppression works, block
rolling and rough closure, block-placement efficiency, riverbed waves, and
(R3–R4) erosion-induced breach. **There is no seepage or piping experiment in
the programme, and none in fifteen years of execution.**

This is worth stating carefully, because it is an institutional observation
rather than a physical one: it does not show that Japanese practice neglects
seepage (D1/D2 doctrine shows the opposite). It shows that the country's premier
full-scale levee-failure experimental capability — sited on the very river this
thesis studies — has been directed entirely at overflow and erosion. That is a
concrete, sourced, non-polemical illustration of where the empirical effort has
gone, and it is the institutional counterpart to the JSCE erosion-dominance
verdict the thesis already engages in Ch7.

---

## 5. Acquisition list (what needs data neither of us has)

The internal technical-paper index (pp798–810) names five unpublished 北海道開発局
technical-conference reports of direct relevance. All are Obihiro Development and
Construction Department (帯広開発建設部) or 治水課 products, so all are in
principle requestable through the same channel as the standing OYO/Fukuda items:

| Title | Why it matters |
|---|---|
| **音更川堤防漏水対策工事報告** (p809) | The construction record of the leakage countermeasures whose *outcome* p277–280 describes. Would give as-built blanket and sheet-wall geometry — the dimensions any R8 remediation sensitivity needs |
| **十勝川水系における河川水と地下水との相互関係について** (p809) | River–groundwater interaction at system scale. Directly bears on the M4 hinterland boundary condition and the ADR-0006 semi-infinite schematisation |
| **札内川扇状地の地下水構造について** (p807) | Alluvial-fan groundwater structure. The Satsunai analogue of the Chiyoda investigation |
| **十勝平野における地下水保全について (第1報/第2報)**, **十勝平野地下水調査** (pp805–806) | Basin-scale groundwater surveys — the natural source of a *study-reach* $k_\text{aq}$ / $D_\text{aq}$ measurement to replace the KP 37.6 proxy |
| **都市環境を考慮した堤防強化対策について** (p803) | Levee-strengthening measures in the urban reach that contains the study sections |

Carried forward unchanged from the predecessor review's §10.1: R2 (the 66.7 km
deficient-section KP list), R3 (Abashiri geotechnical profile), R5 (土層縦断図),
R6 (河川カルテ / 巡視・点検結果 with the ⑫漏水・噴砂 category — the instrument
that would convert §4.1's negative from "not in the narrative" to "not in the
inspection record").

**Closed by this pass:** R1 (§2.4), R4 (§2.5). **R11 confirmed** from the
official gauge inventory (§2.9) and remains an engine-side open item.

---

## 6. What was changed

### Engine (`bep-reliability-engine`)

- `docs/tokachi_bep_inputs_provenance.md` — new §5, recording: the design-HWL /
  datum / freeboard verification chain (§2.1), the three right-bank sluices
  (§2.2), the three-driver qualification on the `remediation_state` drains
  (§2.7), the gauge-inventory facts (§2.9), and the R1/R4 closures.
- This document.
- **No CSV value changed. No config regenerated. No ADR written** — nothing in
  this volume warrants a new architectural decision. Nothing here triggers a
  campaign re-run.

### Thesis (`msc-thesis`)

- **Ch3 §Hydrological Character** — the design-HWL revision chronology pinned to
  named revisions with dates, the T.P. ≡ m MSL verification stated, the 245.7 mm
  design rainfall re-sourced to the primary document and marked as belonging to
  the superseded plan, and the 48-hour design duration of the current plan
  recorded. Footnote added recording the C-1 discharge discrepancy.
- **Ch3 §Study Area** — the sluice inventory at the study cross-sections; the
  absence of any gauge between KP 56.7 and 71.1; the per-reach bed gradients.
- **Ch3 line 753** — precision fix: 38.14 m is the design HWL at the 基準地点
  (KP 56.6), not "at that gauge" (KP 56.7, where it is 38.26 m).
- **Ch4** — the ADR-0032 loading-timescale corroboration from the authority's
  own 17-event concentration-time analysis.
- **Ch7 §Limitations** — the buried-conduit scope gap at the governing section;
  the Chiyoda experimental-channel programme as sourced evidence for where
  empirical effort has gone; the two revetment-flanking erosion observations
  supporting the named missing mechanism.
- No new `references.bib` entry needed: `tokachi_chisuishi_2023` already exists
  and is already romanised with a bracketed English gloss.

---

## 7. Caveats on this review

- Japanese quotations are verbatim from the text layer, spot-checked against
  rendered page images where load-bearing. English renderings are working
  translations, not certified ones.
- Every table quoted as a table (pp71, 268, 613, 642) was **rendered and read
  visually**, not taken from the text layer's column order. Values quoted from
  running prose were taken from the text layer.
- The chainage-offset explanation of the 38.14/38.26 pair (§2.1) is an
  **inference**. The values it reproduces, and the profile that reproduces them,
  are measured.
- The p71 discharge discrepancy (§3) is reported **unresolved**. I could not
  determine the column's definition from the volume and did not construct one.
- §2.2 claims the sluices are absent from the model set. It does **not** claim a
  quantified effect; none is computed here.
- The dam chapters (pp485–532) were judged not relevant and their geotechnical
  values deliberately not carried across. That is a judgement, stated so it can
  be overturned.
