# -*- coding: utf-8 -*-
"""V5-T100 (Wave W09, Slot A10): School Pilot Measurement & Ethics Protocol Test Suite.

Audits and verifies:
1. Formal IRB / Ethics Research Protocol Governance:
   - Protocol lifecycle states: draft, submitted, approved, revoked, expired.
   - Active approved protocol strictly required for inquiry assessments and submissions.
2. Guardian Informed Consent Verification (Decree 13/2023/ND-CP):
   - Prior informed consent registration for minor participants.
   - Pending consent blocks empirical assessment submissions (HTTP 403 GUARDIAN_CONSENT_REQUIRED).
   - Staff/Teacher verification grants verified status, allowing assessments.
   - Consent withdrawal immediately suspends research participation (HTTP 403 GUARDIAN_CONSENT_WITHDRAWN)
     and excludes student data from cohort research metrics.
3. Teacher Workload Assessment & Burnout Defense:
   - Quantitative tracking of preparation, instruction, grading time, and NASA-TLX cognitive load index.
   - Automated categorization (optimal, acceptable, excessive) based on safety thresholds (<=15 min/submission).
   - Summary endpoint computes burnout risk and generates actionable mitigating recommendations.
4. Dual-Assessor Rubric Calibration:
   - S1-S4 rubric evaluations by independent assessors.
   - High agreement within 15% tolerance yields 'calibrated' status and consensus score.
   - Discrepancy > 15% yields 'divergent_requires_review' status with criteria breakdown.
5. Student Data Retention & Scheduled Purging:
   - Audit identifies records past retention limit (data_retention_days).
   - Automated purge scrubs student PII to '[RETENTION_PURGED]' per Decree 13/2023/ND-CP.
6. Negative Abuse Invariant:
   - Results based solely on subjective sentiment or feelings surveys CANNOT be labeled as
     evidence of learning improvement (HTTP 422 CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY).
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
    EthicsProtocolStatus,
    PilotConsentStatus,
    RubricCalibrationStatus,
    SubjectiveSurveyCannotProduceCausalMetricsError,
    TeacherWorkloadCategory,
    calculate_teacher_workload_category,
    calibrate_dual_rubric_scores,
    verify_guardian_consent_status,
    verify_learning_improvement_claim_basis,
)
from backend.history_models import (
    HistoryCausalLearningMetric,
    HistoryEthicsProtocol,
    HistoryLearningOutcomeAssessment,
    HistoryLearningOutcomeEvaluation,
    HistoryLearningOutcomeSubmission,
    HistoryPilotGuardianConsent,
    HistoryRubricCalibration,
    HistorySubjectiveSurvey,
    HistoryTeacherWorkloadLog,
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
        password_hash=hash_password("pilot_secret_123"),
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
# Test 1: Formal IRB / Ethics Research Protocol Governance
# --------------------------------------------------------------------------- #
def test_formal_irb_ethics_protocol_governance(client, db_session):
    """Verify IRB ethics protocol registration, lifecycle states, and active approval enforcement."""
    admin = _make_user(db_session, f"admin_irb_{uuid.uuid4().hex[:6]}@school.vn", "Admin IRB", UserRole.admin)
    headers = _auth_headers_for(admin)

    # 1. Register a protocol via API
    proto_code = f"IRB-HUE-2026-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/v1/history/learning-outcomes/ethics-protocols",
        json={
            "protocol_code": proto_code,
            "title": "Nghiên cứu Thực nghiệm Khảo sát Cửu Đỉnh tại THPT Huế",
            "irb_institution": "Hội đồng Đạo đức Nghiên cứu Đại học Huế",
            "status": "approved",
            "approved_by": "GS. Trần Văn Nghiên",
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
            "data_retention_days": 365,
            "participant_consent_required": True,
        },
        headers=headers,
    )
    assert res.status_code == 200, res.text
    proto_data = res.json()
    assert proto_data["protocol_code"] == proto_code
    assert proto_data["status"] == "approved"
    assert proto_data["participant_consent_required"] is True

    # 2. Reject duplicate protocol code (409)
    res_dup = client.post(
        "/api/v1/history/learning-outcomes/ethics-protocols",
        json={
            "protocol_code": proto_code,
            "title": "Duplicate Protocol",
            "irb_institution": "Đại học Huế",
            "status": "approved",
        },
        headers=headers,
    )
    assert res_dup.status_code == 409

    # 3. Assessment creation blocked if protocol is in draft status (HTTP 422)
    draft_proto = hl.create_ethics_protocol(
        db_session,
        {
            "protocol_code": f"DRAFT-{uuid.uuid4().hex[:6]}",
            "title": "Giao thức Đang soạn thảo",
            "irb_institution": "Đại học Sư phạm Huế",
            "status": "draft",
        },
    )
    res_draft_assess = client.post(
        "/api/v1/history/learning-outcomes/assessments",
        json={
            "ethics_protocol_id": str(draft_proto.id),
            "title": "Bài tập Khảo sát Thực nghiệm",
            "slug": f"draft-inquiry-{uuid.uuid4().hex[:6]}",
            "prompt_markdown": "Hãy quan sát hình tượng Biển Đông trên Cao Đỉnh và đối chiếu sử liệu.",
        },
        headers=headers,
    )
    assert res_draft_assess.status_code == 422
    assert "ETHICS_PROTOCOL_REQUIRED" in res_draft_assess.text


# --------------------------------------------------------------------------- #
# Test 2: Guardian Informed Consent Verification & Withdrawal
# --------------------------------------------------------------------------- #
def test_guardian_informed_consent_verification_and_withdrawal(client, db_session):
    """Verify prior guardian consent registration, verification, and revocation lifecycle."""
    teacher = _make_user(db_session, f"teacher_{uuid.uuid4().hex[:6]}@school.vn", "Thầy Lê Văn", UserRole.teacher)
    student = _make_user(db_session, f"student_minor_{uuid.uuid4().hex[:6]}@school.vn", "Em Nguyễn An", UserRole.learner)
    t_headers = _auth_headers_for(teacher)
    s_headers = _auth_headers_for(student)

    protocol = hl.create_ethics_protocol(
        db_session,
        {
            "protocol_code": f"IRB-CONSENT-{uuid.uuid4().hex[:6]}",
            "title": "Nghiên cứu Có Sự đồng thuận của Phụ huynh",
            "irb_institution": "Sở GD&ĐT Thừa Thiên Huế",
            "status": "approved",
            "participant_consent_required": True,
        },
    )

    assessment = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": protocol.id,
            "title": "Đánh giá Năng lực Sử liệu Pre-Test",
            "slug": f"pre-consent-{uuid.uuid4().hex[:6]}",
            "prompt_markdown": "Đọc bản dập Cao Đỉnh mục Đông Hải và phân tích.",
        },
    )

    # 1. Register guardian consent (status starts as 'pending')
    res_reg = client.post(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol.id}/consent",
        json={
            "ethics_protocol_id": str(protocol.id),
            "student_id": str(student.id),
            "guardian_name": "Nguyễn Văn Ba (Phụ huynh)",
            "guardian_email": "ba.nguyen@family.vn",
            "guardian_phone": "0905123456",
            "relationship_type": "parent",
            "verification_method": "sms_otp",
            "notes": "Đã gửi bản mô tả nghiên cứu và phiếu đồng thuận số #1042",
        },
        headers=s_headers,
    )
    assert res_reg.status_code == 200, res_reg.text
    consent_id = res_reg.json()["id"]
    assert res_reg.json()["consent_status"] == "pending"

    # Query status -> pending
    res_status = client.get(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol.id}/consent/{student.id}/status",
        headers=s_headers,
    )
    assert res_status.status_code == 200
    assert res_status.json()["consent_status"] == "pending"
    assert res_status.json()["is_consent_verified"] is False

    # 2. Student submission blocked while consent is pending (HTTP 403)
    res_sub_blocked = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{assessment.id}/submit",
        json={
            "responses": {"q1": "Hình tượng khắc trên Cao Đỉnh biểu trưng cho chủ quyền biển đảo."},
            "citations_provided": ["Khâm Định Đại Nam Hội Điển Sự Lệ quyển 192"],
        },
        headers=s_headers,
    )
    assert res_sub_blocked.status_code == 403
    assert "GUARDIAN_CONSENT_REQUIRED" in res_sub_blocked.text

    # 3. Teacher verifies consent
    res_verify = client.post(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol.id}/consent/{consent_id}/verify",
        headers=t_headers,
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["consent_status"] == "verified"
    assert res_verify.json()["verified_at"] is not None

    # Query status -> verified
    res_status2 = client.get(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol.id}/consent/{student.id}/status",
        headers=s_headers,
    )
    assert res_status2.json()["is_consent_verified"] is True

    # 4. Now student submission is ACCEPTED
    res_sub_ok = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{assessment.id}/submit",
        json={
            "responses": {"q1": "Hình tượng khắc trên Cao Đỉnh biểu trưng cho chủ quyền biển đảo."},
            "citations_provided": ["Khâm Định Đại Nam Hội Điển Sự Lệ quyển 192"],
        },
        headers=s_headers,
    )
    assert res_sub_ok.status_code == 200
    assert res_sub_ok.json()["status"] == "submitted"

    # 5. Guardian withdraws consent
    res_withdraw = client.post(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol.id}/consent/{consent_id}/withdraw",
        json={"reason": "Phụ huynh yêu cầu rút khỏi thử nghiệm do chuyển trường"},
        headers=s_headers,
    )
    assert res_withdraw.status_code == 200
    assert res_withdraw.json()["consent_status"] == "withdrawn"
    assert res_withdraw.json()["withdrawn_at"] is not None

    # 6. Future submission blocked (HTTP 403 GUARDIAN_CONSENT_WITHDRAWN)
    res_sub_withdrawn = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{assessment.id}/submit",
        json={"responses": {"q1": "Câu trả lời bổ sung"}},
        headers=s_headers,
    )
    assert res_sub_withdrawn.status_code == 403
    assert "GUARDIAN_CONSENT_WITHDRAWN" in res_sub_withdrawn.text


# --------------------------------------------------------------------------- #
# Test 3: Teacher Workload Assessment & Burnout Defense
# --------------------------------------------------------------------------- #
def test_teacher_workload_assessment_and_burnout_prevention(client, db_session):
    """Verify teacher workload logging, cognitive load indexing, and burnout safety thresholds."""
    teacher = _make_user(db_session, f"teacher_workload_{uuid.uuid4().hex[:6]}@school.vn", "Cô Mai", UserRole.teacher)
    headers = _auth_headers_for(teacher)

    # 1. Domain calculator tests
    assert calculate_teacher_workload_category(minutes_spent=30.0, submissions_count=5, cognitive_load_rating=35.0) == "optimal"
    assert calculate_teacher_workload_category(minutes_spent=50.0, submissions_count=5, cognitive_load_rating=50.0) == "acceptable"
    # > 15 min per submission -> excessive
    assert calculate_teacher_workload_category(minutes_spent=100.0, submissions_count=5, cognitive_load_rating=50.0) == "excessive"
    # Cognitive load > 70 -> excessive
    assert calculate_teacher_workload_category(minutes_spent=30.0, submissions_count=5, cognitive_load_rating=85.0) == "excessive"

    # 2. Log optimal grading workload via API
    res_opt = client.post(
        "/api/v1/history/learning-outcomes/teacher-workload",
        json={
            "activity_type": "rubric_grading",
            "minutes_spent": 35.0,
            "submissions_evaluated_count": 5,
            "cognitive_load_rating": 35.0,
            "notes": "Chấm 5 bài kiểm tra Pre-test với thang đo S1-S4",
        },
        headers=headers,
    )
    assert res_opt.status_code == 200, res_opt.text
    assert res_opt.json()["workload_category"] == "optimal"

    # 3. Log excessive workload session via API
    res_exc = client.post(
        "/api/v1/history/learning-outcomes/teacher-workload",
        json={
            "activity_type": "rubric_grading",
            "minutes_spent": 120.0,
            "submissions_evaluated_count": 4,
            "cognitive_load_rating": 80.0,
            "notes": "Phát hiện nhiều bất đồng trong lập luận của học sinh, phải tra cứu bổ sung Châu bản",
        },
        headers=headers,
    )
    assert res_exc.status_code == 200
    assert res_exc.json()["workload_category"] == "excessive"

    # 4. Fetch workload summary & verify burnout warning triggers
    res_summary = client.get(
        f"/api/v1/history/learning-outcomes/teacher-workload/summary?teacher_id={teacher.id}",
        headers=headers,
    )
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_minutes_logged"] == 155.0
    assert summary["total_submissions_evaluated"] == 9
    assert summary["threshold_exceeded"] is True
    assert summary["burnout_risk_level"] == "high"
    assert len(summary["recommendations"]) >= 1
    assert any("Deploy secondary independent assessor" in r for r in summary["recommendations"])


# --------------------------------------------------------------------------- #
# Test 4: Dual-Assessor Rubric Calibration & Divergence Flags
# --------------------------------------------------------------------------- #
def test_dual_assessor_rubric_calibration_and_agreement(client, db_session):
    """Verify dual independent rubric calibration, inter-rater reliability, and divergence flagging."""
    admin = _make_user(db_session, f"admin_calib_{uuid.uuid4().hex[:6]}@school.vn", "Admin Calib", UserRole.admin)
    assessor_a = _make_user(db_session, f"assessor_a_{uuid.uuid4().hex[:6]}@school.vn", "Giám khảo A", UserRole.teacher)
    assessor_b = _make_user(db_session, f"assessor_b_{uuid.uuid4().hex[:6]}@school.vn", "Giám khảo B", UserRole.teacher)
    student = _make_user(db_session, f"student_calib_{uuid.uuid4().hex[:6]}@school.vn", "Học sinh C", UserRole.learner)
    admin_headers = _auth_headers_for(admin)

    # 1. Pure domain calibration function
    scores_high_agree_a = {"S1_SPATIAL": 22.0, "S2_TEMPORAL": 21.0, "S3_EVIDENCE": 24.0, "S4_ARGUMENT": 20.0}  # total 87
    scores_high_agree_b = {"S1_SPATIAL": 20.0, "S2_TEMPORAL": 22.0, "S3_EVIDENCE": 23.0, "S4_ARGUMENT": 21.0}  # total 86
    calib_ok = calibrate_dual_rubric_scores(scores_high_agree_a, scores_high_agree_b, max_score=100.0, tolerance_pct=0.15)
    assert calib_ok["status"] == RubricCalibrationStatus.calibrated.value
    assert calib_ok["score_difference"] == 1.0
    assert calib_ok["divergence_pct"] == 0.01
    assert calib_ok["inter_rater_agreement"] == 0.99
    assert calib_ok["consensus_score"] == 86.5

    scores_divergent_b = {"S1_SPATIAL": 12.0, "S2_TEMPORAL": 14.0, "S3_EVIDENCE": 15.0, "S4_ARGUMENT": 11.0}  # total 52
    calib_div = calibrate_dual_rubric_scores(scores_high_agree_a, scores_divergent_b, max_score=100.0, tolerance_pct=0.15)
    assert calib_div["status"] == RubricCalibrationStatus.divergent_requires_review.value
    assert calib_div["score_difference"] == 35.0
    assert calib_div["divergence_pct"] == 0.35
    assert calib_div["consensus_score"] is None

    # 2. Database & API integration test
    protocol = hl.create_ethics_protocol(
        db_session,
        {
            "protocol_code": f"ETH-CALIB-{uuid.uuid4().hex[:6]}",
            "title": "Nghiên cứu Chuẩn hóa Thang đo",
            "irb_institution": "Đại học Sư phạm",
            "status": "approved",
            "participant_consent_required": False,
        },
    )
    assessment = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": protocol.id,
            "title": "Bài tập Khảo sát Độc lập",
            "slug": f"calib-assess-{uuid.uuid4().hex[:6]}",
            "prompt_markdown": "Phân tích địa lý kinh tế trên Tuyên Đỉnh.",
        },
    )
    submission = hl.submit_learning_outcome_assessment(
        db_session,
        assessment_id=assessment.id,
        student_id=student.id,
        responses={"analysis": "Tuyên Đỉnh khắc sông Gianh và núi Hoành Sơn..."},
        citations_provided=["Đại Nam Thực Lục Chính Biên đệ nhị kỷ"],
    )

    # Assessor A scores 87
    hl.evaluate_learning_outcome_submission(
        db_session,
        submission_id=submission.id,
        assessor_id=assessor_a.id,
        rubric_scores=scores_high_agree_a,
    )
    # Assessor B scores 86
    hl.evaluate_learning_outcome_submission(
        db_session,
        submission_id=submission.id,
        assessor_id=assessor_b.id,
        rubric_scores=scores_high_agree_b,
    )

    # Trigger API calibration
    res_calib = client.post(
        "/api/v1/history/learning-outcomes/rubric-calibration",
        json={
            "submission_id": str(submission.id),
            "assessor_a_id": str(assessor_a.id),
            "assessor_b_id": str(assessor_b.id),
            "tolerance_pct": 0.15,
        },
        headers=admin_headers,
    )
    assert res_calib.status_code == 200, res_calib.text
    calib_json = res_calib.json()
    assert calib_json["status"] == "calibrated"
    assert calib_json["consensus_score"] == 86.5
    assert calib_json["inter_rater_agreement"] >= 0.95
    assert "S1_SPATIAL" in calib_json["criteria_breakdown"]


# --------------------------------------------------------------------------- #
# Test 5: Student Data Retention Audit & Purging Policy
# --------------------------------------------------------------------------- #
def test_student_data_retention_audit_and_purging_policy(client, db_session):
    """Verify retention audit, expired record identification, and PII purging (Decree 13/2023/ND-CP)."""
    admin = _make_user(db_session, f"admin_retention_{uuid.uuid4().hex[:6]}@school.vn", "Admin Retention", UserRole.admin)
    student = _make_user(db_session, f"student_ret_{uuid.uuid4().hex[:6]}@school.vn", "Em Thảo", UserRole.learner)
    assessor = _make_user(db_session, f"assessor_ret_{uuid.uuid4().hex[:6]}@school.vn", "Thầy Hoàng", UserRole.teacher)
    admin_headers = _auth_headers_for(admin)

    # Create protocol with 90 days retention window
    protocol = hl.create_ethics_protocol(
        db_session,
        {
            "protocol_code": f"RET-90D-{uuid.uuid4().hex[:6]}",
            "title": "Nghiên cứu Giới hạn Thời gian Lưu trữ",
            "irb_institution": "UBND Tỉnh Thừa Thiên Huế",
            "status": "approved",
            "data_retention_days": 90,
            "participant_consent_required": False,
        },
    )
    assessment = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": protocol.id,
            "title": "Bài tập Thử nghiệm Lưu trữ",
            "slug": f"ret-assess-{uuid.uuid4().hex[:6]}",
            "prompt_markdown": "Phân tích niên hiệu Minh Mạng trên Cửu Đỉnh.",
        },
    )
    sub = hl.submit_learning_outcome_assessment(
        db_session,
        assessment_id=assessment.id,
        student_id=student.id,
        responses={"sensitive_essay": "Bài làm chứa thông tin chi tiết và quan điểm cá nhân học sinh..."},
        citations_provided=["Châu bản Triều Nguyễn tập 45"],
    )
    eval_record = hl.evaluate_learning_outcome_submission(
        db_session,
        submission_id=sub.id,
        assessor_id=assessor.id,
        rubric_scores={"S1_SPATIAL": 20.0, "S2_TEMPORAL": 20.0, "S3_EVIDENCE": 20.0, "S4_ARGUMENT": 20.0},
        feedback_markdown="Lời nhận xét riêng tư gửi học sinh",
    )
    survey = hl.submit_subjective_survey(
        db_session,
        student_id=student.id,
        survey_name="Khảo sát Cuối kỳ 2025",
        likert_responses={"enjoyment": 5, "clarity": 4},
        feedback_text="Em cảm thấy rất hứng thú với mô hình 3D",
    )

    # Manually backdate submission, evaluation, and survey past the 90-day retention window
    expired_date = datetime.now(timezone.utc) - timedelta(days=95)
    sub.submitted_at = expired_date
    survey.submitted_at = expired_date
    db_session.commit()

    # 1. Audit identifies the expired records
    res_audit = client.post(
        f"/api/v1/history/learning-outcomes/retention/audit?ethics_protocol_id={protocol.id}",
        headers=admin_headers,
    )
    assert res_audit.status_code == 200, res_audit.text
    audit_data = res_audit.json()
    assert audit_data["retention_days_limit"] == 90
    assert audit_data["expired_submissions_count"] >= 1
    assert audit_data["expired_surveys_count"] >= 1
    assert str(sub.id) in [str(x) for x in audit_data["expired_submission_ids"]]

    # 2. Execute purge
    res_purge = client.post(
        "/api/v1/history/learning-outcomes/retention/purge",
        json={
            "ethics_protocol_id": str(protocol.id),
            "confirm_purge": True,
        },
        headers=admin_headers,
    )
    assert res_purge.status_code == 200, res_purge.text
    purge_data = res_purge.json()
    assert purge_data["status"] == "purged"
    assert purge_data["purged_submissions_count"] >= 1
    assert purge_data["purged_evaluations_count"] >= 1
    assert purge_data["purged_surveys_count"] >= 1

    # 3. Verify in database that PII and responses are scrubbed
    db_session.refresh(sub)
    db_session.refresh(eval_record)
    db_session.refresh(survey)

    assert sub.status == "retention_purged"
    assert sub.responses.get("_purged") is True
    assert sub.citations_provided == []
    assert eval_record.feedback_markdown == "[RETENTION_PURGED]"
    assert survey.feedback_text == "[RETENTION_PURGED]"
    assert survey.likert_responses == {}


# --------------------------------------------------------------------------- #
# Test 6: Negative Abuse: Sentiment Survey Cannot Claim Learning Improvement
# --------------------------------------------------------------------------- #
def test_negative_abuse_sentiment_survey_cannot_claim_learning_improvement(client, db_session):
    """Negative Abuse Invariant (P2 / Critical):
    
    Results based solely on subjective sentiment or feelings surveys (including the 1,502 survey)
    CANNOT be labeled or reported as evidence of learning improvement.
    """
    admin = _make_user(db_session, f"admin_claim_{uuid.uuid4().hex[:6]}@school.vn", "Admin Claim", UserRole.admin)
    headers = _auth_headers_for(admin)

    # 1. Pure domain function raises error
    with pytest.raises(SubjectiveSurveyCannotProduceCausalMetricsError) as exc_info:
        verify_learning_improvement_claim_basis(
            claim_type="learning_improvement",
            evidence_basis="subjective_survey",
        )
    assert "cannot be labeled as evidence of learning improvement" in str(exc_info.value)

    with pytest.raises(SubjectiveSurveyCannotProduceCausalMetricsError):
        verify_learning_improvement_claim_basis(
            claim_type="causal_mastery",
            evidence_basis="sentiment_analysis",
        )

    with pytest.raises(SubjectiveSurveyCannotProduceCausalMetricsError):
        verify_learning_improvement_claim_basis(
            claim_type="evidence_of_learning",
            evidence_basis="likert_scale",
        )

    # 2. Allowed domain claim: subjective satisfaction labeled as satisfaction
    verify_learning_improvement_claim_basis(
        claim_type="subjective_satisfaction",
        evidence_basis="subjective_survey",
    )  # Does not raise!

    # 3. API endpoint blocks fraudulent learning improvement claim based on sentiment (HTTP 422)
    res_fake_claim = client.post(
        "/api/v1/history/learning-outcomes/validate-learning-claim",
        json={
            "claim_title": "Ứng dụng giúp cải thiện 40% kết quả học tập",
            "claim_type": "learning_improvement",
            "evidence_basis": "subjective_survey",
        },
        headers=headers,
    )
    assert res_fake_claim.status_code == 422, res_fake_claim.text
    assert "CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY" in res_fake_claim.text
    assert "cannot be labeled as evidence of learning improvement" in res_fake_claim.text

    # Another negative attempt with sentiment analysis basis
    res_fake_claim_sentiment = client.post(
        "/api/v1/history/learning-outcomes/validate-learning-claim",
        json={
            "claim_title": "Tăng trưởng năng lực học sinh qua phân tích cảm xúc",
            "claim_type": "causal_mastery",
            "evidence_basis": "sentiment_analysis",
        },
        headers=headers,
    )
    assert res_fake_claim_sentiment.status_code == 422

    # 4. Legitimate claim based on objective pre/post rubric assessments is ACCEPTED (HTTP 200)
    res_legit_claim = client.post(
        "/api/v1/history/learning-outcomes/validate-learning-claim",
        json={
            "claim_title": "Mức tăng trưởng chuẩn hóa g=0.48 trên năng lực chứng cứ S3",
            "claim_type": "learning_improvement",
            "evidence_basis": "pre_post_inquiry_rubric",
        },
        headers=headers,
    )
    assert res_legit_claim.status_code == 200
    legit_data = res_legit_claim.json()
    assert legit_data["is_valid_evidence_of_learning"] is True
    assert legit_data["rejection_reason"] is None
