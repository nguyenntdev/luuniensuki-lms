# -*- coding: utf-8 -*-
"""Competency Prerequisites & Adaptive Learning Domain Engine (LN-02 / Study 02).

Implements prerequisite-aware adaptive learning path policies for historical education:
- Four-dimensional historical reasoning competency model (S1: Spatial, S2: Temporal, S3: Evidence, S4: Argumentation).
- Strict prerequisite verification across hard curriculum constraints.
- Cycle detection on dependency graphs.
- Score validation (0.0 <= score <= 1.0) and detection of client score spoofing / invalid ranges.
- Abstention mechanism when competency data is insufficient (INV-LN-02-01: missing != 0).
- Pure evaluation functions supporting baseline, intervention, and ablation modes.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Union
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Controlled Vocabularies & Enums
# --------------------------------------------------------------------------- #
class CompetencyDimension(str, Enum):
    """The four historical reasoning competencies under Vietnamese General Education (2018)."""
    S1 = "S1"  # Spatial / Không gian (định vị công trình, bản đồ)
    S2 = "S2"  # Temporal / Thời gian (biên niên, thời kỳ)
    S3 = "S3"  # Evidence / Sử liệu (khai thác nguồn, văn bản, văn khắc)
    S4 = "S4"  # Argumentation / Lập luận (diễn giải, tổng hợp lịch sử)


class RecommendationDecision(str, Enum):
    """Pedagogical policy decision outcomes."""
    recommend_eligible = "recommend_eligible"
    remediate_first = "remediate_first"
    abstain_insufficient_data = "abstain_insufficient_data"
    reject_invalid_score = "reject_invalid_score"
    reject_cycle = "reject_cycle"


class ReasonCode(str, Enum):
    """Auditable reason codes for policy traceability."""
    ELIGIBLE_RECOMMENDATION = "ELIGIBLE_RECOMMENDATION"
    PREREQUISITE_NOT_MET = "PREREQUISITE_NOT_MET"
    INSUFFICIENT_COMPETENCY_DATA = "INSUFFICIENT_COMPETENCY_DATA"
    INVALID_SCORE_RANGE = "INVALID_SCORE_RANGE"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    BASELINE_GREEDY_SCORE = "BASELINE_GREEDY_SCORE"
    ABLATION_NO_PREREQUISITES = "ABLATION_NO_PREREQUISITES"
    ABLATION_COLLAPSED_LATENT = "ABLATION_COLLAPSED_LATENT"
    ABLATION_NO_ABSTENTION = "ABLATION_NO_ABSTENTION"


# --------------------------------------------------------------------------- #
# Domain Exceptions
# --------------------------------------------------------------------------- #
class PrerequisitePolicyError(Exception):
    """Base exception for prerequisite policy errors."""
    pass


class DependencyCycleError(PrerequisitePolicyError):
    """Raised when a dependency graph contains cycles."""
    pass


class InvalidScoreRangeError(PrerequisitePolicyError):
    """Raised when mastery or observed scores are outside valid [0, 1] range."""
    pass


class InsufficientMasteryDataError(PrerequisitePolicyError):
    """Raised when required prerequisite competency data is missing."""
    pass


# --------------------------------------------------------------------------- #
# Domain Models
# --------------------------------------------------------------------------- #
class CompetencyState(BaseModel):
    """Vector of learner mastery across S1-S4 dimensions."""
    id: Optional[str] = None
    s1: Optional[float] = None
    s2: Optional[float] = None
    s3: Optional[float] = None
    s4: Optional[float] = None
    evidence_timestamp: Optional[datetime] = None
    uncertainty: Optional[dict[str, float]] = None

    def get_dimension(self, dimension: Union[str, CompetencyDimension]) -> Optional[float]:
        dim_key = dimension.value if isinstance(dimension, CompetencyDimension) else str(dimension)
        key_map = {"S1": self.s1, "S2": self.s2, "S3": self.s3, "S4": self.s4}
        return key_map.get(dim_key)


class TaskPrerequisite(BaseModel):
    """Prerequisite requirements for a target learning task."""
    task_id: str
    target_competency: str
    prerequisites: dict[str, float] = Field(default_factory=dict)
    hard_or_soft: str = "hard"


class RecommendationTrace(BaseModel):
    """Audit trace for recommendation decision and metrics."""
    decision: str
    reason_codes: list[str]
    policy_version: str
    prerequisite_violated: bool
    competency_coverage: float
    unjustified_recommendation: bool
    target_task_id: Optional[str] = None
    research_only: bool = True


# --------------------------------------------------------------------------- #
# Graph Cycle Detection & Score Validation
# --------------------------------------------------------------------------- #
def detect_dependency_cycle(edges: list[list[str]] | list[tuple[str, str]]) -> bool:
    """Detect whether a directed dependency graph has cycles using 3-color DFS.

    Args:
        edges: List of directed edges [u, v] meaning u -> v (u is prerequisite of v).

    Returns:
        True if at least one cycle exists, False if acyclic (DAG).
    """
    if not edges:
        return False

    adj: dict[str, list[str]] = {}
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) < 2:
            continue
        u, v = str(edge[0]), str(edge[1])
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, [])

    # 0 = unvisited, 1 = visiting (in current DFS stack), 2 = visited (completed)
    visited: dict[str, int] = {}
    has_cycle = False

    def dfs(node: str) -> None:
        nonlocal has_cycle
        if has_cycle:
            return
        visited[node] = 1
        for nxt in adj.get(node, []):
            nxt_state = visited.get(nxt, 0)
            if nxt_state == 1:
                has_cycle = True
                return
            elif nxt_state == 0:
                dfs(nxt)
        visited[node] = 2

    for node in adj:
        if visited.get(node, 0) == 0:
            dfs(node)
            if has_cycle:
                return True

    return False


def validate_score_value(score: Any) -> bool:
    """Check if a score is a valid finite float/int in [0.0, 1.0]."""
    if score is None:
        return False
    if not isinstance(score, (int, float)):
        return False
    if isinstance(score, bool):  # bool is a subclass of int in Python
        return False
    if math.isnan(score) or math.isinf(score):
        return False
    return 0.0 <= float(score) <= 1.0


def validate_all_scenario_scores(scenario_input: dict[str, Any]) -> bool:
    """Validate that all scores and mastery values in scenario_input are within [0.0, 1.0]."""
    score_observed = scenario_input.get("score_observed")
    if score_observed is not None:
        if not validate_score_value(score_observed):
            return False

    mastery = scenario_input.get("mastery", {})
    if isinstance(mastery, dict):
        for val in mastery.values():
            if val is not None and not validate_score_value(val):
                return False

    learner_comp = scenario_input.get("learner", {}).get("competencies", {})
    if isinstance(learner_comp, dict):
        for val in learner_comp.values():
            if val is not None and not validate_score_value(val):
                return False

    return True


def calculate_competency_coverage(mastery: dict[str, Any]) -> float:
    """Calculate coverage ratio across standard competency dimensions S1-S4.

    Returns:
        Fraction of S1-S4 dimensions with observed non-null data (0.0 to 1.0).
    """
    if not isinstance(mastery, dict) or not mastery:
        return 0.0
    all_dims = ["S1", "S2", "S3", "S4"]
    observed = sum(1 for dim in all_dims if mastery.get(dim) is not None and validate_score_value(mastery.get(dim)))
    return round(observed / len(all_dims), 4)


# --------------------------------------------------------------------------- #
# Pure Evaluation Engines (Intervention, Baseline, Ablation)
# --------------------------------------------------------------------------- #
POLICY_VERSION = "ln02-adaptive-v1.0"


def evaluate_intervention(scenario_input: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Intervention Mode:
    - Step 1: Detect cycles in dependency graph -> reject_cycle.
    - Step 2: Validate all score ranges [0.0, 1.0] -> reject_invalid_score.
    - Step 3: Check for missing required prerequisite data -> abstain_insufficient_data.
    - Step 4: Verify hard prerequisites (mastery >= threshold) -> remediate_first if any unmet.
    - Step 5: All checks passed -> recommend_eligible.
    """
    edges = scenario_input.get("graph_edges", [])
    if detect_dependency_cycle(edges):
        return {
            "decision": RecommendationDecision.reject_cycle.value,
            "reason_codes": [ReasonCode.CYCLE_DETECTED.value],
            "policy_version": POLICY_VERSION,
            "prerequisite_violated": False,
            "competency_coverage": calculate_competency_coverage(scenario_input.get("mastery", {})),
            "unjustified_recommendation": False,
            "research_only": True,
        }

    if not validate_all_scenario_scores(scenario_input):
        return {
            "decision": RecommendationDecision.reject_invalid_score.value,
            "reason_codes": [ReasonCode.INVALID_SCORE_RANGE.value],
            "policy_version": POLICY_VERSION,
            "prerequisite_violated": False,
            "competency_coverage": calculate_competency_coverage(scenario_input.get("mastery", {})),
            "unjustified_recommendation": False,
            "research_only": True,
        }

    target_task = scenario_input.get("target_task", {})
    prerequisites = target_task.get("prerequisites", {})
    mastery = scenario_input.get("mastery", {})

    # Check for missing prerequisite competency data
    for req_dim in prerequisites.keys():
        if req_dim not in mastery or mastery[req_dim] is None:
            return {
                "decision": RecommendationDecision.abstain_insufficient_data.value,
                "reason_codes": [ReasonCode.INSUFFICIENT_COMPETENCY_DATA.value],
                "policy_version": POLICY_VERSION,
                "prerequisite_violated": False,
                "competency_coverage": calculate_competency_coverage(mastery),
                "unjustified_recommendation": False,
                "research_only": True,
            }

    # Verify prerequisite competency thresholds
    unmet = []
    for req_dim, threshold in prerequisites.items():
        val = mastery.get(req_dim, 0.0)
        if val < threshold:
            unmet.append(req_dim)

    coverage = calculate_competency_coverage(mastery)

    if unmet:
        return {
            "decision": RecommendationDecision.remediate_first.value,
            "reason_codes": [ReasonCode.PREREQUISITE_NOT_MET.value],
            "policy_version": POLICY_VERSION,
            "prerequisite_violated": False,
            "competency_coverage": coverage,
            "unjustified_recommendation": False,
            "unmet_prerequisites": unmet,
            "research_only": True,
        }

    return {
        "decision": RecommendationDecision.recommend_eligible.value,
        "reason_codes": [ReasonCode.ELIGIBLE_RECOMMENDATION.value],
        "policy_version": POLICY_VERSION,
        "prerequisite_violated": False,
        "competency_coverage": coverage,
        "unjustified_recommendation": False,
        "research_only": True,
    }


