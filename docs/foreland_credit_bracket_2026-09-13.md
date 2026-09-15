# The foreland seepage-length credit, and the Obihiro gauge node

Numbers document of record, **2026-09-13**. This is the single source later
thesis sessions quote from for both subjects.

Governing decisions: **ADR-0052**
(`docs/decisions/0052-foreland-seepage-length-credit.md`) with its companion
measurement `docs/decisions/adr0052-foreland-seepage-credit-bracket.md`; and the
dated amendments made in place to **ADR-0028** (the justification clause) and
**ADR-0035** (the gauge node).

Every figure below was computed or read in the session of 2026-09-13 from a
committed artifact. **No production value changed.**

---

## 0. Provenance

| what | where it comes from |
|---|---|
| the knob | `bep_reliability_engine/sellmeijer.py` (`resolve_effective_seepage_length`), `evaluator.py` (`foreland_seepage_credit`), `config.py` (`Config.foreland_seepage_credit`) |
| Phase 1 bracket | `docs/decisions/adr0052-foreland-credit-companion.json`; driver `python scripts/foreland_credit_bracket_study.py --reading matrix` |
| Phase 3 bracket | `docs/decisions/adr0052-foreland-credit-annualisation.json`; driver `python scripts/foreland_credit_annualisation.py` |
| the sweeps | `results/sensitivity/adr0052_foreland_credit/` (12 full-N sweeps; `results/` is gitignored and regenerable by the driver) |
| the frozen prediction | `docs/decisions/adr0052-foreland-credit-prereg.md`, SHA-256 `ffb7f15b4387103282b0092f0b2399f9e1c7f6344df4b4be567c6cc75227c86f`, pinned in the companion JSON and by test |
| the baseline compared against | `results/tokachi_kp*_historical_matrix.h5`, the persisted production sweeps |
| the source permission | `docs/references/tr-15_technischrapportzandmeevoerendewellen.pdf` §4.4.1 Eqs. (19)/(20) and §4.4.2 |
| the gauge measurement | `bayesian_reliability_updating` replay through `replay_event` + `apply_survival_filter`, all four matrix strata at N = 1e5 |
| the gauge's primary source | `data/raw/Uncertainty_HQrelation.xlsx`, sheet `TokachiRiv._Obihiro` |

---

## 1. The finding, and why the baseline does not change

`hydraulics.response_factor` splits the gross head into three resistances in
series — `r_e = lambda_in / (lambda_out_eff + L + lambda_in)`, the USACE
EM 1110-2-1913 Appendix B Case 7a landside head factor. Since ADR-0028 that
split reaches the **uplift and heave gate only**: both piping heads are gross,
and both limit states evaluate Sellmeijer's `H_c` at the under-levee `L`. The
foreland entry resistance therefore attenuates neither piping load.

TR Zandmeevoerende Wellen (1999) §4.4.1 Eq. (19) gives the entry-point
displacement `L'_v = lambda_1 * th(L_v / lambda_1)` — Eq. (20) defines `th` as
the hyperbolic tangent — which is the **same tanh** the engine already uses for
`lambda_out_eff`. §4.4.2 extends it to piping. Verbatim, read from the rendered
PDF page (printed page 44; the scan's text layer is OCR and garbles the
symbols, so this was taken from the page image, not the text layer):

> **4.4.2 Invloed voorland op het mechanisme Piping**
>
> Net als bij opbarsten is het effect van voorland dat het theoretische
> intreepunt, ten opzichte van een situatie zonder voorland, in de richting van
> het buitenwater wordt verplaatst, volgens dezelfde formule. Daardoor wordt de
> theoretische kwelweglengte met L'_v vergroot.
>
> Zowel in de klassieke regels van Bligh of Lane, als bij de regel van
> Sellmeijer mag de toename van de kwelweg in rekening worden gebracht.

`mag` is *may*. Declining a permissive credit is a recognised conservative
simplification, so **the production baseline still declines it** and this
document measures a bracket.

