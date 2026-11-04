# -*- coding: utf-8 -*-
"""V5-T024 (Wave W02, Slot A04): Atomic Historical Claims Test Suite.

Audits and verifies:
1. Atomic statement granularity: claims must be discrete assertions, not monolithic paragraphs,
   so false or disputed statements cannot hide behind a single citation.
2. Decomposition into atomic claims: paragraphs are decomposed into discrete verifiable statements.
3. Compound claim rejection: rejects compound statements bundling multiple distinct facts or
   hiding disputed propositions.
4. Source relation links (supports vs contradicts vs mentions/contextualizes):
   - Explicit support types in HistoricalSupportType.
   - Only eligible support types ('supports', 'primary_evidence_for') permit verification.
   - Contradicting sources ('contradicts') are tracked and block verification.
5. Epistemic certainty tracking:
   - Explicit certainty levels in HistoricalConfidence ('high', 'medium', 'low', 'disputed').
   - Contradicted or disputed claims CANNOT be masked as verified (negative abuse tests).
   - Attaching a contradicting source immediately demotes an expert_verified claim to 'disputed'.
6. AI Tutor citation & synthesis:
   - AI Tutor cites specific atomic claim IDs and their verification status when synthesizing explanations.
"""
from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select

from backend.domain.atomic_claims import (
    can_verify_atomic_claim,
    claim_has_contradicting_source,
    decompose_into_atomic_claims,
    reject_compound_claim_with_disputed_facts,
    synthesize_atomic_explanations,
    validate_atomic_claim,
)
from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalConfidence,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalSource,
    HistoricalSupportType,
    HistoricalVerificationStatus,
)
from backend.models import User, UserRole
from backend.services import history_governance as gov
from backend.services import history_tutor as tutor


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _make_staff(client, db_session, email: str, display_name: str = "Admin"):
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


def _seed_entity(db_session, slug: str = "cao-dinh-urn", name_vi: str = "Cao Đỉnh") -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type="urn",
        slug=slug,
        name_vi=name_vi,
        publication_status="published",
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session,
    title: str = "Đại Nam Nhất Thống Chí",
    source_type: str = "royal_record",
    author_text: str = "Quốc Sử Quán Triều Nguyễn",
) -> HistoricalSource:
    source = HistoricalSource(
        source_type=source_type,
        title=title,
        author_text=author_text,
        publication_year=1882,
        verification_status="metadata_verified",
    )
    db_session.add(source)
    db_session.flush()
    return source


def _seed_claim(
    db_session,
    entity: HistoricalEntity,
    statement: str,
    *,
    claim_type: str = "chronology",
    confidence: str = "high",
    verification_status: str = "unreviewed",
) -> HistoricalClaim:
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type=claim_type,
        statement_vi=statement,
        confidence=confidence,
        origin="editorial",
        verification_status=verification_status,
    )
    db_session.add(claim)
    db_session.flush()
    return claim


# --------------------------------------------------------------------------- #
# 1. Atomic Claim Decomposition
# --------------------------------------------------------------------------- #
def test_atomic_claim_decomposition():
    """Verify that a monolithic historical paragraph is accurately decomposed into

    discrete atomic assertions that pass atomic validation.
    """
    compound_paragraph = (
        "Cao Đỉnh là chiếc đỉnh đồng lớn nhất trong Cửu Đỉnh được đặt trước sân Thế Miếu. "
        "Đỉnh được khởi đúc vào mùa đông năm Ất Mùi 1835 dưới triều vua Minh Mạng. "
        "Trên thân Cao Đỉnh có chạm khắc 17 hình ảnh biểu tượng của sơn hà xã tắc Việt Nam."
    )

    atomic_claims = decompose_into_atomic_claims(compound_paragraph)

    assert len(atomic_claims) == 3, f"Expected 3 atomic claims, got {len(atomic_claims)}"
    assert "lớn nhất trong Cửu Đỉnh" in atomic_claims[0]
    assert "1835" in atomic_claims[1]
    assert "17 hình ảnh" in atomic_claims[2]

    for stmt in atomic_claims:
        is_atomic, err = validate_atomic_claim(stmt)
        assert is_atomic is True, f"Decomposed claim failed validation: {err}"


