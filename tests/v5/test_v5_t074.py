# -*- coding: utf-8 -*-
"""V5-T074 (Wave W07, Slot A04): P01/P02 Legal Source Acquisition Test Suite.

Audits and verifies:
1. Provider connectors with rights, robots, licensing, and quota policies:
   - Official heritage registry connectors (UNESCO, MOWCAP, DSVH, HMCC, Nom Foundation, etc.).
   - Open scholarly resolvers (DOI, Crossref).
   - Domain validation and policy enforcement.
2. Negative abuse tests:
   - Forbidden copyrighted scan blocked: Attempting to acquire/ingest full scanned PDF of
     in-copyright work without license is strictly blocked (ForbiddenCopyrightedScanError).
   - Paywall bypass strictly blocked: Scraper bypass headers and paywalled publisher evasion
     are rejected (PaywallBypassError).
   - Robots.txt compliance: Disallowed paths are blocked (RobotsDisallowedError).
   - Forbidden pirate/shadow domains: Known pirate scan libraries (Sci-Hub, LibGen) are
     strictly blocked (ForbiddenDomainError).
   - Malicious file sanitization: Executables (PE, ELF, shell) masquerading as PDFs are
     intercepted (MaliciousPayloadError).
   - Authority impersonation: Personal blogs claiming official museum identity are blocked
     (AuthorityImpersonationError).
   - Unknown rights != granted: Ambiguous or unreviewed rights are strictly quarantined
     (QUARANTINED_PENDING_REVIEW), never auto-granted.
3. Candidate normalization and deduplication (P01):
   - Canonicalizes URLs (stripping UTM tracking and session parameters).
   - Normalizes DOIs and ISBNs.
   - Intra-batch candidate deduplication.
   - Database deduplication against existing HistoricalSource records.
4. Legal source acquisition and database persistence (P02):
   - Cleared public domain and open license sources ingested with verification_status='accessible'.
   - Cleared copyrighted sources ingested as metadata-only with verification_status='rights_restricted'
     and excerpt redacted.
   - Atomic and idempotent ingestion preventing duplicate database rows.
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy import select

from backend.history_models import HistoricalSource
from backend.services.history_governance import (
    find_duplicate_source,
    normalize_bibliographic_text,
    normalize_doi,
    normalize_isbn,
)
from backend.services.research_factory import (
    AcquisitionDecision,
    AcquisitionResult,
    AuthorityImpersonationError,
    BaseProviderConnector,
    ForbiddenCopyrightedScanError,
    ForbiddenDomainError,
    LegalRightsStatus,
    LegalSourceAcquisitionService,
    MaliciousPayloadError,
    PaywallBypassError,
    ProviderRegistry,
    RobotsDisallowedError,
    ScoutRole,
    SourceCandidate,
    SourceDiscoveryScout,
    SourceSnapshot,
    UnapprovedSourceQuarantinedError,
    canonicalize_url,
    compute_candidate_hash,
    legal_acquisition_service,
    provider_registry,
)


# ==============================================================================
# 1. Provider Connectors & Policies
# ==============================================================================
def test_provider_connectors_registry_and_policies():
    """Verify built-in authorized connectors, domain extraction, and connector lookup."""
    reg = ProviderRegistry()

    # UNESCO
    unesco_conn = reg.get_connector("https://en.unesco.org/memoryoftheworld/register")
    assert unesco_conn is not None
    assert unesco_conn.is_approved is True
    assert unesco_conn.is_paywalled is False

    # National Heritage Department (dsvh.gov.vn)
    dsvh_conn = reg.get_connector("http://dsvh.gov.vn/di-tich-quoc-gia-dac-biet")
    assert dsvh_conn is not None
    assert dsvh_conn.is_approved is True

    # Nôm Foundation (nomfoundation.org)
    nom_conn = reg.get_connector("https://nomfoundation.org/common/nom_details.php?codepoint=1234")
    assert nom_conn is not None
    assert nom_conn.is_approved is True

    # DOI resolver
    doi_conn = reg.get_connector("https://doi.org/10.1007/s00004-020-00498-8")
    assert doi_conn is not None
    assert doi_conn.is_approved is True

    # Clean domain extraction
    assert reg.extract_domain("https://sub.dsvh.gov.vn:8080/path?arg=1") == "sub.dsvh.gov.vn"
    assert reg.is_domain_approved("unesco.org") is True
    assert reg.is_domain_approved("random-untrusted-domain.xyz") is False


# ==============================================================================
# 2. Robots.txt Compliance Check
# ==============================================================================
def test_robots_txt_compliance_enforced():
    """Verify paths disallowed by robots.txt are deterministically blocked."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    # Permitted path
    allowed_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A01.value,
        title="Hồ sơ Cửu Đỉnh Huế UNESCO",
        url="https://en.unesco.org/memoryoftheworld/register/cuu-dinh",
        claimed_rights=LegalRightsStatus.PUBLIC_DOMAIN,
    )
    result = service.evaluate_and_acquire(allowed_candidate)
    assert result.decision == AcquisitionDecision.ALLOWED_FULL

    # Disallowed path: /restricted/*
    restricted_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A01.value,
        title="Internal Heritage Scans",
        url="https://en.unesco.org/restricted/internal-scans/cuu-dinh.pdf",
        claimed_rights=LegalRightsStatus.PUBLIC_DOMAIN,
    )
    with pytest.raises(RobotsDisallowedError) as exc_info:
        service.evaluate_and_acquire(restricted_candidate)

    assert "Robots.txt forbids access" in str(exc_info.value)
    assert exc_info.value.code == "ROBOTS_DISALLOWED"


