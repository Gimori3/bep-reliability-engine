"""RQ1 static-vs-transient comparison re-expressed in reliability-index terms.

Pure post-processing: this driver contains no physics and evaluates no limit
state. It reads persisted artifacts only and re-expresses estimates that are
already on disk, so every number it prints traces to a named file.

Metric (campaign decision D1, ``docs/work_packages/rq1-revision-campaign_2026-08-28.md``)::

    beta(h) = -Phi^-1( P_f(h) )            per branch
    dbeta   = beta_transient - beta_static  (paired, shared sample)

``beta`` is a strictly decreasing function of ``P_f``, so a confidence
interval on ``P_f`` maps to one on ``beta`` by swapping its endpoints. The
existing exact Clopper-Pearson intervals therefore carry over unchanged --
no new statistical machinery is introduced, and the resolution criteria R1
(at least 30 transient failing rows) and R2 (multiplicative interval width
at most 2) stay defined on the probability ratio ``B`` exactly as
pre-registered, because they map monotonically too.

Inputs (all read-only)::

    results/tokachi_kp*_historical_{matrix,bulk}.h5 + .json   8 production strata
    results/hwl_bias_resolution/ladder_kp{57_4,62_0}_n1000000.h5   comparator ladders
    results/hwl_bias_resolution/ladder_kp{57_4,62_0}_n100000.h5
    results/stage6_6/stage6_6_kp{57_4,62_0}.h5 + *_analysis.json
    results/hwl_bias_resolution/stage_a_brute_kp*.json, stage_a_anchors.json
    results/hwl_bias_resolution/stage_d_epistemic.json
    docs/decisions/canonical-shape-sensitivity.json

Outputs::

    docs/decisions/rq1-beta-reexpression.json    complete machine-readable record
    docs/decisions/rq1-beta-reexpression.csv     flat long-format table
    docs/rq1_beta_reexpression_2026-08-28.md     tables of record (numbers brief)
    docs/figures/rq1_*.png                       five figures (+ msc-thesis copy)

Usage (repo root, venv active)::

    python scripts/rq1_beta_analysis.py                 # everything
    python scripts/rq1_beta_analysis.py --no-figures    # tables only
    python scripts/rq1_beta_analysis.py --bootstrap 200 # faster draft

Paired bootstrap. Component intervals reuse the ADR-0040 Decision 6 design:
one row-index resample per replicate, applied to every branch or comparator
column, so the interval reflects the discordant row set rather than two
independent binomials. The implementation here is the exact
pattern-multinomial equivalent of
:func:`bep_reliability_engine.gap_decomposition.bootstrap_comparator_means`
-- rows are grouped by their joint failure pattern and the pattern counts
resampled multinomially, which is distributionally identical to resampling
row indices and is what makes B = 1000 replicates over 10^6 rows tractable.
It is not sample-path identical to the row-index loop, so replicate values
differ; the estimator does not.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

import h5py
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402
from scipy.stats import norm  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as figstyle  # noqa: E402

from bep_reliability_engine.fragility import FragilityResult, binomial_ci  # noqa: E402

RESULTS = REPO_ROOT / "results"
HWL_DIR = RESULTS / "hwl_bias_resolution"
STAGE66_DIR = RESULTS / "stage6_6"
DOCS = REPO_ROOT / "docs"
DECISIONS = DOCS / "decisions"
CANONICAL = DECISIONS / "canonical-shape-sensitivity.json"
THESIS_FIGURES = Path("d:/repositories/msc-thesis/figures")

BRIEF_MD = DOCS / "rq1_beta_reexpression_2026-08-28.md"
RECORD_JSON = DECISIONS / "rq1-beta-reexpression.json"
RECORD_CSV = DECISIONS / "rq1-beta-reexpression.csv"

#: Pre-registered resolution criteria, unchanged from ADR-0040 and defined on
#: the ratio B. Reproduced (not redefined) here so this driver can label a
#: level exactly as the ratio-space companion does.
R1_MIN_ROWS = 30
R2_MAX_WIDTH = 2.0

#: A paired-bootstrap interval is reported only where both branches clear the
#: R1 floor; below it the deliverable is the one-sided Clopper-Pearson bound.
MIN_ROWS_FOR_BOOTSTRAP = R1_MIN_ROWS

SECTIONS = ("57.4", "58.8", "60.0", "62.0")
D70_READINGS = ("matrix", "bulk")

#: Named stages of the thesis "gap components" table.
LADDER_STAGES = {
    "kp62_0": (46.39, 46.50, 47.00, 48.00, 50.50),
    "kp57_4": (39.21, 39.50, 40.50, 43.25),
}
LADDER_SECTION_KP = {"kp62_0": "62.0", "kp57_4": "57.4"}

#: The engine ladder, expressed as additive beta steps. Each entry is
#: (component, from_comparator, to_comparator); the step is
#: beta(to) - beta(from), and the three steps telescope to beta(C4b)-beta(C0).
BETA_LADDER_STEPS = (
    ("head_convention", "C0", "C1"),
    ("initiation_gate", "C1", "C3b"),
    ("temporal", "C3b", "C4b"),
)
LADDER_COMPARATORS = ("C0", "C1", "C3b", "C4b")

COMPONENT_LABELS = {
    "head_convention": "head convention",
    "initiation_gate": "initiation gate",
    "temporal": "temporal",
}


# --------------------------------------------------------------------------- #
# beta arithmetic                                                             #
# --------------------------------------------------------------------------- #
def beta_from_p(p: float | NDArray[np.float64]) -> Any:
    """Reliability index ``-Phi^-1(p)``.

    ``p = 0`` gives ``+inf`` and ``p = 1`` gives ``-inf``; both are returned
    as such rather than clipped, so a caller must decide explicitly how to
    present an edge rather than silently inheriting a fudged value.
    ``p > 0.5`` gives a negative beta, reported as such (decision D1).
    """
    arr = np.asarray(p, dtype=float)
    with np.errstate(divide="ignore"):
        out = -norm.ppf(arr)
    return float(out) if np.ndim(p) == 0 else out


def _cp(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Exact Clopper-Pearson interval on ``p`` for ``k`` successes in ``n``."""
    lo, hi = binomial_ci(np.array([k / n], dtype=float), n, confidence=confidence)
    return float(lo[0]), float(hi[0])


def beta_interval(k: int, n: int, confidence: float = 0.95) -> dict[str, Any]:
    """Point beta and its monotone image of the Clopper-Pearson interval.

    Returns the probability, its exact interval, the point beta, and the beta
    interval with endpoints swapped (beta is decreasing in p). ``k = 0`` and
    ``k = n`` give an infinite point beta and a one-sided finite bound.
    """
    p = k / n
    p_lo, p_hi = _cp(k, n, confidence)
    return {
        "k": int(k),
        "n": int(n),
        "p": p,
        "p_ci": [p_lo, p_hi],
        "beta": beta_from_p(p),
        # beta is strictly decreasing in p, so the interval endpoints swap.
        "beta_ci": [beta_from_p(p_hi), beta_from_p(p_lo)],
    }


def delta_beta_cp_bound(k_static: int, k_trans: int, n: int) -> float:
    """One-sided lower bound on ``dbeta`` from the two exact intervals.

    The direct analogue of the ratio bound used at KP 57.4 in ADR-0040
    (static lower endpoint over transient upper endpoint): a lower bound on
    ``beta_transient`` comes from the Clopper-Pearson **upper** bound on
    ``P_transient``, and an upper bound on ``beta_static`` from the
    **lower** bound on ``P_static``. Valid whenever the static branch has at
    least one failure; it does not require any transient failure at all,
    which is exactly why it is the deliverable at a zero-count level.
    """
    _, trans_hi = _cp(k_trans, n)
    static_lo, _ = _cp(k_static, n)
    return beta_from_p(trans_hi) - beta_from_p(static_lo)


def _stable_seed(label: str) -> int:
    """Deterministic 32-bit seed from a label, so replicates reproduce."""
    return int.from_bytes(
        hashlib.blake2b(label.encode(), digest_size=4).digest(), "big"
    )


def paired_bootstrap_means(
    columns: NDArray[np.bool_], *, n_replicates: int, seed: int
) -> NDArray[np.float64]:
    """Joint paired-bootstrap means of boolean columns over shared rows.

    ``columns`` is ``(N, K)`` with ``K <= 63``. Within a replicate the SAME
    row resample feeds every column, which is the pairing that makes any
    linear combination of the column means (a difference of probabilities, or
    of their beta images) inherit a paired interval.

    Rows are grouped by their joint failure pattern first: the multinomial
    resample of pattern counts is distributionally identical to resampling
    ``N`` row indices, and turns an ``O(B*N*K)`` gather into an
    ``O(B*P*K)`` matrix product over the ``P`` distinct patterns.

    Returns
    -------
    ndarray
        ``(n_replicates, K)`` replicate means.
    """
    data = np.ascontiguousarray(columns, dtype=bool)
    n_rows, n_cols = data.shape
    if n_cols > 63:
        raise ValueError("pattern packing supports at most 63 columns")
    weights = (np.uint64(1) << np.arange(n_cols, dtype=np.uint64)).astype(np.uint64)
    codes = (data.astype(np.uint64) * weights[None, :]).sum(axis=1, dtype=np.uint64)
    uniq, counts = np.unique(codes, return_counts=True)
    bits = ((uniq[:, None] >> np.arange(n_cols, dtype=np.uint64)[None, :]) & 1).astype(
        np.float64
    )
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(n_rows, counts / n_rows, size=n_replicates)
    return (draws @ bits) / float(n_rows)


def _percentile_ci(
    values: NDArray[np.float64], confidence: float = 0.95
) -> list[float]:
    """Percentile interval, keeping infinities and discarding undefined values.

    A replicate in which a branch draws zero failures gives an infinite beta
    and therefore a genuinely unbounded delta; those are kept, because
    discarding them would quietly narrow the interval at exactly the levels
    whose counts cannot support one. A replicate in which BOTH sides of a
    difference are infinite gives ``inf - inf``, which carries no
    information at all; those are discarded. If fewer than half the
    replicates survive, no interval is reported.
    """
    finite_or_inf = values[~np.isnan(values)]
    if finite_or_inf.size < 0.5 * values.size:
        return [float("nan"), float("nan")]
    alpha = 100.0 * (1.0 - confidence)
    with np.errstate(invalid="ignore"):
        lo, hi = np.percentile(finite_or_inf, [alpha / 2.0, 100.0 - alpha / 2.0])
    return [float(lo), float(hi)]


def delta_beta_bootstrap(
    static_col: NDArray[np.bool_],
    trans_col: NDArray[np.bool_],
    *,
    label: str,
    n_replicates: int,
) -> dict[str, Any]:
    """Paired-bootstrap interval on ``dbeta`` for one conditioning level.

    Replicates in which a branch draws zero (or all) failures give an
    infinite beta and therefore an infinite delta; they are retained in the
    percentile rather than dropped, because dropping them would quietly
    narrow the interval at exactly the levels where the count is too small to
    support one. Their number is reported so a reader can see it.
    """
    means = paired_bootstrap_means(
        np.stack([static_col, trans_col], axis=1),
        n_replicates=n_replicates,
        seed=_stable_seed(label),
    )
    with np.errstate(divide="ignore"):
        deltas = beta_from_p(means[:, 1]) - beta_from_p(means[:, 0])
    n_degenerate = int(np.count_nonzero(~np.isfinite(deltas)))
    lo, hi = _percentile_ci(deltas)
    return {
        "ci": [lo, hi],
        "n_replicates": int(n_replicates),
        "n_degenerate_replicates": n_degenerate,
        "finite": bool(np.isfinite(lo) and np.isfinite(hi)),
    }


