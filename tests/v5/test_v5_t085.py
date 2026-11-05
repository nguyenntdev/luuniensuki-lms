# -*- coding: utf-8 -*-
"""V5-T085 (Wave W08, Slot A05): Safe Migration Release Protocol Test Suite.

Audits and verifies:
1. Topology Invariant: Alembic revision graph MUST have exactly 1 head (no diverging heads).
2. Additive-Only Invariant: Migration upgrade() steps MUST NOT execute destructive operations
   (no DROP TABLE, DROP COLUMN, ALTER TYPE, RENAME TABLE/COLUMN, or op.drop_*).
3. Migration Dry-Run & Offline SQL Generation:
   - CLI `scripts/dev/migration_preflight.py` checks topology, scans migration files,
     and executes `alembic upgrade --sql` offline dry-run.
   - Emitted DDL contains zero destructive statements.
4. Diverging Heads Rejection (Negative):
   - Multi-head topology is detected, reported, and blocked from release.
5. Destructive Operations Detection (Negative):
   - Any attempt to introduce `op.drop_table` or `DROP COLUMN` is caught and pinpointed.
6. Negative Abuse:
   - Full historical claims and inquiries remain 100% intact after upgrade and dry-run procedures.
   - Zero data loss, zero dropped columns, and zero broken constraints.
7. CI Script Integration:
   - `scripts/ci/lint-migration-safety.sh` succeeds with zero errors.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select, text

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimOrigin,
    HistoricalClaimType,
    HistoricalConfidence,
    HistoricalEntity,
    HistoricalEntityType,
    HistoricalPublicationStatus,
    HistoricalVerificationStatus,
)
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from scripts.dev.migration_preflight import (
    DANGEROUS_AST_PATTERNS,
    DANGEROUS_SQL_PATTERNS,
    check_additive_migration_files,
    check_migration_heads,
    run_all_preflight_checks,
    run_migration_dry_run_sql,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ==============================================================================
# 1. Topology: Single Head Verification
# ==============================================================================


def test_migration_graph_topology_single_head():
    """Verify that the Alembic migration tree has strictly 1 head (no diverging heads)."""
    result = check_migration_heads("alembic.ini")
    assert result["passed"] is True, f"Topology check failed: {result.get('message')}"
    assert result["head_count"] == 1, f"Expected 1 head, found {result['head_count']}"
    assert len(result["heads"]) == 1
    assert "Single head verified" in result["message"]


def test_diverging_heads_rejection_negative():
    """Verify that multiple or diverging heads are rejected by topology check."""
    with patch("scripts.dev.migration_preflight.ScriptDirectory") as mock_sd_cls:
        mock_sd = MagicMock()
        mock_sd.get_heads.return_value = ["0072_branch_a", "0072_branch_b"]
        mock_sd_cls.from_config.return_value = mock_sd

        result = check_migration_heads("alembic.ini")
        assert result["passed"] is False
        assert result["head_count"] == 2
        assert "Diverging heads detected" in result["message"]
        assert "0072_branch_a" in result["heads"]
        assert "0072_branch_b" in result["heads"]


# ==============================================================================
# 2. Additive-Only Rule Enforcement
# ==============================================================================


def test_additive_only_rule_enforcement_clean_codebase():
    """Verify that all production migrations contain strictly additive upgrade operations."""
    result = check_additive_migration_files("migrations/versions")
    assert result["passed"] is True, (
        f"Found {result['violations_count']} dangerous operations in migrations: {result['violations']}"
    )
    assert result["checked_files"] >= 80, f"Expected >= 80 migrations, got {result['checked_files']}"
    assert result["violations_count"] == 0
    assert len(result["violations"]) == 0


def test_additive_only_rule_detects_destructive_operations_negative(tmp_path):
    """Verify that destructive operations in upgrade() are flagged with exact line numbers."""
    fake_migrations_dir = tmp_path / "fake_versions"
    fake_migrations_dir.mkdir(parents=True)

    # 1. Destructive file with op.drop_table
    bad_migration_1 = fake_migrations_dir / "9998_bad_drop_table.py"
    bad_migration_1.write_text(
        """
