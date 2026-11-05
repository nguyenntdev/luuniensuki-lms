# -*- coding: utf-8 -*-
"""V5-T075 (Wave W07, Slot A05): P03 Extraction and Hán–Nôm Uncertainty Engine Test Suite.

Audits and verifies:
1. Document Parsing & Structure (P03-A01):
   - Chapter, volume, page, footnote extraction from verified PDF sources.
   - Negative abuse: Scrambled or invalid column reading order raises ColumnReadingOrderError.
2. Printed Vietnamese OCR (P03-A02):
   - Text extraction with confidence score and bounding boxes.
   - Negative abuse: Diacritic stripping that distorts semantic meaning raises DiacriticCorruptionError.
3. Han Glyph Detection (P03-A04):
   - Region bounding boxes on rubbings and stone inscriptions.
   - Negative abuse: Surface scratches / noise misidentified as glyph raises NoiseArtifactDetectedError.
4. Han-Nom Transcription Proposer & Uncertainty Engine (P03-A05):
   - Candidate glyph proposal with Sino-Vietnamese reading, bounding boxes, and uncertainty flags.
   - Mandatory human original script review flag.
   - Negative abuse: Low-confidence glyph (<0.90) CANNOT auto-publish or be marked canonical
     without explicit human epigrapher approval (UnverifiedGlyphAutoPublishForbiddenError).
   - Missing or placeholder source citations strictly block publication.
5. Edition Collation & Layout Locator (P03-A06, P03-A07):
   - Preserves variant readings across editions without silent smoothing.
   - Layout mapping between printed folios (e.g. '14a') and PDF page index.
   - Negative abuse: Mismatched printed page numbers raise MismatchedPrintedPageError.
6. Figure & Caption Extraction (P03-A08):
   - Distinguishes authentic imperial inscriptions from archival watermarks and rubber stamps.
   - Negative abuse: Watermark misidentified as artifact inscription raises WatermarkMisidentifiedAsRelicLabelError.
7. Quality Assessment & Envelope Integrity (P03-A09, P03-A10):
   - Rejects ungrounded claims of 100% OCR accuracy (AssumedPerfectAccuracyForbiddenError).
   - Cryptographic envelope building with SHA-256 parent lineage enforcement (SnapshotLineageDisconnectedError).
8. Cross-Image Epigraphic Checks:
   - Compares 2D rubbings, photogrammetry models, and woodblock printings for glyph congruence.
9. Missing Hán–Nôm Tracking:
   - Proper identification and handling of the 4 known incomplete motifs from W00/W02 baseline.
10. Database Persistence & Audit Integration:
    - Verifies persistence of extraction artifacts and review records in DB models.
"""
from __future__ import annotations

import hashlib
import json
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.domain.han_nom_review import (
    KNOWN_MISSING_HAN_NOM_MOTIF_IDS,
    HanNomReviewStatus,
)
from backend.history_models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
)
from backend.research_factory_models import (
    ResearchEvidenceResult,
    ResearchJob,
    ResearchJobStatus,
    ResearchPhase,
    ResearchPhaseCode,
    ResearchPhaseStatus,
    ResearchRun,
)
from backend.services.research_factory import (
    AssumedPerfectAccuracyForbiddenError,
    BoundingBox,
    ColumnReadingOrderError,
    CrossImageEpigraphicMatch,
    DiacriticCorruptionError,
    DocumentStructureParser,
    EditionCollationAssistant,
    ExtractionEnvelope,
    ExtractionIntegrityAuditor,
    FigureCaptionExtractor,
    GlyphCandidate,
    HanGlyphDetector,
    HanNomExtractionService,
    HanNomTranscriptionProposer,
    LayoutLocator,
    LayoutLocatorMapper,
    MismatchedPrintedPageError,
    NoiseArtifactDetectedError,
    OCRQualityChecker,
    P03ExtractionError,
    SilentVariantCorrectionForbiddenError,
    SnapshotLineageDisconnectedError,
    UnverifiedGlyphAutoPublishForbiddenError,
    VietnamesePrintedOCR,
    WatermarkMisidentifiedAsRelicLabelError,
    han_nom_extraction_service,
)


