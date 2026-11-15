"""Shared decision engine for LN-01 Research V2 policies.

Legacy divergence note
----------------------
The legacy engine ``research/spiral/progression_graph.py``
(``check_cognitive_progression``) rejects any prerequisite edge whose head has
``cognitive_level(head) <= cognitive_level(tail)`` — including EQUAL levels —
and its anchor check treats a grade as covered whenever *any* anchor string is
present for it. Two legacy behaviors are scientifically wrong and are corrected
here:

1. **Alternative-provider false infeasibility (mandatory case).** Two nodes can
   provide the *same learning outcome* (same objective). If the curriculum uses
   both as alternative providers with cross edges (A→B where both carry the
   same objective), the legacy per-edge Bloom-strict-increase rule plus its
   naive DFS cycle extraction can flag the pair as ``reject_no_progression``
   even though a feasible route exists by choosing one provider and skipping
   the other. V2 fixes this: edges between alternative providers of the same
   outcome are *redundancy* edges, not progression edges, and are excluded from
   Bloom-depth gating and from grade-order gating. A cycle that exists only
   through redundancy edges is a *benign* cycle: the planner can still emit a
   feasible route that reaches the outcome exactly once, so it is NOT a false
   infeasibility. Hard infeasibility is declared only when no provider of some
   required outcome is reachable at all, or a cycle exists among
   *progression* edges (true logical contradiction).

2. **Grade-order check on redundant edges.** Legacy rejects grade reversal on
   every edge. V2 checks grade monotonicity only along progression edges
   (edges that advance the outcome), not along alternative-provider edges.

Decision labels follow the legacy/gold vocabulary so the frozen T3 gold is
scoreable verbatim: ``accept``, ``reject_cycle``, ``reject_grade_order``,
``reject_missing_anchor``, ``reject_no_progression``. This is a documented
divergence from ``research_v2.contracts.label_space.LN01_DECISIONS`` (the
path-planning framing); the T3 gold uses the legacy decision space.

All predictions are pure functions of (features, config, seed). No oracle,
fault_id, cohort or expected_decision is ever read.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction

STUDY_ID = "LN-01"

DECISION_ACCEPT = "accept"
DECISION_REJECT_CYCLE = "reject_cycle"
DECISION_REJECT_GRADE_ORDER = "reject_grade_order"
DECISION_REJECT_MISSING_ANCHOR = "reject_missing_anchor"
DECISION_REJECT_NO_PROGRESSION = "reject_no_progression"

VALID_DECISIONS = frozenset(
    {
        DECISION_ACCEPT,
        DECISION_REJECT_CYCLE,
        DECISION_REJECT_GRADE_ORDER,
        DECISION_REJECT_MISSING_ANCHOR,
        DECISION_REJECT_NO_PROGRESSION,
    }
)

MIN_GRADE = 10
MAX_GRADE = 12

# Reason codes (explicit, machine-checkable)
RC_NOMINAL = "nominal_progression_valid"
RC_CYCLE = "prerequisite_cycle_detected"
RC_GRADE_REVERSED = "grade_order_reversed"
RC_GRADE_OOB = "grade_out_of_high_school_bounds"
RC_MISSING_ANCHOR = "missing_curriculum_anchor"
RC_NO_PROGRESSION = "no_cognitive_progression"
RC_INVALID_STRUCTURE = "invalid_graph_structure"
RC_BAD_NODE = "invalid_node_schema"

# Ablation keys understood by this engine (used by ablations.py)
FLAG_SKIP_CYCLE = "skip_cycle_check"
FLAG_SKIP_ANCHOR = "skip_anchor_check"
FLAG_SKIP_DEPTH = "skip_depth_gate"


def _require_mapping(features: Mapping[str, Any], case_id: str) -> None:
    if not isinstance(features, Mapping):
        raise ContractError(f"case {case_id!r}: features must be a mapping")


def _parse_nodes(features: Mapping[str, Any], case_id: str) -> list[dict[str, Any]]:
    raw = features.get("nodes")
    if raw is None or not isinstance(raw, list):
        raise ContractError(f"case {case_id!r}: 'nodes' must be a list")
    nodes: list[dict[str, Any]] = []
    for i, n in enumerate(raw):
        if not isinstance(n, Mapping):
            raise ContractError(f"case {case_id!r}: node {i} must be a mapping")
        try:
            grade = int(n["grade"])
            level = int(n["cognitive_level"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(
                f"case {case_id!r}: node {i} missing/invalid grade or cognitive_level"
            ) from exc
        nodes.append(
            {
                "index": i,
                "grade": grade,
                "cognitive_level": level,
                "objective": str(n.get("objective", "")),
                "content_id": str(n.get("content_id", "")),
            }
        )
    return nodes


def _parse_prerequisites(features: Mapping[str, Any], nodes: list[dict[str, Any]], case_id: str) -> list[tuple[int, int]]:
    raw = features.get("prerequisites")
    if raw is None or not isinstance(raw, list):
        raise ContractError(f"case {case_id!r}: 'prerequisites' must be a list")
    n_nodes = len(nodes)
    edges: list[tuple[int, int]] = []
    for i, e in enumerate(raw):
        if not isinstance(e, (list, tuple)) or len(e) != 2:
            raise ContractError(
                f"case {case_id!r}: prerequisite edge {i} must be a [u, v] pair"
            )
        try:
            u, v = int(e[0]), int(e[1])
        except (TypeError, ValueError) as exc:
            raise ContractError(
                f"case {case_id!r}: prerequisite edge {i} has non-integer endpoints"
            ) from exc
        if not (0 <= u < n_nodes and 0 <= v < n_nodes):
            raise ContractError(
                f"case {case_id!r}: prerequisite edge {i} references unknown node index ({u}, {v}); "
                f"graph has {n_nodes} nodes"
            )
        edges.append((u, v))
    return edges


def _parse_anchor(features: Mapping[str, Any]) -> Mapping[str, Any]:
    anchor = features.get("curriculum_anchor")
    if anchor is None:
        return {}
    if not isinstance(anchor, Mapping):
        raise ContractError("'curriculum_anchor' must be a mapping of grade -> anchor id")
    return anchor


def find_cycles(num_nodes: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    """DFS 3-color cycle detection. Returns cycles as node-index lists."""
    adj: list[list[int]] = [[] for _ in range(num_nodes)]
    for u, v in edges:
        adj[u].append(v)
    color = [0] * num_nodes
    path: list[int] = []
    cycles: list[list[int]] = []

    def dfs(u: int) -> None:
        color[u] = 1
        path.append(u)
        for v in adj[u]:
            if color[v] == 1:
                try:
                    idx = path.index(v)
                    cycles.append(path[idx:] + [v])
                except ValueError:
                    cycles.append([u, v])
            elif color[v] == 0:
                dfs(v)
        path.pop()
        color[u] = 2

    for i in range(num_nodes):
        if color[i] == 0:
            dfs(i)
    return cycles


def _outcome_key(node: dict[str, Any]) -> str:
    """Learning-outcome identity of a node (objective within its content)."""
    return f"{node['content_id']}::{node['objective']}"


def classify_edges(
    nodes: list[dict[str, Any]], edges: list[tuple[int, int]]
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Split edges into (progression, redundancy).

    A redundancy edge carries no new cognitive demand:
      - it connects two DISTINCT nodes providing the SAME learning outcome
        (alternative providers), or
      - it is a self-loop (u == v) on a node that can be entered without
        traversing the self-loop: the node has an incoming edge from a
        different node, or its outcome has a clean alternative provider.

    A self-loop on a uniquely-provided outcome with no alternative entry is a
    true contradiction (the outcome is unobtainable) and stays a progression
    edge, where the cycle detector will flag it.

    Redundancy edges are excluded from Bloom-depth and grade-order gating and
    from the true-cycle test — see the module docstring.
    """
    outcome_by_idx: dict[int, str] = {n["index"]: _outcome_key(n) for n in nodes}
    self_looped = {u for u, v in edges if u == v}

    def _has_external_in(i: int) -> bool:
        return any(u != i and v == i for u, v in edges)

    def _has_clean_alternative(i: int) -> bool:
        return any(
            m != i and outcome_by_idx[m] == outcome_by_idx[i] and m not in self_looped
            for m in outcome_by_idx
        )

    progression: list[tuple[int, int]] = []
    redundancy: list[tuple[int, int]] = []
    for u, v in edges:
        if u == v:
            if _has_external_in(u) or _has_clean_alternative(u):
                redundancy.append((u, v))
            else:
                progression.append((u, v))
        elif outcome_by_idx[u] == outcome_by_idx[v]:
            redundancy.append((u, v))
        else:
            progression.append((u, v))
    return progression, redundancy


