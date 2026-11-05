# -*- coding: utf-8 -*-
"""V5-T076 (Wave W07, Slot A06): P04–P06 Source/Claim Cross-Check Test Suite.

Audits and verifies:
1. Edition Normalization:
   - Canonical primary work matching (Đại Nam thực lục, Đại Nam nhất thống chí, etc.).
   - Standardizes publishers, years, volume representations, and page formats.
   - Mirror / duplicate detection: Prevents counting multiple editions of the same
     work as independent witnesses (P05 Gate: Do not count mirrors twice).
2. Claim-Source Link Binding & Negative Abuse:
   - Negative abuse: Mismatched page citations (out of range or inverted) are strictly
     rejected with MismatchedPageCitationError.
   - Negative abuse: Uncorroborated factual claims (missing locator, missing quote excerpt,
     or referencing non-existent sources) are rejected with UncorroboratedClaimCitationError.
   - Valid citations bind successfully with normalized locators and excerpts.
3. Cross-Source Contradiction Detection:
   - Identifies conflicting statements across sources.
   - Attaching a contradicting source demotes verified claims to 'disputed'.
   - Negative abuse: Disputed claims cannot auto-verify without explicit resolution.
4. Scholarly Dispute Ledger:
   - Tracks historiographical debates (e.g. relief motif identification for urn_nghi_dinh_03).
   - Invariant: Disagreements cannot be deleted or suppressed for narrative smoothness.
5. Date & Chronology Disagreement Resolution:
   - Distinguishes compatible sequential milestones (1835 start vs 1837 installation)
     from true chronological contradictions.
   - Negative abuse: Claiming exact day precision when source only provides decade precision
     is rejected with OverpreciseChronologyError.
6. Place & Historical Geography Temporal Mapping:
   - Maps 19th-century Nguyễn territory (Trấn Hải Đài, Thừa Thiên phủ) to modern correspondence.
   - Negative abuse: Asserting modern boundaries without temporal qualification is rejected
     with AnachronisticGeographyError.
7. Full Entity Cross-Check Pipeline Integration:
   - cross_check_entity_claims produces deterministic, tamper-evident CrossCheckReport.
"""
from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select

