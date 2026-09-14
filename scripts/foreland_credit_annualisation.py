"""ADR-0052 Part 3: the foreland seepage-length credit carried through Phase 3.

The conditional-curve bracket (`scripts/foreland_credit_bracket_study.py`)
measures what declining the TR Zandmeevoerende Wellen 1999 §4.4.2 credit is
worth on the fragility curves. This driver carries the same arms across the
annualisation integral, where every RQ3 and RQ4 headline lives, in exactly the
way `scripts/conductivity_annualisation_study.py` carries the conductivity
bracket.

Nothing is re-swept and nothing is re-implemented. The arm sweeps already exist
under `results/sensitivity/adr0052_foreland_credit/` (N = 1e5, produced by the
bracket study, whose own gate proved each baseline bit-identical to the
persisted production sweep), the Phase 3 hazard cache is reused read-only, and
**the composition and annualisation steps are imported from the conductivity
study, which imports them from the campaign** -- so the production code path is
what gets exercised, and gate 1 tests it.

Gates (a failure aborts rather than being tabulated):

1. The baseline pass must reproduce `rq4_annual.csv` EXACTLY for every
   matrix / prior / 250 m / primary row, field for field (the imported
   `gate_one`). If the baseline does not reproduce production, no arm number
   means anything.
2. Every arm curve must come from a sweep whose sidecar records the expected
   `foreland_seepage_credit`, so an arm cannot silently be the baseline.
3. The 110 segments carrying no BEP source must be bit-identical across every
   arm: the credit reaches the four BEP sections and nothing else.

What it reports, at the four BEP sections in both climates: annual system
probability, the per-mechanism annual contribution, and the mechanism shares --
and whether the RQ3 statement that piping accounts for 81 to 100 per cent of
the summed annual contribution survives the credit.

Usage (repo root, venv active)::

    python scripts/foreland_credit_annualisation.py
    python scripts/foreland_credit_annualisation.py --arms credit_full
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from system_integration.bep_input import load_bep_curve  # noqa: E402


def _load_conductivity_module():
    """Import the conductivity study for its context, gate and annualiser.

    The composition pipeline is **reused, never re-implemented**: a second copy
    could drift from the one that produced the committed Phase 3 records this
    study sits beside. Same ``importlib`` route the other companion studies use.
    """
    path = REPO_ROOT / "scripts" / "conductivity_annualisation_study.py"
    spec = importlib.util.spec_from_file_location(
        "conductivity_annualisation_study", path
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_COND = _load_conductivity_module()
BEP_KPS = _COND.BEP_KPS

ARM_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0052_foreland_credit"
#: This study's own arm posteriors, written by the ordinary Phase 2 CLI. Same
#: shape as the conductivity study's POSTERIOR_ARM_DIR.
POSTERIOR_ARM_DIR = ARM_DIR / "phase2"


def json_out(side: str) -> pathlib.Path:
    suffix = "" if side == "prior" else "-posterior"
    return (
        REPO_ROOT
        / "docs"
        / "decisions"
        / f"adr0052-foreland-credit-annualisation{suffix}.json"
    )


#: The arms, and the ``foreland_seepage_credit`` each sweep must record.
ARMS: dict[str, float] = {"credit_half": 0.5, "credit_full": 1.0}

#: The RQ3 claim under test, from the production campaign record.
RQ3_LOW, RQ3_HIGH = 0.81, 1.00


def _stem(kp: float) -> str:
    return f"tokachi_kp{kp:.1f}_historical_matrix"


def _arm_sweep(kp: float, arm: str) -> Path:
    """The Phase 1 arm sweep. Always Phase 1, whichever side is under test."""
    return ARM_DIR / f"{_stem(kp)}_{arm}.h5"


def _arm_curve_path(kp: float, arm: str, side: str) -> Path:
    """The artifact an arm's BEP curve is read from, per side."""
    if side == "prior":
        return _arm_sweep(kp, arm)
    return POSTERIOR_ARM_DIR / f"{_stem(kp)}_{arm}_posterior.h5"


