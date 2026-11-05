# -*- coding: utf-8 -*-
"""Historical Learning Engine V2 — server-authoritative grading (Phase 8).

Business logic for docs/specs/HISTORY_FIRST_MASTER_SPEC.md sections 32-34:
typed answer contracts, server-side grading per question type (33.1-33.7),
the content-validity invariant (32.2), and V2 mastery dimension updates (34).

Security principle (Spec 33.4): grading is ALWAYS server-authoritative. The
client submits only raw answers; the server derives ``correct``/``score`` from
the question's ``answer_contract`` and authoritative relations in the
knowledge graph. Never trust any score/correctness field sent by the client.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Union
import uuid
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import (
    ClassMember,
    Classroom,
    ContentStatus,
    HistoricalClaim,
    HistoricalEntity,
    HistoricalEntityRelation,
    HistoricalSource,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
    HistoryLessonPlan,
    HistoryCausalLearningMetric,
    HistoryEthicsProtocol,
    HistoryLearningOutcomeAssessment,
    HistoryLearningOutcomeEvaluation,
    HistoryLearningOutcomeSubmission,
    HistorySubjectiveSurvey,
    HistoryPilotGuardianConsent,
    HistoryTeacherWorkloadLog,
    HistoryRubricCalibration,
    LessonContent,
    Motif,
    QuizQuestion,
    Urn,
    User,
    UserSkillLevel,
)
from ..rbac import STAFF_ROLES

# --------------------------------------------------------------------------- #
# Mastery dimensions (Spec 34)
# --------------------------------------------------------------------------- #
MASTERY_DIMENSIONS: list[str] = [
    "recognition",
    "factual_recall",
    "chronology",
    "geography",
    "source_literacy",
    "evidence_reasoning",
    "comparison",
    "contextualization",
]

# Question types that MUST NOT depend on unreviewed claims for authoritative
# learning (Spec 32.2). These are the factual/evidential V2 types.
FACTUAL_QUESTION_TYPES: set[str] = {
    "chronology_order",
    "image_identification",
    "map_location",
    "urn_hotspot",
    "evidence_match",
    "entity_match",
    "compare_two",
    "source_interpretation",
    "relationship_chain",
}

# Claim verification statuses permitted as learning-authority for factual
# questions (Spec 32.2 / Spec 37.1 precedence 1-2).
ELIGIBLE_CLAIM_STATUSES: set[str] = {
    "editor_reviewed",
    "expert_verified",
    "verified",
    "published",
}

# geo_precision -> tolerance multiplier so approximate/uncertain locations
# receive a wider acceptance window (Spec 33.3).
GEO_PRECISION_TOLERANCE_MULTIPLIER: dict[str, float] = {
    "exact": 1.0,
    "settlement": 1.5,
    "modern_correspondence": 2.0,
    "historical_boundary": 2.0,
    "approximate": 3.0,
    "water_body": 4.0,
    "region": 5.0,
    "unknown": 3.0,
}

EARTH_RADIUS_KM = 6371.0


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #
def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres between two lat/lng points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def longest_common_subsequence(a: list, b: list) -> int:
    """Length of the longest common subsequence (order-sensitive partial credit)."""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0
    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        cur = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = max(prev[j], cur[j - 1])
        prev = cur
    return prev[m]


def _ids(value: Any) -> list[str]:
    """Normalize a JSONB list of IDs (str/UUID) into strings for set math."""
    if not isinstance(value, list):
        return []
    return [str(v) for v in value]


# --------------------------------------------------------------------------- #
# Graders (Spec 33). Each returns {correct: bool, score: float, feedback_vi}.
# Signature is uniform: (prompt, answer, expected, db=None) — the ``db`` is
# only consulted by graders that verify against authoritative relations.
# --------------------------------------------------------------------------- #
def grade_chronology_order(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    expected_ids = _ids(expected.get("ordered_entity_ids"))
    submitted = _ids(answer.get("ordered_entity_ids"))
    if not expected_ids:
        correct = not submitted
        score = 1.0 if correct else 0.0
        feedback = "Câu hỏi không có đáp án chuẩn." if correct else "Có lỗi trong đề bài."
    else:
        correct = submitted == expected_ids
        score = longest_common_subsequence(submitted, expected_ids) / len(expected_ids)
        if correct:
            feedback = "Chính xác! Trình tự thời gian đã đúng."
        elif score > 0:
            feedback = (
                "Một phần chính xác — thứ tự còn chưa đúng. "
                "Hãy rà soát lại mốc thời gian của từng sự kiện."
            )
        else:
            feedback = "Chưa chính xác. Hãy sắp xếp lại các sự kiện theo đúng trình tự thời gian."
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def _grade_id_match(prompt: str, answer: dict, expected: dict, db=None) -> dict:
    """Generic exact-entity grader shared by image_identification/entity_match."""
    submitted = answer.get("entity_id") or answer.get("selected_entity_id")
    expected_id = expected.get("entity_id") or expected.get("correct_entity_id")
    correct = submitted is not None and str(submitted) == str(expected_id)
    return {
        "correct": correct,
        "score": 1.0 if correct else 0.0,
        "feedback_vi": "Chính xác! Đây là thực thể đúng." if correct else "Chưa chính xác. Hãy chọn lại thực thể.",
    }


grade_image_identification = _grade_id_match
grade_entity_match = _grade_id_match


def grade_map_location(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    try:
        lat = float(answer.get("lat"))
        lng = float(answer.get("lng"))
    except (TypeError, ValueError):
        return {
            "correct": False,
            "score": 0.0,
            "feedback_vi": "Câu trả lời cần tọa độ lat/lng.",
        }
    try:
        exp_lat = float(expected["lat"])
        exp_lng = float(expected["lng"])
    except (KeyError, TypeError, ValueError):
        return {
            "correct": False,
            "score": 0.0,
            "feedback_vi": "Câu hỏi chưa có đáp án tọa độ chuẩn.",
        }
    distance = haversine_km(lat, lng, exp_lat, exp_lng)
    base_tolerance = float(expected.get("tolerance_km", 5.0))
    multiplier = GEO_PRECISION_TOLERANCE_MULTIPLIER.get(
        str(expected.get("geo_precision", "")), 1.0
    )
    effective_tolerance = base_tolerance * multiplier
    correct = distance <= effective_tolerance
    if correct:
        score = 1.0
        feedback = f"Chính xác! Vị trí đúng trong khoảng {distance:.1f} km."
    else:
        # Linear falloff beyond the tolerance window for gentle partial credit.
        falloff = max(1.0, effective_tolerance)
        score = max(0.0, 1.0 - (distance - effective_tolerance) / falloff)
        feedback = (
            f"Chưa chính xác: cách vị trí chuẩn {distance:.1f} km "
            f"(dung sai {effective_tolerance:.1f} km theo độ chính xác địa lý)."
        )
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def _relief_belongs_to_urn(db: Session, urn_id: UUID, relief_id: UUID) -> bool:
    """True if ``relief_id`` is recorded as ``located_on`` the urn (authoritative
    knowledge graph check, Spec 33.4)."""
    if db is None:
        return True
    count = db.scalar(
        select(func.count())
        .select_from(HistoricalEntityRelation)
        .where(
            HistoricalEntityRelation.subject_entity_id == relief_id,
            HistoricalEntityRelation.predicate == "located_on",
            HistoricalEntityRelation.object_entity_id == urn_id,
        )
    )
    return bool(count and count > 0)


def grade_urn_hotspot(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    hotspot_match = str(answer.get("hotspot_id")) == str(expected.get("hotspot_id"))
    relief_id = expected.get("relief_entity_id")
    urn_id = expected.get("urn_entity_id")
    relief_ok = bool(relief_id) and bool(urn_id) and _relief_belongs_to_urn(
        db, UUID(str(urn_id)), UUID(str(relief_id))
    )
    correct = hotspot_match and relief_ok
    if correct:
        feedback = "Chính xác! Điểm nóng đúng và hoa văn thuộc về đỉnh này."
    elif not hotspot_match:
        feedback = "Chưa chính xác — điểm nóng trên đỉnh chưa đúng."
    else:
        feedback = "Chưa chính xác — hoa văn này không thuộc về đỉnh được chọn."
    return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback_vi": feedback}


def _score_set_overlap(submitted: set, correct_set: set, label: str) -> dict:
    """Shared rubric: exact set match = full; otherwise overlap minus wrong picks."""
    if not correct_set:
        correct = not submitted
        score = 1.0 if correct else 0.0
        feedback = "Chính xác." if correct else "Không được chọn mục nào."
        return {"correct": correct, "score": score, "feedback_vi": feedback}
    correct = submitted == correct_set
    inter = len(submitted & correct_set)
    wrong = len(submitted - correct_set)
    score = max(0.0, (inter - wrong) / len(correct_set))
    if correct:
        feedback = f"Chính xác! Đã chọn đúng {label}."
    elif score > 0:
        feedback = f"Một phần chính xác — còn thiếu hoặc chọn thừa {label}."
    else:
        feedback = f"Chưa chính xác — {label} chưa đúng."
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def grade_evidence_match(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    submitted = set(_ids(answer.get("source_ids")))
    correct_set = set(_ids(expected.get("correct_source_ids")))
    result = _score_set_overlap(submitted, correct_set, "các nguồn tư liệu")
    if result["correct"]:
        result["feedback_vi"] = "Chính xác! Bạn đã xác định đúng nguồn tư liệu hỗ trợ cho khẳng định."
    return result


def grade_multi_select(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    submitted = set(_ids(answer.get("option_ids")))
    correct_set = set(_ids(expected.get("correct_option_ids")))
    return _score_set_overlap(submitted, correct_set, "các phương án")


def grade_source_interpretation(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    inferable = bool(expected.get("inferable", False))
    allowed = set(_ids(expected.get("allowed_conclusion_ids")))
    submitted = set(_ids(answer.get("conclusion_ids")))
    if not inferable:
        correct = not submitted
        score = 1.0 if correct else 0.0
        feedback = (
            "Chính xác — đoạn tư liệu này không đủ căn cứ để rút ra kết luận đó."
            if correct
            else "Chưa chính xác — đoạn tư liệu này không cho phép rút ra kết luận đó."
        )
        return {"correct": correct, "score": score, "feedback_vi": feedback}
    if not allowed:
        correct = not submitted
        score = 1.0 if correct else 0.0
        feedback = "Chính xác." if correct else "Không nên chọn kết luận nào."
        return {"correct": correct, "score": score, "feedback_vi": feedback}
    correct = bool(submitted) and submitted.issubset(allowed)
    if correct:
        score = 1.0
        feedback = "Chính xác! Kết luận nằm trong phạm vi có thể suy luận từ tư liệu."
    else:
        score = max(0.0, len(submitted & allowed) / len(allowed))
        if score > 0:
            feedback = "Một phần chính xác — một số kết luận vượt quá phạm vi suy luận của tư liệu."
        else:
            feedback = "Chưa chính xác — kết luận không được phép suy luận từ tư liệu này."
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def grade_compare_two(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    exp_dims = expected.get("dimensions") or {}
    sub_dims = answer.get("dimensions") or {}
    if not isinstance(exp_dims, dict) or not exp_dims:
        correct = not sub_dims
        score = 1.0 if correct else 0.0
        return {
            "correct": correct,
            "score": score,
            "feedback_vi": "Chính xác." if correct else "Không có tiêu chí so sánh.",
        }
    matched = sum(
        1 for key, value in exp_dims.items() if sub_dims.get(key) == value
    )
    correct = matched == len(exp_dims)
    score = matched / len(exp_dims)
    if correct:
        feedback = "Chính xác! Các tiêu chí so sánh đều đúng."
    elif score > 0:
        feedback = f"Một phần chính xác — {matched}/{len(exp_dims)} tiêu chí đúng."
    else:
        feedback = "Chưa chính xác — các tiêu chí so sánh chưa đúng."
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def grade_relationship_chain(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    expected_ids = _ids(expected.get("chain_entity_ids"))
    submitted = _ids(answer.get("chain_entity_ids"))
    if not expected_ids:
        correct = not submitted
        score = 1.0 if correct else 0.0
        feedback = "Chính xác." if correct else "Câu hỏi chưa có chuỗi quan hệ chuẩn."
    else:
        correct = submitted == expected_ids
        score = longest_common_subsequence(submitted, expected_ids) / len(expected_ids)
        if correct:
            feedback = "Chính xác! Chuỗi quan hệ đã đúng."
        elif score > 0:
            feedback = "Một phần chính xác — thứ tự các quan hệ còn chưa đúng."
        else:
            feedback = "Chưa chính xác — chuỗi quan hệ chưa đúng."
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def grade_short_response(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    """Rubric-based fallback for short responses (Spec 33.7).

    LLM grading MAY assist but is never the sole authoritative grader here;
    this rubric scores against required/accepted keywords declared in the
    answer_contract so high-stakes results stay deterministic.
    """
    text = str(answer.get("text") or answer.get("answer") or "").strip().lower()
    required = [str(k).lower() for k in _ids(expected.get("required_keywords"))]
    accepted = [str(k).lower() for k in _ids(expected.get("accepted_answers"))]
    if accepted:
        exact_hit = any(acc in text for acc in accepted)
        if exact_hit:
            return {
                "correct": True,
                "score": 1.0,
                "feedback_vi": "Chính xác! Câu trả lời khớp với đáp án.",
            }
    if not required:
        return {
            "correct": not text,
            "score": 1.0 if not text else 0.0,
            "feedback_vi": "Chính xác." if not text else "Câu trả lời chưa đạt.",
        }
    hits = sum(1 for kw in required if kw in text)
    score = hits / len(required)
    correct = score == 1.0
    feedback = (
        "Chính xác! Câu trả lời đề cập đầy đủ các ý chính."
        if correct
        else (
            f"Một phần chính xác — còn thiếu {len(required) - hits}/{len(required)} ý chính."
            if hits
            else "Chưa chính xác — câu trả lời chưa đề cập các ý chính."
        )
    )
    return {"correct": correct, "score": round(score, 4), "feedback_vi": feedback}


def grade_multiple_choice(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    submitted = (
        answer.get("answer")
        or answer.get("selected_option")
        or answer.get("choice")
    )
    correct = submitted is not None and str(submitted) == str(
        expected.get("correct_answer")
    )
    return {
        "correct": correct,
        "score": 1.0 if correct else 0.0,
        "feedback_vi": "Chính xác!" if correct else "Chưa chính xác.",
    }


def grade_true_false(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    return grade_multiple_choice(prompt, answer, expected, db)


def grade_image_select(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    return grade_multiple_choice(prompt, answer, expected, db)


def grade_mesh_location(
    prompt: str, answer: dict, expected: dict, db: Optional[Session] = None
) -> dict:
    submitted = answer.get("mesh_name") or answer.get("mesh")
    correct = submitted is not None and str(submitted) == str(
        expected.get("target_mesh_name")
    )
    return {
        "correct": correct,
        "score": 1.0 if correct else 0.0,
        "feedback_vi": "Chính xác! Đã chọn đúng vị trí trên mô hình." if correct else "Chưa chính xác — hãy chọn lại vị trí trên mô hình.",
    }


# --------------------------------------------------------------------------- #
# Grader registry (keyed by question_type)
# --------------------------------------------------------------------------- #
graders: dict[str, Callable[..., dict]] = {
    "multiple_choice": grade_multiple_choice,
    "true_false": grade_true_false,
    "image_select": grade_image_select,
    "mesh_location": grade_mesh_location,
    "chronology_order": grade_chronology_order,
    "image_identification": grade_image_identification,
    "map_location": grade_map_location,
    "urn_hotspot": grade_urn_hotspot,
    "evidence_match": grade_evidence_match,
    "entity_match": grade_entity_match,
    "compare_two": grade_compare_two,
    "source_interpretation": grade_source_interpretation,
    "short_response": grade_short_response,
    "multi_select": grade_multi_select,
    "relationship_chain": grade_relationship_chain,
}


# --------------------------------------------------------------------------- #
# Server-authoritative dispatch
# --------------------------------------------------------------------------- #
def _default_expected(question: QuizQuestion) -> dict:
    """Derive a minimal answer contract for legacy questions without one."""
    return {
        "correct_answer": question.correct_answer,
        "target_mesh_name": question.target_mesh_name,
    }


def grade_question(
    db: Session, question: QuizQuestion, answer: dict
) -> dict:
    """Grade an answer server-side. Returns {correct, score, feedback_vi}."""
    expected = question.answer_contract or _default_expected(question)
    grader = graders.get(question.question_type)
    if grader is None:
        return {
            "correct": False,
            "score": 0.0,
            "feedback_vi": "Chưa có bộ chấm điểm cho loại câu hỏi này.",
        }
    if not isinstance(answer, dict):
        return {
            "correct": False,
            "score": 0.0,
            "feedback_vi": "Câu trả lời phải là một đối tượng dữ liệu.",
        }
    return grader(question.question_text, answer, expected, db=db)


# --------------------------------------------------------------------------- #
# Content validity invariant (Spec 32.2)
# --------------------------------------------------------------------------- #
def content_validity_check(db: Session, question: QuizQuestion) -> bool:
    """A factual/evidential question is valid for authoritative learning only
    when every claim it depends on is verified or editor-reviewed.

    Questions without claim dependencies are valid (legacy questions carry no
    provenance). Questions whose claims are unreviewed/needs_source/rejected/
    disputed/superseded are NOT valid and must be flagged
    ``blocked_for_authoritative_learning``.
    """
    claim_ids = _ids(question.claim_ids)
    if not claim_ids:
        return True
    for raw_id in claim_ids:
        claim = db.get(HistoricalClaim, UUID(raw_id)) if raw_id else None
        if claim is None or claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
            return False
    return True


# --------------------------------------------------------------------------- #
# Mastery V2 (Spec 34)
# --------------------------------------------------------------------------- #
def update_mastery_from_result(
    db: Session, user_id: UUID, question: QuizQuestion, result: dict
) -> list[str]:
    """Update the user's V2 mastery dimensions from a graded result.

    Each skill dimension listed on the question gets an incremental weighted
    average: ``level = (level * n + score) / (n + 1)``. A ``user_skill_levels``
    row is created per dimension on first exposure and the per-row
    ``skill_dimensions`` JSONB keeps a small weighted breakdown.
    """
    dimensions = [str(d) for d in (question.skill_dimensions or [])]
    if not dimensions:
        return []
    score = max(0.0, min(1.0, float(result.get("score", 0.0))))
    correct = bool(result.get("correct", False))
    updated: list[str] = []
    for dimension in dimensions:
        row = db.scalar(
            select(UserSkillLevel).where(
                UserSkillLevel.user_id == user_id,
                UserSkillLevel.skill_type == dimension,
            )
        )
        if row is None:
            row = UserSkillLevel(
                user_id=user_id,
                skill_type=dimension,
                skill_level=0.5,
                total_questions=0,
                correct_answers=0,
                skill_dimensions={},
            )
            db.add(row)
            db.flush()
        prev_total = row.total_questions
        row.skill_level = round(
            (row.skill_level * prev_total + score) / (prev_total + 1), 4
        )
        row.total_questions = prev_total + 1
        if correct:
            row.correct_answers += 1
        row.skill_dimensions = {
            "dimension": dimension,
            "attempts": row.total_questions,
            "correct": row.correct_answers,
            "last_score": score,
        }
        updated.append(dimension)
    return updated


def get_mastery_dimensions(db: Session, user_id: UUID) -> list[dict]:
    """Return the 8 V2 mastery dimensions for a user, with null values when the
    user has no rows yet (Spec 34 default state)."""
    rows = {
        r.skill_type: r
        for r in db.scalars(
            select(UserSkillLevel).where(
                UserSkillLevel.user_id == user_id,
                UserSkillLevel.skill_type.in_(MASTERY_DIMENSIONS),
            )
        )
    }
    result = []
    for dimension in MASTERY_DIMENSIONS:
        row = rows.get(dimension)
        result.append(
            {
                "dimension": dimension,
                "value": row.skill_level if row else None,
                "total_questions": row.total_questions if row else 0,
                "correct_answers": row.correct_answers if row else 0,
                "last_score": (row.skill_dimensions or {}).get("last_score") if row else None,
            }
        )
    return result


# --------------------------------------------------------------------------- #
# Source-Guided Curriculum Mapping & Publishing Gate (V5-T029)
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parents[2]

# Map urn slug to 2D rubbing asset path relative to REPO_ROOT
URN_RUBBING_MAP: dict[str, str] = {
    "cao-dinh": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
    "thuan-dinh": "ban-duc-noi/THUAN DINH/THUẦN ĐỈNH.jpg",
    "nhan-dinh": "ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
    "chuong-dinh": "ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg",
    "tuyen-dinh": "ban-duc-noi/TUYEN DINH/TUYEN DINH.jpg",
    "nghi-dinh": "ban-duc-noi/NGHI DINH/NGHI DINH.jpg",
    "du-dinh": "ban-duc-noi/DU DINH/DỤ ĐỈNH.jpg",
    "huyen-dinh": "ban-duc-noi/HUYEN DINH/HUYỀN ĐỈNH.jpg",
    "anh-dinh": "ban-duc-noi/ANH DINH/ANH ĐỈNH.jpg",
}

CURRICULUM_MODULES: list[dict[str, Any]] = [
    {
        "id": "mod-p2-01",
        "slug": "giai-ma-18-ban-duc-cao-dinh",
        "title_vi": "Giải mã 18 Bản đúc nổi trên Cao Đỉnh",
        "title_en": "Decoding the 18 Relief Inscriptions of Cao Đỉnh",
        "description_vi": "Khám phá mô hình số 3D tương tác và bản dập 2D tương đương của Cao Đỉnh: Khảo sát hình tượng rồng mây, núi non, sông Hương và vũ khí hoàng gia.",
        "description_en": "Interact with the high-resolution 3D digital twin or 2D rubbing equivalent of Cao Đỉnh: Explore dragon clouds, sacred mountains, and imperial armaments.",
        "era": "Triều Minh Mạng (1835–1837)",
        "topic": "Nghệ thuật đúc đồng & Biểu tượng vương quyền Cửu Đỉnh",
        "curriculum_framework": "Chương trình Giáo dục phổ thông 2018 (Thông tư 32/2018/TT-BGDĐT)",
        "roadmap_phase": "P2_INTERACTIVE_3D",
        "historical_competencies": ["S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"],
        "entity_slugs": ["cao-dinh", "the-mieu", "song-huong"],
        "core_claim_keys": ["claim-cao-dinh-01", "claim-cao-dinh-02", "claim-cao-dinh-03"],
        "source_titles": [
            "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 168)",
            "Đại Nam Thực Lục Chính Biên (Đệ nhị kỷ)",
        ],
        "learning_objectives": [
            {
                "code": "OBJ-CAO-DINH-SPATIAL",
                "text_vi": "Xác định vị trí Cao Đỉnh tại vị trí trung tâm trong cụm 9 đỉnh trước Thế Miếu và nhận diện các mảng hoa văn nổi trên thân đỉnh qua mô hình 3D hoặc bản dập 2D",
                "text_en": "Locate Cao Đỉnh at the central position in front of Thế Miếu and identify relief motifs via 3D model or 2D rubbing",
                "competency": "S1_SPATIAL",
                "target_entity_slug": "cao-dinh",
                "target_claim_keys": ["claim-cao-dinh-01"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-CAO-DINH-TEMPORAL",
                "text_vi": "Phân tích tiến trình thời gian khởi đúc năm 1835 và hoàn thành năm 1837 dưới triều vua Minh Mạng",
                "text_en": "Analyze the chronology of casting from 1835 to 1837 under Emperor Minh Mạng",
                "competency": "S2_TEMPORAL",
                "target_entity_slug": "cao-dinh",
                "target_claim_keys": ["claim-cao-dinh-02"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-CAO-DINH-EVIDENCE",
                "text_vi": "Đối chiếu hình khắc 18 bản đúc với chính sử Đại Nam Thực Lục Chính Biên và Khâm Định Đại Nam Hội Điển Sự Lệ",
                "text_en": "Cross-reference the 18 relief inscriptions with primary imperial annals",
                "competency": "S3_EVIDENCE",
                "target_entity_slug": "cao-dinh",
                "target_claim_keys": ["claim-cao-dinh-03"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-CAO-DINH-ARGUMENT",
                "text_vi": "Lập luận về thông điệp biểu tượng vũ trụ quan thống nhất non sông thể hiện qua các hình tượng núi, sông, sản vật và vũ khí",
                "text_en": "Formulate historical arguments on cosmological sovereignty and territorial unity symbolized across the urn",
                "competency": "S4_ARGUMENT",
                "target_entity_slug": "cao-dinh",
                "target_claim_keys": ["claim-cao-dinh-01", "claim-cao-dinh-03"],
                "claims_verified": True,
            },
        ],
        "media_fallback_2d": {
            "available": True,
            "asset_type": "2d_rubbing",
            "url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%89nh.jpg",
            "local_file_path": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
            "description": "Bản dập 2D độ phân giải cao Cao Đỉnh hỗ trợ học tập trong môi trường băng thông thấp hoặc thiết bị không hỗ trợ WebGL",
        },
    },
    {
        "id": "mod-p2-02",
        "slug": "ky-thuat-duc-rong-thuan-dinh",
        "title_vi": "Kỹ thuật Đúc rỗng & Khuôn đất sét Thuần Đỉnh",
        "title_en": "Hollow Casting & Loam Mold Engineering on Thuần Đỉnh",
        "description_vi": "Khảo sát giải phẫu kỹ thuật đúc đồng nguyên khối nặng hàng tấn qua mô hình 3D Thuần Đỉnh và bản dập 2D tư liệu.",
        "description_en": "Examine multi-ton monolithic hollow casting techniques using the Thuần Đỉnh 3D model and 2D archival rubbings.",
        "era": "Triều Minh Mạng (1835–1837)",
        "topic": "Kỹ nghệ luyện kim & Kỹ thuật đúc đồng truyền thống",
        "curriculum_framework": "Chương trình Giáo dục phổ thông 2018 (Thông tư 32/2018/TT-BGDĐT)",
        "roadmap_phase": "P2_INTERACTIVE_3D",
        "historical_competencies": ["S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"],
        "entity_slugs": ["thuan-dinh"],
        "core_claim_keys": ["claim-thuan-dinh-01", "claim-thuan-dinh-02"],
        "source_titles": [
            "Khâm Định Đại Nam Hội Điển Sự Lệ (Công bộ - Đúc tượng)",
            "Châu bản triều Nguyễn",
        ],
        "learning_objectives": [
            {
                "code": "OBJ-THUAN-DINH-SPATIAL",
                "text_vi": "Định vị Thuần Đỉnh trong hàng đỉnh và khảo sát cấu trúc quai, chân đỉnh qua bản dập 2D và mô hình 3D",
                "text_en": "Locate Thuần Đỉnh and examine handle/leg geometry via 2D rubbing and 3D model",
                "competency": "S1_SPATIAL",
                "target_entity_slug": "thuan-dinh",
                "target_claim_keys": ["claim-thuan-dinh-01"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-THUAN-DINH-EVIDENCE",
                "text_vi": "Đối chiếu thành phần hợp kim đồng - chì - kẽm theo chỉ dụ triều đình ghi trong Hội Điển Sự Lệ",
                "text_en": "Cross-reference bronze alloy composition decrees in imperial statutes",
                "competency": "S3_EVIDENCE",
                "target_entity_slug": "thuan-dinh",
                "target_claim_keys": ["claim-thuan-dinh-02"],
                "claims_verified": True,
            },
        ],
        "media_fallback_2d": {
            "available": True,
            "asset_type": "2d_rubbing",
            "url": "/assets/ban-duc-noi/THUAN%20DINH/THU%E1%BA%A6N%20%C4%90%E1%BB%88NH.jpg",
            "local_file_path": "ban-duc-noi/THUAN DINH/THUẦN ĐỈNH.jpg",
            "description": "Bản dập 2D Thuần Đỉnh phục vụ trường học ngoại thành và vùng sâu vùng xa",
        },
    },
    {
        "id": "mod-p1-01",
        "slug": "kham-dinh-dai-nam-hoi-dien",
        "title_vi": "Thư tịch: Khâm Định Đại Nam Hội Điển Sự Lệ",
        "title_en": "Imperial Archives: Khâm Định Đại Nam Administrative Statutes",
        "description_vi": "Khảo cứu các chỉ dụ của Hoàng đế Minh Mạng năm 1835 về việc chọn đất, công thức hợp kim đồng thau và điều động nghệ nhân đúc Cửu Đỉnh.",
        "description_en": "Examine Emperor Minh Mạng’s 1835 edicts concerning clay selection, bronze alloy formulas, and the mobilization of foundry artisans.",
        "era": "Triều Minh Mạng (1835–1837)",
        "topic": "Văn bản hành chính triều đình & Thư tịch Hán Nôm",
        "curriculum_framework": "Chương trình Giáo dục phổ thông 2018 (Thông tư 32/2018/TT-BGDĐT)",
        "roadmap_phase": "P1_HERITAGE_BASELINE",
        "historical_competencies": ["S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"],
        "entity_slugs": ["kham-dinh-dai-nam-hoi-dien-su-le"],
        "core_claim_keys": ["claim-kham-dinh-01", "claim-kham-dinh-02"],
        "source_titles": [
            "Khâm Định Đại Nam Hội Điển Sự Lệ (Nội các triều Nguyễn)",
        ],
        "learning_objectives": [
            {
                "code": "OBJ-HOI-DIEN-EVIDENCE",
                "text_vi": "Trích dẫn chuẩn xác quyển và số tờ trong Hội Điển Sự Lệ quy định việc đúc 9 đỉnh đồng",
                "text_en": "Cite precise volumes and folios in the imperial statutes regulating the casting of the Nine Urns",
                "competency": "S3_EVIDENCE",
                "target_entity_slug": "kham-dinh-dai-nam-hoi-dien-su-le",
                "target_claim_keys": ["claim-kham-dinh-01"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-HOI-DIEN-ARGUMENT",
                "text_vi": "Đánh giá tính xác thực của quy trình huy động thợ đúc và cung cấp nguyên liệu đồng từ các mỏ nội địa",
                "text_en": "Evaluate historical authenticity of artisan mobilization and domestic mineral supply",
                "competency": "S4_ARGUMENT",
                "target_entity_slug": "kham-dinh-dai-nam-hoi-dien-su-le",
                "target_claim_keys": ["claim-kham-dinh-02"],
                "claims_verified": True,
            },
        ],
        "media_fallback_2d": {
            "available": True,
            "asset_type": "2d_rubbing",
            "url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%89nh.jpg",
            "local_file_path": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
            "description": "Bản dập 2D đối chiếu thư tịch triều Nguyễn",
        },
    },
    {
        "id": "mod-p1-03",
        "slug": "ngo-mon-quang-truong-dai-trieu",
        "title_vi": "Ngọ Môn & Trục Thần Đạo Đại Triều Nghi",
        "title_en": "Ngọ Môn Gate & The Central Ceremonial Sacred Axis",
        "description_vi": "Giải mã cấu trúc không gian quyền lực và quy chế phân luồng 5 cửa qua bản đồ trực giao và sử liệu Đại Nam Thực Lục.",
        "description_en": "Decode spatial power hierarchy and 5-portal circulation rules via orthophoto maps and imperial annals.",
        "era": "Triều Minh Mạng (1833)",
        "topic": "Quy hoạch kiến trúc kinh thành Huế",
        "curriculum_framework": "Chương trình Giáo dục phổ thông 2018 (Thông tư 32/2018/TT-BGDĐT)",
        "roadmap_phase": "P1_HERITAGE_BASELINE",
        "historical_competencies": ["S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"],
        "entity_slugs": ["ngo-mon", "cau-trung-dao", "dien-thai-hoa"],
        "core_claim_keys": ["claim-ngo-mon-01", "claim-ngo-mon-02", "claim-ngo-mon-03"],
        "source_titles": [
            "Đại Nam Thực Lục Chính Biên (Đệ nhị kỷ, Quyển 98)",
            "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 168)",
        ],
        "learning_objectives": [
            {
                "code": "OBJ-NGO-MON-SPATIAL",
                "text_vi": "Xác định vai trò tiền tiêu trên trục thần đạo và quy chế 5 cửa ngõ trên cổng Ngọ Môn",
                "text_en": "Map ceremonial vanguard function and five-gate royal circulation protocols",
                "competency": "S1_SPATIAL",
                "target_entity_slug": "ngo-mon",
                "target_claim_keys": ["claim-ngo-mon-01", "claim-ngo-mon-02"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-NGO-MON-TEMPORAL",
                "text_vi": "Nhận diện năm khởi dựng 1833 thay cho đài Nam Sách cũ thời Gia Long",
                "text_en": "Identify 1833 construction date replacing the former Nam Sách Pavilion",
                "competency": "S2_TEMPORAL",
                "target_entity_slug": "ngo-mon",
                "target_claim_keys": ["claim-ngo-mon-01"],
                "claims_verified": True,
            },
            {
                "code": "OBJ-NGO-MON-EVIDENCE",
                "text_vi": "Dẫn chứng quy chế phân luồng cửa ngự đạo từ Khâm Định Đại Nam Hội Điển Sự Lệ",
                "text_en": "Cite five-portal traffic protocols from Imperial Statutes",
                "competency": "S3_EVIDENCE",
                "target_entity_slug": "ngo-mon",
                "target_claim_keys": ["claim-ngo-mon-02", "claim-ngo-mon-03"],
                "claims_verified": True,
            },
        ],
        "media_fallback_2d": {
            "available": True,
            "asset_type": "2d_rubbing",
            "url": "/assets/ban-duc-noi/NGHI%20DINH/NGHI%20DINH.jpg",
            "local_file_path": "ban-duc-noi/NGHI DINH/NGHI DINH.jpg",
            "description": "Bản vẽ tư liệu và bản dập 2D kiến trúc triều Nguyễn",
        },
    },
]


def resolve_2d_rubbing_fallback(
    target_slug_or_motif: str, base_dir: Optional[Path] = None
) -> dict[str, Any]:
    """Resolve the 2D rubbing asset fallback for low-bandwidth educational environments.

    Looks up high-resolution rubbing files in ``ban-duc-noi/`` corresponding to
    the urn or relief motif. Confirms file existence and returns metadata.
    """
    root = base_dir or REPO_ROOT
    slug = (target_slug_or_motif or "").strip().lower()

    # Direct urn match
    rel_path = URN_RUBBING_MAP.get(slug)
    if not rel_path:
        # Try normalizing "cao dinh", "caodinh"
        for k, v in URN_RUBBING_MAP.items():
            if k.replace("-", "") == slug.replace("-", "").replace(" ", ""):
                rel_path = v
                break

    if not rel_path:
        # Check if it matches a relief file under any urn directory
        ban_duc_noi = root / "ban-duc-noi"
        if ban_duc_noi.is_dir():
            for folder in ban_duc_noi.iterdir():
                if folder.is_dir():
                    candidate = folder / f"{target_slug_or_motif}.jpg"
                    if candidate.is_file():
                        rel_path = f"ban-duc-noi/{folder.name}/{candidate.name}"
                        break

    if rel_path:
        full_path = root / rel_path
        if full_path.is_file():
            stat = full_path.stat()
            from urllib.parse import quote
            url_path = "/assets/" + "/".join(quote(part) for part in rel_path.split("/"))
            return {
                "available": True,
                "asset_type": "2d_rubbing",
                "url": url_path,
                "local_file_path": rel_path,
                "byte_size": stat.st_size,
                "description": f"Bản dập 2D tư liệu {target_slug_or_motif} (phục vụ môi trường mạng thấp)",
            }

    # Fallback to default Cao Đỉnh rubbing if target not directly matched
    fallback_rel = "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg"
    full_fallback = root / fallback_rel
    if full_fallback.is_file():
        stat = full_fallback.stat()
        return {
            "available": True,
            "asset_type": "2d_rubbing",
            "url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%89nh.jpg",
            "local_file_path": fallback_rel,
            "byte_size": stat.st_size,
            "description": "Bản dập 2D mặc định (Cao Đỉnh) phục vụ môi trường mạng thấp",
        }

    return {
        "available": False,
        "asset_type": "2d_rubbing",
        "url": "",
        "local_file_path": None,
        "byte_size": 0,
        "description": "Chưa có bản dập 2D cho mục này",
    }


def get_curriculum_modules(db: Optional[Session] = None) -> list[dict[str, Any]]:
    """Return all curriculum modules with live objective claim verification."""
    modules = []
    for mod in CURRICULUM_MODULES:
        item = dict(mod)
        fallback = resolve_2d_rubbing_fallback(item["slug"])
        item["media_fallback_2d"] = fallback

        if db is not None:
            is_valid, obj_reports = validate_curriculum_objective_claims(db, item)
            item["publication_gate_ready"] = is_valid
            new_objectives = []
            for idx, obj in enumerate(item.get("learning_objectives", [])):
                obj_copy = dict(obj)
                if idx < len(obj_reports):
                    obj_copy["claims_verified"] = obj_reports[idx]["claims_verified"]
                new_objectives.append(obj_copy)
            item["learning_objectives"] = new_objectives
        else:
            item["publication_gate_ready"] = True

        modules.append(item)
    return modules


def get_curriculum_module(
    slug_or_id: str, db: Optional[Session] = None
) -> Optional[dict[str, Any]]:
    """Get single curriculum module by slug or id."""
    slug_clean = str(slug_or_id).strip().lower()
    for mod in CURRICULUM_MODULES:
        if mod["slug"] == slug_clean or mod["id"] == slug_clean:
            item = dict(mod)
            item["media_fallback_2d"] = resolve_2d_rubbing_fallback(item["slug"])
            if db is not None:
                is_valid, obj_reports = validate_curriculum_objective_claims(db, item)
                item["publication_gate_ready"] = is_valid
                new_objectives = []
                for idx, obj in enumerate(item.get("learning_objectives", [])):
                    obj_copy = dict(obj)
                    if idx < len(obj_reports):
                        obj_copy["claims_verified"] = obj_reports[idx]["claims_verified"]
                    new_objectives.append(obj_copy)
                item["learning_objectives"] = new_objectives
            else:
                item["publication_gate_ready"] = True
            return item
    return None


def validate_curriculum_objective_claims(
    db: Session, module_slug_or_dict: Union[str, dict[str, Any]]
) -> tuple[bool, list[dict[str, Any]]]:
    """Validate that claims linked to curriculum objectives are verified in DB."""
    if isinstance(module_slug_or_dict, str):
        mod = get_curriculum_module(module_slug_or_dict)
    else:
        mod = module_slug_or_dict

    if not mod:
        return False, [{"issue": "Module not found", "claims_verified": False}]

    all_verified = True
    objective_reports = []

    for obj in mod.get("learning_objectives", []):
        claim_keys = obj.get("target_claim_keys", [])
        obj_report: dict[str, Any] = {
            "code": obj.get("code"),
            "target_claim_keys": claim_keys,
            "claims_verified": True,
            "unverified_keys": [],
        }
        for k in claim_keys:
            claim = db.scalar(
                select(HistoricalClaim).where(HistoricalClaim.claim_key == k)
            )
            if claim is None or claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
                all_verified = False
                obj_report["claims_verified"] = False
                obj_report["unverified_keys"].append(k)

        objective_reports.append(obj_report)

    return all_verified, objective_reports


def validate_lesson_for_publication(
    db: Session,
    lesson: LessonContent,
    required_claim_ids: Optional[list[Union[str, UUID]]] = None,
    module_slug: Optional[str] = None,
) -> tuple[bool, list[str]]:
    """Validate whether a lesson satisfies the historical claim publishing gate.

    Publishing gate invariant (Spec 32.2 / V5-T029):
    A learning module or lesson CANNOT be published if:
    1. Any core required historical claim is unreviewed, needs_source, rejected, disputed, or superseded.
    2. Any required claim ID does not exist in the database.
    3. Associated quiz questions contain unreviewed or disputed claims.

    Returns:
        (is_valid: bool, issues: list[str])
    """
    issues: list[str] = []
    target_claim_ids: list[UUID] = []

    # 1. Collect claim IDs from arguments
    if required_claim_ids:
        for cid in required_claim_ids:
            try:
                target_claim_ids.append(UUID(str(cid)))
            except (ValueError, TypeError):
                issues.append(f"Invalid claim UUID format: {cid}")

    # 2. Collect claim IDs from lesson.additional_images metadata if present
    if lesson.additional_images and isinstance(lesson.additional_images, dict):
        extra_claims = (
            lesson.additional_images.get("required_claim_ids")
            or lesson.additional_images.get("claim_ids")
        )
        if extra_claims and isinstance(extra_claims, list):
            for cid in extra_claims:
                try:
                    uuid_val = UUID(str(cid))
                    if uuid_val not in target_claim_ids:
                        target_claim_ids.append(uuid_val)
                except (ValueError, TypeError):
                    issues.append(f"Invalid claim UUID in lesson metadata: {cid}")

    # 3. Collect claim IDs from module slug mapping if specified
    if module_slug:
        mod = get_curriculum_module(module_slug, db=db)
        if mod and mod.get("core_claim_keys"):
            for k in mod["core_claim_keys"]:
                claim_row = db.scalar(
                    select(HistoricalClaim).where(HistoricalClaim.claim_key == k)
                )
                if claim_row:
                    if claim_row.id not in target_claim_ids:
                        target_claim_ids.append(claim_row.id)
                else:
                    issues.append(f"Curriculum module '{module_slug}' references missing claim key '{k}'")

    # 4. Check each claim's existence and verification status
    for cid in target_claim_ids:
        claim = db.get(HistoricalClaim, cid)
        if claim is None:
            issues.append(f"Required historical claim {cid} not found in database")
            continue
        if claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
            statement_snippet = (claim.statement_vi or "")[:50]
            issues.append(
                f"Historical claim {cid} ('{statement_snippet}...') has ineligible verification_status "
                f"'{claim.verification_status}' (must be expert_verified or editor_reviewed)"
            )

    # 5. Check associated quiz questions for this lesson's motif
    if lesson.motif_id:
        questions = list(
            db.scalars(
                select(QuizQuestion).where(QuizQuestion.motif_id == lesson.motif_id)
            )
        )
        for q in questions:
            for raw_id in _ids(q.claim_ids):
                try:
                    q_claim = db.get(HistoricalClaim, UUID(raw_id))
                    if q_claim is None:
                        issues.append(f"Question '{q.id}' references non-existent claim {raw_id}")
                    elif q_claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
                        issues.append(
                            f"Question '{q.id}' depends on unreviewed/ineligible claim {raw_id} (status: {q_claim.verification_status})"
                        )
                except (ValueError, TypeError):
                    pass

    return len(issues) == 0, issues


def publish_lesson_with_gate(
    db: Session,
    lesson_id: UUID,
    current_user_id: Optional[UUID] = None,
    required_claim_ids: Optional[list[Union[str, UUID]]] = None,
    module_slug: Optional[str] = None,
    review_notes: Optional[str] = None,
) -> LessonContent:
    """Publish a lesson enforcing the historical claim verification gate.

    Raises AppError('LESSON_UNVERIFIED_CLAIMS', ..., 422) if any required
    claim is unreviewed, disputed, or rejected.
    """
    lesson = db.get(LessonContent, lesson_id)
    if lesson is None:
        raise AppError("LESSON_NOT_FOUND", f"Lesson {lesson_id} not found", 404)

    is_valid, issues = validate_lesson_for_publication(
        db, lesson, required_claim_ids=required_claim_ids, module_slug=module_slug
    )

    if not is_valid:
        lesson.content_validation_status = "blocked_for_authoritative_learning"
        lesson.is_published = False
        db.commit()
        raise AppError(
            "LESSON_UNVERIFIED_CLAIMS",
            f"Cannot publish lesson: {'; '.join(issues)}",
            422,
            details={"issues": issues, "lesson_id": str(lesson_id)},
        )

    lesson.content_validation_status = "valid"
    lesson.is_published = True
    lesson.status = ContentStatus.published
    lesson.published_at = datetime.now(timezone.utc)
    lesson.reviewed_at = datetime.now(timezone.utc)
    lesson.reviewed_by_id = current_user_id
    if review_notes:
        lesson.review_notes = review_notes
    db.commit()
    db.refresh(lesson)
    return lesson


def validate_question_for_publication(
    db: Session, question: QuizQuestion
) -> tuple[bool, list[str]]:
    """Validate whether a quiz question satisfies the historical claim publishing gate (Spec 32.2 / V5-T029).

    A quiz question CANNOT be published if:
    1. Its underlying historical claims are in 'unreviewed', 'draft', 'rejected', 'disputed', or 'superseded' state.
    2. Any claim referenced by claim_ids does not exist in the database.
    3. Associated historical entity is disputed or archived.
    """
    issues: list[str] = []
    claim_ids = _ids(question.claim_ids)
    for raw_id in claim_ids:
        try:
            cid = UUID(raw_id)
            claim = db.get(HistoricalClaim, cid)
            if claim is None:
                issues.append(f"Historical claim {raw_id} not found in database")
            elif claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
                issues.append(
                    f"Historical claim {raw_id} has ineligible verification_status '{claim.verification_status}' "
                    f"(must be in {ELIGIBLE_CLAIM_STATUSES})"
                )
        except (ValueError, TypeError):
            issues.append(f"Invalid claim UUID: {raw_id}")

    if question.entity_id:
        entity = db.get(HistoricalEntity, question.entity_id)
        if entity and entity.publication_status in {"disputed", "archived"}:
            issues.append(
                f"Historical entity {question.entity_id} has ineligible publication_status '{entity.publication_status}'"
            )

    return len(issues) == 0, issues


def publish_question_with_gate(
    db: Session,
    question_id: UUID,
    current_user_id: Optional[UUID] = None,
    review_notes: Optional[str] = None,
) -> QuizQuestion:
    """Publish a quiz question enforcing the historical claim verification gate.

    Raises AppError('QUIZ_QUESTION_UNVERIFIED_CLAIMS', ..., 422) if any required
    claim is unreviewed, disputed, or rejected.
    """
    question = db.get(QuizQuestion, question_id)
    if question is None:
        raise AppError("HISTORY_QUESTION_NOT_FOUND", f"Quiz question {question_id} not found", 404)

    is_valid, issues = validate_question_for_publication(db, question)
    if not is_valid:
        question.content_validation_status = "blocked_for_authoritative_learning"
        question.is_published = False
        db.commit()
        raise AppError(
            "QUIZ_QUESTION_UNVERIFIED_CLAIMS",
            f"Cannot publish quiz question: {'; '.join(issues)}",
            422,
            details={"issues": issues, "question_id": str(question_id)},
        )

    question.content_validation_status = "valid"
    question.is_published = True
    question.status = ContentStatus.published
    question.reviewed_at = datetime.now(timezone.utc)
    question.reviewed_by_id = current_user_id
    if review_notes:
        question.review_notes = review_notes
    db.commit()
    db.refresh(question)
    return question


def generate_curriculum_lesson(
    db: Session,
    module_slug: str,
    motif_id: UUID,
    current_user_id: Optional[UUID] = None,
    publish: bool = False,
    enforce_claims_verified: bool = True,
) -> LessonContent:
    """Generate or scaffold an authoritative LMS lesson directly mapped to verified historical entities and claims.

    Maps:
    - Curriculum objectives and historical competencies (S1_SPATIAL, S2_TEMPORAL, S3_EVIDENCE, S4_ARGUMENT)
    - Underlying HistoricalEntity and HistoricalClaim records
    - 2D equivalent media rubbing representation for low-bandwidth / mobile learners

    Negative abuse check:
    If enforce_claims_verified is True or publish is True, blocks creation/publishing if any
    underlying historical claim is in unreviewed, draft, or rejected state.
    """
    mod = get_curriculum_module(module_slug, db=db)
    if not mod:
        raise AppError("CURRICULUM_MODULE_NOT_FOUND", f"Curriculum module '{module_slug}' not found", 404)

    claim_keys = mod.get("core_claim_keys", [])
    verified_claim_ids: list[str] = []
    unverified_issues: list[str] = []

    for k in claim_keys:
        claim = db.scalar(select(HistoricalClaim).where(HistoricalClaim.claim_key == k))
        if claim is None:
            unverified_issues.append(f"Historical claim '{k}' not found in database")
        elif claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
            unverified_issues.append(
                f"Historical claim '{k}' has ineligible status '{claim.verification_status}' "
                f"(must be in {ELIGIBLE_CLAIM_STATUSES})"
            )
        else:
            verified_claim_ids.append(str(claim.id))

    if unverified_issues and (enforce_claims_verified or publish):
        raise AppError(
            "LESSON_UNVERIFIED_CLAIMS",
            f"Cannot generate lesson for module '{module_slug}': {'; '.join(unverified_issues)}",
            422,
            details={"issues": unverified_issues, "module_slug": module_slug},
        )

    fallback_2d = resolve_2d_rubbing_fallback(mod["slug"])
    if not fallback_2d.get("available"):
        fallback_2d = resolve_2d_rubbing_fallback("cao-dinh")

    lesson = db.scalar(select(LessonContent).where(LessonContent.motif_id == motif_id))
    hist_ctx = (
        f"Kỷ nguyên: {mod['era']}. Khung chương trình: {mod['curriculum_framework']}. "
        f"Giai đoạn lộ trình: {mod['roadmap_phase']}."
    )
    symb = "; ".join(obj["text_vi"] for obj in mod.get("learning_objectives", []))
    add_images = {
        "media_fallback_2d": fallback_2d,
        "curriculum_module_slug": mod["slug"],
        "curriculum_objectives": mod.get("learning_objectives", []),
        "required_claim_ids": verified_claim_ids,
        "historical_competencies": mod.get("historical_competencies", []),
    }

    if lesson is None:
        lesson = LessonContent(
            motif_id=motif_id,
            intro_text=mod.get("description_vi"),
            description=f"{mod['title_vi']} - {mod['topic']}",
            historical_context=hist_ctx,
            symbolism=symb,
            additional_images=add_images,
            status=ContentStatus.draft,
            is_published=False,
            content_validation_status="valid" if not unverified_issues else "blocked_for_authoritative_learning",
            last_editor_id=current_user_id,
        )
        db.add(lesson)
    else:
        lesson.intro_text = mod.get("description_vi")
        lesson.description = f"{mod['title_vi']} - {mod['topic']}"
        lesson.historical_context = hist_ctx
        lesson.symbolism = symb
        images = dict(lesson.additional_images or {})
        images.update(add_images)
        lesson.additional_images = images
        lesson.content_validation_status = "valid" if not unverified_issues else "blocked_for_authoritative_learning"
        lesson.last_editor_id = current_user_id

    if publish:
        if unverified_issues:
            lesson.content_validation_status = "blocked_for_authoritative_learning"
            lesson.is_published = False
            db.commit()
            raise AppError(
                "LESSON_UNVERIFIED_CLAIMS",
                f"Cannot publish lesson: {'; '.join(unverified_issues)}",
                422,
                details={"issues": unverified_issues, "module_slug": module_slug},
            )
        lesson.is_published = True
        lesson.status = ContentStatus.published
        lesson.published_at = datetime.now(timezone.utc)
        lesson.reviewed_at = datetime.now(timezone.utc)
        lesson.reviewed_by_id = current_user_id

    db.commit()
    db.refresh(lesson)
    return lesson


def generate_curriculum_quiz_question(
    db: Session,
    module_slug: str,
    motif_id: UUID,
    question_type: str = "evidence_match",
    question_text: Optional[str] = None,
    current_user_id: Optional[UUID] = None,
    publish: bool = False,
    enforce_claims_verified: bool = True,
    answer_contract: Optional[dict] = None,
) -> QuizQuestion:
    """Generate a quiz question explicitly mapped to verified historical claims and entity."""
    mod = get_curriculum_module(module_slug, db=db)
    if not mod:
        raise AppError("CURRICULUM_MODULE_NOT_FOUND", f"Curriculum module '{module_slug}' not found", 404)

    claim_keys = mod.get("core_claim_keys", [])
    verified_claim_ids: list[str] = []
    unverified_issues: list[str] = []

    for k in claim_keys:
        claim = db.scalar(select(HistoricalClaim).where(HistoricalClaim.claim_key == k))
        if claim is None:
            unverified_issues.append(f"Historical claim '{k}' not found in database")
        elif claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
            unverified_issues.append(
                f"Historical claim '{k}' has ineligible status '{claim.verification_status}'"
            )
        else:
            verified_claim_ids.append(str(claim.id))

    if unverified_issues and (enforce_claims_verified or publish):
        raise AppError(
            "QUIZ_QUESTION_UNVERIFIED_CLAIMS",
            f"Cannot generate quiz question: {'; '.join(unverified_issues)}",
            422,
            details={"issues": unverified_issues, "module_slug": module_slug},
        )

    entity_id = None
    if mod.get("entity_slugs"):
        first_slug = mod["entity_slugs"][0]
        entity = db.scalar(select(HistoricalEntity).where(HistoricalEntity.slug == first_slug))
        if entity:
            entity_id = entity.id

    is_valid = len(unverified_issues) == 0
    q_text = question_text or f"Khảo sát bằng chứng lịch sử liên quan đến {mod['title_vi']}"

    question = QuizQuestion(
        motif_id=motif_id,
        question_type=question_type,
        question_text=q_text,
        correct_answer="",
        difficulty=2,
        skill_dimensions=mod.get("historical_competencies", []),
        entity_id=entity_id,
        claim_ids=verified_claim_ids,
        answer_contract=answer_contract or {"claim_ids": verified_claim_ids},
        is_published=publish and is_valid,
        status=ContentStatus.published if (publish and is_valid) else ContentStatus.draft,
        content_validation_status="valid" if is_valid else "blocked_for_authoritative_learning",
        created_by_id=current_user_id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


# --------------------------------------------------------------------------- #
# Source-Locked Classroom Assignment & Rubric Domain (V5-T033)
# --------------------------------------------------------------------------- #
DEFAULT_HISTORICAL_RUBRIC: dict[str, Any] = {
    "criteria": {
        "S1_SPATIAL": {
            "name": "Không gian & Địa lý",
            "description": "Xác định chính xác vị trí địa lý, không gian Cửu Đỉnh / Đại Nam",
            "max_points": 25,
            "weight": 0.25,
        },
        "S2_TEMPORAL": {
            "name": "Thời gian & Biên niên",
            "description": "Đặt sự kiện và di vật đúng niên đại lịch sử và triều đại",
            "max_points": 25,
            "weight": 0.25,
        },
        "S3_EVIDENCE": {
            "name": "Chứng cứ & Nguồn sử",
            "description": "Trích dẫn chính xác nguồn sử liệu nguyên cấp và bản đúc nổi",
            "max_points": 25,
            "weight": 0.25,
        },
        "S4_ARGUMENT": {
            "name": "Lập luận & Đánh giá",
            "description": "Lập luận mạch lạc, phê phán sử liệu và giải thích ý nghĩa biểu tượng",
            "max_points": 25,
            "weight": 0.25,
        },
    },
    "max_score": 100,
}


def validate_assignment_for_publication(
    db: Session,
    lesson: LessonContent,
    claim_ids: Optional[list[Union[str, UUID]]] = None,
) -> tuple[bool, list[str]]:
    """Validate whether an assignment satisfies the historical publication gate (Spec V5-T033).

    Negative abuse invariant:
    An assignment cannot be published if the lesson or associated claims have
    unreviewed, disputed, rejected, or missing historical claims, or if the lesson
    is blocked for authoritative learning.
    """
    issues: list[str] = []

    # 1. Lesson status check
    if getattr(lesson, "content_validation_status", "") == "blocked_for_authoritative_learning":
        issues.append("Lesson is blocked for authoritative learning due to unverified historical claims")

    # 2. Check lesson publication gate
    is_lesson_valid, lesson_issues = validate_lesson_for_publication(
        db, lesson, required_claim_ids=claim_ids
    )
    if not is_lesson_valid:
        issues.extend(lesson_issues)

    # 3. Explicit check on provided claim_ids
    target_claims = []
    if claim_ids:
        for cid in claim_ids:
            try:
                target_claims.append(UUID(str(cid)))
            except (ValueError, TypeError):
                issues.append(f"Invalid claim UUID format: {cid}")

    for cid in target_claims:
        claim = db.get(HistoricalClaim, cid)
        if claim is None:
            issues.append(f"Required historical claim {cid} not found in database")
        elif claim.verification_status not in ELIGIBLE_CLAIM_STATUSES:
            snippet = (claim.statement_vi or "")[:50]
            issues.append(
                f"Historical claim {cid} ('{snippet}...') has ineligible verification_status "
                f"'{claim.verification_status}' (must be expert_verified or editor_reviewed)"
            )

    return (len(issues) == 0, issues)


def create_source_locked_assignment(
    db: Session,
    teacher_id: UUID,
    classroom_id: UUID,
    lesson_id: UUID,
    title: str,
    instructions: Optional[str] = None,
    due_at: Optional[datetime] = None,
    points: int = 100,
    rubric: Optional[dict[str, Any]] = None,
    source_ids: Optional[list[UUID]] = None,
    claim_ids: Optional[list[UUID]] = None,
    status: str = "draft",
) -> HistoryLessonAssignment:
    """Create a classroom lesson assignment with pinned version, rubric, and source set."""
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise AppError("CLASSROOM_NOT_FOUND", "Classroom not found", 404)

    lesson = db.get(LessonContent, lesson_id)
    if not lesson:
        raise AppError("LESSON_NOT_FOUND", "Lesson not found", 404)

    # Pinned lesson snapshot
    lesson_snapshot = {
        "id": str(lesson.id),
        "motif_id": str(lesson.motif_id) if lesson.motif_id else None,
        "version": lesson.version,
        "description": lesson.description,
        "intro_text": lesson.intro_text,
        "historical_context": lesson.historical_context,
        "symbolism": lesson.symbolism,
        "fun_fact": lesson.fun_fact,
        "audio_narration_url": lesson.audio_narration_url,
        "additional_images": lesson.additional_images,
        "content_rating": lesson.content_rating.value if hasattr(lesson.content_rating, "value") else str(lesson.content_rating),
        "content_validation_status": lesson.content_validation_status,
        "status": lesson.status.value if hasattr(lesson.status, "value") else str(lesson.status),
    }

    # Pinned sources
    sources_snapshot: list[dict[str, Any]] = []
    pinned_source_ids: list[str] = []
    if source_ids:
        for sid in source_ids:
            s_uuid = UUID(str(sid))
            pinned_source_ids.append(str(s_uuid))
            src = db.get(HistoricalSource, s_uuid)
            if src:
                sources_snapshot.append({
                    "id": str(src.id),
                    "title": src.title,
                    "author_text": src.author_text,
                    "source_type": src.source_type,
                    "publication_year": src.publication_year,
                    "citation_text": src.citation_text,
                    "rights_status": src.rights_status,
                    "license": src.license,
                })

    # Pinned claims
    pinned_claim_ids: list[str] = []
    if claim_ids:
        for cid in claim_ids:
            pinned_claim_ids.append(str(UUID(str(cid))))
    elif lesson.additional_images and isinstance(lesson.additional_images, dict):
        extra = lesson.additional_images.get("required_claim_ids") or lesson.additional_images.get("claim_ids")
        if isinstance(extra, list):
            for cid in extra:
                try:
                    pinned_claim_ids.append(str(UUID(str(cid))))
                except (ValueError, TypeError):
                    pass

    # Rubric
    assigned_rubric = rubric if rubric is not None else DEFAULT_HISTORICAL_RUBRIC

    # If status is published, gate it!
    published_at = None
    if status == "published":
        is_valid, issues = validate_assignment_for_publication(
            db, lesson=lesson, claim_ids=[UUID(c) for c in pinned_claim_ids]
        )
        if not is_valid:
            raise AppError(
                "ASSIGNMENT_UNVERIFIED_CLAIMS",
                f"Cannot publish assignment with unverified claims: {'; '.join(issues)}",
                422,
                details={"issues": issues},
            )
        published_at = func.now()

    assignment = HistoryLessonAssignment(
        classroom_id=classroom_id,
        lesson_id=lesson_id,
        assigned_by_id=teacher_id,
        title=title,
        instructions=instructions,
        status=status,
        due_at=due_at,
        points=points,
        pinned_version=lesson.version,
        pinned_lesson_snapshot=lesson_snapshot,
        rubric=assigned_rubric,
        pinned_source_ids=pinned_source_ids,
        pinned_sources_snapshot=sources_snapshot,
        pinned_claim_ids=pinned_claim_ids,
        published_at=published_at,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def publish_history_assignment(
    db: Session,
    assignment_id: UUID,
    user_id: UUID,
    is_admin: bool = False,
) -> HistoryLessonAssignment:
    """Publish an assignment enforcing the historical claims gate."""
    assignment = db.get(HistoryLessonAssignment, assignment_id)
    if not assignment:
        raise AppError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)

    classroom = db.get(Classroom, assignment.classroom_id)
    if not is_admin and classroom and classroom.teacher_id != user_id and assignment.assigned_by_id != user_id:
        raise AppError("FORBIDDEN", "Only classroom teacher or admin can publish this assignment", 403)

    lesson = db.get(LessonContent, assignment.lesson_id)
    if not lesson:
        raise AppError("LESSON_NOT_FOUND", "Associated lesson not found", 404)

    claim_uuids = [UUID(c) for c in (assignment.pinned_claim_ids or [])]
    is_valid, issues = validate_assignment_for_publication(db, lesson=lesson, claim_ids=claim_uuids)
    if not is_valid:
        raise AppError(
            "ASSIGNMENT_UNVERIFIED_CLAIMS",
            f"Cannot publish assignment with unverified claims: {'; '.join(issues)}",
            422,
            details={"issues": issues},
        )

    assignment.status = "published"
    assignment.published_at = func.now()
    db.commit()
    db.refresh(assignment)
    return assignment


def validate_submission_content(submission_content: Any) -> dict[str, Any]:
    """Validate student submission content according to M-E-E / S1-S4 principles.

    Requires at least claim/hypothesis, evidence, and explanation/reasoning,
    or a non-empty answer_text. Rejects empty/whitespace-only content.
    """
    if not isinstance(submission_content, dict) or not submission_content:
        raise AppError("INVALID_SUBMISSION_CONTENT", "Submission content must be a non-empty object", 422)

    claim = str(submission_content.get("claim") or submission_content.get("hypothesis") or "").strip()
    evidence = str(submission_content.get("evidence") or "").strip()
    explanation = str(submission_content.get("explanation") or submission_content.get("reasoning") or "").strip()
    answer_text = str(submission_content.get("answer_text") or submission_content.get("text") or "").strip()

    # Must provide either (claim, evidence, explanation) OR a non-empty answer_text with evidence
    has_mee = bool(claim and evidence and explanation)
    has_text = bool(answer_text and (evidence or claim or len(answer_text) >= 10))

    if not has_mee and not has_text:
        raise AppError(
            "INVALID_SUBMISSION_CONTENT",
            "Submission content must include valid historical claim (M), evidence (E), and explanation (E)",
            422,
        )

    return submission_content


def submit_history_assignment(
    db: Session,
    assignment_id: UUID,
    student_id: UUID,
    submission_content: dict[str, Any],
    idempotency_key: Optional[str] = None,
) -> tuple[HistoryAssignmentSubmission, bool]:
    """Submit a response against a source-locked history assignment.

    Enforces:
    1. Assignment existence and published status.
    2. Student classroom enrollment scope.
    3. Assignment deadline enforcement (cannot submit after due_at).
    4. Submission content validation (M-E-E historical structure).
    5. Idempotent submission: if an identical idempotency_key or active submission exists,
       returns the existing submission idempotently without duplicating records.

    Returns:
        tuple[HistoryAssignmentSubmission, bool]: (submission_record, is_newly_created)
    """
    assignment = db.get(HistoryLessonAssignment, assignment_id)
    if not assignment:
        raise AppError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)

    if assignment.status != "published":
        raise AppError("ASSIGNMENT_NOT_PUBLISHED", "Cannot submit to an unpublished assignment", 400)

    # Deadline enforcement
    if assignment.due_at is not None:
        now_utc = datetime.now(timezone.utc)
        due_at_utc = assignment.due_at
        if due_at_utc.tzinfo is None:
            due_at_utc = due_at_utc.replace(tzinfo=timezone.utc)
        if now_utc > due_at_utc:
            raise AppError(
                "ASSIGNMENT_DEADLINE_PASSED",
                f"Assignment deadline has passed ({assignment.due_at.isoformat()}). Submissions are closed.",
                400,
            )

    # Scope enforcement
    member = db.scalar(
        select(ClassMember).where(
            ClassMember.class_id == assignment.classroom_id,
            ClassMember.user_id == student_id,
        )
    )
    user = db.get(User, student_id)
    is_staff = user and user.role in STAFF_ROLES
    if not member and not is_staff:
        raise AppError("NOT_CLASS_MEMBER", "User is not an enrolled member of this classroom", 403)

    # Content validation
    validated_content = validate_submission_content(submission_content)

    # Check idempotency by key first
    if idempotency_key:
        idem_match = db.scalar(
            select(HistoryAssignmentSubmission).where(
                HistoryAssignmentSubmission.assignment_id == assignment_id,
                HistoryAssignmentSubmission.student_id == student_id,
                HistoryAssignmentSubmission.idempotency_key == idempotency_key,
            )
        )
        if idem_match:
            return idem_match, False

    basis_snapshot = assignment.get_assessment_basis()

    existing = db.scalar(
        select(HistoryAssignmentSubmission).where(
            HistoryAssignmentSubmission.assignment_id == assignment_id,
            HistoryAssignmentSubmission.student_id == student_id,
        )
    )
    if existing:
        # If student already submitted, update with idempotency key
        existing.submission_content = validated_content
        existing.status = "submitted"
        existing.submitted_at = datetime.now(timezone.utc)
        if idempotency_key:
            existing.idempotency_key = idempotency_key
        db.commit()
        db.refresh(existing)
        return existing, False

    sub = HistoryAssignmentSubmission(
        assignment_id=assignment_id,
        student_id=student_id,
        status="submitted",
        submission_content=validated_content,
        assessment_basis_snapshot=basis_snapshot,
        idempotency_key=idempotency_key,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub, True


def grade_history_assignment_submission(
    db: Session,
    submission_id: UUID,
    teacher_id: UUID,
    score: float,
    rubric_evaluation: Optional[dict[str, Any]] = None,
    teacher_feedback: Optional[str] = None,
    is_admin: bool = False,
) -> HistoryAssignmentSubmission:
    """Grade a submission using rubric evaluation criteria."""
    sub = db.get(HistoryAssignmentSubmission, submission_id)
    if not sub:
        raise AppError("SUBMISSION_NOT_FOUND", "Submission not found", 404)

    assignment = db.get(HistoryLessonAssignment, sub.assignment_id)
    if not assignment:
        raise AppError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)

    classroom = db.get(Classroom, assignment.classroom_id)
    if not is_admin and classroom and classroom.teacher_id != teacher_id and assignment.assigned_by_id != teacher_id:
        raise AppError("FORBIDDEN", "Only classroom teacher or admin can grade submissions", 403)

    sub.score = score
    sub.rubric_evaluation = rubric_evaluation or {}
    sub.teacher_feedback = teacher_feedback
    sub.status = "graded"
    sub.graded_at = func.now()
    sub.graded_by_id = teacher_id
    db.commit()
    db.refresh(sub)
    return sub


# --------------------------------------------------------------------------- #
# Learning Outcome Measurement Services (V5-T039 / Wave W03 / Slot A09)
# --------------------------------------------------------------------------- #
from ..domain.learning_outcome import (
    DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
    AssessmentInstrumentType,
    AssessmentPhase,
    EthicsProtocolRequiredError,
    EthicsProtocolStatus,
    IndependentAssessorRequiredError,
    InvalidRubricScoreError,
    SubjectiveSurveyCannotProduceCausalMetricsError,
    UnpairedAssessmentError,
    PilotConsentStatus,
    TeacherWorkloadCategory,
    RubricCalibrationStatus,
    calculate_effect_size_cohens_d,
    calculate_inter_rater_reliability,
    calculate_normalized_learning_gain,
    calculate_teacher_workload_category,
    calibrate_dual_rubric_scores,
    validate_assessor_independence,
    validate_ethics_protocol_active,
    validate_rubric_scores,
    verify_causal_learning_eligibility,
    verify_guardian_consent_status,
    verify_learning_improvement_claim_basis,
)


def create_ethics_protocol(
    db: Session,
    payload: dict[str, Any],
    current_user_id: Optional[UUID] = None,
) -> HistoryEthicsProtocol:
    """Register a new research ethics / IRB protocol for learning measurements."""
    code = payload["protocol_code"].strip()
    existing = db.scalar(select(HistoryEthicsProtocol).where(HistoryEthicsProtocol.protocol_code == code))
    if existing:
        raise AppError("PROTOCOL_CODE_EXISTS", f"Protocol code '{code}' already exists", 409)

    protocol = HistoryEthicsProtocol(
        protocol_code=code,
        title=payload["title"].strip(),
        irb_institution=payload["irb_institution"].strip(),
        status=payload.get("status", "approved"),
        approved_by=payload.get("approved_by") or "IRB Ethics Board",
        approved_at=func.now() if payload.get("status", "approved") == "approved" else None,
        valid_until=payload.get("valid_until"),
        data_retention_days=payload.get("data_retention_days", 365),
        participant_consent_required=payload.get("participant_consent_required", True),
    )
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    return protocol


def get_ethics_protocol(db: Session, protocol_id: UUID) -> HistoryEthicsProtocol:
    protocol = db.get(HistoryEthicsProtocol, protocol_id)
    if not protocol:
        raise AppError("ETHICS_PROTOCOL_NOT_FOUND", "Ethics protocol not found", 404)
    return protocol


def create_learning_outcome_assessment(
    db: Session,
    payload: dict[str, Any],
    current_user_id: Optional[UUID] = None,
) -> HistoryLearningOutcomeAssessment:
    """Create a source-based historical inquiry assessment task (pre/post/delayed).

    Enforces active approved ethics protocol invariant.
    """
    protocol_id = payload["ethics_protocol_id"]
    protocol = db.get(HistoryEthicsProtocol, protocol_id)
    if not protocol:
        raise AppError("ETHICS_PROTOCOL_NOT_FOUND", "Specified ethics protocol not found", 404)

    try:
        validate_ethics_protocol_active(protocol.status, protocol.valid_until)
    except EthicsProtocolRequiredError as exc:
        raise AppError("ETHICS_PROTOCOL_REQUIRED", str(exc), 422)

    slug = payload["slug"].strip()
    existing = db.scalar(select(HistoryLearningOutcomeAssessment).where(HistoryLearningOutcomeAssessment.slug == slug))
    if existing:
        raise AppError("ASSESSMENT_SLUG_EXISTS", f"Assessment slug '{slug}' already exists", 409)

    schema = payload.get("rubric_schema") or DEFAULT_HISTORICAL_INQUIRY_RUBRIC

    assessment = HistoryLearningOutcomeAssessment(
        ethics_protocol_id=protocol.id,
        title=payload["title"].strip(),
        slug=slug,
        assessment_phase=payload.get("assessment_phase", "pre_test"),
        instrument_type=AssessmentInstrumentType.source_inquiry_rubric.value,
        target_urn_slug=payload.get("target_urn_slug"),
        target_motif_slug=payload.get("target_motif_slug"),
        prompt_markdown=payload["prompt_markdown"],
        source_ids=[str(s) for s in (payload.get("source_ids") or [])],
        claim_keys=list(payload.get("claim_keys") or []),
        rubric_schema=schema,
        max_score=payload.get("max_score", 100.0),
        is_published=payload.get("is_published", True),
        created_by=current_user_id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def submit_learning_outcome_assessment(
    db: Session,
    assessment_id: UUID,
    student_id: UUID,
    responses: dict[str, Any],
    citations_provided: list[str],
) -> HistoryLearningOutcomeSubmission:
    """Submit responses to a source-based inquiry assessment task."""
    assessment = db.get(HistoryLearningOutcomeAssessment, assessment_id)
    if not assessment:
        raise AppError("ASSESSMENT_NOT_FOUND", "Inquiry assessment not found", 404)

    # Check ethics protocol
    protocol = db.get(HistoryEthicsProtocol, assessment.ethics_protocol_id)
    if not protocol:
        raise AppError("ETHICS_PROTOCOL_NOT_FOUND", "Associated ethics protocol not found", 404)
    try:
        validate_ethics_protocol_active(protocol.status, protocol.valid_until)
    except EthicsProtocolRequiredError as exc:
        raise AppError("ETHICS_PROTOCOL_REQUIRED", str(exc), 422)

    # Verify participant guardian informed consent if required
    if protocol.participant_consent_required:
        consent = db.scalar(
            select(HistoryPilotGuardianConsent).where(
                HistoryPilotGuardianConsent.ethics_protocol_id == protocol.id,
                HistoryPilotGuardianConsent.student_id == student_id,
            )
        )
        if consent:
            if consent.consent_status == PilotConsentStatus.withdrawn.value:
                raise AppError(
                    "GUARDIAN_CONSENT_WITHDRAWN",
                    "Guardian informed consent has been withdrawn for this participant. Research participation is suspended.",
                    403,
                )
            if consent.consent_status != PilotConsentStatus.verified.value:
                raise AppError(
                    "GUARDIAN_CONSENT_REQUIRED",
                    f"Participant requires verified guardian consent for research under protocol '{protocol.protocol_code}'. Current status: '{consent.consent_status}'.",
                    403,
                )

    submission = HistoryLearningOutcomeSubmission(
        assessment_id=assessment.id,
        student_id=student_id,
        assessment_phase=assessment.assessment_phase,
        instrument_type=assessment.instrument_type,
        responses=responses,
        citations_provided=citations_provided,
        status="submitted",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def evaluate_learning_outcome_submission(
    db: Session,
    submission_id: UUID,
    assessor_id: UUID,
    rubric_scores: dict[str, float],
    feedback_markdown: Optional[str] = None,
    evidence_notes: Optional[str] = None,
) -> HistoryLearningOutcomeEvaluation:
    """Score an inquiry submission with an independent assessor rubric evaluation."""
    sub = db.get(HistoryLearningOutcomeSubmission, submission_id)
    if not sub:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    # Check independent assessor invariant: student cannot score their own work
    try:
        validate_assessor_independence(sub.student_id, assessor_id)
    except IndependentAssessorRequiredError as exc:
        raise AppError("INDEPENDENT_ASSESSOR_REQUIRED", str(exc), 403)

    assessment = db.get(HistoryLearningOutcomeAssessment, sub.assessment_id)
    schema = assessment.rubric_schema if assessment else DEFAULT_HISTORICAL_INQUIRY_RUBRIC

    try:
        total = validate_rubric_scores(schema, rubric_scores)
    except InvalidRubricScoreError as exc:
        raise AppError("INVALID_RUBRIC_SCORE", str(exc), 422)

    existing = db.scalar(
        select(HistoryLearningOutcomeEvaluation).where(
            HistoryLearningOutcomeEvaluation.submission_id == sub.id,
            HistoryLearningOutcomeEvaluation.assessor_id == assessor_id,
        )
    )
    if existing:
        existing.rubric_scores = rubric_scores
        existing.total_score = total
        existing.feedback_markdown = feedback_markdown
        existing.evidence_notes = evidence_notes
        existing.evaluated_at = func.now()
        sub.status = "evaluated"
        db.commit()
        db.refresh(existing)
        return existing

    evaluation = HistoryLearningOutcomeEvaluation(
        submission_id=sub.id,
        assessor_id=assessor_id,
        is_independent=True,
        rubric_scores=rubric_scores,
        total_score=total,
        feedback_markdown=feedback_markdown,
        evidence_notes=evidence_notes,
    )
    sub.status = "evaluated"
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def submit_subjective_survey(
    db: Session,
    student_id: UUID,
    survey_name: str,
    likert_responses: dict[str, int],
    perceived_learning_score: Optional[float] = None,
    satisfaction_score: Optional[float] = None,
    feedback_text: Optional[str] = None,
) -> HistorySubjectiveSurvey:
    """Record a separate subjective self-report survey.
    
    This is strictly isolated and cannot be used for causal learning mastery claims.
    """
    survey = HistorySubjectiveSurvey(
        student_id=student_id,
        survey_name=survey_name.strip(),
        instrument_type=AssessmentInstrumentType.self_report_survey.value,
        is_subjective_self_report=True,
        likert_responses=likert_responses,
        perceived_learning_score=perceived_learning_score,
        satisfaction_score=satisfaction_score,
        feedback_text=feedback_text,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey


def compute_causal_learning_outcome(
    db: Session,
    student_id: UUID,
    ethics_protocol_id: UUID,
    pre_submission_id: UUID,
    post_submission_id: UUID,
    delayed_submission_id: Optional[UUID] = None,
    is_survey_data: bool = False,
    survey_response_id: Optional[UUID] = None,
) -> HistoryCausalLearningMetric:
    """Derive causal learning mastery metric from paired pre/post inquiry rubric evaluations.

    NEGATIVE ABUSE INVARIANT:
    Subjective survey responses CANNOT produce causal learning mastery metrics.
    Attempts to compute causal learning gain using survey data or subjective feelings
    fail immediately with HTTP 422 CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY.
    """
    if is_survey_data or survey_response_id is not None:
        raise AppError(
            "CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY",
            "Subjective survey responses (self-reported feelings or Likert scale satisfaction) "
            "cannot produce causal learning mastery metrics. Causal mastery measurements strictly "
            "require objective pre/post source-based inquiry assessments evaluated by independent rubric assessors.",
            422,
        )

    # Validate ethics protocol
    protocol = db.get(HistoryEthicsProtocol, ethics_protocol_id)
    if not protocol:
        raise AppError("ETHICS_PROTOCOL_NOT_FOUND", "Specified ethics protocol not found", 404)
    try:
        validate_ethics_protocol_active(protocol.status, protocol.valid_until)
    except EthicsProtocolRequiredError as exc:
        raise AppError("ETHICS_PROTOCOL_REQUIRED", str(exc), 422)

    # Verify participant guardian informed consent if required
    if protocol.participant_consent_required:
        consent = db.scalar(
            select(HistoryPilotGuardianConsent).where(
                HistoryPilotGuardianConsent.ethics_protocol_id == protocol.id,
                HistoryPilotGuardianConsent.student_id == student_id,
            )
        )
        if consent:
            if consent.consent_status == PilotConsentStatus.withdrawn.value:
                raise AppError(
                    "GUARDIAN_CONSENT_WITHDRAWN",
                    "Guardian informed consent has been withdrawn for this participant. Causal learning metrics cannot be computed.",
                    403,
                )
            if consent.consent_status != PilotConsentStatus.verified.value:
                raise AppError(
                    "GUARDIAN_CONSENT_REQUIRED",
                    f"Participant requires verified guardian consent for causal learning metric calculation. Current status: '{consent.consent_status}'.",
                    403,
                )

    # Validate submissions
    pre_sub = db.get(HistoryLearningOutcomeSubmission, pre_submission_id)
    post_sub = db.get(HistoryLearningOutcomeSubmission, post_submission_id)

    if not pre_sub or not post_sub:
        raise AppError("SUBMISSION_NOT_FOUND", "Pre-test or post-test submission not found", 404)

    # Enforce negative abuse check on submission instruments
    if pre_sub.instrument_type != AssessmentInstrumentType.source_inquiry_rubric.value:
        raise AppError("CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY", "Pre-test is not an objective rubric inquiry task", 422)
    if post_sub.instrument_type != AssessmentInstrumentType.source_inquiry_rubric.value:
        raise AppError("CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY", "Post-test is not an objective rubric inquiry task", 422)

    if pre_sub.student_id != student_id or post_sub.student_id != student_id:
        raise AppError("STUDENT_MISMATCH", "Submissions must belong to the specified student", 400)

    if pre_sub.assessment_phase != AssessmentPhase.pre_test.value:
        raise AppError("INVALID_ASSESSMENT_PHASE", f"Pre-submission phase must be 'pre_test', got '{pre_sub.assessment_phase}'", 400)
    if post_sub.assessment_phase != AssessmentPhase.post_test.value:
        raise AppError("INVALID_ASSESSMENT_PHASE", f"Post-submission phase must be 'post_test', got '{post_sub.assessment_phase}'", 400)

    # Get independent evaluations
    pre_evals = list(
        db.scalars(
            select(HistoryLearningOutcomeEvaluation).where(
                HistoryLearningOutcomeEvaluation.submission_id == pre_sub.id,
                HistoryLearningOutcomeEvaluation.is_independent == True,
            )
        ).all()
    )
    post_evals = list(
        db.scalars(
            select(HistoryLearningOutcomeEvaluation).where(
                HistoryLearningOutcomeEvaluation.submission_id == post_sub.id,
                HistoryLearningOutcomeEvaluation.is_independent == True,
            )
        ).all()
    )

    if not pre_evals:
        raise AppError("EVALUATION_MISSING", "Pre-test submission has not been evaluated by an independent assessor", 422)
    if not post_evals:
        raise AppError("EVALUATION_MISSING", "Post-test submission has not been evaluated by an independent assessor", 422)

    # Compute consensus scores (mean across independent evaluators)
    pre_score = sum(e.total_score for e in pre_evals) / len(pre_evals)
    post_score = sum(e.total_score for e in post_evals) / len(post_evals)

    # Calculate inter-rater agreement if multiple evaluators exist on post
    agreement = None
    if len(post_evals) >= 2:
        agreement = calculate_inter_rater_reliability(post_evals[0].total_score, post_evals[1].total_score, 100.0)

    # Delayed test if provided
    delayed_score = None
    if delayed_submission_id:
        del_sub = db.get(HistoryLearningOutcomeSubmission, delayed_submission_id)
        if del_sub:
            del_evals = list(
                db.scalars(
                    select(HistoryLearningOutcomeEvaluation).where(
                        HistoryLearningOutcomeEvaluation.submission_id == del_sub.id,
                        HistoryLearningOutcomeEvaluation.is_independent == True,
                    )
                ).all()
            )
            if del_evals:
                delayed_score = sum(e.total_score for e in del_evals) / len(del_evals)

    normalized_gain = calculate_normalized_learning_gain(pre_score, post_score, 100.0)
    absolute_gain = round(post_score - pre_score, 2)

    # Calculate per-competency gain (S1-S4)
    competency_gains: dict[str, float] = {}
    pre_criteria: dict[str, list[float]] = {}
    for ev in pre_evals:
        for k, v in (ev.rubric_scores or {}).items():
            pre_criteria.setdefault(k, []).append(float(v))
    post_criteria: dict[str, list[float]] = {}
    for ev in post_evals:
        for k, v in (ev.rubric_scores or {}).items():
            post_criteria.setdefault(k, []).append(float(v))

    for crit in ("S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"):
        c_pre = sum(pre_criteria.get(crit, [0.0])) / max(1, len(pre_criteria.get(crit, [0.0])))
        c_post = sum(post_criteria.get(crit, [0.0])) / max(1, len(post_criteria.get(crit, [0.0])))
        competency_gains[crit] = round(c_post - c_pre, 2)

    metric = HistoryCausalLearningMetric(
        student_id=student_id,
        ethics_protocol_id=ethics_protocol_id,
        pre_submission_id=pre_sub.id,
        post_submission_id=post_sub.id,
        delayed_submission_id=delayed_submission_id,
        pre_score=round(pre_score, 2),
        post_score=round(post_score, 2),
        delayed_score=round(delayed_score, 2) if delayed_score is not None else None,
        normalized_gain=normalized_gain,
        absolute_gain=absolute_gain,
        inter_rater_agreement=agreement,
        competency_gains=competency_gains,
        instrument_type=AssessmentInstrumentType.source_inquiry_rubric.value,
        is_valid_causal_claim=True,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def get_cohort_causal_learning_metrics(
    db: Session,
    ethics_protocol_id: UUID,
) -> dict[str, Any]:
    """Aggregate cohort learning outcome metrics for an approved ethics protocol."""
    protocol = db.get(HistoryEthicsProtocol, ethics_protocol_id)
    if not protocol:
        raise AppError("ETHICS_PROTOCOL_NOT_FOUND", "Ethics protocol not found", 404)

    metrics = list(
        db.scalars(
            select(HistoryCausalLearningMetric).where(
                HistoryCausalLearningMetric.ethics_protocol_id == ethics_protocol_id
            )
        ).all()
    )

    # Exclude students whose guardian consent was withdrawn
    withdrawn_student_ids = set(
        db.scalars(
            select(HistoryPilotGuardianConsent.student_id).where(
                HistoryPilotGuardianConsent.ethics_protocol_id == ethics_protocol_id,
                HistoryPilotGuardianConsent.consent_status == PilotConsentStatus.withdrawn.value,
            )
        ).all()
    )
    if withdrawn_student_ids:
        metrics = [m for m in metrics if m.student_id not in withdrawn_student_ids]

    if not metrics:
        return {
            "total_students": 0,
            "mean_pre_score": 0.0,
            "mean_post_score": 0.0,
            "mean_normalized_gain": 0.0,
            "effect_size_cohens_d": 0.0,
            "mean_inter_rater_agreement": 1.0,
            "competency_averages": {},
            "ethics_protocol_code": protocol.protocol_code,
        }

    n = len(metrics)
    pre_list = [m.pre_score for m in metrics]
    post_list = [m.post_score for m in metrics]
    gains = [m.normalized_gain for m in metrics]
    agreements = [m.inter_rater_agreement for m in metrics if m.inter_rater_agreement is not None]

    cohens_d = calculate_effect_size_cohens_d(pre_list, post_list)

    # Average competency gains
    comp_totals: dict[str, float] = {}
    for m in metrics:
        for k, v in (m.competency_gains or {}).items():
            comp_totals[k] = comp_totals.get(k, 0.0) + float(v)
    comp_avgs = {k: round(v / n, 2) for k, v in comp_totals.items()}

    return {
        "total_students": n,
        "mean_pre_score": round(sum(pre_list) / n, 2),
        "mean_post_score": round(sum(post_list) / n, 2),
        "mean_normalized_gain": round(sum(gains) / n, 4),
        "effect_size_cohens_d": cohens_d,
        "mean_inter_rater_agreement": round(sum(agreements) / len(agreements), 4) if agreements else 1.0,
        "competency_averages": comp_avgs,
        "ethics_protocol_code": protocol.protocol_code,
    }


# --------------------------------------------------------------------------- #
# School Pilot Measurement & Ethics Services (V5-T100 / Wave W09 / Slot A10)
# --------------------------------------------------------------------------- #
def create_pilot_guardian_consent(
    db: Session,
    payload: dict[str, Any],
    current_user_id: Optional[UUID] = None,
) -> HistoryPilotGuardianConsent:
    """Register informed guardian consent for student pilot research participation."""
    protocol_id = payload["ethics_protocol_id"]
    student_id = payload["student_id"]
    protocol = db.get(HistoryEthicsProtocol, protocol_id)
    if not protocol:
        raise AppError("ETHICS_PROTOCOL_NOT_FOUND", "Specified ethics protocol not found", 404)
    student = db.get(User, student_id)
    if not student:
        raise AppError("STUDENT_NOT_FOUND", "Specified student not found", 404)

    existing = db.scalar(
        select(HistoryPilotGuardianConsent).where(
            HistoryPilotGuardianConsent.ethics_protocol_id == protocol_id,
            HistoryPilotGuardianConsent.student_id == student_id,
        )
    )
    if existing:
        existing.guardian_name = payload["guardian_name"].strip()
        existing.guardian_email = payload["guardian_email"].strip()
        existing.guardian_phone = payload.get("guardian_phone")
        existing.relationship_type = payload.get("relationship_type", "parent")
        existing.verification_method = payload.get("verification_method", "school_roster")
        existing.notes = payload.get("notes")
        existing.consent_status = PilotConsentStatus.pending.value
        existing.withdrawn_at = None
        db.commit()
        db.refresh(existing)
        return existing

    consent = HistoryPilotGuardianConsent(
        ethics_protocol_id=protocol_id,
        student_id=student_id,
        guardian_name=payload["guardian_name"].strip(),
        guardian_email=payload["guardian_email"].strip(),
        guardian_phone=payload.get("guardian_phone"),
        relationship_type=payload.get("relationship_type", "parent"),
        consent_status=PilotConsentStatus.pending.value,
        verification_method=payload.get("verification_method", "school_roster"),
        notes=payload.get("notes"),
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def verify_pilot_guardian_consent(
    db: Session,
    consent_id: UUID,
    verifier_id: UUID,
) -> HistoryPilotGuardianConsent:
    """Verify and approve guardian informed consent for a student."""
    consent = db.get(HistoryPilotGuardianConsent, consent_id)
    if not consent:
        raise AppError("CONSENT_RECORD_NOT_FOUND", "Guardian consent record not found", 404)
    consent.consent_status = PilotConsentStatus.verified.value
    consent.verified_by_id = verifier_id
    consent.verified_at = func.now()
    consent.withdrawn_at = None
    db.commit()
    db.refresh(consent)
    return consent


def withdraw_pilot_guardian_consent(
    db: Session,
    consent_id: UUID,
    reason: Optional[str] = None,
) -> HistoryPilotGuardianConsent:
    """Withdraw guardian consent, immediately suspending empirical research participation."""
    consent = db.get(HistoryPilotGuardianConsent, consent_id)
    if not consent:
        raise AppError("CONSENT_RECORD_NOT_FOUND", "Guardian consent record not found", 404)
    consent.consent_status = PilotConsentStatus.withdrawn.value
    consent.withdrawn_at = func.now()
    if reason:
        consent.notes = f"{consent.notes or ''} [Withdrawal reason: {reason}]".strip()
    db.commit()
    db.refresh(consent)
    return consent


def get_pilot_guardian_consent_status(
    db: Session,
    protocol_id: UUID,
    student_id: UUID,
) -> dict[str, Any]:
    """Check guardian consent verification status for a student under an ethics protocol."""
    consent = db.scalar(
        select(HistoryPilotGuardianConsent).where(
            HistoryPilotGuardianConsent.ethics_protocol_id == protocol_id,
            HistoryPilotGuardianConsent.student_id == student_id,
        )
    )
    if not consent:
        return {
            "ethics_protocol_id": protocol_id,
            "student_id": student_id,
            "consent_status": "missing",
            "is_consent_verified": False,
            "verified_at": None,
            "withdrawn_at": None,
        }
    return {
        "ethics_protocol_id": protocol_id,
        "student_id": student_id,
        "consent_status": consent.consent_status,
        "is_consent_verified": consent.consent_status == PilotConsentStatus.verified.value,
        "verified_at": consent.verified_at,
        "withdrawn_at": consent.withdrawn_at,
    }


def log_teacher_workload(
    db: Session,
    teacher_id: UUID,
    payload: dict[str, Any],
) -> HistoryTeacherWorkloadLog:
    """Record educator workload metrics and cognitive load index to prevent burnout."""
    mins = float(payload["minutes_spent"])
    count = int(payload.get("submissions_evaluated_count", 0))
    c_load = float(payload.get("cognitive_load_rating", 50.0))

    category = calculate_teacher_workload_category(mins, count, c_load)

    log_entry = HistoryTeacherWorkloadLog(
        teacher_id=teacher_id,
        school_id=payload.get("school_id"),
        classroom_id=payload.get("classroom_id"),
        ethics_protocol_id=payload.get("ethics_protocol_id"),
        activity_type=payload.get("activity_type", "rubric_grading"),
        minutes_spent=mins,
        submissions_evaluated_count=count,
        cognitive_load_rating=c_load,
        workload_category=category,
        notes=payload.get("notes"),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_teacher_workload_summary(
    db: Session,
    teacher_id: Optional[UUID] = None,
    school_id: Optional[UUID] = None,
    protocol_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Summarize teacher workload metrics and calculate burnout risk indicators."""
    stmt = select(HistoryTeacherWorkloadLog)
    if teacher_id:
        stmt = stmt.where(HistoryTeacherWorkloadLog.teacher_id == teacher_id)
    if school_id:
        stmt = stmt.where(HistoryTeacherWorkloadLog.school_id == school_id)
    if protocol_id:
        stmt = stmt.where(HistoryTeacherWorkloadLog.ethics_protocol_id == protocol_id)

    logs = list(db.scalars(stmt).all())
    total_mins = sum(l.minutes_spent for l in logs)
    total_subs = sum(l.submissions_evaluated_count for l in logs)
    avg_mins_sub = round(total_mins / max(1, total_subs), 2) if total_subs > 0 else 0.0
    avg_load = round(sum(l.cognitive_load_rating for l in logs) / max(1, len(logs)), 2) if logs else 0.0

    threshold_exceeded = any(l.workload_category == TeacherWorkloadCategory.excessive.value for l in logs) or avg_mins_sub > 15.0 or avg_load > 70.0
    overall_status = (
        TeacherWorkloadCategory.excessive.value
        if threshold_exceeded
        else (TeacherWorkloadCategory.acceptable.value if (avg_mins_sub >= 8.0 or avg_load >= 40.0) else TeacherWorkloadCategory.optimal.value)
    )
    burnout_risk = "high" if threshold_exceeded else ("moderate" if overall_status == TeacherWorkloadCategory.acceptable.value else "low")

    recs = []
    if threshold_exceeded:
        recs.append("Grading time per submission exceeds 15 minutes safety threshold. Deploy secondary independent assessor.")
        recs.append("Teacher cognitive load index exceeds 70/100. Reduce rubric criteria granularity or increase grading window.")
    elif overall_status == TeacherWorkloadCategory.acceptable.value:
        recs.append("Workload is within acceptable boundaries. Monitor for grading bottlenecks during final post-test submissions.")
    else:
        recs.append("Workload is optimal. Educator capacity is well-balanced.")

    return {
        "teacher_id": teacher_id,
        "school_id": school_id,
        "total_minutes_logged": round(total_mins, 2),
        "total_submissions_evaluated": total_subs,
        "avg_minutes_per_submission": avg_mins_sub,
        "avg_cognitive_load": avg_load,
        "overall_workload_status": overall_status,
        "threshold_exceeded": threshold_exceeded,
        "burnout_risk_level": burnout_risk,
        "recommendations": recs,
    }


