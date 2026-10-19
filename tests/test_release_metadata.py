"""Release-metadata guard: every place that states the version agrees.

The v1.4.0 release was first tagged on 2026-10-19 with ``pyproject.toml`` still
at 1.3.0 while ``CITATION.cff``, ``CHANGELOG.md`` and the README already said
1.4.0, so ``pip show`` and the run metadata's installed-version stamp disagreed
with the release they came from. Nothing compared the four, so nothing caught
it; the tag was re-cut on the bumped commit the same day.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    with (REPO / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def test_citation_version_matches_pyproject() -> None:
    citation = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(r"^version:\s*(\S+)\s*$", citation, flags=re.MULTILINE)
    assert match, "CITATION.cff has no top-level version field"
    assert match.group(1) == _pyproject_version()


def test_latest_changelog_release_matches_pyproject() -> None:
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, flags=re.MULTILINE)
    assert match, "CHANGELOG.md has no released version heading"
    assert match.group(1) == _pyproject_version()


def test_readme_cites_the_pyproject_version() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    match = re.search(r"Cite version \*\*(\d+\.\d+\.\d+)\*\*", readme)
    assert match, "README.md has no 'Cite version **X.Y.Z**' line"
    assert match.group(1) == _pyproject_version()
