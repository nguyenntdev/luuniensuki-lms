"""V3-G13/G14/G18: replication guard, label audit, cross-paper dedup tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v3.scripts.replicate import ReplicationError, guard
from research_v3.scripts.label_mismatch_audit import audit_study
from research_v3.scripts.cross_paper_dedup import find_collisions

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------- G13


def test_deterministic_guard_requires_byte_identity():
    hashes = {f"seed{s}": "abc" for s in (11, 23)}
    report = guard(method_kind="deterministic", seed_hashes=hashes)
    assert report["status"] == "PASS"
    assert "SAME replicate, not independent evidence" in report["verdict"]
    assert report["identical_across_seeds"] is True


def test_deterministic_guard_fails_on_drift():
    with pytest.raises(ReplicationError):
        guard(method_kind="deterministic", seed_hashes={"seed11": "a", "seed23": "b"})


def test_stochastic_guard_requires_five_independent_seeds():
    with pytest.raises(ReplicationError):
        guard(method_kind="stochastic", seed_hashes={"s1": "a", "s2": "b"})
    identical = {f"seed{s}": "same" for s in range(5)}
    with pytest.raises(ReplicationError) as exc:
        guard(method_kind="stochastic", seed_hashes=identical)
    assert "NOT independent" in str(exc.value) and "pseudo" in str(exc.value).lower()
    ok = guard(method_kind="stochastic", seed_hashes={f"s{i}": f"h{i}" for i in range(5)})
    assert ok["status"] == "PASS"


def test_replicate_cli_modes(tmp_path):
    det = tmp_path / "det"
    for s in (11, 23):
        (det / f"seed{s}").mkdir(parents=True)
        (det / f"seed{s}" / "predictions.jsonl").write_text('{"x": 1}\n')
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.replicate",
         "--runs-root", str(tmp_path), "--study", "det", "--kind", "deterministic"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr

    # 5 identical seeds declared stochastic -> pseudo-replication failure
    stoch = tmp_path / "stoch"
    for s in range(5):
        (stoch / f"seed{s}").mkdir(parents=True)
        (stoch / f"seed{s}" / "predictions.jsonl").write_text('{"x": 1}\n')
    bad = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.replicate",
         "--runs-root", str(tmp_path), "--study", "stoch", "--kind", "stochastic"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 15
    assert "NOT independent" in bad.stderr


# ---------------------------------------------------------------- G14


def test_label_audit_flags_documented_ln09_divergence():
    report = audit_study("LN-09")
    assert report["prereg_present"]
    assert report["mismatches"], "LN-09 prereg/gold vocab divergence must be reported"
    assert report["status"] == "DOCUMENTED_DIVERGENCE"


def test_label_audit_undocumented_mismatch_detected(tmp_path):
    ln = tmp_path / "ln03"
    ln.mkdir()
    (ln / "prereg.yaml").write_text(
        "study_id: LN-03\nprimary_metric: x\ndecision_space: [fake_label_one]\n"
    )
    report = audit_study("LN-03", experiments_dir=tmp_path)
    assert report["status"] == "UNDOCUMENTED_MISMATCH"
    kinds = {m["kind"] for m in report["mismatches"]}
    assert "prereg_vs_gold" in kinds


def test_label_audit_cli_exit_codes():
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.label_mismatch_audit", "--all"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.label_mismatch_audit", "--study", "LN-99"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 7


# ---------------------------------------------------------------- G18


def test_dedup_detects_same_primary_metric():
    prereg = [
        {"paper_id": "P01", "primary_metric": "m", "primary_hypothesis_hash": "h1"},
        {"paper_id": "P02", "primary_metric": "m", "primary_hypothesis_hash": "h2"},
    ]
    collisions = find_collisions(prereg, [])
    assert any(c["kind"] == "same_primary_metric" for c in collisions)


def test_dedup_detects_identical_hypothesis_text():
    prereg = [
        {"paper_id": "P01", "primary_metric": "m1", "primary_hypothesis_hash": "same"},
        {"paper_id": "P02", "primary_metric": "m2", "primary_hypothesis_hash": "same"},
    ]
    collisions = find_collisions(prereg, [])
    assert any(c["kind"] == "identical_primary_hypothesis" for c in collisions)


def test_dedup_clean_portfolio_passes_cli():
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.cross_paper_dedup"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr


def test_dedup_cli_collision_exit(tmp_path):
    exp = tmp_path / "exp"
    for p in ("P01", "P02"):
        d = exp / p.lower()
        d.mkdir(parents=True)
        (d / "pre_registration.yaml").write_text(
            f"study_id: {p}\npaper_id: {p}\nprimary_metric: shared_metric\n"
            "hypotheses:\n  H1: >-\n    Identical claim text for both papers.\n"
        )
    bad = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.cross_paper_dedup", "--experiments-dir", str(exp)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 18
    assert "MERGE_REQUIRED" in bad.stderr
