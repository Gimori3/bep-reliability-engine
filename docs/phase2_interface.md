# Phase 2 Interface: Loading Phase 1 Fragility Output and Replaying M8 on the 2016 Hydrograph

Status: drafted 2026-06-18, against the completed M8 (`evaluator.py`) and M9
(`fragility.py`); updated 2026-07-03 for the built M3 (`hydrographs.py`,
ADR-0019/0020), the built run driver (`run.py`), the datum-anchored fragility
fits (`LognormFragility.datum_m`), and the ADR-0022 Phase 2 replay timestep.
Companion to the authoritative spec `docs/architecture.md` (§2, §8). This
document is the operational contract for Phase 2 Bayesian filtering: how to
load a Phase 1 `FragilityResult` from disk, reconstruct the two extra inputs
Phase 1 does *not* persist (the 2016 hydrograph and the cross-section
geometry), call `evaluate_realization` row-by-row against the 2016 event, and
assemble the Accept–Reject posterior and the survival-discrimination
decomposition.

It documents the code as built; it does not introduce new decisions.

---

## 0. What Phase 2 does, in one paragraph

Phase 1 produces, per cross-section per scenario, a prior sample matrix `theta`
(N×7) and a fitted static/transient fragility-curve pair, persisted to one HDF5
file plus a JSON metadata sidecar. Phase 2 **re-runs the exact Phase 1 transient
evaluator** (`evaluate_realization`, M8) on every prior row against the
deterministic 2016 typhoon hydrograph `h_2016(t)`, rejects the rows that fail
(`Z_transient ≤ 0`), and keeps the survivors as the posterior sample. Because
M8 also returns `Z_static`, the same pass yields a second rejection set under
`h_2016`, and the *additional* rejection produced by the transient criterion
beyond the static one is the marginal informativeness of 2016 survival for the
time-dependent mechanism (spec §8).

The scientific point (spec §8): rows rejected by the static criterion would have
failed even at peak head, so their rejection reflects geometry / material
resistance / sub-critical loading, not any time constraint. Only the *extra*
transient rejection genuinely constrains progression.

---

## 1. What Phase 1 hands off

`bep_reliability_engine.fragility.FragilityResult` is the handoff object (spec
§2). It is persisted by `FragilityResult.save(path)` as **two files**:

- `path` (e.g. `results/tokachi_kp58_historical.h5`) — the HDF5 arrays.
- `path` with a `.json` suffix (e.g. `results/tokachi_kp58_historical.json`) —
  the metadata sidecar. It must sit next to the `.h5`; `load` reads both.

### 1.1 On-disk HDF5 schema (spec §8)

```
/theta_matrix             (N, 7)    float64    # the prior rows to filter
/param_names              (7,)      string     # canonical column identities
/conditioning_grid        (N_h,)    float64    # Phase 1 fragility grid h_i
/P_f_static_raw           (N_h,)    float64    # MC point estimates on the grid
/P_f_trans_raw            (N_h,)    float64
/failure_matrix_static    (N, N_h)  bool       # Phase 1 grid outcomes (static)
/failure_matrix_trans     (N, N_h)  bool       # Phase 1 grid outcomes (transient)
/bootstrap_bands/static_lo (N_h,)   float64
/bootstrap_bands/static_hi (N_h,)   float64
/bootstrap_bands/trans_lo  (N_h,)   float64
/bootstrap_bands/trans_hi  (N_h,)   float64
/binomial_ci/static_lo     (N_h,)   float64    # ADR-0024 Clopper-Pearson CIs
/binomial_ci/static_hi     (N_h,)   float64    #   on the raw points (always on)
/binomial_ci/trans_lo      (N_h,)   float64
/binomial_ci/trans_hi      (N_h,)   float64
/attrs: fit_static_mu, fit_static_sigma, fit_static_datum_m,
        fit_trans_mu, fit_trans_sigma, fit_trans_datum_m
        # NaN mu/sigma encode an ADR-0024 None fit (branch carried by its
        # raw points + binomial CIs; see metadata['fragility_deliverable'])
```

