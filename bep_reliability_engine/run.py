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
* **Middle — realizations j in {1..N}** (``config.mc.n_samples``). A loop calling
  scalar :func:`evaluate_realization` once per row (:func:`_scan_realizations`).
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
* The M3 stub is a deterministic pure function of (level, config) — **no RNG**
  (decision-log constraint: when the real M3 *selects* a d4PDF event it must
  derive a per-level seed deterministically from ``config.mc.seed`` and the
  level index / event_id, or this guarantee breaks).
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

Two marked seams (both grep-able, both single-function body swaps)
------------------------------------------------------------------
1. **M3 STUB** (:func:`_hydrograph_for_level`). M3 (``hydrographs.py``) does not
   exist yet, so the per-level loading is a *single clearly marked synthetic
   stub*: a deterministic two-peak (compound) raised-cosine event from the polder
   baseline peaking at h_i. Its only job is to exercise the M8 plumbing — the two
   peaks deliberately drive the spec §5 memory model; the fragility curve
   it produces is **not physical**, and ``metadata['hydrograph_source']`` is
   stamped ``'phase1_synthetic_stub'`` so no synthetic run is mistaken for a real
   one. It is called **once per level in the main process** (the outer loop), and
   the built record — which duck-types the spec §2 ``HydrographRecord`` (it
   carries ``.h``, ``.peak`` and ``.native_dt``, the three fields M8 reads, plus
   ``.t/.duration_hours/.scenario/.event_id``) — is handed to the worker, so the
   workers never see the stub. The stub already has **the exact signature the
   real loader will have**, ``(level_m: float, config: Config) -> HydrographRecord``
   (see its ``TODO(M3)``), so the swap is **one line**: replace the synthetic body
   with ``return hydrographs.hydrograph_for_level(level_m, config)`` (and drop
   :class:`_StubHydrograph`). The call site is unchanged.
2. **SCALAR-EVALUATION SEAM** (:func:`_scan_realizations`). The middle loop is a
   scalar ``for j in range(N)`` over M8, matching the spec §8 Phase-2 idiom and
   the as-built scalar M7/M8. The spec §6 across-realization vectorization was
   never built into M7; at full N (1e5) x N_h (~30) this scalar path is the
   performance ceiling. It is isolated in this one function so that swapping in a
   future vectorized ``evaluate_batch(theta_matrix, ...)`` (an M7/M8 change, not
   a run.py change) is a single-function body swap — needed before the
   production sweep.

Persistence (spec §2, §8; confirmed decisions)
----------------------------------------------
The run always returns the in-memory :class:`FragilityResult` (the spec §9
notebook idiom). With ``persist=True`` (default) it also writes one HDF5 + JSON
sidecar via M9's :meth:`FragilityResult.save`, to ``output_path`` or, if omitted,
``config.output.results_dir / f"{cross_section_id}_{scenario}.h5"``. The path is
**resolved and guarded before the expensive sweep** (fail fast): an existing
result file (or its sidecar) is **never silently overwritten** — it raises
``FileExistsError`` unless ``overwrite=True``.

Deferred decisions recorded for the decision log
-------------------------------------------------
* **Bootstrap settings deferral (accepted).** ``n_bootstrap`` and ``confidence``
  are not yet :class:`Config` fields; they are fixed here to
  :data:`_BOOTSTRAP_N` / :data:`_BOOTSTRAP_CONFIDENCE`, the bootstrap seed is
  derived from ``config.mc.seed``, and all three are recorded under
  ``metadata['bootstrap']`` so the bands stay config-reproducible. Promoting
  them to :class:`Config` is a clean follow-up.
* **M3-stub determinism constraint (accepted).** See the reproducibility note
  above: the real M3 must keep event selection deterministic-given-config (or
  explicitly per-level seeded) to preserve parallel == serial.

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
from bep_reliability_engine.evaluator import evaluate_realization
from bep_reliability_engine.fragility import FragilityResult, assemble_fragility
from bep_reliability_engine.sampling import ThetaSample, sample_theta

