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
   (0.014, 0.50), and ``seepage_length_cov`` is 0.15 at KP 60.0 / 0.20 elsewhere.
4. **geometry.HWL equals the official 2019 bank-height value** for the row's
   river/KP (ADR-0018), re-read here independently of ``bank_heights.load_hwl``
   so a drifted config, a drifted loader, or an edited bank-height CSV all fail.

It does not re-test the engine physics (other modules do that); it locks the
*configuration layer* against the exact staleness this review found.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bep_reliability_engine.config import Config

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
    "C_e": 0.50,
}
_GAMMA_BL_SUB_MEAN = 6.9
_C_E_MEAN = 0.014


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
_CONFIG_PATHS = sorted(_CONFIG_DIR.glob("kp*.yaml"))


def test_configs_exist() -> None:
    """The generated sweep is present (4 sections x 2 scenarios x 2 interps)."""
    assert len(_CONFIG_PATHS) == 16, [p.name for p in _CONFIG_PATHS]


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
