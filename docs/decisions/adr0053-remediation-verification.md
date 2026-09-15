# ADR-0053 verification and current-evidence reconciliation

Date: 2026-09-15

## Verdicts

The record/interval mismatch, inconsistent rejection of non-finite observations,
and accepted-but-unimplemented public lag activation were independently confirmed
against engine 782086650d82481e20fd8aaf17faa43caf40c0d6. The constant-rate
relationship and two distinct time interfaces were derived before consulting
any external probe implementation. The repair retains the interval kernel and
both driving heads; no prior, physical coefficient or production sensitivity
setting changes.

The gauge prerequisite was partly resolved before this work. Later commits had
already rebuilt the production posteriors and annual system outputs using the
adopted KP56.73 station. The primary workbook independently supports that node;
its first-row rating-coefficient attribution required correction. Four older
datum posteriors and three companion calculations still required refresh.

## Discriminating verification

`tests/test_time_contract.py` checks an independently calculated constant rate,
active terminal loading, inactive endpoints, zero-span records, initial and
final states, threshold timing, nonzero time origins, refinement, terminal
initiation without extra progression, and invalid record/duck inputs. Both
NumPy and Numba public batch paths and the GSA adapter are covered. Existing
one-step tests now supply two instantaneous observations, retaining their
analytic expectations. No tolerance was broadened and no failure assertion was
removed to retain a known error.

The companion JSON records exact input/output hashes and the endpoint proof for
149 persisted configuration arms (4432 conditioning records). All terminal
loads are below the toe, and all inspected sample inputs are finite and positive.
The tilted arm is explicitly distinguished from regenerated prior samples.
For the two GSA studies, exact recorded configuration hashes were recovered
from Git revision 481063b2ca550625ec52db11250e12a172ad70c4. The later configuration
difference adds only a disabled length-effect block. Every recorded GSA level
and the stress figure's actual flashiest-member levels have inert endpoints.
These statements justify retaining outputs; they do not label them as new runs.

All eight production 2016 replays were evaluated again at N=100000. Every row's
static/transient margin, final length, onset time, response factor and failure
flags equals the persisted result exactly. Selected actual completing
trajectories verify the corrected clock. Eight strata of the exact 64-day
2011 sustained hold reproduce the earlier rejection counts: 908 at KP60.0
matrix, of which 326 are additional to the current 2016 rejection, zero
elsewhere. The separate one-extra-step check in the evidence JSON quantifies
per-row terminal-state changes. This does not resolve ADR-0040's distinct
Euler barrier-crossing caveat or strengthen the interpretation of a numerical
sustained hold into a general physical theorem.

## Corrected products and invariant consumers

- Eighty current posteriors receive an explicitly labelled derived clock
  correction: 23854 finite breach times move to the completing interval end
  (+225 seconds for these zero-origin records). Original files and metadata
  remain archived. Every other HDF5 dataset is value-identical; sample identity,
  acceptance masks, posterior curves and uncertainty products are preserved.
  No new physical replay is claimed for these derived copies.
- Four optional KP57.4/KP62.0 datum posteriors are genuinely replayed under
  KP56.73. Their original gauge-56.6 files are retained in the archive.
- The C_e-prior companion is rerun for five candidates at two sections, using
  its existing NumPy baseline check and Numba candidate path. Field-prior
  rejection now agrees with production, 5.512% at KP58.8 and 3.244% at KP60.0.
  Marginal-transient rejection remains zero for all ten candidate/section arms.
- The retained-sample L diagnostics are recomputed from those current masks.
  L mean shifts are +1.339%/+0.519%; CoV shifts are -3.566%/-1.617% at
  KP58.8/KP60.0. The separate interpretive question about a sensitivity-based
  updating ceiling is not adjudicated by this numerical refresh.
- The foreshore 2016 event calculation is rebuilt. Mobilising durations are
  42/67/21/16 hours at KP57.4/58.8/60.0/62.0; critical retreat rates are
  4.762/4.851/28.571/2.750 m/h. Design-level and canonical-grid calculations
  and the entire ensemble climate arm remain identical. The assumed retreat
  law and its interpretation are unchanged.
- Yabe and Gounokawa field reruns retain their scientific payloads. Shikaga's
  field result also stays unchanged; three ancillary Tokachi KP62 diagnostics
  are refreshed from the old 47 m path to the already adopted 40 m path.
- Corrected trajectories regenerate the stress figure and the local B25/S2
  diagnostics. The two gauge-dependent companion figures and foreshore figure
  are regenerated from their current numerical inputs. All were inspected
  before and after; composition and styling are retained.

Annual system integration consumes the invariant acceptance and fragility arrays,
not breach clocks. Its existing gauge-refreshed files are retained with their
original provenance and hashes. Canonical/sustained gap comparisons preserve
exactly their intended interval loads by adding the initial observation node.
Exposure sample-count statistics retain their documented uniform-bin convention;
they are not progression trajectories. These dependencies, their concrete
artifacts and hashes are listed in `adr0053-time-contract-evidence.json`.

## Thesis reconciliation and limits

Chapter 4 states the sample/interval convention and describes the lag screen
without implying a routed lag solver. Appendix J documents validation, public
instantaneous evaluation and state timing; Appendix K records ADR-0053.
Chapter 5's stress caption identifies interval-end states. Chapter 6 and
Appendix I receive the derived gauge-dependent numerical corrections, and the
three affected thesis figures are synchronized. Labels, citation keys and
unaffected scientific statements are preserved. The Summary, Discussion and
Conclusions were searched for dependent numerical/contract echoes.

A concurrent thesis commit 7d34f421fd45cfedadaeef54b4b5acfcb9caeb1c included
these two Chapter 4 edits alongside unrelated citation work. Their exact text
was verified after fetching; no unrelated changes are republished here.
No thesis compilation was performed for this ordinary session. Final-session
pagination and the later assigned scientific interpretations remain pending.

## Final validation

Windows Python 3.11: 991 tests passed (136.08 s), with 8 reviewed bootstrap
degeneracy warnings from deliberately small test grids. Ruff and Black pass.
Black reports optional notebook support unavailable; the current CI Python
source gate is unchanged. Thesis source checks report no dangling labels,
undefined citations, em dashes or Japanese script outside the bibliography.
