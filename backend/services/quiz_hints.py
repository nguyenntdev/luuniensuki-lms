"""
Quiz Hints Service for generating context-aware hints using AI + RAG.

This service handles:
- Generating different types of hints (explain, clue, elimination)
- Using RAG to provide context-aware hints
- Tracking hint usage per question
- Managing heart costs for hints
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from ..models import (
    QuizQuestion,
    QuizHintRequest,
    User,
    Motif,
    HintType,
    HeartTransactionReason,
)
from .hearts import use_heart, has_hearts, get_or_create_user_hearts


# Hint costs in hearts
HINT_COSTS = {
    HintType.explain: 0,  # Free educational content
    HintType.clue: 1,  # Subtle hint
    HintType.elimination: 2,  # Remove wrong answer
}


def get_hint_cost(hint_type: HintType) -> int:
    """Get the heart cost for a hint type."""
    return HINT_COSTS.get(hint_type, 0)


def can_request_hint(
    db: Session,
    user: User,
    question_id: UUID,
    hint_type: HintType,
) -> tuple[bool, str]:
    """
    Check if user can request a hint.
    
    Args:
        db: Database session
        user: The user requesting the hint
        question_id: Quiz question ID
        hint_type: Type of hint being requested
        
    Returns:
        Tuple of (can_request, reason_if_not)
    """
    # Check if question exists
    question = db.get(QuizQuestion, question_id)
    if not question:
        return False, "Question not found"
    
    # Get hint cost
    cost = get_hint_cost(hint_type)
    
    # Check if user has enough hearts
    now = datetime.now(timezone.utc)
    user_hearts = get_or_create_user_hearts(db, user)
    
    # Check unlimited hearts
    if user_hearts.unlimited_until and now < user_hearts.unlimited_until:
        return True, ""
    
    # Check current hearts
    if cost > 0 and user_hearts.current_hearts < cost:
        return False, f"Not enough hearts. Need {cost}, have {user_hearts.current_hearts}"
    
    # Check if user has already used this hint type for this question
    existing_hint = db.execute(
        select(QuizHintRequest)
        .where(
            QuizHintRequest.user_id == user.id,
            QuizHintRequest.question_id == question_id,
            QuizHintRequest.hint_type == hint_type.value,
        )
    ).scalar_one_or_none()
    
    if existing_hint:
        return False, "You have already used this hint type for this question"
    
    return True, ""


def get_question_hints(
    db: Session,
    user: User,
    question_id: UUID,
) -> list[QuizHintRequest]:
    """
    Get all hints the user has requested for a question.
    
    Args:
        db: Database session
        user: The user
        question_id: Quiz question ID
        
    Returns:
        List of hint requests
    """
    hints = db.execute(
        select(QuizHintRequest)
        .where(
            QuizHintRequest.user_id == user.id,
            QuizHintRequest.question_id == question_id,
        )
        .order_by(QuizHintRequest.created_at.asc())
    ).scalars().all()
    
    return list(hints)


def count_user_hints(
    db: Session,
    user: User,
    question_id: Optional[UUID] = None,
) -> int:
    """
    Count how many hints a user has requested.
    
    Args:
        db: Database session
        user: The user
        question_id: Optional question ID to filter by
        
    Returns:
        Number of hints requested
    """
    query = select(func.count(QuizHintRequest.id)).where(
        QuizHintRequest.user_id == user.id
    )
    
    if question_id:
        query = query.where(QuizHintRequest.question_id == question_id)
    
    count = db.execute(query).scalar_one()
    return count


def generate_hint_with_ai(
    db: Session,
    question: QuizQuestion,
    hint_type: HintType,
    rag_sources: list[dict[str, Any]],
    call_deepseek_fn,
) -> str:
    """
    Generate a hint using AI based on question and context.

    Args:
        db: Database session
        question: The quiz question
        hint_type: Type of hint to generate
        rag_sources: RAG sources for context
        call_deepseek_fn: Function to call DeepSeek API

    Returns:
        Generated hint text
    """
    # Build context from RAG sources
    context_parts = []
    for idx, source in enumerate(rag_sources[:5], 1):  # Use top 5 sources
        title = source.get("title", "")
        content = source.get("content", "")
        if content:
            context_parts.append(f"[{idx}] {title}\n{content}")

    context = "\n\n".join(context_parts) if context_parts else "Không có thông tin bổ sung."

    # Build prompt based on hint type
    if hint_type == HintType.explain:
        system_prompt = (
            "Bạn là trợ lý giáo dục giúp học sinh hiểu các khái niệm về họa tiết Cửu Đỉnh. "
            "Nhiệm vụ của bạn là giải thích khái niệm liên quan đến câu hỏi mà KHÔNG đưa ra đáp án. "
            "Hãy giúp học sinh hiểu sâu hơn về chủ đề."
        )
        user_prompt = f"""Dựa vào ngữ cảnh sau:

{context}

Hãy giải thích khái niệm liên quan đến câu hỏi này (KHÔNG đưa ra đáp án):

Câu hỏi: {question.question_text}

Hãy viết một đoạn giải thích ngắn gọn (2-3 câu) giúp học sinh hiểu rõ khái niệm."""

    elif hint_type == HintType.clue:
        system_prompt = (
            "Bạn là trợ lý giáo dục giúp học sinh với gợi ý tinh tế. "
            "Đưa ra gợi ý dẫn dắt về hướng đáp án đúng nhưng KHÔNG nói trực tiếp đáp án."
        )
        user_prompt = f"""Dựa vào ngữ cảnh sau:

