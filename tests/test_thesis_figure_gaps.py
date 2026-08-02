"""Guards for the thesis-inventory figures and their committed evidence.

``docs/thesis_number_inventory_2026-07-30.md`` closed with eighteen numbers that
had no figure and named the five worth building first; row 4.7, the WBI+
peak-only shortcut, was added on 2026-08-02 as the sixth. ``scripts/
thesis_figure_gaps.py`` builds them. What is pinned here is what would otherwise
rot silently:

1. **The dual-write and the declaration.** Every figure is written to tracked
   ``docs/figures/`` by its own driver and is declared in gate G7's
   ``FIGURE_DRIVERS`` by exact name, with every declared path resolving. The
   2026-07-30 pass established that a ``requires``/``sources`` entry which
   matches nothing turns a real gate into a no-op.

2. **The provenance chain for the three extracted slices.** Figures 1, 4 and 6
   are sourced from ``results/``, which is gitignored: a thesis figure whose only
   source is a machine-local artifact does not regenerate on a fresh clone. The
   ``extract`` command lifts the slice each needs into ``docs/decisions/`` and
   records which artifact it was cut from. The gate is a *content* comparison --
   re-extracting from the live artifact must reproduce the committed slice --
   because the campaign manifest carries per-stage timestamps and a file-digest
   gate would therefore fire after every campaign run without a number moving.

3. **The two claims figure 2 exists to make.** ``k_aq`` is the largest knob at
   every section and every anchor, and ``m_p`` is the only knob that cancels.
   Both are re-derived from the committed synthesis record rather than taken
   from the figure, so a change in the evidence fails the test rather than
   quietly redrawing a figure that no longer says what its title says.

4. **ADR-0024.** KP 62.0's 51.0 to 56.5 m grid extension is a hypothetical fit
   stabiliser. Wherever it is plotted it is shaded, and wherever it is tabulated
   it is flagged.

5. **The A1/A2 distinction.** The synthesis record's ``design_hwl`` anchor is
   the nearest *grid level* to a section's HWL, not the HWL (KP 62.0: 46.50 m
   against 46.39 m). ADR-0040 section 2.5 established those are resolvably
   different, so no figure here may call one the other.

No physics runs: every check is against committed evidence, committed CSV or
source structure. Following the 2026-07-31 hardening rule, a tracked path
asserts; only the two genuinely optional gitignored campaign artifacts use
``skipif``.
"""

from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
FIGURES = DOCS / "figures"
DECISIONS = DOCS / "decisions"
DRIVER = REPO / "scripts" / "thesis_figure_gaps.py"

sys.path.insert(0, str(REPO / "scripts"))

PHASE2_SLICE = DECISIONS / "phase2-survival-update-per-stratum.json"
PEAK_SHORTCUT_SLICE = DECISIONS / "phase2-peak-shortcut.json"
RQ4_SLICE = DECISIONS / "phase3-sensitivity-brackets.json"
SYNTHESIS = DECISIONS / "epistemic-bracket-synthesis.json"
HWL_EVIDENCE = DECISIONS / "adr0040-hwl-bias-resolution.json"

#: The six figures and the CSV that carries each one's numbers.
FIGURE_TO_CSV = {
    "phase2_survival_update.png": "phase2-survival-update-per-stratum.csv",
    "phase2_peak_shortcut.png": "phase2-peak-shortcut.csv",
    "epistemic_bracket_ranking.png": "epistemic-bracket-ranking.csv",
    "adr0040_kp57_4_bound.png": "adr0040-kp57_4-bias-bound.csv",
    "rq4_sensitivity_brackets.png": "rq4-sensitivity-brackets.csv",
    "epistemic_knobs_mp_ztoe.png": "epistemic-knobs-mp-ztoe.csv",
}

#: The four Phase 2 diagnostics promoted by ``pipeline.PUBLICATION_FIGURES``
#: (inventory rows 4.3, 4.4 and 5.1). These are written by the Phase 2 package
#: itself, not by ``thesis_figure_gaps.py``, so they have no table-source CSV.
PHASE2_PUBLICATION_FIGURES = {
    "phase2_marginals_kp58_8_matrix.png",
    "phase2_marginals_kp60_0_matrix.png",
    "phase2_fragility_update_kp58_8_matrix.png",
    "phase2_fragility_update_kp60_0_matrix.png",
}

#: ADR-0024: KP 62.0's conditioning grid runs past this stage purely to
#: stabilise the lognormal fit. Read from the record by the driver; repeated
#: here so a change to either has to be made in both places on purpose.
ATTAINABLE_MAX_KP62 = 50.5


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(name: str) -> list[dict[str, str]]:
    with (DECISIONS / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _require(path: Path) -> Path:
    """Assert a committed artifact this guard depends on is still present.

    ``skipif`` is correct for a gitignored machine-local artifact and wrong for
    a tracked one: a move, rename or deletion would silently disable the guard
    while the suite still reported green (``docs/conventions.md`` section 9.4).
    """
    assert path.is_file(), (
        f"{path.relative_to(REPO).as_posix()} is a committed artifact this guard "
        "depends on, and it is missing. Regenerate it with "
        "`python scripts/thesis_figure_gaps.py all`, or update this test in the "
        "same change if it moved."
    )
    return path


# --------------------------------------------------------------------------- #
# 1. The dual-write and the G7 declaration                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", sorted(FIGURE_TO_CSV))
def test_each_figure_and_its_table_source_are_committed(name: str) -> None:
    """Both halves of the deliverable are tracked, and neither is empty.

    The figure is the argument and the CSV is the table source a thesis session
    typesets from. They are written in the same call from the same evidence, so
    one existing without the other means a partial run was committed.
    """
    figure = _require(FIGURES / name)
    _require(DECISIONS / FIGURE_TO_CSV[name])
    assert figure.stat().st_size > 0
    assert len(_rows(FIGURE_TO_CSV[name])) > 0


def test_every_figure_goes_through_the_dual_writing_save_helper() -> None:
    """No bare ``savefig``: the publication copy is not optional.

    ``_figstyle.save`` always writes ``docs/figures/`` and mirrors to the
    study-local directory when asked. A driver that called ``savefig`` directly
    could produce a figure that exists only under gitignored ``results/`` and is
    therefore not a deliverable, which is the failure the dual-write replaced.
    """
    tree = ast.parse(_require(DRIVER).read_text(encoding="utf-8"))

    def dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return f"{dotted(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        return ""

    saves = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and dotted(node.func) == "figstyle.save"
    ]
    assert len(saves) == len(FIGURE_TO_CSV), "one save call per figure"
    for call in saves:
        keywords = {kw.arg for kw in call.keywords}
        assert "mirror" in keywords, "every figure must also be mirrored"

    direct = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and dotted(node.func).endswith(".savefig")
    ]
    assert not direct, "figure writes must go through figstyle.save"


