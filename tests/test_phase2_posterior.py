"""PosteriorResult persistence round-trip and pipeline integration (stub path).

Runs the full pipeline (``run_survival_update``) on the genuine stub-path
Phase 1 result with injected synthetic events, persists, reloads and
compares. Figures are exercised once (smoke) and written into the session
temporary directory.
"""

from __future__ import annotations

import numpy as np
import pytest

from bayesian_reliability_updating.pipeline import (
    Phase2Settings,
    run_survival_update,
)
from bayesian_reliability_updating.posterior import PosteriorResult
from tests.phase2_helpers import (
    Z_TOE,
    flat_record,
    generate_stub_phase1,
    stressing_record,
)


@pytest.fixture(scope="module")
def phase1_path(tmp_path_factory: pytest.TempPathFactory):
    return generate_stub_phase1(tmp_path_factory.mktemp("phase1_stub_pipe"))


@pytest.fixture(scope="module")
def outputs(phase1_path, tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("phase2_out")
    settings = Phase2Settings(
        output_dir=str(out_dir),
        figures=True,
        trace_breach_times=True,
        n_bootstrap=50,
        verify_by_reevaluation=True,
    )
    events = [
        stressing_record(8.5, hours=96, event_id="pipe_event_a"),
        flat_record(Z_TOE + 0.5, event_id="pipe_event_b"),
    ]
    result = run_survival_update(phase1_path, settings=settings, event_records=events)
    return result, out_dir, phase1_path


def test_pipeline_persists_the_pair_and_figures(outputs) -> None:
    result, out_dir, phase1_path = outputs
    stem = phase1_path.stem
    assert (out_dir / f"{stem}_posterior.h5").exists()
    assert (out_dir / f"{stem}_posterior.json").exists()
    figures = list((out_dir / "figures").glob("*.png"))
    assert len(figures) >= 5


def test_pipeline_metadata_carries_full_provenance(outputs) -> None:
    result, _, phase1_path = outputs
    meta = result.metadata
    assert meta["phase1"]["config_hash"]
    assert len(meta["phase1"]["h5_sha256"]) == 64
    assert meta["phase1"]["theta_verified"] is True
    assert meta["phase2"]["l_ini_m"] == 0.0
    assert meta["phase2"]["recovery_r_l"] == 0.0
    chain = meta["phase2"]["event_chain"]
    assert [entry["event_id"] for entry in chain] == [
        "pipe_event_a",
        "pipe_event_b",
    ]
    assert meta["phase2"]["verification"]["verified"] is True
    assert "c_e_headline" in meta["analysis"]
    assert "C_e" in meta["analysis"]["marginals"]


def test_pipeline_chain_composes_the_masks(outputs) -> None:
    result, _, _ = outputs
    joint = (
        result.events["pipe_event_a"].accept_trans
        & result.events["pipe_event_b"].accept_trans
    )
    np.testing.assert_array_equal(result.accept, joint)
    assert result.n_accepted == int(joint.sum())


def test_pipeline_breach_times_only_for_rejected_rows(outputs) -> None:
    result, _, _ = outputs
    arrays = result.events["pipe_event_a"]
    assert arrays.t_breach is not None
    rejected = ~arrays.accept_trans
    assert np.all(np.isfinite(arrays.t_breach[rejected]))
    assert np.all(np.isnan(arrays.t_breach[~rejected]))


def test_posterior_result_round_trips_exactly(outputs, tmp_path) -> None:
    result, out_dir, phase1_path = outputs
    loaded = PosteriorResult.load(out_dir / f"{phase1_path.stem}_posterior.h5")
    np.testing.assert_array_equal(loaded.theta_matrix, result.theta_matrix)
    assert loaded.param_names == result.param_names
    np.testing.assert_array_equal(loaded.accept, result.accept)
    np.testing.assert_array_equal(
        loaded.seepage_length_samples, result.seepage_length_samples
    )
    assert set(loaded.events) == set(result.events)
    for event_id, arrays in result.events.items():
        loaded_arrays = loaded.events[event_id]
        np.testing.assert_array_equal(loaded_arrays.accept_trans, arrays.accept_trans)
        np.testing.assert_array_equal(loaded_arrays.accept_static, arrays.accept_static)
        np.testing.assert_array_equal(loaded_arrays.Z_transient, arrays.Z_transient)
        np.testing.assert_array_equal(loaded_arrays.l_e_final, arrays.l_e_final)
        np.testing.assert_array_equal(loaded_arrays.r_e, arrays.r_e)
        np.testing.assert_array_equal(loaded_arrays.t_breach, arrays.t_breach)
    np.testing.assert_array_equal(
        loaded.fragility.P_f_trans_post_raw, result.fragility.P_f_trans_post_raw
    )
    np.testing.assert_array_equal(
        loaded.fragility.P_f_static_post_raw,
        result.fragility.P_f_static_post_raw,
    )
    for key in ("transient", "static"):
        np.testing.assert_array_equal(
            loaded.fragility.binomial_ci[key][0],
            result.fragility.binomial_ci[key][0],
        )
        np.testing.assert_array_equal(
            loaded.fragility.bootstrap_bands[key][1],
            result.fragility.bootstrap_bands[key][1],
        )
    assert loaded.metadata == result.metadata
    # Optional fits round-trip (None or parameter-equal).
    for attr in ("P_f_trans_post_fit", "P_f_static_post_fit"):
        original = getattr(result.fragility, attr)
        reloaded = getattr(loaded.fragility, attr)
        if original is None:
            assert reloaded is None
        else:
            assert reloaded is not None
            assert reloaded.mu == original.mu
            assert reloaded.sigma == original.sigma
            assert reloaded.datum_m == original.datum_m


def test_pipeline_refuses_overwrite_without_flag(outputs) -> None:
    result, out_dir, phase1_path = outputs
    settings = Phase2Settings(output_dir=str(out_dir), figures=False)
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        run_survival_update(
            phase1_path,
            settings=settings,
            event_records=[flat_record(Z_TOE, event_id="x")],
        )
