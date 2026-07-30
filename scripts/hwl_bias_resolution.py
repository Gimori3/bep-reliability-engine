"""Resolve the design-HWL static-vs-transient bias (companion to ADR-0040).

Pre-registration, criteria and outcome:
``docs/decisions/adr0040-hwl-bias-resolution.md``.
Evidence: ``docs/decisions/adr0040-hwl-bias-resolution.json``.

The 2026-07-29 production campaign left the headline Stage 6.6 bias unresolved at
exactly the level the thesis most wants to quote: at design HWL the transient
comparator rests on 4 failing rows out of 100 000 at KP 62.0 and **zero** at
KP 57.4 (campaign report section 6.1). The owner-chosen method (decision 6,
option C) is executed here:

* ``verify``    -- gate G-A1/G-A2: the N = 1e5 ladder still reproduces the
                   persisted production sweep bit-for-bit, all Euler flips zero.
* ``pilot``     -- N = 2e5 at KP 62.0, measured for wall time and peak RSS
                   (process tree, not just the parent), with the projection to
                   N = 1e6 that selects the Stage A scope.
* ``brute``     -- Stage A: brute-force N = 1e6 at KP 62.0 (ground truth).
* ``tilt``      -- Stage B: the ADR-0029 tilted importance sampler pointed at the
                   gap decomposition for the first time, validated against Stage A.
* ``kp57``      -- Stage C: the validated estimator where brute force cannot reach.
* ``epistemic`` -- Stage D: the epistemic band on the bias *ratio* at the resolved
                   anchor, ``m_p`` first as a negative control.
* ``report``    -- assemble the evidence JSON from the stage artifacts.

This module is physics-free in the ``convergence.py`` / ``sensitivity.py`` sense:
every failure indicator comes from the production machinery (M8 ``evaluate_batch``
directly, or the ADR-0040 comparator ladder which itself goes through M8).

Usage (repo root, venv active)::

    python scripts/hwl_bias_resolution.py verify --sections kp62_0 kp57_4
    python scripts/hwl_bias_resolution.py pilot
    python scripts/hwl_bias_resolution.py brute
    python scripts/hwl_bias_resolution.py tilt
    python scripts/hwl_bias_resolution.py kp57
    python scripts/hwl_bias_resolution.py epistemic
    python scripts/hwl_bias_resolution.py report
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import threading
import time
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import yaml
from joblib import Parallel, delayed
from numpy.typing import NDArray

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bep_reliability_engine.config import (  # noqa: E402
    Config,
    PriorMeanScenario,
    SellmeijerModelFactorSettings,
)
from bep_reliability_engine.evaluator import evaluate_batch  # noqa: E402
from bep_reliability_engine.fragility import (  # noqa: E402
    FragilityResult,
    binomial_ci,
    mc_cov_of_pf,
)
from bep_reliability_engine.gap_decomposition import (  # noqa: E402
    COMPARATOR_ORDER,
    GapDecompositionResult,
    prepare_config,
    run_comparator_ladder,
)
from bep_reliability_engine.run import (  # noqa: E402
    conditioning_hydrographs_for_config,
    model_factor_samples_for_config,
    seepage_length_samples_for_config,
)
from bep_reliability_engine.sampling import sample_theta  # noqa: E402
from bep_reliability_engine.tail_sampling import (  # noqa: E402
    cross_entropy_shift,
    importance_estimate,
    sample_theta_tilted,
)

OUT_DIR = REPO_ROOT / "results" / "hwl_bias_resolution"
EVIDENCE = REPO_ROOT / "docs" / "decisions" / "adr0040-hwl-bias-resolution.json"


def _load_adr0047_module():
    """Import the ADR-0047 study module for its ratio-of-ratios kernel.

    Reused, never re-implemented -- same ``importlib`` route
    ``scripts/epistemic_bracket_synthesis.py`` and
    ``tests/test_dem_cross_section.py`` already use. Stage D's *unweighted*
    ratio-of-ratios is cross-checked against this kernel in the tests, which is
    what licenses the weighted generalisation used alongside it.
    """
    path = REPO_ROOT / "scripts" / "dem_cross_section_study.py"
    spec = importlib.util.spec_from_file_location("dem_cross_section_study", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Pre-registered constants (docs/decisions/adr0040-hwl-bias-resolution.md, Part 1).
# Changing any of these invalidates the pre-registration; tests pin them.
# --------------------------------------------------------------------------
R1_MIN_ROWS: int = 30  # criterion R1: transient failing rows
R2_MAX_WIDTH: float = 2.0  # criterion R2: multiplicative CI width hi/lo
V3_TOLERANCE: float = 1.5  # criterion V3: P_IS / P_A within [1/1.5, 1.5]
V3_MIN_ROWS: int = 100  # criterion V3 applies at levels with >= this many rows
V4_MIN_NEFF: float = 200.0  # criterion V4: Kish n_eff floor at the anchor
V4_COV_FACTOR: float = 0.5  # criterion V4: tilted CoV <= half the plain-LHS CoV
F3_EPISTEMIC_FACTOR: float = 10.0  # criterion F3: epistemic / statistical width
SMOKE_MP_TOLERANCE: float = 1.5  # Stage D: m_p control must give rho in [1/1.5, 1.5]

BOOTSTRAP_REPLICATES: int = 10_000
BOOTSTRAP_SEED: int = 20260730

#: Stage A scope thresholds, fixed in the pre-registration section 1.6.
SCOPE_MAX_RSS_GB: float = 8.0
SCOPE_MAX_WALL_HOURS: float = 6.0

#: Stage B: the seeded conservative tilt the CE pilot starts from, and the
#: parameters tilted (the fm7 interaction direction, ADR-0029 section 4).
CE_SEED_SHIFT: dict[str, float] = {"k_aq": 1.0, "C_e": 1.0}
CE_PARAMETERS: tuple[str, ...] = ("k_aq", "C_e")

SECTIONS: dict[str, dict[str, Any]] = {
    "kp62_0": {
        "config": "configs/kp62_0_historical_matrix.yaml",
        "production_h5": "results/tokachi_kp62.0_historical_matrix.h5",
        "stem": "tokachi_kp62.0_historical_matrix",
        "label": "KP62.0",
        "synthesis_label": "KP62.0",
        "hwl_expected": 46.39,
        "a2_expected": 46.50,
        "attainable_max_m": 50.5,
    },
    "kp57_4": {
        "config": "configs/kp57_4_historical_matrix.yaml",
        "production_h5": "results/tokachi_kp57.4_historical_matrix.h5",
        "stem": "tokachi_kp57.4_historical_matrix",
        "label": "KP57.4",
        "synthesis_label": "KP57.4",
        "hwl_expected": 39.21,
        "a2_expected": 39.25,
        "attainable_max_m": 43.25,
    },
}


# ==========================================================================
# Statistics core -- no physics, injected indicators only.
# ==========================================================================


def paired_column_means_bootstrap(
    columns: Sequence[NDArray[np.bool_]],
    *,
    weights: NDArray[np.float64] | None = None,
    n_replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
    chunk: int = 50,
) -> NDArray[np.float64]:
    """Paired-bootstrap replicate means of K indicator columns on shared rows.

    **One** row-index resample per replicate feeds every column. That pairing is
    the whole point: the columns are evaluated on the same realizations (the
    ADR-0002 shared-sample contract), the transient set nests inside the static
    one in continuous time, and any statistic formed from them -- a difference,
    a ratio, a ratio of ratios -- inherits a CI that reflects the *discordant
    rows* rather than the variance of independent binomials.

    Two exact regimes, selected automatically:

    * **Unweighted** (``weights is None``): K boolean columns take at most
      ``2**K`` joint patterns, and resampling N rows with replacement makes the
      pattern counts exactly ``Multinomial(N, p_hat)``. The multinomial draw is
      therefore not an approximation of the index resample; it is the same
      distribution, at O(B * 2**K) instead of O(B * N). At K = 4 this is
      precisely the 16-cell contingency of the ADR-0047 section 4.5 kernel, and
      the tests cross-check it against that kernel directly.
    * **Weighted** (importance sampling, ADR-0029): pattern counts are no longer
      sufficient statistics once rows carry unequal weight -- two rows with the
      same pattern contribute differently -- so this is the pre-registered
      replacement for the unweighted pattern-count bootstrap, which is
      **invalid** under weights. It is still done exactly, and without an
      O(B * N) index gather, by the *active-row* reduction: a bootstrap draws
      row multiplicities ``c ~ Multinomial(N, uniform)``, and a row whose every
      column is False contributes exactly zero to every mean whatever its
      weight, so only the rows where some column fires need their multiplicity
      tracked. Collapsing all the silent rows into one lumped category gives an
      exactly equivalent ``Multinomial(N, [1/N]*n_active + [n_inactive/N])``
      over ``n_active + 1`` categories. In the deep tail, which is where this
      estimator is used, ``n_active`` is a few hundred out of 1e5.

    Parameters
    ----------
    columns : sequence of numpy.ndarray of bool, shape (N,)
        The indicator columns, all on the same N rows. K = len(columns).
    weights : numpy.ndarray, shape (N,), optional
        Linear importance weights. None means unweighted (all ones).
    n_replicates : int, optional
        Bootstrap replicates B.
    seed : int, optional
        Deterministic RNG seed.
    chunk : int, optional
        Upper bound on replicates drawn per multinomial call in the weighted
        route (the actual chunk adapts to ``n_active`` to cap peak memory). A
        memory/time trade-off only: the draw comes from one seeded generator
        either way.

    Returns
    -------
    numpy.ndarray, shape (B, K)
        Replicate means, column order preserved.
    """
    cols = [np.asarray(c, dtype=bool) for c in columns]
    if not cols:
        raise ValueError("paired_column_means_bootstrap needs at least one column.")
    n = cols[0].size
    if any(c.shape != (n,) for c in cols):
        raise ValueError("every column must be a 1-D array of the same length N.")
    k = len(cols)
    rng = np.random.default_rng(seed)

    if weights is None:
        code = np.zeros(n, dtype=np.int64)
        for bit, col in enumerate(cols):
            code += (np.int64(1) << bit) * col.astype(np.int64)
        counts = np.bincount(code, minlength=1 << k).astype(np.float64)
        bits = np.array(
            [[(pattern >> bit) & 1 for pattern in range(1 << k)] for bit in range(k)],
            dtype=np.float64,
        )
        draws = rng.multinomial(n, counts / n, size=n_replicates).astype(np.float64)
        return draws @ bits.T / n

    w = np.asarray(weights, dtype=np.float64)
    if w.shape != (n,):
        raise ValueError("weights must have the same (N,) shape as the columns.")
    weighted = np.stack([np.where(c, w, 0.0) for c in cols], axis=1)  # (N, K)
    active = np.zeros(n, dtype=bool)
    for col in cols:
        active |= col
    active_weighted = weighted[active]  # (n_active, K)
    n_active = int(active_weighted.shape[0])
    means = np.zeros((n_replicates, k), dtype=np.float64)
    if n_active == 0:
        return means
    # One lumped category absorbs every silent row, so the draw stays an exact
    # Multinomial(N, uniform) over all N rows -- just marginalised.
    probs = np.full(n_active + 1, 1.0 / n, dtype=np.float64)
    probs[-1] = 1.0 - n_active / n
    per_call = max(1, min(chunk, int(2e7 // (n_active + 1)) or 1))
    done = 0
    while done < n_replicates:
        size = min(per_call, n_replicates - done)
        draws = rng.multinomial(n, probs, size=size)[:, :n_active]
        means[done : done + size] = draws @ active_weighted / n
        done += size
    return means


def paired_ratio_bootstrap(
    static_flags: NDArray[np.bool_],
    transient_flags: NDArray[np.bool_],
    *,
    weights: NDArray[np.float64] | None = None,
    n_replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
    chunk: int = 50,
) -> NDArray[np.float64]:
    """Paired-bootstrap replicates of the bias ratio ``P_static / P_transient``."""
    means = paired_column_means_bootstrap(
        [static_flags, transient_flags],
        weights=weights,
        n_replicates=n_replicates,
        seed=seed,
        chunk=chunk,
    )
    p_s, p_t = means[:, 0], means[:, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(p_t > 0.0, p_s / np.where(p_t > 0.0, p_t, 1.0), np.inf)


def _percentile_ci(values: NDArray[np.float64], confidence: float = 0.95) -> tuple:
    alpha = 100.0 * (1.0 - confidence)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan"), float("nan")
    lo, hi = np.percentile(finite, [alpha / 2.0, 100.0 - alpha / 2.0])
    return float(lo), float(hi)


@dataclass(frozen=True)
class RatioEstimate:
    """One bias ratio B = P_static / P_transient with its paired interval.

    ``n_eff_transient`` is the Kish effective failure-region sample size. It is
    carried beside every weighted interval on purpose: an n_eff of 40 is not
    1e6 rows and must never be presented as if it were.
    """

    level_m: float
    p_static: float
    p_transient: float
    ratio: float
    ci_lo: float
    ci_hi: float
    width_factor: float
    k_static: int
    k_transient: int
    n_eff_transient: float
    n_samples: int
    weighted: bool

    @property
    def resolved(self) -> bool:
        """The pre-registered criterion: R1 AND R2 (both, never either)."""
        return (
            self.k_transient >= R1_MIN_ROWS
            and np.isfinite(self.width_factor)
            and self.width_factor <= R2_MAX_WIDTH
        )

    @property
    def criterion_flags(self) -> dict[str, bool]:
        return {
            "R1_rows": bool(self.k_transient >= R1_MIN_ROWS),
            "R2_width": bool(
                np.isfinite(self.width_factor) and self.width_factor <= R2_MAX_WIDTH
            ),
            "resolved": bool(self.resolved),
        }


def bias_ratio(
    level_m: float,
    static_flags: NDArray[np.bool_],
    transient_flags: NDArray[np.bool_],
    *,
    weights: NDArray[np.float64] | None = None,
    n_replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> RatioEstimate:
    """The bias ratio at one level with its paired-bootstrap interval."""
    stat = np.asarray(static_flags, dtype=bool)
    tran = np.asarray(transient_flags, dtype=bool)
    n = stat.size
    if weights is None:
        p_s = float(stat.mean())
        p_t = float(tran.mean())
        n_eff = float(tran.sum()) if tran.any() else float("nan")
    else:
        w = np.asarray(weights, dtype=np.float64)
        p_s = float(np.where(stat, w, 0.0).mean())
        p_t = float(np.where(tran, w, 0.0).mean())
        wt = w[tran]
        n_eff = float(wt.sum() ** 2 / np.square(wt).sum()) if wt.size else float("nan")
    reps = paired_ratio_bootstrap(
        stat, tran, weights=weights, n_replicates=n_replicates, seed=seed
    )
    lo, hi = _percentile_ci(reps)
    ratio = p_s / p_t if p_t > 0.0 else float("inf")
    width = (
        hi / lo if (np.isfinite(lo) and lo > 0.0 and np.isfinite(hi)) else float("inf")
    )
    return RatioEstimate(
        level_m=float(level_m),
        p_static=p_s,
        p_transient=p_t,
        ratio=float(ratio),
        ci_lo=lo,
        ci_hi=hi,
        width_factor=float(width),
        k_static=int(stat.sum()),
        k_transient=int(tran.sum()),
        n_eff_transient=n_eff,
        n_samples=int(n),
        weighted=weights is not None,
    )


def ratio_of_ratios(
    base_static: NDArray[np.bool_],
    base_trans: NDArray[np.bool_],
    arm_static: NDArray[np.bool_],
    arm_trans: NDArray[np.bool_],
    *,
    weights: NDArray[np.float64] | None = None,
    n_replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """rho = (P_s/P_t)_arm / (P_s/P_t)_baseline, paired across all four columns.

    The pairing across *arms* is legitimate by common random numbers: an
    epistemic arm moves a prior mean, a datum or a geometry scalar while leaving
    the family, CoV, name, ordering, seed and LHS design untouched, so row j is
    the same stratum in both arms. Under a tilt the weights are identical in
    both arms too (the ADR-0029 log-weight depends only on the Z coordinates,
    which the arm does not move), so they cancel in the point estimate of rho
    and are carried correctly through the bootstrap.

    Null pinned at rho = 1.0 exactly; ``resolved`` only when the interval
    excludes it (the ADR-0040 Decision 6 rule).
    """
    means = paired_column_means_bootstrap(
        [base_static, base_trans, arm_static, arm_trans],
        weights=weights,
        n_replicates=n_replicates,
        seed=seed,
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        rho_reps = (means[:, 2] / means[:, 3]) / (means[:, 0] / means[:, 1])
    lo, hi = _percentile_ci(rho_reps)

    def _mean(col, w):
        col = np.asarray(col, dtype=bool)
        return float(col.mean()) if w is None else float(np.where(col, w, 0.0).mean())

    bs, bt = _mean(base_static, weights), _mean(base_trans, weights)
    as_, at = _mean(arm_static, weights), _mean(arm_trans, weights)
    point = (as_ / at) / (bs / bt) if at > 0 and bt > 0 and bs > 0 else float("nan")
    return {
        "rho": float(point),
        "rho_lo": lo,
        "rho_hi": hi,
        "resolved": bool(
            np.isfinite(lo) and np.isfinite(hi) and (lo > 1.0 or hi < 1.0)
        ),
        "departure_factor": (
            float(max(point, 1.0 / point))
            if np.isfinite(point) and point > 0
            else float("nan")
        ),
        "min_cell_failures": int(
            min(
                int(np.asarray(c, dtype=bool).sum())
                for c in (base_static, base_trans, arm_static, arm_trans)
            )
        ),
        "weighted": weights is not None,
    }


def _stable_seed(label: str) -> int:
    """A deterministic per-arm bootstrap seed.

    ``hash()`` on a str is salted per interpreter process unless PYTHONHASHSEED
    is pinned, so using it here would make the reported intervals irreproducible
    between runs. CRC32 is stable across processes and platforms.
    """
    return int(zlib.crc32(label.encode("utf-8")) % 2**31)


def cp_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Clopper-Pearson interval for a raw count, via the production helper."""
    lo, hi = binomial_ci(np.array([k / n], dtype=np.float64), n, confidence)
    return float(lo[0]), float(hi[0])


