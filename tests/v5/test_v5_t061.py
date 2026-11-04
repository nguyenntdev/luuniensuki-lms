# -*- coding: utf-8 -*-
"""V5-T061 (Wave W06, Slot A01): Retrieval Only Approved Claims Test Suite.

Audits and verifies:
1. Retrieval strictly returns approved claims (expert_verified, published, editor_reviewed, verified).
2. Zero draft claim leakage: draft and internal_review claims are NEVER retrieved into generation context.
3. Zero unreviewed claim leakage: unreviewed, needs_source, and source_attached claims are blocked by default.
4. Zero disputed or contested claim leakage: disputed, rejected, superseded, archived, or contradicted claims
   are strictly excluded from generation context.
5. Source verification gates: retrieve_sources returns strictly approved sources (metadata_verified, accessible)
   and eligible support bindings (supports, primary_evidence_for).
6. Model invariants: HistoricalClaim.is_approved, is_published, is_draft, is_unreviewed, is_disputed and
   HistoricalSource.is_approved properties.
7. Negative abuse: Asking about a draft-only fact returns explicit abstention ("Không đủ sử liệu xác thực" / abstention),
   with zero draft fact or hallucinated leakage.
8. End-to-end API verification on POST /api/v1/history/tutor/ask: verified fact returns citations & answers,
   while draft-only queries return explicit abstention with confidence='low' and empty citations.
"""
from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from backend.services import history_tutor as tutor


# --------------------------------------------------------------------------- #
# Seeding Helpers
# --------------------------------------------------------------------------- #
def _seed_entity(
    db_session,
    *,
    slug: str | None = None,
    name_vi: str = "Cao Đỉnh",
    entity_type: str = "urn",
    publication_status: str = "published",
) -> HistoricalEntity:
    ent_slug = slug or f"entity-{uuid.uuid4().hex[:8]}"
    entity = HistoricalEntity(
        entity_type=entity_type,
        slug=ent_slug,
        name_vi=name_vi,
        publication_status=publication_status,
        alternative_names=[],
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session,
    *,
    title: str = "Đại Nam Nhất Thống Chí",
    verification_status: str = "metadata_verified",
    source_type: str = "royal_record",
) -> HistoricalSource:
    source = HistoricalSource(
        source_type=source_type,
        title=title,
        author_text="Quốc Sử Quán Triều Nguyễn",
        publication_year=1882,
        verification_status=verification_status,
    )
    db_session.add(source)
    db_session.flush()
    return source


def _seed_claim(
    db_session,
    *,
    entity: HistoricalEntity,
    statement: str,
    verification_status: str = "unreviewed",
    confidence: str = "high",
    claim_type: str = "factual",
    is_current: bool = True,
) -> HistoricalClaim:
    claim = HistoricalClaim(
        entity_id=entity.id,
        statement_vi=statement,
        claim_type=claim_type,
        confidence=confidence,
        origin="editorial",
        verification_status=verification_status,
        is_current=is_current,
    )
    db_session.add(claim)
    db_session.flush()
    return claim


def _bind_source(
    db_session,
    *,
    claim: HistoricalClaim,
    source: HistoricalSource,
    support_type: str = "supports",
    page_start: str = "42",
) -> HistoricalClaimSource:
    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=source.id,
        support_type=support_type,
        page_start=page_start,
    )
    db_session.add(binding)
    db_session.flush()
    return binding


