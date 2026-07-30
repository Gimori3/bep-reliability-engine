"""Tests for the ADR-0047 DEM cross-section extraction.

Pure-logic coverage runs everywhere and needs no DEM: the EPSG:2455
projection round-trip, the JPGIS(GML) tile parser (including the
``gml:startPoint`` padding path that the shipped tiles never exercise), and
the toe-picking rule against synthetic trapezoidal levees whose ``L`` is
known by construction. The tests that need the gitignored GSI drop skip on
fresh clones, mirroring the Phase 3 pattern.

Two guards here are structural rather than numerical:

* the study must never write ``data/processed/tokachi_bep_inputs.csv`` or
  ``configs/*.yaml`` -- adopting a DEM ``L`` is a separate authorised
  decision, because ``geometry.L`` sits inside ``Config.config_hash()`` and
  the Phase 2 replay refuses hash drift;
* the 高水敷幅 (high-water-bed width) must be reported *beside* ``L`` and
  never inside it -- folding the foreshore into ``L`` would double-count the
  foreland resistance already carried by ``lambda_out`` inside ``r_e``
  (ADR-0005/0006, provenance §3.1). This is the single most likely way to
  get the measurement wrong, so it is pinned.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
_SCRIPT = REPO / "scripts" / "dem_cross_section_study.py"


def _load_study_module():
    """Import the driver by path; ``scripts/`` is deliberately not a package."""
    spec = importlib.util.spec_from_file_location("dem_cross_section_study", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dem = _load_study_module()


def _require_tracked(path: Path) -> Path:
    """Assert a *tracked* artifact is still where the test expects it.

    Distinct from the ``requires_*`` marks below, which gate on genuinely
    optional gitignored data drops. A tracked evidence JSON that has moved or
    been deleted must fail loudly: skipping on it let a rename disable the guard
    while the suite stayed green (2026-07-31 hardening pass).
    """
    assert path.is_file(), (
        f"{path.relative_to(REPO).as_posix()} is a tracked evidence artifact "
        "this guard depends on, and it is missing. If it moved, update this "
        "test in the same change."
    )
    return path


requires_dem = pytest.mark.skipif(
    not dem.TILE_DIR.exists(),
    reason="GSI DEM5A tile drop absent (untracked data/raw/)",
)
requires_shapefile = pytest.mark.skipif(
    not dem.SECTIONS_SHP.exists(),
    reason="SECTIONS.shp absent (untracked data/raw/)",
)


# ============================================================================
# Projection
# ============================================================================
def test_plane_projection_round_trips_below_a_millimetre() -> None:
    """EPSG:2455 forward/inverse must not move a point by a measurable amount.

    The whole study is a length measurement on a 5 m raster; a projection
    error even at the centimetre level would be indistinguishable from a
    real geometry change over a 40 m footprint.
    """
    easting = np.array([-83414.0, -85418.0, -87756.0, -90560.0])
    northing = np.array([-118034.0, -117818.3, -117020.0, -117425.0])
    lat, lon = dem.plane_to_geographic(easting, northing)
    back_e, back_n = dem.geographic_to_plane(lat, lon)
    assert np.max(np.abs(back_e - easting)) < 1e-3
    assert np.max(np.abs(back_n - northing)) < 1e-3


def test_plane_projection_lands_in_the_expected_quadrant() -> None:
    """CS XIII origin is 44 N / 144.25 E, so this reach is south and west."""
    lat, lon = dem.plane_to_geographic(-85418.0, -117818.3)
    assert 42.9 < float(lat) < 43.0
    assert 143.1 < float(lon) < 143.3


# ============================================================================
# GML tile parsing
# ============================================================================
def _synthetic_tile(
    values: list[float], nx: int, ny: int, start: tuple[int, int]
) -> str:
    tuples = "\n".join(f"地表面,{v:.2f}" for v in values)
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Dataset>
 <DEM>
 <devDate><gml:timePosition>2025-06-20</gml:timePosition></devDate>
  <coverage>
   <gml:boundedBy>
    <gml:Envelope srsName="fguuid:jgd2024.bl">
     <gml:lowerCorner>42.916666667 143.125</gml:lowerCorner>
     <gml:upperCorner>42.925 143.1375</gml:upperCorner>
    </gml:Envelope>
   </gml:boundedBy>
   <gml:Grid>
    <gml:limits><gml:GridEnvelope>
     <gml:low>0 0</gml:low>
     <gml:high>{nx - 1} {ny - 1}</gml:high>
    </gml:GridEnvelope></gml:limits>
   </gml:Grid>
   <gml:rangeSet><gml:DataBlock>
    <gml:tupleList>
{tuples}
    </gml:tupleList>
   </gml:DataBlock></gml:rangeSet>
   <gml:coverageFunction><gml:GridFunction>
    <gml:sequenceRule order="+x-y">Linear</gml:sequenceRule>
    <gml:startPoint>{start[0]} {start[1]}</gml:startPoint>
   </gml:GridFunction></gml:coverageFunction>
  </coverage>
 </DEM>
</Dataset>
"""


