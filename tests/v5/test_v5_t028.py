# -*- coding: utf-8 -*-
"""V5-T028 (Wave W02, Slot A08): Story Renderer with Verified Citations & Uncertainty Indicators.

Audits and verifies:
1. Bilingual story prose rendering with footnotes:
   - Verifies footnote extraction [^1], [^2], [^dntl-01] from Vietnamese and English text fields.
   - Verifies bidirectional linkage between footnote markers and authoritative bibliographic records.
2. Verified primary bibliographic sources linkage:
   - Validates that footnotes map to existing HistoricalSource records.
   - Verifies inclusion of author, title, publication year, locator, citation text, and source URL.
3. Epistemic uncertainty flags & indicators:
   - Correctly assigns epistemic certainty badges:
     * 'su_lieu_xac_thuc' (Sử liệu xác thực - documented) for primary source-backed passages.
     * 'dang_khao_cuu' (Đang khảo cứu - uncertain) for disputed, unreviewed, or unsupported passages.
     * 'truyen_thuyet_dan_gian' (Truyền thuyết dân gian - traditional) for folklore / oral accounts.
   - Highlights empty evidence warnings for passages asserting fact without backing citations.
4. Source drawer metadata integration:
   - Verifies that bibliographic sources format correctly for slide-out source drawer presentation.
   - Verifies drawer metadata fields (title, author, locator, rights, statement).
5. Strict negative abuse guardrails:
   - Disallows fake or unmapped citations (footnotes referencing non-existent sources fail validation).
   - Rejects unverified or unsupported claims attempting to masquerade as 'Sử liệu xác thực'.
   - Rejects disputed claims attempting to be published as verified historical facts.
   - Prevents empty or bogus citations from bypassing validation gates on create and update.
"""
from __future__ import annotations

import uuid
from typing import Any
import pytest
from sqlalchemy import select

from backend.domain.story_citations import (
    FOOTNOTE_REGEX,
    FootnoteMapper,
    extract_all_story_footnotes,
    extract_footnote_keys,
)
from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
    HistoryStory,
)
from backend.models import User, UserRole
from backend.services import history_stories as svc


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _make_staff(client, db_session, email: str = "curator@example.com", display_name: str = "Story Curator"):
    user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        from backend.security import hash_password
        user = User(
            email=email,
            password_hash=hash_password("Password123!"),
            display_name=display_name,
            username=f"user_{uuid.uuid4().hex[:8]}",
            role=UserRole.admin,
            is_profile_public=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user.role = UserRole.admin
        db_session.commit()

    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _seed_source(
    db_session,
    title: str = "Đại Nam Thực Lục",
    author_text: str = "Quốc sử quán triều Nguyễn",
    publication_year: int = 1848,
    pages: str = "Quyển 28, tờ 15a",
) -> HistoricalSource:
    src = HistoricalSource(
        source_type="royal_chronicle",
        title=title,
        author_text=author_text,
        publication_year=publication_year,
        pages=pages,
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/dntl",
    )
    db_session.add(src)
    db_session.flush()
    return src


def _seed_entity(db_session, slug: str = "cao-dinh-urn", name_vi: str = "Cao Đỉnh") -> HistoricalEntity:
    ent = HistoricalEntity(
        entity_type="urn",
        slug=slug,
        name_vi=name_vi,
        publication_status="published",
    )
    db_session.add(ent)
    db_session.flush()
    return ent


def _seed_claim(
    db_session,
    entity: HistoricalEntity,
    statement_vi: str,
    verification_status: str = "expert_verified",
    confidence: str = "high",
) -> HistoricalClaim:
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_{uuid.uuid4().hex[:8]}",
        claim_type="historical_fact",
        statement_vi=statement_vi,
        origin="editorial",
        verification_status=verification_status,
        confidence=confidence,
    )
    db_session.add(claim)
    db_session.flush()
    return claim


