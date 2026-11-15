"""V3-G04/G05/G06: split protocols, baseline registry, fail-closed training."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v3.datasets.registry import LicenseGateError
from research_v3.eval.splitters import SplitError
from research_v3.scripts.train import (
    DataBlockedError,
    ExperimentCardError,
    gate_datasets,
    load_experiment_card,
    run_training_gate,
)
from research_v3.scripts.validate_splits import materialize_protocol, verify_protocol

REPO_ROOT = Path(__file__).resolve().parents[3]

H = lambda c: c * 64  # noqa: E731


def _rows(n_groups: int = 40):
    return [
        {
            "case_id": f"c{i:03d}",
            "group_id": f"g{i % n_groups}",
            "time_key": f"201{3 + i % 2}J",
            "input": {"x": i},
            "label": "Pass",
        }
        for i in range(4 * n_groups)
    ]


# ---------------------------------------------------------------- G04


def test_split_materialize_and_verify_hash_stable(tmp_path):
    rows = _rows()
    protocol = materialize_protocol(paper_id="PX1", rows=rows, protocol="group")
    assert protocol["partition_sizes"]["train"] > 0
    assert protocol["split_sha256"] == materialize_protocol(
        paper_id="PX1", rows=rows, protocol="group"
    )["split_sha256"]
    assert verify_protocol(protocol, rows, protocol_name="PX1") == []


def test_split_time_protocol_and_gold_never_in_input(tmp_path):
    rows = _rows()
    protocol = materialize_protocol(paper_id="PX2", rows=rows, protocol="time")
    assert protocol["protocol"] == "time"
    assert verify_protocol(protocol, rows, protocol_name="PX2") == []


def test_split_leakage_audit_rejects_gold_in_input():
    rows = _rows(10)
    rows[0]["input"]["gold"] = "cheat"
    with pytest.raises(Exception):
        materialize_protocol(paper_id="PX3", rows=rows, protocol="group")


def test_split_cli_roundtrip_and_drift(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    with rows_path.open("w") as fh:
        for r in _rows():
            fh.write(json.dumps(r) + "\n")
    out = tmp_path / "PX4.json"
    ok = subprocess.run(
        [
            sys.executable, "-m", "research_v3.scripts.validate_splits",
            "--paper", "PX4", "--rows", str(rows_path), "--protocol", "group", "--output", str(out),
        ],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    verify = subprocess.run(
        [
            sys.executable, "-m", "research_v3.scripts.validate_splits",
            "--paper", "PX4", "--rows", str(rows_path), "--verify-only", "--output", str(out),
        ],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert verify.returncode == 0, verify.stderr

    tampered = json.loads(out.read_text())
    tampered["split_sha256"] = "0" * 64
    out.write_text(json.dumps(tampered))
    drift = subprocess.run(
        [
            sys.executable, "-m", "research_v3.scripts.validate_splits",
            "--paper", "PX4", "--rows", str(rows_path), "--verify-only", "--output", str(out),
        ],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert drift.returncode == 9


# ---------------------------------------------------------------- G05


def test_baseline_registry_c2_stays_blocked():
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.baselines.verification.verify_baselines"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    import yaml

    registry = yaml.safe_load(
        (REPO_ROOT / "research_v3/baselines/registry/registry.yaml").read_text()
    )
    c2 = [b for b in registry["baselines"] if b["tier"] == "C2"]
    assert c2 and all(b["status"] == "BLOCKED" for b in c2)


def test_baseline_verifier_rejects_fabricated_c2_approval(tmp_path):
    import yaml

    registry = yaml.safe_load(
        (REPO_ROOT / "research_v3/baselines/registry/registry.yaml").read_text()
    )
    registry["baselines"] = [
        b for b in registry["baselines"] if b["tier"] != "C2"
    ] + [
        {
            "baseline_id": "c2_fabricated",
            "tier": "C2",
            "attribution": "some published model",
            "comparable_task": True,
            "license": "unknown",
            "status": "APPROVED",
        }
    ]
    p = tmp_path / "bad_registry.yaml"
    p.write_text(yaml.safe_dump(registry))
    bad = subprocess.run(
        [
            sys.executable, "-m", "research_v3.baselines.verification.verify_baselines",
            "--registry", str(p),
        ],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 10


# ---------------------------------------------------------------- G06


def _card(**over):
    base = dict(
        paper_id="P06", rq_id="RQ1",
        train_dataset_ids=["oulad-2013-2014"], holdout_dataset_ids=[],
        method_commit_sha="4e5a792e16250106b9d0a577849e864ab7007c92",
        method_hash=H("a"), baseline_version="v3_c1_classical", split_hash=H("b"),
        feature_cutoff="2026-11-15", prereg_sha256=H("c"), hyperparameter_budget="cpu-1h",
        seed=11, hardware="test", wall_time_seconds=0.0,
        dependency_lock_sha256=H("d"), output_path="x", status="BLOCKED",
    )
    base.update(over)
    return base


def test_train_gate_accepts_approved_datasets(tmp_path):
    card = load_experiment_card(_write(tmp_path, _card()))
    manifest = run_training_gate(card, seed=None)
    assert manifest["status"] == "MANIFEST_WRITTEN_TRAINING_STUB"
    assert manifest["manifest_sha256"]
    assert all(d["status"] == "APPROVED" for d in manifest["datasets"])


def test_train_gate_raises_on_blocked_dataset(tmp_path):
    card = load_experiment_card(_write(tmp_path, _card(train_dataset_ids=["assistments"])))
    # the gate must RAISE a license-gate error (never degrade to silent success)
    with pytest.raises((DataBlockedError, LicenseGateError)):
        run_training_gate(card, seed=None)


def test_train_gate_raises_without_card(tmp_path):
    with pytest.raises(ExperimentCardError):
        load_experiment_card(tmp_path / "missing.json")


def test_train_cli_exit_codes(tmp_path):
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.train",
         "--experiment-card", str(_write(tmp_path, _card())), "--dry-run"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr

    blocked = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.train",
         "--experiment-card", str(_write(tmp_path, _card(train_dataset_ids=["ednet"]))),
         "--output", str(tmp_path / "m.json")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert blocked.returncode == 12  # BLOCKED data: raise, never silently succeed
    assert not (tmp_path / "m.json").exists()

    invalid = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.train",
         "--experiment-card", str(_write(tmp_path, _card(rq_id="")))],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert invalid.returncode == 11


def _write(tmp_path: Path, payload: dict) -> Path:
    p = tmp_path / f"card_{abs(hash(json.dumps(payload, sort_keys=True)))}.json"
    p.write_text(json.dumps(payload))
    return p