def test_the_six_figures_are_declared_by_exact_name_in_the_g7_gate() -> None:
    """A glob would let two drivers claim one figure and bind it to the wrong one.

    ``adr0040_kp57_4_bound.png`` is the live case: the design-HWL bias driver's
    ``adr0040_*.png`` pattern would have swept it up, measured it against that
    driver's sources, and never re-drawn it. Both entries now name their files.
    """
    from production_campaign import FIGURE_DRIVERS

    (entry,) = [
        driver
        for driver in FIGURE_DRIVERS
        if driver["label"].startswith("thesis figure gaps")
    ]
    assert set(entry["produces"]) == set(FIGURE_TO_CSV)
    assert not any("*" in pattern for pattern in entry["produces"])
    assert entry["command"][1] == "scripts/thesis_figure_gaps.py"

    claims: dict[str, list[str]] = {}
    for driver in FIGURE_DRIVERS:
        for pattern in driver["produces"]:
            for path in FIGURES.glob(pattern):
                claims.setdefault(path.name, []).append(driver["label"])
    contested = {name: owners for name, owners in claims.items() if len(owners) > 1}
    assert not contested, contested


def test_every_declared_path_of_this_driver_resolves() -> None:
    """A declaration that cannot resolve turns a real gate into a false failure.

    The figure pass already hit this once: a ``requires`` pointing at
    ``adr0033-gsa-study.json`` failed because that evidence is per-section. Every
    input of this driver is committed, so absence is never a fresh clone.
    """
    from production_campaign import FIGURE_DRIVERS

    (entry,) = [
        driver
        for driver in FIGURE_DRIVERS
        if driver["label"].startswith("thesis figure gaps")
    ]
    for field in ("requires", "sources"):
        assert entry[field], f"{field} must not be empty"
        for pattern in entry[field]:
            assert pattern.startswith("docs/"), (
                f"{pattern} is not committed; this driver must not depend on a "
                "gitignored artifact at draw time"
            )
            assert list(REPO.glob(pattern)), pattern


def test_the_draw_command_reads_no_gitignored_artifact() -> None:
    """``figures`` must run from committed evidence alone.

    The whole reason ``extract`` exists is that ``results/`` is gitignored. If
    the draw path reached back into it, a fresh clone would silently produce a
    different figure or none at all.
    """
    tree = ast.parse(_require(DRIVER).read_text(encoding="utf-8"))
    draw = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "cmd_figures"
    )
    names = {node.id for node in ast.walk(draw) if isinstance(node, ast.Name)}
    assert "CAMPAIGN_MANIFEST" not in names
    assert "RQ4_ANNUAL" not in names


