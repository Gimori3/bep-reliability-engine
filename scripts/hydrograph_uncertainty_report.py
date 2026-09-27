"""Assemble the Green Light 5 record from locally cached companion runs.

Recheck surface inputs and resummarize paired event subsampling; this also
keeps historical and warming numerical resampling streams independent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import hydrograph_uncertainty_study as study  # noqa: E402
from criterion_consequence_study import ATTAINABLE_MAX  # noqa: E402

from system_integration.surface_curves import load_surface_curves  # noqa: E402
from system_integration.uemura_models import (  # noqa: E402
    SCOUR_K_CONVERSION_USACE,
    draw_scour,
    load_segment_inputs,
    scour_failure_fraction,
)

KEYS = ("system", "piping", "overflow", "scour", "share")
CASES = [(kp, False) for kp in study.KPS] + [(58.8, True), (60.0, True)]


def shape_record(data_repo: Path, kp: float, berm: bool) -> dict:
    """Rebuild all statistics from event marginals, checking the scour convention."""
    path = study.OUT / f"shapes_{kp}_{berm}_9.json"
    d = json.loads(path.read_text())
    seg = load_segment_inputs(
        REPO / "data/processed/uemura_segments/segment_inputs.csv"
    )[("Tokachi", kp)]
    sc = draw_scour(
        np.random.default_rng(study.SEED + 1),
        10000,
        k_conversion=SCOUR_K_CONVERSION_USACE,
    )
    pop2 = study.population(data_repo, kp, berm, d["n"] * 2)
    assert pop2["input_sha256"] == d["input_sha256"], "stale shape population"
    boots = {}
    for scenario in ("historical", "plus4K"):
        recs, can, _, _ = study.records(data_repo, kp, scenario)
        rows = {row["event"]: row for row in d[scenario]["events"]}
        for name, row in rows.items():
            actual = recs[name]
            assert actual.peak == row["peak"], "changed event or local rating"
            pinned = study.conditioning_record_for_level(
                can, actual.peak, scenario=scenario
            )
            for j, rec in enumerate((pinned, actual)):
                row["probabilities"][j][2] = scour_failure_fraction(
                    rec.h, rec.native_dt, seg, sc
                )
        groups = d[scenario]["selection"]
        arrays = [
            np.array([rows[name]["probabilities"] for name in g["events"]])
            for g in groups
        ]
        boot = study.bootstrap_events(
            groups, arrays, study.SEED + 2 + (scenario == "plus4K")
        )
        boots[scenario] = boot
        d[scenario]["estimates"] = {
            arm: study.weighted_summary(groups, [a[:, j] for a in arrays])
            for j, arm in enumerate(("canonical", "actual"))
        }
        d[scenario]["intervals"] = {
            arm: {
                key: np.percentile(boot[:, j, k], [2.5, 97.5]).tolist()
                for k, key in enumerate(KEYS)
            }
            for j, arm in enumerate(("canonical", "actual"))
        }
        d[scenario]["displacement_ci"] = {
            key: np.percentile(boot[:, 1, k] - boot[:, 0, k], [2.5, 97.5]).tolist()
            for k, key in enumerate(KEYS)
        }
        d[scenario]["system_factor_ci"] = np.percentile(
            boot[:, 1, 0] / boot[:, 0, 0], [2.5, 97.5]
        ).tolist()
        # Check the largest weighted piping contribution, not just largest p.
        event_weight = {
            name: g["weight"] / len(g["events"]) for g in groups for name in g["events"]
        }
        checks = []
        for j, arm in enumerate(("canonical", "actual")):
            name = max(
                rows,
                key=lambda name: rows[name]["probabilities"][j][0] * event_weight[name],
            )
            rec = recs[name]
            if j == 0:
                rec = study.conditioning_record_for_level(
                    can, rec.peak, scenario=scenario
                )
            _, tr = study.evaluate(pop2, rec)
            small = rows[name]["probabilities"][j][0]
            checks.append(
                dict(
                    arm=arm,
                    event=name,
                    p_n=small,
                    p_2n=float(tr.mean()),
                    relative_change=float(tr.mean() / small - 1) if small else None,
                )
            )
        d[scenario]["n_checks"] = checks
        d[scenario]["sampled_events"] = sum(len(g["events"]) for g in groups)
    ratios = boots["plus4K"][:, :, 0] / boots["historical"][:, :, 0]
    d["climate_ratio"] = {
        arm: dict(
            point=d["plus4K"]["estimates"][arm]["system"]
            / d["historical"]["estimates"][arm]["system"],
            interval=np.percentile(ratios[:, j], [2.5, 97.5]).tolist(),
        )
        for j, arm in enumerate(("canonical", "actual"))
    }
    d["climate_ratio_displacement_ci"] = np.percentile(
        ratios[:, 1] - ratios[:, 0], [2.5, 97.5]
    ).tolist()
    d["scour_k_conversion"] = SCOUR_K_CONVERSION_USACE
    d["interval_scope"] = (
        "numerical event subsampling only; descriptive percentile bands with "
        "four events per bin; not hazard, soil or model uncertainty"
    )
    d["evidence_sha256"] = study.digest(path)
    return d


def rating_record(data_repo: Path, kp: float, berm: bool) -> dict:
    """Annualize the rating arm with fixed production surface marginal curves."""
    path = study.OUT / f"rating_{kp}_{berm}_17.json"
    d = json.loads(path.read_text())
    coarse = json.loads((study.OUT / f"rating_{kp}_{berm}_9.json").read_text())
    pop = study.population(data_repo, kp, berm, d["n"])
    assert pop["input_sha256"] == d["input_sha256"] == coarse["input_sha256"]
    assert pop["config_hash"] == d["config_hash"] == coarse["config_hash"]
    assert d["n"] == coarse["n"], "quadrature comparison needs the same population"
    grid = np.array(d["grid"])
    baseline = np.array(d["baseline"])
    uniform = np.array(d["uniform"])
    surfaces = load_surface_curves(
        REPO
        / "data/processed/uemura_surface_curves/uemura_surface_curves_historical.csv"
    )
    for scenario in ("historical", "plus4K"):
        recs, _, _, _ = study.records(data_repo, kp, scenario)
        peaks = np.array([r.peak for r in recs.values()])
        po = surfaces.lookup(
            river="Tokachi", kp=kp, mechanism="overflow", scenario="historical"
        ).evaluate(peaks)
        ps = surfaces.lookup(
            river="Tokachi", kp=kp, mechanism="fluvial_scour", scenario="historical"
        ).evaluate(peaks)
        out = {}
        for name, arr in (("baseline", baseline), ("uniform", uniform)):
            pb, _ = study.curve(grid, arr[:, 1]).evaluate(peaks)
            out[name] = study.summary(np.stack((pb, po, ps), axis=-1))
        d[scenario]["system_comparison"] = out
        d[scenario]["quadrature_relative_change"] = (
            d[scenario]["transient"]["uniform"]
            / coarse[scenario]["transient"]["uniform"]
            - 1
        )
    d["climate_ratio"] = {
        arm: d["plus4K"]["system_comparison"][arm]["system"]
        / d["historical"]["system_comparison"][arm]["system"]
        for arm in ("baseline", "uniform")
    }
    # A local comparison is only quoted where both marginal counts and both
    # survival counts in the unperturbed sample clear the thesis's 30-row floor.
    eligible = (
        np.min(np.concatenate((baseline, 1 - baseline), axis=1) * d["n"], axis=1) >= 30
    ) & (grid <= ATTAINABLE_MAX[kp] + 1e-9)
    anchors = []
    for i in np.flatnonzero(eligible):
        ps, pt = baseline[i]
        qs, qt = uniform[i]
        anchors.append(
            dict(
                stage=float(grid[i]),
                p_static=ps,
                p_transient=pt,
                p_static_rating=qs,
                p_transient_rating=qt,
                B=ps / pt,
                B_rating=qs / qt,
                dbeta=norm.ppf(ps) - norm.ppf(pt),
                dbeta_rating=norm.ppf(qs) - norm.ppf(qt),
            )
        )
    d["resolved_baseline_grid_comparisons"] = anchors
    d["composition_scope"] = (
        "isolated piping-marginal change; primary overflow rating term retained; "
        "existing conditional independence retained, not joint integration "
        "over a shared hydraulic error"
    )
    return d


def inherited_record(data_repo: Path) -> dict:
    """Current revised-grading evidence, not the historical prose in study notes."""
    root = REPO / "docs/decisions"
    toe = json.loads((root / "adr0046-ztoe-companion.json").read_text())
    hazard = json.loads(
        (root / "annualisation-hazard-sampling-uncertainty.json").read_text()
    )
    out = {"replay": {}, "hazard": {}, "toe": {}, "source_digests": {}}
    for kp in study.KPS:
        key = f"KP {kp:.1f}"
        out["replay"][key] = {}
        for folder in ("phase2", "phase2_anchor_rating"):
            p = (
                data_repo
                / "results"
                / folder
                / f"tokachi_kp{kp:.1f}_historical_matrix_posterior.json"
            )
            meta = json.loads(p.read_text())
            out["replay"][key][folder] = meta["phase2"]["posterior"][
                "rejection_fraction"
            ]
        out["hazard"][key] = hazard["sections"][key]["matrix/posterior"]
        row = next(
            r
            for r in toe["sections"]
            if r["cross_section_id"] == f"tokachi_kp{kp:.1f}"
            and r["d70_interpretation"] == "matrix"
        )
        out["toe"][key] = {
            arm: v["rejection_fraction_trans"]
            for arm, v in row["phase2_end_to_end"].items()
        }
    out["structural_pattern_spread"] = hazard["structural_pattern_spread"]
    for name in ("canonical-shape-sensitivity", "composition-seam-rating-error"):
        p = root / f"{name}.json"
        source = json.loads(p.read_text())
        out[name] = {"source": str(p.relative_to(REPO)), "keys": list(source)}
    for name in (
        "canonical-shape-sensitivity",
        "composition-seam-rating-error",
        "adr0046-ztoe-companion",
        "annualisation-hazard-sampling-uncertainty",
    ):
        out["source_digests"][name] = study.digest(root / f"{name}.json")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-repo", type=Path, required=True)
    args = parser.parse_args()
    payload = {
        "study": "hydrograph-uncertainty-study",
        "date": "2026-09-27",
        "preregistration_commit": "7330334",
        "production_defaults_changed": False,
        "additional_source_sha256": {
            "local_rating_workbook": study.digest(
                study.rating_curve_path(args.data_repo / "data/raw", "Tokachi")
            ),
            "segment_inputs": study.digest(
                REPO / "data/processed/uemura_segments/segment_inputs.csv"
            ),
            "primary_surfaces": study.digest(
                REPO
                / "data/processed/uemura_surface_curves"
                / "uemura_surface_curves_historical.csv"
            ),
        },
        "conditioning": (
            "ADR-0054 matrix, prior; baseline plus measured berm, drain inert; "
            "225 s; N=8192 subset of production rows"
        ),
        "rating": [],
        "shapes": [],
    }
    for kp, berm in CASES:
        payload["rating"].append(rating_record(args.data_repo, kp, berm))
        payload["shapes"].append(shape_record(args.data_repo, kp, berm))
        print(kp, berm, "summarized", flush=True)
    with np.load(study.OUT / "ensemble_historical.npz") as f:
        payload["observation_comparison"] = {
            "published_figure_3_17": dict(
                observed_n=50,
                observed_years="1961 to 2010",
                quantiles=[0, 0.05, 0.5, 0.95, 1],
                observed=[190, 285, 647, 2752, 4952],
                published_simulated=[95, 274, 746, 2442, 6300],
            ),
            "provided_export": dict(
                n=len(f["q"]),
                quantiles=np.quantile(
                    f["q"].max(axis=1), [0, 0.05, 0.5, 0.95, 1]
                ).tolist(),
                source_sha256=str(f["sha"]),
            ),
            "verdict": (
                "Published experiment and provided export have different summaries; "
                "no causal explanation inferred. Discharge-level plausibility only, "
                "not independent section-stage or rare-tail validation."
            ),
        }
    payload["inherited"] = inherited_record(args.data_repo)
    path = REPO / "docs/decisions/hydrograph-uncertainty-study.json"
    path.write_text(
        json.dumps(payload, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(path)


if __name__ == "__main__":
    main()
