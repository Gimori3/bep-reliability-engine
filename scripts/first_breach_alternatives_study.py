"""First-breach mechanism shares under the alternative readings (final audit).

Driver for ``docs/decisions/first-breach-alternatives-study.md``. Since ADR-0057
the reported mechanism share of the adopted configuration is the first-breach
split: a year in which both piping and overflow would fail is credited to the
mechanism that breaks through first on the canonical flood scaled to its peak.
The alternative readings the thesis uses to say which mechanism "leads" were
still ranked by the summed-contribution share ``P_BEP / (P_BEP + P_overflow)``,
a different quantity. This driver puts every alternative on the adopted
definition, with the adopted conditioning of ADR-0056 (2016 update at KP 57.4
and 62.0, none at KP 58.8 and 60.0), so that "lead" can mean one thing.

For each alternative and section it re-traces the pipe breach times of the
alternative's OWN failing rows (the M7 kernel with trajectory storage, gated
bit for bit against M8's end state, as ``results_annotations_study`` does for
the adopted rows), races them against the seeded overflow failure times at
every grid stage where overflow fails, and composes the first-breach split
year by year in the production annualisation with the alternative's curve
swapped in (gated against the committed alternative annual values).

Alternatives (each one named input changed, everything else adopted):
``bulk`` (bulk d70), ``k_aq_field_geomean`` / ``k_aq_field_toe`` /
``k_aq_regional_upper`` (ADR-0048 prior means, matrix), ``bulk_k_aq_regional_upper``
(bulk d70 with the regional-upper mean), ``credit_half`` / ``credit_full``
(ADR-0052 foreland credit), ``gravel_x1.80`` (the Dutch gravel multiplier on
H_c, a Phase 1 arm of ``gravel_grading_resistance_study``), ``seepage_tail_0.85``
(the seepage-length prior bounded at 0.85 of its mean, masked rows),
``steady_state`` (the same-head, same-gate static criterion of ADR-0055 with
instantaneous growth: breach when the gate is open and the erosion head first
exceeds H_c), and ``lambda_ac_100`` / ``lambda_ac_40`` (shorter correlation
lengths, n_eff = 2 and 5 independent stretches in the 200 m segment; the
segment's pipe breaks through at the earliest of its failing stretches).

Nothing is re-swept and no default, config, prior, kernel, persisted sweep,
posterior or production annual result changes. Every rebuilt quantity is gated
before an alternative is reported: the adopted re-trace reproduces the committed
``time_order`` of ``drained-section-conditioning-adopted.json`` exactly (same
seed, same draw order), every breach re-run reproduces M8's end state, every
alternative's annual system probability reproduces its committed value.

Usage (worktree root, main venv, ``PYTHONPATH=.``)::

    python scripts/first_breach_alternatives_study.py trace
        --results-root <main>/results --gravel-root <gravel study dir>
    python scripts/first_breach_alternatives_study.py annual
        --results-root <main>/results --gravel-root <gravel study dir>
    python scripts/first_breach_alternatives_study.py report

(``--gravel-root`` holds the ``arms/`` and ``phase2/`` of
``gravel_grading_resistance_study.py``.)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
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


#: The adopted first-breach machinery, imported and never restated.
ras = _load_module("results_annotations_study")
ie = ras.ie
tdf = ras.tdf

KPS = ras.KPS
UNCONDITIONED = ras.UNCONDITIONED
SEED = 20261011
REPLICATES = ras.REPLICATES
BREACH_ROWS = ras.BREACH_ROWS
SEGMENT_LENGTH_M = 200.0
CRACK = 0.3  # Pol SIE 2024 Eq. (6), the adopted crack coefficient (ADR-0055)

OUT_DIR = REPO / "results" / "first_breach_alternatives"
DECISIONS = REPO / "docs" / "decisions"
EVIDENCE = DECISIONS / "first-breach-alternatives-study.json"
ADOPTED = DECISIONS / "drained-section-conditioning-adopted.json"
ALTERNATIVES = DECISIONS / "drained-section-conditioning-alternatives.json"
GRAVEL = DECISIONS / "gravel-grading-resistance-study.json"
SEEPAGE_ADOPTED = DECISIONS / "seepage-length-lower-tail-adopted.json"

#: Swept alternatives: (key, label, Phase 1 path, Phase 2 posterior path).
ROW_ARMS: tuple[str, ...] = (
    "bulk",
    "k_aq_field_geomean",
    "k_aq_field_toe",
    "k_aq_regional_upper",
    "bulk_k_aq_regional_upper",
    "credit_half",
    "credit_full",
    "gravel_x1.80",
    "bulk_k_aq_field_geomean",
    "bulk_k_aq_field_toe",
)
#: Every traced arm, in the fixed order that sets its seed
#: (``SEED + 101 * (position + 1)``), whatever subset a run traces.
ALL_ARMS: tuple[str, ...] = (
    "bulk",
    "k_aq_field_geomean",
    "k_aq_field_toe",
    "k_aq_regional_upper",
    "bulk_k_aq_regional_upper",
    "credit_half",
    "credit_full",
    "gravel_x1.80",
    "seepage_tail_0.85",
    "steady_state",
    "lambda_ac",
    "bulk_k_aq_field_geomean",
    "bulk_k_aq_field_toe",
)
LABELS: dict[str, str] = {
    "adopted": "adopted (matrix, adopted conductivity, no foreland credit)",
    "bulk": "bulk d70 reading",
    "k_aq_field_geomean": "conductivity mean: six-test field geometric mean",
    "k_aq_field_toe": "conductivity mean: landside-toe field test",
    "k_aq_regional_upper": "conductivity mean: regional upper value",
    "bulk_k_aq_regional_upper": "bulk d70 with the regional upper conductivity",
    "bulk_k_aq_field_geomean": "bulk d70 with the six-test field geometric mean",
    "bulk_k_aq_field_toe": "bulk d70 with the landside-toe field test",
    "credit_half": "foreland credit, half of lambda_out_eff",
    "credit_full": "foreland credit, all of lambda_out_eff",
    "gravel_x1.80": "critical head x 1.8 (Dutch gravel allowance)",
    "seepage_tail_0.85": "seepage length bounded at 0.85 of its mean",
    "steady_state": "steady-state criterion, same head and gate (instantaneous growth)",
    "lambda_ac_100": "correlation length 100 m (two independent stretches)",
    "lambda_ac_40": "correlation length 40 m (five independent stretches)",
}


def _stem(kp: float, d70: str = "matrix") -> str:
    return tdf._stem(kp, d70)


def _label(kp: float) -> str:
    return tdf._label(kp)


def _paths(results_root: Path, gravel_root: Path, arm: str, kp: float):
    s, sb = _stem(kp), _stem(kp, "bulk")
    sens = results_root / "sensitivity"
    if arm == "bulk":
        return results_root / f"{sb}.h5", results_root / f"phase2/{sb}_posterior.h5"
    if arm.startswith("k_aq_"):
        return (
            sens / "adr0048_prior_means" / f"{s}_{arm}.h5",
            sens / "conductivity_posterior" / "phase2" / f"{s}_{arm}_posterior.h5",
        )
    if arm.startswith("bulk_k_aq_"):
        a = arm[len("bulk_") :]
        return (
            sens / "adr0048_prior_means" / f"{sb}_{a}.h5",
            sens / "conductivity_posterior" / "phase2" / f"{sb}_{a}_posterior.h5",
        )
    if arm.startswith("credit_"):
        d = sens / "adr0052_foreland_credit"
        return d / f"{s}_{arm}.h5", d / "phase2" / f"{s}_{arm}_posterior.h5"
    if arm == "gravel_x1.80":
        return (
            gravel_root / "arms" / f"{s}_hc_x1.80.h5",
            gravel_root / "phase2" / f"{s}_hc_x1.80_posterior.h5",
        )
    raise KeyError(arm)


def _write_stage(part: str, payload: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"stage_{part}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def _read_stage(part: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / f"stage_{part}.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Row bundles of the swept alternatives                                         #
# --------------------------------------------------------------------------- #
def _arm_bundle(prior: Path, post: Path, label: str):
    """Rows, failure matrix and 2016 accept mask of one swept alternative.

    The object carries exactly what ``ras._pipe_breach_times`` and
    ``ras._time_order_section`` read: ``run``, ``names``, ``theta``, ``L``,
    ``tran``, ``grid``, ``accept``, ``n``, ``config``.
    """
    from bayesian_reliability_updating.replay import load_phase1_run

    run = load_phase1_run(prior)
    theta = np.asarray(run.theta, dtype=np.float64)
    with h5py.File(post, "r") as h5:
        (event,) = list(h5["events"].keys())
        accept = np.asarray(h5["events"][event]["accept_trans"][:]).astype(bool)
        names = [x.decode() if isinstance(x, bytes) else x for x in h5["param_names"]]
        if not np.array_equal(np.asarray(h5["theta_matrix"][:]), theta):
            raise SystemExit(f"{post.name}: theta differs from its Phase 1 run")
    tran = np.asarray(run.result.failure_matrix_tran, dtype=bool)
    return SimpleNamespace(
        run=run,
        names=names,
        theta=theta,
        L=np.asarray(run.seepage_length_samples, dtype=np.float64),
        tran=tran,
        grid=np.asarray(run.result.conditioning_grid, dtype=np.float64),
        accept=accept,
        n=int(theta.shape[0]),
        config=label,
        prior_path=prior,
        post_path=post,
    )


# --------------------------------------------------------------------------- #
# Time order on a row subset (seepage tail) and for the steady-state rule       #
# --------------------------------------------------------------------------- #
def _time_order_masked(b, kp: float, keep: NDArray[np.bool_], rng) -> list[dict]:
    """``ras._time_order_section`` on an explicit row mask."""
    saved = b.accept
    try:
        b.accept = keep
        return ras._time_order_section(b, kp, True, rng)
    finally:
        b.accept = saved


def _static_breach_times(b, record, rows: NDArray[np.int64]):
    """Breach times [s] of the same-head, same-gate static rule (ADR-0055 C3b).

    Instantaneous growth: a row fails when the exit is open (Terzaghi gate,
    the M8 uplift/heave condition, which reduces to the heave check under the
    Terzaghi gradient, ADR-0008) and the erosion head ``h - z_toe - 0.3 D_bl``
    exceeds ``H_c``. Both heads rise with the stage, so on the rising limb the
    first sample at which both hold is the breach time. Gate: the rows with a
    finite time are exactly the rows the persisted C3b flags fail at this
    stage.
    """
    from bep_reliability_engine import evaluator as ev
    from bep_reliability_engine.constants import GAMMA_W
    from bep_reliability_engine.time_contract import validate_record

    config = b.run.config
    theta = b.theta[rows]
    names = b.names
    diag = ev.evaluate_batch_diagnostics(
        theta,
        record,
        b.run.geometry,
        l_ini=0.0,
        seepage_length_samples=b.L[rows],
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
    h = np.asarray(validate_record(record), dtype=np.float64)
    dt_s = float(record.native_dt)
    d_bl = theta[:, names.index("D_bl")]
    gam = theta[:, names.index("gamma_bl_sub")]
    relief = config.toe_gradient_relief_factor
    kept = 1.0 if relief is None else float(relief)
    gate = (diag.r_e * kept)[None, :] * (h[:, None] - z_toe) > (gam * d_bl / GAMMA_W)[
        None, :
    ]
    erosion = (h[:, None] - z_toe - CRACK * d_bl[None, :]) > np.asarray(
        diag.H_c_transient, dtype=np.float64
    )[None, :]
    both = gate & erosion
    hit = both.any(axis=0)
    first = np.argmax(both, axis=0)
    return np.where(hit, first * dt_s, np.inf), hit


def _time_order_static(b, kp: float, keep: NDArray[np.bool_], rng) -> list[dict]:
    """pi(h) for the steady-state rule on the C3b-failing rows of ``keep``."""
    from bep_reliability_engine.run import conditioning_hydrographs_for_config

    seg, draws, shape, h_base, dt_o, _gen = ras._overflow_setup(kp)
    records = conditioning_hydrographs_for_config(b.run.config)
    levels = []
    for i, h in enumerate(b.grid):
        p_o, t_o, _ = ras._overflow_times(float(h), seg, draws, shape, h_base, dt_o)
        if p_o <= 0.0:
            continue
        fail_rows = np.nonzero(b.c3b[:, i] & keep)[0]
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
            t_s, hit = _static_breach_times(b, records[i], take)
            if not np.all(hit):
                raise SystemExit(f"{_label(kp)} {h}: static rule lost a C3b failure")
            entry["n_pipe_traced"] = int(take.size)
            entry["pi_pipe_first"] = ras._pi_first(t_s, t_o)
            entry["pipe_breach_h_quartiles"] = [
                float(x) for x in np.percentile(t_s / 3600.0, [25, 50, 75])
            ]
        levels.append(entry)
        print(f"  static order {_label(kp)} {h:.2f}: {entry.get('pi_pipe_first')}")
    return levels


def _pi_segment(t_p: NDArray, t_o: NDArray, p: float, n: float) -> float:
    """P(segment pipe first | both fail) for ``n`` independent stretches.

    Each stretch fails with probability ``p`` and, if it fails, breaks through
    at a time drawn from the traced per-stretch distribution ``t_p``; the
    segment breaks through at its earliest failing stretch, so
    ``P(T_seg < t) = 1 - (1 - p F(t))**n`` (ties count one half, as in
    ``ras._pi_first``). Reduces to ``ras._pi_first`` at ``n = 1``.
    """
    t_p = np.sort(t_p[np.isfinite(t_p)])
    t_o = t_o[np.isfinite(t_o)]
    if t_p.size == 0 or t_o.size == 0 or p <= 0.0:
        return float("nan")
    lt = np.searchsorted(t_p, t_o, side="left")
    le = np.searchsorted(t_p, t_o, side="right")
    F = (lt + 0.5 * (le - lt)) / t_p.size
    p_seg = 1.0 - (1.0 - p) ** n
    return float(np.mean(1.0 - (1.0 - p * F) ** n) / p_seg)


def _time_order_segment(b, kp: float, keep, rng, n_values) -> dict[str, list]:
    """pi(h) on the adopted rows for each effective stretch count."""
    from bep_reliability_engine.run import conditioning_hydrographs_for_config

    seg, draws, shape, h_base, dt_o, _gen = ras._overflow_setup(kp)
    records = conditioning_hydrographs_for_config(b.run.config)
    out: dict[str, list] = {f"{n:g}": [] for n in n_values}
    for i, h in enumerate(b.grid):
        p_o, t_o, _ = ras._overflow_times(float(h), seg, draws, shape, h_base, dt_o)
        if p_o <= 0.0:
            continue
        fail_rows = np.nonzero(b.tran[:, i] & keep)[0]
        p = float(fail_rows.size / keep.sum())
        if not fail_rows.size:
            continue
        take = (
            fail_rows
            if fail_rows.size <= BREACH_ROWS
            else np.sort(rng.choice(fail_rows, BREACH_ROWS, replace=False))
        )
        t_p, ftrans = ras._pipe_breach_times(b, records[i], take)
        if not np.all(ftrans):
            raise SystemExit(f"{_label(kp)} {h}: re-run lost a breach")
        for n in n_values:
            out[f"{n:g}"].append(
                {
                    "stage_m": float(h),
                    "p_stretch": p,
                    "pi_pipe_first": _pi_segment(t_p, t_o, p, n),
                }
            )
        print(f"  segment order {_label(kp)} {h:.2f}: p={p:.4f}")
    return out


# --------------------------------------------------------------------------- #
# Part: trace                                                                  #
# --------------------------------------------------------------------------- #
def trace_part(results_root: Path, gravel_root: Path, arms: list[str]) -> dict:
    cached = OUT_DIR / "stage_trace.json"
    out: dict[str, Any] = _read_stage("trace") if cached.is_file() else {}
    # Gate: the adopted re-trace reproduces the committed time order exactly.
    if "adopted" not in out:
        rng = np.random.default_rng(ras.SEED + 1)
        mine: dict[str, Any] = {}
        for kp in KPS:
            b = ie.Bundle(results_root, "undrained", kp)
            mine[_label(kp)] = ras._time_order_section(
                b, kp, kp not in UNCONDITIONED, rng
            )
        committed = json.loads(ADOPTED.read_text(encoding="utf-8"))["time_order"]
        for kp in KPS:
            a = [e.get("pi_pipe_first") for e in mine[_label(kp)]]
            c = [e.get("pi_pipe_first") for e in committed[_label(kp)]]
            if len(a) != len(c) or any(
                (x is None) != (y is None)
                or (x is not None and abs(x - y) > 1e-6 * max(1.0, abs(y)))
                for x, y in zip(a, c)
            ):
                raise SystemExit(f"adopted re-trace differs at {_label(kp)}")
        out["adopted"] = mine
        out["adopted_reproduces_committed_time_order"] = True
        _write_stage("trace", out)
    for arm in arms:
        if arm in out:
            continue
        rng = np.random.default_rng(SEED + 101 * (ALL_ARMS.index(arm) + 1))
        tick = time.time()
        res: dict[str, Any] = {}
        for kp in KPS:
            if arm in ROW_ARMS:
                prior, post = _paths(results_root, gravel_root, arm, kp)
                b = _arm_bundle(prior, post, arm)
                keep = np.ones(b.n, bool) if kp in UNCONDITIONED else b.accept
                res[_label(kp)] = _time_order_masked(b, kp, keep, rng)
            elif arm == "seepage_tail_0.85":
                b = ie.Bundle(results_root, "undrained", kp)
                m = b.L >= 0.85 * float(b.run.geometry["L"])
                keep = m if kp in UNCONDITIONED else (m & b.accept)
                res[_label(kp)] = _time_order_masked(b, kp, keep, rng)
            elif arm == "steady_state":
                b = ie.Bundle(results_root, "undrained", kp)
                keep = np.ones(b.n, bool)  # Table 7.4: before any update
                res[_label(kp)] = _time_order_static(b, kp, keep, rng)
            elif arm == "lambda_ac":
                b = ie.Bundle(results_root, "undrained", kp)
                keep = np.ones(b.n, bool) if kp in UNCONDITIONED else b.accept
                res[_label(kp)] = _time_order_segment(
                    b,
                    kp,
                    keep,
                    rng,
                    (SEGMENT_LENGTH_M / 100.0, SEGMENT_LENGTH_M / 40.0),
                )
            else:
                raise KeyError(arm)
        out[arm] = res
        out.setdefault("runtime_s", {})[arm] = round(time.time() - tick, 1)
        _write_stage("trace", out)
        print(f"traced {arm} in {time.time() - tick:.0f} s", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: annual                                                                 #
# --------------------------------------------------------------------------- #
def _committed_system(arm: str) -> dict[tuple[str, str], float]:
    """The committed annual system probability of each alternative cell."""
    alt = json.loads(ALTERNATIVES.read_text(encoding="utf-8"))["cells"]
    out: dict[tuple[str, str], float] = {}
    name = {
        "bulk": "bulk",
        "k_aq_field_geomean": "k_aq_field_geomean",
        "k_aq_field_toe": "k_aq_field_toe",
        "k_aq_regional_upper": "k_aq_regional_upper",
        "bulk_k_aq_regional_upper": "bulk_upper",
    }
    if arm in name:
        for key, cell in alt.items():
            scen, sec = key.split(" ", 1)
            out[(sec, scen)] = float(cell["system_by_arm"][name[arm]])
    elif arm.startswith("bulk_k_aq_"):
        # Bulk-reading conductivity arms: the committed prior side at the
        # drained sections, the posterior side elsewhere (ADR-0056).
        sides = {
            "prior": ras._cond_cells(
                DECISIONS / "conductivity-bracket-annualisation-bulk.json"
            ),
            "posterior": ras._cond_cells(
                DECISIONS / "conductivity-bracket-posterior-side-bulk.json"
            ),
        }
        for kp in KPS:
            side = "prior" if kp in UNCONDITIONED else "posterior"
            for scen in ("historical", "+4K"):
                cell = sides[side][(_label(kp), scen)]
                out[(_label(kp), scen)] = float(
                    cell["arms"][arm[len("bulk_") :]]["p_annual_system"]
                )
    elif arm == "gravel_x1.80":
        cells = json.loads(GRAVEL.read_text(encoding="utf-8"))["annual"]["cells"]
        for kp in KPS:
            br = "T-prior" if kp in UNCONDITIONED else "T-post"
            for scen in ("historical", "+4K"):
                out[(_label(kp), scen)] = float(
                    cells[f"x1.80 {br} {scen} {_label(kp)}"]["p_system"]
                )
    elif arm == "seepage_tail_0.85":
        cells = json.loads(SEEPAGE_ADOPTED.read_text(encoding="utf-8"))["annual"]
        for kp in KPS:
            for scen in ("historical", "+4K"):
                out[(_label(kp), scen)] = float(
                    cells[f"t0.85 {scen} {_label(kp)}"]["p_system"]
                )
    return out


def _curves(A, results_root: Path, gravel_root: Path, arm: str) -> dict[float, Any]:
    from system_integration.bep_input import load_bep_curve

    curves: dict[float, Any] = {}
    for kp in KPS:
        if arm in ROW_ARMS:
            prior, post = _paths(results_root, gravel_root, arm, kp)
            src = prior if kp in UNCONDITIONED else post
            curves[kp] = load_bep_curve(src, branch="transient")
        elif arm == "seepage_tail_0.85":
            b = ie.Bundle(results_root, "undrained", kp)
            m = b.L >= 0.85 * float(b.run.geometry["L"])
            w = m if kp in UNCONDITIONED else (m & b.accept)
            curves[kp] = ie.weighted_curve(b, w.astype(float), "A35 adopted t0.85")
        elif arm == "steady_state":
            b = ie.Bundle(results_root, "undrained", kp)
            curves[kp] = ie.weighted_curve(
                b, np.ones(b.n), "steady-state prior", static=True
            )
        else:
            raise KeyError(arm)
    return curves


def _cell(A, pe_key, pe, peaks, table, packs, scenario) -> dict[str, Any]:
    v = pe[pe_key]
    pb = v["bep"]
    po = v.get("overflow", np.zeros_like(pb))
    pi = ras._pi_at(peaks, table)
    ab, ao = ras._first_breach(pb, po, pi)
    vals = {
        "__system__": v["__system__"],
        "bep": pb,
        "overflow": po,
        "fb_bep": ab,
        "fb_ovf": ao,
    }
    r = A.replicate(vals, scenario, packs[scenario])
    tot = float(ab.mean() + ao.mean())
    sb, so = float(pb.mean()), float(po.mean())
    with np.errstate(divide="ignore", invalid="ignore"):
        fb_r = r["fb_bep"] / (r["fb_bep"] + r["fb_ovf"])
        sum_r = r["bep"] / (r["bep"] + r["overflow"])
    return {
        "p_system": float(v["__system__"].mean()),
        "system_ci95": ras._ci(r["__system__"]),
        "p_bep": sb,
        "p_overflow": so,
        "first_breach_share_bep": (float(ab.mean() / tot) if tot > 0 else None),
        "first_breach_share_ci95": ras._ci(fb_r),
        "first_breach_piping_leads_fraction": float(np.mean(r["fb_bep"] > r["fb_ovf"])),
        "summed_share_bep": (sb / (sb + so) if sb + so > 0 else None),
        "summed_share_ci95": ras._ci(sum_r),
        "summed_piping_leads_fraction": float(np.mean(r["bep"] > r["overflow"])),
        "overflow_zero_every_year": bool(not np.any(po > 0)),
        "pi_interpolated_from_stages": len(
            [e for e in table if np.isfinite(e.get("pi_pipe_first", np.nan))]
        ),
    }


def _leader(cell: dict[str, Any], key: str) -> str | None:
    s = cell.get(key)
    if cell["p_system"] <= 0.0 or s is None:
        return None
    if s > 0.5:
        return "piping"
    if s < 0.5:
        return "overflow"
    return "tie"


def annual_part(results_root: Path, gravel_root: Path, replicates: int) -> dict:
    trace = _read_stage("trace")
    A = ras.Annual(results_root)
    unc = A.unc
    rng = np.random.default_rng(unc.SEED)
    packs = {s: A.multiplicities(s, replicates, rng) for s in A.scenarios}
    adopted_curves = {
        kp: A.production[
            (kp, "matrix", "prior" if kp in UNCONDITIONED else "posterior")
        ]
        for kp in KPS
    }
    committed_adopted = json.loads(ADOPTED.read_text(encoding="utf-8"))["table"]
    cells: dict[str, Any] = {}
    gates: dict[str, Any] = {}

    def run_arm(arm: str, curves, orders) -> None:
        rows, pe = A.run(curves)
        want = _committed_system(arm) if arm != "adopted" else {}
        worst = 0.0
        for scenario in A.scenarios:
            for kp in KPS:
                key = ("Tokachi", kp, scenario)
                cell = _cell(
                    A,
                    key,
                    pe,
                    A.peaks(kp, scenario),
                    orders[_label(kp)],
                    packs,
                    scenario,
                )
                cell["bep_clamped_above_grid"] = rows[key]["bep_clamped_above_grid"]
                if arm == "adopted":
                    c = committed_adopted[f"{scenario} {_label(kp)}"]
                    for f in ("p_system", "first_breach_share_bep"):
                        if c[f] is None or cell[f] is None:
                            if c[f] != cell[f]:
                                raise SystemExit(f"adopted {f} differs {key}")
                        elif abs(cell[f] / c[f] - 1) > 1e-9:
                            raise SystemExit(f"adopted {f} differs {key}")
                elif (_label(kp), scenario) in want:
                    w = want[(_label(kp), scenario)]
                    d = (
                        abs(cell["p_system"] - w) / w
                        if w > 0
                        else abs(cell["p_system"])
                    )
                    worst = max(worst, d)
                    if d > 1e-9:
                        raise SystemExit(
                            f"{arm} {key} system {cell['p_system']} != committed {w}"
                        )
                cells[f"{arm} {scenario} {_label(kp)}"] = cell
        gates[arm] = {
            "committed_system_reproduced": bool(arm == "adopted" or want),
            "max_relative_difference": worst,
        }
        print(f"  annual {arm} done", flush=True)

    run_arm("adopted", adopted_curves, trace["adopted"])
    for arm in [
        a for a in ROW_ARMS + ("seepage_tail_0.85", "steady_state") if a in trace
    ]:
        run_arm(arm, _curves(A, results_root, gravel_root, arm), trace[arm])
    # Correlation length: the production length effect on the adopted curves.
    if "lambda_ac" in trace:
        saved = unc.LAMBDA_AC_M
        try:
            for lam, n in ((100.0, "2"), (40.0, "5")):
                unc.LAMBDA_AC_M = lam
                orders = {sec: tab[n] for sec, tab in trace["lambda_ac"].items()}
                for kp, curve in adopted_curves.items():
                    A.context["bep_curves"][(kp, "matrix", "posterior")] = curve
                rows, pe = unc.annualise_arm(
                    A.campaign, A.context, "matrix", "posterior"
                )
                for kp in KPS:
                    A.context["bep_curves"][(kp, "matrix", "posterior")] = A.production[
                        (kp, "matrix", "posterior")
                    ]
                alt = json.loads(ALTERNATIVES.read_text(encoding="utf-8"))
                arm = f"lambda_ac_{lam:g}"
                for scenario in A.scenarios:
                    for kp in KPS:
                        key = ("Tokachi", kp, scenario)
                        cell = _cell(
                            A,
                            key,
                            pe,
                            A.peaks(kp, scenario),
                            orders[_label(kp)],
                            packs,
                            scenario,
                        )
                        base = committed_adopted[f"{scenario} {_label(kp)}"]["p_system"]
                        fac = alt["lambda_ac_factors"][f"{scenario} {_label(kp)}"][
                            f"{lam:g}"
                        ]
                        if abs(cell["p_system"] / (base * fac) - 1) > 1e-9:
                            raise SystemExit(f"{arm} {key} differs from committed")
                        cell["bep_clamped_above_grid"] = rows[key][
                            "bep_clamped_above_grid"
                        ]
                        cells[f"{arm} {scenario} {_label(kp)}"] = cell
                gates[arm] = {"committed_system_reproduced": True}
                print(f"  annual {arm} done", flush=True)
        finally:
            unc.LAMBDA_AC_M = saved
    A.check_cache()

    # Orderings: which cells change their leading mechanism, per definition.
    arms = sorted({k.split(" ", 1)[0] for k in cells})
    orderings: dict[str, Any] = {}
    for arm in arms:
        rec = {}
        for scenario in A.scenarios:
            for kp in KPS:
                c = cells[f"{arm} {scenario} {_label(kp)}"]
                rec[f"{scenario} {_label(kp)}"] = {
                    "first_breach": _leader(c, "first_breach_share_bep"),
                    "summed": _leader(c, "summed_share_bep"),
                    "first_breach_share": c["first_breach_share_bep"],
                    "summed_share": c["summed_share_bep"],
                    "first_breach_leads_fraction": c[
                        "first_breach_piping_leads_fraction"
                    ],
                }
        orderings[arm] = rec
    return {
        "definition": {
            "share": "first-breach split of the two-branch union (ADR-0057), "
            "each alternative with its own pipe breach times",
            "conditioning": "2016 update at KP 57.4 and 62.0, none at KP 58.8 and "
            "60.0 (ADR-0056); steady_state is before any update (thesis Table 7.4)",
            "summed": "P_BEP / (P_BEP + P_overflow), reported beside it",
        },
        "labels": LABELS,
        "gates": {
            "adopted_retrace_reproduces_committed_time_order": trace.get(
                "adopted_reproduces_committed_time_order", False
            ),
            "adopted_table_reproduced": True,
            "arms": gates,
            "production_table": A.gate,
            "hazard_cache_unchanged": True,
        },
        "replicates": replicates,
        "time_order": {k: v for k, v in trace.items() if k not in ("runtime_s",)},
        "cells": cells,
        "orderings": orderings,
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("part", choices=("trace", "annual", "report"))
    parser.add_argument("--results-root", type=Path, default=REPO / "results")
    parser.add_argument(
        "--gravel-root",
        type=Path,
        default=REPO / "results" / "gravel_grading",
        help="Directory holding the gravel_grading_resistance_study arms/ and phase2/.",
    )
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    parser.add_argument("--arms", nargs="*", default=list(ALL_ARMS))
    args = parser.parse_args(argv)
    if args.part == "trace":
        trace_part(args.results_root, args.gravel_root, args.arms)
    elif args.part == "annual":
        payload = annual_part(args.results_root, args.gravel_root, args.replicates)
        _write_stage("annual", payload)
        EVIDENCE.write_text(
            json.dumps(ras._round(payload), indent=1) + "\n", encoding="utf-8"
        )
        print(f"wrote {EVIDENCE}")
    else:
        d = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        for arm, rec in d["orderings"].items():
            print(arm)
            for cell, v in rec.items():
                print(
                    f"  {cell:22s} first-breach {v['first_breach']!s:8s} "
                    f"{v['first_breach_share']}  summed {v['summed']!s:8s} "
                    f"{v['summed_share']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
