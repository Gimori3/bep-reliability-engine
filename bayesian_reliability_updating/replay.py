"""M8 survival replay: re-run the Phase 1 evaluator under identical assumptions.

Loads a Phase 1 :class:`~bep_reliability_engine.fragility.FragilityResult`,
reconstructs everything the original run threaded into M8 (validated config
from the embedded snapshot, the flat geometry dict, the regenerated
stochastic seepage-length draw, the deterministic Sellmeijer inputs, the
foreland treatment, the progression backend and the ADR-0030 integration
timestep policy) and evaluates every prior row against an observed event
record through
:func:`bep_reliability_engine.evaluator.evaluate_batch_diagnostics`, the
batch twin of the frozen scalar M8 API (ADR-0034).

No physics lives here (spec section 8 point 5): this module only marshals
the Phase 1 objects. The one Phase 2 policy decision it owns is the replay
timestep (ADR-0036): the observed record is refined onto the run's own
``timestepper.target_dt_seconds`` grid (225 s for every production config,
ADR-0030) via the M3 resample hook, superseding the ADR-0022 decision 2
1800 s guidance, because the Euler overshoot that ADR-0030 measured at
coarse timesteps produces exactly the spurious row-wise transient failures
an Accept-Reject filter must not contain.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from bayesian_reliability_updating.events import window_closure_diagnostic
from bep_reliability_engine.config import Config
from bep_reliability_engine.evaluator import (
    BatchDiagnostics,
    evaluate_batch_diagnostics,
    evaluate_realization,
)
from bep_reliability_engine.fragility import FragilityResult
from bep_reliability_engine.hydrographs import (
    HydrographRecord,
    resample_record,
    validate_datum_consistency,
)
from bep_reliability_engine.run import (
    model_factor_samples_for_config,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_theta

logger = logging.getLogger(__name__)

__all__ = [
    "EventReplay",
    "Phase1Run",
    "breach_times_for_rows",
    "load_phase1_run",
    "replay_event",
]

# Phase 2 replays every event from a virgin blanket: the observed survival
# event is the calibration event itself (spec section 5; mission invariant).
_L_INI_M: float = 0.0


@dataclass(frozen=True)
class Phase1Run:
    """One loaded Phase 1 run with its evaluation context reconstructed.

    Attributes
    ----------
    result : FragilityResult
        The loaded handoff artifact (theta matrix, failure matrices, curves,
        metadata).
    config : Config
        The run's validated config, reconstructed from the metadata snapshot
        and hash-checked against ``metadata['config_hash']``.
    geometry : dict
        The flat M8 geometry dict (``config.geometry.as_evaluator_dict()``),
        identical to what the Phase 1 sweep used.
    seepage_length_samples : numpy.ndarray or None
        The regenerated per-realization stochastic L (m), pairing with theta
        row j exactly as in the sweep, or None for deterministic L
        (ADR-0034 seam).
    theta_verified : bool
        True when the retained theta matrix was reproduced bit for bit from
        the config snapshot through the M2 sampler.
    source_path : pathlib.Path
        The loaded HDF5 path.
    h5_sha256, sidecar_sha256 : str
        Provenance hashes of the HDF5 file and its JSON sidecar.
    model_factor_samples : numpy.ndarray or None
        The regenerated per-realization ADR-0045 Sellmeijer model factor
        m_p, pairing with theta row j exactly as in the sweep, or None for
        baseline runs (the block absent or disabled). Regenerated through
        the same public seam as L
        (:func:`bep_reliability_engine.run.model_factor_samples_for_config`)
        so an m_p-enabled Phase 1 run replays under identical assumptions.
    """

    result: FragilityResult
    config: Config
    geometry: dict[str, float]
    seepage_length_samples: NDArray[np.float64] | None
    theta_verified: bool
    source_path: Path
    h5_sha256: str
    sidecar_sha256: str
    model_factor_samples: NDArray[np.float64] | None = None

    @property
    def theta(self) -> NDArray[np.float64]:
        """The (N, 7) prior rows to filter."""
        return self.result.theta_matrix

    @property
    def param_names(self) -> list[str]:
        """Canonical theta column names."""
        return self.result.param_names

    @property
    def n_samples(self) -> int:
        """Prior sample size N."""
        return int(self.result.theta_matrix.shape[0])


@dataclass(frozen=True)
class EventReplay:
    """One event's M8 replay over every prior row.

    Attributes
    ----------
    record : HydrographRecord
        The loading record actually integrated (after the ADR-0036 timestep
        refinement).
    diagnostics : BatchDiagnostics
        Per-realization margins, diagnostics and failure flags from
        ``evaluate_batch_diagnostics`` (row j pairs with theta row j).
    settings : dict
        The evaluation settings snapshot threaded into M8 (provenance).
    window_closure : dict
        The :func:`~bayesian_reliability_updating.events.\
window_closure_diagnostic` outcome for this record against the section toe.
    """

    record: HydrographRecord
    diagnostics: BatchDiagnostics
    settings: dict[str, Any]
    window_closure: dict[str, float | bool]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_phase1_run(path: str | Path, *, verify_theta: bool = True) -> Phase1Run:
    """Load a Phase 1 FragilityResult and reconstruct its evaluation context.

    Parameters
    ----------
    path : str or pathlib.Path
        The Phase 1 HDF5 path (JSON sidecar expected next to it).
    verify_theta : bool, optional
        Re-draw the prior from the config snapshot through the M2 sampler
        and require bit identity with the retained theta matrix (an
        integrity check that the snapshot really regenerates the run;
        default True, costs well under a second at N = 1e5).

    Returns
    -------
    Phase1Run
        The loaded run with config, geometry and the regenerated stochastic
        seepage lengths.

    Raises
    ------
    ValueError
        If the config snapshot is missing or fails validation, its hash
        does not match the recorded ``config_hash``, the geometry block is
        incomplete, or ``verify_theta`` finds a mismatch.
    """
    path = Path(path)
    result = FragilityResult.load(path)
    metadata = result.metadata

    snapshot = metadata.get("config")
    if snapshot is None:
        raise ValueError(
            f"{path.name}: metadata carries no 'config' snapshot; the replay "
            "cannot reconstruct the run's assumptions."
        )
    config = Config.model_validate(snapshot)
    recorded_hash = metadata.get("config_hash")
    if recorded_hash is not None and config.config_hash() != recorded_hash:
        raise ValueError(
            f"{path.name}: reconstructed config hash "
            f"{config.config_hash()[:12]}... does not match the recorded "
            f"config_hash {str(recorded_hash)[:12]}...; refusing to replay "
            "under drifted assumptions."
        )

    geometry = config.geometry.as_evaluator_dict()
    required = {"L", "z_toe", "foreshore_width", "D_fore", "k_fore"}
    if not required <= geometry.keys():
        raise ValueError(
            f"{path.name}: geometry snapshot is missing keys "
            f"{sorted(required - geometry.keys())}."
        )

    theta_verified = False
    if verify_theta:
        redraw = sample_theta(
            config.priors.to_marginal_specs(),
            seed=config.mc.seed,
            rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
            d70_interpretation=config.priors.d70_interpretation,
            n_samples=config.mc.n_samples,
            coupling=config.correlation.coupling,
            bounds=config.priors.bounds,
        )
        if not np.array_equal(redraw.theta_matrix, result.theta_matrix):
            raise ValueError(
                f"{path.name}: the config snapshot does not regenerate the "
                "retained theta matrix; the file's provenance is broken."
            )
        theta_verified = True

    seepage = seepage_length_samples_for_config(config)
    if seepage is not None and seepage.shape[0] != result.theta_matrix.shape[0]:
        raise ValueError(
            f"{path.name}: regenerated L draw has {seepage.shape[0]} rows for "
            f"{result.theta_matrix.shape[0]} theta rows."
        )

    # ADR-0045: regenerate the m_p draw exactly like L. None on baseline runs
    # (the block absent or disabled), so nothing changes for existing files.
    model_factor = model_factor_samples_for_config(config)
    if model_factor is not None and (
        model_factor.shape[0] != result.theta_matrix.shape[0]
    ):
        raise ValueError(
            f"{path.name}: regenerated m_p draw has {model_factor.shape[0]} "
            f"rows for {result.theta_matrix.shape[0]} theta rows."
        )

    sidecar = path.with_suffix(".json")
    return Phase1Run(
        result=result,
        config=config,
        geometry=geometry,
        seepage_length_samples=seepage,
        theta_verified=theta_verified,
        source_path=path,
        h5_sha256=_sha256(path),
        sidecar_sha256=_sha256(sidecar),
        model_factor_samples=model_factor,
    )


def _replay_record(run: Phase1Run, record: HydrographRecord) -> HydrographRecord:
    """Refine the observed record onto the run's integration grid (ADR-0036)."""
    target = run.config.timestepper.target_dt_seconds
    if target is not None and float(target) < float(record.native_dt):
        return resample_record(record, float(target))
    return record


