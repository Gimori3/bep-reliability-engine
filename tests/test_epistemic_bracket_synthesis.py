"""Tests for the cross-bracket epistemic synthesis driver.

The driver is a study script: pure post-processing over persisted companion
sweeps plus in-memory ``geometry.L`` arms. What is worth pinning is that it
stays read-only against the committed inputs, that it refuses to report a
sensitivity against a drifted baseline, and above all that its cancellation
statistic is literally the ADR-0047 one rather than a second copy that could
drift away from the numbers this synthesis compares against.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
_SCRIPT = REPO / "scripts" / "epistemic_bracket_synthesis.py"
_ADR0047_SCRIPT = REPO / "scripts" / "dem_cross_section_study.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ebs = _load("epistemic_bracket_synthesis", _SCRIPT)


def _require_tracked(path: Path) -> Path:
    """Assert a *tracked* evidence artifact is still where the test expects it.

    ``ADR0047_EVIDENCE`` is committed under ``docs/decisions/``, so absence means
    it moved, was renamed or was deleted -- not that it is optional. Skipping on
    it silently disabled the guard while the suite stayed green (2026-07-31
    hardening pass).
    """
    assert path.is_file(), (
        f"{path.relative_to(REPO).as_posix()} is a tracked evidence artifact "
        "this guard depends on, and it is missing. If it moved, update this "
        "test in the same change."
    )
    return path


# --------------------------------------------------------------------------- #
# Structural pins                                                              #
# --------------------------------------------------------------------------- #
def test_ratio_kernel_is_the_adr0047_one_not_a_copy() -> None:
    """The cancellation statistic must be reused, never re-implemented.

    ADR-0047 section 4.5 established the paired-bootstrap ratio-of-ratios and
    published rho values with it. This synthesis re-applies the same test to
    other brackets and compares the answers, so a divergent second copy would
    silently invalidate the comparison.
    """
    adr0047 = _load("dem_cross_section_study_pin", _ADR0047_SCRIPT)
    # The bound functions must be *defined in* the ADR-0047 script ...
    for function in (ebs.ratio_of_ratios_ci, ebs.pattern_counts):
        assert Path(function.__code__.co_filename) == _ADR0047_SCRIPT
    # ... and the synthesis must not carry a second definition of either.
    source = _SCRIPT.read_text(encoding="utf-8")
    assert "def ratio_of_ratios_ci" not in source
    assert "def _pattern_counts" not in source
    assert ebs.RATIO_BOOTSTRAP_N == adr0047.RATIO_BOOTSTRAP_N == 2000
    assert ebs.RATIO_CONFIDENCE == adr0047.RATIO_CONFIDENCE == 0.95
    assert ebs.RATIO_MIN_FAILURES == adr0047.RATIO_MIN_FAILURES


def test_the_synthesis_never_writes_the_committed_inputs_csv_or_configs() -> None:
    """These knobs stay OFF in production; the synthesis only measures them."""
    source = _SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "INPUTS_CSV.write_text",
        "config_path.write_text",
        "to_yaml",
        "yaml.safe_dump",
        "yaml.dump",
    ):
        assert forbidden not in source, f"{forbidden} would mutate a committed input"
    # The only sanctioned override is in memory, through Config.model_validate.
    assert 'data["geometry"]["L"] = float(length)' in source
    assert "Config.model_validate(data)" in source


def test_persisted_arms_are_read_only_companions_under_results_sensitivity() -> None:
    """Every persisted arm must live under ``results/sensitivity/``."""
    for _, _, subdir, _ in ebs.PERSISTED_ARMS:
        assert subdir in {"adr0045_mp", "adr0046_ztoe", "adr0048_prior_means"}
    assert (
        "run_fragility_analysis(config, n_jobs=n_jobs, progress=False, persist=False)"
    )


def test_all_four_matrix_sections_are_covered() -> None:
    """The gap this study closes is KP 62.0 and KP 57.4; do not regress to two."""
    assert set(ebs.SECTIONS) == {"KP57.4", "KP58.8", "KP60.0", "KP62.0"}


def test_all_four_adr0048_scenarios_are_carried() -> None:
    labels = {label for label, *_ in ebs.PERSISTED_ARMS}
    assert {
        "k_aq_field_geomean",
        "k_aq_field_toe",
        "k_aq_regional_upper",
        "gamma_bl_sub_lower",
    } <= labels


# --------------------------------------------------------------------------- #
# Anchors                                                                      #
# --------------------------------------------------------------------------- #
def test_anchor_indices_pick_the_documented_levels() -> None:
    grid = np.array([40.0, 41.0, 42.0, 43.0, 44.0])
    p_trans = np.array([0.0, 2.1e-3, 0.02, 0.51, 0.99])
    anchors = ebs.anchor_indices(grid, p_trans, hwl=42.4)
    assert anchors["lowest_reachable"] == 1  # first level with any failure
    assert anchors["rising_limb"] == 1  # nearest P_f = 2e-3
    assert anchors["transition_midpoint"] == 3  # nearest P_f = 0.5
    assert anchors["design_hwl"] == 2  # nearest stage to the HWL
    assert anchors["grid_top"] == 4


def test_the_two_shoulder_conventions_are_kept_apart() -> None:
    """ADR-0045 and ADR-0048 both say "shoulder" and mean different stages.

    ADR-0045 quotes m_p at the low-probability rising limb (its text names
    P_f ~ 2e-3); ADR-0048 quotes k_aq at the transition midpoint (verified: its
    KP58.8 field-toe x0.088 sits where baseline P_f_trans = 0.4915). A table
    that collapsed them into one "shoulder" column would compare different
    levels, so the driver must carry both and must not use the ambiguous word.
    """
    assert ebs.RISING_LIMB_P_F == pytest.approx(2e-3)
    assert ebs.TRANSITION_P_F == pytest.approx(0.5)
    anchors = ebs.anchor_indices(
        np.array([1.0, 2.0, 3.0]), np.array([2e-3, 0.5, 1.0]), hwl=1.0
    )
    assert "shoulder" not in anchors
    assert anchors["rising_limb"] != anchors["transition_midpoint"]


def test_lowest_reachable_falls_back_to_the_grid_base_when_nothing_fails() -> None:
    grid = np.array([40.0, 41.0])
    anchors = ebs.anchor_indices(grid, np.zeros(2), hwl=40.0)
    assert anchors["lowest_reachable"] == 0


# --------------------------------------------------------------------------- #
# Span / ratio semantics                                                       #
# --------------------------------------------------------------------------- #
def test_span_is_none_when_an_arm_drives_p_f_to_exactly_zero() -> None:
    """A bracket containing P_f = 0 spans an unbounded factor; say so.

    Reporting a finite number there would understate the knob. The ADR-0048
    k_aq field scenarios do exactly this at low stage.
    """
    assert ebs._span([0.0, 1e-3]) is None
    assert ebs._span([1e-4, 1e-3]) == pytest.approx(10.0)


def test_ratio_is_none_against_a_zero_baseline() -> None:
    assert ebs._ratio(1e-3, 0.0) is None
    assert ebs._ratio(2e-3, 1e-3) == pytest.approx(2.0)


def test_compact_rounds_floats_but_preserves_structure_and_non_finites() -> None:
    """The evidence file must stay inside the repo's 500 KB large-file hook."""
    out = ebs._compact({"a": 1.234567891234, "b": [2.5, None, True], "c": "x"})
    assert out["a"] == pytest.approx(1.23457, rel=1e-9)
    assert out["b"] == [2.5, None, True]
    assert out["c"] == "x"
    assert np.isnan(ebs._compact(float("nan")))
    assert ebs._compact(float("inf")) == float("inf")


