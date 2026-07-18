# ADR-0008: Terzaghi Heave Gradient and the Resulting I_er Collapse

Date: 2026-06-12
Status: Accepted

## Context
Pol's initiation gate (SIE 2024 Eq. (7); thesis Eq. (6.6)) conditions pipe progression on an uplift latch and an instantaneous heave check, with the heave limit state built on an **independent** critical heave gradient i_c,h (Lognormal, μ = 0.7, σ = 0.1, based on Schweckendiek et al. 2014; SIE 2024 Table 2). The architecture (§3 steps d–i) instead uses the Terzaghi critical gradient γ'_s/γ_w as the heave threshold, and the 7D stochastic vector (ADR-0001) carries no i_c,h. The spec does not acknowledge that this substitution changes the structure of the gate, which was surfaced during the M5 design review.

Convention note: both limit states are written resistance-minus-load (critical when Z < 0). The printed term order in SIE 2024 Eqs. (8)–(9) / thesis Eqs. (6.7)–(6.8) reads load-minus-resistance, which is inconsistent with the "< 0" tests in the papers' own I_er definition; the resistance-minus-load reading is the only coherent one, matches thesis Eq. (7.14) and the Schweckendiek/TAW convention, and was confirmed against the paper copy on 2026-06-12.

## The algebra
With Δh_blanket(t) = r_e·(h(t) − z_toe) the un-reduced translated blanket overpressure (M4):

```
Z_uplift(t) = (γ'_s · D_bl)/γ_w − Δh_blanket(t)
Z_heave(t)  =  γ'_s/γ_w − Δh_blanket(t)/D_bl  =  Z_uplift(t) / D_bl
```

Setting i_c,h = γ'_s/γ_w makes Z_heave identically Z_uplift scaled by the positive constant 1/D_bl. The two limit states flip sign at the same instant, so heave being active implies uplift is active at that same moment. The uplift latch and the `l_current > 0` clause are then functionally redundant within an event, and the gate

```
I_er(t) = (uplift_ever(t) OR l_current(t) > 0) AND heave_now(t)
```

reduces mathematically to `I_er(t) = heave_now(t)` under this parameterization.

## Decision
Keep the spec's γ'_s/γ_w substitution and document the collapse:

1. **Terzaghi over Schweckendiek.** The classical critical gradient i_c = γ'/γ_w is the physically standard heave criterion and is internally consistent with the uplift check, which is built from the same sampled γ'_s. Pol's i_c,h = 0.7 is an empirical value carrying its own calibration baggage, and adopting it would add an eighth random variable, breaking the 7D vector of ADR-0001.
2. **The full gate structure is retained in M5/M7 as specified** — latch, `l_current > 0` clause, and instantaneous heave check are all implemented even though they currently collapse. They become load-bearing the instant i_c,h is ever decoupled from γ'_s/γ_w, e.g. in a sensitivity run reinstating Pol's Ln(0.7, 0.1).

## Consequences
*   Under the baseline parameterization, I_er(t) ≡ heave_now(t). Diagnostics will show `uplift_occurred` and `heave_occurred` latching at the same timestep; this is correct, not a bug.
*   Pol's hysteresis band is erased: in his formulation, uplift latches at an overpressure of ≈ 0.83·D_bl (γ'/γ_w with base-case weights) while erosion then sustains down to i_c,h·D_bl = 0.7·D_bl. Collapsing the thresholds removes that sustain window, making the engine slightly **less conservative than Pol's base case during the sustain phase of each peak**. The loss is genuinely small for flashy hydrographs, where peaks are short and the sustain window barely opens; it must be acknowledged when comparing against Pol's published reliability results.
*   Pol's uplift model factor m_u (Ln, μ = 1, σ = 0.1) and critical-head model factor m_p (Ln, μ = 1, σ = 0.12) are likewise deliberately not carried: the framework concentrates model-uncertainty calibration into the single stochastic C_e (ADR-0001), which Phase 2 constrains against the 2016 survival record. **[Amended by ADR-0045, 2026-07-18: after ADR-0026 re-justified C_e on intrinsic-uncertainty grounds (model-form uncertainty is m_p's to hold, not C_e's), m_p became available as an opt-in stochastic factor on the single-source H_c — default off, companion runs only. m_u remains not carried.]**
*   The §11 validation assertion "I_er never goes from true to false except via heave inactivation" remains valid (trivially so, since heave is the only active clause).
*   The M5 docstrings must state the collapse and reference this ADR, so the redundant-looking gate code is not "simplified" away later.

## References
- Pol SIE 2024, Eqs. (7)–(10), Table 2
- Pol thesis 2022, Eqs. (6.6)–(6.9), Eq. (7.14)
- Schweckendiek et al. (2014); TAW (1999)
- ADR-0001 (7D vector, stochastic C_e)

## Author confirmation (Pol, 2026-07-07)
Pol confirmed that omitting the flood-fighting clause (t_ff/I_ff, SIE 2024
Eq. (7)) is the better, safer choice: organized flood fighting would be very
difficult or impossible in flashy rivers during typhoons. This confirms the
unconditional-upper-bound erosion indicator (the third clause dropped). No code
change. See `docs/validation/pol-meeting-2026-07-07-dispositions.md`, Answer 8.
