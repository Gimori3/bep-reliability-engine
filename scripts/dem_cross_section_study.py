"""DEM-surveyed seepage length L for the four confined Tokachi sections.

Companion driver for ADR-0047 (see ``docs/decisions/adr0047-dem-seepage-length.md``).
Re-measures the under-levee confined seepage path ``L`` from the GSI DEM5A
airborne-lidar surface (secondary mesh 644331, ``devDate`` 2025-06-20) and
quantifies what the re-measured values would do to the production fragility.

The whole path is in code: JPGIS(GML) tiles -> mosaic -> profile lines placed
perpendicular to the levee alignment of ``data/raw/gis/SECTIONS.shp`` -> toe
picking by an explicit slope-break rule -> ``L`` -> a drift-guarded fragility
sensitivity against the persisted production sweeps.

**No input value is changed by this script.** ``data/processed/tokachi_bep_inputs.csv``
and ``configs/*.yaml`` are read-only here: the fragility arms override
``geometry.L`` in memory only, exactly like ``scripts/foreshore_width_study.py``
overrides ``geometry.foreshore_width``. Adopting a DEM value is a separate,
explicitly authorised decision that carries a full campaign re-run, because
``geometry.L`` sits inside ``Config.config_hash()`` and the Phase 2 replay
refuses hash drift.

**Adoption status (ADR-0047, 2026-07-29).** That decision was subsequently taken
for **KP 62.0 alone**: its CSV ``L`` is now the DEM-surveyed 40.0 m, because the
withdrawn 47.0 m credited a landside berm that never existed (a defect, not a
vintage difference). KP 57.4, KP 58.8 and KP 60.0 keep their 1998 values and
their DEM measurements are carried as an unadopted epistemic bracket. Where a
section has been adopted, this script drives its **withdrawn** value as the
labelled arm, so the comparison that justified adoption stays reproducible from
the new baseline.

Definition (hard constraint, provenance §3.1 / ADR-0005/0006)
------------------------------------------------------------
``L`` is the **under-levee confined path only**: riverside levee toe to
landside levee toe. It must not include the foreshore -- the foreland is
carried separately through ``lambda_out`` inside ``r_e``, so folding the
foreshore into ``L`` would double-count the foreland resistance. The
高水敷幅 (high-water-bed width) is measured here too, but as a **separate,
reported by-product**, never added to ``L``.

Vintage
-------
The DEM surface is **2025-06-20**; the CSV geometry is the **1998** OYO
pre-remediation survey. The difference per section is a finding to report
against the remediation history (provenance §3.2), not evidence that the DEM
is simply "more correct".

Stages
------
``profiles``
    Parse the GML tiles into a mosaic, sample each section's perpendicular
    profile, pick crest/toes, write the profile CSVs and the geometry table.
``datum``
    Hard-constraint-5 gate: DEM crest against the 2019 design bank height,
    DEM landside ground and riverside terrace against Uemura's longitudinal
    ``ground_m_msl`` / ``floodplain_m_msl``. Refuses to continue past ~1 m.
``fragility``
    Per section, re-run the production matrix sweep with the DEM-derived
    ``L`` substituted, after asserting the baseline arm bit-identical to the
    persisted ``results/tokachi_kp*_historical_matrix.h5`` sweep.
``all``
    ``datum`` + ``profiles`` + ``fragility`` (the deliverable).

Usage
-----
    python scripts/dem_cross_section_study.py profiles
    python scripts/dem_cross_section_study.py all
    python scripts/dem_cross_section_study.py fragility --sections KP62.0

The mosaic is cached under ``data/raw/geometry/dem_cross_sections/`` (gitignored)
but is always regenerable from the tiles alone; delete the cache to force a
re-parse. Profile extraction is seconds; the fragility stage is roughly 3 to 4
minutes per arm at the production N = 1e5 (eight arms by default).
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import h5py
import numpy as np
import yaml
from numpy.typing import NDArray

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _figstyle as figstyle  # noqa: E402

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
TILE_DIR = REPO_ROOT / "data/raw/geometry/FG-GML-644331-DEM5A-20250620"
PROFILE_DIR = REPO_ROOT / "data/raw/geometry/dem_cross_sections"
MOSAIC_CACHE = PROFILE_DIR / "_mosaic_cache.npz"
SECTIONS_SHP = REPO_ROOT / "data/raw/gis/SECTIONS.shp"
SECTIONS_DBF = REPO_ROOT / "data/raw/gis/SECTIONS.dbf"
BANK_HEIGHT_CSV = REPO_ROOT / "data/raw/geometry/BankHeight_TokachiRiv_2019.csv"
UEMURA_LONGITUDINAL = REPO_ROOT / "data/processed/uemura_segments/segment_inputs.csv"
INPUTS_CSV = REPO_ROOT / "data/processed/tokachi_bep_inputs.csv"
DEFAULT_OUT = REPO_ROOT / "docs/decisions/adr0047-dem-seepage-length.json"

#: DEM survey vintage, from the tiles' own ``devDate`` (asserted at parse time).
DEM_DEV_DATE = "2025-06-20"
#: Vintage of the OYO geometry the CSV ``L_m`` column is read from.
CSV_GEOMETRY_VINTAGE = "1998"
DEM_NODATA = -9999.0

# --------------------------------------------------------------------------- #
# EPSG:2455 -- JGD2000 / Japan Plane Rectangular CS XIII (SECTIONS.prj)        #
# --------------------------------------------------------------------------- #
GRS80_A = 6378137.0
GRS80_INV_F = 298.257222101
CS13_LAT0_DEG = 44.0
CS13_LON0_DEG = 144.25
CS13_K0 = 0.9999

_F = 1.0 / GRS80_INV_F
_E2 = _F * (2.0 - _F)
_LAT0 = np.deg2rad(CS13_LAT0_DEG)
_LON0 = np.deg2rad(CS13_LON0_DEG)


def _meridian_arc(phi: NDArray[np.float64] | float) -> NDArray[np.float64]:
    """Meridional arc length from the equator to latitude ``phi`` [rad]."""
    e2 = _E2
    c0 = 1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256 - 175 * e2**4 / 16384
    c2 = 3.0 / 8 * (e2 + e2**2 / 4 + 15 * e2**3 / 128 - 455 * e2**4 / 4096)
    c4 = 15.0 / 256 * (e2**2 + 3 * e2**3 / 4 - 77 * e2**4 / 128)
    c6 = 35.0 / 3072 * (e2**3 - 41 * e2**4 / 32)
    c8 = -315.0 / 131072 * e2**4
    return GRS80_A * (
        c0 * phi
        - c2 * np.sin(2 * phi)
        + c4 * np.sin(4 * phi)
        - c6 * np.sin(6 * phi)
        + c8 * np.sin(8 * phi)
    )


_M0 = float(_meridian_arc(_LAT0))


def plane_to_geographic(
    easting_m: NDArray[np.float64] | float,
    northing_m: NDArray[np.float64] | float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Inverse transverse-Mercator: EPSG:2455 metres -> (lat, lon) degrees.

    Parameters
    ----------
    easting_m, northing_m
        Plane Rectangular CS XIII coordinates, metres, as stored in
        ``SECTIONS.shp`` (GIS x = easting, y = northing).

    Returns
    -------
    lat_deg, lon_deg
        Geographic coordinates on GRS80 / JGD2000.

    Notes
    -----
    The standard USGS sixth-order series; round-trips against
    :func:`geographic_to_plane` to well below a millimetre over this reach,
    which is four orders of magnitude finer than the 5 m DEM posting. The
    DEM tiles are JGD2024 and ``SECTIONS.shp`` is JGD2000; the datum
    difference over Hokkaido is sub-metre and is deliberately not corrected,
    since a toe-to-toe *length* is invariant to a common translation.
    """
    e2 = _E2
    ep2 = e2 / (1 - e2)
    arc = _M0 + np.asarray(northing_m, dtype=float) / CS13_K0
    e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
    mu = arc / (GRS80_A * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * np.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * np.sin(4 * mu)
        + (151 * e1**3 / 96) * np.sin(6 * mu)
        + (1097 * e1**4 / 512) * np.sin(8 * mu)
    )
    sin1, cos1, tan1 = np.sin(phi1), np.cos(phi1), np.tan(phi1)
    c1 = ep2 * cos1**2
    t1 = tan1**2
    n1 = GRS80_A / np.sqrt(1 - e2 * sin1**2)
    r1 = GRS80_A * (1 - e2) / (1 - e2 * sin1**2) ** 1.5
    d = np.asarray(easting_m, dtype=float) / (n1 * CS13_K0)
    lat = phi1 - (n1 * tan1 / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lon = (
        _LON0
        + (
            d
            - (1 + 2 * t1 + c1) * d**3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
        )
        / cos1
    )
    return np.rad2deg(lat), np.rad2deg(lon)


def geographic_to_plane(
    lat_deg: NDArray[np.float64] | float,
    lon_deg: NDArray[np.float64] | float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Forward transverse-Mercator: (lat, lon) degrees -> EPSG:2455 metres."""
    phi = np.deg2rad(np.asarray(lat_deg, dtype=float))
    lam = np.deg2rad(np.asarray(lon_deg, dtype=float))
    e2 = _E2
    ep2 = e2 / (1 - e2)
    sin_p, cos_p, tan_p = np.sin(phi), np.cos(phi), np.tan(phi)
    n = GRS80_A / np.sqrt(1 - e2 * sin_p**2)
    t = tan_p**2
    c = ep2 * cos_p**2
    a = (lam - _LON0) * cos_p
    easting = (
        CS13_K0
        * n
        * (
            a
            + (1 - t + c) * a**3 / 6
            + (5 - 18 * t + t**2 + 72 * c - 58 * ep2) * a**5 / 120
        )
    )
    northing = CS13_K0 * (
        _meridian_arc(phi)
        - _M0
        + n
        * tan_p
        * (
            a**2 / 2
            + (5 - t + 9 * c + 4 * c**2) * a**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * ep2) * a**6 / 720
        )
    )
    return easting, northing


# --------------------------------------------------------------------------- #
# JPGIS(GML) DEM5A tiles                                                       #
# --------------------------------------------------------------------------- #
_RE_ENVELOPE = re.compile(
    r"<gml:lowerCorner>([\d.\-]+)\s+([\d.\-]+)</gml:lowerCorner>\s*"
    r"<gml:upperCorner>([\d.\-]+)\s+([\d.\-]+)</gml:upperCorner>"
)
_RE_HIGH = re.compile(r"<gml:high>(\d+)\s+(\d+)</gml:high>")
_RE_START = re.compile(r"<gml:startPoint>(\d+)\s+(\d+)</gml:startPoint>")
_RE_TUPLES = re.compile(r"<gml:tupleList>(.*?)</gml:tupleList>", re.S)
_RE_DEVDATE = re.compile(r"<devDate[^>]*>\s*<gml:timePosition>([\d\-]+)")


def parse_dem_tile(
    path: Path,
) -> tuple[tuple[float, float, float, float], NDArray, str]:
    """Parse one JPGIS(GML) DEM5A tile.

    Parameters
    ----------
    path
        Tile ``.xml`` file.

    Returns
    -------
    envelope
        ``(lat_lo, lon_lo, lat_hi, lon_hi)`` in degrees. Note the GML
        ``lowerCorner``/``upperCorner`` carry **latitude first**.
    grid
        ``(ny, nx)`` elevations in m T.P.; row 0 is the **northernmost**
        (``gml:sequenceRule order="+x-y"``). Cells absent from the tuple list
        are :data:`DEM_NODATA`.
    dev_date
        The tile's ``devDate`` timePosition (survey vintage).

    Notes
    -----
    ``gml:startPoint`` is an offset into the grid: a tile may begin part-way,
    so the head is padded with nodata rather than assuming a full ``nx * ny``
    tuple list.
    """
    text = path.read_text(encoding="utf-8")
    env = _RE_ENVELOPE.search(text)
    high = _RE_HIGH.search(text)
    tuples = _RE_TUPLES.search(text)
    if env is None or high is None or tuples is None:
        raise ValueError(f"{path.name}: not a parseable FGD DEM tile.")
    lat_lo, lon_lo, lat_hi, lon_hi = (float(g) for g in env.groups())
    nx = int(high.group(1)) + 1
    ny = int(high.group(2)) + 1
    values = np.array(
        [
            line.rsplit(",", 1)[1]
            for line in tuples.group(1).strip().splitlines()
            if line.strip()
        ],
        dtype=np.float64,
    )
    offset = 0
    start = _RE_START.search(text)
    if start is not None:
        offset = int(start.group(2)) * nx + int(start.group(1))
    if offset + values.size > nx * ny:
        raise ValueError(f"{path.name}: tuple list overruns the declared grid.")
    grid = np.full(nx * ny, DEM_NODATA, dtype=np.float64)
    grid[offset : offset + values.size] = values
    dev = _RE_DEVDATE.search(text)
    return (
        (lat_lo, lon_lo, lat_hi, lon_hi),
        grid.reshape(ny, nx),
        (dev.group(1) if dev else ""),
    )


@dataclass(frozen=True)
class DemMosaic:
    """A north-up geographic raster mosaic of DEM5A tiles.

    Attributes
    ----------
    grid
        ``(ny, nx)`` elevations in m T.P., row 0 northernmost.
    lat_hi, lon_lo
        Envelope corner of the mosaic (degrees).
    dlat, dlon
        Cell size in degrees (positive; latitude decreases with row index).
    dev_date
        Common ``devDate`` of the contributing tiles.
    """

    grid: NDArray[np.float64]
    lat_hi: float
    lon_lo: float
    dlat: float
    dlon: float
    dev_date: str

    def sample(
        self,
        lat_deg: NDArray[np.float64],
        lon_deg: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Bilinear elevation at geographic points, m T.P.

        Points outside the mosaic are clamped to the edge cell; callers are
        expected to keep profiles inside the envelope (asserted by
        :func:`extract_profile`).
        """
        row = (self.lat_hi - np.asarray(lat_deg, dtype=float)) / self.dlat - 0.5
        col = (np.asarray(lon_deg, dtype=float) - self.lon_lo) / self.dlon - 0.5
        r0 = np.clip(np.floor(row).astype(int), 0, self.grid.shape[0] - 2)
        c0 = np.clip(np.floor(col).astype(int), 0, self.grid.shape[1] - 2)
        fr = np.clip(row - r0, 0.0, 1.0)
        fc = np.clip(col - c0, 0.0, 1.0)
        z00 = self.grid[r0, c0]
        z01 = self.grid[r0, c0 + 1]
        z10 = self.grid[r0 + 1, c0]
        z11 = self.grid[r0 + 1, c0 + 1]
        return (
            z00 * (1 - fr) * (1 - fc)
            + z01 * (1 - fr) * fc
            + z10 * fr * (1 - fc)
            + z11 * fr * fc
        )

    def contains(self, lat_deg: NDArray, lon_deg: NDArray) -> bool:
        """True when every point lies inside the mosaic envelope."""
        lat_lo = self.lat_hi - self.grid.shape[0] * self.dlat
        lon_hi = self.lon_lo + self.grid.shape[1] * self.dlon
        return bool(
            np.all(lat_deg >= lat_lo)
            and np.all(lat_deg <= self.lat_hi)
            and np.all(lon_deg >= self.lon_lo)
            and np.all(lon_deg <= lon_hi)
        )


def load_dem_mosaic(*, use_cache: bool = True, verbose: bool = False) -> DemMosaic:
    """Mosaic every tile in :data:`TILE_DIR`, with an npz cache.

    The cache is a pure accelerator: deleting it reproduces the identical
    mosaic from the tiles alone.
    """
    if use_cache and MOSAIC_CACHE.exists():
        with np.load(MOSAIC_CACHE) as handle:
            return DemMosaic(
                grid=handle["grid"],
                lat_hi=float(handle["lat_hi"]),
                lon_lo=float(handle["lon_lo"]),
                dlat=float(handle["dlat"]),
                dlon=float(handle["dlon"]),
                dev_date=str(handle["dev_date"]),
            )

    tiles = sorted(TILE_DIR.glob("*.xml"))
    if not tiles:
        raise FileNotFoundError(
            f"No DEM tiles under {TILE_DIR}. The GSI drop is gitignored "
            "(data/raw/) and may be absent on a fresh clone."
        )
    parsed = [(path, *parse_dem_tile(path)) for path in tiles]
    dates = {p[3] for p in parsed}
    if len(dates) != 1:
        raise ValueError(f"Tiles carry mixed devDate values: {sorted(dates)}")
    dev_date = dates.pop()
    if dev_date != DEM_DEV_DATE:
        raise ValueError(
            f"DEM devDate is {dev_date!r}, expected {DEM_DEV_DATE!r}. The "
            "study's vintage statement would be wrong; refusing to continue."
        )

    lat_lo = min(p[1][0] for p in parsed)
    lon_lo = min(p[1][1] for p in parsed)
    lat_hi = max(p[1][2] for p in parsed)
    lon_hi = max(p[1][3] for p in parsed)
    ny_tile, nx_tile = parsed[0][2].shape
    dlat = (parsed[0][1][2] - parsed[0][1][0]) / ny_tile
    dlon = (parsed[0][1][3] - parsed[0][1][1]) / nx_tile
    ny = int(round((lat_hi - lat_lo) / dlat))
    nx = int(round((lon_hi - lon_lo) / dlon))

    grid = np.full((ny, nx), DEM_NODATA, dtype=np.float64)
    for _path, (t_lat_lo, t_lon_lo, t_lat_hi, _t_lon_hi), tile, _date in parsed:
        r0 = int(round((lat_hi - t_lat_hi) / dlat))
        c0 = int(round((t_lon_lo - lon_lo) / dlon))
        grid[r0 : r0 + tile.shape[0], c0 : c0 + tile.shape[1]] = tile
    if verbose:
        n_bad = int(np.count_nonzero(grid == DEM_NODATA))
        good = grid[grid != DEM_NODATA]
        print(
            f"mosaic {ny}x{nx} from {len(tiles)} tiles, devDate {dev_date}; "
            f"nodata {n_bad} ({100 * n_bad / grid.size:.4f}%); "
            f"elev {good.min():.2f}..{good.max():.2f} m T.P."
        )

    MOSAIC_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        MOSAIC_CACHE,
        grid=grid,
        lat_hi=lat_hi,
        lon_lo=lon_lo,
        dlat=dlat,
        dlon=dlon,
        dev_date=dev_date,
    )
    return DemMosaic(grid, lat_hi, lon_lo, dlat, dlon, dev_date)


# --------------------------------------------------------------------------- #
# Levee alignment from SECTIONS.shp                                            #
# --------------------------------------------------------------------------- #
def read_polylines(
    shp_path: Path = SECTIONS_SHP, dbf_path: Path = SECTIONS_DBF
) -> dict[str, list[NDArray[np.float64]]]:
    """Read an ESRI polyline shapefile as ``{Name: [part arrays]}``.

    Parts are kept separate (they are *not* concatenated): several of
    Uemura's section polylines are multi-part, and joining the parts would
    insert spurious jump segments into the arc length. This is the only
    substantive difference from the simpler reader in
    ``scripts/build_section_table.py``, which measures whole-record lengths
    and compensates for the jumps with its ``DOUBLE_TRACED`` correction.
    """
    dbf = dbf_path.read_bytes()
    n_records = struct.unpack("<I", dbf[4:8])[0]
    header_len = struct.unpack("<H", dbf[8:10])[0]
    record_len = struct.unpack("<H", dbf[10:12])[0]
    fields: list[tuple[str, int]] = []
    offset = 32
    while dbf[offset] != 0x0D:
        fields.append(
            (
                dbf[offset : offset + 11].split(b"\x00")[0].decode("latin1"),
                dbf[offset + 16],
            )
        )
        offset += 32
    names: list[str] = []
    pos = header_len
    for _ in range(n_records):
        record = dbf[pos : pos + record_len]
        pos += record_len
        cursor = 1
        for fname, flen in fields:
            value = record[cursor : cursor + flen].decode("latin1").strip()
            cursor += flen
            if fname == "Name":
                names.append(value)

    shp = shp_path.read_bytes()
    shapes: list[list[NDArray[np.float64]]] = []
    pos = 100
    while pos < len(shp):
        _number, content_len = struct.unpack(">ii", shp[pos : pos + 8])
        record = shp[pos + 8 : pos + 8 + content_len * 2]
        pos += 8 + content_len * 2
        n_parts, n_points = struct.unpack("<ii", record[36:44])
        part_starts = struct.unpack(f"<{n_parts}i", record[44 : 44 + 4 * n_parts])
        body = 44 + 4 * n_parts
        points = np.frombuffer(
            record[body : body + 16 * n_points], dtype="<f8"
        ).reshape(n_points, 2)
        bounds = list(part_starts) + [n_points]
        shapes.append([points[bounds[i] : bounds[i + 1]] for i in range(n_parts)])
    return dict(zip(names, shapes))


#: The Tokachi right-bank levee alignment as an ordered chain of
#: ``(SECTIONS.shp Name, part index)``, running upstream (increasing KP).
#: Verified contiguous: consecutive parts share an endpoint to < 1 m.
ALIGNMENT_CHAIN: tuple[tuple[str, int], ...] = (
    ("KP58.0", 0),
    ("KP59.6", 1),
    ("KP59.6", 0),
    ("KP61.4", 1),
    ("KP61.4", 0),
    ("KP62.4", 0),
)

#: Arc-length -> KP control points. Each chain part is one of Uemura's section
#: polylines, and ADR-0043 reconstructed the KP node range each section covers
#: (``scripts/build_section_table.py`` ``TABLE``); a section spanning nodes
#: ``kp_from..kp_to`` covers levee from ``kp_from - 0.1`` to ``kp_to + 0.1``.
#: The arc lengths are asserted against these spans at build time.
KP_CONTROL: tuple[tuple[str, float, float], ...] = (
    ("KP58.0", 57.3, 58.9),
    ("KP59.6", 58.9, 60.5),
    ("KP61.4", 60.5, 61.9),
    ("KP62.4", 61.9, 62.9),
)
#: Tolerance on (polyline arc length) vs (KP span x 1000 m). The levee is not
#: the river centreline the KP is measured along, so a percent-level mismatch
#: is expected; ADR-0043 used 0.3 km on the same evidence.
KP_SPAN_TOL_M = 200.0


@dataclass(frozen=True)
class Alignment:
    """Chained levee-crest alignment with an arc-length -> KP map."""

    vertices: NDArray[np.float64]
    arc_length_m: NDArray[np.float64]
    control_s_m: NDArray[np.float64]
    control_kp: NDArray[np.float64]

    def kp_to_s(self, kp: float) -> float:
        """Arc length [m] of a river chainage, by piecewise-linear control."""
        return float(np.interp(kp, self.control_kp, self.control_s_m))

    def s_to_kp(self, s_m: NDArray[np.float64] | float) -> NDArray[np.float64]:
        """River chainage of an arc length [m]."""
        return np.interp(s_m, self.control_s_m, self.control_kp)

    def point_and_tangent(
        self, s_m: float, *, tangent_half_m: float = 60.0
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Alignment point and unit tangent at arc length ``s_m``.

        The tangent is a secant over ``+/-tangent_half_m`` rather than a local
        vertex difference: the polyline vertices are irregularly spaced (2 m
        to 300 m) and a vertex-local tangent would swing by tens of degrees
        between neighbouring stations.
        """
        x = np.interp(s_m, self.arc_length_m, self.vertices[:, 0])
        y = np.interp(s_m, self.arc_length_m, self.vertices[:, 1])
        xa = np.interp(s_m - tangent_half_m, self.arc_length_m, self.vertices[:, 0])
        ya = np.interp(s_m - tangent_half_m, self.arc_length_m, self.vertices[:, 1])
        xb = np.interp(s_m + tangent_half_m, self.arc_length_m, self.vertices[:, 0])
        yb = np.interp(s_m + tangent_half_m, self.arc_length_m, self.vertices[:, 1])
        tangent = np.array([xb - xa, yb - ya], dtype=float)
        return np.array([x, y]), tangent / float(np.hypot(*tangent))


def build_alignment(
    polylines: dict[str, list[NDArray[np.float64]]] | None = None,
) -> Alignment:
    """Chain :data:`ALIGNMENT_CHAIN` into one alignment and anchor its KP.

    Raises
    ------
    ValueError
        If consecutive chain parts do not share an endpoint, or if any
        polyline's arc length disagrees with its ADR-0043 KP span by more
        than :data:`KP_SPAN_TOL_M`.
    """
    if polylines is None:
        polylines = read_polylines()

    vertices: list[NDArray[np.float64]] = []
    part_lengths: dict[str, float] = {}
    for name, index in ALIGNMENT_CHAIN:
        part = polylines[name][index]
        part_lengths[name] = part_lengths.get(name, 0.0) + float(
            np.sum(np.hypot(*np.diff(part, axis=0).T))
        )
        if vertices:
            gap = float(np.hypot(*(part[0] - vertices[-1])))
            if gap > 1.0:
                raise ValueError(
                    f"Alignment chain breaks at {name}[{index}]: {gap:.1f} m gap."
                )
            part = part[1:]
        vertices.extend(part)

    verts = np.asarray(vertices, dtype=float)
    seg = np.hypot(*np.diff(verts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])

    control_s = [0.0]
    control_kp = [KP_CONTROL[0][1]]
    running = 0.0
    for name, kp_from, kp_to in KP_CONTROL:
        span_m = (kp_to - kp_from) * 1000.0
        measured = part_lengths[name]
        if abs(measured - span_m) > KP_SPAN_TOL_M:
            raise ValueError(
                f"{name}: polyline arc length {measured:.0f} m disagrees with the "
                f"ADR-0043 KP span {span_m:.0f} m by more than {KP_SPAN_TOL_M:.0f} m."
            )
        running += measured
        control_s.append(running)
        control_kp.append(kp_to)
    return Alignment(verts, arc, np.asarray(control_s), np.asarray(control_kp))


# --------------------------------------------------------------------------- #
# Profile extraction and toe picking                                           #
# --------------------------------------------------------------------------- #
#: Profile sampling: 1 m posts from 700 m riverward to 400 m landward of the
#: alignment. The riverward reach must clear the low-water channel (the
#: 高水敷幅 by-product); the landward reach must clear 100 m beyond the
#: landside toe by a wide margin (task step 1).
PROFILE_HALF_RIVER_M = 700.0
PROFILE_HALF_LAND_M = 400.0
PROFILE_SPACING_M = 1.0

#: Toe-picking rule constants (see :func:`pick_cross_section`).
CREST_SEARCH_M = 40.0
CREST_BAND_DROP_M = 0.5
SLOPE_WINDOW_M = 5.0
SLOPE_THRESHOLD_DEFAULT = 0.10
SLOPE_THRESHOLD_LADDER: tuple[float, ...] = (0.05, 0.075, 0.10, 0.15, 0.20)
TOE_PERSISTENCE_M = 8.0
TOE_MIN_DROP_M = 1.5
#: 高水敷幅 by-product: the low-water channel shoulder is the first sustained
#: drop of this much below the riverside terrace level.
CHANNEL_DROP_M = 1.5
CHANNEL_PERSISTENCE_M = 20.0
TERRACE_WINDOW_M = 50.0


@dataclass(frozen=True)
class Profile:
    """One sampled cross-section profile.

    Attributes
    ----------
    kp
        River chainage [km].
    offsets_m
        Signed distance along the profile line; **negative is riverside**.
    elevation_m
        Bilinear DEM elevation, m T.P.
    azimuth_deg
        Azimuth of the increasing-offset (landward) direction, degrees from
        north, clockwise.
    origin_xy
        Alignment point in EPSG:2455 metres.
    tangent_azimuth_deg
        Azimuth of the levee alignment tangent at this station.
    """

    kp: float
    offsets_m: NDArray[np.float64]
    elevation_m: NDArray[np.float64]
    azimuth_deg: float
    origin_xy: NDArray[np.float64]
    tangent_azimuth_deg: float
    latitude_deg: NDArray[np.float64] = field(repr=False, default=None)  # type: ignore[assignment]
    longitude_deg: NDArray[np.float64] = field(repr=False, default=None)  # type: ignore[assignment]


def extract_profile(
    mosaic: DemMosaic,
    alignment: Alignment,
    kp: float,
    *,
    azimuth_deg: float | None = None,
    half_river_m: float = PROFILE_HALF_RIVER_M,
    half_land_m: float = PROFILE_HALF_LAND_M,
    spacing_m: float = PROFILE_SPACING_M,
) -> Profile:
    """Sample the DEM along a profile line at chainage ``kp``.

    Parameters
    ----------
    azimuth_deg
        Azimuth of the landward direction. ``None`` (default) uses the true
        perpendicular to the local alignment tangent, with the riverside
        side identified from the terrain (the side carrying the lower
        far-field ground).

    Returns
    -------
    Profile
        Offsets are signed with **negative riverside**, so the returned
        profile is orientation-normalised regardless of which way the
        alignment happens to be digitised.
    """
    origin, tangent = alignment.point_and_tangent(alignment.kp_to_s(kp))
    tangent_az = float(np.degrees(np.arctan2(tangent[0], tangent[1])) % 360.0)
    if azimuth_deg is None:
        normal = np.array([-tangent[1], tangent[0]], dtype=float)
    else:
        rad = np.deg2rad(azimuth_deg)
        normal = np.array([np.sin(rad), np.cos(rad)], dtype=float)

    # Orientation: the riverside carries the lower far-field ground.
    probe = np.arange(150.0, 800.0, 10.0)
    sides = {}
    for sign in (-1.0, 1.0):
        xy = origin[None, :] + (sign * probe)[:, None] * normal[None, :]
        lat, lon = plane_to_geographic(xy[:, 0], xy[:, 1])
        sides[sign] = float(np.percentile(mosaic.sample(lat, lon), 5.0))
    if sides[1.0] < sides[-1.0]:
        normal = -normal

    offsets = np.arange(-half_river_m, half_land_m + 1e-9, spacing_m)
    xy = origin[None, :] + offsets[:, None] * normal[None, :]
    lat, lon = plane_to_geographic(xy[:, 0], xy[:, 1])
    if not mosaic.contains(lat, lon):
        raise ValueError(f"KP {kp}: profile leaves the DEM mosaic envelope.")
    elevation = mosaic.sample(lat, lon)
    if np.any(elevation == DEM_NODATA):
        raise ValueError(f"KP {kp}: profile crosses DEM nodata.")
    azimuth = float(np.degrees(np.arctan2(normal[0], normal[1])) % 360.0)
    return Profile(
        kp=kp,
        offsets_m=offsets,
        elevation_m=elevation,
        azimuth_deg=azimuth,
        origin_xy=origin,
        tangent_azimuth_deg=tangent_az,
        latitude_deg=lat,
        longitude_deg=lon,
    )


#: Landside far-field reference window, measured from the alignment (not from
#: a toe, so the reference cannot move with the pick). The window starts well
#: beyond any plausible levee footprint and is reduced by a percentile rather
#: than a median so that a berm or bench still inside it cannot drag the
#: reference upward.
GROUND_WINDOW_M = (60.0, 350.0)
GROUND_PERCENTILE = 40.0
#: An outer toe is declared where the profile first falls within this much of
#: the landside far-field ground level and stays there.
GROUND_TOLERANCE_M = 0.5
#: How far beyond the embankment toe the outer-toe walk may look for the
#: return to landside ground. A landside seepage berm on a levee of this size
#: is at most a few tens of metres wide; if the profile has not come back to
#: ground within this distance the feature is not a berm of this levee (it is
#: raised landside terrain, a road, a bridge ramp, a sluice apron), and the
#: pick falls back to the embankment toe with ``outer_toe_capped`` set.
OUTER_TOE_MAX_BEYOND_M = 40.0
#: Landside-structure screen: a separate embankment standing at least
#: STRUCTURE_HEIGHT_M above the landside ground reference, beginning at least
#: STRUCTURE_STANDOFF_M beyond the outer toe and within STRUCTURE_SEARCH_M.
STRUCTURE_STANDOFF_M = 10.0
STRUCTURE_SEARCH_M = 150.0
STRUCTURE_HEIGHT_M = 1.5


@dataclass(frozen=True)
class CrossSection:
    """Crest/toe geometry picked from one profile.

    Two landside toe conventions are carried, because they disagree exactly
    where the vintage question bites:

    ``seepage_length_m`` (**primary**)
        Riverside toe to the **outer** landside toe -- the outermost point of
        the embankment complex, berm included. This is the under-levee
        confined path the physics wants: a landside berm is fill resting on
        the same blanket, so it lengthens the confined path, and it is the
        convention the 1998 OYO chains use (provenance §3.1 records KP 62.0
        as "toe-to-toe **incl. landside berm**").
    ``seepage_length_embankment_m``
        Riverside toe to the **first** sustained flat. Identical to the
        primary wherever there is no berm or bench; shorter where there is.

    Both exclude the foreshore by construction.
    """

    kp: float
    crest_elev_m: float
    crest_width_m: float
    crest_river_offset_m: float
    crest_land_offset_m: float
    river_toe_offset_m: float
    river_toe_elev_m: float
    land_toe_offset_m: float
    land_toe_elev_m: float
    land_outer_toe_offset_m: float
    land_outer_toe_elev_m: float
    seepage_length_m: float
    seepage_length_embankment_m: float
    land_ground_elev_m: float
    river_terrace_elev_m: float
    high_water_bed_width_m: float
    landside_bench_present: bool
    landside_structure_present: bool
    outer_toe_capped: bool
    slope_threshold: float


def _outward_slope(
    offsets: NDArray[np.float64], elevation: NDArray[np.float64], window_m: float
) -> NDArray[np.float64]:
    """Forward difference of elevation per metre of increasing offset."""
    step = int(round(window_m / float(offsets[1] - offsets[0])))
    slope = np.full(offsets.size, np.nan)
    slope[:-step] = (elevation[step:] - elevation[:-step]) / window_m
    return slope


def pick_cross_section(
    profile: Profile,
    *,
    slope_threshold: float = SLOPE_THRESHOLD_DEFAULT,
    crest_search_m: float = CREST_SEARCH_M,
    persistence_m: float = TOE_PERSISTENCE_M,
    min_drop_m: float = TOE_MIN_DROP_M,
) -> CrossSection:
    """Pick crest and both toes by an explicit, reproducible slope-break rule.

    The rule, stated in full so it can be audited and its sensitivity
    measured:

    1. **Crest.** The maximum elevation within ``+/-crest_search_m`` of the
       alignment point. The *crest band* is the contiguous run of offsets
       around it lying within :data:`CREST_BAND_DROP_M` of that maximum; its
       extent is the reported crest width.
    2. **Toes.** From each crest-band edge, walk outward. Let
       ``slope(x)`` be the elevation difference over the next
       :data:`SLOPE_WINDOW_M` metres of *outward* travel, per metre. The toe
       is the first offset ``x`` that is at least ``min_drop_m`` below the
       crest and for which ``slope >= -slope_threshold`` holds over the whole
       of ``[x, x + persistence_m]`` -- i.e. the first place the embankment
       face stops descending and stays stopped.
    3. **Outer landside toe.** The first offset beyond the crest at which the
       profile has descended to within :data:`GROUND_TOLERANCE_M` of the
       landside far-field ground, the latter taken as the median over
       :data:`GROUND_WINDOW_M` measured from the alignment (so the reference
       cannot move with the pick). Where there is no berm this is the same
       point as (2).
    4. **L** is the horizontal riverside-toe to landside-toe distance, crest
       width included, reported under both landside conventions.

    Reporting both conventions is deliberate. Step (2) alone stops on a
    landside berm, which is exactly the KP 57.4 ``berm-only`` case the
    1998-vs-2025 vintage gap turns on; step (3) walks to the outer toe of the
    embankment complex, which is the confined path the physics wants and the
    convention the 1998 OYO chains used. A ``landside_bench_present`` flag
    marks where the two can differ.

    Notes
    -----
    ``slope_threshold`` is the one discretionary constant; the caller is
    expected to sweep :data:`SLOPE_THRESHOLD_LADDER` and report the spread
    rather than quoting a single pick.
    """
    offsets = profile.offsets_m
    elevation = profile.elevation_m
    step = float(offsets[1] - offsets[0])

    near = np.abs(offsets) <= crest_search_m
    crest_elev = float(elevation[near].max())
    peak_index = int(np.flatnonzero(near)[int(np.argmax(elevation[near]))])

    band = elevation >= crest_elev - CREST_BAND_DROP_M
    lo = peak_index
    while lo > 0 and band[lo - 1]:
        lo -= 1
    hi = peak_index
    while hi < offsets.size - 1 and band[hi + 1]:
        hi += 1

    slope = _outward_slope(offsets, elevation, SLOPE_WINDOW_M)
    n_persist = max(1, int(round(persistence_m / step)))
    n_window = max(1, int(round(SLOPE_WINDOW_M / step)))

    def _walk(start: int, direction: int) -> int:
        """First sustained flat outward of ``start``; ``direction`` +1/-1.

        The slope is evaluated **in the direction of travel** on both sides,
        so the riverside and landside picks are mirror images of each other.
        Using one signed forward-difference array for both would evaluate the
        riverside face over a window on the wrong side of the probe and push
        that toe several metres too far out.
        """
        index = start
        while True:
            index += direction
            probe = index + direction * (n_persist - 1 + n_window)
            if probe <= 0 or probe >= offsets.size:
                raise ValueError(
                    f"KP {profile.kp}: no toe found before the profile end "
                    f"(direction {direction:+d}, threshold {slope_threshold})."
                )
            if crest_elev - elevation[index] < min_drop_m:
                continue
            probes = index + direction * np.arange(n_persist)
            outward = (
                elevation[probes + direction * n_window] - elevation[probes]
            ) / SLOPE_WINDOW_M
            if np.all(outward >= -slope_threshold):
                return index

    river_index = _walk(lo, -1)
    land_index = _walk(hi, +1)

    land_far = (offsets >= GROUND_WINDOW_M[0]) & (offsets <= GROUND_WINDOW_M[1])
    ground_elev = float(np.percentile(elevation[land_far], GROUND_PERCENTILE))

    # Outer landside toe: the landside boundary of the connected above-ground
    # region containing the crest, i.e. the first offset beyond the crest at
    # which the profile has come down to the landside far-field ground and
    # stays there. Where there is no berm this coincides with the embankment
    # toe; where there is one it walks past it.
    at_ground = elevation <= ground_elev + GROUND_TOLERANCE_M
    outer_index = None
    for index in range(land_index, offsets.size - n_persist):
        if offsets[index] - offsets[land_index] > OUTER_TOE_MAX_BEYOND_M:
            break
        if np.all(at_ground[index : index + n_persist]):
            outer_index = index
            break
    outer_capped = outer_index is None
    if outer_capped:
        outer_index = land_index

    river_terrace = (offsets <= offsets[river_index]) & (
        offsets >= offsets[river_index] - TERRACE_WINDOW_M
    )
    terrace_elev = float(np.median(elevation[river_terrace]))

    # 高水敷幅 by-product: riverside toe -> low-water channel shoulder break.
    n_channel = max(1, int(round(CHANNEL_PERSISTENCE_M / step)))
    below = elevation < terrace_elev - CHANNEL_DROP_M
    channel_index = None
    for index in range(river_index, n_channel, -1):
        if np.all(below[index - n_channel : index]):
            channel_index = index
            break
    bed_width = (
        float(offsets[river_index] - offsets[channel_index])
        if channel_index is not None
        else float("nan")
    )

    # Bench flag: a >=5 m run of near-level ground within 60 m beyond the
    # landside toe and at least 0.3 m above it (a berm or terrace step).
    beyond = (offsets > offsets[land_index]) & (offsets <= offsets[land_index] + 60.0)
    bench = bool(
        np.count_nonzero(
            beyond & (elevation >= elevation[land_index] + 0.3) & (np.abs(slope) < 0.05)
        )
        * step
        >= 5.0
    )

    # Landside-structure flag: a *separate* embankment (road, second-line
    # levee, ramp) standing clear of the ground within reach of the toe. Where
    # this fires, the levee footprint is not cleanly separable from adjacent
    # fill and the picked L must be read as contaminated, not as a survey.
    outer_field = (offsets > offsets[outer_index] + STRUCTURE_STANDOFF_M) & (
        offsets <= offsets[outer_index] + STRUCTURE_SEARCH_M
    )
    structure = bool(np.any(elevation[outer_field] > ground_elev + STRUCTURE_HEIGHT_M))

    return CrossSection(
        kp=profile.kp,
        crest_elev_m=crest_elev,
        crest_width_m=float(offsets[hi] - offsets[lo]),
        crest_river_offset_m=float(offsets[lo]),
        crest_land_offset_m=float(offsets[hi]),
        river_toe_offset_m=float(offsets[river_index]),
        river_toe_elev_m=float(elevation[river_index]),
        land_toe_offset_m=float(offsets[land_index]),
        land_toe_elev_m=float(elevation[land_index]),
        land_outer_toe_offset_m=float(offsets[outer_index]),
        land_outer_toe_elev_m=float(elevation[outer_index]),
        seepage_length_m=float(offsets[outer_index] - offsets[river_index]),
        seepage_length_embankment_m=float(offsets[land_index] - offsets[river_index]),
        land_ground_elev_m=ground_elev,
        river_terrace_elev_m=terrace_elev,
        high_water_bed_width_m=bed_width,
        landside_bench_present=bench,
        landside_structure_present=structure,
        outer_toe_capped=outer_capped,
        slope_threshold=slope_threshold,
    )


# --------------------------------------------------------------------------- #
# Section registry                                                             #
# --------------------------------------------------------------------------- #
#: The four confined production sections. ``config``/``production`` follow the
#: ``scripts/foreshore_width_study.py`` registry; ``z_toe_m`` is the ADR-0021
#: surveyed landside toe (+/-0.3 m), used as an independent extraction check.
SECTIONS: dict[str, dict[str, Any]] = {
    "KP57.4": {
        "kp": 57.4,
        "config": "configs/kp57_4_historical_matrix.yaml",
        "production": "results/tokachi_kp57.4_historical_matrix.h5",
        "z_toe_m": 38.3,
        "oyo_chain": "11.09 + 7.50 + 2.82 + 4.50 + 7.01 = 32.92 m (Form 5 chain)",
        "high_water_bed_width_1998_m": 200.0,
    },
    "KP58.8": {
        "kp": 58.8,
        "config": "configs/kp58_8_historical_matrix.yaml",
        "production": "results/tokachi_kp58.8_historical_matrix.h5",
        "z_toe_m": 38.5,
        "oyo_chain": "Form 5 model span / Form 7 base, 31 to 40 m, adopt 35",
        "high_water_bed_width_1998_m": 325.0,
    },
    "KP60.0": {
        "kp": 60.0,
        "config": "configs/kp60_0_historical_matrix.yaml",
        "production": "results/tokachi_kp60.0_historical_matrix.h5",
        "z_toe_m": 40.0,
        "oyo_chain": "10.0 + 9.5 + 4.0 + 2.5 + 8.8 = 34.8 m (Form 6 footprint)",
        "high_water_bed_width_1998_m": 600.0,
    },
    "KP62.0": {
        "kp": 62.0,
        "config": "configs/kp62_0_historical_matrix.yaml",
        "production": "results/tokachi_kp62.0_historical_matrix.h5",
        "z_toe_m": 44.9,
        "oyo_chain": "toe-to-toe incl. landside berm, 18 + 29.1; range 40 to 55",
        "high_water_bed_width_1998_m": 44.0,
        # ADR-0047 (2026-07-29): the DEM value was ADOPTED here, so the CSV now
        # carries 40.0 and the study's own arm would be a no-op. The withdrawn
        # 1998 value is kept as a labelled arm so the comparison that motivated
        # adoption stays reproducible from the new baseline, in the opposite
        # direction. The 47.0 m credited a landside berm that the 1998 OYO
        # 様式-5 sheet did not model, that the `unreinforced` classification
        # denies, and that 28 of 28 clean stations do not show.
        "withdrawn_L_m": 47.0,
        "adopted_by": "ADR-0047 (2026-07-29)",
    },
}

#: Chainage window over which each section is re-measured. The KP anchor is
#: reproducible but not exact (the levee is not the river centreline the KP is
#: measured along); cross-correlating the DEM crest, landside ground and
#: riverside terrace against the 2019 and Uemura longitudinals localises it to
#: roughly +/-150 m. Scanning +/-300 m therefore brackets the anchor
#: uncertainty *and* delivers the along-levee spread of L, which is the
#: empirical CoV(L) the seepage-length-L study had no data for.
WINDOW_HALF_M = 300.0
WINDOW_STEP_M = 20.0
#: Clean-station screen. A station is rejected when its crest stands more than
#: this far from the *window's own median* crest excess over the 2019 design
#: bank height. Anchoring to the window median rather than to the design
#: profile itself matters: an as-built crest is routinely a few tenths above
#: design along a whole reach (the measured reach mean is +0.30 m), and that
#: uniform over-build is not contamination. What this catches is a *local*
#: departure -- fill sitting on the levee, such as a road or a bridge approach
#: ramp -- which the landside-structure screen cannot see because there is no
#: gap between the two.
CREST_DESIGN_TOLERANCE_M = 0.5
#: Azimuth scan for the perpendicularity check.
AZIMUTH_SCAN_DEG = 30.0
AZIMUTH_STEP_DEG = 2.0


def read_csv_inputs() -> dict[float, dict[str, Any]]:
    """The committed geotechnical CSV, keyed by KP (read-only)."""
    rows: dict[float, dict[str, Any]] = {}
    lines = INPUTS_CSV.read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split(",")
    for line in lines[1:]:
        record = dict(zip(header, line.split(",")))
        rows[float(record["kp"])] = {
            "L_m": float(record["L_m"]),
            "foreshore_width_m": float(record["foreshore_width_m"]),
            "remediation_state": record["remediation_state"],
        }
    return rows


def _read_longitudinal(
    path: Path, columns: tuple[str, ...], river: str
) -> dict[str, NDArray[np.float64]]:
    """KP-indexed columns from a committed longitudinal CSV."""
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split(",")
    collected: dict[str, list[float]] = {name: [] for name in ("kp", *columns)}
    for line in lines[1:]:
        record = dict(zip(header, line.split(",")))
        if record.get("River", record.get("river")) != river:
            continue
        if any(not record.get(name) for name in columns):
            continue
        collected["kp"].append(float(record.get("KP") or record["kp"]))
        for name in columns:
            collected[name].append(float(record[name]))
    return {key: np.asarray(value, dtype=float) for key, value in collected.items()}


# --------------------------------------------------------------------------- #
# Stage: datum                                                                 #
# --------------------------------------------------------------------------- #
#: Hard-constraint-5 gate. A systematic offset larger than this between the DEM
#: surface and the repo's own m T.P. elevations would mean the vertical datums
#: disagree, and every length measured under it would be untrustworthy.
DATUM_TOLERANCE_M = 1.0


def _oriented_normal(
    mosaic: DemMosaic, origin: NDArray[np.float64], tangent: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Unit normal pointing landward (the side with the higher far-field ground)."""
    normal = np.array([-tangent[1], tangent[0]], dtype=float)
    probe = np.arange(150.0, 800.0, 10.0)
    low: dict[float, float] = {}
    for sign in (-1.0, 1.0):
        xy = origin[None, :] + (sign * probe)[:, None] * normal[None, :]
        lat, lon = plane_to_geographic(xy[:, 0], xy[:, 1])
        low[sign] = float(np.percentile(mosaic.sample(lat, lon), 5.0))
    return -normal if low[1.0] < low[-1.0] else normal


def run_datum_check(
    mosaic: DemMosaic, alignment: Alignment, *, verbose: bool = True
) -> dict[str, Any]:
    """Verify the DEM's vertical datum against three independent repo series.

    Compares, at 10 m chainage spacing along the whole alignment:

    * DEM crest against ``DesignBankHeight_R`` of the 2019 bank-height CSV;
    * DEM landside ground (median 60-160 m landward) against Uemura's
      ``ground_m_msl``;
    * DEM riverside terrace (median 60-160 m riverward) against Uemura's
      ``floodplain_m_msl``.

    Returns
    -------
    dict
        Per-comparison mean/median/sd/percentile offsets and a ``passed`` flag.

    Raises
    ------
    ValueError
        If any mean offset exceeds :data:`DATUM_TOLERANCE_M`. GSI 標高 is
        orthometric height on T.P. and the repo's elevations are m T.P./MSL,
        so they must agree; a failure here would silently corrupt every
        downstream length, which is why this is a hard gate and not a warning.
    """
    stations = np.arange(0.0, float(alignment.arc_length_m[-1]), 10.0)
    crest = np.empty(stations.size)
    land = np.empty(stations.size)
    river = np.empty(stations.size)
    for index, s_m in enumerate(stations):
        origin, tangent = alignment.point_and_tangent(float(s_m))
        normal = _oriented_normal(mosaic, origin, tangent)
        for offsets, target in (
            (np.arange(-40.0, 40.1, 1.0), "crest"),
            (np.arange(60.0, 160.1, 2.0), "land"),
            (-np.arange(60.0, 160.1, 2.0), "river"),
        ):
            xy = origin[None, :] + offsets[:, None] * normal[None, :]
            lat, lon = plane_to_geographic(xy[:, 0], xy[:, 1])
            values = mosaic.sample(lat, lon)
            if target == "crest":
                crest[index] = values.max()
            elif target == "land":
                land[index] = float(np.median(values))
            else:
                river[index] = float(np.median(values))

    kp = alignment.s_to_kp(stations)
    bank = _read_longitudinal(BANK_HEIGHT_CSV, ("DesignBankHeight_R",), "Tokachi")
    uemura = _read_longitudinal(
        UEMURA_LONGITUDINAL, ("ground_m_msl", "floodplain_m_msl"), "Tokachi"
    )
    series = {
        "crest_vs_2019_design_bank_height": crest
        - np.interp(kp, bank["kp"], bank["DesignBankHeight_R"]),
        "landside_ground_vs_uemura_ground": land
        - np.interp(kp, uemura["kp"], uemura["ground_m_msl"]),
        "riverside_terrace_vs_uemura_floodplain": river
        - np.interp(kp, uemura["kp"], uemura["floodplain_m_msl"]),
    }

    record: dict[str, Any] = {
        "tolerance_m": DATUM_TOLERANCE_M,
        "n_stations": int(stations.size),
        "kp_range": [float(kp.min()), float(kp.max())],
        "comparisons": {},
        "passed": True,
    }
    for name, residual in series.items():
        entry = {
            "mean_offset_m": float(residual.mean()),
            "median_offset_m": float(np.median(residual)),
            "sd_m": float(residual.std(ddof=1)),
            "p05_m": float(np.percentile(residual, 5)),
            "p95_m": float(np.percentile(residual, 95)),
        }
        entry["passed"] = bool(abs(entry["mean_offset_m"]) <= DATUM_TOLERANCE_M)
        record["comparisons"][name] = entry
        record["passed"] = bool(record["passed"] and entry["passed"])
        if verbose:
            print(
                f"  {name:<42} mean {entry['mean_offset_m']:+.2f} m  "
                f"sd {entry['sd_m']:.2f}  {'PASS' if entry['passed'] else 'FAIL'}"
            )
    if not record["passed"]:
        raise ValueError(
            "DATUM CHECK FAILED: the DEM surface and the repo's m T.P. "
            f"elevations disagree by more than {DATUM_TOLERANCE_M} m. "
            "Refusing to measure lengths against a datum that would silently "
            "corrupt everything downstream."
        )
    return record


# --------------------------------------------------------------------------- #
# Stage: profiles                                                              #
# --------------------------------------------------------------------------- #
def azimuth_scan(
    mosaic: DemMosaic, alignment: Alignment, kp: float
) -> dict[str, float]:
    """Check that the alignment perpendicular really minimises the picked L.

    A profile off-perpendicular by an angle ``theta`` inflates a toe-to-toe
    length by ``1 / cos(theta)`` -- already +6 % at 20 deg -- which would
    masquerade as a real widening. Scanning the azimuth and reporting where
    ``L`` is minimised is the direct test: the minimiser *is* the true
    perpendicular, so its offset from the adopted alignment normal measures
    the residual obliquity actually carried by the reported value.
    """
    base = extract_profile(mosaic, alignment, kp)
    deltas = np.arange(-AZIMUTH_SCAN_DEG, AZIMUTH_SCAN_DEG + 1e-9, AZIMUTH_STEP_DEG)
    lengths: list[float] = []
    kept: list[float] = []
    for delta in deltas:
        try:
            profile = extract_profile(
                mosaic, alignment, kp, azimuth_deg=base.azimuth_deg + float(delta)
            )
            lengths.append(pick_cross_section(profile).seepage_length_m)
            kept.append(float(delta))
        except ValueError:
            continue
    array = np.asarray(lengths)
    best = int(np.argmin(array))
    adopted = int(np.argmin(np.abs(np.asarray(kept))))
    return {
        "adopted_azimuth_deg": base.azimuth_deg,
        "alignment_tangent_azimuth_deg": base.tangent_azimuth_deg,
        "L_at_adopted_azimuth_m": float(array[adopted]),
        "minimising_azimuth_offset_deg": kept[best],
        "L_at_minimising_azimuth_m": float(array[best]),
        "obliquity_inflation_factor": float(
            1.0 / np.cos(np.deg2rad(kept[best])) if kept[best] else 1.0
        ),
    }


def scan_window(
    mosaic: DemMosaic, alignment: Alignment, kp: float
) -> tuple[list[CrossSection], list[float]]:
    """Pick the cross-section at every station of the chainage window."""
    s0 = alignment.kp_to_s(kp)
    picks: list[CrossSection] = []
    offsets: list[float] = []
    for delta in np.arange(-WINDOW_HALF_M, WINDOW_HALF_M + 1e-9, WINDOW_STEP_M):
        station_kp = float(alignment.s_to_kp(s0 + float(delta)))
        try:
            picks.append(
                pick_cross_section(extract_profile(mosaic, alignment, station_kp))
            )
            offsets.append(float(delta))
        except ValueError:
            continue
    return picks, offsets


def write_profile_csv(profile: Profile, path: Path) -> None:
    """Persist one sampled profile so later steps need not re-parse the tiles."""
    path.parent.mkdir(parents=True, exist_ok=True)
    east, north = geographic_to_plane(profile.latitude_deg, profile.longitude_deg)
    header = (
        f"# GSI DEM5A mesh 644331, devDate {DEM_DEV_DATE}; KP {profile.kp:.3f}\n"
        f"# profile azimuth {profile.azimuth_deg:.2f} deg (landward positive); "
        f"alignment tangent {profile.tangent_azimuth_deg:.2f} deg\n"
        "# offsets negative = riverside; easting/northing EPSG:2455; "
        "elevations m T.P.\n"
        "offset_m,easting_m,northing_m,lat_deg,lon_deg,elev_m_tp\n"
    )
    rows = "".join(
        f"{o:.1f},{e:.3f},{n:.3f},{la:.8f},{lo:.8f},{z:.2f}\n"
        for o, e, n, la, lo, z in zip(
            profile.offsets_m,
            east,
            north,
            profile.latitude_deg,
            profile.longitude_deg,
            profile.elevation_m,
        )
    )
    path.write_text(header + rows, encoding="utf-8")


def read_profile_csv(path: Path) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Read back a profile CSV as ``(offsets_m, elevation_m)``.

    Hand-rolled rather than ``np.genfromtxt(names=True)``: the file carries
    ``#`` provenance lines *above* its column-name row, a combination that
    confuses genfromtxt's comment stripping.
    """
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    header = lines[0].split(",")
    offset_col = header.index("offset_m")
    elev_col = header.index("elev_m_tp")
    rows = np.array([[float(c) for c in line.split(",")] for line in lines[1:]])
    return rows[:, offset_col], rows[:, elev_col]


def measure_section(
    mosaic: DemMosaic, alignment: Alignment, label: str, *, verbose: bool = True
) -> dict[str, Any]:
    """Measure one section: nominal pick, threshold ladder, window, azimuth."""
    spec = SECTIONS[label]
    kp = float(spec["kp"])
    csv_rows = read_csv_inputs()

    profile = extract_profile(mosaic, alignment, kp)
    stem = f"kp{kp:.1f}".replace(".", "_")
    write_profile_csv(profile, PROFILE_DIR / f"{stem}_profile.csv")
    nominal = pick_cross_section(profile)

    ladder = {
        f"{threshold:g}": pick_cross_section(
            profile, slope_threshold=threshold
        ).seepage_length_m
        for threshold in SLOPE_THRESHOLD_LADDER
    }
    picks, offsets = scan_window(mosaic, alignment, kp)
    lengths = np.array([p.seepage_length_m for p in picks])
    embankment = np.array([p.seepage_length_embankment_m for p in picks])
    flagged = np.array([p.landside_structure_present for p in picks])

    # Uniform "clean station" screen, applied identically at every section:
    # a station counts only if (a) no separate landside embankment stands
    # near its toe, and (b) its crest is within CREST_DESIGN_TOLERANCE_M of
    # the 2019 design crest. (b) catches fill sitting *on* the levee -- a road
    # or a bridge approach ramp fused with the crest -- which (a) cannot see
    # because there is no gap between the two. Neither screen is tuned to a
    # section: both compare against independent committed data.
    bank = _read_longitudinal(BANK_HEIGHT_CSV, ("DesignBankHeight_R",), "Tokachi")
    station_kp = np.array([p.kp for p in picks])
    crest_excess = np.array([p.crest_elev_m for p in picks]) - np.interp(
        station_kp, bank["kp"], bank["DesignBankHeight_R"]
    )
    raised = np.abs(crest_excess - np.median(crest_excess)) > CREST_DESIGN_TOLERANCE_M
    clean_mask = ~flagged & ~raised
    clean = lengths[clean_mask]

    record: dict[str, Any] = {
        "section": label,
        "kp": kp,
        "csv_L_m": csv_rows[kp]["L_m"],
        "csv_geometry_vintage": CSV_GEOMETRY_VINTAGE,
        "remediation_state": csv_rows[kp]["remediation_state"],
        "oyo_1998_basis": spec["oyo_chain"],
        "dem_dev_date": mosaic.dev_date,
        "nominal_station": {
            "profile_azimuth_deg": profile.azimuth_deg,
            "alignment_tangent_azimuth_deg": profile.tangent_azimuth_deg,
            "crest_elev_m_tp": nominal.crest_elev_m,
            "crest_width_m": nominal.crest_width_m,
            "river_toe_offset_m": nominal.river_toe_offset_m,
            "river_toe_elev_m_tp": nominal.river_toe_elev_m,
            "land_toe_offset_m": nominal.land_toe_offset_m,
            "land_toe_elev_m_tp": nominal.land_toe_elev_m,
            "land_outer_toe_offset_m": nominal.land_outer_toe_offset_m,
            "land_outer_toe_elev_m_tp": nominal.land_outer_toe_elev_m,
            "L_m": nominal.seepage_length_m,
            "L_embankment_only_m": nominal.seepage_length_embankment_m,
            "high_water_bed_width_m": nominal.high_water_bed_width_m,
            "landside_bench_present": nominal.landside_bench_present,
            "landside_structure_present": nominal.landside_structure_present,
        },
        "slope_threshold_ladder_L_m": ladder,
        "slope_threshold_spread_m": float(max(ladder.values()) - min(ladder.values())),
        "window": {
            "half_width_m": WINDOW_HALF_M,
            "step_m": WINDOW_STEP_M,
            "n_stations": int(lengths.size),
            "n_structure_flagged": int(flagged.sum()),
            "L_median_m": float(np.median(lengths)),
            "L_mean_m": float(lengths.mean()),
            "L_sd_m": float(lengths.std(ddof=1)),
            "L_cov": float(lengths.std(ddof=1) / lengths.mean()),
            "L_min_m": float(lengths.min()),
            "L_max_m": float(lengths.max()),
            "L_embankment_median_m": float(np.median(embankment)),
            "n_crest_raised": int(raised.sum()),
            "n_clean": int(clean.size),
            "L_median_clean_m": (
                float(np.median(clean)) if clean.size else float("nan")
            ),
            "L_mean_clean_m": float(clean.mean()) if clean.size else float("nan"),
            "L_cov_clean": (
                float(clean.std(ddof=1) / clean.mean())
                if clean.size > 1
                else float("nan")
            ),
            "L_min_clean_m": float(clean.min()) if clean.size else float("nan"),
            "L_max_clean_m": float(clean.max()) if clean.size else float("nan"),
            "chainage_offsets_m": offsets,
            "L_by_offset_m": [float(v) for v in lengths],
            "crest_excess_over_design_by_offset_m": [float(v) for v in crest_excess],
            "structure_flag_by_offset": [bool(v) for v in flagged],
            "clean_station_by_offset": [bool(v) for v in clean_mask],
        },
        "azimuth_check": azimuth_scan(mosaic, alignment, kp),
        "cross_validation": {
            "z_toe_adr0021_m_tp": spec["z_toe_m"],
            "dem_land_outer_toe_elev_m_tp": nominal.land_outer_toe_elev_m,
            "z_toe_residual_m": nominal.land_outer_toe_elev_m - spec["z_toe_m"],
            "z_toe_within_adr0021_band": bool(
                abs(nominal.land_outer_toe_elev_m - spec["z_toe_m"]) <= 0.3
            ),
            "high_water_bed_width_1998_m": spec["high_water_bed_width_1998_m"],
            "high_water_bed_width_dem_m": nominal.high_water_bed_width_m,
        },
    }
    if verbose:
        window = record["window"]
        print(
            f"  {label}: DEM L {window['L_median_clean_m']:.0f} m (median of "
            f"{window['n_clean']}/{window['n_stations']} clean stations, CoV "
            f"{window['L_cov_clean']:.3f}, range {window['L_min_clean_m']:.0f}-"
            f"{window['L_max_clean_m']:.0f}) vs CSV {record['csv_L_m']:.1f} m; "
            f"all-station median {window['L_median_m']:.0f} m; rejected "
            f"{window['n_structure_flagged']} structure / "
            f"{window['n_crest_raised']} raised-crest"
        )
    return record


# --------------------------------------------------------------------------- #
# Stage: fragility                                                             #
# --------------------------------------------------------------------------- #
#: When the all-station median differs from the clean-station median by more
#: than this, the contaminated reading is driven as a second, labelled arm so
#: the consequence of the extraction ambiguity is measured rather than argued.
ARM_DIVERGENCE_M = 2.0

#: Plain-English rendering of each arm key, for figure text only. The keys
#: themselves are the evidence JSON's own field names and must not change; a
#: main-body thesis figure may not print them, so the display map lives here
#: rather than in the record.
ARM_DISPLAY_NAMES = {
    "dem_clean_median": "clean-station median",
    "dem_all_stations_median": "all-station median",
    "withdrawn_1998": "withdrawn 1998 value",
}

#: House chrome for a legend that has to sit over the marks: a surface plate at
#: high alpha and no edge, which is the device ``_figstyle.mark_hypothetical``
#: uses for the same problem. Not a frame; the house rcParam keeps those off.
_LEGEND_PLATE = {
    "frameon": True,
    "facecolor": figstyle.SURFACE,
    "edgecolor": "none",
    "framealpha": 0.85,
}


def fragility_arms_from_measurements(
    measurements: list[dict[str, Any]],
) -> dict[str, list[tuple[str, float]]]:
    """Map each section's measurements onto the L arms to drive.

    The primary arm is the **clean-station window median**, not the
    nominal-station pick: it is robust to the residual chainage-anchor
    uncertainty, it excludes stations where adjacent or superimposed fill
    makes the levee footprint unresolvable, and its spread is the along-levee
    variability the study reports as an empirical CoV(L). Where the
    all-station median differs materially, it is driven as a second arm so
    the ambiguity is bracketed by measurement.
    """
    arms: dict[str, list[tuple[str, float]]] = {}
    for record in measurements:
        window = record["window"]
        clean = round(float(window["L_median_clean_m"]), 1)
        entries = [("dem_clean_median", clean)]
        contaminated = round(float(window["L_median_m"]), 1)
        if abs(contaminated - clean) > ARM_DIVERGENCE_M:
            entries.append(("dem_all_stations_median", contaminated))
        # Where the DEM value has since been adopted into the CSV, the arm above
        # is a no-op against its own baseline. Drive the withdrawn value instead,
        # so the comparison that justified adoption stays reproducible.
        withdrawn = SECTIONS[record["section"]].get("withdrawn_L_m")
        if withdrawn is not None:
            entries = [
                (name, value)
                for name, value in entries
                if abs(value - record["csv_L_m"]) > 1e-9
            ]
            entries.append(("withdrawn_1998", float(withdrawn)))
        arms[record["section"]] = entries
    return arms


def _run_arm(config_path: Path, seepage_length_m: float, n_jobs: int):
    """Run one sweep with ``geometry.L`` overridden in memory.

    The YAML is loaded, the single field replaced, and the result
    re-validated through :class:`Config`; the on-disk config is never
    written to and the CSV is never touched.
    """
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["geometry"]["L"] = float(seepage_length_m)
    config = Config.model_validate(data)
    return run_fragility_analysis(config, n_jobs=n_jobs, progress=False, persist=False)


def _assert_baseline_bit_identical(result, production_path: Path, label: str) -> None:
    """Refuse to report a sensitivity if the baseline arm has drifted."""
    with h5py.File(production_path, "r") as handle:
        prod_static = np.asarray(handle["P_f_static_raw"])
        prod_trans = np.asarray(handle["P_f_trans_raw"])
    d_static = float(np.max(np.abs(result.P_f_static_raw - prod_static)))
    d_trans = float(np.max(np.abs(result.P_f_trans_raw - prod_trans)))
    if d_static != 0.0 or d_trans != 0.0:
        raise AssertionError(
            f"{label}: baseline arm is not bit-identical to the persisted "
            f"production sweep {production_path.name} (max |d| static "
            f"{d_static:.3e}, transient {d_trans:.3e}). Refusing to report a "
            "sensitivity against a drifted baseline."
        )


def study_fragility(
    label: str, arms: list[tuple[str, float]], n_jobs: int, *, verbose: bool = True
) -> dict[str, Any]:
    """Measure what the DEM L would do to one section's production fragility."""
    spec = SECTIONS[label]
    config_path = REPO_ROOT / spec["config"]
    production_path = REPO_ROOT / spec["production"]
    baseline_L = float(Config.from_yaml(config_path).geometry.L)

    started = time.time()
    baseline = _run_arm(config_path, baseline_L, n_jobs)
    _assert_baseline_bit_identical(baseline, production_path, label)
    grid = np.asarray(baseline.conditioning_grid, dtype=float)

    record: dict[str, Any] = {
        "section": label,
        "config": spec["config"],
        "production_sweep": spec["production"],
        "baseline_L_m": baseline_L,
        "baseline_bit_identical_to_production": True,
        "n_samples": int(baseline.theta_matrix.shape[0]),
        "seepage_length_cov": Config.from_yaml(config_path).seepage_length_cov,
        "arms": {},
    }
    for name, length in arms:
        arm = _run_arm(config_path, length, n_jobs)
        entry: dict[str, Any] = {"L_m": length, "delta_L_m": length - baseline_L}
        for branch in ("trans", "static"):
            baseline_pf = getattr(baseline, f"P_f_{branch}_raw")
            arm_pf = getattr(arm, f"P_f_{branch}_raw")
            delta = np.abs(arm_pf - baseline_pf)
            worst = int(delta.argmax())
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(baseline_pf > 0, arm_pf / baseline_pf, np.nan)
            entry[branch] = {
                "max_abs_delta_P_f": float(delta.max()),
                "max_abs_delta_at_stage_m_msl": float(grid[worst]),
                "P_f_baseline_at_that_stage": float(baseline_pf[worst]),
                "P_f_arm_at_that_stage": float(arm_pf[worst]),
                "min_ratio_where_baseline_positive": (
                    float(np.nanmin(ratio)) if np.any(baseline_pf > 0) else None
                ),
                "max_ratio_where_baseline_positive": (
                    float(np.nanmax(ratio)) if np.any(baseline_pf > 0) else None
                ),
            }
        record["arms"][name] = entry
        if verbose:
            print(
                f"    {label} {name} L={length:.1f} m: "
                f"max |dP_f_trans| = {entry['trans']['max_abs_delta_P_f']:.5f} at "
                f"{entry['trans']['max_abs_delta_at_stage_m_msl']:.2f} m MSL; "
                f"static {entry['static']['max_abs_delta_P_f']:.5f}",
                flush=True,
            )
    record["elapsed_s"] = round(time.time() - started, 1)
    return record


# --------------------------------------------------------------------------- #
# Stage: ratio -- does the static/transient bias claim survive the L change?    #
# --------------------------------------------------------------------------- #
#: Minimum failure count required in *every* one of the four cells
#: (CSV/DEM x static/transient) before a level's ratio is reported at all.
#: Deliberately low: at KP 62.0 a threshold of 50 would leave the ratio
#: evaluable only *above* the crest, and the claim the thesis defends lives at
#: design HWL. The bootstrap interval, not a count gate, is what decides whether
#: a level's ratio actually moved -- a sparse level simply fails to resolve.
RATIO_MIN_FAILURES = 10
#: A level is additionally marked ``well_populated`` above this count, so a
#: reader can separate "resolved on plenty of data" from "resolved on few".
RATIO_WELL_POPULATED = 50
#: Paired-bootstrap replicates for the ratio-of-ratios interval.
RATIO_BOOTSTRAP_N = 2000
RATIO_CONFIDENCE = 0.95


def _pattern_counts(
    csv_static: NDArray[np.bool_],
    csv_trans: NDArray[np.bool_],
    dem_static: NDArray[np.bool_],
    dem_trans: NDArray[np.bool_],
) -> NDArray[np.int64]:
    """Joint 16-cell contingency of the four indicators at one level.

    The four failure indicators at a given conditioning level are functions of
    the *same* realizations (the ADR-0002 shared-sample contract, and the CSV
    and DEM arms share the seed so their theta rows are the same draws). Their
    16 joint pattern counts are therefore the sufficient statistic for all four
    means under a row resample -- which is what makes the paired bootstrap in
    :func:`ratio_of_ratios_ci` exact and cheap instead of a 1e5-row gather.
    """
    code = (
        csv_static.astype(np.int64)
        + 2 * csv_trans.astype(np.int64)
        + 4 * dem_static.astype(np.int64)
        + 8 * dem_trans.astype(np.int64)
    )
    return np.bincount(code, minlength=16).astype(np.int64)


#: Which of the 16 joint patterns carry each indicator (bit order: csv_static,
#: csv_trans, dem_static, dem_trans).
_PATTERN_BITS = np.array(
    [[(k >> b) & 1 for k in range(16)] for b in range(4)], dtype=np.float64
)


def ratio_of_ratios_ci(
    counts: NDArray[np.int64],
    *,
    n_boot: int = RATIO_BOOTSTRAP_N,
    confidence: float = RATIO_CONFIDENCE,
    seed: int = 0,
) -> dict[str, float]:
    """Paired-bootstrap interval on ``(P_s/P_t)_DEM / (P_s/P_t)_CSV``.

    Parameters
    ----------
    counts
        The 16 joint pattern counts from :func:`_pattern_counts`.

    Returns
    -------
    dict
        Point estimate ``rho``, its percentile interval, and ``resolved`` --
        True only when the interval excludes 1.0, i.e. when the static-vs-
        transient bias ratio provably moved. A component whose interval covers
        1.0 is reported as **unresolved, never as a finding** (the ADR-0040
        Decision 6 rule, applied here).

    Notes
    -----
    One row resample is shared by all four means, exactly as
    ``gap_decomposition.bootstrap_comparator_means`` shares one draw across
    comparators. Resampling rows with replacement is equivalent to a
    multinomial draw over the joint patterns, so the bootstrap runs on a
    16-cell table rather than on the (1e5, n_levels) matrices.
    """
    total = int(counts.sum())
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(total, counts / total, size=n_boot).astype(np.float64)
    means = draws @ _PATTERN_BITS.T / total  # (n_boot, 4)
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = (means[:, 2] / means[:, 3]) / (means[:, 0] / means[:, 1])
    rho = rho[np.isfinite(rho)]
    point_means = counts @ _PATTERN_BITS.T / total
    point = float((point_means[2] / point_means[3]) / (point_means[0] / point_means[1]))
    alpha = (1.0 - confidence) / 2.0
    lo = float(np.quantile(rho, alpha))
    hi = float(np.quantile(rho, 1.0 - alpha))
    return {
        "rho": point,
        "rho_lo": lo,
        "rho_hi": hi,
        "resolved": bool(lo > 1.0 or hi < 1.0),
        "n_boot_finite": int(rho.size),
    }


def _design_crest_at(kp: float) -> float:
    """2019 design bank height at a chainage, m MSL (right bank, Tokachi)."""
    bank = _read_longitudinal(BANK_HEIGHT_CSV, ("DesignBankHeight_R",), "Tokachi")
    return float(np.interp(kp, bank["kp"], bank["DesignBankHeight_R"]))


def _load_persisted_sweep(path: Path) -> dict[str, Any]:
    """Read the arrays the ratio stage needs from a persisted sweep."""
    with h5py.File(path, "r") as handle:
        return {
            "grid": np.asarray(handle["conditioning_grid"], dtype=float),
            "P_f_static_raw": np.asarray(handle["P_f_static_raw"], dtype=float),
            "P_f_trans_raw": np.asarray(handle["P_f_trans_raw"], dtype=float),
            "failure_matrix_static": np.asarray(handle["failure_matrix_static"]),
            "failure_matrix_trans": np.asarray(handle["failure_matrix_trans"]),
            "binomial_ci": {
                key: np.asarray(handle[f"binomial_ci/{key}"], dtype=float)
                for key in ("static_lo", "static_hi", "trans_lo", "trans_hi")
            },
        }


def study_ratio(
    label: str, arms: list[tuple[str, float]], n_jobs: int, *, verbose: bool = True
) -> dict[str, Any]:
    """Does the static-vs-transient bias ratio survive substituting the DEM L?

    The thesis's headline claims are **ratios** -- the Stage 6.6
    conventional-practice bias, the WBI+ peak-shortcut over-rejection -- not
    absolute probabilities, and ADR-0048 established that an epistemic bracket
    can dominate the absolute numbers while cancelling in the ratio. This stage
    asks the same question of the L bracket, per conditioning level, with a
    paired-bootstrap interval so "the ratio moved" is a resolvable claim rather
    than a nonzero difference.
    """
    spec = SECTIONS[label]
    config_path = REPO_ROOT / spec["config"]
    production_path = REPO_ROOT / spec["production"]
    baseline_L = float(Config.from_yaml(config_path).geometry.L)
    persisted = _load_persisted_sweep(production_path)

    started = time.time()
    baseline = _run_arm(config_path, baseline_L, n_jobs)
    _assert_baseline_bit_identical(baseline, production_path, label)
    # Stronger than the P_f gate above: the whole failure matrices must match,
    # so a drift that happened to preserve the column means would still fail.
    for name, fresh in (
        ("static", baseline.failure_matrix_stat),
        ("trans", baseline.failure_matrix_tran),
    ):
        if not np.array_equal(fresh, persisted[f"failure_matrix_{name}"]):
            raise AssertionError(
                f"{label}: fresh {name} failure matrix differs from the persisted "
                f"sweep {production_path.name}. Refusing to report a ratio."
            )

    grid = np.asarray(baseline.conditioning_grid, dtype=float)
    geometry = Config.from_yaml(config_path).geometry
    hwl = float(geometry.HWL)
    crest = _design_crest_at(spec["kp"])
    record: dict[str, Any] = {
        "section": label,
        "csv_L_m": baseline_L,
        "hwl_m_msl": hwl,
        "design_crest_m_msl": crest,
        "n_samples": int(baseline.theta_matrix.shape[0]),
        "baseline_failure_matrices_bit_identical_to_production": True,
        "min_failures_per_cell": RATIO_MIN_FAILURES,
        "bootstrap": {"n": RATIO_BOOTSTRAP_N, "confidence": RATIO_CONFIDENCE},
        "baseline_deliverable_form": {
            branch: baseline.metadata["fragility_deliverable"][branch]["form"]
            for branch in ("static", "transient")
        },
        "arms": {},
    }

    for arm_name, dem_L in arms:
        arm = _run_arm(config_path, dem_L, n_jobs)
        levels: list[dict[str, Any]] = []
        for index, stage in enumerate(grid):
            cells = (
                int(persisted["failure_matrix_static"][:, index].sum()),
                int(persisted["failure_matrix_trans"][:, index].sum()),
                int(arm.failure_matrix_stat[:, index].sum()),
                int(arm.failure_matrix_tran[:, index].sum()),
            )
            if min(cells) < RATIO_MIN_FAILURES:
                continue
            counts = _pattern_counts(
                persisted["failure_matrix_static"][:, index],
                persisted["failure_matrix_trans"][:, index],
                arm.failure_matrix_stat[:, index],
                arm.failure_matrix_tran[:, index],
            )
            interval = ratio_of_ratios_ci(counts, seed=index)
            ratio_csv = (
                persisted["P_f_static_raw"][index] / persisted["P_f_trans_raw"][index]
            )
            ratio_dem = float(arm.P_f_static_raw[index] / arm.P_f_trans_raw[index])
            levels.append(
                {
                    "stage_m_msl": float(stage),
                    "well_populated": bool(min(cells) >= RATIO_WELL_POPULATED),
                    "min_cell_failures": int(min(cells)),
                    "at_or_below_hwl": bool(stage <= hwl),
                    "at_or_below_design_crest": bool(stage <= crest),
                    "P_f_static_csv": float(persisted["P_f_static_raw"][index]),
                    "P_f_trans_csv": float(persisted["P_f_trans_raw"][index]),
                    "P_f_static_dem": float(arm.P_f_static_raw[index]),
                    "P_f_trans_dem": float(arm.P_f_trans_raw[index]),
                    "failures_static_csv": cells[0],
                    "failures_trans_csv": cells[1],
                    "failures_static_dem": cells[2],
                    "failures_trans_dem": cells[3],
                    "cp95_trans_csv": [
                        float(persisted["binomial_ci"]["trans_lo"][index]),
                        float(persisted["binomial_ci"]["trans_hi"][index]),
                    ],
                    "cp95_trans_dem": [
                        float(arm.binomial_ci["transient"][0][index]),
                        float(arm.binomial_ci["transient"][1][index]),
                    ],
                    "ratio_static_over_trans_csv": float(ratio_csv),
                    "ratio_static_over_trans_dem": ratio_dem,
                    **interval,
                }
            )

        resolved = [lv for lv in levels if lv["resolved"]]
        attainable = [lv for lv in levels if lv["at_or_below_design_crest"]]
        at_hwl = min(levels, key=lambda lv: abs(lv["stage_m_msl"] - hwl), default=None)
        departures = [abs(np.log(lv["rho"])) for lv in resolved]
        entry: dict[str, Any] = {
            "L_m": dem_L,
            "delta_L_m": dem_L - baseline_L,
            "deliverable_form": {
                branch: arm.metadata["fragility_deliverable"][branch]["form"]
                for branch in ("static", "transient")
            },
            "deliverable_transition_bracketed": {
                branch: bool(
                    arm.metadata["fragility_deliverable"][branch][
                        "transition_bracketed"
                    ]
                )
                for branch in ("static", "transient")
            },
            "deliverable_max_p_f_raw": {
                branch: float(
                    arm.metadata["fragility_deliverable"][branch]["max_p_f_raw"]
                )
                for branch in ("static", "transient")
            },
            "n_levels_evaluated": len(levels),
            "n_levels_resolved": len(resolved),
            "n_levels_at_or_below_design_crest": len(attainable),
            "n_resolved_at_or_below_design_crest": sum(
                1 for lv in attainable if lv["resolved"]
            ),
            "nearest_hwl_level": at_hwl,
            "rho_min": float(min((lv["rho"] for lv in levels), default=float("nan"))),
            "rho_max": float(max((lv["rho"] for lv in levels), default=float("nan"))),
            "max_resolved_departure_factor": float(
                np.exp(max(departures)) if departures else 1.0
            ),
            "levels": levels,
        }
        record["arms"][arm_name] = entry
        if verbose:
            print(
                f"    {label} {arm_name} L={dem_L:g} m: ratio-of-ratios over "
                f"{entry['n_levels_evaluated']} levels in "
                f"[{entry['rho_min']:.3f}, {entry['rho_max']:.3f}]; "
                f"{entry['n_levels_resolved']} resolved; worst resolved "
                f"departure x{entry['max_resolved_departure_factor']:.3f}; "
                f"transient deliverable "
                f"{record['baseline_deliverable_form']['transient']} -> "
                f"{entry['deliverable_form']['transient']}",
                flush=True,
            )

    record["elapsed_s"] = round(time.time() - started, 1)
    return record


# --------------------------------------------------------------------------- #
# Stage: figure                                                                #
# --------------------------------------------------------------------------- #
FIGURE_PATH = REPO_ROOT / "docs" / "figures" / "adr0047_dem_seepage_length.png"


def draw_figure(payload: dict[str, Any], path: Path = FIGURE_PATH) -> None:
    """Three-row summary figure from an evidence payload.

    Row 1: the four picked cross-sections with crest band and toes marked.
    Row 2: L along the levee over the chainage window, clean stations solid.
    Row 3: DEM-vs-CSV L, and the measured fragility effect where it was run.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # House palette and chrome, so this figure reads as one system with
    # the rest: the fixed categorical slots, the two limit states on
    # their thesis-wide hues, hairline solid grid, no legend frames.
    figstyle.style()

    measurements = payload.get("measurements", [])
    if not measurements:
        raise ValueError("payload carries no measurements to draw")
    # ``csv_L_m`` is whatever the geotechnical CSV holds now, which at an
    # adopted section is the surveyed value and not the survey it replaced.
    # A section is adopted exactly where the 1998 reading was withdrawn, so
    # the reference line is named from that rather than labelled "1998
    # survey" for a number the 1998 survey never carried.
    adopted = {
        entry["section"]
        for entry in payload.get("fragility", [])
        if "withdrawn_1998" in entry.get("arms", {})
    }
    vintage = payload.get("csv_geometry_vintage", "1998")
    n = len(measurements)
    fig, axes = plt.subplots(3, n, figsize=(4.6 * n, 11.0), dpi=140)
    axes = np.atleast_2d(axes)

    for column, record in enumerate(measurements):
        label = record["section"]
        csv_source = "adopted" if label in adopted else f"{vintage} survey"
        nominal = record["nominal_station"]
        stem = f"kp{record['kp']:.1f}".replace(".", "_")
        csv_path = PROFILE_DIR / f"{stem}_profile.csv"

        # --- row 1: the picked cross-section ---
        ax = axes[0, column]
        if csv_path.exists():
            offsets, elevation = read_profile_csv(csv_path)
            keep = (offsets >= -160.0) & (offsets <= 160.0)
            ax.plot(offsets[keep], elevation[keep], color=figstyle.INK, lw=1.3)
        for key, colour, marker in (
            ("river_toe", figstyle.BLUE, "v"),
            ("land_outer_toe", figstyle.RED, "v"),
        ):
            ax.plot(
                nominal[f"{key}_offset_m"],
                nominal[f"{key}_elev_m_tp"],
                marker,
                color=colour,
                ms=9,
                zorder=5,
            )
        ax.axvspan(
            (
                nominal["crest_river_offset_m"]
                if "crest_river_offset_m" in nominal
                else -nominal["crest_width_m"] / 2
            ),
            (
                nominal["crest_land_offset_m"]
                if "crest_land_offset_m" in nominal
                else nominal["crest_width_m"] / 2
            ),
            color=figstyle.YELLOW,
            alpha=0.22,
            lw=0,
        )
        ax.annotate(
            f"nominal station L = {nominal['L_m']:.0f} m",
            xy=(
                (nominal["river_toe_offset_m"] + nominal["land_outer_toe_offset_m"])
                / 2,
                nominal["land_outer_toe_elev_m_tp"] - 1.2,
            ),
            ha="center",
            fontsize=10,
            # Text wears an ink token, never a series colour, and this one
            # sits over the profile, so it carries the surface plate too.
            color=figstyle.INK_2,
            weight="bold",
            bbox={
                "facecolor": figstyle.SURFACE,
                "edgecolor": "none",
                "alpha": 0.85,
                "pad": 2.0,
            },
        )
        ax.set_title(
            f"{label}  ({csv_source} {record['csv_L_m']:.1f} m, "
            f"{record['remediation_state']})",
            fontsize=11,
            color=figstyle.INK,
        )
        ax.set_xlabel("offset from alignment [m]  (negative = riverside)")
        if column == 0:
            ax.set_ylabel("elevation [m T.P.]")

        # --- row 2: L along the levee ---
        ax = axes[1, column]
        window = record["window"]
        offsets = np.asarray(window["chainage_offsets_m"], dtype=float)
        lengths = np.asarray(window["L_by_offset_m"], dtype=float)
        clean = np.asarray(window["clean_station_by_offset"], dtype=bool)
        ax.plot(offsets, lengths, color=figstyle.BASELINE, lw=1.0, zorder=1)
        ax.plot(
            offsets[clean],
            lengths[clean],
            "o",
            color=figstyle.GREEN,
            ms=5,
            label="clean",
        )
        ax.plot(
            offsets[~clean],
            lengths[~clean],
            "x",
            color=figstyle.MUTED,
            ms=6,
            label="rejected",
        )
        ax.axhline(
            window["L_median_clean_m"],
            color=figstyle.GREEN,
            ls="--",
            lw=1.4,
            label=f"DEM median {window['L_median_clean_m']:.0f} m",
        )
        ax.axhline(
            record["csv_L_m"],
            color=figstyle.RED,
            ls=":",
            lw=1.6,
            label=f"{csv_source} {record['csv_L_m']:.1f} m",
        )
        ax.set_xlabel("chainage offset from the section [m]")
        if column == 0:
            ax.set_ylabel("picked L [m]")
        # Both legends sit over marks, so they carry the house surface
        # plate rather than a frame, exactly as ``mark_hypothetical`` does.
        ax.legend(fontsize=7, loc="upper left", **_LEGEND_PLATE)

        # --- row 3: the fragility consequence ---
        ax = axes[2, column]
        entry = next(
            (f for f in payload.get("fragility", []) if f["section"] == label), None
        )
        if entry is None:
            ax.text(
                0.5,
                0.5,
                "fragility stage not run",
                ha="center",
                va="center",
                color=figstyle.MUTED,
            )
            ax.set_axis_off()
            continue
        names = list(entry["arms"])
        width = 0.36
        positions = np.arange(len(names))
        # STATIC is blue and TRANSIENT is red for the whole thesis; this
        # figure had them the other way round, which reads backwards
        # against every fragility figure in the results chapters.
        for shift, branch, colour, name in (
            (-width / 2, "trans", figstyle.TRANSIENT, "transient"),
            (width / 2, "static", figstyle.STATIC, "static"),
        ):
            values = [entry["arms"][arm][branch]["max_abs_delta_P_f"] for arm in names]
            ax.bar(positions + shift, values, width, label=name, color=colour)
            for x, value in zip(positions + shift, values):
                ax.annotate(
                    f"{value:.3f}",
                    (x, value),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color=figstyle.INK_2,
                )
        ax.set_xticks(positions)
        ax.set_xticklabels(
            [
                f"{ARM_DISPLAY_NAMES.get(n, n)}\nL={entry['arms'][n]['L_m']:.0f} m"
                for n in names
            ],
            fontsize=8,
        )
        ax.set_ylabel("max |dP_f| vs production" if column == 0 else "")
        ax.legend(fontsize=8, **_LEGEND_PLATE)
        ax.grid(axis="x", visible=False)

    fig.suptitle(
        "Seepage length L surveyed from the national elevation model "
        f"(GSI DEM5A {payload.get('dem_source', '').split('devDate ')[-1]}) "
        f"against the {payload.get('csv_geometry_vintage', '1998')} "
        "OYO cross-section geometry",
        fontsize=13,
        color=figstyle.INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
Stage = Literal["datum", "profiles", "fragility", "ratio", "figure", "all"]

#: Payload keys that cost real compute. A cheap partial run must not silently
#: replace an evidence file that already carries them.
EXPENSIVE_KEYS: tuple[str, ...] = (
    "datum_check",
    "measurements",
    "fragility",
    "ratio",
)


def _write_payload(payload: dict[str, Any], path: Path, *, overwrite: bool) -> None:
    """Write the evidence JSON, refusing to drop expensive content.

    A ``profiles``-only re-run would otherwise wipe the ``fragility`` block
    that cost nine production sweeps. Mirrors the ``--overwrite`` refusal
    guard of ``scripts/run_sweep.py``.
    """
    if path.exists() and not overwrite:
        existing = json.loads(path.read_text(encoding="utf-8"))
        lost = [key for key in EXPENSIVE_KEYS if key in existing and key not in payload]
        if lost:
            raise SystemExit(
                f"Refusing to overwrite {path.name}: it carries {', '.join(lost)} "
                "that this run did not produce. Re-run the missing stage, write "
                "to a different --out, or pass --overwrite to discard it."
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "stage",
        nargs="?",
        default="all",
        choices=("datum", "profiles", "fragility", "ratio", "figure", "all"),
        help="Which stage to run (default: all).",
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        default=list(SECTIONS),
        choices=list(SECTIONS),
        help="Sections to study (default: all four confined sections).",
    )
    parser.add_argument(
        "--n-jobs", type=int, default=4, help="joblib workers per sweep."
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Re-parse the GML tiles instead of using the mosaic cache.",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Evidence JSON output path."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow a partial run to discard expensive blocks already on disk.",
    )
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "study": "ADR-0047 DEM-surveyed seepage length L",
        "generated_by": "scripts/dem_cross_section_study.py",
        "dem_source": (
            f"GSI 基盤地図情報 DEM5A, secondary mesh 644331, devDate {DEM_DEV_DATE}"
        ),
        "csv_geometry_vintage": CSV_GEOMETRY_VINTAGE,
        "d70_interpretation": "matrix",
        "note": (
            "L is the under-levee confined path (riverside toe to landside "
            "toe) only; the foreshore is carried separately through "
            "lambda_out inside r_e and is never added to L. No input value "
            "is changed: the fragility arms override geometry.L in memory, "
            "the CSV and configs are read-only, and every baseline arm is "
            "asserted bit-identical to its persisted production sweep before "
            "any sensitivity is reported."
        ),
    }

    print(f"[mosaic] loading (cache {'off' if args.no_cache else 'on'}) ...")
    mosaic = load_dem_mosaic(use_cache=not args.no_cache, verbose=True)
    alignment = build_alignment()
    payload["alignment"] = {
        "source": "data/raw/gis/SECTIONS.shp (EPSG:2455, JGD2000 CS XIII)",
        "chain": [f"{name}[{index}]" for name, index in ALIGNMENT_CHAIN],
        "total_length_m": float(alignment.arc_length_m[-1]),
        "kp_control_s_m": [float(v) for v in alignment.control_s_m],
        "kp_control_kp": [float(v) for v in alignment.control_kp],
    }

    if args.stage in ("datum", "all"):
        print("[datum] checking the DEM against three repo longitudinals ...")
        payload["datum_check"] = run_datum_check(mosaic, alignment)

    measurements: list[dict[str, Any]] = []
    if args.stage in ("profiles", "fragility", "ratio", "all"):
        print("[profiles] measuring cross-sections ...")
        for label in args.sections:
            measurements.append(measure_section(mosaic, alignment, label))
        payload["measurements"] = measurements

    if args.stage == "figure":
        # Draw-only: never touches the evidence file.
        draw_figure(json.loads(args.out.read_text(encoding="utf-8")))
        print(f"wrote {FIGURE_PATH}")
        return

    if args.stage == "ratio":
        print("[ratio] does the static-vs-transient bias survive the L change? ...")
        arms = fragility_arms_from_measurements(measurements)
        payload["ratio"] = [
            study_ratio(label, arms[label], args.n_jobs) for label in args.sections
        ]

    if args.stage in ("fragility", "all"):
        print("[fragility] driving DEM L through the production engine ...")
        arms = fragility_arms_from_measurements(measurements)
        payload["fragility"] = [
            study_fragility(label, arms[label], args.n_jobs) for label in args.sections
        ]

    _write_payload(payload, args.out, overwrite=args.overwrite)
    print(f"\nwrote {args.out}")
    if args.stage == "all":
        draw_figure(payload)
        print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
