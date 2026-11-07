# -*- coding: utf-8 -*-
"""V5-T130 (Wave W12, Slot A10): Post-Launch 30/60/90-Day Plan Test Suite.

Audits and verifies:
1. 30/60/90-Day Plan Coverage & Architecture:
   - Days 1-30: Operational Stabilization & Trust Verification.
   - Days 31-60: Learning Depth & Cohort Retention.
   - Days 61-90: Sustainable Expansion & B2B School Rollout.
2. Weekly Review Cadence (Quality, Retention, Partner Support):
   - Pillar coverage: PLATFORM_QUALITY, COHORT_RETENTION, PARTNER_SUPPORT.
   - Boundary validations on quality scores, D-14 retention, and SLA compliance.
3. Validated Value Hypotheses:
   - Covers core pedagogical and marketplace hypotheses (HYP-PL-01 to HYP-PL-05).
   - Pre-registered falsification triggers and sample sizes.
4. Feature Prioritization & Decision Engine:
   - Objective RICE score calculation.
   - Transition between APPROVED_NEXT, SCHEDULED, and EVALUATING.
5. NEGATIVE ABUSE INVARIANTS:
   - No feature scale-up or investment expansion based solely on ungrounded demo applause.
   - No feature scale-up based solely on verbal feedback or uncorroborated sentiment.
   - Proposals with verbal/applause basis without verified evidence pointer are strictly REJECTED_UNGROUNDED.
   - Enforces valid evidence reference format (EVID-* or ANALYTICS-*).
6. Documentation and Artifact Parity:
   - docs/plan/POST_LAUNCH_30_60_90_PLAN.md existence and structural alignment.
   - Export utilities and artifact integrity.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from backend.services.post_launch_plan import (
    CANONICAL_MILESTONES,
    CANONICAL_VALUE_HYPOTHESES,
    FeatureProposal,
    FeatureStatus,
    HypothesisTruthStatus,
    PostLaunchMilestone,
    PostLaunchPhase,
    PostLaunchPlanService,
    ReviewPillar,
    ValueHypothesis,
    WeeklyReviewRecord,
    default_post_launch_service,
)


# --------------------------------------------------------------------------- #
# 1. 30/60/90-Day Plan Milestone Architecture & Coverage
# --------------------------------------------------------------------------- #
def test_v5_t130_milestones_30_60_90_coverage():
    """Verify milestones span all 3 post-launch phases with verified metrics."""
    service = default_post_launch_service
    milestones = service.get_milestones()
    assert len(milestones) >= 10, f"Expected at least 10 milestones, found {len(milestones)}"

    p30 = service.get_milestones(PostLaunchPhase.DAYS_1_30)
    p60 = service.get_milestones(PostLaunchPhase.DAYS_31_60)
    p90 = service.get_milestones(PostLaunchPhase.DAYS_61_90)

    assert len(p30) >= 4, f"Days 1-30 requires >= 4 milestones, found {len(p30)}"
    assert len(p60) >= 3, f"Days 31-60 requires >= 3 milestones, found {len(p60)}"
    assert len(p90) >= 3, f"Days 61-90 requires >= 3 milestones, found {len(p90)}"

    # Check critical invariants in milestones
    m30_02 = next(m for m in p30 if m.milestone_id == "M30-02")
    assert "24h" in m30_02.title
    assert "SLA" in m30_02.target_metric

    m30_03 = next(m for m in p30 if m.milestone_id == "M30-03")
    assert "162 Relics" in m30_03.title
    assert "100.0%" in m30_03.target_metric

    m30_04 = next(m for m in p30 if m.milestone_id == "M30-04")
    assert "202,360,638 VND" in m30_04.target_metric

    m60_02 = next(m for m in p60 if m.milestone_id == "M60-02")
    assert "90.0%" in m60_02.sla_threshold

    m90_01 = next(m for m in p90 if m.milestone_id == "M90-01")
    assert "3 High Schools" in m90_01.title


# --------------------------------------------------------------------------- #
# 2. Weekly Review Cadence (Quality, Retention, Partner Support)
# --------------------------------------------------------------------------- #
def test_v5_t130_weekly_review_cadence_and_pillar_enforcement():
    """Verify weekly review records enforce all 3 pillars and validate boundaries."""
    service = PostLaunchPlanService()

    valid_record = WeeklyReviewRecord(
        review_week=1,
        date="2026-11-09",
        quality_score=99.2,
        retention_d14_pct=68.5,
        partner_sla_compliance_pct=100.0,
        active_inquiries_count=12,
        open_tickets_count=1,
        notes="Week 1 post-launch: zero unhandled 5xx exceptions, 100% partner notification SLA.",
        pillars_covered=[
            ReviewPillar.PLATFORM_QUALITY,
            ReviewPillar.COHORT_RETENTION,
            ReviewPillar.PARTNER_SUPPORT,
        ],
    )
    saved = service.record_weekly_review(valid_record)
    assert saved.review_week == 1
    assert len(service.get_weekly_reviews()) == 1

    # Incomplete pillars must raise ValueError
    incomplete_record = WeeklyReviewRecord(
        review_week=2,
        date="2026-11-16",
        quality_score=95.0,
        retention_d14_pct=65.0,
        partner_sla_compliance_pct=98.0,
        active_inquiries_count=18,
        open_tickets_count=2,
        notes="Missing partner support pillar evaluation",
        pillars_covered=[
            ReviewPillar.PLATFORM_QUALITY,
            ReviewPillar.COHORT_RETENTION,
        ],
    )
    with pytest.raises(ValueError, match="missing mandatory pillars"):
        service.record_weekly_review(incomplete_record)

    # Out of range scores must raise ValueError
    invalid_score_record = WeeklyReviewRecord(
        review_week=3,
        date="2026-11-23",
        quality_score=150.0,  # Invalid
        retention_d14_pct=70.0,
        partner_sla_compliance_pct=99.0,
        active_inquiries_count=20,
        open_tickets_count=0,
        notes="Invalid score range test",
    )
    with pytest.raises(ValueError, match="Quality score must be between 0 and 100"):
        service.record_weekly_review(invalid_score_record)


# --------------------------------------------------------------------------- #
# 3. Validated Value Hypotheses
# --------------------------------------------------------------------------- #
def test_v5_t130_validated_value_hypotheses_integrity():
    """Verify 5 core hypotheses exist with testable metrics, triggers, and evidence links."""
    service = default_post_launch_service
    hypotheses = service.get_hypotheses()
    assert len(hypotheses) == 5, f"Expected 5 hypotheses, found {len(hypotheses)}"

    hyp_ids = {h.hypothesis_id for h in hypotheses}
    assert hyp_ids == {"HYP-PL-01", "HYP-PL-02", "HYP-PL-03", "HYP-PL-04", "HYP-PL-05"}

    for h in hypotheses:
        assert h.hypothesis_id.startswith("HYP-PL-")
        assert h.title
        assert h.statement
        assert h.target_metric
        assert h.falsification_trigger
        assert h.sample_size_target > 0
        assert h.truth_status in {HypothesisTruthStatus.HYPOTHESIS, HypothesisTruthStatus.OBSERVED}
        assert h.evidence_pointer_id is not None
        assert h.evidence_pointer_id.startswith("EVID-")

    # Specific checks
    h3 = next(h for h in hypotheses if h.hypothesis_id == "HYP-PL-03")
    assert "4,200,000 VND" in h3.target_metric
    assert h3.evidence_pointer_id == "EVID-IMP-001"


# --------------------------------------------------------------------------- #
# 4. Feature Prioritization Framework & Decision Matrix
# --------------------------------------------------------------------------- #
def test_v5_t130_feature_prioritization_engine():
    """Verify objective RICE scoring and evidence-backed prioritization."""
    service = default_post_launch_service

    # Grounded high-priority operational feature
    grounded_feature = FeatureProposal(
        feature_id="FEAT-01",
        title="Offline Sync Conflict Resolution v2",
        target_phase=PostLaunchPhase.DAYS_31_60,
        reach=8.0,
        impact=4.0,
        confidence=0.90,  # Valid evidence backed
        effort_weeks=2.0,
        evidence_ref="EVID-PRD-001",
        verbal_feedback_only=False,
        demo_applause_basis=False,
    )
    result = service.evaluate_feature_prioritization(grounded_feature)
    assert result.status == FeatureStatus.APPROVED_NEXT
    assert result.calculate_rice_score() == 14.40
    assert "PRIORITIZED" in result.decision_reason

    # Grounded scheduled feature
    scheduled_feature = FeatureProposal(
        feature_id="FEAT-03",
        title="Multi-Urn Comparative Lens (3D Split)",
        target_phase=PostLaunchPhase.DAYS_61_90,
        reach=7.0,
        impact=3.0,
        confidence=0.80,
        effort_weeks=3.0,
        evidence_ref="EVID-PRD-002",
        verbal_feedback_only=False,
        demo_applause_basis=False,
    )
    result = service.evaluate_feature_prioritization(scheduled_feature)
    assert result.status == FeatureStatus.SCHEDULED
    assert result.calculate_rice_score() == 5.60


# --------------------------------------------------------------------------- #
# 5. NEGATIVE ABUSE INVARIANTS: Rejection of Ungrounded Scale-Ups
# --------------------------------------------------------------------------- #
def test_v5_t130_negative_abuse_demo_applause_rejection():
    """NEGATIVE ABUSE INVARIANT:
    No feature scale-up or investment expansion based solely on ungrounded demo applause.
    Any proposal with demo_applause_basis=True and no verified evidence_ref MUST be REJECTED.
    """
    service = default_post_launch_service

    speculative_applause_proposal = FeatureProposal(
        feature_id="FEAT-APPLAUSE-01",
        title="Speculative VR Metaverse Exhibition Dome",
        target_phase=PostLaunchPhase.DAYS_61_90,
        reach=9.0,
        impact=5.0,
        confidence=0.95,  # Inflated confidence from audience cheering
        effort_weeks=8.0,
        evidence_ref=None,  # No empirical evidence pointer
        verbal_feedback_only=False,
        demo_applause_basis=True,  # Based on pitch competition applause
    )

    evaluated = service.evaluate_feature_prioritization(speculative_applause_proposal)
    assert evaluated.status == FeatureStatus.REJECTED_UNGROUNDED
    assert evaluated.confidence <= 0.20, "Ungrounded confidence must be capped at 0.20"
    assert "NEGATIVE_ABUSE_REJECTED" in evaluated.decision_reason
    assert "ungrounded demo applause" in evaluated.decision_reason.lower()


def test_v5_t130_negative_abuse_verbal_feedback_rejection():
    """NEGATIVE ABUSE INVARIANT:
    No feature scale-up based solely on casual verbal feedback or comments.
    """
    service = default_post_launch_service

    verbal_proposal = FeatureProposal(
        feature_id="FEAT-VERBAL-01",
        title="AI Voice Clone for Historical Dynastic Emperors",
        target_phase=PostLaunchPhase.DAYS_61_90,
        reach=4.0,
        impact=3.0,
        confidence=0.80,
        effort_weeks=6.0,
        evidence_ref=None,
        verbal_feedback_only=True,  # Based on verbal remark from visitor
        demo_applause_basis=False,
    )

    evaluated = service.evaluate_feature_prioritization(verbal_proposal)
    assert evaluated.status == FeatureStatus.REJECTED_UNGROUNDED
    assert evaluated.confidence <= 0.20
    assert "NEGATIVE_ABUSE_REJECTED" in evaluated.decision_reason
    assert "verbal feedback" in evaluated.decision_reason.lower()


def test_v5_t130_negative_abuse_invalid_evidence_pointer_rejection():
    """NEGATIVE ABUSE INVARIANT:
    Referencing a fake, arbitrary, or unverified evidence pointer must be rejected.
    """
    service = default_post_launch_service

    fake_pointer_proposal = FeatureProposal(
        feature_id="FEAT-FAKE-01",
        title="Speculative Automated Tour Booking Broker",
        target_phase=PostLaunchPhase.DAYS_61_90,
        reach=6.0,
        impact=4.0,
        confidence=0.70,
        effort_weeks=3.0,
        evidence_ref="INVALID-POINTER-123",  # Must be EVID-* or ANALYTICS-*
        verbal_feedback_only=False,
        demo_applause_basis=False,
    )

    evaluated = service.evaluate_feature_prioritization(fake_pointer_proposal)
    assert evaluated.status == FeatureStatus.REJECTED_UNGROUNDED
    assert "Invalid evidence pointer" in evaluated.decision_reason


# --------------------------------------------------------------------------- #
# 6. Documentation and Artifact Integrity Parity
# --------------------------------------------------------------------------- #
def test_v5_t130_documentation_parity():
    """Verify docs/plan/POST_LAUNCH_30_60_90_PLAN.md exists and contains all required sections."""
    repo_root = Path(__file__).resolve().parents[2]
    doc_path = repo_root / "docs" / "plan" / "POST_LAUNCH_30_60_90_PLAN.md"

    assert doc_path.exists(), f"Plan document {doc_path} must exist"
    content = doc_path.read_text(encoding="utf-8")

    # Invariants and sections check
    assert "PLAN-POST-LAUNCH-30-60-90" in content
    assert "V5-T130" in content
    assert "W12-A10" in content
    assert "STABILIZATION & TRUST" in content
    assert "DEPTH & RETENTION" in content
    assert "EXPANSION & B2B" in content
    assert "CRITICAL INVARIANT" in content
    assert "ungrounded demo applause" in content.lower()
    assert "202,360,638 VND" in content
    assert "HYP-PL-01" in content
    assert "FEAT-01" in content


def test_v5_t130_service_validation_and_json_export():
    """Verify service validation logic and JSON export formatting."""
    service = default_post_launch_service
    report = service.validate_plan_integrity()

    assert report["status"] == "VALIDATED"
    assert report["total_milestones"] >= 10
    assert report["total_hypotheses"] == 5
    assert "STRICT" in report["negative_abuse_guardrail"]

    exported_json = service.export_summary_json()
    assert isinstance(exported_json, str)
    parsed = json.loads(exported_json)
    assert parsed["ticket"] == "V5-T130"
    assert "phases" in parsed
    assert len(parsed["phases"]["days_1_30"]) >= 4
    assert len(parsed["phases"]["days_31_60"]) >= 3
    assert len(parsed["phases"]["days_61_90"]) >= 3
    assert "negative_abuse_invariant" in parsed
    assert parsed["negative_abuse_invariant"]["rejection_code"] == "UNGROUNDED_DEMO_APPLAUSE_REJECTED"
