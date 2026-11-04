# -*- coding: utf-8 -*-
"""Relic inspection service (V5-T045: AR fallback & device capability checks).

Guarantees:
1. Equivalent learning task: Denied camera permission (or 2D turntable fallback)
   grants the exact same completion, same XP (25 XP), and equivalent progress.
2. Anti-replay & idempotency: Repeated submissions on the same target or with the same
   idempotency key return 0 XP and mark already_completed=True.
3. Quality gates: Rejects superficial clicks (< 3s duration or 0 angles/hotspots viewed).
4. Guest isolation: Guests can only inspect demo content.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..apischemas.relic_inspection import (
    RelicInspectionCompleteRequest,
    RelicInspectionCompleteResponse,
    RelicInspectionStatusResponse,
)
from ..domain.gamification import _update_streak
from ..domain.helpers import DISCOVERY_XP
from ..errors import AppError
from ..imperial_models import CONTENT_SCOPE_IMPERIAL, ImperialSite
from ..imperial_v51_models import ImperialArtDetail, ImperialRelicInspection
from ..models import Motif, UnlockStatus, Urn, User, UserProgress, UserRole

logger = logging.getLogger("luuniensuki.api")

MIN_INSPECTION_SECONDS = 3
INSPECTION_XP = DISCOVERY_XP  # 25 XP


def resolve_inspection_target(
    db: Session, target_slug: str
) -> tuple[str, bool, Optional[Motif]]:
    """Resolve a target slug against known art details, urns, sites, or motifs.

    Returns:
        (title, is_demo, motif_or_none)
    """
    clean_slug = (target_slug or "").strip().lower()

    # 1. Check ImperialArtDetail
    art_detail = db.execute(
        select(ImperialArtDetail).where(
            ImperialArtDetail.slug == clean_slug,
            ImperialArtDetail.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
    ).scalar_one_or_none()
    if art_detail:
        return art_detail.title, True, None

    # 2. Check Urn
    urn = db.execute(
        select(Urn).where(Urn.slug == clean_slug)
    ).scalar_one_or_none()
    if urn:
        return urn.name, urn.is_active, None

    # 3. Check Motif
    # Try exact slug match or by name/mesh_name
    motif = db.execute(
        select(Motif).where(
            or_(
                Motif.mesh_name == clean_slug,
                Motif.name == target_slug,
            )
        )
    ).scalars().first()
    if not motif and "-" in clean_slug:
        # Check if relief slug pattern e.g. cao-dinh-01
        parts = clean_slug.split("-")
        if len(parts) >= 2:
            motif = db.execute(
                select(Motif).where(Motif.mesh_name.ilike(f"%{clean_slug}%"))
            ).scalars().first()

    if motif:
        return motif.name, bool(motif.is_demo), motif

    # 4. Check ImperialSite
    site = db.execute(
        select(ImperialSite).where(
            ImperialSite.slug == clean_slug,
            ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
    ).scalar_one_or_none()
    if site:
        return site.name_vi, True, None

    # Default fallback for known urn slugs
    known_urns = {
        "cao-dinh": "Cao Đỉnh",
        "nhan-dinh": "Nhân Đỉnh",
        "chuong-dinh": "Chương Đỉnh",
        "anh-dinh": "Anh Đỉnh",
        "nghi-dinh": "Nghị Đỉnh",
        "thuan-dinh": "Thuần Đỉnh",
        "tuyen-dinh": "Tuyên Đỉnh",
        "du-dinh": "Dụ Đỉnh",
        "huyen-dinh": "Huyền Đỉnh",
    }
    if clean_slug in known_urns:
        return known_urns[clean_slug], True, None

    raise AppError(
        "TARGET_NOT_FOUND",
        f"Heritage relic or inspection target '{target_slug}' was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def record_relic_inspection(
    db: Session,
    user: User,
    payload: RelicInspectionCompleteRequest,
) -> RelicInspectionCompleteResponse:
    """Record an inspection session and award equivalent learning completion.

    CRITICAL INVARIANT (V5-T045):
    A learner who denies camera permission or uses 2D turntable fallback MUST receive
    the exact same XP, server completion, and pedagogical feedback as an AR user.
    """
    target_slug = payload.target_slug.strip().lower()

    # 1. Target resolution & guest guardrail
    target_title, is_demo, motif = resolve_inspection_target(db, target_slug)
    if user.role == UserRole.guest and not is_demo:
        raise AppError(
            "FORBIDDEN_GUEST_ACCESS",
            "Tài khoản khách chỉ được phép quan sát các hiện vật trải nghiệm thử (Demo).",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 2. Quality gate: Duration check (minimum 3 seconds)
    if payload.time_spent_seconds < MIN_INSPECTION_SECONDS:
        raise AppError(
            "INSUFFICIENT_INSPECTION_TIME",
            f"Thời gian quan sát hiện vật chưa đủ ({payload.time_spent_seconds}s). Vui lòng quan sát tối thiểu {MIN_INSPECTION_SECONDS} giây để nắm bắt chi tiết.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Quality gate: Interaction check (must inspect at least one angle or hotspot)
    if not payload.angles_inspected and not payload.hotspots_examined:
        raise AppError(
            "INCOMPLETE_INSPECTION_TASK",
            "Nhiệm vụ quan sát yêu cầu bạn xoay hiện vật hoặc kiểm tra ít nhất một góc nhìn / điểm chi tiết.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    now = datetime.now(timezone.utc)

    # 4. Check idempotency key if provided
    if payload.idempotency_key:
        existing_by_key = db.execute(
            select(ImperialRelicInspection).where(
                ImperialRelicInspection.idempotency_key == payload.idempotency_key
            )
        ).scalar_one_or_none()
        if existing_by_key:
            return RelicInspectionCompleteResponse(
                success=True,
                task_id=existing_by_key.id,
                target_slug=existing_by_key.target_slug,
                target_title=target_title,
                inspection_mode=existing_by_key.inspection_mode,
                camera_permission_granted=existing_by_key.camera_permission_granted,
                equivalent_learning_completed=True,
                xp_awarded=0,
                total_xp=user.total_xp,
                already_completed=True,
                feedback="Nhiệm vụ quan sát đã được ghi nhận trước đó (Idempotent).",
                recorded_at=existing_by_key.created_at,
            )

    # 5. Check if user already completed inspection on this target (Anti-replay)
    existing_inspection = db.execute(
        select(ImperialRelicInspection).where(
            ImperialRelicInspection.user_id == user.id,
            ImperialRelicInspection.target_slug == target_slug,
        )
    ).scalar_one_or_none()

    if existing_inspection:
        return RelicInspectionCompleteResponse(
            success=True,
            task_id=existing_inspection.id,
            target_slug=existing_inspection.target_slug,
            target_title=target_title,
            inspection_mode=existing_inspection.inspection_mode,
            camera_permission_granted=existing_inspection.camera_permission_granted,
            equivalent_learning_completed=True,
            xp_awarded=0,
            total_xp=user.total_xp,
            already_completed=True,
            feedback="Bạn đã hoàn thành khảo sát hiện vật này trước đó. Điểm kinh nghiệm không cộng dồn.",
            recorded_at=existing_inspection.created_at,
        )

    # 6. Create new inspection record
    xp_to_award = INSPECTION_XP
    user.total_xp += xp_to_award
    _update_streak(user, now)
    user.last_active_at = now

    inspection_record = ImperialRelicInspection(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        user_id=user.id,
        target_slug=target_slug,
        inspection_mode=payload.inspection_mode,
        camera_permission_granted=payload.camera_permission_granted,
        device_tier=payload.device_tier or "desktop",
        time_spent_seconds=payload.time_spent_seconds,
        angles_inspected=payload.angles_inspected,
        hotspots_examined=payload.hotspots_examined,
        xp_awarded=xp_to_award,
        idempotency_key=payload.idempotency_key,
        created_at=now,
        updated_at=now,
    )
    db.add(inspection_record)

    # 7. If target is a Motif, synchronize with UserProgress table (hidden -> discovered)
    if motif:
        progress = db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id,
                UserProgress.motif_id == motif.id,
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserProgress(
                user_id=user.id,
                motif_id=motif.id,
                status=UnlockStatus.discovered,
                discovered_at=now,
                xp_earned=xp_to_award,
            )
            db.add(progress)
        elif progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = now
            progress.xp_earned = max(progress.xp_earned, xp_to_award)

    db.commit()
    db.refresh(inspection_record)

    # Dynamic respectful feedback message
    mode_text = (
        "Thực tế tăng cường (WebXR AR)"
        if payload.inspection_mode == "webxr_ar"
        else "Mâm xoay 360° & Bản rập 2D"
    )
    feedback_msg = (
        f"Hoàn thành xuất sắc nhiệm vụ khảo sát {target_title} qua chế độ {mode_text}! "
        f"Bạn được cộng +{xp_to_award} XP vào hồ sơ học tập."
    )

    return RelicInspectionCompleteResponse(
        success=True,
        task_id=inspection_record.id,
        target_slug=target_slug,
        target_title=target_title,
        inspection_mode=payload.inspection_mode,
        camera_permission_granted=payload.camera_permission_granted,
        equivalent_learning_completed=True,
        xp_awarded=xp_to_award,
        total_xp=user.total_xp,
        already_completed=False,
        feedback=feedback_msg,
        recorded_at=inspection_record.created_at,
    )


def get_relic_inspection_status(
    db: Session,
    user: User,
    target_slug: str,
) -> RelicInspectionStatusResponse:
    """Check whether a user has already inspected a relic."""
    clean_slug = (target_slug or "").strip().lower()
    existing = db.execute(
        select(ImperialRelicInspection).where(
            ImperialRelicInspection.user_id == user.id,
            ImperialRelicInspection.target_slug == clean_slug,
        )
    ).scalar_one_or_none()

    if existing:
        return RelicInspectionStatusResponse(
            target_slug=clean_slug,
            is_completed=True,
            completed_mode=existing.inspection_mode,
            camera_permission_granted=existing.camera_permission_granted,
            xp_earned=existing.xp_awarded,
            completed_at=existing.created_at,
        )

    return RelicInspectionStatusResponse(
        target_slug=clean_slug,
        is_completed=False,
        completed_mode=None,
        camera_permission_granted=None,
        xp_earned=0,
        completed_at=None,
    )