# ==============================================================================
# 3. Negative Abuse: Forbidden Copyrighted Scan Blocked
# ==============================================================================
def test_negative_abuse_forbidden_copyrighted_scan_blocked():
    """Negative Abuse Test (must fail before fix):
    
    Ingesting full digital scan of an in-copyright book without publisher authorization
    must be strictly blocked with ForbiddenCopyrightedScanError.
    
    Meanwhile, metadata-only bibliographic citation of the same book without scan payload
    is permitted with excerpt redaction.
    """
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    # Valid PDF bytes for test payload
    sample_pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    copyrighted_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A05.value,
        title="Nghiên cứu Mỹ thuật Triều Nguyễn (2018)",
        author_text="Trần Đức Anh Sơn",
        publication_year=2018,
        edition="1st",
        isbn="978-604-0-12345-6",
        url="https://doi.org",
        claimed_rights=LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED,
        provenance_notes="Sách chuyên khảo về mỹ thuật và Cửu Đỉnh.",
    )

    # Attempt 1: Full scanned document acquisition -> STRICTLY BLOCKED!
    with pytest.raises(ForbiddenCopyrightedScanError) as exc_info:
        service.evaluate_and_acquire(
            copyrighted_candidate,
            payload_bytes=sample_pdf_bytes,
            declared_mime_type="application/pdf",
            is_full_scan_download=True,
        )

    assert exc_info.value.code == "FORBIDDEN_COPYRIGHTED_SCAN"
    assert "Forbidden copyrighted scan" in str(exc_info.value)

    # Attempt 2: Metadata-only bibliographic reference (no raw scan payload) -> ALLOWED_METADATA_ONLY
    meta_result = service.evaluate_and_acquire(
        copyrighted_candidate,
        payload_bytes=None,
        is_full_scan_download=False,
    )
    assert meta_result.decision == AcquisitionDecision.ALLOWED_METADATA_ONLY
    assert meta_result.public_display_allowed is False
    assert meta_result.is_excerpt_redacted is True
    assert meta_result.rights_status == LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED


