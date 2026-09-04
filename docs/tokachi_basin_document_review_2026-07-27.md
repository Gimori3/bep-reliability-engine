# Tokachi basin document review — `docs/references/tokachi_river_basin/`

**Date:** 2026-07-27
**Scope:** exhaustive scan of the 11 PDFs in the (gitignored) folder
`docs/references/tokachi_river_basin/` for material relevant to the BEP thesis
(`msc-thesis`) and the reliability engine (`bep-reliability-engine`).
**Method:** full text extraction via PyMuPDF (10 of 11 PDFs carry a text layer;
one is image-only and was read visually), keyword sweep over the Japanese
seepage/piping/geotechnical vocabulary, then full or targeted deep reading.
Cross-checked against the current thesis chapters and `references.bib` to
separate genuinely new material from what is already integrated.

Page citations are **PDF page numbers** unless a printed page is given as
`(printed NN)`. The 816-page volume has an irregular PDF↔printed offset
(unnumbered plates), so PDF numbering is authoritative here.

---

## 0. Document inventory

| # | File | Document | Publisher / date | Pages | Text layer |
|---|---|---|---|---|---|
| D1 | `syousasekkei_point1407.pdf` | 河川堤防の浸透に対する照査・設計のポイント<br>*Points for verification and design of river levees against seepage* | 独立行政法人土木研究所 地質・地盤研究グループ 土質・振動チーム (**PWRI**), 2014-07 | 66 | yes |
| D2 | `shintou_suibou.pdf` | 浸透に係る重要水防箇所設定手順（案）<br>*Procedure (draft) for designating important flood-fighting locations related to seepage* | 一般財団法人 国土技術研究センター (**JICE**), 2019-03 | 21 | yes |
| D3 | `inr9av000000b2i3.pdf` | 続十勝川治水史 (電子版)<br>*Continued history of Tokachi River flood control* | 北海道開発局 帯広開発建設部, 2023-10 (令和5年10月) | **816** | yes |
| D4 | `inr9av000000b2a9.pdf` | 続十勝川治水史 — front matter + full table of contents | ditto | 18 | yes |
| D5 | `ctll1r0000001cmh.pdf` | 堤防詳細点検結果情報図について<br>*About the levee detailed-inspection result information maps* | 帯広開発建設部, status as of 2008-03 (平成20年3月) | 4 | yes |
| D6 | `ctll1r0000001cp9.pdf` | 十勝川下流堤防詳細点検結果情報図（中間報告）<br>*Tokachi downstream levee detailed-inspection result map (interim)* | 帯広開発建設部, 2008-03 | 1 (map) | mojibake; read visually |
| D7 | `ctll1r0000001cpo.pdf` | 札内川堤防詳細点検結果情報図（中間報告）<br>*Satsunai levee detailed-inspection result map (interim)* | 帯広開発建設部, 2008-03 | 1 (map) | mojibake; read visually |
| D8 | `inr9av0000006kyo.pdf` | 十勝川水系河川整備計画（原案）への記載案<br>*Draft entries for the Tokachi River System River Improvement Plan* | 北海道開発局, 2009-06 | 28 | yes |
| D9 | `inr9av000000axbe.pdf` | 十勝川治水100年 (slide/panel deck) | 帯広開発建設部, 2023-10 | 32 | yes |
| D10 | `inr9av000000ay5o.pdf` | 十勝川治水100年 (print-spread version of D9) | ditto | 16 | **image-only** — read visually |
| D11 | `no648_disaster.pdf` | 2016年8月豪雨災害と土木学会調査団の活動経緯 (自然災害に備える 第4回)<br>*JSCE investigation team report on the August 2016 Hokkaido rainfall disaster* | 中津川誠 (Nakatsugawa, Muroran IT), 2017-07 | 6 | yes |

**Headline assessment.** D1 and D2 are the two most valuable finds: they are the
**authoritative Japanese doctrine documents for exactly the failure mechanism
this thesis models**, and neither is currently cited. D3 is a 816-page
Tokachi-specific goldmine containing hard hydrological data, the official 2016
breach attributions, and the levee remediation history. D5–D7 are the official
seepage-safety screening of the study levees. D11 contains an authoritative
statement that **directly contradicts the thesis's Phase 3 BEP-dominance
conclusion** and must be engaged with.

---

## 1. Japanese seepage doctrine — the biggest literature gain (D1, D2)

The thesis's Chapter 2 currently contrasts the Dutch progression-based framework
against a "Japanese instantaneous gradient check" characterised largely through
Fukuoka et al. (2019) and Tabata/Fukuoka papers. D1 and D2 are the **official
standards themselves**. Adding them upgrades that comparison from
inferred-from-papers to sourced-from-doctrine.

### 1.1 The official Japanese seepage-verification criteria (D1 p16, printed 14)

The three checks performed under 河川堤防設計指針 (2002, rev. 2007) and
河川堤防の構造検討の手引き:

| Mechanism | Criterion |
|---|---|
| Slope sliding (のりすべり) | circular-slip safety factor $F_s \ge 1.2 \times \alpha$ |
| **Piping (パイピング)** | **local hydraulic gradient ≤ critical hydraulic gradient** |
| **Uplift/heave (盤ぶくれ)** | **uplift pressure on the blanket base ≤ the blanket overburden-thickness equivalent** |

**→ Action.** Cite D1 as the primary source for the Japanese verification triad
in Ch2 (replacing/supplementing the inference from Fukuoka). The heave criterion
is *literally* the thesis's $Z_\text{uplift}$ and the ADR-0008 Terzaghi gate —
state this equivalence explicitly, because it makes the Japanese comparator a
formal special case of the engine's initiation gate rather than a different
model. New bib entries: `pwri_2014`, `jice_2019`.

### 1.2 The operational screening thresholds (D2 pp19–20, printed 19–20)

For **foundation leakage (基礎地盤漏水)**, designation as an important
flood-fighting location (重要水防箇所) class A/B uses:

- **$G/W \le 1$** where blanket present — $G$ = weight of the blanket layer,
  $W$ = uplift pressure acting on the blanket base;
- **local hydraulic gradient $i \ge 0.5$** where no blanket present.

For **embankment leakage (堤体漏水)**: $t^* \ge 0.01$ or $F_s$ failing the check
(D2 p9, printed 9).

**→ Action.** These are hard, quotable numbers for the Ch2 comparison table and
for the Ch7 discussion of how the engine's continuous $P_f$ maps onto a
binary Japanese screening class. Note especially that $G/W \le 1$ is exactly
$Z_\text{uplift} \le 0$ — so **the Japanese screening threshold is the engine's
uplift limit state with a unit safety factor**. That is a genuinely strong
framing sentence for Ch2 and Ch7.

### 1.3 The 3 m blanket exemption rule (D1 p39 printed 37; D2 p20 printed 20)

> 堤防高が10m以下で、被覆土層厚が3m程度以上の場合や粘性土地盤の場合には
> パイピング破壊・盤ぶくれに対する安全性の照査は**原則的に不要**

*Where levee height ≤ 10 m and blanket thickness ≳ 3 m, or the foundation is
cohesive, piping/heave verification is in principle unnecessary.*
D2 §5.3 restates it as a screening exclusion: if a cohesive blanket extends
≥ 3 m from the surface, the section is excluded **even if a permeable layer
lies beneath**.

**Cross-check against the engine.** `data/processed/tokachi_bep_inputs.csv`
$D_{bl}$ values are 0.80, 0.85, 0.85, 0.45, 1.0 m — **all far below the 3 m
exemption**. So Japanese doctrine would require piping verification at every one
of the thesis's sections. This is a **favourable and important corroboration**:
the study sections are not exempt under the host country's own rules.

**→ Action.** Add to Ch3 §Bipartite Stratigraphy, as an independent
doctrinal justification that these sections are legitimately in scope for piping
assessment. Also add to Ch7 as the counterfactual: had the blanket been ≥ 3 m,
Japanese practice would have screened these sections out entirely, whereas the
engine would still return a finite $P_f$ — a concrete illustration of the
screening-vs-reliability gap. Note the organic-soil caveat (D1 p39: peat/organic
blanket ⇒ $G$ small ⇒ caution), which matters because peat is widespread in the
lower Tokachi.

### 1.4 The evaluation instant is the end of the high-water duration (D1 p36, printed 34) — **CLAIM RETRACTED, see below**

> すべり・パイピングの照査は**高水位継続時間終了時点**で実施

*Slide and piping verification is performed at the point of termination of the
high-water duration.*

> **RETRACTION (2026-07-27).** The original version of this section concluded
> that the thesis mischaracterises the Japanese check as instantaneous, and that
> the correct like-for-like comparator is therefore the ADR-0040 sustained-peak
> limit C3a/C3b. **Both conclusions were wrong and are withdrawn.** The thesis
> was already correct. No relabelling of the Stage 6.6 ladder should be made.

**Why the original inference failed.** Two errors compounded.

1. *The thesis never claimed a steady-state seepage field.* Ch2
   §"Japanese Levee Verification Practice: Advanced Hydraulics, Static Failure
   Criterion" states that engineers "perform two-dimensional transient
   saturated–unsaturated seepage analysis using actual flood hydrographs", and
   the Introduction says explicitly: "Loading is modeled as a dynamic process
   while failure is judged as an instantaneous one." That is exactly what D1/D2
   describe. The word *instantaneous* in the thesis qualifies the **criterion
   form** (a threshold on a snapshot), not the *choice* of snapshot. D1 p36 only
   fixes *which* snapshot, so it refines a detail without touching the claim.
2. *C3a/C3b is not the Japanese comparator.* The Japanese piping check is an
   **exit-gradient / uplift (initiation)** criterion — in engine terms the M5
   gate. C3a/C3b is defined as `heave gate ∧ H_erosion > H_c,trans`, which
   embeds **Sellmeijer's critical head**, a quantity that does not appear in the
   Japanese check at all. Mapping one onto the other conflated the *evaluation
   instant* axis with the *limit-state* axis.

**What the passage does legitimately add.** Duration enters the Japanese
assessment through the *pore-pressure field* (a longer high-water period raises
the phreatic surface and steepens toe gradients) but not through the *erosion
process* (no state variable for accumulated erosion; a finite exceedance is
indistinguishable from an unbounded one). That is a sharpening of the thesis's
existing framing, worth one clause, and nothing more.

**→ Action (revised, low priority).** Add the evaluation-instant detail and the
mesh-size/phreatic-line requirements as procedural precision in Ch2. Make **no**
change to the Stage 6.6 comparator labelling, and **no** change to the
static–transient gap narrative. *Status: done — Ch2 augmented, and the two
procedural details recorded without disturbing the surrounding claim.*

### 1.5 The $t^*$ formula — discrepancy with the thesis (D2 p13, printed 13)

D2 gives the official operational form (verified by rendering the equation
image, not from the text layer):

$$t^* = \frac{8\,k\,H(t)\cdot(t-t_0)}{3\,\lambda\,b(t)^2}$$

