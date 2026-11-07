# -*- coding: utf-8 -*-
"""Pydantic schemas for Pilot Onboarding Portal (Ticket V5-T116 / Wave W11 Slot A06)."""
from __future__ import annotations

import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PilotInvitationCreateIn(BaseModel):
    pilot_name: str = Field(..., min_length=3, max_length=255)
    target_role: str = Field(..., description="'school_teacher' or 'artisan_partner'")
    organization_name: str = Field(..., min_length=2, max_length=255)
    contact_email: str = Field(..., min_length=5, max_length=255)
    school_id: Optional[UUID] = None
    partner_id: Optional[UUID] = None
    max_uses: int = Field(1, ge=1, le=100)
    expires_in_days: int = Field(30, ge=1, le=365)
    notes: Optional[str] = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)


class PilotInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invitation_code: str
    pilot_name: str
    target_role: str
    organization_name: str
    contact_email: str
    school_id: Optional[UUID] = None
    partner_id: Optional[UUID] = None
    max_uses: int
    used_count: int
    status: str
    expires_at: datetime.datetime
    notes: Optional[str] = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime
    # Note: token secret string only returned when newly generated, never in regular listings
    invitation_token: Optional[str] = None


class PilotValidateInvitationIn(BaseModel):
    token: str = Field(..., min_length=10, description="Raw secret invitation token")


class PilotInvitationValidationResult(BaseModel):
    is_valid: bool
    status: str  # "valid", "expired", "exhausted", "revoked", "invalid"
    message: str
    invitation_code: Optional[str] = None
    pilot_name: Optional[str] = None
    target_role: Optional[str] = None
    organization_name: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None


class PilotActivateIn(BaseModel):
    token: str = Field(..., min_length=10, description="Invitation token to redeem")
    compliance_accepted: bool = Field(
        ..., description="Must explicitly accept pilot compliance terms"
    )


class PilotActivationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    invitation_id: UUID
    role_type: str
    organization_name: str
    status: str
    current_step: str
    completed_steps: list[str]
    compliance_accepted: bool
    compliance_accepted_at: Optional[datetime.datetime] = None
    activated_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    pilot_name: Optional[str] = None


class PilotOnboardingStepIn(BaseModel):
    step: str = Field(..., description="Onboarding step key, e.g. welcome, tour, first_action, etc.")
    completed: bool = True


class PilotUsageHealthOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    activation_id: UUID
    login_count: int
    actions_count: int
    last_action_name: Optional[str] = None
    last_active_at: datetime.datetime
    health_score: float
    health_status: str
    telemetry_summary: dict[str, Any]


class PilotHealthTelemetryRecordIn(BaseModel):
    action_name: str = Field(..., min_length=2, max_length=100)
    details: dict[str, Any] = Field(default_factory=dict)


class PilotSupportRequestCreateIn(BaseModel):
    category: str = Field(
        ...,
        description="'activation', 'onboarding_help', 'feature_feedback', 'data_privacy', 'bug_report'",
    )
    priority: str = Field("normal", description="'low', 'normal', 'high', 'urgent'")
    subject: str = Field(..., min_length=5, max_length=255)
    message: str = Field(..., min_length=10)


class PilotSupportRequestReplyIn(BaseModel):
    message: str = Field(..., min_length=3)


class PilotSupportRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_code: str
    user_id: UUID
    activation_id: Optional[UUID] = None
    category: str
    priority: str
    status: str
    subject: str
    message: str
    responses: list[dict[str, Any]] = Field(default_factory=list)
    resolved_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
