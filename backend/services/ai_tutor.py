"""
AI Tutor Service for Luuniensuki LMS.

This module provides AI-powered tutoring functionality with:
- Conversation management
- Context-aware responses using RAG
- Content safety filtering
- Token usage tracking
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    AIConversation,
    AIMessage,
    ContentRating,
    LessonContent,
    Motif,
    RagDocument,
    RagSettings,
    User,
)
from .ai_privacy import (
    calculate_retention_due_at,
    has_guardian_consent,
    is_minor_user,
    is_training_allowed_for_user,
    sanitize_prompt_pii,
    validate_minor_prompt_safety,
)

logger = logging.getLogger(__name__)

_SAFETY_REPLACEMENT = "[nội dung đã được ẩn vì lý do an toàn]"
_SAFETY_FALLBACK_MESSAGE = (
    "Mình đã ẩn một phần nội dung vì lý do an toàn lứa tuổi. "
    "Hãy thử đặt câu hỏi học tập cụ thể hơn."
)
_UNDERAGE_BLOCK_PATTERNS = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in [
        r"\b(?:sex|sexual|porn|nsfw|nude|naked|xxx|rape)\b",
        r"\b(?:kill|murder|suicide|self[-\s]?harm|bomb|weapon|terror)\b",
        r"\b(?:meth|cocaine|heroin|drug\s*recipe)\b",
        r"\b(?:tự\s*tử|giết|giết\s*người|khiêu\s*dâm|hiếp\s*dâm|ma\s*túy|bom|vũ\s*khí)\b",
    ]
]


def get_user_conversations(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = True,
) -> tuple[list[AIConversation], int]:
    """
    Get user's conversations with pagination.

    Args:
        db: Database session
        user: User object
        page: Page number (1-indexed)
        page_size: Number of items per page
        active_only: Only return active conversations

    Returns:
        Tuple of (conversations, total_count)
    """
    query = select(AIConversation).where(AIConversation.user_id == user.id)

    if active_only:
        query = query.where(AIConversation.is_active == True)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    # Get paginated results
    query = (
        query.order_by(AIConversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    conversations = db.execute(query).scalars().all()
    return list(conversations), total


def create_conversation(
    db: Session,
    user: User,
    title: Optional[str] = None,
    context_type: Optional[str] = None,
    context_id: Optional[UUID] = None,
) -> AIConversation:
    """
    Create a new AI conversation.

    Args:
        db: Database session
        user: User object
        title: Optional conversation title
        context_type: Optional context type (lesson, motif, quest, general)
        context_id: Optional ID of related content

    Returns:
        Created conversation
    """
    is_minor = is_minor_user(user)
    retention_due = calculate_retention_due_at(user)
    guardian_consent_granted = has_guardian_consent(db, user)

    conversation = AIConversation(
        user_id=user.id,
        title=title,
        context_type=context_type,
        context_id=context_id,
        is_minor=is_minor,
        retention_due_at=retention_due,
        guardian_consent_granted=guardian_consent_granted,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(
    db: Session,
    conversation_id: UUID,
    user: User,
) -> Optional[AIConversation]:
    """
    Get a conversation by ID for a specific user.

    Args:
        db: Database session
        conversation_id: Conversation ID
        user: User object

    Returns:
        Conversation or None if not found
    """
    conversation = db.execute(
        select(AIConversation)
        .options(selectinload(AIConversation.messages))
        .where(
            and_(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    return conversation


def delete_conversation(
    db: Session,
    conversation_id: UUID,
    user: User,
) -> bool:
    """
    Delete a conversation.

    Args:
        db: Database session
        conversation_id: Conversation ID
        user: User object

    Returns:
        True if deleted, False if not found
    """
    conversation = get_conversation(db, conversation_id, user)
    if not conversation:
        return False

    db.delete(conversation)
    db.commit()
    return True



def send_message(
    db: Session,
    conversation: AIConversation,
    user: User,
    message_content: str,
    deepseek_chat_func,  # Function to call DeepSeek API
    collect_sources_func,  # Function to collect RAG sources
    get_rag_settings_func,  # Function to get RAG settings
) -> tuple[AIMessage, AIMessage]:
    """
    Send a message in a conversation and get AI response.

    Args:
        db: Database session
        conversation: Conversation object
        user: User object
        message_content: User's message
        deepseek_chat_func: Function to call DeepSeek chat API
        collect_sources_func: Function to collect RAG sources
        get_rag_settings_func: Function to get RAG settings

    Returns:
        Tuple of (user_message, ai_response)
    """
    # 1. Age-appropriate content safety check for minors
    is_safe, safety_feedback = validate_minor_prompt_safety(message_content, user)

    # 2. PII Sanitization for student personal data (phone, email, school address)
    sanitized_content, pii_counts = sanitize_prompt_pii(message_content)
    has_pii = any(c > 0 for c in pii_counts.values())

    # 3. Training eligibility determination
    training_allowed = is_training_allowed_for_user(db, user)

    # Create user message with sanitized content
    user_message = AIMessage(
        conversation_id=conversation.id,
        role="user",
        content=sanitized_content,
        training_allowed=training_allowed,
        pii_redacted=has_pii,
    )
    db.add(user_message)

    # If minor prompt was unsafe, block external AI call and return educational guidance
    if not is_safe:
        ai_response_content = safety_feedback or _SAFETY_FALLBACK_MESSAGE
        ai_message = AIMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response_content,
            training_allowed=False,
            pii_redacted=False,
        )
        db.add(ai_message)

        conversation.message_count += 2
        conversation.updated_at = datetime.now(timezone.utc)
        if not conversation.title and conversation.message_count == 2:
            conversation.title = _generate_title_from_message(sanitized_content)

        db.commit()
        db.refresh(user_message)
        db.refresh(ai_message)
        return user_message, ai_message

    # Get context sources for RAG using sanitized content
    sources = []
    if conversation.context_type and conversation.context_id:
        if conversation.context_type == "motif":
            sources = collect_sources_func(
                db,
                motif_id=conversation.context_id,
                limit=6,
                query=sanitized_content,
            )
        # Add other context types as needed
    else:
        sources = collect_sources_func(
            db,
            limit=6,
            query=sanitized_content,
        )

    # Build conversation history (last 10 messages)
    messages_history = db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation.id)
        .order_by(AIMessage.created_at.desc())
        .limit(10)
    ).scalars().all()

    messages_history = list(reversed(messages_history))

    # Build prompt
    system_prompt = _build_system_prompt(conversation, sources)
    chat_messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in messages_history:
        if msg.role in ["user", "assistant"]:
            chat_messages.append({"role": msg.role, "content": msg.content})

    # Add current message (sanitized)
    chat_messages.append({"role": "user", "content": sanitized_content})

    # Get RAG settings
    rag_settings = get_rag_settings_func(db)
    temperature = float(rag_settings.temperature or 0.7)
    model_override = rag_settings.model_override

    # Call AI with sanitized prompt
    try:
        ai_response_content = deepseek_chat_func(
            chat_messages,
            temperature=temperature,
            model=model_override,
        )
    except Exception as e:
        logger.error(f"Error calling DeepSeek API: {e}")
        ai_response_content = (
            "Xin lỗi, tôi đang gặp vấn đề kỹ thuật. Vui lòng thử lại sau."
        )

    ai_response_content = apply_content_safety_filter(ai_response_content, user)

    from . import ai_observability
    prompt_tokens = ai_observability.estimate_tokens(message_content)
    completion_tokens = ai_observability.estimate_tokens(ai_response_content)

    user_message.tokens_used = prompt_tokens

    # Create AI message
    ai_message = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_response_content,
        tokens_used=prompt_tokens + completion_tokens,
        training_allowed=training_allowed,
        pii_redacted=False,
    )
    db.add(ai_message)

    # Update conversation
    conversation.message_count += 2
    conversation.updated_at = datetime.now(timezone.utc)

    # Auto-generate title from first message if not set
    if not conversation.title and conversation.message_count == 2:
        conversation.title = _generate_title_from_message(sanitized_content)

    ai_observability.record_ai_telemetry(
        db,
        user_id=user.id,
        operation="conversation_message",
        model=model_override or "deepseek",
        provider="deepseek",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=0.0,
        citation_valid_count=len(sources),
        citation_invalid_count=0,
        status="success",
        prompt_text=message_content,
    )

    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)

    return user_message, ai_message


def _build_system_prompt(
    conversation: AIConversation,
    sources: list[dict[str, Any]],
) -> str:
    """Build system prompt with context."""
    base_prompt = (
        "Bạn là AI Tutor cho nền tảng học tập di sản Lưu Niên Sử Kí (Cửu Đỉnh).\n\n"
        "Mục tiêu:\n"
        "- Giúp người học hiểu đúng về lịch sử, biểu tượng và nghệ thuật của Cửu Đỉnh.\n"
        "- Trả lời rõ ràng, có cấu trúc, dễ học.\n\n"
        "Quy tắc bắt buộc:\n"
        "1) Chỉ dùng dữ liệu trong ngữ cảnh được cung cấp.\n"
        "2) Nếu chưa đủ dữ kiện, nói rõ giới hạn và đề xuất câu hỏi làm rõ.\n"
        "3) Ưu tiên cách dẫn dắt gợi mở (hint-first), không trả lời lan man.\n"
        "4) Dùng tiếng Việt tự nhiên, tránh thuật ngữ khó nếu không cần.\n"
    )

    if sources:
        sources_text = "\n\nNgữ cảnh nguồn:\n"
        for i, source in enumerate(sources, 1):
            sources_text += f"\n[{i}] {source.get('title', 'N/A')}\n{source.get('content', '')}\n"
        base_prompt += sources_text

    if conversation.context_type:
        base_prompt += f"\n\nNgữ cảnh phiên học: {conversation.context_type}"

    return base_prompt


def _generate_title_from_message(message: str) -> str:
    """Generate a short title from the first message."""
    # Remove extra whitespace
    message = re.sub(r'\s+', ' ', message.strip())

    # Take first 50 characters
    if len(message) > 50:
        title = message[:47] + "..."
    else:
        title = message

    return title


def apply_content_safety_filter(content: str, user: User) -> str:
    """
    Apply content safety filters based on user age.

    Args:
        content: Content to filter
        user: User object

    Returns:
        Filtered content
    """
    if not content:
        return content

    # Unverified users receive a stricter keyword-based sanitizer.
    # This keeps the response usable while masking high-risk terms.
    is_age_verified = bool(getattr(user, "age_verified", False))
    if is_age_verified:
        return content

    sanitized = content
    total_hits = 0
    for pattern in _UNDERAGE_BLOCK_PATTERNS:
        sanitized, hit_count = pattern.subn(_SAFETY_REPLACEMENT, sanitized)
        total_hits += hit_count

    if total_hits == 0:
        return content

    # Collapse repeated markers into one to keep the answer readable.
    marker_pattern = rf"(?:\s*{re.escape(_SAFETY_REPLACEMENT)}\s*){{2,}}"
    sanitized = re.sub(marker_pattern, f" {_SAFETY_REPLACEMENT} ", sanitized).strip()

    # If too much of the text is unsafe, return a concise safe fallback.
    min_reasonable_len = max(40, int(len(content) * 0.35))
    if total_hits >= 3 or len(sanitized) < min_reasonable_len:
        return _SAFETY_FALLBACK_MESSAGE

    return sanitized
