"""Canonical-shape sensitivity: what the one pinned d4PDF event is worth.

Companion driver for ``docs/decisions/canonical-shape-sensitivity.md`` (defence
brief item A1). Every transient conditional probability in this project is
computed by scaling one pinned ensemble member, ``HPB_m064_1987``, to each
conditioning level. The approved alternate ``HPB_m067_1978`` is already recorded
as ``canonical_event_ids[1]`` in all eight configs; this study exercises it and
measures the difference end to end.

Stages, each independently runnable and each writing into one merged evidence
record::

    python scripts/canonical_shape_sensitivity_study.py shape
    python scripts/canonical_shape_sensitivity_study.py phase1
    python scripts/canonical_shape_sensitivity_study.py ladder
    python scripts/canonical_shape_sensitivity_study.py peak-shortcut
    python scripts/canonical_shape_sensitivity_study.py surface
    python scripts/canonical_shape_sensitivity_study.py phase3
    python scripts/canonical_shape_sensitivity_study.py figures
    python scripts/canonical_shape_sensitivity_study.py all

The member is swapped **in memory only**. ``run.py`` selects
``canonical_event_ids[0]``; that field is inside ``config_hash()``; and the
config drift guard pins the committed ordered list. So reordering a committed
YAML is forbidden three ways, and the only admissible route is the in-memory
pattern of ``scripts/foreshore_width_study.py``: load the YAML, replace the one
key, revalidate through ``Config``, run with ``persist=False``. The committed
configs are never written and a test asserts it.

Four gates, all consequences the companion invariance note derived from source
and none of them findings:

* **Gate 1** every baseline arm reproduces its persisted production sweep
  bit-for-bit on both raw probability vectors;
* **Gate 2** the raw static probabilities are EXACTLY equal between the two
  shape arms at every level of every stratum (the static comparator consumes the
  scalar conditioning level verbatim and never touches the loading record);
* **Gate 3** the six peak-referenced comparators of the Stage 6.6 ladder and the
  whole static Shapley lattice are bit-identical between the arms;
* **Gate 4** the Phase 3 hazard cache is unchanged (the hazard side streams every
  ensemble member and does not know which one is canonical).

Nothing production is touched: no config, no geotechnical CSV, no persisted
sweep, no ``rq4_annual.csv``, no posterior, no committed surface-curve contract.
Arm artifacts live under gitignored ``results/canonical_shape/``.

Runtime: about 39 min for ``phase1`` (eight strata, two arms), about 20 min for
``ladder``, about 8 min for ``surface``, seconds for the rest.
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

import h5py
import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as figstyle  # noqa: E402

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult, binomial_ci  # noqa: E402
from bep_reliability_engine.gap_decomposition import (  # noqa: E402
    GapDecompositionResult,
    bootstrap_comparator_means,
    component_table,
    prepare_config,
    run_comparator_ladder,
    static_pair_shapley,
)
from bep_reliability_engine.hydrographs import (  # noqa: E402
    flood_timescales,
    load_canonical_shape,
)
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402

# --------------------------------------------------------------------------- #
# Registry                                                                      #
# --------------------------------------------------------------------------- #

#: The production shape and the approved alternate, in the order every committed
#: config records them. Read back from the configs and asserted, never trusted
#: from here.
PRODUCTION_EVENT = "HPB_m064_1987"
ALTERNATE_EVENT = "HPB_m067_1978"

#: How each arm is rendered in figure text. The record keys are the d4PDF member
#: headers and are load-bearing provenance; a main-body figure may not print a
#: run identifier, so the substitution happens at render time
#: (``docs/conventions.md`` section 9.3.1).
ARM_DISPLAY_NAMES = {
    PRODUCTION_EVENT: "compound event (production)",
    ALTERNATE_EVENT: "single-peak event",
}

#: Ladder step names as they are rendered. The keys are the analysis record's
#: own field names and are load-bearing; the substitution happens here.
STEP_DISPLAY_NAMES = {
    "head_convention": "head convention",
    "dimensional": "resistance scale",
    "initiation_gate": "initiation gate",
    "temporal_net": "time",
}

#: The eight production strata, by config stem.
STRATA: tuple[tuple[str, str, float], ...] = (
    ("kp57_4_historical_matrix", "tokachi_kp57.4_historical_matrix", 57.4),
    ("kp57_4_historical_bulk", "tokachi_kp57.4_historical_bulk", 57.4),
    ("kp58_8_historical_matrix", "tokachi_kp58.8_historical_matrix", 58.8),
    ("kp58_8_historical_bulk", "tokachi_kp58.8_historical_bulk", 58.8),
    ("kp60_0_historical_matrix", "tokachi_kp60.0_historical_matrix", 60.0),
    ("kp60_0_historical_bulk", "tokachi_kp60.0_historical_bulk", 60.0),
    ("kp62_0_historical_matrix", "tokachi_kp62.0_historical_matrix", 62.0),
    ("kp62_0_historical_bulk", "tokachi_kp62.0_historical_bulk", 62.0),
)

#: The two ADR-0040 comparator-ladder sections.
LADDER_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("kp62_0", "configs/kp62_0_historical_matrix.yaml", "stage6_6_kp62_0.h5"),
    ("kp57_4", "configs/kp57_4_historical_matrix.yaml", "stage6_6_kp57_4.h5"),
)

#: Comparators the invariance note proves peak-referenced, so shape-invariant.
INVARIANT_COMPARATORS = ("C0", "C0b", "C1", "C2", "C3a", "C3b")
#: Comparators that integrate a loading record.
CONDITIONAL_COMPARATORS = ("C4a", "C4b", "C4c", "C4d")

#: ADR-0024 top attainable stage per section; levels above are hypothetical
#: fit stabilisers and must never be plotted as attainable.
ATTAINABLE_MAX_M = {57.4: 43.25, 58.8: 42.75, 60.0: 44.25, 62.0: 50.5}

#: Rows below this count are the ``phase2_report.md`` section 11.1 small-number
#: regime and are excluded from any headline band.
SMALL_NUMBER_ROWS = 100

#: Minimum failing rows for a probability RATIO to be quotable, reusing the
#: pre-registered resolution criterion of the design-level bias resolution.
MIN_FAILING_ROWS = 30

OUT_DIR = REPO_ROOT / "results" / "canonical_shape"
ARM_DIR = OUT_DIR / "arms"
SURFACE_DIR = OUT_DIR / "surface_curves"
DEFAULT_EVIDENCE = REPO_ROOT / "docs" / "decisions" / "canonical-shape-sensitivity.json"
PREREGISTRATION = REPO_ROOT / "docs" / "decisions" / "canonical-shape-sensitivity.md"
FIGURE_NAME = "canonical_shape_sensitivity.png"

PRODUCTION_RESULTS = REPO_ROOT / "results"
STAGE6_6_DIR = REPO_ROOT / "results" / "stage6_6"
PEAK_SHORTCUT_SLICE = REPO_ROOT / "docs" / "decisions" / "phase2-peak-shortcut.json"
RQ4_ANNUAL = REPO_ROOT / "results" / "system_integration" / "phase3" / "rq4_annual.csv"

# Phase 3 production deliverable coordinates, as the annual table labels them.
# ``bep_source`` there is the CURVE side (prior or posterior), not the ADR-0038
# segment-attribution policy, which is also called "exact"; this study is
# prior-side because both its arms are Phase 1 curves.
LAMBDA_AC_M = 250.0
BEP_SOURCE = "prior"
SURFACE_VARIANT = "primary"
BEP_KPS = (57.4, 58.8, 60.0, 62.0)


# --------------------------------------------------------------------------- #
# Small helpers                                                                 #
# --------------------------------------------------------------------------- #
def _rel(path: Path) -> str:
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


def _label(kp: float) -> str:
    """Display label for a section, through the one shared conversion."""
    return figstyle.section_label(f"tokachi_kp{kp:.1f}")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


#: Where Part 2 begins. The digest below covers only what precedes it.
PART_TWO_MARKER = "\n## Part 2"


def preregistration_digest() -> str | None:
    """Digest of Part 1 alone, so appending Part 2 does not invalidate it.

    Hashing the whole note would go stale the moment the outcome was written
    into the same file, which would make the pin meaningless exactly when it
    starts to matter. What has to be immutable is the pre-registration, so the
    hash stops at the Part 2 heading.

    The text is decoded and re-encoded rather than hashed as raw bytes: this
    repository is checked out with line-ending translation, so a byte digest
    would depend on the checkout rather than on the content.
    """
    if not PREREGISTRATION.is_file():
        return None
    text = PREREGISTRATION.read_text(encoding="utf-8")
    part_one = text.split(PART_TWO_MARKER, 1)[0]
    return hashlib.sha256(part_one.encode("utf-8")).hexdigest()


def _merge_evidence(out: Path, stage: str, payload: dict[str, Any]) -> Path:
    """Merge one stage's block into the evidence record, never truncating it.

    A per-stage writer that rebuilt the file from scratch would delete the other
    stages' blocks, which is the overwriting-per-section collision the
    2026-07-30 hardening sweep had to fix twice. Stages are independently
    runnable, so merging is the only correct shape.
    """
    record: dict[str, Any] = {}
    if out.is_file():
        record = _read_json(out)
    record.setdefault(
        "record", "Canonical hydrograph shape sensitivity (defence brief item A1)"
    )
    record.setdefault("generated_by", "scripts/canonical_shape_sensitivity_study.py")
    record.setdefault("preregistration", _rel(PREREGISTRATION))
    record["preregistration_part1_sha256"] = preregistration_digest()
    record["production_event"] = PRODUCTION_EVENT
    record["alternate_event"] = ALTERNATE_EVENT
    record[stage] = payload
    record["updated"] = _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return out


def _config_with_event(config_path: Path, event_id: str) -> Config:
    """Load the committed YAML and swap the canonical member in memory.

    The on-disk config is never written. ``run.py`` selects entry 0, so the
    swapped list simply puts the wanted member first; the alternate stays
    recorded behind it exactly as the committed provenance list does.
    """
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    recorded = list(data["hydrograph_source"]["canonical_event_ids"])
    if recorded != [PRODUCTION_EVENT, ALTERNATE_EVENT]:
        raise AssertionError(
            f"{config_path.name}: canonical_event_ids is {recorded!r}, expected "
            f"{[PRODUCTION_EVENT, ALTERNATE_EVENT]!r}. This study's arm identity "
            "rests on the committed ordered list; refusing to guess."
        )
    ordered = [event_id] + [e for e in recorded if e != event_id]
    data["hydrograph_source"]["canonical_event_ids"] = ordered
    return Config.model_validate(data)


def _assert_configs_untouched(before: dict[str, str]) -> None:
    """The committed configs must be byte-identical after every arm."""
    for name, digest in before.items():
        now = _sha256(REPO_ROOT / "configs" / name)
        if now != digest:
            raise AssertionError(
                f"configs/{name} changed during this study. The arm route is an "
                "in-memory YAML swap and must never write a committed config."
            )


def _config_digests() -> dict[str, str]:
    return {p.name: _sha256(p) for p in sorted((REPO_ROOT / "configs").glob("*.yaml"))}


def _paired_delta_ci(
    a: np.ndarray, b: np.ndarray, *, n_replicates: int = 2000, seed: int = 20260810
) -> tuple[np.ndarray, np.ndarray]:
    """Paired bootstrap interval on ``mean(a) - mean(b)`` over shared rows.

    ``a`` and ``b`` are (N, N_h) boolean failure matrices evaluated on the SAME
    prior sample, so one row-index draw is shared by both arms within a
    replicate. That pairing is what makes the interval reflect the discordant
    set rather than two independent binomials, exactly as the ADR-0040
    component CIs do.
    """
    rng = np.random.default_rng(seed)
    n = a.shape[0]
    deltas = np.empty((n_replicates, a.shape[1]), dtype=np.float64)
    for b_i in range(n_replicates):
        idx = rng.integers(0, n, size=n)
        deltas[b_i] = a[idx].mean(axis=0) - b[idx].mean(axis=0)
    lo, hi = np.percentile(deltas, [2.5, 97.5], axis=0)
    return lo, hi


def _anchor_indices(
    grid: np.ndarray, p_base: np.ndarray, *, hwl: float, peak_2016: float | None
) -> dict[str, int]:
    """The pre-registered anchors, as grid indices.

    Named in advance and never called "the shoulder": the same word means two
    stages two orders of magnitude apart in probability elsewhere in this
    project, so the anchors carry their definitions.
    """
    anchors = {
        "design_level_anchor": int(np.argmin(np.abs(grid - hwl))),
        "transition_midpoint": int(np.argmin(np.abs(p_base - 0.5))),
        "grid_top": int(grid.size - 1),
    }
    if peak_2016 is not None:
        anchors["observed_2016_peak"] = int(np.argmin(np.abs(grid - peak_2016)))
    return anchors


# --------------------------------------------------------------------------- #
# Stage: shape statistics                                                       #
# --------------------------------------------------------------------------- #
def stage_shape(out: Path) -> dict[str, Any]:
    """Measure both members' normalised stage shapes, definition-matched.

    The published 23 h, 18 h, 10 h and 55 h for the production member come from
    ``flood_timescales``; the alternate's recorded "32 h rise" is of unstated
    definition. Running the same function on both is what makes them
    comparable, so the provenance figure is treated as provenance and the
    measurement replaces it.
    """
    config = Config.from_yaml(REPO_ROOT / "configs" / "kp58_8_historical_matrix.yaml")
    source = config.hydrograph_source
    assert source is not None
    members: dict[str, Any] = {}
    for event_id in (PRODUCTION_EVENT, ALTERNATE_EVENT):
        canonical = load_canonical_shape(
            source.data_root, river=source.river, kp=source.kp, event_id=event_id
        )
        record = canonical.source_record
        stats = flood_timescales(np.asarray(record.h), float(record.native_dt))
        shape = np.asarray(canonical.shape, dtype=float)
        dt_h = float(record.native_dt) / 3600.0
        members[event_id] = {
            "rising_limb_h": stats["rising_limb_s"] / 3600.0,
            "rise_10_90_h": stats["rise_10_90_s"] / 3600.0,
            "plateau_h": stats["plateau_s"] / 3600.0,
            "fwhm_h": stats["fwhm_s"] / 3600.0,
            "peak_stage_m_msl": stats["peak_m"],
            "amplitude_m": stats["amplitude_m"],
            "h_base_m_msl": float(canonical.h_base_m),
            "native_dt_s": float(record.native_dt),
            # Time at or above a shape fraction: the currency the barrier
            # actually charges in, since erosion only advances near the crest.
            "hours_above_shape": {
                f"{frac:.2f}": float(np.count_nonzero(shape >= frac) * dt_h)
                for frac in (0.25, 0.50, 0.75, 0.90, 0.95)
            },
            "n_local_maxima_above_half": int(
                np.count_nonzero(
                    (shape[1:-1] > shape[:-2])
                    & (shape[1:-1] >= shape[2:])
                    & (shape[1:-1] >= 0.5)
                )
            ),
        }
    prod = members[PRODUCTION_EVENT]
    alt = members[ALTERNATE_EVENT]
    payload = {
        "note": (
            "Both members measured with the same function that produced the "
            "published production-member timescales, so the numbers are "
            "commensurable. Hours above a shape fraction is the statistic the "
            "progression barrier responds to: a pipe only advances while the "
            "instantaneous head exceeds the equilibrium head, which happens "
            "close to the crest."
        ),
        "members": members,
        "comparison": {
            "rising_limb_ratio_alt_over_prod": alt["rising_limb_h"]
            / prod["rising_limb_h"],
            "fwhm_ratio_alt_over_prod": alt["fwhm_h"] / prod["fwhm_h"],
            "hours_above_0.90_ratio_alt_over_prod": (
                alt["hours_above_shape"]["0.90"] / prod["hours_above_shape"]["0.90"]
                if prod["hours_above_shape"]["0.90"] > 0
                else None
            ),
        },
    }
    _merge_evidence(out, "shape", payload)
    for event_id, m in members.items():
        print(
            f"  {event_id}: rise {m['rising_limb_h']:.1f} h, 10-90 "
            f"{m['rise_10_90_h']:.1f} h, plateau {m['plateau_h']:.1f} h, "
            f"half-amplitude {m['fwhm_h']:.1f} h, "
            f"maxima above half {m['n_local_maxima_above_half']}",
            flush=True,
        )
    return payload


# --------------------------------------------------------------------------- #
# Stage: Phase 1, all eight strata                                              #
# --------------------------------------------------------------------------- #
def _assert_baseline_bit_identical(result, production_path: Path, label: str) -> None:
    """Gate 1. Refuse to report a sensitivity against a drifted baseline."""
    with h5py.File(production_path, "r") as handle:
        prod_static = np.asarray(handle["P_f_static_raw"])
        prod_trans = np.asarray(handle["P_f_trans_raw"])
    d_static = float(np.max(np.abs(result.P_f_static_raw - prod_static)))
    d_trans = float(np.max(np.abs(result.P_f_trans_raw - prod_trans)))
    if d_static != 0.0 or d_trans != 0.0:
        raise AssertionError(
            f"GATE 1 FAILED for {label}: the baseline arm is not bit-identical to "
            f"the persisted production sweep {production_path.name} "
            f"(max abs difference static {d_static:.3e}, transient {d_trans:.3e})."
        )


def _stratum_record(
    stem: str, run_stem: str, kp: float, *, n_jobs: int, peaks_2016: dict[str, float]
) -> dict[str, Any]:
    config_path = REPO_ROOT / "configs" / f"{stem}.yaml"
    production_path = PRODUCTION_RESULTS / f"{run_stem}.h5"
    started = time.time()

    baseline = run_fragility_analysis(
        _config_with_event(config_path, PRODUCTION_EVENT),
        n_jobs=n_jobs,
        progress=False,
        persist=False,
    )
    _assert_baseline_bit_identical(baseline, production_path, run_stem)
    arm = run_fragility_analysis(
        _config_with_event(config_path, ALTERNATE_EVENT),
        n_jobs=n_jobs,
        progress=False,
        persist=False,
    )

    # GATE 2. The static comparator reads the scalar conditioning level verbatim
    # and never touches the loading record, so this is exact equality, not
    # tolerance. One bit of movement voids the run.
    static_delta = np.abs(arm.P_f_static_raw - baseline.P_f_static_raw)
    if float(static_delta.max()) != 0.0:
        raise AssertionError(
            f"GATE 2 FAILED for {run_stem}: the raw static probabilities moved "
            f"with the canonical member (max abs difference "
            f"{float(static_delta.max()):.3e}). The static branch consumes only "
            "the scalar conditioning level; this is a harness defect and the "
            "run is void."
        )
    if not np.array_equal(baseline.theta_matrix, arm.theta_matrix):
        raise AssertionError(
            f"{run_stem}: the two arms do not share one prior sample; the "
            "comparison would not be paired."
        )

    grid = np.asarray(baseline.conditioning_grid, dtype=float)
    base_trans = np.asarray(baseline.failure_matrix_tran, dtype=bool)
    arm_trans = np.asarray(arm.failure_matrix_tran, dtype=bool)
    p_base = np.asarray(baseline.P_f_trans_raw, dtype=float)
    p_arm = np.asarray(arm.P_f_trans_raw, dtype=float)
    delta = p_arm - p_base
    lo, hi = _paired_delta_ci(arm_trans, base_trans)
    resolved = (lo > 0.0) | (hi < 0.0)
    n = int(baseline.theta_matrix.shape[0])
    cp_lo, cp_hi = binomial_ci(p_base, n)

    hwl = float(Config.from_yaml(config_path).geometry.HWL)
    anchors = _anchor_indices(grid, p_base, hwl=hwl, peak_2016=peaks_2016.get(run_stem))
    worst = int(np.argmax(np.abs(delta)))

    # Persist both arms' curves so the later stages consume artifacts rather
    # than re-running the sweeps.
    ARM_DIR.mkdir(parents=True, exist_ok=True)
    for tag, result in (("production", baseline), ("alternate", arm)):
        result.save(ARM_DIR / f"{run_stem}_{tag}.h5")

    record = {
        "stratum": run_stem,
        "section": _label(kp),
        "kp": kp,
        "config": f"configs/{stem}.yaml",
        "production_sweep": _rel(production_path),
        "n_samples": n,
        "gate_1_baseline_bit_identical": True,
        "gate_2_static_exactly_invariant": True,
        "hwl_m_msl": hwl,
        "attainable_max_m_msl": ATTAINABLE_MAX_M[kp],
        "levels_m_msl": grid.tolist(),
        "p_f_trans_production": p_base.tolist(),
        "p_f_trans_alternate": p_arm.tolist(),
        "delta": delta.tolist(),
        "delta_ci": [lo.tolist(), hi.tolist()],
        "resolved": resolved.tolist(),
        "clopper_pearson_production": [cp_lo.tolist(), cp_hi.tolist()],
        "p_f_static": np.asarray(baseline.P_f_static_raw, dtype=float).tolist(),
        "max_abs_delta": float(np.abs(delta).max()),
        "max_abs_delta_at_stage_m_msl": float(grid[worst]),
        "max_abs_delta_resolved": bool(resolved[worst]),
        "n_levels_resolved": int(resolved.sum()),
        "anchors": {
            name: {
                "stage_m_msl": float(grid[i]),
                "p_f_trans_production": float(p_base[i]),
                "p_f_trans_alternate": float(p_arm[i]),
                "delta": float(delta[i]),
                "ratio": (float(p_arm[i] / p_base[i]) if p_base[i] > 0.0 else None),
                "resolved": bool(resolved[i]),
                "clopper_pearson_half_width_production": float(
                    (cp_hi[i] - cp_lo[i]) / 2.0
                ),
                "above_attainable_max": bool(grid[i] > ATTAINABLE_MAX_M[kp]),
            }
            for name, i in anchors.items()
        },
        "elapsed_s": round(time.time() - started, 1),
    }
    return record


def stage_phase1(out: Path, *, n_jobs: int, strata: list[str]) -> dict[str, Any]:
    """Run both arms at every requested stratum under gates 1 and 2."""
    digests = _config_digests()
    peaks_2016 = {}
    if PEAK_SHORTCUT_SLICE.is_file():
        peaks_2016 = {
            s["stratum"]: float(s["event_peak_m_msl"])
            for s in _read_json(PEAK_SHORTCUT_SLICE)["strata"]
        }

    existing = _read_json(out).get("phase1", {}) if out.is_file() else {}
    records: dict[str, Any] = dict(existing.get("strata", {}))
    for stem, run_stem, kp in STRATA:
        if strata and stem not in strata:
            continue
        print(f"[{run_stem}] two arms ...", flush=True)
        record = _stratum_record(
            stem, run_stem, kp, n_jobs=n_jobs, peaks_2016=peaks_2016
        )
        records[run_stem] = record
        # Persisted per stratum, not once at the end: each arm pair costs
        # minutes, and a driver that loses a completed stratum because a later
        # one failed is the shape this repository has had to fix twice.
        _merge_evidence(out, "phase1", _phase1_payload(records))
        print(
            f"  max abs difference {record['max_abs_delta']:.5f} at "
            f"{record['max_abs_delta_at_stage_m_msl']:.2f} m MSL "
            f"({record['n_levels_resolved']} of {len(record['levels_m_msl'])} "
            f"levels resolved); {record['elapsed_s']:.0f} s",
            flush=True,
        )
    _assert_configs_untouched(digests)
    payload = _phase1_payload(records)
    _merge_evidence(out, "phase1", payload)
    return payload


def _phase1_payload(records: dict[str, Any]) -> dict[str, Any]:
    """Assemble the stage block from whatever strata are complete."""
    ordered = [r for _, run_stem, _ in STRATA if (r := records.get(run_stem))]
    signs = [
        np.sign(r["anchors"]["transition_midpoint"]["delta"])
        for r in ordered
        if r["anchors"]["transition_midpoint"]["resolved"]
    ]
    return {
        "note": (
            "Both arms share one prior sample, so every difference is physical "
            "and the bootstrap interval is paired over shared row indices. "
            "Gate 1 asserts each baseline against its persisted production "
            "sweep; gate 2 asserts the raw static probabilities exactly equal "
            "between arms."
        ),
        "gates": {
            "gate_1_baseline_bit_identical": all(
                r["gate_1_baseline_bit_identical"] for r in ordered
            ),
            "gate_2_static_exactly_invariant": all(
                r["gate_2_static_exactly_invariant"] for r in ordered
            ),
            "committed_configs_unchanged": True,
            "n_strata": len(ordered),
        },
        "direction_at_transition_midpoint": {
            "n_resolved": len(signs),
            "n_positive": int(sum(1 for s in signs if s > 0)),
            "n_negative": int(sum(1 for s in signs if s < 0)),
            "unanimous": bool(len(set(signs)) <= 1) if signs else None,
        },
        "strata": records,
    }


# --------------------------------------------------------------------------- #
# Stage: the comparator ladder                                                  #
# --------------------------------------------------------------------------- #
def stage_ladder(out: Path, *, n_jobs: int, sections: list[str]) -> dict[str, Any]:
    """Run the alternate-shape ladder and compare it to the persisted record.

    The production ladder is not re-run: ``results/stage6_6/`` already holds it,
    gate-verified bit-identical to the persisted production sweep by its own
    driver, so loading it is both cheaper and better evidence. Gate 3 then
    doubles as proof that this harness reproduces that guarded record on every
    comparator the shape cannot reach.

    Nothing is written to ``results/stage6_6/`` and no tracked figure is
    touched: the Stage 6.6 driver has no shape axis and no output directory, and
    since 2026-08-10 it correctly refuses a mismatched config rather than
    skipping. That refusal is respected, not bypassed; this stage drives the
    ladder kernel directly instead.
    """
    existing = _read_json(out).get("ladder", {}) if out.is_file() else {}
    records: dict[str, Any] = dict(existing.get("sections", {}))
    digests = _config_digests()

    for key, config_rel, persisted_name in LADDER_SECTIONS:
        if sections and key not in sections:
            continue
        persisted = STAGE6_6_DIR / persisted_name
        if not persisted.is_file():
            raise FileNotFoundError(
                f"missing the persisted production ladder {_rel(persisted)}. "
                "Regenerate with scripts/stage6_6_gap_decomposition.py; this "
                "study consumes it read-only and never writes results/stage6_6/."
            )
        print(f"[{key}] alternate-shape ladder ...", flush=True)
        started = time.time()
        base_result = GapDecompositionResult.load(persisted)
        config = _config_with_event(REPO_ROOT / config_rel, ALTERNATE_EVENT)
        hwl = float(config.geometry.HWL)
        arm_result = run_comparator_ladder(
            prepare_config(config, extra_levels=(hwl,)),
            n_jobs=n_jobs,
            progress=False,
        )

        base_grid = np.asarray(base_result.conditioning_grid, dtype=float)
        arm_grid = np.asarray(arm_result.conditioning_grid, dtype=float)
        if not np.array_equal(base_grid, arm_grid):
            raise AssertionError(
                f"{key}: the arm grid does not match the persisted ladder grid; "
                "the comparison would not be level for level."
            )
        if not np.array_equal(base_result.theta_matrix, arm_result.theta_matrix):
            raise AssertionError(
                f"{key}: the arm and the persisted ladder do not share one prior "
                "sample; the comparison would not be paired."
            )

        # GATE 3. Six comparators are peak-referenced (four statics and the two
        # analytic sustained-peak limits) and cannot see a loading record.
        gate3: dict[str, Any] = {}
        for name in INVARIANT_COMPARATORS:
            identical = bool(
                np.array_equal(
                    base_result.comparators[name], arm_result.comparators[name]
                )
            )
            gate3[name] = identical
            if not identical:
                moved = int(
                    np.count_nonzero(
                        base_result.comparators[name] != arm_result.comparators[name]
                    )
                )
                raise AssertionError(
                    f"GATE 3 FAILED at {key}: comparator {name} moved with the "
                    f"canonical member ({moved} flags differ). It is "
                    "peak-referenced and cannot integrate a loading record; "
                    "this is a harness defect and the run is void."
                )

        # The production side is READ from the persisted analysis rather than
        # recomputed, so the comparison is against the published table itself
        # and not against a second derivation of it. Its own probabilities are
        # re-derived from the matrices first, which checks the two halves of the
        # persisted record against each other for free.
        base_analysis = _read_json(
            persisted.with_name(f"{persisted.stem}_analysis.json")
        )
        base_p = base_result.p_f()
        for name, published in base_analysis["p_f"].items():
            if not np.allclose(base_p[name], np.asarray(published), atol=0.0, rtol=0.0):
                raise AssertionError(
                    f"{key}: comparator {name} in the persisted ladder matrices "
                    "does not reproduce the persisted analysis table."
                )
        base_table = base_analysis["components"]
        base_shapley = base_analysis["static_pair_shapley"]

        arm_boot = bootstrap_comparator_means(arm_result, n_replicates=1000)
        arm_table = component_table(arm_result, arm_boot)
        arm_shapley = static_pair_shapley(arm_result, arm_boot)

        shapley_identical = all(
            np.array_equal(
                np.asarray(base_shapley[name]["delta"]),
                np.asarray(arm_shapley[name]["delta"]),
            )
            for name in base_shapley
            if isinstance(base_shapley[name], dict) and "delta" in base_shapley[name]
        )
        if not shapley_identical:
            raise AssertionError(
                f"GATE 3 FAILED at {key}: the static Shapley lattice moved. Every "
                "expression there is a linear combination of the four static "
                "comparators, all of which gate 3 just proved invariant."
            )
        gate3["static_shapley_lattice"] = True

        arm_p = arm_result.p_f()
        anchors = {
            "design_level_anchor": int(np.argmin(np.abs(base_grid - hwl))),
            "transition_midpoint": int(np.argmin(np.abs(base_p["C4b"] - 0.5))),
            "grid_top": int(base_grid.size - 1),
        }
        # The design anchor rests on a handful of failing rows at this sample
        # size, and a ratio built on a handful of rows is counting noise -- the
        # finding that turned an unresolved 44.7 into a resolved 26.9 once the
        # sample was raised. So a second anchor is carried at the lowest level
        # where BOTH arms clear the same k >= 30 criterion that resolution
        # analysis pre-registered, and every ratio is reported with its row
        # count beside it.
        k_base = base_result.comparators["C4b"].sum(axis=0)
        k_arm = arm_result.comparators["C4b"].sum(axis=0)
        adequate = np.nonzero(
            (k_base >= MIN_FAILING_ROWS) & (k_arm >= MIN_FAILING_ROWS)
        )[0]
        if adequate.size:
            anchors["lowest_adequately_sampled_level"] = int(adequate[0])

        moved: dict[str, Any] = {}
        for name in CONDITIONAL_COMPARATORS:
            d = arm_p[name] - base_p[name]
            moved[name] = {
                "delta": d.tolist(),
                "max_abs_delta": float(np.abs(d).max()),
                "at_stage_m_msl": float(base_grid[int(np.argmax(np.abs(d)))]),
            }

        components: dict[str, Any] = {}
        for ladder_name in ("physics", "engine"):
            base_l = base_table["ladders"][ladder_name]
            arm_l = arm_table["ladders"][ladder_name]
            steps: dict[str, Any] = {}
            for step_name, base_step in base_l["steps"].items():
                arm_step = arm_l["steps"][step_name]
                b_delta = np.asarray(base_step["delta"], dtype=float)
                a_delta = np.asarray(arm_step["delta"], dtype=float)
                b_share = np.asarray(base_step["fraction_of_total"], dtype=float)
                a_share = np.asarray(arm_step["fraction_of_total"], dtype=float)
                steps[step_name] = {
                    "component_production": b_delta.tolist(),
                    "component_alternate": a_delta.tolist(),
                    "component_exactly_invariant": bool(
                        np.array_equal(b_delta, a_delta)
                    ),
                    "share_production": b_share.tolist(),
                    "share_alternate": a_share.tolist(),
                    "anchors": {
                        aname: {
                            "stage_m_msl": float(base_grid[i]),
                            "component_production": float(b_delta[i]),
                            "component_alternate": float(a_delta[i]),
                            "share_production": float(b_share[i]),
                            "share_alternate": float(a_share[i]),
                        }
                        for aname, i in anchors.items()
                    },
                }
            b_total = np.asarray(base_l["total_gap"], dtype=float)
            a_total = np.asarray(arm_l["total_gap"], dtype=float)
            components[ladder_name] = {
                "endpoint": base_l["endpoint"],
                "total_gap_production": b_total.tolist(),
                "total_gap_alternate": a_total.tolist(),
                "steps": steps,
            }

        auxiliary = {}
        for name, base_aux in base_table["auxiliary"].items():
            b = np.asarray(base_aux["delta"], dtype=float)
            a = np.asarray(arm_table["auxiliary"][name]["delta"], dtype=float)
            auxiliary[name] = {
                "production": b.tolist(),
                "alternate": a.tolist(),
                "exactly_invariant": bool(np.array_equal(a, b)),
                "max_abs_change": float(np.abs(a - b).max()),
            }

        # The static-to-transient bias, whose one-sidedness is the opposite of
        # the peak-only factor's: an invariant numerator over a conditional
        # denominator. Reported at both the design anchor and the lowest
        # adequately sampled level, each carrying its own row counts, so a ratio
        # built on a handful of rows can never be read as a measurement.
        def _bias_at(i: int) -> dict[str, Any]:
            k_p = int(base_result.comparators["C4b"][:, i].sum())
            k_a = int(arm_result.comparators["C4b"][:, i].sum())
            return {
                "stage_m_msl": float(base_grid[i]),
                "static_p_f": float(base_p["C0"][i]),
                "transient_p_f_production": float(base_p["C4b"][i]),
                "transient_p_f_alternate": float(arm_p["C4b"][i]),
                "n_failing_rows_production": k_p,
                "n_failing_rows_alternate": k_a,
                "adequately_sampled": bool(
                    k_p >= MIN_FAILING_ROWS and k_a >= MIN_FAILING_ROWS
                ),
                "bias_production": (
                    float(base_p["C0"][i] / base_p["C4b"][i])
                    if base_p["C4b"][i] > 0.0
                    else None
                ),
                "bias_alternate": (
                    float(base_p["C0"][i] / arm_p["C4b"][i])
                    if arm_p["C4b"][i] > 0.0
                    else None
                ),
            }

        bias = {
            "design_hwl_m_msl": hwl,
            "minimum_failing_rows_for_a_quotable_ratio": MIN_FAILING_ROWS,
            "at": {name: _bias_at(i) for name, i in anchors.items()},
        }

        records[key] = {
            "section": _label(float(key.replace("kp", "").replace("_", "."))),
            "config": config_rel,
            "persisted_production_ladder": _rel(persisted),
            "n_samples": int(base_result.n_samples),
            "levels_m_msl": base_grid.tolist(),
            "gate_3": gate3,
            "conditional_comparators": moved,
            "components": components,
            "auxiliary": auxiliary,
            "design_level_bias": bias,
            "euler_flips_alternate": {
                k: int(np.asarray(v).sum()) for k, v in arm_result.flip_counts.items()
            },
            "euler_flips_production": {
                k: int(np.asarray(v).sum()) for k, v in base_result.flip_counts.items()
            },
            "elapsed_s": round(time.time() - started, 1),
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        arm_result.save(OUT_DIR / f"ladder_{key}_alternate.h5")
        # Persisted per section for the same reason the Phase 1 stage is: one
        # section costs a quarter of an hour, and losing a completed one because
        # the next failed is the collision this repository has already fixed
        # twice in its own drivers.
        _merge_evidence(out, "ladder", _ladder_payload(records))
        print(
            f"  gate 3 passed on {len(INVARIANT_COMPARATORS)} comparators and "
            f"the static lattice; transient comparator maximum change "
            f"{moved['C4b']['max_abs_delta']:.5f}; "
            f"{records[key]['elapsed_s']:.0f} s",
            flush=True,
        )

    _assert_configs_untouched(digests)
    payload = _ladder_payload(records)
    _merge_evidence(out, "ladder", payload)
    return payload


def _ladder_payload(records: dict[str, Any]) -> dict[str, Any]:
    """Assemble the stage block from whatever sections are complete."""
    return {
        "note": (
            "The production ladder is the persisted, gate-verified record; only "
            "the alternate arm is computed here. Gate 3 asserts the four static "
            "comparators, the two analytic sustained-peak limits and the whole "
            "static Shapley lattice bit-identical between the arms, so exactly "
            "one telescoping step in each ladder is shape-exposed."
        ),
        "invariant_comparators": list(INVARIANT_COMPARATORS),
        "sections": records,
    }


# --------------------------------------------------------------------------- #
# Stage: the peak-shortcut factor                                               #
# --------------------------------------------------------------------------- #
def stage_peak_shortcut(out: Path) -> dict[str, Any]:
    """Recompute the peak-only numerator on the alternate-shape curves.

    Phase 2 is deliberately NOT re-run. The replay drives the observed 2016
    record built from the Obihiro gauge series and the surveyed flood trace, so
    the denominator is shape-independent by construction; the invariance note
    settles that from source and it is re-asserted here by reading the same
    committed slice the published factors come from. Only the numerator moves.

    The three cases the committed slice keeps apart are kept apart: a factor is
    ``None`` where the replay rejects nothing (not defined, never 1), and a
    stratum whose replay rejects fewer than the small-number threshold stays in
    the record but out of the headline band.
    """
    slice_ = _read_json(PEAK_SHORTCUT_SLICE)
    strata: list[dict[str, Any]] = []
    for published in slice_["strata"]:
        stem = published["stratum"]
        arm_path = ARM_DIR / f"{stem}_alternate.h5"
        base_path = ARM_DIR / f"{stem}_production.h5"
        if not arm_path.is_file() or not base_path.is_file():
            raise FileNotFoundError(
                f"missing arm curves for {stem}; run the phase1 stage first."
            )
        peak = float(published["event_peak_m_msl"])
        replay = float(published["f_replay_transient"])
        base = FragilityResult.load(base_path)
        arm = FragilityResult.load(arm_path)
        grid = np.asarray(base.conditioning_grid, dtype=float)

        # The published reading, reproduced from this study's own baseline arm
        # before the alternate is reported: linear interpolation of the raw
        # Monte Carlo points, not the fitted lognormal and not probit.
        peak_only_base = float(
            np.interp(peak, grid, np.asarray(base.P_f_trans_raw, dtype=float))
        )
        peak_only_arm = float(
            np.interp(
                peak,
                np.asarray(arm.conditioning_grid, dtype=float),
                np.asarray(arm.P_f_trans_raw, dtype=float),
            )
        )
        if abs(peak_only_base - float(published["f_peak_only_transient"])) > 1e-12:
            raise AssertionError(
                f"{stem}: this study's baseline peak-only reading "
                f"{peak_only_base!r} does not reproduce the committed slice's "
                f"{published['f_peak_only_transient']!r}."
            )
        strata.append(
            {
                "stratum": stem,
                "section": published["section"],
                "d70": published["d70"],
                "event_peak_m_msl": peak,
                "f_replay_transient": replay,
                "f_replay_is_shape_invariant": True,
                "f_peak_only_production": peak_only_base,
                "f_peak_only_alternate": peak_only_arm,
                "factor_production": published["over_rejection_factor"],
                "factor_alternate": (
                    (peak_only_arm / replay) if replay > 0.0 else None
                ),
                "n_rejected_replay": published["n_rejected_replay"],
                "small_number_regime": published["small_number_regime"],
            }
        )

    informative = [
        s
        for s in strata
        if s["factor_alternate"] is not None and not s["small_number_regime"]
    ]
    payload = {
        "note": (
            "The denominator is the Phase 2 rejection fraction, which the "
            "replay computes from the observed 2016 record and not from any "
            "canonical member, so it is exactly invariant and Phase 2 was not "
            "re-run. The numerator is the prior transient curve read at the "
            "observed peak, which is where the shape enters. Exposure is "
            "therefore one-sided."
        ),
        "small_number_rows": SMALL_NUMBER_ROWS,
        "strata": strata,
        "headline": {
            "informative_strata": [s["stratum"] for s in informative],
            "factor_production_min": min(s["factor_production"] for s in informative),
            "factor_production_max": max(s["factor_production"] for s in informative),
            "factor_alternate_min": min(s["factor_alternate"] for s in informative),
            "factor_alternate_max": max(s["factor_alternate"] for s in informative),
            "n_not_defined": sum(1 for s in strata if s["factor_alternate"] is None),
        },
    }
    _merge_evidence(out, "peak_shortcut", payload)
    for s in strata:
        if s["factor_alternate"] is None:
            print(f"  {s['stratum']}: not defined under either reading", flush=True)
        else:
            print(
                f"  {s['stratum']}: {s['factor_production']:.3f} -> "
                f"{s['factor_alternate']:.3f}"
                + ("  (small-number regime)" if s["small_number_regime"] else ""),
                flush=True,
            )
    return payload


# --------------------------------------------------------------------------- #
# Stage: Phase 3                                                                #
# --------------------------------------------------------------------------- #
def _load_module(name: str):
    """Import a ``scripts/`` driver for reuse, never re-implementing it."""
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def stage_surface(out: Path) -> dict[str, Any]:
    """Regenerate the Uemura surface curves on the alternate member.

    The overflow model is a duration-above-crest mechanism conditioned on the
    SAME pinned member as the piping curves, so swapping only the piping side
    would change the numerator of the dominance share while leaving the other
    mechanisms on the old shape, confounding shape with mechanism in exactly the
    quantity the dominance question reports. The committed contract CSVs under
    ``data/processed/uemura_surface_curves/`` are never touched: this writes to
    a study-local directory under gitignored ``results/``.
    """
    generator = _load_module("generate_uemura_surface_curves")
    committed_dir = generator.OUT_DIR
    committed_before = {
        p.name: _sha256(p) for p in sorted(committed_dir.glob("*")) if p.is_file()
    }
    SURFACE_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    # The generator reads its member and its output directory from module
    # globals, so rebinding them is enough and the shipped driver is not
    # edited. Its argument parser exists only to make a probe inert, so argv is
    # blanked rather than extended.
    generator.CANONICAL_EVENT = ALTERNATE_EVENT
    generator.OUT_DIR = SURFACE_DIR
    saved_argv = sys.argv
    try:
        sys.argv = [str(REPO_ROOT / "scripts" / "generate_uemura_surface_curves.py")]
        generator.main()
    finally:
        sys.argv = saved_argv
    committed_after = {
        p.name: _sha256(p) for p in sorted(committed_dir.glob("*")) if p.is_file()
    }
    if committed_after != committed_before:
        raise AssertionError(
            "the committed Uemura surface-curve contract changed during this "
            "study; the alternate-shape curves must be written to a study-local "
            "directory only."
        )
    payload = {
        "note": (
            "Overflow and fluvial scour re-executed on the alternate member so "
            "the dominance share compares like with like. The committed "
            "contract set is asserted unchanged."
        ),
        "out_dir": _rel(SURFACE_DIR),
        "canonical_event": ALTERNATE_EVENT,
        "committed_contract_unchanged": True,
        "files": sorted(p.name for p in SURFACE_DIR.glob("*.csv")),
        "elapsed_s": round(time.time() - started, 1),
    }
    _merge_evidence(out, "surface", payload)
    return payload


def stage_phase3(out: Path, *, surface_variant: str) -> dict[str, Any]:
    """Compose and annualise both arms over the 114-segment reach.

    The composition step is imported from ``scripts/phase3_campaign.py`` rather
    than re-implemented, so the baseline gate exercises the production code
    path. Nothing is written to ``results/system_integration/phase3/``; the
    hazard cache is consumed read-only and asserted unchanged (gate 4).
    """
    from system_integration.annualize import annualize
    from system_integration.bep_input import load_bep_curve
    from system_integration.hazard import load_reach_hazard
    from system_integration.segments import build_registry, load_section_table
    from system_integration.surface_curves import SurfaceCurveSet, load_surface_curves
    from system_integration.uemura_models import load_segment_inputs

    campaign = _load_module("phase3_campaign")
    cache_before = {
        p.name: _sha256(p) for p in sorted(campaign.HAZARD_CACHE.glob("*.csv"))
    }

    registry = load_section_table(
        campaign.SECTION_TABLE, build_registry(campaign.DATA_ROOT), allow_gaps=True
    )
    seg_inputs = load_segment_inputs(campaign.SEGMENT_INPUTS)

    def _surface(paths) -> SurfaceCurveSet:
        parts = [load_surface_curves(p) for p in paths]
        return SurfaceCurveSet(
            curves=tuple(c for part in parts for c in part.curves),
            source="uemura_csv",
        )

    surfaces = {"production": _surface(campaign.PRIMARY_FILES)}
    if surface_variant == "alternate":
        alt_files = [SURFACE_DIR / p.name for p in campaign.PRIMARY_FILES]
        missing = [p for p in alt_files if not p.is_file()]
        if missing:
            raise FileNotFoundError(
                f"no alternate-shape surface curves in {_rel(SURFACE_DIR)}; run "
                "the surface stage first, or pass --surface production and scope "
                "every dominance number to the piping side."
            )
        surfaces["alternate"] = _surface(alt_files)
    else:
        surfaces["alternate"] = surfaces["production"]

    # The production side reads the PERSISTED production sweeps, not this
    # study's re-run copies of them. Gate 1 already proved the two agree on the
    # probability vectors; using the deliverable's own files here means the
    # baseline gate tests the composition rather than a re-save.
    curves = {
        "production": {
            kp: load_bep_curve(
                PRODUCTION_RESULTS / f"tokachi_kp{kp:.1f}_historical_matrix.h5",
                branch="transient",
            )
            for kp in BEP_KPS
        },
        "alternate": {
            kp: load_bep_curve(
                ARM_DIR / f"tokachi_kp{kp:.1f}_historical_matrix_alternate.h5",
                branch="transient",
            )
            for kp in BEP_KPS
        },
    }
    node_datum = {kp: curves["production"][kp].datum_m for kp in BEP_KPS}
    nodes = [
        (
            s.river,
            s.kp,
            (
                node_datum[s.kp]
                if s.bep_source_kp is not None
                else seg_inputs[(s.river, round(s.kp, 3))].ground_m_msl
            ),
        )
        for s in registry.segments
    ]
    hazards = {
        scenario: load_reach_hazard(
            campaign.DATA_ROOT,
            nodes=nodes,
            scenario=scenario,
            cache_dir=campaign.HAZARD_CACHE,
        )
        for scenario in campaign.SCENARIOS
    }
    n_eff = max(1.0, campaign.SEGMENT_LENGTH_M / LAMBDA_AC_M)

    def _pass(arm: str) -> dict[tuple[str, float, str], dict[str, Any]]:
        rows: dict[tuple[str, float, str], dict[str, Any]] = {}
        for segment in registry.segments:
            bep = (
                curves[arm].get(segment.kp)
                if segment.bep_source_kp is not None
                else None
            )
            frag, clamped = campaign._compose_segment(
                segment, surfaces[arm], bep, n_eff, "historical"
            )
            if frag is None:
                continue
            key = (segment.river, round(segment.kp, 3))
            for scenario in campaign.SCENARIOS:
                annual = annualize(frag, hazards[scenario][key])
                row: dict[str, Any] = {
                    "river": segment.river,
                    "kp": segment.kp,
                    "scenario": scenario,
                    "p_annual_system": annual.p_f_annual_system,
                    "bep_clamped_above_grid": clamped,
                }
                for mech in ("bep", "overflow", "fluvial_scour"):
                    row[f"p_annual_{mech}"] = annual.p_f_annual_per_mechanism.get(
                        mech, ""
                    )
                    row[f"share_{mech}"] = (
                        annual.dominance_share(mech) if mech in frag.mechanisms else ""
                    )
                rows[(segment.river, segment.kp, scenario)] = row
        return rows

    base_rows = _pass("production")
    arm_rows = _pass("alternate")

    # Gate: the baseline pass reproduces the published production table exactly
    # on the four BEP sections, so the arm is measured against the deliverable.
    import csv

    with open(RQ4_ANNUAL, encoding="utf-8", newline="") as handle:
        published = [
            r
            for r in csv.DictReader(handle)
            if r["d70"] == "matrix"
            and r["bep_source"] == BEP_SOURCE
            and r["lambda_ac_m"] == str(LAMBDA_AC_M)
            and r["surface_variant"] == SURFACE_VARIANT
        ]
    # A filter that selects nothing would make the gate below pass on an empty
    # loop, which is the vacuous-pass shape this repository has had to fix in
    # its own gates twice.
    if len(published) != 228:
        raise AssertionError(
            f"the {SURFACE_VARIANT}/{BEP_SOURCE}/{LAMBDA_AC_M:g} matrix slice of "
            f"{_rel(RQ4_ANNUAL)} selected {len(published)} rows, expected 228 "
            "(114 segments x 2 climates). Refusing to gate on an empty or "
            "partial selection."
        )
    mismatches: list[str] = []
    checked = 0
    for record in published:
        key = (record["river"], float(record["kp"]), record["scenario"])
        mine = base_rows.get(key)
        if mine is None:
            mismatches.append(f"{key}: missing from the baseline pass")
            continue
        checked += 1
        for field in ("p_annual_system", "p_annual_bep", "share_bep"):
            if str(mine[field]) != record[field]:
                mismatches.append(
                    f"{key} {field}: published {record[field]!r} != "
                    f"reproduced {str(mine[field])!r}"
                )
    if mismatches:
        raise AssertionError(
            "the baseline Phase 3 pass does not reproduce the published annual "
            "table; refusing to report a sensitivity against a drifted "
            "baseline.\n  " + "\n  ".join(mismatches[:12])
        )

    cache_after = {
        p.name: _sha256(p) for p in sorted(campaign.HAZARD_CACHE.glob("*.csv"))
    }
    if cache_after != cache_before:
        raise AssertionError(
            "GATE 4 FAILED: the Phase 3 hazard cache changed. The hazard side "
            "streams every ensemble member and cannot depend on which one is "
            "canonical."
        )

    sections: dict[str, Any] = {}
    for kp in BEP_KPS:
        for scenario in campaign.SCENARIOS:
            key = ("Tokachi", kp, scenario)
            b, a = base_rows[key], arm_rows[key]
            sections[f"{_label(kp)} {scenario}"] = {
                "section": _label(kp),
                "scenario": scenario,
                "p_annual_system_production": float(b["p_annual_system"]),
                "p_annual_system_alternate": float(a["p_annual_system"]),
                "p_annual_bep_production": float(b["p_annual_bep"]),
                "p_annual_bep_alternate": float(a["p_annual_bep"]),
                "share_bep_production": float(b["share_bep"]),
                "share_bep_alternate": float(a["share_bep"]),
                "bep_leads_production": float(b["share_bep"]) > 0.5,
                "bep_leads_alternate": float(a["share_bep"]) > 0.5,
                "ordering_changes": (float(b["share_bep"]) > 0.5)
                != (float(a["share_bep"]) > 0.5),
            }

    ratios = {}
    for kp in BEP_KPS:
        hist = sections[f"{_label(kp)} historical"]
        warm = sections[f"{_label(kp)} +4K"]
        ratios[_label(kp)] = {
            "climate_ratio_production": (
                warm["p_annual_system_production"] / hist["p_annual_system_production"]
                if hist["p_annual_system_production"] > 0
                else None
            ),
            "climate_ratio_alternate": (
                warm["p_annual_system_alternate"] / hist["p_annual_system_alternate"]
                if hist["p_annual_system_alternate"] > 0
                else None
            ),
        }

    payload = {
        "note": (
            "The composition step is imported from the production campaign "
            "driver, so the baseline gate exercises the production code path. "
            "Nothing under results/system_integration/phase3/ is written."
        ),
        "surface_variant": surface_variant,
        "surface_scope": (
            "both mechanisms re-conditioned on the alternate member, so the "
            "dominance share compares like with like"
            if surface_variant == "alternate"
            else "PIPING SIDE ONLY: the surface curves stay on the production "
            "member, so every dominance number here is scoped to the piping "
            "side and the share is not a like-for-like comparison"
        ),
        "gates": {
            "baseline_reproduces_published_annual_table": True,
            "n_published_rows_checked": checked,
            "gate_4_hazard_cache_unchanged": True,
        },
        "sections": sections,
        "climate_ratios": ratios,
    }
    _merge_evidence(out, "phase3", payload)
    for name, s in sections.items():
        print(
            f"  {name}: annual {s['p_annual_system_production']:.3e} -> "
            f"{s['p_annual_system_alternate']:.3e}; piping share "
            f"{s['share_bep_production']:.3f} -> {s['share_bep_alternate']:.3f}"
            + ("  ORDERING CHANGES" if s["ordering_changes"] else ""),
            flush=True,
        )
    return payload


# --------------------------------------------------------------------------- #
# Figure                                                                        #
# --------------------------------------------------------------------------- #
def render_figure(record: dict[str, Any]) -> Path:
    """Four panels: the two shapes, the curve response, the ladder, the factor.

    Rendered text carries no run identifier, no decision-record number, no
    module name and no em dash (``docs/conventions.md`` section 9.3.1): this
    figure is a main-body candidate.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figstyle.style()
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 8.4))
    ax_shape, ax_curve, ax_ladder, ax_factor = axes.ravel()

    # Panel A: the two normalised shapes, drawn as hours above a shape fraction,
    # which is the statistic the barrier responds to.
    shape = record.get("shape", {})
    members = shape.get("members", {})
    fracs = [0.25, 0.50, 0.75, 0.90, 0.95]
    width = 0.36
    for k, (event_id, colour) in enumerate(
        ((PRODUCTION_EVENT, figstyle.BLUE), (ALTERNATE_EVENT, figstyle.ORANGE))
    ):
        if event_id not in members:
            continue
        hours = [members[event_id]["hours_above_shape"][f"{f:.2f}"] for f in fracs]
        ax_shape.bar(
            np.arange(len(fracs)) + (k - 0.5) * width,
            hours,
            width=width,
            color=colour,
            label=ARM_DISPLAY_NAMES[event_id],
        )
    ax_shape.set_xticks(np.arange(len(fracs)))
    ax_shape.set_xticklabels([f"{f:.2f}" for f in fracs])
    ax_shape.set_xlabel("stage shape fraction")
    ax_shape.set_ylabel("hours at or above")
    ax_shape.set_title("Where each event spends its time")
    ax_shape.legend()

    # Panel B: the transient curve response at the informative strata.
    phase1 = record.get("phase1", {}).get("strata", {})
    drawn = 0
    for stem, rec in phase1.items():
        if rec["kp"] not in (58.8, 60.0) or "matrix" not in stem:
            continue
        grid = np.asarray(rec["levels_m_msl"], dtype=float)
        colour = figstyle.SECTION_COLORS[rec["section"].replace(" ", "")]
        ax_curve.plot(
            grid,
            rec["p_f_trans_production"],
            color=colour,
            lw=1.8,
            label=f"{rec['section']}, {ARM_DISPLAY_NAMES[PRODUCTION_EVENT]}",
        )
        ax_curve.plot(
            grid,
            rec["p_f_trans_alternate"],
            color=colour,
            lw=1.8,
            ls="--",
            label=f"{rec['section']}, {ARM_DISPLAY_NAMES[ALTERNATE_EVENT]}",
        )
        drawn += 1
    ax_curve.set_yscale("log")
    ax_curve.set_xlabel("peak stage [m T.P.]")
    ax_curve.set_ylabel("transient failure probability")
    ax_curve.set_title("Conditional curves at the two informative sections")
    if drawn:
        ax_curve.legend(fontsize=8)

    # Panel C: the ladder. Component in probability units against its share, so
    # the two are visibly different quantities.
    ladder = record.get("ladder", {}).get("sections", {})
    names, comp_p, comp_a, share_p, share_a = [], [], [], [], []
    # Drawn at the lowest level where both arms carry enough failing rows for a
    # share to mean anything. At the design level one section's time component
    # is zero under BOTH events on zero rows, which would print as "exactly
    # equal" for a component that is in fact shape-exposed: the precise
    # conflation this figure exists to prevent.
    anchor_key = "lowest_adequately_sampled_level"
    for key, sec in ladder.items():
        steps = sec["components"]["engine"]["steps"]
        for step_name, step in steps.items():
            if anchor_key not in step["anchors"]:
                continue
            anchor = step["anchors"][anchor_key]
            names.append(
                f"{sec['section']} at {anchor['stage_m_msl']:.2f}\n"
                f"{STEP_DISPLAY_NAMES.get(step_name, step_name)}"
            )
            comp_p.append(anchor["component_production"])
            comp_a.append(anchor["component_alternate"])
            share_p.append(anchor["share_production"])
            share_a.append(anchor["share_alternate"])
    if names:
        x = np.arange(len(names))
        ax_ladder.bar(
            x - 0.2, share_p, 0.4, color=figstyle.BLUE, label="production event"
        )
        ax_ladder.bar(
            x + 0.2, share_a, 0.4, color=figstyle.ORANGE, label="single-peak event"
        )
        for xi, (cp, ca) in enumerate(zip(comp_p, comp_a)):
            ax_ladder.annotate(
                "exactly equal" if cp == ca else "moves",
                (xi, max(share_p[xi], share_a[xi])),
                textcoords="offset points",
                xytext=(0, 4),
                ha="center",
                fontsize=7.0,
                color=figstyle.INK_2,
            )
        ax_ladder.set_xticks(x)
        ax_ladder.set_xticklabels(names, fontsize=7.5)
        ax_ladder.set_ylabel("share of the total gap")
        ax_ladder.set_title(
            "Shares move where the components themselves do not\n"
            "annotation: the component in probability units, under both events"
        )
        ax_ladder.legend(fontsize=8)

    # Panel D: the peak-only factor, informative strata only.
    peak = record.get("peak_shortcut", {})
    rows = [
        s
        for s in peak.get("strata", [])
        if s["factor_alternate"] is not None and not s["small_number_regime"]
    ]
    if rows:
        x = np.arange(len(rows))
        ax_factor.bar(
            x - 0.2,
            [s["factor_production"] for s in rows],
            0.4,
            color=figstyle.BLUE,
            label="production event",
        )
        ax_factor.bar(
            x + 0.2,
            [s["factor_alternate"] for s in rows],
            0.4,
            color=figstyle.ORANGE,
            label="single-peak event",
        )
        ax_factor.axhline(1.0, color=figstyle.BASELINE, lw=1.0)
        ax_factor.set_xticks(x)
        # The committed slice spells a section without its space; the thesis
        # spells it with one, through the same conversion every other panel uses.
        ax_factor.set_xticklabels(
            [
                figstyle.section_label(
                    f"tokachi_{s['section'].replace(' ', '').lower()}"
                )
                for s in rows
            ]
        )
        ax_factor.set_ylabel("peak-only over-rejection factor")
        ax_factor.set_title(
            "The peak-only shortcut, numerator exposed and denominator not"
        )
        ax_factor.legend(fontsize=8)

    fig.tight_layout()
    path = figstyle.save(fig, FIGURE_NAME, mirror=OUT_DIR / "figures")
    return path


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Canonical hydrograph shape sensitivity: swap the pinned d4PDF "
            "member in memory and measure the difference end to end."
        )
    )
    parser.add_argument(
        "stage",
        choices=(
            "shape",
            "phase1",
            "ladder",
            "peak-shortcut",
            "surface",
            "phase3",
            "figures",
            "all",
        ),
        help="Which stage to run.",
    )
    parser.add_argument("--n-jobs", type=int, default=4, help="joblib workers.")
    parser.add_argument(
        "--strata", nargs="+", default=[], help="Restrict the phase1 stage."
    )
    parser.add_argument(
        "--sections", nargs="+", default=[], help="Restrict the ladder stage."
    )
    parser.add_argument(
        "--surface",
        choices=("alternate", "production"),
        default="alternate",
        help=(
            "Which surface curves the phase3 composition uses. 'production' "
            "scopes every dominance number to the piping side."
        ),
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_EVIDENCE, help="Evidence JSON path."
    )
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Redraw the figure from the committed evidence and write nothing else.",
    )
    args = parser.parse_args(argv)

    out = args.out
    if args.figures_only or args.stage == "figures":
        if not out.is_file():
            raise SystemExit(f"no evidence record at {_rel(out)}; run a stage first.")
        path = render_figure(_read_json(out))
        print(f"wrote {_rel(path)}")
        return 0

    stages = (
        ["shape", "phase1", "ladder", "peak-shortcut", "surface", "phase3"]
        if args.stage == "all"
        else [args.stage]
    )
    for stage in stages:
        print(f"== {stage} ==", flush=True)
        if stage == "shape":
            stage_shape(out)
        elif stage == "phase1":
            stage_phase1(out, n_jobs=args.n_jobs, strata=args.strata)
        elif stage == "ladder":
            stage_ladder(out, n_jobs=args.n_jobs, sections=args.sections)
        elif stage == "peak-shortcut":
            stage_peak_shortcut(out)
        elif stage == "surface":
            stage_surface(out)
        elif stage == "phase3":
            stage_phase3(out, surface_variant=args.surface)
    if args.stage == "all":
        path = render_figure(_read_json(out))
        print(f"wrote {_rel(path)}")
    print(f"\nevidence: {_rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
