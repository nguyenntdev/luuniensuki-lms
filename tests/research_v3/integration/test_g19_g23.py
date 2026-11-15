"""V3-G19/G23: external audit scaffold + claim cross-verification tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from research_v3.scripts.external_audit import audit_status, write_request
from research_v3.scripts.cross_verify_claims import verify

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------- G19


def test_request_written_and_status_blocked(tmp_path):
    result = write_request(
        request_id="t1", release_paths=[Path("x")], method_ids=["m"], seed_policy="s",
        audit_dir=tmp_path,
    )
    assert result["request"]["status"] == "REQUESTED"
    assert result["request"]["human_review_pending"] is True
    status = audit_status("t1", tmp_path)
    assert status["status"] == "BLOCKED"


def test_fabricated_review_is_rejected(tmp_path):
    write_request(request_id="t2", release_paths=[], method_ids=[], seed_policy="s", audit_dir=tmp_path)
    review = {
        "reviewer_name": "X", "reviewer_affiliation": "Y", "clean_environment": False,
        "verdicts": {"c": "VERIFIED"}, "reviewed_at": "2026-11-15",
    }
    (tmp_path / "review_t2.json").write_text(json.dumps(review))
    assert audit_status("t2", tmp_path)["status"] == "INVALID_REVIEW"


def test_honest_review_is_accepted(tmp_path):
    write_request(request_id="t3", release_paths=[], method_ids=[], seed_policy="s", audit_dir=tmp_path)
    review = {
        "reviewer_name": "X", "reviewer_affiliation": "Y", "clean_environment": True,
        "verdicts": {"claim_a": "VERIFIED", "claim_b": "REFUTED"}, "reviewed_at": "2026-11-15",
    }
    (tmp_path / "review_t3.json").write_text(json.dumps(review))
    status = audit_status("t3", tmp_path)
    assert status["status"] == "RECEIVED"
    assert status["refuted"] == ["claim_b"]


def test_external_audit_cli_exit_codes(tmp_path):
    req = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.external_audit", "request",
         "--request-id", "cli1", "--audit-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert req.returncode == 22  # requested; blocked until human returns it
    stat = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.external_audit", "status",
         "--request-id", "cli1", "--audit-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert stat.returncode == 22


# ---------------------------------------------------------------- G23


def test_claims_verified_against_real_v2_runs():
    ok, report = verify(
        REPO_ROOT / "research_artifacts_v2" / "runs",
        REPO_ROOT / "research_artifacts_v2" / "release",
        REPO_ROOT / "dev_null_nonexistent_workflow.yml",
    )
    assert report["n_manifests"] == 198
    assert set(report["tiers_on_disk"]) == {"T3", "T3S"}
    assert report["readiness_recomputed"]["LN-06"] == "PARTIAL"
    assert report["readiness_recomputed"]["LN-01"] == "PASS"
    # the only finding should be the workflow's T1/T2 claim (expected state)
    non_workflow = [f for f in report["findings"] if not f.startswith("research-v2.yml")]
    assert non_workflow == []


def test_claim_of_unexecuted_tier_fails(tmp_path):
    release = tmp_path / "release"
    release.mkdir()
    (release / "SCIENTIFIC_READINESS.md").write_text(
        "# R\n> tiers: T3, T3S, T1\n\n| Study | proposed | C1 | B0 | ablations | Status |\n"
        "|---|---|---|---|---|---|\n| LN-01 | 1.0 | 0.6 | 0.2 | 0.8/0.8/0.8 | PASS |\n"
    )
    ok, report = verify(
        REPO_ROOT / "research_artifacts_v2" / "runs", release,
        REPO_ROOT / "dev_null_nonexistent_workflow.yml",
    )
    assert ok is False
    assert any("ZERO manifests for T1" in f for f in report["findings"])


def test_wrong_readiness_status_fails(tmp_path):
    release = tmp_path / "release"
    release.mkdir()
    (release / "SCIENTIFIC_READINESS.md").write_text(
        "# R\n> tiers: T3, T3S\n\n| Study | proposed | C1 | B0 | ablations | Status |\n"
        "|---|---|---|---|---|---|\n| LN-06 | 1.0 | 0.6 | 0.8 | 0.8/1.0/1.0 | PASS |\n"
    )
    ok, report = verify(
        REPO_ROOT / "research_artifacts_v2" / "runs", release,
        REPO_ROOT / "dev_null_nonexistent_workflow.yml",
    )
    assert ok is False
    assert any("LN-06" in f and "PARTIAL" in f for f in report["findings"])


def test_cross_verify_cli_exit_codes(tmp_path):
    # The repo is now honest (workflow claims T3/T3S, which is what ran), so the
    # real invocation must pass.
    current = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.cross_verify_claims"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert current.returncode == 0, current.stderr

    # Fail-closed check: a workflow that claims a tier with no manifests must
    # exit 19. Build a throwaway workflow making exactly that false claim.
    fake = tmp_path / "fake_workflow.yml"
    fake.write_text(
        "jobs:\n  x:\n    steps:\n      - run: python -m research_v2.scripts.run_matrix --all --tier T9 --strict\n",
        encoding="utf-8",
    )
    bad = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.cross_verify_claims",
         "--workflow", str(fake)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 19, bad.stdout + bad.stderr
    assert any("T9" in line for line in (bad.stdout + bad.stderr).splitlines())
