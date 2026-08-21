"""Replay every ADR-0048 conductivity arm through the Phase 2 survival update.

Companion driver for `docs/decisions/conductivity-bracket-posterior-side.md`
(pre-registered 2026-08-21). It produces the arm posteriors that
``scripts/conductivity_annualisation_study.py --side posterior`` then annualises.

What it does
------------
For each (section, grain-size reading, arm) it calls the ordinary Phase 2
entry point on the persisted ADR-0048 companion sweep, with settings pinned to
the production campaign's own. Nothing about the update is re-implemented here:
this is a loop with a settings gate, which is the only way the arm posteriors
can be comparable to the production posteriors the thesis reports.

Why a driver rather than a shell loop: PowerShell does not glob-expand ``*.h5``
for external programs, the settings have to be gated against the production
sidecar rather than retyped, and a half-finished campaign has to be resumable
without silently re-running what is already on disk.

Settings, read from the production sidecar rather than restated
---------------------------------------------------------------
Anchor ``trace_right``, criterion ``no_breach``, ``--verify`` on (this is
pre-registered GATE 6: it proves an arm regenerates its OWN ADR-0048 shifted
population rather than the baseline one), breach-time tracing on, figures off,
``n_bootstrap`` 1000, ``z_toe_delta_m`` 0.0. A run whose settings do not match
production is refused by the study driver, not tabulated, so this driver
asserts them up front rather than letting the campaign discover it hours later.

Usage (repo root, venv active)::

    python scripts/conductivity_posterior_replay.py                  # all 32
    python scripts/conductivity_posterior_replay.py --d70 matrix     # 16
    python scripts/conductivity_posterior_replay.py --arms k_aq_regional_upper
    python scripts/conductivity_posterior_replay.py --dry-run        # cost only

Existing outputs are skipped unless ``--overwrite`` is given, so an interrupted
campaign resumes where it stopped.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bayesian_reliability_updating.pipeline import (  # noqa: E402
    Phase2Settings,
    run_survival_update,
)

ARM_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0048_prior_means"
OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "conductivity_posterior" / "phase2"
PHASE2_DIR = REPO_ROOT / "results" / "phase2"

BEP_KPS: tuple[float, ...] = (57.4, 58.8, 60.0, 62.0)
D70_CHOICES: tuple[str, ...] = ("matrix", "bulk")
ARMS: tuple[str, ...] = (
    "k_aq_field_geomean",
    "k_aq_field_toe",
    "k_aq_regional_upper",
    "gamma_bl_sub_lower",
)

#: Fields of the production settings that this driver legitimately overrides.
#: Everything else is asserted equal, because a posterior computed under a
#: different acceptance rule is not comparable to the production one.
#:
#: ``trace_breach_times`` is the one substantive exemption, and it is the
#: pre-registration's 2026-08-21 amendment. Tracing re-runs the scalar M8 with
#: trajectory storage once per REJECTED row, so its cost is linear in exactly
#: the quantity the upward conductivity arm inflates: measured at KP 58.8 matrix
#: under ``k_aq_regional_upper``, which rejects 65.5 % against the production
#: 5.7 %, it takes the replay from 69 s to over 69 minutes. Across 32 replays
#: that is the difference between one hour and well over a day.
#:
#: It is exempt because it cannot reach anything this study measures.
#: ``pipeline.run_survival_update`` computes ``state.alive`` in the Accept-Reject
#: chain BEFORE the tracing block, and the posterior fragility is
#: ``posterior_fragility_from_matrices(run, state.alive, ...)``. The traced array
#: ``t_breach`` is only persisted and only plotted, and figures are off here.
#: The structural argument is confirmed empirically: on the worst-case arm above,
#: every array the Phase 3 annualisation consumes is bit-identical with tracing
#: on and off. The arm posteriors therefore carry no breach-time diagnostic,
#: which is a loss of a diagnostic and not of a result.
_OVERRIDDEN = frozenset({"output_dir", "trace_breach_times"})


def _stem(kp: float, d70: str) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{d70}"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def production_settings(d70: str) -> dict:
    """The production campaign's Phase 2 settings, read from its own artifact."""
    sidecar = PHASE2_DIR / f"{_stem(57.4, d70)}_posterior.json"
    if not sidecar.is_file():
        raise FileNotFoundError(
            f"missing production Phase 2 sidecar {_rel(sidecar)}; there is "
            "nothing to pin the arm settings to."
        )
    return json.loads(sidecar.read_text(encoding="utf-8"))["phase2"]["settings"]


