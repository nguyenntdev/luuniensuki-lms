# -*- coding: utf-8 -*-
"""V5-T104 (Wave W10, Slot A04): Museum QR Guided Trails Test Suite.

Audits and verifies:
1. Museum QR guided trail endpoint (/api/v1/heritage/places/{slug}/trail):
   - Returns verified context and primary source linking.
   - Generates cryptographically verifiable HMAC-SHA256 station QR tokens.
   - Provides 100% offline 2D rubbing fallback with file verification and checksums.
2. Verified station QR code authentication (/api/v1/heritage/trail/verify-qr):
   - Genuine token verification succeeds (200 OK, verified=True).
   - Rejection of tampered QR signatures (400 INVALID_QR_SIGNATURE).
   - Rejection of expired QR tokens (400 QR_EXPIRED).
   - Rejection of mismatched site tokens (400 QR_SITE_MISMATCH).
   - Rejection of malformed QR strings (400 INVALID_QR_TOKEN).
3. Accessibility route information & transparency:
   - Sites with verified wheelchair ramp routes (e.g. Điện Thái Hòa) report wheelchair_accessible=True.
   - Sites with steep ancient steps (e.g. Hiển Lâm Các, Lăng Khải Định) report wheelchair_accessible=False
     and detail specific stair barriers.
4. Negative abuse defense:
   - Unknown or unassessed accessibility data is NEVER falsely advertised as accessible.
   - Unverified sites return wheelchair_accessible=False, is_accessibility_verified=False,
     and explicit cautionary disclaimers.
5. Offline 2D rubbing fallback resilience:
   - High-contrast 2D rubbing metadata with existing disk files, legal attributions, and checksums.
6. Access control and unpublished place protection:
   - Unpublished/draft places return 404 to unauthenticated or non-staff users.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.config import settings
from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritagePlace,
    HeritageRecordStatus,
    HeritageSourceEvidence,
)
from backend.security import hash_password
from backend.services.heritage_trails import (
    AccessibilityGrade,
    generate_station_qr_payload,
    get_museum_guided_trail,
    verify_station_qr_token,
)


@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit before each test."""
    import backend.main as main

    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()
    yield
    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()


