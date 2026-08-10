"""The Stage 6.6 driver refuses to overwrite a guarded record it never verified.

ADR-0040 gate (i) requires C0/C4b bit-identical to the persisted production
sweep. Until 2026-08-10 ``verify_against_production`` *recorded* a status and
returned on every non-verifying outcome, and the driver then persisted
``results/stage6_6/`` and dual-wrote the tracked ``docs/figures/`` copies
regardless, exiting 0 -- the driver-side member of the silent-skip class the
2026-07-31 audit closed for tests (`docs/repo_audit_2026-07-31.md` sections 11.2
and 12.4). That audit's AST guards are per-test-file and never covered drivers;
this file is the driver-side equivalent.

These tests assert on tracked paths and never skip on one (`docs/conventions.md`
section 9.4). The end-to-end pair runs the stub hydrograph path at N = 400, so no
gitignored `data/raw/` drop is needed.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import stage6_6_gap_decomposition as D  # noqa: E402

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.run import run_fragility_analysis  # noqa: E402
from tests.test_gap_decomposition import _make_config  # noqa: E402

_DRIVER_SOURCE = REPO_ROOT / "scripts" / "stage6_6_gap_decomposition.py"
_CAMPAIGN_SOURCE = REPO_ROOT / "scripts" / "production_campaign.py"


def _require_tracked(path: Path, why: str) -> Path:
    """Assert a tracked path exists -- never skip on one (conventions 9.4)."""
    assert path.exists(), f"tracked file missing ({why}): {path.relative_to(REPO_ROOT)}"
    return path


# ---------------------------------------------------------------------------
# The gate predicate
# ---------------------------------------------------------------------------


def test_only_bit_identical_clears_the_gate() -> None:
    """Every other status blocks, and so does an absent record."""
    assert D.verification_blocks_write({"status": D.VERIFIED_STATUS}) is None
    for status in (
        "skipped_missing_production_file",
        "skipped_config_mismatch_beyond_length_effect",
        "skipped_n_mismatch",
        D._COMPARABLE,
    ):
        assert D.verification_blocks_write({"status": status}) == status
    # The pilot path used to omit the key entirely; absence is not a pass.
    assert D.verification_blocks_write({}) == "absent"
    assert D.verification_blocks_write(None) == "absent"


def test_every_status_the_driver_can_write_is_classified() -> None:
    """A fifth non-verifying status cannot be added and silently pass.

    AST-parsed rather than grepped, for the same reason as the sibling guards in
    ``test_figure_pass.py``: a string search matches this docstring.
    """
    tree = ast.parse(_require_tracked(_DRIVER_SOURCE, "the driver").read_text())
    statuses = {
        node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Subscript)
        and isinstance(target.slice, ast.Constant)
        and target.slice.value == "status"
    }
    assert statuses, "no `record['status'] = ...' assignments found; guard is blind"
    for status in statuses:
        blocked = D.verification_blocks_write({"status": status}) is not None
        assert blocked == (status != D.VERIFIED_STATUS), (
            f"status {status!r} is neither the verified status nor blocking; "
            "classify it in verification_blocks_write"
        )


# ---------------------------------------------------------------------------
# End to end: refuses on a mismatched config, passes on the production path
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def stub_section(tmp_path_factory) -> dict:
    """A self-contained section: a stub config plus its own 'production' sweep."""
    tmp = tmp_path_factory.mktemp("stage6_6_gate")
    config = _make_config()

    config_path = tmp / "stub_matrix.yaml"
    config_path.write_text(yaml.safe_dump(config.to_metadata(), sort_keys=True))
    # Round-trips through the same loader the driver uses.
    assert Config.from_yaml(config_path).config_hash() == config.config_hash()

    production_path = tmp / "stub_production.h5"
    run_fragility_analysis(
        config, n_jobs=1, progress=False, output_path=production_path, persist=True
    )

    variant = _make_config(geometry={**config.geometry.model_dump(), "L": 31.0})
    variant_path = tmp / "stub_variant.yaml"
    variant_path.write_text(yaml.safe_dump(variant.to_metadata(), sort_keys=True))
    assert variant.config_hash() != config.config_hash()

    return {
        "tmp": tmp,
        "spec": {
            "config": str(config_path),
            "bulk_config": str(config_path),
            "production_h5": str(production_path),
            "attainable_max_m": 14.0,
            "label": "STUB",
        },
        "variant_config": str(variant_path),
    }


@pytest.fixture
def stub_key(stub_section, monkeypatch) -> str:
    """Register the stub section in the driver's registry for one test."""
    monkeypatch.setitem(D.SECTIONS, "stub", dict(stub_section["spec"]))
    return "stub"


