"""The time effect set beside the input uncertainty on one quantity (Pol round 2, A24).

Joost Pol's annotation A24 on the 11 September 2026 thesis asks that the factor
due to flood duration be weighed against the uncertain inputs ("Measuring
permeability has more impact"). Every number this driver needs already exists
in committed evidence JSON under ``docs/decisions/``; it re-runs nothing. It
sets each tested alternative on one quantity, the annual system failure
probability of each investigated segment on the adopted conditioning
(ADR-0056), as the factor ``P(alternative) / P(adopted)``, beside the factor of
the steady-state criterion (the time effect, ADR-0055), and evaluates the
pre-registered predictions P1 to P6 of
``docs/decisions/time-effect-in-proportion-study.md`` by the rule fixed there.

Usage::

    python scripts/time_effect_in_proportion.py            # JSON and figure
    python scripts/time_effect_in_proportion.py --no-figure

Outputs: ``docs/decisions/time-effect-in-proportion-study.json`` and
``docs/figures/time_effect_in_proportion.png``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DECISIONS = REPO / "docs" / "decisions"
OUT_JSON = DECISIONS / "time-effect-in-proportion-study.json"
FIGURE_NAME = "time_effect_in_proportion.png"

SECTIONS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")
DRAINED = ("KP 58.8", "KP 60.0")
CLIMATES = ("historical", "+4K")

SOURCES = {
    "time_factor": "time-dependence-factor-study.json",
    "adopted": "drained-section-conditioning-adopted.json",
    "alternatives": "drained-section-conditioning-alternatives.json",
    "gravel": "gravel-grading-resistance-study.json",
    "seepage_tail": "seepage-length-lower-tail-adopted.json",
    "shape": "canonical-shape-sensitivity.json",
}

#: Row order and display text. Keys are this study's own schema; the labels
#: are what the figure prints (``docs/conventions.md`` section 9.3.1).
ROWS: tuple[tuple[str, str, str], ...] = (
    ("criterion_steady_state", "Steady-state criterion", "criterion"),
    ("k_field_mean", "Conductivity: field-test mean", "conductivity"),
    ("k_toe_test", "Conductivity: landside-toe test", "conductivity"),
    ("k_regional_upper", "Conductivity: regional upper value", "conductivity"),
    ("grain_bulk", "Grain size: whole sand-gravel", "favoring"),
    ("gravel_x1_8", "Gravel allowance, critical head x1.8", "favoring"),
    ("foreland_half", "Foreland credit, half", "favoring"),
    ("foreland_full", "Foreland credit, full", "favoring"),
    ("drain_berm_inert", "Measured berm, drain inert", "favoring"),
    ("drain_berm_relief80", "Measured berm, 80 % drain relief", "favoring"),
    ("seepage_tail_bounded", "Seepage length bounded below", "favoring"),
    ("flood_shorter", "Shorter canonical flood", "favoring"),
    ("correlation_40m", "Correlation length 40 m", "other"),
)


def _load(name: str) -> dict[str, Any]:
    return json.loads((DECISIONS / name).read_text(encoding="utf-8"))


def _sha256(name: str) -> str:
    """SHA-256 of a source's LF-normalised bytes, so any checkout agrees."""
    data = (DECISIONS / name).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _ratio(num: float | None, den: float) -> float | None:
    """``num / den``; ``None`` marks a section the row does not reach."""
    if num is None:
        return None
    return float(num) / float(den)