def test_help_is_inert(tmp_path: Path) -> None:
    """``--help`` must not write anything.

    A ``--help`` sweep during the 2026-07-31 cleanup ran a whole study and
    rewrote a tracked evidence file. The parser is therefore built and the
    arguments parsed before any read or write.
    """
    watched = sorted(DECISIONS.glob("*.json")) + sorted(DECISIONS.glob("*.csv"))
    before = {path: path.stat().st_mtime_ns for path in watched}
    result = subprocess.run(
        [sys.executable, str(DRIVER), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert result.returncode == 0, result.stderr
    assert "extract" in result.stdout and "figures" in result.stdout
    after = {path: path.stat().st_mtime_ns for path in watched}
    assert before == after, "--help touched a committed evidence file"


# --------------------------------------------------------------------------- #
# 2. Provenance of the three extracted slices                                   #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("slice_path", [PHASE2_SLICE, RQ4_SLICE], ids=lambda p: p.name)
def test_each_extracted_slice_records_where_it_came_from(slice_path: Path) -> None:
    """The slice is only trustworthy if it says what it was cut from."""
    record = _read(_require(slice_path))
    source = record["source"]
    assert source["gitignored"] is True
    assert source["path"].startswith("results/")
    assert len(source["sha256"]) == 64
    assert record["generated_by"] == "scripts/thesis_figure_gaps.py extract"


@pytest.mark.parametrize(
    ("slice_path", "extractor", "block"),
    [
        (PHASE2_SLICE, "extract_phase2_slice", "runs"),
        (RQ4_SLICE, "extract_rq4_slice", "sections"),
    ],
    ids=lambda value: value.name if isinstance(value, Path) else str(value),
)
def test_the_slice_still_reproduces_from_the_live_artifact(
    slice_path: Path, extractor: str, block: str
) -> None:
    """When the campaign artifact is on this machine, re-cutting must agree.

    This is the one place the chain from gitignored artifact to committed
    evidence to figure is actually closed. The comparison is on the extracted
    *content*, not on the artifact's file digest: the campaign manifest carries
    a per-stage timestamp and a runtime, so its SHA-256 changes on every run
    while every number in it stays put -- the same churn the 2026-07-31 audit
    hit with `assess_2011_2006_closure.py`, where a diff turned out to be
    `runtime_seconds` and nothing else. A file-digest gate would cry wolf after
    a re-run and stay silent about nothing. The recorded digest is kept as an
    identifier of which artifact was cut, and is checked for shape above.

    The artifact itself is untracked, so its absence is a fresh clone rather
    than a defect.
    """
    import thesis_figure_gaps

    record = _read(_require(slice_path))
    artifact = REPO / record["source"]["path"]
    if not artifact.is_file():
        pytest.skip(
            f"{record['source']['path']} is untracked (gitignored campaign "
            "artifact); absent on a fresh clone"
        )
    fresh = getattr(thesis_figure_gaps, extractor)()
    assert fresh[block] == record[block], (
        f"{record['source']['path']} no longer yields the committed slice. "
        "Re-run `python scripts/thesis_figure_gaps.py extract`."
    )


def test_the_peak_shortcut_slice_records_all_sixteen_artifacts_it_was_cut_from() -> (
    None
):
    """Row 4.7's slice is cut from many artifacts, so it carries a ``sources`` list.

    The other two slices each come from one file and use a singular ``source``
    block. This one is measured across the eight strata, so it names all sixteen
    inputs (a Phase 1 sweep and a Phase 2 posterior sidecar apiece) rather than
    a representative one, which would leave fifteen unrecorded.
    """
    record = _read(_require(PEAK_SHORTCUT_SLICE))
    sources = record["sources"]
    assert len(sources) == 2 * len(record["strata"]) == 16
    for source in sources:
        assert source["gitignored"] is True
        assert source["path"].startswith("results/")
        assert len(source["sha256"]) == 64
    assert record["generated_by"] == "scripts/thesis_figure_gaps.py extract"


def test_the_peak_shortcut_slice_still_reproduces_from_the_live_artifacts() -> None:
    """Closes the chain for row 4.7, when the sweeps are on this machine."""
    import thesis_figure_gaps

    record = _read(_require(PEAK_SHORTCUT_SLICE))
    missing = [s["path"] for s in record["sources"] if not (REPO / s["path"]).is_file()]
    if missing:
        pytest.skip(
            f"{missing[0]} is untracked (gitignored production sweep); absent "
            "on a fresh clone"
        )
    fresh = thesis_figure_gaps.extract_peak_shortcut_slice()
    assert fresh["strata"] == record["strata"], (
        "the production sweeps no longer yield the committed peak-shortcut "
        "slice. Re-run `python scripts/thesis_figure_gaps.py extract`."
    )


# --------------------------------------------------------------------------- #
# 2b. What row 4.7's figure claims (the WBI+ peak-only shortcut)                #
# --------------------------------------------------------------------------- #


def test_the_peak_shortcut_reproduces_the_published_2_75_and_3_90() -> None:
    """``docs/phase2_report.md`` section 11.1 is the published statement.

    It reports the peak-only reading against the replay at production N: KP 58.8
    15.6 % against 5.67 % (factor 2.75) and KP 60.0 13.1 % against 3.36 %
    (3.90). Those are the two informative strata and they are the scope of the
    "2.75 to 3.9x" claim, so the slice's headline band must be exactly them.
    """
    record = _read(_require(PEAK_SHORTCUT_SLICE))
    by_stratum = {s["stratum"]: s for s in record["strata"]}

    kp58_8 = by_stratum["tokachi_kp58.8_historical_matrix"]
    assert kp58_8["f_peak_only_transient"] * 100 == pytest.approx(15.6, abs=0.05)
    assert kp58_8["f_replay_transient"] * 100 == pytest.approx(5.67, abs=0.005)
    assert kp58_8["over_rejection_factor"] == pytest.approx(2.75, abs=0.005)

    kp60_0 = by_stratum["tokachi_kp60.0_historical_matrix"]
    assert kp60_0["f_peak_only_transient"] * 100 == pytest.approx(13.1, abs=0.05)
    assert kp60_0["f_replay_transient"] * 100 == pytest.approx(3.36, abs=0.005)
    assert kp60_0["over_rejection_factor"] == pytest.approx(3.90, abs=0.005)

    headline = record["headline"]
    assert set(headline["informative_strata"]) == {
        "tokachi_kp58.8_historical_matrix",
        "tokachi_kp60.0_historical_matrix",
    }
    assert headline["factor_min"] == pytest.approx(2.75, abs=0.005)
    assert headline["factor_max"] == pytest.approx(3.90, abs=0.005)


def test_the_shortcut_over_rejects_wherever_the_comparison_is_defined() -> None:
    """The direction is the claim; a stratum where it reversed would break it.

    "Biased unsafe" means the peak-only reading discards realizations the full
    replay keeps, never the other way round. If any stratum ever came back with
    a factor below 1, the RQ2 clause would need rewriting, not the figure.
    """
    record = _read(_require(PEAK_SHORTCUT_SLICE))
    defined = [s for s in record["strata"] if s["over_rejection_factor"] is not None]
    assert defined, "at least one stratum must admit the comparison"
    for stratum in defined:
        assert (
            stratum["f_peak_only_transient"] > stratum["f_replay_transient"]
        ), f"{stratum['stratum']}: the peak-only reading no longer over-rejects"
        assert stratum["over_rejection_factor"] > 1.0


def test_a_stratum_with_no_rejection_has_no_factor_rather_than_one() -> None:
    """Not defined, not agreement, not unbounded: three different things.

    Four strata reject nothing under either reading. A factor of 0/0 is not 1.0
    (which would read as "the shortcut agrees here", a claim the data cannot
    support) and not unbounded (which would read as infinite disagreement). It
    is null, and the figure says so in words on those rows. This is the same
    discipline the ranking figure applies to ``unbounded`` against
    ``not defined``.
    """
    record = _read(_require(PEAK_SHORTCUT_SLICE))
    undefined = [s for s in record["strata"] if s["over_rejection_factor"] is None]
    assert len(undefined) == record["headline"]["n_not_defined"] == 4
    for stratum in undefined:
        assert stratum["f_peak_only_transient"] == 0.0
        assert stratum["f_replay_transient"] == 0.0
        assert stratum["n_rejected_replay"] == 0

    rows = {
        (row["section"], row["d70"]): row for row in _rows("phase2-peak-shortcut.csv")
    }
    for stratum in undefined:
        assert (
            rows[(stratum["section"], stratum["d70"])]["over_rejection_factor"]
            == "not defined"
        )


def test_the_small_number_strata_are_marked_and_kept_out_of_the_headline() -> None:
    """65 and 23 rejected rows are not a measurement of a factor.

    Section 11.1 calls KP 57.4 the "small-number regime" at 65 rejected rows;
    KP 60.0 bulk is further into it at 23. Their factors (7.46 and 6.12) are the
    largest in the set, so letting them into the headline band would widen the
    published "2.75 to 3.9x" to "2.75 to 7.5x" on the strength of 88 rows.
    """
    record = _read(_require(PEAK_SHORTCUT_SLICE))
    flagged = {s["stratum"] for s in record["strata"] if s["small_number_regime"]}
    assert flagged == {
        "tokachi_kp57.4_historical_matrix",
        "tokachi_kp60.0_historical_bulk",
    }
    for stratum in record["strata"]:
        assert stratum["small_number_regime"] == (
            0 < stratum["n_rejected_replay"] < record["method"]["small_number_rows"]
        )
    assert not flagged & set(record["headline"]["informative_strata"])


def test_the_peak_only_reading_is_the_prior_transient_curve_not_the_static_one() -> (
    None
):
    """Both sides of the comparison are transient; it compares methods.

    A figure that put the peak-only *static* number against the transient replay
    would be comparing limit states and would read as a much larger effect (the
    static branch rejects 57.6 % at KP 58.8 against the transient 15.6 %). The
    slice's method block states which curve is read, and the survival-update
    slice carries the static column that must NOT be the one used here.
    """
    record = _read(_require(PEAK_SHORTCUT_SLICE))
    assert "P_f_trans_raw" in record["method"]["peak_only"]

    baseline = {
        s["stratum"]: s
        for run in _read(_require(PHASE2_SLICE))["runs"]
        if run["run"] == "baseline"
        for s in run["strata"]
    }
    for stratum in record["strata"]:
        static = baseline[stratum["stratum"]]["f_static_reject"]
        assert stratum["f_peak_only_transient"] != static or static == 0.0


# --------------------------------------------------------------------------- #
# 3. Figure 1 -- the central Bayesian claim                                     #
# --------------------------------------------------------------------------- #


def test_the_marginal_transient_rejection_is_exactly_zero_in_every_run() -> None:
    """The nesting result: the transient failure set sits inside the static one.

    Sixteen runs -- eight baseline strata plus both documented variants at the
    four matrix strata. "Approximately zero" would be a different and much
    weaker claim, so the comparison is exact.
    """
    record = _read(_require(PHASE2_SLICE))
    every = [s for run in record["runs"] for s in run["strata"]]
    assert len(every) == 16
    assert record["totals"]["n_runs"] == 16
    for stratum in every:
        assert stratum["f_marginal_transient"] == 0.0, stratum["stratum"]
    assert record["totals"]["marginal_transient_all_zero"] is True


def test_the_masked_versus_reevaluation_verification_is_exact() -> None:
    """Zero flag mismatches at all eight strata, verified rather than assumed."""
    record = _read(_require(PHASE2_SLICE))
    baseline = next(run for run in record["runs"] if run["run"] == "baseline")
    assert len(baseline["strata"]) == 8
    for stratum in baseline["strata"]:
        assert stratum["verified"] is True, stratum["stratum"]
        assert stratum["flag_mismatch_static"] == 0
        assert stratum["flag_mismatch_trans"] == 0
    assert record["totals"]["flag_mismatches_total"] == 0


def test_the_per_stratum_rejection_figures_are_the_published_ones() -> None:
    """Inventory 4.1, to five decimal places, from the slice the figure draws."""
    rows = {
        (row["section"], row["d70"]): float(row["transient_reject_pct"])
        for row in _rows(FIGURE_TO_CSV["phase2_survival_update.png"])
        if row["run"] == "baseline"
    }
    assert rows[("KP57.4", "matrix")] == pytest.approx(0.065, abs=5e-4)
    assert rows[("KP58.8", "matrix")] == pytest.approx(5.673, abs=5e-4)
    assert rows[("KP60.0", "matrix")] == pytest.approx(3.363, abs=5e-4)
    assert rows[("KP62.0", "matrix")] == 0.0
    assert rows[("KP57.4", "bulk")] == 0.0
    assert rows[("KP58.8", "bulk")] == 0.0
    assert rows[("KP60.0", "bulk")] == pytest.approx(0.023, abs=5e-4)
    assert rows[("KP62.0", "bulk")] == 0.0


def test_the_static_branch_rejects_far_more_than_the_transient_one() -> None:
    """The figure's visual argument, as an assertion on its own numbers.

    Nesting is only visible because the static bar is the outer one at every
    stratum where anything is rejected at all.
    """
    record = _read(_require(PHASE2_SLICE))
    baseline = next(run for run in record["runs"] if run["run"] == "baseline")
    for stratum in baseline["strata"]:
        assert stratum["f_static_reject"] >= stratum["f_trans_reject"], stratum


# --------------------------------------------------------------------------- #
# 4. Figure 2 -- the two claims it exists to make                               #
# --------------------------------------------------------------------------- #


def test_k_aq_is_the_largest_knob_at_every_section_and_every_anchor() -> None:
    """Re-derived from the synthesis, not read off the figure.

    At each (section, anchor) whose baseline has failing rows, ``k_aq`` is
    either unbounded -- an arm sits at exactly zero failures, so no finite span
    can exceed it -- or it is the strict maximum over the other epistemic
    brackets. An unbounded ``k_aq`` is not clipped to a finite number, because
    that would read as a measurement.
    """
    from thesis_figure_gaps import ANCHORS, STATISTICAL_BRACKETS, _span_cell

    sections = _read(_require(SYNTHESIS))["sections"]
    checked = 0
    for section in sections:
        for anchor in ANCHORS:
            k_aq = _span_cell(section, "k_aq_prior_mean", anchor)
            if not k_aq["defined"]:
                continue
            checked += 1
            if k_aq["unbounded"]:
                continue
            others = [
                _span_cell(section, bracket, anchor)
                for bracket in section["brackets"]
                if bracket not in STATISTICAL_BRACKETS and bracket != "k_aq_prior_mean"
            ]
            assert not any(cell["unbounded"] for cell in others), (
                f"{section['section']} {anchor}: k_aq is finite while another "
                "epistemic bracket is unbounded"
            )
            largest = max(float(cell["span"]) for cell in others if cell["defined"])
            assert float(k_aq["span"]) > largest, (section["section"], anchor)
    assert checked == 19, "one anchor is undefined by design (KP 57.4 design HWL)"


def test_kp57_4_has_no_design_level_multiplier_and_that_is_not_a_gap() -> None:
    """Zero transient failures in 1e5 means no multiplier of any kind exists.

    ``unbounded`` and ``not defined`` are different facts and the figure keeps
    them apart: the first says an arm reached zero, the second says the baseline
    did.
    """
    from thesis_figure_gaps import _span_cell

    section = next(
        s for s in _read(_require(SYNTHESIS))["sections"] if s["section"] == "KP57.4"
    )
    cell = _span_cell(section, "k_aq_prior_mean", "design_hwl")
    assert cell["defined"] is False
    assert cell["n_failures_trans_baseline"] == 0
    rows = [
        row
        for row in _rows(FIGURE_TO_CSV["epistemic_bracket_ranking.png"])
        if row["section"] == "KP57.4" and row["anchor"] == "design_hwl"
    ]
    assert rows and all(row["span_trans"] == "not_defined" for row in rows)


def test_m_p_is_the_only_bracket_that_cancels_in_the_ratio() -> None:
    """ADR-0048's property (c) was refuted; only the common-mode knob survives.

    ``m_p`` cancels because ADR-0045 section 2 applies it to the single-source
    H_c in BOTH branches. Every other bracket that moves both branches departs
    from rho = 1 by at least 1.8x at every section. ``gamma'_bl`` is excluded
    from that comparison on purpose: ADR-0028 keeps it out of the static branch
    entirely, so its rho near 1 is inertness, not cancellation, and treating it
    as a second canceller would be the same category error.
    """
    from thesis_figure_gaps import (
        COMMON_MODE_BRACKET,
        SINGLE_BRANCH_BRACKETS,
        _cancellation_by_bracket,
    )

    assert COMMON_MODE_BRACKET == "m_p"
    assert SINGLE_BRANCH_BRACKETS == {"gamma_bl_sub_prior_mean"}

    for section in _read(_require(SYNTHESIS))["sections"]:
        worst = _cancellation_by_bracket(section)
        m_p = worst["m_p"]["max_resolved_departure_factor"]
        assert m_p <= 1.25, (section["section"], m_p)
        for bracket, record in worst.items():
            if bracket == COMMON_MODE_BRACKET or bracket in SINGLE_BRANCH_BRACKETS:
                continue
            assert record["max_resolved_departure_factor"] >= 1.8, (
                section["section"],
                bracket,
                record,
            )


def test_the_contaminated_kp57_4_length_arm_is_excluded_by_name() -> None:
    """ADR-0047: the all-station median at KP 57.4 measures road fill.

    Including it would put the L bracket's departure at 10.7 instead of the
    2.25 the synthesis note publishes, and would attribute a road embankment's
    geometry to the levee.
    """
    from thesis_figure_gaps import (
        CANCELLATION_ARM_EXCLUSIONS,
        _cancellation_by_bracket,
    )

    assert "L_dem_all_stations_median" in CANCELLATION_ARM_EXCLUSIONS
    published = {"KP57.4": 2.25, "KP58.8": 1.82, "KP60.0": 3.22, "KP62.0": 2.11}
    for section in _read(_require(SYNTHESIS))["sections"]:
        worst = _cancellation_by_bracket(section)["L_measurement"]
        assert worst["max_resolved_departure_factor"] == pytest.approx(
            published[section["section"]], abs=0.01
        )


def test_the_ranking_order_is_computed_from_the_evidence() -> None:
    """The ordering claim must follow the data, not an editor's preference."""
    from thesis_figure_gaps import _bracket_order

    order = _bracket_order(_read(_require(SYNTHESIS))["sections"])
    assert order[0] == "k_aq_prior_mean"
    assert set(order) == {
        "k_aq_prior_mean",
        "cov_L",
        "z_toe",
        "L_measurement",
        "m_p",
        "gamma_bl_sub_prior_mean",
    }


# --------------------------------------------------------------------------- #
# 5. Figure 3 -- a bound, not a point estimate                                  #
# --------------------------------------------------------------------------- #


def test_the_kp57_4_bound_reproduces_the_published_148_and_101() -> None:
    """Recomputed from the counts with the repo's own Clopper-Pearson helper.

    The companion note's bound divides the static branch's 95 % lower endpoint
    by the transient branch's 95 % upper one, rather than trusting a bootstrap
    over two failing rows. Recomputing it here keeps the figure's headline
    traceable to ADR-0024's construction instead of to a transcribed number.
    """
    from thesis_figure_gaps import _clopper_pearson_bound

    brute = _read(_require(HWL_EVIDENCE))["stages"]["A_brute_kp57_4"]
    n = int(brute["n_samples"])
    a1, a2 = brute["anchor_A1"], brute["anchor_A2"]
    assert round(_clopper_pearson_bound(a1["k_static"], a1["k_transient"], n)) == 148
    assert round(_clopper_pearson_bound(a2["k_static"], a2["k_transient"], n)) == 101


def test_the_two_kp57_4_anchors_stay_distinct_and_unresolved() -> None:
    """A1 is 39.21 m on 2 rows, A2 is 39.25 m on 10. Neither is an estimate."""
    rows = {
        row["role"]: row
        for row in _rows(FIGURE_TO_CSV["adr0040_kp57_4_bound.png"])
        if row["role"]
    }
    assert float(rows["A1_design_hwl"]["level_m_msl"]) == pytest.approx(39.21)
    assert int(rows["A1_design_hwl"]["k_transient"]) == 2
    assert rows["A1_design_hwl"]["resolved"] == "False"
    assert float(rows["A2_nearest_grid_level"]["level_m_msl"]) == pytest.approx(39.25)
    assert int(rows["A2_nearest_grid_level"]["k_transient"]) == 10
    assert rows["A2_nearest_grid_level"]["resolved"] == "False"
    assert (
        rows["A1_design_hwl"]["level_m_msl"]
        != rows["A2_nearest_grid_level"]["level_m_msl"]
    )


def test_the_quotable_anchor_carries_its_flip_caveat() -> None:
    """39.50 m is the recommended anchor AND one of the three flip levels.

    One barrier-jump row in 521 biases B down about 0.2 %, conservative in
    direction. It is uncomfortable and it is drawn: dropping it quietly would
    misrepresent the number a viva would be shown.
    """
    (row,) = [
        row
        for row in _rows(FIGURE_TO_CSV["adr0040_kp57_4_bound.png"])
        if row["role"] == "A3_quotable_anchor"
    ]
    assert float(row["level_m_msl"]) == pytest.approx(39.50)
    assert int(row["k_transient"]) == 521
    assert float(row["bias_B"]) == pytest.approx(42.7, abs=0.05)
    assert row["resolved"] == "True"
    assert int(row["euler_barrier_jump_rows"]) == 1, (
        "the recommended anchor's own flip contamination must survive into the "
        "table a chapter typesets from"
    )
    source = DRIVER.read_text(encoding="utf-8")
    assert "conservative in direction" in source


def test_the_euler_flip_levels_are_an_n1e6_statement() -> None:
    """Four rows in 1e6; the expected count at the production N = 1e5 is 0.4.

    An unqualified "all Euler-flip counts are 0" reads as a statement about the
    discretisation when it is a statement about the sample size, so the figure
    names its N.
    """
    flips = {
        float(row["level_m_msl"]): int(row["euler_barrier_jump_rows"])
        for row in _rows(FIGURE_TO_CSV["adr0040_kp57_4_bound.png"])
        if int(row["euler_barrier_jump_rows"]) > 0
    }
    assert flips == {39.50: 1, 40.25: 2, 40.75: 1}
    assert sum(flips.values()) == 4
    source = DRIVER.read_text(encoding="utf-8")
    assert "$N = 10^5$" in source and "$N = 10^6$" in source


# --------------------------------------------------------------------------- #
# 6. Figure 4 -- the Phase 3 sensitivity brackets                               #
# --------------------------------------------------------------------------- #


def test_the_rq4_brackets_cover_four_sections_two_climates_and_five_arms() -> None:
    """Campaign decision 5 scopes RQ3/RQ4 to the four characterised sections."""
    rows = _rows(FIGURE_TO_CSV["rq4_sensitivity_brackets.png"])
    assert len(rows) == 4 * 2 * 5
    assert {row["section"] for row in rows} == {
        "KP57.4",
        "KP58.8",
        "KP60.0",
        "KP62.0",
    }
    assert {row["arm"] for row in rows} == {
        "baseline",
        "lambda_ac_100m",
        "lambda_ac_40m",
        "bulk_d70",
        "prior_bep",
    }


def test_the_three_brackets_run_in_the_documented_directions() -> None:
    """A shorter correlation length raises the number; the 2016 update lowers it.

    The signs are the claim. ``lambda_ac`` = 40 m is the conservative end of
    ADR-0037's bracket, so it must never come out below the production value,
    and the posterior must never sit above the prior.
    """
    rows = _rows(FIGURE_TO_CSV["rq4_sensitivity_brackets.png"])
    for row in rows:
        ratio = float(row["ratio_system_to_baseline"])
        if row["arm"] in ("lambda_ac_100m", "lambda_ac_40m"):
            assert ratio > 1.0, row
        elif row["arm"] == "bulk_d70":
            assert ratio < 1.0, row
        elif row["arm"] == "prior_bep":
            assert ratio >= 1.0, row


def test_the_kp58_8_posterior_lowers_the_annual_number_by_about_12_percent() -> None:
    """Inventory 6.10's one named number, from the slice the figure draws."""
    (row,) = [
        row
        for row in _rows(FIGURE_TO_CSV["rq4_sensitivity_brackets.png"])
        if row["section"] == "KP58.8"
        and row["scenario"] == "historical"
        and row["arm"] == "prior_bep"
    ]
    # The prior is 1.141x the posterior, i.e. the update cuts it 12.4 %.
    assert 1.0 - 1.0 / float(row["ratio_system_to_baseline"]) == pytest.approx(
        0.124, abs=0.005
    )


# --------------------------------------------------------------------------- #
# 7. ADR-0024 and the A1/A2 distinction                                         #
# --------------------------------------------------------------------------- #


def test_the_knob_figure_shades_the_hypothetical_extension() -> None:
    """KP 62.0's grid runs to 56.5 m; only 50.5 m of it is attainable.

    The panels plot stage on the x axis and KP 62.0 is on them, so the
    above-crest band must be shaded on every one of the four.
    """
    tree = ast.parse(_require(DRIVER).read_text(encoding="utf-8"))
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "figure_epistemic_knobs"
    )
    calls = [
        node
        for node in ast.walk(func)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "mark_hypothetical"
    ]
    assert calls, "figure 5 plots KP 62.0 against stage and must shade the extension"


def test_the_attainable_maximum_is_read_from_the_record_not_hard_coded() -> None:
    """One source of truth for 50.5 m, so a change cannot half-propagate."""
    from thesis_figure_gaps import STAGE66_KP62, _attainable_max_kp62

    assert _require(STAGE66_KP62)
    assert _attainable_max_kp62() == pytest.approx(ATTAINABLE_MAX_KP62)

    # Parsed, not grepped: naming the value in a docstring is documentation,
    # while a numeric literal in code is a second source of truth that a change
    # to the record would leave behind.
    tree = ast.parse(DRIVER.read_text(encoding="utf-8"))
    literals = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, float)
        and node.value == ATTAINABLE_MAX_KP62
    ]
    assert not literals, (
        "the attainable maximum must come from "
        "docs/decisions/adr0040-stage6-6-kp62_0-analysis.json, not a literal"
    )