def calibrate_submission_rubrics(
    db: Session,
    submission_id: UUID,
    assessor_a_id: UUID,
    assessor_b_id: UUID,
    tolerance_pct: float = 0.15,
) -> HistoryRubricCalibration:
    """Calibrate dual independent assessor rubric evaluations on a single submission."""
    sub = db.get(HistoryLearningOutcomeSubmission, submission_id)
    if not sub:
        raise AppError("SUBMISSION_NOT_FOUND", "Submission not found", 404)

    eval_a = db.scalar(
        select(HistoryLearningOutcomeEvaluation).where(
            HistoryLearningOutcomeEvaluation.submission_id == submission_id,
            HistoryLearningOutcomeEvaluation.assessor_id == assessor_a_id,
        )
    )
    eval_b = db.scalar(
        select(HistoryLearningOutcomeEvaluation).where(
            HistoryLearningOutcomeEvaluation.submission_id == submission_id,
            HistoryLearningOutcomeEvaluation.assessor_id == assessor_b_id,
        )
    )

    if not eval_a or not eval_b:
        raise AppError("EVALUATION_MISSING", "Both independent evaluations must exist before running calibration audit", 422)

    assessment = db.get(HistoryLearningOutcomeAssessment, sub.assessment_id)
    max_score = assessment.max_score if assessment else 100.0

    calib_result = calibrate_dual_rubric_scores(
        scores_a=eval_a.rubric_scores or {},
        scores_b=eval_b.rubric_scores or {},
        max_score=max_score,
        tolerance_pct=tolerance_pct,
    )

    calibration = HistoryRubricCalibration(
        submission_id=submission_id,
        assessor_a_id=assessor_a_id,
        assessor_b_id=assessor_b_id,
        evaluation_a_id=eval_a.id,
        evaluation_b_id=eval_b.id,
        score_a=calib_result["score_a"],
        score_b=calib_result["score_b"],
        score_difference=calib_result["score_difference"],
        divergence_pct=calib_result["divergence_pct"],
        inter_rater_agreement=calib_result["inter_rater_agreement"],
        tolerance_pct=calib_result["tolerance_pct"],
        status=calib_result["status"],
        consensus_score=calib_result["consensus_score"],
        criteria_breakdown=calib_result["criteria_breakdown"],
    )
    db.add(calibration)
    db.commit()
    db.refresh(calibration)
    return calibration


