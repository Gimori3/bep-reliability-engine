"""M1 ``config``: pydantic-validated deterministic inputs for one run.

Single responsibility (spec §1, M1): hold *all* deterministic inputs that a
single run legitimately sets, validate them at load time so unit errors are
caught before a multi-hour run, and expose the exact handoff shapes the built
downstream modules consume. One :class:`Config` fully determines one
reproducible fragility-curve pair; it carries no logic beyond validation and
serialization.

Scope of "all deterministic inputs" (ADR-0015)
----------------------------------------------
A quantity lives in config if it is a *run-varying scientific input* (geometry,
the seven prior specs, θ_repose, the in-situ D_r, the α-selector, S_s, prior
bounds, the conditioning grid, run identity); the *calibrated-model constants*
(Sellmeijer experimental means, White's drag, the regression and Pol
coefficients) stay in ``sellmeijer.py``/``progression.py``/``constants.py`` and
are deliberately **not** exposed here. C_u and KAS are pinned to their
experimental means and therefore also stay as module constants (ADR-0015).

Handoff shapes (verified against the built modules)
---------------------------------------------------
* :meth:`Geometry.as_evaluator_dict` returns exactly the flat dict M8
  ``evaluate_realization`` unpacks — ``{L, z_toe, foreshore_width, D_fore,
  k_fore}`` (ADR-0010). M4 takes unpacked scalars; only M8 sees the dict.
* :meth:`PriorSpecs.to_marginal_specs` returns the seven
  :class:`~bep_reliability_engine.sampling.MarginalSpec` in the canonical
  :data:`~bep_reliability_engine.sampling.PARAM_NAMES` order M2 requires;
  :class:`PriorSpecs` also owns the §12-fm2 ``bounds`` and the
  ``d70_interpretation`` label (a pure metadata tag on the d_70 marginal).
* :class:`CorrelationSpecs` carries the single scalar log-space target and the
  two-population switch M2 ``sample_theta`` consumes (not a 7×7 matrix).
* The aquifer-lag fields are **metadata-only with a deferred consumer** in
  Phase 1: M8 hard-wires the instantaneous head, and the §11 diagnostic that
  would read ``specific_storage_per_m`` is unbuilt (ADR-0014). τ_aq is *derived*
  from S_s downstream, never stored here.

Deferred threading note
-----------------------
``theta_repose_deg``, ``relative_density_insitu`` and ``alpha_exponent`` are
config-owned (ADR-0015) but reach M6 only once the geometry/run-settings dict
channel is threaded through M8 (ADR-0014); their Phase 1 defaults equal the
present M6 constants, so they are baseline-neutral until a run overrides them.
Likewise the conditioning grid and ``target_dt_seconds`` await the unbuilt
orchestrator/M3 (ADR-0013); config is the single source, with no live consumer
in the engine yet.

Units and reproducibility (docs/conventions.md)
-----------------------------------------------
Values are stored in strict SI / kN-m^3, except ``theta_repose_deg`` which is
stored in degrees and converted to radians at this boundary
(:attr:`Config.theta_repose_rad`) — the one place unit conversion is permitted
(spec §1). ``seed`` fully determines the sample matrix.

References
----------
Spec §1 (M1), §2/§8 (handoff and metadata), §7 (the seven marginals and the
mandatory coupling), §11 (S_s / aquifer-response diagnostic), §12 (failure-mode
2 prior bounds; failure-mode 4 α hook), §13 (single decisions). ADR-0010
(geometry/hydrograph schemas), ADR-0013 (Δt ownership), ADR-0014 (aquifer-lag
threading), ADR-0015 (deterministic-input scope and the D_r split).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from bep_reliability_engine.sampling import (
    PARAM_NAMES,
    CouplingMode,
    D70Interpretation,
    MarginalFamily,
    MarginalSpec,
)

__all__ = [
    "MAX_COV",
    "CANONICAL_FAMILY",
    "Geometry",
    "PriorSpec",
    "PriorSpecs",
    "CorrelationSpecs",
    "MCSettings",
    "TimestepperSettings",
    "OutputSettings",
    "Config",
]

# Upper bound on a coefficient of variation. A COV is a fraction (std / mean);
# values above this are almost certainly a percentage entered for a fraction
# (the spec §1 "50 versus 0.50" unit error). 2.0 (= 200%) leaves ample headroom
# for heavy-tailed priors while rejecting the unit slip decisively.
MAX_COV: float = 2.0

# Canonical marginal family per parameter: all seven variables are Lognormal.
# gamma_bl_sub (the submerged blanket weight) is Lognormal per ADR-0016 and the
# thesis blanket prior -- a deliberate deviation from the Normal of spec §7,
# adopted together with the gamma'_s -> {gamma'_bl, gamma'_p} split. Families are
# fixed here, so config validates them rather than treating them as free choices.
CANONICAL_FAMILY: dict[str, MarginalFamily] = {
    "k_aq": "lognormal",
    "d_70": "lognormal",
    "D_aq": "lognormal",
    "D_bl": "lognormal",
    "k_bl": "lognormal",
    "gamma_bl_sub": "lognormal",
    "C_e": "lognormal",
}


class _StrictModel(BaseModel):
    """Base for every config model: immutable and typo-rejecting.

    ``frozen=True`` makes a loaded config immutable (one config = one
    reproducible run, spec §1) and hashable; ``extra='forbid'`` turns an
    unknown or misspelled YAML key into a load-time error rather than a
    silently ignored field — the first line of defense against malformed
    configs.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class Geometry(_StrictModel):
    """Cross-section geometry; the flat dict M8 unpacks (ADR-0010).

    Field names are the exact, case-sensitive keys M8
    ``evaluate_realization`` reads, so :meth:`as_evaluator_dict` is a direct
    ``model_dump``. The built M4 kernels take unpacked scalars and never see
    this dict; M6 reads only ``L``.

    Attributes
    ----------
    L : float
        Seepage length across the structure [m]; strictly positive (the spec
        §1 positive-seepage-length requirement).
    z_toe : float
        Polder surface elevation at the landside exit point [m above datum];
        ≡ h_e in Pol SIE 2024 Eqs. (6) and (8) (ADR-0007). May be any finite
        value (an elevation, not a magnitude).
    foreshore_width : float
        Foreshore width B_f [m] (ADR-0006); ``>= 0``. ``0`` is the
        no-foreshore treatment; the semi-infinite limit is a modeling choice
        made downstream, not a config value.
    D_fore : float
        Deterministic foreshore blanket thickness [m] (ADR-0005); ``> 0``.
    k_fore : float
        Deterministic foreshore blanket vertical conductivity [m/s]
        (ADR-0005); ``> 0``.
    """

    L: float = Field(gt=0.0, description="Seepage length [m], > 0.")
    z_toe: float = Field(description="Exit-point polder elevation [m above datum].")
    foreshore_width: float = Field(ge=0.0, description="Foreshore width B_f [m], >= 0.")
    D_fore: float = Field(gt=0.0, description="Foreshore blanket thickness [m], > 0.")
    k_fore: float = Field(gt=0.0, description="Foreshore blanket k [m/s], > 0.")

    def as_evaluator_dict(self) -> dict[str, float]:
        """Return the flat geometry dict M8 ``evaluate_realization`` consumes.

        Returns
        -------
        dict of str to float
            ``{'L', 'z_toe', 'foreshore_width', 'D_fore', 'k_fore'}`` in SI
            units — the exact keys the built evaluator unpacks (ADR-0010).
        """
        return self.model_dump()


