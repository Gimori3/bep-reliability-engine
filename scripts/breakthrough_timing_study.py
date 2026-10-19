"""When do transient breakthroughs complete, relative to the flood peak?

Un-numbered study (no default changes). For the adopted transient criterion,
matrix reading, KP 58.8 and KP 60.0 as if undrained, prior realizations, the
canonical event scaled to each stage, it times every failing realization's
breakthrough and bins it against the peak of the scaled record.

Breakthrough time follows the record time contract (ADR-0053): the end of the
hourly loading interval in which the pipe first reaches L. With ``t_p`` the
peak observation of the scaled record, the bins are

* before:   ``t <= t_p``               (completed on the rising limb)
* peak hour: ``t_p < t <= t_p + 1 h``  (completed while the peak load acts)
* after:    ``t > t_p + 1 h``          (completed on the falling limb)

The per-row M7 re-run is gated: its end states must equal M8's
(``results_annotations_study._pipe_breach_times``), and every stored
transient failure must be re-timed. Every failing row is timed, in chunks.

Inputs are the persisted production sweeps ``results/tokachi_kp*_historical_matrix.h5``;
run from the repository root, where ``data/raw`` is present. Output:
``docs/decisions/breakthrough-timing-study.json``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import results_annotations_study as ras

from bayesian_reliability_updating.replay import load_phase1_run
from bep_reliability_engine.run import conditioning_hydrographs_for_config

STAGES_M = {
    "57.4": (40.0, 40.5, 41.0, 41.5),
    "58.8": (41.0, 41.5, 42.0, 42.5),
    "60.0": (42.75, 43.25, 43.75, 44.25),
    "62.0": (46.5, 47.0, 47.5, 48.0),
}
CHUNK_ROWS = 20000
HOUR_S = 3600.0


class _Bundle:
    """The attributes ``_pipe_breach_times`` reads from a run."""

    def __init__(self, run, names: list[str]) -> None:
        self.run = run
        self.names = names
        self.theta = np.asarray(run.theta, dtype=np.float64)
        self.L = np.asarray(run.seepage_length_samples, dtype=np.float64)


def _time_rows(bundle: _Bundle, record, rows: np.ndarray) -> np.ndarray:
    """Breakthrough times [s] of ``rows``, re-run in chunks and gated."""
    times = np.empty(rows.size, dtype=np.float64)
    for start in range(0, rows.size, CHUNK_ROWS):
        chunk = rows[start : start + CHUNK_ROWS]
        t_b, failed = ras._pipe_breach_times(bundle, record, chunk)
        if not np.all(failed) or not np.all(np.isfinite(t_b)):
            raise SystemExit("a stored transient failure was not re-timed")
        times[start : start + chunk.size] = t_b
    return times


def study_section(kp: str, results_dir: Path) -> list[dict]:
    path = results_dir / f"tokachi_kp{kp}_historical_matrix.h5"
    run = load_phase1_run(path)
    with h5py.File(path, "r") as handle:
        raw_names = handle["param_names"]
        names = [x.decode() if isinstance(x, bytes) else x for x in raw_names]
    bundle = _Bundle(run, names)
    grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
    failure = np.asarray(run.result.failure_matrix_tran, dtype=bool)
    records = conditioning_hydrographs_for_config(run.config)
    rows_out = []
    for stage in STAGES_M[kp]:
        i = int(np.argmin(np.abs(grid - stage)))
        if abs(grid[i] - stage) > 1e-6:
            continue
        record = records[i]
        t_rel = np.asarray(record.t, dtype=np.float64) - float(record.t[0])
        t_peak = float(t_rel[int(np.argmax(record.h))])
        failing = np.nonzero(failure[:, i])[0]
        entry: dict = {
            "stage_m": float(grid[i]),
            "n_realizations": int(failure.shape[0]),
            "n_transient_fail": int(failing.size),
            "t_peak_h": t_peak / HOUR_S,
        }
        if failing.size:
            t_b = _time_rows(bundle, record, failing)
            rel_h = (t_b - t_peak) / HOUR_S
            entry.update(
                {
                    "n_before_peak": int(np.sum(t_b <= t_peak)),
                    "n_in_peak_hour": int(
                        np.sum((t_b > t_peak) & (t_b <= t_peak + HOUR_S))
                    ),
                    "n_after_peak_hour": int(np.sum(t_b > t_peak + HOUR_S)),
                    "breach_h_rel_peak_percentiles_5_25_50_75_95": [
                        float(x) for x in np.percentile(rel_h, [5, 25, 50, 75, 95])
                    ],
                }
            )
            for key in ("before_peak", "in_peak_hour", "after_peak_hour"):
                entry[f"share_{key}"] = entry[f"n_{key}"] / failing.size
        rows_out.append(entry)
        print(kp, entry, flush=True)
    return rows_out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/decisions/breakthrough-timing-study.json"),
    )
    args = parser.parse_args()
    payload = {
        "study": "breakthrough-timing-study",
        "criterion": (
            "transient (adopted), prior, matrix reading, "
            "KP 58.8 and 60.0 as if undrained"
        ),
        "loading": "canonical event HPB_m064_1987 scaled to each grid stage",
        "time_contract": (
            "ADR-0053: breakthrough at the end of the completing hourly interval"
        ),
        "bins": {
            "before_peak": "t <= t_peak",
            "in_peak_hour": "t_peak < t <= t_peak + 1 h",
            "after_peak_hour": "t > t_peak + 1 h",
        },
        "sections": {kp: study_section(kp, args.results) for kp in STAGES_M},
    }
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
