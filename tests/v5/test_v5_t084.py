# -*- coding: utf-8 -*-
"""V5-T084: Automated Backup and Restoration Rehearsal Test Suite.

Wave W08, Slot A04 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Automated backup script execution:
   - Dumps PostgreSQL schema and data.
   - Compresses with gzip and computes SHA-256 integrity checksum.
   - Supports AES-256-CBC passphrase encryption.
2. Restore rehearsal into disposable drill database (luuniensuki_restore_drill):
   - Restores dump into disposable test database without touching live DB.
   - Verifies exact table and row counts (users, heritage_places, historical_entities, rbpc_inquiries, etc.).
   - Generates structured RPO / RTO verification report JSON with valid metrics.
3. Negative abuse & security invariants:
   - Damaged, tampered, or bit-rotted backup fails integrity check and does NOT overwrite live DB.
   - 0-byte / empty backup fails integrity check.
   - Live DB protection guard strictly aborts if target equals live database.
   - Invalid passphrase triggers decryption failure without corrupting state.
4. Shell scripts CLI interoperability:
   - scripts/backup/backup-database.sh and scripts/backup/restore-rehearsal.sh run end-to-end.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import psycopg
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import (
    HeritagePlace,
    HistoricalEntity,
    User,
    UserRole,
)
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services.backup_restore import (
    CRITICAL_VERIFICATION_TABLES,
    DEFAULT_DRILL_DB,
    BackupError,
    DecryptionError,
    IntegrityError,
    LiveDatabaseProtectionError,
    create_backup,
    decrypt_data,
    encrypt_data,
    get_all_table_counts,
    restore_rehearsal,
    verify_backup_integrity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def backup_test_dir() -> Generator[Path, None, None]:
    """Temporary directory for backup artifacts during test run."""
    td = tempfile.mkdtemp(prefix="test_backup_v5_t084_")
    path = Path(td)
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def cleanup_drill_database() -> Generator[None, None, None]:
    """Ensure disposable drill database is cleaned up before and after each test."""
    yield
    # Cleanup disposable drill DB after test
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")
    clean_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")
    from urllib.parse import urlparse
    p = urlparse(clean_url)
    maint_url = f"postgresql://{p.username}:{p.password or ''}@{p.hostname}:{p.port or 5432}/postgres"
    try:
        with psycopg.connect(maint_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();",
                    (DEFAULT_DRILL_DB,),
                )
                cur.execute(f'DROP DATABASE IF EXISTS "{DEFAULT_DRILL_DB}";')
    except Exception:
        pass


def test_backup_script_execution_and_checksum_generation(
    backup_test_dir: Path,
) -> None:
    """Requirement 1: Dumps DB, compresses with gzip, computes valid SHA-256."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    res = create_backup(
        source_db_url=db_url,
        output_dir=backup_test_dir,
        filename_prefix="t084_unencrypted",
    )

    archive_path = Path(res["archive_path"])
    sha256_path = Path(res["sha256_path"])
    meta_path = Path(res["meta_path"])

    assert archive_path.is_file(), "Backup archive file was not created"
    assert archive_path.stat().st_size > 0, "Backup archive is empty"
    assert archive_path.name.endswith(".sql.gz"), "Expected .sql.gz extension for unencrypted backup"

    # Verify checksum file
    assert sha256_path.is_file(), "Checksum file was not created"
    checksum_content = sha256_path.read_text(encoding="utf-8").strip()
    assert res["archive_sha256"] in checksum_content

    # Verify metadata JSON
    assert meta_path.is_file(), "Metadata JSON was not created"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["backup_id"].startswith("backup_")
    assert meta["archive_sha256"] == res["archive_sha256"]
    assert meta["is_encrypted"] is False
    assert meta["compression"] == "gzip"
    assert isinstance(meta["table_counts"], dict)
    assert len(meta["table_counts"]) > 0

    # Verify integrity tool passes
    v_res = verify_backup_integrity(archive_path, meta_path=meta_path)
    assert v_res["integrity_status"] == "VALID"
    assert v_res["computed_sha256"] == res["archive_sha256"]
    assert v_res["decompressed_sql_bytes"] > 0


