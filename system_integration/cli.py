"""Command-line entry point: ``python -m system_integration``.

Composes the multi-mechanism segment fragility and the annualized failure
probabilities for the BEP-covered segments (RQ3), per scenario (RQ4), from:

* BEP: Phase 2 posterior artifacts (default) or Phase 1 results,
* surface mechanisms: an Uemura CSV when supplied (``--surface-csv``), the
  schema-exact synthetic stub only under ``--allow-stub``, or nothing
  (BEP-only mode — absence stamped, never silent),
* hazard: the committed d4PDF band workbooks through the verbatim M3 chain.

Example (BEP-only, both scenarios, all four OYO sections)::

    python -m system_integration --results-dir results/phase2 \\
        --out results/system_integration

The output JSON per section/scenario carries the composed curve, the
mechanism decomposition, the annualized probabilities and every provenance
stamp (sources, workbooks, lambda_ac).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import sys
from pathlib import Path

import numpy as np

from bep_reliability_engine.fragility import upscale_length_effect
from system_integration.annualize import annualize
from system_integration.bep_input import load_bep_curve
from system_integration.composition import MechanismCurve, compose
from system_integration.hazard import load_node_hazard
from system_integration.segments import OYO_BEP_SECTIONS
from system_integration.surface_curves import (
    SurfaceCurveSet,
    load_surface_curves,
    synthetic_stub,
)

__all__ = ["main"]

logger = logging.getLogger(__name__)

# ADR-0037: primary lambda_ac (n_eff = 1 at the 200 m segment).
_DEFAULT_LAMBDA_AC_M = 250.0
_SEGMENT_LENGTH_M = 200.0
_SCENARIOS = ("historical", "+4K")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m system_integration",
        description=(
            "Phase 3 system integration (ADR-0038): series-system "
            "composition of BEP fragility with the Uemura surface curves, "
            "annualized against the d4PDF stage-frequency per scenario."
        ),
    )
    parser.add_argument(
        "--results-dir",
        default="results/phase2",
        help="Directory of BEP artifacts: Phase 2 *_posterior.h5 (default) "
        "or Phase 1 result files (default: results/phase2).",
    )
    parser.add_argument(
        "--bep-source",
        choices=["posterior", "prior"],
        default="posterior",
        help="BEP curve source (ADR-0038 decision 4; default posterior).",
    )
    parser.add_argument(
        "--d70",
        choices=["matrix", "bulk"],
        default="matrix",
        help="Which co-primary d70 interpretation's artifacts to compose "
        "(default matrix).",
    )
    parser.add_argument(
        "--surface-csv",
        default=None,
        help="Uemura surface-curve CSV (the ADR-0038 decision 5 contract). "
        "Absent -> BEP-only composition.",
    )
    parser.add_argument(
        "--allow-stub",
        action="store_true",
        help="Compose the synthetic surface stub (testing/plumbing only; "
        "results are stamped synthetic_stub).",
    )
    parser.add_argument(
        "--data-root",
        default="data/raw",
        help="Raw data root (band workbooks, rating curves; default data/raw).",
    )
    parser.add_argument(
        "--lambda-ac",
        type=float,
        default=_DEFAULT_LAMBDA_AC_M,
        help=f"ADR-0037 autocorrelation length [m] (default "
        f"{_DEFAULT_LAMBDA_AC_M:g}; primary value, n_eff = 1).",
    )
    parser.add_argument(
        "--out",
        default="results/system_integration",
        help="Output directory (default: results/system_integration).",
    )
    parser.add_argument(
        "--skip-hazard",
        action="store_true",
        help="Skip the d4PDF workbook streaming (composition-only run; "
        "no annualized numbers).",
    )
    return parser


def _bep_artifact(results_dir: Path, kp: float, d70: str, source: str) -> Path:
    """Locate the section's BEP artifact under the campaign naming scheme."""
    stem = f"tokachi_kp{kp:.1f}_historical_{d70}"
    name = f"{stem}_posterior.h5" if source == "posterior" else f"{stem}.h5"
    path = results_dir / name
    if not path.exists():
        raise FileNotFoundError(
            f"BEP artifact {name} not found under {results_dir} — run the "
            "Phase 1 sweep / Phase 2 update first (phase2_report.md section 9)."
        )
    return path


