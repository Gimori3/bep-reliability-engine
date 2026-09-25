"""What the choice of piping criterion does downstream, and what 2016 says between them.

Driver for ``docs/decisions/criterion-consequence-and-2016-evidence-study.md``
(Green Light item 2). Companion study: no default, config, prior, kernel,
persisted sweep or published number changes. Three parts.

``evidence``
    The likelihood ratio of the observed 2016 survival under the transient and
    the static criterion, per section and d70 reading, on the shared prior rows,
    with a paired row bootstrap. Two further comparators split it: the
    crack-reduced static rule (``Z_static + 0.3 D_bl`` at the replayed peak,
    exact from the persisted per-row margin) and the head-equalised transient
    (the ADR-0051 gross-head arm, replayed in memory through
    ``pipeline.run_survival_update`` at production settings). Joint evidence
    over the four sections is bounded over dependence structures. The measured
    berm is read from the persisted ADR-0050 ``berm_only`` replays.

``hypothetical``
    The likelihood ratio one survival, or one breach, would carry at each
    conditioning level under the canonical shape, from the Phase 1 matrices,
    up to each section's attainable maximum. This answers "what observation
    would discriminate".

``annual``
    Four piping branches (transient and static, prior and posterior) composed
    and annualised through the production Phase 3 code path, with the published
    pattern-stratified member-block bootstrap shared by all of them. The static
    posterior is the self-consistent one: the static curve masked by the rows
    that survive the *static* criterion at 2016, built with
    ``fragility_update.posterior_fragility_from_matrices``.

Usage (from a worktree, reading the main checkout's untracked results)::

    python scripts/criterion_consequence_study.py \
        --results-root D:/repositories/bep-reliability-engine/results
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

#: Crack-resistance coefficient of Pol SIE 2024 Eq. (6), the production value.
CRACK_COEFFICIENT = 0.3
#: ADR-0024 attainable maxima [m T.P.], the top of each section's real range.
ATTAINABLE_MAX = {57.4: 43.25, 58.8: 42.75, 60.0: 44.25, 62.0: 50.5}
KPS: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0)
#: Design high water levels [m T.P.] (Table 3.x of the thesis).
DESIGN_HWL = {57.4: 39.21, 58.8: 41.03, 60.0: 42.75, 62.0: 46.39}
D70S: tuple[str, ...] = ("matrix", "bulk")
BRANCHES: tuple[str, ...] = ("T-prior", "T-post", "S-prior", "S-post")
EVIDENCE_BOOTSTRAP = 2000
EVIDENCE_SEED = 20260925
OUT = REPO / "docs/decisions/criterion-consequence-and-2016-evidence-study.json"


def _stem(kp: float, d70: str) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{d70}"


def _label(kp: float) -> str:
    return f"KP {kp:.1f}"


def _event_arrays(path: Path) -> dict[str, np.ndarray]:
    """The single 2016 event's per-row arrays, plus theta, from a posterior."""
    with h5py.File(path, "r") as h5:
        events = list(h5["events"].keys())
        if len(events) != 1:
            raise SystemExit(f"{path.name}: expected one event, found {events}")
        group = h5["events"][events[0]]
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in h5["param_names"][:]
        ]
        out = {
            k: np.asarray(group[k][:])
            for k in ("accept_trans", "accept_static", "Z_static", "initiation")
        }
        out["theta"] = np.asarray(h5["theta_matrix"][:], dtype=np.float64)
        out["param_names"] = names
        out["event_id"] = events[0]
    return out


def _crack_reduced_accept(arrays: dict[str, Any]) -> np.ndarray:
    """Survival under the crack-reduced static rule at the replayed peak.

    ``Z_static = H_c - (h_peak - z_toe)``; the crack-reduced rule compares H_c
    with ``(h_peak - z_toe) - 0.3 D_bl``, so its margin is ``Z_static + 0.3
    D_bl``. Failure is ``Z <= 0`` (ADR-0008), survival the strict complement.
    """
    d_bl = arrays["theta"][:, arrays["param_names"].index("D_bl")]
    return (arrays["Z_static"] + CRACK_COEFFICIENT * d_bl) > 0.0


def _paired_bootstrap(columns: np.ndarray, replicates: int, seed: int) -> np.ndarray:
    """Replicate means of boolean columns under a joint row resample."""
    rng = np.random.default_rng(seed)
    n = columns.shape[0]
    data = columns.astype(np.float64)
    out = np.empty((replicates, columns.shape[1]))
    for b in range(replicates):
        out[b] = data[rng.integers(0, n, size=n)].mean(axis=0)
    return out


