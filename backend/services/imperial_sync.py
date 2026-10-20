# -*- coding: utf-8 -*-
"""Imperial offline sync service — STTTNNĐ (Lưu Niên — Đại Nội Huế).
Spec: STTT-SPEC-PWA-PRINT-001.

Processes queued submissions from PWA / Service Worker IndexedDB when the client
reconnects to the network:
- Idempotent processing per (activity_id, student_id)
- Respects client_timestamp recorded offline
- Handles duplicates, updates, and validates activity existence under CONTENT_SCOPE_IMPERIAL
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..apischemas.imperial_sync import (
    ImperialBatchSyncResponse,
    ImperialOfflineSubmissionItem,
    ImperialSyncItemResult,
)
from ..imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialActivity,
    ImperialSubmission,
)

logger = logging.getLogger(__name__)


def sync_offline_submissions(
    db: Session,
    student_id: UUID,
    items: Sequence[Union[ImperialOfflineSubmissionItem, dict]],
) -> ImperialBatchSyncResponse:
    """Synchronize a batch of offline submissions idempotently.

    For each item:
    1. Validate activity exists and belongs to CONTENT_SCOPE_IMPERIAL.
    2. Check if an ImperialSubmission already exists for (activity_id, student_id).
    3. If exists:
       - If answer_text and evidence_refs match: acknowledge as idempotent duplicate.
       - If student edited their answer offline (newer or different content):
         update answer_text, evidence_refs, submitted_at, and updated_at.
    4. If not exists:
       - Create new ImperialSubmission with client_timestamp as submitted_at.
    5. Return per-item results and aggregate counts.
    """
    results: list[ImperialSyncItemResult] = []
    synced_count = 0
    failed_count = 0

    for raw_item in items:
        if isinstance(raw_item, dict):
            try:
                item = ImperialOfflineSubmissionItem.model_validate(raw_item)
            except Exception as exc:
                failed_count += 1
                results.append(
                    ImperialSyncItemResult(
                        client_id=str(raw_item.get("id", "unknown")),
                        server_id=None,
                        status="failed",
                        activity_id=None,
                        error=f"Invalid submission item format: {exc}",
                    )
                )
                continue
        else:
            item = raw_item

        client_id_str = str(item.id)
        activity_uuid = item.activity_id

        # 1. Validate activity exists
        try:
            activity = db.get(ImperialActivity, activity_uuid)
        except Exception as exc:
            activity = None

        if not activity or getattr(activity, "content_scope", None) != CONTENT_SCOPE_IMPERIAL:
            failed_count += 1
            results.append(
                ImperialSyncItemResult(
                    client_id=client_id_str,
                    server_id=None,
                    status="failed",
                    activity_id=activity_uuid,
                    error=f"Activity '{activity_uuid}' not found or invalid scope",
                )
            )
            continue

        # Validate answer text
        answer_text = str(item.answer_text).strip() if item.answer_text else ""
        if not answer_text:
            failed_count += 1
            results.append(
                ImperialSyncItemResult(
                    client_id=client_id_str,
                    server_id=None,
                    status="failed",
                    activity_id=activity_uuid,
                    error="Answer text must not be empty",
                )
            )
            continue

        # Client timestamp normalization
        submitted_at = item.client_timestamp
        if submitted_at.tzinfo is None:
            submitted_at = submitted_at.replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)

        evidence_refs = item.evidence_refs or []
        classroom_id = item.classroom_id

        try:
            # 2. Check for existing submission by this student for this activity
            stmt = (
                select(ImperialSubmission)
                .where(
                    ImperialSubmission.content_scope == CONTENT_SCOPE_IMPERIAL,
                    ImperialSubmission.activity_id == activity_uuid,
                    ImperialSubmission.student_id == student_id,
                )
                .order_by(ImperialSubmission.submitted_at.desc())
            )
            existing: ImperialSubmission | None = db.scalars(stmt).first()

            if existing is not None:
                # Compare content for idempotency
                content_matched = (
                    existing.answer_text.strip() == answer_text
                    and existing.evidence_refs == evidence_refs
                )
                if content_matched:
                    # Idempotent acknowledgment
                    synced_count += 1
                    results.append(
                        ImperialSyncItemResult(
                            client_id=client_id_str,
                            server_id=existing.id,
                            status="acknowledged",
                            activity_id=activity_uuid,
                            error=None,
                        )
                    )
                else:
                    # Student modified their submission offline or re-submitted
                    existing.answer_text = answer_text
                    existing.evidence_refs = evidence_refs
                    if classroom_id is not None:
                        existing.classroom_id = classroom_id
                    existing.submitted_at = submitted_at
                    existing.updated_at = now_utc
                    existing.row_version = (existing.row_version or 1) + 1
                    db.flush()

                    synced_count += 1
                    results.append(
                        ImperialSyncItemResult(
                            client_id=client_id_str,
                            server_id=existing.id,
                            status="updated",
                            activity_id=activity_uuid,
                            error=None,
                        )
                    )
            else:
                # 3. Create fresh submission
                new_sub = ImperialSubmission(
                    id=uuid4(),
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    activity_id=activity.id,
                    student_id=student_id,
                    classroom_id=classroom_id,
                    status="submitted",
                    answer_text=answer_text,
                    evidence_refs=evidence_refs,
                    score=None,
                    rubric_scores={},
                    feedback=None,
                    graded_by=None,
                    graded_at=None,
                    submitted_at=submitted_at,
                    updated_at=now_utc,
                    row_version=1,
                )
                db.add(new_sub)
                db.flush()

                synced_count += 1
                results.append(
                    ImperialSyncItemResult(
                        client_id=client_id_str,
                        server_id=new_sub.id,
                        status="synced",
                        activity_id=activity_uuid,
                        error=None,
                    )
                )

            db.commit()

        except Exception as exc:
            db.rollback()
            logger.exception("Error syncing offline submission item %s: %s", client_id_str, exc)
            failed_count += 1
            results.append(
                ImperialSyncItemResult(
                    client_id=client_id_str,
                    server_id=None,
                    status="failed",
                    activity_id=activity_uuid,
                    error=f"Database synchronization error: {exc}",
                )
            )

    return ImperialBatchSyncResponse(
        synced_count=synced_count,
        failed_count=failed_count,
        results=results,
    )