def test_gate_passes_on_the_production_path(stub_section, stub_key) -> None:
    """A ladder built from the sweep's own config verifies and clears the gate."""
    result = D.run_section(
        stub_key,
        n_samples=None,
        n_jobs=1,
        out_dir=stub_section["tmp"],
        persist=False,
    )
    record = D.verify_against_production(stub_key, result)
    assert record["status"] == D.VERIFIED_STATUS
    assert record["levels_checked"] > 0
    assert record["theta_identical"] is True
    assert D.verification_blocks_write(record) is None


def test_gate_refuses_a_mismatched_config_before_anything_is_written(
    stub_section, stub_key, monkeypatch, capsys
) -> None:
    """The named refusal: a config change beyond the inert ADR-0037 block.

    Both the cheap pre-ladder check and the full post-ladder check must catch
    it, the refusal must be non-zero, and nothing may be written.
    """
    spec = dict(stub_section["spec"])
    spec["config"] = stub_section["variant_config"]
    monkeypatch.setitem(D.SECTIONS, stub_key, spec)

    variant = D.section_config(stub_key)
    before = sorted(p.name for p in stub_section["tmp"].iterdir())

    # (a) caught before the ladder runs, from the config alone.
    pre = D.production_comparability(
        stub_key,
        n_samples=variant.mc.n_samples,
        config_snapshot=variant.to_metadata(),
        base_config_hash=variant.config_hash(),
    )
    assert pre["status"] == "skipped_config_mismatch_beyond_length_effect"
    assert D.verification_blocks_write(pre) == pre["status"]

    # (b) and again after the ladder, through the full guard.
    result = D.run_section(
        stub_key,
        n_samples=None,
        n_jobs=1,
        out_dir=stub_section["tmp"],
        persist=False,
    )
    record = D.verify_against_production(stub_key, result)
    assert record["status"] == "skipped_config_mismatch_beyond_length_effect"

    # (c) the refusal is non-zero and names the flag that would permit it.
    code = D._refuse(stub_key, record["status"], record, ladder_spent=True)
    assert code == D.REFUSAL_EXIT_CODE != 0
    assert "--allow-unverified" in capsys.readouterr().err

    # (d) nothing was written by any of the above.
    assert sorted(p.name for p in stub_section["tmp"].iterdir()) == before


def test_gate_refuses_a_pilot_n_and_a_missing_production_sweep(
    stub_section, stub_key, monkeypatch
) -> None:
    """The two other cheap outcomes, including the one that had no status at all.

    A pilot ``--n`` writes to the same guarded paths as a production run, and
    before 2026-08-10 it skipped verification entirely rather than recording a
    status.
    """
    base = D.section_config(stub_key)
    pilot = D.production_comparability(
        stub_key,
        n_samples=base.mc.n_samples // 2,
        config_snapshot=base.to_metadata(),
        base_config_hash=base.config_hash(),
    )
    assert pilot["status"] == "skipped_n_mismatch"
    assert D.verification_blocks_write(pilot) == "skipped_n_mismatch"

    spec = dict(stub_section["spec"])
    spec["production_h5"] = str(stub_section["tmp"] / "does_not_exist.h5")
    monkeypatch.setitem(D.SECTIONS, stub_key, spec)
    missing = D.production_comparability(
        stub_key,
        n_samples=base.mc.n_samples,
        config_snapshot=base.to_metadata(),
        base_config_hash=base.config_hash(),
    )
    assert missing["status"] == "skipped_missing_production_file"
    assert D.verification_blocks_write(missing) == "skipped_missing_production_file"


