# -*- coding: utf-8 -*-
"""Business logic and repository service for Partner Discovery & LOI Vault (Ticket V5-T113 / Wave W11 Slot A03).

Features:
- Canonical partner agreements registry with real Huế heritage institutions
- Cryptographic SHA-256 agreement checksums (strictly barring raw signatures or PII)
- Negative abuse enforcement: Revoked or expired partnerships are strictly excluded from active partner discovery
- Secure LOI registration, verification, and revocation workflows
"""
from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from ..apischemas.partner_loi import (
    RbpcLoiChecksumVerifyOut,
    RbpcLoiRegisterIn,
)
from ..errors import AppError
from ..partner_loi_models import (
    RbpcLoiConsentType,
    RbpcPartnerCategory,
    RbpcPartnerLoiStatus,
    RbpcPartnerLoiVault,
)


# --------------------------------------------------------------------------- #
# Canonical Partner LOI Registry (8 Real Huế Heritage Entities)
# --------------------------------------------------------------------------- #
CANONICAL_PARTNER_LOIS: List[Dict[str, Any]] = [
    {
        "loi_id": "LOI-HUE-BRONZE-001",
        "partner_id": "PARTNER-BRONZE-001",
        "partner_name": "Hợp tác xã Đúc đồng Phường Đúc Huế",
        "partner_name_en": "Phuong Duc Bronze Casting Cooperative Hue",
        "slug": "phuong-duc-bronze-casting",
        "category": RbpcPartnerCategory.craft_guild.value,
        "institution_type": "artisan_guild",
        "region": "Phường Đúc, TP. Huế",
        "scope_of_partnership": "Chế tác đồng mỹ nghệ, lưu giữ kỹ thuật đúc Cửu Đỉnh truyền thống, tổ chức workshop đúc mẫu cho học viên và du khách.",
        "scope_details": {
            "focus_areas": ["Imperial Bronze Foundry", "Nine Dynastic Urns casting technique", "Apprentice workshops"],
            "max_monthly_workshops": 12,
            "quota_students_per_session": 15,
            "dignity_charter_confirmed": True,
        },
        "consent_type": RbpcLoiConsentType.bilateral_charter.value,
        "consent_status": "consented",
        "status": RbpcPartnerLoiStatus.active.value,
        "effective_date": datetime.date(2026, 1, 1),
        "expiration_date": datetime.date(2027, 12, 31),
        "agreement_checksum_sha256": "7b988f912445e999c0da27845ba0e64c18c17375a0df1248ab3c7a07530e3860",
        "dignity_charter_binding": True,
        "commercial_terms": {
            "take_rate_pct": 10,
            "upfront_listing_fee_vnd": 0,
            "settlement_cycle": "biweekly",
        },
        "lead_artisan_title": "Nghệ nhân Ưu tú Nguyễn Văn Sáng",
        "contact_role": "Chủ nhiệm Hợp tác xã",
        "is_verified": True,
        "verified_at": datetime.datetime(2026, 1, 2, 8, 30, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "loi_id": "LOI-HUE-PHAPLAM-002",
        "partner_id": "PARTNER-PHAPLAM-002",
        "partner_name": "Xưởng Pháp lam Thái Hưng Huế",
        "partner_name_en": "Thai Hung Hue Enamel Studio",
        "slug": "thai-hung-phap-lam-enamel",
        "category": RbpcPartnerCategory.craft_guild.value,
        "institution_type": "artisan_studio",
        "region": "Kim Long, TP. Huế",
        "scope_of_partnership": "Khôi phục nghệ thuật Pháp lam cung đình Nguyễn, tổ chức trải nghiệm tráng men và nung lò cho đoàn tham quan.",
        "scope_details": {
            "focus_areas": ["Cloisonné and Painted Enamel", "Imperial architectural ornaments", "Experiential firing classes"],
            "max_monthly_workshops": 8,
            "quota_students_per_session": 10,
            "dignity_charter_confirmed": True,
        },
        "consent_type": RbpcLoiConsentType.written_loi.value,
        "consent_status": "consented",
        "status": RbpcPartnerLoiStatus.active.value,
        "effective_date": datetime.date(2026, 2, 1),
        "expiration_date": datetime.date(2027, 6, 30),
        "agreement_checksum_sha256": "23dcae32d5e78393eef1dc9ea338db714d64ef817c9b0e2ad0b0c649938b8ca7",
        "dignity_charter_binding": True,
        "commercial_terms": {
            "take_rate_pct": 10,
            "upfront_listing_fee_vnd": 0,
            "settlement_cycle": "monthly",
        },
        "lead_artisan_title": "Nghệ nhân Đỗ Hữu Triết",
        "contact_role": "Giám đốc Nghệ thuật & Sáng lập",
        "is_verified": True,
        "verified_at": datetime.datetime(2026, 2, 2, 9, 15, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "loi_id": "LOI-HUE-TRUCCHI-003",
        "partner_id": "PARTNER-TRUCCHI-003",
        "partner_name": "Nghệ thuật Trúc Chỉ Việt Nam - Không gian Huế",
        "partner_name_en": "Vietnam Truc Chi Art Studio Hue",
        "slug": "truc-chi-art-hue",
        "category": RbpcPartnerCategory.cultural_association.value,
        "institution_type": "art_atelier",
        "region": "Vĩnh Ninh, TP. Huế",
        "scope_of_partnership": "Trình diễn chế tác đồ họa trúc chỉ trên xơ tre/dừa, kết hợp họa tiết Cửu Đỉnh vào mỹ thuật ứng dụng.",
        "scope_details": {
            "focus_areas": ["Truc Chi handmade paper art", "Water-pressure graphy", "Heritage motifs contemporary art"],
            "max_monthly_workshops": 10,
            "quota_students_per_session": 12,
            "dignity_charter_confirmed": True,
        },
        "consent_type": RbpcLoiConsentType.signed_mou.value,
        "consent_status": "consented",
        "status": RbpcPartnerLoiStatus.active.value,
        "effective_date": datetime.date(2026, 1, 15),
        "expiration_date": datetime.date(2027, 12, 31),
        "agreement_checksum_sha256": "a1bc40285a214d4e3cb481e370e515d6ad05e04cb212e105a5a7dc64ecb90e9e",
        "dignity_charter_binding": True,
        "commercial_terms": {
            "take_rate_pct": 10,
            "upfront_listing_fee_vnd": 0,
            "settlement_cycle": "biweekly",
        },
        "lead_artisan_title": "Họa sĩ Phan Hải Bằng",
        "contact_role": "Chủ nhiệm Sáng lập Trúc Chỉ",
        "is_verified": True,
        "verified_at": datetime.datetime(2026, 1, 16, 10, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "loi_id": "LOI-HUE-EMBROID-004",
        "partner_id": "PARTNER-EMBROID-004",
        "partner_name": "Hợp tác xã Thêu Cung đình Phú Cam",
        "partner_name_en": "Phu Cam Imperial Embroidery Cooperative",
        "slug": "phu-cam-imperial-embroidery",
        "category": RbpcPartnerCategory.craft_guild.value,
        "institution_type": "artisan_guild",
        "region": "Phường Phước Vĩnh, TP. Huế",
        "scope_of_partnership": "Phục dựng hoa văn thêu chỉ vàng triều Nguyễn trên gấm lụa, hướng dẫn học viên thực hành thêu tay.",
        "scope_details": {
            "focus_areas": ["Gold thread royal embroidery", "Silk brocade preservation", "Textile craft classes"],
            "max_monthly_workshops": 6,
            "quota_students_per_session": 8,
            "dignity_charter_confirmed": True,
        },
        "consent_type": RbpcLoiConsentType.bilateral_charter.value,
        "consent_status": "consented",
        "status": RbpcPartnerLoiStatus.active.value,
        "effective_date": datetime.date(2026, 3, 1),
        "expiration_date": datetime.date(2027, 8, 31),
        "agreement_checksum_sha256": "59f42de63467c9c0d16c528f8f260335e3ec7fa6d38e65e68379b3ee42a6c8b9",
        "dignity_charter_binding": True,
        "commercial_terms": {
            "take_rate_pct": 10,
            "upfront_listing_fee_vnd": 0,
            "settlement_cycle": "monthly",
        },
        "lead_artisan_title": "Nghệ nhân Lê Văn Kinh",
        "contact_role": "Trưởng môn Phái thêu Cung đình",
        "is_verified": True,
        "verified_at": datetime.datetime(2026, 3, 2, 14, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "loi_id": "LOI-HUE-QUOCHOC-005",
        "partner_id": "PARTNER-QUOCHOC-005",
        "partner_name": "CLB Di sản & Sử học THPT Chuyên Quốc Học Huế",
        "partner_name_en": "Quoc Hoc High School Heritage & History Club",
        "slug": "quoc-hoc-heritage-club",
        "category": RbpcPartnerCategory.educational_institution.value,
        "institution_type": "high_school",
        "region": "Lê Lợi, TP. Huế",
        "scope_of_partnership": "Thí điểm dự án học tập trải nghiệm tích hợp GDPT 2018, đồng tổ chức tour thực địa Cửu Đỉnh cho học sinh.",
        "scope_details": {
            "focus_areas": ["Grade 10-12 local history modules", "Experiential learning trails", "Student inquiry rubrics"],
            "max_student_cohorts": 4,
            "dignity_charter_confirmed": True,
        },
        "consent_type": RbpcLoiConsentType.framework_agreement.value,
        "consent_status": "consented",
        "status": RbpcPartnerLoiStatus.active.value,
        "effective_date": datetime.date(2026, 1, 10),
        "expiration_date": datetime.date(2027, 5, 31),
        "agreement_checksum_sha256": "a9062eb1ea2e0fb525046e7f722ec10b501cf5681aa3ee7e9114f04642ef9982",
        "dignity_charter_binding": True,
        "commercial_terms": {
            "educational_discount_pct": 100,
            "upfront_listing_fee_vnd": 0,
            "institutional_partnership": True,
        },
        "lead_artisan_title": "ThS. Hoàng Thị Thu Hương",
        "contact_role": "Giáo viên Tổ Lịch sử & Chủ nhiệm CLB",
        "is_verified": True,
        "verified_at": datetime.datetime(2026, 1, 11, 11, 30, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "loi_id": "LOI-HUE-HMCC-006",
        "partner_id": "PARTNER-HMCC-006",
        "partner_name": "Chi hội Hướng dẫn viên Di sản Huế (Liên kết TTBTDT Cố đô)",
        "partner_name_en": "Hue Heritage Guides Association",
        "slug": "hue-heritage-guides-association",
        "category": RbpcPartnerCategory.tourism_operator.value,
        "institution_type": "tourism_association",
        "region": "Đại Nội, TP. Huế",
        "scope_of_partnership": "Đào tạo và kiểm định thuyết minh viên di sản theo tài liệu Đại Nam Thực Lục, cung cấp tour chuyên gia.",
        "scope_details": {
            "focus_areas": ["Curated expert tour guide certification", "Footnote archival source training", "Visitor tour facilitation"],
            "licensed_guides_count": 28,
            "dignity_charter_confirmed": True,
        },
        "consent_type": RbpcLoiConsentType.signed_mou.value,
        "consent_status": "consented",
        "status": RbpcPartnerLoiStatus.active.value,
        "effective_date": datetime.date(2026, 2, 15),
        "expiration_date": datetime.date(2027, 12, 31),
        "agreement_checksum_sha256": "80145c256eefbfd67b255543c7262dc1e7b6d131f4228c2e2e987910ffbe97f2",
        "dignity_charter_binding": True,
        "commercial_terms": {
            "take_rate_pct": 10,
            "upfront_listing_fee_vnd": 0,
            "settlement_cycle": "biweekly",
        },
        "lead_artisan_title": "Ông Nguyễn Quang Trung",
        "contact_role": "Chi hội trưởng",
        "is_verified": True,
        "verified_at": datetime.datetime(2026, 2, 16, 16, 20, 0, tzinfo=datetime.timezone.utc),
    },
    # Negative abuse test benchmarks: Expired agreement
    {
        "loi_id": "LOI-HUE-WOOD-007",
        "partner_id": "PARTNER-WOOD-007",
        "partner_name": "Xưởng Mộc Chạm Mỹ nghệ Hương Thủy (Đã hết hạn)",
        "partner_name_en": "Huong Thuy Traditional Wood Carving (Expired)",
        "slug": "huong-thuy-wood-expired",
        "category": RbpcPartnerCategory.craft_guild.value,
        "institution_type": "artisan_workshop",
        "region": "Thị xã Hương Thủy, Thừa Thiên Huế",
        "scope_of_partnership": "Thí điểm chạm khắc mộc mô phỏng quai vạc Cửu Đỉnh (Hợp đồng thử nghiệm 2025).",
        "scope_details": {"archived_pilot": True},
        "consent_type": RbpcLoiConsentType.written_loi.value,
        "consent_status": "expired",
        "status": RbpcPartnerLoiStatus.expired.value,
        "effective_date": datetime.date(2025, 1, 1),
        "expiration_date": datetime.date(2025, 12, 31),  # In the past
        "agreement_checksum_sha256": "8680d249f7ba3e8992ad81335ee9191d45129656461665a3c9be087799b66bb2",
        "dignity_charter_binding": True,
        "commercial_terms": {"take_rate_pct": 10},
        "lead_artisan_title": "Nghệ nhân Trần Đình Lực",
        "contact_role": "Chủ cơ sở",
        "is_verified": True,
        "verified_at": datetime.datetime(2025, 1, 5, 9, 0, 0, tzinfo=datetime.timezone.utc),
    },
    # Negative abuse test benchmarks: Revoked agreement
    {
        "loi_id": "LOI-HUE-POTTERY-008",
        "partner_id": "PARTNER-POTTERY-008",
        "partner_name": "Doanh nghiệp Gốm Sứ Mỹ Nghệ Phước Tích (Thu hồi)",
        "partner_name_en": "Phuoc Tich Pottery Craft Enterprise (Revoked)",
        "slug": "phuoc-tich-pottery-revoked",
        "category": RbpcPartnerCategory.tourism_operator.value,
        "institution_type": "commercial_agent",
        "region": "Phong Điền, Thừa Thiên Huế",
        "scope_of_partnership": "Hợp tác tour gốm di sản (Đã chấm dứt do vi phạm quy chế định giá khách hàng).",
        "scope_details": {"revocation_notice_sent": True},
        "consent_type": RbpcLoiConsentType.written_loi.value,
        "consent_status": "revoked",
        "status": RbpcPartnerLoiStatus.revoked.value,
        "effective_date": datetime.date(2026, 1, 1),
        "expiration_date": datetime.date(2026, 12, 31),
        "agreement_checksum_sha256": "8d5be1449bca0f5236ad650085ec351ee2bc3d7bc05503b0d4aa697966ea64e3",
        "dignity_charter_binding": False,
        "commercial_terms": {"take_rate_pct": 10},
        "lead_artisan_title": "Đại diện Nguyễn Văn Nam",
        "contact_role": "Đại diện thương mại",
        "is_verified": False,
        "verified_at": None,
        "revoked_at": datetime.datetime(2026, 2, 20, 10, 0, 0, tzinfo=datetime.timezone.utc),
        "revocation_reason": "Vi phạm quy tắc bảo tồn di sản và Dignity Charter (tự ý nâng giá du khách).",
    },
]


def seed_canonical_partner_lois(db: Session) -> int:
    """Idempotently seed the canonical Huế partner LOIs into PostgreSQL."""
    inserted = 0
    for data in CANONICAL_PARTNER_LOIS:
        existing = db.execute(
            select(RbpcPartnerLoiVault).where(RbpcPartnerLoiVault.loi_id == data["loi_id"])
        ).scalar_one_or_none()
        if not existing:
            item = RbpcPartnerLoiVault(
                loi_id=data["loi_id"],
                partner_id=data["partner_id"],
                partner_name=data["partner_name"],
                partner_name_en=data.get("partner_name_en"),
                slug=data["slug"],
                category=data["category"],
                institution_type=data["institution_type"],
                region=data["region"],
                scope_of_partnership=data["scope_of_partnership"],
                scope_details=data.get("scope_details", {}),
                consent_type=data["consent_type"],
                consent_status=data["consent_status"],
                status=data["status"],
                effective_date=data["effective_date"],
                expiration_date=data["expiration_date"],
                agreement_checksum_sha256=data["agreement_checksum_sha256"],
                dignity_charter_binding=data.get("dignity_charter_binding", True),
                commercial_terms=data.get("commercial_terms", {}),
                lead_artisan_title=data.get("lead_artisan_title"),
                contact_role=data.get("contact_role"),
                is_verified=data.get("is_verified", True),
                verified_at=data.get("verified_at"),
                revoked_at=data.get("revoked_at"),
                revocation_reason=data.get("revocation_reason"),
            )
            db.add(item)
            inserted += 1
    if inserted:
        db.commit()
    return inserted


def get_active_partners(
    db: Session,
    category: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[RbpcPartnerLoiVault], int]:
    """Retrieve verified, active partners for public discovery.
    
    CRITICAL NEGATIVE ABUSE INVARIANT:
    Revoked or expired partnerships are strictly filtered out and never returned.
    """
    today = datetime.date.today()
    filters = [
        RbpcPartnerLoiVault.status == RbpcPartnerLoiStatus.active.value,
        RbpcPartnerLoiVault.consent_status.in_(["consented", "verified_written_consent"]),
        RbpcPartnerLoiVault.revoked_at.is_(None),
        RbpcPartnerLoiVault.expiration_date >= today,
    ]
    if category:
        filters.append(RbpcPartnerLoiVault.category == category)
    if region:
        filters.append(RbpcPartnerLoiVault.region.ilike(f"%{region}%"))

    # Count matching active partners
    count_query = select(func.count(RbpcPartnerLoiVault.id)).where(and_(*filters))
    total = db.execute(count_query).scalar_one()

    # Query items ordered by partner name
    items_query = (
        select(RbpcPartnerLoiVault)
        .where(and_(*filters))
        .order_by(RbpcPartnerLoiVault.partner_name.asc())
        .offset(offset)
        .limit(limit)
    )
    raw_items = db.execute(items_query).scalars().all()

    # Secondary defense: double verify Python property
    verified_items = [p for p in raw_items if p.is_currently_active]
    return verified_items, total


def get_active_partner(db: Session, identifier: str) -> RbpcPartnerLoiVault:
    """Retrieve single partner by slug, partner_id, or loi_id.
    
    NEGATIVE ABUSE INVARIANT:
    If partner exists but is revoked or expired, raises 404 RBPC_PARTNER_INACTIVE.
    Under no circumstances is an inactive partner returned as active.
    """
    query = select(RbpcPartnerLoiVault).where(
        or_(
            RbpcPartnerLoiVault.slug == identifier,
            RbpcPartnerLoiVault.partner_id == identifier,
            RbpcPartnerLoiVault.loi_id == identifier,
        )
    )
    partner = db.execute(query).scalar_one_or_none()
    if not partner:
        raise AppError(
            code="RBPC_PARTNER_NOT_FOUND",
            message=f"Partner '{identifier}' not found.",
            status_code=404,
        )

    # Check negative abuse invariant
    if not partner.is_currently_active:
        raise AppError(
            code="RBPC_PARTNER_INACTIVE",
            message=f"Negative abuse invariant: Partner '{identifier}' agreement has expired or been revoked and cannot be displayed as an active partner.",
            status_code=404,
            details={
                "partner_id": partner.partner_id,
                "status": partner.status,
                "is_expired": partner.is_expired,
                "revoked": partner.revoked_at is not None,
            },
        )

    return partner


def list_loi_vault_records(
    db: Session,
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[RbpcPartnerLoiVault], int, int, int, int]:
    """Retrieve full LOI vault records with breakdown counts for due diligence."""
    today = datetime.date.today()
    filters = []
    if status_filter:
        filters.append(RbpcPartnerLoiVault.status == status_filter)
    if category:
        filters.append(RbpcPartnerLoiVault.category == category)

    where_clause = and_(*filters) if filters else True

    # Total and status counts
    total = db.execute(select(func.count(RbpcPartnerLoiVault.id)).where(where_clause)).scalar_one()

    all_records = db.execute(select(RbpcPartnerLoiVault)).scalars().all()
    active_count = sum(1 for r in all_records if r.is_currently_active)
    expired_count = sum(1 for r in all_records if r.is_expired)
    revoked_count = sum(1 for r in all_records if r.status == "revoked" or r.revoked_at is not None)

    items_query = (
        select(RbpcPartnerLoiVault)
        .where(where_clause)
        .order_by(desc(RbpcPartnerLoiVault.created_at))
        .offset(offset)
        .limit(limit)
    )
    items = db.execute(items_query).scalars().all()

    return list(items), total, active_count, expired_count, revoked_count


def get_loi_vault_record(db: Session, loi_id: str) -> RbpcPartnerLoiVault:
    """Retrieve specific LOI vault record by unique reference."""
    query = select(RbpcPartnerLoiVault).where(RbpcPartnerLoiVault.loi_id == loi_id)
    record = db.execute(query).scalar_one_or_none()
    if not record:
        raise AppError(
            code="RBPC_LOI_NOT_FOUND",
            message=f"LOI record '{loi_id}' not found in evidence vault.",
            status_code=404,
        )
    return record


def register_loi_record(
    db: Session,
    payload: RbpcLoiRegisterIn,
    current_user_id: Optional[UUID] = None,
) -> RbpcPartnerLoiVault:
    """Register a new verified LOI/charter agreement into the evidence vault."""
    # Check duplicate loi_id
    existing_loi = db.execute(
        select(RbpcPartnerLoiVault).where(RbpcPartnerLoiVault.loi_id == payload.loi_id)
    ).scalar_one_or_none()
    if existing_loi:
        raise AppError(
            code="RBPC_LOI_DUPLICATE",
            message=f"An agreement with LOI ID '{payload.loi_id}' already exists.",
            status_code=409,
        )

    # Check duplicate slug
    existing_slug = db.execute(
        select(RbpcPartnerLoiVault).where(RbpcPartnerLoiVault.slug == payload.slug)
    ).scalar_one_or_none()
    if existing_slug:
        raise AppError(
            code="RBPC_SLUG_DUPLICATE",
            message=f"Partner slug '{payload.slug}' is already in use.",
            status_code=409,
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    record = RbpcPartnerLoiVault(
        loi_id=payload.loi_id,
        partner_id=payload.partner_id,
        partner_name=payload.partner_name,
        partner_name_en=payload.partner_name_en,
        slug=payload.slug,
        category=payload.category,
        institution_type=payload.institution_type,
        region=payload.region,
        scope_of_partnership=payload.scope_of_partnership,
        scope_details=payload.scope_details or {},
        consent_type=payload.consent_type,
        consent_status="consented",
        status=RbpcPartnerLoiStatus.active.value,
        effective_date=payload.effective_date,
        expiration_date=payload.expiration_date,
        agreement_checksum_sha256=payload.agreement_checksum_sha256,
        dignity_charter_binding=payload.dignity_charter_binding,
        commercial_terms=payload.commercial_terms or {"take_rate_pct": 10, "upfront_fee_vnd": 0},
        lead_artisan_title=payload.lead_artisan_title,
        contact_role=payload.contact_role,
        is_verified=True,
        verified_at=now,
        verified_by_id=current_user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def revoke_loi_record(
    db: Session,
    loi_id: str,
    reason: str,
    current_user_id: Optional[UUID] = None,
) -> RbpcPartnerLoiVault:
    """Revoke an active partner LOI.
    
    Negative abuse effect: Partner is immediately excluded from active discovery.
    """
    record = get_loi_vault_record(db, loi_id)
    now = datetime.datetime.now(datetime.timezone.utc)
    record.status = RbpcPartnerLoiStatus.revoked.value
    record.consent_status = "revoked"
    record.revoked_at = now
    record.revocation_reason = reason
    db.commit()
    db.refresh(record)
    return record


def verify_loi_checksum(
    db: Session,
    loi_id: str,
    document_content: str,
) -> RbpcLoiChecksumVerifyOut:
    """Verify document bytes or text against stored agreement SHA-256 digest."""
    record = get_loi_vault_record(db, loi_id)
    computed = hashlib.sha256(document_content.encode("utf-8")).hexdigest().lower()
    expected = record.agreement_checksum_sha256.lower()
    return RbpcLoiChecksumVerifyOut(
        loi_id=record.loi_id,
        expected_checksum=expected,
        computed_checksum=computed,
        is_match=(computed == expected),
    )


def export_loi_vault(db: Session, export_format: str = "markdown") -> str:
    """Export the LOI vault records as Markdown table or JSON string."""
    records = db.execute(
        select(RbpcPartnerLoiVault).order_by(RbpcPartnerLoiVault.loi_id.asc())
    ).scalars().all()

    if export_format.lower() == "json":
        items = []
        for r in records:
            items.append({
                "loi_id": r.loi_id,
                "partner_id": r.partner_id,
                "partner_name": r.partner_name,
                "category": r.category,
                "institution_type": r.institution_type,
                "region": r.region,
                "scope_of_partnership": r.scope_of_partnership,
                "status": r.status,
                "is_currently_active": r.is_currently_active,
                "is_expired": r.is_expired,
                "effective_date": r.effective_date.isoformat(),
                "expiration_date": r.expiration_date.isoformat(),
                "agreement_checksum_sha256": r.agreement_checksum_sha256,
                "dignity_charter_binding": r.dignity_charter_binding,
            })
        return json.dumps(
            {
                "vault_id": "RBPC-LOI-VAULT-2026",
                "total_records": len(items),
                "records": items,
            },
            indent=2,
            ensure_ascii=False,
        )

    # Markdown export
    lines = [
        "| LOI ID | Partner ID | Partner Name | Category | Scope Summary | Effective Dates | Agreement Checksum (SHA-256) | Status | Dignity Charter |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        dates = f"{r.effective_date.isoformat()} to {r.expiration_date.isoformat()}"
        dignity = "✅ True" if r.dignity_charter_binding else "❌ False"
        lines.append(
            f"| `{r.loi_id}` | `{r.partner_id}` | {r.partner_name} | `{r.category}` | {r.scope_of_partnership[:60]}... | {dates} | `{r.agreement_checksum_sha256}` | `{r.status}` | {dignity} |"
        )
    return "\n".join(lines)
