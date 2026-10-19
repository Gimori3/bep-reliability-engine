# ADR-0059: KP 57.4's aquifer thickness is corrected from 7 m to 12 m

Date: 2026-10-17

## Status
Accepted (owner decision, thesis campaign session 5b, 2026-10-17). Corrects one
production prior mean, `D_aq` at KP 57.4 (both d70 readings); CoV, family and every
other section unchanged. Resolves the 2026-10-16 "under review" marker in
`docs/tokachi_bep_inputs_provenance.md` section 4 (KP 57.40). Supersedes, at KP 57.4
only, every result computed on the earlier 7 m (see Consequences).

---

## Context

`D_aq_m` is defined in the input table and its provenance (section 2) as the combined
A_g + N_s gravel thickness to the K_1p (volcanic-ash) base, and the values 7 / 8 / 9 /
10 m at KP 57.4 / 58.8 / 60.0 / 62.0 had stood unchanged since the table's first commit
(`4c5647b`, 2026-06-26), taken from the original thesis stratigraphy table without a
recorded reading rule. That table's own note for KP 57.4 gives "base about EL 23",
which against an aquifer top near EL 37 m implies about 14 m, not 7.

D_aq enters the model in four places: the Sellmeijer geometry factor F_g, hence the
single-source H_c of both branches; the critical pipe length l_c = (L/2) tanh(2 D/L);
the leakage lengths lambda_in and lambda_out, hence r_e and the uplift/heave gate; and
the inactive tau_aq diagnostic. It does not enter the M7 growth rate.

An independent re-reading of OYO (1999), recorded with method, readings and precision in
`adr0059-kp57-aquifer-thickness.json`, established:

1. **Orientation.** Every geological section, 様式-3 panel and 様式-5 model draws the
   river on the left; B-2, B-4, B-6 and B-9 are the landside-toe borings.
2. **N_s is aquifer in OYO's own analysis.** Each 様式-5 model gives N_s the A_g
   conductivity (3.0E-01, 2.0E-01, 1.0E-01 cm/s at KP 57.4, 58.8, 60.0) or more
   (3.0E-01 against 1.0E-01 at KP 62.0), over volcanic ash two to five orders less
   permeable. The definition is right.
