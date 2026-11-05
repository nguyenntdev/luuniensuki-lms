# -*- coding: utf-8 -*-
"""Progress API router for student learning progression.

Exposes:
- GET /api/v1/progress/summary
- GET /api/v1/progress/motifs/{motif_id}
- POST /api/v1/progress/action (unified with rate-limiting, anti-replay, and anti-abuse)
- POST /api/v1/progress/discover
- POST /api/v1/progress/complete-lesson
- POST /api/v1/progress/submit-quiz
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..apischemas.progress import (
    ClassroomPassportAnalyticsOut,
    MotifProgressionItem,
    PassportCheckInRequest,
    PassportCheckInResponse,
    PassportVerificationRequest,
    PassportVerificationResponse,
    ProgressionActionRequest,
    ProgressionActionResponse,
    StudentProgressionSummaryOut,
    VerifiedPassportOut,
)
from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services import heritage_passport, progress_service

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


@router.get("/summary", response_model=StudentProgressionSummaryOut)
def get_progression_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProgressionSummaryOut:
    """Retrieve full student learning progression summary."""
    return progress_service.get_student_progression_summary(db, current_user)


@router.get("/motifs/{motif_id}", response_model=MotifProgressionItem)
def get_motif_progress(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MotifProgressionItem:
    """Retrieve individual motif progression."""
    return progress_service.get_motif_progression_detail(db, current_user, motif_id)


@router.post("/action", response_model=ProgressionActionResponse)
def handle_progression_action(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Process a server-verified progression action (discover, complete_lesson, submit_quiz)."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action=payload.action,
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        answers=payload.answers,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


@router.post("/discover", response_model=ProgressionActionResponse)
def discover_motif(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Record genuine discovery (hotspot / 3D exploration)."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action="discover",
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


@router.post("/complete-lesson", response_model=ProgressionActionResponse)
def complete_lesson_action(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Record verified lesson completion."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action="complete_lesson",
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


@router.post("/submit-quiz", response_model=ProgressionActionResponse)
def submit_quiz_action(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Record quiz submission and evaluate mastery."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action="submit_quiz",
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        answers=payload.answers,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


# --------------------------------------------------------------------------- #
# Verified Heritage Passport & QR Provenance Endpoints (V5-T092 / W09-A02)
# --------------------------------------------------------------------------- #


@router.post("/passport/check-in", response_model=PassportCheckInResponse)
def handle_passport_checkin(
    payload: PassportCheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PassportCheckInResponse:
    """Process a server-authenticated physical or authorized site visit check-in.

    Invariants:
    - Visit stamp != assessed mastery. A visit stamp records presence, NOT curriculum mastery.
    - QR code provenance is verified cryptographically (HMAC-SHA256).
    - Client-claimed status parameters are strictly ignored.
    """
    res = heritage_passport.process_server_checkin(
        db=db,
        user=current_user,
        site_slug=payload.site_slug,
        verification_method=payload.verification_method,
        qr_token=payload.qr_token,
        qr_payload=payload.qr_payload,
        latitude=payload.latitude,
        longitude=payload.longitude,
        device_metadata=payload.device_metadata,
        client_claimed_status=payload.client_claimed_status,
    )
    return PassportCheckInResponse(**res)


@router.post("/passport/verify-qr", response_model=PassportVerificationResponse)
def verify_passport_qr_token(
    payload: PassportVerificationRequest,
    current_user: User = Depends(get_current_user),
) -> PassportVerificationResponse:
    """Verify cryptographic provenance and authenticity of a heritage QR code token."""
    res = heritage_passport.verify_qr_token(
        qr_token=payload.qr_token,
        expected_site=payload.site_slug,
    )
    return PassportVerificationResponse(**res)


@router.get("/passport", response_model=VerifiedPassportOut)
def get_verified_passport_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerifiedPassportOut:
    """Retrieve current student's server-verified heritage passport and distinct mastery status."""
    res = heritage_passport.get_verified_passport(db=db, user=current_user)
    return VerifiedPassportOut(**res)


@router.get(
    "/passport/classroom/{classroom_id}",
    response_model=ClassroomPassportAnalyticsOut,
)
def get_classroom_passport_analytics(
    classroom_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClassroomPassportAnalyticsOut:
    """Retrieve teacher analytics for verified passport stamps across a classroom.

    Invariant:
    Fake local/client completion is strictly excluded. Only server-verified
    stamps in heritage_passport_stamps are aggregated.
    """
    res = heritage_passport.get_teacher_classroom_passport_analytics(
        db=db,
        classroom_id=classroom_id,
        current_user=current_user,
    )
    return ClassroomPassportAnalyticsOut(**res)