def intervals_overlap(a: tuple[float, float], b: tuple[float, float]) -> bool:
    """Whether two closed intervals intersect (criteria F2 / V2)."""
    if not all(np.isfinite(x) for x in (*a, *b)):
        return True  # an unbounded interval cannot be shown to disagree
    return not (a[1] < b[0] or b[1] < a[0])


# ==========================================================================
# Shared plumbing
# ==========================================================================


class PeakMemory:
    """Sample the peak RSS of this process **and its joblib workers**.

    The parent's own peak working set is not the run's footprint: the level loop
    runs in loky worker processes that each hold a copy of theta and the M8
    working arrays. Measuring only the parent under-reports by roughly the
    worker count, which would make the Stage A scope projection meaningless.
    """

    def __init__(self, interval_s: float = 1.0) -> None:
        self.interval_s = interval_s
        self.peak_gb = float("nan")
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _sample(self) -> float:
        import psutil

        proc = psutil.Process()
        total = proc.memory_info().rss
        for child in proc.children(recursive=True):
            try:
                total += child.memory_info().rss
            except psutil.Error:  # pragma: no cover - race with worker exit
                pass
        return total / 2**30

    def _loop(self) -> None:
        peak = 0.0
        while not self._stop.is_set():
            try:
                peak = max(peak, self._sample())
            except Exception:  # pragma: no cover - defensive
                pass
            self.peak_gb = peak
            self._stop.wait(self.interval_s)

    def __enter__(self) -> PeakMemory:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)