def _ci(samples: np.ndarray) -> list[float] | None:
    samples = samples[np.isfinite(samples)]
    if samples.size == 0:
        return None
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return [float(lo), float(hi)]


# --------------------------------------------------------------------------- #
# Part: evidence                                                                #
# --------------------------------------------------------------------------- #
def _gross_replay(results_root: Path, kp: float, cache_dir: Path) -> np.ndarray:
    """Survival of the head-equalised transient under the 2016 replay.

    Cached as a boolean ``.npy`` in the worktree's own results so a rerun of
    the analysis does not repeat the replay. The settings are the production
    campaign's, read from its sidecar, exactly as the ADR-0050 arm replays do.
    """
    cache = cache_dir / f"{_stem(kp, 'matrix')}_gross_accept_trans.npy"
    if cache.is_file():
        return np.load(cache)
    from bayesian_reliability_updating.pipeline import (
        Phase2Settings,
        run_survival_update,
    )

    sidecar = results_root / "phase2" / f"{_stem(kp, 'matrix')}_posterior.json"
    ref = json.loads(sidecar.read_text(encoding="utf-8"))["phase2"]["settings"]
    settings = Phase2Settings(
        anchor=ref["anchor"],
        criterion=ref["criterion"],
        data_root=str(results_root.parent / ref["data_root"]),
        processed_dir=str(results_root.parent / ref["processed_dir"]),
        output_dir=str(cache_dir),
        verify_by_reevaluation=False,
        trace_breach_times=False,
        figures=False,
        n_bootstrap=ref["n_bootstrap"],
        confidence=ref["confidence"],
        progression_backend=ref["progression_backend"],
        overwrite=False,
        z_toe_delta_m=ref["z_toe_delta_m"],
    )
    source = results_root / "equal_head_convention" / f"{_stem(kp, 'matrix')}_gross.h5"
    tick = time.time()
    result = run_survival_update(source, settings=settings, persist=False)
    (event,) = result.events.values()
    accept = np.asarray(event.accept_trans, dtype=bool)
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.save(cache, accept)
    np.save(
        cache.with_name(cache.name.replace("accept_trans", "accept_static")),
        np.asarray(event.accept_static, dtype=bool),
    )
    print(f"  gross replay KP {kp:.1f}: {time.time() - tick:.0f} s", flush=True)
    return accept


