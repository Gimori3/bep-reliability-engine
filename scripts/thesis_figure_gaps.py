"""Publication figures for the highest-value gaps in the thesis inventory.

``docs/thesis_number_inventory_2026-07-30.md`` names numbers that carry high
thesis value and have no figure anywhere. This driver builds them, their
table-source CSVs, and the committed evidence slices three of them need.

| # | inventory | figure |
|---|---|---|
| 1 | 4.1, 4.2, 5.2 | ``phase2_survival_update.png`` |
| 2 | 7.1 | ``epistemic_bracket_ranking.png`` |
| 3 | 2.5 | ``adr0040_kp57_4_bound.png`` |
| 4 | 6.10 | ``rq4_sensitivity_brackets.png`` |
| 5 | 7.15, 7.16 | ``epistemic_knobs_mp_ztoe.png`` |
| 6 | 4.7 | ``phase2_peak_shortcut.png`` (added 2026-08-02) |

**Why there is an ``extract`` command.** Figures 1, 4 and 6 are sourced from
``results/production_campaign_manifest.json``,
``results/system_integration/phase3/rq4_annual.csv`` and the persisted Phase 1
sweeps plus Phase 2 posteriors, and ``results/`` is gitignored -- a thesis figure
whose only source is a machine-local artifact does not regenerate on a fresh
clone. ``extract`` reads those artifacts and writes the slice each figure needs
to ``docs/decisions/``, recording the source path and its SHA-256 so the
provenance chain stays explicit and checkable (a test compares the recorded
digest against the live artifact whenever it is present). ``figures`` then reads
**only committed evidence**, which is what gate G7 binds to.

Inventory rows 4.3, 4.4 and 5.1 are *not* here: they are Phase 2 diagnostics
rendered by ``bayesian_reliability_updating.pipeline._figures``, which gained
its own dual-write seam on 2026-08-02 (``pipeline.PUBLICATION_FIGURES``).

Commands::

    python scripts/thesis_figure_gaps.py extract  # gitignored -> docs/decisions/
    python scripts/thesis_figure_gaps.py figures  # committed evidence -> PNG + CSV
    python scripts/thesis_figure_gaps.py all      # both, in order

``figures`` is the cheap redraw path the campaign's figure stage runs; it touches
no evidence file and runs no physics. No physics runs anywhere in this module.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _figstyle as figstyle  # noqa: E402

DECISIONS = REPO_ROOT / "docs" / "decisions"
OUT_DIR = REPO_ROOT / "results" / "thesis_figure_gaps"
MIRROR = OUT_DIR / "figures"

# --- gitignored inputs, read only by ``extract`` ------------------------------
CAMPAIGN_MANIFEST = REPO_ROOT / "results" / "production_campaign_manifest.json"
RQ4_ANNUAL = REPO_ROOT / "results" / "system_integration" / "phase3" / "rq4_annual.csv"
PHASE1_RESULTS = REPO_ROOT / "results"
PHASE2_RESULTS = REPO_ROOT / "results" / "phase2"

# --- committed evidence, the only thing ``figures`` reads ---------------------
PHASE2_SLICE = DECISIONS / "phase2-survival-update-per-stratum.json"
PEAK_SHORTCUT_SLICE = DECISIONS / "phase2-peak-shortcut.json"
RQ4_SLICE = DECISIONS / "phase3-sensitivity-brackets.json"
SYNTHESIS = DECISIONS / "epistemic-bracket-synthesis.json"
HWL_EVIDENCE = DECISIONS / "adr0040-hwl-bias-resolution.json"
MP_COMPANION = DECISIONS / "adr0045-mp-companion.json"
ZTOE_COMPANION = DECISIONS / "adr0046-ztoe-companion.json"
#: Source of truth for ADR-0024's ``attainable_max_m``; read, never duplicated.
STAGE66_KP62 = DECISIONS / "adr0040-stage6-6-kp62_0-analysis.json"

SECTIONS = ("KP57.4", "KP58.8", "KP60.0", "KP62.0")

#: The eight production strata, in the order the campaign reports them.
STRATA = tuple(
    f"tokachi_kp{kp}_historical_{d70}"
    for kp in ("57.4", "58.8", "60.0", "62.0")
    for d70 in ("matrix", "bulk")
)

#: Below this many rejected rows the over-rejection factor is a ratio of two
#: small counts and is labelled as such rather than quoted as a measurement.
#: ``docs/phase2_report.md`` section 11.1 calls KP 57.4 (65 rejected rows of
#: 1e5) the "small-number regime"; KP 60.0 bulk, at 23, is further into it.
SMALL_NUMBER_ROWS = 500

#: The three documented Phase 2 readings, in the order the campaign ran them.
PHASE2_RUNS = (
    ("baseline", "phase2_baseline", "no_breach (the deliverable)"),
    ("anchor_rating", "phase2_anchor_rating", "anchor construction: rating"),
    ("no_initiation", "phase2_no_initiation", "criterion: no breach AND no initiation"),
)

#: Plain-English rendering of a run description, for figure text only. The
#: descriptions above are carried verbatim into the committed slice
#: ``docs/decisions/phase2-survival-update-per-stratum.json``, so they name the
#: acceptance criterion exactly as the Phase 2 record does and must not change;
#: a main-body thesis figure may not print that field name.
RUN_DISPLAY_NAMES = {"no_breach (the deliverable)": "no breach (the deliverable)"}

#: ``rq4_annual.csv`` arms, as (label, column overrides against the baseline).
#: The baseline is the production deliverable: matrix d70, posterior BEP source,
#: lambda_ac = 250 m (ADR-0037 primary), primary surface variant.
RQ4_BASELINE = {
    "d70": "matrix",
    "bep_source": "posterior",
    "lambda_ac_m": "250.0",
    "surface_variant": "primary",
}
RQ4_ARMS = (
    ("lambda_ac_100m", {"lambda_ac_m": "100.0"}),
    ("lambda_ac_40m", {"lambda_ac_m": "40.0"}),
    ("bulk_d70", {"d70": "bulk"}),
    ("prior_bep", {"bep_source": "prior"}),
)

#: Anchors of the epistemic ranking, in stage order within a section's grid.
ANCHORS = (
    "lowest_reachable",
    "rising_limb",
    "design_hwl",
    "transition_midpoint",
    "grid_top",
)
#: The two anchors that carry the thesis's claims (synthesis note section 3).
RANKING_PANEL_ANCHORS = ("design_hwl", "transition_midpoint")

#: Brackets that are epistemic knobs, versus the two statistical yardsticks they
#: are ranked against. Order within each group is computed from the data.
STATISTICAL_BRACKETS = ("clopper_pearson", "mc_cov")

BRACKET_LABEL = {
    "k_aq_prior_mean": r"$k_\mathrm{aq}$ prior mean",
    "cov_L": r"CoV($L$) 0.10 to 0.40",
    "z_toe": r"$z_\mathrm{toe}$ $\pm$0.3 m",
    "L_measurement": r"$L$ measurement",
    "m_p": r"$m_p$ model factor",
    "gamma_bl_sub_prior_mean": r"$\gamma'_\mathrm{bl}$ prior mean",
    "clopper_pearson": "Clopper-Pearson (95%)",
    "mc_cov": "Monte Carlo CoV (target)",
}

#: Arms excluded from the per-bracket cancellation summary, with the reason.
#: ADR-0047 measured KP 57.4's all-station median at 67 m and showed it is road
#: fill, not the levee: the section yields no adoptable number, so its departure
#: is not a property of the L bracket. The synthesis note's own section 4(c)
#: table quotes the clean arm (2.25), which this exclusion reproduces.
CANCELLATION_ARM_EXCLUSIONS = {"L_dem_all_stations_median"}

#: Brackets that move only one branch, so a rho near 1 is not cancellation.
#: ADR-0028 separated the static limit state from the uplift/heave gate, and
#: gamma'_bl enters only the gate: its static ratio is exactly 1.000 at every
#: level. It must never be read as a second common-mode knob beside m_p.
SINGLE_BRANCH_BRACKETS = {"gamma_bl_sub_prior_mean"}

#: The only bracket that cancels, and why it is the only one. ADR-0045 section 2
#: applies m_p to the single-source H_c in BOTH its uses (static comparator and
#: transient H_eq anchor), so it is pure common-mode by construction.
COMMON_MODE_BRACKET = "m_p"


# --------------------------------------------------------------------------- #
# Small shared helpers                                                          #
# --------------------------------------------------------------------------- #


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO_ROOT).as_posix()}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(path: Path, why: str) -> Path:
    """Fail loudly on a missing input rather than writing a partial record."""
    if not path.is_file():
        raise SystemExit(
            f"missing input: {path.relative_to(REPO_ROOT).as_posix()}\n  needed for: "
            f"{why}"
        )
    return path


def _write_csv(
    name: str, fieldnames: Sequence[str], rows: list[dict[str, Any]]
) -> Path:
    """Write a figure's underlying numbers so a chapter can typeset the table.

    The figure is the argument and the CSV is the table source; both come from
    the same evidence in the same call, so they cannot drift apart.
    """
    path = DECISIONS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(fieldnames), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(REPO_ROOT).as_posix()}")
    return path


def _section_of(stem: str) -> str:
    """``tokachi_kp58.8_historical_matrix`` -> ``KP58.8``."""
    return "KP" + stem.split("_kp")[1].split("_")[0]


def _d70_of(stem: str) -> str:
    return stem.rsplit("_", 1)[1]


def _fmt_span(value: float | None) -> str:
    """Render a span factor, keeping ``unbounded`` unbounded.

    A span whose smaller end is exactly zero failures is unbounded. Clipping it
    to a finite number would read as a measurement, so it never becomes one --
    in the CSV it is the literal string ``unbounded``.
    """
    if value is None:
        return "unbounded"
    if value >= 100.0:
        return f"{value:.3g}"
    return f"{value:.2f}"


def _attainable_max_kp62() -> float:
    """ADR-0024's attainable maximum stage at KP 62.0, read from the record.

    The 51.0 to 56.5 m grid extension exists only to stabilise the lognormal
    fit. Every figure whose x axis crosses this value shades the region beyond
    it (``_figstyle.mark_hypothetical``); the value itself is never duplicated
    here, it is read from the Stage 6.6 analysis record.
    """
    return float(_read_json(STAGE66_KP62)["attainable_max_m"])


# --------------------------------------------------------------------------- #
# extract: gitignored campaign artifacts -> committed evidence slices           #
# --------------------------------------------------------------------------- #


def extract_phase2_slice() -> dict[str, Any]:
    """Slice the per-stratum Phase 2 survival result out of the campaign manifest.

    The central Bayesian claim of the thesis lives, as of the 2026-07-29
    campaign, only inside a 136 KB gitignored manifest. This lifts the 16 runs
    it covers into a committed record of the shape a figure and a table need.
    """
    _require(CAMPAIGN_MANIFEST, "the Phase 2 per-stratum survival result")
    manifest = _read_json(CAMPAIGN_MANIFEST)
    stages = manifest["stages"]

    runs: list[dict[str, Any]] = []
    for label, stage_key, description in PHASE2_RUNS:
        stage = stages[stage_key]
        strata = []
        for stem, record in stage["per_stratum"].items():
            strata.append(
                {
                    "stratum": stem,
                    "section": _section_of(stem),
                    "d70": _d70_of(stem),
                    "n_prior": record["n_prior"],
                    "n_accepted": record["n_accepted"],
                    "criterion": record["criterion"],
                    "f_static_reject": record["f_static_reject"],
                    "f_trans_reject": record["f_trans_reject"],
                    "f_marginal_transient": record["f_marginal_transient"],
                    "rejection_fraction": record["rejection_fraction"],
                    "flag_mismatch_static": record["flag_mismatch_static"],
                    "flag_mismatch_trans": record["flag_mismatch_trans"],
                    "verified": record["verified"],
                    "hash_current": record["hash_current"],
                }
            )
        runs.append(
            {
                "run": label,
                "stage": stage_key,
                "description": description,
                "campaign_description": stage.get("description"),
                "n_strata": len(strata),
                "strata": strata,
            }
        )

    every = [s for run in runs for s in run["strata"]]
    totals = {
        "n_runs": len(every),
        "n_variant_runs": len(every) - len(runs[0]["strata"]),
        "marginal_transient_all_zero": all(
            s["f_marginal_transient"] == 0.0 for s in every
        ),
        "max_marginal_transient": max(s["f_marginal_transient"] for s in every),
        "flag_mismatches_total": sum(
            s["flag_mismatch_static"] + s["flag_mismatch_trans"] for s in every
        ),
        "verified_all": all(s["verified"] for s in every),
        "hash_current_all": all(s["hash_current"] for s in every),
    }
    return {
        "record": "Phase 2 survival update against the 2016 typhoon, per stratum",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "generated_by": "scripts/thesis_figure_gaps.py extract",
        "note": (
            "Committed slice of the production campaign manifest, extracted so "
            "the central Bayesian claim has a source that survives a fresh "
            "clone. Nothing is computed here: every field is copied verbatim "
            "from results/production_campaign_manifest.json. The recorded "
            "SHA-256 identifies WHICH manifest this was cut from and is not the "
            "gate -- the manifest carries per-stage timestamps and so changes on "
            "every campaign run; what is gated is that re-extracting from the "
            "live artifact reproduces this record's `runs` block exactly. "
            "Rejection fractions are fractions of the N = 1e5 "
            "prior sample. f_marginal_transient is the fraction rejected by the "
            "transient limit state but NOT by the static one -- exactly 0 in "
            "every run, which is the nesting result."
        ),
        "source": {
            "path": CAMPAIGN_MANIFEST.relative_to(REPO_ROOT).as_posix(),
            "sha256": _sha256(CAMPAIGN_MANIFEST),
            "gitignored": True,
            "campaign": manifest.get("campaign"),
        },
        "runs": runs,
        "totals": totals,
    }


def _read_rq4_rows() -> list[dict[str, str]]:
    with RQ4_ANNUAL.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def extract_rq4_slice() -> dict[str, Any]:
    """Slice the four BEP sections' sensitivity arms out of ``rq4_annual.csv``.

    ``rq4_annual.csv`` is 2280 rows and gitignored. Inventory 6.10 needs 40 of
    them: four sections x two climates x (baseline + four arms).
    """
    _require(RQ4_ANNUAL, "the Phase 3 RQ4 sensitivity brackets")
    rows = _read_rq4_rows()

    def pick(section: str, scenario: str, overrides: dict[str, str]) -> dict[str, str]:
        want = dict(RQ4_BASELINE, **overrides)
        matches = [
            row
            for row in rows
            if f"KP{row['kp']}" == section
            and row["scenario"] == scenario
            and all(row[key] == value for key, value in want.items())
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"rq4_annual.csv: expected exactly one row for {section} "
                f"{scenario} {want}, found {len(matches)}"
            )
        return matches[0]

    sections: list[dict[str, Any]] = []
    for section in SECTIONS:
        entries: list[dict[str, Any]] = []
        for scenario in ("historical", "+4K"):
            base = pick(section, scenario, {})
            base_system = float(base["p_annual_system"])
            base_bep = float(base["p_annual_bep"])
            arms = []
            for label, overrides in RQ4_ARMS:
                row = pick(section, scenario, overrides)
                system = float(row["p_annual_system"])
                bep = float(row["p_annual_bep"])
                arms.append(
                    {
                        "arm": label,
                        "p_annual_system": system,
                        "p_annual_bep": bep,
                        "share_bep": (
                            float(row["share_bep"]) if row["share_bep"] else None
                        ),
                        "ratio_system_to_baseline": system / base_system,
                        "ratio_bep_to_baseline": (bep / base_bep) if base_bep else None,
                        "bep_clamped_above_grid": row["bep_clamped_above_grid"]
                        == "True",
                    }
                )
            entries.append(
                {
                    "scenario": scenario,
                    "n_years": int(base["n_years"]),
                    "baseline": {
                        "p_annual_system": base_system,
                        "p_annual_bep": base_bep,
                        "share_bep": float(base["share_bep"]),
                        "bep_clamped_above_grid": base["bep_clamped_above_grid"]
                        == "True",
                    },
                    "arms": arms,
                }
            )
        sections.append({"section": section, "scenarios": entries})

    return {
        "record": "Phase 3 RQ4 sensitivity brackets at the four BEP sections",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "generated_by": "scripts/thesis_figure_gaps.py extract",
        "note": (
            "Committed slice of results/system_integration/phase3/rq4_annual.csv "
            "(2280 rows, gitignored), restricted to the four geotechnically "
            "characterised sections -- the scope campaign decision 5 sets for "
            "RQ3/RQ4. The baseline arm is the production deliverable: matrix "
            "d70, posterior BEP source, lambda_ac = 250 m, primary surface "
            "variant. Ratios are computed here; every P_f is copied verbatim. "
            "The recorded SHA-256 identifies which CSV this was cut from; the "
            "gate is that re-extracting from the live artifact reproduces this "
            "record's `sections` block exactly."
        ),
        "baseline_arm": RQ4_BASELINE,
        "source": {
            "path": RQ4_ANNUAL.relative_to(REPO_ROOT).as_posix(),
            "sha256": _sha256(RQ4_ANNUAL),
            "gitignored": True,
            "n_rows_total": len(rows),
        },
        "sections": sections,
    }


def extract_peak_shortcut_slice() -> dict[str, Any]:
    """Measure the WBI+ peak-only shortcut against the full transient replay.

    Inventory row 4.7. ``docs/phase2_report.md`` section 11.1 states the result
    in prose -- KP 58.8 15.6 % against 5.67 % (factor 2.75), KP 60.0 13.1 %
    against 3.36 % (3.90), KP 57.4 0.48 % against 0.07 % (7.5, small-number
    regime) -- but no artifact holds it, so this recomputes it from the two
    gitignored artifacts it descends from and commits the result.

    The peak-only reading is the Phase 1 **prior transient** fragility read at
    the observed 2016 peak: what a WBI+ practitioner would use for the survival
    constraint, having only the peak level. The replay figure is the Phase 2
    posterior's own rejection fraction over the same N = 1e5 prior sample.
    Interpolation is linear in stage on the raw Monte Carlo points (not the
    fitted lognormal, and not probit): that is the reading section 11.1's
    published numbers reproduce to three decimals.

    Both readings are transient. The comparison is therefore method against
    method on one sample, not limit state against limit state.
    """
    from bep_reliability_engine.fragility import FragilityResult

    sources: list[dict[str, Any]] = []
    strata: list[dict[str, Any]] = []
    for stem in STRATA:
        phase1 = _require(
            PHASE1_RESULTS / f"{stem}.h5", "the Phase 1 prior transient curve"
        )
        posterior = _require(
            PHASE2_RESULTS / f"{stem}_posterior.json", "the Phase 2 replay rejection"
        )
        sources.extend(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha256(path),
                "gitignored": True,
            }
            for path in (phase1, posterior)
        )

        result = FragilityResult.load(phase1)
        record = _read_json(posterior)["phase2"]
        peak = float(record["event_chain"][-1]["record"]["peak_m_msl"])
        grid = np.asarray(result.conditioning_grid, dtype=float)
        peak_only = float(np.interp(peak, grid, np.asarray(result.P_f_trans_raw)))
        replay = float(record["posterior"]["rejection_fraction"])
        n_prior = int(record["posterior"]["n_prior"])
        n_rejected = n_prior - int(record["posterior"]["n_accepted"])
        strata.append(
            {
                "stratum": stem,
                "section": _section_of(stem),
                "d70": _d70_of(stem),
                "n_prior": n_prior,
                "event_peak_m_msl": peak,
                "z_toe_m_msl": float(result.metadata["config"]["geometry"]["z_toe"]),
                "grid_min_m_msl": float(grid[0]),
                "grid_max_m_msl": float(grid[-1]),
                "f_peak_only_transient": peak_only,
                "f_replay_transient": replay,
                # None, not 1.0 and not "unbounded": with no rejection under
                # either reading there is no multiplier to measure. Keeping the
                # three cases apart is the same discipline the ranking figure
                # applies to ``unbounded`` against ``not defined``.
                "over_rejection_factor": (peak_only / replay) if replay > 0.0 else None,
                "n_rejected_replay": n_rejected,
                "n_peak_only_expected": int(round(peak_only * n_prior)),
                "small_number_regime": 0 < n_rejected < SMALL_NUMBER_ROWS,
            }
        )

    informative = [
        s
        for s in strata
        if s["over_rejection_factor"] is not None and not s["small_number_regime"]
    ]
    return {
        "record": "WBI+ peak-only shortcut against the full transient replay",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "generated_by": "scripts/thesis_figure_gaps.py extract",
        "note": (
            "Inventory row 4.7, the RQ2 clause 'what the time-resolved replay "
            "adds over a peak-only reading'. docs/phase2_report.md section 11.1 "
            "carries this comparison in prose only; this record is the artifact "
            "behind it. The peak-only column is the Phase 1 PRIOR TRANSIENT "
            "fragility linearly interpolated on its raw Monte Carlo points at "
            "the observed 2016 peak -- the reading a peak-based (WBI+, Zethof "
            "et al. 2023) survival update would take. The replay column is the "
            "Phase 2 posterior's rejection fraction over the same N = 1e5 prior "
            "sample. Both are transient, so this compares method against method "
            "on one sample. The mechanism is the loading shape: the Phase 1 "
            "curves condition on the canonical d4PDF compound shape scaled to "
            "each level, which carries far more above-toe exposure than the real "
            "2016 event did at the same peak, so the peak-only reading rejects "
            "realizations the full replay retains. over_rejection_factor is null "
            "where the replay rejects nothing -- not defined, never 1."
        ),
        "method": {
            "peak_only": "linear interpolation of P_f_trans_raw on the "
            "conditioning grid at the observed 2016 peak",
            "replay": "metadata['phase2']['posterior']['rejection_fraction']",
            "n_samples": 100000,
            "small_number_rows": SMALL_NUMBER_ROWS,
        },
        "sources": sources,
        "strata": strata,
        "headline": {
            "informative_strata": [s["stratum"] for s in informative],
            "factor_min": min(s["over_rejection_factor"] for s in informative),
            "factor_max": max(s["over_rejection_factor"] for s in informative),
            "n_factor_defined": sum(
                1 for s in strata if s["over_rejection_factor"] is not None
            ),
            "n_not_defined": sum(
                1 for s in strata if s["over_rejection_factor"] is None
            ),
        },
    }


def cmd_extract(args: argparse.Namespace) -> dict[str, Any]:
    """Write the three committed evidence slices from the gitignored artifacts."""
    written = [
        _write_json(args.out_dir / PHASE2_SLICE.name, extract_phase2_slice()),
        _write_json(args.out_dir / RQ4_SLICE.name, extract_rq4_slice()),
        _write_json(
            args.out_dir / PEAK_SHORTCUT_SLICE.name, extract_peak_shortcut_slice()
        ),
    ]
    return {"written": [p.relative_to(REPO_ROOT).as_posix() for p in written]}


# --------------------------------------------------------------------------- #
# Figure 1 -- the Phase 2 survival update, per stratum (inventory 4.1/4.2/5.2)  #
# --------------------------------------------------------------------------- #


def figure_phase2_survival(slice_: dict[str, Any]) -> tuple[Path, list[dict[str, Any]]]:
    """The central Bayesian claim, drawn so the nesting is visible.

    Left: per stratum, the transient rejection bar is drawn *inside* the static
    one. That containment is the result -- the set of realizations the 2016
    survival rejects through the transient limit state is a subset of the set it
    rejects through the static one, so the marginal transient rejection (the
    part sticking out) is exactly zero. A table of three percentages states
    that; a nested bar shows it.

    Right: the same transient filter under the three documented readings, which
    is the honest width of the claim -- the deliverable criterion rejects 0 to
    5.7 %, the strict no-initiation reading 39.6 to 99.6 %.
    """
    runs = {run["run"]: run for run in slice_["runs"]}
    baseline = runs["baseline"]["strata"]
    totals = slice_["totals"]

    fig, (ax, axb) = plt.subplots(
        1, 2, figsize=(13.2, 5.9), gridspec_kw={"width_ratios": [1.32, 1.0]}
    )

    # --- Panel A: nested rejection bars ------------------------------------- #
    order = sorted(baseline, key=lambda s: (s["section"], s["d70"] != "matrix"))
    ypos = np.arange(len(order))[::-1]
    static = np.array([s["f_static_reject"] for s in order]) * 100.0
    trans = np.array([s["f_trans_reject"] for s in order]) * 100.0

    ax.barh(
        ypos,
        static,
        height=0.66,
        color=figstyle.STATIC,
        alpha=0.30,
        lw=0,
        label="rejected by the static limit state",
    )
    ax.barh(
        ypos,
        trans,
        height=0.34,
        color=figstyle.TRANSIENT,
        edgecolor=figstyle.SURFACE,
        lw=1.4,
        label="rejected by the transient limit state (nested inside)",
        zorder=3,
    )
    # The two labels are staggered inside the row band: the values can be an
    # order of magnitude apart (73.315 against 3.363) or almost equal, and a
    # shared baseline would let them collide in the second case.
    for y, s_val, t_val in zip(ypos, static, trans):
        ax.text(
            s_val + 1.2,
            y + 0.19,
            f"{s_val:.3f}",
            va="center",
            fontsize=8.5,
            color=figstyle.INK_2,
        )
        if t_val > 0.0:
            ax.text(
                t_val + 1.2,
                y - 0.19,
                f"{t_val:.3f}",
                va="center",
                fontsize=8.5,
                color=figstyle.TRANSIENT,
            )
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{s['section']}  {s['d70']}" for s in order])
    ax.set_xlabel("share of the N = $10^5$ prior sample rejected [%]")
    ax.set_xlim(0, 88)
    ax.set_title("A  what the 2016 survival rejects, per stratum", loc="left")
    ax.legend(loc="lower right")

    # The marginal is the whole point and it is a column of zeros, so it is
    # drawn as data rather than left to the caption.
    ax.text(
        1.015,
        1.008,
        "marginal\ntransient",
        transform=ax.transAxes,
        fontsize=8.5,
        color=figstyle.INK,
        ha="left",
        va="bottom",
        linespacing=1.25,
    )
    for y, s in zip(ypos, order):
        ax.text(
            1.015,
            y,
            f"{s['f_marginal_transient'] * 100:.3f}",
            transform=ax.get_yaxis_transform(),
            fontsize=8.5,
            color=figstyle.GOOD,
            va="center",
            ha="left",
        )

    # --- Panel B: the same filter under the three documented readings ------- #
    matrix_sections = [s["section"] for s in baseline if s["d70"] == "matrix"]
    reading_colors = (figstyle.ORANGE, figstyle.AQUA, figstyle.VIOLET)
    height = 0.26
    for i, ((label, _stage, description), colour) in enumerate(
        zip(PHASE2_RUNS, reading_colors)
    ):
        by_section = {
            s["section"]: s["rejection_fraction"] * 100.0
            for s in runs[label]["strata"]
            if s["d70"] == "matrix"
        }
        values = [by_section[name] for name in matrix_sections]
        offsets = np.arange(len(matrix_sections))[::-1] + (1 - i) * height
        axb.barh(
            offsets,
            values,
            height=height * 0.92,
            color=colour,
            lw=0,
            label=RUN_DISPLAY_NAMES.get(description, description),
        )
        for y, value in zip(offsets, values):
            axb.text(
                value + 1.2,
                y,
                f"{value:.3f}",
                va="center",
                fontsize=8,
                color=figstyle.INK_2,
            )
    axb.set_yticks(np.arange(len(matrix_sections))[::-1])
    axb.set_yticklabels(matrix_sections)
    axb.set_xlim(0, 135)
    axb.set_xlabel("prior realizations rejected [%]")
    axb.set_title(
        "B  the same update under its three documented readings (matrix $d_{70}$)",
        loc="left",
    )
    axb.legend(loc="lower right", fontsize=8, bbox_to_anchor=(1.0, -0.02))

    fig.suptitle(
        f"Bayesian survival update against the 2016 typhoon: marginal transient "
        f"rejection is exactly 0 in all {totals['n_runs']} runs\n"
        f"masked-retained-matrices versus exact re-evaluation: verified at all "
        f"{len(baseline)} strata, {totals['flag_mismatches_total']} flag mismatches",
        fontsize=11.5,
        x=0.008,
        y=0.995,
        ha="left",
        va="top",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    rows = [
        {
            "run": run["run"],
            "criterion": s["criterion"],
            "section": s["section"],
            "d70": s["d70"],
            "n_prior": s["n_prior"],
            "n_accepted": s["n_accepted"],
            "static_reject_pct": round(s["f_static_reject"] * 100, 5),
            "transient_reject_pct": round(s["f_trans_reject"] * 100, 5),
            "marginal_transient_reject_pct": round(s["f_marginal_transient"] * 100, 5),
            "posterior_rejection_pct": round(s["rejection_fraction"] * 100, 5),
            "flag_mismatch_static": s["flag_mismatch_static"],
            "flag_mismatch_trans": s["flag_mismatch_trans"],
            "verified_exact": s["verified"],
        }
        for run in slice_["runs"]
        for s in run["strata"]
    ]
    return (
        figstyle.save(fig, "phase2_survival_update.png", mirror=MIRROR),
        rows,
    )


# --------------------------------------------------------------------------- #
# Figure 2 -- the epistemic bracket ranking (inventory 7.1)                      #
# --------------------------------------------------------------------------- #


def _span_cell(section: dict[str, Any], bracket: str, anchor: str) -> dict[str, Any]:
    """One cell of the ranking table, keeping ``unbounded`` and ``n/d`` apart.

    Two different things produce a missing number and conflating them would be a
    misreading:

    * **unbounded** -- an *arm* sits at exactly zero failures, so the relative
      span has no finite upper end. The knob was measured; its effect is at
      least the largest resolvable factor.
    * **not defined** -- the *baseline* sits at zero failures at that anchor, so
      no multiplier of any kind exists there. KP 57.4's design HWL (39.25 m,
      zero transient failures in 1e5) is the only such column, and it is a fact
      about the section rather than a gap in the table.
    """
    anchor_record = section["anchors"][anchor]
    defined = anchor_record["n_failures_trans_baseline"] > 0
    raw = section["brackets"][bracket]["span"].get(anchor, {}).get("span_trans")
    return {
        "defined": defined,
        "unbounded": defined and raw is None,
        "span": raw if defined else None,
        "stage_m_msl": anchor_record["stage_m_msl"],
        "p_f_trans_baseline": anchor_record["P_f_trans_baseline"],
        "n_failures_trans_baseline": anchor_record["n_failures_trans_baseline"],
    }


def _bracket_span_curve(section: dict[str, Any], bracket: str) -> list[dict[str, Any]]:
    """The bracket's multiplicative span at *every* conditioning level.

    ``_span_cell`` reads the span the record precomputes at its five named
    anchors. This forms the same quantity over the whole grid, which the record
    stores in the form it costs least to store: the stage grid and the baseline
    curve once per section, and each arm's own ``P_f_trans_arm`` per level. The
    span is the largest transient failure probability any arm of the bracket
    produces divided by the smallest, both relative to the same baseline, so it
    is identical whether it is formed from the probabilities or from the ratios.

    Reproduces the record's own ``ratio_min`` and ``ratio_max`` at all five
    anchors of all four sections, which is the provenance gate on this curve.

    The two ways a number goes missing are kept apart exactly as in
    ``_span_cell``: a level whose *baseline* carries no failure yields no
    multiplier of any kind and is dropped, while a level where an *arm* sits at
    zero failures is retained and marked ``unbounded``.
    """
    grid = section["grid_m_msl"]
    baseline = section["P_f_trans_baseline_curve"]
    arm_levels = [
        section["arms"][arm]["levels"] for arm in section["brackets"][bracket]["arms"]
    ]

    curve: list[dict[str, Any]] = []
    for index, stage in enumerate(grid):
        base = float(baseline[index])
        if base <= 0.0:
            continue
        ratios = [float(levels[index]["P_f_trans_arm"]) / base for levels in arm_levels]
        low, high = min(ratios), max(ratios)
        curve.append(
            {
                "stage_m_msl": float(stage),
                "unbounded": low <= 0.0,
                "span": None if low <= 0.0 else high / low,
            }
        )
    return curve


def _cancellation_by_bracket(section: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Per bracket, the worst resolved ratio-of-ratios departure over its arms.

    Reproduces the synthesis note's own section 4(c) table. The contaminated
    KP 57.4 all-station L arm is excluded by name (see
    ``CANCELLATION_ARM_EXCLUSIONS``) because ADR-0047 established it measures a
    road embankment rather than the levee.
    """
    worst: dict[str, dict[str, Any]] = {}
    for arm_name, arm in section["arms"].items():
        if arm_name in CANCELLATION_ARM_EXCLUSIONS:
            continue
        bracket = arm.get("bracket")
        value = arm.get("max_resolved_departure_factor")
        if bracket is None or not isinstance(value, (int, float)):
            continue
        current = worst.get(bracket)
        if current is None or value > current["max_resolved_departure_factor"]:
            worst[bracket] = {
                "arm": arm_name,
                "max_resolved_departure_factor": float(value),
                "n_levels_ratio_resolved": arm.get("n_levels_ratio_resolved"),
                "n_levels_ratio_evaluated": arm.get("n_levels_ratio_evaluated"),
            }
    return worst


