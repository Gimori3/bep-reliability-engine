"""Stage 6.6 driver: static-transient gap decomposition (ADR-0040/0041).

Runs the ten-comparator ladder (``bep_reliability_engine.gap_decomposition``)
for the governing section KP62.0 and the contrast section KP57.4 (matrix d70
primary), verifies C0/C4b bit-identity against the persisted production
sweeps, runs the sustained-duration verification ladder and the bulk-d70
sensitivity, computes the paired-bootstrap component tables, and renders the
analysis figures. Everything is persisted under ``results/stage6_6/``; every
number in ``docs/stage6_6_report.md`` traces to a file written here. Figures are
written to ``results/stage6_6/figures/`` **and** to the tracked
``docs/figures/`` in the same call -- never copy one by hand.

Usage (from the repo root, venv active)::

    python scripts/stage6_6_gap_decomposition.py                 # everything
    python scripts/stage6_6_gap_decomposition.py --n 10000       # pilot
    python scripts/stage6_6_gap_decomposition.py --skip-run      # re-analyze
    python scripts/stage6_6_gap_decomposition.py --figures-only   # redraw only
    python scripts/stage6_6_gap_decomposition.py --sections kp62_0

Phases (each skippable): run -> verify -> analyze -> duration ladder ->
bulk sensitivity -> figures.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402
from bep_reliability_engine.gap_decomposition import (  # noqa: E402
    ALPHA_3D,
    ENGINE_LADDER_STEPS,
    PHYSICS_LADDER_STEPS,
    GapDecompositionResult,
    bootstrap_comparator_means,
    component_table,
    prepare_config,
    run_comparator_ladder,
    static_pair_shapley,
    sustained_duration_ladder,
)

OUT_DIR = REPO_ROOT / "results" / "stage6_6"
FIG_DIR = OUT_DIR / "figures"
#: Tracked publication copy. ``results/`` is gitignored, so a figure that lives
#: only there is not a deliverable; writing both copies in one call removes the
#: manual copy step that let the KP 62.0 figures go stale twice (2026-07-29,
#: 2026-07-30). Never copy by hand -- re-run the driver.
PUB_FIG_DIR = REPO_ROOT / "docs" / "figures"


def _write_figure(fig, fig_dir: Path, name: str) -> Path:
    """Write the study-local copy and the tracked publication copy together."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    PUB_FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = fig_dir / name
    fig.savefig(path, dpi=170, facecolor=SURFACE)
    fig.savefig(PUB_FIG_DIR / name, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return path


# Section registry (ADR-0040): matrix d70 is the primary decomposition run;
# attainable_max_m is the last non-hypothetical grid level (ADR-0024: the
# KP62.0 levels >= 51.0 are static-bracketing fit-stabilizers, never
# attainable stages).
SECTIONS: dict[str, dict] = {
    "kp62_0": {
        "config": "configs/kp62_0_historical_matrix.yaml",
        "bulk_config": "configs/kp62_0_historical_bulk.yaml",
        "production_h5": "results/tokachi_kp62.0_historical_matrix.h5",
        "attainable_max_m": 50.5,
        "label": "KP62.0",
    },
    "kp57_4": {
        "config": "configs/kp57_4_historical_matrix.yaml",
        "bulk_config": "configs/kp57_4_historical_bulk.yaml",
        "production_h5": "results/tokachi_kp57.4_historical_matrix.h5",
        "attainable_max_m": 43.25,
        "label": "KP57.4",
    },
}

# Fixed comparator -> color assignment (dataviz: color follows the entity,
# fixed categorical order, light-mode palette).
COLORS = {
    "C0": "#2a78d6",  # blue
    "C0b": "#86b6ef",  # light blue (lattice sibling of C0)
    "C1": "#1baf7a",  # aqua
    "C2": "#eda100",  # yellow
    "C3a": "#4a3aa7",  # violet
    "C3b": "#4a3aa7",
    "C4a": "#e34948",  # red
    "C4b": "#e34948",
    "C4c": "#eb6834",  # orange (end-factor bound)
    "C4d": "#eb6834",
}
INK = "#0b0b0b"
MUTED = "#898781"
GRID_COLOR = "#e1e0d9"
SURFACE = "#fcfcfb"
NEUTRAL = "#c3c2b7"

PF_FLOOR = 1e-6  # display floor for log-scale fragility axes


def _apply_style(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, which="major", color=GRID_COLOR, linewidth=0.7)
    ax.tick_params(colors=MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(NEUTRAL)


def run_section(
    key: str, *, n_samples: int | None, n_jobs: int, out_dir: Path, suffix: str = ""
) -> GapDecompositionResult:
    """Run and persist the comparator ladder for one section."""
    spec = SECTIONS[key]
    config_path = spec["bulk_config"] if suffix == "_bulk" else spec["config"]
    config = Config.from_yaml(REPO_ROOT / config_path)
    hwl = float(config.geometry.HWL)
    config_run = prepare_config(config, n_samples=n_samples, extra_levels=(hwl,))
    print(
        f"[{key}{suffix}] ladder: N={config_run.mc.n_samples}, "
        f"{len(config_run.mc.conditioning_grid)} levels (HWL {hwl} inserted), "
        f"n_jobs={n_jobs}"
    )
    started = time.time()
    result = run_comparator_ladder(config_run, n_jobs=n_jobs, progress=True)
    result.metadata["hwl_m"] = hwl
    result.metadata["attainable_max_m"] = spec["attainable_max_m"]
    result.metadata["section_key"] = key + suffix
    result.metadata["base_config_hash"] = config.config_hash()
    path = out_dir / f"stage6_6_{key}{suffix}.h5"
    result.save(path)
    print(f"[{key}{suffix}] done in {time.time() - started:.0f} s -> {path}")
    return result


def verify_against_production(key: str, result: GapDecompositionResult) -> dict:
    """ADR-0040 gate (i): C0/C4b bit-identical to the persisted production sweep."""
    spec = SECTIONS[key]
    prod_path = REPO_ROOT / spec["production_h5"]
    record: dict = {"production_file": spec["production_h5"]}
    if not prod_path.exists():
        record["status"] = "skipped_missing_production_file"
        return record
    production = FragilityResult.load(prod_path)
    prod_hash = production.metadata.get("config_hash")
    if prod_hash != result.metadata.get("base_config_hash"):
        # The generated YAMLs gained the (inert, enabled: false) ADR-0037
        # length_effect block after the production sweeps ran, so the raw
        # hashes differ while the physics inputs are identical. Compare the
        # config snapshots with that key excluded; any OTHER difference is a
        # real mismatch and skips the bit-check.
        prod_cfg = json.loads(json.dumps(production.metadata.get("config", {})))
        run_cfg = json.loads(json.dumps(result.metadata.get("config", {})))
        prod_cfg.pop("length_effect", None)
        run_cfg.pop("length_effect", None)
        # The run grid legitimately carries the inserted HWL level; drop the
        # grid from the identity comparison (levels are matched individually
        # below) alongside length_effect.
        for cfg in (prod_cfg, run_cfg):
            cfg.get("mc", {}).pop("conditioning_grid", None)
        if prod_cfg != run_cfg:
            record["status"] = "skipped_config_mismatch_beyond_length_effect"
            record["production_config_hash"] = prod_hash
            return record
        record["hash_note"] = (
            "raw config hashes differ only by the post-sweep ADR-0037 "
            "length_effect block (enabled: false, physics-inert)"
        )
    if production.theta_matrix.shape[0] != result.n_samples:
        record["status"] = "skipped_n_mismatch"
        return record
    np.testing.assert_array_equal(production.theta_matrix, result.theta_matrix)
    prod_grid = np.asarray(production.conditioning_grid, dtype=np.float64)
    checked = 0
    for j, level in enumerate(prod_grid):
        matches = np.flatnonzero(np.isclose(result.conditioning_grid, level))
        if matches.size != 1:
            continue
        i = int(matches[0])
        np.testing.assert_array_equal(
            production.failure_matrix_stat[:, j], result.comparators["C0"][:, i]
        )
        np.testing.assert_array_equal(
            production.failure_matrix_tran[:, j], result.comparators["C4b"][:, i]
        )
        checked += 1
    record["status"] = "bit_identical"
    record["levels_checked"] = checked
    record["theta_identical"] = True
    print(f"[{key}] production drift-guard: bit-identical at {checked} levels")
    return record


def analyze_section(
    key: str,
    result: GapDecompositionResult,
    *,
    n_bootstrap: int,
    out_dir: Path,
    suffix: str = "",
) -> dict:
    """Bootstrap + component tables + shapley -> analysis JSON."""
    boot = bootstrap_comparator_means(result, n_replicates=n_bootstrap)
    analysis = {
        "section": key + suffix,
        "n_samples": result.n_samples,
        "n_bootstrap": n_bootstrap,
        "hwl_m": result.metadata.get("hwl_m"),
        "attainable_max_m": result.metadata.get("attainable_max_m"),
        "p_f": {k: v.tolist() for k, v in result.p_f().items()},
        "binomial_ci": {
            k: [lo.tolist(), hi.tolist()]
            for k, (lo, hi) in result.binomial_cis().items()
        },
        "flip_counts": {k: v.tolist() for k, v in result.flip_counts.items()},
        "components": component_table(result, boot),
        "static_pair_shapley": static_pair_shapley(result, boot),
    }
    path = out_dir / f"stage6_6_{key}{suffix}_analysis.json"
    path.write_text(json.dumps(analysis, indent=2))
    print(f"[{key}{suffix}] analysis -> {path}")
    return analysis


def pick_ladder_levels(result: GapDecompositionResult) -> tuple[float, ...]:
    """Choose three verification levels where the analytic C3a is informative."""
    p_c3a = result.p_f()["C3a"]
    grid = result.conditioning_grid
    levels: list[float] = []
    for target in (0.02, 0.2, 0.6):
        candidates = np.flatnonzero(p_c3a > 0.0)
        if candidates.size == 0:
            break
        idx = candidates[np.argmin(np.abs(p_c3a[candidates] - target))]
        level = float(grid[idx])
        if level not in levels:
            levels.append(level)
    if not levels:
        levels = [float(x) for x in grid[-3:]]
    return tuple(levels)


def run_duration_ladders(
    key: str,
    result: GapDecompositionResult,
    *,
    n_pilot: int,
    n_jobs: int,
    out_dir: Path,
) -> dict:
    """The ADR-0040 Decision 2 finite-hold verification, both alpha variants."""
    spec = SECTIONS[key]
    config = Config.from_yaml(REPO_ROOT / spec["config"])
    hwl = float(config.geometry.HWL)
    config_pilot = prepare_config(config, n_samples=n_pilot, extra_levels=(hwl,))
    levels = pick_ladder_levels(result)
    print(f"[{key}] duration ladder at levels {levels}, N={n_pilot}")
    out = {
        "levels_m": list(levels),
        "alpha_minus_half": sustained_duration_ladder(
            config_pilot,
            levels_m=levels,
            alpha_exponent_transient=ALPHA_3D,
            n_jobs=n_jobs,
        ),
        "alpha_baseline": sustained_duration_ladder(
            config_pilot,
            levels_m=levels[-1:],
            n_jobs=n_jobs,
        ),
    }
    path = out_dir / f"stage6_6_{key}_duration_ladder.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"[{key}] duration ladder -> {path}")
    return out


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def _plot_curve_with_ci(ax, grid, p, ci, color, label, linestyle="-") -> None:
    p_plot = np.clip(p, PF_FLOOR, None)
    ax.plot(grid, p_plot, color=color, linewidth=2.0, label=label, ls=linestyle)
    # CP bands only where the point estimate is nonzero: a k = 0 level's
    # upper bound would otherwise paint a large box over the sub-transition
    # region (the zero-count levels are carried by the curve floor itself).
    active = np.asarray(p) > 0.0
    lo = np.clip(np.where(active, ci[0], np.nan), PF_FLOOR, None)
    hi = np.clip(np.where(active, ci[1], np.nan), PF_FLOOR, None)
    ax.fill_between(grid, lo, hi, color=color, alpha=0.15, linewidth=0)


def figure_ladder(key: str, result: GapDecompositionResult, fig_dir: Path) -> Path:
    """Five-comparator fragility ladder, physics and engine panels."""
    spec = SECTIONS[key]
    grid = result.conditioning_grid
    p_f = result.p_f()
    cis = result.binomial_cis()
    hwl = result.metadata.get("hwl_m")
    attainable = result.metadata.get("attainable_max_m")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    panels = (
        ("Physics ladder (endpoint alpha = -1/2)", ("C0", "C1", "C2", "C3a", "C4a")),
        ("Engine ladder (production, alpha = -1/3)", ("C0", "C1", "C3b", "C4b")),
    )
    for ax, (title, ids) in zip(axes, panels):
        _apply_style(ax)
        for comp in ids:
            style = "--" if comp.startswith("C3") else "-"
            _plot_curve_with_ci(
                ax, grid, p_f[comp], cis[comp], COLORS[comp], comp, style
            )
        ax.set_yscale("log")
        ax.set_ylim(PF_FLOOR, 1.5)
        ax.set_xlabel("conditioning stage [m MSL]", color=MUTED, fontsize=9)
        ax.set_title(f"{spec['label']}  {title}", color=INK, fontsize=10)
        if hwl is not None:
            ax.axvline(hwl, color=MUTED, linewidth=0.9, ls=":")
            ax.text(
                hwl,
                0.03,
                " HWL",
                color=MUTED,
                fontsize=8,
                ha="left",
                transform=ax.get_xaxis_transform(),
            )
        if attainable is not None and attainable < grid[-1]:
            ax.axvspan(attainable, grid[-1], color=GRID_COLOR, alpha=0.45, zorder=0)
            ax.text(
                0.5 * (attainable + grid[-1]),
                0.40,
                "hypothetical\n(ADR-0024)",
                color=MUTED,
                fontsize=7,
                ha="center",
                transform=ax.get_xaxis_transform(),
            )
        ax.legend(fontsize=8, framealpha=0.9, loc="lower right")
    axes[0].set_ylabel("P_f per event (raw, CP 95% bands)", color=MUTED, fontsize=9)
    fig.tight_layout()
    return _write_figure(fig, fig_dir, f"stage6_6_ladder_{key}.png")


def _waterfall(ax, names, deltas, cis, start_value, start_name, end_name) -> None:
    """Floating-bar waterfall: start total, component drops, end total."""
    positions = np.arange(len(names) + 2)
    running = start_value
    ax.bar(0, start_value, color=NEUTRAL, edgecolor="none", width=0.62, zorder=3)
    for i, (name, delta, ci) in enumerate(zip(names, deltas, cis), start=1):
        color = "#2a78d6" if delta >= 0 else "#e34948"
        ax.bar(
            i,
            abs(delta),
            bottom=min(running, running - delta),
            color=color,
            edgecolor="none",
            width=0.62,
            zorder=3,
        )
        err_center = running - delta
        ax.errorbar(
            i,
            err_center,
            yerr=[
                [max(0.0, err_center - (running - ci[1]))],
                [max(0.0, (running - ci[0]) - err_center)],
            ],
            color=INK,
            linewidth=1.0,
            capsize=3,
            zorder=4,
        )
        running = running - delta
    ax.bar(
        len(names) + 1, running, color=NEUTRAL, edgecolor="none", width=0.62, zorder=3
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [start_name, *names, end_name], rotation=25, ha="right", fontsize=8
    )


def figure_waterfall(
    key: str, result: GapDecompositionResult, analysis: dict, fig_dir: Path
) -> Path:
    """Waterfall of the gap decomposition at HWL and the top attainable level."""
    spec = SECTIONS[key]
    grid = result.conditioning_grid
    hwl = float(result.metadata["hwl_m"])
    attainable = float(result.metadata["attainable_max_m"])
    levels = [("design flood (HWL)", hwl), ("top attainable level", attainable)]
    ladders = (
        ("physics", PHYSICS_LADDER_STEPS, "C4a"),
        ("engine", ENGINE_LADDER_STEPS, "C4b"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.6))
    fig.patch.set_facecolor(SURFACE)
    p_f = result.p_f()
    comp = analysis["components"]
    for row, (ladder_name, steps, endpoint) in enumerate(ladders):
        for col, (level_label, level) in enumerate(levels):
            ax = axes[row][col]
            _apply_style(ax)
            i = int(np.argmin(np.abs(grid - level)))
            names = [s[0] for s in steps]
            deltas = [
                comp["ladders"][ladder_name]["steps"][n]["delta"][i] for n in names
            ]
            cis = [
                (
                    comp["ladders"][ladder_name]["steps"][n]["ci"][0][i],
                    comp["ladders"][ladder_name]["steps"][n]["ci"][1][i],
                )
                for n in names
            ]
            _waterfall(
                ax, names, deltas, cis, float(p_f["C0"][i]), "C0 (static)", endpoint
            )
            ax.set_title(
                f"{spec['label']}  {ladder_name} ladder at {level_label} "
                f"({grid[i]:.2f} m MSL)",
                color=INK,
                fontsize=9,
            )
            ax.set_ylabel("P_f per event", color=MUTED, fontsize=8)
    fig.tight_layout()
    return _write_figure(fig, fig_dir, f"stage6_6_waterfall_{key}.png")


def figure_fractions(
    key: str, result: GapDecompositionResult, analysis: dict, fig_dir: Path
) -> Path:
    """Component share of the total gap as a function of conditioning level."""
    spec = SECTIONS[key]
    grid = result.conditioning_grid
    comp = analysis["components"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    step_colors = {
        "head_convention": "#1baf7a",
        "dimensional": "#eda100",
        "initiation_gate": "#4a3aa7",
        "temporal_net": "#e34948",
    }
    for ax, ladder_name in zip(axes, ("physics", "engine")):
        _apply_style(ax)
        ladder = comp["ladders"][ladder_name]
        for name, block in ladder["steps"].items():
            fraction = np.asarray(block["fraction_of_total"], dtype=float)
            ax.plot(
                grid,
                fraction,
                color=step_colors[name],
                linewidth=2.0,
                label=name.replace("_", " "),
            )
        ax.axhline(0.0, color=NEUTRAL, linewidth=0.9)
        ax.axhline(1.0, color=GRID_COLOR, linewidth=0.9)
        ax.set_ylim(-1.0, 2.0)
        ax.set_xlabel("conditioning stage [m MSL]", color=MUTED, fontsize=9)
        ax.set_title(
            f"{spec['label']}  {ladder_name} ladder component shares",
            color=INK,
            fontsize=10,
        )
        ax.legend(fontsize=8, framealpha=0.9)
    axes[0].set_ylabel(
        "component share of total gap (where resolved)", color=MUTED, fontsize=9
    )
    fig.tight_layout()
    return _write_figure(fig, fig_dir, f"stage6_6_fractions_{key}.png")


def figure_c2c3(
    key: str,
    result: GapDecompositionResult,
    ladder_json: dict | None,
    fig_dir: Path,
) -> Path:
    """C2/C3 consistency overlay: nesting, gate-blocked share, ODE convergence."""
    spec = SECTIONS[key]
    grid = result.conditioning_grid
    p_f = result.p_f()
    cis = result.binomial_cis()
    c2_only = np.mean(result.comparators["C2"] & ~result.comparators["C3a"], axis=0)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(7.2, 6.4), sharex=True, height_ratios=[2.2, 1.0]
    )
    fig.patch.set_facecolor(SURFACE)
    _apply_style(ax1)
    _apply_style(ax2)
    _plot_curve_with_ci(
        ax1, grid, p_f["C2"], cis["C2"], COLORS["C2"], "C2 static crack-reduced 3D"
    )
    _plot_curve_with_ci(
        ax1,
        grid,
        p_f["C3a"],
        cis["C3a"],
        COLORS["C3a"],
        "C3a sustained-peak analytic limit",
        "--",
    )
    ax1.set_yscale("log")
    ax1.set_ylim(PF_FLOOR, 1.5)
    ax1.set_ylabel("P_f per event", color=MUTED, fontsize=9)
    ax1.set_title(
        f"{spec['label']}  C2 vs C3a: exact nesting, gap = initiation gate",
        color=INK,
        fontsize=10,
    )
    ax1.legend(fontsize=8, framealpha=0.9, loc="lower right")

    ax2.plot(grid, c2_only, color="#4a3aa7", linewidth=2.0)
    ax2.set_ylabel("gate-blocked fraction\nP(C2 and not C3a)", color=MUTED, fontsize=8)
    ax2.set_xlabel("conditioning stage [m MSL]", color=MUTED, fontsize=9)

    if ladder_json is not None:
        rows = ladder_json["alpha_minus_half"]["rows"]
        top_level = max(r["level_m"] for r in rows)
        subset = [r for r in rows if r["level_m"] == top_level]
        text = "ODE hold-ladder vs analytic (level {:.2f}):\n".format(top_level)
        text += "\n".join(
            "{:>5.0f} h: missing {:d}, excess {:d}".format(
                r["hours"], r["analytic_not_ode"], r["ode_not_analytic"]
            )
            for r in subset
        )
        ax1.text(
            0.02,
            0.97,
            text,
            transform=ax1.transAxes,
            fontsize=7,
            va="top",
            color=INK,
            bbox=dict(facecolor=SURFACE, edgecolor=GRID_COLOR),
        )
    fig.tight_layout()
    return _write_figure(fig, fig_dir, f"stage6_6_c2c3_{key}.png")


def figure_heq_bound(
    key: str, result: GapDecompositionResult, analysis: dict, fig_dir: Path
) -> Path:
    """The ADR-0041 H_eq-conservatism indicator bound per level."""
    spec = SECTIONS[key]
    grid = result.conditioning_grid
    comp = analysis["components"]["auxiliary"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    fig.patch.set_facecolor(SURFACE)
    _apply_style(ax)
    for name, color, label in (
        ("heq_conservatism_engine", "#e34948", "alpha = -1/3 (C4b - C4c)"),
        ("heq_conservatism_physics", "#eb6834", "alpha = -1/2 (C4a - C4d)"),
    ):
        block = comp[name]
        delta = np.asarray(block["delta"], dtype=float)
        lo = np.asarray(block["ci"][0], dtype=float)
        hi = np.asarray(block["ci"][1], dtype=float)
        ax.plot(grid, delta, color=color, linewidth=2.0, label=label)
        ax.fill_between(grid, lo, hi, color=color, alpha=0.15, linewidth=0)
    ax.axhline(0.0, color=NEUTRAL, linewidth=0.9)
    ax.set_xlabel("conditioning stage [m MSL]", color=MUTED, fontsize=9)
    ax.set_ylabel("Delta P_f from the 0.9 H_c end anchor", color=MUTED, fontsize=9)
    ax.set_title(
        f"{spec['label']}  H_eq-conservatism bound (ADR-0009/0041)",
        color=INK,
        fontsize=10,
    )
    ax.legend(fontsize=8, framealpha=0.9)
    fig.tight_layout()
    return _write_figure(fig, fig_dir, f"stage6_6_heq_{key}.png")


def _redraw_only(sections: list[str]) -> int:
    """Redraw every figure from persisted evidence -- no physics, no rewrites.

    This is the path that keeps the tracked ``docs/figures/`` copies honest
    without a 25-minute ladder re-run per section, and it is deliberately
    read-only with respect to every evidence file: a redraw can never move a
    number.
    """
    drawn = 0
    for key in sections:
        h5_path = OUT_DIR / f"stage6_6_{key}.h5"
        analysis_path = OUT_DIR / f"stage6_6_{key}_analysis.json"
        if not (h5_path.exists() and analysis_path.exists()):
            print(f"[{key}] SKIPPED -- persisted evidence missing ({h5_path.name})")
            continue
        result = GapDecompositionResult.load(h5_path)
        analysis = json.loads(analysis_path.read_text())
        ladder_path = OUT_DIR / f"stage6_6_{key}_duration_ladder.json"
        ladder_json = (
            json.loads(ladder_path.read_text()) if ladder_path.exists() else None
        )
        for path in (
            figure_ladder(key, result, FIG_DIR),
            figure_waterfall(key, result, analysis, FIG_DIR),
            figure_fractions(key, result, analysis, FIG_DIR),
            figure_c2c3(key, result, ladder_json, FIG_DIR),
            figure_heq_bound(key, result, analysis, FIG_DIR),
        ):
            print(f"  {path.relative_to(REPO_ROOT)} (+ docs/figures/{path.name})")
            drawn += 1
    print(f"redrew {drawn} figures; no evidence file touched")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sections", nargs="+", default=list(SECTIONS))
    parser.add_argument("--n", type=int, default=None, help="override N (pilot)")
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--n-pilot", type=int, default=10_000)
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--skip-ladder", action="store_true")
    parser.add_argument("--skip-bulk", action="store_true")
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help=(
            "redraw the figures from the persisted ladder, analysis and "
            "duration-ladder JSONs; runs no physics, re-analyses nothing and "
            "rewrites no evidence file"
        ),
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.figures_only:
        return _redraw_only(args.sections)

    # The summary is MERGED, never rebuilt: --sections is a filter, and a
    # partial re-run must not silently delete the other section's entry (the
    # campaign's G3 gate asserts both sections are present).
    summary_path = OUT_DIR / "stage6_6_summary.json"
    summary: dict = {"sections": {}}
    if summary_path.exists():
        try:
            previous = json.loads(summary_path.read_text())
        except json.JSONDecodeError:
            previous = {}
        if isinstance(previous.get("sections"), dict):
            summary["sections"].update(previous["sections"])

    for key in args.sections:
        section_summary: dict = {}
        h5_path = OUT_DIR / f"stage6_6_{key}.h5"
        if args.skip_run and h5_path.exists():
            result = GapDecompositionResult.load(h5_path)
            print(f"[{key}] loaded persisted ladder ({result.n_samples} rows)")
        else:
            result = run_section(
                key, n_samples=args.n, n_jobs=args.n_jobs, out_dir=OUT_DIR
            )
        if args.n is None:
            section_summary["production_verification"] = verify_against_production(
                key, result
            )
        analysis = analyze_section(
            key, result, n_bootstrap=args.bootstrap, out_dir=OUT_DIR
        )
        section_summary["flip_totals"] = {
            k: int(v.sum()) for k, v in result.flip_counts.items()
        }

        ladder_json = None
        ladder_path = OUT_DIR / f"stage6_6_{key}_duration_ladder.json"
        if not args.skip_ladder:
            ladder_json = run_duration_ladders(
                key, result, n_pilot=args.n_pilot, n_jobs=args.n_jobs, out_dir=OUT_DIR
            )
        elif ladder_path.exists():
            ladder_json = json.loads(ladder_path.read_text())

        if not args.skip_bulk:
            bulk_result = run_section(
                key,
                n_samples=args.n_pilot,
                n_jobs=args.n_jobs,
                out_dir=OUT_DIR,
                suffix="_bulk",
            )
            analyze_section(
                key,
                bulk_result,
                n_bootstrap=max(200, args.bootstrap // 5),
                out_dir=OUT_DIR,
                suffix="_bulk",
            )

        if not args.skip_figures:
            figs = [
                figure_ladder(key, result, FIG_DIR),
                figure_waterfall(key, result, analysis, FIG_DIR),
                figure_fractions(key, result, analysis, FIG_DIR),
                figure_c2c3(key, result, ladder_json, FIG_DIR),
                figure_heq_bound(key, result, analysis, FIG_DIR),
            ]
            section_summary["figures"] = [str(p.relative_to(REPO_ROOT)) for p in figs]
            print(f"[{key}] figures: {len(figs)} written")
        summary["sections"][key] = section_summary

    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