def check_grade_order(nodes: list[dict[str, Any]], edges: list[tuple[int, int]]) -> str | None:
    """Return a failure reason code or None. Checks bounds + monotonic grades."""
    by_idx = {n["index"]: n for n in nodes}
    for n in nodes:
        if not (MIN_GRADE <= n["grade"] <= MAX_GRADE):
            return RC_GRADE_OOB
    for u, v in edges:
        if by_idx[u]["grade"] > by_idx[v]["grade"]:
            return RC_GRADE_REVERSED
    return None


def check_anchor_coverage(nodes: list[dict[str, Any]], anchor: Mapping[str, Any]) -> str | None:
    """Return RC_MISSING_ANCHOR when any referenced grade lacks an authorized anchor.

    Divergence from legacy: a non-empty-but-blank anchor string does NOT count
    as coverage. Anchors must be non-empty strings naming an authorized
    curriculum anchor for the grade band.
    """
    referenced = sorted({n["grade"] for n in nodes})
    for g in referenced:
        val = anchor.get(f"grade{g}")
        if not isinstance(val, str) or not val.strip():
            return RC_MISSING_ANCHOR
    return None


def check_bloom_progression(nodes: list[dict[str, Any]], edges: list[tuple[int, int]]) -> str | None:
    """Return RC_NO_PROGRESSION when a progression edge fails Bloom ascent.

    Only PROGRESSION edges are gated. Redundancy (alternative-provider) edges
    are excluded — see classify_edges and the module docstring.
    """
    by_idx = {n["index"]: n for n in nodes}
    for u, v in edges:
        if by_idx[v]["cognitive_level"] <= by_idx[u]["cognitive_level"]:
            return RC_NO_PROGRESSION
    return None