def _bracket_order(sections: list[dict[str, Any]]) -> list[str]:
    """Rank the epistemic brackets by how far they move transient P_f.

    Data-driven rather than editorial: the sort key is (number of unbounded
    cells, largest finite span) over the two anchors the thesis quotes, so the
    ordering the figure asserts is the one the evidence supports.
    """
    keys: dict[str, tuple[int, float]] = {}
    for bracket in sections[0]["brackets"]:
        if bracket in STATISTICAL_BRACKETS:
            continue
        unbounded, finite = 0, 0.0
        for section in sections:
            for anchor in RANKING_PANEL_ANCHORS:
                cell = _span_cell(section, bracket, anchor)
                if not cell["defined"]:
                    continue
                if cell["unbounded"]:
                    unbounded += 1
                else:
                    finite = max(finite, float(cell["span"]))
        keys[bracket] = (unbounded, finite)
    return sorted(keys, key=lambda b: keys[b], reverse=True)


# --------------------------------------------------------------------------- #
# Figure 2 -- printed geometry and type                                         #
# --------------------------------------------------------------------------- #
#
# The thesis places this figure at ``\textwidth`` in a 170 mm text block, so a
# figure authored much wider than that is reduced on the page and every label
# with it. The 15.4 in layout this replaces was reduced 2.37 times, which put
# its tick labels at 4.4 pt and its notes at 3.4 pt against 10 pt body text and
# 8 pt captions: nothing in it could be read in print. The fix is to author at a
# known multiple of the printed width and to state every type size as the size
# it will have on the page. The multiple keeps the raster fine (about 340 dots
# per printed inch) without changing what the reader sees.

