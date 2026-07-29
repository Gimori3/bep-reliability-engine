"""Repository-hygiene guards.

These tests assert facts about the shape of the repository rather than about
any physics. They exist because both facts were violated in practice and the
violation was invisible until someone went looking.

Between 2026-07-12 and 2026-07-29 seven ``_thesis_*.tex`` / ``_thesis_*.bib``
files accumulated at the repository root. The 2026-07-29 audit
(``msc-thesis/scratch/THESIS_FRAGMENT_AUDIT.md``) found that they had silently
become the *pre-as-built* drafts: they still asserted an r_e-translated static
head (ADR-0028 reversed it), the native integration timestep (ADR-0030), the
withdrawn L/lambda_in validity alarm, the refuted foreshore-width control on
risk (ADR-0025 amendment) and the refuted LHS tail-variance advantage (fm5).
Nothing in the test suite or the ADR process governed them, so nothing caught
the drift. The rule and its rationale are recorded in ``docs/conventions.md``
section 8: thesis text lives only in ``d:\\repositories\\msc-thesis``.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: Extensions that indicate thesis source rather than engine source.
THESIS_SUFFIXES = {".tex", ".bib", ".cls", ".bbl", ".sty"}


def test_no_thesis_fragments_at_the_repository_root() -> None:
    """No ``_thesis*`` .tex/.bib file may reappear at the repository root.

    This is the exact shape of the retired artifacts. A finding reaches the
    thesis by a targeted edit to the relevant msc-thesis chapter; work
    products of record belong under ``docs/``.
    """
    offenders = sorted(
        p.name
        for p in REPO.glob("_thesis*")
        if p.is_file() and p.suffix.lower() in THESIS_SUFFIXES
    )
    assert not offenders, (
        "Thesis source reappeared at the engine repo root: "
        f"{offenders}. Thesis text lives only in d:\\repositories\\msc-thesis "
        "(docs/conventions.md section 8). Write findings to docs/ instead, and "
        "make a targeted edit to the relevant msc-thesis chapter if the thesis "
        "genuinely needs the finding."
    )


def test_no_thesis_source_anywhere_in_the_tracked_tree() -> None:
    """The rule is about the repository, not just its root directory.

    Moving a fragment into ``docs/`` or ``notebooks/`` would evade the root
    check while recreating exactly the problem the rule prevents: a second,
    ungoverned copy of the thesis record that drifts silently.
    ``docs/references/`` is excluded because it holds gitignored reference
    PDFs, and the virtual environment and build caches are not ours.
    """
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}
    offenders = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in THESIS_SUFFIXES:
            continue
        parts = set(path.relative_to(REPO).parts)
        if parts & skip_dirs:
            continue
        offenders.append(path.relative_to(REPO).as_posix())

    assert not offenders, (
        "LaTeX/BibTeX source found in the engine repository: "
        f"{sorted(offenders)}. See docs/conventions.md section 8."
    )


def test_the_conventions_document_still_carries_the_rule() -> None:
    """The rule must survive in a *tracked* file.

    ``project-notes.md`` is gitignored here (``.gitignore``), so a rule written only
    there is machine-local and does not reach a fresh clone.
    ``docs/conventions.md`` is tracked, which is why the rule lives there and
    ``project-notes.md`` only points at it.
    """
    conventions = (REPO / "docs" / "conventions.md").read_text(encoding="utf-8")
    assert "Thesis text does not live in this repository" in conventions
    assert "msc-thesis" in conventions
    assert "XeLaTeX" in conventions
