"""Tests for the Phase 3 ``system_integration`` package (ADR-0038).

Pure-logic coverage runs everywhere: seam validation (surface CSV contract,
section table), composition algebra, the ADR-0024 curve-evaluation policy,
hazard statistics on synthetic events, annualization math. File-seam tests
against the committed rating grid and the gitignored d4PDF workbooks skip on
fresh clones, mirroring the Phase 1/2 pattern.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bep_reliability_engine.fragility import LognormFragility
from system_integration.annualize import annualize, stratified_annual_p_f
from system_integration.bep_input import FragilityCurve, load_bep_curve
from system_integration.composition import MechanismCurve, compose
from system_integration.hazard import EventSummary, NodeHazard
from system_integration.segments import (
    OYO_BEP_SECTIONS,
    Segment,
    SegmentRegistry,
    build_registry,
    load_section_table,
)
from system_integration.surface_curves import load_surface_curves, synthetic_stub

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO / "data" / "raw"

requires_rating_csvs = pytest.mark.skipif(
    not (DATA_ROOT / "rating_curves" / "HQrelation_TokachiRiv_2017.csv").exists(),
    reason="rating-curve CSVs absent (untracked data drop)",
)


# ============================================================================
# Composition algebra
# ============================================================================
def test_compose_series_system_algebra() -> None:
    """P_sys = 1 - prod(1 - P_i), decomposition retained, sources stamped."""
    grid = np.array([1.0, 2.0, 3.0])
    a = MechanismCurve("bep", np.array([0.0, 0.1, 0.5]), "phase2_posterior")
    b = MechanismCurve("overflow", np.array([0.0, 0.2, 0.4]), "uemura_csv")
    system = compose(grid, [a, b])
    np.testing.assert_allclose(system.p_sys, 1.0 - (1.0 - a.p_f) * (1.0 - b.p_f))
    assert system.mechanisms == ("bep", "overflow")
    assert system.sources == {"bep": "phase2_posterior", "overflow": "uemura_csv"}
    # One mechanism only: the system curve IS that mechanism (visible absence).
    solo = compose(grid, [a])
    np.testing.assert_allclose(solo.p_sys, a.p_f)
    assert solo.mechanisms == ("bep",)


def test_compose_dominance_shares_sum_to_one_where_loaded() -> None:
    grid = np.array([1.0, 2.0])
    system = compose(
        grid,
        [
            MechanismCurve("bep", np.array([0.0, 0.3]), "s"),
            MechanismCurve("overflow", np.array([0.0, 0.1]), "s"),
        ],
    )
    shares = system.dominance_share("bep") + system.dominance_share("overflow")
    np.testing.assert_allclose(shares, [0.0, 1.0])  # unloaded stage -> all zero


def test_compose_validation() -> None:
    grid = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="at least one"):
        compose(grid, [])
    with pytest.raises(ValueError, match="duplicate"):
        compose(
            grid,
            [
                MechanismCurve("bep", np.zeros(2), "s"),
                MechanismCurve("bep", np.zeros(2), "s"),
            ],
        )
    with pytest.raises(ValueError, match="outside"):
        compose(grid, [MechanismCurve("bep", np.array([0.0, 1.5]), "s")])
    with pytest.raises(ValueError, match="shape"):
        compose(grid, [MechanismCurve("bep", np.zeros(3), "s")])


# ============================================================================
# Surface-curve seam (ADR-0038 decision 5)
# ============================================================================
def test_synthetic_stub_is_schema_exact_and_stamped() -> None:
    stub = synthetic_stub()
    assert stub.source == "synthetic_stub"
    # 4 KPs x 2 mechanisms x 2 scenarios
    assert len(stub.curves) == 16
    for curve in stub.curves:
        assert np.all(np.diff(curve.stage_m_msl) > 0)
        assert np.all(np.diff(curve.p_f) >= 0)
        assert np.all((curve.p_f >= 0) & (curve.p_f <= 1))
    # The +4K stub curve dominates the historical one (shifted lower).
    hist = stub.lookup(
        river="Tokachi", kp=58.8, mechanism="overflow", scenario="historical"
    )
    plus4k = stub.lookup(river="Tokachi", kp=58.8, mechanism="overflow", scenario="+4K")
    assert hist is not None and plus4k is not None
    assert np.all(plus4k.p_f >= hist.p_f)


def _write_surface_csv(path: Path, rows: list[str]) -> Path:
    header = "river,bank,kp,mechanism,scenario,stage_m_msl,p_f"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def test_load_surface_curves_round_trip(tmp_path: Path) -> None:
    path = _write_surface_csv(
        tmp_path / "uemura.csv",
        [
            "Tokachi,right,58.8,overflow,historical,40.0,0.0",
            "Tokachi,right,58.8,overflow,historical,42.0,0.5",
            "Tokachi,right,58.8,overflow,plus4K,40.0,0.1",
            "Tokachi,right,58.8,overflow,plus4K,42.0,0.7",
        ],
    )
    curves = load_surface_curves(path)
    assert curves.source == "uemura_csv"
    assert len(curves.curves) == 2
    plus4k = curves.lookup(
        river="Tokachi", kp=58.8, mechanism="overflow", scenario="+4K"
    )
    assert plus4k is not None  # the plus4K alias normalized to +4K
    np.testing.assert_allclose(plus4k.evaluate(np.array([41.0])), [0.4])
    # Clamped outside the sampled range.
    np.testing.assert_allclose(plus4k.evaluate(np.array([30.0, 50.0])), [0.1, 0.7])


@pytest.mark.parametrize(
    ("bad_rows", "match"),
    [
        (["Rhine,right,58.8,overflow,historical,40.0,0.0"], "river/bank"),
        (["Tokachi,right,58.8,landslide,historical,40.0,0.0"], "mechanism"),
        (["Tokachi,right,58.8,overflow,rcp85,40.0,0.0"], "scenario"),
        (["Tokachi,right,58.8,overflow,historical,40.0,1.4"], "outside"),
        (
            [
                "Tokachi,right,58.8,overflow,historical,42.0,0.5",
                "Tokachi,right,58.8,overflow,historical,40.0,0.0",
            ],
            "strictly increasing",
        ),
        (
            [
                "Tokachi,right,58.8,overflow,historical,40.0,0.5",
                "Tokachi,right,58.8,overflow,historical,42.0,0.1",
            ],
            "non-decreasing|decreases",
        ),
        (["Tokachi,right,58.8,overflow,historical,40.0,0.0"], "at least two"),
    ],
)
def test_load_surface_curves_validation(
    tmp_path: Path, bad_rows: list[str], match: str
) -> None:
    path = _write_surface_csv(tmp_path / "bad.csv", bad_rows)
    with pytest.raises(ValueError, match=match):
        load_surface_curves(path)


# ============================================================================
# BEP curve evaluation policy (ADR-0024 / ADR-0038 decision 4)
# ============================================================================
def _raw_curve(
    grid: np.ndarray,
    p_raw: np.ndarray,
    fit: LognormFragility | None = None,
    deliverable: bool = False,
) -> FragilityCurve:
    return FragilityCurve(
        grid_m_msl=grid,
        p_raw=p_raw,
        ci_lower=np.zeros_like(p_raw),
        ci_upper=np.minimum(p_raw + 0.01, 1.0),
        fit=fit,
        fit_is_deliverable=deliverable,
        branch="transient",
        source="phase1_prior",
        source_path="synthetic",
    )


def test_raw_curve_probit_interpolation_hits_grid_points() -> None:
    grid = np.array([40.0, 41.0, 42.0])
    p_raw = np.array([0.01, 0.10, 0.50])
    curve = _raw_curve(grid, p_raw)
    p_f, clamped = curve.evaluate(grid)
    np.testing.assert_allclose(p_f, p_raw, rtol=1e-12)
    assert not clamped.any()


def test_raw_curve_never_extrapolates_above_grid() -> None:
    grid = np.array([40.0, 41.0])
    curve = _raw_curve(grid, np.array([0.1, 0.2]))
    p_f, clamped = curve.evaluate(np.array([41.5, 45.0]))
    np.testing.assert_allclose(p_f, [0.2, 0.2])  # held, not extrapolated
    assert clamped.tolist() == [True, True]


def test_raw_curve_leading_zeros_stay_exact_zeros() -> None:
    grid = np.array([40.0, 41.0, 42.0, 43.0])
    curve = _raw_curve(grid, np.array([0.0, 0.0, 0.01, 0.10]))
    p_f, _ = curve.evaluate(np.array([39.0, 40.5, 41.0, 41.5]))
    assert p_f[0] == 0.0
    assert p_f[1] == 0.0
    assert p_f[2] == 0.0  # the last leading-zero grid level itself
    assert 0.0 < p_f[3] < 0.01  # between zero level and first failures


def test_fitted_deliverable_curve_uses_the_fit() -> None:
    grid = np.array([40.0, 41.0, 42.0])
    fit = LognormFragility(mu=0.5, sigma=0.4, datum_m=38.5)
    curve = _raw_curve(grid, np.array([0.2, 0.5, 0.9]), fit=fit, deliverable=True)
    stages = np.array([40.5, 43.0])  # incl. above-grid: fits extrapolate
    p_f, clamped = curve.evaluate(stages)
    np.testing.assert_allclose(p_f, fit.probability_of_failure(stages))
    assert not clamped.any()


def test_load_bep_curve_from_assembled_result(tmp_path: Path) -> None:
    """Round trip through a real persisted FragilityResult artifact."""
    from bep_reliability_engine.fragility import assemble_fragility

    rng = np.random.default_rng(42)
    n, grid = 200, np.array([40.0, 41.0, 42.0, 43.0])
    theta = rng.random((n, 7))
    # Monotone synthetic failure matrices.
    z = rng.random(n)
    thresholds = np.array([0.95, 0.8, 0.5, 0.2])
    fm_tran = z[:, None] > thresholds[None, :]
    fm_stat = z[:, None] > (thresholds[None, :] - 0.05)
    result = assemble_fragility(
        theta,
        [f"p{i}" for i in range(7)],
        grid,
        fm_stat,
        fm_tran,
        {"config": {}},
        n_bootstrap=50,
        confidence=0.95,
        seed=1,
        datum_m=39.0,
    )
    path = tmp_path / "synthetic_result.h5"
    result.save(path)

    curve = load_bep_curve(path, branch="transient")
    assert curve.source == "phase1_prior"
    np.testing.assert_allclose(curve.p_raw, result.P_f_trans_raw)
    assert curve.fit_is_deliverable == (
        result.P_f_trans_fit is not None and float(result.P_f_trans_raw.max()) >= 0.5
    )
    with pytest.raises(ValueError, match="branch"):
        load_bep_curve(path, branch="upliftt")


# ============================================================================
# Hazard statistics + annualization (synthetic events; no workbooks needed)
# ============================================================================
def _synthetic_hazard(peaks: list[float], scenario: str = "historical") -> NodeHazard:
    events = tuple(
        EventSummary(
            event_id=f"HPB_m{i:03d}_1951",
            peak_stage_m_msl=p,
            hours_above_datum=float(10 * i),
            t_rise_h=12.0,
            plateau_h=6.0,
            n_peaks_above_datum=1 + (i % 2),
        )
        for i, p in enumerate(peaks)
    )
    return NodeHazard(
        river="Tokachi",
        kp=58.8,
        scenario=scenario,
        n_years=len(events),
        events=events,
        datum_m_msl=38.5,
        provenance={"band_workbook": "synthetic", "rating_csv": "synthetic"},
    )


def test_annual_exceedance_and_return_periods() -> None:
    hazard = _synthetic_hazard([40.0, 41.0, 42.0, 43.0])
    np.testing.assert_allclose(
        hazard.annual_exceedance(np.array([39.0, 41.5, 43.5])), [1.0, 0.5, 0.0]
    )
    periods, stages = hazard.return_period_stages()
    np.testing.assert_allclose(stages, [43.0, 42.0, 41.0, 40.0])
    np.testing.assert_allclose(periods, [5.0, 2.5, 5.0 / 3.0, 1.25])


def test_annualize_is_the_ensemble_mean_of_the_curve_at_peaks() -> None:
    grid = np.array([40.0, 41.0, 42.0, 43.0])
    system = compose(
        grid,
        [
            MechanismCurve("bep", np.array([0.0, 0.1, 0.4, 0.8]), "s"),
            MechanismCurve("overflow", np.array([0.0, 0.0, 0.2, 0.9]), "s"),
        ],
    )
    hazard = _synthetic_hazard([40.0, 41.0, 42.0, 43.0])
    annual = annualize(system, hazard)
    expected_sys = float(np.mean(system.p_sys))  # peaks == grid exactly
    assert annual.p_f_annual_system == pytest.approx(expected_sys)
    assert annual.p_f_annual_per_mechanism["bep"] == pytest.approx(
        float(np.mean([0.0, 0.1, 0.4, 0.8]))
    )
    assert 0.0 <= annual.dominance_share("bep") <= 1.0


def test_stratified_annual_p_f_partitions_the_ensemble() -> None:
    grid = np.array([40.0, 43.0])
    system = compose(grid, [MechanismCurve("bep", np.array([0.0, 0.6]), "s")])
    hazard = _synthetic_hazard([40.0, 41.0, 42.0, 43.0])
    p_in, p_out, n_in, n_out = stratified_annual_p_f(
        system, hazard, lambda e: e.hours_above_datum > 15.0
    )
    assert n_in + n_out == 4
    total = (p_in * n_in + p_out * n_out) / 4.0
    assert total == pytest.approx(annualize(system, hazard).p_f_annual_system)


def test_hazard_cache_round_trip(tmp_path: Path) -> None:
    from system_integration.hazard import _read_cache, _write_cache

    hazard = _synthetic_hazard([40.0, 42.0])
    cache = tmp_path / "hazard_cache.csv"
    _write_cache(cache, hazard)
    reloaded = _read_cache(cache, river="Tokachi", kp=58.8, scenario="historical")
    assert reloaded.n_years == 2
    np.testing.assert_allclose(reloaded.peak_stages(), hazard.peak_stages())
    assert reloaded.datum_m_msl == 38.5
    with pytest.raises(ValueError, match="does not match"):
        _read_cache(cache, river="Tokachi", kp=60.0, scenario="historical")


# ============================================================================
# Segment registry + section-table seam
# ============================================================================
def _toy_registry() -> SegmentRegistry:
    segments = tuple(
        Segment(river="Tokachi", bank="right", kp=kp, bep_source_kp=source)
        for kp, source in [(58.6, None), (58.8, 58.8), (59.0, None)]
    )
    return SegmentRegistry(segments=segments)


def test_section_table_annotates_and_validates(tmp_path: Path) -> None:
    registry = _toy_registry()
    table = tmp_path / "sections.csv"
    table.write_text(
        "river,bank,kp_from,kp_to,section_id\n" "Tokachi,right,58.5,59.1,Tokachi-3\n",
        encoding="utf-8",
    )
    annotated = load_section_table(table, registry)
    assert all(s.section_id == "Tokachi-3" for s in annotated.segments)

    overlapping = tmp_path / "overlap.csv"
    overlapping.write_text(
        "river,bank,kp_from,kp_to,section_id\n"
        "Tokachi,right,58.5,59.0,A\n"
        "Tokachi,right,58.8,59.2,B\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="overlap"):
        load_section_table(overlapping, registry)

    gappy = tmp_path / "gappy.csv"
    gappy.write_text(
        "river,bank,kp_from,kp_to,section_id\nTokachi,right,58.5,58.9,A\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not covered"):
        load_section_table(gappy, registry)


@requires_rating_csvs
def test_build_registry_on_the_committed_grid() -> None:
    registry = build_registry(DATA_ROOT)
    assert registry.bep_source_policy == "exact"
    # Every OYO section is present and is its own BEP source.
    for river, _bank, kp in OYO_BEP_SECTIONS:
        segment = registry.segment_at(river, kp)
        assert segment.bep_source_kp == kp
    # Exact policy: only the OYO sections carry BEP curves.
    assert len(registry.bep_segments()) == len(OYO_BEP_SECTIONS)
    # Both study reaches present on the 0.2 km grid.
    rivers = {s.river for s in registry.segments}
    assert rivers == {"Tokachi", "Satsunai"}
    nearest = build_registry(DATA_ROOT, bep_source_policy="nearest")
    assert all(
        s.bep_source_kp is not None for s in nearest.segments if s.river == "Tokachi"
    )
    with pytest.raises(ValueError, match="policy"):
        build_registry(DATA_ROOT, bep_source_policy="interpolate")
