"""Pin the round-2 results studies (Pol annotations A19, A13, A35).

Checked without rerunning the sweeps:

* the pure arithmetic the studies rest on: the first-breach split sums to the
  two-branch union, the pairwise "pipe first" probability, the correlation-ratio
  probe and the two-stratum terms;
* the committed records' own gates and the structure the thesis quotes: every
  attribution of the crest study sums to the system probability and the
  time-ordered share lies between the overflow-first and piping-first ones; the
  adopted table (ADR-0056 and ADR-0057) carries the prior at the drained sections
  and the posterior elsewhere; the truncated seepage-length arms are nested;
* the quoted values: KP 62.0 under +4 K is an overflow lead by first breach, the
  drained sections' prior values, the bounded-prior design effects.

Driver ``scripts/results_annotations_study.py``; evidence
``docs/decisions/{crest-attribution-study,drained-section-conditioning-*,
seepage-length-lower-tail-*}.json``. Every record read here is tracked, so
nothing skips, except the overflow re-run, which needs the gitignored d4PDF
band workbooks.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "docs" / "decisions"
KPS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")


def _record(name: str) -> dict:
    return json.loads((DEC / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def driver():
    path = REPO / "scripts" / "results_annotations_study.py"
    spec = importlib.util.spec_from_file_location("results_annotations_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "name",
    [
        "crest-attribution-study",
        "drained-section-conditioning-study",
        "drained-section-conditioning-adopted",
        "drained-section-conditioning-alternatives",
        "seepage-length-lower-tail-study",
        "seepage-length-lower-tail-adopted",
    ],
)
def test_records_stay_under_the_large_file_hook(name) -> None:
    assert (DEC / f"{name}.json").stat().st_size < 500_000


# --------------------------------------------------------------------------- #
# Pure arithmetic                                                             #
# --------------------------------------------------------------------------- #
def test_first_breach_split_sums_to_the_union(driver) -> None:
    rng = np.random.default_rng(1)
    pb, po, pi = rng.random(500), rng.random(500), rng.random(500)
    ab, ao = driver._first_breach(pb, po, pi)
    np.testing.assert_allclose(ab + ao, 1 - (1 - pb) * (1 - po), rtol=0, atol=1e-15)
    lo_b, _ = driver._first_breach(pb, po, np.zeros(500))
    hi_b, _ = driver._first_breach(pb, po, np.ones(500))
    np.testing.assert_allclose(lo_b, pb * (1 - po), atol=1e-15)
    np.testing.assert_allclose(hi_b, pb, atol=1e-15)


def test_pipe_first_probability(driver) -> None:
    inf = np.inf
    assert driver._pi_first(np.array([1.0, 2.0]), np.array([3.0, 4.0])) == 1.0
    assert driver._pi_first(np.array([5.0]), np.array([3.0, 4.0])) == 0.0
    assert driver._pi_first(np.array([3.0]), np.array([3.0])) == 0.5
    # Non-breaching draws are not part of the both-fail pairs.
    assert driver._pi_first(np.array([1.0, inf]), np.array([2.0, inf])) == 1.0
    rng = np.random.default_rng(2)
    a, b = rng.random(300), rng.random(400)
    brute = np.mean(a[:, None] < b[None, :]) + 0.5 * np.mean(a[:, None] == b[None, :])
    assert abs(driver._pi_first(a, b) - brute) < 1e-12


def test_correlation_ratio_probe(driver) -> None:
    rng = np.random.default_rng(3)
    x = rng.random(20_000)
    assert driver._eta2(x > 0.5, x) > 0.9
    assert driver._eta2(rng.random(20_000) > 0.5, x) < 0.01


def test_two_stratum_terms_reconstruct(driver) -> None:
    h = {
        "w_inside": np.array([0.1]),
        "p_inside": np.array([0.3]),
        "p_outside": np.array([0.01]),
    }
    w = {
        "w_inside": np.array([0.2]),
        "p_inside": np.array([0.5]),
        "p_outside": np.array([0.04]),
    }
    q = driver._strata_quantities(h, w)
    p00, p11 = 0.1 * 0.3 + 0.9 * 0.01, 0.2 * 0.5 + 0.8 * 0.04
    assert abs(q["ratio"][0] - p11 / p00) < 1e-12
    assert abs(q["share_long_hist"][0] - 0.03 / p00) < 1e-12
    assert abs(q["freq_factor"][0] - 2.0) < 1e-12


# --------------------------------------------------------------------------- #
# Crest attribution (A19, ADR-0057)                                           #
# --------------------------------------------------------------------------- #
def test_crest_gates_and_attribution_bounds() -> None:
    rec = _record("crest-attribution-study")
    gates = rec["gates"]
    assert gates["production_table"]["passed"] is True
    assert gates["breach_rerun_end_state_equals_M8"] is True
    assert gates["overflow_rerun_equals_model"] is True
    for key, cell in rec["cells"].items():
        assert cell["union_interpolation_rel_dev"] < 5e-3, key
        a = cell["attributions"]
        lo = a["overflow_first"]["bep_share"]
        hi = a["piping_first"]["bep_share"]
        mid = a["time_ordered"]["bep_share"]
        assert lo - 1e-12 <= mid <= hi + 1e-12, key


def test_crest_quoted_values() -> None:
    rec = _record("crest-attribution-study")
    c = rec["cells"]["+4K KP 62.0"]
    assert c["years_above_overflow_crest"] == 62
    assert round(c["bep_share_from_above_overflow_crest"], 2) == 0.61
    to = c["attributions"]["time_ordered"]
    assert round(to["bep_share"], 2) == 0.39
    assert to["bep_share_ci95"][1] < 0.5
    assert to["fraction_replicates_piping_leads"] == 0.0
    for key in ("time_ordered_ovf_minus_1h", "time_ordered_ovf_plus_1h"):
        assert c["attributions"][key]["bep_share_ci95"][1] < 0.5
    h = rec["cells"]["historical KP 62.0"]
    assert round(h["bep_share_from_above_overflow_crest"], 2) == 0.21
    crests = rec["time_order"]["KP 62.0"]["crests"]
    assert crests["grid_attainable_max_m"] - crests["overflow_crest_mean_m"] > 1.8


# --------------------------------------------------------------------------- #
# Drained sections (A13, ADR-0056)                                            #
# --------------------------------------------------------------------------- #
def test_drained_likelihood_ladder() -> None:
    rec = _record("drained-section-conditioning-study")
    pf = rec["per_flood"]
    for kp in ("KP 58.8", "KP 60.0"):
        ladder = [
            pf[f"{n} {kp}"]["rejected_pct"]
            for n in (
                "prior",
                "berm_relief_80pct",
                "berm_relief_60pct",
                "berm_relief_40pct",
                "berm_inert",
                "as_if_undrained",
            )
        ]
        assert ladder == sorted(ladder), kp
    assert round(pf["berm_inert KP 58.8"]["rejected_pct"], 3) == 0.899
    assert round(pf["as_if_undrained KP 58.8"]["rejected_pct"], 3) == 3.813


def test_adopted_table_uses_prior_at_drained_sections() -> None:
    adopted = _record("drained-section-conditioning-adopted")
    drained = _record("drained-section-conditioning-study")["annual"]
    for kp in KPS:
        source = "prior" if kp in ("KP 58.8", "KP 60.0") else "as_if_undrained"
        for scen in ("historical", "+4K"):
            got = adopted["table"][f"{scen} {kp}"]["p_system"]
            want = drained[f"{source} {scen} {kp}"]["p_system"]
            assert got == pytest.approx(want, rel=1e-6), (kp, scen)
    t = adopted["table"]
    assert round(t["historical KP 58.8"]["p_system"] * 1e3, 2) == 6.85
    assert round(t["historical KP 60.0"]["p_system"] * 1e3, 3) == 0.322
    assert t["+4K KP 62.0"]["first_breach_share_ci95"][1] < 0.5
    for kp in KPS[:3]:
        assert t[f"+4K {kp}"]["first_breach_share_bep"] > 0.9
    six = adopted["sixty_year_check"]
    assert round(six["expected_failures_60yr"], 2) == 0.50
    assert round(six["exclusion_over_composed"], 1) == 5.8


# --------------------------------------------------------------------------- #
# Seepage-length lower tail (A35)                                             #
# --------------------------------------------------------------------------- #
def test_truncation_arms_are_nested() -> None:
    rec = _record("seepage-length-lower-tail-study")
    for kp, sec in rec["per_flood"].items():
        tags = sorted(sec["arms"], key=float)
        kept = [sec["arms"][t]["kept_fraction"] for t in tags]
        assert kept == sorted(kept, reverse=True), kp
        assert sec["arms"]["0.00"]["kept_fraction"] == 1.0


def test_bounded_prior_quoted_values() -> None:
    rec = _record("seepage-length-lower-tail-study")
    arm = rec["per_flood"]["KP 58.8"]["arms"]["0.85"]
    assert round(arm["design_grid"]["dbeta"], 2) == 0.83
    assert round(arm["design_grid"]["ratio"], 2) == 3.20
    assert round(arm["rejected_pct"], 2) == 1.01
    anchors = rec["anchors_1e6"]
    assert anchors["KP 62.0 46.39 t0.00"]["k_trans"] == 51
    assert anchors["KP 62.0 46.39 t0.85"]["k_trans"] == 0
    adopted = _record("seepage-length-lower-tail-adopted")["annual"]
    rel = [
        round(adopted[f"t0.85 historical {kp}"]["bep_relative_to_adopted"], 2)
        for kp in KPS
    ]
    assert rel == [0.51, 0.69, 0.60, 0.51]


def test_overflow_rerun_reproduces_the_model(driver) -> None:
    if not (REPO / "data" / "raw" / "hydrographs").is_dir():
        pytest.skip("untracked d4PDF band workbooks not present (data/raw)")
    seg, draws, shape, h_base, dt, _gen = driver._overflow_setup(62.0)
    p, t, _ = driver._overflow_times(49.0, seg, draws, shape, h_base, dt)
    assert 0.0 < p < 1.0
    assert np.isfinite(t).mean() == pytest.approx(p)
