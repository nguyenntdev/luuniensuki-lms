# -*- coding: utf-8 -*-
"""AI Privacy, Child Protections & Zero-Training Compliance Service.

Enforces COPPA, Vietnam Decree 13/2023/ND-CP, and educational AI privacy invariants:
1. PII Sanitization: Pre-invocation redaction of student phone numbers, email addresses,
   and school/physical addresses before sending to external AI models or persisting logs.
2. Age-Appropriate Content Filters: Inbound and outbound content filters blocking self-harm,
   weapons, illicit drugs, adult/NSFW, and violence for minor students.
3. Zero-Training Policy: Prohibits AI model training on minor student messages without
   explicit, verified guardian consent.
4. Minimal Conversation Retention: Automated lifecycle retention enforcement (30 days for minors)
   and right-to-erasure user purge capability.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from ..models import AIConversation, AIJob, AIMessage, ClassMember, User

logger = logging.getLogger("luuniensuki.ai.privacy")

# Redaction placeholders
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_PHONE = "[REDACTED_PHONE]"
REDACTED_ADDRESS = "[REDACTED_ADDRESS]"
REDACTED_STUDENT_ID = "[REDACTED_STUDENT_ID]"

DEFAULT_MINOR_RETENTION_DAYS = 30
DEFAULT_ADULT_RETENTION_DAYS = 90

MINOR_SAFETY_REJECTION_MESSAGE = (
    "Nội dung này không phù hợp với lứa tuổi học sinh. "
    "Bạn hãy đặt câu hỏi liên quan đến lịch sử và di sản văn hóa Cửu Đỉnh nhé."
)

# PII Regexes
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Supports Vietnamese and international phone formats:
# e.g. 0901234567, +84912345678, 098-765-4321, 090 123 4567, (024) 3825 1234, 0387654321
PHONE_REGEX = re.compile(
    r"(?:(?:\+84|84|0)(?:\s*[\.\-]?\s*\d){8,10}\b|\b\(?0\d{1,3}\)?[\s\.\-]?\d{3,4}[\s\.\-]?\d{3,4}\b)"
)

# Geographic and administrative tokens for Vietnamese addresses
GEO_TOKENS = (
    r"(?:số\s+\d+|\d+\s+[A-Za-zÀ-Ỹà-ỹ\s]+|đường|phố|ngõ|ngách|phường|quận|huyện|thành\s*phố|TP\.?|tỉnh|"
    r"Hà\s*Nội|Hồ\s*Chí\s*Minh|TP\.?HCM|Đà\s*Nẵng|Huế|Hải\s*Phòng|Cần\s*Thơ|"
    r"Tây\s*Hồ|Ba\s*Đình|Hoàn\s*Kiếm|Cầu\s*Giấy|Đống\s*Đa|Hai\s*Bà\s*Trưng|"
    r"Thanh\s*Xuân|Bình\s*Thạnh|Tân\s*Bình|Gò\s*Vấp|Quận\s*\d+)"
)

# School and physical address patterns
ADDRESS_PATTERNS = [
    # 1. School name with comma-separated geographic details:
    # e.g. "Trường THPT Chu Văn An, số 10 đường Thụy Khuê, Tây Hồ, Hà Nội"
    re.compile(
        rf"(?:(?:học\s+ở|tại|ở)\s+)?(?:[tT]rường\s+(?:THPT|THCS|Tiểu\s*học|tiểu\s*học|Đại\s*học|đại\s*học|Mầm\s*non|chuyên)\s+[^\n,]+)(?:,\s*(?:{GEO_TOKENS})[^\n,]*)+",
        re.IGNORECASE,
    ),
    # 2. School name with inline street/number (no comma after school name):
    # e.g. "học ở Trường THCS Nguyễn Du số 12 đường Trần Hưng Đạo"
    re.compile(
        rf"(?:(?:học\s+ở|tại|ở)\s+)?(?:[tT]rường\s+(?:THPT|THCS|Tiểu\s*học|tiểu\s*học|Đại\s*học|đại\s*học|Mầm\s*non|chuyên)\s+[^\n,]+?)\s+(?:số\s+\d+[^,\n.]*?\b(?:đường|phố|ngõ|ngách)\b[^,\n.]+)(?:,\s*(?:{GEO_TOKENS})[^\n,]*)*",
        re.IGNORECASE,
    ),
    # 3. Explicit address labels: "địa chỉ trường em là ...", "School address: ..."
    re.compile(
        r"(?:(?:địa\s*chỉ(?:\s+(?:trường|nhà|học|của\s*em|trường\s*em))?|school\s*address)\s*(?::|\s+là)\s*[^,\n.]+(?:,\s*[^,\n.]+)*)",
        re.IGNORECASE,
    ),
    # 4. Standard street address: "số 45 đường Lê Lợi, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh"
    re.compile(
        r"(?:(?:số|Số)\s+\d+[^,\n.]*?\b(?:đường|phố|ngõ|ngách|Đường|Phố)\b[^,\n.]+?(?:,\s*(?:phường|quận|thành\s*phố|TP|tỉnh|huyện|thị\s*xã)[^,\n.]+)+)",
        re.IGNORECASE,
    ),
    # 5. English format "School address: ...", "Address: ..."
    re.compile(
        r"(?:(?:School(?:\s*Address)?|Address)\s*:\s*[^,\n.]+(?:,\s*[^,\n.]+)*)",
        re.IGNORECASE,
    ),
]

# Underage block patterns for inbound student prompts
UNDERAGE_BLOCK_PATTERNS = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in [
        r"\b(?:sex|sexual|porn|nsfw|nude|naked|xxx|rape)\b",
        r"\b(?:kill|murder|suicide|self[-\s]?harm|bomb|weapon|terror)\b",
        r"\b(?:meth|cocaine|heroin|drug\s*recipe)\b",
        r"\b(?:tự\s*tử|tự\s*hại|cắt\s*tay|giết|giết\s*người|khiêu\s*dâm|hiếp\s*dâm|ma\s*túy|thuốc\s*lắc|cần\s*sa|bom|chế\s*tạo\s*bom|vũ\s*khí)\b",
    ]
]


# =============================================================================
# PII Detection and Sanitization
# =============================================================================

def contains_student_pii(text: str) -> bool:
    """Check if text contains any student PII (phone, email, or school address)."""
    if not text:
        return False
    if EMAIL_REGEX.search(text):
        return True
    if PHONE_REGEX.search(text):
        return True
    for pat in ADDRESS_PATTERNS:
        if pat.search(text):
            return True
    return False


def detect_prompt_pii(text: str) -> dict[str, list[str]]:
    """Scan text for student PII and return categorized matches."""
    if not text:
        return {"email": [], "phone": [], "address": []}

    emails = EMAIL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)
    addresses: list[str] = []
    for pat in ADDRESS_PATTERNS:
        matches = pat.findall(text)
        for m in matches:
            if isinstance(m, str):
                addresses.append(m)
            elif isinstance(m, tuple) and m[0]:
                addresses.append(m[0])

    return {
        "email": emails,
        "phone": phones,
        "address": addresses,
    }


def sanitize_prompt_pii(text: str) -> tuple[str, dict[str, int]]:
    """Redact student personal data (phone, email, school address) from prompt.

    Guarantees:
    - Emails replaced with [REDACTED_EMAIL]
    - Phone numbers replaced with [REDACTED_PHONE]
    - School and street addresses replaced with [REDACTED_ADDRESS]
    - Returns sanitized text and count dictionary of redactions performed.
    """
    if not text:
        return text, {"email": 0, "phone": 0, "address": 0}

    counts = {"email": 0, "phone": 0, "address": 0}
    sanitized = text

    # 1. Redact addresses first to prevent numbers inside addresses matching phone regex
    for pat in ADDRESS_PATTERNS:
        sanitized, hit_count = pat.subn(REDACTED_ADDRESS, sanitized)
        counts["address"] += hit_count

    # 2. Redact emails
    sanitized, hit_count = EMAIL_REGEX.subn(REDACTED_EMAIL, sanitized)
    counts["email"] += hit_count

    # 3. Redact phones
    sanitized, hit_count = PHONE_REGEX.subn(REDACTED_PHONE, sanitized)
    counts["phone"] += hit_count

    return sanitized, counts


# =============================================================================
# Age Verification & Content Safety
# =============================================================================

def is_minor_user(user: Optional[User]) -> bool:
    """Determine whether a user is legally a minor (<18) or unverified underage."""
    if user is None:
        return True  # Fail-safe: unauthenticated is treated as minor
    if not getattr(user, "age_verified", False):
        return True
    if user.birth_year is not None:
        current_year = datetime.now(timezone.utc).year
        return (current_year - user.birth_year) < 18
    return False


def validate_minor_prompt_safety(
    prompt: str, user: Optional[User]
) -> tuple[bool, Optional[str]]:
    """Validate inbound prompt for minors against safety guidelines.

    Returns:
        (is_safe, feedback_message)
        If unsafe, is_safe is False and feedback_message provides educational guidance.
    """
    if not prompt:
        return True, None

    if not is_minor_user(user):
        return True, None

    # Check for harmful content patterns
    for pat in UNDERAGE_BLOCK_PATTERNS:
        if pat.search(prompt):
            logger.warning("Unsafe prompt blocked for minor user: pattern match")
            return False, MINOR_SAFETY_REJECTION_MESSAGE

    return True, None


# =============================================================================
# Guardian Consent & Zero-Training Compliance
# =============================================================================

def has_guardian_consent(db: Session, user: User) -> bool:
    """Check if minor user has verified guardian consent for data processing/AI training."""
    if not is_minor_user(user):
        return True  # Adults do not require guardian consent

    # 1. Direct user-level guardian consent
    if getattr(user, "guardian_consent", False):
        return True

    # 2. Classroom-level verified guardian consent
    stmt = select(ClassMember).where(
        ClassMember.user_id == user.id,
        ClassMember.guardian_consent.is_(True),
    )
    result = db.execute(stmt).first()
    return result is not None


def is_training_allowed_for_user(db: Session, user: User) -> bool:
    """Enforce Zero-Training Policy:

    Minor student messages are NEVER eligible for AI model training
    unless verified guardian consent has been explicitly granted.
    """
    if is_minor_user(user):
        return has_guardian_consent(db, user)
    return True


def export_conversations_for_training(
    db: Session,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Export conversation messages eligible for model fine-tuning.

    Strict Invariants:
    1. Zero minor student messages without guardian consent (filtered out 100%).
    2. Zero messages with unredacted PII.
    3. Only messages flagged with training_allowed = True.
    """
    stmt = (
        select(AIMessage, AIConversation, User)
        .join(AIConversation, AIMessage.conversation_id == AIConversation.id)
        .join(User, AIConversation.user_id == User.id)
        .where(
            AIMessage.training_allowed.is_(True),
            AIConversation.is_active.is_(True),
        )
        .order_by(AIMessage.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()

    trainable_dataset: list[dict[str, Any]] = []
    for msg, conv, user in rows:
        # Extra defensive check: verify minor consent dynamically
        if is_minor_user(user) and not has_guardian_consent(db, user):
            logger.warning(
                f"Blocked training export: minor user {user.id} lacks guardian consent"
            )
            continue

        # Extra defensive check: verify no PII in content
        if contains_student_pii(msg.content):
            logger.warning(
                f"Blocked training export: PII detected in message {msg.id}"
            )
            continue

        trainable_dataset.append({
            "message_id": str(msg.id),
            "conversation_id": str(conv.id),
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "is_minor": is_minor_user(user),
            "guardian_consent": has_guardian_consent(db, user),
        })

    return trainable_dataset


# =============================================================================
# Minimal Conversation Retention & Right to Erasure
# =============================================================================

def calculate_retention_due_at(
    user: User,
    reference_time: Optional[datetime] = None,
) -> datetime:
    """Calculate the retention expiration date for a new conversation."""
    ref = reference_time or datetime.now(timezone.utc)
    days = DEFAULT_MINOR_RETENTION_DAYS if is_minor_user(user) else DEFAULT_ADULT_RETENTION_DAYS
    return ref + timedelta(days=days)


def enforce_ai_conversation_retention(
    db: Session,
    minor_retention_days: int = DEFAULT_MINOR_RETENTION_DAYS,
    adult_retention_days: int = DEFAULT_ADULT_RETENTION_DAYS,
    reference_time: Optional[datetime] = None,
) -> dict[str, int]:
    """Enforce conversation retention policy by purging expired conversations.

    - Minors: Conversations older than 30 days are automatically deleted.
    - Adults: Conversations older than 90 days are deleted if retention is enabled.
    - Cascades to all child AIMessage rows and purges associated AIJob records.
    """
    ref = reference_time or datetime.now(timezone.utc)
    minor_cutoff = ref - timedelta(days=minor_retention_days)
    adult_cutoff = ref - timedelta(days=adult_retention_days)

    # Find conversations past retention
    conv_stmt = select(AIConversation).where(
        or_(
            and_(AIConversation.is_minor.is_(True), AIConversation.updated_at < minor_cutoff),
            and_(AIConversation.is_minor.is_(False), AIConversation.updated_at < adult_cutoff),
            and_(AIConversation.retention_due_at.is_not(None), AIConversation.retention_due_at <= ref),
        )
    )
    expired_convs = db.execute(conv_stmt).scalars().all()

    conv_count = len(expired_convs)
    msg_count = 0
    job_count = 0

    if expired_convs:
        expired_ids = [c.id for c in expired_convs]
        expired_user_ids = list({c.user_id for c in expired_convs})

        # Count messages to be deleted
        msg_count_stmt = select(func.count(AIMessage.id)).where(
            AIMessage.conversation_id.in_(expired_ids)
        )
        msg_count = db.execute(msg_count_stmt).scalar() or 0

        # Delete conversations (cascade deletes messages)
        db.execute(
            delete(AIConversation).where(AIConversation.id.in_(expired_ids))
        )

        # Purge associated expired AI jobs for these users
        job_delete_stmt = (
            delete(AIJob)
            .where(
                AIJob.user_id.in_(expired_user_ids),
                AIJob.created_at < minor_cutoff,
            )
        )
        res = db.execute(job_delete_stmt)
        job_count = res.rowcount or 0

        db.commit()

    return {
        "deleted_conversations": conv_count,
        "deleted_messages": msg_count,
        "deleted_jobs": job_count,
    }


def purge_user_ai_history(db: Session, user: User) -> dict[str, int]:
    """Right to Erasure: Permanently delete all AI conversations, messages, and jobs for user."""
    # Count conversations
    convs = db.execute(
        select(AIConversation.id).where(AIConversation.user_id == user.id)
    ).scalars().all()
    conv_count = len(convs)

    msg_count = 0
    if convs:
        msg_count = db.execute(
            select(func.count(AIMessage.id)).where(AIMessage.conversation_id.in_(convs))
        ).scalar() or 0
        db.execute(
            delete(AIConversation).where(AIConversation.user_id == user.id)
        )

    # Purge AI jobs
    job_res = db.execute(
        delete(AIJob).where(AIJob.user_id == user.id)
    )
    job_count = job_res.rowcount or 0

    db.commit()

    return {
        "deleted_conversations": conv_count,
        "deleted_messages": msg_count,
        "deleted_jobs": job_count,
    }
