# The 1998 OYO evaluation, the 1999-2003 remediation, and the thesis framing

Date: 2026-08-24. Status: evidence record. No engine default changed, no thesis file edited.

## 1. The question

The thesis opens on an empirical paradox: cross-sections rated deficient in 1998 came
through the August 2016 typhoons without a recorded sand boil, while the neighbouring
Tokoro River piped severely, and "the field record does not resolve which reading is
right". Two worries were raised about that framing:

1. **Does the 1999-2003 remediation trivially explain the 2016 survival**, making the
   paradox an artefact of comparing a pre-works rating against a post-works flood?
2. **Was the 1998 rating actually against foundation piping (BEP)**, or only against
   through-embankment seepage and slope stability?

Both were investigated directly against the source, not against the thesis's own
account of it.

## 2. Sources read

The primary source is the scanned OYO report already in the repository:

`docs/references/平成10年度　十勝川中流部堤防強化対策検討業務　報告書（調査・解析編）.pdf`
(247 pages, no text layer; read by page rendering at 120-320 dpi).

Also read: the per-section MLIT form sets `docs/references/R0*/*` (様式-3 to 様式-7),
`docs/references/帯広市街地の堤防の現状.pdf` (Fukuda current-state sheet), and
PWRI (2014) 河川堤防の浸透に対する照査・設計のポイント for the present-day criteria.

Page offset in the OYO PDF is +5 (report p. 150 = PDF index 155).

## 3. What the 1998 evaluation actually checked

### 3.1 The criteria are stated exhaustively, and there are two of them

Report §6-1 解析内容について (p. 139) enumerates what was computed:

- **(2) 局所動水勾配** — the local hydraulic gradient at the landside toe
  (堤内側法尻部). "動水勾配が 0.5 以上の場合、安定性に問題があり、対策を必要とする
  断面であると評価した."
- **(3) 法面安定性の検討** — circular-slip stability. "川表側法面で Fs=1.1、川裏側
  法面で Fs=1.2 以下の場合、安定性に問題があり、対策を必要とするものと評価した."

The reach-level summary form 様式-1 浸透に対する詳細調査結果総括表 (Tokachi right
bank, 56.0-66.2 km) carries exactly those two criteria as its 安全性の詳細評価結果
block, with four numeric columns:

| 評価対象断面 (km) | すべり破壊に対する安全率 裏のり | 表のり | 局所動水勾配の最大値 鉛直 | 水平 |
|---|---|---|---|---|
| 57.40 | 1.10 | 1.23 | 0.04 | 0.05 |
| 58.80 | 1.15 | 1.48 | 1.30 | 0.62 |
| 60.00 | 1.08 | 1.45 | 0.50 | 0.40 |
| 62.00 | 1.17 | 1.38 | 0.97 | 0.66 |
| 63.40 | 1.10 | 1.26 | 0.28 | 0.45 |
| 65.00 | 1.68 | 1.88 | 0.08 | 0.11 |

**There is no uplift / 浮上り / 盤ぶくれ / G-W column anywhere in the 1998 evaluation.**
Checked in four independent places in the report: §6-1 (the criteria list), 様式-1 (the
reach summary form), 表6-3-1 (the results summary), and §8 まとめ (the report's own
conclusion). None carries one. The 平成9年10月 調査要領 the work follows
(「河川堤防の浸透に対する調査要領：河川局治水課」, named in §5-2) predates the
separate 盤ぶくれ check that PWRI (2014) now lists as the third of three
(のりすべり / パイピング / 盤ぶくれ).

Note that this is a **six**-section right-bank population, not five. KP 65.00 was
evaluated and passes both criteria.

### 3.2 Foundation piping is named explicitly, per section

表6-3-1 解析結果一覧表 (p. 151) carries a 不安定化の要因 (cause of instability)
column:

| KP | 対策工法 | 不安定化の要因 |
|---|---|---|
| 57.4 | 要 | 高水位時の裏法尻部浸潤面の上昇 |
| 58.8 | 要 | 裏法尻部湿潤面の上昇**及び基盤漏水によるパイピング** |
| 60.0 | 要 | 〃 |
| 62.0 | 要 | 〃 |
| 65.0 | 不要 | (blank) |

**基盤漏水によるパイピング = "piping caused by foundation leakage."** This is the
under-levee foundation mechanism, named by OYO themselves, at three of the four
production sections. It is not embankment through-seepage: 図7-2-1 漏水機構の概念図
draws it as flow through the 砂礫 foundation beneath a 粘性土 cap, emerging at the
landside toe, annotated 基盤漏水 in hand.

