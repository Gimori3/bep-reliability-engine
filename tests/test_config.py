"""Tests for M1 config (``bep_reliability_engine.config``).

Four things are locked here: (1) a complete, representative config loads and
round-trips through YAML without loss; (2) every validator the spec §1 requires
rejects the corresponding bad input (the COV unit-error guard, positive seepage
length, strictly ascending conditioning grid, correlation in the open interval,
plus the lognormal-mean, canonical-family, unknown-key and lag-without-S_s
guards); (3) the handoff shapes match what the *built* modules consume — the
flat M8 geometry dict (ADR-0010, which excludes HWL) and the seven
``MarginalSpec`` in canonical M2 order; and (4) the per-KP HWL lookup from the
official 2019 design bank-height data (``bank_heights.load_hwl``, ADR-0018):
correct value for a known KP, correct river-file selection, strict rejection of
off-grid KPs, and clear errors for missing or non-numeric HWL cells.

Representative values are the Tokachi A_c/A_g stand-ins used across the suite
(``tests/test_sampling.py``, ``tests/test_hydraulics.py``): k_aq ~ 2e-3 m/s,
k_bl ~ 2e-6 m/s, d_70 ~ 2e-4 m, gamma_bl_sub ~ 6.9 kN/m^3, C_e ~ 0.014.
"""

import copy
import json
import math

import pytest
from pydantic import ValidationError

from bep_reliability_engine.bank_heights import load_hwl
from bep_reliability_engine.config import MAX_COV, Config, Geometry
from bep_reliability_engine.sampling import PARAM_NAMES, MarginalSpec


def _valid_config_dict() -> dict:
    """Return a fresh, complete, valid config mapping (deep-copied per call)."""
    return copy.deepcopy(
        {
            "geometry": {
                "L": 50.0,
                "z_toe": 0.0,
                "foreshore_width": 325.0,
                "D_fore": 2.0,
                "k_fore": 2.0e-6,
                "HWL": 40.0,
            },
            "priors": {
                "k_aq": {"family": "lognormal", "mean": 2.0e-3, "cov": 0.50},
                "d_70": {"family": "lognormal", "mean": 2.0e-4, "cov": 0.10},
                "D_aq": {"family": "lognormal", "mean": 20.0, "cov": 0.20},
                "D_bl": {"family": "lognormal", "mean": 3.0, "cov": 0.20},
                "k_bl": {"family": "lognormal", "mean": 2.0e-6, "cov": 0.50},
                "gamma_bl_sub": {"family": "lognormal", "mean": 6.9, "cov": 0.056},
                "C_e": {"family": "lognormal", "mean": 0.014, "cov": 0.50},
                "bounds": {"d_70": [50.0e-6, 1.0e-3]},
                "d70_interpretation": "matrix",
            },
            "correlation": {
                "rho_log_kaq_d70": 0.6,
                "coupling": "correlated",
            },
            "mc": {
                "n_samples": 100_000,
                "seed": 20260617,
                "conditioning_grid": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            },
            "timestepper": {},
            "output": {},
            "theta_repose_deg": 37.0,
            "relative_density_insitu": 0.725,
            "alpha_exponent": -1.0 / 3.0,
            "cross_section_id": "tokachi_kp58",
            "segment_id": "KP58_000",
            "scenario": "historical",
            "remediation_state": "none",
        }
    )


# ===========================================================================
# (1) A complete representative config loads cleanly + YAML round-trip
# ===========================================================================


def test_representative_config_loads_cleanly() -> None:
    """The full representative mapping validates and exposes its fields."""
    cfg = Config.model_validate(_valid_config_dict())

    assert cfg.geometry.L == 50.0
    assert cfg.mc.n_samples == 100_000
    assert cfg.mc.sampling_scheme == "latin_hypercube"  # default applied
    assert cfg.timestepper.integration_scheme == "forward_euler"  # default
    assert cfg.timestepper.aquifer_lag_active is False  # Phase 1 default
    assert cfg.output.store_trajectories is False  # §12 fm6 default
    assert cfg.scenario == "historical"
    assert cfg.correlation.coupling == "correlated"
    # d70_interpretation is owned by PriorSpecs (it labels the d_70 marginal),
    # not by CorrelationSpecs (it drives neither coupling nor the marginal).
    assert cfg.priors.d70_interpretation == "matrix"
    assert not hasattr(cfg.correlation, "d70_interpretation")


