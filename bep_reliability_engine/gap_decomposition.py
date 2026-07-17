"""Stage 6.6: comparator-ladder decomposition of the static-transient gap (ADR-0040).

Quantifies the total bias between the static Sellmeijer comparator (C0, the
production static branch, ADR-0028) and the transient Pol progression model
(C4, the production transient branch, ADR-0027) and decomposes it into the
named spec §12 Failure Mode 4 components -- head-convention, dimensional,
initiation-gate and temporal (net of the ADR-0009 H_eq-conservatism, which is
bounded separately via the ADR-0041 end-factor override) -- on ONE shared
sample: every comparator consumes the identical (N, 7) theta matrix and the
identical independent stochastic-L draw, so comparator differences are
physical, never sampling noise (the ADR-0002 shared-sample contract extended
across the whole ladder).

Comparator set (ADR-0040 Decision 1)
------------------------------------
Static analysis variants (peak load, closed form through the M8 diagnostics):

* ``C0``  raw gross head vs H_c(alpha = -1/3)  -- the production static branch
* ``C0b`` raw gross head vs H_c(alpha = -1/2)  -- path-dependence lattice member
* ``C1``  crack-reduced head vs H_c(-1/3)      -- head-convention variant
* ``C2``  crack-reduced head vs H_c(-1/2)      -- + dimensional variant

Pseudo-static (sustained-peak) comparators, the exact analytic limit
(ADR-0040 Decision 2: under a constant outer level the transient fails iff
the heave gate is open at that level AND the crack-reduced erosion head
strictly exceeds the H_eq curve maximum H_c,transient; the 0.9 end anchor
provably drops out of the sustained indicator):

* ``C3b`` gate AND H_erosion > H_c(-1/3)
* ``C3a`` gate AND H_erosion > H_c(-1/2)

Transient comparators (full canonical-hydrograph ODE through M8):

* ``C4b`` production transient (alpha -1/3, end factor 0.9)
* ``C4a`` ADR-0017 dimensional sensitivity (alpha_transient = -1/2)
* ``C4c`` end factor 1.0 at alpha -1/3 (ADR-0041 H_eq-conservatism bound)
* ``C4d`` end factor 1.0 at alpha -1/2

Ladders (ADR-0040 Decision 1): the engine ladder ``C0 -> C1 -> C3b -> C4b``
decomposes the production gap (no dimensional step -- both production branches
share one H_c by the single-source contract); the physics ladder
``C0 -> C1 -> C2 -> C3a -> C4a`` ends at the 3D-consistent transient.

Everything routes through :func:`~bep_reliability_engine.evaluator.
evaluate_batch_diagnostics` (M8) or its returned diagnostics; the static
comparators reuse the H_c / H_c_transient arrays computed by the very same M8
calls that produce the transient flags, so the shared preamble is shared by
construction. C0 and C4b are asserted bit-identical to the M8 production flags
inside every level task.

Statistics: per-level Clopper-Pearson CIs on every comparator
(:func:`~bep_reliability_engine.fragility.binomial_ci`, ADR-0024) and a joint
paired bootstrap over realizations (one index draw shared by all comparators
per replicate) from which every derived delta, fraction and Shapley value
inherits its CI. Components whose paired CI covers zero are flagged
unresolved.

References: ADR-0040 (design), ADR-0041 (end-factor override), ADR-0009,
ADR-0017, ADR-0024, ADR-0027/0028, ADR-0030 (the trans-not-static Euler-flip
diagnostic reused here), Pol SIE 2024 Eqs. (5)-(11), Sellmeijer (2011).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from joblib import Parallel, delayed
from numpy.typing import NDArray

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import evaluate_batch_diagnostics
from bep_reliability_engine.fragility import binomial_ci
from bep_reliability_engine.hydrographs import HydrographRecord
from bep_reliability_engine.progression import CRACK_RESISTANCE_FACTOR
from bep_reliability_engine.run import (
    conditioning_hydrographs_for_config,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_theta

__all__ = [
    "ALPHA_2D",
    "ALPHA_3D",
    "COMPARATOR_ORDER",
    "COMPARATOR_DEFINITIONS",
    "ENGINE_LADDER_STEPS",
    "PHYSICS_LADDER_STEPS",
    "AUXILIARY_DELTAS",
    "GapDecompositionResult",
    "BootstrapMeans",
    "prepare_config",
    "sustained_peak_record",
    "run_comparator_ladder",
    "bootstrap_comparator_means",
    "delta_ci",
    "component_table",
    "static_pair_shapley",
    "sustained_duration_ladder",
]

# Scale exponents of the Sellmeijer F_s group (spec §12 fm4; ADR-0017).
ALPHA_2D: float = -1.0 / 3.0
ALPHA_3D: float = -0.5

# Canonical comparator order for persistence, bootstrap packing and tables.
COMPARATOR_ORDER: tuple[str, ...] = (
    "C0",
    "C0b",
    "C1",
    "C2",
    "C3b",
    "C3a",
    "C4b",
    "C4a",
    "C4c",
    "C4d",
)

# Human/metadata definitions (persisted verbatim into the JSON sidecar).
COMPARATOR_DEFINITIONS: dict[str, str] = {
    "C0": "static, raw gross head h_peak - z_toe vs H_c(alpha=-1/3); "
    "production static branch (ADR-0028)",
    "C0b": "static, raw gross head vs H_c(alpha=-1/2); lattice member",
    "C1": "static, crack-reduced head (h_peak - z_toe) - 0.3*D_bl vs "
    "H_c(alpha=-1/3); head-convention variant",
    "C2": "static, crack-reduced head vs H_c(alpha=-1/2); dimensional variant",
    "C3b": "pseudo-static analytic sustained-peak limit: heave gate at peak "
    "AND H_erosion(peak) > H_c(alpha=-1/3)",
    "C3a": "pseudo-static analytic sustained-peak limit at H_c(alpha=-1/2)",
    "C4b": "transient, canonical hydrograph, alpha=-1/3, end factor 0.9; "
    "production transient branch (ADR-0027)",
    "C4a": "transient, canonical hydrograph, alpha_transient=-1/2 (ADR-0017)",
    "C4c": "transient, canonical hydrograph, alpha=-1/3, "
    "equilibrium_end_factor=1.0 (ADR-0041)",
    "C4d": "transient, canonical hydrograph, alpha_transient=-1/2, "
    "equilibrium_end_factor=1.0 (ADR-0041)",
}

# Ladder steps as (component_name, minuend, subtrahend): the component's
# contribution to the gap is P_f(minuend) - P_f(subtrahend), so the steps of a
# ladder telescope exactly to P_f(C0) - P_f(endpoint).
PHYSICS_LADDER_STEPS: tuple[tuple[str, str, str], ...] = (
    ("head_convention", "C0", "C1"),
    ("dimensional", "C1", "C2"),
    ("initiation_gate", "C2", "C3a"),
    ("temporal_net", "C3a", "C4a"),
)
ENGINE_LADDER_STEPS: tuple[tuple[str, str, str], ...] = (
    ("head_convention", "C0", "C1"),
    ("initiation_gate", "C1", "C3b"),
    ("temporal_net", "C3b", "C4b"),
)
# Auxiliary deltas outside the telescoping ladders (same sign convention).
AUXILIARY_DELTAS: tuple[tuple[str, str, str], ...] = (
    ("heq_conservatism_engine", "C4b", "C4c"),
    ("heq_conservatism_physics", "C4a", "C4d"),
    ("dimensional_at_static", "C1", "C2"),
    ("dimensional_at_sustained", "C3b", "C3a"),
    ("dimensional_at_transient", "C4b", "C4a"),
    ("total_gap_engine", "C0", "C4b"),
    ("total_gap_physics", "C0", "C4a"),
)

_SOURCE_SUSTAINED = "stage6_6_sustained_peak"


def prepare_config(
    config: Config,
    *,
    n_samples: int | None = None,
    extra_levels: tuple[float, ...] = (),
) -> Config:
    """Return a copy of ``config`` with extra grid levels and/or a reduced N.

    The Stage 6.6 runs evaluate the generated production grid plus the exact
    section HWL (the design-flood evaluation point, ADR-0040 Decision 6), and
    the pilot/verification runs use reduced N. Neither belongs in the
    generated YAML (configs are generated, never hand-edited), so the
    modified copy is built here. Adding levels does not perturb the theta or
    L draws (both are seed-driven only); changing ``n_samples`` yields an
    entirely different LHS sample, which is fine for pilots and wrong for
    production drift-guards -- the driver only overrides N on pilot paths.

    Parameters
    ----------
    config : Config
        The validated base config (typically ``Config.from_yaml``).
    n_samples : int, optional
        Override for ``mc.n_samples`` (pilot runs). None keeps the config N.
    extra_levels : tuple of float, optional
        Conditioning levels [m MSL] merged (set-union, sorted) into
        ``mc.conditioning_grid``; duplicates are dropped.

    Returns
    -------
    Config
        The modified copy; the input config is never mutated.
    """
    updates: dict[str, Any] = {}
    grid = tuple(
        sorted(
            set(float(x) for x in config.mc.conditioning_grid).union(
                float(x) for x in extra_levels
            )
        )
    )
    mc_updates: dict[str, Any] = {"conditioning_grid": grid}
    if n_samples is not None:
        mc_updates["n_samples"] = int(n_samples)
    updates["mc"] = config.mc.model_copy(update=mc_updates)
    return config.model_copy(update=updates)


def sustained_peak_record(
    level_m: float,
    *,
    dt_s: float,
    n_steps: int = 4,
    scenario: str = "historical",
) -> HydrographRecord:
    """Build a constant-stage (sustained-peak) loading record.

    The idealized held-peak loading of the pseudo-static comparators
    (ADR-0040 Decision 2): ``h(t) = level_m`` for every sample, no ramp (the
    ADR-0032-retained instantaneous M4 translation makes a ramp physically
    inert). Short records (default 4 samples) suffice for the analytic-limit
    diagnostics (gate latches and critical heads are level-, not
    duration-dependent); the finite-duration ODE verification ladder passes
    larger ``n_steps``.

    Parameters
    ----------
    level_m : float
        The sustained outer water level [m MSL]; becomes ``peak`` verbatim.
    dt_s : float
        Sample spacing [s]; the forward-Euler integration timestep at the M8
        boundary (ADR-0010/0030 -- pass the run's ``target_dt_seconds``).
    n_steps : int, optional
        Number of samples (>= 2). Default 4 (analytic-limit diagnostics).
    scenario : str, optional
        Scenario tag carried on the record; metadata only.

    Returns
    -------
    HydrographRecord
        The constant record, ``peak == level_m``, provenance marked
        ``stage6_6_sustained_peak``.
    """
    if n_steps < 2:
        raise ValueError(f"n_steps must be >= 2, got {n_steps}.")
    t = np.arange(n_steps, dtype=np.float64) * float(dt_s)
    h = np.full(n_steps, float(level_m), dtype=np.float64)
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(level_m),
        duration_hours=float((n_steps - 1) * dt_s / 3600.0),
        scenario=scenario,
        event_id=f"sustained_h{level_m:g}",
        native_dt=float(dt_s),
        provenance={"source": _SOURCE_SUSTAINED},
    )


@dataclass(frozen=True)
class _LadderSettings:
    """Run-constant evaluation knobs shared by every level task (picklable)."""

    l_ini_m: float
    seepage_length_samples: NDArray[np.float64] | None
    alpha_exponent: float
    theta_repose_rad: float
    relative_density: float
    foreland_open: bool
    sustained_dt_s: float
    scenario: str


def _analytic_sustained_flags(
    gate_open: NDArray[np.bool_],
    h_erosion_m: NDArray[np.float64],
    h_c_transient_m: NDArray[np.float64],
) -> NDArray[np.bool_]:
    """The exact sustained-peak failure indicator (ADR-0040 Decision 2).

    Failure iff the heave gate is open at the sustained level AND the
    crack-reduced erosion head strictly exceeds the H_eq maximum
    ``H_c,transient`` (equality stalls asymptotically at l_c, so it is not
    failure; the boundary set has measure zero under continuous priors).
    """
    return gate_open & (h_erosion_m > h_c_transient_m)


def _evaluate_ladder_level(
    level_index: int,
    level_m: float,
    record: HydrographRecord,
    theta_matrix: NDArray[np.float64],
    geometry: dict[str, float],
    settings: _LadderSettings,
) -> tuple[int, dict[str, NDArray[np.bool_]], dict[str, int]]:
    """One conditioning level: all ten comparators on the shared sample.

    Module-level (picklable for loky). Four transient M8 batch calls (the
    2x2 of alpha_transient x end factor) plus one short sustained-record M8
    call for the gate latches; the six analytic comparators are derived from
    the diagnostics of those same calls, so H_c, H_c_transient, r_e and the
    gate all come from the engine's own shared preamble (drift-proof by
    construction). C0 is asserted equal to the reimplemented static
    comparison as an internal cross-check.

    Returns
    -------
    tuple
        ``(level_index, {comparator_id: (N,) bool}, {diagnostic: count})``
        with the Euler-flip counts (rows failing a comparator that nests
        inside another in continuous time; expected 0 at 225 s, ADR-0030).
    """
    common = dict(
        l_ini=settings.l_ini_m,
        seepage_length_samples=settings.seepage_length_samples,
        alpha_exponent=settings.alpha_exponent,
        theta_repose_rad=settings.theta_repose_rad,
        relative_density=settings.relative_density,
        foreland_open=settings.foreland_open,
        progression_backend="numpy",
    )
    diag_b = evaluate_batch_diagnostics(theta_matrix, record, geometry, **common)
    diag_a = evaluate_batch_diagnostics(
        theta_matrix, record, geometry, alpha_exponent_transient=ALPHA_3D, **common
    )
    diag_c = evaluate_batch_diagnostics(
        theta_matrix, record, geometry, equilibrium_end_factor=1.0, **common
    )
    diag_d = evaluate_batch_diagnostics(
        theta_matrix,
        record,
        geometry,
        alpha_exponent_transient=ALPHA_3D,
        equilibrium_end_factor=1.0,
        **common,
    )
    # Gate latches at the sustained level (constant record => heave_occurred
    # is exactly "heave open at this level"; ADR-0008 collapse). A short
    # record suffices; alpha/end factor do not touch the gate.
    gate_record = sustained_peak_record(
        level_m,
        dt_s=settings.sustained_dt_s,
        scenario=settings.scenario,
    )
    diag_gate = evaluate_batch_diagnostics(
        theta_matrix, gate_record, geometry, **common
    )
    gate_open = np.asarray(diag_gate.heave_occurred, dtype=bool)

    z_toe_m = float(geometry["z_toe"])
    d_bl_m = np.asarray(theta_matrix[:, 3], dtype=np.float64)
    h_c_2d = diag_b.H_c  # alpha = -1/3 (the production, single-source H_c)
    h_c_3d = diag_a.H_c_transient  # alpha = -1/2 (the ADR-0017 second M6 call)

    raw_load_m = float(record.peak) - z_toe_m
    crack_load_m = raw_load_m - CRACK_RESISTANCE_FACTOR * d_bl_m

    flags: dict[str, NDArray[np.bool_]] = {}
    flags["C0"] = np.asarray(diag_b.failure_static, dtype=bool)
    flags["C0b"] = (h_c_3d - raw_load_m) <= 0.0
    flags["C1"] = (h_c_2d - crack_load_m) <= 0.0
    flags["C2"] = (h_c_3d - crack_load_m) <= 0.0
    flags["C3b"] = _analytic_sustained_flags(gate_open, crack_load_m, h_c_2d)
    flags["C3a"] = _analytic_sustained_flags(gate_open, crack_load_m, h_c_3d)
    flags["C4b"] = np.asarray(diag_b.failure_trans, dtype=bool)
    flags["C4a"] = np.asarray(diag_a.failure_trans, dtype=bool)
    flags["C4c"] = np.asarray(diag_c.failure_trans, dtype=bool)
    flags["C4d"] = np.asarray(diag_d.failure_trans, dtype=bool)

    # Internal cross-checks: (a) the reimplemented static comparison equals
    # the M8 static flags bit for bit (C0 is the production static branch);
    # (b) the algebraically exact nestings hold (crack load < raw load since
    # D_bl > 0; strict > inside >=).
    reimplemented_c0 = (h_c_2d - raw_load_m) <= 0.0
    if not np.array_equal(flags["C0"], reimplemented_c0):
        raise AssertionError(
            "static comparator drift: reimplemented C0 differs from the M8 "
            f"failure_static flags at level {level_m} (ADR-0040 gate i)."
        )
    for inner, outer in (("C1", "C0"), ("C2", "C0b"), ("C3a", "C2"), ("C3b", "C1")):
        if np.any(flags[inner] & ~flags[outer]):
            raise AssertionError(
                f"structural nesting violated: {inner} not within {outer} at "
                f"level {level_m}."
            )

    # Euler-flip diagnostics (possible in discrete time only; counted, not
    # asserted -- the ADR-0030 consistency property, expected 0 at 225 s).
    flips = {
        "c4b_not_c0": int(np.sum(flags["C4b"] & ~flags["C0"])),
        "c4b_not_c3b": int(np.sum(flags["C4b"] & ~flags["C3b"])),
        "c4a_not_c3a": int(np.sum(flags["C4a"] & ~flags["C3a"])),
        "c4c_not_c4b": int(np.sum(flags["C4c"] & ~flags["C4b"])),
        "c4d_not_c4a": int(np.sum(flags["C4d"] & ~flags["C4a"])),
    }
    return level_index, flags, flips


@dataclass
class GapDecompositionResult:
    """The Stage 6.6 comparator ladder for one section (ADR-0040).

    Attributes
    ----------
    conditioning_grid : numpy.ndarray, shape (N_h,)
        Conditioning levels [m MSL] (the config grid plus the inserted HWL).
    comparators : dict of str to numpy.ndarray
        ``{comparator_id: (N, N_h) bool}`` failure matrices on the shared
        sample, keys exactly :data:`COMPARATOR_ORDER`.
    theta_matrix : numpy.ndarray, shape (N, 7)
        The shared prior sample (retained; every comparator consumed it).
    param_names : list of str
        Canonical theta column names.
    seepage_length_samples : numpy.ndarray or None
        The shared independent stochastic-L draw, or None (deterministic L).
    flip_counts : dict of str to numpy.ndarray
        Per-level Euler-flip counts (see ``_evaluate_ladder_level``).
    metadata : dict
        Config snapshot + hash, comparator definitions, runtime, code refs.
    """

    conditioning_grid: NDArray[np.float64]
    comparators: dict[str, NDArray[np.bool_]]
    theta_matrix: NDArray[np.float64]
    param_names: list[str]
    seepage_length_samples: NDArray[np.float64] | None
    flip_counts: dict[str, NDArray[np.int64]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def n_samples(self) -> int:
        """Number of realizations N behind every comparator column."""
        return int(self.theta_matrix.shape[0])

    def p_f(self) -> dict[str, NDArray[np.float64]]:
        """Raw per-level failure probabilities per comparator."""
        return {
            name: matrix.mean(axis=0, dtype=np.float64)
            for name, matrix in self.comparators.items()
        }

    def binomial_cis(
        self, confidence: float = 0.95
    ) -> dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]:
        """Clopper-Pearson CIs on the raw points, per comparator (ADR-0024)."""
        return {
            name: binomial_ci(p, self.n_samples, confidence)
            for name, p in self.p_f().items()
        }

    def save(self, path: str | Path) -> None:
        """Persist to HDF5 (arrays) + JSON sidecar (metadata) (spec §8 style)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(path, "w") as handle:
            handle.create_dataset("theta_matrix", data=self.theta_matrix)
            handle.create_dataset(
                "param_names",
                data=np.array(self.param_names, dtype=h5py.string_dtype()),
            )
            handle.create_dataset("conditioning_grid", data=self.conditioning_grid)
            if self.seepage_length_samples is not None:
                handle.create_dataset(
                    "seepage_length_samples", data=self.seepage_length_samples
                )
            comp = handle.create_group("comparators")
            for name in COMPARATOR_ORDER:
                comp.create_dataset(name, data=self.comparators[name])
            flips = handle.create_group("flip_counts")
            for name, counts in self.flip_counts.items():
                flips.create_dataset(name, data=counts)
        sidecar = path.with_suffix(".json")
        sidecar.write_text(json.dumps(self.metadata, indent=2, sort_keys=True))

    @classmethod
    def load(cls, path: str | Path) -> GapDecompositionResult:
        """Load a persisted result (inverse of :meth:`save`)."""
        path = Path(path)
        with h5py.File(path, "r") as handle:
            theta = handle["theta_matrix"][:]
            param_names = [
                s.decode() if isinstance(s, bytes) else str(s)
                for s in handle["param_names"][:]
            ]
            grid = handle["conditioning_grid"][:]
            seepage = (
                handle["seepage_length_samples"][:]
                if "seepage_length_samples" in handle
                else None
            )
            comparators = {
                name: handle["comparators"][name][:].astype(bool)
                for name in handle["comparators"]
            }
            flip_counts = {
                name: handle["flip_counts"][name][:].astype(np.int64)
                for name in handle["flip_counts"]
            }
        sidecar = path.with_suffix(".json")
        metadata = json.loads(sidecar.read_text()) if sidecar.exists() else {}
        return cls(
            conditioning_grid=grid,
            comparators=comparators,
            theta_matrix=theta,
            param_names=param_names,
            seepage_length_samples=seepage,
            flip_counts=flip_counts,
            metadata=metadata,
        )