def adopted_system(adopted: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Adopted annual system probability per climate and section (ADR-0056)."""
    table = adopted["table"]
    return {
        c: {s: float(table[f"{c} {s}"]["p_system"]) for s in SECTIONS} for c in CLIMATES
    }


def collate() -> dict[str, Any]:
    """All factors ``P(alternative) / P(adopted)`` on the adopted conditioning."""
    tdf = _load(SOURCES["time_factor"])
    adopted = _load(SOURCES["adopted"])
    alt = _load(SOURCES["alternatives"])
    gravel = _load(SOURCES["gravel"])["annual"]["cells"]
    tail = _load(SOURCES["seepage_tail"])["annual"]
    shape = _load(SOURCES["shape"])["phase3"]["sections"]
    base = adopted_system(adopted)

    paired = tdf["annual"]["matrix"]["paired_comparisons"]["I-prior / T-prior"]
    factors: dict[str, dict[str, dict[str, float | None]]] = {
        key: {c: {} for c in CLIMATES} for key, _, _ in ROWS
    }
    spans: dict[str, dict[str, float | None]] = {c: {} for c in CLIMATES}
    for c in CLIMATES:
        for s in SECTIONS:
            p0 = base[c][s]
            cell = alt["cells"][f"{c} {s}"]
            arms = cell["system_by_arm"]
            # The adopted arm of the alternatives table is the adopted value.
            if not math.isclose(arms["matrix"], p0, rel_tol=1e-6):
                raise AssertionError(f"{c} {s}: alternatives matrix arm != adopted")
            f = factors
            f["criterion_steady_state"][c][s] = float(
                paired[f"{s} {c} system"]["point"]
            )
            f["k_field_mean"][c][s] = _ratio(arms["k_aq_field_geomean"], p0)
            f["k_toe_test"][c][s] = _ratio(arms["k_aq_field_toe"], p0)
            f["k_regional_upper"][c][s] = _ratio(arms["k_aq_regional_upper"], p0)
            f["grain_bulk"][c][s] = float(cell["bulk_over_matrix_system"])
            f["foreland_half"][c][s] = float(cell["foreland_half_system_ratio"])
            f["foreland_full"][c][s] = float(cell["foreland_full_system_ratio"])
            side = "T-prior" if s in DRAINED else "T-post"
            g1 = gravel[f"x1.00 {side} {c} {s}"]["p_system"]
            if not math.isclose(g1, p0, rel_tol=1e-6):
                raise AssertionError(f"{c} {s}: gravel x1.00 != adopted")
            f["gravel_x1_8"][c][s] = _ratio(
                gravel[f"x1.80 {side} {c} {s}"]["p_system"], p0
            )
            t0 = tail[f"t0.00 {c} {s}"]["p_system"]
            if not math.isclose(t0, p0, rel_tol=1e-6):
                raise AssertionError(f"{c} {s}: seepage tail t0.00 != adopted")
            f["seepage_tail_bounded"][c][s] = _ratio(
                tail[f"t0.85 {c} {s}"]["p_system"], p0
            )
            sc = shape[f"{s} {c}"]
            # Published on the prior basis; the ratio is taken on that basis.
            f["flood_shorter"][c][s] = _ratio(
                sc["p_annual_system_alternate"], sc["p_annual_system_production"]
            )
            f["correlation_40m"][c][s] = float(
                alt["lambda_ac_factors"][f"{c} {s}"]["40"]
            )
            if s in DRAINED:
                dr = adopted["drained_readings"]
                f["drain_berm_inert"][c][s] = _ratio(
                    dr[f"berm {c} {s}"]["p_system"], p0
                )
                f["drain_berm_relief80"][c][s] = _ratio(
                    dr[f"berm_relief_80pct {c} {s}"]["p_system"], p0
                )
            else:
                f["drain_berm_inert"][c][s] = None
                f["drain_berm_relief80"][c][s] = None
            vals = [p0] + [
                arms[a]
                for a in ("k_aq_field_geomean", "k_aq_field_toe", "k_aq_regional_upper")
            ]
            lo, hi = min(vals), max(vals)
            spans[c][s] = None if lo <= 0.0 else hi / lo
    return {"adopted_system": base, "factors": factors, "conductivity_span": spans}


def _abslog(x: float | None) -> float:
    """``|log10 x|``; a zero alternative is an unbounded displacement."""
    if x is None:
        return float("nan")
    if x <= 0.0:
        return math.inf
    return abs(math.log10(x))


def verdicts(col: dict[str, Any]) -> dict[str, Any]:
    """P1 to P6 by the rule fixed in Part 1 of the study note."""
    f = col["factors"]
    te = f["criterion_steady_state"]
    span = col["conductivity_span"]
    out: dict[str, Any] = {}

    # P1: historical conductivity span > 10 x time effect where bounded.
    p1 = {}
    for s in SECTIONS:
        sp = span["historical"][s]
        t = te["historical"][s]
        p1[s] = {
            "span": sp,
            "time_effect": t,
            "span_over_time_effect": None if sp is None else sp / t,
            "holds": True if sp is None else sp > 10.0 * t,
        }
    out["P1"] = {"cells": p1, "holds": all(v["holds"] for v in p1.values())}

    # P2: max displacement of four rows >= (largest time effect)^3 in |log10|.
    te_max = max(te["historical"].values())
    p2 = {}
    for key in ("grain_bulk", "gravel_x1_8", "foreland_full", "drain_berm_relief80"):
        disp = max(_abslog(v) for v in f[key]["historical"].values() if v is not None)
        p2[key] = {
            "max_abs_log10": disp,
            "threshold_abs_log10": 3.0 * math.log10(te_max),
            "holds": disp >= 3.0 * math.log10(te_max),
        }
    out["P2"] = {
        "largest_time_effect": te_max,
        "rows": p2,
        "holds": all(v["holds"] for v in p2.values()),
    }

    # P3: seepage tail and shorter flood each below the time effect everywhere.
    p3 = {}
    for key in ("seepage_tail_bounded", "flood_shorter"):
        cells = {}
        for s in SECTIONS:
            a = _abslog(f[key]["historical"][s])
            b = _abslog(te["historical"][s])
            cells[s] = {
                "factor": f[key]["historical"][s],
                "time_effect": te["historical"][s],
                "holds": a < b,
            }
        p3[key] = {"cells": cells, "holds": all(v["holds"] for v in cells.values())}
    out["P3"] = {"rows": p3, "holds": all(v["holds"] for v in p3.values())}

    # P4: correlation length 40 m raises it by more than the time effect somewhere.
    p4 = {
        s: f["correlation_40m"]["historical"][s] > te["historical"][s] for s in SECTIONS
    }
    out["P4"] = {"cells": p4, "holds": any(p4.values())}

    # P5: +4 K conductivity span > time effect where bounded.
    p5 = {}
    for s in SECTIONS:
        sp = span["+4K"][s]
        t = te["+4K"][s]
        p5[s] = {
            "span": sp,
            "time_effect": t,
            "span_over_time_effect": None if sp is None else sp / t,
            "holds": True if sp is None else sp > t,
        }
    out["P5"] = {"cells": p5, "holds": all(v["holds"] for v in p5.values())}

    # P6: the time effect lowers the annual probability everywhere.
    p6 = {f"{c} {s}": te[c][s] > 1.0 for c in CLIMATES for s in SECTIONS}
    out["P6"] = {"cells": p6, "holds": all(p6.values())}
    return out


def summary(col: dict[str, Any]) -> dict[str, Any]:
    """Per row and climate: the range of factors and the largest displacement."""
    rows = {}
    for key, label, kind in ROWS:
        per = {}
        for c in CLIMATES:
            vals = {s: v for s, v in col["factors"][key][c].items() if v is not None}
            finite = [v for v in vals.values() if v > 0.0]
            per[c] = {
                "min_factor": min(vals.values()) if vals else None,
                "max_factor": max(vals.values()) if vals else None,
                "sections_with_no_computed_failure": sorted(
                    s for s, v in vals.items() if v <= 0.0
                ),
                "max_abs_log10": max((_abslog(v) for v in vals.values()), default=None),
                "min_positive_factor": min(finite) if finite else None,
            }
        rows[key] = {"label": label, "kind": kind, **per}
    return rows


def build() -> dict[str, Any]:
    col = collate()
    return {
        "study": "time-effect-in-proportion",
        "generated_by": "scripts/time_effect_in_proportion.py",
        "note": "docs/decisions/time-effect-in-proportion-study.md",
        "quantity": (
            "annual system failure probability of each investigated 200 m "
            "segment, matrix reading, adopted conductivity, correlation length "
            "250 m, primary surface curves, canonical event, adopted "
            "conditioning (2016 update at KP 57.4 and 62.0, prior at KP 58.8 "
            "and 60.0); factor = P(alternative) / P(adopted)"
        ),
        "criterion_basis": (
            "steady-state over time-dependent criterion, both before any "
            "survival update (time-dependence-factor-study annual block); at "
            "KP 57.4 and 62.0 each criterion's own update changes it by less "
            "than 3 per cent and the drained sections are not conditioned"
        ),
        "flood_shape_basis": (
            "prior on both sides, as published in canonical-shape-sensitivity"
        ),
        "zero_means": "no computed failure in any simulated year: an unbounded factor",
        "sources": {
            k: {"file": v, "sha256_lf": _sha256(v)} for k, v in SOURCES.items()
        },
        "sections": list(SECTIONS),
        "rows": [{"key": k, "label": lab, "kind": kind} for k, lab, kind in ROWS],
        **col,
        "summary": summary(col),
        "verdicts": verdicts(col),
    }


def _round(obj: Any) -> Any:
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return str(obj)
        return float(f"{obj:.6g}")
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v) for v in obj]
    return obj


def write_json(record: dict[str, Any]) -> Path:
    OUT_JSON.write_text(
        json.dumps(_round(record), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return OUT_JSON


def figure(record: dict[str, Any]) -> Path:
    """Two panels (historical, +4 K) of the factor per row and section."""
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as fs
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    width, height = 6.69, 5.6
    scale = fs.scale_for(width, 1.0)
    fs.style(scale)
    fig, axes = plt.subplots(1, 2, figsize=(width, height), sharey=True)
    xmin, xmax = 1e-4, 1e2
    keys = [k for k, _, _ in ROWS]
    labels = [lab for _, lab, _ in ROWS]
    kinds = [kind for _, _, kind in ROWS]
    n = len(keys)
    offsets = dict(zip(SECTIONS, (-0.27, -0.09, 0.09, 0.27)))
    colors = {s: fs.SECTION_COLORS[s.replace(" ", "")] for s in SECTIONS}
    markers = {s: fs.SECTION_MARKERS[s.replace(" ", "")] for s in SECTIONS}
    te = record["factors"]["criterion_steady_state"]
    for ax, c, panel in zip(axes, CLIMATES, ("Historical climate", "+4 K warming")):
        tmax = max(te[c].values())
        ax.axvspan(1.0 / tmax, tmax, color=fs.GRID, alpha=0.9, lw=0, zorder=0)
        ax.axvline(1.0, color=fs.BASELINE, lw=0.9, zorder=1)
        for i in range(1, n):
            if kinds[i] != kinds[i - 1]:
                ax.axhline(i - 0.5, color=fs.BASELINE, lw=0.6, zorder=1)
        for i, key in enumerate(keys):
            for s in SECTIONS:
                v = record["factors"][key][c][s]
                if v is None:
                    continue
                y = i + offsets[s]
                if v <= 0.0 or v < xmin:
                    ax.annotate(
                        "",
                        xy=(xmin * 1.05, y),
                        xytext=(xmin * 4.0, y),
                        arrowprops={
                            "arrowstyle": "-|>",
                            "color": colors[s],
                            "lw": 1.1,
                            "mutation_scale": 7 * scale,
                        },
                        zorder=3,
                    )
                    continue
                ax.plot(
                    v,
                    y,
                    linestyle="none",
                    marker=markers[s],
                    ms=4.6 * scale,
                    mfc=colors[s],
                    mec=fs.INK_2,
                    mew=0.4,
                    zorder=3,
                )
        ax.set_xscale("log")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(n - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
        ax.set_xticks([1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100])
        ax.set_xticklabels(["0.0001", "0.001", "0.01", "0.1", "1", "10", "100"])
        fs.panel_title(ax, panel, scale=scale)
        ax.set_xlabel("Factor on the annual failure probability")
    axes[0].set_yticks(range(n))
    axes[0].set_yticklabels(labels)
    axes[0].tick_params(axis="y", length=0)
    axes[1].tick_params(axis="y", length=0)
    fs.title(
        fig, "The effect of duration beside the tested input alternatives", scale=scale
    )
    handles = [
        Line2D(
            [],
            [],
            linestyle="none",
            marker=markers[s],
            mfc=colors[s],
            mec=fs.INK_2,
            mew=0.4,
            ms=4.6 * scale,
            label=s,
        )
        for s in SECTIONS
    ]
    handles.append(
        Patch(facecolor=fs.GRID, edgecolor="none", label="Size of the time effect")
    )
    fs.legend_below(fig, handles, [h.get_label() for h in handles], scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, FIGURE_NAME)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-figure", action="store_true")
    args = parser.parse_args(argv)
    record = build()
    print("wrote", write_json(record))
    for p, v in record["verdicts"].items():
        print(p, "holds" if v["holds"] else "FAILS")
    if not args.no_figure:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        print("wrote", figure(record))


if __name__ == "__main__":
    main()
