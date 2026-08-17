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
from typing import Any, Callable, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (
    HistoricalClaim,
    HistoricalEntityRelation,
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
ELIGIBLE_CLAIM_STATUSES: set[str] = {"editor_reviewed", "expert_verified"}

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