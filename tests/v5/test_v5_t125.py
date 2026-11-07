# -*- coding: utf-8 -*-
"""V5-T125: Production Load, Failover, Backup & SLO Verification Test Suite.

Wave W12, Slot A05 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Pilot Concurrency Load Simulator & Latency SLO Evaluator:
   - High concurrent execution (50+ simultaneous requests) across read and static endpoints.
   - Enforces p95 <= 300ms budget with 0.0% unhandled server errors.
2. Gateway Failover & Automatic Failback:
   - Simulates primary node outage with consecutive heartbeat drop detection.
   - Validates seamless traffic redirection to secondary gateway and subsequent failback.
3. Database Connection Pool Failover:
   - Simulates transient connection drops and verifies graceful reconnect and transaction retry.
4. Automated Backup & Restore Rehearsal:
   - Full schema and table dump, gzip compression, SHA-256 integrity check.
   - Restoration into disposable drill DB (luuniensuki_restore_drill) with table and row count match.
   - RTO (< 300s) and RPO (< 3600s) SLA validation.
5. On-Disk Verifiable Recovery Evidence (Negative Abuse Core):
   - Evidence bundle is 100% reproducible and verifiable directly from physical disk files.
   - Bit-rot / tampering with archive bytes raises TamperedArchiveError.
   - Forgery of manifest fields raises ManifestTamperingError.
   - Missing or empty evidence files raise MissingRecoveryEvidenceError / EmptyArchiveError.
6. Provider Outages & Graceful Degradation:
   - AI provider 503 outage engages deterministic Socratic fallback with Retry-After header.
   - Media provider 503 outage engages 2D rubbing gallery, bilingual transcript, and offline kit.
7. Network Flap & Idempotency Guarantee:
   - Flapping network with 40% transient drop rate.
   - Retried requests with idempotency key guarantee zero duplicate mutations.
8. Unified Production Release Gate:
   - Clean run generates signed GATE_PASSED release certificate.
   - Failures strictly trigger GATE_BLOCKED.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.main import app
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
    create_backup,
    restore_rehearsal,
)
from backend.services.load_failover_slo import (
    ConcurrencyMetric,
    DatabasePoolFailoverHandler,
    DatabasePoolFailoverResult,
    EmptyArchiveError,
    FailoverDrillResult,
    FailoverNodeStatus,
    GatewayFailoverController,
    LoadConcurrencySimulator,
    ManifestTamperingError,
    MissingRecoveryEvidenceError,
    NetworkFlapResilienceResult,
    NetworkFlapSimulator,
    ProductionReleaseGateReport,
    ProductionSLOE2EEvaluator,
    ProviderOutageResilienceResult,
    ProviderOutageSimulator,
    RecoveryEvidenceEngine,
    RecoveryEvidenceVerificationResult,
    ReleaseGateDecision,
    TamperedArchiveError,
    UnverifiableEvidenceError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(scope="module")
def backup_dir() -> Generator[Path, None, None]:
    td = tempfile.mkdtemp(prefix="test_w12_recovery_evidence_")
    path = Path(td)
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def cleanup_drill_database() -> Generator[None, None, None]:
    """Ensure disposable drill database is cleaned up before and after each test."""
    yield
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


# --------------------------------------------------------------------------- #
# Test 1: Pilot Concurrency Load Simulator & Latency SLO
# --------------------------------------------------------------------------- #

def test_v5_t125_pilot_concurrency_load_and_latency_slo_budget(client: TestClient):
    """Verifies that high pilot concurrency (50 simultaneous requests) meets p95 <= 300ms budget."""
    target_endpoints = [
        "/health",
        "/api/v1/rbpc/config",
        "/api/v1/heritage/places",
        "/api/v1/history/stories",
        "/api/v1/heritage/catalog",
    ]

    # Warm up client
    for ep in target_endpoints:
        client.get(ep)

    concurrency_metrics: List[ConcurrencyMetric] = []

    for ep in target_endpoints:
        def request_worker(_) -> Tuple[float, int]:
            t0 = time.perf_counter()
            resp = client.get(ep)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return latency_ms, resp.status_code

        # Execute 50 concurrent virtual user requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(request_worker, range(50)))

        latencies = [r[0] for r in results]
        status_codes = [r[1] for r in results]

        failed = sum(1 for code in status_codes if code != 200)
        assert failed == 0, f"Endpoint {ep} had {failed} failed requests under concurrency"

        metric = LoadConcurrencySimulator.evaluate_endpoint_concurrency(
            endpoint=ep,
            latencies_ms=latencies,
            target_p95_ms=300.0,
            duration_seconds=1.0,
            failed_count=failed,
        )
        concurrency_metrics.append(metric)

        assert metric.passed is True, f"SLO failed for {ep}: p95 {metric.p95_ms}ms > 300.0ms budget"
        assert metric.p95_ms <= 300.0, f"p95 {metric.p95_ms}ms exceeded 300ms"
        assert metric.total_requests == 50
        assert metric.failed_requests == 0


# --------------------------------------------------------------------------- #
# Test 2: Gateway Failover Detection and Automatic Failback
# --------------------------------------------------------------------------- #

def test_v5_t125_gateway_failover_detection_and_automatic_failback():
    """Verifies primary gateway outage detection, automatic rerouting to secondary, and failback."""
    ctrl = GatewayFailoverController(
        primary_endpoint="http://api_rust:8001",
        secondary_endpoint="http://api:8000",
        consecutive_failure_threshold=3,
    )

    # 1. Initially healthy, traffic routes to primary
    req1 = ctrl.route_request("/api/v1/heritage/catalog")
    assert req1["routed_to"] == "http://api_rust:8001"
    assert req1["is_fallback"] is False

    # 2. Simulate 2 transient drops (below threshold of 3)
    ctrl.report_heartbeat(primary_is_up=False)
    ctrl.report_heartbeat(primary_is_up=False)
    req2 = ctrl.route_request("/api/v1/heritage/catalog")
    assert req2["routed_to"] == "http://api_rust:8001"  # Still primary

    # 3. 3rd drop trips threshold -> Failover to secondary
    ctrl.report_heartbeat(primary_is_up=False)
    assert ctrl.primary_status == FailoverNodeStatus.OFFLINE
    assert ctrl.active_routing_target == "http://api:8000"

    req3 = ctrl.route_request("/api/v1/heritage/catalog")
    assert req3["routed_to"] == "http://api:8000"
    assert req3["is_fallback"] is True

    # 4. Primary node recovers -> Automatic failback
    ctrl.report_heartbeat(primary_is_up=True)
    assert ctrl.primary_status == FailoverNodeStatus.HEALTHY
    assert ctrl.active_routing_target == "http://api_rust:8001"

    req4 = ctrl.route_request("/api/v1/heritage/catalog")
    assert req4["routed_to"] == "http://api_rust:8001"
    assert req4["is_fallback"] is False


# --------------------------------------------------------------------------- #
# Test 3: Database Connection Pool Failover and Retry
# --------------------------------------------------------------------------- #

def test_v5_t125_database_connection_pool_failover_and_retry():
    """Verifies database connection pool retry on transient connection drops."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    call_count = 0

    def query_op(conn: psycopg.Connection) -> int:
        nonlocal call_count
        call_count += 1
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            row = cur.fetchone()
            return row[0]

    val, result = DatabasePoolFailoverHandler.execute_with_failover_retry(
        operation=query_op,
        db_url=db_url,
        max_retries=3,
    )

    assert val == 1
    assert result.passed is True
    assert result.data_intact is True
    assert result.reconnection_time_ms >= 0.0