def run_comparator_ladder(
    config: Config,
    *,
    n_jobs: int = 1,
    progress: bool = False,
) -> GapDecompositionResult:
    """Run the full ten-comparator ladder for one section config (ADR-0040).

    Samples the prior exactly once (the run's own seed recipe, bit-identical
    to :func:`~bep_reliability_engine.run.run_fragility_analysis` for the
    same config), builds the per-level canonical records through the same M3
    path the production sweep used, and evaluates every comparator per level
    on the shared sample. The M7 backend is forced to ``numpy`` (the
    reference path) so C0/C4b stay bit-comparable with the persisted
    production sweeps and the ADR-0041 override is available.

    Parameters
    ----------
    config : Config
        The (possibly :func:`prepare_config`-modified) run configuration.
    n_jobs : int, optional
        joblib worker count over conditioning levels (the spec §3 outer
        loop); results are assembled by level index, so parallel == serial.
    progress : bool, optional
        Wrap the level loop in tqdm.

    Returns
    -------
    GapDecompositionResult
        All ten comparator matrices plus flip diagnostics and metadata.
    """
    started = time.time()
    theta_sample = sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    )
    theta = theta_sample.theta_matrix
    seepage = seepage_length_samples_for_config(config)
    records = conditioning_hydrographs_for_config(config)
    geometry = config.geometry.as_evaluator_dict()
    grid = np.asarray(config.mc.conditioning_grid, dtype=np.float64)

    sustained_dt = (
        float(config.timestepper.target_dt_seconds)
        if config.timestepper.target_dt_seconds is not None
        else float(records[0].native_dt)
    )
    settings = _LadderSettings(
        l_ini_m=0.0,
        seepage_length_samples=seepage,
        alpha_exponent=config.alpha_exponent,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        foreland_open=config.foreland_treatment == "open_entry",
        sustained_dt_s=sustained_dt,
        scenario=config.scenario,
    )

    tasks = (
        delayed(_evaluate_ladder_level)(
            i, float(grid[i]), records[i], theta, geometry, settings
        )
        for i in range(grid.size)
    )
    if progress:
        from tqdm import tqdm

        iterator = tqdm(tasks, total=grid.size, desc="stage6.6 levels")
    else:
        iterator = tasks
    level_results = Parallel(n_jobs=n_jobs)(iterator)

    n = theta.shape[0]
    comparators = {
        name: np.zeros((n, grid.size), dtype=bool) for name in COMPARATOR_ORDER
    }
    flip_counts = {
        name: np.zeros(grid.size, dtype=np.int64)
        for name in (
            "c4b_not_c0",
            "c4b_not_c3b",
            "c4a_not_c3a",
            "c4c_not_c4b",
            "c4d_not_c4a",
        )
    }
    for level_index, flags, flips in level_results:
        for name in COMPARATOR_ORDER:
            comparators[name][:, level_index] = flags[name]
        for name, count in flips.items():
            flip_counts[name][level_index] = count

    metadata: dict[str, Any] = {
        "stage": "6.6",
        "adr": ["ADR-0040", "ADR-0041"],
        "config": config.to_metadata(),
        "config_hash": config.config_hash(),
        "cross_section_id": config.cross_section_id,
        "d70_interpretation": config.priors.d70_interpretation,
        "comparators": dict(COMPARATOR_DEFINITIONS),
        "alpha_2d": ALPHA_2D,
        "alpha_3d": ALPHA_3D,
        "crack_resistance_factor": CRACK_RESISTANCE_FACTOR,
        "progression_backend": "numpy",
        "sustained_dt_s": sustained_dt,
        "n_samples": int(n),
        "runtime_seconds": round(time.time() - started, 1),
        "sampling": theta_sample.metadata,
    }
    return GapDecompositionResult(
        conditioning_grid=grid,
        comparators=comparators,
        theta_matrix=theta,
        param_names=list(theta_sample.param_names),
        seepage_length_samples=seepage,
        flip_counts=flip_counts,
        metadata=metadata,
    )