### 1.1 Provenance checks run this session

- **Pol (2022) thesis p. 158, verbatim**, on the assumptions behind Eq. 7.13:
  "This solution is based on horizontal flow in a leaky aquifer, vertical flow
  (leakage) through the blanket, an infinitely long polder blanket and **no
  riverside blanket**".
- **`pol_sie_2024.pdf` full-text search: ZERO hits** for "riverside blanket",
  "riverside", "foreshore" and "foreland" across its 18-page, 81 171-character
  text layer. Its 21 "blanket" hits are all the polder or landside blanket
  ("polder blanket thickness", "blanket uplift", "cohesive blanket layer").
- `sellmeijer_2011.pdf`: zero hits for "blanket" at all.
- Therefore the foreland entry term is **this repository's own addition**
  (ADR-0005/0006), not an inheritance, and ADR-0028's clause "Raw-static
  inherits a simplification Pol already made; it introduces no new one" is wrong
  on both premises. That clause is amended in place in ADR-0028; the decision it
  supports stands.

### 1.2 What the credit reaches

| reached | not reached — stays on the physical under-levee `L` |
|---|---|
| the Sellmeijer critical head `H_c`, **single-source**, feeding both the static comparator and the transient `H_eq` anchor | the critical pipe length `l_c` (Eq. 13); the traverse length and the `Z_transient = L - l_e` criterion; the `L` in the Eq. (5) rate denominator; the `L` in `r_e` and the leakage lengths; the erosion head `H_erosion`; the uplift and heave gate |

Every entry in the right column is pinned by a test. Because `H_c` is
single-source, **both branches move** — the structural opposite of ADR-0049
(transient-only) and ADR-0050 (gate-only).

---

## 2. The prior-mean series split (the Part 1 reproduction)

Computed through `leakage_length_in`, `leakage_length_out`, `response_factor` and
`compute_critical_head` from each committed config's own prior means:

| section | `lambda_in` | `lambda_out_eff` | `L` | `Sigma` | entry share | `r_e` | `H_c(L)` | `H_c(L_eff)` | `kappa` |
|---|---|---|---|---|---|---|---|---|---|
| KP 57.4 | 102.470 | 98.418 | 33.0 | 233.887 | 42.08 % | 0.4381 | 2.034 | 7.082 | 3.481 |
| KP 58.8 | 116.619 | 115.737 | 35.0 | 267.356 | 43.29 % | 0.4362 | 2.130 | 7.954 | 3.734 |
| KP 60.0 | 87.464 | 87.464 | 34.8 | 209.728 | 41.70 % | 0.4170 | 1.956 | 6.062 | 3.099 |
| KP 62.0 | 38.730 | 31.491 | 40.0 | 110.221 | 28.57 % | 0.3514 | 3.214 | 5.409 | 1.683 |

`r_e` reproduces the thesis §3.3.2 values 0.438 / 0.436 / 0.417 / 0.351. The
entry resistance is **29 to 43 per cent** of the total series resistance.

Head share across `L`, and the overstatement of the piping load that follows
from taking the gross head over that share alone:

| section | intact series (gate regime) | overstatement | post-rupture (`lambda_in` bypassed) | overstatement |
|---|---|---|---|---|
| KP 57.4 | 14.11 % | x7.087 | 25.11 % | x3.982 |
| KP 58.8 | 13.09 % | x7.639 | 23.22 % | x4.307 |
| KP 60.0 | 16.59 % | x6.027 | 28.46 % | x3.513 |
| KP 62.0 | 36.29 % | x2.756 | 55.95 % | x1.787 |

### 2.1 Design load-to-resistance ratios — a correction

The review that opened this question quoted "0.032 / 0.074 / 0.129 / 0.154".
Those were computed by attenuating the head **and** extending `L`, which
double-counts the same foreland. Recomputed as `(HWL - z_toe) / H_c(L_eff)`:

| section | HWL | `z_toe` | gross head | `H_c(L)` | `H_c(L_eff)` | gross / `H_c(L)` | **gross / `H_c(L_eff)`** |
|---|---|---|---|---|---|---|---|
| KP 57.4 | 39.21 | 38.30 | 0.910 | 2.034 | 7.082 | 0.447 | **0.128** |
| KP 58.8 | 41.03 | 38.50 | 2.530 | 2.130 | 7.954 | 1.188 | **0.318** |
| KP 60.0 | 42.75 | 40.00 | 2.750 | 1.956 | 6.062 | 1.406 | **0.454** |
| KP 62.0 | 46.39 | 44.90 | 1.490 | 3.214 | 5.409 | 0.464 | **0.275** |

The KP 57.4 value is **0.128** (0.910 / 7.0815 = 0.12850), not the 0.129 the
review carried.

---

## 3. Phase 1: the design level

Failing realizations of 1e5 at each section's design HWL grid point. Both arms,
both branches.

| section | stage [m MSL] | baseline static | baseline transient | half credit (s / t) | full credit (s / t) |
|---|---|---|---|---|---|
| KP 57.4 | 39.25 | 207 | 0 | 0 / 0 | 0 / 0 |
| KP 58.8 | 41.00 | 72 206 | 26 273 | 0 / 0 | 0 / 0 |
| KP 60.0 | 42.75 | 91 650 | 31 427 | 224 / 0 | 0 / 0 |
| KP 62.0 | 46.50 | 393 | 15 | 0 / 0 | 0 / 0 |

The baseline counts reproduce the published design-level anchors exactly (the
RQ1 index table carries KP 58.8 72 206 / 26 273 and KP 60.0 91 650 / 31 427).

**Under the full credit every design level is 0 of 1e5 on both branches, at all
four sections**, confirming the independent audit. Under the half credit the
same holds except at KP 60.0, which keeps **224** static rows and none transient.

The KP 58.8 row is the one to quote: **half** the entry-point displacement takes
72 206 static and 26 273 transient failures to exactly zero.

---

## 4. Phase 1: the cancellation test

Pre-registered before the arms ran. `rho > 1` at **every resolved level, of every
section, in both arms** — 101 resolved levels, 101 above unity.

| section | arm | evaluated | resolved | `rho` range | static cells moved |
|---|---|---|---|---|---|
| KP 57.4 | half | 8 | 8 | 2.005 to 10.220 | 962 648 |
| KP 57.4 | full | 1 | 1 | 8.726 | 1 187 918 |
| KP 58.8 | half | 12 | 12 | 1.399 to 12.262 | 1 160 356 |
| KP 58.8 | full | 5 | 5 | 6.120 to 20.607 | 1 750 478 |
| KP 60.0 | half | 16 | 16 | 1.138 to 51.783 | 820 746 |
| KP 60.0 | full | 10 | 10 | 2.749 to 65.412 | 1 576 024 |
| KP 62.0 | half | 26 | 26 | 1.010 to 2.279 | 421 982 |
| KP 62.0 | full | 23 | 23 | 1.031 to 2.811 | 790 935 |

No `trans_not_static` row appears in any baseline or arm at any level, so no
ADR-0030 forward-Euler barrier jump contaminates the comparison.

**Prediction against outcome** (full table in the companion note §5.3): P1, P2,
P3 and P5 held; **P4 failed**. P4 predicted the per-section displacement would
order by `kappa`; it orders KP 60.0 > KP 58.8 > KP 57.4 > KP 62.0 instead, and
only the last place held. A `rho` departure is set by where a section's baseline
curves sit relative to the stages that stay resolvable, not by the input's own
magnitude — **never read a mechanism off a `rho` departure alone.**

---

## 5. Phase 1: stage displacement

Stage at which the bound's exceedance probability reaches each anchor, and the
shift from baseline [m]:

| section | anchor | baseline [m MSL] | half credit | shift | full credit | shift |
|---|---|---|---|---|---|---|
| KP 57.4 | 1e-3 | 39.45 | 41.46 | +2.02 | 43.20 | +3.76 |
| KP 57.4 | 1e-2 | 39.64 | 41.81 | +2.17 | 43.70 | +4.05 |
| KP 57.4 | 0.1 | 39.99 | 42.33 | +2.34 | 44.43 | +4.44 |
| KP 57.4 | 0.5 (median) | 40.58 | 43.11 | +2.54 | 45.49 | +4.92 |
| KP 58.8 | 1e-3 | 39.71 | 42.08 | +2.37 | 44.07 | +4.35 |
| KP 58.8 | 1e-2 | 39.92 | 42.44 | +2.52 | 44.60 | +4.68 |
| KP 58.8 | 0.1 | 40.28 | 43.00 | +2.72 | 45.40 | +5.12 |
| KP 58.8 | 0.5 (median) | 40.89 | 43.82 | +2.93 | 46.57 | +5.67 |
| KP 60.0 | 1e-3 | 41.22 | 42.92 | +1.69 | 44.34 | +3.12 |
| KP 60.0 | 1e-2 | 41.41 | 43.20 | +1.79 | 44.74 | +3.33 |
| KP 60.0 | 0.1 | 41.72 | 43.64 | +1.92 | 45.36 | +3.64 |
| KP 60.0 | 0.5 (median) | 42.24 | 44.30 | +2.06 | 46.25 | +4.01 |
| KP 62.0 | 1e-3 | 46.45 | 47.28 | +0.82 | 48.05 | +1.60 |
| KP 62.0 | 1e-2 | 46.78 | 47.68 | +0.90 | 48.53 | +1.75 |
| KP 62.0 | 0.1 | 47.33 | 48.33 | +1.00 | 49.28 | +1.95 |
| KP 62.0 | 0.5 (median) | 48.25 | 49.34 | +1.09 | 50.42 | +2.16 |

Summarised, the shift of the bound across the four anchors:

| section | half credit | full credit |
|---|---|---|
| KP 57.4 | +2.02 to +2.54 m | +3.76 to +4.92 m |
| KP 58.8 | +2.37 to +2.93 m | +4.35 to +5.67 m |
| KP 60.0 | +1.69 to +2.06 m | +3.12 to +4.01 m |
| KP 62.0 | +0.82 to +1.09 m | +1.60 to +2.16 m |

The independent audit that opened this question expected +1.6 to +2.2 m at
KP 62.0, +3.2 to +4.0 at KP 60.0, +4.4 to +4.7 at KP 58.8 and +3.8 at
KP 57.4 for the full credit. **KP 62.0 and KP 57.4 reproduce exactly**; KP 60.0
reproduces to within 0.08 m at its low end; and KP 58.8's upper end is larger
here (+5.67 against +4.7) because this table carries the median anchor, which
that range did not. Nothing in it is contradicted.

---

## 6. Phase 3: the credit through the annualisation

Matrix reading, prior side. Composition and annualisation **imported** from
`scripts/conductivity_annualisation_study.py`, which imports them from the
campaign, so the production code path runs. Gate 1 (baseline reproduces
`rq4_annual.csv` exactly, 228 rows x 20 fields) and gate 3 (220 non-BEP segment
rows bit-identical across every arm) both passed.

| section | scenario | baseline | half credit | full credit | full / baseline |
|---|---|---|---|---|---|
| KP 57.4 | historical | 7.548e-04 | 0 | 0 | 0 |
| KP 57.4 | +4K | 9.542e-03 | 9.724e-04 | 9.114e-04 | 0.0955 |
| KP 58.8 | historical | 8.467e-03 | 2.034e-04 | 1.951e-04 | 0.0230 |
| KP 58.8 | +4K | 4.462e-02 | 3.391e-03 | 2.532e-03 | 0.0568 |
| KP 60.0 | historical | 2.025e-03 | 1.939e-06 | 0 | 0 |
| KP 60.0 | +4K | 1.534e-02 | 4.829e-04 | 2.433e-05 | 0.0016 |
| KP 62.0 | historical | 1.006e-03 | 3.228e-04 | 2.099e-04 | 0.2087 |
| KP 62.0 | +4K | 1.278e-02 | 9.155e-03 | 8.475e-03 | 0.6633 |

