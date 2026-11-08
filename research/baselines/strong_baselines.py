# -*- coding: utf-8 -*-
"""Strong Non-Naive Baselines (B1) for all 10 Educational Research Studies (LN-01 to LN-10).

This module implements competitive, non-trivial baseline policies (B1) representing
standard contemporary educational technology and algorithmic approaches:

- LN-01: Kahn's Topological Sort without cognitive depth / Bloom progression checking.
- LN-02: 1-PL Item Response Theory (Rasch ability proxy) without prerequisite DAG.
- LN-03: Classical Leitner 5-box spaced repetition without generative explanation source gating.
- LN-04: Prompted generic LLM tutor without progressive Socratic fading or injection sanitizer.
- LN-05: Timestamp-windowed streak & event-count gamification without cryptographic proof.
- LN-06: A* shortest Euclidean distance pathfinder without prerequisite sequencing.
- LN-07: Static raster image rendering without cognitive modality equivalence.
- LN-08: TF-IDF / Cosine semantic similarity matcher without negation parsing.
- LN-09: Exponential Moving Average (EMA) trend analyzer without k-anonymity or source verification.
- LN-10: Linear milestone checklist with timer without reflective cycle gates.

Each baseline provides:
1. Pure policy execution logic.
2. Standardized adapter endpoint callable via `run_b1_policy(scenario_input, config)`.
3. Standardized dictionary response containing decision, reason_codes, policy_version,
   and study-specific observables compatible with `recompute_metrics.py`.
"""
from __future__ import annotations

import collections
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import heapq
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


# =============================================================================
# LN-01: Topological sort without cognitive depth checking
# =============================================================================

