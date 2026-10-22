# -*- coding: utf-8 -*-
"""V5-T010: Observability & Deployment Baseline Test Suite.

Audits and verifies:
1. Deployment configuration integrity:
   - docker-compose.prod.yml syntax, required production env vars, healthchecks, dependencies.
   - nginx-luunien-staging.conf reverse proxy configuration (Cloudflare headers, SSL/TLS,
     GDPR log sanitization, rate limiting zones and error envelope, WebRTC routing).
   - scripts/deployment/rollback-staging.sh executable rollback runbook.
2. Health check and readiness probe logic:
   - FastAPI /health responsiveness (healthy vs degraded states).
   - Unimplemented /ready probe (verifying no fake /ready endpoint exists).
   - Rust gateway /health liveness and /api/v1/internal/db-health readiness contracts.
3. Negative / abuse test:
   - "No claiming uptime or metrics PASS without concrete probe definitions."
   - Unmeasured documentation claims (e.g. 99.9% uptime, live_ai_active_sessions in /metrics,
     /ready endpoint) must be flagged as DOCS_ONLY_UNMEASURED and rejected if claimed as PASS.
4. Parity of Prometheus metrics text exposition in backend-rust/src/routes/metrics.rs.
5. Observability baseline artifact integrity:
   artifacts/implementation/W00/W00_A10_observability_baseline.json.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from backend.app import create_app
from backend.deps import get_db

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = (
    REPO_ROOT
    / "artifacts"
    / "implementation"
    / "W00"
    / "W00_A10_observability_baseline.json"
)


# ==============================================================================
# Helper Verification Engine for Concrete Probes
# ==============================================================================

VALID_PROBE_TYPES = {"endpoint", "counter", "container_healthcheck", "script"}


def validate_observability_claim(claim_record: dict) -> None:
    """Validate that an observability or telemetry claim has a concrete probe definition.

    Enforces the Core Mandate:
    'No claiming uptime or metrics PASS without concrete probe definitions.'
    Raises AssertionError if a claim asserts PASS without an authentic, verified probe.
    """
    status = claim_record.get("status")
    probe = claim_record.get("probe")

    if status == "PASS":
        if not probe or not isinstance(probe, dict):
            raise AssertionError(
                f"Abuse detected: Claim '{claim_record.get('claim')}' marked PASS "
                f"without concrete probe definition!"
            )
        probe_type = probe.get("type")
        if probe_type not in VALID_PROBE_TYPES:
            raise AssertionError(
                f"Abuse detected: Probe type '{probe_type}' for claim "
                f"'{claim_record.get('claim')}' is not recognized as a concrete probe!"
            )
        target = probe.get("target")
        if not target:
            raise AssertionError(
                f"Abuse detected: Probe for claim '{claim_record.get('claim')}' "
                f"has empty target definition!"
            )
    elif status in ("DOCS_ONLY_UNMEASURED", "UNIMPLEMENTED_NOT_MEASURED"):
        verdict = claim_record.get("verdict")
        if verdict not in ("FAIL_CLAIM_WITHOUT_PROBE", "UNVERIFIED"):
            raise AssertionError(
                f"Unmeasured claim '{claim_record.get('claim')}' must be flagged with "
                f"verdict='FAIL_CLAIM_WITHOUT_PROBE' or 'UNVERIFIED', got '{verdict}'"
            )


# ==============================================================================
# 1. Deployment Configuration Integrity
# ==============================================================================


def test_docker_compose_prod_configuration_integrity():
    """Verify docker-compose.prod.yml syntax, required production env vars, and healthchecks."""
    compose_file = REPO_ROOT / "docker-compose.prod.yml"
    assert compose_file.exists(), "docker-compose.prod.yml must exist"

    with open(compose_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Raw check for required fail-closed environment variables (:? syntax)
    required_fail_closed_vars = [
        "POSTGRES_DB:?POSTGRES_DB is required in production",
        "POSTGRES_USER:?POSTGRES_USER is required in production",
        "POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required in production",
        "JWT_SECRET_KEY:?JWT_SECRET_KEY is required in production",
        "LIVEKIT_API_KEY:?LIVEKIT_API_KEY is required in production",
        "LIVEKIT_API_SECRET:?LIVEKIT_API_SECRET is required in production",
        "JANUS_ADMIN_SECRET:?JANUS_ADMIN_SECRET is required in production",
        "JANUS_API_SECRET:?JANUS_API_SECRET is required in production",
    ]
    for var_guard in required_fail_closed_vars:
        assert (
            var_guard in content
        ), f"Missing fail-closed production variable guard: {var_guard}"

    # Parse YAML structure
    # Use custom constructor or replace shell interpolation for standard YAML parser
    clean_yaml = re.sub(r"\$\{[^}]+\}", "placeholder_val", content)
    clean_yaml = clean_yaml.replace("$$POSTGRES_USER", "postgres").replace(
        "$$POSTGRES_DB", "luuniensuki"
    )
    parsed = yaml.safe_load(clean_yaml)

    services = parsed.get("services", {})
    expected_services = {
        "db",
        "api",
        "api_rust",
        "web",
        "ai_teacher_agent",
        "livekit",
        "janus-gateway",
        "nginx",
    }
    assert (
        set(services.keys()) == expected_services
    ), f"Services mismatch: {set(services.keys())} vs {expected_services}"

    # Verify db healthcheck
    db_hc = services["db"].get("healthcheck", {})
    assert "pg_isready" in " ".join(
        db_hc.get("test", [])
    ), "db service must define pg_isready healthcheck"
    assert db_hc.get("interval") == "5s"
    assert db_hc.get("retries") == 20

    # Verify container dependencies
    assert (
        services["api"]["depends_on"]["db"]["condition"] == "service_healthy"
    )
    assert (
        services["api_rust"]["depends_on"]["db"]["condition"]
        == "service_healthy"
    )
    assert (
        services["ai_teacher_agent"]["depends_on"]["db"]["condition"]
        == "service_healthy"
    )
    assert "api_rust" in services["web"]["depends_on"]

    # Verify restart policy
    for s_name in ["db", "api", "api_rust", "web", "nginx"]:
        assert (
            services[s_name].get("restart") == "unless-stopped"
        ), f"Service {s_name} missing restart: unless-stopped"


def test_nginx_staging_configuration_integrity():
    """Verify reverse proxy configuration in nginx-luunien-staging.conf."""
    nginx_file = REPO_ROOT / "nginx-luunien-staging.conf"
    assert nginx_file.exists(), "nginx-luunien-staging.conf must exist"

    with open(nginx_file, "r", encoding="utf-8") as f:
        conf = f.read()

    # 1. Cloudflare real IP restoration
    assert (
        "real_ip_header CF-Connecting-IP;" in conf
    ), "Must restore client IP via CF-Connecting-IP"
    assert (
        "set_real_ip_from 173.245.48.0/20;" in conf
    ), "Must include Cloudflare IPv4 ranges"
    assert (
        "set_real_ip_from 2400:cb00::/32;" in conf
    ), "Must include Cloudflare IPv6 ranges"

    # 2. Zero-PII Log Sanitization
    assert (
        "map $remote_addr $anonymized_remote_addr" in conf
    ), "Must mask client IP"
    assert (
        "map $query_string $sanitized_query_string" in conf
    ), "Must redact sensitive query params"
    assert (
        "log_format sanitized_combined" in conf
    ), "Must define sanitized_combined log format"
    for sensitive_param in [
        "token",
        "secret",
        "opaque_token",
        "contact_value",
        "email",
        "phone",
    ]:
        assert (
            sensitive_param in conf
        ), f"Log sanitization regex must redact '{sensitive_param}'"

    # 3. Rate limiting zones & 429 error envelope
    assert (
        "limit_req_zone $binary_remote_addr zone=rbpc_inquiry:10m rate=5r/m;"
        in conf
    )
    assert (
        "limit_req_zone $binary_remote_addr zone=rbpc_ai:10m rate=20r/m;"
        in conf
    )
    assert "limit_req_status 429;" in conf
    assert "error_page 429 = @rate_limited;" in conf
    assert "RATE_LIMIT_EXCEEDED" in conf
    assert "retry_after_seconds" in conf
    assert "add_header Retry-After 60 always;" in conf

    # 4. SSL & Security headers
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in conf
    assert "Strict-Transport-Security" in conf
    assert "X-Frame-Options" in conf
    assert "X-Content-Type-Options" in conf
    assert "Content-Security-Policy" in conf
    assert "Permissions-Policy" in conf

    # 5. Dynamic Docker resolver to prevent startup crash on upstream reboots
    assert (
        "resolver 127.0.0.11 ipv6=off valid=30s;" in conf
    ), "Must use internal Docker DNS resolver"
    assert "set $api_upstream http://api_rust:8001;" in conf
    assert "set $web_upstream http://web:3000;" in conf

    # 6. WebRTC signaling & static caching
    assert "location = /livekit" in conf
    assert "location ^~ /livekit/" in conf
    assert "location ^~ /janus" in conf
    assert "proxy_set_header Upgrade $http_upgrade;" in conf
    assert "proxy_set_header Connection \"upgrade\";" in conf


def test_rollback_script_integrity():
    """Verify existence, permissions, and logic of scripts/deployment/rollback-staging.sh."""
    rollback_script = REPO_ROOT / "scripts" / "deployment" / "rollback-staging.sh"
    assert rollback_script.exists(), "rollback-staging.sh must exist"
    assert os.access(
        rollback_script, os.X_OK
    ), "rollback-staging.sh must be executable"

    with open(rollback_script, "r", encoding="utf-8") as f:
        script = f.read()

    # Verify essential rollback steps:
    # 1. Stop application containers while preserving database
    assert "stop web api api_rust ai_teacher_agent" in script
    # 2. Reset codebase to previous known-good commit
    assert 'git checkout "${PREV_COMMIT}"' in script
    # 3. Rebuild and restart application stack
    assert "up -d --build api api_rust web ai_teacher_agent nginx" in script
    # 4. Post-rollback health check
    assert "/health" in script
    assert "ROLLBACK SUCCESSFUL" in script


# ==============================================================================
# 2. Health Check & Readiness Probes
# ==============================================================================


@pytest.fixture
def api_client():
    """Lightweight test client for health endpoints without full table recreation."""
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        yield client


def test_fastapi_health_endpoint_healthy(api_client):
    """FastAPI /health returns HTTP 200 with status=ok and database=ok when DB is reachable."""
    res = api_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert "version" in data


def test_fastapi_health_endpoint_degraded(api_client):
    """FastAPI /health returns HTTP 200 with status=degraded when DB query raises."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Database connection failure")

    def override_get_db_failing():
        yield mock_db

    from backend.main import app

    app.dependency_overrides[get_db] = override_get_db_failing
    try:
        res = api_client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "degraded"
        assert data["database"] == "error"
    finally:
        app.dependency_overrides.clear()