def evidence_part(
    results_root: Path, cache_dir: Path, replicates: int
) -> dict[str, Any]:
    out: dict[str, Any] = {"per_stratum": {}, "joint": {}, "berm": {}}
    survival = {}
    for d70 in D70S:
        for kp in KPS:
            post = results_root / "phase2" / f"{_stem(kp, d70)}_posterior.h5"
            a = _event_arrays(post)
            t, s = a["accept_trans"].astype(bool), a["accept_static"].astype(bool)
            c1 = _crack_reduced_accept(a)
            cols = [s, c1, t]
            names = ["static_gross", "static_crack_reduced", "transient"]
            if d70 == "matrix":
                gross_t = _gross_replay(results_root, kp, cache_dir)
                gross_s = np.load(
                    cache_dir / f"{_stem(kp, 'matrix')}_gross_accept_static.npy"
                )
                # The static branch cannot see the crack coefficient: identical
                # rows, identical static survival, or the pairing is broken.
                if not np.array_equal(gross_s, s):
                    raise SystemExit(f"KP {kp}: gross-arm static survival differs")
                cols.append(gross_t)
                names.append("transient_gross_head")
            matrix = np.stack(cols, axis=1)
            # Nesting in survival terms: transient survival contains static
            # survival (a static survivor never fails transiently).
            nesting = {
                "static_survivors_failing_transient": int(np.sum(s & ~t)),
                "crack_reduced_survivors_failing_transient": int(np.sum(c1 & ~t)),
            }
            disagree = ~s & t
            ini = a["initiation"].astype(bool)
            nesting["disagreeing_rows"] = int(disagree.sum())
            nesting["disagreeing_rows_gate_opened"] = int(np.sum(disagree & ini))
            nesting["disagreeing_rows_gate_never_opened"] = int(np.sum(disagree & ~ini))
            if d70 == "matrix":
                nesting["static_survivors_failing_gross_transient"] = int(
                    np.sum(s & ~cols[3])
                )
                nesting["transient_survivors_failing_gross_transient"] = int(
                    np.sum(t & ~cols[3])
                )
            p = matrix.mean(axis=0)
            reps = _paired_bootstrap(
                matrix,
                replicates,
                EVIDENCE_SEED + int(kp * 10) + (0 if d70 == "matrix" else 7),
            )
            idx = {n: i for i, n in enumerate(names)}

            def lr(num: str, den: str) -> dict[str, Any]:
                point = float(p[idx[num]] / p[idx[den]])
                with np.errstate(divide="ignore", invalid="ignore"):
                    rep = reps[:, idx[num]] / reps[:, idx[den]]
                return {"point": point, "ci95": _ci(rep), "ln": float(np.log(point))}

            entry: dict[str, Any] = {
                "n": int(matrix.shape[0]),
                "survival_probability": {n: float(p[idx[n]]) for n in names},
                "rejection_fraction": {n: float(1.0 - p[idx[n]]) for n in names},
                "nesting": nesting,
                "LR_transient_over_static": lr("transient", "static_gross"),
                "LR_transient_over_crack_reduced_static": lr(
                    "transient", "static_crack_reduced"
                ),
                "LR_crack_reduced_over_gross_static": lr(
                    "static_crack_reduced", "static_gross"
                ),
            }
            if d70 == "matrix":
                entry["LR_gross_transient_over_static"] = lr(
                    "transient_gross_head", "static_gross"
                )
                entry["LR_transient_over_gross_transient"] = lr(
                    "transient", "transient_gross_head"
                )
                total = entry["LR_transient_over_static"]["ln"]
                if total > 0:
                    head_first = entry["LR_crack_reduced_over_gross_static"]["ln"]
                    head_last = entry["LR_transient_over_gross_transient"]["ln"]
                    entry["ln_LR_split"] = {
                        "total": total,
                        "head_convention_first": head_first,
                        "duration_and_gate_after_head": total - head_first,
                        "head_convention_last": head_last,
                        "duration_and_gate_first": total - head_last,
                        "head_share_first": head_first / total,
                        "head_share_last": head_last / total,
                        "head_share_shapley": 0.5 * (head_first + head_last) / total,
                    }
                survival[kp] = {n: float(p[idx[n]]) for n in names}
            out["per_stratum"][f"{_label(kp)} {d70}"] = entry

    # Joint over the four matrix sections, under one dependence structure
    # imposed on both criteria alike.
    for crit in ("static_gross", "static_crack_reduced", "transient_gross_head"):
        pt = np.array([survival[kp]["transient"] for kp in KPS])
        pc = np.array([survival[kp][crit] for kp in KPS])
        bounds = {
            "comonotone (maximal positive dependence)": (pt.min(), pc.min()),
            "independent": (pt.prod(), pc.prod()),
            "Frechet lower (maximal negative dependence)": (
                max(0.0, pt.sum() - 3.0),
                max(0.0, pc.sum() - 3.0),
            ),
        }
        out["joint"][f"transient over {crit}"] = {
            name: {
                "P_transient": float(a),
                "P_other": float(b),
                "LR": float(a / b) if b > 0 else None,
            }
            for name, (a, b) in bounds.items()
        }

    # Measured berm (ADR-0050 berm_only arm replays), matrix only.
    arm_dir = results_root / "sensitivity" / "adr0050_drained_bracket" / "phase2"
    for kp in (58.8, 60.0):
        path = arm_dir / f"{_stem(kp, 'matrix')}_berm_only_posterior.h5"
        a = _event_arrays(path)
        t, s = a["accept_trans"].astype(bool), a["accept_static"].astype(bool)
        c1 = _crack_reduced_accept(a)
        matrix = np.stack([s, c1, t], axis=1)
        p = matrix.mean(axis=0)
        reps = _paired_bootstrap(matrix, replicates, EVIDENCE_SEED + 900 + int(kp))
        with np.errstate(divide="ignore", invalid="ignore"):
            out["berm"][_label(kp)] = {
                "source": str(path.relative_to(results_root)).replace("\\", "/"),
                "rejection_fraction": {
                    "static_gross": float(1 - p[0]),
                    "static_crack_reduced": float(1 - p[1]),
                    "transient": float(1 - p[2]),
                },
                "LR_transient_over_static": {
                    "point": float(p[2] / p[0]),
                    "ci95": _ci(reps[:, 2] / reps[:, 0]),
                },
                "LR_transient_over_crack_reduced_static": {
                    "point": float(p[2] / p[1]),
                    "ci95": _ci(reps[:, 2] / reps[:, 1]),
                },
                "static_survivors_failing_transient": int(np.sum(s & ~t)),
            }
    return out


