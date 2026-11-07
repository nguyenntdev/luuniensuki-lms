# -*- coding: utf-8 -*-
"""Business logic services for Pilot Onboarding Portal (Ticket V5-T116 / Wave W11 Slot A06)."""
from __future__ import annotations

import datetime
import hashlib
import secrets
from typing import Any, Optional
import uuid

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import (
    PilotInvitation,
    PilotParticipantActivation,
    PilotSupportRequest,
    PilotUsageHealth,
    School,
    SchoolMember,
    User,
    UserRole,
)
from ..models_rbpc import RbpcCreator


PILOT_STEP_CHECKLIST = {
    "school_teacher": [
        "welcome",
        "curriculum_alignment",
        "interactive_lesson_wizard",
        "printable_kit_review",
        "first_class_roster",
        "rubric_grading_practice",
        "activation_complete",
    ],
    "artisan_partner": [
        "welcome",
        "identity_rights_review",
        "artisan_profile_setup",
        "experience_drafting",
        "availability_calendar_setup",
        "oral_history_consent_tour",
        "activation_complete",
    ],
}


def _hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of raw invitation token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def generate_pilot_invitation(
    db: Session,
    pilot_name: str,
    target_role: str,
    organization_name: str,
    contact_email: str,
    invited_by: User,
    school_id: Optional[uuid.UUID] = None,
    partner_id: Optional[uuid.UUID] = None,
    max_uses: int = 1,
    expires_in_days: int = 30,
    notes: Optional[str] = None,
    metadata_payload: Optional[dict[str, Any]] = None,
) -> tuple[PilotInvitation, str]:
    """Staff generates a secure pilot invitation token."""
    if target_role not in ("school_teacher", "artisan_partner"):
        raise AppError(
            code="INVALID_TARGET_ROLE",
            message="Target role must be either 'school_teacher' or 'artisan_partner'.",
            status_code=400,
        )

    # Secure 32-byte secret token
    raw_token = f"ln_pilot_{secrets.token_urlsafe(32)}"
    token_hash = _hash_token(raw_token)
    invitation_code = f"PILOT-{target_role[:3].upper()}-{secrets.token_hex(4).upper()}"

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(days=expires_in_days)

    invitation = PilotInvitation(
        id=uuid.uuid4(),
        invitation_code=invitation_code,
        token_hash=token_hash,
        pilot_name=pilot_name,
        target_role=target_role,
        organization_name=organization_name,
        contact_email=contact_email,
        school_id=school_id,
        partner_id=partner_id,
        max_uses=max_uses,
        used_count=0,
        status="active",
        invited_by_id=invited_by.id,
        expires_at=expires_at,
        notes=notes,
        metadata_payload=metadata_payload or {},
        created_at=now,
        updated_at=now,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return invitation, raw_token


def validate_invitation_token(
    db: Session, raw_token: str
) -> tuple[bool, str, Optional[PilotInvitation]]:
    """Validate raw token against stored hash, expiry, usage count and status."""
    token_hash = _hash_token(raw_token)
    stmt = select(PilotInvitation).where(PilotInvitation.token_hash == token_hash)
    invitation = db.execute(stmt).scalar_one_or_none()

    if not invitation:
        return False, "invalid", None

    now = datetime.datetime.now(datetime.timezone.utc)
    if invitation.status == "revoked":
        return False, "revoked", invitation

    if invitation.expires_at <= now:
        if invitation.status != "expired":
            invitation.status = "expired"
            db.commit()
        return False, "expired", invitation

    if invitation.used_count >= invitation.max_uses:
        if invitation.status != "exhausted":
            invitation.status = "exhausted"
            db.commit()
        return False, "exhausted", invitation

    return True, "valid", invitation


def activate_pilot_participant(
    db: Session,
    user: User,
    raw_token: str,
    compliance_accepted: bool,
) -> PilotParticipantActivation:
    """Authenticated user redeems an invitation token to activate pilot trial."""
    if not compliance_accepted:
        raise AppError(
            code="COMPLIANCE_ACCEPTANCE_REQUIRED",
            message="You must explicitly accept the pilot research and ethics terms to proceed.",
            status_code=400,
        )

    is_valid, reason, invitation = validate_invitation_token(db, raw_token)
    if not is_valid or not invitation:
        if reason == "revoked":
            raise AppError(
                code="PILOT_INVITATION_REVOKED",
                message="This pilot invitation has been revoked by administration.",
                status_code=403,
            )
        elif reason == "expired":
            raise AppError(
                code="PILOT_INVITATION_EXPIRED",
                message="This pilot invitation has expired.",
                status_code=403,
            )
        elif reason == "exhausted":
            raise AppError(
                code="PILOT_INVITATION_EXHAUSTED",
                message="This pilot invitation has reached its maximum redemptions.",
                status_code=403,
            )
        else:
            raise AppError(
                code="PILOT_INVITATION_INVALID",
                message="Invalid pilot invitation token. A valid invitation is required to join private trial.",
                status_code=403,
            )

    # Check if user already activated under this invitation
    existing_act = db.execute(
        select(PilotParticipantActivation).where(
            PilotParticipantActivation.user_id == user.id,
            PilotParticipantActivation.invitation_id == invitation.id,
        )
    ).scalar_one_or_none()

    if existing_act:
        return existing_act

    now = datetime.datetime.now(datetime.timezone.utc)

    # Increment usage on invitation
    invitation.used_count += 1
    if invitation.used_count >= invitation.max_uses:
        invitation.status = "exhausted"

    # Promote or configure user according to pilot role
    if invitation.target_role == "school_teacher":
        user.is_school_verified = True
        if invitation.school_id:
            user.school_id = invitation.school_id
        if user.role == UserRole.learner or user.role == UserRole.guest:
            user.role = UserRole.teacher
    elif invitation.target_role == "artisan_partner":
        if user.role != UserRole.admin and user.role != UserRole.super_admin:
            user.role = UserRole.teacher

    steps = PILOT_STEP_CHECKLIST.get(invitation.target_role, ["welcome", "activation_complete"])

    activation = PilotParticipantActivation(
        id=uuid.uuid4(),
        user_id=user.id,
        invitation_id=invitation.id,
        role_type=invitation.target_role,
        organization_name=invitation.organization_name,
        status="activated",
        current_step=steps[0],
        completed_steps=[],
        compliance_accepted=True,
        compliance_accepted_at=now,
        activated_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(activation)

    # Initialize Usage Health
    health = db.execute(
        select(PilotUsageHealth).where(PilotUsageHealth.user_id == user.id)
    ).scalar_one_or_none()
    if not health:
        health = PilotUsageHealth(
            id=uuid.uuid4(),
            user_id=user.id,
            activation_id=activation.id,
            login_count=1,
            actions_count=1,
            last_action_name="pilot_activated",
            last_active_at=now,
            health_score=100.0,
            health_status="healthy",
            telemetry_summary={
                "activation_date": now.isoformat(),
                "pilot_name": invitation.pilot_name,
                "role_type": invitation.target_role,
            },
            created_at=now,
            updated_at=now,
        )
        db.add(health)

    db.commit()
    db.refresh(activation)
    return activation


def get_user_activation(
    db: Session, user: User
) -> Optional[PilotParticipantActivation]:
    """Retrieve the active pilot activation for the current user."""
    return db.execute(
        select(PilotParticipantActivation)
        .where(PilotParticipantActivation.user_id == user.id)
        .order_by(desc(PilotParticipantActivation.created_at))
    ).scalars().first()


def record_onboarding_step(
    db: Session,
    user: User,
    step: str,
    completed: bool = True,
) -> PilotParticipantActivation:
    """Record progress on guided pilot checklist."""
    activation = get_user_activation(db, user)
    if not activation:
        raise AppError(
            code="NO_ACTIVE_PILOT",
            message="User does not have an active pilot participation.",
            status_code=404,
        )

    all_steps = PILOT_STEP_CHECKLIST.get(
        activation.role_type, ["welcome", "activation_complete"]
    )
    completed_steps = list(activation.completed_steps or [])

    if completed:
        if step not in completed_steps:
            completed_steps.append(step)
    else:
        if step in completed_steps:
            completed_steps.remove(step)

    activation.completed_steps = completed_steps

    # Advance current step
    remaining = [s for s in all_steps if s not in completed_steps]
    if remaining:
        activation.current_step = remaining[0]
    else:
        activation.current_step = all_steps[-1]
        activation.status = "completed"
        if not activation.completed_at:
            activation.completed_at = datetime.datetime.now(datetime.timezone.utc)

    activation.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # Record telemetry
    record_usage_telemetry(db, user, f"step_{step}_completed", {"step": step})

    db.commit()
    db.refresh(activation)
    return activation


def record_usage_telemetry(
    db: Session,
    user: User,
    action_name: str,
    details: Optional[dict[str, Any]] = None,
) -> PilotUsageHealth:
    """Track usage actions and compute health score."""
    health = db.execute(
        select(PilotUsageHealth).where(PilotUsageHealth.user_id == user.id)
    ).scalar_one_or_none()

    now = datetime.datetime.now(datetime.timezone.utc)

    if not health:
        act = get_user_activation(db, user)
        if not act:
            raise AppError(
                code="PILOT_HEALTH_NOT_FOUND",
                message="No pilot activation found to log health telemetry.",
                status_code=404,
            )
        health = PilotUsageHealth(
            id=uuid.uuid4(),
            user_id=user.id,
            activation_id=act.id,
            login_count=1,
            actions_count=1,
            last_action_name=action_name,
            last_active_at=now,
            health_score=100.0,
            health_status="healthy",
            telemetry_summary={action_name: 1},
            created_at=now,
            updated_at=now,
        )
        db.add(health)
    else:
        health.actions_count += 1
        health.last_action_name = action_name
        health.last_active_at = now
        telemetry = dict(health.telemetry_summary or {})
        telemetry[action_name] = telemetry.get(action_name, 0) + 1
        health.telemetry_summary = telemetry

        # Update health score: active use maintains >= 90
        # If user has >= 5 actions, health_score is 100.0; 2-4 is 90.0; 1 is 80.0
        if health.actions_count >= 5:
            health.health_score = 100.0
            health.health_status = "healthy"
        elif health.actions_count >= 2:
            health.health_score = 90.0
            health.health_status = "healthy"
        else:
            health.health_score = 75.0
            health.health_status = "attention_needed"

        health.updated_at = now

    db.commit()
    db.refresh(health)
    return health


def create_pilot_support_request(
    db: Session,
    user: User,
    category: str,
    priority: str,
    subject: str,
    message: str,
) -> PilotSupportRequest:
    """Create dedicated pilot feedback or help request."""
    activation = get_user_activation(db, user)
    now = datetime.datetime.now(datetime.timezone.utc)
    ticket_code = f"PILOT-REQ-{secrets.token_hex(3).upper()}"

    req = PilotSupportRequest(
        id=uuid.uuid4(),
        ticket_code=ticket_code,
        user_id=user.id,
        activation_id=activation.id if activation else None,
        category=category,
        priority=priority,
        status="open",
        subject=subject,
        message=message,
        responses=[],
        created_at=now,
        updated_at=now,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def reply_pilot_support_request(
    db: Session,
    ticket_id: uuid.UUID,
    user: User,
    message: str,
) -> PilotSupportRequest:
    """Add reply to a pilot support ticket."""
    req = db.get(PilotSupportRequest, ticket_id)
    if not req:
        raise AppError(
            code="TICKET_NOT_FOUND",
            message="Support ticket not found.",
            status_code=404,
        )

    # Check access: owner or staff/admin
    is_staff = user.role in (UserRole.admin, UserRole.super_admin)
    if req.user_id != user.id and not is_staff:
        raise AppError(
            code="ACCESS_DENIED",
            message="You do not have permission to view or reply to this ticket.",
            status_code=403,
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    entry = {
        "responder_id": str(user.id),
        "responder_name": user.display_name,
        "is_staff": is_staff,
        "message": message,
        "created_at": now.isoformat(),
    }
    responses = list(req.responses or [])
    responses.append(entry)
    req.responses = responses
    req.updated_at = now
    db.commit()
    db.refresh(req)
    return req
