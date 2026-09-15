"""Verify ADR-0053 endpoint invariance on persisted production/companion inputs.

Reads every current Phase 1 sidecar with a matching HDF5 file; historical
superseded and development self-test folders are excluded explicitly.
No persisted run is relabelled or overwritten. Writes a new evidence JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bayesian_reliability_updating.events import (  # noqa: E402
    default_2016_source,
    observed_event_record,
)
from bayesian_reliability_updating.replay import load_phase1_run  # noqa: E402
from bep_reliability_engine import run as run_module  # noqa: E402
from bep_reliability_engine.config import Config  # noqa: E402


def digest(path: Path) -> str:
    """Hash the actual bytes, not a filename or metadata assertion."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    """Prove a removed final load is inert using its actual loading and toe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_module.load_canonical_shape = lru_cache(maxsize=None)(
        run_module.load_canonical_shape
    )
    rows = []
    for sidecar in sorted(args.results.rglob("*.json")):
        if any(p.startswith("superseded") or "selftest" in p for p in sidecar.parts):
            continue
        h5 = sidecar.with_suffix(".h5")
        if not h5.exists():
            continue
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        if "config" not in metadata:
            continue
        with h5py.File(h5) as handle:
            assembled = "P_f_static_raw" in handle
            if not assembled:
                config = Config.model_validate(metadata["config"])
                assert config.config_hash() == metadata["config_hash"], str(sidecar)
                theta = handle["theta_matrix"][:]
                lengths = (
                    handle["seepage_length_samples"][:]
                    if "seepage_length_samples" in handle
                    else run_module.seepage_length_samples_for_config(config)
                )
                run = SimpleNamespace(
                    config=config,
                    theta=theta,
                    geometry=config.geometry.as_evaluator_dict(),
                    seepage_length_samples=lengths,
                    n_samples=len(theta),
                    theta_verified=bool(
                        np.array_equal(
                            theta, run_module._sample_prior(config).theta_matrix
                        )
                    ),
                )
        if assembled:
            run = load_phase1_run(h5)
        if run.config.hydrograph_source is None:
            continue
        records = run_module.conditioning_hydrographs_for_config(run.config)
        # Independent finite checks supplement validation at construction.
        finite = all(np.isfinite(r.h).all() and np.isfinite(r.t).all() for r in records)
        positive_inputs = bool(
            np.all(run.theta > 0)
            and np.all(
                np.asarray(
                    run.geometry["L"]
                    if run.seepage_length_samples is None
                    else run.seepage_length_samples
                )
                > 0
            )
        )
        last = max(float(r.h[-1]) for r in records)
        toe = float(run.geometry["z_toe"])
        observed = observed_event_record(
            default_2016_source(), section_kp=run.config.hydrograph_source.kp
        )
        row = dict(
            path=str(h5.relative_to(args.results)),
            h5_sha256=digest(h5),
            sidecar_sha256=digest(sidecar),
            config_hash=run.config.config_hash(),
            theta_verified=run.theta_verified,
            n=run.n_samples,
            levels=len(records),
            finite=bool(finite),
            positive_inputs=positive_inputs,
            max_final_stage=last,
            z_toe=toe,
            final_step_inert=bool(finite and positive_inputs and last <= toe),
            observed_final_stage=float(observed.h[-1]),
            observed_final_step_inert=bool(
                np.isfinite(observed.h).all() and observed.h[-1] <= toe
            ),
            time_stage_hashes=[
                hashlib.sha256(r.t.tobytes() + r.h.tobytes()).hexdigest()
                for r in records
            ],
        )
        rows.append(row)
        print(row["path"], row["final_step_inert"], flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(dict(contract="ADR-0053", rows=rows), indent=2)
        )
    assert rows, "no persisted inputs were checked"
    assert all(
        r["final_step_inert"] for r in rows
    ), "active final load requires recomputation"


if __name__ == "__main__":
    main()
