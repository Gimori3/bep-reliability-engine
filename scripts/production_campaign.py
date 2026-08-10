"""Master driver for the definitive Phase 1 + Phase 2 + Phase 3 production campaign.

Every number in the thesis report must trace to one execution of this script.
It contains **no physics**: like ``scripts/phase3_campaign.py`` it only
sequences existing entry points in dependency order, preserves what it is
about to supersede, checks the mandatory gates, and writes a machine-readable
manifest.

Why the re-run exists
---------------------
Six of the eight persisted Phase 1 sweeps carry config hashes that no longer
match ``configs/*.yaml``. The difference is *exactly* the three physics-inert
ADR-0037 ``length_effect`` keys (``enabled``/``lambda_ac_m``/
``segment_length_m``), which the generator started emitting after those sweeps
ran; ``run.py`` consumes the block only when ``enabled`` is true, and it lands
in metadata only. ``Config.to_metadata()`` drops the key when it is ``None``,
so the pre-ADR-0037 sidecars hash without it and the current configs hash with
it. Stage ``configs`` re-proves that claim key by key before anything else
runs, and gate **G1** turns it into a hard requirement: the re-run sweeps must
reproduce the superseded failure matrices bit-for-bit.

Stages (``--stage`` to run a subset, in this order)
--------------------------------------------------
``configs``                regenerate ``configs/`` and assert an EMPTY diff
``phase1``                 8 sweeps, N = 1e5, dt = 225 s                   [G1]
``phase2_baseline``        8 posteriors, ``--verify``                      [G2]
``phase2_anchor_rating``   4 matrix strata, ``--anchor rating``
``phase2_no_initiation``   4 matrix strata, ``--criterion no_breach_no_initiation``
``stage6_6``               KP62.0 + KP57.4, matrix and bulk                [G3]
``phase3``                 full RQ3+RQ4 campaign (hazard cache reused)     [G4]
``phase3_validation``      event-based surface-mechanism validation
``companions``             every bit-identity-asserting companion study
``diagnostics``            G5 collection across every artifact            [G5]

Usage (repo root, venv active)::

    python scripts/production_campaign.py                    # resume/run all
    python scripts/production_campaign.py --stage phase1     # one stage
    python scripts/production_campaign.py --force            # ignore manifest
    python scripts/production_campaign.py --dry-run          # print the plan

Resumability: the manifest records a status per stage. A stage that already
``passed`` is skipped on the next invocation unless ``--force`` is given, so an
interrupted campaign resumes where it stopped. Gate failures are terminal --
the manifest is flushed and the process exits non-zero rather than continuing
into stages that would consume a suspect artifact.

The compute stages deliberately do not regenerate figures (``--no-figures`` /
``--skip-figures`` / ``--no-figure`` are passed through): rendering during a
long sweep buys nothing. Instead the dedicated ``figures`` stage (added
2026-07-30) re-renders every publication figure that has a cheap redraw path
and then **gates on staleness** -- gate G7 fails if any figure under
``docs/figures/`` is older than the artifact it depicts. That gate is the
structural fix for the manual copy step that let the Stage 6.6 KP 62.0 figures
go stale twice. Since 2026-07-31 every tracked figure is *declared*, and G7
fails on an undeclared one: the eight with no plot-only path carry
declaration-only entries binding them to their evidence, so they are staleness-
gated without being re-run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from bep_reliability_engine.config import Config  # noqa: E402
from bep_reliability_engine.fragility import FragilityResult  # noqa: E402

MANIFEST_PATH = REPO / "results" / "production_campaign_manifest.json"
CAMPAIGN_DIR = REPO / "results" / "production_campaign"
PY = sys.executable

# --------------------------------------------------------------------------- #
# Registry                                                                     #
# --------------------------------------------------------------------------- #

#: Persisted sweep stem -> generating config, in the campaign's canonical order.
SECTIONS: dict[str, str] = {
    "tokachi_kp57.4_historical_matrix": "kp57_4_historical_matrix.yaml",
    "tokachi_kp57.4_historical_bulk": "kp57_4_historical_bulk.yaml",
    "tokachi_kp58.8_historical_matrix": "kp58_8_historical_matrix.yaml",
    "tokachi_kp58.8_historical_bulk": "kp58_8_historical_bulk.yaml",
    "tokachi_kp60.0_historical_matrix": "kp60_0_historical_matrix.yaml",
    "tokachi_kp60.0_historical_bulk": "kp60_0_historical_bulk.yaml",
    "tokachi_kp62.0_historical_matrix": "kp62_0_historical_matrix.yaml",
    "tokachi_kp62.0_historical_bulk": "kp62_0_historical_bulk.yaml",
}

MATRIX_STEMS = [s for s in SECTIONS if s.endswith("_matrix")]

#: The three ADR-0037 keys that may legitimately differ between a persisted
#: pre-ADR-0037 sidecar and the current generated config. Nothing else may.
LENGTH_EFFECT_KEYS = frozenset(
    {
        "length_effect.enabled",
        "length_effect.lambda_ac_m",
        "length_effect.segment_length_m",
    }
)

#: Metadata keys whose value is allowed to move between the superseded run and
#: the re-run (G1). Everything else must be equal -- with one asymmetry, below.
G1_VOLATILE_METADATA = frozenset(
    {
        "config",  # differs only by the length_effect block (checked separately)
        "config_hash",  # consequence of the above
        "runtime_seconds",
        "n_jobs",
        "generated",
        "generated_utc",
        "timestamp",
        "code_version",
    }
)

# G1 treats metadata differences asymmetrically, and deliberately so.
#
# A key that is ABSENT in the superseded sidecar and PRESENT in the re-run is a
# diagnostic block that was wired into run.py after that sweep was persisted --
# purely additive, metadata-only, no physics. The 2026-07-29 campaign hit
# exactly one: metadata['aquifer_response'] (ADR-0032, wired 2026-07-11) is
# missing from the three matrix sidecars generated 2026-07-10 and never re-run
# since, and reappears on the re-run. Recording it and passing is right; the
# alternative is a gate that fires every time the engine gains a diagnostic.
#
# A key whose VALUE CHANGED, or that REGRESSED from present to absent, is not
# covered by that argument and still fails the gate. So does any difference in a
# failure matrix, theta, the grid, or the raw P_f vectors -- which is what G1 is
# actually about, and which passed at all eight strata.

#: Spec Section 11 target for the Monte Carlo CoV of the P_f estimator.
PF_COV_TARGET = 0.05
#: ADR-0032 pre-registered aquifer-response threshold.
PI_THRESHOLD = 0.10


# --------------------------------------------------------------------------- #
# Small helpers (pure I/O and bookkeeping -- no physics)                        #
# --------------------------------------------------------------------------- #


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_of(path: Path) -> str | None:
    """SHA-256 of a file, or None when it does not exist."""
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_outputs(paths: list[Path]) -> list[dict[str, Any]]:
    """Manifest records for a stage's outputs: path, size, SHA-256."""
    out: list[dict[str, Any]] = []
    for path in sorted(paths):
        out.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "exists": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256_of(path),
            }
        )
    return out


def flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dicts to dotted keys (lists are compared as leaves)."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            out.update(flatten(value, f"{prefix}.{key}" if prefix else str(key)))
        return out
    return {prefix: obj}


def run_command(
    command: list[str], *, label: str, log_path: Path | None = None
) -> dict[str, Any]:
    """Run a subprocess, stream-capture it, and return a manifest record."""
    started = time.perf_counter()
    start_iso = _utcnow()
    printable = " ".join(command[1:] if command[0] == PY else command)
    print(f"    $ python {printable}", flush=True)
    proc = subprocess.run(
        command,
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.perf_counter() - started
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            f"$ {' '.join(command)}\n\n--- stdout ---\n{proc.stdout}\n"
            f"--- stderr ---\n{proc.stderr}\n",
            encoding="utf-8",
        )
    record = {
        "label": label,
        "command": " ".join(command),
        "start": start_iso,
        "end": _utcnow(),
        "runtime_s": round(elapsed, 2),
        "returncode": proc.returncode,
        "log": (
            str(log_path.relative_to(REPO)).replace("\\", "/")
            if log_path is not None
            else None
        ),
    }
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-25:])
        record["stderr_tail"] = tail
        print(f"    !! returncode {proc.returncode}\n{tail}", flush=True)
    else:
        print(f"    ok ({elapsed:.1f} s)", flush=True)
    return record


def preserve(paths: list[Path], superseded_root: Path) -> list[str]:
    """Move existing artifacts into the superseded root, layout preserved."""
    moved: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        rel = path.relative_to(REPO / "results")
        target = superseded_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        moved.append(str(rel).replace("\\", "/"))
    return moved


class GateFailure(RuntimeError):
    """A mandatory gate failed: the campaign stops, it is not a warning."""


class Gates:
    """Collects gate outcomes for one stage; raises on the first failure."""

    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.records: list[dict[str, Any]] = []

    def check(self, gate: str, name: str, passed: bool, detail: Any) -> None:
        status = "pass" if passed else "FAIL"
        self.records.append(
            {"gate": gate, "name": name, "status": status, "detail": detail}
        )
        marker = "  [OK]" if passed else "  [FAIL]"
        print(f"{marker} {gate} {name}", flush=True)
        if not passed:
            raise GateFailure(
                f"{self.stage}: gate {gate} ({name}) FAILED -- "
                f"{json.dumps(detail)[:2000]}"
            )

    def note(self, gate: str, name: str, detail: Any) -> None:
        """Record an observation that is reported but does not gate."""
        self.records.append(
            {"gate": gate, "name": name, "status": "info", "detail": detail}
        )
        print(f"  [INFO] {gate} {name}", flush=True)


# --------------------------------------------------------------------------- #
# Stage 1 -- configs                                                            #
# --------------------------------------------------------------------------- #


def stage_configs(ctx: "Context") -> dict[str, Any]:
    """Regenerate configs/ and assert the diff is EMPTY (any diff is a bug).

    Also re-proves the re-run justification: the persisted sidecars' config
    snapshots differ from the current generated configs by exactly the three
    ADR-0037 length_effect keys at the six pre-ADR-0037 sections, and by
    nothing at KP62.0 (re-run during the ADR-0047 adoption).
    """
    gates = Gates("configs")
    config_dir = REPO / "configs"
    before = {p.name: p.read_bytes() for p in sorted(config_dir.glob("*.yaml"))}

    # -- the justification audit, BEFORE regenerating anything ---------------
    audit: dict[str, Any] = {}
    unexpected: list[str] = []
    for stem, cfg_name in SECTIONS.items():
        sidecar = REPO / "results" / f"{stem}.json"
        if not sidecar.is_file():
            audit[stem] = {"status": "no_persisted_sidecar"}
            continue
        persisted = json.loads(sidecar.read_text(encoding="utf-8"))
        cfg = Config.from_yaml(config_dir / cfg_name)
        flat_old = flatten(persisted["config"])
        flat_new = flatten(cfg.to_metadata())
        keys = set(flat_old) | set(flat_new)
        diffs = sorted(
            k
            for k in keys
            if flat_old.get(k, "<absent>") != flat_new.get(k, "<absent>")
        )
        extra = sorted(set(diffs) - LENGTH_EFFECT_KEYS)
        audit[stem] = {
            "persisted_config_hash": persisted.get("config_hash"),
            "current_config_hash": cfg.config_hash(),
            "hash_match": persisted.get("config_hash") == cfg.config_hash(),
            "differing_keys": diffs,
            "non_length_effect_differences": extra,
        }
        if extra:
            unexpected.append(stem)

    gates.check(
        "G0",
        "persisted-vs-current config diff is only the ADR-0037 length_effect keys",
        not unexpected,
        {"sections_with_unexpected_diffs": unexpected, "audit": audit},
    )
    n_hash_changes = sum(1 for v in audit.values() if v.get("hash_match") is False)
    gates.note(
        "G0",
        "config_hash changes expected from this re-run",
        {
            "n_sections_hash_changing": n_hash_changes,
            "sections": sorted(
                k for k, v in audit.items() if v.get("hash_match") is False
            ),
        },
    )

    # -- regenerate, then require a byte-identical configs/ -------------------
    cmd = run_command(
        [PY, "scripts/generate_configs.py"],
        label="generate_configs",
        log_path=ctx.log_dir / "configs_generate.log",
    )
    if cmd["returncode"] != 0:
        raise GateFailure("configs: scripts/generate_configs.py failed")

    after = {p.name: p.read_bytes() for p in sorted(config_dir.glob("*.yaml"))}
    changed = sorted(
        name for name in set(before) | set(after) if before.get(name) != after.get(name)
    )
    gates.check(
        "G0",
        "regenerated configs/ is byte-identical (CSV unchanged since ADR-0047)",
        not changed,
        {"changed_files": changed, "n_configs": len(after)},
    )

    return {
        "commands": [cmd],
        "gates": gates.records,
        "outputs": describe_outputs(sorted(config_dir.glob("*.yaml"))),
        "justification_audit": audit,
    }


