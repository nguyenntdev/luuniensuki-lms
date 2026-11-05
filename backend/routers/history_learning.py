# -*- coding: utf-8 -*-
"""Historical Learning Engine V2 API router (Phase 8).

Server-authoritative grading (Spec 33.1-33.7), public question listing, staff
question authoring with the content-validity invariant (Spec 32.2), and the V2
mastery dimension surface (Spec 34).

The grading endpoint NEVER trusts client correctness — the client submits only
``{answer: {...}}`` and the server derives ``correct``/``score`` from the
question's answer contract and authoritative knowledge-graph relations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..apischemas.history_learning import (
    CurriculumCompetencyFlagIn,
    CurriculumCompetencyFlagOut,
    CurriculumCompetencyFlagResolveIn,
    CurriculumCompetencyListOut,
    CurriculumCompetencyOut,
    CurriculumCompetencyRelicMappingIn,
    CurriculumCompetencyRelicMappingListOut,
    CurriculumCompetencyRelicMappingOut,
    CurriculumCompetencyRelicMappingUpdateIn,
    CurriculumFallback2DOut,
    CurriculumModuleListOut,
    CurriculumModuleOut,
    CurriculumPublishValidationIn,
    CurriculumPublishValidationOut,
    HistoryAssignmentAssessmentBasisOut,
    HistoryAssignmentGradeIn,
    HistoryAssignmentSubmissionListOut,
    HistoryAssignmentSubmissionOut,
    HistoryAssignmentSubmitIn,
    HistoryLessonAssignmentCreateIn,
    HistoryLessonAssignmentListOut,
    HistoryLessonAssignmentOut,
    HistoryLessonAssignmentPublishOut,
    HistoryLessonPublishIn,
    HistoryLessonPublishOut,
    HistoryQuestionCreate,
    HistoryQuestionGradeIn,
    HistoryQuestionGradeOut,
    HistoryQuestionListOut,
    HistoryQuestionOut,
    HistorySkillsOut,
    MasteryDimensionOut,
    EthicsProtocolCreate,
    EthicsProtocolOut,
    LearningOutcomeAssessmentCreate,
    LearningOutcomeAssessmentOut,
    LearningOutcomeSubmissionCreate,
    LearningOutcomeSubmissionOut,
    RubricEvaluationCreate,
    RubricEvaluationOut,
    SubjectiveSurveyCreate,
    SubjectiveSurveyOut,
    CausalLearningMetricComputeIn,
    CausalLearningMetricOut,
    CohortCausalLearningMetricsOut,
    BadgeVerificationIn,
    BadgeVerificationOut,
    MobilePracticeSubmitIn,
    MobilePracticeSubmitOut,
    MobilePracticeSyncOut,
    MobileQuizQuestionOut,
    PilotGuardianConsentCreate,
    PilotGuardianConsentOut,
    PilotGuardianConsentStatusOut,
    PilotGuardianConsentWithdrawIn,
    TeacherWorkloadLogCreate,
    TeacherWorkloadLogOut,
    TeacherWorkloadSummaryOut,
    RubricCalibrationCreate,
    RubricCalibrationOut,
    PilotDataRetentionAuditOut,
    PilotDataRetentionPurgeIn,
    PilotDataRetentionPurgeOut,
    LearningImprovementClaimValidateIn,
    LearningImprovementClaimValidateOut,
    HistoryLessonPlanCreateIn,
    HistoryLessonPlanUpdateIn,
    HistoryLessonPlanOut,
    HistoryLessonPlanListOut,
    LessonWizardValidateIn,
    LessonWizardValidateOut,
    PrintableHandoutOut,
)
from ..db import get_db
from ..deps import get_current_user, get_staff_user
from ..errors import AppError
from ..models import (
    ClassMember,
    Classroom,
    CurriculumCompetency,
    CurriculumCompetencyFlag,
    CurriculumCompetencyRelicMapping,
    HistoricalClaim,
    HistoricalEntity,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
    HistoryLessonPlan,
    HistoryQuestionType,
    LessonContent,
    QuizQuestion,
    User,
    UserRole,
)
from ..rbac import ADMIN_ROLES, STAFF_ROLES
from ..services import history_learning as hl
from ..services import curriculum_competency as cc_svc

router = APIRouter(tags=["history-learning"])

# V2 question types (registry keys seeded by migration 0050). Authoring may also
# reference legacy types that already exist on the enum.
V2_QUESTION_TYPES = {
    "chronology_order",
    "image_identification",
    "map_location",
    "urn_hotspot",
    "evidence_match",
    "entity_match",
    "compare_two",
    "source_interpretation",
    "short_response",
    "multi_select",
    "relationship_chain",
}


def _question_to_out(question) -> HistoryQuestionOut:
    out = HistoryQuestionOut.model_validate(question)
    out.status = question.content_validation_status
    return out


def _assignment_to_out(assignment: HistoryLessonAssignment) -> HistoryLessonAssignmentOut:
    return HistoryLessonAssignmentOut(
        id=assignment.id,
        classroom_id=assignment.classroom_id,
        lesson_id=assignment.lesson_id,
        assigned_by_id=assignment.assigned_by_id,
        title=assignment.title,
        instructions=assignment.instructions,
        status=assignment.status,
        due_at=assignment.due_at,
        points=assignment.points,
        pinned_version=assignment.pinned_version,
        pinned_lesson_snapshot=assignment.pinned_lesson_snapshot or {},
        rubric=assignment.rubric or {},
        pinned_source_ids=[str(s) for s in (assignment.pinned_source_ids or [])],
        pinned_sources_snapshot=assignment.pinned_sources_snapshot or [],
        pinned_claim_ids=[str(c) for c in (assignment.pinned_claim_ids or [])],
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        published_at=assignment.published_at,
    )


def _submission_to_out(sub: HistoryAssignmentSubmission) -> HistoryAssignmentSubmissionOut:
    return HistoryAssignmentSubmissionOut(
        id=sub.id,
        assignment_id=sub.assignment_id,
        student_id=sub.student_id,
        status=sub.status,
        submission_content=sub.submission_content or {},
        assessment_basis_snapshot=sub.assessment_basis_snapshot or {},
        idempotency_key=sub.idempotency_key,
        score=sub.score,
        rubric_evaluation=sub.rubric_evaluation,
        teacher_feedback=sub.teacher_feedback,
        submitted_at=sub.submitted_at,
        graded_at=sub.graded_at,
        graded_by_id=sub.graded_by_id,
    )


# --------------------------------------------------------------------------- #
# Grading — auth required, server-authoritative
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/questions/{question_id}/grade",
    response_model=HistoryQuestionGradeOut,
)
def grade_history_question(
    question_id: UUID,
    payload: HistoryQuestionGradeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.get(QuizQuestion, question_id)
    if not question:
        raise AppError("HISTORY_QUESTION_NOT_FOUND", "History question not found", 404)

    result = hl.grade_question(db, question, payload.answer)
    dimensions = question.skill_dimensions or []
    hl.update_mastery_from_result(db, current_user.id, question, result)
    db.commit()

    return HistoryQuestionGradeOut(
        correct=result["correct"],
        score=result["score"],
        feedback_vi=result["feedback_vi"],
        skill_dimensions=list(dimensions),
    )


# --------------------------------------------------------------------------- #
# Public read endpoints — no auth
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/history/questions",
    response_model=HistoryQuestionListOut,
)
def list_history_questions(
    question_type: Optional[str] = Query(default=None),
    entity_id: Optional[UUID] = Query(default=None),
    content_validation_status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = select(QuizQuestion)
    if question_type:
        q = q.where(QuizQuestion.question_type == question_type)
    if entity_id:
        q = q.where(QuizQuestion.entity_id == entity_id)
    if content_validation_status:
        q = q.where(QuizQuestion.content_validation_status == content_validation_status)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(QuizQuestion.created_at.desc()).offset(offset).limit(limit)
        )
    )
    return HistoryQuestionListOut(
        items=[_question_to_out(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/api/v1/history/questions/{question_id}",
    response_model=HistoryQuestionOut,
)
def get_history_question(question_id: UUID, db: Session = Depends(get_db)):
    question = db.get(QuizQuestion, question_id)
    if not question:
        raise AppError("HISTORY_QUESTION_NOT_FOUND", "History question not found", 404)
    return _question_to_out(question)


# --------------------------------------------------------------------------- #
# Authoring — staff only
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/questions",
    response_model=HistoryQuestionOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_question(
    payload: HistoryQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.question_type not in V2_QUESTION_TYPES and not (
        payload.question_type
        in {"multiple_choice", "true_false", "image_select", "mesh_location"}
    ):
        raise AppError(
            "HISTORY_QUESTION_INVALID_TYPE",
            f"Unsupported question_type '{payload.question_type}'",
            422,
        )
    if payload.entity_id and not db.get(HistoricalEntity, payload.entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    if payload.claim_ids:
        for claim_id in payload.claim_ids:
            if not db.get(HistoricalClaim, claim_id):
                raise AppError(
                    "HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404
                )

    data = payload.model_dump()
    data["correct_answer"] = data.get("correct_answer") or ""
    # JSONB columns serialize via stdlib json — store IDs as strings, never UUID
    # objects, so the response/insert round-trips cleanly.
    data["claim_ids"] = [str(c) for c in (data.get("claim_ids") or [])]
    data["source_ids"] = [str(s) for s in (data.get("source_ids") or [])]
    data["created_by_id"] = current_user.id

    question = QuizQuestion(**data)
    # Content-validity invariant (Spec 32.2): a question whose backing claims
    # are not verified/editor-reviewed is blocked for authoritative learning.
    is_valid = hl.content_validity_check(db, question)
    question.content_validation_status = (
        "valid"
        if is_valid
        else "blocked_for_authoritative_learning"
    )
    if not is_valid:
        question.is_published = False
    db.add(question)
    db.flush()
    _ensure_registry_row(db, payload.question_type)
    db.commit()
    return _question_to_out(question)


def _ensure_registry_row(db: Session, key: str) -> None:
    """Idempotently record a V2 question type key in the registry table."""
    if key not in V2_QUESTION_TYPES:
        return
    existing = db.scalar(
        select(HistoryQuestionType).where(HistoryQuestionType.key == key)
    )
    if existing is None:
        db.add(HistoryQuestionType(key=key, label_vi=key, label_en=key, sort_order=0))
        db.flush()


# --------------------------------------------------------------------------- #
# Mastery V2 — auth required
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/history/skills/{user_id}",
    response_model=HistorySkillsOut,
)
def get_history_skills(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != user_id and current_user.role not in (ADMIN_ROLES | STAFF_ROLES):
        raise HTTPException(status_code=403, detail="Not authorized")
    dimensions = hl.get_mastery_dimensions(db, user_id)
    values = [d["value"] for d in dimensions if d["value"] is not None]
    overall = round(sum(values) / len(values), 4) if values else None
    return HistorySkillsOut(
        user_id=user_id,
        dimensions=[MasteryDimensionOut(**d) for d in dimensions],
        overall=overall,
    )


# --------------------------------------------------------------------------- #
# Curriculum Mapping & Publishing Gate Endpoints (V5-T029)
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/history/curriculum/modules",
    response_model=CurriculumModuleListOut,
)
def list_curriculum_modules(db: Session = Depends(get_db)):
    """List curriculum learning modules mapped to verified entities, claims, and 2D fallbacks."""
    modules = hl.get_curriculum_modules(db=db)
    return CurriculumModuleListOut(
        items=[CurriculumModuleOut(**m) for m in modules],
        total=len(modules),
    )


@router.get(
    "/api/v1/history/curriculum/modules/{slug}",
    response_model=CurriculumModuleOut,
)
def get_curriculum_module(slug: str, db: Session = Depends(get_db)):
    """Get single curriculum module with verified claim linkage and 2D rubbing fallback."""
    mod = hl.get_curriculum_module(slug, db=db)
    if not mod:
        raise AppError("CURRICULUM_MODULE_NOT_FOUND", f"Curriculum module '{slug}' not found", 404)
    return CurriculumModuleOut(**mod)


@router.get(
    "/api/v1/history/curriculum/fallbacks/{target}",
    response_model=CurriculumFallback2DOut,
)
def get_curriculum_2d_fallback(target: str):
    """Resolve 2D rubbing asset fallback for low-bandwidth educational environments."""
    fallback = hl.resolve_2d_rubbing_fallback(target)
    return CurriculumFallback2DOut(**fallback)


@router.post(
    "/api/v1/history/curriculum/validate-publish",
    response_model=CurriculumPublishValidationOut,
)
def validate_curriculum_publication(
    payload: CurriculumPublishValidationIn,
    db: Session = Depends(get_db),
):
    """Validate whether a learning module or lesson satisfies the historical claim publishing gate."""
    lesson = None
    if payload.lesson_id:
        lesson = db.get(LessonContent, payload.lesson_id)
        if not lesson:
            raise AppError("LESSON_NOT_FOUND", "Lesson not found", 404)
    else:
        # Dry-run validation dummy object if no lesson_id passed
        lesson = LessonContent(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            motif_id=UUID("00000000-0000-0000-0000-000000000000"),
            description="Dry run validation",
        )

    is_valid, issues = hl.validate_lesson_for_publication(
        db,
        lesson,
        required_claim_ids=payload.claim_ids,
        module_slug=payload.module_slug,
    )

    verified_count = 0
    ineligible_count = 0
    if payload.claim_ids:
        for cid in payload.claim_ids:
            c = db.get(HistoricalClaim, cid)
            if c and c.verification_status in hl.ELIGIBLE_CLAIM_STATUSES:
                verified_count += 1
            else:
                ineligible_count += 1

    return CurriculumPublishValidationOut(
        can_publish=is_valid,
        validation_status="valid" if is_valid else "blocked_for_authoritative_learning",
        issues=issues,
        verified_claims_count=verified_count,
        ineligible_claims_count=ineligible_count,
    )


@router.post(
    "/api/v1/history/lessons/{lesson_id}/publish",
    response_model=HistoryLessonPublishOut,
    dependencies=[Depends(get_staff_user)],
)
def publish_history_lesson(
    lesson_id: UUID,
    payload: Optional[HistoryLessonPublishIn] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a lesson enforcing the historical claim verification gate (staff/admin only)."""
    claim_ids = payload.claim_ids if payload else None
    module_slug = payload.module_slug if payload else None
    notes = payload.review_notes if payload else None

    lesson = hl.publish_lesson_with_gate(
        db=db,
        lesson_id=lesson_id,
        current_user_id=current_user.id,
        required_claim_ids=claim_ids,
        module_slug=module_slug,
        review_notes=notes,
    )

    verified_claims = [str(c) for c in (claim_ids or [])]
    return HistoryLessonPublishOut(
        id=lesson.id,
        motif_id=lesson.motif_id,
        is_published=lesson.is_published,
        status=lesson.status.value if hasattr(lesson.status, "value") else str(lesson.status),
        content_validation_status=lesson.content_validation_status,
        published_at=lesson.published_at,
        verified_claim_ids=verified_claims,
    )


