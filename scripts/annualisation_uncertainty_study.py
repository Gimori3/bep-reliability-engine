"""Hazard-sampling uncertainty on the Phase 3 annualised results.

Companion study for `docs/decisions/annualisation-hazard-sampling-uncertainty.md`
(Part 1 pre-registered 2026-08-20, committed before this driver existed). Chapter 7
concedes that no sampling uncertainty is attached to any annual probability or
climate ratio, and then quotes climate ratios to three significant figures, a
KP 62.0 mechanism split to three decimals and a 43-fold margin at KP 58.8, none of
them with an interval. This puts an interval on each of them.

SCOPE, and it travels with every number below
---------------------------------------------
**Hazard-sampling uncertainty only: the finite-ensemble spread of the d4PDF
peak-stage distribution with the fragility curves held fixed, which is not the
total uncertainty and is far smaller than the aquifer-conductivity bracket that
dominates it and does not cancel.** The conductivity bracket is measured in
`conductivity-bracket-annualisation.md` and moves the KP 58.8 historical piping
contribution by a factor of about 1.8e4; nothing here approaches that.

What it does
------------
Re-composes the Phase 3 segment fragility from the persisted artifacts, evaluates
each composed curve at every ensemble event peak, and block-bootstraps the
annualisation mean. Nothing is re-swept, no hydrograph workbook is streamed and
no Phase 3 output is rewritten: the persisted sweeps, the persisted posteriors and
the warm hazard cache are read-only inputs.

The resampling unit is the **d4PDF ensemble member**, not the simulated year. The
3,000 historical and 5,400 warming events are nested exactly 60-per-member inside
50 and 90 members (the warming member being an SST-pattern and member pair), so
the years are not independent draws and an i.i.d. bootstrap over them is not a
resample of the ensemble's independent units. All 114 nodes carry the identical
event sequence, so one block draw per scenario applies at every node and every
between-node comparison is paired.

Gates (pre-registered; a failure aborts rather than being tabulated)
-------------------------------------------------------------------
0. Every per-event probability vector's unresampled mean equals the production
   ``AnnualizedResult`` field EXACTLY, so the bootstrap provably resamples the
   production quantity rather than a lookalike.
1. The unresampled baseline reproduces ``rq4_annual.csv`` string-identically over
   all four 250 m / primary arms, 228 rows each, 912 rows, every field.
2. The hazard cache is byte-unchanged afterwards (SHA-256 per file).
3. Nothing outside this study's own output directory is written: the Phase 3
   output directory is asserted byte-unchanged too.

Why a standalone companion rather than a ``phase3_campaign.py`` variant axis: the
campaign's no-argument call must stay byte-identical, and an interval is not a
variant of the annualisation, it is a statement about it. The composition step is
**imported** from the campaign, never re-implemented, so gate 1 tests the
production code path; ``tests/test_annualisation_uncertainty.py`` forbids a
second copy.

Usage (repo root, venv active)::

    python scripts/annualisation_uncertainty_study.py
    python scripts/annualisation_uncertainty_study.py --out somewhere.json

``--figures-only`` is deliberately absent: this study owns no figure. The
intervals are drawn onto the existing RQ4 headline figure by
``scripts/phase3_figures.py``, which reads this study's committed record and is
already declared in the campaign's ``FIGURE_DRIVERS`` with a real redraw path.
"""

from __future__ import annotations

import argparse
import csv
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

from system_integration.annualize import (  # noqa: E402
    _curve_interpolators,
    annualize,
    stratified_annual_p_f,
)
from system_integration.bep_input import load_bep_curve  # noqa: E402
from system_integration.hazard import load_reach_hazard  # noqa: E402
from system_integration.segments import build_registry, load_section_table  # noqa: E402
from system_integration.surface_curves import (  # noqa: E402
    SurfaceCurveSet,
    load_surface_curves,
)
from system_integration.uemura_models import load_segment_inputs  # noqa: E402

DECISIONS = REPO_ROOT / "docs" / "decisions"
DEFAULT_OUT = DECISIONS / "annualisation-hazard-sampling-uncertainty.json"
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "annualisation_uncertainty"
NOTE = "docs/decisions/annualisation-hazard-sampling-uncertainty.md"
PRODUCTION_TABLE = (
    REPO_ROOT / "results" / "system_integration" / "phase3" / "rq4_annual.csv"
)
ATTRIBUTION_TABLE = (
    REPO_ROOT / "results" / "system_integration" / "phase3" / "rq4_attribution.json"
)
PHASE3_DIR = REPO_ROOT / "results" / "system_integration" / "phase3"

#: Pre-registration section 1.2. Fixed; the study is deterministic given it.
SEED = 20260820
REPLICATES = 10_000

#: Pre-registration section 1.1: the rest of the variant axis, fixed so it
#: cannot drift. Only the 250 m / primary arm is intervalled; the lambda_ac and
#: surface-variant companions are bracket axes measured elsewhere.
LAMBDA_AC_M = 250.0
SURFACE_VARIANT = "primary"

#: The four gated arms. The first is primary: it is what Chapter 7's system
#: annual table prints. The prior arm is the one the conductivity companion and
#: the 43-fold KP 58.8 margin are measured on, and both grain-size readings are
#: co-primary, so all four are gated and all four are reported.
ARMS: tuple[tuple[str, str], ...] = (
    ("matrix", "posterior"),
    ("matrix", "prior"),
    ("bulk", "posterior"),
    ("bulk", "prior"),
)
PRIMARY_ARM = ("matrix", "posterior")

BEP_KPS: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0)
MECHANISMS: tuple[str, ...] = ("bep", "overflow", "fluvial_scour")

#: Pre-registration section 1.6. The member unit is the estimator; the other
#: three are declared sensitivities on the choice of resampling unit and are
#: never quoted as the hazard-sampling interval.
RESAMPLING_UNITS: tuple[str, ...] = ("member", "event", "year", "sst")

#: Pre-registration section 3.3, fixed 2026-08-20 and committed in aeeb918
#: BEFORE this file carried a line of stratified code. The unit is the MEMBER
#: BLOCK, not the simulated year: a stratum's information is carried by the
#: blocks that hold at least one of its events.
#:
#: F1, occupancy: at least this many carrying blocks. Twenty is where the
#: probability of a replicate containing none of them, about e^-m, reaches
#: 2.1e-9, so no replicate is ever discarded, AND where one block's leverage
#: 1/m reaches the project's standing 5 % Monte Carlo tolerance (ADR-0031,
#: ADR-0032).
STRATUM_BLOCK_FLOOR = 20
#: F2, concentration: no single block may hold more than this share of the
#: stratum. F1 bounds the AVERAGE block weight; an average hides concentration.
#: Expected not to bind; whether it did is reported either way.
STRATUM_MAX_BLOCK_SHARE = 0.20
#: Section 3.6 Q6. The verdict is additionally scored at these floors, reported
#: and never used to choose. Scored as the MEMBERSHIP of the clearing set, not
#: as intervals for cells the pre-registered floor excludes: section 3.4 forbids
#: printing one below the floor, and a sensitivity is not an exemption from it.
FLOOR_SENSITIVITY: tuple[int, ...] = (10, 30)

#: The two stratifications of Table ``tab: rq4 attribution``. The record keys
#: mirror ``rq4_attribution.json`` so gate 4 compares field for field, and the
#: predicates are the campaign's own (``phase3_campaign.main``), not lookalikes.
STRATIFIERS: tuple[dict[str, Any], ...] = (
    {
        "name": "duration",
        "definition": "hours_above_datum > 24 h",
        "predicate": lambda e: e.hours_above_datum > 24.0,
        "inside_key": "p_f_long_loading",
        "outside_key": "p_f_short_loading",
        "count_key": "n_long",
        "quotes": (
            "the concentration-factor range 151 to 378 and the 89 and 93 per "
            "cent share claim"
        ),
    },
    {
        "name": "compound",
        "definition": "n_peaks_above_datum >= 2",
        "predicate": lambda e: e.n_peaks_above_datum >= 2,
        "inside_key": "p_f_compound",
        "outside_key": "p_f_noncompound",
        "count_key": "n_compound",
        "quotes": "the 3.7 to 91 historically and 1.6 to 23 under warming ranges",
    },
)

#: Gate 4a's bound. Bit-identity is NOT achievable here and is not asserted:
#: the block-grouped sum reorders the same addends that ``np.mean`` adds
#: pairwise, so the difference is floating-point ordering, not quantity. The
#: measured deviation is recorded next to the bound (toolkit recipe 8).
UNRESAMPLED_TOLERANCE = 1e-12

SCOPE_STATEMENT = (
    "Hazard-sampling uncertainty ONLY: the finite-ensemble spread of the d4PDF "
    "peak-stage distribution with the fragility curves held fixed, which is not "
    "the total uncertainty and is far smaller than the aquifer-conductivity "
    "bracket that dominates it and does not cancel. Quote this scope wherever "
    "any number here is quoted."
)


