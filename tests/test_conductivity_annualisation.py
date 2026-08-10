"""Guards for the conductivity-bracket annualisation companion (2026-08-10).

The study answers defence-brief item A2: does the largest declared epistemic
unknown in the project, the aquifer conductivity prior mean, change the answers
the thesis actually reports? Those answers are **annualised**, and every prior
measurement of that bracket (ADR-0048, ``epistemic-bracket-synthesis.md``) had
stopped at the conditional fragility curve.

What is pinned here, and why each one earned a guard:

1. **The scope sentence travels with the numbers.** The result is matrix-d70 and
   prior-side only; a bulk-d70 conductivity arm has never been run. A number
   quoted without that is a different claim.
2. **Gate 1 is recorded as passed, over a non-trivial row count.** The whole
   study is worthless if its pipeline does not reproduce the production
   annualisation, so the record must carry the evidence that it did.
3. **The pre-registration is scored honestly.** P1 failed. A later edit that
   quietly flipped it to "held" would erase the study's most useful finding, so
   the failure itself is pinned, together with F5 having fired where it said it
   would.
4. **"No mechanism loaded" is never reported as a share.** The composition
   returns 0.0 for a cell where nothing is loaded, which on a dominance axis is
   indistinguishable from "overflow takes all of it" -- the opposite reading.
5. **The figure is declared, and by exact name.**

Every path referenced here is committed, so absence asserts rather than skips
(conventions section 9.4).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DECISIONS = REPO / "docs" / "decisions"
FIGURES = REPO / "docs" / "figures"
EVIDENCE = DECISIONS / "conductivity-bracket-annualisation.json"
NOTE = DECISIONS / "conductivity-bracket-annualisation.md"
DRIVER = REPO / "scripts" / "conductivity_annualisation_study.py"
FIGURE = FIGURES / "conductivity_bracket_annual.png"

sys.path.insert(0, str(REPO / "scripts"))

SECTIONS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")
SCENARIOS = ("historical", "+4K")
CONDUCTIVITY_ARMS = (
    "k_aq_field_geomean",
    "k_aq_field_toe",
    "k_aq_regional_upper",
)


def _require(path: Path) -> Path:
    """Assert a committed artifact this guard depends on is still present."""
    assert path.is_file(), (
        f"{path.relative_to(REPO).as_posix()} is a committed artifact this guard "
        "depends on, and it is missing. If it moved or was renamed, update this "
        "test in the same change; if it was deleted, the claim it pins is now "
        "unguarded."
    )
    return path


def _evidence() -> dict:
    return json.loads(_require(EVIDENCE).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# 1. Scope                                                                      #
# --------------------------------------------------------------------------- #


def test_the_scope_is_recorded_as_matrix_and_prior_only() -> None:
    """The result is not portable to the bulk grain size or the posterior.

    ADR-0048's arms exist only under matrix d70, and no Phase 2 posterior was
    ever computed for a conductivity scenario. The comparison is therefore
    prior-against-prior, which is exact at KP 62.0 (the 2016 update rejects
    0.00 % there) and a documented campaign variant everywhere else.
    """
    scope = _evidence()["scope"]
    assert scope["d70_interpretation"] == "matrix"
    assert scope["bep_source"] == "prior"
    assert scope["lambda_ac_m"] == 250.0
    assert scope["surface_variant"] == "primary"
    assert sorted(scope["scenarios"]) == sorted(SCENARIOS)
    statement = scope["statement"].lower()
    assert "matrix" in statement and "prior" in statement
    assert "bulk" in statement, "the absent bulk arm must be named, not implied"


def test_the_note_leads_with_the_scope_rather_than_footnoting_it() -> None:
    """A scope that arrives after the headline is a scope nobody quotes."""
    text = _require(NOTE).read_text(encoding="utf-8")
    head = text[: text.index("## Part 1")]
    assert "matrix-d70 and prior-side only" in head
    assert "bulk-d70 conductivity arm has never been run" in head


# --------------------------------------------------------------------------- #
# 2. Gate 1                                                                     #
# --------------------------------------------------------------------------- #


def test_gate_one_reproduced_the_production_table_over_every_published_row() -> None:
    """Without this the arms measure something, but not the thesis's quantity.

    The production campaign's own G4 gate asserts ``rq4_annual.csv`` has zero
    changed rows; this study must reproduce the matrix / prior / 250 m / primary
    slice of that same table field for field before any arm number is reported.
    """
    gate = _evidence()["gates"]["gate_1_reproduces_production_table"]
    assert gate["passed"] is True
    # 114 segments x 2 scenarios. A shrinking count would mean the comparison
    # quietly narrowed to the four BEP sections.
    assert gate["rows_compared"] == 228
    assert gate["fields_compared"] == 20
    assert gate["table"].endswith("rq4_annual.csv")


def test_the_non_bep_segments_are_asserted_invariant_under_every_arm() -> None:
    """A conductivity scenario cannot reach a segment with no BEP source.

    110 of the 114 segments carry ``bep_source = None`` and are surface-only.
    If an arm moved one, the substitution would have leaked somewhere it does
    not belong.
    """
    gate = _evidence()["gates"]["gate_3_non_bep_segments_invariant"]
    assert gate["passed"] is True
    assert gate["segment_scenario_cells_checked"] > 0


def test_the_hazard_cache_was_reused_and_not_rewritten() -> None:
    """The hazard has no conductivity dependence, so re-streaming it is waste.

    It is also a correctness signal: a rewritten cache entry would mean a node
    datum moved, and a moved datum means the arms were not compared against the
    production hazard.
    """
    gate = _evidence()["gates"]["gate_4_hazard_cache_unchanged"]
    assert gate["passed"] is True
    assert gate["cache_files"] > 0


# --------------------------------------------------------------------------- #
# 3. The pre-registration, including the part that failed                       #
# --------------------------------------------------------------------------- #


def test_prediction_one_is_recorded_as_failed_and_kept_that_way() -> None:
    """The most useful result in the study is a prediction that did not hold.

    Part 1 predicted, on the brief's framing, that KP 62.0 would be the only
    section whose historical mechanism ordering the bracket could contest. Three
    of four sections move historically. Silently upgrading this to "held" would
    delete the finding, so the failure is pinned.
    """
    outcome = _evidence()["preregistration_outcome"]
    assert outcome["P1"]["held"] is False
    reversed_sections = outcome["P1"]["sections_reversing_historically"]
    assert "KP 62.0" in reversed_sections
    assert "KP 58.8" in reversed_sections, (
        "KP 58.8 reversing historically is precisely what refutes P1; if it "
        "stops reversing, the note's Part 2 verdict has to be rewritten"
    )


def test_the_named_falsifier_fired_where_it_said_it_would() -> None:
    """F5 named KP 58.8 historical in advance as P1's failure mode.

    A pre-registration that names where it will break, and then breaks exactly
    there, is evidence the mechanism was understood rather than fitted
    afterwards.
    """
    outcome = _evidence()["preregistration_outcome"]
    assert outcome["F5"]["fired"] is True


def test_the_upward_arm_reverses_nothing_anywhere() -> None:
    """P4, and the sign check on ADR-0048's monotone mechanism.

    Higher conductivity raises the response factor and lowers the critical
    head, both pushing piping probability up. Since piping already leads
    everywhere at the production value, a reversal under the upward arm would
    indict the arms or this pipeline rather than reveal physics (falsifier F1).
    """
    outcome = _evidence()["preregistration_outcome"]
    assert outcome["P4"]["held"] is True
    assert outcome["F1"]["fired"] is False

    sections = _evidence()["sections"]
    for label in SECTIONS:
        for scenario in SCENARIOS:
            entry = sections[label][scenario]
            assert (
                "k_aq_regional_upper" not in entry["arms_reversing_the_lead"]
            ), f"{label} {scenario}"


def test_the_blanket_unit_weight_control_stays_quiet() -> None:
    """P7: the negative control that says the machinery is not inventing motion.

    The committed ADR-0048 record shows this arm inert to five decimals at
    KP 62.0 conditionally. If it moved the annualised numbers materially, the
    conductivity result would be an artifact of the pipeline rather than of
    conductivity.
    """
    outcome = _evidence()["preregistration_outcome"]
    assert outcome["P7"]["held"] is True
    for row in outcome["P7"]["cells"]:
        assert row["at_least_ten_times_quieter"], row


def test_the_bracket_is_wider_than_the_length_effect_yardstick_everywhere() -> None:
    """F3 was the falsifier that would have deflated the study, and it did not fire.

    If annualisation had compressed conductivity below the length-effect bracket
    the thesis already carries, then calling it the largest declared unknown
    would be true of the conditional curves and false of the deliverable. It is
    wider at every section and scenario.
    """
    outcome = _evidence()["preregistration_outcome"]
    assert outcome["F3"]["fired"] is False
    for row in outcome["F3"]["cells"]:
        assert row["conductivity_is_wider"], row
        # ``None`` marks an unbounded span (an arm gives exactly zero), which is
        # wider than any finite yardstick by definition.
        if row["conductivity_span"] is not None:
            assert row["conductivity_span"] > row["length_effect_span"]


# --------------------------------------------------------------------------- #
# 4. "Not defined" is not a share                                               #
# --------------------------------------------------------------------------- #


def test_an_unloaded_cell_is_classified_apart_from_a_reversal() -> None:
    """Nothing loaded is not the same claim as the other mechanism leading.

    At KP 57.4 historical the lowest arm drives piping AND overflow to exactly
    zero. The composition reports a 0.0 share there, which on a dominance axis
    reads as "overflow takes all of it" -- the opposite of the truth. The
    verdict vocabulary keeps the two apart.
    """
    sections = _evidence()["sections"]
    entry = sections["KP 57.4"]["historical"]
    assert entry["ordering_verdict"] == "COLLAPSED"
    assert entry["arms_reversing_the_lead"] == []
    assert "k_aq_field_geomean" in entry["arms_collapsing_to_undefined"]
    assert entry["arms"]["k_aq_field_geomean"]["leading_mechanism"] == "not defined"
    # And the baseline it collapses from really does have zero overflow, which
    # is why a reversal there is structurally impossible (P5).
    assert entry["baseline"]["p_annual_overflow"] == 0.0


def test_the_figure_withholds_an_undefined_share_from_the_dominance_line() -> None:
    """Pinned at the source, because a PNG holds no extractable text.

    The one cell with nothing loaded must not be drawn on the share axis as a
    data point. The driver skips it and marks it separately; this asserts the
    skip is still there rather than trusting a visual re-read.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    tree = ast.parse(source)
    (render,) = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "render_figure"
    ]
    compared = [
        node
        for node in ast.walk(render)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(c, ast.Constant) and c.value == "not defined"
            for c in node.comparators
        )
    ]
    assert compared, (
        "render_figure no longer tests for an undefined leading mechanism; an "
        "unloaded cell would be plotted at a share of 0.0, which reads as the "
        "other mechanism taking all of it"
    )


