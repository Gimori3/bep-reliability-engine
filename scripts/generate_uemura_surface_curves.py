"""Generate the ADR-0038 contract surface-curve CSVs (ADR-0042).

Re-executes Uemura's overflow (P1) and fluvial-scour (P2) models per
0.2 km study-reach segment, conditioned per stage level on the production
canonical d4PDF event shape (``HPB_m064_1987``, the same G1 shape that
conditioned every Phase 1/2 BEP curve), with common random numbers across
levels (monotone by construction) and N_MC = 10,000 (his published count).

Outputs under ``data/processed/uemura_surface_curves/``:

* ``uemura_surface_curves_historical.csv`` / ``..._plus4K.csv`` — the
  primary contract CSVs (identical curve values per ADR-0042 decision 4;
  split per scenario for the repo's 500 KB hygiene guard),
* ``uemura_surface_curves_overflow_sine30h.csv`` — overflow companion under
  Uemura's published sine T=30 h shape (thesis Eq. 4.11 positive lobe),
* ``uemura_surface_curves_scour_script_k.csv``   — scour companion under
  Uemura's as-received script k conversion (ADR-0042 decision 9, **amended
  2026-07-21**: the primary set now carries the dimensionally-correct USACE
  stress-based conversion ``0.3048/47.8803``, under which fluvial scour is
  negligible at every node; the as-received script factor
  ``0.3048/0.45359237`` — ~105.6x larger — is retained here as a bounded
  sensitivity companion),
* ``uemura_surface_curves_overflow_no_rating_error.csv`` — overflow companion
  with the paper Eq. (10) stage-rating error suppressed, which is the
  composition-seam sensitivity: the primary curve's argument is the stage a
  rating relation would report, this one's is the realized stage at the levee
  (composition-seam study, 2026-08-21). Same node seed as the primary overflow
  draws, so the crest and turf-velocity draws are common random numbers and
  only the term under test differs,
* ``generation_metadata.json`` + ``provenance.md``.

Every output is validated through ``load_surface_curves`` (the loader IS the
contract) before being committed. Runtime ~5–10 min (3 workbook reads +
vectorized MC).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine.hydrographs import (  # noqa: E402
    build_hydrograph_record,
    load_rating_coefficients,
    normalize_stage_shape,
    parse_member_header,
    rating_curve_path,
    read_discharge_ensemble,
    resolve_band_workbook,
    resolve_discharge_source_kp,
)
from system_integration.surface_curves import load_surface_curves  # noqa: E402
from system_integration.uemura_models import (  # noqa: E402
    SCOUR_K_CONVERSION_SCRIPT,
    SCOUR_K_CONVERSION_USACE,
    draw_overflow,
    draw_scour,
    load_segment_inputs,
    overflow_failure_fraction,
    scour_failure_fraction,
)

DATA_ROOT = REPO / "data" / "raw"
SEGMENT_INPUTS = REPO / "data/processed/uemura_segments/segment_inputs.csv"
OUT_DIR = REPO / "data/processed/uemura_surface_curves"

CANONICAL_EVENT = "HPB_m064_1987"  # the ADR-0020 production shape
N_MC = 10_000  # Uemura's published MC count
LEVEL_STEP_M = 0.2
LEVEL_MARGIN_ABOVE_CREST_M = 3.0
SEED_ROOT = 20260717
SINE_PERIOD_H = 30.0  # thesis Eq. 4.11
SCENARIO_LABELS = ("historical", "plus4K")  # identical curves (ADR-0042 dec. 4)
# Per-(node, mechanism) seed salts. ADR-0042 amendment (2026-07-21): the
# USACE-corrected conversion is now the PRIMARY scour product and the
# as-received script conversion the labeled companion. The integer salts are
# unchanged from the pre-amendment generation, so the corrected primary curve
# is byte-identical to the previously committed ``scour_usace_k`` set (seed 3)
# and the script companion is byte-identical to the previously committed
# primary scour rows (seed 1): this flip re-labels validated numbers, it does
# not recompute them.
MECH_INDEX = {
    "overflow": 0,
    "fluvial_scour_script": 1,  # as-received companion (was the primary seed)
    "overflow_sine": 2,
    "fluvial_scour_usace": 3,  # dimensionally-correct primary (was companion)
}


def _canonical_discharges() -> dict[tuple[str, float], np.ndarray]:
    """Read each needed HPB band workbook once; return t_hours + Q per band."""
    bands: dict[Path, tuple[np.ndarray, np.ndarray]] = {}
    out: dict = {}
    inputs = load_segment_inputs(SEGMENT_INPUTS)
    for river, kp in inputs:
        workbook = resolve_band_workbook(
            DATA_ROOT, river=river, kp=kp, scenario="historical"
        )
        if workbook not in bands:
            print(f"reading {workbook.name} ...", flush=True)
            time_hours, members = read_discharge_ensemble(workbook)
            if CANONICAL_EVENT not in members:
                raise SystemExit(
                    f"canonical event {CANONICAL_EVENT} missing from "
                    f"{workbook.name} — cannot condition {river} KP {kp:g}."
                )
            bands[workbook] = (time_hours, members[CANONICAL_EVENT])
        out[(river, kp)] = bands[workbook]
    return out


def _sine_shape() -> tuple[np.ndarray, np.ndarray]:
    """Positive lobe of sin(2 pi t / T), hourly (thesis Eq. 4.11)."""
    t_hours = np.arange(0.0, SINE_PERIOD_H / 2.0 + 1.0)  # 0..15 h
    return t_hours, np.sin(2.0 * np.pi * t_hours / SINE_PERIOD_H)


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    t0 = time.time()
    inputs = load_segment_inputs(SEGMENT_INPUTS)
    discharges = _canonical_discharges()
    parse_member_header(CANONICAL_EVENT)  # validates the grammar

    rows_primary: list[tuple] = []
    rows_sine: list[tuple] = []
    rows_script: list[tuple] = []
    rows_no_rating: list[tuple] = []
    node_meta: dict[str, dict] = {}

    for node_index, ((river, kp), seg) in enumerate(sorted(inputs.items())):
        coeffs = load_rating_coefficients(rating_curve_path(DATA_ROOT, river))
        a_kp, b_kp = coeffs[kp]
        if river == "Tokachi":
            _, proxied = resolve_discharge_source_kp(kp)
        else:
            proxied = None
        time_hours, q = discharges[(river, kp)]
        record = build_hydrograph_record(
            time_hours,
            q,
            a_kp=a_kp,
            b_kp=b_kp,
            scenario="historical",
            event_id=CANONICAL_EVENT,
            provenance={"kp": kp},
        )
        shape, h_base, _ = normalize_stage_shape(record.h)
        dt_s = float(record.native_dt)

        crest_mean = seg.crest_design_m_msl + seg.crest_err_mu_m
        lo = np.floor(max(seg.floodplain_m_msl, h_base) / LEVEL_STEP_M) * LEVEL_STEP_M
        hi = crest_mean + LEVEL_MARGIN_ABOVE_CREST_M
        levels = np.round(np.arange(lo, hi + LEVEL_STEP_M / 2.0, LEVEL_STEP_M), 6)

        def scaled(level: float) -> np.ndarray:
            if level <= h_base:
                return np.full_like(shape, level)
            return h_base + (level - h_base) * shape

        rng_of = np.random.default_rng(
            np.random.SeedSequence((SEED_ROOT, node_index, MECH_INDEX["overflow"]))
        )
        of_draws = draw_overflow(rng_of, seg, N_MC)
        # Composition-seam companion: identical draw stream, rating-error term
        # zeroed. A FRESH generator on the SAME seed, so crest and u_c are the
        # very same draws as the primary arm and the only difference between
        # the two curve sets is the term under test.
        of_draws_no_rating = draw_overflow(
            np.random.default_rng(
                np.random.SeedSequence((SEED_ROOT, node_index, MECH_INDEX["overflow"]))
            ),
            seg,
            N_MC,
            include_rating_error=False,
        )
        # Primary scour uses the dimensionally-correct USACE stress-based
        # conversion (ADR-0042 amendment 2026-07-21); the as-received script
        # conversion is drawn alongside for the labeled sensitivity companion.
        # Seed salts are unchanged, so both curves are byte-identical to the
        # pre-amendment products with the primary<->companion roles swapped.
        sc_draws = draw_scour(
            np.random.default_rng(
                np.random.SeedSequence(
                    (SEED_ROOT, node_index, MECH_INDEX["fluvial_scour_usace"])
                )
            ),
            N_MC,
            k_conversion=SCOUR_K_CONVERSION_USACE,
        )
        sc_draws_script = draw_scour(
            np.random.default_rng(
                np.random.SeedSequence(
                    (SEED_ROOT, node_index, MECH_INDEX["fluvial_scour_script"])
                )
            ),
            N_MC,
            k_conversion=SCOUR_K_CONVERSION_SCRIPT,
        )

        # Cheap exact-zero guards (common draws make these provable zeros).
        of_zero_below = float(np.min(of_draws.crest_m_msl) - np.max(of_draws.wl_err_m))
        of_zero_below_no_rating = float(np.min(of_draws_no_rating.crest_m_msl))

        p_of, p_sc, p_sc_script, p_of_no_rating = [], [], [], []
        for level in levels:
            h = scaled(float(level))
            if float(np.max(h)) <= of_zero_below:
                p_of.append(0.0)
            else:
                p_of.append(overflow_failure_fraction(h, dt_s, seg, of_draws))
            if float(np.max(h)) <= of_zero_below_no_rating:
                p_of_no_rating.append(0.0)
            else:
                p_of_no_rating.append(
                    overflow_failure_fraction(h, dt_s, seg, of_draws_no_rating)
                )
            if level <= seg.floodplain_m_msl or crest_mean_never_loads(seg, h):
                p_sc.append(0.0)
                p_sc_script.append(0.0)
            else:
                # p_sc = primary (USACE-corrected); p_sc_script = companion.
                p_sc.append(scour_failure_fraction(h, dt_s, seg, sc_draws))
                p_sc_script.append(
                    scour_failure_fraction(h, dt_s, seg, sc_draws_script)
                )

        if p_of[0] != 0.0 or p_sc[0] != 0.0:
            raise SystemExit(
                f"{river} KP {kp:g}: lowest level not a zero anchor "
                f"(overflow {p_of[0]}, scour {p_sc[0]}) — extend the grid down."
            )

        # Sine-30h overflow companion (paper construction, same draws).
        t_sine, lobe = _sine_shape()
        p_of_sine = []
        for level in levels:
            h_sine = float(level) * lobe  # his Eq. 4.11 scales stage directly
            if float(np.max(h_sine)) <= of_zero_below:
                p_of_sine.append(0.0)
            else:
                p_of_sine.append(
                    overflow_failure_fraction(h_sine, 3600.0, seg, of_draws)
                )

        for scen in SCENARIO_LABELS:
            for level, p1, p2 in zip(levels, p_of, p_sc):
                rows_primary.append((river, seg.bank, kp, "overflow", scen, level, p1))
                rows_primary.append(
                    (river, seg.bank, kp, "fluvial_scour", scen, level, p2)
                )
            for level, p in zip(levels, p_of_sine):
                rows_sine.append((river, seg.bank, kp, "overflow", scen, level, p))
            for level, p in zip(levels, p_sc_script):
                rows_script.append(
                    (river, seg.bank, kp, "fluvial_scour", scen, level, p)
                )
            for level, p in zip(levels, p_of_no_rating):
                rows_no_rating.append((river, seg.bank, kp, "overflow", scen, level, p))

        node_meta[f"{river}_KP{kp:g}"] = {
            "h_base_m_msl": h_base,
            "n_levels": int(levels.size),
            "level_range_m_msl": [float(levels[0]), float(levels[-1])],
            "max_p_overflow": max(p_of),
            "max_p_scour": max(p_sc),  # USACE-corrected primary
            "max_p_scour_script_k": max(p_sc_script),  # as-received companion
            "max_p_overflow_no_rating_error": max(p_of_no_rating),
            "discharge_proxied_from": proxied,
        }
        if node_index % 10 == 0:
            print(
                f"[{node_index + 1}/{len(inputs)}] {river} KP {kp:g}: "
                f"P_of(max)={max(p_of):.3f} P_sc(max)={max(p_sc):.3f} "
                f"({time.time() - t0:.0f}s)",
                flush=True,
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = "river,bank,kp,mechanism,scenario,stage_m_msl,p_f\n"
    # The primary set is split per scenario label so each committed file
    # stays under the repo's 500 KB hygiene guard; each file is a fully
    # valid ADR-0038 contract CSV on its own (the campaign merges them).
    for name, rows in (
        (
            "uemura_surface_curves_historical.csv",
            [r for r in rows_primary if r[4] == "historical"],
        ),
        (
            "uemura_surface_curves_plus4K.csv",
            [r for r in rows_primary if r[4] == "plus4K"],
        ),
        ("uemura_surface_curves_overflow_sine30h.csv", rows_sine),
        ("uemura_surface_curves_scour_script_k.csv", rows_script),
        ("uemura_surface_curves_overflow_no_rating_error.csv", rows_no_rating),
    ):
        path = OUT_DIR / name
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(header)
            for river, bank, kp, mech, scen, level, p in rows:
                handle.write(
                    f"{river},{bank},{kp:g},{mech},{scen},{level:.6g},{p:.6g}\n"
                )
        curves = load_surface_curves(path)  # the loader is the contract
        print(f"wrote {path.name}: {len(rows)} rows, {len(curves.curves)} curves OK")

    metadata = {
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "adr": "ADR-0042",
        "canonical_event": CANONICAL_EVENT,
        "n_mc": N_MC,
        "seed_root": SEED_ROOT,
        "level_step_m": LEVEL_STEP_M,
        "scenario_labels_identical_curves": True,
        "scour_k_conversion_primary": "usace (0.3048/47.8803)",
        "scour_k_conversion_companion": "script (0.3048/0.45359237)",
        "overflow_no_rating_error_companion": (
            "paper Eq. (10) stage-rating error zeroed; same node seed as the "
            "primary overflow draws (crest and u_c are common random numbers)"
        ),
        "nodes": node_meta,
        "runtime_s": round(time.time() - t0, 1),
    }
    (OUT_DIR / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    _write_provenance()
    print(f"done in {time.time() - t0:.0f}s")


def crest_mean_never_loads(seg, h: np.ndarray) -> bool:
    """True when the series never reaches the landside ground (his -999 mask
    then forbids declaring failure at every time step)."""
    return float(np.max(h)) <= seg.ground_m_msl


def _write_provenance() -> None:
    text = """# Provenance: data/processed/uemura_surface_curves/

