"""Pin the 2016 initiation-evidence study (Pol comments 3, 6, 7, 9 and 11).

Checked without rerunning anything:

* the committed record's own gates held: the closed-form gate reproduced every
  stored 2016 initiation flag, every breach lies inside initiation and inside
  same-head failure, the rebuilt no-breach posterior and its annual rows
  reproduce production, and the hazard cache was untouched;
* the structure the thesis relies on: initiation does not depend on the d70
  reading; the four-way decomposition of the 2016 outcome sums to one; the
  strict filter keeps exactly the rows with no exit; a detection probability
  ``p_d`` moves no probability by more than ``1 / (1 - p_d)``;
* the quoted values: the initiation shares, the strict-filter annual factors,
  the 75-year return period on the rating axis, the crest margins, and that
  piping keeps the lead in every cell under the strict filter.

Driver ``scripts/initiation_evidence_2016_study.py``; evidence
``docs/decisions/initiation-evidence-2016-study.{md,json}``. Every path read
here is tracked, so nothing skips (conventions section 9.4), except the one
row-level check marked below, which reads gitignored production results.
"""

from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
import pytest

from bep_reliability_engine.constants import GAMMA_W

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "docs" / "decisions" / "initiation-evidence-2016-study.json"
KPS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_record_stays_under_the_large_file_hook() -> None:
    assert RECORD.stat().st_size < 500_000


def test_replay_gates_held(record) -> None:
    for key, gate in record["gates"]["replay"].items():
        assert gate["closed_form_initiation_mismatches"] == 0, key
        assert gate["breaches_without_initiation"] == 0, key
        assert gate["transient_breaches_outside_same_head_failure"] == 0, key
        if key.startswith("undrained"):
            assert gate["rebuilt_posterior_curve"] == "identical to production"


def test_annual_gates_held(record) -> None:
    gates = record["gates"]["annual"]
    assert gates["gate_iii"]["passed"] is True
    assert gates["gate_iii"]["rows_compared"] == 912
    assert gates["hazard_cache_unchanged"] is True
    cells = record["annual"]["cells"]
    for key, cell in cells.items():
        if key.startswith("undrained pd0 T"):
            prod = cells[key.replace("undrained pd0 T", "production")]
            assert cell["p_system"] == prod["p_system"], key
            assert cell["p_bep"] == prod["p_bep"], key


def test_initiation_does_not_depend_on_the_d70_reading(record) -> None:
    ini = record["initiation"]
    for kp in KPS:
        m, b = ini[f"undrained {kp}"], ini[f"bulk {kp}"]
        assert m["P_initiation_prior"] == b["P_initiation_prior"], kp
        assert m["n_no_initiation"] == b["n_no_initiation"], kp


def test_decomposition_sums_to_one(record) -> None:
    for key, entry in record["initiation"].items():
        total = sum(entry["decomposition"].values())
        assert total == pytest.approx(1.0, abs=1e-5), key
        assert entry["decomposition"]["breach"] == pytest.approx(
            entry["P_breach"], abs=1e-6
        ), key


def test_initiation_shares_as_quoted(record) -> None:
    s = record["summary"]["P_initiation_2016_as_if_undrained"]
    assert [round(100 * s[kp], 1) for kp in KPS] == [66.4, 99.6, 99.3, 39.6]
    berm = record["summary"]["P_initiation_2016_berm_relief"]
    assert berm["berm_relief_60pct KP 58.8"] < 0.02
    assert berm["berm_relief_60pct KP 60.0"] < 0.01
    assert berm["berm_relief_80pct KP 58.8"] == 0.0


def test_strict_filter_keeps_the_rows_without_an_exit(record) -> None:
    for kp in KPS:
        cond = record["conditioning"][f"undrained {kp}"]["arms"]["1"]
        ini = record["initiation"][f"undrained {kp}"]
        assert cond["sum_weights"] == pytest.approx(ini["n_no_initiation"]), kp


def test_detection_probability_bound(record) -> None:
    for key, entry in record["conditioning"].items():
        assert entry["H3_bound_violations"] == 0, key
    curve = record["annual"]["detection_probability_curve"]
    for key, cell in curve.items():
        p_d = float(key.split(" ")[0])
        rel = cell["relative_to_no_breach"]
        if rel is None or p_d >= 1.0:
            continue
        assert 1.0 - p_d - 1e-9 <= rel <= 1.0 / (1.0 - p_d) + 1e-9, key


def test_strict_filter_lowers_but_keeps_piping_leading(record) -> None:
    rel = record["summary"]["annual_bep_relative_to_no_breach_historical"]
    strict = rel["undrained pd1 T"]
    assert [round(strict[kp], 2) for kp in KPS] == [0.56, 0.40, 0.24, 0.49]
    half = rel["undrained pd0.5 T"]
    assert half["KP 58.8"] > 0.99 and half["KP 60.0"] > 0.99
    lead = record["summary"]["leading_mechanism"]
    for cell, mech in lead["production"].items():
        if mech == "piping":
            assert lead["undrained pd1 T"][cell] == "piping", cell
    assert record["verdicts"]["H4"]["cells_where_piping_lost_the_lead"] == []


def test_return_period_and_where_probability_is_earned(record) -> None:
    rp = record["summary"]["return_period_2016_rating_axis_yr"]
    assert rp["historical"] == pytest.approx(75.0)
    assert rp["+4K"] == pytest.approx(5400 / 422, rel=1e-5)
    shares = record["summary"]["share_annual_bep_from_years_above_2016"]
    assert min(v["rating_axis"] for v in shares.values()) > 0.80
    assert min(v["trace_axis"] for v in shares.values()) > 0.80
    margins = record["summary"]["crest_margins_m"]
    assert [round(margins[kp]["below_design_crest"], 2) for kp in KPS] == [
        1.05,
        1.78,
        1.95,
        2.16,
    ]


def test_pre_registered_verdicts(record) -> None:
    v = record["verdicts"]
    assert v["H1"]["held"] and v["H2"]["held"] and v["H3"]["held"]
    assert v["H4"]["held"] and v["H6"]["held"]
    assert v["H5"]["share_part_held"] is True
    # Recorded as failed on the trace-anchored peaks; never quietly flipped.
    assert v["H5"]["return_period_part_held"] is False


RESULTS = REPO / "results"


@pytest.mark.skipif(
    not (
        RESULTS / "phase2" / "tokachi_kp58.8_historical_matrix_posterior.h5"
    ).is_file(),
    reason="production replays are untracked (gitignored results/)",
)
def test_closed_form_gate_on_the_persisted_replay() -> None:
    meta = json.loads(
        (RESULTS / "tokachi_kp58.8_historical_matrix.json").read_text(encoding="utf-8")
    )
    z_toe = float(meta["config"]["geometry"]["z_toe"])
    post = RESULTS / "phase2" / "tokachi_kp58.8_historical_matrix_posterior.h5"
    with h5py.File(post, "r") as h5:
        (event,) = list(h5["events"].keys())
        r_e = h5[f"events/{event}/r_e"][:]
        stored = h5[f"events/{event}/initiation"][:].astype(bool)
        names = [x.decode() if isinstance(x, bytes) else x for x in h5["param_names"]]
        theta = h5["theta_matrix"][:]
    weight = (
        theta[:, names.index("gamma_bl_sub")] / GAMMA_W * theta[:, names.index("D_bl")]
    )
    assert np.array_equal(r_e * (40.75 - z_toe) > weight, stored)