#: The thesis text block, in inches: ``total={170mm,257mm}`` in the class.
RANKING_PAGE_WIDTH_IN = 170.0 / 25.4
#: Authored inches per printed inch. Type sizes below are printed points.
RANKING_SCALE = 2.0
#: Width over height of the saved image. A figure placed at ``\textwidth``
#: costs a band of ``textwidth / aspect``, so this may never fall below the
#: 2.571 of the layout it replaces without buying a page.
RANKING_ASPECT = 2.555
#: ``figstyle.save`` writes with ``bbox_inches="tight"``, which pads by this.
RANKING_TIGHT_PAD_IN = 0.1

#: Type sizes in points **on the printed page**. The floor is about 7 pt: the
#: thesis sets body text at 10 pt and captions at 8 pt, and a figure that is
#: read rather than glanced at has to stay within reach of its caption.
RANKING_PT = {
    "suptitle": 8.6,
    "panel_title": 8.0,
    "axis_label": 7.6,
    "tick": 7.0,
    "row_label": 7.0,
    "legend": 6.8,
    "note": 6.6,
    "value": 6.4,
    "inset": 6.2,
    "marker": 3.6,
    "marker_c": 2.2,
}

#: Column widths of the ranking layout, in printed inches, left to right. They
#: sum to the drawn width; the row labels are written into the first one.
RANKING_COLUMNS = {
    "row_labels": 1.12,
    "zoom": 1.00,
    "break": 0.06,
    "log": 0.60,
    "gap_ab": 0.16,
    "gap_bc": 0.36,
    "right": 0.05,
}
#: Heights of the bands above and below the axes, in printed inches.
RANKING_BANDS = {
    "suptitle": 0.17,
    "panel_title": 0.15,
    "tick_labels": 0.13,
    "axis_label": 0.15,
    "note": 0.28,
    "bottom": 0.04,
}


def _rpt(name: str) -> float:
    """A printed type size in the authored units of the ranking figure."""
    return RANKING_PT[name] * RANKING_SCALE


def _ranking_value_label(value: float) -> str:
    """Render a span that sits outside the near-unity zoom, for the mark itself.

    Three significant figures, matching :func:`_fmt_span` so a value read off
    the figure and the same value read out of the table source agree.
    """
    if value < 1000.0:
        return f"{value:.0f}"
    exponent = int(np.floor(np.log10(value)))
    return rf"${value / 10.0**exponent:.2f}\times10^{{{exponent}}}$"


