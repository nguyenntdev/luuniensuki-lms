# -*- coding: utf-8 -*-
"""V5-T077 (Wave W07, Slot A07): P07–P08 Full Narrative + Lesson Draft & Independent QA Test Suite.

Audits and verifies:
1. P07 Narrative Generation:
   - Full bilingual narrative sections (VI/EN) generated strictly from verified claims.
   - Sentence-level source binding: Every single factual sentence bound to claim_id, source_id, locator, and title.
   - Museum label (VI/EN) with verified word count and primary claim citation.
2. P07 Hán-Nôm & 3D Interactive Script:
   - Reviewed Hán-Nôm editorial notes with glyph provenance.
   - 3D/AR narration script with mandatory 2D rubbing fallback.
3. P07 ELLO 6-Step Inquiry Lesson & 4-Level Rubric:
   - 6 pedagogical inquiry steps: hook, observation, source_analysis, synthesis, reflection, evaluation.
   - Explicit evidence requirement and citation enforcement on every task.
   - 4-level rubric (0-3 criteria scale) across mastery dimensions.
   - Factual quiz items locked to verified sources.
4. Content Bundle Assembly:
   - Assembly of all 9 drafting outputs into ContentBundleDraft with deterministic SHA-256.
5. Negative Abuse Gating ("No source -> no invented fact"):
   - Zero unsourced assertions: Injected sentence without source triggers P0_BLOCKER (UNSOURCED_FACTUAL_ASSERTION) and GATE_BLOCKED.
   - Invented facts in English narrative trigger P0_BLOCKER (UNSUPPORTED_EN_FACT) and GATE_BLOCKED.
   - Quizzes on disputed claims trigger P0_BLOCKER (QUIZ_ON_DISPUTED_CLAIM) and GATE_BLOCKED.
   - Inquiry tasks missing citation trigger P0_BLOCKER (MISSING_EVIDENCE_REQUIREMENT) and GATE_BLOCKED.
   - 3D script missing 2D rubbing fallback triggers P0_BLOCKER (MISSING_2D_FALLBACK) and GATE_BLOCKED.
   - Unverified Hán–Nôm glyph triggers P0_BLOCKER (UNVERIFIED_HAN_NOM_GLYPH) and GATE_BLOCKED.
   - Fabricated page locator triggers P0_BLOCKER (FABRICATED_CITATION_LOCATOR) and GATE_BLOCKED.
   - Chronological contradiction triggers P0_BLOCKER (CHRONOLOGICAL_CONTRADICTION) and GATE_BLOCKED.
6. Positive P08 QA:
   - Clean verified bundle passes all 10 checkers with zero P0 blockers (GATE_PASSED).
7. Database Integration:
   - Full persistence into ResearchRun, ResearchPhase (P07 & P08), ResearchJob, and ResearchEvidenceResult.
   - build_dossier_from_entity builds authoritative dossier from seeded DB models.
"""
from __future__ import annotations

import copy
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from backend.research_factory_models import (
    ResearchEvidenceResult,
    ResearchJob,
    ResearchPhase,
    ResearchPhaseCode,
    ResearchPhaseStatus,
    ResearchRun,
)
from backend.services.research_factory import (
    AssessmentRubricPack,
    ContentBundleDraft,
    DisputedClaimQuizError,
    DossierAsset2D,
    DossierAsset3D,
    DossierClaim,
    DossierHanNomRecord,
    DossierSource,
    DossierSourceBinding,
    DraftNarrativeEN,
    DraftNarrativeVI,
    ELLOLessonDraft,
    HanNomEditorialNote,
    InteractiveScript3D,
    InventedFactError,
    Missing2DFallbackError,
    MissingEvidenceRequirementError,
    MuseumLabel,
    NarrativeSection,
    P07DraftingError,
    P07LessonWriter,
    P07NarrativeWriter,
    P08IndependentQARunner,
    QAFindingsReport,
    QAGateStatus,
    QASeverity,
    ResearchDossier,
    SentenceClaimRef,
    UnsourcedAssertionError,
    UnverifiedGlyphError,
    assemble_content_bundle,
    build_dossier_from_entity,
    generate_narrative_and_lesson_draft,
    persist_factory_phase_results,
    run_p08_independent_qa,
)


