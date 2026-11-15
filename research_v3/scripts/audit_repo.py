"""V3-G00 / V3-G11: pin the current git SHA + file inventory hashes.

Writes ``research_v3/data_frozen/source_lock.json`` (or a file under a caller
supplied ``--output`` path) recording the HEAD commit, the pinned SHA passed via
``--source-sha``, whether they match, and a SHA-256 inventory of the V3 source
tree. Every generated file records the timestamp of its creation, so each run
produces a FRESH file; history is never mutated.

The previous audit ``research_v2/reports/G0_repo_audit.json`` is read-only and
is marked HISTORIC in the new lock (its observed SHA is copied verbatim, never
rewritten). This script MUST use ``research_v2.contracts.canonical_hash`` as
the single hashing standard.

Fail-closed: exit 2 when the working tree is dirty unless ``--allow-dirty`` is
given; exit 3 when ``--strict`` and the observed HEAD does not match the pin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_bytes, sha256_input
from research_v3.scripts._paths import (
    DATA_FROZEN_DIR,
    HISTORIC_G0_AUDIT,
    RESEARCH_V2_ROOT,
    RESEARCH_V3_ROOT,
)

# Paths hashed into the inventory (relative to repo root). Keep this list
# explicit: the lock is only meaningful when its scope is pinned.
INVENTORY_ROOTS = (
    "research_v3",
    "tests/research_v3",
)
INVENTORY_SUFFIXES = (".py", ".yaml", ".yml", ".json", ".md", ".toml")

EXIT_OK = 0
EXIT_DIRTY = 2
EXIT_PIN_MISMATCH = 3


class AuditRepoError(RuntimeError):
    """Raised when the repository audit cannot produce a trustworthy lock."""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AuditRepoError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_head(repo: Path = None) -> str:  # type: ignore[assignment]
    return _git(Path(__file__).resolve().parents[2], "rev-parse", "HEAD")


def working_tree_dirty(repo: Path = None) -> tuple[bool, list[str]]:  # type: ignore[assignment]
    repo = repo or Path(__file__).resolve().parents[2]
    out = _git(repo, "status", "--porcelain")
    paths = [line[3:].strip().strip('"') for line in out.splitlines() if line.strip()]
    return bool(paths), paths


def _inventory_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for rel_root in INVENTORY_ROOTS:
        root = repo / rel_root
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix not in INVENTORY_SUFFIXES:
                continue
            files.append(path)
    return files


def build_inventory(repo: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in _inventory_files(repo):
        rel = path.relative_to(repo).as_posix()
        entries.append({"path": rel, "sha256": sha256_bytes(path.read_bytes())})
    return entries


def read_historic_audit(path: Path | None = None) -> dict | None:
    """Load the HISTORIC G0 audit read-only; None when the file is absent."""
    target = Path(path or HISTORIC_G0_AUDIT)
    if not target.is_file():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuditRepoError(f"historic audit {target} is not valid JSON: {exc}") from exc


def build_source_lock(
    *,
    repo: Path,
    source_sha: str | None,
    allow_dirty: bool,
    python_version: str,
    now_utc: str | None = None,
) -> dict:
    """Assemble the source-lock record. Pure: no filesystem writes here."""
    head = git_head(repo)
    dirty, dirty_paths = working_tree_dirty(repo)
    if dirty and not allow_dirty:
        raise AuditRepoError(
            f"working tree is dirty ({len(dirty_paths)} path(s)); commit or pass --allow-dirty"
        )
    if source_sha is not None and not source_sha.strip():
        raise AuditRepoError("--source-sha must be a non-empty commit SHA")

    historic = read_historic_audit()
    inventory = build_inventory(repo)
    inventory_digest = sha256_input(inventory)

    now = now_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "research_v3.source_lock/v1",
        "generated_at_utc": now,
        "task_ids": ["V3-G00", "V3-G11"],
        "git_head_observed": head,
        "source_sha_pinned": (source_sha or head),
        "head_matches_pinned": (source_sha is None or head == source_sha),
        "working_tree_dirty": dirty,
        "dirty_paths": dirty_paths,
        "hash_standard": "sha256(sort_keys,compact,utf8) via research_v2.contracts.canonical_hash",
        "inventory_scope": list(INVENTORY_ROOTS),
        "n_inventory_files": len(inventory),
        "inventory_sha256": inventory_digest,
        "inventory": inventory,
        "historic_prior_audit": {
            "path": str(HISTORIC_G0_AUDIT.relative_to(repo)),
            "status": "HISTORIC",
            "observed_sha_recorded": (historic or {}).get("source_sha_observed"),
            "pinned_sha_recorded": (historic or {}).get("source_sha_pinned"),
            "note": (
                "Read-only reference. The prior V2 audit file was NOT modified; its "
                "observed SHA is copied verbatim as history, never regenerated."
            ),
        },
        "python_version": python_version,
        "fail_closed": {
            "allow_dirty_used": allow_dirty,
            "strict_pin_enforced": True,
        },
    }


def _default_output() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DATA_FROZEN_DIR / f"source_lock_{stamp}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.audit_repo",
        description=(
            "Pin the current git SHA plus a SHA-256 file inventory into a fresh "
            "source-lock JSON (V3-G00/V3-G11). Fail-closed on a dirty tree."
        ),
    )
    parser.add_argument(
        "--source-sha",
        default=None,
        help="Pinned SHA the release claims to correspond to (defaults to observed HEAD)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Permit a dirty working tree (recorded in the lock) instead of exiting 2",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when the observed HEAD does not match --source-sha",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: a fresh timestamped file in research_v3/data_frozen/)",
    )
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parents[2]
    try:
        lock = build_source_lock(
            repo=repo,
            source_sha=args.source_sha,
            allow_dirty=args.allow_dirty,
            python_version=sys.version.split()[0],
        )
    except AuditRepoError as exc:
        print(f"FAIL audit_repo: {exc}", file=sys.stderr)
        return EXIT_DIRTY if "dirty" in str(exc) else 4

    if args.strict and not lock["head_matches_pinned"]:
        print(
            f"FAIL audit_repo: HEAD {lock['git_head_observed']} != pinned "
            f"{lock['source_sha_pinned']}",
            file=sys.stderr,
        )
        return EXIT_PIN_MISMATCH

    output = args.output or _default_output()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"OK audit_repo: head={lock['git_head_observed'][:12]} "
        f"pinned={lock['source_sha_pinned'][:12]} files={lock['n_inventory_files']} "
        f"inventory_sha256={lock['inventory_sha256'][:12]} -> {output}"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