logger = logging.getLogger(__name__)

__all__ = ["run_fragility_analysis"]

# Provenance marker stamped into metadata so a synthetic-stub run is never
# mistaken for a real d4PDF-driven fragility result (see the M3 STUB seam).
_HYDROGRAPH_SOURCE: str = "phase1_synthetic_stub"

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


# ============================================================================
# M3 STUB — the single synthetic-hydrograph seam (module docstring, seam 1).
# _hydrograph_for_level already has the exact signature the real M3 loader will
# have, (level_m, config) -> HydrographRecord, so the swap is one line in its
# body (see the TODO inside). M8 only duck-types .h/.peak/.native_dt.
# ============================================================================
@dataclass(frozen=True)
class _StubHydrograph:
    """Duck-typed stand-in for the unbuilt M3 ``HydrographRecord`` (spec §2).

    Field names mirror the real schema so the M3 swap is mechanical. M8 reads
    only ``h``, ``peak`` and ``native_dt``; the rest are forward-compat carriers.

    Attributes
    ----------
    t : numpy.ndarray, shape (T,)
        Time axis [s] at ``native_dt`` spacing.
    h : numpy.ndarray, shape (T,)
        River stage [m above datum]; the synthetic two-peak bump.
    peak : float
        Static comparator level h_peak [m above datum]; set exactly to the
        conditioning level (authoritative, M8 ambiguity 3).
    duration_hours : float
        Event duration [h].
    scenario : str
        Climate scenario tag carried from the config (provenance only).
    event_id : str
        Synthetic event identifier.
    native_dt : float
        Native temporal resolution / integration timestep [s].
    """

    t: NDArray[np.float64]
    h: NDArray[np.float64]
    peak: float
    duration_hours: float
    scenario: str
    event_id: str
    native_dt: float


def _hydrograph_for_level(level_m: float, config: Config) -> _StubHydrograph:
    """Return the loading hydrograph for conditioning level ``level_m`` (M3 STUB).

    .. note:: TODO(M3) — replace the body of this function with a one-line
       delegation to the real loader once ``bep_reliability_engine/hydrographs.py``
       exists::

           return hydrograph_for_level(level_m, config)  # real M3 loader

       This function's signature, ``(level_m: float, config: Config) ->
       HydrographRecord``, is **already the real loader's signature**, so the swap
       touches only this body (and drops :class:`_StubHydrograph`); the call site
       in :func:`run_fragility_analysis` is unchanged.

    Placeholder loading for fragility-curve construction: a synthetic **two-peak
    compound event** — two raised-cosine bumps separated by an inter-peak trough
    at the polder baseline ``config.geometry.z_toe``, asymmetric in the
    typhoon-like sense of a smaller leading precursor peak
    (``_STUB_PRECURSOR_FRACTION`` of full height) followed by the larger main
    peak at ``level_m``. It is **not physical**, but the two-peak shape
    deliberately exercises the
    spec §5 compound-event memory model — the gate closes in the trough (flat,
    staircase l(t)) and the second peak resumes progression through the
    ``l_current > 0`` clause without re-triggering uplift — so the orchestration
    plumbing is validated against the transient branch's distinguishing feature.
    The real M3 will replace this with an actual d4PDF event anchored at
    ``level_m`` (or a canonical shape scaled to it).

    The function is a **pure, deterministic** function of its arguments (no RNG),
    which is what keeps the parallel sweep identical to a serial run (module
    docstring; decision-log constraint). The native timestep follows the ADR-0013
    policy: ``config.timestepper.target_dt_seconds`` when set, else the stub
    default :data:`_STUB_NATIVE_DT_S`.

    Parameters
    ----------
    level_m : float
        Conditioning level h_i [m above datum]; becomes both ``peak`` and the
        bump maximum.
    config : Config
        The run configuration (M1). The stub reads ``geometry.z_toe`` (baseline),
        ``timestepper.target_dt_seconds`` (native dt) and ``scenario`` (provenance
        tag); the real loader will read whatever it needs from the same object.

    Returns
    -------
    _StubHydrograph
        A record duck-typing the spec §2 ``HydrographRecord`` with ``peak`` set
        exactly to ``level_m``.
    """
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
    return _StubHydrograph(
        t=t,
        h=h,
        peak=float(level_m),
        duration_hours=float(n_steps * native_dt_s / 3600.0),
        scenario=config.scenario,
        event_id=f"stub_h{level_m:g}",
        native_dt=float(native_dt_s),
    )