def test_passphrase_encrypted_backup_and_decryption_lifecycle(
    backup_test_dir: Path,
) -> None:
    """Requirement 1: Supports encryption/passphrase protection with AES-256-CBC."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")
    passphrase = "V5_T084_StrongPassphrase_2026!"

    res = create_backup(
        source_db_url=db_url,
        output_dir=backup_test_dir,
        filename_prefix="t084_encrypted",
        passphrase=passphrase,
    )

    archive_path = Path(res["archive_path"])
    assert archive_path.name.endswith(".sql.gz.enc")
    assert res["is_encrypted"] is True
    assert res["encryption_cipher"] == "aes-256-cbc"

    # Integrity verification with correct passphrase
    v_res = verify_backup_integrity(archive_path, passphrase=passphrase)
    assert v_res["integrity_status"] == "VALID"
    assert v_res["is_encrypted"] is True
    assert v_res["decompressed_sql_bytes"] > 0

    # Negative test: Decryption fails with wrong passphrase
    with pytest.raises(DecryptionError) as exc_info:
        verify_backup_integrity(archive_path, passphrase="WrongPassword_Abuse!")
    assert "Decryption failed" in str(exc_info.value)

    # Negative test: Decryption fails if passphrase omitted for encrypted archive
    with pytest.raises(DecryptionError) as exc_info2:
        verify_backup_integrity(archive_path, passphrase=None)
    assert "no passphrase was provided" in str(exc_info2.value)


def test_restore_rehearsal_recovers_exact_content_without_data_loss(
    engine,
    backup_test_dir: Path,
) -> None:
    """Requirement 2: Restores into disposable DB and verifies exact table and row counts."""
    # Seed known distinct entities in the live test DB across core tables
    # Committed directly so pg_dump process can capture them.
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    test_token = uuid.uuid4().hex[:8]

    user_email = f"rehearsal_student_{test_token}@example.com"
    user_username = f"student_{test_token}"

    with SessionLocal() as direct_session:
        # 1. users
        test_user = User(
            email=user_email,
            username=user_username,
            password_hash=hash_password("Password123!"),
            display_name="Rehearsal Test Student",
            role=UserRole.learner,
        )
        direct_session.add(test_user)

        # 2. heritage_places
        test_place = HeritagePlace(
            slug=f"rehearsal-site-{test_token}",
            name_vi=f"Di tích diễn tập {test_token}",
            name_en=f"Rehearsal Site {test_token}",
            entity_type="monument",
            heritage_category="tangible",
            location_lat=16.469,
            location_lon=107.579,
        )
        direct_session.add(test_place)

        # 3. historical_entities
        test_entity = HistoricalEntity(
            entity_type="monument",
            slug=f"rehearsal-entity-{test_token}",
            name_vi=f"Thực thể lịch sử diễn tập {test_token}",
            name_en=f"Rehearsal Historical Entity {test_token}",
            summary_vi="Thực thể kiểm tra diễn tập khôi phục hệ thống.",
            publication_status="published",
        )
        direct_session.add(test_entity)

        # 4. rbpc_creators, rbpc_experiences, rbpc_inquiries
        test_creator = RbpcCreator(
            slug=f"artisan-drill-{test_token}",
            public_name=f"Rehearsal Artisan {test_token}",
            craft_tradition="Đúc đồng Phường Đúc",
            approved_bio_vi="Nghệ nhân gia truyền phục vụ diễn tập khôi phục dữ liệu.",
            consent_status=RbpcConsentStatus.consented.value,
            is_verified=True,
        )
        direct_session.add(test_creator)
        direct_session.flush()

        test_exp = RbpcExperience(
            slug=f"exp-drill-{test_token}",
            title_vi=f"Trải nghiệm diễn tập {test_token}",
            title_en=f"Drill Experience {test_token}",
            description_vi="Mô tả trải nghiệm diễn tập khôi phục hệ thống.",
            creator_id=test_creator.id,
            provider_name="Trung tâm Di sản Cố đô",
            provider_id=test_user.id,
            publication_state="published",
            availability_mode="inquiry_only",
        )
        direct_session.add(test_exp)
        direct_session.flush()

        test_inquiry = RbpcInquiry(
            public_ref=f"INQ-DRL-{test_token[:4].upper()}",
            experience_id=test_exp.id,
            provider_id=test_user.id,
            name="Học Viên Diễn Tập",
            contact_channel="email",
            contact_value=f"visitor_{test_token}@example.com",
            party_size=2,
            message="Yêu cầu tham quan thử nghiệm trong diễn tập RPO/RTO.",
            consent_version="rbpc-inquiry-v1",
            privacy_accepted=True,
            state=RbpcInquiryStatus.new.value,
            idempotency_key=str(uuid.uuid4()),
            opaque_token=f"tok_drill_{test_token}",
        )
        direct_session.add(test_inquiry)

        direct_session.commit()

    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    # Take backup with known seed
    backup_res = create_backup(
        source_db_url=db_url,
        output_dir=backup_test_dir,
        filename_prefix="t084_rehearsal_exact",
    )

    # Execute restore rehearsal into disposable database
    report = restore_rehearsal(
        archive_path=backup_res["archive_path"],
        target_dbname=DEFAULT_DRILL_DB,
        source_db_url=db_url,
    )

    # Assert rehearsal succeeded and verified exact counts
    assert report["status"] == "SUCCESS"
    assert report["verification_passed"] is True
    assert report["target_database"] == DEFAULT_DRILL_DB
    assert report["table_verification"]["all_tables_matched"] is True
    assert len(report["table_verification"]["mismatched_tables"]) == 0

    # Specifically verify critical tables (users, heritage_places, historical_entities, rbpc_inquiries)
    counts = report["table_verification"]["counts"]
    for table_name in CRITICAL_VERIFICATION_TABLES:
        assert table_name in counts, f"Critical table '{table_name}' missing from verification"
        tbl_info = counts[table_name]
        assert tbl_info["matches"] is True, f"Table '{table_name}' count mismatch: {tbl_info}"
        assert tbl_info["source_count"] == tbl_info["restored_count"]
        assert tbl_info["restored_count"] >= 1, f"Expected table '{table_name}' to have at least 1 record"

    # Connect to restored disposable database directly and verify seeded user is queryable
    clean_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")
    from urllib.parse import urlparse
    p = urlparse(clean_url)
    drill_url = f"postgresql://{p.username}:{p.password or ''}@{p.hostname}:{p.port or 5432}/{DEFAULT_DRILL_DB}"
    with psycopg.connect(drill_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email, username FROM users WHERE email = %s;", (user_email,))
            row = cur.fetchone()
            assert row is not None, "Seeded user was not found in restored database"
            assert row[0] == user_email
            assert row[1] == user_username

    # Clean up test entities from live DB
    with SessionLocal() as cleanup_session:
        cleanup_session.execute(text("DELETE FROM rbpc_inquiries WHERE public_ref LIKE :prefix"), {"prefix": "INQ-DRL-%"})
        cleanup_session.execute(text("DELETE FROM rbpc_experiences WHERE slug LIKE :prefix"), {"prefix": "exp-drill-%"})
        cleanup_session.execute(text("DELETE FROM rbpc_creators WHERE slug LIKE :prefix"), {"prefix": "artisan-drill-%"})
        cleanup_session.execute(text("DELETE FROM historical_entities WHERE slug LIKE :prefix"), {"prefix": "rehearsal-entity-%"})
        cleanup_session.execute(text("DELETE FROM heritage_places WHERE slug LIKE :prefix"), {"prefix": "rehearsal-site-%"})
        cleanup_session.execute(text("DELETE FROM users WHERE email LIKE :prefix"), {"prefix": "rehearsal_student_%"})
        cleanup_session.commit()


def test_rehearsal_rpo_and_rto_metrics_and_structured_report(
    backup_test_dir: Path,
) -> None:
    """Requirement 2: Generates structured RPO / RTO verification report with metrics."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    backup_res = create_backup(
        source_db_url=db_url,
        output_dir=backup_test_dir,
        filename_prefix="t084_metrics",
    )

    report_path = backup_test_dir / "custom_rehearsal_report.json"
    report = restore_rehearsal(
        archive_path=backup_res["archive_path"],
        target_dbname=DEFAULT_DRILL_DB,
        source_db_url=db_url,
        report_output_path=report_path,
        rto_target_seconds=300.0,
        rpo_target_seconds=3600.0,
    )

    assert report_path.is_file(), "Custom report file was not written"
    assert report["report_file"] == str(report_path.resolve())

    # Check RTO metrics
    metrics = report["metrics"]
    assert "rto_seconds" in metrics
    assert isinstance(metrics["rto_seconds"], float)
    assert metrics["rto_seconds"] > 0.0
    assert metrics["rto_seconds"] < 300.0, f"RTO {metrics['rto_seconds']}s exceeded 300s SLA"
    assert metrics["rto_target_met"] is True

    # Check RPO metrics
    assert "rpo_delta_seconds" in metrics
    assert isinstance(metrics["rpo_delta_seconds"], float)
    assert metrics["rpo_delta_seconds"] >= 0.0
    assert metrics["rpo_target_met"] is True

    # Check integrity verification details in report
    integrity = report["integrity_verification"]
    assert integrity["checksum_valid"] is True
    assert integrity["expected_sha256"] == backup_res["archive_sha256"]
    assert integrity["computed_sha256"] == backup_res["archive_sha256"]


