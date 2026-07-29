"""ADR-0048 prior-mean epistemic scenario: gating, application, hash preservation.

Locks the four ADR-0048 guarantees:

1. **Baseline bit-identity when off.** A config without the
   ``prior_mean_scenario`` block, and one carrying it ``enabled=False``,
   produce bit-identical theta matrices and failure matrices; the None case is
   dropped from ``to_metadata()`` so pre-ADR-0048 config hashes are preserved
   (the Phase 2 replay hash gate).
2. **Means only.** When enabled, the named parameters' prior *means* move by
   exactly their factor and nothing else does — families, CoVs, the untouched
   parameters' means, bounds, coupling and seed are all unchanged.
3. **Unmissable in the output.** An enabled scenario stamps
   ``metadata['prior_mean_scenario']`` with the label, the factors, and both
   the baseline and effective means; a baseline run carries no such key.
4. **One shared definition.** ``Config.effective_marginal_specs`` is what both
   the Phase 1 orchestrator and the Phase 2 replay sample, so a scenario run
   regenerates its own population rather than the baseline one.
"""

from __future__ import annotations

import numpy as np
import pytest
from pydantic import ValidationError

from bep_reliability_engine.config import Config, PriorMeanScenario
from bep_reliability_engine.run import run_fragility_analysis
from bep_reliability_engine.sampling import PARAM_NAMES, sample_theta

from .phase2_helpers import stub_config

# The ADR-0048 primary instantiation: the k_aq field-test lower bound. The
# stub prior mean is 1.0e-4 m/s; 0.03 lands it at 3.0e-6, inside the OYO
# field-test range (2.23e-6 .. 1.24e-4 m/s) recorded in provenance §3.6.
K_AQ_FIELD_FACTOR = 0.03


def _run(config: Config, out):
    """Run the stub sweep into a tmp path (never the shared results/ dir)."""
    return run_fragility_analysis(
        config, n_jobs=1, progress=False, output_path=out, overwrite=True
    )


def _scenario_config(**factors: float) -> Config:
    """A stub config carrying an enabled ADR-0048 scenario."""
    return stub_config(
        prior_mean_scenario={
            "enabled": True,
            "label": "test_scenario",
            "factors": dict(factors),
        }
    )


# --- (1) baseline bit-identity and hash preservation -----------------------


def test_absent_block_is_bit_identical_and_hash_preserving():
    """No block at all == the pre-ADR-0048 config, byte-for-byte."""
    baseline = stub_config()
    assert baseline.prior_mean_scenario is None
    # The None field never reaches the snapshot, so the hash a pre-ADR-0048
    # run recorded still reconstructs under this code (Phase 2 replay gate).
    assert "prior_mean_scenario" not in baseline.to_metadata()

    specs = baseline.effective_marginal_specs()
    assert specs == baseline.priors.to_marginal_specs()


def test_disabled_block_leaves_the_draw_bit_identical():
    """enabled=False must not perturb the theta matrix, even with factors set."""
    baseline = stub_config()
    disabled = stub_config(
        prior_mean_scenario={
            "enabled": False,
            "label": "off",
            "factors": {"k_aq": K_AQ_FIELD_FACTOR},
        }
    )
    assert disabled.effective_marginal_specs() == baseline.effective_marginal_specs()

    draw_kwargs = dict(
        seed=baseline.mc.seed,
        rho_log_kaq_d70=baseline.correlation.rho_log_kaq_d70,
        d70_interpretation=baseline.priors.d70_interpretation,
        n_samples=baseline.mc.n_samples,
        coupling=baseline.correlation.coupling,
        bounds=baseline.priors.bounds,
    )
    a = sample_theta(baseline.effective_marginal_specs(), **draw_kwargs)
    b = sample_theta(disabled.effective_marginal_specs(), **draw_kwargs)
    assert np.array_equal(a.theta_matrix, b.theta_matrix)


def test_disabled_block_gives_bit_identical_failure_matrices(tmp_path):
    """End-to-end: a disabled scenario reproduces the baseline run exactly."""
    baseline = _run(stub_config(), tmp_path / "baseline.h5")
    disabled = _run(
        stub_config(
            prior_mean_scenario={
                "enabled": False,
                "label": "off",
                "factors": {"k_aq": K_AQ_FIELD_FACTOR},
            }
        ),
        tmp_path / "disabled.h5",
    )
    assert np.array_equal(baseline.theta_matrix, disabled.theta_matrix)
    assert np.array_equal(baseline.failure_matrix_stat, disabled.failure_matrix_stat)
    assert np.array_equal(baseline.failure_matrix_tran, disabled.failure_matrix_tran)


# --- (2) means only --------------------------------------------------------


