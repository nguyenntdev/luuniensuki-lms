# -*- coding: utf-8 -*-
"""LƯU NIÊN — RBPC 2026 Inquiry Consent Lifecycle & Privacy Retention Service.

Enforces privacy-by-design compliance (Vietnam Decree 13/2023/ND-CP, Art. 11/20):
- 90-day retention window enforcement: automated anonymization/redaction of expired inquiries.
- Immediate consent withdrawal: visitor-initiated right to erasure/redaction via opaque status token.
- Zero-PII immutable audit logging: append-only cryptographic record of retention and withdrawal events.
- Aggregate metrics preservation: references, experience linkage, and party size remain for reporting.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from ..errors import AppError
from ..models_rbpc import RbpcInquiry, RbpcInquiryStatus
from .rbpc_audit import (
    ACTION_RETENTION_PURGE,
    ENTITY_INQUIRY,
    record_audit_entry,
)

logger = logging.getLogger("luuniensuki.rbpc.retention")

ANONYMIZED_NAME = "[ANONYMIZED]"
REDACTED_CONTACT = "[REDACTED]"
ACTION_CONSENT_WITHDRAWN = "consent_withdrawn"
DEFAULT_RETENTION_DAYS = 90


def enforce_inquiry_retention_policy(
    db: Session,
    reference_time: Optional[datetime] = None,
) -> dict[str, Any]:
    """Find and anonymize visitor booking inquiries past their retention window.

    Finds inquiries where:
    - ``retention_due_at <= now`` (standard 90-day window expired), OR
    - closed inquiries past retention,
    and where personal contact details have not yet been redacted.

    Anonymizes:
    - ``name = "[ANONYMIZED]"``
    - ``contact_value = "[REDACTED]"``
    - ``message = None``
    - ``internal_note = None``
    - ``state = "closed"``

    Preserves aggregate metrics (public_ref, experience_id, party_size, desired_date)
    and records an immutable cryptographic audit entry with zero PII.
    """
    ref_time = reference_time or datetime.now(timezone.utc)
    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=timezone.utc)

    stmt = (
        select(RbpcInquiry)
        .where(
            or_(
                and_(
                    RbpcInquiry.retention_due_at.is_not(None),
                    RbpcInquiry.retention_due_at <= ref_time,
                ),
                and_(
                    RbpcInquiry.state == RbpcInquiryStatus.closed.value,
                    or_(
                        and_(
                            RbpcInquiry.retention_due_at.is_not(None),
                            RbpcInquiry.retention_due_at <= ref_time,
                        ),
                        and_(
                            RbpcInquiry.retention_due_at.is_(None),
                            RbpcInquiry.updated_at <= ref_time,
                        ),
                    ),
                ),
            ),
            or_(
                RbpcInquiry.name != ANONYMIZED_NAME,
                RbpcInquiry.contact_value != REDACTED_CONTACT,
                RbpcInquiry.message.is_not(None),
            ),
        )
        .order_by(RbpcInquiry.created_at.asc())
    )

    expired_inquiries = list(db.scalars(stmt))
    anonymized_refs: list[str] = []
    audit_ids: list[str] = []

    for inq in expired_inquiries:
        old_state = inq.state
        anonymized_refs.append(inq.public_ref)

        # Redact all sensitive visitor PII
        inq.name = ANONYMIZED_NAME
        inq.contact_value = REDACTED_CONTACT
        inq.message = None
        inq.internal_note = None
        inq.state = RbpcInquiryStatus.closed.value
        inq.updated_at = datetime.now(timezone.utc)

        # Append immutable audit entry with zero PII
        audit_entry = record_audit_entry(
            db,
            entity_type=ENTITY_INQUIRY,
            entity_id=inq.id,
            action=ACTION_RETENTION_PURGE,
            actor_id=None,
            diff_payload={
                "action": ACTION_RETENTION_PURGE,
                "public_ref": inq.public_ref,
                "previous_state": old_state,
                "new_state": inq.state,
                "reason": "retention_policy_enforcement",
                "reference_time": ref_time.isoformat(),
            },
        )
        audit_ids.append(str(audit_entry.id))

    db.flush()
    logger.info(
        "Enforced inquiry retention policy on %d inquiries as of %s.",
        len(expired_inquiries),
        ref_time.isoformat(),
    )

    return {
        "anonymized_count": len(expired_inquiries),
        "purged_count": len(expired_inquiries),
        "anonymized_references": anonymized_refs,
        "purged_references": anonymized_refs,
        "audit_ids": audit_ids,
        "inquiries": expired_inquiries,
        "reference_time": ref_time.isoformat(),
    }


def withdraw_inquiry_consent(
    db: Session,
    opaque_token: str,
) -> RbpcInquiry:
    """Allow a visitor to withdraw consent immediately via their opaque status bearer token.

    Decree 13/2023/ND-CP Article 11 right of withdrawal:
    - Immediately scrubs personal contact details:
      ``name = "[ANONYMIZED]"``, ``contact_value = "[REDACTED]"``, ``message = None``
    - Marks ``privacy_accepted = False``
    - Transitions lifecycle state to ``closed``
    - Appends immutable cryptographic audit entry for compliance proof
    """
    cleaned_token = (opaque_token or "").strip()
    if not cleaned_token:
        raise AppError(
            "RBPC_INQUIRY_NOT_FOUND",
            "Inquiry not found for status token.",
            status.HTTP_404_NOT_FOUND,
        )

    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(RbpcInquiry.opaque_token == cleaned_token)
    )
    if not inquiry:
        raise AppError(
            "RBPC_INQUIRY_NOT_FOUND",
            "Inquiry not found for status token.",
            status.HTTP_404_NOT_FOUND,
        )

    # Idempotent check: if already withdrawn and anonymized, return existing record
    if not inquiry.privacy_accepted and inquiry.name == ANONYMIZED_NAME:
        return inquiry

    old_state = inquiry.state

    # Scrub PII immediately
    inquiry.name = ANONYMIZED_NAME
    inquiry.contact_value = REDACTED_CONTACT
    inquiry.message = None
    inquiry.internal_note = None
    inquiry.privacy_accepted = False
    inquiry.state = RbpcInquiryStatus.closed.value
    inquiry.updated_at = datetime.now(timezone.utc)

    # Record append-only audit trail
    record_audit_entry(
        db,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry.id,
        action=ACTION_CONSENT_WITHDRAWN,
        actor_id=None,
        diff_payload={
            "action": ACTION_CONSENT_WITHDRAWN,
            "public_ref": inquiry.public_ref,
            "previous_state": old_state,
            "new_state": inquiry.state,
            "privacy_accepted": False,
            "reason": "visitor_withdrew_consent",
        },
    )

    db.flush()
    logger.info(
        "Consent withdrawn and PII redacted for inquiry ref=%s (token=...%s).",
        inquiry.public_ref,
        cleaned_token[-8:],
    )
    return inquiry