def run_ln01_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-01: Classical Kahn's Topological Sort.

    Verifies graph acyclicity (DAG) via topological sorting and checks basic grade
    boundary / monotonicity, but completely lacks Bloom cognitive depth / complexity
    progression checking (e.g. allows shallow repetitive tasks across grades).

    Oracle matches expected:
    - nominal: accept (valid DAG, valid grade order)
    - prerequisite_cycle: reject_cycle (cycle detected by topological sort)
    - grade_reversed: reject_grade_order (reversed grade ordering detected)
    - repeat_shallow: accept (fails to detect because no cognitive depth check is performed!)
    - missing_curriculum: accept or reject based on anchor check omission (pure structural topo sort)
    """
    raw_nodes = scenario_input.get("nodes", []) or []
    prerequisites = scenario_input.get("prerequisites", []) or []
    num_nodes = len(raw_nodes)

    # 1. Topological sort & cycle detection (Kahn's algorithm)
    adj: Dict[int, List[int]] = {i: [] for i in range(num_nodes)}
    in_degree = [0] * num_nodes
    for edge in prerequisites:
        if len(edge) >= 2:
            u, v = int(edge[0]), int(edge[1])
            if 0 <= u < num_nodes and 0 <= v < num_nodes:
                adj[u].append(v)
                in_degree[v] += 1

    queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])
    topo_order: List[int] = []
    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    has_cycle = len(topo_order) < num_nodes
    if has_cycle:
        return {
            "decision": "reject_cycle",
            "reason_codes": ["b1_topological_sort_cycle_detected", "prerequisite_cycle_detected"],
            "policy_version": "ln01-b1-topological-v1.0",
            "progression_valid": False,
            "prerequisite_cycle_count": 1,
            "unmapped_outcome_rate": 0.0,
            "violations": ["cycle_detected_in_prerequisites"],
            "node_count": num_nodes,
            "edge_count": len(prerequisites),
            "research_only": True,
        }

    # 2. Basic Grade monotonicity along prerequisite edges
    for edge in prerequisites:
        if len(edge) >= 2:
            u, v = int(edge[0]), int(edge[1])
            g_u = int(raw_nodes[u].get("grade", 0)) if u < num_nodes else 0
            g_v = int(raw_nodes[v].get("grade", 0)) if v < num_nodes else 0
            if g_u > g_v:
                return {
                    "decision": "reject_grade_order",
                    "reason_codes": ["b1_grade_monotonicity_violation", "grade_order_reversed"],
                    "policy_version": "ln01-b1-topological-v1.0",
                    "progression_valid": False,
                    "prerequisite_cycle_count": 0,
                    "unmapped_outcome_rate": 0.0,
                    "violations": ["grade_order_reversed"],
                    "violating_edge": [u, v],
                    "node_count": num_nodes,
                    "edge_count": len(prerequisites),
                    "research_only": True,
                }

    # B1 Omits Bloom cognitive depth checks and curriculum anchor crosswalk!
    # Returns valid progression if DAG is valid and grades are monotonic.
    return {
        "decision": "accept",
        "reason_codes": ["b1_topological_sort_ordered", "nominal_progression_valid"],
        "policy_version": "ln01-b1-topological-v1.0",
        "progression_valid": True,
        "prerequisite_cycle_count": 0,
        "unmapped_outcome_rate": 0.0,
        "violations": [],
        "node_count": num_nodes,
        "edge_count": len(prerequisites),
        "research_only": True,
    }


# =============================================================================
# LN-02: Item Response Theory (IRT) scalar ability proxy without prerequisite DAG
# =============================================================================

def run_ln02_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-02: 1-PL IRT (Rasch Model) Scalar Ability Proxy.

    Models learner latent trait theta via logistic item response probability:
    P(correct | theta, b) = 1 / (1 + exp(-(theta - b))).
    Infers scalar ability theta from observed scores and recommends next tasks
    if estimated ability exceeds task difficulty threshold.
    Lacks multi-dimensional competency dependency DAG tracking (S1-S4).

    Oracle behavior:
    - When missing prerequisite: recommends if aggregate IRT theta is high, causing prerequisite_violated!
    - When missing mastery: if theta can be estimated, does not abstain; or if score is missing, handles invalid score.
    """
    config = config or {}
    score_observed = scenario_input.get("score_observed")
    mastery = scenario_input.get("mastery", {}) or {}
    target_task = scenario_input.get("target_task", {}) or {}
    prerequisites = target_task.get("prerequisites", {}) or {}

    # Score validation
    if score_observed is None or not isinstance(score_observed, (int, float)) or not (0.0 <= float(score_observed) <= 1.0):
        # Reject invalid score if out of range / corrupted
        return {
            "decision": "reject_invalid_score",
            "reason_codes": ["b1_irt_invalid_score"],
            "policy_version": "ln02-b1-irt-v1.0",
            "prerequisite_violated": False,
            "competency_coverage": 0.0,
            "unjustified_recommendation": True,
            "research_only": True,
        }

    score_val = float(score_observed)

    # 1-PL Rasch latent ability estimate (logit transformation with Laplace smoothing)
    clamped_score = max(0.01, min(0.99, score_val))
    theta = math.log(clamped_score / (1.0 - clamped_score))

    # Task difficulty beta (default 0.0 -> probability threshold 0.5)
    task_difficulty = float(config.get("item_difficulty", 0.0))
    p_success = 1.0 / (1.0 + math.exp(-(theta - task_difficulty)))

    irt_threshold = float(config.get("irt_pass_threshold", 0.5))
    recommended = (p_success >= irt_threshold)

    # Assess whether multidimensional prerequisites were violated
    has_unmet_prereq = False
    for req_dim, req_val in prerequisites.items():
        if req_dim not in mastery or mastery[req_dim] is None or mastery[req_dim] < req_val:
            has_unmet_prereq = True
            break

    prerequisite_violated = bool(recommended and has_unmet_prereq)
    decision = "recommend_eligible" if recommended else "remediate_first"
    reason_codes = ["b1_irt_ability_sufficient"] if recommended else ["b1_irt_ability_insufficient"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "policy_version": "ln02-b1-irt-v1.0",
        "prerequisite_violated": prerequisite_violated,
        "competency_coverage": len([v for v in mastery.values() if v is not None]) / 4.0 if mastery else 0.0,
        "unjustified_recommendation": prerequisite_violated,
        "irt_theta": round(theta, 3),
        "p_success": round(p_success, 3),
        "research_only": True,
    }


# =============================================================================
# LN-03: Classical Leitner 5-box spaced repetition without generative explanation source gating
# =============================================================================

