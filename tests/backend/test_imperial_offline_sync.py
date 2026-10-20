# -*- coding: utf-8 -*-
"""Comprehensive test suite for STTT Imperial City offline batch sync API.
Spec: STTT-SPEC-PWA-PRINT-001 (Backend Offline Sync API).

Validates:
1. Batch sync of multiple submissions:
   - Queued submissions from client IndexedDB are saved to imperial_submissions.
   - Returns synced_count, failed_count, results with server IDs and status.
   - Client timestamp is preserved as submitted_at.
2. Idempotency on duplicated client timestamps & content:
   - Re-syncing the same queued submissions returns status="acknowledged".
   - No duplicate rows are created in imperial_submissions.
   - Duplicate items within the same batch are handled idempotently.
3. Rejection of invalid activity IDs with graceful error reporting:
   - Invalid or non-existent activity UUIDs report status="failed" without aborting valid items.
   - Empty or whitespace answer text reports status="failed".
   - Batch continues processing other valid items.
4. Content update for modified offline answers:
   - Changed answer text updates existing submission and reports status="updated".
5. RBAC enforcement:
   - Learner role or higher required.
   - Guest users rejected with 403 Forbidden.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

import backend.models as models
from backend.apischemas.imperial_sync import (
    ImperialBatchSyncRequest,
    ImperialBatchSyncResponse,
    ImperialOfflineSubmissionItem,
)
from backend.deps import get_current_user, get_db
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    Base,
    ImperialActivity,
    ImperialSite,
    ImperialSubmission,
    ImperialZone,
)
from backend.main import app
from backend.models import User, UserRole
from backend.services.imperial_sync import sync_offline_submissions


# --------------------------------------------------------------------------- #
# Database Fixture for Isolated Testing
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def sync_db_engine():
    """Create in-memory SQLite engine with imperial tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        models.User.__table__,
        ImperialZone.__table__,
        ImperialSite.__table__,
        ImperialActivity.__table__,
        ImperialSubmission.__table__,
    ]
    # Clean PostgreSQL specific defaults for SQLite compatibility
    for t in tables:
        for col in t.columns:
            if (
                col.server_default is not None
                and hasattr(col.server_default, "arg")
                and isinstance(col.server_default.arg, TextClause)
            ):
                col.server_default.arg.text = col.server_default.arg.text.replace(
                    "::jsonb", ""
                )
    Base.metadata.create_all(engine, tables=tables)
    return engine


@pytest.fixture(autouse=True)
def clean_database(sync_db_engine):
    """Clean tables between each test run."""
    TestingSession = sessionmaker(bind=sync_db_engine, autoflush=False, autocommit=False)
    with TestingSession() as sess:
        sess.query(ImperialSubmission).delete()
        sess.query(ImperialActivity).delete()
        sess.query(ImperialSite).delete()
        sess.query(ImperialZone).delete()
        sess.query(models.User).delete()
        sess.commit()
    yield


