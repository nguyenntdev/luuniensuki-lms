#!/usr/bin/env python3
"""Audit script to ensure no legacy content or forbidden terms leak into the STTT scope.

Scope targets:
- data/imperial/
- frontend/src/app/dai-noi/
- frontend/src/components/imperial/
- backend/imperial_models.py
- backend/routers/imperial*.py

Forbidden terms:
- cửu đỉnh
- cuu dinh
- cao đỉnh
- nhân đỉnh
- chương đỉnh
- anh đỉnh
- nghị đỉnh
- thuần đỉnh
- tuyên đỉnh
- dụ đỉnh
- huyền đỉnh
- 162
- bản đúc nổi
- relief motif
- urnslug
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

FORBIDDEN_TERMS: tuple[str, ...] = (
    "cửu đỉnh",
    "cuu dinh",
    "cao đỉnh",
    "nhân đỉnh",
    "chương đỉnh",
    "anh đỉnh",
    "nghị đỉnh",
    "thuần đỉnh",
    "tuyên đỉnh",
    "dụ đỉnh",
    "huyền đỉnh",
    "162",
    "bản đúc nổi",
    "relief motif",
    "urnslug",
)

TARGET_PATTERNS: tuple[str, ...] = (
    "data/imperial/**/*",
    "data/imperial/*",
    "frontend/src/app/dai-noi/**/*",
    "frontend/src/app/dai-noi/*",
    "frontend/src/components/imperial/**/*",
    "frontend/src/components/imperial/*",
    "backend/imperial_models.py",
    "backend/routers/imperial*.py",
)

TEXT_EXTENSIONS: tuple[str, ...] = (
    ".json",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".md",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
)


@dataclass(frozen=True)
class Violation:
    file_path: str
    line_number: int
    matched_term: str
    line_snippet: str


def find_target_files(repo_root: Path) -> list[Path]:
    """Resolve and collect existing text files across the target patterns."""
    collected: set[Path] = set()

    for pattern in TARGET_PATTERNS:
        full_pattern = str(repo_root / pattern)
        for match_str in glob.glob(full_pattern, recursive=True):
            p = Path(match_str)
            if p.is_file():
                if p.suffix.lower() in TEXT_EXTENSIONS or not p.suffix:
                    collected.add(p)

    return sorted(collected)


def scan_file_for_violations(
    file_path: Path, forbidden_terms: Sequence[str] = FORBIDDEN_TERMS
) -> list[Violation]:
    """Scan a single text file for occurrences of any forbidden term."""
    violations: list[Violation] = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        print(f"[WARN] Unable to read file {file_path}: {exc}", file=sys.stderr)
        return violations

    for line_idx, line in enumerate(content.splitlines(), start=1):
        line_lower = line.lower()
        for term in forbidden_terms:
            if term.lower() in line_lower:
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_number=line_idx,
                        matched_term=term,
                        line_snippet=line.strip()[:140],
                    )
                )

    return violations


def audit_scope(
    repo_root: Path | None = None,
    forbidden_terms: Sequence[str] = FORBIDDEN_TERMS,
) -> list[Violation]:
    """Audit the STTT imperial scope for forbidden legacy terms."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    target_files = find_target_files(repo_root)
    all_violations: list[Violation] = []

    for file_path in target_files:
        all_violations.extend(scan_file_for_violations(file_path, forbidden_terms))

    return all_violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit STTT Imperial scope against legacy and forbidden terms"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to repository root (defaults to parent directory tree)",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[2]
    print(f"[AUDIT] Scanning STTT scope under repo root: {repo_root}")

    target_files = find_target_files(repo_root)
    print(f"[AUDIT] Found {len(target_files)} target file(s) in STTT imperial scope.")
    for f in target_files:
        print(f"  - {f.relative_to(repo_root)}")

    violations = audit_scope(repo_root)

    if violations:
        print(f"\n[FAIL] Found {len(violations)} forbidden term violation(s):")
        for v in violations:
            rel = Path(v.file_path).relative_to(repo_root)
            print(
                f"  {rel}:{v.line_number} -> Forbidden: {v.matched_term!r}\n"
                f"    Snippet: {v.line_snippet}"
            )
        return 1

    print("\n[SUCCESS] No forbidden legacy content found in STTT imperial scope. All clean!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
