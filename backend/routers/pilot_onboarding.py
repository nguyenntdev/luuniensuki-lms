# -*- coding: utf-8 -*-
"""API router for Pilot Onboarding Portal (Ticket V5-T116 / Wave W11 Slot A06).

Endpoints:
- POST /api/v1/pilot/invitations (Admin/Staff: generate invitation token)
- GET  /api/v1/pilot/invitations (Admin/Staff: list invitations)
- POST /api/v1/pilot/invitations/validate (Public/Authenticated: check token validity)
- POST /api/v1/pilot/activate (Authenticated: redeem token and join private pilot)
- GET  /api/v1/pilot/my-activation (Authenticated: get current pilot status & checklist)
- POST /api/v1/pilot/onboarding/step (Authenticated: record checklist progress)
- GET  /api/v1/pilot/health (Authenticated: get usage health & telemetry score)
- POST /api/v1/pilot/telemetry (Authenticated: log pilot usage action)
- POST /api/v1/pilot/support (Authenticated: create pilot support / feedback ticket)
- GET  /api/v1/pilot/support (Authenticated: list user or staff pilot tickets)
- POST /api/v1/pilot/support/{id}/reply (Authenticated: add response to pilot ticket)
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..apischemas.pilot_onboarding import (
    PilotActivateIn,
    PilotActivationOut,
    PilotHealthTelemetryRecordIn,
    PilotInvitationCreateIn,
    PilotInvitationOut,
    PilotInvitationValidationResult,
    PilotOnboardingStepIn,
    PilotSupportRequestCreateIn,
    PilotSupportRequestOut,
    PilotSupportRequestReplyIn,
    PilotUsageHealthOut,
    PilotValidateInvitationIn,
)
from ..db import get_db
from ..deps import get_current_user, get_staff_user
from ..errors import AppError
from ..models import (
    PilotInvitation,
    PilotParticipantActivation,
    PilotSupportRequest,
    PilotUsageHealth,
    User,
    UserRole,
)
from ..services import pilot_onboarding as pilot_service

router = APIRouter(prefix="/api/v1/pilot", tags=["pilot_onboarding_portal"])


@router.post(
    "/invitations",
    response_model=PilotInvitationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation_endpoint(
    payload: PilotInvitationCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Staff generates a secure pilot invitation token."""
    invitation, raw_token = pilot_service.generate_pilot_invitation(
        db=db,
        pilot_name=payload.pilot_name,
        target_role=payload.target_role,
        organization_name=payload.organization_name,
        contact_email=payload.contact_email,
        invited_by=current_user,
        school_id=payload.school_id,
        partner_id=payload.partner_id,
        max_uses=payload.max_uses,
        expires_in_days=payload.expires_in_days,
        notes=payload.notes,
        metadata_payload=payload.metadata_payload,
    )
    result = PilotInvitationOut.model_validate(invitation)
    result.invitation_token = raw_token
    return result


