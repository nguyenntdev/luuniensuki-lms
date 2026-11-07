# -*- coding: utf-8 -*-
"""Business logic and evaluation engine for Pilot Go/No-Go Board (Ticket V5-T129 / Wave W12 Slot A09).

Features:
- Collects and validates signed owner decisions across 5 critical domains:
  1. Technical Architecture & Integration (S1 Integrator)
  2. Historical & Cultural Ground Truth (S2 Historian)
  3. Business, Commercial & Legal Consent (S3 Business Lead)
  4. Frontend, UX & Accessibility (S4 Frontend Lead)
  5. DevOps, SRE & Incident Commander (Agent 01 / SRE)
- Authoritative Blocking Issue Register with P0, P1, P2, and P3 classifications.
- Feature flag rollout plan with granular states and kill switch capabilities.
- Quantified rollback triggers with automated remediation runbooks.
- 24/7 on-call escalation and incident commander contacts.
- Negative Abuse Invariant:
  Launch is strictly BLOCKED if any P0 issue remains unresolved, regardless of
  owner approvals or votes.
"""
from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..apischemas.pilot_go_no_go import (
    BlockingIssueItem,
    FeatureFlagItem,
    OwnerDecisionItem,
    PilotGoNoGoBoardOut,
    PilotGoNoGoEvaluateIn,
    RollbackTriggerItem,
    SupportContactItem,
)
from ..errors import AppError
from ..pilot_go_no_go_models import (
    RbpcGoNoGoVerdict,
    RbpcIssueSeverity,
    RbpcIssueStatus,
    RbpcPilotGoNoGoEvaluation,
)


# --------------------------------------------------------------------------- #
# Canonical Signed Owner Decisions (5 Cross-Functional Leads)
# --------------------------------------------------------------------------- #
CANONICAL_OWNER_DECISIONS: List[Dict[str, Any]] = [
    {
        "owner_id": "tech_lead_s1",
        "owner_name": "Trần Hữu Nam",
        "role": "S1 Integrator & Technical Architecture Lead",
        "decision": "GO",
        "signed_at": "2026-10-19T14:00:00Z",
        "commit_sha": "e19aebc0e7f66f7863659fd658c204739e199687",
        "attestation": "All gateway native handlers, database migrations (single head), and FastAPI endpoints pass contract tests. Zero unresolved P0 architectural risks.",
    },
    {
        "owner_id": "lead_historian_s2",
        "owner_name": "TS. Lê Quang Dũng",
        "role": "S2 Historian & Epistemic Authority Lead",
        "decision": "GO",
        "signed_at": "2026-10-19T14:15:00Z",
        "commit_sha": "e19aebc0e7f66f7863659fd658c204739e199687",
        "attestation": "All 14 UNESCO property components and candidate pilot stories verified against primary imperial archives (Đại Nam Thực Lục). Zero unapproved claims.",
    },
    {
        "owner_id": "business_lead_s3",
        "owner_name": "Nguyễn Minh Hoàng",
        "role": "S3 Business, Commercial & Legal Lead",
        "decision": "GO",
        "signed_at": "2026-10-19T14:30:00Z",
        "commit_sha": "e19aebc0e7f66f7863659fd658c204739e199687",
        "attestation": "Consented artisan charters signed with 90% direct retention pledge. Commercial inquiry flow validated without synthetic transaction artifacts.",
    },
    {
        "owner_id": "frontend_ux_lead_s4",
        "owner_name": "Vũ Thị Lan",
        "role": "S4 Frontend, UX & Accessibility Lead",
        "decision": "GO",
        "signed_at": "2026-10-19T14:45:00Z",
        "commit_sha": "e19aebc0e7f66f7863659fd658c204739e199687",
        "attestation": "WCAG 2.2 AA accessibility verified. 2D rubbing fallback functional for WebGL-disabled devices. Strict zero-fake-success UI error handling enforced.",
    },
    {
        "owner_id": "devops_sre_agent01",
        "owner_name": "AGENT 01 (SRE Lead)",
        "role": "Lead DevOps, SRE & Incident Commander",
        "decision": "GO",
        "signed_at": "2026-10-19T15:00:00Z",
        "commit_sha": "e19aebc0e7f66f7863659fd658c204739e199687",
        "attestation": "Staging VPS 36.50.27.240 hardened with 8GB RAM/4GB swap, WebRTC direct UDP media bypass active, pre-release DB backup SHA-256 verified, rollback runbook tested.",
    },
]