§6-3's closing paragraph: "法面のすべり破壊及び法尻部の盤ぶくれ、パイピングの発生が
予想される" — slope sliding failure, and **heave (盤ぶくれ) and piping at the toe**,
are the anticipated failure modes. So heave *is* named, as an anticipated mode, but
never computed as a per-section verdict.

§7-2 不安定化の要因 is the clearest statement of mechanism:

> 一方、基盤においても砂礫を主体とすることから、基盤漏水を発生しやすい地盤といえる。
> 解析の結果対策が要と判断されたのは法尻部の局所動水勾配が限界勾配である Ic=0.5 を
> 大きく上回ることにある。このように法尻部の局所動水勾配が上昇する要因としては、
> 透水性の良好な地盤上に分布する沖積粘性土層（Ac 層）の存在によるものと考えられる。

The countermeasure requirement is driven by the toe gradient exceeding Ic = 0.5, and
the cause is identified as the Ac cap over a conductive foundation. That is the
thesis's own configuration, stated by the 1998 investigators.

### 3.3 Verdict on question 2

The 1998 rating covers **both** mechanisms, and the foundation-piping half is explicit
and per-section. The thesis's wording ("deficient against seepage") is accurate and, if
anything, under-claims: it never quotes 基盤漏水によるパイピング.

One necessary qualification, which the thesis already makes in Chapter 2: the Japanese
piping check is an **initiation** criterion (a threshold on an instantaneous exit
gradient), not a progression-to-breakthrough criterion. So "rated deficient against
foundation piping" is right; "rated deficient against backward erosion piping in the
Sellmeijer sense" would not be. The distinction is the thesis's contribution, not a
weakness in the framing.

## 4. The remediation, and whether it dissolves the paradox

### 4.1 The 1998 report designed the works itself

§7 対策工法の検討 is the countermeasure design study. §7-3 states the two required
effects:

1. 堤体中の浸透水を速やかに堤体外に排水し、浸潤線の発達を防ぐ
2. 裏法尻部の水圧の低減により、局所動水勾配の上昇を防ぐ

Effect (2) is precisely the quantity `toe_gradient_relief_factor` (ADR-0050) sweeps.
Reference given: 漏水対策工設計施工指針（案）: 北海道開発局.

Four options were studied (§7-4): ① 法尻ドレーン, ② 法尻ドレーン (Ac層ドレーン化),
③ 裏法緩傾斜盛土 1:4.0, ④ ③+②. Finding: ① secures stability **only at KP 57.4**;
every other section needs the Ac-layer variant ②.

§7-5 地盤条件から見た対策工法 adds the urban land constraint (max ~10 m to the
river-land boundary, mostly ≤4 m downstream of about KP 61) and reports:
KP 57.4 and KP 60.0 are secured by draining the toe alone, whereas **KP 58.8 and
KP 62.0 cannot have their local hydraulic gradient reduced without drainage
penetrating the Ac layer.**

### 4.2 表7-5-1 gives measured post-drain toe gradients

This is the most consequential find. 表7-5-1 対策工検討結果（用地がない場合）
(p. 174) tabulates the *computed* toe gradients after each drain design:

| KP | pre-works i_v | ① 切り込みドレーン (L=3.00 m, k=5.0e-2 cm/s) | ② 切り込みドレーン Ac層抜く (L=4.00 m, 1.00 m into Ac) |
|---|---|---|---|
| 57.4 | 0.04 | 0.04 / 0.05 ○, Fs 1.65 | — |
| 58.8 | 1.30 | 1.13 / 0.49 × | **0.30 / 0.22 ○, Fs 1.83** |
| 60.0 | 0.50 | 0.48 / 0.36 ○, Fs 1.67 | — |
| 62.0 | 0.97 | 0.95 / 0.23 × | **0.23 / 0.19 ○, Fs 1.90** |

Implied vertical-gradient relief:

| KP | drain ① (above Ac) | drain ② (through Ac) |
|---|---|---|
| 57.4 | 0 % | — |
| 58.8 | 13.1 % | **76.9 %** |
| 60.0 | 4.0 % | — |
| 62.0 | 2.1 % | **76.3 %** |

図8-1 gives the drain body: ρt = 2.00 g/cm³, φ = 40°, c = 0, **k = 5.0e-2 cm/s**
(= 5.0e-4 m/s), L = 3.00 m, H = 1.50 m, drawn at all four sections including KP 62.0.

**This bears directly on the Discussion's claim that the drain relief "is fixed by
nothing on record."** For the relief *magnitude* that statement is now too strong: the
1998 report computes it, on its own FEM, at 77 % and 76 % for the Ac-penetrating
design. The thesis's strongest bracket arm — "the drain removes about four fifths of
the exit gradient" — turns out to be almost exactly the OYO design value. The claim
survives in a narrower form: no *as-built* geometry or drain condition is on record,
and 表7-5-1 is a design-stage computation on OYO's own schematization (a continuous
cohesive layer across the whole domain including the foreshore), not a measurement of
what was installed.

