"""Guards for the conductivity-bracket annualisation companion (2026-08-10).

The study answers defence-brief item A2: does the largest declared epistemic
unknown in the project, the aquifer conductivity prior mean, change the answers
the thesis actually reports? Those answers are **annualised**, and every prior
measurement of that bracket (ADR-0048, ``epistemic-bracket-synthesis.md``) had
stopped at the conditional fragility curve.

What is pinned here, and why each one earned a guard:

1. **The scope sentence travels with the numbers.** Each record is one
   grain-size reading, prior side only; a number is not portable to the other
   reading or to the posterior. A number quoted without that is a different
   claim. Both co-primary readings now exist (note Part 3, 2026-08-10), so a
   record still saying the bulk arm was never run would be false.
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
BULK_EVIDENCE = DECISIONS / "conductivity-bracket-annualisation-bulk.json"
NOTE = DECISIONS / "conductivity-bracket-annualisation.md"
DRIVER = REPO / "scripts" / "conductivity_annualisation_study.py"
FIGURE = FIGURES / "conductivity_bracket_annual.png"
BULK_FIGURE = FIGURES / "conductivity_bracket_both_d70.png"

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


def _bulk() -> dict:
    return json.loads(_require(BULK_EVIDENCE).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# 1. Scope                                                                      #
# --------------------------------------------------------------------------- #


def test_each_record_states_which_grain_size_reading_it_is() -> None:
    """A number is not portable between the two readings or to the posterior.

    The two grain-size readings are co-primary deliverables, so each record has
    to name its own and point at its companion rather than implying it is the
    result. Neither has a Phase 2 posterior: the comparison is prior-against-
    prior, exact at KP 62.0 (the 2016 update rejects 0.00 % there) and a
    documented campaign variant everywhere else.
    """
    for reading, payload in (("matrix", _evidence()), ("bulk", _bulk())):
        scope = payload["scope"]
        assert scope["d70_interpretation"] == reading
        assert scope["bep_source"] == "prior"
        assert scope["lambda_ac_m"] == 250.0
        assert scope["surface_variant"] == "primary"
        assert sorted(scope["scenarios"]) == sorted(SCENARIOS)
        statement = scope["statement"].lower()
        assert reading in statement and "prior" in statement
        assert (
            "no phase 2 posterior" in statement
        ), "the surviving half of the scope must be named, not implied"


def test_neither_record_still_claims_the_bulk_arm_was_never_run() -> None:
    """The matrix record's own scope sentence was overtaken by this repository.

    Until 2026-08-10 it read "no bulk-d70 conductivity arm has ever been run",
    which was true when written and false the moment the replication landed. A
    record of this kind may not carry a claim its own repository has overtaken,
    so the clause became a pointer to the companion record. The matrix numbers
    were not touched.
    """
    for payload in (_evidence(), _bulk()):
        statement = payload["scope"]["statement"].lower()
        assert "never been run" not in statement
        assert "has ever been run" not in statement


def test_the_note_leads_with_the_scope_rather_than_footnoting_it() -> None:
    """A scope that arrives after the headline is a scope nobody quotes."""
    text = _require(NOTE).read_text(encoding="utf-8")
    # Whitespace-normalised: the note is hard-wrapped, so a sentence the reader
    # sees as one line is several in the source.
    head = " ".join(text[: text.index("## Part 1")].split())
    assert "Part 2 is matrix-d70 and prior-side only" in head
    assert "Part 3 is bulk-d70 and prior-side only" in head
    assert "co-primary" in head
    # The surviving half of the original scope must still be stated up front.
    assert "no Phase 2 posterior exists for" in head


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


# --------------------------------------------------------------------------- #
# 6. The bulk-d70 replication (note Part 3, 2026-08-10)                         #
# --------------------------------------------------------------------------- #


def test_gate_one_reproduced_the_production_table_for_the_bulk_reading() -> None:
    """The bulk arms measure the thesis's quantity only if the baseline does.

    Same standard as the matrix reading: the bulk / prior / 250 m / primary slice
    of the published table, field for field, before any arm number is reported.
    """
    gate = _bulk()["gates"]["gate_1_reproduces_production_table"]
    assert gate["passed"] is True
    assert gate["rows_compared"] == 228
    assert gate["fields_compared"] == 20


def test_the_upward_arm_is_the_one_that_contests_the_ordering_under_bulk() -> None:
    """The structural inversion, and the whole reason bulk needed its own run.

    Under bulk the production lead is already overflow at five of eight cells, so
    the downward arms can only push piping further behind and the arm that can
    change an ordering is the upward one. That is the mirror image of the matrix
    reading, where the upward arm reverses nothing anywhere, and it is why a
    single cheap low-conductivity arm would have answered nothing here.
    """
    outcome = _bulk()["preregistration_outcome"]
    assert outcome["B1"]["held"] is True
    assert outcome["B4"]["held"] is True, (
        "B4 records that the matrix prediction P4 fails to replicate; if the "
        "upward arm stopped reversing anything under bulk, the offset finding "
        "would go with it"
    )
    upward = outcome["B1"]["cells_reversed_by_the_upward_arm"]
    downward = outcome["B1"]["cells_reversed_by_a_downward_arm"]
    assert len(upward) > len(downward)
    # And the matrix reading still says the opposite, which is the contrast.
    assert _evidence()["preregistration_outcome"]["P4"]["held"] is True


def test_the_two_brackets_offset_rather_than_compound() -> None:
    """The compound-or-overlap answer, pinned at the cells that carry it.

    The bulk grain-size reading hands the lead to overflow at five cells; the
    upward conductivity arm restores piping at four of them. A later change that
    left this list empty would turn an "offset" conclusion into a "compound" one
    without anyone editing the prose.
    """
    outcome = _bulk()["preregistration_outcome"]
    assert outcome["C1"]["held"] is True
    assert outcome["C2"]["held"] is True
    restored = {
        (c["section"], c["scenario"])
        for c in outcome["C1"]["cells_restored_to_piping_by_the_upward_arm"]
    }
    assert restored == {
        ("KP 57.4", "+4K"),
        ("KP 58.8", "historical"),
        ("KP 58.8", "+4K"),
        ("KP 62.0", "historical"),
    }


def test_no_cell_keeps_its_leading_mechanism_across_both_readings() -> None:
    """The RQ3 consequence: the claim rests on the union, and the union is empty.

    Six of eight cells are contested under both readings. The two that are not
    are each robust under exactly one reading and contested under the other, in
    opposite senses, so the intersection of the robust sets is empty. C4
    predicted the two zero-overflow cells would survive; they do not, because
    under bulk they collapse instead, so C4 scores as held only vacuously and
    the measured truth is stronger than the prediction.
    """
    matrix, bulk = _evidence()["sections"], _bulk()["sections"]
    robust_both = [
        (label, scenario)
        for label in SECTIONS
        for scenario in SCENARIOS
        if matrix[label][scenario]["ordering_verdict"] == "ROBUST"
        and bulk[label][scenario]["ordering_verdict"] == "ROBUST"
    ]
    assert robust_both == []
    assert _bulk()["preregistration_outcome"]["C4"]["invariant_cells"] == []
    # The one robust cell under each reading, and they are different cells.
    assert matrix["KP 60.0"]["historical"]["ordering_verdict"] == "ROBUST"
    assert bulk["KP 60.0"]["historical"]["ordering_verdict"] == "COLLAPSED"
    assert bulk["KP 62.0"]["+4K"]["ordering_verdict"] == "ROBUST"
    assert matrix["KP 62.0"]["+4K"]["ordering_verdict"] == "REVERSED"


def test_the_system_level_bracket_is_narrower_under_bulk_not_wider() -> None:
    """B9 failed, and its failure is the mechanism, so it is pinned.

    The prediction reasoned about the conditional piping curve; the recorded
    quantity is the system probability. Once the grain-size reading demotes
    piping below overflow, the system number is carried by surface curves with no
    aquifer dependence, and every conductivity statistic about the system
    collapses toward the overflow-only value. Upgrading B9 to "held" would delete
    the finding that the two brackets are sub-additive on the deliverable.
    """
    outcome = _bulk()["preregistration_outcome"]
    assert outcome["B9"]["held"] is False
    finite = [c for c in outcome["B9"]["cells"] if c["bulk_span"] is not None]
    assert len(finite) == 6
    for cell in finite:
        assert cell["wider_than_matrix"] is False, cell
        assert cell["bulk_span"] < cell["matrix_span"], cell
    # The second clause of B9 did survive: still wider than the length effect.
    assert outcome["B9"]["wider_than_length_effect_everywhere"] is True


def test_the_climate_ratio_converges_on_the_overflow_only_value() -> None:
    """B7's failure, same mechanism, at the cell where it is unambiguous.

    At KP 58.8 the downward arms lower the climate ratio instead of raising it,
    because they strip the small piping remainder and leave overflow's own ratio
    behind. That value is the overflow annual probabilities' own quotient, so the
    convergence is checked against the arithmetic rather than against a constant.
    """
    bulk = _bulk()
    ratios = bulk["sections"]["KP 58.8"]["climate_ratio_plus4k_over_historical"]
    overflow_only = (
        bulk["sections"]["KP 58.8"]["+4K"]["baseline"]["p_annual_overflow"]
        / bulk["sections"]["KP 58.8"]["historical"]["baseline"]["p_annual_overflow"]
    )
    for arm in ("k_aq_field_geomean", "k_aq_field_toe"):
        assert ratios[arm] < ratios["baseline"]
        assert abs(ratios[arm] / overflow_only - 1.0) < 0.01, arm
    assert any(
        not row["moved_as_predicted"]
        for row in bulk["preregistration_outcome"]["B7"]["cells"]
    )


def test_the_clamped_cells_are_named_under_both_readings() -> None:
    """A clamped piping number is a lower bound and may not be quoted as an estimate.

    Recorded under both readings because it fires under both: on the production
    baseline at two sections under bulk, and on low-conductivity arms even where
    the matrix baseline is a fitted lognormal, because such an arm drops its own
    maximum raw failure fraction below the bracketing threshold. The matrix half
    was not surfaced when that reading was first run.
    """
    for payload in (_evidence(), _bulk()):
        cells = payload["bep_clamped_cells"]
        assert cells, "a reading with clamped cells must name them"
        for cell in cells:
            assert cell["section"] in SECTIONS
            assert cell["scenario"] in SCENARIOS
            assert "LOWER BOUND" in cell["reading"]
    # Under bulk the production baseline itself is clamped; under matrix only arms.
    assert any(c["baseline_clamped"] for c in _bulk()["bep_clamped_cells"])
    assert not any(c["baseline_clamped"] for c in _evidence()["bep_clamped_cells"])


def test_the_attainable_stage_exposure_is_carried_for_the_bulk_reading() -> None:
    """Caveat 8 is four times larger under bulk, and that is not a coverage flag.

    At KP 62.0 under warming the ensemble years that peak above the attainable
    maximum carry 11.8 % of the annual piping probability under matrix and 81 %
    under bulk, while no coverage flag fires under either, because nothing leaves
    the conditioning grid. A number four fifths built on unreachable stages must
    not be read as an estimate of anything.
    """
    band = _bulk()["sections"]["KP 62.0"]["+4K"]["baseline"]["driving_stage_band"]
    assert band["attainable_max_m_msl"] == 50.5
    assert band["frac_of_annual_piping_above_attainable_max"] > 0.5
    # Historical, and KP 57.4 in both climates, are exactly zero under bulk too.
    assert (
        _bulk()["sections"]["KP 62.0"]["historical"]["baseline"]["driving_stage_band"][
            "frac_of_annual_piping_above_attainable_max"
        ]
        == 0.0
    )
    # And no coverage flag fires anywhere, which is why the flags alone are not
    # a sufficient statement about attainability.
    for label in SECTIONS:
        for scenario in SCENARIOS:
            entry = _bulk()["sections"][label][scenario]
            assert entry["baseline"]["coverage_system"]["lower_bound_clamp"] is False


def test_an_arm_cannot_be_compared_across_grain_size_readings() -> None:
    """Both readings share one arm directory and differ only in the file stem.

    A mistyped stem would silently compare a bulk arm against a matrix baseline,
    which no gate downstream would catch, so the guard reads the reading off the
    arm's own configuration rather than off its filename.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    tree = ast.parse(source)
    (provenance,) = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_arm_provenance"
    ]
    checks = [
        node
        for node in ast.walk(provenance)
        if isinstance(node, ast.Attribute) and node.attr == "d70_interpretation"
    ]
    assert checks, (
        "_arm_provenance no longer asserts the arm's own d70 interpretation; a "
        "bulk arm could be compared against a matrix baseline undetected"
    )


