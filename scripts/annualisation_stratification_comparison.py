"""Old versus new for the pattern-stratified annualisation bootstrap.

Companion to Part 3 of `docs/decisions/annualisation-hazard-sampling-uncertainty.md`
(2026-09-17). The estimator's block draw changed from a pooled resample of all
90 warming member blocks to one stratified inside the six prescribed
sea-surface-temperature patterns. That is a change to a **published** interval
set, so the superseded record is kept and this driver states, field by field,
what moved and why, rather than leaving a reader to diff two 150 kB JSONs.

What it checks, and it aborts rather than reporting a violation
---------------------------------------------------------------
1. **Every point estimate is identical.** The design is balanced, so the plain
   ensemble mean is the equally weighted pattern mean exactly; stratification
   cannot move a production number and the comparison would be a different
   study if it had.
2. **Every historical quantity is identical.** The historical ensemble carries
   one forcing group, so its stratified draw is the pooled draw, call for call,
   against the same generator state. Bit-identity here is the proof that only
   the warming half of the estimator changed.
3. **Every pooled resampling-unit arm is identical**, because the sensitivity's
   pooled pass runs first and takes the stream it always took.

What it reports
---------------
Per changed leaf: both values, the relative move, the scenario the path sits
in, and a cause drawn from the structure of the change rather than guessed.
Verdict strings are collected separately, so a changed pre-registration outcome
is never buried among ten thousand interval endpoints.

Usage (repo root, venv active)::

    python scripts/annualisation_stratification_comparison.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = REPO_ROOT / "docs" / "decisions"
SUPERSEDED = (
    DECISIONS / "annualisation-hazard-sampling-uncertainty-pooled-draw-2026-09-14.json"
)
CURRENT = DECISIONS / "annualisation-hazard-sampling-uncertainty.json"
DEFAULT_OUT = DECISIONS / "annualisation-pattern-stratification-comparison.json"

#: Keys whose value is a pre-registered outcome rather than a number.
VERDICT_KEYS = frozenset(
    {
        "verdict",
        "resolved",
        "endpoints_resolve",
        "lead_resolved",
        "resolvably_not_a_tie",
        "three_decimal_quotation_supported",
        "two_decimal_quotation_supported",
        "printed_precision_supported",
        "count_limited",
        "clears_floor",
    }
)

#: Keys that record when or where the study ran, not what it measured.
VOLATILE_KEYS = frozenset({"generated", "elapsed_s", "writes"})


def flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    """Every scalar leaf of a JSON tree, keyed by its slash-joined path."""
    out: dict[str, Any] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            if key in VOLATILE_KEYS and not prefix:
                continue
            out.update(flatten(value, f"{prefix}/{key}" if prefix else str(key)))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            out.update(flatten(value, f"{prefix}[{i}]"))
    else:
        out[prefix] = node
    return out


def scenario_of(path: str) -> str:
    """Which ensemble a path's value is computed from."""
    warming = "/+4K" in path or path.endswith("+4K")
    historical = "/historical" in path or path.endswith("historical")
    if warming and not historical:
        return "+4K"
    if historical and not warming:
        return "historical"
    if warming and historical:
        return "both"
    if "climate_ratio" in path or "ratio" in path:
        return "both"
    return "unscoped"


def cause_of(path: str, scenario: str) -> str:
    """Why this leaf moved, from the structure of the change."""
    if path.endswith("/point") or path.endswith("/published_point"):
        return "POINT ESTIMATE MOVED (must not happen)"
    if scenario == "historical":
        return "HISTORICAL QUANTITY MOVED (must not happen)"
    if "resampling_unit_sensitivity" in path:
        return "resampling-unit arm restructured into pooled and stratified readings"
    if scenario == "+4K":
        return (
            "warming interval no longer carries between-pattern structural "
            "spread: the six prescribed patterns are now held at equal weight "
            "in every replicate instead of being reweighted by the draw"
        )
    if scenario == "both":
        return (
            "climate ratio and its contrasts are formed inside each replicate, "
            "so the warming half of the pairing moved with the estimator while "
            "the historical half did not"
        )
    return "estimator description or new diagnostic"