class PriorSpec(_StrictModel):
    """One marginal distribution specification (spec §7).

    Mirrors :class:`~bep_reliability_engine.sampling.MarginalSpec` as a
    pydantic model (the parameter name comes from the owning
    :class:`PriorSpecs` field, so it is not repeated here). The COV bound is
    the spec §1 unit-error guard.

    Attributes
    ----------
    family : {'lognormal', 'normal'}
        Marginal family. Validated against :data:`CANONICAL_FAMILY` by the
        owning :class:`PriorSpecs` (families are fixed by spec §7).
    mean : float
        Marginal mean in physical units. Must be ``> 0`` for a lognormal.
    cov : float
        Coefficient of variation (std / mean), a fraction in
        ``[0, MAX_COV]``. A value above :data:`MAX_COV` is rejected as a
        suspected percentage-for-fraction unit error (spec §1).
    """

    family: MarginalFamily = Field(description="'lognormal' or 'normal' (spec §7).")
    mean: float = Field(description="Marginal mean [physical units].")
    cov: float = Field(description="Coefficient of variation [-], a fraction.")

    @field_validator("cov")
    @classmethod
    def _cov_is_a_fraction(cls, value: float) -> float:
        """Reject negative COVs and percentage-for-fraction unit errors."""
        if value < 0.0:
            raise ValueError(f"cov must be non-negative, got {value!r}.")
        if value > MAX_COV:
            raise ValueError(
                f"cov={value!r} exceeds the sane maximum {MAX_COV}; this looks "
                "like a percentage (e.g. 50) supplied for a fraction (e.g. 0.50) "
                "— check units (spec §1 validation)."
            )
        return value

    @model_validator(mode="after")
    def _lognormal_needs_positive_mean(self) -> PriorSpec:
        """A lognormal marginal is undefined for a non-positive mean."""
        if self.family == "lognormal" and not self.mean > 0.0:
            raise ValueError(
                f"lognormal marginal requires mean > 0, got {self.mean!r}."
            )
        return self


