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
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import (
    ContentStatus,
    HistoricalClaim,
    HistoricalEntity,
    HistoricalEntityRelation,
    HistoricalSource,
    LessonContent,
    QuizQuestion,
    UserSkillLevel,
)

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

