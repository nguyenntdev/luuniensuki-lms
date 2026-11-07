# -*- coding: utf-8 -*-
"""V5-T113: Partner Discovery and LOI Vault Test Suite.

Wave W11, Slot A03:
- Secure partner evidence register with consent, expiration dates, scope, and agreement checksums (not raw signatures in public repo).
- Negative abuse invariant: Revoked or expired partnerships are never displayed as active partners.
- Fail-closed direct lookup returning 404 (RBPC_PARTNER_INACTIVE) for revoked or expired partners.
- Cryptographic SHA-256 agreement verification without personal PII or raw biometric scans.
- RBAC role enforcement (Admin/Staff required for register and revoke mutations).
- Documentation parity with docs/rbpc/PARTNER_DISCOVERY_LOI_VAULT.md.
"""
from __future__ import annotations

import datetime
import hashlib
from pathlib import Path
import uuid
import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.partner_loi_models import (
    RbpcLoiConsentType,
    RbpcPartnerCategory,
    RbpcPartnerLoiStatus,
    RbpcPartnerLoiVault,
)
from backend.security import hash_password
from backend.services.partner_loi import (
    CANONICAL_PARTNER_LOIS,
    seed_canonical_partner_lois,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def test_v5_t113_canonical_register_integrity(client, db_session):
    """Gate 1: Verify canonical partner LOI registry integrity, non-PII checksums, and fields."""
    seed_canonical_partner_lois(db_session)
    records = db_session.execute(select(RbpcPartnerLoiVault)).scalars().all()
    assert len(records) >= 8, f"Expected at least 8 canonical records, found {len(records)}"

    for r in records:
        assert r.loi_id.startswith("LOI-HUE-")
        assert r.partner_id.startswith("PARTNER-")
        assert len(r.partner_name) > 0
        assert r.scope_of_partnership
        assert r.effective_date
        assert r.expiration_date
        assert r.agreement_checksum_sha256
        assert len(r.agreement_checksum_sha256) == 64
        assert all(c in "0123456789abcdef" for c in r.agreement_checksum_sha256)
        # Anti-PII & Raw Signature Prohibition
        assert "data:image" not in r.agreement_checksum_sha256
        assert "http://" not in r.agreement_checksum_sha256
        assert "https://" not in r.agreement_checksum_sha256


def test_v5_t113_public_partner_discovery_active_only(client, db_session):
    """Gate 2: Public endpoint GET /api/v1/rbpc/partners returns strictly active partners."""
    seed_canonical_partner_lois(db_session)

    res = client.get("/api/v1/rbpc/partners")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 6

    partner_ids = [item["partner_id"] for item in data["items"]]
    loi_ids = [item["loi_id"] for item in data["items"]]

    # Active canonical partners must be present
    assert "PARTNER-BRONZE-001" in partner_ids
    assert "PARTNER-PHAPLAM-002" in partner_ids
    assert "PARTNER-TRUCCHI-003" in partner_ids
    assert "PARTNER-EMBROID-004" in partner_ids
    assert "PARTNER-QUOCHOC-005" in partner_ids
    assert "PARTNER-HMCC-006" in partner_ids

    # NEGATIVE ABUSE INVARIANT: Expired and revoked partners MUST NOT be present
    assert "PARTNER-WOOD-007" not in partner_ids
    assert "LOI-HUE-WOOD-007" not in loi_ids
    assert "PARTNER-POTTERY-008" not in partner_ids
    assert "LOI-HUE-POTTERY-008" not in loi_ids

    for item in data["items"]:
        assert item["is_active"] is True
        exp_date = datetime.date.fromisoformat(item["expiration_date"])
        assert exp_date >= datetime.date.today()


def test_v5_t113_negative_abuse_expired_partner_excluded(client, db_session):
    """Gate 3: Expired partnerships are never displayed as active partners.
    
    1. Excluded from active partner list.
    2. Direct lookup returns HTTP 404 with RBPC_PARTNER_INACTIVE.
    """
    seed_canonical_partner_lois(db_session)

    # 1. Check list exclusion
    res = client.get("/api/v1/rbpc/partners?category=craft_guild")
    assert res.status_code == 200
    items = res.json()["items"]
    assert all(i["partner_id"] != "PARTNER-WOOD-007" for i in items)
    assert all(i["slug"] != "huong-thuy-wood-expired" for i in items)

    # 2. Check direct lookup failure
    res_direct = client.get("/api/v1/rbpc/partners/huong-thuy-wood-expired")
    assert res_direct.status_code == 404
    err = res_direct.json()["error"]
    assert err["code"] == "RBPC_PARTNER_INACTIVE"
    assert "expired" in err["message"].lower()

    # 3. Create a dynamic partner that expired yesterday and verify immediate exclusion
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    two_weeks_ago = datetime.date.today() - datetime.timedelta(days=14)
    expired_dynamic = RbpcPartnerLoiVault(
        loi_id="LOI-TEST-EXPIRED-999",
        partner_id="PARTNER-TEST-999",
        partner_name="Xưởng Chạm Khắc Thử Nghiệm Hết Hạn",
        slug="xuong-cham-khac-expired-999",
        category=RbpcPartnerCategory.craft_guild.value,
        institution_type="artisan_studio",
        region="Huế",
        scope_of_partnership="Thử nghiệm kiểm tra hết hạn thỏa thuận.",
        consent_type=RbpcLoiConsentType.written_loi.value,
        consent_status="consented",
        status=RbpcPartnerLoiStatus.active.value,  # status is active, but date is expired!
        effective_date=two_weeks_ago,
        expiration_date=yesterday,
        agreement_checksum_sha256="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        dignity_charter_binding=True,
    )
    db_session.add(expired_dynamic)
    db_session.commit()

    # Dynamic expired partner must be excluded from active discovery
    res_dyn_list = client.get("/api/v1/rbpc/partners")
    assert res_dyn_list.status_code == 200
    dyn_ids = [i["partner_id"] for i in res_dyn_list.json()["items"]]
    assert "PARTNER-TEST-999" not in dyn_ids

    # Direct lookup fails closed
    res_dyn_get = client.get("/api/v1/rbpc/partners/xuong-cham-khac-expired-999")
    assert res_dyn_get.status_code == 404
    assert res_dyn_get.json()["error"]["code"] == "RBPC_PARTNER_INACTIVE"


def test_v5_t113_negative_abuse_revoked_partner_excluded(client, db_session):
    """Gate 4: Revoked partnerships are never displayed as active partners.
    
    1. Excluded from active partner list.
    2. Direct lookup returns HTTP 404 with RBPC_PARTNER_INACTIVE.
    """
    seed_canonical_partner_lois(db_session)

    # 1. Check list exclusion
    res = client.get("/api/v1/rbpc/partners")
    assert res.status_code == 200
    items = res.json()["items"]
    assert all(i["partner_id"] != "PARTNER-POTTERY-008" for i in items)
    assert all(i["slug"] != "phuoc-tich-pottery-revoked" for i in items)

    # 2. Check direct lookup failure
    res_direct = client.get("/api/v1/rbpc/partners/phuoc-tich-pottery-revoked")
    assert res_direct.status_code == 404
    err = res_direct.json()["error"]
    assert err["code"] == "RBPC_PARTNER_INACTIVE"
    assert "revoked" in err["message"].lower()


def test_v5_t113_revocation_lifecycle_and_immediate_exclusion(client, db_session):
    """Gate 5: Revoking an active partner immediately excludes them from active discovery."""
    seed_canonical_partner_lois(db_session)

    # Admin user
    admin_user = _create_user(
        db_session, f"admin_loi_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin
    )
    _login_user(client, admin_user.email)

    # Before revocation: Bronze casting partner is active
    res_before = client.get("/api/v1/rbpc/partners/phuong-duc-bronze-casting")
    assert res_before.status_code == 200
    assert res_before.json()["partner_id"] == "PARTNER-BRONZE-001"

    # Revoke agreement
    revoke_payload = {
        "reason": "Artisan cooperative requested pause due to workshop renovation and relocation."
    }
    res_revoke = client.post(
        "/api/v1/rbpc/admin/loi-vault/LOI-HUE-BRONZE-001/revoke",
        json=revoke_payload,
    )
    assert res_revoke.status_code == 200, res_revoke.text
    vault_item = res_revoke.json()
    assert vault_item["status"] == "revoked"
    assert vault_item["consent_status"] == "revoked"
    assert vault_item["revoked_at"] is not None
    assert vault_item["revocation_reason"] == revoke_payload["reason"]

    # IMMEDIATELY AFTER REVOCATION: Partner is dropped from active discovery
    res_list_after = client.get("/api/v1/rbpc/partners")
    assert res_list_after.status_code == 200
    partner_ids = [i["partner_id"] for i in res_list_after.json()["items"]]
    assert "PARTNER-BRONZE-001" not in partner_ids

    # Direct lookup immediately returns 404 RBPC_PARTNER_INACTIVE
    res_get_after = client.get("/api/v1/rbpc/partners/phuong-duc-bronze-casting")
    assert res_get_after.status_code == 404
    err = res_get_after.json()["error"]
    assert err["code"] == "RBPC_PARTNER_INACTIVE"


def test_v5_t113_checksum_verification_and_anti_pii_guards(client, db_session):
    """Gate 6: Cryptographic checksum verification and model-level anti-PII defense."""
    seed_canonical_partner_lois(db_session)

    admin_user = _create_user(
        db_session, f"admin_chk_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin
    )
    _login_user(client, admin_user.email)

    # 1. Matching document checksum verification
    document_text = "HỢP TÁC XÃ ĐÚC ĐỒNG PHƯỜNG ĐÚC HUẾ - THỎA THUẬN HỢP TÁC BẢO TỒN CỬU ĐỈNH 2026"
    test_sha = hashlib.sha256(document_text.encode("utf-8")).hexdigest()

    # Update LOI-HUE-PHAPLAM-002 checksum to test_sha
    phaplam = db_session.execute(
        select(RbpcPartnerLoiVault).where(RbpcPartnerLoiVault.loi_id == "LOI-HUE-PHAPLAM-002")
    ).scalar_one()
    phaplam.agreement_checksum_sha256 = test_sha
    db_session.commit()

    # Check match
    res_match = client.post(
        "/api/v1/rbpc/admin/loi-vault/LOI-HUE-PHAPLAM-002/verify-checksum",
        json={"document_content": document_text},
    )
    assert res_match.status_code == 200
    data_match = res_match.json()
    assert data_match["is_match"] is True
    assert data_match["computed_checksum"] == test_sha

    # Check mismatch
    res_mismatch = client.post(
        "/api/v1/rbpc/admin/loi-vault/LOI-HUE-PHAPLAM-002/verify-checksum",
        json={"document_content": "VĂN BẢN ĐÃ BỊ SỬA ĐỔI NỘI DUNG"},
    )
    assert res_mismatch.status_code == 200
    data_mismatch = res_mismatch.json()
    assert data_mismatch["is_match"] is False
    assert data_mismatch["computed_checksum"] != test_sha

    # 2. Model-level Anti-PII & Checksum Validation
    with pytest.raises(ValueError, match="agreement_checksum_sha256 must be a valid 64-character"):
        RbpcPartnerLoiVault(
            loi_id="LOI-INVALID-HASH",
            partner_id="PARTNER-BAD-1",
            partner_name="Invalid Partner",
            slug="invalid-slug",
            category="craft_guild",
            institution_type="guild",
            scope_of_partnership="Invalid scope test",
            effective_date=datetime.date.today(),
            expiration_date=datetime.date.today() + datetime.timedelta(days=365),
            agreement_checksum_sha256="not_a_valid_64_char_hex",
        )

    # 3. Model-level Raw Signature / Data URI Prohibition
    with pytest.raises(ValueError, match="Raw signatures"):
        # Even if padded to 64 chars, data URI/URL substrings must fail closed
        bad_sig = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9h"[:64]
        RbpcPartnerLoiVault(
            loi_id="LOI-RAW-SIGNATURE-BLOCKED",
            partner_id="PARTNER-BAD-2",
            partner_name="Raw Signature Partner",
            slug="raw-sig-partner",
            category="craft_guild",
            institution_type="guild",
            scope_of_partnership="Invalid raw signature test",
            effective_date=datetime.date.today(),
            expiration_date=datetime.date.today() + datetime.timedelta(days=365),
            agreement_checksum_sha256=bad_sig,
        )


def test_v5_t113_admin_role_enforcement_and_scope_security(client, db_session):
    """Gate 7: Learner/guest users cannot register or revoke LOI agreements (HTTP 403/401)."""
    seed_canonical_partner_lois(db_session)

    # Regular learner user
    learner_user = _create_user(
        db_session, f"learner_loi_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner
    )
    _login_user(client, learner_user.email)

    register_payload = {
        "loi_id": "LOI-HACK-001",
        "partner_id": "PARTNER-HACK-001",
        "partner_name": "Unauthorized Craft Partner",
        "slug": "unauthorized-partner",
        "category": "craft_guild",
        "institution_type": "guild",
        "region": "Huế",
        "scope_of_partnership": "Thỏa thuận giả mạo không được phê duyệt bởi Staff/Admin.",
        "effective_date": "2026-01-01",
        "expiration_date": "2027-01-01",
        "agreement_checksum_sha256": "abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    }

    # 1. Learner cannot register LOI
    res_reg = client.post("/api/v1/rbpc/admin/loi-vault", json=register_payload)
    assert res_reg.status_code == 403, res_reg.text

    # 2. Learner cannot revoke LOI
    res_rev = client.post(
        "/api/v1/rbpc/admin/loi-vault/LOI-HUE-TRUCCHI-003/revoke",
        json={"reason": "Unauthorized attempt to revoke"},
    )
    assert res_rev.status_code == 403, res_rev.text

    # 3. Staff user CAN register and view LOI
    staff_user = _create_user(
        db_session, f"staff_loi_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin
    )
    _login_user(client, staff_user.email)

    res_staff_reg = client.post("/api/v1/rbpc/admin/loi-vault", json=register_payload)
    assert res_staff_reg.status_code == 201, res_staff_reg.text
    assert res_staff_reg.json()["loi_id"] == "LOI-HACK-001"


def test_v5_t113_vault_listing_and_counts(client, db_session):
    """Gate 8: Vault endpoint GET /api/v1/rbpc/loi-vault lists records with accurate counts."""
    seed_canonical_partner_lois(db_session)

    res = client.get("/api/v1/rbpc/loi-vault")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total"] >= 8
    assert data["active_count"] >= 6
    assert data["expired_count"] >= 1
    assert data["revoked_count"] >= 1

    # Check detail lookup
    res_item = client.get("/api/v1/rbpc/loi-vault/LOI-HUE-TRUCCHI-003")
    assert res_item.status_code == 200
    item = res_item.json()
    assert item["loi_id"] == "LOI-HUE-TRUCCHI-003"
    assert item["partner_name"] == "Nghệ thuật Trúc Chỉ Việt Nam - Không gian Huế"
    assert item["category"] == "cultural_association"
    assert item["agreement_checksum_sha256"] == "a1bc40285a214d4e3cb481e370e515d6ad05e04cb212e105a5a7dc64ecb90e9e"
    assert item["dignity_charter_binding"] is True
    assert item["is_currently_active"] is True
    assert item["is_expired"] is False


def test_v5_t113_documentation_and_export_parity(client, db_session):
    """Gate 9: Export facilities match docs/rbpc/PARTNER_DISCOVERY_LOI_VAULT.md."""
    seed_canonical_partner_lois(db_session)

    doc_path = REPO_ROOT / "docs" / "rbpc" / "PARTNER_DISCOVERY_LOI_VAULT.md"
    assert doc_path.exists(), f"Missing documentation file at {doc_path}"
    doc_content = doc_path.read_text(encoding="utf-8")

    # Verify all canonical LOI IDs and checksums are documented in markdown
    for canonical in CANONICAL_PARTNER_LOIS:
        assert canonical["loi_id"] in doc_content
        assert canonical["partner_id"] in doc_content
        assert canonical["agreement_checksum_sha256"] in doc_content

    # Staff export
    staff_user = _create_user(
        db_session, f"staff_export_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin
    )
    _login_user(client, staff_user.email)

    # 1. JSON Export
    res_json = client.get("/api/v1/rbpc/admin/loi-vault/export?format=json")
    assert res_json.status_code == 200
    export_json = res_json.json()
    assert export_json["format"] == "json"
    assert export_json["total_records"] >= 8
    assert "records" in export_json["content"]

    # 2. Markdown Export
    res_md = client.get("/api/v1/rbpc/admin/loi-vault/export?format=markdown")
    assert res_md.status_code == 200
    export_md = res_md.json()
    assert export_md["format"] == "markdown"
    assert "| LOI ID | Partner ID |" in export_md["content"]
    assert "LOI-HUE-BRONZE-001" in export_md["content"]