def load_section(key: str) -> tuple[Config, float, float]:
    """Return (config, A1 = exact HWL, A2 = nearest grid level).

    The HWL is read from ``configs/*.yaml`` ``geometry.HWL`` and asserted against
    the tabulated pre-registration value; A2 is derived from the generated
    conditioning grid. No HWL is ever taken from a prose document.
    """
    spec = SECTIONS[key]
    path = REPO_ROOT / spec["config"]
    config = Config.from_yaml(path)
    hwl = float(config.geometry.HWL)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if float(raw["geometry"]["HWL"]) != hwl:
        raise AssertionError(f"{key}: Config.geometry.HWL != the YAML value.")
    if abs(hwl - spec["hwl_expected"]) > 1e-9:
        raise AssertionError(
            f"{key}: config HWL {hwl} != pre-registered {spec['hwl_expected']}. "
            "The pre-registration names the level being resolved; a moved HWL "
            "invalidates it."
        )
    grid = np.asarray(config.mc.conditioning_grid, dtype=np.float64)
    a2 = float(grid[int(np.argmin(np.abs(grid - hwl)))])
    if abs(a2 - spec["a2_expected"]) > 1e-9:
        raise AssertionError(
            f"{key}: nearest grid level {a2} != pre-registered {spec['a2_expected']}."
        )
    return config, hwl, a2


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        value = float(obj)
        return value if np.isfinite(value) else str(value)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    raise TypeError(f"not JSON-serializable: {type(obj)}")


def _num(value: Any) -> float:
    """Read a possibly ``_clean``-stringified float back as a number."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _clean(obj: Any) -> Any:
    """Replace non-finite floats with strings so JSON round-trips exactly."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        return str(obj)
    return obj


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_clean(payload), indent=2, sort_keys=True, default=_jsonable)
    )
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ratio_payload(est: RatioEstimate) -> dict:
    payload = _clean(asdict(est))
    payload.update(est.criterion_flags)
    return payload


def run_ladder(
    config: Config,
    *,
    n_samples: int | None,
    extra_levels: Sequence[float],
    n_jobs: int,
    theta_override: NDArray[np.float64] | None = None,
    grid_override: Sequence[float] | None = None,
) -> tuple[GapDecompositionResult, float, float]:
    """Run the ten-comparator ladder; return (result, wall seconds, peak GB)."""
    cfg = prepare_config(
        config, n_samples=n_samples, extra_levels=tuple(float(x) for x in extra_levels)
    )
    if grid_override is not None:
        grid = tuple(sorted({float(x) for x in grid_override}))
        cfg = cfg.model_copy(
            update={"mc": cfg.mc.model_copy(update={"conditioning_grid": grid})}
        )
    started = time.time()
    with PeakMemory() as probe:
        result = run_comparator_ladder(
            cfg, n_jobs=n_jobs, theta_override=theta_override
        )
    return result, time.time() - started, probe.peak_gb


def level_index(grid: NDArray[np.float64], level_m: float) -> int:
    matches = np.flatnonzero(np.isclose(np.asarray(grid, dtype=float), level_m))
    if matches.size != 1:
        raise KeyError(f"level {level_m} not uniquely present in the grid.")
    return int(matches[0])


def flip_summary(result: GapDecompositionResult) -> dict:
    """Gate G-A2: every Euler-flip count must be exactly 0 at every level.

    Records *where* any nonzero count sits, not just that one exists: a flip is
    the ADR-0030 barrier-jump fingerprint, and whether it lands near the design
    anchor or far above it decides whether it touches the deliverable.
    """
    totals = {name: int(counts.sum()) for name, counts in result.flip_counts.items()}
    offenders: dict[str, list[dict[str, float]]] = {}
    for name, counts in result.flip_counts.items():
        hits = [
            {"level_m": float(result.conditioning_grid[i]), "count": int(counts[i])}
            for i in np.flatnonzero(np.asarray(counts) > 0)
        ]
        if hits:
            offenders[name] = hits
    return {
        "per_diagnostic_totals": totals,
        "all_zero": all(v == 0 for v in totals.values()),
        "levels": int(result.conditioning_grid.size),
        "offending_levels": offenders,
    }


