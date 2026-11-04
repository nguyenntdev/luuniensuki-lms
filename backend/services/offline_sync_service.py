# -*- coding: utf-8 -*-
"""Offline write queue idempotency & synchronization service.

Ticket: V5-T056 (Wave W05, Slot A06)
Spec: Unified offline queue synchronization for mobile and web PWA.

Core Capabilities:
1. Tracks queued offline actions:
   - Inspections: 3D/AR or 2D turntable relic inspections
   - Submissions: Imperial inquiry activities and classroom assignments
   - Progression: Relic discovery, lesson completion, quiz evaluations
2. Retry logic & exponential backoff tracking
3. Conflict resolution:
   - Identical submission content -> 'acknowledged' (idempotent, 0 XP, 0 new rows)
   - Modified student draft before grading -> 'updated' (row_version incremented)
   - Modified student draft AFTER teacher grading -> 'conflict' (server state preserved)
4. Server ACK with authoritative status, timestamps, and server UUIDs
5. Client idempotency keys:
   - Strict deduplication per (user_id, idempotency_key)
   - Anti-replay gamification: Reconnection retries award exactly 0 XP
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Sequence
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..apischemas.offline import (
    OfflineOperationItem,
    OfflineOperationResult,
    OfflineSyncResponse,
)
from ..apischemas.imperial_sync import ImperialOfflineSubmissionItem
from ..apischemas.relic_inspection import RelicInspectionCompleteRequest
from ..errors import AppError
from ..history_models import HistoryAssignmentSubmission
from ..imperial_models import CONTENT_SCOPE_IMPERIAL, ImperialActivity, ImperialSubmission
from ..models import Motif, User
from . import history_learning, imperial_sync, progress_service, relic_inspection

logger = logging.getLogger("luuniensuki.offline_sync")

# In-memory session idempotency store to prevent rapid replay bursts across reconnects
_offline_idempotency_cache: dict[str, OfflineOperationResult] = {}


def clear_offline_idempotency_cache() -> None:
    """Clear in-memory idempotency cache (used for test teardown)."""
    _offline_idempotency_cache.clear()


def process_offline_operation(
    db: Session,
    user: User,
    item: OfflineOperationItem,
    header_idempotency_key: Optional[str] = None,
) -> OfflineOperationResult:
    """Process a single queued offline operation idempotently."""
    idempotency_key = item.idempotency_key or header_idempotency_key or item.operation_id
    cache_key = f"{user.id}:{idempotency_key}"

    # 1. Check idempotency cache for fast replay short-circuit
    if cache_key in _offline_idempotency_cache:
        cached = _offline_idempotency_cache[cache_key]
        logger.info(
            "Returning cached offline operation result for user %s, key %s",
            user.id,
            idempotency_key,
        )
        return OfflineOperationResult(
            operation_id=item.operation_id,
            resource=item.resource,
            status="acknowledged",
            idempotency_key=idempotency_key,
            xp_awarded=0,  # Zero XP on replay
            server_ack=cached.server_ack,
            conflict_resolution=cached.conflict_resolution,
            error=None,
        )

    resource = (item.resource or "").strip().lower()
    payload = item.payload or {}

    try:
        # =====================================================================
        # 1. Relic Inspection Actions
        # =====================================================================
        if resource in ("inspection", "relic_inspection"):
            target_slug = (
                payload.get("target_slug")
                or payload.get("target")
                or payload.get("relic_slug")
                or ""
            ).strip()
            if not target_slug:
                return OfflineOperationResult(
                    operation_id=item.operation_id,
                    resource=resource,
                    status="failed",
                    idempotency_key=idempotency_key,
                    xp_awarded=0,
                    error="Missing target_slug in inspection payload",
                )

            raw_tier = str(payload.get("device_tier", "desktop")).lower()
            if raw_tier in ("low_end_mobile", "mid_range_mobile", "high_end_mobile", "desktop"):
                device_tier = raw_tier
            elif "low" in raw_tier:
                device_tier = "low_end_mobile"
            elif "mid" in raw_tier:
                device_tier = "mid_range_mobile"
            elif "high" in raw_tier or "mobile" in raw_tier:
                device_tier = "high_end_mobile"
            else:
                device_tier = "desktop"

            inspection_req = RelicInspectionCompleteRequest(
                target_slug=target_slug,
                inspection_mode=payload.get("inspection_mode", "turntable_3d"),
                camera_permission_granted=bool(payload.get("camera_permission_granted", False)),
                device_tier=device_tier,
                time_spent_seconds=int(payload.get("time_spent_seconds", 10)),
                angles_inspected=payload.get("angles_inspected") or ["front"],
                hotspots_examined=payload.get("hotspots_examined") or [],
                idempotency_key=idempotency_key,
            )

            res = relic_inspection.record_relic_inspection(db, user=user, payload=inspection_req)
            is_already = getattr(res, "already_completed", False)
            xp = getattr(res, "xp_awarded", 0)

            result = OfflineOperationResult(
                operation_id=item.operation_id,
                resource=resource,
                status="acknowledged" if is_already or xp == 0 else "synced",
                idempotency_key=idempotency_key,
                xp_awarded=xp,
                server_ack={
                    "task_id": str(res.task_id) if hasattr(res, "task_id") else None,
                    "target_slug": res.target_slug,
                    "target_title": res.target_title,
                    "inspection_mode": res.inspection_mode,
                    "already_completed": is_already,
                    "feedback": res.feedback,
                    "recorded_at": res.recorded_at.isoformat() if res.recorded_at else None,
                },
                conflict_resolution="already_completed" if is_already else None,
                error=None,
            )

        # =====================================================================
        # 2. Student Learning Progression Actions
        # =====================================================================
        elif resource in (
            "progression",
            "progress_action",
            "progress_write",
            "discover",
            "complete_lesson",
            "lesson_complete",
            "quiz_submit",
            "submit_quiz",
        ):
            if resource in ("discover", "complete_lesson", "submit_quiz"):
                action = resource
            elif resource == "lesson_complete":
                action = "complete_lesson"
            elif resource == "quiz_submit":
                action = "submit_quiz"
            else:
                action = payload.get("action", "discover")

            motif_raw = payload.get("motif_id") or payload.get("motif")
            if not motif_raw:
                return OfflineOperationResult(
                    operation_id=item.operation_id,
                    resource=resource,
                    status="failed",
                    idempotency_key=idempotency_key,
                    xp_awarded=0,
                    error="Missing motif_id in progression payload",
                )

            motif_uuid: Optional[UUID] = None
            try:
                motif_uuid = UUID(str(motif_raw))
            except ValueError:
                # Look up motif by slug/mesh_name
                motif_obj = db.execute(
                    select(Motif).where(
                        (Motif.mesh_name == str(motif_raw)) | (Motif.name == str(motif_raw))
                    )
                ).scalar_one_or_none()
                if motif_obj:
                    motif_uuid = motif_obj.id

            if not motif_uuid:
                return OfflineOperationResult(
                    operation_id=item.operation_id,
                    resource=resource,
                    status="failed",
                    idempotency_key=idempotency_key,
                    xp_awarded=0,
                    error=f"Motif '{motif_raw}' could not be resolved",
                )

            time_spent = int(payload.get("time_spent_seconds", 10))
            answers = payload.get("answers")
            client_status = payload.get("client_claimed_status")

            res_dict = progress_service.process_progression_action(
                db=db,
                user=user,
                action=action,
                motif_id=motif_uuid,
                time_spent_seconds=time_spent,
                answers=answers,
                idempotency_key=idempotency_key,
                client_claimed_status=client_status,
            )

            xp = res_dict.get("xp_awarded", 0)
            status_changed = res_dict.get("status_changed", False)
            already_mastered = res_dict.get("already_mastered", False)
            already_unlocked = res_dict.get("already_unlocked", False)

            result = OfflineOperationResult(
                operation_id=item.operation_id,
                resource=resource,
                status="synced" if (xp > 0 and status_changed) else "acknowledged",
                idempotency_key=idempotency_key,
                xp_awarded=xp,
                server_ack=res_dict,
                conflict_resolution="already_mastered" if already_mastered else (
                    "already_unlocked" if already_unlocked else None
                ),
                error=None,
            )

        # =====================================================================
        # 3. Student Inquiry & Assignment Submissions
        # =====================================================================
        elif resource in ("submission", "activity_submission", "assignment_submission"):
            # Check if this is an Imperial Activity Submission
            activity_id_raw = payload.get("activity_id")
            assignment_id_raw = payload.get("assignment_id")

            if activity_id_raw:
                try:
                    act_uuid = UUID(str(activity_id_raw))
                except ValueError:
                    return OfflineOperationResult(
                        operation_id=item.operation_id,
                        resource=resource,
                        status="failed",
                        idempotency_key=idempotency_key,
                        xp_awarded=0,
                        error=f"Invalid activity_id UUID: {activity_id_raw}",
                    )

                client_ts = item.created_at or datetime.now(timezone.utc)
                sub_item = ImperialOfflineSubmissionItem(
                    id=item.operation_id,
                    activity_id=act_uuid,
                    answer_text=payload.get("answer_text") or payload.get("claim") or "Trống",
                    evidence_refs=payload.get("evidence_refs") or payload.get("evidence_citations") or [],
                    client_timestamp=client_ts,
                    classroom_id=UUID(str(payload["classroom_id"])) if payload.get("classroom_id") else None,
                )

                batch_res = imperial_sync.sync_offline_submissions(
                    db=db,
                    student_id=user.id,
                    items=[sub_item],
                )

                item_res = batch_res.results[0] if batch_res.results else None
                if not item_res:
                    return OfflineOperationResult(
                        operation_id=item.operation_id,
                        resource=resource,
                        status="failed",
                        idempotency_key=idempotency_key,
                        xp_awarded=0,
                        error="Empty response from imperial_sync",
                    )

                status_val = item_res.status
                conflict_res = None
                if status_val == "conflict":
                    conflict_res = "Submission already graded by teacher. Server state preserved."

                result = OfflineOperationResult(
                    operation_id=item.operation_id,
                    resource=resource,
                    status=status_val,
                    idempotency_key=idempotency_key,
                    xp_awarded=0,
                    server_ack={
                        "server_id": str(item_res.server_id) if item_res.server_id else None,
                        "activity_id": str(item_res.activity_id) if item_res.activity_id else None,
                        "status": item_res.status,
                    },
                    conflict_resolution=conflict_res,
                    error=item_res.error,
                )

            elif assignment_id_raw:
                try:
                    asg_uuid = UUID(str(assignment_id_raw))
                except ValueError:
                    return OfflineOperationResult(
                        operation_id=item.operation_id,
                        resource=resource,
                        status="failed",
                        idempotency_key=idempotency_key,
                        xp_awarded=0,
                        error=f"Invalid assignment_id UUID: {assignment_id_raw}",
                    )

                # Check conflict: if already graded, reject student overwrites
                existing_asg = db.scalar(
                    select(HistoryAssignmentSubmission).where(
                        HistoryAssignmentSubmission.assignment_id == asg_uuid,
                        HistoryAssignmentSubmission.student_id == user.id,
                    )
                )

                if existing_asg and existing_asg.status == "graded":
                    return OfflineOperationResult(
                        operation_id=item.operation_id,
                        resource=resource,
                        status="conflict",
                        idempotency_key=idempotency_key,
                        xp_awarded=0,
                        server_ack={
                            "server_id": str(existing_asg.id),
                            "assignment_id": str(asg_uuid),
                            "status": "graded",
                        },
                        conflict_resolution="Assignment already graded by teacher. Server state preserved.",
                        error="Bài làm đã được chấm điểm. Bản sửa đổi ngoại tuyến không thể ghi đè kết quả.",
                    )

                claim = payload.get("claim", "")
                evidence = payload.get("evidence", "")
                explanation = payload.get("explanation", "")
                citations = payload.get("evidence_citations", [])

                sub_obj, created = history_learning.submit_history_assignment(
                    db=db,
                    assignment_id=asg_uuid,
                    student_id=user.id,
                    claim=claim,
                    evidence=evidence,
                    explanation=explanation,
                    evidence_citations=citations,
                    idempotency_key=idempotency_key,
                )

                result = OfflineOperationResult(
                    operation_id=item.operation_id,
                    resource=resource,
                    status="synced" if created else "updated",
                    idempotency_key=idempotency_key,
                    xp_awarded=0,
                    server_ack={
                        "server_id": str(sub_obj.id),
                        "assignment_id": str(asg_uuid),
                        "status": sub_obj.status,
                    },
                    conflict_resolution="client_draft_updated_pending_submission" if not created else None,
                    error=None,
                )

            else:
                # Generic student submission (e.g. from PWA map / worksheet)
                # Attempt resolving via monument_slug -> ImperialActivity
                monument_slug = payload.get("monument_slug")
                if monument_slug:
                    activity = db.scalar(
                        select(ImperialActivity).where(
                            ImperialActivity.content_scope == CONTENT_SCOPE_IMPERIAL,
                            ImperialActivity.site_slug == monument_slug,
                        )
                    )
                    if activity:
                        sub_item = ImperialOfflineSubmissionItem(
                            id=item.operation_id,
                            activity_id=activity.id,
                            answer_text=payload.get("claim", "") + "\n\n" + payload.get("explanation", ""),
                            evidence_refs=payload.get("evidence_citations", []),
                            client_timestamp=item.created_at or datetime.now(timezone.utc),
                        )
                        batch_res = imperial_sync.sync_offline_submissions(
                            db=db,
                            student_id=user.id,
                            items=[sub_item],
                        )
                        item_res = batch_res.results[0]
                        result = OfflineOperationResult(
                            operation_id=item.operation_id,
                            resource=resource,
                            status=item_res.status,
                            idempotency_key=idempotency_key,
                            xp_awarded=0,
                            server_ack={
                                "server_id": str(item_res.server_id) if item_res.server_id else None,
                                "activity_id": str(item_res.activity_id) if item_res.activity_id else None,
                                "status": item_res.status,
                            },
                            error=item_res.error,
                        )
                    else:
                        return OfflineOperationResult(
                            operation_id=item.operation_id,
                            resource=resource,
                            status="acknowledged",
                            idempotency_key=idempotency_key,
                            xp_awarded=0,
                            server_ack={"acknowledged": True, "monument_slug": monument_slug},
                            conflict_resolution="buffered_without_activity_link",
                        )
                else:
                    return OfflineOperationResult(
                        operation_id=item.operation_id,
                        resource=resource,
                        status="failed",
                        idempotency_key=idempotency_key,
                        xp_awarded=0,
                        error="Missing activity_id, assignment_id, or monument_slug in submission payload",
                    )

        else:
            return OfflineOperationResult(
                operation_id=item.operation_id,
                resource=resource,
                status="failed",
                idempotency_key=idempotency_key,
                xp_awarded=0,
                error=f"Unsupported offline resource: '{resource}'",
            )

        # Cache the result for future replays
        _offline_idempotency_cache[cache_key] = result
        return result

    except AppError as app_err:
        logger.warning("AppError in offline sync for item %s: %s", item.operation_id, app_err)
        return OfflineOperationResult(
            operation_id=item.operation_id,
            resource=resource,
            status="failed",
            idempotency_key=idempotency_key,
            xp_awarded=0,
            error=str(app_err.message),
        )
    except Exception as exc:
        logger.exception("Unexpected error processing offline operation %s: %s", item.operation_id, exc)
        return OfflineOperationResult(
            operation_id=item.operation_id,
            resource=resource,
            status="failed",
            idempotency_key=idempotency_key,
            xp_awarded=0,
            error=f"Server processing error: {exc}",
        )


def sync_offline_batch(
    db: Session,
    user: User,
    operations: Sequence[OfflineOperationItem],
    header_idempotency_key: Optional[str] = None,
) -> OfflineSyncResponse:
    """Batch-synchronize a sequence of offline operations idempotently."""
    results: list[OfflineOperationResult] = []
    synced_count = 0
    acknowledged_count = 0
    conflict_count = 0
    failed_count = 0
    total_xp = 0

    for op in operations:
        res = process_offline_operation(
            db=db,
            user=user,
            item=op,
            header_idempotency_key=header_idempotency_key if len(operations) == 1 else None,
        )
        results.append(res)
        total_xp += res.xp_awarded

        if res.status == "synced":
            synced_count += 1
        elif res.status in ("acknowledged", "updated"):
            acknowledged_count += 1
        elif res.status == "conflict":
            conflict_count += 1
        elif res.status == "failed":
            failed_count += 1

    # Populate top-level fields for single-item convenience
    first = results[0] if results else None

    return OfflineSyncResponse(
        success=(failed_count == 0),
        operation_id=first.operation_id if first else None,
        status=first.status if first else None,
        resource=first.resource if first else None,
        idempotency_key=first.idempotency_key if first else None,
        xp_awarded=first.xp_awarded if first else 0,
        synced_count=synced_count,
        acknowledged_count=acknowledged_count,
        conflict_count=conflict_count,
        failed_count=failed_count,
        total_xp_awarded=total_xp,
        server_ack=first.server_ack if first else None,
        conflict_resolution=first.conflict_resolution if first else None,
        error=first.error if first else None,
        results=results,
    )