# ==============================================================================
# 4. Negative Abuse: Paywall Bypass Strictly Blocked
# ==============================================================================
def test_negative_abuse_paywall_bypass_blocked():
    """Verify scraping behind paywalls or passing bypass evasion headers is blocked."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    paywalled_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A05.value,
        title="Journal of Vietnamese Heritage Studies",
        url="https://www.jstor.org/stable/10.2307/12345678",
        claimed_rights=LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED,
    )

    # 1. Accessing paywalled publisher without institutional subscription
    with pytest.raises(PaywallBypassError) as exc_info:
        service.evaluate_and_acquire(paywalled_candidate)

    assert exc_info.value.code == "PAYWALL_BYPASS_FORBIDDEN"
    assert "subscription" in str(exc_info.value).lower()

    # 2. Attempting unauthorized bypass headers (e.g. X-Bypass-Paywall)
    with pytest.raises(PaywallBypassError) as exc_info2:
        service.evaluate_and_acquire(
            paywalled_candidate,
            headers={"X-Bypass-Paywall": "true"},
        )
    assert "bypass" in str(exc_info2.value).lower()

    # 3. Attempting User-Agent spoofing to evade paywall
    with pytest.raises(PaywallBypassError) as exc_info3:
        service.evaluate_and_acquire(
            paywalled_candidate,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        )
    assert "spoofing" in str(exc_info3.value).lower()


# ==============================================================================
# 5. Negative Abuse: Forbidden Pirate / Shadow Library Domains Blocked
# ==============================================================================
def test_negative_abuse_forbidden_pirate_domain_blocked():
    """Verify pirate scan repositories and shadow libraries are strictly blocked."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    pirate_domains = [
        "https://sci-hub.se/10.1007/s00004-020-00498-8",
        "https://libgen.is/book/index.php?md5=123456789",
        "https://pirated-scans.org/heritage/cuu-dinh.pdf",
        "http://darkweb-heritage.onion/leaked-scan.pdf",
    ]

    for p_url in pirate_domains:
        candidate = scout.create_candidate(
            scout_role=ScoutRole.P01_A05.value,
            title="Sử liệu trái phép",
            url=p_url,
            claimed_rights=LegalRightsStatus.FORBIDDEN_PIRATED,
        )
        with pytest.raises(ForbiddenDomainError) as exc_info:
            service.evaluate_and_acquire(candidate)

        assert exc_info.value.code == "FORBIDDEN_PROVIDER_DOMAIN"
        assert "unauthorized scan repository" in str(exc_info.value).lower()


# ==============================================================================
# 6. Negative Abuse: Unapproved Source Quarantined
# ==============================================================================
def test_negative_abuse_unapproved_source_quarantined():
    """Verify sources from unapproved/unverified domains are quarantined and cannot be ingested."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    unapproved_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A10.value,
        title="Bài viết trên diễn đàn cá nhân về Cửu Đỉnh",
        url="https://forum-lichsu-unverified.net/thread/123",
        claimed_rights=LegalRightsStatus.PUBLIC_DOMAIN,
    )

    result = service.evaluate_and_acquire(unapproved_candidate)
    assert result.decision == AcquisitionDecision.QUARANTINED_PENDING_REVIEW
    assert result.quarantine_required is True

    # Ingestion into HistoricalSource must be strictly rejected
    with pytest.raises(UnapprovedSourceQuarantinedError) as exc_info:
        service.ingest_approved_source(None, result, unapproved_candidate)

    assert exc_info.value.code == "UNAPPROVED_SOURCE_QUARANTINED"


# ==============================================================================
# 7. Negative Abuse: Malicious Payload Disguised as PDF Sanitized
# ==============================================================================
def test_negative_abuse_malicious_payload_sanitized():
    """Verify executable binaries (PE, ELF, shell) masked as PDFs are rejected."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A01.value,
        title="Tài liệu Cửu Đỉnh giả mạo",
        url="https://dsvh.gov.vn/docs/fake.pdf",
        claimed_rights=LegalRightsStatus.PUBLIC_DOMAIN,
    )

    # Windows PE executable (MZ header)
    pe_malware_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    with pytest.raises(MaliciousPayloadError) as exc1:
        service.evaluate_and_acquire(
            candidate,
            payload_bytes=pe_malware_bytes,
            declared_mime_type="application/pdf",
        )
    assert "executable (PE)" in str(exc1.value)

    # Linux ELF executable
    elf_malware_bytes = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    with pytest.raises(MaliciousPayloadError) as exc2:
        service.evaluate_and_acquire(
            candidate,
            payload_bytes=elf_malware_bytes,
            declared_mime_type="application/pdf",
        )
    assert "executable (ELF)" in str(exc2.value)

    # Shell script
    sh_bytes = b"#!/bin/bash\nrm -rf /tmp/data\n"
    with pytest.raises(MaliciousPayloadError) as exc3:
        service.evaluate_and_acquire(
            candidate,
            payload_bytes=sh_bytes,
            declared_mime_type="application/pdf",
        )
    assert "Shell script" in str(exc3.value)

    # Non-PDF random binary declared as application/pdf without %PDF- header
    random_bytes = b"CORRUPTED_NON_PDF_BINARY_DATA_HERE_1234567890"
    with pytest.raises(MaliciousPayloadError) as exc4:
        service.evaluate_and_acquire(
            candidate,
            payload_bytes=random_bytes,
            declared_mime_type="application/pdf",
        )
    assert "missing standard %PDF-" in str(exc4.value)


