"""PosteriorResult: the Phase 2 artifact and its HDF5 + JSON persistence.

One ``PosteriorResult`` file per Phase 1 result file, i.e. per segment per
scenario per d70 interpretation (the Phase 1 stratification is one file per
stratum; spec section 8). Persistence follows the repository contract
exactly (HDF5 via h5py for arrays, JSON sidecar for metadata, no pickle):

HDF5 schema (schema_version 1)::

    /theta_matrix                  (N, 7)  float64   # the filtered prior rows
    /param_names                   (7,)    string
    /seepage_length_samples        (N,)    float64   # only when L stochastic
    /accept                        (N,)    bool      # operative chain mask
    /events/<event_id>/accept_trans      (N,) bool
    /events/<event_id>/accept_static     (N,) bool
    /events/<event_id>/initiation        (N,) bool
    /events/<event_id>/Z_static          (N,) float64
    /events/<event_id>/Z_transient       (N,) float64
    /events/<event_id>/l_e_final         (N,) float64
    /events/<event_id>/t_uh              (N,) float64
    /events/<event_id>/r_e               (N,) float64
    /events/<event_id>/t_breach          (N,) float64  # NaN = no breach;
                                                       # only when traced
    /fragility/conditioning_grid          (N_h,) float64
    /fragility/P_f_trans_post_raw         (N_h,) float64
    /fragility/P_f_static_post_raw        (N_h,) float64
    /fragility/P_f_trans_prior_raw        (N_h,) float64  # convenience copy
    /fragility/P_f_static_prior_raw       (N_h,) float64
    /fragility/binomial_ci/{trans,static}_{lo,hi}     (N_h,) float64
    /fragility/bootstrap_bands/{trans,static}_{lo,hi} (N_h,) float64
    /attrs: schema_version, fit_trans_post_{mu,sigma,datum_m},
            fit_static_post_{mu,sigma,datum_m}   # NaN encodes a None fit

The JSON sidecar carries the full provenance block: the Phase 1 source
(path, SHA-256 of the HDF5 and sidecar, config hash, code version, seeds,
stratifiers), the Phase 2 context (package version, criterion, replay
timestep, event chain with per-event decomposition and record provenance,
posterior counts and warnings, bootstrap settings) and the
prior-versus-posterior marginal summary. Event breach-time and diagnostic
arrays are per-event HDF5 groups; event ORDER lives in the sidecar's
``phase2.event_chain`` list (HDF5 group order is not meaningful).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from numpy.typing import NDArray

from bayesian_reliability_updating.fragility_update import PosteriorFragility
from bep_reliability_engine.fragility import LognormFragility

__all__ = ["EventArrays", "PosteriorResult"]

_SCHEMA_VERSION: int = 1


@dataclass(frozen=True)
class EventArrays:
    """One replayed event's per-row arrays (row j pairs with theta row j)."""

    accept_trans: NDArray[np.bool_]
    accept_static: NDArray[np.bool_]
    initiation: NDArray[np.bool_]
    Z_static: NDArray[np.float64]
    Z_transient: NDArray[np.float64]
    l_e_final: NDArray[np.float64]
    t_uh: NDArray[np.float64]
    r_e: NDArray[np.float64]
    t_breach: NDArray[np.float64] | None = None