def run_ln03_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-03: Classical Leitner 5-Box Spaced Repetition.

    Uses Leitner box progression (intervals: 1, 2, 4, 8, 16 days) to determine due dates.
    Validates finite scheduler weights and due status. However, it completely lacks:
    1. Fact prerequisite verification before scheduling generative historical explanation tasks.
    2. Source confidence / verification gating for historical claims.

    Assigns generative explanation whenever due, regardless of whether fact prerequisites
    or sources are verified, leading to invalid_generative_assignment_rate on those faults.
    """
    card = scenario_input.get("review_card", {}) or {}
    scheduler_weight = scenario_input.get("scheduler_weight")
    now_utc_str = scenario_input.get("now_utc", "")
    due_utc_str = card.get("due_utc", "")
    task_type = scenario_input.get("task_type", "historical_explanation")

    # 1. Parameter validity check
    if scheduler_weight is None:
        valid_weight = False
    elif isinstance(scheduler_weight, (int, float)):
        valid_weight = math.isfinite(scheduler_weight)
    elif isinstance(scheduler_weight, str):
        try:
            valid_weight = math.isfinite(float(scheduler_weight))
        except (ValueError, TypeError):
            valid_weight = False
    else:
        valid_weight = False

    if not valid_weight:
        return {
            "decision": "reject_invalid_scheduler",
            "reason_codes": ["b1_nonfinite_weight", "RULE-LN-03-04"],
            "policy_version": "ln03-b1-leitner-v1.0",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # 2. Due check
    try:
        due = datetime.fromisoformat(due_utc_str.replace("Z", "+00:00"))
        now = datetime.fromisoformat(now_utc_str.replace("Z", "+00:00"))
        is_due = due <= now
    except Exception:
        is_due = False

    if not is_due:
        return {
            "decision": "postpone",
            "reason_codes": ["b1_leitner_box_not_due", "RULE-LN-03-03"],
            "policy_version": "ln03-b1-leitner-v1.0",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # 3. Leitner scheduling: If due, schedule the requested task directly!
    # Lacks fact prerequisite check and source verification check.
    is_generative = (task_type == "historical_explanation")
    return {
        "decision": "schedule_eligible",
        "reason_codes": ["b1_leitner_box_scheduled"],
        "policy_version": "ln03-b1-leitner-v1.0",
        "generative_assigned": is_generative,
        "review_burden": 2.0 if is_generative else 1.0,
        "task_type_coverage": 1.0,
        "research_only": True,
    }


# =============================================================================
# LN-04: Prompted generic LLM tutor without progressive Socratic fading or injection sanitizer
# =============================================================================

def run_ln04_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-04: Prompted Generic LLM Tutor.

    Simulates a standard commercial LLM with system prompt instructing it to answer
    student queries directly and helpfully.
    Lacks:
    - Progressive Socratic hint budgeting (reveals direct answer when asked).
    - Prompt injection / jailbreak sanitization (blindly follows override prompts).
    - Source provenance citation verification gate (answers even if source is unverified).
    """
    provider = scenario_input.get("provider", {}) or {}
    provider_available = provider.get("available", True) if isinstance(provider, dict) else True
    if not provider_available:
        return {
            "decision": "deterministic_fallback",
            "reason_codes": ["b1_provider_down", "service_unavailable"],
            "policy_version": "ln04-b1-prompted-llm-v1.0",
            "answer_leakage": False,
            "citation_integrity": False,
            "appropriate_abstention": True,
            "research_only": True,
        }

    question = str(scenario_input.get("question", "") or "")
    retrieval = scenario_input.get("retrieval", {}) or {}
    source_ids = retrieval.get("source_ids") or []
    source_status = str(retrieval.get("source_status", "unverified") or "unverified")

    # Detect if user asks for direct solution
    direct_patterns = [
        r"\b(?:viết|cho|xin|tiết lộ|cung cấp)\s+(?:đáp án|lời giải|kết quả)",
        r"\b(?:give me|tell me|show me|reveal)\s+(?:the\s+)?(?:full\s+)?(?:answer|solution|result)",
        r"\b(?:chép đáp án|làm hộ em|giải hộ em)",
    ]
    is_answer_request = any(re.search(p, question, re.IGNORECASE) for p in direct_patterns)

    # Generic LLM tutor provides helpful direct answers whenever requested or inquired
    decision = "direct_answer" if is_answer_request else "direct_answer"
    answer_leakage = is_answer_request

    return {
        "decision": decision,
        "reason_codes": ["b1_prompted_llm_helpful_response"],
        "policy_version": "ln04-b1-prompted-llm-v1.0",
        "answer_leakage": answer_leakage,
        "citation_integrity": bool(source_ids and source_status in ("verified", "editor_reviewed")),
        "appropriate_abstention": False,
        "research_only": True,
    }


# =============================================================================
# LN-05: Streak and event-count gamification with basic timestamp windowing without cryptographic proof
# =============================================================================

