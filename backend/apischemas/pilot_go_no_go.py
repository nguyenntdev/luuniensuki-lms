# -*- coding: utf-8 -*-
"""Pydantic API schemas for Pilot Go/No-Go Board (Ticket V5-T129 / Wave W12 Slot A09)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OwnerDecisionItem(BaseModel):
    owner_id: str = Field(..., description="Unique identifier for the domain owner")
    owner_name: str = Field(..., description="Full name of the decision maker")
    role: str = Field(..., description="Role title e.g. S1 Integrator, Lead Historian")
    decision: str = Field(..., description="GO, NO_GO, or CONDITIONAL_GO")
    signed_at: str = Field(..., description="ISO-8601 timestamp of formal sign-off")
    commit_sha: str = Field(..., description="Commit SHA locked at time of sign-off")
    attestation: str = Field(..., description="Attestation statement or signed notes")


class BlockingIssueItem(BaseModel):
    issue_id: str = Field(..., description="Unique issue tracker reference e.g. ISSUE-P0-001")
    title: str = Field(..., description="Summary of the issue")
    severity: str = Field(..., description="P0, P1, P2, or P3")
    status: str = Field(..., description="OPEN, RESOLVED, MITIGATED, or ACCEPTED_RISK")
    owner: str = Field(..., description="Assigned domain lead or engineer")
    description: str = Field(..., description="Technical description of the problem and blast radius")
    resolution_ref: Optional[str] = Field(None, description="Resolution PR, commit SHA, or mitigation runbook")
    resolved_at: Optional[str] = Field(None, description="ISO timestamp when marked resolved/mitigated")


class FeatureFlagItem(BaseModel):
    flag_key: str = Field(..., description="Configuration key for the feature flag")
    description: str = Field(..., description="Description of the feature capability")
    pilot_state: str = Field(..., description="ENABLED, DISABLED, PILOT_ONLY, or PERCENTAGE_ROLLOUT")
    rollout_percentage: float = Field(..., ge=0.0, le=100.0, description="Traffic percentage")
    kill_switch_supported: bool = Field(..., description="Whether instant runtime kill switch is wired")
    owner: str = Field(..., description="Responsible engineering lead")


class RollbackTriggerItem(BaseModel):
    trigger_id: str = Field(..., description="Trigger identifier e.g. TRG-01")
    metric_name: str = Field(..., description="Measurable operational metric")
    threshold: str = Field(..., description="Quantitative tripwire threshold")
    measurement_window: str = Field(..., description="Sliding evaluation window")
    automated_action: str = Field(..., description="Automated remediation or rollback SOP")
    severity: str = Field(..., description="Severity category e.g. P0_CRITICAL, P1_HIGH")


class SupportContactItem(BaseModel):
    tier: str = Field(..., description="Support tier e.g. Tier 1 Support, Tier 2 Incident Commander")
    role_name: str = Field(..., description="Role or team name")
    contact_channel: str = Field(..., description="Communication channel e.g. Telegram, Hotline")
    contact_value: str = Field(..., description="Channel handle, phone, or alias")
    escalation_sla: str = Field(..., description="Maximum response SLA e.g. 15 minutes")


class PilotGoNoGoEvaluateIn(BaseModel):
    release_version: str = Field("v2026.1.0-rbpc", description="Target release version tag")
    target_environment: str = Field("staging", description="Target environment (staging, production)")
    evaluator_name: str = Field("SRE Release Orchestrator", description="Name of evaluating orchestrator")
    owner_decisions: Optional[List[OwnerDecisionItem]] = Field(None, description="Custom owner decisions list")
    blocking_issues: Optional[List[BlockingIssueItem]] = Field(None, description="Custom blocking issues list")
    feature_flags: Optional[List[FeatureFlagItem]] = Field(None, description="Custom feature flags plan")
    rollback_triggers: Optional[List[RollbackTriggerItem]] = Field(None, description="Custom rollback triggers")
    support_contacts: Optional[List[SupportContactItem]] = Field(None, description="Custom support contacts")


class PilotGoNoGoBoardOut(BaseModel):
    board_ref: str = Field(..., description="Unique board evaluation reference")
    release_version: str = Field(..., description="Release version tag")
    target_environment: str = Field(..., description="Target environment")
    verdict: str = Field(..., description="Overall launch verdict: GO, BLOCKED, NO_GO, CONDITIONAL_GO")
    is_launch_blocked: bool = Field(..., description="True if any P0 issue is OPEN or required sign-off is missing/rejected")
    open_p0_count: int = Field(..., description="Number of unresolved P0 issues")
    open_p1_count: int = Field(..., description="Number of unresolved P1 issues")
    open_p2_count: int = Field(..., description="Number of unresolved P2 issues")
    signed_owners_count: int = Field(..., description="Number of signed owner decisions")
    blocking_reasons: List[str] = Field(default_factory=list, description="List of reasons blocking launch")
    owner_decisions: List[OwnerDecisionItem] = Field(default_factory=list, description="Signed owner decisions")
    blocking_issues: List[BlockingIssueItem] = Field(default_factory=list, description="Blocking issue register")
    feature_flags: List[FeatureFlagItem] = Field(default_factory=list, description="Feature flag rollout plan")
    rollback_triggers: List[RollbackTriggerItem] = Field(default_factory=list, description="Automated rollback triggers")
    support_contacts: List[SupportContactItem] = Field(default_factory=list, description="Support contacts & escalation matrix")
    evaluated_at: str = Field(..., description="Evaluation timestamp")
    evaluated_by: str = Field(..., description="Evaluator name")


class PilotGoNoGoExportOut(BaseModel):
    format: str = Field(..., description="Export format: markdown or json")
    board_ref: str = Field(..., description="Board reference")
    verdict: str = Field(..., description="Launch verdict")
    content: str = Field(..., description="Rendered board report content")
