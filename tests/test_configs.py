"""Drift guard: the generated configs must stay in sync with the CSV + thesis.

This is the standing guard demanded by review item #1 (stale configs: the D_bl
means had silently drifted 3-4x from the corrected CSV because the configs were
never regenerated after the CSV fix). It pins, for every file in ``configs/``:

1. **Data-derived means equal the CSV cell** (L, foreshore, k_aq, D_aq, D_bl,
   k_bl, and d_70 for the matrix interpretation), so a CSV edit that is not
   followed by ``python scripts/generate_configs.py`` fails CI here rather than
   silently producing wrong fragility curves.
2. **FIXED CoVs equal the thesis prior table** ``tab:priors_phase1`` (review
   item #2): d_70 = 0.30, D_aq = 0.10, D_bl = 0.167, the three that were stale
   against the old architecture spec-section-7 values; plus the unchanged ones.
3. **gamma / C_e priors and the per-section seepage-length CoV** (review items
   #3, #10): gamma_bl_sub is the FIXED blanket weight (6.9, 0.056), C_e is FIXED
   at the Pol SIE 2024 Table 2 field prior (mean 0.055, std 0.043 => CoV 0.782;
   ADR-0026), and ``seepage_length_cov`` is 0.15 at KP 60.0 / 0.20 elsewhere.
4. **geometry.HWL equals the official 2019 bank-height value** for the row's
   river/KP (ADR-0018), re-read here independently of ``bank_heights.load_hwl``
   so a drifted config, a drifted loader, or an edited bank-height CSV all fail.
5. **geometry.z_toe equals the ADR-0021 landside-toe elevation** [m MSL] — the
   value serving as BOTH the head-translation datum and the exit reference h_e
   (ADR-0007 ``z_toe == h_e``) — and is physically consistent (below HWL, not
   the retired PROVISIONAL 0.0).
6. **mc.conditioning_grid is the approved per-section MSL grid** (2026-07-03,
   audit gap G2): three sub-toe anchors from the base-flow stage region plus a
   0.25 m sweep from just above the toe to HWL + 4 m, bracketing toe and HWL.
7. **hydrograph_source is the ADR-0020 block** with the CSV row's river, the
   section's KP, and the approved ordered canonical event pair (compound
   production shape first, isolated sensitivity end-member second).
8. **The k_aq-d_70 coupling is the ADR-0012 two-population decoupling**
   (``coupling: two_population``, ``rho_log_kaq_d70: 0.0`` recorded but never
   imposed); a reappearing nonzero rho or 'correlated' mode is a regression.
9. **The sweep is historical-only (ADR-0023):** the +4K fragility equals the
   historical fragility by shape invariance, so no ``*_plus4k_*`` config
   exists; climate differentiation lives on the Phase 3 hazard side.

It does not re-test the engine physics (other modules do that); it locks the
*configuration layer* against the exact staleness this review found.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import pytest

from bep_reliability_engine.config import Config
from bep_reliability_engine.hydrographs import (
    build_hydrograph_record,
    validate_datum_consistency,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CSV_PATH = _REPO_ROOT / "data" / "processed" / "tokachi_bep_inputs.csv"
_CONFIG_DIR = _REPO_ROOT / "configs"
_BANK_HEIGHT_DIR = _REPO_ROOT / "data" / "raw" / "geometry"

# Thesis prior table `tab:priors_phase1` CoVs (review item #2). These are what
# the configs must carry; the old architecture spec-section-7 values (d_70 0.10,
# D_aq 0.20, D_bl 0.20) are the staleness this guard rejects.
_EXPECTED_COVS = {
    "k_aq": 0.50,
    "d_70": 0.30,
    "D_aq": 0.10,
    "D_bl": 0.167,
    "k_bl": 0.50,
    "gamma_bl_sub": 0.056,
    # Pol SIE 2024 Table 2 field prior: mean 0.055, std 0.043 => CoV 0.782
    # (ADR-0026, superseding the ADR-0001 calibration-anchored 0.014/0.50).
    "C_e": 0.043 / 0.055,
}
_GAMMA_BL_SUB_MEAN = 6.9
_C_E_MEAN = 0.055

# ADR-0021 landside-toe elevations [m MSL / T.P.] (OYO 1999 transverse sections,
# +/-0.3 m). These serve as BOTH the head-translation datum z_toe and the exit
# reference h_e (ADR-0007 z_toe == h_e); the PROVISIONAL 0.0 is retired.
_Z_TOE_MSL = {
    "57.4": 38.3,
    "58.8": 38.5,
    "60.0": 40.0,
    "62.0": 44.9,
}


def _quarters(start_q: int, end_q: int) -> list[float]:
    """Inclusive quarter-metre range: [start_q/4, ..., end_q/4] (exact floats)."""
    return [q / 4.0 for q in range(start_q, end_q + 1)]


# Approved per-section MSL conditioning grids (2026-07-03; audit gap G2):
# three sub-toe anchors (base-flow stage region — zero-load floor of the
# fragility curve) + a 0.25 m sweep from just above the ADR-0021 toe up to
# HWL + 4 m (covering the extreme-HFB stage range so the fitted curve is not
# extrapolated in the scenario analysis). KP 62.0 additionally carries the
# ADR-0024 static-bracketing extension: 0.5 m steps from 51.0 to 56.5 m MSL
# (12 levels, N_h 26 -> 38), hypothetical fit-stabilizers above the crest
# (47.89 m) and the max attainable stage (~51.5 m) so the static transition
# (P_f ~ 0.54 at 56.5 per the 2026-07-03 probe) is bracketed; the transient
# transition is deliberately NOT chased (raw-tail deliverable instead).
# Duplicated here from the generator deliberately: this file is the drift
# guard, not a re-derivation.
_EXPECTED_GRID_MSL = {
    "57.4": [34.75, 36.50, 38.00, *_quarters(154, 173)],  # 38.50..43.25, N_h=23
    "58.8": [36.50, 37.50, 38.25, *_quarters(155, 180)],  # 38.75..45.00, N_h=29
    "60.0": [38.25, 39.25, 39.75, *_quarters(161, 187)],  # 40.25..46.75, N_h=30
    "62.0": [
        41.75,
        43.25,
        44.50,
        *_quarters(180, 202),  # 45.00..50.50 (0.25 m sweep)
        *[51.0 + 0.5 * i for i in range(12)],  # 51.0..56.5 (ADR-0024), N_h=38
    ],
}


def _csv_rows_by_kp() -> dict[str, dict[str, str]]:
    with open(_CSV_PATH, newline="", encoding="utf-8") as handle:
        return {row["kp"]: row for row in csv.DictReader(handle)}


def _hwl_2019(river: str, kp: float) -> float:
    """Independently re-read the 2019 bank-height HWL (not via bank_heights)."""
    path = _BANK_HEIGHT_DIR / f"BankHeight_{river}Riv_2019.csv"
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if abs(float(row["KP"]) - kp) <= 1e-9:
                return float(row["HWL"])
    raise AssertionError(f"KP {kp} not found in {path.name}")


_CSV_BY_KP = _csv_rows_by_kp()
# Glob EVERYTHING in configs/ (not just "kp*.yaml"): a stray or legacy file
# must fail the guard, not silently escape it (2026-07-03 health assessment:
# a dead pre-MSL example config sat invisible to the old "kp*" glob).
_CONFIG_PATHS = sorted(_CONFIG_DIR.glob("*.yaml"))
# Historical-only per ADR-0023: a reappearing *_plus4k_* file is a regression
# (the +4K fragility IS the historical fragility; no separate run exists).
_CONFIG_NAME_RE = re.compile(r"kp\d{2}_\d_historical_(matrix|bulk)\.yaml\Z")


def test_configs_exist() -> None:
    """The generated sweep is present and nothing else (4 x 2 = 8 files).

    Every YAML in ``configs/`` must be one of the eight generated
    historical-scenario files (ADR-0023 dropped the bit-identical +4K set)
    with the canonical name pattern; a ninth file — however named — fails
    here rather than sitting in the directory unvalidated.
    """
    assert len(_CONFIG_PATHS) == 8, [p.name for p in _CONFIG_PATHS]
    nonconforming = [
        p.name for p in _CONFIG_PATHS if not _CONFIG_NAME_RE.fullmatch(p.name)
    ]
    assert nonconforming == [], nonconforming


@pytest.mark.parametrize("path", _CONFIG_PATHS, ids=lambda p: p.name)
def test_config_matches_csv_and_thesis_priors(path: Path) -> None:
    """Each on-disk config matches its CSV row and the thesis prior CoVs."""
    cfg = Config.from_yaml(path)
    kp = cfg.segment_id.removeprefix("KP")  # "KP62.0" -> "62.0"
    assert kp in _CSV_BY_KP, f"{path.name}: KP {kp} not in CSV"
    row = _CSV_BY_KP[kp]

    # --- (1) Data-derived means equal the CSV cell (the staleness guard) ------
    assert cfg.geometry.L == pytest.approx(float(row["L_m"]))
    assert cfg.geometry.foreshore_width == pytest.approx(
        float(row["foreshore_width_m"])
    )
    assert cfg.priors.k_aq.mean == pytest.approx(float(row["k_aq_mps"]))
    assert cfg.priors.D_aq.mean == pytest.approx(float(row["D_aq_m"]))
    assert cfg.priors.D_bl.mean == pytest.approx(float(row["D_bl_m"]))
    assert cfg.priors.k_bl.mean == pytest.approx(float(row["k_bl_mps"]))
    # D_fore / k_fore are the landside-blanket proxy (ADR-0005), so they track
    # D_bl / k_bl exactly.
    assert cfg.geometry.D_fore == pytest.approx(float(row["D_bl_m"]))
    assert cfg.geometry.k_fore == pytest.approx(float(row["k_bl_mps"]))
    # d_70 mean is the CSV matrix value only for the matrix interpretation; the
    # bulk configs carry the separate bulk-gravel co-primary (provenance 3.3).
    if cfg.priors.d70_interpretation == "matrix":
        assert cfg.priors.d_70.mean == pytest.approx(float(row["d70_m"]))

    # --- (2) FIXED CoVs equal the thesis prior table (review item #2) ---------
    for name, expected in _EXPECTED_COVS.items():
        assert getattr(cfg.priors, name).cov == pytest.approx(expected), (
            f"{path.name}: {name} CoV {getattr(cfg.priors, name).cov} != thesis "
            f"{expected}"
        )

    # --- (3) FIXED gamma/C_e priors + per-section stochastic-L CoV ------------
    assert cfg.priors.gamma_bl_sub.mean == pytest.approx(_GAMMA_BL_SUB_MEAN)
    assert cfg.priors.C_e.mean == pytest.approx(_C_E_MEAN)
    expected_l_cov = 0.15 if kp == "60.0" else 0.20
    assert cfg.seepage_length_cov == pytest.approx(expected_l_cov)

    # --- (4) HWL equals the official 2019 bank-height value (ADR-0018) --------
    assert cfg.geometry.HWL == pytest.approx(_hwl_2019(row["river"], float(kp)))

    # --- (5) z_toe is the ADR-0021 landside-toe elevation [m MSL] -------------
    # One value serves as both the head-translation datum and the exit
    # reference h_e (ADR-0007 z_toe == h_e); the PROVISIONAL 0.0 is retired,
    # and the toe must sit below the design HWL (ADR-0021 cross-check table).
    assert cfg.geometry.z_toe == pytest.approx(_Z_TOE_MSL[kp])
    assert cfg.geometry.z_toe != 0.0
    assert cfg.geometry.z_toe < cfg.geometry.HWL

    # --- (6) Conditioning grid is the approved per-section MSL grid (G2) ------
    grid = list(cfg.mc.conditioning_grid)
    expected_grid = _EXPECTED_GRID_MSL[kp]
    assert grid == pytest.approx(expected_grid), (
        f"{path.name}: conditioning_grid drifted from the approved MSL grid "
        f"(got {len(grid)} levels, expected {len(expected_grid)})"
    )
    # Structural sanity independent of the exact values: strictly increasing,
    # bracketing both the toe (zero-load floor below, loaded levels above) and
    # the design HWL (upper tail covers extreme-HFB stages).
    assert all(b > a for a, b in zip(grid, grid[1:]))
    assert grid[0] < cfg.geometry.z_toe < grid[-1]
    assert grid[-1] > cfg.geometry.HWL

    # --- (7) hydrograph_source is the ADR-0020 block (gap G3) -----------------
    # River/KP explicit (never parsed from cross_section_id); the canonical
    # event list is the approved, ORDERED pair: compound production shape
    # first (the one the run uses), isolated sensitivity end-member second.
    src = cfg.hydrograph_source
    assert src is not None, f"{path.name}: hydrograph_source block missing"
    assert src.data_root == "data/raw"
    assert src.river == row["river"]
    assert src.kp == pytest.approx(float(kp))
    assert list(src.canonical_event_ids) == ["HPB_m064_1987", "HPB_m067_1978"]

    # --- (8) k_aq-d_70 coupling is the ADR-0012 two-population decoupling -----
    # The empirical OYO analysis retired the provisional rho = 0.6: matrix
    # d_70 and framework k_aq are distinct soils, sampled decoupled. rho is
    # carried as 0.0 for schema/audit only (recorded, never imposed;
    # metadata['rho_imposed'] is False). A reappearing nonzero rho or a
    # 'correlated' coupling is a regression against ADR-0012.
    assert cfg.correlation.coupling == "two_population", (
        f"{path.name}: coupling {cfg.correlation.coupling!r} != "
        "'two_population' (ADR-0012)"
    )
    assert cfg.correlation.rho_log_kaq_d70 == 0.0, (
        f"{path.name}: rho_log_kaq_d70 {cfg.correlation.rho_log_kaq_d70!r} "
        "!= 0.0 (ADR-0012 retired the provisional 0.6)"
    )

    # --- (10) Foreland treatment is the ADR-0025 blanketed baseline -----------
    # The open-entry end is an on-demand sensitivity, never a sweep member
    # (the filename pattern above already rejects any *_openfore_* file); a
    # config carrying 'open_entry' into the production set is a regression.
    assert cfg.foreland_treatment == "blanketed_tanh", (
        f"{path.name}: foreland_treatment {cfg.foreland_treatment!r} != "
        "'blanketed_tanh' (ADR-0025 baseline)"
    )


@pytest.mark.parametrize("path", _CONFIG_PATHS, ids=lambda p: p.name)
def test_datum_guard_passes_with_real_z_toe(path: Path) -> None:
    """The MSL datum guard accepts every generated config's z_toe (gap G2).

    The counterpart of ``test_datum_guard_refuses_provisional_z_toe``
    (tests/test_hydrographs.py): with the ADR-0021 toe elevations in place,
    an MSL-datum M3 record paired with a generated config's ``z_toe`` must
    pass ``validate_datum_consistency`` silently — the real-hydrograph path
    is no longer datum-blocked.
    """
    cfg = Config.from_yaml(path)
    # A minimal MSL-stage record via the real construction path (Obihiro
    # rating, ADR-0019 §4), peaking near the reach's HWL band.
    record = build_hydrograph_record(
        np.array([1.0, 2.0, 3.0]),
        np.array([1000.0, 4180.0, 1000.0]),
        a_kp=140.33,
        b_kp=-32.49,
        scenario=cfg.scenario,
        event_id="datum_guard_pass_case",
    )
    assert validate_datum_consistency(record, cfg.geometry.z_toe) is None
