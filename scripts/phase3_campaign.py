"""Phase 3 full RQ3+RQ4 campaign (ADR-0038/0042/0043).

Composes the three-mechanism segment fragility (BEP + Uemura overflow +
Uemura fluvial scour) for every study-reach segment, aggregates to Uemura's
9 sections, and annualizes both scenarios against the per-node d4PDF
stage-frequency. Variant axes:

* d70 interpretation: matrix (primary) / bulk (co-primary bound),
* BEP source: phase2 posterior (default) / phase1 prior (companion),
* lambda_ac: 250 m primary / 100 / 40 m ADR-0037 bracket (posterior only),
* surface variant: primary / scour_usace_k / overflow_sine30h
  (posterior-matrix only; ADR-0042 companions).

Outputs under ``results/system_integration/phase3/``:

* ``rq4_annual.csv``      — master annualized table (one row per segment x
  scenario x variant) with per-mechanism decomposition,
* ``rq3_segment_curves_{d70}_{bep}.json`` — composed conditional curves
  (lambda=250, primary surface; curves are scenario-invariant, ADR-0023),
* ``rq3_sections_{d70}_{bep}.json``       — section-level (max-within-
  section, ADR-0043) curves + annualized numbers,
* ``rq4_attribution.json`` — stratified RQ4 metrics (duration, compound,
  peak) at the BEP sections and the 9 Uemura sections,
* ``campaign_summary.json``.

Runtime: first run streams six band workbooks (~5 min) into
``results/system_integration/hazard_cache/``; afterwards seconds.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine.fragility import upscale_length_effect  # noqa: E402
from bep_reliability_engine.hydrographs import (  # noqa: E402
    load_rating_coefficients,
    rating_curve_path,
)
from system_integration.annualize import annualize, stratified_annual_p_f  # noqa: E402
from system_integration.bep_input import load_bep_curve  # noqa: E402
from system_integration.composition import (  # noqa: E402
    MechanismCurve,
    compose,
    max_within_section_rated,
)
from system_integration.hazard import load_reach_hazard  # noqa: E402
from system_integration.segments import build_registry, load_section_table  # noqa: E402
from system_integration.surface_curves import (  # noqa: E402
    SurfaceCurveSet,
    load_surface_curves,
)
from system_integration.uemura_models import load_segment_inputs  # noqa: E402

DATA_ROOT = REPO / "data/raw"
CURVE_DIR = REPO / "data/processed/uemura_surface_curves"
SECTION_TABLE = REPO / "data/processed/uemura_segments/section_table.csv"
SEGMENT_INPUTS = REPO / "data/processed/uemura_segments/segment_inputs.csv"
OUT_DIR = REPO / "results/system_integration/phase3"
HAZARD_CACHE = REPO / "results/system_integration/hazard_cache"

SCENARIOS = ("historical", "+4K")
# The primary contract set is committed as two per-scenario files (repo
# 500 KB hygiene guard; identical curve values, ADR-0042 decision 4).
PRIMARY_FILES = (
    CURVE_DIR / "uemura_surface_curves_historical.csv",
    CURVE_DIR / "uemura_surface_curves_plus4K.csv",
)
SURFACE_FILES = {
    "scour_usace_k": CURVE_DIR / "uemura_surface_curves_scour_usace_k.csv",
    "overflow_sine30h": CURVE_DIR / "uemura_surface_curves_overflow_sine30h.csv",
}
SEGMENT_LENGTH_M = 200.0

# The 9 Uemura sections in his upstream->downstream composition order
# (= thesis "Tokachi 1-5 / Satsunai 1-4" numbering, ADR-0043 decision 4).
SECTION_ORDER = [
    "KP62.4",
    "KP61.4",
    "KP59.6",
    "KP58.0",
    "KP56.4",
    "KP7.0",
    "KP6.4",
    "KP5.2",
    "KP4.2",
]


def _bep_path(kp: float, d70: str, source: str) -> Path:
    stem = f"tokachi_kp{kp:.1f}_historical_{d70}"
    if source == "posterior":
        return REPO / "results/phase2" / f"{stem}_posterior.h5"
    return REPO / "results" / f"{stem}.h5"


def _compose_segment(segment, surface, bep_curve, n_eff, scenario_label):
    """Composed SystemFragility for one segment (or None when no mechanism)."""
    grids = []
    curves = []
    clamped_any = False

    surf = {}
    for mechanism in ("overflow", "fluvial_scour"):
        curve = surface.lookup(
            river=segment.river,
            kp=segment.kp,
            mechanism=mechanism,
            scenario=scenario_label,
        )
        if curve is not None:
            surf[mechanism] = curve
            grids.append(curve.stage_m_msl)

    if bep_curve is not None:
        grids.append(bep_curve.grid_m_msl)
    if not grids:
        return None, False

    grid = np.unique(np.concatenate(grids))
    if bep_curve is not None:
        p_cs, clamped = bep_curve.evaluate(grid)
        clamped_any = bool(np.any(clamped & (grid <= grid[-1])))
        p_seg = np.asarray(upscale_length_effect(p_cs, n_eff))
        curves.append(
            MechanismCurve(mechanism="bep", p_f=p_seg, source=bep_curve.source)
        )
    for mechanism, curve in surf.items():
        curves.append(
            MechanismCurve(
                mechanism=mechanism, p_f=curve.evaluate(grid), source=surface.source
            )
        )
    return compose(grid, curves), clamped_any


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    registry = load_section_table(
        SECTION_TABLE, build_registry(DATA_ROOT), allow_gaps=True
    )
    seg_inputs = load_segment_inputs(SEGMENT_INPUTS)
    primary_parts = [load_surface_curves(path) for path in PRIMARY_FILES]
    raw_sets = {name: load_surface_curves(path) for name, path in SURFACE_FILES.items()}
    raw_sets["primary"] = SurfaceCurveSet(
        curves=tuple(c for part in primary_parts for c in part.curves),
        source="uemura_csv",
    )
    # The companion files carry only their varied mechanism; a variant run
    # composes the varied curves OVER the primary set (never drops the
    # other surface mechanism).
    surface_sets = {"primary": raw_sets["primary"]}
    for name, varied in (
        ("scour_usace_k", "fluvial_scour"),
        ("overflow_sine30h", "overflow"),
    ):
        kept = [c for c in raw_sets["primary"].curves if c.mechanism != varied]
        surface_sets[name] = SurfaceCurveSet(
            curves=tuple(kept) + raw_sets[name].curves,
            source=f"uemura_csv+{name}",
        )

    # --- BEP curves: (kp, d70, source) -> FragilityCurve --------------------
    bep_curves = {}
    for _river, _bank, kp in [(s.river, s.bank, s.kp) for s in registry.bep_segments()]:
        for d70 in ("matrix", "bulk"):
            for source in ("posterior", "prior"):
                bep_curves[(kp, d70, source)] = load_bep_curve(
                    _bep_path(kp, d70, source), branch="transient"
                )

    # --- Hazard: every node, both scenarios, one workbook read each ---------
    nodes = []
    for s in registry.segments:
        if s.bep_source_kp is not None:
            datum = bep_curves[(s.kp, "matrix", "posterior")].datum_m
        else:
            datum = seg_inputs[(s.river, round(s.kp, 3))].ground_m_msl
        nodes.append((s.river, s.kp, datum))
    hazards = {}
    for scenario in SCENARIOS:
        print(f"hazard: {scenario} ({time.time() - t0:.0f}s)", flush=True)
        hazards[scenario] = load_reach_hazard(
            DATA_ROOT, nodes=nodes, scenario=scenario, cache_dir=HAZARD_CACHE
        )

    # --- Variant matrix ------------------------------------------------------
    variants = []
    for d70 in ("matrix", "bulk"):
        for source in ("posterior", "prior"):
            variants.append((d70, source, 250.0, "primary"))
    for lam in (100.0, 40.0):
        for d70 in ("matrix", "bulk"):
            variants.append((d70, "posterior", lam, "primary"))
    variants.append(("matrix", "posterior", 250.0, "scour_usace_k"))
    variants.append(("matrix", "posterior", 250.0, "overflow_sine30h"))

    annual_rows = []
    curve_payloads = {}  # (d70, source) -> {segment payloads}
    section_payloads = {}
    attribution = {}

    for d70, source, lam, variant in variants:
        n_eff = max(1.0, SEGMENT_LENGTH_M / lam)
        surface = surface_sets[variant]
        store_curves = lam == 250.0 and variant == "primary"
        fragilities = {}  # (river, kp) -> SystemFragility (scenario-invariant)

        for segment in registry.segments:
            key = (segment.river, round(segment.kp, 3))
            bep = (
                bep_curves[(segment.kp, d70, source)]
                if segment.bep_source_kp is not None
                else None
            )
            frag, clamped = _compose_segment(segment, surface, bep, n_eff, "historical")
            if frag is None:
                continue
            fragilities[key] = frag

            for scenario in SCENARIOS:
                hazard = hazards[scenario][key]
                annual = annualize(frag, hazard)
                row = {
                    "river": segment.river,
                    "kp": segment.kp,
                    "section_id": segment.section_id or "",
                    "scenario": scenario,
                    "d70": d70,
                    "bep_source": source,
                    "lambda_ac_m": lam,
                    "surface_variant": variant,
                    "mechanisms": "|".join(frag.mechanisms),
                    "n_years": annual.n_years,
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
                annual_rows.append(row)

        if store_curves:
            payload = {}
            for (river, kp), frag in fragilities.items():
                payload[f"{river}_KP{kp:g}"] = {
                    "stage_m_msl": frag.stage_m_msl.tolist(),
                    "p_sys": frag.p_sys.tolist(),
                    "mechanisms": list(frag.mechanisms),
                    "per_mechanism": {
                        k: v.tolist() for k, v in frag.per_mechanism.items()
                    },
                    "sources": frag.sources,
                }
            curve_payloads[(d70, source)] = payload

            # Section-level aggregation (ADR-0043 decision 3): Uemura's
            # Eq. 14 max conditional on discharge, expressed on the
            # representative node's stage axis via each member's own
            # Eq. 4.19 rating (max_within_section_rated).
            sections = {}
            ratings = {
                river: load_rating_coefficients(rating_curve_path(DATA_ROOT, river))
                for river in ("Tokachi", "Satsunai")
            }
            for sid in SECTION_ORDER:
                rep_river = next(
                    s.river for s in registry.segments if s.section_id == sid
                )
                rep_kp = float(sid[2:])
                members = [
                    (
                        s.kp,
                        fragilities[(s.river, round(s.kp, 3))],
                        ratings[s.river][s.kp],
                    )
                    for s in registry.segments
                    if s.section_id == sid and (s.river, round(s.kp, 3)) in fragilities
                ]
                if not members:
                    continue
                grid = fragilities[(rep_river, round(rep_kp, 3))].stage_m_msl
                p_sys, argmax_kp = max_within_section_rated(
                    members, ratings[rep_river][rep_kp], grid
                )
                entry = {
                    "river": rep_river,
                    "representative_kp": rep_kp,
                    "member_kps": [kp for kp, _, _ in members],
                    "rule": "max_within_section_rated (discharge-aligned)",
                    "stage_m_msl": grid.tolist(),
                    "p_sys": p_sys.tolist(),
                    "argmax_kp": argmax_kp.tolist(),
                    "annual": {},
                }
                for scenario in SCENARIOS:
                    hazard = hazards[scenario][(rep_river, round(rep_kp, 3))]
                    peaks = hazard.peak_stages()
                    p_events = np.interp(peaks, grid, p_sys)
                    entry["annual"][scenario] = float(np.mean(p_events))
                sections[sid] = entry
            section_payloads[(d70, source)] = sections

        # RQ4 attribution at the BEP sections (primary posterior-matrix only).
        if d70 == "matrix" and source == "posterior" and store_curves:
            for segment in registry.bep_segments():
                key = (segment.river, round(segment.kp, 3))
                frag = fragilities[key]
                entry = {}
                for scenario in SCENARIOS:
                    hazard = hazards[scenario][key]
                    hours = np.asarray([e.hours_above_datum for e in hazard.events])
                    loaded = hours > 0.0
                    long_in, long_out, n_li, n_lo = stratified_annual_p_f(
                        frag, hazard, lambda e: e.hours_above_datum > 24.0
                    )
                    comp_in, comp_out, n_ci, n_co = stratified_annual_p_f(
                        frag, hazard, lambda e: e.n_peaks_above_datum >= 2
                    )
                    entry[scenario] = {
                        "n_years": hazard.n_years,
                        "frac_years_loading_toe": float(np.mean(loaded)),
                        "median_hours_above_toe_when_loaded": (
                            float(np.median(hours[loaded])) if loaded.any() else 0.0
                        ),
                        "frac_years_gt24h": float(np.mean(hours > 24.0)),
                        "p_f_long_loading": long_in,
                        "p_f_short_loading": long_out,
                        "n_long": n_li,
                        "p_f_compound": comp_in,
                        "p_f_noncompound": comp_out,
                        "n_compound": n_ci,
                    }
                attribution[f"{segment.river}_KP{segment.kp:g}"] = entry

    # --- Write outputs -------------------------------------------------------
    fields = list(annual_rows[0].keys())
    with open(OUT_DIR / "rq4_annual.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(fields) + "\n")
        for row in annual_rows:
            fh.write(",".join(str(row[f]) for f in fields) + "\n")

    for (d70, source), payload in curve_payloads.items():
        (OUT_DIR / f"rq3_segment_curves_{d70}_{source}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
    for (d70, source), payload in section_payloads.items():
        (OUT_DIR / f"rq3_sections_{d70}_{source}.json").write_text(
            json.dumps(payload, indent=1), encoding="utf-8"
        )
    (OUT_DIR / "rq4_attribution.json").write_text(
        json.dumps(attribution, indent=1), encoding="utf-8"
    )

    summary = {
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "adr": ["ADR-0038", "ADR-0042", "ADR-0043"],
        "n_segments": len(registry.segments),
        "n_segments_with_curves": len({(r["river"], r["kp"]) for r in annual_rows}),
        "n_annual_rows": len(annual_rows),
        "variants": [list(v) for v in variants],
        "surface_source": surface_sets["primary"].source,
        "runtime_s": round(time.time() - t0, 1),
    }
    (OUT_DIR / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