def convergence_block(result: GapDecompositionResult) -> dict:
    """Gate G-A4: spec section 11 analytic estimator CoV, both branches."""
    p_f = result.p_f()
    out: dict[str, Any] = {}
    for branch, name in (("static", "C0"), ("transient", "C4b")):
        cov = mc_cov_of_pf(p_f[name], result.n_samples)
        finite = [c for c in cov if c is not None]
        out[branch] = {
            "max_cov": max(finite) if finite else None,
            "levels_meeting_5pct": int(sum(1 for c in finite if c <= 0.05)),
            "levels_with_defined_cov": len(finite),
            "cov_per_level": cov,
        }
    return out


def ladder_bias_table(result: GapDecompositionResult, **kwargs) -> list[dict]:
    """The bias ratio at every level of a ladder result."""
    rows = []
    for i, level in enumerate(result.conditioning_grid):
        est = bias_ratio(
            float(level),
            result.comparators["C0"][:, i],
            result.comparators["C4b"][:, i],
            **kwargs,
        )
        rows.append(ratio_payload(est))
    return rows


# ==========================================================================
# Direct M8 evaluation (Stage D): production static/transient branches only.
# ==========================================================================


def _eval_level(level_m, record, theta, geometry, settings):
    return level_m, evaluate_batch(theta, record, geometry, **settings)


def production_branches(
    config: Config,
    levels: Sequence[float],
    *,
    theta: NDArray[np.float64] | None = None,
    n_samples: int | None = None,
    n_jobs: int = 1,
) -> dict[float, tuple[NDArray[np.bool_], NDArray[np.bool_]]]:
    """C0 / C4b at the requested levels, straight through M8 ``evaluate_batch``.

    Identical to what the ADR-0040 ladder labels C0 and C4b (it takes those two
    comparators from exactly this call), but without evaluating the other eight,
    which Stage D does not need. Every ADR-0045/0046/0048 knob the arm configs
    carry is threaded here the way ``run.py`` threads it, including the m_p draw
    -- which the comparator ladder does not currently support, and which is why
    Stage D goes direct rather than through the ladder.
    """
    grid = tuple(sorted({float(x) for x in levels}))
    mc_updates: dict[str, Any] = {"conditioning_grid": grid}
    if n_samples is not None:
        mc_updates["n_samples"] = int(n_samples)
    cfg = config.model_copy(update={"mc": config.mc.model_copy(update=mc_updates)})
    if theta is None:
        theta = sample_theta(
            cfg.effective_marginal_specs(),
            seed=cfg.mc.seed,
            rho_log_kaq_d70=cfg.correlation.rho_log_kaq_d70,
            d70_interpretation=cfg.priors.d70_interpretation,
            n_samples=cfg.mc.n_samples,
            coupling=cfg.correlation.coupling,
            bounds=cfg.priors.bounds,
        ).theta_matrix
    records = conditioning_hydrographs_for_config(cfg)
    settings = dict(
        l_ini=0.0,
        seepage_length_samples=seepage_length_samples_for_config(cfg),
        alpha_exponent=cfg.alpha_exponent,
        alpha_exponent_transient=cfg.alpha_exponent_transient,
        theta_repose_rad=cfg.theta_repose_rad,
        relative_density=cfg.relative_density_insitu,
        foreland_open=cfg.foreland_treatment == "open_entry",
        progression_backend="numpy",
        model_factor_samples=model_factor_samples_for_config(cfg),
    )
    geometry = cfg.geometry.as_evaluator_dict()
    out = Parallel(n_jobs=n_jobs)(
        delayed(_eval_level)(float(grid[i]), records[i], theta, geometry, settings)
        for i in range(len(grid))
    )
    return {level: flags for level, flags in out}


def epistemic_arms(config: Config, key: str) -> list[tuple[str, str, Config]]:
    """(arm label, bracket, arm Config) for every Stage D arm.

    Constructed the same way each accepted companion driver constructs it, from
    the section's own committed YAML -- ``m_p`` FIRST, because it is the
    pre-registered negative control (ADR-0045 section 2 applies it to the
    single-source H_c in *both* uses, so it is pure common-mode by construction
    and must return rho ~ 1). Every knob stays OFF in production; these configs
    exist only in memory.
    """
    adr0045 = SellmeijerModelFactorSettings(enabled=True)
    z0 = float(config.geometry.z_toe)
    arms: list[tuple[str, str, Config]] = [
        (
            "m_p",
            "m_p",
            config.model_copy(update={"sellmeijer_model_factor": adr0045}),
        )
    ]
    for label, param, target in (
        ("k_aq_field_toe", "k_aq", 5.15e-4),
        ("k_aq_field_geomean", "k_aq", 5.94e-5),
        ("k_aq_regional_upper", "k_aq", 1.0e-2),
        ("gamma_bl_sub_lower", "gamma_bl_sub", 6.0),
    ):
        factor = target / float(getattr(config.priors, param).mean)
        bracket = "k_aq_prior_mean" if param == "k_aq" else "gamma_bl_sub_prior_mean"
        arms.append(
            (
                label,
                bracket,
                config.model_copy(
                    update={
                        "prior_mean_scenario": PriorMeanScenario(
                            enabled=True, label=label, factors={param: factor}
                        )
                    }
                ),
            )
        )
    for sign in (+1, -1):
        arms.append(
            (
                f"z_toe_{'plus' if sign > 0 else 'minus'}0.30m",
                "z_toe",
                config.model_copy(
                    update={
                        "geometry": config.geometry.model_copy(
                            update={"z_toe": z0 + sign * 0.30}
                        )
                    }
                ),
            )
        )
    for arm_label, arm_L in _seepage_length_arms(key, float(config.geometry.L)):
        arms.append(
            (
                f"L_{arm_label}",
                "L_measurement",
                config.model_copy(
                    update={"geometry": config.geometry.model_copy(update={"L": arm_L})}
                ),
            )
        )
    return arms


def _seepage_length_arms(key: str, current_L: float) -> list[tuple[str, float]]:
    """The ADR-0047 L arms, reusing the synthesis driver's accepted selection."""
    import epistemic_bracket_synthesis as EBS

    return EBS.seepage_length_arms(SECTIONS[key]["synthesis_label"], current_L)


# ==========================================================================
# Stages
# ==========================================================================


def cmd_verify(args: argparse.Namespace) -> dict:
    """Gates G-A1/G-A2: the N = 1e5 ladder still reproduces the persisted sweep."""
    from stage6_6_gap_decomposition import verify_against_production

    payload: dict[str, Any] = {"stage": "G-A1 drift guard", "sections": {}}
    for key in args.sections:
        config, hwl, a2 = load_section(key)
        print(f"[{key}] N=1e5 drift-guard re-run (A1 {hwl}, A2 {a2}) ...")
        result, wall, peak = run_ladder(
            config, n_samples=None, extra_levels=(hwl,), n_jobs=args.n_jobs
        )
        result.metadata["base_config_hash"] = config.config_hash()
        record = verify_against_production(key, result)
        flips = flip_summary(result)
        payload["sections"][key] = {
            "hwl_a1": hwl,
            "a2": a2,
            "n_samples": result.n_samples,
            "wall_seconds": round(wall, 1),
            "peak_rss_gb": round(peak, 2),
            "drift_guard": record,
            "euler_flips": flips,
            "convergence": convergence_block(result),
            "bias_table": ladder_bias_table(result),
        }
        if record.get("status") != "bit_identical":
            raise SystemExit(f"GATE G-A1 FAILED at {key}: {record}")
        if not flips["all_zero"]:
            raise SystemExit(f"GATE G-A2 FAILED at {key}: {flips}")
        out = OUT_DIR / f"ladder_{key}_n{result.n_samples}.h5"
        result.save(out)
        payload["sections"][key]["artifact"] = str(out.relative_to(REPO_ROOT))
        print(f"  wall {wall:.0f}s  peak {peak:.2f} GB  flips all-zero")
    _write(OUT_DIR / "stage_a_verify.json", payload)
    return payload


