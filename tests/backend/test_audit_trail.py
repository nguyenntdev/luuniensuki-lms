# -*- coding: utf-8 -*-
"""Comprehensive tests for RBPC Audit Trails, Cryptographic Hash Chains, and Retention Policies.

Tests verify:
1. Append-only audit entries created on inquiry state transitions.
2. Append-only audit entries created on creator consent modification and experience updates.
3. Cryptographic SHA-256 hash chaining:
   - Genesis record has previous_hash is None.
   - Subsequent records have previous_hash == prior record's new_hash.
   - Recomputing hashes matches stored new_hash byte-for-byte.
   - Tamper detection catches modified diff payload, broken chain, or forged hashes.
4. Retention policy execution:
   - Expired inquiries have PII purged (redacted to marker).
   - Audit trail for purge is created with zero PII.
   - Anonymous identifiers (public_ref, party_size) preserved.
   - Retention extension works correctly with audit logging.
5. Re-import preservation invariant:
   - Re-running heritage/commercial import preserves inquiry states, audit logs, and creator consent.
"""
from __future__ import annotations

import copy
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.services.heritage_import import (
    DEFAULT_CREATORS_PATH,
    DEFAULT_EXPERIENCES_PATH,
    DEFAULT_INVENTORY_PATH,
    DEFAULT_SKETCHFAB_PATH,
    DEFAULT_STORIES_PATH,
    import_heritage_data,
)
from backend.services.rbpc_audit import (
    ACTION_CONSENT_MODIFIED,
    ACTION_EXPERIENCE_UPDATED,
    ACTION_INQUIRY_CREATED,
    ACTION_RETENTION_EXTENDED,
    ACTION_RETENTION_PURGE,
    ACTION_STATE_TRANSITION,
    ENTITY_CREATOR,
    ENTITY_EXPERIENCE,
    ENTITY_INQUIRY,
    apply_inquiry_retention_policy,
    compute_audit_hash,
    extend_inquiry_retention,
    get_audit_trail,
    get_inquiries_due_for_retention,
    get_latest_audit_entry,
    record_audit_entry,
    record_creator_consent_change,
    record_experience_update,
    record_inquiry_state_transition,
    verify_all_audit_chains,
    verify_audit_chain,
)


# --------------------------------------------------------------------------- #
# Fixtures & Helpers
# --------------------------------------------------------------------------- #
def _create_test_artisan_and_experience(db_session) -> tuple[RbpcCreator, RbpcExperience]:
    """Create and persist a consented artisan and workshop experience."""
    creator = RbpcCreator(
        slug=f"artisan-audit-{uuid.uuid4().hex[:8]}",
        public_name="Nghệ nhân Thử Nghiệm",
        craft_tradition="Pháp lam Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử audit trail.",
        consent_status=RbpcConsentStatus.consented.value,
        display_consent_ref="REF-CONSENT-2026-001",
    )
    db_session.add(creator)
    db_session.flush()

    experience = RbpcExperience(
        slug=f"exp-audit-{uuid.uuid4().hex[:8]}",
        creator_id=creator.id,
        provider_name="Xưởng Pháp Lam Thử Nghiệm",
        title_vi="Trải nghiệm chế tác Pháp lam",
        description_vi="Thực hành tráng men và nung đồng truyền thống.",
        area_public="Huế",
        availability_mode="inquiry_only",
        publication_state="published",
    )
    db_session.add(experience)
    db_session.flush()
    return creator, experience


def _create_test_inquiry(db_session, experience_id: uuid.UUID, **kwargs) -> RbpcInquiry:
    """Create and persist a visitor inquiry."""
    defaults = {
        "public_ref": f"INQ-AUD-{uuid.uuid4().hex[:6].upper()}",
        "experience_id": experience_id,
        "name": "Nguyễn Văn Khách",
        "contact_channel": "email",
        "contact_value": "khach@example.com",
        "desired_date": date(2026, 11, 20),
        "party_size": 2,
        "message": "Xin chào, tôi muốn hỏi lịch trống tháng 11.",
        "consent_version": "rbpc-inquiry-v1",
        "privacy_accepted": True,
        "state": RbpcInquiryStatus.new.value,
        "idempotency_key": str(uuid.uuid4()),
        "opaque_token": f"tok_{uuid.uuid4().hex}",
        "retention_due_at": datetime.now(timezone.utc) + timedelta(days=90),
    }
    defaults.update(kwargs)
    inquiry = RbpcInquiry(**defaults)
    db_session.add(inquiry)
    db_session.flush()
    return inquiry


