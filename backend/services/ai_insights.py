"""
AI Learning Insights Service for Cửu Đỉnh Ký.

This service generates natural language summaries of user learning progress
using DeepSeek AI integration.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..config import get_rank_for_xp
from ..models import (
    Badge,
    Motif,
    QuizAttempt,
    UnlockStatus,
    User,
    UserBadge,
    UserProgress,
    UserSession,
)


def get_user_progress_summary(db: Session, user_id: UUID) -> dict[str, Any]:
    """
    Collect comprehensive learning data for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Dictionary with user's learning metrics
    """
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    
    # Get motif stats
    total_motifs = db.execute(select(func.count(Motif.id))).scalar_one()
    
    discovered_motifs = db.execute(
        select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.status.in_([
                    UnlockStatus.discovered,
                    UnlockStatus.learned,
                    UnlockStatus.mastered,
                ])
            )
        )
    ).scalar_one()
    
    learned_motifs = db.execute(
        select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.status.in_([
                    UnlockStatus.learned,
                    UnlockStatus.mastered,
                ])
            )
        )
    ).scalar_one()
    
    mastered_motifs = db.execute(
        select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.status == UnlockStatus.mastered,
            )
        )
    ).scalar_one()
    
    # Get quiz stats
    quiz_attempts = db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.user_id == user_id
        )
    ).scalar_one()
    
    quizzes_passed = db.execute(
        select(func.count(QuizAttempt.id)).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.percentage >= 70,  # Consider 70%+ as passed
            )
        )
    ).scalar_one()
    
    avg_quiz_score = db.execute(
        select(func.avg(QuizAttempt.score)).where(
            QuizAttempt.user_id == user_id
        )
    ).scalar_one() or 0.0
    
    # Get badges
    badges = db.execute(
        select(Badge)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at.desc())
    ).scalars().all()
    
    badge_list = [{"slug": b.slug, "name": b.name} for b in badges]
    
    # Get time spent
    total_time_minutes = _calculate_time_spent(db, user_id)
    
    # Get rank
    rank_info = get_rank_for_xp(user.total_xp)
    
    # Calculate completion percentage
    completion_percent = (discovered_motifs / total_motifs * 100) if total_motifs > 0 else 0.0
    
    return {
        "user_id": str(user_id),
        "display_name": user.display_name,
        "rank": rank_info["title"],
        "total_xp": user.total_xp,
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "completion_percent": round(completion_percent, 1),
        "motifs": {
            "total": total_motifs,
            "discovered": discovered_motifs,
            "learned": learned_motifs,
            "mastered": mastered_motifs,
        },
        "quizzes": {
            "attempts": quiz_attempts,
            "passed": quizzes_passed,
            "average_score": round(avg_quiz_score, 1),
            "pass_rate": round((quizzes_passed / quiz_attempts * 100) if quiz_attempts > 0 else 0, 1),
        },
        "badges": badge_list,
        "time_spent_minutes": total_time_minutes,
    }


def _calculate_time_spent(db: Session, user_id: UUID) -> int:
    """Calculate total time spent in minutes from user sessions."""
    sessions = db.execute(
        select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.ended_at.isnot(None),
            )
        )
    ).scalars().all()

    total_minutes = 0
    for session in sessions:
        if session.ended_at and session.started_at:
            duration = session.ended_at - session.started_at
            total_minutes += int(duration.total_seconds() / 60)

    return total_minutes


def build_insights_prompt(progress: dict[str, Any], language: str = "vi") -> str:
    """
    Build prompt for AI to generate insights.

    Args:
        progress: User progress data
        language: Language code (vi, en)

    Returns:
        Formatted prompt string
    """
    if language == "vi":
        return f"""Phân tích học tập của học viên "{progress['display_name']}" và tạo bản tóm tắt chi tiết:

Thông tin học viên:
- Hạng hiện tại: {progress['rank']}
- Tổng XP: {progress['total_xp']}
- Streak hiện tại: {progress['current_streak']} ngày (Streak dài nhất: {progress['longest_streak']} ngày)
- Tiến độ hoàn thành: {progress['completion_percent']}%

Họa tiết:
- Đã khám phá: {progress['motifs']['discovered']}/{progress['motifs']['total']}
- Đã học: {progress['motifs']['learned']}/{progress['motifs']['total']}
- Đã thành thạo: {progress['motifs']['mastered']}/{progress['motifs']['total']}

Bài kiểm tra:
- Số lần làm: {progress['quizzes']['attempts']}
- Đã đạt: {progress['quizzes']['passed']}
- Điểm trung bình: {progress['quizzes']['average_score']}/100
- Tỷ lệ đạt: {progress['quizzes']['pass_rate']}%

