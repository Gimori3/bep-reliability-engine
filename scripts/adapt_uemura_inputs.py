"""Adapter: Uemura raw drop -> committed per-segment surface-model inputs.

ADR-0042. Reads the gitignored raw drop's ``data/df_river.csv`` (Uemura's own
consolidated per-KP input table for the WP2 surface-failure models), validates
it against the independently committed repo artifacts, restricts it to the
ADR-0038 study reaches, and writes the committed extract

    data/processed/uemura_segments/segment_inputs.csv
    data/processed/uemura_segments/df_river_verbatim.csv   (byte-exact mirror)
    data/processed/uemura_segments/provenance.md

Raw files are read-only; re-run this script after any upstream drop update.

Validations (each a hard failure, per the ADR-0042 adapter contract):

* ``HQ_a``/``HQ_b`` identical to the committed M3 rating files at every
  study-reach node (proves the stage axis is the ADR-0021 m MSL datum);
* ``Average_bh``/``Sig_bh`` match the committed
  ``data/raw/bank_heights/BankHeight_AveSig_*.csv`` provenance files;
* elevation ordering riverbed < floodplain < design crest at every node;
* full coverage of both study reaches with no missing values.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine.hydrographs import (  # noqa: E402
    load_rating_coefficients,
    rating_curve_path,
)
from system_integration.segments import STUDY_REACHES  # noqa: E402

RAW_DROP = REPO / "data" / "digitized" / "uemura_fragility_curves"
DF_RIVER = RAW_DROP / "data" / "df_river.csv"
OUT_DIR = REPO / "data" / "processed" / "uemura_segments"

# ADR-0042 decision 6 (amended 2026-07-22): the source workbook
# ``Uncertainty_HQrelation.xlsx`` arrived (now committed under
# ``data/raw/``). It is the direct implementation of paper Eqs. (9)/(10):
# per gauge, ``Ave`` = mean(observed - rating) and ``Sig`` = STDEV.S of the
# same stage residual [m], which his final ``count_failures``
# (``2021-11-19 Description WP2 Work week 3.ipynb``) consumes verbatim as
# ``wl = h + N(WlevUncMu, WlevUncSigma)`` — the same form as
# ``uemura_models.draw_overflow``. Both gauges' measured Eq. 10 pair is now
# adopted (values rounded to mm), replacing the interim 0.6/0.38 constant
# (which traced to the toy ``frajilty curve ver2.ipynb`` demo, not Eq. 10):
#   Tokachi  <- Obihiro gauge KP56.73, sheet ``TokachiRiv._Obihiro`` K2/L2
#   Satsunai <- Nantai  gauge KP15,    sheet ``SatsunaiRiv._Nantai``  M2/N2
# The residual sign is pinned three ways (paper Eq. 9, workbook formula
# ``=E-I``, his notebook), so ``Ave`` is used with its native sign.
WL_ERR_BY_RIVER: dict[str, tuple[float, float]] = {
    "Tokachi": (-0.160, 0.294),  # Obihiro: Ave -0.16013, Sig 0.29373 (n=238)
    "Satsunai": (-0.051, 0.283),  # Nantai:  Ave -0.05110, Sig 0.28314 (n=236)
}

_RIVER_NAME = {"tokachi": "Tokachi", "satsunai": "Satsunai"}
_BANK = {"Tokachi": "right", "Satsunai": "left"}


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"VALIDATION FAILED: {message}")


def main() -> None:
    # This driver takes no arguments. The parser exists so that a probe
    # (--help, a stray flag) is inert instead of running the whole study.
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    _check(DF_RIVER.exists(), f"raw drop table missing: {DF_RIVER}")
    raw = pd.read_csv(DF_RIVER)

    frames = []
    for river_lower, river in _RIVER_NAME.items():
        kp_lo, kp_hi = STUDY_REACHES[(river, _BANK[river])]
        part = raw[raw["River"] == river_lower].copy()
        part["kp"] = part["KP"].round(1)
        part = part[(part["kp"] >= kp_lo - 1e-6) & (part["kp"] <= kp_hi + 1e-6)]
        expected = round((kp_hi - kp_lo) / 0.2) + 1
        _check(
            len(part) == expected,
            f"{river}: {len(part)} nodes in [{kp_lo}, {kp_hi}], expected "
            f"{expected} on the 0.2 km grid.",
        )
        part["river"] = river
        part["bank"] = _BANK[river]
        frames.append(part)
    df = pd.concat(frames, ignore_index=True)
    _check(
        not df.drop(columns=["river", "bank"]).isna().any().any(),
        "missing values inside the study reaches.",
    )

    # Rating identity against the committed M3 files (ADR-0042 decision 2).
    for river in ("Tokachi", "Satsunai"):
        coeffs = load_rating_coefficients(rating_curve_path(REPO / "data/raw", river))
        sub = df[df["river"] == river]
        for row in sub.itertuples():
            a, b = coeffs[row.kp]
            _check(
                abs(row.HQ_a - a) <= 1e-9 and abs(row.HQ_b - b) <= 1e-9,
                f"{river} KP {row.kp:g}: drop HQ ({row.HQ_a}, {row.HQ_b}) != "
                f"committed rating ({a}, {b}).",
            )

    # Bank-height statistics against the committed provenance files.
    for river in ("Tokachi", "Satsunai"):
        prov = pd.read_csv(
            REPO / "data/raw/bank_heights" / f"BankHeight_AveSig_{river}.csv"
        )
        prov["kp"] = prov["KP"].round(1)
        prov = prov.set_index("kp")
        sub = df[df["river"] == river]
        for row in sub.itertuples():
            if row.kp not in prov.index:
                continue  # provenance file covers a subset; identity where present
            _check(
                abs(row.Average_bh - prov.loc[row.kp, "Average"]) <= 5e-3
                and abs(row.Sig_bh - prov.loc[row.kp, "Sig"]) <= 5e-3,
                f"{river} KP {row.kp:g}: crest stats disagree with "
                "BankHeight_AveSig provenance file.",
            )

    # Elevation ordering sanity.
    bad = df[
        ~(
            (df["RiverbedElevation"] < df["FloodplaneHeight"])
            & (df["FloodplaneHeight"] < df["BankHeight"])
        )
    ]
    _check(
        bad.empty,
        "elevation ordering riverbed < floodplain < crest violated at "
        f"{[(r.river, r.kp) for r in bad.itertuples()]}.",
    )

    out = pd.DataFrame(
        {
            "river": df["river"],
            "bank": df["bank"],
            "kp": df["kp"],
            "crest_design_m_msl": df["BankHeight"],
            "crest_err_mu_m": df["Average_bh"],
            "crest_err_sigma_m": df["Sig_bh"],
            "hwl_m_msl": df["HWL"],
            "ground_m_msl": df["GroundHeight"],
            "floodplain_m_msl": df["FloodplaneHeight"],
            "riverbed_m_msl": df["RiverbedElevation"],
            "crest_width_m": df["CrestWidth"],
            "slope_h_per_v": df["BankGradient"],
            "water_surface_gradient_inv": df["Gradient_WaterSurface"],
            "hq_a": df["HQ_a"],
            "hq_b": df["HQ_b"],
            "wl_err_mu_m": [WL_ERR_BY_RIVER[river][0] for river in df["river"]],
            "wl_err_sigma_m": [WL_ERR_BY_RIVER[river][1] for river in df["river"]],
            # Both gauges are now measured from the workbook (no assumption).
            "wl_err_assumed": [False for _ in df["river"]],
        }
    ).sort_values(["river", "kp"], ignore_index=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_DIR / "segment_inputs.csv", index=False)
    shutil.copyfile(DF_RIVER, OUT_DIR / "df_river_verbatim.csv")
    _write_provenance(len(out))
    print(
        f"Wrote {OUT_DIR / 'segment_inputs.csv'} ({len(out)} segments; "
        "all validations passed)."
    )


_PROVENANCE_ROWS: list[tuple[str, str, str]] = [
    (
        "river, bank, kp",
        "df_river `River`, `KP`",
        "study reaches per ADR-0038 (Tokachi right 53.8-62.8, Satsunai left "
        "3.2-16.6); bank fixed by scope",
    ),
    (
        "crest_design_m_msl",
        "df_river `BankHeight`",
        "design (planned) crest, T.P. m MSL",
    ),
    (
        "crest_err_mu_m, crest_err_sigma_m",
        "df_river `Average_bh`, `Sig_bh`",
        "per-KP actual-minus-design crest stats (paper Eqs. 11-12); validated "
        "against `data/raw/bank_heights/BankHeight_AveSig_*.csv`; sigma used "
        "verbatim per ADR-0042 decision 7",
    ),
    (
        "hwl_m_msl",
        "df_river `HWL`",
        "design high-water level (reference only, not a model input)",
    ),
    (
        "ground_m_msl",
        "df_river `GroundHeight`",
        "landside ground elevation in the embankment (scour failure gate)",
    ),
    (
        "floodplain_m_msl",
        "df_river `FloodplaneHeight`",
        "floodplain elevation (scour onset / Manning depth datum)",
    ),
    (
        "riverbed_m_msl",
        "df_river `RiverbedElevation`",
        "riverbed elevation (plotting/reference)",
    ),
    (
        "crest_width_m",
        "df_river `CrestWidth`",
        "matches WP2 report Table 2 (8 m; 7 m at Tokachi KP62.0+)",
    ),
    (
        "slope_h_per_v",
        "df_river `BankGradient`",
        "levee slope n in n(H):1(V); 3.0 everywhere (WP2 Table 2)",
    ),
    (
        "water_surface_gradient_inv",
        "df_river `Gradient_WaterSurface`",
        "S = 1/value (his script line `S = 1/ Gradient_WaterSurface`)",
    ),
    (
        "hq_a, hq_b",
        "df_river `HQ_a`, `HQ_b`",
        "validated IDENTICAL to the local M3 rating files "
        "`data/raw/rating_curves/HQrelation_*Riv_2017.csv` (Eq. 4.19; "
        "ADR-0021 datum)",
    ),
    (
        "wl_err_mu_m, wl_err_sigma_m",
        "`Uncertainty_HQrelation.xlsx` (Uemura et al. 2024 Eqs. 9-10)",
        "per-gauge water-level rating error N(mu, sigma) [m], mean/STDEV.S of "
        "observed-minus-rating stage: Tokachi <- Obihiro sheet K2/L2 "
        "(-0.160, 0.294); Satsunai <- Nantai sheet M2/N2 (-0.051, 0.283); "
        "both measured (`wl_err_assumed=False`) per ADR-0042 decision 6 "
        "(amended 2026-07-22)",
    ),
]


def _write_provenance(n_rows: int) -> None:
    lines = [
        "# Provenance: data/processed/uemura_segments/",
        "",
        "Generated by `scripts/adapt_uemura_inputs.py` (ADR-0042). Source: the",
        "gitignored raw drop "
        "`data/digitized/uemura_fragility_curves/data/df_river.csv`",
        "(Uemura's consolidated WP2 input table, timestamp 2023-10-19, consumed",
        "verbatim by his `ErosionModel_231019.py`), mirrored here byte-exactly as",
        f"`df_river_verbatim.csv`. {n_rows} study-reach segments.",
        "",
        "| column | source | note |",
        "|---|---|---|",
    ]
    for column, source, note in _PROVENANCE_ROWS:
        lines.append(f"| {column} | {source} | {note} |")
    lines += [
        "",
        "Raw files were not modified. Regeneration:",
        "`python scripts/adapt_uemura_inputs.py`.",
        "",
    ]
    (OUT_DIR / "provenance.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