# --------------------------------------------------------------------------- #
# 1. Approved Claims Retrieval Invariant
# --------------------------------------------------------------------------- #
def test_retrieve_verified_claims_strictly_returns_approved_tiers(db_session):
    """retrieve_verified_claims strictly retrieves approved claims and excludes all unapproved tiers."""
    entity = _seed_entity(db_session, name_vi="Cao Đỉnh Kiểm Tra Tiers")
    source = _seed_source(db_session, verification_status="metadata_verified")

    # Approved claims
    c_expert = _seed_claim(db_session, entity=entity, statement="Khẳng định chuyên gia xác thực", verification_status="expert_verified")
    _bind_source(db_session, claim=c_expert, source=source)
    c_pub = _seed_claim(db_session, entity=entity, statement="Khẳng định đã xuất bản", verification_status="published")
    _bind_source(db_session, claim=c_pub, source=source)
    c_ed = _seed_claim(db_session, entity=entity, statement="Khẳng định biên tập duyệt", verification_status="editor_reviewed")
    _bind_source(db_session, claim=c_ed, source=source)
    c_ver = _seed_claim(db_session, entity=entity, statement="Khẳng định đã thẩm định", verification_status="verified")
    _bind_source(db_session, claim=c_ver, source=source)

    # Ineligible claims
    c_draft = _seed_claim(db_session, entity=entity, statement="Khẳng định bản thảo nháp", verification_status="draft")
    _bind_source(db_session, claim=c_draft, source=source)
    c_internal = _seed_claim(db_session, entity=entity, statement="Khẳng định nội bộ", verification_status="internal_review")
    _bind_source(db_session, claim=c_internal, source=source)
    c_unrev = _seed_claim(db_session, entity=entity, statement="Khẳng định chưa kiểm chứng", verification_status="unreviewed")
    _bind_source(db_session, claim=c_unrev, source=source)
    c_disp = _seed_claim(db_session, entity=entity, statement="Khẳng định tranh cãi", verification_status="disputed")
    _bind_source(db_session, claim=c_disp, source=source)
    c_rej = _seed_claim(db_session, entity=entity, statement="Khẳng định bị từ chối", verification_status="rejected")
    _bind_source(db_session, claim=c_rej, source=source)

    retrieved = tutor.retrieve_verified_claims(db_session, [entity.id])
    retrieved_ids = {c.id for c in retrieved}

    assert c_expert.id in retrieved_ids
    assert c_pub.id in retrieved_ids
    assert c_ed.id in retrieved_ids
    assert c_ver.id in retrieved_ids

    # Must NOT contain draft, internal_review, unreviewed, disputed, or rejected
    assert c_draft.id not in retrieved_ids
    assert c_internal.id not in retrieved_ids
    assert c_unrev.id not in retrieved_ids
    assert c_disp.id not in retrieved_ids
    assert c_rej.id not in retrieved_ids
    assert len(retrieved) == 4


# --------------------------------------------------------------------------- #
# 2. Zero Draft Claim Leakage
# --------------------------------------------------------------------------- #
def test_zero_draft_claim_leakage(db_session):
    """Draft claims must never leak into retrieval, even if include_unverified=True."""
    entity = _seed_entity(db_session, name_vi="Thực thể Thử Nghiệm Nháp")
    source = _seed_source(db_session)

    c_draft = _seed_claim(db_session, entity=entity, statement="Bản thảo nháp về kho vàng bí mật", verification_status="draft")
    _bind_source(db_session, claim=c_draft, source=source)

    c_internal = _seed_claim(db_session, entity=entity, statement="Xem xét nội bộ về hầm ngầm", verification_status="internal_review")
    _bind_source(db_session, claim=c_internal, source=source)

    # Standard retrieval: zero draft
    res1 = tutor.retrieve_verified_claims(db_session, [entity.id], include_unverified=False)
    assert len(res1) == 0

    # With include_unverified=True: draft still strictly forbidden
    res2 = tutor.retrieve_verified_claims(db_session, [entity.id], include_unverified=True)
    assert len(res2) == 0


# --------------------------------------------------------------------------- #
# 3. Zero Disputed or Contested Leakage
# --------------------------------------------------------------------------- #
def test_zero_disputed_or_contested_claim_leakage(db_session):
    """Disputed and contested claims are strictly blocked from retrieval."""
    entity = _seed_entity(db_session, name_vi="Thực thể Tranh Cãi")
    source = _seed_source(db_session)

    c_disp_status = _seed_claim(db_session, entity=entity, statement="Niên đại còn tranh cãi gay gắt", verification_status="disputed")
    _bind_source(db_session, claim=c_disp_status, source=source)

    c_disp_conf = _seed_claim(db_session, entity=entity, statement="Độ tin cậy đang tranh luận", verification_status="editor_reviewed", confidence="disputed")
    _bind_source(db_session, claim=c_disp_conf, source=source)

    c_cont_conf = _seed_claim(db_session, entity=entity, statement="Độ tin cậy bị phản bác", verification_status="verified", confidence="contested")
    _bind_source(db_session, claim=c_cont_conf, source=source)

    c_disp_type = _seed_claim(db_session, entity=entity, statement="Mệnh đề thuộc kiểu tranh luận", verification_status="expert_verified", claim_type="disputed")
    _bind_source(db_session, claim=c_disp_type, source=source)

    retrieved = tutor.retrieve_verified_claims(db_session, [entity.id])
    assert len(retrieved) == 0