@router.get("/invitations", response_model=List[PilotInvitationOut])
def list_invitations_endpoint(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Staff lists all pilot invitations."""
    invitations = db.execute(
        select(PilotInvitation).order_by(desc(PilotInvitation.created_at))
    ).scalars().all()
    return invitations


@router.post("/invitations/validate", response_model=PilotInvitationValidationResult)
def validate_invitation_endpoint(
    payload: PilotValidateInvitationIn,
    db: Session = Depends(get_db),
):
    """Check whether a pilot invitation token is valid before redemption."""
    is_valid, reason, invitation = pilot_service.validate_invitation_token(
        db, payload.token
    )
    if not is_valid or not invitation:
        msg_map = {
            "invalid": "Token thư mời không hợp lệ.",
            "expired": "Thư mời đã hết hạn tham gia thử nghiệm.",
            "exhausted": "Thư mời đã đạt giới hạn số lượt kích hoạt.",
            "revoked": "Thư mời đã bị quản trị viên thu hồi.",
        }
        return PilotInvitationValidationResult(
            is_valid=False,
            status=reason,
            message=msg_map.get(reason, "Thư mời không hợp lệ."),
            invitation_code=invitation.invitation_code if invitation else None,
            pilot_name=invitation.pilot_name if invitation else None,
        )

    return PilotInvitationValidationResult(
        is_valid=True,
        status="valid",
        message="Thư mời hợp lệ và sẵn sàng kích hoạt.",
        invitation_code=invitation.invitation_code,
        pilot_name=invitation.pilot_name,
        target_role=invitation.target_role,
        organization_name=invitation.organization_name,
        expires_at=invitation.expires_at,
    )


@router.post("/activate", response_model=PilotActivationOut)
def activate_pilot_endpoint(
    payload: PilotActivateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Authenticated user redeems an invitation token to activate private pilot access."""
    activation = pilot_service.activate_pilot_participant(
        db=db,
        user=current_user,
        raw_token=payload.token,
        compliance_accepted=payload.compliance_accepted,
    )
    invitation = db.get(PilotInvitation, activation.invitation_id)
    out = PilotActivationOut.model_validate(activation)
    out.pilot_name = invitation.pilot_name if invitation else None
    return out


@router.get("/my-activation", response_model=PilotActivationOut)
def get_my_activation_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get active pilot trial activation and guided checklist progress."""
    activation = pilot_service.get_user_activation(db, current_user)
    if not activation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bạn chưa tham gia đợt thử nghiệm (pilot) nào.",
        )
    invitation = db.get(PilotInvitation, activation.invitation_id)
    out = PilotActivationOut.model_validate(activation)
    out.pilot_name = invitation.pilot_name if invitation else None
    return out


@router.post("/onboarding/step", response_model=PilotActivationOut)
def record_onboarding_step_endpoint(
    payload: PilotOnboardingStepIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record completion of a guided activation checklist step."""
    activation = pilot_service.record_onboarding_step(
        db=db,
        user=current_user,
        step=payload.step,
        completed=payload.completed,
    )
    invitation = db.get(PilotInvitation, activation.invitation_id)
    out = PilotActivationOut.model_validate(activation)
    out.pilot_name = invitation.pilot_name if invitation else None
    return out


@router.get("/health", response_model=PilotUsageHealthOut)
def get_pilot_health_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve usage health, engagement telemetry, and score for current pilot user."""
    activation = pilot_service.get_user_activation(db, current_user)
    if not activation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài khoản chưa có đợt thử nghiệm đang hoạt động.",
        )
    health = db.execute(
        select(PilotUsageHealth).where(PilotUsageHealth.user_id == current_user.id)
    ).scalar_one_or_none()
    if not health:
        health = pilot_service.record_usage_telemetry(
            db, current_user, "health_inquiry", {}
        )
    return health


@router.post("/telemetry", response_model=PilotUsageHealthOut)
def record_telemetry_endpoint(
    payload: PilotHealthTelemetryRecordIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log an interaction action to maintain pilot usage health."""
    health = pilot_service.record_usage_telemetry(
        db=db,
        user=current_user,
        action_name=payload.action_name,
        details=payload.details,
    )
    return health


@router.post(
    "/support",
    response_model=PilotSupportRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def create_support_request_endpoint(
    payload: PilotSupportRequestCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a pilot feedback or support ticket."""
    return pilot_service.create_pilot_support_request(
        db=db,
        user=current_user,
        category=payload.category,
        priority=payload.priority,
        subject=payload.subject,
        message=payload.message,
    )


@router.get("/support", response_model=List[PilotSupportRequestOut])
def list_support_requests_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List pilot support tickets. Staff sees all, participants see their own."""
    is_staff = current_user.role in (UserRole.admin, UserRole.super_admin)
    stmt = select(PilotSupportRequest)
    if not is_staff:
        stmt = stmt.where(PilotSupportRequest.user_id == current_user.id)
    stmt = stmt.order_by(desc(PilotSupportRequest.created_at))
    return db.execute(stmt).scalars().all()


@router.post("/support/{ticket_id}/reply", response_model=PilotSupportRequestOut)
def reply_support_request_endpoint(
    ticket_id: UUID,
    payload: PilotSupportRequestReplyIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a response to a pilot support ticket."""
    return pilot_service.reply_pilot_support_request(
        db=db,
        ticket_id=ticket_id,
        user=current_user,
        message=payload.message,
    )
