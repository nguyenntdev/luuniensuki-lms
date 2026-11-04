# -*- coding: utf-8 -*-
"""V5-T039 (Wave W03, Slot A09): Learning Outcome Measurement Scaffold Test Suite.

Audits and verifies:
1. Learning outcome measurement scaffold in backend/history_models.py and backend/domain/learning_outcome.py:
   - Source-based historical inquiry assessment tasks (pre_test, post_test, delayed_test).
   - Multi-criteria historical rubric (S1_SPATIAL, S2_TEMPORAL, S3_EVIDENCE, S4_ARGUMENT).
   - Independent assessor rubric evaluation with inter-rater agreement.
   - Separate subjective self-report surveys (Likert ratings/feelings).
2. Negative abuse prevention:
   - Subjective survey responses CANNOT produce causal learning mastery metrics.
   - Attempting to derive causal learning outcomes from survey data or feelings strictly fails with HTTP 422
     (CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY).
3. Ethics / IRB protocol enforcement:
   - Inquiry assessments require an active approved ethics protocol.
   - Assessments with draft, expired, or revoked protocols fail with ETHICS_PROTOCOL_REQUIRED (HTTP 422).
4. Independent assessor requirement:
   - Student self-grading is strictly forbidden for authoritative inquiry measurement (HTTP 403 INDEPENDENT_ASSESSOR_REQUIRED).
5. Pre/post causal learning measurement end-to-end:
   - Calculates Hake's normalized gain: g = (post - pre) / (max - pre).
   - Calculates paired Cohen's d effect size across cohorts.
   - Calculates dual evaluator inter-rater reliability.
   - Tracks per-competency gains across S1-S4.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import select

from backend.config import settings
from backend.domain.learning_outcome import (
    DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
    AssessmentInstrumentType,
    AssessmentPhase,
    EthicsProtocolRequiredError,
    EthicsProtocolStatus,
    IndependentAssessorRequiredError,
    InvalidRubricScoreError,
    SubjectiveSurveyCannotProduceCausalMetricsError,
    calculate_effect_size_cohens_d,
    calculate_inter_rater_reliability,
    calculate_normalized_learning_gain,
    validate_assessor_independence,
    validate_ethics_protocol_active,
    validate_rubric_scores,
    verify_causal_learning_eligibility,
)
from backend.history_models import (
    HistoryCausalLearningMetric,
    HistoryEthicsProtocol,
    HistoryLearningOutcomeAssessment,
    HistoryLearningOutcomeEvaluation,
    HistoryLearningOutcomeSubmission,
    HistorySubjectiveSurvey,
)
from backend.models import User, UserRole
from backend.security import create_jwt_token, hash_password
from backend.services import history_learning as hl


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
def _make_user(db_session, email: str, display_name: str, role: UserRole = UserRole.learner) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password("password123"),
        display_name=display_name,
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers_for(user: User) -> dict[str, str]:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": role_str},
    )
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Unit Tests: Domain Invariants & Math Calculators
# --------------------------------------------------------------------------- #
def test_domain_measurement_invariants_and_algorithms():
    """Verify Hake's normalized gain, Cohen's d, inter-rater reliability, and domain rules."""
    # 1. Hake's normalized learning gain: g = (post - pre) / (100 - pre)
    # Pre: 40%, Post: 70% -> (70 - 40) / (100 - 40) = 30 / 60 = 0.5000
    gain = calculate_normalized_learning_gain(40.0, 70.0, 100.0)
    assert gain == 0.5

    # Perfect post-test: Pre: 20%, Post: 100% -> 80 / 80 = 1.0000
    assert calculate_normalized_learning_gain(20.0, 100.0, 100.0) == 1.0

    # Negative gain (performance drop): Pre: 60%, Post: 40% -> (40 - 60) / 60 = -0.3333
    drop = calculate_normalized_learning_gain(60.0, 40.0, 100.0)
    assert drop < 0.0
    assert round(drop, 2) == -0.33

    # Boundary: Pre == 100, Post == 100
    assert calculate_normalized_learning_gain(100.0, 100.0, 100.0) == 0.0

    # 2. Cohen's d effect size
    pre_scores = [30.0, 35.0, 40.0, 45.0, 50.0]
    post_scores = [60.0, 65.0, 70.0, 75.0, 80.0]
    # Each gained exactly 30 points. With identical gains, difference variance is 0, so d handled gracefully
    pre_varied = [30.0, 40.0, 35.0, 50.0, 45.0]
    post_varied = [70.0, 85.0, 65.0, 90.0, 80.0]
    d = calculate_effect_size_cohens_d(pre_varied, post_varied)
    assert d > 2.0  # Large effect size

    # 3. Inter-rater reliability
    irr_perfect = calculate_inter_rater_reliability(85.0, 85.0, 100.0)
    assert irr_perfect == 1.0
    irr_close = calculate_inter_rater_reliability(80.0, 85.0, 100.0)
    assert irr_close == 0.95

    # 4. Rubric bounds checking
    rubric = DEFAULT_HISTORICAL_INQUIRY_RUBRIC
    valid_scores = {"S1_SPATIAL": 20.0, "S2_TEMPORAL": 22.0, "S3_EVIDENCE": 24.0, "S4_ARGUMENT": 21.0}
    total = validate_rubric_scores(rubric, valid_scores)
    assert total == 87.0

    # Negative points rejected
    with pytest.raises(InvalidRubricScoreError):
        validate_rubric_scores(rubric, {"S1_SPATIAL": -5.0, "S2_TEMPORAL": 20.0})

    # Points exceeding max_points (25.0) rejected
    with pytest.raises(InvalidRubricScoreError):
        validate_rubric_scores(rubric, {"S1_SPATIAL": 30.0, "S2_TEMPORAL": 20.0})

    # Unknown criterion rejected
    with pytest.raises(InvalidRubricScoreError):
        validate_rubric_scores(rubric, {"UNKNOWN_CRITERION": 15.0})

    # 5. Assessor independence
    uid1 = uuid.uuid4()
    uid2 = uuid.uuid4()
    validate_assessor_independence(uid1, uid2)  # Passes

    with pytest.raises(IndependentAssessorRequiredError):
        validate_assessor_independence(uid1, uid1)  # Student self-grading fails

    # 6. Ethics protocol active validation
    validate_ethics_protocol_active("approved", datetime.now(timezone.utc) + timedelta(days=30))
    with pytest.raises(EthicsProtocolRequiredError):
        validate_ethics_protocol_active("draft")
    with pytest.raises(EthicsProtocolRequiredError):
        validate_ethics_protocol_active("approved", datetime.now(timezone.utc) - timedelta(days=1))


# --------------------------------------------------------------------------- #
# Negative Abuse Test: Survey Feelings Cannot Produce Causal Mastery Metrics
# --------------------------------------------------------------------------- #
def test_negative_abuse_subjective_survey_cannot_produce_causal_mastery_metrics(client, db_session):
    """Negative Abuse Test (P0): Subjective self-report surveys CANNOT produce causal learning metrics.

    Verifies:
    1. Domain rule directly raises SubjectiveSurveyCannotProduceCausalMetricsError.
    2. Service layer rejects survey payload with AppError CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY (422).
    3. API endpoint POST /api/v1/history/learning-outcomes/causal-metrics rejects survey attempts with 422.
    """
    # 1. Pure domain guard
    with pytest.raises(SubjectiveSurveyCannotProduceCausalMetricsError) as exc_info:
        verify_causal_learning_eligibility(AssessmentInstrumentType.self_report_survey)
    assert "cannot produce causal learning mastery metrics" in str(exc_info.value)

    with pytest.raises(SubjectiveSurveyCannotProduceCausalMetricsError):
        verify_causal_learning_eligibility("source_inquiry_rubric", is_subjective_self_report=True)

    # 2. Service level guard
    admin = _make_user(db_session, f"admin_abuse_{uuid.uuid4().hex[:6]}@example.com", "Admin Abuse", UserRole.admin)
    student = _make_user(db_session, f"student_abuse_{uuid.uuid4().hex[:6]}@example.com", "Student Abuse", UserRole.learner)

    protocol = hl.create_ethics_protocol(
        db_session,
        {
            "protocol_code": f"ETH-ABUSE-{uuid.uuid4().hex[:6]}",
            "title": "Abuse Prevention Protocol",
            "irb_institution": "Hue Heritage Research Board",
            "status": "approved",
        },
    )

    survey = hl.submit_subjective_survey(
        db_session,
        student_id=student.id,
        survey_name="student_satisfaction_survey",
        likert_responses={"feel_confident": 5, "enjoyed_3d": 5},
        perceived_learning_score=4.8,
    )

    # Calling compute_causal_learning_outcome with is_survey_data=True fails
    with pytest.raises(hl.AppError) as app_exc:
        hl.compute_causal_learning_outcome(
            db_session,
            student_id=student.id,
            ethics_protocol_id=protocol.id,
            pre_submission_id=uuid.uuid4(),
            post_submission_id=uuid.uuid4(),
            is_survey_data=True,
            survey_response_id=survey.id,
        )
    assert app_exc.value.code == "CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY"
    assert app_exc.value.status_code == 422

    # 3. HTTP API level guard
    api_payload = {
        "student_id": str(student.id),
        "ethics_protocol_id": str(protocol.id),
        "pre_submission_id": str(uuid.uuid4()),
        "post_submission_id": str(uuid.uuid4()),
        "is_survey_data": True,
        "survey_response_id": str(survey.id),
    }
    res = client.post(
        "/api/v1/history/learning-outcomes/causal-metrics",
        json=api_payload,
        headers=_auth_headers_for(admin),
    )
    assert res.status_code == 422, res.text
    err = res.json()["error"]
    assert err["code"] == "CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY"
    assert "cannot produce causal learning mastery metrics" in err["message"].lower()


# --------------------------------------------------------------------------- #
# Integration Test: Ethics Protocol Enforcement
# --------------------------------------------------------------------------- #
def test_ethics_protocol_enforcement_on_inquiry_assessment_tasks(client, db_session):
    """Inquiry assessment tasks strictly require an active approved ethics protocol."""
    admin = _make_user(db_session, f"admin_eth_{uuid.uuid4().hex[:6]}@example.com", "Admin Eth", UserRole.admin)

    # 1. Create a draft protocol (not approved)
    res_proto = client.post(
        "/api/v1/history/learning-outcomes/ethics-protocols",
        json={
            "protocol_code": f"ETH-DRAFT-{uuid.uuid4().hex[:6]}",
            "title": "Draft Protocol",
            "irb_institution": "University Ethics Board",
            "status": "draft",
        },
        headers=_auth_headers_for(admin),
    )
    assert res_proto.status_code == 200, res_proto.text
    draft_proto_id = res_proto.json()["id"]

    # 2. Attempting to create an inquiry assessment under a draft protocol fails (422)
    assess_payload = {
        "ethics_protocol_id": draft_proto_id,
        "title": "Pre-test Cửu Đỉnh Source Analysis",
        "slug": f"assess-draft-{uuid.uuid4().hex[:6]}",
        "assessment_phase": "pre_test",
        "prompt_markdown": "Hãy khảo sát văn bản khắc trên Cao Đỉnh và đối chiếu với Khâm Định Đại Nam Hội Điển Sự Lệ.",
    }
    res_assess = client.post(
        "/api/v1/history/learning-outcomes/assessments",
        json=assess_payload,
        headers=_auth_headers_for(admin),
    )
    assert res_assess.status_code == 422, res_assess.text
    assert res_assess.json()["error"]["code"] == "ETHICS_PROTOCOL_REQUIRED"

    # 3. Create an approved protocol
    res_appr = client.post(
        "/api/v1/history/learning-outcomes/ethics-protocols",
        json={
            "protocol_code": f"ETH-APPR-{uuid.uuid4().hex[:6]}",
            "title": "Approved Research Protocol",
            "irb_institution": "National Heritage Research Ethics Committee",
            "status": "approved",
            "approved_by": "Prof. Tran Van Giap",
        },
        headers=_auth_headers_for(admin),
    )
    assert res_appr.status_code == 200, res_appr.text
    appr_proto_id = res_appr.json()["id"]

    # 4. Creating assessment under approved protocol succeeds
    assess_payload["ethics_protocol_id"] = appr_proto_id
    assess_payload["slug"] = f"assess-appr-{uuid.uuid4().hex[:6]}"
    res_valid = client.post(
        "/api/v1/history/learning-outcomes/assessments",
        json=assess_payload,
        headers=_auth_headers_for(admin),
    )
    assert res_valid.status_code == 200, res_valid.text
    data = res_valid.json()
    assert data["title"] == "Pre-test Cửu Đỉnh Source Analysis"
    assert data["assessment_phase"] == "pre_test"
    assert data["instrument_type"] == "source_inquiry_rubric"


# --------------------------------------------------------------------------- #
# Integration Test: Independent Assessor Requirement & Rubric Scoring
# --------------------------------------------------------------------------- #
def test_independent_assessor_scoring_and_dual_evaluation_agreement(client, db_session):
    """Students cannot score themselves; independent assessors evaluate using S1-S4 rubric."""
    admin = _make_user(db_session, f"admin_eval_{uuid.uuid4().hex[:6]}@example.com", "Admin Eval", UserRole.admin)
    teacher2 = _make_user(db_session, f"teacher2_{uuid.uuid4().hex[:6]}@example.com", "Teacher Two", UserRole.teacher)
    student = _make_user(db_session, f"student_eval_{uuid.uuid4().hex[:6]}@example.com", "Student Learner", UserRole.learner)

    # 1. Admin creates protocol & assessment
    proto = hl.create_ethics_protocol(
        db_session,
        {
            "protocol_code": f"ETH-RUBRIC-{uuid.uuid4().hex[:6]}",
            "title": "Rubric Scoring Protocol",
            "irb_institution": "Heritage Education Institute",
            "status": "approved",
        },
    )
    assessment = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": proto.id,
            "title": "Post-test Historical Synthesis",
            "slug": f"post-test-{uuid.uuid4().hex[:6]}",
            "assessment_phase": "post_test",
            "prompt_markdown": "Phân tích mối quan hệ giữa hình tượng sông Gianh trên Tuyên Đỉnh và ranh giới lịch sử thời Trịnh - Nguyễn.",
            "rubric_schema": DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
        },
    )

    # 2. Student submits inquiry response
    sub_res = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{assessment.id}/submit",
        json={
            "responses": {
                "essay": "Hình tượng sông Gianh (Linh Giang) trên Tuyên Đỉnh biểu thị biên giới phân tranh thời Trịnh - Nguyễn...",
                "sources_consulted": ["Đại Nam Thực Lục Chính Biên Đệ Nhị Kỷ"],
            },
            "citations_provided": ["Khâm Định Đại Nam Hội Điển Sự Lệ, Quyển 162"],
        },
        headers=_auth_headers_for(student),
    )
    assert sub_res.status_code == 200, sub_res.text
    submission_id = sub_res.json()["id"]

    # 3. Student attempts to evaluate their own submission -> Forbidden 403
    with pytest.raises(hl.AppError) as app_err:
        hl.evaluate_learning_outcome_submission(
            db_session,
            submission_id=uuid.UUID(submission_id),
            assessor_id=student.id,  # Student as assessor
            rubric_scores={"S1_SPATIAL": 25.0, "S2_TEMPORAL": 25.0, "S3_EVIDENCE": 25.0, "S4_ARGUMENT": 25.0},
        )
    assert app_err.value.code == "INDEPENDENT_ASSESSOR_REQUIRED"
    assert app_err.value.status_code == 403

    # 4. Assessor 1 evaluates submission
    eval1_res = client.post(
        f"/api/v1/history/learning-outcomes/submissions/{submission_id}/evaluate",
        json={
            "rubric_scores": {"S1_SPATIAL": 22.0, "S2_TEMPORAL": 20.0, "S3_EVIDENCE": 24.0, "S4_ARGUMENT": 22.0},
            "feedback_markdown": "Lập luận sắc bén, trích dẫn chuẩn xác Hội Điển Sự Lệ.",
        },
        headers=_auth_headers_for(admin),
    )
    assert eval1_res.status_code == 200, eval1_res.text
    assert eval1_res.json()["total_score"] == 88.0
    assert eval1_res.json()["is_independent"] is True

    # 5. Assessor 2 (second independent rater) evaluates submission
    eval2_res = client.post(
        f"/api/v1/history/learning-outcomes/submissions/{submission_id}/evaluate",
        json={
            "rubric_scores": {"S1_SPATIAL": 21.0, "S2_TEMPORAL": 21.0, "S3_EVIDENCE": 23.0, "S4_ARGUMENT": 21.0},
            "feedback_markdown": "Đối chiếu tư liệu chặt chẽ.",
        },
        headers=_auth_headers_for(teacher2),
    )
    assert eval2_res.status_code == 200, eval2_res.text
    assert eval2_res.json()["total_score"] == 86.0

    # 6. Inter-rater agreement between Assessor 1 (88.0) and Assessor 2 (86.0)
    agreement = calculate_inter_rater_reliability(88.0, 86.0, 100.0)
    assert agreement == 0.98  # 98% agreement


# --------------------------------------------------------------------------- #
# Integration Test: End-to-End Pre/Post Causal Learning Outcome Flow
# --------------------------------------------------------------------------- #
def test_causal_learning_outcome_pre_post_end_to_end_flow(client, db_session):
    """Full causal learning outcome measurement lifecycle with paired pre/post tasks."""
    admin = _make_user(db_session, f"admin_causal_{uuid.uuid4().hex[:6]}@example.com", "Admin Causal", UserRole.admin)
    student1 = _make_user(db_session, f"student_c1_{uuid.uuid4().hex[:6]}@example.com", "Student One", UserRole.learner)
    student2 = _make_user(db_session, f"student_c2_{uuid.uuid4().hex[:6]}@example.com", "Student Two", UserRole.learner)

    # 1. Create ethics protocol
    proto_res = client.post(
        "/api/v1/history/learning-outcomes/ethics-protocols",
        json={
            "protocol_code": f"ETH-CAUSAL-{uuid.uuid4().hex[:6]}",
            "title": "Cửu Đỉnh Source Inquiry Causal Study",
            "irb_institution": "Vietnam National Heritage Research Council",
            "status": "approved",
            "approved_by": "Dr. Le Van Hien",
        },
        headers=_auth_headers_for(admin),
    )
    assert proto_res.status_code == 200, proto_res.text
    protocol_id = proto_res.json()["id"]

    # 2. Create pre-test assessment
    pre_assess = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": uuid.UUID(protocol_id),
            "title": "Pre-test: Đại Nam Geography and Annals",
            "slug": f"pre-test-{uuid.uuid4().hex[:6]}",
            "assessment_phase": "pre_test",
            "prompt_markdown": "Trình bày hiểu biết ban đầu về ý nghĩa địa lý các dòng sông lớn khắc trên Cửu Đỉnh.",
            "rubric_schema": DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
        },
    )

    # 3. Create post-test assessment
    post_assess = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": uuid.UUID(protocol_id),
            "title": "Post-test: Đại Nam Geography and Annals",
            "slug": f"post-test-{uuid.uuid4().hex[:6]}",
            "assessment_phase": "post_test",
            "prompt_markdown": "Vận dụng Khâm Định Đại Nam Hội Điển Sự Lệ để chứng minh tính thống nhất lãnh thổ qua đồ án sông núi.",
            "rubric_schema": DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
        },
    )

    # 4. Student 1 takes pre-test (baseline) and post-test (intervention)
    s1_pre_res = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{pre_assess.id}/submit",
        json={
            "responses": {"essay": "Em chỉ biết một vài con sông như sông Hương và sông Gianh."},
            "citations_provided": [],
        },
        headers=_auth_headers_for(student1),
    )
    assert s1_pre_res.status_code == 200
    s1_pre_id = s1_pre_res.json()["id"]

    s1_post_res = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{post_assess.id}/submit",
        json={
            "responses": {
                "essay": "Qua Châu bản triều Nguyễn và Hội Điển Sự Lệ, 9 đỉnh đúc các danh sơn đại xuyên thể hiện chủ quyền toàn vẹn...",
            },
            "citations_provided": ["Khâm Định Đại Nam Hội Điển Sự Lệ", "Đại Nam Thực Lục Chính Biên"],
        },
        headers=_auth_headers_for(student1),
    )
    assert s1_post_res.status_code == 200
    s1_post_id = s1_post_res.json()["id"]

    # 5. Assessor evaluates Student 1 pre-test (low baseline) and post-test (high mastery)
    client.post(
        f"/api/v1/history/learning-outcomes/submissions/{s1_pre_id}/evaluate",
        json={
            "rubric_scores": {"S1_SPATIAL": 10.0, "S2_TEMPORAL": 10.0, "S3_EVIDENCE": 5.0, "S4_ARGUMENT": 10.0},
            "feedback_markdown": "Chưa nắm rõ tư liệu gốc.",
        },
        headers=_auth_headers_for(admin),
    )  # Total 35.0

    client.post(
        f"/api/v1/history/learning-outcomes/submissions/{s1_post_id}/evaluate",
        json={
            "rubric_scores": {"S1_SPATIAL": 22.0, "S2_TEMPORAL": 21.0, "S3_EVIDENCE": 23.0, "S4_ARGUMENT": 22.0},
            "feedback_markdown": "Nắm vững phương pháp khảo cứu sử liệu gốc.",
        },
        headers=_auth_headers_for(admin),
    )  # Total 88.0

    # 6. Compute causal learning metric for Student 1
    # Pre: 35.0, Post: 88.0 -> Normalized gain g = (88 - 35) / (100 - 35) = 53 / 65 = 0.8154
    compute_payload = {
        "student_id": str(student1.id),
        "ethics_protocol_id": protocol_id,
        "pre_submission_id": s1_pre_id,
        "post_submission_id": s1_post_id,
    }
    metric_res = client.post(
        "/api/v1/history/learning-outcomes/causal-metrics",
        json=compute_payload,
        headers=_auth_headers_for(admin),
    )
    assert metric_res.status_code == 200, metric_res.text
    metric_data = metric_res.json()

    assert metric_data["pre_score"] == 35.0
    assert metric_data["post_score"] == 88.0
    assert metric_data["absolute_gain"] == 53.0
    assert metric_data["normalized_gain"] == 0.8154
    assert metric_data["is_valid_causal_claim"] is True
    assert metric_data["instrument_type"] == "source_inquiry_rubric"

    # Per-competency gains
    assert metric_data["competency_gains"]["S3_EVIDENCE"] == 18.0  # 23 - 5
    assert metric_data["competency_gains"]["S1_SPATIAL"] == 12.0   # 22 - 10

    # 7. Student 2 also completes the flow
    s2_pre = hl.submit_learning_outcome_assessment(db_session, pre_assess.id, student2.id, {"essay": "pre"}, [])
    s2_post = hl.submit_learning_outcome_assessment(db_session, post_assess.id, student2.id, {"essay": "post"}, ["Hội Điển"])
    hl.evaluate_learning_outcome_submission(
        db_session, s2_pre.id, admin.id, {"S1_SPATIAL": 12.0, "S2_TEMPORAL": 12.0, "S3_EVIDENCE": 8.0, "S4_ARGUMENT": 8.0}
    )  # 40.0
    hl.evaluate_learning_outcome_submission(
        db_session, s2_post.id, admin.id, {"S1_SPATIAL": 20.0, "S2_TEMPORAL": 20.0, "S3_EVIDENCE": 22.0, "S4_ARGUMENT": 20.0}
    )  # 82.0
    hl.compute_causal_learning_outcome(
        db_session,
        student_id=student2.id,
        ethics_protocol_id=uuid.UUID(protocol_id),
        pre_submission_id=s2_pre.id,
        post_submission_id=s2_post.id,
    )

    # 8. Check Cohort Aggregation Endpoint
    cohort_res = client.get(
        f"/api/v1/history/learning-outcomes/cohort-metrics/{protocol_id}",
        headers=_auth_headers_for(admin),
    )
    assert cohort_res.status_code == 200, cohort_res.text
    cohort_data = cohort_res.json()

    assert cohort_data["total_students"] == 2
    assert cohort_data["mean_pre_score"] == 37.5  # (35 + 40) / 2
    assert cohort_data["mean_post_score"] == 85.0  # (88 + 82) / 2
    assert cohort_data["mean_normalized_gain"] > 0.75
    assert cohort_data["effect_size_cohens_d"] > 0.0
    assert "S3_EVIDENCE" in cohort_data["competency_averages"]


# --------------------------------------------------------------------------- #
# Integration Test: Separate Subjective Survey Isolation
# --------------------------------------------------------------------------- #
def test_separate_subjective_self_report_survey_isolation(client, db_session):
    """Subjective self-report surveys are stored separately and cannot pollute objective assessment."""
    student = _make_user(db_session, f"student_survey_{uuid.uuid4().hex[:6]}@example.com", "Student Survey", UserRole.learner)

    survey_res = client.post(
        "/api/v1/history/learning-outcomes/surveys",
        json={
            "survey_name": "post_inquiry_student_feedback",
            "likert_responses": {
                "enjoyment": 5,
                "confidence_with_sources": 4,
                "visual_clarity_3d": 5,
            },
            "perceived_learning_score": 4.5,
            "satisfaction_score": 5.0,
            "feedback_text": "Em rất thích việc đối chiếu bản dập 2D và mô hình 3D của Cửu Đỉnh.",
        },
        headers=_auth_headers_for(student),
    )
    assert survey_res.status_code == 200, survey_res.text
    survey_data = survey_res.json()

    assert survey_data["instrument_type"] == "self_report_survey"
    assert survey_data["is_subjective_self_report"] is True
    assert survey_data["perceived_learning_score"] == 4.5

    # Verify directly in DB
    record = db_session.get(HistorySubjectiveSurvey, uuid.UUID(survey_data["id"]))
    assert record is not None
    assert record.instrument_type == "self_report_survey"
    assert record.is_subjective_self_report is True