def _gate_two(kp: float, arm: str) -> float | None:
    """Assert the arm sweep really carries the credit it claims to."""
    sidecar = _arm_sweep(kp, arm).with_suffix(".json")
    if not sidecar.is_file():
        raise AssertionError(f"missing sidecar for {_arm_sweep(kp, arm).name}")
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    recorded = meta.get("config", {}).get("foreland_seepage_credit")
    expected = ARMS[arm]
    if recorded is None or float(recorded) != float(expected):
        raise AssertionError(
            f"GATE 2 FAILED: {_arm_sweep(kp, arm).name} records "
            f"foreland_seepage_credit={recorded!r}, expected {expected!r}. The "
            "arm would silently be a different model from the one reported."
        )
    return float(recorded)


def _gate_three(baseline_rows, arm_rows: dict[str, Any]) -> dict[str, Any]:
    """The 110 non-BEP segments must not move under any arm."""
    bep_keys = {(("Tokachi"), kp) for kp in BEP_KPS}
    checked = 0
    for key, row in baseline_rows.items():
        river, kp, _scenario = key
        if (river, round(kp, 1)) in bep_keys:
            continue
        checked += 1
        for arm, rows in arm_rows.items():
            if rows[key] != row:
                raise AssertionError(
                    f"GATE 3 FAILED: non-BEP segment {key} moved under {arm}. "
                    "The credit reaches the four BEP sections and nothing else."
                )
    return {"passed": True, "non_bep_rows_compared": checked}


