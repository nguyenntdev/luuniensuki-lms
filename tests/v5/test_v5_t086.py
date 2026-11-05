# -*- coding: utf-8 -*-
"""V5-T086: Structured Logs, Correlation IDs, Distributed Traces, and Zero-PII Alert Routing.

Wave W08, Slot A06 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Correlation and Request ID propagation across request headers, response headers, and async context.
2. Structured JSON logging with trace context (correlation_id, request_id, latency, status).
3. Automatic PII redaction filter in formatters & handlers:
   - Redacts emails, phone numbers, passwords, Bearer tokens, and JWT secrets to [REDACTED].
4. Negative abuse invariants:
   - Zero raw PII in log records during auth and inquiry flows.
   - Sensitive credentials, contact values, and student info are strictly scrubbed.
5. Alert routing:
   - High-severity events are dispatched to sinks with correlation IDs and zero PII.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.logging_config import (
    AlertRouter,
    AlertRoutingHandler,
    PIIRedactionFilter,
    StructuredJsonFormatter,
    get_correlation_id,
    get_request_id,
    redact_pii,
    redact_pii_recursive,
    set_correlation_id,
    set_request_id,
    setup_logging,
)
from backend.middleware.correlation import CorrelationIdMiddleware


class InMemoryLogHandler(logging.Handler):
    """Custom log handler for capturing formatted log output in test suites."""

    def __init__(self, formatter: logging.Formatter) -> None:
        super().__init__()
        self.setFormatter(formatter)
        self.records: List[logging.LogRecord] = []
        self.formatted_lines: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        self.formatted_lines.append(self.format(record))


@pytest.fixture
def log_capture():
    """Fixture providing an in-memory JSON log capture handler attached to root and app loggers."""
    json_formatter = StructuredJsonFormatter()
    handler = InMemoryLogHandler(json_formatter)
    pii_filter = PIIRedactionFilter()
    handler.addFilter(pii_filter)

    root = logging.getLogger()
    app_logger = logging.getLogger("luuniensuki")
    api_logger = logging.getLogger("luuniensuki.api")
    api_logger.setLevel(logging.DEBUG)
    app_logger.setLevel(logging.DEBUG)
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    app_logger.addHandler(handler)
    api_logger.addHandler(handler)
    yield handler
    root.removeHandler(handler)
    app_logger.removeHandler(handler)
    api_logger.removeHandler(handler)


@pytest.fixture
def app_client():
    """Client using the standard app factory with correlation middleware enabled."""
    app = create_app()
    return TestClient(app)


# ============================================================================= #
# 1. Correlation & Request ID Header & Context Propagation
# ============================================================================= #

def test_correlation_id_propagated_from_request_headers(app_client: TestClient):
    """X-Correlation-ID sent in request must be reflected in response headers."""
    custom_corr_id = "corr-test-trace-12345"
    custom_req_id = "req-test-uuid-67890"

    response = app_client.get(
        "/health",
        headers={
            "X-Correlation-ID": custom_corr_id,
            "X-Request-ID": custom_req_id,
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_corr_id
    assert response.headers.get("X-Request-ID") == custom_req_id


def test_correlation_id_minted_when_omitted(app_client: TestClient):
    """When headers are omitted, server mints fresh correlation and request IDs."""
    response = app_client.get("/health")
    assert response.status_code == 200

    corr_id = response.headers.get("X-Correlation-ID")
    req_id = response.headers.get("X-Request-ID")

    assert corr_id is not None
    assert corr_id.startswith("corr-")
    assert req_id is not None
    assert req_id.startswith("req-")


def test_request_id_used_as_fallback_for_correlation_id(app_client: TestClient):
    """When only X-Request-ID is provided, it is utilized for correlation as well."""
    custom_req_id = "req-standalone-9999"

    response = app_client.get(
        "/health",
        headers={"X-Request-ID": custom_req_id},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_req_id
    assert response.headers.get("X-Correlation-ID") == custom_req_id


def test_contextvars_propagation_in_handlers():
    """Test that contextvars correctly store and reset correlation and request IDs."""
    assert get_correlation_id() == ""
    assert get_request_id() == ""

    t1 = set_correlation_id("test-corr-1")
    t2 = set_request_id("test-req-1")

    assert get_correlation_id() == "test-corr-1"
    assert get_request_id() == "test-req-1"

    from backend.logging_config import reset_correlation_id, reset_request_id
    reset_correlation_id(t1)
    reset_request_id(t2)

    assert get_correlation_id() == ""
    assert get_request_id() == ""


# ============================================================================= #
# 2. Structured JSON Logging & Log Record Context Propagation
# ============================================================================= #

def test_structured_json_logging_with_trace_context(log_capture: InMemoryLogHandler):
    """Log records must be formatted as valid JSON containing trace metadata."""
    t_corr = set_correlation_id("corr-trace-8888")
    t_req = set_request_id("req-uuid-7777")

    logger = logging.getLogger("luuniensuki.api.test")
    logger.info("Executed test operation successfully")

    # Clean up context
    from backend.logging_config import reset_correlation_id, reset_request_id
    reset_correlation_id(t_corr)
    reset_request_id(t_req)

    # Find the emitted log line
    test_lines = [
        line for line in log_capture.formatted_lines
        if "Executed test operation successfully" in line
    ]
    assert len(test_lines) >= 1

    parsed = json.loads(test_lines[0])
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "luuniensuki.api.test"
    assert parsed["message"] == "Executed test operation successfully"
    assert parsed["correlation_id"] == "corr-trace-8888"
    assert parsed["request_id"] == "req-uuid-7777"
    assert "timestamp" in parsed
    assert "module" in parsed
    assert "line_no" in parsed


# ============================================================================= #
# 3. PII Redaction Engine Unit Verification
# ============================================================================= #

def test_redact_pii_emails():
    """All email formats must be redacted to [REDACTED]."""
    text = "User contact is john.doe@example.com or admin_test+1@edu.vn"
    redacted = redact_pii(text)
    assert "john.doe@example.com" not in redacted
    assert "admin_test+1@edu.vn" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_pii_phones():
    """Vietnamese and international phone formats must be redacted to [REDACTED]."""
    cases = [
        "Call me at 0901234567 please",
        "Hotline: +84912345678 available",
        "Phone: 098-765-4321 for booking",
        "Office: (024) 3825 1234 in Hanoi",
        "Mobile: +1 555 123 4567 USA",
    ]
    for case in cases:
        redacted = redact_pii(case)
        assert "[REDACTED]" in redacted
        assert "0901234567" not in redacted
        assert "+84912345678" not in redacted
        assert "098-765-4321" not in redacted


def test_redact_pii_passwords_and_secrets():
    """Passwords, secrets, and auth tokens must be redacted."""
    sample = (
        '{"username": "admin", "password": "SuperSecretPassword123!", "token_secret": "my-secret-key"}'
    )
    redacted = redact_pii(sample)
    assert "SuperSecretPassword123!" not in redacted
    assert "my-secret-key" not in redacted
    assert '"password": "[REDACTED]"' in redacted


def test_redact_pii_bearer_and_jwt_tokens():
    """Bearer tokens and raw JWTs must be redacted."""
    raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozG4B_TEST_SIGNATURE_HERE"
    auth_header = f"Authorization: Bearer {raw_jwt}"

    redacted = redact_pii(auth_header)
    assert raw_jwt not in redacted
    assert "Bearer [REDACTED]" in redacted


def test_redact_pii_recursive_dictionary():
    """Nested dictionaries must have all sensitive keys and strings sanitized."""
    data = {
        "user": {
            "email": "student@history.edu",
            "password": "Password99!",
            "profile": {
                "phone": "0912345678",
                "full_name": "Nguyễn Văn A",
                "notes": "Contact parent at parent@test.vn or 0987654321",
            },
        },
        "public_title": "Cao Đỉnh Relic",
    }
    cleaned = redact_pii_recursive(data)
    assert cleaned["user"]["email"] == "[REDACTED]"
    assert cleaned["user"]["password"] == "[REDACTED]"
    assert cleaned["user"]["profile"]["phone"] == "[REDACTED]"
    assert cleaned["user"]["profile"]["full_name"] == "[REDACTED]"
    assert "parent@test.vn" not in cleaned["user"]["profile"]["notes"]
    assert "0987654321" not in cleaned["user"]["profile"]["notes"]
    assert cleaned["public_title"] == "Cao Đỉnh Relic"


# ============================================================================= #
# 4. Negative Abuse Defense: Simulated Requests Leak Zero PII
# ============================================================================= #

def test_negative_abuse_simulated_auth_flow(app_client: TestClient, log_capture: InMemoryLogHandler):
    """Simulated login attempt with sensitive credentials must not leak password or email to logs."""
    sensitive_email = "test.target.user@secret-domain.org"
    sensitive_password = "SuperUnbreakablePassword2026!"

    # Send login request (will return 401 because credentials are mock)
    response = app_client.post(
        "/api/v1/auth/login",
        json={"email": sensitive_email, "password": sensitive_password},
    )
    # Regardless of response status:
    assert response.status_code in (400, 401, 422)

    # Check all captured log lines
    all_log_text = "\n".join(log_capture.formatted_lines)
    assert sensitive_password not in all_log_text
    assert sensitive_email not in all_log_text


def test_negative_abuse_simulated_inquiry_flow(app_client: TestClient, log_capture: InMemoryLogHandler):
    """Simulated inquiry with visitor contact email/phone must not leak raw PII to logs."""
    visitor_email = "booking.visitor2026@heritage-hue.com"
    visitor_phone = "0988776655"
    visitor_name = "Trần Thị Khách"

    payload = {
        "experience_id": str(uuid.uuid4()),
        "name": visitor_name,
        "contact_value": visitor_email,
        "contact_channel": "email",
        "party_size": 2,
        "note": f"Please call me at {visitor_phone} if email fails.",
    }

    response = app_client.post(
        "/api/v1/rbpc/inquiries",
        json=payload,
    )
    # The inquiry may fail validation (e.g. invalid experience_id), but logs must remain clean
    all_log_text = "\n".join(log_capture.formatted_lines)

    assert visitor_email not in all_log_text
    assert visitor_phone not in all_log_text


def test_negative_abuse_explicit_logger_invocation():
    """Explicit developer log call with PII is intercepted and sanitized by PIIRedactionFilter."""
    json_formatter = StructuredJsonFormatter()
    local_handler = InMemoryLogHandler(json_formatter)
    pii_filter = PIIRedactionFilter()
    local_handler.addFilter(pii_filter)

    app_logger = logging.getLogger("luuniensuki.explicit_test")
    app_logger.handlers.clear()
    app_logger.addHandler(local_handler)
    app_logger.propagate = False
    app_logger.setLevel(logging.DEBUG)

    email = "hacker.student@compromised.net"
    phone = "0912999888"
    password = "LeakedPasswordXYZ"

    # Simulate developer logging PII in format string and arguments
    app_logger.warning("Auth failure for email: %s with pass: %s, contact: %s", email, password, phone)

    matching_lines = [
        line for line in local_handler.formatted_lines
        if "Auth failure for email" in line
    ]
    assert len(matching_lines) >= 1

    logged_line = matching_lines[0]
    assert email not in logged_line
    assert phone not in logged_line
    assert password not in logged_line
    assert "[REDACTED]" in logged_line


# ============================================================================= #
# 5. Alert Routing with Correlation & Zero-PII Invariant
# ============================================================================= #

def test_alert_router_receives_sanitized_payload():
    """Alerts dispatched via AlertRouter must include correlation ID and redacted details."""
    router = AlertRouter.get_instance()
    router.clear_history()

    captured_alerts = []
    def mock_sink(alert_data: dict[str, Any]):
        captured_alerts.append(alert_data)

    router.register_sink("test_security_sink", mock_sink)

    try:
        t_corr = set_correlation_id("corr-alert-999")
        t_req = set_request_id("req-alert-888")

        router.route_alert(
            level="ERROR",
            event_type="security_incident",
            message="Suspicious login for admin@histolab.icu with password=SecretPassword!",
            details={
                "ip": "127.0.0.1",
                "attempted_user": "admin@histolab.icu",
                "phone": "0901234567",
                "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig",
            },
        )

        from backend.logging_config import reset_correlation_id, reset_request_id
        reset_correlation_id(t_corr)
        reset_request_id(t_req)

        assert len(captured_alerts) == 1
        alert = captured_alerts[0]
        assert alert["level"] == "ERROR"
        assert alert["event_type"] == "security_incident"
        assert alert["correlation_id"] == "corr-alert-999"
        assert alert["request_id"] == "req-alert-888"

        # Check message scrubbing
        assert "admin@histolab.icu" not in alert["message"]
        assert "SecretPassword!" not in alert["message"]
        assert "[REDACTED]" in alert["message"]

        # Check details dictionary scrubbing
        details = alert["details"]
        assert details["attempted_user"] == "[REDACTED]"
        assert details["phone"] == "[REDACTED]"
        assert details["token"] == "[REDACTED]"
        assert "admin@histolab.icu" not in str(details)
        assert "0901234567" not in str(details)

    finally:
        router.unregister_sink("test_security_sink")