def test_parse_dem_tile_reads_envelope_grid_and_row_order(tmp_path: Path) -> None:
    """Latitude comes first in the GML corners and row 0 is the northernmost."""
    path = tmp_path / "tile.xml"
    path.write_text(
        _synthetic_tile([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 3, 2, (0, 0)), "utf-8"
    )
    (lat_lo, lon_lo, lat_hi, lon_hi), grid, dev_date = dem.parse_dem_tile(path)
    assert (lat_lo, lat_hi) == (42.916666667, 42.925)
    assert (lon_lo, lon_hi) == (143.125, 143.1375)
    assert dev_date == "2025-06-20"
    assert grid.shape == (2, 3)
    # Row-major under "+x-y": the first three values are the northernmost row.
    assert np.array_equal(grid, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])


def test_parse_dem_tile_pads_a_non_zero_start_point(tmp_path: Path) -> None:
    """A tile that begins part-way must pad its head with nodata, not shift.

    None of the 100 shipped tiles exercises this branch, which is exactly why
    it is tested: a silently misaligned tile would translate part of the
    mosaic and corrupt every profile crossing it.
    """
    path = tmp_path / "tile.xml"
    path.write_text(_synthetic_tile([7.0, 8.0, 9.0, 10.0], 3, 2, (2, 0)), "utf-8")
    _envelope, grid, _dev = dem.parse_dem_tile(path)
    assert grid[0, 0] == dem.DEM_NODATA
    assert grid[0, 1] == dem.DEM_NODATA
    assert np.array_equal(grid[0, 2:], [7.0])
    assert np.array_equal(grid[1], [8.0, 9.0, 10.0])


def test_parse_dem_tile_refuses_an_overrunning_tuple_list(tmp_path: Path) -> None:
    path = tmp_path / "tile.xml"
    path.write_text(_synthetic_tile([1.0] * 8, 3, 2, (0, 0)), "utf-8")
    with pytest.raises(ValueError, match="overruns"):
        dem.parse_dem_tile(path)


# ============================================================================
# Toe picking against synthetic levees
# ============================================================================
#: Toe-pick bias induced by the finite forward-difference slope window: the
#: walk can declare a toe up to ``SLOPE_WINDOW_M * threshold / face_slope``
#: before the true break, once per side. For a 1:3 face at threshold 0.10 on
#: a 1 m grid that is 1 m per side, i.e. L short by 2 m. The direction is
#: conservative for piping (a shorter L raises P_f).
_EXPECTED_WINDOW_BIAS_M = 2.0


