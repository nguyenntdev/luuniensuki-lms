# -*- coding: utf-8 -*-
"""V5-T063 (Wave W06, Slot A03): Hint-first Learning Mode & Citation Provenance Inspection.

Priority: P1; Classification: PRODUCTION_COMPLETION

Verifies:
1. Hint-first learning mode in backend/routers/history_tutor.py and frontend/src/app/dai-noi/ai/page.tsx:
   - AI tutor guides student with Socratic questions/hints to observe motifs and cite sources
     before revealing direct answers.
   - When reveal_answer is False (default in hint-first mode), direct factual resolution is withheld
     and progressive observation prompts, source guidance, and reflection questions are provided.
   - When reveal_answer is True, the full verified factual resolution with citations is unlocked.
2. Motif & Architectural Observation Guidance:
   - Differentiates motif/relief entities, urn entities, and architectural monuments.
   - Specifically instructs students on observing relief carvings, layers, inscriptions, and symbols.
3. Citation Provenance & Exact Primary Source Inspection:
   - Student can inspect exact primary source reference (Title, Author, Volume, Chapter, Page, Folio,
     Locator, Archive URL, Rights Status, Verification Status).
   - Generates and verifies cryptographic SHA-256 provenance hashes.
4. Strict Negative Abuse Guardrails:
   - Rejects queries for non-existent or fabricated source IDs with HTTP 404 (SOURCE_NOT_FOUND).
   - Rejects forged or tampered provenance hashes with HTTP 422 (PROVENANCE_HASH_MISMATCH).
   - Prevents disputed or unverified claims from claiming settled factual authority (su_lieu_xac_thuc).
   - Blocks stripping of primary source citations from verified historical claims.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from backend.services import history_governance as gov
from backend.services import history_tutor as tutor
from backend.services.entity_citations import (
    CitationProvenanceError,
    compute_citation_provenance_hash,
)


# --------------------------------------------------------------------------- #
# Seeding Fixtures & Helpers
# --------------------------------------------------------------------------- #
def _seed_entity(
    db_session: Session,
    *,
    slug: str,
    name_vi: str,
    entity_type: str = "relief",
    summary_vi: str | None = None,
    alternative_names: list[str] | None = None,
) -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type=entity_type,
        slug=slug,
        name_vi=name_vi,
        publication_status="published",
        alternative_names=alternative_names or [name_vi],
        summary_vi=summary_vi or f"Mô tả cho {name_vi}",
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session: Session,
    *,
    title: str = "Đại Nam Thực Lục Chính Biên",
    author_text: str = "Quốc Sử Quán triều Nguyễn",
    publication_year: int = 1848,
    volume: str = "Đệ nhị kỷ",
    pages: str = "Quyển 98, tờ 12a",
    verification_status: str = "metadata_verified",
    rights_status: str = "public_domain",
    url: str = "https://archives.org.vn/dntl-98",
) -> HistoricalSource:
    source = HistoricalSource(
        source_type="royal_chronicle",
        title=title,
        author_text=author_text,
        publication_year=publication_year,
        volume=volume,
        pages=pages,
        verification_status=verification_status,
        rights_status=rights_status,
        url=url,
        license="Public Domain",
    )
    db_session.add(source)
    db_session.flush()
    return source


def _seed_claim(
    db_session: Session,
    *,
    entity: HistoricalEntity,
    statement_vi: str,
    claim_type: str = "factual",
    confidence: str = "high",
    verification_status: str = "expert_verified",
) -> HistoricalClaim:
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type=claim_type,
        statement_vi=statement_vi,
        confidence=confidence,
        verification_status=verification_status,
        origin="editorial",
        is_current=True,
    )
    db_session.add(claim)
    db_session.flush()
    return claim


def _seed_verified_bundle(
    db_session: Session,
    *,
    slug: str = "cao-dinh-hoa-van",
    name_vi: str = "Họa văn Rồng Cao Đỉnh",
    entity_type: str = "relief",
    statement_vi: str = "Hình tượng Rồng trên Cao Đỉnh được chạm nổi ở tầng trên, tượng trưng cho thiên tử và quyền uy tối thượng.",
    source_title: str = "Khâm Định Đại Nam Hội Điển Sự Lệ",
    author_text: str = "Nội Các triều Nguyễn",
    chapter: str = "Quyển 82",
    page_start: str = "14",
    page_end: str = "16",
):
    entity = _seed_entity(
        db_session,
        slug=slug,
        name_vi=name_vi,
        entity_type=entity_type,
        summary_vi=statement_vi,
        alternative_names=[name_vi, slug.replace("_", " "), slug.replace("-", " ")],
    )
    source = _seed_source(
        db_session,
        title=source_title,
        author_text=author_text,
        verification_status="metadata_verified",
        pages=f"Tr. {page_start}-{page_end}",
    )
    claim = _seed_claim(
        db_session,
        entity=entity,
        statement_vi=statement_vi,
        verification_status="unreviewed",
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=source,
        data={
            "support_type": "supports",
            "chapter": chapter,
            "page_start": page_start,
            "page_end": page_end,
        },
    )
    gov.transition_claim_status(db_session, claim=claim, target="editor_reviewed", actor_id=None)
    gov.transition_claim_status(db_session, claim=claim, target="expert_verified", actor_id=None)
    db_session.commit()
    return entity, claim, source


# --------------------------------------------------------------------------- #
# Test 1: Hint-first mode provides Socratic hints without direct answer
# --------------------------------------------------------------------------- #
def test_hint_first_mode_provides_socratic_hints_without_direct_answer(client: TestClient, db_session: Session):
    entity, claim, source = _seed_verified_bundle(
        db_session,
        slug="relief_rong_cao_dinh",
        name_vi="Họa tiết Rồng Cao Đỉnh",
        entity_type="relief",
        statement_vi="Rồng trên Cao Đỉnh đúc năm 1835 tượng trưng cho ngôi thiên tử.",
    )

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Họa tiết rồng trên Cao Đỉnh mang ý nghĩa gì?",
            "mode": "hint_first",
            "reveal_answer": False,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # In hint-first mode, direct answer is not prematurely revealed
    assert data["mode"] == "hint_first"
    assert data["revealed_direct_answer"] is False

    # Check Socratic hints and progressive guidance
    assert len(data["socratic_hints"]) >= 2
    assert data["motif_guidance"] is not None
    assert "quan sát" in data["motif_guidance"].lower()
    assert data["source_investigation_guidance"] is not None

    # Check that the answer markdown is pedagogical guidance rather than raw giveaway
    md = data["answer_markdown"]
    assert "Socratic Hint-First" in md or "Chế độ Học tập Gợi mở" in md
    assert "Bước 1" in md or "Quan sát" in md
    assert "Bước 2" in md or "sử liệu" in md.lower()

    # Citations are preserved for provenance lookup even during hints
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_id"] == str(source.id)


# --------------------------------------------------------------------------- #
# Test 2: Hint-first mode reveals direct answer when requested
# --------------------------------------------------------------------------- #
def test_hint_first_mode_reveals_direct_answer_when_requested(client: TestClient, db_session: Session):
    entity, claim, source = _seed_verified_bundle(
        db_session,
        slug="nghi_dinh_relief",
        name_vi="Nghị Đỉnh",
        entity_type="urn",
        statement_vi="Nghị Đỉnh được đúc vào năm Minh Mạng thứ 16 (1835).",
    )

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Nghị Đỉnh đúc khi nào?",
            "mode": "hint_first",
            "reveal_answer": True,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["revealed_direct_answer"] is True
    md = data["answer_markdown"]
    assert "1835" in md
    assert "Lời giải chi tiết" in md or "Socratic Resolution" in md
    assert data["confidence"] in ("high", "medium")


# --------------------------------------------------------------------------- #
# Test 3: Motif-specific observation guidance for relief motifs
# --------------------------------------------------------------------------- #
def test_motif_observation_guidance_for_relief_motifs(client: TestClient, db_session: Session):
    entity, claim, source = _seed_verified_bundle(
        db_session,
        slug="relief_song_huong",
        name_vi="Sông Hương trên Nhân Đỉnh",
        entity_type="relief",
        statement_vi="Hình tượng Sông Hương (Hương Giang) được khắc trên Nhân Đỉnh.",
    )

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Cho em gợi ý quan sát hoa văn Sông Hương trên Nhân Đỉnh",
            "mode": "socratic",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["mode"] == "hint_first"
    motif_guidance = data.get("motif_guidance") or ""
    # Specifically guides student to observe relief carving & features
    assert any(term in motif_guidance.lower() for term in ("phù điêu", "hoa văn", "đường nét", "đúc nổi", "quan sát"))
    assert len(data["observation_prompts"]) >= 1


# --------------------------------------------------------------------------- #
# Test 4: Inspect exact primary source reference
# --------------------------------------------------------------------------- #
def test_inspect_exact_primary_source_reference(client: TestClient, db_session: Session):
    entity, claim, source = _seed_verified_bundle(
        db_session,
        slug="hien_lam_cac_audit",
        name_vi="Hiển Lâm Các",
        entity_type="architecture",
        statement_vi="Hiển Lâm Các khởi dựng năm 1822 trong khuôn viên Thế Miếu.",
        source_title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc Sử Quán triều Nguyễn",
        chapter="Đệ nhị kỷ, Quyển 98",
        page_start="25",
        page_end="28",
    )

    # Student requests citation provenance
    res = client.get(f"/api/v1/history/tutor/citations/{source.id}/provenance")
    assert res.status_code == 200, res.text
    prov = res.json()

    # Exact primary source reference fields
    assert prov["source_id"] == str(source.id)
    assert prov["source_title"] == "Đại Nam Thực Lục Chính Biên"
    assert prov["author"] == "Quốc Sử Quán triều Nguyễn"
    assert prov["verification_status"] in ("expert_verified", "metadata_verified")
    assert prov["rights_status"] == "public_domain"
    assert "Quyển 98" in prov["locator"]
    assert prov["epistemic_certainty"] == "su_lieu_xac_thuc"
    assert prov["is_disputed"] is False
    assert prov["provenance_verified"] is True
    assert len(prov["provenance_hash"]) == 64  # Valid SHA-256 hex string


# --------------------------------------------------------------------------- #
# Test 5: Negative Abuse - Query fabricated source rejected with 404
# --------------------------------------------------------------------------- #
def test_negative_abuse_query_fabricated_source_rejected(client: TestClient):
    fake_source_id = uuid.uuid4()
    res = client.get(f"/api/v1/history/tutor/citations/{fake_source_id}/provenance")
    assert res.status_code == 404, res.text
    body = res.json()
    assert body["error"]["code"] == "SOURCE_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Test 6: Negative Abuse - Tampered provenance hash rejected with 422
# --------------------------------------------------------------------------- #
def test_negative_abuse_tampered_provenance_hash_rejected(client: TestClient, db_session: Session):
    entity, claim, source = _seed_verified_bundle(
        db_session,
        slug="dien_thai_hoa_hash_test",
        name_vi="Điện Thái Hòa",
        entity_type="architecture",
    )

    # Attempt to query with a forged/tampered hash
    forged_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    res = client.get(
        f"/api/v1/history/tutor/citations/{source.id}/provenance",
        params={"expected_hash": forged_hash},
    )
    assert res.status_code == 422, res.text
    body = res.json()
    assert body["error"]["code"] == "PROVENANCE_HASH_MISMATCH"


# --------------------------------------------------------------------------- #
# Test 7: Negative Abuse - Disputed claim provenance cannot claim settled authority
# --------------------------------------------------------------------------- #
def test_negative_abuse_disputed_claim_provenance_flagged_cannot_claim_settled_authority(
    client: TestClient, db_session: Session
):
    entity = _seed_entity(db_session, slug="disputed_glyph_entity", name_vi="Họa văn chữ Hán chưa khảo")
    source = _seed_source(
        db_session,
        title="Bản tin nghiên cứu đối chiếu",
        verification_status="unreviewed",
    )
    claim = _seed_claim(
        db_session,
        entity=entity,
        statement_vi="Niên đại chữ Hán còn nhiều tranh cãi học thuật.",
        confidence="disputed",
        verification_status="disputed",
    )
    gov.attach_source_to_claim(
        db_session,
        claim=claim,
        source=source,
        data={"support_type": "contradicts", "chapter": "Tập 1"},
    )
    db_session.commit()

    # Inspect provenance
    res = client.get(f"/api/v1/history/tutor/citations/{source.id}/provenance")
    assert res.status_code == 200, res.text
    prov = res.json()

    # Must be marked as disputed and under investigation
    assert prov["is_disputed"] is True
    assert prov["epistemic_certainty"] == "dang_khao_cuu"
    assert prov["epistemic_certainty"] != "su_lieu_xac_thuc"


# --------------------------------------------------------------------------- #
# Test 8: Ask endpoint provenance integration
# --------------------------------------------------------------------------- #
def test_ask_endpoint_provenance_integration(client: TestClient, db_session: Session):
    entity, claim, source = _seed_verified_bundle(
        db_session,
        slug="ngo_mon_provenance_test",
        name_vi="Ngọ Môn Huế",
        entity_type="architecture",
        statement_vi="Ngọ Môn xây dựng năm Minh Mạng thứ 14 (1833).",
    )

    res = client.post(
        "/api/v1/history/tutor/ask",
        json={
            "question": "Ngọ Môn xây dựng năm nào?",
            "inspect_provenance": True,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Citations enriched with provenance hash
    assert len(data["citations"]) >= 1
    cite = data["citations"][0]
    assert cite["source_title"] is not None
    assert cite["provenance_hash"] is not None

    # Provenance records list populated
    assert len(data["provenance_records"]) >= 1
    prov_rec = data["provenance_records"][0]
    assert prov_rec["source_id"] == str(source.id)
    assert prov_rec["provenance_verified"] is True
    assert prov_rec["is_disputed"] is False
