"""Research Spiral - Spiral Curriculum Progression Graph Engine (Study LN-01).

Theory:
- Spiral curriculum (Bruner): Revisiting core cultural heritage topics with increasing
  cognitive complexity and broader contextual integration across Grade 10, 11, and 12.
- Constructive alignment (Biggs): Intended learning outcomes, pedagogical tasks,
  and assessment evidence must align directly with authorized curriculum standards.
- Historical reasoning (Van Drie & Van Boxtel): Movement from observation/identification
  to source contextualization and multi-perspective heritage evaluation.

Pedagogical Invariants:
- INV-LN-01-01: Progression edges must differ in cognitive operations or knowledge
  integration, not just textual repetition (reject_no_progression).
- INV-LN-01-02: Prerequisite relations must form a strict Directed Acyclic Graph (DAG);
  cycles are strictly rejected (reject_cycle).
- INV-LN-01-03: No relation can exist without authorized curriculum anchors for all
  involved grade bands (reject_missing_anchor).
- INV-LN-01-04: Tasks must observe monotonic non-decreasing grade ordering along
  prerequisite edges (reject_grade_order).
- INV-LN-01-05: Learning resources must preserve provenance and content rights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from research.spiral.curriculum_crosswalk import check_anchor_coverage


POLICY_VERSION_INTERVENTION = "2.0-intervention"
POLICY_VERSION_BASELINE = "1.0-baseline"
POLICY_VERSION_ABLATION = "2.0-ablation"


@dataclass(frozen=True)
class PedagogicalNode:
    """Represents a discrete pedagogical task node within the progression graph."""

    index: int
    content_id: str
    grade: int
    cognitive_level: int
    objective: str

    @classmethod
    def from_dict(cls, index: int, data: Dict[str, Any]) -> PedagogicalNode:
        return cls(
            index=index,
            content_id=str(data.get("content_id", "")),
            grade=int(data.get("grade", 0)),
            cognitive_level=int(data.get("cognitive_level", 0)),
            objective=str(data.get("objective", "")),
        )


@dataclass(frozen=True)
class ProgressionDecision:
    """Decision output structure conforming to runner and benchmark contracts."""

    decision: str
    reason_codes: List[str]
    policy_version: str
    progression_valid: bool
    observables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "policy_version": self.policy_version,
            "progression_valid": self.progression_valid,
        }
        res.update(self.observables)
        return res


def detect_prerequisite_cycles(
    num_nodes: int,
    prerequisites: List[List[int]],
) -> List[List[int]]:
    """Detect cycles in prerequisite directed graph using DFS with 3-state coloring.

    States: 0 = unvisited, 1 = visiting (recursion stack), 2 = visited.
    Returns list of cycles found (empty if DAG).
    """
    adj: Dict[int, List[int]] = {i: [] for i in range(num_nodes)}
    for edge in prerequisites:
        if len(edge) >= 2:
            u, v = int(edge[0]), int(edge[1])
            if u in adj and v in adj:
                adj[u].append(v)

    color = [0] * num_nodes
    parent = [-1] * num_nodes
    cycles: List[List[int]] = []

    def dfs(u: int, path: List[int]) -> None:
        color[u] = 1
        path.append(u)

        for v in adj[u]:
            if color[v] == 1:
                # Cycle found! Extract cycle path
                try:
                    idx = path.index(v)
                    cycle = path[idx:] + [v]
                    cycles.append(cycle)
                except ValueError:
                    cycles.append([u, v])
            elif color[v] == 0:
                parent[v] = u
                dfs(v, path)

        path.pop()
        color[u] = 2

    for i in range(num_nodes):
        if color[i] == 0:
            dfs(i, [])

    return cycles


def check_grade_order(
    nodes: List[PedagogicalNode],
    prerequisites: List[List[int]],
) -> Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
    """Validate that prerequisite relationships follow non-decreasing grade levels.

    A prerequisite edge (u, v) where grade(u) > grade(v) violates progression order.
    Also validates that grades reside in valid educational bands (e.g. 10, 11, 12).
    """
    node_map = {n.index: n for n in nodes}

    for edge in prerequisites:
        if len(edge) < 2:
            continue
        u_idx, v_idx = int(edge[0]), int(edge[1])
        u_node = node_map.get(u_idx)
        v_node = node_map.get(v_idx)
        if not u_node or not v_node:
            continue

        if u_node.grade > v_node.grade:
            return (
                False,
                f"Grade reversed: Node {u_idx} (grade {u_node.grade}) precedes Node {v_idx} (grade {v_node.grade})",
                (u_idx, v_idx),
            )

        # Check for invalid lower-grade regression in high school heritage curriculum
        if v_node.grade < 10 or u_node.grade < 10:
            return (
                False,
                f"Grade out of high school bounds: Node {v_idx} has grade {v_node.grade}",
                (u_idx, v_idx),
            )

    return True, None, None


def check_cognitive_progression(
    nodes: List[PedagogicalNode],
    prerequisites: List[List[int]],
) -> Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
    """Validate that subsequent tasks increase cognitive complexity (no shallow repetition).

    If edge (u, v) exists where cognitive_level(v) <= cognitive_level(u), progression is halted.
    """
    node_map = {n.index: n for n in nodes}

    for edge in prerequisites:
        if len(edge) < 2:
            continue
        u_idx, v_idx = int(edge[0]), int(edge[1])
        u_node = node_map.get(u_idx)
        v_node = node_map.get(v_idx)
        if not u_node or not v_node:
            continue

        if v_node.cognitive_level <= u_node.cognitive_level:
            return (
                False,
                f"No cognitive progression: Node {v_idx} (level {v_node.cognitive_level}) <= Node {u_idx} (level {u_node.cognitive_level})",
                (u_idx, v_idx),
            )

    return True, None, None


def evaluate_spiral_progression_intervention(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> ProgressionDecision:
    """Intervention policy: Strict spiral progression validation.

    Checks:
    1. Prerequisite cycles (DAG validation) -> reject_cycle
    2. Grade monotonicity and bounds -> reject_grade_order
    3. Curriculum anchor completeness -> reject_missing_anchor
    4. Cognitive depth increase -> reject_no_progression
    5. Nominal -> accept
    """
    config = config or {}
    raw_nodes = scenario_input.get("nodes", [])
    prerequisites = scenario_input.get("prerequisites", [])
    curriculum_anchor = scenario_input.get("curriculum_anchor", {})

    nodes = [PedagogicalNode.from_dict(i, n) for i, n in enumerate(raw_nodes)]
    num_nodes = len(nodes)

    # 1. Cycle detection (INV-LN-01-02)
    cycles = detect_prerequisite_cycles(num_nodes, prerequisites)
    if cycles:
        return ProgressionDecision(
            decision="reject_cycle",
            reason_codes=["prerequisite_cycle_detected", "Chu trình tiền đề không hợp lệ"],
            policy_version=POLICY_VERSION_INTERVENTION,
            progression_valid=False,
            observables={
                "progression_valid": False,
                "prerequisite_cycle_count": len(cycles),
                "unmapped_outcome_rate": 0.0,
                "cycles_detected": cycles,
                "violations": ["cycle_detected_in_prerequisites"],
                "node_count": num_nodes,
                "edge_count": len(prerequisites),
            },
        )

    # 2. Grade ordering (INV-LN-01-04)
    grade_ok, grade_msg, grade_pair = check_grade_order(nodes, prerequisites)
    if not grade_ok:
        return ProgressionDecision(
            decision="reject_grade_order",
            reason_codes=["grade_order_reversed", "Quan hệ sau → trước đi sai mức lớp"],
            policy_version=POLICY_VERSION_INTERVENTION,
            progression_valid=False,
            observables={
                "progression_valid": False,
                "prerequisite_cycle_count": 0,
                "unmapped_outcome_rate": 0.0,
                "violations": [grade_msg or "grade_order_reversed"],
                "violating_edge": list(grade_pair) if grade_pair else [],
                "node_count": num_nodes,
                "edge_count": len(prerequisites),
            },
        )

    # 3. Curriculum anchor coverage (INV-LN-01-03)
    anchor_ok, missing_grades, unmapped_rate = check_anchor_coverage(raw_nodes, curriculum_anchor)
    if not anchor_ok:
        return ProgressionDecision(
            decision="reject_missing_anchor",
            reason_codes=["missing_curriculum_anchor", "Không có văn bản mục tiêu chương trình"],
            policy_version=POLICY_VERSION_INTERVENTION,
            progression_valid=False,
            observables={
                "progression_valid": False,
                "prerequisite_cycle_count": 0,
                "unmapped_outcome_rate": unmapped_rate,
                "missing_anchor_grades": missing_grades,
                "violations": ["missing_regulatory_curriculum_anchor"],
                "node_count": num_nodes,
                "edge_count": len(prerequisites),
            },
        )

    # 4. Cognitive complexity progression (INV-LN-01-01)
    cog_ok, cog_msg, cog_pair = check_cognitive_progression(nodes, prerequisites)
    if not cog_ok:
        return ProgressionDecision(
            decision="reject_no_progression",
            reason_codes=["no_cognitive_progression", "Hai cấp chỉ lặp hoạt động nhận diện"],
            policy_version=POLICY_VERSION_INTERVENTION,
            progression_valid=False,
            observables={
                "progression_valid": False,
                "prerequisite_cycle_count": 0,
                "unmapped_outcome_rate": 0.0,
                "violations": [cog_msg or "no_cognitive_progression"],
                "violating_edge": list(cog_pair) if cog_pair else [],
                "node_count": num_nodes,
                "edge_count": len(prerequisites),
            },
        )

    # 5. Nominal case: All invariants satisfied
    return ProgressionDecision(
        decision="accept",
        reason_codes=["nominal_progression_valid", "Nhiệm vụ mới dùng kỹ năng bổ sung có lí do"],
        policy_version=POLICY_VERSION_INTERVENTION,
        progression_valid=True,
        observables={
            "progression_valid": True,
            "prerequisite_cycle_count": 0,
            "unmapped_outcome_rate": 0.0,
            "cycles_detected": [],
            "violations": [],
            "node_count": num_nodes,
            "edge_count": len(prerequisites),
        },
    )


def evaluate_spiral_progression_baseline(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> ProgressionDecision:
    """Baseline policy: Flat, content-only sequence.

    Does not verify cognitive depth increase, cycle absence, or curriculum anchor mapping.
    Blindly permits sequences as valid, leading to unverified progression errors.
    """
    raw_nodes = scenario_input.get("nodes", [])
    prerequisites = scenario_input.get("prerequisites", [])

    return ProgressionDecision(
        decision="accept",
        reason_codes=["baseline_flat_progression_allowed"],
        policy_version=POLICY_VERSION_BASELINE,
        progression_valid=True,
        observables={
            "progression_valid": True,
            "prerequisite_cycle_count": 0,
            "unmapped_outcome_rate": 0.0,
            "mode": "baseline",
            "node_count": len(raw_nodes),
            "edge_count": len(prerequisites),
        },
    )


def evaluate_spiral_progression_ablation(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> ProgressionDecision:
    """Ablation policy: Configurable omission of specific pedagogical checks.

    Supported ablation flags:
    - skip_cycle_check / ablation_type="no_cycle_check"
    - skip_grade_order_check / ablation_type="no_grade_check"
    - skip_anchor_check / ablation_type="no_anchor_check"
    - skip_cognitive_check / ablation_type="no_cognitive_check"
    """
    config = config or {}
    ablation_type = str(config.get("ablation_type", "")).lower()

    skip_cycle = (
        bool(config.get("skip_cycle_check", False))
        or bool(config.get("allow_cycles", False))
        or bool(config.get("disable_cycle_check", False))
        or (ablation_type in ("no_cycle_check", "allow_cycles", "disable_cycle_check"))
    )
    skip_grade = (
        bool(config.get("skip_grade_order_check", False))
        or bool(config.get("disable_grade_check", False))
        or bool(config.get("allow_grade_reversal", False))
        or (ablation_type in ("no_grade_check", "disable_grade_check", "no_grade_order_check", "allow_grade_reversal"))
    )
    skip_anchor = (
        bool(config.get("skip_anchor_check", False))
        or bool(config.get("disable_crosswalk", False))
        or bool(config.get("disable_anchor_check", False))
        or (ablation_type in ("no_anchor_check", "disable_crosswalk", "disable_anchor_check"))
    )
    skip_cognitive = (
        bool(config.get("skip_cognitive_check", False))
        or bool(config.get("disable_depth_gate", False))
        or bool(config.get("disable_cognitive_check", False))
        or (ablation_type in ("no_cognitive_check", "disable_depth_gate", "disable_cognitive_check"))
    )

    raw_nodes = scenario_input.get("nodes", [])
    prerequisites = scenario_input.get("prerequisites", [])
    curriculum_anchor = scenario_input.get("curriculum_anchor", {})

    nodes = [PedagogicalNode.from_dict(i, n) for i, n in enumerate(raw_nodes)]
    num_nodes = len(nodes)

    # 1. Cycle detection (unless ablated)
    if not skip_cycle:
        cycles = detect_prerequisite_cycles(num_nodes, prerequisites)
        if cycles:
            return ProgressionDecision(
                decision="reject_cycle",
                reason_codes=["prerequisite_cycle_detected", "Chu trình tiền đề không hợp lệ"],
                policy_version=POLICY_VERSION_ABLATION,
                progression_valid=False,
                observables={
                    "progression_valid": False,
                    "prerequisite_cycle_count": len(cycles),
                    "unmapped_outcome_rate": 0.0,
                    "violations": ["cycle_detected_in_prerequisites"],
                },
            )

    # 2. Grade ordering (unless ablated)
    if not skip_grade:
        grade_ok, grade_msg, grade_pair = check_grade_order(nodes, prerequisites)
        if not grade_ok:
            return ProgressionDecision(
                decision="reject_grade_order",
                reason_codes=["grade_order_reversed", "Quan hệ sau → trước đi sai mức lớp"],
                policy_version=POLICY_VERSION_ABLATION,
                progression_valid=False,
                observables={
                    "progression_valid": False,
                    "prerequisite_cycle_count": 0,
                    "unmapped_outcome_rate": 0.0,
                    "violations": [grade_msg or "grade_order_reversed"],
                },
            )

    # 3. Curriculum anchor coverage (unless ablated)
    if not skip_anchor:
        anchor_ok, missing_grades, unmapped_rate = check_anchor_coverage(raw_nodes, curriculum_anchor)
        if not anchor_ok:
            return ProgressionDecision(
                decision="reject_missing_anchor",
                reason_codes=["missing_curriculum_anchor", "Không có văn bản mục tiêu chương trình"],
                policy_version=POLICY_VERSION_ABLATION,
                progression_valid=False,
                observables={
                    "progression_valid": False,
                    "prerequisite_cycle_count": 0,
                    "unmapped_outcome_rate": unmapped_rate,
                    "missing_anchor_grades": missing_grades,
                    "violations": ["missing_regulatory_curriculum_anchor"],
                },
            )

    # 4. Cognitive complexity progression (unless ablated)
    if not skip_cognitive:
        cog_ok, cog_msg, cog_pair = check_cognitive_progression(nodes, prerequisites)
        if not cog_ok:
            return ProgressionDecision(
                decision="reject_no_progression",
                reason_codes=["no_cognitive_progression", "Hai cấp chỉ lặp hoạt động nhận diện"],
                policy_version=POLICY_VERSION_ABLATION,
                progression_valid=False,
                observables={
                    "progression_valid": False,
                    "prerequisite_cycle_count": 0,
                    "unmapped_outcome_rate": 0.0,
                    "violations": [cog_msg or "no_cognitive_progression"],
                },
            )

    return ProgressionDecision(
        decision="accept",
        reason_codes=["ablation_progression_allowed"],
        policy_version=POLICY_VERSION_ABLATION,
        progression_valid=True,
        observables={
            "progression_valid": True,
            "prerequisite_cycle_count": 0,
            "unmapped_outcome_rate": 0.0,
            "ablation_active": True,
        },
    )
