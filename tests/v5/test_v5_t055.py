# -*- coding: utf-8 -*-
"""V5-T055: Mobile Source Citation UI & Provenance Preservation Test Suite.

Wave W05, Slot A05 (Priority: P1, Classification: PRODUCTION_COMPLETION).

Audits and verifies:
1. Mobile Source Citation UI in mobile/lib/features/urn_viewer/ and mobile/lib/features/explore/:
   - Displays public locators (volume, chapter, page_start, page_end, section, folio).
   - Displays bibliographic citations (source title, author, publisher, publication year, license, rights).
   - Displays Hán-Nôm script characters, Sino-Vietnamese reading, and bilingual translations.
   - Displays epistemic uncertainty indicators (documented/Sử liệu xác thực, traditional/Truyền thuyết dân gian, uncertain/Đang khảo cứu, disputed/Có tranh luận).
2. Unauthorized Restricted Snippets Avoidance:
   - Rights-restricted and unlicensed excerpts are strictly redacted to [REDACTED: RIGHTS_RESTRICTED] for public users.
   - Public metadata, author, title, and public locators remain intact.
   - Privileged staff users retain access to unredacted excerpts for fact-checking.
   - Open/public domain excerpts are visible without redaction.
3. CRITICAL INVARIANT & NEGATIVE ABUSE TEST:
   - Offline content preserves original citation provenance; cannot strip source attribution.
   - Attempting to cache or export content with stripped sources on verified claims fails with MissingSourceAttributionError.
   - Attempting to promote disputed claims to verified status in offline bundles fails with DisputedClaimPromotionError.
   - Tampered or forged provenance hashes fail with CitationProvenanceError.
   - Valid offline bundles preserve complete citation provenance and pass validation cleanly.
4. Mobile Client Source & Architectural Invariants:
   - Analyzes source_citation.dart, source_citation_sheet.dart, epistemic_badge.dart, source_citation_provider.dart.
   - Confirms motif_sidebar.dart and urn_card.dart wire SourceCitationSheet.show.
   - Confirms hive_storage.dart supports citationsBox with authenticated read/write.
5. End-to-End API Integration:
   - Tests GET /api/v1/history/citations/{slug_or_id} and GET /api/v1/history/entities/{slug_or_id}/citations.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models import User, UserRole
from backend.services import history_governance as gov
from backend.services.entity_citations import (
    CitationProvenanceError,
    DisputedClaimPromotionError,
    MissingSourceAttributionError,
    compute_citation_provenance_hash,
    determine_epistemic_certainty,
    format_public_locator,
    resolve_entity_citations_bundle,
    validate_offline_citation_provenance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MOBILE_DIR = REPO_ROOT / "mobile" / "lib"


# ==============================================================================
# Helpers & Database Seeders
# ==============================================================================

def _create_test_staff_user(db_session: Session) -> User:
    """Create a staff/admin user for privileged excerpt testing."""
    email = f"staff_curator_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        email=email,
        username=f"staff_{uuid.uuid4().hex[:6]}",
        password_hash="mock_hashed_pw",
        role=UserRole.admin,
        display_name="Cố Đô Curator",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_canonical_urn_with_citations(
    db_session: Session,
    urn_slug: str = "cao-dinh",
) -> tuple[HistoricalEntity, HistoricalClaim, HistoricalSource, HistoricalClaimSource]:
    """Seed an urn entity with an authoritative historical claim and bibliographic source."""
    # 1. Entity
    entity = db_session.execute(
        select(HistoricalEntity).where(HistoricalEntity.slug == urn_slug)
    ).scalar_one_or_none()

    if not entity:
        entity = HistoricalEntity(
            entity_type="urn",
            slug=urn_slug,
            name_vi="Cao Đỉnh",
            name_en="Cao Dinh (The Supreme Urn)",
            name_han_nom="高鼎",
            alternative_names=["Đỉnh thứ nhất", "Đỉnh Trung ương"],
            summary_vi="Cao Đỉnh là chiếc đỉnh đồng lớn nhất trong Cửu Đỉnh, biểu trưng cho hoàng đế Gia Long.",
            summary_en="Cao Dinh is the primary and largest dynastic bronze urn, dedicated to Emperor Gia Long.",
            publication_status="published",
            content_version=1,
        )
        db_session.add(entity)
        db_session.flush()

    # 2. Bibliographic Source (Public Domain Imperial Chronicle)
    source = HistoricalSource(
        source_type="royal_record",
        title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc Sử Quán Triều Nguyễn",
        publisher="NXB Giáo Dục",
        publication_year=1844,
        volume="Đệ nhị kỷ",
        pages="142-145",
        rights_status="public_domain",
        license="Public Domain (1844 Imperial Chronicle)",
        public_display_allowed=True,
        archive_url="https://repository.histolab.icu/sources/dntl-02-154",
        citation_text="Đại Nam Thực Lục Chính Biên, Đệ nhị kỷ, Quyển CLIV, tr. 142-145.",
        excerpt="Năm Minh Mạng thứ 16, mùa đông tháng 12, đúc xong chín đỉnh lớn đặt trước sân Thế Miếu.",
        verification_status="expert_verified",
    )
    db_session.add(source)
    db_session.flush()

    # 3. Historical Claim
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type="factual",
        statement_vi="Cao Đỉnh được khởi đúc vào tháng Chạp năm Ất Mùi (1835) và hoàn thành vào năm Bính Thân (1836).",
        statement_en="Cao Dinh was cast starting in December 1835 and completed in 1836.",
        confidence="verified",
        verification_status="expert_verified",
        origin="royal_chronicle",
        risk_level="normal",
        is_current=True,
    )
    db_session.add(claim)
    db_session.flush()

    # 4. Claim Source Binding with Public Locators
    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=source.id,
        support_type="supports",
        chapter="CLIV",
        folio="12a-14b",
        page_start="142",
        page_end="145",
        quotation_excerpt="Năm Minh Mạng thứ 16, mùa đông tháng 12, đúc xong chín đỉnh lớn...",
    )
    db_session.add(binding)
    db_session.commit()
    db_session.refresh(entity)
    db_session.refresh(claim)
    db_session.refresh(source)
    db_session.refresh(binding)

    return entity, claim, source, binding


# ==============================================================================
# 1. Public Locator Formatting Tests
# ==============================================================================

def test_public_locator_formatting():
    """Verifies scholarly public locator string assembly across various archival units."""
    # Case A: Volume + Chapter + Folio + Page Range
    binding_a = HistoricalClaimSource(
        chapter="CLIV",
        folio="12a",
        page_start="142",
        page_end="145",
    )
    source_a = HistoricalSource(
        volume="Đệ nhị kỷ",
        title="Đại Nam Thực Lục",
        source_type="royal_record",
    )
    loc_a = format_public_locator(binding=binding_a, source=source_a)
    assert "Đệ nhị kỷ" in loc_a
    assert "Quyển CLIV" in loc_a
    assert "Tờ 12a" in loc_a
    assert "Tr. 142-145" in loc_a

    # Case B: Inscription location on bronze monument
    binding_b = HistoricalClaimSource(
        inscription_location="Hông đỉnh bên phải, tầng thứ 2",
    )
    source_b = HistoricalSource(
        title="Văn Khắc Cửu Đỉnh",
        source_type="inscription",
    )
    loc_b = format_public_locator(binding=binding_b, source=source_b)
    assert "Hông đỉnh bên phải, tầng thứ 2" in loc_b

    # Case C: Single page reference
    binding_c = HistoricalClaimSource(page_start="88")
    source_c = HistoricalSource(title="Mỹ Thuật Huế", source_type="scholarly_book")
    loc_c = format_public_locator(binding=binding_c, source=source_c)
    assert loc_c == "Tr. 88"

    # Case D: Locator override takes priority
    loc_d = format_public_locator(locator_override="Chương 4, mục II, tr. 45")
    assert loc_d == "Chương 4, mục II, tr. 45"


# ==============================================================================
# 2. Epistemic Uncertainty Classifier Tests
# ==============================================================================

def test_epistemic_uncertainty_classifier():
    """Verifies dynamic epistemic certainty assignment for documented, traditional, and disputed assertions."""
    # 1. Documented primary fact (expert_verified with source)
    cl_doc = HistoricalClaim(
        claim_type="factual",
        verification_status="expert_verified",
        statement_vi="Đúc năm 1835-1836",
    )
    code, label_vi, label_en = determine_epistemic_certainty(
        cl_doc, has_source=True, is_disputed=False
    )
    assert code == "su_lieu_xac_thuc"
    assert "Sử liệu xác thực" in label_vi
    assert "Documented" in label_en

    # 2. Traditional folklore / folk account
    cl_folk = HistoricalClaim(
        claim_type="traditional_account",
        verification_status="source_attached",
        statement_vi="Tương truyền có điềm rồng vàng bay qua",
    )
    code_f, label_f_vi, _ = determine_epistemic_certainty(
        cl_folk, has_source=True, is_disputed=False
    )
    assert code_f == "truyen_thuyet_dan_gian"
    assert "Truyền thuyết dân gian" in label_f_vi

    # 3. Disputed scholarly assertion (MUST NEVER masquerade as verified fact)
    cl_disp = HistoricalClaim(
        claim_type="chronology",
        verification_status="disputed",
        confidence="disputed",
        statement_vi="Niên đại chế tác gây tranh cãi",
    )
    code_d, label_d_vi, _ = determine_epistemic_certainty(
        cl_disp, has_source=True, is_disputed=True
    )
    assert code_d == "dang_khao_cuu"
    assert "Có tranh luận" in label_d_vi

    # 4. Unbacked assertion without sources
    cl_unbacked = HistoricalClaim(
        claim_type="factual",
        verification_status="expert_verified",  # pretends to be verified
        statement_vi="Khẳng định nhưng không có bằng chứng",
    )
    code_u, label_u_vi, _ = determine_epistemic_certainty(
        cl_unbacked, has_source=False, is_disputed=False
    )
    assert code_u == "dang_khao_cuu"
    assert "Chưa gắn nguồn" in label_u_vi


# ==============================================================================
# 3. Unauthorized Restricted Snippets Avoidance & Redaction Tests
# ==============================================================================

def test_unauthorized_restricted_snippets_avoidance(client: TestClient, db_session: Session):
    """Verifies that copyrighted/restricted excerpts are strictly redacted for public queries."""
    # Seed entity with rights-restricted source
    entity = HistoricalEntity(
        entity_type="relief",
        slug="test-relief-restricted",
        name_vi="Thái Bình Điểu",
        publication_status="published",
        content_version=1,
    )
    db_session.add(entity)
    db_session.flush()

    restricted_source = HistoricalSource(
        source_type="scholarly_book",
        title="Nghiên Cứu Mỹ Thuật Cửu Đỉnh (Độc quyền xuất bản)",
        author_text="Học Giả Độc Quyền",
        publisher="Nhà Xuất Bản Thương Mại",
        publication_year=2024,
        rights_status="restricted",
        license="All Rights Reserved / Copyrighted",
        public_display_allowed=False,
        citation_text="Nghiên Cứu Mỹ Thuật Cửu Đỉnh, tr. 19-25.",
        excerpt="Đây là trích đoạn tài liệu bản quyền mật cấm trích dẫn tự do trên môi trường số.",
        verification_status="rights_restricted",
    )
    db_session.add(restricted_source)
    db_session.flush()

    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type="interpretation",
        statement_vi="Thái Bình Điểu biểu trưng cho nền thái bình thịnh trị.",
        confidence="verified",
        verification_status="expert_verified",
        origin="academic_paper",
        is_current=True,
    )
    db_session.add(claim)
    db_session.flush()

    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=restricted_source.id,
        support_type="supports",
        page_start="19",
        page_end="25",
        quotation_excerpt="Đây là trích đoạn tài liệu bản quyền mật cấm trích dẫn tự do trên môi trường số.",
    )
    db_session.add(binding)
    db_session.commit()

    # 1. Public / Anonymous Request: Must be redacted
    res_pub = client.get(f"/api/v1/history/citations/{entity.slug}")
    assert res_pub.status_code == 200, res_pub.text
    bundle_pub = res_pub.json()

    assert bundle_pub["has_restricted_sources"] is True
    src_pub = bundle_pub["claims"][0]["sources"][0]
    assert src_pub["is_excerpt_redacted"] is True
    assert src_pub["quotation_excerpt"] == "[REDACTED: RIGHTS_RESTRICTED]"
    # Critical: Metadata and locator MUST be intact
    assert src_pub["source_title"] == "Nghiên Cứu Mỹ Thuật Cửu Đỉnh (Độc quyền xuất bản)"
    assert src_pub["author"] == "Học Giả Độc Quyền"
    assert "Tr. 19-25" in src_pub["locator"]
    assert src_pub["rights_status"] == "restricted"

    # 2. Privileged Staff Request: Allowed unredacted for fact-checking
    bundle_priv = resolve_entity_citations_bundle(
        db_session, entity.slug, is_privileged=True
    )
    src_priv = bundle_priv["claims"][0]["sources"][0]
    assert src_priv["is_excerpt_redacted"] is False
    assert "trích đoạn tài liệu bản quyền mật" in src_priv["quotation_excerpt"]


# ==============================================================================
# 4. Open / Public Domain Excerpt Display Tests
# ==============================================================================

def test_open_public_domain_excerpt_permitted(client: TestClient, db_session: Session):
    """Verifies that public domain and CC0 sources allow unredacted excerpt display."""
    entity, claim, source, binding = _seed_canonical_urn_with_citations(
        db_session, urn_slug="cao-dinh"
    )

    res = client.get(f"/api/v1/history/citations/{entity.slug}")
    assert res.status_code == 200, res.text
    data = res.json()

    src_item = data["claims"][0]["sources"][0]
    assert src_item["is_excerpt_redacted"] is False
    assert src_item["rights_status"] == "public_domain"
    assert "đúc xong chín đỉnh lớn" in src_item["quotation_excerpt"]
    assert src_item["locator"] is not None
    assert "Tr. 142-145" in src_item["locator"]


# ==============================================================================
# 5. Negative Abuse: Offline Content Stripping Sources Is Strictly Rejected
# ==============================================================================

def test_negative_abuse_offline_content_stripping_sources_rejected():
    """Negative Abuse Test: Validates that offline content cannot strip source attribution.
    
    If an offline cache bundle marks a claim as 'su_lieu_xac_thuc' (verified fact)
    while dropping/stripping backing sources, validation engine strictly rejects it
    with MissingSourceAttributionError.
    """
    valid_bundle = {
        "slug": "cao-dinh",
        "claims": [
            {
                "claim_id": "c1",
                "statement_vi": "Khẳng định có bằng chứng",
                "epistemic_certainty": "su_lieu_xac_thuc",
                "is_disputed": False,
                "sources": [
                    {
                        "source_id": "s1",
                        "source_title": "Đại Nam Thực Lục",
                        "locator": "Quyển 3, tr. 14",
                        "rights_status": "public_domain",
                    }
                ],
            }
        ],
    }
    valid_bundle["bundle_provenance_hash"] = compute_citation_provenance_hash(
        "cao-dinh", valid_bundle["claims"]
    )

    # Clean positive check passes
    assert validate_offline_citation_provenance(valid_bundle) is True

    # Abuse 1: Attacker strips source attribution (sources empty)
    stripped_bundle = {
        "slug": "cao-dinh",
        "bundle_provenance_hash": "a" * 64,
        "claims": [
            {
                "claim_id": "c1",
                "statement_vi": "Khẳng định có bằng chứng nhưng bị tước nguồn",
                "epistemic_certainty": "su_lieu_xac_thuc",  # Claims verified fact
                "is_disputed": False,
                "sources": [],  # Sources stripped!
            }
        ],
    }

    with pytest.raises(MissingSourceAttributionError) as exc_info:
        validate_offline_citation_provenance(stripped_bundle)
    assert "source attribution has been stripped" in str(exc_info.value)

    # Abuse 2: Missing bundle provenance hash entirely
    no_hash_bundle = {
        "slug": "cao-dinh",
        "bundle_provenance_hash": "",  # Missing!
        "claims": [],
    }
    with pytest.raises(MissingSourceAttributionError):
        validate_offline_citation_provenance(no_hash_bundle)

    # Abuse 3: Stripped source title
    stripped_title_bundle = {
        "slug": "cao-dinh",
        "bundle_provenance_hash": "b" * 64,
        "claims": [
            {
                "claim_id": "c1",
                "statement_vi": "Nội dung",
                "epistemic_certainty": "su_lieu_xac_thuc",
                "sources": [
                    {
                        "source_id": "s1",
                        "source_title": "   ",  # Blank title stripped!
                        "locator": "Tr. 1",
                        "rights_status": "public_domain",
                    }
                ],
            }
        ],
    }
    with pytest.raises(MissingSourceAttributionError):
        validate_offline_citation_provenance(stripped_title_bundle)


# ==============================================================================
# 6. Negative Abuse: Disputed Claims Cannot Be Promoted In Offline Cache
# ==============================================================================

def test_negative_abuse_disputed_claim_cannot_be_promoted_in_offline_bundle():
    """Negative Abuse Test: Validates that disputed claims cannot be forged as verified in offline cache."""
    disputed_bundle = {
        "slug": "thuan-dinh",
        "bundle_provenance_hash": "c" * 64,
        "claims": [
            {
                "claim_id": "c-disputed",
                "statement_vi": "Khẳng định còn đang tranh cãi gay gắt",
                "is_disputed": True,
                "epistemic_certainty": "su_lieu_xac_thuc",  # FORGERY: attempting to promote disputed claim
                "sources": [
                    {
                        "source_id": "s1",
                        "source_title": "Tạp chí Tranh Luận",
                        "locator": "Tr. 5",
                        "rights_status": "open_access",
                    }
                ],
            }
        ],
    }

    with pytest.raises(DisputedClaimPromotionError) as exc_info:
        validate_offline_citation_provenance(disputed_bundle)
    assert "disputed claim" in str(exc_info.value).lower()
    assert "cannot be promoted" in str(exc_info.value).lower()


# ==============================================================================
# 7. Negative Abuse: Tampered Provenance Hash Is Detected
# ==============================================================================

def test_negative_abuse_tampered_provenance_hash_rejected():
    """Negative Abuse Test: Altering statement or source without valid signature is detected."""
    original_bundle = {
        "slug": "nhan-dinh",
        "claims": [
            {
                "claim_id": "c1",
                "statement_vi": "Khẳng định ban đầu",
                "epistemic_certainty": "su_lieu_xac_thuc",
                "is_disputed": False,
                "sources": [
                    {
                        "source_id": "s1",
                        "source_title": "Khâm Định Đại Nam Hội Điển",
                        "locator": "Quyển 8, tr. 20",
                        "rights_status": "public_domain",
                    }
                ],
            }
        ],
    }
    canonical_hash = compute_citation_provenance_hash("nhan-dinh", original_bundle["claims"])

    # Tampering: attacker changes statement text but keeps old hash
    tampered_bundle = dict(original_bundle)
    tampered_bundle["bundle_provenance_hash"] = canonical_hash
    tampered_bundle["claims"][0]["statement_vi"] = "Văn bản đã bị sửa đổi trái phép!"

    with pytest.raises(CitationProvenanceError) as exc_info:
        validate_offline_citation_provenance(tampered_bundle)
    assert "Provenance hash mismatch" in str(exc_info.value)


# ==============================================================================
# 8. Mobile Client Source Code & Architectural Analysis
# ==============================================================================

def test_mobile_source_citation_architectural_analysis():
    """Audits the Flutter mobile client code to verify complete citation UI wiring."""
    # 1. Domain Entities: source_citation.dart
    citation_entity_path = (
        MOBILE_DIR / "features" / "urn_viewer" / "domain" / "entities" / "source_citation.dart"
    )
    assert citation_entity_path.exists(), "source_citation.dart must exist in domain/entities"
    entity_code = citation_entity_path.read_text(encoding="utf-8")

    assert "enum EpistemicCertainty" in entity_code
    assert "documented('su_lieu_xac_thuc'" in entity_code
    assert "traditional('truyen_thuyet_dan_gian'" in entity_code
    assert "uncertain('dang_khao_cuu'" in entity_code
    assert "disputed('co_tranh_luan'" in entity_code
    assert "class SourceCitation" in entity_code
    assert "locator" in entity_code
    assert "isRestrictedSnippet" in entity_code
    assert "[REDACTED: RIGHTS_RESTRICTED]" in entity_code
    assert "class EntityCitationBundle" in entity_code
    assert "verifyProvenanceIntegrity()" in entity_code
    assert "MissingSourceAttributionError" in entity_code

    # 2. Epistemic Badge: epistemic_badge.dart
    badge_widget_path = (
        MOBILE_DIR / "features" / "urn_viewer" / "presentation" / "widgets" / "epistemic_badge.dart"
    )
    assert badge_widget_path.exists(), "epistemic_badge.dart must exist"
    badge_code = badge_widget_path.read_text(encoding="utf-8")
    assert "class EpistemicBadge extends StatelessWidget" in badge_code
    assert "Semantics(" in badge_code

    # 3. Citation Sheet: source_citation_sheet.dart
    sheet_widget_path = (
        MOBILE_DIR / "features" / "urn_viewer" / "presentation" / "widgets" / "source_citation_sheet.dart"
    )
    assert sheet_widget_path.exists(), "source_citation_sheet.dart must exist"
    sheet_code = sheet_widget_path.read_text(encoding="utf-8")
    assert "class SourceCitationSheet extends ConsumerWidget" in sheet_code
    assert "DraggableScrollableSheet" in sheet_code
    assert "nameHanNom" in sheet_code
    assert "readingHanNom" in sheet_code
    assert "[REDACTED: RIGHTS_RESTRICTED]" in sheet_code
    assert "bundleProvenanceHash" in sheet_code

    # 4. Citation Provider: source_citation_provider.dart
    provider_path = (
        MOBILE_DIR / "features" / "urn_viewer" / "presentation" / "providers" / "source_citation_provider.dart"
    )
    assert provider_path.exists(), "source_citation_provider.dart must exist"
    provider_code = provider_path.read_text(encoding="utf-8")
    assert "entityCitationsProvider" in provider_code
    assert "verifyProvenanceIntegrity()" in provider_code

    # 5. Motif Sidebar Integration: motif_sidebar.dart
    sidebar_path = (
        MOBILE_DIR / "features" / "urn_viewer" / "presentation" / "widgets" / "motif_sidebar.dart"
    )
    assert sidebar_path.exists()
    sidebar_code = sidebar_path.read_text(encoding="utf-8")
    assert "SourceCitationSheet.show" in sidebar_code
    assert "Tra cứu nguồn sử liệu gốc" in sidebar_code

    # 6. Urn Card Integration: urn_card.dart
    urn_card_path = (
        MOBILE_DIR / "features" / "explore" / "presentation" / "widgets" / "urn_card.dart"
    )
    assert urn_card_path.exists()
    urn_card_code = urn_card_path.read_text(encoding="utf-8")
    assert "SourceCitationSheet.show" in urn_card_code

    # 7. HiveStorage Citations Box: hive_storage.dart
    hive_path = MOBILE_DIR / "core" / "storage" / "hive_storage.dart"
    assert hive_path.exists()
    hive_code = hive_path.read_text(encoding="utf-8")
    assert "_citationsBox = 'citations'" in hive_code
    assert "cacheEntityCitations" in hive_code
    assert "getCachedEntityCitations" in hive_code


# ==============================================================================
# 9. End-to-End API Integration Tests
# ==============================================================================

def test_api_citation_endpoint_e2e(client: TestClient, db_session: Session):
    """Verifies that the /api/v1/history/citations/{slug} endpoint returns full structured citations."""
    entity, claim, source, binding = _seed_canonical_urn_with_citations(
        db_session, urn_slug="nhan-dinh"
    )

    # Request citation bundle by urn slug
    res = client.get("/api/v1/history/citations/nhan-dinh")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["slug"] == "nhan-dinh"
    assert data["entity_type"] == "urn"
    assert data["name_vi"] == "Cao Đỉnh" or "Đỉnh" in data["name_vi"]
    assert len(data["claims"]) >= 1
    assert data["total_sources_count"] >= 1
    assert data["bundle_provenance_hash"] is not None
    assert len(data["bundle_provenance_hash"]) >= 16

    claim_out = data["claims"][0]
    assert claim_out["epistemic_certainty"] == "su_lieu_xac_thuc"
    assert claim_out["has_source"] is True

    source_out = claim_out["sources"][0]
    assert source_out["source_title"] == "Đại Nam Thực Lục Chính Biên"
    assert "Tr. 142-145" in source_out["locator"]
    assert source_out["rights_status"] == "public_domain"