Huy hiệu: {len(progress['badges'])} huy hiệu
Thời gian học: {progress['time_spent_minutes']} phút

Yêu cầu:
1. Viết bản tóm tắt ngắn gọn (2-3 câu) về quá trình học tập
2. Nêu 2-3 điểm mạnh nổi bật
3. Nêu 2-3 điểm cần cải thiện
4. Đề xuất 2-3 hoạt động cụ thể để tiếp tục phát triển

Trả về dưới dạng JSON với các trường: summary, strengths (mảng), weaknesses (mảng), recommendations (mảng)."""
    else:
        return f"""Analyze the learning progress of student "{progress['display_name']}" and create a detailed summary:

Student Information:
- Current Rank: {progress['rank']}
- Total XP: {progress['total_xp']}
- Current Streak: {progress['current_streak']} days (Longest: {progress['longest_streak']} days)
- Completion Progress: {progress['completion_percent']}%

Motifs:
- Discovered: {progress['motifs']['discovered']}/{progress['motifs']['total']}
- Learned: {progress['motifs']['learned']}/{progress['motifs']['total']}
- Mastered: {progress['motifs']['mastered']}/{progress['motifs']['total']}

Quizzes:
- Attempts: {progress['quizzes']['attempts']}
- Passed: {progress['quizzes']['passed']}
- Average Score: {progress['quizzes']['average_score']}/100
- Pass Rate: {progress['quizzes']['pass_rate']}%

Badges: {len(progress['badges'])} earned
Study Time: {progress['time_spent_minutes']} minutes

Requirements:
1. Write a brief summary (2-3 sentences) about the learning journey
2. List 2-3 key strengths
3. List 2-3 areas for improvement
4. Suggest 2-3 specific activities to continue development

Return as JSON with fields: summary, strengths (array), weaknesses (array), recommendations (array)."""


def extract_strengths(progress: dict[str, Any]) -> list[str]:
    """Identify user's strong areas based on data."""
    strengths = []

    if progress['current_streak'] >= 7:
        strengths.append(f"Duy trì streak {progress['current_streak']} ngày - thói quen học đều đặn")

    if progress['quizzes']['pass_rate'] >= 80:
        strengths.append(f"Tỷ lệ đạt bài kiểm tra cao ({progress['quizzes']['pass_rate']}%)")

    if progress['quizzes']['average_score'] >= 85:
        strengths.append(f"Điểm trung bình xuất sắc ({progress['quizzes']['average_score']}/100)")

    if progress['completion_percent'] >= 50:
        strengths.append(f"Đã hoàn thành {progress['completion_percent']}% nội dung")

    if len(progress['badges']) >= 5:
        strengths.append(f"Đã đạt {len(progress['badges'])} huy hiệu")

    mastery_rate = (progress['motifs']['mastered'] / progress['motifs']['discovered'] * 100) if progress['motifs']['discovered'] > 0 else 0
    if mastery_rate >= 30:
        strengths.append(f"Tỷ lệ thành thạo cao ({round(mastery_rate, 1)}%)")

    return strengths[:3]


def extract_weaknesses(progress: dict[str, Any]) -> list[str]:
    """Identify areas needing improvement."""
    weaknesses = []

    if progress['current_streak'] < 3:
        weaknesses.append("Chưa duy trì thói quen học đều đặn")

    if progress['quizzes']['pass_rate'] < 60:
        weaknesses.append(f"Tỷ lệ đạt bài kiểm tra thấp ({progress['quizzes']['pass_rate']}%)")

    if progress['quizzes']['average_score'] < 70:
        weaknesses.append(f"Điểm trung bình cần cải thiện ({progress['quizzes']['average_score']}/100)")

    if progress['completion_percent'] < 20:
        weaknesses.append("Tiến độ hoàn thành còn chậm")

    mastery_rate = (progress['motifs']['mastered'] / progress['motifs']['discovered'] * 100) if progress['motifs']['discovered'] > 0 else 0
    if mastery_rate < 20 and progress['motifs']['discovered'] > 5:
        weaknesses.append("Cần tập trung thành thạo kiến thức đã học")

    if progress['time_spent_minutes'] < 60:
        weaknesses.append("Thời gian học còn ít")

    return weaknesses[:3]