def test_yaml_round_trip_is_lossless(tmp_path) -> None:
    """to_yaml -> from_yaml reproduces an equal config and an equal hash."""
    cfg = Config.model_validate(_valid_config_dict())
    path = tmp_path / "tokachi_kp58.yaml"
    cfg.to_yaml(path)

    reloaded = Config.from_yaml(path)
    assert reloaded == cfg
    assert reloaded.to_metadata() == cfg.to_metadata()
    assert reloaded.config_hash() == cfg.config_hash()


def test_from_yaml_rejects_non_mapping_document(tmp_path) -> None:
    """A YAML document that is not a mapping fails before validation."""
    path = tmp_path / "bad.yaml"
    path.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Config.from_yaml(path)


def test_foreland_treatment_field_default_and_validation() -> None:
    """``foreland_treatment`` defaults to the ADR-0025 blanketed baseline.

    The open-entry end is a one-flag, on-demand sensitivity ('open_entry');
    anything else is rejected at load time, and the field is carried into the
    metadata snapshot so every result records which foreland physics ran.
    """
    cfg = Config.model_validate(_valid_config_dict())
    assert cfg.foreland_treatment == "blanketed_tanh"
    assert cfg.to_metadata()["foreland_treatment"] == "blanketed_tanh"

    data = _valid_config_dict()
    data["foreland_treatment"] = "open_entry"
    assert Config.model_validate(data).foreland_treatment == "open_entry"

    data["foreland_treatment"] = "radial_entry"  # not a defined treatment
    with pytest.raises(ValidationError):
        Config.model_validate(data)


# ===========================================================================
# (2) Handoff shapes match the built modules
# ===========================================================================


def test_geometry_as_evaluator_dict_matches_m8_keys() -> None:
    """Geometry emits exactly the flat dict M8 unpacks (ADR-0010).

    HWL is config-carried (spec §1) but is *not* part of the frozen five-key
    M8 contract, so it must be excluded here (ADR-0018).
    """
    cfg = Config.model_validate(_valid_config_dict())
    geom = cfg.geometry.as_evaluator_dict()

    assert set(geom) == {"L", "z_toe", "foreshore_width", "D_fore", "k_fore"}
    assert "HWL" not in geom
    assert geom["L"] == 50.0
    assert geom["foreshore_width"] == 325.0
    assert geom["D_fore"] == 2.0
    assert geom["k_fore"] == 2.0e-6


def test_to_marginal_specs_canonical_order_and_values() -> None:
    """PriorSpecs emits the seven MarginalSpec in canonical M2 order."""
    cfg = Config.model_validate(_valid_config_dict())
    specs = cfg.priors.to_marginal_specs()

    assert [s.name for s in specs] == PARAM_NAMES
    assert all(isinstance(s, MarginalSpec) for s in specs)

    by_name = {s.name: s for s in specs}
    assert by_name["k_aq"].family == "lognormal"
    assert by_name["k_aq"].mean == 2.0e-3
    assert by_name["k_aq"].cov == 0.50
    assert by_name["gamma_bl_sub"].family == "lognormal"
    assert by_name["gamma_bl_sub"].mean == 6.9
    assert by_name["gamma_bl_sub"].cov == 0.056
    assert by_name["C_e"].mean == 0.014


def test_theta_repose_converts_to_radians_at_boundary() -> None:
    """The one config-boundary unit conversion (degrees -> radians)."""
    cfg = Config.model_validate(_valid_config_dict())
    assert cfg.theta_repose_rad == pytest.approx(math.radians(37.0))


def test_to_metadata_is_json_serializable_and_hash_is_stable() -> None:
    """Metadata snapshot is pure JSON; the hash is deterministic and sensitive."""
    cfg = Config.model_validate(_valid_config_dict())
    meta = cfg.to_metadata()

    dumped = json.dumps(meta)  # raises if anything is non-serializable
    assert json.loads(dumped)["cross_section_id"] == "tokachi_kp58"
    assert "theta_repose_rad" not in meta  # derived value is not persisted

    # Same inputs -> same hash; a changed input -> different hash.
    again = Config.model_validate(_valid_config_dict())
    assert again.config_hash() == cfg.config_hash()
    other = _valid_config_dict()
    other["mc"]["seed"] = 1
    assert Config.model_validate(other).config_hash() != cfg.config_hash()


# ===========================================================================
# (3) Validation-failure cases (spec §1 validators)
# ===========================================================================


def test_cov_unit_error_is_rejected() -> None:
    """A COV of 50 (percentage for a fraction) is rejected (spec §1)."""
    bad = _valid_config_dict()
    bad["priors"]["k_aq"]["cov"] = 50.0
    with pytest.raises(ValidationError):
        Config.model_validate(bad)
    # The sane maximum is well below the unit-error magnitude.
    assert MAX_COV < 50.0


