# Task: exhaustively mine 続十勝川治水史 (816 pp) and act on the findings

## Mission

`docs/references/tokachi_river_basin/inr9av000000b2i3.pdf` is the 816-page
*Continued History of Tokachi River Flood Control* (続十勝川治水史), published
October 2023 by the Hokkaido Regional Development Bureau, Obihiro Development
and Construction Department. It is the official documentary record of the river
system this thesis studies.

**A prior review sampled roughly 120 of its 816 pages. Your job is to cover all
816 pages, extract every item relevant to this research, and then act on what
you find** — updating the engine and the thesis where warranted, and escalating
to me where a genuine conflict exists.

Both repositories are in scope:

- `d:\repositories\bep-reliability-engine` — the BEP reliability engine (this repo)
- `d:\repositories\msc-thesis` — the thesis text (a configured additional working directory)

---

## Step 1 — Orient before you extract (do not skip)

Read these first. They will save you hours and stop you from re-deriving or
contradicting settled decisions.

1. **architecture and decision records** — the repo contract. Note especially: configs are *generated*,
   not hand-edited; prior CoVs are fixed constants from the thesis prior table;
   the production campaign is closed.
2. **Apply the tracked repository controls** before starting:
   - `docs/architecture.md` — what must never break
   - accepted ADRs under `docs/decisions/` — change control, configuration
     ownership, settled reversals, and known external-data traps
   - `docs/conventions.md` — ADR lifecycle, companion-note naming, and house style
   - `docs/project_log.md` — dated evidence history and withdrawn findings
3. **`docs/tokachi_basin_document_review_2026-07-27.md`** (1688 lines) — the
   prior review of this folder. §10 is a register of what is still open. **This
   is your baseline: do not redo it, but do independently verify anything you
   intend to rely on.** It contains one worked example of a retracted
   over-reading (§1.4) — read that section specifically, because it shows the
   failure mode you are most at risk of repeating.
4. **`docs/tokachi_bep_inputs_provenance.md`** (535 lines) — the per-cell audit
   trail for the geotechnical CSV. **§4 was added by the prior review from this
   very document.** You must understand this file thoroughly before proposing any
   change to a value, because it records where each current number came from.

---

## Step 2 — The artefact and how to read it

- **375 MB, 816 pages, Japanese, with a working text layer.** PyMuPDF extracts it
  cleanly; no OCR needed.
- Use the repo venv: `./.venv/Scripts/python.exe`. On Windows you **must** set
  `PYTHONIOENCODING=utf-8` or Japanese output dies with a `cp1252` error.
- Write your tooling to the scratchpad, not the repo. A three-script pattern
  worked well previously and is worth reproducing:
  - an extractor that writes one text file with `===== [file] PAGE n/N =====`
    delimiters,
  - a searcher that takes terms and reports `file → page → ±N chars of context`,
    with a `--count` mode that reports only page lists,
  - a page-printer that dumps a given page range.
- **Page-numbering warning:** the PDF page number and the printed page number
  differ by an irregular offset (unnumbered plates). Cite **PDF page numbers**
  as primary and give the printed number in parentheses when visible. The
  offset ranges from about 20 to 28 across the volume — never assume it.
- **Tables and figures often carry the numbers.** Much of the quantitative
  content is inside figure-embedded tables whose text layer extracts as loose
  column fragments in reading order. When a table matters, **render the page
  region to PNG at high magnification and read it visually** rather than trusting
  the fragment order. Several numbers in this document only make sense when seen
  in layout. The prior review found one equation whose text layer was
  ambiguous and which had to be settled by rendering the image.
- **`docs/references/` is gitignored.** The PDFs are machine-local. Never commit
  them; do commit your findings.

---

## Step 3 — Coverage protocol (this is the part that must not be skimped)

The instruction is *the entire document*. A keyword sweep alone will not satisfy
it, because the highest-value material in this volume is in narrative chapters
and figure tables that no keyword list anticipates.

Do both of the following:

**(a) Sequential pass.** Work through all 816 pages in blocks (40–60 pages is a
workable unit). For each block, record in a running ledger: the block range, the
chapter/section it covers, and either the items extracted or an explicit
"nothing relevant" verdict. **Keep this ledger in the deliverable** so coverage
is auditable — I want to be able to confirm the whole document was read, not
just searched.

**(b) Keyword sweep, as a safety net over the sequential pass.** At minimum:
パイピング, 噴砂, 漏水, 基盤漏水, 複合漏水, 浸透, 盤膨れ/盤ぶくれ, 被覆土層,
透水係数, 動水勾配, 局所動水勾配, 粒径, 均等係数, ボーリング, 砂礫, 泥炭,
決壊, 越水, 侵食, 洗掘, 法尻, 川裏, ドレーン, 遮水, ブランケット, 押え盛土,
詳細点検, 質的整備, 堤防強化, 重要水防, 計画高水位, 計画高水流量, 基本高水,
既往最高, 最高水位, ピーク流量, 継続時間, 水位観測所, 流量観測所, 距離標,
樋門, 排水機場, 霞堤, 丘陵堤, 気候変動, 降雨量変化倍率, 流域治水.