def cmd_pilot(args: argparse.Namespace) -> dict:
    """Stage A pilot: measured, then extrapolated to 1e6 to select the scope."""
    key = args.sections[0]
    config, hwl, _ = load_section(key)
    n_pilot = args.n
    print(f"[{key}] pilot at N={n_pilot:,} ...")
    result, wall, peak = run_ladder(
        config, n_samples=n_pilot, extra_levels=(hwl,), n_jobs=args.n_jobs
    )
    scale = 1_000_000 / n_pilot
    bytes_per_row = len(COMPARATOR_ORDER) * result.conditioning_grid.size
    projected_rss = peak * scale if np.isfinite(peak) else float("nan")
    projected_hours = wall * scale / 3600.0
    payload = {
        "stage": "A pilot",
        "section": key,
        "n_pilot": n_pilot,
        "levels": int(result.conditioning_grid.size),
        "wall_seconds": round(wall, 1),
        "peak_rss_gb": round(peak, 2),
        "comparator_array_at_1e6_gb": round(bytes_per_row * 1e6 / 2**30, 2),
        "projection_1e6": {
            "wall_hours": round(projected_hours, 2),
            "peak_rss_gb_linear": round(projected_rss, 2),
            "note": (
                "RSS scales sub-linearly: a fixed interpreter/library footprint "
                "sits in every worker, so the linear projection is an upper bound."
            ),
        },
        "scope_thresholds": {
            "max_rss_gb": SCOPE_MAX_RSS_GB,
            "max_wall_hours": SCOPE_MAX_WALL_HOURS,
        },
        "scope_decision": (
            "full_ten_comparator_ladder"
            if projected_rss <= SCOPE_MAX_RSS_GB
            and projected_hours <= SCOPE_MAX_WALL_HOURS
            else "reduced_scope_required"
        ),
        "euler_flips": flip_summary(result),
    }
    print(json.dumps(_clean(payload["projection_1e6"]), indent=2))
    print(f"  scope decision: {payload['scope_decision']}")
    _write(OUT_DIR / "stage_a_pilot.json", payload)
    return payload


def cmd_brute(args: argparse.Namespace) -> dict:
    """Stage A: brute-force ground truth at N = 1e6."""
    key = args.sections[0]
    config, hwl, a2 = load_section(key)
    n_big = args.n
    print(f"[{key}] Stage A brute force at N={n_big:,} ...")
    result, wall, peak = run_ladder(
        config, n_samples=n_big, extra_levels=(hwl,), n_jobs=args.n_jobs
    )
    # Persist BEFORE gating. A gate that discards the evidence it failed on
    # forces a multi-hour re-run to diagnose its own alarm, and the alarm is
    # exactly the thing worth inspecting. (Learned the hard way: the first
    # KP 57.4 N=1e6 run raised on G-A2 and threw away 2.5 h of comparator
    # matrices.) The gate still stops the task -- it just stops it with the
    # evidence on disk.
    out = OUT_DIR / f"ladder_{key}_n{n_big}.h5"
    result.save(out)
    flips = flip_summary(result)

    # G-A3: consistency with the N=1e5 arm at every adequately-counted level.
    small = GapDecompositionResult.load(OUT_DIR / f"ladder_{key}_n100000.h5")
    consistency = []
    for i, level in enumerate(small.conditioning_grid):
        j = level_index(result.conditioning_grid, float(level))
        row: dict[str, Any] = {"level_m": float(level)}
        ok = True
        for branch, name in (("static", "C0"), ("transient", "C4b")):
            k_small = int(small.comparators[name][:, i].sum())
            p_big = float(result.comparators[name][:, j].mean())
            lo, hi = cp_interval(k_small, small.n_samples)
            inside = bool(lo <= p_big <= hi)
            row[branch] = {
                "k_1e5": k_small,
                "p_1e5": k_small / small.n_samples,
                "p_big": p_big,
                "cp_1e5": [lo, hi],
                "adequate": k_small >= R1_MIN_ROWS,
                "inside": inside,
            }
            if k_small >= R1_MIN_ROWS and not inside:
                ok = False
        row["pass"] = ok
        consistency.append(row)
    n_tested = sum(
        1 for r in consistency if r["static"]["adequate"] or r["transient"]["adequate"]
    )
    n_comparisons = sum(
        1
        for r in consistency
        for branch in ("static", "transient")
        if r[branch]["adequate"]
    )
    failures = [r for r in consistency if not r["pass"]]

    payload = {
        "stage": "A brute force",
        "section": key,
        "n_samples": result.n_samples,
        "levels": int(result.conditioning_grid.size),
        "wall_seconds": round(wall, 1),
        "peak_rss_gb": round(peak, 2),
        "artifact": str(out.relative_to(REPO_ROOT)),
        "anchors": {"A1_hwl": hwl, "A2_grid": a2},
        "euler_flips": flips,
        "convergence": convergence_block(result),
        "gate_G_A3": {
            "levels_tested": n_tested,
            "branch_comparisons_tested": n_comparisons,
            "levels_failing": [r["level_m"] for r in failures],
            "pass": not failures,
            "detail": consistency,
        },
        "bias_table": ladder_bias_table(result),
    }
    for name, level in (("A1", hwl), ("A2", a2)):
        j = level_index(result.conditioning_grid, level)
        est = bias_ratio(
            level, result.comparators["C0"][:, j], result.comparators["C4b"][:, j]
        )
        payload[f"anchor_{name}"] = ratio_payload(est)
        print(
            f"  {name} {level:.2f} m: B={est.ratio:.1f} "
            f"[{est.ci_lo:.1f}, {est.ci_hi:.1f}] k_trans={est.k_transient} "
            f"resolved={est.resolved}"
        )
    payload["gate_G_A2"] = {"pass": flips["all_zero"], "detail": flips}
    # Write the evidence unconditionally, then gate. Both gates stop the task on
    # failure, as pre-registered -- but with the diagnostics on disk.
    _write(OUT_DIR / f"stage_a_brute_{key}.json", payload)
    if not flips["all_zero"]:
        raise SystemExit(
            f"GATE G-A2 FAILED at N={n_big}: nonzero Euler flips "
            f"{flips['per_diagnostic_totals']} at {flips['offending_levels']}. "
            f"Evidence written to stage_a_brute_{key}.json and {out.name}."
        )
    if failures:
        bad = [r["level_m"] for r in failures]
        raise SystemExit(f"GATE G-A3 FAILED at levels {bad}")
    print(f"  wall {wall / 60:.0f} min  peak {peak:.2f} GB  G-A2 + G-A3 pass")
    return payload


def _tilted_population(config: Config, shift: dict[str, float], n_samples: int | None):
    """One tilted draw through the exact M2 pipeline (ADR-0029)."""
    n = int(n_samples if n_samples is not None else config.mc.n_samples)
    return sample_theta_tilted(
        config.effective_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        shift_z=shift or None,
        n_samples=n,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
        stratified=True,
    )


def _self_gate_v1(config: Config) -> dict:
    """V1: zero-shift stratified draws reproduce ``sample_theta`` bit for bit."""
    plain = sample_theta(
        config.effective_marginal_specs(),
        seed=config.mc.seed,
        rho_log_kaq_d70=config.correlation.rho_log_kaq_d70,
        d70_interpretation=config.priors.d70_interpretation,
        n_samples=config.mc.n_samples,
        coupling=config.correlation.coupling,
        bounds=config.priors.bounds,
    ).theta_matrix
    zero = _tilted_population(config, {}, None)
    identical = bool(np.array_equal(plain, zero.theta.theta_matrix))
    weights_unit = bool(np.all(zero.log_weights == 0.0))
    if not (identical and weights_unit):
        raise SystemExit(
            "GATE V1 FAILED: zero-shift tilted draw is not bit-identical to "
            f"sample_theta (theta identical={identical}, weights zero={weights_unit})."
        )
    return {"theta_bit_identical": identical, "log_weights_all_zero": weights_unit}


