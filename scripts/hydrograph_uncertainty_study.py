"""Green Light 5 companion: event shapes and event-constant rating error.

Read production inputs through --data-repo; write only this worktree's outputs.
No production API, default, config or persisted sweep is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import h5py
import numpy as np
from scipy.special import roots_hermitenorm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.evaluator import evaluate_batch  # noqa: E402
from bep_reliability_engine.hydrographs import (  # noqa: E402
    CanonicalShape,
    build_hydrograph_record,
    conditioning_record_for_level,
    load_rating_coefficients,
    normalize_stage_shape,
    parse_member_header,
    rating_curve_path,
    read_discharge_ensemble,
    resample_record,
    resolve_band_workbook,
)
from bep_reliability_engine.run import (  # noqa: E402
    seepage_length_samples_for_config,
)
from system_integration.bep_input import FragilityCurve  # noqa: E402
from system_integration.uemura_models import (  # noqa: E402
    SCOUR_K_CONVERSION_USACE,
    draw_overflow,
    draw_scour,
    load_segment_inputs,
    overflow_failure_fraction,
    scour_failure_fraction,
)

SEED = 20260927
QUANTILES = (0, 0.5, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995, 1)
OUT = REPO / "results/hydrograph_uncertainty"
KPS = (57.4, 58.8, 60.0, 62.0)


def digest(path: Path) -> str:
    """SHA256 input pin, including ignored production artifacts."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stratified_selection(members: dict, per_bin: int = 4) -> list[dict]:
    """Uniform without replacement within peak-rank bins and prescribed SSTs."""
    groups: dict[str, list[str]] = {}
    for name in sorted(members):
        sst = parse_member_header(name)["sst"] or "HPB"
        groups.setdefault(sst, []).append(name)
    rng = np.random.default_rng(SEED)
    selections = []
    for sst, names in sorted(groups.items()):
        ranked = sorted(names, key=lambda name: (float(max(members[name])), name))
        edges = np.rint(np.asarray(QUANTILES) * len(ranked)).astype(int)
        for b, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
            pool = ranked[lo:hi]
            if not pool:
                continue
            selected = rng.choice(pool, size=min(per_bin, len(pool)), replace=False)
            selections.append(
                dict(
                    stratum=f"{sst}_{b}",
                    population=len(pool),
                    weight=len(pool) / len(ranked) / len(groups),
                    events=selected.tolist(),
                )
            )
    assert np.isclose(sum(s["weight"] for s in selections), 1)
    return selections


def curve(grid: np.ndarray, p: np.ndarray) -> FragilityCurve:
    """Existing raw/probit interpolation, with no fitted extrapolation."""
    return FragilityCurve(grid, p, p, p, None, False, "transient", "g5", "g5")


def population(data_repo: Path, kp: float, berm: bool, n: int) -> dict:
    """Exact subset of persisted theta and its original independently drawn L."""
    stem = f"tokachi_kp{kp:.1f}_historical_matrix"
    base = data_repo / "results"
    path = (
        base / "sensitivity/adr0050_drained_bracket" / f"{stem}_berm_only.h5"
        if berm
        else base / f"{stem}.h5"
    )
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    config = Config.model_validate(meta["config"])
    assert config.priors.d_70.mean in (0.0009, 0.00065, 0.00074, 0.00075)
    indices = np.random.default_rng(SEED).permutation(config.mc.n_samples)[:n]
    with h5py.File(path, "r") as f:
        theta = f["theta_matrix"][:][indices]
        grid = f["conditioning_grid"][:]
        s = f["failure_matrix_static"][:][indices]
        t = f["failure_matrix_trans"][:][indices]
    lengths = seepage_length_samples_for_config(config)[indices]
    return dict(
        config=config,
        theta=theta,
        lengths=lengths,
        grid=grid,
        static=s,
        transient=t,
        input_path=str(path),
        input_sha256=digest(path),
        config_hash=config.config_hash(),
    )