def pooled_arm_identity(
    flat_old: dict[str, Any], flat_new: dict[str, Any]
) -> dict[str, Any]:
    """The superseded sensitivity arms against the new record's pooled arms.

    Part 3 moved each resampling-unit arm from
    ``resampling_unit_sensitivity/<unit>/<scenario>/...`` down one level into
    ``.../pooled/...`` and added a ``pattern_stratified`` sibling. The pooled
    pass is drawn first and takes exactly the stream it always took, so every
    one of those values must be bit-identical; the path move is the only
    difference. Checked rather than assumed, because a silent stream shift
    would make the two readings incomparable.
    """
    mismatches: list[str] = []
    compared = 0
    for path, value in flat_old.items():
        if not path.startswith("resampling_unit_sensitivity/"):
            continue
        parts = path.split("/")
        if len(parts) < 3:
            continue
        moved = "/".join(parts[:3] + ["pooled"] + parts[3:])
        target = moved if moved in flat_new else path
        if target not in flat_new:
            mismatches.append(f"{path}: absent from the current record")
            continue
        compared += 1
        if flat_new[target] != value:
            mismatches.append(f"{path}: {value!r} -> {flat_new[target]!r}")
    return {
        "leaves_compared": compared,
        "criterion": (
            "every superseded resampling-unit value reappears bit-identical "
            "under the same unit's pooled arm"
        ),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def compare(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    flat_old = flatten(old)
    flat_new = flatten(new)
    shared = sorted(set(flat_old) & set(flat_new))

    changed: list[dict[str, Any]] = []
    verdicts: list[dict[str, Any]] = []
    unchanged = 0
    violations: list[str] = []
    by_scenario: dict[str, dict[str, int]] = {}

    for path in shared:
        a, b = flat_old[path], flat_new[path]
        key = path.rsplit("/", 1)[-1].split("[")[0]
        scenario = scenario_of(path)
        bucket = by_scenario.setdefault(scenario, {"unchanged": 0, "changed": 0})
        if a == b:
            unchanged += 1
            bucket["unchanged"] += 1
            continue
        bucket["changed"] += 1
        cause = cause_of(path, scenario)
        record = {
            "path": path,
            "old": a,
            "new": b,
            "scenario": scenario,
            "cause": cause,
        }
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if not isinstance(a, bool) and not isinstance(b, bool):
                record["absolute_change"] = b - a
                record["relative_change"] = (b - a) / a if a else None
        if key in VERDICT_KEYS:
            verdicts.append(record)
        changed.append(record)
        if cause.endswith("(must not happen)"):
            violations.append(f"{path}: {a!r} -> {b!r}")

    if violations:
        raise AssertionError(
            "the stratified draw moved something it structurally cannot move; "
            "either the design is not balanced or the historical stratum is not "
            "a single group:\n  " + "\n  ".join(violations[:20])
        )

    pooled = pooled_arm_identity(flat_old, flat_new)
    if pooled["mismatches"]:
        raise AssertionError(
            "a pooled resampling-unit arm moved. It is drawn in a first pass "
            "that takes the stream it always took, so it must be bit-identical "
            "to the superseded record; a move means the sensitivity's stream "
            "consumption changed and the two readings no longer compare one "
            "thing.\n  " + "\n  ".join(pooled["mismatches"][:20])
        )

    return {
        "pooled_arm_identity": pooled,
        "n_leaves_compared": len(shared),
        "n_unchanged": unchanged,
        "n_changed": len(changed),
        "by_scenario": by_scenario,
        "only_in_superseded": sorted(set(flat_old) - set(flat_new)),
        "only_in_current": sorted(set(flat_new) - set(flat_old)),
        "changed_verdicts": verdicts,
        "changed": changed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--superseded", type=Path, default=SUPERSEDED)
    parser.add_argument("--current", type=Path, default=CURRENT)
    args = parser.parse_args(argv)

    old = json.loads(args.superseded.read_text(encoding="utf-8"))
    new = json.loads(args.current.read_text(encoding="utf-8"))
    result = compare(old, new)
    payload = {
        "study": (
            "Old versus new for the pattern-stratified annualisation bootstrap "
            "(Part 3, 2026-09-17)"
        ),
        "generated_by": "scripts/annualisation_stratification_comparison.py",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "note": "docs/decisions/annualisation-hazard-sampling-uncertainty.md",
        "superseded_record": args.superseded.name,
        "current_record": args.current.name,
        "invariants_asserted": [
            "every point estimate identical",
            "every historical quantity identical",
            "every pooled resampling-unit arm identical",
        ],
        **result,
    }
    args.out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    print(f"{result['n_leaves_compared']} shared leaves compared")
    print(f"  unchanged {result['n_unchanged']}, changed {result['n_changed']}")
    for scenario, counts in sorted(result["by_scenario"].items()):
        print(
            f"  {scenario:<11} unchanged {counts['unchanged']:>6}  "
            f"changed {counts['changed']:>6}"
        )
    identity = result["pooled_arm_identity"]
    print(
        f"  pooled sensitivity arms: {identity['leaves_compared']} leaves, "
        "all identical"
    )
    print(f"  verdict fields changed: {len(result['changed_verdicts'])}")
    for record in result["changed_verdicts"]:
        print(f"    {record['path']}: {record['old']!r} -> {record['new']!r}")
    print(f"\nwrote {args.out.relative_to(REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
