"""Design effects of the ensemble nesting on the annual estimand ``P_sys(peak_j)``.

Section 0b of ``docs/decisions/annualisation-hazard-sampling-uncertainty.md``
measured, once and by hand (2026-09-14), how strongly the annual estimand
clusters by ensemble member and, under warming, by sea-surface-temperature
pattern. No driver regenerated it, so the table there predates the ADR-0054
matrix d70 re-basing and the ADR-0059 KP 57.4 aquifer-thickness correction.
This driver recomputes it on the current curves with the estimator section 0b
states:

* the one-way ANOVA moment estimator of the intra-cluster correlation of
  ``P_sys(peak_j)`` over balanced groups (60 years per member, 900 events per
  SST pattern), and
* the design effect ``1 + (m - 1) ICC``, floored at 1.00 for a negative
  estimate, as section 0b prints it.

``P_sys(peak_j)`` is the system curve of
``results/system_integration/phase3/rq3_segment_curves_matrix_{posterior,prior}.json``
at each event's peak stage from ``results/system_integration/hazard_cache``,
interpolated linearly and clamped at the grid ends as
``system_integration.annualize`` does. Two conditionings are reported: the
adopted one of ADR-0056 (posterior at KP 57.4 and 62.0, prior at the drained
KP 58.8 and 60.0) and, for comparison with section 0b, the posterior at all four.

Usage:
    python scripts/hazard_sampling_design_effects.py
        [--results results] [--out docs/decisions/annualisation-design-effects.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np

SECTIONS = {
    "KP 57.4": ("Tokachi_KP57.4", "kp57.4"),
    "KP 58.8": ("Tokachi_KP58.8", "kp58.8"),
    "KP 60.0": ("Tokachi_KP60", "kp60.0"),
    "KP 62.0": ("Tokachi_KP62", "kp62.0"),
}
DRAINED = ("KP 58.8", "KP 60.0")


def icc_design_effect(values: np.ndarray, groups: list[str]) -> dict:
    """One-way ANOVA ICC and design effect for balanced groups."""
    keys = sorted(set(groups))
    index = np.array([keys.index(g) for g in groups])
    k, n = len(keys), len(values)
    m = n // k
    if any(int((index == i).sum()) != m for i in range(k)):
        raise ValueError("groups are not balanced")
    means = np.array([values[index == i].mean() for i in range(k)])
    msb = m * float(((means - values.mean()) ** 2).sum()) / (k - 1)
    msw = sum(float(((values[index == i] - means[i]) ** 2).sum()) for i in range(k)) / (
        n - k
    )
    denom = msb + (m - 1) * msw
    icc = (msb - msw) / denom if denom > 0 else 0.0
    deff = 1.0 + (m - 1) * icc
    return {
        "icc": icc,
        "design_effect": deff,
        "design_effect_floored": max(1.0, deff),
        "groups": k,
        "per_group": m,
    }


def _hazard(results: Path, tag: str, scenario: str) -> list[dict]:
    path = (
        results
        / "system_integration/hazard_cache"
        / (f"hazard_tokachi_{tag}_{scenario}.csv")
    )
    with path.open(encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip('"').startswith("#")]
    return list(csv.DictReader(lines))


def compute(results: Path) -> dict:
    phase3 = results / "system_integration/phase3"
    curves = {
        c: json.loads(
            (phase3 / f"rq3_segment_curves_matrix_{c}.json").read_text(encoding="utf-8")
        )
        for c in ("posterior", "prior")
    }
    cells: dict[str, dict] = {}
    for conditioning in ("adopted", "all_posterior"):
        for label, (node, tag) in SECTIONS.items():
            side = (
                "prior"
                if conditioning == "adopted" and label in DRAINED
                else "posterior"
            )
            curve = curves[side][node]
            x = np.asarray(curve["stage_m_msl"], float)
            y = np.asarray(curve["p_sys"], float)
            for scenario, fname in (("historical", "historical"), ("+4K", "plus4K")):
                rows = _hazard(results, tag, fname)
                peaks = np.array([float(r["peak_stage_m_msl"]) for r in rows])
                p = np.interp(np.clip(peaks, x[0], x[-1]), x, y)
                ids = [r["event_id"] for r in rows]
                entry = {
                    "curve": side,
                    "by_member": icc_design_effect(
                        p, [re.sub(r"_\d{4}$", "", e) for e in ids]
                    ),
                }
                if scenario == "+4K":
                    entry["by_sst_pattern"] = icc_design_effect(
                        p, [e.split("_")[1] for e in ids]
                    )
                cells[f"{conditioning} {scenario} {label}"] = entry
    summary = {}
    for conditioning in ("adopted", "all_posterior"):
        member = [
            v["by_member"]["design_effect_floored"]
            for k, v in cells.items()
            if k.startswith(conditioning + " ")
        ]
        sst = [
            v["by_sst_pattern"]["design_effect_floored"]
            for k, v in cells.items()
            if k.startswith(conditioning + " ") and "by_sst_pattern" in v
        ]
        summary[conditioning] = {
            "member_range": [min(member), max(member)],
            "sst_pattern_range": [min(sst), max(sst)],
        }
    return {"cells": cells, "summary": summary}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--results", type=Path, default=Path("results"))
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("docs/decisions/annualisation-design-effects.json"),
    )
    a = ap.parse_args()
    record = {
        "study": "hazard-sampling-design-effects",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "estimator": (
            "one-way ANOVA ICC of P_sys(peak_j) over balanced groups; design effect "
            "1 + (m - 1) ICC, floored at 1.00 as section 0b of "
            "annualisation-hazard-sampling-uncertainty.md prints it"
        ),
        "curves": "rq3_segment_curves_matrix_{posterior,prior}.json, linear, clamped",
        **compute(a.results),
    }
    a.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    for k, v in record["summary"].items():
        print(k, v)


if __name__ == "__main__":
    main()
