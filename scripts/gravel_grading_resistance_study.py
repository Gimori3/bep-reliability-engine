"""What extra piping resistance from grading or gravel would change (Pol 4 and 5).

Driver for ``docs/decisions/gravel-grading-resistance-study.md``. Companion
study: no production default, config, prior, kernel, persisted sweep, posterior
or annual result changes.

Pol's comments 4 and 5 on the pre-Green-Light thesis: both models are derived
for sand, Dutch practice multiplies the Sellmeijer critical head by 1.8 for
gravel, and experiments show the critical head rising strongly with d60/d10.
This driver measures what an exact multiplier ``c`` on the single-source H_c
does to every answer of the thesis, on the comparator of record (ADR-0055,
same head and same gate):

``arms``      Phase 1 sweeps for ``c`` in ``LADDER`` at the four sections,
              matrix reading, through the bedding angle (theta enters F_r and
              nothing else, so H_c scales by exactly ``c`` in both criteria);
              persisted under the gitignored ``results/gravel_grading/arms``.
``replay``    the 2016 survival replay of every arm with the production Phase 2
              settings (read from the production sidecar, never retyped).
``event``     per-event probabilities, the time-dependence factor and index
              difference, the 2016 rejection, initiation and likelihood ratio,
              for the baseline and every arm; gates (i) H_c ratio and (ii) the
              persisted static column.
``annual``    each arm's prior and posterior transient curves and its same-head
              prior curve through the production Phase 3 annualisation, with
              the member-block bootstrap; gate (iii) the production table.
``resistant`` the material-side numbers sessions 3 and 4 need, read from the
              persisted conductivity, bulk and berm replays.
``figures``   the thesis figure (docs/figures/), house style.
``report``    assemble ``docs/decisions/gravel-grading-resistance-study.json``.

Usage (from the worktree root, main venv, ``PYTHONPATH=.``)::

    python scripts/gravel_grading_resistance_study.py arms --n-jobs 10
    python scripts/gravel_grading_resistance_study.py replay
    python scripts/gravel_grading_resistance_study.py event
    python scripts/gravel_grading_resistance_study.py annual
    python scripts/gravel_grading_resistance_study.py resistant
    python scripts/gravel_grading_resistance_study.py figures
    python scripts/gravel_grading_resistance_study.py report
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import yaml
from numpy.typing import NDArray

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bep_reliability_engine.config import Config  # noqa: E402


def _load_module(name: str):
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The ADR-0055 driver supplies the comparator, the paired statistics and the
#: section constants; the uniformity driver supplies the exact H_c multiplier.
#: Imported, never restated, so the arms cannot drift from those studies.
tdf = _load_module("time_dependence_factor_study")
ucs = _load_module("uniformity_coefficient_study")

KPS = tdf.KPS
DESIGN_HWL = tdf.DESIGN_HWL
ATTAINABLE_MAX = tdf.ATTAINABLE_MAX
DESIGN_GRID = tdf.DESIGN_GRID
PEAK_2016 = tdf.PEAK_2016
R1 = tdf.R1_MIN_TRANSIENT
SEED = 20261007

#: Multipliers on H_c. 1.8 is the Dutch gravel reading (the named alternative).
LADDER: tuple[float, ...] = (1.25, 1.5, 1.8, 2.2, 2.7)
DUTCH_GRAVEL = 1.8

OUT_DIR = REPO / "results" / "gravel_grading"
ARM_DIR = OUT_DIR / "arms"
PHASE2_OUT = OUT_DIR / "phase2"
EVIDENCE = REPO / "docs" / "decisions" / "gravel-grading-resistance-study.json"


def _stem(kp: float, d70: str = "matrix") -> str:
    return tdf._stem(kp, d70)


def _label(kp: float) -> str:
    return tdf._label(kp)


def _ckey(c: float) -> str:
    return f"x{c:.2f}"


def arm_path(kp: float, c: float) -> Path:
    return ARM_DIR / f"{_stem(kp)}_hc_{_ckey(c)}.h5"


def arm_posterior_path(kp: float, c: float) -> Path:
    return PHASE2_OUT / f"{_stem(kp)}_hc_{_ckey(c)}_posterior.h5"


def theta_for(c: float) -> float:
    """Bedding angle [deg] that scales F_r, hence H_c, by exactly ``c``."""
    return float(ucs.theta_for_factor(c))


def _write_stage(part: str, payload: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"stage_{part}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def _read_stage(part: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / f"stage_{part}.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Part: arms                                                                    #
# --------------------------------------------------------------------------- #
def arms_part(n_jobs: int) -> dict[str, Any]:
    """Phase 1 sweeps of the ladder, in-memory config override, persisted locally."""
    from bep_reliability_engine.run import run_fragility_analysis

    ARM_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = {}
    for c in LADDER:
        for kp in KPS:
            target = arm_path(kp, c)
            entry = {"c": c, "theta_repose_deg": theta_for(c), "path": str(target)}
            out[f"{_label(kp)} {_ckey(c)}"] = entry
            if target.is_file():
                continue
            data = yaml.safe_load(tdf._cfg_path(kp, "matrix").read_text("utf-8"))
            data["theta_repose_deg"] = theta_for(c)
            tick = time.time()
            run_fragility_analysis(
                Config.model_validate(data),
                n_jobs=n_jobs,
                progress=False,
                output_path=target,
                overwrite=False,
            )
            entry["runtime_s"] = round(time.time() - tick, 1)
            print(f"  {_label(kp)} H_c x {c}: {entry['runtime_s']} s", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: replay                                                                  #
# --------------------------------------------------------------------------- #
#: Settings this driver legitimately changes against production: where the
#: posterior is written, and the breach-time trace (a plotted diagnostic that
#: cannot reach the accept mask; the ADR-0048 and ADR-0050 replay drivers
#: record the same exemption).
_OVERRIDDEN = frozenset({"output_dir", "trace_breach_times"})


def phase2_settings(results_root: Path):
    from bayesian_reliability_updating.pipeline import Phase2Settings

    sidecar = results_root / "phase2" / f"{_stem(58.8)}_posterior.json"
    reference = json.loads(sidecar.read_text(encoding="utf-8"))["phase2"]["settings"]
    settings = Phase2Settings(
        anchor=reference["anchor"],
        criterion=reference["criterion"],
        data_root=reference["data_root"],
        processed_dir=reference["processed_dir"],
        output_dir=str(PHASE2_OUT),
        verify_by_reevaluation=reference["verify_by_reevaluation"],
        trace_breach_times=False,
        figures=reference["figures"],
        n_bootstrap=reference["n_bootstrap"],
        confidence=reference["confidence"],
        progression_backend=reference["progression_backend"],
        overwrite=False,
        z_toe_delta_m=reference["z_toe_delta_m"],
    )
    drift = sorted(
        f
        for f, v in reference.items()
        if f not in _OVERRIDDEN and getattr(settings, f, object()) != v
    )
    if drift:
        raise SystemExit(f"Phase 2 settings drift against production in {drift}")
    return settings


def replay_part(results_root: Path) -> dict[str, Any]:
    from bayesian_reliability_updating.pipeline import run_survival_update

    PHASE2_OUT.mkdir(parents=True, exist_ok=True)
    settings = phase2_settings(results_root)
    out: dict[str, Any] = {}
    for c in LADDER:
        for kp in KPS:
            target = arm_posterior_path(kp, c)
            key = f"{_label(kp)} {_ckey(c)}"
            if not target.is_file():
                tick = time.time()
                run_survival_update(arm_path(kp, c), settings=settings)
                print(f"  replay {key}: {time.time() - tick:.0f} s", flush=True)
            meta = json.loads(target.with_suffix(".json").read_text(encoding="utf-8"))
            out[key] = meta["phase2"]["posterior"]
    return out


# --------------------------------------------------------------------------- #
# Part: event                                                                   #
# --------------------------------------------------------------------------- #
def _hc(run) -> NDArray[np.float64]:
    """The single-source H_c of every row (stage-independent; one M8 call)."""
    from bep_reliability_engine.evaluator import evaluate_batch_diagnostics
    from bep_reliability_engine.gap_decomposition import sustained_peak_record

    cfg = run.config
    level = float(np.asarray(run.result.conditioning_grid)[0])
    diag = evaluate_batch_diagnostics(
        run.theta,
        sustained_peak_record(level, dt_s=float(cfg.timestepper.target_dt_seconds)),
        run.geometry,
        l_ini=0.0,
        seepage_length_samples=run.seepage_length_samples,
        alpha_exponent=cfg.alpha_exponent,
        theta_repose_rad=cfg.theta_repose_rad,
        relative_density=cfg.relative_density_insitu,
        foreland_open=cfg.foreland_treatment == "open_entry",
        progression_backend="numpy",
        model_factor_samples=run.model_factor_samples,
        critical_length_factor=cfg.critical_length_factor,
        toe_gradient_relief_factor=cfg.toe_gradient_relief_factor,
        foreland_seepage_credit=cfg.foreland_seepage_credit,
    )
    return np.asarray(diag.H_c, dtype=np.float64)


def _flags(path: Path, key: str):
    """Load a run and its C0 / C3b / gate flags, cached under this study."""
    from bayesian_reliability_updating.replay import load_phase1_run

    run = load_phase1_run(path)
    cache = OUT_DIR / "cache" / f"{key}.npz"
    if cache.is_file():
        with np.load(cache) as data:
            flags = {k: data[k] for k in ("C0", "C1", "C3b", "gate", "H_c")}
        if np.array_equal(flags["C0"], run.result.failure_matrix_stat):
            return run, flags
    flags = tdf.same_head_flags(run)  # gate (ii) inside
    flags["H_c"] = _hc(run)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **flags)
    return run, flags


def _replay(path: Path) -> dict[str, NDArray]:
    return tdf._replay_arrays(path)


def _evidence_2016(a: dict[str, NDArray]) -> dict[str, Any]:
    t = a["accept_trans"]
    s = tdf._same_head_survival(a)
    g = a["accept_static"]
    pt, ps = float(t.mean()), float(s.mean())
    return {
        "rejected_transient": 1.0 - pt,
        "rejected_same_head": 1.0 - ps,
        "rejected_gross_static": 1.0 - float(g.mean()),
        "initiated_2016": float(a["initiation"].mean()),
        "LR_transient_over_same_head": pt / ps if ps > 0 else None,
        "same_head_survivors_failing_transient": int(np.sum(s & ~t)),
        "n_rejected_transient": int((~t).sum()),
    }


def _levels(run, flags) -> list[dict[str, Any]]:
    grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
    tran = np.asarray(run.result.failure_matrix_tran, dtype=bool)
    rows = []
    for i, h in enumerate(grid):
        pair = tdf.paired_pair(flags["C3b"][:, i], tran[:, i], SEED + i)
        rows.append(
            {
                "stage_m": float(h),
                "k_T": int(tran[:, i].sum()),
                "k_I": int(flags["C3b"][:, i].sum()),
                "k_C0": int(flags["C0"][:, i].sum()),
                "gate_open": float(flags["gate"][:, i].mean()),
                "time_factor": {
                    k: pair.get(k)
                    for k in ("ratio", "dbeta", "ratio_ci95", "dbeta_ci95", "R1")
                },
            }
        )
    return rows


def event_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"sections": {}, "gates": {}}
    for kp in KPS:
        stem = _stem(kp)
        base_run, base = _flags(results_root / f"{stem}.h5", f"{stem}_base")
        base_tran = np.asarray(base_run.result.failure_matrix_tran, dtype=bool)
        grid = np.asarray(base_run.result.conditioning_grid, dtype=np.float64)
        base_ev = _evidence_2016(
            _replay(results_root / "phase2" / f"{stem}_posterior.h5")
        )
        base_init = _replay(results_root / "phase2" / f"{stem}_posterior.h5")[
            "initiation"
        ]
        sec: dict[str, Any] = {
            "grid_m": grid.tolist(),
            "attainable_max_m": ATTAINABLE_MAX[kp],
            "design_level_m": DESIGN_HWL[kp],
            "design_grid_m": DESIGN_GRID[kp],
            "peak_2016_m": PEAK_2016[kp],
            "arms": {
                "x1.00": {
                    "c": 1.0,
                    "levels": _levels(base_run, base),
                    "evidence_2016": base_ev,
                }
            },
        }
        for c in LADDER:
            run, flags = _flags(arm_path(kp, c), f"{stem}_hc_{_ckey(c)}")
            # Gate (i): H_c scales by exactly c, row for row.
            ratio = flags["H_c"] / base["H_c"]
            worst = float(np.max(np.abs(ratio / c - 1.0)))
            if worst > 1e-12:
                raise SystemExit(f"{_label(kp)} x{c}: H_c ratio off by {worst:.2e}")
            if not np.array_equal(
                np.asarray(run.result.conditioning_grid, dtype=np.float64), grid
            ):
                raise SystemExit(f"{_label(kp)} x{c}: grid differs from production")
            tran = np.asarray(run.result.failure_matrix_tran, dtype=bool)
            nesting = {
                "transient": int(np.sum(tran & ~base_tran)),
                "same_head": int(np.sum(flags["C3b"] & ~base["C3b"])),
                "gross_static": int(np.sum(flags["C0"] & ~base["C0"])),
                "transient_outside_same_head": int(np.sum(tran & ~flags["C3b"])),
            }
            a = _replay(arm_posterior_path(kp, c))
            ev = _evidence_2016(a)
            ev["initiation_identical_to_baseline"] = bool(
                np.array_equal(a["initiation"], base_init)
            )
            out["gates"][f"{_label(kp)} {_ckey(c)}"] = {
                "H_c_ratio_max_rel_dev": worst,
                "nesting_violations": nesting,
            }
            sec["arms"][_ckey(c)] = {
                "c": c,
                "theta_repose_deg": theta_for(c),
                "levels": _levels(run, flags),
                "evidence_2016": ev,
            }
            print(f"  event {_label(kp)} x{c}: done", flush=True)
        out["sections"][_label(kp)] = sec
    return out


# --------------------------------------------------------------------------- #
# Part: annual                                                                  #
# --------------------------------------------------------------------------- #
ARM_KEYS = ("x1.00",) + tuple(_ckey(c) for c in LADDER)
#: Branches per arm: T = adopted transient criterion, I = same head and gate
#: with instantaneous growth (ADR-0055); "-post" is the 2016 transient update.
BRANCHES = ("T-prior", "T-post", "I-prior")


def annual_part(results_root: Path, replicates: int) -> dict[str, Any]:
    from system_integration.bep_input import load_bep_curve

    unc = _load_module("annualisation_uncertainty_study")
    data_repo = results_root.parent
    unc.PRODUCTION_TABLE = results_root / "system_integration/phase3/rq4_annual.csv"
    campaign = unc._load_campaign_module()
    campaign.REPO = data_repo
    campaign.DATA_ROOT = data_repo / "data/raw"
    campaign.HAZARD_CACHE = results_root / "system_integration/hazard_cache"
    cache_before = unc._dir_state(campaign.HAZARD_CACHE, "*.csv")
    context = unc.build_context(campaign)
    production = dict(context["bep_curves"])

    rows: dict[tuple[str, str], Any] = {}
    per_event: dict[tuple[str, str], Any] = {}

    def run_branch(arm: str, branch: str, curves: dict[float, Any], slot: str):
        for kp in KPS:
            context["bep_curves"][(kp, "matrix", slot)] = curves[kp]
        r, pe = unc.annualise_arm(campaign, context, "matrix", slot)
        for kp in KPS:
            context["bep_curves"][(kp, "matrix", slot)] = production[
                (kp, "matrix", slot)
            ]
        rows[(arm, branch)], per_event[(arm, branch)] = r, pe

    # Baseline transient branches straight from production, then gate (iii).
    for source, branch in (("prior", "T-prior"), ("posterior", "T-post")):
        r, pe = unc.annualise_arm(campaign, context, "matrix", source)
        rows[("x1.00", branch)], per_event[("x1.00", branch)] = r, pe
    # The gate compares all four production arms; the bulk pair is annualised
    # only to complete it and is not used further.
    bulk = {
        unc._arm_key("bulk", source): unc.annualise_arm(
            campaign, context, "bulk", source
        )[0]
        for source in ("prior", "posterior")
    }
    gate = unc.gate_one(
        {
            unc._arm_key("matrix", "prior"): rows[("x1.00", "T-prior")],
            unc._arm_key("matrix", "posterior"): rows[("x1.00", "T-post")],
            **bulk,
        }
    )
    print(f"  gate (iii) passed: {gate['rows_compared']} rows", flush=True)

    for arm in ARM_KEYS:
        same_head: dict[float, Any] = {}
        prior: dict[float, Any] = {}
        post: dict[float, Any] = {}
        for kp in KPS:
            stem = _stem(kp)
            if arm == "x1.00":
                path = results_root / f"{stem}.h5"
                key = f"{stem}_base"
            else:
                c = float(arm[1:])
                path = arm_path(kp, c)
                key = f"{stem}_hc_{arm}"
                prior[kp] = load_bep_curve(path, branch="transient")
                post[kp] = load_bep_curve(arm_posterior_path(kp, c), branch="transient")
            run, flags = _flags(path, key)
            grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
            c3b = flags["C3b"]
            same_head[kp] = tdf._same_head_curve(
                grid,
                c3b.mean(axis=0),
                c3b.shape[0],
                float(run.geometry["z_toe"]),
                "same_head_prior",
                run.source_path,
                fitted=True,
            )
        if arm != "x1.00":
            run_branch(arm, "T-prior", prior, "prior")
            run_branch(arm, "T-post", post, "posterior")
        run_branch(arm, "I-prior", same_head, "prior")
        print(f"  annualised {arm}", flush=True)
    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")

    # Surface-only segments must be identical across every arm and branch.
    kp_set = {round(k, 3) for k in KPS}
    base = rows[("x1.00", "T-post")]
    for (arm, branch), rr in rows.items():
        for key, row in rr.items():
            if key[0] == "Tokachi" and round(key[1], 3) in kp_set:
                continue
            strip = {k: v for k, v in row.items() if k != "bep_source"}
            if strip != {k: v for k, v in base[key].items() if k != "bep_source"}:
                raise SystemExit(f"surface-only segment changed: {key} {arm} {branch}")

    def num(v) -> float:
        return 0.0 if v in ("", None) else float(v)

    rng = np.random.default_rng(unc.SEED)
    store: dict[tuple, NDArray] = {}
    points: dict[tuple, float] = {}
    for scenario in campaign.SCENARIOS:
        ids = [
            e.event_id for e in context["hazards"][scenario][("Tokachi", 58.8)].events
        ]
        index, n_blocks, _ = unc.block_index(unc.block_labels(ids, "member"))
        strata = unc.stratum_columns(ids)
        mult = unc.draw_multiplicities_stratified(strata, n_blocks, replicates, rng)
        for (arm, branch), pe in per_event.items():
            for kp in KPS:
                reps = unc.node_replicates(
                    pe[("Tokachi", kp, scenario)], index, n_blocks, mult, len(ids)
                )
                for q in ("__system__", "bep", "overflow"):
                    store[(arm, branch, scenario, kp, q)] = reps.get(
                        q, np.zeros(replicates)
                    )
                row = rows[(arm, branch)][("Tokachi", kp, scenario)]
                for q, field in (
                    ("__system__", "p_annual_system"),
                    ("bep", "p_annual_bep"),
                    ("overflow", "p_annual_overflow"),
                ):
                    points[(arm, branch, scenario, kp, q)] = num(row[field])
                points[(arm, branch, scenario, kp, "share")] = (
                    None if row["share_bep"] in ("", None) else float(row["share_bep"])
                )

    def leading(bep: float, ovf: float) -> str:
        if bep <= 0.0 and ovf <= 0.0:
            return "none"
        return "piping" if bep > ovf else "overflow"

    cells: dict[str, Any] = {}
    for arm in ARM_KEYS:
        for branch in BRANCHES:
            for scenario in campaign.SCENARIOS:
                for kp in KPS:
                    k = (arm, branch, scenario, kp)
                    bep_r = store[k + ("bep",)]
                    ovf_r = store[k + ("overflow",)]
                    sys_r = store[k + ("__system__",)]
                    pb, po = points[k + ("bep",)], points[k + ("overflow",)]
                    cells[f"{arm} {branch} {scenario} {_label(kp)}"] = {
                        "p_system": points[k + ("__system__",)],
                        "p_bep": pb,
                        "p_overflow": po,
                        "share_bep": points[k + ("share",)],
                        "leading": leading(pb, po),
                        "fraction_replicates_piping_leads": float(
                            np.mean(bep_r > ovf_r)
                        ),
                        "system_ci95": [
                            float(x) for x in np.percentile(sys_r, [2.5, 97.5])
                        ],
                    }

    comparisons: dict[str, Any] = {}

    def pair(num_key: tuple, den_key: tuple, scenario: str, kp: float, q: str):
        a = store[num_key + (scenario, kp, q)]
        b = store[den_key + (scenario, kp, q)]
        pa = points[num_key + (scenario, kp, q)]
        pb = points[den_key + (scenario, kp, q)]
        with np.errstate(divide="ignore", invalid="ignore"):
            r = a / b
            db = tdf._beta(b) - tdf._beta(a)
        r, db = r[np.isfinite(r)], db[np.isfinite(db)]
        return {
            "point": (pa / pb) if pb else None,
            "ci95": (
                [float(x) for x in np.percentile(r, [2.5, 97.5])] if r.size else None
            ),
            "delta_beta": (
                float(tdf._beta(pb) - tdf._beta(pa)) if pa > 0 and pb > 0 else None
            ),
            "delta_beta_ci95": (
                [float(x) for x in np.percentile(db, [2.5, 97.5])] if db.size else None
            ),
        }

    for arm in ARM_KEYS:
        for scenario in campaign.SCENARIOS:
            for kp in KPS:
                lab = f"{arm} {scenario} {_label(kp)}"
                comparisons[f"criterion I-prior/T-prior bep {lab}"] = pair(
                    (arm, "I-prior"), (arm, "T-prior"), scenario, kp, "bep"
                )
                comparisons[f"criterion I-prior/T-prior system {lab}"] = pair(
                    (arm, "I-prior"), (arm, "T-prior"), scenario, kp, "__system__"
                )
                if arm != "x1.00":
                    comparisons[f"reduction base/arm T-post bep {lab}"] = pair(
                        ("x1.00", "T-post"), (arm, "T-post"), scenario, kp, "bep"
                    )
                    comparisons[f"reduction base/arm T-post system {lab}"] = pair(
                        ("x1.00", "T-post"), (arm, "T-post"), scenario, kp, "__system__"
                    )
    climate: dict[str, Any] = {}
    for arm in ARM_KEYS:
        for branch in BRANCHES:
            for kp in KPS:
                h = store[(arm, branch, "historical", kp, "__system__")]
                w = store[(arm, branch, "+4K", kp, "__system__")]
                ph = points[(arm, branch, "historical", kp, "__system__")]
                pw = points[(arm, branch, "+4K", kp, "__system__")]
                with np.errstate(divide="ignore", invalid="ignore"):
                    r = w / h
                r = r[np.isfinite(r)]
                climate[f"{arm} {branch} {_label(kp)}"] = {
                    "point": (pw / ph) if ph else None,
                    "ci95": (
                        [float(x) for x in np.percentile(r, [2.5, 97.5])]
                        if r.size
                        else None
                    ),
                }
    rank: dict[str, Any] = {}
    for arm in ARM_KEYS:
        for scenario in campaign.SCENARIOS:
            vals = [points[(arm, "T-post", scenario, kp, "__system__")] for kp in KPS]
            order = [_label(KPS[i]) for i in np.argsort(-np.asarray(vals))]
            stack = np.column_stack(
                [store[(arm, "T-post", scenario, kp, "__system__")] for kp in KPS]
            )
            same = np.all(
                np.argsort(-stack, axis=1) == np.argsort(-np.asarray(vals)), axis=1
            )
            rank[f"{arm} {scenario}"] = {
                "order": order,
                "fraction_replicates_with_this_order": float(np.mean(same)),
            }
    return {
        "gates": {
            "gate_iii": gate,
            "surface_only_segments": "identical across every arm and branch",
            "hazard_cache_unchanged": True,
        },
        "replicates": replicates,
        "seed": unc.SEED,
        "cells": cells,
        "comparisons": comparisons,
        "climate_ratio": climate,
        "posterior_ranking": rank,
    }


# --------------------------------------------------------------------------- #
# Part: resistant                                                               #
# --------------------------------------------------------------------------- #
#: Persisted readings beside the adopted one: (label, prior h5, posterior h5),
#: paths relative to the results root.
def _readings(kp: float) -> list[tuple[str, str, str]]:
    s = _stem(kp)
    sb = _stem(kp, "bulk")
    out = [
        ("adopted", f"{s}.h5", f"phase2/{s}_posterior.h5"),
        ("bulk d70", f"{sb}.h5", f"phase2/{sb}_posterior.h5"),
    ]
    for arm, name in (
        ("k_aq_field_geomean", "field-test conductivity mean"),
        ("k_aq_field_toe", "landside-toe conductivity test"),
        ("k_aq_regional_upper", "regional upper conductivity"),
    ):
        out.append(
            (
                name,
                f"sensitivity/adr0048_prior_means/{s}_{arm}.h5",
                f"sensitivity/conductivity_posterior/phase2/{s}_{arm}_posterior.h5",
            )
        )
    if kp in (58.8, 60.0):
        out.append(
            (
                "measured berm",
                f"sensitivity/adr0050_drained_bracket/{s}_berm_only.h5",
                f"sensitivity/adr0050_drained_bracket/phase2/{s}_berm_only_posterior.h5",
            )
        )
    for c in LADDER:
        out.append((f"H_c x {c}", str(arm_path(kp, c)), str(arm_posterior_path(kp, c))))
    return out


def resistant_part(results_root: Path) -> dict[str, Any]:
    """Probabilities at the design grid, the 2016 peak stage and in 2016 itself."""
    out: dict[str, Any] = {}
    for kp in KPS:
        sec: dict[str, Any] = {}
        for name, prior, post in _readings(kp):
            p_prior = Path(prior) if Path(prior).is_absolute() else results_root / prior
            p_post = Path(post) if Path(post).is_absolute() else results_root / post
            if not (p_prior.is_file() and p_post.is_file()):
                sec[name] = None
                continue
            with h5py.File(p_prior, "r") as h5:
                grid = np.asarray(h5["conditioning_grid"][:], dtype=np.float64)
                p_t = np.asarray(h5["P_f_trans_raw"][:], dtype=np.float64)
                p_s = np.asarray(h5["P_f_static_raw"][:], dtype=np.float64)
            i_d = int(np.argmin(np.abs(grid - DESIGN_GRID[kp])))
            i_p = int(np.argmin(np.abs(grid - PEAK_2016[kp])))
            ev = _evidence_2016(_replay(p_post))
            sec[name] = {
                "design_grid_stage_m": float(grid[i_d]),
                "P_transient_design_grid": float(p_t[i_d]),
                "P_gross_static_design_grid": float(p_s[i_d]),
                "nearest_grid_stage_to_2016_peak_m": float(grid[i_p]),
                "P_transient_canonical_at_2016_peak_stage": float(p_t[i_p]),
                "replay_2016": ev,
            }
        out[_label(kp)] = sec
    return out


# --------------------------------------------------------------------------- #
# Main                                                                          #
# --------------------------------------------------------------------------- #
PARTS = ("arms", "replay", "event", "annual", "resistant", "figures", "report")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("part", choices=PARTS)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=REPO / "results",
        help="Production results root (default: this checkout's results/).",
    )
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--replicates", type=int, default=10_000)
    args = parser.parse_args(argv)
    tick = time.time()
    if args.part == "arms":
        _write_stage("arms", arms_part(args.n_jobs))
    elif args.part == "replay":
        _write_stage("replay", replay_part(args.results_root))
    elif args.part == "event":
        _write_stage("event", event_part(args.results_root))
    elif args.part == "annual":
        _write_stage("annual", annual_part(args.results_root, args.replicates))
    elif args.part == "resistant":
        _write_stage("resistant", resistant_part(args.results_root))
    elif args.part == "figures":
        print(figures_part())
    elif args.part == "report":
        report_part()
    print(f"{args.part}: {time.time() - tick:.0f} s")
    return 0


FIGURE = "resistance_multiplier.png"
#: Named readings drawn on the multiplier axis: (low, high, legend text).
NAMED_READINGS = (
    (1.125, 1.178, "uniformity term as calibrated, sand fraction"),
    (1.577, 1.880, "uniformity term with refitted exponent, sand fraction"),
)


def figures_part() -> Path:
    """The thesis figure: what a shared resistance multiplier does to each answer."""
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as fs
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    an = ev["annual"]["cells"]
    xs = np.array((1.0,) + LADDER)
    width = fs.TEXTWIDTH_IN * 1.6
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(2, 2, figsize=(width, width * 0.62))
    ax_ev, ax_ap, ax_sh, ax_sw = axes.ravel()
    floor = 1e-6
    band_colors = (fs.BASELINE, fs.SEQ_BLUE[0])

    def decorate(ax):
        for (lo, hi, _), col in zip(NAMED_READINGS, band_colors):
            ax.axvspan(lo, hi, color=col, lw=0)
        ax.axvline(DUTCH_GRAVEL, color=fs.INK_2, ls="--", lw=0.9)
        ax.set_xscale("log")
        ax.set_xticks([1.0, 1.25, 1.5, 1.8, 2.2, 2.7])
        ax.set_xticklabels(["1", "1.25", "1.5", "1.8", "2.2", "2.7"])
        ax.minorticks_off()
        ax.set_xlim(0.97, 2.85)

    for kp in KPS:
        key = f"KP{kp:.1f}"
        color, marker = fs.SECTION_COLORS[key], fs.SECTION_MARKERS[key]
        sec = ev["sections"][_label(kp)]
        rej = np.array(
            [sec["arms"][a]["evidence_2016"]["rejected_transient"] for a in ARM_KEYS]
        )
        pos = rej > 0
        ax_ev.plot(xs[pos], rej[pos], color=color, lw=1.3 * scale)
        ax_ev.plot(xs[pos], rej[pos], marker, color=color, ms=3.4 * scale, ls="none")
        ax_ev.plot(
            xs[~pos],
            np.full((~pos).sum(), floor),
            marker,
            color=color,
            mfc="none",
            ms=3.4 * scale,
            ls="none",
        )
        p_bep = np.array(
            [an[f"{a} T-post historical {_label(kp)}"]["p_bep"] for a in ARM_KEYS]
        )
        pos = p_bep > 0
        ax_ap.plot(xs[pos], p_bep[pos], color=color, lw=1.3 * scale)
        ax_ap.plot(xs[pos], p_bep[pos], marker, color=color, ms=3.4 * scale, ls="none")
        ax_ap.plot(
            xs[~pos],
            np.full((~pos).sum(), 1e-10),
            marker,
            color=color,
            mfc="none",
            ms=3.4 * scale,
            ls="none",
        )
        for ax, scen in ((ax_sh, "historical"), (ax_sw, "+4K")):
            sh = np.array(
                [
                    (
                        an[f"{a} T-post {scen} {_label(kp)}"]["share_bep"]
                        if an[f"{a} T-post {scen} {_label(kp)}"]["p_bep"] > 0
                        or an[f"{a} T-post {scen} {_label(kp)}"]["p_overflow"] > 0
                        else np.nan
                    )
                    for a in ARM_KEYS
                ],
                dtype=float,
            )
            ax.plot(xs, sh, color=color, lw=1.3 * scale)
            ax.plot(xs, sh, marker, color=color, ms=3.4 * scale, ls="none")
    for ax in axes.ravel():
        decorate(ax)
    ax_ev.set_yscale("log")
    ax_ev.set_ylim(floor * 0.6, 0.1)
    ax_ev.set_ylabel("share rejected by 2016")
    ax_ap.set_yscale("log")
    ax_ap.set_ylim(1e-10 * 0.6, 3e-2)
    ax_ap.set_ylabel("annual piping probability")
    for ax in (ax_sh, ax_sw):
        ax.axhline(0.5, color=fs.RED, lw=0.9)
        ax.set_ylim(-0.03, 1.03)
        ax.set_ylabel("piping share")
    for ax in (ax_sh, ax_sw):
        ax.set_xlabel("multiplier on the critical head")
    fs.panel_title(ax_ev, "(a) 2016 survival update", scale=scale)
    fs.panel_title(ax_ap, "(b) Annual piping probability, historical", scale=scale)
    fs.panel_title(ax_sh, "(c) Piping share, historical", scale=scale)
    fs.panel_title(ax_sw, "(d) Piping share, +4 K", scale=scale)
    handles = [
        Line2D(
            [],
            [],
            color=fs.SECTION_COLORS[f"KP{kp:.1f}"],
            marker=fs.SECTION_MARKERS[f"KP{kp:.1f}"],
            ms=3.4 * scale,
            lw=1.3 * scale,
        )
        for kp in KPS
    ] + [
        Patch(color=band_colors[0]),
        Patch(color=band_colors[1]),
        Line2D([], [], color=fs.INK_2, ls="--", lw=0.9),
    ]
    labels = [_label(kp) for kp in KPS] + [
        NAMED_READINGS[0][2],
        NAMED_READINGS[1][2],
        "Dutch gravel allowance",
    ]
    fs.title(fig, "What a higher piping resistance would change", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale, ncol=4)
    fs.layout(fig, scale=scale, legend_rows=2)
    return fs.save(fig, FIGURE, mirror=OUT_DIR / "figures")


# --------------------------------------------------------------------------- #
# Part: report                                                                  #
# --------------------------------------------------------------------------- #
def _r(obj: Any, sig: int = 6) -> Any:
    """Round floats to ``sig`` significant figures, recursively."""
    if isinstance(obj, float):
        return float(f"{obj:.{sig}g}") if np.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _r(v, sig) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_r(v, sig) for v in obj]
    return obj


def _qualified(lv: dict[str, Any], kp: float) -> bool:
    """Attainable, at least R1 transient failures, and a defined index gap."""
    return (
        lv["stage_m"] <= ATTAINABLE_MAX[kp] + 1e-9
        and lv["k_T"] >= R1
        and lv["time_factor"]["dbeta"] is not None
    )


def _span(values: list[float]) -> list[float] | None:
    return [float(min(values)), float(max(values))] if values else None


def event_summary(ev: dict[str, Any]) -> dict[str, Any]:
    """Design-grid values and the departures from baseline at shared stages."""
    out: dict[str, Any] = {"by_arm": {}, "design_grid": {}}
    for arm in ARM_KEYS[1:]:
        d_db: list[float] = []
        f_td: list[float] = []
        n = 0
        for lab, sec in ev["sections"].items():
            kp = float(lab.split()[-1])
            base = {lv["stage_m"]: lv for lv in sec["arms"]["x1.00"]["levels"]}
            for lv in sec["arms"][arm]["levels"]:
                b = base[lv["stage_m"]]
                if _qualified(lv, kp) and _qualified(b, kp):
                    n += 1
                    d_db.append(lv["time_factor"]["dbeta"] - b["time_factor"]["dbeta"])
                    f_td.append(lv["time_factor"]["ratio"] / b["time_factor"]["ratio"])
        out["by_arm"][arm] = {
            "shared_qualified_levels": n,
            "delta_dbeta_range": _span(d_db),
            "F_td_factor_range": _span(f_td),
            "dbeta_fell_at_every_shared_level": bool(d_db) and max(d_db) < 0.0,
        }
    for lab, sec in ev["sections"].items():
        kp = float(lab.split()[-1])
        row: dict[str, Any] = {}
        for arm, a in sec["arms"].items():
            lv = next(
                v for v in a["levels"] if abs(v["stage_m"] - DESIGN_GRID[kp]) < 1e-6
            )
            n_rows = 100_000
            row[arm] = {
                "stage_m": lv["stage_m"],
                "P_transient": lv["k_T"] / n_rows,
                "P_same_head": lv["k_I"] / n_rows,
                "P_gross_static": lv["k_C0"] / n_rows,
                "k_transient": lv["k_T"],
                "gate_open": lv["gate_open"],
                "dbeta": lv["time_factor"]["dbeta"] if lv["k_T"] >= R1 else None,
                "dbeta_ci95": (
                    lv["time_factor"]["dbeta_ci95"] if lv["k_T"] >= R1 else None
                ),
                "F_td": lv["time_factor"]["ratio"] if lv["k_T"] >= R1 else None,
                "F_td_ci95": (
                    lv["time_factor"]["ratio_ci95"] if lv["k_T"] >= R1 else None
                ),
            }
        out["design_grid"][lab] = row
    return out


def break_even(cells: dict[str, Any], side: str = "T-post") -> dict[str, Any]:
    """Smallest ladder multiplier at which a cell's leading mechanism changes."""
    out: dict[str, Any] = {}
    for scenario in ("historical", "+4K"):
        for kp in KPS:
            lab = _label(kp)
            base = cells[f"x1.00 {side} {scenario} {lab}"]["leading"]
            first = None
            for c in LADDER:
                if cells[f"{_ckey(c)} {side} {scenario} {lab}"]["leading"] != base:
                    first = c
                    break
            out[f"{scenario} {lab}"] = {
                "baseline_leading": base,
                "first_change_at": first,
            }
    return out


