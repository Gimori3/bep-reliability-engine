"""GSA quantity-of-interest adapter: M8's batch physics with continuous outputs.

The production batch evaluator ``evaluator.evaluate_batch`` deliberately
returns only the two boolean failure columns (spec §12 fm6: the bulk sweep
keeps neither diagnostics nor trajectories). The Stage 6.5 GSA (ADR-0033)
additionally needs the **continuous** per-realization outputs behind those
flags — the static margin and the final pipe-length fraction — because two of
its four QoIs are continuous (ADR-0033 §1). This adapter is the thin,
clearly-bounded answer: the *same* shared preamble, the *same* two branches
through the *same* public M4/M6/M7 kernels, in the same order, returning the
continuous quantities alongside the flags.

It deliberately does **not** modify M8: ``evaluate_batch``'s signature and
return contract are untouched, and this adapter is pinned to it by a
bit-identity drift guard (``tests/test_gsa_qoi.py``: the flags derived here
must equal ``evaluate_batch``'s exactly on the numpy backend). The
shared-sample contract (ADR-0002) is preserved — one theta row feeds both
branches within one call — as are the ADR-0027/0028 head conventions (raw
gross static head, raw crack-reduced erosion head, r_e only in the gate).

This module exists for GSA drivers; the production sweep and the Phase 2
replay continue to use M8 directly.

References
----------
ADR-0033 (the GSA design; §1 QoIs, §5 drift guard); evaluator.evaluate_batch
(the mirrored contract); spec §3 (execution sequence), §4 (shared preamble
then branch).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from bep_reliability_engine.hydraulics import (
    InstantaneousHead,
    leakage_length_in,
    leakage_length_out,
    response_factor,
)
from bep_reliability_engine.progression import integrate_progression
from bep_reliability_engine.sellmeijer import compute_critical_head_vectorized

__all__ = ["QoiBatch", "evaluate_qoi_batch"]


@dataclass(frozen=True)
class QoiBatch:
    """Per-realization GSA outputs for one conditioning level (ADR-0033 §1).

    Attributes
    ----------
    z_static_m : numpy.ndarray, shape (N,)
        Static margin ``H_c - (h_peak - z_toe)`` [m] on the raw gross head
        (ADR-0028) — QoI Y4. ``failure_static = z_static_m <= 0``.
    l_e_final_m : numpy.ndarray, shape (N,)
        Final pipe length after the full hydrograph [m] (clipped at L).
    l_fraction : numpy.ndarray, shape (N,)
        ``l_e_final / L`` in [0, 1] — QoI Y3 (per-realization L when L is
        stochastic).
    failure_static : numpy.ndarray, shape (N,), bool
        ``Z_static <= 0`` — QoI Y2 as a float cast.
    failure_trans : numpy.ndarray, shape (N,), bool
        ``(L - l_e_final) <= 0`` — QoI Y1 as a float cast.
    h_c_m : numpy.ndarray, shape (N,)
        The static critical head [m] (diagnostic; Y4 minus a level constant).
    """

    z_static_m: npt.NDArray[np.float64]
    l_e_final_m: npt.NDArray[np.float64]
    l_fraction: npt.NDArray[np.float64]
    failure_static: npt.NDArray[np.bool_]
    failure_trans: npt.NDArray[np.bool_]
    h_c_m: npt.NDArray[np.float64]


def evaluate_qoi_batch(
    theta_matrix: npt.NDArray[np.float64],
    hydrograph,
    geometry: dict,
    *,
    l_ini: float = 0.0,
    seepage_length_samples: npt.NDArray[np.float64] | None = None,
    alpha_exponent: float | None = None,
    alpha_exponent_transient: float | None = None,
    theta_repose_rad: float | None = None,
    relative_density: float | None = None,
    gamma_p_sub_kn_m3: float | None = None,
    foreland_open: bool = False,
    progression_backend: str = "numpy",
) -> QoiBatch:
    """Evaluate both limit states for all N rows, keeping continuous outputs.

    Same parameters and semantics as
    :func:`~bep_reliability_engine.evaluator.evaluate_batch` (M8's vectorized
    production path), which this function mirrors kernel for kernel; see its
    docstring for the full contract. The only difference is the return type:
    the continuous margins behind the failure flags are retained for the GSA
    QoIs (ADR-0033 §1). The derived flags are bit-identical to
    ``evaluate_batch`` on the numpy backend (drift-guarded by
    ``tests/test_gsa_qoi.py``).

    Returns
    -------
    QoiBatch
        Continuous margins, the erosion fraction, and the two failure flags.

    Raises
    ------
    ValueError
        If ``progression_backend`` is not ``'numpy'`` or ``'numba'``.
    RuntimeError
        If ``progression_backend='numba'`` and numba is not installed.
    """
    if progression_backend not in ("numpy", "numba"):
        raise ValueError(
            f"progression_backend {progression_backend!r} must be 'numpy' or "
            "'numba' (ADR-0029)."
        )
    theta = np.asarray(theta_matrix, dtype=np.float64)

    k_aq_mps = theta[:, 0]
    d_aq_m = theta[:, 2]
    d_bl_m = theta[:, 3]
    k_bl_mps = theta[:, 4]
    gamma_bl_sub_knpm3 = theta[:, 5]
    c_e = theta[:, 6]

    z_toe_m = float(geometry["z_toe"])

    if seepage_length_samples is None:
        seepage_length: float | npt.NDArray[np.float64] = float(geometry["L"])
        geometry_for_hc = geometry
    else:
        seepage_length = np.asarray(seepage_length_samples, dtype=np.float64)
        geometry_for_hc = {**geometry, "L": seepage_length}

    sell_kwargs: dict[str, float] = {}
    if alpha_exponent is not None:
        sell_kwargs["alpha_exponent"] = alpha_exponent
    if theta_repose_rad is not None:
        sell_kwargs["theta_repose_rad"] = theta_repose_rad
    if relative_density is not None:
        sell_kwargs["relative_density"] = relative_density
    if gamma_p_sub_kn_m3 is not None:
        sell_kwargs["gamma_p_sub_kn_m3"] = gamma_p_sub_kn_m3
    sellmeijer = compute_critical_head_vectorized(theta, geometry_for_hc, **sell_kwargs)
    h_c = np.asarray(sellmeijer.H_c, dtype=np.float64)
    l_c = np.asarray(sellmeijer.l_c, dtype=np.float64)

    if alpha_exponent_transient is None:
        h_c_transient = h_c
    else:
        h_c_transient = np.asarray(
            compute_critical_head_vectorized(
                theta,
                geometry_for_hc,
                **{**sell_kwargs, "alpha_exponent": alpha_exponent_transient},
            ).H_c,
            dtype=np.float64,
        )

    lambda_in = leakage_length_in(k_aq_mps, d_aq_m, d_bl_m, k_bl_mps)
    lambda_out_eff = leakage_length_out(
        k_aq_mps,
        d_aq_m,
        geometry["D_fore"],
        geometry["k_fore"],
        geometry["foreshore_width"],
    )
    if foreland_open:
        lambda_out_eff = np.zeros_like(lambda_out_eff)
    r_e = response_factor(lambda_in, lambda_out_eff, seepage_length)

    # Static branch: raw gross head (ADR-0028); the continuous margin is Y4.
    h_peak_m = float(hydrograph.peak)
    z_static = h_c - (h_peak_m - z_toe_m)
    failure_static = z_static <= 0.0

    # Transient branch: identical dispatch to evaluate_batch (ADR-0029).
    h_river_m = np.asarray(hydrograph.h, dtype=np.float64)
    dt_s = float(hydrograph.native_dt)
    if progression_backend == "numba":
        try:
            from bep_reliability_engine.progression_numba import (
                integrate_progression_numba,
            )
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError(
                "progression_backend='numba' requires the optional numba "
                "dependency; install it with `pip install -e .[accel]` or "
                "use the default 'numpy' backend."
            ) from exc
        progression = integrate_progression_numba(
            h_river_m,
            dt_s,
            r_e,
            z_toe_m,
            c_e=c_e,
            k_aq_mps=k_aq_mps,
            d_bl_m=d_bl_m,
            gamma_bl_sub_knpm3=gamma_bl_sub_knpm3,
            h_c_m=h_c_transient,
            l_c_m=l_c,
            seepage_length_m=seepage_length,
            l_ini_m=l_ini,
        )
    else:
        head_model = InstantaneousHead(r_e, z_toe_m)
        progression = integrate_progression(
            h_river_m,
            dt_s,
            head_model,
            z_toe_m,
            c_e=c_e,
            k_aq_mps=k_aq_mps,
            d_bl_m=d_bl_m,
            gamma_bl_sub_knpm3=gamma_bl_sub_knpm3,
            h_c_m=h_c_transient,
            l_c_m=l_c,
            seepage_length_m=seepage_length,
            l_ini_m=l_ini,
            store_trajectory=False,
        )
    l_e_final = np.asarray(progression.l_final_m, dtype=np.float64)
    failure_trans = (seepage_length - l_e_final) <= 0.0

    return QoiBatch(
        z_static_m=z_static,
        l_e_final_m=l_e_final,
        l_fraction=l_e_final / seepage_length,
        failure_static=np.asarray(failure_static, dtype=bool),
        failure_trans=np.asarray(failure_trans, dtype=bool),
        h_c_m=h_c,
    )
