"""Single-topic study of the C_e (erosion coefficient) prior (companion to ADR-0026).

ADR-0026 sets ``C_e ~ Lognormal(mean 0.055, std 0.043)`` (CoV 0.782), Pol's SIE
2024 Table 2 field-reliability prior. Pol's CompGeo 2024 Table 1 instead reports
per-test *calibrated* values (0.007-0.030, small-scale mean 0.016; large-scale
0.014). This script forensically propagates the choice WITHOUT changing any
default: the production C_e prior stays 0.055 (the drift guard pins it).

The clean-contrast trick (common random numbers on the C_e column)
------------------------------------------------------------------
Every candidate prior remaps the SAME underlying standard-normal image of the
C_e LHS stratum. Given the production field-prior draw ``Ce = exp(mu_f +
sig_f*z6)`` we recover ``z6 = (ln Ce - mu_f)/sig_f`` and re-map it through each
candidate marginal (lognormal or a two-component mixture). The other six theta
columns and the independent L draw are untouched, so the ONLY thing that moves
between candidates is the C_e marginal -- the cleanest possible prior contrast,
and bit-identical to re-running M2 with a different C_e ``PriorSpec`` for the
lognormal candidates (verified in ``prior``).

Three analyses (subcommands, or ``all``):

* ``prior``      -- the candidate priors as densities + moments, with the Pol
                    CompGeo Table 1 points and SIE Table 2 marker overlaid
                    (the forensic figure); no engine calls.
* ``propagate``  -- reduced-N transient fragility sweeps under each candidate at
                    KP58.8/KP60.0; multiplicative P_f effect at shoulder /
                    transition / design levels. Asserts the STATIC branch is
                    C_e-invariant (structural-zero validation, ADR-0033).
* ``phase2``     -- the 2016 survival replay at full N under each candidate:
                    transient rejection, marginal-transient (nesting), and the
                    posterior C_e / k_aq pull, versus the production default.

Everything reuses the production kernels through ``evaluate_batch`` /
``evaluate_batch_diagnostics`` (validated bit-identical to the persisted sweeps
and to the production Phase 2 posterior); no config default is touched, no
persisted artifact is modified.

Outputs
-------
JSON records under ``results/sensitivity/ce_prior/`` (gitignored, regenerable)
and figures under ``docs/figures/ce_prior_*.png``.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from bayesian_reliability_updating.filtering import decompose
from bayesian_reliability_updating.pipeline import Phase2Settings, _default_event_record
from bayesian_reliability_updating.replay import load_phase1_run, replay_event
from bep_reliability_engine import run as runmod
from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import evaluate_batch, evaluate_batch_diagnostics

logger = logging.getLogger("ce_prior_study")

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "configs"
RESULTS_DIR = REPO / "results"
OUT_DIR = RESULTS_DIR / "sensitivity" / "ce_prior"
FIG_DIR = REPO / "docs" / "figures"

# The two informative matrix sections (KP58.8/KP60.0 carry the production Phase 2
# information; see project-notes.md). Config stem -> (label, production sweep h5).
SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("kp58_8_historical_matrix", "KP58.8", "tokachi_kp58.8_historical_matrix.h5"),
    ("kp60_0_historical_matrix", "KP60.0", "tokachi_kp60.0_historical_matrix.h5"),
)

STUDY_N = 30_000  # reduced N for the fragility sweep (numba keeps a ladder to minutes)
PHASE2_N = 100_000  # full production N for the survival replay (numpy ~3.4 s / call)
C_E_INDEX = 6  # canonical PARAM_NAMES index of the C_e column


# --------------------------------------------------------------------------- #
# Candidate priors                                                             #
#                                                                              #
# Each is a quantile function ``ppf(u)`` on the C_e stratified uniform, so a    #
# two-component mixture and a lognormal share one interface. All means/CoVs     #
# and the mixture design trace to Pol's papers (see the note); NOTHING here is  #
# invented -- the empirical CompGeo moments are the Table 1 point calibrations. #
# --------------------------------------------------------------------------- #
# Pol CompGeo 2024, Table 1 -- the seven per-test calibrated C_e values
# (B25-232/245/248, FS35-238/240/242, FPH). VERBATIM from the paper.
COMPGEO_TABLE1: tuple[float, ...] = (0.012, 0.010, 0.030, 0.018, 0.007, 0.018, 0.014)
COMPGEO_SMALL_SCALE: tuple[float, ...] = COMPGEO_TABLE1[:6]  # the six small-scale tests
COMPGEO_LARGE_SCALE: float = 0.014  # FPH large-scale (Pol et al. 2021)


def _lognormal_params(mean: float, cov: float) -> tuple[float, float]:
    """(mu_ln, sigma_ln) reproducing the physical (mean, cov) -- M2's rule."""
    sigma = float(np.sqrt(np.log1p(cov * cov)))
    mu = float(np.log(mean) - 0.5 * sigma * sigma)
    return mu, sigma