def test_non_positive_seepage_length_is_rejected() -> None:
    """L must be strictly positive (spec §1)."""
    for bad_L in (0.0, -50.0):
        bad = _valid_config_dict()
        bad["geometry"]["L"] = bad_L
        with pytest.raises(ValidationError):
            Config.model_validate(bad)


def test_non_ascending_conditioning_grid_is_rejected() -> None:
    """The conditioning grid must be strictly ascending and non-empty."""
    for bad_grid in ([3.0, 2.0, 1.0], [1.0, 2.0, 2.0], []):
        bad = _valid_config_dict()
        bad["mc"]["conditioning_grid"] = bad_grid
        with pytest.raises(ValidationError):
            Config.model_validate(bad)


def test_correlation_outside_open_interval_is_rejected() -> None:
    """rho must lie in the open interval (-1, 1)."""
    for bad_rho in (1.0, -1.0, 1.5, -2.0):
        bad = _valid_config_dict()
        bad["correlation"]["rho_log_kaq_d70"] = bad_rho
        with pytest.raises(ValidationError):
            Config.model_validate(bad)


def test_lognormal_with_non_positive_mean_is_rejected() -> None:
    """A lognormal marginal requires a positive mean."""
    bad = _valid_config_dict()
    bad["priors"]["k_aq"]["mean"] = -1.0e-3
    with pytest.raises(ValidationError):
        Config.model_validate(bad)


def test_wrong_canonical_family_is_rejected() -> None:
    """Families are fixed by spec §7; k_aq must stay lognormal."""
    bad = _valid_config_dict()
    bad["priors"]["k_aq"]["family"] = "normal"
    with pytest.raises(ValidationError):
        Config.model_validate(bad)


def test_unknown_key_is_rejected() -> None:
    """extra='forbid' turns a misspelled/unknown key into a load-time error."""
    top = _valid_config_dict()
    top["unexpected_field"] = 1
    with pytest.raises(ValidationError):
        Config.model_validate(top)

    nested = _valid_config_dict()
    nested["geometry"]["seepage_length"] = 50.0  # wrong name for L
    with pytest.raises(ValidationError):
        Config.model_validate(nested)


def test_d70_interpretation_under_correlation_is_rejected() -> None:
    """The label lives in PriorSpecs; supplying it under correlation is an error."""
    bad = _valid_config_dict()
    del bad["priors"]["d70_interpretation"]
    bad["correlation"]["d70_interpretation"] = "matrix"
    with pytest.raises(ValidationError):
        Config.model_validate(bad)


def test_lag_active_without_specific_storage_is_rejected() -> None:
    """Activating the lag requires S_s to derive tau_aq (ADR-0014)."""
    bad = _valid_config_dict()
    bad["timestepper"]["aquifer_lag_active"] = True
    # specific_storage_per_m intentionally left unset (None).
    with pytest.raises(ValidationError):
        Config.model_validate(bad)

    # Supplying S_s makes the same config valid.
    good = _valid_config_dict()
    good["timestepper"]["aquifer_lag_active"] = True
    good["timestepper"]["specific_storage_per_m"] = 5.0e-5
    cfg = Config.model_validate(good)
    assert cfg.timestepper.specific_storage_per_m == 5.0e-5


def test_bounds_with_low_not_below_high_is_rejected() -> None:
    """Per-parameter bounds require low < high and known keys (§12 fm2)."""
    bad_order = _valid_config_dict()
    bad_order["priors"]["bounds"] = {"d_70": [1.0e-3, 50.0e-6]}
    with pytest.raises(ValidationError):
        Config.model_validate(bad_order)

    bad_key = _valid_config_dict()
    bad_key["priors"]["bounds"] = {"not_a_param": [1.0, 2.0]}
    with pytest.raises(ValidationError):
        Config.model_validate(bad_key)


def test_frozen_config_is_immutable() -> None:
    """A loaded config cannot be mutated (one config = one run, spec §1)."""
    cfg = Config.model_validate(_valid_config_dict())
    with pytest.raises((ValidationError, TypeError)):
        cfg.theta_repose_deg = 30.0  # type: ignore[misc]


def test_geometry_constructs_directly() -> None:
    """Geometry is usable standalone (e.g. for targeted unit tests)."""
    geom = Geometry(
        L=30.0, z_toe=2.0, foreshore_width=0.0, D_fore=3.0, k_fore=1.0e-6, HWL=38.14
    )
    assert geom.HWL == 38.14
    assert geom.as_evaluator_dict()["z_toe"] == 2.0


# ===========================================================================
# (4) HWL: required Geometry field + the 2019 bank-height loader (ADR-0018)
# ===========================================================================


