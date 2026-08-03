"""Phase 1 statistical convergence study (ADR-0031): N-ladder + LHS vs crude MC.

One replicate design, two questions (see ``bep_reliability_engine.convergence``):

1. **Estimator convergence (spec §11).** Does N = 10⁵ resolve the failure
   probabilities of interest at a *governing* cross-section? Measured as the
   empirical replicate CoV of P̂_f across a ladder of N, compared against the
   ``1/sqrt(N)`` law and the < 5% field target (Schweckendiek 2014).
2. **Tail variance (spec §12 fm5).** Does LHS buy variance reduction over crude
   Monte Carlo *where it matters* — the deep transient failure tail governed by
   the multiplicative C_e×k_aq interaction (fm7)? Measured as the CoV ratio
   ``CoV_MC / CoV_LHS`` per conditioning level, bulk to tail.

Governing section: **KP58.8** (matrix d_70). BEP is genuinely reachable there —
transient P_f ≈ 0.27 at the design HWL (41.03 m MSL), both branches bracket the
transition with fitted-lognormal deliverables — unlike the foreshore-suppressed
KP62.0 (transient P_f ≈ 8·10⁻⁵ at HWL, transition ~4 m above any attainable
stage). It is also the ADR-0029 fm5 baseline, so this refreshes that finding
under the current physics (C_e = 0.055, raw heads, Δt = 225 s).

Four transient conditioning levels on the production grid span bulk → deep tail
(transient P_f ≈ {0.26, 0.025, 5·10⁻³, 4·10⁻⁴}). Both samplers are drawn from
``sample_theta_tilted`` with no tilt (LHS = ``stratified=True`` is bit-identical
to production M2; crude MC = ``stratified=False`` is the spec §13 debug
fallback), sharing the same iid seepage-length L per replicate so the schemes
differ only in the θ design. Evaluation uses the ADR-0029 numba backend
(failure-indicator-identical to numpy at production scale).

Run from the repository root (venv active)::

    python scripts/convergence_study.py            # full study (KP58.8, default)
    python scripts/convergence_study.py --replicates 3 --n-ladder 1000,3000,10000
    python scripts/convergence_study.py --plot-only # redraw figures from the JSON

    # a second reachable-section record (KP60.0; levels picked from its own
    # production grid to span the same bulk -> deep-tail range):
    python scripts/convergence_study.py \
        --config kp60_0_historical_matrix.yaml \
        --levels 42.75,42.00,41.50,41.25

Outputs (per the repo results/ convention; the default KP58.8 config keeps the
original unsuffixed filenames the ADR-0031 note references, any other config
gets a ``<slug>``-suffixed sibling set so the two records never collide):
  * ``results/convergence/kp58_8_convergence_study.json``      — the full record
  * ``results/figures/convergence_n_ladder.png``                — Objective 1
  * ``results/figures/convergence_tail_lhs_vs_crude.png``       — Objective 2
  * tracked copies under ``docs/decisions/`` / ``docs/figures/``
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _figstyle import section_label as _section_label  # noqa: E402

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.convergence import (  # noqa: E402
    binomial_cov,
    n_for_cov_target,
    run_replicates,
)
from bep_reliability_engine.evaluator import evaluate_batch  # noqa: E402
from bep_reliability_engine.run import (  # noqa: E402
    _hydrograph_for_level,
    _load_canonical_or_none,
)
from bep_reliability_engine.sampling import sample_seepage_length  # noqa: E402

DEFAULT_CONFIG_NAME = "kp58_8_historical_matrix.yaml"

# Four production-grid transient conditioning levels spanning bulk -> deep tail
# per section (transient P_f approx {0.26, 0.025, 5e-3, 4e-4} at N = 1e5),
# picked by inspecting each section's own production sweep grid. Only the
# default (KP58.8) has a built-in default; other configs must pass --levels
# explicitly (module docstring shows the KP60.0 invocation).
DEFAULT_LEVELS = [41.00, 40.25, 40.00, 39.75]
DEFAULT_N_LADDER = [1_000, 3_000, 10_000, 30_000, 100_000, 300_000]
DEFAULT_REPLICATES = 50
BACKEND = "numba"


def _slug(config_path: Path) -> str:
    """A short section identifier from the config filename, e.g. 'kp60_0_matrix'."""
    return config_path.stem.replace("_historical", "")


def _output_paths(config_path: Path) -> dict[str, Path]:
    """Working (results/) and tracked (docs/) artifact paths for one config.

    The default KP58.8 config keeps the original unsuffixed filenames the
    ADR-0031 note and decision text already reference; any other config gets a
    ``<slug>``-suffixed sibling set so a second section's record never
    collides with (or silently overwrites) the first.
    """
    if config_path.name == DEFAULT_CONFIG_NAME:
        return {
            "json": REPO_ROOT
            / "results"
            / "convergence"
            / "kp58_8_convergence_study.json",
            "fig_conv": REPO_ROOT / "results" / "figures" / "convergence_n_ladder.png",
            "fig_tail": REPO_ROOT
            / "results"
            / "figures"
            / "convergence_tail_lhs_vs_crude.png",
            "tracked_json": REPO_ROOT
            / "docs"
            / "decisions"
            / "adr0031-convergence-study.json",
            "tracked_fig_conv": REPO_ROOT
            / "docs"
            / "figures"
            / "adr0031-convergence-n-ladder.png",
            "tracked_fig_tail": REPO_ROOT
            / "docs"
            / "figures"
            / "adr0031-tail-lhs-vs-crude.png",
        }
    slug = _slug(config_path)
    return {
        "json": REPO_ROOT
        / "results"
        / "convergence"
        / f"{slug}_convergence_study.json",
        "fig_conv": REPO_ROOT
        / "results"
        / "figures"
        / f"{slug}_convergence_n_ladder.png",
        "fig_tail": REPO_ROOT / "results" / "figures" / f"{slug}_tail_lhs_vs_crude.png",
        "tracked_json": REPO_ROOT
        / "docs"
        / "decisions"
        / f"adr0031-convergence-study-{slug}.json",
        "tracked_fig_conv": REPO_ROOT
        / "docs"
        / "figures"
        / f"adr0031-convergence-n-ladder-{slug}.png",
        "tracked_fig_tail": REPO_ROOT
        / "docs"
        / "figures"
        / f"adr0031-tail-lhs-vs-crude-{slug}.png",
    }


# Seed-stream tags (SeedSequence entropy words) so every draw is distinct and
# reproducible from the config seed. LHS and crude MC get independent theta
# streams; the seepage-length stream is keyed on (level, replicate) only, so the
# same L feeds both schemes at a replicate index (isolates the theta design).
_TAG_LHS = 0x0000
_TAG_CRUDE = 0x1111
_TAG_LENGTH = 0x5EE9


def _make_evaluate(record, geometry, cfg):
    """Return an ``evaluate(theta_sample, seepage) -> (fail_static, fail_trans)``.

    Closes over the built hydrograph record and geometry for one conditioning
    level; one M8 ``evaluate_batch`` call on the numba backend.
    """

    def evaluate(theta_sample, seepage):
        return evaluate_batch(
            theta_sample.theta_matrix,
            record,
            geometry,
            l_ini=0.0,
            seepage_length_samples=seepage,
            alpha_exponent=cfg.alpha_exponent,
            alpha_exponent_transient=cfg.alpha_exponent_transient,
            theta_repose_rad=cfg.theta_repose_rad,
            relative_density=cfg.relative_density_insitu,
            foreland_open=cfg.foreland_treatment == "open_entry",
            progression_backend=BACKEND,
        )

    return evaluate


def _make_draw_length(cfg, base_seed: int, level_index: int):
    """Per-replicate iid seepage-length draw, seeded on (level, replicate) only.

    Independent of the sampler tag, so LHS and crude MC receive the same L at a
    given replicate index (the fm5 isolation). Returns None when L is
    deterministic (``config.seepage_length_cov`` unset).
    """

    def draw_length(replicate_index: int, n_samples: int):
        if cfg.seepage_length_cov is None:
            return None
        seed = int(
            np.random.SeedSequence(
                [base_seed, _TAG_LENGTH, level_index, replicate_index]
            ).generate_state(1)[0]
        )
        return sample_seepage_length(
            cfg.geometry.L, cfg.seepage_length_cov, seed=seed, n_samples=n_samples
        )

    return draw_length


def _scheme_block(sample) -> dict:
    """Serialize one sampler's replicate statistics at one rung."""
    block: dict[str, float] = {}
    for branch in ("static", "transient"):
        block[f"mean_p_f_{branch}"] = sample.mean_p_f(branch)
        block[f"empirical_cov_{branch}"] = sample.cov(branch)
        block[f"zero_failure_fraction_{branch}"] = sample.zero_failure_fraction(branch)
    return block