# --------------------------------------------------------------------------- #
# Part: hypothetical                                                            #
# --------------------------------------------------------------------------- #
def hypothetical_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for kp in KPS:
        with h5py.File(results_root / f"{_stem(kp, 'matrix')}.h5", "r") as h5:
            grid = np.asarray(h5["conditioning_grid"][:], dtype=float)
            ps = np.asarray(h5["failure_matrix_static"][:], dtype=bool).mean(axis=0)
            pt = np.asarray(h5["failure_matrix_trans"][:], dtype=bool).mean(axis=0)
            n = int(h5["failure_matrix_trans"].shape[0])
        keep = grid <= ATTAINABLE_MAX[kp] + 1e-9
        rows = []
        for h, s, t in zip(grid[keep], ps[keep], pt[keep], strict=True):
            rows.append(
                {
                    "stage_m": float(h),
                    "P_static": float(s),
                    "P_transient": float(t),
                    "LR_one_survival": float((1 - t) / (1 - s)) if s < 1 else None,
                    "LR_one_breach_transient_over_static": (
                        float(t / s) if s > 0 else None
                    ),
                    "static_survivors": int(round((1 - s) * n)),
                }
            )
        finite = [r for r in rows if r["LR_one_survival"] is not None]
        best = max(finite, key=lambda r: r["LR_one_survival"])
        out[_label(kp)] = {
            "attainable_max_m": ATTAINABLE_MAX[kp],
            "n": n,
            "levels": rows,
            "max_LR_one_survival": best,
        }
    return out


# --------------------------------------------------------------------------- #
# Part: annual                                                                  #
# --------------------------------------------------------------------------- #
def _static_self_posterior(results_root: Path, kp: float, d70: str):
    """The static curve conditioned on survival under the static criterion."""
    from bayesian_reliability_updating.fragility_update import (
        posterior_fragility_from_matrices,
    )
    from bayesian_reliability_updating.replay import load_phase1_run
    from system_integration.bep_input import FragilityCurve, _deliverable_fit

    run = load_phase1_run(results_root / f"{_stem(kp, d70)}.h5")
    arrays = _event_arrays(results_root / "phase2" / f"{_stem(kp, d70)}_posterior.h5")
    if not np.array_equal(arrays["theta"], run.result.theta_matrix):
        raise SystemExit(f"KP {kp} {d70}: posterior rows are not the Phase 1 rows")
    accept = arrays["accept_static"].astype(bool)
    frag = posterior_fragility_from_matrices(run, accept)
    lower, upper = frag.binomial_ci["static"]
    curve = FragilityCurve(
        grid_m_msl=np.asarray(frag.conditioning_grid, dtype=np.float64),
        p_raw=np.asarray(frag.P_f_static_post_raw, dtype=np.float64),
        ci_lower=np.asarray(lower, dtype=np.float64),
        ci_upper=np.asarray(upper, dtype=np.float64),
        fit=frag.P_f_static_post_fit,
        fit_is_deliverable=_deliverable_fit(
            frag.P_f_static_post_fit, np.asarray(frag.P_f_static_post_raw)
        ),
        branch="static",
        source="static_self_posterior",
        source_path=str(results_root / "phase2" / f"{_stem(kp, d70)}_posterior.h5"),
        datum_m=float(frag.settings["datum_m"]),
    )
    raw_only = _raw_of(curve, "static_self_posterior_raw")
    return curve, raw_only, int(accept.sum())


def _raw_of(curve, source: str):
    """The same curve evaluated by probit interpolation of its raw points only."""
    from system_integration.bep_input import FragilityCurve

    return FragilityCurve(
        grid_m_msl=curve.grid_m_msl,
        p_raw=curve.p_raw,
        ci_lower=curve.ci_lower,
        ci_upper=curve.ci_upper,
        fit=None,
        fit_is_deliverable=False,
        branch=curve.branch,
        source=source,
        source_path=curve.source_path,
        datum_m=curve.datum_m,
    )


def _fit_check(curve) -> dict[str, Any]:
    """How far the evaluated curve departs from its own raw points."""
    evaluated, _ = curve.evaluate(curve.grid_m_msl)
    dev = np.abs(evaluated - curve.p_raw)
    outside = (evaluated < curve.ci_lower - 1e-12) | (
        evaluated > curve.ci_upper + 1e-12
    )
    return {
        "fit_used": bool(curve.fit is not None and curve.fit_is_deliverable),
        "max_abs_deviation_from_raw": float(dev.max()),
        "levels_outside_binomial_ci": int(outside.sum()),
        "levels": int(curve.grid_m_msl.size),
        "raw": [float(x) for x in curve.p_raw],
        "evaluated": [float(x) for x in evaluated],
        "grid": [float(x) for x in curve.grid_m_msl],
    }


