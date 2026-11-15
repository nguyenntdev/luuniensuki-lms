"""P10 mechanism-isolating ablations (paper packet §5 A1-A4).

Each ablation genuinely removes ONE named mechanism of the proposed design and
is directly sensitive to it (mutation must be observable, or the ablation is
not measuring the mechanism):

- A1 ``no_layer_bridge``    — removes cross-urn bridge edges: the spiral loses
  the shared-vocabulary scaffolding between urns. Sensitive because bridges
  are the only cross-urn connectivity; without them each urn is an isolated
  component (measured: connected-component count).
- A2 ``no_bloom_ascent``    — removes the Bloom depth gate: flat sequences
  (no depth rise) become acceptable (measured: depth-ascent rate collapses).
- A3 ``no_provenance_gate`` — removes the anchor gate: objects with unknown /
  missing curriculum anchors pass silently (measured: a poisoned object with
  an invented anchor is accepted instead of rejected).
- A4 ``random_order``       — seeded random playlist: no spiral structure at
  all (the only stochastic design; seeded for reproducibility).

All ablations run over identical inputs (same 162 objects, same registry) and
the same deterministic policy surface; differences come only from the removed
mechanism — no manufactured data.
"""
from __future__ import annotations

import random
from typing import Sequence

from .anchors import (
    LearningObject,
    P10ContractError,
    PrerequisiteEdge,
    SequenceCertificate,
    SpiralSequence,
)
from .corpus import build_prerequisite_edges
from .registry import CurriculumAnchor, assert_anchor_known
from .spiral_builder import (
    RC_CYCLE,
    RC_GRADE_REVERSED,
    RC_VALID,
    RC_UNKNOWN_ANCHOR,
    _index,
    _kahn_order,
    build_certificate,
    check_anchors,
)

ABLATION_IDS = ("A1_no_layer_bridge", "A2_no_bloom_ascent", "A3_no_provenance_gate", "A4_random_order")


def run_a1_no_layer_bridge(
    objects: Sequence[LearningObject],
    registry: dict[str, CurriculumAnchor],
) -> tuple[SpiralSequence, dict]:
    """Remove cross-urn bridges; report the structural loss honestly."""
    edges = build_prerequisite_edges(objects, within_urn=True, cross_layer_bridges=False)
    idx = _index(objects)
    order = _kahn_order(idx, edges)
    certificate = build_certificate(
        order, idx, edges, registry, enabled_gates=("cycle", "grade", "bloom", "anchor")
    )
    documented, needs_review = check_anchors(idx, registry)
    # Structural sensitivity measure: component census of the DAG.
    components = _weakly_connected_components(idx, edges)
    sequence = SpiralSequence(
        design_id="A1_no_layer_bridge",
        ordered_object_ids=tuple(order),
        certificate=certificate,
        documented_anchor_count=documented,
        needs_expert_review_anchor_count=needs_review,
    )
    return sequence, {"component_census": components}


def run_a2_no_bloom_ascent(
    objects: Sequence[LearningObject],
    registry: dict[str, CurriculumAnchor],
) -> tuple[SpiralSequence, dict]:
    """Remove the Bloom depth gate: certificate stops asserting depth ascent."""
    edges = build_prerequisite_edges(objects)
    idx = _index(objects)
    order = _kahn_order(idx, edges)
    certificate = build_certificate(
        order, idx, edges, registry, enabled_gates=("cycle", "grade", "anchor")
    )
    # Mechanism-sensitivity measure: fraction of progression edges with strict rise.
    ascent_rate = _strict_ascent_rate(idx, edges)
    documented, needs_review = check_anchors(idx, registry)
    sequence = SpiralSequence(
        design_id="A2_no_bloom_ascent",
        ordered_object_ids=tuple(order),
        certificate=certificate,
        documented_anchor_count=documented,
        needs_expert_review_anchor_count=needs_review,
    )
    return sequence, {"progression_strict_ascent_rate": ascent_rate}