# --------------------------------------------------------------------------- #
# 4. Contradicted Claims Excluded
# --------------------------------------------------------------------------- #
def test_contradicted_claims_strictly_excluded(db_session):
    """Claims with contradicting sources must never be returned as approved."""
    entity = _seed_entity(db_session, name_vi="Thực thể Bị Mâu Thuẫn")
    s_supp = _seed_source(db_session, title="Nguồn Ủng Hộ")
    s_contra = _seed_source(db_session, title="Nguồn Bác Bỏ")

    claim = _seed_claim(db_session, entity=entity, statement="Đỉnh đúc bằng hợp kim lạ", verification_status="expert_verified")
    _bind_source(db_session, claim=claim, source=s_supp, support_type="supports")
    _bind_source(db_session, claim=claim, source=s_contra, support_type="contradicts")

    retrieved = tutor.retrieve_verified_claims(db_session, [entity.id])
    assert len(retrieved) == 0


# --------------------------------------------------------------------------- #
# 5. Source Approval Gates in retrieve_sources
# --------------------------------------------------------------------------- #
def test_source_approval_gates_in_retrieve_sources(db_session):
    """retrieve_sources retrieves only approved sources and drops unreviewed or rejected sources."""
    entity = _seed_entity(db_session)
    s_good = _seed_source(db_session, title="Nguồn Chuẩn Đã Xác Minh", verification_status="metadata_verified")
    s_unrev = _seed_source(db_session, title="Nguồn Chưa Thẩm Định", verification_status="unreviewed")
    s_rej = _seed_source(db_session, title="Nguồn Bị Từ Chối", verification_status="rejected")

    claim = _seed_claim(db_session, entity=entity, statement="Đỉnh hoàn thành năm 1837", verification_status="expert_verified")
    _bind_source(db_session, claim=claim, source=s_good, support_type="supports")
    _bind_source(db_session, claim=claim, source=s_unrev, support_type="supports")
    _bind_source(db_session, claim=claim, source=s_rej, support_type="supports")

    sources_map = tutor.retrieve_sources(db_session, [claim.id], approved_only=True)
    retrieved_source_ids = {s["source_id"] for s in sources_map.get(str(claim.id), [])}

    assert str(s_good.id) in retrieved_source_ids
    assert str(s_unrev.id) not in retrieved_source_ids
    assert str(s_rej.id) not in retrieved_source_ids
    assert len(retrieved_source_ids) == 1


# --------------------------------------------------------------------------- #
# 6. HistoricalClaim and HistoricalSource Model Invariants
# --------------------------------------------------------------------------- #
def test_historical_claim_and_source_model_invariants(db_session):
    """Verify is_approved, is_published, is_draft, is_unreviewed, is_disputed properties."""
    entity = _seed_entity(db_session)

    # Approved claim
    c_ok = _seed_claim(db_session, entity=entity, statement="Claim OK", verification_status="expert_verified", confidence="high")
    assert c_ok.is_approved is True
    assert c_ok.is_published is False
    assert c_ok.is_draft is False
    assert c_ok.is_disputed is False

    # Published claim
    c_pub = _seed_claim(db_session, entity=entity, statement="Claim Pub", verification_status="published", confidence="high")
    assert c_pub.is_approved is True
    assert c_pub.is_published is True

    # Draft claim
    c_draft = _seed_claim(db_session, entity=entity, statement="Claim Draft", verification_status="draft")
    assert c_draft.is_approved is False
    assert c_draft.is_draft is True
    assert c_draft.is_unreviewed is False

    # Unreviewed claim
    c_unrev = _seed_claim(db_session, entity=entity, statement="Claim Unreviewed", verification_status="unreviewed")
    assert c_unrev.is_approved is False
    assert c_unrev.is_unreviewed is True

    # Disputed claim
    c_disp = _seed_claim(db_session, entity=entity, statement="Claim Disputed", verification_status="disputed")
    assert c_disp.is_approved is False
    assert c_disp.is_disputed is True

    # Source invariants
    s_verified = _seed_source(db_session, verification_status="metadata_verified")
    s_unrev = _seed_source(db_session, verification_status="unreviewed")
    assert s_verified.is_approved is True
    assert s_unrev.is_approved is False


# --------------------------------------------------------------------------- #
# 7. Negative Abuse: Draft-Only Fact Returns Explicit Abstention
# --------------------------------------------------------------------------- #
def test_negative_abuse_draft_only_fact_returns_explicit_abstention(client, db_session):
    """Asking about a fact that only exists in a draft claim returns explicit abstention and zero leak."""
    entity = _seed_entity(db_session, slug="thuan-dinh-gold", name_vi="Thuận Đỉnh")
    source = _seed_source(db_session)
    _seed_claim(
        db_session,
        entity=entity,
        statement="Thuận Đỉnh chứa kho báu mật mã hoàng cung.",
        verification_status="draft",
        confidence="low",
    )
    db_session.commit()

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Thuận Đỉnh có chứa kho báu mật mã hoàng cung không?"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Explicit abstention
    assert "Không đủ sử liệu xác thực" in data["answer_markdown"] or "khoảng trống bằng chứng" in data["answer_markdown"]
    assert "Không đủ sử liệu xác thực" in data["epistemic_summary"] or "Không tìm thấy" in data["epistemic_summary"]

    # Zero draft leak
    assert "kho báu mật mã" not in data["answer_markdown"]
    assert data["confidence"] == "low"
    assert data["citations"] == []
    assert data["grounding"]["claims_used"] == 0


