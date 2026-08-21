"""Phase 2 re-evaluation verification must reproduce the run it is checking.

``fragility_update.verify_posterior_fragility_by_reevaluation`` re-runs M8 over
the accepted rows and asserts the recomputed failure flags match the retained
matrices. That is only a verification if it re-runs the **same model**. Until
2026-08-21 the call forwarded the geometry, the Sellmeijer exponents and the
foreland treatment but not the three optional M8 keywords a parent run may
carry: the ADR-0045 model-factor draws, the ADR-0049 critical-length factor and
the ADR-0050 toe-gradient relief.

The failure mode is quiet and expensive. Nothing raises at run time; the
verifier simply re-evaluates the *undrained*, unfactored model, finds it differs
from the matrices the parent actually wrote, and reports the parent as
unverifiable. It was found by an ADR-0050 arm replay, where the mismatch count
scaled with the relief strength (2 481 flags at relief 0.80 up to 1 008 624 at
0.20) while the static mismatch stayed exactly 0 -- the signature of a
transient-only keyword going unforwarded.

Production is unaffected either way, because all three default to absent. That
is precisely why this needs a test: the defect is invisible until someone runs
an arm, and the three knobs exist to be run as arms.
"""

from __future__ import annotations

import numpy as np
import pytest

from bayesian_reliability_updating.fragility_update import (
    posterior_fragility_from_matrices,
    verify_posterior_fragility_by_reevaluation,
)
from bayesian_reliability_updating.replay import load_phase1_run
from tests.phase2_helpers import generate_stub_phase1

#: Strong enough to move the transient branch on the stub grid, and mild enough
#: to leave a non-degenerate mix of failing and surviving rows.
_RELIEF = 0.5
_CRITICAL_LENGTH = 1.5


def _verify(path, accept):
    run = load_phase1_run(path, verify_theta=True)
    posterior = posterior_fragility_from_matrices(run, accept, n_bootstrap=50)
    return verify_posterior_fragility_by_reevaluation(run, accept, posterior)


@pytest.fixture(scope="module")
def baseline_run(tmp_path_factory):
    return generate_stub_phase1(tmp_path_factory.mktemp("verify_baseline"))


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({}, id="baseline"),
        pytest.param({"toe_gradient_relief_factor": _RELIEF}, id="adr0050_relief"),
        pytest.param(
            {"critical_length_factor": _CRITICAL_LENGTH}, id="adr0049_critical_length"
        ),
        pytest.param(
            {
                "sellmeijer_model_factor": {
                    "enabled": True,
                    "mean": 1.0,
                    "cov": 0.12,
                }
            },
            id="adr0045_model_factor",
        ),
    ],
)
def test_verification_passes_for_a_run_carrying_an_optional_keyword(
    tmp_path_factory, overrides
) -> None:
    """A parent run with any optional M8 keyword must verify against itself."""
    path = generate_stub_phase1(tmp_path_factory.mktemp("verify_arm"), **overrides)
    run = load_phase1_run(path, verify_theta=True)
    accept = np.ones(run.n_samples, dtype=bool)
    report = _verify(path, accept)
    assert report["verified"], (
        f"a run carrying {sorted(overrides)} does not verify against itself: "
        f"{report}. The re-evaluation is running a different model from the one "
        "that wrote the matrices."
    )
    assert report["flag_mismatch_static"] == 0
    assert report["flag_mismatch_trans"] == 0


def test_the_relief_arm_is_actually_different_from_the_baseline(
    tmp_path_factory, baseline_run
) -> None:
    """Guard that the test above is not verifying two identical runs.

    If the relief did nothing on the stub grid, the parametrized test would pass
    for the wrong reason and the regression would be undetectable again.
    """
    arm = generate_stub_phase1(
        tmp_path_factory.mktemp("verify_arm_delta"),
        toe_gradient_relief_factor=_RELIEF,
    )
    base = load_phase1_run(baseline_run, verify_theta=True)
    relieved = load_phase1_run(arm, verify_theta=True)
    assert not np.array_equal(
        base.result.failure_matrix_tran, relieved.result.failure_matrix_tran
    ), "the relief must move the stub transient matrix for this suite to bite"
    assert np.array_equal(
        base.result.failure_matrix_stat, relieved.result.failure_matrix_stat
    ), "the relief must not move the static matrix (ADR-0028)"