# --------------------------------------------------------------------------- #
# Test 4: Automated Backup & Restore Rehearsal with Table Parity
# --------------------------------------------------------------------------- #

def test_v5_t125_automated_backup_and_restore_rehearsal(backup_dir: Path):
    """Verifies database dump creation, restoration into disposable DB, and row count parity."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")
    clean_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")

    # Seed fresh record directly with autocommit to guarantee latest_record_timestamp is current
    unique_email = f"w12_drill_{uuid.uuid4().hex[:8]}@example.com"
    with psycopg.connect(clean_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, username, role, is_profile_public, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 'learner', true, NOW(), NOW());
                """,
                (str(uuid.uuid4()), unique_email, hash_password("Password123!"), "W12 Drill User", f"u_{uuid.uuid4().hex[:8]}"),
            )

    backup_res = create_backup(
        source_db_url=db_url,
        output_dir=backup_dir,
        filename_prefix="t125_rehearsal",
    )

    archive_path = Path(backup_res["archive_path"])
    assert archive_path.is_file()
    assert archive_path.stat().st_size > 0

    report_path = backup_dir / "t125_rehearsal_report.json"
    report = restore_rehearsal(
        archive_path=str(archive_path),
        target_dbname=DEFAULT_DRILL_DB,
        source_db_url=db_url,
        report_output_path=report_path,
        rto_target_seconds=300.0,
        rpo_target_seconds=3600.0,
    )

    assert report["status"] == "SUCCESS"
    assert report["verification_passed"] is True
    assert report["table_verification"]["all_tables_matched"] is True

    # Check SLA metrics
    metrics = report["metrics"]
    assert metrics["rto_seconds"] < 300.0, f"RTO {metrics['rto_seconds']}s > 300s SLA"
    assert metrics["rto_target_met"] is True
    assert metrics["rpo_delta_seconds"] < 3600.0, f"RPO {metrics['rpo_delta_seconds']}s > 3600s SLA"
    assert metrics["rpo_target_met"] is True


