"""Unit tests for the Phase 3 campaign additions (ADR-0042/0043).

Covers the ADR-0043 section max rule, the ``allow_gaps`` section-table
mode, and the multi-node reach-hazard loader's equivalence with the
single-node loader on a synthetic ensemble (no workbook I/O).
"""

from __future__ import annotations

import numpy as np
import pytest

import system_integration.hazard as hazard_mod
from system_integration.composition import (
    MechanismCurve,
    compose,
    max_within_section,
    max_within_section_rated,
)
from system_integration.hazard import load_node_hazard, load_reach_hazard
from system_integration.segments import (
    Segment,
    SegmentRegistry,
    load_section_table,
)


def _frag(stages, p):
    return compose(
        np.asarray(stages, dtype=float),
        [MechanismCurve(mechanism="bep", p_f=np.asarray(p, dtype=float), source="t")],
    )


class TestMaxWithinSection:
    def test_pointwise_max_and_argmax(self):
        a = _frag([0.0, 1.0, 2.0], [0.0, 0.5, 0.6])
        b = _frag([0.0, 1.0, 2.0], [0.1, 0.2, 0.9])
        grid, p, argmax_kp = max_within_section([(10.0, a), (12.0, b)])
        assert np.array_equal(grid, [0.0, 1.0, 2.0])
        assert np.allclose(p, [0.1, 0.5, 0.9])
        assert np.array_equal(argmax_kp, [12.0, 10.0, 12.0])

    def test_union_grid_interpolation(self):
        a = _frag([0.0, 2.0], [0.0, 1.0])
        b = _frag([1.0, 3.0], [0.8, 0.8])
        grid, p, _ = max_within_section([(1.0, a), (2.0, b)])
        assert np.array_equal(grid, [0.0, 1.0, 2.0, 3.0])
        # At h=1: max(0.5 interp, 0.8) = 0.8; at h=3: max(1.0 clamp, 0.8).
        assert np.allclose(p, [0.8, 0.8, 1.0, 1.0])

    def test_single_member_identity(self):
        a = _frag([0.0, 1.0], [0.2, 0.4])
        grid, p, argmax_kp = max_within_section([(5.0, a)])
        assert np.allclose(p, [0.2, 0.4])
        assert np.array_equal(argmax_kp, [5.0, 5.0])

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="at least one member"):
            max_within_section([])


class TestMaxWithinSectionRated:
    """The discharge-aligned Uemura Eq. 14 rule (ADR-0043 decision 3)."""

    def test_identical_ratings_reduce_to_plain_max(self):
        rating = (100.0, -30.0)
        a = _frag([31.0, 33.0], [0.0, 0.6])
        b = _frag([31.0, 33.0], [0.2, 0.4])
        grid = np.array([31.0, 32.0, 33.0])
        p, argmax_kp = max_within_section_rated(
            [(1.0, a, rating), (2.0, b, rating)], rating, grid
        )
        assert np.allclose(p, [0.2, 0.3, 0.6])
        assert np.array_equal(argmax_kp, [2.0, 1.0, 1.0])

    def test_datum_offset_is_respected(self):
        """A member 2 m lower in datum contributes at ITS OWN local stage:
        with identical curves-relative-to-datum, the rated max equals the
        representative curve — never the naive absolute-stage max."""
        rep_rating = (100.0, -30.0)  # h = sqrt(q/100) + 30
        low_rating = (100.0, -28.0)  # identical shape, 2 m lower datum
        rep = _frag([31.0, 33.0], [0.0, 0.5])
        low = _frag([29.0, 31.0], [0.0, 0.5])  # same curve, own datum
        grid = np.array([31.0, 32.0, 33.0])
        p, _ = max_within_section_rated(
            [(10.0, rep, rep_rating), (9.0, low, low_rating)], rep_rating, grid
        )
        # Same discharge -> same relative stage -> same P at both members.
        assert np.allclose(p, [0.0, 0.25, 0.5])
        # The naive absolute-stage max would wrongly read the low member's
        # saturated tail at the representative stages.
        _, p_naive, _ = max_within_section([(10.0, rep), (9.0, low)])
        assert p_naive[-1] == 0.5  # naive: low member clamped at 0.5 at 33 m

    def test_below_rating_datum_stage_maps_to_zero_discharge(self):
        rating = (100.0, -30.0)
        a = _frag([28.0, 33.0], [0.1, 0.9])
        grid = np.array([29.0, 30.0])  # h + b <= 0 -> q = 0
        p, _ = max_within_section_rated([(1.0, a, rating)], rating, grid)
        # q=0 -> local stage = 30.0 -> interpolated on [28, 33]
        expected = np.interp(30.0, [28.0, 33.0], [0.1, 0.9])
        assert np.allclose(p, [expected, expected])

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="at least one member"):
            max_within_section_rated([], (100.0, -30.0), np.array([31.0]))


