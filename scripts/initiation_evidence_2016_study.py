"""What the 2016 flood shows about initiation and dominance (Pol 3, 6, 7, 9, 11).

Driver for ``docs/decisions/initiation-evidence-2016-study.md``. Companion
study: no production default, config, prior, kernel, persisted sweep, posterior
or annual result changes. Nothing is re-swept: every row-level input is a
persisted Phase 1 sweep, its persisted 2016 replay, or the same-head flags of
the ADR-0055 study (``time_dependence_factor_study``), whose cache is refused
unless its gross-head column reproduces the persisted static column.

``gate``         closed-form 2016 initiation against the stored replay flags,
                 breach inside initiation, transient inside same-head failure,
                 and the rebuilt no-breach posterior curve against production.
``initiation``   the model's probability that an exit opened in 2016, prior and
                 after the no-breach update, per section and configuration
                 (as if undrained, bulk, measured berm, berm with exit-gradient
                 relief); the four-way decomposition of the 2016 outcome (no
                 exit / exit held by resistance / held only by duration /
                 breach); a toe-pressure factor sweep for session 4.
``conditioning`` posterior fragility under a detection probability ``p_d`` for
                 an opened exit (``p_d = 0`` is the adopted no-breach update,
                 ``p_d = 1`` the strict no-initiation filter), both criteria.
``annual``       each conditioning arm through the production Phase 3
                 annualisation with the member-block bootstrap; gate: the
                 rebuilt no-breach arm reproduces the production table.
``dominance``    return periods of the 2016 peaks, where the annual probability
                 is earned relative to the 2016 peak and the design level,
                 conditional probabilities at the 2016 peak, crest margins.
``figures``      the two thesis figures (docs/figures/), house style.
``report``       assemble ``docs/decisions/initiation-evidence-2016-study.json``.

Usage (from the worktree root, main venv, ``PYTHONPATH=.``)::

    python scripts/initiation_evidence_2016_study.py gate --results-root <main>/results
    python scripts/initiation_evidence_2016_study.py initiation --results-root ...
    python scripts/initiation_evidence_2016_study.py conditioning --results-root ...
    python scripts/initiation_evidence_2016_study.py annual --results-root ...
    python scripts/initiation_evidence_2016_study.py dominance --results-root ...
    python scripts/initiation_evidence_2016_study.py figures --results-root ...
    python scripts/initiation_evidence_2016_study.py report
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from numpy.typing import NDArray

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bep_reliability_engine.constants import GAMMA_W  # noqa: E402


def _load_module(name: str):
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The ADR-0055 driver supplies the comparator flags, the section constants and
#: the curve constructor. Imported, never restated.
tdf = _load_module("time_dependence_factor_study")

KPS = tdf.KPS
DESIGN_HWL = tdf.DESIGN_HWL
ATTAINABLE_MAX = tdf.ATTAINABLE_MAX
DESIGN_GRID = tdf.DESIGN_GRID
PEAK_2016 = tdf.PEAK_2016
R1 = tdf.R1_MIN_TRANSIENT
SEED = 20261008
CANONICAL_EVENT = "HPB_m064_1987"

#: Detection probabilities of an opened exit. 0 is the adopted no-breach
#: update, 1 the strict no-initiation filter (ADR-0036 variant).
P_D: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)
#: The finer grid of the annual detection-probability curve (point values).
P_D_FINE: tuple[float, ...] = (
    0.0,
    0.25,
    0.5,
    0.75,
    0.9,
    0.95,
    0.98,
    0.99,
    0.995,
    0.998,
    1.0,
)
#: Factors by which the instantaneous toe overpressure may over-predict the
#: real one (thesis 4.7.2: 1.13 to 2.67 across four field comparisons).
PRESSURE_FACTORS: tuple[float, ...] = (1.0, 1.13, 1.25, 1.5, 2.0, 2.67)

OUT_DIR = REPO / "results" / "initiation_evidence_2016"
EVIDENCE = REPO / "docs" / "decisions" / "initiation-evidence-2016-study.json"


def _stem(kp: float, d70: str = "matrix") -> str:
    return tdf._stem(kp, d70)


def _label(kp: float) -> str:
    return tdf._label(kp)


def _write_stage(part: str, payload: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"stage_{part}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def _read_stage(part: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / f"stage_{part}.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Configurations                                                               #
# --------------------------------------------------------------------------- #
#: (key, label, sections, relief kept or None). "kept" is the ADR-0050 factor:
#: the share of the exit gradient that SURVIVES the drain (0.40 = 60 % relief).
CONFIGS: tuple[tuple[str, str, tuple[float, ...], float | None], ...] = (
    ("undrained", "as if undrained (adopted)", KPS, None),
    ("bulk", "bulk d70 reading", KPS, None),
    ("berm", "measured berm, inert drain", (58.8, 60.0), None),
    ("berm_relief_20pct", "berm, 20 % exit-gradient relief", (58.8, 60.0), 0.80),
    ("berm_relief_40pct", "berm, 40 % exit-gradient relief", (58.8, 60.0), 0.60),
    ("berm_relief_60pct", "berm, 60 % exit-gradient relief", (58.8, 60.0), 0.40),
    ("berm_relief_80pct", "berm, 80 % exit-gradient relief", (58.8, 60.0), 0.20),
)


def _paths(results_root: Path, config: str, kp: float) -> tuple[Path, Path, str]:
    """(Phase 1 prior, Phase 2 posterior, same-head flag cache key)."""
    if config == "undrained":
        s = _stem(kp)
        return results_root / f"{s}.h5", results_root / f"phase2/{s}_posterior.h5", s
    if config == "bulk":
        s = _stem(kp, "bulk")
        return results_root / f"{s}.h5", results_root / f"phase2/{s}_posterior.h5", s
    s = _stem(kp)
    drained = results_root / "sensitivity" / "adr0050_drained_bracket"
    if config == "berm":
        return (
            drained / f"{s}_berm_only.h5",
            drained / "phase2" / f"{s}_berm_only_posterior.h5",
            f"{s}_berm_only",
        )
    relief = int(config.split("_")[2].rstrip("pct"))
    kept = f"{1 - relief / 100:.2f}"
    return (
        drained / f"{s}_joint_{kept}.h5",
        drained / "phase2" / f"{s}_joint_{kept}_posterior.h5",
        f"{s}_{config}",
    )


def _kept(config: str) -> float:
    for key, _, _, kept in CONFIGS:
        if key == config:
            return 1.0 if kept is None else float(kept)
    raise KeyError(config)


class Bundle:
    """One section and configuration: rows, flags, 2016 replay, record peak."""

    def __init__(self, results_root: Path, config: str, kp: float):
        prior, post, key = _paths(results_root, config, kp)
        self.config, self.kp = config, kp
        self.prior_path, self.post_path = prior, post
        self.run, flags = tdf._cached_flags(prior, key)
        self.c3b = np.asarray(flags["C3b"], dtype=bool)
        self.c0 = np.asarray(flags["C0"], dtype=bool)
        self.tran = np.asarray(self.run.result.failure_matrix_tran, dtype=bool)
        self.grid = np.asarray(self.run.result.conditioning_grid, dtype=np.float64)
        self.z_toe = float(self.run.geometry["z_toe"])
        self.theta = np.asarray(self.run.theta, dtype=np.float64)
        self.L = np.asarray(self.run.seepage_length_samples, dtype=np.float64)
        with h5py.File(post, "r") as h5:
            (event,) = list(h5["events"].keys())
            g = h5["events"][event]
            self.ev = {k: np.asarray(g[k][:]) for k in g.keys()}
            names = [
                x.decode() if isinstance(x, bytes) else x for x in h5["param_names"]
            ]
            if not np.array_equal(np.asarray(h5["theta_matrix"][:]), self.theta):
                raise SystemExit(f"{post.name}: theta differs from its Phase 1 run")
        self.names = names
        meta = json.loads(post.with_suffix(".json").read_text(encoding="utf-8"))
        chain = meta["phase2"]["event_chain"][0]
        self.peak = float(chain["record"]["peak_m_msl"])
        self.criterion = chain["criterion"]
        self.accept = self.ev["accept_trans"].astype(bool)
        self.init = self.ev["initiation"].astype(bool)
        self.r_e = self.ev["r_e"].astype(np.float64)
        d_bl = self.theta[:, names.index("D_bl")]
        gam = self.theta[:, names.index("gamma_bl_sub")]
        self.weight_head = (gam / GAMMA_W) * d_bl
        # Same-head survival of the record (ADR-0055): gate at the peak and the
        # erosion head above H_c at the peak.
        self.same_head_survive = tdf._same_head_survival(
            {
                "Z_static": self.ev["Z_static"].astype(np.float64),
                "initiation": self.init,
                "d_bl": d_bl,
            }
        )
        self.gross_survive = self.ev["accept_static"].astype(bool)

    @property
    def n(self) -> int:
        return int(self.theta.shape[0])

    def gate_closed_form(self, factor: float = 1.0) -> NDArray[np.bool_]:
        """2016 initiation with the toe overpressure divided by ``factor``."""
        head = self.r_e * _kept(self.config) * (self.peak - self.z_toe) / factor
        return head > self.weight_head

    def weights(self, p_d: float) -> NDArray[np.float64]:
        """Likelihood of 'no breach, no boil recorded' for each row."""
        w = np.where(self.init, 1.0 - p_d, 1.0)
        return np.where(self.accept, w, 0.0)


def _bundles(results_root: Path, configs=None) -> dict[tuple[str, float], Bundle]:
    out = {}
    for key, _, kps, _ in CONFIGS:
        if configs is not None and key not in configs:
            continue
        for kp in kps:
            out[(key, kp)] = Bundle(results_root, key, kp)
    return out


def _cp(k: int, n: int) -> list[float]:
    return [float(x) for x in tdf._cp(int(k), int(n))]


# --------------------------------------------------------------------------- #
# Weighted curves                                                              #
# --------------------------------------------------------------------------- #
def weighted_p(matrix: NDArray[np.bool_], w: NDArray[np.float64]) -> NDArray:
    s = float(w.sum())
    if s <= 0.0:
        return np.full(matrix.shape[1], np.nan)
    return (w @ matrix.astype(np.float64)) / s


def ess(w: NDArray[np.float64]) -> float:
    s2 = float((w * w).sum())
    return float(w.sum()) ** 2 / s2 if s2 > 0 else 0.0


def weighted_curve(b: Bundle, w: NDArray[np.float64], source: str, *, static=False):
    """A transient (or same-head) FragilityCurve on weighted rows, fitted as M9."""
    from bep_reliability_engine.fragility import binomial_ci, fit_lognormal_fragility
    from system_integration.bep_input import FragilityCurve, _deliverable_fit

    matrix = b.c3b if static else b.tran
    p_raw = weighted_p(matrix, w)
    n_eff = max(1, int(round(ess(w))))
    lower, upper = binomial_ci(p_raw, n_eff, 0.95)
    try:
        fit = fit_lognormal_fragility(b.grid, p_raw, b.z_toe)
    except ValueError:
        fit = None
    return FragilityCurve(
        grid_m_msl=b.grid.copy(),
        p_raw=np.asarray(p_raw, dtype=np.float64),
        ci_lower=np.asarray(lower, dtype=np.float64),
        ci_upper=np.asarray(upper, dtype=np.float64),
        fit=fit,
        fit_is_deliverable=_deliverable_fit(fit, np.asarray(p_raw)),
        branch="static" if static else "transient",
        source=source,
        source_path=str(b.post_path),
        datum_m=b.z_toe,
    )


# --------------------------------------------------------------------------- #
# Part: gate                                                                   #
# --------------------------------------------------------------------------- #
def gate_part(results_root: Path) -> dict[str, Any]:
    from system_integration.bep_input import load_bep_curve

    out: dict[str, Any] = {}
    for (config, kp), b in _bundles(results_root).items():
        closed = b.gate_closed_form()
        mism = int(np.count_nonzero(closed != b.init))
        breach_outside_init = int(np.sum(~b.accept & ~b.init))
        trans_outside_same_head = int(np.sum(~b.accept & b.same_head_survive))
        entry = {
            "criterion_of_persisted_replay": b.criterion,
            "record_peak_m": b.peak,
            "closed_form_initiation_mismatches": mism,
            "breaches_without_initiation": breach_outside_init,
            "transient_breaches_outside_same_head_failure": trans_outside_same_head,
        }
        if mism or breach_outside_init or trans_outside_same_head:
            raise SystemExit(f"{config} {_label(kp)}: gate failed {entry}")
        if config == "undrained":
            mine = weighted_curve(b, b.weights(0.0), "rebuilt")
            prod = load_bep_curve(b.post_path, branch="transient")
            if not np.array_equal(mine.p_raw, prod.p_raw):
                raise SystemExit(f"{_label(kp)}: rebuilt posterior p_raw differs")
            if (mine.fit is None) != (prod.fit is None):
                raise SystemExit(f"{_label(kp)}: rebuilt fit presence differs")
            if mine.fit is not None:
                dmu = abs(mine.fit.mu - prod.fit.mu)
                dsig = abs(mine.fit.sigma - prod.fit.sigma)
                entry["rebuilt_fit_abs_dev"] = [dmu, dsig]
                if max(dmu, dsig) > 1e-12:
                    raise SystemExit(f"{_label(kp)}: rebuilt fit differs {dmu} {dsig}")
            entry["rebuilt_posterior_curve"] = "identical to production"
        out[f"{config} {_label(kp)}"] = entry
        print(f"  gate {config} {_label(kp)}: passed", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: initiation                                                             #
# --------------------------------------------------------------------------- #
def _record_h(kp: float, data_root: Path) -> tuple[NDArray, float]:
    from bayesian_reliability_updating.events import (
        default_2016_source,
        observed_event_record,
    )

    src = default_2016_source(data_root.parent / "processed" / "2016_event")
    r = observed_event_record(src, section_kp=kp, data_root=data_root)
    return np.asarray(r.h, dtype=np.float64), float(r.peak)


def _quart(x: NDArray) -> list[float] | None:
    if x.size == 0:
        return None
    return [float(v) for v in np.percentile(x, [25, 50, 75])]


def initiation_part(results_root: Path, data_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    records = {kp: _record_h(kp, data_root) for kp in KPS}
    for (config, kp), b in _bundles(results_root).items():
        h, peak = records[kp]
        if abs(peak - b.peak) > 1e-9:
            raise SystemExit(f"{_label(kp)}: record peak {peak} != replay {b.peak}")
        n = b.n
        init, acc = b.init, b.accept
        resist = init & b.same_head_survive
        duration = ~b.same_head_survive & acc
        breach = ~acc
        k_init = int(init.sum())
        k_breach = int(breach.sum())
        # Hours with the gate open, among rows that initiated.
        head = (
            b.r_e[:, None] * _kept(config) * (h[None, :] - b.z_toe)
            > b.weight_head[:, None]
        )
        hours_open = head.sum(axis=1)[init]
        d_aq = b.theta[:, b.names.index("D_aq")]
        l_c = 0.5 * b.L * np.tanh(2.0 * d_aq / b.L)
        lef = b.ev["l_e_final"].astype(np.float64)
        surv_init = init & acc
        entry: dict[str, Any] = {
            "n": n,
            "record_peak_m": b.peak,
            "z_toe_m": b.z_toe,
            "P_initiation_prior": k_init / n,
            "P_initiation_prior_ci95": _cp(k_init, n),
            "P_breach": k_breach / n,
            "P_initiation_given_no_breach": (k_init - k_breach) / (n - k_breach),
            "P_no_initiation": 1.0 - k_init / n,
            "n_no_initiation": n - k_init,
            "decomposition": {
                "no_exit": float(np.mean(~init)),
                "exit_held_by_resistance": float(np.mean(resist)),
                "exit_held_only_by_duration": float(np.mean(duration)),
                "breach": float(np.mean(breach)),
            },
            "same_head_static_rejected": float(np.mean(~b.same_head_survive)),
            "gross_static_rejected": float(np.mean(~b.gross_survive)),
            "hours_gate_open_initiated_quartiles": _quart(hours_open),
            "initiated_survivors_past_l_c": (
                float(np.mean(lef[surv_init] >= l_c[surv_init]))
                if surv_init.any()
                else None
            ),
            "initiated_survivors_l_end_over_L_quartiles": _quart(
                (lef / b.L)[surv_init]
            ),
        }
        if config in ("undrained", "berm"):
            entry["pressure_factor_sweep"] = {
                f"{f:g}": float(np.mean(b.gate_closed_form(f)))
                for f in PRESSURE_FACTORS
            }
        # The prior means of the gate's ingredients at the record peak.
        entry["prior_mean_gate_head_m"] = float(
            np.mean(b.r_e) * _kept(config) * (b.peak - b.z_toe)
        )
        entry["prior_mean_weight_head_m"] = float(np.mean(b.weight_head))
        out[f"{config} {_label(kp)}"] = entry
        print(
            f"  initiation {config} {_label(kp)}: P_init {k_init / n:.4f}",
            flush=True,
        )
    return out


# --------------------------------------------------------------------------- #
# Part: conditioning                                                           #
# --------------------------------------------------------------------------- #
COND_CONFIGS = (
    "undrained",
    "berm",
    "berm_relief_40pct",
    "berm_relief_60pct",
    "berm_relief_80pct",
)


def _idx(grid: NDArray, stage: float) -> int:
    return int(np.argmin(np.abs(grid - stage)))


def conditioning_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for (config, kp), b in _bundles(results_root, COND_CONFIGS).items():
        base_w = b.weights(0.0)
        p_t0 = weighted_p(b.tran, base_w)
        p_i0 = weighted_p(b.c3b, base_w)
        prior_means = {
            nm: float(b.theta[:, i].mean()) for i, nm in enumerate(b.names)
        } | {"L": float(b.L.mean())}
        arms: dict[str, Any] = {}
        bound_violations = 0
        for p_d in P_D:
            w = b.weights(p_d)
            p_t = weighted_p(b.tran, w)
            p_i = weighted_p(b.c3b, w)
            k_t = (w[:, None] * b.tran).sum(axis=0)
            if p_d < 1.0:
                with np.errstate(divide="ignore", invalid="ignore"):
                    r = p_t / p_t0
                ok = np.isfinite(r)
                lo, hi = 1.0 - p_d - 1e-12, 1.0 / (1.0 - p_d) + 1e-12
                bound_violations += int(np.sum((r[ok] < lo) | (r[ok] > hi)))
            sw = float(w.sum())
            means = {
                nm: float((w @ b.theta[:, i]) / sw) for i, nm in enumerate(b.names)
            } | {"L": float((w @ b.L) / sw)}
            levels = []
            for i, h in enumerate(b.grid):
                if h > ATTAINABLE_MAX[kp] + 1e-9:
                    continue
                levels.append(
                    {
                        "stage_m": float(h),
                        "P_trans": float(p_t[i]),
                        "P_same_head": float(p_i[i]),
                        "weighted_trans_failures": float(k_t[i]),
                        "ratio_trans_to_no_breach": (
                            float(p_t[i] / p_t0[i]) if p_t0[i] > 0 else None
                        ),
                    }
                )
            i_d = _idx(b.grid, DESIGN_GRID[kp])
            i_p = _idx(b.grid, PEAK_2016[kp])
            arms[f"{p_d:g}"] = {
                "p_d": p_d,
                "sum_weights": sw,
                "retained_share": sw / b.n,
                "ESS": ess(w),
                "design_grid_m": float(b.grid[i_d]),
                "P_trans_design_grid": float(p_t[i_d]),
                "P_same_head_design_grid": float(p_i[i_d]),
                "P_trans_at_2016_peak_grid": float(p_t[i_p]),
                "posterior_means": means,
                "mean_shift_vs_prior": {
                    k: means[k] / prior_means[k] - 1.0 for k in prior_means
                },
                "levels": levels,
            }
        if bound_violations:
            raise SystemExit(f"{config} {_label(kp)}: H3 bound violated")
        # H1: strict against no-breach at count-qualified stages.
        strict = arms["1"]["levels"]
        base = arms["0"]["levels"]
        rises = [
            s["stage_m"]
            for s, z in zip(strict, base, strict=True)
            if s["weighted_trans_failures"] >= R1
            and z["weighted_trans_failures"] >= R1
            and s["P_trans"] > z["P_trans"]
        ]
        out[f"{config} {_label(kp)}"] = {
            "prior_means": prior_means,
            "H3_bound_violations": 0,
            "H1_stages_where_strict_exceeds_no_breach": rises,
            "P_trans_no_breach_design_grid": float(p_t0[_idx(b.grid, DESIGN_GRID[kp])]),
            "P_same_head_no_breach_design_grid": float(
                p_i0[_idx(b.grid, DESIGN_GRID[kp])]
            ),
            "arms": arms,
        }
        print(f"  conditioning {config} {_label(kp)}: done", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: annual                                                                 #
# --------------------------------------------------------------------------- #
#: (arm key, drained-section configuration, p_d, criterion branch).
ANNUAL_ARMS: tuple[tuple[str, str, float, str], ...] = (
    ("undrained pd0 T", "undrained", 0.0, "T"),
    ("undrained pd0.5 T", "undrained", 0.5, "T"),
    ("undrained pd0.9 T", "undrained", 0.9, "T"),
    ("undrained pd1 T", "undrained", 1.0, "T"),
    ("undrained pd1 I", "undrained", 1.0, "I"),
    ("berm pd0 T", "berm", 0.0, "T"),
    ("berm pd0.5 T", "berm", 0.5, "T"),
    ("berm pd1 T", "berm", 1.0, "T"),
    ("berm_relief_60pct pd0 T", "berm_relief_60pct", 0.0, "T"),
    ("berm_relief_60pct pd1 T", "berm_relief_60pct", 1.0, "T"),
)


def _campaign(results_root: Path):
    unc = _load_module("annualisation_uncertainty_study")
    data_repo = results_root.parent
    unc.PRODUCTION_TABLE = results_root / "system_integration/phase3/rq4_annual.csv"
    campaign = unc._load_campaign_module()
    campaign.REPO = data_repo
    campaign.DATA_ROOT = data_repo / "data/raw"
    campaign.HAZARD_CACHE = results_root / "system_integration/hazard_cache"
    return unc, campaign


def annual_part(results_root: Path, replicates: int) -> dict[str, Any]:
    unc, campaign = _campaign(results_root)
    cache_before = unc._dir_state(campaign.HAZARD_CACHE, "*.csv")
    context = unc.build_context(campaign)
    production = dict(context["bep_curves"])
    bundles = _bundles(results_root, ("undrained", "berm", "berm_relief_60pct"))

    rows: dict[str, Any] = {}
    per_event: dict[str, Any] = {}
    # Production no-breach posterior first, then gate (iii).
    r, pe = unc.annualise_arm(campaign, context, "matrix", "posterior")
    rows["production"], per_event["production"] = r, pe
    bulk = {
        unc._arm_key("bulk", s): unc.annualise_arm(campaign, context, "bulk", s)[0]
        for s in ("prior", "posterior")
    }
    gate = unc.gate_one(
        {
            unc._arm_key("matrix", "prior"): unc.annualise_arm(
                campaign, context, "matrix", "prior"
            )[0],
            unc._arm_key("matrix", "posterior"): rows["production"],
            **bulk,
        }
    )
    print(f"  gate (iii) passed: {gate['rows_compared']} rows", flush=True)

    for arm, config, p_d, crit in ANNUAL_ARMS:
        for kp in KPS:
            cfg = (
                config if (config == "undrained" or kp in (58.8, 60.0)) else "undrained"
            )
            b = bundles[(cfg, kp)]
            w = b.weights(p_d)
            context["bep_curves"][(kp, "matrix", "posterior")] = weighted_curve(
                b, w, f"initiation_evidence {arm}", static=(crit == "I")
            )
        r, pe = unc.annualise_arm(campaign, context, "matrix", "posterior")
        for kp in KPS:
            context["bep_curves"][(kp, "matrix", "posterior")] = production[
                (kp, "matrix", "posterior")
            ]
        rows[arm], per_event[arm] = r, pe
        print(f"  annualised {arm}", flush=True)
    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")

    # A finer detection-probability curve, as if undrained, point values only
    # (the figure's panel b); every non-drained choice as in the arms above.
    pd_curve: dict[str, Any] = {}
    for p_d in P_D_FINE:
        for kp in KPS:
            b = bundles[("undrained", kp)]
            context["bep_curves"][(kp, "matrix", "posterior")] = weighted_curve(
                b, b.weights(p_d), f"initiation_evidence pd{p_d:g}"
            )
        r, _ = unc.annualise_arm(campaign, context, "matrix", "posterior")
        for kp in KPS:
            context["bep_curves"][(kp, "matrix", "posterior")] = production[
                (kp, "matrix", "posterior")
            ]
            for scenario in campaign.SCENARIOS:
                row = r[("Tokachi", kp, scenario)]
                base = rows["production"][("Tokachi", kp, scenario)]
                pb = (
                    0.0
                    if row["p_annual_bep"] in ("", None)
                    else float(row["p_annual_bep"])
                )
                p0 = float(base["p_annual_bep"])
                pd_curve[f"{p_d:g} {scenario} {_label(kp)}"] = {
                    "p_bep": pb,
                    "relative_to_no_breach": pb / p0 if p0 > 0 else None,
                    "share_bep": (
                        None
                        if row["share_bep"] in ("", None)
                        else float(row["share_bep"])
                    ),
                    "ESS": ess(bundles[("undrained", kp)].weights(p_d)),
                }
        print(f"  p_d curve {p_d:g}", flush=True)
    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")

    # Gate: the rebuilt no-breach arm reproduces production, field for field.
    for key, row in rows["production"].items():
        mine = rows["undrained pd0 T"][key]
        for f, v in row.items():
            if f == "bep_source":
                continue
            if str(mine[f]) != str(v):
                raise SystemExit(f"rebuilt no-breach arm differs at {key} {f}")
    kp_set = {round(k, 3) for k in KPS}
    for arm, rr in rows.items():
        for key, row in rr.items():
            if key[0] == "Tokachi" and round(key[1], 3) in kp_set:
                continue
            strip = {k: v for k, v in row.items() if k != "bep_source"}
            base = rows["production"][key]
            if strip != {k: v for k, v in base.items() if k != "bep_source"}:
                raise SystemExit(f"surface-only segment changed: {key} {arm}")

    def num(v) -> float:
        return 0.0 if v in ("", None) else float(v)

    rng = np.random.default_rng(unc.SEED)
    cells: dict[str, Any] = {}
    for scenario in campaign.SCENARIOS:
        ids = [
            e.event_id for e in context["hazards"][scenario][("Tokachi", 58.8)].events
        ]
        index, n_blocks, _ = unc.block_index(unc.block_labels(ids, "member"))
        strata = unc.stratum_columns(ids)
        mult = unc.draw_multiplicities_stratified(strata, n_blocks, replicates, rng)
        reps: dict[tuple[str, float], dict[str, NDArray]] = {}
        for arm, pe in per_event.items():
            for kp in KPS:
                reps[(arm, kp)] = unc.node_replicates(
                    pe[("Tokachi", kp, scenario)], index, n_blocks, mult, len(ids)
                )
        for arm in per_event:
            for kp in KPS:
                row = rows[arm][("Tokachi", kp, scenario)]
                rp = reps[(arm, kp)]
                base = reps[("production", kp)]
                pb, po = num(row["p_annual_bep"]), num(row["p_annual_overflow"])
                bep_r = rp.get("bep", np.zeros(replicates))
                ovf_r = rp.get("overflow", np.zeros(replicates))
                with np.errstate(divide="ignore", invalid="ignore"):
                    rel = bep_r / base.get("bep", np.zeros(replicates))
                rel = rel[np.isfinite(rel)]
                pb0 = num(rows["production"][("Tokachi", kp, scenario)]["p_annual_bep"])
                cells[f"{arm} {scenario} {_label(kp)}"] = {
                    "p_system": num(row["p_annual_system"]),
                    "p_bep": pb,
                    "p_overflow": po,
                    "share_bep": (
                        None
                        if row["share_bep"] in ("", None)
                        else float(row["share_bep"])
                    ),
                    "leading": (
                        "none"
                        if pb <= 0 and po <= 0
                        else ("piping" if pb > po else "overflow")
                    ),
                    "fraction_replicates_piping_leads": float(np.mean(bep_r > ovf_r)),
                    "system_ci95": [
                        float(x) for x in np.percentile(rp["__system__"], [2.5, 97.5])
                    ],
                    "bep_relative_to_no_breach": (pb / pb0) if pb0 > 0 else None,
                    "bep_relative_ci95": (
                        [float(x) for x in np.percentile(rel, [2.5, 97.5])]
                        if rel.size
                        else None
                    ),
                }
    # Comment 6 under the no-boil observation: same-head over transient.
    criterion: dict[str, Any] = {}
    for scenario in campaign.SCENARIOS:
        for kp in KPS:
            t = cells[f"undrained pd1 T {scenario} {_label(kp)}"]
            i = cells[f"undrained pd1 I {scenario} {_label(kp)}"]
            criterion[f"{scenario} {_label(kp)}"] = {
                "system_I_over_T_strict": (
                    i["p_system"] / t["p_system"] if t["p_system"] > 0 else None
                ),
                "bep_I_over_T_strict": (
                    i["p_bep"] / t["p_bep"] if t["p_bep"] > 0 else None
                ),
            }
    return {
        "gates": {
            "gate_iii": gate,
            "rebuilt_no_breach_arm": "identical to production, field for field",
            "surface_only_segments": "identical across every arm",
            "hazard_cache_unchanged": True,
        },
        "replicates": replicates,
        "seed": unc.SEED,
        "cells": cells,
        "criterion_under_strict_observation": criterion,
        "detection_probability_curve": pd_curve,
    }


# --------------------------------------------------------------------------- #
# Part: dominance                                                              #
# --------------------------------------------------------------------------- #
def dominance_part(results_root: Path) -> dict[str, Any]:
    from system_integration.uemura_models import load_segment_inputs

    unc, campaign = _campaign(results_root)
    cache_before = unc._dir_state(campaign.HAZARD_CACHE, "*.csv")
    context = unc.build_context(campaign)
    rows, per_event = unc.annualise_arm(campaign, context, "matrix", "posterior")
    _, per_event_prior = unc.annualise_arm(campaign, context, "matrix", "prior")
    if unc._dir_state(campaign.HAZARD_CACHE, "*.csv") != cache_before:
        raise SystemExit("the hazard cache changed during the run; refusing")
    seg = load_segment_inputs(
        REPO / "data/processed/uemura_segments/segment_inputs.csv"
    )
    out: dict[str, Any] = {}
    for kp in KPS:
        si = seg[("Tokachi", round(kp, 3))]
        peak = PEAK_2016[kp]
        # The ensemble's stage axis is the node rating, so the like-for-like
        # 2016 peak for a return period is the rating-anchored one (ADR-0035
        # sensitivity replay), not the surveyed trace, which carries the
        # bend superelevation and local effects the rating does not.
        rating_meta = json.loads(
            (
                results_root / "phase2_anchor_rating" / f"{_stem(kp)}_posterior.json"
            ).read_text(encoding="utf-8")
        )
        rating_rec = rating_meta["phase2"]["event_chain"][0]["record"]
        if rating_rec["provenance"].get("anchor") != "rating":
            raise SystemExit(f"{_label(kp)}: rating-anchor replay is not rating")
        rating_peak = float(rating_rec["peak_m_msl"])
        sec: dict[str, Any] = {
            "peak_2016_m": peak,
            "peak_2016_rating_anchored_m": rating_peak,
            "design_level_m": DESIGN_HWL[kp],
            "design_crest_m": si.crest_design_m_msl,
            "modelled_crest_mean_m": si.crest_design_m_msl + si.crest_err_mu_m,
            "modelled_crest_sd_m": si.crest_err_sigma_m,
            "rating_error_mean_sd_m": [si.wl_err_mu_m, si.wl_err_sigma_m],
            "peak_below_design_crest_m": si.crest_design_m_msl - peak,
            "peak_below_modelled_crest_m": si.crest_design_m_msl
            + si.crest_err_mu_m
            - peak,
            "scenarios": {},
        }
        # Conditional probabilities at the 2016 peak (canonical event).
        bep = context["bep_curves"][(kp, "matrix", "posterior")]
        frag, _ = campaign._compose_segment(
            next(
                s
                for s in context["registry"].segments
                if s.river == "Tokachi" and round(s.kp, 3) == round(kp, 3)
            ),
            context["surface"],
            bep,
            1.0,
            "historical",
        )
        interp = (
            unc._curve_interpolators(frag)
            if hasattr(unc, "_curve_interpolators")
            else None
        )
        if interp is None:
            from annualisation_uncertainty_study import _curve_interpolators as ci

            interp = ci(frag)
        for stage_key, stage in (
            ("at_2016_peak", peak),
            ("at_design_level", DESIGN_HWL[kp]),
        ):
            sec[f"conditional_{stage_key}"] = {
                m: float(np.asarray(interp[m](np.array([stage])))[0]) for m in interp
            }
        # Stage at which overflow and piping reach 1e-2 on the composed axis.
        grid = np.linspace(peak - 1.0, si.crest_design_m_msl + 3.0, 2001)
        for m in ("bep", "overflow"):
            if m in interp:
                vals = np.asarray(interp[m](grid))
                hit = np.nonzero(vals >= 1e-2)[0]
                sec[f"stage_{m}_reaches_1e-2_m"] = (
                    float(grid[hit[0]]) if hit.size else None
                )
        for scenario in campaign.SCENARIOS:
            hz = context["hazards"][scenario][("Tokachi", kp)]
            peaks = np.asarray(hz.peak_stages(), dtype=np.float64)
            n = peaks.size
            vals = per_event[("Tokachi", kp, scenario)]
            vals_prior = per_event_prior[("Tokachi", kp, scenario)]
            above16 = peaks > peak
            aboved = peaks > DESIGN_HWL[kp]
            abover = peaks > rating_peak
            entry: dict[str, Any] = {
                "n_years": int(n),
                "years_above_2016_rating_peak": int(abover.sum()),
                "return_period_2016_rating_peak_yr": (
                    float(n / abover.sum()) if abover.any() else None
                ),
                "years_above_2016_peak": int(above16.sum()),
                "annual_exceedance_2016_peak": float(above16.mean()),
                "return_period_2016_peak_yr": (
                    float(n / above16.sum()) if above16.any() else None
                ),
                "years_above_design": int(aboved.sum()),
                "return_period_design_yr": (
                    float(n / aboved.sum()) if aboved.any() else None
                ),
            }
            for m in ("__system__", "bep", "overflow"):
                for label, v in (("posterior", vals), ("prior", vals_prior)):
                    if m not in v:
                        continue
                    x = np.asarray(v[m], dtype=np.float64)
                    tot = float(x.sum())
                    entry[f"{m}_{label}_annual"] = tot / n
                    entry[f"{m}_{label}_share_from_above_2016_peak"] = (
                        float(x[above16].sum() / tot) if tot > 0 else None
                    )
                    entry[f"{m}_{label}_share_from_above_2016_rating_peak"] = (
                        float(x[abover].sum() / tot) if tot > 0 else None
                    )
                    entry[f"{m}_{label}_share_from_above_design"] = (
                        float(x[aboved].sum() / tot) if tot > 0 else None
                    )
                    entry[f"{m}_{label}_weighted_peak_m"] = (
                        float((x * peaks).sum() / tot) if tot > 0 else None
                    )
            sec["scenarios"][scenario] = entry
        out[_label(kp)] = sec
    return out


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
PARTS = (
    "gate",
    "initiation",
    "conditioning",
    "annual",
    "dominance",
    "figures",
    "report",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("part", choices=PARTS)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=REPO / "results",
        help="Production results root (default: this checkout's results/).",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Raw data root (default: <results-root>/../data/raw).",
    )
    parser.add_argument("--replicates", type=int, default=10_000)
    args = parser.parse_args(argv)
    data_root = args.data_root or args.results_root.parent / "data" / "raw"
    tick = time.time()
    if args.part == "gate":
        _write_stage("gate", gate_part(args.results_root))
    elif args.part == "initiation":
        _write_stage("initiation", initiation_part(args.results_root, data_root))
    elif args.part == "conditioning":
        _write_stage("conditioning", conditioning_part(args.results_root))
    elif args.part == "annual":
        _write_stage("annual", annual_part(args.results_root, args.replicates))
    elif args.part == "dominance":
        _write_stage("dominance", dominance_part(args.results_root))
    elif args.part == "figures":
        print(figures_part(args.results_root, data_root))
    elif args.part == "report":
        report_part()
    print(f"{args.part}: {time.time() - tick:.0f} s")
    return 0


# --------------------------------------------------------------------------- #
# Part: figures                                                                #
# --------------------------------------------------------------------------- #
FIG_RECORD = "survival_2016_record_levels.png"
FIG_INITIATION = "initiation_2016_outcomes.png"
#: Expected hours above the toe in the reconstructed record (thesis Table 6.1).
HOURS_2016 = {57.4: 9, 58.8: 21, 60.0: 28, 62.0: 6}


def _fig_record(record: dict, data_root: Path, fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    from bayesian_reliability_updating.events import (
        default_2016_source,
        observed_event_record,
    )
    from bep_reliability_engine.hydrographs import (
        conditioning_record_for_level,
        load_canonical_shape,
    )
    from system_integration.uemura_models import load_segment_inputs

    ini = record["initiation"]
    seg = load_segment_inputs(
        REPO / "data/processed/uemura_segments/segment_inputs.csv"
    )
    src = default_2016_source(data_root.parent / "processed" / "2016_event")
    width = fs.TEXTWIDTH_IN
    height = width * 0.80
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, axes = plt.subplots(2, 2, figsize=(width, height), sharex=True)
    toe_style = dict(color=fs.MUTED, lw=1.0 * scale, ls=(0, (1.2, 1.6)))
    design_style = dict(color=fs.INK_2, lw=1.0 * scale, ls=(0, (5, 2)))
    crest_style = dict(color=fs.INK_2, lw=1.1 * scale, ls="-")
    model_crest_style = dict(
        color=fs.MECHANISM_COLORS["overflow"],
        lw=1.1 * scale,
        ls=(0, (6, 1.5, 1.5, 1.5)),
    )
    canon_style = dict(color=fs.MAGENTA, lw=1.4 * scale, ls=(0, (3, 1.4)))
    for ax, kp in zip(axes.flat, KPS, strict=True):
        r = observed_event_record(src, section_kp=kp, data_root=data_root)
        h = np.asarray(r.h, dtype=np.float64)
        z_toe = float(ini[f"undrained {_label(kp)}"]["z_toe_m"])
        hours = int((h > z_toe).sum())
        if abs(float(r.peak) - PEAK_2016[kp]) > 5e-4 or hours != HOURS_2016[kp]:
            raise SystemExit(f"{_label(kp)}: record differs from Table 6.1")
        start = r.provenance["window_start_jst"]
        hour0 = int(start[11:13])
        days = 1.0 + np.asarray(r.t, dtype=np.float64) / 86400.0 + hour0 / 24.0
        si = seg[("Tokachi", round(kp, 3))]
        crest = si.crest_design_m_msl
        mcrest = si.crest_design_m_msl + si.crest_err_mu_m
        color = fs.SECTION_COLORS[f"KP{kp:.1f}"]
        keep = days >= 15.0
        ax.plot(days[keep], h[keep], color=color, lw=1.5 * scale, zorder=5)
        ax.fill_between(
            days[keep],
            z_toe,
            h[keep],
            where=h[keep] > z_toe,
            color=color,
            alpha=0.22,
            lw=0,
            zorder=2,
        )
        ax.axhline(z_toe, **toe_style, zorder=3)
        ax.axhline(DESIGN_HWL[kp], **design_style, zorder=3)
        ax.axhline(crest, **crest_style, zorder=3)
        ax.axhline(mcrest, **model_crest_style, zorder=3)
        if kp == 58.8:
            canon = load_canonical_shape(
                data_root, river="Tokachi", kp=58.8, event_id=CANONICAL_EVENT
            )
            rc = conditioning_record_for_level(
                canon, PEAK_2016[58.8], scenario="historical"
            )
            hc = np.asarray(rc.h, dtype=np.float64)
            tc = np.asarray(rc.t, dtype=np.float64) / 86400.0
            shift = days[int(np.argmax(h))] - tc[int(np.argmax(hc))]
            ax.fill_between(
                tc + shift,
                z_toe,
                hc,
                where=hc > z_toe,
                color=canon_style["color"],
                alpha=0.13,
                lw=0,
                zorder=1,
            )
            ax.plot(tc + shift, hc, **canon_style, zorder=3)
            hours_c = float((hc > z_toe).sum() * float(rc.native_dt) / 3600.0)
            if abs(hours_c - 60.0) > 1.0:
                raise SystemExit(f"canonical exposure {hours_c} h, not about 60 h")
        lo = float(np.min(h[keep])) - 0.3
        ax.set_ylim(lo, mcrest + 0.45)
        ax.set_xlim(15.0, 34.0)
        ax.set_xticks([15, 19, 23, 27, 31])
        ax.set_xticklabels(["15 Aug", "19 Aug", "23 Aug", "27 Aug", "31 Aug"])
        fs.panel_title(ax, _label(kp), scale=scale)
        margin = record["dominance"][_label(kp)]["peak_below_design_crest_m"]
        if abs((crest - float(r.peak)) - margin) > 1e-6:
            raise SystemExit(f"{_label(kp)}: crest margin differs from the record")
    for ax in axes[:, 0]:
        ax.set_ylabel("stage [m T.P.]")
    handles = [
        Patch(facecolor=fs.MUTED, alpha=0.35, lw=0),
        Line2D([], [], **toe_style),
        Line2D([], [], **design_style),
        Line2D([], [], **crest_style),
        Line2D([], [], **model_crest_style),
        Line2D([], [], **canon_style),
    ]
    labels = [
        "2016 record, above the toe shaded",
        "landside toe",
        "design level",
        "design crest",
        "crest in the overflow model",
        "canonical flood at the KP 58.8 peak",
    ]
    fs.title(fig, "The 2016 record against the design level and the crest", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale, ncol=3)
    fs.layout(fig, scale=scale, legend_rows=2)
    return fs.save(fig, FIG_RECORD, mirror=mirror)


#: Rows of the outcome panel: (configuration, section, row label).
OUTCOME_ROWS: tuple[tuple[str, float, str], ...] = (
    ("undrained", 57.4, "KP 57.4"),
    ("undrained", 58.8, "KP 58.8, as if undrained"),
    ("berm", 58.8, "KP 58.8, measured berm"),
    ("berm_relief_40pct", 58.8, "KP 58.8, berm, 40 % relief"),
    ("berm_relief_60pct", 58.8, "KP 58.8, berm, 60 % relief"),
    ("undrained", 60.0, "KP 60.0, as if undrained"),
    ("berm", 60.0, "KP 60.0, measured berm"),
    ("berm_relief_40pct", 60.0, "KP 60.0, berm, 40 % relief"),
    ("berm_relief_60pct", 60.0, "KP 60.0, berm, 60 % relief"),
    ("undrained", 62.0, "KP 62.0"),
)
#: Detection probabilities drawn in panel b, at even spacing.
PD_SHOWN: tuple[float, ...] = (0.0, 0.5, 0.9, 0.95, 0.99, 0.998, 1.0)


def _fig_initiation(record: dict, fs, mirror: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    ini = record["initiation"]
    ann = record["annual"]["detection_probability_curve"]
    width = fs.TEXTWIDTH_IN
    height = width * 0.62
    scale = fs.scale_for(width)
    fs.style(scale)
    fig, (ax, bx) = plt.subplots(
        1, 2, figsize=(width, height), gridspec_kw={"width_ratios": (1.25, 1.0)}
    )
    parts = (
        ("no_exit", fs.GRID, "no exit opened"),
        ("exit_held_by_resistance", fs.SEQ_BLUE[2], "exit opened, pipe stalled"),
        (
            "exit_held_only_by_duration",
            fs.VIOLET,
            "stalled only because the flood fell",
        ),
        ("breach", fs.TRANSIENT, "breach"),
    )
    y = np.arange(len(OUTCOME_ROWS))[::-1]
    for yi, (config, kp, _) in zip(y, OUTCOME_ROWS, strict=True):
        dec = ini[f"{config} {_label(kp)}"]["decomposition"]
        left = 0.0
        for key, color, _ in parts:
            ax.barh(yi, dec[key], left=left, color=color, height=0.72, lw=0)
            left += dec[key]
    ax.set_yticks(y)
    ax.set_yticklabels([r[2] for r in OUTCOME_ROWS])
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of the prior foundations")
    fs.panel_title(ax, "The model's 2016 outcome", scale=scale, letter="a")
    xs = np.arange(len(PD_SHOWN))
    for kp in KPS:
        rel = [
            ann[f"{p:g} historical {_label(kp)}"]["relative_to_no_breach"]
            for p in PD_SHOWN
        ]
        color = fs.SECTION_COLORS[f"KP{kp:.1f}"]
        bx.plot(
            xs,
            rel,
            color=color,
            lw=1.5 * scale,
            marker=fs.SECTION_MARKERS[f"KP{kp:.1f}"],
            ms=4 * scale,
            zorder=3,
        )
        if kp in (58.8, 60.0):
            bx.plot(
                xs[-1],
                rel[-1],
                marker=fs.SECTION_MARKERS[f"KP{kp:.1f}"],
                ms=6 * scale,
                mfc=fs.SURFACE,
                mec=color,
                mew=1.3 * scale,
                zorder=4,
                ls="none",
            )
    bx.plot(
        xs[:-1],
        [1 - p for p in PD_SHOWN[:-1]],
        color=fs.MUTED,
        lw=1.0 * scale,
        ls=(0, (4, 2)),
        zorder=2,
    )
    bx.set_xticks(xs)
    bx.set_xticklabels([f"{p:g}" for p in PD_SHOWN])
    bx.set_ylim(0, 1.05)
    bx.set_xlabel("chance that an opened exit was seen and recorded")
    bx.set_ylabel("annual piping probability,\nrelative to the adopted update")
    fs.panel_title(bx, "What the no-boil record could change", scale=scale, letter="b")
    handles = [Patch(facecolor=c, lw=0) for _, c, _ in parts]
    labels = [lab for _, _, lab in parts]
    handles += [
        Line2D(
            [],
            [],
            color=fs.SECTION_COLORS[f"KP{kp:.1f}"],
            lw=1.5 * scale,
            marker=fs.SECTION_MARKERS[f"KP{kp:.1f}"],
            ms=4 * scale,
        )
        for kp in KPS
    ]
    labels += [f"KP {kp:.1f}" for kp in KPS]
    handles.append(Line2D([], [], color=fs.MUTED, lw=1.0 * scale, ls=(0, (4, 2))))
    labels.append("largest possible change")
    fs.title(fig, "Exits in 2016 and the weight of an unrecorded boil", scale=scale)
    fs.legend_below(fig, handles, labels, scale=scale, ncol=5)
    fs.layout(fig, scale=scale, legend_rows=2)
    return fs.save(fig, FIG_INITIATION, mirror=mirror)


def figures_part(results_root: Path, data_root: Path) -> list[str]:  # noqa: ARG001
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as fs

    mirror = OUT_DIR / "figures"
    record = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    rec = _fig_record(record, data_root, fs, mirror)
    ini = _fig_initiation(record, fs, mirror)
    return [str(p.relative_to(REPO)).replace("\\", "/") for p in (rec, ini)]


# --------------------------------------------------------------------------- #
# Part: report                                                                 #
# --------------------------------------------------------------------------- #
def _round(obj: Any, sig: int = 6) -> Any:
    if isinstance(obj, float):
        return float(f"{obj:.{sig}g}") if np.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _round(v, sig) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, sig) for v in obj]
    return obj


def _slim_conditioning(cond: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, entry in cond.items():
        arms = {}
        for p, a in entry["arms"].items():
            keep = {k: v for k, v in a.items() if k != "levels"}
            if p in ("0", "1"):
                keep["levels"] = a["levels"]
            arms[p] = keep
        out[key] = {k: v for k, v in entry.items() if k != "arms"} | {"arms": arms}
    return out


def _summary(ini, cond, ann, dom) -> dict[str, Any]:
    s: dict[str, Any] = {}
    s["P_initiation_2016_as_if_undrained"] = {
        _label(kp): ini[f"undrained {_label(kp)}"]["P_initiation_prior"] for kp in KPS
    }
    s["P_initiation_2016_berm"] = {
        _label(kp): ini[f"berm {_label(kp)}"]["P_initiation_prior"]
        for kp in (58.8, 60.0)
    }
    s["P_initiation_2016_berm_relief"] = {
        f"{c} {_label(kp)}": ini[f"{c} {_label(kp)}"]["P_initiation_prior"]
        for c in (
            "berm_relief_20pct",
            "berm_relief_40pct",
            "berm_relief_60pct",
            "berm_relief_80pct",
        )
        for kp in (58.8, 60.0)
    }
    s["P_initiation_2016_pressure_factor_as_if_undrained"] = {
        _label(kp): ini[f"undrained {_label(kp)}"]["pressure_factor_sweep"]
        for kp in KPS
    }
    s["outcome_decomposition_as_if_undrained"] = {
        _label(kp): ini[f"undrained {_label(kp)}"]["decomposition"] for kp in KPS
    }
    s["hours_gate_open_median"] = {
        _label(kp): ini[f"undrained {_label(kp)}"][
            "hours_gate_open_initiated_quartiles"
        ][1]
        for kp in KPS
    }
    s["strict_no_initiation_retained"] = {
        _label(kp): ini[f"undrained {_label(kp)}"]["n_no_initiation"] for kp in KPS
    }
    s["annual_bep_relative_to_no_breach_historical"] = {
        arm: {
            _label(kp): ann["cells"][f"{arm} historical {_label(kp)}"][
                "bep_relative_to_no_breach"
            ]
            for kp in KPS
        }
        for arm in (
            "undrained pd0.5 T",
            "undrained pd0.9 T",
            "undrained pd1 T",
            "berm pd1 T",
            "berm_relief_60pct pd1 T",
        )
    }
    s["leading_mechanism"] = {
        arm: {
            f"{sc} {_label(kp)}": ann["cells"][f"{arm} {sc} {_label(kp)}"]["leading"]
            for sc in ("historical", "+4K")
            for kp in KPS
        }
        for arm in ("production", "undrained pd1 T", "undrained pd0.5 T", "berm pd1 T")
    }
    s["share_bep"] = {
        arm: {
            f"{sc} {_label(kp)}": ann["cells"][f"{arm} {sc} {_label(kp)}"]["share_bep"]
            for sc in ("historical", "+4K")
            for kp in KPS
        }
        for arm in ("production", "undrained pd1 T", "undrained pd0.5 T", "berm pd1 T")
    }
    s["return_period_2016_rating_axis_yr"] = {
        sc: dom["KP 58.8"]["scenarios"][sc]["return_period_2016_rating_peak_yr"]
        for sc in ("historical", "+4K")
    }
    s["return_period_2016_trace_peak_yr"] = {
        _label(kp): {
            sc: dom[_label(kp)]["scenarios"][sc]["return_period_2016_peak_yr"]
            for sc in ("historical", "+4K")
        }
        for kp in KPS
    }
    s["share_annual_bep_from_years_above_2016"] = {
        _label(kp): {
            "rating_axis": dom[_label(kp)]["scenarios"]["historical"][
                "bep_posterior_share_from_above_2016_rating_peak"
            ],
            "trace_axis": dom[_label(kp)]["scenarios"]["historical"][
                "bep_posterior_share_from_above_2016_peak"
            ],
            "above_design": dom[_label(kp)]["scenarios"]["historical"][
                "bep_posterior_share_from_above_design"
            ],
        }
        for kp in KPS
    }
    s["crest_margins_m"] = {
        _label(kp): {
            "below_design_crest": dom[_label(kp)]["peak_below_design_crest_m"],
            "below_modelled_crest": dom[_label(kp)]["peak_below_modelled_crest_m"],
        }
        for kp in KPS
    }
    s["conditional_at_2016_peak_canonical"] = {
        _label(kp): dom[_label(kp)]["conditional_at_2016_peak"] for kp in KPS
    }
    return s


def _verdicts(ini, cond, ann, dom) -> dict[str, Any]:
    h1 = {
        k: v["H1_stages_where_strict_exceeds_no_breach"]
        for k, v in cond.items()
        if k.startswith("undrained")
    }
    rel = {
        kp: ann["cells"][f"undrained pd1 T historical {_label(kp)}"][
            "bep_relative_to_no_breach"
        ]
        for kp in (57.4, 62.0)
    }
    lead_before = {
        k: v["leading"] for k, v in ann["cells"].items() if k.startswith("production")
    }
    lost = []
    for arm in ("undrained pd1 T", "undrained pd0.5 T"):
        for k, v in lead_before.items():
            key = k.replace("production", arm)
            if v == "piping" and ann["cells"][key]["leading"] != "piping":
                lost.append(key)
    shares = [
        dom[_label(kp)]["scenarios"]["historical"][
            "bep_posterior_share_from_above_2016_peak"
        ]
        for kp in KPS
    ]
    rp = [
        dom[_label(kp)]["scenarios"]["historical"]["return_period_2016_peak_yr"]
        for kp in KPS
    ]
    h6 = {
        kp: 1 - ini[f"berm_relief_60pct {_label(kp)}"]["P_initiation_prior"]
        for kp in (58.8, 60.0)
    }
    return {
        "H1": {"held": all(not v for v in h1.values()), "rises": h1},
        "H2": {"held": all(0.3 <= r <= 0.9 for r in rel.values()), "values": rel},
        "H3": {"held": all(v["H3_bound_violations"] == 0 for v in cond.values())},
        "H4": {
            "held": all("KP 62.0" in x for x in lost),
            "cells_where_piping_lost_the_lead": lost,
        },
        "H5": {
            "share_part_held": min(shares) >= 0.8,
            "return_period_part_held": all(10 <= x <= 100 for x in rp),
            "shares_trace_axis": shares,
            "return_periods_trace_axis_yr": rp,
            "note": "on the ensemble's own rating axis the 2016 flood is a 75-year "
            "event at all four nodes; the pre-registered statement was read on the "
            "trace-anchored peaks, where it fails at KP 57.4 and KP 60.0",
        },
        "H6": {"held": all(v >= 0.5 for v in h6.values()), "P_no_initiation": h6},
    }


def report_part() -> None:
    ini = _read_stage("initiation")
    cond = _read_stage("conditioning")
    ann = _read_stage("annual")
    dom = _read_stage("dominance")
    gate = _read_stage("gate")
    payload = {
        "study": "initiation-evidence-2016-study",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "note": "docs/decisions/initiation-evidence-2016-study.md",
        "generated_by": "scripts/initiation_evidence_2016_study.py",
        "comparator": "ADR-0055 same head and same gate",
        "definitions": {
            "initiation_2016": "uplift-and-heave gate open at some time in the "
            "replayed 2016 record; closed form r_e kept (h_peak - z_toe) > "
            "(gamma_bl_sub / gamma_w) D_bl",
            "p_d": "probability that an exit opened in 2016 would have produced a "
            "boil that was seen and recorded; weight 0 for a breach, 1 - p_d for "
            "an initiated survivor, 1 otherwise",
            "kept": "ADR-0050 factor: share of the exit gradient the drain leaves",
            "pressure_factor": "instantaneous toe overpressure divided by this factor",
            "decomposition": "no_exit: gate never opened; exit_held_by_resistance: "
            "opened, erosion head at the peak not above H_c; "
            "exit_held_only_by_duration: fails the same-head steady-state rule, "
            "survives the transient one; breach: transient failure",
        },
        "summary": _summary(ini, cond, ann, dom),
        "verdicts": _verdicts(ini, cond, ann, dom),
        "gates": {"replay": gate, "annual": ann["gates"]},
        "initiation": ini,
        "conditioning": _slim_conditioning(cond),
        "annual": ann,
        "dominance": dom,
        "figures": [f"docs/figures/{FIG_RECORD}", f"docs/figures/{FIG_INITIATION}"],
    }
    EVIDENCE.write_text(json.dumps(_round(payload), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {EVIDENCE.relative_to(REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
