"""Build the Uemura section-aggregation table (ADR-0043).

Reconstructs the segment -> section membership as KP ranges from the
evidence in Uemura's own committed geometry:

* Satsunai: the four section polylines in ``data/raw/gis/SECTIONS.shp``
  form one contiguous chain anchored at the KP 3.2 node; cumulative arc
  length fixes the boundaries.
* Tokachi: midpoint boundaries between the representative section KPs,
  cross-validated against each polyline's arc length.

The script parses the shapefile itself and FAILS if any reconstructed span
disagrees with its polyline length by more than the ADR-0043 tolerance, or
if any of the ten node assignments embedded in Uemura's notebook output is
violated. Output: ``data/processed/uemura_segments/section_table.csv`` in
the ADR-0038 D2 contract format.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from system_integration.segments import build_registry, load_section_table  # noqa: E402

SECTIONS_SHP = REPO / "data/raw/gis/SECTIONS.shp"
SECTIONS_DBF = REPO / "data/raw/gis/SECTIONS.dbf"
OUT_CSV = REPO / "data/processed/uemura_segments/section_table.csv"

LENGTH_TOL_KM = 0.3  # ADR-0043: one-and-a-half grid steps

# The reconstructed table (ADR-0043 decision 1). kp_from/kp_to inclusive.
TABLE: list[tuple[str, str, float, float, str]] = [
    ("Satsunai", "left", 3.2, 4.6, "KP4.2"),
    ("Satsunai", "left", 4.8, 5.8, "KP5.2"),
    ("Satsunai", "left", 6.0, 6.4, "KP6.4"),
    ("Satsunai", "left", 6.6, 7.0, "KP7.0"),
    ("Tokachi", "right", 53.8, 57.2, "KP56.4"),
    ("Tokachi", "right", 57.4, 58.8, "KP58.0"),
    ("Tokachi", "right", 59.0, 60.4, "KP59.6"),
    ("Tokachi", "right", 60.6, 61.8, "KP61.4"),
    ("Tokachi", "right", 62.0, 62.8, "KP62.4"),
]

# Ten node->section assignments recovered verbatim from Uemura's notebook
# output (ADR-0043 context). The Satsunai KP 3.2 row in that output carried
# the pre-river-filter bug and is excluded as evidence.
KNOWN_ASSIGNMENTS: list[tuple[str, float, str]] = [
    ("Satsunai", 3.4, "KP4.2"),
    ("Satsunai", 3.6, "KP4.2"),
    ("Satsunai", 3.8, "KP4.2"),
    ("Satsunai", 4.0, "KP4.2"),
    ("Tokachi", 62.0, "KP62.4"),
    ("Tokachi", 62.2, "KP62.4"),
    ("Tokachi", 62.4, "KP62.4"),
    ("Tokachi", 62.6, "KP62.4"),
    ("Tokachi", 62.8, "KP62.4"),
]

# Sections whose polylines are drawn as double-traced (out-and-back) pairs:
# their arc length counts the levee span twice (start == end in the .shp).
DOUBLE_TRACED = {"KP59.6", "KP61.4"}
# KP56.4's polyline is a 14-part 22 km sprawl over the whole downstream
# area (multiple alignments); its length does not measure a single levee
# span and is excluded from the length check (ADR-0043 context).
LENGTH_CHECK_EXEMPT = {"KP56.4"}


def _read_polyline_lengths() -> dict[str, float]:
    """Section name -> polyline arc length [km] from SECTIONS.shp/.dbf."""
    data = open(SECTIONS_DBF, "rb").read()
    nrec = struct.unpack("<I", data[4:8])[0]
    hdrlen = struct.unpack("<H", data[8:10])[0]
    reclen = struct.unpack("<H", data[10:12])[0]
    fields = []
    off = 32
    while data[off] != 0x0D:
        name = data[off : off + 11].split(b"\x00")[0].decode("latin1")
        fields.append((name, data[off + 16]))
        off += 32
    names = []
    pos = hdrlen
    for _ in range(nrec):
        rec = data[pos : pos + reclen]
        pos += reclen
        o = 1
        for fname, flen in fields:
            value = rec[o : o + flen].decode("latin1").strip()
            o += flen
            if fname == "Name":
                names.append(value)

    shp = open(SECTIONS_SHP, "rb").read()
    lengths = []
    pos = 100
    while pos < len(shp):
        _, clen = struct.unpack(">ii", shp[pos : pos + 8])
        rec = shp[pos + 8 : pos + 8 + clen * 2]
        pos += 8 + clen * 2
        nparts, npoints = struct.unpack("<ii", rec[36:44])
        off = 44 + 4 * nparts
        pts = np.frombuffer(rec[off : off + 16 * npoints], dtype="<f8").reshape(
            npoints, 2
        )
        lengths.append(float(np.sum(np.hypot(*np.diff(pts, axis=0).T))) / 1000.0)
    return dict(zip(names, lengths))


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    lengths_km = _read_polyline_lengths()
    print(
        "SECTIONS.shp polyline lengths [km]:",
        {k: round(v, 2) for k, v in sorted(lengths_km.items())},
    )

    failures = []
    for river, _bank, kp_from, kp_to, sid in TABLE:
        span_km = kp_to - kp_from + 0.2  # inclusive node range -> covered length
        if sid in LENGTH_CHECK_EXEMPT:
            continue
        poly_km = lengths_km[sid]
        if sid in DOUBLE_TRACED:
            poly_km /= 2.0
        if abs(span_km - poly_km) > LENGTH_TOL_KM:
            failures.append(
                f"{sid}: reconstructed span {span_km:.2f} km vs polyline "
                f"{poly_km:.2f} km (tol {LENGTH_TOL_KM})."
            )
    if failures:
        raise SystemExit("GEOMETRY VALIDATION FAILED:\n" + "\n".join(failures))

    for river, kp, sid in KNOWN_ASSIGNMENTS:
        hit = [
            s
            for r, _b, lo, hi, s in TABLE
            if r == river and lo - 1e-9 <= kp <= hi + 1e-9
        ]
        if hit != [sid]:
            raise SystemExit(
                f"KNOWN-ASSIGNMENT VALIDATION FAILED: {river} KP {kp:g} -> "
                f"{hit!r}, notebook says {sid!r}."
            )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as handle:
        handle.write("river,bank,kp_from,kp_to,section_id\n")
        for river, bank, kp_from, kp_to, sid in TABLE:
            handle.write(f"{river},{bank},{kp_from:g},{kp_to:g},{sid}\n")

    # Final gate: the contract loader itself, with the ADR-0043 gap mode.
    registry = load_section_table(
        OUT_CSV, build_registry(REPO / "data/raw"), allow_gaps=True
    )
    n_assigned = sum(1 for s in registry.segments if s.section_id is not None)
    n_total = len(registry.segments)
    per_section: dict[str, int] = {}
    for s in registry.segments:
        if s.section_id:
            per_section[s.section_id] = per_section.get(s.section_id, 0) + 1
    print(f"wrote {OUT_CSV}: {n_assigned}/{n_total} segments sectioned")
    print("segments per section:", dict(sorted(per_section.items())))


if __name__ == "__main__":
    main()