def _trapezoid_profile(
    *,
    crest_height_m: float = 5.0,
    crest_width_m: float = 8.0,
    side_slope: float = 3.0,
    berm_width_m: float = 0.0,
    berm_height_m: float = 0.0,
    channel_offset_m: float | None = None,
    channel_depth_m: float = 4.0,
    kp: float = 60.0,
) -> "dem.Profile":
    """A synthetic levee whose toe-to-toe length is known by construction.

    Ground is 0 m on both sides. The levee rises ``crest_height_m`` on
    ``1:side_slope`` faces about a flat crest. An optional landside berm of
    ``berm_width_m`` at ``berm_height_m`` sits against the landside toe. An
    optional low-water channel is cut riverward of ``channel_offset_m``.
    """
    offsets = np.arange(-dem.PROFILE_HALF_RIVER_M, dem.PROFILE_HALF_LAND_M + 1e-9, 1.0)
    elevation = np.zeros_like(offsets)
    face = crest_height_m * side_slope
    half = crest_width_m / 2.0

    on_crest = np.abs(offsets) <= half
    elevation[on_crest] = crest_height_m
    river_face = (offsets < -half) & (offsets >= -half - face)
    elevation[river_face] = crest_height_m + (offsets[river_face] + half) / side_slope
    land_face = (offsets > half) & (offsets <= half + face)
    elevation[land_face] = crest_height_m - (offsets[land_face] - half) / side_slope

    if berm_width_m > 0.0:
        # A real berm interrupts the landside face at its own level and then
        # resumes to ground, so the outer toe moves out by exactly the berm
        # width. Splicing a raised shelf on after the full face would instead
        # create an unphysical notch at the toe.
        shoulder = half + (crest_height_m - berm_height_m) * side_slope
        berm = (offsets > shoulder) & (offsets <= shoulder + berm_width_m)
        elevation[berm] = berm_height_m
        ramp = (offsets > shoulder + berm_width_m) & (
            offsets <= shoulder + berm_width_m + berm_height_m * side_slope
        )
        elevation[ramp] = (
            berm_height_m - (offsets[ramp] - (shoulder + berm_width_m)) / side_slope
        )
        elevation[offsets > shoulder + berm_width_m + berm_height_m * side_slope] = 0.0

    if channel_offset_m is not None:
        elevation[offsets <= channel_offset_m] = -channel_depth_m

    return dem.Profile(
        kp=kp,
        offsets_m=offsets,
        elevation_m=elevation,
        azimuth_deg=180.0,
        origin_xy=np.zeros(2),
        tangent_azimuth_deg=270.0,
    )


def test_pick_cross_section_recovers_a_synthetic_trapezoid() -> None:
    """The rule returns the constructed toe-to-toe length, less the window bias."""
    crest_width, height, slope = 8.0, 5.0, 3.0
    true_L = crest_width + 2.0 * height * slope  # 8 + 30 + 30 = 38 m
    picked = dem.pick_cross_section(
        _trapezoid_profile(
            crest_height_m=height, crest_width_m=crest_width, side_slope=slope
        )
    )
    assert picked.seepage_length_m == pytest.approx(true_L - _EXPECTED_WINDOW_BIAS_M)
    assert picked.crest_elev_m == pytest.approx(height)
    assert picked.river_toe_elev_m == pytest.approx(0.0, abs=0.5)
    assert picked.land_toe_elev_m == pytest.approx(0.0, abs=0.5)
    # No berm: the two landside conventions must agree exactly.
    assert picked.seepage_length_embankment_m == picked.seepage_length_m
    assert not picked.landside_bench_present
    assert not picked.landside_structure_present


def test_pick_cross_section_walks_past_a_landside_berm() -> None:
    """The primary convention includes a berm; the embankment one stops short.

    This is the KP 57.4 ``berm-only`` case: the 1998 chains measured a levee
    with no berm, and any later landside berm lengthens the confined path
    because it is fill resting on the same blanket.
    """
    plain = dem.pick_cross_section(_trapezoid_profile())
    bermed = dem.pick_cross_section(
        _trapezoid_profile(berm_width_m=15.0, berm_height_m=1.2)
    )
    # The berm moves the outer toe out by exactly its own width, by construction.
    assert bermed.seepage_length_m == pytest.approx(
        plain.seepage_length_m + 15.0, abs=2.0
    )
    # The embankment-only convention instead stops on the berm *shoulder*, so it
    # comes out shorter than the unbermed levee -- which is why the outer toe is
    # the primary convention rather than a refinement of this one.
    assert bermed.seepage_length_embankment_m < plain.seepage_length_m
    assert bermed.seepage_length_m > bermed.seepage_length_embankment_m + 15.0
    # A berm is part of this levee, not a separate structure.
    assert not bermed.landside_structure_present