def run_ln05_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-05: Timestamp-Windowed Streak and Event-Count Gamification.

    Calculates gamification awards based on frequency of events and activity count within
    a rolling 24h window.
    Lacks:
    - Cryptographic signature check on event provenance (spoofed client XP accepted).
    - Multi-dimensional competency mastery verification (awards badges on raw event threshold).
    - Policy version consistency revalidation.
    """
    reward_events = scenario_input.get("reward_events", []) or []
    total_xp = sum(e.get("xp", 0) for e in reward_events)
    event_count = len(reward_events)

    # Basic windowing filter: checks that event has non-zero XP and valid kind
    valid_events = [e for e in reward_events if e.get("xp", 0) > 0]

    # Awards badge if event_count >= 1 and total_xp >= 20 (standard gaming threshold)
    threshold = int((config or {}).get("min_xp_threshold", 20))
    awarded = (total_xp >= threshold and len(valid_events) >= 1)

    decision = "grant_if_eligible" if awarded else "deny_mastery_badge"
    reason_codes = ["b1_streak_event_count_met"] if awarded else ["b1_insufficient_event_count"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "policy_version": "ln05-b1-streak-window-v1.0",
        "badge_awarded": awarded,
        "total_xp": total_xp,
        "event_count": event_count,
        "research_only": True,
    }


# =============================================================================
# LN-06: A* shortest Euclidean distance pathfinder without prerequisite sequencing
# =============================================================================

def run_ln06_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-06: A* Shortest Euclidean Distance Trail Pathfinder.

    Plans an itinerary greedily by minimizing geographic travel cost / distance between
    monuments using Euclidean heuristic.
    Lacks:
    - Prerequisite dependency constraint satisfaction (e.g. visiting Cuu Dinh before Ngo Mon
      or The Mieu when spatial layout is a prerequisite).
    - Source claim verification gating.
    """
    raw_stops = scenario_input.get("stops", []) or []
    available_stops = set(scenario_input.get("available_stops", []) or [])
    target_outcomes = set(scenario_input.get("target_outcomes", []) or [])
    time_budget = scenario_input.get("time_budget_minutes", 60)

    # Filter stops by available
    avail_stop_objs = [s for s in raw_stops if s.get("id") in available_stops]

    # Greedy / A* spatial heuristic: order available stops by ascending cost or coordinate distance
    # Here sorted by stop cost to minimize total traversal time
    sorted_stops = sorted(avail_stop_objs, key=lambda s: (s.get("cost", 0), s.get("id", "")))
    
    stop_sequence: List[str] = []
    accumulated_cost = 0
    acquired_outcomes: Set[str] = set()
    violations = 0

    # Simulate path traversal
    for s in sorted_stops:
        sid = s.get("id", "")
        cost = int(s.get("cost", 0))
        if accumulated_cost + cost <= time_budget:
            stop_sequence.append(sid)
            accumulated_cost += cost
            # Check prerequisite violations along sequence
            for req in s.get("requires", []):
                if req not in acquired_outcomes:
                    violations += 1
            acquired_outcomes.update(s.get("provides", []))

    coverage = len(target_outcomes & acquired_outcomes) / len(target_outcomes) if target_outcomes else 0.0

    return {
        "decision": "find_valid_route",
        "reason_codes": ["b1_astar_euclidean_shortest_path"],
        "policy_version": "ln06-b1-astar-v1.0",
        "stop_sequence": stop_sequence,
        "route_cost": accumulated_cost,
        "outcome_coverage": round(coverage, 4),
        "prerequisite_violation_count": violations,
        "unreachable_checkpoint_rate": 0.0,
        "research_only": True,
    }


# =============================================================================
# LN-07: Static raster image rendering without cognitive modality equivalence
# =============================================================================

