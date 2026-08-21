"""Replay every ADR-0050 drained-bracket arm through the Phase 2 survival update.

Companion driver for `docs/decisions/adr0050-drained-configuration-bracket.md`.
It produces the arm posteriors that ``scripts/drained_bracket_annualisation.py``
then annualises, so the bracket reaches the annual numbers through the same
Accept-Reject update the production deliverable went through.

There is a second reason to run this beyond plumbing, and it is the more
interesting one. Chapters 6, 8 and 9 all record that the 2016 survival evidence
at these two strata is evaluated on the *undrained* foundation while the
survival itself was produced by a *drained* structure, and they state the
direction of that mismatch without a number. Replaying the drained arms is the
configuration in which the mismatch is absent, so the difference between the two
posteriors is exactly the quantity those chapters describe qualitatively.

Nothing about the update is re-implemented here: this is a loop with a settings
gate, which is the only way an arm posterior can be comparable to the production
posterior the thesis reports. Settings are read from the production sidecar
rather than retyped, and any drift is refused up front.

Why a driver rather than a shell loop: PowerShell does not glob-expand ``*.h5``
for external programs, and a half-finished campaign has to be resumable without
silently re-running what is already on disk.

Usage (repo root, venv active)::

    python scripts/drained_bracket_posterior_replay.py            # all 24
    python scripts/drained_bracket_posterior_replay.py --d70 matrix
    python scripts/drained_bracket_posterior_replay.py --arms berm_only
    python scripts/drained_bracket_posterior_replay.py --dry-run  # cost only

Existing outputs are skipped unless ``--overwrite`` is given.
"""

from __future__ import annotations

import argparse
import importlib.util
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

ARM_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0050_drained_bracket"
OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0050_drained_bracket" / "phase2"
PHASE2_DIR = REPO_ROOT / "results" / "phase2"

D70_CHOICES: tuple[str, ...] = ("matrix", "bulk")

#: Fields of the production settings this driver legitimately overrides.
#: ``trace_breach_times`` is exempt on the same structural ground the ADR-0048
#: replay driver records: ``pipeline.run_survival_update`` computes
#: ``state.alive`` before the tracing block, and the posterior fragility is a
#: function of ``state.alive`` alone, so the traced array is a persisted and
#: plotted diagnostic that cannot reach anything annualised here. Figures are
#: off. Every arm in this bracket is strictly *less* failure-prone than the
#: production baseline, so tracing would in any case be cheaper, not dearer;
#: it is off for comparability with the ADR-0048 arm posteriors, not for cost.
_OVERRIDDEN = frozenset({"output_dir", "trace_breach_times"})


def _load_bracket_module():
    """Import the ADR-0050 bracket driver for its section and arm definitions.

    The arm list is **read, never restated**: a second copy could drift from the
    one that produced the sweeps this driver consumes.
    """
    path = REPO_ROOT / "scripts" / "drained_configuration_bracket.py"
    spec = importlib.util.spec_from_file_location("drained_configuration_bracket", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_BRACKET = _load_bracket_module()
ARMS: tuple[str, ...] = tuple(label for label, _ in _BRACKET.arm_labels())
SECTION_KP: dict[str, float] = {"KP58.8": 58.8, "KP60.0": 60.0}


def _stem(kp: float, d70: str) -> str:
    return f"tokachi_kp{kp:.1f}_historical_{d70}"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def production_settings(d70: str) -> dict:
    """The production campaign's Phase 2 settings, read from its own artifact."""
    sidecar = PHASE2_DIR / f"{_stem(58.8, d70)}_posterior.json"
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


def jobs(
    d70s: list[str], arms: list[str], sections: list[str] | None = None
) -> list[tuple[float, str, str, Path, Path]]:
    """Every (section, reading, arm) replay, with its input and output path."""
    chosen = sorted(SECTION_KP[label] for label in (sections or sorted(SECTION_KP)))
    out: list[tuple[float, str, str, Path, Path]] = []
    for d70 in d70s:
        for kp in chosen:
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
        help="Arms to replay (default: every arm of the bracket).",
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        default=sorted(SECTION_KP),
        choices=sorted(SECTION_KP),
        help=(
            "Sections to replay (default: both). Narrowing the scope also "
            "narrows the missing-sweep check, so a partially complete bracket "
            "can be replayed section by section."
        ),
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--trace-breach-times",
        action="store_true",
        help="Restore the production breach-time diagnostic (see _OVERRIDDEN).",
    )
    args = parser.parse_args(argv)

    todo = jobs(list(args.d70), list(args.arms), list(args.sections))
    missing = [_rel(src) for _, _, _, src, _ in todo if not src.is_file()]
    if missing:
        raise FileNotFoundError(
            "missing ADR-0050 bracket sweeps: "
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
            print(f"  KP {kp:.1f} {d70:<6} {arm:<12} <- {_rel(source)}")
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
        print(f"[{index}/{len(pending)}] KP {kp:.1f} {d70} {arm} ...", flush=True)
        try:
            result = run_survival_update(source, settings=settings)
        except Exception as exc:  # noqa: BLE001 - driver boundary, keep going
            print(f"    FAILED: {exc}", flush=True)
            failures += 1
            continue
        posterior = result.metadata["phase2"]["posterior"]
        print(
            f"    rejected {100.0 * posterior['rejection_fraction']:.3f}% "
            f"({posterior['n_prior'] - posterior['n_accepted']:,} of "
            f"{posterior['n_prior']:,}) in {time.time() - tick:.0f} s "
            f"-> {_rel(target)}",
            flush=True,
        )
    print(
        f"\n{len(pending) - failures} of {len(pending)} replays completed in "
        f"{(time.time() - started) / 60.0:.1f} min"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
