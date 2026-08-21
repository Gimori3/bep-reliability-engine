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

**Two sides, selected by ``--side``.** ``prior`` (the default) is the 2026-08-10
study: it substitutes the arm's Phase 1 curve directly and compares
prior-against-prior. ``posterior`` is the 2026-08-21 continuation: each arm is
first replayed through the Phase 2 Accept-Reject update against the 2016 typhoon
survival record, and the resulting posterior curve is what gets annualised. The
posterior side is measured against the committed prior-side evidence record, so
the difference it reports is the survival constraint and nothing else.

**Both d70 readings are covered, and they are co-primary.** ``--d70 matrix`` is
the default and reproduces the 2026-08-10 record byte for byte apart from its own
timestamp stamps; ``--d70 bulk`` is the 2026-08-10 Part 3 replication. Under bulk
the production lead is ALREADY overflow at five of the eight section-and-climate
cells, so the decisive arm there is the UPWARD one -- the mirror image of the
matrix run, whose P4 recorded the upward arm as reversing nothing anywhere.

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

On the posterior side two further gates apply: 6, that every replay ran with
theta verification on, which is what proves an arm regenerated its OWN shifted
population rather than the baseline one (ADR-0048 decision 3); and 7, that the
prior-side numbers it is compared against are read from the committed record
rather than recomputed. The arm posteriors themselves are produced beforehand
by the ordinary Phase 2 CLI, with settings gated equal to the production
campaign's; ``scripts/conductivity_posterior_replay.py`` is the batch driver.

Usage (repo root, venv active)::

    python scripts/conductivity_annualisation_study.py
    python scripts/conductivity_annualisation_study.py --arms k_aq_field_geomean
    python scripts/conductivity_annualisation_study.py --figures-only
    python scripts/conductivity_annualisation_study.py --d70 bulk
    python scripts/conductivity_annualisation_study.py --d70 bulk --figures-only
    python scripts/conductivity_annualisation_study.py --side posterior
    python scripts/conductivity_annualisation_study.py --side posterior --d70 bulk

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

#: The two co-primary grain-size readings. ``matrix`` is the default and its
#: behaviour is byte-identical to the 2026-08-10 run that produced the committed
#: record; ``bulk`` is the Part 3 replication. This is a genuine axis of the
#: deliverable, not a sensitivity, which is why it is a flag rather than a
#: second driver.
DEFAULT_D70 = "matrix"
D70_CHOICES: tuple[str, ...] = ("matrix", "bulk")

#: Which side of the Bayesian update the arms are carried through. ``prior``
#: reproduces the 2026-08-10 records byte for byte apart from their own scope
#: sentence and timestamps; ``posterior`` is the 2026-08-21 continuation, which
#: replays each arm against the 2016 survival record before annualising it.
#: Default ``prior``, so every pre-existing invocation is unchanged.
DEFAULT_SIDE = "prior"
SIDE_CHOICES: tuple[str, ...] = ("prior", "posterior")

DECISIONS = REPO_ROOT / "docs" / "decisions"
DEFAULT_OUT: dict[tuple[str, str], Path] = {
    ("prior", "matrix"): DECISIONS / "conductivity-bracket-annualisation.json",
    ("prior", "bulk"): DECISIONS / "conductivity-bracket-annualisation-bulk.json",
    ("posterior", "matrix"): (DECISIONS / "conductivity-bracket-posterior-side.json"),
    ("posterior", "bulk"): (
        DECISIONS / "conductivity-bracket-posterior-side-bulk.json"
    ),
}
DEFAULT_OUT_DIR: dict[tuple[str, str], Path] = {
    ("prior", "matrix"): (
        REPO_ROOT / "results" / "sensitivity" / "conductivity_annualisation"
    ),
    ("prior", "bulk"): (
        REPO_ROOT / "results" / "sensitivity" / "conductivity_annualisation_bulk"
    ),
    ("posterior", "matrix"): (
        REPO_ROOT / "results" / "sensitivity" / "conductivity_posterior"
    ),
    ("posterior", "bulk"): (
        REPO_ROOT / "results" / "sensitivity" / "conductivity_posterior_bulk"
    ),
}
ARM_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0048_prior_means"
#: Production Phase 2 posteriors (the campaign's own BEP input, ADR-0038).
PHASE2_DIR = REPO_ROOT / "results" / "phase2"
#: This study's own arm posteriors. Gitignored like every other results/ path;
#: the record of what they contained is the evidence JSON, not the HDF5.
POSTERIOR_ARM_DIR = (
    REPO_ROOT / "results" / "sensitivity" / "conductivity_posterior" / "phase2"
)
PRODUCTION_TABLE = (
    REPO_ROOT / "results" / "system_integration" / "phase3" / "rq4_annual.csv"
)
#: One figure per reading, declared in the campaign by exact filename. The bulk
#: figure is the cross-reading comparison, so it reads BOTH committed records.
FIGURE_NAME: dict[str, str] = {
    "matrix": "conductivity_bracket_annual.png",
    "bulk": "conductivity_bracket_both_d70.png",
}

#: The rest of the pre-registered variant axis. Fixed here so it cannot drift.
#: ``bep_source`` is now the ``--side`` flag rather than a constant; the name is
#: kept for the prior side so nothing that reads it moves.
BEP_SOURCE = "prior"
LAMBDA_AC_M = 250.0
SURFACE_VARIANT = "primary"

#: Scope sentence per reading. The matrix string was frozen verbatim until
#: 2026-08-10, when running the bulk arms made its second clause ("no bulk-d70
#: conductivity arm has ever been run") false. A record of this kind may not
#: carry a claim its own repository has overtaken, so the clause is replaced by
#: a pointer to the companion record; the matrix numbers are untouched.
#: The prior-side strings were frozen verbatim until 2026-08-21, when running
#: the arms through Phase 2 made their last clause ("no Phase 2 posterior exists
#: for any conductivity arm under either reading") false. This is the second
#: time this record has overtaken its own scope sentence, and it is handled the
#: same way as the first: the overtaken clause is replaced by a pointer to the
#: companion record, and not one number is touched.
SCOPE_STATEMENT: dict[tuple[str, str], str] = {
    ("prior", "matrix"): (
        "matrix-d70 and prior-side ONLY. The bulk-d70 reading is the "
        "co-primary companion record conductivity-bracket-annualisation-bulk"
        ".json, run 2026-08-10; the Phase 2 posterior side of both readings is "
        "the companion record conductivity-bracket-posterior-side.json, run "
        "2026-08-21. "
        "Quote this scope wherever any number here is quoted."
    ),
    ("prior", "bulk"): (
        "bulk-d70 and prior-side ONLY. This is the co-primary grain-size "
        "reading, not a sensitivity; the matrix reading is the companion "
        "record conductivity-bracket-annualisation.json. The Phase 2 posterior "
        "side of both readings is the companion record "
        "conductivity-bracket-posterior-side-bulk.json, run 2026-08-21. "
        "Quote this scope wherever any number here is quoted."
    ),
    ("posterior", "matrix"): (
        "matrix-d70 and posterior-side ONLY: every arm is replayed against the "
        "2016 survival record before it is annualised. The prior-side "
        "counterpart is conductivity-bracket-annualisation.json and the "
        "bulk-d70 posterior is conductivity-bracket-posterior-side-bulk.json. "
        "Quote this scope wherever any number here is quoted."
    ),
    ("posterior", "bulk"): (
        "bulk-d70 and posterior-side ONLY: every arm is replayed against the "
        "2016 survival record before it is annualised. This is the co-primary "
        "grain-size reading, not a sensitivity; the matrix posterior is "
        "conductivity-bracket-posterior-side.json and the prior-side "
        "counterpart is conductivity-bracket-annualisation-bulk.json. "
        "Quote this scope wherever any number here is quoted."
    ),
}

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
def _stem(kp: float, d70: str) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{d70}"