# --------------------------------------------------------------------------- #
# 2. Atomic Claim Validation Rejects Compound Monoliths
# --------------------------------------------------------------------------- #
def test_atomic_claim_validation_rejects_compound_monolith(client, db_session):
    """Verify that multi-sentence or multi-paragraph compound statements are rejected

    by the atomic validator and the admin claim creation endpoint.
    """
    admin_user = _make_staff(client, db_session, f"admin_t024_1_{uuid.uuid4().hex[:6]}@example.com")
    entity = _seed_entity(db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Cao Đỉnh")
    db_session.commit()

    compound_stmt = (
        "Cao Đỉnh được đúc vào năm 1835. Nó nặng hơn 2600kg và được chế tác hoàn toàn từ đồng đỏ."
    )

    is_atomic, err_msg = validate_atomic_claim(compound_stmt)
    assert is_atomic is False
    assert "Compound claim detected" in err_msg
    assert "distinct sentences" in err_msg

    multiline_stmt = "Cao Đỉnh được đúc năm 1835.\nNó được làm bằng đồng."
    is_atomic_nl, err_nl = validate_atomic_claim(multiline_stmt)
    assert is_atomic_nl is False
    assert "newline breaks" in err_nl

    # Attempting to post a compound statement via API returns 422
    res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "statement_vi": compound_stmt,
            "claim_type": "factual",
            "origin": "editorial",
        },
    )
    assert res.status_code == 422, f"Expected 422 for compound statement, got: {res.text}"
    data = res.json()
    assert "error" in data
    assert "Compound claim detected" in data["error"]["message"]


# --------------------------------------------------------------------------- #
# 3. Rejects Compound Claims Hiding Disputed Facts
# --------------------------------------------------------------------------- #
def test_reject_compound_claim_hiding_disputed_facts(db_session):
    """Negative abuse test: One false or disputed statement cannot hide inside an

    approved compound statement.
    """
    entity = _seed_entity(db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Nhân Đỉnh")

    # Claim 1: Verified true fact
    claim_verified = _seed_claim(
        db_session,
        entity=entity,
        statement="Nhân Đỉnh được đúc vào tháng 12 năm 1835.",
        confidence=HistoricalConfidence.high.value,
        verification_status=HistoricalVerificationStatus.expert_verified.value,
    )

    # Claim 2: Disputed / false assertion
    claim_disputed = _seed_claim(
        db_session,
        entity=entity,
        statement="Nhân Đỉnh được chế tác hoàn toàn bằng vàng ròng 24K nguyên chất.",
        confidence=HistoricalConfidence.disputed.value,
        verification_status=HistoricalVerificationStatus.disputed.value,
    )
    db_session.flush()

    # An author attempts to submit a compound paragraph blending both
    compound_submission = (
        "Nhân Đỉnh được đúc vào tháng 12 năm 1835 hoàn toàn bằng vàng ròng 24K nguyên chất theo lệnh vua."
    )

    is_valid, reason = reject_compound_claim_with_disputed_facts(
        compound_submission, [claim_verified, claim_disputed]
    )
    assert is_valid is False
    assert "hides disputed or contradicted assertion" in reason
    assert str(claim_disputed.id) in reason


# --------------------------------------------------------------------------- #
# 4. Negative Abuse: Contradicted Claim Cannot Be Masked as Verified
# --------------------------------------------------------------------------- #
def test_negative_abuse_cannot_mask_contradicted_claim_as_verified(client, db_session):
    """Negative abuse test: A claim contradicted by an attached source cannot be

    verified as expert_verified or editor_reviewed.
    """
    admin_user = _make_staff(client, db_session, f"admin_t024_2_{uuid.uuid4().hex[:6]}@example.com")
    entity = _seed_entity(db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Thuần Đỉnh")
    src_support = _seed_source(db_session, title="Tài liệu ủng hộ", source_type="scholarly_book")
    src_contradict = _seed_source(db_session, title="Khảo sát kim loại học", source_type="peer_reviewed_article")

    claim = _seed_claim(
        db_session,
        entity=entity,
        statement="Thuần Đỉnh được chế tác từ kim loại bạch kim.",
        claim_type="material",
        confidence="medium",
        verification_status="unreviewed",
    )
    db_session.flush()

    # Attach supporting source
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=src_support,
        data={"support_type": HistoricalSupportType.supports.value, "page_start": "10"},
        actor_id=admin_user.id,
    )
    # Attach contradicting source
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=src_contradict,
        data={"support_type": HistoricalSupportType.contradicts.value, "page_start": "45"},
        actor_id=admin_user.id,
    )
    db_session.commit()

    # Verify claim is flagged as having contradiction
    assert claim_has_contradicting_source(db_session, claim) is True

    # 1. Direct service layer rejection
    with pytest.raises(ValueError, match="Contradicted claim cannot be approved as editor_reviewed"):
        gov.transition_claim_status(
            db_session, claim=claim, target="editor_reviewed", actor_id=admin_user.id
        )

    with pytest.raises(ValueError, match="Contradicted claim cannot be marked as expert_verified"):
        gov.transition_claim_status(
            db_session, claim=claim, target="expert_verified", actor_id=admin_user.id
        )

    # 2. HTTP Admin API rejection
    res = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "expert_verified"},
    )
    assert res.status_code == 422
    assert "HISTORY_CLAIM_INVALID_TRANSITION" in res.text
    assert "Contradicted claim" in res.text