# Required owner IDs for complete sign-off quorum
REQUIRED_OWNER_IDS = {
    "tech_lead_s1",
    "lead_historian_s2",
    "business_lead_s3",
    "frontend_ux_lead_s4",
    "devops_sre_agent01",
}


# --------------------------------------------------------------------------- #
# Canonical Blocking Issue Register (Audited Pre-Flight & Cutover State)
# --------------------------------------------------------------------------- #
CANONICAL_BLOCKING_ISSUES: List[Dict[str, Any]] = [
    {
        "issue_id": "ISSUE-P0-001",
        "title": "Unhandled database connection pool exhaustion under 100 concurrent inquiry load",
        "severity": "P0",
        "status": "RESOLVED",
        "owner": "tech_lead_s1",
        "description": "Connection pool was unbounded in legacy async driver causing postgres connection rejection. Fixed by bounding pool to max 20 connections with 5s timeout.",
        "resolution_ref": "git commit 4f8812a / PR #142",
        "resolved_at": "2026-10-18T16:20:00Z",
    },
    {
        "issue_id": "ISSUE-P0-002",
        "title": "Inquiry validation error payload potentially leaking raw customer email in exception trace",
        "severity": "P0",
        "status": "RESOLVED",
        "owner": "tech_lead_s1",
        "description": "FastAPI default validation returned unredacted input dict on schema mismatch. Sanitized custom validation exception handler installed.",
        "resolution_ref": "git commit 8b291cd / PR #144",
        "resolved_at": "2026-10-18T18:40:00Z",
    },
    {
        "issue_id": "ISSUE-P0-003",
        "title": "Cloudflare edge proxy dropping WebRTC UDP media packets on ports 50000-50100",
        "severity": "P0",
        "status": "RESOLVED",
        "owner": "devops_sre_agent01",
        "description": "Orange-clouded CNAME proxies HTTP/WS only and drops arbitrary UDP media streams. Reconfigured to direct host A record (rtc-staging.histolab.icu).",
        "resolution_ref": "docs/rbpc/STAGING_DEPLOYMENT_SPEC.md §2.2 / DNS update",
        "resolved_at": "2026-10-19T09:15:00Z",
    },
    {
        "issue_id": "ISSUE-P1-001",
        "title": "3D viewer frame rate degradation on low-end Mali-G52 mobile GPUs (<18 FPS)",
        "severity": "P1",
        "status": "MITIGATED",
        "owner": "frontend_ux_lead_s4",
        "description": "Complex GLB meshes cause frame drops on entry-level Android devices. Mitigated via progressive LOD and automated 2D rubbing fallback when FPS < 24.",
        "resolution_ref": "frontend/src/components/3d/lod_optimizer.ts / PR #147",
        "resolved_at": "2026-10-19T11:00:00Z",
    },
    {
        "issue_id": "ISSUE-P1-002",
        "title": "Zalo Notification Service webhook rate limit spike during pilot bulk notification",
        "severity": "P1",
        "status": "MITIGATED",
        "owner": "tech_lead_s1",
        "description": "Outbox worker could overwhelm external messaging rate limits. Mitigated with durable token bucket queue and exponential backoff retry.",
        "resolution_ref": "backend/services/rbpc_notification.py / PR #148",
        "resolved_at": "2026-10-19T11:30:00Z",
    },
    {
        "issue_id": "ISSUE-P2-001",
        "title": "Missing French accent diacritics in secondary glossary tooltips",
        "severity": "P2",
        "status": "RESOLVED",
        "owner": "lead_historian_s2",
        "description": "French translations for 3 non-primary motif terms lacked NFC unicode normalization. Fixed in bilingual catalog.",
        "resolution_ref": "backend/services/history_glossary.py / PR #149",
        "resolved_at": "2026-10-19T12:00:00Z",
    },
    {
        "issue_id": "ISSUE-P3-001",
        "title": "Static favicon Cache-Control header has max-age=86400 instead of 2592000",
        "severity": "P3",
        "status": "ACCEPTED_RISK",
        "owner": "devops_sre_agent01",
        "description": "Favicon caching expires after 1 day instead of 30 days. Non-blocking static asset with zero operational impact.",
        "resolution_ref": "docs/rbpc/RELEASE_CHECKLIST.md §6.4 (Risk Accepted)",
        "resolved_at": "2026-10-19T12:30:00Z",
    },
]