def run_a3_no_provenance_gate(
    objects: Sequence[LearningObject],
    registry: dict[str, CurriculumAnchor],
    *,
    poisoned_object: LearningObject | None = None,
) -> tuple[SpiralSequence, dict]:
    """Remove the anchor gate: an invented anchor passes silently (demonstrated).

    The default poisoned object fabricates anchor code
    ``NH10-FABRICATED-COMPETENCY`` — precisely the invention this design
    forbids. With the gate ON the build raises UnknownAnchorError; with the
    gate OFF (this ablation) the object sails through, which is exactly the
    failure mode the proposed design closes.
    """
    poison = poisoned_object or LearningObject(
        object_id="urn_poisoned_fabricated_anchor_01",
        urn_slug="cao-dinh",
        motif_name_vi="Họa tiết bị gắn mã năng lực bịa",
        category="linh_thu",
        grade=10,
        layer=1,
        bloom_level=2,
        anchor_code="NH10-FABRICATED-COMPETENCY",
    )
    corpus = list(objects) + [poison]
    edges = build_prerequisite_edges(corpus)
    idx = _index(corpus)
    order = _kahn_order(idx, edges)
    certificate = build_certificate(
        order, idx, edges, registry, enabled_gates=("cycle", "grade", "bloom")
    )
    invented_accepted = any(oid == poison.object_id for oid in order)
    sequence = SpiralSequence(
        design_id="A3_no_provenance_gate",
        ordered_object_ids=tuple(order),
        certificate=certificate,
        documented_anchor_count=0,  # gate off: counts meaningless, recorded as such
        needs_expert_review_anchor_count=0,
    )
    return sequence, {"invented_anchor_accepted": invented_accepted}


def run_a4_random_order(
    objects: Sequence[LearningObject],
    registry: dict[str, CurriculumAnchor],
    *,
    seed: int = 42,
) -> tuple[SpiralSequence, dict]:
    """Seeded random playlist — the only stochastic design, reproducible."""
    idx = _index(objects)
    ids = sorted(idx)
    rng = random.Random(seed)
    shuffled = list(ids)
    rng.shuffle(shuffled)
    ordered_ids = tuple(shuffled)
    # Grade monotonicity along the random playlist (expected to fail).
    grades = [idx[oid].grade for oid in ordered_ids]
    inversions = sum(1 for a, b in zip(grades, grades[1:]) if b < a)
    certificate = SequenceCertificate(
        acyclic=True,
        grade_monotone=inversions == 0,
        bloom_ascent_ok=False,
        anchors_resolved=True,  # anchors checked in check below
        bloom_leap_edges=(),
        reason_codes=(f"random_playlist_seed_{seed}: {inversions} grade inversions",)
        if inversions
        else (RC_VALID,),
    )
    documented, needs_review = check_anchors(idx, registry)
    sequence = SpiralSequence(
        design_id=f"A4_random_order(seed={seed})",
        ordered_object_ids=ordered_ids,
        certificate=certificate,
        documented_anchor_count=documented,
        needs_expert_review_anchor_count=needs_review,
    )
    return sequence, {"playlist_grade_inversions": inversions}


# ---------------------------------------------------------------------------
# Sensitivity helpers
# ---------------------------------------------------------------------------
def _weakly_connected_components(
    idx: dict[str, LearningObject], edges: Sequence[PrerequisiteEdge]
) -> dict[str, int]:
    """Component census: (n_isolated_nodes, n_connected_components_of_edges).

    With bridges removed, sensitivity shows up as more isolated objects and
    more separate edge-components; a plain count is confusing because most
    corpus motifs legitimately have no prerequisite edges.
    """
    parent = {oid: oid for oid in idx}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    referenced: set[str] = set()
    for edge in edges:
        ru, rv = find(edge.tail), find(edge.head)
        if ru != rv:
            parent[ru] = rv
        referenced.add(edge.tail)
        referenced.add(edge.head)
    edge_components = len({find(oid) for oid in referenced}) if referenced else 0
    isolated = len(idx) - len(referenced)
    return {"isolated_objects": isolated, "edge_connected_components": edge_components}


def _strict_ascent_rate(
    idx: dict[str, LearningObject], edges: Sequence[PrerequisiteEdge]
) -> float | None:
    ascending = [
        1 if idx[e.head].bloom_level > idx[e.tail].bloom_level else 0 for e in edges
    ]
    if not ascending:
        return None
    return sum(ascending) / len(ascending)
