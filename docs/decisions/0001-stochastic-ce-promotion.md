# ADR-0001: Seven-Dimensional Stochastic Parameter Space with Stochastic C_e

Date: 2026-05-21
Status: Accepted — **C_e prior amended by ADR-0026** (2026-07-07): the prior is
now `Lognormal(mean 0.055, std 0.043)` (Pol's SIE 2024 field value), not the
`(0.014, COV 0.50)` below, and the justification for treating C_e stochastically
is its intrinsic uncertainty (Pol: laminar-vs-turbulent model uncertainty is
nominally Sellmeijer's ~12% model factor, NOT C_e's to absorb). The promotion of
C_e to a random variable stands. See ADR-0026.

## Context
Standard backward erosion piping (BEP) analyses treat the progression erosion coefficient ($C_e$) as a deterministic constant calibrated to small-scale laboratory experiments. However, field observations suggest that prototype-scale piping transitions to turbulent flow regimes (Okamura 2022, 2025), introducing friction that alters raw progression rates relative to small-scale laminar assumptions.

## Decision
We promote $C_e$ from a fixed baseline to a first-class random variable within our sampling loop, extending our parameter sampling space to seven dimensions. We assume a Lognormal distribution ($\mu = 0.014$, $\text{COV} = 0.50$) to capture small-scale calibration variances while giving the engine computational room to adjust this tail.

## Consequences
*   The prior transient fragility curves will reflect greater uncertainty, sitting higher than standard deterministic assumptions.
*   Phase 2 Bayesian filtering against the 2016 typhoon survival record will directly constrain this uncertainty, reducing conservatism via empirical data without relying on unvalidated, complex physical turbulence functions.
