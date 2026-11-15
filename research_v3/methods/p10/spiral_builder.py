"""P10 spiral sequence builder: constraint-checked curriculum design generator.

Implements METHOD.md §3 exactly:

Invariants (checked in order, fail-closed):
  I-ACYCLIC          prerequisite DAG must be acyclic (iterative DFS, cycle raised)
  I-GRADE-MONOTONE   grade(u) <= grade(v) on every edge; grades in {10,11,12}
  I-BLOOM-ASCENT     bloom(v) >= bloom(u) + min_ascent on every edge; edges with
                     a jump > ``max_leap`` are *flagged* (bloom_leap_flagged) for
                     expert judgement, not silently accepted or rejected
  I-ANCHOR           every object's anchor_code must exist in the frozen
                     registry (UnknownAnchorError otherwise) and be usable for
                     the object's grade

Designs:
  C0 ``linear_playlist``    chronological-category order, no gates (sanity floor)
  C1 ``topological_no_bloom`` Kahn order over the DAG; anchor gate on; Bloom gate off
  Proposed ``spiral_dag``   layer-clustered order with bridge edges, all gates on

Determinism: sorted-key iteration everywhere; ties broken by object_id; the
proposed builder contains no RNG. Random order exists only as ablation A4 with
an explicit seed.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from .anchors import (
    CurriculumAnchor,
    LearningObject,
    P10ContractError,
    PAPER_GRADES,
    PrerequisiteEdge,
    SequenceCertificate,
    SpiralSequence,
    UnknownAnchorError,
)
from .registry import assert_anchor_known

# Reason codes (machine-checkable vocabulary)
RC_VALID = "valid_spiral_sequence"
RC_CYCLE = "prerequisite_cycle_detected"
RC_GRADE_REVERSED = "grade_order_reversed"
RC_GRADE_OOB = "grade_out_of_bounds"
RC_BLOOM_NO_ASCENT = "bloom_depth_not_increasing"
RC_BLOOM_LEAP = "bloom_leap_flagged"
RC_UNKNOWN_ANCHOR = "unknown_curriculum_anchor"
RC_ANCHOR_GRADE_MISMATCH = "anchor_grade_mismatch"

RC_GATE_MAP = {
    "skip_cycle_check": RC_CYCLE,
    "skip_grade_check": RC_GRADE_REVERSED,
    "skip_bloom_check": RC_BLOOM_NO_ASCENT,
    "skip_anchor_check": RC_UNKNOWN_ANCHOR,
}


class CycleError(P10ContractError):
    """Raised when the prerequisite graph contains a directed cycle."""


class GradeInversionError(P10ContractError):
    """Raised when a prerequisite edge runs against grade monotonicity."""


class BloomAscentError(P10ContractError):
    """Raised when a progression edge fails the minimum Bloom ascent."""


# ---------------------------------------------------------------------------
# Object/edge index helpers
# ---------------------------------------------------------------------------
def _index(objects: Sequence[LearningObject]) -> dict[str, LearningObject]:
    idx: dict[str, LearningObject] = {}
    for obj in objects:
        if obj.object_id in idx:
            raise P10ContractError(f"duplicate object_id {obj.object_id!r}")
        idx[obj.object_id] = obj
    return idx


def _adjacency(
    objects: Mapping[str, LearningObject], edges: Sequence[PrerequisiteEdge]
) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {oid: [] for oid in sorted(objects)}
    for edge in edges:
        if edge.tail not in objects:
            raise P10ContractError(f"edge tail {edge.tail!r} is not a known object")
        if edge.head not in objects:
            raise P10ContractError(f"edge head {edge.head!r} is not a known object")
        adj[edge.tail].append(edge.head)
    for oid in adj:
        adj[oid].sort()  # deterministic DFS order
    return adj


# ---------------------------------------------------------------------------
# Invariant checks (pure functions; each returns/raises typed failures)
# ---------------------------------------------------------------------------
def check_acyclic(objects: Mapping[str, LearningObject], edges: Sequence[PrerequisiteEdge]) -> None:
    """Raise CycleError if the directed graph has any cycle (iterative DFS)."""
    adj = _adjacency(objects, edges)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {oid: WHITE for oid in sorted(adj)}
    for start in sorted(adj):
        if color[start] != WHITE:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        path: list[str] = []
        while stack:
            node, ptr = stack.pop()
            if ptr == 0:
                if color[node] == GRAY:
                    raise CycleError(f"prerequisite cycle passes through {node!r}")
                color[node] = GRAY
                path.append(node)
            neighbors = adj[node]
            advanced = False
            while ptr < len(neighbors):
                nxt = neighbors[ptr]
                ptr += 1
                if color[nxt] == GRAY:
                    raise CycleError(
                        f"prerequisite cycle: {' -> '.join(path + [nxt])}"
                    )
                if color[nxt] == WHITE:
                    stack.append((node, ptr))
                    stack.append((nxt, 0))
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                path.pop()


def check_grade_monotone(
    objects: Mapping[str, LearningObject], edges: Sequence[PrerequisiteEdge]
) -> None:
    """Raise GradeInversionError on any grade-decreasing edge or out-of-bounds grade."""
    for oid, obj in objects.items():
        if obj.grade not in PAPER_GRADES:
            raise P10ContractError(f"{oid}: grade {obj.grade} out of bounds")
    for edge in edges:
        g_tail = objects[edge.tail].grade
        g_head = objects[edge.head].grade
        if g_tail > g_head:
            raise GradeInversionError(
                f"grade inversion: {edge.tail} (grade {g_tail}) -> {edge.head} (grade {g_head})"
            )


def check_bloom_ascent(
    objects: Mapping[str, LearningObject],
    edges: Sequence[PrerequisiteEdge],
    *,
    min_ascent: int = 0,
    max_leap: int = 2,
) -> tuple[str, ...]:
    """Raise BloomAscentError if any edge's ascent < min_ascent.

    Returns the (sorted) list of edges whose jump exceeds ``max_leap`` — the
    bloom-leap warnings an expert must judge (flag, not rejection).
    """
    leaps: list[str] = []
    for edge in sorted(edges, key=lambda e: (e.tail, e.head)):
        b_tail = objects[edge.tail].bloom_level
        b_head = objects[edge.head].bloom_level
        if b_head - b_tail < min_ascent:
            raise BloomAscentError(
                f"bloom ascent violation: {edge.tail} (B{b_tail}) -> {edge.head} "
                f"(B{b_head}) needs +{min_ascent}"
            )
        if b_head - b_tail > max_leap:
            leaps.append(f"{edge.tail}->{edge.head}:+{b_head - b_tail}")
    return tuple(sorted(leaps))


def check_anchors(
    objects: Mapping[str, LearningObject],
    registry: Mapping[str, CurriculumAnchor],
) -> tuple[int, int]:
    """Fail-closed anchor resolution; returns (documented, needs_expert_review) counts.

    Raises UnknownAnchorError for any object whose anchor_code is missing from
    the registry — an invented competency code can never pass silently.
    Raises P10ContractError when the anchor exists but does not serve the
    object's grade.
    """
    documented = 0
    needs_review = 0
    for oid in sorted(objects):
        obj = objects[oid]
        anchor = assert_anchor_known(dict(registry), obj.anchor_code)  # raises on unknown
        if anchor.grade != obj.grade:
            raise P10ContractError(
                f"{oid}: anchor {anchor.anchor_code} serves grade {anchor.grade}, "
                f"object is grade {obj.grade} ({RC_ANCHOR_GRADE_MISMATCH})"
            )
        if anchor.confidence_status == "documented":
            documented += 1
        else:
            needs_review += 1
    return documented, needs_review


# ---------------------------------------------------------------------------
# Certificate assembly
# ---------------------------------------------------------------------------
def build_certificate(
    ordered_ids: Sequence[str],
    objects: Mapping[str, LearningObject],
    edges: Sequence[PrerequisiteEdge],
    registry: Mapping[str, CurriculumAnchor],
    *,
    min_ascent: int = 0,
    max_leap: int = 2,
    enabled_gates: Iterable[str] = ("cycle", "grade", "bloom", "anchor"),
) -> SequenceCertificate:
    """Evaluate all (enabled) invariants over an ordering and assemble a certificate.

    Ordering-insensitive checks (cycle, grade bounds, anchor existence) are
    properties of the design, not the permutation; edge-directional checks
    (grade monotonicity, Bloom ascent) are evaluated on the DAG as preregistered
    (the sequence must respect the DAG, so edge validity is necessary for the
    order to be realizable; C0's no-DAG order is checked for grade monotonicity
    along the playlist itself).
    """
    gates = set(enabled_gates)
    reasons: list[str] = []
    acyclic = grade_monotone = anchors_ok = True
    # A disabled gate means the design makes NO claim on that invariant, and a
    # missing claim must not read as a satisfied claim: bloom_ascent_ok stays
    # False unless the Bloom gate actually ran and passed.
    bloom_ok = False
    leaps: tuple[str, ...] = ()

    if "cycle" in gates:
        try:
            check_acyclic(objects, edges)
        except CycleError as exc:
            acyclic = False
            reasons.append(f"{RC_CYCLE}: {exc}")

    if "grade" in gates:
        try:
            check_grade_monotone(objects, edges)
        except (GradeInversionError, P10ContractError) as exc:
            grade_monotone = False
            reasons.append(f"{RC_GRADE_REVERSED}: {exc}")

    if "bloom" in gates:
        bloom_ok = True
        try:
            leaps = check_bloom_ascent(objects, edges, min_ascent=min_ascent, max_leap=max_leap)
        except (BloomAscentError, P10ContractError) as exc:
            bloom_ok = False
            reasons.append(f"{RC_BLOOM_NO_ASCENT}: {exc}")
        else:
            if leaps:
                reasons.append(f"{RC_BLOOM_LEAP}: {len(leaps)} edge(s) flagged for expert review")

    if "anchor" in gates:
        try:
            check_anchors(objects, registry)
        except (UnknownAnchorError, P10ContractError) as exc:
            anchors_ok = False
            reasons.append(f"{RC_UNKNOWN_ANCHOR}: {exc}")

    if not reasons:
        reasons.append(RC_VALID)
    return SequenceCertificate(
        acyclic=acyclic,
        grade_monotone=grade_monotone,
        bloom_ascent_ok=bloom_ok,
        anchors_resolved=anchors_ok,
        bloom_leap_edges=leaps,
        reason_codes=tuple(reasons),
    )


# ---------------------------------------------------------------------------
# Design builders
# ---------------------------------------------------------------------------
def build_linear_playlist(
    objects: Sequence[LearningObject],
    registry: Mapping[str, CurriculumAnchor],
    *,
    design_id: str = "C0_linear_playlist",
    order_key: str = "category",
) -> SpiralSequence:
    """C0: deterministic chronological-category playlist; no DAG, no gating.

    Objects are sorted by (order_key field, object_id) — the sanity floor any
    real design must beat under the expert rubric. Grade monotonicity is
    checked *along the playlist* (a playlist that walks grade 12 then grade 10
    is reported non-monotone) so C0 remains an honest comparator.
    """
    idx = _index(objects)
    ordered = sorted(
        idx.values(), key=lambda o: (str(getattr(o, order_key)), o.object_id)
    )
    ordered_ids = tuple(o.object_id for o in ordered)

    # Playlist-level grade monotonicity (no edges exist for C0).
    grade_monotone = all(
        ordered[i].grade <= ordered[i + 1].grade for i in range(len(ordered) - 1)
    )
    reasons: list[str] = []
    if not grade_monotone:
        reasons.append(f"{RC_GRADE_REVERSED}: playlist descends across grade boundary")
    documented = needs_review = 0
    anchors_ok = True
    try:
        documented, needs_review = check_anchors(idx, registry)
    except (UnknownAnchorError, P10ContractError) as exc:
        anchors_ok = False
        reasons.append(f"{RC_UNKNOWN_ANCHOR}: {exc}")
    if not reasons:
        reasons.append(RC_VALID)

    certificate = SequenceCertificate(
        acyclic=True,  # no edges: vacuously acyclic
        grade_monotone=grade_monotone,
        bloom_ascent_ok=False,  # C0 makes no depth claim
        anchors_resolved=anchors_ok,
        bloom_leap_edges=(),
        reason_codes=tuple(reasons),
    )
    return SpiralSequence(
        design_id=design_id,
        ordered_object_ids=ordered_ids,
        certificate=certificate,
        documented_anchor_count=documented,
        needs_expert_review_anchor_count=needs_review,
    )


def _kahn_order(
    objects: Mapping[str, LearningObject], edges: Sequence[PrerequisiteEdge]
) -> list[str]:
    """Deterministic Kahn topological sort; ties broken by object_id."""
    adj = _adjacency(objects, edges)
    indegree = {oid: 0 for oid in sorted(objects)}
    for edge in edges:
        indegree[edge.head] += 1
    ready = sorted(oid for oid, deg in indegree.items() if deg == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for nxt in adj[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort()
    if len(order) != len(objects):
        stuck = sorted(set(objects) - set(order))
        raise CycleError(f"topological sort incomplete; cycle among {stuck[:5]}…")
    return order


def build_topological_no_bloom(
    objects: Sequence[LearningObject],
    edges: Sequence[PrerequisiteEdge],
    registry: Mapping[str, CurriculumAnchor],
    *,
    design_id: str = "C1_topological_no_bloom",
) -> SpiralSequence:
    """C1: Kahn topological order; anchor gate ON; Bloom gate OFF."""
    idx = _index(objects)
    order = _kahn_order(idx, edges)
    certificate = build_certificate(
        order,
        idx,
        edges,
        registry,
        enabled_gates=("cycle", "grade", "anchor"),  # bloom gate removed
    )
    documented, needs_review = check_anchors(idx, registry)
    return SpiralSequence(
        design_id=design_id,
        ordered_object_ids=tuple(order),
        certificate=certificate,
        documented_anchor_count=documented,
        needs_expert_review_anchor_count=needs_review,
    )


def build_spiral_dag(
    objects: Sequence[LearningObject],
    edges: Sequence[PrerequisiteEdge],
    registry: Mapping[str, CurriculumAnchor],
    *,
    design_id: str = "proposed_spiral_dag",
    min_ascent: int = 0,
    max_leap: int = 2,
) -> SpiralSequence:
    """Proposed: layer-clustered spiral order with bridge edges, all gates on.

    Ordering algorithm (deterministic):
      1. verify all invariants on the design graph (fail-closed);
      2. Kahn layers: process objects in topological order, but grouped by
         (grade, layer, category, object_id) so grade-10 identification work
         precedes grade-11 corroboration precedes grade-12 evaluation — the
         Bruner spiral revisiting themes with rising depth;
      3. emit the flat order plus per-invariant certificates.
    """
    idx = _index(objects)
    # Fail-closed on all four invariants first.
    certificate = build_certificate(
        [],  # ordering-insensitive checks dominate; edge checks use the DAG
        idx,
        edges,
        registry,
        min_ascent=min_ascent,
        max_leap=max_leap,
        enabled_gates=("cycle", "grade", "bloom", "anchor"),
    )
    if not certificate.valid:
        raise P10ContractError(
            f"{design_id}: design graph violates invariants: {certificate.reason_codes}"
        )
    order = _kahn_order(idx, edges)
    # Spiral re-ordering: stable sort by (grade, layer, category, object_id).
    spiral_ranked = sorted(
        order,
        key=lambda oid: (
            idx[oid].grade,
            idx[oid].layer,
            idx[oid].category,
            oid,
        ),
    )
    documented, needs_review = check_anchors(idx, registry)
    return SpiralSequence(
        design_id=design_id,
        ordered_object_ids=tuple(spiral_ranked),
        certificate=certificate,
        documented_anchor_count=documented,
        needs_expert_review_anchor_count=needs_review,
    )