from backend.history_models import (
    AnachronisticGeographyError,
    CanonicalWork,
    CitationValidationResult,
    ContradictionRecord,
    ContradictionStatus,
    DisputeCategory,
    DisputedClaimCannotAutoVerifyError,
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalConfidence,
    HistoricalEntity,
    HistoricalSource,
    HistoricalSupportType,
    HistoricalVerificationStatus,
    MismatchedPageCitationError,
    MirrorDetectionResult,
    NormalizedEdition,
    OverpreciseChronologyError,
    ScholarlyDispute,
    ScholarlyDisputeLedger,
    UncorroboratedClaimCitationError,
    bind_claim_source_verified,
    cross_check_entity_claims,
    detect_duplicate_or_mirror_sources,
    dispute_ledger,
    normalize_edition,
    resolve_date_chronology,
    resolve_place_geography,
    validate_citation_locator,
    verify_claim_corroboration_policy,
)


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _seed_entity(
    db_session,
    slug: str = "cao-dinh",
    name_vi: str = "Cao Đỉnh",
) -> HistoricalEntity:
    ent = db_session.scalars(select(HistoricalEntity).where(HistoricalEntity.slug == slug)).first()
    if ent:
        return ent
    entity = HistoricalEntity(
        entity_type="urn",
        slug=slug,
        name_vi=name_vi,
        name_en="Cao Dinh Urn",
        name_han_nom="高鼎",
        publication_status="published",
        alternative_names=["Urn of Emperor Gia Long"],
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity


def _seed_source(
    db_session,
    title: str,
    pages: str = "350",
    author_text: str = "Quốc sử quán triều Nguyễn",
    publication_year: int = 1962,
    publisher: str = "NXB Sử học, Hà Nội",
    source_type: str = "royal_record",
) -> HistoricalSource:
    source = HistoricalSource(
        source_type=source_type,
        title=title,
        author_text=author_text,
        publisher=publisher,
        publication_year=publication_year,
        pages=pages,
        verification_status="metadata_verified",
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


def _seed_claim(
    db_session,
    entity: HistoricalEntity,
    statement_vi: str,
    claim_type: str = "factual",
    verification_status: str = "editor_reviewed",
    confidence: str = "high",
) -> HistoricalClaim:
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type=claim_type,
        statement_vi=statement_vi,
        verification_status=verification_status,
        confidence=confidence,
        origin="editorial",
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)
    return claim


# --------------------------------------------------------------------------- #
# Unit & Domain Tests
# --------------------------------------------------------------------------- #
def test_normalize_editions_and_canonical_matching():
    """Verifies edition normalization maps variants and translations to canonical works."""
    # Test variant 1: 1962 edition of Dai Nam Thuc Luc
    norm1 = normalize_edition(
        raw_title="Đại Nam thực lục chính biên đệ nhị kỷ",
        publisher="NXB Sử học",
        publication_year=1962,
        volume="Tập II",
    )
    assert norm1.work_code == "WORK-DNTL"
    assert norm1.canonical_title == "Đại Nam thực lục"
    assert norm1.volume == "II"
    assert norm1.is_canonical_match is True
    assert norm1.is_derivative is True

    # Test variant 2: Dai Nam Nhat Thong Chi
    norm2 = normalize_edition(
        raw_title="Đại Nam nhất thống chí (Bản dịch)",
        publisher="NXB Khoa học Xã hội",
        publication_year=1971,
        volume="1",
    )
    assert norm2.work_code == "WORK-DNNTC"
    assert norm2.canonical_title == "Đại Nam nhất thống chí"
    assert norm2.volume == "1"

    # Test variant 3: Museum monograph
    norm3 = normalize_edition(
        raw_title="Cửu Đỉnh Huế",
        publisher="Trung tâm Bảo tồn Di tích Cố đô Huế",
        publication_year=2012,
    )
    assert norm3.work_code == "WORK-CDH-2012"
    assert norm3.is_canonical_match is True


def test_detect_duplicate_and_mirror_sources():
    """Prevents counting reprint/derivative mirrors twice as independent corroborating witnesses (P05 Gate)."""
    src1 = {
        "id": "src-dntl-1962",
        "title": "Đại Nam thực lục - Tập 2",
        "publisher": "NXB Sử học",
        "publication_year": 1962,
    }
    src2 = {
        "id": "src-dntl-2007",
        "title": "Đại Nam thực lục chính biên (Tập 1)",
        "publisher": "NXB Giáo dục",
        "publication_year": 2007,
    }
    src3 = {
        "id": "src-dnntc-1971",
        "title": "Đại Nam nhất thống chí",
        "publisher": "NXB Khoa học Xã hội",
        "publication_year": 1971,
    }

    result: MirrorDetectionResult = detect_duplicate_or_mirror_sources([src1, src2, src3])
    # 3 total editions evaluated, but only 2 independent origins (DNTL and DNNTC)
    assert result.total_sources_evaluated == 3
    assert result.independent_origin_count == 2
    assert "WORK-DNTL" in result.mirror_groups
    assert len(result.mirror_groups["WORK-DNTL"]) == 2
    assert len(result.warnings) > 0
    assert "Counted as 1 independent origin" in result.warnings[0]


def test_mismatched_page_citation_rejected_negative_abuse():
    """NEGATIVE ABUSE: Mismatched page or out-of-bounds page citation is deterministically rejected."""
    source_mock = {
        "id": "src-book-100",
        "title": "Tư liệu Cửu Đỉnh",
        "pages": "1-120",  # Max page is 120
    }

    # Abuse 1: Page 999 exceeds known boundary of 120 pages
    with pytest.raises(MismatchedPageCitationError) as exc_info:
        validate_citation_locator(
            source=source_mock,
            locator={
                "locator_type": "page",
                "page_start": 999,
                "quotation_excerpt": "Đúc Cửu Đỉnh vào năm Minh Mạng 16",
            },
            claim_type="factual",
        )
    assert "exceeds known edition boundary" in str(exc_info.value)

    # Abuse 2: Inverted page range (page_start > page_end)
    with pytest.raises(MismatchedPageCitationError) as exc_info2:
        validate_citation_locator(
            source=source_mock,
            locator={
                "locator_type": "page",
                "page_start": 80,
                "page_end": 40,
                "quotation_excerpt": "Trích đoạn sử liệu",
            },
            claim_type="factual",
        )
    assert "cannot be less than page start" in str(exc_info2.value)

    # Abuse 3: Negative or zero page number
    with pytest.raises(MismatchedPageCitationError) as exc_info3:
        validate_citation_locator(
            source=source_mock,
            locator={
                "locator_type": "page",
                "page_start": 0,
                "quotation_excerpt": "Trích đoạn sử liệu",
            },
            claim_type="factual",
        )
    assert "must be positive" in str(exc_info3.value)


def test_uncorroborated_claim_citation_rejected_negative_abuse():
    """NEGATIVE ABUSE: Factual claim without specific locator, empty excerpt, or non-existent source is rejected."""
    source_mock = {
        "id": "src-valid-01",
        "title": "Đại Nam Thực Lục",
        "pages": "1-500",
    }

    # Abuse 1: Factual claim with empty quotation excerpt
    with pytest.raises(UncorroboratedClaimCitationError) as exc_info:
        validate_citation_locator(
            source=source_mock,
            locator={"locator_type": "page", "page_start": 45, "quotation_excerpt": ""},
            claim_type="factual",
        )
    assert "missing quote excerpt" in str(exc_info.value)

    # Abuse 2: Factual claim with missing locator
    with pytest.raises(UncorroboratedClaimCitationError) as exc_info2:
        validate_citation_locator(
            source=source_mock,
            locator={"quotation_excerpt": "Vua Minh Mạng ngự giá chiêm bái Cửu Đỉnh"},
            claim_type="factual",
        )
    assert "missing specific locator" in str(exc_info2.value)

    # Abuse 3: verify_claim_corroboration_policy rejects claim without any bindings
    claim_mock = {"id": "claim-unsupported", "claim_type": "factual", "statement_vi": "Khẳng định không có nguồn"}
    with pytest.raises(UncorroboratedClaimCitationError) as exc_info3:
        verify_claim_corroboration_policy(claim=claim_mock, bindings=[], sources_by_id={})
    assert "0 source bindings" in str(exc_info3.value)


def test_successful_claim_source_binding_and_locator_validation():
    """Positive flow: Valid citation locator normalizes cleanly."""
    source_mock = {
        "id": "src-valid-02",
        "title": "Khâm định Đại Nam hội điển sự lệ",
        "pages": "1-600",
    }
    result: CitationValidationResult = validate_citation_locator(
        source=source_mock,
        locator={
            "locator_type": "page_range",
            "page_start": 45,
            "page_end": 48,
            "volume": "2",
            "quotation_excerpt": "Năm Minh Mạng thứ 16, mùa đông tháng 10 đúc Cửu Đỉnh",
        },
        claim_type="factual",
    )
    assert result.is_valid is True
    assert result.page_start == 45
    assert result.page_end == 48
    assert result.volume == "2"
    assert result.normalized_locator == "Tập 2, tr. 45-48"


def test_cross_source_contradiction_detection_and_auto_demotion(db_session):
    """Verifies contradiction detection and automatic demotion of verified claims upon attaching contradicting source."""
    entity = _seed_entity(db_session, slug=f"test-urn-{uuid.uuid4().hex[:6]}")
    source_sup = _seed_source(db_session, title="Đại Nam Thực Lục", pages="1-400")
    source_contra = _seed_source(db_session, title="Dị khảo sử học phương Tây thế kỷ 19", pages="1-200")

    claim = _seed_claim(
        db_session,
        entity=entity,
        statement_vi="Cao Đỉnh được đúc và hoàn thành dưới triều vua Minh Mạng.",
        verification_status="expert_verified",
        confidence="high",
    )

    # Attach supporting source
    bind_claim_source_verified(
        db_session,
        claim_id=claim.id,
        source_id=source_sup.id,
        support_type="supports",
        locator={"page_start": 12, "quotation_excerpt": "Minh Mạng năm thứ 16 khởi đúc"},
    )
    assert claim.verification_status == "expert_verified"

    # Now attach contradicting source (e.g. claim that it was cast under a different reign)
    bind_claim_source_verified(
        db_session,
        claim_id=claim.id,
        source_id=source_contra.id,
        support_type="contradicts",
        locator={"page_start": 55, "quotation_excerpt": "Có thuyết ghi nhận khác về niên đại đúc"},
    )
    db_session.refresh(claim)

    # Invariant: Claim must be immediately demoted to 'disputed'
    assert claim.verification_status == "disputed"
    assert claim.confidence == "disputed"
    assert "Automatically demoted to disputed" in claim.review_notes

    # Negative check: Claim cannot be auto-verified while disputed
    ledger = ScholarlyDisputeLedger()
    with pytest.raises(DisputedClaimCannotAutoVerifyError):
        ledger.assert_can_verify(claim, entity.slug)


def test_scholarly_dispute_ledger_tracking():
    """Verifies that scholarly disputes are tracked and preserved without suppression (P06-A07)."""
    ledger = ScholarlyDisputeLedger()
    subject_slug = "urn_nghi_dinh_03"

    dispute: ScholarlyDispute = ledger.register_dispute(
        topic="Identification of Urn Relief urn_nghi_dinh_03 (Kiển thảo vs Kén tằm)",
        category=DisputeCategory.IDENTIFICATION_NAMING,
        subject_slug=subject_slug,
        contending_claims=[
            {"id": "claim-01", "statement_vi": "Hình tượng đại diện cho loài cỏ kiển thảo."},
            {"id": "claim-02", "statement_vi": "Hình tượng đại diện cho tổ kén tằm và ngành tơ lụa."},
        ],
        contending_sources=[
            {"id": "src-01", "title": "Cửu Đỉnh Huế (2012)"},
            {"id": "src-02", "title": "Khảo cứu thực vật học thời Nguyễn"},
        ],
        scholarly_positions=[
            {"scholar": "Trung tâm BTTD Cố đô Huế", "position": "Kiển thảo (cỏ kiển)"},
            {"scholar": "Hội đồng nghiên cứu Hán Nôm", "position": "Tổ kén (tằm dệt)"},
        ],
    )

    assert dispute.status == ContradictionStatus.SCHOLARLY_DISPUTED
    assert dispute.epistemic_certainty == "contested"
    assert ledger.has_unresolved_dispute(subject_slug) is True

    # Assert that neither contending claim can be auto-verified
    with pytest.raises(DisputedClaimCannotAutoVerifyError) as exc_info:
        ledger.assert_can_verify({"id": "claim-01", "claim_type": "factual"}, subject_slug)
    assert "has unresolved scholarly dispute" in str(exc_info.value)


def test_chronology_resolution_and_precision_abuse():
    """Verifies sequential milestone differentiation and blocks overprecise chronology assertions."""
    # Scenario 1: Sequential distinct milestones (1835 start vs 1837 installation) -> Compatible
    res_milestones = resolve_date_chronology(
        date_a_spec={"milestone": "khởi đúc", "reign_era": "Minh Mạng", "reign_year": 16, "date_precision": "year"},
        date_b_spec={"milestone": "đặt trước Thế Miếu", "reign_era": "Minh Mạng", "reign_year": 18, "date_precision": "year"},
    )
    assert res_milestones["is_compatible"] is True
    assert res_milestones["status"] == "COMPATIBLE_SEQUENTIAL_MILESTONES"

    # Scenario 2: Chronological contradiction (conflicting years on the SAME milestone)
    res_conflict = resolve_date_chronology(
        date_a_spec={"milestone": "khởi đúc", "year": 1835, "date_precision": "year"},
        date_b_spec={"milestone": "khởi đúc", "year": 1840, "date_precision": "year"},
    )
    assert res_conflict["is_compatible"] is False
    assert res_conflict["status"] == "CHRONOLOGY_CONTRADICTION"

    # Scenario 3: Negative abuse - Overprecise assertion
    with pytest.raises(OverpreciseChronologyError) as exc_info:
        resolve_date_chronology(
            date_a_spec={
                "milestone": "khởi công",
                "source_precision": "decade",
                "asserted_precision": "exact_day",
            },
            date_b_spec={"milestone": "khởi công"},
        )
    assert "Overprecise chronology error" in str(exc_info.value)


def test_geography_temporal_mapping_and_anachronism_abuse():
    """Verifies temporal mapping of historical places and blocks anachronistic modern geography projection."""
    # Scenario 1: Valid historical mapping of Trấn Hải Đài
    geo_res = resolve_place_geography(
        historical_place_name="Trấn Hải Đài",
        modern_correspondence_claimed="Cửa Thuận An, Thừa Thiên Huế",
    )
    assert geo_res["mapping_status"] == "verified"
    assert geo_res["historical_province"] == "Thừa Thiên phủ"
    assert "Cửa Thuận An" in geo_res["modern_name"]

    # Scenario 2: Negative abuse - projecting modern provincial administration without temporal qualifier
    with pytest.raises(AnachronisticGeographyError) as exc_info:
        resolve_place_geography(
            historical_place_name="Hải Vân Quan",
            modern_correspondence_claimed="Tỉnh Thừa Thiên Huế",  # Missing boundary qualifier / temporal note
            allow_anachronism=False,
        )
    assert "Anachronistic geography" in str(exc_info.value)


def test_end_to_end_entity_cross_check_pipeline(db_session):
    """End-to-end integration test: Verifies cross_check_entity_claims on database rows."""
    slug = f"e2e-urn-{uuid.uuid4().hex[:6]}"
    entity = _seed_entity(db_session, slug=slug, name_vi="Thuần Đỉnh")

    # Seed 2 mirror sources (DNTL 1962 and 2007) and 1 distinct source (DNNTC)
    s1 = _seed_source(db_session, title="Đại Nam thực lục - Tập 2 (1962)", pages="1-400", publication_year=1962)
    s2 = _seed_source(db_session, title="Đại Nam thực lục chính biên (2007)", pages="1-420", publication_year=2007)
    s3 = _seed_source(db_session, title="Đại Nam nhất thống chí", pages="1-350", publication_year=1971)

    # Seed 2 approved claims
    c1 = _seed_claim(db_session, entity, "Thuần Đỉnh là đỉnh thứ sáu trong Cửu Đỉnh.", verification_status="published")
    c2 = _seed_claim(db_session, entity, "Trên Thuần Đỉnh có chạm khắc sông Vĩnh Tế.", verification_status="published")

    # Bind claim 1 to mirror sources s1 and s2
    bind_claim_source_verified(
        db_session, c1.id, s1.id, "supports",
        {"page_start": 30, "page_end": 32, "quotation_excerpt": "Thuần Đỉnh khắc hình sông núi đại danh"}
    )
    bind_claim_source_verified(
        db_session, c1.id, s2.id, "supports",
        {"page_start": 35, "page_end": 37, "quotation_excerpt": "Thuần Đỉnh khắc hình sông núi đại danh"}
    )

    # Bind claim 2 to source s3
    bind_claim_source_verified(
        db_session, c2.id, s3.id, "supports",
        {"page_start": 100, "page_end": 102, "quotation_excerpt": "Kênh Vĩnh Tế ghi khắc trên Thuần Đỉnh"}
    )

    # Execute full cross-check
    report = cross_check_entity_claims(db_session, entity_slug=slug)

    assert report.entity_slug == slug
    assert report.total_claims == 2
    assert report.total_sources == 3
    # Invariant: 3 sources evaluated, but exactly 2 independent origins due to DNTL mirror detection
    assert report.independent_sources_count == 2
    assert report.mirror_sources_detected == 1
    assert report.verified_citations == 3
    assert report.contradictions_detected == 0
    assert report.is_fully_corroborated is True
    assert len(report.summary_sha256) == 64