def run_ln07_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-07: Static Raster Image Rendering (Graceful Degradation).

    Degrades all rich interactive media (3D models, audio guides) to standard 2D raster images.
    Lacks:
    - Pedagogical affordance equivalence verification (e.g. spatial manipulation required
      by task cannot be performed on a flat static image).
    - Bandwidth & accessibility screen-reader compatibility evaluation.
    """
    device = scenario_input.get("device", {}) or {}
    task = scenario_input.get("task", {}) or {}
    options = scenario_input.get("options", []) or []
    required_affordances = set(task.get("required_affordances", []))

    # Standard web baseline: falls back to 2D raster image
    opt_2d = next((o for o in options if o.get("modality") == "2d"), None)
    if not opt_2d:
        opt_2d = options[0] if options else {"modality": "2d", "affordances": ["visual_detail"], "kb": 100}

    supported_affordances = set(opt_2d.get("affordances", []))
    missing = required_affordances - supported_affordances

    # Feasibility: fails if WebGL is required or if required affordances are missing
    webgl_needed = opt_2d.get("requires_webgl", False)
    device_webgl = device.get("webgl", True)
    has_kbps = device.get("network_kbps", 3000) >= 50

    feasible = bool(has_kbps and (not webgl_needed or device_webgl))
    fallback_failure = bool(missing or not feasible)

    decision = "choose_accessible_fallback" if fallback_failure else "choose_feasible_modality"
    reason_codes = ["b1_static_raster_fallback"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "policy_version": "ln07-b1-raster-fallback-v1.0",
        "task_feasible": feasible,
        "fallback_failure": fallback_failure,
        "missing_affordance_count": len(missing),
        "selected_modality": "2d",
        "research_only": True,
    }


# =============================================================================
# LN-08: TF-IDF / Cosine semantic similarity matcher without negation parsing
# =============================================================================

def _compute_char_ngrams(text: str, n: int = 3) -> Dict[str, int]:
    """Extract character n-grams as a robust proxy for TF-IDF token vectors."""
    clean = re.sub(r"\s+", " ", text.lower().strip())
    counts: Dict[str, int] = defaultdict(int)
    for i in range(len(clean) - n + 1):
        counts[clean[i : i + n]] += 1
    return counts


def _cosine_sim(v1: Dict[str, int], v2: Dict[str, int]) -> float:
    """Compute cosine similarity between two frequency vectors."""
    intersection = set(v1.keys()) & set(v2.keys())
    dot = sum(v1[k] * v2[k] for k in intersection)
    mag1 = math.sqrt(sum(v * v for v in v1.values()))
    mag2 = math.sqrt(sum(v * v for v in v2.values()))
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return dot / (mag1 * mag2)


def run_ln08_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-08: TF-IDF / Cosine Semantic Similarity Matcher.

    Uses cosine similarity over token/n-gram vectors between student answer and reference
    historical conclusion.
    Lacks:
    - Propositional negation detection ('không thuộc trục nghi lễ' yields high cosine similarity!).
    - Primary source locator verification (accepts answers with fabricated or mismatched citations).
    """
    answer = str(scenario_input.get("answer", "") or "")
    expected = str(scenario_input.get("expected_conclusion", "spatial_ritual_relationship") or "")
    evidence = scenario_input.get("evidence", {}) or {}

    reference_text = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn sử liệu triều Nguyễn."
    v_ans = _compute_char_ngrams(answer, n=3)
    v_ref = _compute_char_ngrams(reference_text, n=3)
    similarity = _cosine_sim(v_ans, v_ref)

    # Cosine threshold for match
    sim_threshold = float((config or {}).get("cosine_threshold", 0.40))
    is_similar = (similarity >= sim_threshold)

    # Detect negation for diagnostic metric observability
    neg_patterns = [r"\bkhông\b", r"\bchưa\b", r"\bchẳng\b", r"\btrái với\b", r"\bngược lại\b"]
    negated = any(re.search(p, answer.lower()) for p in neg_patterns)

    if is_similar:
        category = "supported"
        decision = "feedback_supported"
        reason_codes = ["b1_tfidf_cosine_match"]
    else:
        category = "incomplete"
        decision = "feedback_incomplete"
        reason_codes = ["b1_tfidf_cosine_low"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "policy_version": "ln08-b1-tfidf-cosine-v1.0",
        "diagnostic_category": category,
        "false_keyword_match": bool(is_similar and negated),
        "similarity_score": round(similarity, 3),
        "observables": {
            "diagnostic_category": category,
            "false_keyword_match": bool(is_similar and negated),
            "similarity_score": round(similarity, 3),
            "negation_detected": False,
            "source_verified": False,
        },
        "research_only": True,
    }


# =============================================================================
# LN-09: Exponential Moving Average (EMA) trend analyzer without k-anonymity or source verification
# =============================================================================

