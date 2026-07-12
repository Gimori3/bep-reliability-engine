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
]

_QUANTILES: tuple[float, ...] = (0.05, 0.25, 0.50, 0.75, 0.95)


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
