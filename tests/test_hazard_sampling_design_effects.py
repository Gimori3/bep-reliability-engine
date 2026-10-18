"""Design effects of the ensemble nesting (scripts/hazard_sampling_design_effects.py).

The estimator is checked on synthetic balanced data with a known structure, and
the committed record is pinned to the values thesis B.1 prints since R57
(2026-10-18): member 1.00 to 1.29, SST pattern 3.2 to 8.9 on the adopted curves.
No sweep is run.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/decisions/annualisation-design-effects.json"


def _module():
    path = ROOT / "scripts/hazard_sampling_design_effects.py"
    spec = importlib.util.spec_from_file_location("hazard_design_effects", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_icc_is_zero_without_clustering_and_one_with_identical_groups():
    mod = _module()
    rng = np.random.default_rng(1)
    groups = [f"g{i}" for i in range(6) for _ in range(900)]
    iid = rng.normal(size=5400)
    out = mod.icc_design_effect(iid, groups)
    assert abs(out["icc"]) < 0.01
    assert 1.0 <= out["design_effect_floored"] < 5.0
    const = np.repeat(rng.normal(size=6), 900)
    assert mod.icc_design_effect(const, groups)["icc"] == pytest.approx(1.0)
    assert mod.icc_design_effect(const, groups)["design_effect"] == pytest.approx(900.0)


def test_unbalanced_groups_are_refused():
    mod = _module()
    with pytest.raises(ValueError):
        mod.icc_design_effect(np.zeros(5), ["a", "a", "b", "b", "b"])


def test_record_matches_the_printed_ranges():
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    adopted = rec["summary"]["adopted"]
    assert [round(x, 2) for x in adopted["member_range"]] == [1.0, 1.29]
    assert [round(x, 1) for x in adopted["sst_pattern_range"]] == [3.2, 8.9]
    # KP 57.4 under warming is inside the range on the corrected thickness.
    kp57 = rec["cells"]["adopted +4K KP 57.4"]["by_sst_pattern"]["design_effect"]
    assert kp57 == pytest.approx(4.02, abs=0.01)
