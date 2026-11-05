# -*- coding: utf-8 -*-
"""V5-T092: Verified Heritage Passport & QR Provenance Test Suite.

Wave W09, Slot A02 (Priority: P2, Classification: NEW_PRODUCT_FEATURE).
Verifies:
1. Server-authenticated check-in:
   - Authenticated student submits signed QR token.
   - Returns 200 with verified stamp, cryptographic provenance hash, and authority.
2. QR Code Provenance Verification:
   - Valid cryptographic HMAC-SHA256 signature verification.
   - Rejection of tampered signatures (HTTP 400, INVALID_QR_SIGNATURE).
   - Rejection of expired QR tokens (HTTP 400, QR_EXPIRED).
   - Rejection of mismatched site tokens (HTTP 400, QR_SITE_MISMATCH).
   - Rejection of unauthorized authorities (HTTP 400, UNAUTHORIZED_HERITAGE_AUTHORITY).
3. Visit Stamp DISTINCT from Assessed Mastery:
   - Check-in records physical / authorized presence in heritage_passport_stamps.
   - Check-in NEVER automatically grants curriculum mastery (UnlockStatus.mastered).
   - Assessed mastery remains strictly gated by academic assessment (quiz >= 80%).
4. Negative Abuse Defense:
   - Fabricated client claims (e.g. client_claimed_status="mastered") are strictly ignored.
   - Fake local/client completions (localStorage manipulation) are excluded from teacher analytics.
   - Only server-verified stamps are aggregated in teacher analytics.
5. Anti-Replay & Idempotent Visits:
   - Repeated check-ins increment checkin_count but award 0 duplicate XP.
6. Summary & Catalog Parity:
   - All 16 monuments in Hue Imperial City cataloged across 4 spatial zones.
   - Student passport summary exposes both verified stamps and assessed mastery counts.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import (
    ClassMember,
    Classroom,
    HeritagePassportStamp,
    Motif,
    MotifCategory,
    MotifRarity,
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
from backend.services.heritage_passport import (
    IMPERIAL_MONUMENTS_CATALOG,
    TOTAL_CATALOG_SEALS,
    generate_qr_token,
    verify_qr_token,
)


# --------------------------------------------------------------------------- #
# Helper Functions & Fixtures
# --------------------------------------------------------------------------- #


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with standard password."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"u_{uuid.uuid4().hex[:8]}",
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


def _login_user(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Helper to authenticate and return auth payload with bearer token headers."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.headers.get("X-Access-Token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# --------------------------------------------------------------------------- #
# 1. Monument Catalog & Invariant Parity Tests
# --------------------------------------------------------------------------- #


def test_all_16_monuments_catalog_validity():
    """Verify that all 16 monuments in Hue Imperial City are cataloged across 4 spatial zones."""
    assert TOTAL_CATALOG_SEALS == 16
    assert len(IMPERIAL_MONUMENTS_CATALOG) == 16

    expected_zones = {
        "central-ceremonial-axis",
        "ancestral-worship-space",
        "purple-forbidden-city",
        "royal-living-gardens",
    }
    actual_zones = {m["zone_slug"] for m in IMPERIAL_MONUMENTS_CATALOG.values()}
    assert actual_zones == expected_zones

    # Check key representative monuments
    assert "ngo-mon" in IMPERIAL_MONUMENTS_CATALOG
    assert IMPERIAL_MONUMENTS_CATALOG["ngo-mon"]["name"] == "Ngọ Môn"
    assert IMPERIAL_MONUMENTS_CATALOG["ngo-mon"]["name_han_nom"] == "午門"
    assert IMPERIAL_MONUMENTS_CATALOG["ngo-mon"]["zone_slug"] == "central-ceremonial-axis"

    assert "dien-thai-hoa" in IMPERIAL_MONUMENTS_CATALOG
    assert IMPERIAL_MONUMENTS_CATALOG["dien-thai-hoa"]["name"] == "Điện Thái Hòa"

    assert "cuu-dinh" in IMPERIAL_MONUMENTS_CATALOG
    assert IMPERIAL_MONUMENTS_CATALOG["cuu-dinh"]["name"] == "Cửu Đỉnh"
    assert IMPERIAL_MONUMENTS_CATALOG["cuu-dinh"]["zone_slug"] == "ancestral-worship-space"


# --------------------------------------------------------------------------- #
# 2. Server-Authenticated Check-in & Provenance Tests
# --------------------------------------------------------------------------- #


def test_server_authenticated_checkin_success(client: TestClient, db_session):
    """Verify server-authenticated check-in using a cryptographically signed QR token."""
    student = _create_user(db_session, "passport_stu1@test.com", UserRole.learner, "Lê Văn Hậu")
    headers = _login_user(client, student.email)

    # Generate genuine QR code token for Ngọ Môn
    qr_token = generate_qr_token(site_slug="ngo-mon", authority="HMCC_HUE_HERITAGE")

    res = client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers,
        json={
            "site_slug": "ngo-mon",
            "verification_method": "qr_code",
            "qr_token": qr_token,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["success"] is True
    assert data["site_slug"] == "ngo-mon"
    assert data["site_name"] == "Ngọ Môn"
    assert data["zone_slug"] == "central-ceremonial-axis"
    assert data["is_verified"] is True
    assert data["is_distinct_from_mastery"] is True
    assert data["xp_awarded"] == 15
    assert data["checkin_count"] == 1
    assert data["authority"] == "HMCC_HUE_HERITAGE"
    assert len(data["provenance_hash"]) == 64  # SHA-256 length

    # Verify DB record
    stamp = db_session.execute(
        select(HeritagePassportStamp).where(
            HeritagePassportStamp.user_id == student.id,
            HeritagePassportStamp.site_slug == "ngo-mon",
        )
    ).scalar_one()

    assert stamp.is_verified is True
    assert stamp.checkin_count == 1
    assert stamp.provenance_hash == data["provenance_hash"]

    # Verify user gained 15 XP
    db_session.refresh(student)
    assert student.total_xp == 15


def test_anti_replay_and_idempotent_checkin(client: TestClient, db_session):
    """Verify repeated check-in at the same site updates visit count but awards 0 duplicate XP."""
    student = _create_user(db_session, "passport_stu2@test.com", UserRole.learner, "Trần Thị Lan")
    headers = _login_user(client, student.email)

    qr_token = generate_qr_token(site_slug="the-mieu")

    # First check-in
    res1 = client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers,
        json={"site_slug": "the-mieu", "qr_token": qr_token},
    )
    assert res1.status_code == 200
    assert res1.json()["xp_awarded"] == 15
    assert res1.json()["checkin_count"] == 1

    # Second check-in at same monument
    res2 = client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers,
        json={"site_slug": "the-mieu", "qr_token": qr_token},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["xp_awarded"] == 0  # Zero repeat XP
    assert data2["checkin_count"] == 2  # Incremented visit count
    assert "ghé thăm 2 lần" in data2["message"]

    # Verify total XP remains 15 (not 30)
    db_session.refresh(student)
    assert student.total_xp == 15


# --------------------------------------------------------------------------- #
# 3. QR Code Provenance Verification & Tamper Resistance Tests
# --------------------------------------------------------------------------- #


def test_qr_code_provenance_verification_success_and_tampering(client: TestClient, db_session):
    """Verify cryptographic provenance checks for valid and tampered QR tokens."""
    student = _create_user(db_session, "passport_stu3@test.com", UserRole.learner)
    headers = _login_user(client, student.email)

    # 1. Valid token verification
    valid_token = generate_qr_token(site_slug="dien-thai-hoa", authority="HMCC_HUE_HERITAGE")
    res_valid = client.post(
        "/api/v1/progress/passport/verify-qr",
        headers=headers,
        json={"qr_token": valid_token, "site_slug": "dien-thai-hoa"},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["valid"] is True
    assert res_valid.json()["site_slug"] == "dien-thai-hoa"

    # 2. Tampered signature
    payload_b64, sig = valid_token.split(".")
    tampered_sig = ("0" if sig[0] != "0" else "1") + sig[1:]
    tampered_token = f"{payload_b64}.{tampered_sig}"

    res_tampered = client.post(
        "/api/v1/progress/passport/verify-qr",
        headers=headers,
        json={"qr_token": tampered_token, "site_slug": "dien-thai-hoa"},
    )
    assert res_tampered.status_code == 400
    assert res_tampered.json()["error"]["code"] == "INVALID_QR_SIGNATURE"

    # 3. Expired token
    expired_token = generate_qr_token(site_slug="dien-thai-hoa", expires_in_seconds=-100)
    res_expired = client.post(
        "/api/v1/progress/passport/verify-qr",
        headers=headers,
        json={"qr_token": expired_token, "site_slug": "dien-thai-hoa"},
    )
    assert res_expired.status_code == 400
    assert res_expired.json()["error"]["code"] == "QR_EXPIRED"

    # 4. Site mismatch (token issued for dien-thai-hoa submitted for the-mieu)
    res_mismatch = client.post(
        "/api/v1/progress/passport/verify-qr",
        headers=headers,
        json={"qr_token": valid_token, "site_slug": "the-mieu"},
    )
    assert res_mismatch.status_code == 400
    assert res_mismatch.json()["error"]["code"] == "QR_SITE_MISMATCH"


def test_qr_unauthorized_authority_rejected(client: TestClient, db_session):
    """Verify QR tokens claiming unauthorized issuers/authorities are rejected."""
    student = _create_user(db_session, "passport_stu4@test.com", UserRole.learner)
    headers = _login_user(client, student.email)

    fake_payload = {
        "v": 1,
        "site": "ngo-mon",
        "auth": "FAKE_UNAUTHORIZED_ENTITY",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "nonce": "testnonce123",
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(fake_payload).encode()).decode().rstrip("=")

    # Even with a secret signature, unapproved authority must fail
    from backend.services.heritage_passport import _get_secret_key
    sig = hmac.new(_get_secret_key().encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    fake_token = f"{payload_b64}.{sig}"

    res = client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers,
        json={"site_slug": "ngo-mon", "qr_token": fake_token},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "UNAUTHORIZED_HERITAGE_AUTHORITY"


# --------------------------------------------------------------------------- #
# 4. Visit Stamp DISTINCT from Assessed Mastery Tests
# --------------------------------------------------------------------------- #


def test_visit_stamp_distinct_from_assessed_mastery(client: TestClient, db_session):
    """Verify invariant: A verified visit stamp does NOT grant assessed academic mastery.

    Mastery strictly requires passing academic assessment quiz (score >= 80%).
    """
    student = _create_user(db_session, "passport_stu5@test.com", UserRole.learner, "Hoàng Nam")
    headers = _login_user(client, student.email)

    # Initial state: student has 0 mastered motifs
    summary_before = client.get("/api/v1/progress/summary", headers=headers).json()
    assert summary_before["mastered_count"] == 0

    # Student performs server check-in at Ngọ Môn
    qr_token = generate_qr_token(site_slug="ngo-mon")
    checkin_res = client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers,
        json={"site_slug": "ngo-mon", "qr_token": qr_token},
    )
    assert checkin_res.status_code == 200
    assert checkin_res.json()["is_verified"] is True
    assert checkin_res.json()["is_distinct_from_mastery"] is True

    # Check student progression summary: mastered_count MUST REMAIN 0!
    summary_after = client.get("/api/v1/progress/summary", headers=headers).json()
    assert summary_after["mastered_count"] == 0, "Visit stamp erroneously awarded academic mastery!"

    # Verify student's passport reflects 1 verified visit stamp, but 0 assessed masteries
    passport_res = client.get("/api/v1/progress/passport", headers=headers).json()
    assert passport_res["verified_stamps_count"] == 1
    assert passport_res["assessed_mastery_count"] == 0
    assert passport_res["distinct_invariants"]["visit_stamp_distinct_from_mastery"] is True


def test_negative_abuse_fake_client_claim_ignored(client: TestClient, db_session):
    """Verify negative abuse: Client claimed status='mastered' during check-in is strictly ignored."""
    student = _create_user(db_session, "passport_stu6@test.com", UserRole.learner)
    headers = _login_user(client, student.email)

    qr_token = generate_qr_token(site_slug="cuu-dinh")

    # Attacker attempts to pass client_claimed_status='mastered' to bypass quiz
    res = client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers,
        json={
            "site_slug": "cuu-dinh",
            "qr_token": qr_token,
            "client_claimed_status": "mastered",  # Spoofed claim
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_verified"] is True
    assert data["xp_awarded"] == 15  # Only visit XP, NOT mastery XP (75 XP)

    # Verify no UserProgress with mastered status exists
    mastered_prog = db_session.execute(
        select(UserProgress).where(
            UserProgress.user_id == student.id,
            UserProgress.status == UnlockStatus.mastered,
        )
    ).scalars().all()
    assert len(mastered_prog) == 0


# --------------------------------------------------------------------------- #
# 5. Teacher Analytics & Fake Local Completion Exclusion Tests
# --------------------------------------------------------------------------- #


def test_negative_abuse_fake_local_completion_excluded_from_teacher_analytics(client: TestClient, db_session):
    """Verify that fake local/client completions are excluded from teacher analytics.

    Teacher analytics queries ONLY server-persisted, verified records.
    """
    teacher = _create_user(db_session, "passport_teacher@test.com", UserRole.teacher, "Thầy Nguyễn Huệ")
    student_a = _create_user(db_session, "stu_authentic@test.com", UserRole.learner, "Học sinh Thật")
    student_b = _create_user(db_session, "stu_fake_local@test.com", UserRole.learner, "Học sinh Giả Mạo")

    # Setup classroom
    classroom = Classroom(
        name="Lớp 11 Lịch Sử Di Sản",
        class_code=f"C{uuid.uuid4().hex[:7]}",
        teacher_id=teacher.id,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    # Add members
    m_teacher = ClassMember(class_id=classroom.id, user_id=teacher.id, role="teacher")
    m_stu_a = ClassMember(class_id=classroom.id, user_id=student_a.id, role="learner")
    m_stu_b = ClassMember(class_id=classroom.id, user_id=student_b.id, role="learner")
    db_session.add_all([m_teacher, m_stu_a, m_stu_b])
    db_session.commit()

    # Student A performs genuine server check-in at Ngọ Môn & Điện Thái Hòa (2 stamps)
    headers_a = _login_user(client, student_a.email)
    client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers_a,
        json={"site_slug": "ngo-mon", "qr_token": generate_qr_token("ngo-mon")},
    )
    client.post(
        "/api/v1/progress/passport/check-in",
        headers=headers_a,
        json={"site_slug": "dien-thai-hoa", "qr_token": generate_qr_token("dien-thai-hoa")},
    )

    # Student B has 0 server-verified check-ins in DB (simulates local storage spoofing)
    # They have 0 records in heritage_passport_stamps

    # Teacher queries classroom passport analytics
    teacher_headers = _login_user(client, teacher.email)
    res = client.get(
        f"/api/v1/progress/passport/classroom/{classroom.id}",
        headers=teacher_headers,
    )
    assert res.status_code == 200, res.text
    analytics = res.json()

    assert analytics["classroom_id"] == str(classroom.id)
    assert analytics["student_count"] == 2
    assert analytics["total_verified_stamps"] == 2
    assert analytics["avg_verified_stamps"] == 1.0

    # Inspect individual student breakdowns
    students_data = {s["student_id"]: s for s in analytics["students"]}

    assert students_data[str(student_a.id)]["verified_stamps_count"] == 2
    # Student B MUST show 0 verified stamps regardless of any client-side localStorage claims
    assert students_data[str(student_b.id)]["verified_stamps_count"] == 0


def test_unauthenticated_and_cross_teacher_access_control(client: TestClient, db_session):
    """Verify security controls: Unauthenticated calls and cross-teacher snooping are forbidden."""
    # 1. Unauthenticated check-in rejected
    res_unauth = client.post(
        "/api/v1/progress/passport/check-in",
        json={"site_slug": "ngo-mon", "qr_token": "dummy"},
    )
    assert res_unauth.status_code == 401

    # 2. Cross-teacher access to classroom passport analytics
    teacher1 = _create_user(db_session, "teacher1@test.com", UserRole.teacher)
    teacher2 = _create_user(db_session, "teacher2@test.com", UserRole.teacher)

    classroom = Classroom(
        name="Lớp A",
        class_code=f"C{uuid.uuid4().hex[:7]}",
        teacher_id=teacher1.id,
    )
    db_session.add(classroom)
    db_session.commit()

    teacher2_headers = _login_user(client, teacher2.email)
    res_forbidden = client.get(
        f"/api/v1/progress/passport/classroom/{classroom.id}",
        headers=teacher2_headers,
    )
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["error"]["code"] == "FORBIDDEN_CLASSROOM_ACCESS"


# --------------------------------------------------------------------------- #
# 6. Legacy Route Compatibility Test
# --------------------------------------------------------------------------- #


def test_legacy_unlock_route_compatibility(client: TestClient):
    """Verify legacy frontend endpoint /api/v1/imperial/passport/unlock responds gracefully."""
    res = client.post(
        "/api/v1/imperial/passport/unlock",
        json={"monument_slug": "ngo-mon", "reason": "Test legacy unlock"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert res.json()["site_slug"] == "ngo-mon"
    assert res.json()["is_verified"] is False