def _label(kp: float) -> str:
    """Display label for a section, through the one shared conversion.

    ``_figstyle.section_label`` is the single place a run identifier becomes a
    river kilometre (conventions section 9.3.1), so both the evidence record and
    the figure key off the same string and cannot drift apart.
    """
    return figstyle.section_label(f"tokachi_kp{kp:.1f}")


def _baseline_sweep(kp: float, d70: str) -> Path:
    """The production Phase 1 sweep. Always Phase 1, whichever side is under
    test: on the posterior side it is still the parent whose provenance and
    conditioning grid the posterior inherits."""
    return REPO_ROOT / "results" / f"{_stem(kp, d70)}.h5"


def _arm_sweep(kp: float, arm: str, d70: str) -> Path:
    """The persisted ADR-0048 companion sweep. Phase 1, both sides."""
    return ARM_DIR / f"{_stem(kp, d70)}_{arm}.h5"


def _baseline_curve_path(kp: float, d70: str, side: str) -> Path:
    """The artifact the baseline BEP curve is read from, per side."""
    if side == "prior":
        return _baseline_sweep(kp, d70)
    return PHASE2_DIR / f"{_stem(kp, d70)}_posterior.h5"


def _arm_curve_path(kp: float, arm: str, d70: str, side: str) -> Path:
    """The artifact an arm's BEP curve is read from, per side."""
    if side == "prior":
        return _arm_sweep(kp, arm, d70)
    return POSTERIOR_ARM_DIR / f"{_stem(kp, d70)}_{arm}_posterior.h5"


#: Phase 2 settings fields that may legitimately differ between this study's arm
#: replays and the production campaign. Everything else is gated equal, because
#: a posterior computed under a different acceptance rule is not comparable to
#: the production posterior the thesis reports.
#:
#: ``trace_breach_times`` is the pre-registration's 2026-08-21 amendment and the
#: only substantive exemption: it is a persisted diagnostic that
#: ``pipeline.run_survival_update`` computes AFTER ``state.alive`` is fixed and
#: that the posterior fragility never reads, and it costs about 60x on the
#: upward conductivity arm because it is linear in the rejected-row count.
#: ``scripts/conductivity_posterior_replay.py`` carries the full argument and the
#: bit-identity measurement that backs it.
_PHASE2_SETTINGS_EXEMPT = frozenset({"output_dir", "trace_breach_times"})


def _production_phase2_settings(d70: str) -> dict[str, Any]:
    """The production campaign's Phase 2 settings, read from its own sidecar.

    Read from the artifact rather than restated here, so the gate cannot drift
    away from what the campaign actually did.
    """
    sidecar = PHASE2_DIR / f"{_stem(57.4, d70)}_posterior.json"
    if not sidecar.is_file():
        raise FileNotFoundError(
            f"missing production Phase 2 sidecar {_rel(sidecar)}; the arm "
            "settings gate has nothing to compare against."
        )
    return json.loads(sidecar.read_text(encoding="utf-8"))["phase2"]["settings"]


def _posterior_provenance(
    kp: float, arm: str | None, d70: str, reference: dict[str, Any]
) -> dict[str, Any]:
    """Gate 2 and gate 6 on one Phase 2 replay, plus the rejection fraction.

    ``arm`` is ``None`` for the baseline posterior, which is the production
    artifact and is checked on exactly the same terms as the arms.
    """
    path = (
        _baseline_curve_path(kp, d70, "posterior")
        if arm is None
        else _arm_curve_path(kp, arm, d70, "posterior")
    )
    sidecar = path.with_suffix(".json")
    if not path.is_file() or not sidecar.is_file():
        raise FileNotFoundError(
            f"missing Phase 2 posterior for KP {kp:.1f} "
            f"{'baseline' if arm is None else 'arm ' + repr(arm)}: "
            f"{_rel(path)}. Produce it with "
            "'python -m bayesian_reliability_updating <phase1.h5> --out "
            f"{_rel(POSTERIOR_ARM_DIR)} --verify --no-figures'."
        )
    block = json.loads(sidecar.read_text(encoding="utf-8"))["phase2"]

    settings = block["settings"]
    drift = sorted(
        field
        for field, value in reference.items()
        if field not in _PHASE2_SETTINGS_EXEMPT and settings.get(field) != value
    )
    if drift:
        raise AssertionError(
            f"GATE 2 FAILED: KP {kp:.1f} "
            f"{'baseline' if arm is None else repr(arm)} Phase 2 settings "
            f"differ from production in {drift}; a posterior computed under a "
            "different acceptance rule is not comparable to the production one."
        )
    verification = block.get("verification") or {}
    if not verification.get("verified"):
        raise AssertionError(
            f"GATE 6 FAILED: KP {kp:.1f} "
            f"{'baseline' if arm is None else repr(arm)} was replayed without "
            "theta verification, so nothing proves the arm regenerated its own "
            "shifted population rather than the baseline one (ADR-0048 dec. 3)."
        )
    posterior = block["posterior"]
    return {
        "posterior": _rel(path),
        "sha256": _sha256(path),
        "n_prior": int(posterior["n_prior"]),
        "n_accepted": int(posterior["n_accepted"]),
        "rejection_fraction": float(posterior["rejection_fraction"]),
        "criterion": posterior["criterion"],
        "anchor": settings["anchor"],
        "theta_verified": True,
        "phase2_settings_match_production": True,
    }


def _rel(path: Path) -> str:
    """Repo-relative path where possible, absolute otherwise.

    ``--out`` and ``--out-dir`` accept any path, and a scratch directory outside
    the repository is exactly how the matrix path is re-verified without
    overwriting the committed record. A bare ``relative_to`` raises there.
    """
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


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


