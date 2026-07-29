"""ADR-0048 companion: quantify the prior-mean epistemic scenarios vs baseline.

The 2005/06 + 2013 Kunijiban borehole drop (``data/raw/borehole_and_soil_survey/``)
put two production prior *means* under independent scrutiny:

* **k_aq (primary).** The production table anchors ``k_aq`` to the OYO 様式-5
  "analysis constants" (1.0e-3 .. 3.0e-3 m/s). The field-permeability
  population now has six members across two independent campaigns — four OYO
  1999 tests recorded but set aside in provenance §3.6, plus two 2005/06
  single-borehole tests at the Satsunai confluence site (5.15e-4 m/s at the
  landside toe, 8.61e-5 m/s on the riverside) — with geometric mean
  5.94e-5 m/s, i.e. 17-51x below the adopted constants. Under the production
  Lognormal(mean, CoV 0.50) the lower field value sits 5.0-7.3 sigma below the
  prior median, so the disagreement is a *mean* offset the CoV cannot carry.
* **gamma_bl_sub (secondary).** Three in-situ sand-replacement densities on
  cover material (1.61 / 1.64 / 1.86 g/cm3) give gamma_t - gamma_w =
  5.98 / 6.28 / 8.44 kN/m3, which *bracket* the 6.90 kN/m3 prior mean rather
  than contradicting it. Only the lower end is run, as a bounding case.

For each persisted production sweep given (default: the two informative matrix
sections KP58.8 and KP60.0), this driver

1. reconstructs the run's exact Config from its own metadata snapshot
   (hash-checked), so the comparison is against the frozen baseline under
   identical assumptions;
2. re-runs the full sweep once per scenario with the ADR-0048
   ``prior_mean_scenario`` block enabled — grid, seed, L draw, hydrographs and
   every other prior all identical, only the named prior mean moved;
3. writes each companion FragilityResult under
   ``results/sensitivity/adr0048_prior_means/`` (never touching the baseline
   files) and the per-level comparison table to
   ``docs/decisions/adr0048-prior-mean-companion.json``.

The baseline is NEVER regenerated: it is loaded read-only from ``results/``.
Scenario factors are computed per section from that section's own prior mean,
so a scenario is specified as an absolute **target mean**, not a factor.

Usage (from the repo root, venv active)::

    python scripts/prior_mean_scenario_companion.py               # both sections
    python scripts/prior_mean_scenario_companion.py --n-jobs 4 \
        results/tokachi_kp58.8_historical_matrix.h5               # one section
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bep_reliability_engine.config import Config, PriorMeanScenario  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402

DEFAULT_BASELINES = [
    "results/tokachi_kp58.8_historical_matrix.h5",
    "results/tokachi_kp60.0_historical_matrix.h5",
]
OUT_DIR = REPO_ROOT / "results" / "sensitivity" / "adr0048_prior_means"
JSON_OUT = REPO_ROOT / "docs" / "decisions" / "adr0048-prior-mean-companion.json"

# (label, parameter, target mean [SI], provenance one-liner). Ordered as a
# descending ladder on k_aq so the JSON reads baseline -> toe test -> field GM.
SCENARIOS: list[tuple[str, str, float, str]] = [
    (
        "k_aq_field_toe",
        "k_aq",
        5.15e-4,
        "KP1.8R-2 landside-toe field permeability, 5.15E-02 cm/s (2005/06 campaign)",
    ),
    (
        "k_aq_field_geomean",
        "k_aq",
        5.94e-5,
        "geometric mean of the six-member field-test population (4 OYO 1999 + 2 new)",
    ),
    (
        "gamma_bl_sub_lower",
        "gamma_bl_sub",
        6.0,
        "lowest of three in-situ sand-replacement densities (1.61 g/cm3 -> 5.98)",
    ),
    (
        "k_aq_regional_upper",
        "k_aq",
        1.0e-2,
        "upper end of the Chiyoda new-channel regional band 1e-3..1e-2 m/s "
        "(tokachi_chisuishi_2023); the unconservative end of the bracket, "
        "flagged in the thesis Discussion as beyond the prior's 95th percentile",
    ),
]


def _ratio(numer: np.ndarray, denom: np.ndarray) -> list[float | None]:
    """Elementwise numer/denom with None where the baseline is exactly 0."""
    return [None if b == 0.0 else float(a / b) for a, b in zip(numer, denom)]


def _load_baseline(path: Path) -> tuple[FragilityResult, Config]:
    baseline = FragilityResult.load(path)
    config = Config.model_validate(baseline.metadata["config"])
    recorded = baseline.metadata.get("config_hash")
    if recorded is not None and config.config_hash() != recorded:
        raise ValueError(
            f"{path.name}: reconstructed config hash does not match the "
            "recorded config_hash; refusing to compare against drifted "
            "assumptions."
        )
    if config.prior_mean_scenario is not None:
        raise ValueError(
            f"{path.name}: baseline already carries a prior_mean_scenario "
            "block; this driver expects the scenario-off production baseline."
        )
    return baseline, config


def run_scenario(
    baseline: FragilityResult,
    config: Config,
    stem: str,
    *,
    label: str,
    param: str,
    target: float,
    basis: str,
    n_jobs: int,
    overwrite: bool,
) -> dict:
    prior_mean = float(getattr(config.priors, param).mean)
    factor = target / prior_mean
    variant = config.model_copy(
        update={
            "prior_mean_scenario": PriorMeanScenario(
                enabled=True, label=label, factors={param: factor}
            )
        }
    )
    out_path = OUT_DIR / f"{stem}_{label}.h5"
    print(
        f"[{stem}] {label}: {param} mean {prior_mean:.3e} -> {target:.3e} "
        f"(x{factor:.4f}) ..."
    )
    companion = run_fragility_analysis(
        variant, n_jobs=n_jobs, progress=True, output_path=out_path, overwrite=overwrite
    )

    grid = np.asarray(baseline.conditioning_grid, dtype=float)
    if not np.array_equal(grid, np.asarray(companion.conditioning_grid, dtype=float)):
        raise RuntimeError("companion grid differs from baseline grid")

    base_stat = np.asarray(baseline.P_f_static_raw, float)
    base_tran = np.asarray(baseline.P_f_trans_raw, float)
    comp_stat = np.asarray(companion.P_f_static_raw, float)
    comp_tran = np.asarray(companion.P_f_trans_raw, float)

    entry = {
        "label": label,
        "parameter": param,
        "basis": basis,
        "companion_file": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "prior_mean_baseline": prior_mean,
        "prior_mean_scenario": target,
        "factor": factor,
        "p_f_static_baseline": base_stat.tolist(),
        "p_f_static_scenario": comp_stat.tolist(),
        "p_f_trans_baseline": base_tran.tolist(),
        "p_f_trans_scenario": comp_tran.tolist(),
        "ratio_static": _ratio(comp_stat, base_stat),
        "ratio_trans": _ratio(comp_tran, base_tran),
    }

    print(
        f"  {'stage':>7s} {'Pf_st base':>11s} {'Pf_st scen':>11s} {'ratio':>7s}"
        f" {'Pf_tr base':>11s} {'Pf_tr scen':>11s} {'ratio':>7s}"
    )
    for i, level in enumerate(grid):
        rs, rt = entry["ratio_static"][i], entry["ratio_trans"][i]
        print(
            f"  {level:7.2f} {base_stat[i]:11.3e} {comp_stat[i]:11.3e} "
            f"{'-' if rs is None else format(rs, '7.3f')} "
            f"{base_tran[i]:11.3e} {comp_tran[i]:11.3e} "
            f"{'-' if rt is None else format(rt, '7.3f')}"
        )
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "baselines",
        nargs="*",
        default=DEFAULT_BASELINES,
        help="Persisted baseline HDF5 files (default: the two informative "
        "matrix sections).",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Run just one scenario label (default: all three).",
    )
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--overwrite", action="store_true", default=True)
    args = parser.parse_args(argv)

    scenarios = [s for s in SCENARIOS if args.only is None or s[0] == args.only]
    if not scenarios:
        parser.error(f"--only {args.only!r} matches no scenario label")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sections = []
    for raw in args.baselines:
        path = (REPO_ROOT / raw) if not Path(raw).is_absolute() else Path(raw)
        baseline, config = _load_baseline(path)
        grid = np.asarray(baseline.conditioning_grid, dtype=float)
        sections.append(
            {
                "baseline_file": path.name,
                "cross_section_id": config.cross_section_id,
                "d70_interpretation": config.priors.d70_interpretation,
                "n_samples": int(config.mc.n_samples),
                "z_toe_m_msl": float(config.geometry.z_toe),
                "grid_m_msl": grid.tolist(),
                "scenarios": [
                    run_scenario(
                        baseline,
                        config,
                        path.stem,
                        label=label,
                        param=param,
                        target=target,
                        basis=basis,
                        n_jobs=args.n_jobs,
                        overwrite=args.overwrite,
                    )
                    for label, param, target, basis in scenarios
                ],
            }
        )

    # Merge into any existing payload so a --only run extends the record
    # rather than truncating it to the single scenario just executed.
    payload = {
        "adr": "0048",
        "description": (
            "Companion sensitivity: prior-mean epistemic scenarios (k_aq "
            "field-test population vs the OYO Form-5 analysis constants vs the "
            "regional upper band; gamma_bl_sub in-situ lower bound) against the "
            "frozen scenario-off production baseline. Baseline files untouched."
        ),
        "sections": sections,
    }
    if JSON_OUT.exists():
        prior = json.loads(JSON_OUT.read_text())
        by_file = {s["baseline_file"]: s for s in prior.get("sections", [])}
        for section in payload["sections"]:
            existing = by_file.get(section["baseline_file"])
            if existing is None:
                by_file[section["baseline_file"]] = section
                continue
            merged = {s["label"]: s for s in existing["scenarios"]}
            merged.update({s["label"]: s for s in section["scenarios"]})
            existing.update(
                {k: v for k, v in section.items() if k != "scenarios"},
            )
            existing["scenarios"] = list(merged.values())
        payload["sections"] = list(by_file.values())
    JSON_OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {JSON_OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
