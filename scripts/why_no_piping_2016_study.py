"""Why the Tokachi sections showed no piping in 2016 (Pol comment 8).

Driver for ``docs/decisions/why-no-piping-2016-study.md``. Companion study: no
production default, config, prior, kernel, persisted sweep, posterior or annual
result changes. The row-level inputs are the persisted Phase 1 sweeps, their
persisted 2016 replays and the same-head flags of the ADR-0055 study, reached
through the session 3 driver (``initiation_evidence_2016_study``); every new
evaluation goes through M8.

``sources``     the arithmetic of study section 3 from the OYO (1999) forms:
                the 2016 peaks against OYO's 1998 levels, hours above today's
                toe in OYO's design waveform, OYO's toe gradients scaled to the
                2016 heads, and the engine-to-OYO factor per section.
``gate``        closed-form 2016 initiation reproduces every stored flag; an M8
                replay of 2016 without relief reproduces the persisted breach
                and initiation flags; the design-grid transient column is
                reproduced by an M8 call on its canonical record.
``exits``       the probability that an exit opened in 2016 and the four-way
                outcome under each diagnostic arm (OYO-matched toe pressure,
                the field-case factors, OYO's drain designs on the measured
                berm, a thicker or heavier blanket).
``replay``      the 2016 breach under OYO-matched toe pressure (an M8 replay of
                the recorded flood with the ADR-0050 relief knob at 1/f).
``antecedent``  the 2016 stage relative to each landside toe in the days
                before the final rise.
``design``      static and transient failure at the design-grid stage under
                OYO-matched toe pressure.
``report``      assemble ``docs/decisions/why-no-piping-2016-study.json``.

Usage (from the worktree root, main venv, ``PYTHONPATH=.``)::

    python scripts/why_no_piping_2016_study.py all --results-root results
    python scripts/why_no_piping_2016_study.py report
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

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


#: Session 3's driver supplies the row bundles (persisted rows, 2016 replay,
#: same-head flags) and the 2016 record constructor. Imported, never restated.
ie = _load_module("initiation_evidence_2016_study")
tdf = ie.tdf

KPS = tdf.KPS
DESIGN_HWL = tdf.DESIGN_HWL
DESIGN_GRID = tdf.DESIGN_GRID
PEAK_2016 = tdf.PEAK_2016
CRACK = tdf.CRACK_RESISTANCE_FACTOR

OUT_DIR = REPO / "results" / "why_no_piping_2016"
EVIDENCE = REPO / "docs" / "decisions" / "why-no-piping-2016-study.json"
QUALIFICATIONS = (
    REPO / "docs" / "decisions" / "physical-model-qualifications-study.json"
)

# --------------------------------------------------------------------------- #
# Source values (study section 2). OYO (1999) forms 5 and 6 per section.       #
# --------------------------------------------------------------------------- #
#: Landside toe today [m T.P.] (2019 survey, ADR-0021), as in every config.
Z_TOE: dict[float, float] = {57.4: 38.30, 58.8: 38.50, 60.0: 40.00, 62.0: 44.90}
#: OYO's 1998 design level (the 1966/1983 plan) [m T.P.], form 5.
OYO_LEVEL: dict[float, float] = {57.4: 39.51, 58.8: 41.33, 60.0: 43.06, 62.0: 46.68}
#: OYO's design water-level waveform, form 5: (hour, stage m T.P.) points A..E.
OYO_WAVEFORM: dict[float, tuple[tuple[float, float], ...]] = {
    57.4: ((0.0, 34.00), (82.9, 34.00), (123.1, 39.51), (124.6, 39.51), (143.6, 34.00)),
    58.8: ((0.0, 36.80), (79.5, 36.80), (123.1, 41.33), (124.6, 41.33), (140.2, 36.80)),
    60.0: ((0.0, 37.80), (82.0, 37.80), (123.1, 43.06), (124.6, 43.06), (142.7, 37.80)),
    62.0: ((0.0, 41.60), (81.4, 41.60), (123.1, 46.68), (124.6, 46.68), (142.1, 41.60)),
}
#: OYO's maximum local toe gradients, form 6 (vertical, horizontal).
OYO_GRADIENT: dict[float, tuple[float, float]] = {
    57.4: (0.04, 0.05),
    58.8: (1.30, 0.62),
    60.0: (0.50, 0.40),
    62.0: (0.97, 0.66),
}
#: OYO's designed drains, report table 7-5-1 (vertical gradient after the
#: drain, and the design): cut through A_c at KP 58.8 and 62.0, on top at 60.0.
OYO_DRAIN: dict[float, tuple[float, str]] = {
    58.8: (0.30, "drain cut through the A_c cover"),
    60.0: (0.48, "drain on top of the cover"),
    62.0: (0.23, "drain cut through the A_c cover (designed, not built)"),
}
#: OYO's criterion and the cover's heave gradient at the prior-mean weight.
OYO_CRITERION = 0.5
GAMMA_BL_SUB_PRIOR_MEAN = 6.9
#: Tokoro (committee report 2017, pp. 2-11, 5-19 to 5-20; Kawajiri et al. 2025).
TOKORO = {
    "gauge": "Futochanae, KP 18.9",
    "design_level_m": 12.38,
    "peak_in_committee_waveform_m": 14.22,
    "hours_above_design_level": "32 h 40 min",
    "boil_site_model_gradients": {"vertical": 0.70, "horizontal": 0.87},
    "boil_sand_k_mps": 1.0e-5,
    "cover_k_mps": 1.0e-7,
    "sand_layer_thickness_m": "about 1.0 under the levee, 0.4 to 0.6 elsewhere",
    "cover_thickness_m": "about 1.0 (KP 24.6); 1.0 to 1.8 (KP 26.2)",
}

#: Field-case translation factors (thesis 4.7.2 and B.2).
FIELD_FACTORS: tuple[float, ...] = (1.13, 2.67)
#: Blanket arms: (label, D_bl multiplier, gamma'_bl multiplier).
BLANKET_ARMS: tuple[tuple[str, float, float], ...] = (
    ("D_bl x 1.5", 1.5, 1.0),
    ("D_bl x 2", 2.0, 1.0),
    ("gamma'_bl x 1.25", 1.0, 1.25),
)
#: OYO's designed relief, fractions of the toe gradient removed.
OYO_RELIEF = {58.8: 1.0 - 0.30 / 1.30, 60.0: 1.0 - 0.48 / 0.50}


def _label(kp: float) -> str:
    return tdf._label(kp)


def _write_stage(part: str, payload: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"stage_{part}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def _read_stage(part: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / f"stage_{part}.json").read_text(encoding="utf-8"))


def oyo_factor() -> dict[float, float]:
    """Engine toe gradient over OYO's at OYO's 1998 head (prior means)."""
    rows = json.loads(QUALIFICATIONS.read_text(encoding="utf-8"))["gradients"]
    return {float(r["kp"]): float(r["ratio_under_levee_to_reported"]) for r in rows}


def hours_above(waveform, threshold: float, step_h: float = 0.001) -> float:
    """Hours a piecewise-linear waveform stands above ``threshold``."""
    t = np.arange(0.0, waveform[-1][0] + step_h, step_h)
    h = np.interp(t, [p[0] for p in waveform], [p[1] for p in waveform])
    return float(np.count_nonzero(h > threshold) * step_h)


# --------------------------------------------------------------------------- #
# Part: sources                                                                #
# --------------------------------------------------------------------------- #
def sources_part() -> dict[str, Any]:
    f = oyo_factor()
    heave = GAMMA_BL_SUB_PRIOR_MEAN / GAMMA_W
    out: dict[str, Any] = {"heave_gradient_prior_mean": heave, "tokoro": TOKORO}
    for kp in KPS:
        ratio = (PEAK_2016[kp] - Z_TOE[kp]) / (OYO_LEVEL[kp] - Z_TOE[kp])
        iv, ih = OYO_GRADIENT[kp]
        entry: dict[str, Any] = {
            "peak_2016_m": PEAK_2016[kp],
            "design_level_today_m": DESIGN_HWL[kp],
            "oyo_level_1998_m": OYO_LEVEL[kp],
            "peak_minus_today_m": PEAK_2016[kp] - DESIGN_HWL[kp],
            "peak_minus_oyo_m": PEAK_2016[kp] - OYO_LEVEL[kp],
            "oyo_base_stage_below_toe_m": Z_TOE[kp] - OYO_WAVEFORM[kp][0][1],
            "oyo_waveform_hours_above_toe": hours_above(OYO_WAVEFORM[kp], Z_TOE[kp]),
            "head_ratio_2016_to_oyo": ratio,
            "oyo_iv_1998": iv,
            "oyo_ih_1998": ih,
            "oyo_iv_scaled_2016": iv * ratio,
            "oyo_ih_scaled_2016": ih * ratio,
            "oyo_iv_2016_exceeds_criterion": bool(iv * ratio >= OYO_CRITERION),
            "oyo_iv_2016_exceeds_heave": bool(iv * ratio > heave),
            "engine_over_oyo_factor": f[kp],
        }
        if kp in OYO_DRAIN:
            iv_d, what = OYO_DRAIN[kp]
            entry["oyo_drain"] = what
            entry["oyo_drain_iv_1998"] = iv_d
            entry["oyo_drain_relief"] = 1.0 - iv_d / iv
            entry["oyo_drain_iv_scaled_2016"] = iv_d * ratio
        out[_label(kp)] = entry
    return out


# --------------------------------------------------------------------------- #
# Row helpers                                                                  #
# --------------------------------------------------------------------------- #
def _outcomes(
    exit_open: NDArray[np.bool_],
    c1_fail: NDArray[np.bool_],
    breach: NDArray[np.bool_] | None,
) -> dict[str, float | None]:
    """Four-way 2016 outcome; ``c1_fail`` is erosion head above H_c at the peak."""
    static = exit_open & c1_fail
    out: dict[str, float | None] = {
        "exit": float(np.mean(exit_open)),
        "no_exit": float(np.mean(~exit_open)),
        "exit_stalls_below_H_c": float(np.mean(exit_open & ~c1_fail)),
        "same_head_static_failure": float(np.mean(static)),
    }
    if breach is None:
        out["held_only_by_duration"] = None
        out["breach"] = None
    else:
        if np.any(breach & ~static):
            raise SystemExit("a breach outside same-head failure: containment broken")
        out["held_only_by_duration"] = float(np.mean(static & ~breach))
        out["breach"] = float(np.mean(breach))
    return out


def _c1_fail(b) -> NDArray[np.bool_]:
    """Erosion head above H_c at the 2016 peak (session 3 / ADR-0055 rule)."""
    d_bl = b.theta[:, b.names.index("D_bl")]
    return (b.ev["Z_static"].astype(np.float64) + CRACK * d_bl) < 0.0


def _gate(b, kept: float) -> NDArray[np.bool_]:
    """2016 initiation with the toe overpressure multiplied by ``kept``."""
    return b.r_e * kept * (b.peak - b.z_toe) > b.weight_head


def _blanket_gate(b, m_d: float, m_g: float) -> NDArray[np.bool_]:
    """2016 initiation with D_bl x m_d (and its leakage length) and gamma x m_g.

    The foreshore blanket is a fixed geometry input (ADR-0005), so only
    lambda_in changes: r_e' = lambda_in' / (S + lambda_in'), with
    S = lambda_out_eff + L recovered row by row from the persisted r_e.
    """
    from bep_reliability_engine.hydraulics import leakage_length_in

    n = b.names
    k_aq = b.theta[:, n.index("k_aq")]
    d_aq = b.theta[:, n.index("D_aq")]
    d_bl = b.theta[:, n.index("D_bl")]
    k_bl = b.theta[:, n.index("k_bl")]
    gam = b.theta[:, n.index("gamma_bl_sub")]
    lam = leakage_length_in(k_aq, d_aq, d_bl, k_bl)
    rest = lam * (1.0 / b.r_e - 1.0)
    lam2 = leakage_length_in(k_aq, d_aq, d_bl * m_d, k_bl)
    r_e2 = lam2 / (rest + lam2)
    weight = (gam * m_g / GAMMA_W) * d_bl * m_d
    return r_e2 * (b.peak - b.z_toe) > weight


def _bundles(results_root: Path, configs=("undrained", "berm")):
    return ie._bundles(results_root, configs=configs)


# --------------------------------------------------------------------------- #
# Part: gate                                                                   #
# --------------------------------------------------------------------------- #
def _record(kp: float, data_root: Path):
    from bayesian_reliability_updating.events import (
        default_2016_source,
        observed_event_record,
    )

    src = default_2016_source(data_root.parent / "processed" / "2016_event")
    return observed_event_record(src, section_kp=kp, data_root=data_root)


def _replay(b, record, relief: float | None):
    """M8 replay of the 2016 record with the ADR-0050 relief knob set."""
    from bayesian_reliability_updating.replay import replay_event

    run = b.run
    if relief is not None:
        cfg = run.config.model_copy(update={"toe_gradient_relief_factor": relief})
        run = dataclasses.replace(run, config=cfg)
    rep = replay_event(run, record)
    d = rep.diagnostics
    return (
        np.asarray(d.failure_trans, dtype=bool),
        np.asarray(d.heave_occurred, dtype=bool),
    )


def gate_part(results_root: Path, data_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for (config, kp), b in _bundles(results_root).items():
        closed = _gate(b, ie._kept(config))
        mism = int(np.count_nonzero(closed != b.init))
        blank = _blanket_gate(b, 1.0, 1.0)
        mism_blank = int(np.count_nonzero(blank != b.init))
        if mism or mism_blank:
            raise SystemExit(f"{config} {_label(kp)}: closed form {mism}/{mism_blank}")
        entry: dict[str, Any] = {
            "closed_form_initiation_mismatches": mism,
            "blanket_identity_mismatches": mism_blank,
        }
        if config == "undrained":
            t0 = time.time()
            rec = _record(kp, data_root)
            if abs(float(rec.peak) - b.peak) > 1e-9:
                raise SystemExit(f"{_label(kp)}: record peak differs")
            fail, heave = _replay(b, rec, None)
            entry["replay_breach_mismatches"] = int(np.count_nonzero(fail != ~b.accept))
            entry["replay_initiation_mismatches"] = int(
                np.count_nonzero(heave != b.init)
            )
            entry["replay_seconds"] = time.time() - t0
            if (
                entry["replay_breach_mismatches"]
                or entry["replay_initiation_mismatches"]
            ):
                raise SystemExit(f"{_label(kp)}: replay does not reproduce {entry}")
        out[f"{config} {_label(kp)}"] = entry
        print(f"  gate {config} {_label(kp)}: passed", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: exits (closed form) and replay (M8)                                    #
# --------------------------------------------------------------------------- #
def exits_part(results_root: Path) -> dict[str, Any]:
    f = oyo_factor()
    out: dict[str, Any] = {}
    for (config, kp), b in _bundles(results_root).items():
        c1 = _c1_fail(b)
        kept = ie._kept(config)
        arms: dict[str, Any] = {
            "adopted": _outcomes(b.init, c1, ~b.accept),
        }
        if config == "undrained":
            arms["OYO-matched toe pressure"] = {
                "factor": f[kp],
                **_outcomes(_gate(b, 1.0 / f[kp]), c1, None),
            }
            for ff in FIELD_FACTORS:
                arms[f"toe pressure / {ff:g}"] = _outcomes(_gate(b, 1.0 / ff), c1, None)
            for label, m_d, m_g in BLANKET_ARMS:
                arms[label] = _outcomes(_blanket_gate(b, m_d, m_g), c1, None)
            # Prior means of the gate ingredients at the 2016 peak.
            arms["prior_mean_gate_head_m"] = float(np.mean(b.r_e) * (b.peak - b.z_toe))
            arms["prior_mean_weight_head_m"] = float(np.mean(b.weight_head))
        if config == "berm" and kp in OYO_RELIEF:
            rel = OYO_RELIEF[kp]
            arms[f"OYO drain design, {100 * rel:.0f} % relief"] = {
                "relief": rel,
                **_outcomes(_gate(b, kept * (1.0 - rel)), c1, None),
            }
            if kp == 58.8:
                # Both readings at once: OYO's toe pressure and OYO's drain.
                arms["OYO drain design and OYO-matched toe pressure"] = _outcomes(
                    _gate(b, kept * (1.0 - rel) / f[kp]), c1, None
                )
        out[f"{config} {_label(kp)}"] = arms
        print(f"  exits {config} {_label(kp)}: done", flush=True)
    return out


def replay_part(results_root: Path, data_root: Path) -> dict[str, Any]:
    f = oyo_factor()
    out: dict[str, Any] = {}
    for (_, kp), b in _bundles(results_root, configs=("undrained",)).items():
        t0 = time.time()
        rec = _record(kp, data_root)
        fail, heave = _replay(b, rec, 1.0 / f[kp])
        closed = _gate(b, 1.0 / f[kp])
        if not np.array_equal(heave, closed):
            raise SystemExit(f"{_label(kp)}: relieved replay gate != closed form")
        out[_label(kp)] = {
            "factor": f[kp],
            "relief_knob": 1.0 / f[kp],
            "breach_rows": int(fail.sum()),
            **_outcomes(heave, _c1_fail(b), fail),
            "seconds": time.time() - t0,
        }
        print(f"  replay {_label(kp)}: breach {fail.mean():.5f}", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: antecedent stage                                                       #
# --------------------------------------------------------------------------- #
def antecedent_part(data_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for kp in KPS:
        rec = _record(kp, data_root)
        h = np.asarray(rec.h, dtype=np.float64)
        dt_h = float(rec.native_dt) / 3600.0
        rel = h - Z_TOE[kp]
        above = rel > 0.0
        i_peak = int(np.argmax(h))
        # The final rise: the last upward crossing of the toe before the peak.
        ups = np.nonzero(above[1:] & ~above[:-1])[0] + 1
        ups = ups[ups <= i_peak]
        i_cross = int(ups[-1]) if ups.size else i_peak
        n48 = int(round(48.0 / dt_h))
        n168 = int(round(168.0 / dt_h))
        w48 = rel[max(0, i_cross - n48) : i_cross]
        w168 = rel[max(0, i_cross - n168) : i_cross]
        out[_label(kp)] = {
            "final_crossing_hour": i_cross * dt_h,
            "mean_stage_minus_toe_48h_before_m": float(np.mean(w48)),
            "min_stage_minus_toe_48h_before_m": float(np.min(w48)),
            "max_stage_minus_toe_week_before_m": float(np.max(w168)),
            "hours_within_1m_below_toe_week_before": float(
                np.count_nonzero(w168 > -1.0) * dt_h
            ),
            "record_start_stage_minus_toe_m": float(rel[0]),
            "hours_above_toe": float(np.count_nonzero(above) * dt_h),
        }
        print(f"  antecedent {_label(kp)}: {out[_label(kp)]}", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Part: design-grid consequence                                                #
# --------------------------------------------------------------------------- #
def design_part(results_root: Path) -> dict[str, Any]:
    from bep_reliability_engine.evaluator import evaluate_batch_diagnostics
    from bep_reliability_engine.gap_decomposition import sustained_peak_record
    from bep_reliability_engine.run import conditioning_hydrographs_for_config

    f = oyo_factor()
    out: dict[str, Any] = {}
    for (_, kp), b in _bundles(results_root, configs=("undrained",)).items():
        run = b.run
        cfg = run.config
        i = int(np.argmin(np.abs(b.grid - DESIGN_GRID[kp])))
        level = float(b.grid[i])
        records = conditioning_hydrographs_for_config(cfg)
        dt = float(cfg.timestepper.target_dt_seconds or 225.0)

        def call(record, relief):
            return evaluate_batch_diagnostics(
                run.theta,
                record,
                run.geometry,
                l_ini=0.0,
                seepage_length_samples=run.seepage_length_samples,
                alpha_exponent=cfg.alpha_exponent,
                theta_repose_rad=cfg.theta_repose_rad,
                relative_density=cfg.relative_density_insitu,
                foreland_open=cfg.foreland_treatment == "open_entry",
                progression_backend="numpy",
                model_factor_samples=run.model_factor_samples,
                critical_length_factor=cfg.critical_length_factor,
                toe_gradient_relief_factor=relief,
                foreland_seepage_credit=cfg.foreland_seepage_credit,
            )

        t0 = time.time()
        base = call(records[i], None)
        trans0 = np.asarray(base.failure_trans, dtype=bool)
        if not np.array_equal(trans0, b.tran[:, i]):
            raise SystemExit(f"{_label(kp)}: design-grid transient not reproduced")
        relieved = call(records[i], 1.0 / f[kp])
        crack = (level - b.z_toe) - CRACK * b.theta[:, b.names.index("D_bl")]
        held0 = call(sustained_peak_record(level, dt_s=dt), None)
        gate0 = np.asarray(held0.heave_occurred, dtype=bool)
        static0 = gate0 & (crack > np.asarray(held0.H_c_transient))
        if not np.array_equal(static0, b.c3b[:, i]):
            raise SystemExit(f"{_label(kp)}: same-head static not reproduced")
        held = call(sustained_peak_record(level, dt_s=dt), 1.0 / f[kp])
        gate = np.asarray(held.heave_occurred, dtype=bool)
        static_f = gate & (crack > np.asarray(held.H_c_transient))
        trans_f = np.asarray(relieved.failure_trans, dtype=bool)
        if np.any(trans_f & ~static_f):
            raise SystemExit(f"{_label(kp)}: relieved containment broken")
        out[_label(kp)] = {
            "stage_m": level,
            "factor": f[kp],
            "P_static_adopted": float(np.mean(static0)),
            "P_trans_adopted": float(np.mean(trans0)),
            "k_trans_adopted": int(trans0.sum()),
            "P_gate_adopted": float(np.mean(gate0)),
            "P_static_oyo": float(np.mean(static_f)),
            "P_trans_oyo": float(np.mean(trans_f)),
            "k_trans_oyo": int(trans_f.sum()),
            "k_static_oyo": int(static_f.sum()),
            "P_gate_oyo": float(np.mean(gate)),
            "seconds": time.time() - t0,
        }
        print(f"  design {_label(kp)}: {out[_label(kp)]}", flush=True)
    return out


# --------------------------------------------------------------------------- #
# Report                                                                       #
# --------------------------------------------------------------------------- #
#: Wall-clock fields stay in the stage files, not in the committed record.
_CLOCK_KEYS = frozenset({"seconds", "replay_seconds"})


def _round(obj: Any, sig: int = 6) -> Any:
    if isinstance(obj, float):
        return float(f"{obj:.{sig}g}")
    if isinstance(obj, dict):
        return {k: _round(v, sig) for k, v in obj.items() if k not in _CLOCK_KEYS}
    if isinstance(obj, list):
        return [_round(v, sig) for v in obj]
    return obj


def _verdicts(src, ex, rp, ant, des) -> dict[str, Any]:
    v: dict[str, Any] = {}
    oyo = {k: rp[_label(k)]["exit"] for k in KPS}
    v["P1"] = {
        "held": all(oyo[k] < 0.05 for k in (57.4, 60.0, 62.0)) and oyo[58.8] > 0.90,
        "exit_shares": oyo,
    }
    b58 = ex["berm KP 58.8"]
    b60 = ex["berm KP 60.0"]
    k58 = [k for k in b58 if k.startswith("OYO drain design,")][0]
    k60 = [k for k in b60 if k.startswith("OYO drain design,")][0]
    v["P2"] = {
        "held": b58[k58]["exit"] < 0.01 and b60[k60]["exit"] > 0.95,
        "kp58_8": b58[k58]["exit"],
        "kp60_0": b60[k60]["exit"],
    }
    und = {k: ex[f"undrained {_label(k)}"] for k in KPS}
    x2 = {k: und[k]["D_bl x 2"]["exit"] for k in KPS}
    x15 = {k: und[k]["D_bl x 1.5"]["exit"] for k in KPS}
    hv = {k: und[k]["gamma'_bl x 1.25"]["exit"] for k in KPS}
    ad = {k: und[k]["adopted"]["exit"] for k in KPS}
    v["P3"] = {
        "held": all(x2[k] < ad[k] for k in KPS)
        and all(x2[k] > 0.25 and x15[k] > 0.80 for k in (58.8, 60.0))
        and all(hv[k] >= x2[k] for k in KPS),
        "x2": x2,
        "x1.5": x15,
        "heavier": hv,
    }
    m48 = {k: ant[_label(k)]["mean_stage_minus_toe_48h_before_m"] for k in KPS}
    v["P4"] = {"held": all(m48[k] >= -1.5 for k in KPS), "mean_48h": m48}
    d60 = des["KP 60.0"]
    d58 = des["KP 58.8"]
    v["P5"] = {
        "held": d60["P_trans_oyo"] < d60["P_trans_adopted"] / 10.0
        and d58["P_trans_oyo"] > 0.75 * d58["P_trans_adopted"],
        "kp60_0": [d60["P_trans_adopted"], d60["P_trans_oyo"]],
        "kp58_8": [d58["P_trans_adopted"], d58["P_trans_oyo"]],
    }
    dur = {k: rp[_label(k)]["held_only_by_duration"] for k in KPS}
    br58 = rp["KP 58.8"]["breach"]
    ad58 = ex["undrained KP 58.8"]["adopted"]["breach"]
    v["P6"] = {
        "held": all(dur[k] < 0.01 for k in (57.4, 60.0, 62.0))
        and abs(br58 - ad58) <= 0.1 * ad58,
        "held_only_by_duration": dur,
        "kp58_8_breach": [ad58, br58],
    }
    return v


def report_part() -> None:
    src = _read_stage("sources")
    gate = _read_stage("gate")
    ex = _read_stage("exits")
    rp = _read_stage("replay")
    ant = _read_stage("antecedent")
    des = _read_stage("design")
    payload = {
        "study": "docs/decisions/why-no-piping-2016-study.md",
        "driver": "scripts/why_no_piping_2016_study.py",
        "comparator": "ADR-0055 same head and same gate",
        "sources": src,
        "gate": gate,
        "exits": ex,
        "replay_oyo_matched": rp,
        "antecedent": ant,
        "design_grid_oyo_matched": des,
        "verdicts": _verdicts(src, ex, rp, ant, des),
    }
    EVIDENCE.write_text(json.dumps(_round(payload), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {EVIDENCE.relative_to(REPO)}")


PARTS = ("sources", "gate", "exits", "replay", "antecedent", "design", "report")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("part", choices=(*PARTS, "all"))
    ap.add_argument("--results-root", type=Path, default=REPO / "results")
    ap.add_argument("--data-root", type=Path, default=REPO / "data" / "raw")
    a = ap.parse_args(argv)
    todo = PARTS if a.part == "all" else (a.part,)
    for part in todo:
        t0 = time.time()
        print(f"[{part}]", flush=True)
        if part == "sources":
            _write_stage(part, sources_part())
        elif part == "gate":
            _write_stage(part, gate_part(a.results_root, a.data_root))
        elif part == "exits":
            _write_stage(part, exits_part(a.results_root))
        elif part == "replay":
            _write_stage(part, replay_part(a.results_root, a.data_root))
        elif part == "antecedent":
            _write_stage(part, antecedent_part(a.data_root))
        elif part == "design":
            _write_stage(part, design_part(a.results_root))
        else:
            report_part()
        print(f"[{part}] {time.time() - t0:.0f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