@dataclass(frozen=True)
class BootstrapMeans:
    """Joint paired-bootstrap comparator means (ADR-0040 Decision 6).

    ``means[b, k, i]`` is the replicate-b mean of comparator
    ``comparator_ids[k]`` at level i, with ONE realization index draw shared
    by all comparators within a replicate (the pairing that makes derived
    delta CIs reflect the discordant sets rather than independent binomials).
    """

    comparator_ids: tuple[str, ...]
    means: NDArray[np.float64]
    seed: int

    def index(self, name: str) -> int:
        """Position of comparator ``name`` in the packed axis."""
        return self.comparator_ids.index(name)


def bootstrap_comparator_means(
    result: GapDecompositionResult,
    *,
    n_replicates: int = 1000,
    seed: int = 20260717,
) -> BootstrapMeans:
    """Draw joint paired-bootstrap means for every comparator and level.

    Resamples realizations with replacement (rows of the shared sample);
    within a replicate the same row draw evaluates every comparator, so any
    linear combination of comparator means inherits a paired CI via
    :func:`delta_ci`.

    Parameters
    ----------
    result : GapDecompositionResult
        The ladder to bootstrap.
    n_replicates : int, optional
        Bootstrap replicates B (default 1000).
    seed : int, optional
        RNG seed (deterministic replicates).

    Returns
    -------
    BootstrapMeans
        ``(B, K, N_h)`` replicate means in :data:`COMPARATOR_ORDER`.
    """
    ids = tuple(COMPARATOR_ORDER)
    n = result.n_samples
    n_h = result.conditioning_grid.size
    stacked = np.concatenate(
        [result.comparators[name].astype(np.uint8) for name in ids], axis=1
    )
    rng = np.random.default_rng(seed)
    means = np.empty((n_replicates, len(ids), n_h), dtype=np.float64)
    for b in range(n_replicates):
        idx = rng.integers(0, n, size=n)
        means[b] = stacked[idx].mean(axis=0, dtype=np.float64).reshape(len(ids), n_h)
    return BootstrapMeans(comparator_ids=ids, means=means, seed=seed)