def figure_epistemic_ranking(
    synthesis: dict[str, Any], attainable_max_kp62: float
) -> tuple[Path, list[dict[str, Any]]]:
    """The brackets, four sections, ranked, and the winner's stage dependence.

    Panels A and B are the ranking at the two anchors that carry the thesis's
    claims. Panel C takes the bracket that wins that ranking and plots its span
    across the whole conditioning grid, which is the one claim the text makes
    about it that no figure showed: it spans orders of magnitude at the
    low-stage end and collapses toward unity as the conditional probability
    saturates, so no single factor for it exists.

    **The span axis of panels A and B is split, and that is the design.** The
    brackets run from 1.00 to above 1e5, and on one logarithmic axis over that
    range every bracket near unity collapses onto the spine with the four
    section marks on top of each other. That is exactly where the section's
    least comfortable reading lives: whether an epistemic bracket is wider or
    narrower than the sampling band on the same estimate is decided inside the
    first factor of three. The near-unity segment is therefore linear and runs
    to just past the widest statistical band, and everything above it is
    logarithmic and carries its value beside the mark. Sections are dodged
    within a row so four marks on one value stay four marks.

    Panel C carried the cancellation test until 2026-08-15, when a coherence
    audit found it drew the same quantity as the bar panel of
    ``epistemic_vs_statistical.png``, which additionally carries the
    Clopper-Pearson yardstick on the same axis and is therefore the better of
    the two. The cancellation numbers are not lost with the panel: every one of
    them stays in this figure's own table source, in the ``cancellation_arm``
    and ``max_resolved_departure_factor`` columns built below.
    """
    sections = {s["section"]: s for s in synthesis["sections"]}
    ordered = _bracket_order(synthesis["sections"])
    rows_order = ordered + list(STATISTICAL_BRACKETS)
    cancellation = {
        name: _cancellation_by_bracket(section) for name, section in sections.items()
    }
    n_rows = len(rows_order)
    scale = RANKING_SCALE

    # --- the printed layout, in printed inches ---------------------------- #
    drawn_w = RANKING_PAGE_WIDTH_IN - 2.0 * RANKING_TIGHT_PAD_IN / scale
    drawn_h = (
        RANKING_PAGE_WIDTH_IN / RANKING_ASPECT - 2.0 * RANKING_TIGHT_PAD_IN / scale
    )
    fig = plt.figure(figsize=(drawn_w * scale, drawn_h * scale))

    col = RANKING_COLUMNS
    panel_w = col["zoom"] + col["break"] + col["log"]
    x_a = col["row_labels"]
    x_b = x_a + panel_w + col["gap_ab"]
    x_c = x_b + panel_w + col["gap_bc"]
    w_c = drawn_w - col["right"] - x_c
    band = RANKING_BANDS
    y_bot = band["bottom"] + band["note"] + band["axis_label"] + band["tick_labels"]
    y_top = drawn_h - band["suptitle"] - band["panel_title"]

    def _axes(x0: float, width: float) -> plt.Axes:
        return fig.add_axes(
            (x0 / drawn_w, y_bot / drawn_h, width / drawn_w, (y_top - y_bot) / drawn_h)
        )

    pairs = []
    for x0 in (x_a, x_b):
        pairs.append(
            (
                _axes(x0, col["zoom"]),
                _axes(x0 + col["zoom"] + col["break"], col["log"]),
            )
        )
    axc = _axes(x_c, w_c)

    # --- the two segments panels A and B share ---------------------------- #
    finite: list[float] = []
    statistical: list[float] = []
    for section in sections.values():
        for bracket in rows_order:
            for anchor in RANKING_PANEL_ANCHORS:
                cell = _span_cell(section, bracket, anchor)
                if cell["defined"] and not cell["unbounded"]:
                    finite.append(float(cell["span"]))
                    if bracket in STATISTICAL_BRACKETS:
                        statistical.append(float(cell["span"]))
    # The split is where the comparison stops being close: a tenth past the
    # widest sampling band, so every bracket that competes with one is inside
    # the linear segment at full resolution.
    split = 1.1 * max(statistical)
    x_top_log = max(finite) * 60.0
    #: Where an unbounded span is drawn, as a fraction of the logarithmic
    #: segment: past every finite mark, with room left for the arrow that says
    #: the value has no upper end.
    x_unbounded = 0.82

    # "design_hwl" in the synthesis record is the nearest *grid level* to each
    # section's HWL, not the HWL itself (KP 62.0: 46.50 m against 46.39 m).
    # ADR-0040 section 2.5 established that those are resolvably different
    # levels, so the panel says which one it is drawing.
    for (ax_zoom, ax_log), anchor, title, x_panel in zip(
        pairs,
        RANKING_PANEL_ANCHORS,
        ("A  at the design-level anchor", "B  at the transition midpoint"),
        (x_a, x_b),
    ):
        for ax in (ax_zoom, ax_log):
            ax.set_ylim(-0.62, n_rows - 0.25)
            ax.set_yticks(list(range(n_rows))[::-1])
            ax.set_yticks([y + 0.5 for y in range(-1, n_rows)], minor=True)
            ax.set_yticklabels([])
            ax.tick_params(
                axis="y", which="both", length=0, labelsize=_rpt("row_label")
            )
            ax.tick_params(axis="x", labelsize=_rpt("tick"), pad=1.5 * scale)
            ax.grid(False)
            ax.grid(
                True,
                axis="y",
                which="minor",
                color=figstyle.GRID,
                lw=0.7 * scale,
                zorder=0,
            )
            ax.grid(True, axis="x", which="major", color=figstyle.GRID, lw=0.7 * scale)
            for spine in ax.spines.values():
                spine.set_linewidth(0.8 * scale)
            for row, bracket in enumerate(rows_order):
                if bracket in STATISTICAL_BRACKETS:
                    ax.axhspan(
                        n_rows - 1.5 - row,
                        n_rows - 0.5 - row,
                        color=figstyle.GRID,
                        alpha=0.55,
                        lw=0,
                        zorder=0,
                    )

        # The unit line stands clear of the spine: every bracket that moves
        # nothing at all sits on it, and against the spine those marks were
        # unreadable.
        ax_zoom.set_xlim(0.88, split)
        ax_zoom.set_xticks([1.0, 1.5, 2.0, 2.5, 3.0])
        ax_zoom.set_xticklabels(["1", "1.5", "2", "2.5", "3"])
        ax_zoom.axvline(1.0, color=figstyle.BASELINE, lw=1.0 * scale, zorder=1)
        if ax_zoom is pairs[0][0]:
            # Both panels carry the same rows in the same order and are aligned
            # on them, so the rows are named once and the minor-tick rules
            # carry the eye across.
            ax_zoom.set_yticklabels(
                [BRACKET_LABEL[b] for b in rows_order], fontsize=_rpt("row_label")
            )
        ax_log.set_xscale("log")
        ax_log.set_xlim(split, x_top_log)
        ax_log.set_xticks([1e1, 1e3, 1e5])
        ax_log.tick_params(axis="y", which="both", left=False)

        # The break is drawn, not implied: two ticks on the facing spines say
        # the axis is cut rather than continuous.
        for ax, side in ((ax_zoom, 1.0), (ax_log, 0.0)):
            for y0 in (0.0, 1.0):
                ax.plot(
                    [side - 0.012, side + 0.012],
                    [y0 - 0.014, y0 + 0.014],
                    transform=ax.transAxes,
                    color=figstyle.BASELINE,
                    lw=0.9 * scale,
                    clip_on=False,
                    zorder=6,
                )

        for row, bracket in enumerate(rows_order):
            y = n_rows - 1 - row
            beyond_zoom: list[tuple[float, float]] = []
            inside_zoom: list[float] = []
            n_defined = 0
            for name in SECTIONS:
                cell = _span_cell(sections[name], bracket, anchor)
                if not cell["defined"]:
                    continue
                n_defined += 1
                colour = figstyle.SECTION_COLORS[name]
                marker = figstyle.SECTION_MARKERS[name]
                y_offset = y + (SECTIONS.index(name) - 1.5) * 0.20
                if cell["unbounded"]:
                    strip = ax_log.get_yaxis_transform()
                    ax_log.plot(
                        [x_unbounded],
                        [y_offset],
                        marker=marker,
                        color=colour,
                        ms=_rpt("marker"),
                        mfc=figstyle.SURFACE,
                        mew=0.9 * scale,
                        ls="none",
                        transform=strip,
                        zorder=4,
                    )
                    ax_log.annotate(
                        "",
                        xy=(0.985, y_offset),
                        xytext=(x_unbounded + 0.030, y_offset),
                        xycoords=strip,
                        textcoords=strip,
                        arrowprops={
                            "arrowstyle": "-|>",
                            "color": colour,
                            "lw": 0.8 * scale,
                            "shrinkA": 0,
                            "shrinkB": 0,
                            "mutation_scale": 5.0 * scale,
                        },
                    )
                    continue
                value = max(float(cell["span"]), 1.0)
                target = ax_zoom if value < split else ax_log
                target.plot(
                    [value],
                    [y_offset],
                    marker=marker,
                    color=colour,
                    ms=_rpt("marker"),
                    ls="none",
                    zorder=4,
                )
                if target is ax_log:
                    beyond_zoom.append((y_offset, value))
                else:
                    inside_zoom.append(value)

            # Where every section in a row agrees to two decimals the marks are
            # one cluster at this scale and no amount of dodging separates
            # them, so the row states the value they share. The rule is the
            # agreement itself, not a choice of which rows to annotate.
            rounded = {round(v, 2) for v in inside_zoom}
            if len(inside_zoom) == n_defined >= 3 and len(rounded) == 1:
                ax_zoom.annotate(
                    f"{max(inside_zoom):.2f}",
                    xy=(max(inside_zoom), y),
                    xytext=(4.0 * scale, 0.0),
                    textcoords="offset points",
                    fontsize=_rpt("value"),
                    color=figstyle.INK_2,
                    ha="left",
                    va="center",
                    zorder=5,
                )

            # Beyond the zoom the axis is coarse, so each mark carries its own
            # number rather than being read off two decades. Where a row holds
            # more than one, the numbers are spread across the row's own band
            # in the order the marks sit in, which is the only place free of
            # every other mark.
            beyond_zoom.sort()
            for rank, (y_offset, value) in enumerate(beyond_zoom):
                spread = (rank - (len(beyond_zoom) - 1) / 2.0) * 0.50
                high = np.log10(value / split) / np.log10(x_top_log / split) > 0.45
                ax_log.annotate(
                    _ranking_value_label(value),
                    xy=(value, y_offset + spread),
                    xytext=(-3.0 * scale if high else 3.0 * scale, 0.0),
                    textcoords="offset points",
                    fontsize=_rpt("value"),
                    color=figstyle.INK_2,
                    ha="right" if high else "left",
                    va="center",
                    annotation_clip=False,
                    zorder=5,
                )

        ax_zoom.set_title(
            title, loc="left", fontsize=_rpt("panel_title"), pad=2.5 * scale
        )
        fig.text(
            (x_panel + panel_w / 2.0) / drawn_w,
            (band["bottom"] + band["note"] + 0.035) / drawn_h,
            r"transient $P_f$ span factor at the anchor",
            fontsize=_rpt("axis_label"),
            color=figstyle.INK_2,
            ha="center",
            va="bottom",
        )

    # The shaded band says what it is inside the panel, so the reader does not
    # have to reach the caption to learn that two of the eight rows are not
    # epistemic knobs at all.
    pairs[0][0].text(
        1.85,
        (n_rows - 1 - rows_order.index(STATISTICAL_BRACKETS[0])) - 0.5,
        "statistical\nyardsticks",
        fontsize=_rpt("inset"),
        color=figstyle.MUTED,
        ha="center",
        va="center",
        linespacing=1.15,
        zorder=5,
    )

    # --- Panel C: the top knob has no single value, it depends on stage ------ #
    # Panels A and B are two stage slices of the ranking; this is the whole
    # stage axis for the knob that wins it. The bracket is the same quantity
    # those panels plot, so the panel needs no second definition: what it adds
    # is that the number they report is a reading off a curve, not a constant.
    # ``ordered`` is computed from the evidence, so the panel draws whichever
    # bracket the ranking actually puts first.
    largest = ordered[0]
    curves = {name: _bracket_span_curve(sections[name], largest) for name in SECTIONS}

    spans = [
        float(point["span"])
        for curve in curves.values()
        for point in curve
        if point["span"] is not None
    ]
    # The unbounded levels sit in a strip above every finite value, so that the
    # eye never reads one as a large finite span.
    y_unbounded = max(spans) * 4.0
    for name in SECTIONS:
        colour = figstyle.SECTION_COLORS[name]
        marker = figstyle.SECTION_MARKERS[name]
        finite_points = [p for p in curves[name] if p["span"] is not None]
        axc.plot(
            [p["stage_m_msl"] for p in finite_points],
            [float(p["span"]) for p in finite_points],
            marker=marker,
            color=colour,
            ms=_rpt("marker_c"),
            lw=1.0 * scale,
            zorder=4,
        )
        for point in (p for p in curves[name] if p["unbounded"]):
            axc.plot(
                [point["stage_m_msl"]],
                [y_unbounded],
                marker=marker,
                color=colour,
                ms=_rpt("marker_c") * 1.4,
                mfc=figstyle.SURFACE,
                mew=0.8 * scale,
                ls="none",
                zorder=4,
            )
            axc.annotate(
                "",
                xy=(point["stage_m_msl"], y_unbounded * 2.6),
                xytext=(point["stage_m_msl"], y_unbounded * 1.35),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": colour,
                    "lw": 0.6 * scale,
                    "shrinkA": 0,
                    "shrinkB": 0,
                    "mutation_scale": 5.0 * scale,
                },
            )
        # A tick on the axis, not a full rule: four vertical lines across a
        # panel this narrow would compete with the curves they annotate.
        axc.plot(
            [sections[name]["hwl_m_msl"]] * 2,
            [0.0, 0.055],
            transform=axc.get_xaxis_transform(),
            color=colour,
            lw=1.6 * scale,
            solid_capstyle="butt",
            zorder=5,
        )

    axc.axhline(1.0, color=figstyle.BASELINE, lw=1.0 * scale)
    axc.set_yscale("log")
    axc.set_ylim(0.55, y_unbounded * 5.0)
    axc.set_xlim(min(p["stage_m_msl"] for c in curves.values() for p in c) - 0.7, 57.4)
    axc.set_xlabel(
        "conditioning water level [m T.P.]",
        fontsize=_rpt("axis_label"),
        labelpad=1.5 * scale,
    )
    axc.set_ylabel(
        f"{BRACKET_LABEL[largest]} span factor",
        fontsize=_rpt("axis_label"),
        labelpad=1.5 * scale,
    )
    axc.set_title(
        "C  the top knob has no single value",
        loc="left",
        x=-0.03,
        fontsize=_rpt("panel_title"),
        pad=2.5 * scale,
    )
    axc.tick_params(labelsize=_rpt("tick"), pad=1.5 * scale)
    axc.grid(True, color=figstyle.GRID, lw=0.7 * scale)
    for spine in axc.spines.values():
        spine.set_linewidth(0.8 * scale)
    figstyle.mark_hypothetical(axc, attainable_max_kp62, label=False)
    # ``get_yaxis_transform`` takes x as an axes fraction and y in data units,
    # so the label tracks the unbounded strip whatever the finite maximum is.
    # It sits above the arrow tips, the one band clear of every mark.
    axc.text(
        0.985,
        y_unbounded * 3.1,
        "unbounded",
        transform=axc.get_yaxis_transform(),
        fontsize=_rpt("inset"),
        color=figstyle.MUTED,
        ha="right",
        va="bottom",
    )

    # The two ways a number goes missing are different facts, and the figure
    # has to keep them apart without the caption's help. The anchor and the
    # high water level are both named because they are resolvably different
    # levels, which is why the panels say "anchor" and not "design HWL".
    kp57_4 = sections["KP57.4"]
    fig.text(
        0.008,
        (band["bottom"] + band["note"]) / drawn_h,
        "An open mark with an arrow is an unbounded span: one arm of that "
        "bracket reaches zero failures.\n"
        "KP 57.4 is absent from panel A: its anchor, the "
        f"{kp57_4['anchors']['design_hwl']['stage_m_msl']:.2f} m grid level "
        f"nearest its {kp57_4['hwl_m_msl']:.2f} m high water level, carries "
        "no transient\n"
        "failure at all in $10^5$, so no span of any kind is defined there. "
        "That is a fact about the section, not a gap in the measurement.",
        fontsize=_rpt("note"),
        color=figstyle.MUTED,
        ha="left",
        va="top",
        linespacing=1.35,
    )

    handles = [
        plt.Line2D(
            [],
            [],
            marker=figstyle.SECTION_MARKERS[name],
            color=figstyle.SECTION_COLORS[name],
            ls="none",
            ms=_rpt("marker") * 1.15,
            label=name.replace("KP", "KP "),
        )
        for name in SECTIONS
    ]
    handles.append(
        plt.Line2D(
            [],
            [],
            marker="o",
            color=figstyle.MUTED,
            ls="none",
            ms=_rpt("marker") * 1.15,
            mfc=figstyle.SURFACE,
            mew=0.9 * scale,
            label="unbounded span",
        )
    )
    # The legend shares the top band with the title rather than taking a strip
    # of its own: the band below the panels is spent on the note, and a strip
    # here would come straight out of the row pitch.
    fig.legend(
        handles=handles,
        loc="upper right",
        ncol=5,
        bbox_to_anchor=(1.0 - col["right"] / drawn_w, 1.0 - 0.010),
        frameon=False,
        fontsize=_rpt("legend"),
        handletextpad=0.4,
        columnspacing=1.0,
        borderpad=0.0,
    )
    fig.text(
        0.008,
        1.0 - 0.016,
        r"$k_\mathrm{aq}$ is the largest knob at every section and every anchor",
        fontsize=_rpt("suptitle"),
        color=figstyle.INK,
        ha="left",
        va="top",
    )

    rows: list[dict[str, Any]] = []
    for bracket in rows_order:
        for name in SECTIONS:
            record = cancellation[name].get(bracket, {})
            for anchor in ANCHORS:
                cell = _span_cell(sections[name], bracket, anchor)
                rows.append(
                    {
                        "bracket": bracket,
                        "kind": (
                            "statistical"
                            if bracket in STATISTICAL_BRACKETS
                            else "epistemic"
                        ),
                        "section": name,
                        "anchor": anchor,
                        "stage_m_msl": cell["stage_m_msl"],
                        "above_attainable_max": (
                            name == "KP62.0"
                            and cell["stage_m_msl"] > attainable_max_kp62
                        ),
                        "p_f_trans_baseline": cell["p_f_trans_baseline"],
                        "n_failures_trans_baseline": cell["n_failures_trans_baseline"],
                        "span_trans": (
                            "not_defined"
                            if not cell["defined"]
                            else _fmt_span(cell["span"])
                        ),
                        "moves_both_branches": bracket not in SINGLE_BRANCH_BRACKETS,
                        "cancellation_arm": record.get("arm", ""),
                        "max_resolved_departure_factor": (
                            round(record["max_resolved_departure_factor"], 4)
                            if record
                            else ""
                        ),
                    }
                )
    return figstyle.save(fig, "epistemic_bracket_ranking.png", mirror=MIRROR), rows