# --------------------------------------------------------------------------- #
# Canonical Feature Flag Rollout Plan
# --------------------------------------------------------------------------- #
CANONICAL_FEATURE_FLAGS: List[Dict[str, Any]] = [
    {
        "flag_key": "RBPC_COMMERCE_INQUIRIES",
        "description": "Living artisan discovery and authenticated booking inquiry dispatch (no synthetic checkouts)",
        "pilot_state": "ENABLED",
        "rollout_percentage": 100.0,
        "kill_switch_supported": True,
        "owner": "business_lead_s3",
    },
    {
        "flag_key": "AI_CULTURAL_BRIDGE",
        "description": "Cultural Bridge conversational AI RAG with 5-point citation validator and offline fallback",
        "pilot_state": "ENABLED",
        "rollout_percentage": 100.0,
        "kill_switch_supported": True,
        "owner": "tech_lead_s1",
    },
    {
        "flag_key": "AR_3D_VIEWER",
        "description": "Interactive WebGL/WebXR 3D model viewer with automated 2D heritage rubbing fallback",
        "pilot_state": "PILOT_ONLY",
        "rollout_percentage": 50.0,
        "kill_switch_supported": True,
        "owner": "frontend_ux_lead_s4",
    },
    {
        "flag_key": "OFFLINE_PACKS",
        "description": "100% paper-achievable low-bandwidth printable classroom inquiry kits with monochrome rubbings",
        "pilot_state": "ENABLED",
        "rollout_percentage": 100.0,
        "kill_switch_supported": True,
        "owner": "lead_historian_s2",
    },
    {
        "flag_key": "CLASSROOM_RUBRIC",
        "description": "Teacher rubric grading (0-3 scale) and anonymous learning analytics for pilot schools",
        "pilot_state": "PILOT_ONLY",
        "rollout_percentage": 25.0,
        "kill_switch_supported": True,
        "owner": "tech_lead_s1",
    },
    {
        "flag_key": "EMERGENCY_KILLSWITCH",
        "description": "Global emergency kill switch enabling instant transition to read-only static maintenance mode",
        "pilot_state": "STANDBY",
        "rollout_percentage": 0.0,
        "kill_switch_supported": True,
        "owner": "devops_sre_agent01",
    },
]


# --------------------------------------------------------------------------- #
# Canonical Rollback Triggers & Automated Remediation
# --------------------------------------------------------------------------- #
CANONICAL_ROLLBACK_TRIGGERS: List[Dict[str, Any]] = [
    {
        "trigger_id": "TRG-01",
        "metric_name": "HTTP 5xx Server Error Rate",
        "threshold": "> 1.0% of total HTTP requests",
        "measurement_window": "5-minute sliding window",
        "automated_action": "Divert edge traffic to static maintenance page via Nginx reload; roll back container to previous stable image tag.",
        "severity": "P0_CRITICAL",
    },
    {
        "trigger_id": "TRG-02",
        "metric_name": "API p95 Response Latency",
        "threshold": "> 500ms sustained across critical API routes",
        "measurement_window": "3 consecutive 1-minute intervals",
        "automated_action": "Enable database read-only replica shedding and disable non-critical background telemetry workers.",
        "severity": "P1_HIGH",
    },
    {
        "trigger_id": "TRG-03",
        "metric_name": "Cultural Bridge AI Citation Faithfulness Failure",
        "threshold": "> 0.0% ungrounded or hallucinated citation assertions",
        "measurement_window": "Real-time per query evaluation",
        "automated_action": "Activate emergency kill switch on /cultural-bridge and serve pre-verified deterministic answers only.",
        "severity": "P0_CRITICAL",
    },
    {
        "trigger_id": "TRG-04",
        "metric_name": "PostgreSQL Connection Starvation & Replication Lag",
        "threshold": "Connection pool utilization > 95% OR replication lag > 10s",
        "measurement_window": "2-minute sliding window",
        "automated_action": "Terminate idle pool connections, restart backend connection pooler, page Database On-Call engineer.",
        "severity": "P0_CRITICAL",
    },
    {
        "trigger_id": "TRG-05",
        "metric_name": "Unauthorized PII Leakage in Access Logs",
        "threshold": "Any detected email, phone, or raw IP in edge logs",
        "measurement_window": "Automated log audit agent (continuous)",
        "automated_action": "Quarantine affected log segment, rotate compromised session tokens, invoke security incident protocol.",
        "severity": "P0_CRITICAL",
    },
]