def delta_ci(
    boot: BootstrapMeans,
    minuend: str,
    subtrahend: str,
    *,
    confidence: float = 0.95,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Paired percentile CI for ``P_f(minuend) - P_f(subtrahend)`` per level."""
    alpha = 100.0 * (1.0 - confidence)
    deltas = (
        boot.means[:, boot.index(minuend), :] - boot.means[:, boot.index(subtrahend), :]
    )
    lo, hi = np.percentile(deltas, [alpha / 2.0, 100.0 - alpha / 2.0], axis=0)
    return lo, hi


def component_table(
    result: GapDecompositionResult,
    boot: BootstrapMeans,
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Assemble the per-level component tables for both ladders (ADR-0040).

    For each ladder step (and each auxiliary delta) the point estimate
    ``P_f(minuend) - P_f(subtrahend)``, the paired bootstrap CI, and a
    ``resolved`` flag (CI excludes zero); plus each step's fraction of the
    ladder's total gap at levels where the total itself is resolved. Steps
    whose CI covers zero are reported unresolved, never as findings
    (mission requirement).

    Returns
    -------
    dict
        JSON-serializable: ``{'levels': [...], 'ladders': {...},
        'auxiliary': {...}, 'confidence': ...}``.
    """
    p_f = result.p_f()
    out: dict[str, Any] = {
        "levels": result.conditioning_grid.tolist(),
        "confidence": confidence,
        "n_samples": result.n_samples,
        "ladders": {},
        "auxiliary": {},
    }
    for ladder_name, steps, endpoint in (
        ("physics", PHYSICS_LADDER_STEPS, "C4a"),
        ("engine", ENGINE_LADDER_STEPS, "C4b"),
    ):
        total = p_f["C0"] - p_f[endpoint]
        total_lo, total_hi = delta_ci(boot, "C0", endpoint, confidence=confidence)
        total_resolved = (total_lo > 0.0) | (total_hi < 0.0)
        ladder: dict[str, Any] = {
            "endpoint": endpoint,
            "total_gap": total.tolist(),
            "total_gap_ci": [total_lo.tolist(), total_hi.tolist()],
            "total_resolved": total_resolved.tolist(),
            "steps": {},
        }
        for name, minuend, subtrahend in steps:
            delta = p_f[minuend] - p_f[subtrahend]
            lo, hi = delta_ci(boot, minuend, subtrahend, confidence=confidence)
            resolved = (lo > 0.0) | (hi < 0.0)
            with np.errstate(divide="ignore", invalid="ignore"):
                fraction = np.where(total_resolved, delta / total, np.nan)
            ladder["steps"][name] = {
                "minuend": minuend,
                "subtrahend": subtrahend,
                "delta": delta.tolist(),
                "ci": [lo.tolist(), hi.tolist()],
                "resolved": resolved.tolist(),
                "fraction_of_total": fraction.tolist(),
            }
        out["ladders"][ladder_name] = ladder
    for name, minuend, subtrahend in AUXILIARY_DELTAS:
        delta = p_f[minuend] - p_f[subtrahend]
        lo, hi = delta_ci(boot, minuend, subtrahend, confidence=confidence)
        out["auxiliary"][name] = {
            "minuend": minuend,
            "subtrahend": subtrahend,
            "delta": delta.tolist(),
            "ci": [lo.tolist(), hi.tolist()],
            "resolved": ((lo > 0.0) | (hi < 0.0)).tolist(),
        }
    return out


def static_pair_shapley(
    result: GapDecompositionResult,
    boot: BootstrapMeans,
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Two-toggle Shapley attribution on the static {head, alpha} lattice.

    The static sub-lattice is complete (C0 raw/-1/3, C0b raw/-1/2, C1
    crack/-1/3, C2 crack/-1/2), so both orderings of the head-convention and
    dimensional components exist exactly, the Shapley value is their average,
    and the interaction is their difference (ADR-0040 Decision 5). Sign
    convention as everywhere: a component's value is its contribution to
    P_f(C0) - P_f(C2) along the chosen path.

    Returns
    -------
    dict
        Per level: both orderings, Shapley values, interaction, with paired
        bootstrap CIs.
    """
    p_f = result.p_f()

    def _combo(expr: dict[str, float]) -> NDArray[np.float64]:
        value = np.zeros_like(p_f["C0"])
        for name, coeff in expr.items():
            value = value + coeff * p_f[name]
        return value

    def _combo_ci(expr: dict[str, float]) -> tuple[list[float], list[float]]:
        samples = np.zeros_like(boot.means[:, 0, :])
        for name, coeff in expr.items():
            samples = samples + coeff * boot.means[:, boot.index(name), :]
        alpha = 100.0 * (1.0 - confidence)
        lo, hi = np.percentile(samples, [alpha / 2.0, 100.0 - alpha / 2.0], axis=0)
        return lo.tolist(), hi.tolist()

    expressions = {
        "head_first_head": {"C0": 1.0, "C1": -1.0},
        "head_first_dimensional": {"C1": 1.0, "C2": -1.0},
        "alpha_first_dimensional": {"C0": 1.0, "C0b": -1.0},
        "alpha_first_head": {"C0b": 1.0, "C2": -1.0},
        "shapley_head": {"C0": 0.5, "C1": -0.5, "C0b": 0.5, "C2": -0.5},
        "shapley_dimensional": {"C1": 0.5, "C2": -0.5, "C0": 0.5, "C0b": -0.5},
        "interaction": {"C0": 1.0, "C1": -1.0, "C0b": -1.0, "C2": 1.0},
    }
    out: dict[str, Any] = {"levels": result.conditioning_grid.tolist()}
    for name, expr in expressions.items():
        lo, hi = _combo_ci(expr)
        out[name] = {"delta": _combo(expr).tolist(), "ci": [lo, hi]}
    return out


def _sustained_ladder_point(
    level_m: float,
    hours: float,
    dt_s: float,
    scenario: str,
    theta: NDArray[np.float64],
    geometry: dict[str, float],
    common: dict[str, Any],
) -> tuple[float, float, dict[str, int]]:
    """One (level, hold-duration) verification point (module-level for loky).

    Integrates the full M7 ODE on a constant record of ``hours`` and compares
    the resulting failure indicator with the analytic sustained-peak limit
    computed from the same call's diagnostics.
    """
    n_steps = max(2, int(round(hours * 3600.0 / dt_s)))
    record = sustained_peak_record(
        level_m, dt_s=dt_s, n_steps=n_steps, scenario=scenario
    )
    diag = evaluate_batch_diagnostics(theta, record, geometry, **common)
    crack_load = (
        float(level_m)
        - float(geometry["z_toe"])
        - CRACK_RESISTANCE_FACTOR * theta[:, 3]
    )
    analytic = _analytic_sustained_flags(
        np.asarray(diag.heave_occurred, dtype=bool), crack_load, diag.H_c_transient
    )
    ode = np.asarray(diag.failure_trans, dtype=bool)
    return (
        level_m,
        hours,
        {
            "analytic_failures": int(analytic.sum()),
            "ode_failures": int(ode.sum()),
            "analytic_not_ode": int(np.sum(analytic & ~ode)),
            "ode_not_analytic": int(np.sum(ode & ~analytic)),
        },
    )


def sustained_duration_ladder(
    config: Config,
    *,
    levels_m: tuple[float, ...],
    durations_hours: tuple[float, ...] = (24.0, 96.0, 384.0, 1536.0),
    alpha_exponent_transient: float | None = None,
    n_jobs: int = 1,
) -> dict[str, Any]:
    """Verify the analytic sustained-peak limit against finite ODE runs.

    For each level, integrates the full M7 ODE on constant records of
    doubling hold duration and counts disagreements with the analytic
    indicator (ADR-0040 Decision 2 verification). Expected behavior: the
    ODE indicator converges to the analytic limit from below (missing
    only near-critical rows whose breach time exceeds the hold), and never
    exceeds it except by forward-Euler barrier jumps (counted separately).

    Parameters
    ----------
    config : Config
        The run configuration (use :func:`prepare_config` for pilot N).
    levels_m : tuple of float
        Conditioning levels [m MSL] to check.
    durations_hours : tuple of float, optional
        Hold durations; default 1, 4, 16, 64 days.
    alpha_exponent_transient : float or None, optional
        The ADR-0017 transient exponent (None = production -1/3).
    n_jobs : int, optional
        joblib workers over (level, duration) tasks.

    Returns
    -------
    dict
        JSON-serializable verification record.
    """
    theta_sample = sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    )
    theta = theta_sample.theta_matrix
    seepage = seepage_length_samples_for_config(config)
    geometry = config.geometry.as_evaluator_dict()
    dt_s = (
        float(config.timestepper.target_dt_seconds)
        if config.timestepper.target_dt_seconds is not None
        else 3600.0
    )
    common = dict(
        l_ini=0.0,
        seepage_length_samples=seepage,
        alpha_exponent=config.alpha_exponent,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        foreland_open=config.foreland_treatment == "open_entry",
        progression_backend="numpy",
    )
    if alpha_exponent_transient is not None:
        common["alpha_exponent_transient"] = alpha_exponent_transient

    tasks = [
        delayed(_sustained_ladder_point)(
            float(level),
            float(hours),
            dt_s,
            config.scenario,
            theta,
            geometry,
            common,
        )
        for level in levels_m
        for hours in durations_hours
    ]
    rows = Parallel(n_jobs=n_jobs)(tasks)
    return {
        "n_samples": int(theta.shape[0]),
        "dt_s": dt_s,
        "alpha_exponent_transient": alpha_exponent_transient,
        "durations_hours": list(durations_hours),
        "levels_m": list(levels_m),
        "rows": [
            {"level_m": level, "hours": hours, **counts}
            for level, hours, counts in rows
        ],
    }