def annual_part(
    results_root: Path, replicates: int, d70s: tuple[str, ...]
) -> dict[str, Any]:
    import annualisation_uncertainty_study as unc

    from system_integration.bep_input import load_bep_curve

    data_repo = results_root.parent
    unc.PRODUCTION_TABLE = results_root / "system_integration/phase3/rq4_annual.csv"
    campaign = unc._load_campaign_module()
    campaign.REPO = data_repo
    campaign.DATA_ROOT = data_repo / "data/raw"
    campaign.HAZARD_CACHE = results_root / "system_integration/hazard_cache"
    cache_before = unc._dir_state(campaign.HAZARD_CACHE, "*.csv")

    context = unc.build_context(campaign)
    production = dict(context["bep_curves"])

    # The four production arms first: gate 1 needs all of them, and T-prior and
    # T-post of each reading are two of this study's branches.
    rows_by_arm: dict[str, Any] = {}
    per_event: dict[tuple[str, str], Any] = {}
    rows_by_branch: dict[tuple[str, str], Any] = {}
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
    for d70 in d70s:
        # S-prior: the Phase 1 static curve.
        for kp in KPS:
            context["bep_curves"][(kp, d70, "prior")] = load_bep_curve(
                campaign._bep_path(kp, d70, "prior"), branch="static"
            )
        static_prior = {kp: context["bep_curves"][(kp, d70, "prior")] for kp in KPS}
        static_post_fit, static_post_raw = {}, {}
        for kp in KPS:
            curve, raw_only, n_acc = _static_self_posterior(results_root, kp, d70)
            static_post_fit[kp], static_post_raw[kp] = curve, raw_only
            accepted[f"{_label(kp)} {d70}"] = n_acc
            for name, c in (
                ("S-post-fit", curve),
                ("S-prior", static_prior[kp]),
                ("T-post", production[(kp, d70, "posterior")]),
                ("T-prior", production[(kp, d70, "prior")]),
            ):
                fit_checks[f"{_label(kp)} {d70} {name}"] = _fit_check(c)
        # Each pass puts one branch's curve in the (prior | posterior) slot the
        # annualiser reads. S-post is the RAW evaluation: a static survival
        # truncates the resistance distribution at the survived stage, which a
        # lognormal cannot represent (pre-registered fallback, 1.2).
        passes = {
            "S-prior": ("prior", static_prior),
            "S-post": ("posterior", static_post_raw),
            "S-post-fit": ("posterior", static_post_fit),
            "T-prior-raw": (
                "prior",
                {kp: _raw_of(production[(kp, d70, "prior")], "raw") for kp in KPS},
            ),
            "T-post-raw": (
                "posterior",
                {kp: _raw_of(production[(kp, d70, "posterior")], "raw") for kp in KPS},
            ),
            "S-prior-raw": (
                "prior",
                {kp: _raw_of(static_prior[kp], "raw") for kp in KPS},
            ),
        }
        for branch, (slot, curves) in passes.items():
            for kp in KPS:
                context["bep_curves"][(kp, d70, slot)] = curves[kp]
            rows, pe = unc.annualise_arm(campaign, context, d70, slot)
            rows_by_branch[(d70, branch)], per_event[(d70, branch)] = rows, pe
            for kp in KPS:
                context["bep_curves"][(kp, d70, slot)] = production[(kp, d70, slot)]
        # Restore production curves so nothing leaks into a later pass.
        for kp in KPS:
            for source in ("prior", "posterior"):
                context["bep_curves"][(kp, d70, source)] = production[(kp, d70, source)]

    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")

    # Gate 2: the 110 surface-only segments must be identical across branches.
    moved = 0
    for (d70, branch), rows in rows_by_branch.items():
        base = rows_by_branch[(d70, "T-post")]
        for key, row in rows.items():
            if round(key[1], 3) in {round(k, 3) for k in KPS} and key[0] == "Tokachi":
                continue
            if {k: v for k, v in row.items() if k != "bep_source"} != {
                k: v for k, v in base[key].items() if k != "bep_source"
            }:
                moved += 1
    if moved:
        raise SystemExit(f"GATE 2 FAILED: {moved} surface-only cells moved")

    # Where the annual probability is earned: the share of each branch's annual
    # system probability contributed by years whose peak exceeds the design
    # high water level, and the probability-weighted mean peak.
    earned: dict[str, Any] = {}
    for d70 in d70s:
        for branch in ("T-prior", "T-post", "S-prior", "S-post"):
            for scenario in campaign.SCENARIOS:
                for kp in KPS:
                    peaks = np.asarray(
                        context["hazards"][scenario][("Tokachi", kp)].peak_stages()
                    )
                    vals = np.asarray(
                        per_event[(d70, branch)][("Tokachi", kp, scenario)][
                            "__system__"
                        ]
                    )
                    total = float(vals.sum())
                    above = peaks > DESIGN_HWL[kp]
                    earned[f"{d70} {branch} {_label(kp)} {scenario}"] = {
                        "share_from_peaks_above_design_level": (
                            float(vals[above].sum() / total) if total else None
                        ),
                        "fraction_of_years_above_design_level": float(above.mean()),
                        "probability_weighted_mean_peak_m": (
                            float((vals * peaks).sum() / total) if total else None
                        ),
                        "design_hwl_m": DESIGN_HWL[kp],
                    }

    branch_names = list(BRANCHES) + [
        "S-post-fit",
        "T-prior-raw",
        "T-post-raw",
        "S-prior-raw",
    ]
    out: dict[str, Any] = {
        "gates": {
            "gate_1": gate1,
            "gate_2": {"passed": True, "criterion": "surface-only segments identical"},
            "hazard_cache_unchanged": True,
        },
        "static_self_posterior_accepted_rows": accepted,
        "where_annual_probability_is_earned": earned,
        "fit_checks": fit_checks,
        "estimator": (
            "d4PDF member-block bootstrap, stratified inside the prescribed SST "
            "patterns (one stratum historically), fragility curves fixed; one "
            "draw per scenario shared by every branch and section"
        ),
        "replicates": replicates,
        "seed": unc.SEED,
    }
    for d70 in d70s:
        rng = np.random.default_rng(unc.SEED)
        block: dict[str, Any] = {}
        reps_store: dict[tuple[str, str, float, str], np.ndarray] = {}
        points: dict[tuple[str, float, str, str], float] = {}
        for scenario in campaign.SCENARIOS:
            ids = [
                e.event_id
                for e in context["hazards"][scenario][("Tokachi", 58.8)].events
            ]
            index, n_blocks, _ = unc.block_index(unc.block_labels(ids, "member"))
            strata = unc.stratum_columns(ids)
            mult = unc.draw_multiplicities_stratified(strata, n_blocks, replicates, rng)
            for branch in branch_names:
                pe = per_event[(d70, branch)]
                for kp in KPS:
                    values = pe[("Tokachi", kp, scenario)]
                    reps = unc.node_replicates(values, index, n_blocks, mult, len(ids))
                    shares = unc.share_replicates(reps)
                    reps_store[(branch, scenario, kp, "system")] = reps["__system__"]
                    reps_store[(branch, scenario, kp, "share_bep")] = shares.get(
                        "bep", np.full(replicates, np.nan)
                    )
                    reps_store[(branch, scenario, kp, "bep")] = reps["bep"]
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
                    points[(branch, kp, scenario, "clamped")] = bool(
                        row["bep_clamped_above_grid"]
                    )
        for branch in branch_names:
            entry: dict[str, Any] = {}
            for scenario in campaign.SCENARIOS:
                sec: dict[str, Any] = {}
                vals = {
                    kp: points[(branch, kp, scenario, "p_annual_system")] for kp in KPS
                }
                order = sorted(KPS, key=lambda k: -vals[k])
                stack = np.column_stack(
                    [reps_store[(branch, scenario, kp, "system")] for kp in KPS]
                )
                same_order = float(
                    np.mean(
                        np.all(
                            np.argsort(-stack, axis=1)
                            == np.argsort(-np.array([vals[k] for k in KPS])),
                            axis=1,
                        )
                    )
                )
                for kp in KPS:
                    sys_reps = reps_store[(branch, scenario, kp, "system")]
                    share_reps = reps_store[(branch, scenario, kp, "share_bep")]
                    bep_reps = reps_store[(branch, scenario, kp, "bep")]
                    ovf_reps = reps_store[(branch, scenario, kp, "overflow")]
                    p_bep = points[(branch, kp, scenario, "p_annual_bep")]
                    p_ovf = points[(branch, kp, scenario, "p_annual_overflow")]
                    sec[_label(kp)] = {
                        "p_annual_system": vals[kp],
                        "ci95": _ci(sys_reps),
                        "p_annual_bep": p_bep,
                        "p_annual_overflow": p_ovf,
                        "share_bep": points[(branch, kp, scenario, "share_bep")],
                        "share_bep_ci95": _ci(share_reps),
                        "leading": (
                            "not loaded"
                            if p_bep + p_ovf == 0
                            else ("piping" if p_bep >= p_ovf else "overflow")
                        ),
                        "fraction_replicates_piping_leads": float(
                            np.mean(bep_reps > ovf_reps)
                        ),
                        "rank": order.index(kp) + 1,
                        "bep_clamped_above_grid": points[
                            (branch, kp, scenario, "clamped")
                        ],
                    }
                sec["order"] = [_label(k) for k in order]
                sec["fraction_replicates_with_this_order"] = same_order
                entry[scenario] = sec
            ratios = {}
            for kp in KPS:
                h = reps_store[(branch, "historical", kp, "system")]
                w = reps_store[(branch, "+4K", kp, "system")]
                ph = points[(branch, kp, "historical", "p_annual_system")]
                pw = points[(branch, kp, "+4K", "p_annual_system")]
                defined, n_undef = unc.ratio_replicates(h, w)
                ratios[_label(kp)] = {
                    "point": (pw / ph) if ph else None,
                    "ci95": _ci(defined) if defined.size else None,
                    "n_undefined_replicates": n_undef,
                }
            entry["climate_ratio"] = ratios
            block[branch] = entry

        # Paired comparisons between branches, per section and scenario.
        comparisons: dict[str, Any] = {}
        pairs = (
            ("S-prior", "T-prior"),
            ("S-post", "T-post"),
            ("S-post-fit", "T-post"),
            ("S-prior-raw", "T-prior-raw"),
            ("S-post", "T-post-raw"),
            ("T-post", "T-prior"),
            ("S-post", "S-prior"),
        )
        for num, den in pairs:
            comp: dict[str, Any] = {}
            for scenario in campaign.SCENARIOS:
                for kp in KPS:
                    a = reps_store[(num, scenario, kp, "system")]
                    b = reps_store[(den, scenario, kp, "system")]
                    pa = points[(num, kp, scenario, "p_annual_system")]
                    pb = points[(den, kp, scenario, "p_annual_system")]
                    with np.errstate(divide="ignore", invalid="ignore"):
                        r = a / b
                    with np.errstate(divide="ignore", invalid="ignore"):
                        db = norm.isf(b) - norm.isf(a)
                    comp[f"{_label(kp)} {scenario}"] = {
                        "point": (pa / pb) if pb else None,
                        "ci95": _ci(r),
                        "fraction_num_above_den": float(np.mean(a > b)),
                        "delta_beta_den_minus_num": (
                            float(norm.isf(pb) - norm.isf(pa)) if pa and pb else None
                        ),
                        "delta_beta_ci95": _ci(db),
                    }
            for kp in KPS:
                ha, wa = (
                    reps_store[(num, "historical", kp, "system")],
                    reps_store[(num, "+4K", kp, "system")],
                )
                hb, wb = (
                    reps_store[(den, "historical", kp, "system")],
                    reps_store[(den, "+4K", kp, "system")],
                )
                with np.errstate(divide="ignore", invalid="ignore"):
                    diff = (wa / ha) / (wb / hb)
                ra = block[num]["climate_ratio"][_label(kp)]["point"]
                rb = block[den]["climate_ratio"][_label(kp)]["point"]
                comp[f"{_label(kp)} climate-ratio quotient"] = {
                    "point": (ra / rb) if (ra and rb) else None,
                    "ci95": _ci(diff),
                    "fraction_num_ratio_above_den": float(np.nanmean(diff > 1.0)),
                }
            comparisons[f"{num} / {den}"] = comp
        out[d70] = {"branches": block, "paired_comparisons": comparisons}
    return out


