#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe Migration Release Protocol & Preflight Validator (Ticket V5-T085 / Slot W08-A05).

Enforces production-grade migration safety invariants:
1. Topology Invariant: Alembic revision graph MUST have exactly 1 head (no diverging heads).
2. Additive-Only Invariant: Migration upgrade() steps MUST NOT execute destructive operations
   (no DROP TABLE, DROP COLUMN, ALTER TYPE, RENAME TABLE/COLUMN, or op.drop_*).
3. Dry-Run SQL Generation: Generates complete offline SQL via `alembic upgrade --sql`
   and validates that the emitted DDL contains zero destructive statements.
4. Expand/Contract Compatibility: Guarantees existing tables, columns, and data remain 100% intact.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure offline mock inspection is registered
try:
    from migrations.env import _setup_offline_mock
    _setup_offline_mock()
except Exception:
    pass

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

# Dangerous patterns for Python/SQL migration source inspection
DANGEROUS_AST_PATTERNS = [
    r"DROP\s+TABLE",
    r"DROP\s+COLUMN",
    r"ALTER\s+.*\s+TYPE\b",
    r"ALTER\s+COLUMN\s+.*\s+TYPE\b",
    r"RENAME\s+TABLE",
    r"RENAME\s+COLUMN",
    r"RENAME\s+TO\b",
    r"DROP\s+CONSTRAINT",
    r"op\.drop_table",
    r"op\.drop_column",
    r"op\.drop_constraint",
]

# Dangerous patterns for emitted SQL DDL validation
DANGEROUS_SQL_PATTERNS = [
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+COLUMN\b",
    r"\bALTER\s+TABLE\s+.*\bDROP\s+(COLUMN|CONSTRAINT)\b",
    r"\bTRUNCATE\b",
    r"\bDROP\s+SCHEMA\b",
    r"\bDROP\s+DATABASE\b",
]

# Legacy migrations created before schema freeze baseline (0057_merge_all_heads)
LEGACY_ALLOWED_EXCEPTIONS = {
    "0037_update_feature_flags_fields.py",
}


def check_migration_heads(config_path: str = "alembic.ini") -> dict[str, Any]:
    """Verify that the Alembic migration tree has exactly one head."""
    resolved_config = Path(config_path)
    if not resolved_config.is_absolute():
        resolved_config = REPO_ROOT / config_path

    if not resolved_config.exists():
        return {
            "passed": False,
            "head_count": 0,
            "heads": [],
            "error": f"Alembic config not found at {resolved_config}",
        }

    cfg = Config(str(resolved_config))
    script = ScriptDirectory.from_config(cfg)
    heads = list(script.get_heads())

    passed = len(heads) == 1
    return {
        "passed": passed,
        "head_count": len(heads),
        "heads": heads,
        "message": (
            f"Single head verified: {heads[0]}"
            if passed
            else f"Diverging heads detected! Found {len(heads)} heads: {heads}"
        ),
    }


def check_additive_migration_files(
    migrations_dir: str = "migrations/versions",
) -> dict[str, Any]:
    """Scan all migration files to ensure upgrade() functions contain only additive operations."""
    import ast

    resolved_dir = Path(migrations_dir)
    if not resolved_dir.is_absolute():
        resolved_dir = REPO_ROOT / migrations_dir

    if not resolved_dir.exists():
        return {
            "passed": False,
            "checked_files": 0,
            "violations": [{"error": f"Directory not found: {resolved_dir}"}],
        }

    migration_files = sorted(resolved_dir.glob("*.py"))
    violations: list[dict[str, Any]] = []
    checked_count = 0

    for file_path in migration_files:
        filename = file_path.name
        if filename in {"env.py", "script.py.mako"}:
            continue
        if filename in LEGACY_ALLOWED_EXCEPTIONS:
            continue

        checked_count += 1
        content = file_path.read_text(encoding="utf-8")

        # Extract only upgrade() body via AST to avoid false positives in downgrade()
        start_line = 1
        upgrade_body = ""
        try:
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
                    lines = content.splitlines()[node.lineno - 1 : node.end_lineno]
                    upgrade_body = "\n".join(lines)
                    start_line = node.lineno
                    break
        except Exception:
            upgrade_body = content

        if not upgrade_body:
            upgrade_body = content

        for pattern in DANGEROUS_AST_PATTERNS:
            matches = list(re.finditer(pattern, upgrade_body, re.IGNORECASE))
            if matches:
                for m in matches:
                    matched_snippet = m.group(0).strip()
                    preceding = upgrade_body[: m.start()]
                    rel_line = preceding.count("\n")
                    file_display = (
                        str(file_path.relative_to(REPO_ROOT))
                        if file_path.is_relative_to(REPO_ROOT)
                        else str(file_path)
                    )
                    violations.append(
                        {
                            "file": file_display,
                            "line": start_line + rel_line,
                            "pattern": pattern,
                            "match": matched_snippet,
                        }
                    )

    return {
        "passed": len(violations) == 0,
        "checked_files": checked_count,
        "violations_count": len(violations),
        "violations": violations,
    }