# --------------------------------------------------------------------------- #
# 5. Negative Abuse: Disputed Confidence Cannot Be Masked as Verified
# --------------------------------------------------------------------------- #
def test_negative_abuse_cannot_mask_disputed_confidence_as_verified(client, db_session):
    """Negative abuse test: A claim marked with confidence='disputed' cannot be

    verified as expert_verified.
    """
    admin_user = _make_staff(client, db_session, f"admin_t024_3_{uuid.uuid4().hex[:6]}@example.com")
    entity = _seed_entity(db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Dụ Đỉnh")
    src = _seed_source(db_session, title="Ghi chép dã sử")

    claim = _seed_claim(
        db_session,
        entity=entity,
        statement="Dụ Đỉnh từng bị di dời khỏi kinh thành năm 1945.",
        claim_type="factual",
        confidence=HistoricalConfidence.disputed.value,
        verification_status="unreviewed",
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=src,
        data={"support_type": HistoricalSupportType.supports.value, "page_start": "50"},
        actor_id=admin_user.id,
    )
    db_session.commit()

    with pytest.raises(ValueError, match="Disputed claim cannot be approved as editor_reviewed"):
        gov.transition_claim_status(
            db_session, claim=claim, target="editor_reviewed", actor_id=admin_user.id
        )

    # API call to expert_verify fails with 422
    res = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "expert_verified"},
    )
    assert res.status_code == 422
    assert "Disputed claim" in res.text


# --------------------------------------------------------------------------- #
# 6. Contradiction Source Attachment Demotes Verified Claim
# --------------------------------------------------------------------------- #
def test_attaching_contradicting_source_demotes_verified_claim(client, db_session):
    """When a new source contradicting an already expert_verified claim is attached,

    the claim is immediately demoted to 'disputed' and confidence is set to 'disputed'.
    """
    admin_user = _make_staff(client, db_session, f"admin_t024_4_{uuid.uuid4().hex[:6]}@example.com")
    entity = _seed_entity(db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Tuyên Đỉnh")
    src1 = _seed_source(db_session, title="Khảo sát ban đầu", source_type="scholarly_book")
    src2_contradict = _seed_source(db_session, title="Văn bản đính chính", source_type="archival_record")

    claim = _seed_claim(
        db_session,
        entity=entity,
        statement="Tuyên Đỉnh có khối lượng đúng 3200 cân đồng.",
        claim_type="measurement",
        confidence="high",
        verification_status="unreviewed",
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=src1,
        data={"support_type": "supports", "page_start": "12"},
        actor_id=admin_user.id,
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="editor_reviewed", actor_id=admin_user.id
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="expert_verified", actor_id=admin_user.id
    )
    db_session.commit()
    assert claim.verification_status == "expert_verified"

    # Attach contradicting source
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=src2_contradict,
        data={"support_type": "contradicts", "page_start": "88"},
        actor_id=admin_user.id,
    )
    db_session.commit()

    db_session.refresh(claim)
    assert claim.verification_status == "disputed", "Verified claim should be demoted to disputed"
    assert claim.confidence == "disputed"

    # Check that audit log recorded the contradict_demote action
    audit = db_session.execute(
        select(HistoricalContentAuditLog).where(
            HistoricalContentAuditLog.resource_id == claim.id,
            HistoricalContentAuditLog.action == "contradict_demote",
        )
    ).scalar_one_or_none()
    assert audit is not None
    assert audit.after_json["verification_status"] == "disputed"


