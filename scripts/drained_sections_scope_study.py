"""Assemble the measured-berm companion reading at KP 58.8 and KP 60.0.

Companion driver for ``docs/decisions/drained-sections-scope-study.md``.
Pure post-processing: no limit state is evaluated, no default changes and no
persisted artifact is written except the evidence record. Every number traces
to an artifact the ADR-0050 bracket already persisted; what this driver adds is
the one consolidated table the thesis quotes beside the as-if-undrained
deliverable, and one estimand ADR-0050 never computed, the reliability-index
separation of the two piping criteria on each arm.

Three parts:

``design``
    The two branches at each section's design-level grid point on every arm,
    with the paired-bootstrap interval on ``dbeta = beta_trans - beta_static``
    and on its displacement from the as-if-undrained arm. The arms share their
    theta rows (same seed, same LHS), and the seepage-length draw is the same
    uniform mapped through a different mean, so resampling rows jointly across
    two arms is the pairing that makes the displacement's interval honest.
    Method and seed convention are imported from ``rq1_beta_analysis.py``.

``survival``
    The 2016 rejection on the production posterior and on each arm's own
    replay, read from the persisted sidecars. Refuses unless every sidecar
    carries the corrected Obihiro gauge node (KP 56.73), because the ADR-0050
    companion note still prints the superseded KP 56.6 values.

``annual``
    Annual system probability, piping share, climate ratio and the four-section
    ranking on the as-if-undrained, measured-berm and strongest-relief arms,
    from the tracked Phase 3 evidence record. The strongest arm's piping curve
    is clamped above the grid there, so its annual values are lower bounds.

Usage (from a worktree, reading the main checkout's untracked results)::

    python scripts/drained_sections_scope_study.py \
        --results-root D:/repositories/bep-reliability-engine/results \
        --out docs/decisions/drained-sections-scope-study.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import h5py
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from rq1_beta_analysis import (  # noqa: E402
    _percentile_ci,
    _stable_seed,
    beta_from_p,
    paired_bootstrap_means,
)

SECTIONS: dict[str, dict[str, Any]] = {
    "KP 58.8": {"stem": "tokachi_kp58.8_historical_matrix", "design_hwl": 41.03},
    "KP 60.0": {"stem": "tokachi_kp60.0_historical_matrix", "design_hwl": 42.75},
}
ARMS: tuple[str, ...] = (
    "gate",
    "berm_only",
    "joint_0.80",
    "joint_0.60",
    "joint_0.40",
    "joint_0.20",
)
ARM_LABELS: dict[str, str] = {
    "gate": "as-if-undrained (1998 seepage length, no relief): the deliverable",
    "berm_only": "measured 2025 berm, drain credited at zero",
    "joint_0.80": "measured berm + 20 % exit-gradient relief",
    "joint_0.60": "measured berm + 40 % exit-gradient relief",
    "joint_0.40": "measured berm + 60 % exit-gradient relief",
    "joint_0.20": "measured berm + 80 % exit-gradient relief",
}
CORRECTED_GAUGE_KP = 56.73
ANNUAL_RECORD = (
    REPO / "docs/decisions/adr0050-drained-bracket-annualisation-matrix-posterior.json"
)
BRACKET_DIR = Path("sensitivity/adr0050_drained_bracket")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _design_column(grid: np.ndarray, design_hwl: float) -> int:
    """Index of the grid point the thesis quotes as the design level.

    Table 6.x reads the nearest grid point at or below the design level:
    41.00 m at KP 58.8 (design 41.03) and 42.75 m at KP 60.0.
    """
    below = np.flatnonzero(grid <= design_hwl + 1e-9)
    return int(below[-1])


def _arm_columns(results_root: Path, stem: str, arm: str, col: int):
    path = results_root / BRACKET_DIR / f"{stem}_{arm}.h5"
    with h5py.File(path, "r") as h5:
        grid = np.asarray(h5["conditioning_grid"][:], dtype=float)
        static = np.asarray(h5["failure_matrix_static"][:, col], dtype=bool)
        trans = np.asarray(h5["failure_matrix_trans"][:, col], dtype=bool)
    return grid, static, trans


def design_part(results_root: Path, n_replicates: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for section, spec in SECTIONS.items():
        stem = spec["stem"]
        with h5py.File(results_root / BRACKET_DIR / f"{stem}_gate.h5", "r") as h5:
            grid = np.asarray(h5["conditioning_grid"][:], dtype=float)
        col = _design_column(grid, spec["design_hwl"])
        stage = float(grid[col])

        # The gate arm is the production run re-executed; its counts at the
        # design column must equal the persisted production sweep's.
        with h5py.File(results_root / f"{stem}.h5", "r") as h5:
            prod_static = int(np.count_nonzero(h5["failure_matrix_static"][:, col]))
            prod_trans = int(np.count_nonzero(h5["failure_matrix_trans"][:, col]))

        cols: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for arm in ARMS:
            g, s, t = _arm_columns(results_root, stem, arm, col)
            if not np.allclose(g, grid):
                raise SystemExit(f"{section} {arm}: conditioning grid differs")
            cols[arm] = (s, t)
        gs, gt = cols["gate"]
        if (int(gs.sum()), int(gt.sum())) != (prod_static, prod_trans):
            raise SystemExit(
                f"{section}: gate-arm counts {int(gs.sum())}/{int(gt.sum())} do not "
                f"reproduce production {prod_static}/{prod_trans}; refusing"
            )

        rows: dict[str, Any] = {}
        for arm in ARMS:
            s, t = cols[arm]
            n = s.size
            k_s, k_t = int(s.sum()), int(t.sum())
            p_s, p_t = k_s / n, k_t / n
            label = f"drained-scope|{section}|{arm}|{stage:.2f}"
            means = paired_bootstrap_means(
                np.stack([gs, gt, s, t], axis=1),
                n_replicates=n_replicates,
                seed=_stable_seed(label),
            )
            with np.errstate(divide="ignore", invalid="ignore"):
                db_gate = beta_from_p(means[:, 1]) - beta_from_p(means[:, 0])
                db_arm = beta_from_p(means[:, 3]) - beta_from_p(means[:, 2])
                shift = db_arm - db_gate
            with np.errstate(divide="ignore"):
                db = float(beta_from_p(p_t) - beta_from_p(p_s)) if k_t else None
            rows[arm] = {
                "label": ARM_LABELS[arm],
                "n": n,
                "static_failures": k_s,
                "transient_failures": k_t,
                "p_static": p_s,
                "p_transient": p_t,
                "ratio_B": (p_s / p_t) if k_t else None,
                "delta_beta": db,
                "delta_beta_ci95": _percentile_ci(db_arm) if k_t >= 30 else None,
                "delta_beta_shift_from_as_if_undrained": (
                    (db - rows["gate"]["delta_beta"])
                    if (k_t and arm != "gate")
                    else None
                ),
                "shift_ci95": (
                    _percentile_ci(shift) if (k_t >= 30 and arm != "gate") else None
                ),
                "resolved_r1": k_t >= 30,
            }
        out[section] = {
            "design_hwl_m": spec["design_hwl"],
            "grid_stage_m": stage,
            "grid_column": col,
            "production_counts_reproduced": {
                "static": prod_static,
                "transient": prod_trans,
            },
            "n_bootstrap_replicates": n_replicates,
            "arms": rows,
        }
    return out


def survival_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for section, spec in SECTIONS.items():
        stem = spec["stem"]
        entries = {
            "as_if_undrained": results_root / "phase2" / f"{stem}_posterior.json"
        }
        for arm in ARMS[1:]:
            entries[arm] = (
                results_root / BRACKET_DIR / "phase2" / f"{stem}_{arm}_posterior.json"
            )
        rows: dict[str, Any] = {}
        for arm, path in entries.items():
            record = _read_json(path)
            text = json.dumps(record)
            if f'"gauge_kp": {CORRECTED_GAUGE_KP}' not in text:
                raise SystemExit(
                    f"{path.name}: not replayed at gauge KP {CORRECTED_GAUGE_KP}"
                )
            post = record["phase2"]["posterior"]
            rows[arm] = {
                "rejection_fraction": round(float(post["rejection_fraction"]), 6),
                "n_accepted": int(post["n_accepted"]),
                "source": str(path.relative_to(results_root)).replace("\\", "/"),
            }
        out[section] = rows
    return out


def annual_part() -> dict[str, Any]:
    record = _read_json(ANNUAL_RECORD)
    keep = ("as_if_undrained", "berm_only", "joint_0.20")
    per: dict[str, Any] = {}
    for entry in record["per_section"]:
        scen = entry["scenarios"]
        rows: dict[str, Any] = {}
        for arm in keep:
            h = scen["historical"][
                "as_if_undrained" if arm == "as_if_undrained" else "arms"
            ]
            w = scen["+4K"]["as_if_undrained" if arm == "as_if_undrained" else "arms"]
            if arm != "as_if_undrained":
                h, w = h[arm], w[arm]
            ratio = (
                (w["p_annual_system"] / h["p_annual_system"])
                if h["p_annual_system"]
                else None
            )
            rows[arm] = {
                "historical": {
                    "p_annual_system": h["p_annual_system"],
                    "share_bep": h["share_bep"],
                    "leading_mechanism": h["leading_mechanism"],
                    "lower_bound": bool(h.get("bep_clamped_above_grid", False)),
                },
                "+4K": {
                    "p_annual_system": w["p_annual_system"],
                    "share_bep": w["share_bep"],
                    "leading_mechanism": w["leading_mechanism"],
                    "lower_bound": bool(w.get("bep_clamped_above_grid", False)),
                },
                "climate_ratio": ratio,
            }
        per[entry["section"]] = rows
    ranking: dict[str, Any] = {}
    for scenario, arms in record["ranking"].items():
        ranking[scenario] = {}
        for arm in keep:
            values = arms[arm]["values"]
            order = arms[arm]["order"]
            top, second = values[order[0]], values[order[1]]
            ranking[scenario][arm] = {
                "order": order,
                "values": values,
                "leader_margin_over_second": (top / second) if second else None,
            }
    return {
        "source": str(ANNUAL_RECORD.relative_to(REPO)).replace("\\", "/"),
        "generated_source": record["generated"],
        "per_section": per,
        "ranking": ranking,
    }


def ranking_part(results_root: Path, replicates: int) -> dict[str, Any]:
    """Hazard-sampling intervals on the measured-berm annual values and ranking.

    Re-annualises through the production composition step (imported, via the
    hazard-sampling study, never copied) twice: once as published and once with
    the two drained sections' matrix posterior curves swapped for their
    measured-berm replays. Both passes must reproduce the tracked ADR-0050
    record exactly, and the warm hazard cache must be unchanged afterwards. One
    pattern-stratified member-block draw per scenario then serves both passes
    and all four sections, so every between-section and between-arm comparison
    is paired, which is what a ranking claim needs.
    """
    import annualisation_uncertainty_study as unc

    from system_integration.bep_input import load_bep_curve

    data_repo = results_root.parent
    campaign = unc._load_campaign_module()
    campaign.REPO = data_repo
    campaign.DATA_ROOT = data_repo / "data/raw"
    campaign.HAZARD_CACHE = results_root / "system_integration/hazard_cache"
    cache_before = unc._dir_state(campaign.HAZARD_CACHE, "*.csv")

    context = unc.build_context(campaign)
    _, per_event_prod = unc.annualise_arm(campaign, context, "matrix", "posterior")
    for kp, section in ((58.8, "KP 58.8"), (60.0, "KP 60.0")):
        stem = SECTIONS[section]["stem"]
        path = results_root / BRACKET_DIR / "phase2" / f"{stem}_berm_only_posterior.h5"
        context["bep_curves"][(kp, "matrix", "posterior")] = load_bep_curve(
            path, branch="transient"
        )
    _, per_event_berm = unc.annualise_arm(campaign, context, "matrix", "posterior")

    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")

    tracked = _read_json(ANNUAL_RECORD)
    expected = tracked["ranking"]
    kps = {"KP 57.4": 57.4, "KP 58.8": 58.8, "KP 60.0": 60.0, "KP 62.0": 62.0}
    rng = np.random.default_rng(unc.SEED)
    out: dict[str, Any] = {
        "estimator": (
            "d4PDF member-block bootstrap, stratified inside the prescribed "
            "sea-surface-temperature patterns (one stratum historically), "
            "fragility curves fixed: hazard-sampling uncertainty only"
        ),
        "replicates": replicates,
        "seed": unc.SEED,
    }
    reps_by_scenario: dict[str, Any] = {}
    for scenario in campaign.SCENARIOS:
        key0 = ("Tokachi", 58.8, scenario)
        ids = [
            e.event_id for e in context["hazards"][scenario][("Tokachi", 58.8)].events
        ]
        index, n_blocks, _ = unc.block_index(unc.block_labels(ids, "member"))
        strata = unc.stratum_columns(ids)
        mult = unc.draw_multiplicities_stratified(strata, n_blocks, replicates, rng)
        cols, names = [], []
        for arm, per_event in (
            ("as_if_undrained", per_event_prod),
            ("berm_only", per_event_berm),
        ):
            for section, kp in kps.items():
                vec = np.asarray(per_event[("Tokachi", kp, scenario)]["__system__"])
                point = float(np.mean(vec))
                # The tracked record carries six significant figures.
                if not np.isclose(
                    point, expected[scenario][arm]["values"][section], rtol=1e-5, atol=0
                ):
                    raise SystemExit(
                        f"{scenario} {arm} {section}: {point} does not reproduce the "
                        f"tracked record {expected[scenario][arm]['values'][section]}"
                    )
                cols.append(vec)
                names.append((arm, section))
        assert key0 in per_event_prod
        sums = unc.block_sums(np.stack(cols, axis=1), index, n_blocks)
        reps = unc.replicate_means(sums, mult, len(ids))
        reps_by_scenario[scenario] = (reps, names, cols)
        block: dict[str, Any] = {}
        for arm in ("as_if_undrained", "berm_only"):
            idx = {s: names.index((arm, s)) for s in kps}
            points = {s: float(np.mean(cols[idx[s]])) for s in kps}
            values = {s: unc._interval(points[s], reps[:, idx[s]]) for s in kps}
            order = sorted(kps, key=lambda s: -points[s])
            ranks = np.argsort(
                np.argsort(-reps[:, [idx[s] for s in kps]], axis=1), axis=1
            )
            rank_freq = {
                s: {str(r + 1): float(np.mean(ranks[:, j] == r)) for r in range(4)}
                for j, s in enumerate(kps)
            }
            same_order = float(
                np.mean(
                    np.all(
                        np.argsort(-reps[:, [idx[s] for s in kps]], axis=1)
                        == np.argsort(-np.asarray([points[s] for s in kps])),
                        axis=1,
                    )
                )
            )
            pairs = {}
            for a in kps:
                for b in kps:
                    if a < b:
                        ratio = reps[:, idx[a]] / reps[:, idx[b]]
                        pairs[f"{a} / {b}"] = {
                            "point": points[a] / points[b] if points[b] else None,
                            "ci95": list(
                                unc.percentile_interval(ratio[np.isfinite(ratio)])
                            ),
                            "fraction_a_above_b": float(
                                np.mean(reps[:, idx[a]] > reps[:, idx[b]])
                            ),
                        }
            block[arm] = {
                "values": values,
                "order": order,
                "fraction_replicates_with_this_exact_order": same_order,
                "rank_frequency": rank_freq,
                "pairwise": pairs,
            }
        out[scenario] = block

    (h_reps, names, h_cols), (w_reps, _, w_cols) = (
        reps_by_scenario["historical"],
        reps_by_scenario["+4K"],
    )
    ratios: dict[str, Any] = {}
    for j, (arm, section) in enumerate(names):
        h_point, w_point = float(np.mean(h_cols[j])), float(np.mean(w_cols[j]))
        defined, n_undefined = unc.ratio_replicates(h_reps[:, j], w_reps[:, j])
        ratios.setdefault(arm, {})[section] = {
            "point": (w_point / h_point) if h_point else None,
            "ci95": list(unc.percentile_interval(defined)) if defined.size else None,
            "n_undefined_replicates": n_undefined,
        }
    out["climate_ratio"] = ratios
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-root", type=Path, default=REPO / "results")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--replicates", type=int, default=10_000)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO / "docs/decisions/drained-sections-scope-study.json",
    )
    args = parser.parse_args()

    record = {
        "study": "Scope of the as-if-undrained deliverable at KP 58.8 and KP 60.0; "
        "the measured-berm companion reading",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generated_by": "scripts/drained_sections_scope_study.py",
        "d70_interpretation": "matrix",
        "companion_definition": (
            "measured 2025 lidar seepage length (42.0 m at KP 58.8, 43.0 m at KP 60.0) "
            "with the toe drain credited at zero; an assumption about the drain, not "
            "a present-day estimate"
        ),
        "design": design_part(args.results_root, args.bootstrap),
        "survival": survival_part(args.results_root),
        "annual": annual_part(),
        "ranking_intervals": ranking_part(args.results_root, args.replicates),
    }
    args.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
