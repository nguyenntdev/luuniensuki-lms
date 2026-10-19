# -*- coding: utf-8 -*-
"""History Tutor Scope Parameterization & RBPC Cultural Bridge Integration Tests.

Validates:
1. `heritage_scope` parameterization (`CUU_DINH`, `RBPC_HUE`, `ALL`):
   - `RBPC_HUE` queries retrieve only Huế-scoped context and do not hallucinate about Cửu Đỉnh.
   - `RBPC_HUE` uses the broader living heritage prompt template from `rbpc_ai`.
   - `CUU_DINH` preserves the legacy Cửu Đỉnh prompt for backward compatibility.
2. `POST /api/v1/rbpc/cultural-bridge` integration:
   - Dispatches to `rbpc_ai.answer_cultural_question()`.
   - Fails closed to structured fallback on unknown entities or timeouts.
"""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from backend.config import settings
from backend.models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models_rbpc import (
    RbpcClaimEvidence,
    RbpcStory,
    RbpcStoryStatus,
    RbpcSupportType,
)
from backend.services import history_governance as gov
from backend.services import rbpc_ai


# --------------------------------------------------------------------------- #
# Seeding Helpers
# --------------------------------------------------------------------------- #
def _seed_entity(
    db_session,
    *,
    slug: str,
    name_vi: str,
    entity_type: str = "relief",
    content_scope: str = "CUU_DINH",
    alternative_names: list[str] | None = None,
    summary_vi: str | None = None,
) -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type=entity_type,
        slug=slug,
        name_vi=name_vi,
        publication_status="published",
        content_scope=content_scope,
        alternative_names=alternative_names or [],
        summary_vi=summary_vi,
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(db_session, **overrides) -> HistoricalSource:
    data = {
        "source_type": "scholarly_book",
        "title": "Nghiên cứu Di sản Cố đô Huế",
        "author_text": "Hội đồng Trị sự Nguyễn Phước Tộc",
        "publication_year": 2012,
        "verification_status": "metadata_verified",
    }
    data.update(overrides)
    source = HistoricalSource(**data)
    db_session.add(source)
    db_session.flush()
    return source


def _seed_verified_claim(
    db_session,
    *,
    entity: HistoricalEntity,
    statement: str,
    claim_type: str = "factual",
    confidence: str = "high",
    content_scope: str | None = None,
    source: HistoricalSource | None = None,
    page_start: str = "24",
) -> tuple[HistoricalClaim, HistoricalSource]:
    if source is None:
        source = _seed_source(db_session)
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type=claim_type,
        statement_vi=statement,
        confidence=confidence,
        origin="editorial",
        verification_status="unreviewed",
        content_scope=content_scope or entity.content_scope,
    )
    db_session.add(claim)
    db_session.flush()

    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=source,
        data={"support_type": "supports", "page_start": page_start},
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="editor_reviewed", actor_id=None
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="expert_verified", actor_id=None
    )
    db_session.flush()
    return claim, source


