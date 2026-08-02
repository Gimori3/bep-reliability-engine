"""Tests for the Phase 2 observed-event ingestion (ADR-0035).

The pure pieces (inverse rating, guards) run everywhere. Beyond those there
are two kinds of dependency here, and they are deliberately handled
differently:

* the **committed** 2016 extracts under ``data/processed/2016_event/`` are
  tracked, so they are *required*: their absence is a broken repository and
  must fail (:data:`requires_processed` -> an asserting fixture);
* the rating-coefficient CSVs under **untracked** ``data/raw/`` are a
  machine-local drop that is legitimately absent on a fresh clone, so they
  keep ``skipif`` (:data:`requires_rating`), mirroring the Phase 1
  ``tests/test_hydrographs.py`` pattern.

**Hardening, 2026-07-31.** ``requires_processed`` used to be a ``skipif`` on
``stage_hourly_Tokachi_201608.csv`` -- a *tracked* path -- across nine
decorator sites. That is the guard class Amendment 1 closed in
``tests/test_figure_pass.py``: moving, renaming or deleting the extract
disabled nine guards at once while the suite still reported green. The mark
now pulls in a fixture that asserts, so the decorator sites are unchanged and
only the outcome flipped from skip to fail.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bayesian_reliability_updating.events import (
    default_2016_source,
    inverse_rating_discharge,
    observed_event_record,
    read_flood_traces,
    read_stage_series,
    window_closure_diagnostic,
)
from bep_reliability_engine.hydrographs import apply_rating_curve
from tests.phase2_helpers import flat_record

_PROCESSED = Path("data/processed/2016_event")
_RATING_CSV = Path("data/raw/rating_curves/HQrelation_TokachiRiv_2017.csv")

#: The committed extracts every ``requires_processed`` test reads. Both are
#: tracked (``git ls-files data/processed/2016_event/``).
_TRACKED_EXTRACTS = (
    _PROCESSED / "stage_hourly_Tokachi_201608.csv",
    _PROCESSED / "flood_trace_2016.csv",
)


@pytest.fixture()
def tracked_2016_extracts() -> Path:
    """Assert the *committed* 2016 extracts are still where ADR-0035 put them.

    These are tracked files, so a miss is not a machine without the optional
    data drop -- it is a repository in which the extract moved, was renamed or
    was deleted. Skipping on that silently disarmed every guard below, which
    is exactly the failure mode the 2026-07-31 hardening pass closed in
    ``tests/test_figure_pass.py``. Fail loudly instead.
    """
    missing = [p.as_posix() for p in _TRACKED_EXTRACTS if not p.is_file()]
    assert not missing, (
        f"committed 2016 extracts missing: {missing}. These are tracked "
        "(ADR-0035, data/processed/2016_event/); if they moved or were "
        "renamed, update this module in the same change, and if they were "
        "deleted the Phase 2 event-ingestion guards are now unpinned. "
        "Regenerate with: python scripts/extract_2016_event.py"
    )
    return _PROCESSED


#: Tracked and required: asserts (see the fixture above), never skips.
requires_processed = pytest.mark.usefixtures("tracked_2016_extracts")

#: Genuinely optional: the rating-coefficient CSVs live in untracked
#: ``data/raw/`` and are absent on a fresh clone, so ``skipif`` is correct
#: here and must stay.
requires_rating = pytest.mark.skipif(
    not _RATING_CSV.exists(),
    reason="rating-coefficient CSVs (untracked data/raw) not present",
)

# Obihiro rating (ADR-0019 section 4 anchor values).
_A_OBIHIRO, _B_OBIHIRO = 140.33, -32.49


# ---------------------------------------------------------------------------
# Pure inverse-rating layer
# ---------------------------------------------------------------------------


def test_inverse_rating_round_trips_through_eq_4_19() -> None:
    """apply_rating_curve(inverse_rating(h)) == h above the rating datum."""
    stage = np.array([32.49, 33.0, 35.5, 37.95, 39.9])
    q_eq = inverse_rating_discharge(stage, _A_OBIHIRO, _B_OBIHIRO)
    back = apply_rating_curve(q_eq, _A_OBIHIRO, _B_OBIHIRO)
    np.testing.assert_allclose(back, stage, rtol=0.0, atol=1e-12)


def test_inverse_rating_reproduces_adr_0019_anchor() -> None:
    """The 37.95 m MSL anchor stage maps to ~4,180 m^3/s (ADR-0019 sec. 4)."""
    q = inverse_rating_discharge(np.array([37.95]), _A_OBIHIRO, _B_OBIHIRO)
    assert abs(q[0] - 4180.0) < 30.0


def test_inverse_rating_floors_low_flow_below_datum() -> None:
    """Sub-datum low-flow readings become zero discharge, not an error."""
    stage = np.array([31.7, 32.0, 33.0])
    q_eq = inverse_rating_discharge(stage, _A_OBIHIRO, _B_OBIHIRO)
    assert q_eq[0] == 0.0 and q_eq[1] == 0.0 and q_eq[2] > 0.0


def test_inverse_rating_rejects_gross_datum_mismatch() -> None:
    """A series metres below the datum is a wrong-datum series: loud."""
    with pytest.raises(ValueError, match="datum mismatch"):
        inverse_rating_discharge(np.array([5.0]), _A_OBIHIRO, _B_OBIHIRO)
    with pytest.raises(ValueError, match="a_kp must be positive"):
        inverse_rating_discharge(np.array([33.0]), -1.0, _B_OBIHIRO)


# ---------------------------------------------------------------------------
# Processed-extract readers
# ---------------------------------------------------------------------------


@requires_processed
def test_read_stage_series_obihiro() -> None:
    source = default_2016_source()
    series = read_stage_series(source.stage_csv, "obihiro")
    assert series.stage_m_msl.shape == (744,)
    assert series.t0_iso == "2016-08-01T01:00"
    assert np.all(np.diff(series.time_hours) == 1.0)
    # The observed 2016 peak at Obihiro (m MSL datum evidence).
    assert abs(float(series.stage_m_msl.max()) - 38.07) < 1e-9


@requires_processed
def test_read_stage_series_missing_station_raises() -> None:
    source = default_2016_source()
    with pytest.raises(ValueError, match="not in"):
        read_stage_series(source.stage_csv, "nonexistent_station")


@requires_processed
def test_read_stage_series_gapped_station_raises() -> None:
    """Kumaushi was closed in 2016; its gaps must be loud, not interpolated."""
    source = default_2016_source()
    with pytest.raises(ValueError, match="gap-free"):
        read_stage_series(source.stage_csv, "kumaushi")


@requires_processed
def test_read_flood_traces_tokachi_study_reach() -> None:
    source = default_2016_source()
    traces = read_flood_traces(source.trace_csv, "Tokachi")
    # The four study sections all carry a right-bank trace.
    for kp, expected in [(57.4, 39.658), (58.8, 40.75), (60.0, 42.296), (62.0, 45.729)]:
        assert abs(traces[kp].trace_right_m - expected) < 1e-9
    # Design HWL cross-check against the generated configs (ADR-0018 chain).
    assert abs(traces[58.8].design_hwl_m - 41.03) < 1e-9


# ---------------------------------------------------------------------------
# Record construction (needs the rating CSVs in data/raw)
# ---------------------------------------------------------------------------


@requires_processed
@requires_rating
def test_trace_anchored_record_peak_is_the_survey_value() -> None:
    source = default_2016_source()
    record = observed_event_record(source, section_kp=58.8, anchor="trace_right")
    assert record.peak == 40.75
    assert float(record.h.max()) == pytest.approx(40.75, abs=1e-9)
    assert record.native_dt == 3600.0
    assert record.provenance["anchor"] == "trace_right"
    assert record.provenance["gauge_station"] == "obihiro"
    assert record.provenance["construction"] == "observed_stage_inverse_rating"


@requires_processed
@requires_rating
def test_rating_anchor_skips_trace_rescaling() -> None:
    source = default_2016_source()
    record = observed_event_record(source, section_kp=58.8, anchor="rating")
    assert record.peak == pytest.approx(float(record.h.max()))
    assert "trace_anchor_m_msl" not in record.provenance


@requires_processed
@requires_rating
def test_trace_anchoring_preserves_shape_and_trough() -> None:
    """Anchoring rescales amplitude only: same normalized shape, same base."""
    source = default_2016_source()
    anchored = observed_event_record(source, section_kp=58.8, anchor="trace_right")
    rating = observed_event_record(source, section_kp=58.8, anchor="rating")
    base_a, base_r = anchored.h.min(), rating.h.min()
    assert base_a == pytest.approx(base_r, abs=1e-9)
    shape_a = (anchored.h - base_a) / (anchored.h.max() - base_a)
    shape_r = (rating.h - base_r) / (rating.h.max() - base_r)
    np.testing.assert_allclose(shape_a, shape_r, atol=1e-12)


@requires_processed
@requires_rating
def test_unknown_anchor_and_unusable_trace_raise() -> None:
    source = default_2016_source()
    with pytest.raises(ValueError, match="anchor"):
        observed_event_record(source, section_kp=58.8, anchor="bogus")
    # KP 58.8's left bank is a no-levee reach (no trace surveyed): the
    # left-bank anchor must fail loudly instead of anchoring on NaN.
    with pytest.raises(ValueError, match="no usable"):
        observed_event_record(source, section_kp=58.8, anchor="trace_left")
    # A KP off the 0.2 km rating grid has no coefficients.
    with pytest.raises(ValueError, match="no rating coefficients"):
        observed_event_record(source, section_kp=58.75, anchor="trace_right")


@requires_processed
@requires_rating
def test_window_closure_confirmed_at_kp58_8() -> None:
    """The truncated September recession is inert: the window ends below toe."""
    source = default_2016_source()
    record = observed_event_record(source, section_kp=58.8, anchor="trace_right")
    closure = window_closure_diagnostic(record, 38.5)
    assert closure["closed"] is True
    assert closure["end_margin_below_toe_m"] > 0.0
    assert closure["hours_after_last_exceedance"] > 0.0


def test_no_existence_skip_in_this_file_gates_on_a_tracked_path() -> None:
    """The anti-pattern must not come back, and it is invisible when it does.

    ``requires_processed`` gated nine tests on a *tracked* CSV, so a move or a
    deletion disarmed all nine while the suite stayed green. The rule that
    replaced it is not self-enforcing, hence this guard: the only
    existence-conditional ``skipif`` left in this module must name the
    untracked ``data/raw/`` drop (``.gitignore`` line 224), which is
    legitimately absent on a fresh clone.

    Parsed, not grepped: the prose above names both forms deliberately, and a
    string search would match this test's own explanation.
    """
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    conditions: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(
            ("mark.skipif", "pytest.skip")
        ):
            conditions.extend(ast.unparse(arg) for arg in node.args)

    assert conditions == ["not _RATING_CSV.exists()"], (
        "An existence-conditional skip appeared in this module: "
        f"{conditions}. skipif is correct only for a gitignored, "
        "machine-local drop such as data/raw/. A tracked artifact must "
        "assert (see the tracked_2016_extracts fixture), or its guards vanish "
        "silently when it moves."
    )


def test_window_closure_flags_a_loaded_window_end() -> None:
    record = flat_record(5.0, event_id="still_loaded")
    closure = window_closure_diagnostic(record, 2.0)
    assert closure["closed"] is False
    assert closure["hours_after_last_exceedance"] == 0.0
