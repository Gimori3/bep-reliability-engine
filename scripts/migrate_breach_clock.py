"""Derive corrected ADR-0053 breach clocks without claiming a physical rerun.

Preserve each original posterior and sidecar, prove its terminal load inert,
and change only finite breach timestamps. Unsupported provenance fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bayesian_reliability_updating.events import (  # noqa: E402
    default_2016_source,
    observed_event_record,
)
from bep_reliability_engine.hydrographs import resample_record  # noqa: E402


def digest(path):
    """SHA256 of actual file bytes."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dataset_hashes(path):
    """Hash every dataset, preserving dtype and shape in the identity."""
    values = {}
    with h5py.File(path) as handle:

        def visit(name, obj):
            if isinstance(obj, h5py.Dataset):
                a = obj[()]
                values[name] = hashlib.sha256(
                    str((a.dtype, a.shape)).encode()
                    + (repr(a.tolist()).encode() if a.dtype.hasobject else a.tobytes())
                ).hexdigest()

        handle.visititems(visit)
    return values


def migrate(sidecar, archive):
    """Apply only the proven elapsed-end-state transformation to one run."""
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    assert "clock_correction_adr0053" not in metadata, "already corrected"
    phase2 = metadata["phase2"]
    assert phase2["l_ini_m"] == 0 and phase2["recovery_r_l"] == 0
    changes = {}
    for event in phase2["event_chain"]:
        assert (
            event["settings"].get("time_contract") is None
        ), "already uses corrected clock"
        provenance = event["record"]["provenance"]
        assert provenance["event_source"] == "typhoon_201608"
        assert provenance["gauge_kp"] == 56.73, "stale gauge requires replay"
        record = observed_event_record(
            default_2016_source(),
            section_kp=provenance["section_kp"],
            anchor=provenance["anchor"],
        )
        dt = event["record"]["native_dt_s"]
        record = resample_record(record, dt)
        closure = event["window_closure"]
        assert closure["end_margin_below_toe_m"] >= 0
        assert record.h[-1] == closure["end_stage_m_msl"]
        assert record.peak == event["record"]["peak_m_msl"]
        assert np.isfinite(record.h).all() and np.isfinite(record.t).all()
        changes[f"events/{event['event_id']}/t_breach"] = {
            "offset_s": float(dt - record.t[0]),
            "record_sha256": hashlib.sha256(
                record.t.tobytes() + record.h.tobytes()
            ).hexdigest(),
        }
    h5 = sidecar.with_suffix(".h5")
    before = dataset_hashes(h5)
    with h5py.File(h5) as handle:
        assert np.isfinite(handle["theta_matrix"][:]).all()
        assert (handle["theta_matrix"][:] > 0).all()
        if "seepage_length_samples" in handle:
            assert (handle["seepage_length_samples"][:] > 0).all()
    archive.mkdir(parents=True, exist_ok=True)
    for source in (h5, sidecar):
        target = archive / source.name
        assert not target.exists(), f"archive exists: {target}"
        shutil.copy2(source, target)
    provenance = dict(
        date="2026-09-15",
        kind="derived_timestamp_correction_not_physical_rerun",
        old_h5_sha256=digest(h5),
        old_sidecar_sha256=digest(sidecar),
        changes=changes,
    )
    with h5py.File(h5, "r+") as handle:
        for name, change in changes.items():
            if name not in handle:
                change["finite_count"] = 0
                continue
            a = handle[name][:]
            finite = np.isfinite(a)
            change["finite_count"] = int(finite.sum())
            a[finite] += change["offset_s"]
            handle[name][:] = a
    after = dataset_hashes(h5)
    assert before.keys() == after.keys()
    assert all(before[k] == after[k] for k in before if k not in changes)
    provenance["unchanged_dataset_hashes"] = {
        k: v for k, v in before.items() if k not in changes
    }
    provenance["new_h5_sha256"] = digest(h5)
    metadata["clock_correction_adr0053"] = provenance
    sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return dict(path=str(sidecar), **provenance, new_sidecar_sha256=digest(sidecar))


def main():
    """Migrate explicitly supplied files, with a separate immutable archive."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sidecars", nargs="+", type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    rows = []
    for path in args.sidecars:
        # Retain relative directories to prevent identical names colliding.
        relative = path.resolve().relative_to((ROOT / "results").resolve())
        rows.append(migrate(path, args.archive / relative.parent))
        args.manifest.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print(path, flush=True)


if __name__ == "__main__":
    main()