# --------------------------------------------------------------------------- #
# Part: figure                                                                  #
# --------------------------------------------------------------------------- #
FIGURE_NAME = "criterion_survival_evidence.png"
#: Landside-toe elevations and 2016 replayed peaks [m T.P.], for the x offset.
PEAK_2016 = {57.4: 39.66, 58.8: 40.75, 60.0: 42.30, 62.0: 45.73}


def figure_part(record: dict[str, Any]) -> Path:
    """What one survival, or one breach, says between the two criteria."""
    import _figstyle as fs
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    width = fs.TEXTWIDTH_IN
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(1, 2, figsize=(width, 0.42 * width), sharex=True)
    hyp = record["hypothetical"]
    ev = record["evidence"]["per_stratum"]
    handles = []
    for kp in KPS:
        key = f"KP{kp:.1f}"
        colour, marker = fs.SECTION_COLORS[key], fs.SECTION_MARKERS[key]
        levels = hyp[_label(kp)]["levels"]
        x = np.array([r["stage_m"] for r in levels]) - DESIGN_HWL[kp]
        surv = np.array([r["LR_one_survival"] for r in levels], dtype=float)
        brk = np.array(
            [
                (
                    np.nan
                    if r["LR_one_breach_transient_over_static"] in (None, 0.0)
                    else r["LR_one_breach_transient_over_static"]
                )
                for r in levels
            ],
            dtype=float,
        )
        axes[0].plot(x, surv, color=colour, lw=1.6)
        axes[1].plot(x, brk, color=colour, lw=1.6)
        lr2016 = ev[f"{_label(kp)} matrix"]["LR_transient_over_static"]["point"]
        axes[0].plot(
            PEAK_2016[kp] - DESIGN_HWL[kp],
            lr2016,
            marker=marker,
            ms=7,
            color=colour,
            mec=fs.INK,
            mew=0.8,
            ls="none",
            zorder=5,
        )
        handles.append(
            Line2D(
                [],
                [],
                color=colour,
                lw=1.6,
                marker=marker,
                ms=6,
                mec=fs.INK,
                mew=0.8,
                label=fs.section_label(f"tokachi_kp{kp:.1f}"),
            )
        )
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

    def _plain(value, _pos):
        return f"{value:g}"

    for ax, ticks in (
        (axes[0], [1, 2, 5, 10, 20, 40]),
        (axes[1], [0.01, 0.03, 0.1, 0.3, 1]),
    ):
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(FixedLocator(ticks))
        ax.yaxis.set_major_formatter(FuncFormatter(_plain))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.axhline(1.0, color=fs.BASELINE, lw=1.0, zorder=1)
        ax.axvline(0.0, color=fs.MUTED, lw=0.8, zorder=1)
        ax.set_xlabel("Stage above the design water level (m)")
        ax.set_ylabel("Likelihood ratio")
        ax.set_xlim(-2.0, 4.3)
    axes[0].set_ylim(0.85, 50.0)
    fs.panel_title(axes[0], "One survival", scale=scale, letter="a")
    fs.panel_title(axes[1], "One breach", scale=scale, letter="b")
    axes[1].set_ylim(4e-3, 1.6)
    fs.title(fig, "What one flood outcome says between the two criteria", scale=scale)
    handles.append(
        Line2D(
            [],
            [],
            color=fs.MUTED,
            marker="o",
            ms=6,
            mec=fs.INK,
            mew=0.8,
            ls="none",
            label="the replayed 2016 record",
        )
    )
    fs.legend_below(fig, handles, [h.get_label() for h in handles], scale=scale)
    fs.layout(fig, scale=scale, legend_rows=1)
    return fs.save(fig, FIGURE_NAME, mirror=REPO / "results" / "criterion_consequence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-root", type=Path, default=REPO / "results")
    parser.add_argument(
        "--cache-dir", type=Path, default=REPO / "results" / "criterion_consequence"
    )
    parser.add_argument(
        "--parts", nargs="+", default=["evidence", "hypothetical", "annual"]
    )
    parser.add_argument("--replicates", type=int, default=10_000)
    parser.add_argument("--evidence-bootstrap", type=int, default=EVIDENCE_BOOTSTRAP)
    parser.add_argument("--annual-d70", nargs="+", default=list(D70S))
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    record: dict[str, Any] = {}
    if args.out.is_file():
        record = json.loads(args.out.read_text(encoding="utf-8"))
    record.update(
        {
            "study": "Criterion consequence downstream, and the 2016 evidence between "
            "the static and transient criteria (Green Light item 2)",
            "generated": datetime.now().isoformat(timespec="seconds"),
            "generated_by": "scripts/criterion_consequence_study.py",
            "note": "docs/decisions/criterion-consequence-and-2016-evidence-study.md",
        }
    )
    if "evidence" in args.parts:
        print("evidence ...", flush=True)
        record["evidence"] = evidence_part(
            args.results_root, args.cache_dir, args.evidence_bootstrap
        )
    if "hypothetical" in args.parts:
        print("hypothetical ...", flush=True)
        record["hypothetical"] = hypothetical_part(args.results_root)
    if "annual" in args.parts:
        print("annual ...", flush=True)
        record["annual"] = annual_part(
            args.results_root, args.replicates, tuple(args.annual_d70)
        )
    if "figure" in args.parts:
        print(f"wrote {figure_part(record)}")
        if args.parts == ["figure"]:
            return
    args.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
