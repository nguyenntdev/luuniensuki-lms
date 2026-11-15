"""Integration test for the read-first-and-scope and repo-sha baseline gates."""
from __future__ import annotations

import json
from pathlib import Path

from research_v2.scripts.inspect_repo import audit
from research_v2.scripts.verify_integrity import main as verify_main

REPO = Path(__file__).resolve().parents[3]


def test_repo_audit_records_pinned_and_observed_sha(tmp_path):
    report = audit(REPO)
    assert report["source_sha_pinned"]
    assert len(report["source_sha_observed"]) == 40
    assert "head_matches_pinned" in report
    assert report["legacy_ok"] is True


def test_verify_integrity_passes_on_clean_tree(tmp_path):
    out = tmp_path / "report.json"
    rc = verify_main(["--legacy-and-v2", "--strict", "--output", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["status"] == "PASS"
    assert data["legacy"]["total_cases"] == 1200


def test_verify_integrity_read_first_and_scope_check(tmp_path):
    out = tmp_path / "scope.json"
    rc = verify_main(["--check", "read-first-and-scope", "--output", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["read_first_and_scope"]["spec_dir_present"] is True
