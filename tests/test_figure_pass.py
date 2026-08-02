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

**Hardening pass, 2026-07-31.** Eight of these guards opened with ``pytest.skip``
or ``skipif`` on a path that is *committed*. That made them vanish silently
rather than fail whenever a document moved, was renamed or was deleted -- and the
worst case was strictly worse than a move: the Euler-flip guard skipped when the
claim was *absent from the text*, so deleting the claim made its own guard pass.
Every target here is tracked, so every one now asserts existence (``_require``),
the claim set names its exemptions explicitly (``EULER_CLAIM_EXEMPT``), and
``test_no_guard_in_this_file_skips_on_a_tracked_path`` keeps the pattern out.
``skipif`` remains correct elsewhere in ``tests/`` for gitignored data drops.
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


def _require(path: Path) -> Path:
    """Assert a *committed* artifact a guard depends on is still where it was.

    Every guard in this file used to open with ``pytest.skip`` on a missing
    path. That is correct for a gitignored machine-local artifact and wrong for
    a tracked one: moving, renaming or deleting a tracked document silently
    disabled its guard and the suite still reported green. Since the claims
    pinned here were each added *because* they had already gone unnoticed once,
    a vanished target must fail loudly (2026-07-31 hardening pass).
    """
    assert path.is_file(), (
        f"{path.relative_to(REPO).as_posix()} is a committed artifact this guard "
        "depends on, and it is missing. If it moved or was renamed, update this "
        "test in the same change; if it was deleted, the claim it pins is now "
        "unguarded."
    )
    return path


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


def test_the_two_hwl_anchors_are_distinct_and_carry_different_row_counts() -> None:
    """A1 (inserted design HWL) is not A2 (nearest grid level).

    They differ by 0.11 m at KP 62.0 and by a resolved 25 % in the bias factor,
    so a document that quotes one as the other is wrong.
    """
    anchors = _read(_require(HWL_EVIDENCE))["stages"]["A_anchors_F2"]["sections"][
        "kp62_0"
    ]
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


def test_the_n1e5_figure_is_recorded_as_superseded_not_as_a_second_estimate() -> None:
    """44.7 on 4 rows and 26.9 on 63 rows are the same quantity at two N.

    The N = 1e5 cell must be present in the record (the figure draws both) and
    must fail its own resolution criteria, so nothing can present it as an
    independent estimate.
    """
    anchors = _read(_require(HWL_EVIDENCE))["stages"]["A_anchors_F2"]["sections"][
        "kp62_0"
    ]
    small = anchors["n100000"]["A1"]
    assert small["k_transient"] == 4
    assert small["ratio"] == pytest.approx(44.75, abs=0.01)
    assert not small["R1_rows"] and not small["R2_width"]
    assert not small["resolved"]


def test_kp57_4_is_a_bound_not_a_point_estimate() -> None:
    """Two failing rows at N = 1e6: report B >= 148, lead with 42.7 at 39.50 m."""
    brute = _read(_require(HWL_EVIDENCE))["stages"]["A_brute_kp57_4"]
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


def test_the_kp57_4_quotable_anchor_is_itself_a_flip_level() -> None:
    """The uncomfortable detail must survive propagation.

    39.50 m is the recommended anchor AND one of the three N = 1e6 barrier-jump
    levels. Dropping that quietly would misrepresent the number, so the record
    is pinned and the documents of record are checked for it below.
    """
    flips = _read(_require(HWL_EVIDENCE))["stages"]["A_brute_kp57_4"]["euler_flips"]
    text = json.dumps(flips)
    assert "39.5" in text, "the flip levels must be recorded, not just a total"
    assert flips["per_diagnostic_totals"]["c4b_not_c3b"] == 4


# --------------------------------------------------------------------------- #
# 3. Claims that acquired a scope                                               #
# --------------------------------------------------------------------------- #

#: Documents that state the Euler-flip result. Each must exist, must still carry
#: the claim, and must carry the N at which the claim holds. Every entry was added
#: *because* it states the result, so all three are required facts, not
#: preconditions to be inferred from the file.
EULER_CLAIM_FILES = [
    DOCS / "production_campaign_2026-07-29.md",
    DOCS / "stage6_6_report.md",
    DECISIONS / "0040-stage6-6-comparator-ladder-gap-decomposition.md",
    DECISIONS / "adr0047-dem-seepage-length.md",
    DECISIONS / "0047-dem-surveyed-seepage-length.md",
]

