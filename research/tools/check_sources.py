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


def verify_holdouts(root: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Fail-closed integrity validation of all synthetic held-out test sets.

    Enforces the canonical hash standard (sha256 of sort_keys + compact + utf8
    JSON of each row's ``input``), unique case ids, the SYNTHETIC_HELD_OUT_TEST_SET
    cohort label, absence of oracle leakage inside ``input``, presence of the
    annotation provenance marker, and a matching ``holdout_manifest.json``.
    """
    holdout_dir = (root or ROOT) / "fixtures" / "holdout"
    issues: List[str] = []
    stats: Dict[str, Any] = {"files": {}, "total_cases": 0}
    if not holdout_dir.is_dir():
        issues.append(f"Holdout directory missing: {holdout_dir}")
        return {"issues": issues, "stats": stats}

    total = 0
    files_stats: Dict[str, Any] = {}
    for study in [f"LN-{i:02d}" for i in range(1, 11)]:
        f = holdout_dir / f"{study}_holdout.jsonl"
        if not f.is_file():
            issues.append(f"Missing holdout file: {f.name}")
            continue
        seen: set[str] = set()
        n = 0
        file_ok = True
        for lineno, line in enumerate(f.open(encoding="utf-8"), 1):
            if not line.strip():
                continue
            n += 1
            try:
                row = json.loads(line)
                if row.get("paper_id") != study:
                    raise AssertionError(f"paper_id {row.get('paper_id')!r} != {study}")
                if row.get("cohort") != "SYNTHETIC_HELD_OUT_TEST_SET":
                    raise AssertionError(f"cohort not SYNTHETIC_HELD_OUT_TEST_SET: {row.get('cohort')!r}")
                if row.get("input_hash") != jsonhash(row.get("input")):
                    raise AssertionError("input_hash does not match canonical hash of input")
                inp = row.get("input", {})
                if "oracle" in inp or "expected_decision" in inp:
                    raise AssertionError("data leakage: oracle/expected_decision inside input")
                if not row.get("annotation_provenance"):
                    raise AssertionError("missing annotation_provenance")
                cid = row.get("case_id")
                if not cid or cid in seen:
                    raise AssertionError(f"duplicate or missing case_id: {cid}")
                seen.add(cid)
            except Exception as e:
                file_ok = False
                issues.append(f"{f.name}:{lineno}: {e}")
                if len(issues) > 50:
                    break
        total += n
        files_stats[f.name] = {
            "cases": n,
            "sha256": h(f),
            "all_input_hashes_valid": file_ok,
        }
        if not file_ok:
            issues.append(f"{study}: holdout integrity failed")
        elif n != 120:
            issues.append(f"{study}: expected 120 holdout cases, found {n}")

    stats["files"] = files_stats
    stats["total_cases"] = total
    if total != 1200:
        issues.append(f"expected 1200 total holdout cases, found {total}")

    manifest_path = holdout_dir / "holdout_manifest.json"
    if not manifest_path.is_file():
        issues.append("Missing holdout_manifest.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("hash_standard") != "sha256(sort_keys,compact,utf8)":
                issues.append("holdout_manifest hash_standard mismatch")
            if manifest.get("total_cases") != total:
                issues.append(f"holdout_manifest total_cases {manifest.get('total_cases')} != {total}")
            for name, info in files_stats.items():
                entry = manifest.get("files", {}).get(name, {})
                if entry.get("sha256") != info["sha256"]:
                    issues.append(f"holdout_manifest sha256 mismatch for {name}")
                if entry.get("cases") != info["cases"]:
                    issues.append(f"holdout_manifest case-count mismatch for {name}")
        except Exception as e:
            issues.append(f"Cannot parse holdout_manifest.json: {e}")

    return {"issues": issues, "stats": stats}


def write_holdout_manifest(root: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Regenerate holdout_manifest.json from the on-disk held-out test sets.

    Byte-deterministic: the manifest is a pure function of fixture content and
    contains no wall-clock timestamp, so identical fixtures always yield an
    identical manifest.
    """
    holdout_dir = (root or ROOT) / "fixtures" / "holdout"
    files: Dict[str, Any] = {}
    total = 0
    for f in sorted(holdout_dir.glob("LN-*_holdout.jsonl")):
        n = sum(1 for line in f.open(encoding="utf-8") if line.strip())
        total += n
        files[f.name] = {"sha256": h(f), "cases": n, "all_input_hashes_valid": True}
    manifest = {
        "hash_standard": "sha256(sort_keys,compact,utf8)",
        "total_cases": total,
        "files": files,
    }
    out = holdout_dir / "holdout_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


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
    ap.add_argument(
        "--write-holdout-manifest",
        action="store_true",
        help="Regenerate holdout_manifest.json from current fixtures, then validate",
    )
    a = ap.parse_args()

    if a.write_holdout_manifest:
        written = write_holdout_manifest()
        print(f"Wrote {written}")

    s = verify_spec(a.spec)
    holdouts = verify_holdouts(ROOT.parent / "research" if (ROOT.parent / "research").is_dir() else ROOT)
    status = "PASS" if not s["issues"] and not holdouts["issues"] else "FAIL"
    out: Dict[str, Any] = {
        "status": status,
        "spec": str((a.spec or ROOT).resolve()),
        "spec_validation": s,
        "holdout_validation": holdouts,
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
        "holdout_total": holdouts["stats"]["total_cases"],
        "issues": s["issues"]
        + holdouts["issues"]
        + (out.get("manuscripts_validation", {}).get("issues", [])),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
