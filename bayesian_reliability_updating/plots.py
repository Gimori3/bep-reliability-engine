"""Phase 2 figures: prior-versus-posterior marginals, fragility update, replay.

Style follows the repository's validated figure conventions (fixed
per-parameter colors carried across every figure, hairline grids, despined
axes; the palette and ink constants mirror ``scripts/gsa_study.py``). All
functions render to a file via the Agg backend and return the path; no
interactive state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from bayesian_reliability_updating.analysis import column  # noqa: E402

__all__ = [
    "plot_breach_times",
    "plot_decomposition",
    "plot_fragility_update",
    "plot_observed_record",
    "plot_prior_posterior_marginals",
    "plot_rejection_scatter",
]

# Fixed per-parameter colors (repository dataviz palette; color follows the
# entity across every figure).
PARAM_COLORS = {
    "k_aq": "#2a78d6",
    "d_70": "#1baf7a",
    "D_aq": "#eda100",
    "D_bl": "#008300",
    "k_bl": "#4a3aa7",
    "gamma_bl_sub": "#e34948",
    "C_e": "#e87ba4",
    "L": "#eb6834",
}
PARAM_TEX = {
    "k_aq": r"$k_{aq}$ [m/s]",
    "d_70": r"$d_{70}$ [m]",
    "D_aq": r"$D_{aq}$ [m]",
    "D_bl": r"$D_{bl}$ [m]",
    "k_bl": r"$k_{bl}$ [m/s]",
    "gamma_bl_sub": r"$\gamma'_{bl}$ [kN/m$^3$]",
    "C_e": r"$C_e$ [-]",
    "L": r"$L$ [m]",
}
_INK = "#0b0b0b"
_INK_2 = "#52514e"
_MUTED = "#898781"
_GRID = "#e1e0d9"
_REJECT = "#e34948"
_ACCEPT = "#898781"
_PRIOR = "#52514e"
_POSTERIOR = "#2a78d6"
_POSTERIOR_STATIC = "#eda100"

_MAX_SCATTER_POINTS = 20000


def _style(ax: plt.Axes) -> None:
    ax.grid(True, axis="both", color=_GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#c3c2b7")
    ax.tick_params(colors=_MUTED, labelsize=8)


def _compact(value: float) -> str:
    """Two significant figures, in the shorter of fixed and scientific form."""
    if value == 0.0:
        return "0"
    exponent = int(np.floor(np.log10(abs(value))))
    if -2 <= exponent <= 3:
        text = f"{value:.{max(0, 1 - exponent)}f}"
        return text.rstrip("0").rstrip(".") if "." in text else text
    mantissa = f"{value / 10.0**exponent:.1f}".rstrip("0").rstrip(".")
    return rf"${mantissa}\times10^{{{exponent}}}$"


def _log_axis_ticks(ax: plt.Axes, values: NDArray[np.float64]) -> None:
    """Three in-range labels on a log abscissa, whatever the span.

    Matplotlib's default log locator labels decade minors, which collides
    illegibly on a panel spanning well under a decade (``gamma'_bl`` runs 5.5 to
    9.5) and crowds one spanning a few (``d_70``). Anchoring the ticks to the
    1st, 50th and 99th percentile of the prior always yields exactly three
    readable, in-range labels. Chrome only: no value is altered.
    """
    ticks = np.percentile(np.asarray(values, dtype=float), [1, 50, 99])
    ax.set_xticks(ticks)
    ax.set_xticklabels([_compact(float(t)) for t in ticks])
    ax.xaxis.set_minor_locator(plt.NullLocator())


def _save(
    fig: plt.Figure, path: str | Path, publication_path: str | Path | None = None
) -> Path:
    """Write the run-local copy and, when asked, the tracked publication copy.

    Both copies come from **one** ``savefig`` pair on the same figure object, so
    no manual copy step can let them diverge (``docs/conventions.md`` section
    9.3). ``publication_path=None`` (the default) is bit-identical to the
    single-write behaviour this function had before the seam was added.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    if publication_path is not None:
        publication_path = Path(publication_path)
        publication_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(publication_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_prior_posterior_marginals(
    theta: NDArray[np.float64],
    param_names: list[str],
    accept: NDArray[np.bool_],
    path: str | Path,
    *,
    title: str = "",
    publication_path: str | Path | None = None,
) -> Path:
    """All seven parameter marginals, prior versus posterior, C_e called out.

    Prior: filled ink-grey histogram. Posterior (accepted rows): stepped
    outline in the parameter's fixed color. Log-scaled abscissa for every
    parameter (all marginals are lognormal). The C_e panel carries the
    prior and posterior means as vertical lines: the laminar-conservatism
    headline of the filter.

    ``publication_path``, when given, receives a second copy of the same figure
    under tracked ``docs/figures/`` (the dual-write seam of section 9.3). The
    caller decides which runs are promoted; see
    ``pipeline.PUBLICATION_FIGURES``.
    """
    accept = np.asarray(accept, dtype=bool)
    fig, axes = plt.subplots(2, 4, figsize=(12.5, 5.8))
    axes_flat = axes.ravel()

    for k, name in enumerate(param_names):
        ax = axes_flat[k]
        _style(ax)
        values = column(theta, param_names, name)
        posterior = values[accept]
        edges = np.geomspace(values.min(), values.max(), 41)
        ax.hist(
            values,
            bins=edges,
            density=True,
            color=_PRIOR,
            alpha=0.28,
            label="prior",
        )
        if posterior.size:
            ax.hist(
                posterior,
                bins=edges,
                density=True,
                histtype="step",
                linewidth=1.8,
                color=PARAM_COLORS.get(name, _POSTERIOR),
                label="posterior",
            )
        ax.set_xscale("log")
        _log_axis_ticks(ax, values)
        ax.set_yticks([])
        emphasis = name == "C_e"
        ax.set_title(
            PARAM_TEX.get(name, name) + ("  (headline)" if emphasis else ""),
            fontsize=10 if emphasis else 9,
            color=_INK,
            fontweight="bold" if emphasis else "normal",
        )
        if emphasis and posterior.size:
            ax.axvline(values.mean(), color=_PRIOR, linewidth=1.2, linestyle="--")
            ax.axvline(
                posterior.mean(),
                color=PARAM_COLORS["C_e"],
                linewidth=1.6,
                linestyle="--",
            )

    legend_ax = axes_flat[len(param_names)]
    legend_ax.axis("off")
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=_PRIOR, alpha=0.28),
        plt.Line2D([0], [0], color=_POSTERIOR, linewidth=1.8),
    ]
    legend_ax.legend(
        handles,
        [
            f"prior (N = {theta.shape[0]:,})",
            f"posterior (N = {int(accept.sum()):,})",
        ],
        loc="center",
        frameon=False,
        fontsize=9,
    )
    if title:
        fig.suptitle(title, fontsize=11, color=_INK)
    # Without this the second row's panel titles land on the first row's tick
    # labels; invisible while the figure lived only under gitignored results/.
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, path, publication_path)