Per ADR-0024 the fits are Optional: `P_f_static_fit` / `P_f_trans_fit` are
`None` where a branch's point set could not be fit (fewer than two interior
levels), and `metadata['fragility_deliverable']` records per branch whether
the deliverable is the fitted lognormal or the raw tail points with their
binomial CIs (`form`, `transition_bracketed`, `max_p_f_raw`, `fit_role`).
Phase 2 filtering is unaffected either way — it consumes the theta matrix and
the M8 evaluator, never the fitted curves. Legacy files (no `binomial_ci`
group) load with the CIs recomputed exactly from the retained matrices.

The fitted curves are lognormal in the load excess `h − datum_m` with
`datum_m = z_toe` (datum-anchored fit, 2026-07-03); files written before the
datum existed load with the backward-compatible `datum_m = 0`. A transient
`<output>.raw.h5` + `.raw.json` pair may exist next to a *crashed* run — it is
the pre-fit recovery payload (raw arrays only, same dataset names), not a
handoff artifact.

**Dataset-naming note (important).** The on-disk failure-matrix datasets use the
spec §8 schema names `failure_matrix_static` / `failure_matrix_trans`, but the
in-memory `FragilityResult` *fields* use the spec §2 names `failure_matrix_stat`
/ `failure_matrix_tran`. The spec is itself inconsistent between §2 and §8;
`save`/`load` map between the two. **Phase 2 should use the loaded object's
fields and never touch the raw HDF5 keys** — then the naming difference is
invisible.

The metadata block (provenance, config snapshot, stratification labels) lives in
the JSON sidecar, not the HDF5 attrs; the HDF5 attrs carry only the fitted
`(μ, σ)`. This is the spec §2/§8 "HDF5 for arrays + JSON sidecar for metadata"
split (HDF5 attrs cannot hold `None` such as `tau_aq`, or nested dicts such as
the config snapshot).

### 1.2 In-memory `FragilityResult` fields Phase 2 reads

| Field | Type | Phase 2 use |
|---|---|---|
| `theta_matrix` | `ndarray (N, 7)` | **the rows to filter** |
| `param_names` | `list[str]` | column identities (canonical order below) |
| `metadata` | `dict` | config snapshot (→ geometry) + stratification labels |
| `failure_matrix_stat` | `ndarray (N, N_h) bool` | Phase 1 **grid** outcomes; *not* the 2016 outcomes (see §1.3) |
| `failure_matrix_tran` | `ndarray (N, N_h) bool` | Phase 1 **grid** outcomes |
| `conditioning_grid`, `P_f_*_raw`, `P_f_*_fit`, `bootstrap_bands` | — | Phase 1 fragility curves; not needed for filtering |

Canonical column order (the M2 contract; `param_names` will equal this):

```python
["k_aq", "d_70", "D_aq", "D_bl", "k_bl", "gamma_bl_sub", "C_e"]
```

### 1.3 What is *not* in the file (and must be supplied by Phase 2)

Per spec §8 the deterministic **2016 hydrograph is a separate input** and is not
part of `FragilityResult`. Two things Phase 2 must supply:

1. The 2016 hydrograph record `h_2016` (§3.1).
2. The cross-section **geometry** dict used in Phase 1, reconstructed from the
   embedded config snapshot (§3.2).

Note the retained `failure_matrix_stat` / `failure_matrix_tran` are the outcomes
on the Phase 1 **conditioning grid** `{h_i}`, not under `h_2016`. Phase 2
computes fresh `h_2016` outcomes by calling M8; the retained matrices support
diagnostics and the §8 decomposition stratification, not the filtering itself.

### 1.4 Loading

```python
from bep_reliability_engine.fragility import FragilityResult

result = FragilityResult.load("results/tokachi_kp58_historical.h5")
theta       = result.theta_matrix          # (N, 7) float64
param_names = result.param_names           # canonical order
meta        = result.metadata              # dict from the JSON sidecar
```