@pytest.mark.parametrize(
    "name",
    ["epistemic_bracket_ranking.png", "epistemic_knobs_mp_ztoe.png"],
)
def test_above_crest_levels_are_flagged_in_the_table_source(name: str) -> None:
    """A CSV a chapter typesets from must say which rows are not attainable.

    Shading carries it in the figure; the flag carries it in the table. Both are
    needed, because the two are read by different people at different times.
    """
    rows = _rows(FIGURE_TO_CSV[name])
    assert any(row["above_attainable_max"] == "True" for row in rows)
    for row in rows:
        expected = (
            row["section"] == "KP62.0"
            and float(row["stage_m_msl"]) > ATTAINABLE_MAX_KP62
        )
        assert (row["above_attainable_max"] == "True") is expected, row


def test_no_figure_here_calls_the_nearest_grid_level_the_design_hwl() -> None:
    """The synthesis anchor is 46.50 m; KP 62.0's design HWL is 46.39 m.

    ADR-0040 section 2.5 established the two are resolvably different (rho =
    1.249 at KP 62.0), so quoting one as the other is a defect, not a rounding.
    The driver says "design-level anchor" and states the HWL beside it.
    """
    source = _require(DRIVER).read_text(encoding="utf-8")
    assert "design-level anchor" in source
    assert "nearest grid level" in source

    section = next(
        s for s in _read(_require(SYNTHESIS))["sections"] if s["section"] == "KP62.0"
    )
    assert section["anchors"]["design_hwl"]["stage_m_msl"] == pytest.approx(46.50)
    assert section["hwl_m_msl"] == pytest.approx(46.39)


