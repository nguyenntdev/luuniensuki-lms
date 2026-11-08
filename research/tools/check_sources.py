#!/usr/bin/env python3
"""Inspect research fixtures and sources; do not create evidence or alter sources."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]


def h(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jsonhash(x: Any) -> str:
    b = json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(b.encode("utf-8")).hexdigest()


def resolve_spec_paths(spec: Optional[pathlib.Path] = None) -> tuple[Optional[pathlib.Path], Optional[pathlib.Path], Optional[pathlib.Path]]:
    """Resolve (spec_root, manifest_path, fixtures_dir)."""
    candidates = []
    if spec:
        spec = spec.resolve()
        candidates.extend([
            (spec, spec / "04_FIXTURES" / "CONCRETE" / "fixture_manifest.json", spec / "04_FIXTURES" / "CONCRETE"),
            (spec, spec / "fixtures" / "fixture_manifest.json", spec / "fixtures"),
            (spec, spec / "fixture_manifest.json", spec),
        ])
    # Repo-internal fallbacks
    candidates.extend([
        (ROOT, ROOT / "fixtures" / "fixture_manifest.json", ROOT / "fixtures"),
        (ROOT.parent, ROOT.parent / "research" / "fixtures" / "fixture_manifest.json", ROOT.parent / "research" / "fixtures"),
        (ROOT.parent, ROOT.parent / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026" / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026" / "04_FIXTURES" / "CONCRETE" / "fixture_manifest.json", ROOT.parent / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026" / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026" / "04_FIXTURES" / "CONCRETE"),
    ])

    for s_root, mf, fix_dir in candidates:
        if mf.is_file() and fix_dir.is_dir():
            return s_root, mf, fix_dir

    return (spec or ROOT, None, None)


def verify_spec(spec: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    issues: List[str] = []
    stats: Dict[str, Any] = {"fixtures": {}, "sha256_entries_verified": 0}

    spec_root, mf_path, fixtures_dir = resolve_spec_paths(spec)

    # 1. SHA256SUMS.txt if present
    checks_candidates = []
    if spec_root:
        checks_candidates.append(spec_root / "SHA256SUMS.txt")
    if fixtures_dir:
        checks_candidates.append(fixtures_dir / "SHA256SUMS.txt")

    checks_found = False
    for checks in checks_candidates:
        if checks.is_file():
            checks_found = True
            base_dir = checks.parent
            for line in checks.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                pair = line.split("  ", 1)
                if len(pair) != 2:
                    continue
                digest, path = pair
                target = base_dir / path
                if not target.is_file():
                    # Check relative to spec_root
                    if spec_root and (spec_root / path).is_file():
                        target = spec_root / path
                    else:
                        issues.append(f"missing spec checksum file: {path}")
                        continue
                if h(target) != digest:
                    issues.append(f"spec checksum mismatch: {path}")
                else:
                    stats["sha256_entries_verified"] += 1
            break

    if not mf_path or not mf_path.is_file() or not fixtures_dir:
        issues.append("Fixture manifest unavailable or missing fixture directory")
        return {"issues": issues, "stats": stats}

    try:
        manifest = json.loads(mf_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"issues": issues + [f"Cannot read fixture manifest: {e}"], "stats": stats}

    # 2. Check each study fixture
    for i in range(1, 11):
        study = f"LN-{i:02d}"
        f = fixtures_dir / f"{study}_concrete.jsonl"
        if not f.is_file():
            issues.append(f"Missing {f}")
            continue

        cohort_info = manifest.get("cohorts", {}).get(study, {})
        expected_sha = cohort_info.get("sha256")
        actual_sha = h(f)
        if expected_sha and actual_sha != expected_sha:
            issues.append(f"{study} concrete hash differs from fixture_manifest: {actual_sha} != {expected_sha}")

        faults: collections.Counter[str] = collections.Counter()
        seen: set[str] = set()
        n = 0
        for lineno, line in enumerate(f.open(encoding="utf-8"), 1):
            if not line.strip():
                continue
            n += 1
            try:
                row = json.loads(line)
                if row.get("paper_id") != study:
                    raise AssertionError(f"Expected paper_id {study}, got {row.get('paper_id')}")
                if row.get("cohort") != "SYNTHETIC_FIXTURE_ONLY":
                    raise AssertionError(f"Expected cohort SYNTHETIC_FIXTURE_ONLY, got {row.get('cohort')}")
                if row.get("input_hash") != jsonhash(row.get("input")):
                    raise AssertionError("input_hash does not match hashed input")
                inp = row.get("input", {})
                if "expected_decision" in inp or "oracle" in inp:
                    raise AssertionError("Data leakage: expected_decision or oracle inside input")
                cid = row.get("case_id")
                if not cid or cid in seen:
                    raise AssertionError(f"duplicate or missing case_id: {cid}")
                seen.add(cid)
                faults[row.get("fault_id", "unknown")] += 1
            except Exception as e:
                issues.append(f"{study}:{lineno}: invalid fixture ({e})")
                if len(issues) > 50:
                    break

        expected_count = cohort_info.get("cases", 720)
        if n != expected_count:
            issues.append(f"{study}: expected {expected_count}, found {n}")
        if sorted(faults.values()) != [144] * 5 and n == 720:
            issues.append(f"{study}: expected five balanced classes of 144, saw {dict(faults)}")
        stats["fixtures"][study] = {"rows": n, "faults": dict(faults), "sha256": actual_sha}

    return {"issues": issues, "stats": stats}


def verify_manuscripts(ms: pathlib.Path) -> Dict[str, Any]:
    issues: List[str] = []
    stats: Dict[str, Any] = {}
    candidates = [
        (ms / "manuscripts_tex", ".tex", "LN-{i:02d}_SU_PHAM_ARXIV_V4"),
        (ms / "manuscripts_md", ".md", "LN-{i:02d}_SU_PHAM_ARXIV_V4"),
        (ms, ".tex", "LN-{i:02d}"),
    ]
    for folder, suffix, pattern in candidates:
        if not folder.is_dir():
            continue
        counts = 0
        for i in range(1, 11):
            fname = pattern.format(i=i) + suffix
            p = folder / fname
            if p.is_file():
                counts += 1
            else:
                issues.append(f"Missing manuscript {p}")
        stats[folder.name] = counts

    if not stats and ms.is_dir():
        issues.append(f"No valid manuscript folders found in {ms}")

    return {"issues": issues, "stats": stats}


def main():
    ap = argparse.ArgumentParser(description="Check source fixtures and manuscripts integrity")
    ap.add_argument("--spec", type=pathlib.Path, default=None, help="Path to spec directory (optional; defaults to repo research/fixtures)")
    ap.add_argument("--manuscripts", type=pathlib.Path, default=None)
    ap.add_argument("--output", type=pathlib.Path, default=None)
    a = ap.parse_args()

    s = verify_spec(a.spec)
    status = "PASS" if not s["issues"] else "FAIL"
    out: Dict[str, Any] = {
        "status": status,
        "spec": str((a.spec or ROOT).resolve()),
        "spec_validation": s,
    }
    if a.manuscripts:
        mm = verify_manuscripts(a.manuscripts.resolve())
        out["manuscripts_validation"] = mm
        if mm["issues"]:
            out["status"] = "FAIL"

    blob = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(blob, encoding="utf-8")

    summary = {
        "status": out["status"],
        "spec_verified": s["stats"]["sha256_entries_verified"],
        "fixture_total": sum(x["rows"] for x in s["stats"]["fixtures"].values()),
        "issues": s["issues"] + (out.get("manuscripts_validation", {}).get("issues", [])),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