{context}

Câu hỏi: {question.question_text}
Đáp án đúng: {question.correct_answer}

Hãy đưa ra một gợi ý tinh tế (1-2 câu) giúp học sinh suy nghĩ về đáp án đúng mà không nói trực tiếp."""

    else:  # elimination
        # For elimination, we don't need AI, we'll handle it differently
        return "Một đáp án sai đã được loại bỏ."

    # Call AI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        hint_text = call_deepseek_fn(messages, temperature=0.7)
        return hint_text.strip()
    except Exception as e:
        # Fallback hint if AI fails
        if hint_type == HintType.explain:
            return "Hãy xem lại bài học về chủ đề này để hiểu rõ hơn."
        else:  # clue
            return "Hãy suy nghĩ kỹ về ý nghĩa và bối cảnh của câu hỏi."


def eliminate_wrong_answer(
    question: QuizQuestion,
    previous_hints: list[QuizHintRequest],
) -> tuple[str, list[str]]:
    """
    Eliminate one wrong answer from the options.

    Args:
        question: The quiz question
        previous_hints: Previous hints for this question

    Returns:
        Tuple of (hint_text, eliminated_options)
    """
    import json

    # Parse options
    if isinstance(question.options, str):
        try:
            options = json.loads(question.options)
        except:
            options = []
    else:
        options = question.options or []

    if not options:
        return "Không thể loại bỏ đáp án cho câu hỏi này.", []

    # Get previously eliminated options
    eliminated = []
    for hint in previous_hints:
        if hint.hint_type == HintType.elimination.value and hint.rag_sources:
            prev_eliminated = hint.rag_sources.get("eliminated_options", [])
            eliminated.extend(prev_eliminated)

    # Find wrong options (not eliminated yet)
    wrong_options = [
        opt for opt in options
        if opt != question.correct_answer and opt not in eliminated
    ]

    if not wrong_options:
        return "Không còn đáp án sai nào để loại bỏ.", eliminated

    # Eliminate the first wrong option
    to_eliminate = wrong_options[0]
    eliminated.append(to_eliminate)

    hint_text = f"Đáp án '{to_eliminate}' đã được loại bỏ vì không đúng."

    return hint_text, eliminated


def create_hint_request(
    db: Session,
    user: User,
    question_id: UUID,
    hint_type: HintType,
    collect_ai_sources_fn,
    call_deepseek_fn,
) -> QuizHintRequest:
    """
    Create a hint request with AI-generated hint.

    Args:
        db: Database session
        user: The user requesting the hint
        question_id: Quiz question ID
        hint_type: Type of hint requested
        collect_ai_sources_fn: Function to collect RAG sources
        call_deepseek_fn: Function to call DeepSeek API

    Returns:
        Created QuizHintRequest

    Raises:
        ValueError: If hint cannot be created
        RuntimeError: If heart deduction fails
    """
    now = datetime.now(timezone.utc)

    # Check if hint can be requested
    can_request, reason = can_request_hint(db, user, question_id, hint_type)
    if not can_request:
        raise ValueError(reason)

    # Get question with motif
    question = db.execute(
        select(QuizQuestion)
        .options(selectinload(QuizQuestion.motif))
        .where(QuizQuestion.id == question_id)
    ).scalar_one_or_none()

    if not question:
        raise ValueError("Question not found")

    # Get previous hints for this question
    previous_hints = get_question_hints(db, user, question_id)

    # Collect RAG sources for context
    rag_sources = collect_ai_sources_fn(
        db,
        motif_id=question.motif_id,
        query=question.question_text,
        limit=6,
    )

    # Generate hint based on type
    if hint_type == HintType.elimination:
        hint_text, eliminated_options = eliminate_wrong_answer(question, previous_hints)
        # Store eliminated options in rag_sources field
        rag_sources_data = {
            "eliminated_options": eliminated_options,
            "sources": [{"type": s.get("type"), "id": s.get("id"), "title": s.get("title")} for s in rag_sources[:3]],
        }
    else:
        hint_text = generate_hint_with_ai(
            db, question, hint_type, rag_sources, call_deepseek_fn
        )
        # Store RAG sources metadata
        rag_sources_data = [
            {
                "type": s.get("type"),
                "id": s.get("id"),
                "title": s.get("title"),
                "content": s.get("content", "")[:200],  # Store first 200 chars
            }
            for s in rag_sources[:5]
        ]

    # Get hint cost
    cost = get_hint_cost(hint_type)

    # Deduct hearts if needed
    if cost > 0:
        success, user_hearts = use_heart(
            db,
            user,
            now,
            reason=HeartTransactionReason.quiz_hint,
            metadata={"question_id": str(question_id), "hint_type": hint_type.value},
        )
        if not success:
            raise RuntimeError("Failed to deduct hearts")

    # Create hint request
    hint_request = QuizHintRequest(
        user_id=user.id,
        question_id=question_id,
        hint_type=hint_type.value,
        hint_text=hint_text,
        heart_cost=cost,
        rag_sources=rag_sources_data,
    )

    db.add(hint_request)
    db.commit()
    db.refresh(hint_request)

    return hint_request