# --------------------------------------------------------------------------- #
# 1. Inquiry State Transitions & Cryptographic Hash Chaining
# --------------------------------------------------------------------------- #
def test_inquiry_state_transitions_audit_trail(db_session):
    """Test sequential state transitions on an inquiry create a valid SHA-256 hash chain."""
    creator, experience = _create_test_artisan_and_experience(db_session)
    inquiry = _create_test_inquiry(db_session, experience.id)

    # 1. Initial entry: inquiry creation
    audit_0 = record_audit_entry(
        db_session,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry.id,
        action=ACTION_INQUIRY_CREATED,
        actor_id=None,
        diff_payload={"state": inquiry.state, "public_ref": inquiry.public_ref},
    )
    assert audit_0.previous_hash is None
    assert audit_0.new_hash is not None
    assert len(audit_0.new_hash) == 64  # SHA-256 hex string

    # 2. State transition: new -> contacted
    audit_1 = record_inquiry_state_transition(
        db_session,
        inquiry=inquiry,
        old_state="new",
        new_state=RbpcInquiryStatus.contacted,
        note="Đã gửi email phản hồi kiểm tra ngày hẹn",
    )
    assert audit_1.previous_hash == audit_0.new_hash
    assert audit_1.new_hash != audit_0.new_hash

    # 3. State transition: contacted -> confirmed
    audit_2 = record_inquiry_state_transition(
        db_session,
        inquiry=inquiry,
        old_state="contacted",
        new_state=RbpcInquiryStatus.confirmed,
        note="Nghệ nhân xác nhận còn chỗ",
    )
    assert audit_2.previous_hash == audit_1.new_hash

    # 4. State transition: confirmed -> closed
    audit_3 = record_inquiry_state_transition(
        db_session,
        inquiry=inquiry,
        old_state="confirmed",
        new_state=RbpcInquiryStatus.closed,
        note="Buổi trải nghiệm đã hoàn tất tốt đẹp",
    )
    assert audit_3.previous_hash == audit_2.new_hash

    # 5. Verify entire audit trail retrieval
    entries, count = get_audit_trail(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert count == 4
    assert len(entries) == 4
    assert [e.action for e in entries] == [
        ACTION_INQUIRY_CREATED,
        ACTION_STATE_TRANSITION,
        ACTION_STATE_TRANSITION,
        ACTION_STATE_TRANSITION,
    ]

    # 6. Verify cryptographic chain validity
    is_valid, errors = verify_audit_chain(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert is_valid is True
    assert len(errors) == 0


# --------------------------------------------------------------------------- #
# 2. Creator Consent Modifications Audit Trail
# --------------------------------------------------------------------------- #
def test_creator_consent_modification_audit_chain(db_session):
    """Test auditing creator consent state transitions: consented -> verified_written -> revoked."""
    creator, _ = _create_test_artisan_and_experience(db_session)

    # 1. Record transition to verified written consent
    audit_1 = record_creator_consent_change(
        db_session,
        creator=creator,
        old_status=RbpcConsentStatus.consented,
        new_status=RbpcConsentStatus.verified_written_consent,
        proof_ref="DOC-SIGNED-2026-HUE-042",
        reason="Đã thu thập văn bản đồng thuận có chữ ký và dấu mộc làng nghề.",
    )
    assert audit_1.previous_hash is None
    assert creator.consent_status == RbpcConsentStatus.verified_written_consent.value
    assert creator.display_consent_ref == "DOC-SIGNED-2026-HUE-042"

    # 2. Record consent revocation
    audit_2 = record_creator_consent_change(
        db_session,
        creator=creator,
        old_status=RbpcConsentStatus.verified_written_consent,
        new_status=RbpcConsentStatus.revoked,
        reason="Nghệ nhân tạm dừng tham gia chương trình theo nguyện vọng cá nhân.",
    )
    assert audit_2.previous_hash == audit_1.new_hash
    assert creator.consent_status == RbpcConsentStatus.revoked.value

    # 3. Cryptographic chain verification
    is_valid, errors = verify_audit_chain(db_session, entity_type=ENTITY_CREATOR, entity_id=creator.id)
    assert is_valid is True
    assert len(errors) == 0


# --------------------------------------------------------------------------- #
# 3. Experience Updates Audit Trail
# --------------------------------------------------------------------------- #
def test_experience_update_audit_trail(db_session):
    """Test auditing experience updates (pricing, capacity, availability mode)."""
    _, experience = _create_test_artisan_and_experience(db_session)

    # Update 1: price adjustment
    audit_1 = record_experience_update(
        db_session,
        experience=experience,
        changes={"indicative_price_amount": 750000.0, "pricing_display": "Từ 750.000 VNĐ / khách"},
        reason="Điều chỉnh chi phí nguyên vật liệu bạc và men màu.",
    )
    assert audit_1.previous_hash is None

    # Update 2: availability mode changed to disabled
    audit_2 = record_experience_update(
        db_session,
        experience=experience,
        changes={"availability_mode": "disabled"},
        reason="Xưởng tu bổ cơ sở vật chất định kỳ.",
    )
    assert audit_2.previous_hash == audit_1.new_hash

    # Verify chain
    is_valid, errors = verify_audit_chain(db_session, entity_type=ENTITY_EXPERIENCE, entity_id=experience.id)
    assert is_valid is True
    assert len(errors) == 0


# --------------------------------------------------------------------------- #
# 4. Tamper Detection & Cryptographic Defense
# --------------------------------------------------------------------------- #
def test_tamper_detection_in_hash_chain(db_session):
    """Verify cryptographic verification catches tampered content or forged hashes."""
    creator, experience = _create_test_artisan_and_experience(db_session)
    inquiry = _create_test_inquiry(db_session, experience.id)

    # Record 2 valid entries
    record_audit_entry(
        db_session,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry.id,
        action=ACTION_INQUIRY_CREATED,
        diff_payload={"state": "new"},
    )
    entry_2 = record_inquiry_state_transition(
        db_session,
        inquiry=inquiry,
        old_state="new",
        new_state=RbpcInquiryStatus.contacted,
    )

    # Verify clean initial state
    is_valid, _ = verify_audit_chain(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert is_valid is True

    # Tamper with diff_payload of entry_2 without updating new_hash
    entry_2.diff_payload = {"state": "hacked_state"}
    db_session.flush()

    # Chain verification MUST fail
    is_tampered, errors = verify_audit_chain(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert is_tampered is False
    assert any("Tampered content at entry" in err for err in errors)

    # Restore correct diff payload and re-verify
    entry_2.diff_payload = {
        "field": "state",
        "old_state": "new",
        "new_state": "contacted",
        "public_ref": inquiry.public_ref,
        "experience_id": str(inquiry.experience_id),
    }
    # Recompute valid hash to make row hash valid, then break previous_hash linkage
    entry_2.new_hash = compute_audit_hash(
        previous_hash="forged_fake_previous_hash_0000000000000000000000000000000000000000",
        entity_type=entry_2.entity_type,
        entity_id=entry_2.entity_id,
        action=entry_2.action,
        actor_id=entry_2.actor_id,
        diff_payload=entry_2.diff_payload,
        approved_scope=entry_2.approved_scope,
        created_at=entry_2.created_at,
    )
    entry_2.previous_hash = "forged_fake_previous_hash_0000000000000000000000000000000000000000"
    db_session.flush()

    is_tampered_link, errors_link = verify_audit_chain(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert is_tampered_link is False
    assert any("Broken hash chain at entry" in err for err in errors_link)


# --------------------------------------------------------------------------- #
# 5. Retention Policies Engine & PII Redaction
# --------------------------------------------------------------------------- #
def test_inquiry_retention_policy_purge_and_audit(db_session):
    """Test purging expired inquiries according to retention policy with zero-PII audit trail."""
    creator, experience = _create_test_artisan_and_experience(db_session)

    # 1. Create an active inquiry (not expired)
    inquiry_active = _create_test_inquiry(
        db_session,
        experience.id,
        retention_due_at=datetime.now(timezone.utc) + timedelta(days=45),
        name="Khách Đang Chờ",
        contact_value="dangcho@example.com",
    )

    # 2. Create an expired inquiry (retention_due_at in the past)
    inquiry_expired = _create_test_inquiry(
        db_session,
        experience.id,
        retention_due_at=datetime.now(timezone.utc) - timedelta(days=5),
        name="Khách Hết Hạn Lưu Trữ",
        contact_value="hethan@example.com",
        message="Thông tin cá nhân cần được gỡ bỏ sau thời gian bảo lưu.",
    )

    # Check queries due for retention
    due = get_inquiries_due_for_retention(db_session)
    assert len(due) == 1
    assert due[0].id == inquiry_expired.id

    # 3. Dry-run execution
    dry_result = apply_inquiry_retention_policy(db_session, dry_run=True)
    assert dry_result["dry_run"] is True
    assert dry_result["expired_count"] == 1
    assert inquiry_expired.name == "Khách Hết Hạn Lưu Trữ"  # Unchanged in dry run

    # 4. Commit execution
    purge_result = apply_inquiry_retention_policy(db_session, dry_run=False)
    assert purge_result["dry_run"] is False
    assert purge_result["purged_count"] == 1
    assert inquiry_expired.public_ref in purge_result["purged_references"]

    # 5. Verify PII fields redacted
    db_session.refresh(inquiry_expired)
    assert inquiry_expired.name == "[RETENTION_PURGED]"
    assert inquiry_expired.contact_value == "[RETENTION_PURGED]"
    assert inquiry_expired.message is None
    assert inquiry_expired.state == RbpcInquiryStatus.closed.value
    assert inquiry_expired.retention_due_at is None

    # Verify active inquiry was completely untouched
    db_session.refresh(inquiry_active)
    assert inquiry_active.name == "Khách Đang Chờ"
    assert inquiry_active.contact_value == "dangcho@example.com"
    assert inquiry_active.retention_due_at is not None

    # 6. Verify audit log created with zero PII
    audit_entries, count = get_audit_trail(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry_expired.id)
    assert count == 1
    purge_audit = audit_entries[0]
    assert purge_audit.action == ACTION_RETENTION_PURGE
    # Verify no PII in diff_payload
    payload_str = str(purge_audit.diff_payload)
    assert "Khách Hết Hạn Lưu Trữ" not in payload_str
    assert "hethan@example.com" not in payload_str
    assert purge_audit.diff_payload["public_ref"] == inquiry_expired.public_ref


def test_extend_inquiry_retention_window(db_session):
    """Test extending retention due date for inquiries in active discussion."""
    creator, experience = _create_test_artisan_and_experience(db_session)
    orig_due = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)
    inquiry = _create_test_inquiry(db_session, experience.id, retention_due_at=orig_due)

    extended_inq, audit = extend_inquiry_retention(
        db_session,
        inquiry_id=inquiry.id,
        additional_days=60,
        reason="Khách yêu cầu dời lịch trải nghiệm sang quý 1 năm sau.",
    )

    expected_due = orig_due + timedelta(days=60)
    assert extended_inq.retention_due_at == expected_due
    assert audit.action == ACTION_RETENTION_EXTENDED
    assert audit.diff_payload["additional_days"] == 60


# --------------------------------------------------------------------------- #
# 6. Re-Import Preservation of Inquiries, Audit Logs & Consent
# --------------------------------------------------------------------------- #
def test_reimport_preserves_inquiries_audit_logs_and_consent(db_session):
    """Verify that running heritage_import never modifies or degrades existing inquiries, audits, or consent."""
    # 1. Run initial import to populate seed catalogue
    import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    # 2. Pick a creator and verify written consent
    creator = db_session.scalar(select(RbpcCreator).limit(1))
    assert creator is not None
    original_creator_slug = creator.slug

    # Set creator to verified_written_consent with custom release code
    record_creator_consent_change(
        db_session,
        creator=creator,
        old_status=creator.consent_status,
        new_status=RbpcConsentStatus.verified_written_consent,
        proof_ref="SPECIAL-RELEASE-CONTRACT-2026",
    )
    db_session.commit()

    # 3. Create an active inquiry with audit trail
    exp = db_session.scalar(select(RbpcExperience).where(RbpcExperience.creator_id == creator.id).limit(1))
    if not exp:
        exp = db_session.scalar(select(RbpcExperience).limit(1))

    inquiry = _create_test_inquiry(
        db_session,
        exp.id,
        state=RbpcInquiryStatus.confirmed.value,
        name="Bảo Lưu Khi Re-import",
        public_ref="INQ-REIMPORT-PRESERVE-01",
    )
    record_inquiry_state_transition(
        db_session,
        inquiry=inquiry,
        old_state="new",
        new_state=RbpcInquiryStatus.confirmed,
        note="Xác nhận trước re-import",
    )
    db_session.commit()

    # Capture counts before re-import
    pre_inquiry_count = db_session.scalar(select(func.count(RbpcInquiry.id)))
    pre_audit_count = db_session.scalar(select(func.count(RbpcContentAudit.id)))

    # 4. Re-run heritage import in commit mode
    _, stats = import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    # 5. Assertions: Inquiries and Audit logs preserved intact
    post_inquiry_count = db_session.scalar(select(func.count(RbpcInquiry.id)))
    post_audit_count = db_session.scalar(select(func.count(RbpcContentAudit.id)))

    assert post_inquiry_count == pre_inquiry_count
    assert post_audit_count == pre_audit_count
    assert stats.inquiries_preserved == pre_inquiry_count
    assert stats.audit_logs_preserved == pre_audit_count

    # Verify specific inquiry state is preserved
    preserved_inq = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.public_ref == "INQ-REIMPORT-PRESERVE-01")
    )
    assert preserved_inq is not None
    assert preserved_inq.state == RbpcInquiryStatus.confirmed.value
    assert preserved_inq.name == "Bảo Lưu Khi Re-import"

    # Verify creator's upgraded consent status is preserved
    db_session.refresh(creator)
    assert creator.consent_status == RbpcConsentStatus.verified_written_consent.value
    assert creator.display_consent_ref == "SPECIAL-RELEASE-CONTRACT-2026"
    assert stats.creators_preserved_consent >= 1

    # Verify all audit chains remain cryptographically intact
    all_valid, summary = verify_all_audit_chains(db_session)
    assert all_valid is True
    assert summary["corrupted_entities_count"] == 0
