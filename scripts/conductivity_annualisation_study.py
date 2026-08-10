"""Aquifer-conductivity epistemic bracket propagated through the Phase 3 annualisation.

Companion study for `docs/decisions/conductivity-bracket-annualisation.md`
(pre-registered Part 1, 2026-08-10). Closes defence-brief item A2: ADR-0048 and
`epistemic-bracket-synthesis.md` measured the k_aq bracket on the **conditional**
fragility curves only, so the largest declared unknown in the study had never been
carried across the annualisation integral where every RQ3 and RQ4 headline lives.

What it does
------------
Re-composes the Phase 3 segment fragility and re-annualises it once per arm,
substituting the persisted ADR-0048 companion sweep for the production Phase 1
prior curve at the four BEP sections. Nothing is re-swept: the arms already exist
under ``results/sensitivity/adr0048_prior_means/`` (N = 1e5, 2026-07-29/30) and
the Phase 3 hazard cache is reused read-only.

**Scope: matrix d70 and prior-side only.** No bulk-d70 conductivity arm exists
and no Phase 2 posterior exists for any arm. At KP 62.0 the production prior and
posterior annual numbers are identical to full precision (the 2016 update rejects
0.00 % there), so prior-against-prior is apples-to-apples where it matters most.

Gates (pre-registered; a failure aborts rather than being tabulated)
-------------------------------------------------------------------
1. The baseline arm must reproduce ``rq4_annual.csv`` EXACTLY for every
   matrix / prior / 250 m / primary row, field for field.
2. Each arm's conditioning grid equals its baseline's; N = 1e5; the sidecar's
   config round-trips to its recorded hash and carries the expected scenario
   label.
3. The 110 segments with no BEP source are bit-identical across every arm.
4. The hazard cache file set and digests are unchanged (no workbook streamed).
5. Nothing is written outside ``results/sensitivity/conductivity_annualisation/``,
   this study's evidence JSON and its own figure.

Why a standalone companion rather than a ``phase3_campaign.py`` variant axis:
the campaign's no-argument call must stay byte-identical, and this study consumes
gitignored ADR-0048 arm outputs the campaign deliberately does not produce
(knobs stay OFF, campaign decision 3). The composition step itself is **imported**
from the campaign, never re-implemented, so gate 1 tests the production code path.

Usage (repo root, venv active)::

    python scripts/conductivity_annualisation_study.py
    python scripts/conductivity_annualisation_study.py --arms k_aq_field_geomean
    python scripts/conductivity_annualisation_study.py --figures-only

``--n-jobs`` is deliberately absent: this study re-runs no sweep and has no
parallelisable work, and a flag that controls nothing is the dead surface the
2026-07-31 audit removed elsewhere.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as figstyle  # noqa: E402

from bep_reliability_engine.config import Config  # noqa: E402
from system_integration.annualize import annualize  # noqa: E402
from system_integration.bep_input import load_bep_curve  # noqa: E402
from system_integration.hazard import load_reach_hazard  # noqa: E402
from system_integration.segments import build_registry, load_section_table  # noqa: E402
from system_integration.surface_curves import (  # noqa: E402
    SurfaceCurveSet,
    load_surface_curves,
)
from system_integration.uemura_models import load_segment_inputs  # noqa: E402

DEFAULT_OUT = (
    REPO_ROOT / "docs" / "decisions" / "conductivity-bracket-annualisation.json"
)
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "conductivity_annualisation"
ARM_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0048_prior_means"
PRODUCTION_TABLE = (
    REPO_ROOT / "results" / "system_integration" / "phase3" / "rq4_annual.csv"
)
FIGURE_NAME = "conductivity_bracket_annual.png"

#: The pre-registered variant axis. Fixed here so it cannot drift.
D70 = "matrix"
BEP_SOURCE = "prior"
LAMBDA_AC_M = 250.0
SURFACE_VARIANT = "primary"

#: Arm labels in the pre-registered order: the conductivity ladder low to high,
#: then the negative control.
ARMS: tuple[str, ...] = (
    "k_aq_field_geomean",
    "k_aq_field_toe",
    "k_aq_regional_upper",
    "gamma_bl_sub_lower",
)
CONDUCTIVITY_ARMS = ("k_aq_field_geomean", "k_aq_field_toe", "k_aq_regional_upper")
CONTROL_ARM = "gamma_bl_sub_lower"

#: Rendered names. The record keys are the evidence JSON's own schema and are
#: never renamed to satisfy the figure rule (conventions section 9.3.1); the
#: substitution happens here, at render time.
ARM_DISPLAY_NAMES: dict[str, str] = {
    "baseline": "production value",
    "k_aq_field_geomean": "field tests, geometric mean",
    "k_aq_field_toe": "field test, landside toe",
    "k_aq_regional_upper": "regional band, upper end",
    "gamma_bl_sub_lower": "blanket unit weight, lower bound",
}
MECHANISM_DISPLAY_NAMES: dict[str, str] = {
    "bep": "backward erosion piping",
    "overflow": "overflow",
    "fluvial_scour": "fluvial scour",
}

#: The four geotechnically characterised sections, keyed by their Phase 3 node.
BEP_KPS: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0)

#: Last non-hypothetical conditioning level per section, where the repository
#: publishes one (ADR-0024: KP 62.0's grid runs above the attainable stage
#: purely to stabilise the lognormal fit, and those levels must never be read as
#: attainable). Values as pinned in ``scripts/stage6_6_gap_decomposition.py`` and
#: ``scripts/hwl_bias_resolution.py``. KP 58.8 and KP 60.0 publish no such
#: figure, so the check is reported as not computed there rather than guessed.
ATTAINABLE_MAX_M: dict[float, float] = {57.4: 43.25, 62.0: 50.5}

#: Display floor for the log axis. Lower than the Phase 3 figures' 1e-7 on
#: purpose: KP 60.0's lowest arm lands at 5.2e-8, and squashing it onto the same
#: floor as KP 57.4's *exactly zero* arm would render a real number and an empty
#: failure set identically. The two are drawn differently below.
DISPLAY_FLOOR = 1e-8


# --------------------------------------------------------------------------- #
# The composition step is imported, never re-implemented                        #
# --------------------------------------------------------------------------- #
def _load_campaign_module():
    """Import ``scripts/phase3_campaign.py`` for its composition step.

    Gate 1 asserts this study reproduces the production table exactly, which is
    only meaningful if the composition it exercises IS the production one. A
    second copy could drift. Same ``importlib`` route
    ``scripts/epistemic_bracket_synthesis.py`` uses to reach the ADR-0047 kernel.
    """
    path = REPO_ROOT / "scripts" / "phase3_campaign.py"
    spec = importlib.util.spec_from_file_location("phase3_campaign", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def _stem(kp: float) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{D70}"


def _label(kp: float) -> str:
    """Display label for a section, through the one shared conversion.

    ``_figstyle.section_label`` is the single place a run identifier becomes a
    river kilometre (conventions section 9.3.1), so both the evidence record and
    the figure key off the same string and cannot drift apart.
    """
    return figstyle.section_label(f"tokachi_kp{kp:.1f}")


def _baseline_sweep(kp: float) -> Path:
    return REPO_ROOT / "results" / f"{_stem(kp)}.h5"


def _arm_sweep(kp: float, arm: str) -> Path:
    return ARM_DIR / f"{_stem(kp)}_{arm}.h5"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _cache_state(cache_dir: Path) -> dict[str, str]:
    if not cache_dir.is_dir():
        return {}
    return {p.name: _sha256(p) for p in sorted(cache_dir.glob("*.csv"))}


def _arm_provenance(kp: float, arm: str) -> dict[str, Any]:
    """Gate 2 on one arm sweep: N, hash round-trip, scenario label."""
    h5 = _arm_sweep(kp, arm)
    sidecar = h5.with_suffix(".json")
    if not h5.is_file() or not sidecar.is_file():
        raise FileNotFoundError(
            f"missing ADR-0048 companion sweep for KP {kp:.1f} arm {arm!r}: "
            f"{h5.relative_to(REPO_ROOT)}. This study consumes the persisted "
            "arms read-only and never re-sweeps; regenerate with "
            "scripts/prior_mean_scenario_companion.py."
        )
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    config = Config.model_validate(metadata["config"])
    recorded = metadata.get("config_hash")
    if recorded is not None and config.config_hash() != recorded:
        raise AssertionError(
            f"KP {kp:.1f} arm {arm!r}: reconstructed config hash does not match "
            "the recorded config_hash; refusing to report against a drifted arm."
        )
    scenario = metadata.get("prior_mean_scenario")
    if scenario is None or scenario.get("label") != arm:
        raise AssertionError(
            f"KP {kp:.1f} arm {arm!r}: sweep does not carry the expected "
            f"prior_mean_scenario label (found {scenario!r})."
        )
    n_samples = int(config.mc.n_samples)
    if n_samples != 100_000:
        raise AssertionError(
            f"KP {kp:.1f} arm {arm!r}: N = {n_samples}, expected 100000."
        )
    parameter = next(iter(scenario["factors"]))
    return {
        "sweep": str(h5.relative_to(REPO_ROOT)).replace("\\", "/"),
        "sha256": _sha256(h5),
        "n_samples": n_samples,
        "config_hash_round_trips": True,
        "parameter": parameter,
        "factor": float(scenario["factors"][parameter]),
        "baseline_prior_mean": float(scenario["baseline_means"][parameter]),
        "effective_prior_mean": float(scenario["effective_means"][parameter]),
    }


# --------------------------------------------------------------------------- #
# Pipeline                                                                      #
# --------------------------------------------------------------------------- #
def build_context(campaign) -> dict[str, Any]:
    """Registry, surface curves and per-node hazard, as the campaign builds them."""
    registry = load_section_table(
        campaign.SECTION_TABLE, build_registry(campaign.DATA_ROOT), allow_gaps=True
    )
    seg_inputs = load_segment_inputs(campaign.SEGMENT_INPUTS)
    parts = [load_surface_curves(path) for path in campaign.PRIMARY_FILES]
    surface = SurfaceCurveSet(
        curves=tuple(c for part in parts for c in part.curves), source="uemura_csv"
    )

    # Node exposure datum. The campaign reads it from the posterior curve; this
    # study is prior-side, so it reads the prior's and asserts the two agree,
    # which is what keeps the warm hazard cache valid (gate 4).
    baseline_curves = {
        kp: load_bep_curve(_baseline_sweep(kp), branch="transient") for kp in BEP_KPS
    }
    datum_agreement = {}
    for kp in BEP_KPS:
        posterior_sidecar = (
            REPO_ROOT / "results" / "phase2" / f"{_stem(kp)}_posterior.json"
        )
        posterior_datum = (
            json.loads(posterior_sidecar.read_text(encoding="utf-8"))
            .get("phase2", {})
            .get("posterior_fragility", {})
            .get("datum_m")
        )
        prior_datum = baseline_curves[kp].datum_m
        if posterior_datum is None or float(posterior_datum) != float(prior_datum):
            raise AssertionError(
                f"KP {kp:.1f}: prior curve datum {prior_datum} differs from the "
                f"posterior datum {posterior_datum} the production campaign used "
                "for its hazard nodes; the cache lookup would not match."
            )
        datum_agreement[_label(kp)] = float(prior_datum)

    nodes = []
    for segment in registry.segments:
        if segment.bep_source_kp is not None:
            datum = baseline_curves[segment.kp].datum_m
        else:
            datum = seg_inputs[(segment.river, round(segment.kp, 3))].ground_m_msl
        nodes.append((segment.river, segment.kp, datum))

    hazards = {
        scenario: load_reach_hazard(
            campaign.DATA_ROOT,
            nodes=nodes,
            scenario=scenario,
            cache_dir=campaign.HAZARD_CACHE,
        )
        for scenario in campaign.SCENARIOS
    }
    return {
        "registry": registry,
        "surface": surface,
        "hazards": hazards,
        "baseline_curves": baseline_curves,
        "datum_agreement": datum_agreement,
    }


def annualise_variant(campaign, context: dict[str, Any], curves: dict[float, Any]):
    """One full 114-segment composition + annualisation pass.

    Returns ``{(river, kp, scenario): row}`` with the campaign's own field set,
    so gate 1 can compare it against ``rq4_annual.csv`` field for field.
    """
    n_eff = max(1.0, campaign.SEGMENT_LENGTH_M / LAMBDA_AC_M)
    rows: dict[tuple[str, float, str], dict[str, Any]] = {}
    coverage: dict[tuple[str, float, str], dict[str, Any]] = {}
    driving: dict[tuple[str, float, str], dict[str, Any]] = {}

    for segment in context["registry"].segments:
        bep = curves.get(segment.kp) if segment.bep_source_kp is not None else None
        frag, clamped = campaign._compose_segment(
            segment, context["surface"], bep, n_eff, "historical"
        )
        if frag is None:
            continue
        key = (segment.river, round(segment.kp, 3))
        for scenario in campaign.SCENARIOS:
            annual = annualize(frag, context["hazards"][scenario][key])
            row: dict[str, Any] = {
                "river": segment.river,
                "kp": segment.kp,
                "section_id": segment.section_id or "",
                "scenario": scenario,
                "d70": D70,
                "bep_source": BEP_SOURCE,
                "lambda_ac_m": LAMBDA_AC_M,
                "surface_variant": SURFACE_VARIANT,
                "mechanisms": "|".join(frag.mechanisms),
                "n_years": annual.n_years,
                "p_annual_system": annual.p_f_annual_system,
                "bep_clamped_above_grid": clamped,
                "system_lower_bound_clamp": annual.coverage["__system__"][
                    "lower_bound_clamp"
                ],
                "system_frac_peaks_above_grid": annual.coverage["__system__"][
                    "frac_peaks_above_grid"
                ],
            }
            for mech in ("bep", "overflow", "fluvial_scour"):
                row[f"p_annual_{mech}"] = annual.p_f_annual_per_mechanism.get(mech, "")
                row[f"share_{mech}"] = (
                    annual.dominance_share(mech) if mech in frag.mechanisms else ""
                )
            rows[(segment.river, segment.kp, scenario)] = row
            coverage[(segment.river, segment.kp, scenario)] = annual.coverage
            if segment.bep_source_kp is not None:
                driving[(segment.river, segment.kp, scenario)] = _driving_stage_band(
                    frag,
                    context["hazards"][scenario][key],
                    attainable_max=ATTAINABLE_MAX_M.get(round(segment.kp, 1)),
                )
    return rows, coverage, driving


def _driving_stage_band(
    fragility, hazard, *, attainable_max: float | None = None
) -> dict[str, Any]:
    """Which peak stages actually carry the annual probability.

    The annual number is a mean of P_sys over ensemble peaks, so each event
    contributes in proportion to its own conditional probability. Weighting the
    peak stages by that contribution gives the stage band the annualised answer
    is really made of, which is what decides whether a bracket measured on the
    conditional curve survives the integral or is averaged away.
    """
    peaks = np.asarray(hazard.peak_stages(), dtype=float)
    p_events = np.interp(peaks, fragility.stage_m_msl, fragility.p_sys)
    total = float(p_events.sum())
    if total <= 0.0:
        return {"defined": False}
    order = np.argsort(peaks)
    stages = peaks[order]
    cumulative = np.cumsum(p_events[order]) / total
    q10, q50, q90 = (float(np.interp(q, cumulative, stages)) for q in (0.1, 0.5, 0.9))
    band: dict[str, Any] = {
        "defined": True,
        "contribution_weighted_stage_p10_m_msl": q10,
        "contribution_weighted_stage_median_m_msl": q50,
        "contribution_weighted_stage_p90_m_msl": q90,
        "grid_top_m_msl": float(fragility.stage_m_msl[-1]),
    }

    # How much of the piping contribution is drawn from the ADR-0024
    # hypothetical grid extension, i.e. from stages the section cannot actually
    # reach. Distinct from a coverage clamp: no peak leaves the grid, so the
    # clamp flags are correctly False, yet part of the answer can still rest on
    # levels the thesis forbids plotting as attainable.
    band["attainable_max_m_msl"] = attainable_max
    if attainable_max is None or "bep" not in fragility.per_mechanism:
        band["frac_of_annual_piping_above_attainable_max"] = None
        return band
    p_bep = np.interp(peaks, fragility.stage_m_msl, fragility.per_mechanism["bep"])
    bep_total = float(p_bep.sum())
    band["frac_peaks_above_attainable_max"] = float(np.mean(peaks > attainable_max))
    band["frac_of_annual_piping_above_attainable_max"] = (
        None
        if bep_total <= 0.0
        else float(p_bep[peaks > attainable_max].sum() / bep_total)
    )
    return band


def gate_one(rows: dict[tuple[str, float, str], dict[str, Any]]) -> dict[str, Any]:
    """Assert the baseline pass reproduces the production table EXACTLY.

    The production CSV writes ``str(value)``, so a stringified comparison is an
    exact float comparison that also covers the ``""`` empty-mechanism cells and
    the boolean flags.
    """
    import csv

    with open(PRODUCTION_TABLE, encoding="utf-8", newline="") as handle:
        published = [
            r
            for r in csv.DictReader(handle)
            if r["d70"] == D70
            and r["bep_source"] == BEP_SOURCE
            and r["lambda_ac_m"] == str(LAMBDA_AC_M)
            and r["surface_variant"] == SURFACE_VARIANT
        ]
    if not published:
        raise AssertionError(
            f"no matrix/prior/{LAMBDA_AC_M:g}/{SURFACE_VARIANT} rows found in "
            f"{PRODUCTION_TABLE.relative_to(REPO_ROOT)}"
        )

    mismatches: list[str] = []
    for record in published:
        key = (record["river"], float(record["kp"]), record["scenario"])
        mine = rows.get(key)
        if mine is None:
            mismatches.append(f"{key}: missing from this study's pass")
            continue
        for field, published_value in record.items():
            if str(mine[field]) != published_value:
                mismatches.append(
                    f"{key} {field}: published {published_value!r} != "
                    f"reproduced {str(mine[field])!r}"
                )
    if mismatches:
        raise AssertionError(
            "GATE 1 FAILED: this study's pipeline does not reproduce the "
            "production annualisation. It is therefore not measuring the "
            "production quantity and no arm number may be reported.\n  "
            + "\n  ".join(mismatches[:20])
        )
    return {
        "passed": True,
        "rows_compared": len(published),
        "fields_compared": len(published[0]),
        "table": str(PRODUCTION_TABLE.relative_to(REPO_ROOT)).replace("\\", "/"),
        "criterion": "every field string-identical to the published table",
    }


def _leading_mechanism(row: dict[str, Any]) -> str:
    """Leading mechanism, or 'not defined' when nothing is loaded."""
    contributions = {
        mech: float(row[f"p_annual_{mech}"])
        for mech in ("bep", "overflow", "fluvial_scour")
        if row[f"p_annual_{mech}"] != ""
    }
    if not contributions or sum(contributions.values()) <= 0.0:
        return "not defined"
    return max(contributions, key=lambda m: contributions[m])


def summarise(
    baseline_rows: dict[tuple[str, float, str], dict[str, Any]],
    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
    baseline_coverage,
    arm_coverage,
    baseline_driving,
    arm_driving,
    campaign,
) -> dict[str, Any]:
    """Per section x scenario verdicts against the pre-registered criteria."""
    sections: dict[str, Any] = {}
    for kp in BEP_KPS:
        label = _label(kp)
        sections[label] = {}
        for scenario in campaign.SCENARIOS:
            key = ("Tokachi", kp, scenario)
            base = baseline_rows[key]
            p_bep = float(base["p_annual_bep"])
            p_ovf = float(base["p_annual_overflow"])
            margin = None if p_ovf == 0.0 else p_bep / p_ovf
            entry: dict[str, Any] = {
                "baseline": {
                    "p_annual_system": float(base["p_annual_system"]),
                    "p_annual_bep": p_bep,
                    "p_annual_overflow": p_ovf,
                    "p_annual_fluvial_scour": float(base["p_annual_fluvial_scour"]),
                    "share_bep": float(base["share_bep"]),
                    "share_overflow": float(base["share_overflow"]),
                    "leading_mechanism": _leading_mechanism(base),
                },
                "reversal_margin_p_bep_over_p_overflow": margin,
                "arms": {},
            }
            for arm in arm_rows:
                row = arm_rows[arm][key]
                arm_bep = float(row["p_annual_bep"])
                entry["arms"][arm] = {
                    "p_annual_system": float(row["p_annual_system"]),
                    "p_annual_bep": arm_bep,
                    "p_annual_overflow": float(row["p_annual_overflow"]),
                    "share_bep": float(row["share_bep"]),
                    "share_overflow": float(row["share_overflow"]),
                    "leading_mechanism": _leading_mechanism(row),
                    "ratio_system_to_baseline": (
                        None
                        if float(base["p_annual_system"]) == 0.0
                        else float(row["p_annual_system"])
                        / float(base["p_annual_system"])
                    ),
                    "ratio_bep_to_baseline": (
                        None if p_bep == 0.0 else arm_bep / p_bep
                    ),
                    "coverage_system": arm_coverage[arm][("Tokachi", kp, scenario)][
                        "__system__"
                    ],
                    "coverage_bep": arm_coverage[arm][("Tokachi", kp, scenario)].get(
                        "bep"
                    ),
                }
            leads = {arm: entry["arms"][arm]["leading_mechanism"] for arm in arm_rows}
            base_lead = entry["baseline"]["leading_mechanism"]
            # The pre-registered classification is three-way, not two-way: an
            # arm that drives EVERY mechanism to zero leaves no share to
            # compare, and reporting that as "overflow leads" would be false.
            reversed_arms = sorted(
                arm
                for arm, lead in leads.items()
                if lead != base_lead and lead != "not defined"
            )
            collapsed_arms = sorted(
                arm for arm, lead in leads.items() if lead == "not defined"
            )
            if reversed_arms:
                verdict = "REVERSED"
            elif collapsed_arms:
                verdict = "COLLAPSED"
            else:
                verdict = "ROBUST"
            entry["ordering_verdict"] = verdict
            entry["arms_reversing_the_lead"] = reversed_arms
            entry["arms_collapsing_to_undefined"] = collapsed_arms
            entry["arms_changing_the_lead"] = sorted(
                set(reversed_arms) | set(collapsed_arms)
            )

            # The comparable width of the knob at this cell, on the same
            # multiplicative footing epistemic-bracket-synthesis.md uses.
            for quantity in ("p_annual_system", "p_annual_bep"):
                values = [entry["baseline"][quantity]] + [
                    entry["arms"][arm][quantity] for arm in CONDUCTIVITY_ARMS
                ]
                low, high = min(values), max(values)
                entry[f"conductivity_span_{quantity}"] = (
                    None if low == 0.0 else high / low
                )
            sections[label][scenario] = entry

        # Climate ratio per arm (P6).
        hist = ("Tokachi", kp, "historical")
        plus = ("Tokachi", kp, "+4K")
        ratios = {
            "baseline": (
                float(baseline_rows[plus]["p_annual_system"])
                / float(baseline_rows[hist]["p_annual_system"])
                if float(baseline_rows[hist]["p_annual_system"]) > 0.0
                else None
            )
        }
        for arm in arm_rows:
            denominator = float(arm_rows[arm][hist]["p_annual_system"])
            ratios[arm] = (
                float(arm_rows[arm][plus]["p_annual_system"]) / denominator
                if denominator > 0.0
                else None
            )
        sections[label]["climate_ratio_plus4k_over_historical"] = ratios

    # Baseline coverage, for the "estimate vs bound" statement, and the stage
    # band the annualised answer is actually made of.
    for kp in BEP_KPS:
        for scenario in campaign.SCENARIOS:
            entry = sections[_label(kp)][scenario]
            entry["baseline"]["coverage_system"] = baseline_coverage[
                ("Tokachi", kp, scenario)
            ]["__system__"]
            entry["baseline"]["driving_stage_band"] = baseline_driving[
                ("Tokachi", kp, scenario)
            ]
            for arm in arm_rows:
                entry["arms"][arm]["driving_stage_band"] = arm_driving[arm][
                    ("Tokachi", kp, scenario)
                ]
    return sections


def evaluate_preregistration(
    sections: dict[str, Any], lambda_yardstick: dict[str, Any], scenarios
) -> dict[str, Any]:
    """Score Part 1's predictions and falsifiers against the measured record.

    Computed from the data by the same driver that produced it, so the verdicts
    in the note cannot drift from the numbers. Nothing here re-tunes a criterion:
    each entry restates the pre-registered rule and reports the outcome.
    """
    labels = [_label(kp) for kp in BEP_KPS]
    hist_reversed = [
        lab
        for lab in labels
        if sections[lab]["historical"]["ordering_verdict"] == "REVERSED"
    ]
    hist_collapsed = [
        lab
        for lab in labels
        if sections[lab]["historical"]["ordering_verdict"] == "COLLAPSED"
    ]

    def _arms_reversing(lab: str, scenario: str) -> list[str]:
        return sections[lab][scenario]["arms_reversing_the_lead"]

    kp62 = _label(62.0)
    p3_ok = set(_arms_reversing(kp62, "+4K")) == {
        "k_aq_field_geomean",
        "k_aq_field_toe",
    }
    p4_ok = not any(
        "k_aq_regional_upper" in _arms_reversing(lab, sc)
        for lab in labels
        for sc in scenarios
    )
    p5_ok = not _arms_reversing(_label(57.4), "historical") and not _arms_reversing(
        _label(60.0), "historical"
    )

    # P6: does the ratio move the predicted way at every cell where defined?
    p6_rows = []
    for lab in labels:
        ratios = sections[lab]["climate_ratio_plus4k_over_historical"]
        base = ratios["baseline"]
        for arm in CONDUCTIVITY_ARMS:
            value = ratios.get(arm)
            if value is None or base is None:
                continue
            rises = value > base
            expected_rise = arm != "k_aq_regional_upper"
            p6_rows.append(
                {
                    "section": lab,
                    "arm": arm,
                    "baseline_ratio": base,
                    "arm_ratio": value,
                    "moved_as_predicted": rises == expected_rise,
                }
            )

    # P7: the control must be at least an order of magnitude quieter than the
    # quietest conductivity arm at the same cell, on a log scale.
    p7_rows = []
    for lab in labels:
        for scenario in scenarios:
            entry = sections[lab][scenario]
            base = entry["baseline"]["p_annual_system"]
            if base <= 0.0:
                continue
            control = abs(
                np.log10(entry["arms"][CONTROL_ARM]["p_annual_system"] / base)
            )
            conductivity = [
                abs(np.log10(entry["arms"][arm]["p_annual_system"] / base))
                for arm in CONDUCTIVITY_ARMS
                if entry["arms"][arm]["p_annual_system"] > 0.0
            ]
            quietest = min(conductivity)
            p7_rows.append(
                {
                    "section": lab,
                    "scenario": scenario,
                    "control_log10_shift": float(control),
                    "quietest_conductivity_log10_shift": float(quietest),
                    "at_least_ten_times_quieter": bool(quietest > 10.0 * control),
                }
            )

    # F3: is the annualised conductivity span narrower than the published
    # length-effect bracket everywhere? (If so, the study deflates itself.)
    f3_rows = []
    for lab in labels:
        for scenario in scenarios:
            span = sections[lab][scenario]["conductivity_span_p_annual_system"]
            yardstick = lambda_yardstick[lab][scenario]
            f3_rows.append(
                {
                    "section": lab,
                    "scenario": scenario,
                    "conductivity_span": span,
                    "length_effect_span": yardstick,
                    "conductivity_is_wider": span is None or span > yardstick,
                }
            )

    return {
        "P1": {
            "statement": (
                "KP 62.0 is the only section whose historical ordering is "
                "contestable"
            ),
            "held": hist_reversed == [kp62] and not hist_collapsed,
            "sections_reversing_historically": hist_reversed,
            "sections_collapsing_historically": hist_collapsed,
        },
        "P2": {
            "statement": (
                "at KP 62.0 historical the low-conductivity arm hands the lead "
                "to overflow"
            ),
            "held": "k_aq_field_geomean" in _arms_reversing(kp62, "historical"),
        },
        "P3": {
            "statement": (
                "KP 62.0 at +4K reverses under both downward arms and holds "
                "under the upward arm"
            ),
            "held": bool(p3_ok),
            "arms_reversing": _arms_reversing(kp62, "+4K"),
        },
        "P4": {
            "statement": "the upward arm reverses no ordering anywhere",
            "held": bool(p4_ok),
        },
        "P5": {
            "statement": (
                "KP 57.4 and KP 60.0 cannot reverse historically, because "
                "overflow is exactly zero there"
            ),
            "held": bool(p5_ok),
            "kp57_4_historical_verdict": sections[_label(57.4)]["historical"][
                "ordering_verdict"
            ],
            "kp60_0_historical_verdict": sections[_label(60.0)]["historical"][
                "ordering_verdict"
            ],
        },
        "P6": {
            "statement": (
                "the climate ratio rises under the downward arms and falls "
                "under the upward arm"
            ),
            "held": all(row["moved_as_predicted"] for row in p6_rows),
            "cells": p6_rows,
        },
        "P7": {
            "statement": (
                "the blanket unit weight control changes no ordering and is at "
                "least an order of magnitude quieter than the quietest "
                "conductivity arm"
            ),
            "held": all(row["at_least_ten_times_quieter"] for row in p7_rows)
            and not any(
                CONTROL_ARM in sections[lab][sc]["arms_changing_the_lead"]
                for lab in labels
                for sc in scenarios
            ),
            "cells": p7_rows,
        },
        "F1": {
            "statement": "the upward arm reverses an ordering (would indict the arms)",
            "fired": not p4_ok,
        },
        "F3": {
            "statement": (
                "the annualised conductivity span is narrower than the published "
                "length-effect bracket at every section (would deflate the study)"
            ),
            "fired": all(not row["conductivity_is_wider"] for row in f3_rows),
            "cells": f3_rows,
        },
        "F5": {
            "statement": (
                "if P1 fails it fails at KP 58.8 historical, the smallest finite "
                "margin outside KP 62.0"
            ),
            "fired": _label(58.8) in hist_reversed,
        },
    }


def reach_invariance(
    baseline_rows: dict[tuple[str, float, str], dict[str, Any]],
    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
) -> dict[str, Any]:
    """GATE 3: no conductivity arm may touch a segment with no BEP source."""
    bep_keys = {(river, kp) for (river, kp, _) in baseline_rows if kp in BEP_KPS}
    checked = 0
    for arm, rows in arm_rows.items():
        for key, base in baseline_rows.items():
            river, kp, _ = key
            if (river, kp) in bep_keys and river == "Tokachi":
                continue
            if str(rows[key]["p_annual_system"]) != str(base["p_annual_system"]):
                raise AssertionError(
                    f"GATE 3 FAILED: arm {arm!r} moved segment {river} KP {kp:.1f}, "
                    "which carries no BEP source and is conductivity-inert by "
                    "construction."
                )
            checked += 1
    return {
        "passed": True,
        "segment_scenario_cells_checked": checked,
        "criterion": (
            "every segment with no BEP source is bit-identical to baseline "
            "under every arm"
        ),
    }


# --------------------------------------------------------------------------- #
# Figure                                                                        #
# --------------------------------------------------------------------------- #
def render_figure(payload: dict[str, Any], out_dir: Path) -> Path:
    """Two panels: the annualised bracket, and the dominance crossing.

    No rendered text carries a decision identifier, a run identifier, a record
    field name or an em dash (conventions section 9.3.1).
    """
    import matplotlib.pyplot as plt

    fs = figstyle
    fs.style()
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14.4, 5.4))

    sections = payload["sections"]
    labels = [_label(kp) for kp in BEP_KPS]
    scenario_marker = {"historical": "o", "+4K": "D"}
    scenario_name = {"historical": "historical climate", "+4K": "4 K warming"}

    # --- left: annual system probability, baseline against the bracket -------
    x_positions = {label: i for i, label in enumerate(labels)}
    any_exact_zero = False
    for scenario, offset in (("historical", -0.13), ("+4K", 0.13)):
        for label in labels:
            entry = sections[label][scenario]
            values = [entry["baseline"]["p_annual_system"]] + [
                entry["arms"][arm]["p_annual_system"] for arm in CONDUCTIVITY_ARMS
            ]
            positive = [v for v in values if v > 0.0]
            exact_zero = len(positive) < len(values)
            plotted = [max(v, DISPLAY_FLOOR) for v in positive]
            x = x_positions[label] + offset
            ax_left.plot(
                [x, x],
                [min(plotted), max(plotted)],
                color=fs.MUTED,
                lw=1.4,
                solid_capstyle="round",
                zorder=1,
            )
            ax_left.plot(
                [x] * len(plotted),
                plotted,
                linestyle="none",
                marker="_",
                ms=11,
                mew=1.6,
                color=fs.INK_2,
                zorder=2,
            )
            if exact_zero:
                # An empty failure set is not a small number. It is drawn at the
                # floor in the alert colour with its own legend entry, so it can
                # never be read off the axis as a probability.
                any_exact_zero = True
                ax_left.plot(
                    [x, x],
                    [DISPLAY_FLOOR, min(plotted)],
                    color=fs.CRITICAL,
                    lw=1.2,
                    linestyle=(0, (1.5, 1.5)),
                    zorder=1,
                )
                ax_left.plot(
                    [x],
                    [DISPLAY_FLOOR],
                    linestyle="none",
                    marker="v",
                    ms=6.5,
                    color=fs.CRITICAL,
                    zorder=3,
                )
            ax_left.plot(
                [x],
                [max(entry["baseline"]["p_annual_system"], DISPLAY_FLOOR)],
                linestyle="none",
                marker=scenario_marker[scenario],
                ms=7,
                color=fs.SECTION_COLORS[label.replace(" ", "")],
                mec=fs.INK,
                mew=0.7,
                zorder=3,
            )
    ax_left.set_yscale("log")
    ax_left.set_xticks(range(len(labels)))
    ax_left.set_xticklabels(labels)
    ax_left.set_xlim(-0.5, len(labels) - 0.5)
    ax_left.set_ylabel("annual system failure probability [1/yr]")
    ax_left.set_title(
        "Annual failure probability across the aquifer conductivity bracket"
    )
    # A probability axis stops at 1; the spans reach 0.12, so this is headroom
    # without inviting anyone to read a rate off the top of the panel.
    ax_left.set_ylim(ax_left.get_ylim()[0], 1.0)
    handles = [
        plt.Line2D(
            [],
            [],
            linestyle="none",
            marker=scenario_marker[s],
            ms=7,
            color=fs.INK_2,
            label=f"production value, {scenario_name[s]}",
        )
        for s in ("historical", "+4K")
    ]
    handles.append(
        plt.Line2D([], [], color=fs.MUTED, lw=1.4, label="span of the three arms")
    )
    if any_exact_zero:
        handles.append(
            plt.Line2D(
                [],
                [],
                color=fs.CRITICAL,
                lw=1.2,
                linestyle=(0, (1.5, 1.5)),
                marker="v",
                ms=6.5,
                label="an arm gives no failures at all",
            )
        )
    # Below the axes: the spans occupy eight decades and the one clear band
    # (above 0.12) is too shallow for four entries once the axis is capped at 1.
    ax_left.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=2,
        fontsize=9.0,
    )

    # --- right: dominance share against conductivity -------------------------
    undefined_points: list[tuple[float, str]] = []
    for label in labels:
        colour = fs.SECTION_COLORS[label.replace(" ", "")]
        for scenario in ("historical", "+4K"):
            entry = sections[label][scenario]
            points = []
            for arm in CONDUCTIVITY_ARMS:
                x_value = payload["arms"][arm][label]["effective_prior_mean"]
                # A cell where nothing is loaded has no share. The composition
                # reports 0.0 there, which on this axis is indistinguishable
                # from "overflow takes all of it" -- the opposite reading. Such
                # points are withheld from the line and marked separately.
                if entry["arms"][arm]["leading_mechanism"] == "not defined":
                    undefined_points.append((x_value, label))
                    continue
                points.append((x_value, entry["arms"][arm]["share_bep"]))
            points.append(
                (
                    payload["baseline_prior_mean_k_aq"][label],
                    entry["baseline"]["share_bep"],
                )
            )
            points.sort()
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax_right.plot(
                xs,
                ys,
                color=colour,
                lw=1.7,
                marker=fs.SECTION_MARKERS[label.replace(" ", "")],
                ms=5.5,
                mfc=colour if scenario == "historical" else fs.SURFACE,
                linestyle="-" if scenario == "historical" else "--",
                label=f"{label}, {scenario_name[scenario]}",
                zorder=3,
            )
            ax_right.plot(
                [payload["baseline_prior_mean_k_aq"][label]],
                [entry["baseline"]["share_bep"]],
                linestyle="none",
                marker="o",
                ms=9,
                mfc="none",
                mec=fs.INK,
                mew=1.2,
                zorder=4,
            )
    if undefined_points:
        ax_right.plot(
            [x for x, _ in undefined_points],
            [0.0] * len(undefined_points),
            linestyle="none",
            marker="x",
            ms=9,
            mew=2.0,
            color=fs.CRITICAL,
            label="no mechanism loaded, share undefined",
            zorder=5,
        )
    ax_right.axhline(0.5, color=fs.CRITICAL, lw=1.3, zorder=2)
    ax_right.text(
        0.985,
        0.5,
        "equal contribution",
        transform=ax_right.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=fs.CRITICAL,
    )
    ax_right.set_xscale("log")
    ax_right.set_ylim(-0.03, 1.03)
    ax_right.set_xlabel("aquifer hydraulic conductivity, prior mean [m/s]")
    ax_right.set_ylabel("piping share of the annual failure probability")
    ax_right.set_title("Which mechanism leads, across the same bracket")
    # Outside the axes: eight series over a monotone rise leave no interior
    # region a legend can occupy without covering a crossing, and the crossings
    # are the point of the panel.
    ax_right.legend(
        loc="center left", bbox_to_anchor=(1.015, 0.5), fontsize=8.8, handlelength=2.4
    )

    fig.suptitle(
        "Aquifer conductivity carried through to annual probability, "
        "matrix grain size, prior fragility",
        fontsize=12.5,
        y=1.005,
    )
    fig.text(
        0.5,
        -0.21,
        "Open circles mark the production value. Both panels: four surveyed "
        "sections, corrected surface curves, 200 m segments.",
        ha="center",
        fontsize=8.5,
        color=fs.MUTED,
    )
    fig.tight_layout()
    return fs.save(fig, FIGURE_NAME, mirror=out_dir / "figures")


# --------------------------------------------------------------------------- #
# Entry point                                                                   #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--arms",
        nargs="+",
        default=list(ARMS),
        choices=list(ARMS),
        help="Arms to propagate (default: all four, the pre-registered set).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Evidence JSON output path.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Study-local output directory (gitignored).",
    )
    parser.add_argument(
        "--no-figure", action="store_true", help="Skip figure rendering."
    )
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help=(
            "Re-render the figure from the committed evidence record and exit. "
            "Writes no evidence file, runs no composition."
        ),
    )
    args = parser.parse_args(argv)

    if args.figures_only:
        payload = json.loads(args.out.read_text(encoding="utf-8"))
        path = render_figure(payload, args.out_dir)
        print(f"wrote {path.relative_to(REPO_ROOT)} (figure only; no record written)")
        return 0

    started = time.time()
    campaign = _load_campaign_module()
    cache_before = _cache_state(campaign.HAZARD_CACHE)

    print("building registry, surface curves and node hazard ...", flush=True)
    context = build_context(campaign)

    print("baseline pass (gate 1) ...", flush=True)
    baseline_rows, baseline_coverage, baseline_driving = annualise_variant(
        campaign, context, context["baseline_curves"]
    )
    gate1 = gate_one(baseline_rows)
    print(
        f"  GATE 1 PASSED: {gate1['rows_compared']} published rows reproduced "
        f"field for field ({gate1['fields_compared']} fields each)",
        flush=True,
    )

    arm_rows: dict[str, Any] = {}
    arm_coverage: dict[str, Any] = {}
    arm_driving: dict[str, Any] = {}
    arm_provenance: dict[str, dict[str, Any]] = {}
    for arm in args.arms:
        print(f"arm: {arm} ...", flush=True)
        curves = {}
        arm_provenance[arm] = {}
        for kp in BEP_KPS:
            label = _label(kp)
            arm_provenance[arm][label] = _arm_provenance(kp, arm)
            curve = load_bep_curve(_arm_sweep(kp, arm), branch="transient")
            if not np.array_equal(
                np.asarray(curve.grid_m_msl),
                np.asarray(context["baseline_curves"][kp].grid_m_msl),
            ):
                raise AssertionError(
                    f"GATE 2 FAILED: {label} arm {arm!r} conditioning grid "
                    "differs from the baseline grid."
                )
            curves[kp] = curve
        arm_rows[arm], arm_coverage[arm], arm_driving[arm] = annualise_variant(
            campaign, context, curves
        )

    gate3 = reach_invariance(baseline_rows, arm_rows)
    cache_after = _cache_state(campaign.HAZARD_CACHE)
    if cache_after != cache_before:
        raise AssertionError(
            "GATE 4 FAILED: the Phase 3 hazard cache changed during this run; "
            "a workbook was streamed or a cache entry rewritten."
        )

    sections = summarise(
        baseline_rows,
        arm_rows,
        baseline_coverage,
        arm_coverage,
        baseline_driving,
        arm_driving,
        campaign,
    )

    # The published lambda_ac yardstick for falsifier F3, read from the same
    # production table (posterior side, which is where the campaign ran it).
    import csv

    with open(PRODUCTION_TABLE, encoding="utf-8", newline="") as handle:
        published = list(csv.DictReader(handle))
    lambda_yardstick: dict[str, Any] = {}
    for kp in BEP_KPS:
        label = _label(kp)
        lambda_yardstick[label] = {}
        for scenario in campaign.SCENARIOS:

            def _p(lam: float, _kp: float = kp, _scenario: str = scenario) -> float:
                return next(
                    float(r["p_annual_system"])
                    for r in published
                    if float(r["kp"]) == _kp
                    and r["scenario"] == _scenario
                    and r["d70"] == D70
                    and r["bep_source"] == "posterior"
                    and r["surface_variant"] == SURFACE_VARIANT
                    and float(r["lambda_ac_m"]) == lam
                )

            lambda_yardstick[label][scenario] = _p(40.0) / _p(250.0)

    prereg = evaluate_preregistration(
        sections, lambda_yardstick, list(campaign.SCENARIOS)
    )

    payload: dict[str, Any] = {
        "study": (
            "Aquifer-conductivity epistemic bracket propagated through the "
            "Phase 3 annualisation (defence-brief item A2)"
        ),
        "generated_by": "scripts/conductivity_annualisation_study.py",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "note": "docs/decisions/conductivity-bracket-annualisation.md",
        "scope": {
            "d70_interpretation": D70,
            "bep_source": BEP_SOURCE,
            "lambda_ac_m": LAMBDA_AC_M,
            "surface_variant": SURFACE_VARIANT,
            "scenarios": list(campaign.SCENARIOS),
            "sections": [_label(kp) for kp in BEP_KPS],
            "statement": (
                "matrix-d70 and prior-side ONLY. No bulk-d70 conductivity arm "
                "has ever been run and no Phase 2 posterior exists for any arm. "
                "Quote this scope wherever any number here is quoted."
            ),
        },
        "gates": {
            "gate_1_reproduces_production_table": gate1,
            "gate_2_arm_provenance": {
                "passed": True,
                "criterion": (
                    "grid equal to baseline, N = 1e5, config hash round-trips, "
                    "expected prior_mean_scenario label"
                ),
            },
            "gate_3_non_bep_segments_invariant": gate3,
            "gate_4_hazard_cache_unchanged": {
                "passed": True,
                "cache_files": len(cache_after),
            },
            "gate_5_no_production_artifact_written": {
                "passed": True,
                "writes": [
                    str(args.out.relative_to(REPO_ROOT)).replace("\\", "/"),
                    str(args.out_dir.relative_to(REPO_ROOT)).replace("\\", "/"),
                    f"docs/figures/{FIGURE_NAME}",
                ],
            },
        },
        "arms": arm_provenance,
        "baseline_prior_mean_k_aq": {
            _label(kp): float(
                Config.model_validate(
                    json.loads(
                        _baseline_sweep(kp)
                        .with_suffix(".json")
                        .read_text(encoding="utf-8")
                    )["config"]
                ).priors.k_aq.mean
            )
            for kp in BEP_KPS
        },
        "node_exposure_datum_m_msl": context["datum_agreement"],
        "preregistration_outcome": prereg,
        "sections": sections,
        "lambda_ac_bracket_yardstick": {
            "definition": (
                "published system P_f at lambda_ac = 40 m divided by 250 m, "
                "posterior side, matrix, primary surface (phase3_report section 6.2)"
            ),
            "values": lambda_yardstick,
        },
        "elapsed_s": round(time.time() - started, 1),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "annual_rows.json").write_text(
        json.dumps(
            {
                "baseline": [{**row} for row in baseline_rows.values()],
                **{
                    arm: [{**row} for row in rows.values()]
                    for arm, rows in arm_rows.items()
                },
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out.relative_to(REPO_ROOT)}")

    if not args.no_figure:
        path = render_figure(payload, args.out_dir)
        print(f"wrote {path.relative_to(REPO_ROOT)}")

    # Console summary against the pre-registered criteria.
    print(
        "\nordering verdicts (pre-registered: REVERSED = an arm hands the lead "
        "to another mechanism; COLLAPSED = an arm leaves no mechanism loaded)"
    )
    for kp in BEP_KPS:
        label = _label(kp)
        for scenario in campaign.SCENARIOS:
            entry = sections[label][scenario]
            margin = entry["reversal_margin_p_bep_over_p_overflow"]
            span = entry["conductivity_span_p_annual_system"]
            print(
                f"  {label:<8} {scenario:<11} margin "
                f"{'inf' if margin is None else format(margin, '.3g'):>8}  "
                f"span {'unbnd' if span is None else format(span, '.3g'):>9}  "
                f"{entry['ordering_verdict']:<10} "
                f"{','.join(entry['arms_changing_the_lead']) or '-'}"
            )
    print("\npre-registration outcome")
    for key in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
        print(f"  {key}: {'HELD' if prereg[key]['held'] else 'FAILED'}")
    for key in ("F1", "F3", "F5"):
        print(f"  {key}: {'FIRED' if prereg[key]['fired'] else 'did not fire'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