def test_negative_abuse_damaged_or_tampered_dump_fails_integrity(
    backup_test_dir: Path,
) -> None:
    """Requirement 3: Restore from damaged dump fails integrity check and does NOT overwrite live DB."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    # Find existing unencrypted backup or create one
    existing = list(backup_test_dir.glob("*.sql.gz"))
    if existing:
        original_path = existing[0]
        meta_file = original_path.parent / f"{original_path.name}.meta.json"
        with open(meta_file, "r", encoding="utf-8") as f:
            original_sha = json.load(f)["archive_sha256"]
    else:
        backup_res = create_backup(
            source_db_url=db_url,
            output_dir=backup_test_dir,
            filename_prefix="t084_tamper_test",
        )
        original_path = Path(backup_res["archive_path"])
        original_sha = backup_res["archive_sha256"]

    # Create a corrupted copy with altered payload bytes (bit rot / corruption)
    corrupt_path = backup_test_dir / "t084_corrupted_payload.sql.gz"
    with open(original_path, "rb") as f_in:
        content = bytearray(f_in.read())

    # Tamper with middle bytes
    assert len(content) > 100
    content[50:80] = b"\x00" * 30

    with open(corrupt_path, "wb") as f_out:
        f_out.write(content)

    # Provide original expected checksum metadata to test checksum mismatch detection
    fake_meta = backup_test_dir / f"{corrupt_path.name}.meta.json"
    with open(fake_meta, "w", encoding="utf-8") as f_meta:
        json.dump({
            "backup_id": "corrupt_drill_test",
            "archive_sha256": original_sha,  # Mismatched!
            "table_counts": {"users": 10},
        }, f_meta)

    # Attempting to restore tampered archive MUST fail with IntegrityError
    with pytest.raises(IntegrityError) as exc_info:
        restore_rehearsal(
            archive_path=corrupt_path,
            target_dbname=DEFAULT_DRILL_DB,
            source_db_url=db_url,
            meta_path=fake_meta,
        )

    assert "Checksum mismatch" in str(exc_info.value) or "Integrity check failed" in str(exc_info.value)


def test_negative_abuse_empty_dump_fails_integrity(
    backup_test_dir: Path,
) -> None:
    """Requirement 3: Restore from 0-byte/empty dump fails integrity check."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    empty_path = backup_test_dir / "empty_corrupt_backup.sql.gz"
    empty_path.write_bytes(b"")  # 0 bytes

    with pytest.raises(IntegrityError) as exc_info:
        restore_rehearsal(
            archive_path=empty_path,
            target_dbname=DEFAULT_DRILL_DB,
            source_db_url=db_url,
        )

    assert "empty (0 bytes)" in str(exc_info.value)


