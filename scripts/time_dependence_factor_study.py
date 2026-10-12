"""The time-dependence factor on one head and one initiation gate (ADR-0055).

Driver for ``docs/decisions/time-dependence-factor-study.md``. Companion study:
no production default, config, prior, kernel, persisted sweep, posterior or
annual result changes. It answers Pol's comments 1 and 2 on the pre-Green-Light
thesis: which single head convention the criterion comparison should use, what
the right metric for the effect of time dependence is, and how that metric
relates to the factor ``F_td`` of Pol et al. (2024, SIE), like for like.

The steady-state comparator of record (ADR-0055) is the Stage 6.6 comparator
``C3b``: the transient model's own crack-reduced erosion head and its own
uplift/heave gate, with instantaneous pipe growth, i.e. failure as soon as the
gate is open and ``(h - z_toe) - 0.3 D_bl > H_c``. That is Pol's "stationary"
model (instantaneous pipe growth, SIE 2024 Eq. 18 and section 3.2) and the
steady-state sub-mechanism check of Dutch practice. Against the adopted
transient branch ``C4b`` it isolates the time a pipe needs and nothing else, so

    F_td(h) = P[C3b](h) / P[C4b](h),   dbeta_td(h) = beta[C4b](h) - beta[C3b](h).

``C3b`` is closed form (ADR-0040 Decision 2), evaluated here through the M8
diagnostics of a short constant-stage record, exactly as
``gap_decomposition._evaluate_ladder_level`` does, and gated on reproducing the
persisted production static matrix (``C0``) bit for bit at every level.

Parts (each writes ``results/time_dependence_factor/stage_<part>.json``; the
``report`` part assembles the committed evidence JSON):

``event``      per-event factor and index difference, eight strata at N = 1e5,
               plus the N = 1e6 anchors and scale alternatives from the
               persisted ADR-0040 ladders.
``larms``      re-run the four ADR-0047 seepage-length arms (not persisted by the
               synthesis study; in-memory ``geometry.L`` override).
``brackets``   the robustness brackets of the RQ1 comparison re-measured in the
               new metric (conductivity means, blanket weight, model factor,
               critical length, seepage length, exit datum, canonical event).
``evidence``   the 2016 likelihood ratio, transient over same-head same-gate.
``annual``     the annual factor: both branches composed and annualised through
               the production Phase 3 path, prior and each criterion's own
               survival update.
``timescale``  held-peak traverse time against the time the flood holds the
               erosion head above each realization's critical head.
``polriver``   Pol's river base case (SIE 2024 Table 2) run through this
               engine's kernels: per-event factor and first-year factor without
               flood fighting.
``figures``    the thesis figures in the house style (docs/figures/).
``report``     assemble ``docs/decisions/time-dependence-factor-study.json``.

Usage (from the worktree, reading the main checkout's untracked results)::

    python scripts/time_dependence_factor_study.py event \
        --results-root D:/repositories/bep-reliability-engine/results
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import yaml
from numpy.typing import NDArray
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.progression import CRACK_RESISTANCE_FACTOR  # noqa: E402

KPS: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0)
D70S: tuple[str, ...] = ("matrix", "bulk")
#: Design high water levels [m T.P.] (thesis Table 3.1).
DESIGN_HWL = {57.4: 39.21, 58.8: 41.03, 60.0: 42.75, 62.0: 46.39}
#: ADR-0024 attainable maxima [m T.P.].
ATTAINABLE_MAX = {57.4: 43.25, 58.8: 42.75, 60.0: 44.25, 62.0: 50.5}
#: Thesis reporting rules (section 4.4): R1 count floor on the transient
#: branch, R2 multiplicative width of the ratio interval, R2beta index width.
R1_MIN_TRANSIENT = 30
R2_MAX_WIDTH = 2.0
R2_BETA_MAX_WIDTH = 0.30
#: The ADR-0047 ratio-of-ratios kernel's own floor, kept so the published
#: gross-head departures reproduce before anything new is reported.
ADR0047_MIN_CELL = 10
BOOT_N = 2000
SEED = 20261006

OUT_DIR = REPO / "results" / "time_dependence_factor"
EVIDENCE = REPO / "docs" / "decisions" / "time-dependence-factor-study.json"

#: ADR-0047 seepage-length arms behind the thesis row "factors 1.02 to 2.29,
#: 84 comparable levels": the clean-station DEM median at three sections and
#: the withdrawn 1998 reading at KP 62.0 (epistemic-bracket-synthesis.json).
L_ARMS: dict[float, tuple[str, float]] = {
    57.4: ("L_dem_clean_median", 36.5),
    58.8: ("L_dem_clean_median", 42.0),
    60.0: ("L_dem_clean_median", 43.0),
    62.0: ("L_withdrawn_1998", 47.0),
}


def _stem(kp: float, d70: str) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{d70}"


def _cfg_path(kp: float, d70: str) -> Path:
    name = f"kp{kp:.1f}".replace(".", "_") + f"_historical_{d70}.yaml"
    return REPO / "configs" / name


def _label(kp: float) -> str:
    return f"KP {kp:.1f}"


def _write_stage(part: str, payload: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"stage_{part}.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=False), encoding="utf-8")
    return path


def _read_stage(part: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / f"stage_{part}.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The same-head, same-gate comparator                                           #
# --------------------------------------------------------------------------- #
def same_head_flags(
    run: Any, *, relief_override: float | None = None
) -> dict[str, NDArray[np.bool_]]:
    """Closed-form C1 and C3b for every row and level of one Phase 1 run.

    One M8 diagnostics call per level on a constant-stage record supplies the
    single-source ``H_c`` (with every knob the run carries: model factor,
    critical length, relief, foreland credit) and the gate latch at that stage;
    under the ADR-0008 collapse a constant record's ``heave_occurred`` is
    exactly "the gate is open at this stage". ``C0`` from the same call must
    equal the run's persisted static column bit for bit, or nothing is
    reported (the ADR-0040 gate (i)).

    ``relief_override`` replaces the run's ADR-0050 relief factor in the gate
    only (0.5 is a halved r_e, since r_e enters nothing but the gate head);
    ``C0`` does not see the gate, so the persisted-column check still holds.

    Returns
    -------
    dict
        ``{"C0", "C1", "C3b", "gate"}`` boolean ``(N, N_h)`` matrices; ``gate``
        is the uplift/heave gate open at the held stage.
    """
    from bep_reliability_engine.evaluator import evaluate_batch_diagnostics
    from bep_reliability_engine.gap_decomposition import sustained_peak_record

    cfg = run.config
    theta = run.theta
    geometry = run.geometry
    grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
    persisted = np.asarray(run.result.failure_matrix_stat, dtype=bool)
    z_toe = float(geometry["z_toe"])
    coef = (
        CRACK_RESISTANCE_FACTOR
        if cfg.crack_resistance_factor is None
        else float(cfg.crack_resistance_factor)
    )
    d_bl = theta[:, 3]
    dt = float(cfg.timestepper.target_dt_seconds or 225.0)
    out = {
        k: np.zeros(persisted.shape, dtype=bool) for k in ("C0", "C1", "C3b", "gate")
    }
    for i, level in enumerate(grid):
        diag = evaluate_batch_diagnostics(
            theta,
            sustained_peak_record(float(level), dt_s=dt),
            geometry,
            l_ini=0.0,
            seepage_length_samples=run.seepage_length_samples,
            alpha_exponent=cfg.alpha_exponent,
            theta_repose_rad=cfg.theta_repose_rad,
            relative_density=cfg.relative_density_insitu,
            foreland_open=cfg.foreland_treatment == "open_entry",
            progression_backend="numpy",
            model_factor_samples=run.model_factor_samples,
            critical_length_factor=cfg.critical_length_factor,
            toe_gradient_relief_factor=(
                cfg.toe_gradient_relief_factor
                if relief_override is None
                else relief_override
            ),
            foreland_seepage_credit=cfg.foreland_seepage_credit,
        )
        c0 = np.asarray(diag.failure_static, dtype=bool)
        if not np.array_equal(c0, persisted[:, i]):
            raise SystemExit(
                f"{run.source_path.name}: recomputed static column differs from "
                f"the persisted one at {level} m; refusing (ADR-0040 gate i)."
            )
        crack = (float(level) - z_toe) - coef * d_bl
        out["C0"][:, i] = c0
        out["C1"][:, i] = (diag.H_c - crack) <= 0.0
        gate = np.asarray(diag.heave_occurred, dtype=bool)
        out["gate"][:, i] = gate
        out["C3b"][:, i] = gate & (crack > diag.H_c_transient)
    return out


def _cached_flags(path: Path, cache_key: str) -> tuple[Any, dict[str, NDArray]]:
    """Load a Phase 1 run and its same-head flags, caching the flags locally."""
    from bayesian_reliability_updating.replay import load_phase1_run

    run = load_phase1_run(path)
    cache = OUT_DIR / "cache" / f"{cache_key}.npz"
    if cache.is_file():
        with np.load(cache) as data:
            if "gate" in data.files:
                flags = {k: data[k] for k in ("C0", "C1", "C3b", "gate")}
                if not np.array_equal(flags["C0"], run.result.failure_matrix_stat):
                    raise SystemExit(f"stale cache {cache.name}")
                return run, flags
    flags = same_head_flags(run)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **flags)
    return run, flags


# --------------------------------------------------------------------------- #
# Paired statistics                                                             #
# --------------------------------------------------------------------------- #
def _beta(p: NDArray[np.float64] | float) -> NDArray[np.float64]:
    """Reliability index; +/-inf at P = 0 / 1."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.asarray(norm.isf(np.asarray(p, dtype=np.float64)))


def paired_pair(
    a: NDArray[np.bool_], b: NDArray[np.bool_], seed: int, n_boot: int = BOOT_N
) -> dict[str, Any]:
    """Ratio P(a)/P(b) and index difference beta(b) - beta(a), paired.

    A row resample is a multinomial draw over the four joint patterns of the
    two indicators, so the bootstrap runs on four cells, exactly as the
    ADR-0047 kernel does on sixteen.
    """
    code = a.astype(np.int64) + 2 * b.astype(np.int64)
    counts = np.bincount(code, minlength=4)
    n = int(counts.sum())
    ka, kb = int(counts[1] + counts[3]), int(counts[2] + counts[3])
    out: dict[str, Any] = {"n": n, "k_a": ka, "k_b": kb, "b_not_a": int(counts[2])}
    pa, pb = ka / n, kb / n
    out["ratio"] = pa / pb if kb else None
    out["dbeta"] = float(_beta(pb) - _beta(pa)) if 0 < ka < n and 0 < kb < n else None
    if kb == 0 or ka == n:
        return out
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(n, counts / n, size=n_boot).astype(np.float64)
    ma = (draws[:, 1] + draws[:, 3]) / n
    mb = (draws[:, 2] + draws[:, 3]) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        r = ma / mb
        db = _beta(mb) - _beta(ma)
    r, db = r[np.isfinite(r)], db[np.isfinite(db)]
    if r.size:
        lo, hi = np.percentile(r, [2.5, 97.5])
        out["ratio_ci95"] = [float(lo), float(hi)]
        out["ratio_width"] = float(hi / lo) if lo > 0 else None
    if db.size and out["dbeta"] is not None:
        lo, hi = np.percentile(db, [2.5, 97.5])
        out["dbeta_ci95"] = [float(lo), float(hi)]
        out["dbeta_width"] = float(hi - lo)
    out["R1"] = kb >= R1_MIN_TRANSIENT
    out["ratio_quotable"] = bool(
        out["R1"]
        and out.get("ratio_width") is not None
        and out["ratio_width"] <= R2_MAX_WIDTH
    )
    out["dbeta_quotable"] = bool(
        out["R1"]
        and out.get("dbeta_width") is not None
        and out["dbeta_width"] <= R2_BETA_MAX_WIDTH
    )
    return out


