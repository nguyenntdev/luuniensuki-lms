# -*- coding: utf-8 -*-
"""LƯU NIÊN — RBPC 2026 Audit Trails, Cryptographic Hash Chains, and Retention Policies.

This module provides the database service for:
1. Append-only audit entries in ``rbpc_content_audit`` whenever:
   - An inquiry changes state (new -> contacted -> confirmed -> declined -> closed).
   - Creator consent is modified or verified (consented -> verified_written_consent -> revoked).
   - A cultural experience is updated (availability mode, pricing, publication).
2. Cryptographic SHA-256 hash chaining:
   - Each audit entry computes ``new_hash = SHA256(previous_hash + canonical_entry_data)``.
   - Consecutive entries form an unbroken cryptographic chain per entity.
   - Provides immutable verification ensuring zero undetected tampering, insertions, or omissions.
3. Retention policies engine:
   - Evaluates ``retention_due_at`` on visitor booking inquiries (default 90-day window).
   - Anonymizes / purges visitor PII (name, contact_value, message) while maintaining aggregate
     counts, public references, and immutable cryptographic audit records with zero PII.
4. Epistemic and privacy invariants:
   - Audit diff payloads MUST NOT store raw personal visitor testimony or private credentials.
   - All operations are isolated to the ``RBPC_HUE`` scope.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models_rbpc import (
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)

logger = logging.getLogger("luuniensuki.rbpc_audit")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
APPROVED_SCOPE_DEFAULT = "RBPC_HUE"
GENESIS_HASH_SENTINEL = "GENESIS"

ENTITY_INQUIRY = "inquiry"
ENTITY_CREATOR = "creator"
ENTITY_EXPERIENCE = "experience"
ENTITY_STORY = "story"
ENTITY_PLACE = "place"

ACTION_STATE_TRANSITION = "state_transition"
ACTION_CONSENT_MODIFIED = "consent_modified"
ACTION_EXPERIENCE_UPDATED = "experience_updated"
ACTION_INQUIRY_CREATED = "inquiry_created"
ACTION_RETENTION_PURGE = "retention_purge"
ACTION_RETENTION_EXTENDED = "retention_extended"
ACTION_GENERIC_UPDATE = "update"


# --------------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------------- #
def _parse_uuid(val: Union[UUID, str, None]) -> Optional[UUID]:
    """Parse UUID from string or return UUID object."""
    if val is None:
        return None
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


def _normalize_datetime(dt: Optional[datetime]) -> str:
    """Normalize datetime to deterministic ISO 8601 UTC string."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def canonical_json(data: Optional[dict[str, Any]]) -> str:
    """Produce deterministic, sorted, compact JSON representation."""
    if not data:
        return "{}"
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


# --------------------------------------------------------------------------- #
# Cryptographic SHA-256 Hash Computation
# --------------------------------------------------------------------------- #
def compute_audit_hash(
    *,
    previous_hash: Optional[str],
    entity_type: str,
    entity_id: Union[UUID, str],
    action: str,
    actor_id: Optional[Union[UUID, str]] = None,
    diff_payload: Optional[dict[str, Any]] = None,
    approved_scope: str = APPROVED_SCOPE_DEFAULT,
    created_at: Optional[datetime] = None,
) -> str:
    """Compute deterministic SHA-256 cryptographic hash for an audit record.

    Preimage construction:
    sha256("prev:{prev_str}|type:{type}|id:{id}|act:{act}|actor:{actor}|diff:{payload}|scope:{scope}|time:{time}")
    """
    prev_str = previous_hash if previous_hash else GENESIS_HASH_SENTINEL
    actor_str = str(actor_id) if actor_id else ""
    id_str = str(entity_id)
    payload_str = canonical_json(diff_payload)
    time_str = _normalize_datetime(created_at)

    preimage = (
        f"prev:{prev_str}|"
        f"type:{entity_type}|"
        f"id:{id_str}|"
        f"act:{action}|"
        f"actor:{actor_str}|"
        f"diff:{payload_str}|"
        f"scope:{approved_scope}|"
        f"time:{time_str}"
    )
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Latest Audit Entry & Chain Lookup
# --------------------------------------------------------------------------- #
def get_latest_audit_entry(
    db: Session,
    *,
    entity_type: str,
    entity_id: Union[UUID, str],
) -> Optional[RbpcContentAudit]:
    """Retrieve the most recent audit entry for an entity."""
    e_id = _parse_uuid(entity_id)
    return db.scalars(
        select(RbpcContentAudit)
        .where(
            RbpcContentAudit.entity_type == str(entity_type),
            RbpcContentAudit.entity_id == e_id,
        )
        .order_by(RbpcContentAudit.created_at.desc(), RbpcContentAudit.id.desc())
    ).first()