class TestAllowGaps:
    def _registry(self):
        segments = tuple(
            Segment(river="Satsunai", bank="left", kp=round(3.2 + 0.2 * i, 1))
            for i in range(5)  # 3.2 .. 4.0
        )
        return SegmentRegistry(segments=segments)

    def test_gap_raises_by_default(self, tmp_path):
        table = tmp_path / "sections.csv"
        table.write_text(
            "river,bank,kp_from,kp_to,section_id\nSatsunai,left,3.2,3.6,S1\n"
        )
        with pytest.raises(ValueError, match="not covered"):
            load_section_table(table, self._registry())

    def test_allow_gaps_leaves_none(self, tmp_path):
        table = tmp_path / "sections.csv"
        table.write_text(
            "river,bank,kp_from,kp_to,section_id\nSatsunai,left,3.2,3.6,S1\n"
        )
        registry = load_section_table(table, self._registry(), allow_gaps=True)
        ids = [s.section_id for s in registry.segments]
        assert ids == ["S1", "S1", "S1", None, None]

    def test_overlap_still_raises_with_gaps(self, tmp_path):
        table = tmp_path / "sections.csv"
        table.write_text(
            "river,bank,kp_from,kp_to,section_id\n"
            "Satsunai,left,3.2,3.6,S1\nSatsunai,left,3.4,4.0,S2\n"
        )
        with pytest.raises(ValueError, match="overlap"):
            load_section_table(table, self._registry(), allow_gaps=True)


class TestReachHazardEquivalence:
    """load_reach_hazard == load_node_hazard on a synthetic ensemble."""

    @pytest.fixture()
    def synthetic(self, monkeypatch, tmp_path):
        time_hours = np.arange(1.0, 25.0)  # 24 h records
        members = {
            "HPB_m001_1951": 100.0
            + 900.0 * np.exp(-0.5 * ((time_hours - 12.0) / 3.0) ** 2),
            "HPB_m002_1952": 100.0
            + 400.0 * np.exp(-0.5 * ((time_hours - 8.0) / 2.0) ** 2),
        }
        coeffs = {57.4: (150.0, -30.0), 58.8: (140.0, -31.0)}

        workbook = tmp_path / "HPB_synthetic.xlsx"
        workbook.write_bytes(b"placeholder")

        import bep_reliability_engine.hydrographs as hg

        monkeypatch.setattr(
            hazard_mod,
            "resolve_band_workbook",
            lambda *a, **k: workbook,
        )
        monkeypatch.setattr(hazard_mod, "load_rating_coefficients", lambda path: coeffs)
        monkeypatch.setattr(
            hg, "read_discharge_ensemble", lambda path: (time_hours, members)
        )
        # The single-node path composes through load_hydrograph_ensemble.
        real_load = hg.load_hydrograph_ensemble

        def fake_load(path, *, kp, rating_coefficients):
            records = {}
            for header, q in members.items():
                info = hg.parse_member_header(header)
                a_kp, b_kp = rating_coefficients[kp]
                records[header] = hg.build_hydrograph_record(
                    time_hours,
                    q,
                    a_kp=a_kp,
                    b_kp=b_kp,
                    scenario=str(info["scenario"]),
                    event_id=header,
                    provenance={**info, "kp": kp},
                )
            return records

        monkeypatch.setattr(hazard_mod, "load_hydrograph_ensemble", fake_load)
        assert real_load is not None
        return coeffs

    def test_equivalence_and_cache(self, synthetic, tmp_path):
        nodes = [("Tokachi", 57.4, 33.0), ("Tokachi", 58.8, 34.0)]
        reach = load_reach_hazard(
            "data/raw",
            nodes=nodes,
            scenario="historical",
            cache_dir=tmp_path / "cache",
        )
        assert set(reach) == {("Tokachi", 57.4), ("Tokachi", 58.8)}
        for river, kp, datum in nodes:
            single = load_node_hazard(
                "data/raw",
                river=river,
                kp=kp,
                scenario="historical",
                datum_m_msl=datum,
            )
            multi = reach[(river, round(kp, 3))]
            assert multi.n_years == single.n_years == 2
            assert np.array_equal(multi.peak_stages(), single.peak_stages())
            for e_multi, e_single in zip(multi.events, single.events):
                assert e_multi == e_single

        # Second call is served from cache and identical.
        reach2 = load_reach_hazard(
            "data/raw",
            nodes=nodes,
            scenario="historical",
            cache_dir=tmp_path / "cache",
        )
        for key, hz in reach.items():
            assert reach2[key].events == hz.events
            assert reach2[key].provenance["band_workbook"] != ""