# --------------------------------------------------------------------------- #
# Figure 3 -- KP 57.4 is a bound, not a point estimate (inventory 2.5)          #
# --------------------------------------------------------------------------- #


def _num(value: Any) -> float:
    """Read a JSON number that may have been serialised as inf/nan text."""
    if isinstance(value, str):
        return float(value)
    return float(value)


def _clopper_pearson_bound(k_static: int, k_transient: int, n: int) -> float:
    """One-sided-in-effect bound on B from the two 95 % Clopper-Pearson bands.

    A bootstrap over two failing rows can only resample the two rows it has, so
    its interval is not trustworthy. The defensible statement divides the static
    branch's 95 % *lower* endpoint by the transient branch's 95 % *upper* one,
    both from the same ADR-0024 Clopper-Pearson construction the rest of the
    project uses. Reproduces the companion note's 148 (A1) and 101 (A2).
    """
    from bep_reliability_engine.fragility import binomial_ci

    static_lo, _ = binomial_ci(np.array([k_static / n]), n)
    _, trans_hi = binomial_ci(np.array([k_transient / n]), n)
    return float(static_lo[0] / trans_hi[0])


def figure_kp57_4_bound(evidence: dict[str, Any]) -> tuple[Path, list[dict[str, Any]]]:
    """What KP 57.4 supports at its design water level, and what it does not.

    The contrast section's whole story is one panel. Two failing transient rows
    at the design HWL anchor and ten at the nearest grid level: neither is a
    point estimate, and the honest deliverable is a Clopper-Pearson bound plus
    the lowest *resolved* level above it. The recommended anchor's own
    contamination -- one Euler barrier-jump row in 521 -- is drawn, because a
    reader taking this panel into a viva has to be able to see it.

    ADR-0024 plays no part here: KP 57.4's grid stops at its attainable maximum
    (43.25 m), so there is no hypothetical extension to shade.
    """
    brute = evidence["stages"]["A_brute_kp57_4"]
    n_samples = int(brute["n_samples"])
    table = [row for row in brute["bias_table"] if int(row["k_transient"]) > 0]
    flips = {
        float(entry["level_m"]): int(entry["count"])
        for entry in brute["euler_flips"]["offending_levels"].get("c4b_not_c3b", [])
    }
    a1, a2 = brute["anchor_A1"], brute["anchor_A2"]
    resolved = [row for row in table if row["resolved"]]
    quotable = min(resolved, key=lambda r: float(r["level_m"]))
    bound_a1 = _clopper_pearson_bound(
        int(a1["k_static"]), int(a1["k_transient"]), n_samples
    )
    bound_a2 = _clopper_pearson_bound(
        int(a2["k_static"]), int(a2["k_transient"]), n_samples
    )

    fig, (ax, axk) = plt.subplots(
        2,
        1,
        figsize=(10.6, 6.6),
        sharex=True,
        gridspec_kw={"height_ratios": [3.1, 1.0], "hspace": 0.08},
    )

    # --- resolved points carry an interval; unresolved ones must not read as
    #     estimates, so they are hollow and their intervals are drawn muted.
    for row in table:
        level, ratio = float(row["level_m"]), _num(row["ratio"])
        lo, hi = _num(row["ci_lo"]), _num(row["ci_hi"])
        is_resolved = bool(row["resolved"])
        ax.errorbar(
            [level],
            [ratio],
            yerr=[[max(ratio - lo, 0.0)], [max(hi - ratio, 0.0)]],
            fmt=figstyle.SECTION_MARKERS["KP57.4"],
            color=figstyle.SECTION_COLORS["KP57.4"] if is_resolved else figstyle.MUTED,
            mfc=(
                figstyle.SECTION_COLORS["KP57.4"] if is_resolved else figstyle.SURFACE
            ),
            mew=1.5,
            ms=6.0,
            lw=1.5,
            capsize=3.5,
            zorder=4 if is_resolved else 3,
        )

    # --- the two design-HWL anchors, and the bound that replaces them -------- #
    # A1 and A2 are 0.04 m apart, so their callouts cannot live beside them.
    # All three sit in one right-hand column with leader lines, stacked in the
    # order a reader meets them going up the axis.
    for anchor, level, bound in (
        (a1, float(a1["level_m"]), bound_a1),
        (a2, float(a2["level_m"]), bound_a2),
    ):
        ax.axvline(level, color=figstyle.BASELINE, lw=1.0, zorder=1)
        ax.annotate(
            "",
            xy=(level, bound * 7.0),
            xytext=(level, bound),
            arrowprops={
                "arrowstyle": "-|>",
                "color": figstyle.VIOLET,
                "lw": 1.8,
                "shrinkA": 0,
                "shrinkB": 0,
            },
            zorder=5,
        )
        ax.plot(
            [level - 0.06, level + 0.06],
            [bound, bound],
            color=figstyle.VIOLET,
            lw=2.6,
            solid_capstyle="butt",
            zorder=5,
        )

    quotable_level = float(quotable["level_m"])
    quotable_flips = flips.get(quotable_level, 0)
    callouts = (
        (
            float(a1["level_m"]),
            bound_a1,
            0.94,
            figstyle.VIOLET,
            f"A1  design HWL, {float(a1['level_m']):.2f} m T.P.\n"
            f"{int(a1['k_transient'])} transient rows in $10^6$: UNRESOLVED.\n"
            f"Report the Clopper-Pearson bound:  $B \\geq$ {bound_a1:.0f}",
        ),
        (
            float(a2["level_m"]),
            bound_a2,
            0.76,
            figstyle.VIOLET,
            f"A2  nearest grid level, {float(a2['level_m']):.2f} m T.P.\n"
            f"{int(a2['k_transient'])} transient rows: also UNRESOLVED,  "
            f"$B \\geq$ {bound_a2:.0f}",
        ),
        (
            quotable_level,
            _num(quotable["ratio"]),
            0.545,
            figstyle.INK,
            f"quotable anchor  {quotable_level:.2f} m MSL\n"
            f"$B$ = {_num(quotable['ratio']):.1f} "
            f"[{_num(quotable['ci_lo']):.1f}, {_num(quotable['ci_hi']):.1f}] "
            f"on {int(quotable['k_transient'])} transient rows, RESOLVED\n"
            f"caveat: this level is itself one of the three Euler barrier-jump\n"
            f"levels -- {quotable_flips} row in {int(quotable['k_transient'])} "
            f"({quotable_flips / int(quotable['k_transient']):.2%}), biasing $B$ "
            f"DOWN about 0.2 %,\nwhich is conservative in direction",
        ),
    )
    for level, value, y_frac, colour, text in callouts:
        ax.annotate(
            text,
            xy=(level, value),
            xycoords="data",
            xytext=(0.30, y_frac),
            textcoords="axes fraction",
            fontsize=8.5,
            color=colour,
            ha="left",
            va="top",
            arrowprops={
                "arrowstyle": "-",
                "color": figstyle.MUTED,
                "lw": 0.9,
                "shrinkB": 3,
            },
        )

    ax.set_yscale("log")
    ax.set_ylabel(r"bias factor  $B = P_{f,\mathrm{static}}/P_{f,\mathrm{transient}}$")
    ax.set_title(
        "KP 57.4 at $N = 10^6$: a bound at the design water level, a resolved "
        "value one grid step above it\n"
        "matrix $d_{70}$, brute force throughout (no weighted number enters this "
        "figure)",
        loc="left",
    )
    handles = [
        plt.Line2D(
            [],
            [],
            marker=figstyle.SECTION_MARKERS["KP57.4"],
            color=figstyle.SECTION_COLORS["KP57.4"],
            ls="none",
            ms=6.5,
            label="resolved (R1 and R2 both met)",
        ),
        plt.Line2D(
            [],
            [],
            marker=figstyle.SECTION_MARKERS["KP57.4"],
            color=figstyle.MUTED,
            mfc=figstyle.SURFACE,
            mew=1.5,
            ls="none",
            ms=6.5,
            label="unresolved, not a point estimate",
        ),
        plt.Line2D(
            [],
            [],
            color=figstyle.VIOLET,
            lw=2.4,
            label="Clopper-Pearson bound on $B$",
        ),
    ]
    ax.legend(handles=handles, loc="upper right")

    # --- the row-count strip: what every point above is actually made of ----- #
    levels = [float(row["level_m"]) for row in table]
    counts = [int(row["k_transient"]) for row in table]
    axk.bar(levels, counts, width=0.14, color=figstyle.MUTED, lw=0)
    axk.axhline(
        30,
        color=figstyle.CRITICAL,
        lw=1.2,
        label="R1 floor = 30 transient rows",
    )
    total_flips = sum(flips.values())
    for level, count in flips.items():
        axk.plot(
            [level],
            [1.5],
            marker="v",
            color=figstyle.CRITICAL,
            ms=6.5,
            ls="none",
            zorder=5,
        )
        axk.annotate(
            f"{count}",
            (level, 1.5),
            textcoords="offset points",
            xytext=(7, -3),
            fontsize=7.5,
            color=figstyle.CRITICAL,
            ha="left",
            va="center",
        )
    axk.plot(
        [],
        [],
        marker="v",
        color=figstyle.CRITICAL,
        ms=6.5,
        ls="none",
        label=(
            f"Euler barrier-jump level ({total_flips} rows in $10^6$; "
            "0.4 expected at $N = 10^5$)"
        ),
    )
    axk.set_yscale("log")
    axk.set_ylim(0.7, 4e6)
    axk.set_ylabel("transient\nfailing rows")
    axk.set_xlabel("conditioning water level [m T.P.]")
    axk.set_xlim(min(levels) - 0.28, max(levels) + 0.28)
    axk.legend(loc="upper right", fontsize=8, ncol=2)

    rows = [
        {
            "level_m_msl": float(row["level_m"]),
            "n_samples": n_samples,
            "k_static": int(row["k_static"]),
            "k_transient": int(row["k_transient"]),
            "p_f_static": _num(row["p_static"]),
            "p_f_transient": _num(row["p_transient"]),
            "bias_B": round(_num(row["ratio"]), 4),
            "ci_lo": round(_num(row["ci_lo"]), 4),
            "ci_hi": round(_num(row["ci_hi"]), 4),
            "ci_width_factor": round(_num(row["width_factor"]), 4),
            "resolved": bool(row["resolved"]),
            "role": (
                "A1_design_hwl"
                if float(row["level_m"]) == float(a1["level_m"])
                else (
                    "A2_nearest_grid_level"
                    if float(row["level_m"]) == float(a2["level_m"])
                    else ("A3_quotable_anchor" if row is quotable else "")
                )
            ),
            "clopper_pearson_bound_B": (
                round(bound_a1, 1)
                if float(row["level_m"]) == float(a1["level_m"])
                else (
                    round(bound_a2, 1)
                    if float(row["level_m"]) == float(a2["level_m"])
                    else ""
                )
            ),
            "euler_barrier_jump_rows": flips.get(float(row["level_m"]), 0),
        }
        for row in table
    ]
    return figstyle.save(fig, "adr0040_kp57_4_bound.png", mirror=MIRROR), rows