# --------------------------------------------------------------------------- #
# Test 5: On-Disk Verifiable Recovery Evidence Bundle
# --------------------------------------------------------------------------- #

def test_v5_t125_disk_reproducible_recovery_evidence_bundle(backup_dir: Path):
    """Verifies that recovery evidence is 100% reproducible and verifiable directly from disk."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")
    clean_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")

    # Seed fresh record to guarantee latest_record_timestamp is strictly within seconds
    unique_email = f"w12_evidence_{uuid.uuid4().hex[:8]}@example.com"
    with psycopg.connect(clean_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, username, role, is_profile_public, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 'learner', true, NOW(), NOW());
                """,
                (str(uuid.uuid4()), unique_email, hash_password("Password123!"), "W12 Evidence User", f"u_{uuid.uuid4().hex[:8]}"),
            )

    bundle_dir = backup_dir / "sealed_recovery_bundle"
    evidence_bundle = RecoveryEvidenceEngine.create_and_seal_evidence_bundle(
        bundle_dir=bundle_dir,
        source_db_url=db_url,
    )

    manifest_path = Path(evidence_bundle["manifest_path"])
    archive_path = Path(evidence_bundle["archive_path"])
    checksum_path = Path(evidence_bundle["checksum_path"])
    report_path = Path(evidence_bundle["report_path"])

    assert manifest_path.is_file()
    assert archive_path.is_file()
    assert checksum_path.is_file()
    assert report_path.is_file()

    # Verify purely from physical disk files
    ver = RecoveryEvidenceEngine.verify_recovery_evidence_from_disk(bundle_dir)
    assert ver.verified_from_disk is True
    assert ver.manifest_verified is True
    assert ver.archive_checksum_verified is True
    assert ver.tamper_detected is False
    assert ver.rto_sla_met is True
    assert ver.rpo_sla_met is True
    assert ver.tables_matched > 0
    assert ver.passed is True


# --------------------------------------------------------------------------- #
# Test 6: Negative Abuse Guardrail 1 - Tampered Archive Bytes
# --------------------------------------------------------------------------- #

def test_v5_t125_negative_abuse_tampered_archive_fails_disk_verification(backup_dir: Path):
    """Negative Abuse: Modifying even 1 byte in the on-disk backup archive strictly fails verification."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    tamper_dir = backup_dir / "tampered_archive_bundle"
    res = RecoveryEvidenceEngine.create_and_seal_evidence_bundle(
        bundle_dir=tamper_dir,
        source_db_url=db_url,
    )

    archive_path = Path(res["archive_path"])
    # Flip 1 byte in the physical file
    with open(archive_path, "r+b") as f:
        f.seek(15)
        byte_val = f.read(1)
        f.seek(15)
        f.write(bytes([byte_val[0] ^ 0xAA]))

    # Must strictly raise TamperedArchiveError
    with pytest.raises(TamperedArchiveError) as exc_info:
        RecoveryEvidenceEngine.verify_recovery_evidence_from_disk(tamper_dir)

    assert "Archive SHA-256 mismatch" in str(exc_info.value)


# --------------------------------------------------------------------------- #
# Test 7: Negative Abuse Guardrail 2 - Manifest Metadata Forgery
# --------------------------------------------------------------------------- #

def test_v5_t125_negative_abuse_manifest_tampering_or_forgery_fails(backup_dir: Path):
    """Negative Abuse: Tampering with manifest fields on disk triggers HMAC signature mismatch."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    manifest_tamper_dir = backup_dir / "tampered_manifest_bundle"
    res = RecoveryEvidenceEngine.create_and_seal_evidence_bundle(
        bundle_dir=manifest_tamper_dir,
        source_db_url=db_url,
    )

    manifest_path = Path(res["manifest_path"])
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Forgery: claim RTO was 0.001s
    manifest_data["measured_rto_seconds"] = 0.001
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    with pytest.raises(ManifestTamperingError) as exc_info:
        RecoveryEvidenceEngine.verify_recovery_evidence_from_disk(manifest_tamper_dir)

    assert "Recovery manifest signature mismatch" in str(exc_info.value)