def test_landside_bench_flag_fires_on_a_toe_ditch_below_a_shelf() -> None:
    """The bench flag marks the KP 62.0 shape: a toe ditch under a higher shelf.

    There the embankment toe is the ditch invert, so a reader must be told
    that level ground beyond it sits *above* the picked toe.
    """
    profile = _trapezoid_profile()
    offsets = profile.offsets_m
    elevation = profile.elevation_m.copy()
    toe = 4.0 + 15.0  # crest half-width + face
    ditch = (offsets > toe - 3.0) & (offsets <= toe + 3.0)
    elevation[ditch] = -0.8
    shelf = (offsets > toe + 3.0) & (offsets <= toe + 25.0)
    elevation[shelf] = 0.0
    picked = dem.pick_cross_section(
        dem.Profile(
            kp=profile.kp,
            offsets_m=offsets,
            elevation_m=elevation,
            azimuth_deg=profile.azimuth_deg,
            origin_xy=profile.origin_xy,
            tangent_azimuth_deg=profile.tangent_azimuth_deg,
        )
    )
    assert picked.land_toe_elev_m < 0.0
    assert picked.landside_bench_present


def test_a_separate_landside_embankment_is_flagged_not_absorbed() -> None:
    """A road or second-line levee standing clear of the toe must be flagged.

    This is the KP 57.4 situation: an adjacent road embankment makes the
    levee footprint unresolvable from elevation data alone, so the pick is
    marked contaminated rather than reported as a survey.
    """
    profile = _trapezoid_profile()
    offsets = profile.offsets_m
    elevation = profile.elevation_m.copy()
    road = (offsets > 60.0) & (offsets <= 90.0)
    elevation[road] = dem.STRUCTURE_HEIGHT_M + 1.0
    picked = dem.pick_cross_section(
        dem.Profile(
            kp=profile.kp,
            offsets_m=offsets,
            elevation_m=elevation,
            azimuth_deg=profile.azimuth_deg,
            origin_xy=profile.origin_xy,
            tangent_azimuth_deg=profile.tangent_azimuth_deg,
        )
    )
    assert picked.landside_structure_present
    # The separate embankment must not have been swallowed into L.
    assert picked.seepage_length_m == dem.pick_cross_section(profile).seepage_length_m


def test_toe_walk_is_capped_so_distant_fill_is_not_absorbed_into_L() -> None:
    """A berm wider than the cap falls back to the embankment toe, flagged."""
    far = dem.pick_cross_section(
        _trapezoid_profile(
            berm_width_m=dem.OUTER_TOE_MAX_BEYOND_M + 40.0, berm_height_m=1.2
        )
    )
    assert far.outer_toe_capped
    assert far.seepage_length_m == far.seepage_length_embankment_m


def test_slope_threshold_moves_the_pick_monotonically() -> None:
    """A looser threshold declares the toe earlier, so L shortens monotonically."""
    profile = _trapezoid_profile()
    lengths = [
        dem.pick_cross_section(profile, slope_threshold=t).seepage_length_m
        for t in dem.SLOPE_THRESHOLD_LADDER
    ]
    assert lengths == sorted(lengths, reverse=True)


def test_high_water_bed_width_is_reported_beside_L_and_never_inside_it() -> None:
    """The hard constraint: the foreshore must not enter the seepage length.

    ``r_e`` already carries the foreland through ``lambda_out``; adding the
    foreshore to ``L`` would double-count that resistance.
    """
    without = dem.pick_cross_section(_trapezoid_profile())
    with_bed = dem.pick_cross_section(_trapezoid_profile(channel_offset_m=-120.0))
    assert with_bed.seepage_length_m == without.seepage_length_m
    # The channel shoulder sits 120 m riverward; the toe is ~19 m riverward.
    assert with_bed.high_water_bed_width_m == pytest.approx(
        120.0 + with_bed.river_toe_offset_m, abs=2.0
    )
    assert with_bed.high_water_bed_width_m > 90.0


