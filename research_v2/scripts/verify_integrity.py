"""Verify integrity of legacy and V2 research data, fail-closed.

Checks (all hard failures in strict mode):
  * every holdout fixture row's ``input_hash`` matches the canonical standard;
  * cohort labels are the synthetic held-out label;
  * oracle bases are allowed non-human bases;
  * no oracle leakage inside ``input``;
  * annotation provenance marker present;
  * optional: dataset registry and manifest hashes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_input
from research_v2.contracts.label_space import (
    ALLOWED_ORACLE_BASES,
    PROVENANCE_MARKER,
    SYNTHETIC_COHORT,
)

STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _iter_jsonl(path: Path):
    for lineno, line in enumerate(path.open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        yield lineno, json.loads(line)


def verify_holdout_file(path: Path) -> tuple[list[str], int]:
    issues: list[str] = []
    n = 0
    seen: set[str] = set()
    for lineno, row in _iter_jsonl(path):
        n += 1
        cid = row.get("case_id")
        if not cid:
            issues.append(f"{path.name}:{lineno}: missing case_id")
            continue
        if cid in seen:
            issues.append(f"{path.name}:{lineno}: duplicate case_id {cid}")
        seen.add(cid)
        if row.get("cohort") != SYNTHETIC_COHORT:
            issues.append(f"{path.name}:{lineno}: cohort != {SYNTHETIC_COHORT}")
        if "input" not in row:
            issues.append(f"{path.name}:{lineno}: missing input")
            continue
        expected = sha256_input(row["input"])
        if row.get("input_hash") != expected:
            issues.append(
                f"{path.name}:{lineno}: stale input_hash (stored={row.get('input_hash')!r} expected={expected!r})"
            )
        inp = row["input"]
        if isinstance(inp, dict) and ("oracle" in inp or "expected_decision" in inp):
            issues.append(f"{path.name}:{lineno}: oracle leakage inside input")
        basis = (row.get("oracle") or {}).get("basis")
        if basis and basis not in ALLOWED_ORACLE_BASES:
            issues.append(f"{path.name}:{lineno}: disallowed oracle basis {basis!r}")
        if row.get("annotation_provenance") != PROVENANCE_MARKER:
            issues.append(f"{path.name}:{lineno}: missing provenance marker")
    return issues, n


def verify_legacy(repo_root: Path) -> dict:
    issues: list[str] = []
    stats: dict[str, int] = {}
    holdout_dir = repo_root / "research" / "fixtures" / "holdout"
    for study in STUDY_IDS:
        f = holdout_dir / f"{study}_holdout.jsonl"
        if not f.is_file():
            issues.append(f"missing holdout file {f}")
            continue
        file_issues, n = verify_holdout_file(f)
        issues.extend(file_issues)
        stats[study] = n
        if n != 120:
            issues.append(f"{study}: expected 120 cases, found {n}")
    total = sum(stats.values())
    if total != 1200:
        issues.append(f"expected 1200 total holdout cases, found {total}")
    return {"issues": issues, "cases_by_study": stats, "total_cases": total}


def verify_v2(repo_root: Path) -> dict:
    issues: list[str] = []
    manifest_path = repo_root / "research_v2" / "data" / "manifest.json"
    if manifest_path.is_file():
        from research_v2.contracts.manifest import load_manifest, ManifestError

        try:
            manifest = load_manifest(manifest_path)
        except ManifestError as exc:
            issues.append(f"data manifest invalid: {exc}")
            manifest = None
        if manifest is not None:
            for entry in manifest.entries:
                p = repo_root / entry.path
                if entry.provenance == "blocked":
                    continue
                if not p.is_file():
                    issues.append(f"{entry.dataset_id}: missing file {entry.path}")
    return {"issues": issues, "manifest_present": manifest_path.is_file()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify Research V2 integrity")
    ap.add_argument("--check", default=None, help="named check to run (read-first-and-scope, repo-sha-baseline)")
    ap.add_argument("--legacy-and-v2", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--output", type=Path, default=None)
    a = ap.parse_args(argv)

    root = _repo_root()
    result: dict = {"repo_root": str(root)}

    if a.check == "repo-sha-baseline":
        from research_v2.scripts.inspect_repo import audit

        result["repo_sha_baseline"] = audit(root)
    elif a.check == "read-first-and-scope":
        report = root / "research_v2" / "reports" / "G0_repo_audit.json"
        result["read_first_and_scope"] = {
            "g0_report_present": report.is_file(),
            "spec_dir_present": (
                root
                / "LUU_NIEN_RESEARCH_V2_456_FILES_52K_LINES"
                / "LUU_NIEN_RESEARCH_V2_450_FILE_EXECUTION_SPEC"
            ).is_dir(),
        }
    else:
        result["legacy"] = verify_legacy(root)
        result["v2"] = verify_v2(root)

    all_issues = []
    for section in ("legacy", "v2"):
        all_issues.extend(result.get(section, {}).get("issues", []))
    if a.check == "repo-sha-baseline":
        if not result["repo_sha_baseline"]["legacy_ok"]:
            all_issues.append("legacy artifacts missing")
    result["status"] = "PASS" if not all_issues else "FAIL"
    result["issues"] = all_issues

    out = a.output or (root / "research_artifacts_v2" / "audits" / "verify_integrity_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "issues": all_issues[:20], "n_issues": len(all_issues)}, ensure_ascii=False, indent=2))

    if a.strict and all_issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