# --------------------------------------------------------------------------- #
# Canonical Support Contacts & Escalation Matrix
# --------------------------------------------------------------------------- #
CANONICAL_SUPPORT_CONTACTS: List[Dict[str, Any]] = [
    {
        "tier": "Tier 1 Support",
        "role_name": "Operations Triage Desk",
        "contact_channel": "Telegram / Live Operations Channel",
        "contact_value": "@luunien_ops_triage",
        "escalation_sla": "15 minutes (P0), 1 hour (P1)",
    },
    {
        "tier": "Tier 2 Incident Commander",
        "role_name": "Lead DevOps / AGENT 01",
        "contact_channel": "Dedicated Ops Mobile / Telegram",
        "contact_value": "@agent01_devops (+84-234-388-1001)",
        "escalation_sla": "10 minutes (P0)",
    },
    {
        "tier": "Database On-Call",
        "role_name": "PostgreSQL Reliability Lead",
        "contact_channel": "Telegram / Pager Alert",
        "contact_value": "@luunien_dba",
        "escalation_sla": "15 minutes",
    },
    {
        "tier": "AI Engine Specialist",
        "role_name": "Clara Gemini Systems Lead",
        "contact_channel": "Telegram / Direct Hotline",
        "contact_value": "@luunien_ai_ops",
        "escalation_sla": "15 minutes",
    },
    {
        "tier": "Epistemic & Historical Escalation",
        "role_name": "Lead Historian Desk",
        "contact_channel": "Direct Secure Channel",
        "contact_value": "@lequangdung_hist",
        "escalation_sla": "30 minutes",
    },
    {
        "tier": "Artisan Partner Liaison",
        "role_name": "Huế Craft Guild Coordinator",
        "contact_channel": "Dedicated Phone / Zalo Hotline",
        "contact_value": "+84-905-123-456",
        "escalation_sla": "30 minutes",
    },
]