def _load_campaign_module():
    """Import ``scripts/phase3_campaign.py`` for its composition step.

    Gate 1 asserts this study reproduces the production table exactly, which is
    only meaningful if the composition it exercises IS the production one. A
    second copy could drift. Same ``importlib`` route
    ``scripts/conductivity_annualisation_study.py`` uses.
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
def _label(kp: float) -> str:
    """Display label for a section, through the one shared conversion.

    ``_figstyle.section_label`` is the single place a run identifier becomes a
    river kilometre (conventions section 9.3.1), so the record, the figure and
    the thesis handoff key off the same string and cannot drift apart.
    """
    return figstyle.section_label(f"tokachi_kp{kp:.1f}")


def _rel(path: Path) -> str:
    """Repo-relative path where possible, absolute otherwise."""
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


def _dir_state(directory: Path, pattern: str = "*") -> dict[str, str]:
    if not directory.is_dir():
        return {}
    return {p.name: _sha256(p) for p in sorted(directory.glob(pattern)) if p.is_file()}


def _arm_key(d70: str, source: str) -> str:
    return f"{d70}/{source}"


# --------------------------------------------------------------------------- #
# Ensemble structure                                                            #
# --------------------------------------------------------------------------- #
def block_labels(event_ids: list[str], unit: str) -> np.ndarray:
    """Resampling-unit label per event.

    The d4PDF member header is ``<prefix>_m<NNN>_<year>``; the prefix is ``HPB``
    historically and ``HFB_<SST>`` under warming, so splitting from the right
    separates the three axes without assuming how many tokens the prefix has.

    Parameters
    ----------
    event_ids : list of str
        Verbatim member headers, workbook order.
    unit : {'member', 'event', 'year', 'sst'}
        ``member`` is the estimator's block (the prefix-and-member pair, so the
        warming block is one SST pattern's one member). The other three are the
        pre-registered sensitivities on the choice of unit.

    Returns
    -------
    numpy.ndarray
        One label per event, dtype object.
    """
    parts = [event_id.rsplit("_", 2) for event_id in event_ids]
    if any(len(p) != 3 for p in parts):
        raise ValueError(
            "an event id does not carry the <prefix>_m<NNN>_<year> grammar; "
            "the resampling unit cannot be derived from it"
        )
    if unit == "member":
        labels = [f"{prefix}_{member}" for prefix, member, _ in parts]
    elif unit == "year":
        labels = [year for _, _, year in parts]
    elif unit == "sst":
        labels = [prefix for prefix, _, _ in parts]
    elif unit == "event":
        labels = list(event_ids)
    else:  # pragma: no cover - defensive
        raise ValueError(f"unknown resampling unit {unit!r}")
    return np.asarray(labels, dtype=object)


def block_index(labels: np.ndarray) -> tuple[np.ndarray, int, list[int]]:
    """(per-event block index, block count, block sizes)."""
    _, inverse = np.unique(labels, return_inverse=True)
    sizes = np.bincount(inverse).tolist()
    return inverse, len(sizes), sizes


def ensemble_structure(event_ids: list[str]) -> dict[str, Any]:
    """The measured nesting, recorded so the estimator choice is checkable."""
    record: dict[str, Any] = {"n_events": len(event_ids)}
    for unit in RESAMPLING_UNITS:
        if unit == "event":
            continue
        labels = block_labels(event_ids, unit)
        _, n_blocks, sizes = block_index(labels)
        record[unit] = {
            "n_blocks": n_blocks,
            "events_per_block": sorted(set(sizes)),
            "balanced": len(set(sizes)) == 1,
        }
    return record


def draw_multiplicities(n_blocks: int, replicates: int, rng) -> np.ndarray:
    """Bootstrap block multiplicities, ``(replicates, n_blocks)``.

    Drawing block counts from ``Multinomial(K, uniform)`` is exactly the
    with-replacement draw of K blocks, and it turns a replicate into one row of
    a matrix product against the per-block sums. Held as ``int32`` so the same
    draw can be shared by all 114 nodes without a memory cost.
    """
    counts = rng.multinomial(n_blocks, np.full(n_blocks, 1.0 / n_blocks), replicates)
    return counts.astype(np.int32)


def replicate_means(
    block_sums: np.ndarray, multiplicities: np.ndarray, n_events: int
) -> np.ndarray:
    """Replicate annual means, ``(replicates, n_curves)``.

    ``block_sums`` is ``(n_blocks, n_curves)``; a replicate's mean is its block
    multiplicities dotted into those sums, divided by the (fixed, because the
    design is balanced) resampled event count.
    """
    return (multiplicities.astype(np.float64) @ block_sums) / float(n_events)


def block_sums(per_event: np.ndarray, index: np.ndarray, n_blocks: int) -> np.ndarray:
    """Per-block sums of an ``(n_events, n_curves)`` probability matrix."""
    out = np.zeros((n_blocks, per_event.shape[1]), dtype=np.float64)
    np.add.at(out, index, per_event)
    return out


def chunked_replicate_means(
    sums: np.ndarray,
    n_blocks: int,
    n_events: int,
    replicates: int,
    rng,
    chunk: int = 1000,
) -> np.ndarray:
    """Replicate means without holding the whole multiplicity matrix.

    Used by the resampling-unit sensitivity, whose i.i.d.-over-events arm has
    one block per event: a full ``(replicates x n_events)`` multiplicity matrix
    would be hundreds of megabytes, while a chunk is tens. The draw is not
    shared across nodes here, because the sensitivity reports marginal widths
    rather than paired differences.
    """
    out = np.empty((replicates, sums.shape[1]), dtype=np.float64)
    done = 0
    while done < replicates:
        take = min(chunk, replicates - done)
        counts = draw_multiplicities(n_blocks, take, rng)
        out[done : done + take] = replicate_means(sums, counts, n_events)
        done += take
    return out


def percentile_interval(samples: np.ndarray) -> tuple[float, float]:
    """Two-sided 95 % percentile interval (pre-registration section 1.3)."""
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return float(lo), float(hi)


def _interval(point: float, samples: np.ndarray) -> dict[str, float]:
    """Point estimate plus its interval. The point is never a bootstrap mean."""
    lo, hi = percentile_interval(samples)
    return {
        "point": float(point),
        "ci_low": lo,
        "ci_high": hi,
        "relative_half_width": (
            float(0.5 * (hi - lo) / point) if point > 0.0 else None
        ),
    }


# --------------------------------------------------------------------------- #
# Pipeline                                                                      #
# --------------------------------------------------------------------------- #
def build_context(campaign) -> dict[str, Any]:
    """Registry, surface curves, BEP curves and per-node hazard.

    Built exactly as ``phase3_campaign.main`` builds them, including the node
    exposure datum, which the campaign reads from the **matrix posterior** curve
    whatever arm is being composed. Reproducing that choice is what keeps the
    warm hazard cache valid, and gate 2 proves no cache entry was rewritten.
    """
    registry = load_section_table(
        campaign.SECTION_TABLE, build_registry(campaign.DATA_ROOT), allow_gaps=True
    )
    seg_inputs = load_segment_inputs(campaign.SEGMENT_INPUTS)
    parts = [load_surface_curves(path) for path in campaign.PRIMARY_FILES]
    surface = SurfaceCurveSet(
        curves=tuple(c for part in parts for c in part.curves), source="uemura_csv"
    )

    bep_curves: dict[tuple[float, str, str], Any] = {}
    for segment in registry.bep_segments():
        for d70 in ("matrix", "bulk"):
            for source in ("posterior", "prior"):
                bep_curves[(segment.kp, d70, source)] = load_bep_curve(
                    campaign._bep_path(segment.kp, d70, source), branch="transient"
                )

    nodes = []
    for segment in registry.segments:
        if segment.bep_source_kp is not None:
            datum = bep_curves[(segment.kp, "matrix", "posterior")].datum_m
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
        "bep_curves": bep_curves,
        "hazards": hazards,
    }


def annualise_arm(campaign, context: dict[str, Any], d70: str, source: str) -> tuple[
    dict[tuple[str, float, str], dict[str, Any]],
    dict[tuple[str, float, str], dict[str, np.ndarray]],
]:
    """One 114-segment composition and annualisation pass, with per-event values.

    Returns ``(rows, per_event)``. ``rows`` carries the campaign's own field set
    so gate 1 can compare it against ``rq4_annual.csv`` field for field.
    ``per_event`` carries, per node and scenario, the composed system curve and
    each present mechanism's curve evaluated at every ensemble event peak: the
    matrix the bootstrap resamples. Gate 0 checks its unresampled mean against
    the ``AnnualizedResult`` field it must reproduce.
    """
    n_eff = max(1.0, campaign.SEGMENT_LENGTH_M / LAMBDA_AC_M)
    rows: dict[tuple[str, float, str], dict[str, Any]] = {}
    per_event: dict[tuple[str, float, str], dict[str, np.ndarray]] = {}
    gate0_failures: list[str] = []

    for segment in context["registry"].segments:
        bep = (
            context["bep_curves"][(segment.kp, d70, source)]
            if segment.bep_source_kp is not None
            else None
        )
        frag, clamped = campaign._compose_segment(
            segment, context["surface"], bep, n_eff, "historical"
        )
        if frag is None:
            continue
        key = (segment.river, round(segment.kp, 3))
        interpolators = _curve_interpolators(frag)
        for scenario in campaign.SCENARIOS:
            hazard = context["hazards"][scenario][key]
            annual = annualize(frag, hazard)
            peaks = hazard.peak_stages()

            values = {"__system__": np.asarray(interpolators["__system__"](peaks))}
            for mechanism in frag.mechanisms:
                values[mechanism] = np.asarray(interpolators[mechanism](peaks))

            # GATE 0. The unresampled mean of the matrix the bootstrap will
            # resample must BE the published annual number, bit for bit.
            if float(np.mean(values["__system__"])) != annual.p_f_annual_system:
                gate0_failures.append(f"{key} {scenario} system")
            for mechanism in frag.mechanisms:
                published = annual.p_f_annual_per_mechanism[mechanism]
                if float(np.mean(values[mechanism])) != published:
                    gate0_failures.append(f"{key} {scenario} {mechanism}")

            row: dict[str, Any] = {
                "river": segment.river,
                "kp": segment.kp,
                "section_id": segment.section_id or "",
                "scenario": scenario,
                "d70": d70,
                "bep_source": source,
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
            for mechanism in MECHANISMS:
                row[f"p_annual_{mechanism}"] = annual.p_f_annual_per_mechanism.get(
                    mechanism, ""
                )
                row[f"share_{mechanism}"] = (
                    annual.dominance_share(mechanism)
                    if mechanism in frag.mechanisms
                    else ""
                )
            rows[(segment.river, segment.kp, scenario)] = row
            per_event[(segment.river, segment.kp, scenario)] = values

    if gate0_failures:
        raise AssertionError(
            "GATE 0 FAILED: this study's per-event probability matrix does not "
            "average to the production annual number at "
            f"{len(gate0_failures)} node-scenario-curve cells, so the bootstrap "
            "would be resampling a lookalike rather than the production "
            "quantity.\n  " + "\n  ".join(gate0_failures[:20])
        )
    return rows, per_event


def gate_one(rows_by_arm: dict[str, dict[tuple[str, float, str], dict[str, Any]]]):
    """Assert the unresampled baseline reproduces the production table EXACTLY.

    The production CSV writes ``str(value)``, so a stringified comparison is an
    exact float comparison that also covers the ``""`` empty-mechanism cells and
    the boolean flags. All four 250 m / primary arms are compared, 228 rows
    each: the matrix/prior arm the pre-registration names, the matrix/posterior
    arm Chapter 7's table actually prints, and both bulk co-primaries.
    """
    with open(PRODUCTION_TABLE, encoding="utf-8", newline="") as handle:
        published = list(csv.DictReader(handle))

    mismatches: list[str] = []
    per_arm: dict[str, int] = {}
    fields_compared = 0
    for d70, source in ARMS:
        arm = _arm_key(d70, source)
        subset = [
            record
            for record in published
            if record["d70"] == d70
            and record["bep_source"] == source
            and record["lambda_ac_m"] == str(LAMBDA_AC_M)
            and record["surface_variant"] == SURFACE_VARIANT
        ]
        if not subset:
            raise AssertionError(
                f"no {arm}/{LAMBDA_AC_M:g}/{SURFACE_VARIANT} rows found in "
                f"{_rel(PRODUCTION_TABLE)}"
            )
        per_arm[arm] = len(subset)
        fields_compared = len(subset[0])
        mine = rows_by_arm[arm]
        for record in subset:
            key = (record["river"], float(record["kp"]), record["scenario"])
            reproduced = mine.get(key)
            if reproduced is None:
                mismatches.append(f"{arm} {key}: missing from this study's pass")
                continue
            for field, published_value in record.items():
                if str(reproduced[field]) != published_value:
                    mismatches.append(
                        f"{arm} {key} {field}: published {published_value!r} != "
                        f"reproduced {str(reproduced[field])!r}"
                    )
    if mismatches:
        raise AssertionError(
            "GATE 1 FAILED: this study's pipeline does not reproduce the "
            "production annualisation. It is therefore not measuring the "
            "production quantity and no interval may be reported.\n  "
            + "\n  ".join(mismatches[:20])
        )
    return {
        "passed": True,
        "rows_compared": sum(per_arm.values()),
        "rows_per_arm": per_arm,
        "fields_compared": fields_compared,
        "table": _rel(PRODUCTION_TABLE),
        "criterion": "every field string-identical to the published table",
    }


# --------------------------------------------------------------------------- #
# The bootstrap                                                                 #
# --------------------------------------------------------------------------- #
def node_replicates(
    values: dict[str, np.ndarray],
    index: np.ndarray,
    n_blocks: int,
    multiplicities: np.ndarray,
    n_events: int,
) -> dict[str, np.ndarray]:
    """Replicate annual means per curve at one node and scenario."""
    names = list(values)
    stacked = np.column_stack([values[name] for name in names])
    sums = block_sums(stacked, index, n_blocks)
    means = replicate_means(sums, multiplicities, n_events)
    return {name: means[:, i] for i, name in enumerate(names)}


def share_replicates(replicates: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Per-replicate dominance shares over the mechanisms actually present.

    Mirrors ``AnnualizedResult.dominance_share``: the denominator is the sum of
    the present mechanisms' own annual contributions, and a replicate in which
    nothing is loaded returns 0 for every share rather than dividing by zero.
    """
    mechanisms = [name for name in replicates if name != "__system__"]
    total = np.zeros_like(replicates["__system__"])
    for name in mechanisms:
        total = total + replicates[name]
    shares: dict[str, np.ndarray] = {}
    for name in mechanisms:
        out = np.zeros_like(total)
        np.divide(replicates[name], total, out=out, where=total > 0.0)
        shares[name] = out
    return shares