class PriorSpecs(_StrictModel):
    """The seven prior marginals plus the optional failure-mode-2 clip.

    Field names are exactly the canonical
    :data:`~bep_reliability_engine.sampling.PARAM_NAMES`, so
    :meth:`to_marginal_specs` emits them in the order M2 requires. Families
    are validated against :data:`CANONICAL_FAMILY` (spec §7).

    Attributes
    ----------
    k_aq, d_70, D_aq, D_bl, k_bl, gamma_bl_sub, C_e : PriorSpec
        The seven marginals in canonical order. All seven Lognormal;
        gamma_bl_sub is Lognormal per ADR-0016 / the thesis blanket prior
        (deviating from the Normal of spec §7).
    bounds : dict of str to tuple of (float, float), optional
        Per-parameter physical clip ``(low, high)`` applied at the sampler
        stage (spec §12 failure mode 2; e.g. ``{'d_70': (50e-6, 1e-3)}``).
        Keys must be parameter names and ``low < high``. Default ``None``.
    d70_interpretation : {'matrix', 'bulk'}
        Which grain-size definition the ``d_70`` marginal (its mean and any
        bounds) represents — the *matrix* sand grain size or the *bulk* gravel
        framework (spec §7, §13). In M2 this is a **pure metadata label**: it
        does not alter the sampling math and does not drive the coupling, so the
        config author is responsible for supplying a ``d_70`` marginal
        consistent with it. It lives here, adjacent to that marginal, rather
        than in :class:`CorrelationSpecs`. Default ``'matrix'``.
    """

    k_aq: PriorSpec
    d_70: PriorSpec
    D_aq: PriorSpec
    D_bl: PriorSpec
    k_bl: PriorSpec
    gamma_bl_sub: PriorSpec
    C_e: PriorSpec
    bounds: dict[str, tuple[float, float]] | None = Field(
        default=None, description="Optional per-parameter (low, high) clip (§12 fm2)."
    )
    d70_interpretation: D70Interpretation = Field(
        default="matrix",
        description="Pure metadata label on the d_70 marginal: 'matrix' or 'bulk'.",
    )

    @model_validator(mode="after")
    def _validate_families_and_bounds(self) -> PriorSpecs:
        """Enforce the spec §7 families and well-formed bounds keys/order."""
        for name, family in CANONICAL_FAMILY.items():
            spec: PriorSpec = getattr(self, name)
            if spec.family != family:
                raise ValueError(
                    f"prior {name!r} must be {family!r} per spec §7, got "
                    f"{spec.family!r}."
                )
        if self.bounds is not None:
            unknown = [k for k in self.bounds if k not in PARAM_NAMES]
            if unknown:
                raise ValueError(
                    f"bounds keys {unknown} are not parameters; expected names "
                    f"from {PARAM_NAMES}."
                )
            for key, (low, high) in self.bounds.items():
                if not low < high:
                    raise ValueError(
                        f"bounds[{key!r}] requires low < high, got {(low, high)!r}."
                    )
        return self

    def to_marginal_specs(self) -> list[MarginalSpec]:
        """Return the seven :class:`MarginalSpec` in canonical M2 order.

        Returns
        -------
        list of MarginalSpec
            One per parameter, ordered by
            :data:`~bep_reliability_engine.sampling.PARAM_NAMES`, ready to pass
            straight to ``sample_theta``.
        """
        return [
            MarginalSpec(
                name=name,
                family=getattr(self, name).family,
                mean=getattr(self, name).mean,
                cov=getattr(self, name).cov,
            )
            for name in PARAM_NAMES
        ]