def test_geometry_hwl_is_required_and_positive() -> None:
    """HWL is a mandatory, strictly positive elevation [m MSL]."""
    missing = _valid_config_dict()
    del missing["geometry"]["HWL"]
    with pytest.raises(ValidationError):
        Config.model_validate(missing)

    for bad_hwl in (0.0, -38.14):
        bad = _valid_config_dict()
        bad["geometry"]["HWL"] = bad_hwl
        with pytest.raises(ValidationError):
            Config.model_validate(bad)


def test_load_hwl_reads_known_tokachi_values() -> None:
    """The loader returns the official 2019 HWL for known grid KPs [m MSL].

    KP 56.6 is the documented reference value; KP 57.4 is a study section;
    KP 62.0 is stored as the integer string ``"62"`` in the CSV, locking the
    float (not string) KP matching.
    """
    assert load_hwl("Tokachi", 56.6) == pytest.approx(38.14)
    assert load_hwl("Tokachi", 57.4) == pytest.approx(39.21)
    assert load_hwl("Tokachi", 62.0) == pytest.approx(46.39)


def test_load_hwl_selects_the_correct_river_file() -> None:
    """The same KP resolves against the requested river's file, not the other's."""
    tokachi = load_hwl("Tokachi", 10.0)
    satsunai = load_hwl("Satsunai", 10.0)
    assert tokachi == pytest.approx(8.64)
    assert satsunai == pytest.approx(59.08)
    assert tokachi != satsunai


def test_load_hwl_unknown_river_is_rejected() -> None:
    """A river without a 2019 bank-height file is a clear error."""
    with pytest.raises(ValueError, match="[Uu]nknown river"):
        load_hwl("Chiyoda", 10.0)


def test_load_hwl_off_grid_kp_is_a_strict_error() -> None:
    """An off-grid KP is rejected (strict match, ADR-0018), naming neighbours."""
    with pytest.raises(ValueError) as excinfo:
        load_hwl("Tokachi", 56.7)
    message = str(excinfo.value)
    assert "56.6" in message
    assert "56.8" in message


