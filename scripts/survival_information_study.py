"""Measure what the 2016 survival constrains, and what it cannot establish.

Companion driver for
``docs/decisions/survival-information-and-nesting-study.md``. Changes no
default, regenerates no persisted production artifact, and derives nothing
the engine's own kernels or committed arrays can supply.

Four parts, selected with ``--part`` (default ``all``):

``conditioning``
    Whether the survival constraint conditions the independently drawn
    seepage length, and by how much. Reads the eight production posteriors
    and reports the acceptance profile ``P(S | L)`` over prior deciles
    alongside the moment shifts, because the profile is what discriminates:
    a conditioned marginal has a sloped profile whether or not its mean has
    moved.

``nesting``
    Whether the empty ``transient_only_reject`` cell is a theorem or a
    measurement. Checks the derived implication row by row on the 2016
    replay (transient failure must force ``Z_static < -0.3 * D_bl``) and
    counts violations across every production conditioning level, which is
    where a forward-Euler step could break it.

``future``
    What a survival OTHER than 2016 would do to the seepage length. Phase
    1's persisted transient failure matrix is the survival indicator of
    every prior row at every conditioning level, computed with that row's
    own paired ``L``, so each column is a hypothetical event's survival set
    and the whole ladder is available at no simulation cost. Scope: these
    are canonical-shape conditioning waves (ADR-0020), not reconstructions
    of any real future flood.

``excursions``
    Whether the 2016 loading contains any inter-peak interval at which a
    memory reset could act, measured at the mechanism's own datum. Separates
    finite duration within one excursion from damage carried between peaks.
    Also reports the above-toe duration at the corrected KP 56.73 gauge node
    and, for attribution only, at the superseded KP 56.6 node.

Usage::

    python scripts/survival_information_study.py \
        --out docs/decisions/survival-information-and-nesting-study.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from bayesian_reliability_updating.analysis import (  # noqa: E402
    seepage_length_update,
)
from bayesian_reliability_updating.events import (  # noqa: E402
    default_2016_source,
    observed_event_record,
)
from bayesian_reliability_updating.replay import load_phase1_run  # noqa: E402
from bep_reliability_engine.progression import (  # noqa: E402
    CRACK_RESISTANCE_FACTOR,
)

SECTIONS: tuple[tuple[str, float], ...] = (
    ("kp57.4", 57.4),
    ("kp58.8", 58.8),
    ("kp60.0", 60.0),
    ("kp62.0", 62.0),
)
READINGS: tuple[str, ...] = ("matrix", "bulk")
SUPERSEDED_GAUGE_KP: float = 56.6


def _phase1(section: str, reading: str) -> Path:
    return REPO / "results" / f"tokachi_{section}_historical_{reading}.h5"


def _posterior(section: str, reading: str) -> Path:
    return (
        REPO
        / "results"
        / "phase2"
        / f"tokachi_{section}_historical_{reading}_posterior.h5"
    )


def _load_posterior(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        names = [
            n.decode() if isinstance(n, bytes) else str(n)
            for n in handle["param_names"][:]
        ]
        (event_id,) = list(handle["events"].keys())
        group = handle["events"][event_id]
        return {
            "event_id": event_id,
            "param_names": names,
            "theta": handle["theta_matrix"][:],
            "L": handle["seepage_length_samples"][:],
            "accept": handle["accept"][:],
            "accept_trans": group["accept_trans"][:],
            "accept_static": group["accept_static"][:],
            "Z_static": group["Z_static"][:],
        }


# ------------------------------------------------------------------ #
# conditioning
# ------------------------------------------------------------------ #


def part_conditioning() -> dict[str, Any]:
    """Does the 2016 survival condition L, and by how much?"""
    out: dict[str, Any] = {}
    for section, _kp in SECTIONS:
        for reading in READINGS:
            data = _load_posterior(_posterior(section, reading))
            summary = seepage_length_update(
                data["L"],
                data["accept"],
                theta=data["theta"],
                param_names=data["param_names"],
            )
            theta_shift = {}
            for index, name in enumerate(data["param_names"]):
                col = data["theta"][:, index]
                kept = col[data["accept"]]
                theta_shift[name] = float(kept.mean() / col.mean() - 1.0)
            out[f"{section}_{reading}"] = {
                "event_id": data["event_id"],
                "n_prior": int(data["accept"].size),
                "n_posterior": int(data["accept"].sum()),
                "rejection_fraction": float(1.0 - data["accept"].mean()),
                "seepage_length": summary,
                "theta_relative_mean_shift": theta_shift,
                "largest_theta_mean_shift": max(
                    theta_shift, key=lambda k: abs(theta_shift[k])
                ),
            }
    return out


# ------------------------------------------------------------------ #
# nesting
# ------------------------------------------------------------------ #


def part_nesting() -> dict[str, Any]:
    """Is the empty marginal-transient cell a theorem or a measurement?"""
    replay: dict[str, Any] = {}
    for section, _kp in SECTIONS:
        for reading in READINGS:
            data = _load_posterior(_posterior(section, reading))
            names = data["param_names"]
            d_bl = data["theta"][:, names.index("D_bl")]
            failed_trans = ~data["accept_trans"]
            failed_static = ~data["accept_static"]
            margin = (
                data["Z_static"][failed_trans]
                + CRACK_RESISTANCE_FACTOR * d_bl[failed_trans]
            )
            survive_t = float(data["accept_trans"].mean())
            survive_s = float(data["accept_static"].mean())
            replay[f"{section}_{reading}"] = {
                "n_fail_transient": int(failed_trans.sum()),
                "n_fail_static": int(failed_static.sum()),
                "marginal_transient_count": int(
                    (data["accept_static"] & ~data["accept_trans"]).sum()
                ),
                "static_only_reject_count": int(
                    (~data["accept_static"] & data["accept_trans"]).sum()
                ),
                "predicted_margin_max_m": (
                    float(margin.max()) if margin.size else None
                ),
                "predicted_margin_holds": (
                    bool((margin < 0.0).all()) if margin.size else None
                ),
                "P_survival_transient_model": survive_t,
                "P_survival_static_model": survive_s,
                "survival_probability_ratio": (
                    survive_t / survive_s if survive_s > 0.0 else None
                ),
            }

    # The same implication across every production conditioning level: this
    # is where a forward-Euler step can jump the equilibrium barrier and
    # produce the violation ADR-0030 used as its timestep diagnostic.
    sweeps: dict[str, Any] = {}
    total_cells = 0
    total_violations = 0
    for section, _kp in SECTIONS:
        for reading in READINGS:
            with h5py.File(_phase1(section, reading), "r") as handle:
                trans = handle["failure_matrix_trans"][:].astype(bool)
                static = handle["failure_matrix_static"][:].astype(bool)
                grid = handle["conditioning_grid"][:]
            violations = int((trans & ~static).sum())
            cells = int(trans.size)
            total_cells += cells
            total_violations += violations
            sweeps[f"{section}_{reading}"] = {
                "n_rows": int(trans.shape[0]),
                "n_levels": int(trans.shape[1]),
                "row_level_evaluations": cells,
                "trans_and_not_static": violations,
                "grid_min_m": float(grid.min()),
                "grid_max_m": float(grid.max()),
            }
    return {
        "replay_2016": replay,
        "conditioning_sweeps": sweeps,
        "total_row_level_evaluations": total_cells,
        "total_trans_and_not_static": total_violations,
        "crack_resistance_factor": CRACK_RESISTANCE_FACTOR,
    }


# ------------------------------------------------------------------ #
# future
# ------------------------------------------------------------------ #


def part_future(min_survivors_fraction: float = 0.01) -> dict[str, Any]:
    """What a survival other than 2016 would do to the seepage length."""
    out: dict[str, Any] = {}
    for section, _kp in SECTIONS:
        for reading in READINGS:
            with h5py.File(_phase1(section, reading), "r") as handle:
                fail = handle["failure_matrix_trans"][:].astype(bool)
                grid = handle["conditioning_grid"][:]
            with h5py.File(_posterior(section, reading), "r") as handle:
                L = handle["seepage_length_samples"][:]
            if L.size != fail.shape[0]:
                raise ValueError(
                    f"{section} {reading}: {L.size} seepage rows against "
                    f"{fail.shape[0]} failure rows."
                )
            # the ladder must be nested for a column to be a survival event
            non_monotone = int((fail[:, :-1] & ~fail[:, 1:]).sum())
            prior_mean = float(L.mean())
            prior_var = float(L.var(ddof=1))
            floor = min_survivors_fraction * L.size

            levels = []
            for index, level in enumerate(grid):
                survive = ~fail[:, index]
                n = int(survive.sum())
                row: dict[str, Any] = {
                    "h_m_msl": float(level),
                    "P_survive": float(survive.mean()),
                    "n_survivors": n,
                }
                if n >= floor:
                    kept = L[survive]
                    row.update(
                        {
                            "mean_m": float(kept.mean()),
                            "relative_mean_shift": float(
                                kept.mean() / prior_mean - 1.0
                            ),
                            "cov": float(kept.std(ddof=1) / kept.mean()),
                            "variance_ratio": float(kept.var(ddof=1) / prior_var),
                        }
                    )
                levels.append(row)

            usable = [r for r in levels if "variance_ratio" in r]
            best = min(usable, key=lambda r: r["variance_ratio"]) if usable else None
            out[f"{section}_{reading}"] = {
                "prior_mean_m": prior_mean,
                "prior_cov": float(L.std(ddof=1) / prior_mean),
                "ladder_non_monotone_pairs": non_monotone,
                "min_survivors_fraction": min_survivors_fraction,
                "levels": levels,
                "most_informative_level": best,
            }
    return out


# ------------------------------------------------------------------ #
# excursions
# ------------------------------------------------------------------ #


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index, n = 0, int(mask.size)
    while index < n:
        if mask[index]:
            end = index
            while end + 1 < n and mask[end + 1]:
                end += 1
            spans.append((index, end))
            index = end + 1
        else:
            index += 1
    return spans


def part_excursions() -> dict[str, Any]:
    """Is there any inter-peak interval at which a memory reset could act?"""
    source = default_2016_source(REPO / "data" / "processed" / "2016_event")
    superseded = dataclasses.replace(source, gauge_kp=SUPERSEDED_GAUGE_KP)
    out: dict[str, Any] = {"gauge_kp": source.gauge_kp}
    per_section: dict[str, Any] = {}
    for section, kp in SECTIONS:
        run = load_phase1_run(_phase1(section, "matrix"), verify_theta=False)
        z_toe = float(run.geometry["z_toe"])
        names = list(run.result.param_names)
        d_bl = run.result.theta_matrix[:, names.index("D_bl")]
        record = observed_event_record(
            source,
            section_kp=kp,
            data_root=str(REPO / "data" / "raw"),
            anchor="trace_right",
        )
        old_record = observed_event_record(
            superseded,
            section_kp=kp,
            data_root=str(REPO / "data" / "raw"),
            anchor="trace_right",
        )
        h = np.asarray(record.h, dtype=float)
        dt_h = float(record.native_dt) / 3600.0

        thresholds = {
            "toe": z_toe,
            "toe_plus_crack_p05": z_toe
            + CRACK_RESISTANCE_FACTOR * float(np.quantile(d_bl, 0.05)),
            "toe_plus_crack_median": z_toe
            + CRACK_RESISTANCE_FACTOR * float(np.median(d_bl)),
        }
        entry: dict[str, Any] = {
            "z_toe_m_msl": z_toe,
            "peak_m_msl": float(h.max()),
            "sample_dt_hours": dt_h,
            "D_bl_median_m": float(np.median(d_bl)),
            "hours_above_toe": float((h > z_toe).sum() * dt_h),
            "hours_above_toe_superseded_gauge": float(
                (np.asarray(old_record.h, dtype=float) > z_toe).sum() * dt_h
            ),
        }
        for label, threshold in thresholds.items():
            spans = _runs(h > threshold)
            entry[label] = {
                "threshold_m_msl": float(threshold),
                "n_excursions": len(spans),
                "excursion_hours": [
                    float((end - start + 1) * dt_h) for start, end in spans
                ],
                "gap_hours": [
                    float((spans[k + 1][0] - spans[k][1] - 1) * dt_h)
                    for k in range(len(spans) - 1)
                ],
            }
        per_section[section] = entry
    out["sections"] = per_section
    out["superseded_gauge_kp"] = SUPERSEDED_GAUGE_KP
    return out


# ------------------------------------------------------------------ #


PARTS = {
    "conditioning": part_conditioning,
    "nesting": part_nesting,
    "future": part_future,
    "excursions": part_excursions,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=(*PARTS, "all"), default="all", help="which part to run"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO
        / "docs"
        / "decisions"
        / "survival-information-and-nesting-study.json",
    )
    args = parser.parse_args(argv)

    selected = PARTS if args.part == "all" else {args.part: PARTS[args.part]}
    record: dict[str, Any] = {
        "study": "survival_information_and_nesting",
        "date": "2026-09-16",
        "note": (
            "Measures what the 2016 survival constrains. No default, prior, "
            "persisted sweep or posterior is changed; every number is read "
            "from committed artifacts or recomputed through the engine's own "
            "kernels."
        ),
    }
    for name, function in selected.items():
        print(f"[survival-information] {name}", flush=True)
        record[name] = function()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(f"[survival-information] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
