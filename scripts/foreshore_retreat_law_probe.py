"""How much of the R10 softening factor is a property of the rate *law*?

The foreshore-exhaustion indicator
(:mod:`system_integration.foreshore_exhaustion`) holds the lateral retreat rate
constant while the high-water bed is mobilised. Two claims were attached to
that choice, and only one of them is true of every law.

**The bounding claim, which is a theorem.** Calibrate any rate ``f(d)`` of
excess depth ``d`` so that ``f(d_peak)`` equals the constant rate. On the
mobilising window ``d(t) <= d_peak``, so for every non-decreasing ``f``

    cumulative_retreat(f) = integral f(d(t)) dt <= f(d_peak) * T_mob,

i.e. ``exposure_ratio(f) <= exposure_ratio(const)``. The constant-rate
treatment is therefore bounding whatever the law, with no exponent involved.

**The magnitude claim, which is not.** The ratio reported per case,
``mean_excess_depth_m / peak_excess_depth_m``, is

    exposure_ratio(f) / exposure_ratio(const) = E[f(d)] / f(d_peak)

only when ``f`` is **linear** in excess depth. Writing ``x = d / d_peak`` in
[0, 1] and ``f = c d**p`` gives ``R(p) = E[x**p]``, which is strictly
decreasing in ``p`` unless the depth is constant: a convex law (the
shear-stress-like case) softens *more* than the mean-to-peak ratio, a concave
law *less*, and the factor is unbounded as ``p`` grows. The engine's
``ExhaustionResult.mean_excess_depth_m`` docstring asserted the magnitude for
"any monotone depth-dependent rate law" until 2026-09-17, and the thesis
carried the same generalization; this driver measures what the exponent
actually buys, so both can state the linear case and the bounding direction
separately.

Nothing here is a new mechanism, a new bracket member or a new default. It
reads the same forcing the parent study reads, adds no uncertain input, and
persists only its own evidence JSON. The indicator, its rate bracket, its
threshold bracket and every published exposure ratio are untouched.

Usage
-----
    python scripts/foreshore_retreat_law_probe.py
    python scripts/foreshore_retreat_law_probe.py --out /tmp/probe.json

Runtime is seconds: one 2016 record per section, no ensemble arm.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from bayesian_reliability_updating.events import (
    default_2016_source,
    observed_event_record,
)
from system_integration.foreshore_exhaustion import load_measured_foreshore_states
from system_integration.segments import build_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "docs" / "decisions" / "r10-foreshore-retreat-law-probe.json"

#: Exponents of the power-law family ``f(d) = c d**p``. 1.0 is the linear law
#: the published mean-to-peak ratio describes; 0.5 and 2.0 bracket it with a
#: concave and a convex member, and 3.0 shows the factor does not converge.
EXPONENTS: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 3.0)

#: Mobilisation-threshold offsets, the parent study's own band [m].
THRESHOLD_OFFSETS_M: tuple[float, ...] = (-1.0, 0.0, +1.0)


def _threshold_label(offset_m: float) -> str:
    return "z_mob" if offset_m == 0.0 else f"z_mob{offset_m:+.1f}m"


def reduction_factors(excess_depth_m: np.ndarray) -> dict[str, Any]:
    """``R(p) = E[x**p]`` and its reciprocal, on one mobilising window."""
    peak = float(excess_depth_m.max())
    x = excess_depth_m / peak
    r_of_p = {f"{p:g}": float(np.mean(x**p)) for p in EXPONENTS}
    return {
        "n_samples": int(excess_depth_m.size),
        "peak_excess_depth_m": peak,
        "mean_excess_depth_m": float(excess_depth_m.mean()),
        "linear_ratio_mean_over_peak": float(excess_depth_m.mean() / peak),
        "R_of_p": r_of_p,
        "softening_factor_1_over_R": {k: 1.0 / v for k, v in r_of_p.items()},
    }


def measure() -> dict[str, Any]:
    """The whole measurement: four sections, three thresholds, five exponents."""
    source = default_2016_source()
    states = load_measured_foreshore_states(build_registry())
    sections: dict[str, Any] = {}
    for state in sorted(states, key=lambda s: s.kp):
        record = observed_event_record(source, section_kp=state.kp)
        stage = np.asarray(record.h, dtype=np.float64)
        per_threshold: dict[str, Any] = {}
        for offset in THRESHOLD_OFFSETS_M:
            z_mob = state.mobilisation_stage_m_msl + offset
            depth = stage[stage > z_mob] - z_mob
            per_threshold[_threshold_label(offset)] = (
                reduction_factors(depth) if depth.size else {"n_samples": 0}
            )
        sections[f"KP{state.kp:.1f}"] = {
            "mobilisation_stage_m_msl": state.mobilisation_stage_m_msl,
            "event_id": record.event_id,
            "thresholds": per_threshold,
        }
    return sections


def gate(sections: dict[str, Any]) -> dict[str, Any]:
    """Two checks, both of them about the shape of the family, not its values.

    Gate 1 is the derived prediction: ``R(p)`` strictly decreases in ``p`` at
    every populated cell. Gate 2 measures the *defect* rather than restating
    the fix. The claim under test is the published one read as universal, that
    *any* monotone law softens the exposure ratio by "roughly two to four";
    the gate fires only if the measured family escapes that window on both
    sides, a concave member below 2 and a convex member above 4. A family
    that were exponent-insensitive would leave the window intact and fail
    this gate, which is why it is asserted this way round.

    An earlier form of gate 2 compared the concave span with the linear span
    across sections and failed: the two overlap (concave 1.55 to 2.16 against
    linear 2.10 to 3.64), because the between-section spread is of the same
    size as the exponent effect. Spans across sections are the wrong
    comparison; the window the thesis printed is the right one.
    """
    decreasing: list[dict[str, Any]] = []
    linear, concave, convex = [], [], []
    for name, block in sections.items():
        for label, cell in block["thresholds"].items():
            if not cell.get("n_samples"):
                continue
            series = [cell["R_of_p"][f"{p:g}"] for p in EXPONENTS]
            decreasing.append(
                {
                    "cell": f"{name}/{label}",
                    "strictly_decreasing": all(
                        later < earlier
                        for earlier, later in zip(series[:-1], series[1:], strict=True)
                    ),
                }
            )
            if label == "z_mob":
                linear.append(cell["softening_factor_1_over_R"]["1"])
                concave.append(cell["softening_factor_1_over_R"]["0.5"])
                convex.append(cell["softening_factor_1_over_R"]["2"])
    return {
        "gate_1_R_strictly_decreasing_in_p": {
            "statement": (
                "R(p) = E[x**p] decreases strictly in p at every populated "
                "section and threshold cell"
            ),
            "held": all(row["strictly_decreasing"] for row in decreasing),
            "cells_checked": len(decreasing),
            "per_cell": decreasing,
        },
        "gate_2_family_escapes_the_published_window": {
            "statement": (
                "read as universal, the published softening window of roughly "
                "two to four does not hold: at the primary threshold some "
                "concave (p=0.5) member softens by less than 2 and some "
                "convex (p=2) member by more than 4"
            ),
            "published_window": [2.0, 4.0],
            "held": bool(min(concave) < 2.0 and max(convex) > 4.0),
            "linear_span": [min(linear), max(linear)],
            "concave_span": [min(concave), max(concave)],
            "convex_span": [min(convex), max(convex)],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    sections = measure()
    gates = gate(sections)
    payload = {
        "study": (
            "R10 foreshore-exhaustion: the retreat-law exponent behind the "
            "softening factor"
        ),
        "generated": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "scripts/foreshore_retreat_law_probe.py",
        "parent": "docs/decisions/r10-foreshore-exhaustion-screening.md",
        "forcing": "observed August 2016 record per section (ADR-0035 chain)",
        "exponents": list(EXPONENTS),
        "not_a_probability": (
            "these are ratios between two screening treatments of the same "
            "event, not probabilities, and no mechanism joins the Phase 3 "
            "composition"
        ),
        "sections": sections,
        "gates": gates,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    for name, block in sections.items():
        cell = block["thresholds"]["z_mob"]
        print(
            f"{name}: mean/peak = {cell['linear_ratio_mean_over_peak']:.3f}, "
            f"softening x{cell['softening_factor_1_over_R']['0.5']:.2f} "
            f"(p=0.5) / x{cell['softening_factor_1_over_R']['1']:.2f} "
            f"(p=1) / x{cell['softening_factor_1_over_R']['2']:.2f} (p=2)"
        )
    for key, block in gates.items():
        print(f"{key}: {'PASS' if block['held'] else 'FAIL'}")
    print(f"wrote {args.out}")
    return 0 if all(b["held"] for b in gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
