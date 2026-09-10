"""Shared publication-figure style for this repository (no physics, no I/O of data).

Single source of truth for the palette and matplotlib rcParams used by the
figure-producing drivers under ``scripts/``. The values are the validated
light-mode reference palette used by the project; the slot **order** is the
colour-vision-deficiency safety mechanism and must not be reshuffled per figure.

House rules this module encodes (they are the ones a reviewer checks):

* fixed categorical slot order, never cycled past slot 8;
* one hue per entity — a filter that drops a series never repaints the others;
* sequential magnitude = one hue light to dark, never a rainbow;
* hairline solid grid and axes, no dashed gridlines, top/right spines off;
* **series identity comes from the legend, never from in-plot labels.** The
  legend sits below the panels, centred, unframed, in a single row where the
  entries fit. Endpoint labels duplicating a legend were removed on
  2026-09-09 at the owner's direction: they cannot show a series whose line
  is hidden under another, which is exactly the case the reader needs;
* **one title, bold, centred, at the top, sized in printed points**, and no
  figure carries a footnote or stamp block. Run conditions, estimator
  descriptions and caveats belong to the caption or the body text, which can
  be revised; text rendered into a PNG cannot. See :func:`title`,
  :func:`panel_title`, :func:`legend_below` and :func:`layout`, and
  ``docs/conventions.md`` section 9.3.2;
* text wears ink tokens, never a series colour;
* **no rendered text in a main-body figure carries an ADR number, a
  specification pointer, a module identifier, a failure-mode tag, a file-format
  name, a run identifier or an em dash.** Thirty of these figures go in the
  thesis main body, whose binding rules exclude all of them, and a caption can
  be rewritten in the thesis repository while text baked into the PNG cannot.
  Say what the figure shows, in the vocabulary of the physics. The rule and its
  substitutions are in ``docs/conventions.md`` section 9.3.1;
  :func:`section_label` is the substitution for a run identifier.

Publication copies live in ``docs/figures/`` (tracked). ``results/`` is
gitignored, so a figure that exists only there is not a deliverable —
:func:`save` therefore always writes the ``docs/figures/`` copy and optionally
mirrors it to a study-local directory.

Existing drivers written before this module (``phase3_figures.py``,
``plot_fragility_curves.py``, ``stage6_6_gap_decomposition.py``,
``gsa_study.py``, ``plot_validation_*.py``, ``bayesian_reliability_updating/
plots.py``) carry byte-identical literals inline; migrating them to import from
here is a mechanical follow-up, deliberately not bundled with the figure pass
that introduced this file.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURES = REPO_ROOT / "docs" / "figures"

# --- categorical slots (fixed order; light mode) -------------------------------
BLUE = "#2a78d6"  # slot 1
ORANGE = "#eb6834"  # slot 2
AQUA = "#1baf7a"  # slot 3
YELLOW = "#eda100"  # slot 4
MAGENTA = "#e87ba4"  # slot 5
GREEN = "#008300"  # slot 6
VIOLET = "#4a3aa7"  # slot 7
RED = "#e34948"  # slot 8

CATEGORICAL = (BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED)

#: The four production cross-sections keep one hue each, everywhere.
#: Only the first three slots validate all-pairs, so scatter-style figures with
#: all four sections rely on marker shape as the secondary channel.
SECTION_COLORS = {
    "KP57.4": BLUE,
    "KP58.8": AQUA,
    "KP60.0": YELLOW,
    "KP62.0": GREEN,
}
SECTION_MARKERS = {"KP57.4": "o", "KP58.8": "s", "KP60.0": "^", "KP62.0": "D"}

#: The two limit states, fixed for the whole thesis.
STATIC = BLUE
TRANSIENT = RED

#: The two climate scenarios, fixed for Phase 3. Deliberately **not** the
#: static/transient pair: until 2026-09-09 the Phase 3 figures painted
#: historical in ``BLUE`` and +4 K in ``RED``, so a reader who had learned
#: those two hues as the limit states in Chapter 6 met them carrying a
#: different meaning in Chapter 7, and Figure 7.4 used blue for "historical"
#: in one panel and for "KP 57.4" in the other. Violet reads cool for the
#: baseline and orange warm for the projection, and neither is a section hue.
CLIMATE_COLORS = {"historical": VIOLET, "+4K": ORANGE}

#: How the warming scenario is written in rendered figure text. The thesis
#: sets it ``$+4$\,K`` at thirty-three sites; two drivers had drifted to
#: "+4K" and "4 K warming", the second of which drops the sign altogether.
CLIMATE_LABELS = {"historical": "historical", "+4K": "+4 K"}

#: The three failure mechanisms composed in Phase 3, fixed for the whole
#: thesis. Until 2026-09-10 ``phase3_figures`` painted piping in the static
#: limit state's blue and overflow in KP 62.0's green, so both hues carried a
#: second meaning for a reader who had met them in Chapter 6, and blue carried
#: three across the document. Teal, brown and plum belong to no other series.
MECHANISM_COLORS = {
    "bep": "#006b70",  # dark teal
    "overflow": "#a85c16",  # brown
    "fluvial_scour": "#a04a86",  # plum
}

#: The secondary channel, and it is load-bearing rather than decorative: the
#: brown and the plum have almost the same relative luminance (107 against
#: 107 on a 0 to 255 scale, against the teal's 76), so a greyscale print or a
#: colour-blind reader separates overflow from scour by dash pattern and
#: marker, not by hue. A figure that draws the trio uses one of these
#: alongside the colour wherever its marks can carry one.
MECHANISM_LINESTYLES = {
    "bep": "none",  # isolated nodes, never a connecting line
    "overflow": (0, (5, 1.6)),
    "fluvial_scour": (0, (1.4, 1.4)),
}
MECHANISM_MARKERS = {"bep": "o", "overflow": "s", "fluvial_scour": "^"}

#: Rendered names for the three mechanisms.
MECHANISM_LABELS = {
    "bep": "BEP (posterior transient)",
    "overflow": "Overflow",
    "fluvial_scour": "Fluvial scour",
}

# --- sequential blue ramp (magnitude only) ------------------------------------
SEQ_BLUE = ("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95")

# --- status (reserved; never a series colour) ---------------------------------
GOOD = "#0ca30c"
WARNING = "#fab219"
SERIOUS = "#ec835a"
CRITICAL = "#d03b3b"

# --- chrome and ink -----------------------------------------------------------
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"


def section_label(cross_section_id: str) -> str:
    """Display name for a run's cross-section identifier.

    ``tokachi_kp58.8`` becomes ``KP 58.8``. A run identifier is implementation
    vocabulary, which the thesis main body excludes; the thesis names a section
    by its river kilometre throughout, and this is the single place that
    conversion lives so it cannot drift between figures.

    Parameters
    ----------
    cross_section_id
        A ``<river>_kp<chainage>`` run identifier, or any other string.

    Returns
    -------
    str
        ``KP <chainage>`` where the grammar matches, otherwise the input
        unchanged, so an unrecognised label is never silently mangled.
    """
    match = re.fullmatch(r"[A-Za-z]+_kp([0-9]+(?:\.[0-9]+)?)", cross_section_id)
    return f"KP {match.group(1)}" if match else cross_section_id


def style(scale: float | None = None) -> None:
    """Apply the house rcParams. Idempotent; call once per driver.

    Parameters
    ----------
    scale
        The figure's :func:`scale_for` factor. When given, every default type
        size is set from :data:`PRINT_PT` multiplied by it, so the figure's
        ticks, axis labels and panel titles print at the house sizes whatever
        width the figure is authored at. When omitted the pre-2026-09-09 sizes
        are kept, so a driver that has not been converted yet is unchanged.
    """
    sizes = (
        {
            "font.size": pt("tick", scale),
            "axes.titlesize": pt("panel_title", scale),
            "axes.labelsize": pt("axis_label", scale),
            "legend.fontsize": pt("legend", scale),
            "xtick.labelsize": pt("tick", scale),
            "ytick.labelsize": pt("tick", scale),
        }
        if scale is not None
        else {
            "font.size": 10.5,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
            "legend.fontsize": 9.5,
        }
    )
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": BASELINE,
            "axes.labelcolor": INK_2,
            "axes.titlecolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.linestyle": "-",
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "figure.dpi": 110,
            **sizes,
        }
    )


# --- the printed-page type scale (docs/conventions.md section 9.3.2) ----------
#: Width of the thesis text block. ``\textwidth`` is 483.69687 pt in
#: ``tudelft-report.cls``; the body is set at 10 pt.
TEXTWIDTH_IN = 483.69687 / 72.27

#: Type sizes **in points on the printed page**, not in authored points. A
#: driver multiplies these by its own :func:`scale_for` factor, so that a figure
#: authored at any width prints its title, its panel titles and its ticks at the
#: same size as every other figure in the thesis. The floor is 7 pt: the body is
#: 10 pt and a figure that is read rather than glanced at has to stay within
#: reach of its caption.
PRINT_PT = {
    "title": 11.0,
    "panel_title": 9.0,
    "axis_label": 8.5,
    "legend": 8.5,
    "tick": 8.0,
    "annotation": 8.0,
    "small": 7.0,
}


def scale_for(figure_width_in: float, textwidth_fraction: float = 1.0) -> float:
    """Authored points per printed point for a figure of this width.

    A figure authored ``figure_width_in`` wide and placed at
    ``textwidth_fraction`` of the text block is reduced by the reciprocal of the
    returned value, so every type size in it must be multiplied by that value to
    print at its intended size.

    Parameters
    ----------
    figure_width_in
        The ``figsize`` width the driver passes to matplotlib.
    textwidth_fraction
        The ``width=`` fraction of ``\\textwidth`` in the thesis
        ``\\includegraphics`` call for this figure.

    Returns
    -------
    float
        The multiplier, ``>= 1`` for any figure wider than its placement.
    """
    return figure_width_in / (textwidth_fraction * TEXTWIDTH_IN)


def pt(name: str, scale: float = 1.0) -> float:
    """One :data:`PRINT_PT` size in authored points at this figure's scale."""
    return PRINT_PT[name] * scale