# --------------------------------------------------------------------------- #
# Stage 2 -- Phase 1 sweeps + G1                                                #
# --------------------------------------------------------------------------- #


def _sweeps_already_current() -> bool:
    """True when results/ already holds sweeps produced under the CURRENT configs.

    The re-run stamps each sidecar with the config hash of the config that
    produced it, so this is an exact test of "the expensive step is already
    done" -- the pre-campaign files carry the superseded hashes and fail it.
    """
    for stem, cfg_name in SECTIONS.items():
        sidecar = REPO / "results" / f"{stem}.json"
        if not (sidecar.is_file() and (REPO / "results" / f"{stem}.h5").is_file()):
            return False
        recorded = json.loads(sidecar.read_text(encoding="utf-8")).get("config_hash")
        if recorded != Config.from_yaml(REPO / "configs" / cfg_name).config_hash():
            return False
    return True


def _latest_complete_baseline() -> Path | None:
    """Newest results/superseded_*/ directory holding all 8 superseded sweeps."""
    roots = sorted(
        (p for p in (REPO / "results").glob("superseded_*") if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    for root in roots:
        if all((root / f"{stem}.h5").is_file() for stem in SECTIONS):
            return root
    return None


def stage_phase1(ctx: "Context") -> dict[str, Any]:
    """Re-run all 8 sweeps and gate them bit-identical to the superseded files."""
    gates = Gates("phase1")
    results = REPO / "results"

    # Resume: if an earlier attempt already produced sweeps under the current
    # configs, re-gate them against the baseline it preserved instead of
    # spending another ~25 minutes reproducing identical files.
    baseline_root = _latest_complete_baseline()
    if _sweeps_already_current() and baseline_root is not None:
        print(
            f"  sweeps already current; re-gating against {baseline_root.name}",
            flush=True,
        )
        cmd = {
            "label": "run_sweep_all_8",
            "command": "(skipped: results/ already carries the current config hashes)",
            "runtime_s": 0.0,
            "returncode": 0,
            "resumed": True,
        }
        moved: list[str] = []
    else:
        targets = [
            results / f"{stem}{ext}" for stem in SECTIONS for ext in (".h5", ".json")
        ]
        moved = preserve(targets, ctx.superseded_root)
        baseline_root = ctx.superseded_root
        print(f"  preserved {len(moved)} file(s) -> {ctx.superseded_rel}", flush=True)

        configs = [str(Path("configs") / name) for name in SECTIONS.values()]
        cmd = run_command(
            [PY, "scripts/run_sweep.py", *configs, "--n-jobs", str(ctx.n_jobs)],
            label="run_sweep_all_8",
            log_path=ctx.log_dir / "phase1_run_sweep.log",
        )
        if cmd["returncode"] != 0:
            raise GateFailure("phase1: scripts/run_sweep.py failed")

    # -- G1: element-wise bit-identity of both failure matrices ---------------
    comparisons: dict[str, Any] = {}
    failures: list[str] = []
    for stem in SECTIONS:
        new_h5 = results / f"{stem}.h5"
        old_h5 = baseline_root / f"{stem}.h5"
        if not old_h5.is_file():
            comparisons[stem] = {"status": "no_superseded_baseline"}
            continue
        new = FragilityResult.load(new_h5)
        old = FragilityResult.load(old_h5)
        same_trans = np.array_equal(new.failure_matrix_tran, old.failure_matrix_tran)
        same_static = np.array_equal(new.failure_matrix_stat, old.failure_matrix_stat)
        same_theta = np.array_equal(new.theta_matrix, old.theta_matrix)
        same_grid = np.array_equal(
            np.asarray(new.conditioning_grid, dtype=float),
            np.asarray(old.conditioning_grid, dtype=float),
        )

        # Metadata differences, classified asymmetrically (see G1 note above).
        meta_new, meta_old = new.metadata, old.metadata
        meta_keys = (set(meta_new) | set(meta_old)) - G1_VOLATILE_METADATA
        additions = sorted(k for k in meta_keys if k in meta_new and k not in meta_old)
        regressions = sorted(
            k for k in meta_keys if k in meta_old and k not in meta_new
        )
        meta_diffs = sorted(
            k
            for k in meta_keys
            if k in meta_new and k in meta_old and meta_new[k] != meta_old[k]
        )
        flat_new = flatten(meta_new.get("config", {}))
        flat_old = flatten(meta_old.get("config", {}))
        cfg_diffs = sorted(
            k
            for k in set(flat_new) | set(flat_old)
            if flat_new.get(k, "<absent>") != flat_old.get(k, "<absent>")
        )
        cfg_extra = sorted(set(cfg_diffs) - LENGTH_EFFECT_KEYS)

        entry = {
            "failure_matrix_trans_identical": bool(same_trans),
            "failure_matrix_static_identical": bool(same_static),
            "theta_matrix_identical": bool(same_theta),
            "conditioning_grid_identical": bool(same_grid),
            "raw_p_f_static_identical": bool(
                np.array_equal(new.P_f_static_raw, old.P_f_static_raw)
            ),
            "raw_p_f_trans_identical": bool(
                np.array_equal(new.P_f_trans_raw, old.P_f_trans_raw)
            ),
            "n_realizations": int(new.theta_matrix.shape[0]),
            "n_levels": int(len(new.conditioning_grid)),
            "metadata_value_changes": meta_diffs,
            "metadata_regressions": regressions,
            "metadata_additive_keys": additions,
            "config_diffs": cfg_diffs,
            "config_diffs_beyond_length_effect": cfg_extra,
            "superseded_config_hash": meta_old.get("config_hash"),
            "new_config_hash": meta_new.get("config_hash"),
        }
        if not (same_trans and same_static and same_theta and same_grid):
            entry["mismatch_cells_trans"] = int(
                np.count_nonzero(new.failure_matrix_tran != old.failure_matrix_tran)
            )
            entry["mismatch_cells_static"] = int(
                np.count_nonzero(new.failure_matrix_stat != old.failure_matrix_stat)
            )
            failures.append(stem)
        if meta_diffs or regressions or cfg_extra:
            failures.append(stem)
        comparisons[stem] = entry

    gates.check(
        "G1",
        "re-run failure matrices element-wise identical to the superseded files",
        not failures,
        {"sections_failing": sorted(set(failures)), "comparisons": comparisons},
    )
    additive = {
        stem: e["metadata_additive_keys"]
        for stem, e in comparisons.items()
        if e.get("metadata_additive_keys")
    }
    gates.note(
        "G1",
        "additive metadata keys gained by the re-run (diagnostics wired after "
        "the superseded sweep was persisted; no physics)",
        additive or "none",
    )

    outputs = [
        results / f"{stem}{ext}" for stem in SECTIONS for ext in (".h5", ".json")
    ]
    return {
        "commands": [cmd],
        "gates": gates.records,
        "outputs": describe_outputs(outputs),
        "superseded": {
            "root": str(baseline_root.relative_to(REPO)).replace("\\", "/"),
            "moved": moved,
        },
    }


# --------------------------------------------------------------------------- #
# Stage 3 -- Phase 2 (baseline + both documented sensitivity variants) + G2      #
# --------------------------------------------------------------------------- #


def _phase2_stage(
    ctx: "Context",
    *,
    stems: list[str],
    out_dir: Path,
    extra_flags: list[str],
    label: str,
    gate_marginal: bool,
) -> dict[str, Any]:
    gates = Gates(label)
    results = REPO / "results"
    existing = [
        p for p in out_dir.glob("*_posterior.*") if p.suffix in {".h5", ".json"}
    ]
    moved = preserve(existing, ctx.superseded_root)
    print(f"  preserved {len(moved)} file(s) -> {ctx.superseded_rel}", flush=True)

    inputs = [str((results / f"{stem}.h5").relative_to(REPO)) for stem in stems]
    cmd = run_command(
        [
            PY,
            "-m",
            "bayesian_reliability_updating",
            *inputs,
            "--out",
            str(out_dir.relative_to(REPO)),
            "--verify",
            "--no-figures",
            *extra_flags,
        ],
        label=label,
        log_path=ctx.log_dir / f"{label}.log",
    )
    if cmd["returncode"] != 0:
        raise GateFailure(f"{label}: bayesian_reliability_updating failed")

    per_stratum: dict[str, Any] = {}
    unverified: list[str] = []
    marginal_nonzero: list[str] = []
    hash_mismatch: list[str] = []
    for stem in stems:
        sidecar = out_dir / f"{stem}_posterior.json"
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        p1, p2 = payload["phase1"], payload["phase2"]
        ver = p2.get("verification", {})
        chain = p2.get("event_chain", [])
        decomp = chain[0]["decomposition"] if chain else {}
        # The replay must have consumed the freshly re-run Phase 1 artifact.
        current_hash = Config.from_yaml(REPO / "configs" / SECTIONS[stem]).config_hash()
        entry = {
            "phase1_config_hash": p1.get("config_hash"),
            "current_config_hash": current_hash,
            "hash_current": p1.get("config_hash") == current_hash,
            "verified": bool(ver.get("verified")),
            "flag_mismatch_static": ver.get("flag_mismatch_static"),
            "flag_mismatch_trans": ver.get("flag_mismatch_trans"),
            "n_prior": p2["posterior"].get("n_prior"),
            "n_accepted": p2["posterior"].get("n_accepted"),
            "rejection_fraction": p2["posterior"].get("rejection_fraction"),
            "criterion": p2["posterior"].get("criterion"),
            "f_static_reject": decomp.get("f_static_reject"),
            "f_trans_reject": decomp.get("f_trans_reject"),
            "f_marginal_transient": decomp.get("f_marginal_transient"),
        }
        per_stratum[stem] = entry
        if not (
            ver.get("verified")
            and ver.get("flag_mismatch_static") == 0
            and ver.get("flag_mismatch_trans") == 0
        ):
            unverified.append(stem)
        if decomp.get("f_marginal_transient"):
            marginal_nonzero.append(stem)
        if not entry["hash_current"]:
            hash_mismatch.append(stem)

    gates.check(
        "G2",
        f"{label}: --verify exact (zero flag mismatches) in every stratum",
        not unverified,
        {"strata_failing": unverified, "per_stratum": per_stratum},
    )
    gates.check(
        "G2",
        f"{label}: every posterior replays the freshly re-run Phase 1 hash",
        not hash_mismatch,
        {"strata_failing": hash_mismatch},
    )
    if gate_marginal:
        gates.check(
            "G2",
            "marginal transient rejection is exactly 0 in all eight strata",
            not marginal_nonzero,
            {
                "strata_with_nonzero_marginal": marginal_nonzero,
                "values": {
                    k: v["f_marginal_transient"] for k, v in per_stratum.items()
                },
            },
        )

    outputs = [
        out_dir / f"{stem}_posterior{ext}" for stem in stems for ext in (".h5", ".json")
    ]
    return {
        "commands": [cmd],
        "gates": gates.records,
        "outputs": describe_outputs(outputs),
        "per_stratum": per_stratum,
        "superseded": {"root": ctx.superseded_rel, "moved": moved},
    }


def stage_phase2_baseline(ctx: "Context") -> dict[str, Any]:
    """All 8 baseline posteriors with --verify; gates G2 including marginal = 0."""
    return _phase2_stage(
        ctx,
        stems=list(SECTIONS),
        out_dir=REPO / "results" / "phase2",
        extra_flags=[],
        label="phase2_baseline",
        gate_marginal=True,
    )


def stage_phase2_anchor_rating(ctx: "Context") -> dict[str, Any]:
    """ADR-0035 anchor sensitivity across all 4 matrix strata."""
    return _phase2_stage(
        ctx,
        stems=MATRIX_STEMS,
        out_dir=REPO / "results" / "phase2_anchor_rating",
        extra_flags=["--anchor", "rating"],
        label="phase2_anchor_rating",
        gate_marginal=False,
    )


def stage_phase2_no_initiation(ctx: "Context") -> dict[str, Any]:
    """ADR-0036 strict-criterion sensitivity across all 4 matrix strata."""
    return _phase2_stage(
        ctx,
        stems=MATRIX_STEMS,
        out_dir=REPO / "results" / "phase2_no_initiation",
        extra_flags=["--criterion", "no_breach_no_initiation"],
        label="phase2_no_initiation",
        gate_marginal=False,
    )


# --------------------------------------------------------------------------- #
# Stage 4 -- Stage 6.6 gap decomposition + G3                                   #
# --------------------------------------------------------------------------- #


def stage_stage6_6(ctx: "Context") -> dict[str, Any]:
    """Ten-comparator ladder at KP62.0 and KP57.4, matrix and bulk."""
    gates = Gates("stage6_6")
    out_dir = REPO / "results" / "stage6_6"
    existing = [p for p in out_dir.glob("stage6_6_*") if p.is_file()]
    moved = preserve(existing, ctx.superseded_root)
    print(f"  preserved {len(moved)} file(s) -> {ctx.superseded_rel}", flush=True)

    cmd = run_command(
        [
            PY,
            "scripts/stage6_6_gap_decomposition.py",
            "--n-jobs",
            str(ctx.n_jobs),
            "--skip-figures",
        ],
        label="stage6_6",
        log_path=ctx.log_dir / "stage6_6.log",
    )
    if cmd["returncode"] != 0:
        raise GateFailure("stage6_6: scripts/stage6_6_gap_decomposition.py failed")

    summary = json.loads(
        (out_dir / "stage6_6_summary.json").read_text(encoding="utf-8")
    )
    sections = summary.get("sections", {})
    drift: dict[str, Any] = {}
    euler: dict[str, Any] = {}
    drift_bad: list[str] = []
    euler_bad: list[str] = []
    for key, section in sections.items():
        record = section.get("production_verification", {})
        drift[key] = record
        if record.get("status") != "bit_identical":
            drift_bad.append(key)
        flips = section.get("flip_totals", {})
        euler[key] = flips
        if any(v for v in flips.values()):
            euler_bad.append(key)

    gates.check(
        "G3",
        "both sections present in the summary (KP62.0 and KP57.4)",
        set(sections) >= {"kp62_0", "kp57_4"},
        {"sections_present": sorted(sections)},
    )
    gates.check(
        "G3",
        "production drift guard bit-identical at all common levels",
        not drift_bad and bool(drift),
        {"sections_failing": drift_bad, "records": drift},
    )
    gates.check(
        "G3",
        "every Euler-flip count is exactly 0",
        not euler_bad,
        {"sections_failing": euler_bad, "counts": euler},
    )

    outputs = [p for p in sorted(out_dir.glob("stage6_6_*")) if p.is_file()]
    return {
        "commands": [cmd],
        "gates": gates.records,
        "outputs": describe_outputs(outputs),
        "superseded": {"root": ctx.superseded_rel, "moved": moved},
    }


# --------------------------------------------------------------------------- #
# Stage 5 -- Phase 3 + G4                                                       #
# --------------------------------------------------------------------------- #


def stage_phase3(ctx: "Context") -> dict[str, Any]:
    """Full RQ3+RQ4 campaign; G4 diffs rq4_annual.csv against the previous one."""
    gates = Gates("phase3")
    out_dir = REPO / "results" / "system_integration" / "phase3"
    prior_rq4 = out_dir / "rq4_annual.csv"
    prior_rows = _read_csv_rows(prior_rq4)

    existing = [p for p in out_dir.glob("*") if p.is_file()]
    moved = preserve(existing, ctx.superseded_root)
    print(f"  preserved {len(moved)} file(s) -> {ctx.superseded_rel}", flush=True)

    cmd = run_command(
        [PY, "scripts/phase3_campaign.py"],
        label="phase3_campaign",
        log_path=ctx.log_dir / "phase3_campaign.log",
    )
    if cmd["returncode"] != 0:
        raise GateFailure("phase3: scripts/phase3_campaign.py failed")

    new_rows = _read_csv_rows(prior_rq4)
    changed, detail = _diff_rq4(prior_rows, new_rows)
    gates.note(
        "G4",
        "rq4_annual.csv changed-row count vs the superseded campaign",
        {
            "changed_rows": changed,
            "n_rows_before": len(prior_rows),
            "n_rows_after": len(new_rows),
            "sample": detail[:20],
        },
    )
    gates.check(
        "G4",
        "rq4_annual.csv row set is unchanged in shape (same keys, same count)",
        len(prior_rows) == len(new_rows) or not prior_rows,
        {"n_rows_before": len(prior_rows), "n_rows_after": len(new_rows)},
    )

    outputs = [p for p in sorted(out_dir.glob("*")) if p.is_file()]
    return {
        "commands": [cmd],
        "gates": gates.records,
        "outputs": describe_outputs(outputs),
        "rq4_changed_rows": changed,
        "rq4_changes": detail,
        "superseded": {"root": ctx.superseded_rel, "moved": moved},
    }


def _read_csv_rows(path: Path) -> dict[tuple[str, ...], dict[str, str]]:
    """Read rq4_annual.csv keyed by its identifying columns."""
    if not path.is_file():
        return {}
    import csv

    rows: dict[tuple[str, ...], dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        key_fields = [
            f
            for f in fields
            if f
            in {
                "river",
                "bank",
                "kp",
                "segment_id",
                "scenario",
                "d70",
                "bep_source",
                "lambda_ac_m",
                "surface_variant",
                "variant",
            }
        ]
        for row in reader:
            key = tuple(row.get(f, "") for f in key_fields)
            rows[key] = row
    return rows


def _diff_rq4(
    before: dict[tuple[str, ...], dict[str, str]],
    after: dict[tuple[str, ...], dict[str, str]],
) -> tuple[int, list[dict[str, Any]]]:
    """Count and describe rows whose values moved."""
    changed = 0
    detail: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after), key=lambda k: tuple(map(str, k))):
        old, new = before.get(key), after.get(key)
        if old == new:
            continue
        changed += 1
        if old is None or new is None:
            detail.append(
                {"key": list(key), "change": "added" if old is None else "removed"}
            )
            continue
        moved = {
            field: {"before": old.get(field), "after": new.get(field)}
            for field in sorted(set(old) | set(new))
            if old.get(field) != new.get(field)
        }
        detail.append({"key": list(key), "fields": moved})
    return changed, detail


def stage_phase3_validation(ctx: "Context") -> dict[str, Any]:
    """Event-based surface-mechanism validation over the full d4PDF ensembles."""
    gates = Gates("phase3_validation")
    out = (
        REPO
        / "results"
        / "system_integration"
        / "phase3"
        / "event_based_validation.json"
    )
    cmd = run_command(
        [PY, "scripts/validate_event_based_surface.py"],
        label="validate_event_based_surface",
        log_path=ctx.log_dir / "phase3_validation.log",
    )
    if cmd["returncode"] != 0:
        raise GateFailure("phase3_validation: validate_event_based_surface.py failed")
    gates.check(
        "G4",
        "event-based validation record written",
        out.is_file(),
        {"path": str(out.relative_to(REPO)).replace("\\", "/")},
    )
    return {
        "commands": [cmd],
        "gates": gates.records,
        "outputs": describe_outputs([out]),
    }


# --------------------------------------------------------------------------- #
# Stage 6 -- companions asserting bit-identity                                  #
# --------------------------------------------------------------------------- #

#: Companion studies that pin themselves against a persisted production sweep.
#: Enumerated programmatically at campaign time (see ``enumerate_companions``);
#: this table carries the invocation for each name that enumeration finds, plus
#: the tracked evidence file to compare against when the driver supports --out.
COMPANION_COMMANDS: dict[str, dict[str, Any]] = {
    "segment_fragility": {
        "argv": ["scripts/segment_fragility.py"],
        "outputs": ["results/segment_fragility_adr0037.json"],
    },
    "qa_re_halved_member": {
        "argv": ["scripts/qa_re_halved_member.py"],
        "outputs": ["results/qa_re_halved_kp58_8.json"],
    },
    "foreshore_width_study": {
        "argv": [
            "scripts/foreshore_width_study.py",
            "--out",
            "results/production_campaign/companions/adr0025-foreshore-sensitivity.json",
        ],
        "outputs": [
            "results/production_campaign/companions/adr0025-foreshore-sensitivity.json"
        ],
        "compare_to": "docs/decisions/adr0025-foreshore-sensitivity.json",
    },
    "seepage_length_study": {
        "argv": ["scripts/seepage_length_study.py", "all"],
        "outputs": [
            "results/sensitivity/seepage_length/marginal_sensitivity.json",
            "results/sensitivity/seepage_length/system_correlation.json",
        ],
    },
    "foreshore_exhaustion_study": {
        "argv": [
            "scripts/foreshore_exhaustion_study.py",
            "--no-figure",
            "--out",
            "results/production_campaign/companions/r10-foreshore-exhaustion-screening.json",
        ],
        "outputs": [
            "results/production_campaign/companions/r10-foreshore-exhaustion-screening.json"
        ],
        "compare_to": "docs/decisions/r10-foreshore-exhaustion-screening.json",
    },
    "assess_2011_2006_closure": {
        "argv": ["scripts/assess_2011_2006_closure.py"],
        "outputs": ["docs/decisions/adr0044-event-closure-bound.json"],
        "git_tracked": True,
    },
    "dem_cross_section_study": {
        "argv": [
            "scripts/dem_cross_section_study.py",
            "fragility",
            "--n-jobs",
            "4",
            "--out",
            "results/production_campaign/companions/adr0047-dem-seepage-length.json",
        ],
        "outputs": [
            "results/production_campaign/companions/adr0047-dem-seepage-length.json"
        ],
        "compare_to": "docs/decisions/adr0047-dem-seepage-length.json",
        # DECLARED, NOT WAIVED. The committed ADR-0047 evidence is a
        # PRE-ADOPTION artifact: the 2026-07-29 adoption changed the CSV
        # (KP62.0 L 47.0 -> 40.0) and re-pinned this driver so KP62.0's
        # baseline is the adopted 40 m with the withdrawn 47 m as the
        # sensitivity arm, but the JSON was never regenerated. Three of the
        # four sections are byte-identical; only the KP62.0 block moved, and
        # in exactly the direction the adoption dictates. Every baseline arm
        # still asserts bit-identical to its persisted production sweep --
        # which is what this stage is really testing. Remedy (belongs to the
        # figure pass, since it re-renders a figure):
        #     python scripts/dem_cross_section_study.py all --overwrite
        # Any key outside this list still fails the gate.
        "expected_changed_keys": ["fragility", "measurements"],
        "expected_change_reason": (
            "committed evidence predates the ADR-0047 KP62.0 adoption; its "
            "KP62.0 block still names L = 47.0 m as baseline"
        ),
    },
    "ce_prior_study": {
        "argv": ["scripts/ce_prior_study.py", "propagate"],
        "outputs": ["results/sensitivity/ce_prior/fragility_propagation.json"],
    },
    "gsa_study": {
        "argv": ["scripts/gsa_study.py", "--skip-companions"],
        "outputs": [
            "docs/decisions/adr0033-gsa-study-kp58_8_matrix.json",
            "docs/decisions/adr0033-gsa-study-kp60_0_matrix.json",
        ],
        "git_tracked": True,
    },
}

#: Volatile keys that are ignored when comparing a companion's fresh record
#: against its committed evidence file.
VOLATILE_JSON_KEYS = frozenset(
    {
        "generated",
        "generated_utc",
        "generated_by",
        "runtime_s",
        "runtime_seconds",
        "timestamp",
        "campaign",
        "elapsed_s",
        # config_hash moves by construction in this campaign (the ADR-0037
        # length_effect keys, section 1). It is asserted directly by G0 and G1,
        # so re-failing every companion on it here would be double-counting a
        # change we have already proven inert.
        "config_hash",
    }
)


#: Why an enumerated hit is NOT run by the companions stage. Every hit must be
#: classified here or the enumeration reports it as UNCLASSIFIED, which is the
#: signal to investigate rather than to widen this dict reflexively.
#:
#: Since 2026-08-10 an unclassified hit **fails** G6 (``gate_companion_
#: classification``) instead of merely being noted, so a new consumer of the
#: persisted sweeps stops the campaign until someone answers two questions in
#: this order: (a) should it RUN here? and only if no, (b) what actually
#: excludes it? A reason that would still be true of a file that SHOULD run is
#: not a reason -- say which gate runs it instead, or which input the campaign
#: deliberately does not produce.
COMPANION_EXCLUSIONS: dict[str, str] = {
    "scripts/production_campaign.py": (
        "this driver itself (it is the thing doing the asserting)"
    ),
    "scripts/run_sweep.py": (
        "produces the persisted sweeps; it is the source, not a consumer"
    ),
    "scripts/generate_configs.py": (
        "produces configs/; run as the campaign's FIRST stage, whose gate is "
        "the EMPTY-diff assertion on configs/*.yaml. Its config_hash match is "
        "a round-trip of what it just wrote (reloaded == in-memory), not a "
        "check against a persisted sweep. Source, not a consumer."
    ),
    "scripts/stage6_6_gap_decomposition.py": (
        "run as its own campaign stage (G3), not as a companion"
    ),
    "scripts/mp_model_factor_companion.py": (
        "ADR-0045 m_p companion: OFF in production (decision 3), KP58.8+KP60.0 "
        "only. Its hash gate reconstructs the Config from the sidecar's own "
        "config block, so it stays self-consistent across the hash change."
    ),
    "scripts/ztoe_sensitivity_study.py": (
        "ADR-0046 z_toe companion: OFF in production (decision 3). Same "
        "sidecar-reconstructed hash gate, so unaffected by the re-run."
    ),
    "scripts/prior_mean_scenario_companion.py": (
        "ADR-0048 prior-mean companion: OFF in production (decision 3). Same "
        "sidecar-reconstructed hash gate, so unaffected by the re-run."
    ),
    "bayesian_reliability_updating/pipeline.py": (
        "not a driver at all -- the shipped Phase 2 package module, which this "
        "campaign already executes as THREE of its own stages (phase2_baseline, "
        "phase2_anchor_rating, phase2_no_initiation), each `python -m "
        "bayesian_reliability_updating ... --verify` under G2. G2 gates the "
        "thing that matters: zero flag mismatches in the exact masked-vs-"
        "re-evaluation check, and every posterior replaying the freshly re-run "
        "Phase 1 hash. Its own regex match is the replay hash it STAMPS into "
        "the posterior sidecar; the gate that consumes it lives in replay.py "
        "and is what --verify exercises. Structurally unreachable from here in "
        "any case: COMPANION_COMMANDS keys resolve to scripts/<name>.py."
    ),
    "scripts/epistemic_bracket_synthesis.py": (
        "synthesises the 16 persisted ADR-0045/0046/0048 arm sweeps under "
        "results/sensitivity/, which the campaign deliberately does NOT "
        "produce (knobs OFF, decision 3) -- the same substantive ground as the "
        "three companion entries above. Running it here would be worse than "
        "redundant: absent an arm it records `available: false` and continues, "
        "so on a machine without those gitignored sweeps it exits 0 and G6's "
        "completion check would pass on a synthesis with every epistemic arm "
        "missing. Cost if ever wired: ~20 min (recorded 249/293/322/359 s for "
        "the four fresh baseline sweeps it gates on)."
    ),
    "scripts/hwl_bias_resolution.py": (
        "ADR-0040 resolution at N = 1e6. A cheap verification-only mode does "
        "exist -- `verify`, ~25 min (recorded 883.4 + 600.1 s) -- so this is "
        "NOT excluded on cost: it is excluded because that mode IMPORTS "
        "stage6_6_gap_decomposition.verify_against_production and calls it at "
        "kp62_0 and kp57_4, i.e. it re-asserts G3's own claim through G3's own "
        "function at G3's own two sections, and its G-A2 flip check is G3's "
        "third check. Its remaining stages are the evidence itself (brute "
        "alone 10188.9 + 4781.5 s = 4.2 h), which conventions section 10.2 "
        "classifies as evidence rather than a regenerable cache -- and "
        "`verify` overwrites files in that directory. Its `figures` "
        "subcommand IS already run by the campaign, in the figures stage "
        "under G7."
    ),
    "scripts/conductivity_annualisation_study.py": (
        "consumes the same ADR-0048 arm sweeps the campaign does not produce "
        "(decision 3); recorded as a deliberate non-entry when it was built "
        "(2026-08-10). Reason re-checked and widened the same day, when the "
        "bulk-d70 replication landed: it now consumes THIRTY-TWO arm sweeps, "
        "16 per grain-size reading, so the missing-arm exposure doubled while "
        "the substantive ground for excluding it is unchanged. Cheap in itself "
        "(recorded 8.0 s per reading) but it raises FileNotFoundError on a "
        "missing arm, so on any machine without those gitignored sweeps it "
        "would fail the campaign at a stage unrelated to the production "
        "deliverable. Its arm-independent Gate 1 (the baseline reproduces "
        "rq4_annual.csv over 228 rows x 20 fields, now once per reading) still "
        "has no gate-only entry point; adding one is the cheap way to make it "
        "campaign-runnable if that is ever wanted. Both its figures ARE "
        "re-drawn by the campaign, in the figures stage under G7."
    ),
    "scripts/canonical_shape_sensitivity_study.py": (
        "canonical-shape sensitivity (defence brief item A1, 2026-08-10). NOT a "
        "cost exclusion, though it is expensive (about 70 min: 16 production-N "
        "sweeps for the eight strata x two arms, a two-section comparator "
        "ladder, and a Uemura surface-curve regeneration). The substantive "
        "ground is that ALL THREE of its baseline gates are restatements of "
        "campaign gates on campaign artifacts, so running it here would "
        "re-assert this campaign's own claims through its own outputs -- the "
        "hwl_bias_resolution.py ground. Its gate 1 (each baseline arm "
        "bit-identical to the persisted sweep) is G1's claim; its gate 3 (the "
        "peak-referenced comparators bit-identical to results/stage6_6/) rests "
        "on the record G3 writes and verifies; and its Phase 3 baseline gate "
        "re-checks rq4_annual.csv, which is G4. What it adds beyond them is the "
        "ALTERNATE arm, i.e. a sensitivity, and sensitivities stay off per "
        "campaign decision 3. It also raises FileNotFoundError on a missing "
        "d4PDF workbook, persisted ladder or annual table, so on a machine "
        "without those gitignored inputs it would fail the campaign at a stage "
        "unrelated to the production deliverable. Its figure IS re-drawn by the "
        "campaign, in the figures stage under G7."
    ),
    "tests/test_canonical_shape_sensitivity.py": (
        "exercised by pytest, not by this stage -- the guard on the study "
        "above. It quotes the run stems and the phrase 'bit-identical', so it "
        "matches for the same self-referential reason its sibling guards do."
    ),
    "tests/test_config.py": "exercised by pytest, not by this stage",
    "tests/test_companion_enumeration_gate.py": (
        "exercised by pytest, not by this stage -- the guard on this very "
        "enumeration. It matched the moment it was written (its docstrings "
        "quote both the f-string stem and the phrase 'bit-identity'), which is "
        "the new gate firing on the first new hit that appeared after it."
    ),
    "tests/test_fragility.py": "exercised by pytest, not by this stage",
    "tests/test_phase2_end_to_end.py": "exercised by pytest, not by this stage",
}


def enumerate_companions() -> dict[str, Any]:
    """Grep scripts/, tests/ and the three packages for bit-identity consumers.

    Returns the programmatic enumeration (the campaign spec asks for this to
    be derived, not copied from a list), together with what the invocation
    table covers and what it does not. ``unclassified`` is the field that
    gates: see ``gate_companion_classification``.

    THIS ENUMERATION IS A FLOOR, NOT A CENSUS -- state it plainly rather than
    let a later reader infer a completeness the regex does not deliver. A file
    is reported only when it matches BOTH halves textually, so either half can
    be evaded:

    * *Path half.* Widened 2026-08-10 to plain ``tokachi_kp`` after
      ``scripts/conductivity_annualisation_study.py`` -- a genuine consumer
      that raises on ``config_hash`` drift -- slipped through by composing its
      stem as ``f"tokachi_kp{kp:.1f}_historical_{D70}"``: the old pattern
      required a literal digit where the f-string places ``{``. A stem built
      from smaller parts (``f"tokachi_{river}_kp..."``) would still evade it.
    * *Assertion half.* A file that reaches its bit-identity check through a
      helper whose name matches none of ``bit-ident`` / ``array_equal`` /
      ``config_hash`` / ``drift guard`` is invisible.
      ``scripts/segment_fragility.py`` is the live example of the second half
      and of why a non-match is not automatically a defect: it reads the
      sweeps by glob and is deliberately run as a companion, but it asserts
      nothing this regex recognises, so it appears under
      ``run_but_not_matched_by_the_regex`` rather than as a hit. That list is
      the superset direction (run here, not detected) and is benign -- running
      something undetected costs coverage, never correctness. The direction
      that matters is a consumer that is neither detected nor run, which is
      what the widening narrows and what this docstring admits is still
      possible.
    """
    import re

    roots = [
        REPO / "scripts",
        REPO / "tests",
        REPO / "bep_reliability_engine",
        REPO / "bayesian_reliability_updating",
        REPO / "system_integration",
    ]
    path_pat = re.compile(r"results/tokachi_kp|tokachi_kp", re.I)
    assert_pat = re.compile(
        r"bit[-_ ]ident|array_equal|assert_array_equal|config_hash|drift.?guard",
        re.I,
    )
    hits: dict[str, dict[str, Any]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            refs_sweeps = bool(path_pat.search(text))
            asserts = bool(assert_pat.search(text))
            if refs_sweeps and asserts:
                rel = str(path.relative_to(REPO)).replace("\\", "/")
                hits[rel] = {
                    "references_persisted_sweeps": refs_sweeps,
                    "has_bit_identity_or_hash_assertion": asserts,
                }
    covered = {f"scripts/{name}.py" for name in COMPANION_COMMANDS}
    not_run = sorted(set(hits) - covered)
    unclassified = sorted(p for p in not_run if p not in COMPANION_EXCLUSIONS)
    stale_exclusions = sorted(
        path for path in COMPANION_EXCLUSIONS if not (REPO / path).is_file()
    )
    return {
        "method": (
            "regex over scripts/, tests/ and the three packages for a "
            "persisted-sweep path reference AND a bit-identity / config-hash "
            "assertion pattern"
        ),
        "detection_is_a_floor_not_a_census": (
            "both halves are textual and either can be evaded; see the "
            "enumerate_companions docstring for the two known routes"
        ),
        "hits": hits,
        "covered_by_this_stage": sorted(covered & set(hits)),
        "found_but_not_run_here": {
            path: COMPANION_EXCLUSIONS.get(path, "UNCLASSIFIED -- investigate")
            for path in not_run
        },
        "unclassified": unclassified,
        "exclusions_with_no_file_on_disk": stale_exclusions,
        "run_but_not_matched_by_the_regex": sorted(covered - set(hits)),
    }


def gate_companion_classification(gates: Gates, enumeration: dict[str, Any]) -> None:
    """Fail G6 when a hit carries no classification, or a reason no file.

    The enforcement half of the enumeration. Before 2026-08-10 the enumeration
    reached the manifest only through ``gates.note``, and G6's sole assertion
    was that every companion which *runs* completes -- so a hit that was
    neither run nor excluded was recorded as ``UNCLASSIFIED -- investigate``
    and could never fail anything. Three accumulated that way across four
    sessions. This is the third instance of the class closed twice already:
    the 13 test guards that skipped on a tracked path (repo audit section
    12.4) and the Stage 6.6 driver gate that recorded a non-verifying status
    and continued (section 12.8). Each time the fix was the same: make the
    recorded outcome refuse.

    Both directions are gated, because both silently classify nothing:

    * a **hit with no classification** -- a new consumer of the persisted
      sweeps, which is exactly what this enumeration exists to catch, so it
      must fail loudly rather than pass silently (the 2026-07-29 asymmetric-
      allowlist precedent: additive facts are recorded and pass, a new
      unexplained one does not);
    * an **exclusion key naming no file on disk** -- a rename or deletion
      leaves a reason behind that reads as a classification but classifies
      nothing, and would mask the renamed file's own reappearance as a hit.

    Called before the companion subprocesses, not after: the verdict is
    decidable from source alone, so an unclassified consumer refuses in
    milliseconds rather than after ~40 minutes of companions. Nothing has been
    written at that point, so this is not the conventions section 9.4
    persist-then-gate case -- there is no evidence for the gate to destroy.
    """
    gates.check(
        "G6",
        "every enumerated bit-identity consumer is classified (run by this "
        "stage, or carrying an explicit COMPANION_EXCLUSIONS reason)",
        not enumeration["unclassified"],
        {
            "unclassified": enumeration["unclassified"],
            "remedy": (
                "answer (a) should it RUN as a campaign companion? -- and only "
                "if no, (b) what actually excludes it. Add to "
                "COMPANION_COMMANDS or COMPANION_EXCLUSIONS accordingly."
            ),
        },
    )
    gates.check(
        "G6",
        "every COMPANION_EXCLUSIONS key still names a file on disk",
        not enumeration["exclusions_with_no_file_on_disk"],
        {"stale_keys": enumeration["exclusions_with_no_file_on_disk"]},
    )


def _tracked_figure_state() -> dict[str, str | None]:
    """SHA-256 of every git-tracked file under docs/figures/."""
    listed = subprocess.run(
        ["git", "ls-files", "docs/figures"], cwd=REPO, capture_output=True, text=True
    ).stdout.split()
    return {rel: sha256_of(REPO / rel) for rel in listed}


def stage_companions(ctx: "Context") -> dict[str, Any]:
    """Run every enumerated bit-identity companion; a failing assert is a gate.

    G6 gates twice. ``gate_companion_classification`` runs first and refuses
    when the enumeration finds a consumer that is neither run here nor
    explicitly excluded; the completion check below then requires every
    companion that does run to finish with its own asserts holding. The first
    without the second would let a new consumer be recorded and ignored, which
    is how three accumulated before 2026-08-10.

    Two of them (``ce_prior_study``, ``gsa_study``) render figures as a side
    effect and offer no skip flag. Figure regeneration is explicitly out of
    scope for this campaign (it is a separate pass), so any tracked figure they
    touch is restored from git afterwards and the fact is recorded.
    """
    gates = Gates("companions")
    enumeration = enumerate_companions()
    # The note is the evidence, the check is the enforcement; keep both. The
    # check runs first because it is free and its failure means the campaign's
    # own census of bit-identity consumers is out of date.
    gates.note("G6", "programmatic companion enumeration", enumeration)
    gate_companion_classification(gates, enumeration)
    figures_before = _tracked_figure_state()

    (CAMPAIGN_DIR / "companions").mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    per_companion: dict[str, Any] = {}
    failed: list[str] = []
    for name, spec in COMPANION_COMMANDS.items():
        print(f"  -- {name}", flush=True)
        record = run_command(
            [PY, *spec["argv"]],
            label=f"companion_{name}",
            log_path=ctx.log_dir / f"companion_{name}.log",
        )
        commands.append(record)
        entry: dict[str, Any] = {"returncode": record["returncode"]}
        if record["returncode"] != 0:
            failed.append(name)
            entry["stderr_tail"] = record.get("stderr_tail")
        compare_to = spec.get("compare_to")
        if compare_to and record["returncode"] == 0:
            fresh = REPO / spec["outputs"][0]
            entry["reproduces_committed_evidence"] = _json_equal_ignoring_volatile(
                fresh, REPO / compare_to
            )
            entry["compared_to"] = compare_to
        if spec.get("git_tracked") and record["returncode"] == 0:
            diff = subprocess.run(
                ["git", "diff", "--stat", "--", *spec["outputs"]],
                cwd=REPO,
                capture_output=True,
                text=True,
            )
            entry["git_diff_stat"] = diff.stdout.strip() or "(no change)"
            entry["reproduces_committed_evidence"] = not diff.stdout.strip()
        per_companion[name] = entry

    # Restore any tracked figure a companion rewrote (out of scope this pass).
    figures_after = _tracked_figure_state()
    touched = sorted(
        rel
        for rel, digest in figures_after.items()
        if figures_before.get(rel) != digest
    )
    if touched:
        subprocess.run(["git", "checkout", "--", *touched], cwd=REPO, check=False)
    gates.note(
        "G6",
        "tracked figures rewritten by a companion and restored from git",
        {"restored": touched} if touched else "none touched",
    )

    gates.check(
        "G6",
        "every bit-identity companion runs to completion (its own asserts hold)",
        not failed,
        {"companions_failing": failed, "per_companion": per_companion},
    )

    outputs: list[Path] = []
    for spec in COMPANION_COMMANDS.values():
        outputs.extend(REPO / p for p in spec["outputs"])
    return {
        "commands": commands,
        "gates": gates.records,
        "outputs": describe_outputs(outputs),
        "enumeration": enumeration,
        "per_companion": per_companion,
        "figures_restored": touched,
    }


def _strip_volatile(node: Any) -> Any:
    if isinstance(node, dict):
        return {
            k: _strip_volatile(v)
            for k, v in node.items()
            if k not in VOLATILE_JSON_KEYS
        }
    if isinstance(node, list):
        return [_strip_volatile(v) for v in node]
    return node


def _json_equal_ignoring_volatile(a: Path, b: Path) -> dict[str, Any] | None:
    """Classify fresh-vs-committed evidence, ignoring timestamp-ish keys.

    Uses the same asymmetry as G1: a block the fresh record *gained* because
    the committed artifact was produced with a stage skipped does not
    contradict the record. The 2026-07-29 campaign hit exactly one -- the R10
    evidence was committed with ``--no-ensemble``, so its ``d4pdf_ensemble``
    is an explicit null that this campaign filled in. A block whose value
    MOVED is a real difference and is reported as CHANGED.
    """
    if not (a.is_file() and b.is_file()):
        return None
    fresh = _strip_volatile(json.loads(a.read_text(encoding="utf-8")))
    committed = _strip_volatile(json.loads(b.read_text(encoding="utf-8")))
    if fresh == committed:
        return {
            "verdict": "identical",
            "changed_keys": [],
            "additive_keys": [],
            "omitted_keys": [],
        }

    changed: list[str] = []
    additive: list[str] = []
    omitted: list[str] = []
    if isinstance(fresh, dict) and isinstance(committed, dict):
        for key in sorted(set(fresh) | set(committed)):
            if fresh.get(key) == committed.get(key):
                continue
            if key not in fresh:
                # This invocation ran a narrower stage set than the committed
                # record was produced with; absence is scope, not a change.
                omitted.append(key)
            elif committed.get(key) is None:
                additive.append(key)
            else:
                changed.append(key)
    else:
        changed.append("<root>")
    return {
        "verdict": "identical_plus_additions" if not changed else "CHANGED",
        "changed_keys": changed,
        "additive_keys": additive,
        "omitted_keys": omitted,
    }


def _git_tracked_evidence_verdict(rel: str) -> dict[str, Any]:
    """Classify a companion that rewrites its own git-tracked evidence file.

    Compares the working-tree file against ``HEAD`` with volatile keys
    stripped. When the only movement is volatile (runtimes, timestamps) the
    file is restored from git: the document of record should not churn on
    timing noise, and leaving it dirty would misrepresent a reproduction as a
    change.
    """
    head = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    path = REPO / rel
    if head.returncode != 0 or not path.is_file():
        return {
            "verdict": "CHANGED",
            "changed_keys": ["<unreadable>"],
            "additive_keys": [],
        }
    fresh = _strip_volatile(json.loads(path.read_text(encoding="utf-8")))
    committed = _strip_volatile(json.loads(head.stdout))
    if fresh == committed:
        subprocess.run(["git", "checkout", "--", rel], cwd=REPO, check=False)
        return {
            "verdict": "identical",
            "changed_keys": [],
            "additive_keys": [],
            "note": (
                "substantive content identical; volatile-only diff " "restored from git"
            ),
        }
    changed = [
        k
        for k in sorted(set(fresh) | set(committed))
        if fresh.get(k) != committed.get(k)
    ]
    return {"verdict": "CHANGED", "changed_keys": changed, "additive_keys": []}


# --------------------------------------------------------------------------- #
# Stage 7 -- G5 diagnostics                                                     #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Stage -- publication figures (regenerate, then assert freshness)              #
# --------------------------------------------------------------------------- #

#: Every publication figure, with the artifact it depicts. ``requires`` lists the
#: inputs that must exist for the driver to work at all (several live under the
#: gitignored ``results/`` or ``data/raw/``, so a fresh clone skips them rather
#: than failing). ``produces`` are glob patterns under ``docs/figures/``.
#: ``sources`` is what the figure depicts -- the staleness gate compares every
#: produced figure against the newest source.
#:
#: Two kinds of entry (2026-07-31, closing the 44-of-52 coverage gap):
#:
#: * ``command`` is a driver with a *cheap redraw path*: it reads persisted
#:   evidence and re-renders, running no physics. The stage runs it, so its
#:   figures are always fresh.
#: * ``command`` is ``None`` -- **declaration only**. The study has no plot-only
#:   path, so nothing is executed; the entry exists to bind the figure to its
#:   source for the staleness gate and to record, in ``redraw``, what re-running
#:   would cost. All eight were verified content-current on 2026-07-31 before
#:   being declared.
#:
#: Two optional keys, both used only by declaration-only entries:
#:
#: * ``source_epoch: "json_generated"`` reads the evidence JSON's own
#:   ``generated`` stamp instead of its filesystem mtime. Needed where both the
#:   figure and its evidence are *tracked* files: git writes them at checkout or
#:   commit time independently, so mtime is not a content signal (ADR-0039 --
#:   its JSON records ``generated: 2026-07-13T07:53:42``, 3.6 min before the
#:   figure, yet carries a 2026-07-17 mtime from the single commit, 780eb0d,
#:   that added both).
#: * ``staleness`` records why an entry declares ``sources: []`` -- i.e. is
#:   explicitly outside the staleness gate because no artifact with a meaningful
#:   mtime exists to bind to. Never a silent omission.
#:
#: Note on gate ordering: every driver here WRITES its figures before this stage
#: gates on their timestamps, so an alarm can never destroy the artifact it is
#: raised about (the 2026-07-30 lesson from `hwl_bias_resolution.cmd_brute`).
FIGURE_DRIVERS: list[dict[str, Any]] = [
    {
        "label": "phase1 fragility curves",
        "command": [PY, "scripts/plot_fragility_curves.py"],
        "requires": ["results/tokachi_kp62.0_historical_matrix.h5"],
        "produces": ["fragility_*.png"],
        "sources": ["results/tokachi_kp*_historical_*.h5"],
    },
    {
        "label": "stage 6.6 (redraw only)",
        "command": [
            PY,
            "scripts/stage6_6_gap_decomposition.py",
            "--figures-only",
        ],
        "requires": ["results/stage6_6/stage6_6_kp62_0.h5"],
        "produces": ["stage6_6_*.png"],
        "sources": [
            "results/stage6_6/stage6_6_kp*.h5",
            "results/stage6_6/stage6_6_kp*_analysis.json",
        ],
    },
    {
        "label": "phase 3 RQ3+RQ4",
        "command": [PY, "scripts/phase3_figures.py"],
        "requires": ["results/system_integration/phase3/rq4_annual.csv"],
        "produces": ["phase3_*.png"],
        "sources": [
            "results/system_integration/phase3/*.json",
            "results/system_integration/phase3/rq4_annual.csv",
        ],
    },
    {
        "label": "seepage-length L study",
        "command": [PY, "scripts/seepage_length_figures.py"],
        "requires": ["docs/decisions/seepage-length-L-study.md"],
        "produces": ["seepage_length_*.png"],
        "sources": ["results/sensitivity/seepage_length/*.json"],
    },
    {
        "label": "design-HWL bias resolution",
        "command": [PY, "scripts/hwl_bias_resolution.py", "figures"],
        "requires": ["docs/decisions/adr0040-hwl-bias-resolution.json"],
        # Exact names, not ``adr0040_*.png``: the thesis-figure-gaps driver
        # below owns adr0040_kp57_4_bound.png, and a glob that swept it up
        # would bind it to the wrong driver's sources and leave it un-redrawn.
        "produces": [
            "adr0040_hwl_bias_resolved.png",
            "adr0040_tilted_is_validation.png",
            "epistemic_vs_statistical.png",
        ],
        "sources": [
            "docs/decisions/adr0040-hwl-bias-resolution.json",
            "docs/decisions/epistemic-bracket-synthesis.json",
        ],
    },
    {
        "label": "thesis figure gaps (six inventory numbers)",
        "command": [PY, "scripts/thesis_figure_gaps.py", "figures"],
        # Every input is committed, so this driver never skips on a fresh
        # clone. The three slices are written by the same script's ``extract``
        # command from gitignored campaign artifacts; each records the source
        # SHA-256, and tests/test_thesis_figure_gaps.py checks it against the
        # live artifact whenever that artifact is present.
        "requires": [
            "docs/decisions/phase2-survival-update-per-stratum.json",
            "docs/decisions/phase2-peak-shortcut.json",
            "docs/decisions/phase3-sensitivity-brackets.json",
            "docs/decisions/epistemic-bracket-synthesis.json",
            "docs/decisions/adr0040-hwl-bias-resolution.json",
            "docs/decisions/adr0045-mp-companion.json",
            "docs/decisions/adr0046-ztoe-companion.json",
            "docs/decisions/adr0040-stage6-6-kp62_0-analysis.json",
        ],
        "produces": [
            "phase2_survival_update.png",
            "phase2_peak_shortcut.png",
            "epistemic_bracket_ranking.png",
            "adr0040_kp57_4_bound.png",
            "rq4_sensitivity_brackets.png",
            "epistemic_knobs_mp_ztoe.png",
        ],
        "sources": [
            "docs/decisions/phase2-survival-update-per-stratum.json",
            "docs/decisions/phase2-peak-shortcut.json",
            "docs/decisions/phase3-sensitivity-brackets.json",
            "docs/decisions/epistemic-bracket-synthesis.json",
            "docs/decisions/adr0040-hwl-bias-resolution.json",
            "docs/decisions/adr0045-mp-companion.json",
            "docs/decisions/adr0046-ztoe-companion.json",
            "docs/decisions/adr0040-stage6-6-kp62_0-analysis.json",
        ],
    },
    {
        # Inventory rows 4.3, 4.4 and 5.1. These four are rendered by the Phase
        # 2 package itself through the ``pipeline.PUBLICATION_FIGURES`` dual-write
        # seam, not by a script under scripts/. ``--figures-only`` recomputes the
        # posterior in memory from its Phase 1 parent and writes NO artifact --
        # the persisted posteriors, whose SHA-256 this campaign's manifest
        # records, are asserted byte-identical across it.
        #
        # It is the slowest redraw path here (about 5.7 min for the two strata,
        # because the seam sits downstream of a full 1e5-row replay). Declaring
        # it declaration-only would have been cheaper and wrong: a real plot-only
        # path exists, so the four figures can be kept unconditionally fresh
        # rather than merely watched.
        "label": "Phase-2 posterior diagnostics (figures-only)",
        "command": [
            PY,
            "-m",
            "bayesian_reliability_updating",
            "results/tokachi_kp58.8_historical_matrix.h5",
            "results/tokachi_kp60.0_historical_matrix.h5",
            "--figures-only",
        ],
        "requires": [
            "results/tokachi_kp58.8_historical_matrix.h5",
            "results/tokachi_kp60.0_historical_matrix.h5",
            # The h_2016 chain: gitignored gauge rating + committed extracts.
            "data/raw/rating_curves/HQrelation_TokachiRiv_2017.csv",
            "data/processed/2016_event/stage_hourly_Tokachi_201608.csv",
            "data/processed/2016_event/flood_trace_2016.csv",
        ],
        "produces": [
            "phase2_marginals_kp58_8_matrix.png",
            "phase2_marginals_kp60_0_matrix.png",
            "phase2_fragility_update_kp58_8_matrix.png",
            "phase2_fragility_update_kp60_0_matrix.png",
        ],
        # What the figures depict: the Phase 1 parents they are recomputed from,
        # the persisted posteriors a reader compares them against, and the
        # observed record that drives the update. Exact paths, not a
        # results/phase2/*.json glob, which would bind these four to the other
        # six strata as well.
        "sources": [
            "results/tokachi_kp58.8_historical_matrix.h5",
            "results/tokachi_kp60.0_historical_matrix.h5",
            "results/phase2/tokachi_kp58.8_historical_matrix_posterior.json",
            "results/phase2/tokachi_kp60.0_historical_matrix_posterior.json",
            "data/processed/2016_event/stage_hourly_Tokachi_201608.csv",
            "data/processed/2016_event/flood_trace_2016.csv",
        ],
    },
    {
        "label": "ADR-0047 DEM seepage length (draw only)",
        "command": [PY, "scripts/dem_cross_section_study.py", "figure"],
        "requires": ["data/raw/geometry/dem_cross_sections/_mosaic_cache.npz"],
        "produces": ["adr0047_dem_seepage_length.png"],
        "sources": ["docs/decisions/adr0047-dem-seepage-length.json"],
    },
    {
        "label": "ADR-0033 GSA (plot only)",
        "command": [PY, "scripts/gsa_study.py", "--plot-only"],
        "requires": ["docs/decisions/adr0033-gsa-study-kp58_8_matrix.json"],
        "produces": ["gsa_*.png"],
        "sources": ["docs/decisions/adr0033-gsa-study*.json"],
    },
    {
        "label": "ADR-0031 convergence (plot only)",
        "command": [PY, "scripts/convergence_study.py", "--plot-only"],
        "requires": ["docs/decisions/adr0031-convergence-study.json"],
        "produces": ["adr0031-*.png"],
        "sources": ["docs/decisions/adr0031-convergence-study*.json"],
    },
    {
        "label": "Japanese case validation (Yabe)",
        "command": [PY, "scripts/plot_validation_yabe.py"],
        "requires": ["results/validation_yabe/validation_results.json"],
        "produces": ["validation_yabe_*.png"],
        "sources": ["results/validation_yabe/validation_results.json"],
    },
    {
        "label": "Japanese case validation (Gounokawa)",
        "command": [PY, "scripts/plot_validation_gounokawa.py"],
        "requires": ["results/validation_gounokawa/validation_results.json"],
        "produces": ["validation_gounokawa_*.png"],
        "sources": ["results/validation_gounokawa/validation_results.json"],
    },
    {
        "label": "Japanese case validation (Shikaga)",
        "command": [PY, "scripts/plot_validation_shikaga.py"],
        "requires": ["results/validation_shikaga/validation_results.json"],
        "produces": ["validation_shikaga_*.png"],
        "sources": ["results/validation_shikaga/validation_results.json"],
    },
    {
        # Companion study, not a campaign stage: it consumes the gitignored
        # ADR-0048 prior-mean arm sweeps, which this campaign deliberately does
        # not produce (the epistemic knobs stay OFF, campaign decision 3). Only
        # its figure is declared here, and it has a real plot-only path --
        # ``--figures-only`` re-renders from the committed evidence record and
        # writes no evidence file -- so the figure is kept unconditionally
        # fresh rather than merely watched.
        "label": "conductivity bracket through the annualisation (figures only)",
        "command": [
            PY,
            "scripts/conductivity_annualisation_study.py",
            "--figures-only",
        ],
        "requires": ["docs/decisions/conductivity-bracket-annualisation.json"],
        # Exact name, not a glob. A ``conductivity_*`` glob would now sweep up
        # the bulk figure declared below, bind it to this entry's sources and
        # leave it un-redrawn -- the trap the 2026-07-31 pass recorded for the
        # shared C_e glob, and the reason the sibling arrived without incident.
        "produces": ["conductivity_bracket_annual.png"],
        "sources": ["docs/decisions/conductivity-bracket-annualisation.json"],
    },
    {
        # The bulk-d70 replication (2026-08-10, note Part 3). Separate entry
        # rather than a second ``produces`` on the one above, because this
        # figure is the CROSS-READING comparison and so depends on BOTH
        # committed records: staleness in either must re-draw it.
        "label": "conductivity bracket, both grain-size readings (figures only)",
        "command": [
            PY,
            "scripts/conductivity_annualisation_study.py",
            "--d70",
            "bulk",
            "--figures-only",
        ],
        "requires": [
            "docs/decisions/conductivity-bracket-annualisation-bulk.json",
            "docs/decisions/conductivity-bracket-annualisation.json",
        ],
        "produces": ["conductivity_bracket_both_d70.png"],
        "sources": [
            "docs/decisions/conductivity-bracket-annualisation-bulk.json",
            "docs/decisions/conductivity-bracket-annualisation.json",
        ],
    },
    {
        # Canonical-shape sensitivity (defence brief item A1, 2026-08-10). A
        # real redraw path: ``figures`` renders from the committed evidence
        # record and returns before any stage runs, so it writes no evidence
        # file and re-runs no sweep. Exact filename, never a glob.
        "label": "canonical hydrograph shape sensitivity (figures only)",
        "command": [
            PY,
            "scripts/canonical_shape_sensitivity_study.py",
            "figures",
        ],
        "requires": ["docs/decisions/canonical-shape-sensitivity.json"],
        "produces": ["canonical_shape_sensitivity.png"],
        "sources": ["docs/decisions/canonical-shape-sensitivity.json"],
    },
    # ---- declaration only (no plot-only path); see the module note above ---- #
    {
        "label": "ADR-0012 k_aq-d70 scatter (declaration only)",
        "command": None,
        "redraw": (
            "no producing script exists in this repository. The scatter was "
            "drawn externally on 2026-07-02 by the analysis that became "
            "docs/decisions/adr0012-kaq-d70-analysis.md, performed without repo "
            "access (its own provenance note, section 0, says so). A trip here "
            "means the paired-specimen table changed and the figure has to be "
            "redrawn by hand."
        ),
        "requires": ["docs/decisions/adr0012-kaq-d70-analysis.md"],
        "produces": ["adr0012-kaq-d70-scatter.png"],
        # The figure depicts the 8 OYO paired records, which exist nowhere as
        # data: they are transcribed into section 1 of the note, from the
        # gitignored 1999 OYO form-4 soil-test PDFs. The note IS the artifact.
        "sources": ["docs/decisions/adr0012-kaq-d70-analysis.md"],
    },
    {
        "label": "ADR-0029 tail-variance study (declaration only)",
        "command": None,
        "redraw": (
            "scripts/tail_variance_study.py has no plot-only path; re-running "
            "it is a full KP 58.8 replicate sweep with tilted-IS estimation."
        ),
        "requires": ["docs/decisions/adr0029-tail-cov-study.json"],
        "produces": ["adr0029-tail-cov.png"],
        "sources": ["docs/decisions/adr0029-tail-cov-study.json"],
    },
    {
        "label": "ADR-0032 aquifer response (declaration only)",
        "command": None,
        "redraw": (
            "scripts/aquifer_response_diagnostic.py has no plot-only path and "
            "needs the gitignored d4PDF band workbooks."
        ),
        "requires": ["docs/decisions/adr0032-aquifer-response-diagnostic.md"],
        "produces": ["adr0032_aquifer_response.png"],
        "sources": [],
        "staleness": (
            "outside the staleness gate: the study writes no evidence artifact "
            "-- only the figure. Its inputs are the two governing configs and "
            "the immutable gitignored d4PDF workbooks, and configs/ is rewritten "
            "unconditionally by this campaign's own configs stage, so a config "
            "mtime carries no content signal. Currency is pinned instead by "
            "identity of tau_aq_central_s (680 s at KP 58.8, 765 s at KP 60.0) "
            "between the figure's companion note and every run-stamped "
            "metadata['aquifer_response'] block."
        ),
    },
    {
        # Promoted from declaration-only on 2026-08-04 by the main-body figure
        # register pass: ``--figures-only`` rebuilds just the showcase
        # trajectories from the persisted ladder and writes NO evidence file,
        # which also retires the overwriting-per-section hazard the 2026-07-31
        # audit recorded here (a --quick payload can no longer reach the
        # production record through the figure path, and the two flags are
        # mutually exclusive).
        "label": "ADR-0039 worst-case timestep stress (figures only)",
        "command": [
            PY,
            "scripts/timestep_convergence_stress.py",
            "--figures-only",
        ],
        "requires": [
            "docs/decisions/adr0039-timestep-stress.json",
            # One d4PDF workbook read per section, to recover the two members
            # the evidence names; no ensemble ranking, no Delta-t ladder.
            "data/raw/hydrographs",
        ],
        "produces": ["adr0039-timestep-stress.png"],
        "sources": ["docs/decisions/adr0039-timestep-stress.json"],
        # Both files are tracked and were added by one commit (780eb0d) whose
        # write left the JSON with a 2026-07-17 mtime and the figure with its
        # 2026-07-13 one. The JSON's own generated stamp (2026-07-13T07:53:42)
        # is the content date, and it precedes the figure by 3.6 min.
        "source_epoch": "json_generated",
    },
    {
        "label": "ADR-0026 C_e prior reconciliation (declaration only)",
        "command": None,
        "redraw": "scripts/ce_prior_study.py has no plot-only path.",
        "requires": ["results/sensitivity/ce_prior/prior_reconciliation.json"],
        "produces": ["ce_prior_reconciliation.png"],
        "sources": ["results/sensitivity/ce_prior/prior_reconciliation.json"],
    },
    {
        "label": "ADR-0026 C_e fragility propagation (declaration only)",
        "command": None,
        "redraw": (
            "scripts/ce_prior_study.py has no plot-only path; this stage is a "
            "CRN column-swap sweep at both informative matrix sections."
        ),
        "requires": ["results/sensitivity/ce_prior/fragility_propagation.json"],
        "produces": ["ce_prior_fragility_propagation.png"],
        # Deliberately one entry per C_e figure: the three stages ran on
        # different dates, so a shared results/sensitivity/ce_prior/*.json glob
        # would measure each figure against the newest of the three.
        "sources": ["results/sensitivity/ce_prior/fragility_propagation.json"],
    },
    {
        "label": "ADR-0026 C_e Phase 2 sensitivity (declaration only)",
        "command": None,
        "redraw": (
            "scripts/ce_prior_study.py has no plot-only path; this stage "
            "replays the Phase 2 survival update under each candidate prior."
        ),
        "requires": ["results/sensitivity/ce_prior/phase2_survival_sensitivity.json"],
        "produces": ["ce_prior_phase2_sensitivity.png"],
        "sources": ["results/sensitivity/ce_prior/phase2_survival_sensitivity.json"],
    },
    {
        "label": "R10 foreshore-exhaustion screening (declaration only)",
        "command": None,
        "redraw": (
            "scripts/foreshore_exhaustion_study.py renders only as a side "
            "effect of a full run (--no-figure suppresses it); the campaign "
            "runs it that way as a bit-identity companion."
        ),
        "requires": ["docs/decisions/r10-foreshore-exhaustion-screening.json"],
        "produces": ["r10_foreshore_exhaustion.png"],
        "sources": ["docs/decisions/r10-foreshore-exhaustion-screening.json"],
    },
]


def _json_generated_epoch(path: Path) -> float | None:
    """Epoch of an evidence JSON's own ``generated`` stamp, or ``None``.

    The content date of an artifact that records when it was produced. Immune
    to the git write that resets a *tracked* file's mtime at checkout or commit
    time, which is why ADR-0039's figure/evidence pair needs it.
    """
    try:
        stamp = json.loads(path.read_text(encoding="utf-8")).get("generated")
    except (OSError, ValueError):
        return None
    if not isinstance(stamp, str):
        return None
    try:
        return datetime.fromisoformat(stamp).timestamp()
    except ValueError:
        return None


def _newest(patterns: list[str], *, epoch: str = "mtime") -> tuple[float, str | None]:
    """Newest timestamp among the files matching any pattern, and which file.

    ``epoch='json_generated'`` prefers each file's own recorded ``generated``
    stamp, falling back to mtime where it has none.
    """
    newest, which = 0.0, None
    for pattern in patterns:
        for path in REPO.glob(pattern):
            if not path.is_file():
                continue
            stamp = _json_generated_epoch(path) if epoch == "json_generated" else None
            if stamp is None:
                stamp = path.stat().st_mtime
            if stamp > newest:
                newest, which = stamp, str(path.relative_to(REPO)).replace("\\", "/")
    return newest, which


def stage_figures(ctx: "Context") -> dict[str, Any]:
    """Regenerate every redrawable publication figure, then gate on staleness.

    The gate is the structural fix for the copy problem: a figure that is older
    than the artifact it depicts fails the campaign, so the 2026-07-29 and
    2026-07-30 cases (Stage 6.6 KP 62.0 rendered before its own ladder re-run)
    cannot recur silently.

    Declaration-only entries (``command`` is ``None``) are not executed: they
    contribute their ``sources`` binding to the staleness gate and their
    ``produces`` names to the coverage check, which is how the eight figures
    whose studies have no plot-only path became gated without being re-run.
    """
    gates = Gates("figures")
    before = _tracked_figure_state()
    commands: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    declaration_only: list[dict[str, Any]] = []

    for driver in FIGURE_DRIVERS:
        if driver["command"] is None:
            declaration_only.append(
                {
                    "label": driver["label"],
                    "figures": driver["produces"],
                    "evidence_present": all(
                        (REPO / r).exists() for r in driver["requires"]
                    ),
                    "redraw": driver["redraw"],
                }
            )
            continue
        missing = [r for r in driver["requires"] if not (REPO / r).exists()]
        if missing:
            skipped.append({"label": driver["label"], "missing": ", ".join(missing)})
            print(f"    -- skipped {driver['label']} (missing {missing[0]})")
            continue
        record = run_command(
            driver["command"],
            label=driver["label"],
            log_path=ctx.log_dir / f"figures_{driver['label'].split()[0]}.log",
        )
        commands.append(record)
        gates.check(
            "G7",
            f"{driver['label']} driver exits 0",
            record["returncode"] == 0,
            record,
        )

    # Staleness: per driver, every figure it owns must be at least as new as the
    # newest artifact it depicts.
    stale: list[dict[str, Any]] = []
    checked = 0
    waived: list[dict[str, Any]] = []
    for driver in FIGURE_DRIVERS:
        if not driver["sources"]:
            waived.append(
                {
                    "label": driver["label"],
                    "figures": driver["produces"],
                    "reason": driver["staleness"],
                }
            )
            continue
        source_mtime, source_file = _newest(
            driver["sources"], epoch=driver.get("source_epoch", "mtime")
        )
        if source_mtime == 0.0:
            continue
        for pattern in driver["produces"]:
            for figure in sorted((REPO / "docs" / "figures").glob(pattern)):
                checked += 1
                if figure.stat().st_mtime + 1.0 < source_mtime:
                    stale.append(
                        {
                            "figure": f"docs/figures/{figure.name}",
                            "driver": driver["label"],
                            "newest_source": source_file,
                            "figure_age_s": round(
                                source_mtime - figure.stat().st_mtime, 1
                            ),
                        }
                    )
    gates.check(
        "G7",
        "no publication figure is older than the artifact it depicts",
        not stale,
        {"checked": checked, "stale": stale},
    )

    mapped = {
        f"docs/figures/{p.name}"
        for driver in FIGURE_DRIVERS
        for pattern in driver["produces"]
        for p in (REPO / "docs" / "figures").glob(pattern)
    }
    unmapped = sorted(set(before) - mapped)
    gates.check(
        "G7",
        "every tracked publication figure is declared in FIGURE_DRIVERS",
        not unmapped,
        {"count": len(unmapped), "figures": unmapped, "declared": len(mapped)},
    )
    gates.note(
        "G7",
        "declared but not redrawn (no plot-only path; re-run their study)",
        {"count": len(declaration_only), "drivers": declaration_only},
    )
    gates.note(
        "G7",
        "declared but outside the staleness gate (no artifact to bind to)",
        {"count": len(waived), "drivers": waived},
    )
    after = _tracked_figure_state()
    return {
        "commands": commands,
        "skipped_drivers": skipped,
        "figures_checked": checked,
        "figures_changed": sorted(
            rel for rel, digest in after.items() if before.get(rel) != digest
        ),
        "figures_declared": len(mapped),
        "figures_unmapped": unmapped,
        "figures_declaration_only": declaration_only,
        "figures_staleness_waived": waived,
        "gates": gates.records,
    }


def stage_diagnostics(ctx: "Context") -> dict[str, Any]:
    """Collect, per run, every diagnostic G5 asks for. Reporting, not gating.

    Deviations from a target here are read against their documented regimes
    (ADR-0024 raw tail for the CoV, ADR-0032 for Pi) rather than treated as
    failures -- G5 says "report", and the campaign document carries the
    interpretation.
    """
    gates = Gates("diagnostics")
    results = REPO / "results"
    per_run: dict[str, Any] = {}
    for stem in SECTIONS:
        sidecar = results / f"{stem}.json"
        if not sidecar.is_file():
            per_run[stem] = {"status": "missing"}
            continue
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        mc = meta.get("mc_convergence", {})
        aq = meta.get("aquifer_response", {})
        deliverable = meta.get("fragility_deliverable", {})
        cov_static = [c for c in mc.get("cov_pf_static", []) or [] if c is not None]
        cov_trans = [c for c in mc.get("cov_pf_trans", []) or [] if c is not None]
        per_run[stem] = {
            "config_hash": meta.get("config_hash"),
            "progression_backend": meta.get("progression_backend"),
            "hydrograph_source": meta.get("hydrograph_source"),
            "length_effect_present": "length_effect" in meta,
            "mc_convergence": {
                "n_realizations": mc.get("n_realizations"),
                "cov_target": mc.get("cov_target", PF_COV_TARGET),
                "max_cov_static": mc.get("max_cov_static"),
                "max_cov_trans": mc.get("max_cov_trans"),
                "meets_cov_target_static": mc.get("meets_cov_target_static"),
                "meets_cov_target_trans": mc.get("meets_cov_target_trans"),
                "n_levels_over_target_static": sum(
                    1 for c in cov_static if c > PF_COV_TARGET
                ),
                "n_levels_over_target_trans": sum(
                    1 for c in cov_trans if c > PF_COV_TARGET
                ),
                "n_interior_levels_static": len(cov_static),
                "n_interior_levels_trans": len(cov_trans),
            },
            "aquifer_response": {
                "present": bool(aq),
                "pi_threshold": aq.get("pi_threshold", PI_THRESHOLD),
                "pi_central": aq.get("pi_central"),
                "pi_corner90": aq.get("pi_corner90"),
                "verdict": aq.get("verdict"),
                "check_a_instantaneous_justified": aq.get(
                    "check_a_instantaneous_justified"
                ),
                "check_b_native_resolves": aq.get("check_b_native_resolves"),
                "margin_vs_threshold": (
                    round(aq["pi_threshold"] / aq["pi_corner90"], 2)
                    if aq.get("pi_corner90")
                    else None
                ),
            },
            "bootstrap_degenerate_replicates": meta.get(
                "bootstrap_degenerate_replicates"
            ),
            "fragility_deliverable": {
                branch: {
                    "form": deliverable.get(branch, {}).get("form"),
                    "fit_role": deliverable.get(branch, {}).get("fit_role"),
                    "transition_bracketed": deliverable.get(branch, {}).get(
                        "transition_bracketed"
                    ),
                    "max_p_f_raw": deliverable.get(branch, {}).get("max_p_f_raw"),
                }
                for branch in ("static", "transient")
            },
        }

    # -- ADR-0032 Pi gate, re-asserted on the fresh runs ----------------------
    pi_bad = [
        stem
        for stem, entry in per_run.items()
        if entry.get("aquifer_response", {}).get("present")
        and entry["aquifer_response"].get("verdict") != "instantaneous"
    ]
    gates.check(
        "G5",
        "ADR-0032 verdict is 'instantaneous' wherever the diagnostic is present",
        not pi_bad,
        {"sections_failing": pi_bad},
    )
    missing_aq = [
        stem
        for stem, e in per_run.items()
        if not e.get("aquifer_response", {}).get("present")
    ]
    gates.check(
        "G5",
        "every re-run sweep carries the ADR-0032 aquifer_response block",
        not missing_aq,
        {"sections_missing": missing_aq},
    )
    degenerate = {
        stem: e.get("bootstrap_degenerate_replicates")
        for stem, e in per_run.items()
        if any(
            v
            for k, v in (e.get("bootstrap_degenerate_replicates") or {}).items()
            if k in {"static", "transient"}
        )
    }
    gates.note(
        "G5", "bootstrap degenerate replicates (nonzero only)", degenerate or "all zero"
    )

    # -- Phase 3 coverage warnings -------------------------------------------
    # phase3_campaign.py propagates only coverage["__system__"]["lower_bound_clamp"]
    # (and frac_peaks_above_grid) to rq4_annual.csv, so `below_grid_unresolved`
    # and the per-mechanism records are not readable from the campaign output.
    # Compose once through the module CLI into a campaign-scoped directory to
    # capture the full AnnualizedResult.coverage block without touching the
    # legacy ADR-0038 BEP-only artifacts in results/system_integration/.
    cov_dir = CAMPAIGN_DIR / "coverage"
    cov_cmd = run_command(
        [
            PY,
            "-m",
            "system_integration",
            "--results-dir",
            "results/phase2",
            "--surface-csv",
            "data/processed/uemura_surface_curves/uemura_surface_curves_historical.csv",
            "--out",
            str(cov_dir.relative_to(REPO)),
        ],
        label="coverage_capture",
        log_path=ctx.log_dir / "diagnostics_coverage.log",
    )
    coverage = _phase3_coverage(cov_dir if cov_cmd["returncode"] == 0 else None)
    gates.note("G5", "Phase 3 AnnualizedResult.coverage warnings", coverage)

    # -- companion evidence, re-classified with the asymmetric rule ----------
    # Recomputed here (rather than trusted from the companions stage) so the
    # manifest always carries the classified verdict even when the comparison
    # rule was refined after that stage ran.
    evidence: dict[str, Any] = {}
    changed_evidence: list[str] = []
    for name, spec in COMPANION_COMMANDS.items():
        target = spec.get("compare_to")
        if target:
            verdict = _json_equal_ignoring_volatile(
                REPO / spec["outputs"][0], REPO / target
            )
        elif spec.get("git_tracked"):
            verdict = _git_tracked_evidence_verdict(spec["outputs"][0])
        else:
            continue
        if verdict is not None:
            expected = set(spec.get("expected_changed_keys", ()))
            unexpected = sorted(set(verdict["changed_keys"]) - expected)
            verdict["unexpected_changed_keys"] = unexpected
            if expected:
                verdict["expected_change_reason"] = spec.get("expected_change_reason")
            if unexpected:
                changed_evidence.append(name)
        evidence[name] = verdict
    gates.check(
        "G5",
        "every companion reproduces its committed evidence (additions and "
        "declared pre-existing staleness allowed, undeclared changes are not)",
        not changed_evidence,
        {"companions_changed": changed_evidence, "per_companion": evidence},
    )
    declared = {
        name: rec.get("expected_change_reason")
        for name, rec in evidence.items()
        if rec and rec.get("changed_keys")
    }
    if declared:
        gates.note(
            "G5",
            "companions whose committed evidence is knowingly stale "
            "(declared, with remedy in the driver)",
            declared,
        )

    return {
        "commands": [],
        "gates": gates.records,
        "outputs": [],
        "per_run": per_run,
        "phase3_coverage": coverage,
    }


def _phase3_coverage(root: Path | None) -> dict[str, Any]:
    """Harvest lower_bound_clamp / below_grid_unresolved from Phase 3 outputs."""
    if root is None:
        return {
            "status": "coverage_capture_failed",
            "campaign_rows_flagged": _phase3_campaign_clamp_flags(),
        }
    flagged: list[dict[str, Any]] = []
    scanned = 0
    missing_block = 0
    for path in sorted(root.glob("system_*.json")):
        scanned += 1
        payload = json.loads(path.read_text(encoding="utf-8"))
        coverage = (payload.get("annualized") or {}).get("coverage") or {}
        if not coverage:
            missing_block += 1
        for curve, record in coverage.items():
            if record.get("lower_bound_clamp") or record.get("below_grid_unresolved"):
                flagged.append(
                    {
                        "file": path.name,
                        "curve": curve,
                        "lower_bound_clamp": record.get("lower_bound_clamp"),
                        "below_grid_unresolved": record.get("below_grid_unresolved"),
                        "frac_peaks_above_grid": record.get("frac_peaks_above_grid"),
                        "frac_peaks_below_grid": record.get("frac_peaks_below_grid"),
                        "p_top": record.get("p_top"),
                        "p_bottom": record.get("p_bottom"),
                    }
                )
    csv_flags = _phase3_campaign_clamp_flags()
    return {
        "source": str(root.relative_to(REPO)).replace("\\", "/"),
        "files_scanned": scanned,
        "files_without_coverage_block": missing_block,
        "flagged_curves": flagged,
        "campaign_rows_flagged": csv_flags,
    }


def _phase3_campaign_clamp_flags() -> dict[str, Any]:
    """Count rq4_annual.csv rows carrying a clamp flag, grouped by section."""
    path = REPO / "results" / "system_integration" / "phase3" / "rq4_annual.csv"
    if not path.is_file():
        return {"status": "missing"}
    import csv
    from collections import Counter

    counts: Counter[str] = Counter()
    total = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        field = next(
            (
                f
                for f in (reader.fieldnames or [])
                if f in {"system_lower_bound_clamp", "bep_clamped_above_grid"}
            ),
            None,
        )
        if field is None:
            return {"status": "no_clamp_column"}
        for row in reader:
            total += 1
            if str(row.get(field, "")).strip().lower() in {"true", "1"}:
                counts[f"{row.get('kp', '?')}/{row.get('d70', '?')}"] += 1
    return {"column": field, "n_rows": total, "flagged_by_section_d70": dict(counts)}


# --------------------------------------------------------------------------- #
# Orchestration                                                                 #
# --------------------------------------------------------------------------- #


class Context:
    """Campaign-wide paths and settings; carries no physics."""

    def __init__(self, *, n_jobs: int, superseded_root: Path, log_dir: Path) -> None:
        self.n_jobs = n_jobs
        self.superseded_root = superseded_root
        self.log_dir = log_dir
        superseded_root.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def superseded_rel(self) -> str:
        return str(self.superseded_root.relative_to(REPO)).replace("\\", "/")


STAGES: list[tuple[str, Callable[[Context], dict[str, Any]], str]] = [
    ("configs", stage_configs, "regenerate configs/ and assert an empty diff"),
    ("phase1", stage_phase1, "8 sweeps, N=1e5, dt=225 s [G1]"),
    ("phase2_baseline", stage_phase2_baseline, "8 posteriors --verify [G2]"),
    ("phase2_anchor_rating", stage_phase2_anchor_rating, "4 matrix, --anchor rating"),
    (
        "phase2_no_initiation",
        stage_phase2_no_initiation,
        "4 matrix, --criterion no_breach_no_initiation",
    ),
    ("stage6_6", stage_stage6_6, "gap decomposition, matrix + bulk [G3]"),
    ("phase3", stage_phase3, "RQ3+RQ4 campaign [G4]"),
    ("phase3_validation", stage_phase3_validation, "event-based surface validation"),
    ("companions", stage_companions, "bit-identity companion studies"),
    ("figures", stage_figures, "regenerate publication figures + staleness gate [G7]"),
    ("diagnostics", stage_diagnostics, "G5 collection"),
]


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.is_file():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"campaign": "bep production campaign", "stages": {}}


def save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--stage",
        nargs="+",
        choices=[name for name, _, _ in STAGES],
        help="run only these stages (dependency order is still enforced)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-run stages the manifest already records as passed",
    )
    parser.add_argument("--n-jobs", type=int, default=8, help="joblib workers")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the plan and exit"
    )
    args = parser.parse_args()

    manifest = load_manifest()
    manifest.setdefault("stages", {})
    selected = args.stage or [name for name, _, _ in STAGES]

    plan = [
        (name, fn, doc)
        for name, fn, doc in STAGES
        if name in selected
        and (args.force or manifest["stages"].get(name, {}).get("status") != "passed")
    ]
    skipped = [
        name
        for name, _, _ in STAGES
        if name in selected and name not in {p[0] for p in plan}
    ]

    print("BEP production campaign")
    print(f"  manifest : {MANIFEST_PATH.relative_to(REPO)}")
    print(f"  n_jobs   : {args.n_jobs}")
    print(f"  to run   : {', '.join(n for n, _, _ in plan) or '(nothing)'}")
    if skipped:
        print(f"  resumed  : {', '.join(skipped)} (already passed; --force to redo)")
    if args.dry_run:
        for name, _, doc in plan:
            print(f"    {name:24s} {doc}")
        return

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    ctx = Context(
        n_jobs=args.n_jobs,
        superseded_root=REPO / "results" / f"superseded_{stamp}",
        log_dir=CAMPAIGN_DIR / "logs",
    )
    manifest["run"] = {
        "started": _utcnow(),
        "n_jobs": args.n_jobs,
        "superseded_root": ctx.superseded_rel,
        "python": sys.version.split()[0],
        "git_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
        ).stdout.strip(),
    }
    save_manifest(manifest)

    campaign_started = time.perf_counter()
    for name, fn, doc in plan:
        print(f"\n=== {name} :: {doc} ===", flush=True)
        started = time.perf_counter()
        entry: dict[str, Any] = {"start": _utcnow(), "description": doc}
        try:
            payload = fn(ctx)
        except GateFailure as exc:
            entry.update(
                {
                    "status": "GATE_FAILED",
                    "end": _utcnow(),
                    "runtime_s": round(time.perf_counter() - started, 2),
                    "error": str(exc),
                }
            )
            manifest["stages"][name] = entry
            manifest["run"]["ended"] = _utcnow()
            manifest["run"]["status"] = "STOPPED_ON_GATE_FAILURE"
            save_manifest(manifest)
            print(f"\n!! CAMPAIGN STOPPED: {exc}", flush=True)
            raise SystemExit(2)
        entry.update(payload)
        entry.update(
            {
                "status": "passed",
                "end": _utcnow(),
                "runtime_s": round(time.perf_counter() - started, 2),
            }
        )
        manifest["stages"][name] = entry
        save_manifest(manifest)
        print(f"=== {name}: passed in {entry['runtime_s']:.1f} s ===", flush=True)

    manifest["run"]["ended"] = _utcnow()
    manifest["run"]["status"] = "complete"
    manifest["run"]["total_runtime_s"] = round(
        time.perf_counter() - campaign_started, 2
    )
    save_manifest(manifest)
    print(f"\nCampaign complete in {manifest['run']['total_runtime_s']:.0f} s.")
    print(f"Manifest: {MANIFEST_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
