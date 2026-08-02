"""ADR-0044 evidence: the sustained-peak upper bound for the 2011 event.

Quantifies, at production N = 1e5 across all eight strata, the MOST any
2011 hydrograph could reject: the surveyed H23.9 trace peak at each study
section is held constant for 64 days (the ADR-0040 sustained-peak
convention, where the ODE provably reaches its analytic limit) and
replayed through the frozen M8 evaluator via the Phase 2 machinery. Since
the real 2011 event was weaker than this hold at every instant, the
resulting rejection fraction is a rigorous upper bound on the rejection
any faithful 2011 time series could produce, and the overlap with the
production 2016 acceptance masks bounds the MARGINAL information 2011
could add beyond 2016.

The 2006 event has no computable bound (no stage record and no trace
survey exist in its drop); it is closed for lack of any constructible
observation, not by this bound.

Run from the repository root (needs the production results in
``results/`` and ``results/phase2/``)::

    python scripts/assess_2011_2006_closure.py
    python scripts/assess_2011_2006_closure.py --strata tokachi_kp58.8_historical_matrix

Writes ``docs/decisions/adr0044-event-closure-bound.json`` and prints the
summary table quoted by ADR-0044 and the Phase 2 report section 12. A
``--strata`` subset merges into the existing record rather than truncating
it, so a partial re-run cannot silently drop the other strata.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import time
from pathlib import Path

import h5py
import numpy as np

from bayesian_reliability_updating.filtering import apply_survival_filter
from bayesian_reliability_updating.replay import load_phase1_run, replay_event
from bep_reliability_engine.hydrographs import HydrographRecord

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_CSV = REPO_ROOT / "data" / "processed" / "2011_event" / "flood_trace_2011.csv"
OUT_JSON = REPO_ROOT / "docs" / "decisions" / "adr0044-event-closure-bound.json"

# One Phase 1 production file per stratum, with its production 2016 posterior.
STRATA: list[str] = [
    "tokachi_kp57.4_historical_matrix",
    "tokachi_kp57.4_historical_bulk",
    "tokachi_kp58.8_historical_matrix",
    "tokachi_kp58.8_historical_bulk",
    "tokachi_kp60.0_historical_matrix",
    "tokachi_kp60.0_historical_bulk",
    "tokachi_kp62.0_historical_matrix",
    "tokachi_kp62.0_historical_bulk",
]

# ADR-0040 sustained-peak convention: at a 64 day hold the forward-Euler
# trajectory has provably reached the analytic sustained-peak limit (zero
# disagreements measured there), so longer holds change nothing.
HOLD_DAYS: float = 64.0
NATIVE_DT_S: float = 3600.0


def _trace_right(kp: float) -> float:
    with open(TRACE_CSV, encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["river"] == "Tokachi" and float(row["kp"]) == round(kp, 2):
                value = row["trace_right_m_msl"]
                if value == "":
                    raise ValueError(f"no right-bank 2011 trace at KP {kp}")
                return float(value)
    raise ValueError(f"KP {kp} not in {TRACE_CSV.name}")


def _sustained_record(level_m: float, kp: float) -> HydrographRecord:
    n = int(round(HOLD_DAYS * 24.0)) + 1
    t = np.arange(n, dtype=np.float64)
    h = np.full(n, float(level_m), dtype=np.float64)
    return HydrographRecord(
        t=t * NATIVE_DT_S,
        h=h,
        peak=float(level_m),
        duration_hours=float(n - 1),
        scenario="historical",
        event_id=f"sustained_2011_trace_kp{kp:g}",
        native_dt=NATIVE_DT_S,
        provenance={
            "construction": "adr0044_sustained_peak_bound",
            "trace_right_m_msl_2011": float(level_m),
            "hold_days": HOLD_DAYS,
        },
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--strata",
        nargs="+",
        default=list(STRATA),
        choices=list(STRATA),
        help="Strata to bound (default: all eight production strata).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUT_JSON,
        help="Evidence JSON output path (default: the tracked ADR-0044 record).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    # The replay's end-above-toe warning is expected by construction here (a
    # sustained hold never recedes); silence that one logger for the run.
    logging.getLogger("bayesian_reliability_updating.replay").setLevel(logging.ERROR)

    records = []
    for stem in args.strata:
        phase1_path = REPO_ROOT / "results" / f"{stem}.h5"
        posterior_path = REPO_ROOT / "results" / "phase2" / f"{stem}_posterior.h5"
        run = load_phase1_run(phase1_path)
        kp = float(run.config.hydrograph_source.kp)
        z_toe = float(run.config.geometry.z_toe)
        level = _trace_right(kp)

        start = time.perf_counter()
        replay = replay_event(run, _sustained_record(level, kp))
        outcome = apply_survival_filter(replay)
        bound_reject = ~outcome.accept_trans

        with h5py.File(posterior_path) as handle:
            accept_2016 = handle["accept"][:].astype(bool)
        marginal_beyond_2016 = bound_reject & accept_2016

        entry = {
            "stratum": stem,
            "kp": kp,
            "z_toe_m_msl": z_toe,
            "trace_right_2011_m_msl": level,
            "head_above_toe_m": round(level - z_toe, 3),
            "n_prior": run.n_samples,
            "bound_reject_count": int(bound_reject.sum()),
            "bound_reject_fraction": float(bound_reject.mean()),
            "bound_static_reject_fraction": float((~outcome.accept_static).mean()),
            "bound_initiation_fraction": float(outcome.initiation_occurred.mean()),
            "reject_2016_count": int((~accept_2016).sum()),
            "marginal_beyond_2016_count": int(marginal_beyond_2016.sum()),
            "marginal_beyond_2016_fraction": float(marginal_beyond_2016.mean()),
            "runtime_seconds": round(time.perf_counter() - start, 1),
        }
        records.append(entry)
        print(
            f"{stem}: 2011 trace {level:.3f} m MSL "
            f"({entry['head_above_toe_m']:+.2f} m vs toe) -> sustained-peak "
            f"bound rejects {entry['bound_reject_count']}/{run.n_samples} "
            f"({100 * entry['bound_reject_fraction']:.3f}%), of which "
            f"{entry['marginal_beyond_2016_count']} beyond the 2016 rejection "
            f"({100 * entry['marginal_beyond_2016_fraction']:.4f}%)."
        )

    # Merge into any existing record so a ``--strata`` subset extends it rather
    # than truncating it to the strata just executed (the per-section
    # overwriting-writer defect found twice in the 2026-07-30 hardening sweep).
    merged = {entry["stratum"]: entry for entry in records}
    if args.out.exists():
        prior = json.loads(args.out.read_text(encoding="utf-8"))
        for entry in prior.get("strata", []):
            merged.setdefault(entry["stratum"], entry)
    ordered = [merged[stem] for stem in STRATA if stem in merged]

    payload = {
        "generated": "scripts/assess_2011_2006_closure.py",
        "date": "2026-07-18",
        "convention": (
            "surveyed H23.9 right-bank trace peak held for 64 days "
            "(ADR-0040 sustained-peak convention), replayed through M8 via "
            "the Phase 2 pipeline at the production N; upper bound on any "
            "faithful 2011 time series"
        ),
        "event_2006": (
            "no bound computable: the 2006 drop carries no stage record and "
            "no trace survey; closed for lack of any constructible "
            "observation"
        ),
        "strata": ordered,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