class CorrelationSpecs(_StrictModel):
    """The mandatory k_aq–d_70 coupling controls M2 consumes (spec §7).

    A single scalar log-space target plus the two-population switch — not a
    7×7 matrix. For the lognormal–lognormal pair the log-space target *is* the
    Gaussian-copula correlation directly (no Nataf root-find).

    ``d70_interpretation`` is deliberately *not* here: it is a pure metadata
    label on the d_70 marginal (in M2 it drives neither the coupling nor the
    marginal), so it lives in :class:`PriorSpecs` next to the d_70 spec it
    describes.

    Attributes
    ----------
    rho_log_kaq_d70 : float
        Target ``rho(ln k_aq, ln d_70)`` in the open interval ``(-1, 1)``.
        Supplied (and recorded) but not imposed when ``coupling`` is
        ``'two_population'``.
    coupling : {'correlated', 'two_population'}
        ``'correlated'`` imposes the coupling with k_aq as the stratification
        anchor; ``'two_population'`` is the decoupled fallback (spec §7, §13).
        Default ``'correlated'``.
    """

    rho_log_kaq_d70: float = Field(
        gt=-1.0, lt=1.0, description="Log-space target in the open interval (-1, 1)."
    )
    coupling: CouplingMode = Field(
        default="correlated", description="'correlated' or 'two_population'."
    )