def ratio_series(historical: np.ndarray, warming: np.ndarray) -> np.ndarray:
    """Per-replicate climate ratio, ``nan`` where it is undefined.

    The two scenarios are disjoint ensembles drawn from independent streams, so
    the ratio is warming over historical replicate by replicate. A replicate
    whose historical mean is exactly zero has no ratio; it is held as ``nan``
    rather than silently turned into an infinity, and the full length is kept so
    that a paired difference between two sections stays aligned on the replicate
    index.
    """
    out = np.full(historical.shape, np.nan, dtype=np.float64)
    defined = historical > 0.0
    out[defined] = warming[defined] / historical[defined]
    return out


def ratio_replicates(
    historical: np.ndarray, warming: np.ndarray
) -> tuple[np.ndarray, int]:
    """The defined climate ratios and the count of replicates that had none."""
    series = ratio_series(historical, warming)
    defined = np.isfinite(series)
    return series[defined], int((~defined).sum())


def _quantity_block(
    row: dict[str, Any],
    reps: dict[str, np.ndarray],
    values: dict[str, np.ndarray],
) -> dict[str, Any]:
    """One node-and-scenario record: system, mechanisms, shares, all intervalled.

    Where at most one mechanism is ever loaded, every share is pinned at the
    same value in every replicate. That is a statement about coverage, not a
    zero-width confidence statement about a probability, so those shares are
    marked degenerate and the mechanisms that never load are named
    (pre-registration rule 1.4 Q3.3). A mechanism that never loads while a
    second one does, as fluvial scour does everywhere, is recorded but does not
    make the split between the other two degenerate.
    """
    present = row["mechanisms"].split("|") if row["mechanisms"] else []
    loaded = [name for name in present if bool(np.any(values[name] > 0.0))]
    never_loaded = [name for name in present if name not in loaded]
    degenerate = len(loaded) <= 1
    block: dict[str, Any] = {
        "n_years": row["n_years"],
        "p_annual_system": _interval(float(row["p_annual_system"]), reps["__system__"]),
        "mechanisms_present": present,
    }
    if never_loaded:
        block["mechanisms_never_loaded"] = never_loaded
    shares = share_replicates(reps)
    for mechanism in MECHANISMS:
        if row[f"p_annual_{mechanism}"] == "":
            continue
        block[f"p_annual_{mechanism}"] = _interval(
            float(row[f"p_annual_{mechanism}"]), reps[mechanism]
        )
        block[f"share_{mechanism}"] = _interval(
            float(row[f"share_{mechanism}"]), shares[mechanism]
        )
        if degenerate:
            block[f"share_{mechanism}"]["degenerate"] = (
                "identical in every replicate because "
                + " and ".join(never_loaded)
                + " returns exactly zero at every simulated event, leaving "
                "only one loaded mechanism; this is a statement about "
                "coverage, not a zero-width confidence statement about a "
                "probability"
            )
    # The dominance margin the thesis quotes at KP 58.8, formed inside each
    # replicate so it is an interval on the ratio and not on its two parts.
    if "bep" in reps and "overflow" in reps:
        defined = reps["overflow"] > 0.0
        if defined.any() and float(row["p_annual_overflow"]) > 0.0:
            margin = reps["bep"][defined] / reps["overflow"][defined]
            block["margin_bep_over_overflow"] = _interval(
                float(row["p_annual_bep"]) / float(row["p_annual_overflow"]), margin
            )
            block["margin_bep_over_overflow"]["n_replicates_undefined"] = int(
                (~defined).sum()
            )
    return block


# --------------------------------------------------------------------------- #
# Pre-registered questions                                                      #
# --------------------------------------------------------------------------- #
def answer_q1(ratio_reps: dict[str, np.ndarray], points: dict[str, float]):
    """Q1: are the four per-section climate ratios resolvably different?

    Paired differences: the same historical and the same warming multiplicities
    drive both sections in a replicate, so the difference reflects the actual
    discordance between the two nodes rather than the variance of two
    independent estimates.
    """
    labels = [_label(kp) for kp in BEP_KPS]
    pairs: dict[str, Any] = {}
    resolved = 0
    for i, first in enumerate(labels):
        for second in labels[i + 1 :]:
            delta = ratio_reps[first] - ratio_reps[second]
            usable = np.isfinite(delta)
            lo, hi = percentile_interval(delta[usable])
            excludes_zero = bool(lo > 0.0 or hi < 0.0)
            resolved += int(excludes_zero)
            pairs[f"{first} - {second}"] = {
                "point": points[first] - points[second],
                "ci_low": lo,
                "ci_high": hi,
                "resolved": excludes_zero,
                "n_replicates_paired": int(usable.sum()),
            }
    if resolved == len(pairs):
        verdict = "YES: all six pairs resolve"
    elif resolved <= 2:
        verdict = (
            "UNANSWERABLE at this ensemble size (pre-registered rule 1.5): two "
            "or fewer of the six pairs resolve, so the four ratios are not "
            "distinguishable and must not be ranked"
        )
    else:
        verdict = f"PARTIAL: {resolved} of 6 pairs resolve"
    return {
        "question": (
            "are the four per-section climate ratios resolvably different from "
            "one another"
        ),
        "rule": (
            "a pair resolves iff the 95 % percentile interval of the paired "
            "bootstrap difference of ratios excludes zero"
        ),
        "pairs": pairs,
        "n_resolved": resolved,
        "n_pairs": len(pairs),
        "verdict": verdict,
    }


