"""What Pol's round-2 annotations change in the results (A19, A13, A35/A34).

Driver for three companion studies:

* ``docs/decisions/crest-attribution-study.md`` (part ``crest``): how much of
  every piping-only annual quantity rests on years whose peak exceeds the crest,
  and how the annual probability divides between piping and overflow when both
  are loaded in the same year, including a time-ordered split from pipe breach
  times and overflow failure times on the canonical flood.
* ``docs/decisions/drained-section-conditioning-study.md`` (part ``drained``):
  the as-if-undrained foundation at KP 58.8 and 60.0 under the prior, under the
  survival likelihood of the levee that actually stood in 2016 (measured berm,
  drain inert or relieving), and under the adopted as-if-undrained update.
* ``docs/decisions/seepage-length-lower-tail-study.md`` (part ``seepage``): the
  seepage-length prior truncated below, evaluated exactly by masking the
  persisted rows on their regenerated L.

Nothing is re-swept and no default, config, prior, kernel, persisted sweep,
posterior or production annual result changes. Every rebuilt quantity is gated
against the production artifact it must reproduce before an alternative is
reported. The time-ordered split re-runs the M7 kernel with trajectory storage
on failing rows only, gated bit for bit against M8's end state.

Usage (worktree root, main venv, ``PYTHONPATH=.``)::

    python scripts/results_annotations_study.py crest --results-root <main>/results
    python scripts/results_annotations_study.py drained --results-root ...
    python scripts/results_annotations_study.py seepage --results-root ...
    python scripts/results_annotations_study.py figures --results-root ...
    python scripts/results_annotations_study.py report
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


def _load_module(name: str):
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: Session 3's driver supplies the row bundles, the weighted M9 curve and the
#: production annualisation; through it the ADR-0055 driver supplies the
#: same-head flags and paired statistics. Imported, never restated.
ie = _load_module("initiation_evidence_2016_study")
tdf = ie.tdf

KPS = ie.KPS
DESIGN_HWL = ie.DESIGN_HWL
DESIGN_GRID = ie.DESIGN_GRID
R1 = ie.R1
SEED = 20261009
REPLICATES = 10_000

OUT_DIR = REPO / "results" / "results_annotations"
DECISIONS = REPO / "docs" / "decisions"
EVIDENCE = {
    "crest": DECISIONS / "crest-attribution-study.json",
    "adopted": DECISIONS / "drained-section-conditioning-adopted.json",
    "alternatives": DECISIONS / "drained-section-conditioning-alternatives.json",
    "drained": DECISIONS / "drained-section-conditioning-study.json",
    "seepage": DECISIONS / "seepage-length-lower-tail-study.json",
    "seepage_adopted": DECISIONS / "seepage-length-lower-tail-adopted.json",
}
#: Truncation points of the seepage-length prior, as fractions of its mean.
#: 0.85 is the shortest clean lidar station within 300 m of each resolvable
#: section over its local median (34/40, 36/42, 37/43 m, ADR-0047 JSON); 1.00 is
#: the definitional bound (no entry or exit inside the footprint).
TRUNCATIONS: tuple[float, ...] = (0.70, 0.80, 0.85, 0.90, 1.00)
#: Rows subsampled per stage for the pipe breach times (seeded).
BREACH_ROWS = 4000


def _label(kp: float) -> str:
    return ie._label(kp)


def _write_stage(part: str, payload: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"stage_{part}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def _read_stage(part: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / f"stage_{part}.json").read_text(encoding="utf-8"))


def _num(v) -> float:
    return 0.0 if v in ("", None) else float(v)


# --------------------------------------------------------------------------- #
# Production annualisation, gated                                              #
# --------------------------------------------------------------------------- #
class Annual:
    """The production Phase 3 pipeline, rebuilt and gated, with curve swaps."""

    def __init__(self, results_root: Path):
        self.unc, self.campaign = ie._campaign(results_root)
        self.cache_before = self.unc._dir_state(self.campaign.HAZARD_CACHE, "*.csv")
        self.context = self.unc.build_context(self.campaign)
        self.production = dict(self.context["bep_curves"])
        arms = {}
        for d70 in ("matrix", "bulk"):
            for source in ("prior", "posterior"):
                arms[self.unc._arm_key(d70, source)] = self.unc.annualise_arm(
                    self.campaign, self.context, d70, source
                )
        self.gate = self.unc.gate_one({k: v[0] for k, v in arms.items()})
        self.rows = {k: v[0] for k, v in arms.items()}
        self.per_event = {k: v[1] for k, v in arms.items()}
        self.scenarios = tuple(self.campaign.SCENARIOS)
        ids = [
            e.event_id
            for e in self.context["hazards"]["historical"][("Tokachi", 58.8)].events
        ]
        self.ids = {
            s: [
                e.event_id for e in self.context["hazards"][s][("Tokachi", 58.8)].events
            ]
            for s in self.scenarios
        }
        del ids

    def peaks(self, kp: float, scenario: str) -> NDArray[np.float64]:
        hz = self.context["hazards"][scenario][("Tokachi", kp)]
        return np.asarray(hz.peak_stages(), dtype=np.float64)

    def run(self, curves: dict[float, Any]):
        """Annualise with the matrix-posterior BEP curve replaced per section."""
        for kp, curve in curves.items():
            self.context["bep_curves"][(kp, "matrix", "posterior")] = curve
        try:
            rows, pe = self.unc.annualise_arm(
                self.campaign, self.context, "matrix", "posterior"
            )
        finally:
            for kp in KPS:
                self.context["bep_curves"][(kp, "matrix", "posterior")] = (
                    self.production[(kp, "matrix", "posterior")]
                )
        self.check_cache()
        # Surface-only segments must not move under a BEP swap.
        base = self.rows[self.unc._arm_key("matrix", "posterior")]
        kp_set = {round(k, 3) for k in KPS}
        for key, row in rows.items():
            if key[0] == "Tokachi" and round(key[1], 3) in kp_set:
                continue
            a = {k: v for k, v in row.items() if k != "bep_source"}
            b = {k: v for k, v in base[key].items() if k != "bep_source"}
            if a != b:
                raise SystemExit(f"surface-only segment changed under a swap: {key}")
        return rows, pe

    def check_cache(self) -> None:
        if (
            self.unc._dir_state(self.campaign.HAZARD_CACHE, "*.csv")
            != self.cache_before
        ):
            raise SystemExit("the hazard cache changed during the run; refusing")

    def multiplicities(self, scenario: str, replicates: int, rng):
        ids = self.ids[scenario]
        index, n_blocks, _ = self.unc.block_index(self.unc.block_labels(ids, "member"))
        strata = self.unc.stratum_columns(ids)
        mult = self.unc.draw_multiplicities_stratified(
            strata, n_blocks, replicates, rng
        )
        return index, n_blocks, mult, len(ids)

    def replicate(self, values: dict[str, NDArray], scenario: str, mult_pack):
        index, n_blocks, mult, n = mult_pack
        return self.unc.node_replicates(values, index, n_blocks, mult, n)


def _ci(x: NDArray) -> list[float]:
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return [float("nan"), float("nan")]
    return [float(v) for v in np.percentile(x, [2.5, 97.5])]


def _section_crests(kp: float) -> dict[str, float]:
    from system_integration.uemura_models import load_segment_inputs

    seg = load_segment_inputs(
        REPO / "data/processed/uemura_segments/segment_inputs.csv"
    )
    si = seg[("Tokachi", round(kp, 3))]
    return {
        "design_level_m": DESIGN_HWL[kp],
        "design_crest_m": si.crest_design_m_msl,
        "overflow_crest_mean_m": si.crest_design_m_msl + si.crest_err_mu_m,
        "overflow_crest_sd_m": si.crest_err_sigma_m,
        "rating_error_mean_m": si.wl_err_mu_m,
        "rating_error_sd_m": si.wl_err_sigma_m,
        "grid_attainable_max_m": ie.ATTAINABLE_MAX[kp],
    }


# --------------------------------------------------------------------------- #
# Part: crest (A19)                                                            #
# --------------------------------------------------------------------------- #
def _overflow_setup(kp: float):
    """The seeded overflow draws and canonical stage shape of one section.

    Reproduces ``generate_uemura_surface_curves.py`` exactly: the node index is
    the position in ``sorted(segment_inputs.items())`` and the draw stream is
    ``SeedSequence((SEED_ROOT, node_index, MECH_INDEX['overflow']))``.
    """
    from bep_reliability_engine.hydrographs import (
        build_hydrograph_record,
        load_rating_coefficients,
        normalize_stage_shape,
        rating_curve_path,
        read_discharge_ensemble,
        resolve_band_workbook,
    )
    from system_integration.uemura_models import draw_overflow, load_segment_inputs

    gen = _load_module("generate_uemura_surface_curves")

    inputs = load_segment_inputs(gen.SEGMENT_INPUTS)
    keys = [k for k, _ in sorted(inputs.items())]
    node_index = keys.index(("Tokachi", round(kp, 3)))
    seg = inputs[("Tokachi", round(kp, 3))]
    coeffs = load_rating_coefficients(rating_curve_path(REPO / "data/raw", "Tokachi"))
    a_kp, b_kp = coeffs[round(kp, 3)]
    _, proxied = gen.resolve_discharge_source_kp(kp)
    del proxied
    workbook = resolve_band_workbook(
        REPO / "data/raw", river="Tokachi", kp=kp, scenario="historical"
    )
    time_hours, members = read_discharge_ensemble(workbook)
    q = members[gen.CANONICAL_EVENT]
    record = build_hydrograph_record(
        time_hours,
        q,
        a_kp=a_kp,
        b_kp=b_kp,
        scenario="historical",
        event_id=gen.CANONICAL_EVENT,
        provenance={"kp": kp},
    )
    shape, h_base, _ = normalize_stage_shape(record.h)
    draws = draw_overflow(
        np.random.default_rng(
            np.random.SeedSequence(
                (gen.SEED_ROOT, node_index, gen.MECH_INDEX["overflow"])
            )
        ),
        seg,
        gen.N_MC,
    )
    return seg, draws, shape, float(h_base), float(record.native_dt), gen


def _overflow_times(level: float, seg, draws, shape, h_base, dt_s):
    """Failure fraction and per-draw failure times [s] (inf if no failure).

    The overflow model sums the damage of each hourly sample (Eq. 4); the time of
    failure is taken as the elapsed time of the sample at which the cumulative
    damage first exceeds the threshold, so its resolution is one hour.
    """
    from system_integration.uemura_models import (
        GRAVITY_MPS2,
        OVERFLOW_DAMAGE_THRESHOLD,
        OVERFLOW_FRICTION_F,
        overflow_failure_fraction,
    )

    h = (
        h_base + (level - h_base) * shape
        if level > h_base
        else np.full_like(shape, level)
    )
    wl = h[:, None] + draws.wl_err_m[None, :]
    depth = np.maximum(wl - draws.crest_m_msl[None, :], 0.0)
    q_ov = np.sqrt(GRAVITY_MPS2 * depth) * depth
    v_toe = (
        8.0 * GRAVITY_MPS2 * q_ov * np.sin(seg.slope_angle_rad) / OVERFLOW_FRICTION_F
    ) ** (1.0 / 3.0)
    dmg = np.maximum(0.0, v_toe**3 - draws.u_c_mps[None, :] ** 3) * dt_s
    cum = np.cumsum(dmg, axis=0)
    fail = cum[-1] > OVERFLOW_DAMAGE_THRESHOLD
    first = np.argmax(cum > OVERFLOW_DAMAGE_THRESHOLD, axis=0)
    t = np.where(fail, first * dt_s, np.inf)
    p = float(np.mean(fail))
    p_prod = overflow_failure_fraction(h, dt_s, seg, draws)
    if p != p_prod:
        raise SystemExit(f"overflow re-run {p} differs from the model {p_prod}")
    return p, t, h


def _pipe_breach_times(b, record, rows: NDArray[np.int64]):
    """Breach times [s] of the given rows under ``record`` (inf if none).

    Re-runs the M7 kernel with trajectory storage on the rows only, with the
    per-row inputs M8 computes for them; gate: the end states equal M8's.
    """
    from bep_reliability_engine import evaluator as ev
    from bep_reliability_engine.progression import integrate_progression
    from bep_reliability_engine.time_contract import validate_record

    config = b.run.config
    names = b.names
    theta = b.theta[rows]
    L = b.L[rows]
    diag = ev.evaluate_batch_diagnostics(
        theta,
        record,
        b.run.geometry,
        l_ini=0.0,
        seepage_length_samples=L,
        alpha_exponent=config.alpha_exponent,
        alpha_exponent_transient=config.alpha_exponent_transient,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        foreland_open=config.foreland_treatment == "open_entry",
        progression_backend="numpy",
        model_factor_samples=None,
        critical_length_factor=config.critical_length_factor,
        toe_gradient_relief_factor=config.toe_gradient_relief_factor,
        crack_resistance_factor=config.crack_resistance_factor,
        foreland_seepage_credit=config.foreland_seepage_credit,
    )
    z_toe = float(b.run.geometry["z_toe"])
    h_river = validate_record(record)[:-1]
    dt_s = float(record.native_dt)
    head = ev.InstantaneousHead(
        ev._gate_response_factor(diag.r_e, config.toe_gradient_relief_factor), z_toe
    )
    prog = integrate_progression(
        h_river,
        dt_s,
        head,
        z_toe,
        c_e=theta[:, names.index("C_e")],
        k_aq_mps=theta[:, names.index("k_aq")],
        d_bl_m=theta[:, names.index("D_bl")],
        gamma_bl_sub_knpm3=theta[:, names.index("gamma_bl_sub")],
        h_c_m=diag.H_c_transient,
        l_c_m=diag.l_c,
        seepage_length_m=L,
        l_ini_m=0.0,
        store_trajectory=True,
        crack_resistance_factor=config.crack_resistance_factor,
    )
    l_final = np.asarray(prog.l_final_m, dtype=np.float64)
    if not np.array_equal(l_final, diag.l_e_final):
        raise SystemExit("breach-time re-run end state differs from M8")
    traj = np.asarray(prog.l_trajectory_m, dtype=np.float64)
    if traj.shape[0] != h_river.size:
        traj = traj.T
    reached = traj >= L[None, :]
    any_r = reached.any(axis=0)
    first = np.argmax(reached, axis=0)
    t = np.where(any_r, (first + 1) * dt_s, np.inf)
    return t, diag.failure_trans


def _pi_first(t_p: NDArray, t_o: NDArray) -> float:
    """P(pipe first | both fail), independent draws; ties count one half."""
    t_p = np.sort(t_p[np.isfinite(t_p)])
    t_o = np.sort(t_o[np.isfinite(t_o)])
    if t_p.size == 0 or t_o.size == 0:
        return float("nan")
    less = np.searchsorted(t_o, t_p, side="right")  # t_o <= t_p
    lt = np.searchsorted(t_o, t_p, side="left")  # t_o < t_p
    ties = less - lt
    pipe_first = (t_o.size - less) + 0.5 * ties
    return float(pipe_first.sum() / (t_p.size * t_o.size))


def _time_order_section(b, kp: float, use_accept: bool, rng) -> list[dict[str, Any]]:
    """pi(h) at every grid stage where overflow fails, for one row bundle."""
    from bep_reliability_engine.run import conditioning_hydrographs_for_config

    seg, draws, shape, h_base, dt_o, _gen = _overflow_setup(kp)
    crest = _section_crests(kp)
    records = conditioning_hydrographs_for_config(b.run.config)
    # Clock alignment: both series start at the canonical window start.
    rec0 = records[-1]  # the top level: a full, non-flat waveform
    t_peak_pipe = float(rec0.t[int(np.argmax(rec0.h))] - rec0.t[0])
    t_peak_ovf = float(np.argmax(shape) * dt_o)
    if abs(t_peak_pipe - t_peak_ovf) > dt_o + 1e-9:
        raise SystemExit(f"{_label(kp)}: clocks differ {t_peak_pipe} {t_peak_ovf}")
    keep = b.accept if use_accept else np.ones(b.n, dtype=bool)
    levels = []
    for i, h in enumerate(b.grid):
        p_o, t_o, _ = _overflow_times(float(h), seg, draws, shape, h_base, dt_o)
        if p_o <= 0.0:
            continue
        fail_rows = np.nonzero(b.tran[:, i] & keep)[0]
        entry: dict[str, Any] = {
            "stage_m": float(h),
            "p_overflow": p_o,
            "n_pipe_failures": int(fail_rows.size),
            "n_rows": int(keep.sum()),
        }
        if fail_rows.size:
            take = (
                fail_rows
                if fail_rows.size <= BREACH_ROWS
                else np.sort(rng.choice(fail_rows, BREACH_ROWS, replace=False))
            )
            t_p, ftrans = _pipe_breach_times(b, records[i], take)
            if not np.all(ftrans) or not np.all(np.isfinite(t_p)):
                raise SystemExit(f"{_label(kp)} {h}: re-run lost a breach")
            entry["n_pipe_traced"] = int(take.size)
            entry["pi_pipe_first"] = _pi_first(t_p, t_o)
            entry["pi_overflow_shift_minus_1h"] = _pi_first(t_p, t_o - dt_o)
            entry["pi_overflow_shift_plus_1h"] = _pi_first(t_p, t_o + dt_o)
            entry["pipe_breach_h_quartiles"] = [
                float(x) for x in np.percentile(t_p / 3600.0, [25, 50, 75])
            ]
            fo = t_o[np.isfinite(t_o)]
            entry["overflow_fail_h_quartiles"] = [
                float(x) for x in np.percentile(fo / 3600.0, [25, 50, 75])
            ]
            entry["peak_time_h"] = t_peak_ovf / 3600.0
            above = np.nonzero(
                h_base + (h - h_base) * shape > crest["overflow_crest_mean_m"]
            )[0]
            entry["mean_crest_first_exceeded_h"] = (
                float(above[0] * dt_o / 3600.0) if above.size else None
            )
        levels.append(entry)
        print(
            f"  time order {b.config} {_label(kp)} {h:.2f}: "
            f"{entry.get('pi_pipe_first')}",
            flush=True,
        )
    return levels


def time_order_part(results_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    rng = np.random.default_rng(SEED)
    for kp in KPS:
        b = ie.Bundle(results_root, "undrained", kp)
        out[_label(kp)] = {
            "crests": _section_crests(kp),
            "levels": _time_order_section(b, kp, True, rng),
        }
    return out


def _pi_at(stages: NDArray, table: list[dict[str, Any]], key="pi_pipe_first"):
    pts = [(e["stage_m"], e[key]) for e in table if np.isfinite(e.get(key, np.nan))]
    if not pts:
        return np.full(stages.shape, 0.5)
    x, y = np.array(pts).T
    return np.interp(stages, x, y)


def crest_part(results_root: Path, replicates: int) -> dict[str, Any]:
    cached = OUT_DIR / "stage_time_order.json"
    if cached.is_file():
        order = _read_stage("time_order")
        print("  time order: reusing stage_time_order.json", flush=True)
    else:
        order = time_order_part(results_root)
        _write_stage("time_order", order)
    A = Annual(results_root)
    post = A.per_event[A.unc._arm_key("matrix", "posterior")]
    prior = A.per_event[A.unc._arm_key("matrix", "prior")]

    # Static (same-head) piping curves, prior and own update, annualised.
    bundles = {kp: ie.Bundle(results_root, "undrained", kp) for kp in KPS}
    static_pe = {}
    for name, wfun in (
        ("S_prior", lambda b: np.ones(b.n)),
        ("S_own", lambda b: b.same_head_survive.astype(np.float64)),
    ):
        curves = {
            kp: ie.weighted_curve(bundles[kp], wfun(bundles[kp]), name, static=True)
            for kp in KPS
        }
        static_pe[name] = A.run(curves)[1]

    rng = np.random.default_rng(A.unc.SEED)
    cells: dict[str, Any] = {}
    for scenario in A.scenarios:
        pack = A.multiplicities(scenario, replicates, rng)
        for kp in KPS:
            key = ("Tokachi", kp, scenario)
            crest = order[_label(kp)]["crests"]
            h = A.peaks(kp, scenario)
            pb = post[key]["bep"]
            po = post[key].get("overflow", np.zeros_like(pb))
            ps_prod = post[key]["__system__"]
            # The production system curve is composed on the stage grid and
            # interpolated at each peak, the marginals likewise; the union of
            # the interpolated marginals therefore differs from the interpolated
            # union by interpolation error only. Gate it, then attribute the
            # union of the marginals so every split sums exactly.
            ps = 1 - (1 - pb) * (1 - po)
            union_dev = (
                float(abs(ps.mean() / ps_prod.mean() - 1)) if ps_prod.sum() else 0.0
            )
            if union_dev > 5e-3:
                raise SystemExit(f"{key}: union of marginals departs {union_dev}")
            pi = _pi_at(h, order[_label(kp)]["levels"])
            pi_lo = _pi_at(h, order[_label(kp)]["levels"], "pi_overflow_shift_minus_1h")
            pi_hi = _pi_at(h, order[_label(kp)]["levels"], "pi_overflow_shift_plus_1h")
            over = pb * po
            attrib = {
                "reported_marginal": (pb, po),
                "overflow_first": (pb - over, po),
                "piping_first": (pb, po - over),
                "symmetric": (pb - over / 2, po - over / 2),
                "time_ordered": (pb - (1 - pi) * over, po - pi * over),
                "time_ordered_ovf_minus_1h": (
                    pb - (1 - pi_lo) * over,
                    po - pi_lo * over,
                ),
                "time_ordered_ovf_plus_1h": (
                    pb - (1 - pi_hi) * over,
                    po - pi_hi * over,
                ),
            }
            above_dc = h > crest["design_crest_m"]
            above_oc = h > crest["overflow_crest_mean_m"]
            attrib["truncate_design_crest"] = (np.where(above_dc, 0.0, pb), po)
            attrib["truncate_overflow_crest"] = (np.where(above_oc, 0.0, pb), po)
            values = {"__system__": ps}
            for name, (ab, ao) in attrib.items():
                values[f"{name}|b"] = ab
                values[f"{name}|o"] = ao
            reps = A.replicate(values, scenario, pack)
            entry: dict[str, Any] = {
                "n_years": int(h.size),
                "p_system": float(ps_prod.mean()),
                "p_union_of_marginals": float(ps.mean()),
                "union_interpolation_rel_dev": union_dev,
                "p_bep": float(pb.mean()),
                "p_overflow": float(po.mean()),
                "years_above_design_crest": int(above_dc.sum()),
                "years_above_overflow_crest": int(above_oc.sum()),
                "bep_share_from_above_design_crest": float(
                    pb[above_dc].sum() / pb.sum()
                ),
                "bep_share_from_above_overflow_crest": float(
                    pb[above_oc].sum() / pb.sum()
                ),
                "bep_share_from_above_design_level": float(
                    pb[h > DESIGN_HWL[kp]].sum() / pb.sum()
                ),
                "bep_prior_share_from_above_overflow_crest": float(
                    prior[key]["bep"][above_oc].sum() / prior[key]["bep"].sum()
                ),
                "max_peak_m": float(h.max()),
                "attributions": {},
            }
            for name, (ab, ao) in attrib.items():
                tot = ab + ao
                if name.startswith("truncate") or name == "reported_marginal":
                    denom = tot
                else:
                    if not np.allclose(tot, ps, rtol=0, atol=1e-14):
                        raise SystemExit(f"{key} {name}: does not sum to the system")
                    denom = ps
                rb, ro = reps[f"{name}|b"], reps[f"{name}|o"]
                with np.errstate(divide="ignore", invalid="ignore"):
                    share_r = rb / (rb + ro)
                Ab, Ao = float(ab.mean()), float(ao.mean())
                entry["attributions"][name] = {
                    "p_bep_attributed": Ab,
                    "p_overflow_attributed": Ao,
                    "bep_share": Ab / float(denom.mean()) if denom.sum() > 0 else None,
                    "bep_share_ci95": _ci(share_r),
                    "fraction_replicates_piping_leads": float(np.mean(rb > ro)),
                }
            # Piping-only quantities with years above the crest removed.
            for tag, mask in (("design_crest", above_dc), ("overflow_crest", above_oc)):
                keep = ~mask
                sp = static_pe["S_prior"][key]["bep"]
                so = static_pe["S_own"][key]["bep"]
                tp = prior[key]["bep"]
                entry[f"without_years_above_{tag}"] = {
                    "p_bep_posterior": float(pb[keep].sum() / h.size),
                    "annual_S_over_T_prior": (
                        float(sp[keep].sum() / tp[keep].sum())
                        if tp[keep].sum() > 0
                        else None
                    ),
                    "annual_S_over_T_own_update": (
                        float(so[keep].sum() / pb[keep].sum())
                        if pb[keep].sum() > 0
                        else None
                    ),
                }
            entry["annual_S_over_T_prior"] = float(
                static_pe["S_prior"][key]["bep"].mean() / prior[key]["bep"].mean()
            )
            entry["annual_S_over_T_own_update"] = float(
                static_pe["S_own"][key]["bep"].mean() / pb.mean()
            )
            entry["static_prior_share_from_above_overflow_crest"] = float(
                static_pe["S_prior"][key]["bep"][above_oc].sum()
                / static_pe["S_prior"][key]["bep"].sum()
            )
            cells[f"{scenario} {_label(kp)}"] = entry
    # Piping climate ratios with and without the above-crest years.
    climate: dict[str, Any] = {}
    for kp in KPS:
        hk, wk = ("historical", _label(kp)), ("+4K", _label(kp))
        h_c = cells[f"historical {_label(kp)}"]
        w_c = cells[f"+4K {_label(kp)}"]
        climate[_label(kp)] = {
            "bep_ratio": w_c["p_bep"] / h_c["p_bep"],
            "system_ratio": w_c["p_system"] / h_c["p_system"],
            "bep_ratio_without_above_overflow_crest": (
                w_c["without_years_above_overflow_crest"]["p_bep_posterior"]
                / h_c["without_years_above_overflow_crest"]["p_bep_posterior"]
            ),
            "bep_ratio_without_above_design_crest": (
                w_c["without_years_above_design_crest"]["p_bep_posterior"]
                / h_c["without_years_above_design_crest"]["p_bep_posterior"]
            ),
        }
        del hk, wk
    A.check_cache()
    return {
        "gates": {
            "production_table": A.gate,
            "union_of_marginals_within_0.5pct_of_system": True,
            "every_attribution_sums_to_system": True,
            "breach_rerun_end_state_equals_M8": True,
            "overflow_rerun_equals_model": True,
            "hazard_cache_unchanged": True,
        },
        "replicates": replicates,
        "time_order": order,
        "cells": cells,
        "climate": climate,
    }


# --------------------------------------------------------------------------- #
# Part: adopted (ADR-0056 and ADR-0057)                                        #
# --------------------------------------------------------------------------- #
#: ADR-0056: the drained sections' as-if-undrained foundation is not conditioned
#: on the 2016 survival of a levee that had berms and drains.
UNCONDITIONED = (58.8, 60.0)
#: Table 7.3 readings at the drained sections, all unconditioned.
READINGS = (
    ("as_if_undrained", "undrained"),
    ("berm", "berm"),
    ("berm_relief_80pct", "berm_relief_80pct"),
)


def _first_breach(pb, po, pi):
    """(piping, overflow) attributed per year; sums to the two-branch union."""
    over = pb * po
    return pb - (1.0 - pi) * over, po - pi * over


def _strata_quantities(rh: dict, rw: dict) -> dict[str, NDArray]:
    """Two-stratum terms per paired replicate (historical, warming)."""
    w, pl, ps = rh["w_inside"], rh["p_inside"], rh["p_outside"]
    w2, pl2, ps2 = rw["w_inside"], rw["p_inside"], rw["p_outside"]
    p00 = w * pl + (1 - w) * ps
    p11 = w2 * pl2 + (1 - w2) * ps2
    p10 = w2 * pl + (1 - w2) * ps
    p01 = w * pl2 + (1 - w) * ps2
    with np.errstate(divide="ignore", invalid="ignore"):
        lnR = np.log(p11 / p00)
        freq = 0.5 * (np.log(p10 / p00) + np.log(p11 / p01))
        return {
            "w_long_hist": w,
            "w_long_warm": w2,
            "p_long_hist": pl,
            "p_long_warm": pl2,
            "p_short_hist": ps,
            "p_short_warm": ps2,
            "R_long": (w2 * pl2) / (w * pl),
            "R_short": ((1 - w2) * ps2) / ((1 - w) * ps),
            "freq_share_first": np.log(p10 / p00) / lnR,
            "freq_share_last": np.log(p11 / p01) / lnR,
            "share_long_hist": w * pl / p00,
            "share_long_warm": w2 * pl2 / p11,
            "freq_factor": w2 / w,
            "sev_long": pl2 / pl,
            "sev_short": ps2 / ps,
            "ratio": p11 / p00,
            "freq_share_lnR": freq / lnR,
            "concentration_hist": pl / ps,
            "concentration_warm": pl2 / ps2,
        }


def adopted_part(results_root: Path, replicates: int) -> dict[str, Any]:
    clim = _load_module("climate_attribution_decomposition")
    A = Annual(results_root)
    unc = A.unc
    prior_key = unc._arm_key("matrix", "prior")
    post_key = unc._arm_key("matrix", "posterior")
    curves = {
        kp: A.production[
            (kp, "matrix", "prior" if kp in UNCONDITIONED else "posterior")
        ]
        for kp in KPS
    }
    rows, pe = A.run(curves)
    # Gate: each section's rows equal the production row of its arm.
    for kp in KPS:
        arm = prior_key if kp in UNCONDITIONED else post_key
        for s in A.scenarios:
            mine, base = rows[("Tokachi", kp, s)], A.rows[arm][("Tokachi", kp, s)]
            for f, v in base.items():
                if f != "bep_source" and str(mine[f]) != str(v):
                    raise SystemExit(f"adopted arm differs at {kp} {s} {f}")

    # First-breach split: pi(h) per section, rows of the adopted conditioning.
    cached = OUT_DIR / "stage_time_order_adopted.json"
    if cached.is_file():
        order = _read_stage("time_order_adopted")
    else:
        rng = np.random.default_rng(SEED + 1)
        order = {}
        for kp in KPS:
            b = ie.Bundle(results_root, "undrained", kp)
            order[_label(kp)] = _time_order_section(b, kp, kp not in UNCONDITIONED, rng)
        for cfg in ("berm", "berm_relief_80pct"):
            for kp in UNCONDITIONED:
                b = ie.Bundle(results_root, cfg, kp)
                order[f"{cfg} {_label(kp)}"] = _time_order_section(b, kp, False, rng)
        _write_stage("time_order_adopted", order)

    rng = np.random.default_rng(unc.SEED)
    packs = {s: A.multiplicities(s, replicates, rng) for s in A.scenarios}
    table: dict[str, Any] = {}
    reps_sys: dict[tuple[str, float], NDArray] = {}
    for scenario in A.scenarios:
        for kp in KPS:
            key = ("Tokachi", kp, scenario)
            v = pe[key]
            h = A.peaks(kp, scenario)
            pb = v["bep"]
            po = v.get("overflow", np.zeros_like(pb))
            pi = _pi_at(h, order[_label(kp)])
            ab, ao = _first_breach(pb, po, pi)
            vals = {
                "__system__": v["__system__"],
                "union": 1 - (1 - pb) * (1 - po),
                "bep": pb,
                "overflow": po,
                "fb_bep": ab,
                "fb_ovf": ao,
            }
            r = A.replicate(vals, scenario, packs[scenario])
            reps_sys[(scenario, kp)] = r["__system__"]
            row = rows[key]
            with np.errstate(divide="ignore", invalid="ignore"):
                fb_share_r = r["fb_bep"] / (r["fb_bep"] + r["fb_ovf"])
                sum_share_r = r["bep"] / (r["bep"] + r["overflow"])
            tot = float(ab.mean() + ao.mean())
            table[f"{scenario} {_label(kp)}"] = {
                "p_system": _num(row["p_annual_system"]),
                "system_ci95": _ci(r["__system__"]),
                "p_bep": float(pb.mean()),
                "p_overflow": float(po.mean()),
                "first_breach_bep": float(ab.mean()),
                "first_breach_overflow": float(ao.mean()),
                "first_breach_share_bep": float(ab.mean() / tot) if tot > 0 else None,
                "first_breach_share_ci95": _ci(fb_share_r),
                "first_breach_piping_leads_fraction": float(
                    np.mean(r["fb_bep"] > r["fb_ovf"])
                ),
                "summed_share_bep": (
                    None if row["share_bep"] in ("", None) else float(row["share_bep"])
                ),
                "summed_share_ci95": _ci(sum_share_r),
                "sum_over_union": (
                    float((pb.mean() + po.mean()) / vals["union"].mean())
                    if vals["union"].sum() > 0
                    else None
                ),
                "bep_share_from_above_design_level": float(
                    pb[h > DESIGN_HWL[kp]].sum() / pb.sum()
                ),
                "system_share_from_above_design_level": float(
                    v["__system__"][h > DESIGN_HWL[kp]].sum() / v["__system__"].sum()
                ),
                "bep_weighted_peak_above_design_m": float(
                    (pb * h).sum() / pb.sum() - DESIGN_HWL[kp]
                ),
                "bep_share_from_above_2016_peak": float(
                    pb[h > ie.PEAK_2016[kp]].sum() / pb.sum()
                ),
            }
    for kp in KPS:
        rr = unc.ratio_series(reps_sys[("historical", kp)], reps_sys[("+4K", kp)])
        hcell = table[f"historical {_label(kp)}"]
        wcell = table[f"+4K {_label(kp)}"]
        hcell["climate_ratio"] = wcell["p_system"] / hcell["p_system"]
        hcell["climate_ratio_ci95"] = _ci(rr)
        hcell["bep_climate_ratio"] = wcell["p_bep"] / hcell["p_bep"]
    # Rank among the four (and the fraction of replicates holding it).
    for scenario in A.scenarios:
        stack = np.column_stack([reps_sys[(scenario, kp)] for kp in KPS])
        ranks = (-stack).argsort(axis=1).argsort(axis=1) + 1
        point = np.array([table[f"{scenario} {_label(kp)}"]["p_system"] for kp in KPS])
        prank = (-point).argsort().argsort() + 1
        for j, kp in enumerate(KPS):
            c = table[f"{scenario} {_label(kp)}"]
            c["rank_of_four"] = int(prank[j])
            c["rank_replicate_share"] = float(np.mean(ranks[:, j] == prank[j]))
    # Reach-wide rank of every node (114) and consequence-section maxima.
    reach: dict[str, Any] = {}
    for scenario in A.scenarios:
        allrows = [
            (r["river"], float(r["kp"]), _num(r["p_annual_system"]), r["section_id"])
            for (_riv, _kp, sc), r in rows.items()
            if sc == scenario
        ]
        allrows.sort(key=lambda x: -x[2])
        ranks_of = {}
        for kp in KPS:
            ranks_of[_label(kp)] = 1 + next(
                i
                for i, x in enumerate(allrows)
                if x[0] == "Tokachi" and abs(x[1] - kp) < 1e-9
            )
        secmax: dict[str, float] = {}
        for _riv, _kp, p, sid in allrows:
            if sid:
                secmax[sid] = max(secmax.get(sid, 0.0), p)
        reach[scenario] = {
            "top": [[a, b, c] for a, b, c, _ in allrows[:20]],
            "rank_of_sections": ranks_of,
            "section_maxima": secmax,
        }

    # Sixty-year non-breach check (thesis 8.3): composed historical piping.
    from scipy.stats import beta as _beta_dist

    ph = np.array([table[f"historical {_label(kp)}"]["p_bep"] for kp in KPS])
    composed = float(1 - np.prod(1 - ph))
    exclusion = float(_beta_dist.ppf(0.95, 1, 60))
    sixty = {
        "composed_annual_piping": composed,
        "expected_failures_60yr": 60 * composed,
        "p_none_60yr": float((1 - composed) ** 60),
        "exclusion_limit_95": exclusion,
        "exclusion_over_composed": exclusion / composed,
    }

    # Two-stratum decomposition (thesis Table 7.5 lower block, 7.5.2 text).
    strata: dict[str, Any] = {}
    stratifiers = {st["name"]: st for st in unc.STRATIFIERS}
    for kp in KPS:
        node = ("Tokachi", round(kp, 3))
        for name in ("duration", "compound"):
            pred = stratifiers[name]["predicate"]
            reps_pair = {}
            point_pair = {}
            occ = {}
            for scenario in A.scenarios:
                hz = A.context["hazards"][scenario][node]
                mask = np.asarray([pred(e) for e in hz.events], dtype=bool)
                vals = pe[("Tokachi", kp, scenario)]["__system__"]
                index, n_blocks, mult, _n = packs[scenario]
                reps_pair[scenario] = clim.replicate_strata(
                    vals, mask, index, n_blocks, mult, unc
                )
                point_pair[scenario] = {
                    "w_inside": np.array([mask.mean()]),
                    "p_inside": np.array([vals[mask].mean() if mask.any() else np.nan]),
                    "p_outside": np.array([vals[~mask].mean()]),
                    "n_inside": int(mask.sum()),
                }
                occ[scenario] = unc.stratum_occupancy(A.ids[scenario], mask)
            pt = _strata_quantities(point_pair["historical"], point_pair["+4K"])
            rq = _strata_quantities(reps_pair["historical"], reps_pair["+4K"])
            strata[f"{_label(kp)} {name}"] = {
                "n_inside": {s: point_pair[s]["n_inside"] for s in A.scenarios},
                "clears_floor": {s: bool(occ[s]["clears_floor"]) for s in A.scenarios},
                **{k: {"point": float(pt[k][0]), "ci95": _ci(rq[k])} for k in pt},
            }

    # The six warming patterns' own annual values, and what resampling them
    # (pooled over pattern blocks) would do to the stratified interval.
    patterns = unc.structural_pattern_spread(pe, A.ids, A.campaign)
    widening: dict[str, Any] = {}
    sst_labels = unc.block_labels(A.ids["+4K"], "sst")
    sst_index, sst_blocks, _ = unc.block_index(sst_labels)
    sst_mult = unc.draw_multiplicities(sst_blocks, replicates, rng)
    for kp in KPS:
        v = pe[("Tokachi", kp, "+4K")]["__system__"]
        point = float(v.mean())
        strat = reps_sys[("+4K", kp)]
        pooled = unc.node_replicates(
            {"s": v}, sst_index, sst_blocks, sst_mult, len(A.ids["+4K"])
        )["s"]
        lo_s, hi_s = np.percentile(strat, [2.5, 97.5])
        lo_p, hi_p = np.percentile(pooled, [2.5, 97.5])
        widening[_label(kp)] = {
            "stratified_relative_half_width": float((hi_s - lo_s) / 2 / point),
            "patterns_resampled_relative_half_width": float((hi_p - lo_p) / 2 / point),
            "factor": float((hi_p - lo_p) / (hi_s - lo_s)),
        }

    # Table 7.3: the drained sections under three readings, all unconditioned.
    drained: dict[str, Any] = {}
    for reading, cfg in READINGS:
        swap = dict(curves)
        for kp in UNCONDITIONED:
            if cfg == "undrained":
                swap[kp] = A.production[(kp, "matrix", "prior")]
            else:
                b = ie.Bundle(results_root, cfg, kp)
                swap[kp] = ie.weighted_curve(b, np.ones(b.n), f"A13 {reading}")
        r_rows, r_pe = A.run(swap)
        r_reps: dict[tuple[str, float], NDArray] = {}
        for scenario in A.scenarios:
            for kp in KPS:
                v = r_pe[("Tokachi", kp, scenario)]
                r_reps[(scenario, kp)] = A.replicate(
                    {"__system__": v["__system__"]}, scenario, packs[scenario]
                )["__system__"]
        for scenario in A.scenarios:
            point = np.array(
                [
                    _num(r_rows[("Tokachi", kp, scenario)]["p_annual_system"])
                    for kp in KPS
                ]
            )
            prank = (-point).argsort().argsort() + 1
            stack = np.column_stack([r_reps[(scenario, kp)] for kp in KPS])
            ranks = (-stack).argsort(axis=1).argsort(axis=1) + 1
            for j, kp in enumerate(KPS):
                if kp not in UNCONDITIONED:
                    continue
                v = r_pe[("Tokachi", kp, scenario)]
                h = A.peaks(kp, scenario)
                pb = v["bep"]
                po = v.get("overflow", np.zeros_like(pb))
                tab = (
                    order[_label(kp)]
                    if cfg == "undrained"
                    else order[f"{cfg} {_label(kp)}"]
                )
                ab, ao = _first_breach(pb, po, _pi_at(h, tab))
                tot = float(ab.mean() + ao.mean())
                row = r_rows[("Tokachi", kp, scenario)]
                drained[f"{reading} {scenario} {_label(kp)}"] = {
                    "p_system": float(point[j]),
                    "system_ci95": _ci(r_reps[(scenario, kp)]),
                    "p_bep": float(pb.mean()),
                    "p_overflow": float(po.mean()),
                    "first_breach_share_bep": float(ab.mean() / tot) if tot else None,
                    "summed_share_bep": (
                        None
                        if row["share_bep"] in ("", None)
                        else float(row["share_bep"])
                    ),
                    "bep_clamped_above_grid": row["bep_clamped_above_grid"],
                    "rank_of_four": int(prank[j]),
                    "rank_replicate_share": float(np.mean(ranks[:, j] == prank[j])),
                }
        for kp in UNCONDITIONED:
            h_ = drained[f"{reading} historical {_label(kp)}"]
            w_ = drained[f"{reading} +4K {_label(kp)}"]
            rr = unc.ratio_series(r_reps[("historical", kp)], r_reps[("+4K", kp)])
            h_["climate_ratio"] = (
                w_["p_system"] / h_["p_system"] if h_["p_system"] else None
            )
            h_["climate_ratio_ci95"] = _ci(rr)
        print(f"  adopted reading {reading} done", flush=True)
    A.check_cache()
    return {
        "definition": {
            "piping_branch": "transient; updated on the 2016 survival at KP 57.4 "
            "and 62.0, unconditioned at KP 58.8 and 60.0 (ADR-0056)",
            "share": "first-breach split of the two-branch union (ADR-0057)",
        },
        "gates": {
            "production_table": A.gate,
            "adopted_rows_equal_production_arm_rows": True,
            "hazard_cache_unchanged": True,
        },
        "replicates": replicates,
        "time_order": order,
        "table": table,
        "reach": reach,
        "sixty_year_check": sixty,
        "strata": strata,
        "pattern_spread": patterns,
        "pattern_resampling_widening": widening,
        "drained_readings": drained,
    }


# --------------------------------------------------------------------------- #
# Part: alternatives (thesis Table 7.2 under ADR-0056)                         #
# --------------------------------------------------------------------------- #
def _cond_cells(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    d = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for sec, by in d["sections"].items():
        for scen, cell in by.items():
            if not isinstance(cell, dict) or "baseline" not in cell:
                continue
            out[(sec, scen)] = cell
    return out


def _foreland_cells(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {(c["section"], c["scenario"]): c for c in d["sections"]}


def alternatives_part(results_root: Path, replicates: int) -> dict[str, Any]:
    """Alternative-reading shares and spans with the adopted conditioning.

    Every value is read from committed evidence: the prior side of each
    companion at the drained sections (ADR-0056), the posterior side at KP 57.4
    and 62.0. Gate: each side's baseline equals the production row of its arm.
    """
    del replicates
    import csv

    with open(
        results_root / "system_integration/phase3/rq4_annual.csv",
        encoding="utf-8",
        newline="",
    ) as handle:
        prod = list(csv.DictReader(handle))

    def prow(kp, scen, d70, source, lam=250.0):
        for r in prod:
            if (
                r["river"] == "Tokachi"
                and abs(float(r["kp"]) - kp) < 1e-9
                and r["scenario"] == scen
                and r["d70"] == d70
                and r["bep_source"] == source
                and float(r["lambda_ac_m"]) == lam
                and r["surface_variant"] == "primary"
            ):
                return r
        raise KeyError((kp, scen, d70, source, lam))

    sides = {
        "prior": {
            "matrix": _cond_cells(
                DECISIONS / "conductivity-bracket-annualisation.json"
            ),
            "bulk": _cond_cells(
                DECISIONS / "conductivity-bracket-annualisation-bulk.json"
            ),
            "foreland": _foreland_cells(
                DECISIONS / "adr0052-foreland-credit-annualisation.json"
            ),
        },
        "posterior": {
            "matrix": _cond_cells(
                DECISIONS / "conductivity-bracket-posterior-side.json"
            ),
            "bulk": _cond_cells(
                DECISIONS / "conductivity-bracket-posterior-side-bulk.json"
            ),
            "foreland": _foreland_cells(
                DECISIONS / "adr0052-foreland-credit-annualisation-posterior.json"
            ),
        },
    }
    out: dict[str, Any] = {}
    for kp in KPS:
        side = "prior" if kp in UNCONDITIONED else "posterior"
        sec = _label(kp)
        for scen in ("historical", "+4K"):
            m = sides[side]["matrix"][(sec, scen)]
            bk = sides[side]["bulk"][(sec, scen)]
            fl = sides[side]["foreland"][(sec, scen)]
            base = prow(kp, scen, "matrix", side)
            bbase = prow(kp, scen, "bulk", side)
            for got, want in (
                (m["baseline"]["p_annual_system"], base["p_annual_system"]),
                (fl["baseline"]["p_annual_system"], base["p_annual_system"]),
                (bk["baseline"]["p_annual_system"], bbase["p_annual_system"]),
            ):
                if abs(float(got) / float(want) - 1) > 1e-12:
                    raise SystemExit(f"{sec} {scen} {side}: baseline differs")
            arms = {
                "matrix": float(base["share_bep"]) if base["share_bep"] else None,
                "bulk": float(bbase["share_bep"]) if bbase["share_bep"] else None,
            }
            for name in ("k_aq_field_geomean", "k_aq_field_toe", "k_aq_regional_upper"):
                a = m["arms"][name]
                arms[name] = a["share_bep"] if a["p_annual_system"] > 0 else None
            ub = bk["arms"]["k_aq_regional_upper"]
            arms["bulk_upper"] = ub["share_bep"] if ub["p_annual_system"] > 0 else None
            for name in ("credit_half", "credit_full"):
                a = fl["arms"][name]
                arms[name] = a["share_bep"] if a["p_annual_system"] > 0 else None
            systems = [m["baseline"]["p_annual_system"]] + [
                m["arms"][n]["p_annual_system"]
                for n in ("k_aq_field_geomean", "k_aq_field_toe", "k_aq_regional_upper")
            ]
            positive = [x for x in systems if x > 0]
            systems_arm = {
                "matrix": float(base["p_annual_system"]),
                "bulk": float(bbase["p_annual_system"]),
                **{
                    n: m["arms"][n]["p_annual_system"]
                    for n in (
                        "k_aq_field_geomean",
                        "k_aq_field_toe",
                        "k_aq_regional_upper",
                    )
                },
                "bulk_upper": ub["p_annual_system"],
            }
            out[f"{scen} {sec}"] = {
                "side": side,
                "system_by_arm": systems_arm,
                "shares_summed": arms,
                "clamped": {
                    "bulk": bbase["bep_clamped_above_grid"],
                    "field": m["arms"]["k_aq_field_geomean"]["coverage_system"][
                        "lower_bound_clamp"
                    ],
                },
                "conductivity_span_system": (
                    max(positive) / min(positive)
                    if len(positive) == len(systems)
                    else None
                ),
                "foreland_full_system_ratio": fl["arms"]["credit_full"][
                    "system_ratio_to_baseline"
                ],
                "foreland_half_system_ratio": fl["arms"]["credit_half"][
                    "system_ratio_to_baseline"
                ],
                "bulk_over_matrix_system": float(bbase["p_annual_system"])
                / float(base["p_annual_system"]),
            }
    for kp in KPS:
        h_ = out[f"historical {_label(kp)}"]["system_by_arm"]
        w_ = out[f"+4K {_label(kp)}"]["system_by_arm"]
        out[f"historical {_label(kp)}"]["climate_ratio_by_arm"] = {
            n: (w_[n] / h_[n] if h_[n] > 0 else None) for n in h_
        }
    # The 40 m and 100 m correlation-length factors on the adopted rows,
    # recomposed (production carries the bracket for the posterior arm only;
    # gate: with the posterior swapped back in, its rows are reproduced).
    A = Annual(results_root)
    unc = A.unc
    adopted_curves = {
        kp: A.production[
            (kp, "matrix", "prior" if kp in UNCONDITIONED else "posterior")
        ]
        for kp in KPS
    }
    lam: dict[str, Any] = {}
    base_rows = A.run(adopted_curves)[0]
    saved = unc.LAMBDA_AC_M
    try:
        for x in (100.0, 40.0):
            unc.LAMBDA_AC_M = x
            post_rows, _ = unc.annualise_arm(
                A.campaign, A.context, "matrix", "posterior"
            )
            for kp in KPS:
                for scen in ("historical", "+4K"):
                    want = prow(kp, scen, "matrix", "posterior", x)
                    got = post_rows[("Tokachi", kp, scen)]
                    if str(got["p_annual_system"]) != want["p_annual_system"]:
                        raise SystemExit(
                            f"lambda {x} posterior row differs {kp} {scen}"
                        )
            for kp, curve in adopted_curves.items():
                A.context["bep_curves"][(kp, "matrix", "posterior")] = curve
            rows_x, _ = unc.annualise_arm(A.campaign, A.context, "matrix", "posterior")
            for kp in KPS:
                A.context["bep_curves"][(kp, "matrix", "posterior")] = A.production[
                    (kp, "matrix", "posterior")
                ]
                for scen in ("historical", "+4K"):
                    b = _num(base_rows[("Tokachi", kp, scen)]["p_annual_system"])
                    v = _num(rows_x[("Tokachi", kp, scen)]["p_annual_system"])
                    lam.setdefault(f"{scen} {_label(kp)}", {})[f"{x:g}"] = v / b
                    if x == 40.0:
                        r = rows_x[("Tokachi", kp, scen)]
                        lam[f"{scen} {_label(kp)}"]["share_bep_40"] = (
                            None
                            if r["share_bep"] in ("", None)
                            else float(r["share_bep"])
                        )
    finally:
        unc.LAMBDA_AC_M = saved
    A.check_cache()
    return {"cells": out, "lambda_ac_factors": lam}


# --------------------------------------------------------------------------- #
# Part: drained (A13)                                                          #
# --------------------------------------------------------------------------- #
DRAINED = (58.8, 60.0)
LIKELIHOODS: tuple[tuple[str, str | None], ...] = (
    ("prior", None),
    ("berm_inert", "berm"),
    ("berm_relief_40pct", "berm_relief_40pct"),
    ("berm_relief_60pct", "berm_relief_60pct"),
    ("berm_relief_80pct", "berm_relief_80pct"),
    ("as_if_undrained", "undrained"),
)


def _aligned(u, b) -> None:
    """Gate: a configuration bundle carries the adopted rows."""
    if not np.array_equal(u.theta, b.theta):
        raise SystemExit(f"{b.config} {_label(b.kp)}: theta differs from adopted")
    ratio = b.L / u.L
    if not np.allclose(ratio, ratio[0], rtol=1e-12, atol=0):
        raise SystemExit(f"{b.config} {_label(b.kp)}: L not a scaled copy")


def _means(b, w: NDArray) -> dict[str, float]:
    out = {}
    for name in ("k_aq", "C_e", "d_70", "D_bl"):
        x = b.theta[:, b.names.index(name)]
        out[name] = float((w * x).sum() / w.sum())
    out["L"] = float((w * b.L).sum() / w.sum())
    return out


def drained_part(results_root: Path, replicates: int) -> dict[str, Any]:
    A = Annual(results_root)
    adopted = {kp: ie.Bundle(results_root, "undrained", kp) for kp in KPS}
    configs = {
        (cfg, kp): ie.Bundle(results_root, cfg, kp)
        for _, cfg in LIKELIHOODS
        if cfg not in (None, "undrained")
        for kp in DRAINED
    }
    for (cfg, kp), b in configs.items():
        _aligned(adopted[kp], b)

    per_flood: dict[str, Any] = {}
    weights: dict[tuple[str, float], NDArray] = {}
    for name, cfg in LIKELIHOODS:
        for kp in DRAINED:
            u = adopted[kp]
            if cfg is None:
                w, ws = np.ones(u.n), np.ones(u.n)
            elif cfg == "undrained":
                w, ws = u.accept.astype(float), u.same_head_survive.astype(float)
            else:
                b = configs[(cfg, kp)]
                w, ws = b.accept.astype(float), b.same_head_survive.astype(float)
            weights[(name, kp)] = w
            i = int(np.argmin(np.abs(u.grid - DESIGN_GRID[kp])))
            pt = ie.weighted_p(u.tran, w)[i]
            ps = ie.weighted_p(u.c3b, ws)[i]
            pts = ie.weighted_p(u.c3b, w)[i]
            per_flood[f"{name} {_label(kp)}"] = {
                "rejected_pct": float(100 * (1 - w.mean())),
                "rejected_rows": int(np.sum(w == 0)),
                "static_rejected_pct": float(100 * (1 - ws.mean())),
                "likelihood_ratio": float(w.mean() / ws.mean()),
                "means_retained": _means(u, w),
                "design_grid_stage_m": float(u.grid[i]),
                "p_trans_design": float(pt),
                "p_static_own_update_design": float(ps),
                "p_static_on_transient_set_design": float(pts),
            }
    prior_means = {
        _label(kp): _means(adopted[kp], np.ones(adopted[kp].n)) for kp in KPS
    }

    # Annual: each conditioning at the drained sections, production elsewhere.
    arms_pe: dict[str, Any] = {}
    arms_rows: dict[str, Any] = {}
    static_pe: dict[str, Any] = {}
    for name, cfg in LIKELIHOODS:
        curves = {
            kp: ie.weighted_curve(adopted[kp], weights[(name, kp)], f"A13 {name}")
            for kp in DRAINED
        }
        arms_rows[name], arms_pe[name] = A.run(curves)
        if cfg is None:
            ws = {kp: np.ones(adopted[kp].n) for kp in DRAINED}
        elif cfg == "undrained":
            ws = {kp: adopted[kp].same_head_survive.astype(float) for kp in DRAINED}
        else:
            ws = {
                kp: configs[(cfg, kp)].same_head_survive.astype(float) for kp in DRAINED
            }
        s_curves = {
            kp: ie.weighted_curve(adopted[kp], ws[kp], f"A13 S {name}", static=True)
            for kp in DRAINED
        }
        static_pe[name] = A.run(s_curves)[1]
    # Gate: the rebuilt adopted arm reproduces production, field for field.
    prod_rows = A.rows[A.unc._arm_key("matrix", "posterior")]
    for key, row in prod_rows.items():
        mine = arms_rows["as_if_undrained"][key]
        for f, v in row.items():
            if f != "bep_source" and str(mine[f]) != str(v):
                raise SystemExit(f"rebuilt as-if-undrained arm differs at {key} {f}")
    prior_rows = A.rows[A.unc._arm_key("matrix", "prior")]
    for kp in DRAINED:
        for s in A.scenarios:
            mine = arms_rows["prior"][("Tokachi", kp, s)]
            base = prior_rows[("Tokachi", kp, s)]
            if abs(_num(mine["p_annual_bep"]) - _num(base["p_annual_bep"])) > 1e-15:
                raise SystemExit(f"rebuilt prior arm differs at {kp} {s}")

    rng = np.random.default_rng(A.unc.SEED)
    annual: dict[str, Any] = {}
    for scenario in A.scenarios:
        pack = A.multiplicities(scenario, replicates, rng)
        sys_reps: dict[tuple[str, float], NDArray] = {}
        for name, _ in LIKELIHOODS:
            for kp in KPS:
                key = ("Tokachi", kp, scenario)
                v = arms_pe[name][key]
                vals = {
                    "__system__": v["__system__"],
                    "bep": v["bep"],
                    "overflow": v.get("overflow", np.zeros_like(v["bep"])),
                }
                reps = A.replicate(vals, scenario, pack)
                sys_reps[(name, kp)] = reps["__system__"]
                row = arms_rows[name][key]
                pb, po = _num(row["p_annual_bep"]), _num(row["p_annual_overflow"])
                cell = {
                    "p_system": _num(row["p_annual_system"]),
                    "p_bep": pb,
                    "p_overflow": po,
                    "share_bep": (
                        None
                        if row["share_bep"] in ("", None)
                        else float(row["share_bep"])
                    ),
                    "system_ci95": _ci(reps["__system__"]),
                    "fraction_replicates_piping_leads": float(
                        np.mean(reps["bep"] > reps["overflow"])
                    ),
                }
                if kp in DRAINED:
                    sb = static_pe[name][key]["bep"].mean()
                    cell["annual_S_over_T_bep_own_update"] = float(sb / v["bep"].mean())
                annual[f"{name} {scenario} {_label(kp)}"] = cell
        for name, _ in LIKELIHOODS:
            stack = np.column_stack([sys_reps[(name, kp)] for kp in KPS])
            ranks = (-stack).argsort(axis=1).argsort(axis=1) + 1
            point = np.array(
                [annual[f"{name} {scenario} {_label(kp)}"]["p_system"] for kp in KPS]
            )
            point_rank = (-point).argsort().argsort() + 1
            for j, kp in enumerate(KPS):
                annual[f"{name} {scenario} {_label(kp)}"]["rank"] = int(point_rank[j])
                annual[f"{name} {scenario} {_label(kp)}"]["rank_replicate_share"] = (
                    float(np.mean(ranks[:, j] == point_rank[j]))
                )
    for name, _ in LIKELIHOODS:
        for kp in KPS:
            h = annual[f"{name} historical {_label(kp)}"]["p_system"]
            w4 = annual[f"{name} +4K {_label(kp)}"]["p_system"]
            annual[f"{name} historical {_label(kp)}"]["climate_ratio"] = (
                w4 / h if h else None
            )
    A.check_cache()
    return {
        "gates": {
            "production_table": A.gate,
            "rows_aligned_theta_and_L": True,
            "rebuilt_as_if_undrained_arm_equals_production": True,
            "rebuilt_prior_arm_equals_production": True,
        },
        "replicates": replicates,
        "per_flood": per_flood,
        "prior_means": prior_means,
        "annual": annual,
    }


# --------------------------------------------------------------------------- #
# Part: seepage (A35)                                                          #
# --------------------------------------------------------------------------- #
def _eta2(y: NDArray[np.bool_], x: NDArray, bins: int = 20) -> float:
    """First-order correlation ratio of a binary indicator on one input."""
    y = y.astype(np.float64)
    v = y.var()
    if v <= 0:
        return float("nan")
    edges = np.quantile(x, np.linspace(0, 1, bins + 1))
    idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, bins - 1)
    cnt = np.bincount(idx, minlength=bins)
    s = np.bincount(idx, weights=y, minlength=bins)
    m = np.divide(s, cnt, out=np.zeros(bins), where=cnt > 0)
    return float(np.sum(cnt * (m - y.mean()) ** 2) / y.size / v)


def _ladder(kp: float, results_root: Path):
    tag = f"{kp:.1f}".replace(".", "_")
    path = results_root / "hwl_bias_resolution" / f"ladder_kp{tag}_n1000000.h5"
    with h5py.File(path, "r") as h5:
        grid = np.asarray(h5["conditioning_grid"][:], dtype=np.float64)
        comp = {
            c: np.asarray(h5["comparators"][c][:], dtype=bool) for c in ("C3b", "C4b")
        }
        L = np.asarray(h5["seepage_length_samples"][:], dtype=np.float64)
    cfg = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))["config"]
    return grid, comp, L, float(cfg["geometry"]["L"])


def seepage_part(results_root: Path, replicates: int) -> dict[str, Any]:
    A = Annual(results_root)
    bundles = {kp: ie.Bundle(results_root, "undrained", kp) for kp in KPS}
    per_flood: dict[str, Any] = {}
    masks: dict[tuple[float, float], NDArray[np.bool_]] = {}
    for kp, b in bundles.items():
        mean_L = float(b.run.geometry["L"])
        if abs(b.L.mean() / mean_L - 1) > 0.01:
            raise SystemExit(f"{_label(kp)}: sampled L mean far from the adopted mean")
        nt = b.tran.sum(axis=0)
        ok = np.nonzero(nt >= R1)[0]
        shoulder = int(ok[0]) if ok.size else None
        sec: dict[str, Any] = {
            "mean_L_m": mean_L,
            "cov_L": float(b.run.config.seepage_length_cov),
            "L_p05_m": float(np.percentile(b.L, 5)),
            "L_min_sampled_m": float(b.L.min()),
            "shoulder_stage_m": None if shoulder is None else float(b.grid[shoulder]),
            "arms": {},
        }
        for t in (0.0, *TRUNCATIONS):
            m = b.L >= t * mean_L
            masks[(kp, t)] = m
            n = int(m.sum())
            pt = b.tran[m].mean(axis=0)
            ps = b.c3b[m].mean(axis=0)
            arm: dict[str, Any] = {
                "kept_fraction": n / b.n,
                "n": n,
                "L_p05_m": float(np.percentile(b.L[m], 5)),
                "levels": [
                    {
                        "stage_m": float(h),
                        "p_trans": float(pt[i]),
                        "p_static": float(ps[i]),
                        "k_trans": int(b.tran[m, i].sum()),
                        "k_static": int(b.c3b[m, i].sum()),
                    }
                    for i, h in enumerate(b.grid)
                ],
            }
            i = int(np.argmin(np.abs(b.grid - DESIGN_GRID[kp])))
            if b.tran[m, i].sum() >= R1:
                arm["design_grid"] = tdf.paired_pair(
                    b.c3b[m, i], b.tran[m, i], SEED + int(10 * kp) + int(100 * t)
                )
            if shoulder is not None:
                arm["shoulder_ratio_trans"] = float(
                    pt[shoulder] / b.tran[:, shoulder].mean()
                )
                arm["shoulder_ratio_static"] = float(
                    ps[shoulder] / b.c3b[:, shoulder].mean()
                )
                arm["shoulder_pair"] = (
                    tdf.paired_pair(
                        b.c3b[m, shoulder], b.tran[m, shoulder], SEED + 5 + int(100 * t)
                    )
                    if b.tran[m, shoulder].sum() >= R1
                    else None
                )
            # 2016 update among the retained rows.
            arm["rejected_pct"] = float(100 * np.mean(~b.accept[m]))
            arm["static_rejected_pct"] = float(100 * np.mean(~b.same_head_survive[m]))
            arm["likelihood_ratio"] = float(
                b.accept[m].mean() / b.same_head_survive[m].mean()
            )
            arm["exit_opened_2016_pct"] = float(100 * b.init[m].mean())
            sec["arms"][f"{t:.2f}"] = arm
        per_flood[_label(kp)] = sec
        print(f"  seepage per-flood {_label(kp)} done", flush=True)

    # Million-draw anchors (KP 57.4, 62.0), truncated on their own persisted L.
    anchors: dict[str, Any] = {}
    for kp, stages in ((57.4, (39.21, 39.5)), (62.0, (46.39, 46.5, 46.75))):
        grid, comp, L, mean_L = _ladder(kp, results_root)
        for t in (0.0, *TRUNCATIONS):
            m = L >= t * mean_L
            for h in stages:
                i = int(np.argmin(np.abs(grid - h)))
                ks, kt = int(comp["C3b"][m, i].sum()), int(comp["C4b"][m, i].sum())
                entry: dict[str, Any] = {
                    "n": int(m.sum()),
                    "k_static": ks,
                    "k_trans": kt,
                }
                if kt >= R1:
                    entry["pair"] = tdf.paired_pair(
                        comp["C3b"][m, i], comp["C4b"][m, i], SEED + 77 + i
                    )
                anchors[f"{_label(kp)} {h:.2f} t{t:.2f}"] = entry
        print(f"  seepage anchors {_label(kp)} done", flush=True)

    # Sensitivity ranking: first-order correlation ratio at the GSA stages.
    ranking: dict[str, Any] = {}
    for kp, stages in ((58.8, (40.25, 41.0)), (60.0, (42.75,))):
        b = bundles[kp]
        for h in stages:
            i = int(np.argmin(np.abs(b.grid - h)))
            for t in (0.0, 0.85, 1.00):
                m = masks[(kp, t)]
                y = b.tran[m, i]
                eta = {
                    name: _eta2(y, b.theta[m, b.names.index(name)]) for name in b.names
                }
                eta["L"] = _eta2(y, b.L[m])
                ranking[f"{_label(kp)} {h:.2f} t{t:.2f}"] = eta

    # Annual: truncated posterior (and prior, both criteria) per t.
    annual: dict[str, Any] = {}
    rng = np.random.default_rng(A.unc.SEED)
    arms_pe: dict[str, Any] = {}
    arms_rows: dict[str, Any] = {}
    for t in (0.0, *TRUNCATIONS):
        tag = f"{t:.2f}"
        post_curves = {
            kp: ie.weighted_curve(
                b, (b.accept & masks[(kp, t)]).astype(float), f"A35 post t{tag}"
            )
            for kp, b in bundles.items()
        }
        arms_rows[tag], arms_pe[tag] = A.run(post_curves)
        prior_t = A.run(
            {
                kp: ie.weighted_curve(b, masks[(kp, t)].astype(float), f"A35 T t{tag}")
                for kp, b in bundles.items()
            }
        )[1]
        prior_s = A.run(
            {
                kp: ie.weighted_curve(
                    b, masks[(kp, t)].astype(float), f"A35 S t{tag}", static=True
                )
                for kp, b in bundles.items()
            }
        )[1]
        for scenario in A.scenarios:
            for kp in KPS:
                key = ("Tokachi", kp, scenario)
                row = arms_rows[tag][key]
                annual[f"t{tag} {scenario} {_label(kp)}"] = {
                    "p_system": _num(row["p_annual_system"]),
                    "p_bep": _num(row["p_annual_bep"]),
                    "p_overflow": _num(row["p_annual_overflow"]),
                    "share_bep": (
                        None
                        if row["share_bep"] in ("", None)
                        else float(row["share_bep"])
                    ),
                    "annual_S_over_T_prior_bep": float(
                        prior_s[key]["bep"].mean() / prior_t[key]["bep"].mean()
                    ),
                }
        print(f"  seepage annual t{tag} done", flush=True)
    # Gate: t = 0 reproduces production.
    prod_rows = A.rows[A.unc._arm_key("matrix", "posterior")]
    for key, row in prod_rows.items():
        for f, v in row.items():
            if f != "bep_source" and str(arms_rows["0.00"][key][f]) != str(v):
                raise SystemExit(f"untruncated arm differs from production {key} {f}")
    for scenario in A.scenarios:
        pack = A.multiplicities(scenario, replicates, rng)
        for t in (0.0, *TRUNCATIONS):
            tag = f"{t:.2f}"
            for kp in KPS:
                key = ("Tokachi", kp, scenario)
                v = arms_pe[tag][key]
                vals = {
                    "__system__": v["__system__"],
                    "bep": v["bep"],
                    "overflow": v.get("overflow", np.zeros_like(v["bep"])),
                }
                base = arms_pe["0.00"][key]
                vals["base_bep"] = base["bep"]
                reps = A.replicate(vals, scenario, pack)
                cell = annual[f"t{tag} {scenario} {_label(kp)}"]
                cell["system_ci95"] = _ci(reps["__system__"])
                cell["fraction_replicates_piping_leads"] = float(
                    np.mean(reps["bep"] > reps["overflow"])
                )
                with np.errstate(divide="ignore", invalid="ignore"):
                    cell["bep_relative_ci95"] = _ci(reps["bep"] / reps["base_bep"])
                cell["bep_relative"] = (
                    cell["p_bep"] / annual[f"t0.00 {scenario} {_label(kp)}"]["p_bep"]
                )
    for t in (0.0, *TRUNCATIONS):
        tag = f"{t:.2f}"
        for kp in KPS:
            h = annual[f"t{tag} historical {_label(kp)}"]["p_system"]
            w4 = annual[f"t{tag} +4K {_label(kp)}"]["p_system"]
            annual[f"t{tag} historical {_label(kp)}"]["climate_ratio"] = (
                w4 / h if h else None
            )
    A.check_cache()
    return {
        "gates": {
            "production_table": A.gate,
            "untruncated_arm_equals_production": True,
            "hazard_cache_unchanged": True,
        },
        "replicates": replicates,
        "per_flood": per_flood,
        "anchors_1e6": anchors,
        "first_order_ranking": ranking,
        "annual": annual,
    }


# --------------------------------------------------------------------------- #
# Part: seepage_adopted (A35 with the ADR-0056 conditioning)                   #
# --------------------------------------------------------------------------- #
def seepage_adopted_part(results_root: Path, replicates: int) -> dict[str, Any]:
    """Annual effect of the bounded seepage-length prior, adopted conditioning.

    The truncated prior conditioned as ADR-0056 conditions the adopted one: the
    2016 update at KP 57.4 and 62.0, none at the drained sections. Shares are
    the summed contributions (the convention of the alternative readings) with
    the overflow-first and piping-first splits beside them.
    """
    A = Annual(results_root)
    bundles = {kp: ie.Bundle(results_root, "undrained", kp) for kp in KPS}
    rng = np.random.default_rng(A.unc.SEED)
    packs = {s: A.multiplicities(s, replicates, rng) for s in A.scenarios}
    out: dict[str, Any] = {}
    base_pe = None
    for t in (0.0, 0.85, 1.00):
        tag = f"{t:.2f}"
        curves = {}
        for kp, b in bundles.items():
            m = b.L >= t * float(b.run.geometry["L"])
            w = m if kp in UNCONDITIONED else (m & b.accept)
            curves[kp] = ie.weighted_curve(b, w.astype(float), f"A35 adopted t{tag}")
        rows, pe = A.run(curves)
        if t == 0.0:
            base_pe = pe
            for kp in KPS:
                arm = (
                    A.unc._arm_key("matrix", "prior")
                    if kp in UNCONDITIONED
                    else A.unc._arm_key("matrix", "posterior")
                )
                for s in A.scenarios:
                    got = rows[("Tokachi", kp, s)]["p_annual_system"]
                    want = A.rows[arm][("Tokachi", kp, s)]["p_annual_system"]
                    if str(got) != str(want):
                        raise SystemExit(f"t=0 adopted arm differs at {kp} {s}")
        reps_sys = {}
        for scenario in A.scenarios:
            for kp in KPS:
                key = ("Tokachi", kp, scenario)
                v = pe[key]
                pb = v["bep"]
                po = v.get("overflow", np.zeros_like(pb))
                over = pb * po
                vals = {
                    "__system__": v["__system__"],
                    "bep": pb,
                    "overflow": po,
                    "ovf_first_b": pb - over,
                    "pip_first_o": po - over,
                    "base_bep": base_pe[key]["bep"],
                }
                r = A.replicate(vals, scenario, packs[scenario])
                reps_sys[(scenario, kp)] = r["__system__"]
                row = rows[key]
                sb, so = float(pb.mean()), float(po.mean())
                union = float((1 - (1 - pb) * (1 - po)).mean())
                with np.errstate(divide="ignore", invalid="ignore"):
                    lead_r = np.mean(r["bep"] > r["overflow"])
                out[f"t{tag} {scenario} {_label(kp)}"] = {
                    "p_system": _num(row["p_annual_system"]),
                    "system_ci95": _ci(r["__system__"]),
                    "p_bep": sb,
                    "p_overflow": so,
                    "summed_share_bep": sb / (sb + so) if sb + so > 0 else None,
                    "overflow_first_share_bep": (
                        float((pb - over).mean()) / union if union > 0 else None
                    ),
                    "piping_first_share_bep": sb / union if union > 0 else None,
                    "fraction_replicates_piping_leads_summed": float(lead_r),
                    "bep_relative_to_adopted": sb / float(base_pe[key]["bep"].mean()),
                    "bep_relative_ci95": _ci(r["bep"] / r["base_bep"]),
                }
        for kp in KPS:
            hc = out[f"t{tag} historical {_label(kp)}"]
            wc = out[f"t{tag} +4K {_label(kp)}"]
            hc["climate_ratio"] = wc["p_system"] / hc["p_system"]
            hc["climate_ratio_ci95"] = _ci(
                A.unc.ratio_series(reps_sys[("historical", kp)], reps_sys[("+4K", kp)])
            )
        print(f"  seepage adopted t{tag} done", flush=True)
    A.check_cache()
    return {"replicates": replicates, "annual": out}


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
PARTS = (
    "crest",
    "adopted",
    "alternatives",
    "drained",
    "seepage",
    "seepage_adopted",
    "report",
)


def _round(obj: Any, sig: int = 6) -> Any:
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return None
        return float(f"{obj:.{sig}g}")
    if isinstance(obj, dict):
        return {k: _round(v, sig) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, sig) for v in obj]
    return obj


def report_part() -> None:
    for part, path in EVIDENCE.items():
        stage = _read_stage(part)
        payload = {
            "study": path.stem,
            "generated_by": "scripts/results_annotations_study.py",
            "note": f"docs/decisions/{path.stem}.md",
            **_round(stage),
        }
        path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("part", choices=PARTS)
    parser.add_argument("--results-root", type=Path, default=REPO / "results")
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    args = parser.parse_args(argv)
    t0 = time.time()
    if args.part == "report":
        report_part()
        return 0
    fn = {
        "crest": crest_part,
        "adopted": adopted_part,
        "alternatives": alternatives_part,
        "drained": drained_part,
        "seepage": seepage_part,
        "seepage_adopted": seepage_adopted_part,
    }[args.part]
    payload = fn(args.results_root, args.replicates)
    print(f"wrote {_write_stage(args.part, payload)} in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
