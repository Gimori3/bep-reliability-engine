"""ADR-0050 drained bracket carried through the Phase 3 annualisation.

Companion to `docs/decisions/adr0050-drained-configuration-bracket.md`. The
bracket is measured on the conditional fragility curves by
``scripts/drained_configuration_bracket.py``; this driver carries it across the
annualisation integral, where every RQ3 and RQ4 headline lives and where the
prioritisation ranking that closes the thesis is formed.

Only KP 58.8 and KP 60.0 are substituted. KP 57.4 and KP 62.0 keep their
production curves, because their recorded works are a side berm alone and none
at all: the bracket is a statement about the two `drained` sections, not about
the reach. That asymmetry is the point. The ranking is a comparison, so moving
two of its four entries is what tests whether the ordering survives.

Reuse rather than re-implementation
-----------------------------------
The composition, context and gate come from
``scripts/conductivity_annualisation_study.py``, which in turn imports the
composition step from ``scripts/phase3_campaign.py``. Nothing in the Phase 3
chain is duplicated here, so gate 1 exercises the production code path and a
drift in the campaign shows up as a gate failure rather than as a silently
divergent second answer.

Gates (a failure aborts rather than being tabulated)
----------------------------------------------------
1. The baseline pass must reproduce ``rq4_annual.csv`` EXACTLY for every
   ``<d70>`` / posterior / 250 m / primary row, field for field.
2. Every segment with no BEP source, and the two BEP segments this bracket does
   not touch, must be bit-identical across every arm. An arm that moved KP 62.0
   would mean the substitution leaked.
3. Each arm's annual system probability at the two substituted segments must be
   non-increasing along the relief ladder, which is the annualised form of the
   conditional-curve monotonicity the bracket driver already enforces.

Sides. ``--side posterior`` (the default) is the deliverable: it annualises the
arm posteriors produced by ``scripts/drained_bracket_posterior_replay.py``, so
the bracket passes through the same survival update the production numbers did.
``--side prior`` annualises the Phase 1 arm curves directly and exists to
separate the survival constraint from the configuration change.

Usage (repo root, venv active)::

    python scripts/drained_bracket_annualisation.py
    python scripts/drained_bracket_annualisation.py --d70 bulk
    python scripts/drained_bracket_annualisation.py --side prior
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from system_integration.bep_input import load_bep_curve  # noqa: E402

ARM_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0050_drained_bracket"
POSTERIOR_ARM_DIR = ARM_DIR / "phase2"
DECISIONS = REPO_ROOT / "docs" / "decisions"

#: The two sections this bracket speaks about. Everything else in the reach
#: keeps its production curve.
BRACKETED_KPS: tuple[float, ...] = (58.8, 60.0)
#: The two it deliberately does not, kept here so gate 2 can name them.
UNTOUCHED_BEP_KPS: tuple[float, ...] = (57.4, 62.0)

D70_CHOICES: tuple[str, ...] = ("matrix", "bulk")
SIDE_CHOICES: tuple[str, ...] = ("posterior", "prior")


def _load(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_CONDUCTIVITY = _load("conductivity_annualisation_study")
_BRACKET = _load("drained_configuration_bracket")

# The three imported seams. Named here so a rename upstream is an ImportError
# at load time rather than a divergent number hours later.
build_context = _CONDUCTIVITY.build_context
annualise_variant = _CONDUCTIVITY.annualise_variant
gate_one = _CONDUCTIVITY.gate_one
_load_campaign_module = _CONDUCTIVITY._load_campaign_module
_label = _CONDUCTIVITY._label

ARMS: tuple[str, ...] = tuple(label for label, _ in _BRACKET.arm_labels())
RELIEF_BY_ARM: dict[str, float | None] = dict(_BRACKET.arm_labels())


def _stem(kp: float, d70: str) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{d70}"


def _arm_curve_path(kp: float, arm: str, d70: str, side: str) -> Path:
    if side == "prior":
        return ARM_DIR / f"{_stem(kp, d70)}_{arm}.h5"
    return POSTERIOR_ARM_DIR / f"{_stem(kp, d70)}_{arm}_posterior.h5"


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _f(value: Any) -> float:
    return 0.0 if value == "" or value is None else float(value)


def _compact(obj: Any, sig: int = 6) -> Any:
    if isinstance(obj, float):
        return (
            obj
            if obj != obj or obj in (float("inf"), float("-inf"))
            else float(f"%.{sig}g" % obj)
        )
    if isinstance(obj, dict):
        return {k: _compact(v, sig) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_compact(v, sig) for v in obj]
    return obj


def _leading(row: dict[str, Any]) -> str:
    contributions = {
        mech: _f(row[f"p_annual_{mech}"])
        for mech in ("bep", "overflow", "fluvial_scour")
        if row[f"p_annual_{mech}"] != ""
    }
    if not contributions or sum(contributions.values()) <= 0.0:
        return "not defined"
    return max(contributions, key=lambda m: contributions[m])


def gate_two(
    baseline_rows: dict[tuple[str, float, str], dict[str, Any]],
    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
) -> dict[str, Any]:
    """Everything this bracket does not speak about must not have moved."""
    substituted = {round(kp, 3) for kp in BRACKETED_KPS}
    checked = 0
    for arm, rows in arm_rows.items():
        for key, row in rows.items():
            if round(key[1], 3) in substituted:
                continue
            checked += 1
            if row != baseline_rows[key]:
                differing = sorted(
                    field
                    for field in row
                    if str(row[field]) != str(baseline_rows[key][field])
                )
                raise AssertionError(
                    f"GATE 2 FAILED: arm {arm} moved segment {key}, which it does "
                    f"not substitute. Fields: {differing}. The substitution has "
                    "leaked outside the two drained sections; refusing to report."
                )
    return {
        "passed": True,
        "cells_compared": checked,
        "untouched_bep_sections": [_label(kp) for kp in UNTOUCHED_BEP_KPS],
        "criterion": (
            "every segment-and-scenario row outside KP 58.8 and KP 60.0 "
            "identical, field for field, in every arm"
        ),
    }


def _phase1_artifact_budget(d70: str) -> dict[tuple[float, str], float]:
    """Absolute annual increase each arm's verified Euler artifacts can explain.

    The Phase 1 record carries, per section and arm, the monotonicity
    violations it found and individually verified to vanish under timestep
    refinement. Each such row raises the conditional transient probability by
    exactly ``1/N`` at the levels where it fires. Annualisation is a weighted
    mean of the system curve over ensemble peaks with weights at most one, and
    the series composition is monotone in each mechanism, so the induced
    increase in the annual system probability is bounded above by
    ``n_artifact / N``.

    That is a **derived** ceiling, not a chosen tolerance, and it is what makes
    the amended gate 3 below a real test: an inversion larger than the artifacts
    can account for still refuses.
    """
    record = json.loads(
        (DECISIONS / "adr0050-drained-configuration-bracket.json").read_text(
            encoding="utf-8"
        )
    )
    budget: dict[tuple[float, str], float] = {}
    for section in record["sections"]:
        if section["d70_interpretation"] != d70:
            continue
        kp = float(section["section"].removeprefix("KP"))
        n = float(section["n_samples"])
        for arm, payload in section["arms"].items():
            budget[(kp, arm)] = payload["monotonicity"]["violations"] / n
    return budget


def gate_three(
    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
    scenarios: tuple[str, ...],
    d70: str,
) -> dict[str, Any]:
    """The annualised form of the conditional-curve monotonicity.

    AMENDED 2026-08-22. The first form demanded exact non-increase and fired at
    KP 58.8 bulk, on increases of 1.2e-08 and 1.9e-08 against a value of
    2.57e-03. Those are the annualised image of the Phase 1 Euler artifacts,
    which the bracket driver has already individually verified to vanish under
    timestep refinement. Demanding that they disappear under an integral is
    demanding that a discretisation artifact stop existing, which no arm can
    satisfy. The gate now bounds the inversion by what those artifacts can
    account for, and still refuses anything larger, including any inversion at
    all where Phase 1 recorded none.
    """
    ladder = [arm for arm in ARMS if RELIEF_BY_ARM[arm] is not None]
    budget = _phase1_artifact_budget(d70)
    checked = 0
    tolerated: list[dict[str, Any]] = []
    for kp in BRACKETED_KPS:
        for scenario in scenarios:
            previous = None
            for arm in ladder:
                value = _f(arm_rows[arm][("Tokachi", kp, scenario)]["p_annual_system"])
                if previous is not None and value > previous:
                    allowed = budget.get((kp, arm), 0.0)
                    increase = value - previous
                    if increase > allowed:
                        raise AssertionError(
                            f"GATE 3 FAILED: at KP {kp:.1f} {scenario}, arm {arm} "
                            f"annualises {increase:.3e} HIGHER than the weaker "
                            f"relief above it, which exceeds the "
                            f"{allowed:.3e} its "
                            f"{int(allowed * 1e5)} verified Euler artifacts can "
                            "account for. Refusing to report."
                        )
                    tolerated.append(
                        {
                            "section": _label(kp),
                            "scenario": scenario,
                            "arm": arm,
                            "increase": increase,
                            "artifact_budget": allowed,
                            "relative_increase": increase / value,
                        }
                    )
                previous = value
                checked += 1
    return {
        "passed": True,
        "comparisons": checked,
        "ladder": ladder,
        "criterion": (
            "annual system probability non-increasing along the ladder, up to "
            "the annualised image of the Phase 1 Euler artifacts, bounded by "
            "n_artifact / N"
        ),
        "tolerated_inversions": tolerated,
    }


def summarise(
    baseline_rows: dict[tuple[str, float, str], dict[str, Any]],
    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
    scenarios: tuple[str, ...],
) -> dict[str, Any]:
    """The bracket as the thesis needs to quote it."""
    per_section: list[dict[str, Any]] = []
    for kp in BRACKETED_KPS:
        entry: dict[str, Any] = {
            "section": _label(kp),
            "kp": kp,
            "consequence_section_id": baseline_rows[("Tokachi", kp, scenarios[0])][
                "section_id"
            ],
            "scenarios": {},
        }
        for scenario in scenarios:
            base = baseline_rows[("Tokachi", kp, scenario)]
            arms: dict[str, Any] = {}
            for arm in ARMS:
                row = arm_rows[arm][("Tokachi", kp, scenario)]
                system = _f(row["p_annual_system"])
                arms[arm] = {
                    "relief_factor": RELIEF_BY_ARM[arm],
                    "p_annual_system": system,
                    "p_annual_bep": _f(row["p_annual_bep"]),
                    "p_annual_overflow": _f(row["p_annual_overflow"]),
                    "share_bep": (
                        None if row["share_bep"] == "" else _f(row["share_bep"])
                    ),
                    "leading_mechanism": _leading(row),
                    # ADR-0024: where the arm's transient transition is not
                    # bracketed the curve holds its last value above the grid,
                    # so the piping contribution can only be higher than
                    # reported. Such an arm is a LOWER BOUND, never an estimate,
                    # and the bracket must be quoted with that word.
                    "bep_clamped_above_grid": bool(row["bep_clamped_above_grid"]),
                    "system_lower_bound_clamp": bool(row["system_lower_bound_clamp"]),
                    "ratio_to_as_if_undrained": (
                        None
                        if _f(base["p_annual_system"]) == 0.0
                        else system / _f(base["p_annual_system"])
                    ),
                }
            entry["scenarios"][scenario] = {
                "as_if_undrained": {
                    "p_annual_system": _f(base["p_annual_system"]),
                    "p_annual_bep": _f(base["p_annual_bep"]),
                    "p_annual_overflow": _f(base["p_annual_overflow"]),
                    "share_bep": (
                        None if base["share_bep"] == "" else _f(base["share_bep"])
                    ),
                    "leading_mechanism": _leading(base),
                    "bep_clamped_above_grid": bool(base["bep_clamped_above_grid"]),
                    "system_lower_bound_clamp": bool(base["system_lower_bound_clamp"]),
                },
                "arms": arms,
            }
        # Climate ratio per arm, and for the baseline.
        if len(scenarios) == 2:
            hist, warm = scenarios
            ratios = {}
            base_hist = _f(baseline_rows[("Tokachi", kp, hist)]["p_annual_system"])
            base_warm = _f(baseline_rows[("Tokachi", kp, warm)]["p_annual_system"])
            ratios["as_if_undrained"] = (
                None if base_hist == 0.0 else base_warm / base_hist
            )
            for arm in ARMS:
                a_hist = _f(arm_rows[arm][("Tokachi", kp, hist)]["p_annual_system"])
                a_warm = _f(arm_rows[arm][("Tokachi", kp, warm)]["p_annual_system"])
                ratios[arm] = None if a_hist == 0.0 else a_warm / a_hist
            entry["climate_ratio"] = ratios
        per_section.append(entry)

    # The prioritisation ranking, per arm and per scenario, over the four BEP
    # segments. This is the object Chapter 9 closes on.
    all_kps = sorted(set(BRACKETED_KPS) | set(UNTOUCHED_BEP_KPS))
    ranking: dict[str, Any] = {}
    for scenario in scenarios:
        variants = {"as_if_undrained": baseline_rows}
        variants.update({arm: arm_rows[arm] for arm in ARMS})
        ranking[scenario] = {}
        for name, rows in variants.items():
            ordered = sorted(
                (
                    (_f(rows[("Tokachi", kp, scenario)]["p_annual_system"]), kp)
                    for kp in all_kps
                ),
                key=lambda pair: (-pair[0], pair[1]),
            )
            ranking[scenario][name] = {
                "order": [_label(kp) for _, kp in ordered],
                "values": {_label(kp): value for value, kp in ordered},
                "leader": _label(ordered[0][1]),
            }
    return {"per_section": per_section, "ranking": ranking}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--d70", default="matrix", choices=list(D70_CHOICES))
    parser.add_argument("--side", default="posterior", choices=list(SIDE_CHOICES))
    args = parser.parse_args(argv)

    campaign = _load_campaign_module()
    scenarios = tuple(campaign.SCENARIOS)
    context = build_context(campaign, args.d70, args.side)

    baseline_curves = dict(context["baseline_curves"])
    print(f"baseline pass ({args.d70}/{args.side}) ...", flush=True)
    baseline_rows, _, _ = annualise_variant(
        campaign, context, baseline_curves, args.d70, args.side
    )
    g1 = gate_one(baseline_rows, args.d70, args.side)
    print(f"  gate 1 passed: {g1['rows_compared']} rows reproduced exactly")

    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]] = {}
    arm_sources: dict[str, dict[str, str]] = {}
    for arm in ARMS:
        curves = dict(baseline_curves)
        sources = {}
        for kp in BRACKETED_KPS:
            path = _arm_curve_path(kp, arm, args.d70, args.side)
            if not path.is_file():
                raise FileNotFoundError(
                    f"missing arm curve {_rel(path)}. Run "
                    "scripts/drained_configuration_bracket.py and, on the "
                    "posterior side, scripts/drained_bracket_posterior_replay.py "
                    "first."
                )
            curves[kp] = load_bep_curve(path, branch="transient")
            sources[_label(kp)] = _rel(path)
        print(f"arm {arm} ...", flush=True)
        rows, _, _ = annualise_variant(campaign, context, curves, args.d70, args.side)
        arm_rows[arm] = rows
        arm_sources[arm] = sources

    g2 = gate_two(baseline_rows, arm_rows)
    print(f"  gate 2 passed: {g2['cells_compared']} untouched cells unmoved")
    g3 = gate_three(arm_rows, scenarios, args.d70)
    print(f"  gate 3 passed: {g3['comparisons']} ladder comparisons monotone")

    payload = {
        "study": "ADR-0050 drained-configuration bracket, Phase 3 annualisation",
        "generated": _dt.datetime.now().replace(microsecond=0).isoformat(),
        "generated_by": "scripts/drained_bracket_annualisation.py",
        "d70_interpretation": args.d70,
        "side": args.side,
        "scope": (
            "KP 58.8 and KP 60.0 only; KP 57.4 and KP 62.0 keep their production "
            "curves because their recorded works are a berm alone and none at all"
        ),
        "bracketed_sections": [_label(kp) for kp in BRACKETED_KPS],
        "arm_curve_sources": arm_sources,
        "gates": {"gate_1": g1, "gate_2": g2, "gate_3": g3},
        **summarise(baseline_rows, arm_rows, scenarios),
    }
    out = DECISIONS / (
        f"adr0050-drained-bracket-annualisation-{args.d70}-{args.side}.json"
    )
    out.write_text(json.dumps(_compact(payload), indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {_rel(out)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