def test_ready_endpoint_is_unimplemented_in_route_table(api_client):
    """Verifies that /ready is NOT implemented on the API (returns 404).

    Prevents false claims that /ready exists when only /api/v1/internal/db-health is implemented.
    """
    res = api_client.get("/ready")
    assert (
        res.status_code == 404
    ), f"/ready should return 404 Not Found, got {res.status_code}"



def test_rust_gateway_health_contract_definitions():
    """Verify Rust gateway /health and /api/v1/internal/db-health definitions in source."""
    health_rs = REPO_ROOT / "backend-rust" / "src" / "routes" / "health.rs"
    assert health_rs.exists(), "backend-rust/src/routes/health.rs must exist"

    with open(health_rs, "r", encoding="utf-8") as f:
        src = f.read()

    # /health unconditionally returns ok
    assert "pub async fn health() -> Json<Value>" in src
    assert 'json!({ "status": "ok" })' in src

    # /api/v1/internal/db-health checks PgPool and returns 200 or 503
    assert (
        "pub async fn db_health(State(pool): State<Option<PgPool>>) -> impl IntoResponse"
        in src
    )
    assert "crate::db::ping(&pool).await" in src
    assert "StatusCode::SERVICE_UNAVAILABLE" in src
    assert "StatusCode::OK" in src