---

## 2. The M8 evaluator Phase 2 calls

Phase 2 imports the **same** function Phase 1 used — no physics is
reimplemented (spec §8, §9; ADR-0011). The signature and `EvaluationResult`
field set are a frozen contract.

```python
from bep_reliability_engine.evaluator import evaluate_realization, EvaluationResult

# evaluate_realization(
#     theta_row: ndarray (7,),     # one prior row, canonical column order, SI
#     hydrograph,                  # record with .h, .peak, .native_dt (§3.1)
#     geometry: dict,              # flat keys L, z_toe, foreshore_width,
#                                  #   D_fore, k_fore (§3.2)
#     l_ini: float = 0.0,          # initial pipe length; 0 for the 2016 replay
#     store_trajectory: bool = False,
# ) -> EvaluationResult
```

`EvaluationResult` fields Phase 2 uses (full set in `evaluator.py`):

| Field | Meaning |
|---|---|
| `Z_transient` | `L - l_e_final` [m]; **failure ⇔ `Z_transient ≤ 0`** |
| `Z_static` | `H_c - r_e·(h_peak - z_toe)` [m]; failure ⇔ `Z_static ≤ 0` |
| `failure_trans`, `failure_static` | the `Z ≤ 0` flags, precomputed |
| `l_e_final` | final pipe length [m] |
| `H_c`, `l_c`, `lambda_in`, `r_e`, `t_uh` | diagnostics (spec §2) |
| `uplift_occurred`, `heave_occurred` | per-event latches |
| `l_trajectory` | `None` unless `store_trajectory=True` |

**Failure-sign convention (ADR-0008):** failure is `Z ≤ 0` (the boundary `Z = 0`
counts as failure). Survival is therefore the strict `Z > 0`. `failure_trans`
and `failure_static` already encode this; prefer them over re-deriving signs.

**`C_e` enters only the transient branch (ADR-0001).** `Z_static` is independent
of `C_e`, so Phase 2 filtering tightens `C_e` only through the transient
criterion — which is the whole point (spec §4, §8).

**`l_ini = 0` for the 2016 replay (spec §5):** the 2016 event is the calibration
event itself; no pre-existing pipe.

---

## 3. The two inputs Phase 2 must reconstruct

### 3.1 The 2016 hydrograph record

M8 consumes a hydrograph by **duck typing** on exactly three fields (ADR-0010).
M3 `hydrographs.py` is built (ADR-0019): the preferred construction is
`build_hydrograph_record` — feed it the 2016 observed discharge (or a stage
series via a direct `HydrographRecord`) and it handles the hours→seconds
conversion, the Eq. 4.19 rating at the section's KP, and `peak`/`native_dt`
derivation, all on the m MSL datum. A structural stand-in (as parts of
`tests/test_evaluator.py` use) remains valid. All quantities strict SI:

- `h` — river stage series, `ndarray (T,)`, **metres above the common datum**
  (m MSL for M3-built records), uniformly sampled at `native_dt`.
- `peak` — scalar static comparator level `h_peak` [m above datum]; authoritative
  (M8 uses `record.peak`, not `max(h)`). For a real event `peak = max(h)`.
- `native_dt` — the authoritative integration timestep `dt_s` **in seconds**
  (M8 uses this directly, not `diff(t)`).

```python
from bep_reliability_engine.hydrographs import build_hydrograph_record

# Preferred: through M3, from the observed 2016 discharge at the section's KP
# rating (a_kp, b_kp from load_rating_coefficients). Stage lands in m MSL.
h_2016 = build_hydrograph_record(
    time_hours, q_2016_m3s, a_kp=a_kp, b_kp=b_kp,
    scenario="historical", event_id="typhoon_2016",
)
```