def evaluate(pop: dict, record, offset: float = 0, backend: str = "numba"):
    """Apply the published event-constant shift through identical head differences."""
    cfg = pop["config"]
    geom = cfg.geometry.as_evaluator_dict()
    geom["z_toe"] -= offset
    return evaluate_batch(
        pop["theta"],
        resample_record(record, 225.0),
        geom,
        seepage_length_samples=pop["lengths"],
        alpha_exponent=cfg.alpha_exponent,
        alpha_exponent_transient=cfg.alpha_exponent_transient,
        theta_repose_rad=cfg.theta_repose_rad,
        relative_density=cfg.relative_density_insitu,
        foreland_open=cfg.foreland_treatment == "open_entry",
        progression_backend=backend,
        critical_length_factor=cfg.critical_length_factor,
        toe_gradient_relief_factor=cfg.toe_gradient_relief_factor,
        crack_resistance_factor=cfg.crack_resistance_factor,
        foreland_seepage_credit=cfg.foreland_seepage_credit,
    )


def ensemble(data_repo: Path, scenario: str) -> tuple:
    """Read the mainstem band once, cache locally, and pin its source digest."""
    path = resolve_band_workbook(
        data_repo / "data/raw",
        river="Tokachi",
        kp=58.8,
        scenario="+4K" if scenario == "plus4K" else scenario,
    )
    cache = OUT / f"ensemble_{scenario}.npz"
    sha = digest(path)
    if cache.exists():
        with np.load(cache) as f:
            assert str(f["sha"]) == sha
            return f["time"], dict(zip(f["names"], f["q"])), sha
    hours, members = read_discharge_ensemble(path)
    np.savez_compressed(
        cache, time=hours, names=list(members), q=list(members.values()), sha=sha
    )
    return hours, members, sha


def records(data_repo: Path, kp: float, scenario: str) -> tuple:
    """All local stages and canonical normalized shape on the same rating."""
    hours, members, sha = ensemble(data_repo, scenario)
    coeffs = load_rating_coefficients(
        rating_curve_path(data_repo / "data/raw", "Tokachi")
    )
    a, b = coeffs[kp]

    def build(name, q):
        return build_hydrograph_record(
            hours, q, a_kp=a, b_kp=b, scenario=scenario, event_id=name
        )

    recs = {name: build(name, q) for name, q in members.items()}
    hp_hours, hp_members, _ = ensemble(data_repo, "historical")
    assert np.array_equal(hp_hours, hours)
    source = build("HPB_m064_1987", hp_members["HPB_m064_1987"])
    shape, base, _ = normalize_stage_shape(source.h)
    return recs, CanonicalShape(source, shape, base), members, sha


def summary(values: np.ndarray) -> dict:
    """Annual marginals, conditional-independent union and sum-normalized share."""
    bep, overflow, scour = np.asarray(values).T
    system = 1 - (1 - bep) * (1 - overflow) * (1 - scour)
    annual = [float(np.mean(x)) for x in (system, bep, overflow, scour)]
    return dict(
        system=annual[0],
        piping=annual[1],
        overflow=annual[2],
        scour=annual[3],
        share=annual[1] / sum(annual[1:]) if sum(annual[1:]) else None,
    )


def weighted_summary(groups: list, arrays: list) -> dict:
    """Weight each finite-population stratum, never each selected event equally."""
    parts = [summary(a) for a in arrays]
    out = {
        name: sum(g["weight"] * p[name] for g, p in zip(groups, parts))
        for name in ("system", "piping", "overflow", "scour")
    }
    total = out["piping"] + out["overflow"] + out["scour"]
    out["share"] = out["piping"] / total if total else 0.0
    return out


def bootstrap_events(groups: list, arrays: list, seed: int) -> np.ndarray:
    """Paired event bootstrap of the finite-ensemble integration subsample."""
    rng = np.random.default_rng(seed)
    boot = np.zeros((2000, 2, 5))
    for group, a in zip(groups, arrays):
        union = 1 - np.prod(1 - a, axis=2)
        vals = np.concatenate((union[..., None], a), axis=2)
        if group["population"] == len(a):
            boot[:, :, :4] += group["weight"] * vals.mean(axis=0)
        else:
            ids = rng.integers(len(a), size=(2000, len(a)))
            boot[:, :, :4] += group["weight"] * vals[ids].mean(axis=1)
    boot[:, :, 4] = np.divide(
        boot[:, :, 1],
        boot[:, :, 1:4].sum(axis=2),
        out=np.zeros((2000, 2)),
        where=boot[:, :, 1:4].sum(axis=2) > 0,
    )
    return boot


