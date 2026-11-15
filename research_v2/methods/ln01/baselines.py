"""LN-01 baselines: C0 naive linear sanity and C1 strong classical.

Comparability cards
-------------------
- ``predict_batch_b0`` (C0, SANITY_ONLY): naive linear acceptance — no graph
  reasoning at all; accepts every structurally valid case. Recorded as
  ``REIMPLEMENTATION`` of the legacy flat baseline
  (``research/spiral/progression_graph.py::evaluate_spiral_progression_baseline``),
  role SANITY_ONLY; must never be called a strong baseline.
- ``predict_batch_c1`` (C1, MATCHED_CLASSICAL): Kahn topological sort with
  grade gating — verifies DAG acyclicity and grade monotonicity, but does NOT
  gate on Bloom cognitive depth and does NOT verify curriculum anchors.
  Recorded as ``REIMPLEMENTATION`` of the legacy topological baseline
  (``evaluate_spiral_progression_topological_baseline``) plus the grade gate
  described in spec 12_C1_STRONG_CLASSICAL ("Kahn topological sort with grade
  gating"). Per the study brief it deliberately omits cognitive Bloom depth
  gating. Independent implementation: does not import the proposed engine's
  decision path (shares only the shared parsing helpers, which contain no
  objective technique).

Both produce the same output type as the proposed method (legacy decision
vocabulary) so metrics are computed on a common decision space.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .engine import (
    DECISION_ACCEPT,
    DECISION_REJECT_CYCLE,
    DECISION_REJECT_GRADE_ORDER,
    RC_CYCLE,
    RC_NOMINAL,
    STUDY_ID,
    check_grade_order,
)

METHOD_VERSION_B0 = "v2-b0-flat-1.0.0"
METHOD_VERSION_C1 = "v2-c1-kahn-1.0.0"


def _parse_minimal(inp: StudyInput) -> tuple[list[dict[str, Any]], list[tuple[int, int]]]:
    """Independent minimal parsing for baselines (no engine decision logic)."""
    from research_v2.contracts.types import ContractError

    features = inp.features
    if not isinstance(features, Mapping):
        raise ContractError(f"case {inp.case_id!r}: features must be a mapping")
    raw_nodes = features.get("nodes")
    if not isinstance(raw_nodes, list):
        raise ContractError(f"case {inp.case_id!r}: 'nodes' must be a list")
    nodes: list[dict[str, Any]] = []
    for i, n in enumerate(raw_nodes):
        if not isinstance(n, Mapping):
            raise ContractError(f"case {inp.case_id!r}: node {i} must be a mapping")
        try:
            grade = int(n["grade"])
            level = int(n["cognitive_level"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(
                f"case {inp.case_id!r}: node {i} missing/invalid grade or cognitive_level"
            ) from exc
        nodes.append({"index": i, "grade": grade, "cognitive_level": level})
    raw_edges = features.get("prerequisites")
    if not isinstance(raw_edges, list):
        raise ContractError(f"case {inp.case_id!r}: 'prerequisites' must be a list")
    edges: list[tuple[int, int]] = []
    for i, e in enumerate(raw_edges):
        if not isinstance(e, (list, tuple)) or len(e) != 2:
            raise ContractError(
                f"case {inp.case_id!r}: prerequisite edge {i} must be a [u, v] pair"
            )
        try:
            u, v = int(e[0]), int(e[1])
        except (TypeError, ValueError) as exc:
            raise ContractError(
                f"case {inp.case_id!r}: prerequisite edge {i} has non-integer endpoints"
            ) from exc
        if not (0 <= u < len(nodes) and 0 <= v < len(nodes)):
            raise ContractError(
                f"case {inp.case_id!r}: prerequisite edge {i} references unknown node index"
            )
        edges.append((u, v))
    return nodes, edges


def predict_batch_b0(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """C0 sanity baseline: naive flat sequencing, accept-when-structurally-valid.

    No cycle, grade, Bloom or anchor reasoning. Existence of any parseable
    graph yields ``accept``; malformed graphs raise typed ContractError (never
    a silent guessed fallback).
    """
    predictions: list[StudyPrediction] = []
    for inp in inputs:
        nodes, _edges = _parse_minimal(inp)
        if not nodes:
            raise ValueError(
                f"case {inp.case_id!r}: C0 baseline cannot score an empty node set"
            )
        predictions.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_ACCEPT,
                score=None,
                reason_codes=("baseline_flat_progression_allowed",),
                evidence_ids=tuple(f"node:{n['index']}" for n in nodes),
            )
        )
    return predictions


def _kahn_topological(nodes: list[dict[str, Any]], edges: list[tuple[int, int]]) -> list[int] | None:
    """Kahn's algorithm. Returns an order or None when a cycle exists."""
    n = len(nodes)
    indeg = [0] * n
    adj: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        indeg[v] += 1
    ready = [i for i in range(n) if indeg[i] == 0]
    order: list[int] = []
    while ready:
        u = ready.pop()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                ready.append(v)
    if len(order) != n:
        return None
    return order


def predict_batch_c1(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """C1 strong classical: Kahn topological sort WITHOUT cognitive Bloom gating.

    Checks:
      1. DAG acyclicity via Kahn's algorithm (grade-agnostic) -> ``reject_cycle``
      2. grade monotonicity + bounds on prerequisite edges -> ``reject_grade_order``
    Deliberately does NOT check Bloom depth ascent or curriculum anchors, per
    spec 12_C1_STRONG_CLASSICAL (this is exactly the mechanism gap the proposed
    method must close).
    """
    predictions: list[StudyPrediction] = []
    for inp in inputs:
        nodes, edges = _parse_minimal(inp)
        evidence = tuple(f"node:{n['index']}" for n in nodes)
        order = _kahn_topological(nodes, edges)
        if order is None:
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision=DECISION_REJECT_CYCLE,
                    score=None,
                    reason_codes=(RC_CYCLE, "kahn_topological_sort_infeasible"),
                    evidence_ids=evidence,
                )
            )
            continue
        grade_code = check_grade_order(nodes, edges)
        if grade_code is not None:
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision=DECISION_REJECT_GRADE_ORDER,
                    score=None,
                    reason_codes=(grade_code,),
                    evidence_ids=evidence,
                )
            )
            continue
        predictions.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_ACCEPT,
                score=None,
                reason_codes=("topological_sort_valid", RC_NOMINAL),
                evidence_ids=evidence,
            )
        )
    return predictions