def plot_fragility_update(
    grid: NDArray[np.float64],
    prior_trans: NDArray[np.float64],
    prior_static: NDArray[np.float64],
    posterior: Any,
    path: str | Path,
    *,
    z_toe_m: float | None = None,
    event_peak_m: float | None = None,
    title: str = "",
    publication_path: str | Path | None = None,
) -> Path:
    """Prior versus posterior fragility, transient and static panels.

    Raw Monte Carlo points with the posterior Clopper-Pearson CIs and
    bootstrap bands; logarithmic probability axis. The observed event's
    peak stage is marked when given: it is the empirical constraint level.

    Parameters
    ----------
    grid : numpy.ndarray
        Conditioning stage grid [m MSL].
    prior_trans, prior_static : numpy.ndarray
        Phase 1 raw prior curves.
    posterior : PosteriorFragility
        The posterior curves object.
    path : str or pathlib.Path
        Output file.
    z_toe_m, event_peak_m : float, optional
        Landside toe and observed peak markers.
    title : str, optional
        Figure title.
    publication_path : str or pathlib.Path, optional
        Second destination for the same figure, under tracked
        ``docs/figures/`` (the dual-write seam of ``docs/conventions.md``
        section 9.3). None (default) writes only ``path``. The caller decides
        which runs are promoted; see ``pipeline.PUBLICATION_FIGURES``.
    """
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), sharey=True)
    panels = (
        (
            "Transient (Pol 2024)",
            prior_trans,
            posterior.P_f_trans_post_raw,
            posterior.binomial_ci["transient"],
            posterior.bootstrap_bands["transient"],
            _POSTERIOR,
        ),
        (
            "Static (Sellmeijer 2011)",
            prior_static,
            posterior.P_f_static_post_raw,
            posterior.binomial_ci["static"],
            posterior.bootstrap_bands["static"],
            _POSTERIOR_STATIC,
        ),
    )
    floor = 0.5 / max(posterior.n_accepted, 2)
    for ax, (label, prior, post, ci, band, color) in zip(axes, panels):
        _style(ax)
        ax.plot(
            grid,
            np.maximum(prior, floor),
            "o-",
            color=_PRIOR,
            markersize=3.5,
            linewidth=1.4,
            label="prior (Phase 1)",
        )
        lo, hi = band
        ax.fill_between(
            grid,
            np.maximum(lo, floor),
            np.maximum(hi, floor),
            color=color,
            alpha=0.15,
            lw=0,
            label="posterior bootstrap band",
        )
        ci_lo, ci_hi = ci
        post_plot = np.maximum(post, floor)
        ax.errorbar(
            grid,
            post_plot,
            yerr=(
                post_plot - np.maximum(ci_lo, floor),
                np.maximum(ci_hi, floor) - post_plot,
            ),
            fmt="s",
            color=color,
            markersize=3.5,
            linewidth=0,
            elinewidth=0.9,
            capsize=2,
            label="posterior (CP 95% CI)",
        )
        if z_toe_m is not None:
            ax.axvline(z_toe_m, color="#c3c2b7", linewidth=0.9)
            ax.annotate(
                "toe",
                (z_toe_m, floor),
                fontsize=7,
                color=_MUTED,
                rotation=90,
                xytext=(2, 4),
                textcoords="offset points",
            )
        if event_peak_m is not None:
            ax.axvline(event_peak_m, color=_REJECT, linewidth=1.1, linestyle="--")
            ax.annotate(
                "2016 peak",
                (event_peak_m, floor),
                fontsize=7,
                color=_REJECT,
                rotation=90,
                xytext=(2, 4),
                textcoords="offset points",
            )
        ax.set_yscale("log")
        ax.set_title(label, fontsize=10, color=_INK)
        ax.set_xlabel("conditioning stage $h_i$ [m MSL]", fontsize=9, color=_INK_2)
    axes[0].set_ylabel("$P_f\\,(h_i)$", fontsize=9, color=_INK_2)
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    if title:
        fig.suptitle(title, fontsize=11, color=_INK)
    return _save(fig, path, publication_path)


