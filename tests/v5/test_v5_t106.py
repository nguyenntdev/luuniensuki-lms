# -*- coding: utf-8 -*-
"""Ticket V5-T106 / Wave W10 Slot A06 Acceptance Tests.

Multi-Language Visitor Assist & Bounded AI Grounding Verification:
1. Supported Locales & Metadata:
   - Primary: Vietnamese ('vi'), English ('en') - native / primary bridge.
   - Extended: French ('fr'), Japanese ('ja'), Korean ('ko') - strictly human-reviewed with explicit disclaimers.
2. Delimiter Boundaries & Injection Defense:
   - Delimiter headers in VI, EN, FR, JA, KO.
   - Neutralizes prompt injection threats and falls closed safely.
3. Bounded AI Assist & Explicit Disclaimers:
   - Extended languages (FR, JA, KO) carry mandatory human-reviewed translation badges and bounded AI disclaimers.
   - System prompts dynamically inject language-specific directives and bounding rules.
4. Deterministic Grounded Synthesis:
   - Deterministic answer generator outputs language-appropriate headers, citations, and disclaimer footers.
5. Critical Negative Abuse Invariant:
   - When verified primary sources are missing (evidence gap), system strictly returns explicit
     uncertainty disclaimer in the visitor's language (VI, EN, FR, JA, KO).
   - Never fabricates ungrounded translations, phantom citations, or speculative cultural facts.
6. End-to-End API Dispatcher & Graceful Fallbacks:
   - Full integration through `rbpc_ai.answer_cultural_question` across all supported languages.
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from backend.models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models_rbpc import (
    RbpcClaimEvidence,
    RbpcStory,
    RbpcSupportType,
)
from backend.services import rbpc_ai


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
def _seed_story_and_claims(db_session: Session) -> tuple[RbpcStory, list[RbpcClaimEvidence]]:
    unique_slug = f"cau-chuyen-duc-dong-hue-{uuid.uuid4().hex[:6]}"
    story = RbpcStory(
        slug=unique_slug,
        title_vi="Kỹ nghệ Đúc đồng Phường Đúc",
        intro_vi="Làng nghề đúc đồng truyền thống bên bờ sông Hương hơn 400 năm lịch sử.",
        status="published",
        content_scope="RBPC_HUE",
    )
    db_session.add(story)
    db_session.flush()

    source = HistoricalSource(
        title="Khâm Định Đại Nam Hội Điển Sự Lệ - Quyển 159",
        author_text="Nội các triều Nguyễn",
        publication_year=1851,
        source_type="archival",
        verification_status="verified",
        content_scope="RBPC_HUE",
    )
    db_session.add(source)
    db_session.flush()

    evidence1 = RbpcClaimEvidence(
        story_id=story.id,
        statement="Kỹ nghệ đúc đồng Phường Đúc hình thành từ thế kỷ 17 dưới thời các chúa Nguyễn.",
        source_ref_id=source.id,
        source_title=source.title,
        citation_label="Quyển 159, tr. 42",
        support_type=RbpcSupportType.direct.value,
        review_status="published_human_approved",
    )
    evidence2 = RbpcClaimEvidence(
        story_id=story.id,
        statement="Thợ đúc Phường Đúc từng tham gia phụng mệnh triều đình đúc Cửu Đỉnh và các vạc đồng lớn.",
        source_ref_id=source.id,
        source_title=source.title,
        citation_label="Quyển 159, tr. 50-52",
        support_type=RbpcSupportType.direct.value,
        review_status="published_human_approved",
    )
    db_session.add_all([evidence1, evidence2])
    db_session.commit()
    return story, [evidence1, evidence2]


# --------------------------------------------------------------------------- #
# 1. Supported Locales & Strict Human Review Metadata
# --------------------------------------------------------------------------- #
def test_multilanguage_supported_locales_and_metadata():
    """Verify supported visitor assist locales and strict human review policies."""
    locales = rbpc_ai.get_supported_visitor_locales()
    assert "vi" in locales
    assert "en" in locales
    assert "fr" in locales
    assert "ja" in locales
    assert "ko" in locales

    # Primary authoritative: VI
    meta_vi = rbpc_ai.get_visitor_locale_metadata("vi")
    assert meta_vi["locale"] == "vi"
    assert meta_vi["review_tier"] == "primary_authoritative"
    assert meta_vi["requires_human_review"] is False
    assert meta_vi["disclaimer_required"] is False

    # Primary international: EN
    meta_en = rbpc_ai.get_visitor_locale_metadata("en")
    assert meta_en["locale"] == "en"
    assert meta_en["review_tier"] == "primary_international"
    assert meta_en["requires_human_review"] is False

    # Extended visitor languages strictly require human review & explicit disclaimers:
    for code in ("fr", "ja", "ko"):
        meta = rbpc_ai.get_visitor_locale_metadata(code)
        assert meta["locale"] == code
        assert meta["review_tier"] == "restricted_human_review_required"
        assert meta["requires_human_review"] is True
        assert meta["disclaimer_required"] is True
        assert len(meta["bounded_ai_disclaimer"]) > 20
        assert len(meta["uncertainty_disclaimer"]) > 20


# --------------------------------------------------------------------------- #
# 2. Bounded AI System Prompts & Delimiter Boundaries
# --------------------------------------------------------------------------- #
def test_multilanguage_system_prompts_and_context_headers():
    """Verify delimiter headers and bounded AI prompt directives for each language."""
    # VI system prompt
    prompt_vi = rbpc_ai.build_rbpc_system_prompt("vi")
    assert "Trợ lý Cầu nối Văn hóa" in prompt_vi
    assert "phẩm giá nghệ nhân" in prompt_vi.lower()
    assert "CLAIM_START" in rbpc_ai.CONTEXT_HEADERS["vi"]

    # EN system prompt
    prompt_en = rbpc_ai.build_rbpc_system_prompt("en")
    assert "Cultural Bridge AI" in prompt_en
    assert "ARTISAN DIGNITY RULE" in prompt_en
    assert "CLAIM_START" in rbpc_ai.CONTEXT_HEADERS["en"]

    # Extended languages (FR, JA, KO) must include bounded AI directive & human review warning
    prompt_fr = rbpc_ai.build_rbpc_system_prompt("fr")
    assert "MULTI-LANGUAGE VISITOR ASSIST DIRECTIVE" in prompt_fr
    assert "French" in prompt_fr
    assert "CLAIM_START" in rbpc_ai.CONTEXT_HEADERS["fr"]

    prompt_ja = rbpc_ai.build_rbpc_system_prompt("ja")
    assert "MULTI-LANGUAGE VISITOR ASSIST DIRECTIVE" in prompt_ja
    assert "Japanese" in prompt_ja
    assert "CLAIM_START" in rbpc_ai.CONTEXT_HEADERS["ja"]

    prompt_ko = rbpc_ai.build_rbpc_system_prompt("ko")
    assert "MULTI-LANGUAGE VISITOR ASSIST DIRECTIVE" in prompt_ko
    assert "Korean" in prompt_ko
    assert "CLAIM_START" in rbpc_ai.CONTEXT_HEADERS["ko"]


# --------------------------------------------------------------------------- #
# 3. Critical Negative Abuse Invariant: Missing Primary Sources Return Uncertainty
# --------------------------------------------------------------------------- #
def test_negative_abuse_missing_primary_source_returns_uncertainty_in_visitor_language():
    """Negative abuse defense: Missing primary source returns explicit uncertainty disclaimer
    in the visitor's language, not ungrounded translation or hallucinated facts.
    """
    # 1. French visitor assist
    v_fr = rbpc_ai.verify_multilanguage_visitor_query(
        question="Quelle est la technique secrète inconnue des chaudronniers?",
        locale="fr",
        has_primary_source=False,
    )
    assert v_fr["status"] == "insufficient_evidence"
    assert v_fr["can_generate_translation"] is False
    assert "Aucune source primaire indépendante" in v_fr["uncertainty_disclaimer"]
    assert "Traduction vérifiée par des experts humains" in v_fr["disclaimer_badge"]

    # 2. Japanese visitor assist
    v_ja = rbpc_ai.verify_multilanguage_visitor_query(
        question="鋳造職人の秘密の配合比率はどのようなものですか？",
        locale="ja",
        has_primary_source=False,
    )
    assert v_ja["status"] == "insufficient_evidence"
    assert v_ja["can_generate_translation"] is False
    assert "原典史料が確認できません" in v_ja["uncertainty_disclaimer"]
    assert "専門家による人手確認済み翻訳" in v_ja["disclaimer_badge"]

    # 3. Korean visitor assist
    v_ko = rbpc_ai.verify_multilanguage_visitor_query(
        question="왕실 주조 장인들의 비공개 주조 배합비는 무엇입니까?",
        locale="ko",
        has_primary_source=False,
    )
    assert v_ko["status"] == "insufficient_evidence"
    assert v_ko["can_generate_translation"] is False
    assert "1차 사료가 존재하지 않습니다" in v_ko["uncertainty_disclaimer"]
    assert "전문가 검수를 거친 공식 번역" in v_ko["disclaimer_badge"]

    # 4. English visitor assist
    v_en = rbpc_ai.verify_multilanguage_visitor_query(
        question="What was the secret undocumented bronze composition?",
        locale="en",
        has_primary_source=False,
    )
    assert v_en["status"] == "insufficient_evidence"
    assert v_en["can_generate_translation"] is False
    assert "No independent verified primary sources exist" in v_en["uncertainty_disclaimer"]


# --------------------------------------------------------------------------- #
# 4. Deterministic Multi-Language Synthesis with Bounded Disclaimers
# --------------------------------------------------------------------------- #
def test_deterministic_multilanguage_synthesis_with_disclaimers():
    """Verify deterministic fallback response generator in all languages."""
    dummy_context = rbpc_ai.RBPCRetrievalContext(
        "Dummy context",
        claims=[],
        sources_by_claim={},
        locale="fr",
    )

    # Empty claims in French
    res_fr = rbpc_ai.build_rbpc_deterministic_answer(
        question="Question sans source",
        claims=[],
        retrieved_context=dummy_context,
        locale="fr",
    )
    assert res_fr["confidence"] == "low"
    assert "Les documents de recherche approuvés ne contiennent actuellement aucune trace" in res_fr["answer_markdown"]
    assert "Avis d'assistance IA encadrée" in res_fr["answer_markdown"]
    assert len(res_fr["citations"]) == 0

    # Empty claims in Japanese
    dummy_context_ja = rbpc_ai.RBPCRetrievalContext(
        "Dummy context ja",
        claims=[],
        sources_by_claim={},
        locale="ja",
    )
    res_ja = rbpc_ai.build_rbpc_deterministic_answer(
        question="史料のない質問",
        claims=[],
        retrieved_context=dummy_context_ja,
        locale="ja",
    )
    assert res_ja["confidence"] == "low"
    assert "承認された学術研究資料には" in res_ja["answer_markdown"]
    assert "限定的AI支援に関する告知" in res_ja["answer_markdown"]

    # Empty claims in Korean
    dummy_context_ko = rbpc_ai.RBPCRetrievalContext(
        "Dummy context ko",
        claims=[],
        sources_by_claim={},
        locale="ko",
    )
    res_ko = rbpc_ai.build_rbpc_deterministic_answer(
        question="사료가 없는 질의",
        claims=[],
        retrieved_context=dummy_context_ko,
        locale="ko",
    )
    assert res_ko["confidence"] == "low"
    assert "승인된 학술 연구 문헌에는" in res_ko["answer_markdown"]
    assert "엄격한 AI 지원 고지" in res_ko["answer_markdown"]


# --------------------------------------------------------------------------- #
# 5. End-to-End Cultural Bridge Dispatcher with Multi-Language Support
# --------------------------------------------------------------------------- #
def test_e2e_cultural_bridge_dispatcher_multilanguage(db_session: Session):
    """Verify answer_cultural_question end-to-end integration across multiple visitor languages."""
    story, evidences = _seed_story_and_claims(db_session)

    # 1. Grounded query in French
    ans_fr = rbpc_ai.answer_cultural_question(
        db=db_session,
        story_slug=story.slug,
        question="Quelle est l'origine du village de fonderie de bronze de Phường Đúc?",
        locale="fr",
        use_llm=False,  # deterministic verification
    )
    assert ans_fr["locale"] == "fr"
    assert ans_fr["status"] == "supported"
    assert ans_fr["epistemic_certainty"] == "high"
    assert len(ans_fr["citations"]) >= 1
    assert "Avis d'assistance IA encadrée" in ans_fr["answer"]
    assert "Quyển 159" in ans_fr["citations"][0]["locator"]

    # 2. Grounded query in Japanese
    ans_ja = rbpc_ai.answer_cultural_question(
        db=db_session,
        story_slug=story.slug,
        question="フオンドゥック青銅鋳造村の起源について教えてください。",
        locale="ja",
        use_llm=False,
    )
    assert ans_ja["locale"] == "ja"
    assert ans_ja["status"] == "supported"
    assert "限定的AI支援に関する告知" in ans_ja["answer"]

    # 3. Grounded query in Korean
    ans_ko = rbpc_ai.answer_cultural_question(
        db=db_session,
        story_slug=story.slug,
        question="프엉득 청동 주조 마을의 기원에 대해 설명해 주세요.",
        locale="ko",
        use_llm=False,
    )
    assert ans_ko["locale"] == "ko"
    assert ans_ko["status"] == "supported"
    assert "엄격한 AI 지원 고지" in ans_ko["answer"]

    # 4. Negative test: unknown story in French returns fail-closed disclaimer
    fallback_fr = rbpc_ai.answer_cultural_question(
        db=db_session,
        story_slug="histoire-inconnue-xyz",
        question="Question sur une histoire inconnue?",
        locale="fr",
        use_llm=False,
    )
    assert fallback_fr["status"] == "insufficient_evidence"
    assert fallback_fr["locale"] == "fr"
    assert "Les documents de recherche approuvés" in fallback_fr["answer"]
    assert "Aucune source primaire indépendante" in fallback_fr["uncertainty_note"]


# --------------------------------------------------------------------------- #
# 6. REST API Endpoint Integration for Multi-Language Visitors
# --------------------------------------------------------------------------- #
def test_cultural_bridge_api_endpoint_multilanguage(client: TestClient, db_session: Session):
    """Verify POST /api/v1/rbpc/cultural-bridge API endpoint accepts and respects visitor locales."""
    story, evidences = _seed_story_and_claims(db_session)

    # 1. Query with French locale
    res_fr = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": story.slug,
            "question": "Comment le village de Phường Đúc a-t-il été fondé?",
            "locale": "fr",
        },
    )
    assert res_fr.status_code == 200, res_fr.text
    payload_fr = res_fr.json()
    assert payload_fr["locale"] == "fr"
    assert payload_fr["status"] == "supported"
    assert len(payload_fr["citations"]) > 0
    assert payload_fr["context_boundary"] is not None

    # 2. Query with Japanese locale
    res_ja = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": story.slug,
            "question": "フオンドゥック青銅鋳造の歴史について教えてください。",
            "locale": "ja",
        },
    )
    assert res_ja.status_code == 200, res_ja.text
    payload_ja = res_ja.json()
    assert payload_ja["locale"] == "ja"
    assert payload_ja["status"] == "supported"

    # 3. Negative abuse: Query with missing evidence story
    res_missing = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": "nonexistent-story-123",
            "question": "Quel est ce monument?",
            "locale": "fr",
        },
    )
    assert res_missing.status_code == 200
    missing_payload = res_missing.json()
    assert missing_payload["status"] == "insufficient_evidence"
    assert "Les documents de recherche approuvés" in missing_payload["answer"]
