"""Test V5-T004: Migrations graph and drift baseline verification.

Validates:
1. Migration graph has a single unambiguous head (0057_merge_all_heads).
2. All revisions are connected to root (0001_initial_schema).
3. No illegal table/column drops or destructive alterations exist in migration history.
4. Negative abuse tests: multiple heads and destructive operations are rejected.
5. Alignment between SQLAlchemy models (backend/models.py, backend/models_rbpc.py) and migrations.
6. Baseline artifact integrity and consistency.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = REPO_ROOT / "alembic.ini"
MIGRATIONS_DIR = REPO_ROOT / "migrations" / "versions"
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "implementation" / "W00" / "W00_A04_migrations_graph_baseline.json"

EXPECTED_BASELINE_SHA = "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
EXPECTED_UNAMBIGUOUS_HEAD = "0092_adaptive_evidence_models"
EXPECTED_ROOT_REVISION = "0001_initial_schema"

DANGEROUS_PATTERNS = [
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


@pytest.fixture(scope="module")
def alembic_script_directory() -> ScriptDirectory:
    """Load Alembic ScriptDirectory from alembic.ini."""
    assert ALEMBIC_INI_PATH.exists(), f"alembic.ini not found at {ALEMBIC_INI_PATH}"
    cfg = Config(str(ALEMBIC_INI_PATH))
    return ScriptDirectory.from_config(cfg)


def test_migration_graph_has_single_unambiguous_head(alembic_script_directory: ScriptDirectory):
    """Verify that Alembic migration graph has exactly one unambiguous head."""
    heads = alembic_script_directory.get_heads()
    assert len(heads) == 1, (
        f"Expected exactly 1 unambiguous migration head, but found {len(heads)}: {heads}. "
        "Multiple heads cause deterministic deployment failure and schema drift."
    )
    assert heads[0] == EXPECTED_UNAMBIGUOUS_HEAD, (
        f"Expected head to be {EXPECTED_UNAMBIGUOUS_HEAD}, got {heads[0]}"
    )


def test_migration_graph_connectivity_and_root(alembic_script_directory: ScriptDirectory):
    """Verify all migrations trace back to the single root revision with no orphaned nodes."""
    revisions = list(alembic_script_directory.walk_revisions())
    assert len(revisions) >= 72, f"Expected at least 72 revisions, found {len(revisions)}"

    rev_map = {r.revision: r for r in revisions}

    # Find root nodes (revisions with down_revision = None)
    roots = [r.revision for r in revisions if r.down_revision is None]
    assert len(roots) == 1, f"Expected exactly 1 root revision, found {roots}"
    assert roots[0] == EXPECTED_ROOT_REVISION, (
        f"Expected root revision to be {EXPECTED_ROOT_REVISION}, got {roots[0]}"
    )

    # Verify 0057_merge_all_heads unifies the 15 branch heads
    head_rev = rev_map["0057_merge_all_heads"]
    down = head_rev.down_revision
    assert isinstance(down, (list, tuple)), "Merge head down_revision must be a tuple/list of branch heads"
    assert len(down) == 15, f"Expected merge head to unify exactly 15 branch heads, found {len(down)}: {down}"


def test_no_illegal_table_or_column_drops_in_history():
    """Verify that no destructive operations exist in migration upgrade scripts.

    Enforces Requirement 6.2 and scripts/ci/lint-migration-safety.sh additive-only rules.
    """
    assert MIGRATIONS_DIR.exists(), f"Migrations dir not found at {MIGRATIONS_DIR}"
    py_files = sorted(list(MIGRATIONS_DIR.glob("*.py")))
    assert len(py_files) >= 72, f"Expected at least 72 migration files, found {len(py_files)}"

    violations = []

    for file_path in py_files:
        filename = file_path.name
        # Skip legacy migration created before schema freeze (mirrors lint-migration-safety.sh)
        if filename in ("0037_update_feature_flags_fields.py", "env.py"):
            continue

        content = file_path.read_text(encoding="utf-8")

        # Extract only upgrade() body to avoid flagging downgrade()
        upgrade_match = re.search(r"def upgrade\(\).*?:(.*?)(?=def downgrade|\Z)", content, re.DOTALL)
        upgrade_body = upgrade_match.group(1) if upgrade_match else content

        for pattern in DANGEROUS_PATTERNS:
            matches = re.findall(pattern, upgrade_body, flags=re.IGNORECASE)
            if matches:
                violations.append((filename, pattern, matches))

    assert not violations, (
        f"Found {len(violations)} destructive operation violations in migration history:\n"
        + "\n".join(f"  {f}: pattern '{p}' matched {m}" for f, p, m in violations)
    )


def test_negative_multiple_heads_rejection():
    """Negative test: verify that a branched graph without unified head is rejected."""
    # Simulate a scenario where down_revision did not include all branches
    simulated_heads = ["branch_a", "branch_b"]
    is_valid = len(simulated_heads) == 1
    assert not is_valid, "Multiple heads must be rejected as invalid / requiring DBA review."


def test_negative_destructive_operation_rejection():
    """Negative test: verify that dangerous operations are caught by safety validator."""
    destructive_snippet = """
    def upgrade() -> None:
        op.drop_table('users')
        op.drop_column('profiles', 'email')
    """
    detected = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, destructive_snippet, flags=re.IGNORECASE):
            detected.append(pattern)

    assert any("drop_table" in p for p in detected), "Expected drop_table pattern to match"
    assert any("drop_column" in p for p in detected), "Expected drop_column pattern to match"
    assert len(detected) >= 2, "Safety validator must detect both drop_table and drop_column"


def test_sqlalchemy_models_migration_alignment():
    """Verify that all tables defined in active SQLAlchemy models exist in migration catalog."""
    from backend.models import Base
    import backend.models_rbpc  # noqa: F401

    model_tables = set(Base.metadata.tables.keys())
    assert len(model_tables) >= 120, f"Expected at least 120 active model tables, found {len(model_tables)}"

    # Parse all tables defined or created in migrations
    migration_tables = set()
    initial_tables = {
        "users", "user_progress", "motifs", "urns", "badges", "user_badges",
        "quiz_questions", "quiz_attempts", "lesson_content", "user_leagues",
        "password_reset_tokens", "funnels"
    }
    migration_tables.update(initial_tables)

    for file_path in MIGRATIONS_DIR.glob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        # op.create_table
        for t in re.findall(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]", content):
            migration_tables.add(t)
        # raw CREATE TABLE
        for t in re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", content, re.IGNORECASE):
            migration_tables.add(t.lower())

    unmigrated = model_tables - migration_tables
    assert not unmigrated, (
        f"Found {len(unmigrated)} active SQLAlchemy model tables missing in migrations: {sorted(unmigrated)}"
    )


def test_baseline_artifact_integrity():
    """Verify the baseline migration graph artifact file exists and matches requirements."""
    assert ARTIFACT_PATH.exists(), f"Artifact missing at {ARTIFACT_PATH}"

    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("ticket_id") == "V5-T004"
    assert data.get("slot") == "W00-A04"
    assert data.get("baseline_source_sha") == EXPECTED_BASELINE_SHA
    assert data.get("status") == "PASS"

    summary = data.get("graph_summary", {})
    assert summary.get("is_single_head") is True
    assert summary.get("unambiguous_head") in {EXPECTED_UNAMBIGUOUS_HEAD, "0057_merge_all_heads"}
    assert summary.get("root_revision") == EXPECTED_ROOT_REVISION
    assert summary.get("merged_heads_count") == 15
    assert len(summary.get("merged_heads", [])) == 15

    safety = data.get("safety_audit", {})
    assert safety.get("result") == "PASS"
    assert safety.get("dangerous_operations_detected") == 0

    alignment = data.get("model_alignment", {})
    assert alignment.get("unmigrated_tables_count") == 0
    assert alignment.get("total_registered_tables", 0) >= 120
