"""Stage 7 config generator for the Tokachi BEP reliability engine.

Reads the consolidated geotechnical input table
``data/processed/tokachi_bep_inputs.csv`` and emits one validated YAML config
per cross-section x scenario x d70_interpretation, each loading cleanly through
:meth:`bep_reliability_engine.config.Config.from_yaml`.

Sweep (provenance + spec section 7)
-----------------------------------
* cross-section -- one CSV row each; KP 63.4 is excluded by default
  (unconfined, A_c blanket absent; provenance 3.1/3.5) and admitted only with
  ``--include-kp634``.
* scenario -- ``historical`` and ``+4K``. The CSV carries no scenario-specific
  geotechnics, so the two configs of a pair are identical apart from the
  ``scenario`` tag; the climate difference lives in the downstream hydrograph.
* d70_interpretation -- ``matrix`` (the CSV ``d70_m`` column) and ``bulk`` (the
  bulk-gravel co-primary of provenance 3.3), both carried as primary runs.

Default = 4 x 2 x 2 = 16 configs; with ``--include-kp634`` = 5 x 2 x 2 = 20.

Value provenance (three categories, never conflated)
----------------------------------------------------
* REAL        -- per-cross-section value read from a CSV cell.
* FIXED       -- pinned by spec section 7 / ADR-0016 / Pol 2024; identical in
                 every config; never read from the data table.
* PROVISIONAL -- placeholder awaiting finalized schematization; flagged in each
                 file's header.

Three non-obvious mappings, verified against the built modules
--------------------------------------------------------------
* **gamma.** The config prior ``gamma_bl_sub`` is the *blanket* submerged unit
  weight, FIXED at (mean 6.9, COV 0.056) per ADR-0016 -- it is NOT read from the
  CSV. The CSV ``gamma_sub_kNm3`` column is the aquifer *particle* weight
  gamma'_p; it is recorded in each YAML header for the audit trail ONLY and is
  **not used** -- the run uses the canonical basin-wide deterministic
  gamma'_p = 16.87 (the pinned ``sellmeijer.GAMMA_P_SUB_DEFAULT``), per the
  review-item-#10 decision, so the per-section CSV spread (16.49--16.85) never
  enters F_r. gamma'_p has no config field.
* **seepage length L.** ``geometry.L`` is the per-section MEAN; its uncertainty
  is carried by the top-level ``seepage_length_cov`` (thesis prior
  `tab:seepage_length_prior`: 0.15 at KP 60.0, 0.20 elsewhere), so the engine
  samples L ~ Lognormal(mean=geometry.L, cov) independently of theta (review #3).
* **foreshore.** ``geometry.D_fore`` / ``geometry.k_fore`` (deterministic
  foreshore blanket, ADR-0005) are per-section proxies copied from the landside
  blanket ``D_bl`` / ``k_bl``, so a single CSV ``D_bl_m`` edit (e.g. resolving
  the provenance 3.8 thickness conflict) moves both ``D_bl`` and ``D_fore``.
* **HWL.** ``geometry.HWL`` is the official 2019 design high-water level
  [m MSL], looked up per river/KP from
  ``data/raw/geometry/BankHeight_*Riv_2019.csv`` via ``bank_heights.load_hwl``
  (strict 0.2 km grid match, ADR-0018) — REAL, but from the bank-height CSVs,
  not the geotech table. The ``DesignBankHeight_L/R`` crest columns are Phase 3
  overflow inputs and never enter M1.
* **z_toe / h_e.** ``geometry.z_toe`` is the per-section landside-toe elevation
  [m MSL] from ADR-0021 (OYO 1999 transverse sections, +/-0.3 m) — REAL, from
  its own table below (``Z_TOE_MSL``), not the geotech CSV. One value serves as
  both the head-translation datum and the M5/M7 exit reference h_e (ADR-0007
  ``z_toe == h_e``); the former PROVISIONAL 0.0 is retired, which is what
  unblocks real (MSL-datum) M3 hydrographs past ``validate_datum_consistency``.
* **conditioning grid.** ``mc.conditioning_grid`` is now river STAGE in m MSL
  (the M3 / ADR-0021 / HWL datum), per section (``CONDITIONING_GRID_MSL``):
  sub-toe anchors + a 0.25 m sweep from just above the toe to HWL + 4 m. The
  former PROVISIONAL above-toe grid is retired.

COVs are FIXED constants (the CSV carries no COV columns); only the five geotech
*means* come from the table per row.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import yaml

from bep_reliability_engine.bank_heights import load_hwl
from bep_reliability_engine.config import Config

# --- Paths -------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "processed" / "tokachi_bep_inputs.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "configs"

# --- CSV preflight expectations ---------------------------------------------
REQUIRED_COLUMNS = {
    "kp",
    "river",
    "bank",
    "L_m",
    "D_aq_m",
    "k_aq_mps",
    "d70_m",
    "D_bl_m",
    "k_bl_mps",
    "gamma_sub_kNm3",
    "foreshore_width_m",
    "remediation_state",
}
EXPECTED_KPS = {"57.4", "58.8", "60.0", "62.0", "63.4"}
EXCLUDED_KP_DEFAULT = "63.4"

# --- Sweep axes --------------------------------------------------------------
# (config field value, filename token); '+4K' is not filename-safe.
# Historical-only per ADR-0023 (shape-invariant climate axis): the +4K
# fragility equals the historical fragility by construction — the canonical
# HPB shape drives all scenarios and the ensembles differ in peak intensity,
# not normalized shape — so the former ("+4K", "plus4k") entry is dropped;
# climate differentiation lives on the Phase 3 hazard side. The '+4K' literal
# stays in the Config schema (scenario remains the run identity).
SCENARIOS: list[tuple[str, str]] = [
    ("historical", "historical"),
]
INTERPRETATIONS: list[str] = ["matrix", "bulk"]

# --- FIXED priors (thesis prior table `tab:priors_phase1` / ADR-0016) ---------
# COVs are specification constants, identical in every config; the CSV has no
# COV columns. Means for the five geotech variables come from the CSV per row.
# These match the thesis Study-Area prior table (NOT the older architecture
# spec-section-7 table): d_70 widened to 0.30 (within-section grading), D_aq
# tightened to 0.10 (rescaled Pol absolute sigma), D_bl 0.167 (Pol absolute
# sigma; the same 0.167 the provenance doc uses for the mu_ln values). The
# corresponding mu_ln reproduce thesis Table `tab:priors_muln` (review item #2).
FIXED_COVS: dict[str, float] = {
    "k_aq": 0.50,
    "d_70": 0.30,
    "D_aq": 0.10,
    "D_bl": 0.167,
    "k_bl": 0.50,
    "gamma_bl_sub": 0.056,
    # Pol SIE 2024 Table 2 field prior: std 0.043 / mean 0.055 = 0.782 (ADR-0026).
    "C_e": 0.043 / 0.055,
}

# Per-section CoV of the stochastic seepage length L (thesis seepage-length prior
# `tab:seepage_length_prior`): 0.15 at the best-constrained KP 60.0, 0.20 at the
# remaining confined sections. L is sampled independently of theta (review #3);
# its mean is the CSV L_m. KP 63.4 (unconfined) is excluded by default.
SEEPAGE_LENGTH_COV: dict[str, float] = {
    "57.4": 0.20,
    "58.8": 0.20,
    "60.0": 0.15,
    "62.0": 0.20,
    "63.4": 0.20,
}

# gamma_bl_sub is the *blanket* submerged weight (ADR-0016), FIXED for every
# config. NOT the CSV gamma_sub_kNm3 (= aquifer particle weight gamma'_p, fed to
# F_r via the pinned sellmeijer.GAMMA_P_SUB_DEFAULT = 16.87).
GAMMA_BL_SUB_MEAN: float = 6.9

# C_e prior is FIXED at Pol's SIE 2024 Table 2 field-reliability prior
# (mean 0.055, std 0.043 => CoV 0.782), recommended by Pol (2026-07-07 meeting)
# for levee reliability calculations, superseding the ADR-0001 calibration-
# anchored (0.014, 0.50). See ADR-0026. Not OYO site data.
C_E_MEAN: float = 0.055

# --- Bulk-gravel co-primary d_70 (provenance section 3.3), in mm -------------
# These live in the provenance prose, NOT the CSV. Matrix configs read the CSV
# d70_m column instead. Converted to metres (x 1e-3) when written.
BULK_D70_MM: dict[str, float] = {
    "57.4": 5.5,
    "58.8": 13.0,
    "60.0": 1.3,
    "62.0": 13.5,
    "63.4": 9.5,
}

# d_70 sample bounds (spec section 12 failure-mode-2 clip), interpretation-
# specific: the matrix clip [50 um, 1 mm] would collapse the mm-scale bulk
# distribution onto its upper edge, so bulk gets a wide non-truncating window.
# Bulk d_70 lies far outside Sellmeijer's validated 150-430 um range, so bulk
# H_c is an extrapolation (provenance section 3.3).
D70_BOUNDS: dict[str, tuple[float, float]] = {
    "matrix": (50.0e-6, 1.0e-3),
    "bulk": (5.0e-4, 5.0e-2),
}

# --- REAL landside-toe elevations [m MSL / T.P.] (ADR-0021) -------------------
# Read from the OYO (1999) transverse soil sections (1:200, +/-0.3 m), datum
# cross-checked against the 2019 bank-height data. Each value serves as BOTH
# the head-translation datum z_toe AND the exit / polder reference h_e for
# uplift, heave and the piping exit (ADR-0007 z_toe == h_e; ADR-0021 replaces
# the foreshore-crest placeholder). The former PROVISIONAL_Z_TOE = 0.0 is
# retired. KP 63.4 is deliberately absent: excluded by default, and admitting
# it requires reading its toe from the OYO sheet first (abort, never invent).
Z_TOE_MSL: dict[str, float] = {
    "57.4": 38.3,
    "58.8": 38.5,
    "60.0": 40.0,
    "62.0": 44.9,
}


def _quarters(start_q: int, end_q: int) -> list[float]:
    """Inclusive quarter-metre range: [start_q/4, ..., end_q/4] (exact floats)."""
    return [q / 4.0 for q in range(start_q, end_q + 1)]


# --- Per-section MSL conditioning grids (approved 2026-07-03; audit gap G2) ----
# Levels are river STAGE h_i [m MSL], the same datum as the M3 hydrographs, the
# ADR-0021 toe and the 2019 HWL — the former PROVISIONAL above-toe grid is
# retired. Construction per section: three sub-toe anchors (from the base-flow
# stage h_base = Eq. 4.19 at Q = 75.44 m^3/s under the local rating, pinning
# the zero-load floor: below the toe, delta_h_blanket < 0 and the gate never
# opens) + a uniform 0.25 m sweep from just above the toe (where the uplift/
# heave transition lives) to HWL + 4 m (covering the extreme-HFB stage range,
# so the fitted curve is not extrapolated in the scenario analysis). N_h =
# 23/29/30/38 against the spec target ~30. Derivation inputs: ADR-0021 toe,
# 2019 HWL, HQrelation_TokachiRiv_2017.csv ratings (h_base = 34.77 / 36.52 /
# 38.29 / 41.70 m MSL at KP 57.4 / 58.8 / 60.0 / 62.0).
#
# KP 62.0 static-bracketing extension (ADR-0024): 0.5 m steps from 51.0 to
# 56.5 m MSL (12 levels, N_h 26 -> 38). These upper levels are HYPOTHETICAL
# fit-stabilizers — they exceed the design crest (47.89 m MSL, ADR-0021
# cross-check table) and the maximum attainable d4PDF stage (~51.5 m MSL at
# the KP 62.0 rating) — added only so the STATIC transition (P_f ~ 0.54 at
# 56.5 per the 2026-07-03 probe) is bracketed and its lognormal fit is
# data-supported. They carry no hazard weight in the fragility x hazard
# composition and must not be plotted as attainable states. The TRANSIENT
# transition (~67 m MSL) is deliberately not chased: per ADR-0024 that
# branch's deliverable is the raw tail with binomial CIs.
_KP62_STATIC_BRACKETING_EXT: list[float] = [51.0 + 0.5 * i for i in range(12)]

CONDITIONING_GRID_MSL: dict[str, list[float]] = {
    "57.4": [34.75, 36.50, 38.00, *_quarters(154, 173)],  # 38.50..43.25, N_h=23
    "58.8": [36.50, 37.50, 38.25, *_quarters(155, 180)],  # 38.75..45.00, N_h=29
    "60.0": [38.25, 39.25, 39.75, *_quarters(161, 187)],  # 40.25..46.75, N_h=30
    "62.0": [
        41.75,
        43.25,
        44.50,
        *_quarters(180, 202),  # 45.00..50.50 (0.25 m sweep to HWL + 4)
        *_KP62_STATIC_BRACKETING_EXT,  # 51.0..56.5 (ADR-0024), N_h=38
    ],
}

# --- Canonical d4PDF shape events (ADR-0020; approved 2026-07-03, gap G1) -----
# ORDERED: the first entry is the shape the run uses — HPB_m064_1987, the
# compound production default (3rd-largest HPB peak 7,214 m^3/s at t = 37 h,
# secondary peak 64% of max at t = 75 h, inter-peak trough 30%; mirrors the
# 2016 typhoon-sequence character and exercises the spec §5 memory model).
# Second: HPB_m067_1978, the isolated single-peak end-member (largest HPB peak
# 7,581 m^3/s, 32 h rise) recorded as the approved shape-sensitivity alternate
# (a sensitivity config reorders the list; selection stays config-side).
CANONICAL_EVENT_IDS: list[str] = ["HPB_m064_1987", "HPB_m067_1978"]

# Root of the raw data drop (ADR-0020): hydrographs/ + rating_curves/ beneath.
HYDROGRAPH_DATA_ROOT: str = "data/raw"

# --- k_aq-d_70 coupling (ADR-0012, accepted 2026-07-03) -----------------------
# The empirical OYO paired-record analysis selected the spec section 7/13
# two-population fallback: the matrix d_70 (Sellmeijer resistance) and the
# framework k_aq (seepage/progression) are physically distinct soils and are
# sampled decoupled. rho is carried as 0.0 for schema/audit only — required by
# CorrelationSpecs, recorded by M2 with rho_imposed=False, never imposed. The
# former PROVISIONAL_RHO_LOG = 0.6 is retired; see ADR-0012 and its companion
# analysis note (docs/decisions/adr0012-kaq-d70-analysis.md).
COUPLING_MODE: str = "two_population"
RHO_LOG_KAQ_D70: float = 0.0

# --- PROVISIONAL placeholders (flagged; await finalized schematization) ------
BASE_SEED: int = 20260626  # one shared seed -> common random numbers across the sweep

# --- Deterministic Sellmeijer inputs (ADR-0015) ------------------------------
THETA_REPOSE_DEG: float = 37.0
RELATIVE_DENSITY_INSITU: float = 0.725
ALPHA_EXPONENT: float = -1.0 / 3.0

# --- Per-section flagged overrides -------------------------------------------
# KP 62.0 remediation is "berm-uncertain" (provenance 3.2): the CSV carries
# 'unreinforced' (conservative; the value the memo lists first). One line to
# change once the current-state cross-section is confirmed.
REMEDIATION_OVERRIDES: dict[str, str] = {
    # "62.0": "berm-only",  # uncomment to switch once confirmed
}

# KP 63.4 has no A_c blanket, so k_bl -- and the k_fore proxy derived from it --
# is undefined (CSV cell = NaN). The section is excluded by default. If admitted
# with --include-kp634, set an explicit flagged proxy here; leaving it None
# aborts rather than inventing a value.
KP634_K_BL_PROXY: float | None = None


def _f(value: str) -> float:
    """Parse a CSV cell to float ('NaN' -> nan)."""
    return float(value)


def _marginal(mean: float, cov: float) -> dict[str, Any]:
    """Return one lognormal marginal spec dict (spec section 7 family)."""
    return {"family": "lognormal", "mean": mean, "cov": cov}


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    """Read and preflight the geotech CSV, failing loudly on any surprise."""
    import csv

    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(
                f"[FATAL] {csv_path}: missing required columns {sorted(missing)}."
            )
        rows = list(reader)

    kps = {row["kp"] for row in rows}
    if kps != EXPECTED_KPS:
        raise SystemExit(
            f"[FATAL] {csv_path}: expected KP set {sorted(EXPECTED_KPS)}, got "
            f"{sorted(kps)} -- the generator targets the five OYO cross-sections "
            "only (provenance section 1)."
        )
    for row in rows:
        if row["river"] != "Tokachi" or row["bank"] != "right":
            raise SystemExit(
                f"[FATAL] KP {row['kp']}: expected Tokachi/right, got "
                f"{row['river']}/{row['bank']}."
            )
    return rows


def build_config_dict(
    row: dict[str, str], scenario_value: str, interpretation: str
) -> dict[str, Any]:
    """Build one config body dict from a CSV row, scenario and interpretation."""
    kp = row["kp"]

    # k_bl from the CSV cell, except KP 63.4 (NaN, A_c absent) which needs the
    # explicit proxy; the same value feeds the k_fore foreshore proxy.
    k_bl = _f(row["k_bl_mps"])
    if math.isnan(k_bl):
        if KP634_K_BL_PROXY is None:
            raise SystemExit(
                f"[FATAL] KP {kp}: k_bl is undefined in the CSV (A_c blanket "
                "absent). Set KP634_K_BL_PROXY at the top of "
                "scripts/generate_configs.py to an explicit, flagged proxy "
                "before generating a config for this section (it also feeds the "
                "k_fore foreshore proxy)."
            )
        k_bl = KP634_K_BL_PROXY

    d_bl = _f(row["D_bl_m"])

    if interpretation == "matrix":
        d70_mean = _f(row["d70_m"])
    else:  # bulk
        d70_mean = BULK_D70_MM[kp] * 1.0e-3

    remediation = REMEDIATION_OVERRIDES.get(kp, row["remediation_state"])

    # ADR-0021 toe + approved MSL grid: both tables cover exactly the four
    # confined sections. A missing KP (i.e. 63.4 admitted via --include-kp634)
    # aborts loudly — its toe must be read from the OYO sheet and a grid
    # derived before a config can exist for it (never invent an elevation).
    try:
        z_toe_msl = Z_TOE_MSL[kp]
        conditioning_grid = CONDITIONING_GRID_MSL[kp]
    except KeyError:
        raise SystemExit(
            f"[FATAL] KP {kp}: no ADR-0021 landside-toe elevation / approved "
            "MSL conditioning grid is defined for this section. Add the toe "
            "(read from the OYO transverse sheet) to Z_TOE_MSL and derive its "
            "grid into CONDITIONING_GRID_MSL in scripts/generate_configs.py "
            "before generating a config for it."
        ) from None

    return {
        "cross_section_id": f"tokachi_kp{kp}",
        "segment_id": f"KP{kp}",
        "scenario": scenario_value,
        "remediation_state": remediation,
        "geometry": {
            "L": _f(row["L_m"]),
            # ADR-0021 landside toe [m MSL]: head-translation datum AND exit
            # reference h_e in one value (ADR-0007 z_toe == h_e).
            "z_toe": z_toe_msl,
            "foreshore_width": _f(row["foreshore_width_m"]),
            "D_fore": d_bl,  # per-section proxy = landside D_bl (ADR-0005)
            "k_fore": k_bl,  # per-section proxy = landside k_bl (ADR-0005)
            # Official 2019 design HWL [m MSL], strict per-KP lookup (ADR-0018)
            "HWL": load_hwl(row["river"], float(kp)),
        },
        "priors": {
            "k_aq": _marginal(_f(row["k_aq_mps"]), FIXED_COVS["k_aq"]),
            "d_70": _marginal(d70_mean, FIXED_COVS["d_70"]),
            "D_aq": _marginal(_f(row["D_aq_m"]), FIXED_COVS["D_aq"]),
            "D_bl": _marginal(d_bl, FIXED_COVS["D_bl"]),
            "k_bl": _marginal(k_bl, FIXED_COVS["k_bl"]),
            "gamma_bl_sub": _marginal(GAMMA_BL_SUB_MEAN, FIXED_COVS["gamma_bl_sub"]),
            "C_e": _marginal(C_E_MEAN, FIXED_COVS["C_e"]),
            "bounds": {"d_70": list(D70_BOUNDS[interpretation])},
            "d70_interpretation": interpretation,
        },
        # ADR-0012: two-population decoupling; rho recorded (0.0), never imposed.
        "correlation": {
            "rho_log_kaq_d70": RHO_LOG_KAQ_D70,
            "coupling": COUPLING_MODE,
        },
        "mc": {
            "n_samples": 100_000,
            "seed": BASE_SEED,
            # Approved per-section MSL stage grid (see CONDITIONING_GRID_MSL).
            "conditioning_grid": list(conditioning_grid),
            "sampling_scheme": "latin_hypercube",
        },
        "timestepper": {
            "integration_scheme": "forward_euler",
            "target_dt_seconds": None,
            "convergence_test": False,
            "convergence_threshold": 0.01,
            "aquifer_lag_active": False,
            "specific_storage_per_m": None,
        },
        "output": {
            "store_trajectories": False,
            "persistence_format": "hdf5",
            "results_dir": "results",
        },
        # ADR-0020: d4PDF source location + the ordered canonical shape events.
        # River/KP are explicit config data (never parsed from the ID strings);
        # the rating path, experiment (HPB/HFB) and band workbook are derived
        # downstream by M3 (rating_curve_path / experiment_for_scenario /
        # resolve_band_workbook, incl. the ADR-0019 §7 KP 62.x proxy routing).
        "hydrograph_source": {
            "data_root": HYDROGRAPH_DATA_ROOT,
            "river": row["river"],
            "kp": float(kp),
            "canonical_event_ids": list(CANONICAL_EVENT_IDS),
        },
        "theta_repose_deg": THETA_REPOSE_DEG,
        "relative_density_insitu": RELATIVE_DENSITY_INSITU,
        "alpha_exponent": ALPHA_EXPONENT,
        "seepage_length_cov": SEEPAGE_LENGTH_COV[kp],
        # ADR-0025: blanketed foreland is the adopted baseline at every
        # section (emitted explicitly for provenance, though it is the
        # default). The open-entry end is an on-demand sensitivity run from a
        # hand-derived config with foreland_treatment: open_entry — never a
        # generated sweep member.
        "foreland_treatment": "blanketed_tanh",
    }


def config_filename(kp: str, scenario_token: str, interpretation: str) -> str:
    """Return ``kp57_4_historical_matrix.yaml``-style unambiguous filename."""
    return f"kp{kp.replace('.', '_')}_{scenario_token}_{interpretation}.yaml"


def header_comment(
    kp: str, scenario_value: str, interpretation: str, gamma_p_csv: str
) -> str:
    """Build the provenance header comment block for one generated config."""
    sep = "# " + "=" * 70
    lines: list[str] = [
        sep,
        f"# GENERATED -- Tokachi KP {kp}, scenario {scenario_value}, "
        f"d70 {interpretation}",
        "# Source: data/processed/tokachi_bep_inputs.csv via "
        "scripts/generate_configs.py",
        "# Do not hand-edit; re-run the generator.",
        "#",
        "# REAL (CSV per section): L, foreshore_width; means of k_aq,",
        "#   d_70(matrix), D_aq, D_bl, k_bl; remediation_state.",
        "# REAL (2019 bank-height CSV, data/raw/geometry): geometry.HWL",
        "#   [m MSL] per river/KP (ADR-0018); DesignBankHeight_* never read.",
        "# REAL (ADR-0021, OYO 1999 transverse sections, +/-0.3 m): geometry.z_toe",
        "#   [m MSL] = the landside-toe elevation, serving as BOTH the head-",
        "#   translation datum and the exit reference h_e (ADR-0007 z_toe == h_e).",
        "# DERIVED (ADR-0021 toe + 2019 HWL + rating h_base; approved 2026-07-03):",
        "#   mc.conditioning_grid = per-section MSL STAGE levels (sub-toe anchors",
        "#   + 0.25 m sweep to HWL + 4 m); same datum as the M3 hydrographs.",
        "# ADR-0020: hydrograph_source pins the d4PDF drop + the ORDERED canonical",
        "#   shape events (first = production compound HPB_m064_1987; second =",
        "#   isolated sensitivity end-member HPB_m067_1978).",
        "# FIXED (spec 7 / ADR-0016 / Pol 2024): all COVs; gamma_bl_sub",
        "#   (6.9, 0.056); C_e (0.055, 0.782) [SIE 2024 Tab 2, ADR-0026];",
        "#   theta_repose_deg; D_r; alpha.",
        "# ADR-0012: k_aq-d_70 coupling = two_population (empirical OYO result;",
        "#   matrix d_70 and framework k_aq are distinct soils, sampled",
        "#   decoupled). rho_log_kaq_d70 = 0.0 is schema/audit only, never",
        "#   imposed; the former provisional 0.6 is retired.",
        "# ADR-0025: foreland_treatment = blanketed_tanh (adopted baseline;",
        "#   open_entry is an on-demand sensitivity, never a sweep member).",
        "# PROVISIONAL: seed;",
        "#   D_fore/k_fore = landside D_bl/k_bl proxy (ADR-0005).",
        f"# gamma: CSV gamma_sub_kNm3 = {gamma_p_csv} kN/m^3 is the per-section",
        "#   aquifer particle weight gamma'_p (Sellmeijer F_r). It is recorded here",
        "#   for the audit trail ONLY and is NOT used: the run uses the canonical",
        "#   basin-wide deterministic gamma'_p = 16.87 (the pinned constant",
        "#   sellmeijer.GAMMA_P_SUB_DEFAULT), per the review-item-#10 decision.",
        "#   gamma'_p is not a config field (ADR-0016); gamma_bl_sub below is the",
        "#   distinct stochastic BLANKET weight that drives uplift/heave.",
    ]
    if interpretation == "bulk":
        lines.append("# bulk: d_70 is the bulk-gravel co-primary (provenance 3.3), far")
        lines.append("#   outside Sellmeijer's 150-430 um range; H_c is extrapolated.")
    if kp == "62.0":
        lines.append("# KP62: remediation 'unreinforced' is berm-uncertain (3.2);")
        lines.append("#   conservative best estimate -- see REMEDIATION_OVERRIDES.")
    if kp == EXCLUDED_KP_DEFAULT:
        lines.append(
            "# KP63.4: unconfined, A_c absent; confined-BEP mechanism mismatched."
        )
        lines.append("#   Admitted via --include-kp634 with an explicit k_bl proxy.")
    lines.append(sep)
    return "\n".join(lines) + "\n\n"


def main(argv: list[str] | None = None) -> None:
    """Generate, write, and reload-validate the Tokachi config sweep."""
    parser = argparse.ArgumentParser(
        description="Generate validated Tokachi BEP run configs from the geotech CSV."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Input CSV path.")
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory."
    )
    parser.add_argument(
        "--include-kp634",
        action="store_true",
        help="Admit KP 63.4 (excluded by default; requires KP634_K_BL_PROXY).",
    )
    args = parser.parse_args(argv)

    rows = read_rows(args.csv)

    # --- KP 63.4 gating: explicit in both directions, never silent ----------
    selected: list[dict[str, str]] = []
    for row in rows:
        if row["kp"] == EXCLUDED_KP_DEFAULT:
            if not args.include_kp634:
                print(
                    f"[skip] KP {row['kp']} excluded by default (unconfined, A_c "
                    "absent; provenance 3.1/3.5). Pass --include-kp634 to admit it."
                )
                continue
            print(f"[include] KP {row['kp']} admitted via --include-kp634.")
        selected.append(row)

    # --- Build + in-memory validate everything BEFORE writing ---------------
    # (so a single bad config aborts with no partial output on disk).
    planned: list[tuple[Path, str, dict[str, Any], Config]] = []
    for row in selected:
        kp = row["kp"]
        for scenario_value, scenario_token in SCENARIOS:
            for interpretation in INTERPRETATIONS:
                body = build_config_dict(row, scenario_value, interpretation)
                try:
                    cfg = Config.model_validate(body)
                except Exception as exc:  # pydantic.ValidationError and friends
                    raise SystemExit(
                        f"[FATAL] In-memory schema validation failed for KP {kp} "
                        f"{scenario_value} {interpretation}: {exc}"
                    ) from exc
                filename = config_filename(kp, scenario_token, interpretation)
                path = args.out_dir / filename
                header = header_comment(
                    kp, scenario_value, interpretation, row["gamma_sub_kNm3"]
                )
                planned.append((path, header, body, cfg))

    if not planned:
        raise SystemExit("[FATAL] No cross-sections selected; nothing to generate.")

    # --- Write all ----------------------------------------------------------
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for path, header, body, _cfg in planned:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(header)
            yaml.safe_dump(body, handle, sort_keys=False, default_flow_style=False)

    # --- Reload pass: every file back through from_yaml; assert it validates -
    failures: list[tuple[Path, str]] = []
    for path, _header, _body, cfg in planned:
        try:
            reloaded = Config.from_yaml(path)
        except Exception as exc:  # pydantic.ValidationError, parse errors
            failures.append((path, f"from_yaml raised: {exc}"))
            continue
        if reloaded.config_hash() != cfg.config_hash():
            failures.append(
                (path, "round-trip mismatch: reloaded config_hash != in-memory")
            )
    if failures:
        for path, message in failures:
            print(f"[FAIL] {path.name}: {message}")
        raise SystemExit(
            f"[FATAL] {len(failures)} of {len(planned)} configs failed schema "
            "reload validation."
        )

    # --- Summary ------------------------------------------------------------
    per_section: dict[str, int] = {}
    for _path, _header, body, _cfg in planned:
        per_section[body["segment_id"]] = per_section.get(body["segment_id"], 0) + 1

    print(
        f"\nAll {len(planned)} configs reload-validated cleanly via "
        "Config.from_yaml."
    )
    print(f"Wrote {len(planned)} configs to {args.out_dir}")
    print("\nPer-cross-section count (expect 4 = 2 scenarios x 2 interpretations):")
    for segment_id in sorted(per_section):
        print(f"  {segment_id}: {per_section[segment_id]}")
    print(
        f"\nSweep: {len(per_section)} cross-sections x {len(SCENARIOS)} scenarios "
        f"x {len(INTERPRETATIONS)} interpretations = {len(planned)} configs."
    )


if __name__ == "__main__":
    main()
