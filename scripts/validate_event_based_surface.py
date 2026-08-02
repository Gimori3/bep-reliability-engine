"""Event-based validation of the ADR-0042 surface curves (companion run).

Runs Uemura's overflow and scour models over EVERY d4PDF ensemble event
(both scenarios) at the 9 section-representative nodes — the ADR-0042
alternative-2 construction — and compares the resulting annual failure
probabilities against (a) the curve-based annualization (canonical-shape
conditioning) and (b) the WP2 final-report Tables 3/4 magnitudes (their
hydrology differs: WFLOW/RRI runs with system behaviour; order-of-magnitude
agreement is the bar).

Scour uses the dimensionally-correct USACE k conversion — the ADR-0042
amendment (2026-07-21) primary — so this run validates the same scour
physics the primary curves carry (under which scour is negligible; the WP2
Table 3 erosion magnitudes reflect the as-received script conversion and
are not expected to be reproduced — see the report §7 and ADR-0042 dec. 9).

Output: ``results/system_integration/phase3/event_based_validation.json``.
Runtime ~5-10 min (4 workbook reads + pruned per-event MC, N_MC = 1,000).
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
    load_rating_coefficients,
    rating_curve_path,
    read_discharge_ensemble,
    resolve_band_workbook,
)
from system_integration.uemura_models import (  # noqa: E402
    SCOUR_BED_ROUGHNESS_KB_M,
    SCOUR_K_CONVERSION_USACE,
    SCOUR_MANNING_N,
    SCOUR_MIN_DEPTH_M,
    draw_overflow,
    draw_scour,
    load_segment_inputs,
    overflow_failure_fraction,
    scour_failure_fraction,
)

DATA_ROOT = REPO / "data/raw"
SEGMENT_INPUTS = REPO / "data/processed/uemura_segments/segment_inputs.csv"
OUT = REPO / "results/system_integration/phase3/event_based_validation.json"

N_MC = 1_000
SEED_ROOT = 20260718

REP_NODES = [
    ("Tokachi", 62.4),
    ("Tokachi", 61.4),
    ("Tokachi", 59.6),
    ("Tokachi", 58.0),
    ("Tokachi", 56.4),
    ("Satsunai", 7.0),
    ("Satsunai", 6.4),
    ("Satsunai", 5.2),
    ("Satsunai", 4.2),
]

# WP2 final report Table 3 (annual breach probability per location; their
# WFLOW/RRI hydrology + both mechanisms + system behaviour) — reference
# magnitudes only, not a numerical target.
WP2_TABLE3 = {
    ("Satsunai", 7.0): (0.002550, 0.009009),
    ("Satsunai", 6.4): (0.000433, 0.002213),
    ("Satsunai", 5.2): (0.000017, 0.002213),
    ("Satsunai", 4.2): (0.000783, 0.005389),
    ("Tokachi", 62.4): (0.000783, 0.000602),
    ("Tokachi", 61.4): (0.000017, 0.001546),
    ("Tokachi", 59.6): (0.000383, 0.002926),
    ("Tokachi", 58.0): (0.000333, 0.002009),
    ("Tokachi", 56.4): (0.000450, 0.005241),
}

SCENARIOS = ("historical", "+4K")


def _scour_upper_bound_fails(h, dt_s, seg, k_max, tau_c_min) -> bool:
    """Deterministic can-it-possibly-fail bound (prunes the event MC)."""
    if float(np.max(h)) <= seg.ground_m_msl:
        return False
    z_crest = seg.crest_design_m_msl
    depth = np.clip(h - seg.floodplain_m_msl, 0.0, z_crest - seg.floodplain_m_msl)
    v = (1.0 / SCOUR_MANNING_N) * depth ** (2.0 / 3.0) * seg.water_surface_slope**0.5
    with np.errstate(divide="ignore"):
        log_term = np.log(30.0 * depth / SCOUR_BED_ROUGHNESS_KB_M)
    f_c = np.where(depth > 0.0, 2.0 * (2.5 * log_term) ** (-2.0), 0.0)
    tau = 0.5 * 1000.0 * f_c * v**2
    excess = np.maximum(0.0, tau - tau_c_min)
    excess[h < seg.floodplain_m_msl + SCOUR_MIN_DEPTH_M] = 0.0
    erosion_ub = float(np.sum(k_max * excess) * dt_s / 3600.0)
    width = np.where(
        h > z_crest,
        seg.crest_width_m,
        seg.crest_width_m + (z_crest - h) * seg.slope_h_per_v,
    )
    loaded = h > seg.ground_m_msl
    return erosion_ub > float(np.min(width[loaded]))


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    t0 = time.time()
    inputs = load_segment_inputs(SEGMENT_INPUTS)
    results: dict[str, dict] = {}

    for scenario in SCENARIOS:
        bands: dict[Path, tuple[np.ndarray, dict]] = {}
        for river, kp in REP_NODES:
            wb = resolve_band_workbook(DATA_ROOT, river=river, kp=kp, scenario=scenario)
            if wb not in bands:
                print(f"reading {wb.name} ...", flush=True)
                bands[wb] = read_discharge_ensemble(wb)

        for node_index, (river, kp) in enumerate(REP_NODES):
            seg = inputs[(river, round(kp, 3))]
            coeffs = load_rating_coefficients(rating_curve_path(DATA_ROOT, river))
            a_kp, b_kp = coeffs[kp]
            wb = resolve_band_workbook(DATA_ROOT, river=river, kp=kp, scenario=scenario)
            time_hours, members = bands[wb]
            dt_s = 3600.0 * float(np.median(np.diff(time_hours)))

            rng_of = np.random.default_rng(
                np.random.SeedSequence((SEED_ROOT, node_index, 0))
            )
            rng_sc = np.random.default_rng(
                np.random.SeedSequence((SEED_ROOT, node_index, 1))
            )
            of_draws = draw_overflow(rng_of, seg, N_MC)
            # Primary scour physics = USACE-corrected conversion (ADR-0042
            # amendment 2026-07-21).
            sc_draws = draw_scour(rng_sc, N_MC, k_conversion=SCOUR_K_CONVERSION_USACE)
            of_gate = float(np.min(of_draws.crest_m_msl) - np.max(of_draws.wl_err_m))
            k_max = float(np.max(sc_draws.k_si_per_hr_pa))
            tau_c_min = float(np.min(sc_draws.tau_c_pa))

            p_of_events, p_sc_events = [], []
            n_of_active = n_sc_active = 0
            for q in members.values():
                with np.errstate(invalid="ignore"):
                    h = np.sqrt(np.maximum(q, 0.0) / a_kp) - b_kp
                peak = float(np.max(h))
                if peak > of_gate:
                    p_of_events.append(
                        overflow_failure_fraction(h, dt_s, seg, of_draws)
                    )
                    n_of_active += 1
                else:
                    p_of_events.append(0.0)
                if _scour_upper_bound_fails(h, dt_s, seg, k_max, tau_c_min):
                    p_sc_events.append(scour_failure_fraction(h, dt_s, seg, sc_draws))
                    n_sc_active += 1
                else:
                    p_sc_events.append(0.0)

            p_of = np.asarray(p_of_events)
            p_sc = np.asarray(p_sc_events)
            p_sys = 1.0 - (1.0 - p_of) * (1.0 - p_sc)
            key = f"{river}_KP{kp:g}"
            results.setdefault(key, {})[scenario] = {
                "n_events": int(p_of.size),
                "n_overflow_active": n_of_active,
                "n_scour_active": n_sc_active,
                "p_annual_overflow_event_based": float(np.mean(p_of)),
                "p_annual_scour_event_based": float(np.mean(p_sc)),
                "p_annual_system_event_based": float(np.mean(p_sys)),
            }
            print(
                f"{scenario} {key}: of={np.mean(p_of):.2e} sc={np.mean(p_sc):.2e} "
                f"(active {n_of_active}/{n_sc_active}; {time.time() - t0:.0f}s)",
                flush=True,
            )

    for (river, kp), (present, future) in WP2_TABLE3.items():
        key = f"{river}_KP{kp:g}"
        results[key]["wp2_table3_reference"] = {
            "historical": present,
            "+4K": future,
            "note": "WFLOW/RRI hydrology + system behaviour; magnitudes only",
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated": _dt.datetime.now().isoformat(timespec="seconds"),
                "adr": "ADR-0042 (event-based companion)",
                "n_mc": N_MC,
                "seed_root": SEED_ROOT,
                "nodes": results,
                "runtime_s": round(time.time() - t0, 1),
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