### 4.3 Does the remediation explain the 2016 survival?

Partly, and exactly where the survival carries information. The honest position has
four parts:

**(a) The works predate the flood, so the confound is real.** Nothing in the record
contradicts this.

**(b) It cannot be the whole explanation, because KP 62.0 is unreinforced.** KP 62.0
carries the second-worst 1998 gradient (i_v = 0.97), is named 基盤漏水によるパイピング,
is one of the two sections OYO said needed Ac-penetrating drainage, and is allocated
`unreinforced` on four independent lines of evidence (Appendix D). It came through 2016
without a boil.

**(c) But KP 62.0's survival is uninformative anyway.** The 2016 trace there peaked
0.66 m *below* the design HWL, the transient model puts the conditional probability at
effectively zero at that stage, and Phase 2 rejects 0.00 % of the prior. KP 57.4 is the
same story from the other side: the trace *exceeded* design HWL by 0.45 m, but 1998
rated it **passing** on gradient (0.04), and its rejection is 0.07 %.

**(d) So the informative evidence and the competing explanation coincide.** All the
Phase 2 rejection lives at KP 58.8 and KP 60.0 (5.67 % and 3.36 %), and those are
exactly the two drained sections.

The thesis already states (d) and its consequence, in Chapter 6 §"How Much the Survival
Rejects" and again in Chapter 9: the survival was produced by a drained structure while
the likelihood is evaluated on the undrained foundation, so the posterior is tighter
than the observation licenses, the parameter shifts are an upper bound, and the
consequence is bounded by the size of the rejection itself. That argument is correct
and complete. **The gap is one of placement, not of substance** — see §6.

## 5. Errors found in the thesis

Three, all in the treatment of the 1998 table. None touches a computed result.

### 5.1 The "Uplift" column is not in the source

`tab:oyo_1998` (Chapter 3) and `tab:app_safety_summary` (Appendix A) both carry an
**Uplift** column with **fail** at all five sections. The 1998 evaluation has no uplift
criterion (§3.1 above). The claim is load-bearing in five places:

- Chapter 3, §"The 1998 Deterministic Safety Evaluation": "Uplift is flagged as failing
  across all five."
- Chapter 3, §"Levee Performance": "rated every one of the five surveyed cross-sections
  as deficient in uplift"
- Chapter 8 line 184: "Every surveyed cross-section was rated deficient in uplift in 1998"
- Chapter 8 line 937: "The 1998 evaluation rated it deficient in uplift at every
  surveyed section"
- Appendix G line 1333: "rated every surveyed section deficient in uplift and three of
  the five deficient in exit gradient"

The likely origin is §6-3's closing sentence, which does name 盤ぶくれ (heave) as an
anticipated failure mode alongside piping — but as a narrative expectation, not a
per-section verdict.

### 5.2 "KP 57.4 is the one section to pass the gradient check" is wrong