def title(fig: plt.Figure, text: str, *, scale: float = 1.0, y: float | None = None):
    """The one figure title: bold, centred, at the top, in printed points.

    A title names what the figure shows. Findings, run conditions and caveats
    are the caption's work, not the title's, because a caption can be revised in
    the thesis repository and a rendered title cannot.
    """
    return fig.suptitle(
        text,
        fontsize=pt("title", scale),
        fontweight="bold",
        color=INK,
        ha="center",
        y=y if y is not None else 0.995,
        va="top",
    )


def panel_title(
    ax: plt.Axes,
    text: str,
    *,
    scale: float = 1.0,
    letter: str | None = None,
):
    """A panel title: regular weight, one step below the figure title.

    A panel that carries a letter is left-aligned so the letter starts the line;
    every other panel title is centred over its own axes.
    """
    if letter:
        return ax.set_title(
            f"{letter}  {text}",
            loc="left",
            fontsize=pt("panel_title", scale),
            color=INK,
        )
    return ax.set_title(
        text, loc="center", fontsize=pt("panel_title", scale), color=INK
    )


def legend_below(
    fig: plt.Figure,
    handles=None,
    labels=None,
    *,
    scale: float = 1.0,
    ncol: int | None = None,
    y: float = 0.0,
    **kwargs,
):
    """The figure legend, centred below the panels, unframed, one row by default.

    ``ncol`` defaults to one entry per column, which is the house single row.
    Pass an explicit ``ncol`` only where the entries genuinely will not fit.
    """
    if handles is None:
        handles, labels = fig.axes[0].get_legend_handles_labels()
    n = ncol if ncol is not None else max(1, len(labels))
    # ``upper center`` anchored at the band's top edge, so the legend hangs
    # below the anchor. :func:`layout` then moves that anchor onto the measured
    # bottom of the panels, which is what keeps the legend clear of the tick
    # labels whatever the figure's aspect ratio and entry count.
    return fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, y),
        ncol=n,
        frameon=False,
        fontsize=pt("legend", scale),
        handlelength=1.9,
        handletextpad=0.6,
        columnspacing=1.7,
        borderaxespad=0.0,
        **kwargs,
    )