# --------------------------------------------------------------------------- #
# Figure 4 -- Phase 3 sensitivity brackets at the four sections (inventory 6.10)#
# --------------------------------------------------------------------------- #

#: One hue per arm. Deliberately avoids the four section hues and the two
#: limit-state hues, which carry fixed identities across the whole thesis. The
#: two lambda_ac settings are one knob at two magnitudes, so they share a hue
#: and separate by marker fill.
RQ4_ARM_STYLE = {
    "lambda_ac_100m": {
        "label": r"$\lambda_\mathrm{ac}$ = 100 m",
        "color": figstyle.ORANGE,
        "marker": "o",
        "filled": False,
    },
    "lambda_ac_40m": {
        "label": r"$\lambda_\mathrm{ac}$ = 40 m (conservative bracket end)",
        "color": figstyle.ORANGE,
        "marker": "o",
        "filled": True,
    },
    "bulk_d70": {
        "label": r"bulk $d_{70}$ interpretation",
        "color": figstyle.VIOLET,
        "marker": "s",
        "filled": True,
    },
    "prior_bep": {
        "label": "prior BEP curves (no 2016 update)",
        "color": figstyle.MAGENTA,
        "marker": "D",
        "filled": True,
    },
}


def figure_rq4_brackets(slice_: dict[str, Any]) -> tuple[Path, list[dict[str, Any]]]:
    """The three sensitivity brackets on the annual system number, side by side.

    Everything is drawn as a factor on the production deliverable, because that
    is how the brackets are quoted and it is the only presentation in which the
    length-effect knob, the grain-size interpretation and the Bayesian update
    are comparable. The absolute baseline sits in the right-hand column so a
    reader can convert any factor back to a probability.
    """
    by_section = {s["section"]: s for s in slice_["sections"]}
    # Both panels share one x range: comparing a bracket between climates is the
    # question, and two independent log axes would silently rescale it.
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.4), sharey=True, sharex=True)

    rows: list[dict[str, Any]] = []
    for ax, scenario, title in zip(
        axes,
        ("historical", "+4K"),
        ("A  historical climate", "B  +4K climate"),
    ):
        for index, name in enumerate(SECTIONS):
            y = len(SECTIONS) - 1 - index
            entry = next(
                e for e in by_section[name]["scenarios"] if e["scenario"] == scenario
            )
            ax.plot(
                [1.0],
                [y],
                marker="|",
                color=figstyle.INK_2,
                ms=13,
                mew=1.8,
                ls="none",
                zorder=3,
            )
            for arm in entry["arms"]:
                style = RQ4_ARM_STYLE[arm["arm"]]
                ax.plot(
                    [arm["ratio_system_to_baseline"]],
                    [y + (list(RQ4_ARM_STYLE).index(arm["arm"]) - 1.5) * 0.16],
                    marker=style["marker"],
                    color=style["color"],
                    mfc=style["color"] if style["filled"] else figstyle.SURFACE,
                    mew=1.5,
                    ms=6.5,
                    ls="none",
                    zorder=4,
                )
            # The absolute baseline is written on the reference mark itself, so
            # every factor on the row can be converted back to a probability
            # without a separate column that could be read against the wrong
            # panel.
            ax.annotate(
                f"{entry['baseline']['p_annual_system']:.2e}/yr",
                (1.0, y),
                textcoords="offset points",
                xytext=(-6, -21),
                fontsize=8,
                color=figstyle.INK_2,
                ha="right",
                va="center",
            )
        ax.axvline(1.0, color=figstyle.BASELINE, lw=1.0)
        ax.set_xscale("log")
        ax.set_xlim(1.2e-3, 7.0)
        ax.set_xlabel("factor on the production annual system $P_f$")
        ax.set_title(title, loc="left")

    axes[0].set_yticks(list(range(len(SECTIONS)))[::-1])
    axes[0].set_yticklabels(SECTIONS)
    axes[0].set_ylim(-0.72, len(SECTIONS) - 0.35)

    handles = [
        plt.Line2D(
            [],
            [],
            marker=style["marker"],
            color=style["color"],
            mfc=style["color"] if style["filled"] else figstyle.SURFACE,
            mew=1.5,
            ls="none",
            ms=6.5,
            label=style["label"],
        )
        for style in RQ4_ARM_STYLE.values()
    ]
    handles.append(
        plt.Line2D(
            [],
            [],
            marker="|",
            color=figstyle.INK_2,
            ls="none",
            ms=11,
            mew=1.8,
            label=r"production deliverable, labeled with its absolute "
            r"$P_f$/yr (matrix $d_{70}$, posterior, $\lambda_\mathrm{ac}$ = 250 m)",
        )
    )
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.012),
        frameon=False,
    )
    fig.suptitle(
        "Phase 3 sensitivity brackets on the annual system failure probability, "
        "at the four geotechnically characterized sections\n"
        r"the bulk $d_{70}$ arm reaches its floor wherever the historical number "
        "does, so the widest factors there are floor effects, not sensitivities",
        fontsize=11.5,
        x=0.008,
        y=0.995,
        ha="left",
        va="top",
    )
    fig.tight_layout(rect=(0, 0.10, 1, 0.935))

    for name in SECTIONS:
        for entry in by_section[name]["scenarios"]:
            rows.append(
                {
                    "section": name,
                    "scenario": entry["scenario"],
                    "arm": "baseline",
                    "p_annual_system": entry["baseline"]["p_annual_system"],
                    "p_annual_bep": entry["baseline"]["p_annual_bep"],
                    "share_bep": round(entry["baseline"]["share_bep"], 6),
                    "ratio_system_to_baseline": 1.0,
                    "ratio_bep_to_baseline": 1.0,
                    "bep_clamped_above_grid": entry["baseline"][
                        "bep_clamped_above_grid"
                    ],
                }
            )
            for arm in entry["arms"]:
                rows.append(
                    {
                        "section": name,
                        "scenario": entry["scenario"],
                        "arm": arm["arm"],
                        "p_annual_system": arm["p_annual_system"],
                        "p_annual_bep": arm["p_annual_bep"],
                        "share_bep": (
                            round(arm["share_bep"], 6)
                            if arm["share_bep"] is not None
                            else ""
                        ),
                        "ratio_system_to_baseline": round(
                            arm["ratio_system_to_baseline"], 6
                        ),
                        "ratio_bep_to_baseline": (
                            round(arm["ratio_bep_to_baseline"], 6)
                            if arm["ratio_bep_to_baseline"] is not None
                            else ""
                        ),
                        "bep_clamped_above_grid": arm["bep_clamped_above_grid"],
                    }
                )
    return figstyle.save(fig, "rq4_sensitivity_brackets.png", mirror=MIRROR), rows


# --------------------------------------------------------------------------- #
# Figure 5 -- the two accepted epistemic-knob companions (inventory 7.15/7.16)  #
# --------------------------------------------------------------------------- #

