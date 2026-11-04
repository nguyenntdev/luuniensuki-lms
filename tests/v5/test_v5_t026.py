# -*- coding: utf-8 -*-
"""V5-T026 (Wave W02, Slot A06): Hán–Nôm Script, Reading, Romanization, and Translation Review.

Audits and verifies:
1. Hán-Nôm script data structure and reading validation:
   - Script glyphs (Hán–Nôm text).
   - Sino-Vietnamese reading (phiên âm Hán-Việt).
   - English / modern Vietnamese translation gloss.
   - Separate script, reading, translation, and review statuses.
2. Negative abuse test:
   - Guessed or unverified glyph (AI-generated, AI OCR candidate, unreviewed seed)
     CANNOT be marked verified without human epigrapher review and sign-off.
   - Missing or empty glyphs cannot be marked verified.
3. Missing Hán-Nôm tracking:
   - The 4 known incomplete motifs from the W00 audit (urn_nghi_dinh_03, urn_thuan_dinh_13,
     urn_tuyen_dinh_11, urn_huyen_dinh_12) are properly identified and tracked as missing / provisional / pending review.
   - None of the 4 are falsely accepted or marked as verified.
4. Epigraphic reading uncertainty preservation:
   - Uncertain or provisional readings are flagged as uncertain and cannot bypass validation.
5. Historical claim translation governance integration:
   - Translation and etymology historical claims created with AI-generated or uncertain
     status cannot transition to expert_verified without epigrapher review.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from sqlalchemy import select

from backend.domain.han_nom_review import (
    KNOWN_MISSING_HAN_NOM_MOTIF_IDS,
    UNREVIEWED_REVIEW_STATUSES,
    VERIFIED_REVIEW_STATUSES,
    HanNomMotifReviewRecord,
    HanNomProvenanceOrigin,
    HanNomReviewError,
    HanNomReviewInput,
    HanNomReviewStatus,
    HanNomTranslationReview,
    UnverifiedPromotionForbiddenError,
    audit_162_han_nom_dataset,
    is_valid_source_citation,
    validate_han_nom_promotion,
)
from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models import User, UserRole
from backend.services import history_governance as gov
from backend.services.heritage_import import (
    HeritageImportService,
    validate_han_nom_reviews,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _make_staff(client, db_session, email: str, display_name: str = "Epigrapher"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.admin
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _seed_entity(db_session, slug: str = "cao-dinh-01", name_vi: str = "Cao Đỉnh") -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type="relief",
        slug=slug,
        name_vi=name_vi,
        name_han_nom="高鼎",
        publication_status="draft",
    )
    db_session.add(entity)
    db_session.flush()
    return entity


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_han_nom_data_structure_and_epigraphic_attributes():
    """Verify Hán-Nôm review data structures support glyphs, reading, and translations."""
    record = HanNomMotifReviewRecord(
        motif_id="urn_cao_dinh_01",
        urn_slug="cao-dinh",
        name_vi="Cao Đỉnh",
        name_en="The Urn of Height",
        han_nom_glyphs="高鼎",
        sino_vietnamese_reading="Cao Đỉnh",
        modern_vi_meaning="Thụy hiệu Cao của vua Gia Long, đỉnh trung tâm",
        english_translation="The Urn of Height",
        review_status=HanNomReviewStatus.human_verified,
        origin=HanNomProvenanceOrigin.epigrapher_verified,
        reference_image_url="/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
        epigrapher_signoff="GS. Nguyễn Đình Hòe (Hội đồng Di sản)",
        notes="Chữ Hán chuẩn trên thân đỉnh, đối chiếu Khâm định Đại Nam hội điển sự lệ",
        is_uncertain=False,
        is_ai_guessed=False,
    )

    assert record.motif_id == "urn_cao_dinh_01"
    assert record.han_nom_glyphs == "高鼎"
    assert record.sino_vietnamese_reading == "Cao Đỉnh"
    assert record.english_translation == "The Urn of Height"
    assert record.review_status == HanNomReviewStatus.human_verified
    assert record.origin == HanNomProvenanceOrigin.epigrapher_verified
    assert record.epigrapher_signoff is not None
    assert not record.is_uncertain
    assert not record.is_ai_guessed


def test_negative_abuse_guessed_glyph_cannot_be_verified():
    """Negative Abuse Test: AI-guessed or unverified glyphs cannot be marked verified."""
    # 1. Direct validator function must raise UnverifiedPromotionForbiddenError
    with pytest.raises(UnverifiedPromotionForbiddenError) as exc_info:
        validate_han_nom_promotion(
            current_status=HanNomReviewStatus.provisional,
            target_status=HanNomReviewStatus.human_verified,
            origin=HanNomProvenanceOrigin.ai_generated,
            is_ai_guessed=True,
            epigrapher_signoff=None,  # Missing human review
            glyphs="艇",  # Hallucinated / guessed seed glyph for Cao Đỉnh
        )
    assert "cannot be marked verified without human epigrapher review" in str(exc_info.value)

    # 2. Pydantic input schema must reject promotion without epigrapher signoff
    with pytest.raises(ValidationError) as pydantic_err:
        HanNomReviewInput(
            motif_id="urn_cao_dinh_01",
            han_nom_glyphs="艇",
            sino_vietnamese_reading="Cao Đỉnh",
            review_status=HanNomReviewStatus.human_verified,
            origin=HanNomProvenanceOrigin.ai_generated,
            is_ai_guessed=True,
            epigrapher_signoff="",  # Empty signoff
        )
    assert "AI-guessed or machine-generated glyphs must never be promoted to verified" in str(pydantic_err.value)

    # 3. AI OCR candidate without epigrapher signoff is also rejected
    with pytest.raises(UnverifiedPromotionForbiddenError):
        validate_han_nom_promotion(
            current_status=HanNomReviewStatus.unreviewed,
            target_status=HanNomReviewStatus.human_verified,
            origin=HanNomProvenanceOrigin.ai_ocr_candidate,
            is_ai_guessed=False,
            epigrapher_signoff=None,
            glyphs="龍",
        )


def test_negative_abuse_empty_or_missing_glyph_cannot_be_verified():
    """Negative Abuse Test: Empty or missing glyphs cannot be promoted to verified."""
    with pytest.raises(HanNomReviewError) as exc_info:
        validate_han_nom_promotion(
            current_status=HanNomReviewStatus.missing,
            target_status=HanNomReviewStatus.human_verified,
            origin=HanNomProvenanceOrigin.epigrapher_verified,
            is_ai_guessed=False,
            epigrapher_signoff="Dr. Epigrapher",
            glyphs=None,  # No glyphs
        )
    assert "Cannot promote empty Hán-Nôm glyphs" in str(exc_info.value)

    with pytest.raises(HanNomReviewError):
        validate_han_nom_promotion(
            current_status=HanNomReviewStatus.missing,
            target_status=HanNomReviewStatus.human_verified,
            origin=HanNomProvenanceOrigin.epigrapher_verified,
            is_ai_guessed=False,
            epigrapher_signoff="Dr. Epigrapher",
            glyphs="   ",  # Blank whitespace
        )


def test_four_known_incomplete_motifs_tracked_as_missing_and_pending_review():
    """Verify that the 4 known incomplete motifs are properly identified and tracked as missing."""
    audit_result = audit_162_han_nom_dataset(DATA_DIR)

    assert audit_result["total_motifs"] == 162
    assert audit_result["with_han_nom"] == 158
    assert audit_result["missing_count"] == 4
    assert audit_result["matches_expected_missing"] is True

    missing_ids = set(audit_result["missing_ids"])
    assert missing_ids == KNOWN_MISSING_HAN_NOM_MOTIF_IDS

    # Inspect each of the 4 incomplete motifs in detail
    records_by_id = {r.motif_id: r for r in audit_result["records"]}
    expected_incomplete = {
        "urn_nghi_dinh_03": "Đàn Mộc",
        "urn_thuan_dinh_13": "Đăng Sơn Ngư",
        "urn_tuyen_dinh_11": "Đại Lãnh",
        "urn_huyen_dinh_12": "Thao Hà",
    }

    for m_id, expected_name in expected_incomplete.items():
        assert m_id in records_by_id
        rec = records_by_id[m_id]
        assert rec.name_vi == expected_name
        assert rec.han_nom_glyphs is None
        assert rec.review_status == HanNomReviewStatus.missing
        assert rec.is_uncertain is True
        assert rec.review_status != HanNomReviewStatus.human_verified


def test_uncertain_and_provisional_readings_flagged_and_preserved():
    """Verify that uncertain readings retain uncertainty flags and provisional status."""
    # When a reading is provisional or uncertain (e.g. damaged rubbing or homophone dispute)
    input_data = HanNomReviewInput(
        motif_id="urn_thuan_dinh_13",
        han_nom_glyphs="攀山魚",  # Hypothetical candidate for Đăng Sơn Ngư
        sino_vietnamese_reading="Đăng Sơn Ngư",
        review_status=HanNomReviewStatus.provisional,
        origin=HanNomProvenanceOrigin.ai_ocr_candidate,
        is_uncertain=True,
        review_notes="Dị bản khắc: chữ 'Đăng' (登) hay 'Phàn' (攀); bản dập mờ cần đối chiếu Châu bản",
    )
    assert input_data.review_status == HanNomReviewStatus.provisional
    assert input_data.is_uncertain is True
    assert "Dị bản khắc" in (input_data.review_notes or "")


def test_valid_epigrapher_promotion_passes_with_provenance():
    """Verify that legitimate epigrapher sign-off successfully promotes to human_verified."""
    # With designated epigrapher signoff, promotion must succeed without error
    validate_han_nom_promotion(
        current_status=HanNomReviewStatus.provisional,
        target_status=HanNomReviewStatus.human_verified,
        origin=HanNomProvenanceOrigin.scholarly_edition,
        is_ai_guessed=False,
        epigrapher_signoff="GS. Trần Văn Giáp - Viện Hán Nôm",
        glyphs="高鼎",
    )

    valid_input = HanNomReviewInput(
        motif_id="urn_cao_dinh_01",
        han_nom_glyphs="高鼎",
        sino_vietnamese_reading="Cao Đỉnh",
        english_translation="The Urn of Height",
        review_status=HanNomReviewStatus.human_verified,
        origin=HanNomProvenanceOrigin.epigrapher_verified,
        is_ai_guessed=False,
        epigrapher_signoff="GS. Trần Văn Giáp - Viện Hán Nôm",
        reference_image_url="/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
    )
    assert valid_input.review_status == HanNomReviewStatus.human_verified
    assert valid_input.epigrapher_signoff == "GS. Trần Văn Giáp - Viện Hán Nôm"


def test_historical_claim_translation_epigraphic_guardrail(client, db_session):
    """Verify that translation historical claims enforce epigraphic review guardrails in governance."""
    _make_staff(client, db_session, "epigrapher_admin@example.com", "Epigrapher Admin")
    entity = _seed_entity(db_session, slug="thao-ha-relief", name_vi="Thao Hà")
    db_session.commit()

    # 1. Create translation claim marked as ai_generated with uncertain confidence
    res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "translation",
            "statement_vi": "Chữ Hán của Thao Hà chưa được phiên âm xác thực trên bản rập.",
            "confidence": "uncertain",
            "verification_status": "unreviewed",
            "origin": "ai_generated",
        },
    )
    assert res.status_code == 200, res.text
    claim_id = res.json()["id"]

    # 2. Negative test: Attempting to transition this unreviewed AI translation to expert_verified MUST fail
    res_trans = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/transition",
        params={"target": "expert_verified"},
    )
    assert res_trans.status_code == 422
    assert "HISTORY_CLAIM_INVALID_TRANSITION" in res_trans.text

    # Verify claim status remained unreviewed
    claim = db_session.get(HistoricalClaim, claim_id)
    assert claim.verification_status == "unreviewed"


def test_all_158_seed_motifs_treated_as_provisional_ai_draft():
    """Verify that all 158 seed motifs with glyphs are classified as provisional and AI-guessed."""
    audit_result = audit_162_han_nom_dataset(DATA_DIR)
    records = audit_result["records"]

    with_glyphs = [r for r in records if r.han_nom_glyphs is not None]
    assert len(with_glyphs) == 158

    # Ensure none of the 158 seed motifs are prematurely marked human_verified
    for r in with_glyphs:
        assert r.review_status != HanNomReviewStatus.human_verified
        assert r.review_status != HanNomReviewStatus.verified
        assert r.is_ai_guessed is True
        assert r.review_status == HanNomReviewStatus.provisional


def test_structured_han_nom_review_schema_and_fields():
    """Verify structured Hán-Nôm review schema implements required fields and controlled statuses."""
    # 1. Unreviewed record with uncertain flag
    unreviewed = HanNomTranslationReview(
        motif_id="urn_nghi_dinh_03",
        urn_slug="nghi_dinh",
        han_nom_text=None,
        reading_quoc_ngu="Đàn Mộc",
        translation_vi="Cây Đàn hương - hương thơm vương giả, gỗ quý ngàn năm",
        translation_en="Sandalwood",
        is_uncertain=True,
        review_status=HanNomReviewStatus.unreviewed,
        origin=HanNomProvenanceOrigin.unspecified_seed,
    )
    assert unreviewed.motif_id == "urn_nghi_dinh_03"
    assert unreviewed.han_nom_text is None
    assert unreviewed.reading_quoc_ngu == "Đàn Mộc"
    assert unreviewed.translation_vi == "Cây Đàn hương - hương thơm vương giả, gỗ quý ngàn năm"
    assert unreviewed.translation_en == "Sandalwood"
    assert unreviewed.is_uncertain is True
    assert unreviewed.review_status == HanNomReviewStatus.unreviewed

    # 2. Verified record with expert review and source citation
    verified = HanNomTranslationReview(
        motif_id="urn_cao_dinh_01",
        urn_slug="cao_dinh",
        han_nom_text="高鼎",
        reading_quoc_ngu="Cao Đỉnh",
        translation_vi="Đỉnh tượng trưng cho vua Thế Tổ Cao Hoàng Đế (Gia Long)",
        translation_en="The Urn of Height",
        is_uncertain=False,
        review_status=HanNomReviewStatus.verified,
        origin=HanNomProvenanceOrigin.historical_record,
        source_citation="Khâm định Đại Nam hội điển sự lệ, quyển 162",
        epigrapher_signoff="GS. Nguyễn Đình Hòe",
    )
    assert verified.motif_id == "urn_cao_dinh_01"
    assert verified.han_nom_text == "高鼎"
    assert verified.reading_quoc_ngu == "Cao Đỉnh"
    assert verified.translation_vi is not None
    assert verified.translation_en == "The Urn of Height"
    assert not verified.is_uncertain
    assert verified.review_status == HanNomReviewStatus.verified
    assert verified.source_citation == "Khâm định Đại Nam hội điển sự lệ, quyển 162"

    # 3. Check property accessors on HanNomMotifReviewRecord
    record = HanNomMotifReviewRecord(
        motif_id="urn_cao_dinh_01",
        urn_slug="cao_dinh",
        name_vi="Cao Đỉnh",
        name_en="The Urn of Height",
        han_nom_glyphs="高鼎",
        sino_vietnamese_reading="Cao Đỉnh",
        modern_vi_meaning="Đỉnh Cao",
        english_translation="The Urn of Height",
        review_status=HanNomReviewStatus.verified,
        origin=HanNomProvenanceOrigin.epigrapher_verified,
        is_uncertain=False,
    )
    assert record.han_nom_text == "高鼎"
    assert record.reading_quoc_ngu == "Cao Đỉnh"
    assert record.translation_vi == "Đỉnh Cao"
    assert record.translation_en == "The Urn of Height"


def test_verified_motifs_require_valid_readings_and_translations():
    """Verify that motifs marked verified must have valid glyphs, readings, and translations."""
    # 1. Missing reading_quoc_ngu fails
    with pytest.raises((HanNomReviewError, ValidationError)) as err:
        HanNomTranslationReview(
            motif_id="urn_cao_dinh_01",
            han_nom_text="高鼎",
            reading_quoc_ngu="",  # Empty reading
            translation_vi="Đỉnh Cao",
            review_status=HanNomReviewStatus.verified,
            epigrapher_signoff="Dr. Epigrapher",
            source_citation="Khâm định Đại Nam hội điển sự lệ",
        )
    assert "Verified review must include a valid reading_quoc_ngu" in str(err.value)

    # 2. Missing translation_vi fails
    with pytest.raises((HanNomReviewError, ValidationError)) as err:
        HanNomTranslationReview(
            motif_id="urn_cao_dinh_01",
            han_nom_text="高鼎",
            reading_quoc_ngu="Cao Đỉnh",
            translation_vi=None,  # Missing translation
            review_status=HanNomReviewStatus.verified,
            epigrapher_signoff="Dr. Epigrapher",
            source_citation="Khâm định Đại Nam hội điển sự lệ",
        )
    assert "Verified review must include a valid translation_vi" in str(err.value)

    # 3. Uncertain cannot be verified
    with pytest.raises((HanNomReviewError, ValidationError)) as err:
        HanNomTranslationReview(
            motif_id="urn_cao_dinh_01",
            han_nom_text="高鼎",
            reading_quoc_ngu="Cao Đỉnh",
            translation_vi="Đỉnh Cao",
            is_uncertain=True,  # Disputed / uncertain
            review_status=HanNomReviewStatus.verified,
            epigrapher_signoff="Dr. Epigrapher",
            source_citation="Khâm định Đại Nam hội điển sự lệ",
        )
    assert "cannot be marked as verified" in str(err.value)


def test_negative_abuse_guessing_glyph_without_source_citation_blocked():
    """Negative Abuse Test: Guessing glyph without source citation is blocked or flagged."""
    # 1. Guessing glyph with None citation is blocked
    with pytest.raises((UnverifiedPromotionForbiddenError, ValidationError)) as err:
        HanNomTranslationReview(
            motif_id="urn_thuan_dinh_13",
            han_nom_text="攀山魚",
            reading_quoc_ngu="Đăng Sơn Ngư",
            translation_vi="Cá leo núi",
            review_status=HanNomReviewStatus.verified,
            is_ai_guessed=True,
            epigrapher_signoff="Epigrapher X",
            source_citation=None,  # Missing citation
        )
    assert "Guessing glyph without source citation is blocked or flagged" in str(err.value)

    # 2. Guessing glyph with placeholder / dummy citations is blocked
    for dummy in ("unknown", "none", "placeholder", "tbd", "todo", "dummy citation", "citation needed"):
        with pytest.raises((UnverifiedPromotionForbiddenError, ValidationError)) as err:
            HanNomTranslationReview(
                motif_id="urn_thuan_dinh_13",
                han_nom_text="攀山魚",
                reading_quoc_ngu="Đăng Sơn Ngư",
                translation_vi="Cá leo núi",
                review_status=HanNomReviewStatus.verified,
                is_ai_guessed=True,
                epigrapher_signoff="Epigrapher X",
                source_citation=dummy,
            )
        assert "Guessing glyph without source citation is blocked or flagged" in str(err.value)

    # 3. validate_han_nom_promotion blocks promotion without valid source citation
    with pytest.raises(UnverifiedPromotionForbiddenError) as err:
        validate_han_nom_promotion(
            current_status=HanNomReviewStatus.unreviewed,
            target_status=HanNomReviewStatus.verified,
            origin=HanNomProvenanceOrigin.ai_generated,
            is_ai_guessed=True,
            epigrapher_signoff="Dr. Epigrapher",
            glyphs="登",
            source_citation="none",
        )
    assert "Guessing glyph without source citation is blocked or flagged" in str(err.value)


def test_four_unconfirmed_motifs_marked_uncertain_or_unreviewed():
    """Verify that the 4 unconfirmed motifs are correctly marked is_uncertain: True and review_status: unreviewed."""
    audit_res = audit_162_han_nom_dataset(DATA_DIR)
    records = {r.motif_id: r for r in audit_res["records"]}

    unconfirmed_ids = ["urn_nghi_dinh_03", "urn_thuan_dinh_13", "urn_tuyen_dinh_11", "urn_huyen_dinh_12"]
    for m_id in unconfirmed_ids:
        assert m_id in records, f"Expected {m_id} to be in audited records"
        rec = records[m_id]
        # Must be marked is_uncertain: True
        assert rec.is_uncertain is True, f"{m_id} must have is_uncertain=True"
        # Must be marked unreviewed (or missing)
        assert rec.review_status in (HanNomReviewStatus.unreviewed, HanNomReviewStatus.missing)
        # Glyph must be None
        assert rec.han_nom_text is None
        assert rec.han_nom_glyphs is None

        # Negative abuse: attempting to verify this unconfirmed motif without glyphs and citation fails
        with pytest.raises((HanNomReviewError, ValidationError)):
            HanNomTranslationReview(
                motif_id=m_id,
                han_nom_text=None,
                reading_quoc_ngu=rec.reading_quoc_ngu,
                translation_vi=rec.translation_vi,
                review_status=HanNomReviewStatus.verified,
                epigrapher_signoff="Dr. Reviewer",
                source_citation="Đại Nam Thực Lục",
            )


def test_heritage_import_validate_han_nom_reviews_integration():
    """Verify integration between heritage_import service and Hán-Nôm review validation."""
    # 1. Validating current data directory must pass
    result = validate_han_nom_reviews(DATA_DIR)
    assert result["is_valid"] is True
    assert result["total"] == 162
    assert result["uncertain_count"] == 4
    assert result["unreviewed_count"] == 162  # Raw seed data is all provisional/unreviewed
    assert result["verified_count"] == 0

    # 2. Service method integration
    svc = HeritageImportService()
    svc_result = svc.validate_han_nom(DATA_DIR)
    assert svc_result["is_valid"] is True
    assert svc_result["total"] == 162

    # 3. Negative abuse: If a batch attempts to pass a guessed glyph as verified without citation, it is flagged
    bad_batch = [
        {
            "motif_id": "urn_nghi_dinh_03",
            "urn_slug": "nghi_dinh",
            "han_nom_text": "檀木",
            "reading_quoc_ngu": "Đàn Mộc",
            "translation_vi": "Cây Đàn Mộc",
            "review_status": "verified",
            "is_ai_guessed": True,
            "source_citation": "placeholder",  # Disqualified dummy citation
            "epigrapher_signoff": None,  # Missing human review
        }
    ]
    bad_result = validate_han_nom_reviews(bad_batch)
    assert bad_result["is_valid"] is False
    assert len(bad_result["errors"]) > 0
    assert "known unconfirmed motif" in bad_result["errors"][0] or "Negative Abuse" in bad_result["errors"][0]