def test_the_two_committed_companions_agree_on_the_production_baseline() -> None:
    """A free consistency gate the figure relies on, so it is checked not assumed.

    ADR-0045's companion carries its own copy of the production curves and the
    synthesis carries another. Figure 5 forms m_p ratios against the first and
    z_toe ratios against the second, so if they ever disagreed every ratio in
    two of its panels would be against a different denominator.
    """
    synthesis = {s["section"]: s for s in _read(_require(SYNTHESIS))["sections"]}
    companion = _read(_require(DECISIONS / "adr0045-mp-companion.json"))
    for section in companion["sections"]:
        label = "KP" + section["cross_section_id"].split("kp")[1]
        expected = synthesis[label]
        assert section["grid_m_msl"] == expected["grid_m_msl"], label
        assert section["p_f_trans_baseline"] == expected["P_f_trans_baseline_curve"]
        assert section["p_f_static_baseline"] == expected["P_f_static_baseline_curve"]


# --------------------------------------------------------------------------- #
# 7. The Phase 2 dual-write seam (inventory rows 4.3, 4.4, 5.1)                  #
# --------------------------------------------------------------------------- #
#
# These four figures are the one set in this file that ``thesis_figure_gaps.py``
# does not draw. They come out of ``bayesian_reliability_updating.pipeline``
# itself, because the posterior they depict is a 1e5-row replay rather than a
# committed slice. What is pinned is the seam: which runs are promoted, that a
# scenario run is not, and that the promotion cannot be silently widened or
# dropped.