@dataclass(frozen=True)
class PosteriorResult:
    """The Phase 2 handoff artifact: posterior sample, curves and provenance.

    Attributes
    ----------
    theta_matrix : numpy.ndarray, shape (N, 7)
        The FULL prior rows (posterior membership is ``accept``); retaining
        the full matrix keeps every mask interpretable and the file
        self-contained.
    param_names : list of str
        Canonical column names.
    seepage_length_samples : numpy.ndarray or None
        The per-row stochastic L actually used in the replay (regenerated
        from the Phase 1 config; persisted here so downstream consumers
        never re-derive the seed recipe).
    accept : numpy.ndarray, shape (N,), bool
        The operative acceptance mask after the whole event chain.
    events : dict of str to EventArrays
        Per-event replay arrays; order in ``metadata['phase2']
        ['event_chain']``.
    fragility : PosteriorFragility
        Posterior curves on the Phase 1 conditioning grid.
    P_f_trans_prior_raw, P_f_static_prior_raw : numpy.ndarray
        The Phase 1 raw prior curves (convenience copies for plotting).
    metadata : dict
        The JSON-sidecar provenance block.
    """

    theta_matrix: NDArray[np.float64]
    param_names: list[str]
    seepage_length_samples: NDArray[np.float64] | None
    accept: NDArray[np.bool_]
    events: dict[str, EventArrays]
    fragility: PosteriorFragility
    P_f_trans_prior_raw: NDArray[np.float64]
    P_f_static_prior_raw: NDArray[np.float64]
    metadata: dict[str, Any]

    @property
    def theta_posterior(self) -> NDArray[np.float64]:
        """The accepted rows (the posterior sample)."""
        return self.theta_matrix[self.accept, :]

    @property
    def n_accepted(self) -> int:
        """Posterior sample size."""
        return int(self.accept.sum())

    @staticmethod
    def _sidecar_path(path: Path) -> Path:
        return path.with_suffix(".json")

    def save(self, path: str | Path) -> None:
        """Persist to HDF5 plus a JSON metadata sidecar.

        Parameters
        ----------
        path : str or pathlib.Path
            Destination HDF5 path; the sidecar is written next to it with a
            ``.json`` suffix.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        string_dtype = h5py.string_dtype(encoding="utf-8")

        with h5py.File(path, "w") as handle:
            handle.attrs["schema_version"] = _SCHEMA_VERSION
            handle.create_dataset("theta_matrix", data=self.theta_matrix)
            handle.create_dataset(
                "param_names",
                data=np.array(self.param_names, dtype=object),
                dtype=string_dtype,
            )
            if self.seepage_length_samples is not None:
                handle.create_dataset(
                    "seepage_length_samples", data=self.seepage_length_samples
                )
            handle.create_dataset("accept", data=np.asarray(self.accept, dtype=bool))

            events_group = handle.create_group("events")
            for event_id, arrays in self.events.items():
                group = events_group.create_group(event_id)
                group.create_dataset(
                    "accept_trans", data=np.asarray(arrays.accept_trans, dtype=bool)
                )
                group.create_dataset(
                    "accept_static",
                    data=np.asarray(arrays.accept_static, dtype=bool),
                )
                group.create_dataset(
                    "initiation", data=np.asarray(arrays.initiation, dtype=bool)
                )
                group.create_dataset("Z_static", data=arrays.Z_static)
                group.create_dataset("Z_transient", data=arrays.Z_transient)
                group.create_dataset("l_e_final", data=arrays.l_e_final)
                group.create_dataset("t_uh", data=arrays.t_uh)
                group.create_dataset("r_e", data=arrays.r_e)
                if arrays.t_breach is not None:
                    group.create_dataset("t_breach", data=arrays.t_breach)

            frag = handle.create_group("fragility")
            frag.create_dataset(
                "conditioning_grid", data=self.fragility.conditioning_grid
            )
            frag.create_dataset(
                "P_f_trans_post_raw", data=self.fragility.P_f_trans_post_raw
            )
            frag.create_dataset(
                "P_f_static_post_raw", data=self.fragility.P_f_static_post_raw
            )
            frag.create_dataset("P_f_trans_prior_raw", data=self.P_f_trans_prior_raw)
            frag.create_dataset("P_f_static_prior_raw", data=self.P_f_static_prior_raw)
            cis = frag.create_group("binomial_ci")
            for key, tag in (("transient", "trans"), ("static", "static")):
                lo, hi = self.fragility.binomial_ci[key]
                cis.create_dataset(f"{tag}_lo", data=np.asarray(lo))
                cis.create_dataset(f"{tag}_hi", data=np.asarray(hi))
            bands = frag.create_group("bootstrap_bands")
            for key, tag in (("transient", "trans"), ("static", "static")):
                lo, hi = self.fragility.bootstrap_bands[key]
                bands.create_dataset(f"{tag}_lo", data=np.asarray(lo))
                bands.create_dataset(f"{tag}_hi", data=np.asarray(hi))

            def _fit_attrs(prefix: str, fit: LognormFragility | None) -> None:
                handle.attrs[f"{prefix}_mu"] = float(fit.mu) if fit else np.nan
                handle.attrs[f"{prefix}_sigma"] = float(fit.sigma) if fit else np.nan
                handle.attrs[f"{prefix}_datum_m"] = (
                    float(fit.datum_m) if fit else np.nan
                )

            _fit_attrs("fit_trans_post", self.fragility.P_f_trans_post_fit)
            _fit_attrs("fit_static_post", self.fragility.P_f_static_post_fit)

        with open(self._sidecar_path(path), "w", encoding="utf-8") as stream:
            json.dump(self.metadata, stream, indent=2, sort_keys=False)

    @classmethod
    def load(cls, path: str | Path) -> PosteriorResult:
        """Reconstruct a PosteriorResult from the HDF5 + JSON pair.

        Parameters
        ----------
        path : str or pathlib.Path
            The HDF5 path written by :meth:`save`.

        Returns
        -------
        PosteriorResult
            The reconstructed artifact; every array round-trips exactly.
        """
        path = Path(path)
        with h5py.File(path, "r") as handle:
            theta_matrix = handle["theta_matrix"][:]
            param_names = [str(n) for n in handle["param_names"].asstr()[:]]
            seepage = (
                handle["seepage_length_samples"][:]
                if "seepage_length_samples" in handle
                else None
            )
            accept = handle["accept"][:].astype(bool)

            events: dict[str, EventArrays] = {}
            for event_id, group in handle["events"].items():
                events[event_id] = EventArrays(
                    accept_trans=group["accept_trans"][:].astype(bool),
                    accept_static=group["accept_static"][:].astype(bool),
                    initiation=group["initiation"][:].astype(bool),
                    Z_static=group["Z_static"][:],
                    Z_transient=group["Z_transient"][:],
                    l_e_final=group["l_e_final"][:],
                    t_uh=group["t_uh"][:],
                    r_e=group["r_e"][:],
                    t_breach=(group["t_breach"][:] if "t_breach" in group else None),
                )

            frag = handle["fragility"]

            def _fit_or_none(prefix: str) -> LognormFragility | None:
                mu = float(handle.attrs[f"{prefix}_mu"])
                sigma = float(handle.attrs[f"{prefix}_sigma"])
                if np.isnan(mu) or np.isnan(sigma):
                    return None
                return LognormFragility(
                    mu=mu,
                    sigma=sigma,
                    datum_m=float(handle.attrs[f"{prefix}_datum_m"]),
                )

            with open(cls._sidecar_path(path), encoding="utf-8") as stream:
                metadata = json.load(stream)

            phase2_meta = metadata.get("phase2", {})
            fragility = PosteriorFragility(
                conditioning_grid=frag["conditioning_grid"][:],
                P_f_trans_post_raw=frag["P_f_trans_post_raw"][:],
                P_f_static_post_raw=frag["P_f_static_post_raw"][:],
                binomial_ci={
                    "transient": (
                        frag["binomial_ci/trans_lo"][:],
                        frag["binomial_ci/trans_hi"][:],
                    ),
                    "static": (
                        frag["binomial_ci/static_lo"][:],
                        frag["binomial_ci/static_hi"][:],
                    ),
                },
                bootstrap_bands={
                    "transient": (
                        frag["bootstrap_bands/trans_lo"][:],
                        frag["bootstrap_bands/trans_hi"][:],
                    ),
                    "static": (
                        frag["bootstrap_bands/static_lo"][:],
                        frag["bootstrap_bands/static_hi"][:],
                    ),
                },
                P_f_trans_post_fit=_fit_or_none("fit_trans_post"),
                P_f_static_post_fit=_fit_or_none("fit_static_post"),
                n_accepted=int(accept.sum()),
                settings=dict(phase2_meta.get("posterior_fragility", {})),
            )

            prior_trans = frag["P_f_trans_prior_raw"][:]
            prior_static = frag["P_f_static_prior_raw"][:]

        return cls(
            theta_matrix=theta_matrix,
            param_names=param_names,
            seepage_length_samples=seepage,
            accept=accept,
            events=events,
            fragility=fragility,
            P_f_trans_prior_raw=prior_trans,
            P_f_static_prior_raw=prior_static,
            metadata=metadata,
        )
