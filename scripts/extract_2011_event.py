"""Extract the September 2011 flood-trace survey into a compact committed CSV.

One-time, re-runnable extraction from the raw 2011 agency drop
``data/processed/2011_event/`` (gitignored below the folder root; see the
README there and ADR-0044) into ``data/processed/2011_event/
flood_trace_2011.csv``. Run from the repository root::

    python scripts/extract_2011_event.py

Source: ``洪水痕跡水位/02_{river}_kon_201109.xls`` (洪水痕跡縦断図データ,
the H23.9 post-flood trace longitudinal profiles): per-KP left/right trace
elevations [m MSL], current levee crest heights, and deepest/mean bed
elevations, for the two study rivers (Tokachi, Satsunai). The 2011 drop's
gauge stage/discharge directories are EMPTY (the reason the 2011 event is
closed as a survival constraint, ADR-0044); the trace survey is the
event's usable observational content and feeds the ADR-0044 sustained-peak
bound. Requires the ``xlrd`` package (.xls format): ``pip install xlrd``.

Everything numeric is emitted verbatim; the source's '-' sentinels become
empty cells.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "processed" / "2011_event" / "洪水痕跡水位"
OUT_CSV = REPO_ROOT / "data" / "processed" / "2011_event" / "flood_trace_2011.csv"

# The study rivers only (the drop also covers Otofuke, Shihoro, Tobetsu and
# Sarubetsu, none of which carries a production BEP section).
SOURCES: dict[str, str] = {
    "Tokachi": "02_tokachi_kon_201109.xls",
    "Satsunai": "02_satsunai_kon_201109.xls",
}

# Column layout of the 洪水痕跡縦断図データ sheets (0-based): KP number,
# reach distance, cumulative distance, trace left, trace right, crest left,
# crest right, deepest bed, mean bed.
_COL_KP = 0
_COL_TRACE_LEFT = 3
_COL_TRACE_RIGHT = 4
_COL_CREST_LEFT = 5
_COL_CREST_RIGHT = 6
_COL_BED_MIN = 7
_COL_BED_AVG = 8


def _numeric_or_blank(value: object) -> str:
    if isinstance(value, (int, float)):
        return repr(float(value))
    return ""


def extract_river(path: Path, river: str) -> list[list[str]]:
    """Extract one river's per-KP trace rows from its .xls profile."""
    import xlrd

    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)
    rows: list[list[str]] = []
    for r in range(sheet.nrows):
        kp = sheet.cell_value(r, _COL_KP)
        if not isinstance(kp, float):
            continue
        trace_left = sheet.cell_value(r, _COL_TRACE_LEFT)
        trace_right = sheet.cell_value(r, _COL_TRACE_RIGHT)
        if not isinstance(trace_left, float) and not isinstance(trace_right, float):
            continue  # a distance-only row with no surveyed trace
        rows.append(
            [
                river,
                repr(round(kp, 2)),
                _numeric_or_blank(trace_left),
                _numeric_or_blank(trace_right),
                _numeric_or_blank(sheet.cell_value(r, _COL_CREST_LEFT)),
                _numeric_or_blank(sheet.cell_value(r, _COL_CREST_RIGHT)),
                _numeric_or_blank(sheet.cell_value(r, _COL_BED_MIN)),
                _numeric_or_blank(sheet.cell_value(r, _COL_BED_AVG)),
            ]
        )
    if not rows:
        raise ValueError(f"no trace rows extracted from {path.name}")
    return rows


def main() -> None:
    try:
        import xlrd  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "the 2011 trace sources are .xls; install xlrd first " "(pip install xlrd)."
        ) from exc

    all_rows: list[list[str]] = []
    for river, filename in SOURCES.items():
        all_rows.extend(extract_river(RAW_DIR / filename, river))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "river",
                "kp",
                "trace_left_m_msl",
                "trace_right_m_msl",
                "crest_left_m_msl",
                "crest_right_m_msl",
                "bed_min_m_msl",
                "bed_avg_m_msl",
            ]
        )
        writer.writerows(all_rows)
    print(f"wrote {OUT_CSV.relative_to(REPO_ROOT)} ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
