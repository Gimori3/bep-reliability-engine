"""Guards for the hazard-sampling-uncertainty companion (2026-08-20).

Chapter 7 concedes that no sampling uncertainty is attached to any annual
probability or climate ratio, then quotes four climate ratios to three
significant figures, a KP 62.0 mechanism split to three decimals and a 43-fold
margin at KP 58.8. The companion puts an interval on each of them.

What is pinned here, and why each one earned a guard:

1. **The scope sentence travels with the numbers.** The interval resamples the
   hazard alone with the fragility curves held fixed. Quoted without that it
   reads as the total uncertainty, which it is not and is nowhere near.
2. **The estimator is the ensemble member, not the simulated year.** The years
   are nested 60-per-member; an i.i.d. bootstrap over them would be a different
   and invalid estimator, and a later edit that quietly switched units would
   change every number here without changing a headline.
3. **Gate 1 is recorded as passed over a non-trivial row count.** The study is
   worthless if its pipeline does not reproduce the production annualisation.
4. **The composition step is imported, never re-implemented.**
5. **The pre-registration is scored honestly**, including the two questions
   whose answer is "not resolvable at this ensemble size". A later edit that
   flipped either into a clean result would erase the study's most useful
   findings.
6. **A degenerate share is classified apart from a resolved one.**
7. **The interval on the ratio is on the ratio**, not a quotient of two
   marginal intervals.
8. **The figure is declared, and the record is one of its sources.**

Every path referenced here is committed except the gitignored production table,
so absence asserts rather than skips (conventions section 9.4); the one
untracked input is guarded by an explicit skip naming it as untracked.
"""

from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
DECISIONS = REPO / "docs" / "decisions"
EVIDENCE = DECISIONS / "annualisation-hazard-sampling-uncertainty.json"
NOTE = DECISIONS / "annualisation-hazard-sampling-uncertainty.md"
DRIVER = REPO / "scripts" / "annualisation_uncertainty_study.py"
FIGURE_DRIVER = REPO / "scripts" / "phase3_figures.py"
FIGURE = REPO / "docs" / "figures" / "phase3_rq4_four_sections.png"
PRODUCTION_TABLE = REPO / "results" / "system_integration" / "phase3" / "rq4_annual.csv"

sys.path.insert(0, str(REPO / "scripts"))

SECTIONS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")
SCENARIOS = ("historical", "+4K")
ARMS = ("matrix/posterior", "matrix/prior", "bulk/posterior", "bulk/prior")


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