def _seed_rbpc_story_with_claims(
    db_session,
    *,
    slug: str = "tieng-chuong-khiem-cung",
    title_vi: str = "Tiếng chuông Khiêm Cung",
) -> tuple[RbpcStory, RbpcClaimEvidence]:
    story = RbpcStory(
        slug=slug,
        title_vi=title_vi,
        intro_vi="Kỹ nghệ đúc chuông đồng truyền thống bên bờ sông Hương.",
        approved_summary_vi="Tóm tắt nghiên cứu kỹ thuật đúc chuông Huế được hội đồng thẩm định.",
        status=RbpcStoryStatus.published.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(story)
    db_session.flush()

    claim_evidence = RbpcClaimEvidence(
        story_id=story.id,
        statement="Kỹ thuật đúc chuông Huế sử dụng khuôn sáp ong và đất thó lòng sông Hương.",
        locale="vi",
        claim_category="maker_technique",
        source_title="Kỹ thuật đúc đồng truyền thống Huế — Viện Nghiên cứu Văn hóa",
        citation_label="Chương 3, tr. 78-82",
        support_type=RbpcSupportType.direct.value,
        review_status="verified",
    )
    db_session.add(claim_evidence)
    db_session.flush()
    db_session.commit()
    return story, claim_evidence


# --------------------------------------------------------------------------- #
# Tests: Heritage Scope Parameterization
# --------------------------------------------------------------------------- #
def test_tutor_rbpc_hue_scope_retrieves_hue_context(client, db_session):
    """RBPC_HUE query retrieves Huế-scoped entities and claims."""
    hue_entity = _seed_entity(
        db_session,
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        entity_type="monument",
        content_scope="RBPC_HUE",
    )
    claim, source = _seed_verified_claim(
        db_session,
        entity=hue_entity,
        statement="Điện Thái Hòa là nơi diễn ra các đại lễ đăng quang của 13 vị vua triều Nguyễn.",
        claim_type="factual",
        content_scope="RBPC_HUE",
        page_start="50",
    )
    db_session.commit()

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Điện Thái Hòa có vai trò gì trong triều đình Huế?",
            "heritage_scope": "RBPC_HUE",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "Điện Thái Hòa" in data["answer_markdown"] or "đại lễ đăng quang" in data["answer_markdown"]
    assert data["grounding"]["claims_used"] >= 1
    assert data["citations"][0]["source_id"] == str(source.id)


def test_tutor_rbpc_hue_scope_blocks_cuu_dinh_hallucination(client, db_session):
    """RBPC_HUE query about Cửu Đỉnh must not retrieve Cửu Đỉnh claims or hallucinate."""
    _seed_entity(
        db_session,
        slug="thuan-dinh-urn",
        name_vi="Thuần Đỉnh",
        entity_type="urn",
        content_scope="CUU_DINH",
    )
    _seed_verified_claim(
        db_session,
        entity=db_session.query(HistoricalEntity).filter_by(slug="thuan-dinh-urn").first(),
        statement="Thuần Đỉnh là đỉnh thứ hai trong Cửu Đỉnh đúc năm 1835.",
        content_scope="CUU_DINH",
    )
    db_session.commit()

    # Ask specifically about Thuần Đỉnh with heritage_scope='RBPC_HUE'
    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Thuần Đỉnh được đúc vào năm nào?",
            "heritage_scope": "RBPC_HUE",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    # Must fail closed: no Cửu Đỉnh entity or claim in RBPC_HUE scope
    assert data["confidence"] == "low"
    assert data["grounding"]["claims_used"] == 0
    assert data["citations"] == []
    assert "khoảng trống bằng chứng" in data["answer_markdown"] or "Không tìm thấy" in data["answer_markdown"]
    assert "1835" not in data["answer_markdown"]


def test_tutor_cuu_dinh_scope_backward_compatibility(client, db_session):
    """CUU_DINH scope preserves full backward compatibility for Cửu Đỉnh questions."""
    urn_entity = _seed_entity(
        db_session,
        slug="nhan-dinh-urn",
        name_vi="Nhân Đỉnh",
        entity_type="urn",
        content_scope="CUU_DINH",
    )
    claim, source = _seed_verified_claim(
        db_session,
        entity=urn_entity,
        statement="Nhân Đỉnh tượng trưng cho vua Minh Mạng và sự phát triển của triều đại.",
        content_scope="CUU_DINH",
        page_start="12",
    )
    db_session.commit()

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Nhân Đỉnh tượng trưng cho điều gì?",
            "heritage_scope": "CUU_DINH",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["confidence"] in ("high", "medium")
    assert "Nhân Đỉnh" in data["answer_markdown"]
    assert data["grounding"]["claims_used"] >= 1
    assert data["citations"][0]["source_id"] == str(source.id)


def test_tutor_all_scope_retrieves_both_domains(client, db_session):
    """Default scope ALL accesses both Cửu Đỉnh and Huế entities."""
    urn = _seed_entity(
        db_session,
        slug="anh-dinh-urn",
        name_vi="Anh Đỉnh",
        entity_type="urn",
        content_scope="CUU_DINH",
    )
    _seed_verified_claim(
        db_session,
        entity=urn,
        statement="Anh Đỉnh được đúc hoàn thành vào năm 1837.",
        content_scope="CUU_DINH",
    )

    place = _seed_entity(
        db_session,
        slug="chua-thien-mu-place",
        name_vi="Chùa Thiên Mụ",
        entity_type="monument",
        content_scope="RBPC_HUE",
    )
    _seed_verified_claim(
        db_session,
        entity=place,
        statement="Chùa Thiên Mụ được chúa Nguyễn Hoàng khởi lập năm 1601.",
        content_scope="RBPC_HUE",
    )
    db_session.commit()

    # Query Urn on ALL scope
    res_urn = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Anh Đỉnh đúc xong năm nào?", "heritage_scope": "ALL"},
    )
    assert res_urn.status_code == 200
    assert "1837" in res_urn.json()["answer_markdown"]

    # Query Monument on ALL scope
    res_place = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Chùa Thiên Mụ lập năm nào?", "heritage_scope": "ALL"},
    )
    assert res_place.status_code == 200
    assert "1601" in res_place.json()["answer_markdown"]