def _tilt_section(key: str, args: argparse.Namespace) -> dict:
    config, hwl, a2 = load_section(key)
    print(f"[{key}] Stage B/C tilted estimator; V1 self-gate ...")
    v1 = _self_gate_v1(config)

    # --- CE pilot: a seeded conservative tilt at the anchor, then one CE step.
    # The seed shift is escalated until the pilot actually observes failures.
    # This is necessary, not cosmetic: at KP 57.4 the anchor carries zero
    # transient failures in 1e5 plain-LHS draws, so a pilot at the nominal seed
    # shift can easily see none either, and cross_entropy_shift refuses (rightly)
    # to invent an update from an empty failure set. Escalating the *seed* only
    # changes where the pilot looks; the CE step that follows is unchanged, the
    # final weights are exact whatever the seed was, and the escalation ladder is
    # recorded so the choice is visible rather than buried.
    escalation: list[dict[str, Any]] = []
    pilot = None
    pilot_fail = None
    for multiplier in (1.0, 2.0, 3.0, 4.0):
        seed_shift = {k: v * multiplier for k, v in CE_SEED_SHIFT.items()}
        print(f"  CE pilot at A1={hwl} with seed shift {seed_shift} ...")
        candidate = _tilted_population(config, seed_shift, args.n_pilot)
        candidate_result, _, _ = run_ladder(
            config,
            n_samples=args.n_pilot,
            extra_levels=(hwl,),
            n_jobs=args.n_jobs,
            theta_override=candidate.theta.theta_matrix,
            grid_override=(hwl,),
        )
        fail = candidate_result.comparators["C4b"][:, 0]
        escalation.append({"seed_shift": seed_shift, "failures": int(fail.sum())})
        if fail.any():
            pilot, pilot_fail = candidate, fail
            break
    if pilot is None or pilot_fail is None:
        raise SystemExit(
            f"{key}: the CE pilot observed no transient failure at {hwl} m even "
            f"at seed shift x4 (ladder {escalation}). The anchor is beyond the "
            "reach of this proposal family; report a bound, not an estimate."
        )
    shift = cross_entropy_shift(pilot, pilot_fail, CE_PARAMETERS)
    print(f"  pilot transient failures {int(pilot_fail.sum())} -> CE shift {shift}")

    # --- Production tilt: one sample, one weight vector, ALL comparators, and
    # the FULL conditioning grid. The grid is not narrowed to the anchor
    # neighbourhood on purpose: the pre-registration tests V2/V3 at *every*
    # level of the Stage A validation set S, which includes levels far above the
    # anchor where an anchor-optimised tilt is expected to be poor. Narrowing
    # the grid would have quietly excluded exactly the levels most likely to
    # falsify the estimator.
    tilted = _tilted_population(config, shift, None)
    result, wall, peak = run_ladder(
        config,
        n_samples=None,
        extra_levels=(hwl,),
        n_jobs=args.n_jobs,
        theta_override=tilted.theta.theta_matrix,
    )
    weights = tilted.weights
    out = OUT_DIR / f"tilted_{key}.h5"
    result.save(out)

    rows: list[dict[str, Any]] = []
    for i, level in enumerate(result.conditioning_grid):
        stat = result.comparators["C0"][:, i]
        tran = result.comparators["C4b"][:, i]
        est_t = importance_estimate(tran, tilted.log_weights)
        est_s = importance_estimate(stat, tilted.log_weights)
        # The weighted bootstrap's cost grows with the number of *active* rows,
        # which is small in the tail and near N at saturation levels. The full
        # B is spent at the two anchors, which are what carry the claim; other
        # levels get B/5, which is ample for the V2/V3 comparisons (those rest
        # on the estimator's own analytic standard error, not on this bootstrap).
        is_anchor = bool(np.isclose(level, hwl) or np.isclose(level, a2))
        ratio = bias_ratio(
            float(level),
            stat,
            tran,
            weights=weights,
            n_replicates=BOOTSTRAP_REPLICATES if is_anchor else 2000,
        )
        rows.append(
            {
                "level_m": float(level),
                "transient": _clean(asdict(est_t)),
                "static": _clean(asdict(est_s)),
                "bias": ratio_payload(ratio),
            }
        )
    return {
        "section": key,
        "anchors": {"A1_hwl": hwl, "A2_grid": a2},
        "V1_self_gate": v1,
        "ce_seed_shift": CE_SEED_SHIFT,
        "ce_seed_escalation": escalation,
        "ce_pilot_n": args.n_pilot,
        "ce_pilot_failures": int(pilot_fail.sum()),
        "ce_shift": shift,
        "n_samples": result.n_samples,
        "wall_seconds": round(wall, 1),
        "peak_rss_gb": round(peak, 2),
        "artifact": str(out.relative_to(REPO_ROOT)),
        "levels": rows,
    }


def cmd_tilt(args: argparse.Namespace) -> dict:
    """Stage B: build the tilted estimator and validate it against Stage A."""
    key = args.sections[0]
    payload = _tilt_section(key, args)

    brute = GapDecompositionResult.load(OUT_DIR / f"ladder_{key}_n{args.n_truth}.h5")
    small = GapDecompositionResult.load(OUT_DIR / f"ladder_{key}_n100000.h5")
    checks: list[dict[str, Any]] = []
    for row in payload["levels"]:
        level = row["level_m"]
        j = level_index(brute.conditioning_grid, level)
        k_truth = int(brute.comparators["C4b"][:, j].sum())
        p_truth = k_truth / brute.n_samples
        cp_truth = cp_interval(k_truth, brute.n_samples)
        p_is = row["transient"]["p_f"]
        se = row["transient"]["standard_error"]
        is_ci = (p_is - 1.96 * se, p_is + 1.96 * se)
        entry = {
            "level_m": level,
            "in_S": k_truth >= R1_MIN_ROWS,
            "k_truth": k_truth,
            "p_truth": p_truth,
            "cp_truth": list(cp_truth),
            "p_is": p_is,
            "is_ci": list(is_ci),
            "ratio_is_over_truth": (p_is / p_truth) if p_truth > 0 else float("nan"),
            "V2_overlap": intervals_overlap(is_ci, cp_truth),
            "n_eff": _num(row["transient"]["n_effective"]),
        }
        checks.append(entry)

    in_s = [c for c in checks if c["in_S"]]
    v2 = all(c["V2_overlap"] for c in in_s)
    v3_levels = [c for c in in_s if c["k_truth"] >= V3_MIN_ROWS]
    v3_within = all(
        1.0 / V3_TOLERANCE <= c["ratio_is_over_truth"] <= V3_TOLERANCE
        for c in v3_levels
        if np.isfinite(c["ratio_is_over_truth"])
    )
    signs = [
        np.sign(np.log(c["ratio_is_over_truth"]))
        for c in in_s
        if np.isfinite(c["ratio_is_over_truth"]) and c["ratio_is_over_truth"] > 0
    ]
    all_same_sign = len(signs) >= 5 and len(set(signs)) == 1
    v3 = bool(v3_within and not all_same_sign)

    a1 = payload["anchors"]["A1_hwl"]
    anchor_row = next(r for r in payload["levels"] if r["level_m"] == a1)
    # _clean() turns non-finite floats into strings for exact JSON round-tripping,
    # so read them back numerically before comparing against a threshold.
    n_eff = _num(anchor_row["transient"]["n_effective"])
    cov_is = _num(anchor_row["transient"]["cov"])
    i_small = level_index(small.conditioning_grid, a1)
    p_small = float(small.comparators["C4b"][:, i_small].mean())
    cov_lhs = (
        float(np.sqrt((1.0 - p_small) / (small.n_samples * p_small)))
        if p_small > 0
        else float("inf")
    )
    v4 = bool(
        np.isfinite(n_eff)
        and n_eff >= V4_MIN_NEFF
        and np.isfinite(cov_is)
        and cov_is <= V4_COV_FACTOR * cov_lhs
    )

    # The static branch under a transient-optimised tilt: measured, not assumed.
    static_cost = []
    for row in payload["levels"]:
        level = row["level_m"]
        i = level_index(small.conditioning_grid, level)
        p_s_small = float(small.comparators["C0"][:, i].mean())
        cov_s_lhs = (
            float(np.sqrt((1.0 - p_s_small) / (small.n_samples * p_s_small)))
            if p_s_small > 0
            else float("inf")
        )
        static_cost.append(
            {
                "level_m": level,
                "cov_static_tilted": _num(row["static"]["cov"]),
                "cov_static_plain_lhs": cov_s_lhs,
                "inflation_factor": (
                    (_num(row["static"]["cov"]) / cov_s_lhs)
                    if np.isfinite(cov_s_lhs) and cov_s_lhs > 0
                    else float("nan")
                ),
                "n_eff_static": _num(row["static"]["n_effective"]),
            }
        )

    payload["validation"] = {
        "V1_self_gate": payload["V1_self_gate"],
        "V2_no_level_disagrees": v2,
        "V3_no_systematic_offset": v3,
        "V3_within_tolerance": bool(v3_within),
        "V3_all_same_sign": bool(all_same_sign),
        "V4_efficiency": v4,
        "V4_detail": {
            "anchor_m": a1,
            "n_eff": n_eff,
            "n_eff_floor": V4_MIN_NEFF,
            "cov_tilted": cov_is,
            "cov_plain_lhs_same_N": cov_lhs,
            "cov_factor_required": V4_COV_FACTOR,
        },
        "VALIDATED": bool(v2 and v3 and v4),
        "levels": checks,
        "static_branch_cost_under_transient_tilt": static_cost,
    }
    print(
        f"  V2={v2} V3={v3} V4={v4} -> VALIDATED={payload['validation']['VALIDATED']}"
    )
    _write(OUT_DIR / f"stage_b_tilt_{key}.json", payload)
    return payload


