"""Tests for the composition-seam rating-error study and its committed record.

The driver is a study script: pure post-processing over the committed surface
curves, the persisted Phase 2 posterior curves and the cached hazard. What is
worth pinning is that it reuses the campaign's composition rather than a second
copy, that it refuses to report against a baseline which does not reproduce the
production table, and that the committed evidence record still carries the
claims the thesis quotes from it.

These tests assert on tracked paths and never skip on one
(``docs/conventions.md`` section 9.4).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_SCRIPT = REPO / "scripts" / "composition_seam_rating_error_study.py"
_EVIDENCE = REPO / "docs" / "decisions" / "composition-seam-rating-error.json"
_NOTE = REPO / "docs" / "decisions" / "composition-seam-rating-error.md"
_COMPANION_CSV = (
    REPO
    / "data"
    / "processed"
    / "uemura_surface_curves"
    / "uemura_surface_curves_overflow_no_rating_error.csv"
)


def _require_tracked(path: Path) -> Path:
    assert path.is_file(), (
        f"tracked artifact missing: {path.relative_to(REPO)}. It moved, was "
        "renamed or was deleted; it is not optional."
    )
    return path


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "composition_seam_rating_error_study", _require_tracked(_SCRIPT)
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _evidence() -> dict:
    return json.loads(_require_tracked(_EVIDENCE).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The driver
# ---------------------------------------------------------------------------


def test_driver_reuses_the_campaign_composition_rather_than_a_copy() -> None:
    """A second copy of ``_compose_segment`` could drift from the production one."""
    driver = _load_driver()
    campaign_source = (REPO / "scripts" / "phase3_campaign.py").read_text(
        encoding="utf-8"
    )
    assert driver._CAMPAIGN._compose_segment.__module__ == "phase3_campaign"
    assert "def _compose_segment" in campaign_source
    assert "def _compose_segment" not in _SCRIPT.read_text(encoding="utf-8"), (
        "the seam driver must import the campaign's composition, not define " "its own"
    )


def test_the_two_surface_arms_differ_only_in_the_overflow_mechanism() -> None:
    driver = _load_driver()
    arms = driver._surface_sets()
    assert set(arms) == {"primary", "no_rating_error"}
    for name in ("fluvial_scour",):
        primary = {
            (c.river, c.kp, c.scenario): tuple(c.p_f)
            for c in arms["primary"].curves
            if c.mechanism == name
        }
        arm = {
            (c.river, c.kp, c.scenario): tuple(c.p_f)
            for c in arms["no_rating_error"].curves
            if c.mechanism == name
        }
        assert primary == arm, f"the arm must leave {name} untouched"
    overflow_moved = any(
        tuple(a.p_f) != tuple(b.p_f)
        for a in arms["primary"].curves
        if a.mechanism == "overflow"
        for b in arms["no_rating_error"].curves
        if b.mechanism == "overflow"
        and (b.river, b.kp, b.scenario) == (a.river, a.kp, a.scenario)
    )
    assert overflow_moved, "the arm must move the overflow mechanism somewhere"


# ---------------------------------------------------------------------------
# The committed record
# ---------------------------------------------------------------------------


def test_the_committed_record_passed_its_baseline_gate() -> None:
    """Every displacement in the note is measured against the production table."""
    record = _evidence()
    assert record["gate"]["status"] == "reproduces_production"
    assert record["gate"]["failures"] == []
    assert record["gate"]["checked_rows"] == 8


def test_the_seam_leaves_every_piping_number_exactly_unchanged() -> None:
    """The thesis states the seam acts on the overflow branch alone.

    Recorded here as the identity it is, not as an approximation: if a future
    regeneration let the arm touch the piping branch, that sentence would be
    wrong and this guard is what says so.
    """
    for section in _evidence()["sections"]:
        assert section["displacement"]["p_annual_bep"] == 1.0, section["kp"]


def test_the_kp62_warming_crossing_is_recorded_as_not_surviving() -> None:
    """The one ordering the seam changes, and the margin it changes from."""
    crossing = _evidence()["kp62_warming_crossing"]
    assert crossing["survives"] is False
    assert crossing["primary"]["dominant"] == "bep"
    assert crossing["no_rating_error"]["dominant"] == "overflow"
    assert abs(crossing["primary"]["margin_bep_over_overflow"] - 1.0013) < 5e-4


def test_the_primary_arm_reproduces_the_published_dominance_counts() -> None:
    """An independent reproduction of the reach-wide table from a second driver."""
    counts = _evidence()["reach_dominance_counts"]["primary"]
    assert counts["historical"] == {
        "no mechanism loaded": 79,
        "overflow": 31,
        "bep": 4,
    }
    assert counts["+4K"] == {"overflow": 109, "bep": 4, "no mechanism loaded": 1}


def test_the_note_and_the_companion_product_are_both_committed() -> None:
    _require_tracked(_NOTE)
    _require_tracked(_COMPANION_CSV)
