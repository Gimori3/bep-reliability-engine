"""How the two RQ1 metrics relate, and what the comparator ladder attributes.

Pure post-processing: this driver contains no physics and evaluates no limit
state. It reads persisted artifacts only, so every number it prints traces to a
named file. It answers four questions that the reliability-index re-expression
of 2026-08-28 left stated rather than measured.

**1. Does the overestimation factor determine the index gap?** No. With

    B      = P_static / P_trans
    dbeta  = beta_trans - beta_static = Phi^-1(P_static) - Phi^-1(P_trans)

``dbeta`` is a function of BOTH branch probabilities, not of their ratio. Fix
``B`` and slide the pair down the tail and ``dbeta`` moves; fix either absolute
probability and ``dbeta`` is then a strictly increasing function of ``B``. That
restricted monotonicity is the whole of what holds, and it is not enough to
carry a width criterion defined on ``B`` over to ``dbeta``.

**2. What does a cancellation claim mean, metric by metric?** Two different
things. An input that multiplies both branch probabilities by the same factor
leaves ``B`` exactly invariant and moves ``dbeta``. An input that shifts both
reliability indices by the same amount leaves ``dbeta`` exactly invariant and
moves ``B``. Neither condition implies the other, so "cancels" must name its
metric. Measured here input by input from the persisted arm sweeps.

**3. Are the comparator ladder's components order-independent?** Only their
sum is. The ladder telescopes, so beta(C4b) - beta(C0) is the same by any
path, but the share it attributes to the head convention depends on where in
the path the head toggle sits. Two legitimate orders are computed from the same
N = 1e6 rows and compared, with a paired-bootstrap interval on their
difference.

**4. Does a shared sample remove sampling noise?** It reduces it. The paired
bootstrap standard error is measured against the independent-resample one at
every anchor; the ratio is the variance reduction, and the paired error is not
zero.

Inputs (all read-only)::

    results/hwl_bias_resolution/ladder_kp{57_4,62_0}_n1000000.h5
    results/equal_head_convention/tokachi_kp{57.4,62.0}_historical_matrix_n1000000.h5
    results/equal_head_convention/*_n1000000.production_trans.npy
    results/sensitivity/adr0045_mp/*_mp.h5           + production sweeps
    results/sensitivity/adr0049_critical_length/*_l_c_{lower,upper}.h5
    results/tokachi_kp*_historical_matrix.h5         the paired baselines
    docs/decisions/epistemic-bracket-synthesis.json  every other arm, points only
    docs/decisions/rq1-beta-reexpression.json        the published per-level record

Outputs::

    docs/decisions/metric-and-decomposition.json     machine-readable record
    docs/decisions/metric-and-decomposition-study.md is written by hand against it

Usage (repo root, venv active)::

    python scripts/metric_decomposition_study.py
    python scripts/metric_decomposition_study.py --bootstrap 200   # faster draft

Statistics. Every interval in this driver is a paired bootstrap over the shared
realization set, and the two kernels are **reused, never re-implemented**:
``dem_cross_section_study._pattern_counts`` for the four-indicator contingency
and ``rq1_beta_analysis.paired_bootstrap_means`` for the comparator columns. A
second copy of either could drift from the one that produced the numbers this
note compares against.
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
from numpy.typing import NDArray
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

RESULTS = REPO_ROOT / "results"
DOCS = REPO_ROOT / "docs"
DECISIONS = DOCS / "decisions"
RECORD_JSON = DECISIONS / "metric-and-decomposition.json"

#: Pre-registered ratio-space criteria (ADR-0040 section 1.1), reproduced not
#: redefined. R1 is a condition on the transient COUNT; R2 on the width of the
#: interval on B.
R1_MIN_ROWS = 30
R2_MAX_WIDTH_FACTOR = 2.0

#: Index-space precision criterion, derived from R2's own stated rule rather
#: than chosen after seeing the results. ADR-0040 section 1.1 fixed R2 = 2.0 so
#: that the interval "cannot straddle a decade": in log terms the interval
#: occupies log10(2) = 0.301 of the one-decade granularity the ratio claim is
#: quoted to. The index claim's granularity is the span the four design-level
#: dbeta values are quoted over, 0.90 to 1.87, so about one index unit. The same
#: 30 per cent rule applied to a granularity of 1.0 index unit gives an ADDITIVE
#: width ceiling of 0.30. It is a ceiling on the DIRECTLY EVALUATED paired
#: bootstrap interval on dbeta, never an image of the interval on B.
R2_BETA_MAX_WIDTH = 0.30
R2_BETA_DERIVATION = (
    "log10(R2_MAX_WIDTH_FACTOR) = 0.301 of one decade, the granularity of the "
    "ratio claim (ADR-0040 s1.1); the same fraction of the 1.0 index unit the "
    "four design-level dbeta values span (0.90 to 1.87) gives 0.30"
)

BOOTSTRAP_N = 2000
CONFIDENCE = 0.95

#: The two N = 1e6 sections that carry both a comparator ladder and a
#: gross-head transient arm, so both ladder orders exist on identical rows.
LADDER_SECTIONS = {
    "kp62_0": {
        "label": "KP 62.0",
        "ladder": "results/hwl_bias_resolution/ladder_kp62_0_n1000000.h5",
        "equal_head": (
            "results/equal_head_convention/"
            "tokachi_kp62.0_historical_matrix_n1000000.h5"
        ),
        "production_trans": (
            "results/equal_head_convention/"
            "tokachi_kp62.0_historical_matrix_n1000000.production_trans.npy"
        ),
        "design_hwl_m": 46.39,
    },
    "kp57_4": {
        "label": "KP 57.4",
        "ladder": "results/hwl_bias_resolution/ladder_kp57_4_n1000000.h5",
        "equal_head": (
            "results/equal_head_convention/"
            "tokachi_kp57.4_historical_matrix_n1000000.h5"
        ),
        "production_trans": (
            "results/equal_head_convention/"
            "tokachi_kp57.4_historical_matrix_n1000000.production_trans.npy"
        ),
        "design_hwl_m": 39.21,
    },
}

#: Arm sweeps whose per-row failure matrices are persisted, so the displacement
#: can carry a paired interval in BOTH metrics rather than a point estimate.
PAIRED_ARMS = {
    "m_p": {
        "adr": "0045",
        "directory": "results/sensitivity/adr0045_mp",
        "suffix": "_mp",
        "channel_reading": (
            "common-mode: multiplies the single-source H_c in both branches"
        ),
    },
    "l_c_lower": {
        "adr": "0049",
        "directory": "results/sensitivity/adr0049_critical_length",
        "suffix": "_l_c_lower",
        "channel_reading": "transient-only: no static channel at all",
    },
    "l_c_upper": {
        "adr": "0049",
        "directory": "results/sensitivity/adr0049_critical_length",
        "suffix": "_l_c_upper",
        "channel_reading": "transient-only: no static channel at all",
    },
}

SECTIONS = ("57.4", "58.8", "60.0", "62.0")


# --------------------------------------------------------------------------- #
# reused kernels                                                              #
# --------------------------------------------------------------------------- #
def _load_script_module(name: str):
    """Import a sibling driver for a kernel, the route the other studies use."""
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ADR0047 = _load_script_module("dem_cross_section_study")
_RQ1 = _load_script_module("rq1_beta_analysis")

beta_from_p = _RQ1.beta_from_p
paired_bootstrap_means = _RQ1.paired_bootstrap_means
_pattern_counts = _ADR0047._pattern_counts
_PATTERN_BITS = _ADR0047._PATTERN_BITS


def _quantile_ci(values: NDArray[np.float64]) -> tuple[float, float]:
    alpha = (1.0 - CONFIDENCE) / 2.0
    finite = values[np.isfinite(values)]
    if finite.size < 0.5 * values.size:
        return float("nan"), float("nan")
    return float(np.quantile(finite, alpha)), float(np.quantile(finite, 1.0 - alpha))


# --------------------------------------------------------------------------- #
# stage 1: the metric relationship, analytically                              #
# --------------------------------------------------------------------------- #
def metric_relationship() -> dict[str, Any]:
    """B does not determine dbeta; with an absolute probability fixed it does.

    The counterexample family is the production KP 62.0 design anchor's own
    ratio, slid down and up the tail at constant B. The monotonicity claim is
    checked against its analytic derivative, not asserted.
    """
    b_fixed = 1696.0 / 63.0
    family = []
    for p_t in (1e-6, 1e-5, 6.3e-5, 1e-4, 1e-3, 1e-2, 3e-2):
        p_s = b_fixed * p_t
        if p_s >= 1.0:
            continue
        family.append(
            {
                "p_transient": p_t,
                "p_static": p_s,
                "B": b_fixed,
                "beta_static": beta_from_p(p_s),
                "beta_transient": beta_from_p(p_t),
                "delta_beta": beta_from_p(p_t) - beta_from_p(p_s),
            }
        )
    deltas = [row["delta_beta"] for row in family]

    # Restricted monotonicity, both restrictions, against the analytic slope.
    monotone_checks = []
    for label, fixed_p in (("p_transient_fixed", 6.3e-5), ("p_static_fixed", 1.696e-3)):
        rows = []
        for b in (2.0, 5.0, 10.0, 26.9, 50.0, 100.0):
            if label == "p_transient_fixed":
                p_t, p_s = fixed_p, b * fixed_p
                slope = fixed_p / norm.pdf(norm.ppf(b * fixed_p))
            else:
                p_s, p_t = fixed_p, fixed_p / b
                slope = fixed_p / (b**2 * norm.pdf(norm.ppf(fixed_p / b)))
            if not (0.0 < p_s < 1.0 and 0.0 < p_t < 1.0):
                continue
            h = 1e-7
            if label == "p_transient_fixed":
                num = (
                    (beta_from_p(fixed_p) - beta_from_p((b + h) * fixed_p))
                    - (beta_from_p(fixed_p) - beta_from_p((b - h) * fixed_p))
                ) / (2 * h)
            else:
                num = (
                    (beta_from_p(fixed_p / (b + h)) - beta_from_p(fixed_p))
                    - (beta_from_p(fixed_p / (b - h)) - beta_from_p(fixed_p))
                ) / (2 * h)
            rows.append(
                {
                    "B": b,
                    "delta_beta": beta_from_p(p_t) - beta_from_p(p_s),
                    "analytic_slope": float(slope),
                    "numeric_slope": float(num),
                    "slope_positive": bool(slope > 0.0),
                }
            )
        monotone_checks.append({"restriction": label, "rows": rows})

    # The two notions of common mode.
    p_s0, p_t0 = 1.696e-3, 6.3e-5
    b0 = p_s0 / p_t0
    d0 = beta_from_p(p_t0) - beta_from_p(p_s0)
    multiplicative = []
    for c in (0.1, 0.5, 2.0, 10.0):
        p_s, p_t = c * p_s0, c * p_t0
        multiplicative.append(
            {
                "factor_on_both_probabilities": c,
                "B": p_s / p_t,
                "B_unchanged": bool(abs(p_s / p_t - b0) < 1e-12),
                "delta_beta": beta_from_p(p_t) - beta_from_p(p_s),
                "delta_beta_ratio_to_baseline": (beta_from_p(p_t) - beta_from_p(p_s))
                / d0,
            }
        )
    additive = []
    for shift in (-0.5, -0.2, 0.2, 0.5):
        p_s = float(norm.cdf(-(beta_from_p(p_s0) + shift)))
        p_t = float(norm.cdf(-(beta_from_p(p_t0) + shift)))
        additive.append(
            {
                "shift_on_both_indices": shift,
                "delta_beta": beta_from_p(p_t) - beta_from_p(p_s),
                "delta_beta_unchanged": bool(
                    abs((beta_from_p(p_t) - beta_from_p(p_s)) - d0) < 1e-9
                ),
                "B": p_s / p_t,
                "B_ratio_to_baseline": (p_s / p_t) / b0,
            }
        )

    # R2's width verdict does not constrain the dbeta interval width.
    width_transfer = []
    for p_t in (1e-6, 1e-4, 1e-2, 5e-2):
        b_lo, b_hi = 5.0, 10.0
        if b_hi * p_t >= 1.0:
            continue
        lo = beta_from_p(p_t) - beta_from_p(b_lo * p_t)
        hi = beta_from_p(p_t) - beta_from_p(b_hi * p_t)
        width_transfer.append(
            {
                "p_transient": p_t,
                "B_interval": [b_lo, b_hi],
                "B_width_factor": b_hi / b_lo,
                "R2_passes": bool(b_hi / b_lo <= R2_MAX_WIDTH_FACTOR),
                "delta_beta_interval": [lo, hi],
                "delta_beta_width": hi - lo,
            }
        )

    return {
        "definitions": {
            "B": "P_static / P_transient",
            "beta": "-Phi^-1(P_f)",
            "delta_beta": "beta_transient - beta_static",
        },
        "constant_B_family": {
            "B": b_fixed,
            "rows": family,
            "delta_beta_min": min(deltas),
            "delta_beta_max": max(deltas),
            "delta_beta_span_factor": max(deltas) / min(deltas),
            "verdict": (
                "one value of B carries a whole range of dbeta, so there is no "
                "map from B alone"
            ),
        },
        "restricted_monotonicity": {
            "statement": (
                "with EITHER absolute branch probability held fixed, dbeta is a "
                "strictly increasing function of B"
            ),
            "d_delta_beta_d_B_at_fixed_p_transient": "p_t / phi(Phi^-1(B p_t)) > 0",
            "d_delta_beta_d_B_at_fixed_p_static": (
                "p_s / (B^2 phi(Phi^-1(p_s / B))) > 0"
            ),
            "checks": monotone_checks,
            "all_slopes_positive": all(
                row["slope_positive"]
                for block in monotone_checks
                for row in block["rows"]
            ),
            "max_relative_slope_error": max(
                abs(row["numeric_slope"] - row["analytic_slope"])
                / abs(row["analytic_slope"])
                for block in monotone_checks
                for row in block["rows"]
            ),
        },
        "two_notions_of_common_mode": {
            "multiplicative_on_probabilities": {
                "leaves_invariant": "B",
                "moves": "delta_beta",
                "rows": multiplicative,
            },
            "additive_on_indices": {
                "leaves_invariant": "delta_beta",
                "moves": "B",
                "rows": additive,
            },
            "verdict": (
                "cancellation in B and cancellation in dbeta are different "
                "conditions and neither implies the other"
            ),
        },
        "tail_asymptotics": {
            "statement": (
                "for small p, dbeta ~ ln(B) / beta, so at fixed B dbeta shrinks"
                " as the tail deepens"
            ),
            "rows": [
                {
                    "p_transient": p_t,
                    "B": b_fixed,
                    "delta_beta": beta_from_p(p_t) - beta_from_p(b_fixed * p_t),
                    "ln_B_over_beta_static": float(
                        np.log(b_fixed) / beta_from_p(b_fixed * p_t)
                    ),
                }
                for p_t in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6)
            ],
        },
        "R2_width_does_not_transfer": {
            "R2_max_width_factor": R2_MAX_WIDTH_FACTOR,
            "rows": width_transfer,
            "delta_beta_width_span_factor": (
                max(r["delta_beta_width"] for r in width_transfer)
                / min(r["delta_beta_width"] for r in width_transfer)
            ),
        },
    }


# --------------------------------------------------------------------------- #
# stage 2: the two ladder orders                                              #
# --------------------------------------------------------------------------- #
def _ladder_columns(key: str) -> dict[str, Any]:
    """C0, C1, C3b, C4b and the gross-head transient on identical rows."""
    spec = LADDER_SECTIONS[key]
    with h5py.File(REPO_ROOT / spec["ladder"], "r") as handle:
        grid = handle["conditioning_grid"][:]
        ladder = {
            name: handle[f"comparators/{name}"][:]
            for name in ("C0", "C1", "C3b", "C4b")
        }
    with h5py.File(REPO_ROOT / spec["equal_head"], "r") as handle:
        eq_grid = handle["conditioning_grid"][:]
        eq_static = handle["failure_matrix_static"][:]
        eq_gross = handle["failure_matrix_trans"][:]
    production = np.load(REPO_ROOT / spec["production_trans"])

    # Gate the pairing rather than assume it: the equal-head arm reproduced the
    # ladder's seed recipe, so its static column must be bit-identical to C0 and
    # its stored production transient to C4b at every shared level.
    gates = []
    columns: dict[float, dict[str, NDArray[np.bool_]]] = {}
    for j, level in enumerate(eq_grid):
        i = int(np.argmin(np.abs(grid - level)))
        static_identical = bool(np.array_equal(eq_static[:, j], ladder["C0"][:, i]))
        trans_identical = bool(np.array_equal(production[:, j], ladder["C4b"][:, i]))
        gates.append(
            {
                "level_m_msl": float(level),
                "ladder_index": i,
                "ladder_level_m_msl": float(grid[i]),
                "static_bit_identical_to_C0": static_identical,
                "stored_production_bit_identical_to_C4b": trans_identical,
            }
        )
        columns[float(level)] = {
            "C0": ladder["C0"][:, i],
            "C1": ladder["C1"][:, i],
            "C3b": ladder["C3b"][:, i],
            "C4b": ladder["C4b"][:, i],
            "C4b_gross": eq_gross[:, j],
        }
    failed = [
        g
        for g in gates
        if not (
            g["static_bit_identical_to_C0"]
            and g["stored_production_bit_identical_to_C4b"]
        )
    ]
    if failed:
        raise RuntimeError(
            "the equal-head arm and the ADR-0040 ladder are not row-paired at "
            f"{[g['level_m_msl'] for g in failed]}; every comparison below "
            "assumes one shared realization set, so this refuses rather than "
            "reporting a difference that could be two samples"
        )
    return {"gates": gates, "columns": columns, "spec": spec}


def ladder_orders(n_replicates: int) -> dict[str, Any]:
    """Two legitimate orders of the additive beta ladder, on identical rows.

    Order A is the published one: the head toggle first, then the initiation
    gate, then the temporal step. Order B puts the head toggle last, which is
    exactly the equal-head-convention comparison read as a ladder step. Both
    telescope to beta(C4b) - beta(C0); the head-convention attribution does not
    have to agree, and the interaction is the measured disagreement.

    Comparators (ADR-0040 Decision 1, ADR-0051)::

        C0        gross-head static           (gross,   no gate, static)
        C1        crack-reduced static        (reduced, no gate, static)
        C3b       gate AND crack-reduced      (reduced, gate,    static)
        C4b       production transient        (reduced, gate,    transient)
        C4b_gross gross-head transient        (gross,   gate,    transient)
    """
    out: dict[str, Any] = {}
    for key in LADDER_SECTIONS:
        loaded = _ladder_columns(key)
        levels = []
        for level, cols in loaded["columns"].items():
            n = int(cols["C0"].size)
            counts = {name: int(col.sum()) for name, col in cols.items()}
            betas = {name: beta_from_p(k / n) for name, k in counts.items()}
            total = betas["C4b"] - betas["C0"]

            order_a = {
                "order": ["head_convention", "initiation_gate", "temporal"],
                "path": ["C0", "C1", "C3b", "C4b"],
                "head_convention": betas["C1"] - betas["C0"],
                "initiation_gate": betas["C3b"] - betas["C1"],
                "temporal": betas["C4b"] - betas["C3b"],
            }
            order_a["sum"] = (
                order_a["head_convention"]
                + order_a["initiation_gate"]
                + order_a["temporal"]
            )
            order_b = {
                "order": ["gate_and_temporal", "head_convention"],
                "path": ["C0", "C4b_gross", "C4b"],
                "gate_and_temporal": betas["C4b_gross"] - betas["C0"],
                "head_convention": betas["C4b"] - betas["C4b_gross"],
            }
            order_b["sum"] = order_b["gate_and_temporal"] + order_b["head_convention"]

            interaction = order_a["head_convention"] - order_b["head_convention"]

            # Paired bootstrap on the order difference: one row resample feeds
            # all five comparator columns, so the interaction inherits pairing.
            stacked = np.stack(
                [
                    cols["C0"],
                    cols["C1"],
                    cols["C4b_gross"],
                    cols["C4b"],
                ],
                axis=1,
            )
            means = paired_bootstrap_means(
                stacked,
                n_replicates=n_replicates,
                seed=_RQ1._stable_seed(f"metric-ladder-{key}-{level:.2f}"),
            )
            with np.errstate(divide="ignore", invalid="ignore"):
                head_a = beta_from_p(means[:, 1]) - beta_from_p(means[:, 0])
                head_b = beta_from_p(means[:, 3]) - beta_from_p(means[:, 2])
                total_rep = beta_from_p(means[:, 3]) - beta_from_p(means[:, 0])
            inter_lo, inter_hi = _quantile_ci(head_a - head_b)
            total_lo, total_hi = _quantile_ci(total_rep)

            shapley_head = 0.5 * (
                order_a["head_convention"] + order_b["head_convention"]
            )
            levels.append(
                {
                    "level_m_msl": level,
                    "n_samples": n,
                    "counts": counts,
                    "betas": betas,
                    "total_delta_beta": total,
                    "total_delta_beta_ci": [total_lo, total_hi],
                    "order_A": order_a,
                    "order_B": order_b,
                    "orders_telescope_to_same_total": bool(
                        abs(order_a["sum"] - total) < 1e-12
                        and abs(order_b["sum"] - total) < 1e-12
                    ),
                    "head_share_A": (
                        order_a["head_convention"] / total
                        if np.isfinite(total) and total != 0.0
                        else None
                    ),
                    "head_share_B": (
                        order_b["head_convention"] / total
                        if np.isfinite(total) and total != 0.0
                        else None
                    ),
                    "interaction_head": interaction,
                    "interaction_head_ci": [inter_lo, inter_hi],
                    "interaction_resolved": bool(
                        np.isfinite(inter_lo)
                        and np.isfinite(inter_hi)
                        and (inter_lo > 0.0 or inter_hi < 0.0)
                    ),
                    "shapley_head": shapley_head,
                    "shapley_head_share": (
                        shapley_head / total
                        if np.isfinite(total) and total != 0.0
                        else None
                    ),
                }
            )
        out[key] = {
            "section": loaded["spec"]["label"],
            "design_hwl_m_msl": loaded["spec"]["design_hwl_m"],
            "pairing_gates": loaded["gates"],
            "pairing_gates_all_pass": all(
                g["static_bit_identical_to_C0"]
                and g["stored_production_bit_identical_to_C4b"]
                for g in loaded["gates"]
            ),
            "levels": levels,
        }
    return out


# --------------------------------------------------------------------------- #
# stage 3: what the shared sample actually buys                               #
# --------------------------------------------------------------------------- #
def _analytic_variance_reduction(p_s: float, p_t: float, n: int) -> dict[str, Any]:
    """Exact delta-method variance of both statistics, paired and unpaired.

    The transient failure set is contained in the static one on every row the
    engine reaches (the nesting theorem), so the joint probability of failing
    both is exactly ``p_t`` and

        Cov(p_s_hat, p_t_hat) = p_t (1 - p_s) / n.

    For ``dbeta`` the two sensitivities have opposite signs, so that positive
    covariance enters with a minus sign and the paired variance is the smaller.
    For ``log B`` the algebra collapses: the paired variance is the DIFFERENCE
    of the two per-branch terms where the unpaired one is their sum. Both are
    exact, so the reduction does not have to be read off a bootstrap.
    """
    if not (0.0 < p_t < 1.0 and 0.0 < p_s < 1.0):
        return {"available": False}
    a_s = 1.0 / norm.pdf(norm.ppf(p_s))
    a_t = -1.0 / norm.pdf(norm.ppf(p_t))
    var_s = p_s * (1.0 - p_s) / n
    var_t = p_t * (1.0 - p_t) / n
    cov = p_t * (1.0 - p_s) / n
    var_d_paired = a_s**2 * var_s + a_t**2 * var_t + 2.0 * a_s * a_t * cov
    var_d_independent = a_s**2 * var_s + a_t**2 * var_t
    term_t = (1.0 - p_t) / (n * p_t)
    term_s = (1.0 - p_s) / (n * p_s)
    var_lb_paired = term_t - term_s
    var_lb_independent = term_t + term_s
    return {
        "available": True,
        "delta_beta_se_paired": float(np.sqrt(var_d_paired)),
        "delta_beta_se_independent": float(np.sqrt(var_d_independent)),
        "delta_beta_variance_reduction": float(var_d_independent / var_d_paired),
        "log_B_se_paired": float(np.sqrt(var_lb_paired)),
        "log_B_se_independent": float(np.sqrt(var_lb_independent)),
        "log_B_variance_reduction": float(var_lb_independent / var_lb_paired),
        "paired_variance_is_positive": bool(var_d_paired > 0.0),
    }


def shared_sample_variance(n_replicates: int) -> dict[str, Any]:
    """Paired against independent resampling, for dbeta and for B.

    The paired bootstrap resamples one row index set and evaluates both
    branches on it. The independent bootstrap resamples each branch separately,
    which is what an unpaired comparison of two runs would give. The ratio of
    standard errors is the variance reduction the shared sample buys; that the
    paired error is not zero is the point.
    """
    out: dict[str, Any] = {}
    for key in LADDER_SECTIONS:
        loaded = _ladder_columns(key)
        rows = []
        for level, cols in loaded["columns"].items():
            static, trans = cols["C0"], cols["C4b"]
            n = int(static.size)
            k_s, k_t = int(static.sum()), int(trans.sum())
            if k_t < R1_MIN_ROWS:
                rows.append(
                    {
                        "level_m_msl": level,
                        "k_static": k_s,
                        "k_transient": k_t,
                        "below_R1": True,
                    }
                )
                continue
            seed = _RQ1._stable_seed(f"metric-crn-{key}-{level:.2f}")
            paired = paired_bootstrap_means(
                np.stack([static, trans], axis=1),
                n_replicates=n_replicates,
                seed=seed,
            )
            rng = np.random.default_rng(seed + 1)
            ind_s = rng.binomial(n, k_s / n, size=n_replicates) / n
            ind_t = rng.binomial(n, k_t / n, size=n_replicates) / n
            analytic = _analytic_variance_reduction(k_s / n, k_t / n, n)
            with np.errstate(divide="ignore", invalid="ignore"):
                d_paired = beta_from_p(paired[:, 1]) - beta_from_p(paired[:, 0])
                d_ind = beta_from_p(ind_t) - beta_from_p(ind_s)
                b_paired = paired[:, 0] / paired[:, 1]
                b_ind = ind_s / ind_t

            def _se(values: NDArray[np.float64]) -> float:
                finite = values[np.isfinite(values)]
                return float(np.std(finite, ddof=1))

            se_d_paired, se_d_ind = _se(d_paired), _se(d_ind)
            se_b_paired, se_b_ind = _se(np.log(b_paired)), _se(np.log(b_ind))
            rows.append(
                {
                    "level_m_msl": level,
                    "k_static": k_s,
                    "k_transient": k_t,
                    "below_R1": False,
                    "delta_beta_se_paired": se_d_paired,
                    "delta_beta_se_independent": se_d_ind,
                    "delta_beta_variance_reduction": (
                        (se_d_ind / se_d_paired) ** 2 if se_d_paired > 0 else None
                    ),
                    "delta_beta_se_paired_is_zero": bool(se_d_paired == 0.0),
                    "log_B_se_paired": se_b_paired,
                    "log_B_se_independent": se_b_ind,
                    "log_B_variance_reduction": (
                        (se_b_ind / se_b_paired) ** 2 if se_b_paired > 0 else None
                    ),
                    "analytic": analytic,
                }
            )
        out[key] = {"section": loaded["spec"]["label"], "levels": rows}
    return out


# --------------------------------------------------------------------------- #
# stage 4: cancellation, input by input and metric by metric                  #
# --------------------------------------------------------------------------- #
def _displacement_ci(
    counts: NDArray[np.int64], *, n_boot: int, seed: int
) -> dict[str, Any]:
    """Both metrics' displacement from the same 16-cell paired resample.

    ``rho`` is the ratio-of-ratios of ADR-0047 section 4.5, cancellation being
    ``rho = 1``. ``delta_delta_beta`` is its index-space analogue, a
    difference-of-differences, cancellation being ``0``. The two verdicts are
    computed from one resample so their disagreement cannot be a sampling
    artifact between two runs.
    """
    total = int(counts.sum())
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(total, counts / total, size=n_boot).astype(np.float64)
    means = (
        draws @ _PATTERN_BITS.T / total
    )  # base_static, base_trans, arm_static, arm_trans
    point = counts @ _PATTERN_BITS.T / total
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = (means[:, 2] / means[:, 3]) / (means[:, 0] / means[:, 1])
        ddb = (beta_from_p(means[:, 3]) - beta_from_p(means[:, 2])) - (
            beta_from_p(means[:, 1]) - beta_from_p(means[:, 0])
        )
        rho_point = float((point[2] / point[3]) / (point[0] / point[1]))
        ddb_point = float(
            (beta_from_p(point[3]) - beta_from_p(point[2]))
            - (beta_from_p(point[1]) - beta_from_p(point[0]))
        )
    rho_lo, rho_hi = _quantile_ci(rho)
    ddb_lo, ddb_hi = _quantile_ci(ddb)
    return {
        "p_static_baseline": float(point[0]),
        "p_transient_baseline": float(point[1]),
        "p_static_arm": float(point[2]),
        "p_transient_arm": float(point[3]),
        "rho": rho_point,
        "rho_ci": [rho_lo, rho_hi],
        "rho_resolved": bool(
            np.isfinite(rho_lo)
            and np.isfinite(rho_hi)
            and (rho_lo > 1.0 or rho_hi < 1.0)
        ),
        "delta_beta_baseline": float(beta_from_p(point[1]) - beta_from_p(point[0])),
        "delta_beta_arm": float(beta_from_p(point[3]) - beta_from_p(point[2])),
        "delta_delta_beta": ddb_point,
        "delta_delta_beta_ci": [ddb_lo, ddb_hi],
        "delta_delta_beta_resolved": bool(
            np.isfinite(ddb_lo)
            and np.isfinite(ddb_hi)
            and (ddb_lo > 0.0 or ddb_hi < 0.0)
        ),
        "min_cell_failures": int(min(point[0], point[1], point[2], point[3]) * total),
    }


def _read_matrices(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        return {
            "grid": handle["conditioning_grid"][:],
            "static": handle["failure_matrix_static"][:],
            "trans": handle["failure_matrix_trans"][:],
        }


def cancellation_both_metrics(n_boot: int) -> dict[str, Any]:
    """Arms with persisted matrices, measured in B and in dbeta at once."""
    attainable = _RQ1.attainable_maxima()
    out: dict[str, Any] = {}
    for arm, spec in PAIRED_ARMS.items():
        arm_rows = []
        for section in SECTIONS:
            base_path = RESULTS / f"tokachi_kp{section}_historical_matrix.h5"
            arm_path = (
                REPO_ROOT
                / spec["directory"]
                / f"tokachi_kp{section}_historical_matrix{spec['suffix']}.h5"
            )
            if not (base_path.exists() and arm_path.exists()):
                arm_rows.append(
                    {
                        "section": f"KP {section}",
                        "available": False,
                        "reason": "missing artifact",
                    }
                )
                continue
            base, arm_data = _read_matrices(base_path), _read_matrices(arm_path)
            if not np.allclose(base["grid"], arm_data["grid"]):
                arm_rows.append(
                    {
                        "section": f"KP {section}",
                        "available": False,
                        "reason": "grid mismatch",
                    }
                )
                continue
            levels = []
            for i, level in enumerate(base["grid"]):
                counts = _pattern_counts(
                    base["static"][:, i],
                    base["trans"][:, i],
                    arm_data["static"][:, i],
                    arm_data["trans"][:, i],
                )
                entry = _displacement_ci(
                    counts,
                    n_boot=n_boot,
                    # Stable across processes: Python's hash() is salted per
                    # interpreter, which would make the intervals irreproducible.
                    seed=_RQ1._stable_seed(f"metric-arm-{arm}-{section}-{level:.2f}"),
                )
                entry["level_m_msl"] = float(level)
                if entry["min_cell_failures"] > 0:
                    levels.append(entry)
            evaluated = [
                lv
                for lv in levels
                if np.isfinite(lv["rho"]) and np.isfinite(lv["delta_delta_beta"])
            ]
            static_exactly_invariant = bool(
                all(
                    abs(lv["p_static_arm"] - lv["p_static_baseline"]) < 1e-15
                    for lv in levels
                )
            )
            # The quotable window: inside the attainable range (ADR-0024), with
            # enough failures in every one of the four cells to support a verdict
            # (the R1 floor), and the verdict actually resolved. Maxima taken
            # over anything wider mix in hypothetical stages and single-row
            # counts, which is how a displacement gets overstated.
            ceiling = attainable[section]
            quotable = [
                lv
                for lv in evaluated
                if lv["level_m_msl"] <= ceiling + 1e-9
                and lv["min_cell_failures"] >= R1_MIN_ROWS
            ]
            arm_rows.append(
                {
                    "section": f"KP {section}",
                    "available": True,
                    "attainable_max_m_msl": ceiling,
                    "n_levels_evaluated": len(evaluated),
                    "n_levels_quotable": len(quotable),
                    "static_exactly_invariant": static_exactly_invariant,
                    "max_rho_departure_factor": (
                        max(
                            (
                                max(lv["rho"], 1.0 / lv["rho"])
                                for lv in evaluated
                                if lv["rho"] > 0
                            ),
                            default=None,
                        )
                    ),
                    "max_abs_delta_delta_beta": (
                        max(
                            (abs(lv["delta_delta_beta"]) for lv in evaluated),
                            default=None,
                        )
                    ),
                    "max_resolved_rho_departure_factor_quotable": (
                        max(
                            (
                                max(lv["rho"], 1.0 / lv["rho"])
                                for lv in quotable
                                if lv["rho"] > 0 and lv["rho_resolved"]
                            ),
                            default=None,
                        )
                    ),
                    "max_resolved_abs_delta_delta_beta_quotable": (
                        max(
                            (
                                abs(lv["delta_delta_beta"])
                                for lv in quotable
                                if lv["delta_delta_beta_resolved"]
                            ),
                            default=None,
                        )
                    ),
                    "n_rho_resolved": sum(1 for lv in evaluated if lv["rho_resolved"]),
                    "n_delta_beta_resolved": sum(
                        1 for lv in evaluated if lv["delta_delta_beta_resolved"]
                    ),
                    "n_quotable_rho_resolved": sum(
                        1 for lv in quotable if lv["rho_resolved"]
                    ),
                    "n_quotable_delta_beta_resolved": sum(
                        1 for lv in quotable if lv["delta_delta_beta_resolved"]
                    ),
                    "n_disagree_rho_resolved_dbeta_not": sum(
                        1
                        for lv in evaluated
                        if lv["rho_resolved"] and not lv["delta_delta_beta_resolved"]
                    ),
                    "n_disagree_dbeta_resolved_rho_not": sum(
                        1
                        for lv in evaluated
                        if lv["delta_delta_beta_resolved"] and not lv["rho_resolved"]
                    ),
                    "n_quotable_disagree_rho_only": sum(
                        1
                        for lv in quotable
                        if lv["rho_resolved"] and not lv["delta_delta_beta_resolved"]
                    ),
                    "n_quotable_disagree_dbeta_only": sum(
                        1
                        for lv in quotable
                        if lv["delta_delta_beta_resolved"] and not lv["rho_resolved"]
                    ),
                    "levels": evaluated,
                }
            )
        out[arm] = {
            "adr": spec["adr"],
            "channel_reading": spec["channel_reading"],
            "sections": arm_rows,
        }
    return out


def cancellation_point_estimates() -> dict[str, Any]:
    """Every other persisted arm, in both metrics, point estimates only.

    Read straight out of the bracket synthesis record, which stores each arm's
    own static and transient probability at every level beside the baseline
    curves. No interval, because reproducing one needs the arm matrices those
    sweeps did not keep; the point estimates are enough to show that a ratio
    verdict and an index verdict are different statements.
    """
    path = DECISIONS / "epistemic-bracket-synthesis.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for section in record["sections"]:
        base_t = section["P_f_trans_baseline_curve"]
        base_s = section["P_f_static_baseline_curve"]
        grid = section["grid_m_msl"]
        for arm, block in section["arms"].items():
            if not block.get("available", True):
                continue
            rows = []
            for i, level in enumerate(grid):
                p_t0, p_s0 = base_t[i], base_s[i]
                lv = block["levels"][i]
                p_t1, p_s1 = lv.get("P_f_trans_arm"), lv.get("P_f_static_arm")
                if not all(
                    isinstance(v, (int, float)) and 0.0 < v < 1.0
                    for v in (p_t0, p_s0, p_t1, p_s1)
                ):
                    continue
                d0 = beta_from_p(p_t0) - beta_from_p(p_s0)
                d1 = beta_from_p(p_t1) - beta_from_p(p_s1)
                rows.append(
                    {
                        "level_m_msl": level,
                        "rho": (p_s1 / p_t1) / (p_s0 / p_t0),
                        "delta_beta_baseline": d0,
                        "delta_beta_arm": d1,
                        "delta_delta_beta": d1 - d0,
                    }
                )
            if not rows:
                continue
            out.append(
                {
                    "section": section["section"],
                    "arm": arm,
                    "n_levels": len(rows),
                    "rho_min": min(r["rho"] for r in rows),
                    "rho_max": max(r["rho"] for r in rows),
                    "max_rho_departure_factor": max(
                        max(r["rho"], 1.0 / r["rho"]) for r in rows if r["rho"] > 0
                    ),
                    "delta_delta_beta_min": min(r["delta_delta_beta"] for r in rows),
                    "delta_delta_beta_max": max(r["delta_delta_beta"] for r in rows),
                    "max_abs_delta_delta_beta": max(
                        abs(r["delta_delta_beta"]) for r in rows
                    ),
                    "levels": rows,
                }
            )
    return {"source": str(path.relative_to(REPO_ROOT)).replace("\\", "/"), "arms": out}


# --------------------------------------------------------------------------- #
# stage 5: the gates, traced to their estimands                               #
# --------------------------------------------------------------------------- #
def gate_estimands() -> dict[str, Any]:
    """R1 and R2 against a directly evaluated index-space width criterion.

    R1 is a condition on the transient COUNT, so it governs any estimator built
    from those counts, dbeta included; the reason is the shared sample, not a
    map between metrics. R2 is a condition on the width of the interval on B and
    has no image in index space. The replacement is R2beta, a ceiling on the
    directly evaluated paired-bootstrap interval on dbeta, derived from R2's own
    stated rule.
    """
    path = DECISIONS / "rq1-beta-reexpression.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for family in ("design_anchors",):
        for key, entry in record[family].items():
            ci = entry.get("delta_beta_ci")
            width = (
                ci[1] - ci[0]
                if ci and all(np.isfinite(v) for v in ci)
                else float("nan")
            )
            rows.append(
                {
                    "family": family,
                    "key": key,
                    "section": entry.get("section"),
                    "level_m_msl": entry.get("level_m_msl"),
                    "n_samples": entry.get("n_samples"),
                    "k_transient": entry.get("k_transient"),
                    "R1_rows": bool(entry.get("R1_rows")),
                    "B_width_factor": entry.get("B_width_factor"),
                    "R2_width": bool(entry.get("R2_width")),
                    "resolved_ratio_space": bool(entry.get("resolved")),
                    "delta_beta": entry.get("delta_beta"),
                    "delta_beta_ci": ci,
                    "delta_beta_ci_source": entry.get("delta_beta_ci_source"),
                    "delta_beta_ci_width": width,
                    "R2_beta_width": bool(
                        np.isfinite(width) and width <= R2_BETA_MAX_WIDTH
                    ),
                    "resolved_index_space": bool(
                        entry.get("R1_rows")
                        and np.isfinite(width)
                        and width <= R2_BETA_MAX_WIDTH
                    ),
                    "delta_beta_lower_bound": entry.get("delta_beta_lower_bound"),
                }
            )
    # Whole-grid sweep of the two large-sample sections, so the confusion
    # between the two verdicts is counted rather than sampled at four anchors.
    grid_rows = []
    for family in ("grids", "grids_n100000"):
        for key, entries in record.get(family, {}).items():
            for entry in entries:
                ci = entry.get("delta_beta_ci")
                width = (
                    ci[1] - ci[0]
                    if ci and all(np.isfinite(v) for v in ci)
                    else float("nan")
                )
                grid_rows.append(
                    {
                        "family": family,
                        "key": key,
                        "level_m_msl": entry.get("level_m_msl"),
                        "k_transient": entry.get("k_transient"),
                        "R1_rows": bool(entry.get("R1_rows")),
                        "R2_width": bool(entry.get("R2_width")),
                        "resolved_ratio_space": bool(entry.get("resolved")),
                        "delta_beta_ci_width": width,
                        "R2_beta_width": bool(
                            np.isfinite(width) and width <= R2_BETA_MAX_WIDTH
                        ),
                        "resolved_index_space": bool(
                            entry.get("R1_rows")
                            and np.isfinite(width)
                            and width <= R2_BETA_MAX_WIDTH
                        ),
                    }
                )
    confusion = {
        "both_resolved": sum(
            1
            for r in grid_rows
            if r["resolved_ratio_space"] and r["resolved_index_space"]
        ),
        "ratio_only": sum(
            1
            for r in grid_rows
            if r["resolved_ratio_space"] and not r["resolved_index_space"]
        ),
        "index_only": sum(
            1
            for r in grid_rows
            if r["resolved_index_space"] and not r["resolved_ratio_space"]
        ),
        "neither": sum(
            1
            for r in grid_rows
            if not r["resolved_ratio_space"] and not r["resolved_index_space"]
        ),
        "n_levels": len(grid_rows),
    }
    confusion["ratio_only_levels"] = [
        {
            "key": r["key"],
            "family": r["family"],
            "level_m_msl": r["level_m_msl"],
            "k_transient": r["k_transient"],
            "B_width_passes": r["R2_width"],
            "delta_beta_ci_width": r["delta_beta_ci_width"],
        }
        for r in grid_rows
        if r["resolved_ratio_space"] and not r["resolved_index_space"]
    ]
    confusion["index_space_is_never_more_permissive"] = confusion["index_only"] == 0
    return {
        "source": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "R1": {
            "estimand": "the transient failure COUNT at the level",
            "threshold": R1_MIN_ROWS,
            "transfers_to_delta_beta": True,
            "reason": (
                "both estimators are functions of the same two counts on the "
                "same rows, so a count floor governs both; this is the shared "
                "sample, not a map between metrics"
            ),
        },
        "R2": {
            "estimand": "the multiplicative width of the 95 per cent interval on B",
            "threshold": R2_MAX_WIDTH_FACTOR,
            "transfers_to_delta_beta": False,
            "reason": (
                "a width condition on a ratio has no image in index space; "
                "see metric_relationship.R2_width_does_not_transfer"
            ),
        },
        "R2_beta": {
            "estimand": (
                "the additive width of the directly evaluated 95 per cent "
                "paired-bootstrap interval on delta beta"
            ),
            "threshold": R2_BETA_MAX_WIDTH,
            "derivation": R2_BETA_DERIVATION,
        },
        "anchors": rows,
        "grid_confusion": confusion,
        "grid_levels": grid_rows,
    }


# --------------------------------------------------------------------------- #
# main                                                                        #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_N)
    args = parser.parse_args(argv)

    started = time.perf_counter()
    record: dict[str, Any] = {
        "study": (
            "Metric relationship and comparator-ladder order"
            " (audit F3, M01, M02, M03)"
        ),
        "generated_by": "scripts/metric_decomposition_study.py",
        "bootstrap": {"n": args.bootstrap, "confidence": CONFIDENCE},
        "criteria": {
            "R1_min_transient_rows": R1_MIN_ROWS,
            "R2_max_B_ci_width_factor": R2_MAX_WIDTH_FACTOR,
            "R2_beta_max_ci_width": R2_BETA_MAX_WIDTH,
            "R2_beta_derivation": R2_BETA_DERIVATION,
        },
    }
    print("stage 1: metric relationship")
    record["metric_relationship"] = metric_relationship()
    print("stage 2: ladder orders")
    record["ladder_orders"] = ladder_orders(args.bootstrap)
    print("stage 3: shared-sample variance")
    record["shared_sample_variance"] = shared_sample_variance(args.bootstrap)
    print("stage 4: cancellation in both metrics")
    record["cancellation_paired"] = cancellation_both_metrics(args.bootstrap)
    record["cancellation_points"] = cancellation_point_estimates()
    print("stage 5: gate estimands")
    record["gate_estimands"] = gate_estimands()
    record["elapsed_s"] = round(time.perf_counter() - started, 1)

    RECORD_JSON.write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8"
    )
    print(f"wrote {RECORD_JSON.relative_to(REPO_ROOT)}  ({record['elapsed_s']} s)")

    # Console summary of the four findings.
    mr = record["metric_relationship"]
    print()
    print(
        f"  B alone: one B = {mr['constant_B_family']['B']:.3f} spans dbeta "
        f"{mr['constant_B_family']['delta_beta_min']:.3f} to "
        f"{mr['constant_B_family']['delta_beta_max']:.3f}"
    )
    print(
        "  restricted monotonicity holds: "
        f"{mr['restricted_monotonicity']['all_slopes_positive']}"
    )
    for key, block in record["ladder_orders"].items():
        for lv in block["levels"]:
            if abs(lv["level_m_msl"] - block["design_hwl_m_msl"]) < 1e-9:
                print(
                    f"  {block['section']} {lv['level_m_msl']:.2f} m: total "
                    f"{lv['total_delta_beta']:.4f}; head share A "
                    f"{lv['head_share_A']:.3f} vs B {lv['head_share_B']:.3f}; "
                    f"interaction {lv['interaction_head']:+.4f} "
                    f"{lv['interaction_head_ci']}"
                )
    ge = record["gate_estimands"]
    print(
        f"  gate confusion over {ge['grid_confusion']['n_levels']} grid levels: "
        f"{ge['grid_confusion']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