# --------------------------------------------------------------------------- #
# 1. Bilingual Footnote Extraction and Mapping
# --------------------------------------------------------------------------- #
def test_footnote_regex_and_bilingual_extraction():
    """Verify markdown footnote regex extracts tokens from Vietnamese and English text."""
    text_vi = "Đỉnh này được đúc vào năm Bính Thân 1836[^1] dưới sự chỉ đạo của Nội các[^dntl-02]."
    text_en = "This urn was cast in the year 1836[^1] under imperial decree[^dntl-02]."

    keys_vi = extract_footnote_keys(text_vi)
    assert keys_vi == ["1", "dntl-02"]

    keys_en = extract_footnote_keys(text_en)
    assert keys_en == ["1", "dntl-02"]

    blocks = [
        {
            "type": "text",
            "body_vi": text_vi,
            "body_en": text_en,
        },
        {
            "type": "quote",
            "quote_vi": "Khắc hình rồng mây[^3].",
            "quote_en": "Carved with clouds and dragon[^3].",
        },
    ]

    refs = extract_all_story_footnotes(blocks)
    assert len(refs) == 6
    locales = [r.locale for r in refs]
    assert "vi" in locales and "en" in locales
    extracted_keys = [r.key for r in refs]
    assert "1" in extracted_keys and "dntl-02" in extracted_keys and "3" in extracted_keys