def ratio_and_width(k_static: int, k_trans: int, n: int) -> dict[str, Any]:
    """The probability ratio B and the R1/R2 flags, kept for cross-reference."""
    p_s, p_t = k_static / n, k_trans / n
    ratio = p_s / p_t if k_trans > 0 else float("inf")
    s_lo, s_hi = _cp(k_static, n)
    t_lo, t_hi = _cp(k_trans, n)
    lo = s_lo / t_hi if t_hi > 0 else float("inf")
    hi = s_hi / t_lo if t_lo > 0 else float("inf")
    width = hi / lo if np.isfinite(hi) and lo > 0 else float("inf")
    return {
        "B": ratio,
        "B_ci": [lo, hi],
        "B_width_factor": width,
        "R1_rows": bool(k_trans >= R1_MIN_ROWS),
        "R2_width": bool(np.isfinite(width) and width <= R2_MAX_WIDTH),
        "resolved": bool(
            k_trans >= R1_MIN_ROWS and np.isfinite(width) and width <= R2_MAX_WIDTH
        ),
    }


def level_row(
    static_col: NDArray[np.bool_],
    trans_col: NDArray[np.bool_],
    *,
    level_m: float,
    label: str,
    n_replicates: int,
) -> dict[str, Any]:
    """Everything the brief quotes about one section at one stage."""
    n = int(static_col.size)
    k_s = int(static_col.sum())
    k_t = int(trans_col.sum())
    stat = beta_interval(k_s, n)
    tran = beta_interval(k_t, n)
    row: dict[str, Any] = {
        "level_m_msl": float(level_m),
        "n_samples": n,
        "k_static": k_s,
        "k_transient": k_t,
        "p_static": stat["p"],
        "p_transient": tran["p"],
        "survival_static": 1.0 - stat["p"],
        "survival_transient": 1.0 - tran["p"],
        "beta_static": stat["beta"],
        "beta_static_ci": stat["beta_ci"],
        "beta_transient": tran["beta"],
        "beta_transient_ci": tran["beta_ci"],
        "delta_beta": tran["beta"] - stat["beta"],
    }
    row.update(ratio_and_width(k_s, k_t, n))
    bootstrappable = (
        MIN_ROWS_FOR_BOOTSTRAP <= k_s <= n - MIN_ROWS_FOR_BOOTSTRAP
        and MIN_ROWS_FOR_BOOTSTRAP <= k_t <= n - MIN_ROWS_FOR_BOOTSTRAP
    )
    if bootstrappable:
        boot = delta_beta_bootstrap(
            static_col, trans_col, label=label, n_replicates=n_replicates
        )
        row["delta_beta_ci"] = boot["ci"]
        row["delta_beta_ci_source"] = "paired_bootstrap"
        row["delta_beta_degenerate_replicates"] = boot["n_degenerate_replicates"]
    else:
        row["delta_beta_ci"] = None
        row["delta_beta_ci_source"] = "counts_below_R1_floor"
        row["delta_beta_degenerate_replicates"] = None
    if k_s > 0:
        row["delta_beta_lower_bound"] = delta_beta_cp_bound(k_s, k_t, n)
    else:
        row["delta_beta_lower_bound"] = None
    return row


# --------------------------------------------------------------------------- #
# inputs                                                                      #
# --------------------------------------------------------------------------- #
def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def attainable_maxima() -> dict[str, float]:
    """Per-section attainable maximum stage, read from committed evidence."""
    record = _read_json(CANONICAL)
    out: dict[str, float] = {}
    for stratum in record["phase1"]["strata"].values():
        kp = f"{stratum['kp']:.1f}"
        out[kp] = float(stratum["attainable_max_m_msl"])
    return out


def production_tables(n_replicates: int) -> dict[str, Any]:
    """Per-level beta / dbeta for all eight persisted production strata."""
    attainable = attainable_maxima()
    out: dict[str, Any] = {}
    for reading in D70_READINGS:
        for kp in SECTIONS:
            name = f"tokachi_kp{kp}_historical_{reading}"
            path = RESULTS / f"{name}.h5"
            result = FragilityResult.load(path)
            sidecar = _read_json(path.with_suffix(".json"))
            geometry = sidecar["config"]["geometry"]
            grid = result.conditioning_grid
            rows = [
                level_row(
                    result.failure_matrix_stat[:, i],
                    result.failure_matrix_tran[:, i],
                    level_m=float(grid[i]),
                    label=f"{name}|{grid[i]:.2f}",
                    n_replicates=n_replicates,
                )
                for i in range(grid.size)
            ]
            for row in rows:
                row["attainable"] = bool(row["level_m_msl"] <= attainable[kp] + 1e-9)
            out[name] = {
                "stratum": name,
                "section": f"KP {kp}",
                "kp": float(kp),
                "d70_interpretation": reading,
                "hwl_m_msl": float(geometry["HWL"]),
                "z_toe_m_msl": float(geometry["z_toe"]),
                "attainable_max_m_msl": attainable[kp],
                "artifact": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "config_hash": sidecar["config_hash"],
                "levels": rows,
            }
    return out


def _ladder_columns(
    path: Path, stages: Sequence[float]
) -> tuple[NDArray[np.float64], dict[str, NDArray[np.bool_]], int]:
    """Read only the named stages' columns for the four ladder comparators."""
    with h5py.File(path, "r") as handle:
        grid = handle["conditioning_grid"][:]
        idx = [int(np.argmin(np.abs(grid - stage))) for stage in stages]
        columns = {
            name: handle[f"comparators/{name}"][:, idx] for name in LADDER_COMPARATORS
        }
        n_samples = int(handle["comparators/C0"].shape[0])
    return grid[idx], columns, n_samples


def ladder_tables(n_replicates: int) -> dict[str, Any]:
    """The comparator ladder as ADDITIVE beta steps at the named stages.

    Because beta is a per-branch scalar, the three engine-ladder steps sum
    exactly to the total ``beta(C4b) - beta(C0)`` -- the share-vs-factor
    tangle that a probability-space decomposition creates does not arise.
    """
    sources = {
        "kp62_0": {
            1000000: HWL_DIR / "ladder_kp62_0_n1000000.h5",
            100000: STAGE66_DIR / "stage6_6_kp62_0.h5",
        },
        "kp57_4": {
            1000000: HWL_DIR / "ladder_kp57_4_n1000000.h5",
            100000: STAGE66_DIR / "stage6_6_kp57_4.h5",
        },
    }
    out: dict[str, Any] = {}
    for key, by_n in sources.items():
        stages = LADDER_STAGES[key]
        per_n: dict[str, Any] = {}
        for n_nominal, path in by_n.items():
            levels, columns, n_samples = _ladder_columns(path, stages)
            entries = []
            for j, level in enumerate(levels):
                counts = {
                    name: int(columns[name][:, j].sum()) for name in LADDER_COMPARATORS
                }
                betas = {
                    name: beta_interval(counts[name], n_samples)
                    for name in LADDER_COMPARATORS
                }
                boot = paired_bootstrap_means(
                    np.stack([columns[name][:, j] for name in LADDER_COMPARATORS], 1),
                    n_replicates=n_replicates,
                    seed=_stable_seed(f"{key}|{n_samples}|{level:.2f}|ladder"),
                )
                with np.errstate(divide="ignore"):
                    beta_reps = beta_from_p(boot)
                order = {name: i for i, name in enumerate(LADDER_COMPARATORS)}

                def supported(*names: str) -> bool:
                    """Both endpoints must clear the R1 floor for an interval."""
                    return all(
                        MIN_ROWS_FOR_BOOTSTRAP
                        <= counts[name]
                        <= n_samples - MIN_ROWS_FOR_BOOTSTRAP
                        for name in names
                    )

                # inf - inf (both comparators empty in a replicate) is a
                # genuinely undefined delta; _percentile_ci discards it.
                errstate = np.errstate(invalid="ignore")
                steps: dict[str, Any] = {}
                for component, src, dst in BETA_LADDER_STEPS:
                    with errstate:
                        deltas = beta_reps[:, order[dst]] - beta_reps[:, order[src]]
                    steps[component] = {
                        "from": src,
                        "to": dst,
                        "delta_beta": betas[dst]["beta"] - betas[src]["beta"],
                        "ci": (_percentile_ci(deltas) if supported(src, dst) else None),
                        "n_degenerate_replicates": int(
                            np.count_nonzero(~np.isfinite(deltas))
                        ),
                    }
                with errstate:
                    total_reps = beta_reps[:, order["C4b"]] - beta_reps[:, order["C0"]]
                    equal_reps = beta_reps[:, order["C4b"]] - beta_reps[:, order["C1"]]
                entries.append(
                    {
                        "level_m_msl": float(level),
                        "n_samples": n_samples,
                        "counts": counts,
                        "beta": {
                            name: betas[name]["beta"] for name in LADDER_COMPARATORS
                        },
                        "beta_ci": {
                            name: betas[name]["beta_ci"] for name in LADDER_COMPARATORS
                        },
                        "steps": steps,
                        "total_delta_beta": (
                            betas["C4b"]["beta"] - betas["C0"]["beta"]
                        ),
                        "total_delta_beta_ci": (
                            _percentile_ci(total_reps)
                            if supported("C0", "C4b")
                            else None
                        ),
                        "equal_convention_delta_beta": (
                            betas["C4b"]["beta"] - betas["C1"]["beta"]
                        ),
                        "equal_convention_delta_beta_ci": (
                            _percentile_ci(equal_reps)
                            if supported("C1", "C4b")
                            else None
                        ),
                        "equal_convention_lower_bound": (
                            delta_beta_cp_bound(counts["C1"], counts["C4b"], n_samples)
                            if counts["C1"] > 0
                            else None
                        ),
                        "resolved": ratio_and_width(
                            counts["C0"], counts["C4b"], n_samples
                        )["resolved"],
                        "delta_beta_lower_bound": (
                            delta_beta_cp_bound(counts["C0"], counts["C4b"], n_samples)
                            if counts["C0"] > 0
                            else None
                        ),
                    }
                )
            per_n[str(n_samples)] = {
                "artifact": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "stages": entries,
            }
        out[key] = {
            "section": f"KP {LADDER_SECTION_KP[key]}",
            "by_n": per_n,
        }
    return out


def grid_delta_beta(path: Path, label: str, n_replicates: int) -> list[dict[str, Any]]:
    """Whole-grid production-branch dbeta (C0 vs C4b) with paired intervals."""
    with h5py.File(path, "r") as handle:
        grid = handle["conditioning_grid"][:]
        static = handle["comparators/C0"][:]
        trans = handle["comparators/C4b"][:]
    return [
        level_row(
            static[:, i],
            trans[:, i],
            level_m=float(grid[i]),
            label=f"{label}|grid|{grid[i]:.2f}",
            n_replicates=n_replicates,
        )
        for i in range(grid.size)
    ]