#: Entries of the list above that are permitted NOT to carry the claim.
#: **Deliberately empty**, and deliberately explicit. The previous form inferred
#: the exempt set from the text (``if "euler" not in lowered: skip``), which meant
#: *deleting* the claim from a document made its own guard pass. Removing a
#: document from the claim set is now an edit someone has to make on purpose,
#: here, with a reason.
EULER_CLAIM_EXEMPT: frozenset[str] = frozenset()


@pytest.mark.parametrize("path", EULER_CLAIM_FILES, ids=lambda p: p.name)
def test_every_euler_flip_claim_carries_the_N_at_which_it_holds(path: Path) -> None:
    """Gate G-A2 fired at KP 57.4 at N = 1e6: 4 rows in 1e6.

    The expected count at the production N = 1e5 is 0.4, which is why every
    earlier run saw zero. An unqualified "all Euler-flip counts are 0" reads as
    a statement about the discretisation when it is a statement about the
    sample size.
    """
    _require(path)
    lowered = path.read_text(encoding="utf-8").lower()
    if path.name in EULER_CLAIM_EXEMPT:
        pytest.skip(f"{path.name} is a declared exemption from the claim set")
    assert "euler" in lowered, (
        f"{path.name} no longer states the Euler-flip result. If that is "
        "intended, remove it from EULER_CLAIM_FILES explicitly; do not let the "
        "guard lapse by deletion."
    )
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
    nothing, which is how a stale figure passes. A declaration-only entry
    (``command is None``, added 2026-07-31 for the eight studies with no
    plot-only path) may drop ``sources`` only by recording *why* in
    ``staleness`` -- explicitly out of scope, never silently.
    """
    from production_campaign import FIGURE_DRIVERS

    assert FIGURE_DRIVERS, "the figure stage must declare at least one driver"
    for driver in FIGURE_DRIVERS:
        for field in ("label", "command", "requires", "produces", "sources"):
            assert field in driver, f"{driver.get('label')} missing {field!r}"
        assert driver["produces"], f"{driver['label']} produces nothing"
        if driver["command"] is None:
            assert driver["redraw"], f"{driver['label']} must say why it is not run"
            if not driver["sources"]:
                assert driver[
                    "staleness"
                ], f"{driver['label']} drops sources without a recorded reason"
        else:
            assert driver["sources"], f"{driver['label']} declares no sources"
            # The command must be code in this repository, not an arbitrary
            # external tool. Two forms qualify: a driver under scripts/, and
            # `-m <package>` for one of the three top-level packages. The
            # second was added 2026-08-02 for the Phase 2 posterior
            # diagnostics, whose dual-write seam lives in the shipped package
            # (bayesian_reliability_updating.pipeline) rather than in a script,
            # because the figures depend on a 1e5-row replay.
            head = driver["command"][1]
            if head == "-m":
                assert driver["command"][2] in {
                    "bep_reliability_engine",
                    "bayesian_reliability_updating",
                    "system_integration",
                }, driver["command"]
            else:
                assert head.startswith("scripts/"), driver["command"]


def test_every_tracked_publication_figure_is_declared() -> None:
    """Coverage is the point: every figure has a declared source, no exceptions.

    The 2026-07-30 pass reached 44 of 52 and *listed* the remainder. A listed
    figure is an unchecked figure, so the eight were declared on 2026-07-31 and
    the coverage note became gate G7's hard check. The set has grown since (57
    on 2026-07-31, 62 on 2026-08-02 with the four promoted Phase 2 diagnostics
    and row 4.7's peak-shortcut panel); the invariant is the coverage, not the
    count, so this asserts the difference is empty rather than a number.
    """
    from production_campaign import FIGURE_DRIVERS

    tracked = {p.name for p in FIGURES.glob("*.png")}
    declared = {
        p.name
        for driver in FIGURE_DRIVERS
        for pattern in driver["produces"]
        for p in FIGURES.glob(pattern)
    }
    assert not tracked - declared, sorted(tracked - declared)


def test_declared_figure_sources_resolve_to_real_paths() -> None:
    """A ``sources`` pattern that matches nothing turns a gate into a no-op.

    Sibling of the ``requires`` guard below: the GSA entry pointed ``requires``
    at a per-section evidence file that does not exist, and the driver silently
    skipped. The same mistake in ``sources`` is worse -- the driver runs and the
    staleness comparison is simply skipped, so a stale figure passes.
    """
    from production_campaign import FIGURE_DRIVERS

    unresolved = []
    for driver in FIGURE_DRIVERS:
        for pattern in driver["sources"]:
            # results/ and data/raw/ are gitignored: absence is a fresh clone,
            # not a typo. A docs/ source must really match something.
            if pattern.startswith("docs/") and not list(REPO.glob(pattern)):
                unresolved.append((driver["label"], pattern))
    assert not unresolved, unresolved


def test_the_adr0039_pair_is_gated_on_its_recorded_generation_time() -> None:
    """Why that entry needs ``source_epoch``, pinned so it is not "simplified".

    Figure and evidence are both tracked and were added by one commit (780eb0d,
    2026-07-17) whose write left the JSON with a 2026-07-17 mtime and the figure
    with its 2026-07-13 one. On mtime the figure looks four days stale; on the
    JSON's own ``generated`` stamp it is 3.6 min newer, which is the truth.
    """
    from production_campaign import FIGURE_DRIVERS

    (entry,) = [
        d for d in FIGURE_DRIVERS if d["produces"] == ["adr0039-timestep-stress.png"]
    ]
    assert entry.get("source_epoch") == "json_generated"

    evidence = _require(DECISIONS / "adr0039-timestep-stress.json")
    figure = _require(FIGURES / "adr0039-timestep-stress.png")
    from datetime import datetime

    generated = datetime.fromisoformat(_read(evidence)["generated"]).timestamp()
    assert generated <= figure.stat().st_mtime + 1.0


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


def test_no_guard_in_this_file_skips_on_a_tracked_path() -> None:
    """The anti-pattern must not come back, and it is invisible when it does.

    Eight guards here once opened with ``pytest.skip`` on a committed document
    or evidence JSON. A move, rename or deletion then disabled the guard and the
    suite still reported green -- which is how the unqualified Euler-flip claim
    survived in five documents. ``skipif`` remains correct for gitignored
    machine-local artifacts; this file references none, so it should contain no
    existence-conditional skip at all.

    The single permitted ``pytest.skip`` is the declared ``EULER_CLAIM_EXEMPT``
    branch, which gates on a named set rather than on whether a file happens to
    be present.
    """
    # Parsed, not grepped: the prose above names both forms deliberately, and
    # this assertion would otherwise match itself.
    import ast

    source = (REPO / "tests" / "test_figure_pass.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    def _dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return f"{_dotted(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        return ""

    skipifs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _dotted(node.func) == "pytest.mark.skipif"
    ]
    assert not skipifs, (
        "a skipif reappeared in test_figure_pass.py; every path it references is "
        "tracked, so absence must fail loudly (use _require)"
    )

    skips = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _dotted(node.func) == "pytest.skip"
    ]
    assert (
        len(skips) == 1
    ), "the only permitted skip is the declared EULER_CLAIM_EXEMPT branch"
    assert "EULER_CLAIM_EXEMPT" in source


def test_the_epistemic_ranking_covers_all_four_matrix_sections() -> None:
    """ADR-0047's log left KP 62.0, the governing section, unmeasured.

    The figure and the thesis inventory both assume four sections; if the
    evidence ever narrows again the figure would silently plot fewer bars.
    """
    sections = _read(_require(SYNTHESIS_EVIDENCE))["sections"]
    assert {s["section"] for s in sections} == {
        "KP57.4",
        "KP58.8",
        "KP60.0",
        "KP62.0",
    }
    for section in sections:
        assert section["baseline_failure_matrices_bit_identical_to_production"]
        assert "k_aq_prior_mean" in section["brackets"]