# ==============================================================================
# 8. Negative Abuse: Authority Impersonation Detected
# ==============================================================================
def test_negative_abuse_authority_impersonation_detected():
    """Verify blogs spoofing official museum or archival authority are blocked."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    impersonating_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A04.value,
        title="Thông tin hiện vật Cửu Đỉnh",
        authority_name="Bảo tàng Lịch sử Quốc gia",
        url="https://baotanglichsu-blog.blogspot.com/cuu-dinh-post",
        claimed_rights=LegalRightsStatus.PUBLIC_DOMAIN,
    )

    with pytest.raises(AuthorityImpersonationError) as exc_info:
        service.evaluate_and_acquire(impersonating_candidate)

    assert exc_info.value.code == "AUTHORITY_IMPERSONATION_DETECTED"
    assert "Impersonation detected" in str(exc_info.value)
    assert "blogspot.com" in str(exc_info.value)


# ==============================================================================
# 9. Rights Decision Matrix: Unknown Rights != Granted
# ==============================================================================
def test_unknown_rights_never_converted_to_granted():
    """Verify ambiguous/unknown rights are strictly quarantined and never granted."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout()

    unknown_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A07.value,
        title="Văn bản Hán Nôm chưa rõ bản quyền",
        url="https://nomfoundation.org/record/123",
        claimed_rights=LegalRightsStatus.UNKNOWN_UNREVIEWED,
    )

    res = service.evaluate_and_acquire(unknown_candidate)
    assert res.decision == AcquisitionDecision.QUARANTINED_PENDING_REVIEW
    assert res.quarantine_required is True
    assert res.public_display_allowed is False

    # Open licenses testing
    cc_by_candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A05.value,
        title="Open Research on Imperial Bronze Casting",
        url="https://doi.org/10.1000/open-cast",
        claimed_rights=LegalRightsStatus.CC_BY,
    )
    cc_res = service.evaluate_and_acquire(cc_by_candidate)
    assert cc_res.decision == AcquisitionDecision.ALLOWED_FULL
    assert cc_res.public_display_allowed is True
    assert cc_res.is_excerpt_redacted is False


# ==============================================================================
# 10. Candidate Discovery & Deduplication (P01)
# ==============================================================================
def test_p01_candidate_discovery_and_deduplication(db_session):
    """Verify URL canonicalization, DOI/ISBN normalization, and batch deduplication."""
    scout = SourceDiscoveryScout(db=db_session)

    # 1. URL Canonicalization strips tracking params
    raw_url = "https://en.unesco.org/memoryoftheworld/register/cuu-dinh/?utm_source=fb&utm_medium=cpc&ref=twitter#section1"
    canon = canonicalize_url(raw_url)
    assert canon == "https://en.unesco.org/memoryoftheworld/register/cuu-dinh"

    # 2. DOI normalization
    doi1 = normalize_doi("https://doi.org/10.1007/S00004-020-00498-8")
    doi2 = normalize_doi("doi:10.1007/s00004-020-00498-8")
    assert doi1 == "10.1007/s00004-020-00498-8"
    assert doi1 == doi2

    # 3. Create candidates with duplicate DOI and URL
    cand1 = scout.create_candidate(
        scout_role=ScoutRole.P01_A05.value,
        title="Đồng đúc thời Nguyễn",
        author_text="Nguyễn Văn A",
        publication_year=2020,
        doi="10.1007/s00004-020-00498-8",
        url="https://doi.org/10.1007/s00004-020-00498-8",
        claimed_rights=LegalRightsStatus.CC_BY,
    )

    cand2 = scout.create_candidate(
        scout_role=ScoutRole.P01_A09.value,
        title="Đồng đúc thời Nguyễn (Bản quét lại)",
        author_text="Nguyễn Văn A",
        publication_year=2020,
        doi="https://doi.org/10.1007/S00004-020-00498-8",  # duplicate DOI
        url="https://doi.org/10.1007/s00004-020-00498-8?utm_source=scholar",
        claimed_rights=LegalRightsStatus.CC_BY,
    )

    deduped = scout.deduplicate_batch([cand1, cand2], db=db_session)
    assert len(deduped) == 2
    assert deduped[0].is_duplicate is False
    assert deduped[1].is_duplicate is True
    assert deduped[1].duplicate_of_id == cand1.id
    assert deduped[1].duplicate_matched_by == "doi"