# ==============================================================================
# 3. Prometheus Metrics & Telemetry Parity
# ==============================================================================


def test_prometheus_metrics_contract_and_parity():
    """Verify Prometheus metrics exposed by Rust gateway in backend-rust/src/routes/metrics.rs."""
    metrics_rs = REPO_ROOT / "backend-rust" / "src" / "routes" / "metrics.rs"
    assert metrics_rs.exists(), "backend-rust/src/routes/metrics.rs must exist"

    with open(metrics_rs, "r", encoding="utf-8") as f:
        src = f.read()

    expected_counters = [
        "REQUEST_COUNT",
        "ERROR_COUNT",
        "GATEWAY_COUNT",
        "NATIVE_COUNT",
        "LATENCY_SUM_MS",
        "STREAK_REPAIR_TOTAL",
        "STREAK_BRB_TOTAL",
        "FRIEND_STREAK_INCREMENT_TOTAL",
        "PHOENIX_BADGE_TOTAL",
        "FSRS_REVIEWS_TOTAL",
    ]
    for counter in expected_counters:
        assert (
            counter in src
        ), f"Missing required atomic counter in metrics.rs: {counter}"

    # Verify Prometheus output text format (note Rust format! escapes braces with {{ }})
    assert "http_requests_total" in src
    assert "http_errors_total" in src
    assert 'http_requests_by_mode_total{{mode=\\"native\\"}}' in src
    assert 'http_requests_by_mode_total{{mode=\\"gateway\\"}}' in src
    assert "http_request_duration_milliseconds_sum" in src

    # Verify that docs-only unmeasured metrics are NOT in metrics.rs
    docs_only_metrics = [
        "live_ai_active_sessions",
        "live_ai_audio_minutes_total",
        "live_ai_token_expenditure_total",
    ]
    for m in docs_only_metrics:
        assert (
            m not in src
        ), f"Docs-only metric '{m}' was found in metrics.rs! Update baseline artifact if implemented."


