"""End-to-end Phase 2 test on a genuine small-N production-path Phase 1 run.

Runs the ACTUAL Phase 1 engine (canonical d4PDF shape, production KP 58.8
config, ADR-0030 225 s grid) at small N, then the full Phase 2 pipeline
against the real 2016 observed event (trace-anchored Obihiro construction).
This exercises every genuine interface end to end: band-workbook
resolution, rating CSVs, the processed 2016 extracts, config-snapshot
reconstruction, stochastic-L regeneration, the 225 s replay, filtering,
decomposition, posterior fragility and persistence.

Requires the untracked ``data/raw`` drop (rating curves + d4PDF band
workbooks); skips on fresh clones, mirroring the Phase 1 real-path tests.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bayesian_reliability_updating.pipeline import (
    Phase2Settings,
    run_survival_update,
)
from bayesian_reliability_updating.posterior import PosteriorResult
from bep_reliability_engine.config import Config
from bep_reliability_engine.run import run_fragility_analysis

_RATING = Path("data/raw/rating_curves/HQrelation_TokachiRiv_2017.csv")
_BAND = Path(
    "data/raw/hydrographs/Hydro Data, HPB, Tokachi Riv. KP056.20-KP061.80.xlsx"
)
_PROCESSED = Path("data/processed/2016_event/stage_hourly_Tokachi_201608.csv")

requires_real_data = pytest.mark.skipif(
    not (_RATING.exists() and _BAND.exists() and _PROCESSED.exists()),
    reason="untracked data/raw drop or processed 2016 extracts not present",
)

_SMALL_N = 1000


@pytest.fixture(scope="module")
def phase1_small(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A genuine KP 58.8 production-config run at small N."""
    config = Config.from_yaml("configs/kp58_8_historical_matrix.yaml")
    small = config.model_dump(mode="json")
    small["mc"]["n_samples"] = _SMALL_N
    config_small = Config.model_validate(small)
    out = tmp_path_factory.mktemp("phase1_real") / "tokachi_kp58.8_matrix_smallN.h5"
    run_fragility_analysis(
        config_small, n_jobs=1, progress=False, output_path=out, overwrite=True
    )
    return out


@requires_real_data
def test_end_to_end_2016_update_at_kp58_8(
    phase1_small: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    out_dir = tmp_path_factory.mktemp("phase2_real")
    settings = Phase2Settings(
        output_dir=str(out_dir),
        figures=True,
        trace_breach_times=True,
        n_bootstrap=200,
    )
    result = run_survival_update(phase1_small, settings=settings)

    # The replay ran on the ADR-0030 grid with the trace-anchored record.
    chain = result.metadata["phase2"]["event_chain"]
    assert len(chain) == 1
    event = chain[0]
    assert event["settings"]["replay_dt_seconds"] == 225.0
    assert event["record"]["peak_m_msl"] == 40.75  # KP 58.8 right-bank trace
    assert event["record"]["provenance"]["anchor"] == "trace_right"
    assert event["window_closure"]["closed"] is True

    # Mass conservation and mask consistency.
    arrays = result.events[event["event_id"]]
    n = result.theta_matrix.shape[0]
    assert n == _SMALL_N
    assert int(arrays.accept_trans.sum()) + int((~arrays.accept_trans).sum()) == n
    np.testing.assert_array_equal(result.accept, arrays.accept_trans)

    # Decomposition consistency against the raw masks.
    table = event["decomposition"]
    assert table["n_prior"] == n
    assert table["f_trans_reject"] == pytest.approx(
        float((~arrays.accept_trans).mean())
    )
    assert table["f_marginal_transient"] == pytest.approx(
        float((arrays.accept_static & ~arrays.accept_trans).mean())
    )
    cell_sum = sum(c["count"] for c in table["cells"].values())
    assert cell_sum == n

    # Provenance: theta regenerated bit for bit, L stochastic and retained.
    assert result.metadata["phase1"]["theta_verified"] is True
    assert result.seepage_length_samples is not None

    # Persistence round-trip of the real-path artifact.
    loaded = PosteriorResult.load(out_dir / f"{phase1_small.stem}_posterior.h5")
    np.testing.assert_array_equal(loaded.accept, result.accept)
    assert loaded.metadata == result.metadata

    # Figures exist.
    assert len(list((out_dir / "figures").glob("*.png"))) >= 4

    # The C_e headline is present and finite.
    headline = result.metadata["analysis"]["c_e_headline"]
    assert np.isfinite(headline["prior_mean"])
    assert np.isfinite(headline["posterior_mean"])


@requires_real_data
def test_end_to_end_masked_matrix_equals_reevaluation(phase1_small: Path) -> None:
    """Mission invariant 7 on the REAL path: the two posterior-fragility
    routes agree exactly (bit-identical flags, zero curve deviation)."""
    from bayesian_reliability_updating.fragility_update import (
        posterior_fragility_from_matrices,
        verify_posterior_fragility_by_reevaluation,
    )
    from bayesian_reliability_updating.replay import load_phase1_run

    run = load_phase1_run(phase1_small)
    rng = np.random.default_rng(9)
    accept = rng.random(run.n_samples) < 0.6
    posterior = posterior_fragility_from_matrices(run, accept, n_bootstrap=50)
    report = verify_posterior_fragility_by_reevaluation(run, accept, posterior)
    assert report["verified"] is True