# --------------------------------------------------------------------------- #
# Fixtures & Helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def mock_dossier() -> ResearchDossier:
    """Creates a comprehensive verified research dossier fixture for Cao Đỉnh motif."""
    claim_1 = DossierClaim(
        claim_id=str(uuid.uuid4()),
        claim_type="factual",
        statement_vi="Cao Đỉnh là đỉnh đầu tiên và tối cao trong Cửu Đỉnh, biểu trưng cho sự thống nhất giang sơn Đại Nam.",
        statement_en="Cao Dinh is the premier and supreme urn among the Nine Dynastic Urns, symbolizing the territorial unification of Dai Nam.",
        verification_status="expert_verified",
        confidence="high",
        is_approved=True,
        is_disputed=False,
        source_bindings=[
            DossierSourceBinding(
                source_id="src_dai_nam_nhat_thong_chi",
                source_title="Đại Nam Nhất Thống Chí",
                locator="Quyển 1, Tr. 45-48",
                support_type="primary_evidence_for",
                excerpt="Đúc Cửu Đỉnh đặt trước Thế Miếu; Cao Đỉnh đứng đầu ở chính giữa.",
            )
        ],
    )
    claim_2 = DossierClaim(
        claim_id=str(uuid.uuid4()),
        claim_type="chronology",
        statement_vi="Cửu Đỉnh được Hoàng đế Minh Mạng khởi công đúc vào tháng 12 năm 1835 và hoàn thành năm 1837.",
        statement_en="The Nine Dynastic Urns were commissioned by Emperor Minh Mang in December 1835 and completed in 1837.",
        verification_status="published",
        confidence="high",
        is_approved=True,
        is_disputed=False,
        source_bindings=[
            DossierSourceBinding(
                source_id="src_dai_nam_thuc_luc",
                source_title="Đại Nam Thực Lục Chính Biên",
                locator="Đệ nhị kỷ, Quyển CLVI",
                support_type="supports",
                excerpt="Ất Mùi, Minh Mạng năm thứ 16, mùa đông tháng 12, đúc xong chín đỉnh.",
            )
        ],
    )
    claim_3 = DossierClaim(
        claim_id=str(uuid.uuid4()),
        claim_type="symbolism",
        statement_vi="Hình tượng Rồng mây (Long vân) trên Cao Đỉnh biểu thị quyền uy tối thượng của thiên tử và sự che chở của trời đất.",
        statement_en="The Dragon and Clouds relief on Cao Dinh signifies supreme imperial authority and celestial protection.",
        verification_status="verified",
        confidence="high",
        is_approved=True,
        is_disputed=False,
        source_bindings=[
            DossierSourceBinding(
                source_id="src_kham_dinh_hoi_dien",
                source_title="Khâm Định Đại Nam Hội Điển Sự Lệ",
                locator="Quyển 198, Khắc hình các đỉnh",
                support_type="supports",
                excerpt="Cao Đỉnh: chạm rồng bay trong mây, chính diện trang nghiêm.",
            )
        ],
    )

    sources = [
        DossierSource(
            source_id="src_dai_nam_nhat_thong_chi",
            title="Đại Nam Nhất Thống Chí",
            author="Quốc Sử Quán Triều Nguyễn",
            publication_year=1882,
            source_type="royal_record",
            verification_status="metadata_verified",
            license="PUBLIC_DOMAIN",
            rights_status="cleared",
            available_locators=["Quyển 1, Tr. 45-48"],
        ),
        DossierSource(
            source_id="src_dai_nam_thuc_luc",
            title="Đại Nam Thực Lục Chính Biên",
            author="Quốc Sử Quán Triều Nguyễn",
            publication_year=1848,
            source_type="royal_record",
            verification_status="accessible",
            license="PUBLIC_DOMAIN",
            rights_status="cleared",
            available_locators=["Đệ nhị kỷ, Quyển CLVI"],
        ),
        DossierSource(
            source_id="src_kham_dinh_hoi_dien",
            title="Khâm Định Đại Nam Hội Điển Sự Lệ",
            author="Nội Các Triều Nguyễn",
            publication_year=1851,
            source_type="royal_record",
            verification_status="metadata_verified",
            license="PUBLIC_DOMAIN",
            rights_status="cleared",
            available_locators=["Quyển 198, Khắc hình các đỉnh"],
        ),
    ]

    assets_3d = [
        DossierAsset3D(
            asset_id="asset_mesh_cao_dinh",
            mesh_id="mesh_cao_dinh_body",
            urn_slug="cao_dinh",
            hotspot_ids=["hs_cao_dinh_dragon_01"],
        )
    ]

    assets_2d = [
        DossierAsset2D(
            asset_id="asset_rubbing_cao_dinh_dragon",
            asset_type="rubbing_2d",
            file_url="/assets/ban-duc-noi/cao_dinh_long_van.webp",
            attribution="Bảo tàng Cổ vật Cung đình Huế",
            is_rubbing_fallback=True,
        )
    ]

    han_nom = [
        DossierHanNomRecord(
            motif_id="cao_dinh_long_van",
            glyph_original="龍雲",
            sino_vietnamese="Long Vân",
            english_gloss="Dragon and Clouds",
            review_status="verified",
            is_glyph_verified=True,
        )
    ]

    dossier = ResearchDossier(
        entity_id=str(uuid.uuid4()),
        entity_slug="cao-dinh-long-van",
        name_vi="Hình tượng Rồng Mây trên Cao Đỉnh",
        name_en="Dragon and Clouds on Cao Dinh",
        urn_slug="cao_dinh",
        content_scope="NINE_URNS",
        claims=[claim_1, claim_2, claim_3],
        sources=sources,
        assets_3d=assets_3d,
        assets_2d=assets_2d,
        han_nom_records=han_nom,
        license_scope="CC_BY_NC_SA_4.0",
    )
    dossier.dossier_sha256 = dossier.compute_sha256()
    return dossier