# ==============================================================================
# 1. P03-A01: Document Structure & Column Reading Order
# ==============================================================================
def test_p03_a01_document_structure_parsing():
    """Verify chapter/volume extraction and column order enforcement."""
    # Positive case: valid vertical column flow
    res = DocumentStructureParser.parse("Quyển 1: Cao Đỉnh chi giám...", columns_layout="vertical_right_to_left")
    assert res["parsed"] is True
    assert "Quyển 1" in res["chapters"]

    # Negative abuse case: scrambled reading order must fail
    with pytest.raises(ColumnReadingOrderError) as exc_info:
        DocumentStructureParser.parse(
            "Scrambled text stream",
            columns_layout="scrambled_reading_order",
            source_id="src_woodblock_01",
        )
    assert exc_info.value.code == "INVALID_COLUMN_READING_ORDER"
    assert "reading order" in str(exc_info.value).lower()


# ==============================================================================
# 2. P03-A02: Vietnamese Printed OCR & Diacritic Preservation
# ==============================================================================
def test_p03_a02_vietnamese_ocr_and_diacritic_protection():
    """Verify diacritic preservation and guard against stripped diacritic corruption."""
    # Positive case
    text_vi = "Họa tiết trên Nhân Đỉnh biểu trưng cho sự trường tồn của xã tắc."
    res = VietnamesePrintedOCR.extract_text(text_vi, confidence=0.96)
    assert res["diacritics_intact"] is True
    assert res["confidence"] == 0.96

    # Negative abuse case: dropped diacritics corrupting relic name
    with pytest.raises(DiacriticCorruptionError) as exc_info:
        VietnamesePrintedOCR.extract_text(
            "Mo ta ve Nhan Dinh va Cuu Dinh trieu Nguyen",
            source_id="src_monograph_42",
        )
    assert exc_info.value.code == "VIETNAMESE_DIACRITIC_CORRUPTED"
    assert "diacritic loss" in str(exc_info.value).lower()


# ==============================================================================
# 3. P03-A04: Han Glyph Region Detection & Rubbing Noise Filtering
# ==============================================================================
def test_p03_a04_han_glyph_detection_and_noise_filtering():
    """Verify glyph localization while filtering rubbing scratches and patina noise."""
    # Positive case
    clean_rubbing = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR_CLEAN_RUBBING"
    boxes = HanGlyphDetector.detect_regions(clean_rubbing, is_background_noise=False)
    assert len(boxes) == 1
    assert isinstance(boxes[0], BoundingBox)
    assert boxes[0].x == 0.1

    # Negative abuse case: surface scratch falsely detected as Han character
    noisy_scratch = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR_BRONZE_SCRATCH"
    with pytest.raises(NoiseArtifactDetectedError) as exc_info:
        HanGlyphDetector.detect_regions(noisy_scratch, is_background_noise=True, source_id="rubbing_nhan_dinh_07")
    assert exc_info.value.code == "NOISE_ARTIFACT_DETECTED_AS_GLYPH"


