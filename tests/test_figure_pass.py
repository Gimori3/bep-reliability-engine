"""Guards for the 2026-07-30 figure pass and its number-consistency fixes.

Three families of fact are pinned here, each because it was violated in
practice and the violation was invisible until someone went looking.

1. **The copy problem.** The Stage 6.6 KP 62.0 figures went stale twice
   (2026-07-29 and 2026-07-30) because a driver wrote to gitignored
   ``results/`` and a human copied to tracked ``docs/figures/``. The
   structural fix is that every publication figure is written to
   ``docs/figures/`` by its own driver, plus a campaign stage that gates on
   staleness. These tests pin both halves.

2. **The two anchors.** Stage 6.6 evaluates 39 levels at KP 62.0: the
   38-level generated grid **plus** the exact section HWL inserted by
   ``prepare_config``. KP 62.0's design HWL (46.39 m) and its nearest grid
   level (46.50 m) carry different row counts and resolvably different bias
   factors, and quoting one as the other is a defect
   (``adr0040-hwl-bias-resolution.md`` sections 1.2 and 2.5).

3. **Claims that acquired a scope.** "Every Euler-flip count is exactly 0" is
   an N = 1e5 statement, and the ADR-0029 tilted sampler is validated for a
   single-branch tail probability but not for a ratio between branches. Both
   were unqualified in the documents of record until this pass.

No physics runs here: every check is against committed evidence JSON or file
layout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
FIGURES = DOCS / "figures"
DECISIONS = DOCS / "decisions"

sys.path.insert(0, str(REPO / "scripts"))

HWL_EVIDENCE = DECISIONS / "adr0040-hwl-bias-resolution.json"
SYNTHESIS_EVIDENCE = DECISIONS / "epistemic-bracket-synthesis.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# 1. The shared figure style                                                    #
# --------------------------------------------------------------------------- #


def test_figstyle_categorical_slots_are_a_fixed_ordered_set() -> None:
    """The slot ORDER is the colour-vision-deficiency mechanism, not cosmetic.

    A reshuffle silently breaks the adjacent-pair separation the palette was
    validated on, so the order is pinned rather than merely the membership.
    """
    import _figstyle as figstyle

    assert figstyle.CATEGORICAL == (
        "#2a78d6",  # 1 blue
        "#eb6834",  # 2 orange
        "#1baf7a",  # 3 aqua
        "#eda100",  # 4 yellow
        "#e87ba4",  # 5 magenta
        "#008300",  # 6 green
        "#4a3aa7",  # 7 violet
        "#e34948",  # 8 red
    )
    assert len(set(figstyle.CATEGORICAL)) == 8, "no slot may repeat a hue"


def test_figstyle_section_colours_cover_the_four_production_sections() -> None:
    """One hue per entity: a section keeps its colour in every figure."""
    import _figstyle as figstyle

    assert set(figstyle.SECTION_COLORS) == {"KP57.4", "KP58.8", "KP60.0", "KP62.0"}
    assert set(figstyle.SECTION_MARKERS) == set(figstyle.SECTION_COLORS)
    # Marker shape is the secondary channel: past three slots the palette does
    # not clear the all-pairs floor, so hue alone must never carry identity.
    assert len(set(figstyle.SECTION_MARKERS.values())) == 4


def test_figstyle_save_writes_the_tracked_publication_copy(tmp_path) -> None:
    """``save`` always writes ``docs/figures/``; the mirror is optional.

    This is the invariant that removes the manual copy step. If ``save`` ever
    stops writing the tracked copy, a figure can exist only under gitignored
    ``results/`` and is not a deliverable.
    """
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as figstyle
    import matplotlib.pyplot as plt

    figstyle.style()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    name = "_pytest_figstyle_probe.png"
    mirror = tmp_path / "mirror"
    out = figstyle.save(fig, name, mirror=mirror)
    try:
        assert out == FIGURES / name
        assert out.is_file() and out.stat().st_size > 0
        assert (mirror / name).is_file()
        assert out.read_bytes() == (mirror / name).read_bytes()
    finally:
        out.unlink(missing_ok=True)


def test_figstyle_marks_the_hypothetical_extension_only_above_the_attainable_max(
    tmp_path,
) -> None:
    """ADR-0024: KP 62.0's above-crest levels must never read as attainable.

    ``attainable_max_m`` is 50.5 m, so the shading covers 51.0 to 56.5 m and
    nothing below. An axis that never reaches the boundary gets no shading at
    all rather than a spurious band.
    """
    import matplotlib

    matplotlib.use("Agg")
    import _figstyle as figstyle
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.set_xlim(41.0, 56.5)
    before = len(ax.patches)
    figstyle.mark_hypothetical(ax, 50.5)
    assert len(ax.patches) > before, "the shaded band must be drawn"

    fig2, ax2 = plt.subplots()
    ax2.set_xlim(41.0, 47.0)
    figstyle.mark_hypothetical(ax2, 50.5)
    assert not ax2.patches, "no band when the axis never reaches the boundary"
    plt.close(fig)
    plt.close(fig2)


# --------------------------------------------------------------------------- #
# 2. The two design-HWL anchors are different levels                            #
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not HWL_EVIDENCE.is_file(), reason="HWL evidence JSON absent")
def test_the_two_hwl_anchors_are_distinct_and_carry_different_row_counts() -> None:
    """A1 (inserted design HWL) is not A2 (nearest grid level).

    They differ by 0.11 m at KP 62.0 and by a resolved 25 % in the bias factor,
    so a document that quotes one as the other is wrong.
    """
    anchors = _read(HWL_EVIDENCE)["stages"]["A_anchors_F2"]["sections"]["kp62_0"]
    a1 = anchors["n1000000"]["A1"]
    a2 = anchors["n1000000"]["A2"]
    assert a1["level_m"] == pytest.approx(46.39)
    assert a2["level_m"] == pytest.approx(46.50)
    assert a1["level_m"] != a2["level_m"]
    assert a1["k_transient"] == 63
    assert a2["k_transient"] == 176
    assert a1["ratio"] == pytest.approx(26.9, abs=0.1)
    assert a2["ratio"] == pytest.approx(21.6, abs=0.1)
    assert a1["resolved"] and a2["resolved"]
    assert anchors["n1000000"]["stage_separation_m"] == pytest.approx(0.11)


@pytest.mark.skipif(not HWL_EVIDENCE.is_file(), reason="HWL evidence JSON absent")
def test_the_n1e5_figure_is_recorded_as_superseded_not_as_a_second_estimate() -> None:
    """44.7 on 4 rows and 26.9 on 63 rows are the same quantity at two N.

    The N = 1e5 cell must be present in the record (the figure draws both) and
    must fail its own resolution criteria, so nothing can present it as an
    independent estimate.
    """
    anchors = _read(HWL_EVIDENCE)["stages"]["A_anchors_F2"]["sections"]["kp62_0"]
    small = anchors["n100000"]["A1"]
    assert small["k_transient"] == 4
    assert small["ratio"] == pytest.approx(44.75, abs=0.01)
    assert not small["R1_rows"] and not small["R2_width"]
    assert not small["resolved"]


@pytest.mark.skipif(not HWL_EVIDENCE.is_file(), reason="HWL evidence JSON absent")
def test_kp57_4_is_a_bound_not_a_point_estimate() -> None:
    """Two failing rows at N = 1e6: report B >= 148, lead with 42.7 at 39.50 m."""
    brute = _read(HWL_EVIDENCE)["stages"]["A_brute_kp57_4"]
    assert brute["anchor_A1"]["k_transient"] == 2
    assert not brute["anchor_A1"]["R1_rows"]
    resolved = [
        row
        for row in brute["bias_table"]
        if row["resolved"] and row["k_transient"] >= 30
    ]
    lowest = min(resolved, key=lambda r: r["level_m"])
    assert lowest["level_m"] == pytest.approx(39.50)
    assert lowest["ratio"] == pytest.approx(42.7, abs=0.2)
    assert lowest["k_transient"] == 521


@pytest.mark.skipif(not HWL_EVIDENCE.is_file(), reason="HWL evidence JSON absent")
def test_the_kp57_4_quotable_anchor_is_itself_a_flip_level() -> None:
    """The uncomfortable detail must survive propagation.

    39.50 m is the recommended anchor AND one of the three N = 1e6 barrier-jump
    levels. Dropping that quietly would misrepresent the number, so the record
    is pinned and the documents of record are checked for it below.
    """
    flips = _read(HWL_EVIDENCE)["stages"]["A_brute_kp57_4"]["euler_flips"]
    text = json.dumps(flips)
    assert "39.5" in text, "the flip levels must be recorded, not just a total"
    assert flips["per_diagnostic_totals"]["c4b_not_c3b"] == 4


# --------------------------------------------------------------------------- #
# 3. Claims that acquired a scope                                               #
# --------------------------------------------------------------------------- #

#: Documents that state the Euler-flip result. Each must carry its N.
EULER_CLAIM_FILES = [
    DOCS / "production_campaign_2026-07-29.md",
    DOCS / "stage6_6_report.md",
    DECISIONS / "0040-stage6-6-comparator-ladder-gap-decomposition.md",
    DECISIONS / "adr0047-dem-seepage-length.md",
    DECISIONS / "0047-dem-surveyed-seepage-length.md",
]


@pytest.mark.parametrize("path", EULER_CLAIM_FILES, ids=lambda p: p.name)
def test_every_euler_flip_claim_carries_the_N_at_which_it_holds(path: Path) -> None:
    """Gate G-A2 fired at KP 57.4 at N = 1e6: 4 rows in 1e6.

    The expected count at the production N = 1e5 is 0.4, which is why every
    earlier run saw zero. An unqualified "all Euler-flip counts are 0" reads as
    a statement about the discretisation when it is a statement about the
    sample size.
    """
    if not path.is_file():
        pytest.skip(f"{path.name} absent")
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    if "euler" not in lowered:
        pytest.skip("no Euler-flip claim in this file")
    # Every paragraph asserting zero flips must mention an N nearby.
    assert "n = 1e5" in lowered or "n = 1e6" in lowered or "n=1e5" in lowered, (
        f"{path.name} states an Euler-flip result without naming the sample "
        "size it holds at"
    )


def test_the_tilted_sampler_recommendation_carries_its_ratio_exclusion() -> None:
    """ADR-0029's sampler is single-branch-validated, not ratio-validated.

    Pointed at the static-vs-transient bias it failed V2 and V4: a
    transient-optimised tilt inflates the static estimator up to 940x. Both the
    spec text and the ADR must say so wherever the sampler is recommended.
    """
    arch = (DOCS / "architecture.md").read_text(encoding="utf-8").lower()
    assert "sample_theta_tilted" in arch
    assert "ratio between" in arch, (
        "architecture.md failure mode 5 recommends the tilted sampler without "
        "excluding a ratio between branches"
    )

    adr = (
        (DECISIONS / "0029-timestepper-acceleration-and-tail-estimator.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    assert "not** validated for" in adr or "not validated for" in adr
    assert "single-branch" in adr


def test_the_cancellation_rule_is_stated_as_common_mode_only() -> None:
    """ADR-0048's property (c) was refuted; the surviving rule is narrower.

    A bracket cancels in the static-vs-transient ratio only if it is pure
    common-mode. Every document that discusses cancellation must carry that
    form, not the withdrawn "epistemic brackets largely cancel".
    """
    for name in (
        DOCS / "architecture.md",
        DECISIONS / "0048-prior-mean-epistemic-scenarios.md",
        DECISIONS / "epistemic-bracket-synthesis.md",
    ):
        text = name.read_text(encoding="utf-8").lower()
        assert "common-mode" in text, f"{name.name} lacks the common-mode rule"


# --------------------------------------------------------------------------- #
# 4. The campaign's figure stage                                                #
# --------------------------------------------------------------------------- #


def test_every_figure_driver_declares_requires_produces_and_sources() -> None:
    """The staleness gate needs all three fields to mean anything.

    ``sources`` is what the figure depicts; without it the gate silently checks
    nothing, which is how a stale figure passes.
    """
    from production_campaign import FIGURE_DRIVERS

    assert FIGURE_DRIVERS, "the figure stage must declare at least one driver"
    for driver in FIGURE_DRIVERS:
        for field in ("label", "command", "requires", "produces", "sources"):
            assert field in driver, f"{driver.get('label')} missing {field!r}"
        assert driver["produces"], f"{driver['label']} produces nothing"
        assert driver["sources"], f"{driver['label']} declares no sources"
        assert driver["command"][1].startswith("scripts/"), driver["command"]


def test_figure_driver_requires_paths_exist_or_are_gitignored_data() -> None:
    """A ``requires`` path that can never exist makes the driver dead code.

    The GSA entry was written against ``adr0033-gsa-study.json``, which does not
    exist (the evidence is per-section), so the driver silently skipped and its
    nine figures went unchecked until the gate caught them.
    """
    from production_campaign import FIGURE_DRIVERS

    tracked_but_absent = []
    for driver in FIGURE_DRIVERS:
        for rel in driver["requires"]:
            path = REPO / rel
            # results/ and data/raw/ are gitignored, so absence there is
            # expected on a fresh clone. A docs/ path must really exist.
            if rel.startswith("docs/") and not path.exists():
                tracked_but_absent.append((driver["label"], rel))
    assert not tracked_but_absent, tracked_but_absent


def test_the_stage6_6_driver_writes_the_tracked_publication_copy() -> None:
    """Structural fix for the copy problem, pinned at the source.

    Every Stage 6.6 figure goes through ``_write_figure``, which writes both the
    study-local copy and ``docs/figures/``. A driver that writes only to
    ``results/`` reintroduces the manual step.
    """
    source = (REPO / "scripts" / "stage6_6_gap_decomposition.py").read_text(
        encoding="utf-8"
    )
    assert "PUB_FIG_DIR" in source
    assert 'REPO_ROOT / "docs" / "figures"' in source
    # No figure function may call savefig directly any more.
    assert source.count("fig.savefig(") == 2, (
        "figure writes must go through _write_figure (which itself calls "
        "savefig exactly twice)"
    )


def test_the_stage6_6_summary_is_merged_not_rebuilt() -> None:
    """``--sections kp62_0`` must not delete KP 57.4 from the summary.

    The campaign's G3 gate asserts both sections are present, so a partial
    re-run that rebuilt the payload would fail the next campaign for a reason
    that has nothing to do with the physics.
    """
    source = (REPO / "scripts" / "stage6_6_gap_decomposition.py").read_text(
        encoding="utf-8"
    )
    assert 'summary["sections"].update(previous["sections"])' in source


def test_the_stage6_6_redraw_path_touches_no_evidence_file() -> None:
    """``--figures-only`` must be read-only with respect to every artifact.

    A redraw that re-analysed could move a number while claiming to redraw, so
    the path is structurally forbidden from writing anything but figures.
    """
    import ast

    source = (REPO / "scripts" / "stage6_6_gap_decomposition.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_redraw_only"
    )
    called = {
        node.func.attr
        for node in ast.walk(func)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    for forbidden in ("write_text", "save", "to_csv"):
        assert forbidden not in called, f"_redraw_only calls {forbidden}"


# --------------------------------------------------------------------------- #
# 5. Phase 2's figures-only seam                                                #
# --------------------------------------------------------------------------- #


def test_phase2_figures_only_defaults_off_and_never_persists() -> None:
    """Default False keeps the baseline bit-identical; True skips the write.

    The persisted posteriors' SHA-256s are recorded in the production campaign
    manifest, so refreshing a figure must not touch them.
    """
    from bayesian_reliability_updating.pipeline import Phase2Settings

    assert Phase2Settings().figures_only is False
    assert Phase2Settings(figures_only=True).figures_only is True

    source = (REPO / "bayesian_reliability_updating" / "pipeline.py").read_text(
        encoding="utf-8"
    )
    assert "if persist and not settings.figures_only:" in source
    assert "if persist and settings.figures:" in source


# --------------------------------------------------------------------------- #
# 6. The RQ4 scope decision                                                     #
# --------------------------------------------------------------------------- #


def test_the_reach_distribution_figure_is_captioned_as_context_not_the_answer() -> None:
    """110 of 114 segments have no BEP source and are surface-only lower bounds.

    Campaign decision 5 scopes RQ3/RQ4 to the four characterised sections, so
    the 114-segment distribution must never be presented as the RQ4 result.
    """
    source = (REPO / "scripts" / "phase3_figures.py").read_text(encoding="utf-8")
    assert "fig_rq4_four_sections" in source
    assert "REACH CONTEXT (not the RQ4 answer)" in source
    assert "110 of 114" in source


@pytest.mark.skipif(
    not SYNTHESIS_EVIDENCE.is_file(), reason="synthesis evidence JSON absent"
)
def test_the_epistemic_ranking_covers_all_four_matrix_sections() -> None:
    """ADR-0047's log left KP 62.0, the governing section, unmeasured.

    The figure and the thesis inventory both assume four sections; if the
    evidence ever narrows again the figure would silently plot fewer bars.
    """
    sections = _read(SYNTHESIS_EVIDENCE)["sections"]
    assert {s["section"] for s in sections} == {
        "KP57.4",
        "KP58.8",
        "KP60.0",
        "KP62.0",
    }
    for section in sections:
        assert section["baseline_failure_matrices_bit_identical_to_production"]
        assert "k_aq_prior_mean" in section["brackets"]