# ============================================================================
# END M3 STUB
# ============================================================================


# ============================================================================
# SCALAR-EVALUATION SEAM — replace the body of _scan_realizations with the
# vectorized M7/M8 batch path (evaluate_batch(theta_matrix, ...)) before the
# production sweep. This is the single function to swap; _evaluate_level and the
# rest of run.py are agnostic to scalar-vs-batch. (Module docstring, seam 2.)
# ============================================================================
def _scan_realizations(
    theta_matrix: NDArray[np.float64],
    hydrograph: _StubHydrograph,
    geometry: dict[str, float],
    l_ini_m: float,
) -> tuple[NDArray[np.bool_], NDArray[np.bool_]]:
    """Evaluate all N realizations at one conditioning level (the middle loop).

    Scalar fallback: loops :func:`evaluate_realization` over the N rows of
    ``theta_matrix`` against the same ``hydrograph``, reading only the two failure
    flags (the diagnostics and trajectories the result also carries are discarded
    here — the bulk fragility run keeps neither, per spec §12 failure mode 6).

    **This is the deferred-vectorization seam.** When the M7/M8 batch path lands,
    replace the loop with a single ``evaluate_batch(theta_matrix, hydrograph,
    geometry, l_ini=l_ini_m)`` call returning the two boolean columns directly;
    nothing else in run.py changes.

    Parameters
    ----------
    theta_matrix : numpy.ndarray, shape (N, 7)
        The shared prior population in canonical column order (read-only).
    hydrograph : _StubHydrograph
        This level's loading record (``peak`` == the conditioning level).
    geometry : dict of str to float
        The flat M8 geometry dict (``Geometry.as_evaluator_dict``).
    l_ini_m : float
        Initial pipe length [m]; 0 for Phase 1 prior fragility.

    Returns
    -------
    col_static, col_trans : numpy.ndarray, shape (N,), dtype bool
        Per-realization static and transient failure indicators at this level.
    """
    n_samples = theta_matrix.shape[0]
    col_static = np.empty(n_samples, dtype=bool)
    col_trans = np.empty(n_samples, dtype=bool)
    for j in range(n_samples):
        result = evaluate_realization(
            theta_matrix[j],
            hydrograph,
            geometry,
            l_ini=l_ini_m,
            store_trajectory=False,
        )
        col_static[j] = result.failure_static
        col_trans[j] = result.failure_trans
    return col_static, col_trans


# ============================================================================
# END SCALAR-EVALUATION SEAM
# ============================================================================


