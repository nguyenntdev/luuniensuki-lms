# -*- coding: utf-8 -*-
"""Research Teacher Analytics - Intervention Rules Engine (Study LN-09).

Theory: Learning analytics; teacher orchestration; formative assessment.
Research Context: Diễn giải dữ liệu học tập thành gợi ý can thiệp dạy học GDĐP có giải thích cho giáo viên.

Pedagogical Invariants:
- INV-LN-09-01: Không suy ra người học kém từ dữ liệu thiếu.
- INV-LN-09-02: Khuyến nghị có căn cứ phải truy ngược được tới nhiệm vụ và yêu cầu cần đạt.
- INV-LN-09-03: Gợi ý không tự động thành điểm hay hoạt động bắt buộc nếu giáo viên chưa chấp thuận.
- INV-LN-09-04: Không dùng tên thật và điểm thật trong báo cáo benchmark synthetic.
- INV-LN-09-05: Điều kiện mâu thuẫn tín hiệu và không đủ dữ liệu phải được hiển thị tường minh, không ẩn.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.domain.instructional_recommendations import (
    DecisionCode,
    DecisionSupportCard,
    INSTRUCTIONAL_ACTION_CATALOG,
    ReasonCode,
    evaluate_instructional_recommendation,
)

POLICY_VERSION_INTERVENTION = "study-v1"
POLICY_VERSION_BASELINE = "baseline-v1.0"
POLICY_VERSION_ABLATION = "ablation-v1.0"


@dataclass(frozen=True)
class InterventionEvaluationResult:
    decision: str
    reason_codes: List[str]
    policy_version: str
    action_proposed: bool
    abstention_appropriate: bool
    intervention_traceable: bool
    candidate_intervention: Optional[str] = None
    rationale: Optional[str] = None
    observables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "policy_version": self.policy_version,
            "action_proposed": self.action_proposed,
            "abstention_appropriate": self.abstention_appropriate,
            "intervention_traceable": self.intervention_traceable,
            "candidate_intervention": self.candidate_intervention,
            "rationale": self.rationale,
            "research_only": True,
        }
        res.update(self.observables)
        return res


def evaluate_baseline_rules(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> InterventionEvaluationResult:
    """Baseline policy: Standard dashboard heuristics that display raw progress/scores

    or generate generic ungrounded recommendations without source validation,
    freshness constraints, or explicit abstention.
    """
    config = config or {}
    candidate = scenario_input.get("candidate_intervention") or "additional_source_comparison_activity"
    descriptive_only = config.get("descriptive_only", False)

    if descriptive_only:
        # Simple dashboard with no recommendations
        return InterventionEvaluationResult(
            decision=DecisionCode.descriptive_summary_only.value,
            reason_codes=[ReasonCode.descriptive_only_no_action.value],
            policy_version=POLICY_VERSION_BASELINE,
            action_proposed=False,
            abstention_appropriate=False,
            intervention_traceable=False,
            candidate_intervention=None,
            rationale="Chỉ báo cáo tiến độ mô tả, không đưa ra hành động can thiệp.",
            observables={
                "mode": "baseline",
                "evidence_count": len(scenario_input.get("learning_evidence") or []),
                "k_anonymity_satisfied": True,
            },
        )

    # Standard baseline: blindly proposes candidate intervention without verifying
    # evidence validity, consistency, source grounding, or observation freshness.
    evidence_list = scenario_input.get("learning_evidence") or []
    age_days = scenario_input.get("observation_age_days", 0)

    return InterventionEvaluationResult(
        decision=DecisionCode.propose_explained_action.value,
        reason_codes=["baseline_ungrounded_heuristic"],
        policy_version=POLICY_VERSION_BASELINE,
        action_proposed=True,
        abstention_appropriate=False,
        intervention_traceable=False,  # Lacks rigorous evidence traceability
        candidate_intervention=candidate,
        rationale=f"Gợi ý mặc định theo thuật toán thống kê: {candidate}",
        observables={
            "mode": "baseline",
            "evidence_count": len(evidence_list),
            "observation_age_days": age_days,
            "k_anonymity_satisfied": True,
            "source_verification_bypassed": True,
            "freshness_check_bypassed": True,
        },
    )


def evaluate_intervention_rules(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> InterventionEvaluationResult:
    """Intervention policy: Rigorous evidence-grounded decision rules enforcing:

    1. Minimum evidence availability (INV-LN-09-01: no low-mastery inference from missing data)
    2. Signal consistency (INV-LN-09-05: explicit abstention on unresolved conflict)
    3. Source and assessment task verification (INV-LN-09-02: unverified source => abstention)
    4. Data freshness (stale data > 30 days => request refresh)
    5. Privacy protection via k-anonymity (n >= 5)
    6. Pedagogical curriculum traceability for every proposed action
    """
    config = config or {}
    max_staleness = config.get("max_staleness_days", 30)
    k_threshold = config.get("k_threshold", 5)

    card: DecisionSupportCard = evaluate_instructional_recommendation(
        scenario_input,
        max_staleness_days=max_staleness,
        k_threshold=k_threshold,
        allow_unverified=False,
        allow_conflicts=False,
        allow_stale=False,
        descriptive_only=False,
        include_rationale=True,
    )

    evidence_list = scenario_input.get("learning_evidence") or []
    verified_count = sum(1 for ev in evidence_list if ev.get("verified", False))

    observables: Dict[str, Any] = {
        "mode": "intervention",
        "evidence_count": len(evidence_list),
        "verified_evidence_count": verified_count,
        "observation_age_days": card.data_freshness_days,
        "k_anonymity_satisfied": card.k_anonymity_satisfied,
        "limitations": list(card.limitations),
        "curriculum_anchor_id": card.action.curriculum_anchor_id if card.action else None,
        "teaching_action_id": card.action.id if card.action else None,
    }

    return InterventionEvaluationResult(
        decision=card.decision,
        reason_codes=card.reason_codes,
        policy_version=POLICY_VERSION_INTERVENTION,
        action_proposed=card.action_proposed,
        abstention_appropriate=card.abstention_appropriate,
        intervention_traceable=card.intervention_traceable,
        candidate_intervention=(
            card.action.action_type if card.action else scenario_input.get("candidate_intervention")
        ),
        rationale=card.rationale,
        observables=observables,
    )


def evaluate_ablation_rules(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> InterventionEvaluationResult:
    """Ablation policy testing specific policy components:

    - 'descriptive_only' (A1): Dashboard without any suggestions.
    - 'no_freshness_source' (A2): Removes freshness and source verification constraints.
    - 'no_rationale' (A3): Removes pedagogical explanation and curriculum anchoring.
    """
    config = config or {}
    ablation_type = config.get("ablation_type", "no_freshness_source")

    if ablation_type == "descriptive_only" or config.get("descriptive_only", False):
        card = evaluate_instructional_recommendation(
            scenario_input,
            descriptive_only=True,
        )
    elif ablation_type == "no_freshness_source" or config.get("no_freshness_source", False):
        # Ignore staleness and unverified sources
        card = evaluate_instructional_recommendation(
            scenario_input,
            allow_unverified=True,
            allow_stale=True,
            include_rationale=True,
        )
    elif ablation_type == "no_rationale" or config.get("no_rationale", False):
        # Full intervention rules but without pedagogical explanation
        card = evaluate_instructional_recommendation(
            scenario_input,
            include_rationale=False,
        )
    else:
        # Default ablation: evaluate with configured override flags
        card = evaluate_instructional_recommendation(
            scenario_input,
            allow_unverified=config.get("allow_unverified", False),
            allow_conflicts=config.get("allow_conflicts", False),
            allow_stale=config.get("allow_stale", False),
            descriptive_only=config.get("descriptive_only", False),
            include_rationale=config.get("include_rationale", True),
        )

    evidence_list = scenario_input.get("learning_evidence") or []
    return InterventionEvaluationResult(
        decision=card.decision,
        reason_codes=card.reason_codes,
        policy_version=POLICY_VERSION_ABLATION,
        action_proposed=card.action_proposed,
        abstention_appropriate=card.abstention_appropriate,
        intervention_traceable=card.intervention_traceable,
        candidate_intervention=(
            card.action.action_type if card.action else scenario_input.get("candidate_intervention")
        ),
        rationale=card.rationale,
        observables={
            "mode": "ablation",
            "ablation_type": ablation_type,
            "evidence_count": len(evidence_list),
            "k_anonymity_satisfied": card.k_anonymity_satisfied,
        },
    )