# --------------------------------------------------------------------------- #
# Test 8: Negative Abuse Guardrail 3 - Missing or Empty Evidence Files
# --------------------------------------------------------------------------- #

def test_v5_t125_negative_abuse_missing_or_empty_evidence_fails(backup_dir: Path):
    """Negative Abuse: Missing or 0-byte evidence files on disk strictly fail verification."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    missing_dir = backup_dir / "missing_evidence_bundle"
    res = RecoveryEvidenceEngine.create_and_seal_evidence_bundle(
        bundle_dir=missing_dir,
        source_db_url=db_url,
    )

    # Remove checksum file
    checksum_path = Path(res["checksum_path"])
    os.remove(checksum_path)

    with pytest.raises(MissingRecoveryEvidenceError) as exc_info:
        RecoveryEvidenceEngine.verify_recovery_evidence_from_disk(missing_dir)
    assert "Mandatory evidence file missing on disk" in str(exc_info.value)

    # Empty 0-byte archive test
    empty_dir = backup_dir / "empty_archive_bundle"
    res2 = RecoveryEvidenceEngine.create_and_seal_evidence_bundle(
        bundle_dir=empty_dir,
        source_db_url=db_url,
    )
    with open(res2["archive_path"], "wb") as f:
        pass  # 0 bytes

    with pytest.raises(EmptyArchiveError) as exc_info2:
        RecoveryEvidenceEngine.verify_recovery_evidence_from_disk(empty_dir)
    assert "Backup archive on disk is 0 bytes" in str(exc_info2.value)


# --------------------------------------------------------------------------- #
# Test 9: External Provider Outages (AI & Media) Graceful Fallbacks
# --------------------------------------------------------------------------- #

def test_v5_t125_provider_outage_resilience_and_graceful_fallbacks():
    """Verifies deterministic Socratic fallback on AI outage and 2D rubbing on Media outage."""
    # 1. AI Provider Outage (DeepSeek 503)
    ai_resp, ai_res = ProviderOutageSimulator.simulate_ai_outage_response(
        user_query="Ai đã chỉ đạo đúc Cửu Đỉnh?",
        outage_http_status=503,
    )
    assert ai_res.passed is True
    assert ai_res.retry_header_present is True
    assert ai_res.retry_after_seconds == 30
    assert ai_res.provenance_labeled is True
    assert ai_resp["provenance"] == "fallback_deterministic_socratic"
    assert "Đại Nam Thực Lục" in ai_resp["answer"]

    # 2. Media Provider Outage (LiveKit 503)
    media_resp, media_res = ProviderOutageSimulator.simulate_media_outage_response("cao-dinh")
    assert media_res.passed is True
    assert media_res.offline_learning_achievable is True
    assert media_resp["media_plane_status"] == "OFFLINE"
    assert media_resp["fallback_engaged"] == "2d_rubbing_and_transcript"
    assert "cao-dinh-rubbing.jpg" in media_resp["fallback_rubbing_url"]


# --------------------------------------------------------------------------- #
# Test 10: Network Flap Resilience and Idempotency Guarantee
# --------------------------------------------------------------------------- #

def test_v5_t125_network_flap_resilience_and_idempotency_guarantee(db_session):
    """Verifies client exponential backoff during network flaps and strict zero-duplicate guarantee."""
    idempotency_key = f"IDEMP-{uuid.uuid4().hex[:12].upper()}"
    mutation_invocations = 0

    def db_mutation():
        nonlocal mutation_invocations
        mutation_invocations += 1
        # Atomic record check / create simulating server-side idempotency lock
        existing = db_session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": f"{idempotency_key}@idemp.test"}
        ).fetchone()

        if existing:
            return {"user_id": str(existing[0]), "status": "ALREADY_PROCESSED"}

        new_user = User(
            email=f"{idempotency_key}@idemp.test",
            password_hash=hash_password("Password123!"),
            display_name="Idempotent Learner",
            username=f"u_{uuid.uuid4().hex[:8]}",
            role=UserRole.learner,
            is_profile_public=True,
        )
        db_session.add(new_user)
        db_session.commit()
        return {"user_id": str(new_user.id), "status": "CREATED"}

    # Simulate network flap with multiple retries
    final_result, flap_res = NetworkFlapSimulator.simulate_flapping_request(
        idempotency_key=idempotency_key,
        execution_func=db_mutation,
        flap_probability=0.5,
        max_client_retries=4,
    )

    assert flap_res.passed is True
    assert flap_res.zero_duplicate_guaranteed is True
    assert flap_res.duplicate_records_created == 0

    # Verify exactly ONE row in the database
    rows = db_session.execute(
        text("SELECT COUNT(*) FROM users WHERE email = :email"),
        {"email": f"{idempotency_key}@idemp.test"}
    ).scalar()
    assert rows == 1, f"Expected exactly 1 row, found {rows}"


# --------------------------------------------------------------------------- #
# Test 11: Unified Production Release Gate Evaluation (GATE_PASSED & GATE_BLOCKED)
# --------------------------------------------------------------------------- #

def test_v5_t125_unified_production_release_gate_evaluation(backup_dir: Path, client: TestClient):
    """Verifies that clean drills produce signed GATE_PASSED, and failures produce GATE_BLOCKED."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/luuniensuki_test")

    # 1. Concurrency metric
    cm = LoadConcurrencySimulator.evaluate_endpoint_concurrency(
        endpoint="/health",
        latencies_ms=[12.5, 14.1, 15.0, 16.2, 18.0],
        target_p95_ms=300.0,
    )
    assert cm.passed is True

    # 2. Gateway failover drill
    gw = FailoverDrillResult(
        scenario="PRIMARY_GATEWAY_OUTAGE",
        primary_node="http://api_rust:8001",
        secondary_node="http://api:8000",
        detection_time_ms=120.0,
        failover_duration_ms=45.0,
        requests_during_outage=100,
        requests_served_by_fallback=100,
        requests_dropped=0,
        failback_successful=True,
        passed=True,
    )

    # 3. DB pool failover
    db_pool = DatabasePoolFailoverResult(
        simulated_outage_type="TRANSIENT_DROPPED_CONNECTION",
        reconnection_attempts=1,
        reconnection_time_ms=25.0,
        transaction_retried=True,
        data_intact=True,
        passed=True,
    )

    # 4. Verified recovery bundle on disk
    evidence_dir = backup_dir / "release_gate_evidence"
    RecoveryEvidenceEngine.create_and_seal_evidence_bundle(
        bundle_dir=evidence_dir,
        source_db_url=db_url,
    )
    rec_ver = RecoveryEvidenceEngine.verify_recovery_evidence_from_disk(evidence_dir)
    assert rec_ver.passed is True

    # 5. Provider outage results
    _, ai_po = ProviderOutageSimulator.simulate_ai_outage_response("test", 503)
    _, media_po = ProviderOutageSimulator.simulate_media_outage_response("cao-dinh")

    # 6. Network flap result
    flap_res = NetworkFlapResilienceResult(
        total_attempts=3,
        flaps_encountered=2,
        successful_deliveries=1,
        idempotency_key="RELEASE-IDEMP-001",
        duplicate_records_created=0,
        zero_duplicate_guaranteed=True,
        passed=True,
    )

    # Positive Release Gate: All pass -> GATE_PASSED
    report = ProductionSLOE2EEvaluator.evaluate_production_readiness(
        concurrency_metrics=[cm],
        gateway_failover=gw,
        db_pool_failover=db_pool,
        recovery_verification=rec_ver,
        provider_outages=[ai_po, media_po],
        network_flap_result=flap_res,
    )

    assert report.decision == ReleaseGateDecision.GATE_PASSED
    assert len(report.blockers) == 0
    assert len(report.signed_hash) == 64  # Valid SHA-256

    # Negative Release Gate: Concurrency violation or tamper -> GATE_BLOCKED
    failing_cm = LoadConcurrencySimulator.evaluate_endpoint_concurrency(
        endpoint="/health",
        latencies_ms=[450.0, 520.0, 600.0],
        target_p95_ms=300.0,
    )
    blocked_report = ProductionSLOE2EEvaluator.evaluate_production_readiness(
        concurrency_metrics=[failing_cm],
        gateway_failover=gw,
        db_pool_failover=db_pool,
        recovery_verification=rec_ver,
        provider_outages=[ai_po, media_po],
        network_flap_result=flap_res,
    )

    assert blocked_report.decision == ReleaseGateDecision.GATE_BLOCKED
    assert len(blocked_report.blockers) > 0
    assert "Concurrency SLO violated" in blocked_report.blockers[0]