**The thesis (`2. Theoretical and Empirical Foundations.tex:78`) writes
$t^* = \frac{5}{2}\frac{kHt'}{\lambda b^2}$** — coefficient 5/2 = 2.5 versus
JICE's 8/3 ≈ 2.667.

> **RESOLVED (2026-07-27) — the thesis is correct.** Fukuoka et al. (2019) was
> obtained (`docs/references/2019-suiko-fukuoka.pdf`) and its Eq. (1) rendered
> from the page image: it reads $t^* = \frac{5}{2}\frac{kHt'}{\lambda b^2}$,
> matching the thesis exactly. No change to the coefficient was required.

The two published forms are therefore both genuine, and the difference is not an
error in either. They also carry **different reference definitions**, which is
the likely origin of the differing constant: Fukuoka measures $H$ above the
high-water bed, $t'$ from the flooding of that bed, and $b$ as the levee base
width, whereas JICE measures $H(t)$ from the **landside toe elevation**,
$(t - t_0)$ from the moment the stage first reaches the **higher of the two
toes**, and $b(t)$ as the horizontal distance from the water-line intersection
with the riverside face to the landside toe. A different length scale yields a
different constant.

**→ Action.** Keep 5/2, cite `fukuoka_tabata_2018` as the derivation of record,
and note the operational variant. *Status: done — Ch2 now states both forms, the
$\lambda = 0.4$ and max(Hazen, Creager) conventions, and the $t^* \geq 0.01$
extraction threshold.*

D2 also supplies **operational precision the thesis currently lacks**:

- $t_0$ = the time at which, **within one flood**, the river level *first*
  reaches **the higher of the two toe elevations** (both riverside and landside
  toes are considered; D2 p16, printed 16).
- $H(t)$ = height difference between river level and the **landside** toe
  elevation.
- $b(t)$ = horizontal distance between the point where the water level
  intersects the **riverside slope face** and the **landside toe**.
- $\lambda$ = **porosity, taken uniformly as 0.4** (D2 p16, printed 16).
- $t^*$ is evaluated time-step-wise and **the maximum over the flood** is the
  section's representative value; that maximum "often appears just after the
  peak water level" (D2 p17, printed 17).
- Threshold **0.01**, with extraction extended to the adjacent
  below-threshold distance markers for conservatism (D2 p17, printed 17).
- **Gravel levees (礫堤防) are excluded from $t^*$ screening** because $t^*$ is
  permeability-driven and would flag gravel levees as most dangerous, yet no
  gravel-levee embankment-leakage failure case exists (D2 p11, printed 11).
  Definition: gravelly soil excluding the surface 30–50 cm cover; where fill
  history is mixed, judged on the landside-toe soil.

**→ Action.** Tighten the Ch2 $t^*$ paragraph with these definitions.
Two items are directly load-bearing for the thesis:
- The **"maximum just after the peak"** property is an independent,
  officially-documented Japanese statement that **the critical moment lags the
  peak** — this corroborates the thesis's core time-dependence argument from
  within Japanese practice. Quote it.
- The **gravel-levee exclusion** is important: the Tokachi levees *are* built of
  local sand-gravel (see §3.2). So $t^*$ screening formally does not apply to
  them, which both explains why Fukuoka et al. applied it to the wide *lower*
  reach and limits how far the thesis can lean on $t^*$ for the study sections.
  State this limitation explicitly in Ch2.

### 1.6 The official BEP mechanism description (D1 p5, printed 3)

> 河川水位が上昇し川裏のり尻付近の動水勾配が高まると、浸透破壊が起き、噴砂が
> 始まる。堤内地盤に被覆土層が存在する場合には被覆土層下面に圧力が作用し、
> ある程度大きくなると盤ぶくれが生じる。さらに圧力が大きくなると被覆土層が
> 破れ、漏水・噴砂が生じる。このような噴砂が継続すると、**徐々にパイプ状の
> 水みちが川表側に向かって形成される**。漏水・噴砂は勢いを増し、堤防にとって
> 有害な空洞が堤防下に形成される。

This is the **retrogressive (backward) erosion piping mechanism stated verbatim
in Japanese official doctrine**: uplift → blanket rupture → sand boil →
progressive formation of a pipe-shaped flow path *toward the riverside* →
cavity beneath the levee.

**→ Action (high value for Ch1/Ch2).** The thesis's framing benefits enormously
from being able to say that Japanese doctrine *recognises the same
retrogressive mechanism* but implements it as a threshold check rather than a
progression model. This is a much stronger position than "Japanese practice
uses a different (gradient) model". Quote D1 p5 in Ch2 and reference it in the
Introduction's problem statement.

### 1.7 The Japanese variation-progression process diagram (D2 p2, printed 2, Fig. 1.1)

Rising river level + rainfall branches into:

- **blanket present** → 盤膨れ (heave) → 基礎地盤パイピング (foundation piping)
  → 漏水・噴砂 (leakage/sand boil)
- **blanket absent** → 基礎地盤・噴砂
- seepage reaching beneath the landside toe → 堤体湿潤化 → 堤体パイピング
  *(shown dashed)* / のり面の変状 → のり面のすべり / のり面のはらみ出し
  → 天端陥没 (crest settlement)

With the critical annotation:

> 直轄河川においては、堤体からの漏水・噴砂は確認されているものの、このような
> 変状から天端陥没等の変状に至った事例は**確認されていない**

*In directly-managed rivers, embankment leakage and sand boils HAVE been
observed, but no case has been confirmed of such deformation progressing to
crest settlement.*

**→ Action (high value for Ch1/Ch2/Ch7).** This is an official,
nationwide-scope empirical statement that **initiation is observed but
completion is not** — precisely the thesis's central physical claim
(initiation ≠ breach; progression is duration-limited). It is a stronger form
of the same evidence the thesis currently draws from Gounokawa and Yabe.
Reproduce Fig. 1.1 (or redraw it) in Ch2 as the Japanese counterpart to the
Dutch fault tree, and cite the annotation in the Introduction.

### 1.8 The 200 m distance-marker interval (D2 p7 printed 7, p13 printed 13)

- 堤防形状: cross-section survey collected at **≈200 m intervals**.
- $t^*$ computed **at distance markers (200 m interval as standard)**.
- Borehole investigations exist at **200–400 m intervals** along the levee
  where survey density is high (D1 p22, printed 20).

**→ Action.** This is a **citable doctrinal justification for the thesis's
200 m segment discretisation** (Phase 3 / ADR-0037 / ADR-0043), which currently
rests on the rating-grid spacing and Uemura's own segmentation. Add to Ch3
§Spatial Scope and to the ADR-0037/0043 provenance discussion. It also
independently supports the seepage-length-L study's finding that the production
`exact` policy (sections 1.2–2.0 km apart) is far coarser than doctrine assumes.

### 1.9 Permeability determination conventions (D1 pp23, 56–58; D2 pp14–15)

- **For $t^*$, use the SIMPLE arithmetic mean of layer permeabilities, not the
  log-mean** — because for flow parallel to layering the most permeable layer
  governs, and $k_{Ave} = (k_1H_1 + k_2H_2)/(H_1+H_2)$ is then exact (D2 p14,
  printed 14). Design practice otherwise conventionally log-averages.
- Preference order: field permeability tests → laboratory tests → **only if
  neither, grain-size estimation** (D2 p15, printed 15).
- Grain-size methods in the D1 appendix:
  - **A5 Hazen**: $k = C_k \cdot 0.7(0.03 + t) \cdot D_{10}^2$ (cm/s, cm),
    $C_k$ = 150 uniform grains / 116 loose fine sand / 70 well-packed fine sand
    / 60 mixed sand / 46 dirty grains.
  - **A6 Creager**: a full $D_{20}$ → $k$ lookup table, 28 rows from
    $D_{20}=0.005$ mm ($k=3.0\times10^{-6}$ cm/s) to $D_{20}=2.00$ mm
    ($k=1.8$ cm/s). Selected rows: 0.10 mm → 1.75e-3; 0.20 → 8.90e-3;
    0.30 → 2.20e-2; 0.50 → 7.50e-2; 1.00 → 3.60e-1 cm/s.
  - **A7 Fukuda–Uno**: uses uniformity coefficient $U_c$, $d_{50}$ and void
    ratio $e$; $\ln \sigma_w = 0.484 + 0.420\ln U_c$ then a mean pore diameter.
- **A4** gives the standard $k$-vs-soil-type chart in **m/s**
  ($10^{-11}$ to $10^{0}$), with test-method applicability.
- Observed scatter guidance (D1 p22, printed 20): **permeability scatter is a
  factor of several to ~10**; density scatter **± 0.1 g/cm³**.

**→ Actions.**
1. **Ch3 §Prior Parameter Distributions:** the ± 0.1 g/cm³ density scatter
   translates to ≈ 5 % on total unit weight, which **independently corroborates
   the thesis prior CoV($\gamma'_{bl}$) = 0.056**. Cite it.
2. **CoV($k_{aq}$) = 0.50 needs a comment.** A lognormal with CoV 0.50 spans
   only ≈ a factor of 2.9 at 95 %, whereas doctrine describes observed
   permeability scatter as a factor of several to ~10. Either defend 0.50 as
   *within-layer at a section* (as opposed to between-site) or add a bounding
   sensitivity. This is a genuine and answerable reviewer question — see also
   §2.1 below, where the measured Tokachi aquifer $k$ range sits above the
   prior's 95th percentile.
3. **Engine, optional:** the Creager table is a ready-made independent
   $d\!\to\!k$ relation. The ADR-0012 $k_{aq}$–$d_{70}$ analysis
   (`docs/decisions/adr0012-kaq-d70-analysis.md`) could be cross-checked
   against it as a companion. Creager uses $D_{20}$, not $d_{70}$, so this is a
   *consistency check on the OYO pairs*, not a substitute relation. Low
   priority; do not change any default.
4. **Ch4/Ch7:** the arithmetic-vs-log averaging convention is a nice concrete
   example of Japanese practice deliberately choosing the conservative
   aggregation for a duration-sensitive index. Worth one sentence.

### 1.10 Nationwide seepage-deficiency statistics (D1 p3 printed 1, p34 printed 32)

From the detailed inspection of ~10,000 km of directly-managed levees
(治水課 survey, **as of 2011-01**), Fig. 6.3.1:

| Outcome | Share |
|---|---|
| ① all checks OK | 59.2 % |
| ② all NG | 1.5 % |
| ③ landside slope + piping NG | 9.5 % |
| ④ landside + riverside NG | 2.0 % |
| ⑤ riverside + piping NG | 0.3 % |
| ⑥ landside only NG | 13.1 % |
| **⑦ piping only NG** | **13.8 %** |
| ⑧ riverside only NG | 0.5 % |

⇒ **piping-related failure of the check: 25.1 %** of Japan's directly-managed
levee length. D1 p3 separately records that the first publication of the
verification results rated **just over 30 %** of the ~10,000 km as weak
sections. D1 p34 also notes that nationwide the most common reasons for
requiring works are **landside slope sliding and landside-toe piping failure**.

**→ Action (Introduction, high value).** This is the Japanese counterpart to
whatever Dutch figure the thesis uses for piping-driven safety deficiency. It
lets the Introduction state the scale of the problem in *both* jurisdictions
with sourced numbers, which materially strengthens the motivation. Use the
25.1 % piping figure with its 2011-01 date and 10,000 km denominator.

### 1.11 Field interpretation of "leakage observed" (D1 p33, printed 31)

Two distinct meanings, requiring different responses:
1. **Clear water** — no piping-failure risk; the *leakage discharge can be
   measured to back-calculate the embankment permeability*.
2. **Turbid, sediment-carrying water** — piping / internal erosion concern;
   worst case a cavity (piping hole) exists and its extent must be investigated.

**→ Action.** Directly relevant to how the thesis interprets historical leakage
records as evidence. Phase 2 currently conditions on *survival* (no breach),
which is safe; but if any leakage records are later used as observations, this
taxonomy is the standard for admitting them. Add to Ch3 §2016 section and to
the Ch7 discussion of what the survival observation does and does not license.

### 1.12 Countermeasure-to-mechanism mapping (D1 p35 printed 33, Table 7.1.1)

For 盤ぶくれ・パイピング (heave/piping) specifically:

| Method | Physical effect |
|---|---|
| 断面拡大工法 section enlargement | ① lengthen seepage path (lower gradient) ② gentler slope → stability |
| ドレーン工法 drain | ① reduce hydraulic gradient at the landside toe |
| 川表遮水工法 riverside cutoff (sheet pile) | ① lengthen seepage path ② reduce foundation water pressure near landside toe |
| ブランケット工法 blanket | ① reduce foundation seepage flow ② reduce pressure near landside toe |
| 堤内基盤排水工法 landside foundation drainage | ① reduce uplift at the landside toe |
| 天端舗装工 crest paving | ① reduce infiltration into the embankment |

Design details worth recording:
- **Drain**: thickness ≥ 0.5 m; width set so the *average hydraulic gradient is
  < 0.3*; filter on the embankment side; most effective when embankment
  $k \approx 10^{-3}$–$10^{-4}$ cm/s, ineffective at $5\times10^{-2}$ or
  $5\times10^{-5}$ cm/s (D1 pp44–45, printed 42–43).
- **Riverside cutoff**: to reduce the landside local gradient, **penetration
  must reach ≥ 90 % of the permeable-layer thickness**; Fig. 11.1.2 gives the
  $i/i_0$ versus penetration-ratio curve. Ineffective where large gravel or
  cobbles deform the sheet pile, or where the permeable layer is laterally
  extensive so flow wraps around the ends (D1 pp49–50, printed 47–48).
- **Blanket**: needs **≥ 30 m width** to be effective; ≥ 50 cm thickness if of
  soil; must normally be combined with riverside slope covering (D1 p51,
  printed 49).

**→ Action (this is the concrete answer to the `remediation_state` caveat).**
The engine's `remediation_state` column is currently "a label, not physics"
(architecture and decision records; `docs/phase2_report.md` §11), which is the single most awkward
caveat in the Phase 2/Phase 3 story. Table 7.1.1 tells you exactly which
engine quantity each Japanese countermeasure changes:

| Tokachi remediation | Engine handle |
|---|---|
| berm / section enlargement | increases $L$ (seepage length) |
| landside-toe drain | reduces the exit gradient → acts on the uplift/heave gate |
| foreland blanket | increases the foreland leakage credit → reduces $r_e$ (already the ADR-0025 `blanketed_tanh` baseline) |
| riverside sheet-pile cutoff | increases effective $L$ *only if* penetration ≥ 90 % $D_{aq}$ |

Recommended follow-up: a **default-OFF, opt-in remediation sensitivity** in the
engine (per `bep-change-control`: new knob ⇒ default-OFF and bit-identical
baseline, `to_metadata()` must drop `None` to preserve config hashes for the
Phase 2 replay gate). This converts the `drained` / `berm-only` labels at
KP58.8/60.0/57.4 into a *measured* $\Delta P_f$ bracket, in the same pattern as
the KP58.8 $r_e$-halved QA member. **Do not change any default.** Given the
campaign is closed, the honest minimum is to document the mapping in Ch7 and
state the direction of the bias; the opt-in member is a stretch goal.

Also note the **30 m blanket-width rule**: the engine's `foreshore_width_m` is
200 / 325 / 600 / 44 / 0 m. KP62.0 at 44 m is only just above the doctrinal
minimum, and KP63.4 at 0 m is below it — consistent with ADR-0025's finding
that KP62.0's foreland treatment is the sensitive one.

### 1.13 Blocked-hinterland ("dead-end") foundation structure (D1 p32, printed 30)

> 透水性地盤において裏のり尻下や堤内地盤側に粘性土等の難透水層が分布して
> いると、いわゆる**行止り地盤**を形成し、湿潤面を押し上げ、漏水やパイピング
> が発生しやすい

Figures 6.2.1–6.2.3 illustrate three vulnerable layer structures: a
low-permeability old levee combined with a permeable widening; a permeable layer
sandwiched inside a low-permeability embankment; and the dead-end foundation.

**→ Action.** This bears on the ADR-0006 hinterland-extent treatment. The
engine resolved hinterland extents "conservative" and records semi-infinite
status in `metadata['leakage_geometry']`. Japanese doctrine flags the *opposite*
configuration — a **blocked** hinterland — as the more dangerous one, because
it pushes the phreatic surface up rather than letting head bleed away. Worth a
Ch4/Ch7 sentence acknowledging that a semi-infinite hinterland is not
unconditionally conservative, and a cross-check of whether any study section has
a landside low-permeability barrier. If one does, that is a genuine
non-conservatism in M4 worth documenting as an open problem.

### 1.14 Local-gradient evaluation practice (D1 p38, printed 36)

- FEM element size must be **≤ ~1/10 of the levee height** — the computed local
  gradient is mesh-dependent.
- The evaluation point must lie **below the phreatic line** (no piping above it).
- Vertical-only where a retaining wall precludes horizontal piping at the toe,
  conditional on the wall backfill draining properly.
- $G/W$ must be evaluated at the position where it is **smallest** (D1 p39,
  printed 37).

**→ Action.** Ch2/Ch7 footnote: the Japanese gradient criterion is
mesh-resolution dependent, which is a structural disadvantage relative to the
engine's analytic formulation. This is a fair, sourced point in the engine's
favour and worth one sentence in the Discussion.

### 1.15 Reference flood durations used in PWRI trial calculations (D1 p33, printed 31)

PWRI's own seepage trial calculations use **20 h / 40 h / 75 h** durations, with
layer permeabilities $k = 3.0\times10^{-2}$ (high-permeability layer),
$2.0\times10^{-3}$ (homogeneous), $1.0\times10^{-4}$ cm/s (low-permeability old
levee).

**→ Action.** Ch4/Ch5 context for the timestep and duration discussion. Compare
to ADR-0032's measured Tokachi loading (median $T_\text{rise}$ 18 h, plateau
9 h) — the Tokachi event is at or below the *shortest* duration PWRI trials,
which supports the ADR-0032 conclusion that the loading "is not flashy" in the
lag sense while still being short in the *progression* sense.

---

## 2. Tokachi-specific quantitative data usable by the engine (D3)

### 2.1 Floodplain aquifer properties at Chiyoda (D3 p359, printed 337) — **highest-value engine datum**

From the Chiyoda new-channel groundwater investigation (observations from 1983,
well census 2001-11):

> 帯水層は、概ね**砂礫層（厚さ15～20m 程度）**で構成され、**透水係数は
> $10^{-1}$～$10^{0}$ cm/s** と高い（浸透しやすい）ことが確認された

- **Aquifer: sand-gravel, thickness 15–20 m**
- **Permeability $10^{-1}$–$10^{0}$ cm/s = $1\times10^{-3}$–$1\times10^{-2}$ m/s**
- Groundwater table **2–4 m below ground surface** in the Aikawa/Senju hinterland
- Regional groundwater flow parallel to the Tokachi, west → east; the Chiyoda
  weir induces a pronounced **bypass seepage flow (迂回浸透流)**: upstream of
  the weir the river recharges the hinterland farmland, downstream the flow
  reverses toward the river
- A groundwater contour map + flow net (1983-04-23) exists as a figure
- 68 wells in 2001-11; 22 within the predicted ≥ 0.5 m drawdown zone; new
  channel cut 4–5 m below the pre-works groundwater level; max predicted
  drawdown ≈ 3 m

**Comparison with the engine's priors:**

| | Engine (`tokachi_bep_inputs.csv`) | Chiyoda measurement |
|---|---|---|
| $D_{aq}$ | 7, 8, 9, 10, 11 m | **15–20 m** |
| $k_{aq}$ | 3e-3, 2e-3, 1e-3, 1e-3, 6e-5 m/s | **1e-3 – 1e-2 m/s** |

**Both are higher than the engine's central values.** With mean $k_{aq}$ = 3e-3
and CoV 0.50, the lognormal 95th percentile is ≈ 5.8e-3 m/s, so the **upper end
of the measured Chiyoda range (1e-2 m/s) lies beyond the prior's 95th
percentile**.

**Caveat that must be stated:** Chiyoda is at **KP 37.6**, ~20 km downstream of
the study sections (KP 57.4–63.4), in a different geomorphic setting. This is
*corroborating regional evidence*, not a substitute for the OYO section data.

**→ Actions.**
1. **Ch3 §Bipartite Stratigraphy / §Geotechnical Dataset:** add as independent
   regional corroboration that the Tokachi floodplain aquifer is a
   high-permeability sand-gravel unit — this is exactly the physical setting the
   thesis's $A_g$ layer represents, sourced from an official investigation
   rather than only the OYO logs.
2. **Ch3 §Prior Parameter Distributions + Ch7:** state explicitly that the
   measured regional $k_{aq}$ band extends above the prior's 95th percentile,
   and that this makes the prior **non-conservative at the upper tail** for
   $k_{aq}$ (higher $k_{aq}$ ⇒ lower Sellmeijer critical head ⇒ higher $P_f$).
   Pair it with the CoV question raised in §1.9.
3. **Engine (optional, opt-in only):** a $k_{aq}$ upper-bracket sensitivity
   member reusing the pattern of the ADR-0046 z_toe companion — a
   *scenario*, not a prior change. Do **not** touch the CSV or the generated
   configs; the drift guard (`tests/test_configs.py`) pins them to the CSV and
   ADR-0012/0023.
4. **Ch4 / ADR-0006 note:** the 2–4 m hinterland groundwater depth and the
   documented bypass-seepage pattern are direct evidence about M4's hinterland
   boundary condition. The observed reversal of flow direction across the weir
   also shows the hinterland head is not a passive far-field constant. Worth a
   sentence on the limits of the Mazure semi-infinite schematisation.

### 2.2 Water-level gauge inventory (D3 pp613–614, printed 585–586; catchments p605, printed 577)

Status April 2022 (令和4年4月). Selected rows relevant to the thesis:

| River | Station | KP (距離標, km) | Catchment (km²) | Record start |
|---|---|---|---|---|
| Tokachi | 芽室太 Memurobuto | 71.1 | 1546.4 | **1908-05** |
| Tokachi | **帯広 Obihiro** | **56.7** | **2677.8** | **1907-01** |
| Tokachi | 十勝中央大橋 | 48.4 | 4482.8 | 2005-02 |
| Tokachi | 千代田 Chiyoda | 37.6 | 5081.5 | 1915-07 |
| Tokachi | 茂岩 Motoiwa | 21.0 | 8276.9 | 1916-04 |
| Tokachi | 旅来 Tabikorai | 9.3 | 8338.7 | 1903-05 |
| Tokachi | 大津 Otsu | 3.2 | 8379.5 | 1903-05 |
| Otofuke | 音更 Otofuke | 9.1 | 707.9 | 1910-08 |
| Satsunai | 第二大川橋 | 20.7 | 580.0 | 1960-07 |
| **Satsunai** | **南帯橋 Nantaibashi** | **15.0** | **608.1** | **1951-10** |
| **Satsunai** | **札内 Satsunai** | **4.0** | **698.9** | **1911-12** |
| Totabetsu | 戸蔦橋 | 13.7 | 160.6 | 1956-09 |
| Obihiro R. | 東3条 | 2.2 | 181.0 | 1984-04 |

**→ Actions.**
1. **Ch3 §d4PDF / data provenance:** the Obihiro gauge is at **KP 56.7**,
   catchment **2,677.8 km²**, with a record from **January 1907** — a 115+ year
   observed record. The thesis uses Obihiro stage as the entry point of the M3
   inverse-rating chain (ADR-0035); pinning the KP and catchment removes an
   ambiguity, and the record length is worth stating.
2. **Phase 3 Satsunai gauge choice — engine-side open item, deliberately NOT
   carried into the thesis.** *Decision (2026-07-27): the thesis does not assess
   the Satsunai for BEP, so this needs no thesis text. It is retained here as a
   durable engine record in case those sections are later brought into the
   analysis.* The Phase 3 Satsunai
   sections are **KP 7.0, 6.4, 5.2, 4.2**, and the rating chain uses the
   **Nantai (南帯橋, KP 15.0)** gauge (ADR-0042 dec. 6, `WL_ERR_BY_RIVER`).
   But there is a **closer gauge — 札内 at KP 4.0, record from 1911** — sitting
   *inside* the Phase 3 Satsunai reach. Nantaibashi is 8–11 km upstream of the
   sections it is being used for. Two things follow:
   - Verify whether Uemura's `df_river.csv` / `Uncertainty_HQrelation.xlsx`
     genuinely keys the lower-Satsunai nodes to Nantai, or whether the
     Satsunai-gauge choice is an artefact of which sheet was available. The
     D7 closure measured the Satsunai←Nantai rating error as
     N(−0.051, 0.283) m; if 札内 is the physically appropriate gauge for
     KP 4.2–7.0 the error should be re-derived there.
   - If Nantai is retained (e.g. for consistency with Uemura), state the
     8–11 km extrapolation explicitly as a Phase 3 limitation in Ch3/Ch7.
     **This is a real open item, not a cosmetic one** — record it as a residual
     alongside D8.
3. **Optional independent hazard check:** the 115-year Obihiro record is an
   observational counterpart to the d4PDF empirical annual-max stage-frequency
   curve used in `system_integration/hazard.py`. A comparison of the observed
   annual-max stage distribution against the d4PDF historical ensemble would be
   a genuinely valuable validation of the Phase 3 hazard side, which is
   currently ensemble-only. Medium effort, high value.

### 2.3 Design high water levels and channel widths (D3 p199, printed 177)

| River | Station | Distance (km) | 計画高水位 T.P. (m) | 川幅 (m) |
|---|---|---|---|---|
| Tokachi | 芽室 Memuro | 71.0 | 64.04 | 450 |
| **Tokachi** | **帯広 Obihiro** | **56.6** | **38.14** | **510** |
| Tokachi | 千代田 | 37.6 | 17.78 | 740 |
| Tokachi | 茂岩 | 21.0 | 11.61 | 960 |
| Tokachi | 河口 mouth | 2.4 | 5.10 | 960 |
| Otofuke | 音更 | 9.0 | 74.30 | 270 |
| **Satsunai** | **南帯橋** | **15.0** | **79.22** | **400** |
| Toshibetsu | 利別 | 8.0 | 15.72 | 440 |
| Urahoro-Tokachi | 十勝太 | 3.6 | 4.03 | 400 |

**Warning: the Obihiro design HWL differs across plan revisions**, and D3
reproduces several without always flagging which is current:

| Source in D3 | Obihiro 計画高水位 |
|---|---|
| p73 / p82 (1981, 1988 flood chapters) | 38.56 m |
| p87 (2016 flood chapter) | **38.26 m** |
| p150 / p158 (basic-policy comparison tables) | 38.44 m |
| p199 (river improvement plan) | **38.14 m** |

**→ Action (accuracy item).** The thesis contains `38.14` once and `38.07`
twice. Whichever HWL the thesis uses for the Phase 3 crest/grid-top comparison
must be **pinned to a named plan revision with a date**, because a 0.42 m spread
across revisions is large relative to the fragility shoulder. Add a footnote in
Ch3 recording the revision history above. Also record the Obihiro warning
ladder (§2.5) since it defines the operationally meaningful stages.

Also from D3 p264 (printed 242), the crest-width / freeboard planning history
(m), useful as a geometry cross-check:

| Plan year | Obihiro crest width | freeboard | Nantaibashi | Otofuke |
|---|---|---|---|---|
| 1966 (昭41) | 6.5 | 1.5 | 5.5 | 5.5 |
| 1980 (昭55) | 7.0 | 1.5 | 7.0 | 5.5 |
| 1988 (昭63) | 8.0 | 1.5 | 7.0 | 5.5 |

### 2.4 Design standard, design rainfall, and target discharges

- **Design scale at Obihiro: 1/150** (150-year annual exceedance);
  design rainfall **245.7 mm** (D3 p137, printed 117). Other points:
  Motoiwa 1/150 / 214.8 mm; Otofuke 1/150 / 235.0 mm; Memuro 1/150 / 256.5 mm;
  Toshibetsu 1/100 / 203.3 mm; Satsunai Dam 1/100 / 346.6 mm.
  Note ※1: Nantaibashi carries **two** design rainfalls because the design scale
  is 1/100 downstream and 1/150 upstream of the Totabetsu confluence.
- **River-improvement-plan target discharges** (D3 p176, printed 156):
  Obihiro target 5,100 m³/s, Tokachi Dam regulates 800 ⇒ **4,300 m³/s allocated
  to the channel**; Motoiwa 11,100 ⇒ 10,300; Otofuke at Otofuke 900;
  **Satsunai at Nantaibashi 1,400**; Toshibetsu 3,000; Tokachita 1,400.
- 1980 revision: **Tokachi Ohashi design discharge raised 4,000 → 6,100 m³/s**
  (D3 p280, printed 258); Motoiwa basic high water 15,200, design high water
  13,700 (from 9,700) (D3 p269, printed 247); Satsunai at Nantaibashi design
  high water 2,700 m³/s in the 1980 revision, from 1,600 in 1966 (D3 p253).

**→ Action.** Ch3 §Tokachi River Basin. The **1/150 design standard** is the
single most useful of these: the thesis's Phase 3 annualised system $P_f$
(median 3.7e-4/yr historical, segments > 1e-3/yr rising 2 → 45 under +4K) can be
benchmarked directly against the design intent of $6.7\times10^{-3}$/yr. That
comparison is a strong Ch6/Ch7 result and costs nothing to compute. Note
carefully that 1/150 is the *design flood* return period, not a target
*failure* probability — the comparison must be framed as "the engine's
annualised failure probability versus the annual exceedance probability of the
design load", not as compliance.

### 2.5 The 2016 event — station data (D3 p87, printed 67) — **directly Phase 2 relevant**

Reference levels (2016-era plan) and the three flood peaks:

| | 共栄橋 | 芽室太 | **帯広** | 千代田 | 茂岩 | 音更 | **南帯橋** | 利別 | 十勝太 |
|---|---|---|---|---|---|---|---|---|---|
| 計画高水位 (m) | 146.72 | 64.27 | **38.26** | 17.76 | 11.63 | 74.96 | **79.31** | 15.94 | 4.05 |
| 氾濫危険水位 | 145.40 | – | 37.40 | – | 10.90 | 74.20 | – | 14.60 | 3.20 |
| 避難判断水位 | 145.20 | – | 36.80 | – | 10.00 | 73.80 | – | 14.10 | 2.60 |
| 避難注意水位 | 144.30 | 62.40 | 35.20 | 14.30 | 6.90 | 73.10 | 77.40 | 12.60 | 2.50 |
| 水防団待機水位 | 143.50 | 61.50 | 34.20 | 13.10 | 6.20 | 72.40 | 76.60 | 12.00 | 2.00 |
| **T7 peak level** | 143.35 | 61.92 | 34.74 | 13.89 | 7.96 | 72.68 | 76.99 | 13.70 | 3.17 |
| T7 peak Q (m³/s) | 295 | 845 | 1,195 | 2,641 | 3,149 | 377 | 837 | 977 | – |
| **T11+T9 peak level** | 144.09 | 62.93 | 35.57 | 14.24 | 8.02 | 72.40 | 76.10 | 13.57 | 2.39 |
| T11+T9 peak Q | 633 | 1,677 | 1,951 | 2,907 | 3,223 | 291 | 504 | 959 | – |
| **T10 peak level** | 144.00 | **64.79** | **38.07** | **18.74** | **12.68** | 74.45 | missing | 15.51 | 3.13 |
| **T10 peak Q** | 585 | 3,433 | **6,334** | 10,571 | 11,608 | 1,182 | missing | 1,251 | – |

Plus the critical note:

> 札内川は、南帯橋水位観測所が**ケーブル切断により欠測**となったが、観測され
> ている範囲での最高水位（**８月31日２時 79.38m**）が計画高水位を超える出水と
> なった

*The Satsunai Nantaibashi gauge went missing due to a severed cable, but the
maximum level within the recorded range — **79.38 m at 02:00 on 31 August** —
exceeded the design high water level (79.31 m).*

**Key readings:**
- **Obihiro 2016 peak = 38.07 m, i.e. 0.19 m BELOW the 38.26 m design HWL.**
  The Tokachi *did not* exceed design HWL at Obihiro.
- Downstream it did: Chiyoda +0.98 m, Motoiwa +1.05 m, Memurobuto +0.52 m.
- The Satsunai **did** exceed its design HWL, and the gauge record is truncated.
- The event is a genuine **three-peak sequence at the same gauge**
  (34.74 → 35.57 → 38.07 m at Obihiro), with peak discharge rising
  1,195 → 1,951 → 6,334 m³/s.

**→ Actions (high priority).**
1. **Verify the Phase 2 loading against this table.** ADR-0035 anchors the 2016
   peak per section to the surveyed right-bank flood trace, with Obihiro stage →
   inverse gauge rating → section rating. The official Obihiro peak of
   **38.07 m** is an independent check on the head of that chain. If the
   replay's Obihiro-equivalent peak disagrees materially, that is a finding.
   Concretely: `bayesian_reliability_updating` reconstructs $h_{2016}$ per
   section; compare the reconstructed Obihiro-datum peak to 38.07 m.
2. **The Nantaibashi cable failure is a documented data gap** that the thesis
   should state, because it means the *observed* Satsunai peak is a lower bound
   (≥ 79.38 m). If any Phase 3 Satsunai reasoning leans on an observed 2016
   Satsunai stage, it is leaning on truncated data. Add to Ch3 §2016 and to the
   Phase 3 limitations.
3. **The three-peak structure is the empirical justification for the
   compound-event treatment.** Ch3/Ch4 should cite these three measured peaks at
   one gauge as the physical basis for the two-peak/compound hydrograph and for
   Pol's compound-event memory model, rather than treating multi-peak loading as
   a modelling convenience. It also gives real numbers for the ADR-0044
   sustained-peak bound discussion.
4. **Add the warning ladder to Ch3.** 水防団待機 34.20 → 避難注意 35.20 →
   避難判断 36.80 → 氾濫危険 37.40 → 計画高水位 38.26 m at Obihiro. These are
   the operationally meaningful stages and make the fragility curve's
   conditioning grid interpretable to a Japanese reader (and to the committee).

### 2.6 The 2016 event — the three levee breaches and their official causes (D3 pp90–93, printed 70–73)

Three breaches in the directly-managed Tokachi system, each 200 m:

| Location | Confirmed | Official cause (per 十勝川堤防調査委員会) |
|---|---|---|
| **Otofuke KP21.2 left bank** | 08-31 17:30 | *During the falling limb*, channel migration occurred; **bank and embankment erosion** caused the breach |
| **Satsunai KP25.0 left bank** | 08-31 05:20 | Ponded inner water plus overflow from the **Totabetsu River** (prefectural section) levee breach **overtopped the levee from the LANDSIDE** (trace evidence); levee breached |
| **Satsunai KP40.5 left bank** | 09-01 11:10 | *During the falling limb*, channel migration; **bank and embankment erosion** |

**None of the three was attributed to seepage or piping.** Two were
falling-limb erosion; one was landside overtopping.

**→ Actions (high priority — affects claims in two directions).**
1. **This strengthens the Phase 2 observation.** The thesis's survival
   observation is currently supported by `tokachi_levee_committee_2017`. D3
   gives the *positive* complement: the committee attributed every breach that
   did occur to a non-seepage mechanism. So the 2016 record is not merely
   "no piping observed at the study sections" but "**no piping breach anywhere
   in the directly-managed Tokachi system, with all three actual breaches
   attributed to other mechanisms**". That is a materially stronger statement of
   the conditioning evidence. Put it in Ch3 §2016 and Ch5.
2. **This weakens the Phase 3 RQ3 BEP-dominance headline** and must be
   confronted, not buried. Phase 3 concluded BEP dominates 64–100 % of summed
   annual contributions at all four quantified sections historically. The
   empirical record is 3/3 erosion or landside-overtopping. The honest
   reconciliation available from the material at hand:
   - the breaches are on the **left** bank of Otofuke/Satsunai, outside the
     four quantified Tokachi right-bank sections;
   - the **Satsunai KP25.0 landside-overtopping mechanism is outside the
     mechanism set entirely** (neither BEP, nor overflow from the river, nor
     fluvial scour) — a genuine model-scope gap worth stating;
   - fluvial scour being computed as **exactly zero at all 114 nodes** under the
     corrected USACE conversion (ADR-0042 dec. 9) is *hard to reconcile* with
     three erosion-caused breaches in one event. This deserves an explicit
     paragraph. It does not invalidate the dimensional correction — that was
     resolved on dimensional grounds — but it does mean the **scour model as
     re-executed is not capturing the mechanism that actually broke these
     levees** (channel migration and bank erosion on the falling limb, which
     Uemura's USACE point-scour formulation does not represent).
   Route this through `bep-external-positioning` before it goes in the
   Discussion; it changes the confidence attached to a headline claim.
3. **"Falling-limb" is a striking detail.** Both erosion breaches occurred as
   the flood receded. The thesis's transient BEP argument also concerns what
   happens after the peak. Worth one sentence noting that both the seepage and
   the erosion mechanisms at Tokachi are recession-phase phenomena — which
   argues against any peak-only (WBI+-style) shortcut for *either* mechanism,
   generalising the thesis's 2.75–3.9× peak-shortcut over-rejection finding.

### 2.7 The 2016 event — rainfall, damage, and duration (D3 pp85–89, 94–95; D11)

- Four typhoons in one month: T7 (08-17), T11, T9 (08-23), T10 approach/landfall
  (08-30/31). **First time since typhoon statistics began in 1951 that more than
  one typhoon made landfall on Hokkaido in a year** (D11 p2).
- T10 took an unprecedented course, landing at Ofunato from the Pacific side,
  driving three days of moist easterly flow and **orographic rainfall** on the
  SE slopes of the Hidaka range (D3 p85; D11 p2).
- **Cumulative rainfall over the four typhoons** (D3 p86, printed 66), mm —
  selected: Obihiro **312.0** (88.0 + 60.5 + 31.5 + 132.0); Nukabira-gensenkyo
  832.0; Satsunai Dam 790; Totabetsu **908**; Kamisatsunai 605; Shintoku 564.5;
  Mitsumata 636.5.
- **3-day totals 08-29 → 08-31** (D3 p89, printed 69): Nissho 363, Fushimi 409,
  **Totabetsu 574**, Kamisatsunai 378, Satsunai-futamata 388, Satsunai Dam 501.
  At Obihiro 198.6 mm/3 d; Motoiwa 167.1 mm/3 d (D3 p88).
- Damage in the Tokachi basin (D3 pp88–89): outer-water inundation **644 ha**,
  inner-water **768 ha**, total **1,412 ha**; 3 dead, 7 injured; 25 houses
  destroyed, 76 half-destroyed, 115 above-floor, 129 below-floor;
  agriculture > 19,000 ha; total **¥10.55 billion**.
- Hokkaido-wide (D11 p1): 4 dead, 2 missing, 29 destroyed, 273 above-floor,
  989 below-floor; max 687 shelters, 11,176 evacuees; agriculture 40,258 ha;
  **total ¥280.3 billion — the largest in Hokkaido's history**, exceeding the
  1981 "56 flood" (¥270.5 billion). Designated 激甚災害.
- **Flood-fighting operations ran 2016-08-17 13:10 → 2016-09-05 21:00 —
  approximately 19 days** (D3 p94, printed 74). Four drainage pump stations
  operated (Obihiro, Shimo-Ushikubetsu, Ikusota, Ikeda).
- Dams: Tokachi Dam stored ~45 million m³; **Satsunai Dam experienced
  record-maximum rainfall and overflowed its emergency spillway**, storing
  ~24.4 million m³ (D3 p95, printed 75).
- 12 Tokachi-system stations recorded their **highest level on record** (D11 p3).
- **Antecedent-wetness mechanism** (D11 p2): water levels had not fully receded
  from the first three typhoons before the next rain, so soil moisture stayed
  near saturation and runoff response to T10 was amplified.

**→ Actions.**
1. **Ch1 / Ch3:** the ¥280.3 billion record, the 1951-onwards
   never-before-more-than-one-typhoon fact, and the 12 record stage records are
   excellent, sourced motivation. Currently absent from the thesis.
2. **Ch3 / Ch4:** the antecedent-wetness mechanism is the physical justification
   for treating the 2016 loading as a *compound* event with memory rather than
   three independent floods — which is exactly what the Pol SIE 2024
   compound-event memory model represents and what the engine's uplift latch and
   monotonic pipe length encode. Cite D11 for it.
3. **Ch3 / ADR-0044 discussion:** the ~19-day flood-fighting window and the
   Satsunai Dam emergency-spillway overflow bound how long the system was under
   load. Useful context for the sustained-peak bound.

### 2.8 The 1981 (昭和56) August flood at Obihiro (D3 pp72–73, printed 52–53)

- Obihiro peak level **37.84 m at 22:00 on 08-05, 0.72 m below the then design
  HWL** (⇒ 38.56 m); Obihiro peak discharge **4,750 m³/s**; Motoiwa peak level
  10.19 m, peak discharge 6,749 m³/s; Shinsei-bashi 1,787 m³/s.
- Obihiro city 4-day rainfall **162 mm — an all-time record at the time**;
  basin average 220 mm; mountains 300+ mm (Kaminiwamatsu 355, Nukabira 325,
  Kamisatsunai 337).
- "十勝川本流・同支川は大正11年以来の洪水" — the largest flood on the Tokachi
  main stem and tributaries **since 1922**.
- Obihiro River and Baibai River rose to the brink of levee overflow.

**Resulting Obihiro peak-stage record for the thesis:**
1981-08: 37.84 m / 4,750 m³/s → 2016-08: **38.07 m / 6,334 m³/s** (record).

**→ Action.** Ch3 flood-history section: gives the two largest modern events at
the study gauge with both stage and discharge, which is exactly what is needed
to place the fragility-curve conditioning grid in historical context. Note that
even the record 2016 event did not reach the design HWL at Obihiro — a clean,
sourced statement of how far the observed record sits below the design load,
and therefore of how much extrapolation the Phase 3 annualisation is doing.

### 2.9 Historical flood and hazard chronology (D3 p736; D9/D10)

- 1962 (昭37) typhoon flood: **Motoiwa 8,839 m³/s**, 3,793 houses damaged,
  inundation area **40,768 ha**.
- 1952 (昭27) Tokachi-oki earthquake M8.2, intensity 5 at Obihiro, 9,507 houses
  damaged (D3 p103, printed 83).
- 1960 Chile tsunami: 205 houses; Otsu tsunami height 3.0 m.
- **2003-09 Tokachi-oki earthquake: levee slope failure and crest cracking over
  approximately 30 km** (D3 p103, printed 83).
- 1993 Kushiro-oki and 2003 Tokachi-oki damaged largely the *same* sites; where
  the 1993 repair had included foundation treatment and full re-excavation
  (Tokachi Tounai, Higashi-Inaho), almost no 2003 damage occurred; where only
  partial re-excavation was done (Horooka), nearly the full length was damaged
  in 2003 (D3 p122, printed 102).
- 2011-09 heavy rain: **part of the Otofuke River levee was lost** (D3 p603);
  PWRI uses this event as its erosion example (D1 p6, Fig. 2.2.1, "H23.9·音更川").
- Basin overview (D10 p6): catchment **9,010 km²**; main-stem length **156 km**;
  basin population ~320,000; **assumed inundation area 617.4 km²** with
  ~168,000 people; land use 63 % forest / 29 % farmland / 1 % urban; source
  Mt. Tokachi (2,077 m); Tokachi agricultural output ¥304.1 billion (2020),
  22 % of all Hokkaido; 47 % of national sugar beet, 33 % of wheat, 25 % of
  potatoes.

**→ Actions.**
1. **Ch1/Ch3:** the 9,010 km² / 156 km / 617.4 km² / 168,000-people /
   food-supply figures are the best available one-paragraph justification of
   *consequence* for the study area, which the Introduction needs in order to
   motivate a reliability (rather than purely mechanistic) treatment.
2. **Ch3 / Ch7:** the **2003 earthquake cracking over ~30 km** is directly
   relevant to seepage. D1 p54 lists residual earthquake-induced cracks among
   the candidate locations for internal erosion and collapse. Pre-existing
   cracks are an unmodelled defect pathway; note it as an open problem.
3. **Ch7:** the 1993-vs-2003 repair-quality contrast is a clean, sourced
   demonstration that remediation *depth* determines recurrence — supporting
   the §1.12 argument that `remediation_state` needs physical rather than
   label treatment.

### 2.10 Channel gradient and morphology (D3 pp283–285, 392)

- **Channel gradient from upstream to near Obihiro: about 1/200 to 1/600**
  (D3 p392, printed 370).
- Upstream reaches are **alluvial-fan channels** with sand-gravel banks, steep
  slope, **double-row bars**, unstable; disaster incidence in double-row-bar
  reaches is nearly **twice** that of single-row-bar reaches (D3 p285,
  printed 263).
- Mishima pitch theory: Satsunai meander wavelength **1,300 m** per meander
  (D3 p284); later replaced by the meander theory of Yamaguchi et al.
- Satsunai is a **wide braided (複列網状) river**, channel unstable, thalweg
  frequently approaching the levee (D3 p288, printed 266).
- Satsunai was constrained from a wide fan flow to a **400–450 m levee corridor
  over 17 years**; the reach where levees cut off former channels is about
  **1/3 of the total levee length** (D3 p293, printed 271).
- 1992 movable-bed hydraulic model experiment on the Satsunai found that scour
  near groynes can be substantial and can affect levee stability; 2D flow
  analysis at design discharge was also performed (D3 p281, printed 259).
- 堤防防御ライン (levee defence line) methodology introduced 2002 and applied to
  the Tokachi upstream reaches (D3 p286, printed 264).

**→ Actions.**
1. **Ch3 §Study Area:** the 1/200–1/600 gradient and braided/double-row-bar
   morphology are the sourced basis for calling the Tokachi a steep, flashy,
   gravel-bed river — currently asserted in the thesis but thinly sourced.
2. **Phase 3 / Ch7:** "levees cut off former channels over ~1/3 of the Satsunai
   levee length" is a **first-order seepage risk factor** (a buried palaeochannel
   under or beside a levee is the classic high-permeability path; D1 p32 and D3
   p277 both flag it). This is a strong argument that the Satsunai BEP hazard is
   *spatially heterogeneous* in a way the four-section `exact` policy cannot
   resolve — and it connects to the seepage-length-L study's latent
   spatial-correlation tension.
3. The Satsunai movable-bed model experiment and 2D analysis are candidate
   independent references for the Phase 3 fluvial-scour mechanism, which
   currently rests entirely on the re-executed Uemura USACE model.

---

## 3. Tokachi levee seepage-remediation history — bears directly on `remediation_state`

### 3.1 Official recognition of foundation leakage in the study reach (D3 p265, printed 243)

Among the characteristic features of Tokachi levee development:

> ④ 上流域においては、堤防基盤が**沖積世の氾濫原堆積物からなる極めて透水性の
> 高い地質**のため、**基盤漏水**や堤体漏水により堤防の機能が失われるおそれの
> ある箇所において「漏水対策」が行われた。

*In the upstream basin, because the levee foundation consists of Holocene
floodplain deposits of extremely high permeability, "leakage countermeasures"
were carried out at locations at risk of losing levee function through
**foundation leakage** or embankment leakage.*

**→ Action (important — this is the strongest single sentence supporting the
thesis premise).** The official flood-control history of the study river
explicitly identifies **foundation leakage (基盤漏水) — the exact mechanism the
engine models — as a recognised and remediated hazard in the upstream reach
that contains the study sections**. Quote it in Ch1 and Ch3. It is also the
direct counter to the JSCE claim in §5.1.

### 3.2 Compound embankment-and-foundation leakage (D3 p277, printed 255)

> 十勝川水系の上流域においては、堤防の基礎地盤は沖積世の氾濫原堆積物からなる
> 極めて透水性が高い地質であり、**堤体材も現地土を用いた砂礫土から構成されて
> いるため透水性も高く、堤体と基盤（地盤）の複合漏水**の形態をとっていると
> 考えられた。

*The foundation is extremely permeable Holocene floodplain deposit; the
embankment material is also sand-gravel from local borrow and so is also
permeable; the leakage is therefore thought to take the form of **compound
embankment-plus-foundation leakage**.*

**→ Action (a limitation the thesis must state).** The engine models
**foundation** BEP only (blanket + aquifer; M4–M7). The official
characterisation of the study reach is a *compound* mechanism in which the
embankment itself is permeable sand-gravel. Two consequences:
1. State this as a scope limitation in Ch4 and Ch7 — the engine's separation of
   the embankment from the foundation is a schematisation, and at Tokachi the
   embankment is not an impermeable cap.
2. It also **explains the gravel-levee exclusion** from $t^*$ screening (§1.5)
   and why Fukuoka et al. applied $t^*$ to the wide *lower* reach: the study
   sections' own embankments are gravelly.

### 3.3 Duration is required by the Japanese standard's own words (D3 p277)

Quoting 河川砂防技術基準 as applied from the late 1970s:

> 堤防は堤体材料、基礎地盤材料、水位、**高水の継続時間**等を考慮して、浸透水の
> しゃ断及びクイックサンド、パイピング現象を生じさせないような構造でなければ
> ならない

*The levee must be structured so as not to permit quicksand or piping,
**considering the embankment material, foundation material, water level, and the
duration of high water**.*

**→ Action (excellent Introduction/Ch2 material).** The Japanese technical
standard has **required consideration of high-water duration since the 1970s**,
yet the implementing verification is a duration-terminal threshold check rather
than a progression model. That is the thesis's research gap **stated in the
standard's own vocabulary**, which is a far stronger framing than an
externally-imposed critique. Use it in the Introduction's problem statement.

### 3.4 A documented countermeasure failure in the study geology (D3 p280, printed 258)

First-hand account by 北條紘次, then head of the Obihiro River Office, on the
FY1977–79 **Otofuke–Kino levee foundation-leakage countermeasure**
(音更～木野築堤基礎漏水対策): sheet walls (1 m wide, 5–9 m long thin steel
plates) jetted and vibrated into the **sand-gravel foundation** as a cutoff.

> しかしながらシートウォール工法は、より細粒の地盤を対象に開発された工法で
> あり、**砂礫基礎の連続止水壁としては不適切であると推定される**。そこで55
> 年度は**高水敷に所要の土質ブランケットを設ける工法に変更**した。

*However, the sheet-wall method was developed for finer-grained ground and is
presumed **inappropriate as a continuous cutoff wall in a sand-gravel
foundation**. Therefore in FY1980 the method was **changed to placing a soil
blanket on the high-water bed**.*

Corroborated doctrinally by D1 p50 (large gravel/cobbles deform sheet piles;
cutoff integrity is not maintained) and D1 p49 (≥ 90 % penetration required).

**→ Actions (high value).**
1. **This validates the engine's ADR-0025 baseline.** The actual remediation
   deployed at Tokachi is a **foreland blanket**, precisely the
   `blanketed_tanh` foreland treatment the engine adopts as its baseline. That
   is a physical, documented justification for a decision currently defended on
   evidence-weighting grounds. Add to the ADR-0025 rationale and to Ch4.
2. **It is also a clean case study for Ch7:** a piping countermeasure that
   failed on the *material* mismatch between method and geology, in this exact
   reach. It supports the argument that remediation must be modelled physically
   rather than as a label.
3. Same page: the 1980 revision raised the **Tokachi Ohashi design discharge
   from 4,000 to 6,100 m³/s**; the site was constricted by the Kino levee
   (planned width 500 m vs actual 370 m), prompting a 130 m setback requiring
   ~80 buildings and 6 ha of land, and replacement of the Tokachi Ohashi bridge.

### 3.5 Otofuke urban reach: levees built along former channels (D3 pp277–278, printed 255–256)

> 特に音更川下流の市街地区間では、**旧河道上を縦断的に築堤が造られた箇所も
> 多くあり、漏水の危険性が高く**、対策の優先度も高いことから、多くの区間で
> 漏水対策工事が実施された。

Leakage countermeasures began in **1976 (昭和51)** and proceeded in stages; two
methods were used based on geological investigation — **sheet wall** (combined
with high-water revetment) and the **blanket method**. Standard drawings for
both are reproduced (D3 p278), along with a channel-migration history figure for
the Otofuke (D3 p277).

**→ Action.** Ch3/Ch7: the palaeochannel-alignment risk factor is officially
documented for the Otofuke urban reach; combined with §2.10's "1/3 of Satsunai
levee length cuts off former channels", this is a well-sourced argument that the
study area's seepage hazard is palaeochannel-controlled and spatially
heterogeneous. Also: **the standard drawings on D3 p278 give the actual
as-built geometry of the blanket and sheet-wall remediations** — if any
remediation modelling is attempted (§1.12), these are the dimensions to use.

### 3.6 Timeline of the modern seepage-verification-driven remediation

- **2002-07**: 河川堤防設計指針 issued (design and safety-verification methods).
- **2002-02**: 河川堤防の構造検討の手引き (JICE).
- **2004**: 河川堤防質的整備技術ガイドライン（案）.
- Tokachi performed seepage-resistance verification under these and carried out
  strengthening where required, notably **landside-toe drain works
  (裏のり尻ドレーン工法)** (D3 p279, printed 257 — includes the
  "浸透に対する安全度照査の手順" flow diagram).
- **FY2003–2007**: "堤防の耐浸透性能の照査結果に基づく浸透対策に着手" — seepage
  countermeasures based on the verification results were *initiated* in this
  period (D3 p241, printed 221).
- **2004** earthquake review: dynamic deformation analysis found that
  **large-section (hill levee) + drain works is effective as both an earthquake
  and a seepage countermeasure**; Obihiro accordingly implemented drain works in
  the liquefaction-prone lower Tokachi (D3 p122, printed 102).

**→ Action.** This is the **provenance chain for the engine's
`remediation_state` labels** (`drained` at KP58.8/60.0, `berm-only` at KP57.4,
`unreinforced` at KP62.0/63.4). Record the dates in
`docs/tokachi_bep_inputs_provenance.md` — the per-cell audit trail currently has
no source for that column. Note that works were *initiated* FY2003–2007, which
is consistent with the 2008 screening maps (§4) still showing deficient
sections.

### 3.7 The hill levee (丘陵堤) and the Fukuoka et al. (2019) reach (D3 pp269–271, printed 247–249)

- Motivated by widespread **peaty soft ground** in the lower Tokachi.
- 1:5 slope gives a slope-slide safety factor of about **1.2**; chosen over
  押え盛土 (counterweight fill) because single-slope geometry eases maintenance
  and it consumes the large volumes of dredged/excavated material.
- **Planned reach: Tokachi river mouth → KP 37.6 (Chiyoda Ohashi); Toshibetsu
  confluence → KP 8.0.** Construction from FY1987, staged (first to HWL height,
  then to full crest).
- On 2016: "平成28年８月洪水では計画高水位を超えていたが、**堤防の浸透破壊が
  起きず**、その効果が検証されている" — in the 2016 flood the design HWL was
  exceeded yet **no seepage failure of the levee occurred**, verifying the
  design.
- **Cited to:** 福岡捷二・石塚宗司・田端幸輔,「堤防脆弱性指標を用いた平成28年
  十勝川大洪水時における丘陵堤整備区間の浸透破壊に対する安全性と破堤リスク
  軽減に向けた今後の堤防設計の考え方」, 土木学会論文集B1（水工学）, Vol.75,
  No.2, 2019.

**Superseded by direct reading of the paper (2026-07-27).** Fukuoka et al.
(2019) was subsequently obtained and read in full. It contains a finding that is
**more consequential than anything in D3 on this topic**, and that materially
strengthens the thesis:

> また、基盤漏水やパイピング被害は見られなかった。これは、大きな堤防によって
> 泥炭性軟弱地盤が圧密され、**最終圧密状態の透水係数が 10⁻¹¹ m/s と非常に
> 小さい値を持つため**である。

*Furthermore, no foundation leakage or piping damage was observed. This is
because the peaty soft ground has been consolidated by the large levee, and its
final consolidated-state permeability has the very small value of 10⁻¹¹ m/s.*
(citing Hayashi, Mitachi & Nishimoto 2008, now `hayashi_2008`)

**The mechanism Fukuoka invokes for the absence of foundation piping is an
effectively impermeable consolidated-peat foundation — not the wide
cross-section.** The wide cross-section (and hence $t^*$) explains the absence of
**embankment** seepage damage and landside slope sliding. The paper's own
threshold legend confirms the scope: $10^{-2}$–$10^{-1}$ → 裏法滑り (landside
slope sliding), $>10^{-1}$ → 決壊.

This is decisive for transferability. The study sections sit on a sand-gravel
aquifer at $10^{-3}$–$10^{-2}$ m/s (§2.1); the hill-levee reach sits on
consolidated peat at $10^{-11}$ m/s. **The contrast is eight to nine orders of
magnitude.** The Fukuoka reassurance is therefore not merely *outside the reach*
— it is **inapplicable in principle** to the study sections, because the physical
mechanism that protected the lower reach does not exist at them. *Status: done —
Ch3 rewritten accordingly; this is now the strongest available answer to a
predictable committee question.*

Two further scope conditions from the paper, both now in Ch2:

- **Sections with mean embankment gravel content ≥ 15 % were excluded** from the
  assessment, citing PWRI large-scale model experiments (`pwri_4300_2015`)
  showing very small seepage-failure risk in such material. Excluded: left bank
  32.6–37k, right bank 23–25k and 31–33k. This is the quantified form of the
  JICE gravel-levee exemption (§1.5). It cuts *against* the thesis and must be
  stated: it is Japanese experimental evidence that gravel-rich levees resist
  seepage failure. The scope limit is that it concerns *embankment* seepage, not
  foundation BEP through a confined aquifer.
- **A second, recession form of the index** (Eq. 2), with $H_\text{max}$ the
  landward-migrating phreatic crest and $b'$ the shortened distance to the toe,
  and the explicit conclusion that *for some interval after the peak the
  landside seepage-failure risk exceeds that at the peak*. In the 2016
  computations $t^*$ stayed near maximum for ~10 h into recession; under design
  discharge one section held $t^* > 10^{-2}$ for ~12 h. **This is a strong,
  independent, peer-reviewed Japanese corroboration of the thesis's core
  "the critical instant is not the peak" claim**, reached by a different physical
  route (phreatic-surface lag rather than pipe progression). The thesis was not
  using it. *Status: done — added to Ch2 and Ch7.*

**→ Action (precision item, and a favourable one).** D3 additionally pins down
what the thesis states loosely about the reach. Critically:

**The Fukuoka et al. (2019) result applies to the 丘陵堤 (hill-levee) reach,
KP 0–37.6 — which does NOT contain the thesis's study sections at
KP 57.4–63.4.**

The thesis's wording ("the wide gently sloping levees of the lower Tokachi
reach", Ch2:149 and Ch3:39) is *correct*, but a reader could mistake it for
covering the study sections. Three consequences:
1. Add an explicit sentence in Ch2 and Ch3 stating the reach limits
   (KP 0–37.6) and that the study sections lie **outside** it. This protects
   against a committee question and *strengthens* the thesis: the $t^*$-based
   reassurance demonstrably does not extend to the study sections, which are
   narrower, steeper, gravel-bodied, and — per §3.1 — in the reach where
   foundation-leakage countermeasures were actually needed.
2. The design HWL exceedance in 2016 that Fukuoka et al. analyse was at
   **Chiyoda / Motoiwa** (+0.98 / +1.05 m, §2.5), not at Obihiro, where the
   peak stayed 0.19 m below HWL. Make that explicit.
3. Note that the study sections are gravel levees and thus formally **outside
   the $t^*$ screening scope** (§1.5) — a second, independent reason the
   Fukuoka reassurance does not transfer.

### 3.8 Kasumi-tei (霞堤, discontinuous levees) — a Phase 3 segment-definition issue (D3 pp265–268, printed 243–246)

- Retained today: **Tokachi upstream 13 locations, Satsunai 13, Otofuke 8**.
- Purpose: tributary confluence and inner-water handling; cheaper than sluice
  structures and drains inner/floodwater quickly; also receives and returns
  floodwater if an upstream levee breaches.
- A location list with 距離標 (KP) is tabulated (D3 p268, printed 246). Read
  values include Tokachi **right bank 西帯広築堤 KP63.8**, left bank
  西士狩築堤 KP65.8, right bank ピウカ築堤 KP69.4, 芽室築堤 KP74.6,
  中島築堤 KP76.6, 御影築堤 KP80.4, left bank 芽室太築堤 KP80.6,
  熊牛築堤 KP85.0 (list continues beyond the extracted text).

**→ Action (a real Phase 3 correctness question).** A kasumi-tei is an
**intentionally discontinuous levee** — it is not a continuous barrier and its
failure semantics differ fundamentally from a continuous segment. Phase 3
composes 114 segments as a series system over the 0.2 km grid
(`system_integration/segments.py`, `composition.py`). If any of those segments
falls in a kasumi-tei opening, its inclusion as a series element is wrong.
**Tokachi right bank KP63.8 is only 0.4 km from the thesis's KP63.4 section**
(which is excluded by default, but is in the CSV), and the Satsunai has 13
kasumi-tei. Recommended: read the full table from D3 p268 and check the 114-node
registry against it. If overlaps exist, either exclude those nodes or document
the treatment. Low effort, and it protects an RQ4 headline number.

### 3.9 Other levee-protection measures in the study reach

- **High-velocity-flow countermeasures (高速流対策)** for Satsunai and Otofuke
  were formalised in the **2010-06** river improvement plan, motivated by
  hydraulic model experiments and 2D analysis showing scour/erosion could breach
  levees near urban areas (D3 pp265, 281).
- Obihiro urban reach: high-water revetment on the Tokachi right bank
  北帯広築堤 and Satsunai left bank 東帯広築堤 from **1979**; Satsunai completed
  1982, Tokachi completed by 1993, coordinated with the Tokachi Ohashi
  replacement. At the Tokachi Ohashi bend, revetment was carried **above the
  design HWL to the planned crest height** (D3 p272, printed 250).
- Side-berm fill (側帯盛土) with tree planting under the "green corridor"
  programme: Satsunai 東帯広築堤 1993–94; Tokachi 北帯広築堤 1999–2003
  (D3 pp272–273).
- Otofuke urban reach: leakage countermeasures **combined with** high-water
  revetment, using sheet wall in some sections and the blanket method in others
  (D3 p274, printed 252).

**→ Action.** These are the physical works present at or adjacent to the study
sections. Two uses: (a) Ch3 §Study Area, to describe the as-built condition
honestly; (b) the **side-berm fill at 北帯広築堤 (Tokachi right bank, Obihiro),
1999–2003** is a documented seepage-relevant intervention in the study reach and
should be reconciled against the `remediation_state` labels in
`tokachi_bep_inputs.csv`.

---

## 4. The official seepage-safety screening of the study levees (D5, D6, D7)

### 4.1 The screening statistics (D5 p1)

Obihiro Development and Construction Department, **status as of end FY2007 /
March 2008**:

| Quantity | Value |
|---|---|
| Total detailed-inspection target levee length | **398.2 km** |
| Inspected by end FY2007 | **359.8 km (90 %)** |
| **Length where seepage safety falls BELOW the standard** | **66.7 km** |
| Share of inspected | **19 %** |
| Share of total | **17 %** |

Remaining ~40 km to be completed in FY2008. Results were reflected into the
**重要水防箇所** designations and shared with flood-fighting management bodies.
Evaluation condition: **"計画規模の降雨が発生した場合での評価"** — evaluated
under design-scale rainfall with the river level rising to the design level.

D5 p2 carries an important official caveat: the detailed inspection assesses
only the levee's *own* safety at the design water level under design total
rainfall; many sections still lack adequate height or width, so **the detailed
inspection result alone cannot be taken as an evaluation of a section's flood
safety**.

D5 p2 also gives a plain-language mechanism description:

> その状態が長く続くと、堤防の法すべりが生じ易くなったり、**堤防の中に形成
> された水の通り道が徐々に拡大する**ことで、水とともに堤防の土が流れ出して
> しまい、堤防が崩れるおそれが生じます。

*If that state continues for a long time, ... the water path formed within the
levee gradually expands ...* — i.e. the **time-dependence of pipe growth stated
in the authority's own public-facing explanation**.

**→ Actions.**
1. **Ch1/Ch3, high value:** "**66.7 km of 359.8 km inspected (19 %) of the
   Obihiro Development Bureau's levees fail the seepage safety standard**" is a
   study-area-specific counterpart to the national 25.1 % figure (§1.10) and to
   whatever Dutch figure the thesis uses. It localises the motivation precisely.
   Both are currently absent from the thesis.
2. Quote the D5 p2 time-dependence sentence in the Introduction — a public
   authority document asserting progressive pipe enlargement over time is
   rhetorically strong support for the thesis's framing.
3. Record the official caveat: this screening is *seepage-only* and does not
   address height/width adequacy. It is the right comparator for the engine's
   BEP branch specifically, not for overall levee safety.

### 4.2 The screening maps (D6, D7)

Both maps are dated **March 2008** and use a three-class code:

- **RED** — 浸透による堤防の安全性が**不足する**区間 (seepage safety insufficient)
- **NAVY** — 浸透による堤防の安全性が確保されている区間 (secured)
- **GREEN** — 詳細点検を今後実施予定している区間 (inspection planned)

**D6 (十勝川下流)** covers the downstream reach (Ikeda / Toyokoro / Urahoro to
the Pacific, roughly KP 0–40). Red segments are present.

**D7 (札内川)** covers the Satsunai and, within its frame, the Tokachi main stem
around Obihiro. Red segments are visible on the Tokachi near Obihiro and on the
Satsunai.

**Limitation of this review:** the maps are raster images embedded at limited
resolution. At 14× magnification the distance-marker labels were **not legibly
resolvable** here, so this review made no claim about which KP values are red.

> **RESOLVED (2026-07-27) by the user, who read the maps directly: all levee
> sections assessed in the thesis are classified 浸透による堤防の安全性が
> 確保されている区間 — "reaches in which seepage safety is secured".**

This is a significant result and it is **not** in tension with `oyo_1999`, which
rated several of the same cross-sections deficient in 1998. The two records
describe different configurations at different dates, and together they form a
coherent chronology:

| Date | Record | Configuration |
|---|---|---|
| 1998 | `oyo_1999` rates all five sections deficient in uplift, three in exit gradient | unremediated |
| 1999–2003 | toe drains at KP58.8/60.0, side-berm widening at KP57.4 | works executed |
| 2008-03 | `obihiro_levee_inspection_2008` classifies all study reaches as *safety secured* | remediated |

**This resolves the `remediation_state` awkwardness into a clean statement.** The
engine evaluates the *unremediated* foundation, so its fragility quantifies the
hazard that the 1999–2003 works were installed to suppress; the 2008
classification records the outcome after they were installed. The official
verdict is therefore **not a contradiction of the computed fragility but a
statement about a different configuration of the same cross-sections**. Two
consequences, both now written into the thesis:

1. The computed numbers must not be presented as present-day reliability
   estimates for the drained sections. Ch3 and Ch7 now say so explicitly.
2. The chronology is itself evidence that the mechanism was taken seriously by
   the authority at these exact locations — which reinforces rather than
   undercuts the thesis premise.

*Status: done — Ch3 §2016 carries the chronology, Ch7 §Limitations carries the
configuration-difference argument and the countermeasure→engine-quantity map.*

**→ Actions.**
1. **This is the single most valuable acquisition target from this folder.**
   The 2008 official screening is a **direct, independent, authority-issued
   verdict on the seepage safety of the very sections the engine models**. If
   the study sections' screening status can be established, it becomes a
   validation datum for the engine's BEP fragility ordering — a comparison the
   thesis does not currently have. Two routes:
   - georeference D7 (the map carries a 1:50,000 scale bar and a north arrow,
     so a two-point affine fit to the Tokachi/Satsunai confluence and Tokachi
     Ohashi would be adequate); or
   - **request the 十勝川中流 (middle-reach) sheet** — see §7.
2. Frame it carefully when used. The screening is a **binary, design-condition,
   deterministic** verdict; the engine produces a **continuous, stage-conditioned
   probability**. The legitimate comparison is *rank ordering* across sections,
   not a numerical match. If the screening says "secured" where the engine gives
   non-trivial $P_f$, the reconciliation runs through §1.4 (the Japanese check is
   duration-terminal at the design condition, not a full progression model) —
   which is exactly the thesis's thesis.

### 4.3 The Abashiri River case study — a long-duration analogue (D5 p4)

Abashiri River, Sumiyoshi/Hongo district:

- In the **September 2001** flood the water level **remained above the warning
  level for 234 continuous hours** (~9.75 days), creating breach risk;
  evacuation advisory issued.
- **Leakage from the embankment occurred** and flood-fighting was carried out —
  **月の輪工 (ring-levee works) at 7 locations, monitoring at 10 locations**.
- Quality-improvement works from 2002. **Purpose: securing safety against
  piping failure of the landside foundation ground and landside slope sliding.**
- Countermeasures: **section enlargement (landside 1:3.0, riverside 1:5.0)
  + drain works (L = 6.5 m)**, plus relocation of the landside drainage channel.
  H.W.L = 2.35 m.
- Photographs of the 2001 leakage, the ring-levee works, and the October 2006
  outer water level are included.

**→ Action (high value — this is a new validation candidate).** A Hokkaido
levee, **234 hours above warning level**, with observed embankment leakage,
officially attributed to landside-foundation piping risk, that **did not
breach**. This is:
1. The **regional upper bound on flood duration** — an order of magnitude longer
   than the Tokachi's measured 18 h rise / 9 h plateau (ADR-0032). It shows that
   the sustained-peak limit (ADR-0040 C3a/C3b) is *physically reachable in this
   region*, which materially strengthens the case for the sustained-peak
   comparator being the right conventional-practice benchmark and for the
   ADR-0044 sustained-peak bound being a meaningful (not merely formal) device.
2. A **fourth Japanese validation case** in the same family as
   Gounokawa / Yabe / Shikaga (`docs/validation/`), with the distinctive feature
   of extreme duration plus survival. The existing three cases established
   "no discrete pipe 3/3, $C_e$ on the fast side, static comparator conservative
   4/4"; a 234-hour survival would test the transient model in the
   duration-dominated limit, which none of the existing cases does.
   D5 alone is too thin to execute a case study (no geotechnical profile), so
   this is an **acquisition-and-then-execute** recommendation, not an
   immediate one.
3. Immediately usable regardless: cite the 234-hour figure in Ch2/Ch3 as the
   regional duration envelope.

Same page, D5 p3, shows a dated fill-history cross-section for the 幾春別川
(S34 peat fill, S39 peat-mixed silt, H1 cohesive, S51 sandy, S62 sandy, H2
cohesive, H4 peat/sandy, S53–54 sand compaction) — a good illustration of
Japanese 築堤履歴 practice for Ch3, though not Tokachi.

---

## 5. The erosion-versus-piping dominance tension — must be addressed in the Discussion

### 5.1 The JSCE investigation team's verdict (D11 p4)

> 札内川や音更川等の十勝川水系の河川は、河道周辺に広く砂礫を堆積させている。
> **砂礫で構成された堤防や地盤は、透水係数が大きく、せん断にも強いため
> パイピングや法すべりなどの浸透破壊に対して強いが、側岸侵食や越流侵食に
> 対して弱い。** したがって、これらの河川では護岸や水制を効果的に使うことに
> よって侵食を防ぐ方策が必要となる。

*Rivers of the Tokachi system such as the Satsunai and Otofuke have widely
deposited sand-gravel around the channel. Levees and ground composed of
sand-gravel have **large permeability and are also strong in shear, so they are
strong against seepage failure such as piping and slope sliding, but weak
against lateral bank erosion and overflow erosion**. Therefore these rivers
require measures to prevent erosion by effective use of revetments and
groynes.*

Reinforced by a retrospective column (D3 p706, printed 684):

> 土砂を含む巨大なエネルギーの流下する札内川では、**破堤などを含む災害原因の
> 大半は、河岸侵食によるもの**であったと記憶しています。

*For the Satsunai, the majority of disaster causes including breaching were due
to bank erosion.*

**This is a direct, authoritative challenge to the thesis's Phase 3 RQ3
conclusion** that BEP dominates 64–100 % of summed annual contributions at all
four quantified sections historically. It also **explains** why Uemura's WP2
erosion-dominance headline exists and why the thesis failed to reproduce it: the
Japanese expert consensus is that Tokachi levees are erosion-limited, not
seepage-limited.

**→ Action (highest-priority Discussion item; route through
`bep-external-positioning`).** Do not omit this and do not soften the Phase 3
result to accommodate it. Engage it directly. The available material supports a
substantive rebuttal-and-concession:

**Where the JSCE reasoning is questionable.** The stated mechanism —
"large permeability ⇒ strong against piping" — is **backwards for backward
erosion piping**. In Sellmeijer's rule the critical head *decreases* with
increasing aquifer permeability (higher $k_{aq}$ ⇒ larger $\lambda_{in}$, larger
$r_e$-driven exit gradients and a lower critical head), so high $k_{aq}$
*increases* BEP susceptibility. The JSCE sentence conflates two mechanisms:
shear strength (genuinely favourable — it resists *slope sliding*) and
permeability (genuinely *unfavourable* for BEP). It is a heuristic about
slope stability generalised to piping without justification. **The engine's
own numbers make the point quantitatively**: $k_{aq}$ is a top-ranked input in
the ADR-0033 GSA and its effect on $P_f$ is positive.

**Where the JSCE view is corroborated and must be conceded.** The 3/3 breach
attributions in 2016 (§2.6) were all erosion or landside overtopping. That is
strong empirical support for erosion dominance *as a cause of realised
breaches*, and it should be conceded plainly.

**The reconciliation the thesis can offer.** These are not contradictory if the
distinction is drawn between *mechanism susceptibility* and *realised failure
rate under the observed loading*: erosion has dominated realised breaches
because erosion acts on the rising and falling limbs at *every* moderate flood,
whereas BEP requires both the uplift/heave gate to open and sufficient duration
above the critical head — conditions the observed record has not yet supplied at
the study sections. Under the *design and +4K* loading, where the gate opens and
durations lengthen, the balance shifts. That is precisely a statement the engine
can support with its own fragility curves, and it is a genuine scientific
contribution rather than a defensive move.

**The honest caveat that must accompany it.** The Phase 3 comparison is only as
good as its surface-mechanism models. With corrected-USACE fluvial scour
computing **exactly zero at all 114 nodes**, the composition attributes to BEP
essentially all of what is not overflow — so the BEP-dominance share is
**partly an artefact of a scour model that returns zero**, and the 2016 record
shows the erosion mechanism that actually breaks these levees (falling-limb
channel migration and bank erosion) is not represented by a point-scour
formulation at all. State the BEP-dominance conclusion **conditional on the
surface-mechanism model set**, and name the missing mechanism.

### 5.2 The Tokoro River sand-boil caution (D11 p5)

From the Tokoro River findings:

> 破堤した箇所に対し、破堤しなかった箇所は、土質の粘着性が大きいとともに
> 内水が湛水して堤脚部の侵食を抑制していた可能性が考えられる。また、
> **噴砂の発生規模・位置には周辺地盤性状が大きく関与し、堤体から離れた噴砂は、
> 破堤と直接結び付かない可能性がある。**

*Compared with breached locations, non-breached locations had greater soil
cohesion, and ponded inner water may have suppressed toe erosion. Also, **the
scale and location of sand boils is strongly governed by the surrounding ground
properties, and sand boils remote from the embankment may not be directly
linked to breaching**.*

Also on the Tokoro: at 太茶苗 (Futachanae), the design HWL was exceeded for
~6 hours on 2016-08-18 and for **~32 hours on 08-20 to 08-22**, nearly reached
again on 08-23; four overtopping locations; the tributary Shibayamasawa levee
breached; ~430 ha inundated (D11 p5).

**→ Actions.**
1. **This is the Tokoro lead the thesis already flagged** (memory:
   "next: Tokoro boil sites" from the Japanese case-validation campaign). D11
   supplies the JSCE finding.
2. **It qualifies the thesis's Tokoro–Tokachi contrast.** Ch2
   §"Historical Field Evidence: The Paradox of Survival and the Tokoro–Tokachi
   Contrast" and Ch3:39 use observed Tokoro sand boiling as evidence that the
   regional stratigraphy is seepage-vulnerable. That inference stands, but the
   JSCE caution means **sand boils remote from the embankment are not
   necessarily evidence of incipient BEP of that levee**. Add the qualification
   — it costs little and pre-empts an obvious challenge. If any Tokoro boil is
   used quantitatively, its distance from the levee toe matters.
3. **The 32-hour design-HWL exceedance at Futachanae** is another regional
   duration datum, intermediate between Tokachi's ~9 h plateau and Abashiri's
   234 h. Useful for the Ch2/Ch3 duration envelope.
4. Kushiro River, same event: **slope sliding failure at left bank KP46.0**
   (D11 p5) — a seepage-family failure in the region in 2016, worth noting
   alongside the Tokachi non-failure.

---

## 6. Climate change — the official Japanese adaptation benchmark (D3 pp187, 195–196)

The revised 十勝川水系河川整備基本方針 (Reiwa 4 / 2022) sets the basic
high-water discharge **with an explicit climate-change allowance**:

- **Design scale retained at 1/150.**
- **Rainfall change multiplier for +2 °C warming: 1.15×**
  (降雨量変化倍率（2℃上昇時の降雨量の変化倍率1.15倍）).
- Target design rainfall = the 1/150 annual-exceedance rainfall × 1.15 ⇒
  **247 mm/48 h at Motoiwa, 297 mm/48 h at Obihiro** (D3 p187, printed 167).
- Method: comprehensive judgement across (a) probability analysis of rainfall
  data with the multiplier applied (sample period 1961–2010), (b) **ensemble
  projected rainfall waveforms from climate models (+2 °C future climate)**, and
  (c) historical flood stretching.
- **New basic high-water peak discharges:**
  - **Motoiwa 21,000 m³/s** (previous plan 15,200)
  - **Obihiro 9,700 m³/s** (previous plan 6,800; the 1/150 estimate was
    ~10,000)
- Historical-flood stretching at Obihiro (event, actual mm/48 h, stretch factor,
  resulting peak m³/s): 1961-07-26 / 135.2 / ×2.198 / 7,600 ;
  1962-08-04 / 163.8 / ×1.814 / 9,700 ; 1972-09-17 / 190.8 / ×1.557 / 10,700 ;
  1981-08-05 / 274.4 / ×1.083 / 7,800 ; 2001-09-11 / 157.5 / ×1.886 / 7,900.
- At Motoiwa: 1962-08-04 ×1.844 → 20,700 ; 1981-08-06 ×1.208 → 16,900 ;
  1998-08-29 ×1.838 → 13,800 ; 2003-08-10 ×1.404 → 18,700 ;
  **2011-09-06 ×2.202 → 19,700**.
- **d4PDF is named** in a D3 interview (p716, printed 684) in the context of
  Yamada Tomohito's (Hokkaido University) advocacy for incorporating d4PDF into
  river planning — the same ensemble the thesis uses.

**→ Actions (high value for Ch6/Ch7 — this is the policy anchor the climate
chapter currently lacks).**
1. **State the official benchmark.** Japanese practice at Tokachi has already
   adopted a climate allowance: **+2 °C, ×1.15 rainfall, and a design discharge
   at Obihiro raised 6,800 → 9,700 m³/s (+43 %)**. The thesis's Phase 3 reports
   the mean annual system $P_f$ rising ~18× and segments above 1e-3/yr going
   2 → 45 from historical to +4K. Placing the engine's climate result beside the
   officially adopted adaptation response makes the Phase 3 chapter *policy
   relevant* rather than purely numerical, and gives the committee a familiar
   reference point.
2. **Be explicit about the scenario mismatch.** The thesis uses d4PDF **+4 K**;
   the official plan uses **+2 °C**. These are different scenarios and must not
   be compared as though equivalent. The right framing: the engine's +4K result
   is a *more severe* scenario than the one currently embedded in Japanese
   design, so the engine's numbers bound the officially planned-for condition.
   State the ×1.15 rainfall multiplier as the officially adopted +2 °C
   equivalent and note that a +4 K multiplier would be larger.
3. **Useful calibration:** the 2016 observed Obihiro peak of 6,334 m³/s is ~93 %
   of the *old* basic high water (6,800) and ~65 % of the *new* (9,700). That
   single sentence conveys how much headroom the design revision added and how
   far the observed record sits below the design condition.
4. **The d4PDF endorsement (p716)** is a citable indication that the ensemble the
   thesis uses is the one Japanese river planning is moving toward — worth a
   sentence in Ch3 §d4PDF to justify the data choice institutionally.
5. **The 2011 Motoiwa entry (×2.202 → 19,700 m³/s)** is relevant to ADR-0044's
   event-set closure: the 2011 event is treated in official planning as one of
   the five reference floods at Motoiwa. It does not change the ADR-0044
   conclusion (which rests on sub-toe trace levels at the study sections and a
   zero-rejection sustained-peak bound), but it is worth noting that 2011 is
   officially significant at basin scale even though it is uninformative for the
   study sections.

---

## 7. Missing material worth requesting

1. **十勝川中流 (Tokachi middle-reach) levee detailed-inspection result map.**
   The folder has only 下流 (D6) and 札内川 (D7). The study sections
   (KP 57.4–63.4) are in the **middle** reach. This sheet would give the
   official 2008 seepage-safety class for the exact modelled sections and is
   the highest-value single missing document. Same series, same publisher
   (帯広開発建設部), same date.
2. **The underlying 66.7 km deficient-section list** (KP ranges) behind D5's
   statistics. Either as a table or as the 重要水防箇所 designation list, which
   D5 p1 says the results were folded into. This would turn D5's aggregate into
   a per-section comparator.
3. **Fukuoka, Ishizuka & Tabata (2019)** itself — needed to resolve the
   $t^*$ coefficient question (§1.5) and to confirm the reach limits (§3.7).
   Already in `references.bib` as `fukuoka_2019`; the PDF does not appear to be
   in `docs/references/`.
4. **Abashiri Sumiyoshi/Hongo geotechnical profile** if the 234-hour case is to
   become a fourth validation study (§4.3).
5. **The full kasumi-tei location table** from D3 p268 at readable resolution,
   to check against the Phase 3 114-node registry (§3.8).
6. **土層縦断図 / geological longitudinal profile** for the Tokachi middle reach
   — already a known open item (the seepage-length-L study names it as the
   trigger for the `nearest` segment policy and reach-scale length-effect
   composition). D1 p7 and D2 p7 both describe it as standard available
   material, which suggests it exists and can be requested.
7. **河川カルテ (river ledger) / 巡視・点検結果** for the study sections — D1
   p4 lists these as the standard record of past deformation, including the
   ⑫漏水・噴砂 (leakage/sand boil) category and the C/d inspection ratings. If
   any study section has a recorded leakage or sand-boil event, that is a
   *directly usable additional Phase 2 observation*, and the D1 p33 clear-vs-
   turbid taxonomy (§1.11) governs how to admit it.

---

## 8. Prioritised action list

> **Execution status, 2026-07-27.** Items 1 and 5 were resolved by verification
> rather than by editing: item 1 is **retracted** (the thesis was correct, see
> §1.4) and item 5 confirmed the thesis's coefficient (see §1.5). The 2008
> screening question (item 30) was resolved by the user. Everything marked
> *done* below has been written into the thesis and the engine docs; the
> remainder is listed in §10 with what is needed to close it.

### Tier 1 — affects claims; do before the Discussion is finalised

| # | Action | Where | Status |
|---|---|---|---|
| 1 | ~~Re-anchor the Japanese comparator to the duration-terminal check; relabel Stage 6.6 C3a/C3b as the like-for-like practice comparator~~ | — | **RETRACTED** (§1.4). Thesis was correct. Evaluation-instant detail added to Ch2 as precision only; Stage 6.6 labelling untouched |
| 2 | Confront the JSCE erosion-dominance verdict; rebut the permeability reasoning, concede the 3/3 breach attributions, state RQ3 as conditional on the surface-mechanism set | Ch7 §Limitations | **done** |
| 3 | Add the 2016 breach attributions as the positive complement to the Phase 2 survival observation | Ch3 | **done** |
| 4 | Pin the Fukuoka reach limits and the reason the result does not transfer | Ch2, Ch3 | **done** — strengthened well beyond the original item by the consolidated-peat finding (§3.7) |
| 5 | Resolve the $t^*$ coefficient | Ch2 | **RESOLVED** (§1.5). Thesis correct; variant now noted |
| 6 | Pin the Obihiro design HWL and footnote the revision history | Ch3 | **done** — 38.26 m used for 2016, with the 0.19 m sub-HWL consequence stated |
| 7 | Verify the Phase 2 reconstructed 2016 Obihiro-datum peak against 38.07 m | engine | **open** — see §10 |
| 8 | State the compound embankment+foundation leakage scope limitation | Ch7 §Limitations | **done** |

### Tier 2 — strong additions, low risk

| # | Action | Where |
|---|---|---|
| 9 | Cite D1 and D2 as the primary Japanese doctrine sources; add `pwri_2014`, `jice_2019` to `references.bib` | Ch2 |
| 10 | Add the **verification triad and screening thresholds** ($F_s\ge1.2\alpha$; $G/W\le1$; $i\ge0.5$; $t^*\ge0.01$) and the $G/W \equiv Z_\text{uplift}$ equivalence | Ch2 |
| 11 | Add the **3 m blanket exemption** and note all study sections are far below it (§1.3) | Ch3, Ch7 |
| 12 | Add the **official BEP mechanism description** (§1.6) and the **Fig. 1.1 progression diagram with its "never reached crest settlement" annotation** (§1.7) | Ch1, Ch2 |
| 13 | Add the **seepage-deficiency statistics**: national 25.1 % (§1.10) and study-area **66.7/359.8 km = 19 %** (§4.1) | Ch1, Ch3 |
| 14 | Add the **duration is required by the standard's own words** quote (§3.3) | Ch1, Ch2 |
| 15 | Add the **Chiyoda aquifer measurement** (15–20 m, 1e-3–1e-2 m/s) as regional corroboration, and state that it exceeds the $k_{aq}$ prior's 95th percentile (§2.1) | Ch3, Ch7 |
| 16 | Add the **200 m distance-marker doctrine** as justification for the segment length (§1.8) | Ch3, ADR-0037/0043 notes |
| 17 | Add the **1/150 design standard** and benchmark the Phase 3 annualised $P_f$ against $6.7\times10^{-3}$/yr (§2.4) | Ch3, Ch6, Ch7 |
| 18 | Add the **official +2 °C / ×1.15 / 6,800→9,700 m³/s adaptation benchmark**, with the +4K-vs-+2 °C mismatch stated (§6) | Ch6, Ch7 |
| 19 | Add the **three-peak 2016 gauge record** as the empirical basis for compound-event treatment (§2.5) | Ch3, Ch4 |
| 20 | Add the **Obihiro warning ladder** to make the conditioning grid interpretable (§2.5) | Ch3 |
| 21 | Add the **sheet-wall failure in sand-gravel → blanket** account as physical support for the ADR-0025 blanketed baseline (§3.4) | Ch4, ADR-0025 rationale |
| 22 | Add the **palaeochannel alignment** evidence (Otofuke urban reach; ~1/3 of Satsunai levee length) as a spatial-heterogeneity argument (§2.10, §3.5) | Ch3, Ch7 |
| 23 | Add the **Abashiri 234-hour survival** as the regional duration envelope (§4.3) | Ch2, Ch3 |
| 24 | Add the **Tokoro sand-boil-remoteness caution** to the Tokoro–Tokachi contrast (§5.2) | Ch2, Ch3 |
| 25 | Add the **basin consequence figures** (9,010 km², 617.4 km² inundation area, 168,000 people, food-supply role) (§2.9) | Ch1, Ch3 |
| 26 | Record the **`remediation_state` provenance chain** (2002/2004 guidelines; FY2003–2007 initiation; drain works; 1999–2003 side-berm at 北帯広築堤) | `docs/tokachi_bep_inputs_provenance.md` |
| 27 | Document the **countermeasure→engine-quantity mapping** as the answer to the `remediation_state` caveat (§1.12) | Ch7, `docs/phase2_report.md` §11 |

### Tier 3 — engine work; all opt-in, no defaults touched

| # | Action | Notes |
|---|---|---|
| 28 | Check the **114-node Phase 3 registry against the kasumi-tei list** (§3.8) | Low effort, protects an RQ4 number |
| 29 | Resolve the **Satsunai gauge question** — 札内 (KP 4.0) vs Nantai (KP 15.0) for the KP 4.2–7.0 nodes (§2.2) | Real open item; sits with residual D8 |
| 30 | **Georeference D7** (or obtain the middle-reach sheet) to establish the official 2008 screening class of the study sections (§4.2, §7.1) | Highest-value validation opportunity in this folder |
| 31 | **Observed-vs-d4PDF hazard check** using the 115-year Obihiro annual-max record (§2.2) | Medium effort, validates the Phase 3 hazard side, currently ensemble-only |
| 32 | Optional **$k_{aq}$ upper-bracket scenario** in the ADR-0046 companion pattern (§2.1) | Scenario only; do not touch the CSV or generated configs (drift guard) |
| 33 | Optional **opt-in remediation sensitivity** converting `remediation_state` labels into a measured $\Delta P_f$ (§1.12) | Default-OFF, bit-identical baseline, `None` dropped from `to_metadata()`; route through `bep-change-control` |
| 34 | Optional **Creager cross-check** of the ADR-0012 $k_{aq}$–$d_{70}$ pairs (§1.9) | Consistency check only ($D_{20}$ vs $d_{70}$); no default change |
| 35 | Consider **Abashiri as a fourth validation case** once a geotechnical profile is obtained (§4.3) | Would test the duration-dominated limit that no existing case covers |

---

## 9. Caveats on this review

- Page-level citations are to **PDF page numbers**; printed page numbers are
  given where observed. The 816-page volume's offset is irregular.
- D6/D7 could **not** be resolved to specific KP values at the available raster
  resolution. No claim here asserts the screening class of any study section.
- The $t^*$ coefficient discrepancy (§1.5) is reported as unresolved: the JICE
  form (8/3) was read from a rendered image and is reliable; whether Fukuoka
  et al. (2019) use 5/2 was not verifiable from this folder.
- Japanese quotations are reproduced verbatim with working English renderings;
  they are not certified translations.
- Values transcribed from figure-embedded tables in D3 (rainfall multipliers,
  discharge bar charts on pp195–196) came from the text layer of chart labels
  and should be visually confirmed before being quoted in the thesis.
- The Chiyoda aquifer data (§2.1) is at KP 37.6, ~20 km downstream of the study
  sections; it is regional corroboration, not section data.

---

## 10. Register of what remains open (as of 2026-07-27)

Everything below is something I could **not** close from the material available.
Each entry states exactly what is needed.

### 10.1 Needs a data artefact I do not have

| # | Item | What is needed | Why it cannot be closed here |
|---|---|---|---|
| R1 | **Verify the Phase 2 reconstructed 2016 Obihiro peak against the official 38.07 m** (§2.5) | Nothing external — this is an engine run. Requires the production Phase 1 `.h5` artefacts to be present locally (`results/*_historical_*.h5`), which are gitignored and may be absent | Cannot be checked by reading; needs the replay executed and the reconstructed Obihiro-datum peak printed |
| R2 | **The 66.7 km deficient-section KP list** behind the 2008 programme statistics (§4.1) | The per-reach table or the 重要水防箇所 designation list for the Obihiro jurisdiction. Request from Obihiro Kaiken / Fukuda-san alongside the items already pending in `tokachi_bep_inputs_provenance.md` §3.1 | Only the jurisdiction aggregate (66.7 / 359.8 km) is published in D5; the KP breakdown is not |
| R3 | **Abashiri Sumiyoshi/Hongo geotechnical profile** for a possible fourth validation case (§4.3) | Borehole logs / blanket and aquifer properties for that reach | D5 gives the loading (234 h above warning level), the remediation and the outcome, but no soil profile, so the case cannot be executed |
| R4 | **Kasumi-tei location table at readable resolution** (§3.8) | The full 霞堤一覧表 from 続十勝川治水史 PDF p. 268 — either a higher-resolution scan, or the same list from another source | The text layer truncates partway through the table. **Note this is a Phase 3 correctness item, not a thesis item:** a kasumi-tei is an intentionally discontinuous levee, so any of the 114 series-system nodes falling in an opening is wrongly composed. Tokachi right bank KP63.8 is 0.4 km from the CSV's KP63.4 |
| R5 | **土層縦断図 (along-levee soil profile) for the Tokachi middle reach** | Already a standing request in `tokachi_bep_inputs_provenance.md` §3.1. D1 p7 and D2 p7 both describe it as routinely available material, which strengthens the case that it exists and can be asked for | Needed to resolve the palaeochannel heterogeneity now documented in Ch3, and to justify a `nearest` segment policy |
| R6 | **河川カルテ / inspection records for the study sections** | The 巡視・点検結果 record, specifically the ⑫漏水・噴砂 category and any C/d ratings | If any study section has a recorded leakage or sand-boil event, that is a **directly usable additional Phase 2 observation**. The D1 p33 clear-water-versus-turbid taxonomy governs admissibility |

### 10.2 Needs an engine run, all opt-in and default-OFF

| # | Item | Scope discipline |
|---|---|---|
| R7 | **$k_\text{aq}$ upper-bracket scenario** at the measured Chiyoda upper bound (§2.1, provenance §6.4) | A **scenario** in the ADR-0046 pattern, not a prior change. Do not edit the CSV or generated configs — `tests/test_configs.py` pins them to ADR-0012/0023 |
| R8 | **Remediation sensitivity** converting `remediation_state` labels into a measured ΔP_f, using the countermeasure→quantity map (provenance §6.3) | Default-OFF, bit-identical baseline, `None` dropped from `Config.to_metadata()` so the Phase 2 replay hash gate keeps passing. Route through `bep-change-control` |
| R9 | **Observed-vs-d4PDF hazard check** using the 115-year Obihiro annual-max record (§2.2) | Read-only comparison; validates the Phase 3 hazard side, which is currently ensemble-only |
| R10 | **Migration-capable bank-retreat surface mechanism** (§5.1, and now Ch7 §Limitations) | This is the substantive one. The corrected-USACE scour model returns exactly zero at all 114 nodes while two levees in this system failed by falling-limb channel migration in 2016. A point-scour formulation cannot represent that. Recommended in Ch8 rather than executed |
| R11 | **Satsunai gauge choice** — 札内 (KP 4.0) vs Nantai (KP 15.0) for the KP 4.2–7.0 nodes (§2.2) | Engine-side only by explicit decision; not carried into the thesis, since the Satsunai is not assessed for BEP |

### 10.3 Needs a judgement I should not make unilaterally

| # | Item | The question |
|---|---|---|
| R12 | **Whether the JSCE rebuttal in Ch7 is pitched correctly** | The text now rebuts the permeability reasoning, concedes the empirical record, and offers a susceptibility-versus-realised-rate reconciliation. Whether to press the rebuttal harder or soften it is an authorial and supervisory call, and it touches a headline RQ3 claim. Worth reviewing against `bep-external-positioning` before the defence |
| R13 | **Whether the two $t^*$ variants warrant a footnote or the body text** | Currently in the body of Ch2. Fukuoka 5/2 with floodplain-referenced variables; JICE 8/3 with toe-referenced variables. Both are correct for their own definitions; the constant difference is presented as arising from the differing length scale, which is an inference and is flagged as such |