**Replay timestep (ADR-0022):** Phase 1 fragility integrates at the native
hourly resolution (3600 s), but the Phase 2 per-realization replay runs at
**native/2 = 1800 s** — per-row `l_e` accuracy governs the Accept–Reject
filter, and at 3600 s individual realizations near the breach boundary carry
up to tens of percent of `l_e` sensitivity. Resample `h` onto the 1800 s grid
(linear interpolation) and set `native_dt = 1800.0` on the record before the
replay.

Datum and units are load-bearing: `h` and `z_toe` must share the vertical datum
(`z_toe ≡ h_e` in Pol SIE 2024 Eqs. 6/8, ADR-0007; the generated configs carry
the ADR-0021 toe elevations in m MSL), `native_dt` is seconds, and all heads
are metres.

### 3.2 The geometry dict (must equal Phase 1's exactly)

M8 unpacks a flat geometry dict with exactly these keys (ADR-0010), strict SI:

```
L                # seepage length [m]
z_toe            # polder exit-point elevation [m above datum] (= h_e)
foreshore_width  # B_f [m]
D_fore           # foreshore blanket thickness [m]
k_fore           # foreshore blanket vertical conductivity [m/s]
```

Phase 2 must replay under the **identical** geometry Phase 1 used, so that
filtering re-runs under identical assumptions (spec §8 point 4). Reconstruct it
from the config snapshot embedded in `metadata`. The run driver is expected to
embed `Config.to_metadata()` (M1) under `metadata["config"]`, whose
`geometry` block already has exactly these five keys:

```python
geometry = dict(result.metadata["config"]["geometry"])
# or, to re-validate via M1:
# from bep_reliability_engine.config import Geometry
# geometry = Geometry(**result.metadata["config"]["geometry"]).as_evaluator_dict()
```

> Provenance note: the run driver (`run.py`, built) embeds the full
> `Config.to_metadata()` under `metadata["config"]`, so geometry (and the
> priors, seed, scenario) are recoverable exactly as shown above. Phase 2
> should still assert the five keys are present rather than trusting the
> layout blindly.

---

## 4. Accept–Reject filtering against `h_2016`

The procedure of spec §8: evaluate every prior row once, keep `Z_transient > 0`.

```python
import numpy as np
from bep_reliability_engine.evaluator import evaluate_realization

N = theta.shape[0]
results = [
    evaluate_realization(theta[j], h_2016, geometry, l_ini=0.0)
    for j in range(N)
]

# Survival is the strict complement of failure (Z <= 0 is failure, ADR-0008).
survive_trans  = np.array([not r.failure_trans  for r in results])
survive_static = np.array([not r.failure_static for r in results])

theta_posterior = theta[survive_trans]      # the Phase 2 posterior sample
```

`theta_posterior` is the posterior prior-sample (the rows that survive the 2016
transient criterion). Phase 2 Bayesian analysis proceeds from here (e.g.
prior-vs-posterior marginals for all seven parameters, with `C_e` called out per
spec §12 failure mode 7).

Notes:
- The loop is pure and deterministic: same `theta`, `h_2016`, `geometry` →
  identical result, every time.
- Only `Z_transient` (and `Z_static` for §5) are needed; leave
  `store_trajectory=False` (default) unless tracing a subset — full trajectories
  are ~800 MB at N=1e5 (spec §12 failure mode 6). For a visualization subset or a
  breach-timing study, enable it on a few hundred rows.
- Performance: the transient branch is O(T) per row (the static branch is O(1)).
  The N rows are independent and embarrassingly parallel — `joblib.Parallel`
  over chunks of rows mirrors the Phase 1 outer-loop strategy (spec §6).

---

## 5. Survival-discrimination decomposition

Because M8 returns both margins under `h_2016`, the single pass yields two
rejection sets. Cross-tabulate them (the rigorous artifact); the static and
transient failure sets are **not** strictly nested (the branches use different
driving heads — gross peak head for static vs the `0.3·D_bl`-reduced,
time-integrated head for transient, spec §3/§4), so report the full 2×2.