def plot_decomposition(
    decomposition: dict[str, Any], path: str | Path, *, title: str = ""
) -> Path:
    """The survival-discrimination two-by-two as a labelled bar chart."""
    cells = decomposition["cells"]
    order = [
        ("both_survive", "survives both", _ACCEPT),
        (
            "transient_only_reject",
            "survives static, FAILS transient\n(marginal transient information)",
            _POSTERIOR,
        ),
        ("static_only_reject", "fails static, survives transient", _POSTERIOR_STATIC),
        ("both_reject", "fails both", _REJECT),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    _style(ax)
    labels = [label for _, label, _ in order]
    fractions = [cells[key]["fraction"] for key, _, _ in order]
    colors = [color for _, _, color in order]
    bars = ax.barh(range(len(order))[::-1], fractions, color=colors, height=0.62)
    for bar, (key, _, _) in zip(bars, order):
        cell = cells[key]
        ax.annotate(
            f" {cell['fraction']:.2%}  (n = {cell['count']:,})",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            va="center",
            fontsize=8,
            color=_INK_2,
        )
    ax.set_yticks(range(len(order))[::-1])
    ax.set_yticklabels(labels, fontsize=8, color=_INK)
    ax.set_xlabel("fraction of prior realizations", fontsize=9, color=_INK_2)
    ax.set_xlim(0, 1.12)
    if title:
        ax.set_title(title, fontsize=10, color=_INK)
    return _save(fig, path)


def plot_rejection_scatter(
    theta: NDArray[np.float64],
    param_names: list[str],
    accept: NDArray[np.bool_],
    path: str | Path,
    *,
    x_name: str = "k_aq",
    y_name: str = "C_e",
    title: str = "",
    seed: int = 0,
) -> Path:
    """Accepted versus rejected rows in the C_e times k_aq plane (log-log).

    The expected rejection signature concentrates in the upper-right
    (fast-progression) corner; the plot makes the joint structure of the
    constraint visible, which the marginals alone cannot.
    """
    accept = np.asarray(accept, dtype=bool)
    x = column(theta, param_names, x_name)
    y = column(theta, param_names, y_name)
    n = x.size
    if n > _MAX_SCATTER_POINTS:
        rng = np.random.default_rng(seed)
        keep = rng.choice(n, size=_MAX_SCATTER_POINTS, replace=False)
    else:
        keep = np.arange(n)
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    _style(ax)
    accepted = keep[accept[keep]]
    rejected = keep[~accept[keep]]
    ax.scatter(
        x[accepted],
        y[accepted],
        s=3.0,
        color=_ACCEPT,
        alpha=0.25,
        linewidths=0,
        label=f"accepted (n = {int(accept.sum()):,})",
    )
    ax.scatter(
        x[rejected],
        y[rejected],
        s=4.5,
        color=_REJECT,
        alpha=0.5,
        linewidths=0,
        label=f"rejected (n = {int((~accept).sum()):,})",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(PARAM_TEX.get(x_name, x_name), fontsize=9, color=_INK_2)
    ax.set_ylabel(PARAM_TEX.get(y_name, y_name), fontsize=9, color=_INK_2)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    if title:
        ax.set_title(title, fontsize=10, color=_INK)
    return _save(fig, path)


def plot_observed_record(
    record: Any,
    path: str | Path,
    *,
    z_toe_m: float | None = None,
    trace_level_m: float | None = None,
    title: str = "",
) -> Path:
    """The constructed observed-event stage record at one section."""
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    _style(ax)
    t_days = np.asarray(record.t, dtype=np.float64) / 86400.0
    ax.plot(
        t_days,
        record.h,
        color=_POSTERIOR,
        linewidth=1.3,
        label="constructed stage h(t)",
    )
    if z_toe_m is not None:
        ax.axhline(z_toe_m, color="#c3c2b7", linewidth=1.0)
        ax.annotate(
            "landside toe",
            (t_days[0], z_toe_m),
            fontsize=7,
            color=_MUTED,
            xytext=(2, 3),
            textcoords="offset points",
        )
    if trace_level_m is not None:
        ax.axhline(trace_level_m, color=_REJECT, linewidth=1.0, linestyle="--")
        ax.annotate(
            "surveyed trace peak",
            (t_days[0], trace_level_m),
            fontsize=7,
            color=_REJECT,
            xytext=(2, 3),
            textcoords="offset points",
        )
    ax.set_xlabel("days since window start", fontsize=9, color=_INK_2)
    ax.set_ylabel("stage [m MSL]", fontsize=9, color=_INK_2)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    if title:
        ax.set_title(title, fontsize=10, color=_INK)
    return _save(fig, path)


def plot_breach_times(
    t_breach_s: NDArray[np.float64],
    record: Any,
    path: str | Path,
    *,
    title: str = "",
) -> Path:
    """When the rejected realizations breach, against the loading record."""
    finite = np.asarray(t_breach_s, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    _style(ax)
    t_days = np.asarray(record.t, dtype=np.float64) / 86400.0
    ax2 = ax.twinx()
    ax2.plot(t_days, record.h, color=_MUTED, linewidth=1.0, alpha=0.7)
    ax2.set_ylabel("stage [m MSL]", fontsize=8, color=_MUTED)
    ax2.tick_params(colors=_MUTED, labelsize=7)
    for spine in ("top",):
        ax2.spines[spine].set_visible(False)
    if finite.size:
        ax.hist(finite / 86400.0, bins=40, color=_REJECT, alpha=0.75)
    ax.set_xlabel("days since window start", fontsize=9, color=_INK_2)
    ax.set_ylabel("rejected realizations breaching", fontsize=9, color=_INK_2)
    if title:
        ax.set_title(title, fontsize=10, color=_INK)
    return _save(fig, path)