def get_recommendations(progress: dict[str, Any]) -> list[str]:
    """Get personalized recommendations based on progress."""
    recommendations = []

    if progress['current_streak'] < 7:
        recommendations.append("Cố gắng học mỗi ngày để xây dựng streak dài hơn")

    if progress['quizzes']['pass_rate'] < 70:
        recommendations.append("Ôn tập kỹ nội dung trước khi làm bài kiểm tra")

    if progress['motifs']['mastered'] < progress['motifs']['learned']:
        recommendations.append("Hoàn thành bài kiểm tra để thành thạo các họa tiết đã học")

    if progress['completion_percent'] < 50:
        recommendations.append("Khám phá thêm các họa tiết mới để mở rộng kiến thức")

    if len(progress['badges']) < 3:
        recommendations.append("Tham gia nhiệm vụ hàng ngày để nhận huy hiệu")

    recommendations.append("Duy trì thói quen học đều đặn mỗi ngày")

    return recommendations[:3]


async def generate_learning_insights(
    db: Session,
    user_id: UUID,
    language: str = "vi",
    call_deepseek_fn=None,
) -> dict[str, Any]:
    """
    Generate natural language learning insights for a user.

    Args:
        db: Database session
        user_id: User ID
        language: Language code (vi, en)
        call_deepseek_fn: Function to call DeepSeek API

    Returns:
        Dictionary with AI-generated insights
    """
    # Collect user's learning data
    progress = get_user_progress_summary(db, user_id)

    # Build prompt for AI
    prompt = build_insights_prompt(progress, language)

    # Call DeepSeek API if available
    ai_response = None
    if call_deepseek_fn:
        try:
            system_prompt = "Bạn là trợ lý AI chuyên phân tích học tập. Trả lời bằng JSON hợp lệ." if language == "vi" else "You are an AI learning analytics assistant. Return valid JSON."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            response = call_deepseek_fn(messages, temperature=0.7)

            # Try to parse JSON response
            try:
                # Strip markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]  # Remove ```
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                cleaned_response = cleaned_response.strip()

                ai_response = json.loads(cleaned_response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract meaningful summary
                debugPrint_log = f"[AI_INSIGHTS] JSON decode failed for response: {cleaned_response[:200]}..."
                print(debugPrint_log)

                # Check if response looks like JSON and try to extract summary
                if '"summary"' in response:
                    import re
                    match = re.search(r'"summary"\s*:\s*"([^"]+)"', response)
                    if match:
                        ai_response = {"summary": match.group(1), "strengths": [], "areas_to_improve": [], "recommendations": []}
                    else:
                        ai_response = None  # Will use rule-based fallback
                elif '{' in response and '}' in response:
                    # Looks like JSON but couldn't parse - don't use raw response
                    ai_response = None  # Will use rule-based fallback
                else:
                    # Plain text - use as summary
                    ai_response = {"summary": response}
        except Exception:
            # Fallback if AI call fails
            ai_response = None

    # Use AI response if available, otherwise use rule-based extraction
    if ai_response and isinstance(ai_response, dict):
        summary = ai_response.get("summary", "")
        strengths = ai_response.get("strengths", [])
        weaknesses = ai_response.get("weaknesses", [])
        recommendations = ai_response.get("recommendations", [])
    else:
        summary = _generate_fallback_summary(progress, language)
        strengths = extract_strengths(progress)
        weaknesses = extract_weaknesses(progress)
        recommendations = get_recommendations(progress)

    return {
        "summary": summary,
        "strengths": strengths if strengths else extract_strengths(progress),
        "areas_to_improve": weaknesses if weaknesses else extract_weaknesses(progress),
        "recommendations": recommendations if recommendations else get_recommendations(progress),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "progress_data": {
            "xp": progress["total_xp"],
            "streak": progress["current_streak"],
            "completion_percent": progress["completion_percent"],
            "badges_count": len(progress["badges"]),
        },
    }


def _generate_fallback_summary(progress: dict[str, Any], language: str = "vi") -> str:
    """Generate a simple summary when AI is not available."""
    if language == "vi":
        return f"""{progress['display_name']} đang ở hạng {progress['rank']} với {progress['total_xp']} XP.
Đã khám phá {progress['motifs']['discovered']} họa tiết và đạt {progress['quizzes']['passed']}/{progress['quizzes']['attempts']} bài kiểm tra.
Streak hiện tại: {progress['current_streak']} ngày."""
    else:
        return f"""{progress['display_name']} is at {progress['rank']} rank with {progress['total_xp']} XP.
Discovered {progress['motifs']['discovered']} motifs and passed {progress['quizzes']['passed']}/{progress['quizzes']['attempts']} quizzes.
Current streak: {progress['current_streak']} days."""