def test_arm_shift_size_normalises_away_the_unequal_scenario_confound() -> None:
    """Raw departure factors are not comparable across sections.

    An ADR-0048 scenario is an absolute *target* mean, so k_aq moves by x0.17 at
    KP 57.4 but only x0.515 at KP 62.0. A section with a larger input shift shows
    a larger ratio departure for that reason alone, so the cross-section
    comparison must be made per decade of input movement.
    """
    arm = {"metadata": {"config": {"prior_mean_scenario": {"factors": {"k_aq": 0.1}}}}}
    out = ebs._arm_shift_size(arm, {"max_resolved_departure_factor": 100.0})
    assert out["scenario_parameter"] == "k_aq"
    assert out["input_decades_moved"] == pytest.approx(1.0)
    assert out["rho_decades_per_input_decade"] == pytest.approx(2.0)
    # An arm with no scenario block (m_p, z_toe, L) contributes nothing.
    assert ebs._arm_shift_size({"metadata": {"config": {}}}, {}) == {}


# --------------------------------------------------------------------------- #
# The L bracket arm selection                                                  #
# --------------------------------------------------------------------------- #
def test_seepage_length_arms_drop_the_no_op_arm_and_carry_the_withdrawn_value() -> None:
    """At KP 62.0 the DEM value *is* the adopted L, so only 47 m is informative.

    The evidence file still records ``csv_L_m = 47.0`` (it predates the ADR-0047
    adoption), so the driver must feed the arm-selection rule the config's live
    L instead -- otherwise it asks for a no-op 40 m arm alongside the withdrawn
    one and burns a sweep to measure a ratio of exactly 1.
    """
    _require_tracked(ebs.ADR0047_EVIDENCE)
    arms = ebs.seepage_length_arms("KP62.0", current_L=40.0)
    assert arms == [("withdrawn_1998", 47.0)]
    lengths = [length for _, length in arms]
    assert 40.0 not in lengths


