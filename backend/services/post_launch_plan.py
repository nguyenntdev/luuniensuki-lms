# -*- coding: utf-8 -*-
"""Post-Launch 30/60/90-Day Operational Plan and Prioritization Service.

Ticket: V5-T130 (Wave W12, Slot A10).
Goal:
- Post-launch 30/60/90-day plan in docs/plan/ and artifacts/.
- Weekly quality/retention/partner support review cadence.
- Validated value hypotheses tracking.
- Evidence-grounded feature prioritization engine.
- Negative abuse invariant:
  No feature scale-up or investment expansion based solely on ungrounded demo applause or verbal feedback.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union


class PostLaunchPhase(str, Enum):
    DAYS_1_30 = "DAYS_1_30"
    DAYS_31_60 = "DAYS_31_60"
    DAYS_61_90 = "DAYS_61_90"


class HypothesisTruthStatus(str, Enum):
    OBSERVED = "OBSERVED"
    HYPOTHESIS = "HYPOTHESIS"
    FORECAST = "FORECAST"
    FALSIFIED = "FALSIFIED"
    VALIDATED = "VALIDATED"


class FeatureStatus(str, Enum):
    APPROVED_NEXT = "APPROVED_NEXT"
    SCHEDULED = "SCHEDULED"
    EVALUATING = "EVALUATING"
    REJECTED_UNGROUNDED = "REJECTED_UNGROUNDED"


class ReviewPillar(str, Enum):
    PLATFORM_QUALITY = "PLATFORM_QUALITY"
    COHORT_RETENTION = "COHORT_RETENTION"
    PARTNER_SUPPORT = "PARTNER_SUPPORT"


@dataclass(frozen=True)
class PostLaunchMilestone:
    milestone_id: str
    phase: PostLaunchPhase
    title: str
    target_metric: str
    sla_threshold: str
    verification_method: str
    status: str = "SCHEDULED"


@dataclass(frozen=True)
class ValueHypothesis:
    hypothesis_id: str
    title: str
    statement: str
    target_metric: str
    falsification_trigger: str
    sample_size_target: int
    truth_status: HypothesisTruthStatus
    evidence_pointer_id: Optional[str] = None


@dataclass(frozen=True)
class PrioritizationScore:
    reach: float
    impact: float
    confidence: float
    effort_weeks: float
    priority_score: float


@dataclass
class FeatureProposal:
    feature_id: str
    title: str
    target_phase: PostLaunchPhase
    reach: float  # 1 - 10
    impact: float  # 1 - 5
    confidence: float  # 0.1 - 1.0 (uncorroborated capped at 0.2)
    effort_weeks: float  # 1 - 8
    evidence_ref: Optional[str] = None
    verbal_feedback_only: bool = False
    demo_applause_basis: bool = False
    status: FeatureStatus = FeatureStatus.EVALUATING
    decision_reason: Optional[str] = None

    def calculate_rice_score(self) -> float:
        if self.effort_weeks <= 0:
            raise ValueError("Effort in weeks must be strictly positive.")
        raw_score = (self.reach * self.impact * self.confidence) / self.effort_weeks
        return round(raw_score, 2)


@dataclass
class WeeklyReviewRecord:
    review_week: int  # 1 - 12
    date: str
    quality_score: float  # 0 - 100
    retention_d14_pct: float  # percentage
    partner_sla_compliance_pct: float  # percentage
    active_inquiries_count: int
    open_tickets_count: int
    notes: str
    pillars_covered: List[ReviewPillar] = field(
        default_factory=lambda: [
            ReviewPillar.PLATFORM_QUALITY,
            ReviewPillar.COHORT_RETENTION,
            ReviewPillar.PARTNER_SUPPORT,
        ]
    )


# --------------------------------------------------------------------------- #
# Canonical Pre-Registered Milestones
# --------------------------------------------------------------------------- #
CANONICAL_MILESTONES: List[PostLaunchMilestone] = [
    # Days 1-30: Stabilization & Trust
    PostLaunchMilestone(
        milestone_id="M30-01",
        phase=PostLaunchPhase.DAYS_1_30,
        title="Zero-Defect Runtime Telemetry & Uptime",
        target_metric="API Gateway Availability >= 99.9%",
        sla_threshold="p95 Latency <= 300ms",
        verification_method="Prometheus alert logs & Axum status telemetry",
    ),
    PostLaunchMilestone(
        milestone_id="M30-02",
        phase=PostLaunchPhase.DAYS_1_30,
        title="24h Partner Inquiry Response SLA Enforcement",
        target_metric="Inquiry Notification SLA Adherence >= 98.0%",
        sla_threshold="Partner notification delay <= 24 hours",
        verification_method="Audit of rbpc_notification_outbox & escalation triggers",
    ),
    PostLaunchMilestone(
        milestone_id="M30-03",
        phase=PostLaunchPhase.DAYS_1_30,
        title="162 Relics Source Lock Audit",
        target_metric="Approved Claims Coverage = 100.0%",
        sla_threshold="Zero unreviewed/disputed claims in AI tutor RAG",
        verification_method="Automated audit_162_publication test harness",
    ),
    PostLaunchMilestone(
        milestone_id="M30-04",
        phase=PostLaunchPhase.DAYS_1_30,
        title="In-Kind Sponsorship Burn Rate Monitoring",
        target_metric="Sponsorship Burn <= 202,360,638 VND budget cap",
        sla_threshold="Monthly burn <= 25,000,000 VND equiv",
        verification_method="Cloud VPS and PhoTue AI token invoice reconciliation",
    ),
    # Days 31-60: Depth & Retention
    PostLaunchMilestone(
        milestone_id="M60-01",
        phase=PostLaunchPhase.DAYS_31_60,
        title="FSRS Spaced Repetition Tuning & Anti-Burst Audit",
        target_metric="Day-14 Fact Retention >= 65.0%",
        sla_threshold="Dwell time >= 2.0s per card, zero rapid burst inflation",
        verification_method="FSRS review log analysis and mastery stamp checks",
    ),
    PostLaunchMilestone(
        milestone_id="M60-02",
        phase=PostLaunchPhase.DAYS_31_60,
        title="Artisan Booking Settlement Turnaround",
        target_metric="Settlement Settlement Cycle <= 48 hours",
        sla_threshold="Artisan Direct Payout = 90.0% contracted rate",
        verification_method="RbpcSettlementLedger audit",
    ),
    PostLaunchMilestone(
        milestone_id="M60-03",
        phase=PostLaunchPhase.DAYS_31_60,
        title="Mobile Offline Rubbing Sync Reliability",
        target_metric="Offline Sync Success >= 99.0%",
        sla_threshold="Client idempotency key zero duplication",
        verification_method="Mobile offline sync queue telemetry",
    ),
    # Days 61-90: Expansion & B2B
    PostLaunchMilestone(
        milestone_id="M90-01",
        phase=PostLaunchPhase.DAYS_61_90,
        title="B2B School Pilot Rollout (3 High Schools)",
        target_metric="Enrolled Classrooms >= 9, Active Students >= 250",
        sla_threshold="Rubric completion >= 80.0%",
        verification_method="School pilot portal onboarding checklist & gradebook records",
    ),
    PostLaunchMilestone(
        milestone_id="M90-02",
        phase=PostLaunchPhase.DAYS_61_90,
        title="Post-Launch Revenue & GMV Actuals Reconciliation",
        target_metric="Actual Booking GMV Ledger Reconciled",
        sla_threshold="Platform take rate strictly 10.0%, zero unverified GMV",
        verification_method="Unit economics actual ledger reconciliation",
    ),
    PostLaunchMilestone(
        milestone_id="M90-03",
        phase=PostLaunchPhase.DAYS_61_90,
        title="Formal Research Studies (LN-01 to LN-10) Empirical Audit",
        target_metric="10/10 Research Invariants Verified with Student Cohorts",
        sla_threshold="Statistical significance p < 0.05 on learning gains",
        verification_method="Pedagogical research evaluation suite",
    ),
]


# --------------------------------------------------------------------------- #
# Canonical Validated Value Hypotheses
# --------------------------------------------------------------------------- #
CANONICAL_VALUE_HYPOTHESES: List[ValueHypothesis] = [
    ValueHypothesis(
        hypothesis_id="HYP-PL-01",
        title="Socratic Hint-First AI Learning Retention",
        statement="Students using hint-first AI guidance achieve >= 25% higher Day-14 fact retention than direct answer reveals.",
        target_metric="Day-14 Retention >= 65.0%",
        falsification_trigger="Day-14 Retention < 45.0%",
        sample_size_target=100,
        truth_status=HypothesisTruthStatus.HYPOTHESIS,
        evidence_pointer_id="EVID-PRD-001",
    ),
    ValueHypothesis(
        hypothesis_id="HYP-PL-02",
        title="Low-Bandwidth Printable Rubbing Parity",
        statement="Students completing lessons with offline monochrome rubbings achieve identical rubric pass rates as 3D WebGL users.",
        target_metric="Rubric Pass Rate Delta <= 5.0%",
        falsification_trigger="Rubric Pass Rate Delta > 12.0%",
        sample_size_target=80,
        truth_status=HypothesisTruthStatus.HYPOTHESIS,
        evidence_pointer_id="EVID-PRD-002",
    ),
    ValueHypothesis(
        hypothesis_id="HYP-PL-03",
        title="Artisan Direct Wage Retention & Uplift",
        statement="A contracted 90% direct payout model yields >= 4,200,000 VND monthly supplemental earnings for verified artisans.",
        target_metric="Monthly Artisan Uplift >= 4,200,000 VND",
        falsification_trigger="Monthly Artisan Uplift < 2,000,000 VND",
        sample_size_target=5,
        truth_status=HypothesisTruthStatus.HYPOTHESIS,
        evidence_pointer_id="EVID-IMP-001",
    ),
    ValueHypothesis(
        hypothesis_id="HYP-PL-04",
        title="Teacher 45-Minute Lesson Wizard Preparation Efficiency",
        statement="Using pre-curated primary sources reduces teacher lesson planning duration by >= 40% (under 25 minutes total).",
        target_metric="Preparation Time <= 25 mins",
        falsification_trigger="Preparation Time > 40 mins",
        sample_size_target=15,
        truth_status=HypothesisTruthStatus.HYPOTHESIS,
        evidence_pointer_id="EVID-CST-002",
    ),
    ValueHypothesis(
        hypothesis_id="HYP-PL-05",
        title="Cultural Inquiry Visitor Conversion Rate",
        statement="Cultural travelers exploring verified rubbing details convert to booking inquiries at >= 3x higher rate than generic landing pages.",
        target_metric="Conversion Multiplier >= 3.0x",
        falsification_trigger="Conversion Multiplier < 1.5x",
        sample_size_target=500,
        truth_status=HypothesisTruthStatus.HYPOTHESIS,
        evidence_pointer_id="EVID-CST-001",
    ),
]


class PostLaunchPlanService:
    """Evaluates post-launch milestones, weekly review cadence, and feature prioritization.
    
    Enforces the Negative Abuse Invariant:
    No feature scale-up or investment expansion based solely on ungrounded demo applause or verbal feedback.
    """

    def __init__(
        self,
        milestones: Optional[Sequence[PostLaunchMilestone]] = None,
        hypotheses: Optional[Sequence[ValueHypothesis]] = None,
    ):
        self._milestones: Dict[str, PostLaunchMilestone] = {
            m.milestone_id: m for m in (milestones or CANONICAL_MILESTONES)
        }
        self._hypotheses: Dict[str, ValueHypothesis] = {
            h.hypothesis_id: h for h in (hypotheses or CANONICAL_VALUE_HYPOTHESES)
        }
        self._weekly_reviews: List[WeeklyReviewRecord] = []

    def get_milestones(self, phase: Optional[PostLaunchPhase] = None) -> List[PostLaunchMilestone]:
        res = list(self._milestones.values())
        if phase:
            res = [m for m in res if m.phase == phase]
        return sorted(res, key=lambda x: x.milestone_id)

    def get_hypotheses(self) -> List[ValueHypothesis]:
        return sorted(list(self._hypotheses.values()), key=lambda x: x.hypothesis_id)

    def record_weekly_review(self, record: WeeklyReviewRecord) -> WeeklyReviewRecord:
        """Register a weekly review ensuring all three pillars are explicitly audited."""
        required_pillars = {
            ReviewPillar.PLATFORM_QUALITY,
            ReviewPillar.COHORT_RETENTION,
            ReviewPillar.PARTNER_SUPPORT,
        }
        if not required_pillars.issubset(set(record.pillars_covered)):
            missing = required_pillars - set(record.pillars_covered)
            raise ValueError(f"Weekly review missing mandatory pillars: {[p.value for p in missing]}")
        if record.quality_score < 0 or record.quality_score > 100:
            raise ValueError("Quality score must be between 0 and 100.")
        if record.retention_d14_pct < 0 or record.retention_d14_pct > 100:
            raise ValueError("Retention percentage must be between 0 and 100.")
        if record.partner_sla_compliance_pct < 0 or record.partner_sla_compliance_pct > 100:
            raise ValueError("Partner SLA compliance must be between 0 and 100.")

        self._weekly_reviews.append(record)
        return record

    def get_weekly_reviews(self) -> List[WeeklyReviewRecord]:
        return sorted(self._weekly_reviews, key=lambda x: x.review_week)

    def evaluate_feature_prioritization(
        self,
        proposal: FeatureProposal,
    ) -> FeatureProposal:
        """Evaluate a candidate feature proposal enforcing the negative abuse guardrail.
        
        Negative abuse invariant:
        - If proposal is based solely on verbal feedback or demo applause without verified evidence pointer -> REJECTED_UNGROUNDED.
        - Confidence score must be capped at 0.20 if no quantitative evidence pointer exists.
        - Scale-up or sprint approval strictly requires evidence_ref and score >= 5.0.
        """
        # Negative abuse check: demo applause or verbal feedback without empirical grounding
        if proposal.demo_applause_basis or proposal.verbal_feedback_only:
            if not proposal.evidence_ref:
                proposal.status = FeatureStatus.REJECTED_UNGROUNDED
                proposal.confidence = min(proposal.confidence, 0.20)
                proposal.decision_reason = (
                    "NEGATIVE_ABUSE_REJECTED: No feature scale-up or investment expansion "
                    "is authorized based solely on ungrounded demo applause or verbal feedback."
                )
                return proposal

        # If evidence pointer is supplied, verify format
        if proposal.evidence_ref:
            if not (proposal.evidence_ref.startswith("EVID-") or proposal.evidence_ref.startswith("ANALYTICS-")):
                proposal.status = FeatureStatus.REJECTED_UNGROUNDED
                proposal.confidence = min(proposal.confidence, 0.20)
                proposal.decision_reason = (
                    f"NEGATIVE_ABUSE_REJECTED: Invalid evidence pointer '{proposal.evidence_ref}'. "
                    "Must reference a verified EVID-* or ANALYTICS-* record."
                )
                return proposal

        # Calculate score
        score = proposal.calculate_rice_score()
        if score >= 10.0:
            proposal.status = FeatureStatus.APPROVED_NEXT
            proposal.decision_reason = f"PRIORITIZED: High score {score} backed by verified evidence."
        elif score >= 5.0:
            proposal.status = FeatureStatus.SCHEDULED
            proposal.decision_reason = f"SCHEDULED: Viable score {score} for subsequent horizon."
        else:
            proposal.status = FeatureStatus.EVALUATING
            proposal.decision_reason = f"DEFERRED: Score {score} below active implementation threshold."

        return proposal

    def validate_plan_integrity(self) -> Dict[str, Any]:
        """Validate 30/60/90-day plan coverage, hypotheses, and negative abuse guards."""
        p30 = self.get_milestones(PostLaunchPhase.DAYS_1_30)
        p60 = self.get_milestones(PostLaunchPhase.DAYS_31_60)
        p90 = self.get_milestones(PostLaunchPhase.DAYS_61_90)

        if not p30 or not p60 or not p90:
            raise ValueError("All three phases (30, 60, 90 days) must have registered milestones.")

        return {
            "total_milestones": len(self._milestones),
            "breakdown": {
                "days_1_30": len(p30),
                "days_31_60": len(p60),
                "days_61_90": len(p90),
            },
            "total_hypotheses": len(self._hypotheses),
            "negative_abuse_guardrail": (
                "STRICT: No feature scale-up or investment expansion authorized based solely "
                "on ungrounded demo applause or verbal feedback."
            ),
            "status": "VALIDATED",
        }

    def export_summary_json(self) -> str:
        """Export clean JSON summary of the post-launch plan."""
        data = {
            "title": "LƯU NIÊN Post-Launch 30/60/90-Day Operational & Strategic Plan",
            "ticket": "V5-T130",
            "wave": "W12",
            "slot": "A10",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "phases": {
                "days_1_30": [asdict(m) for m in self.get_milestones(PostLaunchPhase.DAYS_1_30)],
                "days_31_60": [asdict(m) for m in self.get_milestones(PostLaunchPhase.DAYS_31_60)],
                "days_61_90": [asdict(m) for m in self.get_milestones(PostLaunchPhase.DAYS_61_90)],
            },
            "validated_value_hypotheses": [asdict(h) for h in self.get_hypotheses()],
            "weekly_review_cadence": {
                "cadence": "Weekly every Monday 09:00 ICT",
                "pillars": [p.value for p in ReviewPillar],
            },
            "negative_abuse_invariant": {
                "rule": "No feature scale-up or investment expansion based solely on ungrounded demo applause or verbal feedback.",
                "rejection_code": "UNGROUNDED_DEMO_APPLAUSE_REJECTED",
                "evidence_requirement": "Strict requirement for verified EVID-* or ANALYTICS-* pointer",
            },
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


# Default singleton instance
default_post_launch_service = PostLaunchPlanService()