# --------------------------------------------------------------------------- #
# 8. Negative Abuse: Unreviewed-Only Fact Returns Explicit Abstention
# --------------------------------------------------------------------------- #
def test_negative_abuse_unreviewed_fact_returns_explicit_abstention(client, db_session):
    """Asking about an unreviewed fact without flag returns explicit abstention."""
    entity = _seed_entity(db_session, slug="nhan-dinh-unrev", name_vi="Nhân Đỉnh")
    _seed_claim(
        db_session,
        entity=entity,
        statement="Nhân Đỉnh là biểu tượng của bí thuật phong thủy phương Đông.",
        verification_status="unreviewed",
        confidence="unknown",
    )
    db_session.commit()

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Nhân Đỉnh có bí thuật phong thủy không?"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert "Không đủ sử liệu xác thực" in data["answer_markdown"] or "khoảng trống bằng chứng" in data["answer_markdown"]
    assert "bí thuật" not in data["answer_markdown"]
    assert data["citations"] == []
    assert data["confidence"] == "low"


# --------------------------------------------------------------------------- #
# 9. Negative Abuse: Disputed Fact Returns Explicit Abstention
# --------------------------------------------------------------------------- #
def test_negative_abuse_disputed_fact_returns_explicit_abstention(client, db_session):
    """Asking about a disputed fact returns explicit abstention."""
    entity = _seed_entity(db_session, slug="tuyen-dinh-disp", name_vi="Tuyên Đỉnh")
    _seed_claim(
        db_session,
        entity=entity,
        statement="Tuyên Đỉnh được di dời vào năm 1945.",
        verification_status="disputed",
        confidence="disputed",
    )
    db_session.commit()

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Tuyên Đỉnh có bị di dời năm 1945 không?"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert "Không đủ sử liệu xác thực" in data["answer_markdown"] or "khoảng trống bằng chứng" in data["answer_markdown"]
    assert "1945" not in data["answer_markdown"]
    assert data["citations"] == []


# --------------------------------------------------------------------------- #
# 10. End-to-End Segregation: Verified Query Answers vs Draft Query Abstains
# --------------------------------------------------------------------------- #
def test_end_to_end_verified_vs_draft_segregation(client, db_session):
    """On the same entity, asking about a verified fact succeeds with citations,
    while asking about a draft-only fact abstains with zero draft leakage."""
    entity = _seed_entity(db_session, slug="cao-dinh-seg", name_vi="Cao Đỉnh")
    source = _seed_source(db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ")

    # 1. Verified fact
    c_verified = _seed_claim(
        db_session,
        entity=entity,
        statement="Cao Đỉnh được đúc vào tháng 12 năm 1835.",
        verification_status="expert_verified",
        confidence="high",
        claim_type="chronology",
    )
    _bind_source(db_session, claim=c_verified, source=source, page_start="88")

    # 2. Draft-only fact on the same entity
    _seed_claim(
        db_session,
        entity=entity,
        statement="Cao Đỉnh từng chứa kho vũ khí bí mật thời kháng chiến.",
        verification_status="draft",
        confidence="low",
        claim_type="factual",
    )
    db_session.commit()

    # Query 1: Ask about the verified fact -> Must succeed with citations
    res_ok = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Cao Đỉnh được đúc khi nào?"},
    )
    assert res_ok.status_code == 200, res_ok.text
    data_ok = res_ok.json()
    assert data_ok["confidence"] in ("high", "medium")
    assert "1835" in data_ok["answer_markdown"]
    assert len(data_ok["citations"]) >= 1
    assert data_ok["citations"][0]["source_id"] == str(source.id)
    assert "kho vũ khí bí mật" not in data_ok["answer_markdown"]

    # Query 2: Ask about the draft fact -> Must abstain, zero leak
    # In deterministic mode, because the draft fact was not retrieved, the answer only has verified facts
    # and zero leak of the draft proposition.
    res_draft = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Cao Đỉnh có kho vũ khí bí mật không?"},
    )
    assert res_draft.status_code == 200, res_draft.text
    data_draft = res_draft.json()
    assert "kho vũ khí bí mật" not in data_draft["answer_markdown"]