# ==============================================================================
# 4. P03-A05: Han-Nom Transcription Proposer & Negative Abuse Guardrail
# ==============================================================================
def test_p03_a05_low_confidence_glyph_auto_publish_blocked():
    """Negative abuse test: Low-confidence or unreviewed glyph cannot auto-publish without human epigrapher."""
    locator = LayoutLocator(pdf_page_index=15, printed_page_number="14b")

    # 1. Low confidence candidate proposal (flagged with uncertainty)
    candidate = han_nom_extraction_service.process_han_nom_extraction(
        character="鼎",
        confidence_score=0.74,
        locator=locator,
        sino_vietnamese_reading="Đỉnh",
        is_human_reviewed=False,
        human_epigrapher=None,
        attempt_auto_publish=False,
    )
    assert candidate.uncertainty_flag is True
    assert candidate.review_status == HanNomReviewStatus.uncertain.value
    assert "below required" in candidate.uncertainty_reason

    # 2. Attempting auto-publishing low confidence glyph without epigrapher review MUST fail
    with pytest.raises(UnverifiedGlyphAutoPublishForbiddenError) as exc_info:
        han_nom_extraction_service.process_han_nom_extraction(
            character="鼎",
            confidence_score=0.74,
            locator=locator,
            sino_vietnamese_reading="Đỉnh",
            is_human_reviewed=False,
            human_epigrapher=None,
            source_citation="Đại Nam Thực Lục Chính Biên, Quyển 120",
            attempt_auto_publish=True,
        )
    assert exc_info.value.code == "LOW_CONFIDENCE_GLYPH_AUTO_PUBLISH_FORBIDDEN"
    assert "cannot be auto-published" in str(exc_info.value)

    # 3. Even with high AI confidence (0.98), unreviewed glyph CANNOT auto-publish without human epigrapher
    with pytest.raises(UnverifiedGlyphAutoPublishForbiddenError) as exc_info2:
        han_nom_extraction_service.process_han_nom_extraction(
            character="龜",
            confidence_score=0.98,
            locator=locator,
            sino_vietnamese_reading="Quy",
            is_human_reviewed=False,
            human_epigrapher=None,
            source_citation="Khâm Định Đại Nam Hội Điển Sự Lệ, Tập 3",
            attempt_auto_publish=True,
        )
    assert exc_info2.value.code == "LOW_CONFIDENCE_GLYPH_AUTO_PUBLISH_FORBIDDEN"

    # 4. Attempting auto-publishing with placeholder/fabricated source citation MUST fail
    with pytest.raises(UnverifiedGlyphAutoPublishForbiddenError) as exc_info3:
        han_nom_extraction_service.process_han_nom_extraction(
            character="龜",
            confidence_score=0.95,
            locator=locator,
            sino_vietnamese_reading="Quy",
            is_human_reviewed=True,
            human_epigrapher="Dr. Nguyen (Epigrapher)",
            source_citation="citation needed",
            attempt_auto_publish=True,
        )
    assert "without a valid, non-placeholder source citation" in str(exc_info3.value)

    # 5. Legitimate human epigrapher approval with valid citation passes
    verified_candidate = han_nom_extraction_service.process_han_nom_extraction(
        character="龜",
        confidence_score=0.95,
        locator=locator,
        sino_vietnamese_reading="Quy",
        is_human_reviewed=True,
        human_epigrapher="GS. Trần Văn Giáp (Chuyên gia Hán Nôm)",
        source_citation="Đại Nam Thực Lục Chính Biên, Đệ Nhị Kỷ, Quyển 120, Tr. 15",
        attempt_auto_publish=True,
    )
    assert verified_candidate.review_status == HanNomReviewStatus.human_verified.value
    assert verified_candidate.is_human_reviewed is True
    assert verified_candidate.human_epigrapher_reviewer == "GS. Trần Văn Giáp (Chuyên gia Hán Nôm)"


# ==============================================================================
# 5. P03-A06 & P03-A07: Edition Collation & Layout Locator Mapping
# ==============================================================================
def test_p03_edition_collation_and_page_mapping():
    """Verify variant collation and digital page to printed folio alignment."""
    # Collation without silent smoothing
    res = EditionCollationAssistant.compare_variants(
        edition_a="Cao Đỉnh",
        edition_b="Cao Đảnh",
        silently_harmonize=False,
    )
    assert res["has_variants"] is True
    assert res["discrepancy_preserved"] is True

    # Silent smoothing attempt blocked
    with pytest.raises(SilentVariantCorrectionForbiddenError):
        EditionCollationAssistant.compare_variants(
            edition_a="Bản Nội Các 1848",
            edition_b="Bản Quốc Sử Quán 1909",
            silently_harmonize=True,
        )

    # Layout locator mapping
    locator = LayoutLocatorMapper.map_locator(pdf_index=45, printed_folio="Tr. 33")
    assert locator.pdf_page_index == 45
    assert locator.printed_page_number == "Tr. 33"

    # Divergence error
    with pytest.raises(MismatchedPrintedPageError) as exc_info:
        LayoutLocatorMapper.map_locator(pdf_index=45, printed_folio="Tr. 120", divergence_detected=True)
    assert exc_info.value.code == "MISMATCHED_PRINTED_PAGE_LOCATOR"