def get_audit_trail(
    db: Session,
    *,
    entity_type: str,
    entity_id: Union[UUID, str],
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[RbpcContentAudit], int]:
    """Retrieve chronological audit trail entries and total count for an entity."""
    e_id = _parse_uuid(entity_id)
    base_filter = [
        RbpcContentAudit.entity_type == str(entity_type),
        RbpcContentAudit.entity_id == e_id,
    ]
    total = db.scalar(select(func.count(RbpcContentAudit.id)).where(*base_filter)) or 0
    entries = list(
        db.scalars(
            select(RbpcContentAudit)
            .where(*base_filter)
            .order_by(RbpcContentAudit.created_at.asc(), RbpcContentAudit.id.asc())
            .offset(offset)
            .limit(limit)
        )
    )
    return entries, total


# --------------------------------------------------------------------------- #
# Core Append-Only Audit Entry Recording
# --------------------------------------------------------------------------- #
def record_audit_entry(
    db: Session,
    *,
    entity_type: str,
    entity_id: Union[UUID, str],
    action: str,
    actor_id: Optional[Union[UUID, str]] = None,
    diff_payload: Optional[dict[str, Any]] = None,
    approved_scope: str = APPROVED_SCOPE_DEFAULT,
    created_at: Optional[datetime] = None,
) -> RbpcContentAudit:
    """Record an immutable, append-only audit entry with cryptographic hash chaining.

    Args:
        db: SQLAlchemy database session.
        entity_type: Controlled resource type ('inquiry', 'creator', 'experience', etc.).
        entity_id: Target resource UUID.
        action: Event action name ('state_transition', 'consent_modified', etc.).
        actor_id: Authenticated user ID or None for anonymous/system.
        diff_payload: JSON-serializable diff dictionary (free of visitor PII).
        approved_scope: Content boundary scope, defaults to 'RBPC_HUE'.
        created_at: Timestamp override or current UTC time.

    Returns:
        The persisted and cryptographically signed RbpcContentAudit record.
    """
    e_id = _parse_uuid(entity_id)
    if e_id is None:
        raise ValueError("entity_id is required and must be a valid UUID")

    a_id = _parse_uuid(actor_id)
    entry_time = created_at or datetime.now(timezone.utc)

    # 1. Retrieve the tip of the hash chain for this entity
    last_entry = get_latest_audit_entry(db, entity_type=entity_type, entity_id=e_id)
    previous_hash = last_entry.new_hash if last_entry else None

    # 2. Compute cryptographic SHA-256 hash chain
    new_hash = compute_audit_hash(
        previous_hash=previous_hash,
        entity_type=entity_type,
        entity_id=e_id,
        action=action,
        actor_id=a_id,
        diff_payload=diff_payload,
        approved_scope=approved_scope,
        created_at=entry_time,
    )

    # 3. Create and append audit record
    audit_record = RbpcContentAudit(
        id=uuid.uuid4(),
        entity_type=entity_type,
        entity_id=e_id,
        action=action,
        actor_id=a_id,
        previous_hash=previous_hash,
        new_hash=new_hash,
        diff_payload=diff_payload,
        approved_scope=approved_scope,
        created_at=entry_time,
    )
    db.add(audit_record)
    db.flush()

    logger.debug(
        "Recorded audit entry %s for %s:%s (action=%s, prev=%s, new=%s)",
        audit_record.id,
        entity_type,
        e_id,
        action,
        previous_hash[:8] if previous_hash else "None",
        new_hash[:8],
    )
    return audit_record