def cmd_kp57(args: argparse.Namespace) -> dict:
    """Stage C: the estimator where brute force cannot reach."""
    args.sections = ["kp57_4"]
    payload = _tilt_section("kp57_4", args)
    payload["stage"] = "C KP57.4"
    _write(OUT_DIR / "stage_c_kp57_4.json", payload)
    for row in payload["levels"]:
        b = row["bias"]
        print(
            f"  {row['level_m']:.2f} m: B={b['ratio']} k_trans={b['k_transient']} "
            f"n_eff={row['transient']['n_effective']}"
        )
    return payload


def lowest_resolved_level(key: str, n: int) -> float | None:
    """The lowest conditioning level whose bias meets R1 and R2 at N = ``n``.

    Added after Stage A measured KP 57.4's two design-HWL anchors as *unresolved*
    even at N = 1e6 (2 and 10 transient rows). An epistemic band computed on an
    unresolved ratio would be uninformative, so Stage D also evaluates the lowest
    level where the ratio *is* resolved -- which is the level the deliverable
    recommends quoting at that section. At KP 62.0 this coincides with A1, so the
    addition costs nothing there and is not a second bite at the anchor question.
    """
    path = OUT_DIR / f"stage_a_brute_{key}.json"
    if not path.exists():
        return None
    for row in _read(path)["bias_table"]:
        if row.get("resolved"):
            return float(row["level_m"])
    return None


def cmd_epistemic(args: argparse.Namespace) -> dict:
    """Stage D: the epistemic band on the bias ratio, at the anchors.

    **Brute force, not the tilted estimator.** Stage B's pre-registered §1.4
    condition fired: a tilt optimised for the transient region inflates the
    *static* branch's CoV 1.5x at the anchor rising past 100x at saturation, and
    the pre-registration committed in advance that in that case "the estimator is
    reported as unsuitable for the ratio". Since the bias is precisely a ratio
    between the two branches, Stage D runs every arm unweighted at the same
    N = 1e6 the Stage A ground truth uses. That is the fallback §1.1 named, and it
    needs no validation beyond the gates Stage A already passed.
    """
    payload: dict[str, Any] = {
        "stage": "D epistemic band",
        "method": (
            "unweighted brute force at N=1e6 -- the Stage B estimator failed its "
            "pre-registered validation (V2, V4) and inflates the static branch, "
            "which is fatal for a ratio between branches"
        ),
        "n_samples": args.n,
        "sections": {},
    }
    for key in args.sections:
        config, hwl, a2 = load_section(key)
        anchors: list[tuple[str, float]] = [("A1", hwl), ("A2", a2)]
        a3 = lowest_resolved_level(key, args.n)
        if a3 is not None and a3 not in (hwl, a2):
            anchors.append(("A3_lowest_resolved", a3))
        levels = tuple(lv for _, lv in anchors)
        print(
            f"[{key}] Stage D at {', '.join(f'{n}={lv}' for n, lv in anchors)}, "
            f"N={args.n:,} (unweighted) ..."
        )

        # Gate 1: at production N the direct M8 route must reproduce the
        # persisted sweep bit-for-bit, which is what licenses this route at all.
        base_prod = production_branches(config, levels, n_jobs=args.n_jobs)
        persisted = FragilityResult.load(REPO_ROOT / SECTIONS[key]["production_h5"])
        pg = np.asarray(persisted.conditioning_grid, dtype=float)
        j = level_index(pg, a2)
        gate = {
            "level_m": a2,
            "n_samples": int(config.mc.n_samples),
            "static_bit_identical": bool(
                np.array_equal(persisted.failure_matrix_stat[:, j], base_prod[a2][0])
            ),
            "trans_bit_identical": bool(
                np.array_equal(persisted.failure_matrix_tran[:, j], base_prod[a2][1])
            ),
        }
        if not (gate["static_bit_identical"] and gate["trans_bit_identical"]):
            raise SystemExit(
                f"Stage D baseline gate FAILED at {key}: the direct M8 route does "
                "not reproduce the persisted production sweep."
            )
        print(f"  gate 1: bit-identical to the persisted sweep at {a2} m (N=1e5)")

        # Gate 2: the N=1e6 baseline must equal the Stage A ladder's own C0/C4b
        # columns, so the arms are compared against the very ground truth whose
        # gates passed -- not against a differently-drawn population.
        base = production_branches(config, levels, n_samples=args.n, n_jobs=args.n_jobs)
        ladder_path = OUT_DIR / f"ladder_{key}_n{args.n}.h5"
        gate2: dict[str, Any] = {"artifact": str(ladder_path.name)}
        if ladder_path.exists():
            ladder = GapDecompositionResult.load(ladder_path)
            for name, level in anchors:
                i = level_index(ladder.conditioning_grid, level)
                gate2[name] = {
                    "static_bit_identical": bool(
                        np.array_equal(ladder.comparators["C0"][:, i], base[level][0])
                    ),
                    "trans_bit_identical": bool(
                        np.array_equal(ladder.comparators["C4b"][:, i], base[level][1])
                    ),
                }
            if not all(
                v["static_bit_identical"] and v["trans_bit_identical"]
                for k, v in gate2.items()
                if isinstance(v, dict)
            ):
                raise SystemExit(
                    f"Stage D gate 2 FAILED at {key}: the N={args.n} baseline "
                    "differs from the Stage A ladder's own C0/C4b columns."
                )
            print(f"  gate 2: bit-identical to the Stage A N={args.n:,} ladder")
        else:
            gate2["status"] = "skipped_no_ladder_artifact"

        arms_out: list[dict[str, Any]] = []
        for label, bracket, arm_cfg in epistemic_arms(config, key):
            arm = production_branches(
                arm_cfg, levels, n_samples=args.n, n_jobs=args.n_jobs
            )
            entry: dict[str, Any] = {"arm": label, "bracket": bracket, "anchors": {}}
            for name, level in anchors:
                bs, bt = base[level]
                as_, at = arm[level]
                rho = ratio_of_ratios(bs, bt, as_, at, seed=_stable_seed(label))
                entry["anchors"][name] = {
                    "level_m": level,
                    "rho": rho,
                    "p_trans_baseline": float(np.asarray(bt).mean()),
                    "p_trans_arm": float(np.asarray(at).mean()),
                    "p_static_arm": float(np.asarray(as_).mean()),
                    "k_trans_arm": int(np.asarray(at).sum()),
                    "bias_arm": ratio_payload(
                        bias_ratio(level, as_, at, n_replicates=args.bootstrap)
                    ),
                }
            arms_out.append(entry)
            r = entry["anchors"]["A1"]["rho"]
            print(
                f"  {label:<26} A1 rho={r['rho']:.4g} "
                f"[{r['rho_lo']:.4g}, {r['rho_hi']:.4g}] "
                f"resolved={r['resolved']} k_arm="
                f"{entry['anchors']['A1']['k_trans_arm']}"
            )
        payload["sections"][key] = {
            "anchors": {name: lv for name, lv in anchors},
            "baseline_gate_production_n": gate,
            "baseline_gate_ground_truth_n": gate2,
            "baseline_bias": {
                name: ratio_payload(
                    bias_ratio(level, *base[level], n_replicates=args.bootstrap)
                )
                for name, level in anchors
            },
            "arms": arms_out,
        }
        # The m_p control, evaluated at EVERY anchor. It is a statement about the
        # machinery, so it is only informative where the anchor carries enough
        # failing rows to say anything: at an anchor with 2 baseline rows the
        # control is testing counting noise, not the code.
        control = next(a for a in arms_out if a["arm"] == "m_p")
        control_rows = []
        for name, _ in anchors:
            rho_here = control["anchors"][name]["rho"]["rho"]
            passes = bool(
                np.isfinite(rho_here)
                and 1.0 / SMOKE_MP_TOLERANCE <= rho_here <= SMOKE_MP_TOLERANCE
            )
            control_rows.append(
                {
                    "anchor": name,
                    "rho": rho_here,
                    "baseline_k_transient": payload["sections"][key]["baseline_bias"][
                        name
                    ]["k_transient"],
                    "pass": passes,
                }
            )
        payload["sections"][key]["mp_control"] = control_rows
        for row in control_rows:
            print(
                f"  m_p control at {row['anchor']}: rho={row['rho']:.3f} "
                f"(baseline {row['baseline_k_transient']} rows) -> pass={row['pass']}"
            )
        rho_mp = control["anchors"][anchors[0][0]]["rho"]["rho"]
        ok = bool(
            np.isfinite(rho_mp)
            and 1.0 / SMOKE_MP_TOLERANCE <= rho_mp <= SMOKE_MP_TOLERANCE
        )
        payload["sections"][key]["mp_control_pass"] = ok
    # Merge into any existing record rather than replacing it: this command is
    # run per section, and rebuilding the payload from scratch silently dropped
    # the other section's results the first time.
    out_path = OUT_DIR / "stage_d_epistemic.json"
    if out_path.exists():
        merged = _read(out_path)
        merged.setdefault("sections", {}).update(payload["sections"])
        merged.update({k: v for k, v in payload.items() if k != "sections"})
        payload = merged
    _write(out_path, payload)
    return payload