def _arm_provenance(kp: float, arm: str, d70: str) -> dict[str, Any]:
    """Gate 2 on one arm sweep: N, hash round-trip, scenario label, reading."""
    h5 = _arm_sweep(kp, arm, d70)
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
    # The two readings share an arm directory and differ only in the stem, so a
    # mistyped stem would silently compare a bulk arm against a matrix baseline.
    # Asserted from the arm's own config rather than trusted from its filename.
    if config.priors.d70_interpretation != d70:
        raise AssertionError(
            f"KP {kp:.1f} arm {arm!r}: sweep carries "
            f"d70_interpretation={config.priors.d70_interpretation!r}, expected "
            f"{d70!r}; refusing to compare across grain-size readings."
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
def build_context(campaign, d70: str, side: str = "prior") -> dict[str, Any]:
    """Registry, surface curves and per-node hazard, as the campaign builds them.

    The node exposure datum stays pinned to the **matrix** curve whatever ``d70``
    is under test, because that is what the campaign used when it wrote the
    hazard cache. It is the exit toe elevation and is identical across the two
    readings at all four sections, but that is asserted below rather than
    assumed: a datum that moved would silently invalidate the cache lookup and
    with it gate 1.
    """
    registry = load_section_table(
        campaign.SECTION_TABLE, build_registry(campaign.DATA_ROOT), allow_gaps=True
    )
    seg_inputs = load_segment_inputs(campaign.SEGMENT_INPUTS)
    parts = [load_surface_curves(path) for path in campaign.PRIMARY_FILES]
    surface = SurfaceCurveSet(
        curves=tuple(c for part in parts for c in part.curves), source="uemura_csv"
    )

    # Node exposure datum. The campaign reads it from the posterior curve; on
    # the prior side this study reads the prior's and asserts the two agree,
    # which is what keeps the warm hazard cache valid (gate 4). On the posterior
    # side it is reading the campaign's own artifact, and the same assertion
    # then simply confirms the two sides share one exposure datum.
    baseline_curves = {
        kp: load_bep_curve(_baseline_curve_path(kp, d70, side), branch="transient")
        for kp in BEP_KPS
    }
    node_datum = {
        kp: load_bep_curve(_baseline_sweep(kp, "matrix"), branch="transient").datum_m
        for kp in BEP_KPS
    }
    datum_agreement = {}
    for kp in BEP_KPS:
        posterior_sidecar = (
            REPO_ROOT / "results" / "phase2" / f"{_stem(kp, 'matrix')}_posterior.json"
        )
        posterior_datum = (
            json.loads(posterior_sidecar.read_text(encoding="utf-8"))
            .get("phase2", {})
            .get("posterior_fragility", {})
            .get("datum_m")
        )
        prior_datum = node_datum[kp]
        if posterior_datum is None or float(posterior_datum) != float(prior_datum):
            raise AssertionError(
                f"KP {kp:.1f}: prior curve datum {prior_datum} differs from the "
                f"posterior datum {posterior_datum} the production campaign used "
                "for its hazard nodes; the cache lookup would not match."
            )
        if float(baseline_curves[kp].datum_m) != float(prior_datum):
            raise AssertionError(
                f"KP {kp:.1f}: the {d70} curve datum "
                f"{baseline_curves[kp].datum_m} differs from the matrix datum "
                f"{prior_datum} the hazard cache was built on; the two readings "
                "would not be composed against the same exposure."
            )
        datum_agreement[_label(kp)] = float(prior_datum)

    nodes = []
    for segment in registry.segments:
        if segment.bep_source_kp is not None:
            datum = node_datum[segment.kp]
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


def annualise_variant(
    campaign,
    context: dict[str, Any],
    curves: dict[float, Any],
    d70: str,
    side: str = "prior",
):
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
                "d70": d70,
                "bep_source": side,
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


def gate_one(
    rows: dict[tuple[str, float, str], dict[str, Any]], d70: str, side: str = "prior"
) -> dict[str, Any]:
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
            if r["d70"] == d70
            and r["bep_source"] == side
            and r["lambda_ac_m"] == str(LAMBDA_AC_M)
            and r["surface_variant"] == SURFACE_VARIANT
        ]
    if not published:
        raise AssertionError(
            f"no {d70}/{side}/{LAMBDA_AC_M:g}/{SURFACE_VARIANT} rows found in "
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


def clamped_cells(
    baseline_rows: dict[tuple[str, float, str], dict[str, Any]],
    arm_rows: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Cells whose piping annual probability is an ADR-0024 lower bound.

    ``bep_clamped_above_grid`` fires where the section's transient transition is
    not bracketed, so the raw-tail branch holds its last value above the grid
    instead of extrapolating. The piping contribution there can only be higher
    than reported, which is why such a cell must never be quoted as an estimate
    and why a *failure* to reverse at one is weaker evidence than a reversal.

    Emitted into the record only when the list is non-empty. Under the matrix
    reading nothing is clamped at these four sections -- a fact gate 1 already
    proves, since it reproduces the published flag field for field -- so the
    matrix record stays byte-identical to the one this study first wrote.
    """
    cells: list[dict[str, Any]] = []
    for kp in BEP_KPS:
        for (river, seg_kp, scenario), row in baseline_rows.items():
            if river != "Tokachi" or seg_kp != kp:
                continue
            arms = sorted(
                arm
                for arm, rows in arm_rows.items()
                if bool(rows[(river, seg_kp, scenario)]["bep_clamped_above_grid"])
            )
            if not row["bep_clamped_above_grid"] and not arms:
                continue
            cells.append(
                {
                    "section": _label(kp),
                    "scenario": scenario,
                    "baseline_clamped": bool(row["bep_clamped_above_grid"]),
                    "arms_clamped": arms,
                    "reading": (
                        "the piping annual probability here is a LOWER BOUND, "
                        "not an estimate"
                    ),
                }
            )
    return cells


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


def evaluate_preregistration_bulk(
    sections: dict[str, Any],
    matrix_sections: dict[str, Any],
    lambda_yardstick: dict[str, Any],
    matrix_spans: dict[str, Any],
    scenarios,
) -> dict[str, Any]:
    """Score Part 3 section 3.1's predictions against the measured bulk record.

    Separate from :func:`evaluate_preregistration` on purpose. The bulk
    predictions are not the matrix ones re-run: under bulk the production lead is
    already overflow at five of eight cells, so the arm that can change an
    ordering is the upward one and several matrix predictions invert. Folding
    both into one scorer would have meant a statement string that reads
    differently depending on an argument, which is how a pre-registration
    quietly becomes a description.
    """
    labels = [_label(kp) for kp in BEP_KPS]

    def _cells():
        for lab in labels:
            for sc in scenarios:
                yield lab, sc

    def _changing(lab: str, sc: str) -> list[str]:
        return sections[lab][sc]["arms_changing_the_lead"]

    def _reversing(lab: str, sc: str) -> list[str]:
        return sections[lab][sc]["arms_reversing_the_lead"]

    upward_reversals = [
        {"section": lab, "scenario": sc}
        for lab, sc in _cells()
        if "k_aq_regional_upper" in _reversing(lab, sc)
    ]
    downward_reversals = [
        {"section": lab, "scenario": sc}
        for lab, sc in _cells()
        if set(_reversing(lab, sc)) & {"k_aq_field_geomean", "k_aq_field_toe"}
    ]

    # B7: climate ratio direction, same rule as the matrix P6.
    b7_rows = []
    for lab in labels:
        ratios = sections[lab]["climate_ratio_plus4k_over_historical"]
        base = ratios["baseline"]
        for arm in CONDUCTIVITY_ARMS:
            value = ratios.get(arm)
            if value is None or base is None:
                continue
            b7_rows.append(
                {
                    "section": lab,
                    "arm": arm,
                    "baseline_ratio": base,
                    "arm_ratio": value,
                    "moved_as_predicted": (value > base)
                    == (arm != "k_aq_regional_upper"),
                }
            )

    # B8: the control, and whether it is louder here than it was under matrix.
    b8_rows = []
    for lab, sc in _cells():
        entry = sections[lab][sc]
        base = entry["baseline"]["p_annual_system"]
        if base <= 0.0:
            continue
        shift = abs(entry["arms"][CONTROL_ARM]["p_annual_system"] / base - 1.0)
        b8_rows.append(
            {
                "section": lab,
                "scenario": sc,
                "control_relative_shift": float(shift),
                "under_two_percent": bool(shift < 0.02),
            }
        )

    # B9: wider than the matrix span, and wider than the length-effect bracket.
    b9_rows = []
    for lab, sc in _cells():
        span = sections[lab][sc]["conductivity_span_p_annual_system"]
        matrix_span = matrix_spans[lab][sc]
        yardstick = lambda_yardstick[lab][sc]
        b9_rows.append(
            {
                "section": lab,
                "scenario": sc,
                "bulk_span": span,
                "matrix_span": matrix_span,
                # ``None`` is an unbounded span (an arm gives exactly zero),
                # which is wider than any finite figure by definition.
                "wider_than_matrix": span is None
                or (matrix_span is not None and span > matrix_span),
                "wider_than_length_effect": span is None or span > yardstick,
            }
        )

    # C: the two brackets together.
    d70_flipped, restored, conductivity_changes_it = [], [], []
    for lab, sc in _cells():
        bulk_lead = sections[lab][sc]["baseline"]["leading_mechanism"]
        matrix_lead = matrix_sections[lab][sc]["baseline"]["leading_mechanism"]
        if bulk_lead != matrix_lead:
            d70_flipped.append({"section": lab, "scenario": sc})
            if "k_aq_regional_upper" in _reversing(lab, sc):
                restored.append({"section": lab, "scenario": sc})
            if _changing(lab, sc):
                conductivity_changes_it.append({"section": lab, "scenario": sc})

    invariant = [
        {
            "section": lab,
            "scenario": sc,
            "overflow_is_exactly_zero": (
                sections[lab][sc]["baseline"]["p_annual_overflow"] == 0.0
            ),
        }
        for lab, sc in _cells()
        if not _changing(lab, sc)
        and not matrix_sections[lab][sc]["arms_changing_the_lead"]
    ]

    return {
        "B1": {
            "statement": (
                "under bulk the contest is driven by the upward arm, not the "
                "downward ones"
            ),
            "held": bool(upward_reversals)
            and len(upward_reversals) >= len(downward_reversals),
            "cells_reversed_by_the_upward_arm": upward_reversals,
            "cells_reversed_by_a_downward_arm": downward_reversals,
        },
        "B2": {
            "statement": ("the upward arm reverses KP 57.4 +4K and KP 58.8 +4K"),
            "held": all(
                "k_aq_regional_upper" in _reversing(_label(kp), "+4K")
                for kp in (57.4, 58.8)
            ),
            "kp57_4_plus4k": "k_aq_regional_upper" in _reversing(_label(57.4), "+4K"),
            "kp58_8_plus4k": "k_aq_regional_upper" in _reversing(_label(58.8), "+4K"),
        },
        "B3": {
            "statement": "the upward arm does not reverse KP 62.0 in either climate",
            "held": not any(
                "k_aq_regional_upper" in _reversing(_label(62.0), sc)
                for sc in scenarios
            ),
        },
        "B4": {
            "statement": (
                "the matrix P4, that the upward arm reverses no ordering "
                "anywhere, does NOT replicate under bulk"
            ),
            "held": bool(upward_reversals),
            "note": "held here means the matrix prediction failed to replicate",
        },
        "B5": {
            "statement": (
                "KP 57.4 and KP 60.0 cannot REVERSE historically, overflow being "
                "exactly zero; KP 57.4 historical collapses under the lowest arm"
            ),
            "held": (
                not _reversing(_label(57.4), "historical")
                and not _reversing(_label(60.0), "historical")
                and "k_aq_field_geomean"
                in sections[_label(57.4)]["historical"]["arms_collapsing_to_undefined"]
            ),
            "kp57_4_historical_verdict": sections[_label(57.4)]["historical"][
                "ordering_verdict"
            ],
            "kp60_0_historical_verdict": sections[_label(60.0)]["historical"][
                "ordering_verdict"
            ],
        },
        "B6": {
            "statement": (
                "the lowest arm reverses KP 60.0 +4K, the one warmed cell piping "
                "still leads under bulk; the milder downward arm does not"
            ),
            "held": (
                "k_aq_field_geomean" in _reversing(_label(60.0), "+4K")
                and "k_aq_field_toe" not in _reversing(_label(60.0), "+4K")
            ),
            "arms_reversing": _reversing(_label(60.0), "+4K"),
        },
        "B7": {
            "statement": (
                "the climate ratio rises under the downward arms and falls "
                "under the upward arm"
            ),
            "held": all(row["moved_as_predicted"] for row in b7_rows),
            "cells": b7_rows,
        },
        "B8": {
            "statement": (
                "the blanket unit weight control changes no ordering and moves "
                "every annual number by under two per cent"
            ),
            "held": all(row["under_two_percent"] for row in b8_rows)
            and not any(CONTROL_ARM in _changing(lab, sc) for lab, sc in _cells()),
            "cells": b8_rows,
        },
        "B9": {
            "statement": (
                "the annualised conductivity span is wider under bulk than under "
                "matrix at every cell, and wider than the length-effect bracket"
            ),
            "held": all(row["wider_than_matrix"] for row in b9_rows),
            "wider_than_length_effect_everywhere": all(
                row["wider_than_length_effect"] for row in b9_rows
            ),
            "cells": b9_rows,
        },
        "C1": {
            "statement": (
                "the two brackets act on the same piping numerator in opposite "
                "directions: the bulk reading suppresses piping, the upward "
                "conductivity arm restores it"
            ),
            "held": bool(restored),
            "cells_where_the_grain_size_reading_flips_the_lead": d70_flipped,
            "cells_restored_to_piping_by_the_upward_arm": restored,
        },
        "C2": {
            "statement": (
                "at least one cell whose lead the bulk reading hands to overflow "
                "is restored to piping by the upward arm"
            ),
            "held": bool(restored),
        },
        "C3": {
            "statement": (
                "the conductivity bracket still changes the lead at every cell "
                "the grain-size reading flips"
            ),
            "held": len(conductivity_changes_it) == len(d70_flipped),
            "flipped_by_grain_size": len(d70_flipped),
            "also_changed_by_conductivity": len(conductivity_changes_it),
        },
        "C4": {
            "statement": (
                "across the union of both readings and the full bracket, the only "
                "cells whose lead is invariant are those where overflow is "
                "exactly zero"
            ),
            "held": all(cell["overflow_is_exactly_zero"] for cell in invariant),
            "invariant_cells": invariant,
        },
        "BF1": {
            "statement": (
                "no arm changes any lead under bulk (the bracket would be inert "
                "where the curves sit lowest; would indict the pipeline)"
            ),
            "fired": not any(_changing(lab, sc) for lab, sc in _cells()),
        },
        "BF2": {
            "statement": (
                "a cell whose overflow annual is exactly zero reports overflow "
                "as the leading mechanism (bug signature)"
            ),
            "fired": any(
                sections[lab][sc]["baseline"]["p_annual_overflow"] == 0.0
                and any(
                    sections[lab][sc]["arms"][arm]["leading_mechanism"] == "overflow"
                    for arm in sections[lab][sc]["arms"]
                )
                for lab, sc in _cells()
            ),
        },
        "BF3": {
            "statement": (
                "the bulk conductivity span is narrower than the matrix span at "
                "every cell (would refute B9)"
            ),
            "fired": all(not row["wider_than_matrix"] for row in b9_rows),
        },
        "BF5": {
            "statement": (
                "if B2 fails it fails at KP 58.8 +4K, which needs a factor of "
                "9.43 against a matrix multiplier of 2.81"
            ),
            "fired": "k_aq_regional_upper" not in _reversing(_label(58.8), "+4K"),
        },
    }


def compare_against_prior_side(
    sections: dict[str, Any], prior_sections: dict[str, Any], scenarios
) -> dict[str, Any]:
    """Cell-by-cell posterior-against-prior comparison of the same bracket.

    The prior-side numbers come from the committed evidence record rather than
    being recomputed here, so the two sides are compared on exactly the
    quantities the repository already published. ``span_ratio`` below 1 means
    the survival constraint NARROWED the bracket at that cell; above 1 means it
    widened it. ``None`` appears wherever a span is unbounded, which is a fact
    about an arm producing no failures at all and is never rendered as a number.
    """
    cells: dict[str, Any] = {}
    for kp in BEP_KPS:
        label = _label(kp)
        cells[label] = {}
        for scenario in scenarios:
            post = sections[label][scenario]
            prior = prior_sections[label][scenario]
            entry: dict[str, Any] = {
                "prior_span_p_annual_system": prior[
                    "conductivity_span_p_annual_system"
                ],
                "posterior_span_p_annual_system": post[
                    "conductivity_span_p_annual_system"
                ],
                "prior_span_p_annual_bep": prior["conductivity_span_p_annual_bep"],
                "posterior_span_p_annual_bep": post["conductivity_span_p_annual_bep"],
                "prior_ordering_verdict": prior["ordering_verdict"],
                "posterior_ordering_verdict": post["ordering_verdict"],
                "ordering_verdict_unchanged": (
                    prior["ordering_verdict"] == post["ordering_verdict"]
                ),
                "prior_arms_changing_the_lead": prior["arms_changing_the_lead"],
                "posterior_arms_changing_the_lead": post["arms_changing_the_lead"],
                "arms": {},
            }
            for span_field in ("p_annual_system", "p_annual_bep"):
                a = prior[f"conductivity_span_{span_field}"]
                b = post[f"conductivity_span_{span_field}"]
                entry[f"span_ratio_{span_field}"] = (
                    None if a in (None, 0.0) or b is None else b / a
                )
            # Per-arm posterior/prior movement, which is the mechanism: the
            # bracket can only move if the arms move unequally.
            for arm in ("baseline", *ARMS):
                prior_v = (
                    prior["baseline"] if arm == "baseline" else prior["arms"].get(arm)
                )
                post_v = (
                    post["baseline"] if arm == "baseline" else post["arms"].get(arm)
                )
                if prior_v is None or post_v is None:
                    continue
                entry["arms"][arm] = {
                    "prior_p_annual_system": prior_v["p_annual_system"],
                    "posterior_p_annual_system": post_v["p_annual_system"],
                    "posterior_over_prior_system": (
                        None
                        if prior_v["p_annual_system"] == 0.0
                        else post_v["p_annual_system"] / prior_v["p_annual_system"]
                    ),
                    "prior_p_annual_bep": prior_v["p_annual_bep"],
                    "posterior_p_annual_bep": post_v["p_annual_bep"],
                    "posterior_over_prior_bep": (
                        None
                        if prior_v["p_annual_bep"] == 0.0
                        else post_v["p_annual_bep"] / prior_v["p_annual_bep"]
                    ),
                }
            cells[label][scenario] = entry

        prior_ratios = prior_sections[label]["climate_ratio_plus4k_over_historical"]
        post_ratios = sections[label]["climate_ratio_plus4k_over_historical"]
        cells[label]["climate_ratio_plus4k_over_historical"] = {
            arm: {
                "prior": prior_ratios.get(arm),
                "posterior": post_ratios.get(arm),
                "posterior_over_prior": (
                    None
                    if not prior_ratios.get(arm) or post_ratios.get(arm) is None
                    else post_ratios[arm] / prior_ratios[arm]
                ),
            }
            for arm in sorted(set(prior_ratios) | set(post_ratios))
        }
    return cells


def evaluate_preregistration_posterior(
    sections: dict[str, Any],
    comparison: dict[str, Any],
    rejection: dict[str, Any],
    scenarios,
) -> dict[str, Any]:
    """Score the 2026-08-21 Part 1 predictions against the measured record.

    A third scorer rather than an argument on the first two, for the reason the
    bulk scorer already gives: a pre-registration whose statement string depends
    on a flag has stopped being a pre-registration.
    """
    labels = [_label(kp) for kp in BEP_KPS]

    def _cells():
        for lab in labels:
            for sc in scenarios:
                yield lab, sc

    def _rej(lab: str, arm: str) -> float:
        entry = rejection[lab].get(arm)
        # A partial --arms run scores only what it measured; a missing arm is
        # absent from the ladder rather than silently scored as zero, which
        # would let an incomplete run report P1 as held.
        return float("nan") if entry is None else float(entry["rejection_fraction"])

    full_ladder = (
        "k_aq_field_geomean",
        "k_aq_field_toe",
        "baseline",
        "k_aq_regional_upper",
    )
    ladder = tuple(a for a in full_ladder if a in rejection[labels[0]])
    monotone = {
        lab: len(ladder) == len(full_ladder)
        and all(
            _rej(lab, ladder[i]) <= _rej(lab, ladder[i + 1]) + 1e-12
            for i in range(len(ladder) - 1)
        )
        for lab in labels
    }
    narrowed = {
        (lab, sc): comparison[lab][sc]["span_ratio_p_annual_system"]
        for lab, sc in _cells()
    }
    resolved = {k: v for k, v in narrowed.items() if v is not None}
    ordering_held = {
        (lab, sc): comparison[lab][sc]["ordering_verdict_unchanged"]
        for lab, sc in _cells()
    }
    climate_shift = {
        (lab, arm): entry["posterior_over_prior"]
        for lab in labels
        for arm, entry in comparison[lab][
            "climate_ratio_plus4k_over_historical"
        ].items()
        if entry["posterior_over_prior"] is not None
    }
    arm_moves = {
        (lab, sc, arm): v["posterior_over_prior_system"]
        for lab, sc in _cells()
        for arm, v in comparison[lab][sc]["arms"].items()
        if v["posterior_over_prior_system"] is not None
    }
    downward = ("k_aq_field_geomean", "k_aq_field_toe")

    return {
        "P1_rejection_monotone_in_k_aq": {
            "statement": (
                "rejection fraction is monotone non-decreasing in the effective "
                "k_aq prior mean: geomean <= toe <= baseline <= regional_upper"
            ),
            "held": all(monotone.values()),
            "per_section": monotone,
        },
        "P2_upward_arm_rejects_materially_more": {
            "statement": (
                "k_aq_regional_upper rejects more than baseline at all four "
                "sections, and by more than a factor of two at KP 58.8 and "
                "KP 60.0"
            ),
            "held": all(
                _rej(lab, "k_aq_regional_upper") > _rej(lab, "baseline")
                for lab in labels
            )
            and all(
                _rej(lab, "k_aq_regional_upper") > 2.0 * _rej(lab, "baseline")
                for lab in (_label(58.8), _label(60.0))
            ),
            "rejection_fraction_by_arm": {
                lab: {
                    arm: _rej(lab, arm)
                    for arm in ("baseline", *ARMS)
                    if arm in rejection[lab]
                }
                for lab in labels
            },
        },
        "P3_kp62_stops_being_a_copy_of_the_prior_side": {
            "statement": (
                "at KP 62.0 the baseline rejects exactly 0, and "
                "k_aq_regional_upper is predicted to reject a non-zero fraction "
                "there, so the posterior side stops being a copy of the prior"
            ),
            "held": _rej(_label(62.0), "k_aq_regional_upper") > 0.0,
            "baseline_rejection": _rej(_label(62.0), "baseline"),
            "regional_upper_rejection": _rej(_label(62.0), "k_aq_regional_upper"),
        },
        "P4_downward_arms_inert_to_the_update": {
            "statement": (
                "both downward arms reject no more than baseline, and their "
                "annual numbers move less than the 12.4 % the baseline itself "
                "shows"
            ),
            "held": all(
                _rej(lab, arm) <= _rej(lab, "baseline") + 1e-12
                for lab in labels
                for arm in downward
            )
            and all(
                abs(v - 1.0) <= 0.124
                for (_lab, _sc, arm), v in arm_moves.items()
                if arm in downward
            ),
            "largest_downward_arm_movement": (
                max(
                    (
                        abs(v - 1.0)
                        for (_l, _s, a), v in arm_moves.items()
                        if a in downward
                    ),
                    default=0.0,
                )
            ),
        },
        "P5_posterior_span_narrower_and_by_less_than_two": {
            "statement": (
                "the posterior span of p_annual_system is smaller than the prior "
                "span at every cell where both are finite, and by less than a "
                "factor of two"
            ),
            "held": bool(resolved)
            and all(v < 1.0 for v in resolved.values())
            and all(v > 0.5 for v in resolved.values()),
            "span_ratio_posterior_over_prior": {
                f"{lab} {sc}": v for (lab, sc), v in narrowed.items()
            },
            "cells_resolved": len(resolved),
            "cells_unbounded": len(narrowed) - len(resolved),
        },
        "P6_ordering_verdicts_unchanged": {
            "statement": (
                "every ordering verdict of the prior-side record is reproduced "
                "on the posterior side"
            ),
            "held": all(ordering_held.values()),
            "cells_unchanged": sum(1 for v in ordering_held.values() if v),
            "cells_total": len(ordering_held),
            "cells_changed": [
                f"{lab} {sc}" for (lab, sc), v in ordering_held.items() if not v
            ],
        },
        "P7_climate_ratios_move_less_than_20_per_cent": {
            "statement": (
                "every arm's +4K/historical system ratio changes by less than "
                "20 % from its prior-side value"
            ),
            "held": all(abs(v - 1.0) < 0.20 for v in climate_shift.values()),
            "largest_shift": (
                max((abs(v - 1.0) for v in climate_shift.values()), default=0.0)
            ),
            "ratios_resolved": len(climate_shift),
        },
        "P8_unit_weight_control_stays_quiet": {
            "statement": (
                "gamma_bl_sub_lower rejects within a factor of two of baseline "
                "and changes no ordering anywhere"
            ),
            "held": all(
                _rej(lab, CONTROL_ARM) <= 2.0 * max(_rej(lab, "baseline"), 1e-9)
                for lab in labels
            )
            and not any(
                CONTROL_ARM in sections[lab][sc]["arms_changing_the_lead"]
                for lab, sc in _cells()
            ),
            "control_rejection": {lab: _rej(lab, CONTROL_ARM) for lab in labels},
        },
        "F1_no_posterior_exceeds_its_prior": {
            "statement": (
                "Accept-Reject can only remove realizations, so under nesting no "
                "arm's posterior annual number may exceed its prior one; a rise "
                "indicts the pipeline"
            ),
            "fired": any(v > 1.0 + 1e-12 for v in arm_moves.values()),
            "largest_ratio_seen": max(arm_moves.values(), default=0.0),
        },
        "F2_rejection_non_monotone": {
            "statement": "the rejection fraction is non-monotone in k_aq",
            "fired": not all(monotone.values()),
        },
        "F3_posterior_span_wider_than_prior": {
            "statement": (
                "the falsifier for H1: the posterior span is WIDER than the "
                "prior span at any cell"
            ),
            "fired": any(v > 1.0 for v in resolved.values()),
            "cells_wider": [
                f"{lab} {sc}"
                for (lab, sc), v in narrowed.items()
                if v is not None and v > 1.0
            ],
        },
        "F4_the_measured_null": {
            "statement": (
                "the deflating outcome: the span moves by less than 1 % at every "
                "cell, in which case the honest result is that the survival "
                "constraint leaves the bracket unchanged"
            ),
            "fired": bool(resolved)
            and all(abs(v - 1.0) < 0.01 for v in resolved.values()),
            "largest_span_movement": (
                max((abs(v - 1.0) for v in resolved.values()), default=0.0)
            ),
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
    return fs.save(fig, FIGURE_NAME["matrix"], mirror=out_dir / "figures")


def render_both_d70_figure(
    bulk: dict[str, Any], matrix: dict[str, Any], out_dir: Path
) -> Path:
    """The cross-reading answer: do the two brackets compound or offset?

    Both grain-size readings on one dominance axis, so the crossing of the
    equal-contribution line is visible rather than asserted, and so the reader
    can see that the two act on the same quantity in opposite directions. Cells
    whose piping number is a lower bound are marked, never quoted as estimates.

    No rendered text carries a decision identifier, a run identifier, a record
    field name or an em dash (conventions section 9.3.1).
    """
    import matplotlib.pyplot as plt

    fs = figstyle
    fs.style()
    fig, axes = plt.subplots(2, 4, figsize=(15.2, 7.4), sharey="row", sharex="col")

    labels = [_label(kp) for kp in BEP_KPS]
    reading_name = {"matrix": "matrix grain size", "bulk": "bulk grain size"}
    reading_style = {"matrix": ("-", "o"), "bulk": ("--", "s")}
    scenario_name = {"historical": "historical climate", "+4K": "4 K warming"}
    clamped = {
        (cell["section"], cell["scenario"])
        for cell in bulk.get("bep_clamped_cells", [])
    }

    for col, label in enumerate(labels):
        colour = fs.SECTION_COLORS[label.replace(" ", "")]
        for row, scenario in enumerate(("historical", "+4K")):
            ax = axes[row][col]
            for reading, payload in (("matrix", matrix), ("bulk", bulk)):
                entry = payload["sections"][label][scenario]
                linestyle, marker = reading_style[reading]
                points = []
                undefined = []
                for arm in CONDUCTIVITY_ARMS:
                    x = payload["arms"][arm][label]["effective_prior_mean"]
                    if entry["arms"][arm]["leading_mechanism"] == "not defined":
                        undefined.append(x)
                        continue
                    points.append((x, entry["arms"][arm]["share_bep"]))
                points.append(
                    (
                        payload["baseline_prior_mean_k_aq"][label],
                        entry["baseline"]["share_bep"],
                    )
                )
                points.sort()
                ax.plot(
                    [p[0] for p in points],
                    [p[1] for p in points],
                    color=colour,
                    lw=1.7,
                    linestyle=linestyle,
                    marker=marker,
                    ms=5.0,
                    mfc=colour if reading == "matrix" else fs.SURFACE,
                    zorder=3,
                )
                ax.plot(
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
                if undefined:
                    ax.plot(
                        undefined,
                        [0.0] * len(undefined),
                        linestyle="none",
                        marker="x",
                        ms=8,
                        mew=2.0,
                        color=fs.CRITICAL,
                        zorder=5,
                    )
            ax.axhline(0.5, color=fs.CRITICAL, lw=1.1, zorder=2)
            ax.set_xscale("log")
            ax.set_ylim(-0.06, 1.06)
            if (label, scenario) in clamped:
                # Tinted panel rather than a text label: these curves occupy
                # the top edge at one section and the bottom edge at another,
                # so every corner collides somewhere. The tint carries a
                # legend entry instead.
                ax.set_facecolor("#fbeeee")
            if row == 0:
                ax.set_title(label, fontsize=10.5)
            if row == 1:
                ax.set_xlabel("conductivity [m/s]", fontsize=9)
            if col == 0:
                ax.set_ylabel(f"{scenario_name[scenario]}\npiping share", fontsize=9.5)

    handles = [
        plt.Line2D(
            [],
            [],
            color=fs.INK_2,
            lw=1.7,
            linestyle=reading_style[r][0],
            marker=reading_style[r][1],
            ms=5.0,
            mfc=fs.INK_2 if r == "matrix" else fs.SURFACE,
            label=reading_name[r],
        )
        for r in ("matrix", "bulk")
    ]
    handles += [
        plt.Line2D(
            [],
            [],
            linestyle="none",
            marker="o",
            ms=9,
            mfc="none",
            mec=fs.INK,
            mew=1.2,
            label="production value",
        ),
        plt.Line2D([], [], color=fs.CRITICAL, lw=1.1, label="equal contribution"),
        plt.Line2D(
            [],
            [],
            linestyle="none",
            marker="x",
            ms=8,
            mew=2.0,
            color=fs.CRITICAL,
            label="no mechanism loaded, share undefined",
        ),
        plt.Rectangle(
            (0, 0),
            1,
            1,
            facecolor="#fbeeee",
            edgecolor=fs.MUTED,
            lw=0.6,
            label="tinted panel: piping is a lower bound",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.095),
        ncol=3,
        fontsize=9.0,
    )
    fig.suptitle(
        "Which mechanism leads, across the conductivity bracket, under both "
        "grain-size readings",
        fontsize=12.5,
    )
    fig.text(
        0.5,
        0.012,
        "Above the line piping leads; below it overflow does. The two readings "
        "move the same piping contribution in opposite directions, so raising "
        "conductivity can restore a lead the bulk reading removes.",
        ha="center",
        fontsize=8.5,
        color=fs.MUTED,
    )
    fig.tight_layout(rect=(0, 0.135, 1, 1))
    return fs.save(fig, FIGURE_NAME["bulk"], mirror=out_dir / "figures")


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
        "--d70",
        default=DEFAULT_D70,
        choices=list(D70_CHOICES),
        help=(
            "Grain-size reading to propagate. The two are co-primary "
            "deliverables, not a result and a sensitivity (default: matrix)."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Evidence JSON output path (default: the record for the reading).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Study-local output directory (gitignored).",
    )
    parser.add_argument(
        "--side",
        default=DEFAULT_SIDE,
        choices=list(SIDE_CHOICES),
        help=(
            "Which side of the Bayesian update to carry the arms through. "
            "'prior' (default) reproduces the 2026-08-10 records; 'posterior' "
            "replays each arm against the 2016 survival record first."
        ),
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
    d70 = args.d70
    side = args.side
    if args.out is None:
        args.out = DEFAULT_OUT[(side, d70)]
    if args.out_dir is None:
        args.out_dir = DEFAULT_OUT_DIR[(side, d70)]

    if args.figures_only:
        if side != "prior":
            parser.error(
                "--figures-only is a prior-side path: the posterior-side record "
                "carries no figure of its own."
            )
        payload = json.loads(args.out.read_text(encoding="utf-8"))
        if d70 == "bulk":
            # The bulk figure is the cross-reading comparison, so it reads the
            # committed matrix record too. Both are tracked evidence.
            matrix_payload = json.loads(
                DEFAULT_OUT[("prior", "matrix")].read_text(encoding="utf-8")
            )
            path = render_both_d70_figure(payload, matrix_payload, args.out_dir)
        else:
            path = render_figure(payload, args.out_dir)
        print(f"wrote {_rel(path)} (figure only; no record written)")
        return 0

    started = time.time()
    campaign = _load_campaign_module()
    cache_before = _cache_state(campaign.HAZARD_CACHE)

    print("building registry, surface curves and node hazard ...", flush=True)
    context = build_context(campaign, d70, side)

    # On the posterior side the acceptance rule itself is part of the
    # comparison, so it is gated against the production campaign's own settings
    # for the baseline as well as for every arm.
    phase2_reference = _production_phase2_settings(d70) if side == "posterior" else None
    rejection: dict[str, dict[str, Any]] = {}
    if phase2_reference is not None:
        for kp in BEP_KPS:
            rejection[_label(kp)] = {
                "baseline": _posterior_provenance(kp, None, d70, phase2_reference)
            }

    print(f"baseline pass, {d70} reading, {side} side (gate 1) ...", flush=True)
    baseline_rows, baseline_coverage, baseline_driving = annualise_variant(
        campaign, context, context["baseline_curves"], d70, side
    )
    gate1 = gate_one(baseline_rows, d70, side)
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
            # The Phase 1 provenance is checked on both sides: a posterior is
            # only as sound as the sweep it was filtered from.
            arm_provenance[arm][label] = _arm_provenance(kp, arm, d70)
            if phase2_reference is not None:
                phase2 = _posterior_provenance(kp, arm, d70, phase2_reference)
                arm_provenance[arm][label]["phase2"] = phase2
                rejection[label][arm] = phase2
            curve = load_bep_curve(
                _arm_curve_path(kp, arm, d70, side), branch="transient"
            )
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
            campaign, context, curves, d70, side
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
                    and r["d70"] == d70
                    and r["bep_source"] == "posterior"
                    and r["surface_variant"] == SURFACE_VARIANT
                    and float(r["lambda_ac_m"]) == lam
                )

            lambda_yardstick[label][scenario] = _p(40.0) / _p(250.0)

    matrix_payload = (
        None
        if d70 == "matrix" or side == "posterior"
        else json.loads(DEFAULT_OUT[("prior", "matrix")].read_text(encoding="utf-8"))
    )
    comparison: dict[str, Any] | None = None
    if side == "posterior":
        # GATE 7's other half: the prior-side record this is measured against is
        # the committed one, read rather than recomputed, so the difference
        # reported is the update and nothing else.
        prior_record = DEFAULT_OUT[("prior", d70)]
        if not prior_record.is_file():
            raise FileNotFoundError(
                f"missing prior-side record {_rel(prior_record)}; the posterior "
                "side is defined only against it."
            )
        prior_payload = json.loads(prior_record.read_text(encoding="utf-8"))
        comparison = compare_against_prior_side(
            sections, prior_payload["sections"], list(campaign.SCENARIOS)
        )
        prereg = evaluate_preregistration_posterior(
            sections, comparison, rejection, list(campaign.SCENARIOS)
        )
    elif matrix_payload is None:
        prereg = evaluate_preregistration(
            sections, lambda_yardstick, list(campaign.SCENARIOS)
        )
    else:
        prereg = evaluate_preregistration_bulk(
            sections,
            matrix_payload["sections"],
            lambda_yardstick,
            {
                label: {
                    scenario: matrix_payload["sections"][label][scenario][
                        "conductivity_span_p_annual_system"
                    ]
                    for scenario in campaign.SCENARIOS
                }
                for label in (_label(kp) for kp in BEP_KPS)
            },
            list(campaign.SCENARIOS),
        )

    clamped = clamped_cells(baseline_rows, arm_rows)

    payload: dict[str, Any] = {
        "study": (
            "Aquifer-conductivity epistemic bracket propagated through the "
            "Phase 3 annualisation (defence-brief item A2)"
            if side == "prior"
            else (
                "Aquifer-conductivity epistemic bracket measured on the "
                "POSTERIOR side of the 2016 survival update"
            )
        ),
        "generated_by": "scripts/conductivity_annualisation_study.py",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "note": (
            "docs/decisions/conductivity-bracket-annualisation.md"
            if side == "prior"
            else "docs/decisions/conductivity-bracket-posterior-side.md"
        ),
        "scope": {
            "d70_interpretation": d70,
            "bep_source": side,
            "lambda_ac_m": LAMBDA_AC_M,
            "surface_variant": SURFACE_VARIANT,
            "scenarios": list(campaign.SCENARIOS),
            "sections": [_label(kp) for kp in BEP_KPS],
            "statement": SCOPE_STATEMENT[(side, d70)],
        },
        "gates": {
            "gate_1_reproduces_production_table": gate1,
            "gate_2_arm_provenance": {
                "passed": True,
                "criterion": (
                    "grid equal to baseline, N = 1e5, config hash round-trips, "
                    "expected prior_mean_scenario label"
                    + (
                        ""
                        if side == "prior"
                        else "; Phase 2 settings identical to the production "
                        "campaign in every field but the output path"
                    )
                ),
            },
            "gate_3_non_bep_segments_invariant": gate3,
            "gate_4_hazard_cache_unchanged": {
                "passed": True,
                "cache_files": len(cache_after),
            },
            "gate_5_no_production_artifact_written": {
                "passed": True,
                "writes": [_rel(args.out), _rel(args.out_dir)]
                + ([] if side == "posterior" else [f"docs/figures/{FIGURE_NAME[d70]}"]),
            },
            **(
                {}
                if side == "prior"
                else {
                    "gate_6_theta_verified_on_every_replay": {
                        "passed": True,
                        "criterion": (
                            "every Phase 2 replay ran with verify_by_reevaluation, "
                            "so each arm regenerated its OWN shifted population "
                            "(ADR-0048 decision 3) rather than the baseline one"
                        ),
                        "replays_checked": sum(len(v) for v in rejection.values()),
                    },
                    "gate_7_prior_side_record_is_the_committed_one": {
                        "passed": True,
                        "criterion": (
                            "the prior-side comparison numbers are read from the "
                            "committed evidence record, not recomputed here"
                        ),
                        "record": _rel(DEFAULT_OUT[("prior", d70)]),
                        "record_generated": prior_payload["generated"],
                    },
                }
            ),
        },
        "arms": arm_provenance,
        "baseline_prior_mean_k_aq": {
            _label(kp): float(
                Config.model_validate(
                    json.loads(
                        _baseline_sweep(kp, d70)
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
    # Posterior-side only, so the prior-side records keep their exact key set.
    if side == "posterior":
        payload["survival_update"] = {
            "definition": (
                "Phase 2 Accept-Reject against the 2016 typhoon survival "
                "record, per arm; rejection_fraction is the share of the N = 1e5 "
                "prior realizations that would have breached under that event "
                "and is the mechanism behind everything the bracket does here"
            ),
            "by_section": {
                label: {
                    arm: {
                        "rejection_fraction": entry["rejection_fraction"],
                        "n_accepted": entry["n_accepted"],
                    }
                    for arm, entry in arms.items()
                }
                for label, arms in rejection.items()
            },
        }
        payload["posterior_vs_prior"] = comparison
    # Emitted only when non-empty, which keeps the matrix record byte-identical
    # to the one this study first wrote: no matrix cell at these four sections
    # is clamped, and gate 1 proves it by reproducing the published flag.
    if clamped:
        payload["bep_clamped_cells"] = clamped

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
    print(f"\nwrote {_rel(args.out)}")

    # The posterior side carries no figure of its own: its finding is a
    # comparison of two spans and a rejection ladder, both of which a table
    # states completely. A second conductivity figure would make the same point
    # as the first with one arm moved, which is the definition of a float that
    # has not earned its place.
    if not args.no_figure and side == "prior":
        path = (
            render_figure(payload, args.out_dir)
            if matrix_payload is None
            else render_both_d70_figure(payload, matrix_payload, args.out_dir)
        )
        print(f"wrote {_rel(path)}")

    if side == "posterior":
        print("\nrejection fraction by arm (the mechanism)")
        for kp in BEP_KPS:
            label = _label(kp)
            cells = "  ".join(
                f"{arm.replace('k_aq_', '').replace('gamma_bl_sub_', 'gamma '):>14s}"
                f" {100.0 * rejection[label][arm]['rejection_fraction']:6.3f}%"
                for arm in (
                    "k_aq_field_geomean",
                    "k_aq_field_toe",
                    "baseline",
                    "k_aq_regional_upper",
                    CONTROL_ARM,
                )
                if arm in rejection[label]
            )
            print(f"  {label:<8} {cells}")
        print("\nbracket span, prior against posterior")
        for kp in BEP_KPS:
            label = _label(kp)
            for scenario in campaign.SCENARIOS:
                cell = comparison[label][scenario]
                pri = cell["prior_span_p_annual_system"]
                post = cell["posterior_span_p_annual_system"]
                ratio = cell["span_ratio_p_annual_system"]
                print(
                    f"  {label:<8} {scenario:<11} prior "
                    f"{'unbnd' if pri is None else format(pri, '.4g'):>9}  "
                    f"posterior {'unbnd' if post is None else format(post, '.4g'):>9}"
                    f"  ratio {'n/d' if ratio is None else format(ratio, '.4g'):>8}"
                    f"  ordering "
                    f"{'unchanged' if cell['ordering_verdict_unchanged'] else 'MOVED'}"
                )

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
    for key, entry in prereg.items():
        if "held" in entry:
            print(f"  {key}: {'HELD' if entry['held'] else 'FAILED'}")
    for key, entry in prereg.items():
        if "fired" in entry:
            print(f"  {key}: {'FIRED' if entry['fired'] else 'did not fire'}")
    if clamped:
        print(
            "\ncells whose piping annual probability is a LOWER BOUND "
            "(transition not bracketed, so the raw tail is held above the grid)"
        )
        for cell in clamped:
            print(
                f"  {cell['section']:<8} {cell['scenario']:<11} "
                f"baseline {'clamped' if cell['baseline_clamped'] else 'clear':<8} "
                f"arms {','.join(cell['arms_clamped']) or '-'}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
