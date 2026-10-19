# -*- coding: utf-8 -*-
"""Unit tests for Cultural Bridge AI service module (Phase 1, RBPC 2026)."""
from __future__ import annotations

import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uuid
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from backend.services import rbpc_ai


def test_scope_aware_retrieval_filtering():
    """Verify strictly content_scope='RBPC_HUE' and published status are retrieved."""
    claims = [
        {
            "id": str(uuid.uuid4()),
            "statement_vi": "Ngọ Môn là cổng chính phía Nam của Hoàng thành Huế.",
            "content_scope": "RBPC_HUE",
            "editorial_status": "published",
            "verification_status": "expert_verified",
        },
        {
            "id": str(uuid.uuid4()),
            "statement_vi": "Cửu Đỉnh gồm 9 đỉnh đồng đặt trước sân Thế Miếu.",
            "content_scope": "CUU_DINH",  # Legacy scope - must be filtered out
            "editorial_status": "published",
            "verification_status": "expert_verified",
        },
        {
            "id": str(uuid.uuid4()),
            "statement_vi": "Bản nháp thông tin về nghề đúc đồng Huế chưa duyệt.",
            "content_scope": "RBPC_HUE",
            "editorial_status": "draft",  # Draft - must be filtered out
            "verification_status": "unreviewed",
        },
        {
            "id": str(uuid.uuid4()),
            "statement_vi": "Lăng Tự Đức mang phong cách kiến trúc viên lâm đặc sắc.",
            "content_scope": "RBPC_HUE",
            "editorial_status": "published",
            "verification_status": "editor_reviewed",
        },
    ]

    filtered = rbpc_ai.retrieve_rbpc_claims(
        db=None,
        query="Ngọ Môn",
        content_scope="RBPC_HUE",
        editorial_status="published",
        claims_source=claims,
    )

    assert len(filtered) == 2
    scopes = {c["content_scope"] for c in filtered}
    assert scopes == {"RBPC_HUE"}
    statuses = {c["editorial_status"] for c in filtered}
    assert statuses == {"published"}
    assert "Ngọ Môn" in filtered[0]["statement_vi"]


def test_bilingual_prompt_construction_and_rules():
    """Verify delimiters, anti-hallucination mandate, and artisan dignity rule in prompts."""
    prompt_vi = rbpc_ai.build_rbpc_system_prompt("vi")
    prompt_en = rbpc_ai.build_rbpc_system_prompt("en")

    # Delimiter boundaries
    assert "[[[CLAIM_START]]]" in prompt_vi
    assert "[[[CLAIM_END]]]" in prompt_vi
    assert "[[[CLAIM_START]]]" in prompt_en
    assert "[[[CLAIM_END]]]" in prompt_en

    # Anti-hallucination mandate
    assert "NGUYÊN TẮC CHỐNG ẢO GIÁC" in prompt_vi
    assert "khoảng trống bằng chứng" in prompt_vi
    assert "ANTI-HALLUCINATION MANDATE" in prompt_en
    assert "evidence gap" in prompt_en

    # Artisan dignity rule
    assert "QUY TẮC TÔN TRỌNG PHẨM GIÁ NGHỆ NHÂN" in prompt_vi
    assert "1835" in prompt_vi
    assert "ARTISAN DIGNITY RULE" in prompt_en
    assert "1835" in prompt_en
    assert "imperial antiquities" in prompt_en

    # Dynamic message construction with context
    cid = str(uuid.uuid4())
    context = rbpc_ai.RBPCRetrievalContext(
        "[[[CLAIM_START]]]\nStatement: Huế có 14 cụm di tích UNESCO.\n[[[CLAIM_END]]]",
        claims=[{"id": cid, "statement_vi": "Huế có 14 cụm di tích UNESCO."}],
        sources_by_claim={},
    )
    messages_vi = rbpc_ai.build_rbpc_prompt_messages("Huế có bao nhiêu di tích?", context, locale="vi")
    assert len(messages_vi) == 2
    assert messages_vi[0]["role"] == "system"
    assert messages_vi[1]["role"] == "user"
    assert "[[[CLAIM_START]]]" in messages_vi[1]["content"]