def test_the_bulk_figure_is_declared_by_exact_name_and_reads_both_records() -> None:
    """G7, and the reason this figure is a separate entry rather than a sibling.

    It is the cross-reading comparison, so staleness in EITHER committed record
    must redraw it. Folding it into the matrix entry as a second ``produces``
    would have bound it to only one of its two sources.
    """
    from production_campaign import FIGURE_DRIVERS

    (entry,) = [
        d
        for d in FIGURE_DRIVERS
        if d["produces"] == ["conductivity_bracket_both_d70.png"]
    ]
    assert entry["command"] is not None, "a real plot-only path exists; use it"
    assert entry["command"][-1] == "--figures-only"
    assert "--d70" in entry["command"] and "bulk" in entry["command"]
    assert set(entry["sources"]) == {
        "docs/decisions/conductivity-bracket-annualisation-bulk.json",
        "docs/decisions/conductivity-bracket-annualisation.json",
    }
    _require(BULK_FIGURE)


def test_no_figure_entry_claims_both_conductivity_figures() -> None:
    """A ``conductivity_*`` glob would bind the sibling to the wrong sources.

    The 2026-07-31 pass recorded exactly this trap for the shared prior-study
    glob, where one entry silently claimed three figures and measured them all
    against the newest.
    """
    from production_campaign import FIGURE_DRIVERS

    claims: list[str] = []
    for driver in FIGURE_DRIVERS:
        claims.extend(driver["produces"])
    for name in (
        "conductivity_bracket_annual.png",
        "conductivity_bracket_both_d70.png",
    ):
        assert claims.count(name) == 1, f"{name} is claimed {claims.count(name)} times"


def test_the_companion_driver_can_write_its_record_somewhere_else() -> None:
    """The missing flag the 2026-07-31 audit listed, now present.

    Without it the only way to exercise the prior-mean companion was to write the
    tracked ADR-0048 record, so a trial run could not be separated from a real
    one. The default is unchanged, so the no-argument call still merges into that
    record rather than truncating it.
    """
    companion = REPO / "scripts" / "prior_mean_scenario_companion.py"
    tree = ast.parse(_require(companion).read_text(encoding="utf-8"))
    flags = [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ]
    assert "--out" in flags
    # The record must still be written through the argument, not the constant.
    assert "JSON_OUT.write_text" not in companion.read_text(encoding="utf-8")


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