# ==============================================================================
# 11. Legal Acquisition & Database Ingestion Idempotency (P02)
# ==============================================================================
def test_p02_source_acquisition_and_db_ingestion_idempotency(db_session):
    """Verify ingestion of approved source into HistoricalSource, checksumming, and idempotency."""
    service = LegalSourceAcquisitionService()
    scout = SourceDiscoveryScout(db=db_session)

    uid = uuid.uuid4().hex[:6]
    candidate = scout.create_candidate(
        scout_role=ScoutRole.P01_A02.value,
        title=f"Đại Nam thực lục - Chính biên {uid}",
        author_text="Quốc sử quán triều Nguyễn",
        publication_year=1848,
        edition="Bản khắc mộc bản triều Tự Đức",
        source_type="chronicle",
        url=f"https://nomfoundation.org/record/dntl_{uid}",
        claimed_rights=LegalRightsStatus.PUBLIC_DOMAIN,
        provenance_notes="Bản dập mộc bản khắc in năm Tự Đức thứ 1.",
    )

    # 1. Evaluate acquisition
    sample_pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    acq_result = service.evaluate_and_acquire(
        candidate,
        payload_bytes=sample_pdf_bytes,
        declared_mime_type="application/pdf",
    )
    assert acq_result.decision == AcquisitionDecision.ALLOWED_FULL
    assert acq_result.public_display_allowed is True
    assert acq_result.snapshot is not None
    assert len(acq_result.snapshot.sha256_hash) == 64

    # 2. Ingest into HistoricalSource
    source_row = service.ingest_approved_source(db_session, acq_result, candidate)
    assert source_row.id is not None
    assert source_row.title == candidate.title
    assert source_row.verification_status == "accessible"
    assert source_row.public_display_allowed is True
    assert source_row.checksum == acq_result.snapshot.sha256_hash

    # 3. Idempotent re-ingestion of same candidate
    reingested_row = service.ingest_approved_source(db_session, acq_result, candidate)
    assert reingested_row.id == source_row.id

    # 4. Ingest copyrighted source as metadata-only
    cr_cand = scout.create_candidate(
        scout_role=ScoutRole.P01_A05.value,
        title=f"Luận án Tiến sĩ Khảo cổ Cửu Đỉnh {uid}",
        author_text="Nhà nghiên cứu XYZ",
        publication_year=2021,
        source_type="scholarly_paper",
        isbn=f"978-604-99-{uid[:4]}",
        url=f"https://doi.org/10.1234/thesis_{uid}",
        claimed_rights=LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED,
        provenance_notes="Trích đoạn luận án bảo vệ tại ĐHQG.",
    )
    cr_result = service.evaluate_and_acquire(cr_cand, payload_bytes=None)
    assert cr_result.decision == AcquisitionDecision.ALLOWED_METADATA_ONLY
    assert cr_result.public_display_allowed is False

    cr_source_row = service.ingest_approved_source(db_session, cr_result, cr_cand)
    assert cr_source_row.id is not None
    assert cr_source_row.verification_status == "rights_restricted"
    assert cr_source_row.public_display_allowed is False
    assert cr_source_row.excerpt is None  # Excerpt redacted for rights_restricted