The following clusters are **known to be unread** by the prior review and are
where I would start prioritising within the sequential pass:

| PDF pages | Why it matters |
|---|---|
| **51–71, 74–84** | 既往洪水の概要 and the 1981/1988 flood chapters. Expected to carry **peak stage, peak discharge and duration for every major historical event**. Highest expected value in the volume — an observed stage/duration record is exactly what a duration-governed failure model needs. |
| **104** | The **only** 噴砂 (sand boil) hit in all 816 pages. Read it carefully and in context. |
| **111–180** | Flood-control plan revisions; repeated 計画高水位 tables. The design-level revision history. |
| **164–204** | ピーク流量 cluster and the 基本高水 determination, including the climate-adjusted 2022 revision. |
| **405–425** | 排水機場 and 樋門 (drainage pump stations, sluices) plus a ドレーン hit at 423. Interior drainage — bears on the Satsunai KP25.0 landside-overtopping mechanism that the model set omits. |
| **478–540** | Dam chapters. 495–497 carry ボーリング, 砂礫, 粒径, 遮水 — grain-size and permeability data, though for dam materials rather than levee foundations. Judge relevance carefully. |
| **605–660** | Station inventories, 距離標 tables, bridges. |
| **688–760** | Recent works, climate adaptation, 流域治水. **700 is one of only two パイピング hits.** |
| **795–816** | Closing chapters and the year-by-year chronology. |

---

## Step 4 — Triage every finding into one of four classes

Label each item explicitly. The class determines what you do with it.

### Class A — NEW data (no current equivalent)
**You are pre-approved to integrate this.** Add it to the thesis where it
strengthens the argument, and record it in the engine's provenance file. Use
judgement about where it belongs; do not pad chapters with material that does
not earn its place.

### Class B — CORROBORATING (independently supports a value I already use)
**You are pre-approved to integrate this.** This is the most valuable class for a
defence: it converts an asserted number into a sourced one. Record it in
`docs/tokachi_bep_inputs_provenance.md` and cite it in the thesis where the value
is introduced. **Do not change the value itself** — corroboration means the
current value stands with better support.

### Class C — CONFLICTING (a different value for a parameter I already document)
**Stop. Do not edit. Escalate to me.** See the conflict protocol in Step 5.

### Class D — CONTEXT (narrative, institutional, historical; no numbers)
Judge whether it strengthens the Introduction, Study Area or Discussion. Much of
the most rhetorically useful material in this volume is Class D — first-hand
engineer accounts, official statements of mechanism, documented countermeasure
failures. Integrate the good ones; do not hoard the rest.

---

## Step 5 — Conflict protocol (Class C)

When this document gives a different value for something already documented, do
**not** assume the newer or more official-looking source wins. Produce a
comparison I can adjudicate:

1. **Trace my current value properly first.** Read
   `docs/tokachi_bep_inputs_provenance.md` for that cell, find the owning ADR in
   `docs/decisions/`, and read the thesis passage that uses it. State what the
   current value is, where it came from, and on what reasoning it was adopted.
   Do this *before* forming a view.
2. **Characterise the new value precisely.** What exactly was measured, where,
   when, by whom, at what scale, under what definition? A value from a different
   KP, a different geomorphic setting, a different plan revision, or a different
   variable definition is often **not** in conflict at all — it is a different
   quantity. Check this before calling it a conflict.
3. **Present both cases** with the physical consequence of choosing each,
   including which direction is conservative for BEP failure probability.
4. **Give a clear recommendation** and say how confident you are.
5. **Then wait for my decision.** Do not implement either side.

Known live example to expect: the prior review found the Chiyoda floodplain
aquifer measured at 15–20 m thick with k = 1e-3 to 1e-2 m/s (PDF p. 359), against
CSV values of `D_aq` 7–11 m and `k_aq` 6e-5 to 3.0e-3 m/s. That was **correctly**
classified as regional corroboration rather than conflict, because Chiyoda is
KP 37.6 — some 20 km downstream, in a different setting — and no prior was
changed. It did, however, surface a real concern: the measured upper bound lies
beyond the 95th percentile of the `k_aq` prior. That is the standard of reasoning
I want: separate "different quantity" from "same quantity, different value", and
follow the consequence through either way.

---

## Step 6 — The cost-of-change rule (read this twice)

**This is the single most important operational constraint, and it is not
obvious from the code.**

`data/processed/tokachi_bep_inputs.csv` is not an ordinary data file. Changing a
mean in it invalidates, in cascade:

- all **8 production fragility sweeps** at N = 1e5 (`configs/` are regenerated
  from the CSV, so their **config hashes change**);
- the **Phase 2 posterior update**, whose replay reconstructs runs from the
  metadata snapshot and **hash-checks the config** — a changed hash breaks the
  gate outright;