# --------------------------------------------------------------------------- #
# 5. Campaign wiring and driver hygiene                                         #
# --------------------------------------------------------------------------- #


def test_the_figure_is_declared_in_the_campaign_by_exact_name() -> None:
    """Gate G7 asserts every tracked publication figure is declared.

    The name is exact rather than a glob: a ``conductivity_*.png`` pattern that
    later swept up a sibling would bind it to this driver's sources and leave it
    un-redrawn, which is the trap the 2026-07-31 pass recorded for the shared
    C_e glob.
    """
    from production_campaign import FIGURE_DRIVERS

    (entry,) = [
        d
        for d in FIGURE_DRIVERS
        if d["produces"] == ["conductivity_bracket_annual.png"]
    ]
    assert entry["command"] is not None, "a real plot-only path exists; use it"
    assert entry["command"][-1] == "--figures-only"
    assert entry["requires"] == [
        "docs/decisions/conductivity-bracket-annualisation.json"
    ]
    assert entry["sources"] == [
        "docs/decisions/conductivity-bracket-annualisation.json"
    ]
    _require(FIGURE)


def test_the_redraw_path_writes_no_evidence_record() -> None:
    """``--figures-only`` must not be able to overwrite the committed record.

    Conventions section 9.4: gate before the write when the write overwrites a
    guarded artifact. Here the stronger form applies -- the redraw path simply
    has no write to guard, so a figure refresh can never truncate the evidence
    the note is built from.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    tree = ast.parse(source)
    (main_fn,) = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    branch = [
        node
        for node in ast.walk(main_fn)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Attribute)
        and node.test.attr == "figures_only"
    ]
    assert branch, "the --figures-only early-exit branch is gone"
    writes = [
        node
        for node in ast.walk(branch[0])
        if isinstance(node, ast.Attribute)
        and node.attr in {"write_text", "write_bytes"}
    ]
    assert not writes, "the figures-only branch must write no record"
    returns = [node for node in ast.walk(branch[0]) if isinstance(node, ast.Return)]
    assert returns, "the figures-only branch must exit before the study runs"


def test_the_composition_step_is_imported_not_reimplemented() -> None:
    """Gate 1 only means something if it exercises the production composition.

    A second copy of ``_compose_segment`` could drift from the one that produced
    the published table, and the gate would then pass against a private
    duplicate. Same reasoning as the ADR-0047 ratio kernel, which
    ``epistemic_bracket_synthesis.py`` imports rather than copies.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    assert "_load_campaign_module" in source
    assert "phase3_campaign.py" in source
    assert (
        "def _compose_segment" not in source
    ), "the composition must be imported from the campaign, never redefined here"


def test_the_driver_does_not_modify_the_production_phase3_outputs() -> None:
    """The campaign's G4 gate asserts ``rq4_annual.csv`` has zero changed rows.

    This study reads that table and must never write into that directory; its
    own outputs live under ``results/sensitivity/conductivity_annualisation/``.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    assert "results/system_integration/phase3" not in source.replace("\\", "/") or (
        "PRODUCTION_TABLE" in source
    )
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in {
            "write_text",
            "write_bytes",
        }:
            target = ast.unparse(node.value)
            assert "PRODUCTION_TABLE" not in target, target


def test_no_existence_guard_in_this_file_skips_on_a_tracked_path() -> None:
    """The silent-skip class, kept out of this file by parse rather than grep.

    Conventions section 9.4: skipping on a committed path means a move, rename
    or deletion disables the guard while the suite still reports green. Every
    path referenced here is tracked, so this file should contain no
    existence-conditional skip at all. Parsed rather than grepped for the same
    reason its sibling in ``test_figure_pass.py`` is: a string check matches its
    own explanation.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))

    def _dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return f"{_dotted(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        return ""

    offenders = [
        _dotted(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _dotted(node.func) in {"pytest.skip", "pytest.mark.skipif"}
    ]
    assert not offenders, offenders