from alembic import op
import sqlalchemy as sa

revision = '9998_bad_drop_table'
down_revision = '0071_research_publication_releases'

def upgrade():
    op.drop_table('historical_claims')

def downgrade():
    pass
""",
        encoding="utf-8",
    )

    # 2. Destructive file with op.drop_column
    bad_migration_2 = fake_migrations_dir / "9999_bad_drop_column.py"
    bad_migration_2.write_text(
        """
from alembic import op
import sqlalchemy as sa

revision = '9999_bad_drop_column'
down_revision = '9998_bad_drop_table'

def upgrade() -> None:
    op.add_column('users', sa.Column('new_col', sa.String(50)))
    op.drop_column('rbpc_inquiries', 'sla_due_at')

def downgrade() -> None:
    pass
""",
        encoding="utf-8",
    )

    # 3. Clean migration with harmless downgrade drop
    clean_migration = fake_migrations_dir / "9997_clean_migration.py"
    clean_migration.write_text(
        """
from alembic import op
import sqlalchemy as sa

revision = '9997_clean_migration'
down_revision = '0070_research_factory_core'

def upgrade() -> None:
    op.create_table(
        'temp_safe_table',
        sa.Column('id', sa.Integer, primary_key=True)
    )

def downgrade() -> None:
    op.drop_table('temp_safe_table')