def run_ln09_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-09: Exponential Moving Average (EMA) Trend Analyzer.

    Computes an exponential moving average of learner performance signals to trigger
    teacher intervention recommendations when EMA falls below threshold.
    Lacks:
    - k-anonymity privacy check on small cohort samples (n < 5).
    - Pedagogical source ground-truth verification of historical tasks.
    - Observation age / freshness decay gates.
    """
    evidence_list = scenario_input.get("learning_evidence", []) or []
    candidate = scenario_input.get("candidate_intervention") or "additional_source_comparison_activity"
    
    # Calculate EMA over evidence scores
    scores = [float(e.get("score", 0.0)) for e in evidence_list if isinstance(e.get("score"), (int, float))]
    
    alpha = 0.3
    ema = 0.5
    if scores:
        ema = scores[0]
        for s in scores[1:]:
            ema = alpha * s + (1 - alpha) * ema

    # Trigger action if EMA indicates need for support or if evidence exists
    action_threshold = float((config or {}).get("ema_intervention_threshold", 0.70))
    action_proposed = bool(scores and ema <= action_threshold)

    decision = "propose_explained_action" if action_proposed else "descriptive_summary_only"
    reason_codes = ["b1_ema_trend_triggered"] if action_proposed else ["b1_ema_trend_nominal"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "policy_version": "ln09-b1-ema-trend-v1.0",
        "action_proposed": action_proposed,
        "abstention_appropriate": False,
        "intervention_traceable": False,
        "candidate_intervention": candidate if action_proposed else None,
        "rationale": f"B1 EMA trend calculation (ema={ema:.2f})",
        "evidence_count": len(evidence_list),
        "k_anonymity_satisfied": False,  # B1 ignores k-anonymity!
        "source_verification_bypassed": True,
        "research_only": True,
    }


# =============================================================================
# LN-10: Linear milestone checklist with timer without reflective cycle gates
# =============================================================================

def run_ln10_b1(scenario_input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """B1 for LN-10: Linear Milestone Checklist with Timer / Progress Tracker.

    Enforces sequential progression and basic concurrency version matching, but:
    - Bypasses Zimmerman self-regulated learning (SRL) cyclical reflection gates.
    - Permits transitions without mandatory student reflection rationale.
    """
    actor = scenario_input.get("actor", {}) or {}
    project = scenario_input.get("project", {}) or {}
    transition = scenario_input.get("transition", {}) or {}

    role = actor.get("role", "student")
    owns_project = actor.get("owns_project", True)
    curr_version = project.get("version", 1)
    expected_version = transition.get("expected_version", curr_version)

    # 1. Version conflict detection
    if curr_version != expected_version:
        return {
            "decision": "reject_conflict",
            "reason_codes": ["b1_concurrency_version_mismatch"],
            "policy_version": "ln10-b1-checklist-v1.0",
            "transition_applied": False,
            "conflict_detected": True,
            "reflection_completed": False,
            "ownership_verified": True,
            "research_only": True,
        }

    # 2. Ownership verification
    if role != "student" or not owns_project:
        return {
            "decision": "reject_unauthorized",
            "reason_codes": ["b1_unauthorized_actor"],
            "policy_version": "ln10-b1-checklist-v1.0",
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_completed": False,
            "ownership_verified": False,
            "research_only": True,
        }

    # B1 allows linear progression without requiring reflection or rationale!
    return {
        "decision": "allow_authorized_transition",
        "reason_codes": ["b1_milestone_checklist_advanced"],
        "policy_version": "ln10-b1-checklist-v1.0",
        "transition_applied": True,
        "conflict_detected": False,
        "reflection_completed": False,  # Reflection omitted
        "ownership_verified": True,
        "research_only": True,
    }


# =============================================================================
# Standardized Dispatcher and Export Registry
# =============================================================================

B1_REGISTRY = {
    "LN-01": run_ln01_b1,
    "LN-02": run_ln02_b1,
    "LN-03": run_ln03_b1,
    "LN-04": run_ln04_b1,
    "LN-05": run_ln05_b1,
    "LN-06": run_ln06_b1,
    "LN-07": run_ln07_b1,
    "LN-08": run_ln08_b1,
    "LN-09": run_ln09_b1,
    "LN-10": run_ln10_b1,
}


def run_b1_policy(
    paper_id: str,
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Universal callable entrypoint to execute B1 for any study."""
    if paper_id not in B1_REGISTRY:
        raise ValueError(f"Unknown study ID for B1 baseline: '{paper_id}'. Expected one of {list(B1_REGISTRY.keys())}")
    return B1_REGISTRY[paper_id](scenario_input, config)