### 6.1 The RQ3 dominance statement does not survive

Piping's share of the summed annual contribution, historically:

| section | baseline | half credit | full credit |
|---|---|---|---|
| KP 57.4 | 1.000 | 0.000 | 0.000 |
| KP 58.8 | 0.977 | 0.043 | 0.000 |
| KP 60.0 | 1.000 | 1.000 | 0.000 |
| KP 62.0 | 0.812 | 0.407 | 0.059 |

The published claim is **81 to 100 per cent** historically, and the baseline pass
reproduces exactly that. Under the full credit the four shares are **0.000,
0.000, 0.000, 0.059** — piping stops leading anywhere and overflow carries the
number. Across all eight section-and-climate cells the full credit leaves **0 of
8** in the published band and the half credit 2 of 8.

This is the largest displacement of an RQ3 headline any knob in the register has
produced. It does **not** refute the published result, which takes the
conservative side of a permissive choice; it states what that choice is worth.
**The dominance claim must not be quoted without it.**


### 6.2 The posterior side, and why it is the same

**Added 2026-09-14.** Section 6.1 above annualises the **prior** side. The
published RQ3 and RQ4 headline does not: `scripts/phase3_campaign.py` defaults
to `bep_source = posterior`, and the thesis's KP 58.8 historical
7.45e-3 is the posterior row of `rq4_annual.csv` (the prior row is 8.47e-3). So
the prior-side table qualified numbers the thesis does not print, and the
like-for-like comparison had to be measured on the side the claim lives on.

It was, through `scripts/foreland_credit_annualisation.py --side posterior`
after replaying all eight ADR-0052 arms through the ordinary Phase 2 CLI. Gate 1
(the baseline pass reproduces `rq4_annual.csv` field for field, 228 rows x 20
fields) and gate 3 (220 non-BEP rows bit-identical across every arm) both
passed.

**The arm values are bit-for-bit identical to the prior side at all 8 of 8
cells.** That is not a coincidence and it is the finding:

> **Under the credit, the 2016 survival record rejects nothing.** All eight arm
> replays return `accepted 100,000 of 100,000 rows (rejection 0.00%)` — both
> arms, all four sections. The credited `H_c` is so far above the observed
> loading that no realization fails under it, so the posterior *is* the prior
> and the survival constraint carries no information at all.

Only the *baseline* differs between the two sides, because only the baseline is
actually filtered by the 2016 record. The consequence for the headline is
therefore that the RQ3 verdict is **unchanged** on the side that matters:

| section | baseline (posterior) | half credit | full credit |
|---|---|---|---|
| KP 57.4 | 1.000 | 0.000 | 0.000 |
| KP 58.8 | 0.974 | 0.043 | 0.000 |
| KP 60.0 | 1.000 | 1.000 | 0.000 |
| KP 62.0 | 0.812 | 0.407 | 0.059 |

Full credit leaves **0 of 8** section-and-climate cells inside the published
81-to-100-per-cent band, exactly as on the prior side. §6.1's conclusion stands;
what changes is that it now rests on the comparison the thesis actually makes.

There is a second-order point worth keeping. The credit and the 2016 update
both push in the same direction — both remove failing realizations — but they
cannot compound, because the credit removes the very realizations the update
would have rejected. A study that credited the foreland *and* claimed the
survival constraint as additional evidence would be counting the same evidence
twice. Here it is measured to be exactly zero the second time.

---

## 7. The Obihiro gauge node, corrected from KP 56.6 to KP 56.73

### 7.1 The evidence