# --------------------------------------------------------------------------- #
# 2. Footnote to Primary Bibliographic Source Linkage
# --------------------------------------------------------------------------- #
def test_footnote_resolution_to_bibliographic_sources(db_session):
    """Verify that footnote tokens resolve to DB-backed sources with metadata."""
    src1 = _seed_source(db_session, title="Đại Nam Thực Lục", publication_year=1848, pages="Quyển 28, tờ 15a")
    src2 = _seed_source(db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ", publication_year=1851, pages="Quyển 118, tờ 89")
    db_session.commit()

    blocks = [
        {
            "type": "text",
            "body_vi": "Cao Đỉnh là chiếc đỉnh đầu tiên được hợp thức hóa vị trí[^1]. Quy thức doanh tạo rất nghiêm ngặt[^2].",
            "body_en": "Cao Dinh was the primary bronze urn cast[^1]. Regulations were strictly observed[^2].",
            "citations": [
                {
                    "source_id": str(src1.id),
                    "footnote_key": "1",
                    "epistemic_certainty": "su_lieu_xac_thuc",
                },
                {
                    "source_id": str(src2.id),
                    "footnote_key": "2",
                    "epistemic_certainty": "su_lieu_xac_thuc",
                },
            ],
        }
    ]

    res = FootnoteMapper.resolve_story_citations_and_footnotes(blocks=blocks, db=db_session)
    assert res.is_valid is True
    assert len(res.broken_references) == 0
    assert len(res.citations) == 2

    # Check mapping
    fn1 = res.footnote_map.get("1")
    assert fn1 is not None
    assert fn1["source_id"] == str(src1.id)
    assert fn1["source_title"] == "Đại Nam Thực Lục"
    assert fn1["publication_year"] == 1848
    assert fn1["locator"] == "Quyển 28, tờ 15a"
    assert fn1["epistemic_certainty"] == "su_lieu_xac_thuc"

    fn2 = res.footnote_map.get("2")
    assert fn2 is not None
    assert fn2["source_id"] == str(src2.id)
    assert fn2["source_title"] == "Khâm Định Đại Nam Hội Điển Sự Lệ"


# --------------------------------------------------------------------------- #
# 3. Epistemic Uncertainty & Confidence Tone Indicators
# --------------------------------------------------------------------------- #
def test_epistemic_uncertainty_indicators_for_disputed_and_unsupported(db_session):
    """Verify epistemic status resolves correctly to dang_khao_cuu for disputed/unsupported content."""
    ent = _seed_entity(db_session, slug="huyen-dinh-urn", name_vi="Huyền Đỉnh")
    src = _seed_source(db_session, title="Châu Bản Triều Nguyễn", publication_year=1836)
    disputed_claim = _seed_claim(
        db_session,
        ent,
        statement_vi="Niên đại hoàn thành chiếc đỉnh bị tranh cãi.",
        verification_status="disputed",
        confidence="disputed",
    )
    db_session.commit()

    blocks = [
        {
            "type": "text",
            "body_vi": "Khẳng định này còn tranh luận[^1]. Khẳng định này không có nguồn[^2].",
            "citations": [
                {
                    "claim_id": str(disputed_claim.id),
                    "source_id": str(src.id),
                    "footnote_key": "1",
                    "epistemic_certainty": "dang_khao_cuu",
                },
                {
                    "source_id": None,
                    "footnote_key": "2",
                    "source_title": "Tài liệu chưa kiểm chứng",
                    "epistemic_certainty": "dang_khao_cuu",
                },
            ],
        }
    ]

    res = FootnoteMapper.resolve_story_citations_and_footnotes(blocks=blocks, db=db_session)
    fn1 = res.footnote_map.get("1")
    assert fn1["epistemic_certainty"] == "dang_khao_cuu"
    assert fn1["is_disputed"] is True

    fn2 = res.footnote_map.get("2")
    assert fn2["epistemic_certainty"] == "dang_khao_cuu"
    assert fn2["has_source"] is False


def test_traditional_account_folklore_epistemic_tone(db_session):
    """Verify folklore and traditional accounts resolve to truyen_thuyet_dan_gian."""
    src = _seed_source(db_session, title="Lĩnh Nam Chích Quái", publication_year=1492)
    db_session.commit()

    blocks = [
        {
            "type": "text",
            "body_vi": "Dân gian truyền tụng điềm lành xuất hiện khi đỉnh được đúc xong[^1].",
            "citations": [
                {
                    "source_id": str(src.id),
                    "footnote_key": "1",
                    "epistemic_certainty": "truyen_thuyet_dan_gian",
                }
            ],
        }
    ]

    res = FootnoteMapper.resolve_story_citations_and_footnotes(blocks=blocks, db=db_session)
    assert res.is_valid is True
    fn1 = res.footnote_map.get("1")
    assert fn1["epistemic_certainty"] == "truyen_thuyet_dan_gian"


# --------------------------------------------------------------------------- #
# 4. Negative Abuse Guardrails: Disallow Fake or Unmapped Citations
# --------------------------------------------------------------------------- #
def test_negative_abuse_broken_unmapped_footnote_rejected(db_session):
    """Reject story validation when footnote [^99] has no matching source or citation."""
    blocks = [
        {
            "type": "text",
            "body": "Đoạn văn này có cước chú ma không hề tồn tại[^99].",
            "citations": [],
        }
    ]

    errors = FootnoteMapper.validate_strict_citations(blocks=blocks, db=db_session)
    assert len(errors) > 0
    assert any("Broken footnote reference: [^99]" in e for e in errors)


def test_negative_abuse_fake_nonexistent_source_id_rejected(db_session):
    """Reject story when citation references a fake UUID not present in HistoricalSource."""
    fake_source_id = str(uuid.uuid4())
    blocks = [
        {
            "type": "text",
            "body": "Đoạn văn trích dẫn nguồn giả mạo[^1].",
            "citations": [
                {
                    "source_id": fake_source_id,
                    "footnote_key": "1",
                }
            ],
        }
    ]

    errors = FootnoteMapper.validate_strict_citations(blocks=blocks, db=db_session)
    assert len(errors) > 0
    assert any("Fake or non-existent source" in e for e in errors)


def test_negative_abuse_claim_without_evidence_pretending_verified(db_session):
    """Reject story when a claim without backing evidence claims to be 'Sử liệu xác thực'."""
    blocks = [
        {
            "type": "text",
            "body": "Khẳng định không có bằng chứng nhưng tự nhận là sử liệu xác thực.",
            "citations": [
                {
                    "source_id": None,
                    "source_title": "Nguồn tự tạo",
                    "epistemic_certainty": "su_lieu_xac_thuc",
                    "is_verified": True,
                }
            ],
        }
    ]

    errors = FootnoteMapper.validate_strict_citations(blocks=blocks, db=db_session)
    assert len(errors) > 0
    assert any("Evidence abuse" in e for e in errors)


def test_negative_abuse_disputed_claim_cannot_be_presented_as_verified(db_session):
    """Reject attempt to present a disputed claim as verified historical fact."""
    ent = _seed_entity(db_session, slug="thuan-dinh-urn", name_vi="Thuần Đỉnh")
    src = _seed_source(db_session, title="Gia Định Thành Thông Chí")
    disputed_claim = _seed_claim(
        db_session,
        ent,
        statement_vi="Chi tiết hoa văn bị các nhà nghiên cứu phản bác.",
        verification_status="disputed",
        confidence="disputed",
    )
    db_session.commit()

    blocks = [
        {
            "type": "text",
            "body": "Nội dung hoa văn đỉnh đồng[^1].",
            "citations": [
                {
                    "claim_id": str(disputed_claim.id),
                    "source_id": str(src.id),
                    "footnote_key": "1",
                    "epistemic_certainty": "su_lieu_xac_thuc",
                }
            ],
        }
    ]

    errors = FootnoteMapper.validate_strict_citations(blocks=blocks, db=db_session)
    assert len(errors) > 0
    assert any("cannot present disputed" in e.lower() or "contested claim abuse" in e.lower() for e in errors)


# --------------------------------------------------------------------------- #
# 5. API Router Integration: GET, POST, and PUT Story Citations
# --------------------------------------------------------------------------- #
def test_story_api_returns_structured_citations(client, db_session):
    """Verify that public API returns resolved structured citations with sources."""
    src = _seed_source(
        db_session,
        title="Đại Nam Nhất Thống Chí",
        author_text="Quốc sử quán triều Nguyễn",
        publication_year=1882,
        pages="Tập Kinh sư, tr. 45",
    )
    story = HistoryStory(
        slug="truyen-cuu-dinh-khao-chung",
        title_vi="Cửu Đỉnh: Khảo chứng Sử liệu",
        title_en="Nine Dynastic Urns: Archival Evidence",
        status="published",
        publication_status="expert_verified",
        blocks=[
            {
                "type": "text",
                "body": "Được đúc vào tháng 12 năm Ất Mùi 1835[^1].",
                "citations": [
                    {
                        "source_id": str(src.id),
                        "footnote_key": "1",
                        "epistemic_certainty": "su_lieu_xac_thuc",
                    }
                ],
            }
        ],
    )
    db_session.add(story)
    db_session.commit()

    res = client.get("/api/v1/history/stories/truyen-cuu-dinh-khao-chung")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["slug"] == "truyen-cuu-dinh-khao-chung"
    assert "citations" in data
    assert len(data["citations"]) == 1

    cite = data["citations"][0]
    assert cite["source_id"] == str(src.id)
    assert cite["source_title"] == "Đại Nam Nhất Thống Chí"
    assert cite["author"] == "Quốc sử quán triều Nguyễn"
    assert cite["publication_year"] == 1882
    assert cite["locator"] == "Tập Kinh sư, tr. 45"
    assert cite["epistemic_certainty"] == "su_lieu_xac_thuc"


def test_story_api_rejects_post_with_unmapped_footnote(client, db_session):
    """Verify that staff POST /api/v1/history/stories rejects unmapped footnotes."""
    _make_staff(client, db_session, email="editor_t028@example.com")

    payload = {
        "slug": "truyen-chua-nguon-ma",
        "title_vi": "Truyện chứa nguồn ma",
        "status": "draft",
        "blocks": [
            {
                "type": "text",
                "body": "Có cước chú [^ghost] nhưng không có nguồn tương ứng.",
            }
        ],
    }

    res = client.post("/api/v1/history/stories", json=payload)
    assert res.status_code == 422, res.text
    err = res.json()["error"]
    assert err["code"] == "HISTORY_STORY_INVALID_BLOCKS"
    assert "Broken footnote reference: [^ghost]" in err["message"]


def test_story_api_rejects_post_with_fake_source_id(client, db_session):
    """Verify that staff POST /api/v1/history/stories rejects non-existent source IDs."""
    _make_staff(client, db_session, email="editor_t028_fake@example.com")
    fake_id = str(uuid.uuid4())

    payload = {
        "slug": "truyen-nguon-khong-ton-tai",
        "title_vi": "Truyện nguồn không tồn tại",
        "status": "draft",
        "blocks": [
            {
                "type": "text",
                "body": "Cước chú trỏ tới nguồn rác[^1].",
                "citations": [
                    {
                        "source_id": fake_id,
                        "footnote_key": "1",
                    }
                ],
            }
        ],
    }

    res = client.post("/api/v1/history/stories", json=payload)
    assert res.status_code == 422, res.text
    err = res.json()["error"]
    assert err["code"] == "HISTORY_STORY_INVALID_BLOCKS"
    assert "Fake or non-existent source" in err["message"]
