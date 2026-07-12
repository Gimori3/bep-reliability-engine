"""Acceptance-logic truth tests and decomposition consistency (no I/O).

These tests drive :mod:`bayesian_reliability_updating.filtering` with
hand-built :class:`BatchDiagnostics` payloads whose flags are known by
construction, so the acceptance rule, the mass conservation and the
two-by-two decomposition are checked as pure logic, independent of any
physics or data.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest

from bayesian_reliability_updating.filtering import (
    apply_survival_filter,
    decompose,
)
from bayesian_reliability_updating.replay import EventReplay
from bep_reliability_engine.evaluator import BatchDiagnostics
from tests.phase2_helpers import flat_record


def _diagnostics(
    failure_trans: list[bool],
    failure_static: list[bool],
    initiation: list[bool] | None = None,
) -> BatchDiagnostics:
    n = len(failure_trans)
    trans = np.asarray(failure_trans, dtype=bool)
    static = np.asarray(failure_static, dtype=bool)
    init = (
        np.asarray(initiation, dtype=bool) if initiation is not None else trans.copy()
    )
    zeros = np.zeros(n, dtype=np.float64)
    return BatchDiagnostics(
        Z_static=np.where(static, -1.0, 1.0),
        Z_transient=np.where(trans, -1.0, 1.0),
        l_e_final=zeros,
        H_c=zeros + 5.0,
        H_c_transient=zeros + 5.0,
        l_c=zeros + 1.0,
        lambda_in=zeros + 100.0,
        r_e=zeros + 0.5,
        t_uh=np.where(init, 3600.0, np.nan),
        failure_static=static,
        failure_trans=trans,
        uplift_occurred=init,
        heave_occurred=init,
    )


def _replay(diagnostics: BatchDiagnostics) -> EventReplay:
    record = flat_record(1.0, event_id="logic_fixture")
    return EventReplay(
        record=record,
        diagnostics=diagnostics,
        settings={"event_id": "logic_fixture"},
        window_closure={"closed": True},
    )


def test_acceptance_is_strict_complement_of_transient_failure() -> None:
    """Accept iff Z_transient > 0: the failure flags encode Z <= 0 exactly."""
    diagnostics = _diagnostics(
        failure_trans=[True, False, False, True],
        failure_static=[False, False, True, True],
    )
    outcome = apply_survival_filter(_replay(diagnostics))
    np.testing.assert_array_equal(outcome.accept, [False, True, True, False])
    np.testing.assert_array_equal(outcome.accept, outcome.accept_trans)
    np.testing.assert_array_equal(outcome.accept_static, [True, True, False, False])


def test_posterior_mass_conservation() -> None:
    """Accepted plus rejected equals N, and the fractions agree."""
    rng = np.random.default_rng(7)
    trans = list(rng.random(500) < 0.3)
    static = list(rng.random(500) < 0.2)
    outcome = apply_survival_filter(_replay(_diagnostics(trans, static)))
    assert outcome.n_accepted + int((~outcome.accept).sum()) == outcome.n_prior
    assert outcome.rejection_fraction == pytest.approx(
        1.0 - outcome.n_accepted / outcome.n_prior
    )


def test_decomposition_cells_partition_the_prior() -> None:
    rng = np.random.default_rng(11)
    accept_static = rng.random(1000) < 0.7
    accept_trans = rng.random(1000) < 0.6
    table = decompose(accept_static, accept_trans)
    counts = [cell["count"] for cell in table["cells"].values()]
    assert sum(counts) == 1000
    assert table["f_marginal_transient"] == pytest.approx(
        table["cells"]["transient_only_reject"]["fraction"]
    )
    assert table["f_trans_reject"] == pytest.approx(float((~accept_trans).mean()))
    assert table["f_static_reject"] == pytest.approx(float((~accept_static).mean()))


def test_decomposition_reports_non_nested_sets_faithfully() -> None:
    """Rows can fail static yet survive transient; the cell must not vanish."""
    accept_static = np.array([False, False, True, True])
    accept_trans = np.array([True, False, True, False])
    table = decompose(accept_static, accept_trans)
    assert table["cells"]["static_only_reject"]["count"] == 1
    assert table["cells"]["transient_only_reject"]["count"] == 1
    assert table["cells"]["both_reject"]["count"] == 1
    assert table["cells"]["both_survive"]["count"] == 1


def test_strict_criterion_additionally_rejects_initiation_rows() -> None:
    """no_breach_no_initiation removes rows whose uplift+heave gate latched."""
    diagnostics = _diagnostics(
        failure_trans=[False, False, False, True],
        failure_static=[False, False, False, False],
        initiation=[False, True, False, True],
    )
    baseline = apply_survival_filter(_replay(diagnostics), criterion="no_breach")
    strict = apply_survival_filter(
        _replay(diagnostics), criterion="no_breach_no_initiation"
    )
    np.testing.assert_array_equal(baseline.accept, [True, True, True, False])
    np.testing.assert_array_equal(strict.accept, [True, False, True, False])
    # The strict posterior is a subset of the baseline posterior.
    assert np.all(strict.accept <= baseline.accept)


def test_unknown_criterion_raises() -> None:
    diagnostics = _diagnostics([False], [False])
    with pytest.raises(ValueError, match="criterion"):
        apply_survival_filter(_replay(diagnostics), criterion="bogus")


def test_posterior_collapse_error_fires_on_total_collapse(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Below the scale-aware collapse floor an error-level diagnostic fires."""
    n = 40
    with caplog.at_level(logging.ERROR):
        outcome = apply_survival_filter(_replay(_diagnostics([True] * n, [False] * n)))
    assert outcome.n_accepted == 0
    assert any("collapsed" in w for w in outcome.warnings)
    assert any("collapsed" in message for message in caplog.messages)


def test_posterior_headroom_warning_fires_below_half(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Keeping under half the prior logs the headroom warning."""
    n = 40
    trans = [True] * (n - 3) + [False] * 3  # keeps 3 of 40 rows
    with caplog.at_level(logging.WARNING):
        outcome = apply_survival_filter(_replay(_diagnostics(trans, [False] * n)))
    assert outcome.n_accepted == 3
    assert any("headroom" in w for w in outcome.warnings)


def test_all_accept_produces_no_warning() -> None:
    outcome = apply_survival_filter(_replay(_diagnostics([False] * 50, [False] * 50)))
    assert outcome.n_accepted == 50
    assert outcome.rejection_fraction == 0.0
    assert outcome.warnings == []