# ==============================================================================
# 6. P03-A08: Figure & Caption Extraction (Watermark Protection)
# ==============================================================================
def test_p03_a08_watermark_misidentification_blocked():
    """Verify archive stamps and copyright watermarks are not taken as relic inscriptions."""
    # Valid authentic caption
    clean_cap = FigureCaptionExtractor.extract_caption("Bản dập chữ Hán: Long Mã tại Cao Đỉnh")
    assert "Long Mã" in clean_cap

    # Watermark mistaken for relic label MUST fail
    with pytest.raises(WatermarkMisidentifiedAsRelicLabelError) as exc_info:
        FigureCaptionExtractor.extract_caption("Vietnam National Archives Copyright 2024 - Do not copy")
    assert exc_info.value.code == "WATERMARK_MISIDENTIFIED_AS_RELIC_LABEL"


# ==============================================================================
# 7. P03-A09 & P03-A10: OCR Quality Assessment & Cryptographic Lineage
# ==============================================================================
def test_p03_ocr_quality_and_lineage_envelope():
    """Verify quality checks and cryptographic parent snapshot lineage."""
    # Self-proclaimed 100% accuracy with non-zero error rate MUST fail
    with pytest.raises(AssumedPerfectAccuracyForbiddenError) as exc_info:
        OCRQualityChecker.evaluate_quality(sample_cer=0.03, claimed_accuracy=1.0)
    assert exc_info.value.code == "ASSUMED_PERFECT_ACCURACY_FORBIDDEN"

    # Valid quality assessment
    q = OCRQualityChecker.evaluate_quality(sample_cer=0.02, claimed_accuracy=0.98)
    assert q["accuracy_validated"] is True
    assert q["cer"] == 0.02

    # Envelope building with cryptographic verification
    source_sha = hashlib.sha256(b"source_pdf_v1_bytes").hexdigest()
    findings = [{"subject_id": "urn_cao_dinh_01", "locator": "Tr. 14", "text": "Cao Đỉnh"}]

    envelope = ExtractionIntegrityAuditor.build_envelope(
        run_id="run_p03_test",
        agent_index=10,
        agent_role="P03-A10 Extraction integrity auditor",
        findings=findings,
        uncertainty=[],
        source_snapshot_hash=source_sha,
        calculated_parent_hash=source_sha,
    )
    assert envelope.artifact_sha256 is not None
    assert envelope.source_version_refs == [source_sha]

    # Tampered snapshot hash MUST fail
    with pytest.raises(SnapshotLineageDisconnectedError) as exc_info2:
        ExtractionIntegrityAuditor.build_envelope(
            run_id="run_p03_test",
            agent_index=10,
            agent_role="P03-A10 Extraction integrity auditor",
            findings=findings,
            uncertainty=[],
            source_snapshot_hash=source_sha,
            calculated_parent_hash="tampered_hash_0000000000000000",
        )
    assert exc_info2.value.code == "SNAPSHOT_LINEAGE_DISCONNECTED"


# ==============================================================================
# 8. Cross-Image Epigraphic Checks (Rubbing vs 3D vs Woodblock)
# ==============================================================================
def test_cross_image_epigraphic_congruence():
    """Verify comparison across 2D rubbing, 3D photogrammetry mesh, and woodblock print."""
    rubbing_hash = hashlib.sha256(b"rubbing_glyph").hexdigest()
    photo_hash = hashlib.sha256(b"3d_photogrammetry_glyph").hexdigest()
    woodblock_hash = hashlib.sha256(b"woodblock_glyph").hexdigest()

    # Congruent match
    match = han_nom_extraction_service.verify_cross_image_epigraphy(
        target_motif_id="urn_cao_dinh_01",
        relic_reading="Cao Đỉnh",
        rubbing_hash=rubbing_hash,
        photo_hash=photo_hash,
        woodblock_hash=woodblock_hash,
        force_discrepancy=False,
    )
    assert match.is_epigraphically_congruent is True
    assert match.discrepancy_notes is None

    # Discrepant match preserved
    discrepant = han_nom_extraction_service.verify_cross_image_epigraphy(
        target_motif_id="urn_cao_dinh_01",
        relic_reading="Cao Đỉnh",
        rubbing_hash=rubbing_hash,
        photo_hash=photo_hash,
        woodblock_hash=woodblock_hash,
        force_discrepancy=True,
    )
    assert discrepant.is_epigraphically_congruent is False
    assert "Stroke variation" in discrepant.discrepancy_notes