# --------------------------------------------------------------------------- #
# Test 1: P07 Narrative Drafting & Strict Sentence-Level Binding
# --------------------------------------------------------------------------- #
def test_p07_narrative_drafting_sentence_binding(mock_dossier: ResearchDossier):
    """Verifies that P07 drafting binds every factual sentence to claim and source."""
    writer = P07NarrativeWriter(mock_dossier)

    narrative_vi = writer.write_vietnamese_narrative()
    assert narrative_vi.title == "Khảo cứu lịch sử: Hình tượng Rồng Mây trên Cao Đỉnh"
    assert len(narrative_vi.sections) >= 2
    assert narrative_vi.word_count > 0
    assert len(narrative_vi.all_sentences) == 3
    assert narrative_vi.sha256 != ""

    for ref in narrative_vi.all_sentences:
        assert ref.claim_id is not None
        assert ref.source_id in ("src_dai_nam_nhat_thong_chi", "src_dai_nam_thuc_luc", "src_kham_dinh_hoi_dien")
        assert ref.locator != ""
        assert ref.is_verified is True
        assert len(ref.sentence_text) > 10

    # English narrative
    narrative_en = writer.write_english_narrative()
    assert len(narrative_en.all_sentences) == 3
    assert len(narrative_en.bilingual_aligned_ids) == 3
    assert narrative_en.sha256 != ""

    # Museum Label
    label = writer.write_museum_label()
    assert label.word_count_vi > 20
    assert label.word_count_en > 20
    assert len(label.sentence_claim_refs) == 1
    assert "Đại Nam Nhất Thống Chí" in label.label_vi


# --------------------------------------------------------------------------- #
# Test 2: P07 Han-Nom & 3D Interactive Narration with 2D Fallback
# --------------------------------------------------------------------------- #
def test_p07_hannom_and_3d_narration_script(mock_dossier: ResearchDossier):
    """Verifies Hán-Nôm notes and 3D narration script with 2D rubbing fallback."""
    writer = P07NarrativeWriter(mock_dossier)

    # Han-Nom notes
    notes = writer.write_hannom_notes()
    assert len(notes) == 1
    note = notes[0]
    assert note.glyph_original == "龍雲"
    assert note.sino_vietnamese == "Long Vân"
    assert note.is_glyph_verified is True

    # 3D interactive script
    script = writer.write_interactive_script()
    assert len(script.hotspots) == 1
    assert script.hotspots[0].target_mesh_id == "mesh_cao_dinh_body"
    assert script.fallback_2d.image_url == "/assets/ban-duc-noi/cao_dinh_long_van.webp"
    assert "bản dập" in script.fallback_2d.rubbing_caption_vi.lower()
    assert script.sha256 != ""