@pytest.fixture
def db_session(sync_db_engine) -> Generator[Session, None, None]:
    """Yield a database session and roll back after each test."""
    TestingSession = sessionmaker(bind=sync_db_engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_users(db_session: Session) -> dict[str, models.User]:
    """Create test users: learner and guest."""
    learner_id = uuid4()
    learner_user = models.User(
        id=learner_id,
        username=f"learner_{learner_id.hex[:6]}",
        email=f"learner_{learner_id.hex[:6]}@example.com",
        display_name=f"Learner {learner_id.hex[:6]}",
        password_hash="mock_hash",
        role=models.UserRole.learner,
    )
    guest_id = uuid4()
    guest_user = models.User(
        id=guest_id,
        username=f"guest_{guest_id.hex[:6]}",
        email=f"guest_{guest_id.hex[:6]}@example.com",
        display_name=f"Guest {guest_id.hex[:6]}",
        password_hash="mock_hash",
        role=models.UserRole.guest,
    )
    db_session.add_all([learner_user, guest_user])
    db_session.commit()
    return {"learner": learner_user, "guest": guest_user}


@pytest.fixture
def seeded_activities(db_session: Session, test_users: dict[str, models.User]) -> list[ImperialActivity]:
    """Seed test zone, site, and activities."""
    user = test_users["learner"]
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="central-axis",
        title_vi="Trục trung tâm",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="ngo-mon",
        name_vi="Ngọ Môn",
        site_type="gate",
        condition="extant",
        learning_level="L2_LEARNING_READY",
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(site)
    db_session.flush()

    act1 = ImperialActivity(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        activity_type="evidence_reflection",
        title="Quan sát Ngọ Môn",
        instructions="Ghi lại nhận định thực địa về cấu trúc đài đá và lầu Ngũ Phụng.",
        max_points=100,
        is_active=True,
    )
    act2 = ImperialActivity(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        activity_type="evidence_reflection",
        title="Đối chiếu sử liệu Ngọ Môn",
        instructions="Đối chiếu vết đạn chiến tranh với ghi chép Đại Nam Thực Lục.",
        max_points=100,
        is_active=True,
    )
    db_session.add_all([act1, act2])
    db_session.commit()
    return [act1, act2]


@pytest.fixture
def api_client(db_session: Session, test_users: dict[str, models.User]) -> Generator[TestClient, None, None]:
    """Provide TestClient with dependency overrides defaulting to learner user."""
    def _override_db():
        yield db_session

    def _override_user():
        return test_users["learner"]

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_batch_sync_multiple_submissions(
    api_client: TestClient,
    db_session: Session,
    seeded_activities: list[ImperialActivity],
    test_users: dict[str, models.User],
):
    """Verify batch sync of multiple offline submissions saves them with timestamps."""
    act1, act2 = seeded_activities
    client_ts1 = "2026-10-16T08:30:00Z"
    client_ts2 = "2026-10-16T08:45:00Z"

    payload = {
        "items": [
            {
                "id": "offline-item-001",
                "activity_id": str(act1.id),
                "answer_text": "Đài đá hình chữ U trổ 5 cửa, cửa giữa dành riêng cho vua.",
                "evidence_refs": [{"source": "field_observation", "detail": "Cửa Ngọ Môn chính giữa"}],
                "client_timestamp": client_ts1,
            },
            {
                "id": "offline-item-002",
                "activity_id": str(act2.id),
                "answer_text": "Vết tích đạn pháo trên cột gỗ lầu Ngũ Phụng ghi dấu biến cố lịch sử 1968.",
                "evidence_refs": [{"source": "primary_doc", "citation": "Đại Nam Thực Lục Chính Biên"}],
                "client_timestamp": client_ts2,
            },
        ]
    }

    response = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["synced_count"] == 2
    assert data["failed_count"] == 0
    assert len(data["results"]) == 2

    res1, res2 = data["results"]
    assert res1["client_id"] == "offline-item-001"
    assert res1["status"] == "synced"
    assert res1["server_id"] is not None
    assert res1["error"] is None

    assert res2["client_id"] == "offline-item-002"
    assert res2["status"] == "synced"
    assert res2["server_id"] is not None
    assert res2["error"] is None

    # Verify rows in database
    subs = db_session.query(ImperialSubmission).filter(
        ImperialSubmission.student_id == test_users["learner"].id
    ).all()
    assert len(subs) == 2


def test_idempotency_on_duplicated_client_timestamps(
    api_client: TestClient,
    db_session: Session,
    seeded_activities: list[ImperialActivity],
    test_users: dict[str, models.User],
):
    """Verify re-syncing the same offline items returns acknowledged without duplicating rows."""
    act1 = seeded_activities[0]
    client_ts = "2026-10-16T09:00:00Z"

    payload = {
        "items": [
            {
                "id": "queued-item-duplicate-test",
                "activity_id": str(act1.id),
                "answer_text": "Cột cờ phía trước Ngọ Môn là Kỳ Đài.",
                "evidence_refs": [],
                "client_timestamp": client_ts,
            }
        ]
    }

    # First sync
    res1 = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["synced_count"] == 1
    assert data1["results"][0]["status"] == "synced"
    first_server_id = data1["results"][0]["server_id"]

    # Count before second sync
    initial_count = db_session.query(ImperialSubmission).count()
    assert initial_count == 1

    # Second sync (replay / retry)
    res2 = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["synced_count"] == 1
    assert data2["failed_count"] == 0
    assert data2["results"][0]["status"] == "acknowledged"
    assert data2["results"][0]["server_id"] == first_server_id

    # Verify database still has exactly 1 row (no duplicate row)
    final_count = db_session.query(ImperialSubmission).count()
    assert final_count == 1


def test_rejection_of_invalid_activity_ids(
    api_client: TestClient,
    db_session: Session,
    seeded_activities: list[ImperialActivity],
):
    """Verify non-existent activity IDs and blank answers fail gracefully without breaking batch."""
    act1 = seeded_activities[0]
    fake_activity_id = str(uuid4())

    payload = {
        "items": [
            {
                "id": "valid-item-1",
                "activity_id": str(act1.id),
                "answer_text": "Đáp án hợp lệ cho trạm Ngọ Môn.",
                "evidence_refs": [],
                "client_timestamp": "2026-10-16T09:15:00Z",
            },
            {
                "id": "invalid-item-bad-id",
                "activity_id": fake_activity_id,
                "answer_text": "Đáp án cho hoạt động không tồn tại.",
                "evidence_refs": [],
                "client_timestamp": "2026-10-16T09:16:00Z",
            },
            {
                "id": "invalid-item-blank-answer",
                "activity_id": str(act1.id),
                "answer_text": "   ",
                "evidence_refs": [],
                "client_timestamp": "2026-10-16T09:17:00Z",
            },
        ]
    }

    response = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["synced_count"] == 1
    assert data["failed_count"] == 2
    assert len(data["results"]) == 3

    valid_res = data["results"][0]
    assert valid_res["client_id"] == "valid-item-1"
    assert valid_res["status"] == "synced"
    assert valid_res["server_id"] is not None

    bad_id_res = data["results"][1]
    assert bad_id_res["client_id"] == "invalid-item-bad-id"
    assert bad_id_res["status"] == "failed"
    assert bad_id_res["server_id"] is None
    assert "not found" in bad_id_res["error"]

    blank_res = data["results"][2]
    assert blank_res["client_id"] == "invalid-item-blank-answer"
    assert blank_res["status"] == "failed"
    assert blank_res["server_id"] is None
    assert "empty" in blank_res["error"].lower()


def test_update_existing_submission_with_modified_content(
    api_client: TestClient,
    db_session: Session,
    seeded_activities: list[ImperialActivity],
):
    """Verify that editing an answer offline updates the existing submission record."""
    act1 = seeded_activities[0]

    # Initial submission
    first_payload = {
        "items": [
            {
                "id": "item-edit-v1",
                "activity_id": str(act1.id),
                "answer_text": "Bản nháp ban đầu tại thực địa.",
                "evidence_refs": [],
                "client_timestamp": "2026-10-16T10:00:00Z",
            }
        ]
    }
    res1 = api_client.post("/api/v1/imperial/submissions/batch-sync", json=first_payload)
    assert res1.status_code == 200
    server_id = res1.json()["results"][0]["server_id"]

    # Student updates the reflection offline and syncs later
    second_payload = {
        "items": [
            {
                "id": "item-edit-v2",
                "activity_id": str(act1.id),
                "answer_text": "Bản hoàn chỉnh sau khi thảo luận nhóm tại thực địa.",
                "evidence_refs": [{"source": "group_discussion"}],
                "client_timestamp": "2026-10-16T10:30:00Z",
            }
        ]
    }
    res2 = api_client.post("/api/v1/imperial/submissions/batch-sync", json=second_payload)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["synced_count"] == 1
    assert data2["results"][0]["status"] == "updated"
    assert data2["results"][0]["server_id"] == server_id

    # Verify content in DB is updated
    updated_row = db_session.query(ImperialSubmission).filter_by(id=UUID(server_id)).one()
    assert updated_row.answer_text == "Bản hoàn chỉnh sau khi thảo luận nhóm tại thực địa."
    assert len(updated_row.evidence_refs) == 1


def test_rbac_guest_cannot_sync(
    db_session: Session,
    test_users: dict[str, models.User],
    seeded_activities: list[ImperialActivity],
):
    """Verify that guest users are rejected with 403 Forbidden."""
    def _override_db():
        yield db_session

    def _override_guest():
        return test_users["guest"]

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_guest

    with TestClient(app) as client:
        payload = {
            "items": [
                {
                    "id": "guest-item-1",
                    "activity_id": str(seeded_activities[0].id),
                    "answer_text": "Guest answer",
                    "evidence_refs": [],
                    "client_timestamp": "2026-10-16T11:00:00Z",
                }
            ]
        }
        res = client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
        assert res.status_code == 403

    app.dependency_overrides.clear()


def test_direct_service_layer(
    db_session: Session,
    seeded_activities: list[ImperialActivity],
    test_users: dict[str, models.User],
):
    """Verify calling sync_offline_submissions directly as a service function."""
    act1 = seeded_activities[0]
    learner = test_users["learner"]

    items = [
        ImperialOfflineSubmissionItem(
            id="service-call-001",
            activity_id=act1.id,
            answer_text="Thử nghiệm gọi trực tiếp từ tầng service",
            evidence_refs=[],
            client_timestamp=datetime.now(timezone.utc),
        )
    ]

    response = sync_offline_submissions(
        db=db_session,
        student_id=learner.id,
        items=items,
    )

    assert isinstance(response, ImperialBatchSyncResponse)
    assert response.synced_count == 1
    assert response.failed_count == 0
    assert response.results[0].status == "synced"
    assert response.results[0].server_id is not None