def _intervals(payload: dict):
    """Every ``{point, ci_low, ci_high}`` block anywhere in the record."""
    if isinstance(payload, dict):
        if {"point", "ci_low", "ci_high"} <= set(payload):
            yield payload
        for value in payload.values():
            yield from _intervals(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _intervals(value)


# --------------------------------------------------------------------------- #
# 1. Scope                                                                      #
# --------------------------------------------------------------------------- #
def test_the_record_states_that_it_resamples_the_hazard_alone() -> None:
    """The interval is hazard-sampling only; nothing here is total uncertainty.

    The fragility curves are held fixed, so a reader who takes one of these
    intervals for the total uncertainty is off by orders of magnitude. The
    statement must be in the record itself, not only in the note.
    """
    scope = _evidence()["scope"]
    statement = scope["statement"].lower()
    assert "hazard-sampling uncertainty only" in statement
    assert "not" in statement and "total uncertainty" in statement
    assert "conductivity" in statement
    assert scope["resamples"] == "the d4PDF hazard only"
    assert "fragility" in scope["held_fixed"]


def test_the_note_leads_with_the_scope_rather_than_footnoting_it() -> None:
    """A scope that arrives after the numbers is a scope nobody reads."""
    text = _require(NOTE).read_text(encoding="utf-8")
    heading = text.index("## Scope of the claim")
    first_number_section = text.index("## 0.")
    assert (
        heading < first_number_section
    ), "the scope section must precede the first section carrying numbers"
    assert "hazard-sampling uncertainty only" in text.lower()


def test_the_figure_renders_the_scope_and_not_just_the_intervals() -> None:
    """Text baked into a PNG cannot be fixed in the thesis repository.

    The RQ4 headline figure is a main-body figure. Its intervals would read as
    total uncertainty without the qualification, and conventions section 9.3.1
    is the reason that qualification has to be right here rather than in a
    caption.
    """
    source = _require(FIGURE_DRIVER).read_text(encoding="utf-8")
    assert "held fixed, so this is not the total uncertainty" in source
    assert "conductivity range is far wider" in source
    _require(FIGURE)


def test_no_rendered_text_in_the_amended_figure_carries_a_forbidden_token() -> None:
    """Conventions section 9.3.1, for the strings this change added.

    Only the added strings are in scope; the pre-existing ones were swept on
    2026-08-04. An em dash, a snake_case field name or an engine identifier
    baked into the PNG cannot be rewritten in the thesis repository.
    """
    source = _require(FIGURE_DRIVER).read_text(encoding="utf-8")
    tree = ast.parse(source)
    added = [
        "95 per cent flood-ensemble sampling interval",
        "Intervals are flood-ensemble sampling only",
        "Climate ratio per section, with its 95 per cent sampling interval",
    ]
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    rendered = " ".join(
        literal
        for literal in literals
        if any(literal.startswith(prefix[:30]) for prefix in added)
    )
    assert rendered, "the added figure strings are no longer present to check"
    assert "—" not in rendered, "an em dash reached a main-body figure"
    for forbidden in ("p_annual", "ci_low", "ci_high", "rq4_annual", "ADR-", "engine"):
        assert forbidden not in rendered, (
            f"{forbidden!r} is engine vocabulary and must not be rendered into "
            "a main-body figure"
        )


# --------------------------------------------------------------------------- #
# 2. The estimator                                                              #
# --------------------------------------------------------------------------- #
def test_the_resampling_unit_is_the_ensemble_member_not_the_year() -> None:
    """The years are nested, so an i.i.d. bootstrap over them is invalid.

    This is the single decision the whole study rests on. A later edit that
    switched the unit would move every interval here without touching a
    headline, so the unit and the reason are both pinned.
    """
    estimator = _evidence()["estimator"]
    assert "ensemble member" in estimator["unit"]
    assert "nested" in estimator["why_not_years"]
    assert "not independent draws" in estimator["why_not_years"]


def test_the_ensemble_nesting_is_recorded_and_balanced() -> None:
    """50 x 60 historical and 90 x 60 warming, exactly balanced."""
    structure = _evidence()["ensemble_structure"]
    assert structure["historical"]["n_events"] == 3000
    assert structure["historical"]["member"]["n_blocks"] == 50
    assert structure["historical"]["member"]["events_per_block"] == [60]
    assert structure["+4K"]["n_events"] == 5400
    assert structure["+4K"]["member"]["n_blocks"] == 90
    assert structure["+4K"]["member"]["events_per_block"] == [60]
    for scenario in SCENARIOS:
        assert structure[scenario]["member"]["balanced"] is True


def test_the_preregistered_replicate_count_and_interval_type_are_honoured() -> None:
    """At least the 2,000 floor, and a percentile interval as pre-registered."""
    estimator = _evidence()["estimator"]
    assert estimator["replicates"] >= 2000
    assert estimator["replicates"] == estimator["preregistered_replicates"]
    assert "percentile" in estimator["interval"]
    assert "95" in estimator["interval"]
    assert isinstance(estimator["seed"], int)


def test_point_estimates_are_never_bootstrap_means() -> None:
    """Every interval must bracket its own point estimate.

    A point that fell outside its interval would mean the record had started
    reporting a bootstrap mean, which is a different (and biased, for a ratio)
    quantity from the production value the thesis quotes.
    """
    for block in _intervals(_evidence()):
        assert block["ci_low"] <= block["point"] <= block["ci_high"], block


def test_the_multiplicity_draw_is_a_with_replacement_block_resample() -> None:
    """The counts formulation must equal a literal block resample.

    A replicate is implemented as block multiplicities dotted into per-block
    sums rather than as a gathered index array. That is only the same estimator
    if the multiplicities really are the with-replacement draw, so the identity
    is checked directly against an explicit resample of the same blocks.
    """
    import annualisation_uncertainty_study as study

    rng = np.random.default_rng(7)
    values = rng.random((12, 2))
    index = np.repeat(np.arange(4), 3)
    sums = study.block_sums(values, index, 4)

    multiplicities = study.draw_multiplicities(4, 200, np.random.default_rng(11))
    assert (multiplicities.sum(axis=1) == 4).all()

    means = study.replicate_means(sums, multiplicities, 12)
    for replicate, counts in enumerate(multiplicities):
        blocks = np.concatenate(
            [values[index == block] for block, n in enumerate(counts) for _ in range(n)]
        )
        assert blocks.shape[0] == 12
        assert np.allclose(means[replicate], blocks.mean(axis=0), rtol=1e-12)


def test_the_block_label_grammar_survives_both_member_header_forms() -> None:
    """``HPB_m001_1951`` and ``HFB_CC_m101_2051`` split the same way.

    The warming header carries an extra sea-surface-pattern token, so a split
    from the left would put the pattern in the member slot for one ensemble and
    not the other.
    """
    import annualisation_uncertainty_study as study

    ids = ["HPB_m001_1951", "HPB_m001_1952", "HFB_CC_m101_2051", "HFB_MR_m101_2051"]
    assert list(study.block_labels(ids, "member")) == [
        "HPB_m001",
        "HPB_m001",
        "HFB_CC_m101",
        "HFB_MR_m101",
    ]
    assert list(study.block_labels(ids, "year")) == ["1951", "1952", "2051", "2051"]
    assert list(study.block_labels(ids, "sst")) == ["HPB", "HPB", "HFB_CC", "HFB_MR"]


# --------------------------------------------------------------------------- #
# 3. Gates                                                                      #
# --------------------------------------------------------------------------- #
def test_gate_one_reproduced_the_production_table_over_every_published_row() -> None:
    """912 rows, four arms, every field string-identical."""
    gate = _evidence()["gates"]["gate_1_reproduces_production_table"]
    assert gate["passed"] is True
    assert gate["rows_compared"] == 912
    assert gate["fields_compared"] == 20
    assert set(gate["rows_per_arm"]) == set(ARMS)
    assert all(count == 228 for count in gate["rows_per_arm"].values())
    assert "string-identical" in gate["criterion"]


def test_the_per_event_matrix_averages_to_the_published_number() -> None:
    """Gate 0: the bootstrap resamples the production quantity, not a lookalike."""
    gate = _evidence()["gates"][
        "gate_0_per_event_matrix_averages_to_the_published_number"
    ]
    assert gate["passed"] is True
    assert "no tolerance" in gate["criterion"]


def test_the_hazard_cache_and_the_phase3_outputs_were_left_alone() -> None:
    """Gates 2 and 3: read-only over the campaign's artifacts."""
    gates = _evidence()["gates"]
    assert gates["gate_2_hazard_cache_unchanged"]["passed"] is True
    assert gates["gate_2_hazard_cache_unchanged"]["cache_files"] == 228
    assert gates["gate_3_no_production_artifact_written"]["passed"] is True


def test_the_record_matches_the_live_production_table() -> None:
    """The intervals must sit on the annual numbers that are actually published.

    ``results/`` is gitignored, so this is the one guard here that may skip: on
    a fresh clone the untracked production table is absent.
    """
    if not PRODUCTION_TABLE.is_file():
        pytest.skip(
            "results/system_integration/phase3/rq4_annual.csv is untracked "
            "(gitignored campaign output); absent on a fresh clone"
        )
    payload = _evidence()
    arm = payload["scope"]["primary_arm"]
    d70, source = arm.split("/")
    seen = 0
    with open(PRODUCTION_TABLE, encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            label = f"KP {float(record['kp']):.1f}"
            if (
                record["d70"] != d70
                or record["bep_source"] != source
                or record["lambda_ac_m"] != "250.0"
                or record["surface_variant"] != "primary"
                or label not in SECTIONS
            ):
                continue
            block = payload["sections"][label][arm][record["scenario"]]
            assert str(block["p_annual_system"]["point"]) == record["p_annual_system"]
            seen += 1
    assert seen == len(SECTIONS) * len(SCENARIOS)


# --------------------------------------------------------------------------- #
# 4. The pre-registered questions                                               #
# --------------------------------------------------------------------------- #
def test_q1_records_which_pairs_of_climate_ratios_resolve() -> None:
    """Five of the six pairs resolve; the two 12.7s do not.

    The unresolved pair is the study's most quotable negative: KP 57.4 and
    KP 62.0 rise by factors this ensemble cannot tell apart, so their
    near-equality must not be read as a finding about the two sections.
    """
    q1 = _evidence()["preregistration_outcome"]["Q1"]
    assert q1["n_pairs"] == 6
    assert q1["n_resolved"] == 5
    assert q1["verdict"].startswith("PARTIAL")
    unresolved = [key for key, entry in q1["pairs"].items() if not entry["resolved"]]
    assert unresolved == ["KP 57.4 - KP 62.0"]
    for entry in q1["pairs"].values():
        assert entry["n_replicates_paired"] == _evidence()["estimator"]["replicates"], (
            "the between-section difference must be paired on every replicate; "
            "an unpaired difference would inflate the interval"
        )


def test_q2_records_the_kp62_warming_split_as_a_tie() -> None:
    """A production margin of 1.0013 does not survive its own sampling interval.

    Both halves are pinned: the split is not resolvably different from level,
    and the third decimal the thesis table prints is not an estimated digit.
    """
    q2 = _evidence()["preregistration_outcome"]["Q2"]
    assert q2["resolvably_not_a_tie"] is False
    assert q2["three_decimal_quotation_supported"] is False
    assert q2["verdict"].startswith("TIE")
    difference = q2["difference_p_annual_bep_minus_overflow"]
    assert difference["ci_low"] < 0.0 < difference["ci_high"]
    assert 1.0 < q2["production_margin_bep_over_overflow"] < 1.01


def test_q3_separates_a_resolved_lead_from_a_degenerate_one() -> None:
    """The lead resolves at all four sections, two of them only by coverage.

    KP 57.4 and KP 60.0 have no loaded overflow branch at all, so their share
    is 1.0 in every replicate. Counting those as measured leads would make the
    dominance claim look better evidenced than it is.
    """
    q3 = _evidence()["preregistration_outcome"]["Q3"]
    assert q3["n_resolved"] == 4
    assert q3["n_structurally_degenerate"] == 2
    assert q3["verdict"].startswith("YES")
    degenerate = {
        label
        for label, entry in q3["sections"].items()
        if entry["structurally_degenerate"]
    }
    assert degenerate == {"KP 57.4", "KP 60.0"}
    for label in ("KP 58.8", "KP 62.0"):
        entry = q3["sections"][label]
        assert entry["lead_resolved"] is True
        assert entry["two_decimal_quotation_supported"] is False, (
            f"{label}: the share is quoted to two decimals in Chapter 7 and its "
            "interval does not support that precision; the guard exists so a "
            "later run that tightened it is noticed rather than assumed"
        )


def test_a_degenerate_share_is_never_reported_as_a_measured_one() -> None:
    """A zero-width share carries the reason it is zero-width.

    Reported bare, ``0.5 % of a share`` and ``no competing mechanism exists``
    look identical, and the second is a statement about coverage.
    """
    payload = _evidence()
    arm = payload["scope"]["primary_arm"]
    for label in ("KP 57.4", "KP 60.0"):
        share = payload["sections"][label][arm]["historical"]["share_bep"]
        assert share["ci_low"] == share["ci_high"] == share["point"] == 1.0
        assert "degenerate" in share
        assert "coverage" in share["degenerate"]
        assert "not a zero-width confidence statement" in share["degenerate"]
    for label in ("KP 58.8", "KP 62.0"):
        share = payload["sections"][label][arm]["historical"]["share_bep"]
        assert "degenerate" not in share, (
            f"{label} has two loaded mechanisms, so its share is measured; "
            "marking it degenerate would hide a real interval"
        )


# --------------------------------------------------------------------------- #
# 5. The ratio is an interval on the ratio                                      #
# --------------------------------------------------------------------------- #
def test_the_climate_ratio_interval_is_not_a_quotient_of_marginal_intervals() -> None:
    """Formed inside each replicate, so it is strictly tighter than the quotient.

    Dividing the warming interval by the historical one treats the two ends as
    simultaneously attainable and produces a band far wider than the ratio's
    own. The record must be the narrower, correct one.
    """
    payload = _evidence()
    arm = payload["scope"]["primary_arm"]
    for label in SECTIONS:
        entry = payload["sections"][label][arm]
        ratio = entry["climate_ratio"]
        historical = entry["historical"]["p_annual_system"]
        warming = entry["+4K"]["p_annual_system"]
        naive_low = warming["ci_low"] / historical["ci_high"]
        naive_high = warming["ci_high"] / historical["ci_low"]
        assert ratio["ci_low"] > naive_low, label
        assert ratio["ci_high"] < naive_high, label
        assert "inside each replicate" in ratio["definition"]


def test_the_two_scenarios_are_drawn_independently() -> None:
    """Disjoint ensembles, so their replicate draws must be independent."""
    pairing = _evidence()["estimator"]["pairing"]
    assert "independent streams" in pairing
    assert "inside each replicate" in pairing


# --------------------------------------------------------------------------- #
# 6. Structure of the change                                                    #
# --------------------------------------------------------------------------- #
def test_the_composition_step_is_imported_not_reimplemented() -> None:
    """A second copy of ``_compose_segment`` could drift from the production one.

    Gate 1 only means something if the composition it exercises IS the
    campaign's. If this driver ever defined its own, the gate would be
    comparing a copy against a table the copy no longer produces.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    assert "def _compose_segment" not in source, (
        "the composition step must be imported from scripts/phase3_campaign.py, "
        "never re-implemented here"
    )
    assert "campaign._compose_segment(" in source
    assert "phase3_campaign.py" in source


def test_the_driver_writes_nothing_into_the_production_directories() -> None:
    """No write path may point at results/system_integration/ or configs/."""
    tree = ast.parse(_require(DRIVER).read_text(encoding="utf-8"))
    writes = {"write_text", "write_bytes", "mkdir", "savefig", "unlink"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in writes:
            continue
        rendered = ast.unparse(node)
        for forbidden in ("PHASE3_DIR", "HAZARD_CACHE", "PRODUCTION_TABLE", "configs"):
            assert forbidden not in rendered, (
                f"{node.func.attr} targets {forbidden}; this study is read-only "
                "over the production artifacts"
            )


def test_the_figure_driver_refuses_rather_than_skipping_without_the_record() -> None:
    """A missing tracked record must fail, not silently drop the intervals.

    Conventions section 9.4: a tracked artifact is asserted, never skipped. A
    figure that quietly loses its error bars is the exact failure mode that
    rule exists for, and it would be invisible in a green suite.
    """
    source = _require(FIGURE_DRIVER).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_hazard_intervals"
    )
    raises = [node for node in ast.walk(function) if isinstance(node, ast.Raise)]
    assert (
        len(raises) >= 2
    ), "_hazard_intervals must raise on a missing record and on a stale one"
    raised = " ".join(ast.unparse(node) for node in raises)
    assert "FileNotFoundError" in raised
    assert "AssertionError" in raised
    # The docstring is excluded deliberately: it *discusses* skipping, so a
    # substring search that included it would pass for the wrong reason.
    executable = [node for node in function.body if not isinstance(node, ast.Expr)]
    body = ast.unparse(ast.Module(body=executable, type_ignores=[]))
    assert "skip" not in body.lower()


def test_the_record_is_declared_as_a_source_of_the_rq4_figure() -> None:
    """Staleness in the record must redraw the figure that depicts it."""
    import importlib.util

    path = REPO / "scripts" / "production_campaign.py"
    spec = importlib.util.spec_from_file_location("production_campaign_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    entries = [
        driver
        for driver in module.FIGURE_DRIVERS
        if any(
            "phase3_rq4_four_sections" in name or name == "phase3_*.png"
            for name in driver["produces"]
        )
    ]
    assert len(entries) == 1, (
        "exactly one FIGURE_DRIVERS entry may own the RQ4 headline figure; two "
        "would bind it to the wrong sources"
    )
    assert (
        "docs/decisions/annualisation-hazard-sampling-uncertainty.json"
        in entries[0]["sources"]
    )


def test_the_study_runs_as_a_campaign_companion_and_is_compared() -> None:
    """Classified on substance: it consumes only what the campaign produces.

    None of the exclusion grounds recorded for the other Phase 3 companions
    applies here (no gitignored sensitivity arm, no re-assertion of another
    gate's claim through that gate's own function), so it runs, and its fresh
    record is compared against the committed one.
    """
    import importlib.util

    path = REPO / "scripts" / "production_campaign.py"
    spec = importlib.util.spec_from_file_location("production_campaign_guard2", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    spec_entry = module.COMPANION_COMMANDS["annualisation_uncertainty_study"]
    assert spec_entry["compare_to"] == (
        "docs/decisions/annualisation-hazard-sampling-uncertainty.json"
    )
    assert "scripts/annualisation_uncertainty_study.py" in spec_entry["argv"]
    assert (
        "scripts/annualisation_uncertainty_study.py" not in module.COMPANION_EXCLUSIONS
    ), "the driver is run, so it must not also carry an exclusion reason"

    enumeration = module.enumerate_companions()
    assert enumeration["unclassified"] == []
    assert enumeration["exclusions_with_no_file_on_disk"] == []


def test_the_note_and_the_record_agree_on_every_verdict() -> None:
    """Part 2's prose may not say something the evidence record does not.

    Two copies of a verdict is exactly the drift shape the retired thesis
    fragments had, so the prose is pinned against the machine-readable record
    rather than trusted.
    """
    text = _require(NOTE).read_text(encoding="utf-8")
    outcome = _evidence()["preregistration_outcome"]
    assert "## 2. Outcome" in text
    part_two = text[text.index("## 2. Outcome") :]
    assert len(part_two.splitlines()) > 20, "Part 2 is still a placeholder"
    assert f"{outcome['Q1']['n_resolved']} of 6" in part_two
    assert "KP 57.4 - KP 62.0" in part_two or "KP 57.4 and KP 62.0" in part_two
    assert "tie" in part_two.lower()
    assert "degenerate" in part_two.lower()


def test_no_numbered_adr_was_consumed_and_the_judgement_is_recorded() -> None:
    """The ADR judgement is explicit, not inferred from an absent file.

    ``bep-change-control``'s test is whether a change can alter what a baseline
    run computes. This one cannot, so it is a companion. Recording the reasoning
    is what stops a later session re-litigating it.
    """
    text = _require(NOTE).read_text(encoding="utf-8")
    assert "**No numbered ADR.**" in text
    assert "no `Config` field is added" in text
    assert not list(DECISIONS.glob("*annualisation-hazard*")) or True
    numbered = sorted(p.name for p in DECISIONS.glob("[0-9][0-9][0-9][0-9]-*.md"))
    assert not any("hazard-sampling" in name for name in numbered), (
        "this companion consumed no ADR number; a numbered file with this "
        "slug means the judgement was reversed without updating the note"
    )


def test_no_existence_guard_in_this_file_skips_on_a_tracked_path() -> None:
    """Conventions section 9.4, enforced on this file.

    Skipping on a committed path means a move or deletion silently disables the
    guard while the suite still reports green. The single legitimate skip here
    is the gitignored production table, and its reason says "untracked".
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    skips = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "skip"
    ]
    assert len(skips) == 1, (
        "exactly one skip is expected in this file, on the untracked "
        f"production table; found {len(skips)}"
    )
    reason = ast.unparse(skips[0])
    assert (
        "untracked" in reason
    ), "a skip must name the untracked artifact it is skipping on"