class MCSettings(_StrictModel):
    """Monte Carlo and conditioning-grid settings (spec §1, §13).

    Attributes
    ----------
    n_samples : int
        Realizations N per cross-section; ``> 0``. Default ``100_000``
        (spec §13).
    seed : int
        RNG seed; ``>= 0``. Fully determines the sample matrix (spec §13).
    conditioning_grid : tuple of float
        The strictly ascending conditioning levels ``{h_1, ..., h_Nh}`` [m
        above datum]; non-empty (spec §1, §13). Consumed by the unbuilt outer
        loop; config is the single source.
    sampling_scheme : {'latin_hypercube'}
        Fixed at Latin Hypercube (spec §13); recorded for provenance.
    """

    n_samples: int = Field(default=100_000, gt=0, description="Realizations N, > 0.")
    seed: int = Field(ge=0, description="RNG seed, >= 0; determines the matrix.")
    conditioning_grid: tuple[float, ...] = Field(
        description="Strictly ascending conditioning levels [m above datum]."
    )
    sampling_scheme: Literal["latin_hypercube"] = Field(
        default="latin_hypercube", description="Fixed LHS (spec §13)."
    )

    @field_validator("conditioning_grid")
    @classmethod
    def _strictly_ascending(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        """Require a non-empty, strictly increasing conditioning grid.

        A single-element grid is intentionally accepted: one conditioning level
        is a valid (degenerate) run, and the strict-ascending check is then
        vacuously satisfied. Only emptiness and out-of-order multi-element grids
        are rejected.
        """
        if len(value) == 0:
            raise ValueError("conditioning_grid must be non-empty.")
        if any(b <= a for a, b in zip(value, value[1:])):
            raise ValueError(
                f"conditioning_grid must be strictly ascending, got {value!r}."
            )
        return value


class TimestepperSettings(_StrictModel):
    """Integration, convergence-policy and aquifer-lag settings.

    Per ADR-0013 the operative Δt is the hydrograph ``native_dt`` at the M8
    boundary; config owns only the resolution/convergence *policy* and an
    optional coarsening applied at M3 record construction (M3 unbuilt). Per
    ADR-0014 the aquifer-lag fields are metadata-only with a deferred consumer
    (the unbuilt §11 diagnostic); τ_aq is derived from S_s, never stored.

    Attributes
    ----------
    integration_scheme : {'forward_euler'}
        Fixed forward Euler (spec §10, §13); recorded for provenance.
    target_dt_seconds : float or None
        Optional target/coarsening Δt [s] applied when M3 builds the record
        (ADR-0013); ``> 0`` when set. Default ``None`` (use native resolution).
    convergence_test : bool
        Whether to run the §11 Δt/2 convergence test. Default ``False``.
    convergence_threshold : float
        Acceptance threshold for the Δt/2 test (fractional l_e change), in
        ``(0, 1)``. Default ``0.01`` (the spec §11 <1% target).
    aquifer_lag_active : bool
        Global lag flag (ADR-0004, ADR-0014). Phase 1 default ``False``
        (instantaneous). Metadata-only until the §11 diagnostic is built.
    specific_storage_per_m : float or None
        Specific storage S_s [1/m] for τ_aq (ADR-0004); ``> 0`` when set.
        Required when ``aquifer_lag_active`` is True. Default ``None``.
    """

    integration_scheme: Literal["forward_euler"] = Field(
        default="forward_euler", description="Fixed forward Euler (spec §10, §13)."
    )
    target_dt_seconds: float | None = Field(
        default=None, gt=0.0, description="Optional coarsening Δt [s] (ADR-0013)."
    )
    convergence_test: bool = Field(
        default=False, description="Run the §11 Δt/2 convergence test."
    )
    convergence_threshold: float = Field(
        default=0.01, gt=0.0, lt=1.0, description="Δt/2 acceptance threshold (§11)."
    )
    aquifer_lag_active: bool = Field(
        default=False, description="Global lag flag (ADR-0014); Phase 1 False."
    )
    specific_storage_per_m: float | None = Field(
        default=None, gt=0.0, description="S_s [1/m] for τ_aq (ADR-0004)."
    )

    @model_validator(mode="after")
    def _lag_requires_specific_storage(self) -> TimestepperSettings:
        """S_s is needed to derive τ_aq once the lag is active (ADR-0014)."""
        if self.aquifer_lag_active and self.specific_storage_per_m is None:
            raise ValueError(
                "specific_storage_per_m is required when aquifer_lag_active is "
                "True (ADR-0014; it is the input from which tau_aq is derived)."
            )
        return self


class OutputSettings(_StrictModel):
    """Output behavior: trajectory retention and persistence format.

    Attributes
    ----------
    store_trajectories : bool
        Retain the full l(t) trajectories; default ``False`` (~800 MB per
        cross-section at N = 1e5, spec §12 failure mode 6). Enable for the
        2016 calibration run and visualization subsets.
    persistence_format : {'hdf5'}
        Large-array persistence format (spec §2, §8); fixed at HDF5 with a
        JSON metadata sidecar. Recorded for provenance.
    results_dir : str
        Directory for result files. Default ``'results'``.
    """

    store_trajectories: bool = Field(
        default=False, description="Retain l(t); default off (§12 fm6)."
    )
    persistence_format: Literal["hdf5"] = Field(
        default="hdf5", description="HDF5 + JSON sidecar (spec §2, §8)."
    )
    results_dir: str = Field(default="results", description="Result output directory.")


class Config(_StrictModel):
    """Complete deterministic input set for one reproducible run (spec §1, M1).

    Composes the six nested settings models with the run-level deterministic
    Sellmeijer inputs (ADR-0015) and the run-identity provenance fields
    (spec §8). One :class:`Config` fully determines one fragility-curve pair.
    :meth:`from_yaml` loads and validates; :meth:`to_metadata` and
    :meth:`config_hash` give M9 a clean, JSON-serializable snapshot to embed in
    result metadata.

    Attributes
    ----------
    geometry : Geometry
        Cross-section geometry (the M8 flat dict, ADR-0010).
    priors : PriorSpecs
        The seven marginals plus optional §12-fm2 bounds.
    correlation : CorrelationSpecs
        The k_aq–d_70 coupling controls M2 consumes.
    mc : MCSettings
        Monte Carlo settings and the conditioning grid.
    timestepper : TimestepperSettings
        Integration/convergence policy and the aquifer-lag fields.
    output : OutputSettings
        Trajectory-storage and persistence settings.
    theta_repose_deg : float
        Bedding (repose) angle [degrees], ``0 < θ < 90`` (ADR-0015). Converted
        to radians at this boundary by :attr:`theta_repose_rad`. Default 37°.
    relative_density_insitu : float
        In-situ relative density D_r [-], ``0 < D_r <= 1``. This is the
        **run-varying numerator** of the Sellmeijer F_r ratio
        ``(D_r / D_r,m)^0.35`` and the *only* relative-density quantity config
        owns. The regression **normalization mean** ``D_r,m`` is a distinct,
        pinned model constant (``sellmeijer.D_R_MEAN``, alongside the pinned
        ``C_u``/``KAS`` means) that config never exposes and that is never
        run-varying — so the two roles cannot be conflated (ADR-0015 D_r split).
        Default 0.725; equal to ``D_r,m`` only by the coincidence of the Pol
        base case sitting at the Sellmeijer experimental mean.
    alpha_exponent : float
        Sellmeijer scale exponent selector (ADR-0015, spec §12 fm4): ``-1/3``
        (2D baseline) or ``-1/2`` (3D sensitivity). Default ``-1/3``.
    cross_section_id : str
        Cross-section identifier; provenance only (spec §8).
    segment_id : str
        200 m segment identifier; provenance only (spec §8, §12 tradeoff 3).
    scenario : {'historical', '+4K'}
        Climate scenario tag; provenance only (spec §2, §8). Default
        ``'historical'``.
    remediation_state : str
        Remediation state label for the §8 stratified decomposition;
        provenance only. Default ``'none'``.
    """

    geometry: Geometry
    priors: PriorSpecs
    correlation: CorrelationSpecs
    mc: MCSettings
    timestepper: TimestepperSettings
    output: OutputSettings

    # Deterministic Sellmeijer/model inputs (ADR-0015). Defaults equal the
    # present M6 constants, so they are baseline-neutral until threaded.
    theta_repose_deg: float = Field(
        default=37.0, gt=0.0, lt=90.0, description="Repose angle [deg] (ADR-0015)."
    )
    relative_density_insitu: float = Field(
        default=0.725,
        gt=0.0,
        le=1.0,
        description="In-situ D_r [-] (F_r numerator); D_r,m stays a module constant.",
    )
    alpha_exponent: float = Field(
        default=-1.0 / 3.0, description="Scale exponent: -1/3 (2D) or -1/2 (3D)."
    )

    # Run identity / provenance (spec §8 metadata attrs; no engine consumer).
    cross_section_id: str = Field(description="Cross-section identifier (provenance).")
    segment_id: str = Field(description="200 m segment identifier (provenance).")
    scenario: Literal["historical", "+4K"] = Field(
        default="historical", description="Climate scenario tag (provenance)."
    )
    remediation_state: str = Field(
        default="none", description="Remediation state label (provenance)."
    )

    @property
    def theta_repose_rad(self) -> float:
        """Repose angle in radians — the one config-boundary unit conversion.

        Returns
        -------
        float
            ``radians(theta_repose_deg)``, the form M6 consumes
            (docs/conventions.md: conversions only at the config boundary).
        """
        return math.radians(self.theta_repose_deg)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load and validate a config from a YAML file.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to a YAML document whose top level is a mapping of the
            :class:`Config` fields.

        Returns
        -------
        Config
            The validated config; unknown keys and out-of-range values raise
            ``pydantic.ValidationError`` (or ``ValueError`` for a non-mapping
            document) before any run begins.

        Raises
        ------
        ValueError
            If the YAML document does not parse to a mapping.
        pydantic.ValidationError
            If any field is missing, mistyped, or fails a validator.
        """
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(
                f"{path}: top-level YAML must be a mapping of Config fields, got "
                f"{type(data).__name__}."
            )
        return cls.model_validate(data)

    def to_yaml(self, path: str | Path) -> None:
        """Serialize the config to a YAML file (round-trips via :meth:`from_yaml`).

        Parameters
        ----------
        path : str or pathlib.Path
            Destination path. The document is the JSON-mode dump of
            :meth:`to_metadata`, so it reloads to an equal config.
        """
        with open(path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_metadata(), handle, sort_keys=False)

    def to_metadata(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot for M9 to embed in results.

        Returns
        -------
        dict
            ``model_dump(mode='json')``: nested dicts of primitives/lists only
            (tuples become lists, Literals become strings), suitable for the
            HDF5 JSON metadata sidecar (spec §2, §8). The derived
            ``theta_repose_rad`` is *not* included; consumers convert from
            ``theta_repose_deg`` as needed.
        """
        return self.model_dump(mode="json")

    def config_hash(self) -> str:
        """Return a stable SHA-256 over the canonical metadata snapshot.

        Returns
        -------
        str
            Hex digest of the key-sorted JSON of :meth:`to_metadata`; the
            ``config_hash`` provenance attr of spec §8. Two configs with
            identical inputs hash identically regardless of field ordering in
            the source YAML.
        """
        payload = json.dumps(self.to_metadata(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