def main(argv: list[str] | None = None) -> int:
    """Run the composition for every OYO BEP section and scenario."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _build_parser().parse_args(argv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_dir = Path(args.results_dir)

    surface: SurfaceCurveSet | None = None
    if args.surface_csv is not None:
        surface = load_surface_curves(args.surface_csv)
    elif args.allow_stub:
        surface = synthetic_stub()
        logger.warning(
            "Composing the SYNTHETIC surface stub (--allow-stub); every "
            "output is stamped synthetic_stub."
        )

    n_eff = max(1.0, _SEGMENT_LENGTH_M / args.lambda_ac)
    written: list[str] = []
    for river, bank, kp in OYO_BEP_SECTIONS:
        bep_path = _bep_artifact(results_dir, kp, args.d70, args.bep_source)
        bep = load_bep_curve(bep_path, branch="transient")
        grid = bep.grid_m_msl
        bep_p_cs, clamped = bep.evaluate(grid)
        bep_p_seg = np.asarray(upscale_length_effect(bep_p_cs, n_eff))

        for scenario in _SCENARIOS:
            curves = [MechanismCurve(mechanism="bep", p_f=bep_p_seg, source=bep.source)]
            if surface is not None:
                for mechanism in ("overflow", "fluvial_scour"):
                    curve = surface.lookup(
                        river=river, kp=kp, mechanism=mechanism, scenario=scenario
                    )
                    if curve is None:
                        logger.warning(
                            "%s KP %.1f %s/%s: no surface curve in the set; "
                            "composing without it.",
                            river,
                            kp,
                            mechanism,
                            scenario,
                        )
                        continue
                    curves.append(
                        MechanismCurve(
                            mechanism=mechanism,
                            p_f=curve.evaluate(grid),
                            source=surface.source,
                        )
                    )
            system = compose(grid, curves)

            payload: dict[str, object] = {
                "generated": _dt.datetime.now().isoformat(timespec="seconds"),
                "adr": "ADR-0038",
                "river": river,
                "bank": bank,
                "kp": kp,
                "scenario": scenario,
                "bep_artifact": bep_path.name,
                "bep_source": bep.source,
                "bep_branch": bep.branch,
                "lambda_ac_m": args.lambda_ac,
                "n_eff": n_eff,
                "mechanisms": list(system.mechanisms),
                "sources": system.sources,
                "stage_m_msl": grid.tolist(),
                "p_sys": system.p_sys.tolist(),
                "per_mechanism": {
                    k: v.tolist() for k, v in system.per_mechanism.items()
                },
                "bep_clamped_above_grid": bool(np.any(clamped)),
            }

            if not args.skip_hazard:
                hazard = load_node_hazard(
                    args.data_root,
                    river=river,
                    kp=kp,
                    scenario=scenario,
                    # Section toe (the fragility fit datum) as the exposure
                    # reference, so the RQ4 above-toe stratifiers are live.
                    datum_m_msl=bep.datum_m,
                    cache_csv=out_dir / f"hazard_{river.lower()}_kp{kp:.1f}_"
                    f"{scenario.replace('+', 'plus')}.csv",
                )
                annual = annualize(system, hazard)
                payload["annualized"] = {
                    "n_years": annual.n_years,
                    "p_f_annual_system": annual.p_f_annual_system,
                    "p_f_annual_per_mechanism": annual.p_f_annual_per_mechanism,
                    "hazard_provenance": hazard.provenance,
                }

            scenario_token = scenario.replace("+", "plus")
            out_path = (
                out_dir / f"system_{river.lower()}_kp{kp:.1f}_{scenario_token}_"
                f"{args.d70}.json"
            )
            out_path.write_text(json.dumps(payload, indent=2))
            written.append(out_path.name)
            logger.info("Wrote %s", out_path)

    logger.info("Done: %d composition files under %s.", len(written), out_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via __main__
    sys.exit(main())