def report_part() -> None:
    ev = _read_stage("event")
    an = _read_stage("annual")
    res = _read_stage("resistant")
    rep = _read_stage("replay")
    sections = {}
    for lab, sec in ev["sections"].items():
        kp = float(lab.split()[-1])
        sections[lab] = {
            "design_level_m": sec["design_level_m"],
            "design_grid_m": sec["design_grid_m"],
            "peak_2016_m": sec["peak_2016_m"],
            "attainable_max_m": sec["attainable_max_m"],
            "arms": {
                arm: {
                    "c": a["c"],
                    "evidence_2016": a["evidence_2016"],
                    "levels": [
                        {
                            "stage_m": lv["stage_m"],
                            "k_T": lv["k_T"],
                            "k_I": lv["k_I"],
                            "k_C0": lv["k_C0"],
                            "gate_open": lv["gate_open"],
                            "F_td": lv["time_factor"]["ratio"],
                            "dbeta": lv["time_factor"]["dbeta"],
                            "R1": lv["time_factor"]["R1"],
                        }
                        for lv in a["levels"]
                        if lv["stage_m"] <= ATTAINABLE_MAX[kp] + 1e-9
                    ],
                }
                for arm, a in sec["arms"].items()
            },
        }
    record = {
        "study": "gravel-grading-resistance-study",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "date": "2026-10-06",
        "comparator": "ADR-0055: same head and same gate (C3b) against C4b",
        "reading": "matrix d70; KP 58.8 and KP 60.0 as if undrained; N = 1e5",
        "ladder": list(LADDER),
        "dutch_gravel_factor": DUTCH_GRAVEL,
        "theta_repose_deg": {_ckey(c): theta_for(c) for c in LADDER},
        "gates": {"event": ev["gates"], "annual": an["gates"]},
        "replay_posterior_metadata": rep,
        "event_summary": event_summary(ev),
        "sections": sections,
        "annual": {
            "replicates": an["replicates"],
            "seed": an["seed"],
            "cells": an["cells"],
            "comparisons": an["comparisons"],
            "climate_ratio": an["climate_ratio"],
            "posterior_ranking": an["posterior_ranking"],
            "break_even_posterior": break_even(an["cells"], "T-post"),
            "break_even_prior": break_even(an["cells"], "T-prior"),
        },
        "resistant_readings": res,
    }
    EVIDENCE.write_text(json.dumps(_r(record), indent=1) + "\n", encoding="utf-8")
    print(
        f"wrote {EVIDENCE.relative_to(REPO)} ({EVIDENCE.stat().st_size / 1e3:.0f} kB)"
    )


if __name__ == "__main__":
    raise SystemExit(main())
