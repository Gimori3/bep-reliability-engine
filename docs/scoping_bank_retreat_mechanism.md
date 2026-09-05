# Scoping note: a migration-capable bank-retreat mechanism for Phase 3

**Date:** 2026-07-28
**Status:** **decided and executed at Tier 1** (2026-07-28). Tier 1 is built and
reported — indicator `system_integration/foreshore_exhaustion.py`, driver
`scripts/foreshore_exhaustion_study.py`, evidence
`docs/decisions/r10-foreshore-exhaustion-screening.json`, companion note
`docs/decisions/r10-foreshore-exhaustion-screening.md`, figure
`docs/figures/r10_foreshore_exhaustion.png`, tests
`tests/test_foreshore_exhaustion.py`. **Tier 2 and Tier 3 are declined by the
the author**; Tier 2 remains available and would need ADR-0047 first.
No ADR was consumed: the indicator adds no mechanism to the Phase 3
composition (structurally pinned by test) and every Phase 3 artifact is
byte-identical after the work.
**Origin:** review item R10, `docs/tokachi_basin_document_review_2026-07-27.md` §10.2
**Decision requested:** whether to build, and at which of the three tiers below —
**answered: Tier 1 yes, Tier 2 no for this timeline, Tier 3 declined in writing**

---

## 1. Why this is the top remaining gap

Phase 3 composes three mechanisms per segment: BEP (engine-derived), overflow
(Uemura P1) and fluvial scour (Uemura P2). Under the ADR-0042 decision 9
dimensionally-corrected conversion, **P2 returns exactly zero at all 114 segments
in both climate scenarios**.

Meanwhile the documentary record for this exact system is:

| Event | Location | Official attributed cause |
|---|---|---|
| 2016-08 | Otofuke KP21.2 L | falling-limb channel migration; bank + embankment erosion |
| 2016-08 | Satsunai KP40.5 L | falling-limb channel migration; bank + embankment erosion |
| 2016-08 | Satsunai KP25.0 L | landside overtopping from a Tottabetsu breach |
| 2011-09 | Otofuke KP18.2 | high-water-bed erosion advancing into the embankment, ~5 m of levee length per hour, no revetment present |

So the mechanism with the strongest empirical claim to having caused levee failure
in this basin contributes **nothing** to the composition, and the mechanism that
dominates the composition (BEP) has **never** been observed to breach here. That
asymmetry is the single largest threat to the RQ3 dominance conclusion, and it is
a modelling gap rather than a data gap.

## 2. Why P2 cannot be repaired by recalibration

Established by reading `system_integration/uemura_models.py` (2026-07-28):

`scour_failure_fraction` **is** structurally a lateral model — accumulated
horizontal erosion versus the levee body width at the prevailing stage. Two
features, not the calibration, make it the wrong process:

1. **Forcing.** Shear derives from a uniform-flow Manning velocity computed from
   *floodplain* inundation depth `d = clip(h − z_fp, 0, z_crest − z_fp)` and the
   water-surface slope. Erosion is therefore keyed to how deeply the high-water
   bed is submerged, not to the near-bank velocity of a channel attacking the
   bank.
2. **Geometry.** `SegmentSurfaceInputs` carries crest elevation, ground
   elevation, floodplain elevation, crest width, levee slope and water-surface
   gradient. There is **no thalweg position, no bend curvature, and no foreshore
   width**. Nothing can record the channel approaching the levee.

Consequence: the model has no representation in which a *receding* flood is more
dangerous than a peak one, yet three of the four documented failures above
occurred on the falling limb. Raising `k` would inflate a process that is still
the wrong one, which is why the as-received script factor should not be
reinstated as a repair.

## 3. The mechanism to represent

The physical chain in the documented failures:

```
channel migration / bar dynamics
  → thalweg approaches the levee line
  → near-bank velocity attacks the bank toe
  → foreshore (high-water bed) width is consumed
  → attack reaches the embankment
  → embankment erodes laterally → breach
```

The state variable the current model lacks is the **remaining foreshore width**,
and the failure condition is its exhaustion. This is not an invention: Japanese
practice on this river manages the mechanism with exactly that variable. The
堤防防御ライン (levee defence line) methodology, introduced in the 2002 河道計画
guidance and applied to the upper Tokachi, defines a **required high-water-bed
width** and triggers intervention when the observed bank encroaches past it
(続十勝川治水史, PDF p. 286). Phase 1 already carries a per-section
`foreshore_width_m` (200 / 325 / 600 / 44 / 0 m) for the BEP foreland credit, so
the variable exists in the repo.

## 4. Three implementation tiers

### Tier 1 — Foreshore-exhaustion screening indicator (~1 day)

Deterministic, per segment, no new stochastic inputs. Take the documented 2011
Otofuke retreat rate as an order-of-magnitude erosion velocity (~5 m of levee
length per hour is a *longitudinal* rate, so it needs converting to a lateral
retreat rate — treat as bounding, not calibrated), integrate over the time the
stage exceeds the foreshore-mobilising threshold, and compare against
`foreshore_width_m`.