def test_the_promoted_phase_2_figures_are_committed_and_declared() -> None:
    """Rows 4.3, 4.4 and 5.1 must survive a fresh clone into the thesis."""
    from production_campaign import FIGURE_DRIVERS

    for name in sorted(PHASE2_PUBLICATION_FIGURES):
        assert _require(FIGURES / name).stat().st_size > 0

    (entry,) = [
        driver
        for driver in FIGURE_DRIVERS
        if driver["label"].startswith("Phase-2 posterior diagnostics")
    ]
    assert set(entry["produces"]) == PHASE2_PUBLICATION_FIGURES
    assert not any("*" in pattern for pattern in entry["produces"])
    assert "--figures-only" in entry["command"], (
        "the redraw path must be the read-only one: the persisted posteriors "
        "are SHA-256-recorded in the campaign manifest"
    )
    assert entry["sources"], "these figures must be bound to what they depict"


def test_the_seam_promotes_exactly_the_two_informative_matrix_strata() -> None:
    """Four of 44, chosen deliberately, not a blanket dual-write.

    The two informative strata are KP 58.8 and KP 60.0 matrix (transient
    rejection 5.67 % and 3.36 % against <= 0.07 % everywhere else). Every number
    inventory rows 4.3, 4.4 and 5.1 quote is measured at exactly these two. A
    widened registry would put near-null pairs in the thesis; a narrowed one
    would drop a number that has no other home.
    """
    from bayesian_reliability_updating.pipeline import PUBLICATION_FIGURES

    assert set(PUBLICATION_FIGURES) == {
        "tokachi_kp58.8_historical_matrix",
        "tokachi_kp60.0_historical_matrix",
    }
    promoted = set()
    for stem, kinds in PUBLICATION_FIGURES.items():
        assert set(kinds) == {"marginals", "fragility_update"}, stem
        promoted |= set(kinds.values())
    assert promoted == PHASE2_PUBLICATION_FIGURES