def shapes(data_repo: Path, kp: float, berm: bool, n: int) -> dict:
    """Paired actual-event versus canonical loading, with prescribed SST weights."""
    pop = population(data_repo, kp, berm, n)
    pop2 = population(data_repo, kp, berm, n * 2)
    seg = load_segment_inputs(
        REPO / "data/processed/uemura_segments/segment_inputs.csv"
    )
    seg = seg[("Tokachi", kp)]
    draws = draw_overflow(np.random.default_rng(SEED), seg, 10000)
    sc_draws = draw_scour(
        np.random.default_rng(SEED + 1),
        10000,
        k_conversion=SCOUR_K_CONVERSION_USACE,
    )
    result = dict(kp=kp, berm=berm, n=n, input_sha256=pop["input_sha256"])
    boot_by_climate = {}
    for scenario in ("historical", "plus4K"):
        recs, canonical, members, sha = records(data_repo, kp, scenario)
        groups = stratified_selection(members)
        arrays, event_rows = [], []
        for group in groups:
            vals = []
            for name in group["events"]:
                actual = recs[name]
                pinned = conditioning_record_for_level(
                    canonical, actual.peak, scenario=scenario
                )
                pair = []
                for rec in (pinned, actual):
                    st, tr = evaluate(pop, rec)
                    po = (
                        overflow_failure_fraction(rec.h, rec.native_dt, seg, draws)
                        if rec.peak > np.min(draws.crest_m_msl - draws.wl_err_m)
                        else 0.0
                    )
                    ps = scour_failure_fraction(rec.h, rec.native_dt, seg, sc_draws)
                    pair.append([float(tr.mean()), po, ps])
                vals.append(pair)
                event_rows.append(
                    dict(event=name, peak=actual.peak, probabilities=pair)
                )
            arrays.append(np.asarray(vals))
            print(kp, berm, scenario, group["stratum"], flush=True)
        estimates = {
            arm: weighted_summary(groups, [a[:, j] for a in arrays])
            for j, arm in enumerate(("canonical", "actual"))
        }
        boot = bootstrap_events(groups, arrays, SEED + 2 + (scenario == "plus4K"))
        keys = ("system", "piping", "overflow", "scour", "share")
        boot_by_climate[scenario] = boot
        checks = []
        for j, arm in enumerate(("canonical", "actual")):
            top = max(event_rows, key=lambda row: row["probabilities"][j][0])
            rec = recs[top["event"]]
            if j == 0:
                rec = conditioning_record_for_level(
                    canonical, rec.peak, scenario=scenario
                )
            st2, tr2 = evaluate(pop2, rec)
            checks.append(
                dict(
                    arm=arm,
                    event=top["event"],
                    n=2 * n,
                    p=float(tr2.mean()),
                    p_n=top["probabilities"][j][0],
                )
            )
        result[scenario] = dict(
            estimates=estimates,
            selection=groups,
            events=event_rows,
            ensemble_sha256=sha,
            n_checks=checks,
            intervals={
                arm: {
                    key: np.percentile(boot[:, j, k], [2.5, 97.5]).tolist()
                    for k, key in enumerate(keys)
                }
                for j, arm in enumerate(("canonical", "actual"))
            },
            displacement_ci={
                key: np.percentile(boot[:, 1, k] - boot[:, 0, k], [2.5, 97.5]).tolist()
                for k, key in enumerate(keys)
            },
        )
    ratio = boot_by_climate["plus4K"][:, :, 0] / boot_by_climate["historical"][:, :, 0]
    result["climate_ratio"] = {
        arm: dict(
            point=result["plus4K"]["estimates"][arm]["system"]
            / result["historical"]["estimates"][arm]["system"],
            interval=np.percentile(ratio[:, j], [2.5, 97.5]).tolist(),
        )
        for j, arm in enumerate(("canonical", "actual"))
    }
    result["climate_ratio_displacement_ci"] = np.percentile(
        ratio[:, 1] - ratio[:, 0], [2.5, 97.5]
    ).tolist()
    return result