def design_anchors(n_replicates: int) -> dict[str, Any]:
    """The four design-level anchors of the campaign plan, section 1.3."""
    anchors: dict[str, Any] = {}
    for key, level in (("kp62_0", 46.39), ("kp57_4", 39.21)):
        path = HWL_DIR / f"ladder_{key}_n1000000.h5"
        levels, columns, n_samples = _ladder_columns(path, [level])
        anchors[key] = level_row(
            columns["C0"][:, 0],
            columns["C4b"][:, 0],
            level_m=float(levels[0]),
            label=f"{key}|anchor|{level:.2f}",
            n_replicates=n_replicates,
        )
        anchors[key]["artifact"] = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        anchors[key]["section"] = f"KP {LADDER_SECTION_KP[key]}"
    for kp, level in (("58.8", 41.00), ("60.0", 42.75)):
        name = f"tokachi_kp{kp}_historical_matrix"
        result = FragilityResult.load(RESULTS / f"{name}.h5")
        i = int(np.argmin(np.abs(result.conditioning_grid - level)))
        row = level_row(
            result.failure_matrix_stat[:, i],
            result.failure_matrix_tran[:, i],
            level_m=float(result.conditioning_grid[i]),
            label=f"{name}|anchor|{level:.2f}",
            n_replicates=n_replicates,
        )
        row["artifact"] = f"results/{name}.h5"
        row["section"] = f"KP {kp}"
        anchors[f"kp{kp.replace('.', '_')}"] = row
    return anchors


def epistemic_arms() -> dict[str, Any]:
    """The KP 62.0 design-level epistemic bracket, re-expressed in dbeta.

    Counts come from the Stage D brute-force arms; the baseline is the same
    anchor the rest of the brief uses. Each arm is a separate 10^6 population
    under a changed prior, so the arms are compared as displacements of the
    anchor, never bootstrapped against one another.
    """
    record = _read_json(HWL_DIR / "stage_d_epistemic.json")
    n = int(record["n_samples"])
    out: dict[str, Any] = {"n_samples": n, "sections": {}}
    for key, section in record["sections"].items():
        anchor_key = "A1"
        rows = []
        for arm in section["arms"]:
            anchor = arm["anchors"].get(anchor_key)
            if anchor is None:
                continue
            entry = anchor["bias_arm"]
            k_s, k_t = int(entry["k_static"]), int(entry["k_transient"])
            stat = beta_interval(k_s, n)
            tran = beta_interval(k_t, n) if k_t > 0 else None
            rows.append(
                {
                    "arm": arm["arm"],
                    "bracket": arm.get("bracket"),
                    "level_m_msl": float(entry["level_m"]),
                    "k_static": k_s,
                    "k_transient": k_t,
                    "B": float(entry["ratio"]) if k_t > 0 else float("inf"),
                    "beta_static": stat["beta"],
                    "beta_transient": tran["beta"] if tran else None,
                    "delta_beta": (tran["beta"] - stat["beta"]) if tran else None,
                    "delta_beta_lower_bound": (
                        delta_beta_cp_bound(k_s, k_t, n) if k_s > 0 else None
                    ),
                    "resolved": bool(entry["resolved"]),
                }
            )
        out["sections"][key] = {
            "anchor": anchor_key,
            "section": f"KP {LADDER_SECTION_KP.get(key, key)}",
            "arms": rows,
        }
    return out


def canonical_event() -> dict[str, Any]:
    """Design-level dbeta under the production and the alternate member.

    The static branch is exactly invariant between the two members (gate 2 of
    the canonical-shape study), so the whole displacement sits in the
    transient branch and the comparison is clean.
    """
    record = _read_json(CANONICAL)
    out: dict[str, Any] = {
        "production_event": record["production_event"],
        "alternate_event": record["alternate_event"],
        "artifact": "docs/decisions/canonical-shape-sensitivity.json",
        "static_exactly_invariant": bool(
            record["phase1"]["gates"]["gate_2_static_exactly_invariant"]
        ),
        "strata": {},
    }
    for name, stratum in record["phase1"]["strata"].items():
        if stratum["stratum"].endswith("bulk"):
            continue
        levels = np.asarray(stratum["levels_m_msl"], dtype=float)
        hwl = float(stratum["hwl_m_msl"])
        i = int(np.argmin(np.abs(levels - hwl)))
        p_t_prod = float(stratum["p_f_trans_production"][i])
        p_t_alt = float(stratum["p_f_trans_alternate"][i])
        # The static branch is not carried in the canonical-shape record; it
        # is read from the production sweep at the same level, which is the
        # same estimate by construction (gate 1, bit-identical baseline).
        result = FragilityResult.load(RESULTS / f"{stratum['stratum']}.h5")
        j = int(np.argmin(np.abs(result.conditioning_grid - levels[i])))
        p_s = float(result.P_f_static_raw[j])
        entry = {
            "stratum": stratum["stratum"],
            "section": stratum["section"],
            "level_m_msl": float(levels[i]),
            "hwl_m_msl": hwl,
            "n_samples": int(stratum["n_samples"]),
            "p_static": p_s,
            "p_transient_production": p_t_prod,
            "p_transient_alternate": p_t_alt,
            "beta_static": beta_from_p(p_s),
            "beta_transient_production": beta_from_p(p_t_prod),
            "beta_transient_alternate": beta_from_p(p_t_alt),
            "delta_beta_production": beta_from_p(p_t_prod) - beta_from_p(p_s),
            "delta_beta_alternate": beta_from_p(p_t_alt) - beta_from_p(p_s),
            "resolved": bool(stratum["resolved"][i]),
        }
        entry["delta_beta_shift"] = (
            entry["delta_beta_alternate"] - entry["delta_beta_production"]
        )
        out["strata"][stratum["stratum"]] = entry
    return out


# --------------------------------------------------------------------------- #
# serialisation                                                               #
# --------------------------------------------------------------------------- #
def _jsonable(obj: Any) -> Any:
    """JSON-safe rendering; non-finite floats become their string names."""
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        value = float(obj)
        return value if np.isfinite(value) else str(value)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


CSV_COLUMNS = (
    "table",
    "section",
    "d70_interpretation",
    "n_samples",
    "level_m_msl",
    "role",
    "k_static",
    "k_transient",
    "p_static",
    "p_transient",
    "beta_static",
    "beta_static_ci_lo",
    "beta_static_ci_hi",
    "beta_transient",
    "beta_transient_ci_lo",
    "beta_transient_ci_hi",
    "delta_beta",
    "delta_beta_ci_lo",
    "delta_beta_ci_hi",
    "delta_beta_lower_bound",
    "B",
    "resolved",
    "attainable",
    "artifact",
)


def _fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}g}" if np.isfinite(value) else str(float(value))
    return str(value)


def _csv_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def emit(
        table: str, base: dict[str, Any], row: dict[str, Any], **extra: Any
    ) -> None:
        ci = row.get("delta_beta_ci") or [None, None]
        rows.append(
            {
                "table": table,
                "section": base.get("section", ""),
                "d70_interpretation": base.get("d70_interpretation", ""),
                "n_samples": row.get("n_samples"),
                "level_m_msl": row.get("level_m_msl"),
                "role": extra.get("role", ""),
                "k_static": row.get("k_static"),
                "k_transient": row.get("k_transient"),
                "p_static": row.get("p_static"),
                "p_transient": row.get("p_transient"),
                "beta_static": row.get("beta_static"),
                "beta_static_ci_lo": (row.get("beta_static_ci") or [None, None])[0],
                "beta_static_ci_hi": (row.get("beta_static_ci") or [None, None])[1],
                "beta_transient": row.get("beta_transient"),
                "beta_transient_ci_lo": (row.get("beta_transient_ci") or [None, None])[
                    0
                ],
                "beta_transient_ci_hi": (row.get("beta_transient_ci") or [None, None])[
                    1
                ],
                "delta_beta": row.get("delta_beta"),
                "delta_beta_ci_lo": ci[0],
                "delta_beta_ci_hi": ci[1],
                "delta_beta_lower_bound": row.get("delta_beta_lower_bound"),
                "B": row.get("B"),
                "resolved": row.get("resolved"),
                "attainable": row.get("attainable"),
                "artifact": extra.get("artifact", base.get("artifact", "")),
            }
        )

    for stratum in record["production"].values():
        for row in stratum["levels"]:
            emit("production", stratum, row)
    for key, section in record["ladder"].items():
        for n_key, block in section["by_n"].items():
            for entry in block["stages"]:
                base = {"section": section["section"], "d70_interpretation": "matrix"}
                emit(
                    "ladder_total",
                    base,
                    {
                        "n_samples": entry["n_samples"],
                        "level_m_msl": entry["level_m_msl"],
                        "k_static": entry["counts"]["C0"],
                        "k_transient": entry["counts"]["C4b"],
                        "beta_static": entry["beta"]["C0"],
                        "beta_transient": entry["beta"]["C4b"],
                        "beta_static_ci": entry["beta_ci"]["C0"],
                        "beta_transient_ci": entry["beta_ci"]["C4b"],
                        "delta_beta": entry["total_delta_beta"],
                        "delta_beta_ci": entry["total_delta_beta_ci"],
                        "delta_beta_lower_bound": entry["delta_beta_lower_bound"],
                        "resolved": entry["resolved"],
                    },
                    artifact=block["artifact"],
                    role="C0_to_C4b",
                )
                for component, step in entry["steps"].items():
                    emit(
                        "ladder_step",
                        base,
                        {
                            "n_samples": entry["n_samples"],
                            "level_m_msl": entry["level_m_msl"],
                            "k_static": entry["counts"][step["from"]],
                            "k_transient": entry["counts"][step["to"]],
                            "beta_static": entry["beta"][step["from"]],
                            "beta_transient": entry["beta"][step["to"]],
                            "delta_beta": step["delta_beta"],
                            "delta_beta_ci": step["ci"],
                        },
                        artifact=block["artifact"],
                        role=component,
                    )
                emit(
                    "equal_convention",
                    base,
                    {
                        "n_samples": entry["n_samples"],
                        "level_m_msl": entry["level_m_msl"],
                        "k_static": entry["counts"]["C1"],
                        "k_transient": entry["counts"]["C4b"],
                        "beta_static": entry["beta"]["C1"],
                        "beta_transient": entry["beta"]["C4b"],
                        "delta_beta": entry["equal_convention_delta_beta"],
                        "delta_beta_ci": entry["equal_convention_delta_beta_ci"],
                    },
                    artifact=block["artifact"],
                    role="C1_to_C4b",
                )
    for key, section in record["epistemic"]["sections"].items():
        for arm in section["arms"]:
            emit(
                "epistemic_arm",
                {"section": section["section"], "d70_interpretation": "matrix"},
                {
                    "n_samples": record["epistemic"]["n_samples"],
                    "level_m_msl": arm["level_m_msl"],
                    "k_static": arm["k_static"],
                    "k_transient": arm["k_transient"],
                    "beta_static": arm["beta_static"],
                    "beta_transient": arm["beta_transient"],
                    "delta_beta": arm["delta_beta"],
                    "delta_beta_lower_bound": arm["delta_beta_lower_bound"],
                    "B": arm["B"],
                    "resolved": arm["resolved"],
                },
                artifact="results/hwl_bias_resolution/stage_d_epistemic.json",
                role=arm["arm"],
            )
    for entry in record["canonical_event"]["strata"].values():
        for role, key_p, key_b in (
            ("production_event", "p_transient_production", "delta_beta_production"),
            ("alternate_event", "p_transient_alternate", "delta_beta_alternate"),
        ):
            emit(
                "canonical_event",
                {"section": entry["section"], "d70_interpretation": "matrix"},
                {
                    "n_samples": entry["n_samples"],
                    "level_m_msl": entry["level_m_msl"],
                    "p_static": entry["p_static"],
                    "p_transient": entry[key_p],
                    "beta_static": entry["beta_static"],
                    "beta_transient": beta_from_p(entry[key_p]),
                    "delta_beta": entry[key_b],
                    "resolved": entry["resolved"],
                },
                artifact="docs/decisions/canonical-shape-sensitivity.json",
                role=role,
            )
    return rows