# ==============================================================================
# 9. Missing Hán–Nôm Tracking (4 Incomplete Motifs)
# ==============================================================================
def test_known_incomplete_motifs_tracking():
    """Verify the 4 motifs lacking glyphs are tracked as missing and require epigrapher signoff."""
    for motif_id in KNOWN_MISSING_HAN_NOM_MOTIF_IDS:
        audit = han_nom_extraction_service.audit_known_uncertainties(motif_id)
        assert audit["is_known_missing"] is True
        assert audit["status"] == HanNomReviewStatus.missing.value
        assert audit["requires_epigrapher_signoff"] is True


# ==============================================================================
# 10. Database Persistence & Pipeline Integration
# ==============================================================================
def test_p03_database_persistence_and_job_evidence(db_session: Session):
    """Verify ResearchRun -> ResearchPhase (P03) -> ResearchJob (P03-A05) -> ResearchEvidenceResult persistence."""
    # 1. Create Run
    run = ResearchRun(
        mode="STRICT_PRODUCTION",
        content_scope="NINE_URNS",
        subject_type="RELIEF",
        subject_id="urn_nhan_dinh_01",
        status="RUNNING",
    )
    db_session.add(run)
    db_session.flush()

    # 2. Create P03 Phase
    p03_phase = ResearchPhase(
        run_id=run.id,
        phase_code=ResearchPhaseCode.P03.value,
        phase_order=3,
        wave=1,
        status=ResearchPhaseStatus.RUNNING.value,
        input_manifest_sha256="abc123inputmanifest",
        barrier_passed=False,
    )
    db_session.add(p03_phase)
    db_session.flush()

    # 3. Create Job for P03-A05
    job_p03_a05 = ResearchJob(
        phase_id=p03_phase.id,
        agent_index=5,
        slot_number=5,
        role_key="P03-A05",
        agent_role="P03-A05 Han-Nom transcription proposer",
        idempotency_key=f"run_{run.id}_P03_A05_{uuid.uuid4().hex[:6]}",
        status=ResearchJobStatus.SUCCEEDED.value,
    )
    db_session.add(job_p03_a05)
    db_session.flush()

    # 4. Extract verified glyph and create EvidenceResult
    locator = LayoutLocator(pdf_page_index=22, printed_page_number="Tr. 18a")
    candidate = han_nom_extraction_service.process_han_nom_extraction(
        character="神龜",
        confidence_score=0.96,
        locator=locator,
        sino_vietnamese_reading="Thần Quy",
        is_human_reviewed=True,
        human_epigrapher="Dr. Le Van (Nom Specialist)",
        source_citation="Đại Nam Thực Lục Chính Biên, Đệ Nhị Kỷ, Quyển 120",
        attempt_auto_publish=True,
    )

    envelope = ExtractionIntegrityAuditor.build_envelope(
        run_id=str(run.id),
        agent_index=5,
        agent_role="P03-A05 Han-Nom transcription proposer",
        findings=[candidate.model_dump()],
        uncertainty=[],
        source_snapshot_hash="src_snapshot_sha256_mock",
    )

    ev_result = ResearchEvidenceResult(
        job_id=job_p03_a05.id,
        schema_version="source_passages/v1",
        output_schema="GlyphCandidate",
        artifact_sha256=envelope.artifact_sha256,
        status="SUCCEEDED",
        source_ids=["src_dntlc_120"],
        claim_ids=["claim_than_quy_01"],
        evidence_locator_ids=["Tr. 18a"],
        raw_envelope=envelope.model_dump(),
    )
    db_session.add(ev_result)
    db_session.flush()

    # 5. Verify records in DB
    db_phase = db_session.execute(select(ResearchPhase).where(ResearchPhase.id == p03_phase.id)).scalar_one()
    assert db_phase.phase_code == "P03"

    db_job = db_session.execute(select(ResearchJob).where(ResearchJob.id == job_p03_a05.id)).scalar_one()
    assert db_job.role_key == "P03-A05"

    db_ev = db_session.execute(select(ResearchEvidenceResult).where(ResearchEvidenceResult.id == ev_result.id)).scalar_one()
    assert db_ev.schema_version == "source_passages/v1"
    assert db_ev.raw_envelope["findings"][0]["character"] == "神龜"
    assert db_ev.raw_envelope["findings"][0]["human_epigrapher_reviewer"] == "Dr. Le Van (Nom Specialist)"