def layout(
    fig: plt.Figure,
    *,
    scale: float = 1.0,
    legend_rows: int = 0,
    has_title: bool = True,
    extra_top_in: float = 0.0,
    extra_bottom_in: float = 0.0,
) -> None:
    """``tight_layout`` with the house bands reserved and nothing more.

    The band above the panels is one title height plus a half, which is the
    house gap; the band below is one legend row height per row. Reserving them
    in inches and converting to figure fractions keeps the gap identical
    whatever the figure's aspect ratio, which is what stops the title band from
    drifting from a hairline on one figure to a quarter of the canvas on
    another.
    """
    height_in = float(fig.get_size_inches()[1])
    top_in = (pt("title", scale) / 72.0) * 1.55 if has_title else 0.0
    top_in += extra_top_in
    bottom_in = legend_rows * (pt("legend", scale) / 72.0) * 2.0 + extra_bottom_in
    rect = (
        0.0,
        min(0.45, bottom_in / height_in),
        1.0,
        1.0 - min(0.45, top_in / height_in),
    )
    fig.tight_layout(rect=rect)
    if fig.legends or (has_title and fig._suptitle is not None):
        # ``tight_layout`` lays out the axes and ignores the suptitle, so a
        # fixed ``y`` leaves a band whose depth depends on whatever else sits
        # above the panels (a secondary axis, a long panel title). Measure the
        # panels once they are placed and set the gap in inches instead, which
        # is what makes the title sit the same distance above the panels on
        # every figure in the thesis.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        inv = fig.transFigure.inverted()
        boxes = [
            ax.get_tightbbox(renderer).transformed(inv)
            for ax in fig.axes
            if ax.get_visible()
        ]
        if boxes and has_title and fig._suptitle is not None:
            gap = (pt("title", scale) / 72.0) * 0.55 / height_in
            fig._suptitle.set_y(min(0.999, max(b.y1 for b in boxes) + gap))
            fig._suptitle.set_va("bottom")
        if boxes and fig.legends:
            gap = (pt("legend", scale) / 72.0) * 0.75 / height_in
            fig.legends[0].set_bbox_to_anchor(
                (0.5, min(b.y0 for b in boxes) - gap), transform=fig.transFigure
            )


