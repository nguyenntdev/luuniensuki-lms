"""Integration test for the read-first-and-scope and repo-sha baseline gates."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from research_v2.scripts import freeze_release
from research_v2.scripts.freeze_release import freeze
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
    # The spec package is an external planning artefact and may be absent from a
    # clean checkout; the G0 audit report is the in-repo source of truth.
    assert data["read_first_and_scope"]["g0_report_present"] is True
    assert "spec_dir_present" in data["read_first_and_scope"]


# ---------------------------------------------------------------------------
# Fail-closed exit semantics + manifest hash/case-count verification
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402

from research_v2.contracts.manifest import DataManifest, DatasetEntry, write_manifest  # noqa: E402


def _read_default_manifest():
    return json.loads((REPO / "research_v2" / "data" / "manifest.json").read_text(encoding="utf-8"))


def _copy_manifest_with_entry(tmp_path: Path, source_entry: dict, *, sha256: str | None = None,
                              cases: int | None = None) -> Path:
    """Write a temp manifest containing one entry (optionally tampered) whose
    path still resolves against the real repo root."""
    data = _read_default_manifest()
    entry = dict(source_entry)
    if sha256 is not None:
        entry["sha256"] = sha256
    if cases is not None:
        entry["cases"] = cases
    data["entries"] = [entry]
    manifest_path = tmp_path / "manifest.json"
    write_manifest(
        DataManifest(hash_standard=data["hash_standard"]),
        manifest_path,
    )
    # write_manifest serialises DataManifest; rebuild from raw dicts instead so
    # every source field (source_url, version, ...) round-trips exactly.
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _single_real_entry() -> dict:
    entries = _read_default_manifest()["entries"]
    live = [e for e in entries if e["provenance"] != "blocked"]
    assert live, "manifest must contain at least one non-blocked entry"
    return live[0]


def test_clean_run_exits_zero_without_strict(tmp_path):
    """Fail-closed default: a clean tree still passes WITHOUT --strict."""
    out = tmp_path / "report.json"
    rc = verify_main(["--legacy-and-v2", "--output", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["status"] == "PASS"


def test_allow_failures_returns_zero_even_with_issues(tmp_path):
    """--allow-failures is the explicit informational opt-out: even a tampered
    manifest (which fails closed by default) must exit 0 under this flag."""
    entry = _single_real_entry()
    manifest_path = _copy_manifest_with_entry(tmp_path, entry, sha256="0" * 64)
    strict_out = tmp_path / "strict.json"
    relaxed_out = tmp_path / "relaxed.json"
    assert verify_main(["--legacy-and-v2", "--manifest", str(manifest_path), "--output", str(strict_out)]) != 0
    rc = verify_main(
        ["--legacy-and-v2", "--manifest", str(manifest_path), "--allow-failures", "--output", str(relaxed_out)]
    )
    assert rc == 0
    data = json.loads(relaxed_out.read_text())
    assert data["status"] == "FAIL"
    assert data["issues"]


def test_manifest_sha256_tampering_exits_nonzero(tmp_path):
    """A tampered manifest sha256 must fail closed (nonzero exit)."""
    entry = _single_real_entry()
    bad_sha = "0" * 64
    assert bad_sha != entry["sha256"]
    manifest_path = _copy_manifest_with_entry(tmp_path, entry, sha256=bad_sha)
    out = tmp_path / "report.json"
    rc = verify_main(["--legacy-and-v2", "--manifest", str(manifest_path), "--output", str(out)])
    assert rc != 0
    data = json.loads(out.read_text())
    assert data["status"] == "FAIL"
    assert any("sha256 mismatch" in issue for issue in data["issues"])


def test_dataset_byte_tampering_exits_nonzero(tmp_path):
    """One flipped byte in a dataset file must fail closed via a temp manifest
    that points at the temp copy."""
    entry = _single_real_entry()
    source = REPO / entry["path"]
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    row = json.loads(lines[0])
    row["case_id"] = row["case_id"] + "-tampered"
    lines[0] = json.dumps(row, ensure_ascii=False) + "\n"
    tampered = tmp_path / "tampered.jsonl"
    tampered.write_text("".join(lines), encoding="utf-8")

    tampered_entry = dict(entry)
    tampered_entry["path"] = str(tampered.resolve())
    manifest_path = _copy_manifest_with_entry(tmp_path, tampered_entry)
    out = tmp_path / "report.json"
    rc = verify_main(["--legacy-and-v2", "--manifest", str(manifest_path), "--output", str(out)])
    assert rc != 0
    data = json.loads(out.read_text())
    assert data["status"] == "FAIL"
    assert any("sha256 mismatch" in issue for issue in data["issues"])
    # Sanity: the stored hash really no longer matches the tampered bytes.
    assert hashlib.sha256(tampered.read_bytes()).hexdigest() != tampered_entry["sha256"]


def test_case_count_mismatch_exits_nonzero(tmp_path):
    """entry.cases drifting from the actual JSONL line count must fail closed."""
    entry = _single_real_entry()
    manifest_path = _copy_manifest_with_entry(tmp_path, entry, cases=entry["cases"] + 1)
    out = tmp_path / "report.json"
    rc = verify_main(["--legacy-and-v2", "--manifest", str(manifest_path), "--output", str(out)])
    assert rc != 0
    data = json.loads(out.read_text())
    assert any("case count mismatch" in issue for issue in data["issues"])


def test_clean_custom_manifest_exits_zero_without_strict(tmp_path):
    """A faithful temp manifest (single verified entry) still passes fail-closed."""
    entry = _single_real_entry()
    manifest_path = _copy_manifest_with_entry(tmp_path, entry)
    out = tmp_path / "report.json"
    rc = verify_main(["--legacy-and-v2", "--manifest", str(manifest_path), "--output", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["status"] == "PASS"


# --- freeze_release clean-source default semantics -----------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=str(repo), check=True, capture_output=True, text=True
    )


@pytest.fixture()
def temp_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "research_v2").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "research_v2" / "seed.py").write_text("# committed source\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo


def test_freeze_rejects_uncommitted_source_by_default(temp_git_repo: Path, tmp_path: Path):
    (temp_git_repo / "research_v2" / "new_source.py").write_text("# dirty source\n")
    with pytest.raises(RuntimeError, match="uncommitted SOURCE changes"):
        freeze(temp_git_repo, tmp_path / "out", assert_clean=True)


def test_freeze_allows_generated_artifact_paths(temp_git_repo: Path, tmp_path: Path):
    generated = temp_git_repo / "research_artifacts_v2" / "fake.json"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text("{}\n")
    manifest = freeze(temp_git_repo, tmp_path / "out", assert_clean=True)
    assert manifest["source_dirty_paths"] == []
    assert manifest["working_tree_dirty"] is False


def test_freeze_allowlist_covers_v2_data_and_reports(
    temp_git_repo: Path, tmp_path: Path
):
    data_file = temp_git_repo / "research_v2" / "data" / "materialized.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("{}\n")
    report = temp_git_repo / "research_v2" / "reports" / "summary.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("{}\n")
    manifest = freeze(temp_git_repo, tmp_path / "out", assert_clean=True)
    assert manifest["source_dirty_paths"] == []


def test_freeze_records_dirty_source_when_assert_disabled(
    temp_git_repo: Path, tmp_path: Path
):
    (temp_git_repo / "research_v2" / "dirty.py").write_text("# dirty source\n")
    manifest = freeze(temp_git_repo, tmp_path / "out", assert_clean=False)
    assert manifest["source_dirty_paths"] == ["research_v2/dirty.py"]
    assert manifest["working_tree_dirty"] is True


def test_main_returns_1_on_dirty_source(
    temp_git_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    (temp_git_repo / "research_v2" / "dirty.py").write_text("# dirty source\n")
    monkeypatch.setattr(freeze_release, "_repo_root", lambda: temp_git_repo)

    # Default semantics: dirty SOURCE tree must fail (exit 1).
    rc = freeze_release.main(["--all", "--out", str(tmp_path / "out2")])
    assert rc == 1

    # Explicit opt-out for informational runs: succeeds and records the dirt.
    out = tmp_path / "out"
    rc = freeze_release.main(["--all", "--out", str(out), "--allow-dirty-source"])
    assert rc == 0
    manifest = json.loads((out / "release_manifest.json").read_text())
    assert manifest["working_tree_dirty"] is True
    assert manifest["source_dirty_paths"] == ["research_v2/dirty.py"]


def test_cli_assert_clean_flag_is_noop_but_allowed(
    temp_git_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(freeze_release, "_repo_root", lambda: temp_git_repo)
    rc = freeze_release.main(["--all", "--assert-clean", "--out", str(tmp_path / "out")])
    assert rc == 0
    assert (tmp_path / "out" / "release_manifest.json").is_file()
