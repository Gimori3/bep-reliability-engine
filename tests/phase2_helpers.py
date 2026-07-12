"""Shared fixtures-as-helpers for the Phase 2 test modules.

The Phase 2 unit and integration tests need a genuine Phase 1
``FragilityResult`` exercising the true interface (mission requirement: no
hand-mocked handoff fixtures for the end-to-end path). The cheapest genuine
run is the synthetic-stub hydrograph path (no external data), which the
Phase 1 suite itself uses: N a few hundred, a short conditioning grid,
seconds of runtime. The result is generated once per test session and
persisted into a session-scoped temporary directory.

Synthetic observed-event records (a negligible flat record and a stressing
long-plateau record) complement it for the acceptance-logic and
laminar-signature tests; both are duck-type-valid M3 records built through
the concrete ``HydrographRecord`` type.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from bep_reliability_engine.config import Config
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.run import run_fragility_analysis

STUB_SEED = 20260712
STUB_N = 300
# Grid tuned like tests/test_run.py: both branches interior for the stub
# two-peak event with the test priors below.
STUB_GRID = [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 10.0, 11.0]
STUB_DT_S = 7200.0
Z_TOE = 2.0


def stub_config(**overrides) -> Config:
    """A small, fast, fittable stub-path Config (test_run.py pattern)."""
    data = {
        "cross_section_id": "phase2_test_xs",
        "segment_id": "P2TEST.000",
        "scenario": "historical",
        "remediation_state": "none",
        "geometry": {
            "L": 30.0,
            "z_toe": Z_TOE,
            "foreshore_width": 0.0,
            "D_fore": 3.0,
            "k_fore": 1.0e-6,
            "HWL": 16.0,
        },
        "priors": {
            "k_aq": {"family": "lognormal", "mean": 1.0e-4, "cov": 0.50},
            "d_70": {"family": "lognormal", "mean": 2.0e-4, "cov": 0.10},
            "D_aq": {"family": "lognormal", "mean": 3.0, "cov": 0.20},
            "D_bl": {"family": "lognormal", "mean": 3.0, "cov": 0.20},
            "k_bl": {"family": "lognormal", "mean": 1.0e-6, "cov": 0.50},
            "gamma_bl_sub": {"family": "lognormal", "mean": 6.9, "cov": 0.056},
            "C_e": {"family": "lognormal", "mean": 0.20, "cov": 0.50},
            "bounds": {"d_70": [50.0e-6, 1.0e-3]},
            "d70_interpretation": "matrix",
        },
        "correlation": {"rho_log_kaq_d70": 0.0, "coupling": "two_population"},
        "mc": {
            "n_samples": STUB_N,
            "seed": STUB_SEED,
            "conditioning_grid": [float(x) for x in STUB_GRID],
            "sampling_scheme": "latin_hypercube",
        },
        "timestepper": {
            "integration_scheme": "forward_euler",
            "target_dt_seconds": STUB_DT_S,
            "convergence_test": False,
            "convergence_threshold": 0.01,
            "aquifer_lag_active": False,
            "specific_storage_per_m": None,
        },
        "output": {
            "store_trajectories": False,
            "persistence_format": "hdf5",
            "results_dir": "results",
        },
        "theta_repose_deg": 37.0,
        "relative_density_insitu": 0.725,
        "alpha_exponent": -1.0 / 3.0,
        "seepage_length_cov": 0.2,
    }
    data.update(overrides)
    return Config.model_validate(data)


def generate_stub_phase1(tmp_dir: Path, **config_overrides) -> Path:
    """Run the genuine Phase 1 engine on the stub path; return the HDF5 path.

    The stochastic seepage length is ON (cov 0.2 in :func:`stub_config`)
    so the L-regeneration seam is exercised end to end.
    """
    config = stub_config(**config_overrides)
    out = tmp_dir / f"{config.cross_section_id}_stub.h5"
    if not out.exists():
        run_fragility_analysis(
            config, n_jobs=1, progress=False, output_path=out, overwrite=True
        )
    return out


def flat_record(
    level_m: float, *, hours: int = 48, dt_s: float = 3600.0, event_id: str = "flat"
) -> HydrographRecord:
    """A constant-stage record (negligible when level_m sits at the toe)."""
    n = max(2, int(round(hours * 3600.0 / dt_s)))
    t = np.arange(n, dtype=np.float64) * dt_s
    h = np.full(n, float(level_m), dtype=np.float64)
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(level_m),
        duration_hours=float((n - 1) * dt_s / 3600.0),
        scenario="historical",
        event_id=event_id,
        native_dt=float(dt_s),
    )


def stressing_record(
    peak_m: float,
    *,
    hours: int = 96,
    dt_s: float = 3600.0,
    base_m: float = Z_TOE,
    event_id: str = "stress",
) -> HydrographRecord:
    """A long single-plateau event driving sustained progression.

    Rises from the toe baseline to ``peak_m`` and holds a broad plateau, so
    high C_e times k_aq rows breach while slow rows survive: the shape the
    laminar-conservatism signature tests need.
    """
    n = max(8, int(round(hours * 3600.0 / dt_s)))
    t = np.arange(n, dtype=np.float64) * dt_s
    ramp = n // 4
    h = np.full(n, float(peak_m), dtype=np.float64)
    h[:ramp] = base_m + (peak_m - base_m) * np.linspace(0.0, 1.0, ramp)
    h[-ramp:] = base_m + (peak_m - base_m) * np.linspace(1.0, 0.0, ramp)
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(h.max()),
        duration_hours=float((n - 1) * dt_s / 3600.0),
        scenario="historical",
        event_id=event_id,
        native_dt=float(dt_s),
    )
