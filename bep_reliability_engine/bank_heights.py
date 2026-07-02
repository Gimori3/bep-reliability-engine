"""Per-KP design high-water-level (HWL) lookup from the 2019 bank-height data.

Thin, standalone reader for the official 2019 design bank-height tables
(``data/raw/geometry/BankHeight_{Tokachi,Satsunai}Riv_2019.csv``, 0.2 km KP
spacing). Only the ``HWL`` column feeds the seepage engine: it is the design
high-water level in **metres above MSL**, the same vertical datum as the M3
stage hydrographs, which is what makes it the correct source for
``config.Geometry.HWL`` (ADR-0018). The two ``DesignBankHeight_*`` columns are
crest elevations for the Phase 3 overflow mechanism and are deliberately never
parsed or returned here — this module is the firewall that keeps them out of M1.

This is config-generation support, not engine physics: ``scripts/
generate_configs.py`` calls :func:`load_hwl` once per cross-section while
building a config; nothing in the M4–M9 kernels imports it. Keeping the CSV
I/O here (rather than in the pydantic model) preserves M1 as a pure data
object (spec §1).

KP matching is **strict** (ADR-0018): a requested KP must land on the 0.2 km
grid within a tiny float tolerance, otherwise the lookup fails loudly and names
the two nearest available KPs. Nearest-match or interpolation would silently
mask a typo'd KP; all current study sections are exact grid points.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

__all__ = ["DEFAULT_BANK_HEIGHT_DIR", "HWL_CSV_BY_RIVER", "load_hwl"]

# Repo-relative home of the official 2019 bank-height tables.
DEFAULT_BANK_HEIGHT_DIR: Path = (
    Path(__file__).resolve().parents[1] / "data" / "raw" / "geometry"
)

# River name (the geotech CSV ``river`` column) -> 2019 bank-height filename.
HWL_CSV_BY_RIVER: dict[str, str] = {
    "Tokachi": "BankHeight_TokachiRiv_2019.csv",
    "Satsunai": "BankHeight_SatsunaiRiv_2019.csv",
}

# KP match tolerance [km]: generous against float parsing noise, far below the
# 0.2 km grid spacing, so it can only ever match the intended grid point.
_KP_MATCH_TOL_KM: float = 1.0e-6


def load_hwl(
    river: str, kp: float, *, data_dir: str | Path = DEFAULT_BANK_HEIGHT_DIR
) -> float:
    """Return the official 2019 design HWL [m MSL] for one river KP.

    Parameters
    ----------
    river : str
        River name selecting the bank-height file; one of
        :data:`HWL_CSV_BY_RIVER` (``'Tokachi'`` or ``'Satsunai'``).
    kp : float
        Kilometre-post of the cross-section [km]. Must match a 0.2 km grid
        point of the file exactly (strict match, ADR-0018).
    data_dir : str or pathlib.Path, optional
        Directory holding the bank-height CSVs. Defaults to
        ``data/raw/geometry`` at the repository root.

    Returns
    -------
    float
        The design high-water level at that KP, metres above MSL — the same
        vertical datum as the M3 stage hydrographs. Validated positive and
        finite.

    Raises
    ------
    ValueError
        If the river is unknown, the file lacks the expected columns, the KP
        is not a grid point (the message names the two nearest available
        KPs), or the HWL cell is empty, non-numeric, non-finite, or
        non-positive.
    """
    try:
        filename = HWL_CSV_BY_RIVER[river]
    except KeyError:
        known = ", ".join(sorted(HWL_CSV_BY_RIVER))
        raise ValueError(
            f"Unknown river {river!r}; 2019 bank-height HWL data exist for: "
            f"{known}."
        ) from None

    path = Path(data_dir) / filename
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = {"River", "KP", "HWL"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path.name}: missing required column(s) {sorted(missing)}; "
                "expected the 2019 bank-height schema (River, KP, HWL, ...)."
            )
        rows = list(reader)

    file_kps: list[float] = []
    matched_row: dict[str, str] | None = None
    for row in rows:
        try:
            row_kp = float(row["KP"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{path.name}: non-numeric KP cell {row['KP']!r}."
            ) from exc
        file_kps.append(row_kp)
        if matched_row is None and abs(row_kp - kp) <= _KP_MATCH_TOL_KM:
            matched_row = row

    if matched_row is None:
        nearest = sorted(sorted(file_kps, key=lambda v: abs(v - kp))[:2])
        nearest_txt = " and ".join(f"{value:g}" for value in nearest)
        raise ValueError(
            f"KP {kp:g} is not a grid point of {path.name} (0.2 km spacing); "
            f"nearest available KPs are {nearest_txt}. Off-grid KPs are "
            "rejected by design (strict match, ADR-0018) — confirm the KP "
            "before relaxing this."
        )

    raw_hwl = (matched_row["HWL"] or "").strip()
    if not raw_hwl:
        raise ValueError(f"{path.name}: HWL cell at KP {kp:g} is empty.")
    try:
        hwl = float(raw_hwl)
    except ValueError as exc:
        raise ValueError(
            f"{path.name}: HWL cell at KP {kp:g} is non-numeric: {raw_hwl!r}."
        ) from exc
    if not math.isfinite(hwl) or hwl <= 0.0:
        raise ValueError(
            f"{path.name}: HWL at KP {kp:g} must be a positive, finite "
            f"elevation [m MSL], got {hwl!r}."
        )
    return hwl