```python
# Boolean masks over the N prior rows, under h_2016.
reject_static = ~survive_static
reject_trans  = ~survive_trans

both_survive   = survive_static & survive_trans
static_only    = reject_static  & survive_trans     # fails static, survives transient
transient_only = survive_static & reject_trans       # survives static, FAILS transient
both_reject    = reject_static  & reject_trans

# Headline fractions.
f_static_reject = reject_static.mean()
f_trans_reject  = reject_trans.mean()

# Marginal informativeness of 2016 survival for the TIME-DEPENDENT mechanism:
# the additional rejection produced by the transient criterion beyond static,
# i.e. rows that pass at peak head but fail the progression ODE over time.
f_marginal_transient = transient_only.mean()
```

`transient_only` is the set whose rejection is attributable to the time-dependent
mechanism alone — rows that would survive a conventional static check at peak
head but do not survive the transient progression over the full `h_2016`. Its
fraction `f_marginal_transient` is the answer to the survival-discrimination
question (spec §8): whether 2016 survival genuinely constrains progression, or is
already explained by simpler (static) physics.

### 5.1 Stratification by remediation_state and d70_interpretation

The decomposition is reported **within the remediation state and grain-size
interpretation of each segment** (spec §8). The key structural fact: these
labels are **scalar metadata on the whole run**, not per-row fields — one
`FragilityResult` file *is* one stratum. They are written once by Phase 1 and
read back from the sidecar:

```python
remediation_state  = result.metadata["remediation_state"]   # §8 stratifier, e.g. 'none'
d70_interpretation = result.metadata["d70_interpretation"]  # 'matrix' | 'bulk' (spec §7/§13)
segment_id         = result.metadata["segment_id"]          # 200 m grid (tradeoff 3)
scenario           = result.metadata["scenario"]            # use the 'historical' run for 2016
```

So stratifying does **not** mean masking rows inside one file; it means computing
the §5 decomposition **once per file** and tabulating the headline fractions
across the set of Phase 1 outputs, keyed by `(remediation_state,
d70_interpretation)` (and `segment_id`). Because both grain-size interpretations
are carried as **primary** runs (spec §7, §13), every segment contributes a
`matrix` row and a `bulk` row; reporting them side by side is what exposes the
fragility curves' dependence on the grain-size definition.

```python
import numpy as np
from bep_reliability_engine.fragility import FragilityResult
from bep_reliability_engine.evaluator import evaluate_realization

def decompose_one(h5_path, h_2016):
    """Run the §5 decomposition for a single Phase 1 file (one stratum)."""
    result   = FragilityResult.load(h5_path)
    theta    = result.theta_matrix
    geometry = dict(result.metadata["config"]["geometry"])
    res = [evaluate_realization(theta[j], h_2016, geometry, l_ini=0.0)
           for j in range(theta.shape[0])]
    survive_static = np.array([not r.failure_static for r in res])
    survive_trans  = np.array([not r.failure_trans  for r in res])
    return {
        "segment_id":         result.metadata["segment_id"],
        "remediation_state":  result.metadata["remediation_state"],
        "d70_interpretation": result.metadata["d70_interpretation"],
        "scenario":           result.metadata["scenario"],
        "f_static_reject":    float((~survive_static).mean()),
        "f_trans_reject":     float((~survive_trans).mean()),
        # marginal transient informativeness: survives static, fails transient
        "f_marginal_transient": float((survive_static & ~survive_trans).mean()),
    }

# One row per Phase 1 output file; group/pivot by the stratifiers downstream
# (e.g. pandas.DataFrame(rows).pivot_table(index=["segment_id", "remediation_state"],
#  columns="d70_interpretation", values="f_marginal_transient")).
rows = [decompose_one(p, h_2016) for p in historical_h5_paths]
```

Use the **historical** scenario file for the 2016 event throughout (the `+4K`
runs are for the climate-projection fragility, not the 2016 replay).

---