`bayesian_reliability_updating/events.py` selected the gauge's rating at
KP 56.6. That is a node of the regular 0.2 km survey grid — the design
*reference point*, which the thesis distinguishes from the station
(`appendix-c.tex`: "The Obihiro gauge lies 0.1 km upstream at KP 56.7").

The decisive evidence is a **primary station register**, not an inference from
the rating table's off-grid spacing (23 of its 512 nodes are off-grid, and three
of those sit within 3 cm of each other near KP 43.3, so "off-grid implies
station" is not a safe rule). `data/raw/Uncertainty_HQrelation.xlsx` — the same
workbook ADR-0042 decision 6 takes the rating error from — carries a sheet
`TokachiRiv._Obihiro` whose first data row reads `River = Tokachi`,
`point = "Obihiro"`, `KP = 56.73`, with that station's own rating
`HQ_a = 135.36`, `HQ_b = -32.62`. Those are **exactly** the KP 56.73 row of the
committed `HQrelation_TokachiRiv_2017.csv`, and not the KP 56.6 row
(140.33, -32.49). Its companion sheet names "Nantai Bridge" at KP 15 the same
way. Phase 3 already read the node this way
(`system_integration/segments.py`, `docs/phase3_report.md`); Phase 2 did not.

`default_2016_source` now uses 56.73, pinned by two tests in
`tests/test_phase2_events.py`, one of which requires the node to carry the
station register's own coefficients so a silent revert cannot pass.

### 7.2 What it moves

All four matrix strata, N = 1e5, through the engine's own replay and filter.

**Production (`anchor='trace_right'`).** The surveyed trace pins the peak, so the
peak and the trough floor are *exactly* unchanged and only the interior of the
wave moves (max 0.106 to 0.130 m, mean 0.043 to 0.053 m).

| section | rejection at 56.6 | at 56.73 | change | static failures | marginal transient |
|---|---|---|---|---|---|
| KP 57.4 | 0.0650 % (65) | 0.0630 % (63) | -0.0020 pp | 6 258 both | 0 both |
| KP 58.8 | 5.6730 % (5 673) | 5.5120 % (5 512) | -0.1610 pp | 57 634 both | 0 both |
| KP 60.0 | 3.3630 % (3 363) | 3.2440 % (3 244) | -0.1190 pp | 73 315 both | 0 both |
| KP 62.0 | 0.0000 % (0) | 0.0000 % (0) | 0.0000 pp | 0 both | 0 both |

The 56.6 column reproduces the published per-stratum figures exactly (0.065 /
5.673 / 3.363 / 0.000). **The static rejection column is exactly unchanged at
every section, the transient column moves by at most 0.161 percentage points,
and the marginal transient-not-static count stays exactly 0 in all sixteen
cells.** No conclusion moves.

**The rating-anchored sensitivity (`anchor='rating'`)** moves much more, because
there the gauge rating sets the peak outright:

| section | peak at 56.6 | at 56.73 | change | rejection at 56.6 | at 56.73 |
|---|---|---|---|---|---|
| KP 57.4 | 39.2302 | 39.0208 | -0.2095 m | 0.0000 % | 0.0000 % |
| KP 58.8 | 40.9916 | 40.7817 | -0.2099 m | 10.8140 % | 6.0820 % |
| KP 60.0 | 41.8174 | 41.6520 | -0.1653 m | 0.3370 % | 0.1020 % |
| KP 62.0 | 46.8865 | 46.6433 | -0.2431 m | 0.0470 % | 0.0090 % |

The 56.6 column reproduces the published anchor-construction bracket exactly
(0.00 / 10.81 / 0.34 / 0.05). **At the corrected node it is 0.00 / 6.08 / 0.10 /
0.01 per cent.** The bracket stays one-sided in the same direction and narrows.

### 7.3 Regenerated, 2026-09-14