def replay_event(
    run: Phase1Run,
    record: HydrographRecord,
    *,
    progression_backend: str | None = None,
) -> EventReplay:
    """Replay one observed event through M8 for every prior row.

    Threads the identical evaluation settings the Phase 1 sweep used
    (shared-sample contract, ADR-0002: the same theta row and the same
    regenerated L_j feed both limit states in one call) and integrates on
    the run's own ADR-0030 timestep grid. ``l_ini = 0`` and recovery
    ``r_l = 0`` throughout (spec section 5).

    Parameters
    ----------
    run : Phase1Run
        The loaded Phase 1 run.
    record : HydrographRecord
        The observed event's loading record at this run's section (native
        cadence; refined here).
    progression_backend : str, optional
        Override for the M7 batch backend. None (default) uses the run's
        own ``config.timestepper.progression_backend``.

    Returns
    -------
    EventReplay
        The per-row diagnostics and the actually integrated record.

    Raises
    ------
    ValueError
        From the MSL datum guard, or if the record cannot be refined onto
        the run's integration grid.
    """
    validate_datum_consistency(record, float(run.geometry["z_toe"]))
    replay_rec = _replay_record(run, record)

    backend = (
        progression_backend
        if progression_backend is not None
        else run.config.timestepper.progression_backend
    )
    config = run.config
    settings: dict[str, Any] = {
        "l_ini_m": _L_INI_M,
        "replay_dt_seconds": float(replay_rec.native_dt),
        "record_native_dt_seconds": float(record.native_dt),
        "alpha_exponent": float(config.alpha_exponent),
        "alpha_exponent_transient": (
            None
            if config.alpha_exponent_transient is None
            else float(config.alpha_exponent_transient)
        ),
        "theta_repose_deg": float(config.theta_repose_deg),
        "relative_density_insitu": float(config.relative_density_insitu),
        "foreland_treatment": config.foreland_treatment,
        "progression_backend": backend,
        "seepage_length_stochastic": run.seepage_length_samples is not None,
        "model_factor_stochastic": run.model_factor_samples is not None,
        "event_id": replay_rec.event_id,
        "peak_m_msl": float(replay_rec.peak),
    }

    closure = window_closure_diagnostic(replay_rec, float(run.geometry["z_toe"]))
    if not closure["closed"]:
        logger.warning(
            "Observed record %s ends ABOVE the landside toe (end stage %.2f m "
            "MSL, toe %.2f): the truncated recession could still drive "
            "progression and the survival constraint may be understated.",
            replay_rec.event_id,
            closure["end_stage_m_msl"],
            float(run.geometry["z_toe"]),
        )

    diagnostics = evaluate_batch_diagnostics(
        run.theta,
        replay_rec,
        run.geometry,
        l_ini=_L_INI_M,
        seepage_length_samples=run.seepage_length_samples,
        alpha_exponent=config.alpha_exponent,
        alpha_exponent_transient=config.alpha_exponent_transient,
        theta_repose_rad=config.theta_repose_rad,
        relative_density=config.relative_density_insitu,
        foreland_open=config.foreland_treatment == "open_entry",
        progression_backend=backend,
        model_factor_samples=run.model_factor_samples,
    )
    return EventReplay(
        record=replay_rec,
        diagnostics=diagnostics,
        settings=settings,
        window_closure=closure,
    )


