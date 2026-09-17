"""The ADR-0012 dependence diagnostic between aquifer conductivity and grain size.

Redraws the paired-specimen scatter that decided the two-population coupling:
laboratory conductivity against the two grain-size descriptors, on the eight OYO
specimens for which both are available on the same sample.

Until 2026-09-09 this figure had no producing script. It had been drawn
externally on 2026-07-02 by the analysis that became
``docs/decisions/adr0012-kaq-d70-analysis.md``, and the campaign registry
carried it as a declaration with the instruction to redraw it by hand. That is
what a hand-drawn figure costs: it kept matplotlib's default palette, a framed
legend, four-sided axes and axis labels that rendered code identifiers
literally, none of which match the rest of the thesis; one point label was
hidden behind the marker of the point above it, so the KP 58.8 specimen read as
"8.8/2"; two more labels crossed the right spine; and the two out-of-scope
specimens carried the same label as each other, because the convention took the
trailing index of the sample code and B-2-2 and B-3-2 both end in 2.

The eight records live in section 1 of the ADR note, transcribed there from the
gitignored 1999 OYO form-4 soil-test sheets. **The note is the data source**:
they exist nowhere else as data, so this driver reads the note's own table
rather than restating the numbers, and a correction to the note reaches the
figure on the next run.

Run from the repository root (venv active)::

    python scripts/plot_kaq_d70_scatter.py

Writes ``docs/figures/adr0012-kaq-d70-scatter.png`` and the study-local copy.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as fs  # noqa: E402

NOTE = REPO_ROOT / "docs" / "decisions" / "adr0012-kaq-d70-analysis.md"
FIGURE_NAME = "adr0012-kaq-d70-scatter.png"
MIRROR = REPO_ROOT / "results" / "figures"

#: Sections carried by the production configs. KP 63.4 is unconfined and out of
#: scope (no A_c blanket), so its two specimens are marked and excluded from the
#: regressions, exactly as the note's statistics section does.
IN_SCOPE_KP = {"57.4", "58.8", "60.0", "62.0"}
#: Below this gravel percentage the specimen characterises the sand matrix
#: rather than the gravel framework. The note's soil-type split uses 15 per cent.
SAND_GRAVEL_PERCENT = 15.0

#: The figure's authored width and its ``width=`` fraction of ``\textwidth``.
WIDTH_IN = 11.0
PLACEMENT = 1.0


@dataclass(frozen=True)
class Specimen:
    """One paired record: a grain-size distribution and a laboratory k."""

    kp: str
    sample: str
    gravel_percent: float
    d60_mm: float
    d10_mm: float
    k_mps: float

    @property
    def in_scope(self) -> bool:
        return self.kp in IN_SCOPE_KP

    @property
    def is_sand(self) -> bool:
        return self.gravel_percent < SAND_GRAVEL_PERCENT

    @property
    def label(self) -> str:
        """``KP 58.8 B-4-2``: the borehole is part of the identity.

        The old labels were ``<chainage>/<trailing index>``, which gave the two
        KP 63.4 specimens the same name. Two different points may not share a
        label, so the borehole travels with it.
        """
        return f"KP {self.kp} {self.sample}"


def read_specimens(note: Path = NOTE) -> list[Specimen]:
    """Parse the paired-specimen table out of the ADR note.

    The note is the artifact, so the table is read rather than restated. Only
    rows whose first cell is a chainage are taken, which skips the header, the
    separator and every other table in the document.
    """
    rows: list[Specimen] = []
    for line in note.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not re.fullmatch(r"\d+\.\d", cells[0]):
            continue
        try:
            rows.append(
                Specimen(
                    kp=cells[0],
                    sample=cells[1],
                    gravel_percent=float(cells[2].strip("*")),
                    d60_mm=float(cells[3].strip("*")),
                    d10_mm=float(cells[4].strip("*")),
                    k_mps=float(cells[5].strip("*")),
                )
            )
        except ValueError:
            continue
    if len(rows) != 8:
        raise SystemExit(
            f"expected the 8 paired specimens of {note.name}, parsed {len(rows)}"
        )
    return rows


def pearson_and_slope(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Pearson r and the ordinary least-squares slope of y on x."""
    r = float(np.corrcoef(x, y)[0, 1])
    slope = float(np.polyfit(x, y, 1)[0])
    return r, slope


def _panel(ax, specimens, size_key, scale, hazen_slope=None):
    """One panel: ln k against one grain-size descriptor."""
    in_scope = [s for s in specimens if s.in_scope]
    x_all = np.log(np.array([getattr(s, size_key) for s in in_scope]))
    y_all = np.log(np.array([s.k_mps for s in in_scope]))
    r, slope = pearson_and_slope(x_all, y_all)

    grid = np.linspace(x_all.min(), x_all.max(), 2)
    intercept = float(np.polyfit(x_all, y_all, 1)[1])
    ax.plot(
        grid,
        slope * grid + intercept,
        "-",
        color=fs.INK_2,
        lw=1.4,
        zorder=2,
        label="least squares on the in-scope six",
    )
    if hazen_slope is not None:
        centre_x, centre_y = float(x_all.mean()), float(y_all.mean())
        ax.plot(
            grid,
            centre_y + hazen_slope * (grid - centre_x),
            "--",
            color=fs.MUTED,
            lw=1.2,
            zorder=2,
            label=f"Hazen slope {hazen_slope:+.0f}",
        )

    styles = {
        "gravel": (fs.BLUE, "o", "gravel framework, in scope"),
        "sand": (fs.MAGENTA, "D", "sand matrix, in scope"),
        "out": (fs.MUTED, "s", "KP 63.4, out of scope"),
    }
    for spec in specimens:
        key = "out" if not spec.in_scope else ("sand" if spec.is_sand else "gravel")
        colour, marker, label = styles[key]
        ax.plot(
            np.log(getattr(spec, size_key)),
            np.log(spec.k_mps),
            marker,
            color=colour,
            ms=7,
            mec=fs.SURFACE,
            mew=0.8,
            ls="none",
            zorder=4,
            label=label,
        )
    return r, slope