Generated by `scripts/generate_uemura_surface_curves.py` (ADR-0042) from
`data/processed/uemura_segments/segment_inputs.csv` (see its provenance.md)
and the committed d4PDF HPB band workbooks via the verbatim M3 chain.

* Models: `system_integration/uemura_models.py` — faithful reproductions of
  Uemura's overflow (Dean cumulative-work, paper Eqs. 1-5) and fluvial-scour
  (USACE excess-shear, ErosionModel_231019.py) failure-judgment models;
  equivalence to his reference implementations is pinned by
  `tests/test_uemura_models.py`.
* Conditioning: canonical event HPB_m064_1987 scaled per level by the G1
  rule (ADR-0020) at each node's own rating; common random numbers across
  levels (curves exactly monotone); N_MC = 10,000.
* `uemura_surface_curves_historical.csv` + `uemura_surface_curves_plus4K.csv`
  — PRIMARY (contract format, ADR-0038 dec. 5), split per scenario label to
  respect the repo's 500 KB hygiene guard; the two files carry identical
  curve values (ADR-0042 dec. 4) and each validates independently.
* `uemura_surface_curves_overflow_sine30h.csv` — overflow companion under
  the published sine T=30 h construction (thesis Eq. 4.11).
* `uemura_surface_curves_scour_script_k.csv` — scour companion under
  Uemura's as-received script k conversion (ADR-0042 decision 9, amended
  2026-07-21). The PRIMARY set now carries the dimensionally-correct USACE
  stress-based conversion (0.3048/47.8803), under which fluvial scour is
  negligible at every node; this companion carries the as-received script
  factor (0.3048/0.45359237, ~105.6x larger) as a bounded sensitivity.
* `uemura_surface_curves_overflow_no_rating_error.csv` — overflow companion
  with the paper Eq. (10) stage-rating error suppressed
  (`draw_overflow(..., include_rating_error=False)`), the composition-seam
  sensitivity of the 2026-08-21 study. The primary curve's argument is the
  stage a rating relation would report; this one's is the realized stage at
  the levee, which is what the piping branch's argument already is. Drawn on
  the SAME node seed as the primary overflow set, so the crest and turf
  critical-velocity draws are identical and only the term under test moves.

Raw drop files were read-only inputs. Regeneration:
`python scripts/generate_uemura_surface_curves.py`.
"""
    (OUT_DIR / "provenance.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