# ---------------------------------------------------------------------------
# The two paths that must keep working
# ---------------------------------------------------------------------------


def test_figures_only_never_reaches_the_gate(monkeypatch, capsys) -> None:
    """A legitimate redraw must not be stoppable by the gate.

    Proved directly rather than by inspection: both gate entry points are
    replaced with raisers, and ``--figures-only`` still completes. It is a
    read-only redraw of already-persisted evidence, so it has nothing to guard.
    """

    def _boom(*args, **kwargs):  # pragma: no cover - must never be reached
        raise AssertionError("--figures-only reached the drift gate")

    monkeypatch.setattr(D, "verification_blocks_write", _boom)
    monkeypatch.setattr(D, "production_comparability", _boom)
    monkeypatch.setattr(D, "verify_against_production", _boom)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stage6_6_gap_decomposition.py",
            "--figures-only",
            "--sections",
            "no_such_section",
        ],
    )
    assert D.main() == 0
    assert "no evidence file touched" in capsys.readouterr().out


@pytest.mark.skipif(
    not (REPO_ROOT / "results" / "stage6_6" / "stage6_6_summary.json").exists(),
    reason="untracked: results/stage6_6/ is a gitignored campaign artifact",
)
@pytest.mark.parametrize("key", ["kp62_0", "kp57_4"])
def test_the_persisted_campaign_evidence_clears_the_gate(key: str) -> None:
    """The refusal does not fire on the production path, re-derived not assumed.

    Replays the refactored guard over the persisted ladder (no physics, nothing
    written) and requires both that it clears the gate and that the record it
    produces is identical to the one the campaign already recorded -- so the
    campaign's ``stage6_6_summary.json`` stays byte-unchanged.
    """
    import json

    from bep_reliability_engine.gap_decomposition import GapDecompositionResult

    ladder = D.section_h5_path(key)
    if not ladder.exists():  # untracked companion of the summary
        pytest.skip(f"untracked: {ladder.name} not present")

    recorded = json.loads((D.OUT_DIR / "stage6_6_summary.json").read_text())
    previous = recorded["sections"][key]["production_verification"]
    replayed = D.verify_against_production(key, GapDecompositionResult.load(ladder))

    assert D.verification_blocks_write(replayed) is None
    assert json.dumps(replayed) == json.dumps(previous)


def test_the_campaign_invocation_does_not_opt_out() -> None:
    """The campaign's own command carries no opt-out, so G3's gate is real.

    Asserted from the tracked driver source rather than from the gitignored
    manifest: the campaign runs ``--n-jobs N --skip-figures`` and nothing else,
    so its recorded ``bit_identical`` status is what clears the new gate.
    """
    source = _require_tracked(_CAMPAIGN_SOURCE, "the campaign driver").read_text()
    tree = ast.parse(source)
    invocations = [
        [e.value for e in node.elts if isinstance(e, ast.Constant)]
        for node in ast.walk(tree)
        if isinstance(node, ast.List)
        and any(
            isinstance(e, ast.Constant)
            and e.value == "scripts/stage6_6_gap_decomposition.py"
            for e in node.elts
        )
    ]
    assert invocations, "no stage6_6 invocation found in the campaign driver"
    for argv in invocations:
        assert "--allow-unverified" not in argv, (
            "the campaign must not opt out of the drift guard; its status is "
            "bit_identical, so the refusal never fires there"
        )