# --------------------------------------------------------------------------- #
# Test 3: P07 ELLO 6-Step Inquiry Lesson & 4-Level Rubric
# --------------------------------------------------------------------------- #
def test_p07_ello_lesson_and_rubric_pack(mock_dossier: ResearchDossier):
    """Verifies that ELLO lesson implements 6 steps with evidence requirements and 4-level rubric."""
    lesson_writer = P07LessonWriter(mock_dossier)

    lesson = lesson_writer.generate_ello_lesson()
    assert len(lesson.inquiry_steps) == 6
    step_keys = [s.step_key for s in lesson.inquiry_steps]
    assert step_keys == ["hook", "observation", "source_analysis", "synthesis", "reflection", "evaluation"]

    for s in lesson.inquiry_steps:
        assert s.requires_citation is True
        assert s.evidence_requirement != ""
        assert len(s.bound_claim_ids) >= 1
        assert len(s.bound_source_ids) >= 1

    # Assessment Pack
    pack = lesson_writer.generate_assessment_rubric_pack()
    assert len(pack.rubric_criteria) == 3
    for crit in pack.rubric_criteria:
        assert set(crit.levels.keys()) == {0, 1, 2, 3}

    assert len(pack.quiz_items) == 3
    for q in pack.quiz_items:
        assert q.correct_option_index == 0
        assert q.bound_claim_id != ""
        assert q.bound_source_id != ""
        assert q.is_disputed is False


# --------------------------------------------------------------------------- #
# Test 4: Content Bundle Assembly & Hash Lineage
# --------------------------------------------------------------------------- #
def test_content_bundle_draft_assembly(mock_dossier: ResearchDossier):
    """Verifies assemble_content_bundle aggregates all parts and computes SHA-256."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)
    assert bundle.entity_slug == "cao-dinh-long-van"
    assert bundle.schema_version == "v1.0"
    assert bundle.bundle_sha256 != ""
    assert len(bundle.aggregated_sentence_claim_refs) == 7  # 3 VI + 3 EN + 1 Label
    assert len(bundle.source_bibliography) == 3


# --------------------------------------------------------------------------- #
# Test 5: P08 Independent QA (Positive Clean Gate Passage)
# --------------------------------------------------------------------------- #
def test_p08_independent_qa_gate_passed(mock_dossier: ResearchDossier):
    """Verifies that clean, fully verified content bundle passes all 10 QA checkers."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)
    qa_report = run_p08_independent_qa(bundle, mock_dossier)

    assert qa_report.gate_status == QAGateStatus.GATE_PASSED
    assert qa_report.p0_blockers_count == 0
    assert qa_report.sha256 != ""


# --------------------------------------------------------------------------- #
# Negative Abuse Tests ("No source -> no invented fact")
# --------------------------------------------------------------------------- #
def test_negative_abuse_unsourced_sentence_fails_qa(mock_dossier: ResearchDossier):
    """Negative Abuse: Sentences without verified sources cannot hide invented facts."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)

    # Malicious injection: inject an unsourced invented sentence into Vietnamese narrative
    invented_sentence = "Một số thợ thủ công người phương Tây bí mật tham gia đúc Cửu Đỉnh."
    bundle.narrative_vi.sections[0].paragraphs.append(invented_sentence)
    # Notice: not added to sec.sentence_claim_refs!

    qa_report = run_p08_independent_qa(bundle, mock_dossier)

    # QA must detect unsourced sentence as P0_BLOCKER and fail the gate
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert qa_report.p0_blockers_count >= 1

    unsourced_findings = [f for f in qa_report.findings if f.finding_code == "UNSOURCED_FACTUAL_ASSERTION"]
    assert len(unsourced_findings) >= 1
    assert "lacks source binding" in unsourced_findings[0].message


def test_negative_abuse_invented_english_fact_fails_qa(mock_dossier: ResearchDossier):
    """Negative Abuse: English narrative adding unsupported facts absent from dossier is blocked."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)

    # Inject unsupported claim into English narrative
    invented_ref = SentenceClaimRef(
        sentence_index=99,
        sentence_text="French engineers secretly drafted the mold for Cao Dinh.",
        claim_id="invented-claim-999",  # not in dossier
        source_id="src_dai_nam_nhat_thong_chi",
        source_title="Đại Nam Nhất Thống Chí",
        locator="Quyển 1, Tr. 45",
        is_verified=False,
    )
    bundle.narrative_en.sections[0].paragraphs.append(invented_ref.sentence_text)
    bundle.narrative_en.sections[0].sentence_claim_refs.append(invented_ref)
    bundle.narrative_en.all_sentences.append(invented_ref)

    qa_report = run_p08_independent_qa(bundle, mock_dossier)
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert any(f.finding_code == "UNSUPPORTED_EN_FACT" for f in qa_report.findings)


