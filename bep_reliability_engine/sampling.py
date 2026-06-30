"""M2 ``prior_sampler``: the seven-dimensional Latin Hypercube prior sampler.

Single responsibility (spec §1, M2): convert the seven marginal distribution
specifications into a stratified ``(N, 7)`` sample matrix in physical units,
with the mandatory k_aq-d_70 correlation imposed, and hand it downstream as a
named structure that never forces callers to index raw column numbers. This
module knows nothing about limit states.

The sampling kernel :func:`sample_theta` and the data containers
(:class:`MarginalSpec`, :class:`ThetaSample`) are implemented and exercised by
``tests/test_sampling.py``. The correlation method, and why it is preferred
over Iman-Conover rank reordering, is recorded under "Which column keeps
perfect LHS stratification" below and in the :func:`sample_theta` docstring.

The seepage length L is **not** part of the seven-dimensional theta vector: the
thesis samples it as a per-section stochastic geometric parameter independent of
the soil properties, so :func:`sample_seepage_length` draws it from a standalone
1-D LHS keyed by its own (run-derived) seed, leaving the k_aq-d_70 copula
untouched.

Canonical column order (the M2 data-flow contract, spec §2)
-----------------------------------------------------------
``PARAM_NAMES = ['k_aq', 'd_70', 'D_aq', 'D_bl', 'k_bl', 'gamma_bl_sub', 'C_e']``

This is the single authoritative ordering for the whole engine; the consuming
modules (M6 ``sellmeijer``, M4 ``hydraulics``, M8 ``evaluator``) read their
columns by name against this exact list, so it must not drift. M2 owns it;
``theta_matrix`` rows are LHS draws and columns are physical-units values.

Sampling algorithm (spec §7, "Implementation")
----------------------------------------------
1. Stratified uniform LHS design ``U`` in ``(0, 1)^(N x 7)`` via
   ``scipy.stats.qmc.LatinHypercube(d=7, seed=seed)``; column ``j`` is the
   ``PARAM_NAMES[j]`` axis. The seed fully determines the matrix (spec §13;
   docs/conventions.md: deterministic RNG seeds everywhere).
2. Map to independent standard normals columnwise, ``Z = Phi^-1(U)``; each
   column inherits the LHS stratification.
3. Impose the k_aq-d_70 correlation (correlated mode only) by the conditional
   Gaussian-copula construction with **k_aq as the anchor**::

       z'_kaq  = z_kaq
       z'_d70  = rho * z_kaq + sqrt(1 - rho**2) * z_d70

   so ``corr(z'_kaq, z'_d70) = rho`` while both stay standard normal.
4. Map each standard-normal column to physical units through its marginal
   inverse CDF (lognormal or normal; see :class:`MarginalSpec`).
5. Optionally clip to physically defensible per-parameter ``bounds`` (the spec
   §12 failure-mode-2 guard against pathological H_c tails).
6. Wrap as a :class:`ThetaSample`.

Why the correlation is specified in *log* space (the Nataf collapse)
--------------------------------------------------------------------
The one mandatory correlation couples k_aq and d_70, and **both are
lognormal**. The standard-normal (Gaussian-copula) variables underlying a
lognormal are exactly its logs, so a correlation target stated as
``rho(ln k_aq, ln d_70)`` *is* the Gaussian-copula correlation directly:
``rho_gauss = rho_log`` with no Nataf root-finding. This is precisely why the
spec supplies the target in log space (spec §7; this module's
``rho_log_kaq_d70`` argument). Generalizing to a correlation that involves a
*normal* marginal, or to a target stated in physical space, would reinstate
the Nataf integral and is a documented future extension (spec §7: "any further
empirically identified correlations applied through the same transform").

Which column keeps perfect LHS stratification (design decision, flag for ADR)
-----------------------------------------------------------------------------
Steps 2 and 4 are monotone per column, so for every column left untouched by
step 3 the marginal CDF of the physical sample reproduces the original LHS
uniform exactly and the one-point-per-stratum coverage is preserved. Step 3
mixes only the *second* correlated variable, so **k_aq (the anchor) and the
five independent variables retain perfect stratification, while d_70 alone
carries the correlation perturbation** and is only approximately uniform.

The choice to anchor on k_aq (rather than d_70) is deliberate: k_aq has
COV 0.50 and co-drives the deep failure tail with C_e through the
multiplicative C_e * k_aq interaction (spec §7; §12 failure modes 5 and 7),
so preserving its stratification preserves the LHS variance reduction exactly
where it pays off, whereas d_70 (COV 0.10, tight) absorbs the perturbation at
little cost. This asymmetry is the "perturbation that imposing correlation
introduces" the stratification test must account for, and is a candidate for a
dedicated ADR.

Two-population fallback (spec §7, §13)
--------------------------------------
If the OYO 1999 paired records show the matrix grain size and the bulk
conductivity to be statistically decoupled, the single correlated population
is replaced by a two-population soil model (erodible sand matrix vs armouring
gravel framework) in which k_aq and d_70 are sampled independently. Select it
with ``coupling='two_population'``: step 3 is skipped, ``rho_log_kaq_d70`` is
not imposed, and both k_aq and d_70 then retain perfect LHS stratification.
Both the matrix and bulk d_70 interpretations are carried as primary runs, so
``d70_interpretation`` ('matrix' | 'bulk') is recorded in the returned metadata
for the §8 stratified decomposition; it labels which physical grain-size
definition the supplied d_70 marginal represents and does not itself alter the
sampling math.

Units and reproducibility
-------------------------
Marginals are specified and returned in strict SI / kN-m^3 physical units
(docs/conventions.md): k_aq, k_bl [m/s]; d_70, D_aq, D_bl [m]; gamma_bl_sub
[kN/m^3]; C_e [-]. Unit conversion happens only in M1 config loading, never
here. M1 ``config`` does not exist yet, so the marginal specs, the target
log-space correlation, the seed, and the d70 interpretation are taken as direct
arguments rather than read from a config object.

References
----------
Spec §1 (M2 responsibility), §2 (the theta_matrix / param_names contract),
§7 (the seven-dimensional vector, the marginal table, the mandatory Nataf
coupling and the two-population fallback), §10 (``scipy.stats.qmc``), §12
(failure mode 2 prior bounds; failure modes 5 and 7 on the C_e * k_aq tail),
§13 (single decisions: LHS, N = 1e5, mandatory coupling, d70 interpretation).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm
from scipy.stats.qmc import LatinHypercube

logger = logging.getLogger(__name__)

__all__ = [
    "PARAM_NAMES",
    "MarginalFamily",
    "CouplingMode",
    "D70Interpretation",
    "MarginalSpec",
    "ThetaSample",
    "sample_theta",
    "sample_seepage_length",
]

# Canonical theta-vector column order (spec §2, the M2 data-flow contract).
# This is the single source of the ordering; M6/M4/M8 read columns by name
# against this list. Do not reorder.
PARAM_NAMES: list[str] = [
    "k_aq",
    "d_70",
    "D_aq",
    "D_bl",
    "k_bl",
    "gamma_bl_sub",
    "C_e",
]

MarginalFamily = Literal["lognormal", "normal"]
CouplingMode = Literal["correlated", "two_population"]
D70Interpretation = Literal["matrix", "bulk"]


@dataclass(frozen=True)
class MarginalSpec:
    """One parameter's marginal distribution specification (spec §7).

    A pure, validated data holder: the moment-matching that turns ``mean`` and
    ``cov`` into distribution parameters lives in the sampler, not here, so
    this class never anticipates the sampler's arithmetic.

    Parameters
    ----------
    name : str
        Parameter name; must be one of :data:`PARAM_NAMES`.
    family : {'lognormal', 'normal'}
        Marginal family. All seven canonical variables are Lognormal;
        gamma_bl_sub (the submerged blanket weight) is Lognormal per ADR-0016
        and the thesis blanket prior, deviating from the Normal of spec §7.
        The 'normal' family remains supported by this data holder.
    mean : float
        Marginal mean in physical units (m/s, m, kN/m^3 or dimensionless as
        appropriate). Must be > 0 for a lognormal family.
    cov : float
        Coefficient of variation (std / mean), dimensionless. Must be >= 0.
        Note this is the *fraction* (e.g. 0.50), not a percentage; M1 config
        validation is what catches a 50-vs-0.50 unit error before a long run
        (spec §1), and the sampler re-asserts the COV is a fraction.

    Notes
    -----
    For a lognormal marginal the implementation will moment-match via
    ``sigma_ln**2 = ln(1 + cov**2)`` and ``mu_ln = ln(mean) - sigma_ln**2 / 2``
    so the physical mean and COV are reproduced exactly. For a normal marginal
    ``sigma = mean * cov``. These relations are stated for the implementer and
    are intentionally *not* exposed as helpers, so the tests can recompute them
    independently as a genuine check.
    """

    name: str
    family: MarginalFamily
    mean: float
    cov: float

    def __post_init__(self) -> None:
        if self.name not in PARAM_NAMES:
            raise ValueError(
                f"MarginalSpec.name {self.name!r} is not one of the canonical "
                f"parameter names {PARAM_NAMES}."
            )
        if self.family not in ("lognormal", "normal"):
            raise ValueError(
                f"MarginalSpec.family {self.family!r} must be 'lognormal' or "
                "'normal'."
            )
        if self.cov < 0.0:
            raise ValueError(
                f"MarginalSpec.cov {self.cov!r} for {self.name!r} must be >= 0."
            )
        if self.family == "lognormal" and not self.mean > 0.0:
            raise ValueError(
                f"Lognormal marginal {self.name!r} needs mean > 0, got "
                f"{self.mean!r}."
            )


@dataclass(frozen=True)
class ThetaSample:
    """The M2 sample handed downstream: named structure plus ndarray view.

    The hot loops consume :attr:`theta_matrix` directly (a C-contiguous
    ``(N, 7)`` ``float64`` array in :data:`PARAM_NAMES` order); analysis and
    persistence code use the named accessors so column identities are never
    in doubt (spec §2: "downstream modules never index into raw column
    numbers").

    Attributes
    ----------
    theta_matrix : numpy.ndarray, shape (N, 7)
        The stratified prior draws in physical units, canonical column order.
        This is the ndarray view for the hot loops (M4/M6/M8 read it as-is).
    param_names : list of str
        A copy of :data:`PARAM_NAMES`; ``theta_matrix[:, param_names.index(x)]``
        is the column for parameter ``x``.
    metadata : dict
        Run-provenance record carried into the §8 HDF5 attrs. Documented keys:
        ``param_names``, ``n_samples``, ``seed``, ``sampling_scheme``
        (= 'latin_hypercube'), ``coupling`` ('correlated' | 'two_population'),
        ``correlation_space`` (= 'log'), ``rho_log_kaq_d70`` (the target),
        ``rho_imposed`` (bool; False in two-population mode),
        ``d70_interpretation`` ('matrix' | 'bulk'), ``prior_families``,
        ``prior_means``, ``prior_covs`` (each a name->value dict),
        ``c_e_stochastic`` (= True, ADR-0001), and ``bounds`` (or None).
    """

    theta_matrix: NDArray[np.float64]
    param_names: list[str] = field(default_factory=lambda: list(PARAM_NAMES))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def n_samples(self) -> int:
        """Number of realizations N (rows of :attr:`theta_matrix`)."""
        return int(self.theta_matrix.shape[0])

    def column(self, name: str) -> NDArray[np.float64]:
        """Return the ``(N,)`` column for parameter ``name`` (named access).

        Parameters
        ----------
        name : str
            One of :attr:`param_names`.

        Returns
        -------
        numpy.ndarray, shape (N,)
            A view into :attr:`theta_matrix`.

        Raises
        ------
        KeyError
            If ``name`` is not a known parameter.
        """
        try:
            index = self.param_names.index(name)
        except ValueError as exc:
            raise KeyError(
                f"{name!r} is not a parameter; expected one of " f"{self.param_names}."
            ) from exc
        return self.theta_matrix[:, index]

    def as_named_dict(self) -> dict[str, NDArray[np.float64]]:
        """Return ``{name: column}`` for all parameters (e.g. for plotting)."""
        return {name: self.column(name) for name in self.param_names}


def sample_theta(
    marginals: Sequence[MarginalSpec],
    *,
    seed: int,
    rho_log_kaq_d70: float,
    d70_interpretation: D70Interpretation,
    n_samples: int = 100_000,
    coupling: CouplingMode = "correlated",
    bounds: Mapping[str, tuple[float, float]] | None = None,
) -> ThetaSample:
    """Draw the ``(N, 7)`` LHS prior with the k_aq-d_70 coupling imposed (M2).

    Generates the stratified Latin Hypercube design, imposes the mandatory
    k_aq-d_70 correlation through the log-space Gaussian copula (or skips it in
    the two-population fallback), maps to physical units, and returns the
    :class:`ThetaSample`. The ``seed`` fully determines the result (spec §13).

    **Method.** The mandatory k_aq-d_70 correlation is imposed with a
    Gaussian-copula (Nataf) conditional construction anchored on k_aq --
    ``z_d70 <- rho*z_kaq + sqrt(1-rho**2)*z_d70`` applied to the standard-normal
    images of the LHS design before the marginal map. For the single
    lognormal-lognormal pair the log-space target *is* the Gaussian-copula
    correlation, so no Nataf root-find is needed. This preserves the LHS
    stratification of every column except d_70 (k_aq and the five independent
    variables keep exact one-per-stratum coverage) -- the best preservation a
    copula transform allows; anchoring on k_aq spends the unavoidable
    perturbation on the tight COV-0.10 grain size rather than on the
    heavy-tailed k_aq that co-drives the failure tail. The alternative
    Iman-Conover rank reordering preserves *all* marginals exactly by permuting
    within columns, but controls the rank (Spearman) rather than the log-space
    Pearson correlation the project calibrates against and departs from the
    spec §7 Nataf framing, so it is not used here.

    Parameters
    ----------
    marginals : sequence of MarginalSpec
        Exactly the seven canonical marginals, in any order; they are sorted
        into :data:`PARAM_NAMES` order internally. Taken as a direct argument
        because M1 ``config`` does not exist yet (it will later supply these).
    seed : int
        RNG seed for ``scipy.stats.qmc.LatinHypercube``. Deterministic: the
        same seed yields the bit-identical ``theta_matrix`` (spec §13;
        docs/conventions.md).
    rho_log_kaq_d70 : float
        Target correlation ``rho(ln k_aq, ln d_70)`` in log space, in the open
        interval (-1, 1). Because both marginals are lognormal this equals the
        Gaussian-copula correlation directly (see the module docstring). Used
        only when ``coupling='correlated'``; supplied (and recorded) but not
        imposed when ``coupling='two_population'``.
    d70_interpretation : {'matrix', 'bulk'}
        Which grain-size definition the supplied ``d_70`` marginal represents
        (spec §7, §13). Recorded in ``metadata['d70_interpretation']`` for the
        §8 stratified decomposition; does not alter the sampling math.
    n_samples : int, optional
        Number of realizations N. Default ``100_000`` per spec §13
        (N = 1e5 per cross-section); tests pass a smaller N.
    coupling : {'correlated', 'two_population'}, optional
        ``'correlated'`` (default) imposes ``rho_log_kaq_d70`` via the
        Gaussian copula with k_aq as the stratification anchor.
        ``'two_population'`` is the decoupled fallback (spec §7, §13): k_aq and
        d_70 are sampled independently and both retain full LHS stratification.
    bounds : mapping of str to (float, float), optional
        Optional per-parameter ``(low, high)`` physical clip applied after the
        copula map — the spec §12 failure-mode-2 guard against pathological
        H_c tails (e.g. ``{'d_70': (50e-6, 1e-3)}``). Default None (no clip).
        Clipping mildly truncates the extreme marginal tails; it is a safety
        bound, not a primary distributional control.

    Returns
    -------
    ThetaSample
        ``theta_matrix`` ``(N, 7)`` ``float64`` in canonical order, a copy of
        :data:`PARAM_NAMES`, and the documented ``metadata``.

    Raises
    ------
    ValueError
        If ``marginals`` is not exactly the seven canonical names (missing,
        extra or duplicated); if ``coupling='correlated'`` and
        ``rho_log_kaq_d70`` is not in (-1, 1); if ``d70_interpretation`` is not
        'matrix' or 'bulk'; if ``coupling`` is unknown; or if ``n_samples`` is
        not a positive integer.

    Notes
    -----
    Mathematical assumptions and guarantees the implementation must honor:

    * **Marginals preserved.** Each column's empirical mean and COV recover the
      specified ``MarginalSpec`` (lognormal via ``sigma_ln**2 = ln(1+cov**2)``,
      ``mu_ln = ln(mean) - sigma_ln**2/2``; normal via ``sigma = mean*cov``),
      independent of ``coupling``.
    * **Correlation recovered.** In ``'correlated'`` mode the empirical
      log-space correlation of (k_aq, d_70) recovers ``rho_log_kaq_d70`` within
      sampling tolerance; in ``'two_population'`` mode it is ~0.
    * **Stratification.** k_aq and the five independent variables retain perfect
      one-point-per-stratum LHS coverage in both modes; d_70 retains it only in
      ``'two_population'`` mode (in ``'correlated'`` mode it is the perturbed,
      approximately uniform column — see the module docstring).
    * **No C_e in the static branch.** C_e is sampled here (ADR-0001) but enters
      only the transient limit state downstream; the sampler is agnostic to
      that and draws all seven marginals uniformly.
    """
    # --- Validate inputs (fail fast before the expensive draw) ----------
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

    if bounds:
        unknown = [name for name in bounds if name not in PARAM_NAMES]
        if unknown:
            raise ValueError(
                f"bounds keys {unknown} are not parameters; expected names from "
                f"{PARAM_NAMES}."
            )

    n_dim = len(PARAM_NAMES)

    # --- 1. Stratified LHS design on the unit hypercube (scipy QMC). One
    # point per stratum per dimension; the integer seed makes the design fully
    # reproducible (spec §10, §13). seed= is used (not rng=) for compatibility
    # across the pinned scipy >= 1.11 range.
    design = LatinHypercube(d=n_dim, seed=seed).random(n_samples)

    # --- 2. Map to independent, stratified standard normals.
    z = norm.ppf(design)

    # --- 3. Impose the k_aq-d_70 correlation (Gaussian copula, k_aq anchor).
    # k_aq keeps its stratified column; d_70 becomes a standard normal
    # correlated with k_aq at exactly rho (see the Method note). Skipped in the
    # decoupled two-population mode.
    if coupling == "correlated":
        i_kaq = PARAM_NAMES.index("k_aq")
        i_d70 = PARAM_NAMES.index("d_70")
        rho = float(rho_log_kaq_d70)
        z[:, i_d70] = rho * z[:, i_kaq] + np.sqrt(1.0 - rho**2) * z[:, i_d70]

    # --- 4. Map each standard-normal column to its physical marginal.
    # Lognormal moment-matching from the physical (mean, COV):
    #   sigma_ln**2 = ln(1 + COV**2),  mu_ln = ln(mean) - sigma_ln**2 / 2
    # reproduces the physical mean and COV exactly (the mean is NOT exp(mu_ln)).
    theta = np.empty((n_samples, n_dim), dtype=np.float64)
    for j, name in enumerate(PARAM_NAMES):
        spec = spec_by_name[name]
        if spec.family == "lognormal":
            sigma_ln = np.sqrt(np.log(1.0 + spec.cov**2))
            mu_ln = np.log(spec.mean) - 0.5 * sigma_ln**2
            theta[:, j] = np.exp(mu_ln + sigma_ln * z[:, j])
        else:  # normal: sigma = mean * COV
            theta[:, j] = spec.mean + spec.mean * spec.cov * z[:, j]

    # --- 5. Clip to physically defensible bounds; log the clipped fraction.
    # The spec §12 failure-mode-2 guard against pathological H_c tails. Applied
    # after the copula map, so it mildly truncates the extreme marginal tails.
    clipped_fraction: dict[str, float] = {}
    if bounds:
        for name, (low, high) in bounds.items():
            j = PARAM_NAMES.index(name)
            col = theta[:, j]
            n_out = int(np.count_nonzero((col < low) | (col > high)))
            frac = n_out / n_samples
            clipped_fraction[name] = frac
            theta[:, j] = np.clip(col, low, high)
            logger.info(
                "Bounds clip: %.4f%% (%d/%d) of %s samples clipped to [%g, %g] "
                "(spec §12 failure mode 2).",
                100.0 * frac,
                n_out,
                n_samples,
                name,
                low,
                high,
            )

    # --- 6. Assemble the named result with provenance metadata.
    metadata: dict[str, Any] = {
        "param_names": list(PARAM_NAMES),
        "n_samples": int(n_samples),
        "seed": int(seed),
        "sampling_scheme": "latin_hypercube",
        "coupling": coupling,
        "correlation_space": "log",
        "rho_log_kaq_d70": float(rho_log_kaq_d70),
        "rho_imposed": coupling == "correlated",
        "d70_interpretation": d70_interpretation,
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
    }
    return ThetaSample(
        theta_matrix=theta,
        param_names=list(PARAM_NAMES),
        metadata=metadata,
    )


def sample_seepage_length(
    mean_m: float,
    cov: float,
    *,
    seed: int,
    n_samples: int = 100_000,
) -> NDArray[np.float64]:
    """Draw the ``(N,)`` stochastic seepage length L, independent of theta.

    The thesis carries the seepage length L as a per-cross-section stochastic
    geometric parameter (lognormal), sampled **independently of the Nataf-
    coupled theta vector** rather than as the eighth column of
    :func:`sample_theta`. This keeps L out of the k_aq-d_70 copula entirely (it
    is geometric, not a soil property) while still propagating its uncertainty
    into H_c (linear in L), l_c, r_e, the H_eq curve and Z_transient = L - l_e.

    A standalone 1-D Latin Hypercube design is used so L keeps the same one-
    point-per-stratum marginal coverage as the theta columns; the ``seed`` is
    derived by the caller from the run seed so the draw is reproducible and
    independent of the theta LHS (``run.py`` derives it via ``SeedSequence``).

    Parameters
    ----------
    mean_m : float
        Arithmetic mean seepage length [m] (the per-section ``geometry.L``).
        Must be > 0.
    cov : float
        Coefficient of variation (std / mean) [-], a fraction. Must be > 0
        (use the deterministic path, not this function, for a fixed L).
    seed : int
        RNG seed for the 1-D LHS. Deterministic: the same seed yields the
        bit-identical draw.
    n_samples : int, optional
        Number of realizations N. Default ``100_000`` (spec §13); must match
        the theta-matrix row count so L_j pairs with theta_j row-for-row.

    Returns
    -------
    numpy.ndarray, shape (N,)
        Stratified lognormal seepage-length draws [m], in physical units. The
        empirical mean and COV recover ``mean_m`` and ``cov`` within sampling
        tolerance via the same moment-matching as the theta marginals
        (``sigma_ln**2 = ln(1+cov**2)``, ``mu_ln = ln(mean) - sigma_ln**2/2``).

    Raises
    ------
    ValueError
        If ``mean_m <= 0``, ``cov <= 0`` or ``n_samples < 1``.
    """
    if not mean_m > 0.0:
        raise ValueError(f"mean_m must be > 0, got {mean_m!r}.")
    if not cov > 0.0:
        raise ValueError(
            f"cov must be > 0 for a stochastic seepage length, got {cov!r}; "
            "use the deterministic geometry.L path for a fixed L."
        )
    if n_samples < 1:
        raise ValueError(f"n_samples must be a positive integer, got {n_samples}.")

    design = LatinHypercube(d=1, seed=seed).random(n_samples)[:, 0]
    z = norm.ppf(design)
    sigma_ln = np.sqrt(np.log(1.0 + cov**2))
    mu_ln = np.log(mean_m) - 0.5 * sigma_ln**2
    return np.exp(mu_ln + sigma_ln * z)
