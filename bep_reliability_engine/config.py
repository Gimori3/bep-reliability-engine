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
  ``Geometry.HWL`` (the 2019 design high-water level, ADR-0018) is
  config-carried but deliberately excluded from that frozen contract.
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

Threading status
----------------
``theta_repose_deg`` (via :attr:`theta_repose_rad`), ``relative_density_insitu``
and ``alpha_exponent`` are config-owned (ADR-0015) and are now **threaded
through M8** (``run.py`` passes them to ``evaluate_batch`` ->
``compute_critical_head``), so a run that overrides them is honored rather than
silently ignored. Their defaults still equal the M6 constants, so an
un-overridden run is baseline-neutral. ``alpha_exponent`` feeds the single shared
H_c (a *symmetric* knob: both branches shift together); the transient-only
``alpha_exponent_transient`` (ADR-0017) delivers the spec §12 fm4 dimensional-bias
decomposition by recomputing a separate transient H_c (None by default ->
single-source preserved). ``seepage_length_cov`` is consumed by ``run.py``
(stochastic L draw), and the conditioning grid drives the ``run.py`` sweep.
``target_dt_seconds`` is honored on both hydrograph paths: the synthetic stub
builds directly on that grid, and the canonical d4PDF path refines the built
record via ``hydrographs.resample_record`` (the ADR-0013 record-construction
hook, realized with ADR-0030 as an *integration-Δt* policy: linear
interpolation of the resolved hourly signal, integer subdivisions only; also
the mechanism for the ADR-0022 Phase 2 native/2 replay).

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
    "HydrographSource",
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
    """Cross-section geometry; carries the flat dict M8 unpacks (ADR-0010).

    Field names are the exact, case-sensitive keys M8
    ``evaluate_realization`` reads, plus ``HWL`` which is config-carried only:
    :meth:`as_evaluator_dict` emits the frozen five-key ADR-0010 dict and
    excludes ``HWL`` (ADR-0018). The built M4 kernels take unpacked scalars
    and never see this dict; M6 reads only ``L``.

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
    HWL : float
        Design high-water level [m MSL]; ``> 0``. Sourced from the official
        2019 design bank-height data
        (``data/raw/geometry/BankHeight_*Riv_2019.csv`` via
        ``bank_heights.load_hwl``, ADR-0018), on the same MSL datum as the M3
        stage hydrographs and as ``z_toe`` (the generated configs carry the
        ADR-0021 landside-toe elevations in m MSL, retiring the former
        PROVISIONAL 0.0). Excluded from :meth:`as_evaluator_dict`.
    """

    L: float = Field(gt=0.0, description="Seepage length [m], > 0.")
    z_toe: float = Field(description="Exit-point polder elevation [m above datum].")
    foreshore_width: float = Field(ge=0.0, description="Foreshore width B_f [m], >= 0.")
    D_fore: float = Field(gt=0.0, description="Foreshore blanket thickness [m], > 0.")
    k_fore: float = Field(gt=0.0, description="Foreshore blanket k [m/s], > 0.")
    HWL: float = Field(
        gt=0.0, description="Design high-water level [m MSL], > 0 (ADR-0018)."
    )

    def as_evaluator_dict(self) -> dict[str, float]:
        """Return the flat geometry dict M8 ``evaluate_realization`` consumes.

        Returns
        -------
        dict of str to float
            ``{'L', 'z_toe', 'foreshore_width', 'D_fore', 'k_fore'}`` in SI
            units — the exact keys the built evaluator unpacks (ADR-0010).
            ``HWL`` is excluded: the M8 contract is frozen and the evaluator
            has no HWL consumer (ADR-0018).
        """
        return self.model_dump(
            include={"L", "z_toe", "foreshore_width", "D_fore", "k_fore"}
        )


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
        above datum]; non-empty (spec §1, §13). Config is the single source;
        ``run.py`` sweeps it as the outer (parallel) loop.
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
    boundary; config owns only the resolution/convergence *policy*. The
    ``target_dt_seconds`` policy is applied at record construction on both
    paths: the synthetic stub builds directly on that grid, and the canonical
    (d4PDF) path refines the built record via ``hydrographs.resample_record``
    (ADR-0013 hook; ADR-0030 integration-Δt policy — integer subdivisions of
    the native grid only, so the loading signal is unchanged and only the
    forward-Euler grid is refined; also the ADR-0022 Phase 2 native/2 replay
    mechanism). Per ADR-0014 the aquifer-lag fields are metadata-only with
    a deferred consumer (the unbuilt §11 diagnostic); τ_aq is derived from S_s,
    never stored.

    Attributes
    ----------
    integration_scheme : {'forward_euler'}
        Fixed forward Euler (spec §10, §13); recorded for provenance.
    target_dt_seconds : float or None
        Optional integration Δt [s] applied when the record is built
        (ADR-0013/0030); ``> 0`` when set, and on the canonical path an
        integer subdivision of the native resolution. Default ``None``
        (integrate at native resolution).
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
    progression_backend : {'numpy', 'numba'}
        M7 batch-timestepper backend for the production sweep (ADR-0029).
        ``'numpy'`` (default) is the reference path, bit-identical to looping
        the scalar M8 evaluator. ``'numba'`` selects the JIT-parallel kernel:
        numerically equivalent to < 1e-10 but **not bit-identical** (platform
        ``pow`` may differ in the last ulp), which is why the choice lives in
        config — one config must fully determine one result — and is recorded
        in the persisted metadata. Requires the optional ``numba`` dependency
        (``pip install -e .[accel]``) and the instantaneous head model
        (refused when ``aquifer_lag_active`` is True).
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
    progression_backend: Literal["numpy", "numba"] = Field(
        default="numpy",
        description=(
            "M7 batch-timestepper backend (ADR-0029): 'numpy' (reference, "
            "bit-identical to the scalar loop) or 'numba' (JIT-parallel, "
            "< 1e-10 equivalence, requires the optional [accel] extra)."
        ),
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

    @model_validator(mode="after")
    def _numba_backend_requires_instantaneous_head(self) -> TimestepperSettings:
        """The numba kernel inlines the instantaneous M4 form only (ADR-0029).

        Refusing the combination at load time is the fail-fast alternative to
        silently dropping the lag: a lagged run must use the numpy backend
        until the exponential lag update is implemented in the kernel.
        """
        if self.aquifer_lag_active and self.progression_backend == "numba":
            raise ValueError(
                "progression_backend='numba' supports only the instantaneous "
                "head model; the aquifer-lag form is numpy-only (ADR-0029). "
                "Set progression_backend='numpy' or deactivate the lag."
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


class HydrographSource(_StrictModel):
    """Where the d4PDF hydrograph data lives + the canonical shape events.

    The ADR-0020 block that makes M3 reachable from a config: the data-drop
    root, the explicit river/KP (never parsed out of ``cross_section_id`` —
    ID strings are labels, not data), and the **ordered** canonical event
    list that pins the G1 conditioning-level shapes. The block is optional on
    :class:`Config` (``None`` default): a config without it can only run the
    synthetic-stub path, and the orchestrator refuses the real-hydrograph
    path without it.

    Derived, not stored here: the rating CSV path
    (:func:`~bep_reliability_engine.hydrographs.rating_curve_path`), the
    scenario -> experiment mapping
    (:func:`~bep_reliability_engine.hydrographs.experiment_for_scenario`),
    and the band workbook
    (:func:`~bep_reliability_engine.hydrographs.resolve_band_workbook`,
    which also applies the ADR-0019 §7 upper-Tokachi proxy routing).

    Attributes
    ----------
    data_root : str
        Root of the raw data drop; the loader expects ``hydrographs/`` and
        ``rating_curves/`` beneath it. Default ``'data/raw'``.
    river : {'Tokachi', 'Satsunai'}
        The study node's river (closed literal; feeds the rating filename
        convention and the band-file scan).
    kp : float
        The study node's KP, ``> 0``. Selects the rating coefficients and —
        after the §7 proxy routing — the band workbook.
    canonical_event_ids : tuple of str
        Verbatim d4PDF member headers (ADR-0019 §1 grammar, validated at
        load time) whose shapes drive the conditioning-level scaling
        (ADR-0020 Decision 1). **Ordered: the first entry is the shape the
        run uses**; subsequent entries are approved alternates recorded for
        provenance (a shape-sensitivity run is a config with the list
        reordered — selection stays config-side so one config still fully
        determines one result).
    """

    data_root: str = Field(
        default="data/raw", description="Root of the raw data drop (ADR-0020)."
    )
    river: Literal["Tokachi", "Satsunai"] = Field(
        description="Study node's river (explicit, never parsed from IDs)."
    )
    kp: float = Field(gt=0.0, description="Study node's KP, > 0.")
    canonical_event_ids: tuple[str, ...] = Field(
        min_length=1,
        description=(
            "Ordered d4PDF member headers pinning the G1 canonical shapes; "
            "the first entry is the shape the run uses (ADR-0020)."
        ),
    )

    @field_validator("canonical_event_ids")
    @classmethod
    def _ids_parse_as_member_headers(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject event IDs that are not valid d4PDF member headers.

        The load-time guard against a typo'd member ID surfacing hours into a
        run: every entry must satisfy the ADR-0019 §1 header grammar
        (``HPB_mXXX_YYYY`` / ``HFB_{SST}_mXXX_YYYY``).
        """
        # Imported here to keep M1 import-light and one-directional (M3 never
        # imports config, so no cycle either way; this just keeps the module
        # graph lazy).
        from bep_reliability_engine.hydrographs import parse_member_header

        for index, event_id in enumerate(value):
            try:
                parse_member_header(event_id)
            except ValueError as exc:
                raise ValueError(
                    f"canonical_event_ids[{index}] = {event_id!r} is not a "
                    f"d4PDF member header (ADR-0019 §1): {exc}"
                ) from exc
        return value


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
    hydrograph_source : HydrographSource or None
        d4PDF data location, explicit river/KP, and the ordered canonical
        shape events (ADR-0020). ``None`` (default) keeps pre-ADR-0020
        configs valid; the real-hydrograph path requires the block.
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
        Sellmeijer **static/baseline** scale exponent (ADR-0015, spec §12 fm4):
        ``-1/3`` (2D baseline) or ``-1/2`` (3D, symmetric — shifts both branches).
        Default ``-1/3``.
    alpha_exponent_transient : float or None
        **Transient-only** scale-exponent override for the dimensional-bias
        decomposition (ADR-0017). ``None`` (default) keeps the single-source H_c
        (the transient H_eq anchor is the same H_c as the static comparator,
        bit-identical to baseline). Set to ``-1/2`` to recompute the transient
        H_c at the 3D exponent while the static comparator retains
        ``alpha_exponent`` (``-1/3``), isolating the 2D-vs-3D dimensional bias
        from the temporal bias. Production configs leave this ``None``; it is set
        only for the dedicated sensitivity run.
    seepage_length_cov : float or None
        Coefficient of variation of the seepage length L. ``None`` (default)
        keeps L deterministic at ``geometry.L``; a positive value (``0 < CoV
        <= MAX_COV``) makes the engine draw L ~ Lognormal(mean ``geometry.L``,
        cov this) **independently of the Nataf-coupled theta vector**, per the
        thesis seepage-length prior. The mean L lives in ``geometry.L``; this
        field only adds its spread. Sampled once per run with a seed derived
        from ``mc.seed`` so the parallel sweep stays reproducible.
    foreland_treatment : {'blanketed_tanh', 'open_entry'}
        Foreland entry treatment (ADR-0025). ``'blanketed_tanh'`` (default,
        the adopted baseline): leaky foreland blanket with the ADR-0006
        finite-width tanh entry length. ``'open_entry'``: the USACE x1 = 0
        bound — the evidence-disfavored KP 62.0 sensitivity, runnable on
        demand with this one flag but never generated into the production
        sweep. Recorded in run metadata.
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

    # d4PDF hydrograph source (ADR-0020). Optional: None keeps every
    # pre-ADR-0020 config valid and restricts the run to the synthetic-stub
    # path; the orchestrator refuses the real-hydrograph path without it.
    hydrograph_source: HydrographSource | None = Field(
        default=None,
        description=(
            "d4PDF data location, river/KP, and the ordered canonical shape "
            "events (ADR-0020). None = synthetic-stub path only."
        ),
    )

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
    alpha_exponent_transient: float | None = Field(
        default=None,
        description=(
            "Transient-only scale-exponent override (ADR-0017). None = "
            "single-source H_c (baseline); set to -1/2 for the dimensional-bias "
            "decomposition (static keeps alpha_exponent, transient uses this)."
        ),
    )
    seepage_length_cov: float | None = Field(
        default=None,
        gt=0.0,
        le=MAX_COV,
        description=(
            "CoV of the per-section stochastic seepage length L. None = L "
            "deterministic at geometry.L; a positive value samples L ~ "
            "Lognormal(mean=geometry.L, cov=this) independently of theta."
        ),
    )
    foreland_treatment: Literal["blanketed_tanh", "open_entry"] = Field(
        default="blanketed_tanh",
        description=(
            "Foreland entry treatment (ADR-0025). 'blanketed_tanh' (baseline): "
            "leaky foreland blanket with the ADR-0006 finite-width tanh entry "
            "length. 'open_entry': the USACE x1 = 0 bound (river head applied "
            "directly at the riverside toe) — the evidence-disfavored "
            "sensitivity for the KP 62.0 foreland-confinement question, run "
            "on demand only, never a production-sweep member."
        ),
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