def test_load_hwl_missing_or_non_numeric_hwl_is_rejected(tmp_path) -> None:
    """Empty, non-numeric, or non-positive HWL cells raise clear errors."""
    header = "River,KP,HWL,DesignBankHeight_L,DesignBankHeight_R\n"
    (tmp_path / "BankHeight_TokachiRiv_2019.csv").write_text(
        header
        + "Tokachi,1.0,,3.0,3.0\n"
        + "Tokachi,1.2,abc,3.0,3.0\n"
        + "Tokachi,1.4,-5.0,3.0,3.0\n",
        encoding="utf-8",
    )
    for bad_kp in (1.0, 1.2, 1.4):
        with pytest.raises(ValueError, match="HWL"):
            load_hwl("Tokachi", bad_kp, data_dir=tmp_path)

    # A file missing the HWL column entirely is rejected up front.
    (tmp_path / "BankHeight_SatsunaiRiv_2019.csv").write_text(
        "River,KP,DesignBankHeight_L,DesignBankHeight_R\nSatsunai,2.8,34.93,34.93\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="HWL"):
        load_hwl("Satsunai", 2.8, data_dir=tmp_path)


# ---------------------------------------------------------------------------
# hydrograph_source block (ADR-0020)
# ---------------------------------------------------------------------------


def _valid_hydrograph_source() -> dict:
    """A valid ADR-0020 hydrograph_source block (the approved G1 event pair)."""
    return {
        "data_root": "data/raw",
        "river": "Tokachi",
        "kp": 57.4,
        "canonical_event_ids": ["HPB_m064_1987", "HPB_m067_1978"],
    }


def test_hydrograph_source_defaults_to_none() -> None:
    """The block is optional (ADR-0020): a config without it stays valid.

    Backwards compatibility for every pre-ADR-0020 config; the orchestrator
    refuses the real-hydrograph path when the block is None, so omission is
    safe, not silent.
    """
    config = Config.model_validate(_valid_config_dict())
    assert config.hydrograph_source is None


def test_hydrograph_source_loads_and_round_trips(tmp_path) -> None:
    """A config with the block loads, exposes its fields, and round-trips.

    The ordered-list semantics matter (ADR-0020: the FIRST entry is the shape
    the run uses), so order must survive the YAML round trip.
    """
    data = _valid_config_dict()
    data["hydrograph_source"] = _valid_hydrograph_source()
    config = Config.model_validate(data)

    src = config.hydrograph_source
    assert src is not None
    assert src.data_root == "data/raw"
    assert src.river == "Tokachi"
    assert src.kp == pytest.approx(57.4)
    assert list(src.canonical_event_ids) == ["HPB_m064_1987", "HPB_m067_1978"]

    path = tmp_path / "with_source.yaml"
    config.to_yaml(path)
    reloaded = Config.from_yaml(path)
    assert reloaded.config_hash() == config.config_hash()
    assert list(reloaded.hydrograph_source.canonical_event_ids) == list(
        src.canonical_event_ids
    )


def test_hydrograph_source_rejects_unknown_river() -> None:
    """river is a closed literal ('Tokachi' | 'Satsunai'); typos fail at load."""
    data = _valid_config_dict()
    data["hydrograph_source"] = {**_valid_hydrograph_source(), "river": "Tokachii"}
    with pytest.raises(ValidationError):
        Config.model_validate(data)


def test_hydrograph_source_rejects_empty_event_list() -> None:
    """canonical_event_ids must be non-empty (ADR-0020: it pins the G1 shape)."""
    data = _valid_config_dict()
    data["hydrograph_source"] = {
        **_valid_hydrograph_source(),
        "canonical_event_ids": [],
    }
    with pytest.raises(ValidationError):
        Config.model_validate(data)


def test_hydrograph_source_rejects_malformed_event_id() -> None:
    """Each canonical event ID must parse as a d4PDF member header.

    The load-time guard against a typo'd member ID failing deep inside a
    multi-hour run: 'HXB_m001_1951' (unknown experiment) and a free-text
    label are both rejected by the ADR-0019 header grammar.
    """
    for bad in ("HXB_m001_1951", "typhoon-2016"):
        data = _valid_config_dict()
        data["hydrograph_source"] = {
            **_valid_hydrograph_source(),
            "canonical_event_ids": ["HPB_m064_1987", bad],
        }
        with pytest.raises(ValidationError, match="canonical_event_ids"):
            Config.model_validate(data)


def test_hydrograph_source_rejects_non_positive_kp() -> None:
    """kp must be strictly positive."""
    data = _valid_config_dict()
    data["hydrograph_source"] = {**_valid_hydrograph_source(), "kp": 0.0}
    with pytest.raises(ValidationError):
        Config.model_validate(data)


# ============================================================================
# ADR-0037: length_effect block — validation and hash compatibility
# ============================================================================
def test_length_effect_defaults_off_and_n_eff_clamps() -> None:
    """Defaults are OFF/250 m/200 m; n_eff clamps at 1 from below (ADR-0037 §3)."""
    from bep_reliability_engine.config import LengthEffectSettings

    settings = LengthEffectSettings()
    assert settings.enabled is False
    assert settings.lambda_ac_m == 250.0
    assert settings.segment_length_m == 200.0
    assert settings.n_eff == 1.0  # 200/250 = 0.8 -> clamped
    assert LengthEffectSettings(lambda_ac_m=100.0).n_eff == 2.0
    assert LengthEffectSettings(lambda_ac_m=40.0).n_eff == 5.0
    with pytest.raises(ValidationError):
        LengthEffectSettings(lambda_ac_m=0.0)
    with pytest.raises(ValidationError):
        LengthEffectSettings(segment_length_m=-1.0)


def test_length_effect_none_is_dropped_from_metadata_and_hash_stable() -> None:
    """A config without the block hashes as if the field did not exist.

    Load-bearing compatibility (ADR-0037): pre-ADR-0037 result snapshots
    reconstruct to ``length_effect=None``; ``to_metadata`` must drop the key
    so their recomputed ``config_hash`` still matches what the persisted run
    recorded (the Phase 2 replay refuses hash drift).
    """
    config = Config.model_validate(_valid_config_dict())
    snapshot = config.to_metadata()
    assert "length_effect" not in snapshot
    # Round-trip through the snapshot (the Phase 2 replay path) is stable.
    rebuilt = Config.model_validate(snapshot)
    assert rebuilt.length_effect is None
    assert rebuilt.config_hash() == config.config_hash()


def test_length_effect_block_present_when_set() -> None:
    """A set block survives the snapshot round trip and changes the hash."""
    data = _valid_config_dict()
    data["length_effect"] = {
        "enabled": False,
        "lambda_ac_m": 250.0,
        "segment_length_m": 200.0,
    }
    config = Config.model_validate(data)
    snapshot = config.to_metadata()
    assert snapshot["length_effect"] == data["length_effect"]
    rebuilt = Config.model_validate(snapshot)
    assert rebuilt.config_hash() == config.config_hash()
    without = Config.model_validate(_valid_config_dict())
    assert config.config_hash() != without.config_hash()