def test_an_oblique_profile_inflates_the_picked_length_by_one_over_cos() -> None:
    """Off-perpendicular sampling stretches a toe-to-toe length by 1/cos(theta).

    This is why the study scans azimuth and reports where L is minimised: at
    20 deg the inflation is already +6 %, which would read as a real widening.
    """
    base = _trapezoid_profile()
    for theta_deg in (10.0, 20.0, 30.0):
        stretch = 1.0 / math.cos(math.radians(theta_deg))
        oblique = dem.Profile(
            kp=base.kp,
            offsets_m=base.offsets_m,
            # Sampling the same terrain along an oblique line stretches the
            # apparent horizontal scale by exactly 1/cos(theta).
            elevation_m=np.interp(
                base.offsets_m / stretch, base.offsets_m, base.elevation_m
            ),
            azimuth_deg=base.azimuth_deg + theta_deg,
            origin_xy=base.origin_xy,
            tangent_azimuth_deg=base.tangent_azimuth_deg,
        )
        picked = dem.pick_cross_section(oblique)
        expected = dem.pick_cross_section(base).seepage_length_m * stretch
        assert picked.seepage_length_m == pytest.approx(expected, rel=0.06)


# ============================================================================
# Structural guards
# ============================================================================
def test_the_study_never_writes_the_committed_inputs_csv_or_configs() -> None:
    """Adopting a DEM L is a separate authorised decision, not a side effect.

    ``geometry.L`` is inside ``Config.config_hash()``; writing it here would
    invalidate all eight persisted Phase 1 sweeps, the Phase 2 posterior and
    the Phase 3 campaign through the replay hash gate.
    """
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
    assert 'data["geometry"]["L"] = float(seepage_length_m)' in source
    assert "Config.model_validate(data)" in source


def test_the_fragility_stage_gates_on_baseline_bit_identity() -> None:
    """A sensitivity against a drifted baseline is refused, not reported."""
    source = _SCRIPT.read_text(encoding="utf-8")
    assert "_assert_baseline_bit_identical" in source
    assert "Refusing to report a " in source
    assert "sensitivity against a drifted baseline" in source
    assert "P_f_static_raw" in source and "P_f_trans_raw" in source


# ============================================================================
# Evidence and DEM-dependent integration
# ============================================================================
@requires_shapefile
def test_build_alignment_is_contiguous_and_anchored() -> None:
    """The chained parts must join, and the KP anchor must span the reach."""
    alignment = dem.build_alignment()
    assert alignment.arc_length_m[-1] == pytest.approx(5501.0, abs=5.0)
    assert alignment.control_kp[0] == 57.3
    assert alignment.control_kp[-1] == 62.9
    # Monotone arc length and a strictly increasing KP map.
    assert np.all(np.diff(alignment.arc_length_m) > 0)
    assert np.all(np.diff(alignment.control_s_m) > 0)
    for kp in (57.4, 58.8, 60.0, 62.0):
        s_m = alignment.kp_to_s(kp)
        assert 0.0 < s_m < alignment.arc_length_m[-1]
        assert float(alignment.s_to_kp(s_m)) == pytest.approx(kp)


@requires_dem
@requires_shapefile
def test_measured_sections_reproduce_the_committed_evidence() -> None:
    """Re-measuring must reproduce the numbers the ADR quotes."""
    # The evidence JSON is TRACKED, so absence means moved/renamed/deleted, not
    # "not generated yet" -- assert rather than skip (2026-07-31 hardening pass).
    # The outer requires_dem/requires_shapefile marks still cover the genuinely
    # optional part: the gitignored data/raw/ tile drop.
    path = _require_tracked(
        REPO / "docs" / "decisions" / "adr0047-dem-seepage-length.json"
    )
    evidence = json.loads(path.read_text(encoding="utf-8"))
    mosaic = dem.load_dem_mosaic()
    alignment = dem.build_alignment()
    recorded = {m["section"]: m for m in evidence["measurements"]}
    for label in recorded:
        fresh = dem.measure_section(mosaic, alignment, label, verbose=False)
        assert fresh["window"]["L_median_m"] == pytest.approx(
            recorded[label]["window"]["L_median_m"]
        )
        assert fresh["nominal_station"]["L_m"] == pytest.approx(
            recorded[label]["nominal_station"]["L_m"]
        )


