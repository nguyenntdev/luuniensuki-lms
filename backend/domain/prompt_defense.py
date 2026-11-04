# -*- coding: utf-8 -*-
"""Prompt-Injection Defenses & Untrusted Input Sanitization (Wave W06 / Ticket V5-T066).

Treats all user/student inputs and external source texts as UNTRUSTED.
Enforces:
1. Strict system boundary delimiters with escaping of embedded delimiters.
2. Prompt injection & adversarial abuse detection (overrides, jailbreaks, secret leakage, code/shell).
3. Tool execution allowlist with zero code execution or shell evaluation.
4. Secret redaction / scrubbing across generated responses.
"""
from __future__ import annotations

import logging
import os
import re
import unicodedata
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings

logger = logging.getLogger("luuniensuki.prompt_defense")

# --------------------------------------------------------------------------- #
# Constants & Enums
# --------------------------------------------------------------------------- #
MAX_UNTRUSTED_INPUT_LENGTH = 4000

# Canonical boundary delimiters used by history tutor and RBPC AI
DELIMITER_CLAIM_START = "[[[CLAIM_START]]]"
DELIMITER_CLAIM_END = "[[[CLAIM_END]]]"

# Forbidden control / bidi / zero-width characters used for obfuscation
BIDI_AND_ZERO_WIDTH_CHARS = re.compile(
    r"[\u200B-\u200F\u202A-\u202E\u2066-\u2069\uFEFF\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)

# Regex matching any claim or context boundary forgery attempt
DELIMITER_ESCAPE_PATTERN = re.compile(
    r"\[{2,3}\s*(?:CLAIM|CONTEXT|SYSTEM|DATA)_(?:START|END|HEADER)[^\]]*\]{2,3}",
    re.IGNORECASE,
)

# Strict Tool Execution Allowlist: Only these safe, purely informational tools may run.
ALLOWED_TOOLS: frozenset[str] = frozenset(
    {
        "open_entity",
        "view_source",
        "search_claims",
        "get_epistemic_status",
        "suggest_followup",
    }
)

# Forbidden execution patterns in tool names or parameter payloads
FORBIDDEN_EXECUTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(eval|exec|compile|__import__|globals|locals|getattr|setattr)\s*\(", re.IGNORECASE),
    re.compile(r"\b(os\.system|subprocess\.|popen|spawn|shutil\.|sys\.)", re.IGNORECASE),
    re.compile(r"\b(bash|sh|zsh|powershell|cmd\.exe)\b", re.IGNORECASE),
    re.compile(r"(?:/bin/sh|/bin/bash|/etc/passwd|/etc/shadow|\brm\s+-rf\b|\bcat\s+/etc)", re.IGNORECASE),
    re.compile(r"(?:\||\;|\&|\`|\$\()(?:\s*[\w\.\/]+)+"),
)

# Injection and adversarial abuse patterns
INJECTION_DIRECTIVE_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    (
        "instruction_override",
        re.compile(
            r"\b(?:ignore|disregard|forget|bypass|override)\s+(?:all\s+)?(?:previous|prior|above|system)\s+(?:instructions|rules|directives|prompts|commands)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "instruction_override_vi",
        re.compile(
            r"\b(?:bỏ qua|quên|ghi đè|không tuân theo)\s+(?:mọi\s+)?(?:chỉ dẫn|hướng dẫn|quy tắc|lệnh|chỉ thị)\s+(?:trước|trước đó|hệ thống)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "jailbreak_roleplay",
        re.compile(
            r"\b(?:you are now|pretend to be|act as|switch to)\s+(?:dan|developer mode|unrestricted|an evil|an unfiltered|god mode)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "jailbreak_roleplay_vi",
        re.compile(
            r"\b(?:chuyển sang|đóng vai|vào chế độ)\s+(?:lập trình viên|developer mode|dan|không giới hạn|bỏ kiểm duyệt)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "secret_exfiltration",
        re.compile(
            r"\b(?:print|reveal|show|dump|leak|output|echo|display|tell me)\s+(?:the\s+)?(?:secret|api[ _]?key|jwt|password|token|credentials|env|environment variable|database[ _]?url)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "secret_exfiltration_names",
        re.compile(
            r"\b(?:jwt_secret_key|deepseek_api_key|clara_api_key|database_url|secret_key|postgres_password)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "secret_exfiltration_vi",
        re.compile(
            r"\b(?:in|tiết lộ|cho xem|xuất|đọc|hiển thị)\s+(?:khóa bí mật|mật khẩu|api key|jwt secret|biến môi trường|chuỗi kết nối db)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "code_shell_execution",
        re.compile(
            r"\b(?:run shell|execute code|exec command|os\.system|eval\(|exec\(|subprocess|cat /etc/passwd|rm -rf)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "code_shell_execution_vi",
        re.compile(
            r"\b(?:thực thi lệnh|chạy lệnh|chạy shell|thực thi mã|mở terminal)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "system_prompt_leak",
        re.compile(
            r"\b(?:repeat|show|print|reveal|output)\s+(?:the\s+)?(?:system prompt|initial instructions|hidden instructions|base prompt)\b",
            re.IGNORECASE,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Custom Exceptions
# --------------------------------------------------------------------------- #
class PromptInjectionDetectedError(ValueError):
    """Raised when an active prompt injection attack is detected and rejected."""

    def __init__(self, message: str, threats: list[str]):
        super().__init__(message)
        self.threats = threats


class UnauthorizedToolError(PermissionError):
    """Raised when an attempt is made to invoke an unauthorized tool."""


class SecurityViolationError(PermissionError):
    """Raised when an execution pattern violates strict security policies."""


# --------------------------------------------------------------------------- #
# Untrusted Text Sanitization & Delimiter Neutralization
# --------------------------------------------------------------------------- #
def sanitize_untrusted_text(
    text: Optional[str],
    *,
    max_length: int = MAX_UNTRUSTED_INPUT_LENGTH,
    escape_delimiters: bool = True,
) -> str:
    """Sanitize untrusted student questions or external source texts.

    Guarantees:
    - Normalizes Unicode and strips invisible zero-width and bidirectional control characters.
    - Neutralizes forged system/claim boundary delimiters (e.g. [[[CLAIM_END]]]).
    - Enforces input length bounds to prevent token-exhaustion denial of service.
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    # 1. Strip invisible / bidi control characters used for obfuscation
    cleaned = BIDI_AND_ZERO_WIDTH_CHARS.sub("", text)

    # 2. Unicode normalization (NFC ensures consistent glyph representation)
    cleaned = unicodedata.normalize("NFC", cleaned)

    # 3. Delimiter escape: replace forged delimiters with safe inert representations
    if escape_delimiters:
        # Explicit known boundary tags
        cleaned = cleaned.replace(
            DELIMITER_CLAIM_START, "[SAFE_DATA_DELIMITER:CLAIM_START]"
        )
        cleaned = cleaned.replace(
            DELIMITER_CLAIM_END, "[SAFE_DATA_DELIMITER:CLAIM_END]"
        )
        # Any regex match of [[[...]]] or [[...]] boundary attempts
        cleaned = DELIMITER_ESCAPE_PATTERN.sub(
            lambda m: f"[SAFE_TAG:{m.group(0).strip('[] ')}]", cleaned
        )

    # 4. Length truncation
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


# --------------------------------------------------------------------------- #
# Prompt Injection & Abuse Detection
# --------------------------------------------------------------------------- #
def detect_prompt_injection(text: str) -> tuple[bool, list[str]]:
    """Inspect text for prompt injection, jailbreak, secret exfiltration, or code execution.

    Returns:
        (is_injection, detected_threat_categories)
    """
    if not text or not text.strip():
        return False, []

    threats: list[str] = []
    normalized = " ".join(text.split()).lower()

    for category, pattern in INJECTION_DIRECTIVE_PATTERNS:
        if pattern.search(text) or pattern.search(normalized):
            threats.append(category)

    # Also check for code/shell evaluation patterns
    for pat in FORBIDDEN_EXECUTION_PATTERNS:
        if pat.search(text):
            if "code_shell_execution" not in threats:
                threats.append("code_shell_execution")
            break

    is_injection = len(threats) > 0
    return is_injection, threats


def inspect_prompt_safety(text: str) -> dict[str, Any]:
    """Perform a structured security audit of a prompt or query."""
    sanitized = sanitize_untrusted_text(text)
    is_injection, threats = detect_prompt_injection(text)

    if not is_injection:
        risk_level = "safe"
    elif any(t in threats for t in ("code_shell_execution", "secret_exfiltration", "secret_exfiltration_names")):
        risk_level = "critical"
    elif any(t in threats for t in ("instruction_override", "jailbreak_roleplay")):
        risk_level = "high"
    else:
        risk_level = "medium"

    return {
        "is_safe": not is_injection,
        "risk_level": risk_level,
        "threats": threats,
        "sanitized_text": sanitized,
    }


# --------------------------------------------------------------------------- #
# Secret Redaction / Scrubbing
# --------------------------------------------------------------------------- #
def _gather_known_secrets() -> list[str]:
    """Collect sensitive strings that must NEVER leak in model outputs."""
    secrets_set: set[str] = set()

    # Collect from settings object
    for attr in (
        "jwt_secret_key",
        "deepseek_api_key",
        "clara_api_key",
        "database_url",
        "livekit_api_key",
        "livekit_api_secret",
        "livekit_webhook_secret",
        "embedding_api_key",
    ):
        val = getattr(settings, attr, None)
        if val and isinstance(val, str) and len(val.strip()) >= 4:
            secrets_set.add(val.strip())

    # Collect from environment variables
    sensitive_env_keys = (
        "SECRET",
        "KEY",
        "PASSWORD",
        "TOKEN",
        "DATABASE_URL",
        "PRIVATE",
    )
    for env_name, env_val in os.environ.items():
        if any(sk in env_name.upper() for sk in sensitive_env_keys):
            if env_val and len(env_val.strip()) >= 4:
                # Do not redact common short values like 'true', 'false', '0', '1', 'dev'
                if env_val.strip().lower() not in {"true", "false", "development", "production", "test", "postgres"}:
                    secrets_set.add(env_val.strip())

    # Sort longer secrets first to avoid partial substring collisions
    return sorted(secrets_set, key=len, reverse=True)


# Generic regex patterns for credentials
_GENERIC_SECRET_PATTERNS = (
    # JWT Tokens
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # Private Key blocks
    re.compile(r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]+)?PRIVATE KEY-----"),
    # General API keys (sk-..., sk_..., secret-..., token-...)
    re.compile(r"\b(?:sk|secret|token|api)[-_][a-zA-Z0-9_\-]{16,}\b"),
)


def scrub_secrets(
    text: Optional[str],
    additional_secrets: Optional[Sequence[str]] = None,
) -> str:
    """Scrub known and pattern-matched secrets from any response or log string."""
    if not text:
        return ""

    scrubbed = str(text)

    # 1. Scrub exact known secrets
    known = _gather_known_secrets()
    if additional_secrets:
        known.extend(s for s in additional_secrets if s and len(s) >= 4)
        known = sorted(set(known), key=len, reverse=True)

    for sec in known:
        if sec in scrubbed:
            scrubbed = scrubbed.replace(sec, "[REDACTED_SECRET]")

    # 2. Scrub regex patterns
    # Database URL passwords specifically
    scrubbed = re.sub(
        r"((?:postgres|postgresql|mysql)(?:\+[a-z0-9]+)?:\/\/[^:]+:)([^@]+)(@)",
        r"\1[REDACTED_PASSWORD]\3",
        scrubbed,
    )

    # JWTs, private keys, API key patterns
    for pat in _GENERIC_SECRET_PATTERNS:
        scrubbed = pat.sub("[REDACTED_SECRET]", scrubbed)

    return scrubbed


# --------------------------------------------------------------------------- #
# Tool Execution Allowlist (Zero Code Execution & Zero Shell Evaluation)
# --------------------------------------------------------------------------- #
def validate_tool_call(
    tool_name: str,
    params: Optional[dict[str, Any]] = None,
) -> bool:
    """Validate that a tool call is in the strict allowlist and contains NO code/shell payloads.

    Raises:
        UnauthorizedToolError: If tool_name is not in ALLOWED_TOOLS.
        SecurityViolationError: If tool name or parameters contain code or shell evaluation patterns.
    """
    clean_tool = (tool_name or "").strip()

    # 1. Check for dangerous command / shell / eval injection in tool name
    for pat in FORBIDDEN_EXECUTION_PATTERNS:
        if pat.search(clean_tool):
            logger.warning("Blocked dangerous execution attempt in tool name: %s", clean_tool)
            raise SecurityViolationError(
                f"Security violation: Code/shell evaluation is forbidden. Attempted: '{clean_tool}'"
            )

    # 2. Allowlist verification
    if clean_tool not in ALLOWED_TOOLS:
        logger.warning("Rejected unauthorized tool call: %s", clean_tool)
        raise UnauthorizedToolError(
            f"Tool '{clean_tool}' is not in the allowlist. Zero code execution permitted."
        )

    # 3. Check parameters for forbidden shell / eval payloads
    if params:
        for key, val in params.items():
            val_str = str(val)
            for pat in FORBIDDEN_EXECUTION_PATTERNS:
                if pat.search(val_str):
                    logger.warning("Blocked dangerous execution payload in parameter '%s': %s", key, val_str)
                    raise SecurityViolationError(
                        f"Security violation: Code/shell evaluation in parameter '{key}' is forbidden."
                    )

    return True


def execute_allowed_tool(
    tool_name: str,
    params: Optional[dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    """Execute an allowed, safe informational tool.

    STRICT GUARANTEE: Zero code execution, zero shell evaluation, pure read-only data lookup.
    """
    # 1. Enforce strict allowlist and security checks
    validate_tool_call(tool_name, params)

    params = params or {}
    clean_tool = tool_name.strip()

    # 2. Dispatch to pure read-only deterministic logic
    if clean_tool == "open_entity":
        entity_id = params.get("entity_id") or params.get("id")
        slug = params.get("slug")
        if db is not None:
            from ..models import HistoricalEntity
            stmt = select(HistoricalEntity)
            if entity_id:
                try:
                    stmt = stmt.where(HistoricalEntity.id == UUID(str(entity_id)))
                except (ValueError, TypeError):
                    stmt = stmt.where(HistoricalEntity.slug == str(entity_id))
            elif slug:
                stmt = stmt.where(HistoricalEntity.slug == str(slug))
            else:
                return {"status": "error", "message": "Missing entity_id or slug."}
            entity = db.scalar(stmt)
            if not entity:
                return {"status": "not_found", "entity": None}
            return {
                "status": "success",
                "tool": "open_entity",
                "entity": {
                    "id": str(entity.id),
                    "name_vi": entity.name_vi,
                    "name_en": entity.name_en,
                    "slug": entity.slug,
                    "entity_type": entity.entity_type,
                    "summary_vi": entity.summary_vi,
                },
            }
        return {
            "status": "success",
            "tool": "open_entity",
            "entity": {"id": str(entity_id or slug), "slug": str(slug or entity_id)},
        }

    elif clean_tool == "view_source":
        source_id = params.get("source_id") or params.get("id")
        if not source_id:
            return {"status": "error", "message": "Missing source_id."}
        if db is not None:
            from ..models import HistoricalSource
            try:
                src_uuid = UUID(str(source_id))
                src = db.get(HistoricalSource, src_uuid)
            except (ValueError, TypeError):
                src = None
            if not src:
                return {"status": "not_found", "source": None}
            return {
                "status": "success",
                "tool": "view_source",
                "source": {
                    "id": str(src.id),
                    "title": src.title,
                    "author_text": src.author_text,
                    "publication_year": src.publication_year,
                    "source_type": src.source_type,
                    "verification_status": src.verification_status,
                },
            }
        return {
            "status": "success",
            "tool": "view_source",
            "source": {"id": str(source_id)},
        }

    elif clean_tool == "search_claims":
        query = sanitize_untrusted_text(str(params.get("query") or ""))
        limit = min(int(params.get("limit") or 10), 20)
        return {
            "status": "success",
            "tool": "search_claims",
            "query": query,
            "limit": limit,
            "claims": [],
        }

    elif clean_tool == "get_epistemic_status":
        status_key = str(params.get("status") or "")
        return {
            "status": "success",
            "tool": "get_epistemic_status",
            "status_key": status_key,
            "description": "Epistemic verification state indicator.",
        }

    elif clean_tool == "suggest_followup":
        topic = sanitize_untrusted_text(str(params.get("topic") or ""))
        return {
            "status": "success",
            "tool": "suggest_followup",
            "suggestions": [
                f"Tìm hiểu thêm về bối cảnh lịch sử của {topic}",
                f"Các nguồn tư liệu mộc bản và châu bản ghi chép gì về {topic}?",
            ],
        }

    raise UnauthorizedToolError(f"Unhandled tool: {clean_tool}")