- the **Phase 3 RQ3/RQ4 campaign** that consumes the persisted curves;
- the **Stage 6.6 gap decomposition**, which is bit-identity-pinned to the
  persisted sweeps;
- the ADR-0039 / 0040 / 0045 / 0046 companion studies;
- `tests/test_configs.py::test_config_matches_csv_and_thesis_priors`, the drift
  guard that pins configs to the CSV and to the ADR-0012/0023 decisions.

**Therefore: a CSV mean change is a full campaign re-run, not an edit.** Default
to the cheaper and usually more correct action — **record the new evidence in the
provenance file and discuss it in the thesis** — and reserve an actual value
change for a case strong enough to justify re-running everything. When you do
propose one, state the re-run cost explicitly in the same breath as the
recommendation, so I can weigh it.

Related frozen surfaces, all covered by the repository's change-control rules:

- **Prior CoVs are fixed constants** from the thesis prior table
  `tab:priors_phase1`. They are not yours to adjust.
- **Any new configuration axis must be opt-in, default-OFF, and bit-identical at
  baseline**, with `None` dropped from `Config.to_metadata()` so pre-existing
  config hashes survive. This is the ADR-0037/0045 pattern and the Phase 2 gate
  depends on it.
- **Never hand-edit `configs/*.yaml`.** Re-run `scripts/generate_configs.py`.
- `evaluate_realization` / `EvaluationResult` are a frozen API (ADR-0011).

If a finding genuinely warrants a new architectural decision, write a numbered
ADR. **Next free number is 0047.** Follow `docs/decisions/ADR_TEMPLATE.md` and
the conventions in `docs/conventions.md`.

---

## Step 7 — Deliverables

1. **A findings document** at
   `docs/tokachi_chisuishi_full_review_<YYYY-MM-DD>.md`, containing:
   - the **page-coverage ledger** from Step 3(a) — non-negotiable, this is how I
     verify the whole document was read;
   - every finding, with PDF page (and printed page), a verbatim Japanese
     quotation for anything load-bearing, a working English rendering, its
     **class (A/B/C/D)**, and what you did or propose to do;
   - a **Class C conflict register** — the escalations, formatted per Step 5;
   - an explicit list of what you looked for and did **not** find, since a
     negative result on an open question is a real result here.
2. **Engine changes**, as warranted: provenance additions, an ADR if a decision
   was made, opt-in scenario code only under the Step 6 rules.
3. **Thesis changes**, as warranted, in `d:\repositories\msc-thesis`. New sources
   need `references.bib` entries. **Romanise Japanese titles with a bracketed
   English gloss** rather than pasting raw CJK — the bibliography currently
   throws ~168 non-fatal Unicode errors under pdfLaTeX and there is no reason to
   add more.
4. **A prioritised recommendation list** for me: what you did, what you propose,
   what you escalated, and what needs data neither of us has.

---

## Step 8 — Verification before you report

- **Thesis:** `latexmk -pdf -interaction=nonstopmode report.tex`. Do **not** pass
  `-halt-on-error` — a pre-existing font-expansion warning in Chapter 4 will stop
  the build spuriously. Success criteria: a PDF is produced, and
  `grep -c "undefined" report.log` returns **0**. The ~168 `Unicode character`
  errors are pre-existing and non-fatal; confirm you have not increased the count.
- **Engine:** `pytest -m "not slow"` must be green (**495 passed** at the time of
  writing). If you touched anything the sweeps depend on, say so loudly.
- **If you changed nothing in a repo, say that too.** A clean "no change needed
  here" is a valid and useful outcome.

---

## Guardrails

- **Report faithfully.** If a number is illegible, say illegible. If a table is
  ambiguous, say ambiguous. Never reconstruct a value you could not read — the
  provenance file's value is that every cell is traceable, and one invented
  number destroys that.
- **Distinguish what the document says from what you infer from it.** Both are
  welcome; conflating them is not.
- **Flag conversions and datums.** This project has already been bitten twice by
  external data: a unit conversion off by ~105.6× and a rating-error placeholder
  taken from a demo notebook. Elevations here are T.P. (Tokyo Peil); the engine
  works in m MSL with surveyed toe elevations. Check before you equate them.
- **Watch for plan-revision drift.** The design high water level at Obihiro
  appears in this volume as 38.14, 38.26, 38.44 and 38.56 m across different plan
  revisions. Any figure you extract must be tied to a named revision and date, or
  it is worthless.
- **Do not re-litigate settled reversals.** The accepted ADRs and project log list them.
  If something in this document appears to overturn an ADR, that is a Class C
  escalation, not an edit.
- **Physics stays in the engine.** No physics in scripts or notebooks; strict SI
  in kernels; unit conversion only at the M1/M3 boundary.

## Definition of done

All 816 pages accounted for in the ledger; every finding classified and either
integrated (A, B, D) or escalated (C); both repos build and test green; and a
recommendation list on my desk that tells me exactly what I am being asked to
approve and what it would cost.

Work autonomously within these bounds. Ask me only about Class C conflicts and
about anything that would trigger a campaign re-run.