def test_negative_abuse_quiz_on_disputed_claim_blocked(mock_dossier: ResearchDossier):
    """Negative Abuse: Factual quiz items built on disputed claims are blocked."""
    disputed_claim = DossierClaim(
        claim_id="disputed-claim-001",
        claim_type="disputed",
        statement_vi="Cao Đỉnh từng bị dịch chuyển vị trí trong thời kỳ chiến tranh.",
        statement_en="Cao Dinh was relocated during wartime.",
        verification_status="disputed",
        confidence="disputed",
        is_approved=False,
        is_disputed=True,
        source_bindings=[],
    )
    dossier_with_dispute = copy.deepcopy(mock_dossier)
    dossier_with_dispute.claims.append(disputed_claim)

    lesson_writer = P07LessonWriter(dossier_with_dispute)
    pack = lesson_writer.generate_assessment_rubric_pack()

    # Artificially inject quiz based on disputed claim
    pack.quiz_items.append(
        pack.quiz_items[0].model_copy(
            update={
                "quiz_id": "quiz_disputed_test",
                "bound_claim_id": disputed_claim.claim_id,
                "is_disputed": True,
            }
        )
    )

    bundle = generate_narrative_and_lesson_draft(mock_dossier)
    bundle.assessment_pack = pack

    qa_report = run_p08_independent_qa(bundle, dossier_with_dispute)
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert any(f.finding_code == "QUIZ_ON_DISPUTED_CLAIM" for f in qa_report.findings)


def test_negative_abuse_missing_2d_fallback_blocked(mock_dossier: ResearchDossier):
    """Negative Abuse: 3D interactive script lacking 2D rubbing fallback is blocked."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)

    # Corrupt fallback
    bundle.interactive_script_3d.fallback_2d.image_url = ""

    qa_report = run_p08_independent_qa(bundle, mock_dossier)
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert any(f.finding_code == "MISSING_2D_FALLBACK" for f in qa_report.findings)


def test_negative_abuse_unverified_han_nom_glyph_blocked(mock_dossier: ResearchDossier):
    """Negative Abuse: Unreviewed or hallucinated Hán-Nôm glyph is blocked."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)

    # Set glyph as unverified
    bundle.hannom_notes[0].is_glyph_verified = False

    qa_report = run_p08_independent_qa(bundle, mock_dossier)
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert any(f.finding_code == "UNVERIFIED_HAN_NOM_GLYPH" for f in qa_report.findings)