# --------------------------------------------------------------------------- #
# 7. Source Relation Links: Supports vs Contradicts vs Contextualizes
# --------------------------------------------------------------------------- #
def test_source_relation_links_supports_vs_contradicts(db_session):
    """Verify explicit support types and their exact epistemic permissions."""
    entity = _seed_entity(db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Huyền Đỉnh")
    source = _seed_source(db_session)

    # Validate that all expected support types exist in HistoricalSupportType
    expected_types = {
        "supports",
        "partially_supports",
        "contextualizes",
        "contradicts",
        "mentions",
        "primary_evidence_for",
        "secondary_interpretation_of",
    }
    actual_types = {t.value for t in HistoricalSupportType}
    assert expected_types.issubset(actual_types)

    # 'contextualizes' or 'mentions' does NOT satisfy the verification invariant for factual claims
    claim_ctx = _seed_claim(
        db_session, entity=entity, statement="Huyền Đỉnh được đặt ở góc tây nam Thế Miếu."
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim_ctx,
        source=source,
        data={"support_type": HistoricalSupportType.contextualizes.value},
    )
    db_session.flush()

    assert gov.claim_has_eligible_source(db_session, claim_ctx) is False
    with pytest.raises(ValueError, match="Editor review of a factual claim requires an eligible source"):
        gov.transition_claim_status(db_session, claim=claim_ctx, target="editor_reviewed", actor_id=None)

    # 'primary_evidence_for' DOES satisfy the invariant
    claim_evid = _seed_claim(
        db_session, entity=entity, statement="Huyền Đỉnh được đúc vào năm 1836."
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim_evid,
        source=source,
        data={"support_type": HistoricalSupportType.primary_evidence_for.value, "page_start": "20"},
    )
    db_session.flush()

    assert gov.claim_has_eligible_source(db_session, claim_evid) is True
    gov.transition_claim_status(db_session, claim=claim_evid, target="editor_reviewed", actor_id=None)
    gov.transition_claim_status(db_session, claim=claim_evid, target="expert_verified", actor_id=None)
    assert claim_evid.verification_status == "expert_verified"


# --------------------------------------------------------------------------- #
# 8. AI Tutor Cites Atomic Claim IDs and Verification Status
# --------------------------------------------------------------------------- #
def test_ai_tutor_cites_atomic_claim_ids_and_verification_status(client, db_session):
    """AI tutor synthesizes explanations citing specific atomic claim IDs and their

    epistemic verification status.
    """
    entity = _seed_entity(
        db_session, slug=f"urn-{uuid.uuid4().hex[:6]}", name_vi="Anh Đỉnh"
    )
    source = _seed_source(
        db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ", source_type="royal_record"
    )
    claim = _seed_claim(
        db_session,
        entity=entity,
        statement="Anh Đỉnh được đúc hoàn thành vào năm Đinh Dậu 1837.",
        claim_type="chronology",
        confidence="high",
        verification_status="unreviewed",
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=source,
        data={"support_type": "supports", "page_start": "104"},
    )
    gov.transition_claim_status(db_session, claim=claim, target="editor_reviewed", actor_id=None)
    gov.transition_claim_status(db_session, claim=claim, target="expert_verified", actor_id=None)
    db_session.commit()

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Anh Đỉnh được hoàn thành năm nào?"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # 1. Answer markdown contains atomic claim ID and epistemic status
    assert "1837" in data["answer_markdown"]
    assert str(claim.id) in data["answer_markdown"], "Atomic claim ID must be cited in answer explanation"
    assert "expert_verified" in data["answer_markdown"], "Verification status must be explicitly stated"

    # 2. Citations explicitly carry atomic claim IDs
    assert len(data["citations"]) >= 1
    citation = data["citations"][0]
    assert citation["source_id"] == str(source.id)
    assert str(claim.id) in citation["claim_ids"]
    assert "104" in citation["locator"]

    # 3. Grounding tracking
    assert data["grounding"]["claims_retrieved"] >= 1
    assert data["grounding"]["claims_used"] >= 1
    assert data["grounding"]["sources_used"] >= 1
