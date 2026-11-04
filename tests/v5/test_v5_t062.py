# -*- coding: utf-8 -*-
"""V5-T062 (Wave W06, Slot A02): Citation Faithfulness Validator Test Suite.

Audits and verifies:
1. Retrieval binding of generated answer spans to real retrieved source passages with precise locators (page, volume, year).
2. Quotation faithfulness validation:
   - Verifies quotes accurately reflect the retrieved source excerpt/passage.
   - Rejects or flags unfaithful, manipulated, or fabricated quotes.
3. Negative abuse & anti-hallucination guardrails:
   - Invented UUIDs fail validation with reason 'source_id_invalid' or 'source_not_found'.
   - Unretrieved sources fail with 'source_not_retrieved'.
   - Unbound claims fail with 'no_claim_source_binding'.
   - Missing or empty locators fail with 'missing_locator'.
   - Nonexistent / out-of-bounds page numbers fail with 'locator_out_of_bounds'.
   - Invented / forged locator text fails with 'invented_locator'.
4. Cross-service parity between RBPC Cultural Bridge (`rbpc_ai.py`) and History Tutor (`history_tutor.py`).
"""
from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select

from backend.models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
    User,
    UserRole,
)
from backend.services import history_tutor as tutor
from backend.services import rbpc_ai
from backend.services import history_governance as gov


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _seed_entity(db_session, slug="huyen-dinh-urn", name_vi="Huyền Đỉnh") -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type="urn",
        slug=slug,
        name_vi=name_vi,
        name_en="Huyen Dinh Urn",
        publication_status="published",
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session,
    title="Đại Nam Thực Lục Chính Biên",
    volume="Đệ nhị kỷ",
    publication_year=1848,
    content_scope="RBPC_HUE",
) -> HistoricalSource:
    source = HistoricalSource(
        source_type="official_chronicle",
        title=title,
        volume=volume,
        author_text="Quốc sử quán triều Nguyễn",
        publication_year=publication_year,
        verification_status="verified",
        content_scope=content_scope,
    )
    db_session.add(source)
    db_session.flush()
    return source


def _seed_verified_claim_with_locator(
    db_session,
    entity: HistoricalEntity,
    source: HistoricalSource,
    statement: str,
    page_start: str = "45",
    page_end: str = "48",
    chapter: str = "154",
) -> tuple[HistoricalClaim, HistoricalClaimSource]:
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type="factual",
        statement_vi=statement,
        statement_en=statement,
        confidence="high",
        origin="archival",
        verification_status="expert_verified",
        content_scope="RBPC_HUE",
        is_current=True,
    )
    db_session.add(claim)
    db_session.flush()

    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=source.id,
        support_type="supports",
        page_start=page_start,
        page_end=page_end,
        chapter=chapter,
    )
    db_session.add(binding)
    db_session.flush()
    return claim, binding


# --------------------------------------------------------------------------- #
# Test Cases
# --------------------------------------------------------------------------- #
def test_precise_locator_formatting_volume_page_year(db_session):
    """Verify locator text extraction preserves volume, chapter, page, and year."""
    entity = _seed_entity(db_session, slug="thuan-dinh-urn", name_vi="Thuần Đỉnh")
    source = _seed_source(
        db_session,
        title="Khâm Định Đại Nam Hội Điển Sự Lệ",
        volume="Tập 3",
        publication_year=1851,
    )
    claim, binding = _seed_verified_claim_with_locator(
        db_session,
        entity,
        source,
        statement="Thuần Đỉnh được đúc năm 1836.",
        page_start="102",
        page_end="105",
        chapter="Quyển 88",
    )
    db_session.commit()

    # Test history_tutor locator extraction
    ht_sources = tutor.retrieve_sources(db_session, [claim.id])
    assert str(claim.id) in ht_sources
    source_meta = ht_sources[str(claim.id)][0]
    loc = source_meta["locator"]
    assert "Tập 3" in loc
    assert "Quyển 88" in loc
    assert "tr. 102-105" in loc
    assert "năm 1851" in loc

    # Test rbpc_ai locator extraction
    rbpc_sources = rbpc_ai.retrieve_rbpc_sources(db_session, [claim.id])
    assert str(claim.id) in rbpc_sources
    rbpc_meta = rbpc_sources[str(claim.id)][0]
    rbpc_loc = rbpc_meta["locator"]
    assert "Tập 3" in rbpc_loc
    assert "Quyển 88" in rbpc_loc
    assert "tr. 102-105" in rbpc_loc
    assert "năm 1851" in rbpc_loc


def test_quotation_faithfulness_validation():
    """Verify quotation faithfulness accurately measures statement overlap."""
    source_passages = [
        "Vào mùa đông năm Ất Mùi 1835, hoàng đế Minh Mạng hạ chỉ đúc Cửu Đỉnh.",
        "Đúc xong chín đỉnh đồng lớn đặt trước sân Thế Miếu năm 1837.",
    ]

    # 1. Faithful quotes (exact substring or high token overlap)
    assert tutor.validate_quotation_faithfulness(
        "hoàng đế Minh Mạng hạ chỉ đúc Cửu Đỉnh", source_passages
    )
    assert rbpc_ai.validate_rbpc_quotation_faithfulness(
        "Mùa đông năm 1835 hoàng đế Minh Mạng hạ lệnh đúc Cửu Đỉnh", source_passages, threshold=0.7
    )

    # 2. Fabricated / ungrounded quotes fail validation
    assert not tutor.validate_quotation_faithfulness(
        "Vua Gia Long đã mua 10 chiếc đỉnh từ thương nhân người Pháp", source_passages
    )
    assert not rbpc_ai.validate_rbpc_quotation_faithfulness(
        "Công ty tư nhân đã đúc đỉnh này để làm quà lưu niệm năm 2020", source_passages
    )