def evaluate_baseline(scenario_input: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Baseline Mode:
    Greedily recommends next content based solely on aggregate score,
    completely ignoring specific prerequisite competencies (S1-S4).
    """
    threshold = (config or {}).get("aggregate_score_threshold", 0.5)
    score_observed = scenario_input.get("score_observed")
    score_val = float(score_observed) if validate_score_value(score_observed) else 0.0
    mastery = scenario_input.get("mastery", {})
    target_task = scenario_input.get("target_task", {})
    prerequisites = target_task.get("prerequisites", {})

    # In baseline, recommend_eligible is greedily chosen if aggregate score >= threshold
    recommended = bool(score_val >= threshold)
    decision = RecommendationDecision.recommend_eligible.value if recommended else RecommendationDecision.remediate_first.value

    # Check whether a prerequisite violation actually occurred:
    # A violation occurs if content is recommended despite unmet prerequisites.
    has_unmet_prereq = False
    for req_dim, req_val in prerequisites.items():
        if req_dim not in mastery or mastery[req_dim] is None or mastery[req_dim] < req_val:
            has_unmet_prereq = True
            break

    prerequisite_violated = bool(recommended and has_unmet_prereq)
    unjustified = bool(recommended and (has_unmet_prereq or not validate_all_scenario_scores(scenario_input) or detect_dependency_cycle(scenario_input.get("graph_edges", []))))

    return {
        "decision": decision,
        "reason_codes": [ReasonCode.BASELINE_GREEDY_SCORE.value],
        "policy_version": "ln02-baseline-v1.0",
        "prerequisite_violated": prerequisite_violated,
        "competency_coverage": calculate_competency_coverage(mastery),
        "unjustified_recommendation": unjustified,
        "research_only": True,
    }


def evaluate_ablation(scenario_input: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Ablation Mode:
    Supports variants specified via config:
    1. 'no_prerequisites' / 'ignore_prerequisites': Removes prerequisite checks; uses aggregate score after graph/score checks.
    2. 'single_latent_skill': Collapses S1-S4 into a single scalar average.
    3. 'fixed_target_s3': Constrains verification solely to S3 evidence competency.
    4. 'no_abstention': Disables abstention; defaults missing data to 0.0.
    5. 'disable_remediation': Bypasses remediation guidance on unmet prerequisites.
    """
    cfg = config or {}
    variant = cfg.get("variant") or cfg.get("ablation_type")
    if not variant:
        if cfg.get("ignore_prerequisites") is True:
            variant = "no_prerequisites"
        elif cfg.get("fixed_target_s3") is True:
            variant = "fixed_target_s3"
        elif cfg.get("disable_remediation") is True:
            variant = "disable_remediation"
        else:
            variant = "no_prerequisites"
    if variant == "ignore_prerequisites":
        variant = "no_prerequisites"

    edges = scenario_input.get("graph_edges", [])
    if detect_dependency_cycle(edges):
        return {
            "decision": RecommendationDecision.reject_cycle.value,
            "reason_codes": [ReasonCode.CYCLE_DETECTED.value],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": False,
            "competency_coverage": calculate_competency_coverage(scenario_input.get("mastery", {})),
            "unjustified_recommendation": False,
            "research_only": True,
        }

    if not validate_all_scenario_scores(scenario_input):
        return {
            "decision": RecommendationDecision.reject_invalid_score.value,
            "reason_codes": [ReasonCode.INVALID_SCORE_RANGE.value],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": False,
            "competency_coverage": calculate_competency_coverage(scenario_input.get("mastery", {})),
            "unjustified_recommendation": False,
            "research_only": True,
        }

    mastery = scenario_input.get("mastery", {})
    target_task = scenario_input.get("target_task", {})
    prerequisites = target_task.get("prerequisites", {})

    if variant == "no_abstention":
        # Missing data is not abstained; imputed as 0.0
        imputed_mastery = {k: (mastery.get(k) if mastery.get(k) is not None else 0.0) for k in ["S1", "S2", "S3", "S4"]}
        unmet = [k for k, thresh in prerequisites.items() if imputed_mastery.get(k, 0.0) < thresh]
        if unmet:
            decision = RecommendationDecision.remediate_first.value
            reason_code = ReasonCode.ABLATION_NO_ABSTENTION.value
        else:
            decision = RecommendationDecision.recommend_eligible.value
            reason_code = ReasonCode.ELIGIBLE_RECOMMENDATION.value

        return {
            "decision": decision,
            "reason_codes": [reason_code],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": False,
            "competency_coverage": calculate_competency_coverage(mastery),
            "unjustified_recommendation": False,
            "research_only": True,
        }

    elif variant == "single_latent_skill":
        # Collapse S1-S4 into single scalar average
        # If any prerequisite is missing, abstain
        for req_dim in prerequisites.keys():
            if req_dim not in mastery or mastery[req_dim] is None:
                return {
                    "decision": RecommendationDecision.abstain_insufficient_data.value,
                    "reason_codes": [ReasonCode.INSUFFICIENT_COMPETENCY_DATA.value],
                    "policy_version": f"ln02-ablation-{variant}-v1.0",
                    "prerequisite_violated": False,
                    "competency_coverage": calculate_competency_coverage(mastery),
                    "unjustified_recommendation": False,
                    "research_only": True,
                }
        valid_scores = [v for v in mastery.values() if isinstance(v, (int, float))]
        latent_skill = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        avg_threshold = sum(prerequisites.values()) / len(prerequisites) if prerequisites else 0.5
        recommended = latent_skill >= avg_threshold
        decision = RecommendationDecision.recommend_eligible.value if recommended else RecommendationDecision.remediate_first.value

        # Check actual dimensional violation
        has_dim_deficit = any(mastery.get(k, 0.0) < thresh for k, thresh in prerequisites.items())
        prereq_violated = recommended and has_dim_deficit

        return {
            "decision": decision,
            "reason_codes": [ReasonCode.ABLATION_COLLAPSED_LATENT.value],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": prereq_violated,
            "competency_coverage": calculate_competency_coverage(mastery),
            "unjustified_recommendation": prereq_violated,
            "research_only": True,
        }

    elif variant in ("fixed_target_s3", "fixed_s3"):
        # Evaluates only S3 prerequisite, ignoring all other dimensional requirements
        s3_threshold = prerequisites.get("S3", 0.4)
        if "S3" not in mastery or mastery["S3"] is None:
            return {
                "decision": RecommendationDecision.abstain_insufficient_data.value,
                "reason_codes": [ReasonCode.INSUFFICIENT_COMPETENCY_DATA.value],
                "policy_version": f"ln02-ablation-{variant}-v1.0",
                "prerequisite_violated": False,
                "competency_coverage": calculate_competency_coverage(mastery),
                "unjustified_recommendation": False,
                "research_only": True,
            }
        s3_val = mastery.get("S3", 0.0)
        recommended = s3_val >= s3_threshold
        decision = RecommendationDecision.recommend_eligible.value if recommended else RecommendationDecision.remediate_first.value
        has_dim_deficit = any(mastery.get(k) is None or mastery.get(k, 0.0) < thresh for k, thresh in prerequisites.items())
        prereq_violated = bool(recommended and has_dim_deficit)
        return {
            "decision": decision,
            "reason_codes": [ReasonCode.ABLATION_COLLAPSED_LATENT.value],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": prereq_violated,
            "competency_coverage": calculate_competency_coverage(mastery),
            "unjustified_recommendation": prereq_violated,
            "research_only": True,
        }

    elif variant in ("disable_remediation", "no_remediation"):
        # Disables remediation path; recommends eligible directly even if prerequisites unmet
        for req_dim in prerequisites.keys():
            if req_dim not in mastery or mastery[req_dim] is None:
                return {
                    "decision": RecommendationDecision.abstain_insufficient_data.value,
                    "reason_codes": [ReasonCode.INSUFFICIENT_COMPETENCY_DATA.value],
                    "policy_version": f"ln02-ablation-{variant}-v1.0",
                    "prerequisite_violated": False,
                    "competency_coverage": calculate_competency_coverage(mastery),
                    "unjustified_recommendation": False,
                    "research_only": True,
                }
        unmet = [k for k, thresh in prerequisites.items() if mastery.get(k, 0.0) < thresh]
        has_dim_deficit = bool(unmet)
        return {
            "decision": RecommendationDecision.recommend_eligible.value,
            "reason_codes": [ReasonCode.ABLATION_NO_PREREQUISITES.value],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": has_dim_deficit,
            "competency_coverage": calculate_competency_coverage(mastery),
            "unjustified_recommendation": has_dim_deficit,
            "research_only": True,
        }

    else:  # "no_prerequisites"
        # Bỏ điều kiện tiên quyết và chỉ dùng điểm tổng
        score_observed = scenario_input.get("score_observed")
        score_val = float(score_observed) if validate_score_value(score_observed) else 0.0
        recommended = score_val >= 0.5
        decision = RecommendationDecision.recommend_eligible.value if recommended else RecommendationDecision.remediate_first.value
        has_dim_deficit = any(mastery.get(k) is None or mastery.get(k, 0.0) < thresh for k, thresh in prerequisites.items())

        return {
            "decision": decision,
            "reason_codes": [ReasonCode.ABLATION_NO_PREREQUISITES.value],
            "policy_version": f"ln02-ablation-{variant}-v1.0",
            "prerequisite_violated": bool(recommended and has_dim_deficit),
            "competency_coverage": calculate_competency_coverage(mastery),
            "unjustified_recommendation": bool(recommended and has_dim_deficit),
            "research_only": True,
        }
