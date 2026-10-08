"""Fetch the August 2016 hourly stage of the Tokoro River at Futochanae.

One-off extract for the Pol round-2 loading-context study
(``docs/decisions/loading-context-study.md``). The Tokoro is not a study river;
its 2016 record is shown beside the Tokachi and Satsunai records because the
Tokoro boiled in the same storms (thesis Section 8.2).

Source: the public MLIT Water Information System (www1.river.go.jp), station
Futochanae on the Tokoro River, station ID ``301111281108060``, item "hourly
water level" (``KIND=2``). The station page gives the gauge zero as T.P. 0.000 m,
so the readings are T.P. elevations [m], the engine datum. The download file is
Shift-JIS text with one row per day and 24 value/flag pairs; a flag ``*`` marks
a provisional value, ``$`` missing, ``#`` closed and ``-`` unregistered.

Output: ``data/processed/2016_event/stage_hourly_Tokoro_201608.csv`` in the
layout of the other ``stage_hourly_*`` extracts (744 hourly samples,
2016-08-01T01:00 to 2016-09-01T00:00 JST, hour 24 written as 00:00 of the next
day). Run again only to reproduce the committed file; it needs network access.
"""

from __future__ import annotations

import datetime as dt
import re
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "processed" / "2016_event" / "stage_hourly_Tokoro_201608.csv"
STATION_ID = "301111281108060"
BASE = "http://www1.river.go.jp"
PAGE = (
    BASE + "/cgi-bin/DspWaterData.exe?KIND=2&ID={sid}&BGNDATE=20160801"
    "&ENDDATE=20160831&KAWABOU=NO"
)


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
        return response.read()


def parse_hourly_dat(text: str) -> list[tuple[dt.datetime, float | None, str]]:
    """Parse a WIS hourly water-level download into (time, stage, flag) rows."""
    rows: list[tuple[dt.datetime, float | None, str]] = []
    for line in text.splitlines():
        if not re.match(r"^\d{4}/\d{2}/\d{2},", line):
            continue
        parts = line.split(",")
        day = dt.datetime.strptime(parts[0], "%Y/%m/%d")
        for hour in range(24):
            raw = parts[1 + 2 * hour].strip()
            flag = parts[2 + 2 * hour].strip()
            usable = raw not in ("", "-") and flag not in ("$", "#", "-")
            rows.append(
                (
                    day + dt.timedelta(hours=hour + 1),
                    float(raw) if usable else None,
                    flag,
                )
            )
    return rows


def main() -> None:
    page = _get(PAGE.format(sid=STATION_ID)).decode("euc_jp", errors="replace")
    link = re.search(r'href="(/dat/dload/download/[^"]+\.dat)"', page, flags=re.I)
    if link is None:
        raise SystemExit("no download link on the WIS data page")
    text = _get(BASE + link.group(1)).decode("shift_jis")
    rows = parse_hourly_dat(text)
    if len(rows) != 744:
        raise SystemExit(f"expected 744 hourly rows for August 2016, got {len(rows)}")
    flagged = [r for r in rows if r[2]]
    if flagged:
        raise SystemExit(f"{len(flagged)} flagged values; inspect before use")
    lines = ["datetime_jst,futochanae"]
    for when, stage, _ in rows:
        lines.append(f"{when:%Y-%m-%dT%H:%M},{'' if stage is None else f'{stage:.2f}'}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