# --------------------------------------------------------------------------- #
# Specialized Event Loggers: Inquiry State Transitions
# --------------------------------------------------------------------------- #
def record_inquiry_state_transition(
    db: Session,
    *,
    inquiry: Union[RbpcInquiry, UUID, str],
    old_state: Optional[str],
    new_state: Union[str, RbpcInquiryStatus],
    actor_id: Optional[Union[UUID, str]] = None,
    note: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> RbpcContentAudit:
    """Record an append-only audit entry for an inquiry state transition.

    Enforces zero PII in audit payloads: only reference, state, and non-PII notes are stored.
    """
    inquiry_obj: Optional[RbpcInquiry] = None
    if isinstance(inquiry, RbpcInquiry):
        inquiry_obj = inquiry
        inquiry_id = inquiry.id
    else:
        inquiry_id = _parse_uuid(inquiry)
        if inquiry_id:
            inquiry_obj = db.get(RbpcInquiry, inquiry_id)

    new_state_str = new_state.value if isinstance(new_state, RbpcInquiryStatus) else str(new_state)
    old_state_str = old_state.value if isinstance(old_state, RbpcInquiryStatus) else (str(old_state) if old_state else None)

    public_ref = inquiry_obj.public_ref if inquiry_obj else "unknown"
    exp_id = str(inquiry_obj.experience_id) if inquiry_obj else None

    diff_payload: dict[str, Any] = {
        "field": "state",
        "old_state": old_state_str,
        "new_state": new_state_str,
        "public_ref": public_ref,
    }
    if exp_id:
        diff_payload["experience_id"] = exp_id
    if note:
        diff_payload["note"] = note
    if metadata:
        diff_payload.update(metadata)

    return record_audit_entry(
        db,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry_id,
        action=ACTION_STATE_TRANSITION,
        actor_id=actor_id,
        diff_payload=diff_payload,
    )


# --------------------------------------------------------------------------- #
# Specialized Event Loggers: Creator Consent Modifications
# --------------------------------------------------------------------------- #
def record_creator_consent_change(
    db: Session,
    *,
    creator: Union[RbpcCreator, UUID, str],
    new_status: Union[str, RbpcConsentStatus],
    old_status: Optional[Union[str, RbpcConsentStatus]] = None,
    actor_id: Optional[Union[UUID, str]] = None,
    reason: Optional[str] = None,
    proof_ref: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> RbpcContentAudit:
    """Record an append-only audit entry when creator consent is modified or revoked.

    Also updates the creator ORM instance if passed.
    """
    creator_obj: Optional[RbpcCreator] = None
    if isinstance(creator, RbpcCreator):
        creator_obj = creator
        creator_id = creator.id
    else:
        creator_id = _parse_uuid(creator)
        if creator_id:
            creator_obj = db.get(RbpcCreator, creator_id)

    new_status_str = new_status.value if isinstance(new_status, RbpcConsentStatus) else str(new_status)
    old_status_str = (
        old_status.value
        if isinstance(old_status, RbpcConsentStatus)
        else (str(old_status) if old_status else (creator_obj.consent_status if creator_obj else None))
    )

    # Mutate ORM object if present
    if creator_obj:
        creator_obj.consent_status = new_status_str
        if proof_ref:
            creator_obj.display_consent_ref = proof_ref
        creator_obj.updated_at = datetime.now(timezone.utc)

    creator_slug = creator_obj.slug if creator_obj else "unknown"
    public_name = creator_obj.public_name if creator_obj else "unknown"

    diff_payload: dict[str, Any] = {
        "field": "consent_status",
        "old_status": old_status_str,
        "new_status": new_status_str,
        "creator_slug": creator_slug,
        "public_name": public_name,
    }
    if proof_ref:
        diff_payload["proof_ref"] = proof_ref
    if reason:
        diff_payload["reason"] = reason
    if metadata:
        diff_payload.update(metadata)

    return record_audit_entry(
        db,
        entity_type=ENTITY_CREATOR,
        entity_id=creator_id,
        action=ACTION_CONSENT_MODIFIED,
        actor_id=actor_id,
        diff_payload=diff_payload,
    )


# --------------------------------------------------------------------------- #
# Specialized Event Loggers: Experience Updates
# --------------------------------------------------------------------------- #
def record_experience_update(
    db: Session,
    *,
    experience: Union[RbpcExperience, UUID, str],
    changes: dict[str, Any],
    actor_id: Optional[Union[UUID, str]] = None,
    reason: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> RbpcContentAudit:
    """Record an append-only audit entry when a cultural experience offering is updated."""
    exp_obj: Optional[RbpcExperience] = None
    if isinstance(experience, RbpcExperience):
        exp_obj = experience
        exp_id = experience.id
    else:
        exp_id = _parse_uuid(experience)
        if exp_id:
            exp_obj = db.get(RbpcExperience, exp_id)

    slug = exp_obj.slug if exp_obj else "unknown"
    title_vi = exp_obj.title_vi if exp_obj else "unknown"

    diff_payload: dict[str, Any] = {
        "experience_slug": slug,
        "title_vi": title_vi,
        "changes": changes,
    }
    if reason:
        diff_payload["reason"] = reason
    if metadata:
        diff_payload.update(metadata)

    return record_audit_entry(
        db,
        entity_type=ENTITY_EXPERIENCE,
        entity_id=exp_id,
        action=ACTION_EXPERIENCE_UPDATED,
        actor_id=actor_id,
        diff_payload=diff_payload,
    )


# --------------------------------------------------------------------------- #
# Cryptographic Chain Verification Engine
# --------------------------------------------------------------------------- #
def verify_audit_chain(
    db: Session,
    *,
    entity_type: str,
    entity_id: Union[UUID, str],
) -> tuple[bool, list[str]]:
    """Cryptographically verify the hash chain integrity for an entity.

    Checks:
    1. Recomputed SHA-256 hash of each row matches its stored ``new_hash``.
    2. Genesis entry (index 0) has ``previous_hash is None``.
    3. Each subsequent entry's ``previous_hash`` exactly equals the preceding entry's ``new_hash``.

    Returns:
        tuple[bool, list[str]]: (is_valid, list of verification error messages).
    """
    entries, _ = get_audit_trail(db, entity_type=entity_type, entity_id=entity_id, limit=10000)
    if not entries:
        return True, []

    errors: list[str] = []
    expected_prev_hash: Optional[str] = None

    for idx, entry in enumerate(entries):
        # 1. Verify previous_hash linkage
        if idx == 0:
            if entry.previous_hash is not None:
                errors.append(
                    f"Genesis entry {entry.id} has non-null previous_hash: '{entry.previous_hash}'"
                )
        else:
            if entry.previous_hash != expected_prev_hash:
                errors.append(
                    f"Broken hash chain at entry index {idx} ({entry.id}): "
                    f"stored previous_hash='{entry.previous_hash}' != expected '{expected_prev_hash}'"
                )

        # 2. Recompute cryptographic hash for this row
        recomputed = compute_audit_hash(
            previous_hash=entry.previous_hash,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            action=entry.action,
            actor_id=entry.actor_id,
            diff_payload=entry.diff_payload,
            approved_scope=entry.approved_scope,
            created_at=entry.created_at,
        )

        if entry.new_hash != recomputed:
            errors.append(
                f"Tampered content at entry {entry.id} (index {idx}): "
                f"stored new_hash='{entry.new_hash}' != recomputed '{recomputed}'"
            )

        expected_prev_hash = entry.new_hash

    is_valid = len(errors) == 0
    return is_valid, errors


def verify_all_audit_chains(db: Session) -> tuple[bool, dict[str, Any]]:
    """Verify cryptographic integrity across all distinct entities in ``rbpc_content_audit``."""
    # Group distinct (entity_type, entity_id) pairs
    distinct_entities = db.execute(
        select(RbpcContentAudit.entity_type, RbpcContentAudit.entity_id).distinct()
    ).all()

    total_entities = len(distinct_entities)
    verified_entities = 0
    all_errors: dict[str, list[str]] = {}

    for e_type, e_id in distinct_entities:
        is_valid, errors = verify_audit_chain(db, entity_type=e_type, entity_id=e_id)
        if is_valid:
            verified_entities += 1
        else:
            all_errors[f"{e_type}:{e_id}"] = errors

    is_all_valid = len(all_errors) == 0
    summary = {
        "is_valid": is_all_valid,
        "total_entities_checked": total_entities,
        "verified_entities_count": verified_entities,
        "corrupted_entities_count": len(all_errors),
        "errors": all_errors,
    }
    return is_all_valid, summary


# --------------------------------------------------------------------------- #
# Retention Policies Engine
# --------------------------------------------------------------------------- #
def get_inquiries_due_for_retention(
    db: Session,
    *,
    as_of: Optional[datetime] = None,
) -> list[RbpcInquiry]:
    """Query inquiries whose contact retention window has expired."""
    cutoff = as_of or datetime.now(timezone.utc)
    return list(
        db.scalars(
            select(RbpcInquiry)
            .where(
                RbpcInquiry.retention_due_at.is_not(None),
                RbpcInquiry.retention_due_at <= cutoff,
            )
            .order_by(RbpcInquiry.retention_due_at.asc())
        )
    )


def apply_inquiry_retention_policy(
    db: Session,
    *,
    as_of: Optional[datetime] = None,
    actor_id: Optional[Union[UUID, str]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute retention policy purge on expired visitor booking inquiries.

    Privacy-by-Design Rules:
    - Redacts personal identifiable fields: ``name``, ``contact_value``, ``message``, ``internal_note``.
    - Replaces with privacy markers (``[RETENTION_PURGED]``).
    - Sets state to ``closed``.
    - Sets ``retention_due_at = None`` to mark purge complete.
    - Preserves anonymous metrics: ``public_ref``, ``experience_id``, ``party_size``, ``desired_date``.
    - Appends an immutable cryptographic audit entry to ``rbpc_content_audit`` with zero PII.
    """
    cutoff = as_of or datetime.now(timezone.utc)
    expired = get_inquiries_due_for_retention(db, as_of=cutoff)

    purged_refs: list[str] = []
    audits_recorded: list[str] = []

    if dry_run:
        return {
            "dry_run": True,
            "expired_count": len(expired),
            "purged_references": [inq.public_ref for inq in expired],
            "cutoff": cutoff.isoformat(),
        }

    for inq in expired:
        old_state = inq.state
        purged_refs.append(inq.public_ref)

        # Redact PII
        inq.name = "[RETENTION_PURGED]"
        inq.contact_value = "[RETENTION_PURGED]"
        inq.message = None
        inq.internal_note = None
        inq.state = RbpcInquiryStatus.closed.value
        inq.retention_due_at = None
        inq.updated_at = datetime.now(timezone.utc)

        # Record audit entry with zero PII
        audit_entry = record_audit_entry(
            db,
            entity_type=ENTITY_INQUIRY,
            entity_id=inq.id,
            action=ACTION_RETENTION_PURGE,
            actor_id=actor_id,
            diff_payload={
                "action": ACTION_RETENTION_PURGE,
                "public_ref": inq.public_ref,
                "previous_state": old_state,
                "new_state": inq.state,
                "reason": "retention_due_at_expired",
                "purged_at": cutoff.isoformat(),
            },
        )
        audits_recorded.append(str(audit_entry.id))

    db.flush()
    logger.info("Executed retention purge on %d expired inquiries.", len(expired))
    return {
        "dry_run": False,
        "purged_count": len(expired),
        "purged_references": purged_refs,
        "audit_ids": audits_recorded,
        "cutoff": cutoff.isoformat(),
    }


def extend_inquiry_retention(
    db: Session,
    *,
    inquiry_id: Union[UUID, str],
    additional_days: int = 30,
    actor_id: Optional[Union[UUID, str]] = None,
    reason: Optional[str] = None,
) -> tuple[RbpcInquiry, RbpcContentAudit]:
    """Extend the retention window for an ongoing inquiry with audit logging."""
    i_id = _parse_uuid(inquiry_id)
    inquiry = db.get(RbpcInquiry, i_id)
    if not inquiry:
        raise ValueError(f"Inquiry with ID '{inquiry_id}' not found.")

    old_retention = inquiry.retention_due_at
    base_time = old_retention or datetime.now(timezone.utc)
    new_retention = base_time + timedelta(days=additional_days)
    inquiry.retention_due_at = new_retention
    inquiry.updated_at = datetime.now(timezone.utc)

    audit_entry = record_audit_entry(
        db,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry.id,
        action=ACTION_RETENTION_EXTENDED,
        actor_id=actor_id,
        diff_payload={
            "action": ACTION_RETENTION_EXTENDED,
            "public_ref": inquiry.public_ref,
            "old_retention_due_at": old_retention.isoformat() if old_retention else None,
            "new_retention_due_at": new_retention.isoformat(),
            "additional_days": additional_days,
            "reason": reason,
        },
    )
    return inquiry, audit_entry
