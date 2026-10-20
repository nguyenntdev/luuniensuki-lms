# -*- coding: utf-8 -*-
"""Imperial learning service — STTTNNĐ (Lưu Niên — Đại Nội Huế).

Provides learning paths, pedagogical inquiry activities, student submissions,
and rubric-based grading:
- Learning paths & steps retrieval (thematic walking and learning trails)
- Site-based inquiry activity retrieval
- Student activity submission with evidence references
- Teacher submission review and rubric evaluation (S1-S4: spatial, temporal, evidence, argument)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..apischemas.imperial import (
    ImperialActivityOut,
    ImperialLearningPathDetail,
    ImperialLearningPathSummary,
    ImperialPathStepOut,
    ImperialSiteSummary,
    ImperialSubmissionCreate,
    ImperialSubmissionGrade,
    ImperialSubmissionOut,
)
from ..errors import AppError
from ..imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialActivity,
    ImperialLearningPath,
    ImperialPathStep,
    ImperialSite,
    ImperialSubmission,
)

# Reference to supplemental zones and sites data
_ZONES_AND_SITES_FILE = Path(__file__).resolve().parents[2] / "data" / "imperial" / "zones_and_sites.json"
_supplemental_cache: Optional[dict[str, dict[str, Any]]] = None


def _get_supplemental_data() -> dict[str, dict[str, Any]]:
    global _supplemental_cache
    if _supplemental_cache is not None:
        return _supplemental_cache
    cache: dict[str, dict[str, Any]] = {}
    if _ZONES_AND_SITES_FILE.exists():
        try:
            raw = json.loads(_ZONES_AND_SITES_FILE.read_text(encoding="utf-8"))
            for s in raw.get("sites", []):
                slug = s.get("slug")
                if slug:
                    cache[slug] = s
        except Exception:
            pass
    _supplemental_cache = cache
    return _supplemental_cache


# --------------------------------------------------------------------------- #
# Curated Default Learning Paths
# --------------------------------------------------------------------------- #
_DEFAULT_LEARNING_PATHS = [
    {
        "slug": "truc-chinh-dao-hoang-thanh",
        "title": "Trục Chính Đạo Hoàng Thành",
        "title_en": "Central Ceremonial Axis Trail",
        "description": "Hành trình khám phá trật tự quyền lực, phong thủy và nghi lễ cung đình từ Ngọ Môn qua cầu Trung Đạo, sân Đại Triều Nghi đến điện Thái Hòa.",
        "kind": "thematic_trail",
        "duration_min": 45,
        "age_group": "all",
        "learning_objectives": [
            "Hiểu cấu trúc phân tầng quyền lực và nghi lễ từ Ngọ Môn đến Điện Thái Hòa",
            "Đối chiếu chính sử Đại Nam Thực Lục với mặt bằng kiến trúc di tích",
            "Phân tích vai trò phong thủy của trục thần đạo trong quy hoạch kinh thành Huế",
        ],
        "prerequisites": "Kiến thức nhập môn về lịch sử triều Nguyễn",
        "display_order": 1,
        "steps": [
            {
                "site_slug": "ngo-mon",
                "step_order": 1,
                "title": "Khảo sát Ngọ Môn & Lầu Ngũ Phụng",
                "prompt": "Khảo sát 5 cửa ngõ và lầu Ngũ Phụng: phân tích nguyên lý phân tầng và chức năng nghi lễ ban lịch Sóc, truyền loa tiến sĩ.",
                "source_requirement": "Đại Nam Thực Lục Chính Biên (Đệ nhị kỷ, Quyển 98)",
                "rubrics": {
                    "S1_spatial": "Xác định vai trò tiền tiêu trên trục thần đạo",
                    "S2_temporal": "Nhận diện năm 1833 thời Minh Mạng",
                    "S3_evidence": "Dẫn chứng quy chế 5 cửa từ Đại Nam Thực Lục",
                    "S4_argument": "Phân tích mối liên hệ giữa thẩm quyền chính trị và kiến trúc",
                },
                "estimated_minutes": 10,
            },
            {
                "site_slug": "cau-trung-dao",
                "step_order": 2,
                "title": "Vượt hồ Thái Dịch qua Cầu Trung Đạo",
                "prompt": "Quan sát hai cửa đồng quán và mặt cầu lát đá thanh qua hồ Thái Dịch; giải thích vai trò nhịp chuyển tiếp tâm lý trước khi vào sân đại triều.",
                "source_requirement": "Đại Nam Nhất Thống Chí (Quyển 1)",
                "rubrics": {
                    "S1_spatial": "Định vị cầu Trung Đạo kết nối Ngọ Môn và sân Đại Triều",
                    "S2_temporal": "Thời điểm xây dựng năm 1833",
                    "S3_evidence": "Sử liệu Nhất Thống Chí về hồ Thái Dịch",
                    "S4_argument": "Ý nghĩa phong thủy tụ thủy sinh tài của hồ cảnh quan",
                },
                "estimated_minutes": 10,
            },
            {
                "site_slug": "san-dai-trieu-nghi",
                "step_order": 3,
                "title": "Phân tầng phẩm hàm tại Sân Đại Triều Nghi",
                "prompt": "Đối chiếu vị trí hai hàng bia phẩm tán (phẩm trật) trên hai tầng sân: giải thích trật tự quan văn bên tả, quan võ bên hữu.",
                "source_requirement": "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 65)",
                "rubrics": {
                    "S1_spatial": "Phân biệt tầng sân trên (tứ phẩm trở lên) và dưới (ngũ đến cửu phẩm)",
                    "S2_temporal": "Khởi tạo thời Gia Long và định chế thời Minh Mạng",
                    "S3_evidence": "Trích dẫn Hội Điển Sự Lệ về nghi thức bái mạng",
                    "S4_argument": "Đánh giá tính quy củ trong lễ nghi triều chính",
                },
                "estimated_minutes": 10,
            },
            {
                "site_slug": "dien-thai-hoa",
                "step_order": 4,
                "title": "Biểu tượng vương quyền tại Điện Thái Hòa",
                "prompt": "Phân tích kết cấu 'trùng thiềm điệp ốc' với 80 cột gỗ lim và ý nghĩa ngai vàng thiên tử dưới bửu tán; đọc giải hệ thống thơ văn chữ Hán trên ô hộc liên ba.",
                "source_requirement": "Đại Nam Thực Lục Chính Biên (Đệ nhất kỷ Q.26, Đệ nhị kỷ Q.105) & Hội Điển Sự Lệ (Q.64)",
                "rubrics": {
                    "S1_spatial": "Xác định tâm điểm quyền lực tối cao của Hoàng Thành",
                    "S2_temporal": "Mốc dựng 1805 và chuyển dời năm 1833",
                    "S3_evidence": "Dẫn chứng quy thức trùng thiềm điệp ốc và thơ ngự chế",
                    "S4_argument": "Lập luận về thông điệp thái bình văn hiến của vương triều",
                },
                "estimated_minutes": 15,
            },
        ],
    },
    {
        "slug": "khong-gian-tho-tu-hoang-gia",
        "title": "Không Gian Thờ Tự Hoàng Gia",
        "title_en": "Ancestral Worship Space Trail",
        "description": "Tuyến học tập tìm hiểu đạo hiếu, tín ngưỡng tổ tiên và tính chính danh triều đại tại cụm di tích Thế Tổ Miếu và Hiển Lâm Các.",
        "kind": "ancestral_trail",
        "duration_min": 40,
        "age_group": "all",
        "learning_objectives": [
            "Khám phá hệ thống miếu điện thờ phụng các vua và tổ tiên triều Nguyễn",
            "Phân tích quy thức thờ tự và tính chính danh triều đại",
            "Đối chiếu kiến trúc gỗ cổ truyền tại Hiển Lâm Các",
        ],
        "prerequisites": "Kiến thức về thế thứ các vua triều Nguyễn",
        "display_order": 2,
        "steps": [
            {
                "site_slug": "the-to-mieu",
                "step_order": 1,
                "title": "Tôn vinh tiền nhân tại Thế Tổ Miếu",
                "prompt": "Khảo sát kiến trúc miếu thờ lớn nhất triều Nguyễn; tìm hiểu quy tắc an vị thần khám và tính chính thống triều đại.",
                "source_requirement": "Đại Nam Thực Lục Chính Biên (Đệ nhị kỷ, Quyển 12)",
                "rubrics": {
                    "S1_spatial": "Vị trí linh thiêng phía tây nam Hoàng Thành",
                    "S2_temporal": "Khởi công năm 1821 thời Minh Mạng",
                    "S3_evidence": "Quy chế thờ tự chính tự và tả hữu tòng tự",
                    "S4_argument": "Ý nghĩa đạo hiếu và tính pháp lý vương triều",
                },
                "estimated_minutes": 15,
            },
            {
                "site_slug": "hien-lam-cac",
                "step_order": 2,
                "title": "Kiến trúc kỳ vĩ của Hiển Lâm Các",
                "prompt": "Đánh giá công trình kiến trúc gỗ cao nhất Hoàng Thành (17m); giải thích vai trò đài kỷ niệm ghi công các đại thần công thần khai quốc.",
                "source_requirement": "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 64)",
                "rubrics": {
                    "S1_spatial": "Tòa gác 3 tầng sừng sững đối diện Thế Miếu",
                    "S2_temporal": "Xây dựng năm 1821-1822",
                    "S3_evidence": "Tài liệu kỹ thuật mộng giằng kiến trúc gỗ triều Nguyễn",
                    "S4_argument": "Biểu tượng tưởng niệm và vinh danh công lao xã tắc",
                },
                "estimated_minutes": 15,
            },
        ],
    },
]


def _ensure_default_learning_paths(db: Session) -> None:
    """Ensure curated default learning paths and steps exist in the database."""
    # Find all sites mapped by slug
    site_stmt = select(ImperialSite).where(ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL)
    sites = {s.slug: s for s in db.execute(site_stmt).scalars().all()}
    if not sites:
        return

    for path_data in _DEFAULT_LEARNING_PATHS:
        slug = path_data["slug"]
        path = db.execute(
            select(ImperialLearningPath).where(
                ImperialLearningPath.content_scope == CONTENT_SCOPE_IMPERIAL,
                ImperialLearningPath.slug == slug,
            )
        ).scalar_one_or_none()

        if not path:
            path_id = uuid5(NAMESPACE_DNS, f"imperial_path:{slug}")
            path = ImperialLearningPath(
                id=path_id,
                content_scope=CONTENT_SCOPE_IMPERIAL,
                slug=slug,
                title=path_data["title"],
                title_en=path_data.get("title_en"),
                description=path_data.get("description"),
                kind=path_data.get("kind", "standard"),
                duration_min=path_data.get("duration_min", 45),
                age_group=path_data.get("age_group", "all"),
                learning_objectives=path_data.get("learning_objectives", []),
                prerequisites=path_data.get("prerequisites"),
                review_status="published",
                is_published=True,
                display_order=path_data.get("display_order", 0),
                row_version=1,
            )
            db.add(path)
            db.flush()

            # Create steps
            for step_data in path_data.get("steps", []):
                site_slug = step_data["site_slug"]
                site = sites.get(site_slug)
                if not site:
                    continue

                step_id = uuid5(NAMESPACE_DNS, f"imperial_step:{slug}:{step_data['step_order']}")
                step = ImperialPathStep(
                    id=step_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    path_id=path.id,
                    site_id=site.id,
                    step_order=step_data["step_order"],
                    title=step_data.get("title"),
                    prompt=step_data["prompt"],
                    source_requirement=step_data.get("source_requirement"),
                    rubrics=step_data.get("rubrics"),
                    estimated_minutes=step_data.get("estimated_minutes", 10),
                )
                db.add(step)

    db.commit()


def _format_path_detail(p: ImperialLearningPath) -> ImperialLearningPathDetail:
    """Format an ImperialLearningPath entity into ImperialLearningPathDetail schema."""
    formatted_steps: list[ImperialPathStepOut] = []
    for step in sorted(p.steps, key=lambda s: s.step_order):
        site_summary = None
        if step.site:
            site_summary = ImperialSiteSummary(
                id=step.site.id,
                zone_id=step.site.zone_id,
                slug=step.site.slug,
                name_vi=step.site.name_vi,
                name_en=step.site.name_en,
                site_type=step.site.site_type,
                condition=step.site.condition,
                learning_level=step.site.learning_level,
                is_published=step.site.is_published,
                display_order=step.site.display_order,
            )
        formatted_steps.append(
            ImperialPathStepOut(
                id=step.id,
                content_scope=step.content_scope,
                path_id=step.path_id,
                site_id=step.site_id,
                step_order=step.step_order,
                title=step.title,
                prompt=step.prompt,
                source_requirement=step.source_requirement,
                rubrics=step.rubrics,
                estimated_minutes=step.estimated_minutes,
                site=site_summary,
            )
        )

    return ImperialLearningPathDetail(
        id=p.id,
        content_scope=p.content_scope,
        slug=p.slug,
        title=p.title,
        title_en=p.title_en,
        description=p.description,
        kind=p.kind,
        duration_min=p.duration_min,
        age_group=p.age_group,
        learning_objectives=p.learning_objectives or [],
        prerequisites=p.prerequisites,
        review_status=p.review_status,
        is_published=p.is_published,
        display_order=p.display_order,
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
        row_version=p.row_version,
        steps=formatted_steps,
    )


# =========================================================================== #
# Learning Paths Endpoints Services
# =========================================================================== #
def get_learning_paths(
    db: Session, published_only: bool = True
) -> list[ImperialLearningPathDetail]:
    """List curated trails with steps and associated monument sites."""
    _ensure_default_learning_paths(db)

    stmt = (
        select(ImperialLearningPath)
        .where(ImperialLearningPath.content_scope == CONTENT_SCOPE_IMPERIAL)
        .options(
            selectinload(ImperialLearningPath.steps).selectinload(ImperialPathStep.site)
        )
    )
    if published_only:
        stmt = stmt.where(ImperialLearningPath.is_published == True)

    stmt = stmt.order_by(ImperialLearningPath.display_order.asc(), ImperialLearningPath.title.asc())
    paths = db.execute(stmt).scalars().all()

    return [_format_path_detail(p) for p in paths]


def get_learning_path_by_slug(db: Session, slug: str) -> ImperialLearningPathDetail:
    """Retrieve detailed learning path trail with step sequence and site metadata."""
    _ensure_default_learning_paths(db)

    stmt = (
        select(ImperialLearningPath)
        .where(
            ImperialLearningPath.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialLearningPath.slug == slug,
        )
        .options(
            selectinload(ImperialLearningPath.steps).selectinload(ImperialPathStep.site)
        )
    )
    path = db.execute(stmt).scalar_one_or_none()
    if not path:
        raise AppError("IMPERIAL_PATH_NOT_FOUND", f"Learning path '{slug}' not found", 404)

    return _format_path_detail(path)


# =========================================================================== #
# Activities & Pedagogical Tasks
# =========================================================================== #
def get_site_activities(db: Session, site_slug: str) -> list[ImperialActivityOut]:
    """List pedagogical inquiry activities and reflection tasks for an architectural site."""
    site = db.execute(
        select(ImperialSite).where(
            ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialSite.slug == site_slug,
        )
    ).scalar_one_or_none()
    if not site:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Imperial site '{site_slug}' not found", 404)

    stmt = (
        select(ImperialActivity)
        .where(
            ImperialActivity.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialActivity.site_id == site.id,
            ImperialActivity.is_active == True,
        )
        .order_by(ImperialActivity.created_at.asc())
    )
    activities = list(db.execute(stmt).scalars().all())

    # If no activities in database yet, auto-populate from supplemental seed data
    if not activities:
        supp = _get_supplemental_data().get(site_slug, {})
        task = supp.get("pedagogical_task")
        if task:
            act_id = uuid5(NAMESPACE_DNS, f"activity:{site_slug}")
            act = ImperialActivity(
                id=act_id,
                content_scope=CONTENT_SCOPE_IMPERIAL,
                site_id=site.id,
                path_id=None,
                activity_type=task.get("deliverable_type", "evidence_reflection"),
                title=task.get("title") or f"Khảo sát và đối chiếu sử liệu {site.name_vi}",
                instructions=task.get("task_prompt") or f"Tìm hiểu và phân tích cấu trúc {site.name_vi}.",
                rubric_json=supp.get("rubrics", {}),
                max_points=100,
                is_active=True,
                row_version=1,
            )
            db.add(act)
            db.commit()
            db.refresh(act)
            activities = [act]
        else:
            # Baseline activity if not in supplemental
            act_id = uuid5(NAMESPACE_DNS, f"activity:default:{site_slug}")
            act = ImperialActivity(
                id=act_id,
                content_scope=CONTENT_SCOPE_IMPERIAL,
                site_id=site.id,
                path_id=None,
                activity_type="evidence_reflection",
                title=f"Khảo sát di tích {site.name_vi}",
                instructions=f"Học sinh hãy đối chiếu thông tin lịch sử và kiến trúc của {site.name_vi} với chính sử triều Nguyễn.",
                rubric_json={
                    "S1_spatial": "Xác định vị trí di tích trong không gian Hoàng Thành",
                    "S2_temporal": "Xác định niên đại xây dựng và thời kỳ lịch sử",
                    "S3_evidence": "Trích dẫn được tư liệu hoặc bằng chứng lịch sử",
                    "S4_argument": "Lập luận mạch lạc, thể hiện tư duy lịch sử",
                },
                max_points=100,
                is_active=True,
                row_version=1,
            )
            db.add(act)
            db.commit()
            db.refresh(act)
            activities = [act]

    return [ImperialActivityOut.model_validate(a) for a in activities]


# =========================================================================== #
# Student Submissions & Teacher Rubric Grading
# =========================================================================== #
def submit_activity(
    db: Session,
    activity_id: UUID,
    student_id: UUID,
    payload: Union[ImperialSubmissionCreate, dict[str, Any]],
) -> ImperialSubmissionOut:
    """Save student answer, evidence references, and timestamp for an inquiry task."""
    activity = db.get(ImperialActivity, activity_id)
    if not activity or activity.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ACTIVITY_NOT_FOUND", f"Activity '{activity_id}' not found", 404)

    answer_text = (
        payload.answer_text
        if isinstance(payload, ImperialSubmissionCreate)
        else payload.get("answer_text", "")
    )
    if not answer_text or not str(answer_text).strip():
        raise AppError("INVALID_SUBMISSION", "Answer text must not be empty", 400)

    evidence_refs = (
        payload.evidence_refs
        if isinstance(payload, ImperialSubmissionCreate)
        else payload.get("evidence_refs", [])
    )
    classroom_id = (
        payload.classroom_id
        if isinstance(payload, ImperialSubmissionCreate)
        else payload.get("classroom_id")
    )

    now = datetime.now(timezone.utc)
    submission = ImperialSubmission(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        activity_id=activity.id,
        student_id=student_id,
        classroom_id=classroom_id,
        status="submitted",
        answer_text=str(answer_text).strip(),
        evidence_refs=evidence_refs or [],
        score=None,
        rubric_scores={},
        feedback=None,
        graded_by=None,
        graded_at=None,
        submitted_at=now,
        updated_at=now,
        row_version=1,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return ImperialSubmissionOut.model_validate(submission)


def get_submissions_for_teacher(
    db: Session,
    teacher_id: UUID,
    activity_id: Optional[UUID] = None,
) -> list[ImperialSubmissionOut]:
    """List student submissions for teacher evaluation with optional activity filtering."""
    stmt = select(ImperialSubmission).where(
        ImperialSubmission.content_scope == CONTENT_SCOPE_IMPERIAL
    )
    if activity_id is not None:
        stmt = stmt.where(ImperialSubmission.activity_id == activity_id)

    stmt = stmt.order_by(ImperialSubmission.submitted_at.desc())
    submissions = db.execute(stmt).scalars().all()

    return [ImperialSubmissionOut.model_validate(s) for s in submissions]


def grade_submission(
    db: Session,
    submission_id: UUID,
    teacher_id: UUID,
    payload: Union[ImperialSubmissionGrade, dict[str, Any]],
) -> ImperialSubmissionOut:
    """Record rubric scores S1-S4 (0-3 scale each), total score, and teacher feedback."""
    submission = db.get(ImperialSubmission, submission_id)
    if not submission or submission.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_SUBMISSION_NOT_FOUND", f"Submission '{submission_id}' not found", 404)

    raw_rubric_scores = (
        payload.rubric_scores
        if isinstance(payload, ImperialSubmissionGrade)
        else payload.get("rubric_scores")
    )
    score = (
        payload.score
        if isinstance(payload, ImperialSubmissionGrade)
        else payload.get("score")
    )
    feedback = (
        payload.feedback
        if isinstance(payload, ImperialSubmissionGrade)
        else payload.get("feedback")
    )
    grade_status = (
        payload.status
        if isinstance(payload, ImperialSubmissionGrade)
        else payload.get("status", "graded")
    )

    validated_rubrics: dict[str, int] = {}
    if raw_rubric_scores:
        for criterion, score_val in raw_rubric_scores.items():
            if not isinstance(score_val, int) or score_val < 0 or score_val > 3:
                raise AppError(
                    "INVALID_RUBRIC_SCORE",
                    f"Rubric score '{criterion}' must be an integer between 0 and 3",
                    400,
                )
            validated_rubrics[str(criterion)] = int(score_val)

    # Compute total score if not explicitly given
    if score is not None:
        final_score = float(score)
    elif validated_rubrics:
        final_score = float(sum(validated_rubrics.values()))
    else:
        final_score = 0.0

    now = datetime.now(timezone.utc)
    submission.score = final_score
    submission.rubric_scores = validated_rubrics
    submission.feedback = feedback
    submission.status = grade_status or "graded"
    submission.graded_by = teacher_id
    submission.graded_at = now
    submission.updated_at = now
    submission.row_version = (submission.row_version or 1) + 1

    db.commit()
    db.refresh(submission)

    return ImperialSubmissionOut.model_validate(submission)
