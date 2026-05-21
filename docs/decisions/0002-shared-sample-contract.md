# ADR-0002: Shared-Sample Contract via Unified Limit State Evaluator

Date: 2026-05-21
Status: Accepted

## Context
Quantifying the operational bias between static limit states (Sellmeijer 2011) and transient limit states (Pol 2024) requires ensuring that differences are due to time-dependent physics rather than random sampling noise.

## Decision
We mandate a strict shared-sample contract executed via module `M8 (limit_state_evaluator)`. A single function call will consume exactly the same realization vector $\theta_j$ and the same calculated response factor $r_e$ to evaluate both the static and transient safety margins simultaneously.

## Consequences
*   Independent execution tracks for static and transient loops are banned.
*   Statistical variance in our bias metrics ($\Delta Z$) is minimized, isolating the precise impact of transient hydrograph structures.