def _section_rows(rows, kp: float, scenario: str) -> dict[str, Any]:
    return rows[("Tokachi", kp, scenario)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arms", nargs="*", default=list(ARMS), choices=list(ARMS))
    parser.add_argument(
        "--side",
        choices=("prior", "posterior"),
        default="prior",
        help=(
            "Which side of the 2016 survival update to annualise. 'prior' "
            "(default) reproduces the 2026-09-13 record. 'posterior' is the "
            "side the published RQ3/RQ4 headline lives on "
            "(phase3_campaign.py defaults to bep_source=posterior), so it is "
            "the like-for-like comparison for those numbers; it requires the "
            "arm posteriors under results/sensitivity/adr0052_foreland_credit/"
            "phase2/."
        ),
    )
    args = parser.parse_args(argv)

    started = time.time()
    campaign = _COND._load_campaign_module()
    print("building registry, surface curves and node hazard ...", flush=True)
    context = _COND.build_context(campaign, "matrix", args.side)

    print(f"baseline pass, {args.side} side (gate 1) ...", flush=True)
    baseline_rows, _cov, _drv = _COND.annualise_variant(
        campaign, context, context["baseline_curves"], "matrix", args.side
    )
    gate1 = _COND.gate_one(baseline_rows, "matrix", args.side)
    print(
        f"  gate 1 passed: {gate1['rows_compared']} rows x "
        f"{gate1['fields_compared']} fields reproduce "
        f"{gate1['table']} exactly",
        flush=True,
    )

    arm_rows: dict[str, Any] = {}
    arm_credits: dict[str, dict[str, float | None]] = {}
    for arm in args.arms:
        print(f"arm {arm} (phi = {ARMS[arm]}) ...", flush=True)
        arm_credits[arm] = {}
        curves = {}
        for kp in BEP_KPS:
            arm_credits[arm][_COND._label(kp)] = _gate_two(kp, arm)
            curves[kp] = load_bep_curve(
                _arm_curve_path(kp, arm, args.side), branch="transient"
            )
            if float(curves[kp].datum_m) != float(
                context["baseline_curves"][kp].datum_m
            ):
                raise AssertionError(
                    f"{arm} KP {kp}: curve datum differs from the baseline's; "
                    "the arm would not be composed against the same exposure."
                )
        arm_rows[arm], _c, _d = _COND.annualise_variant(
            campaign, context, curves, "matrix", args.side
        )
    gate3 = _gate_three(baseline_rows, arm_rows)
    print(
        f"  gate 3 passed: {gate3['non_bep_rows_compared']} non-BEP rows "
        "bit-identical across every arm",
        flush=True,
    )

    sections: list[dict[str, Any]] = []
    for kp in BEP_KPS:
        for scenario in campaign.SCENARIOS:
            base = _section_rows(baseline_rows, kp, scenario)
            entry: dict[str, Any] = {
                "section": _COND._label(kp),
                "scenario": scenario,
                "mechanisms": base["mechanisms"],
                "baseline": {
                    "p_annual_system": base["p_annual_system"],
                    "p_annual_bep": base["p_annual_bep"],
                    "p_annual_overflow": base["p_annual_overflow"],
                    "p_annual_fluvial_scour": base["p_annual_fluvial_scour"],
                    "share_bep": base["share_bep"],
                    "share_overflow": base["share_overflow"],
                    "bep_clamped_above_grid": base["bep_clamped_above_grid"],
                },
                "arms": {},
            }
            for arm in args.arms:
                row = _section_rows(arm_rows[arm], kp, scenario)
                entry["arms"][arm] = {
                    "p_annual_system": row["p_annual_system"],
                    "p_annual_bep": row["p_annual_bep"],
                    "p_annual_overflow": row["p_annual_overflow"],
                    "p_annual_fluvial_scour": row["p_annual_fluvial_scour"],
                    "share_bep": row["share_bep"],
                    "share_overflow": row["share_overflow"],
                    "bep_clamped_above_grid": row["bep_clamped_above_grid"],
                    "system_ratio_to_baseline": (
                        None
                        if not base["p_annual_system"]
                        else row["p_annual_system"] / base["p_annual_system"]
                    ),
                    "bep_ratio_to_baseline": (
                        None
                        if not base["p_annual_bep"]
                        else row["p_annual_bep"] / base["p_annual_bep"]
                    ),
                }
            sections.append(entry)

    # The RQ3 statement under test, evaluated rather than asserted.
    rq3: dict[str, Any] = {
        "claim": (
            "piping accounts for 81 to 100 per cent of the summed annual "
            "contribution at the four BEP sections"
        ),
        "baseline_shares": {},
        "arm_shares": {},
        "verdict": {},
    }
    for entry in sections:
        key = f"{entry['section']} {entry['scenario']}"
        rq3["baseline_shares"][key] = entry["baseline"]["share_bep"]
        rq3["arm_shares"][key] = {
            arm: entry["arms"][arm]["share_bep"] for arm in args.arms
        }

    def _in_band(value: Any) -> bool | None:
        if value == "" or value is None:
            return None
        return bool(RQ3_LOW <= float(value) <= RQ3_HIGH)

    rq3["verdict"]["baseline_all_in_band"] = all(
        _in_band(v) for v in rq3["baseline_shares"].values() if _in_band(v) is not None
    )
    for arm in args.arms:
        shares = [rq3["arm_shares"][k][arm] for k in rq3["arm_shares"]]
        flags = [_in_band(v) for v in shares]
        rq3["verdict"][arm] = {
            "cells_evaluated": sum(f is not None for f in flags),
            "cells_in_band": sum(bool(f) for f in flags if f is not None),
            "all_in_band": all(f for f in flags if f is not None),
            "min_share": min(
                (float(v) for v in shares if v not in ("", None)), default=None
            ),
            "max_share": max(
                (float(v) for v in shares if v not in ("", None)), default=None
            ),
        }

    payload = {
        "adr": "0052",
        "description": (
            "The TR Zandmeevoerende Wellen 1999 section 4.4.2 foreland "
            "seepage-length credit carried through the Phase 3 annualisation, "
            "matrix reading, prior side. Composition and annualisation imported "
            "from scripts/conductivity_annualisation_study.py (which imports "
            "them from the campaign), so the production code path is what runs. "
            "No sweep re-run, no hazard workbook streamed, no production value "
            "changed."
        ),
        "side": args.side,
        "arms": {arm: ARMS[arm] for arm in args.arms},
        "arm_credit_recorded": arm_credits,
        "gates": {"gate_1_reproduces_production": gate1, "gate_3_non_bep": gate3},
        "sections": sections,
        "rq3": rq3,
        "total_runtime_s": round(time.time() - started, 1),
    }
    # The conductivity study writes its payload unrounded; this one follows it
    # rather than introducing a second convention for the same kind of record.
    out = json_out(args.side)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out.relative_to(REPO_ROOT)}")
    for entry in sections:
        arms = "  ".join(
            f"{arm}: {entry['arms'][arm]['p_annual_system']:.3e} "
            f"(share_bep {entry['arms'][arm]['share_bep']})"
            for arm in args.arms
        )
        print(
            f"  {entry['section']:>9s} {entry['scenario']:<12s} baseline "
            f"{entry['baseline']['p_annual_system']:.3e} "
            f"(share_bep {entry['baseline']['share_bep']})   {arms}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
