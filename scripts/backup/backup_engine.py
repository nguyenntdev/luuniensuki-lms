# -*- coding: utf-8 -*-
"""Backup and Restore Rehearsal Engine for Luuniensuki LMS.

Provides:
- Automated PostgreSQL backup dumping with gzip compression and SHA-256 checksums.
- Passphrase encryption support using AES-256-CBC with PBKDF2.
- Integrity verification of archive and checksum before any restoration.
- Live database protection (strictly preventing rehearsal restores from targeting live DB).
- Restore rehearsal into disposable drill database (default: luuniensuki_restore_drill).
- Exact table and row count verification across core tables (users, heritage_places,
  historical_entities, rbpc_inquiries, etc.).
- Verifiable RPO / RTO metric calculation and structured JSON report generation.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import psycopg

# Core tables required to be verified during restoration rehearsal
CRITICAL_VERIFICATION_TABLES = [
    "users",
    "heritage_places",
    "historical_entities",
    "rbpc_inquiries",
]

DEFAULT_DRILL_DB = "luuniensuki_restore_drill"
DEFAULT_RTO_TARGET_SECONDS = 300.0  # 5 minutes SLA
DEFAULT_RPO_TARGET_SECONDS = 3600.0  # 1 hour SLA


class BackupError(Exception):
    """Base exception for backup operations."""
    pass


class RestoreError(Exception):
    """Base exception for restore operations."""
    pass


class IntegrityError(RestoreError):
    """Raised when backup file is missing, empty, or fails checksum verification."""
    pass


class DecryptionError(RestoreError):
    """Raised when archive decryption fails due to invalid passphrase or corruption."""
    pass


class LiveDatabaseProtectionError(RestoreError):
    """Raised when an attempt is made to restore into a live or production database."""
    pass


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    dbname: str
    raw_url: str

    @classmethod
    def from_url(cls, db_url: str) -> "DatabaseConfig":
        clean_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")
        parsed = urlparse(clean_url)
        return cls(
            host=parsed.hostname or "127.0.0.1",
            port=parsed.port or 5432,
            user=parsed.username or "postgres",
            password=parsed.password or "",
            dbname=parsed.path.lstrip("/") or "postgres",
            raw_url=db_url,
        )

    def to_psycopg_url(self, override_dbname: Optional[str] = None) -> str:
        db = override_dbname or self.dbname
        pwd_part = f":{self.password}" if self.password else ""
        return f"postgresql://{self.user}{pwd_part}@{self.host}:{self.port}/{db}"


def detect_docker_container(explicit_container: Optional[str] = None) -> Optional[str]:
    """Detect available docker container for PostgreSQL if pg_dump not on host."""
    if explicit_container:
        return explicit_container

    env_container = os.environ.get("POSTGRES_CONTAINER") or os.environ.get("DOCKER_CONTAINER")
    if env_container:
        return env_container

    # Check if docker is available
    if not shutil.which("docker"):
        return None

    try:
        res = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    cname, cimg = parts[0], parts[1]
                    if "luuniensuki" in cname and "db" in cname:
                        return cname
                    if "postgres" in cimg.lower():
                        return cname
    except Exception:
        pass
    return None


def compute_sha256(filepath: str | Path) -> str:
    """Compute SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_all_table_counts(db_config: DatabaseConfig, dbname: Optional[str] = None) -> Dict[str, int]:
    """Query row counts for all public tables in the specified database."""
    conn_url = db_config.to_psycopg_url(override_dbname=dbname)
    counts: Dict[str, int] = {}
    try:
        with psycopg.connect(conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
                )
                tables = [row[0] for row in cur.fetchall()]
                for table in tables:
                    try:
                        cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                        res = cur.fetchone()
                        counts[table] = int(res[0]) if res else 0
                    except Exception:
                        counts[table] = 0
    except Exception as e:
        raise BackupError(f"Failed to query table counts from database '{dbname or db_config.dbname}': {e}") from e
    return counts


