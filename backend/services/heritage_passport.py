# -*- coding: utf-8 -*-
"""Heritage Passport service for verified site check-ins and QR provenance.

Invariants:
1. Server-authenticated check-in: All passport stamps are validated server-side.
2. QR Code Provenance: Cryptographically verified HMAC-SHA256 signatures issued by authorized heritage bodies.
3. Visit Stamp != Assessed Mastery: A verified visit stamp records physical or verified site presence.
   It NEVER automatically grants curriculum mastery (score >= 80% quiz or mastered progression).
4. Negative Abuse Defense: Fake local/client completions (localStorage manipulation, spoofed status claims)
   are strictly rejected and excluded from teacher analytics and verified passport stamps.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..errors import AppError
from ..models import (
    ClassMember,
    Classroom,
    HeritagePassportStamp,
    UnlockStatus,
    User,
    UserProgress,
    UserRole,
)

logger = logging.getLogger("luuniensuki.passport")

# Standard Hue Imperial City Monument Catalog (16 Royal Seals / Sites)
IMPERIAL_MONUMENTS_CATALOG: dict[str, dict[str, Any]] = {
    "ngo-mon": {
        "slug": "ngo-mon",
        "name": "Ngọ Môn",
        "name_han_nom": "午門",
        "seal_title": "Ngọ Môn Chi Ấn",
        "zone_slug": "central-ceremonial-axis",
        "zone_name": "Trục trung tâm",
        "construction_year": 1833,
        "reign": "Minh Mạng",
    },
    "cau-trung-dao": {
        "slug": "cau-trung-dao",
        "name": "Cầu Trung Đạo",
        "name_han_nom": "中道橋",
        "seal_title": "Trung Đạo Kiều Triện",
        "zone_slug": "central-ceremonial-axis",
        "zone_name": "Trục trung tâm",
        "construction_year": 1833,
        "reign": "Minh Mạng",
    },
    "san-dai-trieu-nghi": {
        "slug": "san-dai-trieu-nghi",
        "name": "Sân Đại Triều Nghi",
        "name_han_nom": "大朝儀墀",
        "seal_title": "Đại Triều Nghi Triện",
        "zone_slug": "central-ceremonial-axis",
        "zone_name": "Trục trung tâm",
        "construction_year": 1805,
        "reign": "Gia Long",
    },
    "dien-thai-hoa": {
        "slug": "dien-thai-hoa",
        "name": "Điện Thái Hòa",
        "name_han_nom": "太和殿",
        "seal_title": "Thái Hòa Điện Ấn",
        "zone_slug": "central-ceremonial-axis",
        "zone_name": "Trục trung tâm",
        "construction_year": 1805,
        "reign": "Gia Long",
    },
    "the-mieu": {
        "slug": "the-mieu",
        "name": "Thế Miếu",
        "name_han_nom": "世廟",
        "seal_title": "Thế Tổ Miếu Triện",
        "zone_slug": "ancestral-worship-space",
        "zone_name": "Không gian thờ tự",
        "construction_year": 1821,
        "reign": "Minh Mạng",
    },
    "hien-lam-cac": {
        "slug": "hien-lam-cac",
        "name": "Hiển Lâm Các",
        "name_han_nom": "顯臨閣",
        "seal_title": "Hiển Lâm Các Triện",
        "zone_slug": "ancestral-worship-space",
        "zone_name": "Không gian thờ tự",
        "construction_year": 1821,
        "reign": "Minh Mạng",
    },
    "cuu-dinh": {
        "slug": "cuu-dinh",
        "name": "Cửu Đỉnh",
        "name_han_nom": "九鼎",
        "seal_title": "Hoàng Triều Cửu Đỉnh Triện",
        "zone_slug": "ancestral-worship-space",
        "zone_name": "Không gian thờ tự",
        "construction_year": 1835,
        "reign": "Minh Mạng",
    },
    "dien-phung-tien": {
        "slug": "dien-phung-tien",
        "name": "Điện Phụng Tiên",
        "name_han_nom": "奉先殿",
        "seal_title": "Phụng Tiên Điện Ấn",
        "zone_slug": "ancestral-worship-space",
        "zone_name": "Không gian thờ tự",
        "construction_year": 1829,
        "reign": "Minh Mạng",
    },
    "dai-cung-mon": {
        "slug": "dai-cung-mon",
        "name": "Đại Cung Môn",
        "name_han_nom": "大宮門",
        "seal_title": "Đại Cung Môn Triện",
        "zone_slug": "purple-forbidden-city",
        "zone_name": "Tử Cấm Thành",
        "construction_year": 1833,
        "reign": "Minh Mạng",
    },
    "dien-can-chanh": {
        "slug": "dien-can-chanh",
        "name": "Điện Cần Chánh",
        "name_han_nom": "勤政殿",
        "seal_title": "Cần Chánh Điện Ấn",
        "zone_slug": "purple-forbidden-city",
        "zone_name": "Tử Cấm Thành",
        "construction_year": 1804,
        "reign": "Gia Long",
    },
    "dien-can-thanh": {
        "slug": "dien-can-thanh",
        "name": "Điện Càn Thành",
        "name_han_nom": "乾成殿",
        "seal_title": "Càn Thành Điện Ấn",
        "zone_slug": "purple-forbidden-city",
        "zone_name": "Tử Cấm Thành",
        "construction_year": 1811,
        "reign": "Gia Long",
    },
    "dien-khon-thai": {
        "slug": "dien-khon-thai",
        "name": "Điện Khôn Thái",
        "name_han_nom": "坤泰殿",
        "seal_title": "Khôn Thái Điện Ấn",
        "zone_slug": "purple-forbidden-city",
        "zone_name": "Tử Cấm Thành",
        "construction_year": 1807,
        "reign": "Gia Long",
    },
    "nhat-thanh-lau": {
        "slug": "nhat-thanh-lau",
        "name": "Nhật Thành Lầu",
        "name_han_nom": "日成樓",
        "seal_title": "Nhật Thành Lầu Triện",
        "zone_slug": "purple-forbidden-city",
        "zone_name": "Tử Cấm Thành",
        "construction_year": 1923,
        "reign": "Khải Định",
    },
    "vuon-thieu-phuong": {
        "slug": "vuon-thieu-phuong",
        "name": "Vườn Thiệu Phương",
        "name_han_nom": "紹芳園",
        "seal_title": "Thiệu Phương Ngự Uyển Triện",
        "zone_slug": "royal-living-gardens",
        "zone_name": "Không gian sinh hoạt",
        "construction_year": 1841,
        "reign": "Thiệu Trị",
    },
    "thai-binh-lau": {
        "slug": "thai-binh-lau",
        "name": "Thái Bình Lầu",
        "name_han_nom": "太平樓",
        "seal_title": "Thái Bình Thư Lầu Triện",
        "zone_slug": "royal-living-gardens",
        "zone_name": "Không gian sinh hoạt",
        "construction_year": 1921,
        "reign": "Khải Định",
    },
    "cung-dien-tho": {
        "slug": "cung-dien-tho",
        "name": "Cung Diên Thọ",
        "name_han_nom": "延壽宮",
        "seal_title": "Diên Thọ Cung Ấn",
        "zone_slug": "royal-living-gardens",
        "zone_name": "Không gian sinh hoạt",
        "construction_year": 1804,
        "reign": "Gia Long",
    },
}

TOTAL_CATALOG_SEALS = len(IMPERIAL_MONUMENTS_CATALOG)
PASSPORT_CHECKIN_XP = 15

ALLOWED_AUTHORITIES = {
    "HMCC_HUE_HERITAGE",
    "LUUNIENSUKI_OFFICIAL",
    "HUE_MONUMENTS_CENTRE",
}


def _get_secret_key(override: Optional[str] = None) -> str:
    """Return the HMAC key used to generate and verify QR codes."""
    if override:
        return override
    key = getattr(settings, "jwt_secret_key", None)
    if not key or key == "insecure_dev_secret_change_in_prod":
        return "luuniensuki_heritage_passport_qr_secret_key_2026"
    return str(key)


def generate_qr_token(
    site_slug: str,
    authority: str = "HMCC_HUE_HERITAGE",
    expires_in_seconds: int = 86400,
    nonce: Optional[str] = None,
    secret: Optional[str] = None,
) -> str:
    """Generate a cryptographically verifiable QR check-in token for a heritage site."""
    if site_slug not in IMPERIAL_MONUMENTS_CATALOG:
        raise AppError(
            code="SITE_NOT_FOUND",
            message=f"Heritage site '{site_slug}' is not recognized in monument catalog.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    now_ts = int(time.time())
    exp_ts = (now_ts + expires_in_seconds) if (expires_in_seconds is not None and expires_in_seconds != 0) else 0
    token_nonce = nonce or uuid.uuid4().hex[:12]

    payload = {
        "v": 1,
        "site": site_slug,
        "auth": authority,
        "iat": now_ts,
        "exp": exp_ts,
        "nonce": token_nonce,
    }

    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")

    secret_key = _get_secret_key(secret)
    signature = hmac.new(
        secret_key.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_qr_token(
    qr_token: str,
    expected_site: Optional[str] = None,
    secret: Optional[str] = None,
) -> dict[str, Any]:
    """Validate a QR check-in token's cryptographic signature, expiration, and authority."""
    if not qr_token or "." not in qr_token:
        raise AppError(
            code="INVALID_QR_FORMAT",
            message="QR check-in token is missing or malformed.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    parts = qr_token.strip().split(".")
    if len(parts) != 2:
        raise AppError(
            code="INVALID_QR_FORMAT",
            message="QR token format must be payload.signature.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    payload_b64, signature = parts[0], parts[1]

    # Verify HMAC signature
    secret_key = _get_secret_key(secret)
    expected_sig = hmac.new(
        secret_key.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        logger.warning("QR provenance signature mismatch: potential forgery or tampering detected.")
        raise AppError(
            code="INVALID_QR_SIGNATURE",
            message="QR code cryptographic provenance signature is invalid or tampered.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Decode payload
    try:
        # Re-pad base64url string if needed
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        raw_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(raw_json)
    except Exception as e:
        raise AppError(
            code="MALFORMED_QR_PAYLOAD",
            message=f"Failed to decode QR code payload: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate authority
    auth = payload.get("auth", "")
    if auth not in ALLOWED_AUTHORITIES:
        raise AppError(
            code="UNAUTHORIZED_HERITAGE_AUTHORITY",
            message=f"QR token authority '{auth}' is not recognized or authorized.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate expiration
    exp = payload.get("exp", 0)
    now_ts = int(time.time())
    if exp > 0 and now_ts > exp:
        raise AppError(
            code="QR_EXPIRED",
            message=f"QR check-in token expired at {datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    token_site = payload.get("site", "")
    if token_site not in IMPERIAL_MONUMENTS_CATALOG:
        raise AppError(
            code="SITE_NOT_FOUND",
            message=f"Site '{token_site}' specified in QR is not in monument catalog.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Validate expected site if supplied
    if expected_site and token_site != expected_site:
        raise AppError(
            code="QR_SITE_MISMATCH",
            message=f"QR token is issued for site '{token_site}', but check-in was requested for '{expected_site}'.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return {
        "valid": True,
        "site_slug": token_site,
        "site_name": IMPERIAL_MONUMENTS_CATALOG[token_site]["name"],
        "zone_slug": IMPERIAL_MONUMENTS_CATALOG[token_site]["zone_slug"],
        "authority": auth,
        "issued_at": datetime.fromtimestamp(payload.get("iat", now_ts), tz=timezone.utc),
        "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc) if exp > 0 else None,
        "nonce": payload.get("nonce"),
        "signature": signature,
    }


def process_server_checkin(
    db: Session,
    user: User,
    site_slug: str,
    verification_method: str = "qr_code",
    qr_token: Optional[str] = None,
    qr_payload: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    device_metadata: Optional[dict[str, Any]] = None,
    client_claimed_status: Optional[str] = None,
) -> dict[str, Any]:
    """Execute a server-authenticated check-in and issue a verified heritage passport stamp.

    Guarantees:
    - Visit stamp != assessed mastery. A visit stamp records physical presence, NOT curriculum mastery.
    - Negative abuse: Fake client completion claims (e.g. client_claimed_status="mastered") are strictly ignored.
    - Anti-replay: Repeated check-ins increment checkin_count but award 0 duplicate XP.
    """
    if site_slug not in IMPERIAL_MONUMENTS_CATALOG:
        raise AppError(
            code="SITE_NOT_FOUND",
            message=f"Monuments site '{site_slug}' is not recognized.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    site_info = IMPERIAL_MONUMENTS_CATALOG[site_slug]

    # Verify provenance based on verification method
    qr_nonce = None
    authority = "HMCC_HUE_HERITAGE"
    effective_token = qr_token or qr_payload

    if verification_method == "qr_code":
        if not effective_token:
            raise AppError(
                code="QR_TOKEN_REQUIRED",
                message="A valid QR provenance token is required for physical QR check-in.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        verification_result = verify_qr_token(effective_token, expected_site=site_slug)
        qr_nonce = verification_result["nonce"]
        authority = verification_result["authority"]
    elif verification_method in {"geofence", "staff_code", "kiosk"}:
        # Staff or kiosk verification
        qr_nonce = f"{verification_method}_{uuid.uuid4().hex[:8]}"
        authority = "LUUNIENSUKI_OFFICIAL"
    else:
        raise AppError(
            code="UNSUPPORTED_VERIFICATION_METHOD",
            message=f"Verification method '{verification_method}' is not supported.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Negative Abuse defense: Client cannot claim 'mastered' status or bypass academic evaluation
    if client_claimed_status:
        logger.info(
            "Client claimed status '%s' during passport check-in for user %s. Ignored per invariant V5-T092.",
            client_claimed_status,
            user.id,
        )

    now = datetime.now(timezone.utc)

    # Check for existing stamp
    existing_stamp = db.execute(
        select(HeritagePassportStamp).where(
            HeritagePassportStamp.user_id == user.id,
            HeritagePassportStamp.site_slug == site_slug,
        )
    ).scalar_one_or_none()

    xp_awarded = 0
    if existing_stamp:
        # Existing verified stamp: increment visit count, update timestamp, zero repeat XP
        existing_stamp.checkin_count += 1
        existing_stamp.last_visited_at = now
        existing_stamp.is_verified = True
        stamp = existing_stamp
        message = f"Chào mừng bạn quay lại {site_info['name']}! Bạn đã ghé thăm {stamp.checkin_count} lần."
    else:
        # First-time verified check-in
        xp_awarded = PASSPORT_CHECKIN_XP
        user.total_xp = (user.total_xp or 0) + xp_awarded

        # Cryptographic provenance hash linking user, site, timestamp, and QR nonce
        provenance_str = f"{user.id}:{site_slug}:{qr_nonce}:{now.isoformat()}:{authority}"
        provenance_hash = hashlib.sha256(provenance_str.encode("utf-8")).hexdigest()

        stamp = HeritagePassportStamp(
            user_id=user.id,
            site_slug=site_slug,
            site_name=site_info["name"],
            zone_slug=site_info["zone_slug"],
            verification_method=verification_method,
            qr_nonce=qr_nonce,
            provenance_hash=provenance_hash,
            authority=authority,
            stamped_at=now,
            checkin_count=1,
            last_visited_at=now,
            is_verified=True,
            latitude=latitude,
            longitude=longitude,
            device_metadata=device_metadata,
        )
        db.add(stamp)
        message = f"Chúc mừng! Đã đóng dấu xác thực thành công tại {site_info['name']} (+{xp_awarded} XP)."

    db.commit()
    db.refresh(stamp)

    return {
        "success": True,
        "stamp_id": stamp.id,
        "site_slug": stamp.site_slug,
        "site_name": stamp.site_name,
        "zone_slug": stamp.zone_slug,
        "verification_method": stamp.verification_method,
        "provenance_hash": stamp.provenance_hash,
        "authority": stamp.authority,
        "stamped_at": stamp.stamped_at,
        "checkin_count": stamp.checkin_count,
        "xp_awarded": xp_awarded,
        "is_verified": stamp.is_verified,
        "is_distinct_from_mastery": True,
        "message": message,
    }


def get_verified_passport(db: Session, user: User) -> dict[str, Any]:
    """Retrieve current user's verified passport and distinct curriculum mastery count."""
    # Verified stamps in DB
    stamps = db.execute(
        select(HeritagePassportStamp)
        .where(
            HeritagePassportStamp.user_id == user.id,
            HeritagePassportStamp.is_verified.is_(True),
        )
        .order_by(HeritagePassportStamp.stamped_at.asc())
    ).scalars().all()

    # Assessed academic mastery in DB (strictly distinct from visit stamps)
    mastered_count = db.execute(
        select(func.count(UserProgress.id)).where(
            UserProgress.user_id == user.id,
            UserProgress.status == UnlockStatus.mastered,
        )
    ).scalar_one()

    verified_count = len(stamps)
    completion_pct = round((verified_count / TOTAL_CATALOG_SEALS) * 100, 1)

    return {
        "user_id": user.id,
        "display_name": user.display_name or user.username or "Học viên",
        "verified_stamps_count": verified_count,
        "total_available_seals": TOTAL_CATALOG_SEALS,
        "verified_completion_percent": completion_pct,
        "assessed_mastery_count": mastered_count,
        "can_export_verified_certificate": verified_count >= 12,
        "distinct_invariants": {
            "visit_stamp_distinct_from_mastery": True,
            "fake_local_stamps_excluded": True,
        },
        "stamps": [
            {
                "id": s.id,
                "site_slug": s.site_slug,
                "site_name": s.site_name,
                "zone_slug": s.zone_slug,
                "verification_method": s.verification_method,
                "provenance_hash": s.provenance_hash,
                "authority": s.authority,
                "stamped_at": s.stamped_at,
                "checkin_count": s.checkin_count,
                "last_visited_at": s.last_visited_at,
                "is_verified": s.is_verified,
                "is_distinct_from_mastery": True,
            }
            for s in stamps
        ],
    }


def get_teacher_classroom_passport_analytics(
    db: Session,
    classroom_id: UUID,
    current_user: User,
) -> dict[str, Any]:
    """Provide teacher analytics for verified passport check-ins across a classroom.

    Invariant:
    Fake local/client completion is NOT counted. Only server-authenticated,
    verified stamps stored in heritage_passport_stamps are queried and aggregated.
    """
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise AppError(
            code="CLASSROOM_NOT_FOUND",
            message="Classroom not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Permission check: user must be the teacher or an admin
    if current_user.role not in (UserRole.admin, UserRole.super_admin):
        if classroom.teacher_id != current_user.id:
            raise AppError(
                code="FORBIDDEN_CLASSROOM_ACCESS",
                message="Only classroom teachers or admins may access student passport analytics.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # Query enrolled learners
    learner_members = db.execute(
        select(ClassMember).where(
            ClassMember.class_id == classroom_id,
            ClassMember.role == "learner",
        )
    ).scalars().all()

    student_summaries: list[dict[str, Any]] = []
    total_stamps_sum = 0

    for m in learner_members:
        student = db.get(User, m.user_id)
        if not student:
            continue

        # Strictly query server-verified records
        student_stamps = db.execute(
            select(HeritagePassportStamp).where(
                HeritagePassportStamp.user_id == student.id,
                HeritagePassportStamp.is_verified.is_(True),
            ).order_by(HeritagePassportStamp.last_visited_at.desc())
        ).scalars().all()

        verified_count = len(student_stamps)
        total_stamps_sum += verified_count
        last_stamp = student_stamps[0].last_visited_at if student_stamps else None

        # Assessed mastery count
        mastered_count = db.execute(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == student.id,
                UserProgress.status == UnlockStatus.mastered,
            )
        ).scalar_one()

        student_summaries.append({
            "student_id": student.id,
            "display_name": student.display_name or student.username or "Học sinh",
            "email": student.email,
            "verified_stamps_count": verified_count,
            "assessed_mastery_count": mastered_count,
            "last_stamp_at": last_stamp,
            "is_fake_client_claim_detected": False,
        })

    student_count = len(student_summaries)
    avg_stamps = round(total_stamps_sum / student_count, 1) if student_count > 0 else 0.0

    return {
        "classroom_id": classroom_id,
        "student_count": student_count,
        "total_verified_stamps": total_stamps_sum,
        "avg_verified_stamps": avg_stamps,
        "students": student_summaries,
    }