def answer_q2(
    reps: dict[str, np.ndarray], shares: dict[str, np.ndarray], row: dict[str, Any]
):
    """Q2: is the KP 62.0 warming mechanism split distinguishable from a tie?"""
    delta = reps["bep"] - reps["overflow"]
    lo, hi = percentile_interval(delta)
    not_a_tie = bool(lo > 0.0 or hi < 0.0)
    share_lo, share_hi = percentile_interval(shares["bep"])
    third_decimal_supported = bool(round(share_lo, 3) == round(share_hi, 3))
    return {
        "question": (
            "is the KP 62.0 warming mechanism split resolvably distinguishable "
            "from a tie"
        ),
        "rule_1": (
            "not a tie iff the 95 % interval of the paired difference of the "
            "two mechanisms' annual contributions excludes zero"
        ),
        "rule_2": (
            "the three-decimal quotation is supported iff both endpoints of the "
            "95 % interval of the piping share round to the same third decimal"
        ),
        "difference_p_annual_bep_minus_overflow": {
            "point": float(row["p_annual_bep"]) - float(row["p_annual_overflow"]),
            "ci_low": lo,
            "ci_high": hi,
        },
        "production_margin_bep_over_overflow": (
            float(row["p_annual_bep"]) / float(row["p_annual_overflow"])
        ),
        "share_bep": {
            "point": float(row["share_bep"]),
            "ci_low": share_lo,
            "ci_high": share_hi,
        },
        "resolvably_not_a_tie": not_a_tie,
        "three_decimal_quotation_supported": third_decimal_supported,
        "verdict": (
            "NOT A TIE: the split resolves"
            if not_a_tie
            else "TIE: the split is not distinguishable from level"
        ),
    }


def answer_q3(sections: dict[str, Any], arm: str):
    """Q3: are the historical mechanism shares resolvable as a lead?"""
    per_section: dict[str, Any] = {}
    resolved = 0
    degenerate = 0
    for kp in BEP_KPS:
        label = _label(kp)
        block = sections[label][arm]["historical"]
        share = block.get("share_bep")
        if share is None:
            per_section[label] = {"leading_mechanism_defined": False}
            continue
        is_degenerate = "degenerate" in share
        leads = bool(share["ci_low"] > 0.5)
        resolved += int(leads)
        degenerate += int(is_degenerate)
        printed = f"{share['point']:.2f}"
        per_section[label] = {
            "share_bep": share["point"],
            "ci_low": share["ci_low"],
            "ci_high": share["ci_high"],
            "lead_resolved": leads,
            "structurally_degenerate": is_degenerate,
            "two_decimal_quotation_supported": bool(
                f"{share['ci_low']:.2f}" == printed == f"{share['ci_high']:.2f}"
            ),
        }
    if resolved == 0:
        verdict = (
            "UNANSWERABLE (pre-registered rule 1.5): no section's share "
            "interval clears 0.5, so the annualised dominance claim does not "
            "survive hazard-sampling uncertainty"
        )
    elif resolved == degenerate and degenerate > 0:
        verdict = (
            "COVERAGE ONLY (pre-registered rule 1.5): the only sections whose "
            "lead resolves are the structurally degenerate ones, so the range "
            "statement rests on coverage rather than on measurement"
        )
    elif resolved == len(BEP_KPS):
        verdict = "YES: piping's lead resolves at all four sections"
    else:
        verdict = f"PARTIAL: the lead resolves at {resolved} of 4 sections"
    return {
        "question": (
            "are the historical mechanism shares (81 to 100 per cent) "
            "resolvable as a lead"
        ),
        "rule_1": (
            "the lead is resolved at a section iff the lower endpoint of the "
            "95 % interval of the piping share exceeds 0.5"
        ),
        "rule_3": (
            "a section whose competing branch is exactly zero at every event is "
            "classified as structurally degenerate, not as a resolved share"
        ),
        "sections": per_section,
        "n_resolved": resolved,
        "n_structurally_degenerate": degenerate,
        "verdict": verdict,
    }


# --------------------------------------------------------------------------- #
# Part two: the stratified entries of the RQ4 attribution table                 #
# --------------------------------------------------------------------------- #
def stratum_occupancy(event_ids: list[str], mask: np.ndarray) -> dict[str, Any]:
    """Occupancy of one stratum in the study's own resampling unit.

    Pre-registration section 3.2. The year count is not the resource a block
    bootstrap spends: the **carrying member blocks** are, so a stratum of 152
    years spread over 46 members and one of 152 years inside 3 members are not
    the same object. Section 3.3's floor is evaluated on what this returns.

    Parameters
    ----------
    event_ids : list of str
        Verbatim member headers, workbook order.
    mask : numpy.ndarray
        Boolean stratum membership, one entry per event.

    Returns
    -------
    dict
        Year count, carrying and total block counts, the largest single block's
        share of the stratum, the SST patterns spanned, and the F1/F2 verdict
        with any failing criterion named in full.
    """
    labels = block_labels(event_ids, "member")
    _, n_blocks_total, _ = block_index(labels)
    n_events = int(mask.sum())
    if n_events:
        _, counts = np.unique(labels[mask], return_counts=True)
        carrying = int(counts.size)
        largest = float(counts.max()) / float(n_events)
        patterns = int(np.unique(block_labels(event_ids, "sst")[mask]).size)
    else:
        carrying, largest, patterns = 0, 0.0, 0

    failures: list[str] = []
    if carrying < STRATUM_BLOCK_FLOOR:
        failures.append(
            f"F1 occupancy: {carrying} carrying member blocks, floor is "
            f"{STRATUM_BLOCK_FLOOR}"
        )
    if largest > STRATUM_MAX_BLOCK_SHARE:
        failures.append(
            f"F2 concentration: the largest member block holds "
            f"{100.0 * largest:.1f} % of the stratum, cap is "
            f"{100.0 * STRATUM_MAX_BLOCK_SHARE:.0f} %"
        )
    return {
        "n_years": n_events,
        "n_carrying_member_blocks": carrying,
        "n_member_blocks": n_blocks_total,
        "largest_block_share": largest,
        "n_sst_patterns": patterns,
        "clears_floor": not failures,
        "floor_failures": failures,
    }


