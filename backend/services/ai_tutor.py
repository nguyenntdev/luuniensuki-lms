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

logger = logging.getLogger(__name__)


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
    conversation = AIConversation(
        user_id=user.id,
        title=title,
        context_type=context_type,
        context_id=context_id,
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
    # Create user message
    user_message = AIMessage(
        conversation_id=conversation.id,
        role="user",
        content=message_content,
    )
    db.add(user_message)

    # Get context sources for RAG
    sources = []
    if conversation.context_type and conversation.context_id:
        if conversation.context_type == "motif":
            sources = collect_sources_func(
                db,
                motif_id=conversation.context_id,
                limit=6,
                query=message_content,
            )
        # Add other context types as needed
    else:
        sources = collect_sources_func(
            db,
            limit=6,
            query=message_content,
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

    # Add current message
    chat_messages.append({"role": "user", "content": message_content})

    # Get RAG settings
    rag_settings = get_rag_settings_func(db)
    temperature = float(rag_settings.temperature or 0.7)
    model_override = rag_settings.model_override

    # Call AI
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

    # Create AI message
    ai_message = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_response_content,
    )
    db.add(ai_message)

    # Update conversation
    conversation.message_count += 2
    conversation.updated_at = datetime.now(timezone.utc)

    # Auto-generate title from first message if not set
    if not conversation.title and conversation.message_count == 2:
        conversation.title = _generate_title_from_message(message_content)

    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)

    return user_message, ai_message


def _build_system_prompt(
    conversation: AIConversation,
    sources: list[dict[str, Any]],
) -> str:
    """Build system prompt with context."""
    base_prompt = """Bạn là trợ lý AI thông minh cho nền tảng học tập Lưu Niên Sử Kí (Cửu Đỉnh).

Nhiệm vụ của bạn:
- Giúp người học hiểu về lịch sử và văn hóa Việt Nam qua các họa tiết trên Cửu Đỉnh
- Trả lời câu hỏi dựa trên ngữ cảnh được cung cấp
- Sử dụng ngôn ngữ rõ ràng, dễ hiểu
- Khuyến khích sự tò mò và khám phá sâu hơn
- Khi không chắc chắn, hãy thừa nhận thay vì đoán mò

"""

    if sources:
        sources_text = "\n\nNgữ cảnh:\n"
        for i, source in enumerate(sources, 1):
            sources_text += f"\n[{i}] {source.get('title', 'N/A')}\n{source.get('content', '')}\n"
        base_prompt += sources_text

    if conversation.context_type:
        base_prompt += f"\n\nCuộc trò chuyện này liên quan đến: {conversation.context_type}"

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
    # For now, this is a placeholder
    # In production, you might want to:
    # - Check for inappropriate content
    # - Filter based on user age
    # - Apply custom filtering rules

    # Basic check: if user is not age-verified, apply stricter filters
    if not user.age_verified:
        # Could add content filtering logic here
        pass

    return content