def build_settings(d70: str, *, trace_breach_times: bool = False) -> Phase2Settings:
    """Production settings, with only the documented exemptions changed."""
    reference = production_settings(d70)
    settings = Phase2Settings(
        anchor=reference["anchor"],
        criterion=reference["criterion"],
        data_root=reference["data_root"],
        processed_dir=reference["processed_dir"],
        output_dir=str(OUT_DIR),
        verify_by_reevaluation=reference["verify_by_reevaluation"],
        trace_breach_times=trace_breach_times,
        figures=reference["figures"],
        n_bootstrap=reference["n_bootstrap"],
        confidence=reference["confidence"],
        progression_backend=reference["progression_backend"],
        overwrite=False,
        z_toe_delta_m=reference["z_toe_delta_m"],
    )
    drift = sorted(
        field
        for field, value in reference.items()
        if field not in _OVERRIDDEN and getattr(settings, field, object()) != value
    )
    if drift:
        raise AssertionError(
            f"settings drift against the production campaign in {drift}; refusing "
            "to produce arm posteriors that are not comparable to the production "
            "ones."
        )
    return settings


def jobs(d70s: list[str], arms: list[str]) -> list[tuple[float, str, str, Path, Path]]:
    """Every (section, reading, arm) replay, with its input and output path."""
    out: list[tuple[float, str, str, Path, Path]] = []
    for d70 in d70s:
        for kp in BEP_KPS:
            for arm in arms:
                source = ARM_DIR / f"{_stem(kp, d70)}_{arm}.h5"
                target = OUT_DIR / f"{_stem(kp, d70)}_{arm}_posterior.h5"
                out.append((kp, d70, arm, source, target))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--d70",
        nargs="+",
        default=list(D70_CHOICES),
        choices=list(D70_CHOICES),
        help="Grain-size readings to replay (default: both, co-primary).",
    )
    parser.add_argument(
        "--arms",
        nargs="+",
        default=list(ARMS),
        choices=list(ARMS),
        help="Arms to replay (default: all four, the pre-registered set).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-run replays whose output already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the work and exit without replaying anything.",
    )
    parser.add_argument(
        "--trace-breach-times",
        action="store_true",
        help=(
            "Restore the production breach-time diagnostic. Off by default: it "
            "is linear in the rejected-row count, which the upward conductivity "
            "arm inflates 12-fold, and it cannot reach the posterior fragility "
            "(see _OVERRIDDEN). Turning it on costs about 60x."
        ),
    )
    args = parser.parse_args(argv)

    todo = jobs(list(args.d70), list(args.arms))
    missing = [_rel(src) for _, _, _, src, _ in todo if not src.is_file()]
    if missing:
        raise FileNotFoundError(
            "missing ADR-0048 companion sweeps: "
            + ", ".join(missing[:6])
            + ("" if len(missing) <= 6 else f" (+{len(missing) - 6} more)")
        )

    pending = [j for j in todo if args.overwrite or not j[4].is_file()]
    print(
        f"{len(todo)} replays in scope, {len(todo) - len(pending)} already on "
        f"disk, {len(pending)} to run"
    )
    if args.dry_run:
        for kp, d70, arm, source, _ in pending:
            print(f"  KP {kp:.1f} {d70:<6} {arm:<20} <- {_rel(source)}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    settings_by_reading = {
        d70: build_settings(d70, trace_breach_times=args.trace_breach_times)
        for d70 in args.d70
    }

    started = time.time()
    failures = 0
    for index, (kp, d70, arm, source, target) in enumerate(pending, start=1):
        settings = settings_by_reading[d70]
        if args.overwrite:
            settings = settings.model_copy(update={"overwrite": True})
        tick = time.time()
        print(
            f"[{index}/{len(pending)}] KP {kp:.1f} {d70} {arm} ...",
            flush=True,
        )
        try:
            result = run_survival_update(source, settings=settings)
        except Exception as exc:  # noqa: BLE001 - driver boundary, keep going
            print(f"    FAILED: {exc}", flush=True)
            failures += 1
            continue
        posterior = result.metadata["phase2"]["posterior"]
        elapsed = time.time() - tick
        print(
            f"    rejected {100.0 * posterior['rejection_fraction']:.3f}% "
            f"({posterior['n_prior'] - posterior['n_accepted']:,} of "
            f"{posterior['n_prior']:,}) in {elapsed:.0f} s -> {_rel(target)}",
            flush=True,
        )
    total = time.time() - started
    print(
        f"\n{len(pending) - failures} of {len(pending)} replays completed in "
        f"{total / 60.0:.1f} min"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
