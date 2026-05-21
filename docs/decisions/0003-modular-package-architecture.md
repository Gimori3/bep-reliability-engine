# ADR-0003: Modular Python Package Architecture

Date: 2026-05-21
Status: Accepted

## Context
The BEP reliability engine must support clean Phase 1 fragility analysis, seamless structural imports into Phase 2 Bayesian filtering pipelines, scalable unit testing via pytest, and precise git version tracking.

## Decision
Adopt a flat, modular Python package architecture with thin Jupyter notebook drivers. Core physics implementations reside in importable `.py` modules inside the `bep_phase1` package directory positioned directly at the repository root. Notebooks are restricted to execution orchestration, visualization plotting, and exploratory data analysis.

## Consequences
*   Enables automated testing across core computational modules.
*   Guarantees that Phase 2 can cleanly pull from the exact same physics baseline using package import statements without deep source paths.
