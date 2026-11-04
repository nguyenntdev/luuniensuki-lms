# -*- coding: utf-8 -*-
"""V5-T056 (Wave W05, Slot A06): Offline Queue Idempotency Test Suite.

Audits and verifies:
1. Queued offline actions tracking across:
   - Inspections: 3D/AR or 2D turntable relic inspections
   - Submissions: Imperial inquiry activities and classroom assignments
   - Progression: Relic discovery, lesson completion, quiz evaluation
2. Server ACK and client idempotency keys:
   - Server returns authoritative ACK (synced, acknowledged, updated, conflict, failed)
   - Echoes idempotency keys and server UUIDs
3. Conflict resolution:
   - Identical submission content -> acknowledged without duplicating rows
   - Modified student draft before grading -> updated with incremented row_version
   - Modified student draft AFTER teacher grading -> conflict resolution strictly
     preserves teacher score, feedback, and status
4. Negative abuse & anti-replay gamification:
   - Reconnection retries do NOT duplicate database submissions
   - Reconnection retries do NOT award multiple XP (XP awarded exactly once)
   - Malicious burst retries receive 0 duplicate XP
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialActivity,
    ImperialSite,
    ImperialSubmission,
    ImperialZone,
)
from backend.imperial_v51_models import ImperialArtDetail
from backend.models import (
    Motif,
    MotifCategory,
    QuestionType,
    QuizAttempt,
    QuizQuestion,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
    UserRole,
)
from backend.security import hash_password
from backend.services.offline_sync_service import clear_offline_idempotency_cache
from backend.services.progress_service import clear_idempotency_cache


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear memory idempotency stores before each test."""
    clear_offline_idempotency_cache()
    clear_idempotency_cache()
    yield
    clear_offline_idempotency_cache()
    clear_idempotency_cache()


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Helper to persist a test user."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        total_xp=0,
        current_streak=0,
        longest_streak=0,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers_for(user: User) -> dict[str, str]:
    from datetime import timedelta
    from backend.config import settings
    from backend.security import create_jwt_token

    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={
            "type": "access",
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        },
    )
    return {"Authorization": f"Bearer {token}"}


