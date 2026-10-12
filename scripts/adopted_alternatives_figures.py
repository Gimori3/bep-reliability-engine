"""Conductivity-bracket figures on the adopted configuration (final audit).

The two conductivity figures the thesis carries were drawn from the
posterior-side records, which update the drained sections KP 58.8 and 60.0 on
the 2016 survival as if they had neither berm nor drain. Since ADR-0056 the
adopted configuration keeps the prior there. This driver draws both figures on
the adopted configuration from committed evidence only:

* ``conductivity_bracket_annual_span_adopted.png``: annual system probability at
  the adopted conductivity and the span of the three alternative prior means;
* ``conductivity_bracket_both_d70_adopted.png``: the piping share across the
  conductivity bracket under both grain-size readings, with the first-breach
  share of ADR-0057 (``--share first_breach``, from
  ``first-breach-alternatives-study.json``) or the summed-contribution share
  (``--share summed``, from the conductivity records).

Each section is read from the side ADR-0056 adopts: the prior-side records
(``conductivity-bracket-annualisation*.json``) at KP 58.8 and 60.0, the
posterior-side records elsewhere. Gate: with ``--share first_breach`` every
cell's annual system probability in the first-breach record equals the
conductivity record's. Nothing is computed beyond that selection.

Usage (worktree root, ``PYTHONPATH=.``)::

    python scripts/adopted_alternatives_figures.py --share first_breach
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import _figstyle as fs  # noqa: E402
import conductivity_annualisation_study as cas  # noqa: E402

DECISIONS = REPO / "docs" / "decisions"
UNCONDITIONED = ("KP 58.8", "KP 60.0")
SIDES = {
    ("prior", "matrix"): DECISIONS / "conductivity-bracket-annualisation.json",
    ("prior", "bulk"): DECISIONS / "conductivity-bracket-annualisation-bulk.json",
    ("posterior", "matrix"): DECISIONS / "conductivity-bracket-posterior-side.json",
    ("posterior", "bulk"): DECISIONS / "conductivity-bracket-posterior-side-bulk.json",
}
FIRST_BREACH = DECISIONS / "first-breach-alternatives-study.json"
MIRROR = REPO / "results" / "first_breach_alternatives"
SPAN_NAME = "conductivity_bracket_annual_span_adopted.png"
BOTH_NAME = "conductivity_bracket_both_d70_adopted.png"


def adopted_payload(d70: str) -> dict[str, Any]:
    """The conductivity record with each section on its ADR-0056 side."""
    prior = json.loads(SIDES[("prior", d70)].read_text(encoding="utf-8"))
    post = json.loads(SIDES[("posterior", d70)].read_text(encoding="utf-8"))
    out = copy.deepcopy(post)
    for label in post["sections"]:
        if label in UNCONDITIONED:
            out["sections"][label] = copy.deepcopy(prior["sections"][label])
            if prior["arms"].keys() != post["arms"].keys():
                raise SystemExit("the two sides carry different arms")
    out["bep_clamped_cells"] = [
        c
        for side, d in (("prior", prior), ("posterior", post))
        for c in d.get("bep_clamped_cells", [])
        if (c["section"] in UNCONDITIONED) == (side == "prior")
    ]
    out["adopted_sides"] = {
        label: ("prior" if label in UNCONDITIONED else "posterior")
        for label in post["sections"]
    }
    return out


def with_first_breach(payload: dict[str, Any], d70: str) -> dict[str, Any]:
    """Replace every share by the first-breach share, gated on P_sys."""
    fb = json.loads(FIRST_BREACH.read_text(encoding="utf-8"))["cells"]
    base_arm = "adopted" if d70 == "matrix" else "bulk"
    prefix = "" if d70 == "matrix" else "bulk_"
    out = copy.deepcopy(payload)
    for label, by in out["sections"].items():
        for scen, entry in by.items():
            if scen not in ("historical", "+4K"):
                continue  # e.g. the climate-ratio block beside the two cells
            pairs = [(entry["baseline"], f"{base_arm} {scen} {label}")] + [
                (entry["arms"][arm], f"{prefix}{arm} {scen} {label}")
                for arm in cas.CONDUCTIVITY_ARMS
            ]
            for cell, key in pairs:
                rec = fb[key]
                want = float(cell["p_annual_system"])
                got = float(rec["p_system"])
                # The first-breach record holds six significant figures.
                if abs(got - want) > 1e-5 * max(abs(want), 1e-300):
                    raise SystemExit(f"{key}: first-breach P_sys {got} != {want}")
                cell["share_bep"] = rec["first_breach_share_bep"]
    return out


def render_span(payload: dict[str, Any]) -> Path:
    """Adopted value and the span of the three alternatives, per section."""
    width = 6.69
    scale = fs.scale_for(width, 1.0)
    fs.style(scale)
    fig, ax = plt.subplots(figsize=(width, 3.6))
    labels = [cas._label(kp) for kp in cas.BEP_KPS]
    marker = {"historical": "o", "+4K": "D"}
    name = {"historical": "historical", "+4K": "+4 K"}
    any_zero = False
    for scenario, offset in (("historical", -0.13), ("+4K", 0.13)):
        for i, label in enumerate(labels):
            entry = payload["sections"][label][scenario]
            values = [entry["baseline"]["p_annual_system"]] + [
                entry["arms"][arm]["p_annual_system"] for arm in cas.CONDUCTIVITY_ARMS
            ]
            positive = [v for v in values if v > 0.0]
            zero = len(positive) < len(values)
            plotted = [max(v, cas.DISPLAY_FLOOR) for v in positive]
            x = i + offset
            ax.plot(
                [x, x],
                [min(plotted), max(plotted)],
                color=fs.MUTED,
                lw=1.4,
                solid_capstyle="round",
                zorder=1,
            )
            ax.plot(
                [x] * len(plotted),
                plotted,
                linestyle="none",
                marker="_",
                ms=9,
                mew=1.4,
                color=fs.INK_2,
                zorder=2,
            )
            if zero:
                any_zero = True
                ax.plot(
                    [x, x],
                    [cas.DISPLAY_FLOOR, min(plotted)],
                    color=fs.CRITICAL,
                    lw=1.2,
                    linestyle=(0, (1.5, 1.5)),
                    zorder=1,
                )
                ax.plot(
                    [x],
                    [cas.DISPLAY_FLOOR],
                    linestyle="none",
                    marker="v",
                    ms=6,
                    color=fs.CRITICAL,
                    zorder=3,
                )
            ax.plot(
                [x],
                [max(values[0], cas.DISPLAY_FLOOR)],
                linestyle="none",
                marker=marker[scenario],
                ms=6.5,
                color=fs.SECTION_COLORS[label.replace(" ", "")],
                mec=fs.INK,
                mew=0.7,
                zorder=3,
            )
    ax.set_yscale("log")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(ax.get_ylim()[0], 1.0)
    ax.set_ylabel("annual system failure\nprobability [1/yr]")
    handles = [
        plt.Line2D(
            [],
            [],
            linestyle="none",
            marker=marker[s],
            ms=6.5,
            color=fs.INK_2,
            label=f"adopted value, {name[s]}",
        )
        for s in ("historical", "+4K")
    ]
    handles.append(
        plt.Line2D(
            [], [], color=fs.MUTED, lw=1.4, label="span of the three alternatives"
        )
    )
    if any_zero:
        handles.append(
            plt.Line2D(
                [],
                [],
                color=fs.CRITICAL,
                lw=1.2,
                linestyle=(0, (1.5, 1.5)),
                marker="v",
                ms=6,
                label="an alternative gives no failure",
            )
        )
    fs.title(
        fig, "Annual failure probability across the conductivity bracket", scale=scale
    )
    fs.legend_below(fig, handles, [h.get_label() for h in handles], scale=scale, ncol=2)
    fs.layout(fig, scale=scale, legend_rows=2)
    return fs.save(fig, SPAN_NAME, mirror=MIRROR / "figures")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--share", choices=("first_breach", "summed"), required=True)
    args = parser.parse_args(argv)
    pm, pb = adopted_payload("matrix"), adopted_payload("bulk")
    print("wrote", render_span(pm))
    if args.share == "first_breach":
        pm, pb = with_first_breach(pm, "matrix"), with_first_breach(pb, "bulk")
    saved = dict(cas.FIGURE_NAME)
    try:
        cas.FIGURE_NAME["bulk"] = BOTH_NAME
        print("wrote", cas.render_both_d70_figure(pb, pm, MIRROR))
    finally:
        cas.FIGURE_NAME.clear()
        cas.FIGURE_NAME.update(saved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