def test_negative_abuse_invented_uuids_and_nonexistent_sources(db_session):
    """Assert invented UUIDs or nonexistent source records are strictly rejected."""
    entity = _seed_entity(db_session, slug="tuyen-dinh-urn", name_vi="Tuyên Đỉnh")
    source = _seed_source(db_session, title="Đại Nam Nhất Thống Chí")
    claim, _ = _seed_verified_claim_with_locator(
        db_session, entity, source, statement="Tuyên Đỉnh nằm bên phải sân Thế Miếu.", page_start="12"
    )
    db_session.commit()

    claims = tutor.retrieve_verified_claims(db_session, [entity.id])
    sources = tutor.retrieve_sources(db_session, [c.id for c in claims])
    context = tutor.build_retrieval_context(claims, sources)

    fake_uuid_1 = "not-a-valid-uuid"
    fake_uuid_2 = str(uuid.uuid4())  # valid UUID format, but nonexistent in DB

    citations = [
        {"source_id": fake_uuid_1, "claim_ids": [str(claim.id)], "locator": "tr. 12"},
        {"source_id": fake_uuid_2, "claim_ids": [str(claim.id)], "locator": "tr. 12"},
        {"source_id": str(source.id), "claim_ids": [str(claim.id)], "locator": "tr. 12"},
    ]

    valid, invalid = tutor.validate_citations(db_session, citations, context)
    assert len(valid) == 1
    assert valid[0]["source_id"] == str(source.id)
    assert len(invalid) == 2

    reasons_by_id = {c["source_id"]: reasons for c, reasons in invalid}
    assert "source_id_invalid" in reasons_by_id[fake_uuid_1]
    assert "source_not_found" in reasons_by_id[fake_uuid_2]
    assert "source_not_retrieved" in reasons_by_id[fake_uuid_2]


def test_negative_abuse_nonexistent_pages_and_invented_citations(db_session):
    """Assert nonexistent page numbers (out of bounds) or forged locators fail validation."""
    entity = _seed_entity(db_session, slug="du-dinh-urn", name_vi="Dụ Đỉnh")
    source = _seed_source(db_session, title="Mục lục Châu bản triều Nguyễn")
    claim, _ = _seed_verified_claim_with_locator(
        db_session, entity, source, statement="Dụ Đỉnh có chạm hình con vẹt.", page_start="25", page_end="28"
    )
    db_session.commit()

    claims = tutor.retrieve_verified_claims(db_session, [entity.id])
    sources = tutor.retrieve_sources(db_session, [c.id for c in claims])
    context = tutor.build_retrieval_context(claims, sources)

    citations = [
        # 1. Nonexistent wildly out of bounds page number (e.g. page 9999 when retrieved is ~25)
        {"source_id": str(source.id), "claim_ids": [str(claim.id)], "locator": "tr. 9999"},
        # 2. Fabricated / forged locator text
        {"source_id": str(source.id), "claim_ids": [str(claim.id)], "locator": "tờ bịa đặt"},
        # 3. Missing / empty locator
        {"source_id": str(source.id), "claim_ids": [str(claim.id)], "locator": ""},
        # 4. Valid locator
        {"source_id": str(source.id), "claim_ids": [str(claim.id)], "locator": "tr. 25-28"},
    ]

    valid, invalid = tutor.validate_citations(db_session, citations, context)
    assert len(valid) == 1
    assert valid[0]["locator"] == "tr. 25-28"

    invalid_reasons = {c["locator"]: reasons for c, reasons in invalid}
    assert "locator_out_of_bounds" in invalid_reasons["tr. 9999"]
    assert "invented_locator" in invalid_reasons["tờ bịa đặt"]
    assert "missing_locator" in invalid_reasons[""]


def test_rbpc_ai_citation_faithfulness_and_quotation_check(db_session):
    """Assert RBPC Cultural Bridge validator enforces quotation faithfulness and locator bounds."""
    entity = _seed_entity(db_session, slug="nhan-dinh-urn", name_vi="Nhân Đỉnh")
    source = _seed_source(db_session, title="Đồng khánh Khải định chính yếu sách")
    claim, _ = _seed_verified_claim_with_locator(
        db_session,
        entity,
        source,
        statement="Nhân Đỉnh tượng trưng cho sự nhân đức của tiên đế Minh Mạng.",
        page_start="50",
    )
    db_session.commit()

    claims = rbpc_ai.retrieve_rbpc_claims(db_session, [entity.id])
    sources = rbpc_ai.retrieve_rbpc_sources(db_session, [claim.id])
    ctx = rbpc_ai.build_rbpc_retrieval_context(claims, sources)

    # Citation with faithful quote
    faithful_citation = {
        "source_id": str(source.id),
        "claim_ids": [str(claim.id)],
        "locator": "tr. 50",
        "quote": "sự nhân đức của tiên đế Minh Mạng",
    }
    # Citation with unfaithful quote
    unfaithful_citation = {
        "source_id": str(source.id),
        "claim_ids": [str(claim.id)],
        "locator": "tr. 50",
        "quote": "Minh Mạng đã bay lên mặt trăng năm 1836",
    }

    valid_f, invalid_f = rbpc_ai.validate_rbpc_citations(db_session, [faithful_citation], ctx)
    assert len(valid_f) == 1
    assert len(invalid_f) == 0

    valid_u, invalid_u = rbpc_ai.validate_rbpc_citations(db_session, [unfaithful_citation], ctx)
    assert len(valid_u) == 0
    assert len(invalid_u) == 1
    assert "quotation_unfaithful" in invalid_u[0][1]