**Superseding the 2026-09-13 text of this section, which recorded the artifacts
as deliberately not regenerated.** On the author's instruction the pipeline was
re-run at the corrected node the next day, on the ADR-0047 principle that
governs this repository: *adopt where wrong, hold where merely old.* KP 56.6 is
wrong rather than old — ADR-0035 decision 2 exists so that the inverse-then-
forward composition "reproduces the observed series exactly at the gauge", and
inverting an Obihiro stage series through a different station's coefficients
does not do that. The engine's published source is what a reader regenerates
from, so leaving the default at a node the artifacts no longer matched would
have made the thesis unreproducible from its own engine.

Re-run through `scripts/production_campaign.py --stage phase2_baseline
phase2_anchor_rating phase2_no_initiation phase3 --force`, plus
`scripts/thesis_figure_gaps.py all`, `scripts/ztoe_sensitivity_study.py` and
`scripts/annualisation_uncertainty_study.py`. **Every gate passed**: `--verify`
exact (zero flag mismatches) in every stratum, every posterior replaying the
current Phase 1 hash, marginal transient rejection exactly 0 in all eight
strata, and the Phase 3 row set unchanged in shape.

What moved, measured rather than predicted:

* **Phase 2 baseline**: the three matrix transient rejections in §7.2 above,
  and nothing else. The static column is exactly invariant at all eight strata;
  all four bulk strata are unchanged.
* **Phase 2 `anchor='rating'`**: 0.00 / 10.81 / 0.34 / 0.05 to
  **0.00 / 6.08 / 0.10 / 0.01** per cent.
* **Phase 2 `no_breach_no_initiation`: exactly unchanged** (66.389 / 99.568 /
  99.304 / 39.552 per cent). That criterion is dominated by the uplift-and-heave
  latch, which the gauge does not reach.
* **Peak-only over-rejection**: the numerators are read at the *surveyed trace*
  peak, which the correction leaves untouched, so only the denominators move.
  The factors go 2.75 to **2.83** (KP 58.8) and 3.90 to **4.04** (KP 60.0), and
  the alternate-member factors 1.45 / 1.57 to **1.49 / 1.63**.
* **The ±0.3 m exit-datum band at KP 58.8**: 1.68 to 12.99 per cent becomes
  **1.63 to 12.73** per cent.
* **Phase 3**: 30 of 2280 rows move, all posterior-side at the four BEP
  sections, the largest by 0.38 per cent. Five of the eight rows of the thesis's
  annual table change by one unit in the third significant figure; KP 62.0 is
  untouched in every column, because its Phase 2 rejection is 0.00 per cent and
  its posterior therefore *is* its prior.

**No conclusion changes anywhere.** One qualitative statement did: the
anchor-rating effect was described as "roughly twice as high at KP 58.8 and ten
times lower at KP 60.0" and is now a tenth higher and about thirty times lower.
One sentence was deleted rather than restated: Chapter 6 had flagged that the
KP 58.8 peak-only factor "coincides numerically" with that section's
design-level static-to-transient ratio and called the agreement accidental. At
2.83 against 2.75 the coincidence no longer exists.

One derived fact also moved and has been corrected in place: the 2016 Obihiro
record's low-flow excursion below the flood-rating datum is **0.95 m over 371 of
744 hourly samples** at KP 56.73, against 0.82 m over 354 samples at KP 56.6,
the difference being the 0.13 m higher datum term. Both are far inside the 2.0 m
wrong-datum guard.

---

## 8. Scope not covered

- ~~The bulk d70 reading was not run.~~ **Closed 2026-09-14**: it is §9.
- ~~The Phase 3 propagation is prior-side only.~~ **Closed 2026-09-14**: the
  posterior side is measured in §6.2, and it is the side the published headline
  lives on. The arms reject 0.00 per cent under the 2016 record, so the two
  sides agree bit-for-bit on every arm.