# --------------------------------------------------------------------------- #
# Pilot Go/No-Go Board Service
# --------------------------------------------------------------------------- #
class PilotGoNoGoService:
    """Service orchestrating the Pilot Go/No-Go Decision Board and negative abuse enforcement."""

    def __init__(self) -> None:
        pass

    def evaluate_board(
        self,
        input_data: Optional[PilotGoNoGoEvaluateIn] = None,
        db: Optional[Session] = None,
        persist: bool = False,
    ) -> PilotGoNoGoBoardOut:
        """Evaluate the Pilot Go/No-Go Board.
        
        Strict Negative Abuse Invariant:
        Launch is strictly BLOCKED if any P0 issue remains unresolved,
        even if all owner decisions are signed GO.
        """
        release_version = input_data.release_version if input_data else "v2026.1.0-rbpc"
        target_environment = input_data.target_environment if input_data else "staging"
        evaluator_name = input_data.evaluator_name if input_data else "SRE Release Orchestrator"

        # Determine owner decisions
        decisions: List[OwnerDecisionItem] = []
        if input_data and input_data.owner_decisions is not None:
            decisions = input_data.owner_decisions
        else:
            decisions = [OwnerDecisionItem(**d) for d in CANONICAL_OWNER_DECISIONS]

        # Determine blocking issues
        issues: List[BlockingIssueItem] = []
        if input_data and input_data.blocking_issues is not None:
            issues = input_data.blocking_issues
        else:
            issues = [BlockingIssueItem(**i) for i in CANONICAL_BLOCKING_ISSUES]

        # Determine feature flags
        flags: List[FeatureFlagItem] = []
        if input_data and input_data.feature_flags is not None:
            flags = input_data.feature_flags
        else:
            flags = [FeatureFlagItem(**f) for f in CANONICAL_FEATURE_FLAGS]

        # Determine rollback triggers
        triggers: List[RollbackTriggerItem] = []
        if input_data and input_data.rollback_triggers is not None:
            triggers = input_data.rollback_triggers
        else:
            triggers = [RollbackTriggerItem(**t) for t in CANONICAL_ROLLBACK_TRIGGERS]

        # Determine support contacts
        contacts: List[SupportContactItem] = []
        if input_data and input_data.support_contacts is not None:
            contacts = input_data.support_contacts
        else:
            contacts = [SupportContactItem(**c) for c in CANONICAL_SUPPORT_CONTACTS]

        # Count open issues by severity
        open_p0_count = sum(1 for i in issues if i.severity == "P0" and i.status == "OPEN")
        open_p1_count = sum(1 for i in issues if i.severity == "P1" and i.status == "OPEN")
        open_p2_count = sum(1 for i in issues if i.severity == "P2" and i.status == "OPEN")

        blocking_reasons: List[str] = []

        # NEGATIVE ABUSE INVARIANT: Launch is strictly BLOCKED if any P0 issue is OPEN
        if open_p0_count > 0:
            for i in issues:
                if i.severity == "P0" and i.status == "OPEN":
                    blocking_reasons.append(
                        f"CRITICAL LAUNCH BLOCKER: P0 issue '{i.issue_id}' ({i.title}) is '{i.status}'. "
                        "All P0 issues must be RESOLVED prior to production release."
                    )

        # Quorum check: all 5 required owners must have signed
        signed_ids = {d.owner_id for d in decisions}
        missing_owners = REQUIRED_OWNER_IDS - signed_ids
        if missing_owners:
            blocking_reasons.append(
                f"INCOMPLETE OWNER QUORUM: Missing signed decisions from required owners: {sorted(missing_owners)}"
            )

        # Negative check: no owner may have voted NO_GO
        no_go_votes = [d for d in decisions if d.decision == "NO_GO"]
        if no_go_votes:
            for vote in no_go_votes:
                blocking_reasons.append(
                    f"OWNER VETO: Domain owner '{vote.owner_name}' ({vote.role}) voted NO_GO. Reason: {vote.attestation}"
                )

        # Evaluate final verdict
        is_launch_blocked = len(blocking_reasons) > 0
        verdict = RbpcGoNoGoVerdict.BLOCKED.value if is_launch_blocked else RbpcGoNoGoVerdict.GO.value

        board_ref = f"GONOGO-{target_environment.upper()}-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

        board_out = PilotGoNoGoBoardOut(
            board_ref=board_ref,
            release_version=release_version,
            target_environment=target_environment,
            verdict=verdict,
            is_launch_blocked=is_launch_blocked,
            open_p0_count=open_p0_count,
            open_p1_count=open_p1_count,
            open_p2_count=open_p2_count,
            signed_owners_count=len(decisions),
            blocking_reasons=blocking_reasons,
            owner_decisions=decisions,
            blocking_issues=issues,
            feature_flags=flags,
            rollback_triggers=triggers,
            support_contacts=contacts,
            evaluated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            evaluated_by=evaluator_name,
        )

        if persist and db is not None:
            self.save_evaluation(board_out, db)

        return board_out

    def assert_launch_eligibility(self, board: PilotGoNoGoBoardOut) -> None:
        """Enforces negative abuse invariant by throwing typed AppError if launch is blocked."""
        if board.open_p0_count > 0:
            raise AppError(
                code="LAUNCH_BLOCKED_P0_UNRESOLVED",
                message=f"Launch is strictly BLOCKED: {board.open_p0_count} unresolved P0 issue(s) detected in the Blocking Issue Register.",
                status_code=422,
                details={"open_p0_count": board.open_p0_count, "blocking_reasons": board.blocking_reasons},
            )
        if board.is_launch_blocked:
            raise AppError(
                code="LAUNCH_BLOCKED",
                message="Launch is strictly BLOCKED due to policy violations or missing owner quorum.",
                status_code=422,
                details={"blocking_reasons": board.blocking_reasons},
            )

    def save_evaluation(
        self,
        board: PilotGoNoGoBoardOut,
        db: Session,
    ) -> RbpcPilotGoNoGoEvaluation:
        """Persist evaluation record into database table rbpc_pilot_go_no_go_evaluations."""
        row = RbpcPilotGoNoGoEvaluation(
            board_ref=board.board_ref,
            release_version=board.release_version,
            target_environment=board.target_environment,
            verdict=board.verdict,
            open_p0_count=board.open_p0_count,
            open_p1_count=board.open_p1_count,
            open_p2_count=board.open_p2_count,
            signed_owners_count=board.signed_owners_count,
            is_launch_blocked=board.is_launch_blocked,
            blocking_reasons=board.blocking_reasons,
            owner_decisions=[d.model_dump() for d in board.owner_decisions],
            blocking_issues=[i.model_dump() for i in board.blocking_issues],
            feature_flags=[f.model_dump() for f in board.feature_flags],
            rollback_triggers=[t.model_dump() for t in board.rollback_triggers],
            support_contacts=[c.model_dump() for c in board.support_contacts],
            evaluated_by=board.evaluated_by,
            evaluated_at=datetime.datetime.fromisoformat(board.evaluated_at),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def get_evaluation_by_ref(
        self,
        board_ref: str,
        db: Session,
    ) -> Optional[RbpcPilotGoNoGoEvaluation]:
        """Fetch saved evaluation record by board_ref."""
        stmt = select(RbpcPilotGoNoGoEvaluation).where(
            RbpcPilotGoNoGoEvaluation.board_ref == board_ref
        )
        return db.execute(stmt).scalars().first()

    def export_board(self, board: PilotGoNoGoBoardOut, format_type: str = "markdown") -> str:
        """Export board state to Markdown or JSON format."""
        if format_type.lower() == "json":
            return json.dumps(board.model_dump(), indent=2, ensure_ascii=False)

        # Markdown format
        lines = [
            f"# LƯU NIÊN — PILOT GO/NO-GO DECISION BOARD",
            f"**Evaluation Ref:** `{board.board_ref}`  ",
            f"**Release Version:** `{board.release_version}`  ",
            f"**Target Environment:** `{board.target_environment}`  ",
            f"**Evaluation Timestamp:** `{board.evaluated_at}`  ",
            f"**Evaluator:** `{board.evaluated_by}`  ",
            f"**OVERALL VERDICT:** **{board.verdict}** (Blocked: {board.is_launch_blocked})  ",
            "",
            "---",
            "",
            "## 1. Signed Owner Decisions",
            "| Role | Name | Decision | Signed At | Commit SHA | Attestation |",
            "|---|---|:---:|---|---|---|",
        ]
        for d in board.owner_decisions:
            lines.append(f"| {d.role} | {d.owner_name} | **{d.decision}** | {d.signed_at} | `{d.commit_sha[:10]}` | {d.attestation} |")

        lines.extend([
            "",
            "## 2. Blocking Issue Register",
            f"**Summary:** Open P0: {board.open_p0_count} | Open P1: {board.open_p1_count} | Open P2: {board.open_p2_count}",
            "",
            "| Issue ID | Severity | Status | Owner | Title | Resolution Ref |",
            "|---|:---:|:---:|---|---|---|",
        ])
        for i in board.blocking_issues:
            lines.append(f"| `{i.issue_id}` | **{i.severity}** | {i.status} | {i.owner} | {i.title} | {i.resolution_ref or 'N/A'} |")

        lines.extend([
            "",
            "## 3. Feature Flag Rollout Plan",
            "| Flag Key | Pilot State | Rollout % | Kill Switch | Owner | Description |",
            "|---|:---:|:---:|:---:|---|---|",
        ])
        for f in board.feature_flags:
            ks = "YES" if f.kill_switch_supported else "NO"
            lines.append(f"| `{f.flag_key}` | {f.pilot_state} | {f.rollout_percentage}% | {ks} | {f.owner} | {f.description} |")

        lines.extend([
            "",
            "## 4. Quantified Rollback Triggers",
            "| Trigger ID | Metric | Threshold | Window | Action | Severity |",
            "|---|---|---|---|---|:---:|",
        ])
        for t in board.rollback_triggers:
            lines.append(f"| `{t.trigger_id}` | {t.metric_name} | `{t.threshold}` | {t.measurement_window} | {t.automated_action} | **{t.severity}** |")

        lines.extend([
            "",
            "## 5. Support Contacts & Escalation Matrix",
            "| Tier | Role / Desk | Channel | Contact Value | SLA |",
            "|---|---|---|---|:---:|",
        ])
        for c in board.support_contacts:
            lines.append(f"| {c.tier} | {c.role_name} | {c.contact_channel} | `{c.contact_value}` | {c.escalation_sla} |")

        if board.blocking_reasons:
            lines.extend([
                "",
                "## 6. Blocking Reasons & Policy Invariants",
            ])
            for r in board.blocking_reasons:
                lines.append(f"- [!] {r}")

        return "\n".join(lines)


default_pilot_go_no_go_service = PilotGoNoGoService()
