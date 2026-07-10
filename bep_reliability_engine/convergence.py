"""Statistical convergence study: estimator CoV vs N, LHS vs crude Monte Carlo.

Single responsibility: the *statistical* machinery for the spec §11 convergence
study and the spec §12 fm5 tail-variance question, with **no physics** — the
limit-state evaluation is injected as a callable, exactly as ``run.py`` keeps
physics inside M8. Two questions, one replicate design (ADR-0031):

* **Estimator convergence (spec §11).** Does N = 10⁵ resolve the failure
  probabilities of interest? The spec target is a Monte Carlo estimator
  coefficient of variation ``CoV(P̂_f) < 5%`` across the relevant failure range
  (Schweckendiek 2014), expected to fall as ``1/sqrt(N)``. The per-run
  ``metadata['mc_convergence']`` block records the *analytic binomial* CoV at
  the single operating N; this module measures the **empirical** replicate CoV
  across a ladder of N, which needs no iid assumption and so also tests whether
  the production LHS sampler actually follows the binomial law.
* **Tail variance (spec §12 fm5).** LHS stratifies marginals; the deep transient
  tail is governed by the multiplicative C_e×k_aq interaction (fm7). Whether LHS
  beats crude Monte Carlo *in the tail* must be measured, not assumed. Running
  the same replicate ladder for both samplers — LHS (``stratified=True``) and
  crude MC (``stratified=False``), both from
  :func:`~bep_reliability_engine.tail_sampling.sample_theta_tilted` with no tilt
  so the LHS arm is bit-identical to production M2 — gives the variance-reduction
  ratio ``CoV_MC / CoV_LHS`` per conditioning level, and its decay from bulk to
  tail is the fm5 answer.

Design contract
---------------
:func:`run_replicates` draws ``n_replicates`` independent θ populations at one N
under one sampler and reduces each to its per-branch failure fraction. The two
physics dependencies are **injected**:

* ``evaluate(theta_sample, seepage) -> (fail_static, fail_trans)`` — one M8
  ``evaluate_batch`` call at the fixed conditioning level (the driver closes over
  the built hydrograph record and geometry).
* ``draw_length(replicate_index, n_samples) -> seepage | None`` — the per-
  replicate stochastic seepage length L. The driver derives its seed from the
  ``(level, replicate)`` pair **only**, so the *same* L feeds LHS and crude MC at
  a given replicate index and the two schemes differ **only** in the θ design —
  the clean isolation the fm5 question requires (matching ADR-0029's protocol).

All seeds derive from a single ``seed_root`` via ``numpy.random.SeedSequence``,
so a whole study is reproducible from one integer, and the θ streams of the two
samplers are independent (distinct ``scheme_tag``).

References
----------
Spec §11 (convergence diagnostic, the 5% CoV target, 1/sqrt(N)), §12 fm5/fm7
(LHS-vs-crude tail variance, the C_e×k_aq interaction). ADR-0029 (the tilted-IS
tail study this complements), ADR-0031 (this study). Schweckendiek (2014) for
the < 5% CoV field standard.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from bep_reliability_engine.fragility import PF_COV_TARGET
from bep_reliability_engine.sampling import MarginalSpec, ThetaSample
from bep_reliability_engine.tail_sampling import sample_theta_tilted

__all__ = [
    "PF_COV_TARGET",
    "ReplicateSample",
    "binomial_cov",
    "empirical_cov",
    "n_for_cov_target",
    "run_replicates",
]

# Physics callables injected by the driver (no physics lives in this module).
EvaluateFn = Callable[
    [ThetaSample, "NDArray[np.float64] | None"],
    "tuple[NDArray[np.bool_], NDArray[np.bool_]]",
]
DrawLengthFn = Callable[[int, int], "NDArray[np.float64] | None"]


def empirical_cov(p_f_replicates: NDArray[np.float64]) -> float:
    """Empirical coefficient of variation of a replicated ``P̂_f``.

    The ground-truth estimator precision: ``std(P̂_f) / mean(P̂_f)`` over the
    replicate seeds, with the sample standard deviation (``ddof=1``). Needs no
    distributional assumption, so it measures the true CoV of whichever sampler
    produced the replicates (unlike the analytic binomial formula, which assumes
    iid draws).

    Parameters
    ----------
    p_f_replicates : numpy.ndarray, shape (R,)
        The ``R`` replicate point estimates of ``P_f`` at one (sampler, N,
        conditioning level).

    Returns
    -------
    float
        The empirical CoV, or ``nan`` when the replicate mean is 0 (every
        replicate saw zero failures — the estimator is blind at this depth and
        N, which is itself the reportable finding).
    """
    p = np.asarray(p_f_replicates, dtype=np.float64)
    if p.size < 2:
        return float("nan")
    mean = float(p.mean())
    if mean <= 0.0:
        return float("nan")
    return float(p.std(ddof=1) / mean)


def binomial_cov(p: float, n_samples: int) -> float:
    """Analytic CoV of the crude Monte Carlo (iid binomial) ``P̂_f`` estimator.

    ``CoV(P̂_f) = sqrt((1 - p) / (N p))`` — the ``1/sqrt(N)`` reference the
    empirical CoV is compared against (spec §11). This is the exact estimator
    CoV for crude Monte Carlo and, per the fm5 finding, the *effective* CoV of
    LHS in the deep tail as well (where stratification of marginals buys nothing
    against the C_e×k_aq interaction).

    Parameters
    ----------
    p : float
        Failure probability at the conditioning level.
    n_samples : int
        Sample size N.

    Returns
    -------
    float
        The binomial estimator CoV, or ``nan`` for ``p`` outside ``(0, 1)``.
    """
    p = float(p)
    if not 0.0 < p < 1.0 or n_samples <= 0:
        return float("nan")
    return float(np.sqrt((1.0 - p) / (n_samples * p)))


def n_for_cov_target(p: float, cov_target: float = PF_COV_TARGET) -> float:
    """Binomial sample size N needed to reach a target estimator CoV at ``p``.

    Inverts :func:`binomial_cov`: ``N = (1 - p) / (p · cov_target²)``. The
    ``1/p`` blow-up is the spec §11 reason a fixed N cannot hold the 5% target
    arbitrarily deep into the tail — each decade of ``p`` costs a decade of N.

    Parameters
    ----------
    p : float
        Failure probability at the conditioning level.
    cov_target : float, optional
        Target estimator CoV. Default :data:`PF_COV_TARGET` (0.05, the
        Schweckendiek 2014 field standard).

    Returns
    -------
    float
        The required N (a real number; round up in reporting), or ``nan`` for
        ``p`` outside ``(0, 1)``.
    """
    p = float(p)
    if not 0.0 < p < 1.0 or cov_target <= 0.0:
        return float("nan")
    return float((1.0 - p) / (p * cov_target**2))


@dataclass(frozen=True)
class ReplicateSample:
    """Replicated ``P̂_f`` estimates at one (sampler, N, conditioning level).

    Attributes
    ----------
    n_samples : int
        Sample size N behind each replicate estimate.
    stratified : bool
        ``True`` for the LHS (production) sampler, ``False`` for crude Monte
        Carlo.
    p_f_static, p_f_trans : numpy.ndarray, shape (R,)
        The ``R`` replicate failure fractions for the static and transient
        branches.
    n_failures_static, n_failures_trans : numpy.ndarray of int, shape (R,)
        Per-replicate failure counts (``0`` flags a blind replicate).
    """

    n_samples: int
    stratified: bool
    p_f_static: NDArray[np.float64]
    p_f_trans: NDArray[np.float64]
    n_failures_static: NDArray[np.int64]
    n_failures_trans: NDArray[np.int64]

    @property
    def scheme(self) -> str:
        """``'lhs'`` (stratified) or ``'crude_mc'`` (iid) label."""
        return "lhs" if self.stratified else "crude_mc"

    def cov(self, branch: str) -> float:
        """Empirical CoV of ``P̂_f`` for ``'static'`` or ``'transient'``."""
        return empirical_cov(self._branch(branch))

    def mean_p_f(self, branch: str) -> float:
        """Replicate-mean ``P̂_f`` for ``'static'`` or ``'transient'``."""
        return float(np.mean(self._branch(branch)))

    def zero_failure_fraction(self, branch: str) -> float:
        """Fraction of replicates that observed zero failures (blind runs)."""
        counts = self.n_failures_static if branch == "static" else self.n_failures_trans
        return float(np.mean(np.asarray(counts) == 0))

    def _branch(self, branch: str) -> NDArray[np.float64]:
        if branch == "static":
            return self.p_f_static
        if branch == "transient":
            return self.p_f_trans
        raise ValueError(f"branch {branch!r} must be 'static' or 'transient'.")


def _derive_seed(seed_root: int, *words: int) -> int:
    """A distinct, reproducible 32-bit seed from the root and integer tags."""
    return int(np.random.SeedSequence([int(seed_root), *words]).generate_state(1)[0])


def run_replicates(
    *,
    marginals: Sequence[MarginalSpec],
    sampler_kwargs: Mapping[str, Any],
    evaluate: EvaluateFn,
    draw_length: DrawLengthFn,
    n_samples: int,
    n_replicates: int,
    seed_root: int,
    stratified: bool,
    scheme_tag: int,
    level_tag: int,
) -> ReplicateSample:
    """Replicate ``P̂_f`` at one N under one sampler (LHS or crude MC).

    Draws ``n_replicates`` independent θ populations of size ``n_samples`` from
    :func:`~bep_reliability_engine.tail_sampling.sample_theta_tilted` with no
    tilt (``shift_z=None``) — ``stratified=True`` is the production LHS design
    (bit-identical to M2), ``stratified=False`` is the spec §13 crude-MC debug
    fallback — evaluates each against the injected physics at the fixed
    conditioning level, and reduces to per-branch failure fractions.

    Parameters
    ----------
    marginals : sequence of MarginalSpec
        The seven canonical marginals (``config.priors.to_marginal_specs()``).
    sampler_kwargs : mapping
        The remaining ``sample_theta_tilted`` keywords shared by every draw:
        ``rho_log_kaq_d70``, ``d70_interpretation``, ``coupling``, ``bounds``.
    evaluate : callable
        ``evaluate(theta_sample, seepage) -> (fail_static, fail_trans)``, one
        M8 batch at the fixed level; both returns are boolean ``(N,)`` arrays.
    draw_length : callable
        ``draw_length(replicate_index, n_samples) -> seepage | None``. Seeded
        from ``(level, replicate)`` only (not the sampler), so LHS and crude MC
        share the same L at each replicate index — isolating the θ-design effect.
    n_samples : int
        Sample size N for this ladder rung.
    n_replicates : int
        Number of independent replicate seeds R.
    seed_root : int
        Root entropy; every draw's seed derives from it via ``SeedSequence``.
    stratified : bool
        ``True`` for LHS, ``False`` for crude MC.
    scheme_tag : int
        Distinguishes the two samplers' independent θ seed streams.
    level_tag : int
        Distinguishes conditioning levels' seed streams.

    Returns
    -------
    ReplicateSample
        The R replicate failure fractions and counts for both branches.
    """
    p_f_static = np.empty(n_replicates, dtype=np.float64)
    p_f_trans = np.empty(n_replicates, dtype=np.float64)
    n_fail_static = np.empty(n_replicates, dtype=np.int64)
    n_fail_trans = np.empty(n_replicates, dtype=np.int64)

    for r in range(n_replicates):
        seed = _derive_seed(seed_root, scheme_tag, level_tag, n_samples, r)
        tilted = sample_theta_tilted(
            marginals,
            seed=seed,
            shift_z=None,
            n_samples=n_samples,
            stratified=stratified,
            **sampler_kwargs,
        )
        seepage = draw_length(r, n_samples)
        fail_static, fail_trans = evaluate(tilted.theta, seepage)
        p_f_static[r] = float(np.mean(fail_static))
        p_f_trans[r] = float(np.mean(fail_trans))
        n_fail_static[r] = int(np.sum(fail_static))
        n_fail_trans[r] = int(np.sum(fail_trans))

    return ReplicateSample(
        n_samples=int(n_samples),
        stratified=bool(stratified),
        p_f_static=p_f_static,
        p_f_trans=p_f_trans,
        n_failures_static=n_fail_static,
        n_failures_trans=n_fail_trans,
    )