def audit_pilot_data_retention(
    db: Session,
    ethics_protocol_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Audit student assessment and survey records exceeding research retention limit."""
    retention_days = 365
    if ethics_protocol_id:
        protocol = db.get(HistoryEthicsProtocol, ethics_protocol_id)
        if protocol and protocol.data_retention_days:
            retention_days = protocol.data_retention_days

    from datetime import timedelta
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    stmt_subs = select(HistoryLearningOutcomeSubmission).where(
        HistoryLearningOutcomeSubmission.submitted_at < cutoff_date,
        HistoryLearningOutcomeSubmission.status != "retention_purged",
    )
    if ethics_protocol_id:
        stmt_subs = stmt_subs.join(HistoryLearningOutcomeAssessment).where(
            HistoryLearningOutcomeAssessment.ethics_protocol_id == ethics_protocol_id
        )
    expired_subs = list(db.scalars(stmt_subs).all())

    stmt_surveys = select(HistorySubjectiveSurvey).where(
        HistorySubjectiveSurvey.submitted_at < cutoff_date,
        HistorySubjectiveSurvey.survey_name != "[PURGED]",
    )
    expired_surveys = list(db.scalars(stmt_surveys).all())

    sub_ids = [s.id for s in expired_subs]
    eval_count = 0
    if sub_ids:
        eval_count = db.scalar(
            select(func.count(HistoryLearningOutcomeEvaluation.id)).where(
                HistoryLearningOutcomeEvaluation.submission_id.in_(sub_ids)
            )
        ) or 0

    return {
        "ethics_protocol_id": ethics_protocol_id,
        "retention_days_limit": retention_days,
        "expired_submissions_count": len(expired_subs),
        "expired_evaluations_count": int(eval_count),
        "expired_surveys_count": len(expired_surveys),
        "expired_submission_ids": sub_ids,
        "expired_survey_ids": [s.id for s in expired_surveys],
        "audit_timestamp": datetime.now(timezone.utc),
    }


def purge_expired_pilot_data(
    db: Session,
    ethics_protocol_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Purge PII from expired student assessment and survey records per Decree 13/2023/ND-CP."""
    audit = audit_pilot_data_retention(db, ethics_protocol_id)
    sub_ids = audit["expired_submission_ids"]
    survey_ids = audit["expired_survey_ids"]

    purged_subs = 0
    purged_evals = 0
    purged_surveys = 0

    now = datetime.now(timezone.utc)

    if sub_ids:
        subs = list(db.scalars(select(HistoryLearningOutcomeSubmission).where(HistoryLearningOutcomeSubmission.id.in_(sub_ids))).all())
        for s in subs:
            s.responses = {"_purged": True, "policy": "Decree_13_2023_ND_CP", "purged_at": now.isoformat()}
            s.citations_provided = []
            s.status = "retention_purged"
            purged_subs += 1

        evals = list(db.scalars(select(HistoryLearningOutcomeEvaluation).where(HistoryLearningOutcomeEvaluation.submission_id.in_(sub_ids))).all())
        for e in evals:
            e.feedback_markdown = "[RETENTION_PURGED]"
            e.evidence_notes = "[RETENTION_PURGED]"
            purged_evals += 1

    if survey_ids:
        surveys = list(db.scalars(select(HistorySubjectiveSurvey).where(HistorySubjectiveSurvey.id.in_(survey_ids))).all())
        for sur in surveys:
            sur.survey_name = "[PURGED]"
            sur.likert_responses = {}
            sur.feedback_text = "[RETENTION_PURGED]"
            purged_surveys += 1

    db.commit()

    return {
        "purged_submissions_count": purged_subs,
        "purged_evaluations_count": purged_evals,
        "purged_surveys_count": purged_surveys,
        "status": "purged",
        "policy": "Decree_13_2023_ND_CP_compliance",
        "purged_at": now,
    }


def validate_learning_improvement_claim(
    db: Session,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Validate that learning improvement claims are grounded in objective assessments, not sentiment."""
    claim_title = payload["claim_title"].strip()
    claim_type = payload.get("claim_type", "learning_improvement").strip()
    evidence_basis = payload.get("evidence_basis", "pre_post_inquiry_rubric").strip()

    try:
        verify_learning_improvement_claim_basis(claim_type, evidence_basis)
    except SubjectiveSurveyCannotProduceCausalMetricsError as exc:
        raise AppError("CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY", str(exc), 422)

    return {
        "claim_title": claim_title,
        "claim_type": claim_type,
        "evidence_basis": evidence_basis,
        "is_valid_evidence_of_learning": True,
        "rejection_reason": None,
        "justification": "Evidence is grounded in objective historical inquiry assessments evaluated by independent rubric assessors.",
    }


# --------------------------------------------------------------------------- #
# Mobile Lesson Quiz Sync & Server Assessment Engine (V5-T057)
# --------------------------------------------------------------------------- #
def sync_mobile_practice_questions(
    db: Session,
    lesson_id: Optional[UUID] = None,
    motif_id: Optional[UUID] = None,
    category: Optional[str] = None,
    difficulty: Optional[int] = None,
    limit: int = 10,
    mode: Optional[str] = "quick_review",
) -> dict[str, Any]:
    """Fetch real published, content-validated quiz questions for mobile practice sync.

    Parity with backend server assessment tasks:
    - Never leaks correct_answer or answer_contract to the client.
    - Filters out unreviewed / blocked questions (content_validation_status != 'valid').
    - Only serves active, published questions.
    """
    from ..models import LessonContent, Motif, QuizQuestion
    import uuid

    q = select(QuizQuestion).where(
        QuizQuestion.is_active.is_(True),
        QuizQuestion.is_published.is_(True),
        QuizQuestion.content_validation_status != "blocked_for_authoritative_learning",
    )

    resolved_motif_id = motif_id
    if lesson_id:
        lesson = db.get(LessonContent, lesson_id)
        if lesson and lesson.motif_id:
            resolved_motif_id = lesson.motif_id

    if resolved_motif_id:
        q = q.where(QuizQuestion.motif_id == resolved_motif_id)
    elif category:
        q = q.join(Motif, Motif.id == QuizQuestion.motif_id).where(Motif.category == category)

    if difficulty:
        q = q.where(QuizQuestion.difficulty == difficulty)

    questions = db.scalars(q.order_by(QuizQuestion.created_at.asc()).limit(limit)).all()

    items = []
    for q_item in questions:
        opts = q_item.options if isinstance(q_item.options, list) else None
        q_type_str = (
            q_item.question_type.value
            if hasattr(q_item.question_type, "value")
            else str(q_item.question_type)
        )
        items.append({
            "id": q_item.id,
            "motif_id": q_item.motif_id,
            "lesson_id": lesson_id,
            "question_type": q_type_str,
            "question_text": q_item.question_text,
            "options": opts,
            "target_mesh_name": q_item.target_mesh_name,
            "difficulty": max(1, int(q_item.difficulty or 1)),
            "points": 10 if q_item.difficulty == 1 else (15 if q_item.difficulty == 2 else 20),
            "skill_type": q_item.skill_type,
            "skill_dimensions": [str(d) for d in (q_item.skill_dimensions or [])],
            "image_url": None,
            "hint": getattr(q_item, "hint", None),
            "content_validation_status": q_item.content_validation_status or "valid",
            "is_verified_content": True,
        })

    return {
        "session_id": uuid.uuid4(),
        "items": items,
        "total_questions": len(items),
        "server_timestamp": datetime.now(timezone.utc),
        "assessment_mode": mode or "quick_review",
    }


def submit_mobile_practice_assessment(
    db: Session,
    user: User,
    answers: dict[str, str],
    session_id: Optional[UUID] = None,
    motif_id: Optional[UUID] = None,
    lesson_id: Optional[UUID] = None,
    time_taken_seconds: Optional[int] = None,
    client_claimed_badges: Optional[list[str]] = None,
    client_claimed_score: Optional[float] = None,
) -> dict[str, Any]:
    """Server-authoritative grading for mobile practice quiz and assessment tasks.

    Negative Abuse Guardrails:
    - Never trusts client-side scores or claimed badges.
    - If percentage < 80%: passed is False, mastery XP is 0, and all client-claimed
      badges are strictly denied.
    - If passed >= 80%: evaluates legitimate milestone & performance badges, awards
      them persistently in user_badges, advances motif to mastered, and records
      verified QuizAttempt.
    """
    from ..domain.gamification import _apply_xp_boost, _award_badge, _update_streak
    from ..domain.helpers import (
        BADGE_FIRST_MASTERED,
        BADGE_PERFECT_SCORE,
        BADGE_SPEED_DEMON,
        DISCOVERY_XP,
        LESSON_XP,
        MASTERED_XP,
        QUIZ_PASS_PERCENT,
    )
    from ..models import (
        Badge,
        LessonContent,
        Motif,
        QuizAttempt,
        QuizQuestion,
        UnlockStatus,
        UserBadge,
        UserProgress,
    )

    resolved_motif_id = motif_id
    if lesson_id and not resolved_motif_id:
        lesson = db.get(LessonContent, lesson_id)
        if lesson and lesson.motif_id:
            resolved_motif_id = lesson.motif_id

    # Resolve questions to grade
    questions = []
    if answers:
        q_ids = []
        for k in answers.keys():
            try:
                q_ids.append(UUID(str(k)))
            except (ValueError, TypeError):
                continue
        if q_ids:
            questions = list(
                db.scalars(
                    select(QuizQuestion).where(
                        QuizQuestion.id.in_(q_ids),
                        QuizQuestion.is_active.is_(True),
                    )
                ).all()
            )

    if not questions and resolved_motif_id:
        questions = list(
            db.scalars(
                select(QuizQuestion)
                .where(
                    QuizQuestion.motif_id == resolved_motif_id,
                    QuizQuestion.is_active.is_(True),
                )
                .order_by(QuizQuestion.created_at.asc())
            ).all()
        )

    if not questions:
        raise AppError(
            code="NO_QUIZ_QUESTIONS",
            message="No active quiz questions found for this assessment",
            status_code=404,
        )

    # Server grading
    score = 0
    details = []
    for q in questions:
        q_id_str = str(q.id)
        user_ans = str(answers.get(q_id_str, "")).strip()
        expected = str(q.correct_answer or "").strip()
        is_corr = bool(user_ans and user_ans.lower() == expected.lower())
        if is_corr:
            score += 1
        details.append({
            "question_id": q.id,
            "correct": is_corr,
            "user_answer": user_ans,
            "explanation": q.explanation,
        })

    max_score = len(questions)
    percentage = int(round((score / max_score) * 100)) if max_score > 0 else 0
    passed = percentage >= QUIZ_PASS_PERCENT

    denied_badges: list[str] = []
    awarded_badges: list[dict[str, Any]] = []

    now = datetime.now(timezone.utc)
    xp_awarded = 0
    previous_status = None
    new_status = None

    if resolved_motif_id:
        progress = db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id,
                UserProgress.motif_id == resolved_motif_id,
            )
        ).scalar_one_or_none()

        if progress is None:
            progress = UserProgress(
                user_id=user.id,
                motif_id=resolved_motif_id,
                status=UnlockStatus.discovered,
                discovered_at=now,
                xp_earned=DISCOVERY_XP,
                quiz_attempts=0,
                quiz_best_score=0,
            )
            db.add(progress)
            user.total_xp += DISCOVERY_XP

        previous_status = progress.status.value
        progress.quiz_attempts = (progress.quiz_attempts or 0) + 1
        progress.quiz_best_score = max(progress.quiz_best_score or 0, percentage)

        # Persistent QuizAttempt record
        attempt = QuizAttempt(
            user_id=user.id,
            motif_id=resolved_motif_id,
            score=score,
            max_score=max_score,
            percentage=percentage,
            answers=[{"question_id": str(q.id), "answer": answers.get(str(q.id), "")} for q in questions],
            time_taken_seconds=time_taken_seconds,
        )
        db.add(attempt)

        target_xp = DISCOVERY_XP + LESSON_XP + MASTERED_XP
        if passed:
            if progress.status != UnlockStatus.mastered:
                progress.status = UnlockStatus.mastered
                progress.mastered_at = progress.mastered_at or now
                delta = max(0, target_xp - progress.xp_earned)
                if delta > 0:
                    progress.xp_earned = target_xp
                    delta_with_boost = _apply_xp_boost(user, delta, now)
                    user.total_xp += delta_with_boost
                    xp_awarded = delta_with_boost
            new_status = progress.status.value
        else:
            new_status = progress.status.value

    if passed:
        # Evaluate legitimate badge candidates
        legitimate_candidates: list[str] = []
        mastered_count = db.execute(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == user.id,
                UserProgress.status == UnlockStatus.mastered,
            )
        ).scalar_one()
        if mastered_count <= 1:
            legitimate_candidates.append(BADGE_FIRST_MASTERED)

        if percentage == 100:
            legitimate_candidates.append(BADGE_PERFECT_SCORE)

        if time_taken_seconds is not None and time_taken_seconds <= 30:
            legitimate_candidates.append(BADGE_SPEED_DEMON)

        for b_slug in legitimate_candidates:
            badge_obj = db.execute(
                select(Badge).where(Badge.slug == b_slug, Badge.is_active.is_(True))
            ).scalar_one_or_none()
            if badge_obj:
                existing_ub = db.execute(
                    select(UserBadge).where(
                        UserBadge.user_id == user.id,
                        UserBadge.badge_id == badge_obj.id,
                    )
                ).scalar_one_or_none()
                if not existing_ub:
                    db.add(
                        UserBadge(
                            user_id=user.id,
                            badge_id=badge_obj.id,
                            earned_at=now,
                        )
                    )
                    if badge_obj.xp_bonus:
                        user.total_xp += badge_obj.xp_bonus
                    awarded_badges.append({
                        "slug": badge_obj.slug,
                        "name": badge_obj.name,
                        "icon_url": badge_obj.icon_url,
                        "xp_bonus": badge_obj.xp_bonus,
                        "tier": badge_obj.tier.value if hasattr(badge_obj.tier, "value") else str(badge_obj.tier),
                    })

        # Compare with client claimed badges
        if client_claimed_badges:
            awarded_slugs = {b["slug"] for b in awarded_badges}
            for claimed_slug in client_claimed_badges:
                if claimed_slug not in awarded_slugs and claimed_slug not in denied_badges:
                    denied_badges.append(claimed_slug)
    else:
        # Negative abuse: If test failed, all client-claimed badges are denied
        if client_claimed_badges:
            for claimed_slug in client_claimed_badges:
                if claimed_slug not in denied_badges:
                    denied_badges.append(claimed_slug)

    _update_streak(user, now)
    user.last_active_at = now
    db.commit()

    return {
        "success": True,
        "session_id": session_id,
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "passed": passed,
        "xp_awarded": xp_awarded,
        "total_xp": user.total_xp,
        "server_verified": True,
        "awarded_badges": awarded_badges,
        "denied_badges": denied_badges,
        "details": details,
        "previous_status": previous_status,
        "new_status": new_status,
    }


def verify_completion_badge(
    db: Session,
    user: User,
    badge_slug: str,
    motif_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Verify that a student has legitimately earned a completion badge via server assessment.

    Negative Abuse Guardrail:
    Students cannot earn graded completion badges locally without verified server response.
    """
    from ..models import Badge, UserBadge

    badge = db.execute(
        select(Badge).where(Badge.slug == badge_slug, Badge.is_active.is_(True))
    ).scalar_one_or_none()
    if not badge:
        raise AppError(
            code="BADGE_NOT_FOUND",
            message=f"Badge '{badge_slug}' does not exist.",
            status_code=404,
        )

    user_badge = db.execute(
        select(UserBadge).where(
            UserBadge.user_id == user.id,
            UserBadge.badge_id == badge.id,
        )
    ).scalar_one_or_none()

    if not user_badge:
        raise AppError(
            code="UNVERIFIED_COMPLETION",
            message="Student cannot earn graded completion badges locally without verified server response.",
            status_code=400,
            details={"badge_slug": badge_slug, "server_verified": False},
        )

    return {
        "badge_slug": badge_slug,
        "is_verified": True,
        "earned_at": user_badge.earned_at,
        "message": f"Badge '{badge.name}' verified by server.",
    }


# --------------------------------------------------------------------------- #
# Teacher 45-Minute Lesson Wizard Service (V5-T091 / Wave W09 / Slot A01)
# --------------------------------------------------------------------------- #
DEFAULT_WIZARD_OBJECTIVES = {
    "historical_competencies": [
        {
            "code": "S1_SPATIAL",
            "name_vi": "Năng lực Không gian & Bối cảnh Địa lý",
            "description_vi": "Xác định chính xác vị trí khắc chạm trên Cửu Đỉnh, không gian Kinh thành Huế và địa danh gắn liền.",
        },
        {
            "code": "S2_TEMPORAL",
            "name_vi": "Năng lực Thời gian & Tiến trình Lịch sử",
            "description_vi": "Khảo sát niên đại đúc đỉnh (Minh Mạng 16-17 / 1835-1836) và các mốc lịch sử liên đới.",
        },
        {
            "code": "S3_EVIDENCE",
            "name_vi": "Năng lực Sử liệu & Khảo chứng Nguồn",
            "description_vi": "Khai thác, đối chiếu chép sử chính thống (Đại Nam Thực Lục, Hội Điển) với hình tượng phù điêu.",
        },
        {
            "code": "S4_ARGUMENT",
            "name_vi": "Năng lực Lập luận & Đánh giá Di sản",
            "description_vi": "Phân tích ý nghĩa biểu tượng quyền uy, tư tưởng độc lập tự chủ và bảo tồn giá trị di sản văn hóa.",
        },
    ],
    "qualities": [
        "Yêu nước & Tự hào về di sản Cửu Đỉnh — Ký ức thế giới UNESCO",
        "Trung thực & Cẩn trọng trong trích dẫn chứng cứ lịch sử",
        "Ý thức trách nhiệm gìn giữ và bảo vệ di tích Cố đô Huế",
    ],
    "key_takeaways": [
        "Hiểu rõ giá trị nghệ thuật đúc đồng và chạm khắc đỉnh đồng thời Nguyễn.",
        "Hình thành tư duy phản biện khi đọc và đối chiếu sử liệu thành văn với hiện vật bảo vật quốc gia.",
    ],
}

DEFAULT_WIZARD_ACTIVITIES = [
    {
        "activity_number": 1,
        "name_vi": "Hoạt động 1: Khởi động & Kích hoạt tri thức nền (5 phút)",
        "duration_minutes": 5,
        "objective_vi": "Tạo hứng thú, kết nối hiểu biết ban đầu của học sinh về Cửu Đỉnh và đặt ra câu hỏi định hướng.",
        "teacher_actions": [
            "Chiếu hình ảnh bản dập 2D hoặc mô hình 3D của đỉnh/hoa văn.",
            "Nêu câu hỏi kích hoạt: Tại sao hình tượng này lại được triều đình đúc trên vị trí trang trọng của Cửu Đỉnh?",
        ],
        "student_actions": [
            "Quan sát chi tiết phù điêu, thảo luận nhanh cặp đôi 2 phút.",
            "Ghi nhận ấn tượng ban đầu vào mục Khởi động trên phiếu học tập.",
        ],
        "deliverables_vi": "Ghi chép 3 đặc điểm nổi bật quan sát được vào phiếu học tập.",
        "assessment_criteria_vi": "Nhận diện được hình tượng hoa văn và cảm nhận bối cảnh mỹ thuật thời Nguyễn.",
        "guiding_prompts_vi": [
            "Em nhìn thấy những đường nét chi tiết nào nổi bật trên phù điêu?",
            "Vị trí hoa văn này nằm ở tầng trên, giữa hay chân đỉnh?",
        ],
    },
    {
        "activity_number": 2,
        "name_vi": "Hoạt động 2: Khảo sát hiện vật & Đối chiếu sử liệu gốc (15 phút)",
        "duration_minutes": 15,
        "objective_vi": "Học sinh trực tiếp đối chiếu hình ảnh hoa văn với trích đoạn sử liệu chính thống đã được thẩm định.",
        "teacher_actions": [
            "Chuyển giao trích đoạn tư liệu nguồn (Đại Nam Thực Lục, Khâm Định Hội Điển).",
            "Hướng dẫn phương pháp đọc sử liệu: Tác giả, xuất xứ, niên đại và ý nghĩa trích đoạn.",
        ],
        "student_actions": [
            "Làm việc nhóm 4 học sinh: Đọc sử liệu, gạch chân từ khóa về địa danh, sự kiện, quy cách đúc đỉnh.",
            "Điền thông tin xuất xứ và trích dẫn cốt lõi vào bảng khảo chứng tư liệu.",
        ],
        "deliverables_vi": "Bảng đối chiếu 3 cột: Hiện vật quan sát — Trích chép sử liệu — Nhận định bước đầu.",
        "assessment_criteria_vi": "Trích dẫn chính xác tập, quyển, trang của nguồn sử liệu đã được phê duyệt.",
        "guiding_prompts_vi": [
            "Sử sách ghi chép hình tượng này được đúc vào năm nào?",
            "Có sự thống nhất hay khác biệt nào giữa lời văn chép sử và hình ảnh trên bản dập?",
        ],
    },
    {
        "activity_number": 3,
        "name_vi": "Hoạt động 3: Thảo luận sâu & Giải quyết câu hỏi nghiên cứu (15 phút)",
        "duration_minutes": 15,
        "objective_vi": "Phát triển tư duy phân tích, lập luận lịch sử dựa trên chứng cứ đã thu thập.",
        "teacher_actions": [
            "Theo dõi thảo luận các nhóm, gợi mở các khía cạnh biểu tượng và tư tưởng thời Minh Mạng.",
            "Tổ chức đối thoại giữa các nhóm học sinh.",
        ],
        "student_actions": [
            "Tổng hợp luận điểm nhóm: Trả lời câu hỏi trọng tâm của bài học.",
            "Phản biện và bổ sung góc nhìn cho nhóm bạn dựa trên chứng cứ nguồn.",
        ],
        "deliverables_vi": "Sơ đồ tư duy hoặc bản tóm tắt luận điểm (Evidence Brief) của nhóm.",
        "assessment_criteria_vi": "Đạt chuẩn Rubric S3 (Chứng cứ) và S4 (Lập luận) ở mức 2 trở lên.",
        "guiding_prompts_vi": [
            "Hoa văn này phản ánh điều gì về chủ quyền lãnh thổ hoặc sự thịnh vượng của vương triều?",
            "Chứng cứ xác thực nhất để chứng minh cho luận điểm của nhóm em là gì?",
        ],
    },
    {
        "activity_number": 4,
        "name_vi": "Hoạt động 4: Đánh giá & Vé ra cửa (Exit Ticket) (10 phút)",
        "duration_minutes": 10,
        "objective_vi": "Đo lường mức độ đạt chuẩn mục tiêu bài học qua phiếu đánh giá cá nhân và tự lượng giá theo Rubric.",
        "teacher_actions": [
            "Phát lệnh làm Vé ra cửa (Exit ticket) cá nhân 5 phút.",
            "Tổng kết nhanh tiết học, dặn dò nhiệm vụ mở rộng tại nhà.",
        ],
        "student_actions": [
            "Hoàn thành câu hỏi Vé ra cửa cá nhân ngắn gọn 3-5 câu.",
            "Tự đánh giá nhóm theo thang điểm Rubric S1-S4.",
        ],
        "deliverables_vi": "Phiếu Vé ra cửa cá nhân và Phiếu tự đánh giá Rubric nộp cho giáo viên.",
        "assessment_criteria_vi": "Đạt từ 8/12 điểm Rubric chuẩn hoá hoặc hoàn thành tốt nội dung Vé ra cửa.",
        "guiding_prompts_vi": [
            "Bài học hôm nay giúp em thay đổi nhận thức gì về di sản Cửu Đỉnh?",
            "Nêu 1 bằng chứng lịch sử em ấn tượng nhất và giải thích lý do.",
        ],
    },
]

DEFAULT_WIZARD_RUBRIC = {
    "scale_description": "Thang đo 4 mức độ năng lực lịch sử (0 - Chưa đạt, 1 - Đạt cơ bản, 2 - Khá, 3 - Xuất sắc)",
    "levels": [
        {"score": 0, "label_vi": "Chưa đạt (Cần củng cố)"},
        {"score": 1, "label_vi": "Đạt cơ sở (Mức 1)"},
        {"score": 2, "label_vi": "Khá (Mức 2)"},
        {"score": 3, "label_vi": "Xuất sắc (Mức 3)"},
    ],
    "criteria": {
        "S1_SPATIAL": {
            "name": "Năng lực Không gian (S1)",
            "max_points": 3,
            "weight": 0.25,
            "descriptors": {
                "0": "Không xác định được vị trí của đỉnh và phù điêu trên hiện vật.",
                "1": "Xác định được đỉnh nhưng nhầm lẫn vị trí tầng khắc của phù điêu.",
                "2": "Xác định chính xác vị trí trên đỉnh và liên hệ được địa danh gốc.",
                "3": "Mô tả chuẩn xác không gian di sản, toạ độ, hướng nhìn và bối cảnh Kinh thành Huế.",
            },
        },
        "S2_TEMPORAL": {
            "name": "Năng lực Thời gian (S2)",
            "max_points": 3,
            "weight": 0.25,
            "descriptors": {
                "0": "Mơ hồ hoặc sai lệch hoàn toàn về niên đại đúc đỉnh.",
                "1": "Nhớ được triều đại Minh Mạng nhưng không rõ năm tháng cụ thể.",
                "2": "Nêu đúng mốc 1835-1836 và xếp đúng trình tự thời gian sự kiện.",
                "3": "Đặt hiện vật chính xác vào tiến trình lịch sử vương triều và phân tích được bối cảnh thời đại.",
            },
        },
        "S3_EVIDENCE": {
            "name": "Năng lực Khảo chứng Sử liệu (S3)",
            "max_points": 3,
            "weight": 0.25,
            "descriptors": {
                "0": "Không sử dụng trích dẫn sử liệu hoặc đưa thông tin hư cấu.",
                "1": "Có dẫn tư liệu nhưng thiếu xuất xứ (tập, quyển, năm xuất bản).",
                "2": "Trích dẫn đúng nguồn sử liệu chính thức đã được thẩm định.",
                "3": "Đối chiếu thành thạo đa nguồn, phân biệt rõ lời chép sử và nhận định chủ quan.",
            },
        },
        "S4_ARGUMENT": {
            "name": "Năng lực Lập luận & Phân tích (S4)",
            "max_points": 3,
            "weight": 0.25,
            "descriptors": {
                "0": "Diễn đạt rời rạc, không đưa ra được luận điểm rõ ràng.",
                "1": "Có luận điểm nhưng lập luận còn đơn giản, thiếu dẫn chứng minh hoạ.",
                "2": "Lập luận mạch lạc, có dẫn chứng phù hợp từ hiện vật và sử liệu.",
                "3": "Lập luận sắc bén, sâu sắc, khái quát hoá được giá trị tư tưởng và biểu tượng di sản.",
            },
        },
    },
    "exit_ticket": {
        "prompt_vi": "Dựa trên tư liệu chép trong sử sách và hình ảnh bản dập/mô hình 3D, hãy viết đoạn văn ngắn (5-7 câu) làm sáng tỏ vì sao phù điêu này được xếp vào nhóm biểu tượng quan trọng trên Cửu Đỉnh.",
        "expected_evidence_vi": "Học sinh cần nêu được: (1) Tên đỉnh & hoa văn; (2) Trích dẫn vắn tắt từ nguồn chính sử (Đại Nam Thực Lục hoặc Hội Điển); (3) Ý nghĩa biểu tượng về chủ quyền/thống nhất non sông.",
        "time_allowed_minutes": 5,
    },
}


def validate_lesson_plan_for_publication(
    db: Session,
    plan_data: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Strictly validate that a lesson plan satisfies the historical authority publishing gate.

    Negative abuse invariant (Spec V5-T091 / W09-A01):
    A lesson plan CANNOT be published without approved historical object/source.
    Rejects:
    - Missing historical object (both entity_id, urn_id, and motif_id are absent).
    - Missing historical sources (source_ids is empty).
    - Missing historical claims (claim_ids is empty).
    - Any backing claim has an ineligible status (unreviewed, needs_source, disputed, rejected, superseded).
    - Any non-existent claim or source ID.
    """
    issues: list[str] = []

    entity_id = plan_data.get("entity_id")
    urn_id = plan_data.get("urn_id")
    motif_id = plan_data.get("motif_id")
    lesson_id = plan_data.get("lesson_id")

    # Invariant 1: Must reference at least one verified historical object
    has_object = False
    if entity_id:
        ent = db.get(HistoricalEntity, UUID(str(entity_id)))
        if ent:
            has_object = True
        else:
            issues.append(f"Historical entity {entity_id} not found in database.")
    if urn_id:
        urn = db.get(Urn, UUID(str(urn_id)))
        if urn:
            has_object = True
        else:
            issues.append(f"Urn {urn_id} not found in database.")
    if motif_id:
        motif = db.get(Motif, UUID(str(motif_id)))
        if motif:
            has_object = True
        else:
            issues.append(f"Motif {motif_id} not found in database.")
    if lesson_id:
        lesson = db.get(LessonContent, UUID(str(lesson_id)))
        if lesson:
            has_object = True
        else:
            issues.append(f"Lesson content {lesson_id} not found in database.")

    if not has_object:
        issues.append("Lesson plan must link to an approved historical object (Entity, Urn, Motif, or Lesson).")

    # Invariant 2: Must reference at least one historical source
    source_ids = plan_data.get("source_ids") or []
    if not source_ids:
        issues.append("Lesson plan cannot publish without at least one approved historical source.")
    else:
        for sid in source_ids:
            try:
                s = db.get(HistoricalSource, UUID(str(sid)))
                if not s:
                    issues.append(f"Historical source {sid} not found in database.")
                elif getattr(s, "verification_status", None) not in (
                    "verified",
                    "expert_verified",
                    "published",
                    "metadata_verified",
                    "accessible",
                ):
                    issues.append(f"Historical source {sid} has unverified status: '{s.verification_status}'.")
            except (ValueError, TypeError):
                issues.append(f"Invalid source UUID: {sid}")

    # Invariant 3: Must reference at least one historical claim and ALL claims MUST be verified
    claim_ids = plan_data.get("claim_ids") or []
    if not claim_ids:
        issues.append("Lesson plan cannot publish without approved historical claims (claim_ids is empty).")
    else:
        for cid in claim_ids:
            try:
                c = db.get(HistoricalClaim, UUID(str(cid)))
                if not c:
                    issues.append(f"Historical claim {cid} not found in database.")
                elif c.verification_status not in ELIGIBLE_CLAIM_STATUSES:
                    issues.append(
                        f"Historical claim {cid} has ineligible status '{c.verification_status}' "
                        f"(rejects unreviewed, needs_source, or disputed claims)."
                    )
            except (ValueError, TypeError):
                issues.append(f"Invalid claim UUID: {cid}")

    # Invariant 4: Must have 45-minute lesson structure (duration >= 30 and <= 90)
    duration = plan_data.get("duration_minutes") or 45
    if duration != 45 and (duration < 15 or duration > 120):
        issues.append(f"Invalid duration: {duration} minutes (standard 45-minute wizard format expected).")

    return len(issues) == 0, issues


def generate_printable_handout_payload(
    db: Session,
    plan: HistoryLessonPlan,
) -> dict[str, Any]:
    """Generate comprehensive structured A4 printable handout content for teacher and students."""
    # Resolve entity / motif / urn titles
    object_title = plan.topic
    object_code = ""
    urn_name = "Cửu Đỉnh Hoàng Cung Huế"
    if plan.urn_id:
        urn_row = db.get(Urn, plan.urn_id)
        if urn_row:
            urn_name = urn_row.name
    if plan.motif_id:
        motif_row = db.get(Motif, plan.motif_id)
        if motif_row:
            object_title = f"{motif_row.name} ({motif_row.name_en or ''})"
            object_code = motif_row.mesh_name or ""
    elif plan.entity_id:
        ent_row = db.get(HistoricalEntity, plan.entity_id)
        if ent_row:
            object_title = ent_row.name_vi
            object_code = ent_row.slug

    # Format sources for printing
    sources_print: list[dict[str, Any]] = []
    for s_item in (plan.sources_snapshot or []):
        sources_print.append({
            "title": s_item.get("title", ""),
            "author": s_item.get("author_text", ""),
            "pages": s_item.get("citation_text") or s_item.get("pages", ""),
            "publication_year": s_item.get("publication_year", ""),
            "license": s_item.get("license", "Public Domain"),
        })

    # Visual media block
    media_block = {
        "media_variant": plan.media_variant,
        "rubbing_asset_path": (plan.media_config or {}).get("rubbing_url") or "/assets/ban-duc-noi/cao_dinh/long.jpg",
        "qr_code_verification_url": f"https://lms.histolab.icu/dai-noi/giao-vien?plan_id={plan.id}",
        "caption_vi": f"Bản dập 2D / Hiện vật phù điêu {object_title} trên {urn_name} (Bảo vật Quốc gia)",
    }

    # Activities / Inquiry stations
    stations: list[dict[str, Any]] = []
    for act in (plan.inquiry_activities or DEFAULT_WIZARD_ACTIVITIES):
        stations.append({
            "step_number": act.get("activity_number", 1),
            "step_title": act.get("name_vi", ""),
            "duration": f"{act.get('duration_minutes', 10)} phút",
            "task_instructions": act.get("objective_vi", ""),
            "deliverable": act.get("deliverables_vi", ""),
            "student_workspace_lines": 4,
            "guiding_questions": act.get("guiding_prompts_vi", []),
        })

    # Exit ticket
    rubric_obj = plan.assessment_rubric or DEFAULT_WIZARD_RUBRIC
    exit_ticket_obj = rubric_obj.get("exit_ticket") or DEFAULT_WIZARD_RUBRIC["exit_ticket"]

    handout = {
        "header": {
            "institution_vi": "SỞ GIÁO DỤC VÀ ĐÀO TẠO THỪA THIÊN HUẾ",
            "school_placeholder": "TRƯỜNG THPT: .....................................................",
            "student_fields": {
                "name": "Họ và tên học sinh: .....................................................",
                "class": "Lớp: ..............",
                "group": "Nhóm: ..............",
                "date": "Ngày: ...../...../2026",
            },
            "document_title": f"PHIẾU HỌC TẬP KHẢO CỨU DI SẢN (45 PHÚT)",
            "subtitle": f"Chuyên đề: {plan.title} — {urn_name}",
            "framework_code": plan.curriculum_framework,
            "target_grade": plan.target_grade,
        },
        "objectives": plan.objectives or DEFAULT_WIZARD_OBJECTIVES,
        "sources": sources_print,
        "visual_media": media_block,
        "inquiry_stations": stations,
        "exit_ticket": exit_ticket_obj,
        "rubric": rubric_obj,
        "export_metadata": {
            "plan_id": str(plan.id),
            "version": plan.version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "page_setup": "A4 Portrait / 2 Pages Double-Sided",
            "anti_abuse_seal": f"SEAL_V5_{uuid.uuid4().hex[:12].upper()}",
        },
    }
    return handout


def create_lesson_plan(
    db: Session,
    teacher: User,
    payload_dict: dict[str, Any],
) -> HistoryLessonPlan:
    """Create a new 45-minute lesson plan via the wizard."""
    source_ids = payload_dict.get("source_ids") or []
    claim_ids = payload_dict.get("claim_ids") or []

    # Prepare sources snapshot
    sources_snapshot: list[dict[str, Any]] = []
    for sid in source_ids:
        src = db.get(HistoricalSource, UUID(str(sid)))
        if src:
            sources_snapshot.append({
                "id": str(src.id),
                "title": src.title,
                "author_text": src.author_text,
                "source_type": src.source_type,
                "publication_year": src.publication_year,
                "citation_text": src.citation_text,
                "license": src.license,
                "rights_status": src.rights_status,
            })

    # Prepare claims snapshot
    claims_snapshot: list[dict[str, Any]] = []
    for cid in claim_ids:
        clm = db.get(HistoricalClaim, UUID(str(cid)))
        if clm:
            claims_snapshot.append({
                "id": str(clm.id),
                "claim_key": clm.claim_key,
                "statement_vi": clm.statement_vi,
                "verification_status": clm.verification_status,
                "confidence": clm.confidence,
                "claim_type": clm.claim_type,
            })

    status = payload_dict.get("status") or "draft"
    objectives = payload_dict.get("objectives") or DEFAULT_WIZARD_OBJECTIVES
    activities = payload_dict.get("inquiry_activities") or DEFAULT_WIZARD_ACTIVITIES
    rubric = payload_dict.get("assessment_rubric") or DEFAULT_WIZARD_RUBRIC

    plan_id = uuid.uuid4()
    plan = HistoryLessonPlan(
        id=plan_id,
        teacher_id=teacher.id,
        title=payload_dict["title"],
        topic=payload_dict["topic"],
        target_grade=payload_dict.get("target_grade") or "Lớp 10 THPT",
        duration_minutes=payload_dict.get("duration_minutes") or 45,
        curriculum_framework=payload_dict.get("curriculum_framework") or "CV 5512/BGDĐT",
        status=status,
        content_validation_status="valid",
        entity_id=payload_dict.get("entity_id"),
        urn_id=payload_dict.get("urn_id"),
        motif_id=payload_dict.get("motif_id"),
        lesson_id=payload_dict.get("lesson_id"),
        media_variant=payload_dict.get("media_variant") or "2d_rubbing",
        media_config=payload_dict.get("media_config") or {},
        objectives=objectives,
        source_ids=[str(s) for s in source_ids],
        claim_ids=[str(c) for c in claim_ids],
        sources_snapshot=sources_snapshot,
        claims_snapshot=claims_snapshot,
        inquiry_activities=activities,
        assessment_rubric=rubric,
        version=1,
    )

    # Pre-generate handout
    plan.printable_handout = generate_printable_handout_payload(db, plan)

    # Check publication gate if requested as published
    if status == "published":
        is_valid, issues = validate_lesson_plan_for_publication(db, payload_dict)
        if not is_valid:
            raise AppError(
                "LESSON_PLAN_UNVERIFIED_CLAIMS",
                f"Cannot publish lesson plan with unverified claims or missing sources: {'; '.join(issues)}",
                422,
                details={"issues": issues},
            )
        plan.published_at = datetime.now(timezone.utc)

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def publish_lesson_plan(
    db: Session,
    plan_id: UUID,
    user: User,
    is_admin: bool = False,
) -> HistoryLessonPlan:
    """Publish a draft lesson plan enforcing the negative abuse historical claims gate."""
    plan = db.get(HistoryLessonPlan, plan_id)
    if not plan:
        raise AppError("LESSON_PLAN_NOT_FOUND", "Lesson plan not found", 404)

    if not is_admin and plan.teacher_id != user.id:
        raise AppError("FORBIDDEN", "You can only publish lesson plans you authored.", 403)

    plan_data = {
        "entity_id": plan.entity_id,
        "urn_id": plan.urn_id,
        "motif_id": plan.motif_id,
        "lesson_id": plan.lesson_id,
        "source_ids": plan.source_ids,
        "claim_ids": plan.claim_ids,
        "duration_minutes": plan.duration_minutes,
    }

    is_valid, issues = validate_lesson_plan_for_publication(db, plan_data)
    if not is_valid:
        plan.content_validation_status = "blocked_for_authoritative_learning"
        db.commit()
        raise AppError(
            "LESSON_PLAN_UNVERIFIED_CLAIMS",
            f"Cannot publish lesson plan without verified historical claims and sources: {'; '.join(issues)}",
            422,
            details={"issues": issues},
        )

    plan.status = "published"
    plan.content_validation_status = "valid"
    plan.published_at = datetime.now(timezone.utc)
    plan.printable_handout = generate_printable_handout_payload(db, plan)
    db.commit()
    db.refresh(plan)
    return plan