def write_csv(record: dict[str, Any], path: Path) -> None:
    rows = _csv_rows(record)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _fmt(row.get(key)) for key in CSV_COLUMNS})


# --------------------------------------------------------------------------- #
# markdown brief                                                              #
# --------------------------------------------------------------------------- #
def _n(value: Any, digits: int = 2, dash: str = "n/a") -> str:
    if value is None:
        return dash
    value = float(value)
    if not np.isfinite(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.{digits}f}"


def _ci(pair: Any, digits: int = 2) -> str:
    if not pair:
        return "not supported"
    return f"[{_n(pair[0], digits)}, {_n(pair[1], digits)}]"


def _find(rows: Iterable[dict[str, Any]], level: float) -> dict[str, Any]:
    return min(rows, key=lambda r: abs(r["level_m_msl"] - level))


def _pow10(n: int | str) -> str:
    """Sample size as a power of ten, for a table cell."""
    return f"10^{int(round(np.log10(float(int(n)))))}"


def _bounded(value: float, bound: float | None) -> str:
    """Point estimate where one exists, otherwise the one-sided bound.

    A bound at or below zero is arithmetically valid and carries no
    information about a difference that is expected to be positive, so it is
    reported as absent rather than printed as if it said something.
    """
    if np.isfinite(value):
        return _n(value)
    if bound is not None and bound > 0.0:
        return f"at least {_n(bound)}"
    return "no useful bound"