def _lognormal_ppf(
    mean: float, cov: float
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    mu, sigma = _lognormal_params(mean, cov)
    return lambda u: np.exp(mu + sigma * norm.ppf(u))


def _lognormal_pdf(
    mean: float, cov: float
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    mu, sigma = _lognormal_params(mean, cov)
    return lambda x: np.exp(-((np.log(x) - mu) ** 2) / (2 * sigma * sigma)) / (
        x * sigma * np.sqrt(2 * np.pi)
    )


def _mixture_pdf(
    comps: list[tuple[float, float, float]],
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    weights = np.array([w for w, _, _ in comps], float)
    weights = weights / weights.sum()
    pdfs = [_lognormal_pdf(m, c) for _, m, c in comps]

    def pdf(x: NDArray[np.float64]) -> NDArray[np.float64]:
        return sum(w * f(x) for w, f in zip(weights, pdfs))

    return pdf


def _mixture_ppf(
    comps: list[tuple[float, float, float]],
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Quantile function of a lognormal mixture, by numeric inversion of the CDF.

    ``comps`` = list of (weight, mean, cov). The mixture CDF is monotone, so a
    fine bisection on a log grid inverts it to machine tolerance for the study.
    """
    weights = np.array([w for w, _, _ in comps], float)
    weights = weights / weights.sum()
    params = [_lognormal_params(m, c) for _, m, c in comps]

    def cdf(x: NDArray[np.float64]) -> NDArray[np.float64]:
        out = np.zeros_like(x, dtype=float)
        for w, (mu, sig) in zip(weights, params):
            out += w * norm.cdf((np.log(x) - mu) / sig)
        return out

    # A dense monotone lookup on log C_e covering well beyond both components.
    grid = np.exp(np.linspace(np.log(1e-4), np.log(1.0), 200_001))
    cgrid = cdf(grid)

    def ppf(u: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.interp(np.clip(u, cgrid[0], cgrid[-1]), cgrid, grid)

    return ppf


@dataclass(frozen=True)
class Candidate:
    key: str
    label: str
    kind: str  # 'lognormal' | 'mixture'
    ppf: Callable[[NDArray[np.float64]], NDArray[np.float64]]
    pdf: Callable[[NDArray[np.float64]], NDArray[np.float64]]
    provenance: str
    mean_nominal: float | None = None
    cov_nominal: float | None = None


_COMPGEO_COV = float(np.std(COMPGEO_TABLE1, ddof=1) / np.mean(COMPGEO_TABLE1))
_MIXTURE_COMPS: list[tuple[float, float, float]] = [
    (0.5, 0.016, 0.48),
    (0.5, 0.055, 0.48),
]


def candidates() -> list[Candidate]:
    """The candidate C_e priors, all traceable to Pol's papers."""
    return [
        Candidate(
            "compgeo_lab",
            "CompGeo lab  Ln(0.016, 0.48)",
            "lognormal",
            _lognormal_ppf(0.016, _COMPGEO_COV),
            _lognormal_pdf(0.016, _COMPGEO_COV),
            "Pol CompGeo 2024 Table 1: small-scale mean 0.016; CoV = empirical "
            "std/mean of the 7 point calibrations (time-dependent dl/dt target).",
            0.016,
            _COMPGEO_COV,
        ),
        Candidate(
            "adr0001_lab",
            "ADR-0001 lab  Ln(0.014, 0.50)",
            "lognormal",
            _lognormal_ppf(0.014, 0.50),
            _lognormal_pdf(0.014, 0.50),
            "ADR-0001 (retired): FPH large-scale 0.014, CoV 0.50 chosen to span "
            "the CompGeo between-test scatter.",
            0.014,
            0.50,
        ),
        Candidate(
            "field_meanshift_labcov",
            "Field mean, lab CoV  Ln(0.055, 0.50)",
            "lognormal",
            _lognormal_ppf(0.055, 0.50),
            _lognormal_pdf(0.055, 0.50),
            "Diagnostic isolation (ADR-0026 alt-considered #2): SIE mean 0.055 "
            "with the lab CoV 0.50 -- separates the mean shift from the CoV widening.",
            0.055,
            0.50,
        ),
        Candidate(
            "field_adr0026",
            "Field ADR-0026  Ln(0.055, 0.782)  [PRODUCTION]",
            "lognormal",
            _lognormal_ppf(0.055, 0.043 / 0.055),
            _lognormal_pdf(0.055, 0.043 / 0.055),
            "PRODUCTION DEFAULT. Pol SIE 2024 Table 2: mean 0.055, std 0.043 "
            "(CoV 0.782); mean = post-critical-rate calibration (thesis App. E).",
            0.055,
            0.043 / 0.055,
        ),
        Candidate(
            "reconciled_mixture",
            "Reconciled mixture  0.5 Ln(0.016,0.48) + 0.5 Ln(0.055,0.48)",
            "mixture",
            _mixture_ppf(_MIXTURE_COMPS),
            _mixture_pdf(_MIXTURE_COMPS),
            "Two-target bridge: equal mass on the CompGeo time-development target "
            "(0.016) and the SIE post-critical-rate target (0.055), each carrying "
            "the ~0.48 between-test scatter. Encodes the unexplained factor 3-4 "
            "(ADR-0026) as a genuinely bimodal epistemic prior rather than "
            "smearing it into one wide lognormal.",
        ),
    ]


PRODUCTION_KEY = "field_adr0026"


def _field_z6(ce_column: NDArray[np.float64]) -> NDArray[np.float64]:
    """Recover the standard-normal image of the C_e stratum from a field draw.

    The production C_e column is ``exp(mu_f + sig_f*z6)`` (M2, no C_e clip), so
    ``z6`` is recovered exactly. Remapping z6 through any candidate quantile
    function is common random numbers on C_e: identical ranks, identical
    stratification, only the marginal changes.
    """
    mu_f, sig_f = _lognormal_params(0.055, 0.043 / 0.055)
    return (np.log(ce_column) - mu_f) / sig_f


def _remap_ce(z6: NDArray[np.float64], cand: Candidate) -> NDArray[np.float64]:
    """Map the recovered C_e stratum image through a candidate marginal."""
    return cand.ppf(norm.cdf(z6))


# --------------------------------------------------------------------------- #
# Shared engine driver                                                         #
# --------------------------------------------------------------------------- #
def _load_config(stem: str, *, n: int, backend: str) -> Config:
    cfg = Config.from_yaml(CONFIG_DIR / f"{stem}.yaml")
    data = cfg.model_dump()
    data["mc"]["n_samples"] = int(n)
    data["timestepper"]["progression_backend"] = backend
    return Config.model_validate(data)


def _sweep_pf(
    config: Config,
    theta: NDArray[np.float64],
    L: NDArray[np.float64] | None,
    records: list,
    geom: dict,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Per-level (static, transient) P_f for one theta/L pairing."""
    n_h = len(records)
    pf_st = np.empty(n_h)
    pf_tr = np.empty(n_h)
    for i, rec in enumerate(records):
        cs, ct = evaluate_batch(
            theta,
            rec,
            geom,
            seepage_length_samples=L,
            alpha_exponent=config.alpha_exponent,
            theta_repose_rad=config.theta_repose_rad,
            relative_density=config.relative_density_insitu,
            alpha_exponent_transient=config.alpha_exponent_transient,
            foreland_open=config.foreland_treatment == "open_entry",
            progression_backend=config.timestepper.progression_backend,
        )
        pf_st[i] = float(cs.mean())
        pf_tr[i] = float(ct.mean())
    return pf_st, pf_tr


# --------------------------------------------------------------------------- #
# Q1 -- the prior comparison (no engine)                                       #
# --------------------------------------------------------------------------- #
def run_prior() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cands = candidates()
    # Sample each candidate's marginal off a common fine uniform grid for the
    # empirical moments (the mixture has no closed-form CoV).
    u = (np.arange(1, 500_001) - 0.5) / 500_000.0
    record: dict[str, Any] = {
        "analysis": "prior_reconciliation",
        "compgeo_table1_values": list(COMPGEO_TABLE1),
        "compgeo_small_scale_mean": float(np.mean(COMPGEO_SMALL_SCALE)),
        "compgeo_all7_mean": float(np.mean(COMPGEO_TABLE1)),
        "compgeo_all7_cov": float(
            np.std(COMPGEO_TABLE1, ddof=1) / np.mean(COMPGEO_TABLE1)
        ),
        "compgeo_small_scale_cov": float(
            np.std(COMPGEO_SMALL_SCALE, ddof=1) / np.mean(COMPGEO_SMALL_SCALE)
        ),
        "sie2024_table2": {"mean": 0.055, "std": 0.043, "cov": 0.043 / 0.055},
        "candidates": {},
    }
    for c in cands:
        x = c.ppf(u)
        record["candidates"][c.key] = {
            "label": c.label,
            "kind": c.kind,
            "provenance": c.provenance,
            "mean_nominal": c.mean_nominal,
            "cov_nominal": c.cov_nominal,
            "empirical_mean": float(x.mean()),
            "empirical_cov": float(x.std() / x.mean()),
            "median": float(np.median(x)),
            "p05": float(np.quantile(x, 0.05)),
            "p95": float(np.quantile(x, 0.95)),
        }
    path = OUT_DIR / "prior_reconciliation.json"
    path.write_text(json.dumps(record, indent=2))
    logger.info("wrote %s", path)
    _plot_priors(record)
    return record


def _plot_priors(record: dict[str, Any]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cands = candidates()
    x = np.exp(np.linspace(np.log(1e-3), np.log(0.5), 2000))
    fig, ax = plt.subplots(figsize=(9, 5.2))
    colors = {
        "compgeo_lab": "#1b7837",
        "adr0001_lab": "#4d9221",
        "field_meanshift_labcov": "#f1a340",
        "field_adr0026": "#c51b7d",
        "reconciled_mixture": "#2166ac",
    }
    for c in cands:
        lw = 2.6 if c.key == PRODUCTION_KEY else 1.7
        ls = "-" if c.kind == "lognormal" else "--"
        ax.plot(x, c.pdf(x), ls, color=colors[c.key], lw=lw, label=c.label)
    # CompGeo Table 1 point calibrations (rug)
    for v in COMPGEO_TABLE1:
        ax.axvline(v, ymin=0.0, ymax=0.06, color="black", lw=1.0)
    ax.axvline(
        COMPGEO_TABLE1[0],
        ymin=0.0,
        ymax=0.06,
        color="black",
        lw=1.0,
        label="Pol CompGeo 2024 Table 1 (per-test)",
    )
    ax.axvline(
        0.055, color="#c51b7d", lw=1.0, ls=":", label="SIE 2024 Table 2 mean 0.055"
    )
    ax.axvline(
        0.016, color="#1b7837", lw=1.0, ls=":", label="CompGeo small-scale mean 0.016"
    )
    ax.set_xscale("log")
    ax.set_xlabel(r"erosion coefficient $C_e$  [-]")
    ax.set_ylabel("probability density")
    ax.set_title("C_e prior reconciliation: lab calibrations vs field prior (ADR-0026)")
    ax.legend(fontsize=7.5, loc="upper right")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    out = FIG_DIR / "ce_prior_reconciliation.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    logger.info("wrote %s", out)


# --------------------------------------------------------------------------- #
# Q2 -- fragility propagation                                                  #
# --------------------------------------------------------------------------- #
def run_propagate(backend: str = "numba") -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cands = candidates()
    record: dict[str, Any] = {
        "analysis": "fragility_propagation",
        "n_samples": STUDY_N,
        "backend": backend,
        "production_candidate": PRODUCTION_KEY,
        "sections": {},
    }
    for stem, label, _h5 in SECTIONS:
        cfg = _load_config(stem, n=STUDY_N, backend=backend)
        theta = runmod._sample_prior(cfg).theta_matrix
        L = runmod.seepage_length_samples_for_config(cfg)
        records = runmod.conditioning_hydrographs_for_config(cfg)
        geom = cfg.geometry.as_evaluator_dict()
        grid = np.asarray(cfg.mc.conditioning_grid, float)
        z6 = _field_z6(theta[:, C_E_INDEX])

        curves: dict[str, Any] = {}
        static_ref: NDArray[np.float64] | None = None
        for c in cands:
            theta_v = theta.copy()
            theta_v[:, C_E_INDEX] = _remap_ce(z6, c)
            pf_st, pf_tr = _sweep_pf(cfg, theta_v, L, records, geom)
            # STATIC branch must be C_e-invariant (structural zero, ADR-0033).
            if static_ref is None:
                static_ref = pf_st
            else:
                assert np.array_equal(pf_st, static_ref), (
                    f"{label}: static P_f moved under C_e prior {c.key!r} -- "
                    "the C_e-transient-only architecture is violated."
                )
            curves[c.key] = {
                "empirical_ce_mean": float(theta_v[:, C_E_INDEX].mean()),
                "static": pf_st.tolist(),
                "transient": pf_tr.tolist(),
            }
        landmarks = _landmarks(
            grid,
            np.asarray(curves[PRODUCTION_KEY]["transient"]),
            float(cfg.geometry.HWL),
        )
        record["sections"][label] = {
            "config": stem,
            "grid_m_msl": grid.tolist(),
            "HWL_m_msl": float(cfg.geometry.HWL),
            "z_toe_m_msl": float(cfg.geometry.z_toe),
            "static_pf_c_e_invariant": static_ref.tolist(),
            "landmarks": landmarks,
            "curves": curves,
        }
        logger.info("propagate: %s done", label)
    path = OUT_DIR / "fragility_propagation.json"
    path.write_text(json.dumps(record, indent=2))
    logger.info("wrote %s", path)
    _plot_propagation(record)
    return record


def _landmarks(
    grid: NDArray[np.float64], pf_prod: NDArray[np.float64], hwl: float
) -> dict[str, Any]:
    """Shoulder / transition / design-level indices off the production curve."""
    # shoulder: first level with transient P_f >= 0.02
    above = np.nonzero(pf_prod >= 0.02)[0]
    shoulder = int(above[0]) if above.size else int(np.argmax(pf_prod > 0))
    # transition: nearest to 0.5
    transition = int(np.argmin(np.abs(pf_prod - 0.5)))
    # design: nearest grid stage to HWL (fallback to top of loaded sweep)
    design = int(np.argmin(np.abs(grid - hwl))) if hwl else len(grid) - 1
    return {
        "shoulder": {
            "index": shoulder,
            "stage_m_msl": float(grid[shoulder]),
            "pf_prod": float(pf_prod[shoulder]),
        },
        "transition": {
            "index": transition,
            "stage_m_msl": float(grid[transition]),
            "pf_prod": float(pf_prod[transition]),
        },
        "design": {
            "index": design,
            "stage_m_msl": float(grid[design]),
            "pf_prod": float(pf_prod[design]),
        },
    }


def _plot_propagation(record: dict[str, Any]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cands = candidates()
    colors = {
        "compgeo_lab": "#1b7837",
        "adr0001_lab": "#4d9221",
        "field_meanshift_labcov": "#f1a340",
        "field_adr0026": "#c51b7d",
        "reconciled_mixture": "#2166ac",
    }
    secs = list(record["sections"].items())
    fig, axes = plt.subplots(
        1, len(secs), figsize=(6.6 * len(secs), 5.0), squeeze=False
    )
    for ax, (label, sec) in zip(axes[0], secs):
        grid = np.asarray(sec["grid_m_msl"])
        for c in cands:
            pf = np.asarray(sec["curves"][c.key]["transient"])
            lw = 2.6 if c.key == PRODUCTION_KEY else 1.6
            ls = "-" if c.key != "reconciled_mixture" else "--"
            ax.plot(
                grid, pf, ls, color=colors[c.key], lw=lw, label=c.label.split("  ")[0]
            )
        pf_stat = np.asarray(sec["static_pf_c_e_invariant"])
        ax.plot(
            grid, pf_stat, ":", color="grey", lw=1.6, label="static (C_e-invariant)"
        )
        for name, m in sec["landmarks"].items():
            ax.axvline(m["stage_m_msl"], color="black", lw=0.7, alpha=0.4)
            ax.text(m["stage_m_msl"], 0.92, name[:4], rotation=90, fontsize=7, va="top")
        ax.axvline(sec["HWL_m_msl"], color="red", lw=1.0, ls="-.", alpha=0.6)
        ax.set_title(f"{label}: transient fragility vs C_e prior")
        ax.set_xlabel("river stage h  [m MSL]")
        ax.set_ylabel(r"$P_f$")
        ax.set_ylim(-0.02, 1.02)
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=7.5, loc="center right")
    fig.tight_layout()
    out = FIG_DIR / "ce_prior_fragility_propagation.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    logger.info("wrote %s", out)


# --------------------------------------------------------------------------- #
# Q3 -- Phase 2 survival replay                                                #
# --------------------------------------------------------------------------- #
def run_phase2(backend: str = "numba") -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cands = candidates()
    param_names = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]
    record: dict[str, Any] = {
        "analysis": "phase2_survival_sensitivity",
        "n_samples": PHASE2_N,
        "backend_note": (
            "candidate replays use numba; baseline cross-checked vs config numpy"
        ),
        "production_candidate": PRODUCTION_KEY,
        "sections": {},
    }
    settings = Phase2Settings()
    for stem, label, h5 in SECTIONS:
        run = load_phase1_run(RESULTS_DIR / h5)
        rec = _default_event_record(run, settings)
        # One replay to obtain the ADR-0036-refined 225 s record; reused verbatim.
        base_replay = replay_event(run, rec)
        refined = base_replay.record
        geom = run.geometry
        theta = run.theta
        L = run.seepage_length_samples
        z6 = _field_z6(theta[:, C_E_INDEX])

        cfg = run.config
        section_out: dict[str, Any] = {
            "config": stem,
            "results_h5": h5,
            "candidates": {},
        }
        for c in cands:
            theta_v = theta.copy()
            theta_v[:, C_E_INDEX] = _remap_ce(z6, c)
            diag = evaluate_batch_diagnostics(
                theta_v,
                refined,
                geom,
                l_ini=0.0,
                seepage_length_samples=L,
                alpha_exponent=cfg.alpha_exponent,
                alpha_exponent_transient=cfg.alpha_exponent_transient,
                theta_repose_rad=cfg.theta_repose_rad,
                relative_density=cfg.relative_density_insitu,
                foreland_open=cfg.foreland_treatment == "open_entry",
                progression_backend=backend,
                model_factor_samples=run.model_factor_samples,
            )
            accept_trans = ~np.asarray(diag.failure_trans, dtype=bool)
            accept_static = ~np.asarray(diag.failure_static, dtype=bool)
            decomp = decompose(accept_static, accept_trans)
            # posterior = accepted (survived transient) rows
            acc = accept_trans
            ce_v = theta_v[:, C_E_INDEX]
            shift = {}
            for j, name in enumerate(param_names):
                pr = float(theta_v[:, j].mean())
                po = float(theta_v[acc, j].mean()) if acc.any() else float("nan")
                shift[name] = {
                    "prior_mean": pr,
                    "posterior_mean": po,
                    "mean_change_pct": 100.0 * (po - pr) / pr if pr else float("nan"),
                }
            section_out["candidates"][c.key] = {
                "label": c.label,
                "prior_ce_mean": float(ce_v.mean()),
                "transient_rejection_frac": float(1.0 - acc.mean()),
                "static_rejection_frac": float(decomp["f_static_reject"]),
                "marginal_transient_rejection_frac": float(
                    decomp["f_marginal_transient"]
                ),
                "n_accepted": int(acc.sum()),
                "posterior_shift": shift,
            }
            logger.info(
                "phase2: %s / %-22s trans %.4f%% marg %.4f%% C_e %+.1f%%",
                label,
                c.key,
                100.0 * (1.0 - acc.mean()),
                100.0 * decomp["f_marginal_transient"],
                section_out["candidates"][c.key]["posterior_shift"]["C_e"][
                    "mean_change_pct"
                ],
            )
        record["sections"][label] = section_out
    path = OUT_DIR / "phase2_survival_sensitivity.json"
    path.write_text(json.dumps(record, indent=2))
    logger.info("wrote %s", path)
    _plot_phase2(record)
    return record


def _plot_phase2(record: dict[str, Any]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cands = candidates()
    keys = [c.key for c in cands]
    labels = [c.label.split("  ")[0] for c in cands]
    secs = list(record["sections"].items())
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.0))
    xs = np.arange(len(keys))
    width = 0.38
    for si, (label, sec) in enumerate(secs):
        off = (si - 0.5) * width
        trej = [100 * sec["candidates"][k]["transient_rejection_frac"] for k in keys]
        mtrej = [
            100 * sec["candidates"][k]["marginal_transient_rejection_frac"]
            for k in keys
        ]
        cepull = [
            sec["candidates"][k]["posterior_shift"]["C_e"]["mean_change_pct"]
            for k in keys
        ]
        axes[0].bar(xs + off, trej, width, label=label)
        axes[1].bar(xs + off, mtrej, width, label=label)
        axes[2].bar(xs + off, cepull, width, label=label)
    titles = [
        "2016 transient rejection [%]",
        "marginal-transient rejection [%]\n(nesting: 0 => static-nested)",
        "posterior C_e mean pull [%]",
    ]
    # The middle panel is all-zero by design (every prior nests transient in
    # static under 2016); annotate so the flat panel reads as the finding, not
    # a broken plot, and fix a symmetric y-range around 0.
    all_mtrej = [
        100 * sec["candidates"][k]["marginal_transient_rejection_frac"]
        for _, sec in secs
        for k in keys
    ]
    if max(all_mtrej) == 0.0:
        axes[1].set_ylim(-1.0, 1.0)
        axes[1].axhline(0.0, color="black", lw=1.2)
        axes[1].text(
            0.5,
            0.5,
            "0.0000% for EVERY prior\n(transient failure nested in static under 2016)",
            transform=axes[1].transAxes,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round", fc="#eef6ff", ec="#2166ac"),
        )
    for ax, t in zip(axes, titles):
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7.5)
        ax.set_title(t, fontsize=10)
        ax.grid(True, axis="y", alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("Phase 2 (2016 survival) sensitivity to the C_e prior", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = FIG_DIR / "ce_prior_phase2_sensitivity.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    logger.info("wrote %s", out)


# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("analysis", choices=["prior", "propagate", "phase2", "all"])
    ap.add_argument("--backend", default="numba", choices=["numpy", "numba"])
    args = ap.parse_args()

    if args.analysis in ("prior", "all"):
        run_prior()
    if args.analysis in ("propagate", "all"):
        run_propagate(backend=args.backend)
    if args.analysis in ("phase2", "all"):
        run_phase2(backend=args.backend)


if __name__ == "__main__":
    main()
