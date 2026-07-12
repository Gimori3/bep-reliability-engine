"""Stage 6.5 global sensitivity analysis of the Phase 1 engine (ADR-0033).

Variance-based Sobol' indices (first-order S_i, total-effect ST_i) of the
eight-dimensional production input space (the seven theta parameters plus the
stochastic seepage length L) for four scalar QoIs per conditioning level:

* ``trans_indicator``  — 1{Z_transient <= 0}  (Y1, the primary reliability QoI)
* ``static_indicator`` — 1{Z_static <= 0}     (Y2, the comparator; the Y1-Y2
  contrast is the bias attribution)
* ``l_fraction``       — l_e,final / L        (Y3, progression dynamics)
* ``z_static``         — H_c - (h_i - z_toe)  (Y4, pure Sellmeijer resistance)

Method (ADR-0033): scrambled-Sobol' radial design (Saltelli et al. 2010,
cost N*(k+2) per replicate), Saltelli-2010 S_i + Jansen ST_i estimators,
R independent Owen scramblings for the primary (Student-t) CIs, row-bootstrap
(Primer p. 166) as the cross-check CI, and an N-ladder for the convergence
demonstration. The engine enters through ``gsa_qoi.evaluate_qoi_batch``
(bit-identical failure flags to M8's ``evaluate_batch``; drift-guarded).

Run from the repository root (venv active)::

    python scripts/gsa_study.py                  # full study: KP58.8 + KP60.0
                                                 #   + companions (bulk d70,
                                                 #   Nataf rho=0.6 both anchors)
    python scripts/gsa_study.py --config kp60_0_historical_matrix.yaml \
        --levels 42.00,42.75,43.25,44.25         # one section
    python scripts/gsa_study.py --skip-companions
    python scripts/gsa_study.py --plot-only      # redraw figures from JSONs

Outputs (repo convention: working copies under ``results/gsa/``, tracked
copies under ``docs/decisions`` / ``docs/figures``):

* ``results/gsa/<slug>_gsa.json``                    — per-section record
* ``results/gsa/kp58_8_matrix_companions_gsa.json``  — companion record
* figures ``gsa_indices_<slug>.png``, ``gsa_levels_<slug>.png``,
  ``gsa_convergence_<slug>.png``, ``gsa_companions.png``

The scenario axis: per ADR-0023 the canonical shape is scenario-invariant, so
a "+4K GSA" at matched level is definitionally identical to the historical
one; the driver *verifies* this bit-identity once per section and records it
instead of running a redundant sweep (ADR-0033 §6).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.gsa_qoi import evaluate_qoi_batch  # noqa: E402
from bep_reliability_engine.hydrographs import (  # noqa: E402
    conditioning_record_for_level,
    resample_record,
)
from bep_reliability_engine.run import (  # noqa: E402
    _hydrograph_for_level,
    _load_canonical_or_none,
)
from bep_reliability_engine.sensitivity import (  # noqa: E402
    GsaInputSpace,
    aggregate_replicates,
    bootstrap_indices,
    generate_design,
    sobol_indices,
    split_outputs,
    stack_evaluation_matrix,
)

# ---------------------------------------------------------------------------
# Study configuration (ADR-0033 §3, §7)
# ---------------------------------------------------------------------------
DEFAULT_SECTIONS: dict[str, list[float]] = {
    # Conditioning levels per section: shoulder / design HWL / transition /
    # upper, read off each section's production fragility curve (ADR-0033 §1).
    "kp58_8_historical_matrix.yaml": [40.25, 41.00, 41.50, 42.50],
    "kp60_0_historical_matrix.yaml": [42.00, 42.75, 43.25, 44.25],
}
# Design levels (the HWL grid point) for the companion runs.
DESIGN_LEVEL = {"kp58_8": 41.00, "kp60_0": 42.75}

DEFAULT_N_LADDER = [1024, 2048, 4096, 8192]
DEFAULT_REPLICATES = 25
DEFAULT_N_BOOT = 500
CONFIDENCE = 0.95
BACKEND = "numba"
RHO_COMPANION = 0.6  # the retired pre-ADR-0012 provisional value (bounding)

QOI_KEYS = ["trans_indicator", "static_indicator", "l_fraction", "z_static"]
QOI_LABELS = {
    "trans_indicator": "Y1: transient failure indicator",
    "static_indicator": "Y2: static failure indicator",
    "l_fraction": "Y3: final erosion fraction l_e/L",
    "z_static": "Y4: static margin Z_static",
}

# Seed-stream tags (SeedSequence entropy words): the GSA draws its own stream
# family off the config seed, disjoint from the production sweep and the
# ADR-0031 study by the tag word.
_TAG_GSA = 0x65A0
_TAG_BOOT = 0xB007

# Fixed per-input colors (dataviz palette, validated: worst adjacent CVD
# dE 24.2). Color follows the entity across every figure; the three
# sub-3:1-contrast hues get direct labels wherever they carry meaning.
INPUT_COLORS = {
    "k_aq": "#2a78d6",
    "d_70": "#1baf7a",
    "D_aq": "#eda100",
    "D_bl": "#008300",
    "k_bl": "#4a3aa7",
    "gamma_bl_sub": "#e34948",
    "C_e": "#e87ba4",
    "L": "#eb6834",
}
INPUT_TEX = {
    "k_aq": r"$k_{aq}$",
    "d_70": r"$d_{70}$",
    "D_aq": r"$D_{aq}$",
    "D_bl": r"$D_{bl}$",
    "k_bl": r"$k_{bl}$",
    "gamma_bl_sub": r"$\gamma'_{bl}$",
    "C_e": r"$C_e$",
    "L": r"$L$",
}
_INK = "#0b0b0b"
_INK_2 = "#52514e"
_MUTED = "#898781"
_GRID = "#e1e0d9"


def _slug(config_path: Path) -> str:
    return config_path.stem.replace("_historical", "")


def _paths(slug: str) -> dict[str, Path]:
    return {
        "json": REPO_ROOT / "results" / "gsa" / f"{slug}_gsa.json",
        "tracked_json": REPO_ROOT
        / "docs"
        / "decisions"
        / f"adr0033-gsa-study-{slug}.json",
    }


def _fig_paths(name: str) -> tuple[Path, Path]:
    return (
        REPO_ROOT / "results" / "figures" / f"{name}.png",
        REPO_ROOT / "docs" / "figures" / f"{name}.png",
    )


def _seed(*words: int) -> int:
    return int(np.random.SeedSequence(list(words)).generate_state(1)[0])


# ---------------------------------------------------------------------------
# Engine wiring
# ---------------------------------------------------------------------------
def _space_from_config(
    cfg: Config,
    *,
    coupling: str | None = None,
    rho: float | None = None,
    anchor: str = "k_aq",
) -> GsaInputSpace:
    """Build the GSA input space from a run config (production prior)."""
    return GsaInputSpace(
        marginals=tuple(cfg.priors.to_marginal_specs()),
        bounds=cfg.priors.bounds,
        seepage_mean_m=(cfg.geometry.L if cfg.seepage_length_cov is not None else None),
        seepage_cov=cfg.seepage_length_cov,
        coupling=coupling if coupling is not None else cfg.correlation.coupling,
        rho_log_kaq_d70=(rho if rho is not None else cfg.correlation.rho_log_kaq_d70),
        anchor=anchor,
    )


def _qoi_vectors(qoi) -> dict[str, np.ndarray]:
    return {
        "trans_indicator": qoi.failure_trans.astype(np.float64),
        "static_indicator": qoi.failure_static.astype(np.float64),
        "l_fraction": np.asarray(qoi.l_fraction, dtype=np.float64),
        "z_static": np.asarray(qoi.z_static_m, dtype=np.float64),
    }


def _evaluate_design(
    space: GsaInputSpace,
    n_base: int,
    seed: int,
    record,
    geometry: dict,
    cfg: Config,
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """One replicate: design -> engine -> per-QoI (y_A, y_B, y_ABi)."""
    u_a, u_b = generate_design(space.k, n_base, seed=seed)
    u_all = stack_evaluation_matrix(u_a, u_b)
    theta, seepage = space.map_uniform(u_all)
    qoi = evaluate_qoi_batch(
        theta,
        record,
        geometry,
        l_ini=0.0,
        seepage_length_samples=seepage,
        alpha_exponent=cfg.alpha_exponent,
        alpha_exponent_transient=cfg.alpha_exponent_transient,
        theta_repose_rad=cfg.theta_repose_rad,
        relative_density=cfg.relative_density_insitu,
        foreland_open=cfg.foreland_treatment == "open_entry",
        progression_backend=BACKEND,
    )
    return {
        key: split_outputs(y, n_base, space.k) for key, y in _qoi_vectors(qoi).items()
    }


def _run_level(
    level_m: float,
    level_index: int,
    cfg: Config,
    canonical,
    space: GsaInputSpace,
    *,
    n_ladder: list[int],
    n_replicates: int,
    n_boot: int,
    stream_tag: int = 0,
) -> dict:
    """All rungs and replicates for one conditioning level (all QoIs)."""
    geometry = cfg.geometry.as_evaluator_dict()
    record = _hydrograph_for_level(float(level_m), cfg, canonical)
    base_seed = int(cfg.mc.seed)

    rung_blocks: dict[str, list[dict]] = {key: [] for key in QOI_KEYS}
    for rung_index, n_base in enumerate(n_ladder):
        final_rung = rung_index == len(n_ladder) - 1
        reps: dict[str, list] = {key: [] for key in QOI_KEYS}
        boot_s: dict[str, list[np.ndarray]] = {key: [] for key in QOI_KEYS}
        boot_st: dict[str, list[np.ndarray]] = {key: [] for key in QOI_KEYS}
        for r in range(n_replicates):
            seed = _seed(base_seed, _TAG_GSA, stream_tag, level_index, rung_index, r)
            split_by_qoi = _evaluate_design(space, n_base, seed, record, geometry, cfg)
            for key, (y_a, y_b, y_abi) in split_by_qoi.items():
                reps[key].append(sobol_indices(y_a, y_b, y_abi, names=space.names))
                if final_rung and n_boot > 0:
                    ci = bootstrap_indices(
                        y_a,
                        y_b,
                        y_abi,
                        n_boot=n_boot,
                        seed=_seed(
                            base_seed,
                            _TAG_BOOT,
                            stream_tag,
                            level_index,
                            r,
                            QOI_KEYS.index(key),
                        ),
                        confidence=CONFIDENCE,
                    )
                    boot_s[key].append(ci["S_boot"])
                    boot_st[key].append(ci["ST_boot"])

        for key in QOI_KEYS:
            agg = aggregate_replicates(reps[key], confidence=CONFIDENCE)
            block = {
                "n_base": int(n_base),
                "S_mean": agg["S_mean"].tolist(),
                "S_se": agg["S_se"].tolist(),
                "S_lo": agg["S_lo"].tolist(),
                "S_hi": agg["S_hi"].tolist(),
                "ST_mean": agg["ST_mean"].tolist(),
                "ST_se": agg["ST_se"].tolist(),
                "ST_lo": agg["ST_lo"].tolist(),
                "ST_hi": agg["ST_hi"].tolist(),
                "mean_y": agg["mean_y_mean"],
                "var_y": agg["var_y_mean"],
                "sum_S": float(np.sum(agg["S_mean"])),
            }
            if final_rung and n_boot > 0 and boot_s[key]:
                # Bootstrap CI of the *replicate-mean* index: average the
                # b-th draw across replicates, then take percentiles
                # (ADR-0033 §4: the cross-check to the t-interval).
                s_all = np.mean(np.stack(boot_s[key]), axis=0)  # (B, k)
                st_all = np.mean(np.stack(boot_st[key]), axis=0)
                alpha = 100.0 * (1.0 - CONFIDENCE) / 2.0
                block["boot_S_lo"] = np.nanpercentile(s_all, alpha, axis=0).tolist()
                block["boot_S_hi"] = np.nanpercentile(
                    s_all, 100 - alpha, axis=0
                ).tolist()
                block["boot_ST_lo"] = np.nanpercentile(st_all, alpha, axis=0).tolist()
                block["boot_ST_hi"] = np.nanpercentile(
                    st_all, 100 - alpha, axis=0
                ).tolist()
            rung_blocks[key].append(block)

    def _safe_drift(final_vals, prev_vals) -> float:
        """Max |delta| across inputs; NaN when the QoI is degenerate."""
        delta = np.abs(np.asarray(final_vals, float) - np.asarray(prev_vals, float))
        return float(np.nanmax(delta)) if not np.all(np.isnan(delta)) else float("nan")

    qois = {}
    for key in QOI_KEYS:
        rungs = rung_blocks[key]
        final, prev = rungs[-1], rungs[-2] if len(rungs) > 1 else rungs[-1]
        drift_s = _safe_drift(final["S_mean"], prev["S_mean"])
        drift_st = _safe_drift(final["ST_mean"], prev["ST_mean"])
        qois[key] = {
            "label": QOI_LABELS[key],
            "rungs": rungs,
            "convergence": {
                "drift_S_last_two_rungs": drift_s,
                "drift_ST_last_two_rungs": drift_st,
                "converged_0p02": bool(max(drift_s, drift_st) < 0.02),
            },
        }
        final_st = np.array(rungs[-1]["ST_mean"], dtype=float)
        top_name = (
            "(degenerate)"
            if np.all(np.isnan(final_st))
            else space.names[int(np.nanargmax(final_st))]
        )
        print(
            f"  h={level_m:6.2f}  {key:16s}  mean_y={rungs[-1]['mean_y']:.4f}  "
            f"top ST={top_name:12s}"
            f"  drift={max(drift_s, drift_st):.4f}",
            flush=True,
        )
    return {"level_m": float(level_m), "qois": qois}


def _scenario_invariance_check(cfg: Config, canonical, level_m: float) -> dict:
    """ADR-0023/ADR-0033 §6: verify the +4K record is bit-identical."""
    rec_hist = conditioning_record_for_level(
        canonical, float(level_m), scenario="historical"
    )
    rec_4k = conditioning_record_for_level(canonical, float(level_m), scenario="+4K")
    if cfg.timestepper.target_dt_seconds is not None:
        rec_hist = resample_record(rec_hist, cfg.timestepper.target_dt_seconds)
        rec_4k = resample_record(rec_4k, cfg.timestepper.target_dt_seconds)
    identical = bool(
        np.array_equal(rec_hist.h, rec_4k.h) and rec_hist.peak == rec_4k.peak
    )
    return {
        "level_m": float(level_m),
        "loading_bit_identical_across_scenarios": identical,
        "note": (
            "ADR-0023 shape invariance: one canonical HPB shape drives all "
            "scenarios, so a +4K GSA at matched conditioning level is "
            "definitionally identical; the climate signal is the "
            "level-dependence of the indices (ADR-0033 §6)."
        ),
    }


def _warm_numba(cfg: Config, canonical, space: GsaInputSpace, level_m: float):
    """Force the numba JIT compile before any timed work."""
    geometry = cfg.geometry.as_evaluator_dict()
    record = _hydrograph_for_level(float(level_m), cfg, canonical)
    u = np.full((64, space.k), 0.5) + np.linspace(-0.2, 0.2, 64)[:, None]
    theta, seepage = space.map_uniform(u)
    evaluate_qoi_batch(
        theta,
        record,
        geometry,
        seepage_length_samples=seepage,
        progression_backend=BACKEND,
    )


def run_section(
    config_path: Path,
    levels: list[float],
    *,
    n_ladder: list[int],
    n_replicates: int,
    n_boot: int,
) -> dict:
    """The full per-section study (all levels, all QoIs, ladder + CIs)."""
    cfg = Config.from_yaml(config_path)
    canonical = _load_canonical_or_none(cfg)
    space = _space_from_config(cfg)
    _warm_numba(cfg, canonical, space, levels[0])

    print(
        f"== {cfg.cross_section_id} ({cfg.priors.d70_interpretation} d_70), "
        f"k={space.k}, R={n_replicates}, ladder={n_ladder}",
        flush=True,
    )
    t0 = time.perf_counter()
    level_records = [
        _run_level(
            level,
            i,
            cfg,
            canonical,
            space,
            n_ladder=n_ladder,
            n_replicates=n_replicates,
            n_boot=n_boot,
        )
        for i, level in enumerate(levels)
    ]
    runtime = time.perf_counter() - t0

    design_level = levels[min(1, len(levels) - 1)]
    return {
        "study": "Stage 6.5 variance-based GSA (ADR-0033)",
        "config": config_path.name,
        "config_hash": cfg.config_hash(),
        "cross_section_id": cfg.cross_section_id,
        "d70_interpretation": cfg.priors.d70_interpretation,
        "input_names": space.names,
        "generator_roles": space.generator_roles,
        "coupling": space.coupling,
        "rho_log_kaq_d70": space.rho_log_kaq_d70,
        "estimators": {
            "first_order": "Saltelli et al. (2010): mean(y_B*(y_ABi - y_A))/V",
            "total_effect": "Jansen (1999): mean((y_A - y_ABi)^2)/(2V)",
            "design": "scrambled-Sobol radial, cost N*(k+2) per replicate",
        },
        "n_replicates": int(n_replicates),
        "n_ladder": [int(n) for n in n_ladder],
        "n_boot": int(n_boot),
        "confidence": CONFIDENCE,
        "progression_backend": BACKEND,
        "base_seed": int(cfg.mc.seed),
        "scenario_invariance_check": _scenario_invariance_check(
            cfg, canonical, design_level
        ),
        "levels": level_records,
        "runtime_seconds": runtime,
    }


# The bulk d_70 interpretation reads the coarse gravel-framework grain size
# (13 mm vs the 0.53 mm matrix), lifting the whole KP58.8 fragility ~4 m: at
# the matrix design level 41.0 m the bulk transient P_f is 0.0 (a degenerate
# indicator, itself a finding). The bulk companion therefore compares at a
# MATCHED CURVE POSITION — the top-of-grid 45.0 m, its own near-transition
# level (P_f,trans ~ 0.15) — not at the matched stage.
BULK_COMPANION_LEVEL = 45.0


def run_companions(
    matrix_config: Path,
    bulk_config: Path,
    design_level: float,
    *,
    n_base: int,
    n_replicates: int,
    n_boot: int,
) -> dict:
    """The ADR-0033 §7 companions (final N only).

    * ``bulk_d70``: the co-primary bulk grain-size interpretation (ranking
      robustness), at its own matched-curve-position level (see
      :data:`BULK_COMPANION_LEVEL`).
    * ``nataf_anchor_k_aq`` / ``nataf_anchor_d_70``: the rho = 0.6 bounding
      Nataf case at the design level via the Rosenblatt/generator route
      (full vs independent contributions of the correlated pair,
      ADR-0033 §2).
    """
    runs = {}
    jobs = [
        ("bulk_d70", bulk_config, None, None, "k_aq", BULK_COMPANION_LEVEL),
        (
            "nataf_anchor_k_aq",
            matrix_config,
            "correlated",
            RHO_COMPANION,
            "k_aq",
            design_level,
        ),
        (
            "nataf_anchor_d_70",
            matrix_config,
            "correlated",
            RHO_COMPANION,
            "d_70",
            design_level,
        ),
    ]
    t0 = time.perf_counter()
    for stream, (tag, path, coupling, rho, anchor, level_m) in enumerate(jobs):
        cfg = Config.from_yaml(path)
        canonical = _load_canonical_or_none(cfg)
        space = _space_from_config(cfg, coupling=coupling, rho=rho, anchor=anchor)
        _warm_numba(cfg, canonical, space, level_m)
        print(f"== companion {tag} ({path.name}) at h={level_m}", flush=True)
        record = _run_level(
            level_m,
            0,
            cfg,
            canonical,
            space,
            n_ladder=[n_base],
            n_replicates=n_replicates,
            n_boot=n_boot,
            stream_tag=1 + stream,
        )
        runs[tag] = {
            "config": path.name,
            "coupling": space.coupling,
            "rho_log_kaq_d70": space.rho_log_kaq_d70,
            "anchor": anchor if coupling == "correlated" else None,
            "generator_roles": space.generator_roles,
            "d70_interpretation": cfg.priors.d70_interpretation,
            "level_m": float(level_m),
            "level_note": (
                "matched curve position (bulk fragility sits ~4 m higher; "
                "matrix design stage is degenerate P_f=0 under bulk)"
                if tag == "bulk_d70"
                else "matrix design level"
            ),
            "level": record,
        }
    return {
        "study": "Stage 6.5 GSA companions (ADR-0033 §7)",
        "design_level_m": float(design_level),
        "bulk_companion_level_m": float(BULK_COMPANION_LEVEL),
        "n_base": int(n_base),
        "n_replicates": int(n_replicates),
        "confidence": CONFIDENCE,
        "rho_companion": RHO_COMPANION,
        "runs": runs,
        "runtime_seconds": time.perf_counter() - t0,
    }


# ---------------------------------------------------------------------------
# Figures (dataviz method: fixed per-input colors, thin marks, hairline grid,
# direct labels for the low-contrast hues, one axis per panel)
# ---------------------------------------------------------------------------
def _style_axis(ax):
    ax.set_axisbelow(True)
    ax.grid(True, axis="both", color=_GRID, linewidth=0.7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#c3c2b7")
    ax.tick_params(colors=_MUTED, labelsize=8)


def _final_rung(payload_level: dict, qoi: str) -> dict:
    return payload_level["qois"][qoi]["rungs"][-1]


def _fig_indices_bars(payload: dict, slug: str) -> None:
    """Headline: S and ST per input at the design level, all four QoIs."""
    import matplotlib.pyplot as plt

    names = payload["input_names"]
    design = payload["levels"][min(1, len(payload["levels"]) - 1)]
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.6), sharey=True)
    y_pos = np.arange(len(names))[::-1]
    for ax, key in zip(axes.ravel(), QOI_KEYS):
        rung = _final_rung(design, key)
        s = np.array(rung["S_mean"])
        st = np.array(rung["ST_mean"])
        s_err = np.array(rung["S_hi"]) - s
        st_err = np.array(rung["ST_hi"]) - st
        colors = [INPUT_COLORS[n] for n in names]
        ax.barh(
            y_pos + 0.19,
            st,
            height=0.34,
            color=colors,
            alpha=0.45,
            xerr=st_err,
            error_kw={"ecolor": _INK_2, "elinewidth": 0.9, "capsize": 2},
        )
        ax.barh(
            y_pos - 0.19,
            s,
            height=0.34,
            color=colors,
            xerr=s_err,
            error_kw={"ecolor": _INK_2, "elinewidth": 0.9, "capsize": 2},
        )
        ax.set_yticks(y_pos)
        ax.set_yticklabels([INPUT_TEX[n] for n in names], fontsize=10)
        ax.axvline(0.0, color="#c3c2b7", linewidth=0.9)
        _style_axis(ax)
        mean_y = rung["mean_y"]
        extra = f"  ($P_f$ = {mean_y:.3f})" if "indicator" in key else ""
        ax.set_title(QOI_LABELS[key] + extra, fontsize=10, color=_INK)
        ax.set_xlabel("Sobol' index", fontsize=9, color=_INK_2)
    # Shared S/ST legend (solid = S, translucent = ST), neutral ink.
    from matplotlib.patches import Patch

    fig.legend(
        handles=[
            Patch(facecolor=_INK_2, label="first-order $S_i$"),
            Patch(facecolor=_INK_2, alpha=0.45, label="total-effect $S_{Ti}$"),
        ],
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    fig.suptitle(
        f"Sobol' indices at the design level h = {design['level_m']:.2f} m "
        f"MSL — {payload['cross_section_id']} "
        f"({payload['d70_interpretation']} $d_{{70}}$), "
        f"R = {payload['n_replicates']} scramblings, 95% CI",
        fontsize=11,
        color=_INK,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    _save(fig, f"gsa_indices_{slug}")


def _spread_label_positions(values: list[float], sep: float) -> list[float]:
    """Nudge overlapping end-label y-positions apart (ascending stacking)."""
    values = np.asarray(values, dtype=float)
    out = values.copy()
    order = np.argsort(values)
    floor = -np.inf
    for idx in order:
        out[idx] = max(out[idx], floor + sep)
        floor = out[idx]
    return out.tolist()


def _direct_label_lines(ax, x_end: float, names, end_values, *, min_value=0.03):
    """Right-edge direct labels for the lines that carry visible signal.

    Labels below ``min_value`` are omitted (the figure legend still names
    every series); collisions are resolved by vertical stacking.
    """
    keep = [(n, v) for n, v in zip(names, end_values) if abs(v) >= min_value]
    if not keep:
        return
    y_min, y_max = ax.get_ylim()
    spread = _spread_label_positions([v for _, v in keep], sep=0.035 * (y_max - y_min))
    for (name, _), y in zip(keep, spread):
        ax.annotate(
            INPUT_TEX[name],
            (x_end, y),
            xytext=(6, 0),
            textcoords="offset points",
            fontsize=9,
            color=INPUT_COLORS[name],
            va="center",
        )


def _series_legend(fig, names, **kwargs) -> None:
    """One figure-level legend naming every input in its fixed color."""
    from matplotlib.lines import Line2D

    handles = [
        Line2D([0], [0], color=INPUT_COLORS[n], lw=2.4, label=INPUT_TEX[n])
        for n in names
    ]
    fig.legend(
        handles=handles,
        loc=kwargs.pop("loc", "lower center"),
        ncol=kwargs.pop("ncol", len(names)),
        frameon=False,
        fontsize=9,
        **kwargs,
    )


def _fig_level_dependence(payload: dict, slug: str) -> None:
    """S_i and ST_i vs conditioning level for the transient indicator (Y1)."""
    import matplotlib.pyplot as plt

    names = payload["input_names"]
    levels = [lvl["level_m"] for lvl in payload["levels"]]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.9), sharey=True)
    for ax, which in zip(axes, ("S", "ST")):
        end_values = []
        for j, name in enumerate(names):
            vals = [
                _final_rung(lvl, "trans_indicator")[f"{which}_mean"][j]
                for lvl in payload["levels"]
            ]
            lo = [
                _final_rung(lvl, "trans_indicator")[f"{which}_lo"][j]
                for lvl in payload["levels"]
            ]
            hi = [
                _final_rung(lvl, "trans_indicator")[f"{which}_hi"][j]
                for lvl in payload["levels"]
            ]
            color = INPUT_COLORS[name]
            ax.plot(levels, vals, "-", color=color, linewidth=2.0)
            ax.plot(levels, vals, "o", color=color, markersize=4.5)
            ax.fill_between(levels, lo, hi, color=color, alpha=0.12, lw=0)
            end_values.append(vals[-1])
        _direct_label_lines(ax, levels[-1], names, end_values)
        _style_axis(ax)
        label = "first-order $S_i$" if which == "S" else "total-effect $S_{Ti}$"
        ax.set_title(f"{label} — transient failure indicator", fontsize=10, color=_INK)
        ax.set_xlabel("conditioning level h [m MSL]", fontsize=9, color=_INK_2)
        pf = [
            _final_rung(lvl, "trans_indicator")["mean_y"] for lvl in payload["levels"]
        ]
        sec = ax.secondary_xaxis("top")
        sec.set_xticks(levels)
        sec.set_xticklabels([f"{p:.2g}" for p in pf], fontsize=7)
        sec.tick_params(colors=_MUTED, length=0)
        sec.set_xlabel("$P_f$(h)", fontsize=8, color=_MUTED)
        sec.spines["top"].set_visible(False)
    axes[0].set_ylabel("Sobol' index", fontsize=9, color=_INK_2)
    fig.suptitle(
        f"Index rotation along the conditioning axis — "
        f"{payload['cross_section_id']} (the +4K direction is rightward; "
        "ADR-0023/ADR-0033 §6)",
        fontsize=11,
        color=_INK,
    )
    _series_legend(fig, names)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    _save(fig, f"gsa_levels_{slug}")


def _fig_convergence(payload: dict, slug: str) -> None:
    """Convergence ladder at the design level: index vs N with CIs (Y1)."""
    import matplotlib.pyplot as plt

    names = payload["input_names"]
    design = payload["levels"][min(1, len(payload["levels"]) - 1)]
    rungs = design["qois"]["trans_indicator"]["rungs"]
    n_vals = [r["n_base"] for r in rungs]
    final_st = np.array(rungs[-1]["ST_mean"])
    top = list(np.argsort(final_st)[::-1][:4])
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.7), sharex=True)
    for ax, which in zip(axes, ("S", "ST")):
        end_values, end_names = [], []
        for j in top:
            name = names[j]
            vals = [r[f"{which}_mean"][j] for r in rungs]
            lo = [r[f"{which}_lo"][j] for r in rungs]
            hi = [r[f"{which}_hi"][j] for r in rungs]
            color = INPUT_COLORS[name]
            ax.plot(n_vals, vals, "o-", color=color, linewidth=2.0, markersize=4.5)
            ax.fill_between(n_vals, lo, hi, color=color, alpha=0.15, lw=0)
            end_values.append(vals[-1])
            end_names.append(name)
        ax.set_xscale("log", base=2)
        _direct_label_lines(ax, n_vals[-1], end_names, end_values, min_value=0.0)
        _style_axis(ax)
        label = "first-order $S_i$" if which == "S" else "total-effect $S_{Ti}$"
        ax.set_title(label, fontsize=10, color=_INK)
        ax.set_xlabel("base sample N per replicate", fontsize=9, color=_INK_2)
    axes[0].set_ylabel("Sobol' index (95% CI)", fontsize=9, color=_INK_2)
    drift = design["qois"]["trans_indicator"]["convergence"]
    worst_drift = max(drift["drift_S_last_two_rungs"], drift["drift_ST_last_two_rungs"])
    fig.suptitle(
        f"Convergence ladder, transient indicator at h = "
        f"{design['level_m']:.2f} m — {payload['cross_section_id']} "
        f"(last-two-rungs drift {worst_drift:.3f})",
        fontsize=11,
        color=_INK,
    )
    _series_legend(fig, [names[j] for j in top], ncol=4)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    _save(fig, f"gsa_convergence_{slug}")


def _fig_interaction_gap(payload: dict, slug: str) -> None:
    """The fm7 diagnostic: ST - S per input vs level (transient indicator)."""
    import matplotlib.pyplot as plt

    names = payload["input_names"]
    levels = [lvl["level_m"] for lvl in payload["levels"]]
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    end_values = []
    for j, name in enumerate(names):
        gap = [
            _final_rung(lvl, "trans_indicator")["ST_mean"][j]
            - _final_rung(lvl, "trans_indicator")["S_mean"][j]
            for lvl in payload["levels"]
        ]
        color = INPUT_COLORS[name]
        emphasize = name in ("C_e", "k_aq")
        ax.plot(
            levels,
            gap,
            "o-",
            color=color,
            linewidth=2.4 if emphasize else 1.4,
            markersize=5 if emphasize else 3.5,
            alpha=1.0 if emphasize else 0.55,
        )
        end_values.append(gap[-1])
    _direct_label_lines(ax, levels[-1], names, end_values)
    ax.axhline(0.0, color="#c3c2b7", linewidth=0.9)
    _style_axis(ax)
    ax.set_xlabel("conditioning level h [m MSL]", fontsize=9, color=_INK_2)
    ax.set_ylabel(r"interaction gap $S_{Ti} - S_i$", fontsize=9, color=_INK_2)
    ax.set_title(
        f"Interaction involvement, transient indicator — "
        f"{payload['cross_section_id']} (fm7: $C_e \\times k_{{aq}}$)",
        fontsize=10,
        color=_INK,
    )
    _series_legend(fig, names, ncol=4)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    _save(fig, f"gsa_interaction_{slug}")


def _fig_companions(comp: dict, baseline_payload: dict) -> None:
    """Companion comparison at the design level: Y1 total-effect indices."""
    import matplotlib.pyplot as plt

    names = baseline_payload["input_names"]
    design = baseline_payload["levels"][min(1, len(baseline_payload["levels"]) - 1)]
    base_rung = _final_rung(design, "trans_indicator")

    series = [("baseline (matrix, two-population)", base_rung)]
    for tag in ("bulk_d70", "nataf_anchor_k_aq", "nataf_anchor_d_70"):
        run = comp["runs"][tag]
        series.append((tag, _final_rung(run["level"], "trans_indicator")))

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    x = np.arange(len(names), dtype=float)
    width = 0.19
    hatches = [None, "//", None, "\\\\"]
    alphas = [1.0, 0.75, 0.5, 0.35]
    bulk_level = comp.get("bulk_companion_level_m", BULK_COMPANION_LEVEL)
    labels = {
        "baseline (matrix, two-population)": "baseline (matrix, indep.)",
        "bulk_d70": f"bulk $d_{{70}}$ (h={bulk_level:.1f} m, matched position)",
        "nataf_anchor_k_aq": r"Nataf $\rho$=0.6, $k_{aq}$ full",
        "nataf_anchor_d_70": r"Nataf $\rho$=0.6, $d_{70}$ full",
    }
    for s, (tag, rung) in enumerate(series):
        st = np.array(rung["ST_mean"])
        err = np.array(rung["ST_hi"]) - st
        ax.bar(
            x + (s - 1.5) * width,
            st,
            width=width * 0.92,
            color=[INPUT_COLORS[n] for n in names],
            alpha=alphas[s],
            hatch=hatches[s],
            edgecolor="white",
            linewidth=0.5,
            yerr=err,
            error_kw={"ecolor": _INK_2, "elinewidth": 0.8, "capsize": 1.5},
            label=labels[tag],
        )
    ax.set_xticks(x)
    ax.set_xticklabels([INPUT_TEX[n] for n in names], fontsize=10)
    _style_axis(ax)
    ax.set_ylabel(r"total-effect $S_{Ti}$ (Y1)", fontsize=9, color=_INK_2)
    ax.set_title(
        f"Companion runs (baseline and Nataf at h = "
        f"{comp['design_level_m']:.2f} m) — ranking robustness "
        "(bars grouped per input; alpha/hatch = run)",
        fontsize=10,
        color=_INK,
    )
    from matplotlib.patches import Patch

    legend_handles = [
        Patch(
            facecolor=_INK_2,
            alpha=alphas[s],
            hatch=hatches[s],
            edgecolor="white",
            label=labels[tag],
        )
        for s, (tag, _) in enumerate(series)
    ]
    ax.legend(handles=legend_handles, frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    _save(fig, "gsa_companions")


def _save(fig, name: str) -> None:
    for path in _fig_paths(name):
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160, facecolor="white")
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    import matplotlib.pyplot as plt

    plt.close(fig)


def _plot_section(payload: dict, slug: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    _fig_indices_bars(payload, slug)
    _fig_level_dependence(payload, slug)
    _fig_convergence(payload, slug)
    _fig_interaction_gap(payload, slug)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _write_json(payload: dict, paths: dict[str, Path]) -> None:
    text = json.dumps(payload, indent=2) + "\n"
    for path in (paths["json"], paths["tracked_json"]):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="single config YAML under configs/; default runs both governing "
        "sections (KP58.8 + KP60.0 matrix)",
    )
    parser.add_argument(
        "--levels",
        type=str,
        default=None,
        help="comma-separated conditioning stages [m MSL]; required with "
        "--config unless it is one of the two defaults",
    )
    parser.add_argument(
        "--ladder",
        type=str,
        default=",".join(str(n) for n in DEFAULT_N_LADDER),
        help="comma-separated base-N ladder (each a power of two)",
    )
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--n-boot", type=int, default=DEFAULT_N_BOOT)
    parser.add_argument("--skip-companions", action="store_true")
    parser.add_argument(
        "--companions-only",
        action="store_true",
        help="run only the companion sweeps (the section JSONs must exist)",
    )
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help="skip all sweeps; redraw figures from the existing JSONs",
    )
    args = parser.parse_args()
    n_ladder = [int(n) for n in args.ladder.split(",")]

    if args.companions_only:
        sections = {}
    elif args.config is not None:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = REPO_ROOT / "configs" / config_path
        if args.levels is not None:
            levels = [float(x) for x in args.levels.split(",")]
        elif config_path.name in DEFAULT_SECTIONS:
            levels = DEFAULT_SECTIONS[config_path.name]
        else:
            parser.error("--levels is required for a non-default --config.")
        sections = {config_path: levels}
    else:
        sections = {
            REPO_ROOT / "configs" / name: lv for name, lv in DEFAULT_SECTIONS.items()
        }

    for config_path, levels in sections.items():
        slug = _slug(config_path)
        paths = _paths(slug)
        if args.plot_only:
            source = paths["json"] if paths["json"].exists() else paths["tracked_json"]
            payload = json.loads(source.read_text(encoding="utf-8"))
        else:
            payload = run_section(
                config_path,
                levels,
                n_ladder=n_ladder,
                n_replicates=args.replicates,
                n_boot=args.n_boot,
            )
            print(f"section runtime {payload['runtime_seconds']:.0f} s")
            _write_json(payload, paths)
        _plot_section(payload, slug)

    if args.companions_only or (not args.skip_companions and args.config is None):
        comp_paths = _paths("kp58_8_matrix_companions")
        matrix_cfg = REPO_ROOT / "configs" / "kp58_8_historical_matrix.yaml"
        if args.plot_only:
            source = (
                comp_paths["json"]
                if comp_paths["json"].exists()
                else comp_paths["tracked_json"]
            )
            comp = json.loads(source.read_text(encoding="utf-8"))
        else:
            comp = run_companions(
                matrix_cfg,
                REPO_ROOT / "configs" / "kp58_8_historical_bulk.yaml",
                DESIGN_LEVEL["kp58_8"],
                n_base=n_ladder[-1],
                n_replicates=args.replicates,
                n_boot=args.n_boot,
            )
            print(f"companions runtime {comp['runtime_seconds']:.0f} s")
            _write_json(comp, comp_paths)
        baseline = json.loads(
            _paths("kp58_8_matrix")["json"].read_text(encoding="utf-8")
        )
        import matplotlib

        matplotlib.use("Agg")
        _fig_companions(comp, baseline)


if __name__ == "__main__":
    main()