def test_seepage_length_arms_at_a_held_section_drive_the_unadopted_dem_value() -> None:
    _require_tracked(ebs.ADR0047_EVIDENCE)
    arms = dict(ebs.seepage_length_arms("KP58.8", current_L=35.0))
    assert arms["dem_clean_median"] == pytest.approx(42.0)


# --------------------------------------------------------------------------- #
# The baseline gate                                                            #
# --------------------------------------------------------------------------- #
class _FakeResult:
    def __init__(self, static: np.ndarray, trans: np.ndarray) -> None:
        self.failure_matrix_stat = static
        self.failure_matrix_tran = trans


def test_gate_baseline_accepts_an_identical_pair() -> None:
    static = np.array([[True, False], [False, True]])
    trans = np.array([[False, False], [True, True]])
    persisted = {"failure_matrix_static": static, "failure_matrix_trans": trans}
    ebs.gate_baseline(_FakeResult(static.copy(), trans.copy()), persisted, "KP62.0")


def test_gate_baseline_refuses_a_single_flipped_cell() -> None:
    """Gates on the whole matrix, so a drift preserving P_f still fails."""
    static = np.array([[True, False], [False, True]])
    trans = np.array([[False, False], [True, True]])
    persisted = {"failure_matrix_static": static, "failure_matrix_trans": trans}
    drifted = static.copy()
    drifted[0, 0], drifted[0, 1] = False, True  # column means preserved
    with pytest.raises(AssertionError, match="Refusing to report"):
        ebs.gate_baseline(_FakeResult(drifted, trans.copy()), persisted, "KP62.0")


# --------------------------------------------------------------------------- #
# The cancellation statistic behaves as documented                             #
# --------------------------------------------------------------------------- #
def test_rho_is_one_and_unresolved_when_the_arm_equals_the_baseline() -> None:
    """A no-op arm must not read as a moved ratio."""
    rng = np.random.default_rng(0)
    static = rng.random(20000) < 0.30
    trans = rng.random(20000) < 0.10
    counts = ebs.pattern_counts(static, trans, static.copy(), trans.copy())
    out = ebs.ratio_of_ratios_ci(counts, seed=1)
    assert out["rho"] == pytest.approx(1.0)
    assert out["resolved"] is False


def test_rho_resolves_when_only_the_transient_branch_moves() -> None:
    """The statistic detects a genuine one-sided shift."""
    rng = np.random.default_rng(1)
    static = rng.random(50000) < 0.40
    trans = static & (rng.random(50000) < 0.50)
    arm_trans = static & (rng.random(50000) < 0.90)
    counts = ebs.pattern_counts(static, trans, static.copy(), arm_trans)
    out = ebs.ratio_of_ratios_ci(counts, seed=2)
    assert out["rho"] < 1.0
    assert out["resolved"] is True
    assert out["rho_lo"] < out["rho"] < out["rho_hi"]
