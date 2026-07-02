# ADR-0018: HWL sourced from the 2019 design bank-height data (MSL datum, strict per-KP lookup)

Date: 2026-07-02

## Status
Accepted

---

## Context

Spec §1 lists HWL among the M1 cross-section geometry inputs ("L, foreshore width, HWL, z_toe"), but it was never implemented: the built `Geometry` model carried only the five ADR-0010 evaluator keys, and no HWL value existed anywhere in the configuration layer. The geotech source of truth (`data/processed/tokachi_bep_inputs.csv`) has no HWL column; the provenance document (§3.7) discusses HWL only as an audit-trail quantity, noting the erroneous KP 63.4 appendix carry-over (46.68 m) and its resolution (~49.0 m).

The official 2019 design bank-height tables (`data/raw/geometry/BankHeight_TokachiRiv_2019.csv`, `BankHeight_SatsunaiRiv_2019.csv`; columns `River, KP, HWL, DesignBankHeight_L, DesignBankHeight_R` at 0.2 km KP spacing) provide HWL on the MSL datum — the same vertical datum as the M3 stage hydrographs (rating-curve output). Consistency of datum between HWL and the stage series is what makes this the correct source for the seepage engine. The two `DesignBankHeight_*` columns are levee crest elevations that belong to the Phase 3 overflow mechanism, not to Phase 1 BEP.

The study-section KPs (57.4, 58.8, 60.0, 62.0, plus the excluded 63.4) all fall exactly on the 0.2 km grid. The 2019 file's KP 63.4 value (48.80 m) independently corroborates the provenance §3.7 resolution (~49.0 m, not 46.68 m).

---

## Decision

1. `Geometry` gains a **required** field `HWL: float` (strictly positive, finite), the design high-water level in **metres above MSL**, sourced from the official 2019 bank-height data.
2. A thin standalone loader, `bep_reliability_engine.bank_heights.load_hwl(river, kp, *, data_dir)`, reads the relevant river's 2019 CSV, selects the row matching the requested KP, validates the HWL cell (present, numeric, finite, positive), and returns the float. `scripts/generate_configs.py` calls it once per cross-section; the pydantic model carries no I/O.
3. KP matching is **strict**: the requested KP must coincide with a 0.2 km grid point within a tiny float tolerance (1e-6 km). An off-grid KP raises a `ValueError` naming the two nearest available KPs. No nearest-match, no interpolation.
4. The `DesignBankHeight_L/R` columns are never parsed or returned — the loader is the firewall keeping Phase 3 crest data out of M1.
5. `Geometry.as_evaluator_dict()` continues to emit **exactly** the five ADR-0010 keys (`L, z_toe, foreshore_width, D_fore, k_fore`); HWL is config-carried but excluded from the frozen M8 contract, which has no HWL consumer.

---

## Alternatives Considered

### Nearest-match or linear interpolation for off-grid KPs
Pros: tolerant of study sections that fall between grid points. Cons: silently masks a typo'd KP (the failure mode that matters most for a hand-entered kilometre-post); all current study KPs are exact grid points, so tolerance buys nothing today. Rejected; strict match can be relaxed later behind an explicit decision if an off-grid section ever appears.

### Housing the lookup in `config.py` (module-level function or model validator)
Pros: one fewer file. Cons: M1 is specified as a pure data object; baking CSV I/O into the config module (or worse, the pydantic model) couples validation to the filesystem and makes the model unusable without the data tree. Rejected in favour of a separate thin module.

### Making HWL optional (default `None`)
Pros: no breakage of existing configs/fixtures. Cons: a silently absent HWL defeats the purpose of sourcing it officially; configs are generated, so regeneration is cheap. Rejected.

### Adding an HWL column to the geotech CSV
Pros: single input table. Cons: duplicates an official published dataset into a hand-maintained file, creating a second source of truth that can drift; the provenance doc explicitly keeps HWL out of that CSV. Rejected — the 2019 files are read directly.

---

## Rationale

The HWL value that conditions the seepage analysis must live on the same vertical datum as the stage hydrographs it will be compared against (M3, rating-curve output, MSL). The 2019 design bank-height tables are the official source for that quantity; reading them directly, per river and per KP, removes any transcription step. Strictness in the KP match converts the likeliest input error (a wrong kilometre-post) into a loud failure that names the neighbouring grid points. Excluding HWL from the evaluator dict preserves the ADR-0010 M8 contract bit-for-bit — no engine module changes, and `run.py`/Phase 2 behaviour is untouched.

---

## Consequences

- All 16 generated configs now carry `geometry.HWL` (57.4 → 39.21, 58.8 → 41.03, 60.0 → 42.75, 62.0 → 46.39 m MSL); configs are regenerated, not hand-edited, per standing policy.
- `tests/test_configs.py` (drift guard) additionally pins each config's HWL against an independent re-read of the 2019 CSV, so a drifted config, loader, or bank-height file fails CI.
- `tests/test_config.py` locks the loader behaviour: known-KP value (Tokachi KP 56.6 = 38.14 m), river-file selection, strict off-grid rejection, and clear errors for empty/non-numeric/non-positive HWL cells.
- **Datum caveat**: `z_toe` remains a PROVISIONAL 0.0 in generated configs. HWL (m MSL) and z_toe are not directly comparable until z_toe carries its true MSL elevation; the `Geometry.HWL` docstring states this explicitly. Resolving z_toe is a separate, pending schematization task.
- The engine has no HWL consumer yet (M3 partial, conditioning grid PROVISIONAL in metres above toe). When the conditioning grid is re-anchored to MSL stages, HWL is available as the site-specific reference level.

---

## References

- Spec §1 (M1 geometry contents), §2/ADR-0010 (frozen M8 geometry dict).
- ADR-0007 (z_toe ≡ h_e datum), ADR-0010 (hydrograph/geometry handoff contracts).
- `docs/tokachi_bep_inputs_provenance.md` §3.7 (KP 63.4 HWL resolution).
- `data/raw/geometry/BankHeight_TokachiRiv_2019.csv`, `BankHeight_SatsunaiRiv_2019.csv` (2019 design bank-height data, MSL datum).
