"""Prior-versus-posterior analysis: marginals, the C_e headline, correlations.

All theta access is by column NAME through ``param_names`` (never by
position). The scientific headline of the survival filter is the erosion
coefficient C_e (spec section 4, section 12 failure mode 7; thesis
methodology): the static branch has no C_e exposure (ADR-0001), so any
posterior tightening of C_e is attributable to the transient survival
constraint alone, and the expected signature is a downward shift of the
posterior C_e (with its high-C_e-times-high-k_aq corner preferentially
rejected), quantifying the laminar-flow conservatism the constraint can
remove.

Schweckendiek (2014) section 4.2.2 cautions that updating introduces or
changes correlations between the variables; the posterior sample carries
them exactly (rejection is joint), and :func:`correlation_shift` reports
the induced changes (Spearman rank, robust for the lognormal marginals) so
downstream users never mistake the posterior for a product of independent
marginals.

The seepage length is the one conditioned quantity that is not a theta
column, and until 2026-09-16 nothing here measured it. It is drawn
independently of theta, but the survival event depends on it, so with an
independent prior ``pi(theta, L) = pi(theta) pi(L)`` the conditioned
marginal is

    pi(L | S) = pi(L) * P(S | L) / P(S),

which equals ``pi(L)`` if and only if ``P(S | L)`` is constant in ``L``.
Rejection here is row-wise on the joint draw, so the retained sample
carries the conditioned L exactly; what was missing was any diagnostic that
looked at it. :func:`seepage_length_update` supplies one, and reports the
acceptance profile ``P(S | L)`` itself rather than only the moment shifts,
because a shifted mean is evidence of conditioning while an unshifted mean
is not evidence of its absence. See
``docs/decisions/survival-information-and-nesting-study.md``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import stats

__all__ = [
    "c_e_headline",
    "column",
    "correlation_shift",
    "marginal_summary",
    "prior_posterior_summary",
    "seepage_length_update",
]

_QUANTILES: tuple[float, ...] = (0.05, 0.25, 0.50, 0.75, 0.95)

# Deciles of the prior L draw for the acceptance profile P(S | L). Ten bins
# of 1e4 rows at production N give a per-bin binomial standard error under
# 0.005 at the acceptance levels actually observed, which is an order below
# the profile spread the production strata show.
_ACCEPTANCE_BINS: int = 10


def column(
    theta: NDArray[np.float64], param_names: list[str], name: str
) -> NDArray[np.float64]:
    """One named theta column (the no-positional-indexing accessor).

    Parameters
    ----------
    theta : numpy.ndarray, shape (N, 7)
        The sample matrix.
    param_names : list of str
        Canonical column names.
    name : str
        The requested parameter.

    Returns
    -------
    numpy.ndarray, shape (N,)
        The column values.

    Raises
    ------
    ValueError
        If the name is not a column.
    """
    try:
        return theta[:, param_names.index(name)]
    except ValueError:
        raise ValueError(
            f"unknown parameter {name!r}; columns are {param_names}."
        ) from None


def marginal_summary(values: NDArray[np.float64]) -> dict[str, float]:
    """Location, spread and quantiles of one marginal sample."""
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    std = float(values.std(ddof=1)) if values.size > 1 else float("nan")
    summary = {
        "n": int(values.size),
        "mean": mean,
        "std": std,
        "cov": std / mean if mean != 0.0 else float("nan"),
    }
    for q in _QUANTILES:
        summary[f"p{int(round(100 * q)):02d}"] = float(np.quantile(values, q))
    return summary


def prior_posterior_summary(
    theta: NDArray[np.float64],
    param_names: list[str],
    accept: NDArray[np.bool_],
) -> dict[str, Any]:
    """Per-parameter prior and posterior marginal statistics.

    Parameters
    ----------
    theta : numpy.ndarray, shape (N, 7)
        The full prior rows.
    param_names : list of str
        Canonical column names.
    accept : numpy.ndarray, shape (N,), bool
        The operative acceptance mask.

    Returns
    -------
    dict
        Per parameter: ``prior`` and ``posterior`` summaries, the relative
        mean shift, and the two-sample Kolmogorov-Smirnov statistic between
        the accepted subset and the full prior (a scale-free measure of how
        much the constraint moved this marginal; its p-value is not
        meaningful here because the subset is nested in the prior, so only
        the statistic is reported).
    """
    accept = np.asarray(accept, dtype=bool)
    result: dict[str, Any] = {}
    for name in param_names:
        prior_values = column(theta, param_names, name)
        posterior_values = prior_values[accept]
        prior = marginal_summary(prior_values)
        posterior = marginal_summary(posterior_values)
        if posterior_values.size and prior["mean"] != 0.0:
            shift = posterior["mean"] / prior["mean"] - 1.0
        else:
            shift = float("nan")
        if posterior_values.size:
            ks = float(stats.ks_2samp(posterior_values, prior_values).statistic)
        else:
            ks = float("nan")
        result[name] = {
            "prior": prior,
            "posterior": posterior,
            "relative_mean_shift": float(shift),
            "ks_statistic": ks,
        }
    return result


def c_e_headline(
    theta: NDArray[np.float64],
    param_names: list[str],
    accept: NDArray[np.bool_],
) -> dict[str, float]:
    """The laminar-conservatism headline: how the constraint moved C_e.

    Returns
    -------
    dict
        Prior and posterior C_e means, the posterior-to-prior mean ratio,
        the p95 shift (the calibration acts on the fast tail), and the
        rejection concentration: the rejection fraction inside the top
        prior decile of the product ``C_e * k_aq`` (the fm7 interaction
        driver) versus the overall rejection fraction.
    """
    accept = np.asarray(accept, dtype=bool)
    c_e = column(theta, param_names, "C_e")
    k_aq = column(theta, param_names, "k_aq")

    prior_mean = float(c_e.mean())
    posterior_mean = float(c_e[accept].mean()) if accept.any() else float("nan")
    prior_p95 = float(np.quantile(c_e, 0.95))
    posterior_p95 = (
        float(np.quantile(c_e[accept], 0.95)) if accept.any() else float("nan")
    )

    driver = c_e * k_aq
    top_decile = driver >= np.quantile(driver, 0.90)
    overall_rejection = float((~accept).mean())
    top_rejection = (
        float((~accept[top_decile]).mean()) if top_decile.any() else float("nan")
    )
    return {
        "prior_mean": prior_mean,
        "posterior_mean": posterior_mean,
        "posterior_over_prior_mean": (
            posterior_mean / prior_mean if prior_mean else float("nan")
        ),
        "prior_p95": prior_p95,
        "posterior_p95": posterior_p95,
        "rejection_fraction_overall": overall_rejection,
        "rejection_fraction_top_decile_ce_kaq": top_rejection,
        "rejection_concentration_ratio": (
            top_rejection / overall_rejection
            if overall_rejection > 0.0
            else float("nan")
        ),
    }


def correlation_shift(
    theta: NDArray[np.float64],
    param_names: list[str],
    accept: NDArray[np.bool_],
) -> dict[str, Any]:
    """Spearman rank correlations before and after filtering.

    Reports the full matrices plus the largest induced change, so the
    updating-induced dependence (Schweckendiek 2014 section 4.2.2) is
    visible instead of silently ignored.
    """
    accept = np.asarray(accept, dtype=bool)
    prior_rho = stats.spearmanr(theta).statistic
    posterior_rho = stats.spearmanr(theta[accept, :]).statistic
    prior_rho = np.atleast_2d(np.asarray(prior_rho, dtype=np.float64))
    posterior_rho = np.atleast_2d(np.asarray(posterior_rho, dtype=np.float64))
    delta = posterior_rho - prior_rho
    off_diagonal = ~np.eye(delta.shape[0], dtype=bool)
    flat_index = int(np.abs(np.where(off_diagonal, delta, 0.0)).argmax())
    i, j = np.unravel_index(flat_index, delta.shape)
    return {
        "param_names": list(param_names),
        "prior_spearman": prior_rho.tolist(),
        "posterior_spearman": posterior_rho.tolist(),
        "max_abs_shift": float(np.abs(delta[i, j])),
        "max_shift_pair": [param_names[int(i)], param_names[int(j)]],
        "max_shift_value": float(delta[i, j]),
    }


def seepage_length_update(
    seepage_length_samples: NDArray[np.float64],
    accept: NDArray[np.bool_],
    *,
    theta: NDArray[np.float64] | None = None,
    param_names: list[str] | None = None,
    bins: int = _ACCEPTANCE_BINS,
) -> dict[str, Any]:
    """How the survival constraint conditions the seepage length.

    The seepage length is drawn independently of ``theta`` (ADR-0001,
    ``sampling.sample_seepage_length``) but it is not independent of the
    survival event: it sets the critical head, the rate denominator and the
    breach criterion itself. Independence in the PRIOR therefore does not
    make the retained marginal equal to the prior marginal, and this
    function measures the difference instead of assuming it away.

    The reported object of record is ``acceptance_by_bin``, the empirical
    ``P(S | L)`` over equal-count bins of the prior draw. It is the
    discriminating quantity: the conditioned marginal equals the prior if
    and only if this profile is flat, whereas the mean shift can be small,
    or vanish by symmetry, while the profile is steep.

    Parameters
    ----------
    seepage_length_samples : numpy.ndarray, shape (N,)
        The per-row stochastic L actually used in the replay (row j pairs
        with theta row j and with ``accept`` element j).
    accept : numpy.ndarray, shape (N,), bool
        The operative acceptance mask.
    theta : numpy.ndarray, shape (N, 7), optional
        The prior rows. When given with ``param_names``, the induced
        dependence between L and each theta column is reported too.
    param_names : list of str, optional
        Canonical column names, required with ``theta``.
    bins : int
        Number of equal-count L bins for the acceptance profile.

    Returns
    -------
    dict
        ``prior`` and ``posterior`` marginal summaries, the relative mean
        and coefficient-of-variation shifts, the retained variance ratio,
        the two-sample Kolmogorov-Smirnov statistic, the acceptance profile
        with its bin edges, counts and spread, and (when ``theta`` is given)
        the prior and posterior Spearman rank correlations between L and
        every theta column with their induced changes.

    Raises
    ------
    ValueError
        If the array lengths disagree, or if exactly one of ``theta`` and
        ``param_names`` is given.
    """
    L = np.asarray(seepage_length_samples, dtype=np.float64)
    accept = np.asarray(accept, dtype=bool)
    if L.shape != accept.shape:
        raise ValueError(
            f"seepage length has shape {L.shape} against acceptance mask "
            f"{accept.shape}; the two must pair row for row."
        )
    if (theta is None) != (param_names is None):
        raise ValueError("theta and param_names must be given together.")

    prior = marginal_summary(L)
    retained = L[accept]
    posterior = marginal_summary(retained) if retained.size else None

    def _cov(summary: dict[str, float] | None) -> float:
        if summary is None or not summary["mean"]:
            return float("nan")
        return summary["std"] / summary["mean"]

    prior_cov, posterior_cov = _cov(prior), _cov(posterior)
    result: dict[str, Any] = {
        "prior": prior,
        "posterior": posterior,
        "prior_cov": prior_cov,
        "posterior_cov": posterior_cov,
        "relative_mean_shift": (
            posterior["mean"] / prior["mean"] - 1.0
            if posterior is not None and prior["mean"]
            else float("nan")
        ),
        "relative_cov_shift": (
            posterior_cov / prior_cov - 1.0 if prior_cov else float("nan")
        ),
        "variance_ratio": (
            (posterior["std"] / prior["std"]) ** 2
            if posterior is not None and prior["std"]
            else float("nan")
        ),
        "ks_statistic": (
            float(stats.ks_2samp(retained, L).statistic)
            if retained.size
            else float("nan")
        ),
    }

    # P(S | L) over equal-count bins of the prior draw. Quantile edges keep
    # the bin counts equal, so every bin's binomial error is the same.
    edges = np.quantile(L, np.linspace(0.0, 1.0, bins + 1))
    edges[-1] = np.nextafter(edges[-1], np.inf)
    index = np.clip(np.digitize(L, edges) - 1, 0, bins - 1)
    rates, counts = [], []
    for b in range(bins):
        member = index == b
        counts.append(int(member.sum()))
        rates.append(float(accept[member].mean()) if member.any() else float("nan"))
    finite = [r for r in rates if np.isfinite(r)]
    result["acceptance_by_bin"] = rates
    result["acceptance_bin_counts"] = counts
    result["acceptance_bin_edges"] = [float(e) for e in edges]
    result["acceptance_spread"] = (
        float(max(finite) - min(finite)) if finite else float("nan")
    )

    if theta is not None and param_names is not None:
        induced: dict[str, dict[str, float]] = {}
        for name in param_names:
            values = column(theta, param_names, name)
            rho_prior = float(stats.spearmanr(L, values).statistic)
            rho_post = (
                float(stats.spearmanr(retained, values[accept]).statistic)
                if retained.size > 2
                else float("nan")
            )
            induced[name] = {
                "spearman_prior": rho_prior,
                "spearman_posterior": rho_post,
                "shift": rho_post - rho_prior,
            }
        result["induced_dependence"] = induced
        finite_shifts = {k: v for k, v in induced.items() if np.isfinite(v["shift"])}
        if finite_shifts:
            worst = max(finite_shifts, key=lambda k: abs(finite_shifts[k]["shift"]))
            result["max_induced_shift_parameter"] = worst
            result["max_induced_shift_value"] = finite_shifts[worst]["shift"]
    return result