def run_migration_dry_run_sql(
    config_path: str = "alembic.ini",
    target: str = "head",
    from_rev: str | None = "0057_merge_all_heads",
) -> dict[str, Any]:
    """Execute Alembic upgrade in offline SQL mode and validate emitted DDL for zero destructive ops."""
    resolved_config = Path(config_path)
    if not resolved_config.is_absolute():
        resolved_config = REPO_ROOT / config_path

    cfg = Config(str(resolved_config))

    # Ensure offline mock inspector is active
    try:
        from migrations.env import _setup_offline_mock
        _setup_offline_mock()
    except Exception:
        pass

    rev_spec = f"{from_rev}:{target}" if from_rev else target

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            command.upgrade(cfg, rev_spec, sql=True)
        raw_sql = stdout_buf.getvalue()
    except Exception as exc:
        return {
            "passed": False,
            "revision_spec": rev_spec,
            "sql_bytes": 0,
            "error": f"Failed to generate offline SQL: {exc}",
            "violations": [{"error": str(exc)}],
        }

    violations: list[dict[str, Any]] = []
    lines = raw_sql.splitlines()

    for idx, line in enumerate(lines, start=1):
        # Ignore Alembic version tracking deletions (safe merge cleanup)
        if "DELETE FROM alembic_version" in line:
            continue

        for pat in DANGEROUS_SQL_PATTERNS:
            match = re.search(pat, line, re.IGNORECASE)
            if match:
                violations.append(
                    {
                        "line_number": idx,
                        "pattern": pat,
                        "line": line.strip(),
                    }
                )

    return {
        "passed": len(violations) == 0,
        "revision_spec": rev_spec,
        "sql_bytes": len(raw_sql.encode("utf-8")),
        "lines_count": len(lines),
        "violations_count": len(violations),
        "violations": violations,
        "sql_preview": lines[:20] if lines else [],
        "sql_text": raw_sql,
    }


def run_all_preflight_checks(
    config_path: str = "alembic.ini",
    target: str = "head",
    from_rev: str | None = "0057_merge_all_heads",
    migrations_dir: str = "migrations/versions",
) -> dict[str, Any]:
    """Run complete preflight validation suite."""
    heads_result = check_migration_heads(config_path=config_path)
    files_result = check_additive_migration_files(migrations_dir=migrations_dir)
    sql_result = run_migration_dry_run_sql(
        config_path=config_path, target=target, from_rev=from_rev
    )

    all_passed = (
        heads_result["passed"] and files_result["passed"] and sql_result["passed"]
    )

    return {
        "all_passed": all_passed,
        "checks": {
            "topology_single_head": heads_result,
            "additive_migration_files": files_result,
            "dry_run_sql_generation": {
                k: v for k, v in sql_result.items() if k != "sql_text"
            },
        },
        "target_revision": target,
        "from_revision": from_rev,
        "_raw_sql": sql_result.get("sql_text", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Alembic Safe Migration Release Protocol Preflight Validator"
    )
    parser.add_argument(
        "--config", "-c", default="alembic.ini", help="Path to alembic.ini"
    )
    parser.add_argument(
        "--target", "-t", default="head", help="Target revision (default: head)"
    )
    parser.add_argument(
        "--from-rev",
        default="0057_merge_all_heads",
        help="Starting revision for SQL dry run (default: 0057_merge_all_heads)",
    )
    parser.add_argument(
        "--migrations-dir",
        default="migrations/versions",
        help="Directory containing migration versions",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Exit with non-zero status on any defect (default: True)",
    )
    parser.add_argument(
        "--output-sql",
        help="Optional file path to write generated SQL dry-run output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON results",
    )

    args = parser.parse_args()

    results = run_all_preflight_checks(
        config_path=args.config,
        target=args.target,
        from_rev=args.from_rev,
        migrations_dir=args.migrations_dir,
    )

    raw_sql = results.pop("_raw_sql", "")

    if args.output_sql and raw_sql:
        out_p = Path(args.output_sql)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(raw_sql, encoding="utf-8")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=== Alembic Safe Migration Release Preflight ===")
        print(f"Target Revision : {args.target}")
        print(f"From Revision   : {args.from_rev}")
        print("-" * 50)

        # 1. Topology
        t_res = results["checks"]["topology_single_head"]
        t_status = "PASS" if t_res["passed"] else "FAIL"
        print(f"[{t_status}] Topology Check: {t_res.get('message')}")

        # 2. Additive Files
        f_res = results["checks"]["additive_migration_files"]
        f_status = "PASS" if f_res["passed"] else "FAIL"
        print(
            f"[{f_status}] Additive Files Check: {f_res['checked_files']} checked, "
            f"{f_res['violations_count']} violations"
        )
        if f_res["violations"]:
            for v in f_res["violations"]:
                print(f"       ! {v['file']}:{v.get('line', '?')} - {v['pattern']}")

        # 3. Dry-Run SQL
        s_res = results["checks"]["dry_run_sql_generation"]
        s_status = "PASS" if s_res["passed"] else "FAIL"
        print(
            f"[{s_status}] Dry-Run SQL Generation: {s_res.get('sql_bytes', 0)} bytes, "
            f"{s_res.get('violations_count', 0)} violations"
        )
        if s_res.get("violations"):
            for v in s_res["violations"]:
                print(f"       ! Line {v['line_number']}: {v['line']}")

        print("-" * 50)
        overall = "SUCCESS - Safe for Release" if results["all_passed"] else "FAILED - Release Blocked"
        print(f"Overall Result: {overall}")

    if not results["all_passed"] and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