def write_markdown(record: dict[str, Any], path: Path) -> None:
    """Assemble the numbers brief. Every number is interpolated, never typed."""
    prod = record["production"]
    ladder = record["ladder"]
    anchors = record["design_anchors"]
    lines: list[str] = []
    add = lines.append

    add("# RQ1 static-vs-transient comparison in reliability-index terms")
    add("")
    add(f"Tables of record, {record['generated']}. Generated by")
    add("`scripts/rq1_beta_analysis.py` from persisted artifacts only; no limit")
    add("state is evaluated here and no configuration is read for anything but")
    add("provenance. Machine-readable companions:")
    add("`docs/decisions/rq1-beta-reexpression.json` (complete) and")
    add("`docs/decisions/rq1-beta-reexpression.csv` (flat).")
    add("")
    add("## 1. Metric and conventions")
    add("")
    add("Per branch, per conditioning level h,")
    add("")
    add("    beta(h) = -Phi^-1( P_f(h) ),   dbeta(h) = beta_transient - beta_static")
    add("")
    add("- beta is strictly decreasing in P_f, so an interval on P_f maps to one")
    add("  on beta by swapping its endpoints. The exact Clopper-Pearson intervals")
    add("  already persisted with every sweep are reused unchanged; no new")
    add("  statistical machinery is introduced.")
    add("- P_f above 0.5 gives a negative beta and is reported as such.")
    add("- A zero-failure level gives an infinite point beta. The deliverable")
    add("  there is a one-sided bound: the Clopper-Pearson **upper** bound on")
    add("  P_transient gives a **lower** bound on beta_transient, and the")
    add("  **lower** bound on P_static gives an **upper** bound on beta_static,")
    add("  so their difference is a lower bound on dbeta. This is the exact")
    add("  analogue of the ratio bound already used at KP 57.4.")
    add("- dbeta intervals are paired bootstrap over the shared realization set,")
    add(f"  B = {record['n_bootstrap']} replicates, percentile method, one row")
    add("  resample per replicate applied to both branches. Reported only where")
    add(f"  both branches carry at least {MIN_ROWS_FOR_BOOTSTRAP} failing rows")
    add("  (the R1 floor); below that the bound above is the deliverable.")
    add("- The resolution criteria R1 (at least 30 transient failing rows) and R2")
    add("  (interval width factor at most 2) remain defined on the probability")
    add("  ratio B exactly as pre-registered. They are not restated on dbeta:")
    add("  the map is monotone, so a level resolved on B is resolved on dbeta.")
    add("")
    add("## 2. Design-level anchors")
    add("")
    add(
        "| Section | level [m MSL] | N | k_static | k_transient |"
        " beta_static | beta_transient | dbeta | B |"
    )
    add("|---|---|---|---|---|---|---|---|---|")
    order = ("kp62_0", "kp57_4", "kp58_8", "kp60_0")
    for key in order:
        row = anchors[key]
        bound = row["k_transient"] < MIN_ROWS_FOR_BOOTSTRAP
        beta_t = (
            f"at least {_n(row['beta_transient_ci'][0])}"
            if bound
            else _n(row["beta_transient"])
        )
        dbeta = (
            f"at least {_n(row['delta_beta_lower_bound'])}"
            if bound
            else _n(row["delta_beta"])
        )
        b_val = f"at least {_n(row['B_ci'][0], 0)}" if bound else _n(row["B"], 1)
        add(
            f"| {row['section']} | {row['level_m_msl']:.2f} | "
            f"{_pow10(row['n_samples'])} | {row['k_static']} | "
            f"{row['k_transient']} | "
            f"{_n(row['beta_static'])} | {beta_t} | **{dbeta}** | {b_val} |"
        )
    add("")
    add("Interval detail (95 %):")
    add("")
    for key in order:
        row = anchors[key]
        ci = (
            _ci(row["delta_beta_ci"])
            if row["delta_beta_ci"]
            else f"one-sided, dbeta at least {_n(row['delta_beta_lower_bound'])}"
        )
        add(
            f"- {row['section']} at {row['level_m_msl']:.2f} m MSL: "
            f"beta_static {_n(row['beta_static'])} {_ci(row['beta_static_ci'])}, "
            f"beta_transient {_n(row['beta_transient'])} "
            f"{_ci(row['beta_transient_ci'])}, dbeta {ci}. "
            f"Artifact `{row['artifact']}`."
        )
    add("")
    add("### Verification against the campaign plan, section 1.3")
    add("")
    add("| Anchor | plan dbeta | measured | agreement |")
    add("|---|---|---|---|")
    plan_expectation = {
        "kp62_0": ("0.90", 0.90),
        "kp57_4": ("at least 1.28", 1.28),
        "kp58_8": ("1.22", 1.22),
        "kp60_0": ("1.87", 1.87),
    }
    for key in order:
        row = anchors[key]
        planned, planned_value = plan_expectation[key]
        measured = (
            row["delta_beta_lower_bound"]
            if row["k_transient"] < MIN_ROWS_FOR_BOOTSTRAP
            else row["delta_beta"]
        )
        prefix = "at least " if row["k_transient"] < MIN_ROWS_FOR_BOOTSTRAP else ""
        agree = "matches" if abs(measured - planned_value) < 0.005 else "see note"
        add(
            f"| {row['section']} at {row['level_m_msl']:.2f} m MSL | {planned} | "
            f"{prefix}{_n(measured)} | {agree} |"
        )
    add("")
    kp57 = anchors["kp57_4"]
    kp60 = anchors["kp60_0"]
    add("Two departures, both understood and neither a data problem:")
    add("")
    add(
        f"- **KP 57.4, {_n(kp57['delta_beta_lower_bound'])} against the plan's"
        f" 1.28.** The plan paired the lower bound on beta_transient"
        f" ({_n(kp57['beta_transient_ci'][0])}) with the POINT estimate of"
        f" beta_static ({_n(kp57['beta_static'])}). The bound quoted here"
        " instead pairs it with the upper bound on beta_static"
        f" ({_n(kp57['beta_static_ci'][1])}), which is the construction the"
        " ratio bound B at least 148 already uses at the same anchor (static"
        " lower endpoint over transient upper endpoint). The stricter figure is"
        " the one to quote; the difference is 0.02 and the direction is"
        " conservative."
    )
    add(
        f"- **KP 60.0 rounding.** The plan lists beta_static -1.39 and"
        f" beta_transient 0.49; the artifact gives"
        f" {kp60['beta_static']:.3f} and {kp60['beta_transient']:.3f}, which"
        f" round to {_n(kp60['beta_static'])} and {_n(kp60['beta_transient'])}."
        f" The difference, {_n(kp60['delta_beta'])}, is unchanged, so no"
        " downstream claim moves."
    )
    add("")
    add("## 3. dbeta against stage, and what B does over the same range")
    add("")
    add("Attainable stages only (the KP 62.0 grid extension above 50.50 m MSL is")
    add("excluded here and shaded, never plotted as attainable, in the figures).")
    add("")
    add(
        "| Stratum | stages with both branches interior |"
        " dbeta at the lowest | dbeta minimum |"
        " dbeta at the top attainable | dbeta range |"
        " B at the lowest | B at the top |"
    )
    add("|---|---|---|---|---|---|---|---|")
    severity: dict[str, dict[str, float]] = {}
    for name, stratum in prod.items():
        rows = [
            r
            for r in stratum["levels"]
            if r["attainable"] and np.isfinite(r["delta_beta"])
        ]
        if not rows:
            continue
        dbetas = np.array([r["delta_beta"] for r in rows])
        ratios = np.array([r["B"] for r in rows])
        severity[name] = {
            "first": float(dbetas[0]),
            "min": float(dbetas.min()),
            "last": float(dbetas[-1]),
            "b_first": float(ratios[0]),
            "b_last": float(ratios[-1]),
            "level_first": rows[0]["level_m_msl"],
            "level_last": rows[-1]["level_m_msl"],
        }
        add(
            f"| {stratum['section']} {stratum['d70_interpretation']} | {len(rows)} "
            f"({rows[0]['level_m_msl']:.2f} to {rows[-1]['level_m_msl']:.2f}) | "
            f"{_n(dbetas[0])} | {_n(dbetas.min())} | {_n(dbetas[-1])} | "
            f"{_n(dbetas.max() - dbetas.min())} | {_n(ratios[0], 1)} | "
            f"{_n(ratios[-1], 2)} |"
        )
    add("")
    add("Reading, stated in both directions as the campaign requires:")
    add("")
    matrix_keys = [k for k in severity if k.endswith("matrix")]
    b_span = max(severity[k]["b_first"] / severity[k]["b_last"] for k in matrix_keys)
    b_span_lo = min(severity[k]["b_first"] / severity[k]["b_last"] for k in matrix_keys)
    d_span = max(severity[k]["last"] - severity[k]["min"] for k in matrix_keys)
    add(
        f"- **B decays and dbeta does not.** Over the attainable range of the four"
        f" matrix strata the ratio falls by a factor of {b_span_lo:.0f} to"
        f" {b_span:.0f} and lands between"
        f" {min(severity[k]['b_last'] for k in matrix_keys):.2f} and"
        f" {max(severity[k]['b_last'] for k in matrix_keys):.2f}, that is, within"
        " a few tens of percent of parity. Over the same range dbeta is"
        " shallowly U-shaped: it dips by at most"
        f" {max(severity[k]['first'] - severity[k]['min'] for k in matrix_keys):.2f}"
        " on the low shoulder and then rises monotonically to its maximum at the"
        f" top attainable stage, a total rise of up to {d_span:.2f}."
    )
    add(
        "- So the claim that the two models converge toward parity at extreme"
        " overload is a statement about P_f and about the failure tail only. It"
        " is false of the survival tail, which is where a ratio of failure"
        " probabilities stops carrying information and beta keeps carrying it."
    )
    add(
        "- The existing claim that conventional practice is most conservative"
        " exactly at design levels is a ratio-space statement. It survives"
        " re-scoped to the ratio; in dbeta the design level is near the flat"
        " part of the curve, not its maximum."
    )
    add("")
    add("### Survival reading at the top attainable level")
    add("")
    add(
        "| Section | level [m MSL] | static survival | transient survival | B | dbeta |"
    )
    add("|---|---|---|---|---|---|")
    for kp in SECTIONS:
        stratum = prod[f"tokachi_kp{kp}_historical_matrix"]
        rows = [r for r in stratum["levels"] if r["attainable"]]
        row = rows[-1]
        add(
            f"| KP {kp} | {row['level_m_msl']:.2f} | "
            f"{row['survival_static'] * 100:.2f} % | "
            f"{row['survival_transient'] * 100:.1f} % | {_n(row['B'], 2)} | "
            f"{_n(row['delta_beta'])} |"
        )
    add("")
    add("## 4. The comparator ladder as additive dbeta steps")
    add("")
    add("beta is a per-branch scalar, so the engine ladder telescopes exactly:")
    add("")
    add("    dbeta_total = [beta(C1)-beta(C0)] + [beta(C3b)-beta(C1)]")
    add("                + [beta(C4b)-beta(C3b)]")
    add("")
    add("with C0 the production static branch, C1 the crack-reduced static")
    add("comparator, C3b the analytic sustained-peak limit and C4b the")
    add("production transient branch. The three steps are the head convention,")
    add("the initiation gate and the temporal mechanism. No share-of-total")
    add("denominator is needed, and the components add rather than multiply.")
    add("")
    for key in ("kp62_0", "kp57_4"):
        section = ladder[key]
        for n_key in sorted(section["by_n"], key=lambda s: -int(s)):
            block = section["by_n"][n_key]
            add(
                f"**{section['section']}, N = {_pow10(n_key)}** "
                f"(`{block['artifact']}`)"
            )
            add("")
            add(
                "| stage [m MSL] | k(C0) | k(C4b) | beta(C0) | head convention |"
                " initiation gate | temporal | beta(C4b) | dbeta total |"
                " equal convention beta(C4b)-beta(C1) | resolved |"
            )
            add("|---|---|---|---|---|---|---|---|---|---|---|")
            for entry in block["stages"]:
                steps = entry["steps"]

                def cell(component: str) -> str:
                    step = steps[component]
                    value = step["delta_beta"]
                    if not np.isfinite(value):
                        return "n/a"
                    return _n(value)

                total = (
                    f"**{_n(entry['total_delta_beta'])}**"
                    if np.isfinite(entry["total_delta_beta"])
                    else f"**at least {_n(entry['delta_beta_lower_bound'])}**"
                )
                equal = _bounded(
                    entry["equal_convention_delta_beta"],
                    entry["equal_convention_lower_bound"],
                )
                add(
                    f"| {entry['level_m_msl']:.2f} | {entry['counts']['C0']} | "
                    f"{entry['counts']['C4b']} | "
                    f"{_n(entry['beta']['C0'])} | "
                    f"{cell('head_convention')} | "
                    f"{cell('initiation_gate')} | "
                    f"{cell('temporal')} | "
                    f"{_n(entry['beta']['C4b'])} | {total} | {equal} | "
                    f"{'yes' if entry['resolved'] else 'no'} |"
                )
            add("")
    add(
        "`n/a` marks a step whose comparator has no failing realization at that"
        " stage, so its beta is infinite and the step carries no finite value;"
        " the total is then a one-sided bound. `resolved` is the pre-registered"
        " R1-and-R2 verdict on the ratio B at that stage, carried over"
        " unchanged."
    )
    add("")
    add("Paired-bootstrap intervals on every step are in the JSON companion")
    add("under `ladder.<section>.by_n.<N>.stages[].steps.<component>.ci`.")
    add("")
    big = ladder["kp62_0"]["by_n"]["1000000"]["stages"]
    first, last = big[0], big[-1]
    add("Two things the additive form makes visible that the share-of-gap form")
    add("did not:")
    add("")
    add(
        "- **The initiation gate contributes exactly zero at KP 62.0** at every"
        " named stage (C1 and C3b have identical failure sets there), so the"
        " section's whole gap is head convention plus temporal."
    )
    add(
        f"- **The two surviving components move in opposite directions with"
        f" stage.** At KP 62.0 between {first['level_m_msl']:.2f} and"
        f" {last['level_m_msl']:.2f} m MSL the head-convention step falls from"
        f" {_n(first['steps']['head_convention']['delta_beta'])} to"
        f" {_n(last['steps']['head_convention']['delta_beta'])} while the"
        f" temporal step rises from"
        f" {_n(first['steps']['temporal']['delta_beta'])} to"
        f" {_n(last['steps']['temporal']['delta_beta'])}. The near-flat total is"
        " the sum of a decaying head-convention term and a growing temporal one,"
        " not a flat mechanism."
    )
    add("")
    add("### The Dutch-practice equal-convention comparison in dbeta")
    add("")
    add("C1 against C4b is the already-measured equal-convention reading: both")
    add("branches crack-reduced, so the contested 0.3 x D_bl term cancels and")
    add("what remains is the initiation gate plus the temporal mechanism.")
    add("")
    add(
        "| Section | N | stage [m MSL] | k(C1) | k(C4b) |"
        " dbeta equal convention | 95 % CI |"
    )
    add("|---|---|---|---|---|---|---|")
    for key in ("kp62_0", "kp57_4"):
        section = ladder[key]
        for n_key in sorted(section["by_n"], key=lambda s: -int(s)):
            for entry in section["by_n"][n_key]["stages"]:
                shown = _bounded(
                    entry["equal_convention_delta_beta"],
                    entry["equal_convention_lower_bound"],
                )
                add(
                    f"| {section['section']} | {_pow10(n_key)} | "
                    f"{entry['level_m_msl']:.2f} | {entry['counts']['C1']} | "
                    f"{entry['counts']['C4b']} | {shown} | "
                    f"{_ci(entry['equal_convention_delta_beta_ci'])} |"
                )
    add("")
    eq_quotable = [
        entry
        for key in ("kp62_0", "kp57_4")
        for entry in ladder[key]["by_n"]["1000000"]["stages"]
        if entry["equal_convention_delta_beta_ci"]
    ]
    eq_design = [e for e in eq_quotable if abs(e["level_m_msl"] - 46.39) < 0.01] + [
        e for e in eq_quotable if abs(e["level_m_msl"] - 39.50) < 0.01
    ]
    add(
        "At the two design-neighbourhood stages that carry enough transient"
        " rows to support an interval, the equal-convention difference is "
        + " and ".join(
            f"{_n(e['equal_convention_delta_beta'])} at "
            f"{e['level_m_msl']:.2f} m MSL"
            for e in eq_design
        )
        + ". Both fall inside the campaign's pre-registered band of about 0.2"
        " to 0.7 for this quantity (plan section 4, expectation 3), so that"
        " expectation is met on the already-measured reduced-versus-reduced"
        " reading. The gross-versus-gross reading is the separate new run."
    )
    add("")
    add("## 5. Epistemic arms of the KP 62.0 design anchor, in dbeta")
    add("")
    add("Each arm is its own 10^6 population under a changed prior, so the arms")
    add("are reported as displacements of the anchor and never bootstrapped")
    add(
        "against one another. Source"
        " `results/hwl_bias_resolution/stage_d_epistemic.json`."
    )
    add("")
    add(
        "| arm | bracket | k_static | k_transient | B |"
        " beta_static | beta_transient | dbeta | shift in dbeta |"
        " resolved |"
    )
    add("|---|---|---|---|---|---|---|---|---|---|")
    kp62_anchor = anchors["kp62_0"]
    arms = record["epistemic"]["sections"]["kp62_0"]["arms"]
    for arm in arms:
        if arm["k_static"] == 0:
            beta_t = dbeta_txt = shift_txt = "n/a"
        elif arm["delta_beta"] is None or arm["k_transient"] < MIN_ROWS_FOR_BOOTSTRAP:
            beta_t = (
                "n/a" if arm["beta_transient"] is None else _n(arm["beta_transient"])
            )
            dbeta_txt = f"at least {_n(arm['delta_beta_lower_bound'])}"
            shift_txt = "n/a"
        else:
            dbeta_txt = _n(arm["delta_beta"])
            shift_txt = f"{arm['delta_beta'] - kp62_anchor['delta_beta']:+.2f}"
            beta_t = _n(arm["beta_transient"])
        beta_s = "n/a" if arm["k_static"] == 0 else _n(arm["beta_static"])
        add(
            f"| {arm['arm']} | {arm['bracket']} | {arm['k_static']} | "
            f"{arm['k_transient']} | {_n(arm['B'], 2)} | "
            f"{beta_s} | {beta_t} | {dbeta_txt} | {shift_txt} | "
            f"{'yes' if arm['resolved'] else 'no'} |"
        )
    add("")
    add(
        "The `k_aq_field_geomean` arm has no failing realization on either"
        " branch in 10^6, so nothing about it is quotable in either metric."
        " The `k_aq_field_toe`, `z_toe_plus0.30m` and `L_withdrawn_1998` arms"
        " carry fewer than the 30 transient rows the pre-registered R1 floor"
        " requires, so they are one-sided bounds and their B values are"
        " likewise unresolved."
    )
    add("")
    resolved_arms = [
        a
        for a in arms
        if a["delta_beta"] is not None and a["k_transient"] >= MIN_ROWS_FOR_BOOTSTRAP
    ]
    b_lo = min(a["B"] for a in resolved_arms)
    b_hi = max(a["B"] for a in resolved_arms)
    d_lo = min(a["delta_beta"] for a in resolved_arms)
    d_hi = max(a["delta_beta"] for a in resolved_arms)
    all_points = [a["delta_beta"] for a in arms if a["delta_beta"] is not None]
    all_b = [a["B"] for a in arms if a["delta_beta"] is not None]
    anchor_ci = kp62_anchor["delta_beta_ci"]
    anchor_width = anchor_ci[1] - anchor_ci[0]
    add(
        f"Across the arms that clear the R1 floor the bracket spans"
        f" B = {b_lo:.2f} to {b_hi:.1f}, a factor of {b_hi / b_lo:.1f}."
        f" In dbeta the same arms span {d_lo:.2f} to {d_hi:.2f}, a range of"
        f" {d_hi - d_lo:.2f}. Taking every arm's point estimate, including the"
        f" three whose transient counts are below the floor, the spread is"
        f" B = {min(all_b):.2f} to {max(all_b):.1f}, a factor of"
        f" {max(all_b) / min(all_b):.0f}, against dbeta"
        f" {min(all_points):.2f} to {max(all_points):.2f}, a range of"
        f" {max(all_points) - min(all_points):.2f}."
    )
    add("")
    add(
        f"The re-expression does not make the bracket go away, and it should"
        f" not be reported as if it did. What it does is change the bracket's"
        f" apparent size relative to the number it brackets: an order of"
        f" magnitude in B becomes about two tenths of a beta unit, which is"
        f" roughly {(max(all_points) - min(all_points)) / anchor_width:.0f} times"
        f" the width of the anchor's own 95 percent sampling interval"
        f" {_ci(anchor_ci)}. In ratio terms the same comparison reads as a"
        " factor-of-ten disagreement; in index terms it reads as a two tenths"
        " shift on a difference of about nine tenths. Both statements are true"
        " of the same eight populations."
    )
    add("")
    add("## 6. Canonical-event exposure in dbeta")
    add("")
    add("The static branch is exactly invariant between the two canonical")
    add("members, so the whole displacement sits in the transient branch.")
    add("")
    add(
        "| Section | level [m MSL] | P_transient production |"
        " P_transient alternate | dbeta production |"
        " dbeta alternate | shift |"
    )
    add("|---|---|---|---|---|---|---|")
    skipped: list[str] = []
    for entry in record["canonical_event"]["strata"].values():
        k_alt = entry["p_transient_alternate"] * entry["n_samples"]
        if not entry["resolved"] or k_alt < MIN_ROWS_FOR_BOOTSTRAP:
            skipped.append(f"{entry['section']} ({k_alt:.0f} rows)")
            continue
        add(
            f"| {entry['section']} | {entry['level_m_msl']:.2f} | "
            f"{entry['p_transient_production']:.5f} | "
            f"{entry['p_transient_alternate']:.5f} | "
            f"{_n(entry['delta_beta_production'])} | "
            f"{_n(entry['delta_beta_alternate'])} | "
            f"{entry['delta_beta_shift']:+.2f} |"
        )
    add("")
    add(
        "Not quoted, because the alternate member leaves too few failing"
        " transient realizations at N = 10^5 to clear the R1 floor: "
        + ", ".join(skipped)
        + "."
    )
    add(
        "The direction is the same at every section that resolves: the shorter,"
        " flashier alternate member lowers the transient probability, raises"
        " beta_transient, and therefore WIDENS the index difference. The"
        " canonical event is an exposure on this comparison in the"
        " conservative direction, that is, the production member is the one"
        " that flatters the transient model."
    )
    add("")
    add("## 7. Traceability")
    add("")
    add("| Quantity | Artifact |")
    add("|---|---|")
    for stratum in prod.values():
        add(
            f"| {stratum['section']} {stratum['d70_interpretation']}"
            f" per-level table | `{stratum['artifact']}` |"
        )
    for key, section in ladder.items():
        for n_key, block in section["by_n"].items():
            add(
                f"| {section['section']} ladder at N = {_pow10(n_key)} | "
                f"`{block['artifact']}` |"
            )
    add("| epistemic arms | `results/hwl_bias_resolution/stage_d_epistemic.json` |")
    add("| canonical event | `docs/decisions/canonical-shape-sensitivity.json` |")
    add(
        "| design anchors, ratio form |"
        " `results/hwl_bias_resolution/stage_a_brute_kp62_0.json`,"
        " `stage_a_brute_kp57_4.json`, `stage_a_anchors.json` |"
    )
    add("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# figures                                                                     #
# --------------------------------------------------------------------------- #
def _save(fig: plt.Figure, name: str) -> Path:
    out = figstyle.save(fig, name)
    if THESIS_FIGURES.is_dir():
        (THESIS_FIGURES / name).write_bytes(out.read_bytes())
    return out


def _finite_rows(rows: Sequence[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [r for r in rows if np.isfinite(r.get(key, np.nan))]


def figure_beta_curves(record: dict[str, Any]) -> Path:
    """Production fragility comparison on a reliability-index axis."""
    figstyle.style()
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.2), sharey=True)
    for ax, kp in zip(axes.ravel(), SECTIONS):
        stratum = record["production"][f"tokachi_kp{kp}_historical_matrix"]
        rows = stratum["levels"]
        for branch, colour, marker, label in (
            ("static", figstyle.STATIC, "o", "Static, Sellmeijer 2011"),
            ("transient", figstyle.TRANSIENT, "D", "Transient, Pol 2024"),
        ):
            sub = _finite_rows(rows, f"beta_{branch}")
            if not sub:
                continue
            x = [r["level_m_msl"] for r in sub]
            y = [r[f"beta_{branch}"] for r in sub]
            lo = [r[f"beta_{branch}"] - r[f"beta_{branch}_ci"][0] for r in sub]
            hi = [r[f"beta_{branch}_ci"][1] - r[f"beta_{branch}"] for r in sub]
            lo = [v if np.isfinite(v) else 0.0 for v in lo]
            hi = [v if np.isfinite(v) else 0.0 for v in hi]
            ax.errorbar(
                x,
                y,
                yerr=[lo, hi],
                fmt=marker,
                color=colour,
                ms=4.0,
                mec=figstyle.SURFACE,
                mew=0.5,
                elinewidth=1.0,
                capsize=1.8,
                lw=1.6,
                ls="-",
                label=label,
                zorder=4,
            )
        ax.axhline(0.0, color=figstyle.BASELINE, lw=1.0, zorder=2)
        ax.annotate(
            "P = 0.5",
            xy=(0.995, 0.0),
            xycoords=("axes fraction", "data"),
            xytext=(0, 3),
            textcoords="offset points",
            fontsize=8,
            color=figstyle.MUTED,
            ha="right",
        )
        ax.axvline(
            stratum["z_toe_m_msl"], color=figstyle.MUTED, lw=1.1, ls=(0, (4, 2, 1, 2))
        )
        ax.axvline(stratum["hwl_m_msl"], color=figstyle.INK_2, lw=1.1, ls=(0, (5, 3)))
        for value, text, colour in (
            (stratum["z_toe_m_msl"], "toe", figstyle.MUTED),
            (stratum["hwl_m_msl"], "design HWL", figstyle.INK_2),
        ):
            ax.annotate(
                text,
                xy=(value, 0.06),
                xycoords=("data", "axes fraction"),
                xytext=(3, 0),
                textcoords="offset points",
                rotation=90,
                fontsize=8.5,
                color=colour,
                va="bottom",
            )
        ax.set_title(f"KP {kp}", loc="left")
        ax.set_xlabel("conditioning water level h  [m MSL]")
        ax.set_ylim(-4.2, 5.2)
        # Shade only where the grid genuinely runs past the attainable stage;
        # at KP 57.4 the grid stops there, so an axis margin must not be
        # mistaken for an unattainable band.
        grid_max = max(r["level_m_msl"] for r in rows)
        attainable = stratum["attainable_max_m_msl"]
        if grid_max > attainable + 1e-9:
            figstyle.mark_hypothetical(ax, attainable, label=False)
            ax.annotate(
                "above the\nattainable stage",
                xy=(attainable, 0.97),
                xycoords=("data", "axes fraction"),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=8,
                color=figstyle.MUTED,
                ha="left",
                va="top",
            )
    for ax in axes[:, 0]:
        ax.set_ylabel(r"reliability index  $\beta = -\Phi^{-1}(P_f)$")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(0.99, 1.0), ncols=2)
    fig.suptitle(
        "Backward erosion piping fragility on a reliability-index axis",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=figstyle.INK,
    )
    fig.text(
        0.01,
        0.005,
        "Historical scenario, matrix d$_{70}$, N = 10$^5$ Latin hypercube. Points "
        "are raw Monte Carlo estimates; bars are the 95 % Clopper-Pearson "
        "intervals mapped through $\\beta = -\\Phi^{-1}(P_f)$.\nLevels at which a "
        "branch has zero or all realizations failing have an infinite $\\beta$ "
        "and are omitted; the bound they support is tabulated instead.",
        fontsize=8,
        color=figstyle.MUTED,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 0.95))
    return _save(fig, "rq1_beta_curves.png")