# ==============================================================================
# 4. Negative / Abuse Test: No PASS Without Concrete Probe
# ==============================================================================


def test_negative_abuse_probe_validation_rejects_unmeasured_claims():
    """Abuse test: Reject claiming PASS for unmeasured or docs-only claims without a probe.

    Enforces:
    'No claiming uptime or metrics PASS without concrete probe definitions.'
    """
    # Case 1: Attempting to claim 99.99% uptime PASS without a probe must FAIL
    false_uptime_claim = {
        "claim": "99.99% Production Uptime SLA",
        "status": "PASS",
        "probe": None,
    }
    with pytest.raises(
        AssertionError, match="without concrete probe definition"
    ):
        validate_observability_claim(false_uptime_claim)

    # Case 2: Attempting to claim unmeasured live_ai_active_sessions PASS with invalid probe
    false_metric_claim = {
        "claim": "live_ai_active_sessions",
        "status": "PASS",
        "probe": {
            "type": "invalid_probe_type",
            "target": "docs/rbpc/STAGING_DEPLOYMENT_SPEC.md",
        },
    }
    with pytest.raises(AssertionError, match="not recognized as a concrete probe"):
        validate_observability_claim(false_metric_claim)

    # Case 3: Attempting to claim /ready probe PASS without target
    false_ready_claim = {
        "claim": "/ready endpoint",
        "status": "PASS",
        "probe": {"type": "endpoint", "target": ""},
    }
    with pytest.raises(AssertionError, match="empty target definition"):
        validate_observability_claim(false_ready_claim)

    # Case 4: Valid concrete probe claiming PASS must succeed
    valid_probe = {
        "claim": "Process Liveness",
        "status": "PASS",
        "probe": {
            "type": "endpoint",
            "target": "https://luunien.histolab.icu/health",
        },
    }
    validate_observability_claim(valid_probe)

    # Case 5: Honest DOCS_ONLY_UNMEASURED claim with FAIL_CLAIM_WITHOUT_PROBE verdict succeeds
    honest_claim = {
        "claim": "live_ai_active_sessions",
        "status": "DOCS_ONLY_UNMEASURED",
        "verdict": "FAIL_CLAIM_WITHOUT_PROBE",
    }
    validate_observability_claim(honest_claim)


# ==============================================================================
# 5. Baseline Artifact Validation
# ==============================================================================


def test_observability_baseline_artifact_validity():
    """Verify that the baseline artifact exists and conforms to the implementation contract."""
    assert ARTIFACT_PATH.exists(), f"Artifact missing: {ARTIFACT_PATH}"

    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Meta validation
    meta = data.get("meta", {})
    assert meta.get("ticket_id") == "V5-T010"
    assert meta.get("slot") == "W00-A10"
    assert (
        meta.get("baseline_source_sha")
        == "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
    )
    assert meta.get("status") == "PASS"

    # 2. Deployment manifests audit
    manifests = data.get("deployment_manifests", {})
    dc_prod = manifests.get("docker_compose_prod", {})
    assert dc_prod.get("syntax_valid") is True
    assert dc_prod.get("services_count") == 8
    assert len(dc_prod.get("required_production_env_vars", [])) == 8

    # 3. Reverse proxy audit
    proxy = data.get("reverse_proxy_configuration", {})
    staging = proxy.get("staging_config", {})
    assert staging.get("syntax_valid") is True
    assert staging.get("domain") == "luunien.histolab.icu"
    assert (
        staging.get("cloudflare_real_ip_restoration", {}).get("enabled")
        is True
    )

    # 4. Health and readiness probes
    probes_data = data.get("health_and_readiness_probes", {}).get("probes", [])
    ready_probe = next((p for p in probes_data if p.get("path") == "/ready"), None)
    assert ready_probe is not None, "Baseline must account for /ready probe"
    assert ready_probe.get("status") == "UNIMPLEMENTED_NOT_MEASURED"
    assert ready_probe.get("verified") is False

    # 5. Unmeasured / docs-only claims must be flagged
    telemetry = data.get("logging_and_monitoring_telemetry", {})
    unmeasured_claims = telemetry.get("unmeasured_or_docs_only_claims", [])
    assert len(unmeasured_claims) >= 4, "Must catalogue unmeasured claims"
    for claim in unmeasured_claims:
        assert (
            claim.get("status") == "DOCS_ONLY_UNMEASURED"
        ), f"Claim {claim.get('claim')} must be marked DOCS_ONLY_UNMEASURED"
        assert claim.get("verdict") == "FAIL_CLAIM_WITHOUT_PROBE"
        # Run abuse verification engine on artifact claim
        validate_observability_claim(claim)

    # 6. Operational commands
    ops = data.get("verified_operational_commands", {})
    assert len(ops.get("staging", [])) >= 5
    assert len(ops.get("production", [])) >= 5
