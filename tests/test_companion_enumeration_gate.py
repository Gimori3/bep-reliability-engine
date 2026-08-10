"""G6 refuses an enumerated bit-identity consumer that nobody classified.

``scripts/production_campaign.py::enumerate_companions`` greps the tree for
consumers of the persisted production sweeps. Until 2026-08-10 it reached the
manifest only through ``gates.note``, and G6's sole assertion was that every
companion which *runs* completes -- so a hit that was neither run nor excluded
was recorded as ``UNCLASSIFIED -- investigate`` and could never fail anything.
Three accumulated that way across four sessions
(`docs/repo_audit_2026-07-31.md` section 12.9).

This is the third instance of one class. The first two closures were the 13
test guards that skipped on a tracked path (audit sections 11.2 and 12.4) and
the Stage 6.6 driver gate that recorded a non-verifying status and continued
(section 12.8). Neither could have caught this one: both AST guards parse only
the test file they live in, and the Stage 6.6 fix is a gate inside a different
driver. Each time the remedy was the same -- make the recorded outcome refuse.

These tests assert on tracked paths and never skip on one
(`docs/conventions.md` section 9.4). Nothing here runs a companion, a sweep or
the campaign: the gate is decidable from source alone, which is why it is
called before the subprocesses rather than after.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import production_campaign as PC  # noqa: E402


def _require_tracked(path: Path, why: str) -> Path:
    """Assert a tracked path exists -- never skip on one (conventions 9.4)."""
    assert path.exists(), f"tracked file missing ({why}): {path.relative_to(REPO_ROOT)}"
    return path


# ---------------------------------------------------------------------------
# The state the gate protects
# ---------------------------------------------------------------------------


def test_the_enumeration_yields_zero_unclassified_hits() -> None:
    """Every consumer of the persisted sweeps is run here or explicitly excluded."""
    enumeration = PC.enumerate_companions()
    assert enumeration["unclassified"] == [], (
        "a bit-identity consumer of the persisted production sweeps is neither "
        "run by the companions stage nor carries a COMPANION_EXCLUSIONS reason. "
        "Answer (a) should it RUN? -- and only if no, (b) what actually "
        "excludes it."
    )


def test_every_exclusion_key_still_names_a_file_on_disk() -> None:
    """A rename or deletion must not leave a reason that classifies nothing."""
    enumeration = PC.enumerate_companions()
    assert enumeration["exclusions_with_no_file_on_disk"] == []
    for path in PC.COMPANION_EXCLUSIONS:
        _require_tracked(REPO_ROOT / path, "a COMPANION_EXCLUSIONS key")


def test_every_companion_command_names_a_driver_on_disk() -> None:
    """The other half of the same rule: a run entry must resolve to a script."""
    for name in PC.COMPANION_COMMANDS:
        _require_tracked(
            REPO_ROOT / "scripts" / f"{name}.py", "a COMPANION_COMMANDS key"
        )


# ---------------------------------------------------------------------------
# The gate itself, exercised rather than asserted to exist
# ---------------------------------------------------------------------------


def test_gate_passes_on_the_repository_as_it_stands() -> None:
    """The production path: the real enumeration clears the real gate."""
    gates = PC.Gates("companions")
    PC.gate_companion_classification(gates, PC.enumerate_companions())
    assert [record["status"] for record in gates.records] == ["pass", "pass"]
    assert {record["gate"] for record in gates.records} == {"G6"}


def test_gate_fires_when_a_classification_is_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drop one exclusion and the campaign must refuse -- the whole point.

    Exercised, not asserted to exist. A gate nobody has seen fire is the defect
    this file closes: the pre-2026-08-10 note recorded exactly this state and
    passed.
    """
    victim = "scripts/epistemic_bracket_synthesis.py"
    assert victim in PC.COMPANION_EXCLUSIONS
    trimmed = {k: v for k, v in PC.COMPANION_EXCLUSIONS.items() if k != victim}
    monkeypatch.setattr(PC, "COMPANION_EXCLUSIONS", trimmed)

    enumeration = PC.enumerate_companions()
    assert enumeration["unclassified"] == [victim]

    gates = PC.Gates("companions")
    with pytest.raises(PC.GateFailure) as excinfo:
        PC.gate_companion_classification(gates, enumeration)
    assert victim in str(excinfo.value)
    assert gates.records[0]["status"] == "FAIL"