def stratum_replicates(
    values: np.ndarray,
    mask: np.ndarray,
    index: np.ndarray,
    n_blocks: int,
    multiplicities: np.ndarray,
) -> dict[str, np.ndarray]:
    """Replicate conditional means, concentration factor and share.

    Stratum membership is a property of the event and travels with it through
    the resample, so a replicate's two strata are whatever its drawn blocks
    happen to contain. Both the ratio and the share are formed **inside** the
    replicate (pre-registration section 3.5), never as a quotient of two
    marginal intervals.

    Five per-block sums carry everything: the probability sum and the event
    count inside the stratum, the same two outside it, and the whole-ensemble
    probability sum that is the share's denominator.

    Returns
    -------
    dict of numpy.ndarray
        ``p_in``, ``p_out``, ``concentration``, ``share``; ``nan`` in any
        replicate where the quantity is undefined (an empty stratum, or a zero
        denominator). Under the section 3.3 floor no replicate is undefined,
        and the count is reported so that claim is checkable rather than
        assumed.
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
    totals = multiplicities.astype(np.float64) @ block_sums(stacked, index, n_blocks)
    s_in, n_in, s_out, n_out, s_all = (totals[:, i] for i in range(5))

    def _ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        out = np.full(num.shape, np.nan, dtype=np.float64)
        np.divide(num, den, out=out, where=den > 0.0)
        return out

    p_in = _ratio(s_in, n_in)
    p_out = _ratio(s_out, n_out)
    concentration = np.full(p_in.shape, np.nan, dtype=np.float64)
    usable = np.isfinite(p_in) & np.isfinite(p_out) & (p_out > 0.0)
    concentration[usable] = p_in[usable] / p_out[usable]
    return {
        "p_in": p_in,
        "p_out": p_out,
        "concentration": concentration,
        "share": _ratio(s_in, s_all),
    }


def _defined_interval(point: float, samples: np.ndarray) -> dict[str, Any]:
    """``_interval`` over the defined replicates, with the undefined count kept."""
    defined = np.isfinite(samples)
    record = _interval(point, samples[defined])
    record["n_replicates_undefined"] = int((~defined).sum())
    return record


def _with_printed_precision(record: dict[str, Any], fmt: str) -> dict[str, Any]:
    """Pre-registered rule 3: does the interval support the printed precision?

    A quoted value is supported at the precision the thesis prints it to iff
    **both** endpoints of its interval round to that same printed value. The
    thesis prints a concentration factor as a whole number and a share as a
    whole percentage, so those are the two formats scored. Applied
    mechanically here rather than eyeballed from the note.
    """
    printed = fmt.format(record["point"])
    record["printed"] = printed
    record["printed_precision_supported"] = bool(
        fmt.format(record["ci_low"]) == printed == fmt.format(record["ci_high"])
    )
    return record


def _count_limited(
    point: float, occupancy: dict[str, Any], what: str
) -> dict[str, Any]:
    """Pre-registration section 3.4: the count and no number.

    The production point estimate stays visible, because it is arithmetically
    exact for the ensemble as simulated and it is the value the thesis prints.
    It carries no interval, no half-width and no resolution verdict, and it may
    not be an endpoint of any range quoted as measured.
    """
    return {
        "point": float(point),
        "count_limited": True,
        "interval_withheld_because": "; ".join(occupancy["floor_failures"]),
        "n_years": occupancy["n_years"],
        "n_carrying_member_blocks": occupancy["n_carrying_member_blocks"],
        "n_member_blocks": occupancy["n_member_blocks"],
        "rule": (
            f"pre-registered floor, section 3.3: {what} is reported with the "
            "count and no number below "
            f"{STRATUM_BLOCK_FLOOR} carrying member blocks or above a "
            f"{100.0 * STRATUM_MAX_BLOCK_SHARE:.0f} % single-block share"
        ),
    }


def compose_bep_sections(campaign, context: dict[str, Any], d70: str, source: str):
    """The four characterised sections' composed curves, production path.

    Composed through the campaign's own ``_compose_segment`` exactly as
    ``annualise_arm`` does, so the stratified pass consumes the same curve gate
    1 has already proven reproduces the published annualisation.
    """
    n_eff = max(1.0, campaign.SEGMENT_LENGTH_M / LAMBDA_AC_M)
    out = {}
    for segment in context["registry"].bep_segments():
        frag, _ = campaign._compose_segment(
            segment,
            context["surface"],
            context["bep_curves"][(segment.kp, d70, source)],
            n_eff,
            "historical",
        )
        out[(segment.river, round(segment.kp, 3))] = frag
    return out


def stratified_attribution(
    campaign,
    context: dict[str, Any],
    frags: dict[tuple[str, float], Any],
    per_event: dict[tuple[str, float, str], dict[str, np.ndarray]],
    rows: dict[tuple[str, float, str], dict[str, Any]],
    event_ids: dict[str, list[str]],
    index_by_scenario: dict[str, tuple[np.ndarray, int]],
    multiplicities: dict[str, np.ndarray],
) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    """Intervals on the stratified entries, at the cells that clear the floor.

    Part two of the pre-registration. Same estimator, same seed, **same
    multiplicity draw** as part one, so every stratified quantity is paired
    with every other and with the annual quantities on the replicate index,
    and so this pass cannot perturb a single number in sections 2.2 to 2.7.

    Gate 4 runs here, in two halves. **4a** asserts that the unresampled
    stratified estimator reproduces the production ``stratified_annual_p_f``
    output to within ``UNRESAMPLED_TOLERANCE``; exact equality is not asserted
    and is not achievable, because the block-grouped sum reorders the addends
    ``np.mean`` adds pairwise. **4b** asserts that the production output itself
    is field for field the published ``rq4_attribution.json``, by float
    equality with no tolerance.

    Returns
    -------
    tuple
        ``(record, samples, gate4)``. ``samples`` carries the replicate arrays
        of the clearing cells only, which is what Q4 and Q5 difference.
    """
    published = json.loads(ATTRIBUTION_TABLE.read_text(encoding="utf-8"))
    sections: dict[str, Any] = {}
    samples: dict[str, dict[str, np.ndarray]] = {}
    mismatches: list[str] = []
    worst_deviation = 0.0

    for kp in BEP_KPS:
        label = _label(kp)
        node = ("Tokachi", round(kp, 3))
        frag = frags[node]
        entry = published[f"Tokachi_KP{kp:g}"]
        sections[label] = {}

        for scenario in campaign.SCENARIOS:
            hazard = context["hazards"][scenario][node]
            values = per_event[("Tokachi", kp, scenario)]["__system__"]
            index, n_blocks = index_by_scenario[scenario]
            pub = entry[scenario]
            p_annual = float(rows[("Tokachi", kp, scenario)]["p_annual_system"])

            hours = np.asarray([e.hours_above_datum for e in hazard.events])
            loaded = hours > 0.0
            for field, mine in (
                ("n_years", hazard.n_years),
                ("frac_years_loading_toe", float(np.mean(loaded))),
                (
                    "median_hours_above_toe_when_loaded",
                    float(np.median(hours[loaded])) if loaded.any() else 0.0,
                ),
                ("frac_years_gt24h", float(np.mean(hours > 24.0))),
            ):
                if mine != pub[field]:
                    mismatches.append(
                        f"{label} {scenario} {field}: published {pub[field]!r} "
                        f"!= reproduced {mine!r}"
                    )

            block: dict[str, Any] = {
                "n_years": hazard.n_years,
                "p_annual_system": p_annual,
            }
            for strat in STRATIFIERS:
                name = strat["name"]
                p_in, p_out, n_in, n_out = stratified_annual_p_f(
                    frag, hazard, strat["predicate"]
                )
                for field, mine in (
                    (strat["inside_key"], p_in),
                    (strat["outside_key"], p_out),
                    (strat["count_key"], n_in),
                ):
                    if mine != pub[field]:
                        mismatches.append(
                            f"{label} {scenario} {field}: published "
                            f"{pub[field]!r} != reproduced {mine!r}"
                        )

                mask = np.asarray(
                    [strat["predicate"](e) for e in hazard.events], dtype=bool
                )
                occupancy = stratum_occupancy(event_ids[scenario], mask)
                concentration_point = p_in / p_out if p_out > 0.0 else float("nan")
                share_point = (
                    n_in * p_in / (hazard.n_years * p_annual)
                    if p_annual > 0.0
                    else float("nan")
                )
                cell: dict[str, Any] = {
                    "definition": strat["definition"],
                    "occupancy": occupancy,
                    "p_f_inside": p_in,
                    "p_f_outside": p_out,
                    "n_inside": n_in,
                    "n_outside": n_out,
                }

                if occupancy["clears_floor"]:
                    reps = stratum_replicates(
                        values, mask, index, n_blocks, multiplicities[scenario]
                    )
                    # GATE 4a. Unit multiplicities reduce the replicate formula
                    # to the production estimator, so the two must agree; the
                    # difference is summation order alone.
                    unit = stratum_replicates(
                        values,
                        mask,
                        index,
                        n_blocks,
                        np.ones((1, n_blocks), dtype=np.int32),
                    )
                    for got, want in (
                        (float(unit["p_in"][0]), p_in),
                        (float(unit["p_out"][0]), p_out),
                    ):
                        deviation = abs(got - want) / want if want else abs(got)
                        worst_deviation = max(worst_deviation, deviation)
                        if deviation > UNRESAMPLED_TOLERANCE:
                            mismatches.append(
                                f"{label} {scenario} {name}: the unresampled "
                                f"block estimator gives {got!r} against the "
                                f"production {want!r} (relative {deviation:.3e})"
                            )
                    cell["concentration_factor"] = _with_printed_precision(
                        _defined_interval(concentration_point, reps["concentration"]),
                        "{:.0f}",
                    )
                    cell["share_of_annual_total"] = _with_printed_precision(
                        _defined_interval(share_point, reps["share"]),
                        "{:.0%}",
                    )
                    cell["p_f_inside_interval"] = _defined_interval(p_in, reps["p_in"])
                    samples[f"{label}|{scenario}|{name}"] = reps
                else:
                    cell["concentration_factor"] = _count_limited(
                        concentration_point, occupancy, "the concentration factor"
                    )
                    cell["share_of_annual_total"] = _count_limited(
                        share_point, occupancy, "the share of the annual total"
                    )
                block[name] = cell
            sections[label][scenario] = block

    if mismatches:
        raise AssertionError(
            "GATE 4 FAILED: the stratified pass does not reproduce the "
            "published RQ4 attribution, so its intervals would not be on the "
            "published quantity.\n  " + "\n  ".join(mismatches[:20])
        )
    gate4 = {
        "passed": True,
        "table": _rel(ATTRIBUTION_TABLE),
        "cells_compared": len(BEP_KPS) * len(campaign.SCENARIOS),
        "fields_per_cell": 10,
        "criterion_4b": (
            "every field of rq4_attribution.json reproduced by float equality "
            "with no tolerance, through the production stratified_annual_p_f"
        ),
        "criterion_4a": (
            "the unresampled block estimator reproduces the production "
            "conditional means; bit-identity is not asserted because the "
            "block-grouped sum reorders the addends np.mean adds pairwise"
        ),
        "unresampled_tolerance": UNRESAMPLED_TOLERANCE,
        "worst_relative_deviation": worst_deviation,
    }
    return sections, samples, gate4


def _clearing_cells(
    sections: dict[str, Any], stratifier: str, scenario: str
) -> list[str]:
    """Section labels whose cell clears the pre-registered floor, in KP order."""
    return [
        _label(kp)
        for kp in BEP_KPS
        if sections[_label(kp)][scenario][stratifier]["occupancy"]["clears_floor"]
    ]


def _range_verdict(
    sections: dict[str, Any],
    samples: dict[str, dict[str, np.ndarray]],
    stratifier: str,
    scenario: str,
    quantity: str,
    key: str,
) -> dict[str, Any]:
    """One question's scoring: the range, its pairs, and the excluded cells.

    Pre-registration section 3.6 rules 1 to 3. The pairs are **paired** on the
    replicate index, which the shared multiplicity draw makes valid: one block
    draw serves every node, so a difference reflects the discordance between two
    sections under a common resample of the hazard rather than the variance of
    two independent estimates.
    """
    clearing = _clearing_cells(sections, stratifier, scenario)
    withheld = []
    for kp in BEP_KPS:
        label = _label(kp)
        if label in clearing:
            continue
        occupancy = sections[label][scenario][stratifier]["occupancy"]
        point = sections[label][scenario][stratifier][key]["point"]
        withheld.append(
            {
                "section": label,
                "point": point,
                "n_years": occupancy["n_years"],
                "n_carrying_member_blocks": occupancy["n_carrying_member_blocks"],
                "failing_criterion": "; ".join(occupancy["floor_failures"]),
                # Section 3.4 permits exactly one comparison against an
                # intervalled cell, because it costs nothing: whether the
                # count-limited point falls inside the other's interval. It is
                # an observation about where an unmeasured value sits, never a
                # measurement of it, and never a resolution verdict.
                "point_falls_inside": [
                    other
                    for other in clearing
                    if sections[other][scenario][stratifier][key]["ci_low"]
                    <= point
                    <= sections[other][scenario][stratifier][key]["ci_high"]
                ],
                "observation_is_not_a_measurement": (
                    "where a count-limited point sits relative to another "
                    "cell's interval; this cell has no interval of its own and "
                    "no resolution verdict may be formed from it"
                ),
            }
        )

    pairs: dict[str, Any] = {}
    resolved = 0
    for i, first in enumerate(clearing):
        for second in clearing[i + 1 :]:
            delta = (
                samples[f"{first}|{scenario}|{stratifier}"][quantity]
                - samples[f"{second}|{scenario}|{stratifier}"][quantity]
            )
            usable = np.isfinite(delta)
            lo, hi = percentile_interval(delta[usable])
            excludes_zero = bool(lo > 0.0 or hi < 0.0)
            resolved += int(excludes_zero)
            pairs[f"{first} - {second}"] = {
                "point": (
                    sections[first][scenario][stratifier][key]["point"]
                    - sections[second][scenario][stratifier][key]["point"]
                ),
                "ci_low": lo,
                "ci_high": hi,
                "resolved": excludes_zero,
                "n_replicates_paired": int(usable.sum()),
            }

    blocks = [sections[label][scenario][stratifier][key] for label in clearing]
    # Derived from rule 2's pairs, not a new rule: a RANGE is carried by its two
    # endpoints, so whether those two resolve is the question a reader of the
    # range actually has. Every other pair speaks to the ordering in between.
    endpoints_resolve = None
    if len(clearing) >= 2:
        lowest = min(
            clearing,
            key=lambda label: sections[label][scenario][stratifier][key]["point"],
        )
        highest = max(
            clearing,
            key=lambda label: sections[label][scenario][stratifier][key]["point"],
        )
        endpoints_resolve = bool(
            pairs.get(
                f"{lowest} - {highest}", pairs.get(f"{highest} - {lowest}", {})
            ).get("resolved", False)
        )

    if not clearing:
        verdict = (
            "UNANSWERABLE (pre-registered section 3.7): no cell clears the "
            "floor, so no range may be quoted at all"
        )
    elif len(clearing) == 1:
        verdict = (
            f"SINGLE CELL: only {clearing[0]} clears the floor, so there is no "
            "range, only one intervalled value"
        )
    elif resolved == 0:
        verdict = (
            "COLLAPSED (pre-registered section 3.7): cells clear the floor but "
            "no pair of them resolves, so the spread is not a measured range"
        )
    elif resolved == len(pairs):
        verdict = f"RANGE SUPPORTED over the {len(clearing)} cells that clear"
    else:
        verdict = (
            f"PARTIAL: {resolved} of {len(pairs)} pairs among the "
            f"{len(clearing)} clearing cells resolve"
        )
    return {
        "scenario": scenario,
        "stratifier": stratifier,
        "quantity": key,
        "clearing_cells": clearing,
        "range_point": (
            [min(b["point"] for b in blocks), max(b["point"] for b in blocks)]
            if blocks
            else None
        ),
        "range_interval": (
            [min(b["ci_low"] for b in blocks), max(b["ci_high"] for b in blocks)]
            if blocks
            else None
        ),
        "per_cell": {
            label: sections[label][scenario][stratifier][key] for label in clearing
        },
        "printed_precision_supported_at": [
            label
            for label in clearing
            if sections[label][scenario][stratifier][key]["printed_precision_supported"]
        ],
        "pairs": pairs,
        "endpoints_resolve": endpoints_resolve,
        "n_resolved": resolved,
        "n_pairs": len(pairs),
        "withheld_below_floor": withheld,
        "verdict": verdict,
    }


def floor_sensitivity(sections: dict[str, Any]) -> dict[str, Any]:
    """Q6: which cells clear at 10, at the pre-registered 20, and at 30 blocks.

    Reported, never used to choose. Scored as the **membership** of the
    clearing set and the point-estimate endpoints that follow from it, not as
    intervals for cells the pre-registered floor excludes: section 3.4 forbids
    printing one below the floor, and a declared sensitivity is not an
    exemption from a rule fixed in advance.
    """
    out: dict[str, Any] = {}
    for floor in sorted({*FLOOR_SENSITIVITY, STRATUM_BLOCK_FLOOR}):
        per_floor: dict[str, Any] = {}
        for strat in STRATIFIERS:
            name = strat["name"]
            for scenario in ("historical", "+4K"):
                clearing = [
                    _label(kp)
                    for kp in BEP_KPS
                    if sections[_label(kp)][scenario][name]["occupancy"][
                        "n_carrying_member_blocks"
                    ]
                    >= floor
                    and sections[_label(kp)][scenario][name]["occupancy"][
                        "largest_block_share"
                    ]
                    <= STRATUM_MAX_BLOCK_SHARE
                ]
                points = [
                    sections[label][scenario][name]["concentration_factor"]["point"]
                    for label in clearing
                ]
                per_floor[f"{name}/{scenario}"] = {
                    "clearing_cells": clearing,
                    "concentration_range_point": (
                        [min(points), max(points)] if points else None
                    ),
                }
        out[str(floor)] = {
            "is_the_preregistered_floor": floor == STRATUM_BLOCK_FLOOR,
            "cells": per_floor,
        }
    out["reading"] = (
        "membership of the clearing set at each floor, with the point-estimate "
        "endpoints that follow. No interval is computed for a cell the "
        "pre-registered floor excludes: section 3.4 forbids printing one and a "
        "sensitivity does not suspend it"
    )
    return out


# --------------------------------------------------------------------------- #
# Sensitivity on the resampling unit                                            #
# --------------------------------------------------------------------------- #
def unit_sensitivity(
    per_event: dict[tuple[str, float, str], dict[str, np.ndarray]],
    event_ids: dict[str, list[str]],
    campaign,
    rng,
) -> dict[str, Any]:
    """Pre-registration section 1.6: what the choice of resampling unit is worth.

    Reported, never quoted as the headline interval. The i.i.d.-over-events unit
    is the naive estimator the production numbers implicitly assume; the
    calendar-year unit is the crossed axis (in the historical ensemble every
    member shares the observed sea-surface temperature of a given year); the
    six-pattern unit is **structural climate-model spread rather than sampling
    noise**, and a percentile interval from six units is not trustworthy at its
    ends.
    """
    out: dict[str, Any] = {}
    for unit in RESAMPLING_UNITS:
        entry: dict[str, Any] = {}
        for scenario in campaign.SCENARIOS:
            ids = event_ids[scenario]
            if unit == "sst" and len(set(block_labels(ids, "sst"))) < 2:
                continue
            index, n_blocks, _ = block_index(block_labels(ids, unit))
            stacked = np.column_stack(
                [
                    per_event[("Tokachi", round(kp, 3), scenario)]["__system__"]
                    for kp in BEP_KPS
                ]
            )
            sums = block_sums(stacked, index, n_blocks)
            # The i.i.d.-over-events unit has one block per event, so its
            # multiplicity matrix is (replicates x n_events) and is drawn in
            # chunks rather than held whole.
            means = chunked_replicate_means(sums, n_blocks, len(ids), REPLICATES, rng)
            per_section: dict[str, Any] = {}
            for column, kp in enumerate(BEP_KPS):
                lo, hi = percentile_interval(means[:, column])
                point = float(np.mean(stacked[:, column]))
                per_section[_label(kp)] = {
                    "ci_low": lo,
                    "ci_high": hi,
                    "relative_half_width": (
                        float(0.5 * (hi - lo) / point) if point > 0.0 else None
                    ),
                }
            entry[scenario] = {"n_blocks": n_blocks, "sections": per_section}
        out[unit] = entry
    out["reading"] = (
        "member is the estimator; event is the naive independent-years "
        "alternative the production numbers implicitly assume; year is the "
        "crossed shared-forcing axis; sst is the six warming sea-surface "
        "patterns and is structural climate-model spread rather than "
        "hazard-sampling noise, reported because it is the largest measured "
        "grouping and never quoted as the sampling interval"
    )
    return out


# --------------------------------------------------------------------------- #
# Summaries                                                                     #
# --------------------------------------------------------------------------- #
def summarise(
    rows_by_arm: dict[str, dict[tuple[str, float, str], dict[str, Any]]],
    replicates_by_arm: dict[str, dict[tuple[str, float, str], dict[str, np.ndarray]]],
    per_event_by_arm: dict[str, Any],
    ratio_by_arm: dict[str, dict[str, dict[str, Any]]],
    campaign,
) -> dict[str, Any]:
    """Section-level record for the four characterised sections, every arm."""
    sections: dict[str, Any] = {}
    for kp in BEP_KPS:
        label = _label(kp)
        sections[label] = {}
        for d70, source in ARMS:
            arm = _arm_key(d70, source)
            entry: dict[str, Any] = {}
            for scenario in campaign.SCENARIOS:
                key = ("Tokachi", kp, scenario)
                entry[scenario] = _quantity_block(
                    rows_by_arm[arm][key],
                    replicates_by_arm[arm][key],
                    per_event_by_arm[arm][key],
                )
            for name, record in ratio_by_arm[arm][label].items():
                entry[name] = record
            sections[label][arm] = entry
    return sections


def climate_ratio_record(
    rows: dict[tuple[str, float, str], dict[str, Any]],
    reps: dict[tuple[str, float, str], dict[str, np.ndarray]],
    kp: float,
    curve: str,
    field: str,
) -> dict[str, Any] | None:
    """Climate ratio for one curve at one section, formed inside each replicate."""
    historical = rows[("Tokachi", kp, "historical")]
    warming = rows[("Tokachi", kp, "+4K")]
    if historical[field] in ("", None) or float(historical[field]) <= 0.0:
        return None
    ratio, undefined = ratio_replicates(
        reps[("Tokachi", kp, "historical")][curve], reps[("Tokachi", kp, "+4K")][curve]
    )
    record = _interval(float(warming[field]) / float(historical[field]), ratio)
    record["n_replicates_undefined"] = undefined
    record["definition"] = (
        f"warming {field} divided by historical, formed inside each replicate, "
        "never a quotient of two marginal intervals"
    )
    return record


def reach_summary(
    rows: dict[tuple[str, float, str], dict[str, Any]],
    replicates: dict[tuple[str, float, str], dict[str, np.ndarray]],
) -> list[dict[str, Any]]:
    """Compact per-segment record for all 114 segments (study directory only)."""
    out: list[dict[str, Any]] = []
    for (river, kp, scenario), row in rows.items():
        reps = replicates[(river, kp, scenario)]
        lo, hi = percentile_interval(reps["__system__"])
        out.append(
            {
                "river": river,
                "kp": kp,
                "section_id": row["section_id"],
                "scenario": scenario,
                "mechanisms": row["mechanisms"],
                "p_annual_system": float(row["p_annual_system"]),
                "ci_low": lo,
                "ci_high": hi,
            }
        )
    return out


def section_aggregate_intervals(
    campaign,
    context: dict[str, Any],
    multiplicities: dict[str, np.ndarray],
    d70: str,
    source: str,
) -> dict[str, Any]:
    """Intervals on the nine Uemura section aggregates, system level only.

    Chapter 7 quotes the Tokachi 4 aggregate alongside the segment numbers, and
    it is a different node's curve (the ADR-0043 within-section maximum on the
    representative node's rated stage axis), so it needs its own interval rather
    than borrowing KP 58.8's. Read from the persisted campaign payload, whose
    ``p_sys`` this study does not recompute; the annual point estimate is
    re-derived by the campaign's own ``np.interp`` and asserted against the
    persisted one.
    """
    payload = json.loads(
        (campaign.OUT_DIR / f"rq3_sections_{d70}_{source}.json").read_text(
            encoding="utf-8"
        )
    )
    out: dict[str, Any] = {}
    for sid, entry in payload.items():
        river = entry["river"]
        kp = float(entry["representative_kp"])
        grid = np.asarray(entry["stage_m_msl"], dtype=np.float64)
        p_sys = np.asarray(entry["p_sys"], dtype=np.float64)
        block: dict[str, Any] = {"river": river, "representative_kp": kp}
        replicates: dict[str, np.ndarray] = {}
        for scenario, published in entry["annual"].items():
            hazard = context["hazards"][scenario][(river, round(kp, 3))]
            peaks = hazard.peak_stages()
            values = np.interp(peaks, grid, p_sys)
            if float(np.mean(values)) != published:
                raise AssertionError(
                    f"GATE 0 FAILED at section aggregate {sid} {scenario}: "
                    "the re-derived mean does not reproduce the persisted "
                    "annual value."
                )
            ids = [event.event_id for event in hazard.events]
            index, n_blocks, _ = block_index(block_labels(ids, "member"))
            reps = node_replicates(
                {"p": values}, index, n_blocks, multiplicities[scenario], len(ids)
            )["p"]
            replicates[scenario] = reps
            block[scenario] = _interval(float(published), reps)
        ratio, undefined = ratio_replicates(replicates["historical"], replicates["+4K"])
        if ratio.size and replicates["historical"].size:
            point_hist = float(entry["annual"]["historical"])
            block["climate_ratio"] = (
                _interval(float(entry["annual"]["+4K"]) / point_hist, ratio)
                if point_hist > 0.0
                else {
                    "point": None,
                    "reason": "historical annual probability is exactly zero",
                }
            )
            block["climate_ratio"]["n_replicates_undefined"] = undefined
        out[sid] = block
    return out


# --------------------------------------------------------------------------- #
# Driver                                                                        #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Evidence record (default: the committed companion JSON).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Study directory for the full 114-segment table.",
    )
    parser.add_argument(
        "--replicates",
        type=int,
        default=REPLICATES,
        help=(
            "Bootstrap replicates per scenario. The pre-registered value is "
            f"{REPLICATES}; a smaller value is a smoke test and is stamped as "
            "such in the record."
        ),
    )
    args = parser.parse_args(argv)

    started = time.time()
    campaign = _load_campaign_module()

    cache_before = _dir_state(campaign.HAZARD_CACHE, "*.csv")
    phase3_before = _dir_state(PHASE3_DIR)

    print("building context (persisted curves + warm hazard cache) ...", flush=True)
    context = build_context(campaign)

    event_ids = {
        scenario: [
            event.event_id
            for event in context["hazards"][scenario][("Tokachi", 58.8)].events
        ]
        for scenario in campaign.SCENARIOS
    }
    structure = {
        scenario: ensemble_structure(ids) for scenario, ids in event_ids.items()
    }
    # Every node carries the identical event sequence, which is what lets one
    # block draw per scenario serve all 114 nodes and makes every between-node
    # comparison paired. Asserted, not assumed.
    for scenario in campaign.SCENARIOS:
        for key, hazard in context["hazards"][scenario].items():
            if [event.event_id for event in hazard.events] != event_ids[scenario]:
                raise AssertionError(
                    f"node {key} carries a different {scenario} event sequence "
                    "from the reference node; a shared block draw would not be "
                    "a paired comparison."
                )

    rows_by_arm: dict[str, dict[tuple[str, float, str], dict[str, Any]]] = {}
    per_event_by_arm: dict[str, Any] = {}
    for d70, source in ARMS:
        arm = _arm_key(d70, source)
        print(f"annualising {arm} ...", flush=True)
        rows, per_event = annualise_arm(campaign, context, d70, source)
        rows_by_arm[arm] = rows
        per_event_by_arm[arm] = per_event

    print("gate 1: reproducing the production table ...", flush=True)
    gate1 = gate_one(rows_by_arm)
    print(
        f"  GATE 1 PASSED: {gate1['rows_compared']} published rows reproduced "
        f"field for field ({gate1['fields_compared']} fields each)",
        flush=True,
    )

    rng = np.random.default_rng(SEED)
    index_by_scenario: dict[str, tuple[np.ndarray, int]] = {}
    multiplicities: dict[str, np.ndarray] = {}
    for scenario in campaign.SCENARIOS:
        labels = block_labels(event_ids[scenario], "member")
        index, n_blocks, _ = block_index(labels)
        index_by_scenario[scenario] = (index, n_blocks)
        multiplicities[scenario] = draw_multiplicities(n_blocks, args.replicates, rng)

    print(
        f"bootstrapping {args.replicates} replicates over "
        f"{index_by_scenario['historical'][1]} historical and "
        f"{index_by_scenario['+4K'][1]} warming members ...",
        flush=True,
    )
    replicates_by_arm: dict[str, dict[tuple[str, float, str], dict[str, np.ndarray]]]
    replicates_by_arm = {}
    ratio_by_arm: dict[str, dict[str, dict[str, Any]]] = {}
    ratio_samples: dict[str, dict[str, np.ndarray]] = {}
    for d70, source in ARMS:
        arm = _arm_key(d70, source)
        node_reps: dict[tuple[str, float, str], dict[str, np.ndarray]] = {}
        for key, values in per_event_by_arm[arm].items():
            scenario = key[2]
            index, n_blocks = index_by_scenario[scenario]
            node_reps[key] = node_replicates(
                values,
                index,
                n_blocks,
                multiplicities[scenario],
                len(event_ids[scenario]),
            )
        replicates_by_arm[arm] = node_reps
        ratio_by_arm[arm] = {}
        ratio_samples[arm] = {}
        for kp in BEP_KPS:
            label = _label(kp)
            records: dict[str, Any] = {}
            system = climate_ratio_record(
                rows_by_arm[arm], node_reps, kp, "__system__", "p_annual_system"
            )
            if system is not None:
                records["climate_ratio"] = system
            piping = climate_ratio_record(
                rows_by_arm[arm], node_reps, kp, "bep", "p_annual_bep"
            )
            if piping is not None:
                records["climate_ratio_piping_only"] = piping
            ratio_by_arm[arm][label] = records
            ratio_samples[arm][label] = ratio_series(
                node_reps[("Tokachi", kp, "historical")]["__system__"],
                node_reps[("Tokachi", kp, "+4K")]["__system__"],
            )

    sections = summarise(
        rows_by_arm, replicates_by_arm, per_event_by_arm, ratio_by_arm, campaign
    )

    primary = _arm_key(*PRIMARY_ARM)
    ratio_points = {
        _label(kp): sections[_label(kp)][primary]["climate_ratio"]["point"]
        for kp in BEP_KPS
    }
    q1 = answer_q1(ratio_samples[primary], ratio_points)
    kp62_key = ("Tokachi", 62.0, "+4K")
    q2 = answer_q2(
        replicates_by_arm[primary][kp62_key],
        share_replicates(replicates_by_arm[primary][kp62_key]),
        rows_by_arm[primary][kp62_key],
    )
    q3 = answer_q3(sections, primary)

    # ----- Part two: the stratified entries -------------------------------- #
    # GATE 5. The stratified pass reuses the multiplicity draw already made and
    # takes nothing further from the stream, which is what proves it added a
    # quantity rather than perturbing the estimator: every interval of sections
    # 2.2 to 2.7 is computed from the same draw and comes out unchanged.
    print("stratified attribution (part two) ...", flush=True)
    rng_state_before = rng.bit_generator.state
    stratified, stratified_samples, gate4 = stratified_attribution(
        campaign,
        context,
        compose_bep_sections(campaign, context, *PRIMARY_ARM),
        per_event_by_arm[primary],
        rows_by_arm[primary],
        event_ids,
        index_by_scenario,
        multiplicities,
    )
    if rng.bit_generator.state != rng_state_before:
        raise AssertionError(
            "GATE 5 FAILED: the stratified pass advanced the random stream, so "
            "it did not reuse part one's multiplicity draw and every part-one "
            "interval would move with it."
        )
    print(
        f"  GATE 4 PASSED: {gate4['cells_compared']} attribution cells "
        f"reproduced field for field (worst unresampled deviation "
        f"{gate4['worst_relative_deviation']:.2e})",
        flush=True,
    )
    q4 = {
        scenario: _range_verdict(
            stratified,
            stratified_samples,
            "duration",
            scenario,
            "concentration",
            "concentration_factor",
        )
        for scenario in campaign.SCENARIOS
    }
    q5 = {
        scenario: _range_verdict(
            stratified,
            stratified_samples,
            "duration",
            scenario,
            "share",
            "share_of_annual_total",
        )
        for scenario in campaign.SCENARIOS
    }
    q4_compound = {
        scenario: _range_verdict(
            stratified,
            stratified_samples,
            "compound",
            scenario,
            "concentration",
            "concentration_factor",
        )
        for scenario in campaign.SCENARIOS
    }
    q6 = floor_sensitivity(stratified)

    print("resampling-unit sensitivity ...", flush=True)
    sensitivity = unit_sensitivity(
        per_event_by_arm[primary], event_ids, campaign, np.random.default_rng(SEED + 1)
    )

    print("section aggregates ...", flush=True)
    aggregates = section_aggregate_intervals(
        campaign, context, multiplicities, *PRIMARY_ARM
    )

    cache_after = _dir_state(campaign.HAZARD_CACHE, "*.csv")
    if cache_after != cache_before:
        raise AssertionError(
            "GATE 2 FAILED: the Phase 3 hazard cache changed during this run; "
            "a workbook was streamed or a cache entry rewritten."
        )
    phase3_after = _dir_state(PHASE3_DIR)
    if phase3_after != phase3_before:
        raise AssertionError(
            "GATE 3 FAILED: a Phase 3 production output changed during this "
            "run. This study is read-only over results/system_integration/."
        )

    payload: dict[str, Any] = {
        "study": (
            "Hazard-sampling uncertainty on the Phase 3 annualised results: a "
            "block bootstrap over d4PDF ensemble members with the fragility "
            "curves held fixed"
        ),
        "generated_by": "scripts/annualisation_uncertainty_study.py",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "note": NOTE,
        "scope": {
            "statement": SCOPE_STATEMENT,
            "resamples": "the d4PDF hazard only",
            "held_fixed": (
                "every fragility curve, so this is not the total uncertainty"
            ),
            "dominated_by": (
                "the aquifer-conductivity bracket, "
                "docs/decisions/conductivity-bracket-annualisation.md"
            ),
            "arms": [_arm_key(d70, source) for d70, source in ARMS],
            "primary_arm": primary,
            "lambda_ac_m": LAMBDA_AC_M,
            "surface_variant": SURFACE_VARIANT,
        },
        "estimator": {
            "unit": "d4PDF ensemble member (the prefix-and-member pair)",
            "why_not_years": (
                "the simulated years are nested exactly 60-per-member inside "
                "the ensemble members, so they are not independent draws and an "
                "i.i.d. bootstrap over them is not a resample of the ensemble's "
                "independent units"
            ),
            "replicates": args.replicates,
            "preregistered_replicates": REPLICATES,
            "seed": SEED,
            "interval": "two-sided 95 % percentile (2.5 / 97.5)",
            "point_estimates": (
                "always the unresampled production values, never a bootstrap " "mean"
            ),
            "pairing": (
                "one block draw per scenario shared by all 114 nodes, so every "
                "between-node difference is paired; the two scenarios are drawn "
                "from independent streams and the climate ratio is formed "
                "inside each replicate"
            ),
        },
        "ensemble_structure": structure,
        "gates": {
            "gate_0_per_event_matrix_averages_to_the_published_number": {
                "passed": True,
                "criterion": (
                    "float equality, no tolerance, at every node, scenario and "
                    "curve of every arm"
                ),
            },
            "gate_1_reproduces_production_table": gate1,
            "gate_4_reproduces_rq4_attribution": gate4,
            "gate_5_stratified_pass_reused_the_part_one_draw": {
                "passed": True,
                "criterion": (
                    "the random stream's state is unchanged across the "
                    "stratified pass, so part one's multiplicity draw is the "
                    "one used and no interval in sections 2.2 to 2.7 moved"
                ),
            },
            "gate_2_hazard_cache_unchanged": {
                "passed": True,
                "cache_files": len(cache_after),
            },
            "gate_3_no_production_artifact_written": {
                "passed": True,
                "phase3_files_unchanged": len(phase3_after),
                "criterion": (
                    "SHA-256 of every file under results/system_integration/"
                    "phase3/ unchanged across the run; this study's own two "
                    "outputs are listed under the record's 'writes' key"
                ),
            },
        },
        # Kept out of the gate block, and named in the campaign's volatile-key
        # set, because the paths follow --out / --out-dir: the campaign runs
        # this driver into its own companions directory and compares the result
        # against the committed record, which would otherwise differ on nothing
        # but where it was told to write.
        "writes": [_rel(args.out), _rel(args.out_dir)],
        "sections": sections,
        "section_aggregates": aggregates,
        "stratified_attribution": {
            "scope": (
                "the stratified entries of Table 'tab: rq4 attribution', "
                "matrix / posterior / 250 m / primary, the only arm "
                "rq4_attribution.json exists for"
            ),
            "floor": {
                "F1_min_carrying_member_blocks": STRATUM_BLOCK_FLOOR,
                "F2_max_single_block_share": STRATUM_MAX_BLOCK_SHARE,
                "unit": (
                    "the d4PDF ensemble member block, not the simulated year: "
                    "a stratum's information is carried by the blocks holding "
                    "at least one of its events"
                ),
                "preregistered": (
                    "section 3.3 of the note, committed 2026-08-20 in aeeb918 "
                    "before this driver carried a line of stratified code"
                ),
                "below_the_floor": (
                    "the year count, the carrying-member count, the failing "
                    "criterion and the production point estimate labelled "
                    "count-limited; no interval, no half-width, no resolution "
                    "verdict, and no admission to a range quoted as measured"
                ),
            },
            "sections": stratified,
        },
        "preregistration_outcome": {
            "Q1": q1,
            "Q2": q2,
            "Q3": q3,
            "Q4": q4,
            "Q5": q5,
            "Q4_compound": q4_compound,
            "Q6_floor_sensitivity": q6,
        },
        "resampling_unit_sensitivity": sensitivity,
        "elapsed_s": round(time.time() - started, 1),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "reach_intervals.json").write_text(
        json.dumps(
            {
                arm: reach_summary(rows_by_arm[arm], replicates_by_arm[arm])
                for arm in (_arm_key(d70, source) for d70, source in ARMS)
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {_rel(args.out)}")
    print(f"wrote {_rel(args.out_dir / 'reach_intervals.json')}")

    print(f"\n{SCOPE_STATEMENT}\n")
    print("annual system failure probability, primary arm, 95 % interval")
    for kp in BEP_KPS:
        label = _label(kp)
        for scenario in campaign.SCENARIOS:
            block = sections[label][primary][scenario]["p_annual_system"]
            print(
                f"  {label:<8} {scenario:<11} {block['point']:.3e}  "
                f"[{block['ci_low']:.3e}, {block['ci_high']:.3e}]  "
                f"+/-{100.0 * (block['relative_half_width'] or 0.0):.1f} %"
            )
    print("\nclimate ratio, primary arm, 95 % interval")
    for kp in BEP_KPS:
        block = sections[_label(kp)][primary]["climate_ratio"]
        print(
            f"  {_label(kp):<8} {block['point']:.2f}  "
            f"[{block['ci_low']:.2f}, {block['ci_high']:.2f}]"
        )
    print("\nstratified attribution, duration stratum, primary arm")
    for kp in BEP_KPS:
        label = _label(kp)
        for scenario in campaign.SCENARIOS:
            cell = stratified[label][scenario]["duration"]
            occ = cell["occupancy"]
            stamp = (
                f"{occ['n_years']:>4} yr / {occ['n_carrying_member_blocks']:>2} of "
                f"{occ['n_member_blocks']} members"
            )
            conc = cell["concentration_factor"]
            share = cell["share_of_annual_total"]
            if conc.get("count_limited"):
                print(
                    f"  {label:<8} {scenario:<11} {stamp}  "
                    f"concentration {conc['point']:.0f}, share "
                    f"{100.0 * share['point']:.0f} %  COUNT-LIMITED, no interval"
                )
            else:
                print(
                    f"  {label:<8} {scenario:<11} {stamp}  "
                    f"concentration {conc['point']:.0f} "
                    f"[{conc['ci_low']:.0f}, {conc['ci_high']:.0f}], share "
                    f"{100.0 * share['point']:.0f} % "
                    f"[{100.0 * share['ci_low']:.0f}, "
                    f"{100.0 * share['ci_high']:.0f}]"
                )

    print("\npre-registration outcome")
    for key, entry in payload["preregistration_outcome"].items():
        if "verdict" in entry:
            print(f"  {key}: {entry['verdict']}")
        else:
            for scenario, sub in entry.items():
                if isinstance(sub, dict) and "verdict" in sub:
                    print(f"  {key} {scenario}: {sub['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