# --------------------------------------------------------------------------- #
# Curriculum Competency Catalog Endpoints (V5-T095 / Wave W09 / Slot A05)
# Vietnam 2018 General Education Program (GDPT 2018)
# --------------------------------------------------------------------------- #
def _format_mapping_out(m: CurriculumCompetencyRelicMapping) -> CurriculumCompetencyRelicMappingOut:
    return CurriculumCompetencyRelicMappingOut(
        id=m.id,
        competency_id=m.competency_id,
        competency_code=m.competency.code if m.competency else None,
        competency_name_vi=m.competency.name_vi if m.competency else None,
        competency_domain=m.competency.domain if m.competency else None,
        relic_urn_slug=m.relic_urn_slug,
        relic_motif_id=m.relic_motif_id,
        entity_slug=m.entity_slug,
        grade_band=m.grade_band,
        min_grade=m.min_grade,
        max_grade=m.max_grade,
        learning_activity_vi=m.learning_activity_vi,
        learning_activity_en=m.learning_activity_en,
        evidence_requirement_vi=m.evidence_requirement_vi,
        evidence_requirement_en=m.evidence_requirement_en,
        status=m.status,
        is_reviewed=m.is_reviewed,
        review_warning=m.review_warning,
        flag_count=m.flag_count,
        created_by_id=m.created_by_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _format_flag_out(f: CurriculumCompetencyFlag) -> CurriculumCompetencyFlagOut:
    return CurriculumCompetencyFlagOut(
        id=f.id,
        mapping_id=f.mapping_id,
        flagged_by_id=f.flagged_by_id,
        flagged_by_name=f.flagged_by.display_name if f.flagged_by else None,
        reason=f.reason,
        commentary=f.commentary,
        suggested_correction=f.suggested_correction,
        status=f.status,
        resolved_by_id=f.resolved_by_id,
        resolution_notes=f.resolution_notes,
        created_at=f.created_at,
        resolved_at=f.resolved_at,
    )


@router.get(
    "/api/v1/history/curriculum/competencies",
    response_model=CurriculumCompetencyListOut,
)
def list_curriculum_competencies(
    framework: Optional[str] = Query(None, description="Curriculum framework, e.g. VN_GDPT_2018"),
    domain: Optional[str] = Query(None, description="Competency domain"),
    db: Session = Depends(get_db),
):
    """List standard historical competencies under Vietnam 2018 General Education Program."""
    comps = cc_svc.list_competencies(db, framework=framework, domain=domain)
    return CurriculumCompetencyListOut(
        items=[CurriculumCompetencyOut.model_validate(c) for c in comps],
        total=len(comps),
    )


@router.get(
    "/api/v1/history/curriculum/competencies/mappings",
    response_model=CurriculumCompetencyRelicMappingListOut,
)
def list_curriculum_competency_mappings(
    urn_slug: Optional[str] = Query(None, description="Filter by relic urn slug"),
    motif_id: Optional[str] = Query(None, description="Filter by relic motif id"),
    competency_code: Optional[str] = Query(None, description="Filter by competency code"),
    grade: Optional[int] = Query(None, ge=6, le=12, description="Filter by target grade (6-12)"),
    grade_band: Optional[str] = Query(None, description="Filter by grade band"),
    status: Optional[str] = Query(None, description="Filter by status (unreviewed, verified, flagged)"),
    db: Session = Depends(get_db),
):
    """List curriculum competency mappings across real relics and grade bands with review warnings."""
    mappings = cc_svc.list_relic_mappings(
        db,
        urn_slug=urn_slug,
        motif_id=motif_id,
        competency_code=competency_code,
        grade=grade,
        grade_band=grade_band,
        status=status,
    )
    return CurriculumCompetencyRelicMappingListOut(
        items=[_format_mapping_out(m) for m in mappings],
        total=len(mappings),
    )


@router.get(
    "/api/v1/history/curriculum/competencies/mappings/{mapping_id}",
    response_model=CurriculumCompetencyRelicMappingOut,
)
def get_curriculum_competency_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
):
    """Get single curriculum competency relic mapping with review status and warnings."""
    mapping = cc_svc.get_relic_mapping(db, mapping_id)
    if not mapping:
        raise AppError("MAPPING_NOT_FOUND", f"Mapping {mapping_id} not found", 404)
    return _format_mapping_out(mapping)