def check_true_cycle(
    nodes: list[dict[str, Any]],
    progression_edges: list[tuple[int, int]],
    redundancy_edges: list[tuple[int, int]],
) -> str | None:
    """Return RC_CYCLE only for cycles that are genuinely infeasible.

    A cycle purely among alternative providers of the same outcome is benign:
    a planner can pick one provider and reach the outcome without traversing
    the cycle. A cycle that includes at least one progression edge is a real
    logical contradiction (outcome A requires B requires ... requires A with
    strictly increasing Bloom depth), which cannot be scheduled.
    """
    if not progression_edges:
        # All edges redundant: any cycle is benign.
        return None
    # Contract-check on the V2 invariants: a cycle containing at least one
    # progression edge implies an unsatisfiable strict-increase chain, so it is
    # infeasible regardless of Bloom gating being enabled.
    true_edges = list(progression_edges)
    cycles = find_cycles(len(nodes), true_edges)
    if cycles:
        return RC_CYCLE
    return None


def evaluate_case(
    inp: StudyInput,
    config: Mapping[str, Any],
) -> StudyPrediction:
    """Core constraint-aware spiral progression decision.

    Hard-check ordering (fail-fast certificate semantics):
        1. structural schema validation (typed ContractError, not a decision)
        2. cycle feasibility among progression edges
        3. grade monotonicity / bounds (progression edges only)
        4. curriculum anchor coverage
        5. Bloom depth gating (progression edges only)
        6. nominal accept

    Ablation flags in ``config`` disable checks 2/4/5 individually:
    ``skip_cycle_check``, ``skip_anchor_check``, ``skip_depth_gate``.
    """
    features = inp.features
    _require_mapping(features, inp.case_id)
    nodes = _parse_nodes(features, inp.case_id)
    edges = _parse_prerequisites(features, nodes, inp.case_id)
    anchor = _parse_anchor(features)

    skip_cycle = bool(config.get(FLAG_SKIP_CYCLE, False))
    skip_anchor = bool(config.get(FLAG_SKIP_ANCHOR, False))
    skip_depth = bool(config.get(FLAG_SKIP_DEPTH, False))

    progression_edges, redundancy_edges = classify_edges(nodes, edges)
    evidence_ids = tuple(f"node:{n['index']}" for n in nodes)

    if not skip_cycle:
        cycle_code = check_true_cycle(nodes, progression_edges, redundancy_edges)
        if cycle_code is not None:
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_REJECT_CYCLE,
                score=None,
                reason_codes=(RC_CYCLE,),
                evidence_ids=evidence_ids,
            )

    grade_code = check_grade_order(nodes, progression_edges)
    if grade_code is not None:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision=DECISION_REJECT_GRADE_ORDER,
            score=None,
            reason_codes=(grade_code,),
            evidence_ids=evidence_ids,
        )

    if not skip_anchor:
        anchor_code = check_anchor_coverage(nodes, anchor)
        if anchor_code is not None:
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_REJECT_MISSING_ANCHOR,
                score=None,
                reason_codes=(RC_MISSING_ANCHOR,),
                evidence_ids=evidence_ids,
            )

    if not skip_depth:
        depth_code = check_bloom_progression(nodes, progression_edges)
        if depth_code is not None:
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_REJECT_NO_PROGRESSION,
                score=None,
                reason_codes=(RC_NO_PROGRESSION,),
                evidence_ids=evidence_ids,
            )

    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=DECISION_ACCEPT,
        score=None,
        reason_codes=(RC_NOMINAL,),
        evidence_ids=evidence_ids,
    )