def test_post_generation_citation_validator_5_points():
    """Verify 5-point citation validation: invalid UUID, not found, not retrieved, no binding, missing locator."""
    source_valid = str(uuid.uuid4())
    claim_valid = str(uuid.uuid4())
    source_unretrieved = str(uuid.uuid4())

    source_valid2 = str(uuid.uuid4())
    context = rbpc_ai.RBPCRetrievalContext(
        "context-text",
        claims=[{"id": claim_valid, "statement_vi": "Điện Thái Hòa được trùng tu."}],
        sources_by_claim={
            claim_valid: [
                {
                    "source_id": source_valid,
                    "title": "Hồ sơ UNESCO 678",
                    "locator": "tr. 45",
                },
                {
                    "source_id": source_valid2,
                    "title": "Đại Nam Thực Lục",
                    "locator": "Tập 2",
                },
            ]
        },
    )

    citations = [
        # 1. Valid citation
        {
            "source_id": source_valid,
            "claim_ids": [claim_valid],
            "locator": "tr. 45",
        },
        # 2. Invalid UUID format
        {
            "source_id": "not-a-uuid-1234",
            "claim_ids": [claim_valid],
            "locator": "tr. 10",
        },
        # 3. Source not retrieved
        {
            "source_id": source_unretrieved,
            "claim_ids": [claim_valid],
            "locator": "tr. 20",
        },
        # 4. No claim-source binding
        {
            "source_id": source_valid,
            "claim_ids": [str(uuid.uuid4())],  # non-bound claim
            "locator": "tr. 45",
        },
        # 5. Missing locator
        {
            "source_id": source_valid2,
            "claim_ids": [claim_valid],
            "locator": "",
        },
    ]

    valid, invalid = rbpc_ai.validate_rbpc_citations(db=None, citations=citations, retrieved_context=context)

    assert len(valid) == 1
    assert valid[0]["source_id"] == source_valid

    assert len(invalid) == 4
    reasons_by_source = {c["source_id"]: reasons for c, reasons in invalid}

    assert "source_id_invalid" in reasons_by_source["not-a-uuid-1234"]
    assert "source_not_retrieved" in reasons_by_source[source_unretrieved]
    assert "no_claim_source_binding" in reasons_by_source[source_valid]
    assert "missing_locator" in reasons_by_source[source_valid2]


def test_unsupported_assertion_checker_and_disclaimer():
    """Verify unsupported factual statements are flagged while disclaimers are preserved."""
    claim_id = str(uuid.uuid4())
    context = rbpc_ai.RBPCRetrievalContext(
        "context",
        claims=[
            {
                "id": claim_id,
                "statement_vi": "Chùa Thiên Mụ được xây dựng năm 1601 thời chúa Nguyễn Hoàng.",
            }
        ],
        sources_by_claim={},
        entities={"e1": {"label": "Chùa Thiên Mụ"}},
    )

    answer_grounded = (
        "Chùa Thiên Mụ được khởi lập vào năm 1601 dưới thời chúa Nguyễn Hoàng. "
        "Hiện chưa có đủ bằng chứng đã kiểm chứng về số lượng tượng đồng nguyên bản."
    )
    flagged = rbpc_ai.check_rbpc_unsupported_assertions(answer_grounded, context, locale="vi")
    assert len(flagged) == 0

    answer_hallucinated = (
        "Chùa Thiên Mụ được khởi lập năm 1601. "
        "Vào năm 1999 chính phủ Pháp đã tài trợ 50 triệu USD để đúc tượng vàng tại chùa."
    )
    flagged_hallucinated = rbpc_ai.check_rbpc_unsupported_assertions(answer_hallucinated, context, locale="vi")
    assert len(flagged_hallucinated) >= 1
    assert "50 triệu USD" in flagged_hallucinated[0]

    qualified = rbpc_ai.attach_epistemic_disclaimer(answer_hallucinated, flagged_hallucinated, locale="vi")
    assert "Lưu ý thẩm định" in qualified
    assert "50 triệu USD" in qualified


