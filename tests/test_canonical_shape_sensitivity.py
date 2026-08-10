"""Guards for the canonical-shape sensitivity study (defence brief item A1).

The study measures what the one pinned d4PDF member is worth by swapping it in
memory and re-running Phase 1, the comparator ladder, the peak-only shortcut and
the Phase 3 composition. These guards cover the three things that could quietly
go wrong afterwards: the pre-registration drifting away from the numbers it was
supposed to predate, an invariance the companion note proves being reported as a
finding rather than asserted as a gate, and the arm route acquiring a way to
write a committed config.

Every path referenced here is tracked, so nothing skips: absence must fail.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
NOTE = REPO / "docs" / "decisions" / "canonical-shape-sensitivity.md"
EVIDENCE = REPO / "docs" / "decisions" / "canonical-shape-sensitivity.json"
DRIVER = REPO / "scripts" / "canonical_shape_sensitivity_study.py"
FIGURE = REPO / "docs" / "figures" / "canonical_shape_sensitivity.png"
CONFIGS = REPO / "configs"

#: The production member and the approved alternate, in committed order.
PRODUCTION_EVENT = "HPB_m064_1987"
ALTERNATE_EVENT = "HPB_m067_1978"


def _require(path: Path, what: str) -> Path:
    """Assert a tracked artifact is present. Never skip on one."""
    assert path.is_file(), (
        f"missing {path.relative_to(REPO).as_posix()}, which holds {what}. "
        "This path is tracked, so absence is a defect and not a fresh clone."
    )
    return path


def _load_driver():
    spec = importlib.util.spec_from_file_location("canonical_shape_study", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _evidence() -> dict[str, Any]:
    return json.loads(
        _require(EVIDENCE, "the study's measured record").read_text(encoding="utf-8")
    )


# --------------------------------------------------------------------------- #
# The pre-registration                                                          #
# --------------------------------------------------------------------------- #
def test_part_one_states_its_predictions_and_its_falsifiers() -> None:
    """A pre-registration that can be read as a summary is not one.

    The whole value of Part 1 is that it commits to a direction that the
    measurement can refute, so the direction word, the falsifiers and the
    "written before any number" claim all have to be present in the file that
    Part 2 is appended to.
    """
    text = _require(NOTE, "the study's pre-registration").read_text(encoding="utf-8")
    assert "## Part 1: pre-registration" in text
    for marker in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
        assert (
            f"**Prediction {marker}" in text or f"* **{marker}.**" in text
        ), f"prediction {marker} is missing from Part 1"
    for marker in ("F1", "F2", "F3", "F4", "F5"):
        assert f"**{marker}.**" in text, f"falsifier {marker} is missing from Part 1"
    assert "before any number existed" in text
    for gate in ("Gate 1", "Gate 2", "Gate 3", "Gate 4"):
        assert f"**{gate}.**" in text, f"{gate} is not declared in Part 1"


def test_the_record_pins_the_preregistration_it_was_measured_against() -> None:
    """The record carries a digest of Part 1 as it stood when it was measured.

    Without this, Part 1 could be edited after the fact to agree with Part 2 and
    nothing would notice. The digest does not prevent an edit; it makes an edit
    visible, which is the most a single repository can offer.

    It covers Part 1 alone. Hashing the whole note would go stale the moment the
    outcome was appended to the same file, i.e. exactly when the pin starts to
    matter, and a pin that always fails is a pin nobody reads.
    """
    record = _evidence()
    assert record["preregistration"] == "docs/decisions/canonical-shape-sensitivity.md"
    module = _load_driver()
    assert record["preregistration_part1_sha256"] == module.preregistration_digest(), (
        "Part 1 has changed since the evidence record was last written. Re-run "
        "the study, or record why the pre-registration was amended."
    )
    text = NOTE.read_text(encoding="utf-8")
    assert module.PART_TWO_MARKER in text, (
        "the digest is defined as everything before the Part 2 heading; without "
        "that heading it would silently cover the whole note"
    )


def test_part_two_reports_the_outcome_of_every_prediction() -> None:
    """Part 2 must dispose of each prediction, including the ones that failed.

    A pre-registered study that quietly drops a refuted prediction is worse than
    one that never pre-registered, because it looks disciplined.
    """
    text = NOTE.read_text(encoding="utf-8")
    assert "## Part 2" in text, "Part 2 has not been written yet"
    verdicts = text.split("## Part 2", 1)[1]
    for marker in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
        assert marker in verdicts, f"Part 2 does not dispose of {marker}"
    assert "REFUTED" in verdicts or "CONFIRMED" in verdicts


# --------------------------------------------------------------------------- #
# The invariances are gates, not findings                                       #
# --------------------------------------------------------------------------- #
def test_every_stratum_passed_both_phase_one_gates() -> None:
    """Gate 1 and gate 2, asserted from the record rather than described.

    Gate 2 is the load-bearing one: the static comparator consumes the scalar
    conditioning level verbatim and never reads the loading record, so a static
    probability that moved with the member would mean the harness, not the
    physics, produced the answer.
    """
    strata = _evidence()["phase1"]["strata"]
    assert len(strata) == 8, f"expected all eight strata, found {sorted(strata)}"
    for stem, record in strata.items():
        assert record["gate_1_baseline_bit_identical"] is True, stem
        assert record["gate_2_static_exactly_invariant"] is True, stem


def test_the_design_level_bias_at_the_drained_sections_is_recomputable() -> None:
    """The published bias reproduces, and the alternate value follows from it.

    The static branch is invariant by gate 2, so the ratio at any level follows
    from the record with no further computation. The two drained sections are
    the only ones where the design level sits near mid-curve, so they are the
    only ones where both arms carry enough failing rows for the ratio to be a
    measurement rather than a count of a handful.
    """
    strata = _evidence()["phase1"]["strata"]
    expected = {
        "tokachi_kp58.8_historical_matrix": (2.75, 4.87),
        "tokachi_kp60.0_historical_matrix": (2.92, 6.03),
    }
    for stem, (published, alternate) in expected.items():
        record = strata[stem]
        i = record["levels_m_msl"].index(
            min(
                record["levels_m_msl"],
                key=lambda level: abs(level - record["hwl_m_msl"]),
            )
        )
        static = record["p_f_static"][i]
        production = record["p_f_trans_production"][i]
        arm = record["p_f_trans_alternate"][i]
        n = record["n_samples"]
        assert round(production * n) >= 1000 and round(arm * n) >= 1000, (
            f"{stem}: the design-level ratio rests on too few failing rows to "
            "be quoted as a measurement"
        )
        assert round(static / production, 2) == published, stem
        assert round(static / arm, 2) == alternate, stem
        assert static / arm > static / production, (
            f"{stem}: the bias must rise under the shorter loading, since the "
            "numerator is invariant and the denominator falls"
        )


def test_the_peak_referenced_comparators_are_asserted_invariant() -> None:
    """Gate 3 covers the four statics, both sustained limits and the lattice."""
    module = _load_driver()
    assert set(module.INVARIANT_COMPARATORS) == {
        "C0",
        "C0b",
        "C1",
        "C2",
        "C3a",
        "C3b",
    }
    assert set(module.CONDITIONAL_COMPARATORS) == {"C4a", "C4b", "C4c", "C4d"}
    assert not set(module.INVARIANT_COMPARATORS) & set(
        module.CONDITIONAL_COMPARATORS
    ), "a comparator cannot be both peak-referenced and hydrograph-driven"

    ladder = _evidence()["ladder"]["sections"]
    assert ladder, "the ladder stage has not been run"
    for key, section in ladder.items():
        for name in module.INVARIANT_COMPARATORS:
            assert section["gate_3"][name] is True, f"{key}: {name} moved"
        assert section["gate_3"]["static_shapley_lattice"] is True, key


def test_the_head_convention_component_is_invariant_while_its_share_is_not() -> None:
    """The distinction the companion invariance note exists to draw.

    The component is a difference of two peak-referenced statics and cannot
    move. Its share divides by a total that ends at a transient comparator, so
    the share can and does move. Reporting them as one quantity is the specific
    error this study must not repeat.
    """
    ladder = _evidence()["ladder"]["sections"]
    for key, section in ladder.items():
        for ladder_name, steps in section["components"].items():
            head = steps["steps"]["head_convention"]
            assert head["component_exactly_invariant"] is True, (
                f"{key}/{ladder_name}: the head-convention component moved, which "
                "is impossible for a difference of two peak-referenced statics"
            )
            gate = steps["steps"].get("initiation_gate")
            if gate is not None:
                assert (
                    gate["component_exactly_invariant"] is True
                ), f"{key}/{ladder_name}: the initiation-gate component moved"


def test_the_replay_denominator_is_recorded_as_shape_invariant() -> None:
    """Phase 2 was not re-run, and the record says why in machine-readable form.

    The replay drives the observed 2016 record, so the denominator of the
    peak-only factor cannot move. Only the numerator is exposed.
    """
    peak = _evidence()["peak_shortcut"]
    published = json.loads(
        _require(
            REPO / "docs" / "decisions" / "phase2-peak-shortcut.json",
            "the published peak-only comparison",
        ).read_text(encoding="utf-8")
    )
    by_stem = {s["stratum"]: s for s in published["strata"]}
    for stratum in peak["strata"]:
        assert stratum["f_replay_is_shape_invariant"] is True
        assert (
            stratum["f_replay_transient"]
            == by_stem[stratum["stratum"]]["f_replay_transient"]
        ), (
            f"{stratum['stratum']}: the replay rejection fraction differs from "
            "the committed slice; the denominator must be carried over, not "
            "recomputed under a shape arm"
        )


def test_the_three_peak_only_cases_stay_apart() -> None:
    """Not defined, small-number and headline are three states, never one.

    Four strata reject nothing under either reading, so no multiplier exists
    there: that is ``None``, never 1.0 and never "agreement". Two more reject
    fewer rows than the published small-number threshold and stay in the record
    but out of the headline band.
    """
    peak = _evidence()["peak_shortcut"]
    strata = peak["strata"]
    not_defined = [s for s in strata if s["factor_alternate"] is None]
    assert not_defined, "the not-defined case has vanished from the record"
    for stratum in not_defined:
        assert stratum["f_replay_transient"] == 0.0
    headline = set(peak["headline"]["informative_strata"])
    for stratum in strata:
        if stratum["small_number_regime"]:
            assert stratum["stratum"] not in headline, (
                f"{stratum['stratum']} is in the small-number regime and must "
                "not carry the headline band"
            )


# --------------------------------------------------------------------------- #
# The arm route                                                                 #
# --------------------------------------------------------------------------- #
def test_the_arm_swap_never_writes_a_committed_config() -> None:
    """The in-memory route, exercised and then checked byte for byte.

    Reordering a committed config is forbidden three ways -- the field is inside
    the config hash, the orchestrator hard-codes entry zero, and the drift guard
    pins the committed order -- so the arm must swap in memory only.
    """
    module = _load_driver()
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in CONFIGS.glob("*.yaml")
    }
    assert before, "no committed configs found"

    path = CONFIGS / "kp58_8_historical_matrix.yaml"
    config = module._config_with_event(path, ALTERNATE_EVENT)
    assert config.hydrograph_source is not None
    ordered = list(config.hydrograph_source.canonical_event_ids)
    assert ordered[0] == ALTERNATE_EVENT, "the arm does not select the alternate"
    assert PRODUCTION_EVENT in ordered, (
        "the production member must stay recorded behind the arm's selection, "
        "exactly as the committed provenance list records its own alternate"
    )

    baseline = module._config_with_event(path, PRODUCTION_EVENT)
    assert list(baseline.hydrograph_source.canonical_event_ids) == [
        PRODUCTION_EVENT,
        ALTERNATE_EVENT,
    ], "the baseline arm must reproduce the committed order exactly"
    assert baseline.config_hash() != config.config_hash(), (
        "the two arms must be distinguishable by config hash, or a shape arm "
        "could replay as the baseline"
    )

    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in CONFIGS.glob("*.yaml")
    }
    assert after == before, "the arm route wrote to a committed config"


def test_the_arm_refuses_a_config_whose_member_list_is_not_the_committed_pair() -> None:
    """Guessing which member is the alternate is worse than refusing."""
    import pytest
    import yaml

    module = _load_driver()
    path = CONFIGS / "kp58_8_historical_matrix.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["hydrograph_source"]["canonical_event_ids"] = ["HPB_m064_1987"]
    scratch = REPO / "results" / "canonical_shape" / "_test_config.yaml"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    scratch.write_text(yaml.safe_dump(data), encoding="utf-8")
    try:
        with pytest.raises(AssertionError, match="canonical_event_ids"):
            module._config_with_event(scratch, ALTERNATE_EVENT)
    finally:
        scratch.unlink()


def test_the_committed_provenance_no_longer_carries_the_unreproducible_rise() -> None:
    """The alternate's recorded rise was wrong and misled two documents.

    Measured with the same function that gives the production member its 23 h
    rising limb, the alternate rises in 16 h; no onset threshold from 2 to 50
    per cent of amplitude yields 32 h in either the discharge or the stage
    domain. The correction has to live where the next reader will meet it.
    """
    source = _require(
        REPO / "scripts" / "generate_configs.py", "the canonical member provenance"
    ).read_text(encoding="utf-8")
    block = source.split("CANONICAL_EVENT_IDS")[0]
    assert (
        "32 h rise)" not in block
    ), "the unreproducible 32 h rise is being asserted again as a fact"
    assert "does not reproduce" in block


# --------------------------------------------------------------------------- #
# Figure and campaign wiring                                                    #
# --------------------------------------------------------------------------- #
def test_the_redraw_path_writes_no_evidence_file() -> None:
    """A figure command that can rewrite the evidence is not a redraw path.

    Parsed rather than grepped: the module's prose names both functions, so a
    textual check would match its own explanation.
    """
    tree = ast.parse(DRIVER.read_text(encoding="utf-8"))
    render = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "render_figure"
    )
    called = {
        node.func.id
        for node in ast.walk(render)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_merge_evidence" not in called, (
        "render_figure writes the evidence record; the redraw path must be "
        "read-only so gate G7 can re-render without producing new evidence"
    )


def test_the_figure_is_declared_with_an_exact_filename() -> None:
    """Gate G7 wiring, including the glob trap the 2026-07-31 pass recorded."""
    spec = importlib.util.spec_from_file_location(
        "production_campaign", REPO / "scripts" / "production_campaign.py"
    )
    assert spec is not None and spec.loader is not None
    campaign = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = campaign
    spec.loader.exec_module(campaign)

    entries = [
        d
        for d in campaign.FIGURE_DRIVERS
        if "canonical_shape_sensitivity.png" in d["produces"]
    ]
    assert len(entries) == 1, "the figure must be declared exactly once"
    entry = entries[0]
    assert entry["produces"] == ["canonical_shape_sensitivity.png"], (
        "declare the exact filename, never a glob: a canonical_* glob would "
        "claim a future sibling and bind it to the wrong driver's sources"
    )
    assert entry["command"] is not None, "a real redraw path exists, so use it"
    assert entry["sources"] == ["docs/decisions/canonical-shape-sensitivity.json"]
    assert entry["requires"] == ["docs/decisions/canonical-shape-sensitivity.json"]
    _require(FIGURE, "the study's publication figure")


def test_the_study_is_classified_in_the_companion_enumeration() -> None:
    """G6: a consumer that neither runs nor carries a reason fails the campaign."""
    spec = importlib.util.spec_from_file_location(
        "production_campaign_g6", REPO / "scripts" / "production_campaign.py"
    )
    assert spec is not None and spec.loader is not None
    campaign = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = campaign
    spec.loader.exec_module(campaign)

    enumeration = campaign.enumerate_companions()
    assert enumeration["unclassified"] == [], enumeration["unclassified"]
    assert enumeration["exclusions_with_no_file_on_disk"] == []
    driver_rel = "scripts/canonical_shape_sensitivity_study.py"
    assert driver_rel in enumeration["hits"], (
        "the study asserts bit-identity against persisted sweeps and must be "
        "detected; if it stopped matching, the enumeration lost coverage"
    )
    reason = enumeration["found_but_not_run_here"][driver_rel]
    assert "UNCLASSIFIED" not in reason
    assert "NOT a cost exclusion" in reason, (
        "the exclusion must state what substantively excludes it, since a cheap "
        "verification mode question was answered first"
    )


# --------------------------------------------------------------------------- #
# Presentation discipline                                                       #
# --------------------------------------------------------------------------- #
def test_rendered_arm_names_carry_no_member_header() -> None:
    """A main-body figure prints no run or member identifier.

    The record keys stay the verbatim d4PDF headers, which are load-bearing
    provenance; the substitution happens at render time through a display map.
    """
    module = _load_driver()
    assert set(module.ARM_DISPLAY_NAMES) == {PRODUCTION_EVENT, ALTERNATE_EVENT}
    for shown in module.ARM_DISPLAY_NAMES.values():
        assert "HPB" not in shown
        assert "—" not in shown, "no em dash in rendered text"


def test_the_anchors_never_use_the_bare_word_shoulder() -> None:
    """One project, two "shoulders" two orders of magnitude apart in probability.

    The epistemic-bracket synthesis had to name both explicitly after the word
    was found meaning the rising limb in one record and the transition midpoint
    in another. The anchors here carry their definitions instead.
    """
    module = _load_driver()
    record = _evidence()
    names: set[str] = set()
    for stratum in record["phase1"]["strata"].values():
        names |= set(stratum["anchors"])
    assert "transition_midpoint" in names
    assert not any("shoulder" in name for name in names)
    assert "shoulder" not in module.__doc__.lower()


def test_no_existence_skip_in_this_file_gates_on_a_tracked_path() -> None:
    """The silent-skip class must not reappear here.

    Every artifact this file reads is tracked, so absence is a defect and must
    fail. Parsed rather than grepped, for the same self-matching reason its
    siblings are: the docstrings above name both forms deliberately.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))

    def _dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return f"{_dotted(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        return ""

    offenders = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _dotted(node.func) in {"pytest.skip", "pytest.mark.skipif"}
    ]
    assert not offenders, (
        "an existence-conditional skip appeared in a file whose every path is "
        "tracked; use _require so absence fails loudly"
    )