## 6. End-to-end minimal example

```python
import numpy as np
from types import SimpleNamespace
from bep_reliability_engine.fragility import FragilityResult
from bep_reliability_engine.evaluator import evaluate_realization

# 1. Load Phase 1 output (HDF5 + JSON sidecar).
result      = FragilityResult.load("results/tokachi_kp58_historical.h5")
theta       = result.theta_matrix
geometry    = dict(result.metadata["config"]["geometry"])
assert {"L", "z_toe", "foreshore_width", "D_fore", "k_fore"} <= geometry.keys()

# 2. Build the 2016 record (SI: metres above the z_toe datum, dt in seconds).
#    ADR-0022: the Phase 2 replay runs at native/2 = 1800 s — resample the
#    hourly series onto the 1800 s grid first (see §3.1).
h2016 = np.asarray(load_h2016_series_1800s_m(), dtype=np.float64)  # project-specific
h_2016 = SimpleNamespace(h=h2016, native_dt=1800.0, peak=float(h2016.max()))

# 3. Replay M8 on every prior row.
res = [evaluate_realization(theta[j], h_2016, geometry, l_ini=0.0)
       for j in range(theta.shape[0])]
survive_trans  = np.array([not r.failure_trans  for r in res])
survive_static = np.array([not r.failure_static for r in res])

# 4. Posterior + survival-discrimination headline.
theta_posterior = theta[survive_trans]
f_static_reject = (~survive_static).mean()
f_trans_reject  = (~survive_trans).mean()
f_marginal      = (survive_static & ~survive_trans).mean()
print(theta_posterior.shape, f_static_reject, f_trans_reject, f_marginal)
```

---

## 7. Checklist and gotchas

- [ ] Use the **historical** scenario file for the 2016 replay.
- [ ] `h_2016.h` and `geometry["z_toe"]` share the vertical datum; both in metres.
- [ ] `native_dt` is **seconds**, at the ADR-0022 replay resolution
      (native/2 = 1800 s for the per-realization 2016 replay).
- [ ] `geometry` is the **identical** Phase 1 geometry (from the config snapshot),
      not a hand-entered copy.
- [ ] `l_ini = 0.0` (spec §5).
- [ ] Survival is `not failure_*` (strict `Z > 0`); failure is `Z ≤ 0` (ADR-0008).
- [ ] Read `FragilityResult` **fields** (`failure_matrix_stat`/`tran`), not raw
      HDF5 keys (`failure_matrix_static`/`trans`) — `load` handles the mapping.
- [ ] Keep `store_trajectory=False` for the full sweep; enable only on a subset.
- [ ] Do not reimplement physics — import `evaluate_realization` (spec §8, §9).

---

## 8. References

- `docs/architecture.md` §2 (FragilityResult and M8 I/O contracts), §4 (shared
  preamble then branch; C_e in transient only), §5 (l_ini, memory model), §6
  (parallelism), §8 (Phase 2 handoff, Accept–Reject, survival-discrimination
  decomposition, HDF5 schema, JSON sidecar), §11 (timestep convergence), §12
  (failure modes 6, 7), §13.
- ADR-0001 (C_e stochastic; static branch has no C_e exposure), ADR-0002
  (shared-sample contract), ADR-0007 (`z_toe ≡ h_e` datum, r_e-translated head),
  ADR-0008 (`Z ≤ 0` failure convention), ADR-0010 (HydrographRecord and geometry
  dict schemas), ADR-0011 (M8 orchestration contract / frozen import surface),
  ADR-0019 (M3 data facts and Eq. 4.19), ADR-0021 (MSL toe elevations),
  ADR-0022 (Phase 1 native 3600 s acceptance; Phase 2 replay at 1800 s).
- Code: `bep_reliability_engine/evaluator.py` (M8 `evaluate_realization`,
  `EvaluationResult`), `bep_reliability_engine/fragility.py` (M9
  `FragilityResult.load`/`save`).
```