def test_enabled_scenario_scales_only_the_named_mean():
    """The factor hits exactly one mean; family, cov and siblings are untouched."""
    baseline = stub_config()
    scenario = _scenario_config(k_aq=K_AQ_FIELD_FACTOR)

    base_by_name = {s.name: s for s in baseline.priors.to_marginal_specs()}
    eff_by_name = {s.name: s for s in scenario.effective_marginal_specs()}

    assert [s.name for s in scenario.effective_marginal_specs()] == PARAM_NAMES

    assert eff_by_name["k_aq"].mean == pytest.approx(
        base_by_name["k_aq"].mean * K_AQ_FIELD_FACTOR
    )
    assert eff_by_name["k_aq"].cov == base_by_name["k_aq"].cov
    assert eff_by_name["k_aq"].family == base_by_name["k_aq"].family

    for name in PARAM_NAMES:
        if name == "k_aq":
            continue
        assert eff_by_name[name] == base_by_name[name], name


def test_multi_parameter_scenario_applies_each_factor():
    """The secondary ADR-0048 case moves gamma_bl_sub alongside k_aq."""
    baseline = stub_config()
    scenario = _scenario_config(k_aq=K_AQ_FIELD_FACTOR, gamma_bl_sub=6.0 / 6.9)

    base_by_name = {s.name: s for s in baseline.priors.to_marginal_specs()}
    eff_by_name = {s.name: s for s in scenario.effective_marginal_specs()}

    assert eff_by_name["k_aq"].mean == pytest.approx(
        base_by_name["k_aq"].mean * K_AQ_FIELD_FACTOR
    )
    assert eff_by_name["gamma_bl_sub"].mean == pytest.approx(6.0)
    assert eff_by_name["D_bl"] == base_by_name["D_bl"]


def test_enabled_scenario_actually_moves_the_population():
    """Sanity: the scaled draw is a genuinely different, lower k_aq population."""
    baseline = stub_config()
    scenario = _scenario_config(k_aq=K_AQ_FIELD_FACTOR)
    draw_kwargs = dict(
        seed=baseline.mc.seed,
        rho_log_kaq_d70=baseline.correlation.rho_log_kaq_d70,
        d70_interpretation=baseline.priors.d70_interpretation,
        n_samples=baseline.mc.n_samples,
        coupling=baseline.correlation.coupling,
        bounds=baseline.priors.bounds,
    )
    base = sample_theta(baseline.effective_marginal_specs(), **draw_kwargs)
    scen = sample_theta(scenario.effective_marginal_specs(), **draw_kwargs)

    i = PARAM_NAMES.index("k_aq")
    ratio = scen.theta_matrix[:, i] / base.theta_matrix[:, i]
    # A pure mean rescale of a lognormal is an exact multiplicative shift of
    # every realization under the same LHS design.
    assert np.allclose(ratio, K_AQ_FIELD_FACTOR)
    # Columns other than k_aq are untouched.
    for j, name in enumerate(PARAM_NAMES):
        if name == "k_aq":
            continue
        assert np.array_equal(scen.theta_matrix[:, j], base.theta_matrix[:, j]), name


# --- (3) unmissable in the output ------------------------------------------


def test_metadata_stamp_present_only_for_a_scenario_run(tmp_path):
    """A baseline run carries no key; a scenario run records label and means."""
    baseline = _run(stub_config(), tmp_path / "baseline.h5")
    assert "prior_mean_scenario" not in baseline.metadata

    scenario = _run(_scenario_config(k_aq=K_AQ_FIELD_FACTOR), tmp_path / "scenario.h5")
    block = scenario.metadata["prior_mean_scenario"]
    assert block["enabled"] is True
    assert block["label"] == "test_scenario"
    assert block["factors"] == {"k_aq": K_AQ_FIELD_FACTOR}
    assert block["baseline_means"]["k_aq"] == pytest.approx(1.0e-4)
    assert block["effective_means"]["k_aq"] == pytest.approx(1.0e-4 * K_AQ_FIELD_FACTOR)
    # Untouched parameters report the same value on both sides.
    assert block["baseline_means"]["D_bl"] == block["effective_means"]["D_bl"]


def test_scenario_changes_the_config_hash():
    """A scenario run must not collide with the baseline hash it deviates from."""
    assert (
        stub_config().config_hash()
        != _scenario_config(k_aq=K_AQ_FIELD_FACTOR).config_hash()
    )


# --- (4) validation --------------------------------------------------------


def test_unknown_parameter_name_is_rejected():
    with pytest.raises(ValidationError, match="are not parameters"):
        PriorMeanScenario(enabled=True, label="x", factors={"k_aquifer": 0.5})


def test_non_positive_factor_is_rejected():
    with pytest.raises(ValidationError, match="must all be > 0"):
        PriorMeanScenario(enabled=True, label="x", factors={"k_aq": 0.0})


def test_enabled_with_no_factors_is_rejected():
    """An enabled-but-empty scenario is a silent no-op; refuse it."""
    with pytest.raises(ValidationError, match="silent no-op"):
        PriorMeanScenario(enabled=True, label="x", factors={})


def test_disabled_with_no_factors_is_allowed():
    """The off case stays constructible with no factors (the generated default)."""
    assert PriorMeanScenario().enabled is False
