"""Pin the exact climate decomposition and the composition identities.

These are arithmetic properties of the committed Phase 3 record, not reruns of
the study. Each one contradicts a statement the thesis carried before
2026-09-17, so a regression here would let the old statement become true again
and go unnoticed:

* the total climate ratio was described as the PRODUCT of a long-duration
  frequency factor and a within-stratum severity factor. That product is the
  change in the long stratum's CONTRIBUTION, one addend of the exact mixture;
* "frequency exceeds severity" was quoted as a statement about the total. It
  holds inside the long stratum and does not hold over both strata;
* mechanism shares normalise by the SUM of the marginals, not by the union.

Nothing here touches a default, a config, a prior or a persisted result. The
driver is ``scripts/climate_attribution_decomposition.py`` and the evidence is
``docs/decisions/climate-attribution-and-composition-study.{md,json}``.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "docs" / "decisions" / "climate-attribution-and-composition-study.json"
ATTRIBUTION = (
    REPO / "results" / "system_integration" / "phase3" / "rq4_attribution.json"
)

#: Identities over a finite partition; only summation order may differ.
EXACT = 1e-12

SECTIONS = ("KP 57.4", "KP 58.8", "KP 60.0", "KP 62.0")
#: The two sections whose long-duration stratum clears the pre-registered
#: occupancy floor in BOTH scenarios, and therefore the only two whose
#: attribution the thesis may quote with an interval.
RESOLVED = ("KP 58.8", "KP 60.0")


@pytest.fixture(scope="module")
def record() -> dict:
    if not RECORD.exists():  # pragma: no cover - the record is committed
        pytest.skip(f"{RECORD} not present")
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def duration(record: dict) -> dict:
    return {name: record["two_stratum"][name]["duration"] for name in SECTIONS}


class TestPartitionIsExact:
    """The stratified table and the annual number are one identity apart."""

    def test_every_gate_passed(self, record: dict) -> None:
        for name, gate in record["gates"].items():
            assert gate["passed"], name

    def test_partition_reconstructs_the_published_annual_probability(
        self, duration: dict
    ) -> None:
        for name, block in duration.items():
            for scenario in ("historical", "+4K"):
                cell = block[scenario]
                recon = (
                    cell["w_inside"] * cell["p_f_inside"]
                    + (1.0 - cell["w_inside"]) * cell["p_f_outside"]
                )
                assert recon == pytest.approx(
                    cell["p_annual_published"], rel=EXACT
                ), name

    def test_stratified_fields_are_the_published_ones(self, duration: dict) -> None:
        published = json.loads(ATTRIBUTION.read_text(encoding="utf-8"))
        keys = {"KP 57.4": 57.4, "KP 58.8": 58.8, "KP 60.0": 60.0, "KP 62.0": 62.0}
        for name, block in duration.items():
            entry = published[f"Tokachi_KP{keys[name]:g}"]
            for scenario in ("historical", "+4K"):
                cell, pub = block[scenario], entry[scenario]
                assert cell["w_inside"] == pub["frac_years_gt24h"]
                assert cell["p_f_inside"] == pub["p_f_long_loading"]
                assert cell["p_f_outside"] == pub["p_f_short_loading"]
                assert cell["n_inside"] == pub["n_long"]


class TestTheTotalRatioIsAMixtureAndNotTheProduct:
    """The correction itself, stated as two assertions that cannot both hold."""

    def test_mixture_of_the_two_contribution_ratios_is_the_total(
        self, duration: dict
    ) -> None:
        for name, block in duration.items():
            s = block["historical_share_inside"]
            mixture = (
                s * block["ratio_inside_contribution"]
                + (1.0 - s) * block["ratio_outside_contribution"]
            )
            assert mixture == pytest.approx(block["ratio_total"], rel=EXACT), name

    def test_product_is_the_inside_contribution_ratio(self, duration: dict) -> None:
        for name, block in duration.items():
            product = block["frequency_factor_inside"] * block["severity_factor_inside"]
            assert product == pytest.approx(
                block["ratio_inside_contribution"], rel=EXACT
            ), name

    def test_the_product_is_not_the_total_ratio_where_the_stratum_is_a_minority(
        self, duration: dict
    ) -> None:
        """KP 57.4 carries 13 per cent of its historical probability in the long
        stratum, and there the product overshoots the total by a factor above 2.
        This is the measured defect; if it ever disappears, the correction in
        Chapter 7 has lost its subject."""
        worst = max(block["product_over_total_ratio"] for block in duration.values())
        assert worst > 2.0
        assert duration["KP 57.4"]["product_over_total_ratio"] == pytest.approx(
            2.26, abs=0.01
        )

    def test_the_error_of_the_product_has_its_exact_closed_form(
        self, duration: dict
    ) -> None:
        """``R_in - R = (1 - s_in)(R_in - R_out)`` exactly.

        This is why the product is a usable approximation at KP 58.8 and
        KP 60.0 and not at KP 57.4: the error is the weight deficit times the
        gap between the two strata's contribution ratios. It also explains
        KP 62.0, where the share is only 0.59 and the product is still within
        5 per cent, because there the two contribution ratios nearly coincide.
        A share test alone would get that section wrong."""
        for name, block in duration.items():
            error = block["ratio_inside_contribution"] - block["ratio_total"]
            closed = (1.0 - block["historical_share_inside"]) * (
                block["ratio_inside_contribution"] - block["ratio_outside_contribution"]
            )
            assert error == pytest.approx(closed, rel=EXACT, abs=1e-12), name


class TestFrequencyDoesNotDominateOverBothStrata:
    """The claim that survives, and the claim that does not."""

    def test_attribution_terms_sum_to_the_log_ratio(self, duration: dict) -> None:
        for name, block in duration.items():
            a = block["attribution_log"]
            for freq, sev in (
                ("frequency_first", "severity_last"),
                ("frequency_last", "severity_first"),
                ("frequency_shapley", "severity_shapley"),
            ):
                assert a[freq] + a[sev] == pytest.approx(
                    a["log_total"], rel=EXACT
                ), f"{name} {freq}"

    def test_frequency_exceeds_severity_inside_the_long_stratum(
        self, duration: dict
    ) -> None:
        for name, block in duration.items():
            assert (
                block["frequency_factor_inside"] > block["severity_factor_inside"]
            ), name
            assert block["frequency_share_of_log_inside"] > 0.5, name

    def test_frequency_is_never_a_majority_over_both_strata(
        self, duration: dict
    ) -> None:
        for name, block in duration.items():
            a = block["attribution_log"]
            for key in (
                "frequency_share_first",
                "frequency_share_last",
                "frequency_share_shapley",
            ):
                assert a[key] <= 0.53, f"{name} {key}"
            assert block["attribution_additive"]["frequency_share"] <= 0.53, name

    def test_the_resolved_pair_carries_intervals_that_straddle_a_half(
        self, duration: dict
    ) -> None:
        for name in RESOLVED:
            interval = duration[name]["intervals"]["frequency_share_shapley"]
            assert interval["ci_low"] < 0.5 < interval["ci_high"], name

    def test_intervals_are_withheld_below_the_occupancy_floor(
        self, duration: dict
    ) -> None:
        for name in SECTIONS:
            block = duration[name]
            if name in RESOLVED:
                assert block["both_strata_clear_floor"]
                assert "withheld" not in block["intervals"]
            else:
                assert not block["both_strata_clear_floor"]
                assert "withheld" in block["intervals"]


class TestMechanismSharesNormaliseBySumNotUnion:
    """What the published shares are shares of, and how far that is from the union."""

    def test_sum_of_marginals_is_at_least_the_union(self, record: dict) -> None:
        for name, scenarios in record["composition_overlap"].items():
            for scenario, cell in scenarios.items():
                assert cell["sum_over_union"] >= 1.0 - EXACT, f"{name} {scenario}"
                assert cell["union_over_largest"] >= 1.0 - EXACT, f"{name} {scenario}"

    def test_shares_sum_to_one_and_union_normalised_marginals_do_not(
        self, record: dict
    ) -> None:
        for name, scenarios in record["composition_overlap"].items():
            for scenario, cell in scenarios.items():
                assert sum(cell["sum_normalised_shares"].values()) == pytest.approx(
                    1.0, rel=EXACT
                ), f"{name} {scenario}"
                assert sum(
                    cell["union_normalised_marginals"].values()
                ) == pytest.approx(cell["sum_over_union"], rel=EXACT)

    def test_the_overlap_is_largest_at_the_kp62_warming_tie(self, record: dict) -> None:
        """The tie cell is the one where the denominator choice matters most,
        and the tie itself is invariant to it because both mechanisms share the
        denominator."""
        cells = {
            (name, scenario): cell["sum_over_union"]
            for name, scenarios in record["composition_overlap"].items()
            for scenario, cell in scenarios.items()
        }
        worst = max(cells, key=cells.__getitem__)
        assert worst == ("KP 62.0", "+4K")
        assert cells[worst] == pytest.approx(1.314, abs=0.002)
        cell = record["composition_overlap"]["KP 62.0"]["+4K"]
        assert cell["sum_normalised_shares"]["bep"] == pytest.approx(0.500, abs=0.002)
        assert cell["union_normalised_marginals"]["bep"] == pytest.approx(
            0.658, abs=0.002
        )

    def test_frechet_bracket_contains_the_independent_union(self, record: dict) -> None:
        """Conditional dependence alone, with the marginals held fixed, can only
        move the union inside this bracket. The independence assumption is
        therefore not non-conservative by construction: it sits strictly
        inside, above the positively dependent end."""
        for name, scenarios in record["composition_overlap"].items():
            for scenario, cell in scenarios.items():
                lo, hi = cell["frechet_lower"], cell["frechet_upper"]
                assert lo - EXACT <= cell["p_annual_union"] <= hi + EXACT


class TestHistoricalNonBreachCheck:
    """The sixty-year consistency arithmetic, and the two silent assumptions."""

    def test_series_union_and_sixty_year_figures(self, record: dict) -> None:
        c = record["historical_consistency"]
        values = list(c["per_section_annual_bep"].values())
        series = 1.0 - math.prod(1.0 - p for p in values)
        assert c["reach_annual_series_union"] == pytest.approx(series, rel=EXACT)
        assert c["expected_failures"] == pytest.approx(60.0 * series, rel=EXACT)
        assert c["p_no_failure"] == pytest.approx((1.0 - series) ** 60, rel=EXACT)
        assert round(c["reach_annual_series_union"], 4) == 0.0108
        assert c["expected_failures"] == pytest.approx(0.645, abs=0.001)
        assert c["p_no_failure"] == pytest.approx(0.523, abs=0.001)

    def test_exact_one_sided_bound_is_below_the_rule_of_three(
        self, record: dict
    ) -> None:
        """The thesis printed 5.0e-2, which is 3/n. The exact one-sided 95 per
        cent limit for zero successes in sixty trials is 1 - 0.05^(1/60)."""
        c = record["historical_consistency"]
        assert c["exclusion_upper_95_exact"] == pytest.approx(
            1.0 - 0.05 ** (1.0 / 60.0), rel=EXACT
        )
        assert c["exclusion_upper_95_exact"] == pytest.approx(0.0487, abs=0.0001)
        assert c["exclusion_upper_95_exact"] < c["exclusion_upper_95_rule_of_three"]
        assert c["exact_upper_over_reported"] == pytest.approx(4.53, abs=0.01)

    def test_independence_over_states_the_reach_probability(self, record: dict) -> None:
        c = record["historical_consistency"]
        assert c["reach_annual_series_union"] > c["reach_annual_largest"]
        assert c["union_over_largest"] == pytest.approx(1.46, abs=0.01)

    def test_both_assumptions_are_recorded_with_their_directions(
        self, record: dict
    ) -> None:
        assumptions = record["historical_consistency"]["assumptions"]
        assert set(assumptions) == {
            "inter_section_independence",
            "persistent_epistemic_uncertainty",
            "not_calibration",
        }
        assert "Jensen" in assumptions["persistent_epistemic_uncertainty"]