KP 63.4 also passes: 0.28 and 0.45, both below 0.5. The thesis's own table shows both
values unbolded, so the sentence contradicts the table beside it. Two of the five pass.
This also weakens, in passing, the sentence that follows it ("the gradient-failing
sections are those with narrower foreshores"), since KP 63.4 is tabulated as
river-tight and passes — though the thesis refutes the causal reading of that
correlation anyway.

### 5.3 The slope-stability threshold is stated loosely

Appendix A gives "approximately 1.1 to 1.2". §6-1 is explicit and asymmetric: **1.1 on
the riverside slope, 1.2 on the landside slope.** Every tabulated verdict is consistent
with the exact rule, so this is a precision fix, not a verdict change.

## 6. Two things the source supports that the thesis does not yet use

**(a) OYO's own conclusion names exactly the four production sections.** §8 まとめ (3):
"安定性に問題があり、対策を必要とする断面は以下の断面である" — 十勝川右岸 KP 57.4,
KP 58.8, KP 60.0, KP 62.0, all 北帯広築堤. Those are precisely the four cross-sections
carrying a BEP prior. The population is not a convenience selection driven by borehole
coverage; it is the set the 1998 investigators themselves flagged.

§8 (2) also confirms the blanket boundary independently: "十勝川右岸の調査結果に
よれば、KP63.0 付近より下流側には、表層部にシルト〜砂質シルトからなる Ac 層が存在
し" — the Ac layer exists downstream of about KP 63.0, which is why KP 63.4 carries no
piping prior.

**(b) The 1998 design event held HWL for 1.5 hours.** Appendix F already records this
(様式-5, 計画高水位継続時間 1.5 hr, recession 0.29 m/h). The 2016 event held high water
24 to 34 hours. The deficiency rating that the paradox is built on was computed against
a loading two orders of magnitude shorter in the dimension this thesis argues is
governing. The main text notes that the single-peak design hydrograph "cannot
reproduce" the compound signature, but never quotes the 1.5 hours against the 24 to 34.

## 7. Recommendations

Ranked by importance.

1. **Remove the Uplift column** from `tab:oyo_1998` and `tab:app_safety_summary`, and
   rewrite the five dependent sentences. Replace with what the source does say: three of
   the four production sections are named 基盤漏水によるパイピング (foundation-leakage
   piping) as their cause of instability, and the report anticipates 盤ぶくれ (heave) and
   piping at the landside toe as the failure modes. This is a strict improvement — the
   replacement claim is stronger, more specific, and quotable.
2. **Fix "the one section to pass the gradient check"** to two (KP 57.4 and KP 63.4).
3. **Pull the confound forward.** The argument is already correct in Chapters 6 and 9.
   Add one clause to the Summary and one sentence to the Introduction so the reader
   meets the competing explanation at the same time as the paradox, and add
   "the remediation state" to the Chapter 4 list of alternative explanations, which
   currently names blanket attenuation, static resistance, and non-attainment but not
   the works. No result changes.
4. **Anchor the drainage bracket to 表7-5-1.** Soften "fixed by nothing on record" to
   the as-built form, and report the 77 % / 76 % OYO design values as an independent
   corroboration of the strongest bracket arm. This converts a swept endpoint into a
   design-anchored one.
5. **Add the four-section coincidence** (§6a) where the BEP population is justified, and
   the 1.5 h versus 24 to 34 h contrast (§6b) where the compound signature is argued.
6. **State the slope thresholds exactly** (1.1 riverside, 1.2 landside).

## 8. Both flagged items resolved (2026-08-25)

### 8.1 The cover-layer split: CONFIRMED verbatim

JICE (2012) 河川堤防の構造検討の手引き（改訂版）, JICE資料第111002号, p. 47,
表4.2.1 浸透に対する安全性の照査基準 (source now at
`docs/references/Literature/teibou_kouzou02.pdf`, PDF page index 28):

| 項目 | 部位 | 照査基準 |
|---|---|---|
| すべり破壊（浸潤破壊）に対する安全性 | 裏のり | Fs ≥ 1.2 × α₁ × α₂ |
| | 表のり | Fs ≥ 1.0 |
| パイピング破壊（浸透破壊）に対する安全性 | 被覆土 **なし** | **i < 0.5** (i = 裏のり尻近傍の基礎地盤の局所動水勾配の最大値) |
| | 被覆土 **あり** | **G/W > 1.0** (G = 被覆土層の重量, W = 被覆土層基底面に作用する揚圧力) |

The same section states the two verification items as ①洪水時のすべり破壊 and
②洪水時の**基礎地盤の**パイピング破壊 — foundation-ground piping, which independently
corroborates §3.2 above.

The 1998 evaluation applied `i < 0.5` at all sections, including the four with an
$A_c$ blanket of 0.45 to 0.85 m, i.e. the **被覆土あり** row. The mechanism current
guidance would verify there — blanket uplift via G/W, which is this engine's initiation
gate — was never checked. Written into the thesis at Chapter 3
§"The 1998 Deterministic Safety Evaluation" and Appendix A.

### 8.2 The §6-3 scoping reading: REFUTED, no thesis change made

The hypothesis was that the §6-3 sentence naming only "KP58.8〜KP62.0区間の断面" is
scoped to the gradient-driven problem, with KP 57.4 needing works on slope stability
alone. **It does not survive checking.** The sentence reads in full:

> 解析結果によれば、安定上問題を生じ、対策が必要と考えられる断面は十勝川右岸の内、
> KP58.8〜KP62.0区間の断面で、**不安定箇所は川裏側法面である**。

The unstable location it names is the **landside slope** — precisely the criterion
KP 57.4 fails (Fs = 1.104 against a 1.2 threshold). A gradient-scoped reading would have
named the toe (法尻部), and it does not. The sentence is therefore inconsistent with
four other statements in the same report, all of which include KP 57.4: 表6-3-1 (marked
要), 表7-4-1 (secured by option ① or ③), §7-5 (secured by draining the toe), and §8
まとめ (listed first of four).

Action taken: the thesis cites §8 まとめ as the authority for the four-section list and
does not quote §6-3. Appendix A records the inconsistency in one sentence so a reader
who goes to the source is not caught by it.
