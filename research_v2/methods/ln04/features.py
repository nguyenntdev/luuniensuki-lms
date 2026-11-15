"""Shared LN-04 inference helpers.

Pure deterministic feature extraction from ``StudyInput.features`` (the masked
inference-time payload). No oracle, gold, or fault material is read here.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .labels import VERIFIED_SOURCE_STATUSES

# ---------------------------------------------------------------
# Answer-request (leakage-seeking) patterns — VN + EN
# ---------------------------------------------------------------
ANSWER_REQUEST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:viết|cho|xin|tiết\s+lộ|cung\s+cấp)\s+(?:đáp\s+án|lời\s+giải|kết\s+quả)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:give\s+me|tell\s+me|show\s+me|reveal)\s+(?:the\s+)?(?:full\s+)?"
        r"(?:answer|solution|result)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:chép\s+đáp\s+án|làm\s+hộ\s+em|giải\s+hộ\s+em|viết\s+giúp\s+em|"
        r"viết\s+hộ\s+em|xin\s+đáp\s+án|viết\s+đáp\s+án|cho\s+em\s+đáp\s+án|"
        r"viết\s+ra\s+đáp\s+án|đáp\s+án\s+đầy\s+đủ|"
        r"đáp\s+án\s+hoàn\s+chỉnh|lời\s+giải\s+đầy\s+đủ|lời\s+giải\s+trọn\s+vẹn|"
        r"kết\s+quả\s+trọn\s+vẹn|xin\s+kết\s+quả|cho\s+em\s+kết\s+quả)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:cheat|copy\s+(?:into|for)|to\s+submit)\b", re.IGNORECASE),
)

# ---------------------------------------------------------------
# Prompt-injection / instruction-override / jailbreak patterns
# ---------------------------------------------------------------
INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    # VN rule-override
    re.compile(
        r"\b(?:bỏ\s+qua|quên|ghi\s+đè)\s+(?:mọi|toàn\s+bộ|các)?\s*"
        r"(?:quy\s+tắc|chỉ\s+dẫn|hướng\s+dẫn|lệnh|chỉ\s+thị|giới\s+hạn\s+bảo\s+mật|"
        r"quy\s+định\s+sư\s+phạm|quy\s+tắc\s+kiểm\s+duyệt)\b",
        re.IGNORECASE,
    ),
    # EN rule-override
    re.compile(
        r"\b(?:ignore|disregard|bypass|override|forget)\s+(?:all\s+|any\s+|the\s+|"
        r"previous\s+|prior\s+|your\s+)?(?:rules|instructions|directives|system|"
        r"pedagogical|safety|guardrails|constraints|filters)\b",
        re.IGNORECASE,
    ),
    # pedagogical-boundary dismissals ("no need to follow pedagogy rules")
    re.compile(
        r"\b(?:không\s+cần\s+tuân\s+thủ|không\s+tuân\s+thủ)\s+(?:mọi\s+|các\s+|"
        r"quy\s+định\s+|quy\s+tắc\s+|giới\s+hạn\s+)?(?:sư\s+phạm|quy\s+định|quy\s+tắc)\b",
        re.IGNORECASE,
    ),
    # source-irrelevance claims
    re.compile(
        r"\b(?:nội\s+dung\s+nguồn\s+không\s+quan\s+trọng|source\s+does\s+not\s+matter|"
        r"source\s+doesn't\s+matter|không\s+cần\s+gợi\s+mở\s+gì\s+cả)\b",
        re.IGNORECASE,
    ),
    # roleplay jailbreaks
    re.compile(
        r"\b(?:act\s+as|pretend\s+(?:you\s+are|to\s+be)|đóng\s+vai|switch\s+to|"
        r"you\s+are\s+now|giả\s+lập)\s+(?:dan\b|developer\s+mode|unrestricted|"
        r"an?\s+omnipotent|root|admin|lập\s+trình\s+viên)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:do\s+anything\s+now|developer\s+mode|jailbreak|unrestricted\s+"
        r"(?:mode|roleplay|teacher|assistant))\b",
        re.IGNORECASE,
    ),
    # system/credential exfiltration
    re.compile(
        r"\b(?:system\s+override|in\s+khóa\s+bí\s+mật|print\s+jwt_secret_key|"
        r"dump\s+internal\s+prompt|print\s+system\s+prompt|dump\s+the\s+answer|"
        r"leak\s+the\s+solution|tắt\s+bộ\s+lọc\s+gợi\s+ý|in\s+khóa\s+secret|"
        r"khóa\s+bí\s+mật\s+hệ\s+thống|in\s+file\s+kết\s+quả|"
        r"quên\s+đi\s+vai\s+trò|xuất\s+trực\s+tiếp\s+file)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:jwt_secret|secret_key|api_key|system\s+prompt)\b", re.IGNORECASE),
    # exam/assessment dump requests framed as overrides
    re.compile(
        r"\b(?:xuất\s+toàn\s+bộ|reveal\s+the\s+full\s+solution\s+key|"
        r"giải\s+đáp\s+trọn\s+vẹn|lời\s+giải\s+chi\s+tiết\s+của\s+bài\s+(?:kiểm|thi))\b",
        re.IGNORECASE,
    ),
)

# Markers that retrieved-note text itself carries injection payload. A note
# containing these must never be treated as a trustworthy answer channel.
NOTE_INJECTION_MARKERS: tuple[re.Pattern[str], ...] = INJECTION_PATTERNS


def first_match(patterns: tuple[re.Pattern[str], ...], text: str) -> str | None:
    """Return the matched substring of the first matching pattern, else None."""
    if not text:
        return None
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def get_question(features: Mapping[str, Any]) -> str:
    return str(features.get("question", "") or "")


def get_retrieval(features: Mapping[str, Any]) -> dict[str, Any]:
    retrieval = dict(_as_mapping(features.get("retrieval")))
    notes = features.get("retrieved_notes")
    if isinstance(notes, list):
        retrieval.setdefault("notes", notes)
    return retrieval


def get_task(features: Mapping[str, Any]) -> dict[str, Any]:
    return dict(_as_mapping(features.get("task")))


def get_learner(features: Mapping[str, Any]) -> dict[str, Any]:
    return dict(_as_mapping(features.get("learner")))


def source_is_verified(retrieval: Mapping[str, Any]) -> bool:
    """Fail-closed source gate: verified only with explicit verified status."""
    source_ids = retrieval.get("source_ids")
    has_ids = bool(source_ids) if isinstance(source_ids, list) else bool(source_ids)
    status = str(retrieval.get("source_status", "unverified") or "unverified")
    return has_ids and status in VERIFIED_SOURCE_STATUSES


def answer_release_allowed(task: Mapping[str, Any]) -> bool:
    return bool(task.get("answer_release_allowed", False))


def question_requests_answer(question: str) -> bool:
    return first_match(ANSWER_REQUEST_PATTERNS, question) is not None


def question_is_injection(question: str) -> bool:
    return first_match(INJECTION_PATTERNS, question) is not None


def note_is_malicious(note_text: str) -> bool:
    """A retrieved note carrying instruction-override payload is untrusted."""
    return first_match(NOTE_INJECTION_MARKERS, note_text) is not None


def hint_level_of(task: Mapping[str, Any]) -> int:
    raw = task.get("hint_level", 1)
    try:
        return max(1, min(3, int(raw)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 1