3. **KP 57.4's 7 m is the A_g alone.** A_g + N_s measures 10.3 m at the riverside-toe
   boring B-1, 12.5 m under the crest and 13.35 m at the landside-toe boring B-2
   (report Fig. 4-1-1, 1:200, read to +/-0.3 m; the 様式-5 model gives 10.0 / 11.5 /
   14.1 m; the report's longitudinal profile about 10.4 m along the levee). The A_g
   alone is 7.4 m at B-1. 7 m lies 3.3 to 6.35 m below the combined thickness at every
   position.
4. **The other three rows follow the definition** within the sources' resolution: each
   adopted value lies within 0.4 to 1.25 m of its own section's combined thickness at
   every position (KP 58.8: 8.45 to 10.5 m against 8; KP 60.0: 7.8 to 8.5 against 9;
   KP 62.0: 8.8 to 11.6 against 10), i.e. within reading precision plus the integer
   rounding all rows use. They do not reveal a single position rule.
5. **Independent corroboration.** Kunijiban KP1.8R-1, about 0.9 km downstream of
   KP 57.4, logs 11.7 m of aquifer over tuff; the regional base trend interpolates to
   EL 23.9 m at KP 57.4, where OYO's K_1p top lies at 23.75 to 26.6 m. A 7 m aquifer
   would put the base near EL 30 m, above the base at KP 58.8.
6. **No printed boring log exists in the sources** (様式-4 is the soil-test summary;
   the report's end matter has no 柱状図), so the value rests on the drawings.

Measured before the decision (same seed, D_aq mean only, baseline bit-identical to
production): the transient P_f at 40.00 m is 1.9 to 2.8 times the 7 m value across the
candidates 10.3, 12.0 and 13.3 m; between 12 and 13.3 m the time-dependence factor moves
by about 1 per cent and absolute probabilities by 13 to 23 per cent.

## Decision

1. **KP 57.4 `D_aq_m` = 12 m** (both d70 readings), the mean of the combined thickness
   over the seepage path (riverside toe 10.3, crest 12.5, landside toe 13.35 m: 12.05 m;
   the 様式-5 model 11.9 m), rounded to an integer like the other rows. Owner's choice
   between this and the landside-toe 13 m, the evidence not fixing a position rule.
2. **CoV stays 0.10.** Around 12 m its 95 per cent band (9.8 to 14.4 m) spans the
   riverside-to-landside range of the section.
3. **KP 58.8, 60.0 and 62.0 are unchanged.**
4. **Every KP 57.4 result is recomputed** through its own driver on the corrected
   configs: the two production sweeps, their 2016 posteriors (baseline, rating anchor,
   no-initiation criterion), the Stage 6.6 ladder, the ADR-0040 N = 1e5 and N = 1e6
   ladders, the Phase 3 composition, every companion arm sweep with a KP 57.4 arm, and
   every study record the thesis reads. Superseded production files are preserved in
   `results/superseded_kp57daq_20261017T135158/`.

## Alternatives Considered

### 13 m, the landside-toe boring
Where D_bl is read and the exit sits. Not chosen: D_aq enters F_g and l_c, which describe
the aquifer under the levee, and the other rows do not show a landside rule (KP 62.0's
10 m is nearer its section mean than its landside 8.8 m). Between 12 and 13 m the
time-dependence factor differs by about 1 per cent.

### Keep 7 m and describe it as the A_g alone
Would make the definition false at one section only, and OYO's own model treats N_s as
aquifer. Declined.

### Re-read all four sections with one positional rule
Would move the other three rows by up to 1.3 m to correct a scatter that already lies
within reading precision and rounding. Not indicated by the evidence; not taken.

## Rationale
The correction makes the KP 57.4 input satisfy the definition every document states, on
the evidence of three independent OYO drawings and an independent boring, and leaves the
rows that already satisfy it untouched.

## Consequences

**Configs and pins.** Config hashes of `tokachi_kp57.4_historical_{matrix,bulk}` change
(d737929b2cc7 -> 638a49c93ec3, a06bf4aaadb5 -> 16e269975937); the other six equal their
persisted sweeps. `tests/test_configs.py` pins D_aq absolutely (`_AQUIFER_THICKNESS_M`).

**Re-run (2026-10-17/18), each through its own driver and gates.** Production sweeps
(both readings; gross containment 0 violations; both branches `fitted_lognormal`), Phase 2
(baseline, rating anchor, no-initiation; zero flag mismatches), Stage 6.6 (drift guard
bit-identical at 23 levels, flips 0 at N = 1e5), the ADR-0040 N = 1e5 and N = 1e6 ladders
(twice, identical) and stages C, D (both gates bit-identical; the m_p control now passes at
all three anchors) and F2, Phase 3, every companion arm with a KP 57.4 arm (m_p, z_toe,
prior means and their posterior replays, critical length, foreland credit both readings
and its posteriors and annualisations, canonical shape, equal head at N = 1e5 and 1e6,
uniformity, gravel, seepage length, DEM arms and ratio, open entry, drained bracket and
scope, composition seam, segment table) and every study record the thesis reads
(time-dependence factor, criterion consequence, survival information, initiation evidence,
why-no-piping, physical-model qualifications, epistemic synthesis, climate attribution,
annualisation uncertainty, results annotations, first breach, timestep stress, breakthrough
timing, hydrograph uncertainty, time effect in proportion, RQ1 re-expression, metric
decomposition). Superseded production and study artifacts: `results/superseded_kp57daq_20261017T135158/`.
The two hand-placed Stage 6.6 KP 57.4 copies were transcribed from the live artifacts.
`docs/rq1_beta_reexpression_2026-08-28.md` is the generated brief of
`scripts/rq1_beta_analysis.py`; its tables were regenerated in place, as ADR-0054 did on
2026-09-25 (its 'Tables of record' line now reads 2026-10-18; the 2026-09-25 tables stay
in the history at 209ef9c).

**Code changes forced by the corrected numbers** (each a pinned gate re-read, none a
relaxed rule): ADR-0040's G-A2 documented barrier-jump class at KP 57.4 now names
`c4b_not_c3b` and `c4a_not_c3a`, each share measured against the class's own transient
branch (one row each in 1e6: 40.00 m, 1 of 43,280; 39.75 m on the alpha = -1/2 branch,
1 of 155,380; none at a quoted anchor); the equal-head study's pinned N = 1e6 seed-recipe
count at 39.21 m is 1170 (was 302); `conductivity_posterior_replay.py` exempts the
file-handling flag `overwrite` from its settings-drift gate, as
`conductivity_annualisation_study.py` already did, because the KP 57.4 production
posteriors were regenerated in place; `first_breach_alternatives_study.py` read its
uniformity arms from a hard-coded pre-campaign folder and now reads
`results/time_dependence_factor/u_arms`. Tests pinned to evidence values were updated
with dated notes.

**Results.** KP 57.4 becomes more vulnerable on both branches (a thicker aquifer lowers
H_c through F_g and lengthens l_c). The design level stays unresolved (17 same-head
against 5 transient failures in 1e6; dbeta between 0 and 0.62); the resolved anchor at
39.50 m gives F_td 3.12 [2.94, 3.32] and dbeta 0.345 [0.328, 0.364] on 2,223 / 712
failures (was 3.44 and 0.336 on 561 / 163). The 2016 update rejects 76 matrix
realizations (was 16); LR 1.01; joint LR comonotone 1.34, independent 1.43, Frechet
bound 1.47. Annual system P_f 8.53e-4 historical and 1.025e-2 under +4 K (was 4.98e-4 and
7.59e-3); climate ratio 12.0. Qualitative consequences: the static criterion no longer
reorders the sections annually; under the bulk reading piping now leads KP 57.4 under
warming (overflow leads 4 of 8 bulk cells, was 5); KP 57.4 rises to third of 114 nodes
historically. All values: the dated addenda of `docs/phase2_report.md`,
`docs/phase3_report.md` and `docs/stage6_6_report.md`, and the regenerated records.

**Invariants checked.** Gross-head containment holds (0 violations, both readings);
Euler barrier jumps at 225 s are zero at N = 1e5 and two rows in 1e6, as above; the
timestep stress test finds no flip and no threshold shift from 225 s down at KP 57.4, but
the literal 1 % terminal-l_e criterion at KP 57.4 now needs Dt <= 56.25 s (ADR-0039's
rider read 112.5 s; it binds only consumers of l_e magnitude, not failure flags); the time
contract code path is unchanged; no anchor quoted below 30 failures.

**Not re-run; superseded at KP 57.4 by this ADR.** Dated or hand-made records keep their
KP 57.4 numbers as records of their date: `adr0053-*` evidence,
`annualisation-hazard-sampling-uncertainty-pooled-draw-2026-09-14.json`,
`annualisation-pattern-stratification-comparison.json`, `assumptions-overview-study.json`,
`bimodal-foundation-d70-study.json`, `examiner-residues-closed-2026-09-04.json`,
`adr0044-event-closure-bound.json`, and `phase2-survival-update-per-stratum.json`
(a slice of `results/production_campaign_manifest.json`, which records the pre-ADR-0059
campaign; the KP 57.4 production SHA-256 values in that manifest no longer match the live
files, whose predecessors are in the superseded tree).

**Pre-existing behaviour found, not changed.** `critical_length_bracket_study.py` and
`foreland_credit_bracket_study.py` seed bootstrap intervals with Python's salted
`hash()`, so interval ends (not points or counts) differ between runs; the first-breach
study and the reach-interval bootstrap share one random stream across sections, so a
KP 57.4 change moves other sections within Monte Carlo noise (at most 0.0005 in a share).

The provenance section 1 boring header is corrected by a dated pointer (its order is
riverside / crest / landside toe).

## References
- OYO Corporation (1999), report and 様式-3/4/5 sheets (see the evidence JSON).
- `docs/tokachi_bep_inputs_provenance.md` sections 2, 4 (KP 57.40), 6.4, 8.2.
- Sellmeijer (2011) for F_g; Pol et al. (2024) for l_c.