@router.post(
    "/api/v1/history/curriculum/competencies/mappings",
    response_model=CurriculumCompetencyRelicMappingOut,
    status_code=201,
)
def create_curriculum_competency_mapping(
    payload: CurriculumCompetencyRelicMappingIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher or staff creates a new competency relic mapping. Defaults to unreviewed with review warning."""
    mapping = cc_svc.create_relic_mapping(
        db=db,
        user=current_user,
        data=payload.model_dump(),
    )
    return _format_mapping_out(mapping)


@router.put(
    "/api/v1/history/curriculum/competencies/mappings/{mapping_id}",
    response_model=CurriculumCompetencyRelicMappingOut,
)
def update_curriculum_competency_mapping(
    mapping_id: UUID,
    payload: CurriculumCompetencyRelicMappingUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher or staff updates an existing competency relic mapping."""
    mapping = cc_svc.update_relic_mapping(
        db=db,
        user=current_user,
        mapping_id=mapping_id,
        data=payload.model_dump(exclude_unset=True),
    )
    return _format_mapping_out(mapping)


@router.post(
    "/api/v1/history/curriculum/competencies/mappings/{mapping_id}/flag",
    response_model=CurriculumCompetencyFlagOut,
    status_code=201,
)
def flag_curriculum_competency_mapping(
    mapping_id: UUID,
    payload: CurriculumCompetencyFlagIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher flags an inaccurate competency mapping, triggering 'flagged' status and review warnings."""
    flag = cc_svc.flag_relic_mapping(
        db=db,
        user=current_user,
        mapping_id=mapping_id,
        reason=payload.reason,
        commentary=payload.commentary,
        suggested_correction=payload.suggested_correction,
    )
    return _format_flag_out(flag)


@router.get(
    "/api/v1/history/curriculum/competencies/mappings/{mapping_id}/flags",
    response_model=list[CurriculumCompetencyFlagOut],
)
def list_curriculum_competency_mapping_flags(
    mapping_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List teacher flags and inaccuracy reports for a competency mapping (teachers and staff only)."""
    flags = cc_svc.list_mapping_flags(db, mapping_id, current_user)
    return [_format_flag_out(f) for f in flags]


@router.post(
    "/api/v1/history/curriculum/competencies/flags/{flag_id}/resolve",
    response_model=CurriculumCompetencyFlagOut,
)
def resolve_curriculum_competency_flag(
    flag_id: UUID,
    payload: CurriculumCompetencyFlagResolveIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Staff or administrator resolves or dismisses a teacher inaccuracy flag."""
    flag = cc_svc.resolve_mapping_flag(
        db=db,
        user=current_user,
        flag_id=flag_id,
        action=payload.action,
        resolution_notes=payload.resolution_notes,
        updated_mapping_status=payload.updated_mapping_status,
    )
    return _format_flag_out(flag)


@router.post(
    "/api/v1/history/curriculum/competencies/mappings/{mapping_id}/verify",
    response_model=CurriculumCompetencyRelicMappingOut,
)
def verify_curriculum_competency_mapping(
    mapping_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Staff or administrator verifies a competency mapping, clearing review warnings."""
    mapping = cc_svc.verify_relic_mapping(
        db=db,
        user=current_user,
        mapping_id=mapping_id,
    )
    return _format_mapping_out(mapping)


@router.get(
    "/api/v1/history/curriculum/competencies/{code}",
    response_model=CurriculumCompetencyOut,
)
def get_curriculum_competency(
    code: str,
    db: Session = Depends(get_db),
):
    """Get single historical competency details by code."""
    comp = cc_svc.get_competency_by_code(db, code)
    if not comp:
        raise AppError("COMPETENCY_NOT_FOUND", f"Competency '{code}' not found", 404)
    return CurriculumCompetencyOut.model_validate(comp)


# --------------------------------------------------------------------------- #
# Source-Locked Classroom Assignment & Rubric Endpoints (V5-T033)
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/assignments",
    response_model=HistoryLessonAssignmentOut,
    status_code=201,
)
def create_history_assignment(
    payload: HistoryLessonAssignmentCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a classroom lesson assignment with source-locked lesson snapshot and rubric."""
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN", "Only teachers or staff can create assignments", 403)

    classroom = db.get(Classroom, payload.classroom_id)
    if not classroom:
        raise AppError("CLASSROOM_NOT_FOUND", "Classroom not found", 404)

    if current_user.role not in ADMIN_ROLES and classroom.teacher_id != current_user.id:
        raise AppError("FORBIDDEN", "You can only create assignments for classrooms you teach", 403)

    assignment = hl.create_source_locked_assignment(
        db=db,
        teacher_id=current_user.id,
        classroom_id=payload.classroom_id,
        lesson_id=payload.lesson_id,
        title=payload.title,
        instructions=payload.instructions,
        due_at=payload.due_at,
        points=payload.points,
        rubric=payload.rubric,
        source_ids=payload.source_ids,
        claim_ids=payload.claim_ids,
        status=payload.status,
    )
    return _assignment_to_out(assignment)


@router.get(
    "/api/v1/history/assignments",
    response_model=HistoryLessonAssignmentListOut,
)
def list_history_assignments(
    classroom_id: Optional[UUID] = Query(default=None),
    lesson_id: Optional[UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List historical lesson assignments."""
    query = select(HistoryLessonAssignment)
    if classroom_id:
        query = query.where(HistoryLessonAssignment.classroom_id == classroom_id)
    if lesson_id:
        query = query.where(HistoryLessonAssignment.lesson_id == lesson_id)
    if status:
        query = query.where(HistoryLessonAssignment.status == status)

    if current_user.role not in STAFF_ROLES:
        query = (
            query.join(ClassMember, ClassMember.class_id == HistoryLessonAssignment.classroom_id)
            .where(ClassMember.user_id == current_user.id)
            .where(HistoryLessonAssignment.status == "published")
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(HistoryLessonAssignment.created_at.desc()).offset(offset).limit(limit)).all()

    return HistoryLessonAssignmentListOut(
        items=[_assignment_to_out(a) for a in items],
        total=total,
    )


@router.get(
    "/api/v1/history/assignments/{assignment_id}",
    response_model=HistoryLessonAssignmentOut,
)
def get_history_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single history lesson assignment."""
    assignment = db.get(HistoryLessonAssignment, assignment_id)
    if not assignment:
        raise AppError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)
    return _assignment_to_out(assignment)


@router.post(
    "/api/v1/history/assignments/{assignment_id}/publish",
    response_model=HistoryLessonAssignmentPublishOut,
)
def publish_history_assignment_endpoint(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish an assignment enforcing the negative abuse claim verification gate."""
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN", "Only teachers or staff can publish assignments", 403)

    assignment = hl.publish_history_assignment(
        db=db,
        assignment_id=assignment_id,
        user_id=current_user.id,
        is_admin=(current_user.role in ADMIN_ROLES),
    )
    return HistoryLessonAssignmentPublishOut(
        id=assignment.id,
        classroom_id=assignment.classroom_id,
        lesson_id=assignment.lesson_id,
        status=assignment.status,
        pinned_version=assignment.pinned_version,
        published_at=assignment.published_at or datetime.now(timezone.utc),
        verified_claim_ids=[str(c) for c in (assignment.pinned_claim_ids or [])],
        pinned_source_ids=[str(s) for s in (assignment.pinned_source_ids or [])],
    )


@router.get(
    "/api/v1/history/assignments/{assignment_id}/assessment-basis",
    response_model=HistoryAssignmentAssessmentBasisOut,
)
def get_history_assignment_assessment_basis(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the immutable assessment basis for an assignment (Spec V5-T033)."""
    assignment = db.get(HistoryLessonAssignment, assignment_id)
    if not assignment:
        raise AppError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)

    basis = assignment.get_assessment_basis()
    pub_at = None
    if basis.get("published_at"):
        try:
            pub_at = datetime.fromisoformat(basis["published_at"])
        except (ValueError, TypeError):
            pub_at = None

    return HistoryAssignmentAssessmentBasisOut(
        assignment_id=UUID(basis["assignment_id"]),
        classroom_id=UUID(basis["classroom_id"]),
        lesson_id=UUID(basis["lesson_id"]),
        pinned_version=basis["pinned_version"],
        lesson_snapshot=basis["lesson_snapshot"],
        rubric=basis["rubric"],
        pinned_source_ids=basis["pinned_source_ids"],
        pinned_sources=basis["pinned_sources"],
        pinned_claim_ids=basis["pinned_claim_ids"],
        published_at=pub_at,
    )


@router.post(
    "/api/v1/history/assignments/{assignment_id}/submit",
    response_model=HistoryAssignmentSubmissionOut,
)
def submit_history_assignment_endpoint(
    assignment_id: UUID,
    payload: HistoryAssignmentSubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit student work against a source-locked assignment with validation and idempotency."""
    sub, _is_new = hl.submit_history_assignment(
        db=db,
        assignment_id=assignment_id,
        student_id=current_user.id,
        submission_content=payload.submission_content,
        idempotency_key=payload.idempotency_key,
    )
    return _submission_to_out(sub)


@router.get(
    "/api/v1/history/assignments/{assignment_id}/submissions",
    response_model=HistoryAssignmentSubmissionListOut,
)
def list_history_assignment_submissions(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List submissions for an assignment (teacher or admin)."""
    assignment = db.get(HistoryLessonAssignment, assignment_id)
    if not assignment:
        raise AppError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)

    classroom = db.get(Classroom, assignment.classroom_id)
    if (
        current_user.role not in ADMIN_ROLES
        and classroom
        and classroom.teacher_id != current_user.id
        and assignment.assigned_by_id != current_user.id
    ):
        raise AppError("FORBIDDEN", "Only teacher of the classroom or admin can view all submissions", 403)

    subs = db.scalars(
        select(HistoryAssignmentSubmission)
        .where(HistoryAssignmentSubmission.assignment_id == assignment_id)
        .order_by(HistoryAssignmentSubmission.submitted_at.desc())
    ).all()
    return HistoryAssignmentSubmissionListOut(
        items=[_submission_to_out(s) for s in subs],
        total=len(subs),
    )


@router.get(
    "/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}",
    response_model=HistoryAssignmentSubmissionOut,
)
def get_history_assignment_submission(
    assignment_id: UUID,
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single submission (by student owner or teacher/admin)."""
    sub = db.get(HistoryAssignmentSubmission, submission_id)
    if not sub or sub.assignment_id != assignment_id:
        raise AppError("SUBMISSION_NOT_FOUND", "Submission not found", 404)

    if current_user.role not in ADMIN_ROLES and sub.student_id != current_user.id:
        assignment = db.get(HistoryLessonAssignment, assignment_id)
        classroom = db.get(Classroom, assignment.classroom_id) if assignment else None
        if not (classroom and classroom.teacher_id == current_user.id) and not (
            assignment and assignment.assigned_by_id == current_user.id
        ):
            raise AppError("FORBIDDEN", "Not authorized to view this submission", 403)

    return _submission_to_out(sub)


@router.post(
    "/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}/grade",
    response_model=HistoryAssignmentSubmissionOut,
)
def grade_history_assignment_submission_endpoint(
    assignment_id: UUID,
    submission_id: UUID,
    payload: HistoryAssignmentGradeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grade a submission using rubric criteria (teacher or admin)."""
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN", "Only teachers or staff can grade submissions", 403)

    sub = hl.grade_history_assignment_submission(
        db=db,
        submission_id=submission_id,
        teacher_id=current_user.id,
        score=payload.score,
        rubric_evaluation=payload.rubric_evaluation,
        teacher_feedback=payload.teacher_feedback,
        is_admin=(current_user.role in ADMIN_ROLES),
    )
    return _submission_to_out(sub)


@router.get(
    "/api/v1/history/submissions",
    response_model=list[HistoryAssignmentSubmissionOut],
    include_in_schema=False,
)
def list_all_history_submissions(
    classroom_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Historical inquiry submissions endpoint for teachers and students (Spec V5-T031)."""
    if current_user.role not in STAFF_ROLES:
        stmt = (
            select(HistoryAssignmentSubmission)
            .where(HistoryAssignmentSubmission.student_id == current_user.id)
            .order_by(HistoryAssignmentSubmission.submitted_at.desc())
        )
    else:
        stmt = select(HistoryAssignmentSubmission).order_by(
            HistoryAssignmentSubmission.submitted_at.desc()
        )
        if classroom_id:
            stmt = stmt.join(
                HistoryLessonAssignment,
                HistoryLessonAssignment.id == HistoryAssignmentSubmission.assignment_id,
            ).where(HistoryLessonAssignment.classroom_id == classroom_id)

    subs = db.scalars(stmt).all()
    return [_submission_to_out(s) for s in subs]


# --------------------------------------------------------------------------- #
# Learning Outcome Measurement Endpoints (V5-T039 / Wave W03 / Slot A09)
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/learning-outcomes/ethics-protocols",
    response_model=EthicsProtocolOut,
    dependencies=[Depends(get_staff_user)],
)
def create_ethics_protocol_endpoint(
    payload: EthicsProtocolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register an ethics / IRB protocol for learning outcome measurement research (staff/admin)."""
    return hl.create_ethics_protocol(db, payload.model_dump(), current_user_id=current_user.id)


@router.get(
    "/api/v1/history/learning-outcomes/ethics-protocols/{protocol_id}",
    response_model=EthicsProtocolOut,
)
def get_ethics_protocol_endpoint(
    protocol_id: UUID,
    db: Session = Depends(get_db),
):
    """Get ethics protocol details."""
    return hl.get_ethics_protocol(db, protocol_id)


@router.post(
    "/api/v1/history/learning-outcomes/assessments",
    response_model=LearningOutcomeAssessmentOut,
    dependencies=[Depends(get_staff_user)],
)
def create_learning_outcome_assessment_endpoint(
    payload: LearningOutcomeAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a source-based inquiry assessment task (pre/post/delayed) linked to an approved ethics protocol."""
    return hl.create_learning_outcome_assessment(db, payload.model_dump(), current_user_id=current_user.id)


@router.get(
    "/api/v1/history/learning-outcomes/assessments/{assessment_id}",
    response_model=LearningOutcomeAssessmentOut,
)
def get_learning_outcome_assessment_endpoint(
    assessment_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve an assessment task with prompt and rubric."""
    assessment = db.get(hl.HistoryLearningOutcomeAssessment, assessment_id)
    if not assessment:
        raise AppError("ASSESSMENT_NOT_FOUND", "Assessment not found", 404)
    return assessment


@router.post(
    "/api/v1/history/learning-outcomes/assessments/{assessment_id}/submit",
    response_model=LearningOutcomeSubmissionOut,
)
def submit_learning_outcome_assessment_endpoint(
    assessment_id: UUID,
    payload: LearningOutcomeSubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student submits answers to an objective source inquiry assessment."""
    return hl.submit_learning_outcome_assessment(
        db,
        assessment_id=assessment_id,
        student_id=current_user.id,
        responses=payload.responses,
        citations_provided=payload.citations_provided,
    )


@router.post(
    "/api/v1/history/learning-outcomes/submissions/{submission_id}/evaluate",
    response_model=RubricEvaluationOut,
    dependencies=[Depends(get_staff_user)],
)
def evaluate_learning_outcome_submission_endpoint(
    submission_id: UUID,
    payload: RubricEvaluationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Independent assessor evaluates a student submission against objective rubric criteria."""
    return hl.evaluate_learning_outcome_submission(
        db,
        submission_id=submission_id,
        assessor_id=current_user.id,
        rubric_scores=payload.rubric_scores,
        feedback_markdown=payload.feedback_markdown,
        evidence_notes=payload.evidence_notes,
    )


@router.post(
    "/api/v1/history/learning-outcomes/surveys",
    response_model=SubjectiveSurveyOut,
)
def submit_subjective_survey_endpoint(
    payload: SubjectiveSurveyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a subjective self-report survey (isolated from causal mastery metrics)."""
    return hl.submit_subjective_survey(
        db,
        student_id=current_user.id,
        survey_name=payload.survey_name,
        likert_responses=payload.likert_responses,
        perceived_learning_score=payload.perceived_learning_score,
        satisfaction_score=payload.satisfaction_score,
        feedback_text=payload.feedback_text,
    )


@router.post(
    "/api/v1/history/learning-outcomes/causal-metrics",
    response_model=CausalLearningMetricOut,
    dependencies=[Depends(get_staff_user)],
)
def compute_causal_learning_outcome_endpoint(
    payload: CausalLearningMetricComputeIn,
    db: Session = Depends(get_db),
):
    """Compute causal learning gain between pre/post objective inquiry assessments.
    
    Negative abuse check: Rejects survey responses (feelings/satisfaction).
    """
    return hl.compute_causal_learning_outcome(
        db,
        student_id=payload.student_id,
        ethics_protocol_id=payload.ethics_protocol_id,
        pre_submission_id=payload.pre_submission_id,
        post_submission_id=payload.post_submission_id,
        delayed_submission_id=payload.delayed_submission_id,
        is_survey_data=payload.is_survey_data,
        survey_response_id=payload.survey_response_id,
    )


@router.get(
    "/api/v1/history/learning-outcomes/cohort-metrics/{ethics_protocol_id}",
    response_model=CohortCausalLearningMetricsOut,
    dependencies=[Depends(get_staff_user)],
)
def get_cohort_causal_metrics_endpoint(
    ethics_protocol_id: UUID,
    db: Session = Depends(get_db),
):
    """Get aggregated cohort causal learning metrics (mean gain, Cohen's d, inter-rater reliability)."""
    return hl.get_cohort_causal_learning_metrics(db, ethics_protocol_id)


# --------------------------------------------------------------------------- #
# School Pilot Measurement & Ethics Endpoints (V5-T100 / Wave W09 / Slot A10)
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/learning-outcomes/ethics-protocols/{ethics_protocol_id}/consent",
    response_model=PilotGuardianConsentOut,
)
def register_pilot_guardian_consent_endpoint(
    ethics_protocol_id: UUID,
    payload: PilotGuardianConsentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register informed guardian consent for student pilot research participation."""
    consent_data = payload.model_dump()
    consent_data["ethics_protocol_id"] = ethics_protocol_id
    return hl.create_pilot_guardian_consent(db, consent_data, current_user_id=current_user.id)


@router.post(
    "/api/v1/history/learning-outcomes/ethics-protocols/{ethics_protocol_id}/consent/{consent_id}/verify",
    response_model=PilotGuardianConsentOut,
    dependencies=[Depends(get_staff_user)],
)
def verify_pilot_guardian_consent_endpoint(
    ethics_protocol_id: UUID,
    consent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Staff or teacher verifies authenticated guardian consent."""
    return hl.verify_pilot_guardian_consent(db, consent_id=consent_id, verifier_id=current_user.id)


@router.post(
    "/api/v1/history/learning-outcomes/ethics-protocols/{ethics_protocol_id}/consent/{consent_id}/withdraw",
    response_model=PilotGuardianConsentOut,
)
def withdraw_pilot_guardian_consent_endpoint(
    ethics_protocol_id: UUID,
    consent_id: UUID,
    payload: PilotGuardianConsentWithdrawIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Withdraw guardian consent, immediately suspending empirical research participation."""
    return hl.withdraw_pilot_guardian_consent(db, consent_id=consent_id, reason=payload.reason)


@router.get(
    "/api/v1/history/learning-outcomes/ethics-protocols/{ethics_protocol_id}/consent/{student_id}/status",
    response_model=PilotGuardianConsentStatusOut,
)
def get_pilot_guardian_consent_status_endpoint(
    ethics_protocol_id: UUID,
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Query guardian informed consent status for a student under an ethics protocol."""
    return hl.get_pilot_guardian_consent_status(db, protocol_id=ethics_protocol_id, student_id=student_id)


@router.post(
    "/api/v1/history/learning-outcomes/teacher-workload",
    response_model=TeacherWorkloadLogOut,
)
def log_teacher_workload_endpoint(
    payload: TeacherWorkloadLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record educator workload metrics and NASA-TLX cognitive load index."""
    data = payload.model_dump()
    return hl.log_teacher_workload(db, teacher_id=current_user.id, payload=data)


@router.get(
    "/api/v1/history/learning-outcomes/teacher-workload/summary",
    response_model=TeacherWorkloadSummaryOut,
)
def get_teacher_workload_summary_endpoint(
    teacher_id: Optional[UUID] = Query(default=None),
    school_id: Optional[UUID] = Query(default=None),
    ethics_protocol_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Summarize teacher workload metrics and burnout risk indicators."""
    target_teacher = teacher_id or (current_user.id if current_user.role in (UserRole.teacher, UserRole.learner) else None)
    return hl.get_teacher_workload_summary(
        db,
        teacher_id=target_teacher,
        school_id=school_id,
        protocol_id=ethics_protocol_id,
    )


@router.post(
    "/api/v1/history/learning-outcomes/rubric-calibration",
    response_model=RubricCalibrationOut,
    dependencies=[Depends(get_staff_user)],
)
def calibrate_submission_rubrics_endpoint(
    payload: RubricCalibrationCreate,
    db: Session = Depends(get_db),
):
    """Calibrate dual independent assessor rubric evaluations and check scoring divergence."""
    return hl.calibrate_submission_rubrics(
        db,
        submission_id=payload.submission_id,
        assessor_a_id=payload.assessor_a_id,
        assessor_b_id=payload.assessor_b_id,
        tolerance_pct=payload.tolerance_pct,
    )


@router.post(
    "/api/v1/history/learning-outcomes/retention/audit",
    response_model=PilotDataRetentionAuditOut,
    dependencies=[Depends(get_staff_user)],
)
def audit_pilot_data_retention_endpoint(
    ethics_protocol_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Audit pilot assessment and survey records exceeding data retention limits."""
    return hl.audit_pilot_data_retention(db, ethics_protocol_id=ethics_protocol_id)


@router.post(
    "/api/v1/history/learning-outcomes/retention/purge",
    response_model=PilotDataRetentionPurgeOut,
    dependencies=[Depends(get_staff_user)],
)
def purge_expired_pilot_data_endpoint(
    payload: PilotDataRetentionPurgeIn,
    db: Session = Depends(get_db),
):
    """Purge student PII from expired records per Decree 13/2023/ND-CP."""
    if not payload.confirm_purge:
        raise HTTPException(status_code=400, detail="confirm_purge must be true to execute retention purge")
    return hl.purge_expired_pilot_data(db, ethics_protocol_id=payload.ethics_protocol_id)


@router.post(
    "/api/v1/history/learning-outcomes/validate-learning-claim",
    response_model=LearningImprovementClaimValidateOut,
)
def validate_learning_improvement_claim_endpoint(
    payload: LearningImprovementClaimValidateIn,
    db: Session = Depends(get_db),
):
    """Validate learning improvement claims. Rejects subjective sentiment / feelings surveys (HTTP 422)."""
    return hl.validate_learning_improvement_claim(db, payload.model_dump())


# --------------------------------------------------------------------------- #
# Mobile Lesson Quiz Sync & Server Assessment Endpoints (V5-T057)
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/history/practice/sync",
    response_model=MobilePracticeSyncOut,
)
def sync_mobile_practice(
    lesson_id: Optional[UUID] = Query(default=None),
    motif_id: Optional[UUID] = Query(default=None),
    category: Optional[str] = Query(default=None),
    difficulty: Optional[int] = Query(default=None, ge=1, le=5),
    limit: int = Query(default=10, ge=1, le=50),
    mode: Optional[str] = Query(default="quick_review"),
    db: Session = Depends(get_db),
):
    """Sync real published quiz questions for mobile practice modes.

    Parity with backend server assessment tasks:
    - Never leaks correct answers or answer contracts to the client.
    - Questions must be published and content-validated.
    """
    return hl.sync_mobile_practice_questions(
        db=db,
        lesson_id=lesson_id,
        motif_id=motif_id,
        category=category,
        difficulty=difficulty,
        limit=limit,
        mode=mode,
    )


@router.get(
    "/api/v1/history/lessons/{lesson_id}/quiz-sync",
    response_model=MobilePracticeSyncOut,
)
def sync_lesson_quiz(
    lesson_id: UUID,
    difficulty: Optional[int] = Query(default=None, ge=1, le=5),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Sync real published quiz questions for a specific historical lesson."""
    return hl.sync_mobile_practice_questions(
        db=db,
        lesson_id=lesson_id,
        difficulty=difficulty,
        limit=limit,
        mode="lesson_quiz",
    )


@router.post(
    "/api/v1/history/practice/submit",
    response_model=MobilePracticeSubmitOut,
)
def submit_mobile_practice(
    payload: MobilePracticeSubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit mobile practice assessment answers with server-authoritative grading.

    Negative abuse guardrails:
    - Scoring is derived server-side from active question records.
    - Badges are only awarded if server-calculated score >= 80% pass threshold.
    - Any client-claimed badges or scores submitted without server verification
      are rejected.
    """
    return hl.submit_mobile_practice_assessment(
        db=db,
        user=current_user,
        answers=payload.answers,
        session_id=payload.session_id,
        motif_id=payload.motif_id,
        lesson_id=payload.lesson_id,
        time_taken_seconds=payload.time_taken_seconds,
        client_claimed_badges=payload.client_claimed_badges,
        client_claimed_score=payload.client_claimed_score,
    )


@router.post(
    "/api/v1/history/practice/verify-badge",
    response_model=BadgeVerificationOut,
)
def verify_badge_claim(
    payload: BadgeVerificationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify that a completion badge was awarded via legitimate server evaluation.

    Negative abuse guardrail:
    Returns HTTP 400 if user attempts to claim a graded completion badge locally
    without a verified server response.
    """
    return hl.verify_completion_badge(
        db=db,
        user=current_user,
        badge_slug=payload.badge_slug,
        motif_id=payload.motif_id,
    )


# --------------------------------------------------------------------------- #
# Teacher 45-Minute Lesson Wizard Endpoints (V5-T091 / Wave W09 / Slot A01)
# --------------------------------------------------------------------------- #
def _lesson_plan_to_out(plan: HistoryLessonPlan) -> HistoryLessonPlanOut:
    return HistoryLessonPlanOut(
        id=plan.id,
        teacher_id=plan.teacher_id,
        title=plan.title,
        topic=plan.topic,
        target_grade=plan.target_grade,
        duration_minutes=plan.duration_minutes,
        curriculum_framework=plan.curriculum_framework,
        status=plan.status,
        content_validation_status=plan.content_validation_status,
        entity_id=plan.entity_id,
        urn_id=plan.urn_id,
        motif_id=plan.motif_id,
        lesson_id=plan.lesson_id,
        media_variant=plan.media_variant,
        media_config=plan.media_config or {},
        objectives=plan.objectives or {},
        source_ids=[str(s) for s in (plan.source_ids or [])],
        claim_ids=[str(c) for c in (plan.claim_ids or [])],
        sources_snapshot=plan.sources_snapshot or [],
        claims_snapshot=plan.claims_snapshot or [],
        inquiry_activities=plan.inquiry_activities or [],
        assessment_rubric=plan.assessment_rubric or {},
        printable_handout=plan.printable_handout or {},
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        published_at=plan.published_at,
    )


@router.post(
    "/api/v1/history/lesson-wizard/validate",
    response_model=LessonWizardValidateOut,
)
def validate_lesson_wizard_endpoint(
    payload: LessonWizardValidateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate 5-phase lesson plan against historical authority & publishing gates."""
    plan_dict = payload.model_dump()
    is_valid, issues = hl.validate_lesson_plan_for_publication(db, plan_dict)

    verified_count = 0
    ineligible_count = 0
    for cid in payload.claim_ids:
        clm = db.get(HistoricalClaim, cid)
        if clm and clm.verification_status in hl.ELIGIBLE_CLAIM_STATUSES:
            verified_count += 1
        else:
            ineligible_count += 1

    return LessonWizardValidateOut(
        can_publish=is_valid,
        validation_status="valid" if is_valid else "blocked_for_authoritative_learning",
        issues=issues,
        verified_claims_count=verified_count,
        ineligible_claims_count=ineligible_count,
        warnings=[],
    )


@router.post(
    "/api/v1/history/lesson-plans",
    response_model=HistoryLessonPlanOut,
    status_code=201,
)
def create_history_lesson_plan(
    payload: HistoryLessonPlanCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new 45-minute structured lesson plan via the teacher wizard."""
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN", "Only teachers or staff can create lesson plans", 403)

    plan = hl.create_lesson_plan(db, current_user, payload.model_dump())
    return _lesson_plan_to_out(plan)


@router.get(
    "/api/v1/history/lesson-plans",
    response_model=HistoryLessonPlanListOut,
)
def list_history_lesson_plans(
    status: Optional[str] = Query(default=None),
    motif_id: Optional[UUID] = Query(default=None),
    entity_id: Optional[UUID] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List 45-minute lesson plans with teacher and status filters."""
    query = select(HistoryLessonPlan)
    if status:
        query = query.where(HistoryLessonPlan.status == status)
    if motif_id:
        query = query.where(HistoryLessonPlan.motif_id == motif_id)
    if entity_id:
        query = query.where(HistoryLessonPlan.entity_id == entity_id)

    if current_user.role not in ADMIN_ROLES:
        # Teachers see their own plans plus published public plans
        query = query.where(
            (HistoryLessonPlan.teacher_id == current_user.id)
            | (HistoryLessonPlan.status == "published")
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(HistoryLessonPlan.created_at.desc()).offset(offset).limit(limit)).all()
    return HistoryLessonPlanListOut(
        items=[_lesson_plan_to_out(p) for p in items],
        total=total,
    )


@router.get(
    "/api/v1/history/lesson-plans/{plan_id}",
    response_model=HistoryLessonPlanOut,
)
def get_history_lesson_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full details of a 45-minute lesson plan."""
    plan = db.get(HistoryLessonPlan, plan_id)
    if not plan:
        raise AppError("LESSON_PLAN_NOT_FOUND", "Lesson plan not found", 404)
    return _lesson_plan_to_out(plan)


@router.post(
    "/api/v1/history/lesson-plans/{plan_id}/publish",
    response_model=HistoryLessonPlanOut,
)
def publish_history_lesson_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a lesson plan enforcing negative abuse historical claims gate."""
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN", "Only teachers or staff can publish lesson plans", 403)

    is_admin = current_user.role in ADMIN_ROLES
    plan = hl.publish_lesson_plan(db, plan_id, current_user, is_admin=is_admin)
    return _lesson_plan_to_out(plan)


@router.get(
    "/api/v1/history/lesson-plans/{plan_id}/printable-handout",
    response_model=PrintableHandoutOut,
)
def get_lesson_plan_printable_handout(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve pre-formatted printable student worksheet and teacher guide."""
    plan = db.get(HistoryLessonPlan, plan_id)
    if not plan:
        raise AppError("LESSON_PLAN_NOT_FOUND", "Lesson plan not found", 404)

    handout = plan.printable_handout or hl.generate_printable_handout_payload(db, plan)
    return PrintableHandoutOut(**handout)




