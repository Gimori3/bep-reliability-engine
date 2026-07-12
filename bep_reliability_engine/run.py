"""Top-level orchestrator: ``run_fragility_analysis(config)`` (spec §3, §6, §9).

Single responsibility: drive the three nested loops of spec §3 over the *built*
module interfaces (M1 ``config`` -> M2 ``sampling`` -> M8 ``evaluator`` -> M9
``fragility``) and emit one persisted :class:`FragilityResult` per cross-section
per scenario. This module contains **no physics**: every limit
state goes through M8 ``evaluate_realization`` so the shared-sample contract
(ADR-0002) is enforced in exactly one place and never re-implemented here.

Logical execution sequence (spec §3)
------------------------------------
Three nested levels, mapped onto the *as-built* scalar M8:

* **Outer — conditioning levels h_i** (``config.mc.conditioning_grid``,
  N_h ~ 30). Embarrassingly parallel (spec §6); this is the ``joblib`` axis
  (:func:`_evaluate_level`, one task per level).
* **Middle — realizations j in {1..N}** (``config.mc.n_samples``). One
  vectorized :func:`~bep_reliability_engine.evaluator.evaluate_batch` call per
  level, advancing all N realizations through the M4/M6/M7 kernels in a single
  pass (spec §6; review item #5) — bit-identical to looping the scalar
  ``evaluate_realization`` over the rows.
* **Inner — timesteps t_k.** Irreducibly serial; lives entirely inside M7 and is
  invisible here.

The shared-preamble-then-branch pattern (H_c, l_c, lambda_in, r_e per theta_j,
then static O(1) / transient O(T)) is owned by M8, not re-derived here.

Where theta is sampled (spec §2, §6)
------------------------------------
**Once, in the main process, before any loop** (:func:`_sample_prior` from
``config.mc.seed``). The *same* ``theta_matrix`` is reused read-only across every
h_i: a fragility curve is P(fail | h_i) over one fixed prior population, so row j
must mean the same theta_j in every column, and M9's row-bootstrap (ADR-0002)
is only valid under that shared row identity. The (N, 7) array is handed to the
``joblib`` workers read-only; loky auto-memmaps it once it exceeds ~1 MB
(N >~ 18k), so large-N sharing is copy-free.

Reproducibility by construction — parallel == serial
-----------------------------------------------------
The parallel sweep is bit-identical to a serial run, and identical across
``n_jobs`` and ``joblib`` backend, *by construction*:

* All stochasticity is front-loaded into the single :func:`_sample_prior` call,
  executed in the main process outside the parallel region.
* :func:`evaluate_realization` is a pure deterministic function (forward Euler,
  no RNG anywhere in M4-M8).
* Hydrograph construction has **no RNG on either path**: the canonical d4PDF
  shape is loaded **once, in the main process** (the event is pinned by
  ``config.hydrograph_source.canonical_event_ids[0]``, ADR-0020 §5) and the
  per-level scaling (:func:`~bep_reliability_engine.hydrographs.\
conditioning_record_for_level`) is a pure function of (shape, level); the
  synthetic stub is likewise a pure function of (level, config).
* Aggregation is **index-addressed**: each task returns its own ``level_index``
  and the main process writes column ``level_index``, so the result is invariant
  to task completion order and worker count.
* The M9 bootstrap runs serially in the main process *after* assembly, seeded
  from ``config.mc.seed``.

Because of this, ``n_jobs`` cannot change results, so it is a runtime keyword of
:func:`run_fragility_analysis`, **not** a :class:`Config` field (Config alone
determines one fragility pair; putting ``n_jobs`` in its hash would be wrong).
Backend note: the scalar M8 middle loop is CPU-bound pure Python, so processes
(loky, the joblib default) are used — a threading backend would serialize on the
GIL.

Per-level hydrograph construction: two config-selected paths
-------------------------------------------------------------
:func:`_hydrograph_for_level` builds each conditioning level's loading record
(a concrete M3 :class:`~bep_reliability_engine.hydrographs.HydrographRecord`)
in the **main process**; workers receive the built record only.

1. **CANONICAL d4PDF SHAPE (production).** When ``config.hydrograph_source``
   is set (ADR-0020), the canonical event — the *first* entry of
   ``canonical_event_ids`` — is loaded **once per run** in the main process
   (:func:`~bep_reliability_engine.hydrographs.load_canonical_shape`: band
   workbook resolved by the event's own experiment, stage under the node's own
   local rating, ADR-0019 §7 proxy honored) and normalized in stage domain.
   Each level is then the pure rescaling ``h(t) = h_base + (h_i - h_base) *
   shape(t)`` with the trough floor pinned at the section's base-flow stage
   h_base (ADR-0021 item 4 — NOT z_toe) and ``peak = h_i`` verbatim (ADR-0010).
   The MSL datum guard
   (:func:`~bep_reliability_engine.hydrographs.validate_datum_consistency`)
   runs at load time, **before any expensive work**, so an unresolved
   provisional ``z_toe = 0.0`` fails loudly rather than silently producing
   ~35 m heads. ``metadata['hydrograph_source']`` is stamped
   ``'d4pdf_scaled_canonical'`` and ``metadata['hydrograph']`` carries the full
   shape provenance (gap G5).
2. **SYNTHETIC STUB (plumbing/dev only).** When ``hydrograph_source`` is None,
   the legacy deterministic two-peak raised-cosine event from the polder
   baseline peaking at h_i is used. It exercises the M8 plumbing (the two peaks
   drive the spec §5 memory model) but is **not physical**;
   ``metadata['hydrograph_source']`` stays ``'phase1_synthetic_stub'`` so no
   synthetic run is mistaken for a real one.

**VECTORIZED MIDDLE LOOP** (:func:`_evaluate_level` ->
:func:`~bep_reliability_engine.evaluator.evaluate_batch`): each level is one
``evaluate_batch`` call across all N realizations, bit-identical to looping the
scalar ``evaluate_realization`` (locked by
``test_orchestration_matches_reference_loop``), so the spec §8 Phase-2 idiom
(per-row ``evaluate_realization``) and the M9 row-bootstrap are unaffected.

Persistence (spec §2, §8; confirmed decisions)
----------------------------------------------
The run always returns the in-memory :class:`FragilityResult` (the spec §9
notebook idiom). With ``persist=True`` (default) it also writes one HDF5 + JSON
sidecar via M9's :meth:`FragilityResult.save`, to ``output_path`` or, if omitted,
``config.output.results_dir / f"{cross_section_id}_{scenario}.h5"``. The path is
**resolved and guarded before the expensive sweep** (fail fast): an existing
result file (or its sidecar) is **never silently overwritten** — it raises
``FileExistsError`` unless ``overwrite=True``.

**Crash recovery (raw payload before fitting).** The sweep is the expensive
part; the M9 fitting/bootstrap that follows can fail on a tail-dominated grid.
A persisting run therefore writes the raw payload (theta matrix, grid, both
failure matrices, metadata) to ``<output>.raw.h5`` + ``.raw.json`` *before*
:func:`~bep_reliability_engine.fragility.assemble_fragility` is called, so an
assembly failure can never destroy a completed sweep. On success the recovery
pair is removed once the full result is saved.

Deferred decisions recorded for the decision log
-------------------------------------------------
* **Bootstrap settings deferral (accepted).** ``n_bootstrap`` and ``confidence``
  are not yet :class:`Config` fields; they are fixed here to
  :data:`_BOOTSTRAP_N` / :data:`_BOOTSTRAP_CONFIDENCE`, the bootstrap seed is
  derived from ``config.mc.seed``, and all three are recorded under
  ``metadata['bootstrap']`` so the bands stay config-reproducible. Promoting
  them to :class:`Config` is a clean follow-up.
* **M3 determinism constraint (discharged).** Event selection is
  config-pinned (``canonical_event_ids[0]``, ADR-0020 §5) and the per-level
  scaling is a pure function, so parallel == serial holds on the real path by
  construction (locked by the n_jobs-invariance test, gap G4).

References
----------
Spec §3 (execution sequence), §4 (shared preamble then branch), §6
(vectorization/parallelization), §8 (Phase 2 handoff, persistence), §9
(``run_fragility_analysis`` entry point), §11 (timestep/native_dt), §12
(failure mode 6 trajectory memory; Tradeoff 1 numpy-vs-JIT). ADR-0001
(c_e_stochastic), ADR-0002 (shared-sample contract), ADR-0013 (native_dt /
target_dt), ADR-0014 (aquifer-lag deferred; instantaneous head in Phase 1).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

import numpy as np
from joblib import Parallel, delayed
from numpy.typing import NDArray
from tqdm import tqdm

from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import evaluate_batch
from bep_reliability_engine.fragility import (
    FragilityResult,
    assemble_fragility,
    save_raw_failure_payload,
)
from bep_reliability_engine.hydraulics import (
    aquifer_response_diagnostic,
    aquifer_response_time,
    leakage_length_in,
    leakage_length_out,
)
from bep_reliability_engine.hydrographs import (
    CanonicalShape,
    HydrographRecord,
    conditioning_record_for_level,
    flood_timescales,
    load_canonical_shape,
    resample_record,
    validate_datum_consistency,
)
from bep_reliability_engine.sampling import (
    ThetaSample,
    sample_seepage_length,
    sample_theta,
)

logger = logging.getLogger(__name__)

__all__ = [
    "conditioning_hydrographs_for_config",
    "run_fragility_analysis",
    "seepage_length_samples_for_config",
]

# Provenance markers stamped into metadata['hydrograph_source'] so a
# synthetic-stub run is never mistaken for a real d4PDF-driven result and
# vice versa (module docstring: the two config-selected paths).
_SOURCE_SYNTHETIC: str = "phase1_synthetic_stub"
_SOURCE_D4PDF: str = "d4pdf_scaled_canonical"

# M3-stub shape constants (placeholder physics only). 10 min native resolution is
# the spec §11 field-scale default; the duration is a multi-day compound-event
# stand-in long enough to drive progression across the conditioning grid.
_STUB_NATIVE_DT_S: float = 600.0
_STUB_DURATION_HOURS: float = 60.0

# Height of the leading precursor peak as a fraction of the main peak in the
# synthetic two-peak compound event: a smaller precursor then the larger main
# (typhoon) peak, which reaches level_m. < 1 makes the event asymmetric.
_STUB_PRECURSOR_FRACTION: float = 0.5

# Bootstrap settings (deferred from Config; recorded in metadata). M9 defaults
# are (1000, 0.95); pinned explicitly here so the recorded provenance is truthful
# regardless of any future change to the M9 defaults.
_BOOTSTRAP_N: int = 1000
_BOOTSTRAP_CONFIDENCE: float = 0.95

# Phase 1 prior fragility integrates every event from a virgin blanket (spec §5).
_L_INI_M: float = 0.0

# Salt for the stochastic-L seed: derived from config.mc.seed via SeedSequence so
# the seepage-length draw is reproducible AND independent of the 7-D theta LHS
# (review item #3). Keeping it front-loaded in the main process preserves the
# parallel == serial guarantee.
_SEEPAGE_LENGTH_SEED_SALT: int = 0x5EE_1E9


@dataclass(frozen=True)
class _EvalSettings:
    """Per-run evaluation knobs handed to every conditioning-level task.

    Constant across the conditioning grid, so one instance is built in the main
    process and passed to each :func:`_evaluate_level` task (picklable for loky;
    the large ``seepage_length_samples`` array is memmapped read-only by loky).

    Attributes
    ----------
    l_ini_m : float
        Initial pipe length [m] (0 for Phase 1 prior fragility).
    seepage_length_samples : numpy.ndarray or None
        Per-realization stochastic L [m], or None for deterministic geometry.L.
    alpha_exponent, theta_repose_rad, relative_density : float
        Deterministic run-owned Sellmeijer inputs threaded to M6 (ADR-0015,
        review item #6). gamma'_p stays the basin-wide pinned M6 constant
        (16.87, review item #10), so it is not carried here.
    alpha_exponent_transient : float or None
        Transient-only scale-exponent override (ADR-0017). None keeps the
        single-source H_c (baseline); a value (e.g. -1/2) drives the
        dimensional-bias decomposition.
    foreland_open : bool
        ADR-0025 foreland treatment: False = blanketed baseline (the adopted
        production setting), True = the open-entry (x1 = 0) on-demand
        sensitivity, from ``config.foreland_treatment``.
    progression_backend : str
        M7 batch-timestepper backend from
        ``config.timestepper.progression_backend`` (ADR-0029): 'numpy'
        (reference, bit-identical to the scalar loop) or 'numba'
        (JIT-parallel, < 1e-10 equivalence, recorded in metadata via the
        config snapshot).
    """

    l_ini_m: float
    seepage_length_samples: NDArray[np.float64] | None
    alpha_exponent: float
    theta_repose_rad: float
    relative_density: float
    alpha_exponent_transient: float | None
    foreland_open: bool
    progression_backend: str


# ============================================================================
# PER-LEVEL HYDROGRAPH CONSTRUCTION — two config-selected paths (module
# docstring): the canonical d4PDF shape (production; hydrograph_source set) or
# the legacy synthetic stub (plumbing/dev; hydrograph_source None). Both build
# a concrete M3 HydrographRecord in the main process.
# ============================================================================
def _load_canonical_or_none(config: Config) -> CanonicalShape | None:
    """Load the run's canonical d4PDF shape once, or None for the stub path.

    Called **once per run, in the main process, before any expensive work**:

    * ``config.hydrograph_source`` is None -> None (the synthetic-stub path;
      the only path available to pre-ADR-0020 configs).
    * Otherwise the **first** canonical event (ADR-0020 ordered-list
      semantics) is loaded at the node's KP via
      :func:`~bep_reliability_engine.hydrographs.load_canonical_shape`, and
      the MSL datum guard runs immediately: real d4PDF stages are m MSL
      (ADR-0019 §3), so an unresolved provisional ``z_toe = 0.0`` raises here
      — fail fast — rather than silently driving M8 with ~35 m heads (gap G2).

    Returns
    -------
    CanonicalShape or None
        The loaded, datum-checked shape, or None for the stub path.
    """
    if config.hydrograph_source is None:
        return None
    source = config.hydrograph_source
    canonical = load_canonical_shape(
        source.data_root,
        river=source.river,
        kp=source.kp,
        event_id=source.canonical_event_ids[0],
    )
    validate_datum_consistency(canonical.source_record, config.geometry.z_toe)
    return canonical


def _hydrograph_for_level(
    level_m: float, config: Config, canonical: CanonicalShape | None = None
) -> HydrographRecord:
    """Build the loading record for conditioning level ``level_m``.

    Pure, deterministic function of its arguments (no RNG, no I/O — the
    canonical shape was already loaded by :func:`_load_canonical_or_none`),
    which is what keeps the parallel sweep identical to a serial run.

    **Canonical path** (``canonical`` given): the pure G1 rescaling via
    :func:`~bep_reliability_engine.hydrographs.conditioning_record_for_level`
    — ``h(t) = h_base + (level_m - h_base) * shape(t)``, trough floor pinned
    at the section's base-flow stage h_base (ADR-0021 item 4), ``peak =
    level_m`` verbatim (ADR-0010), full source window. When
    ``config.timestepper.target_dt_seconds`` is set the built record is then
    refined onto that grid via
    :func:`~bep_reliability_engine.hydrographs.resample_record` (the ADR-0013
    record-construction hook; integration-Δt policy per ADR-0030 — linear
    interpolation, loading signal unchanged, forward-Euler grid refined).

    **Stub path** (``canonical`` None): the legacy synthetic **two-peak
    compound event** — two raised-cosine bumps separated by an inter-peak
    trough at the polder baseline ``config.geometry.z_toe``, a smaller leading
    precursor peak (``_STUB_PRECURSOR_FRACTION`` of full height) then the
    larger main peak at ``level_m``. Not physical, but the two-peak shape
    deliberately exercises the spec §5 compound-event memory model (gate
    closes in the trough, progression resumes through the ``l_current > 0``
    clause). Native timestep per ADR-0013:
    ``config.timestepper.target_dt_seconds`` when set, else
    :data:`_STUB_NATIVE_DT_S`.

    Parameters
    ----------
    level_m : float
        Conditioning level h_i; becomes ``peak`` on both paths. MSL stage on
        the canonical path; the legacy above-datum convention on the stub path.
    config : Config
        The run configuration (M1).
    canonical : CanonicalShape, optional
        The run's loaded canonical shape (None -> stub path).

    Returns
    -------
    HydrographRecord
        The level's loading record, ``peak`` set exactly to ``level_m``.
    """
    if canonical is not None:
        record = conditioning_record_for_level(
            canonical, level_m, scenario=config.scenario
        )
        if config.timestepper.target_dt_seconds is not None:
            record = resample_record(record, config.timestepper.target_dt_seconds)
        return record

    z_toe_m = float(config.geometry.z_toe)
    native_dt_s = (
        float(config.timestepper.target_dt_seconds)
        if config.timestepper.target_dt_seconds is not None
        else _STUB_NATIVE_DT_S
    )
    n_steps = max(6, int(round(_STUB_DURATION_HOURS * 3600.0 / native_dt_s)))
    t = np.arange(n_steps, dtype=np.float64) * native_dt_s
    # Two raised-cosine humps (each 0 at its ends, 1 at its centre) concatenated,
    # so the join is an inter-peak trough back at the baseline. The first hump is
    # scaled down to a precursor, leaving the global max on the second (main) hump;
    # normalising then puts the main peak at exactly 1, anchored to level_m.
    n_first = n_steps // 2
    hump_first = 0.5 * (1.0 - np.cos(np.linspace(0.0, 2.0 * np.pi, n_first)))
    hump_second = 0.5 * (1.0 - np.cos(np.linspace(0.0, 2.0 * np.pi, n_steps - n_first)))
    shape = np.concatenate([_STUB_PRECURSOR_FRACTION * hump_first, hump_second])
    shape /= shape.max()
    h = z_toe_m + (level_m - z_toe_m) * shape
    return HydrographRecord(
        t=t,
        h=h,
        peak=float(level_m),
        duration_hours=float(n_steps * native_dt_s / 3600.0),
        scenario=config.scenario,
        event_id=f"stub_h{level_m:g}",
        native_dt=float(native_dt_s),
        provenance={"source": _SOURCE_SYNTHETIC},
    )


# ============================================================================
# END PER-LEVEL HYDROGRAPH CONSTRUCTION
# ============================================================================


# ============================================================================
# VECTORIZED EVALUATION (was the scalar seam). The middle loop is now a single
# vectorized M8 ``evaluate_batch`` call per conditioning level, advancing all N
# realizations through the already-vectorized M4/M6/M7 kernels in one pass (spec
# §6, review item #5). It is bit-identical to looping the scalar
# ``evaluate_realization`` over the rows — locked end to end by
# ``tests/test_run.py::test_orchestration_matches_reference_loop``.
# ============================================================================
def _evaluate_level(
    level_index: int,
    hydrograph: HydrographRecord,
    theta_matrix: NDArray[np.float64],
    geometry: dict[str, float],
    settings: _EvalSettings,
) -> tuple[int, NDArray[np.bool_], NDArray[np.bool_]]:
    """Outer-loop task: one conditioning level, all N realizations (vectorized).

    Module-level (picklable for loky): evaluates the realizations against the
    already-built ``hydrograph`` (constructed in the main process, not here)
    via one :func:`~bep_reliability_engine.evaluator.evaluate_batch` call,
    and returns its own ``level_index`` so the caller can assemble the failure
    matrices by index, independent of task completion order (the reproducibility
    guarantee). Only the two boolean failure columns are kept — the bulk run
    retains neither diagnostics nor trajectories (spec §12 failure mode 6).

    Parameters
    ----------
    level_index : int
        Column index of this level in the (N, N_h) failure matrices.
    hydrograph : HydrographRecord
        This level's loading record, built once in the main process by
        :func:`_hydrograph_for_level` (``peak`` == the conditioning level).
    theta_matrix : numpy.ndarray, shape (N, 7)
        The shared prior population (read-only).
    geometry : dict of str to float
        The flat M8 geometry dict.
    settings : _EvalSettings
        The run-constant evaluation knobs (l_ini, stochastic-L samples, and the
        threaded Sellmeijer inputs), shared across every level.

    Returns
    -------
    tuple of (int, numpy.ndarray, numpy.ndarray)
        ``(level_index, col_static, col_trans)`` with both columns shape (N,)
        and dtype bool.
    """
    col_static, col_trans = evaluate_batch(
        theta_matrix,
        hydrograph,
        geometry,
        l_ini=settings.l_ini_m,
        seepage_length_samples=settings.seepage_length_samples,
        alpha_exponent=settings.alpha_exponent,
        alpha_exponent_transient=settings.alpha_exponent_transient,
        theta_repose_rad=settings.theta_repose_rad,
        relative_density=settings.relative_density,
        foreland_open=settings.foreland_open,
        progression_backend=settings.progression_backend,
    )
    return level_index, col_static, col_trans


def _sample_prior(config: Config) -> ThetaSample:
    """Draw the (N, 7) prior once from the config (the M2 boundary, spec §2)."""
    return sample_theta(
        config.priors.to_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    )


def _sample_seepage_length_or_none(config: Config) -> NDArray[np.float64] | None:
    """Draw the stochastic seepage length L, or None when L is deterministic.

    Returns None when ``config.seepage_length_cov`` is unset (L stays the scalar
    ``config.geometry.L`` for every realization). Otherwise draws the ``(N,)``
    lognormal L (mean ``geometry.L``, cov ``seepage_length_cov``) with a seed
    derived from ``config.mc.seed`` via ``SeedSequence`` so it is reproducible
    and independent of the theta LHS (review item #3). Front-loaded in the main
    process, like the theta draw, so the parallel sweep stays bit-reproducible.
    """
    if config.seepage_length_cov is None:
        return None
    l_seed = int(
        np.random.SeedSequence(
            [config.mc.seed, _SEEPAGE_LENGTH_SEED_SALT]
        ).generate_state(1)[0]
    )
    return sample_seepage_length(
        config.geometry.L,
        config.seepage_length_cov,
        seed=l_seed,
        n_samples=config.mc.n_samples,
    )


def seepage_length_samples_for_config(config: Config) -> NDArray[np.float64] | None:
    """Regenerate the run's stochastic seepage-length draw from its config.

    Public re-entry point for the exact per-realization L vector a
    :func:`run_fragility_analysis` run paired with theta row j (ADR-0034):
    the draw is fully determined by ``config.mc.seed`` (via the same
    ``SeedSequence`` salt), ``config.geometry.L``, ``config.seepage_length_cov``
    and ``config.mc.n_samples``, and the L samples are deliberately **not**
    persisted in the FragilityResult, so downstream consumers (the Phase 2
    survival replay, which must re-run M8 under identical assumptions)
    regenerate them through this function rather than re-deriving the seed
    recipe. Returns None when L is deterministic
    (``config.seepage_length_cov`` unset), exactly like the run itself.

    Parameters
    ----------
    config : Config
        The run configuration; for a persisted run, reconstruct it from the
        metadata snapshot via ``Config.model_validate(metadata['config'])``.

    Returns
    -------
    numpy.ndarray of shape (N,) or None
        The identical L vector the run used, or None for deterministic L.
    """
    return _sample_seepage_length_or_none(config)


def conditioning_hydrographs_for_config(config: Config) -> list[HydrographRecord]:
    """Build the run's per-level loading records, exactly as the sweep did.

    Public re-entry point for the conditioning-grid hydrographs of a
    :func:`run_fragility_analysis` run (ADR-0034): the canonical shape is
    loaded once (datum-guarded) and each grid level's record is built by the
    same :func:`_hydrograph_for_level` path the sweep used, including the
    ADR-0030 ``target_dt_seconds`` refinement. Exists for the Phase 2
    posterior-fragility **verification** mode, which re-evaluates accepted
    rows on the identical grid records and must reproduce the retained
    failure matrices bit for bit.

    Parameters
    ----------
    config : Config
        The run configuration (reconstructable from the metadata snapshot).

    Returns
    -------
    list of HydrographRecord
        One record per conditioning level, in grid order; ``record.peak``
        equals the level verbatim.

    Raises
    ------
    ValueError
        Propagated from the canonical-shape loading or the MSL datum guard,
        exactly as in :func:`run_fragility_analysis`.
    """
    canonical = _load_canonical_or_none(config)
    return [
        _hydrograph_for_level(float(level_m), config, canonical)
        for level_m in config.mc.conditioning_grid
    ]


def _leakage_geometry_block(
    theta_sample: ThetaSample,
    seepage_length_samples: NDArray[np.float64] | None,
    config: Config,
) -> dict[str, float | str]:
    """ADR-0006 (amended 2026-07-05) leakage-geometry record — descriptive only.

    The predecessor of this block was an L/lambda_in "validity" alarm; the
    amendment withdrew it as a category error (L is the exact linear USACE-L2
    base-width term of the ratio form and carries no smallness condition; the
    genuine finite-extent corrections act on the foreland and hinterland
    extents). What remains worth recording per run is the *geometry* behind
    r_e over the sampled prior: the median leakage lengths, the foreland tanh
    credit (how far B_f is from semi-infinite), the median shares of the
    three r_e denominator terms, the descriptive L/lambda_in (reported, NOT a
    gate), and the hinterland semi-infinite assumption with the 3*lambda_in
    extent threshold its site verification needs — auto-generating the
    numbers the L3 resolution reads. Nothing here warns and nothing gates;
    the block goes to ``metadata['leakage_geometry']``.

    When L is stochastic the per-realization L_j pairs with theta_j
    row-for-row, exactly as in the evaluation itself.
    """
    lambda_in = leakage_length_in(
        theta_sample.column("k_aq"),
        theta_sample.column("D_aq"),
        theta_sample.column("D_bl"),
        theta_sample.column("k_bl"),
    )
    lambda_out = leakage_length_out(
        theta_sample.column("k_aq"),
        theta_sample.column("D_aq"),
        config.geometry.D_fore,
        config.geometry.k_fore,
        np.inf,  # semi-infinite reference for the tanh-credit ratio
    )
    lambda_out_eff = leakage_length_out(
        theta_sample.column("k_aq"),
        theta_sample.column("D_aq"),
        config.geometry.D_fore,
        config.geometry.k_fore,
        config.geometry.foreshore_width,
    )
    if config.foreland_treatment == "open_entry":
        # ADR-0025 sensitivity: record the geometry the run actually uses
        # (x1 = 0), not the blanketed value the measured foreshore would give.
        lambda_out_eff = np.zeros_like(lambda_in)
    seepage: NDArray[np.float64] | float = (
        seepage_length_samples
        if seepage_length_samples is not None
        else float(config.geometry.L)
    )
    denominator = lambda_out_eff + seepage + lambda_in
    median_lambda_in = float(np.median(lambda_in))
    block: dict[str, float | str] = {
        "median_lambda_in_m": median_lambda_in,
        "median_lambda_out_eff_m": float(np.median(lambda_out_eff)),
        "foreshore_width_m": float(config.geometry.foreshore_width),
        "median_foreland_tanh_credit": float(np.median(lambda_out_eff / lambda_out)),
        "median_L_over_lambda_in": float(np.median(seepage / lambda_in)),
        "denominator_share_foreland_median": float(
            np.median(lambda_out_eff / denominator)
        ),
        "denominator_share_base_L_median": float(np.median(seepage / denominator)),
        "denominator_share_hinterland_median": float(
            np.median(lambda_in / denominator)
        ),
        "hinterland_assumption": "semi_infinite",
        "hinterland_semi_infinite_threshold_m": 3.0 * median_lambda_in,
    }
    logger.info(
        "Leakage geometry (ADR-0006): median lambda_in %.3g m, lambda_out_eff "
        "%.3g m (tanh credit %.2f); denominator shares foreland/L/hinterland "
        "%.2f/%.2f/%.2f; hinterland semi-infinite needs >= %.0f m.",
        block["median_lambda_in_m"],
        block["median_lambda_out_eff_m"],
        block["median_foreland_tanh_credit"],
        block["denominator_share_foreland_median"],
        block["denominator_share_base_L_median"],
        block["denominator_share_hinterland_median"],
        block["hinterland_semi_infinite_threshold_m"],
    )
    return block


def _aquifer_response_block(
    config: Config,
    theta_sample: ThetaSample,
    canonical: CanonicalShape | None,
) -> dict[str, Any]:
    """ADR-0032 aquifer-response diagnostic record — descriptive; gates nothing.

    Records, per run, the evidence behind the M4 instantaneous-vs-lag choice
    (spec §11): the pre-registered analytic verdict from
    :func:`hydraulics.aquifer_response_diagnostic` at this section's prior means
    and the driver S_s, enriched with empirical τ_aq percentiles over the drawn
    prior (τ_aq = S_s·D_aq·D_bl/k_bl per realization) and the rising-limb /
    plateau timescales measured on the canonical loading shape. It makes the
    instantaneous default an *evidenced* decision carried in every result,
    rather than an inherited assumption. The actual translation form the run
    used is the separate global ``metadata['aquifer_lag_active']`` flag.

    On the synthetic-stub path (``canonical is None``) the loading timescales
    are unavailable, so Π and the verdict degrade to ``timescales_unavailable``
    while the τ_aq magnitudes are still recorded.
    """
    specs = {m.name: m for m in config.priors.to_marginal_specs()}
    if canonical is not None:
        record = canonical.source_record
        ts = flood_timescales(record.h, record.native_dt)
        t_rise_s: float | None = ts["rising_limb_s"]
        t_plateau_s: float | None = ts["plateau_s"]
        native_dt_s: float | None = float(record.native_dt)
    else:
        ts = {}
        t_rise_s = t_plateau_s = native_dt_s = None

    block = aquifer_response_diagnostic(
        segment_id=config.segment_id,
        d_aq_mean_m=specs["D_aq"].mean,
        d_bl_mean_m=specs["D_bl"].mean,
        k_bl_mean_mps=specs["k_bl"].mean,
        d_aq_cov=specs["D_aq"].cov,
        d_bl_cov=specs["D_bl"].cov,
        k_bl_cov=specs["k_bl"].cov,
        t_rise_s=t_rise_s,
        t_plateau_s=t_plateau_s,
        native_dt_s=native_dt_s,
    )

    # Empirical τ_aq over the actual production sample at the driver S_s: the
    # tail the analytic central/corner points summarize (τ_aq depends only on
    # D_aq, D_bl, k_bl; k_aq cancels).
    tau_sample = aquifer_response_time(
        theta_sample.column("D_aq"),
        theta_sample.column("D_bl"),
        theta_sample.column("k_bl"),
        block["s_s_driver_per_m"],
    )
    block["tau_aq_sample_pctl_s"] = {
        "p50": float(np.percentile(tau_sample, 50)),
        "p90": float(np.percentile(tau_sample, 90)),
        "p99": float(np.percentile(tau_sample, 99)),
        "max": float(np.max(tau_sample)),
    }
    if ts:
        block["rise_10_90_s"] = ts["rise_10_90_s"]
        block["fwhm_s"] = ts["fwhm_s"]

    logger.info(
        "Aquifer response (ADR-0032): tau_aq central %.0f s / corner90 %.0f s "
        "@ S_s=%.0e; T_rise %s; Pi_central %s; verdict '%s' (lag_active=%s).",
        block["tau_aq_central_s"],
        block["tau_aq_corner90_s"],
        block["s_s_driver_per_m"],
        "n/a" if t_rise_s is None else f"{t_rise_s:.0f} s",
        "n/a" if block["pi_central"] is None else f"{block['pi_central']:.3f}",
        block["verdict"],
        config.timestepper.aquifer_lag_active,
    )
    return block


def _code_version() -> str:
    """Return the installed package version, or ``'unknown'`` if not installed."""
    try:
        return importlib_metadata.version("bep_reliability_engine")
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


def _resolve_output_path(config: Config, output_path: str | Path | None) -> Path:
    """Resolve the HDF5 destination (explicit, else derived from config, spec §8).

    The derived path is ``results_dir / f"{cross_section_id}_{scenario}.h5"`` with
    ``'+'`` mapped to ``'plus'`` so ``'+4K'`` yields a filesystem-safe stem.
    """
    if output_path is not None:
        return Path(output_path)
    scenario_tag = config.scenario.replace("+", "plus")
    stem = f"{config.cross_section_id}_{scenario_tag}"
    return Path(config.output.results_dir) / f"{stem}.h5"


def _guard_no_overwrite(path: Path, overwrite: bool) -> None:
    """Refuse to clobber an existing result (or its JSON sidecar) unless asked.

    Raises before the expensive sweep so a prior run is never silently lost.
    """
    sidecar = path.with_suffix(".json")
    existing = [str(p) for p in (path, sidecar) if p.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing result file(s) {existing} from a "
            "prior run; pass overwrite=True to replace them, or choose another "
            "output_path."
        )


def _build_metadata(
    config: Config,
    theta_sample: ThetaSample,
    runtime_seconds: float,
    n_jobs: int,
    seepage_length_stochastic: bool,
    canonical: CanonicalShape | None,
    leakage_geometry: dict[str, float | str],
    aquifer_response: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the spec §8 provenance block for the FragilityResult sidecar.

    Merges the full config snapshot and hash, the M2 sampling provenance, runtime
    fields, the loud hydrograph-source marker plus the full shape provenance
    (gap G5; ADR-0019 §9 scenario tags and §1 member provenance flow through
    here), and the deferred bootstrap settings.

    The assembled dict is **canonicalized to JSON-native types** before return
    (``json.loads(json.dumps(...))`` — the same operation M9's save/load applies),
    so the in-memory metadata equals what reloads from the sidecar. Without this,
    the sampling block's ``bounds`` are tuples that JSON normalizes to lists on
    reload, and a strict ``loaded.metadata == result.metadata`` check (the M9
    round-trip contract) would fail on a run produced here. It also surfaces any
    non-serializable value here rather than later at ``save`` time.
    """
    metadata = {
        "config": config.to_metadata(),
        "config_hash": config.config_hash(),
        "sampling": theta_sample.metadata,
        "code_version": _code_version(),
        "runtime_seconds": float(runtime_seconds),
        "n_jobs": int(n_jobs),
        "engine": "run_fragility_analysis",
        # spec §8 attrs surfaced at top level for convenient stratification.
        "cross_section_id": config.cross_section_id,
        "segment_id": config.segment_id,
        "scenario": config.scenario,
        "remediation_state": config.remediation_state,
        "d70_interpretation": config.priors.d70_interpretation,
        "lhs_seed": int(config.mc.seed),
        "correlation_rho_k_d70": float(config.correlation.rho_log_kaq_d70),
        # ADR-0012 (accepted 2026-07-03): the empirical OYO paired-record
        # analysis adopted the two-population decoupling — matrix d_70 and
        # framework k_aq sampled decoupled, rho recorded as 0.0 but never
        # imposed (metadata['sampling']['rho_imposed'] is False). This status
        # replaces the former provisional_pending_adr_0012 marker; runs
        # persisted before ADR-0012 still carry that older marker and are not
        # retroactively re-blessed.
        "correlation_rho_k_d70_status": "empirical_two_population_adr_0012",
        # ADR-0006 (amended 2026-07-05): descriptive leakage geometry behind
        # r_e (medians, denominator shares, foreland tanh credit, hinterland
        # semi-infinite status). Records only; the former L/lambda_in alarm
        # was withdrawn as a category error by the amendment.
        "leakage_geometry": dict(leakage_geometry),
        "c_e_stochastic": True,
        # ADR-0029: which M7 batch backend produced the failure matrices.
        # 'numpy' is the bit-identical reference; 'numba' is equivalent to
        # < 1e-10 only, so the marker keeps the two distinguishable forever.
        "progression_backend": config.timestepper.progression_backend,
        "aquifer_lag_active": bool(config.timestepper.aquifer_lag_active),
        "tau_aq": None,  # lag inactive in Phase 1 (ADR-0014); from S_s when active.
        # ADR-0032: the spec §11 aquifer-response diagnostic that justifies the
        # instantaneous default. tau_aq magnitudes, the flood timescales, Pi vs
        # the pre-registered threshold, and the per-section verdict — descriptive
        # evidence, distinct from the global aquifer_lag_active flag above.
        "aquifer_response": dict(aquifer_response),
        # Sellmeijer inputs threaded to M6 (review #6); gamma'_p stays the pinned
        # basin-wide M6 constant 16.87 (review #10), not run-varying.
        "alpha_exponent": float(config.alpha_exponent),
        # Transient-only scale exponent for the dimensional-bias decomposition
        # (ADR-0017); None = single-source H_c (baseline).
        "alpha_exponent_transient": (
            None
            if config.alpha_exponent_transient is None
            else float(config.alpha_exponent_transient)
        ),
        "dimensional_decomposition_active": config.alpha_exponent_transient is not None,
        "theta_repose_deg": float(config.theta_repose_deg),
        "relative_density_insitu": float(config.relative_density_insitu),
        # ADR-0025: which foreland entry physics ran. 'blanketed_tanh' is the
        # adopted baseline; 'open_entry' marks the on-demand KP 62.0
        # sensitivity so its results can never masquerade as baseline.
        "foreland_treatment": config.foreland_treatment,
        # Stochastic seepage length L (review #3); mean lives in geometry.L.
        "seepage_length": {
            "stochastic": bool(seepage_length_stochastic),
            "mean_m": float(config.geometry.L),
            "cov": (
                None
                if config.seepage_length_cov is None
                else float(config.seepage_length_cov)
            ),
        },
        # Hydrograph path marker + full shape provenance (gap G5). The 'scenario'
        # key above is the RUN identity; the canonical shape's own source
        # experiment/scenario (HPB/'historical' for the approved events, driving
        # both scenarios by design) lives inside the provenance block.
        "hydrograph_source": (
            _SOURCE_SYNTHETIC if canonical is None else _SOURCE_D4PDF
        ),
        "hydrograph": (
            None
            if canonical is None
            else {
                "shape_event_id": canonical.source_record.event_id,
                # Ordered ADR-0020 list: [0] is the shape used above; the rest
                # are the approved alternates recorded for provenance.
                "canonical_event_ids": list(
                    config.hydrograph_source.canonical_event_ids
                ),
                "h_base_m_msl": float(canonical.h_base_m),
                "source_peak_stage_m_msl": float(canonical.source_record.peak),
                "native_dt_s": float(canonical.source_record.native_dt),
                "duration_hours": float(canonical.source_record.duration_hours),
                "provenance": dict(canonical.source_record.provenance),
            }
        ),
        "bootstrap": {
            "n_bootstrap": int(_BOOTSTRAP_N),
            "confidence": float(_BOOTSTRAP_CONFIDENCE),
            "seed": int(config.mc.seed),
            "note": (
                "n_bootstrap/confidence are not yet Config fields (deferred, "
                "accepted); seed derived from config.mc.seed."
            ),
        },
    }
    return json.loads(json.dumps(metadata))


def run_fragility_analysis(
    config: Config,
    *,
    n_jobs: int = 1,
    progress: bool = True,
    output_path: str | Path | None = None,
    overwrite: bool = False,
    persist: bool = True,
) -> FragilityResult:
    """Run the full Phase 1 fragility analysis for one config (spec §3, §9).

    Samples the prior once, sweeps the conditioning grid (parallel over levels),
    aggregates the per-realization static/transient failure indicators into the
    two (N, N_h) matrices, and assembles + (by default) persists the
    :class:`FragilityResult` Phase 2 handoff. Returns the result in memory either
    way (spec §9 notebook idiom).

    Reproducibility is by construction: the only RNG (the prior draw and the M9
    bootstrap) runs in the main process; the per-(level, realization) evaluation
    is a pure deterministic function and the stub hydrograph is deterministic;
    aggregation is index-addressed. The result is therefore **identical for any**
    ``n_jobs`` (see the module docstring).

    .. warning::
       With ``config.hydrograph_source`` unset the transient loading is the
       legacy **synthetic stub**
       (``metadata['hydrograph_source'] == 'phase1_synthetic_stub'``) and the
       curves validate the engine plumbing, not site physics. Production runs
       set the block (ADR-0020) and are stamped ``'d4pdf_scaled_canonical'``.

    Parameters
    ----------
    config : Config
        The validated run configuration (M1). Fully determines the sampled prior
        and the conditioning grid.
    n_jobs : int, optional
        Worker count for the ``joblib`` sweep over conditioning levels. Default 1
        (serial; cleanest tracebacks for development). Any value yields identical
        results; ``-1`` uses all cores.
    progress : bool, optional
        Show a ``tqdm`` progress bar over the conditioning levels. Default True.
    output_path : str or pathlib.Path, optional
        Explicit HDF5 destination. When ``None`` (default) and ``persist`` is
        True, the path is derived from ``config.output.results_dir`` and the run
        identity. Ignored when ``persist`` is False.
    overwrite : bool, optional
        Allow replacing an existing result file (or its JSON sidecar). Default
        False: an existing file raises ``FileExistsError`` *before* the sweep.
    persist : bool, optional
        Write the result to disk via :meth:`FragilityResult.save`. Default True.
        Set False to obtain the in-memory result only (tests, exploration).

    Returns
    -------
    FragilityResult
        The fitted static/transient fragility curves with bootstrap bands and the
        retained ``theta_matrix`` and both failure matrices (spec §2, §8).

    Raises
    ------
    FileExistsError
        If ``persist`` and the resolved output (or its sidecar) already exists and
        ``overwrite`` is False.
    ValueError
        If the canonical shape cannot be loaded (missing data, unknown event)
        or the MSL datum guard trips (``z_toe`` still the provisional 0.0 with
        real MSL stages, gap G2) — both raised **before** the sweep; or,
        propagated from M9, if a fragility branch has fewer than two interior
        (``0 < P_f < 1``) conditioning levels — i.e. the grid does not bracket
        the transition for that branch.
    """
    # 1. Resolve and guard the output path BEFORE any expensive work (fail fast,
    #    so a long run is never lost to a refused write at the end).
    resolved_path: Path | None = None
    if persist:
        resolved_path = _resolve_output_path(config, output_path)
        _guard_no_overwrite(resolved_path, overwrite)

    # 1b. Load the canonical d4PDF shape ONCE (main process) and run the MSL
    #     datum guard — also before any expensive work. None => stub path.
    canonical = _load_canonical_or_none(config)

    # 2. Sample theta ONCE, and the stochastic seepage length L ONCE (front-load
    #    all RNG in the main process; both shared read-only across every level).
    theta_sample = _sample_prior(config)
    theta_matrix = theta_sample.theta_matrix
    n_samples = theta_sample.n_samples
    seepage_length_samples = _sample_seepage_length_or_none(config)

    # 2b. ADR-0006 (amended) leakage-geometry record: the descriptive geometry
    #     behind r_e over the sampled prior, computed once for the whole run
    #     (lambda_in is level-independent). Records, never gates or warns —
    #     the former L/lambda_in alarm was a category error (amendment).
    leakage_geometry = _leakage_geometry_block(
        theta_sample, seepage_length_samples, config
    )

    # 2c. ADR-0032 aquifer-response diagnostic: the spec §11 evidence behind the
    #     M4 instantaneous-vs-lag choice (tau_aq vs the flood rising-limb time),
    #     computed once per run and recorded. Descriptive; the active form is the
    #     global config.timestepper.aquifer_lag_active flag.
    aquifer_response = _aquifer_response_block(config, theta_sample, canonical)

    # 3. Shared, read-only per-level inputs and the run-constant eval settings
    #    (l_ini, stochastic-L samples, threaded Sellmeijer inputs; review #3/#6).
    geometry = config.geometry.as_evaluator_dict()
    settings = _EvalSettings(
        l_ini_m=_L_INI_M,
        seepage_length_samples=seepage_length_samples,
        alpha_exponent=config.alpha_exponent,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        alpha_exponent_transient=config.alpha_exponent_transient,
        foreland_open=config.foreland_treatment == "open_entry",
        progression_backend=config.timestepper.progression_backend,
    )
    grid = np.asarray(config.mc.conditioning_grid, dtype=np.float64)
    n_levels = int(grid.size)

    logger.info(
        "Fragility run: N=%d realizations x N_h=%d levels (n_jobs=%s, source=%s).",
        n_samples,
        n_levels,
        n_jobs,
        _SOURCE_SYNTHETIC if canonical is None else _SOURCE_D4PDF,
    )

    # 4. Outer loop over conditioning levels (parallel). Each level's hydrograph
    #    is built once in THIS (main) process — delayed() evaluates its arguments
    #    here before dispatch — and the built record is handed to the worker; the
    #    canonical shape (or the stub construction) never crosses into workers.
    #    tqdm wraps the task iterable; joblib pulls from it as workers free up,
    #    tracking progress for any n_jobs. n_jobs=1 forces fully serial execution
    #    (the reproducibility-check path).
    level_iter: Any = enumerate(grid)
    if progress:
        level_iter = tqdm(
            level_iter, total=n_levels, desc="conditioning levels", unit="level"
        )

    start = time.perf_counter()
    level_results = Parallel(n_jobs=n_jobs)(
        delayed(_evaluate_level)(
            level_index,
            _hydrograph_for_level(float(level_m), config, canonical),  # main process
            theta_matrix,
            geometry,
            settings,
        )
        for level_index, level_m in level_iter
    )
    runtime_seconds = time.perf_counter() - start

    # 5. Aggregate into the (N, N_h) failure matrices, index-addressed so the
    #    assembly is independent of completion order (spec §2, §8).
    failure_matrix_stat = np.empty((n_samples, n_levels), dtype=bool)
    failure_matrix_tran = np.empty((n_samples, n_levels), dtype=bool)
    for level_index, col_static, col_trans in level_results:
        failure_matrix_stat[:, level_index] = col_static
        failure_matrix_tran[:, level_index] = col_trans

    # 6. Persist the raw failure payload BEFORE any fitting (crash recovery):
    #    the sweep is the expensive part, and an M9 fitting/bootstrap failure on
    #    a tail-dominated grid must never destroy it. On success the recovery
    #    pair is removed after the full result is saved (step 8).
    metadata = _build_metadata(
        config,
        theta_sample,
        runtime_seconds,
        n_jobs,
        seepage_length_stochastic=seepage_length_samples is not None,
        canonical=canonical,
        leakage_geometry=leakage_geometry,
        aquifer_response=aquifer_response,
    )
    raw_path: Path | None = None
    if resolved_path is not None:
        raw_path = resolved_path.with_suffix(".raw.h5")
        save_raw_failure_payload(
            raw_path,
            theta_matrix=theta_matrix,
            param_names=theta_sample.param_names,
            conditioning_grid=grid,
            failure_matrix_stat=failure_matrix_stat,
            failure_matrix_tran=failure_matrix_tran,
            metadata=metadata,
        )
        logger.info(
            "Wrote raw failure payload to %s (crash recovery; removed on success).",
            raw_path,
        )

    # 7. Assemble the FragilityResult (M9). Bootstrap runs serially here, seeded
    #    from config.mc.seed, so it too is independent of n_jobs.
    try:
        result = assemble_fragility(
            theta_matrix,
            theta_sample.param_names,
            grid,
            failure_matrix_stat,
            failure_matrix_tran,
            metadata,
            n_bootstrap=_BOOTSTRAP_N,
            confidence=_BOOTSTRAP_CONFIDENCE,
            seed=config.mc.seed,
            # Fits are anchored to the load excess above the exit point, so
            # (mu, sigma) are datum-invariant (fix 5, 2026-07-03).
            datum_m=float(config.geometry.z_toe),
        )
    except Exception:
        if raw_path is not None:
            logger.error(
                "Fragility assembly failed after the sweep; the raw failure "
                "payload survives at %s (+ JSON sidecar) for recovery.",
                raw_path,
            )
        raise

    # 8. Persist the full result (HDF5 + JSON sidecar) if requested; the raw
    #    recovery pair is then superseded and removed.
    if resolved_path is not None:
        result.save(resolved_path)
        if raw_path is not None:
            raw_path.unlink(missing_ok=True)
            raw_path.with_suffix(".json").unlink(missing_ok=True)
        logger.info(
            "Wrote fragility result to %s (+ JSON sidecar %s).",
            resolved_path,
            resolved_path.with_suffix(".json"),
        )

    return result