def cmd_anchors(args: argparse.Namespace) -> dict:
    """Criterion F2: is the bias resolvably different at A1 and A2?

    The pre-registered F2 test asks whether the two anchors' 95 % intervals
    overlap. That is the *conservative* form, because it treats the two levels as
    if they were independent estimates -- and they are not: the failure set at
    46.39 m is nested inside the one at 46.50 m on the very same rows, so a
    paired comparison is far sharper. Both are reported here, the pre-registered
    one first, because a paired test that fires where the overlap test does not
    is a finding about the *stage-sensitivity of the bias*, not a licence to
    retro-fit the criterion.

    The paired statistic is the same ratio-of-ratios used everywhere else, with
    "arm" = the A1 column and "baseline" = the A2 column, so rho > 1 means the
    bias is larger at the lower level. Null pinned at rho = 1.
    """
    payload: dict[str, Any] = {"stage": "F2 anchor comparison", "sections": {}}
    for key in args.sections:
        _, hwl, a2 = load_section(key)
        for n in (args.n, 100_000):
            path = OUT_DIR / f"ladder_{key}_n{n}.h5"
            if not path.exists():
                continue
            result = GapDecompositionResult.load(path)
            i1 = level_index(result.conditioning_grid, hwl)
            i2 = level_index(result.conditioning_grid, a2)
            e1 = bias_ratio(
                hwl, result.comparators["C0"][:, i1], result.comparators["C4b"][:, i1]
            )
            e2 = bias_ratio(
                a2, result.comparators["C0"][:, i2], result.comparators["C4b"][:, i2]
            )
            paired = ratio_of_ratios(
                result.comparators["C0"][:, i2],
                result.comparators["C4b"][:, i2],
                result.comparators["C0"][:, i1],
                result.comparators["C4b"][:, i1],
                seed=_stable_seed(f"{key}-anchors"),
            )
            entry = {
                "n_samples": result.n_samples,
                "A1": ratio_payload(e1),
                "A2": ratio_payload(e2),
                "F2_intervals_overlap": intervals_overlap(
                    (e1.ci_lo, e1.ci_hi), (e2.ci_lo, e2.ci_hi)
                ),
                "F2_paired_rho_A1_over_A2": paired,
                "stage_separation_m": round(a2 - hwl, 4),
            }
            payload["sections"].setdefault(key, {})[f"n{result.n_samples}"] = entry
            print(
                f"[{key}] N={result.n_samples:,}: A1 B={e1.ratio:.1f} "
                f"[{e1.ci_lo:.1f},{e1.ci_hi:.1f}] (k={e1.k_transient})  "
                f"A2 B={e2.ratio:.1f} [{e2.ci_lo:.1f},{e2.ci_hi:.1f}] "
                f"(k={e2.k_transient})"
            )
            print(
                f"    F2 overlap={entry['F2_intervals_overlap']}  "
                f"paired rho={paired['rho']:.3f} "
                f"[{paired['rho_lo']:.3f},{paired['rho_hi']:.3f}] "
                f"resolved={paired['resolved']}"
            )
    _write(OUT_DIR / "stage_a_anchors.json", payload)
    return payload


def cmd_report(args: argparse.Namespace) -> dict:
    """Assemble the evidence JSON from every stage artifact on disk."""
    payload: dict[str, Any] = {
        "study": "design-HWL static-vs-transient bias resolution",
        "companion_note": "docs/decisions/adr0040-hwl-bias-resolution.md",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "preregistered_criteria": {
            "R1_min_transient_rows": R1_MIN_ROWS,
            "R2_max_ci_width_factor": R2_MAX_WIDTH,
            "V3_tolerance": V3_TOLERANCE,
            "V3_min_rows": V3_MIN_ROWS,
            "V4_min_n_eff": V4_MIN_NEFF,
            "V4_cov_factor": V4_COV_FACTOR,
            "F3_epistemic_factor": F3_EPISTEMIC_FACTOR,
            "mp_control_tolerance": SMOKE_MP_TOLERANCE,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        },
        "stages": {},
    }
    for name, filename in (
        ("A_verify", "stage_a_verify.json"),
        ("A_pilot", "stage_a_pilot.json"),
        ("A_brute_kp62_0", "stage_a_brute_kp62_0.json"),
        ("A_brute_kp57_4", "stage_a_brute_kp57_4.json"),
        ("A_anchors_F2", "stage_a_anchors.json"),
        ("B_tilt_kp62_0", "stage_b_tilt_kp62_0.json"),
        # No C_kp57_4 tilted record: the Stage B estimator failed its
        # pre-registered validation, so KP 57.4 was done by brute force
        # (A_brute_kp57_4 above) rather than with the estimator.
        ("D_epistemic", "stage_d_epistemic.json"),
    ):
        path = OUT_DIR / filename
        if path.exists():
            payload["stages"][name] = _read(path)
    _write(EVIDENCE, payload)
    return payload


COMMANDS: dict[str, Callable[[argparse.Namespace], dict]] = {
    "verify": cmd_verify,
    "pilot": cmd_pilot,
    "brute": cmd_brute,
    "tilt": cmd_tilt,
    "kp57": cmd_kp57,
    "epistemic": cmd_epistemic,
    "anchors": cmd_anchors,
    "report": cmd_report,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--sections", nargs="+", default=["kp62_0"])
    parser.add_argument("--n", type=int, default=200_000)
    parser.add_argument("--n-truth", type=int, default=1_000_000)
    parser.add_argument("--n-pilot", type=int, default=20_000)
    parser.add_argument("--n-jobs", type=int, default=6)
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_REPLICATES)
    args = parser.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    COMMANDS[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
