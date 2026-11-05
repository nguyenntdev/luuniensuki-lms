# -*- coding: utf-8 -*-
"""Structured JSON logging, correlation IDs, distributed traces, and alert routing.

Ticket V5-T086 / Wave W08-A06.
Production invariants:
1. Structured JSON logging with `correlation_id` and `request_id` propagation.
2. Automatic PII redaction filter in formatters & handlers:
   - Redacts emails, phone numbers, auth passwords, bearer tokens, and JWT tokens/secrets into [REDACTED].
3. Negative abuse defense: Contact email/phone and student personal info are NEVER written to logs.
4. High-severity and security alert routing with zero PII leakage.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

# Context variables for propagating trace correlation across async execution boundaries
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

REDACTED = "[REDACTED]"

# --------------------------------------------------------------------------- #
# PII Redaction Regular Expressions
# --------------------------------------------------------------------------- #

# Email matching
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Phone matching: Vietnam domestic & international formats
PHONE_REGEX = re.compile(
    r"(?:(?:\+84|84|0)(?:[\s.\-]?\d){8,10}\b|"
    r"\b\(?0\d{1,3}\)?[\s.\-]?\d{3,4}[\s.\-]?\d{3,4}\b|"
    r"\b\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b)"
)

# Bearer token matching
BEARER_REGEX = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9\-_.~+/=]{10,}\b"
)

# JWT token matching (header.payload.signature)
JWT_REGEX = re.compile(
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
)

# Passwords, passphrases, secrets
PASSWORD_FIELD_REGEX = re.compile(
    r'(?i)(["\']?(?:password|passphrase|secret|passwd|pwd|pass|old_password|new_password|confirm_password|token_secret|jwt_secret)["\']?\s*[:=]\s*)(["\'][^"\']*["\']|[^\s,;&]+)'
)

# Auth and session tokens
AUTH_TOKEN_FIELD_REGEX = re.compile(
    r'(?i)(["\']?(?:access_token|refresh_token|id_token|session_token|auth_token)["\']?\s*[:=]\s*)(["\'][^"\']*["\']|[^\s,;&]+)'
)

# Contact info and student personal info fields
CONTACT_FIELD_REGEX = re.compile(
    r'(?i)(["\']?(?:contact_value|parent_email|parent_phone|guardian_email|guardian_phone|student_name|full_name)["\']?\s*[:=]\s*)(["\'][^"\']*["\']|[^\s,;&]+)'
)

# CCCD / National ID (9 or 12 digits preceded by relevant keyword)
NATIONAL_ID_REGEX = re.compile(
    r'(?i)(["\']?(?:cccd|cmnd|citizen_id|national_id|student_id)["\']?\s*[:=]\s*)(["\']?\d{9,12}["\']?|\d{9,12})'
)

SENSITIVE_KEYS = {
    "password",
    "passphrase",
    "secret",
    "passwd",
    "pwd",
    "pass",
    "old_password",
    "new_password",
    "confirm_password",
    "token_secret",
    "jwt_secret",
    "access_token",
    "refresh_token",
    "id_token",
    "session_token",
    "token",
    "authorization",
    "cookie",
    "set-cookie",
    "email",
    "phone",
    "contact_value",
    "parent_email",
    "parent_phone",
    "guardian_email",
    "guardian_phone",
    "student_name",
    "full_name",
    "national_id",
    "citizen_id",
    "cccd",
    "cmnd",
}


def _mask_field_match(m: re.Match) -> str:
    """Mask matched sensitive field value preserving quotes if present."""
    prefix = m.group(1)
    val = m.group(2)
    if val.startswith(('"', "'")) and val.endswith(('"', "'")) and len(val) >= 2:
        q = val[0]
        return f"{prefix}{q}{REDACTED}{q}"
    return f"{prefix}{REDACTED}"


def redact_pii(text: str) -> str:
    """Scrub sensitive PII (emails, phones, passwords, tokens, JWTs, student info) from text."""
    if not text or not isinstance(text, str):
        return text

    # 1. Redact Bearer tokens first
    text = BEARER_REGEX.sub("Bearer [REDACTED]", text)

    # 2. Redact JWTs
    text = JWT_REGEX.sub(REDACTED, text)

    # 3. Redact Password fields
    text = PASSWORD_FIELD_REGEX.sub(_mask_field_match, text)

    # 4. Redact Auth tokens
    text = AUTH_TOKEN_FIELD_REGEX.sub(_mask_field_match, text)

    # 5. Redact National ID fields
    text = NATIONAL_ID_REGEX.sub(_mask_field_match, text)

    # 6. Redact Contact fields
    text = CONTACT_FIELD_REGEX.sub(_mask_field_match, text)

    # 7. Redact Emails
    text = EMAIL_REGEX.sub(REDACTED, text)

    # 8. Redact Phone numbers
    text = PHONE_REGEX.sub(REDACTED, text)

    return text


def redact_pii_recursive(data: Any) -> Any:
    """Recursively scrub sensitive PII from dictionaries, lists, and primitives."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower().strip()
            if k_lower in SENSITIVE_KEYS:
                sanitized[k] = REDACTED
            elif isinstance(v, (dict, list, tuple)):
                sanitized[k] = redact_pii_recursive(v)
            elif isinstance(v, str):
                sanitized[k] = redact_pii(v)
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(data, list):
        return [redact_pii_recursive(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(redact_pii_recursive(item) for item in data)
    elif isinstance(data, str):
        return redact_pii(data)
    return data


# --------------------------------------------------------------------------- #
# Trace Context Accessors
# --------------------------------------------------------------------------- #

def get_correlation_id() -> str:
    """Get the active request correlation ID from context."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> Token:
    """Set the active request correlation ID in context."""
    return correlation_id_ctx.set(correlation_id)


def reset_correlation_id(token: Token) -> None:
    """Reset the correlation ID context to its prior state."""
    correlation_id_ctx.reset(token)


def get_request_id() -> str:
    """Get the active request ID from context."""
    return request_id_ctx.get()


def set_request_id(request_id: str) -> Token:
    """Set the active request ID in context."""
    return request_id_ctx.set(request_id)


def reset_request_id(token: Token) -> None:
    """Reset the request ID context to its prior state."""
    request_id_ctx.reset(token)


# --------------------------------------------------------------------------- #
# Logging Filter & Structured Formatter
# --------------------------------------------------------------------------- #

class PIIRedactionFilter(logging.Filter):
    """Logging filter that redacts all PII and enriches records with correlation & request IDs."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Propagate correlation_id and request_id onto the log record
        corr_id = getattr(record, "correlation_id", None) or get_correlation_id()
        req_id = getattr(record, "request_id", None) or get_request_id()
        record.correlation_id = corr_id
        record.request_id = req_id

        # Redact record message and args
        if record.args:
            try:
                if isinstance(record.args, dict):
                    redacted_args = {k: redact_pii_recursive(v) for k, v in record.args.items()}
                    formatted = record.msg % redacted_args
                else:
                    redacted_args = tuple(redact_pii_recursive(a) for a in record.args)
                    formatted = record.msg % redacted_args
                record.msg = redact_pii(formatted)
                record.args = ()
            except Exception:
                record.msg = redact_pii(str(record.msg))
        elif isinstance(record.msg, str):
            record.msg = redact_pii(record.msg)
        else:
            record.msg = redact_pii(str(record.msg))

        # Redact custom extra details if attached
        if hasattr(record, "details") and isinstance(record.details, dict):
            record.details = redact_pii_recursive(record.details)

        return True


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON lines with correlation ID, trace metadata, and zero PII."""

    def format(self, record: logging.LogRecord) -> str:
        # Context extraction
        corr_id = getattr(record, "correlation_id", None) or get_correlation_id() or None
        req_id = getattr(record, "request_id", None) or get_request_id() or None

        raw_msg = record.getMessage() if record.args else str(record.msg)
        sanitized_msg = redact_pii(raw_msg)

        now_utc = datetime.now(timezone.utc).isoformat()

        entry: dict[str, Any] = {
            "timestamp": now_utc,
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_msg,
            "correlation_id": corr_id,
            "request_id": req_id,
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
        }

        # Optional HTTP metadata
        for field in ("method", "path", "status_code", "duration_ms", "client_ip"):
            val = getattr(record, field, None)
            if val is not None:
                entry[field] = val

        # Exception formatting with PII redaction
        if record.exc_info:
            exc_str = self.formatException(record.exc_info)
            entry["exc_info"] = redact_pii(exc_str)

        # Extra structured details
        if hasattr(record, "details") and isinstance(record.details, dict):
            entry["details"] = redact_pii_recursive(record.details)

        return json.dumps(entry, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Alert Router & Alert Handler
# --------------------------------------------------------------------------- #

class AlertRouter:
    """Routes high-severity, security, and operational alerts with zero PII."""

    _instance: Optional["AlertRouter"] = None

    def __init__(self) -> None:
        self.sinks: Dict[str, Callable[[dict[str, Any]], None]] = {}
        self.history: List[dict[str, Any]] = []
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "AlertRouter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_sink(self, name: str, sink_fn: Callable[[dict[str, Any]], None]) -> None:
        """Register a destination sink callback for alerts."""
        with self._lock:
            self.sinks[name] = sink_fn

    def unregister_sink(self, name: str) -> None:
        """Unregister an alert sink."""
        with self._lock:
            self.sinks.pop(name, None)

    def route_alert(
        self,
        level: str,
        event_type: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Dispatch a sanitized alert to all registered sinks."""
        cid = correlation_id or get_correlation_id() or None
        rid = request_id or get_request_id() or None

        sanitized_details = redact_pii_recursive(details or {})
        sanitized_msg = redact_pii(message)

        alert_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "event_type": event_type,
            "message": sanitized_msg,
            "correlation_id": cid,
            "request_id": rid,
            "details": sanitized_details,
        }

        with self._lock:
            self.history.append(alert_payload)
            if len(self.history) > 1000:
                self.history = self.history[-1000:]
            active_sinks = list(self.sinks.values())

        for sink in active_sinks:
            try:
                sink(alert_payload)
            except Exception as e:
                logging.getLogger("luuniensuki.alerts").warning("Alert sink error: %s", str(e))

        return alert_payload

    def get_history(self) -> List[dict[str, Any]]:
        with self._lock:
            return list(self.history)

    def clear_history(self) -> None:
        with self._lock:
            self.history.clear()


class AlertRoutingHandler(logging.Handler):
    """Log handler that intercepts ERROR and CRITICAL records and dispatches alerts."""

    def __init__(self, level: int = logging.ERROR) -> None:
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            try:
                msg = record.getMessage() if record.args else str(record.msg)
                details = getattr(record, "details", {})
                if not isinstance(details, dict):
                    details = {"raw_details": str(details)}
                AlertRouter.get_instance().route_alert(
                    level=record.levelname,
                    event_type="log_event",
                    message=msg,
                    details=details,
                    correlation_id=getattr(record, "correlation_id", None),
                    request_id=getattr(record, "request_id", None),
                )
            except Exception:
                self.handleError(record)


# --------------------------------------------------------------------------- #
# Global Logging Initialization
# --------------------------------------------------------------------------- #

def setup_logging(
    level: Optional[int] = None,
    json_logs: bool = True,
) -> None:
    """Configure system-wide logging with PII redaction and structured formatting."""
    log_level = level or logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    pii_filter = PIIRedactionFilter()

    # Preserve any pytest capture handlers while adding the PII filter
    has_stdout_handler = False
    for h in root_logger.handlers:
        h.addFilter(pii_filter)
        if type(h) is logging.StreamHandler:
            has_stdout_handler = True
            if json_logs:
                h.setFormatter(StructuredJsonFormatter())

    if not has_stdout_handler:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.addFilter(pii_filter)
        if json_logs:
            handler.setFormatter(StructuredJsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] [%(name)s] [corr=%(correlation_id)s] %(message)s"
                )
            )
        root_logger.addHandler(handler)

    # Attach AlertRoutingHandler if not present
    if not any(isinstance(h, AlertRoutingHandler) for h in root_logger.handlers):
        alert_handler = AlertRoutingHandler()
        alert_handler.addFilter(pii_filter)
        root_logger.addHandler(alert_handler)

    # Also install filter on the primary app loggers
    for name in ("luuniensuki", "luuniensuki.api", "luuniensuki.rbpc", "luuniensuki.ai_telemetry"):
        app_log = logging.getLogger(name)
        if not any(isinstance(f, PIIRedactionFilter) for f in app_log.filters):
            app_log.addFilter(pii_filter)