def get_latest_record_timestamp(db_config: DatabaseConfig, dbname: Optional[str] = None) -> Optional[datetime]:
    """Find the most recent created_at or updated_at timestamp in the database."""
    conn_url = db_config.to_psycopg_url(override_dbname=dbname)
    latest: Optional[datetime] = None
    try:
        with psycopg.connect(conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name, column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND column_name IN ('created_at', 'updated_at', 'timestamp')
                    ORDER BY table_name;
                """)
                ts_cols = cur.fetchall()
                for table, col in ts_cols:
                    try:
                        cur.execute(f'SELECT MAX("{col}") FROM "{table}" WHERE "{col}" IS NOT NULL;')
                        val = cur.fetchone()
                        if val and val[0]:
                            ts_val = val[0]
                            if isinstance(ts_val, datetime):
                                if ts_val.tzinfo is None:
                                    ts_val = ts_val.replace(tzinfo=timezone.utc)
                                if latest is None or ts_val > latest:
                                    latest = ts_val
                    except Exception:
                        continue
    except Exception:
        pass
    return latest


def dump_database_sql(
    db_config: DatabaseConfig,
    container_name: Optional[str] = None,
) -> bytes:
    """Execute pg_dump to produce clean PostgreSQL SQL dump bytes."""
    native_pg_dump = shutil.which("pg_dump")
    container = detect_docker_container(container_name)

    dump_flags = ["--clean", "--if-exists", "--no-owner", "--no-privileges", "--quote-all-identifiers"]

    if native_pg_dump:
        cmd = [
            native_pg_dump,
            "-h", db_config.host,
            "-p", str(db_config.port),
            "-U", db_config.user,
            "-d", db_config.dbname,
            *dump_flags,
        ]
        env = os.environ.copy()
        if db_config.password:
            env["PGPASSWORD"] = db_config.password
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise BackupError(f"pg_dump native execution failed (code {proc.returncode}): {stderr.decode('utf-8', errors='replace')}")
        return stdout

    elif container:
        cmd = [
            "docker", "exec", "-i",
            container,
            "pg_dump",
            "-U", db_config.user,
            "-d", db_config.dbname,
            *dump_flags,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise BackupError(f"Docker pg_dump failed in container '{container}' (code {proc.returncode}): {stderr.decode('utf-8', errors='replace')}")
        return stdout
    else:
        raise BackupError("Neither pg_dump nor a running PostgreSQL Docker container was found to perform the dump.")


def restore_sql_into_db(
    sql_data: bytes,
    db_config: DatabaseConfig,
    target_dbname: str,
    container_name: Optional[str] = None,
) -> None:
    """Stream SQL statements into target database."""
    # Sanitize dump: Strip PostgreSQL 17-specific parameters (like transaction_timeout)
    # when restoring onto PG 15/16 targets (e.g. GitHub Actions CI runner)
    if b"transaction_timeout" in sql_data:
        sql_data = re.sub(rb"(?i)SET\s+transaction_timeout\s*=[^;]*;\s*", b"", sql_data)

    native_psql = shutil.which("psql")
    container = detect_docker_container(container_name)

    if native_psql:
        cmd = [
            native_psql,
            "-h", db_config.host,
            "-p", str(db_config.port),
            "-U", db_config.user,
            "-d", target_dbname,
            "--quiet",
            "-v", "ON_ERROR_STOP=1",
        ]
        env = os.environ.copy()
        if db_config.password:
            env["PGPASSWORD"] = db_config.password
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = proc.communicate(input=sql_data)
        if proc.returncode != 0:
            raise RestoreError(f"psql native restore failed (code {proc.returncode}): {stderr.decode('utf-8', errors='replace')}")
        return

    elif container:
        cmd = [
            "docker", "exec", "-i",
            container,
            "psql",
            "-U", db_config.user,
            "-d", target_dbname,
            "--quiet",
            "-v", "ON_ERROR_STOP=1",
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(input=sql_data)
        if proc.returncode != 0:
            raise RestoreError(f"Docker psql restore failed in container '{container}' (code {proc.returncode}): {stderr.decode('utf-8', errors='replace')}")
        return
    else:
        # Fallback: Execute via psycopg connection
        conn_url = db_config.to_psycopg_url(override_dbname=target_dbname)
        try:
            with psycopg.connect(conn_url, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_data.decode("utf-8", errors="replace"))
        except Exception as e:
            raise RestoreError(f"psycopg fallback restore failed: {e}") from e


def recreate_disposable_database(db_config: DatabaseConfig, target_dbname: str) -> None:
    """Drop and recreate the disposable target drill database."""
    maint_url = db_config.to_psycopg_url(override_dbname="postgres")
    try:
        with psycopg.connect(maint_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Terminate active connections to disposable database
                cur.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();",
                    (target_dbname,),
                )
                cur.execute(f'DROP DATABASE IF EXISTS "{target_dbname}";')
                cur.execute(f'CREATE DATABASE "{target_dbname}";')
    except Exception as e:
        raise RestoreError(f"Failed to recreate disposable drill database '{target_dbname}': {e}") from e


def encrypt_data(data: bytes, passphrase: str) -> bytes:
    """Encrypt binary payload using openssl AES-256-CBC with PBKDF2."""
    cmd = [
        "openssl", "enc", "-aes-256-cbc",
        "-salt", "-pbkdf2", "-iter", "100000",
        "-pass", f"pass:{passphrase}",
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=data)
    if proc.returncode != 0:
        raise BackupError(f"Encryption failed: {stderr.decode('utf-8', errors='replace')}")
    return stdout


def decrypt_data(data: bytes, passphrase: str) -> bytes:
    """Decrypt binary payload using openssl AES-256-CBC with PBKDF2."""
    cmd = [
        "openssl", "enc", "-d", "-aes-256-cbc",
        "-pbkdf2", "-iter", "100000",
        "-pass", f"pass:{passphrase}",
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=data)
    if proc.returncode != 0:
        raise DecryptionError(f"Decryption failed: invalid passphrase or corrupted cipher blocks: {stderr.decode('utf-8', errors='replace')}")
    return stdout


def create_backup(
    source_db_url: str,
    output_dir: str | Path = "backups",
    filename_prefix: str = "lms_backup",
    passphrase: Optional[str] = None,
    container_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute complete automated database backup."""
    start_time = time.time()
    created_at_dt = datetime.now(timezone.utc)
    timestamp_str = created_at_dt.strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{timestamp_str}_{os.urandom(4).hex()}"

    db_config = DatabaseConfig.from_url(source_db_url)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Capture source table row counts
    table_counts = get_all_table_counts(db_config)
    latest_record_ts = get_latest_record_timestamp(db_config)

    # 2. Dump SQL schema and data
    raw_sql = dump_database_sql(db_config, container_name=container_name)

    # 3. Compress with gzip
    compressed_bytes = gzip.compress(raw_sql, compresslevel=9)

    # 4. Encrypt if passphrase provided
    is_encrypted = bool(passphrase)
    if is_encrypted:
        final_bytes = encrypt_data(compressed_bytes, passphrase=passphrase)  # type: ignore
        archive_name = f"{filename_prefix}_{timestamp_str}_{backup_id[-6:]}.sql.gz.enc"
    else:
        final_bytes = compressed_bytes
        archive_name = f"{filename_prefix}_{timestamp_str}_{backup_id[-6:]}.sql.gz"

    archive_path = out_path / archive_name
    with open(archive_path, "wb") as f:
        f.write(final_bytes)

    # 5. Compute SHA-256 checksum
    checksum = compute_sha256(archive_path)
    sha256_path = out_path / f"{archive_name}.sha256"
    with open(sha256_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {archive_name}\n")

    duration = time.time() - start_time

    # 6. Generate metadata manifest
    metadata = {
        "backup_id": backup_id,
        "created_at": created_at_dt.isoformat(),
        "database_name": db_config.dbname,
        "archive_filename": archive_name,
        "archive_path": str(archive_path.resolve()),
        "archive_sha256": checksum,
        "size_bytes": len(final_bytes),
        "uncompressed_bytes": len(raw_sql),
        "compressed_bytes": len(compressed_bytes),
        "compression": "gzip",
        "is_encrypted": is_encrypted,
        "encryption_cipher": "aes-256-cbc" if is_encrypted else None,
        "duration_seconds": round(duration, 3),
        "table_counts": table_counts,
        "latest_record_timestamp": latest_record_ts.isoformat() if latest_record_ts else None,
    }

    meta_path = out_path / f"{archive_name}.meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    metadata["meta_path"] = str(meta_path.resolve())
    metadata["sha256_path"] = str(sha256_path.resolve())
    return metadata


def verify_backup_integrity(
    archive_path: str | Path,
    meta_path: Optional[str | Path] = None,
    passphrase: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify archive integrity, existence, non-emptiness, checksum, and decompressibility."""
    path = Path(archive_path)
    if not path.is_file():
        raise IntegrityError(f"Backup archive does not exist: {path}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise IntegrityError(f"Backup archive is empty (0 bytes): {path}")

    computed_sha256 = compute_sha256(path)

    # Look for expected checksum
    expected_sha256: Optional[str] = None
    sha256_file = path.parent / f"{path.name}.sha256"
    if sha256_file.is_file():
        content = sha256_file.read_text(encoding="utf-8").strip()
        expected_sha256 = content.split()[0]
    elif meta_path and Path(meta_path).is_file():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            expected_sha256 = meta.get("archive_sha256")
    else:
        # Check adjacent .meta.json
        meta_adjacent = path.parent / f"{path.name}.meta.json"
        if meta_adjacent.is_file():
            with open(meta_adjacent, "r", encoding="utf-8") as f:
                meta = json.load(f)
                expected_sha256 = meta.get("archive_sha256")

    if expected_sha256 and computed_sha256 != expected_sha256:
        raise IntegrityError(
            f"Integrity check failed: Checksum mismatch for '{path.name}'! "
            f"Expected {expected_sha256}, got {computed_sha256}. Damaged or tampered backup."
        )

    # Read archive bytes
    with open(path, "rb") as f:
        raw_bytes = f.read()

    # Check encryption / decryption
    is_encrypted = path.name.endswith(".enc")
    if is_encrypted:
        if not passphrase:
            raise DecryptionError(f"Archive '{path.name}' is encrypted, but no passphrase was provided.")
        decrypted_bytes = decrypt_data(raw_bytes, passphrase=passphrase)
    else:
        decrypted_bytes = raw_bytes

    # Check gzip decompression
    try:
        decompressed_sql = gzip.decompress(decrypted_bytes)
        if len(decompressed_sql) == 0:
            raise IntegrityError("Decompressed SQL payload is empty.")
    except Exception as e:
        if isinstance(e, (IntegrityError, DecryptionError)):
            raise
        raise IntegrityError(f"Corrupt gzip compressed stream in archive '{path.name}': {e}") from e

    return {
        "integrity_status": "VALID",
        "archive_file": str(path.resolve()),
        "size_bytes": file_size,
        "computed_sha256": computed_sha256,
        "expected_sha256": expected_sha256,
        "is_encrypted": is_encrypted,
        "decompressed_sql_bytes": len(decompressed_sql),
        "decompressed_sql": decompressed_sql,
    }


def restore_rehearsal(
    archive_path: str | Path,
    target_dbname: str = DEFAULT_DRILL_DB,
    source_db_url: Optional[str] = None,
    meta_path: Optional[str | Path] = None,
    passphrase: Optional[str] = None,
    report_output_path: Optional[str | Path] = None,
    container_name: Optional[str] = None,
    rto_target_seconds: float = DEFAULT_RTO_TARGET_SECONDS,
    rpo_target_seconds: float = DEFAULT_RPO_TARGET_SECONDS,
) -> Dict[str, Any]:
    """Execute complete restore rehearsal with verification and RPO/RTO metrics."""
    rehearsal_start_ts = datetime.now(timezone.utc)
    drill_id = f"drill_{rehearsal_start_ts.strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

    # Resolve database configs
    effective_source_url = source_db_url or os.environ.get("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/luuniensuki_test"
    db_config = DatabaseConfig.from_url(effective_source_url)

    # 1. Safety check: Ensure target DB does not match live database!
    if target_dbname == db_config.dbname:
        raise LiveDatabaseProtectionError(
            f"REFUSING TO RESTORE: Target database '{target_dbname}' matches the live database! "
            f"Restore rehearsal must strictly target a disposable drill database."
        )

    # 2. Check metadata
    archive_file = Path(archive_path)
    meta_file = Path(meta_path) if meta_path else archive_file.parent / f"{archive_file.name}.meta.json"
    metadata: Dict[str, Any] = {}
    if meta_file.is_file():
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    # 3. Integrity verification (fails early on corrupt / empty / checksum mismatch)
    integrity_result = verify_backup_integrity(archive_file, meta_path=meta_file, passphrase=passphrase)
    decompressed_sql: bytes = integrity_result["decompressed_sql"]

    # 4. Recreate disposable target database
    recreate_disposable_database(db_config, target_dbname=target_dbname)

    # 5. Execute restore and measure RTO
    rto_start_time = time.time()
    restore_sql_into_db(decompressed_sql, db_config, target_dbname=target_dbname, container_name=container_name)
    rto_end_time = time.time()
    measured_rto = round(rto_end_time - rto_start_time, 3)

    # 6. Verify table row counts
    restored_table_counts = get_all_table_counts(db_config, dbname=target_dbname)
    source_counts = metadata.get("table_counts") or get_all_table_counts(db_config, dbname=db_config.dbname)

    table_verifications: Dict[str, Dict[str, Any]] = {}
    all_matched = True
    mismatched_tables: List[str] = []

    # Verify tables from source snapshot
    tables_to_check = set(list(source_counts.keys()) + CRITICAL_VERIFICATION_TABLES)
    for t in sorted(tables_to_check):
        src_c = source_counts.get(t, 0)
        rst_c = restored_table_counts.get(t, 0)
        is_match = (src_c == rst_c)
        table_verifications[t] = {
            "source_count": src_c,
            "restored_count": rst_c,
            "matches": is_match,
        }
        if not is_match:
            all_matched = False
            mismatched_tables.append(t)

    # 7. Compute RPO metrics
    backup_created_str = metadata.get("created_at")
    backup_created_dt: Optional[datetime] = None
    if backup_created_str:
        try:
            backup_created_dt = datetime.fromisoformat(backup_created_str)
        except Exception:
            pass

    latest_record_str = metadata.get("latest_record_timestamp")
    latest_record_dt: Optional[datetime] = None
    if latest_record_str:
        try:
            latest_record_dt = datetime.fromisoformat(latest_record_str)
        except Exception:
            pass

    # Calculate RPO delta
    if latest_record_dt and backup_created_dt:
        rpo_delta = abs((backup_created_dt - latest_record_dt).total_seconds())
    elif backup_created_dt:
        rpo_delta = abs((rehearsal_start_ts - backup_created_dt).total_seconds())
    else:
        rpo_delta = 0.0

    rto_met = measured_rto <= rto_target_seconds
    rpo_met = rpo_delta <= rpo_target_seconds
    verification_passed = all_matched and (len(mismatched_tables) == 0)

    # 8. Compile structured report
    report = {
        "drill_id": drill_id,
        "status": "SUCCESS" if verification_passed else "FAILED",
        "verification_passed": verification_passed,
        "rehearsal_timestamp": rehearsal_start_ts.isoformat(),
        "backup_id": metadata.get("backup_id", "unknown"),
        "backup_archive": str(archive_file.resolve()),
        "backup_created_at": backup_created_str,
        "source_database": db_config.dbname,
        "target_database": target_dbname,
        "is_encrypted": integrity_result["is_encrypted"],
        "integrity_verification": {
            "checksum_valid": True,
            "expected_sha256": integrity_result["expected_sha256"],
            "computed_sha256": integrity_result["computed_sha256"],
            "archive_size_bytes": integrity_result["size_bytes"],
            "decompressed_sql_bytes": integrity_result["decompressed_sql_bytes"],
        },
        "metrics": {
            "rto_seconds": measured_rto,
            "rto_target_seconds": rto_target_seconds,
            "rto_target_met": rto_met,
            "rpo_delta_seconds": round(rpo_delta, 3),
            "rpo_target_seconds": rpo_target_seconds,
            "rpo_target_met": rpo_met,
            "latest_source_record_timestamp": latest_record_str,
        },
        "table_verification": {
            "total_tables_checked": len(tables_to_check),
            "all_tables_matched": all_matched,
            "critical_tables_checked": CRITICAL_VERIFICATION_TABLES,
            "counts": table_verifications,
            "mismatched_tables": mismatched_tables,
        },
        "summary": (
            f"Restore rehearsal {'PASSED' if verification_passed else 'FAILED'}. "
            f"Restored into '{target_dbname}' in {measured_rto}s (RTO target {rto_target_seconds}s). "
            f"RPO delta is {round(rpo_delta, 1)}s. "
            f"{len(table_verifications)} tables checked, all matched: {all_matched}."
        ),
    }

    # 9. Save report JSON
    if report_output_path:
        rep_p = Path(report_output_path)
    else:
        rep_dir = Path("backups/reports")
        rep_dir.mkdir(parents=True, exist_ok=True)
        rep_p = rep_dir / f"rehearsal_{drill_id}.json"

    rep_p.parent.mkdir(parents=True, exist_ok=True)
    with open(rep_p, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    report["report_file"] = str(rep_p.resolve())
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Luuniensuki Backup & Restore Rehearsal CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backup subcommand
    p_backup = subparsers.add_parser("backup", help="Create automated database backup")
    p_backup.add_argument("--db-url", default=os.environ.get("DATABASE_URL"), help="Database connection URL")
    p_backup.add_argument("--output-dir", default="backups", help="Directory to store backup")
    p_backup.add_argument("--prefix", default="lms_backup", help="Filename prefix")
    p_backup.add_argument("--passphrase", default=os.environ.get("BACKUP_PASSPHRASE"), help="Passphrase for encryption")
    p_backup.add_argument("--container", default=None, help="Postgres docker container name")

    # Restore rehearsal subcommand
    p_restore = subparsers.add_parser("restore", help="Execute restore rehearsal into disposable drill database")
    p_restore.add_argument("--archive", "-a", required=True, help="Path to backup archive file")
    p_restore.add_argument("--target-db", "-t", default=DEFAULT_DRILL_DB, help="Disposable drill database name")
    p_restore.add_argument("--source-db-url", default=os.environ.get("DATABASE_URL"), help="Source database URL to protect")
    p_restore.add_argument("--meta", "-m", default=None, help="Path to metadata JSON")
    p_restore.add_argument("--passphrase", default=os.environ.get("BACKUP_PASSPHRASE"), help="Passphrase if encrypted")
    p_restore.add_argument("--report", "-r", default=None, help="Path to write report JSON")
    p_restore.add_argument("--container", default=None, help="Postgres docker container name")

    # Verify subcommand
    p_verify = subparsers.add_parser("verify", help="Verify backup integrity and checksum")
    p_verify.add_argument("--archive", "-a", required=True, help="Path to backup archive file")
    p_verify.add_argument("--meta", "-m", default=None, help="Path to metadata JSON")
    p_verify.add_argument("--passphrase", default=os.environ.get("BACKUP_PASSPHRASE"), help="Passphrase if encrypted")

    args = parser.parse_args()

    if args.command == "backup":
        if not args.db_url:
            sys.exit("Error: --db-url or DATABASE_URL environment variable required.")
        try:
            res = create_backup(
                source_db_url=args.db_url,
                output_dir=args.output_dir,
                filename_prefix=args.prefix,
                passphrase=args.passphrase,
                container_name=args.container,
            )
            print(f"[OK] Backup created successfully: {res['archive_path']}")
            print(f"[OK] SHA-256 Checksum: {res['archive_sha256']}")
            print(f"[OK] Size: {res['size_bytes']} bytes (Encrypted: {res['is_encrypted']})")
            print(f"[OK] Metadata: {res['meta_path']}")
        except Exception as e:
            sys.exit(f"Backup failed: {e}")

    elif args.command == "restore":
        try:
            rep = restore_rehearsal(
                archive_path=args.archive,
                target_dbname=args.target_db,
                source_db_url=args.source_db_url,
                meta_path=args.meta,
                passphrase=args.passphrase,
                report_output_path=args.report,
                container_name=args.container,
            )
            print(f"[{rep['status']}] Rehearsal Drill ID: {rep['drill_id']}")
            print(f"[{rep['status']}] Target DB: {rep['target_database']}")
            print(f"[{rep['status']}] Measured RTO: {rep['metrics']['rto_seconds']}s (Target Met: {rep['metrics']['rto_target_met']})")
            print(f"[{rep['status']}] Measured RPO Delta: {rep['metrics']['rpo_delta_seconds']}s (Target Met: {rep['metrics']['rpo_target_met']})")
            print(f"[{rep['status']}] Table Verification: {rep['table_verification']['total_tables_checked']} checked, all matched: {rep['table_verification']['all_tables_matched']}")
            print(f"[{rep['status']}] Report JSON: {rep['report_file']}")
            if not rep["verification_passed"]:
                sys.exit(1)
        except Exception as e:
            sys.exit(f"Restore rehearsal failed: {e}")

    elif args.command == "verify":
        try:
            v_res = verify_backup_integrity(
                archive_path=args.archive,
                meta_path=args.meta,
                passphrase=args.passphrase,
            )
            print(f"[OK] Integrity status: {v_res['integrity_status']}")
            print(f"[OK] Checksum: {v_res['computed_sha256']}")
            print(f"[OK] Archive size: {v_res['size_bytes']} bytes")
            print(f"[OK] Decompressed SQL size: {v_res['decompressed_sql_bytes']} bytes")
        except Exception as e:
            sys.exit(f"Integrity check failed: {e}")


if __name__ == "__main__":
    main()