def test_tutor_prompt_selection_by_scope(client, db_session, monkeypatch):
    """RBPC_HUE uses the new living craft prompt; CUU_DINH uses the legacy prompt."""
    place = _seed_entity(
        db_session,
        slug="lang-tu-duc-monument",
        name_vi="Lăng Tự Đức",
        entity_type="monument",
        content_scope="RBPC_HUE",
    )
    _seed_verified_claim(
        db_session,
        entity=place,
        statement="Lăng Tự Đức mang phong cách kiến trúc viên lâm đặc sắc.",
        content_scope="RBPC_HUE",
    )
    db_session.commit()

    captured_prompts = []

    def mock_deepseek_chat(messages, **kwargs):
        captured_prompts.append(messages[0]["content"])
        return "Lăng Tự Đức mang phong cách viên lâm. [SOURCE:00000000-0000-0000-0000-000000000000]"

    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")
    monkeypatch.setattr("backend.routers.history_tutor._call_deepseek_chat", mock_deepseek_chat)

    # 1. Scope RBPC_HUE: Must use rbpc_ai prompt
    client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Kiến trúc Lăng Tự Đức?", "heritage_scope": "RBPC_HUE"},
    )
    assert len(captured_prompts) == 1
    prompt_rbpc = captured_prompts[0]
    assert "Trợ lý Cầu nối Văn hóa" in prompt_rbpc
    assert "QUY TẮC TÔN TRỌNG PHẨM GIÁ NGHỆ NHÂN" in prompt_rbpc
    assert "1835" in prompt_rbpc

    # 2. Scope CUU_DINH: Must use legacy Cửu Đỉnh prompt
    urn = _seed_entity(
        db_session,
        slug="tuyen-dinh-legacy",
        name_vi="Tuyên Đỉnh",
        entity_type="urn",
        content_scope="CUU_DINH",
    )
    _seed_verified_claim(
        db_session,
        entity=urn,
        statement="Tuyên Đỉnh được đúc năm 1835.",
        content_scope="CUU_DINH",
    )
    db_session.commit()

    client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Tuyên Đỉnh được đúc năm nào?", "heritage_scope": "CUU_DINH"},
    )
    assert len(captured_prompts) == 2
    prompt_cuu_dinh = captured_prompts[1]
    assert "Lưu Niên Sử Kí (Cửu Đỉnh)" in prompt_cuu_dinh
    assert "Trợ lý Cầu nối Văn hóa" not in prompt_cuu_dinh


# --------------------------------------------------------------------------- #
# Tests: Cultural Bridge Endpoint & Router Integration
# --------------------------------------------------------------------------- #
def test_cultural_bridge_endpoint_dispatches_and_succeeds(client, db_session):
    """POST /api/v1/rbpc/cultural-bridge successfully returns structured response."""
    story, claim = _seed_rbpc_story_with_claims(db_session)

    res = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": story.slug,
            "question": "Vì sao kỹ thuật làm khuôn sáp ong lại quan trọng trong việc đúc chuông Huế?",
            "locale": "vi",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "supported"
    assert data["locale"] == "vi"
    assert "khuôn sáp ong" in data["answer"] or "chuông Huế" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["title"] == "Kỹ thuật đúc đồng truyền thống Huế — Viện Nghiên cứu Văn hóa"
    assert "Chương 3, tr. 78-82" in data["citations"][0]["locator"]
    assert data["model_version"] == "clara-gemini-3.8-flash-tiered-v1"
    assert "nghệ nhân" in data["context_boundary"]
    assert data["epistemic_certainty"] in ("high", "medium")


def test_cultural_bridge_fail_closed_unknown_entity(client, db_session):
    """POST /api/v1/rbpc/cultural-bridge fails closed on unknown story slug."""
    res = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": "non-existent-fabricated-story-slug",
            "question": "Kỹ thuật bí mật là gì?",
            "locale": "vi",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "insufficient_evidence"
    assert data["epistemic_certainty"] == "insufficient_sources"
    assert data["citations"] == []
    assert data["review_status"] == "editorial_fallback"
    assert "Tài liệu nghiên cứu đã được phê duyệt hiện chưa ghi nhận chi tiết" in data["answer"]


def test_cultural_bridge_fail_closed_on_service_timeout(client, db_session, monkeypatch):
    """POST /api/v1/rbpc/cultural-bridge returns structured fallback on service error/timeout."""
    story, _ = _seed_rbpc_story_with_claims(db_session)

    def fake_ask_error(*args, **kwargs):
        raise TimeoutError("Clara Gemini router connection timed out after 30s")

    monkeypatch.setattr("backend.services.rbpc_ai.ask_cultural_bridge", fake_ask_error)

    res = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": story.slug,
            "question": "Quy trình pha đồng và thiếc?",
            "locale": "vi",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "insufficient_evidence"
    assert data["epistemic_certainty"] == "insufficient_sources"
    assert data["citations"] == []
    assert data["review_status"] == "editorial_fallback"
    assert "Hệ thống gặp sự cố kết nối" in (data["uncertainty_note"] or "")
