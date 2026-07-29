# Study note: the stochastic seepage length L — marginal, spatial correlation, and the Phase 2 ceiling

Date: 2026-07-19. Status: **Accepted** — the §5 recommendations were adopted by the author
(2026-07-19); **no production default changed, no new binding ADR**. The adopted model and
its reporting/consistency requirements are locked into `docs/architecture.md` (§7 stochastic
vector, §12 open-decisions, §13 single-decisions table) and the project-notes.md as-built state.
Companion to **ADR-0033** (GSA — L is the top total-effect input) and **ADR-0037**
(length effect / λ_ac). Parent decisions unchanged.

Records (gitignored, regenerable): `results/sensitivity/seepage_length/{marginal_sensitivity,system_correlation,phase2_ceiling}.json`.
Drivers: `scripts/seepage_length_study.py` (marginal|system|ceiling|all), `scripts/seepage_length_figures.py`.
Figures: `docs/figures/seepage_length_marginal.png`, `…_marginal_ratio.png`, `…_system_and_ceiling.png`.
New helpers (pure, unwired, opt-in): `system_integration.composition.length_effect_effective_count` + `reach_union`
(`tests/test_system_integration.py`).

---

## 0. Why this study

The ADR-0033 GSA established that the stochastic seepage length **L is the top- or
co-top-ranked total-effect input for every QoI at every conditioning level** — it acts
through H_c, the rate denominator, r_e, *and* the failure criterion Z = L − l_e itself —
and that because Phase 2 Accept–Reject filters only the 7-column θ matrix, survival
evidence cannot reduce it (ADR-0033 §2, §5: "the L finding in particular motivates
scrutiny of the 0.20"). Yet L is modelled as `Lognormal(mean = geometry.L, CoV 0.20)`
(0.15 at KP60.0), sampled independently of θ and independently per cross-section, and
ADR-0037's length-effect correction is the identity (n_eff = 1) at the primary
λ_ac = 250 m. This note asks whether the *marginal*, the *spatial correlation*, and the
*Phase 2 ceiling* those choices imply are defensible, and quantifies each. The engine
driver is validated **bit-identical** to the persisted production sweeps
(`scripts/seepage_length_study.py` reproduces `results/tokachi_kp58.8_historical_matrix.h5`
P_f to max |ΔP_f| = 0.0 at N = 1e5, numpy backend).

---

## 1. The marginal — is CoV 0.20 lognormal defensible?

### 1.1 Where 0.20 comes from (traced)

The value is **engineering judgement, not a fit**, and traces cleanly:

- **Thesis §3, `tab:seepage_length_prior`** (`3. Study Area…tex` L399–402): per-section
  lognormal, CoV **0.15 at KP60.0** (best-constrained), **0.20 at KP57.4/58.8/62.0**,
  "representing the combined uncertainty in the **base-width reading** and the
  possibility that the **effective exit lies a short distance beyond the toe**."
- **The L-determination memo** (via `docs/tokachi_bep_inputs_provenance.md` §3.1): the L
  means are "explicit engineering-judgement estimates, not surveyed values of L"; the
  residual uncertainty "is dominated **not by reading error in the well-dimensioned
  levee footprint** but by the **unverified position of the landside blanket
  boundary**"; the memo "recommends a modest per-section lognormal (CoV 0.15 at KP 60.0,
  0.20 elsewhere) and a **one-sided upward sensitivity case**."
- The **lognormal shape** is the project-wide distributional convention (thesis §3
  "Distributional Family and Lognormal Transform"; Pol SIE 2024), positive-support and
  moment-matched exactly like the θ marginals.

**Flag:** there is **no external fitted CoV(L)** to compare against. Van Beek (2015),
Sellmeijer (2011) and WBI/Schweckendiek treat the *seepage length itself* as a
geometric quantity — Dutch semi-probabilistic piping practice generally takes L
deterministic from geometry and carries the schematisation/exit uncertainty elsewhere
(Schweckendiek 2014 makes the *blanket thickness* the one random field, and the *exit
point* uncertain, not L). Making L stochastic at all is therefore already more
uncertainty-aware than standard practice; the specific magnitude 0.20/0.15 is a
site-specific judgement and cannot be traced to a literature number — stated here rather
than papered over.

### 1.2 What the geometry itself implies

Interpreting the memo's own base-width *ranges* as spread:

| Section | Range → adopt | implied CoV (min–max=2σ / 90% / 95%) |
|---|---|---|
| KP58.8 | [31, 40] → 35 | 0.129 / 0.078 / 0.066 |
| KP62.0 | [40, 55] → 47 | 0.160 / 0.097 / 0.081 |
| KP57.4 | dimension chain 32.92 (point) | — |
| KP60.0 | footprint 34.8 (point) | — (CoV 0.15 assigned) |

**[Note added 2026-07-29 (ADR-0047).** The KP 62.0 row's adopted value is no longer
47 m: the DEM re-survey showed the 47 m credited a landside berm that never existed,
and the CSV now carries **40 m** — the bottom of that very range. The row is left as
written because it records what the memo's ranges imply about *spread*, and the
conclusion below is unaffected: the measured along-levee spread (0.073–0.184) brackets
the 0.08–0.16 derived here, and `seepage_length_cov` stays 0.20 / 0.15 everywhere.]

So **base-width reading scatter alone implies CoV ≈ 0.08–0.16** — *below* the assigned
0.20. The extra padding to 0.20 is the "exit lies a short distance beyond the toe"
epistemic term. The production value is therefore a **defensible, mildly conservative
lumped allowance**, not an inflation.

The genuinely dominant uncertainty the memo names — the **landside boundary position**
and the **remediation offset** (berm-only current path "+10 to +30 m" beyond the 1998
toe value) — is **one-sided upward** and much larger than any symmetric spread. A
symmetric lognormal does not represent it; because a *longer* L raises H_c and lowers
P_f, omitting the upside is **conservative** (see §1.4).

### 1.3 How far P_f moves (measured, N = 30 000, four sections, numba)

Transient P_f ratio to the production CoV 0.20, holding the LHS design fixed so only the
distribution changes (`marginal_sensitivity.json`; figure `…_marginal.png`,
`…_marginal_ratio.png`):

| CoV(L) | transient shoulder (P_f≈0.05) | transient design (P_f≈0.30) | static shoulder |
|---|---|---|---|
| deterministic | **0.18–0.32×** | 0.69–0.81× | 0.63–0.95× |
| 0.10 | 0.33–0.49× | 0.78–0.86× | 0.75–0.96× |
| 0.15 | 0.58–0.69× | 0.88–0.92× | 0.87–0.98× |
| **0.20 (prod.)** | **1.00×** | **1.00×** | **1.00×** |
| 0.30 | 1.73–2.23× | 1.15–1.23× | 1.04–1.28× |
| 0.40 | 2.57–3.79× | 1.28–1.43× | 1.08–1.49× |

**The transient shoulder is the CoV-sensitive regime** — it swings **≈ 3–4× across the
defensible CoV 0.10→0.40 range** (and ≈ 2.5–3× just over 0.15→0.30), because the heavy
short-L tail governs early failures (fm7-adjacent: short L pairs with a fast-rate corner).
The **design-level P_f is robust** (≤ 1.4× even at CoV 0.40). Deterministic L badly
under-predicts the shoulder (0.18–0.32×), so **making L stochastic at all is
first-order** — the shoulder is where the length effect and the CoV live.

### 1.4 Shape

At fixed moments (CoV 0.20), a **normal** marginal raises the transient shoulder P_f only
**1.11–1.26×** and leaves the design level unchanged (0.98–0.99×) — the shape is
**second-order** relative to the CoV magnitude. The **one-sided upward** case (mean +15%,
the memo's berm/longer-path direction) **cuts** transient P_f to **0.33–0.40× (shoulder)
/ 0.52–0.57× (design)** — confirming the symmetric lognormal is conservative and that the
memo's one-sided sensitivity case (already planned in the thesis at the live sections) is
the correct complement, not the base model.

---

## 2. Spatial correlation — the length effect restated at the system level

### 2.1 The consistency question

ADR-0037 fixes the *within*-segment weakest-link count `n_eff = max(1, L_seg/λ_ac)` and
**clamps it at 1**, so at λ_ac = 250 m a 200 m segment is the identity ("no
amplification"). The *between*-segment treatment in Phase 3 is the **same
autocorrelation story one scale up**, and it was never made explicit. For a reach of
length R populated at 200 m spacing, the true number of *effectively independent*
cross-sections is `n_independent = R/λ_ac`, while a segment-independent series union
assumes `n_segments = R/200`. Treating segments as independent therefore mis-counts the
independent failure opportunities by exactly:

> **independence over-count = λ_ac / segment_spacing** — *independent of R*:
> **1.25 at λ_ac = 250 m**, 0.50 at 100 m, 0.20 at 40 m.

A ratio > 1 (primary) means segment-independence is **conservative** (over-states the
reach union); < 1 (the k-governed brackets) means it **under-counts** sub-segment weak
spots and *under-states* the reach union. This is the exact reach-scale companion of
`fragility.upscale_length_effect`, and it shows the ADR-0037 clamp discards precisely the
information (λ_ac > L_seg ⇒ adjacent segments correlated) that reappears one scale up.

### 2.2 The production deliverable is insensitive to it — by construction

Under the production `bep_source_policy = 'exact'` (ADR-0038), BEP lives at **only the
four OYO sections, 1.2–2.0 km apart — far beyond any λ_ac**. Their independent L draws are
therefore *physically correct*, and the reach-union bounds are tight
(`system_correlation.json`, from the committed RQ4 annual BEP at the four nodes):

| scenario | reach union (independent) | reach union (comonotone) | ratio |
|---|---|---|---|
| historical / posterior | 1.02e-2 | 7.34e-3 | **1.39** |
| +4K / posterior | 6.71e-2 | 4.05e-2 | **1.66** |

So the production BEP system numbers are **insensitive** to the inter-segment L
correlation (worst case ~1.7×, and independence is the correct choice anyway). Within a
consequence section, Uemura's Eq. 14 already uses the **max** (`max_within_section_rated`
— full dependence), consistent with λ_ac ≫ within-section spacing. **The current
treatment is thus internally consistent at both extremes** (full dependence within a
section; independence between 1.2–2.0 km OYO sections).

### 2.3 Where the tension is latent

The inconsistency would bite only if a **densely-populated reach** were composed under
naive segment-independence — the `'nearest'` policy, or future data (the OYO 土層縦断図)
that populates the borehole-free reaches at 200 m. There, with ~34 segments over a 6.8 km
Tokachi reach, independence assumes 34 independent units where λ_ac = 250 m implies only
27 (ratio 1.25, conservative), but λ_ac = 40 m would imply 170 (independence
under-states 5×). This is the length effect exactly, and it is why populating those
reaches must go through the reach-scale correction, not a naive product. The two new
`composition` helpers (`length_effect_effective_count`, `reach_union` with
`correlation ∈ {independent, comonotone}`) provide the bound; they are pure, default to
independence (= current behaviour), and are **not wired into the campaign**.

---

## 3. The Phase 2 ceiling — how much residual uncertainty is L-borne

Read directly off the **production N = 1e5 posteriors** (`results/phase2/*_matrix_posterior.h5`;
`phase2_ceiling.json`), no re-run:

| section | 2016 rejection | L mean Δ | L CoV Δ | k_aq mean Δ | C_e mean Δ |
|---|---|---|---|---|---|
| KP58.8 | 5.67% | **+1.37%** | **−3.63%** | −4.15% | −4.07% |
| KP60.0 | 3.36% | **+0.54%** | **−1.66%** | −3.00% | −3.71% |

**The 2016 survival barely moves L** (mean +0.5–1.4%, CoV −1.7–3.6%: it trims a few
short-L rows, nudging L *up* toward the safer/longer end), while it shifts the soil
properties it *can* filter (k_aq, C_e down ~4%). L is not in the filtered θ vector; it is
regenerated per row and carried, so its marginal is a near-invariant of the update.

A first-order share (correlation ratio η² of the transient failure indicator at a
future shoulder level, **validated ≈ the ADR-0033 Saltelli S_i**: η²_L = 0.252 vs GSA
S_L ≈ 0.26 at KP58.8; η²_kaq = 0.210 vs 0.21) stays L-dominant prior *and* posterior.
The relevant ceiling number is the **total-effect** share the GSA already measured:
**ST_L ≈ 0.49–0.78 of the transient failure-indicator variance is L-borne**, and since
the posterior L marginal ≈ the prior, that share is **essentially irreducible by survival
evidence** — a floor that no amount of additional survival events (which only filter θ
rows) can lower.

**Implication for the thesis's Bayesian-updating claims.** The 2016 survival genuinely
tightens the *soil-property* corner — the k_aq/C_e ~4% shift, along the joint fm7
direction the GSA flagged — but it **cannot tighten the single largest contributor to
BEP fragility uncertainty**, the geometric L. The updating claim must be scoped
accordingly: the posterior narrows θ, not the fragility-dominant geometry, so the
head-line prior→posterior fragility shift is bounded from below in variance by the
L-borne floor. This *reinforces* the existing fm7 caveat (marginal posterior std-devs
understate the information gained) with a second, structural one: an entire ≥ ½ of the
fragility variance sits outside the filter's reach.

---

## 4. New findings (not previously known)

1. **The transient shoulder P_f is 3–4× sensitive to CoV(L)** over the defensible 0.10–0.40
   band, while the **design-level P_f is robust (≤ 1.4×)**. The shoulder — not the transition
   — is where the L marginal is the dominant epistemic knob. (New: the GSA ranked L but did
   not quantify the fragility's *elasticity* to the CoV choice.)
2. **Base-width scatter alone implies CoV ≈ 0.08–0.16**, below the assigned 0.20; the
   production value is a padded, mildly-conservative lumped allowance, and its **dominant
   physical uncertainty is one-sided upward** (boundary/remediation) — a direction the
   symmetric lognormal omits and whose omission *lowers* P_f (mean +15% → P_f ×0.33–0.57).
   So the symmetric CoV 0.20 is conservative on the mean, not aggressive.
3. **The length effect and the cross-segment independence are the same autocorrelation
   story at two scales**, and the ADR-0037 n_eff = 1 clamp hides a **1.25× inter-segment
   over-count** at λ_ac = 250 m. The production `exact` 4-section deliverable is
   insensitive to it (bounds within ~1.4–1.7×) and internally consistent; the tension is
   **latent**, biting only a densely-populated reach.
4. **L is a near-invariant of the 2016 survival update** (mean +0.5–1.4%, CoV −1.7–3.6%),
   quantifying the ADR-0033 "hard ceiling": **≈ ½–¾ of the transient fragility variance is
   L-borne and irreducible** by any θ-only survival filter — a structural bound on the
   Bayesian-updating claim, distinct from and additional to the fm7 marginal-understatement
   caveat.
5. A first-order **correlation-ratio η² recovers the GSA Saltelli S_i** on an arbitrary
   sample (η²_L 0.25 vs S_L 0.26), a cheap reusable posterior-sample sensitivity probe.

## 5. Recommendation for the production L model

**Keep the production model as-is** — per-section lognormal, CoV 0.15 (KP60.0) / 0.20
(elsewhere), sampled independently of θ and per section. It is traceable, defensible, and
mildly conservative; **no default changes, no new binding ADR.** Specifically:

1. **Marginal:** retain CoV 0.20/0.15 lognormal. **Report the shoulder-P_f CoV(L) band
   explicitly** as the dominant epistemic knob at the shoulder (it is a bigger lever there
   than any single θ marginal), and keep the memo's **one-sided-upward** case as the
   correct complement — noting the symmetric prior is conservative, not neutral. The
   `config.seepage_length_cov` field already exercises the CoV band; no new knob is needed.
2. **Spatial correlation:** keep L independent per section for the `exact` four-section
   deliverable (correct). **Do not** compose a densely-populated reach under naive
   independence: if the `nearest` policy or the OYO 土層縦断図 ever populates the
   borehole-free reaches, route through the reach-scale length effect
   (`length_effect_effective_count` / `reach_union`) and report the λ_ac bracket, exactly
   as ADR-0037 does within a segment.
3. **Phase 2:** frame the updating result around the L ceiling — survival tightens θ
   (k_aq/C_e ~4%), not the fragility-dominant geometric L; ≈ ½–¾ of the transient
   fragility variance is outside the filter's reach.

**On a new capability / config field.** No config-level opt-in was added: the CoV band is
already reachable via `seepage_length_cov`, and inter-segment correlation is a *system*
post-processing concept, not a per-cross-section input — a gratuitous Config field would
have risked the Phase 2 config-hash gate for no modelling gain. The warranted capability
is the pair of **pure, unwired, default-independent** `system_integration.composition`
helpers, which follow the ADR-0037/0045 spirit (opt-in, default = current behaviour,
bit-identical baseline) without touching the config surface at all.

---

## 6. Reproduction

```
python scripts/seepage_length_study.py all --backend numba   # ~a few minutes
python scripts/seepage_length_figures.py                     # redraws the 3 figures
pytest tests/test_system_integration.py -k "reach_union or effective_count"
```

Cautions for reuse: the marginal ratios are conditional on the ADR-0026 C_e prior, the
two-population coupling and the production geometry (as with the ADR-0033 indices); the
η² probe is first-order only (use the GSA for total effects); the reach bounds assume the
weakest-link/series form the thesis adopts. All numbers regenerate from the committed
configs and the persisted posteriors.