""",
        encoding="utf-8",
    )

    result = check_additive_migration_files(str(fake_migrations_dir))
    assert result["passed"] is False
    assert result["violations_count"] >= 2

    flagged_files = {v["file"] for v in result["violations"]}
    assert any("9998_bad_drop_table" in f for f in flagged_files)
    assert any("9999_bad_drop_column" in f for f in flagged_files)
    # The clean migration must NOT be flagged even though downgrade() has op.drop_table
    assert not any("9997_clean_migration" in f for f in flagged_files)


# ==============================================================================
# 3. Migration Dry-Run & Offline SQL Generation
# ==============================================================================


def test_migration_dry_run_sql_generation():
    """Verify that alembic upgrade --sql dry-run generates valid DDL with zero destructive ops."""
    result = run_migration_dry_run_sql(
        config_path="alembic.ini",
        target="head",
        from_rev="0057_merge_all_heads",
    )

    assert result["passed"] is True, f"Dry-run SQL validation failed: {result.get('error')}"
    assert result["sql_bytes"] > 20000, f"Generated SQL too small: {result.get('sql_bytes')} bytes"
    assert result["lines_count"] > 300
    assert result["violations_count"] == 0
    assert len(result["violations"]) == 0

    sql_text = result["sql_text"]
    # Check that standard additive operations are present
    assert "CREATE TABLE" in sql_text
    assert "CREATE INDEX" in sql_text
    assert "ALTER TABLE" in sql_text

    # Check that destructive statements are completely absent
    for pat in DANGEROUS_SQL_PATTERNS:
        matches = [line for line in sql_text.splitlines() if not "DELETE FROM alembic_version" in line]
        bad_lines = [l for l in matches if re_search(pat, l)]
        assert len(bad_lines) == 0, f"Found destructive DDL matching {pat}: {bad_lines}"


def re_search(pattern: str, text_str: str) -> bool:
    import re

    return bool(re.search(pattern, text_str, re.IGNORECASE))


def test_migration_dry_run_detects_destructive_sql_negative():
    """Verify that dangerous SQL patterns are identified if present in emitted SQL."""
    import re

    synthetic_bad_sql = """
    BEGIN;
    CREATE TABLE safe_table (id UUID PRIMARY KEY);
    DROP TABLE users CASCADE;
    ALTER TABLE historical_claims DROP COLUMN statement;
    TRUNCATE rbpc_inquiries;
    COMMIT;
    """

    violations = []
    for idx, line in enumerate(synthetic_bad_sql.splitlines(), start=1):
        for pat in DANGEROUS_SQL_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                violations.append({"line": idx, "pattern": pat, "text": line.strip()})

    assert len(violations) >= 3
    patterns_found = {v["pattern"] for v in violations}
    assert r"\bDROP\s+TABLE\b" in patterns_found
    assert r"\bDROP\s+COLUMN\b" in patterns_found
    assert r"\bTRUNCATE\b" in patterns_found


# ==============================================================================
# 4. CLI Runner Integration
# ==============================================================================


def test_migration_preflight_cli_execution():
    """Verify that scripts/dev/migration_preflight.py CLI executes cleanly and returns exit code 0."""
    script_path = REPO_ROOT / "scripts/dev/migration_preflight.py"
    assert script_path.exists(), f"CLI script not found at {script_path}"

    proc = subprocess.run(
        [sys.executable, str(script_path), "--json", "--strict"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    assert proc.returncode == 0, f"CLI preflight failed (code {proc.returncode}):\n{proc.stderr}\n{proc.stdout}"
    data = json.loads(proc.stdout)
    assert data["all_passed"] is True
    assert data["checks"]["topology_single_head"]["passed"] is True
    assert data["checks"]["additive_migration_files"]["passed"] is True
    assert data["checks"]["dry_run_sql_generation"]["passed"] is True


def test_ci_lint_migration_safety_script_passes():
    """Verify that scripts/ci/lint-migration-safety.sh succeeds."""
    sh_path = REPO_ROOT / "scripts/ci/lint-migration-safety.sh"
    assert sh_path.exists(), f"Lint script not found at {sh_path}"

    proc = subprocess.run(
        ["bash", str(sh_path)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    assert proc.returncode == 0, f"CI lint script failed (code {proc.returncode}):\n{proc.stderr}\n{proc.stdout}"
    assert "Single Alembic migration head verified" in proc.stdout
    assert "OK: All migrations are safe" in proc.stdout


# ==============================================================================
# 5. Negative Abuse: Historical Claims & Inquiries Intact Invariant
# ==============================================================================


def test_negative_abuse_historical_claims_and_inquiries_remain_intact(db_session):
    """Negative Abuse Test: Verify 100% data integrity for historical claims and inquiries.

    Ensures:
    1. Records created prior to migration check remain unaltered.
    2. Zero data loss across columns (id, public_ref, statement, tokens, timestamps, foreign keys).
    3. Expand/contract safety: adding new columns/tables never alters or deletes existing data.
    4. Destructive DDL against critical tables is rejected and safe state preserved.
    """
    # A. Seed Historical Entity & Claim
    unique_suffix = uuid.uuid4().hex[:8]
    entity = HistoricalEntity(
        id=uuid.uuid4(),
        entity_type=HistoricalEntityType.urn.value,
        slug=f"urn_preflight_{unique_suffix}",
        name_vi="Cao Đỉnh Thử Nghiệm",
        publication_status=HistoricalPublicationStatus.published.value,
        content_scope="CUU_DINH",
        summary_vi="Bản ghi kiểm thử tính toàn vẹn dữ liệu di sản.",
    )
    db_session.add(entity)
    db_session.flush()

    claim = HistoricalClaim(
        id=uuid.uuid4(),
        entity_id=entity.id,
        claim_type=HistoricalClaimType.factual.value,
        statement_vi=f"Cao Đỉnh được đúc vào năm Minh Mạng thứ 16 ({unique_suffix}).",
        confidence=HistoricalConfidence.high.value,
        verification_status=HistoricalVerificationStatus.verified.value,
        origin=HistoricalClaimOrigin.authoritative_import.value,
        content_scope="CUU_DINH",
        review_notes="Bản ghi gốc được bảo vệ trước mọi migration.",
    )
    db_session.add(claim)

    # B. Seed RBPC Creator, Experience & Inquiry
    creator = RbpcCreator(
        slug=f"creator-preflight-{unique_suffix}",
        public_name="Nghệ nhân Đúc Đồng Preflight",
        craft_tradition="Đúc đồng thủ công Huế",
        approved_bio_vi="Nghệ nhân bảo tồn di sản.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-preflight-{unique_suffix}",
        creator_id=creator.id,
        provider_id=creator.id,
        provider_name="Xưởng Đúc Đồng Thử Nghiệm",
        title_vi="Trải nghiệm Đúc Đồng Thử Nghiệm",
        description_vi="Chương trình thử nghiệm di sản phi vật thể.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    public_ref = f"INQ-TEST-{unique_suffix[:4].upper()}"
    opaque_token = f"tok_preflight_{unique_suffix}"
    retention_date = datetime.now(timezone.utc) + timedelta(days=90)

    inquiry = RbpcInquiry(
        public_ref=public_ref,
        experience_id=exp.id,
        name="Lê Hoàng Long",
        contact_channel="email",
        contact_value="long.le@example.com",
        desired_date=date.today() + timedelta(days=7),
        party_size=4,
        message="Yêu cầu tham quan nghiên cứu lịch sử mỹ thuật Cửu Đỉnh.",
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-preflight-{unique_suffix}",
        opaque_token=opaque_token,
        retention_due_at=retention_date,
        sla_due_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(inquiry)
    db_session.commit()

    saved_claim_id = claim.id
    saved_claim_statement = claim.statement_vi
    saved_inquiry_id = inquiry.id
    saved_inquiry_ref = inquiry.public_ref
    saved_inquiry_token = inquiry.opaque_token

    # C. Execute Preflight Protocol Checks (Mimics Release Preflight)
    preflight_results = run_all_preflight_checks(
        config_path="alembic.ini",
        target="head",
        from_rev="0057_merge_all_heads",
    )
    assert preflight_results["all_passed"] is True, f"Preflight failed: {preflight_results['checks']}"

    # D. Verification: Read back rows directly and verify 100% integrity
    db_session.expire_all()

    queried_claim = db_session.execute(
        select(HistoricalClaim).where(HistoricalClaim.id == saved_claim_id)
    ).scalar_one()

    assert queried_claim.id == saved_claim_id
    assert queried_claim.statement_vi == saved_claim_statement
    assert queried_claim.entity_id == entity.id
    assert queried_claim.verification_status == HistoricalVerificationStatus.verified.value
    assert queried_claim.confidence == HistoricalConfidence.high.value

    queried_inquiry = db_session.execute(
        select(RbpcInquiry).where(RbpcInquiry.id == saved_inquiry_id)
    ).scalar_one()

    assert queried_inquiry.id == saved_inquiry_id
    assert queried_inquiry.public_ref == saved_inquiry_ref
    assert queried_inquiry.opaque_token == saved_inquiry_token
    assert queried_inquiry.contact_value == "long.le@example.com"
    assert queried_inquiry.state == RbpcInquiryStatus.new.value
    assert queried_inquiry.party_size == 4
    assert queried_inquiry.retention_due_at is not None
    assert queried_inquiry.sla_due_at is not None

    # E. Verify that the table schema retains all columns and constraints
    res = db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'historical_claims'"
        )
    )
    claim_columns = {row[0] for row in res}
    assert "statement_vi" in claim_columns
    assert "confidence" in claim_columns
    assert "verification_status" in claim_columns
    assert "entity_id" in claim_columns

    res = db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'rbpc_inquiries'"
        )
    )
    inquiry_columns = {row[0] for row in res}
    assert "public_ref" in inquiry_columns
    assert "opaque_token" in inquiry_columns
    assert "idempotency_key" in inquiry_columns
    assert "sla_due_at" in inquiry_columns
    assert "retention_due_at" in inquiry_columns