@pytest.mark.parametrize("name", sorted(PHASE2_PUBLICATION_FIGURES))
def test_each_promoted_figure_name_states_its_stratum(name: str) -> None:
    """A file called ``marginals.png`` in a shared directory is unusable.

    ``docs/figures/`` is flat and holds 62 files, so the section and the d70
    interpretation both have to be in the name.
    """
    assert name.startswith("phase2_")
    assert ("kp58_8" in name) or ("kp60_0" in name)
    assert name.endswith("_matrix.png")


def test_an_adr0046_scenario_run_writes_no_publication_copy() -> None:
    """The registry is keyed on the stem, and that is load-bearing.

    ADR-0046 suffixes a z_toe scenario's output stem (``_ztoe_plus0.30m``) so a
    scenario posterior can never masquerade as the baseline. Keying the figure
    registry on the same stem extends that guarantee to ``docs/figures/``: a
    scenario finds no entry and writes nothing there.
    """
    from bayesian_reliability_updating.pipeline import publication_path

    baseline = "tokachi_kp58.8_historical_matrix"
    assert publication_path(baseline, "marginals") is not None
    for suffix in ("_ztoe_plus0.30m", "_ztoe_minus0.30m"):
        assert publication_path(baseline + suffix, "marginals") is None
        assert publication_path(baseline + suffix, "fragility_update") is None


