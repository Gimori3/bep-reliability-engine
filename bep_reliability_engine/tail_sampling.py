"""Deep-tail variance reduction: the tilted (importance) prior sampler.

Why this module exists (spec §12, failure modes 5 and 7)
---------------------------------------------------------
The deep transient failure tail is governed by the *multiplicative*
C_e x k_aq interaction, not by any single marginal, and LHS stratifies
marginals only — so the assumed LHS tail-variance advantage over crude Monte
Carlo is unverified there (fm5). The spec's stated mitigation is a
variance-reduction scheme "targeted at the joint tail (importance sampling or
subset simulation) ... for the lowest conditioning levels", with the sampler
interface left "open to substitution". This module is that substitute:
:func:`sample_theta_tilted` mirrors the M2 :func:`~bep_reliability_engine.\
sampling.sample_theta` surface and returns the same :class:`~bep_reliability_\
engine.sampling.ThetaSample` plus exact log importance weights, so the tilted
population drops straight into ``evaluate_batch``.

Importance sampling was chosen over subset simulation (ADR-0029): the
transient limit state is monotone in C_e and k_aq (both enter the Pol rate
multiplicatively, so more of either never prevents failure), which makes a
mean-shift proposal along exactly that interaction direction well-posed,
one-shot and reproducible from a single seed — whereas subset simulation's
adaptive MCMC levels would break the engine's front-loaded-RNG
reproducibility-by-construction and its fixed (N, N_h) failure-matrix
contracts. The **production sweep is untouched**: the Phase 2 handoff
requires the plain LHS prior ``theta_matrix`` and unweighted failure matrices
(spec §2, §8 — non-negotiable), so the tilted sampler is a *tail estimator*
for the lowest conditioning levels and for the fm5 verification study, never
a replacement population.

How the tilt works (and why the weights are exact)
--------------------------------------------------
The M2 pipeline is ``U (LHS) -> Z = Phi^-1(U) -> [copula] -> [marginal map]
-> [bounds clip]``. The tilt adds a constant ``nu_i`` to the *independent*
standard-normal column of each tilted parameter **before** the copula step:
the proposal for that column is N(nu, 1) instead of N(0, 1), i.e. an
exponential tilting of the Gaussian, and every step downstream of Z — the
Gaussian copula, the lognormal/normal marginal maps, the fm2 bounds clip —
is a fixed deterministic transform applied identically under prior and
proposal. The likelihood ratio therefore lives entirely in Z-space and is
exact::

    log w(z') = sum_i [ -nu_i * z'_i + nu_i**2 / 2 ]      (z' ~ N(nu_i, 1))

For a lognormal marginal a Z-shift of ``nu`` is a physical-space scale
factor ``exp(nu * sigma_ln)`` on that parameter (the proposal stays
lognormal with the same sigma_ln), so tilting (k_aq, C_e) pushes samples
straight up the high-C_e x high-k_aq corner that dominates the transient
tail (fm7) while leaving the other five marginals and the copula structure
untouched. In ``'correlated'`` coupling the k_aq shift propagates to d_70
through the copula exactly as physics requires (a coherent joint shift);
the weight formula is unchanged because the copula is downstream of Z.

Estimator: ``P_f = (1/N) * sum_j w_j * I_j`` (:func:`importance_estimate`),
unbiased under both iid and LHS-stratified proposals (LHS is unbiased for
any integrable integrand; its reported standard error uses the iid formula
and is mildly conservative under stratification — the fm5 study measures
replicate CoV empirically instead of trusting it). The shift is chosen by
one cross-entropy step from a pilot run (:func:`cross_entropy_shift`):
for a Gaussian family the CE-optimal mean is the weighted mean of the
failure-region Z values.

Crude Monte Carlo (the spec §13 "debug fallback", needed as the fm5 study
baseline) is the same pipeline with ``stratified=False`` and zero shift:
iid uniforms replace the LHS design, all weights are exactly 1.

Units and reproducibility follow M2 exactly: physical SI marginals, the
seed fully determines the draw, ``stratified=True`` with zero shift and
``coupling='two_population'`` reproduces ``sample_theta`` bit for bit
(pinned by ``tests/test_tail_sampling.py``).

References
----------
Spec §7 (the C_e x k_aq product note), §12 fm5/fm7, §13 (LHS + crude-MC
fallback). ADR-0029 (estimator decision and the fm5 study). Owen, "Monte
Carlo theory, methods and examples", ch. 9 (exponential tilting / mean-shift
IS); Rubinstein & Kroese (cross-entropy method).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm
from scipy.stats.qmc import LatinHypercube

from bep_reliability_engine.sampling import (
    PARAM_NAMES,
    CouplingMode,
    D70Interpretation,
    MarginalSpec,
    ThetaSample,
)

logger = logging.getLogger(__name__)

__all__ = [
    "TiltedSample",
    "TailEstimate",
    "sample_theta_tilted",
    "importance_estimate",
    "cross_entropy_shift",
]


@dataclass(frozen=True)
class TiltedSample:
    """A tilted prior draw: the M2 sample plus its exact importance weights.

    Attributes
    ----------
    theta : ThetaSample
        The physical-units ``(N, 7)`` sample in canonical column order —
        the same container the untilted M2 sampler returns, so downstream
        consumers (``evaluate_batch``) are agnostic to the tilt. Its
        ``metadata`` records the tilt provenance (``shift_z``,
        ``stratified``, ``sampling_scheme``).
    log_weights : numpy.ndarray, shape (N,)
        Exact log importance weights ``log w_j`` (module docstring). All
        zeros when ``shift_z`` is empty (crude MC / plain LHS).
    z_by_param : dict of str to numpy.ndarray
        The post-shift, pre-copula standard-normal column per parameter
        (the proposal-space coordinates). Retained so
        :func:`cross_entropy_shift` and tail diagnostics can run without
        re-deriving Z from physical values.
    shift_z : dict of str to float
        The applied Z-space shift per tilted parameter (empty = no tilt).
    """

    theta: ThetaSample
    log_weights: NDArray[np.float64]
    z_by_param: dict[str, NDArray[np.float64]] = field(repr=False)
    shift_z: dict[str, float] = field(default_factory=dict)

    @property
    def weights(self) -> NDArray[np.float64]:
        """Linear importance weights ``exp(log_weights)``."""
        return np.exp(self.log_weights)


@dataclass(frozen=True)
class TailEstimate:
    """One weighted failure-probability estimate with its precision.

    Attributes
    ----------
    p_f : float
        The importance-sampling estimate ``(1/N) sum w_j I_j`` (equals the
        raw Monte Carlo fraction when all weights are 1).
    standard_error : float
        iid standard error of ``p_f`` (sample std of ``w_j I_j`` over
        sqrt(N)). Mildly conservative under an LHS-stratified proposal.
    cov : float
        ``standard_error / p_f`` — the spec §11 convergence metric, here on
        the weighted estimator. NaN when ``p_f`` is 0.
    n_failures : int
        Count of failed realizations (unweighted).
    n_effective : float
        Kish effective sample size of the *failure-region* weights,
        ``(sum w I)**2 / sum (w I)**2``. Small values flag weight
        degeneracy (a too-aggressive or misdirected tilt). NaN when no
        realization fails.
    n_samples : int
        Proposal sample size N.
    """

    p_f: float
    standard_error: float
    cov: float
    n_failures: int
    n_effective: float
    n_samples: int


def sample_theta_tilted(
    marginals: Sequence[MarginalSpec],
    *,
    seed: int,
    rho_log_kaq_d70: float,
    d70_interpretation: D70Interpretation,
    shift_z: Mapping[str, float] | None = None,
    n_samples: int = 100_000,
    coupling: CouplingMode = "two_population",
    bounds: Mapping[str, tuple[float, float]] | None = None,
    stratified: bool = True,
) -> TiltedSample:
    """Draw a tilted ``(N, 7)`` prior with exact importance weights.

    The substitutable-sampler entry point of spec §12 fm5: the M2 pipeline
    (LHS design -> standard normals -> copula -> marginal map -> fm2 bounds
    clip) with an optional Z-space mean shift on selected parameters applied
    *before* the copula, and the exact log likelihood ratio returned
    alongside (module docstring). With ``shift_z=None`` and
    ``stratified=True`` this reproduces M2 ``sample_theta`` bit for bit
    (two-population coupling) with all-zero weights; with
    ``stratified=False`` it is the spec §13 crude-MC debug fallback.

    Parameters
    ----------
    marginals : sequence of MarginalSpec
        Exactly the seven canonical marginals (any order), as for
        ``sample_theta``.
    seed : int
        Seed for the LHS design (``stratified=True``) or the iid uniform
        generator (``stratified=False``). Fully determines the draw.
    rho_log_kaq_d70 : float
        Log-space k_aq-d_70 target, imposed only in ``'correlated'``
        coupling — same semantics as M2.
    d70_interpretation : {'matrix', 'bulk'}
        Metadata label on the d_70 marginal (spec §7), passed through.
    shift_z : mapping of str to float, optional
        Z-space mean shift per parameter name (e.g. ``{'k_aq': 1.5,
        'C_e': 1.5}`` — the fm7 interaction direction). For a lognormal
        marginal a shift of ``nu`` multiplies that parameter's physical
        scale by ``exp(nu * sigma_ln)``. ``None`` or empty = no tilt,
        weights all 1.
    n_samples : int, optional
        Proposal sample size N. Default ``100_000`` (spec §13); tail
        studies typically use the reduced operating N.
    coupling : {'two_population', 'correlated'}, optional
        The M2 coupling mode. Default ``'two_population'`` — the ADR-0012
        production parameterization (note: M2's own default is
        ``'correlated'`` for spec-§7 fidelity; this module defaults to the
        adopted production mode because it exists to estimate *production*
        tails). In ``'correlated'`` mode a k_aq shift coherently shifts
        d_70 through the copula; the weights are unaffected (the copula is
        downstream of Z).
    bounds : mapping of str to (float, float), optional
        The fm2 physical clip, as for ``sample_theta``. Valid together with
        any tilt: the clip is a deterministic transform downstream of
        Z-space, so the weights stay exact (module docstring).
    stratified : bool, optional
        ``True`` (default): Latin Hypercube design, as everywhere in the
        engine. ``False``: iid uniforms — crude Monte Carlo, the fm5 study
        baseline.

    Returns
    -------
    TiltedSample
        The physical sample (a :class:`ThetaSample` with tilt provenance in
        its metadata), the exact ``(N,)`` log weights, the proposal-space Z
        columns, and the applied shifts.

    Raises
    ------
    ValueError
        On any malformed input: wrong marginal set, unknown ``shift_z`` or
        ``bounds`` keys, non-finite shifts, out-of-range rho, or a
        non-positive ``n_samples``.

    Notes
    -----
    Mathematical guarantees (pinned by ``tests/test_tail_sampling.py``):

    * **Unbiasedness.** ``E_q[w * f(theta)] = E_p[f(theta)]`` for any
      integrable f, under both iid and LHS proposals, for any shift and
      either coupling, with or without bounds — because the density ratio
      is taken in the independent-Z space upstream of every deterministic
      transform.
    * **Marginal shift.** A tilted lognormal column remains lognormal with
      unchanged ``sigma_ln`` and log-mean ``mu_ln + nu * sigma_ln``.
    * **Zero-shift degeneracy.** ``shift_z = {}`` gives ``w_j = 1``
      exactly, and with ``stratified=True`` reproduces the M2 sampler bit
      for bit in two-population coupling.
    """
    if n_samples < 1:
        raise ValueError(f"n_samples must be a positive integer, got {n_samples}.")
    if coupling not in ("correlated", "two_population"):
        raise ValueError(
            f"coupling {coupling!r} must be 'correlated' or 'two_population'."
        )
    if d70_interpretation not in ("matrix", "bulk"):
        raise ValueError(
            f"d70_interpretation {d70_interpretation!r} must be 'matrix' or 'bulk'."
        )

    spec_by_name: dict[str, MarginalSpec] = {}
    for spec in marginals:
        if spec.name in spec_by_name:
            raise ValueError(f"Duplicate marginal supplied for {spec.name!r}.")
        spec_by_name[spec.name] = spec
    missing = [name for name in PARAM_NAMES if name not in spec_by_name]
    if missing:
        raise ValueError(
            f"Missing marginal specs for {missing}; exactly the seven canonical "
            f"parameters {PARAM_NAMES} are required."
        )

    if coupling == "correlated" and not -1.0 < rho_log_kaq_d70 < 1.0:
        raise ValueError(
            f"rho_log_kaq_d70 {rho_log_kaq_d70!r} must lie in the open interval "
            "(-1, 1) when coupling='correlated'."
        )

    shifts: dict[str, float] = {}
    if shift_z:
        unknown = [name for name in shift_z if name not in PARAM_NAMES]
        if unknown:
            raise ValueError(
                f"shift_z keys {unknown} are not parameters; expected names from "
                f"{PARAM_NAMES}."
            )
        for name, value in shift_z.items():
            value = float(value)
            if not np.isfinite(value):
                raise ValueError(f"shift_z[{name!r}] must be finite, got {value!r}.")
            if value != 0.0:
                shifts[name] = value

    if bounds:
        unknown = [name for name in bounds if name not in PARAM_NAMES]
        if unknown:
            raise ValueError(
                f"bounds keys {unknown} are not parameters; expected names from "
                f"{PARAM_NAMES}."
            )

    n_dim = len(PARAM_NAMES)

    # --- 1. Uniform design: stratified LHS (the engine default, same
    # constructor as M2 so the zero-shift draw is bit-identical) or iid
    # uniforms (crude MC, the fm5 baseline).
    if stratified:
        design = LatinHypercube(d=n_dim, seed=seed).random(n_samples)
    else:
        design = np.random.default_rng(seed).uniform(size=(n_samples, n_dim))

    # --- 2. Independent standard normals (each column stratified when LHS).
    z = norm.ppf(design)

    # --- 3. THE TILT (before the copula): shift the independent column of
    # each tilted parameter; the proposal there is N(nu, 1). The exact log
    # likelihood ratio is accumulated per tilted column:
    #   log w = -nu * z' + nu**2 / 2,   z' the post-shift draw.
    log_weights = np.zeros(n_samples, dtype=np.float64)
    for name, nu in shifts.items():
        j = PARAM_NAMES.index(name)
        z[:, j] = z[:, j] + nu
        log_weights += -nu * z[:, j] + 0.5 * nu * nu

    # Proposal-space Z retained per parameter (cross-entropy + diagnostics).
    z_by_param = {name: z[:, j].copy() for j, name in enumerate(PARAM_NAMES)}

    # --- 4. Copula step (correlated mode only), identical to M2: k_aq is
    # the anchor, d_70 absorbs the mix. Downstream of the tilt, so a k_aq
    # shift propagates into d_70 coherently and the weights are unchanged.
    if coupling == "correlated":
        i_kaq = PARAM_NAMES.index("k_aq")
        i_d70 = PARAM_NAMES.index("d_70")
        rho = float(rho_log_kaq_d70)
        z[:, i_d70] = rho * z[:, i_kaq] + np.sqrt(1.0 - rho**2) * z[:, i_d70]

    # --- 5. Marginal map, identical to M2 (moment-matched lognormal /
    # normal), then the fm2 bounds clip — both deterministic, weights exact.
    theta = np.empty((n_samples, n_dim), dtype=np.float64)
    for j, name in enumerate(PARAM_NAMES):
        spec = spec_by_name[name]
        if spec.family == "lognormal":
            sigma_ln = np.sqrt(np.log(1.0 + spec.cov**2))
            mu_ln = np.log(spec.mean) - 0.5 * sigma_ln**2
            theta[:, j] = np.exp(mu_ln + sigma_ln * z[:, j])
        else:  # normal: sigma = mean * COV
            theta[:, j] = spec.mean + spec.mean * spec.cov * z[:, j]

    clipped_fraction: dict[str, float] = {}
    if bounds:
        for name, (low, high) in bounds.items():
            j = PARAM_NAMES.index(name)
            col = theta[:, j]
            n_out = int(np.count_nonzero((col < low) | (col > high)))
            clipped_fraction[name] = n_out / n_samples
            theta[:, j] = np.clip(col, low, high)

    metadata: dict[str, Any] = {
        "param_names": list(PARAM_NAMES),
        "n_samples": int(n_samples),
        "seed": int(seed),
        "sampling_scheme": (
            "latin_hypercube_tilted" if stratified else "crude_mc_tilted"
        ),
        "stratified": bool(stratified),
        "coupling": coupling,
        "correlation_space": "log",
        "rho_log_kaq_d70": float(rho_log_kaq_d70),
        "rho_imposed": coupling == "correlated",
        "d70_interpretation": d70_interpretation,
        "shift_z": {k: float(v) for k, v in shifts.items()},
        "prior_families": {name: spec_by_name[name].family for name in PARAM_NAMES},
        "prior_means": {name: float(spec_by_name[name].mean) for name in PARAM_NAMES},
        "prior_covs": {name: float(spec_by_name[name].cov) for name in PARAM_NAMES},
        "c_e_stochastic": True,
        "bounds": (
            {k: (float(v[0]), float(v[1])) for k, v in bounds.items()}
            if bounds
            else None
        ),
        "clipped_fraction": clipped_fraction or None,
        "importance_sampling": bool(shifts),
    }

    if shifts:
        logger.info(
            "Tilted prior draw: N=%d, shifts %s (Z-space), %s design.",
            n_samples,
            shifts,
            "LHS" if stratified else "iid",
        )

    return TiltedSample(
        theta=ThetaSample(
            theta_matrix=theta,
            param_names=list(PARAM_NAMES),
            metadata=metadata,
        ),
        log_weights=log_weights,
        z_by_param=z_by_param,
        shift_z=shifts,
    )


def importance_estimate(
    failure: NDArray[np.bool_],
    log_weights: NDArray[np.float64],
) -> TailEstimate:
    """Weighted failure-probability estimate from one tilted evaluation.

    Implements the standard (non-self-normalized, hence unbiased) importance
    estimator ``P_f = (1/N) sum_j w_j I_j`` with its iid standard error and
    the Kish effective size of the failure-region weights.

    Parameters
    ----------
    failure : numpy.ndarray of bool, shape (N,)
        Per-realization failure indicators from ``evaluate_batch`` on the
        tilted population (either branch; in practice the transient one —
        the static branch has no C_e exposure, ADR-0001, so tilting C_e
        only moves the transient tail).
    log_weights : numpy.ndarray of float, shape (N,)
        The ``TiltedSample.log_weights``. All-zero weights reduce the
        estimator to the raw Monte Carlo fraction exactly.

    Returns
    -------
    TailEstimate
        Point estimate, iid standard error, CoV, failure count, Kish
        effective failure sample size, and N.

    Notes
    -----
    The standard error uses the iid formula ``std(w * I) / sqrt(N)``; under
    an LHS-stratified proposal it is mildly conservative (spec §12 fm5's
    whole point is that stratification's *tail* benefit must be measured,
    not assumed — the ADR-0029 study measures replicate CoV empirically).
    """
    fail = np.asarray(failure, dtype=bool)
    log_w = np.asarray(log_weights, dtype=np.float64)
    if fail.shape != log_w.shape:
        raise ValueError(
            f"failure {fail.shape} and log_weights {log_w.shape} must share "
            "one (N,) shape."
        )
    n = fail.size
    if n == 0:
        raise ValueError("importance_estimate needs at least one realization.")

    weighted_indicator = np.where(fail, np.exp(log_w), 0.0)
    p_f = float(weighted_indicator.mean())
    if n > 1:
        standard_error = float(weighted_indicator.std(ddof=1) / np.sqrt(n))
    else:
        standard_error = float("nan")

    failure_weights = weighted_indicator[fail]
    if failure_weights.size:
        n_effective = float(
            failure_weights.sum() ** 2 / np.square(failure_weights).sum()
        )
    else:
        n_effective = float("nan")

    return TailEstimate(
        p_f=p_f,
        standard_error=standard_error,
        cov=float(standard_error / p_f) if p_f > 0.0 else float("nan"),
        n_failures=int(fail.sum()),
        n_effective=n_effective,
        n_samples=int(n),
    )


def cross_entropy_shift(
    sample: TiltedSample,
    failure: NDArray[np.bool_],
    parameters: Sequence[str] = ("k_aq", "C_e"),
) -> dict[str, float]:
    """One cross-entropy update of the Z-space shift from a pilot run.

    For a Gaussian proposal family the cross-entropy-optimal mean is the
    (importance-weighted) mean of the failure-region proposal coordinates
    (Rubinstein & Kroese)::

        nu*_i = sum_j w_j I_j z'_ij / sum_j w_j I_j

    Run a pilot (untilted LHS at reduced N, or a conservatively tilted
    draw), pass it here, and use the returned shifts for the production
    tilt. One step suffices in practice for the monotone C_e x k_aq tail;
    iterating is legitimate but each pilot costs a batch evaluation.

    Parameters
    ----------
    sample : TiltedSample
        The pilot draw (its ``z_by_param`` and ``log_weights`` are used).
        An untilted pilot has all-one weights, reducing the update to the
        plain mean of the failure-region Z.
    failure : numpy.ndarray of bool, shape (N,)
        Pilot failure indicators from ``evaluate_batch``.
    parameters : sequence of str, optional
        Which parameters to tilt. Default ``('k_aq', 'C_e')`` — the fm7
        interaction pair; the other five parameters' CE updates are near
        zero by construction and adding them mostly adds weight variance.

    Returns
    -------
    dict of str to float
        The CE-updated Z-space shift per requested parameter, ready to pass
        as ``shift_z``.

    Raises
    ------
    ValueError
        If no pilot realization fails (no CE update exists — raise rather
        than silently returning zeros), or a parameter is unknown.
    """
    fail = np.asarray(failure, dtype=bool)
    if not fail.any():
        raise ValueError(
            "cross_entropy_shift: the pilot produced no failures; enlarge the "
            "pilot N, raise the conditioning level, or seed a manual shift."
        )
    unknown = [name for name in parameters if name not in PARAM_NAMES]
    if unknown:
        raise ValueError(f"parameters {unknown} are not canonical names {PARAM_NAMES}.")

    weights = np.where(fail, np.exp(sample.log_weights), 0.0)
    total = float(weights.sum())
    return {
        name: float((weights * sample.z_by_param[name]).sum() / total)
        for name in parameters
    }