def _declutter(values: list[float], min_sep: float) -> list[float]:
    """Push a column of label positions apart, keeping their order.

    One forward pass fixes every overlap in a sorted column, and the block is
    then recentred so the set does not drift toward the top of the panel.
    """
    out = list(values)
    for i in range(1, len(out)):
        if out[i] - out[i - 1] < min_sep:
            out[i] = out[i - 1] + min_sep
    shift = (sum(values) - sum(out)) / len(out)
    return [v + shift for v in out]


#: Where the label column stands, as a fraction of the panel width. The data
#: occupies the left of the panel and the labels a single column to its right.
LABEL_COLUMN_X = 0.66
#: Least vertical space between two labels, as a fraction of the panel height.
LABEL_MIN_SEP = 0.082


def _label_points(ax, specimens, size_key, scale):
    """Point labels in one decluttered column, each on its own leader.

    Two different points may never share a label and no label may sit on a
    marker: the figure this replaces did both, and its second attempt, two
    columns offset from the points themselves, failed as soon as a left-hand
    and a right-hand label met near the middle of the panel. One column at a
    fixed x cannot collide with the other, and a hairline leader carries the
    association that the offset used to carry.
    """
    xs = np.array([np.log(getattr(s, size_key)) for s in specimens])
    ys = np.array([np.log(s.k_mps) for s in specimens])
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    fx = (xs - x0) / (x1 - x0)
    fy = (ys - y0) / (y1 - y0)

    order = sorted(range(len(specimens)), key=lambda i: fy[i])
    placed = _declutter([fy[i] for i in order], LABEL_MIN_SEP)
    for i, y_label in zip(order, placed):
        ax.annotate(
            specimens[i].label,
            xy=(fx[i], fy[i]),
            xycoords="axes fraction",
            xytext=(LABEL_COLUMN_X, y_label),
            textcoords="axes fraction",
            fontsize=fs.pt("small", scale),
            color=fs.INK_2,
            ha="left",
            va="center",
            zorder=5,
            arrowprops={
                "arrowstyle": "-",
                "color": fs.BASELINE,
                "lw": 0.7,
                "shrinkA": 1.0,
                "shrinkB": 4.0,
            },
        )


def build_figure(specimens: list[Specimen]):
    """The two-panel diagnostic, house style."""
    scale = fs.scale_for(WIDTH_IN, PLACEMENT)
    fs.style(scale)
    # ``wspace`` opened at the owner's direction: the two panels stood shoulder
    # to shoulder and the right panel's labels ran into the left panel's ticks.
    fig, axes = plt.subplots(
        1, 2, figsize=(WIDTH_IN, 4.9), gridspec_kw={"wspace": 0.24}
    )

    results = {}
    for ax, key, name, descriptor, hazen in (
        # The descriptor names the percentile, not a relative size. It read
        # "median" for d60 and "fine" for d10; d60 is the 60th-percentile
        # diameter and the median is d50, which OYO reports separately. The
        # leading "Against the" was dropped with it: the percentile form is
        # nine characters longer and the two titles then met in the gutter.
        (axes[0], "d60_mm", r"$\ln\,d_{60}$  [mm]", "60th-percentile", None),
        (axes[1], "d10_mm", r"$\ln\,d_{10}$  [mm]", "10th-percentile", 2.0),
    ):
        r, slope = _panel(ax, specimens, key, scale, hazen_slope=hazen)
        results[key] = r
        ax.set_xlabel(name, fontsize=fs.pt("axis_label", scale))
        fs.panel_title(
            ax,
            f"{descriptor} diameter: r = {r:+.2f}, slope {slope:+.2f}",
            scale=scale,
        )
        # Room for the label columns on both flanks, taken before the labels
        # are placed so their axes-fraction positions are the final ones.
        lo, hi = ax.get_xlim()
        ax.set_xlim(lo - 0.10 * (hi - lo), hi + 1.05 * (hi - lo))
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo - 0.10 * (hi - lo), hi + 0.12 * (hi - lo))
        _label_points(ax, specimens, key, scale)
    axes[0].set_ylabel(
        r"$\ln\,k_\mathrm{lab}$  [m s$^{-1}$]",
        fontsize=fs.pt("axis_label", scale),
    )

    handles, labels = axes[1].get_legend_handles_labels()
    seen, keep_h, keep_l = set(), [], []
    for h, lab in zip(handles, labels):
        if lab in seen:
            continue
        seen.add(lab)
        keep_h.append(h)
        keep_l.append(lab)
    fs.legend_below(fig, keep_h, keep_l, scale=scale, ncol=3)
    fs.title(
        fig,
        "Laboratory conductivity against grain size, paired specimens",
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=2)
    return fig, results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)

    specimens = read_specimens()
    fig, results = build_figure(specimens)
    out = fs.save(fig, FIGURE_NAME, mirror=MIRROR)
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    for key, r in results.items():
        print(f"  in-scope Pearson r, ln k against ln {key[:3]}: {r:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