def test_an_unpromoted_stratum_or_kind_writes_no_publication_copy() -> None:
    """The other six strata and the other four figure kinds stay run-local."""
    from bayesian_reliability_updating.pipeline import publication_path

    assert publication_path("tokachi_kp62.0_historical_matrix", "marginals") is None
    assert publication_path("tokachi_kp58.8_historical_bulk", "marginals") is None
    for kind in ("decomposition", "rejection_scatter", "record", "breach_times"):
        assert publication_path("tokachi_kp58.8_historical_matrix", kind) is None


def test_the_seam_is_wired_into_exactly_the_two_promoted_plot_calls() -> None:
    """AST guard: the dual-write cannot be dropped or widened by accident.

    ``_figures`` makes six kinds of plot call. Exactly two carry
    ``publication_path``; the rest must not, or a run-local diagnostic would
    start landing in the tracked publication directory.
    """
    import ast as _ast

    source = (REPO / "bayesian_reliability_updating" / "pipeline.py").read_text(
        encoding="utf-8"
    )
    tree = _ast.parse(source)
    figures = next(
        node
        for node in _ast.walk(tree)
        if isinstance(node, _ast.FunctionDef) and node.name == "_figures"
    )
    wired = {
        node.func.attr
        for node in _ast.walk(figures)
        if isinstance(node, _ast.Call)
        and isinstance(node.func, _ast.Attribute)
        and any(kw.arg == "publication_path" for kw in node.keywords)
    }
    assert wired == {"plot_prior_posterior_marginals", "plot_fragility_update"}


def test_the_publication_copy_defaults_off_in_the_plot_helper() -> None:
    """The default path is byte-identical to the pre-seam behaviour.

    ``_save`` writes one file when ``publication_path`` is None and two when it
    is given, from one figure object. The default keeps every other Phase 2
    figure, and every non-promoted run, exactly where it was.
    """
    import matplotlib.pyplot as plt

    from bayesian_reliability_updating import plots

    tmp = REPO / "results" / "_seam_selftest"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        fig = plt.figure()
        fig.add_subplot(111).plot([0, 1], [0, 1])
        plots._save(fig, tmp / "only.png")
        assert (tmp / "only.png").is_file()
        assert not (tmp / "also.png").exists()

        fig = plt.figure()
        fig.add_subplot(111).plot([0, 1], [0, 1])
        plots._save(fig, tmp / "run_local.png", tmp / "published.png")
        assert (tmp / "run_local.png").read_bytes() == (
            tmp / "published.png"
        ).read_bytes(), "both copies come from one figure and must be identical"
    finally:
        for path in tmp.glob("*.png"):
            path.unlink()
        tmp.rmdir()


def test_the_marginal_panels_carry_three_readable_ticks_on_any_span() -> None:
    """The promoted figure has to be legible, and the default locator was not.

    Matplotlib labels log-decade *minors*, which collides illegibly on a panel
    spanning well under a decade (``gamma'_bl`` runs about 5.5 to 9.5) and
    crowds one spanning several (``d_70``). That was invisible while these
    figures lived only under gitignored ``results/``. Percentile-anchored ticks
    give exactly three in-range labels whatever the span; this is chrome, and no
    plotted value depends on it.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    from bayesian_reliability_updating import plots

    for values in (
        np.geomspace(5.5, 9.5, 5000),  # sub-decade
        np.geomspace(1e-7, 1e-2, 5000),  # five decades
    ):
        fig, ax = plt.subplots()
        ax.set_xscale("log")
        ax.set_xlim(values.min(), values.max())
        plots._log_axis_ticks(ax, values)
        ticks = ax.get_xticks()
        assert len(ticks) == 3
        assert all(values.min() <= t <= values.max() for t in ticks)
        assert len(ax.xaxis.get_minorticklocs()) == 0
        assert all(label.get_text() for label in ax.get_xticklabels())
        plt.close(fig)

    assert plots._compact(6.9) == "6.9"
    assert plots._compact(0.043) == "0.043"
    assert plots._compact(0.00087) == r"$8.7\times10^{-4}$"