#: The two arms of the ADR-0046 datum bracket. A lower toe raises the head the
#: structure sees, so ``minus`` is the conservative end.
ZTOE_ARMS = (
    ("ztoe_minus0.30m", r"$z_\mathrm{toe}$ $-$0.30 m", "-"),
    ("ztoe_plus0.30m", r"$z_\mathrm{toe}$ $+$0.30 m", "--"),
)


def _ratio(arm: Sequence[float], baseline: Sequence[float]) -> np.ndarray:
    """Arm-over-baseline, with undefined cells masked rather than invented."""
    arm_a = np.asarray(arm, dtype=float)
    base_a = np.asarray(baseline, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(base_a > 0.0, arm_a / base_a, np.nan)
    return np.where(out > 0.0, out, np.nan)


def figure_epistemic_knobs(
    mp: dict[str, Any],
    ztoe: dict[str, Any],
    synthesis: dict[str, Any],
    attainable_max_kp62: float,
) -> tuple[Path, list[dict[str, Any]]]:
    """The Sellmeijer model factor and the exit-datum bracket, both branches.

    Neither knob is in the thesis at all, and both are accepted, default-OFF
    sensitivities measured at all four matrix sections. Drawn as a factor on the
    production curve against stage, because both effects are strongly
    stage-dependent -- which is the reason the bare word "shoulder" is banned
    here: ADR-0045 quotes m_p at the rising limb and ADR-0048 quotes k_aq at the
    transition midpoint, and those are stages two orders of magnitude apart in
    P_f. Every anchor is therefore marked at its stage and labelled with its
    baseline transient P_f.

    KP 62.0's grid runs to 56.5 m, past the 50.5 m attainable maximum, so
    ADR-0024's hypothetical extension is shaded on every panel.
    """
    sections_syn = {s["section"]: s for s in synthesis["sections"]}
    mp_by_section = {
        "KP" + s["cross_section_id"].split("kp")[1]: s for s in mp["sections"]
    }
    ztoe_by_section = {
        "KP" + s["cross_section_id"].split("kp")[1]: s for s in ztoe["sections"]
    }

    # The two committed companions must agree with the synthesis on what the
    # production baseline is; if they ever do not, every ratio below is
    # meaningless, so it is checked rather than assumed.
    for name in SECTIONS:
        expected = sections_syn[name]
        assert mp_by_section[name]["grid_m_msl"] == expected["grid_m_msl"]
        assert (
            mp_by_section[name]["p_f_trans_baseline"]
            == expected["P_f_trans_baseline_curve"]
        )
        assert (
            mp_by_section[name]["p_f_static_baseline"]
            == expected["P_f_static_baseline_curve"]
        )
        assert ztoe_by_section[name]["grid_m_msl"] == expected["grid_m_msl"]

    # One shared y range across all four panels: that m_p barely leaves the
    # unit line while the datum bracket swings two decades is itself the
    # finding, and per-panel autoscaling would hide it.
    fig, axes = plt.subplots(2, 2, figsize=(13.6, 7.6), sharex=True, sharey=True)
    rows: list[dict[str, Any]] = []

    panels = (
        (axes[0][0], "m_p", "static", r"A  $m_p$ on the static comparator"),
        (axes[0][1], "m_p", "transient", r"B  $m_p$ on the transient limit state"),
        (axes[1][0], "z_toe", "static", r"C  $z_\mathrm{toe}$ $\pm$0.3 m, static"),
        (
            axes[1][1],
            "z_toe",
            "transient",
            r"D  $z_\mathrm{toe}$ $\pm$0.3 m, transient",
        ),
    )

    for ax, knob, branch, title in panels:
        for name in SECTIONS:
            grid = np.asarray(sections_syn[name]["grid_m_msl"], dtype=float)
            baseline = (
                sections_syn[name]["P_f_static_baseline_curve"]
                if branch == "static"
                else sections_syn[name]["P_f_trans_baseline_curve"]
            )
            colour = figstyle.SECTION_COLORS[name]
            if knob == "m_p":
                arms = (
                    (
                        "m_p",
                        r"$m_p$ ~ LN(1.0, CoV 0.12)",
                        "-",
                        mp_by_section[name][
                            "p_f_static_mp" if branch == "static" else "p_f_trans_mp"
                        ],
                    ),
                )
            else:
                arms = tuple(
                    (
                        arm_key,
                        arm_label,
                        arm_style,
                        ztoe_by_section[name]["phase1"][arm_key][
                            "p_f_static" if branch == "static" else "p_f_trans"
                        ],
                    )
                    for arm_key, arm_label, arm_style in ZTOE_ARMS
                )
            for arm_key, _arm_label, arm_style, arm_curve in arms:
                ratio = _ratio(arm_curve, baseline)
                ax.plot(
                    grid,
                    ratio,
                    color=colour,
                    lw=1.9 if arm_style == "-" else 1.5,
                    ls=arm_style,
                    zorder=3,
                )
                for level, base_value, arm_value, value in zip(
                    grid, baseline, arm_curve, ratio
                ):
                    anchor_name = next(
                        (
                            key
                            for key in ANCHORS
                            if sections_syn[name]["anchors"][key]["stage_m_msl"]
                            == level
                        ),
                        "",
                    )
                    rows.append(
                        {
                            "knob": knob,
                            "arm": arm_key,
                            "section": name,
                            "branch": branch,
                            "stage_m_msl": float(level),
                            "above_attainable_max": bool(
                                name == "KP62.0" and level > attainable_max_kp62
                            ),
                            "p_f_baseline": float(base_value),
                            "p_f_arm": float(arm_value),
                            "ratio_arm_to_baseline": (
                                round(float(value), 6) if np.isfinite(value) else ""
                            ),
                            "anchor": anchor_name,
                            "p_f_trans_baseline_at_stage": sections_syn[name][
                                "P_f_trans_baseline_curve"
                            ][int(np.argmin(np.abs(grid - level)))],
                        }
                    )

            # Anchor markers: filled = rising limb, hollow = transition midpoint.
            if branch == "transient":
                primary_arm = arms[0]
                ratio = _ratio(primary_arm[3], baseline)
                for anchor_key, filled in (
                    ("rising_limb", True),
                    ("transition_midpoint", False),
                ):
                    stage = sections_syn[name]["anchors"][anchor_key]["stage_m_msl"]
                    index = int(np.argmin(np.abs(grid - stage)))
                    if not np.isfinite(ratio[index]):
                        continue
                    ax.plot(
                        [grid[index]],
                        [ratio[index]],
                        marker=figstyle.SECTION_MARKERS[name],
                        color=colour,
                        mfc=colour if filled else figstyle.SURFACE,
                        mew=1.5,
                        ms=6.5,
                        ls="none",
                        zorder=5,
                    )

        ax.axhline(1.0, color=figstyle.BASELINE, lw=1.0)
        ax.set_yscale("log")
        ax.set_ylim(3e-3, 4e2)
        ax.set_title(title, loc="left")
        figstyle.mark_hypothetical(
            ax, attainable_max_kp62, label=(ax is axes[0][1]), label_y=0.97
        )

    for ax in axes[:, 0]:
        ax.set_ylabel("factor on the production $P_f$")
    for ax in axes[1]:
        ax.set_xlabel("conditioning water level [m T.P.]")

    # The two numbers the inventory asks these panels to carry, marked where
    # they are measured rather than only stated in the caption.
    # Quoted from these curves rather than from ADR-0045's headline, which was
    # measured at two sections and at its own stage: the whole point of the
    # anchors marked below is that "the shoulder" names different stages in
    # different records.
    axes[0][0].annotate(
        r"$m_p$ raises the static branch $\times$3.0 to 6.0 at the deepest"
        "\nreachable level, falling through "
        r"$\times$1.3 to 1.7 at the marked"
        "\nrising limb, to within 2 % of 1 above the transition midpoint",
        xy=(0.025, 0.40),
        xycoords="axes fraction",
        fontsize=8,
        color=figstyle.INK_2,
        ha="left",
        va="top",
    )
    axes[0][1].annotate(
        r"transient maxima $\times$1.6 to 2.8 over the four sections,"
        "\nand "
        r"$\times$1.5 to 2.5 at the two informative"
        "\nmatrix sections alone",
        xy=(0.025, 0.40),
        xycoords="axes fraction",
        fontsize=8,
        color=figstyle.INK_2,
        ha="left",
        va="top",
    )
    kp62 = sections_syn["KP62.0"]
    hwl_stage = kp62["anchors"]["design_hwl"]["stage_m_msl"]
    hwl_index = kp62["grid_m_msl"].index(hwl_stage)
    span = kp62["brackets"]["z_toe"]["span"]["design_hwl"]
    lo = _ratio(
        ztoe_by_section["KP62.0"]["phase1"]["ztoe_plus0.30m"]["p_f_trans"],
        kp62["P_f_trans_baseline_curve"],
    )[hwl_index]
    hi = _ratio(
        ztoe_by_section["KP62.0"]["phase1"]["ztoe_minus0.30m"]["p_f_trans"],
        kp62["P_f_trans_baseline_curve"],
    )[hwl_index]
    axes[1][1].annotate(
        "",
        xy=(hwl_stage, hi),
        xytext=(hwl_stage, lo),
        arrowprops={
            "arrowstyle": "<|-|>",
            "color": figstyle.INK,
            "lw": 1.4,
            "shrinkA": 0,
            "shrinkB": 0,
        },
        zorder=6,
    )
    axes[1][1].annotate(
        f"span $\\times${span['span_trans']:.0f} at KP 62.0's design-level anchor\n"
        f"({hwl_stage:.2f} m MSL, the nearest grid level to its "
        f"{kp62['hwl_m_msl']:.2f} m HWL,\n"
        f"{kp62['anchors']['design_hwl']['n_failures_trans_baseline']} failing rows): "
        r"the second-largest knob there,"
        "\n"
        r"ahead of $L$ at $\times$15",
        xy=(hwl_stage, hi),
        xytext=(hwl_stage + 0.7, 1.6e2),
        fontsize=8,
        color=figstyle.INK,
        ha="left",
        va="top",
        arrowprops={"arrowstyle": "-", "color": figstyle.MUTED, "lw": 0.9},
    )

    handles = [
        plt.Line2D(
            [],
            [],
            color=figstyle.SECTION_COLORS[name],
            lw=2.0,
            marker=figstyle.SECTION_MARKERS[name],
            ms=6.5,
            label=name,
        )
        for name in SECTIONS
    ]
    handles += [
        plt.Line2D(
            [], [], color=figstyle.INK_2, lw=1.9, ls="-", label=r"$-$0.30 m arm"
        ),
        plt.Line2D(
            [], [], color=figstyle.INK_2, lw=1.5, ls="--", label=r"$+$0.30 m arm"
        ),
        plt.Line2D(
            [],
            [],
            color=figstyle.INK_2,
            marker="o",
            ls="none",
            ms=6.5,
            label=r"rising limb (baseline transient $P_f$ 4e-4 to 2e-3)",
        ),
        plt.Line2D(
            [],
            [],
            color=figstyle.INK_2,
            marker="o",
            mfc=figstyle.SURFACE,
            mew=1.5,
            ls="none",
            ms=6.5,
            label=r"transition midpoint (baseline transient $P_f$ $\approx$ 0.5)",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        bbox_to_anchor=(0.5, -0.008),
        frameon=False,
    )
    fig.suptitle(
        "The two epistemic knobs measured at all four matrix sections, "
        "on one shared scale\n"
        r"the Sellmeijer model factor $m_p$ and the surveyed exit datum "
        r"$\pm$0.3 m: both collapse toward 1 as $P_f$ saturates, and the "
        "datum is the wider of the two at the design anchor",
        fontsize=11.5,
        x=0.008,
        y=0.995,
        ha="left",
        va="top",
    )
    fig.tight_layout(rect=(0, 0.075, 1, 0.94))
    return figstyle.save(fig, "epistemic_knobs_mp_ztoe.png", mirror=MIRROR), rows


# --------------------------------------------------------------------------- #
# Figure 6 -- the WBI+ peak-only shortcut (inventory 4.7)                       #
# --------------------------------------------------------------------------- #

#: The peak-only reading and the full replay are both *transient*, so they are
#: two methods on one sample rather than two limit states. The transient hue is
#: kept for the deliverable; the shortcut gets slot 7, which validates against
#: it at deltaE 22.7 (protan) / 33.6 (normal).
SHORTCUT = figstyle.VIOLET
REPLAY = figstyle.TRANSIENT


def figure_peak_shortcut(slice_: dict[str, Any]) -> tuple[Path, list[dict[str, Any]]]:
    """What the time-resolved replay adds over a peak-only reading (row 4.7).

    The RQ2 clause this answers is comparative, so the figure is built around
    the *gap* rather than around either number. Panel A draws each stratum as a
    connector between the two readings on one log axis: the shortcut dot always
    sits to the right of the replay dot, and the connector is the over-rejection.
    Panel B is the same thing as a factor, so the 2.75 to 3.90 headline is
    readable without arithmetic.

    Three things the drawing refuses to blur:

    * a stratum where neither reading rejects anything has **no factor** -- it
      is not agreement (1.0) and not an infinite disagreement. Those four rows
      keep their place on the axis and say so, rather than being dropped;
    * the two strata whose factor rests on 65 and 23 rejected rows are marked
      as the small-number regime ``docs/phase2_report.md`` section 11.1 calls
      them, and are excluded from the headline band;
    * the headline band spans only the two informative strata, which is the
      scope in which "2.75 to 3.9x" is a measurement.
    """
    strata = slice_["strata"]
    headline = slice_["headline"]
    fig, (ax, axb) = plt.subplots(
        1, 2, figsize=(13.4, 5.7), gridspec_kw={"width_ratios": [1.45, 1.0]}
    )

    # --- Panel A: the gap, per stratum -------------------------------------- #
    ypos = np.arange(len(strata))[::-1]
    floor = 0.01  # [%] log-axis floor; below it a value is drawn as "0"
    for y, s in zip(ypos, strata):
        peak_only = s["f_peak_only_transient"] * 100.0
        replay = s["f_replay_transient"] * 100.0
        if s["over_rejection_factor"] is None:
            ax.text(
                floor * 1.35,
                y,
                "0 and 0; no factor defined",
                va="center",
                fontsize=8.5,
                color=figstyle.MUTED,
                style="italic",
            )
            continue
        ax.plot(
            [replay, peak_only],
            [y, y],
            color=figstyle.BASELINE,
            lw=2.6,
            solid_capstyle="round",
            zorder=2,
        )
        ax.plot(
            replay,
            y,
            "o",
            ms=9,
            color=REPLAY,
            mec=figstyle.SURFACE,
            mew=1.4,
            zorder=4,
            label="full transient replay (the deliverable)" if y == ypos[0] else None,
        )
        ax.plot(
            peak_only,
            y,
            "D",
            ms=8.5,
            color=SHORTCUT,
            mec=figstyle.SURFACE,
            mew=1.4,
            zorder=4,
            label="peak-only reading (WBI+ shortcut)" if y == ypos[0] else None,
        )
        # Three labels per row, staggered so none can collide: the two values
        # on their own marks, the factor above the connector that earns it.
        ax.text(
            peak_only * 1.30,
            y,
            f"{peak_only:.3f}",
            va="center",
            fontsize=8,
            color=SHORTCUT,
        )
        ax.text(
            replay * 0.77,
            y,
            f"{replay:.3f}",
            va="center",
            ha="right",
            fontsize=8,
            color=REPLAY,
        )
        ax.text(
            float(np.sqrt(replay * peak_only)),
            y + 0.26,
            rf"$\times${s['over_rejection_factor']:.2f}",
            va="bottom",
            ha="center",
            fontsize=9.5,
            color=figstyle.INK,
            fontweight="bold",
        )
    ax.set_xscale("log")
    ax.set_xlim(floor, 60.0)
    # Headroom for the top row's factor label, which rides above its connector.
    ax.set_ylim(-0.7, len(strata) - 1 + 0.85)
    ax.set_yticks(ypos)
    ax.set_yticklabels(
        [
            f"{s['section']}  {s['d70']}" + ("  *" if s["small_number_regime"] else "")
            for s in strata
        ]
    )
    ax.set_xlabel("share of the N = $10^5$ prior sample rejected [%], log scale")
    ax.set_title("A  the same 2016 survival read two ways, per stratum", loc="left")
    # Upper right: the only quadrant no mark or annotation reaches (the top two
    # rows carry the smallest values, so their right half is empty).
    ax.legend(loc="upper right")

    # --- Panel B: the factor ------------------------------------------------ #
    defined = [s for s in strata if s["over_rejection_factor"] is not None]
    bpos = np.arange(len(defined))[::-1]
    factors = [s["over_rejection_factor"] for s in defined]
    axb.axvspan(
        headline["factor_min"],
        headline["factor_max"],
        color=SHORTCUT,
        alpha=0.13,
        lw=0,
        zorder=0,
        label=(
            "headline band: informative strata only, "
            rf"$\times${headline['factor_min']:.2f} to "
            rf"$\times${headline['factor_max']:.2f}"
        ),
    )
    axb.axvline(1.0, color=figstyle.BASELINE, lw=1.4, zorder=1)
    axb.barh(
        bpos,
        factors,
        height=0.5,
        color=[
            figstyle.MUTED if s["small_number_regime"] else SHORTCUT for s in defined
        ],
        hatch=["///" if s["small_number_regime"] else "" for s in defined],
        edgecolor=figstyle.SURFACE,
        lw=0,
        zorder=3,
    )
    for y, s in zip(bpos, defined):
        axb.text(
            s["over_rejection_factor"] + 0.14,
            y,
            rf"$\times${s['over_rejection_factor']:.2f}",
            va="center",
            fontsize=9.5,
            fontweight="normal" if s["small_number_regime"] else "bold",
            color=figstyle.MUTED if s["small_number_regime"] else figstyle.INK,
        )
    axb.axvline(1.0, color=figstyle.BASELINE, lw=1.4, zorder=1)
    axb.text(
        1.06,
        -0.62,
        "agreement",
        fontsize=8,
        color=figstyle.MUTED,
        va="center",
        ha="left",
    )
    axb.set_yticks(bpos)
    # The rejected-row count rides on the tick label rather than trailing the
    # bar: it belongs to the stratum, and as a bar annotation it overflowed the
    # axis on the two widest bars.
    axb.set_yticklabels(
        [
            f"{s['section']}  {s['d70']}\n{s['n_rejected_replay']:,} rejected rows"
            + ("  *" if s["small_number_regime"] else "")
            for s in defined
        ],
        fontsize=9,
    )
    axb.set_ylim(-0.9, len(defined) - 0.35)
    axb.set_xlim(0, 10.6)
    axb.set_xlabel("over-rejection factor, peak-only / replay [-]")
    axb.set_title("B  how much the shortcut over-rejects", loc="left")
    axb.legend(loc="lower right", fontsize=8.5)

    fig.suptitle(
        "The peak-only reading of the 2016 survival rejects realizations the "
        "full transient replay retains:\n"
        rf"$\times${headline['factor_min']:.2f} (KP 58.8) and "
        rf"$\times${headline['factor_max']:.2f} (KP 60.0), the two strata where the "
        "update is informative. Both readings are transient, on one N = $10^5$ "
        "sample.",
        fontsize=11.5,
        x=0.008,
        y=0.995,
        ha="left",
        va="top",
    )
    fig.text(
        0.008,
        0.012,
        "Mechanism: the Phase 1 curves condition on the canonical d4PDF "
        "compound shape scaled to each level, which carries far more above-toe "
        "exposure than the real 2016 event did at the same peak, so a reading "
        "that sees only the peak cannot tell the two apart.\n"
        "* small-number regime: the factor is a ratio of two small counts. "
        "Peak-only values are the prior transient curve interpolated linearly "
        "on its raw Monte Carlo points at the observed peak.",
        fontsize=8,
        color=figstyle.MUTED,
        ha="left",
        va="bottom",
        linespacing=1.35,
    )
    fig.tight_layout(rect=(0, 0.085, 1, 0.925))

    rows = [
        {
            "section": s["section"],
            "d70": s["d70"],
            "n_prior": s["n_prior"],
            "event_peak_m_msl": round(s["event_peak_m_msl"], 3),
            "z_toe_m_msl": s["z_toe_m_msl"],
            "peak_only_transient_pct": round(s["f_peak_only_transient"] * 100, 4),
            "replay_transient_pct": round(s["f_replay_transient"] * 100, 4),
            "over_rejection_factor": (
                "not defined"
                if s["over_rejection_factor"] is None
                else round(s["over_rejection_factor"], 3)
            ),
            "n_rejected_replay": s["n_rejected_replay"],
            "n_peak_only_expected": s["n_peak_only_expected"],
            "small_number_regime": s["small_number_regime"],
        }
        for s in strata
    ]
    return figstyle.save(fig, "phase2_peak_shortcut.png", mirror=MIRROR), rows


# --------------------------------------------------------------------------- #
# figures: committed evidence -> six figures and six table sources              #
# --------------------------------------------------------------------------- #

#: Every figure this driver owns, with the CSV that carries its numbers. The
#: CSV is the table source a thesis session typesets from; both are written in
#: the same call from the same evidence so they cannot drift apart.
FIGURE_CSV = {
    "phase2_survival_update.png": "phase2-survival-update-per-stratum.csv",
    "epistemic_bracket_ranking.png": "epistemic-bracket-ranking.csv",
    "adr0040_kp57_4_bound.png": "adr0040-kp57_4-bias-bound.csv",
    "rq4_sensitivity_brackets.png": "rq4-sensitivity-brackets.csv",
    "epistemic_knobs_mp_ztoe.png": "epistemic-knobs-mp-ztoe.csv",
    "phase2_peak_shortcut.png": "phase2-peak-shortcut.csv",
}


def cmd_figures(args: argparse.Namespace) -> dict[str, Any]:
    """Draw all six figures and write all six table sources.

    Reads committed evidence only. Runs no physics, and touches no evidence
    file: the three slices under ``docs/decisions/`` are inputs here, written
    by ``extract``.
    """
    for path, why in (
        (PHASE2_SLICE, "figure 1 -- run `thesis_figure_gaps.py extract` first"),
        (RQ4_SLICE, "figure 4 -- run `thesis_figure_gaps.py extract` first"),
        (
            PEAK_SHORTCUT_SLICE,
            "figure 6 -- run `thesis_figure_gaps.py extract` first",
        ),
        (SYNTHESIS, "figures 2 and 5"),
        (HWL_EVIDENCE, "figure 3"),
        (MP_COMPANION, "figure 5"),
        (ZTOE_COMPANION, "figure 5"),
        (STAGE66_KP62, "ADR-0024's attainable maximum stage"),
    ):
        _require(path, why)

    figstyle.style()
    attainable_max = _attainable_max_kp62()
    synthesis = _read_json(SYNTHESIS)

    written: list[tuple[Path, list[dict[str, Any]]]] = [
        figure_phase2_survival(_read_json(PHASE2_SLICE)),
        figure_epistemic_ranking(synthesis, attainable_max),
        figure_kp57_4_bound(_read_json(HWL_EVIDENCE)),
        figure_rq4_brackets(_read_json(RQ4_SLICE)),
        figure_epistemic_knobs(
            _read_json(MP_COMPANION),
            _read_json(ZTOE_COMPANION),
            synthesis,
            attainable_max,
        ),
        figure_peak_shortcut(_read_json(PEAK_SHORTCUT_SLICE)),
    ]

    produced: list[str] = []
    for figure_path, rows in written:
        produced.append(figure_path.relative_to(REPO_ROOT).as_posix())
        print(f"wrote {produced[-1]}")
        csv_path = _write_csv(FIGURE_CSV[figure_path.name], list(rows[0]), rows)
        produced.append(csv_path.relative_to(REPO_ROOT).as_posix())
    return {"written": produced}


def cmd_all(args: argparse.Namespace) -> dict[str, Any]:
    """Extract the three slices, then draw everything."""
    return {"extract": cmd_extract(args), "figures": cmd_figures(args)}


COMMANDS: dict[str, Callable[[argparse.Namespace], dict[str, Any]]] = {
    "extract": cmd_extract,
    "figures": cmd_figures,
    "all": cmd_all,
}


def main(argv: Sequence[str] | None = None) -> int:
    # The parser is built and the arguments parsed before anything is read or
    # written, so `--help` and a stray flag are both inert. A --help sweep once
    # ran a study here and rewrote a tracked evidence file.
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "command",
        choices=sorted(COMMANDS),
        help="extract the committed evidence slices, draw the figures, or both",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DECISIONS,
        help="where `extract` writes its slices (default: docs/decisions/)",
    )
    args = parser.parse_args(argv)
    MIRROR.mkdir(parents=True, exist_ok=True)
    COMMANDS[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
