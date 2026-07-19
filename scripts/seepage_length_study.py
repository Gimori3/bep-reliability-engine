"""Single-topic study of the stochastic seepage length L (companion to ADR-0033/0037).

L is the top- or co-top total-effect input for every QoI (ADR-0033 GSA), yet it
is modelled as ``Lognormal(mean=geometry.L, CoV 0.20)`` sampled independently of
theta and independently per cross-section, and ADR-0037's length effect is the
identity (n_eff = 1) at the primary lambda_ac = 250 m. This script quantifies the
consequences of both the *marginal* and the *spatial-correlation* choices, and the
*Phase 2 ceiling* L imposes, WITHOUT changing any default behaviour.

Three analyses (subcommands, or ``all``):

* ``marginal``   — reduced-N sweeps varying CoV(L) and the marginal shape across the
                   four confined sections; how far P_f (both branches) moves.
* ``system``     — the length effect restated at the 114-segment system level: the
                   inter-segment L-correlation implied by lambda_ac, and the
                   independence <-> full-correlation bounds on a reach union.
* ``ceiling``    — how much of the residual Phase 2 posterior uncertainty at
                   KP58.8/60.0 is L-borne (irreducible by survival evidence), read
                   off the persisted production posteriors + the GSA.

Everything reuses the production kernels through ``evaluate_batch`` (validated
bit-identical to the persisted sweeps) and the public regeneration seams; no
config default is touched, no persisted artifact is modified.

Outputs
-------
JSON records under ``results/sensitivity/seepage_length/`` (gitignored, regenerable)
and figures under ``docs/figures/seepage_length_*.png``.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm
from scipy.stats.qmc import LatinHypercube

from bayesian_reliability_updating.posterior import PosteriorResult
from bep_reliability_engine import run as runmod
from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import evaluate_batch

logger = logging.getLogger("seepage_length_study")

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "configs"
OUT_DIR = REPO / "results" / "sensitivity" / "seepage_length"
FIG_DIR = REPO / "docs" / "figures"
RQ4_CSV = REPO / "results" / "system_integration" / "phase3" / "rq4_annual.csv"

# The four confined production sections (matrix interpretation is the informative
# one; see project-notes.md). Config stem -> label.
SECTIONS: tuple[tuple[str, str], ...] = (
    ("kp57_4_historical_matrix", "KP57.4"),
    ("kp58_8_historical_matrix", "KP58.8"),
    ("kp60_0_historical_matrix", "KP60.0"),
    ("kp62_0_historical_matrix", "KP62.0"),
)

# CoV(L) ladder for the marginal-sensitivity sweep. None = deterministic L.
# 0.15/0.20 are the production values (tab:seepage_length_prior); 0.10 is the
# base-width-reading-only reading; 0.30/0.40 stress a wider epistemic allowance.
COV_LADDER: tuple[float | None, ...] = (None, 0.10, 0.15, 0.20, 0.30, 0.40)
PROD_COV = 0.20  # the production value at three of the four sections

STUDY_N = 30_000  # reduced N; numba backend keeps a full ladder to minutes
STUDY_SEED_SALT = 0x5EE_10A  # this study's own L design salt (distinct from run.py)


# --------------------------------------------------------------------------- #
# Shared engine driver (validated bit-identical to the persisted sweep)        #
# --------------------------------------------------------------------------- #
def _load_config(stem: str, *, n: int, backend: str) -> Config:
    cfg = Config.from_yaml(CONFIG_DIR / f"{stem}.yaml")
    # Reduced N and (optionally) the numba backend for the ladder; nothing here
    # is persisted, so this never touches a production default.
    data = cfg.model_dump()
    data["mc"]["n_samples"] = int(n)
    data["timestepper"]["progression_backend"] = backend
    return Config.model_validate(data)


def _draw_L(
    mean_m: float,
    cov: float,
    *,
    design: NDArray[np.float64],
    family: str = "lognormal",
    mean_shift: float = 0.0,
) -> NDArray[np.float64]:
    """Map one fixed LHS design to physical L under a chosen marginal.

    Holding ``design`` (the unit-hypercube draws) fixed across CoV/shape makes
    every ladder rung differ ONLY in the distribution, not in the sampling noise
    — the cleanest possible CoV/shape contrast.

    Parameters
    ----------
    family : {'lognormal', 'normal'}
        ``lognormal`` reproduces ``sample_seepage_length`` exactly; ``normal``
        is the same-moment Gaussian (truncated below at a small positive floor),
        the alternative-shape comparator.
    mean_shift : float
        Fractional shift of the mean (e.g. +0.15 = the memo's one-sided upward
        case toward the longer, classical single-domain path). 0 = as specified.
    """
    z = norm.ppf(design)
    mean = mean_m * (1.0 + mean_shift)
    if family == "lognormal":
        sigma = np.sqrt(np.log1p(cov * cov))
        mu = np.log(mean) - 0.5 * sigma * sigma
        return np.exp(mu + sigma * z)
    if family == "normal":
        L = mean + mean * cov * z
        return np.maximum(L, 0.05 * mean)  # guard the negative tail
    raise ValueError(f"unknown family {family!r}")


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
# Q1 — marginal sensitivity                                                    #
# --------------------------------------------------------------------------- #
def run_marginal(backend: str = "numba") -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "analysis": "marginal_cov_and_shape_sensitivity",
        "n_samples": STUDY_N,
        "backend": backend,
        "cov_ladder": ["deterministic" if c is None else c for c in COV_LADDER],
        "production_cov": PROD_COV,
        "sections": {},
    }
    design = LatinHypercube(d=1, seed=STUDY_SEED_SALT).random(STUDY_N)[:, 0]

    for stem, label in SECTIONS:
        cfg = _load_config(stem, n=STUDY_N, backend=backend)
        theta = runmod._sample_prior(cfg).theta_matrix
        records = runmod.conditioning_hydrographs_for_config(cfg)
        geom = cfg.geometry.as_evaluator_dict()
        grid = np.asarray(cfg.mc.conditioning_grid, float)
        L_mean = float(cfg.geometry.L)

        curves: dict[str, Any] = {}
        # CoV ladder (lognormal), design fixed.
        for cov in COV_LADDER:
            key = "det" if cov is None else f"cov{cov:.2f}"
            L = None if cov is None else _draw_L(L_mean, cov, design=design)
            pf_st, pf_tr = _sweep_pf(cfg, theta, L, records, geom)
            curves[key] = {"static": pf_st.tolist(), "transient": pf_tr.tolist()}
        # Alternative shapes at the production CoV.
        L_norm = _draw_L(L_mean, PROD_COV, design=design, family="normal")
        pf_st, pf_tr = _sweep_pf(cfg, theta, L_norm, records, geom)
        curves["normal_cov0.20"] = {
            "static": pf_st.tolist(),
            "transient": pf_tr.tolist(),
        }
        L_up = _draw_L(L_mean, PROD_COV, design=design, mean_shift=0.15)
        pf_st, pf_tr = _sweep_pf(cfg, theta, L_up, records, geom)
        curves["lognormal_meanplus15pct"] = {
            "static": pf_st.tolist(),
            "transient": pf_tr.tolist(),
        }

        record["sections"][label] = {
            "config": stem,
            "L_mean_m": L_mean,
            "grid_m_msl": grid.tolist(),
            "curves": curves,
        }
        logger.info("marginal: %s done (L_mean=%.1f m)", label, L_mean)

    path = OUT_DIR / "marginal_sensitivity.json"
    path.write_text(json.dumps(record, indent=2))
    logger.info("wrote %s", path)
    return record


# --------------------------------------------------------------------------- #
# Q2 — spatial correlation / system                                            #
# --------------------------------------------------------------------------- #
def _reach_bounds_from_rq4() -> dict[str, Any]:
    """Independence vs full-correlation bounds on a BEP reach union from RQ4.

    The RQ4 CSV carries per-node annual system P_f with BEP only at the four
    OYO nodes (``p_annual_bep`` blank elsewhere). A reach 'union' over the BEP
    nodes is bounded by:
      * independence:      P = 1 - prod(1 - p_i)
      * full correlation:  P = max_i p_i  (comonotone)
    Under the production 'exact' policy the four BEP nodes are 1.2-2.0 km apart
    (>> lambda_ac), so the two bounds are nearly equal — independence is
    physically correct there. The gap only opens if the borehole-free reaches
    are populated (the 'nearest' policy) with segments sharing one section's
    curve.
    """
    import csv

    rows = list(csv.DictReader(open(RQ4_CSV, encoding="utf-8")))
    out: dict[str, Any] = {}
    for scenario in ("historical", "+4K"):
        for source in ("posterior", "prior"):
            # Primary variant only (lambda_ac 250, primary surface, matrix), else
            # the lambda brackets and surface variants duplicate every BEP node.
            pf = [
                float(r["p_annual_bep"])
                for r in rows
                if r["scenario"] == scenario
                and r["bep_source"] == source
                and r["d70"] == "matrix"
                and r["lambda_ac_m"] == "250.0"
                and r["surface_variant"] == "primary"
                and r.get("p_annual_bep", "") not in ("", None)
            ]
            if not pf:
                continue
            pf_arr = np.asarray(pf, float)
            indep = 1.0 - np.prod(1.0 - pf_arr)
            comon = float(pf_arr.max())
            out[f"{scenario}/{source}"] = {
                "n_bep_nodes": int(pf_arr.size),
                "p_bep_nodes": pf_arr.tolist(),
                "reach_union_independent": float(indep),
                "reach_union_comonotone": float(comon),
                "independent_over_comonotone": (
                    float(indep / comon) if comon > 0 else None
                ),
            }
    return out


def _dense_reach_illustration() -> dict[str, Any]:
    """Length-effect-at-system bound for a *densely populated* BEP reach.

    The production 'exact' policy places BEP at only the 4 widely-spaced OYO
    sections, so independence there is physically correct. The tension bites
    only when the borehole-free reach is populated (the 'nearest' policy, or
    future data): then N_seg 200 m segments each carry a section's curve and
    treating them as independent competes with the true effective count
    R/lambda_ac. This illustrates the reach BEP union under each treatment for
    a representative per-segment conditional P_f, at a HWL-like operating point.
    """
    reach_km = 6.8  # Tokachi confined BEP reach KP 56.0-62.8 (thesis scope)
    seg_m = 200.0
    n_seg = int(round(reach_km * 1000.0 / seg_m))  # segment-independence count
    out: dict[str, Any] = {"reach_km": reach_km, "n_segments_200m": n_seg, "cases": {}}
    # A representative CONDITIONAL (per-event, not annual) segment P_f at an
    # operating stage; spanned to show the bound is order-robust.
    for p_cs in (0.02, 0.10, 0.25):
        row: dict[str, Any] = {"p_cs": p_cs}
        row["independent_Nseg"] = float(1.0 - (1.0 - p_cs) ** n_seg)
        row["comonotone_full_corr"] = float(p_cs)
        for name, lam in (
            ("lambda250", 250.0),
            ("lambda100", 100.0),
            ("lambda40", 40.0),
        ):
            n_eff = reach_km * 1000.0 / lam
            row[f"correlated_{name}"] = float(1.0 - (1.0 - p_cs) ** n_eff)
        out["cases"][f"p_cs_{p_cs}"] = row
    return out


def run_system() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seg = 200.0  # Uemura segment length / node spacing [m]
    lambdas = {"primary_250": 250.0, "bracket_100": 100.0, "bracket_40": 40.0}
    # Effective-independent-count logic for a reach of length R populated at
    # 200 m spacing: true independent units = R/lambda_ac; the segment-
    # independence model assumes R/seg = N_seg units. The ratio is lambda_ac/seg
    # and is independent of R. >1 => independence OVER-counts (conservative);
    # <1 => independence UNDER-counts (misses within-segment sub-units).
    ratios = {name: lam / seg for name, lam in lambdas.items()}
    record: dict[str, Any] = {
        "analysis": "spatial_correlation_system_bounds",
        "segment_spacing_m": seg,
        "lambda_ac_m": lambdas,
        "independence_over_true_effective_count": ratios,
        "note": (
            "ratio = lambda_ac / segment_spacing; the factor by which treating "
            "200 m segments as independent over-counts (>1) or under-counts (<1) "
            "the effective number of independent cross-sections in a reach. "
            "n_eff_within_segment (ADR-0037) = max(1, seg/lambda_ac); the reach "
            "restatement drops the clamp and compounds across segments."
        ),
        "reach_union_bounds_from_rq4": _reach_bounds_from_rq4(),
        "dense_reach_illustration": _dense_reach_illustration(),
    }
    path = OUT_DIR / "system_correlation.json"
    path.write_text(json.dumps(record, indent=2))
    logger.info("wrote %s", path)
    return record


# --------------------------------------------------------------------------- #
# Q3 — Phase 2 ceiling                                                         #
# --------------------------------------------------------------------------- #
def _correlation_ratio(
    y: NDArray[np.float64], x: NDArray[np.float64], bins: int = 20
) -> float:
    """First-order sensitivity eta^2 = Var(E[y|x]) / Var(y) by binning x.

    A sample-based main-effect (first-order Sobol') proxy computable from any
    sample. Robust for a Bernoulli y (the failure indicator).
    """
    y = np.asarray(y, float)
    vy = y.var()
    if vy <= 0.0:
        return 0.0
    edges = np.quantile(x, np.linspace(0.0, 1.0, bins + 1))
    edges[-1] += 1e-9
    idx = np.clip(np.digitize(x, edges) - 1, 0, bins - 1)
    num = 0.0
    ybar = y.mean()
    for b in range(bins):
        m = idx == b
        if m.any():
            num += m.mean() * (y[m].mean() - ybar) ** 2
    return float(num / vy)


def run_ceiling(backend: str = "numba") -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    param_names = ["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]
    posts = {
        "KP58.8": (
            REPO / "results/phase2/tokachi_kp58.8_historical_matrix_posterior.h5",
            "kp58_8_historical_matrix",
        ),
        "KP60.0": (
            REPO / "results/phase2/tokachi_kp60.0_historical_matrix_posterior.h5",
            "kp60_0_historical_matrix",
        ),
    }
    record: dict[str, Any] = {
        "analysis": "phase2_L_borne_ceiling",
        "sections": {},
        "note": (
            "The posterior L marginal ~= the prior L marginal (survival barely "
            "moves L, which is not in the filtered theta vector), while the theta "
            "marginals shift. eta^2_L is the first-order share of the future-level "
            "transient failure variance carried by L, prior vs posterior."
        ),
    }
    for label, (path, stem) in posts.items():
        if not path.exists():
            logger.warning("missing posterior %s; skipping", path)
            continue
        post = PosteriorResult.load(path)
        theta = post.theta_matrix
        L = post.seepage_length_samples
        accept = post.accept
        n = int(accept.size)
        na = int(accept.sum())

        def _moments(v: NDArray[np.float64], m: NDArray[np.bool_]) -> dict[str, float]:
            vv = v[m]
            return {
                "mean": float(vv.mean()),
                "std": float(vv.std()),
                "cov": float(vv.std() / vv.mean()) if vv.mean() != 0 else float("nan"),
            }

        all_mask = np.ones(n, bool)
        L_prior = _moments(L, all_mask)
        L_post = _moments(L, accept)
        theta_shift = {}
        for j, name in enumerate(param_names):
            pr = _moments(theta[:, j], all_mask)
            po = _moments(theta[:, j], accept)
            theta_shift[name] = {
                "prior_mean": pr["mean"],
                "posterior_mean": po["mean"],
                "mean_change_pct": 100.0 * (po["mean"] - pr["mean"]) / pr["mean"],
            }

        # First-order L share of a future-level transient failure indicator,
        # prior vs posterior, re-evaluated through the production kernels at a
        # shoulder-ish future stage. We reconstruct the config to get geometry
        # and a loading record, then evaluate on prior and posterior rows.
        eta = None
        if na > 200:
            # Config from configs/ (same hash as the posterior's Phase 1 source);
            # gives geometry + grid + the canonical loading shape. Full production
            # N, so the posterior theta/L rows pair with it row-for-row.
            cfg = _load_config(
                stem, n=int(post.metadata["phase1"]["n_samples"]), backend=backend
            )
            records = runmod.conditioning_hydrographs_for_config(cfg)
            geom = cfg.geometry.as_evaluator_dict()
            grid = np.asarray(cfg.mc.conditioning_grid, float)
            # choose a level near prior transient P_f ~ 0.1-0.4 (informative)
            prior_pf = np.asarray(post.P_f_trans_prior_raw, float)
            want = np.argmin(np.abs(prior_pf - 0.25))
            rec = records[want]
            _cs, ct = evaluate_batch(
                theta,
                rec,
                geom,
                seepage_length_samples=L,
                alpha_exponent=cfg.alpha_exponent,
                theta_repose_rad=cfg.theta_repose_rad,
                relative_density=cfg.relative_density_insitu,
                progression_backend=cfg.timestepper.progression_backend,
            )
            y = ct.astype(float)
            # combined theta "super-variable" via its dominant axis k_aq is not
            # a clean scalar; report L, k_aq, C_e first-order shares.
            eta = {
                "level_m": float(grid[want]),
                "prior_pf": float(y.mean()),
                "prior": {
                    "L": _correlation_ratio(y, L),
                    "k_aq": _correlation_ratio(y, theta[:, 0]),
                    "C_e": _correlation_ratio(y, theta[:, 6]),
                },
            }
            if na > 200:
                ya = y[accept]
                eta["posterior_pf"] = float(ya.mean())
                eta["posterior"] = {
                    "L": _correlation_ratio(ya, L[accept]),
                    "k_aq": _correlation_ratio(ya, theta[accept, 0]),
                    "C_e": _correlation_ratio(ya, theta[accept, 6]),
                }

        record["sections"][label] = {
            "n_prior": n,
            "n_accepted": na,
            "rejection_fraction": 1.0 - na / n,
            "L_prior": L_prior,
            "L_posterior": L_post,
            "L_cov_change_pct": 100.0
            * (L_post["cov"] - L_prior["cov"])
            / L_prior["cov"],
            "L_mean_change_pct": 100.0
            * (L_post["mean"] - L_prior["mean"])
            / L_prior["mean"],
            "theta_marginal_shift": theta_shift,
            "future_level_first_order_shares": eta,
        }
        logger.info("ceiling: %s done (accepted %d/%d)", label, na, n)

    path = OUT_DIR / "phase2_ceiling.json"
    path.write_text(json.dumps(record, indent=2))
    logger.info("wrote %s", path)
    return record


# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "analysis",
        choices=["marginal", "system", "ceiling", "all"],
        help="which analysis to run",
    )
    ap.add_argument("--backend", default="numba", choices=["numpy", "numba"])
    args = ap.parse_args()

    if args.analysis in ("marginal", "all"):
        run_marginal(backend=args.backend)
    if args.analysis in ("system", "all"):
        run_system()
    if args.analysis in ("ceiling", "all"):
        run_ceiling(backend=args.backend)


if __name__ == "__main__":
    main()
