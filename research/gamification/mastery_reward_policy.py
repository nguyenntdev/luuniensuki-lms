"""Research Gamification - Mastery Reward Policy Engine (Study LN-05).

Theory: Self-determination theory; mastery learning; gamification.
Research context: Trò chơi hóa gắn minh chứng làm chủ năng lực trong học tập di sản số Cửu Đỉnh.
Pedagogical Invariants:
- INV-LN-05-01: Client-supplied XP is not evidence of competency.
- INV-LN-05-02: Replaying the same task does not create new independent evidence.
- INV-LN-05-03: Participation badges must not be confused with historical competency mastery.
- INV-LN-05-04: When task definitions or policy versions change, existing awards must be revalidated.
- INV-LN-05-05: Thresholds must not be lowered simply because baseline issued more badges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


POLICY_VERSION = "2.0-intervention"
BASELINE_POLICY_VERSION = "1.0-baseline"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    decision: str
    reason_codes: List[str]
    policy_version: str
    badge_awarded: bool
    observables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "policy_version": self.policy_version,
            "badge_awarded": self.badge_awarded,
        }
        res.update(self.observables)
        return res


def evaluate_mastery_reward_baseline(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> PolicyEvaluationResult:
    """Baseline policy: Awards mastery badges purely on XP thresholds, click counts,

    or superficial streaks without verifying underlying historical competency or evidence provenance.
    """
    config = config or {}
    xp_threshold = config.get("baseline_xp_threshold", 50)
    
    reward_events = scenario_input.get("reward_events", [])
    total_xp = sum(e.get("xp", 0) for e in reward_events)
    
    # In baseline mode, any event granting XP or user activity is blindly trusted
    # Even forged client XP or duplicated events trigger badge award if total_xp > 0
    # In LN-05 concrete fixtures:
    # nominal: total_xp = 20
    # duplicate_events: total_xp = 40
    # missing_competency: total_xp = 20
    # spoofed_xp: total_xp = 10000
    # stale_policy: total_xp = 20
    # Baseline awards badge as long as there is any activity/XP (e.g. total_xp > 0)
    awarded = len(reward_events) > 0 or total_xp > 0
    
    decision = "grant_if_eligible" if awarded else "deny_mastery_badge"
    reason_codes = ["baseline_xp_grant"] if awarded else ["baseline_insufficient_xp"]
    
    return PolicyEvaluationResult(
        decision=decision,
        reason_codes=reason_codes,
        policy_version=BASELINE_POLICY_VERSION,
        badge_awarded=awarded,
        observables={
            "total_xp": total_xp,
            "event_count": len(reward_events),
            "mode": "baseline",
        },
    )


def evaluate_mastery_reward_intervention(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> PolicyEvaluationResult:
    """Intervention policy: Enforces genuine assessment criteria (>=80% or threshold

    on source evaluation tasks, M-E-E submission verification), idempotency and anti-replay,
    and distinct separation of XP from mastery.
    """
    config = config or {}
    badge = scenario_input.get("badge", {})
    req_competency = badge.get("requires_competency", "S3")
    min_level = badge.get("min_level", 0.75)
    badge_policy_version = badge.get("policy_version", 2)
    event_policy_version = scenario_input.get("event_policy_version")
    
    reward_events = scenario_input.get("reward_events", [])
    skill_evidence = scenario_input.get("skill_evidence", {})
    
    # Check 1: Policy version freshness (INV-LN-05-04 / RULE-LN-05-05)
    # Stale policy requires revalidation before badge issuance
    if event_policy_version is not None and event_policy_version != badge_policy_version:
        return PolicyEvaluationResult(
            decision="revalidate_badge",
            reason_codes=["stale_policy_version", "revalidation_required"],
            policy_version=POLICY_VERSION,
            badge_awarded=False,
            observables={
                "event_policy_version": event_policy_version,
                "badge_policy_version": badge_policy_version,
                "badge_awarded": False,
                "replay_prevented": False,
            },
        )
    
    # Check 2: Client forged XP / provenance check (INV-LN-05-01 / RULE-LN-05-04)
    # Events not signed/originated by server actor are rejected as forged
    for ev in reward_events:
        actor = ev.get("actor")
        if actor != "server":
            return PolicyEvaluationResult(
                decision="reject_forged_event",
                reason_codes=["untrusted_actor", "client_forged_xp"],
                policy_version=POLICY_VERSION,
                badge_awarded=False,
                observables={
                    "forged_actor": actor,
                    "badge_awarded": False,
                    "replay_prevented": False,
                },
            )
            
    # Check 3: Event uniqueness / deduplication / anti-replay (INV-LN-05-02 / RULE-LN-05-02)
    event_ids = [ev.get("event_id") for ev in reward_events if "event_id" in ev]
    if len(event_ids) != len(set(event_ids)):
        return PolicyEvaluationResult(
            decision="deduplicate_events",
            reason_codes=["replayed_event_detected", "idempotency_violation"],
            policy_version=POLICY_VERSION,
            badge_awarded=False,
            observables={
                "duplicate_count": len(event_ids) - len(set(event_ids)),
                "badge_awarded": False,
                "replay_prevented": True,
            },
        )
        
    # Check 4: Historical competency evidence & verified task (INV-LN-05-03 / RULE-LN-05-03)
    verified_task = skill_evidence.get("verified_task", False)
    competency_score = skill_evidence.get(req_competency, 0.0)
    
    if not verified_task or competency_score < min_level:
        return PolicyEvaluationResult(
            decision="deny_mastery_badge",
            reason_codes=["missing_competency_evidence", "score_below_threshold"],
            policy_version=POLICY_VERSION,
            badge_awarded=False,
            observables={
                "competency": req_competency,
                "score": competency_score,
                "threshold": min_level,
                "verified_task": verified_task,
                "badge_awarded": False,
                "replay_prevented": False,
            },
        )
        
    # Check 5: Nominal grant (RULE-LN-05-01)
    return PolicyEvaluationResult(
        decision="grant_if_eligible",
        reason_codes=["verified_competency_achieved", "provenance_validated"],
        policy_version=POLICY_VERSION,
        badge_awarded=True,
        observables={
            "competency": req_competency,
            "score": competency_score,
            "threshold": min_level,
            "verified_task": True,
            "badge_awarded": True,
            "replay_prevented": False,
        },
    )


def evaluate_mastery_reward_ablation(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> PolicyEvaluationResult:
    """Ablation policy: Configurable ablations:

    - ablation_type = 'xp_only': awards badge purely on XP.
    - ablation_type = 'disable_anti_replay': bypasses deduplication check.
    - ablation_type = 'disable_provenance': ignores untrusted client actor check.
    """
    config = config or {}
    ablation_type = config.get("ablation_type", "xp_only")
    
    if ablation_type == "xp_only":
        return evaluate_mastery_reward_baseline(scenario_input, config)
        
    # Start from intervention logic with specific gates disabled
    badge = scenario_input.get("badge", {})
    req_competency = badge.get("requires_competency", "S3")
    min_level = badge.get("min_level", 0.75)
    badge_policy_version = badge.get("policy_version", 2)
    event_policy_version = scenario_input.get("event_policy_version")
    
    reward_events = scenario_input.get("reward_events", [])
    skill_evidence = scenario_input.get("skill_evidence", {})
    
    if event_policy_version is not None and event_policy_version != badge_policy_version:
        return PolicyEvaluationResult(
            decision="revalidate_badge",
            reason_codes=["stale_policy_version"],
            policy_version="2.0-ablation",
            badge_awarded=False,
            observables={"badge_awarded": False},
        )
        
    if ablation_type != "disable_provenance":
        for ev in reward_events:
            if ev.get("actor") != "server":
                return PolicyEvaluationResult(
                    decision="reject_forged_event",
                    reason_codes=["untrusted_actor"],
                    policy_version="2.0-ablation",
                    badge_awarded=False,
                    observables={"badge_awarded": False},
                )
                
    if ablation_type != "disable_anti_replay":
        event_ids = [ev.get("event_id") for ev in reward_events if "event_id" in ev]
        if len(event_ids) != len(set(event_ids)):
            return PolicyEvaluationResult(
                decision="deduplicate_events",
                reason_codes=["replayed_event_detected"],
                policy_version="2.0-ablation",
                badge_awarded=False,
                observables={"badge_awarded": False},
            )
            
    verified_task = skill_evidence.get("verified_task", False)
    competency_score = skill_evidence.get(req_competency, 0.0)
    
    if not verified_task or competency_score < min_level:
        return PolicyEvaluationResult(
            decision="deny_mastery_badge",
            reason_codes=["missing_competency_evidence"],
            policy_version="2.0-ablation",
            badge_awarded=False,
            observables={"badge_awarded": False},
        )
        
    return PolicyEvaluationResult(
        decision="grant_if_eligible",
        reason_codes=["verified_competency_achieved"],
        policy_version="2.0-ablation",
        badge_awarded=True,
        observables={"badge_awarded": True},
    )