- **Output:** a per-segment time-to-exhaustion and a binary screening flag.
- **Value:** immediately shows which segments are *capable* of the mechanism.
  KP 62.0, at 44 m of foreshore, is 14× narrower than KP 60.0 at 600 m; if the
  indicator separates them by orders of magnitude, that alone qualifies the
  dominance ordering usefully.
- **Weakness:** not a probability, so it cannot enter the series composition.
- **Deliverable:** a `scripts/` study plus a companion note. No engine change, no
  ADR needed if it stays a study.

**EXECUTED 2026-07-28** — full results in
`docs/decisions/r10-foreshore-exhaustion-screening.md`. Headlines: 4 of the 114
segments carry a measured B_f (the four confined OYO sections; no width was
interpolated for the other 110). The indicator is reported as the *critical*
lateral retreat rate `v* = B_f / T_mob`, which at the design level reads 0.7
(KP 62.0) / 3.0 (KP 57.4) / 3.9 (KP 58.8) / 9.8 (KP 60.0) m/h, and under the
observed 2016 loading 2.6 / 4.4 / 4.5 / 27 m/h. The KP 62.0-vs-KP 60.0
separation anticipated above is **measured at 10.5× (2016) and 13.6× (design
HWL)** against a 13.6× width contrast, and is asserted in the driver against a
5× floor. KP 62.0 is the only section flagged at the central 1 m/h rate in
either climate. **Every critical rate lies inside the assumed 0.1–10 m/h
bracket, so the verdict flips within the bracket** — the indicator establishes
an exposure *ordering* and a scale, not a screening decision, and is reported
that way.

### Tier 2 — Probabilistic foreshore-exhaustion fragility (~1 week)

Promote Tier 1 to a stage-conditioned fragility curve `P_f,retreat(h)` that can
join the series composition as a fourth mechanism.

- Stochastic inputs: bank-material erodibility (lognormal), the lateral retreat
  rate coefficient, and the foreshore width itself (which is survey-dated and
  has changed since 1998).
- Forcing: near-bank velocity rather than floodplain sheet flow. A defensible
  first cut is a bend-corrected channel velocity, using the documented
  1/200–1/600 channel gradient (PDF p. 392) and the Tokachi Ohashi constriction
  geometry (planned 500 m versus actual 370 m, PDF p. 280).
- **Requires an ADR** (next free number **0047**) because it adds a mechanism to
  the Phase 3 composition. Must be **opt-in and default-OFF** so the existing
  three-mechanism campaign results remain reproducible and bit-identical.
- **Validation target available:** the model must reproduce, at least to order of
  magnitude, that Otofuke KP21.2 and Satsunai KP40.5 fail while the study
  sections do not, under the 2016 loading. That is a genuine falsification test,
  not a fitting exercise — which is what makes this tier worth doing.

### Tier 3 — Morphodynamic coupling (out of scope)

A planform evolution model (bar dynamics, bend migration, sediment supply). This
is a thesis in itself. The basin already has the ingredients — the 1992 movable-bed
hydraulic model experiments on the Satsunai (PDF p. 281), the Chiyoda experimental
channel campaign of 2021–22, the Mishima 1,300 m meander wavelength analysis
(PDF p. 284) — but coupling them is well beyond the remaining scope. **Recommend
explicitly declining this and recording it as further work.**

## 5. Recommendation

**Build Tier 1; propose Tier 2 only if the thesis timeline genuinely allows; decline
Tier 3 in writing.**

Reasoning. Tier 1 is cheap, needs no ADR, adds no configuration surface, cannot
disturb any persisted result, and already discharges the intellectual obligation:
it converts "the represented mechanism set omits the empirically dominant process"
from an admission into a quantified statement about which segments are exposed.
That is enough to make the RQ3 conditioning honest and defensible.

Tier 2 is where the real scientific value sits, because of the falsification test
in §4, but it adds a mechanism to a **closed campaign**. Even default-OFF it
invites the question of why the headline numbers do not include it, and answering
that properly means re-running and re-reporting Phase 3. That is a scope decision,
not a technical one.

**What I need from you:** a yes/no on Tier 1, and a judgement on whether Tier 2
fits the timeline. If Tier 2 is wanted, it needs ADR-0047 drafted first, before
any code.

## 6. Guardrails if this is built

- Default-OFF, bit-identical baseline; `None` dropped from
  `Config.to_metadata()` so the Phase 2 replay hash gate keeps passing.
- The new mechanism is **external-model physics** in the ADR-0042 sense and
  belongs in a quarantined module that imports nothing from the BEP kernels.
- Do not reinstate the as-received scour `k` factor as a proxy for this
  mechanism. The dimensional correction was decided on dimensional grounds
  (ADR-0042 decision 9) and is independent of this gap; conflating the two would
  re-open a settled question for the wrong reason.
- State the retreat-rate provenance honestly. The 2011 figure is a single
  observation from a narrative account, not a calibrated rate, and any curve
  built on it is order-of-magnitude at best.
