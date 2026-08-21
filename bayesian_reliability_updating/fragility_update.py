"""Posterior fragility curves from the retained Phase 1 failure matrices.

Default path (mission invariant 7; ADR-0036): the posterior fragility needs
NO re-running of the conditioning sweep. Under the shared-sample contract
(ADR-0002) the retained (N, N_h) failure matrices hold each prior row's
outcome at every conditioning level for exactly the (theta_j, L_j) pair the
survival replay classified, so the posterior curve at level i is the
failure fraction among accepted rows:

    P_f_post(h_i) = mean(failure_matrix[accept, i])

which is precisely the Monte Carlo form of Schweckendiek (2014) Eq. 4.12,
``P(F_i | epsilon) = P(F_i and epsilon) / P(epsilon)``, with the evidence
``epsilon`` the survival of the observed event.

Uncertainty on the posterior points mirrors the Phase 1 deliverable
(ADR-0024): always-on Clopper-Pearson binomial CIs with ``n = n_accepted``
(reusing M9's :func:`~bep_reliability_engine.fragility.binomial_ci`), plus
percentile bootstrap bands from resampling the accepted rows with
replacement. Where the point set brackets the transition, a lognormal fit
through M9's :func:`~bep_reliability_engine.fragility.fit_lognormal_fragility`
is attached (datum-anchored at z_toe like Phase 1); fits stay Optional and
their absence is not an error (raw tail points with CIs are the intended
presentation in the tail, per ADR-0024).

Verification path (optional; mission invariant 7): re-evaluate the accepted
rows on the run's own conditioning records rebuilt by
:func:`bep_reliability_engine.run.conditioning_hydrographs_for_config` and
require EXACT agreement with the masked-matrix curves. Because the same M8
kernels integrate the same records for the same (theta_j, L_j) pairs, the
re-evaluated failure flags must reproduce the retained matrix columns bit
for bit; any deviation means the replay context is not identical to the
Phase 1 run and the whole update would be invalid, so it raises.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from bayesian_reliability_updating.replay import Phase1Run
from bep_reliability_engine.evaluator import evaluate_batch
from bep_reliability_engine.fragility import (
    LognormFragility,
    binomial_ci,
    fit_lognormal_fragility,
)
from bep_reliability_engine.run import conditioning_hydrographs_for_config

logger = logging.getLogger(__name__)

__all__ = [
    "PosteriorFragility",
    "posterior_fragility_from_matrices",
    "verify_posterior_fragility_by_reevaluation",
]

_BOOTSTRAP_N_DEFAULT: int = 1000
_BOOTSTRAP_CONFIDENCE_DEFAULT: float = 0.95

# Salt for the posterior bootstrap seed, derived from the Phase 1 config seed
# via SeedSequence (the run.py pattern) so posterior bands are reproducible
# from the same provenance chain yet independent of the Phase 1 draws.
_POSTERIOR_BOOTSTRAP_SALT: int = 0x0B57E210


@dataclass(frozen=True)
class PosteriorFragility:
    """Posterior fragility curves over the Phase 1 conditioning grid.

    Attributes
    ----------
    conditioning_grid : numpy.ndarray, shape (N_h,)
        The Phase 1 grid [m MSL], unchanged.
    P_f_trans_post_raw, P_f_static_post_raw : numpy.ndarray, shape (N_h,)
        Posterior failure fractions among accepted rows, per branch, both
        conditioned on the same (transient-survival) evidence.
    binomial_ci : dict
        ``{'transient': (lo, hi), 'static': (lo, hi)}`` Clopper-Pearson
        95 percent CIs on the raw posterior points, ``n = n_accepted``.
    bootstrap_bands : dict
        Same keys; percentile bands from resampling accepted rows.
    P_f_trans_post_fit, P_f_static_post_fit : LognormFragility or None
        Optional datum-anchored lognormal fits (M9 criteria; None where the
        posterior point set cannot support a fit).
    n_accepted : int
        Rows behind every posterior fraction.
    settings : dict
        Bootstrap settings and seed provenance.
    """

    conditioning_grid: NDArray[np.float64]
    P_f_trans_post_raw: NDArray[np.float64]
    P_f_static_post_raw: NDArray[np.float64]
    binomial_ci: dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]
    bootstrap_bands: dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]
    P_f_trans_post_fit: LognormFragility | None
    P_f_static_post_fit: LognormFragility | None
    n_accepted: int
    settings: dict[str, Any]


def _fit_or_none(
    grid: NDArray[np.float64], p_f: NDArray[np.float64], datum_m: float
) -> LognormFragility | None:
    """Attempt the M9 lognormal fit; a tail-only point set yields None."""
    try:
        return fit_lognormal_fragility(grid, p_f, datum_m=datum_m)
    except ValueError:
        return None


def posterior_fragility_from_matrices(
    run: Phase1Run,
    accept: NDArray[np.bool_],
    *,
    n_bootstrap: int = _BOOTSTRAP_N_DEFAULT,
    confidence: float = _BOOTSTRAP_CONFIDENCE_DEFAULT,
) -> PosteriorFragility:
    """Posterior fragility by masking the retained failure matrices (default).

    Parameters
    ----------
    run : Phase1Run
        The loaded Phase 1 run (matrices, grid, datum, seed provenance).
    accept : numpy.ndarray, shape (N,), bool
        The operative acceptance mask over the original prior rows.
    n_bootstrap : int, optional
        Bootstrap replicates for the posterior bands (default 1000,
        mirroring the Phase 1 run driver).
    confidence : float, optional
        Two-sided band coverage (default 0.95).

    Returns
    -------
    PosteriorFragility
        Raw posterior curves, CIs, bands and Optional fits.

    Raises
    ------
    ValueError
        If the mask length does not match the matrices, or no row is
        accepted (a fully rejected prior admits no posterior curve; that
        outcome must be handled upstream as a contradiction between model
        and observation).
    """
    accept = np.asarray(accept, dtype=bool)
    matrix_tran = run.result.failure_matrix_tran
    matrix_stat = run.result.failure_matrix_stat
    if accept.shape[0] != matrix_tran.shape[0]:
        raise ValueError(
            f"acceptance mask has {accept.shape[0]} rows for "
            f"{matrix_tran.shape[0]} matrix rows."
        )
    n_accepted = int(accept.sum())
    if n_accepted == 0:
        raise ValueError(
            "no accepted rows: the prior is fully rejected by the survival "
            "constraint, so no posterior fragility exists. This contradicts "
            "the observed survival and must be investigated upstream."
        )

    grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
    accepted_tran = matrix_tran[accept, :]
    accepted_stat = matrix_stat[accept, :]
    p_trans = accepted_tran.mean(axis=0)
    p_static = accepted_stat.mean(axis=0)

    cis = {
        "transient": binomial_ci(p_trans, n_accepted, confidence),
        "static": binomial_ci(p_static, n_accepted, confidence),
    }

    seed = int(
        np.random.SeedSequence(
            [int(run.config.mc.seed), _POSTERIOR_BOOTSTRAP_SALT]
        ).generate_state(1)[0]
    )
    rng = np.random.default_rng(seed)
    alpha = (1.0 - confidence) / 2.0
    boot_trans = np.empty((n_bootstrap, grid.size), dtype=np.float64)
    boot_stat = np.empty((n_bootstrap, grid.size), dtype=np.float64)
    for b in range(n_bootstrap):
        rows = rng.integers(0, n_accepted, size=n_accepted)
        boot_trans[b] = accepted_tran[rows, :].mean(axis=0)
        boot_stat[b] = accepted_stat[rows, :].mean(axis=0)
    bands = {
        "transient": (
            np.quantile(boot_trans, alpha, axis=0),
            np.quantile(boot_trans, 1.0 - alpha, axis=0),
        ),
        "static": (
            np.quantile(boot_stat, alpha, axis=0),
            np.quantile(boot_stat, 1.0 - alpha, axis=0),
        ),
    }

    datum = float(run.config.geometry.z_toe)
    return PosteriorFragility(
        conditioning_grid=grid,
        P_f_trans_post_raw=p_trans,
        P_f_static_post_raw=p_static,
        binomial_ci=cis,
        bootstrap_bands=bands,
        P_f_trans_post_fit=_fit_or_none(grid, p_trans, datum),
        P_f_static_post_fit=_fit_or_none(grid, p_static, datum),
        n_accepted=n_accepted,
        settings={
            "path": "masked_matrix",
            "n_bootstrap": int(n_bootstrap),
            "confidence": float(confidence),
            "bootstrap_seed": seed,
            "datum_m": datum,
        },
    )


def verify_posterior_fragility_by_reevaluation(
    run: Phase1Run,
    accept: NDArray[np.bool_],
    posterior: PosteriorFragility,
) -> dict[str, Any]:
    """Re-evaluate accepted rows on the conditioning grid; require exactness.

    Rebuilds the run's per-level loading records
    (:func:`~bep_reliability_engine.run.conditioning_hydrographs_for_config`)
    and pushes only the accepted rows (with their regenerated L_j) through
    :func:`~bep_reliability_engine.evaluator.evaluate_batch` per level. The
    resulting failure fractions must equal the masked-matrix posterior
    curves EXACTLY: same kernels, same records, same rows, so any deviation
    proves the reconstructed context differs from the Phase 1 run.

    Parameters
    ----------
    run : Phase1Run
        The loaded Phase 1 run.
    accept : numpy.ndarray, bool
        The operative acceptance mask.
    posterior : PosteriorFragility
        The masked-matrix posterior to verify against.

    Returns
    -------
    dict
        ``verified`` (True), the maximum absolute deviations (0.0 on
        success) and the flag-mismatch counts (0 on success).

    Raises
    ------
    AssertionError
        If any re-evaluated failure flag differs from the retained matrix
        entry for an accepted row, or the recomputed fractions differ from
        the masked-matrix curves.
    """
    accept = np.asarray(accept, dtype=bool)
    theta_accepted = run.theta[accept, :]
    seepage = run.seepage_length_samples
    seepage_accepted = None if seepage is None else seepage[accept]
    config = run.config

    records = conditioning_hydrographs_for_config(config)
    grid = np.asarray(run.result.conditioning_grid, dtype=np.float64)
    if len(records) != grid.size:
        raise AssertionError(
            f"rebuilt {len(records)} conditioning records for a grid of "
            f"{grid.size} levels."
        )

    retained_stat = run.result.failure_matrix_stat[accept, :]
    retained_tran = run.result.failure_matrix_tran[accept, :]
    # Optional M8 keywords the parent run may carry. They must be forwarded or
    # this function re-evaluates a DIFFERENT model from the one that produced
    # the matrices it is checking, and reports the difference as a verification
    # failure. All three default to None/absent, so a production run is
    # unaffected; the arms of ADR-0045, ADR-0049 and ADR-0050 are not.
    model_factor_accepted = (
        None if run.model_factor_samples is None else run.model_factor_samples[accept]
    )
    flag_mismatch_static = 0
    flag_mismatch_trans = 0
    p_trans = np.empty(grid.size, dtype=np.float64)
    p_static = np.empty(grid.size, dtype=np.float64)
    for i, record in enumerate(records):
        col_static, col_trans = evaluate_batch(
            theta_accepted,
            record,
            run.geometry,
            l_ini=0.0,
            seepage_length_samples=seepage_accepted,
            alpha_exponent=config.alpha_exponent,
            alpha_exponent_transient=config.alpha_exponent_transient,
            theta_repose_rad=config.theta_repose_rad,
            relative_density=config.relative_density_insitu,
            foreland_open=config.foreland_treatment == "open_entry",
            progression_backend=config.timestepper.progression_backend,
            model_factor_samples=model_factor_accepted,
            critical_length_factor=config.critical_length_factor,
            toe_gradient_relief_factor=config.toe_gradient_relief_factor,
        )
        flag_mismatch_static += int((col_static != retained_stat[:, i]).sum())
        flag_mismatch_trans += int((col_trans != retained_tran[:, i]).sum())
        p_static[i] = col_static.mean()
        p_trans[i] = col_trans.mean()

    max_dev_trans = float(np.max(np.abs(p_trans - posterior.P_f_trans_post_raw)))
    max_dev_static = float(np.max(np.abs(p_static - posterior.P_f_static_post_raw)))
    report = {
        "verified": bool(
            flag_mismatch_static == 0
            and flag_mismatch_trans == 0
            and max_dev_trans == 0.0
            and max_dev_static == 0.0
        ),
        "flag_mismatch_static": flag_mismatch_static,
        "flag_mismatch_trans": flag_mismatch_trans,
        "max_abs_dev_trans": max_dev_trans,
        "max_abs_dev_static": max_dev_static,
        "n_accepted": int(accept.sum()),
        "n_levels": int(grid.size),
    }
    if not report["verified"]:
        raise AssertionError(
            "re-evaluation verification FAILED: the reconstructed replay "
            f"context is not identical to the Phase 1 run ({report})."
        )
    logger.info(
        "Posterior fragility verification passed: %d accepted rows x %d "
        "levels re-evaluated, zero flag mismatches, exact curve agreement.",
        report["n_accepted"],
        report["n_levels"],
    )
    return report