def test_negative_abuse_fabricated_locator_blocked(mock_dossier: ResearchDossier):
    """Negative Abuse: Fabricated or placeholder page locators are detected and blocked."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)

    # Inject fake page locator
    bundle.aggregated_sentence_claim_refs[0].locator = "fake_page_999"

    qa_report = run_p08_independent_qa(bundle, mock_dossier)
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert any(f.finding_code == "FABRICATED_CITATION_LOCATOR" for f in qa_report.findings)


def test_negative_abuse_chronological_contradiction_blocked(mock_dossier: ResearchDossier):
    """Negative Abuse: Chronological contradictions (e.g. 20th century) are caught."""
    bundle = generate_narrative_and_lesson_draft(mock_dossier)

    # Insert chronological blunder
    bundle.museum_label.label_vi += " Hiện vật được đúc vào thế kỷ 20 dưới triều đại mới."

    qa_report = run_p08_independent_qa(bundle, mock_dossier)
    assert qa_report.gate_status == QAGateStatus.GATE_BLOCKED
    assert any(f.finding_code == "CHRONOLOGICAL_CONTRADICTION" for f in qa_report.findings)


# --------------------------------------------------------------------------- #
# Test 6: Database Persistence & Invariants
# --------------------------------------------------------------------------- #
def test_factory_persistence_and_dossier_from_db(db_session: Session):
    """Verifies DB seeding, build_dossier_from_entity, and persistence in research tables."""
    # 1. Seed historical entity, source, and claim in DB
    ent = HistoricalEntity(
        entity_type="relief",
        slug=f"relief-test-{uuid.uuid4().hex[:6]}",
        name_vi="Thần Quy Biển Nam",
        name_en="Sacred Turtle of the Southern Sea",
        name_han_nom="神龜",
        alternative_names=["Rùa Vàng"],
        publication_status="published",
    )
    db_session.add(ent)
    db_session.flush()

    src = HistoricalSource(
        source_type="royal_record",
        title="Đại Nam Thực Lục Chính Biên - Bản Khắc",
        publication_year=1848,
        pages="Quyển 120, Tr. 15",
        verification_status="metadata_verified",
        license="PUBLIC_DOMAIN",
        rights_status="cleared",
    )
    db_session.add(src)
    db_session.flush()

    claim = HistoricalClaim(
        entity_id=ent.id,
        claim_type="factual",
        statement_vi="Thần Quy là linh vật hộ trì xã tắc biểu hiện cho sự vững bền trường cửu của quốc gia.",
        statement_en="The Sacred Turtle is a guardian mythical creature signifying national endurance.",
        verification_status="expert_verified",
        confidence="high",
        origin="editorial",
    )
    db_session.add(claim)
    db_session.flush()

    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=src.id,
        support_type="primary_evidence_for",
        chapter="Quyển 120",
        page_start="15",
        quotation_excerpt="Đúc Thần Quy nơi Nhân Đỉnh, biểu trưng cho sự trường tồn vạn đại.",
    )
    db_session.add(binding)
    db_session.flush()

    # 2. Build dossier from DB
    dossier = build_dossier_from_entity(db_session, ent.slug)
    assert dossier.entity_slug == ent.slug
    assert len(dossier.claims) == 1
    assert len(dossier.sources) == 1
    assert "Quyển 120" in dossier.claims[0].source_bindings[0].locator

    # 3. Generate draft and run QA
    bundle = generate_narrative_and_lesson_draft(dossier)
    qa_report = run_p08_independent_qa(bundle, dossier)
    assert qa_report.gate_status == QAGateStatus.GATE_PASSED

    # 4. Create ResearchRun and persist results
    run = ResearchRun(
        mode="STRICT_PRODUCTION",
        content_scope="NINE_URNS",
        subject_type="RELIEF",
        subject_id=ent.slug,
        status="RUNNING",
    )
    db_session.add(run)
    db_session.flush()

    persisted_meta = persist_factory_phase_results(db_session, run.id, bundle, qa_report)
    assert persisted_meta["gate_status"] == "GATE_PASSED"
    assert persisted_meta["p0_blockers_count"] == 0
    assert "p07_evidence_id" in persisted_meta
    assert "p08_evidence_id" in persisted_meta

    # Verify rows in DB
    phases = db_session.scalars(select(ResearchPhase).where(ResearchPhase.run_id == run.id)).all()
    assert len(phases) == 2  # P07 and P08
    p07_db = next(p for p in phases if p.phase_code == ResearchPhaseCode.P07.value)
    p08_db = next(p for p in phases if p.phase_code == ResearchPhaseCode.P08.value)
    assert p07_db.status == ResearchPhaseStatus.COMPLETED.value
    assert p08_db.status == ResearchPhaseStatus.COMPLETED.value
    assert p08_db.barrier_passed is True

    evidence_results = db_session.scalars(select(ResearchEvidenceResult)).all()
    assert len(evidence_results) >= 2
