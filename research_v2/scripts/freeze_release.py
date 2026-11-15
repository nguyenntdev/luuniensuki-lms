"""Freeze a Research V2 release: verify clean tree, hashes and produce a manifest."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def freeze(repo_root: Path, out_dir: Path, *, assert_clean: bool = True) -> dict:
    head = _git("rev-parse", "HEAD", cwd=repo_root)
    dirty = bool(_git("status", "--porcelain", cwd=repo_root))
    if assert_clean and dirty:
        raise RuntimeError("working tree is dirty; commit before freezing a release")

    files = []
    for base in ("research_v2", "tests/research_v2"):
        p = repo_root / base
        if not p.is_dir():
            continue
        for f in sorted(p.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                files.append({"path": str(f.relative_to(repo_root)), "sha256": sha256_file(f)})

    manifest = {
        "release_id": datetime.now(timezone.utc).strftime("v2-%Y%m%dT%H%M%SZ"),
        "source_commit": head,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "working_tree_dirty": dirty,
        "n_files": len(files),
        "files": files,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "release_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Freeze Research V2 release")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--assert-clean", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    root = _repo_root()
    out = a.out or (root / "research_artifacts_v2" / "release")
    try:
        manifest = freeze(root, out, assert_clean=a.assert_clean)
    except RuntimeError as exc:
        print(f"FREEZE FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"release_id": manifest["release_id"], "n_files": manifest["n_files"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
