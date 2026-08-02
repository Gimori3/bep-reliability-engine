"""Shared publication-figure style for this repository (no physics, no I/O of data).

Single source of truth for the palette and matplotlib rcParams used by the
figure-producing drivers under ``scripts/``. The values are the validated
light-mode reference palette of the ``dataviz`` guide; the slot **order** is the
colour-vision-deficiency safety mechanism and must not be reshuffled per figure.

House rules this module encodes (they are the ones a reviewer checks):

* fixed categorical slot order, never cycled past slot 8;
* one hue per entity — a filter that drops a series never repaints the others;
* sequential magnitude = one hue light to dark, never a rainbow;
* hairline solid grid and axes, no dashed gridlines, top/right spines off;
* a legend whenever two or more series are drawn, direct labels used
  *selectively* (endpoint / extreme / the one series that matters);
* text wears ink tokens, never a series colour;
* **a rendered title carries no ADR number and no statement about the project's
  own evolution.** Thirty of these figures go in the thesis main body, whose
  binding rules exclude both, and a caption can be rewritten in the thesis
  repository while text baked into the PNG cannot. Say what the figure shows, in
  the vocabulary of the physics. Three titles still violate this and are listed
  with their fix in ``docs/conventions.md`` section 9.3.1; the worst of them also
  asserts a fact the repository's own record now contradicts.

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


def style() -> None:
    """Apply the house rcParams. Idempotent; call once per driver."""
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
            "font.size": 10.5,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
            "legend.fontsize": 9.5,
            "figure.dpi": 110,
        }
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
    stage purely to stabilise the lognormal fit. Those levels must never be
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
            "hypothetical fit stabiliser\n(ADR-0024; not attainable)",
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