def _evaluate_level(
    level_index: int,
    hydrograph: _StubHydrograph,
    theta_matrix: NDArray[np.float64],
    geometry: dict[str, float],
    l_ini_m: float,
) -> tuple[int, NDArray[np.bool_], NDArray[np.bool_]]:
    """Outer-loop task: one conditioning level, all N realizations.

    Module-level (picklable for loky): scans the realizations against the
    already-built ``hydrograph`` (the M3 stub is called in the main process, not
    here), and returns its own ``level_index`` so the caller can assemble the
    failure matrices by index, independent of task completion order (the
    reproducibility guarantee).

    Parameters
    ----------
    level_index : int
        Column index of this level in the (N, N_h) failure matrices.
    hydrograph : _StubHydrograph
        This level's loading record, built once in the main process by
        :func:`_hydrograph_for_level` (``peak`` == the conditioning level).
    theta_matrix : numpy.ndarray, shape (N, 7)
        The shared prior population (read-only).
    geometry : dict of str to float
        The flat M8 geometry dict.
    l_ini_m : float
        Initial pipe length [m].

    Returns
    -------
    tuple of (int, numpy.ndarray, numpy.ndarray)
        ``(level_index, col_static, col_trans)`` with both columns shape (N,)
        and dtype bool.
    """
    col_static, col_trans = _scan_realizations(
        theta_matrix, hydrograph, geometry, l_ini_m
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
) -> dict[str, Any]:
    """Assemble the spec §8 provenance block for the FragilityResult sidecar.

    Merges the full config snapshot and hash, the M2 sampling provenance, runtime
    fields, the loud stub marker, and the deferred bootstrap settings.

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
        "c_e_stochastic": True,
        "aquifer_lag_active": bool(config.timestepper.aquifer_lag_active),
        "tau_aq": None,  # lag inactive in Phase 1 (ADR-0014); from S_s when active.
        "hydrograph_source": _HYDROGRAPH_SOURCE,
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
       The transient loading is a **synthetic stub** while M3 is unbuilt
       (``metadata['hydrograph_source'] == 'phase1_synthetic_stub'``); the curves
       validate the engine plumbing, not site physics.

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
        Propagated from M9 if a fragility branch has fewer than two interior
        (``0 < P_f < 1``) conditioning levels — i.e. the grid does not bracket the
        transition for that branch.
    """
    # 1. Resolve and guard the output path BEFORE any expensive work (fail fast,
    #    so a long run is never lost to a refused write at the end).
    resolved_path: Path | None = None
    if persist:
        resolved_path = _resolve_output_path(config, output_path)
        _guard_no_overwrite(resolved_path, overwrite)

    # 2. Sample theta ONCE (front-load all RNG; shared read-only across levels).
    theta_sample = _sample_prior(config)
    theta_matrix = theta_sample.theta_matrix
    n_samples = theta_sample.n_samples

    # 3. Shared, read-only per-level inputs.
    geometry = config.geometry.as_evaluator_dict()
    grid = np.asarray(config.mc.conditioning_grid, dtype=np.float64)
    n_levels = int(grid.size)

    logger.info(
        "Fragility run: N=%d realizations x N_h=%d levels (n_jobs=%s, source=%s).",
        n_samples,
        n_levels,
        n_jobs,
        _HYDROGRAPH_SOURCE,
    )

    # 4. Outer loop over conditioning levels (parallel). Each level's hydrograph
    #    is built once in THIS (main) process by the M3 seam — delayed() evaluates
    #    its arguments here before dispatch — and the built record is handed to the
    #    worker, which never touches the stub. tqdm wraps the task iterable;
    #    joblib pulls from it as workers free up, tracking progress for any n_jobs.
    #    n_jobs=1 forces fully serial execution (the reproducibility-check path).
    level_iter: Any = enumerate(grid)
    if progress:
        level_iter = tqdm(
            level_iter, total=n_levels, desc="conditioning levels", unit="level"
        )

    start = time.perf_counter()
    level_results = Parallel(n_jobs=n_jobs)(
        delayed(_evaluate_level)(
            level_index,
            _hydrograph_for_level(float(level_m), config),  # M3 seam, main process
            theta_matrix,
            geometry,
            _L_INI_M,
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

    # 6. Assemble the FragilityResult (M9). Bootstrap runs serially here, seeded
    #    from config.mc.seed, so it too is independent of n_jobs.
    metadata = _build_metadata(config, theta_sample, runtime_seconds, n_jobs)
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
    )

    # 7. Persist (HDF5 + JSON sidecar) if requested.
    if resolved_path is not None:
        result.save(resolved_path)
        logger.info(
            "Wrote fragility result to %s (+ JSON sidecar %s).",
            resolved_path,
            resolved_path.with_suffix(".json"),
        )

    return result