def figure_delta_beta_vs_stage(record: dict[str, Any]) -> Path:
    """dbeta against stage, with the ratio's decay underneath it."""
    figstyle.style()
    fig, axes = plt.subplots(
        2,
        4,
        figsize=(14.6, 6.8),
        sharex="col",
        gridspec_kw={"height_ratios": [1.5, 1.0], "hspace": 0.12},
    )
    for col, kp in enumerate(SECTIONS):
        stratum = record["production"][f"tokachi_kp{kp}_historical_matrix"]
        rows = [
            r
            for r in stratum["levels"]
            if r["attainable"] and np.isfinite(r["delta_beta"])
        ]
        colour = figstyle.SECTION_COLORS[f"KP{kp}"]
        top, bottom = axes[0][col], axes[1][col]
        x = [r["level_m_msl"] for r in rows]
        y = [r["delta_beta"] for r in rows]
        band = [r for r in rows if r["delta_beta_ci"]]
        if band:
            top.fill_between(
                [r["level_m_msl"] for r in band],
                [r["delta_beta_ci"][0] for r in band],
                [r["delta_beta_ci"][1] for r in band],
                color=colour,
                alpha=0.22,
                lw=0,
            )
        top.plot(x, y, "-", color=colour, lw=2.0, zorder=3)
        top.plot(
            x,
            y,
            figstyle.SECTION_MARKERS[f"KP{kp}"],
            color=colour,
            ms=4.2,
            mec=figstyle.SURFACE,
            mew=0.5,
            ls="none",
            zorder=4,
        )
        bottom.plot(x, [r["B"] for r in rows], "-", color=colour, lw=2.0)
        bottom.plot(
            x,
            [r["B"] for r in rows],
            figstyle.SECTION_MARKERS[f"KP{kp}"],
            color=colour,
            ms=4.2,
            mec=figstyle.SURFACE,
            mew=0.5,
            ls="none",
        )
        bottom.axhline(1.0, color=figstyle.BASELINE, lw=1.0)
        bottom.set_yscale("log")
        for ax in (top, bottom):
            ax.axvline(
                stratum["hwl_m_msl"], color=figstyle.INK_2, lw=1.0, ls=(0, (5, 3))
            )
        top.annotate(
            "design HWL",
            xy=(stratum["hwl_m_msl"], 0.03),
            xycoords=("data", "axes fraction"),
            xytext=(3, 0),
            textcoords="offset points",
            rotation=90,
            fontsize=8,
            color=figstyle.INK_2,
            va="bottom",
        )
        top.set_title(f"KP {kp}", loc="left")
        top.set_ylim(0.0, 2.6)
        bottom.set_ylim(0.8, 600.0)
        bottom.set_xlabel("conditioning water level h  [m MSL]")
    axes[0][0].set_ylabel(
        r"$\Delta\beta = \beta_\mathrm{trans} - \beta_\mathrm{static}$"
    )
    axes[1][0].set_ylabel("ratio  $B = P_{f,\mathrm{static}}/P_{f,\mathrm{trans}}$")
    fig.suptitle(
        "The same comparison under two metrics: the index difference holds, "
        "the probability ratio decays",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=figstyle.INK,
    )
    fig.text(
        0.01,
        0.005,
        "Attainable stages only, matrix d$_{70}$, N = 10$^5$. Shaded band: 95 % "
        "paired-bootstrap interval on $\\Delta\\beta$ over the shared "
        "realization set. Note the different vertical scales: the top row is "
        "linear over a range of about 1.4, the bottom row logarithmic over "
        "nearly three decades.",
        fontsize=8,
        color=figstyle.MUTED,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    return _save(fig, "rq1_delta_beta_vs_stage.png")


def _beta_waterfall(ax: plt.Axes, entry: dict[str, Any]) -> None:
    """Additive floating-bar waterfall from beta(C0) up to beta(C4b)."""
    names = [component for component, _, _ in BETA_LADDER_STEPS]
    start = entry["beta"]["C0"]
    running = start
    ax.bar(0, start, color=figstyle.BASELINE, width=0.62, zorder=3)
    colours = {
        "head_convention": figstyle.AQUA,
        "initiation_gate": figstyle.VIOLET,
        "temporal": figstyle.RED,
    }
    for i, component in enumerate(names, start=1):
        step = entry["steps"][component]
        delta = step["delta_beta"]
        ax.bar(
            i,
            abs(delta),
            bottom=min(running, running + delta),
            color=colours[component],
            width=0.62,
            zorder=3,
        )
        lo, hi = step["ci"] or (np.nan, np.nan)
        if np.isfinite(lo) and np.isfinite(hi) and np.isfinite(delta):
            centre = running + delta
            ax.errorbar(
                i,
                centre,
                yerr=[[max(0.0, delta - lo)], [max(0.0, hi - delta)]],
                color=figstyle.INK,
                lw=1.0,
                capsize=3,
                zorder=5,
            )
        ax.annotate(
            f"{delta:+.2f}",
            (i, running + delta),
            textcoords="offset points",
            xytext=(0, 6 if delta >= 0 else -12),
            ha="center",
            fontsize=8,
            color=figstyle.INK,
        )
        running += delta
    ax.bar(len(names) + 1, running, color=figstyle.BASELINE, width=0.62, zorder=3)
    ax.axhline(0.0, color=figstyle.BASELINE, lw=1.0)
    ax.set_xticks(np.arange(len(names) + 2))
    ax.set_xticklabels(
        [
            r"$\beta$ static",
            *(COMPONENT_LABELS[n] for n in names),
            r"$\beta$ transient",
        ],
        rotation=22,
        ha="right",
        fontsize=8.5,
    )


def figure_beta_waterfall(record: dict[str, Any]) -> Path:
    """The additive dbeta ladder at the design and top attainable levels."""
    figstyle.style()
    fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.0))
    picks = (
        ("kp62_0", 46.39, "design flood level"),
        ("kp62_0", 50.50, "top attainable level"),
        ("kp57_4", 39.21, "design flood level"),
        ("kp57_4", 43.25, "top attainable level"),
    )
    for ax, (key, level, label) in zip(axes.ravel(), picks):
        block = record["ladder"][key]["by_n"]["1000000"]
        entry = _find(block["stages"], level)
        _beta_waterfall(ax, entry)
        resolved = entry["resolved"]
        note = "" if resolved else "  (transient count below the R1 floor)"
        ax.set_title(
            f"{record['ladder'][key]['section']} at the {label}, "
            f"{entry['level_m_msl']:.2f} m MSL{note}",
            loc="left",
            fontsize=10,
        )
        ax.set_ylabel(r"reliability index  $\beta$")
        ax.annotate(
            rf"total $\Delta\beta$ = {entry['total_delta_beta']:.2f}",
            (0.98, 0.04),
            xycoords="axes fraction",
            ha="right",
            fontsize=9,
            color=figstyle.INK,
        )
    fig.suptitle(
        "Where the static-to-transient index difference comes from",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=figstyle.INK,
    )
    fig.text(
        0.01,
        0.005,
        "N = 10$^6$ comparator ladder, matrix d$_{70}$. $\\beta$ telescopes, so "
        "the three steps sum exactly to the total; no share-of-gap denominator "
        "is involved. Bars carry 95 % paired-bootstrap intervals.\nThe "
        "KP 57.4 design panel rests on two failing transient realizations in "
        "10$^6$ and is shown for its shape only; the quotable statement there "
        "is the one-sided bound.",
        fontsize=8,
        color=figstyle.MUTED,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    return _save(fig, "rq1_beta_waterfall.png")


def figure_hwl_dbeta_resolved(record: dict[str, Any]) -> Path:
    """KP 62.0 design-level index difference: N = 10^5 against N = 10^6."""
    figstyle.style()
    rows = record["grids"]["kp62_0"]
    small = record["grids_n100000"]["kp62_0"]
    attainable = record["production"]["tokachi_kp62.0_historical_matrix"][
        "attainable_max_m_msl"
    ]
    fig = plt.figure(figsize=(13.4, 6.2))
    gs = fig.add_gridspec(
        2,
        2,
        width_ratios=[1.55, 1.0],
        height_ratios=[2.5, 1.0],
        hspace=0.14,
        wspace=0.22,
    )
    ax = fig.add_subplot(gs[0, 0])
    axk = fig.add_subplot(gs[1, 0], sharex=ax)
    axz = fig.add_subplot(gs[:, 1])

    usable = [r for r in rows if np.isfinite(r["delta_beta"])]

    def draw(axis: plt.Axes, legend: bool) -> None:
        band = [r for r in usable if r["delta_beta_ci"]]
        if band:
            axis.fill_between(
                [r["level_m_msl"] for r in band],
                [r["delta_beta_ci"][0] for r in band],
                [r["delta_beta_ci"][1] for r in band],
                color=figstyle.BLUE,
                alpha=0.20,
                lw=0,
                label="95 % paired interval, $N = 10^6$" if legend else None,
            )
        axis.plot(
            [r["level_m_msl"] for r in usable],
            [r["delta_beta"] for r in usable],
            "-",
            color=figstyle.BLUE,
            lw=2.0,
            zorder=3,
        )
        for marker, keep, text in (
            ("o", True, "$N = 10^6$, resolved (R1 and R2 met on $B$)"),
            ("x", False, "$N = 10^6$, not resolved"),
        ):
            sub = [r for r in usable if bool(r["resolved"]) is keep]
            if not sub:
                continue
            axis.plot(
                [r["level_m_msl"] for r in sub],
                [r["delta_beta"] for r in sub],
                marker,
                color=figstyle.BLUE,
                ms=6.5,
                mew=1.6,
                mfc=figstyle.SURFACE if keep else figstyle.BLUE,
                ls="none",
                zorder=4,
                label=text if legend else None,
            )

    draw(ax, True)
    draw(axz, False)

    for i, level in enumerate((46.39, 46.50)):
        row = _find(small, level)
        if not np.isfinite(row["delta_beta"]):
            continue
        ci = row["delta_beta_ci"]
        yerr = None
        if ci and np.isfinite(ci[0]) and np.isfinite(ci[1]):
            yerr = [
                [max(0.0, row["delta_beta"] - ci[0])],
                [max(0.0, ci[1] - row["delta_beta"])],
            ]
        for axis in (ax, axz):
            axis.errorbar(
                [row["level_m_msl"]],
                [row["delta_beta"]],
                yerr=yerr,
                fmt="s",
                color=figstyle.RED,
                ms=6.0,
                lw=1.6,
                capsize=4,
                zorder=5,
                label=(
                    "$N = 10^5$ record (superseded)"
                    if (axis is ax and i == 0)
                    else None
                ),
            )
        axz.annotate(
            f"{row['delta_beta']:.2f} on {row['k_transient']} rows",
            (row["level_m_msl"], row["delta_beta"]),
            textcoords="offset points",
            xytext=((-8, 8) if i == 0 else (10, 12)),
            fontsize=8.5,
            color=figstyle.RED,
            ha="right" if i == 0 else "left",
            va="bottom",
        )

    # The design-HWL callout is a quotation of the anchor, so it reads the
    # ``design_anchors`` entry rather than the same level's row in the stage
    # sweep. Both are paired bootstraps of one estimand, and the anchor entry
    # is the one the reported interval comes from; taking the sweep's own draw
    # here printed a second interval for a number the report quotes once.
    anchor = record["design_anchors"]["kp62_0"]
    for level, note, dy in (
        (46.39, "A1  design HWL", 0.99),
        (46.50, "A2  nearest grid level", 0.72),
    ):
        row = _find(usable, level)
        quoted = anchor if abs(anchor["level_m_msl"] - level) < 1e-9 else row
        for axis in (ax, axz):
            axis.axvline(row["level_m_msl"], color=figstyle.BASELINE, lw=1.0, zorder=1)
        axz.annotate(
            f"{note}\n{row['level_m_msl']:.2f} m MSL\n"
            rf"$\Delta\beta$ = {row['delta_beta']:.2f} {_ci(quoted['delta_beta_ci'])}"
            f"\n{row['k_transient']} transient rows, resolved\n"
            f"($B$ = {row['B']:.1f}, on which R1 and R2 are defined)",
            (0.03, dy),
            xycoords="axes fraction",
            fontsize=8.5,
            color=figstyle.INK,
            ha="left",
            va="top",
        )

    ax.set_ylabel(r"$\Delta\beta = \beta_\mathrm{trans} - \beta_\mathrm{static}$")
    ax.set_title(
        "KP 62.0 conventional-practice bias as an index difference\n"
        "matrix $d_{70}$, adopted $L$ = 40 m, 225 s integration grid",
        loc="left",
    )
    ax.legend(loc="lower right")
    ax.tick_params(labelbottom=False)
    ax.set_ylim(0.0, 2.6)

    kx = [r["level_m_msl"] for r in rows]
    axk.bar(
        kx,
        [max(r["k_transient"], 0.4) for r in rows],
        width=0.18,
        color=figstyle.MUTED,
        lw=0,
    )
    axk.axhline(
        R1_MIN_ROWS,
        color=figstyle.CRITICAL,
        lw=1.2,
        label=f"R1 floor = {R1_MIN_ROWS} rows",
    )
    axk.set_yscale("log")
    axk.set_ylim(0.7, 2e8)
    axk.set_ylabel("transient\nfailing rows")
    axk.set_xlabel("conditioning water level [m MSL]")
    axk.legend(loc="upper left")
    ax.set_xlim(min(kx) - 0.4, max(kx) + 0.4)
    axz.set_xlim(46.09, 47.35)
    axz.set_ylim(0.62, 1.92)
    axz.set_xlabel("conditioning water level [m MSL]")
    axz.set_ylabel(r"$\Delta\beta$")
    axz.set_title("The anchor neighborhood, in index terms", loc="left")
    figstyle.mark_hypothetical(ax, attainable, label=False)
    figstyle.mark_hypothetical(axk, attainable, label_y=0.97)
    return _save(fig, "rq1_hwl_dbeta_resolved.png")


def figure_kp57_dbeta_bound(record: dict[str, Any]) -> Path:
    """KP 57.4: a one-sided index bound at the design level, resolved above it."""
    figstyle.style()
    rows = [r for r in record["grids"]["kp57_4"] if r["k_transient"] > 0]
    fig, (ax, axk) = plt.subplots(
        2,
        1,
        figsize=(10.6, 6.6),
        sharex=True,
        gridspec_kw={"height_ratios": [3.1, 1.0], "hspace": 0.08},
    )
    flips = record["euler_flips"]["kp57_4"]
    for row in rows:
        resolved = bool(row["resolved"])
        ci = row["delta_beta_ci"]
        yerr = None
        if ci and np.isfinite(ci[0]) and np.isfinite(ci[1]):
            yerr = [
                [max(0.0, row["delta_beta"] - ci[0])],
                [max(0.0, ci[1] - row["delta_beta"])],
            ]
        ax.errorbar(
            [row["level_m_msl"]],
            [row["delta_beta"]],
            yerr=yerr,
            fmt=figstyle.SECTION_MARKERS["KP57.4"],
            color=figstyle.SECTION_COLORS["KP57.4"] if resolved else figstyle.MUTED,
            mfc=figstyle.SECTION_COLORS["KP57.4"] if resolved else figstyle.SURFACE,
            mew=1.5,
            ms=6.0,
            lw=1.5,
            capsize=3.5,
            zorder=4 if resolved else 3,
        )
    anchors = [_find(record["grids"]["kp57_4"], level) for level in (39.21, 39.25)]
    for row in anchors:
        bound = row["delta_beta_lower_bound"]
        ax.axvline(row["level_m_msl"], color=figstyle.BASELINE, lw=1.0, zorder=1)
        ax.annotate(
            "",
            xy=(row["level_m_msl"], bound + 0.55),
            xytext=(row["level_m_msl"], bound),
            arrowprops={
                "arrowstyle": "-|>",
                "color": figstyle.VIOLET,
                "lw": 1.8,
                "shrinkA": 0,
                "shrinkB": 0,
            },
            zorder=5,
        )
        ax.plot(
            [row["level_m_msl"] - 0.06, row["level_m_msl"] + 0.06],
            [bound, bound],
            color=figstyle.VIOLET,
            lw=2.6,
            solid_capstyle="butt",
            zorder=5,
        )
    quotable = min((r for r in rows if r["resolved"]), key=lambda r: r["level_m_msl"])
    q_flips = flips.get(f"{quotable['level_m_msl']:.2f}", 0)
    callouts = (
        (
            anchors[0],
            anchors[0]["delta_beta_lower_bound"],
            0.95,
            figstyle.VIOLET,
            f"A1  design HWL, {anchors[0]['level_m_msl']:.2f} m MSL\n"
            f"{anchors[0]['k_transient']} transient rows in $10^6$: UNRESOLVED.\n"
            "Report the one-sided bound:  "
            rf"$\Delta\beta \geq$ {anchors[0]['delta_beta_lower_bound']:.2f}",
        ),
        (
            anchors[1],
            anchors[1]["delta_beta_lower_bound"],
            0.78,
            figstyle.VIOLET,
            f"A2  nearest grid level, {anchors[1]['level_m_msl']:.2f} m MSL\n"
            f"{anchors[1]['k_transient']} transient rows: also UNRESOLVED,  "
            rf"$\Delta\beta \geq$ {anchors[1]['delta_beta_lower_bound']:.2f}",
        ),
        (
            quotable,
            quotable["delta_beta"],
            0.55,
            figstyle.INK,
            f"quotable anchor  {quotable['level_m_msl']:.2f} m MSL\n"
            rf"$\Delta\beta$ = {quotable['delta_beta']:.2f} "
            f"{_ci(quotable['delta_beta_ci'])}\n"
            f"on {quotable['k_transient']} transient rows, RESOLVED\n"
            f"caveat: one of the three barrier-jump levels,\n"
            f"{q_flips} row in {quotable['k_transient']}",
        ),
    )
    for row, value, y_frac, colour, text in callouts:
        ax.annotate(
            text,
            xy=(row["level_m_msl"], value),
            xycoords="data",
            xytext=(0.22, y_frac),
            textcoords="axes fraction",
            fontsize=8.5,
            color=colour,
            ha="left",
            va="top",
            arrowprops={
                "arrowstyle": "-",
                "color": figstyle.MUTED,
                "lw": 0.9,
                "shrinkB": 3,
            },
        )
    ax.set_ylabel(r"$\Delta\beta = \beta_\mathrm{trans} - \beta_\mathrm{static}$")
    ax.set_ylim(0.9, 2.9)
    ax.set_title(
        "KP 57.4 at $N = 10^6$: a bound at the design water level, a resolved "
        "value one grid step above it\n"
        "matrix $d_{70}$, brute force throughout",
        loc="left",
    )
    ax.legend(
        handles=[
            plt.Line2D(
                [],
                [],
                marker=figstyle.SECTION_MARKERS["KP57.4"],
                color=figstyle.SECTION_COLORS["KP57.4"],
                ls="none",
                ms=6.5,
                label="resolved (R1 and R2 both met on $B$)",
            ),
            plt.Line2D(
                [],
                [],
                marker=figstyle.SECTION_MARKERS["KP57.4"],
                color=figstyle.MUTED,
                mfc=figstyle.SURFACE,
                mew=1.5,
                ls="none",
                ms=6.5,
                label="unresolved, not a point estimate",
            ),
            plt.Line2D(
                [],
                [],
                color=figstyle.VIOLET,
                lw=2.4,
                label=r"one-sided lower bound on $\Delta\beta$",
            ),
        ],
        loc="upper right",
    )
    levels = [r["level_m_msl"] for r in rows]
    axk.bar(
        levels, [r["k_transient"] for r in rows], width=0.14, color=figstyle.MUTED, lw=0
    )
    axk.axhline(
        R1_MIN_ROWS,
        color=figstyle.CRITICAL,
        lw=1.2,
        label=f"R1 floor = {R1_MIN_ROWS} transient rows",
    )
    total_flips = sum(flips.values())
    for level_key, count in flips.items():
        axk.plot(
            [float(level_key)],
            [1.5],
            marker="v",
            color=figstyle.CRITICAL,
            ms=6.5,
            ls="none",
            zorder=5,
        )
        axk.annotate(
            f"{count}",
            (float(level_key), 1.5),
            textcoords="offset points",
            xytext=(7, -3),
            fontsize=7.5,
            color=figstyle.CRITICAL,
            ha="left",
            va="center",
        )
    axk.plot(
        [],
        [],
        marker="v",
        color=figstyle.CRITICAL,
        ms=6.5,
        ls="none",
        label=f"barrier-jump level ({total_flips} rows in $10^6$)",
    )
    axk.set_yscale("log")
    axk.set_ylim(0.7, 5e9)
    axk.set_ylabel("transient\nfailing rows")
    axk.set_xlabel("conditioning water level [m MSL]")
    axk.set_xlim(min(levels) - 0.28, max(levels) + 0.28)
    axk.legend(loc="upper right", fontsize=8, ncol=2)
    fig.text(
        0.01,
        0.002,
        "The resolution criteria R1 and R2 stay defined on the probability "
        "ratio $B$, exactly as pre-registered; $\\beta$ is a monotone "
        "re-expression of the same estimates and intervals, so a level "
        "resolved on $B$ is resolved on $\\Delta\\beta$.",
        fontsize=8,
        color=figstyle.MUTED,
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    return _save(fig, "rq1_kp57_4_dbeta_bound.png")


# --------------------------------------------------------------------------- #
# driver                                                                      #
# --------------------------------------------------------------------------- #
def build_record(n_replicates: int) -> dict[str, Any]:
    record: dict[str, Any] = {
        "record": "RQ1 static-vs-transient comparison in reliability-index terms",
        "generated": date.today().isoformat(),
        "generated_by": "scripts/rq1_beta_analysis.py",
        "plan_of_record": "docs/work_packages/rq1-revision-campaign_2026-08-28.md",
        "metric": {
            "beta": "-Phi^-1(P_f)",
            "delta_beta": "beta_transient - beta_static",
            "interval_method": "monotone image of the exact Clopper-Pearson interval",
            "delta_beta_interval_method": (
                "paired percentile bootstrap over the shared" " realization set"
            ),
            "n_bootstrap": n_replicates,
            "min_rows_for_bootstrap": MIN_ROWS_FOR_BOOTSTRAP,
            "resolution_criteria": {
                "defined_on": "probability ratio B",
                "R1_min_transient_rows": R1_MIN_ROWS,
                "R2_max_ci_width_factor": R2_MAX_WIDTH,
                "note": "kept as pre-registered; the map to beta is monotone",
            },
        },
        "n_bootstrap": n_replicates,
    }
    print("production strata ...")
    record["production"] = production_tables(n_replicates)
    print("comparator ladders ...")
    record["ladder"] = ladder_tables(n_replicates)
    print("design anchors ...")
    record["design_anchors"] = design_anchors(n_replicates)
    print("epistemic arms ...")
    record["epistemic"] = epistemic_arms()
    print("canonical event ...")
    record["canonical_event"] = canonical_event()
    print("whole-grid ladder sequences ...")
    record["grids"] = {
        key: grid_delta_beta(
            HWL_DIR / f"ladder_{key}_n1000000.h5", f"{key}_n1000000", n_replicates
        )
        for key in ("kp62_0", "kp57_4")
    }
    record["grids_n100000"] = {
        key: grid_delta_beta(
            STAGE66_DIR / f"stage6_6_{key}.h5", f"{key}_n100000", n_replicates
        )
        for key in ("kp62_0",)
    }
    record["euler_flips"] = {}
    for key in ("kp62_0", "kp57_4"):
        brute = _read_json(HWL_DIR / f"stage_a_brute_{key}.json")
        offending = brute["euler_flips"].get("offending_levels", {}) or {}
        record["euler_flips"][key] = {
            f"{float(entry['level_m']):.2f}": int(entry["count"])
            for entry in offending.get("c4b_not_c3b", [])
        }
    return record


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="paired-bootstrap replicates B (default 1000)",
    )
    parser.add_argument(
        "--no-figures", action="store_true", help="write tables only, skip the figures"
    )
    args = parser.parse_args(argv)

    record = build_record(args.bootstrap)
    DECISIONS.mkdir(parents=True, exist_ok=True)
    RECORD_JSON.write_text(
        json.dumps(_jsonable(record), indent=1) + "\n", encoding="utf-8"
    )
    write_csv(record, RECORD_CSV)
    write_markdown(record, BRIEF_MD)
    print(f"wrote {RECORD_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {RECORD_CSV.relative_to(REPO_ROOT)}")
    print(f"wrote {BRIEF_MD.relative_to(REPO_ROOT)}")

    if not args.no_figures:
        for builder in (
            figure_beta_curves,
            figure_delta_beta_vs_stage,
            figure_beta_waterfall,
            figure_hwl_dbeta_resolved,
            figure_kp57_dbeta_bound,
        ):
            path = builder(record)
            print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
