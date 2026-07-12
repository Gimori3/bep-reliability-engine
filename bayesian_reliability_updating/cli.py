"""Command-line entry point: ``python -m bayesian_reliability_updating``.

One documented command runs the whole Phase 2 update for one or more
Phase 1 result files (one PosteriorResult pair plus figures per input)::

    python -m bayesian_reliability_updating results/tokachi_kp58.8_*.h5

Against the future production sweep the full campaign is::

    python -m bayesian_reliability_updating results/*_historical_*.h5 \\
        --out results/phase2 --verify

Every option defaults to the documented baseline (trace-anchored 2016
record, no-breach criterion, breach-time tracing on, figures on).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from bayesian_reliability_updating.pipeline import (
    Phase2Settings,
    run_survival_update,
)

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bayesian_reliability_updating",
        description=(
            "Bayesian reliability updating (Phase 2): Accept-Reject filter "
            "the Phase 1 prior against observed survival of the 2016 "
            "typhoon event and regenerate posterior fragility curves."
        ),
    )
    parser.add_argument(
        "phase1",
        nargs="+",
        help="Phase 1 FragilityResult HDF5 file(s) (JSON sidecars next to them).",
    )
    parser.add_argument(
        "--out",
        default="results/phase2",
        help="Output directory for PosteriorResult pairs and figures "
        "(default: results/phase2).",
    )
    parser.add_argument(
        "--anchor",
        choices=["trace_right", "trace_left", "rating"],
        default="trace_right",
        help="Observed-record peak anchoring (ADR-0035; default trace_right, "
        "the study levees' bank).",
    )
    parser.add_argument(
        "--criterion",
        choices=["no_breach", "no_breach_no_initiation"],
        default="no_breach",
        help="Acceptance criterion (ADR-0036; default no_breach, the thesis "
        "baseline). no_breach_no_initiation additionally rejects rows whose "
        "uplift-plus-heave gate latched (documented caveats apply).",
    )
    parser.add_argument(
        "--data-root",
        default="data/raw",
        help="Raw data root holding rating_curves/ (default data/raw).",
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed/2016_event",
        help="Processed observed-event extracts (default "
        "data/processed/2016_event).",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Also verify the posterior fragility by exact re-evaluation of "
        "the accepted rows on the conditioning grid (slower).",
    )
    parser.add_argument(
        "--no-breach-times",
        action="store_true",
        help="Skip the per-row breach-time tracing of rejected realizations.",
    )
    parser.add_argument(
        "--no-figures", action="store_true", help="Skip figure rendering."
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Posterior bootstrap replicates (default 1000).",
    )
    parser.add_argument(
        "--backend",
        choices=["numpy", "numba"],
        default=None,
        help="M7 progression backend override for the replay (default: the "
        "Phase 1 config's own backend).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing PosteriorResult pairs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 2 update for every given Phase 1 file.

    Parameters
    ----------
    argv : list of str, optional
        Argument vector (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Process exit code (0 on full success, 1 if any input failed).
    """
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    args = _build_parser().parse_args(argv)
    settings = Phase2Settings(
        anchor=args.anchor,
        criterion=args.criterion,
        data_root=args.data_root,
        processed_dir=args.processed_dir,
        output_dir=args.out,
        verify_by_reevaluation=args.verify,
        trace_breach_times=not args.no_breach_times,
        figures=not args.no_figures,
        n_bootstrap=args.n_bootstrap,
        progression_backend=args.backend,
        overwrite=args.overwrite,
    )

    failures = 0
    for path in args.phase1:
        try:
            result = run_survival_update(Path(path), settings=settings)
        except Exception:  # noqa: BLE001 - CLI boundary, report and continue
            logging.getLogger(__name__).exception("FAILED: %s", path)
            failures += 1
            continue
        posterior = result.metadata["phase2"]["posterior"]
        print(
            f"{Path(path).name}: accepted {posterior['n_accepted']:,} of "
            f"{posterior['n_prior']:,} rows "
            f"(rejection {100.0 * posterior['rejection_fraction']:.2f}%)"
        )
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