def test_negative_abuse_live_database_protection(
    backup_test_dir: Path,
) -> None:
    """Requirement 3: Rehearsal script refuses to overwrite live database."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    existing = list(backup_test_dir.glob("*.sql.gz"))
    if existing:
        archive_path = existing[0]
    else:
        backup_res = create_backup(
            source_db_url=db_url,
            output_dir=backup_test_dir,
            filename_prefix="t084_live_guard",
        )
        archive_path = Path(backup_res["archive_path"])

    # Attempt to target the live database
    from scripts.backup.backup_engine import DatabaseConfig
    source_cfg = DatabaseConfig.from_url(db_url)
    with pytest.raises(LiveDatabaseProtectionError) as exc_info:
        restore_rehearsal(
            archive_path=archive_path,
            target_dbname=source_cfg.dbname,  # Same as source DB!
            source_db_url=db_url,
        )

    assert "REFUSING TO RESTORE" in str(exc_info.value)
    assert "matches the live database" in str(exc_info.value)


def test_cli_shell_scripts_end_to_end(
    backup_test_dir: Path,
) -> None:
    """Requirement 1 & 2: Shell scripts backup-database.sh and restore-rehearsal.sh run end-to-end."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")
    backup_script = REPO_ROOT / "scripts" / "backup" / "backup-database.sh"
    restore_script = REPO_ROOT / "scripts" / "backup" / "restore-rehearsal.sh"

    assert backup_script.is_file() and os.access(backup_script, os.X_OK)
    assert restore_script.is_file() and os.access(restore_script, os.X_OK)

    # 1. Run backup shell script
    cli_out_dir = backup_test_dir / "cli_run"
    proc_backup = subprocess.run(
        [
            str(backup_script),
            "--db-url", db_url,
            "--output-dir", str(cli_out_dir),
            "--prefix", "cli_test_backup",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc_backup.returncode == 0, f"backup-database.sh failed: {proc_backup.stderr}"
    assert "[OK] Backup created successfully" in proc_backup.stdout
    assert "[OK] SHA-256 Checksum" in proc_backup.stdout

    # Find created archive
    archives = list(cli_out_dir.glob("cli_test_backup_*.sql.gz"))
    assert len(archives) == 1, f"Expected 1 archive in {cli_out_dir}, found {archives}"
    created_archive = archives[0]

    # 2. Run restore rehearsal shell script
    cli_report = cli_out_dir / "cli_rehearsal_report.json"
    proc_restore = subprocess.run(
        [
            str(restore_script),
            "--archive", str(created_archive),
            "--target-db", DEFAULT_DRILL_DB,
            "--source-db-url", db_url,
            "--report", str(cli_report),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc_restore.returncode == 0, f"restore-rehearsal.sh failed: {proc_restore.stderr}"
    assert "[SUCCESS] Rehearsal Drill ID" in proc_restore.stdout
    assert "[SUCCESS] Measured RTO" in proc_restore.stdout
    assert "[SUCCESS] Table Verification" in proc_restore.stdout
    assert cli_report.is_file()
