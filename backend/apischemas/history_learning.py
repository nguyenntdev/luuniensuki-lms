# -*- coding: utf-8 -*-
"""Historical Learning Engine V2 API schemas (Phase 8).

Request/response models for the question-model V2 endpoints and mastery
dimensions per docs/specs/HISTORY_FIRST_MASTER_SPEC.md sections 32-34.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HistoryQuestionCreate(BaseModel):
    motif_id: UUID
    question_type: str
    question_text: str = Field(..., min_length=1, max_length=2000)
    options: Optional[list[Any]] = None
    correct_answer: Optional[str] = None
    target_mesh_name: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=5)
    skill_type: Optional[str] = None
    explanation: Optional[str] = None
    is_published: bool = True
    is_active: bool = True
    # V2 common fields (Spec 32.1)
    skill_dimensions: Optional[list[str]] = None
    entity_id: Optional[UUID] = None
    claim_ids: Optional[list[UUID]] = None
    source_ids: Optional[list[UUID]] = None
    answer_contract: Optional[dict[str, Any]] = None


class HistoryQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int
    skill_type: Optional[str] = None
    explanation: Optional[str] = None
    is_published: bool
    is_active: bool
    content_validation_status: str
    skill_dimensions: Optional[list[Any]] = None
    entity_id: Optional[UUID] = None
    claim_ids: Optional[list[Any]] = None
    source_ids: Optional[list[Any]] = None
    answer_contract: Optional[dict] = None
    status: Optional[str] = None
    created_at: datetime


class HistoryQuestionListOut(BaseModel):
    items: list[HistoryQuestionOut]
    total: int
    offset: int
    limit: int


class HistoryQuestionGradeIn(BaseModel):
    """Client submits ONLY the raw answer. Correctness is never accepted from
    the client — the server derives it from the answer contract (Spec 33.4)."""

    answer: dict[str, Any]


class HistoryQuestionGradeOut(BaseModel):
    correct: bool
    score: float
    feedback_vi: str
    skill_dimensions: list[str]


class MasteryDimensionOut(BaseModel):
    dimension: str
    value: Optional[float] = None
    total_questions: int = 0
    correct_answers: int = 0
    last_score: Optional[float] = None


class HistorySkillsOut(BaseModel):
    user_id: UUID
    dimensions: list[MasteryDimensionOut]
    overall: Optional[float] = None


# --------------------------------------------------------------------------- #
# Curriculum Mapping & Publishing Gate Schemas (V5-T029)
# --------------------------------------------------------------------------- #
class CurriculumObjectiveOut(BaseModel):
    code: str
    text_vi: str
    text_en: Optional[str] = None
    competency: str
    target_entity_slug: Optional[str] = None
    target_claim_keys: list[str] = Field(default_factory=list)
    claims_verified: bool = True


class CurriculumFallback2DOut(BaseModel):
    available: bool = True
    asset_type: str = "2d_rubbing"
    url: str
    local_file_path: Optional[str] = None
    byte_size: Optional[int] = None
    description: Optional[str] = None


class CurriculumModuleOut(BaseModel):
    id: str
    slug: str
    title_vi: str
    title_en: Optional[str] = None
    description_vi: str
    description_en: Optional[str] = None
    era: str
    topic: str
    curriculum_framework: str
    roadmap_phase: str
    historical_competencies: list[str] = Field(default_factory=list)
    learning_objectives: list[CurriculumObjectiveOut] = Field(default_factory=list)
    media_fallback_2d: Optional[CurriculumFallback2DOut] = None
    entity_slugs: list[str] = Field(default_factory=list)
    core_claim_keys: list[str] = Field(default_factory=list)
    publication_gate_ready: bool = True


class CurriculumModuleListOut(BaseModel):
    items: list[CurriculumModuleOut]
    total: int


class CurriculumPublishValidationIn(BaseModel):
    lesson_id: Optional[UUID] = None
    module_slug: Optional[str] = None
    claim_ids: Optional[list[UUID]] = None


class CurriculumPublishValidationOut(BaseModel):
    can_publish: bool
    validation_status: str
    issues: list[str] = Field(default_factory=list)
    verified_claims_count: int = 0
    ineligible_claims_count: int = 0


class HistoryLessonPublishIn(BaseModel):
    claim_ids: Optional[list[UUID]] = None
    module_slug: Optional[str] = None
    review_notes: Optional[str] = None


class HistoryLessonPublishOut(BaseModel):
    id: UUID
    motif_id: UUID
    is_published: bool
    status: str
    content_validation_status: str
    published_at: Optional[datetime] = None
    verified_claim_ids: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Curriculum Competency Catalog Schemas (V5-T095 / Wave W09 / Slot A05)
# --------------------------------------------------------------------------- #
class CurriculumCompetencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    standard_framework: str
    domain: str
    name_vi: str
    name_en: str
    description_vi: str
    description_en: str
    grade_band_descriptors: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime


class CurriculumCompetencyListOut(BaseModel):
    items: list[CurriculumCompetencyOut]
    total: int


class CurriculumCompetencyRelicMappingIn(BaseModel):
    competency_id: UUID
    relic_urn_slug: Optional[str] = None
    relic_motif_id: Optional[str] = None
    entity_slug: Optional[str] = None
    grade_band: str = "GRADE_10_12"
    min_grade: int = Field(default=6, ge=6, le=12)
    max_grade: int = Field(default=12, ge=6, le=12)
    learning_activity_vi: str = Field(..., min_length=3)
    learning_activity_en: Optional[str] = None
    evidence_requirement_vi: str = Field(..., min_length=3)
    evidence_requirement_en: Optional[str] = None


class CurriculumCompetencyRelicMappingUpdateIn(BaseModel):
    relic_urn_slug: Optional[str] = None
    relic_motif_id: Optional[str] = None
    entity_slug: Optional[str] = None
    grade_band: Optional[str] = None
    min_grade: Optional[int] = Field(default=None, ge=6, le=12)
    max_grade: Optional[int] = Field(default=None, ge=6, le=12)
    learning_activity_vi: Optional[str] = None
    learning_activity_en: Optional[str] = None
    evidence_requirement_vi: Optional[str] = None
    evidence_requirement_en: Optional[str] = None


class CurriculumCompetencyRelicMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    competency_id: UUID
    competency_code: Optional[str] = None
    competency_name_vi: Optional[str] = None
    competency_domain: Optional[str] = None
    relic_urn_slug: Optional[str] = None
    relic_motif_id: Optional[str] = None
    entity_slug: Optional[str] = None
    grade_band: str
    min_grade: int
    max_grade: int
    learning_activity_vi: str
    learning_activity_en: Optional[str] = None
    evidence_requirement_vi: str
    evidence_requirement_en: Optional[str] = None
    status: str
    is_reviewed: bool
    review_warning: Optional[str] = None
    flag_count: int = 0
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class CurriculumCompetencyRelicMappingListOut(BaseModel):
    items: list[CurriculumCompetencyRelicMappingOut]
    total: int


class CurriculumCompetencyFlagIn(BaseModel):
    reason: str
    commentary: str = Field(..., min_length=5)
    suggested_correction: Optional[dict[str, Any]] = None


class CurriculumCompetencyFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mapping_id: UUID
    flagged_by_id: UUID
    flagged_by_name: Optional[str] = None
    reason: str
    commentary: str
    suggested_correction: Optional[dict[str, Any]] = None
    status: str
    resolved_by_id: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class CurriculumCompetencyFlagResolveIn(BaseModel):
    action: str = Field(default="resolved")  # "resolved" or "dismissed"
    resolution_notes: str = Field(..., min_length=3)
    updated_mapping_status: Optional[str] = None


# --------------------------------------------------------------------------- #
# Source-Locked Classroom Assignment & Rubric Schemas (V5-T033)
# --------------------------------------------------------------------------- #
class HistoryLessonAssignmentCreateIn(BaseModel):
    classroom_id: UUID
    lesson_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    instructions: Optional[str] = None
    due_at: Optional[datetime] = None
    points: int = Field(default=100, ge=1, le=1000)
    rubric: Optional[dict[str, Any]] = None
    source_ids: Optional[list[UUID]] = None
    claim_ids: Optional[list[UUID]] = None
    status: str = Field(default="draft")


class HistoryLessonAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    classroom_id: UUID
    lesson_id: UUID
    assigned_by_id: Optional[UUID] = None
    title: str
    instructions: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    points: int
    pinned_version: int
    pinned_lesson_snapshot: dict[str, Any] = Field(default_factory=dict)
    rubric: dict[str, Any] = Field(default_factory=dict)
    pinned_source_ids: list[str] = Field(default_factory=list)
    pinned_sources_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    pinned_claim_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class HistoryLessonAssignmentListOut(BaseModel):
    items: list[HistoryLessonAssignmentOut]
    total: int


class HistoryAssignmentAssessmentBasisOut(BaseModel):
    assignment_id: UUID
    classroom_id: UUID
    lesson_id: UUID
    pinned_version: int
    lesson_snapshot: dict[str, Any] = Field(default_factory=dict)
    rubric: dict[str, Any] = Field(default_factory=dict)
    pinned_source_ids: list[str] = Field(default_factory=list)
    pinned_sources: list[dict[str, Any]] = Field(default_factory=list)
    pinned_claim_ids: list[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None


class HistoryLessonAssignmentPublishOut(BaseModel):
    id: UUID
    classroom_id: UUID
    lesson_id: UUID
    status: str
    pinned_version: int
    published_at: datetime
    verified_claim_ids: list[str] = Field(default_factory=list)
    pinned_source_ids: list[str] = Field(default_factory=list)


class HistoryAssignmentSubmitIn(BaseModel):
    submission_content: dict[str, Any] = Field(..., description="Student response content, evidence citations, etc.")
    idempotency_key: Optional[str] = Field(default=None, description="Client idempotency key for network retry deduplication")


class HistoryAssignmentSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignment_id: UUID
    student_id: UUID
    status: str
    submission_content: dict[str, Any] = Field(default_factory=dict)
    assessment_basis_snapshot: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None
    score: Optional[float] = None
    rubric_evaluation: Optional[dict[str, Any]] = None
    teacher_feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    graded_by_id: Optional[UUID] = None


class HistoryAssignmentSubmissionListOut(BaseModel):
    items: list[HistoryAssignmentSubmissionOut]
    total: int


class HistoryAssignmentGradeIn(BaseModel):
    score: float = Field(..., ge=0.0)
    rubric_evaluation: Optional[dict[str, Any]] = None
    teacher_feedback: Optional[str] = None


# --------------------------------------------------------------------------- #
# Learning Outcome Measurement Schemas (V5-T039 / Wave W03 / Slot A09)
# --------------------------------------------------------------------------- #
class EthicsProtocolCreate(BaseModel):
    protocol_code: str = Field(..., min_length=3, max_length=100)
    title: str = Field(..., min_length=3, max_length=255)
    irb_institution: str = Field(..., min_length=3, max_length=255)
    status: str = Field(default="approved", description="draft, submitted, approved, revoked, expired")
    approved_by: Optional[str] = None
    valid_until: Optional[datetime] = None
    data_retention_days: int = Field(default=365, ge=30)
    participant_consent_required: bool = True


class EthicsProtocolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    protocol_code: str
    title: str
    irb_institution: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    data_retention_days: int
    participant_consent_required: bool
    created_at: datetime
    updated_at: datetime


class LearningOutcomeAssessmentCreate(BaseModel):
    ethics_protocol_id: UUID
    title: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    assessment_phase: str = Field(default="pre_test", description="pre_test, post_test, delayed_test")
    prompt_markdown: str = Field(..., min_length=10)
    target_urn_slug: Optional[str] = None
    target_motif_slug: Optional[str] = None
    source_ids: list[UUID] = Field(default_factory=list)
    claim_keys: list[str] = Field(default_factory=list)
    rubric_schema: Optional[dict[str, Any]] = None
    max_score: float = Field(default=100.0, ge=1.0)
    is_published: bool = True


class LearningOutcomeAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ethics_protocol_id: UUID
    title: str
    slug: str
    assessment_phase: str
    instrument_type: str
    target_urn_slug: Optional[str] = None
    target_motif_slug: Optional[str] = None
    prompt_markdown: str
    source_ids: list[Any] = Field(default_factory=list)
    claim_keys: list[Any] = Field(default_factory=list)
    rubric_schema: dict[str, Any] = Field(default_factory=dict)
    max_score: float
    is_published: bool
    created_at: datetime


class LearningOutcomeSubmissionCreate(BaseModel):
    responses: dict[str, Any] = Field(..., description="Student inquiry answers, essay, source analysis")
    citations_provided: list[str] = Field(default_factory=list, description="Primary source citations utilized")


class LearningOutcomeSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID
    student_id: UUID
    assessment_phase: str
    instrument_type: str
    responses: dict[str, Any] = Field(default_factory=dict)
    citations_provided: list[Any] = Field(default_factory=list)
    status: str
    submitted_at: datetime
    created_at: datetime


class RubricEvaluationCreate(BaseModel):
    rubric_scores: dict[str, float] = Field(..., description="Criteria scores, e.g. S1_SPATIAL: 25.0")
    feedback_markdown: Optional[str] = None
    evidence_notes: Optional[str] = None


class RubricEvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    assessor_id: UUID
    is_independent: bool
    rubric_scores: dict[str, Any]
    total_score: float
    feedback_markdown: Optional[str] = None
    evidence_notes: Optional[str] = None
    evaluated_at: datetime


class SubjectiveSurveyCreate(BaseModel):
    survey_name: str = Field(..., min_length=2, max_length=100)
    likert_responses: dict[str, int] = Field(..., description="Likert 1-5 ratings for enjoyment, perceived confidence, etc.")
    perceived_learning_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    satisfaction_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    feedback_text: Optional[str] = None


class SubjectiveSurveyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    survey_name: str
    instrument_type: str
    is_subjective_self_report: bool
    likert_responses: dict[str, Any]
    perceived_learning_score: Optional[float] = None
    satisfaction_score: Optional[float] = None
    feedback_text: Optional[str] = None
    submitted_at: datetime


class CausalLearningMetricComputeIn(BaseModel):
    student_id: UUID
    ethics_protocol_id: UUID
    pre_submission_id: UUID
    post_submission_id: UUID
    delayed_submission_id: Optional[UUID] = None
    # Negative abuse security check field: if survey data is passed
    survey_response_id: Optional[UUID] = None
    is_survey_data: bool = False


class CausalLearningMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    ethics_protocol_id: UUID
    pre_submission_id: UUID
    post_submission_id: UUID
    delayed_submission_id: Optional[UUID] = None
    pre_score: float
    post_score: float
    delayed_score: Optional[float] = None
    normalized_gain: float
    absolute_gain: float
    inter_rater_agreement: Optional[float] = None
    competency_gains: dict[str, Any] = Field(default_factory=dict)
    instrument_type: str
    is_valid_causal_claim: bool
    computed_at: datetime


class CohortCausalLearningMetricsOut(BaseModel):
    total_students: int
    mean_pre_score: float
    mean_post_score: float
    mean_normalized_gain: float
    effect_size_cohens_d: float
    mean_inter_rater_agreement: float
    competency_averages: dict[str, float]
    ethics_protocol_code: str


# --------------------------------------------------------------------------- #
# Mobile Lesson Quiz Sync & Server Assessment Schemas (V5-T057)
# --------------------------------------------------------------------------- #
class MobileQuizQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int = 1
    points: int = 10
    skill_type: Optional[str] = None
    skill_dimensions: Optional[list[str]] = None
    image_url: Optional[str] = None
    hint: Optional[str] = None
    content_validation_status: str = "valid"
    is_verified_content: bool = True


class MobilePracticeSyncOut(BaseModel):
    session_id: UUID
    items: list[MobileQuizQuestionOut]
    total_questions: int
    server_timestamp: datetime
    assessment_mode: str


class MobilePracticeSubmitIn(BaseModel):
    session_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    answers: dict[str, str] = Field(default_factory=dict)
    time_taken_seconds: Optional[int] = None
    # Client-claimed values to test and enforce server-authoritative grading / anti-abuse
    client_claimed_badges: Optional[list[str]] = None
    client_claimed_score: Optional[float] = None


class AwardedBadgeDetail(BaseModel):
    slug: str
    name: str
    icon_url: str
    xp_bonus: int = 0
    tier: str = "bronze"


class MobileQuestionResultDetail(BaseModel):
    question_id: UUID
    correct: bool
    user_answer: str
    explanation: Optional[str] = None


class MobilePracticeSubmitOut(BaseModel):
    success: bool
    session_id: Optional[UUID] = None
    score: int
    max_score: int
    percentage: int
    passed: bool
    xp_awarded: int
    total_xp: int
    server_verified: bool = True
    awarded_badges: list[AwardedBadgeDetail] = Field(default_factory=list)
    denied_badges: list[str] = Field(default_factory=list)
    details: list[MobileQuestionResultDetail] = Field(default_factory=list)
    previous_status: Optional[str] = None
    new_status: Optional[str] = None


class BadgeVerificationIn(BaseModel):
    badge_slug: str
    session_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None


class BadgeVerificationOut(BaseModel):
    badge_slug: str
    is_verified: bool
    earned_at: Optional[datetime] = None
    message: str


# --------------------------------------------------------------------------- #
# School Pilot Measurement & Ethics Schemas (V5-T100 / Wave W09 / Slot A10)
# --------------------------------------------------------------------------- #
class PilotGuardianConsentCreate(BaseModel):
    ethics_protocol_id: UUID
    student_id: UUID
    guardian_name: str = Field(..., min_length=2, max_length=255)
    guardian_email: str = Field(..., min_length=5, max_length=255)
    guardian_phone: Optional[str] = None
    relationship_type: str = Field(default="parent", description="parent, legal_guardian, custodian")
    verification_method: str = Field(default="school_roster", description="sms_otp, digital_signature, paper_signed, school_roster")
    notes: Optional[str] = None


class PilotGuardianConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ethics_protocol_id: UUID
    student_id: UUID
    guardian_name: str
    guardian_email: str
    guardian_phone: Optional[str] = None
    relationship_type: str
    consent_status: str
    verification_method: str
    verified_by_id: Optional[UUID] = None
    notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PilotGuardianConsentStatusOut(BaseModel):
    ethics_protocol_id: UUID
    student_id: UUID
    consent_status: str
    is_consent_verified: bool
    verified_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None


class PilotGuardianConsentWithdrawIn(BaseModel):
    reason: Optional[str] = None


class TeacherWorkloadLogCreate(BaseModel):
    school_id: Optional[UUID] = None
    classroom_id: Optional[UUID] = None
    ethics_protocol_id: Optional[UUID] = None
    activity_type: str = Field(default="rubric_grading", description="preparation, inquiry_instruction, rubric_grading, reflection")
    minutes_spent: float = Field(..., ge=0.0)
    submissions_evaluated_count: int = Field(default=0, ge=0)
    cognitive_load_rating: float = Field(default=50.0, ge=0.0, le=100.0)
    notes: Optional[str] = None


class TeacherWorkloadLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    school_id: Optional[UUID] = None
    classroom_id: Optional[UUID] = None
    ethics_protocol_id: Optional[UUID] = None
    activity_type: str
    minutes_spent: float
    submissions_evaluated_count: int
    cognitive_load_rating: float
    workload_category: str
    notes: Optional[str] = None
    logged_at: datetime


class TeacherWorkloadSummaryOut(BaseModel):
    teacher_id: Optional[UUID] = None
    school_id: Optional[UUID] = None
    total_minutes_logged: float
    total_submissions_evaluated: int
    avg_minutes_per_submission: float
    avg_cognitive_load: float
    overall_workload_status: str
    threshold_exceeded: bool
    burnout_risk_level: str
    recommendations: list[str] = Field(default_factory=list)


class RubricCalibrationCreate(BaseModel):
    submission_id: UUID
    assessor_a_id: UUID
    assessor_b_id: UUID
    tolerance_pct: float = Field(default=0.15, ge=0.0, le=1.0)


class RubricCalibrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    assessor_a_id: UUID
    assessor_b_id: UUID
    score_a: float
    score_b: float
    score_difference: float
    divergence_pct: float
    inter_rater_agreement: float
    tolerance_pct: float
    status: str
    consensus_score: Optional[float] = None
    criteria_breakdown: dict[str, Any] = Field(default_factory=dict)
    calibrated_at: datetime


class PilotDataRetentionAuditOut(BaseModel):
    ethics_protocol_id: Optional[UUID] = None
    retention_days_limit: int
    expired_submissions_count: int
    expired_evaluations_count: int
    expired_surveys_count: int
    expired_submission_ids: list[UUID] = Field(default_factory=list)
    expired_survey_ids: list[UUID] = Field(default_factory=list)
    audit_timestamp: datetime


class PilotDataRetentionPurgeIn(BaseModel):
    ethics_protocol_id: Optional[UUID] = None
    confirm_purge: bool = True


class PilotDataRetentionPurgeOut(BaseModel):
    purged_submissions_count: int
    purged_evaluations_count: int
    purged_surveys_count: int
    status: str
    policy: str
    purged_at: datetime


class LearningImprovementClaimValidateIn(BaseModel):
    claim_title: str
    claim_type: str = Field(default="learning_improvement", description="learning_improvement, causal_mastery, subjective_satisfaction")
    evidence_basis: str = Field(default="pre_post_inquiry_rubric", description="pre_post_inquiry_rubric, subjective_survey, sentiment_analysis, likert_scale")
    ethics_protocol_id: Optional[UUID] = None
    pre_post_metric_id: Optional[UUID] = None
    survey_id: Optional[UUID] = None


class LearningImprovementClaimValidateOut(BaseModel):
    claim_title: str
    claim_type: str
    evidence_basis: str
    is_valid_evidence_of_learning: bool
    rejection_reason: Optional[str] = None
    justification: str


# --------------------------------------------------------------------------- #
# Teacher 45-Minute Lesson Wizard Schemas (V5-T091 / Wave W09 / Slot A01)
# --------------------------------------------------------------------------- #
class HistoricalCompetencyItem(BaseModel):
    code: str = Field(..., description="e.g. S1_SPATIAL, S2_TEMPORAL, S3_EVIDENCE, S4_ARGUMENT")
    name_vi: str
    description_vi: str


class LessonWizardObjectivesIn(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    target_grade: str = Field(default="Lớp 10 THPT")
    duration_minutes: int = Field(default=45, ge=15, le=120)
    curriculum_framework: str = Field(default="CV 5512/BGDĐT")
    historical_competencies: list[HistoricalCompetencyItem] = Field(default_factory=list)
    qualities: list[str] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)


class LessonWizardMediaIn(BaseModel):
    media_variant: str = Field(default="2d_rubbing", description="2d_rubbing, 3d_model, hybrid")
    rubbing_url: Optional[str] = None
    model_url: Optional[str] = None
    target_mesh_name: Optional[str] = None
    fallback_2d_url: Optional[str] = None
    visual_annotations: list[dict[str, Any]] = Field(default_factory=list)


class LessonWizardInquiryActivity(BaseModel):
    activity_number: int = Field(..., ge=1, le=10)
    name_vi: str
    duration_minutes: int = Field(..., ge=1, le=90)
    objective_vi: str
    teacher_actions: list[str] = Field(default_factory=list)
    student_actions: list[str] = Field(default_factory=list)
    deliverables_vi: str
    assessment_criteria_vi: Optional[str] = None
    guiding_prompts_vi: list[str] = Field(default_factory=list)


class LessonWizardAssessmentIn(BaseModel):
    criteria: dict[str, Any] = Field(default_factory=dict, description="Rubric criteria (S1-S4 0-3 scale)")
    exit_ticket: dict[str, Any] = Field(default_factory=dict, description="Exit ticket prompt, expected evidence, time allowed")


class HistoryLessonPlanCreateIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    topic: str = Field(..., min_length=2, max_length=255)
    target_grade: str = Field(default="Lớp 10 THPT")
    duration_minutes: int = Field(default=45, ge=15, le=120)
    curriculum_framework: str = Field(default="CV 5512/BGDĐT")
    entity_id: Optional[UUID] = None
    urn_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    media_variant: str = Field(default="2d_rubbing")
    media_config: dict[str, Any] = Field(default_factory=dict)
    objectives: dict[str, Any] = Field(default_factory=dict)
    source_ids: list[UUID] = Field(default_factory=list)
    claim_ids: list[UUID] = Field(default_factory=list)
    inquiry_activities: list[dict[str, Any]] = Field(default_factory=list)
    assessment_rubric: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="draft", description="draft, published, archived")


class HistoryLessonPlanUpdateIn(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    target_grade: Optional[str] = None
    duration_minutes: Optional[int] = None
    curriculum_framework: Optional[str] = None
    entity_id: Optional[UUID] = None
    urn_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    media_variant: Optional[str] = None
    media_config: Optional[dict[str, Any]] = None
    objectives: Optional[dict[str, Any]] = None
    source_ids: Optional[list[UUID]] = None
    claim_ids: Optional[list[UUID]] = None
    inquiry_activities: Optional[list[dict[str, Any]]] = None
    assessment_rubric: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class HistoryLessonPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: Optional[UUID] = None
    title: str
    topic: str
    target_grade: str
    duration_minutes: int
    curriculum_framework: str
    status: str
    content_validation_status: str
    entity_id: Optional[UUID] = None
    urn_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    media_variant: str
    media_config: dict[str, Any] = Field(default_factory=dict)
    objectives: dict[str, Any] = Field(default_factory=dict)
    source_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    sources_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    claims_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    inquiry_activities: list[dict[str, Any]] = Field(default_factory=list)
    assessment_rubric: dict[str, Any] = Field(default_factory=dict)
    printable_handout: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class HistoryLessonPlanListOut(BaseModel):
    items: list[HistoryLessonPlanOut]
    total: int


class LessonWizardValidateIn(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    entity_id: Optional[UUID] = None
    urn_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    source_ids: list[UUID] = Field(default_factory=list)
    claim_ids: list[UUID] = Field(default_factory=list)
    objectives: dict[str, Any] = Field(default_factory=dict)
    media_variant: str = Field(default="2d_rubbing")
    media_config: dict[str, Any] = Field(default_factory=dict)
    inquiry_activities: list[dict[str, Any]] = Field(default_factory=list)
    assessment_rubric: dict[str, Any] = Field(default_factory=dict)


class LessonWizardValidateOut(BaseModel):
    can_publish: bool
    validation_status: str
    issues: list[str] = Field(default_factory=list)
    verified_claims_count: int = 0
    ineligible_claims_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class PrintableHandoutOut(BaseModel):
    header: dict[str, Any]
    objectives: dict[str, Any]
    sources: list[dict[str, Any]]
    visual_media: dict[str, Any]
    inquiry_stations: list[dict[str, Any]]
    exit_ticket: dict[str, Any]
    rubric: dict[str, Any]
    export_metadata: dict[str, Any]