- **Open on the thesis side, 2026-09-15.** The declined credit is carried in the
  Chapter 6 piping-conditions register, the Chapter 7 system-conditions register
  and its dominance section, the Chapter 8 limitations register, the Chapter 9
  RQ3 answer and answers register, and Appendix B. It is **not** named in the
  Summary. Adding it there needs a re-wording of author-edited Summary prose,
  which `msc-thesis/CLAUDE.md` reserves to the author, and takes the Summary from
  two pages to three: the last Summary page ends flush, and a 191-character
  insertion produced exactly two lines of overflow at an isolated build. The
  sentence is drafted and left for the author in the 2026-09-14/15 project-log
  entry. Until it is placed, §6.1's rule ("the dominance claim must not be quoted
  without it") is satisfied by the main body and not by the abstract.

---

## 9. The bulk d70 reading

**Added 2026-09-14**, closing §8's stated omission. Twelve further full-N
sweeps, `python scripts/foreland_credit_bracket_study.py --reading bulk`;
evidence `docs/decisions/adr0052-foreland-credit-companion-bulk.json`. **All
four gates passed bit-identical** against the persisted bulk production sweeps.

`kappa` is identical to the matrix reading at every section (3.481 / 3.734 /
3.099 / 1.683), which is expected and worth stating: the credit is
`phi * lambda_out_eff`, and `lambda_out_eff` depends on `k_aq`, `D_aq` and the
foreshore geometry, not on `d_70`. The two readings differ only in where the
baseline curves sit, not in how far the credit moves them.

### 9.1 Design level

Failing realizations of 1e5 at each section's design HWL grid point:

| section | baseline static / transient | half credit | full credit |
|---|---|---|---|
| KP 57.4 | 0 / 0 | 0 / 0 | 0 / 0 |
| KP 58.8 | 1 / 0 | 0 / 0 | 0 / 0 |
| KP 60.0 | 9 264 / 1 054 | 0 / 0 | 0 / 0 |
| KP 62.0 | 0 / 0 | 0 / 0 | 0 / 0 |

The matrix conclusion carries over: under either credit the design level holds
**0 failing realizations of 1e5 on both branches at all four sections**. Under
bulk it is a weaker statement, because three of the four baselines are already
at or near zero — only KP 60.0 has a design-level population to remove.

### 9.2 Cancellation

`rho > 1` at **every level where it resolves: 18 of 18**, range 1.13 to 12.25.
So the direction is the same as under matrix and P3 holds again.

**P2 fails under bulk, and the reason is resolution rather than physics.** Of
21 evaluated levels only 18 resolve; at three levels (KP 62.0, half credit) the
95 % interval covers unity. That does **not** demonstrate cancellation at those
levels — it means the bulk baseline carries too few failing realizations there
for the test to exclude it either way. Stated the other way round: under bulk
the bracket is measured over a much smaller resolvable window (18 levels
against the matrix reading's 101), because the bulk curves sit far lower.

P1, P3 and P5 hold as under matrix; P4 fails again, and more emphatically --
the observed order is KP 60.0 > KP 62.0 > KP 57.4 = KP 58.8 (the last two
having no resolvable level at all), against a `kappa` order of KP 58.8 >
KP 57.4 > KP 60.0 > KP 62.0. This is the second independent confirmation that
the displacement of the ratio is set by where the baseline curves sit, not by
the size of the input's own perturbation.

### 9.3 Stage displacement

Under bulk the sustained-peak bound is pushed so far that the credited curve
often leaves even the extended scan range: the median crossing is undefined
under full credit at KP 57.4, KP 58.8 and KP 62.0, and under half credit at
KP 58.8. Where both crossings exist, the full-credit shift at the 1e-3 anchor
is **+8.59 m** (KP 57.4), **+6.06 m** (KP 60.0) and **+5.25 m** (KP 62.0),
against the matrix reading's +3.76, +3.12 and +1.60 m. The credit is worth
*more* stage under bulk, not less, because the bulk curves are flatter in the
band the bound crosses.

**These are displacements of an indicator, never attainable stages**, and under
bulk several of them sit above the top of the scan, which is itself well above
any attainable level.
