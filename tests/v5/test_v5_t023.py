# -*- coding: utf-8 -*-
"""V5-T023 (Wave W02, Slot A03): Bibliographic source registry test suite.

Audits and verifies:
1. Bibliographic source registry model & fields:
   - Verifies HistoricalSource registry fields: edition, license, locator/pages,
     checksum/hash, excerpt, rights_status, verification_status, citation_text.
   - Verifies HistoricalClaimSource locators and quotation excerpts.
2. Public vs Private field separation:
   - Public queries (GET /api/v1/history/sources, GET /api/v1/history/sources/{id})
     strictly omit internal private fields (created_by, content_scope).
   - Staff/Admin endpoint (GET /api/v1/admin/history/sources/{id}) exposes
     audit/provenance fields (created_by, content_scope, raw_excerpt).
3. Negative abuse test (Rights Restriction Enforcement):
   - Unlicensed, copyrighted, or rights_restricted excerpts are completely
     inaccessible to the public/anonymous API.
   - Raw restricted text is strictly redacted from public responses ([REDACTED: RIGHTS_RESTRICTED]).
   - Metadata citation (title, author, publisher, pages, support_type, license,
     rights_status) remains fully preserved and intact.
   - Privileged staff users retain authenticated access to raw excerpts for fact-checking.
4. Open/Public Domain excerpt access:
   - Sources with public_domain / CC0 rights and public_display_allowed=True permit
     excerpt display to public anonymous queries.
5. Deduplication of bibliographic sources:
   - Strict deduplication by normalized ISBN (hyphenated vs unhyphenated).
   - Strict deduplication by normalized DOI (URL resolver vs bare DOI identifier).
   - Strict deduplication by normalized Title + Author text (case/accent normalization).
   - Dedicated pre-flight check endpoint (GET /api/v1/history/sources/check-duplicate).
   - Duplicate creation rejection with HTTP 409 Conflict (HISTORICAL_SOURCE_DUPLICATE).
   - Staff bypass parameter (?check_duplicate=false) for intentional separate editions.
6. Deterministic checksum computation & verification:
   - Canonical SHA-256 metadata hash computation and persistence.
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
    HistoricalSourceVerificationStatus,
)
from backend.main import app
from backend.models import User, UserRole
from backend.services import history_governance as gov


# ==============================================================================
# Helpers
# ==============================================================================

def _create_staff_user(client: TestClient, db_session, email_prefix: str = "staff") -> tuple[User, str]:
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    password = "StaffSecurePassword123!"
    display_name = f"Staff {email_prefix.title()}"
    
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert res.status_code == 201, res.text

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.admin
    db_session.commit()
    db_session.refresh(user)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, login_res.text
    return user, password


def _create_test_entity(db_session, **overrides) -> HistoricalEntity:
    slug = f"entity-{uuid.uuid4().hex[:8]}"
    data = {
        "entity_type": "relief",
        "slug": slug,
        "name_vi": f"Thực Thể {slug}",
        "name_en": f"Entity {slug}",
        "publication_status": "published",
    }
    data.update(overrides)
    entity = HistoricalEntity(**data)
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity


# ==============================================================================
# 1. Source Registry Fields Verification
# ==============================================================================

def test_source_registry_fields_and_persistence(client: TestClient, db_session):
    """Verify source registry fields: edition, license, locator/pages, checksum, excerpt."""
    user, _ = _create_staff_user(client, db_session, "registry_fields")
    
    unique_isbn = f"978-604-0-{uuid.uuid4().hex[:5]}"
    unique_doi = f"10.1000/cuudinh.{uuid.uuid4().hex[:8]}"
    custom_checksum = f"sha256:{uuid.uuid4().hex}"
    
    payload = {
        "source_type": "scholarly_book",
        "title": "Nghiên Cứu Chi Tiết Cửu Đỉnh Huế",
        "subtitle": "Khảo Luận Về Nghệ Thuật Đúc Đồng Thế Kỷ XIX",
        "author_text": "Hội Đồng Khảo Cổ Hoàng Gia",
        "publisher": "NXB Thuận Hóa",
        "publication_year": 2020,
        "edition": "Tái bản lần thứ 2 có sửa chữa",
        "volume": "Tập 1",
        "issue": "Số 4",
        "pages": "tr. 45-89",
        "isbn": unique_isbn,
        "doi": unique_doi,
        "license": "CC-BY-4.0",
        "rights_status": "open_access",
        "public_display_allowed": True,
        "derivative_allowed": True,
        "verification_status": "metadata_verified",
        "citation_text": "Hội Đồng Khảo Cổ Hoàng Gia (2020), Nghiên Cứu Chi Tiết Cửu Đỉnh Huế, NXB Thuận Hóa.",
        "checksum": custom_checksum,
        "excerpt": "Cửu Đỉnh biểu trưng cho sự trường tồn và thống nhất lãnh thổ của triều đình.",
    }

    res = client.post("/api/v1/admin/history/sources", json=payload)
    assert res.status_code == 200, res.text
    created = res.json()
    source_id = created["id"]

    # Verify response matches sent registry fields
    assert created["edition"] == "Tái bản lần thứ 2 có sửa chữa"
    assert created["license"] == "CC-BY-4.0"
    assert created["pages"] == "tr. 45-89"
    assert created["checksum"] == custom_checksum
    assert created["excerpt"] == payload["excerpt"]
    assert created["isbn"] == gov.normalize_isbn(unique_isbn)
    assert created["doi"] == gov.normalize_doi(unique_doi)

    # Verify directly in DB model
    db_source = db_session.get(HistoricalSource, uuid.UUID(source_id))
    assert db_source is not None
    assert db_source.edition == "Tái bản lần thứ 2 có sửa chữa"
    assert db_source.license == "CC-BY-4.0"
    assert db_source.pages == "tr. 45-89"
    assert db_source.checksum == custom_checksum
    assert db_source.excerpt == payload["excerpt"]
    assert db_source.created_by == user.id


# ==============================================================================
# 2. Public vs Private Field Separation
# ==============================================================================

def test_public_vs_private_field_separation(client: TestClient, db_session):
    """Test public vs private field separation in bibliographic source queries."""
    user, _ = _create_staff_user(client, db_session, "priv_separation")

    # Create source with private provenance metadata
    payload = {
        "source_type": "archival_record",
        "title": "Châu Bản Triều Nguyễn - Tập Chiếu Chỉ Năm Minh Mạng 17",
        "author_text": "Nội Các Triều Nguyễn",
        "publication_year": 1836,
        "edition": "Chính bản lưu trữ",
        "pages": "Tờ 12-15",
        "rights_status": "public_domain",
        "public_display_allowed": True,
        "verification_status": "metadata_verified",
    }
    create_res = client.post("/api/v1/admin/history/sources", json=payload)
    assert create_res.status_code == 200, create_res.text
    source_id = create_res.json()["id"]

    # Ensure internal DB record has created_by
    db_source = db_session.get(HistoricalSource, uuid.UUID(source_id))
    assert db_source.created_by == user.id
    db_source.content_scope = "heritage_internal_confidential"
    db_session.commit()

    # 1. Anonymous public query on GET /api/v1/history/sources/{source_id}
    anon_client = TestClient(app)
    pub_res = anon_client.get(f"/api/v1/history/sources/{source_id}")
    assert pub_res.status_code == 200, pub_res.text
    pub_data = pub_res.json()

    # Public response MUST NOT expose created_by or content_scope
    assert "created_by" not in pub_data, "Public endpoint must not leak created_by user ID"
    assert "content_scope" not in pub_data, "Public endpoint must not leak internal content_scope"
    assert pub_data["title"] == payload["title"]
    assert pub_data["edition"] == payload["edition"]

    # 2. Anonymous public list on GET /api/v1/history/sources
    list_res = anon_client.get("/api/v1/history/sources", params={"search": "Châu Bản Triều Nguyễn"})
    assert list_res.status_code == 200, list_res.text
    list_items = list_res.json()["items"]
    assert len(list_items) >= 1
    target = next((item for item in list_items if item["id"] == source_id), None)
    assert target is not None
    assert "created_by" not in target, "Public list must not leak created_by"
    assert "content_scope" not in target, "Public list must not leak content_scope"

    # 3. Staff admin query on GET /api/v1/admin/history/sources/{source_id}
    # Authenticated staff user using 'client'
    admin_res = client.get(f"/api/v1/admin/history/sources/{source_id}")
    assert admin_res.status_code == 200, admin_res.text
    admin_data = admin_res.json()

    # Admin response MUST expose private audit fields
    assert "created_by" in admin_data
    assert admin_data["created_by"] == str(user.id)
    assert admin_data["content_scope"] == "heritage_internal_confidential"


# ==============================================================================
# 3. Negative Abuse Test: Rights Restriction Enforcement
# ==============================================================================

def test_negative_abuse_unlicensed_restricted_excerpt_inaccessible_to_public(client: TestClient, db_session):
    """Negative abuse test: Unlicensed/restricted excerpt is inaccessible to public API (redacted/omitted)."""
    staff_user, _ = _create_staff_user(client, db_session, "rights_enforce")
    entity = _create_test_entity(db_session)

    secret_raw_excerpt = "CONFIDENTIAL_COPYRIGHTED_PASSAGE_DO_NOT_DISCLOSE_1985"
    secret_claim_quotation = "SECRET_UNLICENSED_QUOTATION_EXCERPT_HERITAGE_RESTRICTED"

    # 1. Create a rights-restricted source (copyrighted, unlicensed, public_display_allowed=False)
    source_payload = {
        "source_type": "scholarly_book",
        "title": "Tuyển Tập Chuyên Khảo Cửu Đỉnh (Bản Dịch Giới Hạn)",
        "author_text": "Nhà Nghiên Cứu Bí Danh",
        "publisher": "NXB Bản Quyền Độc Quyền",
        "publication_year": 1985,
        "edition": "Ấn bản hạn chế 50 bản",
        "pages": "tr. 101-105",
        "rights_status": "copyrighted",
        "license": "All Rights Reserved",
        "public_display_allowed": False,
        "verification_status": "rights_restricted",
        "citation_text": "Nhà Nghiên Cứu Bí Danh (1985), Tuyển Tập Chuyên Khảo Cửu Đỉnh, tr. 101-105.",
        "excerpt": secret_raw_excerpt,
    }
    src_res = client.post("/api/v1/admin/history/sources", json=source_payload)
    assert src_res.status_code == 200, src_res.text
    source_id = src_res.json()["id"]

    # 2. Create a claim and attach the restricted source with quotation_excerpt
    claim_payload = {
        "entity_id": str(entity.id),
        "claim_type": "factual",
        "statement_vi": "Chi tiết hoa văn trên Huyền Đỉnh phản ánh kỹ thuật đúc hợp kim đặc thù.",
        "confidence": "high",
        "verification_status": "unreviewed",
        "origin": "editorial",
    }
    claim_res = client.post("/api/v1/admin/history/claims", json=claim_payload)
    assert claim_res.status_code == 200, claim_res.text
    claim_id = claim_res.json()["id"]

    bind_payload = {
        "source_id": source_id,
        "support_type": "supports",
        "locator_type": "pages",
        "page_start": "102",
        "page_end": "103",
        "chapter": "Chương 4",
        "quotation_excerpt": secret_claim_quotation,
        "editor_note": "Ghi chú biên tập nội bộ: Đoạn trích bản quyền chưa được cấp phép công khai.",
    }
    bind_res = client.post(f"/api/v1/admin/history/claims/{claim_id}/sources", json=bind_payload)
    assert bind_res.status_code == 200, bind_res.text

    # --------------------------------------------------------------------------
    # Abuse verification: Unauthenticated anonymous public client attempts access
    # --------------------------------------------------------------------------
    anon_client = TestClient(app)

    # Abuse Check A: Public lookup of source by ID
    pub_src_res = anon_client.get(f"/api/v1/history/sources/{source_id}")
    assert pub_src_res.status_code == 200, pub_src_res.text
    
    # 1. The raw secret excerpt MUST NOT appear anywhere in the HTTP response text
    assert secret_raw_excerpt not in pub_src_res.text, (
        "CRITICAL LEAK: Unlicensed excerpt found in public source lookup HTTP response text"
    )
    # 2. Excerpt field is redacted/omitted
    pub_src_data = pub_src_res.json()
    assert pub_src_data["excerpt"] == gov.REDACTED_EXCERPT_TEXT
    # 3. Metadata citation MUST be preserved
    assert pub_src_data["title"] == source_payload["title"]
    assert pub_src_data["author_text"] == source_payload["author_text"]
    assert pub_src_data["citation_text"] == source_payload["citation_text"]
    assert pub_src_data["rights_status"] == "copyrighted"
    assert pub_src_data["license"] == "All Rights Reserved"

    # Abuse Check B: Public list of sources
    pub_list_res = anon_client.get("/api/v1/history/sources", params={"search": "Tuyển Tập Chuyên Khảo"})
    assert pub_list_res.status_code == 200, pub_list_res.text
    assert secret_raw_excerpt not in pub_list_res.text, (
        "CRITICAL LEAK: Unlicensed excerpt found in public sources list HTTP response text"
    )
    matching_item = next((item for item in pub_list_res.json()["items"] if item["id"] == source_id), None)
    assert matching_item is not None
    assert matching_item["excerpt"] == gov.REDACTED_EXCERPT_TEXT

    # Abuse Check C: Public claim-sources lookup
    pub_claim_src_res = anon_client.get(f"/api/v1/history/claims/{claim_id}/sources")
    assert pub_claim_src_res.status_code == 200, pub_claim_src_res.text
    assert secret_claim_quotation not in pub_claim_src_res.text, (
        "CRITICAL LEAK: Unlicensed claim quotation excerpt found in public claim-sources HTTP response text"
    )
    claim_src_bindings = pub_claim_src_res.json()
    assert len(claim_src_bindings) == 1
    binding_out = claim_src_bindings[0]
    assert binding_out["quotation_excerpt"] == gov.REDACTED_EXCERPT_TEXT
    # Preserves metadata locator fields
    assert binding_out["support_type"] == "supports"
    assert binding_out["page_start"] == "102"
    assert binding_out["page_end"] == "103"
    assert binding_out["chapter"] == "Chương 4"
    assert binding_out["source_id"] == source_id

    # --------------------------------------------------------------------------
    # Privileged check: Authenticated staff user CAN view raw excerpts
    # --------------------------------------------------------------------------
    # Staff lookup of claim sources
    staff_claim_src_res = client.get(f"/api/v1/history/claims/{claim_id}/sources")
    assert staff_claim_src_res.status_code == 200
    assert staff_claim_src_res.json()[0]["quotation_excerpt"] == secret_claim_quotation

    # Staff lookup of admin source detail
    staff_admin_src_res = client.get(f"/api/v1/admin/history/sources/{source_id}")
    assert staff_admin_src_res.status_code == 200
    assert staff_admin_src_res.json()["raw_excerpt"] == secret_raw_excerpt


def test_public_open_licensed_excerpt_accessible_to_public(client: TestClient, db_session):
    """Positive test: Public domain or CC0 excerpt is unredacted for public users."""
    _create_staff_user(client, db_session, "open_access")
    entity = _create_test_entity(db_session)

    open_excerpt = "Văn bản khắc minh văn trên Cao Đỉnh hoàn toàn thuộc phạm vi công cộng."

    # 1. Create open source
    source_payload = {
        "source_type": "inscription",
        "title": "Minh Văn Trên Cao Đỉnh Triều Nguyễn",
        "publication_year": 1836,
        "rights_status": "public_domain",
        "license": "CC0-1.0",
        "public_display_allowed": True,
        "verification_status": "accessible",
        "citation_text": "Minh Văn Cao Đỉnh (1836), Cửu Đỉnh Đại Nội Huế.",
        "excerpt": open_excerpt,
    }
    src_res = client.post("/api/v1/admin/history/sources", json=source_payload)
    assert src_res.status_code == 200
    source_id = src_res.json()["id"]

    # 2. Attach to claim
    claim_payload = {
        "entity_id": str(entity.id),
        "claim_type": "factual",
        "statement_vi": "Minh văn khắc chữ Hán cổ trên bề mặt Cao Đỉnh.",
        "confidence": "high",
        "verification_status": "unreviewed",
        "origin": "editorial",
    }
    claim_res = client.post("/api/v1/admin/history/claims", json=claim_payload)
    claim_id = claim_res.json()["id"]

    bind_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/sources",
        json={"source_id": source_id, "support_type": "supports", "quotation_excerpt": open_excerpt},
    )
    assert bind_res.status_code == 200

    # 3. Anonymous public check
    anon_client = TestClient(app)
    pub_res = anon_client.get(f"/api/v1/history/sources/{source_id}")
    assert pub_res.status_code == 200
    assert pub_res.json()["excerpt"] == open_excerpt

    pub_claim_src_res = anon_client.get(f"/api/v1/history/claims/{claim_id}/sources")
    assert pub_claim_src_res.status_code == 200
    assert pub_claim_src_res.json()[0]["quotation_excerpt"] == open_excerpt


# ==============================================================================
# 4. Deduplication of Bibliographic Sources Tests
# ==============================================================================

def test_deduplication_by_isbn(client: TestClient, db_session):
    """Test deduplication of bibliographic sources by normalized ISBN."""
    _create_staff_user(client, db_session, "dedup_isbn")

    canonical_isbn = "978-604-0-99999-1"
    clean_isbn = "9786040999991"

    # 1. Register canonical source with hyphenated ISBN
    res1 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "scholarly_book",
            "title": "Mỹ Thuật Huế Thời Nguyễn",
            "author_text": "Chu Quang Trứ",
            "publication_year": 2000,
            "isbn": canonical_isbn,
        },
    )
    assert res1.status_code == 200, res1.text
    source_id = res1.json()["id"]

    # 2. Pre-flight duplicate check with unhyphenated ISBN
    anon_client = TestClient(app)
    check_res = anon_client.get(
        "/api/v1/history/sources/check-duplicate",
        params={"isbn": clean_isbn},
    )
    assert check_res.status_code == 200, check_res.text
    check_data = check_res.json()
    assert check_data["is_duplicate"] is True
    assert check_data["matched_by"] == "isbn"
    assert check_data["duplicate_source"]["id"] == source_id

    # 3. Attempt to register duplicate source with unhyphenated ISBN
    res2 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "reference_work",
            "title": "Mỹ Thuật Huế (Bản In Lại)",
            "author_text": "Chu Quang Trứ",
            "isbn": clean_isbn,
        },
    )
    assert res2.status_code == 409, "Duplicate ISBN registration must return 409 Conflict"
    err = res2.json()
    assert err["error"]["code"] == "HISTORICAL_SOURCE_DUPLICATE"
    assert err["error"]["details"]["matched_by"] == "isbn"
    assert err["error"]["details"]["duplicate_id"] == source_id


def test_deduplication_by_doi(client: TestClient, db_session):
    """Test deduplication of bibliographic sources by normalized DOI."""
    _create_staff_user(client, db_session, "dedup_doi")

    bare_doi = f"10.1007/s00123-020-{uuid.uuid4().hex[:6]}"
    resolver_doi = f"https://doi.org/{bare_doi}"

    # 1. Register source with bare DOI
    res1 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "peer_reviewed_article",
            "title": "Metallurgical Analysis of Nineteenth-Century Hue Bronze Urns",
            "author_text": "Tran Dinh et al.",
            "publication_year": 2021,
            "doi": bare_doi,
        },
    )
    assert res1.status_code == 200, res1.text
    source_id = res1.json()["id"]

    # 2. Pre-flight duplicate check with URL resolver DOI format
    anon_client = TestClient(app)
    check_res = anon_client.get(
        "/api/v1/history/sources/check-duplicate",
        params={"doi": resolver_doi},
    )
    assert check_res.status_code == 200, check_res.text
    check_data = check_res.json()
    assert check_data["is_duplicate"] is True
    assert check_data["matched_by"] == "doi"
    assert check_data["duplicate_source"]["id"] == source_id

    # 3. Attempt to register duplicate source with URL resolver DOI
    res2 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "peer_reviewed_article",
            "title": "Metallurgical Analysis of Hue Urns (Preprint)",
            "doi": resolver_doi,
        },
    )
    assert res2.status_code == 409, "Duplicate DOI registration must return 409 Conflict"
    err = res2.json()
    assert err["error"]["code"] == "HISTORICAL_SOURCE_DUPLICATE"
    assert err["error"]["details"]["matched_by"] == "doi"
    assert err["error"]["details"]["duplicate_id"] == source_id


def test_deduplication_by_title_and_author(client: TestClient, db_session):
    """Test deduplication of bibliographic sources by normalized Title + Author text."""
    _create_staff_user(client, db_session, "dedup_title_author")

    canonical_title = "Đại Nam Nhất Thống Chí"
    canonical_author = "Quốc Sử Quán Triều Nguyễn"

    # 1. Register canonical source
    res1 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "royal_record",
            "title": canonical_title,
            "author_text": canonical_author,
            "publication_year": 1882,
        },
    )
    assert res1.status_code == 200, res1.text
    source_id = res1.json()["id"]

    # 2. Pre-flight check with lowercase, unaccented, and extra whitespace variant
    anon_client = TestClient(app)
    check_res = anon_client.get(
        "/api/v1/history/sources/check-duplicate",
        params={
            "title": "  dai  nam   nhat thong chi  ",
            "author_text": "quoc su quan trieu nguyen",
        },
    )
    assert check_res.status_code == 200, check_res.text
    check_data = check_res.json()
    assert check_data["is_duplicate"] is True
    assert check_data["matched_by"] == "title_author"
    assert check_data["duplicate_source"]["id"] == source_id

    # 3. Attempt to register duplicate with lowercase normalized title/author
    res2 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "royal_record",
            "title": "đại nam nhất thống chí",
            "author_text": "quốc sử quán triều nguyễn",
            "publication_year": 1882,
        },
    )
    assert res2.status_code == 409, "Duplicate Title+Author registration must return 409 Conflict"
    err = res2.json()
    assert err["error"]["code"] == "HISTORICAL_SOURCE_DUPLICATE"
    assert err["error"]["details"]["matched_by"] == "title_author"
    assert err["error"]["details"]["duplicate_id"] == source_id


def test_deduplication_by_checksum(client: TestClient, db_session):
    """Test deduplication of bibliographic sources by explicit checksum."""
    _create_staff_user(client, db_session, "dedup_chk")

    custom_checksum = f"sha256:{uuid.uuid4().hex}"

    # 1. Register source with unique checksum
    res1 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "scholarly_book",
            "title": f"Chuyên Khảo Đồ Đồng {uuid.uuid4().hex[:6]}",
            "author_text": "Tác Giả A",
            "publication_year": 2010,
            "checksum": custom_checksum,
        },
    )
    assert res1.status_code == 200, res1.text
    source_id = res1.json()["id"]

    # 2. Attempt to register another source with different metadata but same checksum
    res2 = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "reference_work",
            "title": f"Tài Liệu Khác Hoàn Toàn {uuid.uuid4().hex[:6]}",
            "author_text": "Tác Giả B",
            "publication_year": 2015,
            "checksum": custom_checksum,
        },
    )
    assert res2.status_code == 409, "Duplicate checksum registration must return 409 Conflict"
    err = res2.json()
    assert err["error"]["code"] == "HISTORICAL_SOURCE_DUPLICATE"
    assert err["error"]["details"]["matched_by"] == "checksum"
    assert err["error"]["details"]["duplicate_id"] == source_id


def test_deduplication_bypass_flag(client: TestClient, db_session):
    """Verify staff can bypass deduplication check when explicitly permitted (?check_duplicate=false)."""
    _create_staff_user(client, db_session, "dedup_bypass")

    title = f"Tập Thơ Ngự Chế Cửu Đỉnh {uuid.uuid4().hex[:6]}"
    author = "Hoàng Đế Minh Mạng"

    res1 = client.post(
        "/api/v1/admin/history/sources",
        json={"source_type": "royal_record", "title": title, "author_text": author},
    )
    assert res1.status_code == 200

    # Create distinct edition/translation by bypassing deduplication
    res2 = client.post(
        "/api/v1/admin/history/sources?check_duplicate=false",
        json={
            "source_type": "critical_edition",
            "title": title,
            "author_text": author,
            "edition": "Bản Dịch Chú Thích Mới 2026",
        },
    )
    assert res2.status_code == 200, "Bypassing deduplication should return 200 OK"
    assert res2.json()["id"] != res1.json()["id"]


# ==============================================================================
# 5. Deterministic Checksum Computation Verification
# ==============================================================================

def test_deterministic_checksum_computation(client: TestClient, db_session):
    """Test deterministic checksum calculation and auto-population."""
    _create_staff_user(client, db_session, "checksum_eval")

    data1 = {
        "source_type": "scholarly_book",
        "title": "Văn Hóa Cố Đô",
        "author_text": "Phan Thuận An",
        "publication_year": 1995,
        "edition": "1st Edition",
        "isbn": "978-0-123-45678-9",
        "doi": "10.1234/vancodo",
    }
    data2 = {
        "source_type": "scholarly_book",
        "title": "  văn hóa cố đô  ",
        "author_text": "phan thuận an",
        "publication_year": 1995,
        "edition": "1st edition",
        "isbn": "9780123456789",
        "doi": "https://doi.org/10.1234/vancodo",
    }

    # Deterministic canonical hashing
    hash1 = gov.compute_source_checksum(data1)
    hash2 = gov.compute_source_checksum(data2)
    assert hash1 == hash2, "Checksum must be identical across normalized representations"

    # Auto-computed on create when none is supplied
    res = client.post(
        "/api/v1/admin/history/sources?check_duplicate=false",
        json={
            "source_type": "reference_work",
            "title": f"Từ Điển Địa Danh Xứ Huế {uuid.uuid4().hex[:6]}",
            "author_text": "Bùi Minh Đức",
            "publication_year": 2001,
        },
    )
    assert res.status_code == 200
    created = res.json()
    assert created["checksum"] is not None
    assert len(created["checksum"]) == 64  # SHA-256 hex string length
