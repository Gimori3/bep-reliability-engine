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

COVs are FIXED constants (the CSV carries no COV columns); only the five geotech
*means* come from the table per row.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import yaml

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
SCENARIOS: list[tuple[str, str]] = [
    ("historical", "historical"),
    ("+4K", "plus4k"),
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
    "C_e": 0.50,
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

# C_e prior is FIXED from Pol 2024 calibration (not OYO site data).
C_E_MEAN: float = 0.014

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

# --- PROVISIONAL placeholders (flagged; await finalized schematization) ------
PROVISIONAL_Z_TOE: float = 0.0  # exit-point polder elevation [m]; datum convention
PROVISIONAL_RHO_LOG: float = 0.6  # rho(ln k_aq, ln d_70); estimate from OYO pairs
PROVISIONAL_GRID: list[float] = [  # conditioning levels [m above toe]; target N_h~30
    4.0,
    4.5,
    5.0,
    5.5,
    6.0,
    6.5,
    7.0,
    7.5,
    8.0,
    8.5,
    9.0,
]
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

    return {
        "cross_section_id": f"tokachi_kp{kp}",
        "segment_id": f"KP{kp}",
        "scenario": scenario_value,
        "remediation_state": remediation,
        "geometry": {
            "L": _f(row["L_m"]),
            "z_toe": PROVISIONAL_Z_TOE,
            "foreshore_width": _f(row["foreshore_width_m"]),
            "D_fore": d_bl,  # per-section proxy = landside D_bl (ADR-0005)
            "k_fore": k_bl,  # per-section proxy = landside k_bl (ADR-0005)
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
        "correlation": {
            "rho_log_kaq_d70": PROVISIONAL_RHO_LOG,
            "coupling": "correlated",
        },
        "mc": {
            "n_samples": 100_000,
            "seed": BASE_SEED,
            "conditioning_grid": list(PROVISIONAL_GRID),
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
        "theta_repose_deg": THETA_REPOSE_DEG,
        "relative_density_insitu": RELATIVE_DENSITY_INSITU,
        "alpha_exponent": ALPHA_EXPONENT,
        "seepage_length_cov": SEEPAGE_LENGTH_COV[kp],
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
        "# FIXED (spec 7 / ADR-0016 / Pol 2024): all COVs; gamma_bl_sub",
        "#   (6.9, 0.056); C_e (0.014, 0.50); theta_repose_deg; D_r; alpha.",
        "# PROVISIONAL: z_toe, rho_log_kaq_d70, conditioning_grid, seed;",
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