def breach_times_for_rows(
    run: Phase1Run,
    replay: EventReplay,
    row_indices: NDArray[np.integer],
) -> NDArray[np.float64]:
    """Per-row time to breach under the replayed event, from l(t) trajectories.

    Re-runs the scalar M8 evaluator with ``store_trajectory=True`` for the
    requested rows only (the observed-event replay is the one run where
    trajectory retention is warranted, spec section 12 failure mode 6) and
    returns the first time the pipe reaches the row's seepage length. Rows
    that never breach return NaN.

    Parameters
    ----------
    run : Phase1Run
        The loaded run (supplies theta, geometry, settings and L_j).
    replay : EventReplay
        The event replay whose record to integrate (uses the identical
        refined record, so the flags reproduce exactly).
    row_indices : numpy.ndarray of int
        The rows to trace (typically the transient-rejected set).

    Returns
    -------
    numpy.ndarray, shape (len(row_indices),)
        Time to breach [s] from the record start, NaN where the row does
        not breach.
    """
    config = run.config
    times = np.full(len(row_indices), np.nan, dtype=np.float64)
    for out_idx, j in enumerate(np.asarray(row_indices, dtype=int)):
        geometry = dict(run.geometry)
        if run.seepage_length_samples is not None:
            geometry["L"] = float(run.seepage_length_samples[j])
        result = evaluate_realization(
            run.theta[j],
            replay.record,
            geometry,
            l_ini=_L_INI_M,
            store_trajectory=True,
            alpha_exponent=config.alpha_exponent,
            alpha_exponent_transient=config.alpha_exponent_transient,
            theta_repose_rad=config.theta_repose_rad,
            relative_density=config.relative_density_insitu,
            foreland_open=config.foreland_treatment == "open_entry",
            model_factor_mp=(
                None
                if run.model_factor_samples is None
                else float(run.model_factor_samples[j])
            ),
        )
        trajectory = result.l_trajectory
        if trajectory is None:
            continue
        reached = np.nonzero(trajectory >= float(geometry["L"]))[0]
        if reached.size:
            times[out_idx] = float(replay.record.t[reached[0]])
    return times