def test_gate_fires_on_a_hit_no_rule_mentions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A brand-new consumer must fail loudly, not be recorded and ignored.

    The 2026-07-29 asymmetric-allowlist precedent: an additive fact passes, an
    unexplained new one does not. Simulated by narrowing both classification
    tables rather than by writing a file into the tree.
    """
    monkeypatch.setattr(PC, "COMPANION_EXCLUSIONS", {})
    monkeypatch.setattr(PC, "COMPANION_COMMANDS", {})

    enumeration = PC.enumerate_companions()
    assert len(enumeration["unclassified"]) == len(enumeration["hits"])

    with pytest.raises(PC.GateFailure):
        PC.gate_companion_classification(PC.Gates("companions"), enumeration)


def test_gate_fires_on_a_stale_exclusion_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reason naming a file that no longer exists classifies nothing."""
    stale = dict(PC.COMPANION_EXCLUSIONS)
    stale["scripts/a_driver_that_was_renamed_away.py"] = "stale reason"
    monkeypatch.setattr(PC, "COMPANION_EXCLUSIONS", stale)

    enumeration = PC.enumerate_companions()
    assert enumeration["exclusions_with_no_file_on_disk"] == [
        "scripts/a_driver_that_was_renamed_away.py"
    ]

    gates = PC.Gates("companions")
    with pytest.raises(PC.GateFailure):
        PC.gate_companion_classification(gates, enumeration)
    # The unclassified check passed first; the stale-key check is what failed.
    assert [record["status"] for record in gates.records] == ["pass", "FAIL"]


# ---------------------------------------------------------------------------
# The wiring: the note is the evidence, the check is the enforcement
# ---------------------------------------------------------------------------


def test_the_stage_both_notes_and_gates_the_enumeration() -> None:
    """Keeping the note is deliberate; the check must not have replaced it.

    Read from source because running the stage runs every companion (hours).
    """
    source = _require_tracked(
        REPO_ROOT / "scripts" / "production_campaign.py", "the campaign driver"
    ).read_text(encoding="utf-8")
    stage = source.split("def stage_companions(")[1].split("\ndef ")[0]
    note_at = stage.index("programmatic companion enumeration")
    gate_at = stage.index("gate_companion_classification(gates, enumeration)")
    loop_at = stage.index("for name, spec in COMPANION_COMMANDS.items():")
    assert note_at < gate_at, "the note is the evidence and must survive the check"
    assert gate_at < loop_at, (
        "the classification gate is decidable from source, so it must refuse "
        "before the companion subprocesses rather than after ~40 minutes"
    )


def test_the_detection_limitation_is_recorded_not_silently_inherited() -> None:
    """The enumeration is a floor; its docstring must say so.

    ``scripts/conductivity_annualisation_study.py`` evaded the pre-2026-08-10
    pattern by composing its stem with an f-string. The widening catches that
    file; it does not make the regex a census, and the next reader is entitled
    to know which claim is being made.
    """
    doc = PC.enumerate_companions.__doc__ or ""
    assert "FLOOR, NOT A CENSUS" in doc.upper()
    assert "conductivity_annualisation_study" in doc
    enumeration = PC.enumerate_companions()
    assert "detection_is_a_floor_not_a_census" in enumeration


def test_the_widened_pattern_still_catches_the_file_that_evaded_it() -> None:
    """Regression pin for the 2026-08-10 widening.

    The study composes ``f"tokachi_kp{kp:.1f}_historical_{D70}"``, so the old
    ``tokachi_kp[0-9]`` needed a digit where the f-string places ``{``.
    """
    enumeration = PC.enumerate_companions()
    assert "scripts/conductivity_annualisation_study.py" in enumeration["hits"]
    assert "scripts/generate_configs.py" in enumeration["hits"]


def test_this_guard_file_is_itself_an_enumerated_and_classified_hit() -> None:
    """The gate's first live catch was this file, and that is the demonstration.

    Its docstrings quote both the f-string stem and the phrase the assertion
    half matches, so it became a hit the moment it was written -- the same
    self-matching trap the AST guards in ``test_figure_pass.py`` and
    ``test_stage6_6_driver_gate.py`` were written around. Here the honest
    answer was to classify it like its three ``tests/`` siblings, so pin that
    it stayed classified rather than being exempted by a narrowed pattern.
    """
    enumeration = PC.enumerate_companions()
    me = "tests/test_companion_enumeration_gate.py"
    assert me in enumeration["hits"]
    assert me in PC.COMPANION_EXCLUSIONS
    assert me not in enumeration["unclassified"]


def test_run_but_not_matched_is_the_benign_direction() -> None:
    """A companion that runs without matching costs coverage, never correctness.

    Pinned so the list is a recorded fact rather than an unexamined leftover:
    each of these is invoked by the stage but fails one half of the regex.
    """
    enumeration = PC.enumerate_companions()
    assert set(enumeration["run_but_not_matched_by_the_regex"]) == {
        "scripts/assess_2011_2006_closure.py",
        "scripts/foreshore_exhaustion_study.py",
        "scripts/gsa_study.py",
        "scripts/segment_fragility.py",
    }
    for path in enumeration["run_but_not_matched_by_the_regex"]:
        stem = Path(path).stem
        assert stem in PC.COMPANION_COMMANDS, f"{stem} is not run by the stage"