def run_study(config_path: Path, levels, n_ladder, n_replicates) -> dict:
    """Execute the full replicate study and return the JSON-ready payload."""
    cfg = Config.from_yaml(config_path)
    base_seed = int(cfg.mc.seed)
    canonical = _load_canonical_or_none(cfg)
    geometry = cfg.geometry.as_evaluator_dict()
    marginals = cfg.priors.to_marginal_specs()
    sampler_kwargs = dict(
        rho_log_kaq_d70=cfg.correlation.rho_log_kaq_d70,
        d70_interpretation=cfg.priors.d70_interpretation,
        coupling=cfg.correlation.coupling,
        bounds=cfg.priors.bounds,
    )

    # Warm up the numba kernels once (JIT compile) so it is out of the timings.
    warm_record = _hydrograph_for_level(float(levels[0]), cfg, canonical)
    warm_theta = _warm_theta(marginals, sampler_kwargs)
    _make_evaluate(warm_record, geometry, cfg)(warm_theta, None)

    t_start = time.perf_counter()
    level_records = []
    for level_index, level in enumerate(levels):
        record = _hydrograph_for_level(float(level), cfg, canonical)
        evaluate = _make_evaluate(record, geometry, cfg)
        draw_length = _make_draw_length(cfg, base_seed, level_index)

        rungs = []
        ref_p = {"static": float("nan"), "transient": float("nan")}
        for n_samples in n_ladder:
            lhs = run_replicates(
                marginals=marginals,
                sampler_kwargs=sampler_kwargs,
                evaluate=evaluate,
                draw_length=draw_length,
                n_samples=n_samples,
                n_replicates=n_replicates,
                seed_root=base_seed,
                stratified=True,
                scheme_tag=_TAG_LHS,
                level_tag=level_index,
            )
            crude = run_replicates(
                marginals=marginals,
                sampler_kwargs=sampler_kwargs,
                evaluate=evaluate,
                draw_length=draw_length,
                n_samples=n_samples,
                n_replicates=n_replicates,
                seed_root=base_seed,
                stratified=False,
                scheme_tag=_TAG_CRUDE,
                level_tag=level_index,
            )
            # Reference P_f: the largest-N LHS replicate mean (most precise).
            ref_p = {
                "static": lhs.mean_p_f("static"),
                "transient": lhs.mean_p_f("transient"),
            }
            rung = {
                "n_samples": int(n_samples),
                "lhs": _scheme_block(lhs),
                "crude_mc": _scheme_block(crude),
            }
            for branch in ("static", "transient"):
                p_ref = lhs.mean_p_f(branch)
                rung[f"binomial_cov_{branch}"] = binomial_cov(p_ref, n_samples)
                cov_lhs = lhs.cov(branch)
                cov_crude = crude.cov(branch)
                rung[f"cov_ratio_mc_over_lhs_{branch}"] = (
                    float(cov_crude / cov_lhs)
                    if np.isfinite(cov_crude) and np.isfinite(cov_lhs) and cov_lhs > 0
                    else float("nan")
                )
            rungs.append(rung)
            print(
                f"h={level:6.2f}  N={n_samples:7d}  "
                f"Pf_tr={lhs.mean_p_f('transient'):.3e}  "
                f"CoV_tr LHS={lhs.cov('transient'):.3f} / "
                f"MC={crude.cov('transient'):.3f}  "
                f"(ratio MC/LHS={rungs[-1]['cov_ratio_mc_over_lhs_transient']:.2f})",
                flush=True,
            )

        level_records.append(
            {
                "level_m": float(level),
                "p_f_ref": ref_p,
                "n_for_cov_target": {
                    "static": n_for_cov_target(ref_p["static"]),
                    "transient": n_for_cov_target(ref_p["transient"]),
                },
                "rungs": rungs,
            }
        )

    runtime = time.perf_counter() - t_start
    return {
        "study": "Phase 1 statistical convergence study (ADR-0031)",
        "objectives": [
            "estimator convergence: empirical CoV(P_f) vs N vs 5% target (spec §11)",
            "tail variance: LHS vs crude MC CoV ratio, bulk->tail (spec §12 fm5)",
        ],
        "config": config_path.name,
        "config_hash": cfg.config_hash(),
        "cross_section_id": cfg.cross_section_id,
        "d70_interpretation": cfg.priors.d70_interpretation,
        "governing_justification": (
            "KP58.8: BEP reachable (transient P_f ~ 0.27 at HWL 41.03 m, both "
            "branches bracket the transition); not foreshore-suppressed like "
            "KP62.0; ADR-0029 fm5 baseline."
            if config_path.name == DEFAULT_CONFIG_NAME
            else f"{cfg.cross_section_id} ({cfg.priors.d70_interpretation} d_70): "
            "second reachable-section record alongside KP58.8 (ADR-0031), levels "
            "picked from its own production grid to span the same bulk -> "
            "deep-tail P_f range."
        ),
        "branch_focus": "transient",
        "hydrograph_source": "d4pdf_scaled_canonical",
        "progression_backend": BACKEND,
        "base_seed": base_seed,
        "cov_target": 0.05,
        "n_replicates": int(n_replicates),
        "n_ladder": [int(n) for n in n_ladder],
        "levels": level_records,
        "runtime_seconds": runtime,
    }


