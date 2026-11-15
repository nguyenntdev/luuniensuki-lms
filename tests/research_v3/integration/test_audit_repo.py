"""V3-G00/G11: audit_repo source-lock tests (positive + forced-negative)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.scripts.audit_repo import (
    AuditRepoError,
    build_source_lock,
    read_historic_audit,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_source_lock_pins_head_and_inventory(tmp_path):
    lock = build_source_lock(
        repo=REPO_ROOT,
        source_sha=None,
        allow_dirty=True,  # the dev worktree may be dirty; lock records it
        python_version=sys.version.split()[0],
        now_utc="2026-11-15T00:00:00Z",
    )
    assert lock["schema"] == "research_v3.source_lock/v1"
    assert len(lock["git_head_observed"]) == 40
    assert lock["source_sha_pinned"] == lock["git_head_observed"]
    assert lock["head_matches_pinned"] is True
    assert lock["n_inventory_files"] > 0
    assert lock["inventory_sha256"] == sha256_input(lock["inventory"])
    # HISTORIC prior audit must be marked and never rewritten
    assert lock["historic_prior_audit"]["status"] == "HISTORIC"
    assert lock["historic_prior_audit"]["observed_sha_recorded"] == (
        read_historic_audit() or {}
    ).get("source_sha_observed")


def test_source_lock_records_dirty_state_when_allowed():
    wrong_pin = "0" * 40  # definitely not the current HEAD
    lock = build_source_lock(
        repo=REPO_ROOT,
        source_sha=wrong_pin,
        allow_dirty=True,
        python_version="3.12.0",
        now_utc="2026-11-15T00:00:00Z",
    )
    assert isinstance(lock["working_tree_dirty"], bool)
    assert lock["head_matches_pinned"] is False
    assert lock["source_sha_pinned"] == wrong_pin


def test_cli_writes_fresh_file_and_strict_pin_mismatch_fails(tmp_path):
    out = tmp_path / "lock.json"
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.audit_repo", "--allow-dirty", "--output", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    data = json.loads(out.read_text())
    assert data["n_inventory_files"] > 0

    bad = subprocess.run(
        [
            sys.executable, "-m", "research_v3.scripts.audit_repo",
            "--source-sha", "deadbeef", "--allow-dirty", "--strict", "--output", str(tmp_path / "l2.json"),
        ],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 3  # strict pin mismatch