def _seed_urn_and_motif(
    db_session,
    name: str = "Thần Sấm (Lôi)",
    mesh_name: str = "relief_loi_t056",
    is_demo: bool = False,
) -> tuple[Urn, Motif]:
    urn = Urn(
        slug=f"urn-{uuid.uuid4().hex[:6]}",
        name=f"Cao Đỉnh {uuid.uuid4().hex[:4]}",
        model_url="https://example.com/urn.glb",
        display_order=1,
        is_demo=is_demo,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        name=name,
        name_en="Thunder God",
        mesh_name=f"{mesh_name}_{uuid.uuid4().hex[:6]}",
        urn_id=urn.id,
        category=MotifCategory.thien_van,
        pos_x=0.0,
        pos_y=1.0,
        pos_z=0.0,
        bounding_radius=1.0,
        is_active=True,
        is_demo=is_demo,
    )
    db_session.add(motif)
    db_session.flush()

    # Add 1 quiz question to support quiz submissions
    q = QuizQuestion(
        motif_id=motif.id,
        question_text="Ý nghĩa biểu tượng của Thần Sấm?",
        question_type=QuestionType.multiple_choice,
        options=["Sức mạnh thiên nhiên", "Mùa màng", "Sông núi", "Đất đai"],
        correct_answer="Sức mạnh thiên nhiên",
        difficulty=1,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(motif)
    return urn, motif


def _seed_imperial_activity(db_session, creator: User) -> tuple[ImperialSite, ImperialActivity]:
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug=f"zone-t056-{uuid4().hex[:8]}",
        title_vi="Khu vực Hoàng Thành",
        title_en="Imperial Citadel",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug=f"ngo-mon-{uuid4().hex[:8]}",
        name_vi="Ngọ Môn Huế",
        name_en="Meridian Gate",
        site_type="gate",
        condition="extant",
        learning_level="L2_VERIFIED",
        summary_vi="Cổng chính phía nam của Hoàng thành Huế.",
        historical_context="Xây dựng năm 1833 dưới thời vua Minh Mạng.",
        architectural_features="Cấu trúc năm cửa chín lầu.",
        construction_year=1833,
        is_published=True,
        display_order=1,
        created_by=creator.id,
    )
    db_session.add(site)
    db_session.flush()

    activity = ImperialActivity(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        activity_type="inquiry",
        title="Khảo sát năm cửa Ngọ Môn",
        instructions="Phân tích trật tự phân tầng không gian và chính sử triều Nguyễn.",
        max_points=12,
        is_active=True,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return site, activity


def _seed_art_detail(db_session, site: ImperialSite, slug: str = "ngai-vang-t056") -> ImperialArtDetail:
    detail = ImperialArtDetail(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        title="Ngai Vàng Triều Nguyễn",
        slug=slug,
        kind="carving",
        motif="Cửu Long tranh châu",
        material="Gỗ quý dát vàng",
        technique="Chạm lộng sơn thếp",
        description_observation="Ngai vàng đặt uy nghiêm trên bệ tam cấp.",
        story_body="Ngai vàng chế tác từ thời Gia Long.",
        story_type="documented_event",
        review_status="published",
        row_version=1,
    )
    db_session.add(detail)
    db_session.commit()
    db_session.refresh(detail)
    return detail


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_offline_relic_inspection_sync_and_idempotency(client, db_session):
    """Verifies queued relic inspection idempotency, server ACK, and zero duplicate XP on retry."""
    user = _create_user(db_session, f"student_insp_{uuid4().hex[:6]}@example.com")
    admin = _create_user(db_session, f"admin_insp_{uuid4().hex[:6]}@example.com", UserRole.admin)
    site, _ = _seed_imperial_activity(db_session, admin)
    _seed_art_detail(db_session, site, slug="ngai-vang-t056")

    headers = _auth_headers_for(user)
    idemp_key = f"idemp_insp_{uuid4().hex[:8]}"

    op_payload = {
        "operation_id": f"op_{uuid4().hex[:8]}",
        "resource": "inspection",
        "payload": {
            "target_slug": "ngai-vang-t056",
            "inspection_mode": "webxr_ar",
            "camera_permission_granted": True,
            "device_tier": "mobile_high",
            "time_spent_seconds": 30,
            "angles_inspected": ["front", "top", "iso"],
            "hotspots_examined": ["dragon_carving"],
        },
        "idempotency_key": idemp_key,
    }

    # 1. First sync attempt (online reconnection)
    res1 = client.post("/api/v1/offline/sync", json=op_payload, headers=headers)
    assert res1.status_code == 200, res1.text
    data1 = res1.json()

    assert data1["success"] is True
    assert data1["status"] == "synced"
    assert data1["xp_awarded"] == 25
    assert data1["total_xp_awarded"] == 25
    assert data1["synced_count"] == 1
    assert data1["acknowledged_count"] == 0
    assert data1["server_ack"]["task_id"] is not None

    # Check user XP in DB
    db_session.refresh(user)
    assert user.total_xp == 25

    # 2. Reconnection retry with the identical idempotency key
    res2 = client.post("/api/v1/offline/sync", json=op_payload, headers=headers)
    assert res2.status_code == 200, res2.text
    data2 = res2.json()

    assert data2["success"] is True
    assert data2["status"] == "acknowledged"
    assert data2["xp_awarded"] == 0  # Replay awards ZERO XP!
    assert data2["total_xp_awarded"] == 0
    assert data2["acknowledged_count"] == 1

    # Verify user total_xp did NOT double
    db_session.refresh(user)
    assert user.total_xp == 25


def test_offline_progression_sync_and_anti_replay_xp(client, db_session):
    """Verifies queued offline progression (discover, lesson, quiz) with anti-replay XP caps."""
    user = _create_user(db_session, f"student_prog_{uuid4().hex[:6]}@example.com")
    _, motif = _seed_urn_and_motif(db_session)
    headers = _auth_headers_for(user)

    # 1. Queued Discovery Action
    disc_key = f"idemp_disc_{uuid4().hex[:8]}"
    disc_op = {
        "operation_id": f"op_disc_{uuid4().hex[:8]}",
        "resource": "progression",
        "payload": {
            "action": "discover",
            "motif_id": str(motif.id),
            "time_spent_seconds": 12,
        },
        "idempotency_key": disc_key,
    }

    res_disc1 = client.post("/api/v1/offline/sync", json=disc_op, headers=headers)
    assert res_disc1.status_code == 200, res_disc1.text
    d1 = res_disc1.json()
    assert d1["status"] == "synced"
    assert d1["xp_awarded"] == 25

    # Discovery Retry (reconnection)
    res_disc2 = client.post("/api/v1/offline/sync", json=disc_op, headers=headers)
    assert res_disc2.status_code == 200
    d2 = res_disc2.json()
    assert d2["status"] == "acknowledged"
    assert d2["xp_awarded"] == 0

    # 2. Queued Lesson Completion Action
    lesson_key = f"idemp_lesson_{uuid4().hex[:8]}"
    lesson_op = {
        "operation_id": f"op_lesson_{uuid4().hex[:8]}",
        "resource": "progression",
        "payload": {
            "action": "complete_lesson",
            "motif_id": str(motif.id),
            "time_spent_seconds": 45,
        },
        "idempotency_key": lesson_key,
    }

    res_les1 = client.post("/api/v1/offline/sync", json=lesson_op, headers=headers)
    assert res_les1.status_code == 200
    l1 = res_les1.json()
    assert l1["status"] == "synced"
    assert l1["xp_awarded"] == 50

    # Lesson Retry (reconnection)
    res_les2 = client.post("/api/v1/offline/sync", json=lesson_op, headers=headers)
    assert res_les2.status_code == 200
    l2 = res_les2.json()
    assert l2["status"] == "acknowledged"
    assert l2["xp_awarded"] == 0

    # 3. Queued Quiz Submit Action (Passing >= 80%)
    quiz_question = db_session.execute(
        select(QuizQuestion).where(QuizQuestion.motif_id == motif.id)
    ).scalars().first()

    quiz_key = f"idemp_quiz_{uuid4().hex[:8]}"
    quiz_op = {
        "operation_id": f"op_quiz_{uuid4().hex[:8]}",
        "resource": "progression",
        "payload": {
            "action": "submit_quiz",
            "motif_id": str(motif.id),
            "time_spent_seconds": 60,
            "answers": {str(quiz_question.id): "Sức mạnh thiên nhiên"},
        },
        "idempotency_key": quiz_key,
    }

    res_q1 = client.post("/api/v1/offline/sync", json=quiz_op, headers=headers)
    assert res_q1.status_code == 200
    q1 = res_q1.json()
    assert q1["status"] == "synced"
    assert q1["xp_awarded"] == 75
    assert q1["server_ack"]["quiz_passed"] is True

    # Quiz Retry after motif mastered
    res_q2 = client.post("/api/v1/offline/sync", json=quiz_op, headers=headers)
    assert res_q2.status_code == 200
    q2 = res_q2.json()
    assert q2["status"] == "acknowledged"
    assert q2["xp_awarded"] == 0

    # Total cumulative XP must equal 25 + 50 + 75 = 150
    db_session.refresh(user)
    assert user.total_xp == 150


def test_offline_submission_sync_identical_and_updated_draft(client, db_session):
    """Verifies queued submission idempotency: identical answer acknowledges, updated answer updates row."""
    user = _create_user(db_session, f"student_sub_{uuid4().hex[:6]}@example.com")
    admin = _create_user(db_session, f"admin_sub_{uuid4().hex[:6]}@example.com", UserRole.admin)
    _, activity = _seed_imperial_activity(db_session, admin)
    headers = _auth_headers_for(user)

    sub_key = f"idemp_sub_{uuid4().hex[:8]}"
    base_sub_op = {
        "operation_id": f"op_sub_{uuid4().hex[:8]}",
        "resource": "submission",
        "payload": {
            "activity_id": str(activity.id),
            "answer_text": "Khảo sát Ngọ Môn: Cửa giữa dành cho vua, hai bên dành cho quan lại.",
            "evidence_refs": ["Khâm Định Đại Nam Hội Điển Sự Lệ"],
        },
        "idempotency_key": sub_key,
    }

    # 1. Fresh offline submission sync
    res1 = client.post("/api/v1/offline/sync", json=base_sub_op, headers=headers)
    assert res1.status_code == 200, res1.text
    d1 = res1.json()
    assert d1["status"] == "synced"
    server_id = d1["server_ack"]["server_id"]
    assert server_id is not None

    # Check 1 database row created
    subs = db_session.execute(
        select(ImperialSubmission).where(
            ImperialSubmission.activity_id == activity.id,
            ImperialSubmission.student_id == user.id,
        )
    ).scalars().all()
    assert len(subs) == 1
    assert subs[0].row_version == 1

    # 2. Reconnection retry with IDENTICAL content
    res2 = client.post("/api/v1/offline/sync", json=base_sub_op, headers=headers)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "acknowledged"
    assert d2["server_ack"]["server_id"] == server_id

    # Count remains exactly 1!
    subs2 = db_session.execute(
        select(ImperialSubmission).where(
            ImperialSubmission.activity_id == activity.id,
            ImperialSubmission.student_id == user.id,
        )
    ).scalars().all()
    assert len(subs2) == 1
    assert subs2[0].row_version == 1

    # 3. Student modified draft offline before teacher grading
    updated_op = {
        "operation_id": f"op_sub_edit_{uuid4().hex[:8]}",
        "resource": "submission",
        "payload": {
            "activity_id": str(activity.id),
            "answer_text": "Bổ sung khảo sát Ngọ Môn: Lầu Ngũ Phụng có 100 cột lim.",
            "evidence_refs": ["Ảnh tư liệu EFEO 1920"],
        },
        "idempotency_key": f"idemp_sub_edit_{uuid4().hex[:8]}",
    }
    res3 = client.post("/api/v1/offline/sync", json=updated_op, headers=headers)
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["status"] == "updated"

    # Database submission updated with row_version incremented
    db_session.expire_all()
    updated_sub = db_session.execute(
        select(ImperialSubmission).where(
            ImperialSubmission.activity_id == activity.id,
            ImperialSubmission.student_id == user.id,
        )
    ).scalars().one()
    assert updated_sub.row_version == 2
    assert "Lầu Ngũ Phụng" in updated_sub.answer_text


def test_offline_submission_conflict_resolution_preserves_graded_assessment(client, db_session):
    """Verifies that an offline edit cannot overwrite a teacher's graded assessment (Conflict Resolution)."""
    user = _create_user(db_session, f"student_conf_{uuid4().hex[:6]}@example.com")
    teacher = _create_user(db_session, f"teacher_conf_{uuid4().hex[:6]}@example.com", UserRole.teacher)
    admin = _create_user(db_session, f"admin_conf_{uuid4().hex[:6]}@example.com", UserRole.admin)
    _, activity = _seed_imperial_activity(db_session, admin)
    headers = _auth_headers_for(user)

    # 1. Student submits initial answer offline
    initial_op = {
        "operation_id": f"op_initial_{uuid4().hex[:8]}",
        "resource": "submission",
        "payload": {
            "activity_id": str(activity.id),
            "answer_text": "Bản làm bài đầu tiên.",
            "evidence_refs": [],
        },
        "idempotency_key": f"idemp_initial_{uuid4().hex[:8]}",
    }
    res1 = client.post("/api/v1/offline/sync", json=initial_op, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "synced"

    # 2. Teacher grades the submission
    sub = db_session.execute(
        select(ImperialSubmission).where(
            ImperialSubmission.activity_id == activity.id,
            ImperialSubmission.student_id == user.id,
        )
    ).scalars().one()

    sub.status = "graded"
    sub.score = 10.0
    sub.feedback = "Bài làm rất tốt, phân tích chuẩn xác."
    sub.graded_by = teacher.id
    sub.graded_at = datetime.now(timezone.utc)
    db_session.commit()

    # 3. Student comes online and syncs a late edit
    late_op = {
        "operation_id": f"op_late_{uuid4().hex[:8]}",
        "resource": "submission",
        "payload": {
            "activity_id": str(activity.id),
            "answer_text": "Em sửa lại câu trả lời sau khi nộp.",
            "evidence_refs": ["Sách mới trích"],
        },
        "idempotency_key": f"idemp_late_{uuid4().hex[:8]}",
    }
    res2 = client.post("/api/v1/offline/sync", json=late_op, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()

    # Conflict detected and server state preserved!
    assert data2["status"] == "conflict"
    assert data2["conflict_count"] == 1
    assert "chấm điểm" in data2["results"][0]["error"] or "graded" in data2["results"][0]["error"]

    # Verify database state was NOT corrupted by the student's offline edit
    db_session.expire_all()
    sub_after = db_session.get(ImperialSubmission, sub.id)
    assert sub_after.status == "graded"
    assert sub_after.score == 10.0
    assert sub_after.feedback == "Bài làm rất tốt, phân tích chuẩn xác."
    assert sub_after.answer_text == "Bản làm bài đầu tiên."


def test_negative_abuse_rapid_reconnection_burst_and_replay(client, db_session):
    """Verifies that 10 rapid concurrent or replay re-transmissions award XP only once."""
    user = _create_user(db_session, f"student_burst_{uuid4().hex[:6]}@example.com")
    admin = _create_user(db_session, f"admin_burst_{uuid4().hex[:6]}@example.com", UserRole.admin)
    site, _ = _seed_imperial_activity(db_session, admin)
    _seed_art_detail(db_session, site, slug="ngai-vang-burst")
    headers = _auth_headers_for(user)

    idemp_key = f"burst_idemp_{uuid4().hex[:8]}"
    op = {
        "operation_id": "op_burst_1",
        "resource": "inspection",
        "payload": {
            "target_slug": "ngai-vang-burst",
            "inspection_mode": "turntable_3d",
            "time_spent_seconds": 20,
            "angles_inspected": ["front"],
        },
        "idempotency_key": idemp_key,
    }

    total_xp_recorded = 0
    # Send 10 rapid requests simulating network flakiness reconnect loop
    for i in range(10):
        res = client.post("/api/v1/offline/sync", json=op, headers=headers)
        assert res.status_code == 200
        d = res.json()
        total_xp_recorded += d["xp_awarded"]

    # Total XP awarded across all 10 calls must be EXACTLY 25, never 250!
    assert total_xp_recorded == 25
    db_session.refresh(user)
    assert user.total_xp == 25


def test_offline_batch_sync_mixed_actions(client, db_session):
    """Verifies batch synchronization with mixed actions (inspection, progression, submission)."""
    user = _create_user(db_session, f"student_batch_{uuid4().hex[:6]}@example.com")
    admin = _create_user(db_session, f"admin_batch_{uuid4().hex[:6]}@example.com", UserRole.admin)
    site, activity = _seed_imperial_activity(db_session, admin)
    _seed_art_detail(db_session, site, slug="chi-tiet-batch")
    _, motif = _seed_urn_and_motif(db_session, name="Thần Gió (Phong)")
    headers = _auth_headers_for(user)

    batch_payload = {
        "operations": [
            {
                "operation_id": f"op_b1_{uuid4().hex[:6]}",
                "resource": "inspection",
                "payload": {
                    "target_slug": "chi-tiet-batch",
                    "inspection_mode": "turntable_3d",
                    "time_spent_seconds": 15,
                    "angles_inspected": ["front", "back"],
                },
                "idempotency_key": f"key_b1_{uuid4().hex[:6]}",
            },
            {
                "operation_id": f"op_b2_{uuid4().hex[:6]}",
                "resource": "progression",
                "payload": {
                    "action": "discover",
                    "motif_id": str(motif.id),
                    "time_spent_seconds": 20,
                },
                "idempotency_key": f"key_b2_{uuid4().hex[:6]}",
            },
            {
                "operation_id": f"op_b3_{uuid4().hex[:6]}",
                "resource": "submission",
                "payload": {
                    "activity_id": str(activity.id),
                    "answer_text": "Phân tích trật tự kiến trúc Đại Nội.",
                    "evidence_refs": [],
                },
                "idempotency_key": f"key_b3_{uuid4().hex[:6]}",
            },
        ]
    }

    # 1. Batch Sync
    res1 = client.post("/api/v1/offline/batch-sync", json=batch_payload, headers=headers)
    assert res1.status_code == 200, res1.text
    data1 = res1.json()

    assert data1["success"] is True
    assert data1["synced_count"] == 3
    assert data1["acknowledged_count"] == 0
    assert data1["failed_count"] == 0
    assert data1["total_xp_awarded"] == 50  # 25 (insp) + 25 (progression discovery)

    # 2. Resend identical batch (reconnect retry)
    res2 = client.post("/api/v1/offline/batch-sync", json=batch_payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["success"] is True
    assert data2["synced_count"] == 0
    assert data2["acknowledged_count"] == 3  # All 3 acknowledged
    assert data2["total_xp_awarded"] == 0   # ZERO duplicate XP!


def test_offline_sync_error_handling(client, db_session):
    """Verifies validation errors and unauthenticated security gates."""
    user = _create_user(db_session, f"student_err_{uuid4().hex[:6]}@example.com")
    headers = _auth_headers_for(user)

    # 1. Unauthenticated request rejected with 401
    unauth_res = client.post(
        "/api/v1/offline/sync",
        json={"operation_id": "op_unauth", "resource": "inspection", "payload": {}},
    )
    assert unauth_res.status_code == 401

    # 2. Empty payload missing operations and resource
    bad_req = client.post("/api/v1/offline/sync", json={}, headers=headers)
    assert bad_req.status_code == 400

    # 3. Unsupported resource returns status 'failed' inside result without 500 crash
    bad_res = client.post(
        "/api/v1/offline/sync",
        json={
            "operation_id": "op_bad_res",
            "resource": "unsupported_hack",
            "payload": {},
        },
        headers=headers,
    )
    assert bad_res.status_code == 200
    data = bad_res.json()
    assert data["failed_count"] == 1
    assert data["results"][0]["status"] == "failed"
    assert "Unsupported offline resource" in data["results"][0]["error"]
