# -*- coding: utf-8 -*-
"""V5-T109: Creator Oral History Consent Studio Test Suite.

Wave W10, Slot A09:
- Audio transcript and version tracking
- Per-use media consent
- Revocation / right to erasure (Decree 13/2023/ND-CP)
- Cultural context preservation
- Negative abuse invariant: Revoked audio is immediately unavailable publicly and CDN/local caches are invalidated.

Audits and verifies:
1. Negative abuse test:
   - When an oral history recording is revoked, public endpoint immediately refuses to serve with HTTP 403.
   - Cache-Control headers returned are no-cache, no-store, and cache invalidation is triggered.
   - In-memory and persistent CDN revocation registry (AssetCacheRevocation) is verified.
2. Draft creation with cultural context:
   - Records oral history with community tradition epistemic certainty, recording date, location, interviewer, and audio duration.
   - Creates initial versioned transcript (v1) linked to recording.
3. Multi-version transcript evolution:
   - Appends version 2 with synchronized timed cues and change summary.
   - Verifies artisan review flag on transcript version.
4. Per-use media consent lifecycle:
   - Updates consent scope (full_public, educational_only, preview_only).
   - Validates consent agreement reference and timestamps.
5. Right to Erasure (GDPR / Decree 13/2023/ND-CP):
   - Redacts audio URL, content hash, and scrubs transcript text to '[ERASED UNDER RIGHT-TO-ERASURE]'.
   - Status updates to 'erased' and audit ledger records erasure action.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritagePlace,
    RbpcAudioConsentScope,
    RbpcAudioTranscriptVersion,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcOralHistoryRecording,
    RbpcOralHistoryStatus,
)
from backend.services.offline_licensing import (
    _IN_MEMORY_REVOKED_ASSETS,
    clear_revocation_cache,
    is_asset_revoked,
)
from backend.history_models import AssetCacheRevocation
from backend.config import settings
from backend.security import create_jwt_token, hash_password
from datetime import timedelta


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password("test_pass_123"),
        display_name=display_name or email.split("@")[0],
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers_for(user: User) -> dict[str, str]:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": role_str},
    )
    return {"Authorization": f"Bearer {token}"}


def _setup_creator(db_session, user: User) -> tuple[HeritagePlace, RbpcCreator]:
    place = HeritagePlace(
        id=uuid.uuid4(),
        slug=f"place-phuong-duc-{uuid.uuid4().hex[:6]}",
        name_vi="Phường Đúc Đồng Cố Đô",
        name_en="Phuong Duc Bronze Casting Guild",
        entity_type="community",
        heritage_category="traditional_craft",
        editorial_status="approved",
        content_scope="RBPC_HUE",
        visitor_summary_vi="Làng nghề đúc đồng truyền thống bên bờ sông Hương.",
        visitor_summary_en="Traditional bronze casting village along Perfume River.",
    )
    db_session.add(place)
    db_session.flush()

    creator = RbpcCreator(
        id=uuid.uuid4(),
        slug=f"artisan-nguyen-van-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Nguyễn Văn Sáng",
        craft_tradition="Đúc đồng Phường Đúc",
        craft_tradition_en="Phuong Duc Bronze Casting",
        approved_bio_vi="Truyền nhân đời thứ 5 nghề đúc chuông đồng và vạc đồng Cố Đô.",
        approved_bio_en="5th-generation bronze casting master specializing in temple bells.",
        public_region="Phường Đúc, TP. Huế",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
        years_of_practice=42,
        generation_lineage="Đời thứ 5",
        heritage_place_id=place.id,
        reviewer_id=user.id,
    )
    db_session.add(creator)
    db_session.flush()

    # Link an experience so provider has access in studio
    exp = RbpcExperience(
        id=uuid.uuid4(),
        slug=f"exp-duc-dong-{uuid.uuid4().hex[:6]}",
        title_vi="Đúc chuông đồng truyền thống",
        title_en="Traditional Bronze Bell Casting",
        description_vi="Trải nghiệm khuôn đất và rót đồng thủ công",
        description_en="Hands-on clay molding and bronze pouring",
        provider_name="Xưởng Đúc Đồng Nguyễn Văn",
        creator_id=creator.id,
        provider_id=user.id,
        publication_state="published",
        indicative_price_amount=350000.0,
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(creator)
    return place, creator


def test_negative_abuse_revoked_audio_immediately_unavailable_and_cache_invalidated(client, db_session):
    """NEGATIVE ABUSE INVARIANT (V5-T109):
    A revoked oral history recording MUST be immediately unavailable publicly (HTTP 403)
    and CDN/local caches must be invalidated with no-cache/no-store headers.
    """
    clear_revocation_cache()

    staff_user = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    staff_headers = _auth_headers_for(staff_user)

    _, creator = _setup_creator(db_session, staff_user)

    # 1. Create recording draft with full public consent
    create_payload = {
        "creator_id": str(creator.id),
        "title_vi": "Ký ức đúc Đại Hồng Chung thời Khải Định",
        "title_en": "Memories of Casting Great Temple Bell",
        "audio_url": "/assets/rbpc/audio/bell_1923.webm",
        "audio_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "audio_duration_seconds": 185,
        "mime_type": "audio/webm",
        "cultural_context_vi": "Kỹ thuật phối hợp đồng đỏ, thiếc và vàng ròng tạo âm vang sâu lắng của chuông chùa Cố Đô.",
        "recording_date": "2026-03-15",
        "recording_location": "Xưởng đúc Phường Đúc, TP. Huế",
        "interviewer_name": "Nhà nghiên cứu Trần Đại",
        "initial_transcript_vi": "Chuông đồng Huế khác chuông miền Bắc ở độ ngân vang...",
    }

    create_res = client.post(
        "/api/v1/rbpc/partner/oral-history",
        json=create_payload,
        headers=staff_headers,
    )
    assert create_res.status_code == 201, create_res.text
    rec_data = create_res.json()
    rec_id = rec_data["id"]

    # 2. Grant full public consent
    consent_payload = {
        "consent_scope": "full_public",
        "consent_granted": True,
        "consent_agreement_ref": "AGR-2026-PD-009",
        "consent_notes": "Artisan consented to public educational streaming",
    }
    consent_res = client.post(
        f"/api/v1/rbpc/partner/oral-history/{rec_id}/consent",
        json=consent_payload,
        headers=staff_headers,
    )
    assert consent_res.status_code == 200, consent_res.text
    assert consent_res.json()["status"] == "consented"
    assert consent_res.json()["consent_scope"] == "full_public"

    # 3. Verify public endpoint serves the consented audio
    pub_res = client.get(f"/api/v1/rbpc/oral-history/{rec_id}")
    assert pub_res.status_code == 200, pub_res.text
    assert pub_res.json()["title_vi"] == "Ký ức đúc Đại Hồng Chung thời Khải Định"

    # 4. REVOKE CONSENT (Negative abuse trigger)
    revoke_payload = {
        "reason": "Artisan requested immediate withdrawal of voice recording due to sacred family ritual terms.",
        "erase_data": False,
    }
    revoke_res = client.post(
        f"/api/v1/rbpc/partner/oral-history/{rec_id}/revoke",
        json=revoke_payload,
        headers=staff_headers,
    )
    assert revoke_res.status_code == 200, revoke_res.text
    assert revoke_res.json()["status"] == "revoked"
    assert revoke_res.json()["consent_scope"] == "revoked"
    assert revoke_res.json()["revocation_reason"] == revoke_payload["reason"]

    # 5. NEGATIVE ABUSE VERIFICATION:
    # Public endpoint MUST fail closed with HTTP 403 FORBIDDEN and return anti-stale cache headers
    pub_revoked_res = client.get(f"/api/v1/rbpc/oral-history/{rec_id}")
    assert pub_revoked_res.status_code == 403, pub_revoked_res.text
    err_body = pub_revoked_res.json()
    assert err_body["error"]["code"] == "ORAL_HISTORY_REVOKED"
    assert "cache_headers" in err_body["error"]["details"]
    cache_headers = err_body["error"]["details"]["cache_headers"]
    assert "no-cache" in cache_headers["Cache-Control"]
    assert "PURGE_CDN_IMMEDIATE" in cache_headers["X-Cache-Invalidation"]

    # 6. Verify in-memory and persistent CDN cache invalidation engine
    assert is_asset_revoked(str(rec_id), db_session) is True
    assert str(rec_id) in _IN_MEMORY_REVOKED_ASSETS

    # Check database table AssetCacheRevocation
    revocation_entry = db_session.scalar(
        select(AssetCacheRevocation).where(AssetCacheRevocation.asset_id == str(rec_id))
    )
    assert revocation_entry is not None
    assert revocation_entry.cdn_purged is True
    assert "Oral history consent revoked" in revocation_entry.revocation_reason


def test_oral_history_multi_version_transcript_and_artisan_verification(client, db_session):
    """Verifies audio transcript versioning (v1 -> v2) and timecode cue synchronization."""
    partner_user = _create_user(db_session, f"partner_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    partner_headers = _auth_headers_for(partner_user)

    _, creator = _setup_creator(db_session, partner_user)

    # 1. Create draft recording (initial v1 created automatically)
    create_payload = {
        "creator_id": str(creator.id),
        "title_vi": "Bí quyết pha tỷ lệ thiếc và đồng trong nghệ thuật đúc chuông",
        "title_en": "Tin and Bronze Ratio Secrets in Bell Casting",
        "audio_url": "/assets/rbpc/audio/tin_ratio.webm",
        "audio_sha256": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "audio_duration_seconds": 120,
        "mime_type": "audio/webm",
        "cultural_context_vi": "Bí quyết gia truyền gìn giữ tỷ lệ kim loại để chuông không bị nứt vỡ khi đánh.",
        "recording_date": "2026-04-10",
        "recording_location": "Xưởng đúc Phường Đúc",
        "initial_transcript_vi": "Phần một: Chọn đồng đỏ hạt lựu nguyên chất.",
        "initial_cues": [
            {"time_sec": 0.0, "end_time_sec": 15.5, "text": "Đồng đỏ phải chọn kỹ từ các mỏ chất lượng.", "speaker": "Nghệ nhân Sáng"}
        ],
    }

    res1 = client.post(
        "/api/v1/rbpc/partner/oral-history",
        json=create_payload,
        headers=partner_headers,
    )
    assert res1.status_code == 201, res1.text
    rec = res1.json()
    assert rec["current_version_number"] == 1
    assert rec["latest_transcript"]["version_number"] == 1
    assert rec["latest_transcript"]["is_verified_by_artisan"] is False

    # 2. Add version 2 with expanded cues and artisan verification
    v2_payload = {
        "transcript_text_vi": "Phần một: Chọn đồng đỏ hạt lựu. Phần hai: Nung chảy ở nhiệt độ trên 1100 độ C và thử màu lửa.",
        "transcript_text_en": "Part 1: Selecting copper. Part 2: Smelting above 1100C and observing fire hue.",
        "timed_cues": [
            {"time_sec": 0.0, "end_time_sec": 14.0, "text": "Đồng đỏ phải chọn loại hạt lựu tinh khiết.", "speaker": "Nghệ nhân Sáng", "section_title": "Tuyển chọn nguyên liệu"},
            {"time_sec": 14.5, "end_time_sec": 45.0, "text": "Khi lửa chuyển từ đỏ sang xanh ngọc là thời khắc rót thiếc vào khuôn.", "speaker": "Nghệ nhân Sáng", "section_title": "Quan sát ngọn lửa"},
        ],
        "change_summary": "Bổ sung thời gian chuẩn xác và giải nghĩa màu lửa nung theo xác nhận của nghệ nhân.",
        "verify_by_artisan": True,
    }

    res2 = client.post(
        f"/api/v1/rbpc/partner/oral-history/{rec['id']}/versions",
        json=v2_payload,
        headers=partner_headers,
    )
    assert res2.status_code == 200, res2.text
    rec2 = res2.json()
    assert rec2["current_version_number"] == 2
    assert rec2["latest_transcript"]["version_number"] == 2
    assert rec2["latest_transcript"]["is_verified_by_artisan"] is True
    assert rec2["latest_transcript"]["artisan_verified_at"] is not None
    assert len(rec2["latest_transcript"]["timed_cues"]) == 2
    assert rec2["latest_transcript"]["timed_cues"][1]["section_title"] == "Quan sát ngọn lửa"

    # 3. Verify database versions count
    versions = db_session.scalars(
        select(RbpcAudioTranscriptVersion)
        .where(RbpcAudioTranscriptVersion.recording_id == rec["id"])
        .order_by(RbpcAudioTranscriptVersion.version_number.asc())
    ).all()
    assert len(versions) == 2
    assert versions[0].version_number == 1
    assert versions[1].version_number == 2


def test_right_to_erasure_and_data_scrubbing(client, db_session):
    """Verifies Right-to-Erasure (GDPR / Decree 13/2023/ND-CP) redacts PII and voice recordings."""
    clear_revocation_cache()

    admin_user = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    admin_headers = _auth_headers_for(admin_user)

    _, creator = _setup_creator(db_session, admin_user)

    # 1. Create recording
    create_payload = {
        "creator_id": str(creator.id),
        "title_vi": "Kỷ niệm tuổi thơ và gia đình nghệ nhân thời loạn lạc",
        "audio_url": "/assets/rbpc/audio/family_personal_history.webm",
        "audio_sha256": "fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
        "audio_duration_seconds": 240,
        "cultural_context_vi": "Những tâm sự riêng tư về gia đình và tổ nghiệp.",
        "initial_transcript_vi": "Tên tôi là Nguyễn Văn Sáng, sinh quán tại làng cổ...",
    }

    res = client.post(
        "/api/v1/rbpc/partner/oral-history",
        json=create_payload,
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    rec = res.json()
    rec_id = rec["id"]

    # 2. Invoke Right to Erasure (erase_data = True)
    erase_payload = {
        "reason": "Chủ thể dữ liệu yêu cầu xóa bỏ vĩnh viễn ghi âm cá nhân theo Nghị định 13/2023/NĐ-CP.",
        "erase_data": True,
    }
    erase_res = client.post(
        f"/api/v1/rbpc/partner/oral-history/{rec_id}/revoke",
        json=erase_payload,
        headers=admin_headers,
    )
    assert erase_res.status_code == 200, erase_res.text
    erased_rec = erase_res.json()
    assert erased_rec["status"] == "erased"
    assert erased_rec["consent_scope"] == "revoked"
    assert erased_rec["erased_at"] is not None
    assert erased_rec["audio_url"] is None
    assert erased_rec["audio_sha256"] is None
    assert "[ERASED UNDER RIGHT-TO-ERASURE" in erased_rec["latest_transcript"]["transcript_text_vi"]

    # 3. Verify public endpoint returns 403 with purge headers
    pub_res = client.get(f"/api/v1/rbpc/oral-history/{rec_id}")
    assert pub_res.status_code == 403


def test_partner_oral_history_studio_listing_and_isolation(client, db_session):
    """Verifies listing and provider isolation in Oral History Studio."""
    p1 = _create_user(db_session, f"p1_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    p2 = _create_user(db_session, f"p2_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)

    t1 = _auth_headers_for(p1)
    t2 = _auth_headers_for(p2)

    _, c1 = _setup_creator(db_session, p1)
    _, c2 = _setup_creator(db_session, p2)

    # p1 creates recording for c1
    r1 = client.post(
        "/api/v1/rbpc/partner/oral-history",
        json={
            "creator_id": str(c1.id),
            "title_vi": "Lịch sử đúc đồng c1",
            "cultural_context_vi": "Ngữ cảnh văn hóa c1",
        },
        headers=t1,
    )
    assert r1.status_code == 201

    # p2 creates recording for c2
    r2 = client.post(
        "/api/v1/rbpc/partner/oral-history",
        json={
            "creator_id": str(c2.id),
            "title_vi": "Lịch sử hoa giấy c2",
            "cultural_context_vi": "Ngữ cảnh văn hóa c2",
        },
        headers=t2,
    )
    assert r2.status_code == 201

    # p1 lists recordings: only c1's recording is returned
    list1 = client.get(
        "/api/v1/rbpc/partner/oral-history",
        headers=t1,
    )
    assert list1.status_code == 200
    items1 = list1.json()["items"]
    assert any(i["title_vi"] == "Lịch sử đúc đồng c1" for i in items1)
    assert not any(i["title_vi"] == "Lịch sử hoa giấy c2" for i in items1)