def _warm_theta(marginals, sampler_kwargs):
    """A tiny throwaway theta sample used only to force numba compilation."""
    from bep_reliability_engine.tail_sampling import sample_theta_tilted

    return sample_theta_tilted(
        marginals,
        seed=0,
        shift_z=None,
        n_samples=256,
        stratified=True,
        **sampler_kwargs,
    ).theta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_NAME,
        help="config YAML under configs/ (or an absolute/relative path); "
        "default is the KP58.8 governing-section config",
    )
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument(
        "--n-ladder",
        type=str,
        default=",".join(str(n) for n in DEFAULT_N_LADDER),
        help="comma-separated N values",
    )
    parser.add_argument(
        "--levels",
        type=str,
        default=None,
        help="comma-separated conditioning stages [m MSL]; required unless "
        "--config is the KP58.8 default, which has its own built-in levels",
    )
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help="skip the sweep; redraw figures from the existing JSON",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / "configs" / config_path
    paths = _output_paths(config_path)

    if args.plot_only:
        source = paths["json"] if paths["json"].exists() else paths["tracked_json"]
        payload = json.loads(source.read_text(encoding="utf-8"))
        _plot(payload, paths)
        return

    if args.levels is None:
        if config_path.name != DEFAULT_CONFIG_NAME:
            parser.error(
                "--levels is required for a non-default --config (no built-in "
                "levels exist for this section); see the module docstring for "
                "the KP60.0 example."
            )
        levels = DEFAULT_LEVELS
    else:
        levels = [float(x) for x in args.levels.split(",")]
    n_ladder = [int(n) for n in args.n_ladder.split(",")]
    payload = run_study(config_path, levels, n_ladder, args.replicates)

    text = json.dumps(payload, indent=2) + "\n"
    for path in (paths["json"], paths["tracked_json"]):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    print(f"({payload['runtime_seconds']:.0f} s)")
    _plot(payload, paths)