def test_deterministic_zero_hallucination_fallback():
    """Verify deterministic fallback handles both empty evidence and verified claims."""
    # 1. Empty evidence -> structured evidence gap refusal
    empty_context = rbpc_ai.RBPCRetrievalContext("", claims=[], sources_by_claim={})
    res_empty_vi = rbpc_ai.build_rbpc_deterministic_answer(
        "Có bao nhiêu khẩu đại bác trong kinh thành?", [], empty_context, locale="vi"
    )
    assert res_empty_vi["confidence"] == "low"
    assert "khoảng trống bằng chứng" in res_empty_vi["answer_markdown"]
    assert res_empty_vi["citations"] == []

    res_empty_en = rbpc_ai.build_rbpc_deterministic_answer(
        "How many cannons were cast?", [], empty_context, locale="en"
    )
    assert "evidence gap" in res_empty_en["answer_markdown"]

    # 2. Available claims -> verbatim synthesis with artisan dignity note
    cid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    claim = {
        "id": cid,
        "statement_vi": "Nghệ nhân đúc đồng Phường Đúc thực hành phương pháp thủ công cổ truyền.",
        "statement_en": "Artisans in Phường Đúc practice traditional bronze casting methods.",
        "verification_status": "expert_verified",
        "editorial_status": "published",
    }
    context = rbpc_ai.RBPCRetrievalContext(
        "context",
        claims=[claim],
        sources_by_claim={
            cid: [
                {
                    "source_id": sid,
                    "title": "Nghề đồng Huế",
                    "locator": "tr. 12",
                }
            ]
        },
    )

    res_verified = rbpc_ai.build_rbpc_deterministic_answer(
        "Sản phẩm đúc đồng của nghệ nhân có phải cổ vật không?",
        [claim],
        context,
        locale="vi",
    )
    assert res_verified["confidence"] in ("medium", "high")
    assert "Phẩm giá nghệ nhân" in res_verified["answer_markdown"] or "phẩm giá nghệ nhân" in res_verified["answer_markdown"]
    assert len(res_verified["citations"]) == 1
    assert res_verified["citations"][0]["source_id"] == sid


def test_clara_gemini_router_error_graceful_fallback(monkeypatch):
    """Verify Clara Gemini router failure gracefully degrades to zero-hallucination fallback."""
    cid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    claim = {
        "id": cid,
        "statement_vi": "Nhã nhạc cung đình Huế được UNESCO công nhận năm 2003.",
        "verification_status": "expert_verified",
        "editorial_status": "published",
        "content_scope": "RBPC_HUE",
    }
    sources = {
        cid: [
            {
                "source_id": sid,
                "title": "Hồ sơ Nhã nhạc UNESCO",
                "locator": "Mục II.1",
            }
        ]
    }

    # Simulate network failure on Clara router
    def fake_call_chat(*args, **kwargs):
        raise RuntimeError("Clara router connection timed out.")

    monkeypatch.setattr(rbpc_ai, "call_clara_gemini_chat", fake_call_chat)
    monkeypatch.setenv("CLARA_API_KEY", "test-key")

    result = rbpc_ai.ask_cultural_bridge(
        db=None,
        question="Nhã nhạc được UNESCO công nhận năm nào?",
        locale="vi",
        claims_override=[claim],
        sources_override=sources,
        use_llm=True,
    )

    # Must not raise 500 / error; must return grounded deterministic answer
    assert "Nhã nhạc cung đình Huế" in result["answer_markdown"]
    assert "2003" in result["answer_markdown"]
    assert len(result["citations"]) == 1
    assert result["citations"][0]["source_id"] == sid
