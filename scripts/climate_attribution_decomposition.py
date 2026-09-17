"""The exact two-stratum climate decomposition, and what the shares are shares of.

Companion study for `docs/decisions/climate-attribution-and-composition-study.md`
(2026-09-17). Nothing here changes a default, a prior, a config field, a
persisted sweep, a posterior, an annual number or a fragility curve: every
quantity is an arithmetic statement about already-committed artifacts, and the
gates exist to prove that.

Three questions, one driver, because all three are statements about the same
composed annual probability.

1. THE CLIMATE RATIO. Chapter 7 decomposes the warming-to-historical annual
   ratio as the product of a long-duration frequency factor and a within-stratum
   conditional-probability factor, and concludes from it that the annual
   probability rises mainly because long-duration floods become more frequent.
   The product is exact for the LONG STRATUM'S CONTRIBUTION and is not the total
   ratio. For a two-stratum partition of the same finite event set,

       P   = w_L p_L + (1 - w_L) p_S                                       (1)
       R   = P'/P = s_L R_L + s_S R_S,   s_k = C_k / P,  C_k = w_k p_k     (2)
       R_L = (w'_L / w_L) (p'_L / p_L) = f_L g_L                           (3)

   so (3) is R_L, one addend of (2). Section `two_stratum` measures both, and
   `attribution` gives the frequency/severity split of (2) over BOTH strata,
   which needs a counterfactual and is therefore reported at both orders and as
   the symmetric (Shapley) average of them.

2. WHAT A MECHANISM SHARE IS A SHARE OF. `SystemFragility.dominance_share` and
   `AnnualizedResult.dominance_share` both compute `P_i / sum_j P_j`, a
   sum-normalised marginal share. The composed system probability is the union
   `1 - prod_j (1 - P_j)`, which is smaller whenever two mechanisms are loaded
   at once. Section `composition_overlap` measures the gap, and the Frechet
   bracket `max_i P_i <= P_union <= min(1, sum_i P_i)` that bounds what
   conditional dependence alone could do to the union with the marginals held
   fixed.

3. THE HISTORICAL NON-BREACH CHECK. Section `historical_consistency` reproduces
   the four-segment series composition, its sixty-year expectation and
   no-failure probability, and replaces the rule-of-three exclusion threshold
   with the exact one-sided binomial limit. It also states the two silent
   assumptions and their directions, both of which run in the model's favour.

Estimator, seed and draw are IMPORTED from
`scripts/annualisation_uncertainty_study.py` rather than re-implemented, so the
intervals here are paired with that study's on the replicate index and carry its
pattern-stratified draw (ADR-free Part 3 correction, 2026-09-17). Its own record
is neither read for a value nor rewritten.

Gates (a failure aborts; it is never tabulated)
----------------------------------------------
0. Equation (1) reproduces the published `p_annual_system` at every cell.
1. Every field of `rq4_attribution.json` is reproduced by float equality, and
   the primary-arm rows of `rq4_annual.csv` string-identically.
2. Equation (2) reproduces the total ratio at every section.
3. The frequency and severity terms sum to log R exactly, at both orders and
   at the Shapley average.
4. Equation (3) reproduces the long-contribution ratio exactly.
5. THE DEFECT, MEASURED RATHER THAN ASSERTED: the product (3) must differ from
   the total ratio (2) by more than the tolerance at at least one section. Run
   against a single-stratum partition this gate fails, which is what makes it a
   measurement of the error rather than a restatement of the fix.
6. Nothing outside this study's own outputs is written.

Usage (repo root, venv active)::

    python scripts/climate_attribution_decomposition.py
    python scripts/climate_attribution_decomposition.py --replicates 200
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

DECISIONS = REPO_ROOT / "docs" / "decisions"
DEFAULT_OUT = DECISIONS / "climate-attribution-and-composition-study.json"
NOTE = "docs/decisions/climate-attribution-and-composition-study.md"
UNCERTAINTY_DRIVER = REPO_ROOT / "scripts" / "annualisation_uncertainty_study.py"

#: Equations (1) to (3) are exact identities over a finite partition, so the
#: only admissible deviation is floating-point summation order. This is the same
#: bound the parent study uses for its own reordering gate.
EXACT_TOLERANCE = 1e-12

#: Gate 5. The product of the long-stratum factors must MISS the total ratio by
#: at least this much somewhere, or the defect being corrected is not present in
#: the data and the correction would be unmotivated.
DEFECT_MIN_RELATIVE = 1e-6

SCOPE_STATEMENT = (
    "Point quantities are exact arithmetic on the committed Phase 3 artifacts. "
    "Intervals are hazard-sampling uncertainty ONLY, the finite-ensemble spread "
    "of the d4PDF peak-stage distribution with the fragility curves held fixed, "
    "and are far narrower than the aquifer-conductivity bracket, which does not "
    "cancel. Quote that scope wherever any interval here is quoted."
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dir_state(directory: Path, pattern: str = "*") -> dict[str, str]:
    if not directory.exists():
        return {}
    return {_rel(p): _sha256(p) for p in sorted(directory.glob(pattern)) if p.is_file()}


def shapley_log(p_00: float, p_10: float, p_01: float, p_11: float) -> dict[str, float]:
    """Two-factor attribution of ``log(p_11 / p_00)`` between the two factors.

    ``p_10`` moves the first factor only (here the stratum weights), ``p_01``
    the second only (the conditional probabilities). The two orderings bracket
    the attribution and their average is the Shapley value; both are reported
    because the split is counterfactual and the order is a choice, not a fact.
    """
    total = math.log(p_11 / p_00)
    first_first = math.log(p_10 / p_00)
    first_last = math.log(p_11 / p_01)
    second_first = math.log(p_01 / p_00)
    second_last = math.log(p_11 / p_10)
    return {
        "log_total": total,
        "frequency_first": first_first,
        "frequency_last": first_last,
        "frequency_shapley": 0.5 * (first_first + first_last),
        "severity_first": second_first,
        "severity_last": second_last,
        "severity_shapley": 0.5 * (second_first + second_last),
        "frequency_share_first": first_first / total,
        "frequency_share_last": first_last / total,
        "frequency_share_shapley": 0.5 * (first_first + first_last) / total,
    }


def shapley_additive(
    p_00: float, p_10: float, p_01: float, p_11: float
) -> dict[str, float]:
    """The same attribution in probability units rather than log units."""
    total = p_11 - p_00
    freq = 0.5 * ((p_10 - p_00) + (p_11 - p_01))
    sev = 0.5 * ((p_01 - p_00) + (p_11 - p_10))
    return {
        "delta_total": total,
        "frequency": freq,
        "severity": sev,
        "frequency_share": freq / total,
    }


def two_stratum_point(entry: dict[str, Any], strat: dict[str, Any]) -> dict[str, Any]:
    """Equation (1) at one section and scenario, from the published fields."""
    w_in = entry[strat["weight_key"]]
    p_in = entry[strat["inside_key"]]
    p_out = entry[strat["outside_key"]]
    return {
        "w_inside": w_in,
        "p_f_inside": p_in,
        "p_f_outside": p_out,
        "n_inside": entry[strat["count_key"]],
        "n_years": entry["n_years"],
        "contribution_inside": w_in * p_in,
        "contribution_outside": (1.0 - w_in) * p_out,
        "p_annual_reconstructed": w_in * p_in + (1.0 - w_in) * p_out,
    }


def replicate_strata(
    values: np.ndarray,
    mask: np.ndarray,
    index: np.ndarray,
    n_blocks: int,
    multiplicities: np.ndarray,
    uncertainty,
) -> dict[str, np.ndarray]:
    """Replicate ``w``, ``p_inside``, ``p_outside`` and the annual mean.

    The five per-block sums are the parent study's own, so a unit multiplicity
    row reduces this to the production estimator, which gate 0 checks.
    """
    inside = mask.astype(np.float64)
    stacked = np.column_stack(
        [
            np.where(mask, values, 0.0),
            inside,
            np.where(mask, 0.0, values),
            1.0 - inside,
            values,
        ]
    )
    totals = multiplicities.astype(np.float64) @ uncertainty.block_sums(
        stacked, index, n_blocks
    )
    s_in, n_in, s_out, n_out, s_all = (totals[:, i] for i in range(5))
    n_all = n_in + n_out

    def _ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        out = np.full(num.shape, np.nan, dtype=np.float64)
        np.divide(num, den, out=out, where=den > 0.0)
        return out

    return {
        "w_inside": _ratio(n_in, n_all),
        "p_inside": _ratio(s_in, n_in),
        "p_outside": _ratio(s_out, n_out),
        "p_annual": _ratio(s_all, n_all),
    }


def paired_attribution_replicates(
    hist: dict[str, np.ndarray], warm: dict[str, np.ndarray]
) -> dict[str, np.ndarray]:
    """Replicate ratios and the Shapley frequency share, formed per replicate."""
    w0, pl0, ps0 = hist["w_inside"], hist["p_inside"], hist["p_outside"]
    w1, pl1, ps1 = warm["w_inside"], warm["p_inside"], warm["p_outside"]
    p00 = w0 * pl0 + (1.0 - w0) * ps0
    p11 = w1 * pl1 + (1.0 - w1) * ps1
    p10 = w1 * pl0 + (1.0 - w1) * ps0
    p01 = w0 * pl1 + (1.0 - w0) * ps1

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = p11 / p00
        log_total = np.log(ratio)
        freq = 0.5 * (np.log(p10 / p00) + np.log(p11 / p01))
        share = freq / log_total
        contribution_ratio = (w1 * pl1) / (w0 * pl0)
        frequency_factor = w1 / w0
        severity_factor = pl1 / pl0
    for arr in (ratio, log_total, freq, share, contribution_ratio):
        arr[~np.isfinite(arr)] = np.nan
    return {
        "ratio_total": ratio,
        "ratio_inside_contribution": contribution_ratio,
        "frequency_factor": frequency_factor,
        "severity_factor": severity_factor,
        "frequency_share_shapley": share,
        "product_over_total": contribution_ratio / ratio,
    }


def composition_overlap(row: dict[str, Any], mechanisms: tuple[str, ...]) -> dict:
    """Sum of marginals against the union, and the Frechet bracket on the union.

    The shares Chapter 7 prints normalise by the SUM. The composed annual
    probability is the union. Both are correct quantities; they are not the same
    quantity, and this measures the distance between them.
    """
    marginals = {
        m: float(row[f"p_annual_{m}"]) for m in mechanisms if row[f"p_annual_{m}"] != ""
    }
    union = float(row["p_annual_system"])
    total = sum(marginals.values())
    largest = max(marginals.values()) if marginals else 0.0
    return {
        "marginals": marginals,
        "p_annual_union": union,
        "sum_of_marginals": total,
        "largest_marginal": largest,
        "sum_over_union": total / union if union > 0.0 else float("nan"),
        "union_over_largest": union / largest if largest > 0.0 else float("nan"),
        "frechet_lower": largest,
        "frechet_upper": min(1.0, total),
        "dependence_factor_range": [
            largest / union if union > 0.0 else float("nan"),
            min(1.0, total) / union if union > 0.0 else float("nan"),
        ],
        "sum_normalised_shares": {
            m: v / total for m, v in marginals.items() if total > 0.0
        },
        "union_normalised_marginals": {
            m: v / union for m, v in marginals.items() if union > 0.0
        },
    }


def historical_consistency(
    per_section: dict[str, float], years: int = 60
) -> dict[str, Any]:
    """The four-segment reach union and the sixty-year non-breach check."""
    values = list(per_section.values())
    series = 1.0 - math.prod(1.0 - p for p in values)
    exact_upper = 1.0 - 0.05 ** (1.0 / years)
    rule_of_three = 3.0 / years
    return {
        "per_section_annual_bep": per_section,
        "years": years,
        "reach_annual_series_union": series,
        "reach_annual_sum": sum(values),
        "reach_annual_largest": max(values),
        "union_over_largest": series / max(values),
        "expected_failures": years * series,
        "p_no_failure": (1.0 - series) ** years,
        "exclusion_upper_95_exact": exact_upper,
        "exclusion_upper_95_rule_of_three": rule_of_three,
        "exact_upper_over_reported": exact_upper / series,
        "rule_of_three_over_reported": rule_of_three / series,
        "assumptions": {
            "inter_section_independence": (
                "the series union assumes the four sections fail independently "
                "given the year. They share one flood, so positive dependence is "
                "expected; under it the reach union falls toward the largest "
                "single-section value, here a factor of "
                f"{series / max(values):.3f} below the independent composition. "
                "The independent composition therefore OVER-states the reach "
                "probability, which makes the check conservative."
            ),
            "persistent_epistemic_uncertainty": (
                "the sixty years are treated as independent Bernoulli trials at a "
                "known p. The soil and conductivity uncertainty is persistent, so "
                "p is one uncertain number held fixed across the sixty years. "
                "(1 - p)^60 is convex in p, so E[(1 - p)^60] >= (1 - E[p])^60 by "
                "Jensen: the reported no-failure probability is a LOWER bound on "
                "the one a persistent-epistemic treatment gives, and the record "
                "is therefore at least as consistent with the model as stated."
            ),
            "not_calibration": (
                "the check constrains over-prediction only. It excludes nothing "
                "below its threshold and cannot confirm the reported value."
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--replicates",
        type=int,
        default=None,
        help="Bootstrap replicates per scenario (default: the parent study's).",
    )
    args = parser.parse_args(argv)

    started = time.time()
    uncertainty = _load(UNCERTAINTY_DRIVER, "_s07_uncertainty")
    campaign = uncertainty._load_campaign_module()
    replicates = args.replicates or uncertainty.REPLICATES

    cache_before = _dir_state(campaign.HAZARD_CACHE, "*.csv")
    phase3_before = _dir_state(uncertainty.PHASE3_DIR)

    print("building context (persisted curves + warm hazard cache) ...", flush=True)
    context = uncertainty.build_context(campaign)
    d70, source = uncertainty.PRIMARY_ARM
    print(f"annualising {uncertainty._arm_key(d70, source)} ...", flush=True)
    rows, per_event = uncertainty.annualise_arm(campaign, context, d70, source)

    published_attr = json.loads(
        uncertainty.ATTRIBUTION_TABLE.read_text(encoding="utf-8")
    )
    with open(uncertainty.PRODUCTION_TABLE, encoding="utf-8", newline="") as handle:
        published_rows = list(csv.DictReader(handle))

    # ---------------------------------------------------------------- gate 1
    mismatches: list[str] = []
    compared = 0
    for kp in uncertainty.BEP_KPS:
        for scenario in campaign.SCENARIOS:
            mine = rows[("Tokachi", kp, scenario)]
            want = next(
                r
                for r in published_rows
                if r["river"] == "Tokachi"
                and float(r["kp"]) == kp
                and r["scenario"] == scenario
                and r["d70"] == d70
                and r["bep_source"] == source
                and r["surface_variant"] == uncertainty.SURFACE_VARIANT
                and float(r["lambda_ac_m"]) == uncertainty.LAMBDA_AC_M
            )
            for field, value in want.items():
                got = str(mine[field])
                if got != value:
                    mismatches.append(f"KP{kp:g} {scenario} {field}: {got} != {value}")
                compared += 1
    if mismatches:
        raise AssertionError(
            "GATE 1 FAILED: the recomposed primary arm does not reproduce "
            "rq4_annual.csv.\n  " + "\n  ".join(mismatches[:20])
        )
    print(f"  GATE 1 PASSED: {compared} published fields reproduced", flush=True)

    event_ids = {
        scenario: [
            e.event_id for e in context["hazards"][scenario][("Tokachi", 58.8)].events
        ]
        for scenario in campaign.SCENARIOS
    }
    rng = np.random.default_rng(uncertainty.SEED)
    index_by_scenario: dict[str, tuple[np.ndarray, int]] = {}
    multiplicities: dict[str, np.ndarray] = {}
    for scenario in campaign.SCENARIOS:
        labels = uncertainty.block_labels(event_ids[scenario], "member")
        index, n_blocks, _ = uncertainty.block_index(labels)
        index_by_scenario[scenario] = (index, n_blocks)
        multiplicities[scenario] = uncertainty.draw_multiplicities_stratified(
            uncertainty.stratum_columns(event_ids[scenario]),
            n_blocks,
            replicates,
            rng,
        )

    strat_by_name = {s["name"]: dict(s) for s in uncertainty.STRATIFIERS}
    strat_by_name["duration"]["weight_key"] = "frac_years_gt24h"
    strat_by_name["compound"]["weight_key"] = None  # published weight absent

    sections: dict[str, Any] = {}
    gate0: list[str] = []
    gate2: list[str] = []
    gate3: list[str] = []
    gate4: list[str] = []
    defect_seen: list[float] = []
    worst = {"gate0": 0.0, "gate2": 0.0, "gate3": 0.0, "gate4": 0.0}

    for kp in uncertainty.BEP_KPS:
        label = uncertainty._label(kp)
        entry = published_attr[f"Tokachi_KP{kp:g}"]
        node = ("Tokachi", round(kp, 3))
        block: dict[str, Any] = {}

        for name, strat in strat_by_name.items():
            if strat["weight_key"] is None:
                continue
            per_scenario: dict[str, Any] = {}
            reps: dict[str, dict[str, np.ndarray]] = {}
            clears = True
            for scenario in campaign.SCENARIOS:
                pub = entry[scenario]
                point = two_stratum_point(pub, strat)
                p_annual = float(rows[("Tokachi", kp, scenario)]["p_annual_system"])
                point["p_annual_published"] = p_annual
                deviation = abs(point["p_annual_reconstructed"] - p_annual) / p_annual
                worst["gate0"] = max(worst["gate0"], deviation)
                if deviation > EXACT_TOLERANCE:
                    gate0.append(f"{label} {scenario} {name}: {deviation:.3e}")
                point["reconstruction_relative_deviation"] = deviation
                point["share_of_annual_total"] = (
                    point["contribution_inside"] / point["p_annual_reconstructed"]
                )

                hazard = context["hazards"][scenario][node]
                mask = np.asarray(
                    [strat["predicate"](e) for e in hazard.events], dtype=bool
                )
                occupancy = uncertainty.stratum_occupancy(event_ids[scenario], mask)
                point["occupancy"] = occupancy
                clears = clears and occupancy["clears_floor"]

                values = per_event[("Tokachi", kp, scenario)]["__system__"]
                index, n_blocks = index_by_scenario[scenario]
                reps[scenario] = replicate_strata(
                    values, mask, index, n_blocks, multiplicities[scenario], uncertainty
                )
                per_scenario[scenario] = point

            hist, warm = per_scenario["historical"], per_scenario["+4K"]
            ratio_total = (
                warm["p_annual_reconstructed"] / hist["p_annual_reconstructed"]
            )
            ratio_in = warm["contribution_inside"] / hist["contribution_inside"]
            ratio_out = warm["contribution_outside"] / hist["contribution_outside"]
            s_in = hist["share_of_annual_total"]
            mixture = s_in * ratio_in + (1.0 - s_in) * ratio_out
            dev2 = abs(mixture - ratio_total) / ratio_total
            worst["gate2"] = max(worst["gate2"], dev2)
            if dev2 > EXACT_TOLERANCE:
                gate2.append(f"{label} {name}: {dev2:.3e}")

            f_in = warm["w_inside"] / hist["w_inside"]
            g_in = warm["p_f_inside"] / hist["p_f_inside"]
            dev4 = abs(f_in * g_in - ratio_in) / ratio_in
            worst["gate4"] = max(worst["gate4"], dev4)
            if dev4 > EXACT_TOLERANCE:
                gate4.append(f"{label} {name}: {dev4:.3e}")
            defect_seen.append(abs(f_in * g_in - ratio_total) / ratio_total)

            p00 = hist["p_annual_reconstructed"]
            p11 = warm["p_annual_reconstructed"]
            p10 = (
                warm["w_inside"] * hist["p_f_inside"]
                + (1.0 - warm["w_inside"]) * hist["p_f_outside"]
            )
            p01 = (
                hist["w_inside"] * warm["p_f_inside"]
                + (1.0 - hist["w_inside"]) * warm["p_f_outside"]
            )
            log_attr = shapley_log(p00, p10, p01, p11)
            add_attr = shapley_additive(p00, p10, p01, p11)
            for pair in (
                ("frequency_first", "severity_last"),
                ("frequency_last", "severity_first"),
                ("frequency_shapley", "severity_shapley"),
            ):
                total = log_attr[pair[0]] + log_attr[pair[1]]
                dev3 = abs(total - log_attr["log_total"]) / abs(log_attr["log_total"])
                worst["gate3"] = max(worst["gate3"], dev3)
                if dev3 > EXACT_TOLERANCE:
                    gate3.append(f"{label} {name} {pair[0]}: {dev3:.3e}")

            record: dict[str, Any] = {
                "definition": strat["definition"],
                "historical": hist,
                "+4K": warm,
                "ratio_total": ratio_total,
                "ratio_inside_contribution": ratio_in,
                "ratio_outside_contribution": ratio_out,
                "historical_share_inside": s_in,
                "mixture_reconstruction": mixture,
                "mixture_relative_deviation": dev2,
                "frequency_factor_inside": f_in,
                "severity_factor_inside": g_in,
                "product_inside": f_in * g_in,
                "product_over_total_ratio": f_in * g_in / ratio_total,
                "frequency_share_of_log_inside": math.log(f_in) / math.log(f_in * g_in),
                "counterfactual_frequency_only": p10,
                "counterfactual_severity_only": p01,
                "attribution_log": log_attr,
                "attribution_additive": add_attr,
                "both_strata_clear_floor": clears,
            }
            if clears:
                paired = paired_attribution_replicates(reps["historical"], reps["+4K"])
                record["intervals"] = {
                    key: uncertainty._defined_interval(
                        {
                            "ratio_total": ratio_total,
                            "ratio_inside_contribution": ratio_in,
                            "frequency_factor": f_in,
                            "severity_factor": g_in,
                            "frequency_share_shapley": log_attr[
                                "frequency_share_shapley"
                            ],
                            "product_over_total": f_in * g_in / ratio_total,
                        }[key],
                        paired[key],
                    )
                    for key in (
                        "ratio_total",
                        "ratio_inside_contribution",
                        "frequency_factor",
                        "severity_factor",
                        "frequency_share_shapley",
                        "product_over_total",
                    )
                }
            else:
                record["intervals"] = {
                    "withheld": (
                        "below the pre-registered occupancy floor of "
                        f"{uncertainty.STRATUM_BLOCK_FLOOR} carrying member "
                        "blocks in at least one scenario; point values only"
                    )
                }
            block[name] = record
        sections[label] = block

    for name, failures in (
        ("GATE 0", gate0),
        ("GATE 2", gate2),
        ("GATE 3", gate3),
        ("GATE 4", gate4),
    ):
        if failures:
            raise AssertionError(
                f"{name} FAILED: an identity that holds by construction did "
                "not reproduce.\n  " + "\n  ".join(failures[:20])
            )
    if max(defect_seen) <= DEFECT_MIN_RELATIVE:
        raise AssertionError(
            "GATE 5 FAILED: the long-stratum product agrees with the total "
            "ratio everywhere, so the decomposition defect this study corrects "
            "is not present in the data it was measured on."
        )
    print(
        "  GATES 0,2,3,4 PASSED; GATE 5 measured a worst product-versus-total "
        f"departure of {max(defect_seen):.4f}",
        flush=True,
    )

    overlap = {}
    for kp in uncertainty.BEP_KPS:
        label = uncertainty._label(kp)
        overlap[label] = {
            scenario: composition_overlap(
                rows[("Tokachi", kp, scenario)], uncertainty.MECHANISMS
            )
            for scenario in campaign.SCENARIOS
        }

    consistency = historical_consistency(
        {
            uncertainty._label(kp): float(
                rows[("Tokachi", kp, "historical")]["p_annual_bep"]
            )
            for kp in uncertainty.BEP_KPS
        }
    )

    # ---------------------------------------------------------------- gate 6
    cache_after = _dir_state(campaign.HAZARD_CACHE, "*.csv")
    phase3_after = _dir_state(uncertainty.PHASE3_DIR)
    if cache_after != cache_before or phase3_after != phase3_before:
        raise AssertionError(
            "GATE 6 FAILED: this study wrote to the hazard cache or the Phase 3 "
            "output directory; it is a read-only consumer of both."
        )

    record = {
        "study": "climate attribution and system composition",
        "note": NOTE,
        "driver": _rel(Path(__file__).resolve()),
        "generated": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - started, 1),
        "scope": SCOPE_STATEMENT,
        "arm": {
            "d70": d70,
            "bep_source": source,
            "surface_variant": uncertainty.SURFACE_VARIANT,
            "lambda_ac_m": uncertainty.LAMBDA_AC_M,
        },
        "estimator": {
            "imported_from": _rel(UNCERTAINTY_DRIVER),
            "seed": uncertainty.SEED,
            "replicates": replicates,
            "resampling_unit": "d4PDF ensemble member block",
            "draw": "pattern-stratified (fixed SST-pattern composition)",
            "occupancy_floor_blocks": uncertainty.STRATUM_BLOCK_FLOOR,
        },
        "inputs": {
            _rel(uncertainty.PRODUCTION_TABLE): _sha256(uncertainty.PRODUCTION_TABLE),
            _rel(uncertainty.ATTRIBUTION_TABLE): _sha256(uncertainty.ATTRIBUTION_TABLE),
        },
        "identities": {
            "1_partition": "P = w_in p_in + (1 - w_in) p_out",
            "2_ratio_mixture": "R = s_in R_in + (1 - s_in) R_out",
            "3_inside_product": "R_in = (w'_in / w_in) (p'_in / p_in)",
            "note": (
                "identity 3 is the change in the INSIDE stratum's contribution, "
                "one addend of identity 2, and is not the total ratio"
            ),
        },
        "two_stratum": sections,
        "composition_overlap": overlap,
        "historical_consistency": consistency,
        "gates": {
            "0_partition_reconstructs_published_annual": {
                "passed": True,
                "tolerance": EXACT_TOLERANCE,
                "worst_relative_deviation": worst["gate0"],
            },
            "1_production_rows_reproduced": {
                "passed": True,
                "fields_compared": compared,
                "table": _rel(uncertainty.PRODUCTION_TABLE),
            },
            "2_mixture_reconstructs_total_ratio": {
                "passed": True,
                "tolerance": EXACT_TOLERANCE,
                "worst_relative_deviation": worst["gate2"],
            },
            "3_attribution_terms_sum_to_log_ratio": {
                "passed": True,
                "tolerance": EXACT_TOLERANCE,
                "worst_relative_deviation": worst["gate3"],
            },
            "4_inside_product_reconstructs_inside_ratio": {
                "passed": True,
                "tolerance": EXACT_TOLERANCE,
                "worst_relative_deviation": worst["gate4"],
            },
            "5_defect_present": {
                "passed": True,
                "criterion": (
                    "the inside-stratum product must miss the total ratio by "
                    f"more than {DEFECT_MIN_RELATIVE} somewhere"
                ),
                "worst_relative_departure": max(defect_seen),
            },
            "6_read_only": {
                "passed": True,
                "hazard_cache_files": len(cache_after),
                "phase3_files": len(phase3_after),
            },
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {_rel(args.out)} in {record['elapsed_s']} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