def test_evidence_json_carries_the_vintage_and_the_no_change_statement() -> None:
    """The record must say which surface it measured and that nothing changed."""
    path = _require_tracked(
        REPO / "docs" / "decisions" / "adr0047-dem-seepage-length.json"
    )
    evidence = json.loads(path.read_text(encoding="utf-8"))
    assert dem.DEM_DEV_DATE in evidence["dem_source"]
    assert evidence["csv_geometry_vintage"] == "1998"
    assert "No input value is changed" in evidence["note"]
    assert evidence["datum_check"]["passed"] is True


# --------------------------------------------------------------------------- #
# The ratio-of-ratios estimator (ADR-0047 section 4.5)                         #
# --------------------------------------------------------------------------- #
def _paired_indicators(n: int = 60_000, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    """A static/transient indicator pair with the transient nested in the static.

    Mirrors the production situation: the transient failure set is a subset of
    the static one at the same realizations (the shared-sample contract).
    """
    rng = np.random.default_rng(seed)
    static = rng.random(n) < 0.40
    transient = static & (rng.random(n) < 0.25)
    return static, transient


def test_ratio_of_ratios_is_exactly_one_when_the_arms_are_identical() -> None:
    """The null case must return 1.0 exactly, not merely close to it.

    This is what makes the estimator's pairing auditable: because one row
    resample feeds all four means, an unchanged arm cannot manufacture spread.
    """
    static, transient = _paired_indicators()
    counts = dem._pattern_counts(static, transient, static, transient)
    result = dem.ratio_of_ratios_ci(counts)
    assert result["rho"] == 1.0
    assert result["rho_lo"] == 1.0 and result["rho_hi"] == 1.0
    assert result["resolved"] is False


def test_ratio_of_ratios_does_not_resolve_a_common_mode_change() -> None:
    """A change that scales BOTH branches must come out unresolved.

    This is the ADR-0048 k_aq situation -- an epistemic bracket that dominates
    absolute P_f but cancels in the static-vs-transient ratio. The estimator
    must be able to return that verdict, or its finding for L would be an
    artefact of the method rather than of the input.
    """
    static, transient = _paired_indicators()
    rng = np.random.default_rng(11)
    keep = rng.random(static.size) < 0.75
    counts = dem._pattern_counts(static, transient, static & keep, transient & keep)
    result = dem.ratio_of_ratios_ci(counts)
    assert result["rho"] == pytest.approx(1.0, abs=0.02)
    assert result["resolved"] is False


def test_ratio_of_ratios_resolves_a_transient_only_change() -> None:
    """A change that moves only the transient branch must resolve.

    This is the L situation: L enters the transient limit state through
    Z = L - l_e and the rate denominator on top of the shared H_c, so it is
    not a common-mode shift.
    """
    static, transient = _paired_indicators()
    rng = np.random.default_rng(13)
    keep = rng.random(static.size) < 0.60
    counts = dem._pattern_counts(static, transient, static, transient & keep)
    result = dem.ratio_of_ratios_ci(counts)
    assert result["rho"] > 1.2
    assert result["resolved"] is True
    assert result["rho_lo"] > 1.0


def test_ratio_evidence_reports_every_level_with_an_interval() -> None:
    """Every reported level must carry a resolvable/unresolvable verdict."""
    path = _require_tracked(
        REPO / "docs" / "decisions" / "adr0047-dem-seepage-length-ratio.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    for section in payload["ratio"]:
        # The baseline must have matched the persisted sweep on the whole
        # failure matrices, not merely on the column means.
        assert section["baseline_failure_matrices_bit_identical_to_production"]
        for arm in section["arms"].values():
            assert arm["levels"], "an arm reported no evaluable levels"
            for level in arm["levels"]:
                assert level["rho_lo"] <= level["rho"] <= level["rho_hi"]
                assert level["resolved"] == (
                    level["rho_lo"] > 1.0 or level["rho_hi"] < 1.0
                )