def save(fig: plt.Figure, name: str, *, mirror: Path | None = None) -> Path:
    """Write ``name`` to ``docs/figures/`` and optionally mirror it.

    Parameters
    ----------
    fig
        The figure to write. Closed afterwards.
    name
        File name including the ``.png`` suffix.
    mirror
        Optional study-local directory (under gitignored ``results/``) to
        receive a byte-identical second copy, so a study keeps its evidence
        next to its data. The ``docs/figures/`` copy is the deliverable.

    Returns
    -------
    Path
        The publication copy's path.
    """
    DOCS_FIGURES.mkdir(parents=True, exist_ok=True)
    out = DOCS_FIGURES / name
    fig.savefig(out, dpi=170, bbox_inches="tight")
    if mirror is not None:
        mirror.mkdir(parents=True, exist_ok=True)
        fig.savefig(mirror / name, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out


def mark_hypothetical(
    ax: plt.Axes,
    attainable_max_m: float,
    *,
    label: bool = True,
    label_y: float = 0.03,
) -> None:
    """Shade the ADR-0024 above-crest grid extension as unattainable.

    KP 62.0's conditioning grid runs past the physically attainable maximum
    stage purely to stabilize the lognormal fit. Those levels must never be
    read as attainable, so every figure whose x axis crosses
    ``attainable_max_m`` shades and labels the region beyond it.
    """
    lo, hi = ax.get_xlim()
    if hi <= attainable_max_m:
        return
    ax.axvspan(attainable_max_m, hi, color=GRID, alpha=0.55, zorder=0, lw=0)
    ax.axvline(attainable_max_m, color=BASELINE, lw=1.0, zorder=1)
    if label:
        ax.text(
            attainable_max_m + 0.02 * (hi - lo),
            label_y,
            "hypothetical fit stabilizer\n(above the attainable stage)",
            transform=ax.get_xaxis_transform(),
            fontsize=8,
            color=MUTED,
            ha="left",
            va="top" if label_y > 0.5 else "bottom",
            # A chrome annotation may sit over marks, so it carries a surface
            # plate rather than competing with them.
            bbox={
                "facecolor": SURFACE,
                "edgecolor": "none",
                "alpha": 0.88,
                "pad": 2.0,
            },
        )
    ax.set_xlim(lo, hi)
