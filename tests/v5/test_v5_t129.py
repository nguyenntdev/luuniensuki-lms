# -*- coding: utf-8 -*-
"""V5-T129 (Wave W12, Slot A09): Pilot Go/No-Go Board Test Suite.

Audits and verifies:
1. Canonical Go/No-Go Board completeness and structure:
   - 5 domain owner decisions (Tech, Historian, Business, Frontend, DevOps).
   - Blocking issue register (P0, P1, P2, P3) with 0 open P0 issues.
   - 6 feature flags with granular pilot states and kill switches.
   - 5 quantified rollback triggers with automated remediation SOPs.
   - 6 support tiers with defined SLAs and escalation contacts.
2. Owner Decisions Integrity:
   - All 5 required owners present and signed GO.
   - Valid commit SHAs, ISO timestamps, and signed attestations.
3. Negative Abuse Guardrail 1 (Unresolved P0 Issue Blocks Launch):
   - Launch is strictly BLOCKED if any P0 issue remains unresolved,
     even if all 5 domain owners voted GO.
   - assert_launch_eligibility raises HTTP 422 LAUNCH_BLOCKED_P0_UNRESOLVED.
4. Negative Abuse Guardrail 2 (Owner Veto Blocks Launch):
   - A single dissenting NO_GO vote strictly forces verdict to BLOCKED.
5. Negative Abuse Guardrail 3 (Missing Owner Quorum Blocks Launch):
   - Missing any required domain owner strictly forces verdict to BLOCKED.
6. Positive Acceptance (Golden Go/No-Go Board):
   - All P0 resolved + 5/5 signed GO -> verdict == GO, is_launch_blocked == False.
7. Database Persistence & Reload:
   - Board evaluations persist in rbpc_pilot_go_no_go_evaluations table.
8. REST API Endpoints Integration:
   - GET  /api/v1/rbpc/go-no-go/board
   - POST /api/v1/rbpc/go-no-go/evaluate
   - GET  /api/v1/rbpc/go-no-go/evaluations/{board_ref}
   - GET  /api/v1/rbpc/go-no-go/export
9. Documentation and Artifact Parity:
   - Verifies docs/rbpc/RELEASE_CHECKLIST.md Section 11.
   - Verifies artifacts/implementation/W12/W12_A09_pilot_go_no_go_board.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app import create_app
from backend.apischemas.pilot_go_no_go import (
    BlockingIssueItem,
    FeatureFlagItem,
    OwnerDecisionItem,
    PilotGoNoGoEvaluateIn,
    RollbackTriggerItem,
    SupportContactItem,
)
from backend.errors import AppError
from backend.pilot_go_no_go_models import (
    RbpcGoNoGoVerdict,
    RbpcIssueSeverity,
    RbpcIssueStatus,
    RbpcPilotGoNoGoEvaluation,
)
from backend.services.pilot_go_no_go import (
    CANONICAL_BLOCKING_ISSUES,
    CANONICAL_FEATURE_FLAGS,
    CANONICAL_OWNER_DECISIONS,
    CANONICAL_ROLLBACK_TRIGGERS,
    CANONICAL_SUPPORT_CONTACTS,
    REQUIRED_OWNER_IDS,
    PilotGoNoGoService,
    default_pilot_go_no_go_service,
)


# --------------------------------------------------------------------------- #
# 1. Canonical Board Structure & Completeness
# --------------------------------------------------------------------------- #
def test_v5_t129_canonical_board_completeness():
    """Verify that canonical Go/No-Go board evaluates to GO and satisfies all quorums."""
    service = default_pilot_go_no_go_service
    board = service.evaluate_board()

    assert board.board_ref.startswith("GONOGO-STAGING-")
    assert board.release_version == "v2026.1.0-rbpc"
    assert board.target_environment == "staging"
    assert board.verdict == "GO"
    assert board.is_launch_blocked is False
    assert board.open_p0_count == 0
    assert board.open_p1_count == 0
    assert board.open_p2_count == 0
    assert board.signed_owners_count == 5
    assert len(board.blocking_reasons) == 0

    # Verify items collections
    assert len(board.owner_decisions) == 5
    assert len(board.blocking_issues) >= 7
    assert len(board.feature_flags) == 6
    assert len(board.rollback_triggers) == 5
    assert len(board.support_contacts) == 6


# --------------------------------------------------------------------------- #
# 2. Owner Decisions Integrity (5 Domain Quorum)
# --------------------------------------------------------------------------- #
def test_v5_t129_owner_decisions_quorum_and_integrity():
    """Verify all 5 required owners have signed GO with valid metadata and commit SHA."""
    service = default_pilot_go_no_go_service
    board = service.evaluate_board()

    signed_ids = {d.owner_id for d in board.owner_decisions}
    assert signed_ids == REQUIRED_OWNER_IDS, f"Missing owners: {REQUIRED_OWNER_IDS - signed_ids}"

    for d in board.owner_decisions:
        assert d.owner_name
        assert d.role
        assert d.decision == "GO"
        assert len(d.commit_sha) >= 7
        assert "T" in d.signed_at
        assert len(d.attestation) > 20


# --------------------------------------------------------------------------- #
# 3. Blocking Issues Register & 0 Open P0s
# --------------------------------------------------------------------------- #
def test_v5_t129_blocking_issues_register_resolution():
    """Verify all P0 issues in the canonical register are strictly RESOLVED."""
    service = default_pilot_go_no_go_service
    board = service.evaluate_board()

    p0_issues = [i for i in board.blocking_issues if i.severity == "P0"]
    assert len(p0_issues) >= 3, "Expected at least 3 canonical P0 issues cataloged"

    for p0 in p0_issues:
        assert p0.status == "RESOLVED", f"P0 issue {p0.issue_id} is {p0.status}, must be RESOLVED"
        assert p0.resolution_ref is not None, f"P0 issue {p0.issue_id} missing resolution_ref"
        assert p0.resolved_at is not None

    p1_issues = [i for i in board.blocking_issues if i.severity == "P1"]
    for p1 in p1_issues:
        assert p1.status in ("RESOLVED", "MITIGATED")


# --------------------------------------------------------------------------- #
# 4. Feature Flags and Emergency Kill Switches
# --------------------------------------------------------------------------- #
def test_v5_t129_feature_flags_and_kill_switches():
    """Verify 6 feature flags are mapped with pilot states and emergency kill switches."""
    service = default_pilot_go_no_go_service
    board = service.evaluate_board()

    flag_map = {f.flag_key: f for f in board.feature_flags}
    expected_flags = {
        "RBPC_COMMERCE_INQUIRIES",
        "AI_CULTURAL_BRIDGE",
        "AR_3D_VIEWER",
        "OFFLINE_PACKS",
        "CLASSROOM_RUBRIC",
        "EMERGENCY_KILLSWITCH",
    }
    assert set(flag_map.keys()) == expected_flags

    for flag in board.feature_flags:
        assert flag.kill_switch_supported is True, f"Flag {flag.flag_key} must support kill switch"
        assert flag.owner
        assert flag.pilot_state in ("ENABLED", "DISABLED", "PILOT_ONLY", "STANDBY")

    # Master kill switch must be on standby with 0% traffic initially
    assert flag_map["EMERGENCY_KILLSWITCH"].pilot_state == "STANDBY"
    assert flag_map["EMERGENCY_KILLSWITCH"].rollout_percentage == 0.0


# --------------------------------------------------------------------------- #
# 5. Rollback Triggers & Support Escalation Matrix
# --------------------------------------------------------------------------- #
def test_v5_t129_rollback_triggers_and_support_escalation():
    """Verify quantified tripwire thresholds and multi-tier on-call contacts."""
    service = default_pilot_go_no_go_service
    board = service.evaluate_board()

    triggers = {t.trigger_id: t for t in board.rollback_triggers}
    assert "TRG-01" in triggers  # 5xx error rate
    assert "TRG-02" in triggers  # latency
    assert "TRG-03" in triggers  # AI faithfulness
    assert "TRG-04" in triggers  # DB connection
    assert "TRG-05" in triggers  # PII

    for t in board.rollback_triggers:
        assert t.threshold
        assert t.measurement_window
        assert t.automated_action
        assert t.severity in ("P0_CRITICAL", "P1_HIGH")

    contacts = {c.tier: c for c in board.support_contacts}
    assert "Tier 1 Support" in contacts
    assert "Tier 2 Incident Commander" in contacts
    assert "Database On-Call" in contacts
    assert "AI Engine Specialist" in contacts
    assert "Epistemic & Historical Escalation" in contacts
    assert "Artisan Partner Liaison" in contacts

    for c in board.support_contacts:
        assert c.contact_value
        assert "min" in c.escalation_sla or "hour" in c.escalation_sla


# --------------------------------------------------------------------------- #
# 6. Negative Abuse Guardrail 1: Open P0 Strictly Blocks Launch
# --------------------------------------------------------------------------- #
def test_v5_t129_negative_abuse_unresolved_p0_blocks_launch():
    """Negative Abuse Invariant: If even ONE P0 issue is OPEN, launch is strictly BLOCKED."""
    service = default_pilot_go_no_go_service

    # Create issues list with an open P0 defect
    custom_issues = [
        BlockingIssueItem(
            issue_id="ISSUE-P0-999",
            title="Active database connection leak causing memory exhaustion",
            severity="P0",
            status="OPEN",  # OPEN P0 DEFECT!
            owner="tech_lead_s1",
            description="Leaked connection locks row in production.",
            resolution_ref=None,
            resolved_at=None,
        ),
        BlockingIssueItem(
            issue_id="ISSUE-P1-001",
            title="Minor styling glitch on mobile Safari",
            severity="P1",
            status="RESOLVED",
            owner="frontend_ux_lead_s4",
            description="Resolved with CSS fix.",
            resolution_ref="commit 123456",
            resolved_at="2026-10-19T10:00:00Z",
        ),
    ]

    eval_input = PilotGoNoGoEvaluateIn(
        release_version="v2026.1.0-rbpc",
        target_environment="staging",
        evaluator_name="Test Evaluator",
        blocking_issues=custom_issues,
    )

    board = service.evaluate_board(input_data=eval_input)

    # Invariant assertions: Launch must be strictly BLOCKED
    assert board.open_p0_count == 1
    assert board.is_launch_blocked is True
    assert board.verdict == "BLOCKED"
    assert any("CRITICAL LAUNCH BLOCKER: P0 issue 'ISSUE-P0-999'" in r for r in board.blocking_reasons)

    # Gatekeeper check: assert_launch_eligibility MUST raise HTTP 422 AppError
    with pytest.raises(AppError) as exc_info:
        service.assert_launch_eligibility(board)

    err = exc_info.value
    assert err.status_code == 422
    assert err.code == "LAUNCH_BLOCKED_P0_UNRESOLVED"
    assert "unresolved P0 issue(s) detected" in err.message


# --------------------------------------------------------------------------- #
# 7. Negative Abuse Guardrail 2: Owner Veto (NO_GO) Blocks Launch
# --------------------------------------------------------------------------- #
def test_v5_t129_negative_abuse_owner_no_go_vote_blocks_launch():
    """Negative Abuse Invariant: If any domain owner votes NO_GO, launch is BLOCKED."""
    service = default_pilot_go_no_go_service

    # Clone canonical decisions but change S2 Historian to NO_GO
    modified_decisions = []
    for d in CANONICAL_OWNER_DECISIONS:
        item = OwnerDecisionItem(**d)
        if item.owner_id == "lead_historian_s2":
            item.decision = "NO_GO"
            item.attestation = "VETO: Disputed citation in story 3 requires archival re-check."
        modified_decisions.append(item)

    eval_input = PilotGoNoGoEvaluateIn(
        release_version="v2026.1.0-rbpc",
        target_environment="staging",
        owner_decisions=modified_decisions,
    )

    board = service.evaluate_board(input_data=eval_input)

    assert board.is_launch_blocked is True
    assert board.verdict == "BLOCKED"
    assert any("OWNER VETO: Domain owner 'TS. Lê Quang Dũng'" in r for r in board.blocking_reasons)

    with pytest.raises(AppError) as exc_info:
        service.assert_launch_eligibility(board)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "LAUNCH_BLOCKED"


# --------------------------------------------------------------------------- #
# 8. Negative Abuse Guardrail 3: Missing Owner Quorum Blocks Launch
# --------------------------------------------------------------------------- #
def test_v5_t129_negative_abuse_missing_owner_quorum_blocks_launch():
    """Negative Abuse Invariant: Missing any required domain owner blocks launch."""
    service = default_pilot_go_no_go_service

    # Omit devops_sre_agent01 from decisions
    partial_decisions = [
        OwnerDecisionItem(**d) for d in CANONICAL_OWNER_DECISIONS if d["owner_id"] != "devops_sre_agent01"
    ]

    eval_input = PilotGoNoGoEvaluateIn(
        release_version="v2026.1.0-rbpc",
        target_environment="staging",
        owner_decisions=partial_decisions,
    )

    board = service.evaluate_board(input_data=eval_input)

    assert board.is_launch_blocked is True
    assert board.verdict == "BLOCKED"
    assert any("INCOMPLETE OWNER QUORUM" in r for r in board.blocking_reasons)
    assert any("devops_sre_agent01" in r for r in board.blocking_reasons)


# --------------------------------------------------------------------------- #
# 9. Database Persistence and Reload
# --------------------------------------------------------------------------- #
def test_v5_t129_database_persistence_and_reload(db_session):
    """Verify that board evaluation records persist and reload accurately from the database."""
    service = default_pilot_go_no_go_service
    board = service.evaluate_board()

    # Save to database
    saved_row = service.save_evaluation(board, db_session)
    assert saved_row.id is not None
    assert saved_row.board_ref == board.board_ref
    assert saved_row.verdict == "GO"
    assert saved_row.is_launch_blocked is False
    assert saved_row.open_p0_count == 0
    assert saved_row.signed_owners_count == 5

    # Reload from database
    reloaded = service.get_evaluation_by_ref(board.board_ref, db_session)
    assert reloaded is not None
    assert reloaded.board_ref == board.board_ref
    assert len(reloaded.owner_decisions) == 5
    assert len(reloaded.blocking_issues) >= 7
    assert len(reloaded.feature_flags) == 6
    assert len(reloaded.rollback_triggers) == 5
    assert len(reloaded.support_contacts) == 6


# --------------------------------------------------------------------------- #
# 10. REST API Endpoints Integration
# --------------------------------------------------------------------------- #
def test_v5_t129_api_endpoints_integration(client: TestClient):
    """Verify REST API endpoints for Pilot Go/No-Go Board."""
    # 1. GET /api/v1/rbpc/go-no-go/board
    res = client.get("/api/v1/rbpc/go-no-go/board")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["verdict"] == "GO"
    assert data["is_launch_blocked"] is False
    assert data["open_p0_count"] == 0
    assert data["signed_owners_count"] == 5

    # 2. POST /api/v1/rbpc/go-no-go/evaluate (Custom Evaluation with Open P0)
    blocked_payload = {
        "release_version": "v2026.1.0-rbpc",
        "target_environment": "staging",
        "evaluator_name": "API Tester",
        "blocking_issues": [
            {
                "issue_id": "ISSUE-P0-API-01",
                "title": "Severe TLS handshake termination bug",
                "severity": "P0",
                "status": "OPEN",
                "owner": "devops_sre_agent01",
                "description": "TLS termination failure under load.",
            }
        ],
    }
    res_eval = client.post("/api/v1/rbpc/go-no-go/evaluate", json=blocked_payload)
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["verdict"] == "BLOCKED"
    assert eval_data["is_launch_blocked"] is True
    assert eval_data["open_p0_count"] == 1
    eval_ref = eval_data["board_ref"]

    # 3. GET /api/v1/rbpc/go-no-go/evaluations/{board_ref}
    res_saved = client.get(f"/api/v1/rbpc/go-no-go/evaluations/{eval_ref}")
    assert res_saved.status_code == 200
    saved_data = res_saved.json()
    assert saved_data["board_ref"] == eval_ref
    assert saved_data["verdict"] == "BLOCKED"

    # Nonexistent ref returns 404
    res_404 = client.get("/api/v1/rbpc/go-no-go/evaluations/NONEXISTENT-REF-999")
    assert res_404.status_code == 404

    # 4. GET /api/v1/rbpc/go-no-go/export (Markdown format)
    res_export_md = client.get("/api/v1/rbpc/go-no-go/export?format=markdown")
    assert res_export_md.status_code == 200
    export_md = res_export_md.json()
    assert export_md["format"] == "markdown"
    assert export_md["verdict"] == "GO"
    assert "# LƯU NIÊN — PILOT GO/NO-GO DECISION BOARD" in export_md["content"]
    assert "Signed Owner Decisions" in export_md["content"]

    # 5. GET /api/v1/rbpc/go-no-go/export (JSON format)
    res_export_json = client.get("/api/v1/rbpc/go-no-go/export?format=json")
    assert res_export_json.status_code == 200
    export_json = res_export_json.json()
    assert export_json["format"] == "json"
    parsed_json = json.loads(export_json["content"])
    assert parsed_json["verdict"] == "GO"


# --------------------------------------------------------------------------- #
# 11. Documentation and Artifact Parity
# --------------------------------------------------------------------------- #
def test_v5_t129_documentation_and_artifact_parity():
    """Verify parity between codebase, RELEASE_CHECKLIST.md, and implementation artifact."""
    root = Path(__file__).resolve().parent.parent.parent

    # 1. Verify docs/rbpc/RELEASE_CHECKLIST.md
    checklist_path = root / "docs" / "rbpc" / "RELEASE_CHECKLIST.md"
    assert checklist_path.exists(), "docs/rbpc/RELEASE_CHECKLIST.md must exist"
    checklist_content = checklist_path.read_text(encoding="utf-8")

    assert "Section IX — Pilot Go/No-Go Board (W12-A09 / Ticket V5-T129)" in checklist_content
    assert "CORE NEGATIVE ABUSE INVARIANT" in checklist_content
    assert "Signed Owner Decisions Matrix" in checklist_content
    assert "Trần Hữu Nam" in checklist_content
    assert "TS. Lê Quang Dũng" in checklist_content
    assert "Nguyễn Minh Hoàng" in checklist_content
    assert "Vũ Thị Lan" in checklist_content
    assert "AGENT 01" in checklist_content
    assert "Authoritative Blocking Issue Register" in checklist_content
    assert "ISSUE-P0-001" in checklist_content
    assert "ISSUE-P0-002" in checklist_content
    assert "ISSUE-P0-003" in checklist_content
    assert "Feature Flag Rollout Plan" in checklist_content
    assert "Quantified Rollback Triggers" in checklist_content
    assert "TRG-01" in checklist_content
    assert "Support Contacts & Incident Escalation Directory" in checklist_content
    assert "FINAL VERDICT: UNANIMOUS GO" in checklist_content

    # 2. Verify artifacts/implementation/W12/W12_A09_pilot_go_no_go_board.json
    artifact_path = root / "artifacts" / "implementation" / "W12" / "W12_A09_pilot_go_no_go_board.json"
    assert artifact_path.exists(), "artifacts/implementation/W12/W12_A09_pilot_go_no_go_board.json must exist"
    artifact_data = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert artifact_data["ticket_id"] == "V5-T129"
    assert artifact_data["wave"] == "W12"
    assert artifact_data["slot"] == "A09"
    assert artifact_data["status"] == "COMPLETED"
    assert artifact_data["implementation_summary"]["overall_verdict"] == "GO"
    assert artifact_data["implementation_summary"]["is_launch_blocked"] is False
    assert artifact_data["implementation_summary"]["signed_owners_quorum"]["required_count"] == 5
    assert artifact_data["implementation_summary"]["signed_owners_quorum"]["signed_count"] == 5
    assert artifact_data["implementation_summary"]["blocking_issue_register"]["open_p0"] == 0
    assert artifact_data["implementation_summary"]["feature_flags_plan"]["total_flags"] == 6
    assert artifact_data["implementation_summary"]["rollback_triggers"]["total_triggers"] == 5
    assert artifact_data["implementation_summary"]["support_contacts"]["total_contacts"] == 6