def _cp(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Two-sided Clopper-Pearson endpoints (each a one-sided 97.5 % bound)."""
    from bep_reliability_engine.fragility import binomial_ci

    lo, hi = binomial_ci(np.array([k / n]), n, conf)
    return float(lo[0]), float(hi[0])


# --------------------------------------------------------------------------- #
# Part: event                                                                   #
# --------------------------------------------------------------------------- #
def event_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"n1e5": {}, "n1e6": {}}
    for kp in KPS:
        for d70 in D70S:
            stem = _stem(kp, d70)
            run, flags = _cached_flags(results_root / f"{stem}.h5", stem)
            grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
            trans = np.asarray(run.result.failure_matrix_tran, dtype=bool)
            levels = []
            for i, h in enumerate(grid):
                seed = SEED + i + int(kp * 100) + (0 if d70 == "matrix" else 50000)
                td = paired_pair(flags["C3b"][:, i], trans[:, i], seed)
                gross = paired_pair(flags["C0"][:, i], trans[:, i], seed + 1)
                head_gate = paired_pair(flags["C0"][:, i], flags["C3b"][:, i], seed + 2)
                levels.append(
                    {
                        "stage_m": float(h),
                        "attainable": bool(h <= ATTAINABLE_MAX[kp] + 1e-9),
                        "k_C0": int(flags["C0"][:, i].sum()),
                        "k_C1": int(flags["C1"][:, i].sum()),
                        "k_C3b": int(flags["C3b"][:, i].sum()),
                        "k_C4b": int(trans[:, i].sum()),
                        "flips_C4b_not_C3b": int(
                            np.sum(trans[:, i] & ~flags["C3b"][:, i])
                        ),
                        "flips_C3b_not_C1": int(
                            np.sum(flags["C3b"][:, i] & ~flags["C1"][:, i])
                        ),
                        "time_factor": td,
                        "gross_static_vs_transient": gross,
                        "gross_static_vs_same_head": head_gate,
                    }
                )
            out["n1e5"][f"{_label(kp)} {d70}"] = {
                "n": int(trans.shape[0]),
                "design_hwl_m": DESIGN_HWL[kp],
                "attainable_max_m": ATTAINABLE_MAX[kp],
                "levels": levels,
            }
            print(f"  event {stem}: done", flush=True)

    # N = 1e6 anchors from the persisted ADR-0040 ladders (C0, C1, C3b, C3a,
    # C4b, C4a on one shared sample, re-based under ADR-0054).
    ladder_dir = results_root / "hwl_bias_resolution"
    for kp, tag in ((62.0, "62_0"), (57.4, "57_4")):
        with h5py.File(ladder_dir / f"ladder_kp{tag}_n1000000.h5", "r") as h5:
            grid = np.asarray(h5["conditioning_grid"][:], dtype=np.float64)
            comp = {
                c: np.asarray(h5["comparators"][c][:], dtype=bool)
                for c in ("C0", "C1", "C3b", "C3a", "C4b", "C4a")
            }
        n = comp["C0"].shape[0]
        levels = []
        for i, h in enumerate(grid):
            if h > ATTAINABLE_MAX[kp] + 1e-9:
                continue
            seed = SEED + 7000 + i + int(kp * 10)
            entry = {
                "stage_m": float(h),
                **{f"k_{c}": int(m[:, i].sum()) for c, m in comp.items()},
                "flips_C4b_not_C3b": int(
                    np.sum(comp["C4b"][:, i] & ~comp["C3b"][:, i])
                ),
                "time_factor": paired_pair(comp["C3b"][:, i], comp["C4b"][:, i], seed),
                "gross_static_vs_transient": paired_pair(
                    comp["C0"][:, i], comp["C4b"][:, i], seed + 1
                ),
                "gross_static_vs_same_head": paired_pair(
                    comp["C0"][:, i], comp["C3b"][:, i], seed + 2
                ),
                "scale_transient_only": paired_pair(
                    comp["C3b"][:, i], comp["C4a"][:, i], seed + 3
                ),
                "scale_symmetric": paired_pair(
                    comp["C3a"][:, i], comp["C4a"][:, i], seed + 4
                ),
            }
            k3, k4 = entry["k_C3b"], entry["k_C4b"]
            if k4 < R1_MIN_TRANSIENT:
                # Union-bound construction of thesis section 5.1: one-sided
                # 97.5 % endpoints of the two branch counts.
                lo3, hi3 = _cp(k3, n)
                lo4, hi4 = _cp(k4, n)
                entry["bounds_union"] = {
                    "ratio_lower": lo3 / hi4 if hi4 > 0 else None,
                    "dbeta_lower": float(_beta(hi4) - _beta(lo3)),
                    "dbeta_upper": float(_beta(lo4) - _beta(hi3)) if lo4 > 0 else None,
                    "containment_lower": (
                        "ratio >= 1 and dbeta >= 0 by the nesting theorem"
                    ),
                }
            levels.append(entry)
        out["n1e6"][_label(kp)] = {"n": n, "levels": levels}
    return out


# --------------------------------------------------------------------------- #
# Part: brackets                                                                #
# --------------------------------------------------------------------------- #
def _adr0047():
    import importlib.util

    path = REPO / "scripts" / "dem_cross_section_study.py"
    spec = importlib.util.spec_from_file_location("dem_cross_section_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _arm_registry(results_root: Path, kp: float) -> list[tuple[str, str, Path]]:
    stem = _stem(kp, "matrix")
    sens = results_root / "sensitivity"
    arms = [
        (
            "k_aq",
            "k_aq_field_geomean",
            sens / "adr0048_prior_means" / f"{stem}_k_aq_field_geomean.h5",
        ),
        (
            "k_aq",
            "k_aq_field_toe",
            sens / "adr0048_prior_means" / f"{stem}_k_aq_field_toe.h5",
        ),
        (
            "k_aq",
            "k_aq_regional_upper",
            sens / "adr0048_prior_means" / f"{stem}_k_aq_regional_upper.h5",
        ),
        (
            "gamma_bl_sub",
            "gamma_bl_sub_lower",
            sens / "adr0048_prior_means" / f"{stem}_gamma_bl_sub_lower.h5",
        ),
        ("m_p", "m_p", sens / "adr0045_mp" / f"{stem}_mp.h5"),
        ("l_c", "l_c_lower", sens / "adr0049_critical_length" / f"{stem}_l_c_lower.h5"),
        ("l_c", "l_c_upper", sens / "adr0049_critical_length" / f"{stem}_l_c_upper.h5"),
        (
            "canonical_event",
            "alternate",
            results_root / "canonical_shape" / "arms" / f"{stem}_alternate.h5",
        ),
    ]
    name, _ = L_ARMS[kp]
    arms.append(("L", name, OUT_DIR / "l_arms" / f"{stem}_{name}.h5"))
    for arm in UNIFORMITY_ARMS:
        arms.append(("C_u", f"cu_{arm}", OUT_DIR / "u_arms" / f"{stem}_cu_{arm}.h5"))
    for shift in ("minus0.30m", "plus0.30m"):
        arms.append(
            (
                "z_toe",
                f"z_toe_{shift}",
                sens / "adr0046_ztoe" / f"{stem}_ztoe_{shift}.h5",
            )
        )
    if kp in (58.8, 60.0):
        drained = sens / "adr0050_drained_bracket"
        arms.append(("drain", "berm_only", drained / f"{stem}_berm_only.h5"))
        # The ADR-0050 factor is the fraction of the exit gradient that SURVIVES
        # the drain: 0.20 is 80 per cent relief, 0.80 is 20 per cent.
        for kept in ("0.80", "0.60", "0.40", "0.20"):
            relief = round(100 * (1 - float(kept)))
            arms.append(
                (
                    "drain",
                    f"berm_relief_{relief}pct",
                    drained / f"{stem}_joint_{kept}.h5",
                )
            )
    return arms


def _compare(
    base_s: NDArray,
    base_t: NDArray,
    arm_s: NDArray,
    arm_t: NDArray,
    grid,
    kp,
    dem,
    *,
    attainable_only: bool = True,
) -> dict[str, Any]:
    """Per-level ratio-of-ratios (ADR-0047 kernel) and index displacement.

    ``attainable_only=False`` counts the whole grid, as the published
    synthesis did, so its reproduction gate compares like with like.
    """
    levels = []
    for i, h in enumerate(grid):
        if attainable_only and h > ATTAINABLE_MAX[kp] + 1e-9:
            continue
        cells = [int(m[:, i].sum()) for m in (base_s, base_t, arm_s, arm_t)]
        entry: dict[str, Any] = {"stage_m": float(h), "cells": cells}
        if min(cells) >= ADR0047_MIN_CELL:
            counts = dem._pattern_counts(
                base_s[:, i], base_t[:, i], arm_s[:, i], arm_t[:, i]
            )
            entry.update(dem.ratio_of_ratios_ci(counts, seed=i))
            n = int(counts.sum())
            p = counts @ dem._PATTERN_BITS.T / n
            if np.all((p > 0) & (p < 1)):
                db_base = float(_beta(p[1]) - _beta(p[0]))
                db_arm = float(_beta(p[3]) - _beta(p[2]))
                rng = np.random.default_rng(SEED + 11 + i)
                draws = rng.multinomial(n, counts / n, size=BOOT_N).astype(np.float64)
                m = draws @ dem._PATTERN_BITS.T / n
                disp = (_beta(m[:, 3]) - _beta(m[:, 2])) - (
                    _beta(m[:, 1]) - _beta(m[:, 0])
                )
                disp = disp[np.isfinite(disp)]
                entry["dbeta_base"] = db_base
                entry["dbeta_arm"] = db_arm
                entry["dbeta_displacement"] = db_arm - db_base
                if disp.size:
                    entry["dbeta_displacement_ci95"] = [
                        float(x) for x in np.percentile(disp, [2.5, 97.5])
                    ]
        levels.append(entry)

    def summary(floor: int) -> dict[str, Any]:
        ev = [lv for lv in levels if "rho" in lv and min(lv["cells"]) >= floor]
        res = [lv for lv in ev if lv["resolved"] and lv["rho"] > 0]
        deps = [abs(np.log(lv["rho"])) for lv in res]
        disp = [lv["dbeta_displacement"] for lv in ev if "dbeta_displacement" in lv]
        return {
            "floor_min_cell": floor,
            "n_levels": len(ev),
            "n_resolved": len(res),
            "rho_min": min((lv["rho"] for lv in ev), default=None),
            "rho_max": max((lv["rho"] for lv in ev), default=None),
            "max_resolved_departure_factor": float(np.exp(max(deps))) if deps else None,
            "dbeta_displacement_min": min(disp, default=None),
            "dbeta_displacement_max": max(disp, default=None),
            "max_abs_dbeta_displacement": max((abs(x) for x in disp), default=None),
        }

    return {
        "levels": levels,
        "summary_floor10": summary(ADR0047_MIN_CELL),
        "summary_R1": summary(R1_MIN_TRANSIENT),
    }


def brackets_part(results_root: Path) -> dict[str, Any]:

    dem = _adr0047()
    out: dict[str, Any] = {}
    for kp in KPS:
        stem = _stem(kp, "matrix")
        base, base_flags = _cached_flags(results_root / f"{stem}.h5", stem)
        grid = np.asarray(base.result.conditioning_grid, dtype=np.float64)
        base_t = np.asarray(base.result.failure_matrix_tran, dtype=bool)
        section: dict[str, Any] = {}
        for bracket, arm, path in _arm_registry(results_root, kp):
            if not path.is_file():
                section[arm] = {
                    "bracket": bracket,
                    "available": False,
                    "path": str(path),
                }
                continue
            arm_run, arm_flags = _cached_flags(path, f"{stem}_{arm}")
            arm_grid = np.asarray(arm_run.result.conditioning_grid, dtype=np.float64)
            if not np.array_equal(arm_grid, grid):
                raise SystemExit(f"{path.name}: grid differs from production")
            arm_t = np.asarray(arm_run.result.failure_matrix_tran, dtype=bool)
            entry = {
                "bracket": bracket,
                "available": True,
                "path": str(path),
                "same_head_static_identical_to_production": bool(
                    np.array_equal(arm_flags["C3b"], base_flags["C3b"])
                ),
                "gross_static_identical_to_production": bool(
                    np.array_equal(arm_flags["C0"], base_flags["C0"])
                ),
                "time_factor": _compare(
                    base_flags["C3b"], base_t, arm_flags["C3b"], arm_t, grid, kp, dem
                ),
                "gross_ratio_reproduction": _compare(
                    base_flags["C0"],
                    base_t,
                    arm_flags["C0"],
                    arm_t,
                    grid,
                    kp,
                    dem,
                    attainable_only=False,
                ),
            }
            entry["gross_ratio_reproduction"].pop("levels")
            section[arm] = entry
            print(f"  bracket {stem} {arm}: done", flush=True)
        out[_label(kp)] = section
    # Gate: the gross-head departures must reproduce the published synthesis.
    synth = json.loads(
        (REPO / "docs" / "decisions" / "epistemic-bracket-synthesis.json").read_text(
            encoding="utf-8"
        )
    )
    repro = []
    for sec in synth["sections"]:
        kp = float(sec["section"].replace("KP", ""))
        for arm, rec in sec["arms"].items():
            mine = out[_label(kp)].get(arm)
            if (
                not mine
                or not mine.get("available")
                or "max_resolved_departure_factor" not in rec
            ):
                continue
            got = mine["gross_ratio_reproduction"]["summary_floor10"]
            repro.append(
                {
                    "section": sec["section"],
                    "arm": arm,
                    "published": rec["max_resolved_departure_factor"],
                    "reproduced": got["max_resolved_departure_factor"],
                    "published_n_levels": rec["n_levels_ratio_evaluated"],
                    "reproduced_n_levels": got["n_levels"],
                }
            )
    out["gross_reproduction_gate"] = repro
    return out


# --------------------------------------------------------------------------- #
# Part: evidence                                                                #
# --------------------------------------------------------------------------- #
def _replay_arrays(path: Path) -> dict[str, NDArray]:
    with h5py.File(path, "r") as h5:
        (event,) = list(h5["events"].keys())
        g = h5["events"][event]
        return {
            "accept_trans": np.asarray(g["accept_trans"][:], dtype=bool),
            "accept_static": np.asarray(g["accept_static"][:], dtype=bool),
            "Z_static": np.asarray(g["Z_static"][:], dtype=np.float64),
            "initiation": np.asarray(g["initiation"][:], dtype=bool),
            "d_bl": np.asarray(h5["theta_matrix"][:, 3], dtype=np.float64),
        }


def _same_head_survival(a: dict[str, NDArray]) -> NDArray[np.bool_]:
    """Survival of 2016 under instantaneous growth on the same head and gate.

    Both the gate head and the erosion head rise with the stage, so on any
    record "gate open and erosion head above H_c at some time" holds iff it
    holds at the replayed peak: failure is ``initiation`` (the gate latched at
    some time, hence at the peak) and ``Z_static + 0.3 D_bl < 0``.
    """
    c1_fail = (a["Z_static"] + CRACK_RESISTANCE_FACTOR * a["d_bl"]) < 0.0
    return ~(a["initiation"] & c1_fail)


def evidence_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "per_stratum": {},
        "joint": {},
        "berm": {},
        "hypothetical": {},
    }
    surv: dict[float, tuple[float, float]] = {}
    for d70 in D70S:
        for kp in KPS:
            a = _replay_arrays(
                results_root / "phase2" / f"{_stem(kp, d70)}_posterior.h5"
            )
            t = a["accept_trans"]
            s = _same_head_survival(a)
            g = a["accept_static"]
            # Containment in survival terms: a same-head survivor never fails
            # transiently.
            viol = int(np.sum(s & ~t))
            pt, ps, pg = t.mean(), s.mean(), g.mean()
            # LR = P(survive | transient) / P(survive | same head): failures are
            # the complements, so pair on the failure indicators.
            pair = paired_pair(
                ~t, ~s, SEED + 300 + int(kp * 10) + (0 if d70 == "matrix" else 7)
            )
            rng = np.random.default_rng(SEED + 400 + int(kp * 10))
            code = (~s).astype(np.int64) + 2 * (~t).astype(np.int64)
            counts = np.bincount(code, minlength=4)
            n = int(counts.sum())
            draws = rng.multinomial(n, counts / n, size=BOOT_N) / n
            surv_s = 1.0 - (draws[:, 1] + draws[:, 3])
            surv_t = 1.0 - (draws[:, 2] + draws[:, 3])
            lr = surv_t / surv_s
            entry = {
                "n": n,
                "rejected_transient": float(1 - pt),
                "rejected_same_head": float(1 - ps),
                "rejected_gross_static": float(1 - pg),
                "same_head_survivors_failing_transient": viol,
                "LR_transient_over_same_head": float(pt / ps),
                "LR_ci95": [float(x) for x in np.percentile(lr, [2.5, 97.5])],
                "LR_transient_over_gross_static": float(pt / pg),
                "LR_same_head_over_gross_static": float(ps / pg),
                "failing_rows": {"transient": pair["k_a"], "same_head": pair["k_b"]},
            }
            out["per_stratum"][f"{_label(kp)} {d70}"] = entry
            if d70 == "matrix":
                surv[kp] = (float(pt), float(ps))
    pt = np.array([surv[kp][0] for kp in KPS])
    ps = np.array([surv[kp][1] for kp in KPS])
    out["joint"] = {
        "comonotone": float(pt.min() / ps.min()),
        "independent": float(pt.prod() / ps.prod()),
        "frechet_lower": (
            float(max(0.0, pt.sum() - 3) / max(0.0, ps.sum() - 3))
            if ps.sum() > 3
            else None
        ),
        "note": "one dependence structure imposed on both criteria alike",
    }
    arm_dir = results_root / "sensitivity" / "adr0050_drained_bracket" / "phase2"
    for kp in (58.8, 60.0):
        a = _replay_arrays(arm_dir / f"{_stem(kp, 'matrix')}_berm_only_posterior.h5")
        t, s = a["accept_trans"], _same_head_survival(a)
        out["berm"][_label(kp)] = {
            "rejected_transient": float(1 - t.mean()),
            "rejected_same_head": float(1 - s.mean()),
            "LR_transient_over_same_head": float(t.mean() / s.mean()),
            "same_head_survivors_failing_transient": int(np.sum(s & ~t)),
        }
    # What one survival or one breach of the canonical flood would say, by stage.
    for kp in KPS:
        stem = _stem(kp, "matrix")
        run, flags = _cached_flags(results_root / f"{stem}.h5", stem)
        grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
        pt_ = np.asarray(run.result.failure_matrix_tran, dtype=bool).mean(axis=0)
        ps_ = flags["C3b"].mean(axis=0)
        rows = []
        for h, s_, t_ in zip(grid, ps_, pt_, strict=True):
            if h > ATTAINABLE_MAX[kp] + 1e-9:
                continue
            rows.append(
                {
                    "stage_m": float(h),
                    "P_same_head": float(s_),
                    "P_transient": float(t_),
                    "LR_one_survival": float((1 - t_) / (1 - s_)) if s_ < 1 else None,
                    "LR_one_breach": float(t_ / s_) if s_ > 0 else None,
                }
            )
        finite = [r for r in rows if r["LR_one_survival"] is not None]
        out["hypothetical"][_label(kp)] = {
            "levels": rows,
            "max_LR_one_survival": max(finite, key=lambda r: r["LR_one_survival"]),
        }
    return out


# --------------------------------------------------------------------------- #
# Part: annual                                                                  #
# --------------------------------------------------------------------------- #
#: Branch names: T = adopted transient, I = instantaneous growth on the same
#: head and gate (the comparator of record). "-post" is each criterion's own
#: 2016 update; "-raw" evaluates the curve by its raw points only.
ANNUAL_BRANCHES = (
    "T-prior",
    "T-post",
    "I-prior",
    "I-post",
    "I-post-fit",
    "T-prior-raw",
    "T-post-raw",
    "I-prior-raw",
)
ANNUAL_PAIRS = (
    ("I-prior", "T-prior"),
    ("I-post", "T-post"),
    ("I-post-fit", "T-post"),
    ("I-prior-raw", "T-prior-raw"),
    ("I-post", "T-post-raw"),
    ("T-post", "T-prior"),
    ("I-post", "I-prior"),
)


def _same_head_curve(grid, p_raw, n, z_toe, source, path, *, fitted: bool):
    """A FragilityCurve for the same-head branch, fitted as M9 fits production."""
    from bep_reliability_engine.fragility import binomial_ci, fit_lognormal_fragility
    from system_integration.bep_input import FragilityCurve, _deliverable_fit

    lower, upper = binomial_ci(p_raw, n, 0.95)
    fit = None
    if fitted:
        try:
            fit = fit_lognormal_fragility(grid, p_raw, z_toe)
        except ValueError:
            fit = None
    return FragilityCurve(
        grid_m_msl=np.asarray(grid, dtype=np.float64),
        p_raw=np.asarray(p_raw, dtype=np.float64),
        ci_lower=np.asarray(lower, dtype=np.float64),
        ci_upper=np.asarray(upper, dtype=np.float64),
        fit=fit,
        fit_is_deliverable=(
            _deliverable_fit(fit, np.asarray(p_raw)) if fitted else False
        ),
        branch="static",
        source=source,
        source_path=str(path),
        datum_m=float(z_toe),
    )


def annual_part(results_root: Path, replicates: int) -> dict[str, Any]:
    import annualisation_uncertainty_study as unc
    from criterion_consequence_study import _fit_check, _raw_of

    data_repo = results_root.parent
    unc.PRODUCTION_TABLE = results_root / "system_integration/phase3/rq4_annual.csv"
    campaign = unc._load_campaign_module()
    campaign.REPO = data_repo
    campaign.DATA_ROOT = data_repo / "data/raw"
    campaign.HAZARD_CACHE = results_root / "system_integration/hazard_cache"
    cache_before = unc._dir_state(campaign.HAZARD_CACHE, "*.csv")
    context = unc.build_context(campaign)
    production = dict(context["bep_curves"])

    rows_by_arm: dict[str, Any] = {}
    rows_by_branch: dict[tuple[str, str], Any] = {}
    per_event: dict[tuple[str, str], Any] = {}
    for d70 in D70S:
        for source, branch in (("prior", "T-prior"), ("posterior", "T-post")):
            rows, pe = unc.annualise_arm(campaign, context, d70, source)
            rows_by_arm[unc._arm_key(d70, source)] = rows
            rows_by_branch[(d70, branch)] = rows
            per_event[(d70, branch)] = pe
    gate1 = unc.gate_one(rows_by_arm)
    print(f"  gate 1 passed: {gate1['rows_compared']} rows", flush=True)

    fit_checks: dict[str, Any] = {}
    accepted: dict[str, int] = {}
    for d70 in D70S:
        curves: dict[str, dict[float, Any]] = {b: {} for b in ANNUAL_BRANCHES[2:]}
        for kp in KPS:
            stem = _stem(kp, d70)
            run, flags = _cached_flags(results_root / f"{stem}.h5", stem)
            grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
            z_toe = float(run.geometry["z_toe"])
            c3b = flags["C3b"]
            n = c3b.shape[0]
            prior_p = c3b.mean(axis=0)
            prior = _same_head_curve(
                grid, prior_p, n, z_toe, "same_head_prior", run.source_path, fitted=True
            )
            a = _replay_arrays(results_root / "phase2" / f"{stem}_posterior.h5")
            accept = _same_head_survival(a)
            accepted[f"{_label(kp)} {d70}"] = int(accept.sum())
            post_p = c3b[accept].mean(axis=0)
            post_raw = _same_head_curve(
                grid,
                post_p,
                int(accept.sum()),
                z_toe,
                "same_head_self_posterior_raw",
                run.source_path,
                fitted=False,
            )
            post_fit = _same_head_curve(
                grid,
                post_p,
                int(accept.sum()),
                z_toe,
                "same_head_self_posterior",
                run.source_path,
                fitted=True,
            )
            curves["I-prior"][kp] = prior
            curves["I-post"][kp] = post_raw
            curves["I-post-fit"][kp] = post_fit
            curves["T-prior-raw"][kp] = _raw_of(production[(kp, d70, "prior")], "raw")
            curves["T-post-raw"][kp] = _raw_of(
                production[(kp, d70, "posterior")], "raw"
            )
            curves["I-prior-raw"][kp] = _raw_of(prior, "raw")
            for name, c in (("I-prior", prior), ("I-post-fit", post_fit)):
                fit_checks[f"{_label(kp)} {d70} {name}"] = _fit_check(c)
        slots = {
            "I-prior": "prior",
            "I-post": "posterior",
            "I-post-fit": "posterior",
            "T-prior-raw": "prior",
            "T-post-raw": "posterior",
            "I-prior-raw": "prior",
        }
        for branch, slot in slots.items():
            for kp in KPS:
                context["bep_curves"][(kp, d70, slot)] = curves[branch][kp]
            rows, pe = unc.annualise_arm(campaign, context, d70, slot)
            rows_by_branch[(d70, branch)], per_event[(d70, branch)] = rows, pe
            for kp in KPS:
                context["bep_curves"][(kp, d70, slot)] = production[(kp, d70, slot)]
        print(f"  annualised {d70}", flush=True)
    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")

    # Gate 2: the 110 surface-only segments must be identical across branches.
    kp_set = {round(k, 3) for k in KPS}
    for (d70, branch), rows in rows_by_branch.items():
        base = rows_by_branch[(d70, "T-post")]
        for key, row in rows.items():
            if key[0] == "Tokachi" and round(key[1], 3) in kp_set:
                continue
            if {k: v for k, v in row.items() if k != "bep_source"} != {
                k: v for k, v in base[key].items() if k != "bep_source"
            }:
                raise SystemExit(f"GATE 2 FAILED at {key} in {d70} {branch}")

    earned: dict[str, Any] = {}
    for d70 in D70S:
        for branch in ("T-prior", "I-prior", "T-post", "I-post"):
            for scenario in campaign.SCENARIOS:
                for kp in KPS:
                    peaks = np.asarray(
                        context["hazards"][scenario][("Tokachi", kp)].peak_stages()
                    )
                    for comp in ("__system__", "bep"):
                        vals = np.asarray(
                            per_event[(d70, branch)][("Tokachi", kp, scenario)][comp]
                        )
                        total = float(vals.sum())
                        above = peaks > DESIGN_HWL[kp]
                        earned[f"{d70} {branch} {_label(kp)} {scenario} {comp}"] = {
                            "share_from_peaks_above_design_level": (
                                float(vals[above].sum() / total) if total else None
                            ),
                            "probability_weighted_mean_peak_m": (
                                float((vals * peaks).sum() / total) if total else None
                            ),
                        }

    out: dict[str, Any] = {
        "gates": {
            "gate_1": gate1,
            "gate_2": "surface-only segments identical across every branch",
            "hazard_cache_unchanged": True,
        },
        "same_head_self_posterior_accepted_rows": accepted,
        "where_annual_probability_is_earned": earned,
        "fit_checks": fit_checks,
        "replicates": replicates,
        "seed": unc.SEED,
    }
    for d70 in D70S:
        rng = np.random.default_rng(unc.SEED)
        reps_store: dict[tuple[str, str, float, str], np.ndarray] = {}
        points: dict[tuple[str, float, str, str], Any] = {}
        for scenario in campaign.SCENARIOS:
            ids = [
                e.event_id
                for e in context["hazards"][scenario][("Tokachi", 58.8)].events
            ]
            index, n_blocks, _ = unc.block_index(unc.block_labels(ids, "member"))
            strata = unc.stratum_columns(ids)
            mult = unc.draw_multiplicities_stratified(strata, n_blocks, replicates, rng)
            for branch in ANNUAL_BRANCHES:
                pe = per_event[(d70, branch)]
                for kp in KPS:
                    reps = unc.node_replicates(
                        pe[("Tokachi", kp, scenario)], index, n_blocks, mult, len(ids)
                    )
                    shares = unc.share_replicates(reps)
                    reps_store[(branch, scenario, kp, "system")] = reps["__system__"]
                    reps_store[(branch, scenario, kp, "bep")] = reps["bep"]
                    reps_store[(branch, scenario, kp, "share_bep")] = shares.get(
                        "bep", np.full(replicates, np.nan)
                    )
                    reps_store[(branch, scenario, kp, "overflow")] = reps.get(
                        "overflow", np.zeros(replicates)
                    )
                    row = rows_by_branch[(d70, branch)][("Tokachi", kp, scenario)]
                    for field in (
                        "p_annual_system",
                        "p_annual_bep",
                        "p_annual_overflow",
                    ):
                        v = row[field]
                        points[(branch, kp, scenario, field)] = (
                            0.0 if v in ("", None) else float(v)
                        )
                    points[(branch, kp, scenario, "share_bep")] = (
                        None
                        if row["share_bep"] in ("", None)
                        else float(row["share_bep"])
                    )
        block: dict[str, Any] = {}
        for branch in ANNUAL_BRANCHES:
            entry: dict[str, Any] = {}
            for scenario in campaign.SCENARIOS:
                vals = {
                    kp: points[(branch, kp, scenario, "p_annual_system")] for kp in KPS
                }
                order = sorted(KPS, key=lambda k: -vals[k])
                stack = np.column_stack(
                    [reps_store[(branch, scenario, kp, "system")] for kp in KPS]
                )
                same = np.all(
                    np.argsort(-stack, axis=1)
                    == np.argsort(-np.array([vals[k] for k in KPS])),
                    axis=1,
                )
                sec: dict[str, Any] = {
                    "order": [_label(k) for k in order],
                    "fraction_replicates_with_this_order": float(np.mean(same)),
                }
                for kp in KPS:
                    share = reps_store[(branch, scenario, kp, "share_bep")]
                    share = share[np.isfinite(share)]
                    bep = reps_store[(branch, scenario, kp, "bep")]
                    ovf = reps_store[(branch, scenario, kp, "overflow")]
                    sec[_label(kp)] = {
                        "p_annual_system": vals[kp],
                        "p_annual_bep": points[(branch, kp, scenario, "p_annual_bep")],
                        "p_annual_overflow": points[
                            (branch, kp, scenario, "p_annual_overflow")
                        ],
                        "share_bep": points[(branch, kp, scenario, "share_bep")],
                        "share_bep_ci95": (
                            [float(x) for x in np.percentile(share, [2.5, 97.5])]
                            if share.size
                            else None
                        ),
                        "fraction_replicates_piping_leads": float(np.mean(bep > ovf)),
                        "system_ci95": [
                            float(x)
                            for x in np.percentile(
                                reps_store[(branch, scenario, kp, "system")],
                                [2.5, 97.5],
                            )
                        ],
                        "rank": order.index(kp) + 1,
                    }
                entry[scenario] = sec
            ratios = {}
            for kp in KPS:
                h = reps_store[(branch, "historical", kp, "system")]
                w = reps_store[(branch, "+4K", kp, "system")]
                ph = points[(branch, kp, "historical", "p_annual_system")]
                pw = points[(branch, kp, "+4K", "p_annual_system")]
                with np.errstate(divide="ignore", invalid="ignore"):
                    r = w / h
                r = r[np.isfinite(r)]
                ratios[_label(kp)] = {
                    "point": (pw / ph) if ph else None,
                    "ci95": (
                        [float(x) for x in np.percentile(r, [2.5, 97.5])]
                        if r.size
                        else None
                    ),
                }
            entry["climate_ratio"] = ratios
            block[branch] = entry
        comparisons: dict[str, Any] = {}
        for num, den in ANNUAL_PAIRS:
            comp: dict[str, Any] = {}
            for scenario in campaign.SCENARIOS:
                for kp in KPS:
                    for q, field in (
                        ("system", "p_annual_system"),
                        ("bep", "p_annual_bep"),
                    ):
                        a = reps_store[(num, scenario, kp, q)]
                        b = reps_store[(den, scenario, kp, q)]
                        pa = points[(num, kp, scenario, field)]
                        pb = points[(den, kp, scenario, field)]
                        with np.errstate(divide="ignore", invalid="ignore"):
                            r = a / b
                            db = _beta(b) - _beta(a)
                        r, db = r[np.isfinite(r)], db[np.isfinite(db)]
                        comp[f"{_label(kp)} {scenario} {q}"] = {
                            "point": (pa / pb) if pb else None,
                            "ci95": (
                                [float(x) for x in np.percentile(r, [2.5, 97.5])]
                                if r.size
                                else None
                            ),
                            "fraction_num_above_den": float(np.mean(a > b)),
                            "delta_beta": (
                                float(_beta(pb) - _beta(pa)) if pa and pb else None
                            ),
                            "delta_beta_ci95": (
                                [float(x) for x in np.percentile(db, [2.5, 97.5])]
                                if db.size
                                else None
                            ),
                        }
            for kp in KPS:
                ha = reps_store[(num, "historical", kp, "system")]
                wa = reps_store[(num, "+4K", kp, "system")]
                hb = reps_store[(den, "historical", kp, "system")]
                wb = reps_store[(den, "+4K", kp, "system")]
                with np.errstate(divide="ignore", invalid="ignore"):
                    q = (wb / hb) / (wa / ha)
                q = q[np.isfinite(q)]
                ra = block[num]["climate_ratio"][_label(kp)]["point"]
                rb = block[den]["climate_ratio"][_label(kp)]["point"]
                comp[f"{_label(kp)} climate-ratio quotient den over num"] = {
                    "point": (rb / ra) if (ra and rb) else None,
                    "ci95": (
                        [float(x) for x in np.percentile(q, [2.5, 97.5])]
                        if q.size
                        else None
                    ),
                }
            comparisons[f"{num} / {den}"] = comp
        out[d70] = {"branches": block, "paired_comparisons": comparisons}
    return out


# --------------------------------------------------------------------------- #
# Part: timescale                                                               #
# --------------------------------------------------------------------------- #
def held_peak_traverse_s(
    h_er: NDArray, h_c: NDArray, l_c: NDArray, length: NDArray, c_e: NDArray, k: NDArray
) -> NDArray[np.float64]:
    """Time [s] for a pipe to cross the whole path under a held erosion head.

    The integral of ``dl / v(l)`` with the engine's own rate (Eq. 5) and
    equilibrium curve (Eq. 11), on Chebyshev nodes clustered at both ends of
    the two linear branches of ``H_eq``, so the slowest point, the critical
    length, is resolved. Defined for ``h_er > h_c`` (the held peak passes the
    barrier); other rows return ``inf``.
    """
    from bep_reliability_engine.progression import equilibrium_head, progression_rate

    h_er, h_c, l_c, length, c_e, k = (
        np.asarray(x, dtype=np.float64)[:, None]
        for x in (h_er, h_c, l_c, length, c_e, k)
    )
    u = 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, 401)))[None, :]
    total = np.zeros(h_er.shape[0])
    for seg in (l_c * u, l_c + (length - l_c) * u):
        heq = equilibrium_head(seg, h_c, l_c, length)
        v = progression_rate(h_er, heq, c_e, k, length)
        with np.errstate(divide="ignore"):
            inv = np.where(v > 0, 1.0 / v, np.inf)
        total += 0.5 * ((inv[:, 1:] + inv[:, :-1]) * np.diff(seg, axis=1)).sum(axis=1)
    return total


def _time_above(h: NDArray, dt_s: float, threshold: NDArray) -> NDArray[np.float64]:
    """Hours each row's threshold is exceeded by the interval loads ``h``."""
    out = np.empty(threshold.size)
    for start in range(0, threshold.size, 20000):
        thr = threshold[start : start + 20000, None]
        out[start : start + 20000] = (h[None, :] > thr).sum(axis=1) * dt_s / 3600.0
    return out


def _quartiles(x: NDArray) -> dict[str, float] | None:
    x = x[np.isfinite(x)]
    if x.size == 0:
        return None
    q = np.percentile(x, [25, 50, 75])
    return {
        "q25": float(q[0]),
        "median": float(q[1]),
        "q75": float(q[2]),
        "n": int(x.size),
    }


def _prior_median(spec) -> float:
    """Median of a lognormal prior given its mean and CoV."""
    return float(spec.mean / np.sqrt(1.0 + spec.cov**2))


def timescale_part(results_root: Path) -> dict[str, Any]:
    from bep_reliability_engine.evaluator import evaluate_batch_diagnostics
    from bep_reliability_engine.gap_decomposition import sustained_peak_record
    from bep_reliability_engine.run import conditioning_hydrographs_for_config
    from bep_reliability_engine.sellmeijer import compute_critical_head_vectorized

    out: dict[str, Any] = {"sections": {}, "median_soil": {}}
    for kp in KPS:
        stem = _stem(kp, "matrix")
        run, flags = _cached_flags(results_root / f"{stem}.h5", stem)
        cfg = run.config
        grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
        trans = np.asarray(run.result.failure_matrix_tran, dtype=bool)
        records = conditioning_hydrographs_for_config(cfg)
        theta = run.theta
        z_toe = float(run.geometry["z_toe"])
        d_bl, gam, c_e, k = theta[:, 3], theta[:, 5], theta[:, 6], theta[:, 0]
        # Levels: the lowest R1-qualified one, the design grid level, the stage
        # where the transient branch is near one half, and the attainable top.
        k4 = trans.sum(axis=0)
        attain = grid <= ATTAINABLE_MAX[kp] + 1e-9
        idx_low = int(np.argmax((k4 >= R1_MIN_TRANSIENT) & attain))
        idx_design = int(np.argmin(np.abs(grid - DESIGN_HWL[kp])))
        p4 = k4 / trans.shape[0]
        idx_mid = int(np.argmin(np.where(attain, np.abs(p4 - 0.5), np.inf)))
        idx_top = int(np.max(np.nonzero(attain)[0]))
        diag = evaluate_batch_diagnostics(
            theta,
            sustained_peak_record(float(grid[idx_design]), dt_s=225.0),
            run.geometry,
            seepage_length_samples=run.seepage_length_samples,
            alpha_exponent=cfg.alpha_exponent,
            theta_repose_rad=cfg.theta_repose_rad,
            relative_density=cfg.relative_density_insitu,
            progression_backend="numpy",
        )
        h_c, l_c, r_e = diag.H_c, diag.l_c, diag.r_e
        length = run.seepage_length_samples
        thr_er = z_toe + CRACK_RESISTANCE_FACTOR * d_bl + h_c
        thr_gate = z_toe + gam * d_bl / (9.81 * r_e)
        threshold = np.maximum(thr_er, thr_gate)
        levels = {}
        for tag, i in (
            ("lowest_qualified", idx_low),
            ("design", idx_design),
            ("transient_near_half", idx_mid),
            ("attainable_top", idx_top),
        ):
            rows = flags["C3b"][:, i]
            h_er = (grid[i] - z_toe) - CRACK_RESISTANCE_FACTOR * d_bl
            t_hold = np.full(theta.shape[0], np.inf)
            t_hold[rows] = (
                held_peak_traverse_s(
                    h_er[rows], h_c[rows], l_c[rows], length[rows], c_e[rows], k[rows]
                )
                / 3600.0
            )
            rec = records[i]
            loads = np.asarray(rec.h[:-1], dtype=np.float64)
            t_avail = _time_above(loads, float(rec.native_dt), threshold)
            fail_t = trans[:, i] & rows
            only_i = rows & ~trans[:, i]
            levels[tag] = {
                "stage_m": float(grid[i]),
                "k_same_head": int(rows.sum()),
                "k_transient": int(trans[:, i].sum()),
                "record_hours_above_toe": float(
                    np.sum(loads > z_toe) * rec.native_dt / 3600.0
                ),
                "held_peak_traverse_h": {
                    "transient_failures": _quartiles(t_hold[fail_t]),
                    "instantaneous_only": _quartiles(t_hold[only_i]),
                },
                "hours_head_above_critical": {
                    "transient_failures": _quartiles(t_avail[fail_t]),
                    "instantaneous_only": _quartiles(t_avail[only_i]),
                },
                "ratio_traverse_over_available": {
                    "transient_failures": _quartiles(t_hold[fail_t] / t_avail[fail_t]),
                    "instantaneous_only": _quartiles(t_hold[only_i] / t_avail[only_i]),
                },
            }
        out["sections"][_label(kp)] = levels
        # The median foundation of the prior, at heads 10 and 50 per cent above
        # its own critical head: a deterministic scale for the text.
        specs = cfg.priors.to_marginal_specs()
        med = {s.name: _prior_median(s) for s in specs}
        row = np.array(
            [
                [
                    med[n]
                    for n in (
                        "k_aq",
                        "d_70",
                        "D_aq",
                        "D_bl",
                        "k_bl",
                        "gamma_bl_sub",
                        "C_e",
                    )
                ]
            ]
        )
        l_med = float(cfg.geometry.L)
        sr = compute_critical_head_vectorized(
            row,
            {"L": np.array([l_med])},
            alpha_exponent=cfg.alpha_exponent,
            theta_repose_rad=cfg.theta_repose_rad,
            relative_density=cfg.relative_density_insitu,
        )
        hc0, lc0 = np.atleast_1d(sr.H_c), np.atleast_1d(sr.l_c)
        out["median_soil"][_label(kp)] = {
            "inputs": {**med, "L": l_med},
            "H_c_m": float(hc0[0]),
            "l_c_m": float(lc0[0]),
            **{
                f"traverse_h_at_{int(100 * f)}pct_overload": float(
                    held_peak_traverse_s(
                        hc0 * (1 + f),
                        hc0,
                        lc0,
                        np.array([l_med]),
                        np.array([med["C_e"]]),
                        np.array([med["k_aq"]]),
                    )[0]
                    / 3600.0
                )
                for f in (0.1, 0.5)
            },
        }
        print(f"  timescale {stem}: done", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: polriver                                                                #
# --------------------------------------------------------------------------- #
#: Pol et al. (2024, SIE) Table 2, river base case, as read from the rendered
#: page (journal p. 8): (mean, spread, "sd" or "cov"), all lognormal. The
#: heave gradient i_c,h ~ LN(0.7, 0.1) and the uplift model factor m_u are not
#: carried: this engine's gate is the Terzaghi collapse (ADR-0008), stated as a
#: deviation in the note.
POL_TABLE2 = {
    "L": (50.0, 5.0, "sd"),
    "D_aq": (20.0, 0.5, "sd"),
    "D_bl": (3.0, 0.5, "sd"),
    "gamma_sat_bl": (18.0, 1.0, "sd"),
    "d_70": (150e-6, 0.1, "cov"),
    "k_aq": (1e-4, 0.5, "cov"),
    "C_e": (0.055, 0.043, "sd"),
    "m_p": (1.0, 0.12, "sd"),
}
POL_R_E = 0.6
POL_DP_MEAN_H, POL_DP_SD_H = 48.0, 24.0
#: Pol SIE 2024 Table 3, the reproducible (no flood fighting) river case 3d,
#: h_p ~ Gumbel(3, 0.25), year 2025 (one event from an intact blanket).
POL_CASE_3D_2025 = {"P_td": 1.1e-3, "P_stat": 7.3e-3, "F_td": 6.5}


def _pol_sample(n: int, seed: int) -> dict[str, NDArray]:
    rng = np.random.default_rng(seed)
    out = {}
    for name, (mean, spread, kind) in POL_TABLE2.items():
        sd = spread if kind == "sd" else spread * mean
        s = np.sqrt(np.log(1.0 + (sd / mean) ** 2))
        out[name] = rng.lognormal(np.log(mean) - 0.5 * s * s, s, n)
    return out


def pol_trapezoid(hp: float, dp_h: float, dt_s: float, h0: float = 0.0) -> NDArray:
    """Pol's river hydrograph (SIE 2024 Fig. 6b): base 240 + 3 Dp hours."""
    d0 = 240.0 + 3.0 * dp_h
    rise = 0.5 * (d0 - dp_h) * 3600.0
    t = np.arange(0.0, d0 * 3600.0 + 0.5 * dt_s, dt_s)
    h = np.interp(t, [0.0, rise, rise + dp_h * 3600.0, d0 * 3600.0], [h0, hp, hp, h0])
    return h


def polriver_part(n: int) -> dict[str, Any]:
    from bep_reliability_engine.progression_numba import integrate_progression_numba
    from bep_reliability_engine.sellmeijer import compute_critical_head_vectorized

    smp = _pol_sample(n, SEED + 2024)
    gam = smp["gamma_sat_bl"] - 9.81
    theta = np.column_stack(
        [
            smp["k_aq"],
            smp["d_70"],
            smp["D_aq"],
            smp["D_bl"],
            np.full(n, 1e-6),
            gam,
            smp["C_e"],
        ]
    )
    sr = compute_critical_head_vectorized(theta, {"L": smp["L"]})
    h_c = np.asarray(sr.H_c) * smp["m_p"]
    l_c = np.asarray(sr.l_c)
    d_bl = smp["D_bl"]
    gate_head = gam * d_bl / (9.81 * POL_R_E)  # stage at which the gate opens
    s_ln = np.sqrt(np.log(1.0 + (POL_DP_SD_H / POL_DP_MEAN_H) ** 2))
    m_ln = np.log(POL_DP_MEAN_H) - 0.5 * s_ln * s_ln
    x, w = np.polynomial.hermite_e.hermegauss(7)
    dps = list(np.exp(m_ln + s_ln * x))
    weights = list(w / np.sqrt(2.0 * np.pi))
    hp_grid = np.round(np.arange(2.0, 7.0 + 1e-9, 0.1), 2)
    dt = 225.0
    stat = np.array(
        [np.mean((hp > gate_head) & (hp - 0.3 * d_bl > h_c)) for hp in hp_grid]
    )
    p_td = np.zeros((hp_grid.size, len(dps) + 1))
    for j, dp in enumerate(dps + [POL_DP_MEAN_H]):
        for i, hp in enumerate(hp_grid):
            if stat[i] == 0.0:
                continue
            h = pol_trapezoid(float(hp), float(dp), dt)
            res = integrate_progression_numba(
                h[:-1],
                dt,
                POL_R_E,
                0.0,
                smp["C_e"],
                smp["k_aq"],
                d_bl,
                gam,
                h_c,
                l_c,
                smp["L"],
            )
            p_td[i, j] = float(np.mean(np.asarray(res.l_final_m) >= smp["L"] - 1e-12))
        print(f"  pol river Dp = {dp:.1f} h: done", flush=True)
    p_td_mixed = p_td[:, : len(dps)] @ np.asarray(weights)

    def first_year(loc: float, scale: float = 0.25) -> dict[str, float]:
        edges = np.concatenate(
            [[-np.inf], 0.5 * (hp_grid[1:] + hp_grid[:-1]), [np.inf]]
        )
        cdf = np.exp(-np.exp(-(edges - loc) / scale))
        mass = np.diff(cdf)
        ps, pt = float(mass @ stat), float(mass @ p_td_mixed)
        return {"P_stat": ps, "P_td": pt, "F_td": ps / pt if pt else None}

    per_event = []
    for i, hp in enumerate(hp_grid):
        if stat[i] == 0.0:
            continue
        pt48 = p_td[i, -1]
        per_event.append(
            {
                "hp_m": float(hp),
                "P_stat": float(stat[i]),
                "P_td_Dp48": float(pt48),
                "P_td_Dp_mixed": float(p_td_mixed[i]),
                "F_td_Dp48": float(stat[i] / pt48) if pt48 > 0 else None,
                "F_td_Dp_mixed": (
                    float(stat[i] / p_td_mixed[i]) if p_td_mixed[i] > 0 else None
                ),
                "dbeta_Dp48": (
                    float(_beta(pt48) - _beta(stat[i]))
                    if 0 < pt48 < 1 and 0 < stat[i] < 1
                    else None
                ),
                "transient_failures_Dp48": int(round(pt48 * n)),
            }
        )
    # Time scales at the per-event level where the stationary probability is
    # closest to 0.5 and at 0.1, for the Dp = 48 h hydrograph.
    scales = {}
    for target in (0.1, 0.5):
        i = int(np.argmin(np.abs(stat - target)))
        hp = float(hp_grid[i])
        rows = (hp > gate_head) & (hp - 0.3 * d_bl > h_c)
        t_hold = (
            held_peak_traverse_s(
                (hp - 0.3 * d_bl)[rows],
                h_c[rows],
                l_c[rows],
                smp["L"][rows],
                smp["C_e"][rows],
                smp["k_aq"][rows],
            )
            / 3600.0
        )
        h = pol_trapezoid(hp, POL_DP_MEAN_H, 3600.0)
        thr = np.maximum(0.3 * d_bl + h_c, gate_head)[rows]
        t_avail = _time_above(h[:-1], 3600.0, thr)
        scales[f"P_stat_near_{target}"] = {
            "hp_m": hp,
            "P_stat": float(stat[i]),
            "held_peak_traverse_h": _quartiles(t_hold),
            "hours_head_above_critical_Dp48": _quartiles(t_avail),
            "ratio": _quartiles(t_hold / t_avail),
        }
    med = {
        k: float(v[0] / np.sqrt(1 + (v[1] / v[0] if v[2] == "sd" else v[1]) ** 2))
        for k, v in POL_TABLE2.items()
    }
    row = np.array(
        [
            [
                med["k_aq"],
                med["d_70"],
                med["D_aq"],
                med["D_bl"],
                1e-6,
                med["gamma_sat_bl"] - 9.81,
                med["C_e"],
            ]
        ]
    )
    sr0 = compute_critical_head_vectorized(row, {"L": np.array([med["L"]])})
    hc0, lc0 = np.atleast_1d(sr0.H_c), np.atleast_1d(sr0.l_c)
    median_soil = {
        "inputs": med,
        "H_c_m": float(hc0[0]),
        "l_c_m": float(lc0[0]),
        **{
            f"traverse_h_at_{int(100 * f)}pct_overload": float(
                held_peak_traverse_s(
                    hc0 * (1 + f),
                    hc0,
                    lc0,
                    np.array([med["L"]]),
                    np.array([med["C_e"]]),
                    np.array([med["k_aq"]]),
                )[0]
                / 3600.0
            )
            for f in (0.1, 0.5)
        },
    }
    return {
        "n": n,
        "seed": SEED + 2024,
        "r_e": POL_R_E,
        "dp_nodes_h": [float(x) for x in dps],
        "dp_weights": [float(x) for x in weights],
        "deviations_from_pol": [
            "Terzaghi heave gradient gamma'_bl/gamma_w (ADR-0008) instead of "
            "i_c,h ~ LN(0.7, 0.1); no uplift model factor m_u",
            "gamma'_p = 16.87 kN/m3 (this engine's basin constant) in F_r",
            "no flood fighting: only Pol's case 3d is reproducible",
            "trapezoid starts at the polder level h0 = 0 (Fig. 6b mean level ~0.1 m)",
        ],
        "first_year_no_flood_fighting": {
            "Gumbel(3, 0.25), Pol case 3d": first_year(3.0),
            "Gumbel(4, 0.25), base-case level": first_year(4.0),
            "Gumbel(3.5, 0.25)": first_year(3.5),
            "pol_published_case_3d_2025": POL_CASE_3D_2025,
        },
        "per_event": per_event,
        "timescales": scales,
        "median_soil": median_soil,
    }


# --------------------------------------------------------------------------- #
# Part: figures                                                                 #
# --------------------------------------------------------------------------- #
#: Thesis-facing legend names for the two rules (docs/conventions.md 9.3.1).
RULE_LABELS = {
    "static": "Steady state: same head and gate, instantaneous growth",
    "transient": "Time-dependent: pipe growth through the flood",
}
FIGURES = (
    "same_head_fragility_log.png",
    "time_factor_vs_stage.png",
    "same_head_initiation.png",
    "same_head_survival_evidence.png",
    "time_factor_tokachi_rhine.png",
    "same_head_mp_ztoe.png",
)
#: The replayed 2016 peaks at the four sections [m T.P.] (thesis Table 6.1).
PEAK_2016 = {57.4: 39.658, 58.8: 40.750, 60.0: 42.296, 62.0: 45.729}


def _sec_key(kp: float) -> str:
    return f"KP{kp:.1f}"


def _fig_fragility(results_root: Path, fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    from bep_reliability_engine.fragility import binomial_ci

    width = fs.TEXTWIDTH_IN * 1.6
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(2, 2, figsize=(width, width * 0.56), sharey=True)
    for ax, kp in zip(axes.ravel(), KPS, strict=True):
        stem = _stem(kp, "matrix")
        run, flags = _cached_flags(results_root / f"{stem}.h5", stem)
        grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
        n = flags["C3b"].shape[0]
        z_toe = float(run.geometry["z_toe"])
        p_s = flags["C3b"].mean(axis=0)
        p_t = np.asarray(run.result.failure_matrix_tran, dtype=bool).mean(axis=0)
        # Raw points joined by straight lines, no fitted curve: a lognormal fit
        # in the deep tail can cross the other branch where no raw point does.
        for p, color, marker in (
            (p_s, fs.STATIC, "o"),
            (p_t, fs.TRANSIENT, "D"),
        ):
            lo, hi = binomial_ci(p, n, 0.95)
            ok = p > 0
            ax.plot(grid[ok], p[ok], color=color, lw=1.3 * scale)
            ax.errorbar(
                grid[ok],
                p[ok],
                yerr=[p[ok] - lo[ok], hi[ok] - p[ok]],
                fmt=marker,
                ms=2.6 * scale,
                color=color,
                mec="white",
                mew=0.4,
                elinewidth=0.8,
                capsize=0,
            )
        ax.set_yscale("log")
        ax.set_ylim(5e-6, 1.6)
        ax.set_xlim(z_toe - 0.5, grid[-1])
        ax.axvline(z_toe, color=fs.MUTED, ls="-.", lw=0.9)
        ax.axvline(DESIGN_HWL[kp], color=fs.INK_2, ls="--", lw=0.9)
        if kp == 62.0:
            fs.mark_hypothetical(ax, ATTAINABLE_MAX[kp], label=False)
        fs.panel_title(ax, f"KP {kp:.1f}", scale=scale)
        ax.set_xlabel("peak stage h  [m T.P.]")
    for ax in axes[:, 0]:
        ax.set_ylabel("P(failure | h)")
    handles = [
        Line2D([], [], color=fs.STATIC, marker="o", lw=1.3 * scale, ms=3 * scale),
        Line2D([], [], color=fs.TRANSIENT, marker="D", lw=1.3 * scale, ms=3 * scale),
        Line2D([], [], color=fs.MUTED, ls="-.", lw=0.9),
        Line2D([], [], color=fs.INK_2, ls="--", lw=0.9),
    ]
    fs.title(fig, "Piping fragility under the two rules", scale=scale)
    fs.legend_below(
        fig,
        handles,
        ["steady state", "time-dependent", "landside toe", "design level"],
        scale=scale,
    )
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, "same_head_fragility_log.png", mirror=mirror)


def _fig_time_factor(fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    ev = _load("event")
    width = fs.TEXTWIDTH_IN * 1.6
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(2, 4, figsize=(width, width * 0.52), sharey="row")
    for j, kp in enumerate(KPS):
        color = fs.SECTION_COLORS[_sec_key(kp)]
        marker = fs.SECTION_MARKERS[_sec_key(kp)]
        levels = [
            lv
            for lv in ev["n1e5"][f"{_label(kp)} matrix"]["levels"]
            if lv["attainable"] and lv["k_C4b"] > 0 and lv["k_C3b"] < 100000
        ]
        x = np.array([lv["stage_m"] for lv in levels])
        q = np.array([bool(lv["time_factor"].get("R1", False)) for lv in levels])
        db = np.array([lv["time_factor"]["dbeta"] or np.nan for lv in levels])
        fr = np.array([lv["time_factor"]["ratio"] or np.nan for lv in levels])
        for row, (vals, key) in enumerate(((db, "dbeta_ci95"), (fr, "ratio_ci95"))):
            ax = axes[row, j]
            ci = [lv["time_factor"].get(key) or [np.nan, np.nan] for lv in levels]
            lo = np.array([c[0] for c in ci])
            hi = np.array([c[1] for c in ci])
            ax.fill_between(x[q], lo[q], hi[q], color=color, alpha=0.18, lw=0)
            ax.plot(x[q], vals[q], color=color, lw=1.4 * scale)
            ax.plot(
                x[q],
                vals[q],
                marker,
                color=color,
                ms=3.2 * scale,
                mec="white",
                mew=0.4,
                ls="none",
            )
            ax.plot(
                x[~q],
                vals[~q],
                marker,
                color=color,
                ms=3.2 * scale,
                mfc="none",
                ls="none",
            )
            ax.axvline(DESIGN_HWL[kp], color=fs.INK_2, ls="--", lw=0.9)
        if _label(kp) in ev["n1e6"]:
            for lv in ev["n1e6"][_label(kp)]["levels"]:
                if round(lv["stage_m"], 2) not in (46.39, 46.5, 39.21, 39.5):
                    continue
                tf = lv["time_factor"]
                if tf.get("R1"):
                    for row, (v, key) in enumerate(
                        (("dbeta", "dbeta_ci95"), ("ratio", "ratio_ci95"))
                    ):
                        lo, hi = tf[key]
                        axes[row, j].errorbar(
                            lv["stage_m"],
                            tf[v],
                            yerr=[[tf[v] - lo], [hi - tf[v]]],
                            fmt="s",
                            ms=4.0 * scale,
                            mfc="white",
                            mec=fs.INK,
                            color=fs.INK,
                            elinewidth=0.9,
                            capsize=2,
                        )
                elif "bounds_union" in lv and round(lv["stage_m"], 2) == 39.21:
                    up = lv["bounds_union"]["dbeta_upper"]
                    axes[0, j].plot(
                        [lv["stage_m"]] * 2, [0.0, up], color=fs.VIOLET, lw=2.2 * scale
                    )
        fs.panel_title(axes[0, j], f"KP {kp:.1f}", scale=scale)
        axes[1, j].set_yscale("log")
        axes[1, j].set_xlabel("peak stage h  [m T.P.]")
    axes[0, 0].set_ylim(0, 1.7)
    axes[1, 0].set_ylim(0.9, 12)
    axes[1, 0].set_yticks([1, 2, 5, 10])
    axes[1, 0].set_yticklabels(["1", "2", "5", "10"])
    axes[0, 0].set_ylabel("index difference Δβ")
    axes[1, 0].set_ylabel("time factor  $P_s/P_t$")
    handles = [
        Line2D([], [], color=fs.MUTED, marker="o", ls="-", ms=3.2 * scale),
        Line2D(
            [], [], color=fs.MUTED, marker="o", mfc="none", ls="none", ms=3.2 * scale
        ),
        Line2D([], [], color=fs.INK, marker="s", mfc="white", ls="none", ms=4 * scale),
        Line2D([], [], color=fs.VIOLET, lw=2.2 * scale),
        Line2D([], [], color=fs.INK_2, ls="--", lw=0.9),
    ]
    labels = [
        "100,000 draws with 95 % paired interval",
        "fewer than 30 time-dependent failures",
        "one million draws",
        "design-level bounds",
        "design level",
    ]
    fs.title(fig, "The effect of finite flood duration against stage", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, "time_factor_vs_stage.png", mirror=mirror)


def _fig_initiation(results_root: Path, fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    width = fs.TEXTWIDTH_IN * 1.5
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(1, 4, figsize=(width, width * 0.30), sharey=True)
    for ax, kp in zip(axes, KPS, strict=True):
        stem = _stem(kp, "matrix")
        run, flags = _cached_flags(results_root / f"{stem}.h5", stem)
        grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
        keep = grid <= ATTAINABLE_MAX[kp] + 1e-9
        trans = np.asarray(run.result.failure_matrix_tran, dtype=bool)
        for vals, color in (
            (flags["gate"].mean(axis=0), fs.VIOLET),
            (flags["C3b"].mean(axis=0), fs.STATIC),
            (trans.mean(axis=0), fs.TRANSIENT),
        ):
            ax.plot(grid[keep], vals[keep], color=color, lw=1.6 * scale)
        ax.axvline(DESIGN_HWL[kp], color=fs.INK_2, ls="--", lw=0.9)
        ax.axvline(PEAK_2016[kp], color=fs.MUTED, ls=":", lw=1.1)
        first = int(np.argmax(flags["gate"].mean(axis=0) > 0))
        ax.set_xlim(grid[max(0, first - 1)], ATTAINABLE_MAX[kp])
        fs.panel_title(ax, f"KP {kp:.1f}", scale=scale)
        ax.set_xlabel("peak stage h  [m T.P.]")
    axes[0].set_ylabel("probability")
    handles = [
        Line2D([], [], color=fs.VIOLET, lw=1.6 * scale),
        Line2D([], [], color=fs.STATIC, lw=1.6 * scale),
        Line2D([], [], color=fs.TRANSIENT, lw=1.6 * scale),
        Line2D([], [], color=fs.INK_2, ls="--", lw=0.9),
        Line2D([], [], color=fs.MUTED, ls=":", lw=1.1),
    ]
    labels = [
        "exit opens at the peak",
        "steady-state failure",
        "time-dependent failure",
        "design level",
        "2016 peak",
    ]
    fs.title(fig, "Initiation and the two piping rules", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, "same_head_initiation.png", mirror=mirror)


def _fig_survival(fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    evd = _load("evidence")
    width = fs.TEXTWIDTH_IN * 1.4
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(1, 2, figsize=(width, width * 0.40))
    for kp in KPS:
        color = fs.SECTION_COLORS[_sec_key(kp)]
        marker = fs.SECTION_MARKERS[_sec_key(kp)]
        rows = evd["hypothetical"][_label(kp)]["levels"]
        x = np.array([r["stage_m"] - DESIGN_HWL[kp] for r in rows])
        surv = np.array([r["LR_one_survival"] or np.nan for r in rows], dtype=float)
        # A breach ratio rests on the time-dependent count: R1 floor.
        brk = np.array(
            [
                (
                    r["LR_one_breach"]
                    if r["LR_one_breach"] and r["P_transient"] * 1e5 >= R1_MIN_TRANSIENT
                    else np.nan
                )
                for r in rows
            ],
            dtype=float,
        )
        ok = np.isfinite(surv)
        axes[0].plot(x[ok], surv[ok], color=color, lw=1.4 * scale)
        ok = np.isfinite(brk)
        axes[1].plot(x[ok], brk[ok], color=color, lw=1.4 * scale)
        lr = evd["per_stratum"][f"{_label(kp)} matrix"]["LR_transient_over_same_head"]
        axes[0].plot(
            PEAK_2016[kp] - DESIGN_HWL[kp],
            lr,
            marker,
            color=color,
            ms=5 * scale,
            mec="white",
            ls="none",
        )
    for ax, letter, text, ticks in (
        (axes[0], "a", "One survival", [1, 2, 5, 10, 20]),
        (axes[1], "b", "One breach", [0.2, 0.3, 0.5, 0.7, 1]),
    ):
        ax.set_yscale("log")
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"{t:g}" for t in ticks])
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        ax.axhline(1.0, color=fs.BASELINE, lw=1.0)
        ax.axvline(0.0, color=fs.INK_2, ls="--", lw=0.9)
        ax.set_xlabel("peak stage relative to the design level  [m]")
        fs.panel_title(ax, text, scale=scale, letter=letter)
    axes[0].set_ylabel("likelihood ratio")
    handles = [
        Line2D(
            [],
            [],
            color=fs.SECTION_COLORS[_sec_key(k)],
            marker=fs.SECTION_MARKERS[_sec_key(k)],
            lw=1.4 * scale,
            ms=4 * scale,
        )
        for k in KPS
    ]
    fs.title(fig, "What one flood outcome says between the two rules", scale=scale)
    fs.legend_below(fig, handles, [f"KP {k:.1f}" for k in KPS], scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, "same_head_survival_evidence.png", mirror=mirror)


def _fig_tokachi_rhine(fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    ev = _load("event")
    pol = _load("polriver")
    width = fs.TEXTWIDTH_IN * 1.4
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(1, 2, figsize=(width, width * 0.42))
    for kp in KPS:
        color = fs.SECTION_COLORS[_sec_key(kp)]
        marker = fs.SECTION_MARKERS[_sec_key(kp)]
        entry = ev["n1e5"][f"{_label(kp)} matrix"]
        lv = [
            v for v in entry["levels"] if v["attainable"] and v["time_factor"].get("R1")
        ]
        ps = np.array([v["k_C3b"] / entry["n"] for v in lv])
        fr = np.array([v["time_factor"]["ratio"] for v in lv])
        db = np.array([v["time_factor"]["dbeta"] for v in lv])
        for ax, y in ((axes[0], fr), (axes[1], db)):
            ax.plot(
                ps,
                y,
                marker,
                color=color,
                ls="-",
                lw=1.2 * scale,
                ms=3.2 * scale,
                mec="white",
                mew=0.4,
            )
    pe = [
        r for r in pol["per_event"] if r["transient_failures_Dp48"] >= R1_MIN_TRANSIENT
    ]
    ps = np.array([r["P_stat"] for r in pe])
    for ax, key in ((axes[0], "F_td_Dp48"), (axes[1], "dbeta_Dp48")):
        y = np.array([np.nan if r[key] is None else r[key] for r in pe], dtype=float)
        ax.plot(ps, y, color=fs.INK, ls="-", lw=1.8 * scale, marker="x", ms=3.5 * scale)
    for ax, letter, text in (
        (axes[0], "a", "Time factor"),
        (axes[1], "b", "Index difference"),
    ):
        ax.set_xscale("log")
        ax.set_xlabel("steady-state failure probability per flood")
        fs.panel_title(ax, text, scale=scale, letter=letter)
    axes[0].set_yscale("log")
    axes[0].set_yticks([1, 2, 5, 10])
    axes[0].set_yticklabels(["1", "2", "5", "10"])
    axes[0].set_ylabel("$P_s/P_t$")
    axes[1].set_ylabel("Δβ")
    handles = [
        Line2D(
            [],
            [],
            color=fs.SECTION_COLORS[_sec_key(k)],
            marker=fs.SECTION_MARKERS[_sec_key(k)],
            lw=1.2 * scale,
            ms=3.5 * scale,
        )
        for k in KPS
    ] + [Line2D([], [], color=fs.INK, marker="x", lw=1.8 * scale, ms=3.5 * scale)]
    labels = [f"KP {k:.1f}" for k in KPS] + ["Dutch river base case, 48 h peak"]
    fs.title(fig, "Tokachi and a Dutch river levee per flood", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, "time_factor_tokachi_rhine.png", mirror=mirror)


def _fig_knobs(fs, mirror: Path) -> Path:
    """Model factor and exit datum on each rule separately (thesis Figure C.4).

    Replaces ``epistemic_knobs_mp_ztoe.png``, whose static panels are the
    gross-head rule. Only count-qualified stages are drawn: at least 30
    failures and 30 survivors in both the arm and the adopted sample.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    brackets = _load("brackets")
    n = 100_000
    width = fs.TEXTWIDTH_IN * 1.5
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(2, 2, figsize=(width, width * 0.62), sharex=True)
    panels = (
        (axes[0, 0], ("m_p",), 0, "Model factor, steady state", "a"),
        (axes[0, 1], ("m_p",), 1, "Model factor, time-dependent", "b"),
        (
            axes[1, 0],
            ("z_toe_minus0.30m", "z_toe_plus0.30m"),
            0,
            "Exit datum, steady state",
            "c",
        ),
        (
            axes[1, 1],
            ("z_toe_minus0.30m", "z_toe_plus0.30m"),
            1,
            "Exit datum, time-dependent",
            "d",
        ),
    )
    for ax, arm_keys, branch, title, letter in panels:
        for kp in KPS:
            color = fs.SECTION_COLORS[_sec_key(kp)]
            marker = fs.SECTION_MARKERS[_sec_key(kp)]
            for arm_key in arm_keys:
                x, y = [], []
                for lv in brackets[_label(kp)][arm_key]["time_factor"]["levels"]:
                    base, arm = lv["cells"][branch], lv["cells"][2 + branch]
                    if min(base, arm) >= R1_MIN_TRANSIENT and max(base, arm) <= n - 30:
                        x.append(lv["stage_m"])
                        y.append(arm / base)
                ax.plot(
                    x,
                    y,
                    marker,
                    color=color,
                    ls="--" if arm_key == "z_toe_plus0.30m" else "-",
                    lw=1.2 * scale,
                    ms=2.8 * scale,
                    mec="white",
                    mew=0.3,
                )
        ax.axhline(1.0, color=fs.MUTED, lw=0.8)
        ax.set_yscale("log")
        ticks = [1, 1.5, 2, 2.5] if arm_keys == ("m_p",) else [0.1, 0.3, 1, 3, 10, 30]
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"{t:g}" for t in ticks])
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        fs.panel_title(ax, title, scale=scale, letter=letter)
    for ax in axes[1]:
        ax.set_xlabel("peak stage h  [m T.P.]")
    for ax in axes[:, 0]:
        ax.set_ylabel("P(arm) / P(adopted)")
    handles = [
        Line2D(
            [],
            [],
            color=fs.SECTION_COLORS[_sec_key(k)],
            marker=fs.SECTION_MARKERS[_sec_key(k)],
            lw=1.2 * scale,
            ms=3.2 * scale,
        )
        for k in KPS
    ] + [
        Line2D([], [], color=fs.INK_2, ls="-", lw=1.2 * scale),
        Line2D([], [], color=fs.INK_2, ls="--", lw=1.2 * scale),
    ]
    labels = [f"KP {k:.1f}" for k in KPS] + [
        "datum 0.30 m lower",
        "datum 0.30 m higher",
    ]
    fs.title(fig, "Model factor and exit datum on each rule", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, "same_head_mp_ztoe.png", mirror=mirror)


def figures_part(results_root: Path) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as fs

    mirror = OUT_DIR / "figures"
    written = [
        _fig_fragility(results_root, fs, mirror),
        _fig_time_factor(fs, mirror),
        _fig_initiation(results_root, fs, mirror),
        _fig_survival(fs, mirror),
        _fig_tokachi_rhine(fs, mirror),
        _fig_knobs(fs, mirror),
    ]
    return {"figures": [str(p.relative_to(REPO)).replace("\\", "/") for p in written]}


# --------------------------------------------------------------------------- #
# Part: larms                                                                   #
# --------------------------------------------------------------------------- #
def larms_part(n_jobs: int) -> dict[str, Any]:
    """Re-run the four ADR-0047 seepage-length arms and persist them locally.

    Same in-memory override as ``dem_cross_section_study._run_arm``: the YAML
    is loaded, ``geometry.L`` replaced and the result re-validated; the on-disk
    config is never written. Persisted under the gitignored worktree results so
    the ``brackets`` part can pair them row for row with production.
    """
    from bep_reliability_engine.run import run_fragility_analysis

    arm_dir = OUT_DIR / "l_arms"
    arm_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = {}
    for kp, (name, value) in L_ARMS.items():
        path = arm_dir / f"{_stem(kp, 'matrix')}_{name}.h5"
        if path.is_file():
            out[_label(kp)] = {"arm": name, "L_m": value, "path": str(path)}
            continue
        data = yaml.safe_load(_cfg_path(kp, "matrix").read_text(encoding="utf-8"))
        data["geometry"]["L"] = float(value)
        config = Config.model_validate(data)
        tick = time.time()
        run_fragility_analysis(
            config, n_jobs=n_jobs, progress=False, output_path=path, overwrite=False
        )
        out[_label(kp)] = {
            "arm": name,
            "L_m": value,
            "path": str(path),
            "runtime_s": round(time.time() - tick, 1),
        }
        print(f"  L arm {_label(kp)} {name} = {value} m: done", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: uarms                                                                   #
# --------------------------------------------------------------------------- #
UNIFORMITY_ARMS = ("cap", "sand", "matrix")


def uarms_part(n_jobs: int) -> dict[str, Any]:
    """Re-run the Green Light item 1 uniformity arms and persist them locally.

    The arm definition (an exact multiplier on H_c through the bedding angle)
    is imported from ``uniformity_coefficient_study``, never re-derived, so the
    arms cannot drift from the ones that study reported.
    """
    import importlib.util

    from bep_reliability_engine.run import run_fragility_analysis

    path = REPO / "scripts" / "uniformity_coefficient_study.py"
    spec = importlib.util.spec_from_file_location("uniformity_coefficient_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    factors = module.arm_factors()
    arm_dir = OUT_DIR / "u_arms"
    arm_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = {}
    for arm in UNIFORMITY_ARMS:
        for kp in KPS:
            spec_kp = factors[arm][f"{kp:.1f}"]
            target = arm_dir / f"{_stem(kp, 'matrix')}_cu_{arm}.h5"
            out[f"{_label(kp)} {arm}"] = {**spec_kp, "path": str(target)}
            if target.is_file():
                continue
            data = yaml.safe_load(_cfg_path(kp, "matrix").read_text(encoding="utf-8"))
            data["theta_repose_deg"] = float(spec_kp["theta_repose_deg"])
            tick = time.time()
            run_fragility_analysis(
                Config.model_validate(data),
                n_jobs=n_jobs,
                progress=False,
                output_path=target,
                overwrite=False,
            )
            out[f"{_label(kp)} {arm}"]["runtime_s"] = round(time.time() - tick, 1)
            print(f"  uniformity arm {_label(kp)} {arm}: done", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: rehalf                                                                  #
# --------------------------------------------------------------------------- #
def rehalf_part(results_root: Path) -> dict[str, Any]:
    """The thesis's halved-r_e test, read on the same-head comparator.

    r_e enters only the gate head (ADR-0028), so halving it is the ADR-0050
    relief factor 0.5 on the gate and nothing else. The transient side of this
    test is the published one; only the gate and C3b are new here.
    """
    stem = _stem(58.8, "matrix")
    run, base = _cached_flags(results_root / f"{stem}.h5", stem)
    half = same_head_flags(run, relief_override=0.5)
    grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
    levels = [
        {
            "stage_m": float(h),
            "gate_base": float(base["gate"][:, i].mean()),
            "gate_half": float(half["gate"][:, i].mean()),
            "P_same_head_base": float(base["C3b"][:, i].mean()),
            "P_same_head_half": float(half["C3b"][:, i].mean()),
            "new_same_head_failures": int(
                (half["C3b"][:, i] & ~base["C3b"][:, i]).sum()
            ),
        }
        for i, h in enumerate(grid)
    ]
    return {"section": "KP 58.8 matrix", "relief_equivalent": 0.5, "levels": levels}


# --------------------------------------------------------------------------- #
# Part: report                                                                  #
# --------------------------------------------------------------------------- #
def _round(obj: Any, sig: int = 6) -> Any:
    """Round floats to ``sig`` significant figures, recursively."""
    if isinstance(obj, float):
        if not np.isfinite(obj) or obj == 0.0:
            return obj
        return float(f"{obj:.{sig}g}")
    if isinstance(obj, dict):
        return {k: _round(v, sig) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, sig) for v in obj]
    return obj


def _load(part: str) -> dict[str, Any]:
    """A stage file if present, else that part of the committed evidence."""
    path = OUT_DIR / f"stage_{part}.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))[part]


def _severity(ev: dict[str, Any]) -> dict[str, Any]:
    """Per-section summary of the time factor over attainable R1 levels."""
    out = {}
    for kp in KPS:
        entry = ev["n1e5"][f"{_label(kp)} matrix"]
        n = entry["n"]
        q = [
            lv
            for lv in entry["levels"]
            if lv["attainable"] and lv["time_factor"].get("R1")
        ]
        top = q[-1]
        out[_label(kp)] = {
            "n_levels_R1": len(q),
            "lowest_R1_stage_m": q[0]["stage_m"],
            "ratio_at_lowest_R1": q[0]["time_factor"]["ratio"],
            "dbeta_at_lowest_R1": q[0]["time_factor"]["dbeta"],
            "ratio_max_R1": max(lv["time_factor"]["ratio"] for lv in q),
            "top_stage_m": top["stage_m"],
            "ratio_at_top": top["time_factor"]["ratio"],
            "dbeta_at_top": top["time_factor"]["dbeta"],
            "survival_same_head_at_top": 1 - top["k_C3b"] / n,
            "survival_transient_at_top": 1 - top["k_C4b"] / n,
            "dbeta_min_R1": min(lv["time_factor"]["dbeta"] for lv in q),
            "dbeta_max_R1": max(lv["time_factor"]["dbeta"] for lv in q),
        }
    return out


def _anchors(ev: dict[str, Any]) -> dict[str, Any]:
    """The design-level anchors in the thesis's Table 5.1 layout."""
    rows = {}
    picks = (
        ("KP 57.4 design", "n1e6", "KP 57.4", 39.21),
        ("KP 57.4 resolved", "n1e6", "KP 57.4", 39.5),
        ("KP 58.8 design grid", "n1e5", "KP 58.8 matrix", 41.0),
        ("KP 60.0 design", "n1e5", "KP 60.0 matrix", 42.75),
        ("KP 62.0 design", "n1e6", "KP 62.0", 46.39),
        ("KP 62.0 nearest grid", "n1e6", "KP 62.0", 46.5),
    )
    for name, block, key, stage in picks:
        entry = ev[block][key]
        n = entry["n"]
        lv = next(v for v in entry["levels"] if abs(v["stage_m"] - stage) < 1e-6)
        rows[name] = {
            "N": n,
            "stage_m": stage,
            "P_same_head": lv["k_C3b"] / n,
            "P_transient": lv["k_C4b"] / n,
            "P_gross_static": lv["k_C0"] / n,
            "k_same_head": lv["k_C3b"],
            "k_transient": lv["k_C4b"],
            "k_gross_static": lv["k_C0"],
            "time_factor": lv["time_factor"],
            "gross_static_vs_transient": {
                k: lv["gross_static_vs_transient"].get(k) for k in ("ratio", "dbeta")
            },
            "gross_static_vs_same_head": {
                k: lv["gross_static_vs_same_head"].get(k) for k in ("ratio", "dbeta")
            },
            **({"bounds_union": lv["bounds_union"]} if "bounds_union" in lv else {}),
            **(
                {
                    "scale_transient_only": lv["scale_transient_only"],
                    "scale_symmetric": lv["scale_symmetric"],
                }
                if "scale_transient_only" in lv
                else {}
            ),
        }
    return rows


#: Arms whose per-branch ratios the thesis quotes beside the paired metrics.
SINGLE_BRANCH_ARMS = ("m_p", "z_toe_minus0.30m", "z_toe_plus0.30m")
#: The drained-section ladder of thesis Table C.6, at the design-grid stages.
DRAINED_LADDER = (
    ("as if undrained", None),
    ("measured berm, inert drain", "berm_only"),
    ("berm, 20 % relief", "berm_relief_20pct"),
    ("berm, 40 % relief", "berm_relief_40pct"),
    ("berm, 60 % relief", "berm_relief_60pct"),
    ("berm, 80 % relief", "berm_relief_80pct"),
)
DESIGN_GRID = {57.4: 39.25, 58.8: 41.0, 60.0: 42.75, 62.0: 46.5}


def _level(arm: dict[str, Any], stage: float) -> dict[str, Any]:
    return next(
        lv for lv in arm["time_factor"]["levels"] if abs(lv["stage_m"] - stage) < 1e-6
    )


def _pair_from_counts(k_s: int, k_t: int, n: int) -> dict[str, Any]:
    """F_td and Delta-beta from the two branch counts of one arm and level."""
    return {
        "k_same_head": k_s,
        "k_transient": k_t,
        "P_transient": k_t / n,
        "time_factor": k_s / k_t if k_t else None,
        "dbeta": (
            float(_beta(k_t / n) - _beta(k_s / n)) if 0 < k_t and k_s < n else None
        ),
    }


def _derived(ev: dict[str, Any], brackets: dict[str, Any]) -> dict[str, Any]:
    """Values the thesis quotes that are functions of the stored counts only."""
    n = 100_000
    # Pairing: variance of Delta-beta for independent over paired samples, by
    # the delta method on the four joint cells, at attainable R1 matrix levels.
    gains = []
    for kp in KPS:
        for lv in ev["n1e5"][f"{_label(kp)} matrix"]["levels"]:
            tf = lv["time_factor"]
            if not (lv["attainable"] and tf.get("R1") and tf["dbeta"] is not None):
                continue
            pa, pb = tf["k_a"] / tf["n"], tf["k_b"] / tf["n"]
            p11 = (tf["k_b"] - tf["b_not_a"]) / tf["n"]
            ga = 1.0 / norm.pdf(norm.isf(pa))
            gb = 1.0 / norm.pdf(norm.isf(pb))
            ind = ga**2 * pa * (1 - pa) + gb**2 * pb * (1 - pb)
            par = ind - 2 * ga * gb * (p11 - pa * pb)
            gains.append((ind / par, _label(kp), lv["stage_m"]))
    lo, hi = min(gains), max(gains)
    out: dict[str, Any] = {
        "pairing_variance_gain": {
            "n_levels": len(gains),
            "min": lo[0],
            "min_at": [lo[1], lo[2]],
            "max": hi[0],
            "max_at": [hi[1], hi[2]],
        }
    }
    # Per-branch ratios arm/base where both arms have >= 30 failures and
    # >= 30 survivors, attainable stages (thesis C.3 model-factor paragraph).
    single: dict[str, Any] = {}
    for arm_key in SINGLE_BRANCH_ARMS:
        for kp in KPS:
            rs, rt = [], []
            for lv in brackets[_label(kp)][arm_key]["time_factor"]["levels"]:
                bs, bt, a_s, a_t = lv["cells"]
                if min(bs, a_s) >= R1_MIN_TRANSIENT and max(bs, a_s) <= n - 30:
                    rs.append(a_s / bs)
                if min(bt, a_t) >= R1_MIN_TRANSIENT and max(bt, a_t) <= n - 30:
                    rt.append(a_t / bt)
            single[f"{_label(kp)} {arm_key}"] = {
                "same_head_ratio_min": min(rs, default=None),
                "same_head_ratio_max": max(rs, default=None),
                "transient_ratio_min": min(rt, default=None),
                "transient_ratio_max": max(rt, default=None),
            }
    out["single_branch_ratios"] = single
    # Drained ladder at the design-grid stages.
    ladder: dict[str, Any] = {}
    for kp in (58.8, 60.0):
        rows = {}
        for name, arm_key in DRAINED_LADDER:
            lv = _level(brackets[_label(kp)]["berm_only"], DESIGN_GRID[kp])
            k_s, k_t = (lv["cells"][0], lv["cells"][1])
            if arm_key is not None:
                lv = _level(brackets[_label(kp)][arm_key], DESIGN_GRID[kp])
                k_s, k_t = lv["cells"][2], lv["cells"][3]
                rows[name] = {
                    **_pair_from_counts(k_s, k_t, n),
                    "dbeta_displacement": lv.get("dbeta_displacement"),
                    "dbeta_displacement_ci95": lv.get("dbeta_displacement_ci95"),
                }
            else:
                rows[name] = _pair_from_counts(k_s, k_t, n)
        ladder[f"{_label(kp)} {DESIGN_GRID[kp]:.2f} m"] = rows
    out["drained_ladder"] = ladder
    # Every KP 62.0 arm at 46.75 m, the first grid stage above the 46.39 m
    # design level with at least 30 transient failures in the adopted sample.
    kp62 = {}
    for arm_key, arm in brackets["KP 62.0"].items():
        if not (isinstance(arm, dict) and arm.get("available")):
            continue
        cells = _level(arm, 46.75)["cells"]
        kp62.setdefault("adopted", _pair_from_counts(cells[0], cells[1], n))
        kp62[arm_key] = _pair_from_counts(cells[2], cells[3], n)
    out["kp62_arms_46.75m"] = kp62
    # Uniformity arms: summary over the four sections, and Delta-beta at the
    # two drained design-grid stages.
    unif = {}
    for arm_key in ("cu_cap", "cu_sand", "cu_matrix"):
        summ = [
            brackets[_label(kp)][arm_key]["time_factor"]["summary_R1"] for kp in KPS
        ]
        design = {}
        for kp in (58.8, 60.0):
            cells = _level(brackets[_label(kp)][arm_key], DESIGN_GRID[kp])["cells"]
            design[_label(kp)] = _pair_from_counts(cells[2], cells[3], n)
        unif[arm_key] = {
            "time_factor_ratio_min": min(s["rho_min"] for s in summ),
            "time_factor_ratio_max": max(s["rho_max"] for s in summ),
            "dbeta_displacement_min": min(s["dbeta_displacement_min"] for s in summ),
            "dbeta_displacement_max": max(s["dbeta_displacement_max"] for s in summ),
            "design_grid": design,
        }
    out["uniformity"] = unif
    return out


#: Per-level pair fields the evidence keeps; n, k_a, k_b and the widths are
#: the level's own counts or follow from the kept interval.
PAIR_KEEP = ("b_not_a", "ratio", "dbeta", "ratio_ci95", "dbeta_ci95", "R1")


def _slim_event(ev: dict[str, Any]) -> dict[str, Any]:
    """Drop levels nothing fails at and fields recoverable from the counts."""
    out = {"n1e5": {}, "n1e6": {}}
    for block in ("n1e5", "n1e6"):
        for key, entry in ev[block].items():
            levels = []
            for lv in entry["levels"]:
                if lv["k_C0"] == 0:
                    continue
                slim = {k: v for k, v in lv.items() if not isinstance(v, dict)}
                for k, v in lv.items():
                    if isinstance(v, dict):
                        slim[k] = (
                            {kk: v[kk] for kk in PAIR_KEEP if kk in v}
                            if "b_not_a" in v
                            else v
                        )
                levels.append(slim)
            out[block][key] = {**entry, "levels": levels}
    return out


def report_part() -> dict[str, Any]:
    ev = _load("event")
    brackets = _load("brackets")
    derived = _derived(ev, brackets)
    anchors, severity = _anchors(ev), _severity(ev)
    for section in brackets.values():
        if not isinstance(section, dict):
            continue
        for arm in section.values():
            if isinstance(arm, dict) and "path" in arm:
                arm["path"] = Path(arm["path"]).name
            if isinstance(arm, dict) and "gross_ratio_reproduction" in arm:
                # The floor-10 summary is what the reproduction gate compares.
                arm["gross_ratio_reproduction"].pop("summary_R1", None)
    for kp_key, section in brackets.items():
        if not isinstance(section, dict):
            continue
        for arm in section.values():
            if isinstance(arm, dict) and "time_factor" in arm:
                arm["time_factor"]["levels"] = [
                    {
                        k: lv.get(k)
                        for k in (
                            "stage_m",
                            "cells",
                            "rho",
                            "rho_lo",
                            "rho_hi",
                            "resolved",
                            "dbeta_displacement",
                            "dbeta_displacement_ci95",
                        )
                        if k in lv
                    }
                    for lv in arm["time_factor"]["levels"]
                    if max(lv["cells"]) > 0
                ]
                # Four significant figures per level: the summaries and the
                # quoted values are computed above at full precision.
                arm["time_factor"]["levels"] = _round(arm["time_factor"]["levels"], 4)
    annual = _load("annual")
    for d70 in D70S:
        annual[d70]["paired_comparisons"] = {
            k: v
            for k, v in annual[d70]["paired_comparisons"].items()
            if k
            in (
                "I-prior / T-prior",
                "I-post / T-post",
                "I-post-fit / T-post",
                "I-prior-raw / T-prior-raw",
                "I-post / T-post-raw",
            )
        }
    annual["fit_checks"] = {
        k: {
            kk: v[kk]
            for kk in (
                "fit_used",
                "max_abs_deviation_from_raw",
                "levels_outside_binomial_ci",
            )
        }
        for k, v in annual["fit_checks"].items()
    }
    record = {
        "study": "The time-dependence factor on one head and one initiation gate "
        "(Pol comments 1 and 2)",
        "adr": "ADR-0055",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "generated_by": "scripts/time_dependence_factor_study.py",
        "note": "docs/decisions/time-dependence-factor-study.md",
        "definitions": {
            "same_head_static": "C3b: gate open at the peak and h_peak - z_toe - "
            "0.3 D_bl > H_c (instantaneous growth on the transient model's own "
            "head and gate)",
            "time_factor": "P(C3b) / P(C4b), Pol et al. (2024) F_td per event",
            "dbeta": "beta(C4b) - beta(C3b)",
            "gross_static": "C0, the persisted production static branch "
            "(Sellmeijer's gross head, no gate)",
            "R1": f"at least {R1_MIN_TRANSIENT} transient failures",
            "R2": f"ratio interval width factor at most {R2_MAX_WIDTH}",
            "R2beta": f"index interval width at most {R2_BETA_MAX_WIDTH}",
        },
        "design_anchors": anchors,
        "severity": severity,
        "derived": derived,
        "halved_r_e": _load("rehalf"),
        "event": _slim_event(ev),
        "brackets": brackets,
        "evidence": _load("evidence"),
        "annual": annual,
        "timescale": _load("timescale"),
        "polriver": _load("polriver"),
        "seepage_length_arms": _load("larms"),
        "uniformity_arms": _load("uarms"),
    }
    record = _round(record)
    text = json.dumps(record, indent=None, separators=(",", ":"))
    EVIDENCE.write_text(text + "\n", encoding="utf-8")
    return {"evidence": str(EVIDENCE), "bytes": len(text)}


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "part",
        choices=[
            "event",
            "larms",
            "brackets",
            "evidence",
            "annual",
            "timescale",
            "polriver",
            "uarms",
            "rehalf",
            "figures",
            "report",
        ],
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=REPO / "results",
        help="Directory holding the production results (read-only).",
    )
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--replicates", type=int, default=10_000)
    parser.add_argument("--pol-n", type=int, default=100_000)
    args = parser.parse_args(argv)
    started = time.time()
    if args.part == "larms":
        payload = larms_part(args.n_jobs)
    elif args.part == "event":
        payload = event_part(args.results_root)
    elif args.part == "brackets":
        payload = brackets_part(args.results_root)
    elif args.part == "evidence":
        payload = evidence_part(args.results_root)
    elif args.part == "annual":
        payload = annual_part(args.results_root, args.replicates)
    elif args.part == "timescale":
        payload = timescale_part(args.results_root)
    elif args.part == "polriver":
        payload = polriver_part(args.pol_n)
    elif args.part == "figures":
        payload = figures_part(args.results_root)
    elif args.part == "uarms":
        payload = uarms_part(args.n_jobs)
    elif args.part == "rehalf":
        payload = rehalf_part(args.results_root)
    elif args.part == "report":
        print(report_part())
        return 0
    else:
        raise SystemExit(f"part {args.part!r} not implemented yet")
    payload["elapsed_s"] = round(time.time() - started, 1)
    print(_write_stage(args.part, payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
