"""The Phase 2 pipeline: one Phase 1 result in, one PosteriorResult out.

Composes the package end to end for one segment stratum (one Phase 1 file =
one segment, scenario and d70 interpretation): load and verify the Phase 1
run, build the observed-event record at the run's own section, replay M8
over every prior row, filter, decompose, regenerate the posterior fragility
from the retained matrices, optionally verify by re-evaluation, analyse the
prior-to-posterior shift, persist and plot. ``run_survival_update`` is the
function behind the CLI (``python -m bayesian_reliability_updating``).
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from bayesian_reliability_updating import __version__ as _phase2_version
from bayesian_reliability_updating.analysis import (
    c_e_headline,
    correlation_shift,
    prior_posterior_summary,
)
from bayesian_reliability_updating.events import (
    default_2016_source,
    observed_event_record,
    read_flood_traces,
)
from bayesian_reliability_updating.fragility_update import (
    posterior_fragility_from_matrices,
    verify_posterior_fragility_by_reevaluation,
)
from bayesian_reliability_updating.posterior import EventArrays, PosteriorResult
from bayesian_reliability_updating.replay import (
    Phase1Run,
    breach_times_for_rows,
    load_phase1_run,
)
from bayesian_reliability_updating.sequential import apply_event, initial_state
from bep_reliability_engine.hydrographs import HydrographRecord

logger = logging.getLogger(__name__)

__all__ = [
    "PUBLICATION_FIGURES",
    "PUBLICATION_FIGURE_DIR",
    "Phase2Settings",
    "run_survival_update",
]

#: Tracked publication directory. ``results/`` is gitignored, so a figure that
#: lives only there is not a deliverable (``docs/conventions.md`` section 9.3).
PUBLICATION_FIGURE_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"

#: The Phase 2 figures promoted to ``docs/figures/``, by Phase 1 run stem and
#: figure kind. Added 2026-08-02 to close inventory rows 4.3, 4.4 and 5.1.
#:
#: **The selection is deliberate and is the whole point of this being a
#: registry rather than a blanket dual-write.** ``_figures`` renders 44 files
#: across the eight strata; four are promoted:
#:
#: * only the ``marginals`` and ``fragility_update`` kinds, which are what the
#:   thesis asks for (the posterior parameter shift and the prior-to-posterior
#:   fragility shift). ``decomposition``, ``rejection_scatter``, ``record`` and
#:   ``breach_times`` stay run-local diagnostics;
#: * only at **KP 58.8 and KP 60.0 matrix**, the two informative strata
#:   (transient rejection 5.67 % and 3.36 % against <= 0.07 % everywhere else,
#:   ``docs/phase2_report.md`` section 11.1). Every number rows 4.3, 4.4 and
#:   5.1 quote is measured at exactly these two. That the update is
#:   *concentrated* there is carried across all eight strata by
#:   ``phase2_survival_update.png``, so a near-null pair at KP 57.4 or KP 62.0
#:   would add a figure without adding a fact.
#:
#: Keying on the **stem** is load-bearing: the ADR-0046 z_toe scenario suffixes
#: the stem (``_ztoe_plus0.30m``), so a scenario run finds no entry and writes
#: no publication copy. A scenario can therefore never masquerade as the
#: baseline in ``docs/figures/``, which is the same guarantee the name-segregated
#: output stem gives the posterior itself.
PUBLICATION_FIGURES: dict[str, dict[str, str]] = {
    "tokachi_kp58.8_historical_matrix": {
        "marginals": "phase2_marginals_kp58_8_matrix.png",
        "fragility_update": "phase2_fragility_update_kp58_8_matrix.png",
    },
    "tokachi_kp60.0_historical_matrix": {
        "marginals": "phase2_marginals_kp60_0_matrix.png",
        "fragility_update": "phase2_fragility_update_kp60_0_matrix.png",
    },
}


def publication_path(stem: str, kind: str) -> Path | None:
    """Tracked destination for one Phase 2 figure, or None if not promoted.

    Parameters
    ----------
    stem : str
        The Phase 1 run stem the figures are named for (``paths['stem'].name``).
    kind : str
        Figure kind, e.g. ``'marginals'`` or ``'fragility_update'``.

    Returns
    -------
    pathlib.Path or None
        The ``docs/figures/`` path when this (stem, kind) is promoted by
        :data:`PUBLICATION_FIGURES`, else None.
    """
    name = PUBLICATION_FIGURES.get(stem, {}).get(kind)
    return None if name is None else PUBLICATION_FIGURE_DIR / name


class Phase2Settings(BaseModel):
    """Validated Phase 2 run settings (the CLI constructs one per run).

    Attributes
    ----------
    anchor : str
        Observed-record peak anchoring (ADR-0035): ``'trace_right'``
        (default; the study levees' bank), ``'trace_left'`` or
        ``'rating'``.
    criterion : str
        Acceptance criterion (ADR-0036): ``'no_breach'`` (baseline) or the
        stricter optional ``'no_breach_no_initiation'``.
    data_root : str
        Root of the raw data drop (rating curves; ADR-0020 layout).
    processed_dir : str
        Directory of the processed observed-event extracts.
    output_dir : str
        Where PosteriorResult files (and ``figures/``) are written.
    verify_by_reevaluation : bool
        Run the exact re-evaluation verification of the posterior
        fragility (mission invariant 7; slower).
    trace_breach_times : bool
        Trace per-row breach times for the transient-rejected set through
        the scalar M8 with trajectories (the sanctioned trajectory run).
    figures : bool
        Render the figure set.
    n_bootstrap : int
        Posterior bootstrap replicates.
    confidence : float
        Two-sided band coverage.
    progression_backend : str or None
        Optional M7 backend override for the replay (None uses the Phase 1
        config's own backend).
    overwrite : bool
        Allow replacing an existing PosteriorResult pair.
    z_toe_delta_m : float
        ADR-0046 epistemic exit-datum scenario: offset [m] applied to the
        replay's ``z_toe`` (the surveyed ±0.3 m sensitivity). Default 0.0
        (baseline, bit-identical). Nonzero deltas suffix the output stem
        (``_ztoe_plus0.30m`` / ``_ztoe_minus0.30m``) so a scenario run can
        never masquerade as the baseline posterior, and are stamped into
        ``metadata['phase2']['z_toe_scenario']``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    anchor: Literal["trace_right", "trace_left", "rating"] = "trace_right"
    criterion: Literal["no_breach", "no_breach_no_initiation"] = "no_breach"
    data_root: str = "data/raw"
    processed_dir: str = "data/processed/2016_event"
    output_dir: str = "results/phase2"
    verify_by_reevaluation: bool = False
    trace_breach_times: bool = True
    figures: bool = True
    #: Redraw the figures from a recomputed-in-memory posterior WITHOUT writing
    #: (or overwriting) the PosteriorResult pair. Added 2026-07-30 so a stale
    #: figure can be refreshed against its current Phase 1 parent without
    #: touching a persisted artifact whose SHA-256 the production campaign
    #: manifest records. Default False is bit-identical to previous behaviour.
    figures_only: bool = False
    n_bootstrap: int = Field(default=1000, ge=10)
    confidence: float = Field(default=0.95, gt=0.0, lt=1.0)
    progression_backend: Literal["numpy", "numba"] | None = None
    overwrite: bool = False
    z_toe_delta_m: float = 0.0


def _output_paths(phase1_path: Path, settings: Phase2Settings) -> dict[str, Path]:
    stem = phase1_path.stem
    if settings.z_toe_delta_m != 0.0:
        # ADR-0046: scenario outputs are name-segregated from the baseline
        # posterior ('+' is spelled out, matching the '+4K' -> 'plus' rule).
        sign = "plus" if settings.z_toe_delta_m > 0.0 else "minus"
        stem = f"{stem}_ztoe_{sign}{abs(settings.z_toe_delta_m):.2f}m"
    out_dir = Path(settings.output_dir)
    return {
        "h5": out_dir / f"{stem}_posterior.h5",
        "sidecar": out_dir / f"{stem}_posterior.json",
        "figures": out_dir / "figures",
        "stem": Path(stem),
    }


def _guard_no_overwrite(paths: dict[str, Path], overwrite: bool) -> None:
    existing = [str(p) for p in (paths["h5"], paths["sidecar"]) if p.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing Phase 2 result(s) {existing}; "
            "pass overwrite=True (CLI: --overwrite) to replace them."
        )


def _default_event_record(run: Phase1Run, settings: Phase2Settings) -> HydrographRecord:
    """The built-in 2016 record at the run's own section (ADR-0035)."""
    source_block = run.config.hydrograph_source
    if source_block is None:
        raise ValueError(
            "the Phase 1 config carries no hydrograph_source block, so the "
            "run's river and KP are unknown; pass an explicit event record."
        )
    source = default_2016_source(settings.processed_dir)
    if source.river != source_block.river:
        raise ValueError(
            f"built-in 2016 source covers the {source.river}, but the run's "
            f"section is on the {source_block.river}; pass an explicit "
            "event record."
        )
    return observed_event_record(
        source,
        section_kp=float(source_block.kp),
        data_root=settings.data_root,
        anchor=settings.anchor,
    )


def _figures(
    run: Phase1Run,
    result: PosteriorResult,
    chain_summary: list[dict[str, Any]],
    replays: list,
    paths: dict[str, Path],
) -> list[str]:
    from bayesian_reliability_updating import plots

    stem = paths["stem"].name
    fig_dir = paths["figures"]
    # The replay datum (equals the config toe except under the ADR-0046
    # scenario, where figures must draw the shifted toe actually used).
    z_toe = float(run.geometry["z_toe"])
    written: list[str] = []

    written.append(
        str(
            plots.plot_prior_posterior_marginals(
                result.theta_matrix,
                result.param_names,
                result.accept,
                fig_dir / f"{stem}_marginals.png",
                title=f"{stem}: prior vs posterior marginals",
                publication_path=publication_path(stem, "marginals"),
            )
        )
    )
    last_event = chain_summary[-1]
    written.append(
        str(
            plots.plot_fragility_update(
                result.fragility.conditioning_grid,
                result.P_f_trans_prior_raw,
                result.P_f_static_prior_raw,
                result.fragility,
                fig_dir / f"{stem}_fragility_update.png",
                z_toe_m=z_toe,
                event_peak_m=float(last_event["record"]["peak_m_msl"]),
                title=f"{stem}: fragility update",
                publication_path=publication_path(stem, "fragility_update"),
            )
        )
    )
    written.append(
        str(
            plots.plot_decomposition(
                last_event["decomposition"],
                fig_dir / f"{stem}_decomposition.png",
                title=f"{stem}: survival-discrimination decomposition "
                f"({last_event['event_id']})",
            )
        )
    )
    written.append(
        str(
            plots.plot_rejection_scatter(
                result.theta_matrix,
                result.param_names,
                result.accept,
                fig_dir / f"{stem}_rejection_scatter.png",
                title=f"{stem}: accept/reject in the k_aq x C_e plane",
            )
        )
    )
    for _, _, replay in replays:
        trace = replay.record.provenance.get("trace_anchor_m_msl")
        written.append(
            str(
                plots.plot_observed_record(
                    replay.record,
                    fig_dir / f"{stem}_{replay.record.event_id}_record.png",
                    z_toe_m=z_toe,
                    trace_level_m=trace,
                    title=f"{stem}: observed record {replay.record.event_id}",
                )
            )
        )
    for event_id, arrays in result.events.items():
        if arrays.t_breach is not None and np.isfinite(arrays.t_breach).any():
            replay = next(r for _, _, r in replays if r.record.event_id == event_id)
            written.append(
                str(
                    plots.plot_breach_times(
                        arrays.t_breach,
                        replay.record,
                        fig_dir / f"{stem}_{event_id}_breach_times.png",
                        title=f"{stem}: rejected-realization breach times "
                        f"({event_id})",
                    )
                )
            )
    return written


def run_survival_update(
    phase1_path: str | Path,
    *,
    settings: Phase2Settings | None = None,
    event_records: list[HydrographRecord] | None = None,
    persist: bool = True,
) -> PosteriorResult:
    """Run the full Phase 2 update for one Phase 1 result file.

    Parameters
    ----------
    phase1_path : str or pathlib.Path
        A Phase 1 FragilityResult HDF5 (JSON sidecar next to it).
    settings : Phase2Settings, optional
        Run settings; defaults throughout when omitted.
    event_records : list of HydrographRecord, optional
        The survival events to apply, in order. None (default) applies the
        built-in 2016 record at the run's own section. Passing more than
        one record composes them sequentially (posterior-in,
        posterior-out).
    persist : bool, optional
        Write the PosteriorResult pair (and figures when enabled). The
        in-memory result is returned either way.

    Returns
    -------
    PosteriorResult
        The persisted (or in-memory) Phase 2 artifact.

    Raises
    ------
    FileExistsError
        If the output pair exists and overwrite is not set.
    ValueError
        Propagated from loading, construction, replay or filtering.
    """
    settings = settings or Phase2Settings()
    phase1_path = Path(phase1_path)
    paths = _output_paths(phase1_path, settings)
    if persist and not settings.figures_only:
        # figures_only never writes the PosteriorResult pair, so the guard that
        # protects it does not apply.
        _guard_no_overwrite(paths, settings.overwrite)

    start = time.perf_counter()
    run = load_phase1_run(phase1_path, z_toe_delta_m=settings.z_toe_delta_m)
    if event_records is None:
        event_records = [_default_event_record(run, settings)]

    # Sequential Accept-Reject chain (masks over original prior rows).
    state = initial_state(run)
    for record in event_records:
        state, outcome, replay = apply_event(
            state,
            record,
            criterion=settings.criterion,
            progression_backend=settings.progression_backend,
        )

    # Per-event arrays for persistence; breach times for the rejected rows.
    events: dict[str, EventArrays] = {}
    for event_id, outcome, replay in state.chain:
        diag = replay.diagnostics
        t_breach = None
        if settings.trace_breach_times:
            rejected_rows = np.nonzero(~outcome.accept_trans)[0]
            t_breach = np.full(run.n_samples, np.nan, dtype=np.float64)
            if rejected_rows.size:
                logger.info(
                    "Tracing breach times for %d rejected rows (%s)...",
                    rejected_rows.size,
                    event_id,
                )
                t_breach[rejected_rows] = breach_times_for_rows(
                    run, replay, rejected_rows
                )
        events[event_id] = EventArrays(
            accept_trans=outcome.accept_trans,
            accept_static=outcome.accept_static,
            initiation=outcome.initiation_occurred,
            Z_static=diag.Z_static,
            Z_transient=diag.Z_transient,
            l_e_final=diag.l_e_final,
            t_uh=diag.t_uh,
            r_e=diag.r_e,
            t_breach=t_breach,
        )

    posterior_fragility = posterior_fragility_from_matrices(
        run,
        state.alive,
        n_bootstrap=settings.n_bootstrap,
        confidence=settings.confidence,
    )
    verification: dict[str, Any] | None = None
    if settings.verify_by_reevaluation:
        verification = verify_posterior_fragility_by_reevaluation(
            run, state.alive, posterior_fragility
        )

    chain_summary = state.chain_summary()
    marginals = prior_posterior_summary(run.theta, run.param_names, state.alive)
    headline = c_e_headline(run.theta, run.param_names, state.alive)
    correlations = correlation_shift(run.theta, run.param_names, state.alive)

    phase1_meta = run.result.metadata
    trace_context = _trace_context(run, settings)
    metadata: dict[str, Any] = {
        "phase1": {
            "path": str(phase1_path),
            "h5_sha256": run.h5_sha256,
            "sidecar_sha256": run.sidecar_sha256,
            "config_hash": phase1_meta.get("config_hash"),
            "code_version": phase1_meta.get("code_version"),
            "cross_section_id": phase1_meta.get("cross_section_id"),
            "segment_id": phase1_meta.get("segment_id"),
            "scenario": phase1_meta.get("scenario"),
            "remediation_state": phase1_meta.get("remediation_state"),
            "d70_interpretation": phase1_meta.get("d70_interpretation"),
            "lhs_seed": phase1_meta.get("lhs_seed"),
            "n_samples": run.n_samples,
            "theta_verified": run.theta_verified,
            "hydrograph_source": phase1_meta.get("hydrograph_source"),
        },
        "phase2": {
            "package_version": _phase2_version,
            "settings": settings.model_dump(),
            "l_ini_m": 0.0,
            "recovery_r_l": 0.0,
            "event_chain": chain_summary,
            "posterior": {
                "n_prior": run.n_samples,
                "n_accepted": state.n_alive,
                "rejection_fraction": 1.0 - state.n_alive / run.n_samples,
                "criterion": settings.criterion,
                "warnings": [w for _, o, _ in state.chain for w in o.warnings],
            },
            "posterior_fragility": posterior_fragility.settings,
            "verification": verification,
            "trace_context": trace_context,
            # ADR-0046 epistemic exit-datum scenario (0.0 = baseline): the
            # replay datum actually used, so a scenario posterior is
            # self-describing beyond its filename suffix.
            "z_toe_scenario": {
                "delta_m": float(settings.z_toe_delta_m),
                "z_toe_config_m_msl": float(run.config.geometry.z_toe),
                "z_toe_replay_m_msl": float(run.geometry["z_toe"]),
            },
            "runtime_seconds": time.perf_counter() - start,
        },
        "analysis": {
            "marginals": marginals,
            "c_e_headline": headline,
            "correlation_shift": correlations,
        },
    }
    metadata = json.loads(json.dumps(metadata))

    result = PosteriorResult(
        theta_matrix=run.theta,
        param_names=run.param_names,
        seepage_length_samples=run.seepage_length_samples,
        accept=state.alive,
        events=events,
        fragility=posterior_fragility,
        P_f_trans_prior_raw=np.asarray(run.result.P_f_trans_raw, dtype=np.float64),
        P_f_static_prior_raw=np.asarray(run.result.P_f_static_raw, dtype=np.float64),
        metadata=metadata,
    )

    if persist and not settings.figures_only:
        result.save(paths["h5"])
        logger.info(
            "Wrote Phase 2 result to %s (+ sidecar); posterior keeps %d of "
            "%d rows (rejection %.2f%%).",
            paths["h5"],
            state.n_alive,
            run.n_samples,
            100.0 * (1.0 - state.n_alive / run.n_samples),
        )
    elif persist:
        logger.info(
            "figures_only: NOT writing %s; posterior keeps %d of %d rows "
            "(rejection %.2f%%).",
            paths["h5"].name,
            state.n_alive,
            run.n_samples,
            100.0 * (1.0 - state.n_alive / run.n_samples),
        )
    if persist and settings.figures:
        written = _figures(run, result, chain_summary, state.chain, paths)
        logger.info("Wrote %d figures under %s.", len(written), paths["figures"])
    return result


def _trace_context(run: Phase1Run, settings: Phase2Settings) -> dict[str, Any] | None:
    """Record the surveyed trace and design HWL at the section (provenance)."""
    source_block = run.config.hydrograph_source
    if source_block is None:
        return None
    source = default_2016_source(settings.processed_dir)
    if source.trace_csv is None or not Path(source.trace_csv).exists():
        return None
    if source.river != source_block.river:
        return None
    traces = read_flood_traces(source.trace_csv, source.river)
    trace = traces.get(round(float(source_block.kp), 1))
    if trace is None:
        return None
    return {
        "kp": trace.kp,
        "design_hwl_m_msl": trace.design_hwl_m,
        "trace_left_m_msl": trace.trace_left_m,
        "trace_right_m_msl": trace.trace_right_m,
    }
