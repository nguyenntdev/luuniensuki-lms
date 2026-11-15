"""Inspect the repository against the pinned Research V2 source snapshot.

Emits ``research_v2/reports/G0_repo_audit.json`` and exits nonzero in strict
mode when the working tree HEAD differs from the pinned SHA or required legacy
artifacts are missing.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PINNED_SHA = "abcfab201d47db4cf89edf4b769c645438522d3a"

REQUIRED_LEGACY_PATHS = [
    "research/heritage_trails/cognitive_route.py",
    "research/integrations/ln06.py",
    "research/fixtures/holdout/LN-01_holdout.jsonl",
    "research/fixtures/holdout/LN-10_holdout.jsonl",
    "tests/research",
]

EXPECTED_V2_PATHS = [
    "research_v2/contracts/types.py",
    "research_v2/contracts/canonical_hash.py",
    "research_v2/contracts/label_space.py",
    "research_v2/contracts/task_registry.py",
    "research_v2/evaluation/runner.py",
    "research_v2/evaluation/metrics.py",
    "research_v2/evaluation/statistical_tests.py",
    "research_v2/scripts/inspect_repo.py",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def audit(repo_root: Path | None = None) -> dict:
    root = Path(repo_root or _repo_root())
    head = _git("rev-parse", "HEAD", cwd=root)
    dirty = bool(_git("status", "--porcelain", cwd=root))
    missing_legacy = [p for p in REQUIRED_LEGACY_PATHS if not (root / p).exists()]
    missing_v2 = [p for p in EXPECTED_V2_PATHS if not (root / p).exists()]
    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha_observed": head,
        "source_sha_pinned": PINNED_SHA,
        "head_matches_pinned": head == PINNED_SHA,
        "working_tree_dirty": dirty,
        "python_version": platform.python_version(),
        "missing_legacy_paths": missing_legacy,
        "missing_v2_paths": missing_v2,
        "legacy_ok": not missing_legacy,
        "v2_core_present": not missing_v2,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Inspect repository for Research V2")
    ap.add_argument("--strict", action="store_true", help="exit nonzero on any discrepancy")
    ap.add_argument("--output", type=Path, default=None)
    a = ap.parse_args(argv)

    report = audit()
    out = a.output or (_repo_root() / "research_v2" / "reports" / "G0_repo_audit.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    problems = []
    if not report["legacy_ok"]:
        problems.append(f"missing legacy paths: {report['missing_legacy_paths']}")
    if not report["v2_core_present"]:
        problems.append(f"missing v2 core paths: {report['missing_v2_paths']}")
    if a.strict and not report["head_matches_pinned"]:
        problems.append(
            f"HEAD {report['source_sha_observed']} differs from pinned {PINNED_SHA}"
        )
    if problems:
        for p in problems:
            print(f"STRICT FAIL: {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