def _plot(payload: dict, paths: dict[str, Path]) -> None:
    """Draw the two study figures from the JSON payload."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    branch = payload["branch_focus"]
    target = payload["cov_target"]
    n_rep = payload["n_replicates"]
    levels = payload["levels"]
    colors = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    # ---- Figure 1: Objective 1 — empirical CoV (LHS) vs N -----------------
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    n_all = np.array(payload["n_ladder"], dtype=float)
    for i, lvl in enumerate(levels):
        p_ref = lvl["p_f_ref"][branch]
        ns, covs = [], []
        for rung in lvl["rungs"]:
            cov = rung["lhs"][f"empirical_cov_{branch}"]
            if np.isfinite(cov):
                ns.append(rung["n_samples"])
                covs.append(cov)
        color = colors[i % len(colors)]
        ax.loglog(
            ns,
            covs,
            "o-",
            color=color,
            label=rf"$h={lvl['level_m']:.2f}$ m, $P_f\approx${p_ref:.1e}",
        )
    # 1/sqrt(N) reference anchored to the shallowest level's first point.
    anchor = levels[0]["rungs"][0]
    ref_cov = anchor["lhs"][f"empirical_cov_{branch}"]
    ref_n = anchor["n_samples"]
    if np.isfinite(ref_cov):
        ax.loglog(
            n_all,
            ref_cov * np.sqrt(ref_n / n_all),
            "k:",
            label=r"$1/\sqrt{N}$ reference",
        )
    ax.axhline(target, color="0.4", ls="--", lw=1.2, label=f"{target:.0%} target")
    ax.set_xlabel("realizations $N$")
    ax.set_ylabel(rf"empirical CoV of $\hat{{P}}_f$ ({branch}), $R={n_rep}$ replicates")
    ax.set_title(
        f"Estimator convergence, {_section_label(payload['cross_section_id'])} "
        f"({payload['d70_interpretation']} $d_{{70}}$), Latin hypercube sampling"
    )
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    _savefig_both(fig, paths["fig_conv"], paths["tracked_fig_conv"])
    plt.close(fig)

    # ---- Figure 2: Objective 2 — LHS vs crude MC, bulk -> tail ------------
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11.5, 5.0))
    for i, lvl in enumerate(levels):
        color = colors[i % len(colors)]
        p_ref = lvl["p_f_ref"][branch]
        ns_l, cov_l, ns_c, cov_c = [], [], [], []
        for rung in lvl["rungs"]:
            cl = rung["lhs"][f"empirical_cov_{branch}"]
            cc = rung["crude_mc"][f"empirical_cov_{branch}"]
            if np.isfinite(cl):
                ns_l.append(rung["n_samples"])
                cov_l.append(cl)
            if np.isfinite(cc):
                ns_c.append(rung["n_samples"])
                cov_c.append(cc)
        ax0.loglog(ns_l, cov_l, "o-", color=color, label=rf"$P_f\approx${p_ref:.1e}")
        ax0.loglog(ns_c, cov_c, "s--", color=color, alpha=0.7)
    ax0.axhline(target, color="0.4", ls=":", lw=1.0)
    ax0.set_xlabel("realizations $N$")
    ax0.set_ylabel(rf"empirical CoV of $\hat{{P}}_f$ ({branch})")
    ax0.set_title("LHS (solid ●) vs crude MC (dashed ■)")
    ax0.grid(True, which="both", alpha=0.3)
    ax0.legend(fontsize=8, title="conditioning level")

    # Right panel: variance-reduction ratio MC/LHS vs P_f, one point per level.
    # The ratio is N-invariant in expectation, so the ladder mean per level is
    # the robust statistic (its SE shrinks with both R and the ladder length).
    p_axis, ratios, se = [], [], []
    for lvl in levels:
        vals = np.array(
            [
                r[f"cov_ratio_mc_over_lhs_{branch}"]
                for r in lvl["rungs"]
                if np.isfinite(r[f"cov_ratio_mc_over_lhs_{branch}"])
            ]
        )
        if vals.size < 2:
            continue
        p_axis.append(lvl["p_f_ref"][branch])
        ratios.append(float(vals.mean()))
        se.append(float(vals.std(ddof=1) / np.sqrt(vals.size)))
    if p_axis:
        ax1.errorbar(
            p_axis,
            ratios,
            yerr=se,
            fmt="D-",
            color="#1f77b4",
            capsize=4,
            label="ladder mean ± SE",
        )
        ax1.set_xscale("log")
        ax1.invert_xaxis()
    ax1.axhline(1.0, color="0.3", ls="--", lw=1.2, label="parity (no advantage)")
    ax1.set_xlabel(rf"$P_f$ ({branch}) — deeper tail $\rightarrow$")
    ax1.set_ylabel(r"variance-reduction ratio  $\mathrm{CoV_{MC}}/\mathrm{CoV_{LHS}}$")
    ax1.set_title("LHS advantage decays bulk → tail")
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend(fontsize=8)

    fig.suptitle(
        f"fm5 tail-variance: LHS vs crude MC — {payload['cross_section_id']}, "
        f"R={n_rep}",
        y=1.02,
    )
    fig.tight_layout()
    _savefig_both(
        fig, paths["fig_tail"], paths["tracked_fig_tail"], bbox_inches="tight"
    )
    plt.close(fig)


def _savefig_both(fig, working_path: Path, tracked_path: Path, **kwargs) -> None:
    """Save one figure to both the results/ working copy and the tracked docs/ copy."""
    for path in (working_path, tracked_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160, **kwargs)
        print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
