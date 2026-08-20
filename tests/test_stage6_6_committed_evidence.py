"""Guards for the committed copies of the Stage 6.6 evidence.

``docs/stage6_6_report.md`` line 11 says the ``docs/decisions/adr0040-stage6-6-*``
records are "the number-bearing evidence" and that "every number below traces to
those files". Nothing enforced that, and no driver writes them:
``scripts/stage6_6_gap_decomposition.py`` writes only ``results/stage6_6/`` and
the tracked ``docs/figures/`` copies, so these five files were placed by hand by
05821aa and could only be kept current by hand.

They were not. ADR-0047 (2026-07-29) changed KP 62.0's seepage length from 47.0 m
to 40.0 m, the production campaign regenerated the live artifacts, and commit
263bf85 (2026-08-06) carried the post-adoption figures into the report and the
thesis but not into these copies. The two KP 62.0 records therefore sat stating a
design-level static/transient ratio of 21.0 -- the figure the repository had
retired -- while the report and Chapter 6 carried the live values. They were
transcribed from the live artifacts on 2026-08-20.

This is the failure mode ``docs/conventions.md`` section 9.3 records for figures,
one level over: a hand-maintained copy of a generated artifact goes stale
silently. Figures were fixed structurally, by making every driver dual-write.
These records have no driver, so the structural fix available here is this guard,
a content comparison against the live artifact whenever it is on the machine.

The comparison is on content, not on file digest, for the reason
``tests/test_thesis_figure_gaps.py`` gives for the extracted slices: a digest gate
fires on volatile keys after every campaign run without a number moving.
``results/stage6_6/`` is gitignored, so its absence is a fresh clone and skips;
every tracked path here asserts.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
DECISIONS = REPO / "docs" / "decisions"
LIVE = REPO / "results" / "stage6_6"

#: Committed copy -> the live campaign artifact it must reproduce. The KP 57.4
#: pair is as much the point as the KP 62.0 pair: it is the control that proved
#: the 2026-08-20 staleness was ADR-0047's section-specific adoption and not a
#: general drift, and it must keep reproducing for that reading to hold.
COMMITTED_TO_LIVE = {
    "adr0040-stage6-6-kp62_0-analysis.json": ("stage6_6_kp62_0_analysis.json"),
    "adr0040-stage6-6-kp62_0-duration-ladder.json": (
        "stage6_6_kp62_0_duration_ladder.json"
    ),
    "adr0040-stage6-6-kp57_4-analysis.json": ("stage6_6_kp57_4_analysis.json"),
    "adr0040-stage6-6-kp57_4-duration-ladder.json": (
        "stage6_6_kp57_4_duration_ladder.json"
    ),
}

#: Records rewritten on 2026-08-20 from the live artifact, which therefore carry
#: a ``provenance`` block naming what they were cut from. The KP 57.4 pair was
#: already current and was deliberately left untouched, so it carries none: the
#: block records a replacement event, not a general schema.
REWRITTEN = (
    "adr0040-stage6-6-kp62_0-analysis.json",
    "adr0040-stage6-6-kp62_0-duration-ladder.json",
)

#: Keys the campaign's own comparison helper ignores
#: (``scripts/production_campaign.py::VOLATILE_JSON_KEYS``), plus the provenance
#: block a committed copy carries and the live artifact never has.
IGNORED = frozenset(
    {
        "generated",
        "generated_utc",
        "generated_by",
        "runtime_s",
        "runtime_seconds",
        "timestamp",
        "campaign",
        "elapsed_s",
        "config_hash",
        "provenance",
    }
)


def _leaves(node: Any, path: str = "", out: dict[str, Any] | None = None) -> dict:
    if out is None:
        out = {}
    if isinstance(node, dict):
        for key, value in node.items():
            if key in IGNORED:
                continue
            _leaves(value, f"{path}.{key}" if path else key, out)
    elif isinstance(node, list):
        if not node:
            out[path] = "<empty>"
        for index, value in enumerate(node):
            _leaves(value, f"{path}[{index}]", out)
    else:
        out[path] = node
    return out


def _same(left: Any, right: Any) -> bool:
    """NaN equals NaN here: a bootstrap fraction is undefined at a zero gap."""
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
    return left == right


def _read(path: Path) -> dict:
    assert path.is_file(), f"{path.relative_to(REPO)} is tracked and must exist"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("committed", sorted(COMMITTED_TO_LIVE))
def test_the_committed_copy_reproduces_the_live_artifact(committed: str) -> None:
    """The whole point of the copy is that it carries the live numbers."""
    live = LIVE / COMMITTED_TO_LIVE[committed]
    if not live.is_file():
        pytest.skip(
            f"results/stage6_6/{live.name} is untracked (gitignored campaign "
            "artifact); absent on a fresh clone"
        )
    tracked = _leaves(_read(DECISIONS / committed))
    fresh = _leaves(json.loads(live.read_text(encoding="utf-8")))
    assert set(tracked) == set(fresh), (
        f"docs/decisions/{committed} and results/stage6_6/{live.name} no longer "
        "have the same shape"
    )
    drifted = sorted(key for key in tracked if not _same(tracked[key], fresh[key]))
    assert not drifted, (
        f"docs/decisions/{committed} no longer matches results/stage6_6/"
        f"{live.name} at {len(drifted)} values, e.g. {drifted[:5]}. No driver "
        "writes the committed copy; transcribe it from the live artifact."
    )


@pytest.mark.parametrize("committed", REWRITTEN)
def test_a_rewritten_copy_says_what_it_was_cut_from(committed: str) -> None:
    """A hand-placed copy is only trustworthy if it names its source."""
    provenance = _read(DECISIONS / committed)["provenance"]
    source = provenance["source"]
    assert source["gitignored"] is True
    assert source["path"].startswith("results/stage6_6/")
    assert len(source["sha256"]) == 64
    assert "no sweep, ladder or study was re-run" in provenance["transcribed_by"]


@pytest.mark.parametrize("committed", REWRITTEN)
def test_a_rewritten_copy_points_at_the_resolved_bias(committed: str) -> None:
    """The retired "about 21" lived in exactly these files.

    Both the pre-adoption 21.0 and the post-adoption 44.75 are N = 1e5 counts
    that ``docs/stage6_6_report.md`` section 9 tells the reader not to quote, so
    replacing one with the other is not on its own enough: the record has to send
    an examiner to the resolved figure.
    """
    note = _read(DECISIONS / committed)["provenance"]["quotable_design_hwl_bias"]
    assert "26.9" in note and "[21.6, 35.3]" in note
    assert "adr0040-hwl-bias-resolution.json" in note


def test_the_summary_still_matches_the_live_verification_statuses() -> None:
    """The summary was deliberately not replaced, on the ground that it carries
    no superseded number. That ground has to keep holding.
    """
    live_path = LIVE / "stage6_6_summary.json"
    if not live_path.is_file():
        pytest.skip(
            "results/stage6_6/stage6_6_summary.json is untracked (gitignored "
            "campaign artifact); absent on a fresh clone"
        )
    committed = _read(DECISIONS / "adr0040-stage6-6-summary.json")
    tracked = _leaves(committed)
    fresh = _leaves(json.loads(live_path.read_text(encoding="utf-8")))
    shared = set(tracked) & set(fresh)
    drifted = sorted(key for key in shared if not _same(tracked[key], fresh[key]))
    assert not drifted, (
        "adr0040-stage6-6-summary.json was left in place because every value it "
        "shares with the live summary was identical; that is no longer true at "
        f"{drifted}."
    )
    # The keys the live record does not carry are explained, not silently
    # different: 'figures' is written only on a rendering run, 'hash_note' only
    # on a config-hash mismatch that no longer occurs.
    extra = {key.split(".")[-1].split("[")[0] for key in set(tracked) - shared}
    documented = set(committed["provenance"]["keys_the_live_record_does_not_carry"])
    assert extra <= documented, (
        "the summary carries keys the live record lacks and nothing explains "
        f"them: {sorted(extra - documented)}"
    )