def rating(data_repo: Path, kp: float, berm: bool, n: int, order: int) -> dict:
    """Direct additive error versus peak convolution on the full canonical grid."""
    pop = population(data_repo, kp, berm, n)
    recs, canonical, _, sha = records(data_repo, kp, "historical")
    grid = pop["grid"]
    z, weights = roots_hermitenorm(order)
    weights /= np.sqrt(2 * np.pi)
    offsets = -0.160 + 0.294 * z
    baseline = np.stack([pop["static"].mean(0), pop["transient"].mean(0)], axis=-1)
    direct = np.zeros_like(baseline)
    uniform = np.empty((order, len(grid), 2))
    for k, (offset, weight) in enumerate(zip(offsets, weights)):
        for i, level in enumerate(grid):
            rec = conditioning_record_for_level(canonical, level, scenario="historical")
            flags = evaluate(pop, rec, offset)
            uniform[k, i] = [f.mean() for f in flags]
        direct += weight * uniform[k]
        print(kp, berm, "rating", order, k, flush=True)
    # Production and backend gates at a shoulder and a high level.
    gates = []
    for i in (int(np.argmin(abs(baseline[:, 1] - 0.05))), len(grid) - 3):
        rec = conditioning_record_for_level(canonical, grid[i], scenario="historical")
        got = evaluate(pop, rec)
        ref = evaluate(pop, rec, backend="numpy")
        assert np.array_equal(got, ref)
        assert np.array_equal(got[0], pop["static"][:, i])
        assert np.array_equal(got[1], pop["transient"][:, i])
        # The algebraic toe device must equal shifting the entire record.
        shifted = replace(rec, h=rec.h + 0.294, peak=rec.peak + 0.294)
        assert np.array_equal(evaluate(pop, rec, 0.294), evaluate(pop, shifted))
        gates.append(float(grid[i]))
    result = dict(
        kp=kp,
        berm=berm,
        n=n,
        order=order,
        grid=grid.tolist(),
        baseline=baseline.tolist(),
        uniform=direct.tolist(),
        gates=gates,
        input_sha256=pop["input_sha256"],
        ensemble_sha256=sha,
        config_hash=pop["config_hash"],
    )
    np.savez_compressed(
        OUT / f"rating_arrays_{kp}_{berm}_{order}.npz",
        uniform=uniform,
        offsets=offsets,
        weights=weights,
    )
    for scenario in ("historical", "plus4K"):
        recs, _, _, _ = records(data_repo, kp, scenario)
        peaks = np.array([r.peak for r in recs.values()])
        annual = {}
        for j, branch in enumerate(("static", "transient")):
            base_curve = curve(grid, baseline[:, j])
            direct_p, clamped = curve(grid, direct[:, j]).evaluate(peaks)
            b, _ = base_curve.evaluate(peaks)
            conv = {}
            for q in (9, 17, 33):
                zs, ws = roots_hermitenorm(q)
                pp = np.stack(
                    [base_curve.evaluate(peaks - 0.160 + 0.294 * x)[0] for x in zs]
                )
                conv[str(q)] = float(np.mean(ws @ pp / np.sqrt(2 * np.pi)))
            annual[branch] = dict(
                baseline=float(b.mean()),
                uniform=float(direct_p.mean()),
                convolution=conv,
                above_grid_fraction=float(clamped.mean()),
                below_grid_fraction=float(np.mean(peaks < grid[0])),
            )
        result[scenario] = annual
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=("rating", "shapes"))
    parser.add_argument("--data-repo", type=Path, required=True)
    parser.add_argument("--kp", type=float, required=True)
    parser.add_argument("--berm", action="store_true")
    parser.add_argument("--n", type=int, default=8192)
    parser.add_argument("--order", type=int, default=9)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    tick = time.time()
    if args.part == "rating":
        result = rating(args.data_repo, args.kp, args.berm, args.n, args.order)
    else:
        result = shapes(args.data_repo, args.kp, args.berm, args.n)
    result["runtime_s"] = time.time() - tick
    result["backend"] = (
        "numba opt-in, 225 s; production-row flags checked by rating stage"
    )
    path = OUT / f"{args.part}_{args.kp}_{args.berm}_{args.order}.json"
    path.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(path, flush=True)


if __name__ == "__main__":
    main()
