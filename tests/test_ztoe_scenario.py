"""ADR-0046 epistemic exit-datum scenario (z_toe +/- 0.3 m).

Locks the scenario contract:

* default ``z_toe_delta_m = 0.0`` is the baseline, bit-identical (geometry
  equals the config snapshot);
* a nonzero delta shifts ONLY the replay geometry — the config snapshot,
  its hash check and the retained Phase 1 matrices stay untouched;
* the physics responds exactly as the datum algebra says: Z_static shifts
  by exactly +delta, and the transient failure set nests monotonically
  (raising the toe can only remove failures, lowering it only add);
* scenario Phase 2 outputs are name-suffixed and metadata-stamped so they
  can never masquerade as the baseline posterior.
"""

from __future__ import annotations

import numpy as np
import pytest

from bayesian_reliability_updating.cli import _build_parser
from bayesian_reliability_updating.pipeline import (
    Phase2Settings,
    _output_paths,
    run_survival_update,
)
from bayesian_reliability_updating.replay import load_phase1_run, replay_event

from .phase2_helpers import Z_TOE, generate_stub_phase1, stressing_record


@pytest.fixture(scope="module")
def stub_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ztoe_scenario")
    return generate_stub_phase1(tmp, cross_section_id="ztoe_scenario_xs")


def test_default_delta_is_baseline(stub_path) -> None:
    run = load_phase1_run(stub_path)
    assert run.z_toe_delta_m == 0.0
    assert run.geometry["z_toe"] == run.config.geometry.z_toe == Z_TOE


def test_delta_shifts_geometry_not_config(stub_path) -> None:
    run = load_phase1_run(stub_path, z_toe_delta_m=+0.3)
    assert run.z_toe_delta_m == pytest.approx(0.3)
    assert run.geometry["z_toe"] == pytest.approx(Z_TOE + 0.3)
    # The config snapshot is untouched (and its hash check passed above).
    assert run.config.geometry.z_toe == Z_TOE


def test_replay_z_static_shifts_exactly_and_failures_nest(stub_path) -> None:
    record = stressing_record(9.0)
    base = replay_event(load_phase1_run(stub_path), record)

    up = replay_event(load_phase1_run(stub_path, z_toe_delta_m=+0.3), record)
    np.testing.assert_allclose(
        up.diagnostics.Z_static, base.diagnostics.Z_static + 0.3, atol=1e-12
    )
    # Raising the toe lowers every head: failures can only disappear.
    assert not np.any(up.diagnostics.failure_trans & ~base.diagnostics.failure_trans)

    down = replay_event(load_phase1_run(stub_path, z_toe_delta_m=-0.3), record)
    np.testing.assert_allclose(
        down.diagnostics.Z_static, base.diagnostics.Z_static - 0.3, atol=1e-12
    )
    assert not np.any(base.diagnostics.failure_trans & ~down.diagnostics.failure_trans)
    # The scenario genuinely bites on this stressing record.
    assert down.diagnostics.failure_trans.sum() > base.diagnostics.failure_trans.sum()


def test_scenario_output_paths_are_name_segregated(stub_path) -> None:
    baseline = _output_paths(stub_path, Phase2Settings())
    scenario = _output_paths(stub_path, Phase2Settings(z_toe_delta_m=+0.3))
    negative = _output_paths(stub_path, Phase2Settings(z_toe_delta_m=-0.3))
    assert baseline["h5"].name == f"{stub_path.stem}_posterior.h5"
    assert scenario["h5"].name == f"{stub_path.stem}_ztoe_plus0.30m_posterior.h5"
    assert negative["h5"].name == f"{stub_path.stem}_ztoe_minus0.30m_posterior.h5"


def test_run_survival_update_scenario_stamps_and_moves(stub_path) -> None:
    record = stressing_record(9.0)
    common = dict(
        figures=False, trace_breach_times=False, n_bootstrap=10, overwrite=True
    )
    base = run_survival_update(
        stub_path,
        settings=Phase2Settings(**common),
        event_records=[record],
        persist=False,
    )
    up = run_survival_update(
        stub_path,
        settings=Phase2Settings(z_toe_delta_m=+0.3, **common),
        event_records=[record],
        persist=False,
    )
    scenario = up.metadata["phase2"]["z_toe_scenario"]
    assert scenario["delta_m"] == pytest.approx(0.3)
    assert scenario["z_toe_config_m_msl"] == pytest.approx(Z_TOE)
    assert scenario["z_toe_replay_m_msl"] == pytest.approx(Z_TOE + 0.3)
    assert base.metadata["phase2"]["z_toe_scenario"]["delta_m"] == 0.0

    # Raising the datum weakens the evidence: rejection can only shrink.
    r_base = base.metadata["phase2"]["posterior"]["rejection_fraction"]
    r_up = up.metadata["phase2"]["posterior"]["rejection_fraction"]
    assert r_up <= r_base


def test_cli_flag_parses() -> None:
    args = _build_parser().parse_args(["some.h5", "--ztoe-delta", "-0.3"])
    assert args.ztoe_delta == pytest.approx(-0.3)
    assert _build_parser().parse_args(["some.h5"]).ztoe_delta == 0.0