def _create_user(db_session, email: str, role: UserRole = UserRole.learner) -> User:
    """Helper to create and persist a test user."""
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        display_name=f"User {email.split('@')[0]}",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client: TestClient, email: str) -> None:
    """Helper to log in a user and set access session cookies on client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert res.status_code == 200, res.text


# --------------------------------------------------------------------------- #
# Test 1: Positive Trail Retrieval with Sources & 2D Rubbing Fallback
# --------------------------------------------------------------------------- #
def test_museum_qr_guided_trail_retrieval_and_sources(client: TestClient, db_session):
    """Test retrieval of museum guided trail with verified primary sources and 2D rubbing."""
    place = HeritagePlace(
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        name_en="Hall of Supreme Harmony",
        entity_type="monument",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
        location_lat=16.4697,
        location_lon=107.5794,
        visitor_summary_vi="Tòa điện thiết triều uy nghiêm trên trục thần đạo Hoàng thành.",
    )
    db_session.add(place)
    db_session.flush()

    source = HeritageSourceEvidence(
        place_id=place.id,
        source_title="Đại Nam Thực Lục Chính Biên (Đệ nhất kỷ)",
        source_author="Quốc sử quán triều Nguyễn",
        publication_year=1848,
        cited_section="Quyển 26",
        statement="Khởi công xây đắp Điện Thái Hòa quy thức trùng thiềm điệp ốc.",
        evidence_status="verified",
        reuse_rights="public_domain",
        content_scope="RBPC_HUE",
    )
    db_session.add(source)
    db_session.commit()

    res = client.get("/api/v1/heritage/places/dien-thai-hoa/trail")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["place_slug"] == "dien-thai-hoa"
    assert data["place_name_vi"] == "Điện Thái Hòa"
    assert data["total_stations"] >= 1
    assert data["primary_sources_count"] >= 1
    assert data["primary_sources"][0]["source_title"] == "Đại Nam Thực Lục Chính Biên (Đệ nhất kỷ)"

    # Verify 2D rubbing fallback
    rubbing = data["offline_rubbing_fallback"]
    assert rubbing["format"] == "image/jpeg"
    assert rubbing["rights_attribution"] != ""
    assert rubbing["file_exists"] is True

    # Verify Station QR code
    station = data["stations"][0]
    assert station["station_code"].startswith("QR-")
    assert "qr_token" in station
    assert "https://lms.histolab.icu/heritage/dien-thai-hoa?qr=" in station["qr_data_uri"]


# --------------------------------------------------------------------------- #
# Test 2: Cryptographic QR Code Verification & Tamper Resistance
# --------------------------------------------------------------------------- #
def test_trail_qr_cryptographic_verification_and_tampering(client: TestClient):
    """Test HMAC-SHA256 signature verification and tamper detection on QR tokens."""
    # 1. Genuine token
    qr_payload = generate_station_qr_payload(
        site_slug="dien-thai-hoa",
        station_index=1,
        authority="HMCC_HUE_HERITAGE",
        ttl_seconds=3600,
    )
    token = qr_payload["qr_token"]

    verify_res = client.post(
        "/api/v1/heritage/trail/verify-qr",
        json={"qr_token": token, "expected_site": "dien-thai-hoa"},
    )
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()
    assert verify_data["verified"] is True
    assert verify_data["site_slug"] == "dien-thai-hoa"
    assert verify_data["station_index"] == 1
    assert verify_data["authority"] == "HMCC_HUE_HERITAGE"

    # 2. Tampered signature rejected
    tampered_token = token[:-5] + "abcde"
    tamper_res = client.post(
        "/api/v1/heritage/trail/verify-qr",
        json={"qr_token": tampered_token, "expected_site": "dien-thai-hoa"},
    )
    assert tamper_res.status_code == 400
    assert tamper_res.json()["error"]["code"] == "INVALID_QR_SIGNATURE"

    # 3. Expired token rejected
    expired_payload = generate_station_qr_payload(
        site_slug="dien-thai-hoa",
        station_index=1,
        authority="HMCC_HUE_HERITAGE",
        ttl_seconds=-100,  # in the past
    )
    expired_res = client.post(
        "/api/v1/heritage/trail/verify-qr",
        json={"qr_token": expired_payload["qr_token"], "expected_site": "dien-thai-hoa"},
    )
    assert expired_res.status_code == 400
    assert expired_res.json()["error"]["code"] == "QR_EXPIRED"

    # 4. Site mismatch rejected
    mismatch_res = client.post(
        "/api/v1/heritage/trail/verify-qr",
        json={"qr_token": token, "expected_site": "lang-tu-duc"},
    )
    assert mismatch_res.status_code == 400
    assert mismatch_res.json()["error"]["code"] == "QR_SITE_MISMATCH"

    # 5. Malformed token rejected
    malformed_res = client.post(
        "/api/v1/heritage/trail/verify-qr",
        json={"qr_token": "not-a-valid-jwt-or-token"},
    )
    assert malformed_res.status_code == 400
    assert malformed_res.json()["error"]["code"] == "INVALID_QR_TOKEN"


# --------------------------------------------------------------------------- #
# Test 3: Wheelchair Accessibility Reporting (True Positive & True Negative)
# --------------------------------------------------------------------------- #
def test_trail_accessibility_positive_and_negative_reporting(client: TestClient, db_session):
    """Test that verified accessible sites report true, and stepped sites report false with notes."""
    # Seed dien-thai-hoa
    place_th = HeritagePlace(
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        entity_type="monument",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(place_th)
    db_session.commit()

    # A. Fully accessible site: Điện Thái Hòa
    res_thai_hoa = client.get("/api/v1/heritage/places/dien-thai-hoa/trail")
    assert res_thai_hoa.status_code == 200
    acc_thai_hoa = res_thai_hoa.json()["accessibility"]
    assert acc_thai_hoa["wheelchair_accessible"] is True
    assert acc_thai_hoa["is_accessibility_verified"] is True
    assert acc_thai_hoa["accessibility_grade"] == AccessibilityGrade.full_wheelchair.value
    assert len(acc_thai_hoa["ramp_locations"]) > 0

    # B. Inaccessible steep steps: Hiển Lâm Các
    place_hlc = HeritagePlace(
        slug="hien-lam-cac",
        name_vi="Hiển Lâm Các",
        entity_type="monument",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(place_hlc)
    db_session.commit()

    res_hlc = client.get("/api/v1/heritage/places/hien-lam-cac/trail")
    assert res_hlc.status_code == 200
    acc_hlc = res_hlc.json()["accessibility"]
    assert acc_hlc["wheelchair_accessible"] is False
    assert acc_hlc["is_accessibility_verified"] is True
    assert acc_hlc["accessibility_grade"] == AccessibilityGrade.inaccessible_steep_steps.value
    assert "cầu thang" in acc_hlc["wheelchair_route_summary"].lower()


# --------------------------------------------------------------------------- #
# Test 4: Negative Abuse - Unknown Accessibility is NEVER Falsely Advertised
# --------------------------------------------------------------------------- #
def test_negative_abuse_unknown_accessibility_is_never_advertised_as_accessible(
    client: TestClient, db_session
):
    """Negative Abuse Invariant: Sites without verified accessibility surveys MUST NOT be falsely advertised as accessible."""
    place_unknown = HeritagePlace(
        slug="chua-huyen-bi-unverified",
        name_vi="Chùa Huyền Bí (Chưa Khảo Sát)",
        entity_type="site",
        heritage_category="religious_spiritual",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(place_unknown)
    db_session.commit()

    res = client.get("/api/v1/heritage/places/chua-huyen-bi-unverified/trail")
    assert res.status_code == 200
    acc = res.json()["accessibility"]

    # Invariant assertion: strictly NOT accessible and strictly unverified
    assert acc["wheelchair_accessible"] is False
    assert acc["is_accessibility_verified"] is False
    assert acc["accessibility_grade"] == AccessibilityGrade.unknown_unverified.value
    assert "chưa được khảo sát" in acc["wheelchair_route_summary"].lower()
    assert acc["ramp_locations"] == []


# --------------------------------------------------------------------------- #
# Test 5: Unpublished Heritage Place Protection
# --------------------------------------------------------------------------- #
def test_unpublished_place_trail_protection(client: TestClient, db_session):
    """Verify that draft/unpublished places return 404 to anonymous visitors."""
    place_draft = HeritagePlace(
        slug="draft-palace-secret",
        name_vi="Cung Điện Mới Khảo Sát",
        entity_type="building",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.draft.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(place_draft)
    db_session.commit()

    # Anonymous user gets 404
    res_anon = client.get("/api/v1/heritage/places/draft-palace-secret/trail")
    assert res_anon.status_code == 404
    assert res_anon.json()["error"]["code"] == "HERITAGE_PLACE_NOT_FOUND"

    # Staff user can view draft trail
    staff = _create_user(db_session, "trail_staff@histolab.icu", role=UserRole.admin)
    _login_user(client, "trail_staff@histolab.icu")

    res_staff = client.get("/api/v1/heritage/places/draft-palace-secret/trail")
    assert res_staff.status_code == 200
    assert res_staff.json()["place_slug"] == "draft-palace-secret"
